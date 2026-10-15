"""
test_edge_titles.py -- t1title() .. r2title(), the edge titles (WP-31 D2,
section 27).

The defect: dash declared the eight edge titles, stored them in
graph_options and named them as unsupported; the renderer drew none of
them.  It also declared title2() and subtitle2(), which twoway has not, and
named those as unsupported too: twoway refuses them, "option title2() not
allowed", r(198) (and "option subtitle2() not allowed").

twoway's rule (graph_g.class parse_and_log_titles, _fr_title_parse_and_log
.ado; measured in test/fixtures/edge_title_truth.json by
scripts/extract_edge_title_truth.do, s2color):

* t titles are drawn above the plot region, b below, l to the left and r
  to the right, the l and r titles turned on their side (SVG rotate(-90));
* a "1" title is ring 1 and a "2" title ring 2, both inside the legend
  (ring 3), the note, the caption, the subtitle and the title, and outside
  every axis on that side (three y axes, two on the left: the l titles are
  outside axis 3's title);
* the "1" titles are the scheme's subheading box (medium), the "2" titles
  its body box (medsmall) -- except b2title(), which twoway's parser
  builds with `textboxstyle b1title' (graph_g.class:294), so it is
  subheading too (measured: B2 110.01 SVG units, T2 99.99);
* size(), color(), prefix and suffix as on title(); a repeat is the last
  copy's text unless suffix or prefix joins them;
* on a by() graph each panel carries the edge titles (two T1, B1, L1 and R1
  texts for by(foreign)).

The fix draws each as a side-panel ``Title`` tagged ``["dash_edge_title",
<key>]``, inserted after the panel's axes, ring 1 nearest the frame, in
both modes (``_dash_edge_titles``); ``_dash_move_legend`` puts the legend
after them.
"""
import json
import os
import re
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from bokeh.models import Axis, Legend, Title  # noqa: E402

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "edge_title_truth.json")
_ROOT = os.path.join(_HERE, "..")
_KEYS = ("t1title", "t2title", "b1title", "b2title",
         "l1title", "l2title", "r1title", "r2title")
_SIDE = {"t": "above", "b": "below", "l": "left", "r": "right"}

with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)


def _lab(k):
    return k[:2].upper()


def _figs(mode, go, plots=None, scheme="s2color"):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        figs, _c = tp._figures_in(mode, tp._spec(
            plots or [tp._sc()], {"scheme": scheme}, go))
    return figs, [str(w.message) for w in caught] + list(_c or [])


def _fig(mode, go, plots=None, scheme="s2color"):
    figs, caught = _figs(mode, go, plots, scheme)
    assert len(figs) == 1, len(figs)
    return figs[0], caught


def _edges(fig, key=None):
    """[(side, index, Title)] of the edge titles of *fig* (of *key*)."""
    out = []
    for side in ("above", "below", "left", "right"):
        for i, m in enumerate(getattr(fig, side)):
            tags = list(getattr(m, "tags", None) or [])
            if isinstance(m, Title) and "dash_edge_title" in tags \
                    and (key is None or key in tags):
                out.append((side, i, m))
    return out


def _index(fig, side, pred):
    return [i for i, m in enumerate(getattr(fig, side)) if pred(m)]


def _svg(case, text):
    return [t for t in TRUTH[case]["texts"] if t["text"] == text]


# ============================================================
# The fixture
# ============================================================
class TestTheFixture:

    def test_meta_is_stamped(self):
        m = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source", "members"):
            assert m.get(k), k
        assert m["source"] == "scripts/extract_edge_title_truth.do"

    def test_every_case_was_measured(self):
        for k in ("all", "one", "yaxis2", "yaxis3", "legend12", "subopts",
                  "by_tb", "merged_title", "spellings", "refuse_title2",
                  "refuse_subtitle2", "refuse_title2_segment"):
            assert k in TRUTH, k
        assert TRUTH["refuse_title2"] == {
            "rc": 198, "msg": "option title2() not allowed"}
        assert TRUTH["refuse_subtitle2"] == {
            "rc": 198, "msg": "option subtitle2() not allowed"}

    def test_twoways_rings_as_measured(self):
        """The SVG order the drawing tests encode: T1 nearer the plot than
        T2, both inside the subtitle and the title; B1, B2, the legend, the
        note and the caption outward below; L2 left of L1, R2 right of R1;
        l and r turned -90 degrees."""
        y = {t["text"]: t["y"] for t in TRUTH["all"]["texts"]}
        x = {t["text"]: t["x"] for t in TRUTH["all"]["texts"]}
        assert y["T"] < y["S"] < y["T2"] < y["T1"]
        assert y["B1"] < y["B2"] < y["Mileage (mpg)"] < y["N"] < y["C"]
        assert x["L2"] < x["L1"] and x["R1"] < x["R2"]
        for t in TRUTH["all"]["texts"]:
            if t["text"] in ("L1", "L2", "R1", "R2"):
                assert t["rotate"] == -90.0, t
            if t["text"] in ("T1", "T2", "B1", "B2"):
                assert t["rotate"] == 0.0, t

    def test_b2title_is_subheading_in_twoway(self):
        one = TRUTH["one"]
        assert one["b2title"]["size"] == one["b1title"]["size"] == "medium"
        assert one["t2title"]["size"] == "medsmall"


