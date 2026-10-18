"""scripts/svg_scheme_visual.py -- the reader behind
scripts/extract_scheme_visual_truth.do (BUGS.md "The scheme visual truth
covers 4 of 26 schemes and renders no histogram", WP-32).

It reads the SVGs that generator writes for one scheme and returns what
twoway drew: the graph size, the graph and plot regions, the legend box,
the text sizes and colours, the p1-p3 markers of a scatter, the p1-p3
lines of a line and of a connected plot, and a histogram's bars.

WHAT STATA'S SVG WRITER EMITS (measured 18oct2026, StataNow 19.5)

* Elements in drawing order: the canvas ``<rect>``, the graph region's
  fill and outline, then the plot region's fill and outline when the
  scheme draws them (economist draws neither; s1mono no fill), then grid
  lines, plots, axes, the legend and the titles.
* A filled marker is two elements at one centre: the fill and an outline
  (``fill:none``) on the centre line of the symbol: ``<circle>`` for a
  circle, ``<rect>`` for a square, a four-point ``<polygon>`` on the axes
  through its centre for a diamond, three points for a triangle.
* A solid line is one ``<path>``; a dashed one is exploded into many
  ``<line>`` segments (no dasharray).
* A text's size is ``font-size:<units>px`` and its colour ``fill``.

The synthetic data of the generator keep every data segment diagonal and
the three series in bands of their own (y1 near 1, y2 = y1 + 4, y3 = y1 +
8), so a series is told from the others by its band, and axis lines, ticks,
grid lines and legend keys (all axis-aligned) from data lines by their
direction.  Stdlib only: imported by Stata's Python.
"""

import math
import os
import re

_RE_EL = re.compile(r"<(rect|line|circle|polygon|path|text)\b([^>]*?)/?>"
                    r"(?:([^<]*)</text>)?", re.S)
_RE_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_RE_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _f(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _colour(s):
    if s is None:
        return None
    s = s.strip().lower()
    return None if s in ("", "none") else s


def _opacity(s):
    v = _f(s)
    return 1.0 if v is None else v


def elements(text):
    """Every drawn element of an SVG document *text*, in order: dicts with
    ``kind``, ``fill``, ``stroke`` (lower case, None for none),
    ``width`` (stroke width), ``fill_opacity`` and ``stroke_opacity`` (1
    when not written), the geometry (``x``/``y``/``w``/``h`` for a
    rect, ``cx``/``cy``/``r`` for a circle, ``x1``.. for a line, ``pts``
    for a polygon or path) and, for a text, ``text`` and ``size``."""
    out = []
    for m in _RE_EL.finditer(text):
        kind, raw, body = m.group(1), m.group(2), m.group(3)
        a = dict(_RE_ATTR.findall(raw))
        st = {}
        for part in a.get("style", "").split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                st[k.strip()] = v.strip()
        e = {"kind": kind, "fill": _colour(st.get("fill", a.get("fill"))),
             "stroke": _colour(st.get("stroke", a.get("stroke"))),
             "width": _f(st.get("stroke-width", a.get("stroke-width"))),
             "fill_opacity": _opacity(st.get("fill-opacity")),
             "stroke_opacity": _opacity(st.get("stroke-opacity"))}
        if kind == "rect":
            e.update(x=_f(a.get("x")), y=_f(a.get("y")),
                     w=_f(a.get("width")), h=_f(a.get("height")))
        elif kind == "circle":
            e.update(cx=_f(a.get("cx")), cy=_f(a.get("cy")), r=_f(a.get("r")))
        elif kind == "line":
            e.update(x1=_f(a.get("x1")), y1=_f(a.get("y1")),
                     x2=_f(a.get("x2")), y2=_f(a.get("y2")))
        elif kind in ("polygon", "path"):
            nums = [float(v) for v in _RE_NUM.findall(
                a.get("points", a.get("d", "")))]
            e["pts"] = list(zip(nums[0::2], nums[1::2]))
        else:
            e["text"] = (body or "").replace(" ", " ").strip()
            size = st.get("font-size", "")
            e["size"] = _f(size[:-2] if size.endswith("px") else size)
            e["x"], e["y"] = _f(a.get("x")), _f(a.get("y"))
        out.append(e)
    return out


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def graph_size(text):
    """(width, height) in inches and the viewBox (W, H)."""
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)in"[^>]*\bheight="([\d.]+)in"'
                  r'[^>]*\bviewBox="0 0 ([\d.]+) ([\d.]+)"', text)
    if not m:
        raise ValueError("no <svg> size and viewBox")
    return ([float(m.group(1)), float(m.group(2))],
            [float(m.group(3)), float(m.group(4))])


