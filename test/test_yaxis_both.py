"""yaxis(1 2) and xaxis(1 2): a layer on both axes (WP-31 C10b).

GAPS3 C10: dash refused ``yaxis(1 2)`` (the rule was ``yaxis=int,1,2``)
where twoway draws it.  What twoway does, measured in
test/fixtures/parsed_values_truth.json (scripts/extract_parsed_values_truth.do):
``twoway line mpg weight, yaxis(1 2)`` draws the layer ONCE, in one plot
region whose y scale both axes read (``yaxis_dexes`` "2 1", axis 1 and
axis 2 both 10 to 41), with one legend key.  A layer naming both axes
ties them: ``(line mpg weight, yaxis(1 2)) (line price weight, yaxis(2))``
is one region and one scale, 0 to 15906, for both lines; without the
``1 2`` layer the two axes keep their own scales.

dash reads the value as a list of axis numbers (``_dash_axis_numbers``;
``_dash_axis_tokens`` is the axis-label tokenizer); a figure
with a layer on both axes gets its second axis on the first axis's range
-- the same Range object -- so the two read one scale through every
re-finish, zoom and filter move, in both modes.
"""
import json
import os
import re
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "parsed_values_truth.json")
_SRC = os.path.join(_HERE, "..", "dash_render.py")
MODES = ("saved", "served")


@pytest.fixture(scope="module")
def truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _models(mode, spec):
    if mode == "saved":
        r, _w = tp._standalone(spec)
        return list(r._last_layout_root.references())
    doc, _w = tp._served(spec)
    return [m for root in doc.roots for m in root.references()]


def _figure(models):
    """The one figure that draws data."""
    from bokeh.models import GlyphRenderer, Plot
    figs = [m for m in models if isinstance(m, Plot)
            and any(isinstance(r, GlyphRenderer) for r in m.renderers)]
    assert len(figs) == 1, figs
    return figs[0]


def _lines(fig):
    from bokeh.models import GlyphRenderer, Line
    return [r for r in fig.renderers
            if isinstance(r, GlyphRenderer) and isinstance(r.glyph, Line)]


def _legend_items(fig):
    return [it for lg in fig.legend for it in lg.items]


def _build(mode, plots, go=None, bo=None):
    return _figure(_models(mode, tp._spec(plots, bo, go)))


def _both(**o):
    return plot_for("line", dict({"yaxis": "1 2"}, **o))