# ============================================================
# Drawn, where twoway draws them
# ============================================================
@pytest.mark.parametrize("mode", MODES)
class TestEdgeTitlesAreDrawn:

    @pytest.mark.parametrize("k", _KEYS)
    def test_each_side_and_ring(self, mode, k):
        f, _c = _fig(mode, {k: '"%s"' % _lab(k)})
        got = _edges(f, k)
        assert len(got) == 1, got
        side, _i, t = got[0]
        assert side == _SIDE[k[0]]
        assert t.text == _lab(k)
        assert t.text_font_style == "normal"

    def test_all_eight_at_once(self, mode):
        f, _c = _fig(mode, {k: '"%s"' % _lab(k) for k in _KEYS})
        assert sorted(t.text for _s, _i, t in _edges(f)) == \
            sorted(_lab(k) for k in _KEYS)


@pytest.mark.parametrize("mode", MODES)
class TestRingOrder:

    @pytest.mark.parametrize("letter", ["t", "b", "l", "r"])
    def test_one_inside_two(self, mode, letter):
        f, _c = _fig(mode, {letter + "1title": '"ONE"',
                            letter + "2title": '"TWO"'})
        side = _SIDE[letter]
        (s1, i1, _a), = _edges(f, letter + "1title")
        (s2, i2, _b), = _edges(f, letter + "2title")
        assert s1 == s2 == side
        assert i1 < i2
        axes = _index(f, side, lambda m: isinstance(m, Axis))
        assert all(a < i1 for a in axes), (axes, i1)

    def test_legend_and_note_stay_outside(self, mode):
        f, _c = _fig(mode, {"b1title": '"B1"', "b2title": '"B2"',
                            "note": '"N"', "caption": '"C"'},
                     [tp._sc(), tp._sc(yvar="price")])
        kinds = []
        for m in f.below:
            if isinstance(m, Axis):
                kinds.append("axis")
            elif isinstance(m, Legend):
                kinds.append("legend")
            elif isinstance(m, Title):
                kinds.append(m.text)
        kinds = [k for i, k in enumerate(kinds)
                 if k != "axis" or i == 0 or kinds[i - 1] != "axis"]
        assert kinds == ["axis", "B1", "B2", "legend", "N", "C"], kinds

    def test_a_legend_at_twelve_is_outside_t1_t2(self, mode):
        f, _c = _fig(mode, {"t1title": '"T1"', "t2title": '"T2"',
                            "legend": "position(12)"},
                     [tp._sc(), tp._sc(yvar="price")])
        legs = _index(f, "above", lambda m: isinstance(m, Legend))
        (_s1, i1, _a), = _edges(f, "t1title")
        (_s2, i2, _b), = _edges(f, "t2title")
        assert legs and i1 < i2 < legs[0], (i1, i2, legs)

    @pytest.mark.parametrize("n", [2, 3])
    def test_outside_every_axis_on_the_side(self, mode, n):
        """yaxis(2): axis 2 on the right, R1 outside it (yaxis2); yaxis(3)
        too: axes 1 to 3 all on the left, L1 outside axis 3's title
        (yaxis3)."""
        plots = [tp._sc(), tp.plot_for("scatter", yvar="price", xvar="weight",
                                       options={"yaxis": "2"})]
        if n == 3:
            plots.append(tp.plot_for("scatter", yvar="rep", xvar="weight",
                                     options={"yaxis": "3"}))
        f, _c = _fig(mode, {"l1title": '"L1"', "r1title": '"R1"'}, plots)
        sides = (("l1title", "left"),) if n == 3 else \
            (("l1title", "left"), ("r1title", "right"))
        for k, side in sides:
            (_s, i, _t), = _edges(f, k)
            axes = _index(f, side, lambda m: isinstance(m, Axis))
            assert len(axes) >= (n if side == "left" and n == 3 else 1)
            assert all(a < i for a in axes), (k, axes, i)
        x = {t["text"]: t["x"] for t in TRUTH["yaxis%d" % n]["texts"]}
        assert x["L1"] < min(v for t, v in x.items()
                             if t not in ("L1", "R1", "L2", "R2"))