def regions(els):
    """The graph region's colour and the plot region's fill and border.

    The canvas, the graph region's fill and its outline are the first
    three rects; the plot region's fill and outline are the rects that
    follow them before any other element."""
    rects = [e for e in els[:3] if e["kind"] == "rect"]
    if len(rects) < 3:
        raise ValueError("fewer than three leading rects")
    graph = rects[1]["fill"] or rects[0]["fill"]
    fill = border = None
    for e in els[3:]:
        if e["kind"] != "rect":
            break
        if e["fill"] is not None:
            fill = e
        elif e["stroke"] is not None:
            border = e
    effective = fill["fill"] if fill else graph
    rec = {"graph_region_background": graph,
           "plot_region_background_effective": effective,
           "plot_region_border": {
               "color": border["stroke"] if border else None,
               "width_units": border["width"] if border else None,
               "visible": bool(border and border["stroke"] != effective
                               and border["stroke_opacity"] > 0
                               and (border["width"] or 0) > 0)}}
    return rec


def _encloses(r, x, y):
    return (r["x"] <= x <= r["x"] + r["w"]) and (r["y"] <= y <= r["y"] + r["h"])


def text_box(els, label, graph):
    """The box drawn behind the text *label*: the last filled and the last
    outlined rect before it (after the regions) that enclose its anchor."""
    idx = next(i for i, e in enumerate(els)
               if e["kind"] == "text" and e["text"] == label)
    t = els[idx]
    fill = border = None
    for e in els[3:idx]:
        if e["kind"] == "rect" and _encloses(e, t["x"], t["y"]):
            if e["fill"] is not None:
                fill = e
            elif e["stroke"] is not None:
                border = e
    under = fill["fill"] if fill else graph
    return {"has_background": fill is not None,
            "background": fill["fill"] if fill else None,
            "has_border": border is not None,
            "border_color": border["stroke"] if border else None,
            "border_visible": bool(border and border["stroke"] != under
                                   and border["stroke_opacity"] > 0)}


def fonts(els, height):
    """Size and colour of the title, subtitle, axis title, a tick label,
    the first legend label and the note."""
    want = {"title": "TTL", "subtitle": "SUB", "axis_title": "XTL",
            "legend_label": "LK1", "note": "NTE"}
    out = {}
    texts = [e for e in els if e["kind"] == "text"]
    for key, label in want.items():
        t = next(e for e in texts if e["text"] == label)
        out[key] = {"units": t["size"],
                    "pct_of_height": round(100 * t["size"] / height, 4),
                    "color": t["fill"]}
    tick = next(e for e in texts
                if re.fullmatch(r"-?[\d,]+(\.\d+)?", e["text"]))
    out["tick_label"] = {"units": tick["size"],
                         "pct_of_height": round(100 * tick["size"] / height, 4),
                         "color": tick["fill"]}
    return out


def _centre(e):
    if e["kind"] == "circle":
        return e["cx"], e["cy"]
    if e["kind"] == "rect":
        return e["x"] + e["w"] / 2, e["y"] + e["h"] / 2
    xs = [p[0] for p in e["pts"]]
    ys = [p[1] for p in e["pts"]]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def _extent(e):
    """The centre-line width of a marker element."""
    if e["kind"] == "circle":
        return 2 * e["r"]
    if e["kind"] == "rect":
        return e["w"]
    xs = [p[0] for p in e["pts"]]
    return max(xs) - min(xs)


def _symbol(e):
    if e["kind"] == "circle":
        return "circle"
    if e["kind"] == "rect":
        return "square"
    pts = e["pts"]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) == 3:
        return "triangle"
    if len(pts) == 4:
        cx, cy = _centre(e)
        on_axes = all(abs(x - cx) < 0.05 or abs(y - cy) < 0.05
                      for x, y in pts)
        return "diamond" if on_axes else "square"
    return "polygon%d" % len(pts)


def _bands(items, key, n=3):
    """Split *items* into *n* groups by *key* at the n-1 widest gaps;
    returned from the largest key (the lowest data value: SVG y grows
    downwards) to the smallest."""
    items = sorted(items, key=key, reverse=True)
    if len(items) < n:
        raise ValueError("fewer items than bands")
    gaps = sorted(range(1, len(items)),
                  key=lambda i: key(items[i - 1]) - key(items[i]),
                  reverse=True)[:n - 1]
    cuts = [0] + sorted(gaps) + [len(items)]
    return [items[cuts[i]:cuts[i + 1]] for i in range(n)]


def _plotted(els):
    """The elements drawn before the first text: the regions, grid lines
    and plots.  The axes' labels, the legend (its keys among them) and the
    titles come after."""
    out = []
    for e in els[3:]:
        if e["kind"] == "text":
            break
        out.append(e)
    return out


