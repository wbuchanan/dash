"""Marker-label and colour-key chrome from the scheme (WP-30 P1.4b).

twoway draws a marker label in the scheme's marker-label style --
``color p#label`` -> ``plabel`` -> ``p#`` -> ``p`` with that colour's
opacity, and ``gsize p#label`` -> ``plabel`` -- at its own layer's index,
and a ``colorvar()`` colour key with the scheme's tick-label and axis-title
text and its tick style, on the graph region.  dash drew every label
#444444 at 10px and the key as a white box with #444444 text under every
scheme.

The truth is ``test/fixtures/scheme_layer_truth.json``'s ``s33`` probes
(``scripts/extract_scheme_layer_truth.do``, live twoway SVG exports).  A
size is compared in Stata's relative units: twoway's font-size over a
hundredth of the canvas's smaller side against dash's
``css_to_pt(size) / PT_PER_RS``, within 1%.  Each fixture group is checked
by one test per mode that loops over every row and reports every mismatch.
"""

import json
import math
import os
import re
import sys

import pytest
from bokeh.models import ColorBar, CustomJS, LabelSet, LinearAxis

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_served_linked_views as tlv  # noqa: E402
from test_scheme_resolution import MODES, _draw, _props_scheme  # noqa: E402
from test_scheme_review_fixes import _user_scheme  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

T = dr.OptionTranslator
FIXTURE = os.path.join(_HERE, "fixtures", "scheme_layer_truth.json")

#: The user schemes of the fixture's probes (plan section 33, Stata truth).
W33A = ["#include s2color", "color plabel green", "gsize plabel large"]
W33B = ["#include s2color", "color p1label blue", "gsize p1label vlarge",
        "color plabel green"]
W33C = ["#include s2color", "color label white", "gsize label huge"]
W33D = ["#include s2color", "color p1 red"]
W33K = ["#include s2color", "gsize axis_title vlarge", "color axis_title red",
        "gsize tick_label small", "color tick_label blue"]
W33T = ["#include s2color", "color axisline orange", "color tick purple",
        "color clegend_line green", "color clegend blue"]
USER = {"w33a": W33A, "w33b": W33B, "w33c": W33C, "w33d": W33D,
        "w33k": W33K, "w33t": W33T}

_LABELLED = {"mlabel": "mpg"}


# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release


def _s33():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _schemes_in_cwd(tmp_path, monkeypatch):
    """Write every user scheme into *tmp_path*, the working directory."""
    for name, lines in USER.items():
        _user_scheme(tmp_path, monkeypatch, f"{name}.scheme", lines)


def _rs(css):
    return T.css_to_pt(css) / T.PT_PER_RS


def _close(a, b):
    return a is not None and b is not None and abs(a - b) <= 0.01 * b


def _labels(drawn):
    """The LabelSets of each figure, in the order the layers drew them."""
    return [m for f in drawn.figures for m in f.center
            if isinstance(m, LabelSet)]


def _key_chrome(cell):
    """A key cell's chrome as a ColorBar's attributes: its axis's labels and
    ticks, its title Label, its own background (WP-42 CV-3)."""
    from types import SimpleNamespace
    ax, tl = cell._dash_key_axis, cell._dash_key_title
    return SimpleNamespace(
        major_label_text_color=ax.major_label_text_color,
        major_label_text_font_size=ax.major_label_text_font_size,
        title_text_color=tl.text_color,
        title_text_font_size=tl.text_font_size,
        title_text_font_style=tl.text_font_style,
        background_fill_alpha=cell.background_fill_alpha,
        major_tick_line_color=ax.major_tick_line_color,
        major_tick_in=ax.major_tick_in, major_tick_out=ax.major_tick_out)


def _colorbar(drawn):
    """The colour key's chrome.  Flipped (WP-42 CV-3): it was a ColorBar;
    twoway draws swatches beside a z axis, a key cell, whose axis and
    title carry the same chrome."""
    cells = [c for f in drawn.figures
             for c in ([f] if "dash_key_cell" in (f.tags or [])
                       else [getattr(f, "_dash_key_cell", None)])
             if c is not None]
    if cells:
        (cell,) = {id(c): c for c in cells}.values()
        return _key_chrome(cell)
    (bar,) = [m for f in drawn.figures for m in f.select({"type": ColorBar})]
    return bar


