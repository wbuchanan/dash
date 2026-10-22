"""Judge each corpus example: twoway's picture against dash's (WP-33 33-05).

    python3 scripts/corpus/verdict.py --run <run> [--rules <json>] [--ledger <json>]
                                      [--gaps4 <md>]

Reads <run>/examples.jsonl, twoway.jsonl (33-03) and dash.jsonl (33-04) and
writes <run>/verdicts.jsonl: per example its rc pair, a verdict (Same,
Close or Differs), the measured differences, each tagged with the GAPS4 id
of the ledger row that explains it, the image score, the glyph colours, the
gallery flag and a one-line summary in Stata terms.

The verdict (DECISIONS A-4, D-33-05.a): the geometry and colour checks
alone decide Differs; a difference a live ledger row explains makes Close;
the image score can only move a geometry-clean pair from Same to Close.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import base64
import collections
import json
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import svg_layer  # noqa: E402
import svg_truth  # noqa: E402

from scripts.corpus import ledger as ledger_mod  # noqa: E402

RULES_PATH = os.path.join(REPO, "test", "fixtures", "corpus_verdict_rules.json")
LEDGER_PATH = os.path.join(REPO, "test", "fixtures", "corpus_ledger.json")

#: Every check's name in Stata terms, for the caption line (DECISIONS A-24).
STATA_TERMS = {
    "rc": "return code", "first_line": "message", "x_ticks": "x-axis ticks",
    "y_ticks": "y-axis ticks", "x_labels": "x-axis labels", "y_labels": "y-axis labels",
    "axis_titles": "axis titles", "titles": "titles", "legend": "legend keys",
    "glyphs": "number of markers", "glyph_extents": "marker positions",
    "marker_shape": "marker symbol", "frame_aspect": "plot region shape",
    "colours": "colours", "image": "picture", "x_scale": "x-axis scale",
    "y_scale": "y-axis scale", "x_labels_none": "x-axis labels",
    "y_labels_none": "y-axis labels", "text_size": "text size", "margins": "margins",
    "marker_size": "marker size", "line_width": "line width",
    "marker_labels": "marker labels", "outline_extra": "bar outline",
}

#: The keys of one verdicts.jsonl row, in order.
ROW_KEYS = ("id", "plottype", "source", "rc_twoway", "rc_dash", "rc_pair", "first_twoway",
            "first_dash", "verdict", "ssim", "size_matched", "panels", "differences",
            "checks", "ledger", "summary", "colours", "gallery", "skip")

#: Bokeh's marker names read as svg_layer's (D-33-05.b).
BOKEH_SHAPES = {"cross": "plus", "inverted_triangle": "v"}

SUMMARY_MAX = 200

#: (svg, w, h) => base64 of the w x h luminance bytes (D-33-05.f).
RASTER_JS = r"""(async (svg, w, h) => {
  const img = new Image();
  img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svg)));
  await img.decode();
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const g = c.getContext("2d");
  g.fillStyle = "#ffffff"; g.fillRect(0, 0, w, h); g.drawImage(img, 0, 0, w, h);
  const d = g.getImageData(0, 0, w, h).data, out = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i++)
    out[i] = Math.round(0.299 * d[4 * i] + 0.587 * d[4 * i + 1] + 0.114 * d[4 * i + 2]);
  let s = "";
  for (let i = 0; i < out.length; i += 8192)
    s += String.fromCharCode.apply(null, out.subarray(i, i + 8192));
  return btoa(s);
})"""

RASTER_PAGE = '<!doctype html><meta charset="utf-8"><title>raster</title>\n'
RASTER_READY = "document.readyState === 'complete'"

_HEX6 = re.compile(r"^#([0-9a-f]{6})$")
_HEX8 = re.compile(r"^#([0-9a-f]{8})$")
_HEX3 = re.compile(r"^#([0-9a-f]{3})$")
_RGBF = re.compile(r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$")


def _blank(s):
    return " ".join(str(s).split()) if s is not None else None


# ---- colours ----------------------------------------------------------------

def rgb(text):
    """(r, g, b) of #rgb, #rrggbb or rgb(r, g, b) (either case), (r, g, b, a)
    of #rrggbbaa (a colour drawn with an opacity below 1); None otherwise."""
    if not isinstance(text, str):
        return None
    t = text.strip().lower()
    m = _HEX8.match(t)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
    m = _HEX6.match(t)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = _HEX3.match(t)
    if m:
        return tuple(int(c * 2, 16) for c in m.group(1))
    m = _RGBF.match(t)
    if m:
        v = tuple(int(x) for x in m.groups())
        return v if all(0 <= x <= 255 for x in v) else None
    return None


def _hex(c):
    return "#" + "".join("%02x" % x for x in c)


def _with_alpha(text, alpha):
    """text's colour as #rrggbb, or #rrggbbaa when alpha is below 1 (D49)."""
    c = rgb(text)
    if c is None:
        return None
    c = c[:3]
    if isinstance(alpha, (int, float)) and 0 <= alpha < 1:
        c = c + (int(round(alpha * 255)),)
    return _hex(c)


def _rgba(c):
    return c if len(c) == 4 else c + (255,)


def _dist(a, b):
    return max(abs(x - y) for x, y in zip(_rgba(a), _rgba(b)))


def _nearest(c, others):
    return min((_dist(c, o) for o in others), default=None)


def colour_diff(tw, da, tol):
    """Each side's readable colours with no counterpart within tol on the other
    side, as sorted #rrggbb lists (D-33-05.b)."""
    a = {rgb(c) for c in tw} - {None}
    b = {rgb(c) for c in da} - {None}
    left = sorted(_hex(c) for c in a if (_nearest(c, b) is None or _nearest(c, b) > tol))
    right = sorted(_hex(c) for c in b if (_nearest(c, a) is None or _nearest(c, a) > tol))
    return left, right


def colour_distances(tw, da):
    """Every readable colour's distance to its nearest colour on the other side."""
    a = {rgb(c) for c in tw} - {None}
    b = {rgb(c) for c in da} - {None}
    if not a or not b:
        return []
    return [_nearest(c, b) for c in sorted(a)] + [_nearest(c, a) for c in sorted(b)]


