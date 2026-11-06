"""WP-31 section 24 (GAPS3 D1): minor ticks and minor labels as twoway draws
them.

The defect, measured at the batch-8 base (3b4ff75): ``xmtick()``,
``ymtick()``, ``xmlabel()``, ``ymlabel()``, ``tmtick()`` and ``tmlabel()``
were declared, bounded and written to the graph's options, then named in
dash.ado's pending blocks and never read by the renderer, so
``dash scatter mpg weight, xmtick(##5)`` printed ``dash: ignoring
unsupported option(s): xmtick()`` and drew no minor tick; the axis(2)
copies had no key to reach (``_dash_axfam`` routed neither family).

twoway's truth is ``test/fixtures/minor_tick_truth.json``
(``scripts/extract_minor_tick_truth.do``): for each probe the labelled
(``.minor``, xmlabel) or unlabelled (``.minornl``, xmtick) tickset's rule
(``min``, ``max``, ``delta``, ``between``, ``use_rule``), its listed
``ticks``/``texts``, the label ``format``, the scale it widens (``scale``)
and the ``positions`` tickset_g.class's draw walks (min(delta)max up to
max + .48*delta).  Keys: m_between5, m_between_default, m_between_uneven,
m_between_even_list, m_between_label, m_between_count, m_between_foreign,
m_explicit, m_count, m_minmax, m_widen, m_log, m_labels, m_y_between,
m_axis2, m_date_between, m_refusal.

Measured, and drawn here: ``##N`` steps the major rule's delta / N from the
major minimum extended by whole steps to the scale's minimum, to the major
maximum extended to the scale's maximum; on majors that are an explicit
list (no rule) it leaves one tick at 0 and widens the scale to it
(m_between_uneven, m_between_even_list); on a %td axis tsnatscale's uneven
majors give none (m_date_between); a labelled ``##N`` skips the majors;
``##N`` on xlabel()/xtick() is noted, "##5 ignored, only allowed for minor
ticks", and ignored (m_refusal, rc 0).

While iterating: ``python3 -m pytest test/test_minor_ticks.py -q``.
"""
import json
import math
import os
import re
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_default_axes as tda  # noqa: E402

