"""svg_layer.py -- read the drawn elements of a Stata ``graph export`` SVG,
one record per element, for the scheme-reach truth (WP-30 P1.4a).

``scripts/svg_truth.py`` reads circles, paths and rects; Stata 19.5 also
writes diamond, square-outline and triangle markers as ``<polygon>`` and an
``x`` or ``plus`` marker as two ``<line>`` elements, so this reader takes
every drawn shape.  It parses the file text with regular expressions as
data: no Stata import, no network, no ``eval``.
"""

from __future__ import annotations

import math
import re

_TAG = re.compile(r"<(circle|rect|polygon|path|line|use)\b([^>]*)>")
_DEFS = re.compile(r"<defs>.*?</defs>", re.S)
_DEF_PATH = re.compile(r'<path\b[^>]*\bid="([^"]+)"[^>]*\bd="([^"]*)"')
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_NUM = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
_VIEWBOX = re.compile(r'viewBox="([^"]*)"')


def _style(attrs: dict) -> dict:
    out = {}
    for part in attrs.get("style", "").split(";"):
        k, _, v = part.partition(":")
        if k.strip():
            out[k.strip().lower()] = v.strip()
    for k in ("fill", "stroke", "fill-opacity", "stroke-opacity",
              "stroke-width"):
        if k not in out and k in attrs:
            out[k] = attrs[k]
    return out


def _colour(v):
    v = (v or "").strip().lower()
    return v or None


def _float(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _points(kind: str, a: dict) -> "list[tuple[float, float]]":
    if kind == "circle":
        cx, cy, r = (_float(a.get(k)) or 0.0 for k in ("cx", "cy", "r"))
        return [(cx - r, cy - r), (cx + r, cy + r)]
    if kind == "rect":
        x, y, w, h = (_float(a.get(k)) or 0.0
                      for k in ("x", "y", "width", "height"))
        return [(x, y), (x + w, y + h)]
    if kind == "line":
        return [(_float(a.get("x1")) or 0.0, _float(a.get("y1")) or 0.0),
                (_float(a.get("x2")) or 0.0, _float(a.get("y2")) or 0.0)]
    if kind == "use":
        kind = "path"
    nums = [float(n) for n in _NUM.findall(
        a.get("points", "") if kind == "polygon" else a.get("d", ""))]
    return list(zip(nums[0::2], nums[1::2]))


def svg_elements(path: str) -> "list[dict]":
    """Every drawn ``<circle>``, ``<rect>``, ``<polygon>``, ``<path>`` and
    ``<line>`` of the SVG at *path*, in document order.

    Each record has ``kind``, ``fill``, ``fill_opacity``, ``stroke``,
    ``stroke_opacity``, ``stroke_width`` (colours lower-cased; an absent
    opacity is None), ``extent`` (the larger side of the element's
    geometry: a circle's 2r, a rect's larger side, the bounding box of
    points or of a path's coordinates), ``center`` and ``points``.  A rect
    covering more than half the canvas (the background) is left out.  An
    area, range area or band is a ``<path>`` in ``<defs>`` drawn by a
    ``<use>``: it is read as a path with the ``<use>``'s style."""
    with open(path, encoding="utf-8") as fh:
        txt = fh.read()
    defs = {}
    for blk in _DEFS.findall(txt):
        for pid, d in _DEF_PATH.findall(blk):
            defs[pid] = d
    txt = _DEFS.sub("", txt)
    m = _VIEWBOX.search(txt)
    vb = [float(n) for n in _NUM.findall(m.group(1))] if m else []
    area = vb[2] * vb[3] if len(vb) == 4 else None
    out = []
    for tm in _TAG.finditer(txt):
        kind = tm.group(1)
        a = dict(_ATTR.findall(tm.group(2)))
        if kind == "use":
            ref = a.get("xlink:href", a.get("href", "")).lstrip("#")
            if ref not in defs:
                continue
            a["d"] = defs[ref]
        st = _style(a)
        pts = _points(kind, a)
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if kind == "rect" and area and w * h > area / 2.0:
            continue
        fill = _colour(st.get("fill"))
        if kind in ("line",) and fill is None:
            fill = "none"
        out.append({
            "kind": "path" if kind == "use" else kind,
            "fill": fill,
            "fill_opacity": _float(st.get("fill-opacity")),
            "stroke": _colour(st.get("stroke")),
            "stroke_opacity": _float(st.get("stroke-opacity")),
            "stroke_width": _float(st.get("stroke-width")),
            "extent": round(max(w, h), 4),
            "center": (round((max(xs) + min(xs)) / 2.0, 2),
                       round((max(ys) + min(ys)) / 2.0, 2)),
            "points": [(round(x, 2), round(y, 2)) for x, y in pts],
        })
    return out


def _filled(e: dict) -> bool:
    return e.get("fill") not in (None, "none")


def _stroked(e: dict) -> bool:
    return e.get("stroke") not in (None, "none")


def markers(elements: "list[dict]", tol: float = 1.0) -> "list[list[dict]]":
    """Group consecutive elements sharing one centre (within *tol*) into
    markers: Stata draws a filled marker as a fill element then its
    outline, and an ``x`` or ``plus`` as two lines, each about one
    centre."""
    groups: "list[list[dict]]" = []
    for e in elements:
        if groups:
            last = groups[-1][-1]
            c0 = last["center"]
            dx = abs(c0[0] - e["center"][0])
            dy = abs(c0[1] - e["center"][1])
            # A filled marker's outline follows its fill element; a
            # triangle's outline is inset, so its box centre moves.
            outline = (len(groups[-1]) == 1 and _filled(last)
                       and not _stroked(last) and _stroked(e)
                       and not _filled(e) and e["kind"] == last["kind"]
                       and max(dx, dy) <= last["extent"] / 4.0)
            if outline or (dx <= tol and dy <= tol):
                groups[-1].append(e)
                continue
        groups.append([e])
    return groups


def marker_shape(elements: "list[dict]") -> "str | None":
    """The marker one group of elements draws: ``circle``, ``square``,
    ``diamond``, ``triangle``, ``x``, ``plus`` or ``v``; None when the
    group is no marker (a lone line is a segment, not an ``x``)."""
    kinds = [e["kind"] for e in elements]
    if "circle" in kinds:
        return "circle"
    if "rect" in kinds:
        return "square"
    poly = [e for e in elements if e["kind"] == "polygon"]
    if poly:
        pts = poly[0]["points"]
        if len(pts) == 3:
            return "triangle"
        if len(pts) == 4:
            cx = poly[0]["center"][0]
            if any(abs(x - cx) <= 0.5 for x, _ in pts):
                return "diamond"
            return "square"
        return None
    lines = [e for e in elements if e["kind"] == "line"]
    if len(lines) == 2:
        diag = all(abs(p[1][0] - p[0][0]) > 0.5 and abs(p[1][1] - p[0][1]) > 0.5
                   for p in (ln["points"] for ln in lines))
        return "x" if diag else "plus"
    paths = [e for e in elements if e["kind"] == "path"]
    if len(paths) == 1 and len(paths[0]["points"]) == 3 and \
            not _filled(paths[0]):
        return "v"
    return None


def hollow(elements: "list[dict]") -> bool:
    """True when no element of the marker has a colour fill."""
    return not any(_filled(e) for e in elements)


def stroke_extent(elements: "list[dict]") -> "float | None":
    """The extent of the marker's stroked outline (its fill element's when
    nothing is stroked)."""
    st = [e["extent"] for e in elements if _stroked(e)]
    if st:
        return max(st)
    fl = [e["extent"] for e in elements if _filled(e)]
    return max(fl) if fl else None