# ---- twoway's side ----------------------------------------------------------

def _inside(pr, x, y):
    return pr["left"] <= x <= pr["right"] and pr["top"] <= y <= pr["bottom"]


def _panels(doc):
    pr = doc["plotregion"]
    if not pr or not doc["regions"]:
        return 1 if pr else 0
    w, h = pr["right"] - pr["left"], pr["bottom"] - pr["top"]
    n = 0
    for r in doc["regions"]:
        rw, rh = r["right"] - r["left"], r["bottom"] - r["top"]
        if r["fill"] == pr["fill"] and abs(rw - w) <= 0.02 * w and abs(rh - h) <= 0.02 * h:
            n += 1
    return max(n, 1)


def _to_data(fit, p, p_low, p_high):
    if not fit or fit.get("space") != "linear" or fit.get("reversed") or p_high == p_low:
        return None
    return fit["low"] + (p - p_low) * (fit["high"] - fit["low"]) / (p_high - p_low)


def _grid_lines(path, pr):
    """The (px, stroke, width, orientation) of every grid or axis line group."""
    lines = svg_truth.svg_lines(path)
    w, h = pr["right"] - pr["left"], pr["bottom"] - pr["top"]
    out = set()
    for kind, coord, size in (("h", "y1", w), ("v", "x1", h)):
        for g in svg_truth.line_groups(lines[kind], coord):
            if g["span_to"] - g["span_from"] >= 0.95 * size:
                out.add((kind, g["px"], g["stroke"], g["width"]))
    return out


def _region_box(e, regions):
    """True when e is a rect drawing one region's fill or outline."""
    if e["kind"] != "rect":
        return False
    (x0, y0), (x1, y1) = e["points"][0], e["points"][-1]
    for r in regions:
        tol = max(1.0, e.get("stroke_width") or 0.0)
        if abs(x0 - r["left"]) <= tol and abs(y0 - r["top"]) <= tol and \
                abs(x1 - r["right"]) <= tol and abs(y1 - r["bottom"]) <= tol:
            return True
    return False


def _glyph_elements(path, pr, elements, regions):
    """The drawn elements inside the plot region that are glyphs: not the
    region's own fill or outline, not a grid or axis line (D-33-05.b)."""
    grid = _grid_lines(path, pr)
    w, h = pr["right"] - pr["left"], pr["bottom"] - pr["top"]
    out = []
    for e in elements:
        cx, cy = e["center"]
        if not _inside(pr, cx, cy):
            continue
        if e["kind"] == "rect" and e["fill"] == pr.get("fill") or _region_box(e, regions):
            continue
        pts = e["points"]
        if e["kind"] == "line" and len(pts) == 2:
            (x1, y1), (x2, y2) = pts
            if round(y1, 2) == round(y2, 2) and ("h", round(y1, 2), e["stroke"],
                                                 e["stroke_width"]) in grid:
                continue
            if round(x1, 2) == round(x2, 2) and ("v", round(x1, 2), e["stroke"],
                                                 e["stroke_width"]) in grid:
                continue
        if pts and (len({p[1] for p in pts}) == 1 and e["extent"] >= 0.95 * w
                    or len({p[0] for p in pts}) == 1 and e["extent"] >= 0.95 * h):
            continue
        out.append(e)
    return out


#: A text's width estimated as this share of its font size per character.
CHAR_W = 0.5


def _past(x, anchor, size, n, lo, hi):
    """True when a text of n characters at x runs past [lo, hi] (D50)."""
    w = CHAR_W * (size or 0) * n
    left = x - w if anchor == "end" else (x - w / 2.0 if anchor == "middle" else x)
    return left < lo - 1 or left + w > hi + 1


def _twoway_colours(path, pr, elements, regions):
    seen = []
    for e in _glyph_elements(path, pr, elements, regions):
        if e["fill"] not in (None, "none") and e["fill_opacity"] != 0:
            seen.append((e["fill"], e["fill_opacity"]))
        if e["stroke"] not in (None, "none") and e["stroke_opacity"] != 0:
            seen.append((e["stroke"], e["stroke_opacity"]))
    cols = sorted(set(seen), key=str)
    good = sorted({_with_alpha(c, a) for c, a in cols if rgb(c)})
    return {"set": good, "unread": sum(1 for c, _ in cols if rgb(c) is None)}


def _stroked_width(e):
    return e["stroke_width"] if e["stroke"] not in (None, "none") and \
        e["stroke_opacity"] != 0 and e["stroke_width"] else 0.0


def _label_value(s):
    """svg_truth.label_value, also reading a %e label (1.0e-04)."""
    v = svg_truth.label_value(s)
    if v is None and s is not None:
        t = s.strip().replace("\u2212", "-").replace(",", "")
        if re.fullmatch(r"-?(\d+\.?\d*|\.\d+)[eE][-+]?\d+", t):
            v = float(t)
    return v


