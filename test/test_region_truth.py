"""plotregion()/graphregion()/bgcolor() against twoway's own drawing
(WP-30 P1.20a, section 38).

dash read only color()/fcolor(), lcolor() and lwidth() of a region, under
their full names: ``plotregion(c(red))`` drew nothing, ``none`` drew black,
``%NN`` was dropped, ``style()``, ``lstyle()`` and ``lpattern()`` were
ignored, and ``bgcolor()`` coloured the graph region, where twoway paints it
on the canvas under an opaque graph region (IR-2).  The truth is
``test/fixtures/region_truth.json`` (``scripts/extract_region_truth.do``,
StataNow 19.5): the spellings twoway's region parser accepts (S), its
refusals (R, checked by test_twoway_option_parity.cscript RS-01..RS-04),
the rects it draws under three schemes (D) and for repeated copies (M).
"""

import json
import os
import sys

import pytest
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "region_truth.json"),
          encoding="utf-8") as _fh:
    _FIX = json.load(_fh)
_P = _FIX["probes"]

#: The string dash's Mata merge (_dash_rep_merge, TR-38.6) gives for each M
#: probe's two copies; test_twoway_option_parity.cscript RS-12 holds every
#: one equal to the merge's output.
_MERGED = {
    "M01": ("plotregion", "fcolor(red) lcolor(blue)"),
    "M02": ("plotregion", "color(red)"),
    "M03": ("plotregion", "color(blue)"),
    "M04": ("plotregion", "style(none)"),
    "M05": ("plotregion", "lstyle(none)"),
    "M06": ("plotregion", "color(red)"),
    "M07": ("plotregion", "lcolor(red) fcolor(blue)"),
    "M08": ("plotregion", "style(none) fcolor(red)"),
    "M09": ("graphregion", "fcolor(red) lcolor(blue)"),
}

#: Probes twoway draws with what dash names and does not draw (BR-38.9):
#: the inner boxes, ifcolor() (section 47), and intensity() (a P2 row).
_NAMED_ONLY = {"D37", "D38", "D39"}

_SCHEMES = ("s2color", "stcolor", "s1color")

#: Schemes whose plot region twoway leaves unfilled (s1color's
#: ``shadestyle plotregion none``): the scheme files carry no such key, so
#: dash fills it with ``color plotregion``; a residual of the scheme
#: extractor, not of the region reader.  There the plot fill is compared
#: only where the probe sets one.
_UNFILLED = {s for s in _SCHEMES if _P[f"{s}|D01"]["plot_fill"] is None}


def _opts_of(cmd):
    """The graph options of a probe's twoway command, as dash's spec holds
    them (each region option once, as one merged copy)."""
    tail = cmd.split(",", 1)[1] if "," in cmd else ""
    go = {}
    for tok in dr._dash_by_tokens(tail.strip()):
        name, _, arg = tok.partition("(")
        go[name.strip()] = arg[:-1] if arg.endswith(")") else arg
    return go


def _blend(top, alpha, under):
    return dr._dash_region_blend(top, alpha, under) if top else under


def _want(rec):
    """twoway's composited canvas, graph and plot colours and its outlines."""
    c = rec["canvas"]["fill"]
    gf = rec["graph_fill"]
    g = _blend(gf and gf["fill"], gf and gf["fill_opacity"], c)
    pf = rec["plot_fill"]
    p = _blend(pf and pf["fill"], pf and pf["fill_opacity"], g)

    def line(r):
        if r is None or r["stroke"] in (None, "none") or r["opacity"] == 0:
            return None
        return (r["stroke"], 1.0 if r["opacity"] is None else r["opacity"],
                r["width"], r["dasharray"] is not None)
    return g, p, line(rec["graph_line"]), line(rec["plot_line"])


def _figs(mode, graphs, scheme):
    """{title: figure} for one spec of many one-scatter graphs."""
    spec = tp._spec(graphs=[(f"g{i}", [plot_for("scatter")],
                             dict(go, title=t))
                            for i, (t, go) in enumerate(graphs)],
                    build_options={"scheme": scheme})
    if mode == "saved":
        r, _ = tp._standalone(spec)
        roots = [r._last_layout_root]
    else:
        doc, _ = tp._served(spec)
        roots = doc.roots
    return {f.title.text: f for root in roots
            for f in root.select({"type": figure})}


def _outlined(go):
    """True when the graph region names an outline sub-option (TR-38.4)."""
    t = dr._dash_region_table()
    return any(dr._dash_subopt_canon(k.split("(", 1)[0].strip(), t) in
               ("style", "lstyle", "lcolor", "lwidth", "lpattern", "color")
               for k in dr._dash_by_tokens(go.get("graphregion", "")))


