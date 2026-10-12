"""Derive a rig layout diagram from a Citrus canvas JSON plus homography sidecars.

Nothing here is authored geometry: every rectangle, circle, and number comes
from the canvas JSON fields (named next to each value) and the OpenCV
`homography_matrix` in each sidecar. The only arithmetic is the arena origin
rule (`center - size / 2`) and applying the matrix in its declared direction
(`camera_view_px -> final_display_canvas_px`) or its inverse, exactly as the
contracts state.
"""

from __future__ import annotations

import html
import json
import math
import re
from typing import Any

Matrix = list[list[float]]
Point = tuple[float, float]


def parse_opencv_homography(text: str) -> Matrix:
    m = re.search(r"homography_matrix:.*?data:\s*\[(.*?)\]", text, re.S)
    if not m:
        raise ValueError("no homography_matrix data block in sidecar")
    vals = [float(v) for v in re.split(r"[\s,]+", m.group(1).strip()) if v]
    if len(vals) != 9:
        raise ValueError(f"expected 9 homography values, found {len(vals)}")
    return [vals[0:3], vals[3:6], vals[6:9]]


def invert3(h: Matrix) -> Matrix:
    a, b, c = h[0]
    d, e, f = h[1]
    g, hh, i = h[2]
    det = a * (e * i - f * hh) - b * (d * i - f * g) + c * (d * hh - e * g)
    if abs(det) < 1e-18:
        raise ValueError("homography is singular")
    adj = [
        [e * i - f * hh, -(b * i - c * hh), b * f - c * e],
        [-(d * i - f * g), a * i - c * g, -(a * f - c * d)],
        [d * hh - e * g, -(a * hh - b * g), a * e - b * d],
    ]
    return [[v / det for v in row] for row in adj]


def apply(h: Matrix, p: Point) -> Point:
    x, y = p
    u = h[0][0] * x + h[0][1] * y + h[0][2]
    v = h[1][0] * x + h[1][1] * y + h[1][2]
    w = h[2][0] * x + h[2][1] * y + h[2][2]
    return (u / w, v / w)


def _fmt(v: float) -> str:
    return f"{v:.1f}" if abs(v - round(v)) > 1e-6 else f"{int(round(v))}"


def _poly(points: list[Point], sx: float, sy: float, ox: float, oy: float) -> str:
    return " ".join(f"{ox + x * sx:.1f},{oy + y * sy:.1f}" for x, y in points)


ARENA_COLORS = ["#2a5db0", "#c9641b", "#7a9a01", "#7a3fb5", "#b03060", "#008080"]


def build_layout(canvas: dict[str, Any], homographies: dict[str, Matrix]) -> dict[str, Any]:
    """Pull the fields the diagram needs, keeping the JSON key of each value."""
    out: dict[str, Any] = {
        "canvas_name": canvas.get("canvas_name"),
        "canvas_width_px": canvas["canvas_width_px"],
        "canvas_height_px": canvas["canvas_height_px"],
        "arenas": [],
    }
    for arena_id, cfg in canvas["arenas"].items():
        cams = cfg.get("camera_calibrations") or []
        if not cams:
            continue
        cam = cams[0]
        cx, cy = cam["arena_center_x_px"], cam["arena_center_y_px"]
        w, hgt = cam["arena_width_px"], cam["arena_height_px"]
        origin = (cx - w / 2, cy - hgt / 2)  # GetArenaOriginXInCanvasPx / Y
        ex, ey = cfg["experimental_area_center_x_px"], cfg["experimental_area_center_y_px"]
        shape = cfg.get("experimental_area_shape", "CIRCLE")
        rec = {
            "arena_id": arena_id,
            "camera_id": str(cam["camera_id"]),
            "native_width_px": cam.get("native_width_px"),
            "native_height_px": cam.get("native_height_px"),
            "arena_center_px": (cx, cy),
            "arena_size_px": (w, hgt),
            "arena_origin_px": origin,
            "experimental_area_center_arena_px": (ex, ey),
            "experimental_area_center_canvas_px": (origin[0] + ex, origin[1] + ey),
            "experimental_area_shape": shape,
            "experimental_area_radius_px": cfg.get("experimental_area_radius_px"),
            "experimental_area_width_px": cfg.get("experimental_area_width_px"),
            "experimental_area_height_px": cfg.get("experimental_area_height_px"),
            "pixels_per_mm_camera": cam.get("pixels_per_mm_camera"),
            "pixels_per_mm_projector": cam.get("pixels_per_mm_projector"),
            "homography": homographies.get(str(cam["camera_id"])),
        }
        out["arenas"].append(rec)
    return out