def _axis(path, doc, axis):
    """Ticks, labels and fit of the first panel's axis, in data order."""
    r = svg_truth.svg_axis_reading(path, axis, doc=doc)
    pr = r.get("plotregion")
    if pr is None:
        return {"ticks": [], "labels": [], "fit": None, "label_objs": [], "near": None,
                "side": None, "scale": None, "pos": []}
    lo, hi = (pr["left"], pr["right"]) if axis == "x" else (pr["top"], pr["bottom"])
    keep = [k for k, px in enumerate(r["tick_px"]) if lo - 2.5 <= px <= hi + 2.5] \
        if len(r["labels"]) == len(r["tick_px"]) else list(range(len(r["labels"])))
    labels = [r["labels"][k] for k in keep]
    objs = [r["label_objs"][k] for k in keep]
    pxs = [r["tick_px"][k] for k in keep] if len(r["labels"]) == len(r["tick_px"]) else []
    pairs = [(px, _label_value(lb)) for px, lb in zip(pxs, labels)
             if lb is not None and _label_value(lb) is not None]
    edges = (pr["left"], pr["right"]) if axis == "x" else (pr["bottom"], pr["top"])
    fit = svg_truth.fit_axis_mapping(pairs, *edges) if len(pairs) >= 2 else None
    ticks = [v for _, v in pairs]
    texts = [_blank(lb) for lb in labels if lb is not None]
    # The scale: two labelled ticks fit any space, so it needs three (D46).
    scale = None
    if fit and len(pairs) >= 3:
        scale = "log" if fit["space"] == "log10" else "linear"
    lo_px, span = (pr["left"], pr["right"] - pr["left"]) if axis == "x" else \
        (pr["bottom"], pr["top"] - pr["bottom"])
    pos = [round((px - lo_px) / span, 4) for px, _ in pairs] if span else []
    # Pixel order is left to right on x, top to bottom on y: put both in
    # data order (ascending), as dash's axes list them.
    flip = (axis == "y") != bool(fit and fit["reversed"])
    if flip:
        ticks, texts, pos = ticks[::-1], texts[::-1], pos[::-1]
    return {"ticks": ticks, "labels": texts, "fit": fit, "scale": scale, "pos": pos,
            "label_objs": [o for o in objs if o is not None],
            "near": r["label_offaxis_px"], "side": r["tick_side"]}


def _squarish(g):
    """False for a group of rects that is no square marker: a bar (D51)."""
    for e in g:
        if e["kind"] == "rect":
            (x0, y0), (x1, y1) = e["points"][0], e["points"][-1]
            w, h = abs(x1 - x0), abs(y1 - y0)
            if abs(w - h) > 0.25 * max(w, h, 1e-9):
                return False
    return True


def _in_box(r, x, y):
    return r["left"] <= x <= r["right"] and r["top"] <= y <= r["bottom"]


def _turned(t):
    return t["rotate"] is not None and abs(abs(t["rotate"]) - 90) < 1


