#!/usr/bin/env python3
"""Build derived explainers from pinned source repositories.

Commands
--------
lock     Pin every source in sources.yaml to its current local HEAD.
build    Extract excerpts named by explainers/*.yaml, render site/ and context/.
verify   Re-extract every excerpt and confirm it still matches site/manifest.json.

Design rule: this tool never writes prose. Every content block on a page is a
verbatim excerpt (markdown section, Python symbol, or anchored line range) read
from a source repo at its locked commit via `git show`, and every diagram is
parsed from the text of an excerpt on the same page.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay import render_tracking_replay  # noqa: E402
from rig_canvas import render_h5_rig_canvas, render_rig_canvas  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("pyyaml is required: pip install -r requirements.txt")

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover
    MarkdownIt = None

ROOT = Path(__file__).resolve().parent.parent
SOURCES_YAML = ROOT / "sources.yaml"
LOCK_JSON = ROOT / "sources.lock.json"
EXPLAINERS_DIR = ROOT / "explainers"
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"
CONTEXT_DIR = ROOT / "context"
MANIFEST_JSON = SITE_DIR / "manifest.json"


# ---------------------------------------------------------------------------
# Sources and lockfile
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return out.stdout


def _remote_to_https(remote: str) -> str | None:
    m = re.match(r"^git@github\.com:(.+?)(?:\.git)?$", remote.strip())
    if m:
        return f"https://github.com/{m.group(1)}"
    m = re.match(r"^https://github\.com/(.+?)(?:\.git)?/?$", remote.strip())
    if m:
        return f"https://github.com/{m.group(1)}"
    return None


def load_sources() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(SOURCES_YAML.read_text())
    return data["sources"]


def load_data_sources() -> dict[str, dict[str, Any]]:
    """Local, non-git data files (rig configs) that get snapshotted into data/."""
    data = yaml.safe_load(SOURCES_YAML.read_text())
    return data.get("data", {}) or {}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cmd_lock(_: argparse.Namespace) -> None:
    sources = load_sources()
    lock: dict[str, Any] = {
        "locked_at_utc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "sources": {},
        "data": {},
    }
    for name, spec in load_data_sources().items():
        base = Path(spec["local_path"])
        kind = spec.get("kind", "copy")
        files: dict[str, Any] = {}
        for rel in spec["files"]:
            src = base / rel
            if not src.is_file():
                sys.exit(f"data source {name}: {src} does not exist")
            mtime = (dt.datetime.fromtimestamp(src.stat().st_mtime, dt.timezone.utc)
                     .replace(microsecond=0).isoformat().replace("+00:00", "Z"))
            if kind == "copy":
                dst = DATA_DIR / name / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                files[rel] = {"sha256": _sha256_file(src), "bytes": src.stat().st_size, "mtime_utc": mtime}
            elif kind == "h5-calibration-snapshot":
                # Large session files are not copied; a verbatim JSON export of
                # root attrs and /calibration_snapshot is snapshotted instead.
                from h5_extract import EXTRACTOR_ID, write_extract  # noqa: PLC0415
                out_rel = posixpath.splitext(rel)[0] + ".calibration_snapshot.json"
                dst = DATA_DIR / name / out_rel
                rec = write_extract(src, dst)
                files[out_rel] = {"sha256": _sha256_file(dst), "bytes": dst.stat().st_size, "mtime_utc": mtime,
                                  "extracted_from": rel, "source_sha256": rec["source_sha256"],
                                  "source_bytes": rec["source_bytes"], "extractor": EXTRACTOR_ID}
            elif kind == "h5-tracking-window":
                from h5_extract import TRACKING_EXTRACTOR_ID, write_tracking_window  # noqa: PLC0415
                out_rel = posixpath.splitext(rel)[0] + ".tracking_window.json"
                dst = DATA_DIR / name / out_rel
                rec = write_tracking_window(src, spec["window"], dst)
                files[out_rel] = {"sha256": _sha256_file(dst), "bytes": dst.stat().st_size, "mtime_utc": mtime,
                                  "extracted_from": rel, "source_sha256": rec["source_sha256"],
                                  "source_bytes": rec["source_bytes"], "extractor": TRACKING_EXTRACTOR_ID,
                                  "window": spec["window"]}
            else:
                sys.exit(f"data source {name}: unknown kind {kind!r}")
        lock["data"][name] = {"local_path": str(base), "role": spec.get("role", ""), "kind": kind, "files": files}
        print(f"{name:16} {kind} snapshot of {len(files)} file(s) from {base}")
    for name, spec in sources.items():
        repo = Path(spec["local_path"])
        commit = _git(repo, "rev-parse", "HEAD").strip()
        branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
        dirty = bool(_git(repo, "status", "--porcelain").strip())
        try:
            remote = _git(repo, "remote", "get-url", "origin").strip()
        except subprocess.CalledProcessError:
            remote = ""
        pushed = bool(_git(repo, "branch", "-r", "--contains", commit).strip())
        lock["sources"][name] = {
            "commit": commit,
            "branch": branch,
            "remote": remote,
            "web": _remote_to_https(remote),
            "commit_on_remote": pushed,
            "working_tree_dirty": dirty,
            "commit_date": _git(repo, "show", "-s", "--format=%cI", commit).strip(),
        }
        flag = " (uncommitted local changes ignored)" if dirty else ""
        push = "" if pushed else " (commit not on any remote branch)"
        print(f"{name:16} {commit[:12]} {branch}{flag}{push}")
    LOCK_JSON.write_text(json.dumps(lock, indent=2) + "\n")
    print(f"wrote {LOCK_JSON.relative_to(ROOT)}")


def load_lock() -> dict[str, Any]:
    if not LOCK_JSON.exists():
        sys.exit("sources.lock.json missing: run `python3 tools/explain.py lock` first")
    return json.loads(LOCK_JSON.read_text())


class SourceReader:
    """Reads files from a source repo at its locked commit, never the worktree."""

    def __init__(self) -> None:
        self.sources = load_sources()
        self.data_sources = load_data_sources()
        self.lock = load_lock()
        self._cache: dict[tuple[str, str], list[str]] = {}

    def is_data(self, source: str) -> bool:
        if source in self.data_sources:
            return True
        if source in self.sources:
            return False
        raise KeyError(f"unknown source {source!r}; declare it in sources.yaml")

    def commit(self, source: str) -> str:
        if self.is_data(source):
            return "snapshot"
        return self.lock["sources"][source]["commit"]

    def data_sha256(self, source: str, path: str) -> str:
        return self.lock["data"][source]["files"][path]["sha256"]

    def web(self, source: str) -> str | None:
        if self.is_data(source):
            return None
        return self.lock["sources"][source].get("web")

    def lines(self, source: str, path: str) -> list[str]:
        key = (source, path)
        if key not in self._cache:
            if self.is_data(source):
                snap = DATA_DIR / source / path
                if not snap.is_file():
                    raise FileNotFoundError(f"{snap} missing: run `lock` to snapshot data source {source}")
                actual = _sha256_file(snap)
                if actual != self.data_sha256(source, path):
                    raise ValueError(f"data snapshot {snap} does not match sources.lock.json; run `lock`")
                text = snap.read_text()
            else:
                repo = Path(self.sources[source]["local_path"])
                text = _git(repo, "show", f"{self.commit(source)}:{path}")
            self._cache[key] = text.split("\n")
            if self._cache[key] and self._cache[key][-1] == "":
                self._cache[key].pop()
        return self._cache[key]

    def text(self, source: str, path: str) -> str:
        return "\n".join(self.lines(source, path))

    def blob_url(self, source: str, path: str, start: int, end: int) -> str | None:
        if self.is_data(source):
            return f"data/{source}/{path}"
        web = self.web(source)
        if not web:
            return None
        return f"{web}/blob/{self.commit(source)}/{path}#L{start}-L{end}"


# ---------------------------------------------------------------------------
# Excerpt extraction
# ---------------------------------------------------------------------------


@dataclass
class Excerpt:
    id: str
    source: str
    path: str
    start: int  # 1-indexed inclusive
    end: int  # 1-indexed inclusive
    kind: str  # "markdown" | "code"
    language: str
    text: str
    selector: dict[str, Any]
    note: str = ""  # curator note kept out of the content column

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")


def _heading_spans(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line_index, level, heading_text) for ATX headings outside code fences."""
    spans = []
    fence: str | None = None
    for i, line in enumerate(lines):
        m = _FENCE_RE.match(line)
        if m:
            marker = m.group(2)
            if fence is None:
                fence = marker[0]
            elif marker[0] == fence:
                fence = None
            continue
        if fence:
            continue
        h = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if h:
            spans.append((i, len(h.group(1)), h.group(2)))
    return spans