def _draw_plots(plots, scheme, mode, graph_options=None):
    return _draw(tp._spec(plots, {"scheme": scheme}, graph_options or {}),
                 mode)


def _label_mismatch(where, ls, fill, size_rs, opacity):
    """Every way LabelSet *ls* differs from twoway's (fill, size, opacity)."""
    out = []
    if str(ls.text_color).lower() != fill.lower():
        out.append(f"{where}: colour {ls.text_color} != twoway {fill}")
    if not _close(_rs(ls.text_font_size), size_rs):
        out.append(f"{where}: size {ls.text_font_size} "
                   f"({_rs(ls.text_font_size):.3f} rs) != twoway {size_rs}")
    want = 1.0 if opacity is None else opacity
    if not math.isclose(float(ls.text_alpha), want, abs_tol=1e-6):
        out.append(f"{where}: opacity {ls.text_alpha} != twoway {want}")
    return out


#: chain tag -> (scheme, plots) drawing the probe's command in dash.
_CHAIN = {
    "w33a": ("w33a", [plot_for("scatter", _LABELLED)]),
    "w33b": ("w33b", [plot_for("scatter", _LABELLED),
                      plot_for("scatter", _LABELLED, yvar="price")]),
    "w33c": ("w33c", [plot_for("scatter", _LABELLED)]),
    "w33d": ("w33d", [plot_for("scatter", _LABELLED)]),
    "mcolor": ("s2color", [plot_for("scatter", dict(_LABELLED,
                                                    mcolor="red"))]),
    "mlabsize2": ("s2color", [plot_for("scatter", dict(_LABELLED,
                                                       mlabsize="*2"))]),
    "mlabcolor": ("s2color", [plot_for("scatter", dict(_LABELLED,
                                                       mlabcolor="red"))]),
    "trmlabcolor": ("sttrans", [plot_for("scatter", dict(_LABELLED,
                                                         mlabcolor="red"))]),
    "trmcolor": ("sttrans", [plot_for("scatter", dict(_LABELLED,
                                                      mcolor="red"))]),
}


def _type_plots(ptype):
    """``(scatter) (<ptype>, mlabel)``: the second layer labelled."""
    if ptype == "scatteri":
        second = {"type": "scatteri", "values": [[20.0, 3000.0, "lab"]],
                  "options": {}}
    elif ptype == "pcarrowi":
        second = {"type": "pcarrowi",
                  "values": [[20.0, 3000.0, 30.0, 4000.0, "lab"]],
                  "options": {}}
    else:
        second = plot_for(ptype, dict(_LABELLED))
    return [plot_for("scatter"), second]


class TestTheFixture:

    def test_the_s33_probes_are_recorded(self):
        d = _s33()
        s33 = {k: v for k, v in d["probes"].items() if k.startswith("s33_")}
        assert {v["group"] for v in s33.values()} == {
            "mlabel", "mlabel_chain", "mlabel_types", "colorkey"}
        assert [k for k, v in s33.items() if v["rc"] != 0] == []
        assert sorted(d["derived"]["s33"]) == ["chain", "key", "label",
                                               "types"]
        assert len(d["derived"]["s33"]["types"]) == 11
        assert d["_meta"]["source"] == "scripts/extract_scheme_layer_truth.do"


class TestMarkerLabelsAgainstTheFixture:

    @pytest.mark.parametrize("mode", MODES)
    def test_each_probe(self, mode, tmp_path, monkeypatch):
        """Every ``label`` and ``chain`` probe: each layer's labels take
        twoway's colour, opacity and size (the scheme's default under eight
        schemes, the p#label/plabel chain of w33a-w33d, and mcolor(),
        mlabcolor() and mlabsize(*2) acting on that default)."""
        _schemes_in_cwd(tmp_path, monkeypatch)
        s33 = _s33()["derived"]["s33"]
        bad = []
        for scheme, row in sorted(s33["label"].items()):
            lss = _labels(_draw_plots([plot_for("scatter", _LABELLED)],
                                      scheme, mode))
            bad += _label_mismatch(scheme, lss[0], row["fill"],
                                   row["size_rs"], row["opacity"])
        for tag, layers in sorted(s33["chain"].items()):
            scheme, plots = _CHAIN[tag]
            lss = _labels(_draw_plots(plots, scheme, mode))
            if len(lss) != len(layers):
                bad.append(f"{tag}: {len(lss)} label layers, twoway "
                           f"{len(layers)}")
                continue
            for i, (ls, (fill, size_rs, op)) in enumerate(zip(lss, layers)):
                bad += _label_mismatch(f"{tag} layer {i + 1}", ls, fill,
                                       size_rs, op)
        assert bad == []