@pytest.mark.parametrize("mode", MODES)
class TestStyles:

    def _style(self, name):
        return dr.SchemeParser("s2color").textbox_style(name)

    def test_ring_one_is_subheading(self, mode):
        size, colour = self._style("subheading")
        for k in ("t1title", "b1title", "l1title", "r1title"):
            f, _c = _fig(mode, {k: '"X"'})
            (_s, _i, t), = _edges(f, k)
            assert (t.text_font_size, t.text_color) == (size, colour), k

    def test_ring_two_is_body(self, mode):
        size, colour = self._style("body")
        for k in ("t2title", "l2title", "r2title"):
            f, _c = _fig(mode, {k: '"X"'})
            (_s, _i, t), = _edges(f, k)
            assert (t.text_font_size, t.text_color) == (size, colour), k

    def test_b2title_is_b1titles_box_as_in_twoway(self, mode):
        size, colour = self._style("subheading")
        f, _c = _fig(mode, {"b2title": '"X"'})
        (_s, _i, t), = _edges(f, "b2title")
        assert (t.text_font_size, t.text_color) == (size, colour)

    def test_size_color_prefix_suffix(self, mode):
        size, _colour = self._style("subheading")
        f, caught = _fig(mode, {"t1title": '"X", size(large) color(red)',
                                "b1title": '"A" "B"',
                                "l1title": '"L", suffix'})
        (_s, _i, t), = _edges(f, "t1title")
        assert t.text_font_size != size
        assert str(t.text_color).lower() in ("red", "#ff0000")
        (_s, _i, b), = _edges(f, "b1title")
        assert b.text == "A\nB"
        (_s, _i, lt), = _edges(f, "l1title")
        assert lt.text == "L"
        assert not [w for w in caught if "title()" in w], caught


@pytest.mark.parametrize("mode", MODES)
class TestNamedSubOptions:

    @pytest.mark.parametrize("sub", ["position(3)", "ring(2)", "span",
                                     "orientation(horizontal)"])
    def test_named_once(self, mode, sub):
        f, caught = _fig(mode, {"t1title": '"X", %s' % sub})
        named = [w for w in caught if "t1title()" in w and sub in w]
        assert len(named) == 1, caught
        assert len(_edges(f, "t1title")) == 1


class TestSilentWhenHonoured:
    """dash.ado names a pending option; a drawn one is not pending."""

    @pytest.mark.parametrize("k", _KEYS + ("title2", "subtitle2"))
    def test_no_note(self, k):
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            src = fh.read()
        assert ("`_dash_pending' %s\"'" % k) not in src, k


class TestSchemes:

    def test_every_scheme_names_the_styles(self):
        names = sorted(f[5:-7] for f in os.listdir(_ROOT)
                       if f.startswith("dash-") and f.endswith(".scheme"))
        assert len(names) == 26, names
        for n in names:
            with open(os.path.join(_ROOT, "dash-%s.scheme" % n),
                      encoding="utf-8") as fh:
                src = fh.read()
            for k in _KEYS:
                assert re.search(r"(?m)^textboxstyle\s+%s\s+\S+" % k, src), \
                    (n, k)
            sp = dr.SchemeParser(n)
            assert set(sp.edge_title_styles) == set(_KEYS), n

    def test_s2colors_styles(self):
        sp = dr.SchemeParser("s2color")
        assert sp.edge_title_styles == {
            "t1title": "subheading", "t2title": "body",
            "b1title": "subheading", "b2title": "subheading",
            "l1title": "subheading", "l2title": "body",
            "r1title": "subheading", "r2title": "body"}


@pytest.mark.parametrize("mode", MODES)
class TestOnAByGraph:

    def test_on_every_panel(self, mode):
        """twoway draws the edge titles on each by() panel (by_tb: two of
        each of T1, B1, L1 and R1 for by(foreign))."""
        texts = [t["text"] for t in TRUTH["by_tb"]["texts"]]
        for lab in ("T1", "B1", "L1", "R1"):
            assert texts.count(lab) == 2, lab
        figs, _c = _figs(mode, {"by": "foreign", "t1title": '"T1"',
                                "b1title": '"B1"', "l1title": '"L1"',
                                "r1title": '"R1"'})
        panels = [f for f in figs if _edges(f)]
        assert len(panels) == 2, len(figs)
        for f in panels:
            assert sorted(t.text for _s, _i, t in _edges(f)) == \
                ["B1", "L1", "R1", "T1"]


@pytest.mark.parametrize("mode", MODES)
class TestTextIsACanvasSink:

    def test_raw_title_text(self, mode):
        f, _c = _fig(mode, {"t1title": '"</title><script>x</script>"'})
        (_s, _i, t), = _edges(f, "t1title")
        assert t.text == "</title><script>x</script>"


class TestTitleCopies:
    """title("A") title("B") is one line, B, in twoway (merged_title); the
    edge titles' repeats follow the same rule (spellings b_b)."""

    def test_the_last_copy_is_drawn(self):
        assert TRUTH["merged_title"] == {"n": 1, "text": "B"}
        assert TRUTH["spellings"]["b_b"]["bound"] == {"b1title": "B"}
        assert TRUTH["subopts"]["b1title_lines"] == 2