tb = tda.tb
P = tb._plot
_MODES = ("saved", "served")
_ROOT = os.path.join(_HERE, "..")
_FIXTURE = os.path.join(_HERE, "fixtures", "minor_tick_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)
_SC = [P("scatter", "mpg", "weight")]
_KEYS = ("m_between5", "m_between_default", "m_between_uneven",
         "m_between_even_list", "m_between_label", "m_between_count",
         "m_between_foreign", "m_explicit", "m_count", "m_minmax",
         "m_widen", "m_log", "m_labels", "m_y_between", "m_axis2",
         "m_date_between", "m_refusal")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

#: auto's display formats, so the axes write what twoway writes.
_FORMATS = {"weight": "%8.0gc", "mpg": "%8.0g", "price": "%8.0gc"}


def _figs(mode, go, plots=None, filt=""):
    return tda._figs(mode, tda._spec(plots or _SC, go, filt=filt,
                                     formats=_FORMATS))


def _axis(fig, which, name="default"):
    return tda._axis(fig, which, name)


def _args(fig, which, name="default"):
    from bokeh.models import CustomJSTicker
    t = _axis(fig, which, name).ticker
    return dict(t.args or {}) if isinstance(t, CustomJSTicker) else {}


def _minor(fig, which, name="default"):
    """Every minor position the axis's ticker returns before the range
    filter: xtick()'s extra, the explicit minor ones and the placed
    ``##N`` ones."""
    a = _args(fig, which, name)
    out = list(a.get("extra") or []) + list(a.get("mextra") or [])
    fx = a.get("mfixed")
    if fx is not None:
        out += list(fx.ticks or [])
    return sorted(set(float(v) for v in out))


def _labels(fig, which, axis_no="1"):
    from bokeh.models import Label, LabelSet
    out = []
    for m in list(fig.center) + list(fig.renderers):
        if isinstance(m, (Label, LabelSet)) \
                and m.name == "dash_minor_labels" \
                and list(m.tags or [])[:2] == [which, axis_no]:
            out.append(m)
    return out


def _label_rows(fig, which, axis_no="1"):
    from bokeh.models import LabelSet
    rows = []
    for m in _labels(fig, which, axis_no):
        if isinstance(m, LabelSet):
            d = m.source.data
            rows += list(zip([float(v) for v in d["pos"]], list(d["text"])))
        else:
            v = m.x if which == "x" else m.y
            rows.append((float(v), m.text))
    return sorted(rows)


def _near(a, b, tol=1e-6):
    return len(a) == len(b) and all(abs(x - y) <= tol * max(1.0, abs(y))
                                    for x, y in zip(a, b))


def _scheme(name="s2color"):
    return dr.SchemeParser(name)


# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_meta_is_stamped(self):
        m = _T["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source", "members"):
            assert m.get(k), k

    def test_every_case_was_measured(self):
        assert sorted(k for k in _T if k != "_meta") == sorted(_KEYS)
        assert len(_T["m_between5"]["positions"]) == 26
        assert _T["m_between_uneven"]["positions"] == [0.0]
        assert _T["m_date_between"]["positions"] == []
        assert _T["m_refusal"]["rc"] == 0


class TestTheHelpers:
    def test_rule_of_even_majors(self):
        assert dr._dash_minor_rule([0, 1000, 2000, 3000]) == (0.0, 3000.0,
                                                              1000.0)
        assert dr._dash_minor_rule([1000, 2000, 4000]) is None
        assert dr._dash_minor_rule([5]) is None
        # An added value off the rule leaves it (xlabel(#5 2500)).
        assert dr._dash_minor_rule([0, 1000, 2000, 2500, 3000],
                                   extra=[2500]) == (0.0, 3000.0, 1000.0)

    def test_between_walks_twoways_rule(self):
        for key, rule, n, lab in (
                ("m_between5", (0, 5000, 1000), 5, False),
                ("m_between_default", (2000, 5000, 1000), 5, False),
                ("m_between_label", (2000, 5000, 1000), 4, True),
                ("m_y_between", (10, 40, 10), 2, True),
                ("m_between_foreign", (1500, 3500, 500), 5, False)):
            t = _T[key]
            lo, hi = t["scale"]
            got = dr._dash_minor_between(rule, n, lo, hi, labelled=lab)
            want = t["positions"]
            if lab:
                want = [v for v in want
                        if all(abs(v - m) > (hi - lo) / 10000.0 for m in
                               [rule[0] + i * rule[2] for i in range(
                                   int(round((rule[1] - rule[0])
                                             / rule[2])) + 1)])]
            assert _near(got, want), (key, got, want)

    def test_no_rule_draws_nothing(self):
        assert dr._dash_minor_between(None, 5, 0, 10) == []

    def test_the_ticker_code_under_node(self):
        code = ("const cb_data = {start: 0, end: 10}; "
                "const mfixed = {ticks: [2, 4, 12]}; "
                "const mextra = [5]; const extra = [7]; "
                "const f = function () {" + dr._DASH_MTICK_JS + "}; "
                "process.stdout.write(JSON.stringify(f().sort((a, b) => a - b)));")
        out = js_runner.run_js(code)
        assert (json.loads(out) if isinstance(out, str) else out) == [
            2, 4, 5, 7]

    def test_the_rule_regex(self):
        assert dr._DASH_MINOR_RULE_RE.match("##5").group(1) == "5"
        assert dr._DASH_MINOR_RULE_RE.match("#5") is None


class TestMinorTicksAreDrawn:
    @pytest.mark.parametrize("mode", _MODES)
    def test_explicit_positions(self, mode):
        f = _figs(mode, {"xmtick": "1500 2500"})[0]
        a = _args(f, "x")
        assert a.get("mextra") == [1500.0, 2500.0]
        assert "extra" not in a
        # twoway widens the scale to an explicit minor tick (m_explicit).
        assert tda._inner(f, "x")[0] == pytest.approx(
            _T["m_explicit"]["scale"][0])

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("form,want", [
        ("1500(500)2500", [1500.0, 2000.0, 2500.0]),
        ("minmax", _T["m_minmax"]["positions"]),
        ("#3", _T["m_count"]["positions"])])
    def test_rule_forms(self, mode, form, want):
        f = _figs(mode, {"xmtick": form})[0]
        assert _near(_minor(f, "x"), want), (_minor(f, "x"), want)

    @pytest.mark.parametrize("mode", _MODES)
    def test_widens_the_scale(self, mode):
        f = _figs(mode, {"xmtick": "6000"})[0]
        assert tda._inner(f, "x")[1] == pytest.approx(
            _T["m_widen"]["scale"][1])


class TestBetweenRule:
    @pytest.mark.parametrize("mode", _MODES)
    def test_between_matches_twoway(self, mode):
        bad = []
        for key, go in (
                ("m_between5", {"xlabel": "0(1000)5000", "xmtick": "##5"}),
                ("m_between_default", {"xmtick": "##5"}),
                ("m_between_count", {"xlabel": "#3", "xmtick": "##2"}),
                ("m_log", {"xscale": "log", "xmtick": "##5"})):
            f = _figs(mode, go)[0]
            assert _args(f, "x").get("between") == int(
                _T[key]["between"]), key
            got = _minor(f, "x")
            if not _near(got, _T[key]["positions"]):
                bad.append((key, got, _T[key]["positions"]))
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    def test_uneven_majors_draw_nothing(self, mode):
        # twoway's lone tick at 0 for majors that are an uneven list, and
        # the scale widened to it.
        key = "m_between_uneven"
        f = _figs(mode, {"xlabel": "1000 2000 4000", "xmtick": "##5"})[0]
        assert _minor(f, "x") == _T[key]["positions"]
        assert tda._inner(f, "x")[0] == pytest.approx(_T[key]["scale"][0])

    @pytest.mark.parametrize("mode", _MODES)
    def test_an_even_list_is_read_as_its_rule(self, mode):
        # Flipped (WP-31 D1c): an evenly spaced list typed as one is no
        # rule (twoway: m_between_even_list, a lone tick at 0); dash.ado
        # keeps a lone a(b)c as typed, which stays a rule.
        f = _figs(mode, {"xlabel": "1000 2000 3000", "xmtick": "##5"})[0]
        assert _minor(f, "x") == _T["m_between_even_list"]["positions"]

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_date_axis_with_uneven_majors_draws_none(self, mode, tmp_path):
        import test_date_range as tdr
        spec = tdr._spec([P("scatter", "close", "date")],
                         graph_options={"xmtick": "##2"})
        df = tdr._frame([14977.0 + 30 * i for i in range(40)])
        if mode == "saved":
            f = list(tdr._saved(tmp_path, spec, df)[0].figures.values())[0]
        else:
            f = tb._figs_of(tdr._served(tmp_path, spec, df)[0].roots)[0]
        assert _minor(f, "x") == []


class TestMinorLength:
    @pytest.mark.parametrize("mode", _MODES)
    def test_half_tiny_alone(self, mode):
        f = _figs(mode, {"xmtick": "1500"})[0]
        ax = _axis(f, "x")
        s = _scheme()
        # gsize minortick half_tiny: half of the tick's tiny.
        assert s.minortick_length_px == pytest.approx(
            s.tick_length_px / 2.0, rel=1e-3)
        assert ax.minor_tick_out == int(round(s.minortick_length_px)) == 3
        assert ax.minor_tick_in == 0
        assert ax.minor_tick_line_width == pytest.approx(
            s.minortick_line_width)

    @pytest.mark.parametrize("mode", _MODES)
    def test_shared_slot_takes_the_major_length(self, mode):
        f = _figs(mode, {"xmtick": "1500", "xtick": "2500"})[0]
        ax = _axis(f, "x")
        assert ax.minor_tick_out == ax.major_tick_out == 5
        assert _minor(f, "x") == [1500.0, 2500.0]


class TestMinorLabels:
    @pytest.mark.parametrize("mode", _MODES)
    def test_texts_and_units(self, mode):
        from bokeh.models import LabelSet
        f = _figs(mode, {"xmlabel": '1500 "a" 2500'})[0]
        ms = _labels(f, "x")
        assert len(ms) == 1 and isinstance(ms[0], LabelSet)
        m = ms[0]
        t = _T["m_labels"]
        assert t["texts"] == ["a", ""] and t["format"] == "%8.0gc"
        assert _label_rows(f, "x") == [(1500.0, "a"), (2500.0, "2,500")]
        assert m.y_units == "screen" and m.x_units == "data"
        assert m.text_font_size == _scheme().minortick_label_font_size
        assert m.text_color == _scheme().tick_label_color
        assert m.text_baseline == "top" and m.text_align == "center"
        # The labelled positions are minor ticks too.
        assert _minor(f, "x") == [1500.0, 2500.0]

    @pytest.mark.parametrize("mode", _MODES)
    def test_date_axis_text(self, mode, tmp_path):
        import test_date_range as tdr
        spec = tdr._spec([P("scatter", "close", "date")],
                         graph_options={"xmlabel": "14978"})
        df = tdr._frame([14977.0 + i for i in range(5)])
        if mode == "saved":
            f = list(tdr._saved(tmp_path, spec, df)[0].figures.values())[0]
        else:
            f = tb._figs_of(tdr._served(tmp_path, spec, df)[0].roots)[0]
        rows = _label_rows(f, "x")
        assert [r[1] for r in rows] == [dr._dash_fmt_text(14978.0, "%td")]

    @pytest.mark.parametrize("mode", _MODES)
    def test_y_axis_geometry(self, mode):
        f = _figs(mode, {"ymlabel": "##2", "ylabel": "10(10)40"})[0]
        m = _labels(f, "y")[0]
        assert m.x_units == "screen" and m.y_units == "data"
        # The minor labels take the scheme's vertical_tick angle, as the
        # major ones do (ticksetstyle-minor_vert_default.style).
        assert _scheme().tick_angle_y == 90.0
        assert m.angle == pytest.approx(math.pi / 2)
        assert m.text_align == "center" and m.text_baseline == "bottom"
        t = _T["m_y_between"]
        want = [v for v in t["positions"] if v not in (10.0, 20.0, 30.0,
                                                       40.0)]
        assert [r[0] for r in _label_rows(f, "y")] == want
        fmt = _axis(f, "y").formatter.args["fmt"]
        assert [r[1] for r in _label_rows(f, "y")] == [
            dr._dash_fmt_text(v, fmt) for v in want]


class TestAxisTwo:
    def test_routed_to_the_second_axis(self):
        src = open(os.path.join(_ROOT, "dash_parse.mata"),
                   encoding="utf-8").read()
        assert re.search(r'"mlabel", "mlabels", "mlabel", "3", "3", '
                         r'"mlabel2"', src)
        assert re.search(r'"mtick",\s+"mticks",\s+"mtick",\s+"3", "5", '
                         r'"mtick2"', src)
        ado = open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8").read()
        for k in ("xmlabel2", "ymlabel2", "xmtick2", "ymtick2"):
            assert f"{k}=axislist" in ado, k

    @pytest.mark.parametrize("mode", _MODES)
    def test_labels_use_frame_nodes(self, mode):
        from bokeh.models import Label, Node
        f = _figs(mode, {"ymlabel2": "5000 10000"}, plots=tb.DUAL_Y)[0]
        ms = _labels(f, "y", "2")
        assert len(ms) == 2 and all(isinstance(m, Label) for m in ms)
        for m in ms:
            assert isinstance(m.x, Node) and m.x.symbol == "right"
            assert m.y_units == "data" and m.y_range_name == "y2"
        assert sorted(m.y for m in ms) == _T["m_axis2"]["ticks"]
        assert _minor(f, "y", "y2") == _T["m_axis2"]["ticks"]
        assert _minor(f, "y") == []

    @pytest.mark.parametrize("mode", _MODES)
    def test_ticks_on_the_second_axis(self, mode):
        f = _figs(mode, {"ymtick2": "5000 10000"}, plots=tb.DUAL_Y)[0]
        assert _minor(f, "y", "y2") == _T["m_axis2"]["ticks"]


class TestNoMinorByDefault:
    @pytest.mark.parametrize("mode", _MODES)
    def test_none_drawn(self, mode):
        f = _figs(mode, {})[0]
        for which in ("x", "y"):
            assert _minor(f, which) == []
            assert not _labels(f, which)

    def test_every_scheme_says_zero(self):
        names = sorted(n[len("dash-"):-len(".scheme")]
                       for n in os.listdir(_ROOT)
                       if n.startswith("dash-") and n.endswith(".scheme"))
        assert len(names) == 26
        for n in names:
            s = dr.SchemeParser(n)
            assert s.numticks_minor == {"x": 0, "y": 0}, n


class TestXtickIsUnchanged:
    @pytest.mark.parametrize("mode", _MODES)
    def test_args_and_length(self, mode):
        f = _figs(mode, {"ytick": "15 25"})[0]
        a = _args(f, "y")
        assert set(a) == {"base", "extra"}
        ax = _axis(f, "y")
        assert ax.minor_tick_out == ax.major_tick_out == 5
        assert ax.minor_tick_line_color == ax.major_tick_line_color


class TestAfterAMove:
    def _moved(self, mode, go):
        spec = tda._spec(_SC, go, filt=tda._DROP[0])
        figs = tda._after(mode, spec, tda._DROP[1], tda._DROP[2])
        return figs[0]

    @pytest.mark.parametrize("mode", _MODES)
    def test_explicit_hold(self, mode):
        f = self._moved(mode, {"xmtick": "1500 2500",
                               "xmlabel": '2000 "two"'})
        assert _minor(f, "x") == [1500.0, 2000.0, 2500.0]
        assert _label_rows(f, "x") == [(2000.0, "two")]

    @pytest.mark.parametrize("mode", _MODES)
    def test_between_follows_the_majors(self, mode):
        f = self._moved(mode, {"xmtick": "##5"})
        t = _T["m_between_foreign"]
        assert _near(_minor(f, "x"), t["positions"]), _minor(f, "x")

    @pytest.mark.parametrize("mode", _MODES)
    def test_labels_follow_the_majors(self, mode):
        f = self._moved(mode, {"xmlabel": "##5"})
        t = _T["m_between_foreign"]
        want = [v for v in t["positions"] if v % 500.0]
        assert _near([r[0] for r in _label_rows(f, "x")], want)


class TestZoom:
    @pytest.mark.parametrize("mode", _MODES)
    def test_between_follows_a_zoom(self, mode):
        spec = tda._spec(_SC, {"ymtick": "##2"})
        f = (tda._saved(spec).figures["g1"] if mode == "saved"
             else tb._figs_of(tda._served(spec).roots)[0])
        rng = f.y_range
        rng.start, rng.end = 20.0, 30.0
        cb = tda._zoom_cb(rng)
        js_runner.JsSession([cb]).run(cb, cb_obj=rng)
        majors = dr._dash_natscale_ticks(20.0, 30.0, 5)
        step = (majors[1] - majors[0]) / 2.0
        got = _minor(f, "y")
        assert got and all(abs((v - majors[0]) / step
                               - round((v - majors[0]) / step)) < 1e-9
                           for v in got), got


class TestMinorGrid:
    @pytest.mark.parametrize("mode", _MODES)
    def test_grid_word(self, mode):
        f = _figs(mode, {"xmtick": "1500 2500, grid"})[0]
        s = _scheme()
        # Flipped (WP-44 AX-6): the minor style was wrong because twoway's
        # gridstyle minor is major (tick_style_truth.json ax6_xmtick_*).
        assert any(g.minor_grid_line_color == s.grid_color
                   and list(g.minor_grid_line_dash)
                   == list(s.major_grid_dash or [])
                   for g in f.xgrid)
        f0 = _figs(mode, {"xmtick": "1500 2500"})[0]
        assert all(g.minor_grid_line_color is None for g in f0.xgrid)


class TestSilentWhenHonoured:
    @pytest.mark.parametrize("option", ["xmlabel", "xmtick", "tmlabel",
                                        "tmtick", "ymlabel", "ymtick"])
    def test_no_note(self, option):
        ado = open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8").read()
        assert f"_dash_pending' {option}\"" not in ado

    def test_no_renderer_note(self):
        spec = tda._spec(_SC, {"xmtick": "##5", "xmlabel": "1500 2500",
                               "ymtick": "15 25", "ymlabel": "##2"})
        tag, sp, dp = tda._write(spec)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            rr = dr.DashRenderer(sp, dp)
            tda.render_models(rr)
        assert not [str(w.message) for w in caught
                    if "mtick" in str(w.message) or "mlabel" in str(w.message)]


class TestMajorBetweenIsIgnored:
    def test_noted_and_default(self):
        spec = tda._spec(_SC, {"xlabel": "##5"})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            tag, sp, dp = tda._write(spec)
            rr = dr.DashRenderer(sp, dp)
            tda.render_models(rr)
        msgs = [str(w.message) for w in caught]
        assert any(_T["m_refusal"]["note"] in m for m in msgs), msgs
        f = rr.figures["g1"]
        # Flipped (WP-31 D6): a lone ##5 draws what xlabel(none) draws,
        # no labels or ticks (test/fixtures/axis_look_truth.json
        # dh_xlabel), not the default ticks.
        assert list(tda._ticks(f, "x")) == []


class TestLabelTextIsACanvasSink:
    def test_raw_in_column_only(self, tmp_path):
        hostile = "<img src=x onerror=alert(1)>"
        spec = tda._spec(_SC, {"xmlabel": '2000 "%s"' % hostile})
        tag, sp, dp = tda._write(spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rr = dr.DashRenderer(sp, dp, str(tmp_path / "o.html"))
            page = rr.render()
        f = rr.figures["g1"]
        assert _label_rows(f, "x") == [(2000.0, hostile)]
        # Outside the escaped Bokeh JSON the text appears nowhere.
        assert hostile not in page