def markers(els, height):
    """p1-p3 of the scatter: symbol, fill, outline, sizes."""
    data = [e for e in _plotted(els) if e["kind"] in ("circle", "polygon")
            or (e["kind"] == "rect" and e["w"] is not None and e["w"] < 200)]
    out = {}
    for i, band in enumerate(_bands(data, lambda e: _centre(e)[1])):
        fills = [e for e in band if e["fill"] is not None]
        lines = [e for e in band if e["fill"] is None and e["stroke"]]
        first = (lines or fills)[0]
        sym = _symbol(first)
        nominal = _extent(first) / (math.sqrt(2) if sym == "diamond" else 1)
        if not lines:
            nominal = _extent(first)
        ow = lines[0]["width"] if lines else 0.0
        out["p%d" % (i + 1)] = {
            "symbol": sym, "solid": bool(fills),
            "color": fills[0]["fill"] if fills else None,
            "opacity": fills[0]["fill_opacity"] if fills else None,
            "outline_color": lines[0]["stroke"] if lines else None,
            "outline_opacity": lines[0]["stroke_opacity"] if lines else None,
            "outline_width_units": ow,
            "nominal_size_units": round(nominal, 2),
            "nominal_size_pct_of_height": round(100 * nominal / height, 4),
            "n_drawn": len(band) // (2 if fills and lines else 1)}
    return out


def _diagonal(e):
    if e["kind"] == "line":
        return abs(e["x2"] - e["x1"]) > 0.01 and abs(e["y2"] - e["y1"]) > 0.01
    return e["kind"] == "path" and len(e["pts"]) > 2 and e["fill"] is None


def _mean_y(e):
    if e["kind"] == "line":
        return (e["y1"] + e["y2"]) / 2
    return sum(p[1] for p in e["pts"]) / len(e["pts"])


def lines(els, height):
    """p1-p3 of a line or connected plot: colour, pattern, width."""
    data = [e for e in _plotted(els) if _diagonal(e)]
    out = {}
    for i, band in enumerate(_bands(data, _mean_y)):
        strokes = sorted({e["stroke"] for e in band})
        widths = sorted({e["width"] for e in band})
        if len(strokes) != 1 or len(widths) != 1:
            raise ValueError("series p%d drawn in %s %s" % (i + 1, strokes,
                                                           widths))
        solid = len(band) == 1 and band[0]["kind"] == "path"
        out["p%d" % (i + 1)] = {
            "color": strokes[0], "pattern": "solid" if solid else "dashed",
            "width_units": widths[0],
            "width_pct_of_height": round(100 * widths[0] / height, 4)}
    return out


def histogram(els, height):
    """The bars of a histogram: their fill and outline."""
    rects = [e for e in els[3:] if e["kind"] == "rect"]
    groups = {}
    for e in rects:
        if e["fill"] is not None:
            groups.setdefault(("fill", e["fill"], e["fill_opacity"],
                               round(e["y"] + e["h"])), []).append(e)
        elif e["stroke"] is not None:
            groups.setdefault(("line", e["stroke"], e["width"]), []).append(e)
    fills = max((k for k in groups if k[0] == "fill"),
                key=lambda k: len(groups[k]))
    n = len(groups[fills])
    outline = [k for k in groups if k[0] == "line" and len(groups[k]) == n]
    if len(outline) > 1:
        raise ValueError("ambiguous bar outlines %s" % outline)
    o = outline[0] if outline else None
    return {"n_bars": n, "fill": fills[1], "fill_opacity": fills[2],
            "outline_color": o[1] if o else None,
            "outline_width_units": o[2] if o else None,
            "outline_width_pct_of_height": (
                round(100 * o[2] / height, 4) if o else None)}


def symbol_ladder(work, names):
    """{msize name: drawn nominal size, % of the graph's height}."""
    out = {}
    for z in names:
        text = _read(os.path.join(work, "ms_%s.svg" % z))
        _size, (_w, h) = graph_size(text)
        m = markers(elements(text), h)
        out[z] = m["p1"]["nominal_size_pct_of_height"]
    return out


def symbol_name(pct, ladder, tol=0.01):
    """The msize name whose drawn size is *pct* within *tol* relative."""
    best = min(ladder, key=lambda z: abs(ladder[z] - pct))
    return best if abs(ladder[best] - pct) <= tol * ladder[best] else None


def measure_scheme(work, scheme, ladder):
    sc = _read(os.path.join(work, "sc_%s.svg" % scheme))
    size, (w, h) = graph_size(sc)
    els = elements(sc)
    rec = {"graph_size_in": size, "viewBox": [w, h]}
    rec.update(regions(els))
    rec["legend"] = text_box(els, "LK1", rec["graph_region_background"])
    rec["fonts"] = fonts(els, h)
    rec["markers"] = markers(els, h)
    for m in rec["markers"].values():
        m["stata_symbolsize_name"] = symbol_name(
            m["nominal_size_pct_of_height"], ladder)
    for kind, key in (("ln", "lines_twoway_line"),
                      ("cn", "lines_twoway_connected")):
        text = _read(os.path.join(work, "%s_%s.svg" % (kind, scheme)))
        rec[key] = lines(elements(text), graph_size(text)[1][1])
    hi = _read(os.path.join(work, "hi_%s.svg" % scheme))
    rec["histogram"] = histogram(elements(hi), graph_size(hi)[1][1])
    return rec


def measure_all(work, schemes, ladder_names):
    ladder = symbol_ladder(work, ladder_names)
    return {"symbolsize_ladder_pct_of_height": ladder,
            "schemes": {s: measure_scheme(work, s, ladder) for s in schemes}}
