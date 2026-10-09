"""Read a colorvar() layer's colours from Bokeh models (WP-29 S07, P0.16).

Every test that reads a colour mapping goes through here, so none
hard-codes the name of the derived colour column: since WP-29 P0.16 it is
``__dash_cvar<k>_<var>``, unique per layer, and a missing value is None
drawn in the mapper's ``nan_color``.

Each function takes either Bokeh models or the plain dict specs a model's
property can hold (``{"field": ..., "transform": ...}``), as
``test_help_claims_7._colour_mapped_one`` does.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402


def _get(spec, key):
    if isinstance(spec, dict):
        return spec.get(key)
    return getattr(spec, key, None)


def _figures(model):
    """The figures under *model* (a Document, a layout, a figure or a list
    of them) in layout order: rows, columns, grid cells and tabs in the
    order the page lays them out."""
    out, seen = [], set()

    def visit(m):
        if m is None or isinstance(m, (int, float, str)):
            return
        if isinstance(m, (list, tuple)):
            for x in m:
                visit(x)
            return
        if id(m) in seen:
            return
        seen.add(id(m))
        if type(m).__name__ == "figure":
            out.append(m)
            return
        roots = getattr(m, "roots", None)
        if roots is not None and not hasattr(m, "children"):
            visit(list(roots))
            return
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                visit(k)

    visit(model)
    return out


def _colour_spec(renderer):
    g = getattr(renderer, "glyph", None)
    if g is None:
        return None
    for attr in ("fill_color", "line_color"):
        v = getattr(g, attr, None)
        if _get(v, "transform") is not None and isinstance(
                _get(v, "field"), str):
            return v
    return None


def colour_renderers(model):
    """The colour-mapped GlyphRenderers under *model*, a colour key's
    invisible swatches excluded, in figure and renderer order."""
    out = []
    for f in _figures(model):
        for r in f.renderers:
            if dr._dash_is_swatch(r):
                continue
            if _colour_spec(r) is not None:
                out.append(r)
    return out


def colour_field(renderer):
    """The column *renderer*'s colour is read from, or None."""
    spec = _colour_spec(renderer)
    return None if spec is None else _get(spec, "field")


def colour_mapper(renderer):
    """The colour mapper (the field spec's transform), or None."""
    spec = _colour_spec(renderer)
    return None if spec is None else _get(spec, "transform")


def colour_values(renderer):
    """Every row's value in the colour column, as a list."""
    field = colour_field(renderer)
    if field is None:
        return []
    return list(renderer.data_source.data.get(field, []))


def drawn_colour_values(renderer):
    """The colour values of the rows *renderer* draws, through its view
    (a BooleanFilter or an IndexFilter)."""
    vals = colour_values(renderer)
    view = getattr(renderer, "view", None)
    flt = getattr(view, "filter", None) if view is not None else None
    idx = getattr(flt, "indices", None) if flt is not None else None
    if idx is not None:
        return [vals[i] for i in idx if i < len(vals)]
    bools = getattr(flt, "booleans", None) if flt is not None else None
    if bools is not None:
        return [v for v, b in zip(vals, bools) if b]
    return vals


def _key_cells(model):
    """The by() colour-key cells (``dash_by_clegend``, WP-30 P1.15c) under
    *model*: bare Plots beside the panels, holding the one key."""
    roots = list(getattr(model, "roots", None) or [model])
    out = []
    for r in roots:
        for m in (r.references() if hasattr(r, "references") else ()):
            if getattr(m, "name", None) == "dash_by_clegend" and m not in out:
                out.append(m)
    return out


def colour_bars(model):
    """(low, high) of every ColorBar's mapper under *model*, a by() grid's
    colour-key cell included."""
    out = []
    for f in _figures(model) + _key_cells(model):
        for side in ("right", "left", "above", "below", "center"):
            for a in getattr(f, side):
                # A by() panel label's box is a one-colour ColorBar named
                # dash_by_label_box (WP-30 P1.15c), not a colour key.
                if type(a).__name__ == "ColorBar" and \
                        a.name != "dash_by_label_box":
                    m = a.color_mapper
                    out.append((m.low, m.high))
    return out


def colour_keys(model):
    """How many colour keys *model* draws: ColorBars plus Legends named
    ``dr._COLORVAR_LEGEND_NAME``."""
    n = 0
    for f in _figures(model):
        for side in ("right", "left", "above", "below", "center"):
            for a in getattr(f, side):
                tn = type(a).__name__
                if (tn == "ColorBar" and a.name != "dash_by_label_box") or (
                        tn == "Legend"
                        and str(a.name or "") == dr._COLORVAR_LEGEND_NAME):
                    n += 1
    return n


def interval_bounds(labels):
    """Each interval label as ``(lo, hi)`` floats: thousands commas are
    stripped, the parts split on U+2013, and ``≤x`` reads as ``(None, x)``
    and ``>x`` as ``(x, None)``.  A label that is not an interval is
    ``(None, None)``."""
    out = []
    for lab in labels:
        t = str(lab).replace(",", "").strip()
        try:
            if t.startswith("≤"):
                out.append((None, float(t[1:])))
            elif t.startswith(">"):
                out.append((float(t[1:]), None))
            elif "–" in t:
                a, b = t.split("–", 1)
                out.append((float(a), float(b)))
            else:
                out.append((None, None))
        except ValueError:
            out.append((None, None))
    return out


def figures_by_title(model):
    """{title text: figure} for every figure under *model*."""
    out = {}
    for f in _figures(model):
        t = getattr(getattr(f, "title", None), "text", None)
        out[t] = f
    return out