def extract_md_section(reader: SourceReader, source: str, path: str, heading: str) -> tuple[int, int]:
    lines = reader.lines(source, path)
    spans = _heading_spans(lines)
    m = re.match(r"^(#*)\s*(.*?)\s*$", heading)
    want_level, want_text = len(m.group(1)), m.group(2)
    matches = [s for s in spans if s[2] == want_text and (not want_level or s[1] == want_level)]
    if not matches:
        available = "\n  ".join(f"{'#' * lvl} {txt}" for _, lvl, txt in spans)
        raise KeyError(f"heading {heading!r} not found in {source}:{path}. Headings:\n  {available}")
    if len(matches) > 1:
        raise KeyError(f"heading {heading!r} is ambiguous in {source}:{path}")
    idx, level, _ = matches[0]
    end = len(lines)
    for j, lvl, _ in spans:
        if j > idx and lvl <= level:
            end = j
            break
    while end > idx + 1 and not lines[end - 1].strip():
        end -= 1
    return idx + 1, end


def _json_block_end(lines: list[str], start: int) -> int:
    """Index of the line closing the JSON value that begins on `start` (brace/bracket matching, string-aware)."""
    depth = 0
    in_str = False
    esc = False
    opened = False
    for i in range(start, len(lines)):
        for ch in lines[i]:
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch in "{[":
                depth += 1
                opened = True
            elif ch in "}]":
                depth -= 1
        if opened and depth == 0:
            return i
        if not opened and i > start:
            return start  # scalar value on one line
    raise ValueError("unterminated JSON block")