def _exp_area_outline_arena(rec: dict[str, Any], n: int = 72) -> list[Point]:
    """Experimental-area boundary in arena_relative_canvas_px."""
    ex, ey = rec["experimental_area_center_arena_px"]
    if rec["experimental_area_shape"] == "CIRCLE" and rec["experimental_area_radius_px"]:
        r = rec["experimental_area_radius_px"]
        return [(ex + r * math.cos(2 * math.pi * k / n), ey + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    w, hgt = rec["experimental_area_width_px"] or 0, rec["experimental_area_height_px"] or 0
    return [(ex - w / 2, ey - hgt / 2), (ex + w / 2, ey - hgt / 2), (ex + w / 2, ey + hgt / 2), (ex - w / 2, ey + hgt / 2)]


def render_rig_canvas_svg(layout: dict[str, Any]) -> str:
    cw, ch = layout["canvas_width_px"], layout["canvas_height_px"]
    width = 960
    pad = 40
    s = (width - 2 * pad) / cw
    height = pad * 2 + ch * s + 44
    out = [
        f'<svg class="rig" viewBox="0 0 {width} {height:.0f}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="final_display_canvas_px layout of canvas {html.escape(str(layout["canvas_name"]))}">',
        "<defs><marker id='ax' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'>"
        "<path d='M0 0L10 5L0 10z' fill='currentColor'/></marker></defs>",
        f'<text x="{pad}" y="{pad - 14}" class="title">final_display_canvas_px — canvas_name={html.escape(str(layout["canvas_name"]))}, '
        f'canvas_width_px={cw}, canvas_height_px={ch}</text>',
        f'<text x="{pad}" y="{height - 20:.0f}" class="small">solid = arena region (arena_center ± arena_size/2) · '
        f'filled = experimental area · + = experimental_area_center</text>',
        f'<text x="{pad}" y="{height - 6:.0f}" class="small">dashed = camera native frame corners pushed through homography_matrix</text>',
        f'<rect x="{pad}" y="{pad}" width="{cw * s:.1f}" height="{ch * s:.1f}" class="frame"/>',
        # axes glyph at origin (0,0): +x right, +y down per the frame contract
        f'<line x1="{pad}" y1="{pad}" x2="{pad + 70}" y2="{pad}" class="axis" marker-end="url(#ax)"/>',
        f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{pad + 70}" class="axis" marker-end="url(#ax)"/>',
        f'<text x="{pad + 74}" y="{pad + 5}" class="axis-label">+x</text>',
        f'<text x="{pad + 6}" y="{pad + 82}" class="axis-label">+y</text>',
        f'<text x="{pad + 6}" y="{pad - 3}" class="axis-label">(0,0)</text>',
    ]
    for k, rec in enumerate(layout["arenas"]):
        color = ARENA_COLORS[k % len(ARENA_COLORS)]
        ox, oy = rec["arena_origin_px"]
        w, hgt = rec["arena_size_px"]
        out.append(
            f'<rect x="{pad + ox * s:.1f}" y="{pad + oy * s:.1f}" width="{w * s:.1f}" height="{hgt * s:.1f}" '
            f'class="arena" stroke="{color}"/>'
        )
        out.append(f'<circle cx="{pad + ox * s:.1f}" cy="{pad + oy * s:.1f}" r="3.5" fill="{color}"/>')
        out.append(
            f'<text x="{pad + ox * s + 5:.1f}" y="{pad + oy * s - 6:.1f}" class="small" fill="{color}">'
            f'{html.escape(rec["arena_id"])} origin ({_fmt(ox)}, {_fmt(oy)})</text>'
        )
        outline = [(ox + x, oy + y) for x, y in _exp_area_outline_arena(rec)]
        out.append(f'<polygon points="{_poly(outline, s, s, pad, pad)}" class="exp" stroke="{color}" fill="{color}"/>')
        ecx, ecy = rec["experimental_area_center_canvas_px"]
        out.append(f'<line x1="{pad + ecx * s - 5:.1f}" y1="{pad + ecy * s:.1f}" x2="{pad + ecx * s + 5:.1f}" y2="{pad + ecy * s:.1f}" stroke="{color}" stroke-width="1.2"/>')
        out.append(f'<line x1="{pad + ecx * s:.1f}" y1="{pad + ecy * s - 5:.1f}" x2="{pad + ecx * s:.1f}" y2="{pad + ecy * s + 5:.1f}" stroke="{color}" stroke-width="1.2"/>')
        if rec["homography"] and rec["native_width_px"] and rec["native_height_px"]:
            nw, nh = rec["native_width_px"], rec["native_height_px"]
            corners = [(0, 0), (nw, 0), (nw, nh), (0, nh)]
            quad = [apply(rec["homography"], c) for c in corners]
            out.append(f'<polygon points="{_poly(quad, s, s, pad, pad)}" class="cam" stroke="{color}"/>')
        out.append(
            f'<text x="{pad + (ox + w / 2) * s:.1f}" y="{pad + (oy + hgt) * s + 14:.1f}" class="small" text-anchor="middle" fill="{color}">'
            f'camera_id={html.escape(rec["camera_id"])}</text>'
        )
    out.append("</svg>")
    return "".join(out)


def render_camera_panels_svg(layout: dict[str, Any]) -> str:
    arenas = [a for a in layout["arenas"] if a["homography"] and a["native_width_px"]]
    if not arenas:
        return ""
    n = len(arenas)
    panel = 220
    gap = 22
    pad = 26
    width = pad * 2 + n * panel + (n - 1) * gap
    height = pad + 24 + panel + 40
    out = [
        f'<svg class="rig" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="camera_view_px of each camera with the arena region and experimental area mapped through inverse(H)">',
        f'<text x="{pad}" y="{pad - 8}" class="title">camera_view_px — arena region and experimental area mapped through inverse(H_camera_to_display)</text>',
    ]
    for k, rec in enumerate(arenas):
        color = ARENA_COLORS[k % len(ARENA_COLORS)]
        nw, nh = rec["native_width_px"], rec["native_height_px"]
        s = panel / max(nw, nh)
        x0 = pad + k * (panel + gap)
        y0 = pad + 24
        hinv = invert3(rec["homography"])
        out.append(f'<rect x="{x0}" y="{y0}" width="{nw * s:.1f}" height="{nh * s:.1f}" class="frame"/>')
        out.append(f'<line x1="{x0}" y1="{y0}" x2="{x0 + 34}" y2="{y0}" class="axis" marker-end="url(#ax)"/>')
        out.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + 34}" class="axis" marker-end="url(#ax)"/>')
        ox, oy = rec["arena_origin_px"]
        w, hgt = rec["arena_size_px"]
        arena_quad = [apply(hinv, p) for p in [(ox, oy), (ox + w, oy), (ox + w, oy + hgt), (ox, oy + hgt)]]
        out.append(f'<polygon points="{_poly(arena_quad, s, s, x0, y0)}" class="arena" stroke="{color}"/>')
        outline = [apply(hinv, (ox + x, oy + y)) for x, y in _exp_area_outline_arena(rec)]
        out.append(f'<polygon points="{_poly(outline, s, s, x0, y0)}" class="exp" stroke="{color}" fill="{color}"/>')
        ecx, ecy = apply(hinv, rec["experimental_area_center_canvas_px"])
        out.append(f'<circle cx="{x0 + ecx * s:.1f}" cy="{y0 + ecy * s:.1f}" r="2.5" fill="{color}"/>')
        out.append(
            f'<text x="{x0}" y="{y0 + panel + 16}" class="small">{html.escape(rec["camera_id"])} · {html.escape(rec["arena_id"])} · {nw}×{nh}</text>'
        )
        out.append(
            f'<text x="{x0}" y="{y0 + panel + 30}" class="small" fill="{color}">exp. center → ({_fmt(ecx)}, {_fmt(ecy)})</text>'
        )
    out.append("</svg>")
    return "".join(out)


def render_numbers_table(layout: dict[str, Any]) -> str:
    head = (
        "<tr><th>arena_id</th><th>camera_id</th>"
        "<th>arena_center_x_px, arena_center_y_px</th><th>arena_width_px × arena_height_px</th>"
        "<th>arena origin<br><small>center − size/2</small></th>"
        "<th>experimental_area_center_x_px, _y_px<br><small>arena_relative_canvas_px</small></th>"
        "<th>same point in final_display_canvas_px<br><small>origin + center</small></th>"
        "<th>same point in camera_view_px<br><small>inverse(H) · p_display</small></th>"
        "<th>pixels_per_mm_camera</th><th>pixels_per_mm_projector</th></tr>"
    )
    rows = []
    for rec in layout["arenas"]:
        cx, cy = rec["arena_center_px"]
        w, hgt = rec["arena_size_px"]
        ox, oy = rec["arena_origin_px"]
        ex, ey = rec["experimental_area_center_arena_px"]
        dx, dy = rec["experimental_area_center_canvas_px"]
        cam = "—"
        if rec["homography"]:
            kx, ky = apply(invert3(rec["homography"]), (dx, dy))
            cam = f"({_fmt(kx)}, {_fmt(ky)})"
        ppm_c = rec["pixels_per_mm_camera"]
        ppm_p = rec["pixels_per_mm_projector"]
        rows.append(
            f"<tr><td>{html.escape(rec['arena_id'])}</td><td>{html.escape(rec['camera_id'])}</td>"
            f"<td>({_fmt(cx)}, {_fmt(cy)})</td><td>{_fmt(w)} × {_fmt(hgt)}</td><td>({_fmt(ox)}, {_fmt(oy)})</td>"
            f"<td>({_fmt(ex)}, {_fmt(ey)})</td><td>({_fmt(dx)}, {_fmt(dy)})</td><td>{cam}</td>"
            f"<td>{'' if ppm_c is None else f'{ppm_c:.2f}'}</td><td>{'' if ppm_p is None else f'{ppm_p:.3f}'}</td></tr>"
        )
    return f"<table class='numbers'><thead>{head}</thead><tbody>{''.join(rows)}</tbody></table>"


def render_rig_canvas(canvas_json_text: str, homography_texts: dict[str, str]) -> str:
    canvas = json.loads(canvas_json_text)
    homographies = {cam: parse_opencv_homography(txt) for cam, txt in homography_texts.items()}
    layout = build_layout(canvas, homographies)
    return (
        render_rig_canvas_svg(layout)
        + render_camera_panels_svg(layout)
        + render_numbers_table(layout)
    )
