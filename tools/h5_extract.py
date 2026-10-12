"""Export a Citrus session H5 `/calibration_snapshot` (and root attrs) to JSON.

This is a verbatim dump, not an interpretation: every attribute is copied,
small datasets are copied in full, and large datasets (embedded PNG buffers)
are replaced by their shape, dtype, byte count, and sha256 so the JSON stays
reviewable. Keys are sorted and the layout is fixed so a `json_path` selector
can quote a sub-tree by line range.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np

EXTRACTOR_ID = "human-explainers.h5_extract.calibration_snapshot.v1"
MAX_INLINE_ELEMENTS = 64
MAX_INLINE_TEXT_BYTES = 65536


def _scalar(v: Any) -> Any:
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, np.generic):
        v = v.item()
        return v.decode("utf-8", errors="replace") if isinstance(v, bytes) else v
    if isinstance(v, np.ndarray):
        return [_scalar(x) for x in v.tolist()] if v.ndim else _scalar(v[()])
    return v


def _attrs(obj: Any) -> dict[str, Any]:
    return {k: _scalar(v) for k, v in sorted(obj.attrs.items())}


def _dataset(ds: h5py.Dataset) -> dict[str, Any]:
    rec: dict[str, Any] = {"attrs": _attrs(ds), "dtype": str(ds.dtype), "shape": list(ds.shape)}
    if ds.dtype.kind in ("S", "O") or h5py.check_string_dtype(ds.dtype):
        raw = ds[()]
        if isinstance(raw, np.ndarray):
            raw = raw.tobytes() if raw.dtype.kind == "S" else raw.item()
        if isinstance(raw, str):
            raw = raw.encode()
        if len(raw) <= MAX_INLINE_TEXT_BYTES:
            rec["value"] = raw.decode("utf-8", errors="replace")
        else:
            rec["omitted"] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        return rec
    if ds.size <= MAX_INLINE_ELEMENTS:
        rec["value"] = _scalar(ds[()])
    else:
        data = ds[()].tobytes()
        rec["omitted"] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return rec


def _group(g: h5py.Group) -> dict[str, Any]:
    rec: dict[str, Any] = {"attrs": _attrs(g)}
    groups, datasets = {}, {}
    for name in sorted(g.keys()):
        child = g[name]
        if isinstance(child, h5py.Group):
            groups[name] = _group(child)
        else:
            datasets[name] = _dataset(child)
    if groups:
        rec["groups"] = groups
    if datasets:
        rec["datasets"] = datasets
    return rec


def extract(h5_path: Path) -> dict[str, Any]:
    sha = hashlib.sha256()
    with h5_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    with h5py.File(h5_path, "r") as h:
        out = {
            "extractor": EXTRACTOR_ID,
            "h5py_version": h5py.__version__,
            "source_file": str(h5_path),
            "source_sha256": sha.hexdigest(),
            "source_bytes": h5_path.stat().st_size,
            "root_attrs": _attrs(h),
            "calibration_snapshot": _group(h["calibration_snapshot"]) if "calibration_snapshot" in h else None,
        }
    return out


def write_extract(h5_path: Path, out_path: Path) -> dict[str, Any]:
    rec = extract(h5_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rec, indent=2, sort_keys=False) + "\n")
    return rec


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: h5_extract.py <session.h5> <out.json>")
    write_extract(Path(sys.argv[1]), Path(sys.argv[2]))
