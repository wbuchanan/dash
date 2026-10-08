"""scripts/svg_truth.py -- WP-28 S02: the one reader for a Stata-exported
twoway SVG.

WHY THIS EXISTS

Eight of WP-28's 22 gaps (B1, B2, B3, B5, B6, B7, D1, X2, plus G16) are
proved against what twoway *draws*, not against a documented rule.  Before
this module, seven certification scripts each re-discovered the same facts
about Stata's SVG writer with a private parser (`scripts/extract_axis_truth.
do`'s `parse_svg`/`axis_facts`, `test_help_claims_8.cscript`'s `_hc_svg`
family, `test_help_claims_2.cscript`'s `_hc2_rawhas`, and four more), and
none of them accounted for the one fact that breaks an exact text match for
no visible reason: Stata's SVG writer represents a run of spaces as U+00A0,
not U+0020 (`nbsp(on)` is the default; `svg_options.sthlp:128-137`).  This
module is that one reader.  Every later section's `extract_*_truth.do`
script and every block of `test/test_gaps2_truth.cscript` reads an SVG only
through the public names below.

WHAT STATA'S WRITER EMITS (measured; see `scripts/extract_axis_truth.do`'s
header and `test/fixtures/svg_truth_smoke.json`)

* The plotregion is a solid-fill ``<rect>`` written before its border;
  regions come outermost first (canvas, graphregion, plotregion, legend /
  by-panel regions).
* Each tick is a short black ``<line>`` touching a plotregion edge; each
  tick label is a ``<text>`` whose ``x`` (x axis) or ``y`` (y axis) sits at
  the tick.
* Gridlines are dashed, multi-segment ``<line>`` groups.
* Legend keys are ``<text>`` elements *without* a ``text-anchor`` attribute;
  titles and labels carry ``font-size:NNpx`` inside ``style``.
* Colours are ``stroke:#RRGGBB`` / ``fill:#RRGGBB`` in upper case; this
  module lower-cases every colour at read time (dash's own scheme tables
  write lower case).
* A run of spaces inside a string is written as U+00A0 (``nbsp(on)``,
  the default).

RULES FOR ANY CALLER OF THIS MODULE

* Stdlib only (``re``, ``html``, ``math``, ``collections``): this file must
  import under Stata's Python (3.13 measured) and under a newer development
  interpreter alike.
* This file is a plain ``.py`` module, never a ``python:`` block inside a
  ``.do`` file, so its regexes may hold a literal backtick freely.  A
  ``python:`` block that *imports* this module must never call back into
  Stata (no ``SFIToolkit.stata()``/``stata()``) and must never write a
  literal backtick in its own source -- spell one ``\\x60`` there, not here.
* Every Stata run that produces or reads a fixture through this module goes
  through ``scripts/stata_slot.sh <scratch-dir> <file>.do`` (CLAUDE.md rule
  10; sets ``STATATMP=<scratch-dir>/tmp/``, trailing slash); a certification
  script is never handed to the wrapper directly (it ``cd``\\ s into
  ``test/`` first via a two-line driver -- see ``sections/BRIEF.md``
  "Running one cscript").
* A fixture this module's output is pinned against is committed with
  ``git add -f`` (``.git/info/exclude`` hides ``*.json``/``*.txt``) and
  named by a test or certification script (``test_fixtures_are_committed.
  py``).

Imported by pytest as
``sys.path.insert(0, os.path.join(_ROOT, "scripts")); import svg_truth``;
by a do-file's ``python:`` block as
``sys.path.insert(0, Macro.getGlobal("ZS_REPO") + "/scripts")``; by
``test/cert_svg.do`` as its header describes.
"""

import collections
import html
import math
import re

