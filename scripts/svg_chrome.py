"""Read a twoway graph's chrome from its SVG export (WP-30 P1.2a).

Stdlib only.  The geometry comes from ``svg_truth.svg_document`` (its
caller rules hold: a Stata-written SVG, colours lower-cased at read time);
this module adds the facts section 15 compares: where each title sits and
how it is aligned, the tick labels' rotation and side, the ticks' count,
position, length, colour and width, the axis lines and the grids.

The plot region is found by a sentinel: every probe carries
``plotregion(lcolor("1 2 3") lstyle(foreground))``, which twoway writes as
one ``<rect ... style="fill:none;stroke:#010203;stroke-width:W"/>`` inset by
W/2 from the plot region and which moves no text (measured 03oct2026,
``p2.do``: s2color's rect at x=393.68 with W=5.76 against region left
390.8).  Lengths are reported in Stata units, ``rs = min(viewBox W, H) /
100``.  Every regex is anchored on an attribute and has no nested
quantifier, so a hostile file reads in linear time.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import svg_truth  # noqa: E402

_RE_RECT = re.compile(r"<rect ([^>]*?)/?>")
_RE_TEXT = re.compile(r"<text ([^>]*)>([^<]*)</text>")
_RE_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_RE_VIEWBOX = re.compile(r'viewBox="([0-9.\- ]+)"')
_NUM = re.compile(r"^[-+]?[0-9][0-9,]*\.?[0-9]*$|^[-+]?\.[0-9]+$")


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _attrs(s):
    return dict(_RE_ATTR.findall(s))


def _style(a):
    out = {}
    for part in (a.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def _f(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _rs(text):
    m = _RE_VIEWBOX.search(text)
    if not m:
        return 1.0
    parts = [float(x) for x in m.group(1).split()]
    return min(parts[2], parts[3]) / 100.0 if len(parts) == 4 else 1.0


def svg_region(path, sentinel="#010203"):
    """``{"left", "top", "right", "bottom", "rs"}``: the sentinel rect grown
    by half its stroke width, or None when no sentinel is drawn."""
    text = _read(path)
    for m in _RE_RECT.finditer(text):
        a = _attrs(m.group(1))
        st = _style(a)
        if (st.get("stroke") or a.get("stroke") or "").lower() != sentinel:
            continue
        w = _f(st.get("stroke-width", a.get("stroke-width")), 0.0) or 0.0
        x, y = _f(a.get("x"), 0.0), _f(a.get("y"), 0.0)
        wd, ht = _f(a.get("width"), 0.0), _f(a.get("height"), 0.0)
        return {"left": x - w / 2, "top": y - w / 2,
                "right": x + wd + w / 2, "bottom": y + ht + w / 2,
                "rs": _rs(text)}
    return None


def _texts(path):
    out = []
    for m in _RE_TEXT.finditer(_read(path)):
        a = _attrs(m.group(1))
        st = _style(a)
        rot = 0.0
        tr = a.get("transform") or ""
        mm = re.search(r"rotate\((-?[0-9.]+)", tr)
        if mm:
            rot = float(mm.group(1))
        out.append({"text": svg_truth.normalise_text(m.group(2)),
                    "x": _f(a.get("x"), 0.0), "y": _f(a.get("y"), 0.0),
                    "anchor": a.get("text-anchor") or st.get("text-anchor")
                    or "start",
                    "weight": st.get("font-weight", a.get("font-weight"))
                    or "normal",
                    "style": st.get("font-style", a.get("font-style"))
                    or "normal",
                    "rotate": rot})
    return out


def _side(x, y, region):
    if y < region["top"]:
        return "above"
    if y > region["bottom"]:
        return "below"
    if x < region["left"]:
        return "left"
    if x > region["right"]:
        return "right"
    return "inside"


_ALIGN = {"start": "left", "middle": "center", "end": "right"}


def svg_text_place(path, text, region):
    """``{"side", "align", "weight", "style"}`` of the first ``<text>``
    reading *text*, or None."""
    for t in _texts(path):
        if t["text"] == text:
            return {"side": _side(t["x"], t["y"], region),
                    "align": _ALIGN.get(t["anchor"], "left"),
                    "weight": t["weight"], "style": t["style"]}
    return None


def _labels(path, axis, region):
    """The numeric tick labels beside the y edges (``axis`` "y") or below
    or above the region (``"x"``)."""
    out = []
    for t in _texts(path):
        if not _NUM.match(t["text"].replace("−", "-")):
            continue
        if axis == "x" and (t["y"] > region["bottom"]
                            or t["y"] < region["top"]) \
                and region["left"] - 1 <= t["x"] <= region["right"] + 1:
            out.append(t)
        if axis == "y" and (t["x"] < region["left"]
                            or t["x"] > region["right"]) \
                and region["top"] - 1 <= t["y"] <= region["bottom"] + 1:
            out.append(t)
    return out


def svg_label_rotation(path, axis, region, side=None):
    """Degrees, counter-clockwise, of *axis*'s tick labels (SVG's
    ``rotate(-90)`` is 90), or None when it draws none.  *side* picks one
    edge where an axis 2 labels the other."""
    labs = [t for t in _labels(path, axis, region)
            if side is None or _label_side_of(t, axis, region) == side]
    if not labs:
        return None
    return round(-labs[0]["rotate"]) % 360


def _label_side_of(t, axis, region):
    if axis == "y":
        mid = (region["left"] + region["right"]) / 2
        return "left" if t["x"] < mid else "right"
    mid = (region["top"] + region["bottom"]) / 2
    return "above" if t["y"] < mid else "below"


def svg_label_side(path, axis, region):
    """The sides *axis*'s tick labels sit on: ``["left"]``, ``["right"]``,
    or both, in that order."""
    sides = {_label_side_of(t, axis, region)
             for t in _labels(path, axis, region)}
    order = ("left", "right") if axis == "y" else ("below", "above")
    return [s for s in order if s in sides]


def _segments(path):
    doc = svg_truth.svg_document(path)
    return doc["hlines"], doc["vlines"]


def _collinear(lines, coord):
    """Positions (rounded coord, stroke) holding three or more segments: a
    dashed gridline, never a tick."""
    seen = {}
    for d in lines:
        k = (round(d[coord], 1), d["stroke"])
        seen[k] = seen.get(k, 0) + 1
    return {k for k, n in seen.items() if n >= 3}


def svg_ticks(path, edge, region):
    """``{"n", "position", "length_rs", "color", "width_rs"}`` of the short
    single lines touching the region's *edge* (``left``, ``right``,
    ``bottom`` or ``top``); ``n`` 0 when none is drawn."""
    rs = region["rs"]
    h, v = _segments(path)
    if edge in ("left", "right"):
        lines, along, cross = h, "y1", ("x1", "x2")
    else:
        lines, along, cross = v, "x1", ("y1", "y2")
    at = region[edge]
    runs = _collinear(lines, along)
    ticks = []
    for d in lines:
        if (round(d[along], 1), d["stroke"]) in runs:
            continue
        a, b = d[cross[0]], d[cross[1]]
        length = abs(a - b)
        if length <= 0 or length > 5 * rs:
            continue
        lo, hi = min(a, b), max(a, b)
        tol = 0.6 * (d["width"] or 1.0) + 0.6
        if lo < at - tol and hi > at + tol:
            pos = "crossing"
        elif min(abs(a - at), abs(b - at)) <= tol:
            outward = 1 if edge in ("right", "bottom") else -1
            free = hi if abs(lo - at) <= abs(hi - at) else lo
            pos = "outside" if (free - at) * outward > 0 else "inside"
        else:
            continue
        ticks.append((length, pos, d))
    if not ticks:
        return {"n": 0, "position": None, "length_rs": None, "color": None,
                "width_rs": None, "minor": 0}
    longest = max(t[0] for t in ticks)
    major = [t for t in ticks if t[0] >= 0.75 * longest]
    t0 = major[0]
    return {"n": len(major), "position": t0[1],
            "length_rs": round(t0[0] / rs, 3), "color": t0[2]["stroke"],
            "width_rs": round((t0[2]["width"] or 0.0) / rs, 3),
            "minor": len(ticks) - len(major)}


def svg_axis_line(path, edge, region):
    """True when a line of at least half the edge lies on *edge*."""
    h, v = _segments(path)
    if edge in ("left", "right"):
        lines, coord, a, b = v, "x1", "y1", "y2"
        span = region["bottom"] - region["top"]
    else:
        lines, coord, a, b = h, "y1", "x1", "x2"
        span = region["right"] - region["left"]
    at = region[edge]
    for d in lines:
        if abs(d[coord] - at) <= 0.6 * (d["width"] or 1.0) + 0.6 \
                and abs(d[a] - d[b]) >= span / 2:
            return True
    return False


def svg_grid(path, axis, region):
    """``{"drawn", "dashed", "color"}`` of *axis*'s major grid: the lines
    across the region at its ticks (horizontal lines for y, vertical for
    x).  Dashed means more than one collinear segment per gridline."""
    h, v = _segments(path)
    if axis == "y":
        lines, coord = h, "y1"
        lo, hi = region["left"], region["right"]
        s0, s1 = "x1", "x2"
    else:
        lines, coord = v, "x1"
        lo, hi = region["top"], region["bottom"]
        s0, s1 = "y1", "y2"
    inner = [d for d in lines
             if lo - 0.6 <= min(d[s0], d[s1]) and max(d[s0], d[s1]) <= hi + 0.6
             and region["top" if axis == "y" else "left"] + 1
             < d[coord] < region["bottom" if axis == "y" else "right"] - 1]
    groups = svg_truth.line_groups(inner, coord)
    full = [g for g in groups
            if (g["span_to"] - g["span_from"]) >= 0.5 * (hi - lo)]
    if not full:
        return {"drawn": False, "dashed": False, "color": None}
    return {"drawn": True, "dashed": any(g["n_segments"] > 1 for g in full),
            "color": full[0]["stroke"]}