def extract_json_path(lines: list[str], path: str) -> tuple[int, int]:
    """Line range of the value at a dotted key path in an indent=2 pretty-printed JSON file."""
    start, end = 0, len(lines) - 1
    for depth, key in enumerate(path.split("."), start=1):
        pat = re.compile(r'^' + ' ' * (2 * depth) + r'"' + re.escape(key) + r'": ')
        found = None
        for i in range(start, end + 1):
            if pat.match(lines[i]):
                found = i
                break
        if found is None:
            raise KeyError(f"json_path {path!r}: key {key!r} not found at depth {depth}")
        start, end = found, _json_block_end(lines, found)
    return start + 1, end + 1


def extract_py_symbol(reader: SourceReader, source: str, path: str, symbol: str) -> tuple[int, int]:
    text = "\n".join(reader.lines(source, path)) + "\n"
    tree = ast.parse(text)
    parts = symbol.split(".")
    node: Any = tree
    for part in parts:
        found = None
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and child.name == part:
                found = child
                break
            if isinstance(child, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == part for t in child.targets
            ):
                found = child
                break
        if found is None:
            raise KeyError(f"symbol {symbol!r} not found in {source}:{path}")
        node = found
    start = node.lineno
    if getattr(node, "decorator_list", None):
        start = min(d.lineno for d in node.decorator_list)
    return start, node.end_lineno


_LANG_BY_EXT = {
    ".py": "python",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".cu": "cuda",
    ".md": "markdown",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".fbs": "flatbuffers",
}


def build_excerpt(reader: SourceReader, spec: dict[str, Any]) -> Excerpt:
    source = spec["source"]
    path = spec["path"]
    ext = posixpath.splitext(path)[1]
    language = _LANG_BY_EXT.get(ext, "")
    lines = reader.lines(source, path)

    if "heading" in spec:
        start, end = extract_md_section(reader, source, path, spec["heading"])
        kind = "markdown"
    elif "symbol" in spec:
        start, end = extract_py_symbol(reader, source, path, spec["symbol"])
        kind = "code"
    elif "json_path" in spec:
        start, end = extract_json_path(lines, spec["json_path"])
        kind = "code"
    elif "lines" in spec:
        if spec["lines"] == "all":
            start, end = 1, len(lines)
        else:
            start, end = spec["lines"]
        kind = "markdown" if ext == ".md" else "code"
    else:
        raise ValueError(f"excerpt {spec.get('id')} needs heading, symbol, or lines")

    if not (1 <= start <= end <= len(lines)):
        raise ValueError(f"excerpt {spec.get('id')}: lines {start}-{end} out of range (file has {len(lines)})")
    text = "\n".join(lines[start - 1 : end])

    anchors = spec.get("anchor")
    if anchors:
        for anchor in [anchors] if isinstance(anchors, str) else anchors:
            if anchor not in text:
                raise ValueError(
                    f"excerpt {spec.get('id')}: anchor {anchor!r} not present in "
                    f"{source}:{path} lines {start}-{end}; the source moved"
                )

    selector = {k: v for k, v in spec.items() if k in ("heading", "symbol", "json_path", "lines", "anchor")}
    return Excerpt(
        id=spec["id"],
        source=source,
        path=path,
        start=start,
        end=end,
        kind=kind,
        language=language,
        text=text,
        selector=selector,
        note=spec.get("note", ""),
    )


# ---------------------------------------------------------------------------
# Derived diagrams (parsed from excerpt text, never authored)
# ---------------------------------------------------------------------------


def _code_fence_bodies(text: str) -> list[str]:
    bodies, cur, fence = [], [], None
    for line in text.split("\n"):
        m = _FENCE_RE.match(line)
        if m and (fence is None or m.group(2)[0] == fence):
            if fence is None:
                fence, cur = m.group(2)[0], []
            else:
                bodies.append("\n".join(cur))
                fence = None
            continue
        if fence is not None:
            cur.append(line)
    return bodies


_EQ_RE = re.compile(r"^\s*(p_[A-Za-z0-9_]+)\s*(=|~)\s*(.+?)\s*$")