# ---------------------------------------------------------------------------
# Low-level SVG attribute/element regexes.  A Stata SVG element is always
# self-closing (<line .../>, <rect .../>, <circle .../>, <path .../>) except
# <text>, which carries its content between an opening and closing tag.
# ---------------------------------------------------------------------------
_RE_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_RE_TEXT = re.compile(r'<text ([^>]*?)>(.*?)</text>', re.S)
_RE_LINE = re.compile(r'<line ([^/>]*)/>')
_RE_RECT = re.compile(r'<rect ([^/>]*)/>')
_RE_CIRCLE = re.compile(r'<circle ([^/>]*)/>')
_RE_PATH = re.compile(r'<path ([^/>]*)/>')
_RE_VIEWBOX = re.compile(r'viewBox="([\d.\- ]+)"')
_RE_ROTATE = re.compile(r'rotate\((-?[\d.]+)')
_RE_VERSION = re.compile(r'<!--(.*?Stata.*?)-->', re.S | re.I)

#: Stata's rendered minus sign; label_value() reads it as an ASCII hyphen.
_MINUS = "−"
#: The space Stata's SVG writer uses for a run of spaces (nbsp(on), the
#: default).
_NBSP = " "


def _attrs(s):
    """{attribute name: value} for one element's attribute text."""
    return dict(_RE_ATTR.findall(s))