class TestTheFixture:
    def test_meta_is_stamped(self, truth):
        assert sorted(truth["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        assert truth["_meta"]["source"] == \
            "scripts/extract_parsed_values_truth.do"

    def test_twoway_draws_the_layer_once_on_one_scale(self, truth):
        b = truth["yaxis"]["both"]
        assert (b["rc"], b["plots"], b["regions"], b["legend_keys"]) == \
            (0, 1, 1, 1)
        assert b["yaxis_dexes"] == ["2 1"]
        assert b["yscale1"] == b["yscale2"]
        t = truth["yaxis"]["tied"]
        assert (t["plots"], t["regions"]) == (2, 1)
        assert t["yscale1"] == t["yscale2"] == [0.0, 15906.0]
        u = truth["yaxis"]["untied"]
        assert u["regions"] == 2 and u["yscale1"] != u["yscale2"]
        assert truth["xaxis"]["both"]["xaxis_dexes"] == ["2 1"]


class TestTokens:
    def test_each_form(self):
        f = dr._dash_axis_numbers
        assert f({"yaxis": "1"}, "yaxis") == ["1"]
        assert f({"yaxis": "2"}, "yaxis") == ["2"]
        assert f({"yaxis": "1 2"}, "yaxis") == ["1", "2"]
        assert f({"yaxis": "2 1"}, "yaxis") == ["1", "2"]
        assert f({"yaxis": "1 1"}, "yaxis") == ["1"]
        assert f({"yaxis": " 2 "}, "yaxis") == ["2"]
        assert f({}, "yaxis") == ["1"]
        assert f(None, "xaxis") == ["1"]
        assert f({"xaxis": ""}, "xaxis") == ["1"]
        assert f({"xaxis": 2}, "xaxis") == ["2"]

    def test_served_copy(self):
        spec = tp._spec([_both()])
        _tag, sp, dp = tp._write(spec)
        with tempfile.TemporaryDirectory() as d:
            ap = os.path.join(d, "app.py")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr.ServerAppBuilder(sp, dp).build(ap)
            with open(ap, encoding="utf-8") as fh:
                src = fh.read()
        assert "def _dash_axis_numbers(" in src
        # Flipped (WP-31 C10c): the tie is _dash_axis_groups', which
        # generalises _dash_axes_tied to axes 1-9.
        assert "def _dash_axis_groups(" in src


@pytest.mark.parametrize("mode", MODES)
class TestBothAxes:
    def test_drawn_once(self, mode):
        # twoway: one plot (fixture yaxis.both.plots).
        fig = _build(mode, [_both()])
        assert len(_lines(fig)) == 1

    def test_one_legend_key(self, mode):
        plain = _build(mode, [plot_for("line"), plot_for("line",
                                                         yvar="price")])
        both = _build(mode, [_both(), plot_for("line", yvar="price")])
        assert len(_legend_items(both)) == len(_legend_items(plain)) == 2

    def test_the_second_axis_exists(self, mode):
        from bokeh.models import LinearAxis
        fig = _build(mode, [_both()])
        right = [a for a in fig.right if isinstance(a, LinearAxis)]
        assert [a.y_range_name for a in right] == ["y2"]
        # One scale: axis 2 reads axis 1's range.
        assert fig.extra_y_ranges["y2"] is fig.y_range

    def test_the_axes_show_the_same_ticks(self, mode):
        fig = _build(mode, [_both()])
        left = [a for a in fig.left if a.y_range_name == "default"][0]
        right = [a for a in fig.right if a.y_range_name == "y2"][0]
        assert list(getattr(right.ticker, "ticks", [])) == \
            list(getattr(left.ticker, "ticks", []))
        assert list(getattr(left.ticker, "ticks", []))

    def test_xaxis_both(self, mode):
        from bokeh.models import LinearAxis
        fig = _build(mode, [plot_for("line", {"xaxis": "1 2"})])
        assert len(_lines(fig)) == 1
        above = [a for a in fig.above if isinstance(a, LinearAxis)]
        assert [a.x_range_name for a in above] == ["x2"]
        assert fig.extra_x_ranges["x2"] is fig.x_range

    def test_tied_layers_share_one_scale(self, mode):
        # (line mpg weight, yaxis(1 2)) (line price weight, yaxis(2)):
        # twoway's one scale spans both (fixture yaxis.tied).
        fig = _build(mode, [_both(), plot_for("line", {"yaxis": "2"},
                                              yvar="price")])
        assert fig.extra_y_ranges["y2"] is fig.y_range
        assert fig.y_range.start <= 14.0 and fig.y_range.end >= 11385.0

    def test_untied_axes_keep_their_scales(self, mode):
        fig = _build(mode, [plot_for("line"),
                            plot_for("line", {"yaxis": "2"}, yvar="price")])
        assert fig.extra_y_ranges["y2"] is not fig.y_range
        assert fig.y_range.end < 100.0

    def test_callers_do_not_reassign(self, mode):
        # After the full build the layer's renderers are on the shared
        # scale, under its own name (TR-06.4, R1-04 as measured).
        fig = _build(mode, [_both(), plot_for("line", {"yaxis": "2"},
                                              yvar="price")])
        names = [r.y_range_name for r in _lines(fig)]
        assert names[0] == "default"
        rng = {"default": fig.y_range, **fig.extra_y_ranges}
        assert all(rng[n] is fig.y_range for n in names)


class TestMoves:
    def _spec(self):
        return tp._spec([_both(), plot_for("line", {"yaxis": "2"},
                                           yvar="price")],
                        {"filter": "foreign, type(dropdown)"})

    def test_saved(self):
        # One object in the saved document: every move the page's script
        # makes to the first axis's range is the second axis's too.
        r, _w = tp._standalone(self._spec())
        fig = _figure(list(r._last_layout_root.references()))
        assert fig.extra_y_ranges["y2"].id == fig.y_range.id

    def test_served(self):
        from bokeh.models import Select
        doc, _w = tp._served(self._spec())
        w = [m for m in tp._widgets_of(doc) if isinstance(m, Select)][0]
        raw = [v for v, lab in w.options if lab == "Foreign"][0]
        tp._fire(w, raw)
        fig = _figure([m for root in doc.roots for m in root.references()])
        assert fig.extra_y_ranges["y2"] is fig.y_range
        # Foreign rows: mpg 17-30, price 4453-11385; one scale over both.
        assert fig.y_range.start <= 17.0 and fig.y_range.end >= 11385.0


class TestEverySiteReadsTokens:
    def test_no_equality_read_remains(self):
        with open(_SRC, encoding="utf-8") as fh:
            src = fh.read()
        bad = re.findall(
            r'get\((?:axis_key|"[xy]axis"), "1"\)[^\n]*?\)\s*\.strip\(\)\s*'
            r'(?:==|!=)\s*(?:"2"|str\(axis_number\))', src)
        bad += re.findall(
            r'get\((?:letter \+ "axis"|phys \+ "axis"), "1"\)\)\.strip\(\)'
            r'\s*==\s*"2"', src)
        assert bad == []