def parse_transform_chain(text: str) -> dict[str, Any]:
    """Nodes are `p_<frame>` variables, edges are the equations relating them."""
    nodes: list[str] = []
    edges: list[dict[str, str]] = []
    defs: list[str] = []
    for body in _code_fence_bodies(text):
        for line in body.split("\n"):
            m = _EQ_RE.match(line)
            if not m:
                if re.match(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*\(", line):
                    defs.append(line.strip())
                continue
            lhs, op, rhs = m.groups()
            rhs_vars = [v for v in re.findall(r"p_[A-Za-z0-9_]+", rhs) if v != lhs]
            for v in (lhs, *rhs_vars):
                if v not in nodes:
                    nodes.append(v)
            for v in rhs_vars:
                edges.append({"from": v, "to": lhs, "op": op, "label": line.strip()})
    return {"nodes": nodes, "edges": edges, "definitions": defs}


def render_transform_chain_svg(chain: dict[str, Any], order: list[str] | None) -> str:
    nodes = list(chain["nodes"])
    if order:
        missing = [n for n in order if n not in nodes]
        if missing:
            raise ValueError(f"diagram order names nodes not in the excerpt: {missing}")
        nodes = [n for n in order] + [n for n in nodes if n not in order]
    if not nodes:
        return "<p class='warn'>No <code>p_*</code> equations found in the excerpt.</p>"

    box_w, box_h, gap, pad = 260, 54, 150, 24
    width = pad * 2 + len(nodes) * box_w + (len(nodes) - 1) * gap
    above = [e for e in chain["edges"] if nodes.index(e["from"]) < nodes.index(e["to"])]
    below = [e for e in chain["edges"] if nodes.index(e["from"]) > nodes.index(e["to"])]
    lane_h = 64
    top_h = pad + lane_h * max(1, len(above))
    height = top_h + box_h + lane_h * max(1, len(below)) + pad
    xs = {n: pad + i * (box_w + gap) for i, n in enumerate(nodes)}
    y_box = top_h

    out = [
        f'<svg class="chain" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="Transform chain parsed from the excerpt above">',
        "<defs>"
        '<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
        '<path d="M0 0L10 5L0 10z" fill="currentColor"/></marker></defs>',
    ]
    for n in nodes:
        x = xs[n]
        out.append(
            f'<rect x="{x}" y="{y_box}" width="{box_w}" height="{box_h}" rx="8" class="node"/>'
            f'<text x="{x + box_w / 2}" y="{y_box + box_h / 2 + 5}" text-anchor="middle" class="node-label">{html.escape(n)}</text>'
        )

    def draw(edges: list[dict[str, str]], upward: bool) -> None:
        for k, e in enumerate(edges):
            x1 = xs[e["from"]] + box_w / 2
            x2 = xs[e["to"]] + box_w / 2
            lane = (k + 1) * lane_h
            if upward:
                y0, yl = y_box, y_box - lane + 18
            else:
                y0, yl = y_box + box_h, y_box + box_h + lane - 18
            path = f"M{x1} {y0} L{x1} {yl} L{x2} {yl} L{x2} {y0}"
            out.append(f'<path d="{path}" class="edge" marker-end="url(#arr)"/>')
            ty = yl - 8 if upward else yl + 18
            out.append(
                f'<text x="{(x1 + x2) / 2}" y="{ty}" text-anchor="middle" class="edge-label">'
                f"{html.escape(e['label'])}</text>"
            )

    draw(above, upward=True)
    draw(below, upward=False)
    out.append("</svg>")
    defs = chain["definitions"]
    legend = ""
    if defs:
        legend = "<p class='diagram-note'>Also defined in the excerpt: " + ", ".join(
            f"<code>{html.escape(d.split('=')[0].strip())}</code>" for d in defs
        ) + ".</p>"
    return "".join(out) + legend


_BULLET_RE = re.compile(r"^(\s*)[-*]\s+(.*)$")


def parse_bullet_cards(text: str) -> list[dict[str, Any]]:
    """Top-level bullets that start with a `code` term become cards; nested bullets become rows."""
    cards: list[dict[str, Any]] = []
    for line in text.split("\n"):
        m = _BULLET_RE.match(line)
        if not m:
            continue
        indent, body = len(m.group(1)), m.group(2).strip()
        if indent == 0:
            term = re.match(r"^`([^`]+)`\s*(.*)$", body)
            if term:
                cards.append({"term": term.group(1), "tail": term.group(2), "rows": []})
            else:
                cards.append({"term": None, "tail": body, "rows": []})
        elif cards:
            cards[-1]["rows"].append(body)
    return [c for c in cards if c["term"]]


def render_bullet_cards(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return "<p class='warn'>No bullet definitions found in the excerpt.</p>"
    out = ['<div class="cards">']
    for c in cards:
        out.append(f'<div class="card"><h4><code>{html.escape(c["term"])}</code></h4>')
        if c["tail"]:
            out.append(f"<p>{_inline_md(c['tail'])}</p>")
        if c["rows"]:
            out.append("<ul>" + "".join(f"<li>{_inline_md(r)}</li>" for r in c["rows"]) + "</ul>")
        out.append("</div>")
    out.append("</div>")
    return "".join(out)


def _inline_md(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

CSS = """
:root{--bg:#fafaf8;--fg:#1b1b1b;--muted:#5b5b5b;--line:#d9d6cf;--card:#ffffff;--accent:#2a5db0;--code:#f1efe9;
 --orange:#c9641b;--citrus:#7a9a01;--palette:#7a3fb5;--contracts:#2a5db0}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15161a;--fg:#e8e6e1;--muted:#a3a39c;--line:#33353c;--card:#1d1f25;--accent:#8ab4ff;--code:#23252c}}
:root[data-theme=dark]{--bg:#15161a;--fg:#e8e6e1;--muted:#a3a39c;--line:#33353c;--card:#1d1f25;--accent:#8ab4ff;--code:#23252c}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 80px}
a{color:var(--accent)}
h1{font-size:1.9rem;line-height:1.2;margin:.2em 0 .3em}h2{font-size:1.35rem;margin:2.2em 0 .6em;padding-top:.4em;border-top:1px solid var(--line)}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em}
code{background:var(--code);padding:.1em .35em;border-radius:4px}
pre{background:var(--code);padding:12px 14px;border-radius:8px;overflow-x:auto;line-height:1.45}pre code{background:none;padding:0}
.lede{color:var(--muted);margin:0 0 1em}
.rule{border:1px dashed var(--line);border-radius:8px;padding:10px 14px;color:var(--muted);font-size:.92rem}
.excerpt{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:18px 0;overflow:hidden}
.excerpt>header{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;padding:8px 14px;border-bottom:1px solid var(--line);font-size:.84rem;color:var(--muted)}
.excerpt>header .path{font-family:ui-monospace,Menlo,Consolas,monospace;word-break:break-all}
.excerpt>.body{padding:6px 16px 14px}
.excerpt .body h1,.excerpt .body h2,.excerpt .body h3,.excerpt .body h4{font-size:1.02rem;margin:1em 0 .4em;border:0;padding:0}
.excerpt .body table{border-collapse:collapse;display:block;overflow-x:auto;max-width:100%;font-size:.92rem}
.excerpt .body th,.excerpt .body td{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-weight:600;color:#fff;font-size:.78rem;letter-spacing:.02em}
.badge-agent-contracts{background:var(--contracts)}.badge-orange{background:var(--orange)}.badge-citrus{background:var(--citrus)}.badge-palette{background:var(--palette)}.badge-data{background:#5f6368}
svg.rig{width:100%;height:auto;display:block;color:var(--fg);margin:8px 0}
svg.rig .frame{fill:var(--code);stroke:var(--fg);stroke-width:1.2}
svg.rig .arena{fill:none;stroke-width:1.6}
svg.rig .exp{fill-opacity:.12;stroke-width:1.2}
svg.rig .cam{fill:none;stroke-width:1.2;stroke-dasharray:5 4}
svg.rig .axis{stroke:currentColor;stroke-width:1.4}
svg.rig .title{font:600 13px ui-monospace,Menlo,Consolas,monospace;fill:var(--fg)}
svg.rig .small{font:11px ui-monospace,Menlo,Consolas,monospace;fill:var(--muted);paint-order:stroke;stroke:var(--bg);stroke-width:4px;stroke-linejoin:round}
svg.rig .axis-label{font:11px ui-monospace,Menlo,Consolas,monospace;fill:var(--fg)}
table.numbers{border-collapse:collapse;font-size:.82rem;display:block;overflow-x:auto;margin:8px 0}
table.numbers th,table.numbers td{border:1px solid var(--line);padding:4px 7px;text-align:left;vertical-align:top;white-space:nowrap}
table.numbers th small{font-weight:400;color:var(--muted)}
.note{font-size:.9rem;color:var(--muted);margin:-8px 0 14px 2px}
.diagram{margin:14px 0 6px}.diagram-note{color:var(--muted);font-size:.9rem}
svg.chain{width:100%;height:auto;display:block;color:var(--fg)}
svg.chain .node{fill:var(--card);stroke:var(--accent);stroke-width:2}
svg.chain .node-label{font:600 15px ui-monospace,Menlo,Consolas,monospace;fill:var(--fg)}
svg.chain .edge{fill:none;stroke:currentColor;stroke-width:1.6}
svg.chain .edge-label{font:12.5px ui-monospace,Menlo,Consolas,monospace;fill:var(--muted);paint-order:stroke;stroke:var(--bg);stroke-width:6px;stroke-linejoin:round}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.card{border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:var(--card)}
.card h4{margin:0 0 6px;font-size:1rem}.card p{margin:.3em 0}.card ul{margin:.3em 0 0;padding-left:18px;font-size:.92rem}
.toc{padding-left:18px}.warn{color:var(--orange)}
table.lock{border-collapse:collapse;font-size:.9rem;display:block;overflow-x:auto}
table.lock th,table.lock td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
footer{margin-top:60px;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line);padding-top:12px}
"""


def _md_renderer():
    if MarkdownIt is None:
        return None
    return MarkdownIt("commonmark", {"html": False, "linkify": False}).enable("table")


def _rewrite_relative_links(html_text: str, reader: SourceReader, source: str, path: str) -> str:
    web = reader.web(source)
    if not web:
        return html_text
    base_dir = posixpath.dirname(path)
    commit = reader.commit(source)

    def repl(m: re.Match[str]) -> str:
        href = m.group(1)
        if re.match(r"^(https?:|mailto:|#)", href):
            return m.group(0)
        target = posixpath.normpath(posixpath.join(base_dir, href))
        return f'href="{web}/blob/{commit}/{target}"'

    return re.sub(r'href="([^"]+)"', repl, html_text)


def render_excerpt_body(ex: Excerpt, reader: SourceReader, md) -> str:
    if ex.kind == "markdown" and md is not None:
        body = md.render(ex.text)
        return _rewrite_relative_links(body, reader, ex.source, ex.path)
    lang = f' class="language-{ex.language}"' if ex.language else ""
    return f"<pre><code{lang}>{html.escape(ex.text)}</code></pre>"


def render_excerpt(ex: Excerpt, reader: SourceReader, md) -> str:
    url = reader.blob_url(ex.source, ex.path, ex.start, ex.end)
    lines = f"L{ex.start}–L{ex.end}" if ex.start != ex.end else f"L{ex.start}"
    if reader.is_data(ex.source):
        badge = f'<span class="badge badge-data">data · {html.escape(ex.source)}</span>'
        shown_path = f"{reader.lock['data'][ex.source]['local_path']}/{ex.path}"
        link = f'<a href="{url}">snapshot sha256 {reader.data_sha256(ex.source, ex.path)[:10]}</a>'
    else:
        badge = f'<span class="badge badge-{ex.source}">{ex.source}</span>'
        shown_path = ex.path
        link = f'<a href="{url}">view at {reader.commit(ex.source)[:10]}</a>' if url else ""
    sel = next(iter(ex.selector.items()), None)
    sel_txt = ""
    if sel:
        k, v = sel
        sel_txt = f"<span>{k}: <code>{html.escape(str(v))}</code></span>"
    note = f'<p class="note">{_inline_md(ex.note)}</p>' if ex.note else ""
    return (
        f'<section class="excerpt" id="{html.escape(ex.id)}">'
        f'<header>{badge}'
        f'<span class="path">{html.escape(shown_path)}</span><span>{lines}</span>{sel_txt}{link}</header>'
        f'<div class="body">{render_excerpt_body(ex, reader, md)}</div></section>{note}'
    )


def render_diagram(spec: dict[str, Any], excerpts: dict[str, Excerpt], reader: SourceReader) -> str:
    kind = spec["kind"]
    src = excerpts[spec["from"]]
    inputs = [src]
    if kind == "transform-chain":
        chain = parse_transform_chain(src.text)
        svg = render_transform_chain_svg(chain, spec.get("order"))
    elif kind == "bullet-cards":
        svg = render_bullet_cards(parse_bullet_cards(src.text))
    elif kind == "tracking-replay":
        calib = excerpts[spec["calibration"]]
        inputs.append(calib)
        svg = render_tracking_replay(
            reader.text(src.source, src.path), reader.text(calib.source, calib.path), spec.get("player_id", "replay")
        )
    elif kind == "h5-rig-canvas":
        # One Citrus session extract per arena; each must be quoted on the page.
        texts = []
        for eid in spec["inputs"]:
            x = excerpts[eid]
            if x is not src:
                inputs.append(x)
            texts.append(reader.text(x.source, x.path))
        svg = render_h5_rig_canvas(texts)
    elif kind == "rig-canvas":
        # The canvas JSON and each homography sidecar must be quoted on the page;
        # the diagram reads those same files in full. Camera id comes from the
        # sidecar filename `homography_<arena>_<camera_id>.yml` (Citrus naming).
        homographies: dict[str, str] = {}
        for hid in spec.get("homographies", []):
            hx = excerpts[hid]
            inputs.append(hx)
            m = re.match(r"^homography_.*_(\d+)\.ya?ml$", posixpath.basename(hx.path))
            if not m:
                raise ValueError(f"cannot read camera id from sidecar name {hx.path}")
            homographies[m.group(1)] = reader.text(hx.source, hx.path)
        svg = render_rig_canvas(reader.text(src.source, src.path), homographies)
    else:
        raise ValueError(f"unknown diagram kind {kind!r}")
    cites = ", ".join(
        f'<a href="#{html.escape(x.id)}">{html.escape(x.id)}</a> ({html.escape(x.source)}: <code>{html.escape(x.path)}</code>)'
        for x in inputs
    )
    return (
        f'<figure class="diagram">{svg}'
        f'<figcaption class="diagram-note">Derived automatically from {cites}.</figcaption></figure>'
    )


def page_shell(title: str, body: str, lock: dict[str, Any], depth: int = 0) -> str:
    home = "../" * depth + "index.html"
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>"
        f"<nav><a href='{home}'>All explainers</a></nav>{body}"
        f"<footer>Generated from sources locked at {html.escape(lock['locked_at_utc'])}. "
        "Every block above is a verbatim excerpt; nothing on this page was written by hand.</footer>"
        "</main></body></html>"
    )


def build_explainer(
    spec: dict[str, Any], reader: SourceReader, md, manifest: dict[str, Any]
) -> tuple[str, str]:
    """Returns (html, context_markdown)."""
    excerpts: dict[str, Excerpt] = {}
    html_parts = [f"<h1>{html.escape(spec['title'])}</h1>"]
    if spec.get("question"):
        html_parts.append(f"<p class='lede'>{html.escape(spec['question'])}</p>")
    html_parts.append(
        "<p class='rule'>Everything below is quoted verbatim from a source repository at a pinned commit. "
        "Section headings are the curator's only words; diagrams are parsed from the quoted text.</p>"
    )
    toc = []
    body_parts = []
    ctx = [f"# {spec['title']}", "", f"Question: {spec.get('question', '')}".rstrip(), ""]
    ctx.append(
        "Curated context bundle. Each block is a verbatim excerpt from a source repository "
        "at the commit named in its header. Contract precedence rules inside the excerpts still apply."
    )
    ctx.append("")

    for si, section in enumerate(spec["sections"], 1):
        anchor = f"s{si}"
        toc.append(f"<li><a href='#{anchor}'>{html.escape(section['title'])}</a></li>")
        body_parts.append(f"<h2 id='{anchor}'>{html.escape(section['title'])}</h2>")
        ctx.append(f"## {section['title']}")
        ctx.append("")
        for item in section["items"]:
            if "diagram" in item:
                body_parts.append(render_diagram(item["diagram"], excerpts, reader))
                continue
            ex = build_excerpt(reader, item)
            if ex.id in excerpts:
                raise ValueError(f"duplicate excerpt id {ex.id}")
            excerpts[ex.id] = ex
            body_parts.append(render_excerpt(ex, reader, md))
            manifest["excerpts"][f"{spec['slug']}:{ex.id}"] = {
                "source": ex.source,
                "commit": reader.commit(ex.source),
                "file_sha256": reader.data_sha256(ex.source, ex.path) if reader.is_data(ex.source) else None,
                "path": ex.path,
                "start": ex.start,
                "end": ex.end,
                "selector": ex.selector,
                "sha256": ex.sha256,
            }
            url = reader.blob_url(ex.source, ex.path, ex.start, ex.end)
            if reader.is_data(ex.source):
                ctx.append(
                    f"### {ex.id}\n\nsource: local data snapshot {ex.source}, sha256 {reader.data_sha256(ex.source, ex.path)}  \n"
                    f"path: {reader.lock['data'][ex.source]['local_path']}/{ex.path} (lines {ex.start}-{ex.end})"
                )
            else:
                ctx.append(
                    f"### {ex.id}\n\nsource: {ex.source} @ {reader.commit(ex.source)}  \n"
                    f"path: {ex.path} (lines {ex.start}-{ex.end})"
                    + (f"  \nurl: {url}" if url else "")
                )
            if ex.note:
                ctx.append(f"curator note: {ex.note}")
            ctx.append("")
            if ex.kind == "markdown":
                ctx.append(ex.text)
            else:
                ctx.append(f"```{ex.language}\n{ex.text}\n```")
            ctx.append("")

    html_parts.append(f"<ol class='toc'>{''.join(toc)}</ol>")
    html_parts.extend(body_parts)
    return "".join(html_parts), "\n".join(ctx).rstrip() + "\n"


def render_index(explainers: list[dict[str, Any]], lock: dict[str, Any], sources: dict[str, Any]) -> str:
    items = "".join(
        f"<li><a href='{e['slug']}.html'>{html.escape(e['title'])}</a>"
        + (f" <span class='lede'>— {html.escape(e['question'])}</span>" if e.get("question") else "")
        + "</li>"
        for e in explainers
    )
    rows = []
    for name, info in lock["sources"].items():
        web = info.get("web")
        commit = info["commit"]
        link = f"<a href='{web}/commit/{commit}'>{commit[:12]}</a>" if web else commit[:12]
        flags = []
        if not info.get("commit_on_remote", True):
            flags.append("commit not on remote")
        if info.get("working_tree_dirty"):
            flags.append("local uncommitted changes ignored")
        rows.append(
            f"<tr><td><span class='badge badge-{name}'>{name}</span></td>"
            f"<td>{html.escape(sources[name].get('role', ''))}</td><td>{link}</td>"
            f"<td><code>{html.escape(info['branch'])}</code></td><td>{html.escape(info['commit_date'][:10])}</td>"
            f"<td>{html.escape('; '.join(flags))}</td></tr>"
        )
    data_rows = []
    for name, info in lock.get("data", {}).items():
        files = "<br>".join(
            f"<a href='data/{name}/{html.escape(rel)}'><code>{html.escape(rel)}</code></a> <small>{meta['sha256'][:10]}</small>"
            for rel, meta in info["files"].items()
        )
        data_rows.append(
            f"<tr><td><span class='badge badge-data'>data · {html.escape(name)}</span></td>"
            f"<td>{html.escape(info.get('role', ''))}</td><td><code>{html.escape(info['local_path'])}</code></td><td>{files}</td></tr>"
        )
    data_table = (
        "<h2>Snapshotted local data</h2><p class='lede'>Rig configuration files that live outside git. "
        "They are copied verbatim and pinned by sha256 at lock time.</p>"
        "<table class='lock'><thead><tr><th>Snapshot</th><th>Role</th><th>Original location</th><th>Files</th></tr></thead>"
        f"<tbody>{''.join(data_rows)}</tbody></table>"
        if data_rows
        else ""
    )
    body = (
        "<h1>Human explainers</h1>"
        "<p class='lede'>Visual explainers generated from the contracts and code that actually run the rigs. "
        "No prose is authored here; the pages quote sources at pinned commits.</p>"
        f"<h2>Explainers</h2><ul>{items}</ul>"
        "<h2>Pinned sources</h2><table class='lock'><thead><tr><th>Source</th><th>Role</th><th>Commit</th>"
        f"<th>Branch</th><th>Date</th><th>Flags</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
        + data_table
        + "<h2>Agent context bundles</h2><p>The same excerpts, as plain markdown for agents: "
        + ", ".join(f"<a href='context/{e['slug']}.md'><code>context/{e['slug']}.md</code></a>" for e in explainers)
        + ".</p>"
    )
    return page_shell("Human explainers", body, lock)


def load_explainers() -> list[dict[str, Any]]:
    specs = []
    for path in sorted(EXPLAINERS_DIR.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        spec.setdefault("slug", path.stem)
        specs.append(spec)
    return specs


def cmd_build(_: argparse.Namespace) -> None:
    reader = SourceReader()
    md = _md_renderer()
    if md is None:
        print("warning: markdown-it-py not installed; markdown excerpts render as plain <pre>", file=sys.stderr)
    SITE_DIR.mkdir(exist_ok=True)
    CONTEXT_DIR.mkdir(exist_ok=True)
    manifest: dict[str, Any] = {"locked_at_utc": reader.lock["locked_at_utc"], "excerpts": {}}
    explainers = load_explainers()
    for spec in explainers:
        body, ctx = build_explainer(spec, reader, md, manifest)
        (SITE_DIR / f"{spec['slug']}.html").write_text(page_shell(spec["title"], body, reader.lock))
        (CONTEXT_DIR / f"{spec['slug']}.md").write_text(ctx)
        n = sum(1 for k in manifest["excerpts"] if k.startswith(spec["slug"] + ":"))
        print(f"built site/{spec['slug']}.html and context/{spec['slug']}.md ({n} excerpts)")
    (SITE_DIR / "index.html").write_text(render_index(explainers, reader.lock, reader.sources))
    (SITE_DIR / ".nojekyll").write_text("")
    if DATA_DIR.is_dir():
        shutil.copytree(DATA_DIR, SITE_DIR / "data", dirs_exist_ok=True)
    shutil.copytree(CONTEXT_DIR, SITE_DIR / "context", dirs_exist_ok=True)
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote site/index.html and {MANIFEST_JSON.relative_to(ROOT)}")


def cmd_verify(_: argparse.Namespace) -> None:
    reader = SourceReader()
    if not MANIFEST_JSON.exists():
        sys.exit("site/manifest.json missing: run build first")
    manifest = json.loads(MANIFEST_JSON.read_text())
    failures = 0
    seen = set()
    for name, info in reader.lock.get("data", {}).items():
        for rel, meta in info["files"].items():
            snap = DATA_DIR / name / rel
            if not snap.is_file() or _sha256_file(snap) != meta["sha256"]:
                print(f"FAIL data {name}/{rel}: snapshot missing or altered")
                failures += 1
            orig = Path(info["local_path"]) / rel
            if orig.is_file() and _sha256_file(orig) != meta["sha256"]:
                print(f"warn data {name}/{rel}: local original changed since lock (run `lock` to refresh)")
    for spec in load_explainers():
        for section in spec["sections"]:
            for item in section["items"]:
                if "diagram" in item:
                    continue
                key = f"{spec['slug']}:{item['id']}"
                seen.add(key)
                try:
                    ex = build_excerpt(reader, item)
                except Exception as exc:  # noqa: BLE001
                    print(f"FAIL {key}: {exc}")
                    failures += 1
                    continue
                rec = manifest["excerpts"].get(key)
                if rec is None:
                    print(f"FAIL {key}: not in manifest (rebuild)")
                    failures += 1
                elif rec["sha256"] != ex.sha256 or rec["commit"] != reader.commit(ex.source):
                    print(f"FAIL {key}: content or commit changed since build (rebuild)")
                    failures += 1
                else:
                    print(f"ok   {key}")
    stale = set(manifest["excerpts"]) - seen
    for key in sorted(stale):
        print(f"FAIL {key}: in manifest but no longer in any explainer (rebuild)")
        failures += 1
    if failures:
        sys.exit(f"{failures} excerpt(s) failed verification")
    print("all excerpts verified against locked sources")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("lock").set_defaults(fn=cmd_lock)
    sub.add_parser("build").set_defaults(fn=cmd_build)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