def _graph_line(f):
    """``(colour, alpha, width, dashed)`` of the outline dash draws round
    figure *f*'s graph region (its box's CSS outline, WP-45 GW-6), or
    ``(None, None, None, None)``."""
    import re
    box = getattr(f, "_dash_region_cell", None)
    o = str(dict(getattr(box, "styles", None) or {}).get("outline", ""))
    m = re.match(r"calc\(var\(--dash-k, [0-9.]+\) \* ([0-9.]+)px\) "
                 r"(solid|dashed|dotted) (#[0-9a-f]{6}|rgba\(([0-9]+),"
                 r"([0-9]+),([0-9]+),([0-9.]+)\))$", o)
    if not m:
        return None, None, None, None
    if m.group(3).startswith("#"):
        col, alpha = m.group(3), 1.0
    else:
        col = "#%02x%02x%02x" % tuple(int(m.group(i)) for i in (4, 5, 6))
        alpha = float(m.group(7))
    return col, alpha, float(m.group(1)), m.group(2) != "solid"


def _near(a, b):
    return (a is not None and b is not None and all(
        abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) <= 1 for i in (1, 3, 5)))


class TestTheFixture:
    def test_it_is_stamped(self):
        meta = _FIX["_meta"]
        assert all(k in meta for k in ("stata_version", "born_date",
                                       "dash_commit", "extracted"))
        assert meta["stata_version"].startswith("19.")
        want = ({f"R{i:02d}" for i in range(1, 24)}
                | {f"{s}|D{i:02d}" for s in _SCHEMES for i in range(1, 44)}
                | set(_MERGED) | {"B01"})
        assert want <= set(_P), sorted(want - set(_P))

    def test_the_by_residual_is_recorded(self):
        # by()'s outer graphregion() is IR-9's residual, not drawn here.
        assert _P["B01"]["twoway_draws_outer_graphregion"] is False


class TestTheTable:
    def test_it_is_twoways_parser(self):
        table = dr._dash_region_table()
        bad = []
        for pid, rec in _P.items():
            if not pid.startswith("S|"):
                continue
            _, full, typed = pid.split("|")
            # marginonly's prefixes are typed bare, so m is margin without
            # its argument: refused, and still margin's spelling.
            got = dr._dash_subopt_canon(typed, table)
            if (got == full) != (rec["rc"] == 0):
                bad.append((typed, got, rec["rc"]))
        assert not bad, bad


class TestAgainstTwoway:
    """Every D probe under three schemes and every M probe: the composited
    plot and graph colours, each outline's presence, colour, opacity and
    dash, and widths as ratios to the base probe's, within 2 %."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_probe(self, mode):
        bad = []
        for scheme in _SCHEMES:
            graphs = []
            for i in range(1, 44):
                pid = f"D{i:02d}"
                if pid not in _NAMED_ONLY:
                    graphs.append((pid, _opts_of(_P[f"{scheme}|{pid}"]["cmd"])))
            if scheme == "s2color":
                graphs += [(m, {o: v}) for m, (o, v) in _MERGED.items()]
            figs = _figs(mode, graphs, scheme)
            base_tw = _P[f"{scheme}|D01"]
            base = figs["D01"]
            for pid, go in graphs:
                rec = _P[pid] if pid.startswith("M") else _P[f"{scheme}|{pid}"]
                f = figs[pid]
                g, p, gl, pl = _want(rec)
                if not _near(f.border_fill_color, g):
                    bad.append((scheme, pid, "graph", f.border_fill_color, g))
                if scheme in _UNFILLED and rec["plot_fill"] is None:
                    pass
                elif not _near(f.background_fill_color, p):
                    bad.append((scheme, pid, "plot", f.background_fill_color, p))
                # WP-45 GW-6: the graph's outline is its graph region
                # box's CSS outline, at the graph's edge.
                gcol, galpha, gwidth, gdash = _graph_line(f)
                for role, want, col, alpha, width, dash, tw0, d0 in (
                        ("plot_line", pl, f.outline_line_color,
                         f.outline_line_alpha, f.outline_line_width,
                         f.outline_line_dash, base_tw["plot_line"]["width"],
                         base.outline_line_width),
                        ("graph_line", gl, gcol, galpha, gwidth, gdash,
                         base_tw["graph_line"]["width"],
                         _graph_line(base)[2])):
                    # Flipped (WP-45 GW-6): the skip "dash draws no graph
                    # outline unasked" is gone -- twoway strokes it in the
                    # scheme's colour, and so does dash now.
                    if (col is None) != (want is None):
                        bad.append((scheme, pid, role, col, want))
                        continue
                    if want is None:
                        continue
                    got = (str(col).lower(), round(float(alpha), 3),
                           round(width / d0, 2), bool(dash))
                    exp = (want[0], round(want[1], 3),
                           round(want[2] / tw0, 2), want[3])
                    if (got[0], got[1], got[3]) != (exp[0], exp[1], exp[3]) \
                            or abs(got[2] - exp[2]) > 0.02 * exp[2]:
                        bad.append((scheme, pid, role, got, exp))
        assert not bad, bad