def twoway_geometry(svg_path):
    """The checks' values read from twoway's SVG (D-33-05.b); a by() graph's
    first panel only."""
    doc = svg_truth.svg_document(svg_path)
    pr = doc["plotregion"]
    out = {"panels": _panels(doc), "x_ticks": [], "y_ticks": [], "x_labels": [],
           "y_labels": [], "axis_titles": [], "titles": [], "legend": [], "glyphs": None,
           "glyph_counts": [], "glyph_extents": None, "markers": [], "marker_shape": [],
           "frame_aspect": None, "colours": {"set": [], "unread": 0}, "x_span": None,
           "y_span": None, "x_scale": None, "y_scale": None, "x_tick_pos": [],
           "y_tick_pos": [], "text_size": None,
           "insets": None, "marker_sizes": [], "line_widths": [], "labels_outside": None,
           "line_widths_lines": [], "outlined": None}
    if pr is None:
        return out
    x, y = _axis(svg_path, doc, "x"), _axis(svg_path, doc, "y")
    out.update(x_ticks=x["ticks"], y_ticks=y["ticks"], x_labels=x["labels"],
               y_labels=y["labels"], x_scale=x["scale"], y_scale=y["scale"],
               x_tick_pos=x["pos"], y_tick_pos=y["pos"])
    for k, a in (("x_span", x), ("y_span", y)):
        if a["fit"]:
            out[k] = a["fit"]["high"] - a["fit"]["low"]
    w, h = pr["right"] - pr["left"], pr["bottom"] - pr["top"]
    out["frame_aspect"] = w / h if h else None
    used = {id(o) for o in x["label_objs"] + y["label_objs"]}
    texts = [t for t in doc["texts"] if id(t) not in used and t["text"].strip()
             and t["x"] is not None and t["y"] is not None]
    # Regions outside the plot region: legend boxes, by() strips, other
    # panels (svg_document's regions also hold every solid bar).
    others = [r for r in doc["regions"][1:]
              if not (_in_box(pr, r["left"], r["top"]) and _in_box(pr, r["right"], r["bottom"]))]
    # The x-axis title: centred text below the x labels, the nearest to them;
    # the y-axis title: turned text on the y labels' side, the nearest.
    below = max(x["near"] if x["near"] is not None else pr["bottom"], pr["bottom"])
    xt = [t for t in texts if t["rotate"] is None and t["anchor"] == "middle"
          and _label_value(t["text"]) is None and t["y"] > below
          and t["x"] >= pr["left"] - 0.1 * w
          and not any(_in_box(r, t["x"], t["y"]) for r in others)]
    xt = [t for t in sorted(xt, key=lambda t: t["y"])[:1]
          if out["panels"] > 1 or t["y"] - below <= 4 * (t["size"] or 0)]
    right = y["side"] == "right of plotregion"
    yt = [t for t in texts if _turned(t)
          and (t["x"] > pr["right"] if right else t["x"] < pr["left"])]
    yt = sorted(yt, key=lambda t: abs(t["x"] - (pr["right"] if right else pr["left"])))[:1]
    out["axis_titles"] = [_blank(t["text"]) for t in xt + yt]
    taken = {id(t) for t in xt + yt}
    legend, titles = [], []
    for t in texts:
        if id(t) in taken or _in_box(pr, t["x"], t["y"]):
            continue
        boxed = any(_in_box(r, t["x"], t["y"]) for r in others)
        if t["anchor"] is None and boxed:
            legend.append(_blank(t["text"]))
        elif not boxed and not _turned(t) and _label_value(t["text"]) is None:
            titles.append(t)
    out["legend"] = legend
    # Marker labels (texts anchored inside the plot region): does any run
    # past it?  twoway lets them (D50, MS-15).
    labs = [t for t in texts if id(t) not in taken and _in_box(pr, t["x"], t["y"])]
    if labs:
        out["labels_outside"] = any(_past(t["x"], t["anchor"], t["size"], len(t["text"]),
                                          pr["left"], pr["right"]) for t in labs)
    # A title by() repeats on every panel is read once.
    out["titles"] = list(dict.fromkeys(
        t["text"].strip() for t in sorted(titles, key=lambda t: (t["y"], t["x"]))))
    # Markers inside the plot region: small groups svg_layer names a shape.
    els = svg_layer.svg_elements(svg_path)
    small = 0.05 * min(w, h)
    inside = [e for e in els if _inside(pr, *e["center"]) and not _region_box(e, [pr])]
    groups = [g for g in svg_layer.markers(inside) if svg_layer.marker_shape(g)
              and max(e["extent"] for e in g) <= small and _squarish(g)]
    by_colour = {}
    total = 0
    for g in groups:
        # Markers drawn at one spot fall in one group: count its copies of
        # the group's first element.
        k0 = g[0]
        copies = sum(1 for e in g if (e["kind"], e["fill"], e["stroke"], e["points"]) ==
                     (k0["kind"], k0["fill"], k0["stroke"], k0["points"]))
        total += copies
        cx, cy = g[0]["center"]
        dx = _to_data(x["fit"], cx, pr["left"], pr["right"])
        dy = _to_data(y["fit"], cy, pr["bottom"], pr["top"])
        out["markers"].append((dx, dy, svg_layer.marker_shape(g)))
        col = next((e["fill"] for e in g if e["fill"] not in (None, "none")),
                   next((e["stroke"] for e in g if e["stroke"] not in (None, "none")), None))
        by_colour[col] = by_colour.get(col, 0) + copies
    out["glyphs"] = total or None
    out["glyph_counts"] = sorted(by_colour.values(), reverse=True)
    out["marker_shape"] = sorted({m[2] for m in out["markers"]})
    pts = [(m[0], m[1]) for m in out["markers"]]
    if pts and all(p[0] is not None and p[1] is not None for p in pts):
        out["glyph_extents"] = {"x": [min(p[0] for p in pts), max(p[0] for p in pts)],
                                "y": [min(p[1] for p in pts), max(p[1] for p in pts)]}
    out["colours"] = _twoway_colours(svg_path, pr, els, [pr])
    # D49: text size, outer insets, marker size and line width, each
    # relative to the canvas.
    cv = doc["canvas"]
    if cv and cv["w"] and cv["h"]:
        cw, ch = cv["w"], cv["h"]
        sizes = sorted(o["size"] for o in x["label_objs"] + y["label_objs"] if o.get("size"))
        if sizes:
            out["text_size"] = round(sizes[len(sizes) // 2] / cw, 5)
        out["insets"] = [round(pr["left"] / cw, 4), round(pr["top"] / ch, 4),
                         round((cw - pr["right"]) / cw, 4), round((ch - pr["bottom"]) / ch, 4)]
        out["marker_sizes"] = sorted({round(max(e["extent"] + _stroked_width(e) for e in g) / cw, 5)
                                      for g in groups})
        in_groups = {id(e) for g in groups for e in g}
        glyphs = [e for e in _glyph_elements(svg_path, pr, els, [pr]) if id(e) not in in_groups]
        filled = [e for e in glyphs if e["kind"] in ("rect", "path", "polygon")
                  and e["fill"] not in (None, "none") and e["fill_opacity"] != 0]
        shapes = {tuple(e["points"]) for e in filled}

        def outline(e):
            # A bar's outline rect, or a path tracing a filled area's edge.
            return _stroked_width(e) and (e["kind"] == "rect" or tuple(e["points"]) in shapes)
        out["line_widths"] = sorted({round(_stroked_width(e) / cw, 5)
                                     for e in glyphs if _stroked_width(e)})
        out["line_widths_lines"] = sorted({round(_stroked_width(e) / cw, 5)
                                           for e in glyphs if _stroked_width(e)
                                           and not outline(e)})
        if filled:
            out["outlined"] = any(outline(e) for e in glyphs)
    return out


# ---- dash's side ------------------------------------------------------------

def _written(v):
    """(kind, value) of a dumped property: ("value", v), ("field", None) or ("none", None)."""
    if v is None:
        return "none", None
    if isinstance(v, dict):
        if "field" in v or "expr" in v:
            return "field", None
        if "value" in v:
            return ("none", None) if v["value"] is None else ("value", v["value"])
        return "none", None
    return "value", v


def _alpha_zero(v):
    k, a = _written(v)
    return k == "value" and isinstance(a, (int, float)) and a == 0


def _pick_axis(axes, dim, side):
    own = [a for a in axes if a.get("dim") == dim]
    for a in own:
        if a.get("side") == side:
            return a
    return own[0] if own else None


_SVG_TEXT = re.compile(r"<text\b[^>]*>([^<]*)</text>")
_SVG_TEXT_SIZE = re.compile(r"<text\b[^>]*\bfont-size=\"([0-9.]+)(px|pt)\"[^>]*>([^<]*)</text>")


def _num(v):
    k, x = _written(v)
    return x if k == "value" and isinstance(x, (int, float)) else None


_SVG_TEXT_FULL = re.compile(r"(<g clip-path=\"[^\"]*\">)?<text\b([^>]*)>([^<]*)</text>")


def _dash_labels_outside(text, lo, hi, top, bottom):
    """D50: True when a text drawn without a clip runs past the frame from an
    anchor inside it; False when the frame's texts all stay in it (a text
    under a clip-path is cut at the frame); None when there is none."""
    seen = None
    for clip, attrs, body in _SVG_TEXT_FULL.findall(text):
        a = dict(re.findall(r'([\w:-]+)="([^"]*)"', attrs))
        try:
            x, y = float(a.get("x")), float(a.get("y"))
        except (TypeError, ValueError):
            continue
        if clip:
            seen = bool(seen)
            continue
        if not (lo <= x <= hi and top <= y <= bottom):
            continue
        m = re.match(r"([0-9.]+)(px|pt)", a.get("font-size", ""))
        size = float(m.group(1)) * (4.0 / 3.0 if m.group(2) == "pt" else 1.0) if m else 0.0
        past = _past(x, a.get("text-anchor"), size, len(svg_truth.normalise_text(body)), lo, hi)
        seen = bool(seen) or past
    return seen


#: Glyphs that fill a bar or an area; their line is an outline (D51).
_AREA_GLYPHS = ("VBar", "HBar", "Quad", "Rect", "Block", "Patch", "Patches", "VArea", "HArea",
                "VAreaStep", "HAreaStep", "VStrip", "HStrip")


def _dash_sizes(out, f, figs, svg_path):
    """D49: text size, outer insets, marker size and line width of figure f,
    each relative to the page the figures fill."""
    boxes = [g.get("bbox") for g in figs if g.get("bbox") and len(g["bbox"]) == 4]
    if not boxes:
        return
    pw = max(b[0] + b[2] for b in boxes)
    ph = max(b[1] + b[3] for b in boxes)
    bb, fr = f.get("bbox"), f.get("frame")
    if not (pw and ph):
        return
    if bb and fr and len(fr) == 4:
        fx, fy = bb[0] + fr[0], bb[1] + fr[1]
        out["insets"] = [round(fx / pw, 4), round(fy / ph, 4),
                         round((pw - fx - fr[2]) / pw, 4), round((ph - fy - fr[3]) / ph, 4)]
    if svg_path is not None:
        labels = set(out["x_labels"] + out["y_labels"])
        sizes = sorted(float(n) * (4.0 / 3.0 if u == "pt" else 1.0)
                       for n, u, t in _SVG_TEXT_SIZE.findall(_read(svg_path))
                       if _blank(svg_truth.normalise_text(t)) in labels)
        if sizes:
            out["text_size"] = round(sizes[len(sizes) // 2] / pw, 5)
        if bb and fr and len(fr) == 4:
            out["labels_outside"] = _dash_labels_outside(_read(svg_path), fx, fx + fr[2],
                                                         fy, fy + fr[3])
    marks, widths, lines, outlined = set(), set(), set(), None
    for r in f.get("renderers") or []:
        if r.get("visible") is False:
            continue
        lw = _num(r.get("line_width")) or 0.0
        drawn = _written(r.get("line"))[0] == "value" and not _alpha_zero(r.get("line_alpha"))
        if r.get("glyph") == "Scatter":
            size = _num(r.get("size"))
            if size and (r.get("n") or 0) > 0:
                marks.add(round((size + (lw if drawn else 0.0)) / pw, 5))
        elif r.get("glyph") in _AREA_GLYPHS and \
                _written(r.get("fill"))[0] != "none" and not _alpha_zero(r.get("fill_alpha")):
            stroked = bool(drawn and lw)
            outlined = bool(outlined) or stroked
            if stroked:
                widths.add(round(lw / pw, 5))
        elif drawn and lw:
            widths.add(round(lw / pw, 5))
            lines.add(round(lw / pw, 5))
    out["marker_sizes"] = sorted(marks)
    out["line_widths"] = sorted(widths)
    out["line_widths_lines"] = sorted(lines)
    out["outlined"] = outlined


def dash_geometry(view, svg_path=None):
    """The checks' values read from a 33-04 view dump (D-33-05.b).  With
    svg_path (dash's exported SVG), a legend label the picture does not draw
    as text -- a hidden legend, which the dump does not mark -- is left out."""
    figs = [f for f in ((view or {}).get("figures") or []) if isinstance(f, dict)]
    out = {"panels": sum(1 for f in figs if f.get("axes")), "x_ticks": [], "y_ticks": [], "x_labels": [],
           "y_labels": [], "axis_titles": [], "titles": [], "legend": [], "glyphs": None,
           "glyph_counts": [], "glyph_extents": None, "markers": [], "marker_shape": [],
           "frame_aspect": None, "colours": {"set": [], "unread": 0}, "x_scale": None,
           "y_scale": None, "x_tick_pos": [], "y_tick_pos": [], "text_size": None,
           "insets": None, "marker_sizes": [], "line_widths": [], "labels_outside": None,
           "line_widths_lines": [], "outlined": None}
    if not figs:
        return out
    f = next((g for g in figs if g.get("axes")), figs[0])
    axes = f.get("axes") or []
    xa, ya = _pick_axis(axes, 0, "below"), _pick_axis(axes, 1, "left")
    for k, a in (("x", xa), ("y", ya)):
        if a:
            out[k + "_ticks"] = [t for t in (a.get("ticks") or []) if isinstance(t, (int, float))]
            out[k + "_labels"] = [_blank(lb) for lb in (a.get("labels") or []) if lb is not None
                                  and _blank(lb)]
            out[k + "_scale"] = a.get("scale")
            fr = f.get("frame")
            px = a.get("tick_px") or []
            if fr and len(fr) == 4 and fr[2] and fr[3]:
                # Shares of the plot region from its low edge (left; bottom).
                out[k + "_tick_pos"] = [
                    round((p - fr[0]) / fr[2] if k == "x" else (fr[1] + fr[3] - p) / fr[3], 4)
                    for p in px if isinstance(p, (int, float))]
    def texts(g):
        return [t for t in (g.get("titles") or [])
                if isinstance(t.get("text"), str) and t["text"].strip()]
    panels = [g for g in figs if g.get("axes")]
    cells = [g for g in figs if not g.get("axes")]
    own = texts(f)
    if len(panels) > 1:
        # A by() graph: a title whose text differs between the panels at the
        # same place is the panel's own label (twoway draws it in a strip).
        others = [texts(g) for g in panels[1:]]
        own = [t for k, t in enumerate(own)
               if all(k < len(o) and o[k]["text"] == t["text"] for o in others)]
    x_title = xa.get("title") if xa else None
    y_title = ya.get("title") if ya else None
    # by()'s shared axis titles sit in cells of their own: the y title on a
    # cell's left; the x title in a cell below the panels -- the first of
    # two cells with a title below (the note's comes last), or a lone one
    # narrower than the page (the note's cell spans the page).
    below = [g for g in cells if any(t.get("side") == "below" for t in texts(g))]
    page = max(((g.get("bbox") or [0, 0, 0])[0] + (g.get("bbox") or [0, 0, 0])[2]
                for g in figs), default=0)
    x_cell = None
    if len(panels) > 1 and not x_title and below:
        bb = below[0].get("bbox") or [0, 0, page]
        if len(below) > 1 or bb[2] < page - 1:
            x_cell = below[0]
    rest = []
    for g in cells:
        for t in texts(g):
            if t.get("side") == "left" and not y_title:
                y_title = t["text"]
            elif g is x_cell and t.get("side") == "below" and not x_title:
                x_title = t["text"]
            else:
                rest.append(t)
    out["axis_titles"] = [_blank(t) for t in (x_title, y_title) if t and _blank(t)]
    # One title per drawn line (dash keeps a multi-line title as one text).
    out["titles"] = list(dict.fromkeys(
        ln.strip() for t in own + rest for ln in t["text"].split("\n") if ln.strip()))
    legend = [_blank(it["label"]) for it in (f.get("legend") or [])
              if it.get("label") is not None and _blank(it["label"])]
    if svg_path is not None and legend:
        drawn = collections.Counter(_blank(svg_truth.normalise_text(t))
                                    for t in _SVG_TEXT.findall(_read(svg_path)))
        for g in figs:
            for a in g.get("axes") or []:
                drawn.subtract(_blank(lb) for lb in (a.get("labels") or []) if lb)
                if a.get("title"):
                    drawn.subtract([_blank(a["title"])])
            drawn.subtract(_blank(t["text"]) for t in texts(g))
        kept = []
        for lb in legend:
            if drawn[lb] > 0:
                drawn[lb] -= 1
                kept.append(lb)
        legend = kept
    out["legend"] = legend
    fr = f.get("frame")
    if fr and len(fr) == 4 and fr[2] and fr[3]:
        out["frame_aspect"] = fr[2] / fr[3]
    _dash_sizes(out, f, figs, svg_path)
    seen, unread, counts, shapes, xs, ys = [], 0, [], set(), [], []
    for r in f.get("renderers") or []:
        if r.get("visible") is False:
            continue
        for key, alpha in (("fill", "fill_alpha"), ("line", "line_alpha")):
            k, c = _written(r.get(key))
            if k == "field":
                unread += 1
            elif k == "value" and not _alpha_zero(r.get(alpha)):
                if rgb(c) is None:
                    unread += 1
                else:
                    ka, a = _written(r.get(alpha))
                    seen.append(_with_alpha(c, a if ka == "value" else None))
        if r.get("glyph") == "Scatter" and (r.get("n") or 0) > 0:
            counts.append(r["n"])
            m = r.get("marker")
            for name in (m if isinstance(m, list) else [m]):
                if isinstance(name, str):
                    shapes.add(BOKEH_SHAPES.get(name, name))
            if r.get("x") and r.get("y"):
                xs += list(r["x"])
                ys += list(r["y"])
    out["colours"] = {"set": sorted(set(seen)), "unread": unread}
    out["glyphs"] = sum(counts) if counts else None
    out["glyph_counts"] = sorted(counts, reverse=True)
    out["marker_shape"] = sorted(shapes)
    out["markers"] = [(None, None, s) for s in sorted(shapes)]
    if xs and ys:
        out["glyph_extents"] = {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)]}
    return out


# ---- the comparison ---------------------------------------------------------

def _diff(check, tw, da):
    return {"check": check, "twoway": tw, "dash": da, "within_tol": False}


def _span(vals, given):
    if given:
        return abs(given)
    vals = [v for v in vals if isinstance(v, (int, float))]
    s = (max(vals) - min(vals)) if vals else 0.0
    return s or 1.0


def _sizes_differ(a, b, rel):
    return any(not any(abs(x - y) <= rel * x for y in b) for x in a) or \
        any(not any(abs(x - y) <= rel * y for x in a) for y in b)


def _size_checks(tw, da, rules):
    """D49: text size, margins, marker size and line width."""
    out = []
    a, b = tw.get("text_size"), da.get("text_size")
    if a and b and abs(a - b) > rules.get("text_rel", 0.05) * a:
        out.append(_diff("text_size", a, b))
    a, b = tw.get("insets"), da.get("insets")
    if a and b and max(abs(x - y) for x, y in zip(a, b)) > rules.get("inset_abs", 0.005):
        out.append(_diff("margins", a, b))
    extra = tw.get("outlined") is False and da.get("outlined") is True
    if extra:
        out.append(_diff("outline_extra", False, True))
    for k, check in (("marker_sizes", "marker_size"), ("line_widths", "line_width")):
        a, b = tw.get(k) or [], da.get(k) or []
        if extra and k == "line_widths":
            # dash's extra outline is outline_extra's, not a line width.
            b = da.get("line_widths_lines") or []
        if a and b and _sizes_differ(a, b, rules.get("size_rel", 0.05)):
            out.append(_diff(check, a, b))
    return out


def compare(tw, da, rules):
    """One dict per check outside tolerance: check, twoway, dash, within_tol."""
    out = []
    for ax in ("x", "y"):
        a, b = tw.get(ax + "_ticks") or [], da.get(ax + "_ticks") or []
        if a and b:
            span = _span(a, tw.get(ax + "_span"))
            tol = rules["tick_rel"] * span
            if len(a) != len(b) or any(abs(p - q) > tol for p, q in zip(a, b)):
                out.append(_diff(ax + "_ticks", a, b))
    for ax in ("x", "y"):
        a, b = tw.get(ax + "_scale"), da.get(ax + "_scale")
        if a in ("linear", "log") and b in ("linear", "log") and a != b:
            out.append(_diff(ax + "_scale", a, b))
    for ax in ("x", "y"):
        a, b = tw.get(ax + "_labels") or [], da.get(ax + "_labels") or []
        if a != b:
            # twoway leaving an axis unlabelled is its own check (D48, BY-32).
            out.append(_diff(ax + ("_labels_none" if not a else "_labels"), a, b))
    for k in ("axis_titles", "titles", "legend"):
        if (tw.get(k) or []) != (da.get(k) or []):
            out.append(_diff(k, tw.get(k) or [], da.get(k) or []))
    if tw.get("glyphs") and da.get("glyphs"):
        a, b = tw.get("glyph_counts") or [], da.get("glyph_counts") or []
        if len(a) == len(b) and len(a) > 1:
            if a != b:
                out.append(_diff("glyphs", a, b))
        elif tw["glyphs"] != da["glyphs"]:
            out.append(_diff("glyphs", tw["glyphs"], da["glyphs"]))
    out += _size_checks(tw, da, rules)
    a, b = tw.get("labels_outside"), da.get("labels_outside")
    if a is not None and b is not None and a != b:
        out.append(_diff("marker_labels", a, b))
    te, de = tw.get("glyph_extents"), da.get("glyph_extents")
    if te and de:
        for ax in ("x", "y"):
            span = _span(te[ax], tw.get(ax + "_span"))
            tol = rules["extent_rel"] * span
            if any(abs(p - q) > tol for p, q in zip(te[ax], de[ax])):
                out.append(_diff("glyph_extents", te, de))
                break
    if tw.get("marker_shape") and da.get("marker_shape") and \
            set(tw["marker_shape"]) != set(da["marker_shape"]):
        out.append(_diff("marker_shape", sorted(tw["marker_shape"]), sorted(da["marker_shape"])))
    fa, fb = tw.get("frame_aspect"), da.get("frame_aspect")
    if fa is not None and fb is not None and abs(fa - fb) > rules["aspect_abs"]:
        out.append(_diff("frame_aspect", round(fa, 4), round(fb, 4)))
    ca = (tw.get("colours") or {}).get("set") or []
    cb = (da.get("colours") or {}).get("set") or []
    if ca and cb:
        left, right = colour_diff(ca, cb, rules.get("colour_tol", 0))
        if left or right:
            out.append(_diff("colours", left, right))
    return out


# ---- the ledger -------------------------------------------------------------

def load_ledger(path):
    """The rows of a corpus_ledger.json fixture."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["rows"]


def _matches(row, d, example):
    if row["check"] != d["check"]:
        return False
    if row["plottype"] not in ("*", example.get("plottype")):
        return False
    return row["when"] == "*" or bool(re.search(row["when"], example.get("cmd") or ""))


def explain(diffs, example, ledger, states):
    """diffs with gaps4 set to the first live matching row's gaps4_id (or None)."""
    out = []
    for d in diffs:
        d = dict(d)
        d["gaps4"] = None
        for row in ledger:
            if ledger_mod.live(row, states) and _matches(row, d, example):
                d["gaps4"] = row["gaps4_id"]
                break
        out.append(d)
    return out


# ---- the verdict ------------------------------------------------------------

def verdict(rc_tw, rc_da, first_tw, first_da, diffs, s, rules):
    """Same, Close or Differs by D-33-05.a; diffs are explain()'s."""
    unexplained = [d for d in diffs if d.get("gaps4") is None and d["check"] != "image"]
    explained = [d for d in diffs if d.get("gaps4") is not None]
    if rc_tw != 0 and rc_da != 0:
        return "Same" if not diffs else ("Close" if not unexplained else "Differs")
    if (rc_tw == 0) != (rc_da == 0):
        return "Close" if not unexplained else "Differs"
    if unexplained:
        return "Differs"
    if explained:
        return "Close"
    t_same = rules.get("T_same")
    if t_same is None:
        return "Same"
    return "Same" if s is not None and s >= t_same else "Close"


def summary(diffs):
    """The caption line: "Same", or the differences in Stata terms (A-24)."""
    if not diffs:
        return "Same"
    terms = []
    for d in diffs:
        t = STATA_TERMS[d["check"]]
        if t not in terms:
            terms.append(t)
    line = ""
    for t in terms:
        nxt = t if not line else line + ", " + t
        if len(nxt) > SUMMARY_MAX:
            break
        line = nxt
    return line


def gallery(row):
    """True when twoway drew the example and dash's answer is not a documented refusal."""
    if row.get("skip") or row.get("rc_twoway") != 0:
        return False
    if row.get("rc_dash") not in (0, None):
        for d in row.get("differences") or []:
            if d["check"] == "rc" and (d.get("gaps4") or "").endswith("(documented)"):
                return False
    return True


# ---- the image score --------------------------------------------------------

def ssim(a, b):
    """Mean SSIM (Wang 2004, Gaussian window sigma 1.5, L 255) less a 5 px border."""
    import numpy
    from scipy.ndimage import gaussian_filter
    x = numpy.asarray(a, dtype=numpy.float64)
    y = numpy.asarray(b, dtype=numpy.float64)
    if x.shape != y.shape:
        raise ValueError("images differ in size: %s and %s" % (x.shape, y.shape))

    def f(z):
        return gaussian_filter(z, sigma=1.5, truncate=3.5, mode="reflect")
    ux, uy = f(x), f(y)
    vx = f(x * x) - ux * ux
    vy = f(y * y) - uy * uy
    vxy = f(x * y) - ux * uy
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    s = ((2 * ux * uy + c1) * (2 * vxy + c2)) / ((ux * ux + uy * uy + c1) * (vx + vy + c2))
    pad = 5
    return float(s[pad:-pad, pad:-pad].mean())


def raster(probe, svg_text, w, h):
    """The h x w luminance image Chrome draws of svg_text on a white canvas."""
    import numpy
    v = probe.eval_async("(%s)(%s, %d, %d)" % (RASTER_JS, json.dumps(svg_text), int(w), int(h)))
    return numpy.frombuffer(base64.b64decode(v), dtype=numpy.uint8).reshape(int(h), int(w)) \
        .astype(float)


# ---- one example ------------------------------------------------------------

def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _size(tw, da):
    if da.get("w") and da.get("h"):
        return int(da["w"]), int(da["h"])
    return (int(round((tw.get("width_in") or 7.5) * 96)),
            int(round((tw.get("height_in") or 4.5) * 96)))


def _open_probe(run_dir):
    from scripts.corpus import dash_run
    page = os.path.join(run_dir, "raster.html")
    if not os.path.exists(page):
        with open(page, "w", encoding="utf-8") as fh:
            fh.write(RASTER_PAGE)
    return dash_run.CorpusProbe(page, timeout=120, ready=RASTER_READY).__enter__()


def _score(probe, run_dir, tw, da):
    w, h = _size(tw, da)
    own = probe is None
    try:
        if own:
            probe = _open_probe(run_dir)
        a = raster(probe, _read(os.path.join(run_dir, tw["svg"])), w, h)
        b = raster(probe, _read(os.path.join(run_dir, da["svg"])), w, h)
        return round(ssim(a, b), 4)
    except Exception:  # noqa: BLE001 -- no Chrome or a page that will not draw: no score
        return None
    finally:
        if own and probe is not None:
            probe.__exit__(None, None, None)


def judge(example, tw, da, run_dir, rules, ledger, states, probe=None):
    """The verdicts.jsonl row of one example (the Published interface)."""
    tw, da = tw or {}, da or {}
    row = dict.fromkeys(ROW_KEYS)
    row.update(id=example["id"], plottype=example.get("plottype"),
               source=example.get("source"), rc_twoway=tw.get("rc"), rc_dash=da.get("rc"),
               first_twoway=tw.get("first_line"), first_dash=da.get("first_line"),
               differences=[], checks=[], ledger=[],
               colours={"twoway": [], "dash": [], "unread": 0}, gallery=False)
    row["rc_pair"] = [row["rc_twoway"], row["rc_dash"]]
    skip = tw.get("skip") or da.get("skip")
    if not tw:
        skip = skip or "no twoway record"
    elif not da:
        skip = skip or "no dash record"
    elif tw.get("rc") is None or da.get("rc") is None:
        skip = skip or "not run"
    elif tw["rc"] == 0 and da["rc"] == 0 and not (tw.get("svg") and da.get("svg")):
        skip = "no %s picture" % ("twoway" if not tw.get("svg") else "dash")
        if da.get("export_error"):
            skip += ": " + str(da["export_error"])[:200]
    if skip:
        row["skip"] = skip
        return row
    rc_tw, rc_da = tw["rc"], da["rc"]
    s = None
    if rc_tw != 0 or rc_da != 0:
        diffs = []
        if rc_tw != rc_da:
            diffs.append(_diff("rc", "r(%d)" % rc_tw, "r(%d)" % rc_da))
        if rc_tw != 0 and rc_da != 0 and _blank(tw.get("first_line")) != _blank(da.get("first_line")):
            diffs.append(_diff("first_line", tw.get("first_line"), da.get("first_line")))
    else:
        g_tw = twoway_geometry(os.path.join(run_dir, tw["svg"]))
        with open(os.path.join(run_dir, da["view"]), encoding="utf-8") as fh:
            g_da = dash_geometry(json.load(fh), os.path.join(run_dir, da["svg"]))
        diffs = compare(g_tw, g_da, rules)
        row["panels"] = "1 of %d" % max(g_tw["panels"], g_da["panels"], 1)
        row["size_matched"] = da.get("size_matched")
        row["colours"] = {"twoway": g_tw["colours"]["set"], "dash": g_da["colours"]["set"],
                          "unread": g_tw["colours"]["unread"] + g_da["colours"]["unread"]}
        s = _score(probe, run_dir, tw, da)
    diffs = explain(diffs, example, ledger, states)
    v = verdict(rc_tw, rc_da, tw.get("first_line"), da.get("first_line"), diffs, s, rules)
    if rc_tw == 0 and rc_da == 0 and v == "Close" and not diffs:
        # Clean geometry, image score below T_same (or none): the picture.
        diffs.append({"check": "image", "twoway": None, "dash": s, "within_tol": False,
                      "gaps4": None})
    row.update(verdict=v, ssim=s, differences=diffs,
               checks=sorted({d["check"] for d in diffs}),
               ledger=sorted({re.sub(r"\s*\(.*\)$", "", d["gaps4"]) for d in diffs
                              if d["gaps4"]}),
               summary=summary(diffs))
    row["gallery"] = gallery(row)
    return row


def _jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def run(run_dir, rules_path, ledger_path, gaps4_path=None):
    """Judge every example of run_dir; writes verdicts.jsonl; counts per verdict."""
    with open(rules_path, encoding="utf-8") as fh:
        rules = json.load(fh)
    led = load_ledger(ledger_path)
    states = ledger_mod.gaps4_states(gaps4_path)
    examples = sorted(_jsonl(os.path.join(run_dir, "examples.jsonl")), key=lambda e: e["id"])
    tws = {r["id"]: r for r in _jsonl(os.path.join(run_dir, "twoway.jsonl"))}
    das = {r["id"]: r for r in _jsonl(os.path.join(run_dir, "dash.jsonl"))}
    try:
        probe = _open_probe(run_dir)
    except Exception:  # noqa: BLE001 -- no Chrome: every score is missing
        probe = None
    counts = {"Same": 0, "Close": 0, "Differs": 0, "skipped": 0}
    rows = []
    try:
        for e in examples:
            r = judge(e, tws.get(e["id"]), das.get(e["id"]), run_dir, rules, led, states,
                      probe=probe if probe is not None else _NO_PROBE)
            rows.append(r)
            counts[r["verdict"] or "skipped"] += 1
    finally:
        if probe is not None:
            probe.__exit__(None, None, None)
    with open(os.path.join(run_dir, "verdicts.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({k: r[k] for k in ROW_KEYS}) + "\n")
    return counts


class _NoChrome:
    """A probe that cannot draw: every image score is missing."""

    def eval_async(self, expr):
        raise RuntimeError("no Chrome")


_NO_PROBE = _NoChrome()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, metavar="RUN_DIR")
    ap.add_argument("--rules", default=RULES_PATH)
    ap.add_argument("--ledger", default=LEDGER_PATH)
    ap.add_argument("--gaps4", default=os.path.join(REPO, "GAPS4.md"))
    a = ap.parse_args(argv)
    c = run(a.run, a.rules, a.ledger, a.gaps4)
    print("corpus: verdicts Same %(Same)d, Close %(Close)d, Differs %(Differs)d, "
          "skipped %(skipped)d" % c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