class TestEveryLabelledTypeTakesItsLayersColour:

    @pytest.mark.parametrize("mode", MODES)
    def test_the_second_layer(self, mode):
        """On each of the 11 labelled types, the second layer's labels are
        twoway's p2 colour: each call of the label applier passes its own
        layer's index."""
        types = _s33()["derived"]["s33"]["types"]
        bad = []
        for ptype, fill in sorted(types.items()):
            lss = _labels(_draw_plots(_type_plots(ptype), "s2color", mode))
            got = sorted({str(ls.text_color).lower() for ls in lss})
            if got != [fill.lower()]:
                bad.append(f"{ptype}: {got} != twoway {fill}")
        assert bad == []


class TestTheColourKeyAgainstTheFixture:

    @pytest.mark.parametrize("mode", MODES)
    def test_each_probe(self, mode, tmp_path, monkeypatch):
        """Every ``key`` probe: the colour bar's labels take the tick-label
        size and colour, its title the axis-title size and colour, upright;
        its ticks the scheme's tick colour on twoway's side; and it has no
        background of its own."""
        _schemes_in_cwd(tmp_path, monkeypatch)
        keys = _s33()["derived"]["s33"]["key"]
        bad = []
        for scheme, row in sorted(keys.items()):
            bar = _colorbar(_draw_plots(
                [plot_for("scatter", {"colorvar": "price"})], scheme, mode))
            for what, colour, size, fill, rs in (
                    ("labels", bar.major_label_text_color,
                     bar.major_label_text_font_size, row["label_fill"],
                     row["label_rs"]),
                    ("title", bar.title_text_color,
                     bar.title_text_font_size, row["title_fill"],
                     row["title_rs"])):
                if str(colour).lower() != fill:
                    bad.append(f"{scheme} {what}: {colour} != twoway {fill}")
                if not _close(_rs(size), rs):
                    bad.append(f"{scheme} {what}: {size} != twoway {rs} rs")
            if bar.title_text_font_style != "normal":
                bad.append(f"{scheme}: title {bar.title_text_font_style}")
            if bar.background_fill_alpha != 0:
                bad.append(f"{scheme}: background alpha "
                           f"{bar.background_fill_alpha}")
            if row["tick_stroke"] is not None:
                if str(bar.major_tick_line_color).lower() != \
                        row["tick_stroke"]:
                    bad.append(f"{scheme} ticks: {bar.major_tick_line_color}"
                               f" != twoway {row['tick_stroke']}")
                side = ("outward" if bar.major_tick_out > 0
                        and bar.major_tick_in == 0 else "inward"
                        if bar.major_tick_in > 0 and bar.major_tick_out == 0
                        else "crossing")
                if side != row["tick_side"]:
                    bad.append(f"{scheme} ticks: {side} != twoway "
                               f"{row['tick_side']}")
        assert bad == []


class TestTheColourKeyTakesTheSchemeChrome:

    def test_the_chrome_dict(self):
        s = dr.SchemeParser("s2color")
        assert s.colorbar_chrome() == {
            "background_fill_alpha": 0.0,
            "major_label_text_font_size": s.tick_label_font_size,
            "major_label_text_color": s.tick_label_color,
            "title_text_font_size": s.axis_title_font_size,
            "title_text_color": s.axis_title_color,
            "title_text_font_style": "normal",
            "major_tick_line_color": s.tick_color,
            "major_tick_line_width": s.tick_line_width,
            "major_tick_in": 0,
            "major_tick_out": int(round(s.tick_length_px)),
        }

    def test_the_tick_pair_is_the_axis_rule(self):
        """outside (s2color), inside (economist) and crossing at an odd
        whole length: the key's tick pair is the one ``apply_to_axis`` sets
        on an axis from the same parser."""
        crossing = _props_scheme(dict(
            dr.SchemeParser("s2color")._props,
            **{"tickposition axis_tick": "crossing",
               "gsize tick": str(7 / T.PX_PER_PT / T.PT_PER_RS)}))
        assert crossing.tick_position == "crossing"
        assert round(crossing.tick_length_px) % 2 == 1
        bad = []
        for s in (dr.SchemeParser("s2color"), dr.SchemeParser("economist"),
                  crossing):
            ax = LinearAxis()
            s.apply_to_axis(ax)
            c = s.colorbar_chrome()
            if (c["major_tick_in"], c["major_tick_out"]) != \
                    (ax.major_tick_in, ax.major_tick_out):
                bad.append((s.tick_position, c["major_tick_in"],
                            c["major_tick_out"], ax.major_tick_in,
                            ax.major_tick_out))
        assert bad == []

    def test_ztitle_star_multiplies_the_schemes_title(self):
        """ztitle(, size(*2)) doubles the scheme's axis-title size (s1manual
        3.901 rs, measured), not a fixed default."""
        s1manual = _s33()["derived"]["s33"]["key"]["s1manual"]
        bar = _colorbar(_draw_plots(
            [plot_for("scatter", {"colorvar": "price"})], "s1manual",
            "standalone", {"ztitle": ", size(*2)"}))
        assert _close(_rs(bar.title_text_font_size),
                      2 * s1manual["title_rs"])