def _fnum(s, default=None):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _style_of(a):
    """{property: value} for the ``style="a:b;c:d"`` attribute, if any."""
    out = {}
    for part in a.get("style", "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _lower(s):
    return s.lower() if isinstance(s, str) else s


def normalise_text(s):
    """The text of a ``<text>`` element as a human reads it: HTML entities
    decoded, then every U+00A0 (Stata's "a run of spaces") turned into an
    ordinary space.  Nothing else about the text changes -- a genuine run of
    several spaces stays a run of several spaces."""
    return html.unescape(s).replace(_NBSP, " ")


# ---------------------------------------------------------------------------
# svg_document: the whole structural reading of one SVG file.
# ---------------------------------------------------------------------------
def svg_document(path, as_written=False):
    """The structural facts of a Stata-written SVG at *path*.

    Returns a dict with keys ``texts``, ``hlines``, ``vlines``,
    ``diaglines``, ``rects``, ``circles``, ``paths``, ``canvas``,
    ``regions``, ``plotregion``, ``axis_line`` and ``version``.

    ``plotregion`` is the first solid-fill ``<rect>`` that is not (nearly)
    the whole canvas -- Stata writes canvas, graphregion, plotregion, then
    any legend / by-panel regions, in that order -- or, when no such rect
    exists, the bounding box of the longest black horizontal and vertical
    ``<line>`` (``axis_line``).  Every colour is lower-cased at read time.

    With *as_written*, each text and rect also carries ``fill_raw`` and
    each line ``stroke_raw``: the colour as the writer spelled it (Stata
    upper-cases the hex it computes and keeps a named colour's lower case,
    ``#0000ff`` for blue), for a record that has always kept that spelling
    (``scripts/extract_axis_truth.do``, WP-28 S18).
    """
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        txt = fh.read()

    texts = []
    for m in _RE_TEXT.finditer(txt):
        a = _attrs(m.group(1))
        st = _style_of(a)
        rot = None
        mr = _RE_ROTATE.search(a.get("transform", ""))
        if mr:
            rot = float(mr.group(1))
        fill = st.get("fill", a.get("fill"))
        raw = m.group(2)
        texts.append({
            "x": _fnum(a.get("x")),
            "y": _fnum(a.get("y")),
            "anchor": a.get("text-anchor"),
            "rotate": rot,
            "size": _fnum(st.get("font-size", "").replace("px", "")),
            "fill": _lower(fill),
            # As written (Stata upper-cases hex it computes and keeps a
            # named colour's lower case: #0000ff for blue), for a record
            # that has always kept the writer's own spelling.
            "fill_raw": fill,
            "font_family": st.get("font-family"),
            "text": normalise_text(raw),
            "raw": raw,
        })

    hlines, vlines, diaglines = [], [], []
    for m in _RE_LINE.finditer(txt):
        a = _attrs(m.group(1))
        st = _style_of(a)
        x1, y1 = _fnum(a.get("x1")), _fnum(a.get("y1"))
        x2, y2 = _fnum(a.get("x2")), _fnum(a.get("y2"))
        if None in (x1, y1, x2, y2):
            continue
        d = {
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "stroke": _lower(st.get("stroke", a.get("stroke"))),
            "stroke_raw": st.get("stroke", a.get("stroke")),
            "width": _fnum(st.get("stroke-width", a.get("stroke-width", ""))),
            "dasharray": st.get("stroke-dasharray", a.get("stroke-dasharray")),
        }
        if abs(y1 - y2) < 0.01:
            hlines.append(d)
        elif abs(x1 - x2) < 0.01:
            vlines.append(d)
        else:
            diaglines.append(d)

    rects = []
    for m in _RE_RECT.finditer(txt):
        a = _attrs(m.group(1))
        st = _style_of(a)
        rects.append({
            "x": _fnum(a.get("x")), "y": _fnum(a.get("y")),
            "w": _fnum(a.get("width")), "h": _fnum(a.get("height")),
            "fill": _lower(st.get("fill", a.get("fill"))),
            "fill_raw": st.get("fill", a.get("fill")),
            "stroke": _lower(st.get("stroke", a.get("stroke"))),
        })

    circles = []
    for m in _RE_CIRCLE.finditer(txt):
        a = _attrs(m.group(1))
        st = _style_of(a)
        circles.append({
            "cx": _fnum(a.get("cx")), "cy": _fnum(a.get("cy")),
            "r": _fnum(a.get("r")),
            "fill": _lower(st.get("fill", a.get("fill"))),
            "stroke": _lower(st.get("stroke", a.get("stroke"))),
            "fill_opacity": _fnum(st.get("fill-opacity", a.get("fill-opacity"))),
            "stroke_opacity": _fnum(st.get("stroke-opacity",
                                           a.get("stroke-opacity"))),
        })

    paths = []
    for m in _RE_PATH.finditer(txt):
        a = _attrs(m.group(1))
        st = _style_of(a)
        paths.append({
            "d": a.get("d"),
            "fill": _lower(st.get("fill", a.get("fill"))),
            "stroke": _lower(st.get("stroke", a.get("stroke"))),
            "fill_opacity": _fnum(st.get("fill-opacity", a.get("fill-opacity"))),
            "stroke_opacity": _fnum(st.get("stroke-opacity",
                                           a.get("stroke-opacity"))),
        })

    canvas = None
    mv = _RE_VIEWBOX.search(txt)
    if mv:
        vb = [float(t) for t in mv.group(1).split()]
        canvas = {"x": vb[0], "y": vb[1], "w": vb[2], "h": vb[3]}

    regions = []
    if canvas:
        area = canvas["w"] * canvas["h"]
        for r in rects:
            if not r["w"] or not r["h"]:
                continue
            if r["fill"] in (None, "none"):
                continue
            if r["w"] * r["h"] >= 0.95 * area:
                continue
            regions.append({
                "left": r["x"], "top": r["y"],
                "right": r["x"] + r["w"], "bottom": r["y"] + r["h"],
                "fill": r["fill"],
            })

    plotregion = None
    if regions:
        r = regions[0]
        plotregion = dict(r)
        plotregion["source"] = (
            "first solid-fill <rect> inside the graph region (Stata writes "
            "canvas, graphregion, plotregion, then legend / by-panel "
            "regions, in that order)"
        )

    def _black(d):
        return (d.get("stroke") or "") == "#000000"

    axis_line = None
    hb = [d for d in hlines if _black(d)]
    vb_ = [d for d in vlines if _black(d)]
    if hb and vb_:
        bot = max(hb, key=lambda d: abs(d["x2"] - d["x1"]))
        lef = max(vb_, key=lambda d: abs(d["y2"] - d["y1"]))
        axis_line = {
            "h_y": bot["y1"],
            "h_x_from": min(bot["x1"], bot["x2"]),
            "h_x_to": max(bot["x1"], bot["x2"]),
            "v_x": lef["x1"],
            "v_y_from": min(lef["y1"], lef["y2"]),
            "v_y_to": max(lef["y1"], lef["y2"]),
        }
    if plotregion is None and axis_line:
        plotregion = {
            "left": axis_line["v_x"], "right": axis_line["h_x_to"],
            "top": axis_line["v_y_from"], "bottom": axis_line["h_y"],
            "fill": None,
            "source": "axis-line bounding box (no solid-fill region rect)",
        }

    version = None
    mver = _RE_VERSION.search(txt)
    if mver:
        version = mver.group(1).strip()

    if not as_written:
        for d in texts + rects:
            d.pop("fill_raw", None)
        for d in hlines + vlines + diaglines:
            d.pop("stroke_raw", None)

    return {
        "texts": texts, "hlines": hlines, "vlines": vlines,
        "diaglines": diaglines, "rects": rects, "circles": circles,
        "paths": paths, "canvas": canvas, "regions": regions,
        "plotregion": plotregion, "axis_line": axis_line, "version": version,
    }


def svg_texts(path):
    """One dict per ``<text>`` element of *path*, in document order: the
    ``texts`` list of :func:`svg_document`."""
    return svg_document(path)["texts"]


def svg_has_text(path, text, *, lower=False):
    """The number of ``<text>`` elements of *path* whose normalised text
    equals *text* exactly (whole element, not a substring); case-insensitive
    when *lower* is true."""
    target = text.lower() if lower else text
    n = 0
    for t in svg_texts(path):
        cand = t["text"].lower() if lower else t["text"]
        if cand == target:
            n += 1
    return n


def svg_fills(path, *, elements=("circle", "path", "polygon", "rect")):
    """The fill colours of *path*, grouped by colour.

    Returns ``{colour: {"n": int, "kinds": {element kind: count}, "opacity":
    [distinct fill-opacity values, sorted]}}``.  Colour is lower-cased;
    ``none`` and an absent fill are excluded.  *elements* restricts which
    element kinds are counted (``polygon`` is accepted for symmetry; Stata's
    writer emits markers as ``<circle>``/``<path>``, never ``<polygon>``, so
    that bucket is always empty today).
    """
    doc = svg_document(path)
    source = {
        "circle": doc["circles"],
        "path": doc["paths"],
        "rect": doc["rects"],
        "polygon": [],
    }
    out = {}
    for kind in elements:
        for item in source.get(kind, []):
            fill = item.get("fill")
            if not fill or fill == "none":
                continue
            entry = out.setdefault(fill, {"n": 0, "kinds": {}, "opacity": set()})
            entry["n"] += 1
            entry["kinds"][kind] = entry["kinds"].get(kind, 0) + 1
            op = item.get("fill_opacity")
            if op is not None:
                entry["opacity"].add(op)
    for entry in out.values():
        entry["opacity"] = sorted(entry["opacity"])
    return out


def svg_rects(path):
    """Every ``<rect>`` of *path* in document order (WP-30 P1.20a), each
    with the ten keys ``x``, ``y``, ``w``, ``h``, ``fill``, ``fill_opacity``,
    ``stroke``, ``stroke_width``, ``stroke_opacity`` and ``dasharray``
    (colours lower-cased; an absent attribute is None).  Stata writes the
    canvas first, then the graph region's fill and outline, then the plot
    region's, so the region roles are read from the order and position."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    out = []
    for m in _RE_RECT.finditer(txt):
        a = _attrs(m.group(1))
        st = _style_of(a)

        def get(k):
            return st.get(k, a.get(k))
        out.append({
            "x": _fnum(a.get("x")), "y": _fnum(a.get("y")),
            "w": _fnum(a.get("width")), "h": _fnum(a.get("height")),
            "fill": _lower(get("fill")),
            "fill_opacity": _fnum(get("fill-opacity")),
            "stroke": _lower(get("stroke")),
            "stroke_width": _fnum(get("stroke-width")),
            "stroke_opacity": _fnum(get("stroke-opacity")),
            "dasharray": get("stroke-dasharray"),
        })
    return out


def svg_marker_fills(path):
    """:func:`svg_fills` restricted to circles, paths and polygons -- the
    element kinds Stata draws markers with -- so canvas, region and bar
    rectangles are excluded."""
    return svg_fills(path, elements=("circle", "path", "polygon"))


def svg_lines(path):
    """``{"h": [...], "v": [...], "diag": [...]}``: every ``<line>`` of
    *path*, split by orientation, each with ``x1``, ``y1``, ``x2``, ``y2``,
    ``stroke`` (lower-case), ``width`` and ``dasharray``.  Use
    :func:`line_groups` to collapse a dashed gridline's segments into one
    group."""
    doc = svg_document(path)
    return {"h": doc["hlines"], "v": doc["vlines"], "diag": doc["diaglines"]}


def line_groups(lines, coord):
    """Collapse the segments of one drawn line (a solid line is one
    segment; a dashed gridline is several) into one group per off-axis
    pixel position, stroke and width.  *coord* is ``"y1"`` to group
    horizontal lines by their y position, ``"x1"`` to group vertical lines
    by their x position.  Each group has ``px`` (the off-axis pixel),
    ``stroke``, ``width``, ``n_segments``, ``span_from`` and ``span_to``
    (the along-axis extent)."""
    g = collections.defaultdict(list)
    for d in lines:
        g[(round(d[coord], 2), d["stroke"], d["width"])].append(d)
    span_key = "x" if coord in ("y1", "y2") else "y"
    a = "x1" if span_key == "x" else "y1"
    b = "x2" if span_key == "x" else "y2"
    out = []
    for key in sorted(g, key=lambda k: (k[0], str(k[1]), k[2] or 0)):
        segs = sorted(g[key], key=lambda d: min(d[a], d[b]))
        lo = min(min(d[a], d[b]) for d in segs)
        hi = max(max(d[a], d[b]) for d in segs)
        out.append({
            "px": key[0], "stroke": key[1], "width": key[2],
            "n_segments": len(segs), "span_from": lo, "span_to": hi,
        })
    return out


def svg_plotregion(path):
    """``{"left", "top", "right", "bottom", "fill", "source"}`` -- the
    first solid-fill non-canvas rect, else the axis-line bounding box, or
    ``None`` when neither can be identified."""
    return svg_document(path)["plotregion"]


def label_value(s):
    """Parse a rendered tick label back to a number, or ``None`` when it is
    not one (a category label such as ``"Q3"``).  Stata's rendered minus
    sign and thousands commas are normalised first."""
    if s is None:
        return None
    t = s.strip().replace(_MINUS, "-").replace(",", "")
    if re.fullmatch(r'-?(\d+\.?\d*|\.\d+)', t or "x"):
        return float(t)
    return None


def fit_axis_mapping(pairs, edge_start, edge_end):
    """Fit tick pixel -> tick value over *pairs* (``[(px, value), ...]``),
    trying a linear space then a log10 space (skipped when any value is not
    positive), each judged by the 1e-3 relative-residual rule (a fit of
    exactly two pairs is accepted outright, since two points determine a
    line without a residual to judge).  The accepted fit is then inverted at
    *edge_start* and *edge_end* (the plot-region edges in axis order) to
    give the two edge values.

    Returns ``{"space", "units_per_px", "residual", "low", "high",
    "reversed"}``, or ``None`` when fewer than two pairs are given or no
    space fits."""
    if len(pairs) < 2:
        return None
    for space in ("linear", "log10"):
        pp = pairs
        if space == "log10":
            if any(v <= 0 for _, v in pairs):
                continue
            pp = [(px, math.log10(v)) for px, v in pairs]
        (p0, v0), (p1, v1) = pp[0], pp[-1]
        if p1 == p0 or v1 == v0:
            continue
        slope = (v1 - v0) / (p1 - p0)
        resid = max(abs((v - v0) - slope * (px - p0)) for px, v in pp)
        scale = max(abs(v) for _, v in pp) or 1.0
        if resid / scale < 1e-3 or len(pp) == 2:
            def _inv(px, v0=v0, p0=p0, slope=slope, space=space):
                z = v0 + slope * (px - p0)
                return 10 ** z if space == "log10" else z
            lo_edge, hi_edge = _inv(edge_start), _inv(edge_end)
            return {
                "space": space,
                "units_per_px": slope,
                "residual": resid,
                "low": min(lo_edge, hi_edge),
                "high": max(lo_edge, hi_edge),
                "reversed": bool(hi_edge < lo_edge),
            }
    return None


def svg_axis_reading(path, axis, tick_values=None, doc=None):
    """Everything the axis reader sees on *axis* (``"x"`` or ``"y"``) of
    *path*, whether or not the ticks fit a scale -- the one reading
    :func:`svg_axis_extent` answers from, kept whole for a caller that
    records the tick marks, gridlines and label elements too
    (``scripts/extract_axis_truth.do``, WP-28 S18, which read them through
    a private copy of this logic until then).

    *doc* is :func:`svg_document`'s reading of *path* when the caller
    already has it.  *tick_values* is as for :func:`svg_axis_extent`; a
    length mismatch raises the same ``ValueError``.

    Returns a dict: ``plotregion`` (None when none could be identified,
    and then only ``reason`` besides), ``tick_px``, ``n_ticks``,
    ``tick_side`` (``"below plotregion"``/``"above plotregion"`` on x,
    ``"left of plotregion"``/``"right of plotregion"`` on y, or None),
    ``grid`` (the gridline groups of :func:`line_groups`), ``label_objs``
    (per tick pixel, the ``<text>`` element matched to it, or None),
    ``label_offaxis_px`` (the row or column the labels were read from, or
    None), ``labels``, ``pairs`` (the ``(px, value)`` pairs fitted),
    ``fit`` (:func:`fit_axis_mapping`'s answer, or None) and ``reason``
    (why there is no fit, else None).
    """
    if doc is None:
        doc = svg_document(path)
    pr = doc["plotregion"]
    if pr is None:
        return {"plotregion": None,
                "reason": "no plotregion could be identified in the SVG"}
    tol = 2.5

    def _black(d):
        return (d.get("stroke") or "") == "#000000"

    if axis == "x":
        marks_below, marks_above = [], []
        for d in doc["vlines"]:
            if not _black(d):
                continue
            ylo, yhi = min(d["y1"], d["y2"]), max(d["y1"], d["y2"])
            if (yhi - ylo) > 0.5 * (pr["bottom"] - pr["top"]):
                continue
            if abs(ylo - pr["bottom"]) < tol:
                marks_below.append(round(d["x1"], 2))
            elif abs(yhi - pr["top"]) < tol:
                marks_above.append(round(d["x1"], 2))
        grid = [g for g in line_groups(
                    [d for d in doc["vlines"] if not _black(d)], "x1")
                if g["n_segments"] > 3
                and g["span_to"] - g["span_from"] > 0.8 * (pr["bottom"] - pr["top"])]
        tick_px = sorted(set(marks_below or marks_above))
        tick_side = ("below plotregion" if marks_below else
                     ("above plotregion" if marks_above else None))
        cand = [t for t in doc["texts"] if t["y"] is not None
                and (t["y"] > pr["bottom"] or t["y"] < pr["top"])]
        keyc, offc = "x", "y"
        near_edge = pr["bottom"] if marks_below else pr["top"]
        edge_start, edge_end = pr["left"], pr["right"]
    elif axis == "y":
        marks_left, marks_right = [], []
        for d in doc["hlines"]:
            if not _black(d):
                continue
            xlo, xhi = min(d["x1"], d["x2"]), max(d["x1"], d["x2"])
            if (xhi - xlo) > 0.5 * (pr["right"] - pr["left"]):
                continue
            if abs(xhi - pr["left"]) < tol:
                marks_left.append(round(d["y1"], 2))
            elif abs(xlo - pr["right"]) < tol:
                marks_right.append(round(d["y1"], 2))
        grid = [g for g in line_groups(
                    [d for d in doc["hlines"] if not _black(d)], "y1")
                if g["n_segments"] > 3
                and g["span_to"] - g["span_from"] > 0.8 * (pr["right"] - pr["left"])]
        tick_px = sorted(set(marks_left or marks_right))
        tick_side = ("left of plotregion" if marks_left else
                     ("right of plotregion" if marks_right else None))
        cand = [t for t in doc["texts"] if t["x"] is not None
                and (t["x"] < pr["left"] or t["x"] > pr["right"])]
        keyc, offc = "y", "x"
        near_edge = pr["left"] if marks_left else pr["right"]
        edge_start, edge_end = pr["bottom"], pr["top"]
    else:
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")

    if not tick_px:
        tick_px = sorted({g["px"] for g in grid})
    n_ticks = len(tick_px)

    labels, lab_px, label_objs = [], [], []
    label_offaxis_px = None
    if cand and tick_px:
        clusters = collections.defaultdict(list)
        for t in cand:
            clusters[round(t[offc], 1)].append(t)
        best = min(clusters, key=lambda c: abs(c - near_edge))
        label_offaxis_px = best
        row = clusters[best]
        used = set()
        for p in tick_px:
            pick, pd = None, 1e18
            for j, t in enumerate(row):
                if j in used or t[keyc] is None:
                    continue
                dd = abs(t[keyc] - p)
                if dd < pd:
                    pick, pd = j, dd
            if pick is not None and pd < 250:
                used.add(pick)
                labels.append(row[pick]["text"])
                label_objs.append(row[pick])
            else:
                labels.append(None)
                label_objs.append(None)
            lab_px.append(p)
    else:
        labels = [None] * len(tick_px)
        label_objs = [None] * len(tick_px)
        lab_px = list(tick_px)

    if tick_values is not None:
        if len(tick_values) != len(lab_px):
            raise ValueError(
                f"tick_values has {len(tick_values)} entries but "
                f"{len(lab_px)} tick pixel(s) were found"
            )
        pairs = list(zip(lab_px, tick_values))
    else:
        pairs = [(px, label_value(l)) for px, l in zip(lab_px, labels)
                 if l is not None and label_value(l) is not None]

    out = {"plotregion": pr, "tick_px": tick_px, "n_ticks": n_ticks,
           "tick_side": tick_side, "grid": grid, "label_objs": label_objs,
           "label_offaxis_px": label_offaxis_px, "labels": labels,
           "pairs": pairs, "fit": None, "reason": None}
    if len(pairs) < 2:
        out["reason"] = (
            "fewer than two tick labels parse as numbers, so the "
            "pixel<->data map could not be inverted; the tick pixel "
            "positions are still exact"
        )
        return out
    fit = fit_axis_mapping(pairs, edge_start, edge_end)
    if fit is None:
        out["reason"] = "no linear or log10 fit satisfied the residual rule"
        return out
    out["fit"] = fit
    return out


def svg_axis_extent(path, axis, tick_values=None):
    """The drawn extent of *axis* (``"x"`` or ``"y"``) in *path*: the data
    value at each plot-region edge, fitted over the labelled ticks as
    :func:`svg_axis_reading` locates them (short black tick lines at the
    near plotregion edge; the row or column of ``<text>`` nearest that
    edge, matched to the nearest tick pixel within 250 px).

    When *tick_values* is given, it replaces ``label_value(label)`` for
    every tick: it must have one entry per tick pixel found, in ascending
    pixel order along that axis (left to right for the x axis -- pixel x
    grows rightward; top to bottom for the y axis -- pixel y grows
    downward, so the first entry is the axis's *top* tick).  A length
    mismatch raises ``ValueError`` naming both counts.

    Returns ``{"low", "high", "space", "reversed", "tick_px", "tick_labels",
    "tick_values", "residual", "plotregion", "n_ticks"}``, or ``None`` when
    fewer than two ticks pair with a value or no fit satisfies the residual
    rule -- in which case ``svg_axis_extent.last_reason`` names why.
    """
    svg_axis_extent.last_reason = None
    r = svg_axis_reading(path, axis, tick_values)
    if r["plotregion"] is None or r["fit"] is None:
        svg_axis_extent.last_reason = r["reason"]
        return None
    fit = r["fit"]
    return {
        "low": fit["low"], "high": fit["high"], "space": fit["space"],
        "reversed": fit["reversed"], "tick_px": r["tick_px"],
        "tick_labels": r["labels"],
        "tick_values": list(tick_values) if tick_values is not None
                        else [p[1] for p in r["pairs"]],
        "residual": fit["residual"], "plotregion": r["plotregion"],
        "n_ticks": r["n_ticks"],
    }


svg_axis_extent.last_reason = None