class TestTheOptionsStillWin:

    def test_mlabsize_keyword_wins(self):
        """mlabsize(large) draws large (4.861 rs) whatever the scheme's
        size."""
        (ls,) = _labels(_draw_plots(
            [plot_for("scatter", dict(_LABELLED, mlabsize="large"))],
            "s2color", "standalone"))
        assert _close(_rs(ls.text_font_size), 4.861)


class TestTheParsersLabelStyle:

    def test_props_alone_give_the_attributes(self):
        s = _props_scheme(dict(dr.SchemeParser("s2color")._props,
                               **{"gsize plabel": "large",
                                  "color p2label": "red"}))
        assert s.p_label_sizes[0] == "14pt"
        assert s.p_label_colors[1] == "#ff0000"
        assert s.p_label_colors[0] == s.p_colors[0]

    def test_the_index_wraps_at_fifteen(self):
        s = dr.SchemeParser("s2color")
        assert s.default_mlabel_style(15) == s.default_mlabel_style(0)
        assert s.default_mlabel_style(1) == (s.p_label_colors[1],
                                             s.p_label_alphas[1],
                                             s.p_label_sizes[1])


class TestAfterAFilterMove:

    def test_the_served_label_and_key_keep_their_style(self, tmp_path):
        """A served filter move redraws data, never a label's or the key's
        style: s1rcolor's labels stay #ffff00 at small and the key's labels
        #ffffff."""
        spec = tlv._spec(
            [tlv._graph("g1", [plot_for("scatter", _LABELLED)]),
             tlv._graph("g2", [plot_for("scatter", {"colorvar": "price"})])],
            [tlv._filter("dropdown")], link="")
        spec["build_options"]["scheme"] = "s1rcolor"
        doc = tlv._served_doc(tmp_path, spec)
        tlv._fire(doc, "foreign", "1")
        (ls,) = doc.select({"type": LabelSet})
        # Flipped (WP-42 CV-3): the key was a ColorBar; it is a key cell.
        (cell,) = [p for p in doc.select({"tags": "dash_key_cell"})]
        bar = _key_chrome(cell)
        assert (str(ls.text_color).lower(), ls.text_font_size) == \
            ("#ffff00", "8pt")
        assert str(bar.major_label_text_color).lower() == "#ffffff"

    def test_no_saved_script_writes_label_or_key_style(self):
        """No saved page script writes a LabelSet's or ColorBar's style (nor
        a key cell's axis or title, WP-42 CV-3), so
        the construction defaults hold after a move: no CustomJS of a built
        page and no JavaScript string of the module assigns one."""
        # An assignment to a model property; a KPI card's ``k.text_color``
        # read into its HTML is not one.
        pat = re.compile(r"\.(text_color|text_font_size|text_alpha|"
                         r"major_label_text\w*|title_text\w*|"
                         r"major_tick_line\w*)\s*=(?!=)")
        d = _draw_plots([plot_for("scatter", dict(_LABELLED,
                                                  colorvar="price"))],
                        "s2color", "standalone")
        codes = [m.code for f in d.figures for m in f.select({"type":
                                                              CustomJS})]
        codes += [v for k, v in vars(dr).items()
                  if isinstance(v, str) and k.isupper() and "JS" in k]
        assert [c[:60] for c in codes if pat.search(c)] == []
