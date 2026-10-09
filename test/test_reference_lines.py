"""xline() and yline() as twoway draws them (WP-30 P1.21a, section 39).

The defect (DROPIN-REMAINING.md P1.21; research p1-21 section 1): a numlist
position -- ``xline(2000(500)3000)``, ``2000/2002``, ``2000 2500 to 3500``
-- drew nothing and was named as an unimplemented sub-option; a copy
starting with such a run took the style of the copy after it;
``xline(3000 3000)`` drew two lines; ``lstyle()`` was named and dropped;
``nan``, ``inf`` and ``1_000`` drew at NaN, infinity and 1000; lines were
drawn over the markers, one ``add_layout`` at a time; and nothing bounded
how many a spec could ask for.

twoway's truth: test/fixtures/refline_truth.json, written by
scripts/extract_refline_truth.do (StataNow 19.5, sysuse auto).  The
renderer's reading here is the fallback for a spec written by hand;
dash.ado expands positions with Stata's own numlist
(test/test_suboption_reporting.cscript XP-01..XP-08).

While iterating run only this file (CLAUDE.md rule 10):
``python3 -m pytest test/test_reference_lines.py -q``.
"""
import json
import os
import re
import sys
import time
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.models import Plot, Span  # noqa: E402
from bokeh.plotting import figure as bokeh_figure  # noqa: E402
from test_mode_parity import (_sc, _served, _served_after_move,  # noqa: E402
                              _spec, _standalone)
from test_saved_filter_layers import _move, _render  # noqa: E402

_FIX = json.load(open(os.path.join(_ROOT, "test", "fixtures",
                                   "refline_truth.json"), encoding="utf-8"))
_P = _FIX["probes"]
MODES = ("saved", "served")


def _go(opt):
    """A twoway option string's xline()/yline() copies as dash.ado joins
    them: ``{"xline": "a, lc(red), b"}``."""
    go = {}
    for m in re.finditer(r"\b([xy]line)\(", opt):
        i, depth = m.end(), 1
        while depth:
            depth += {"(": 1, ")": -1}.get(opt[i], 0)
            i += 1
        name, body = m.group(1), opt[m.end():i - 1]
        go[name] = f"{go[name]}, {body}" if name in go else body
    return go


def _draw(go, mode, scheme="s2color"):
    """``(spans, warnings)`` of one scatter with graph options *go*."""
    spec = _spec([_sc()], {"scheme": scheme}, go)
    if mode == "saved":
        r, w = _standalone(spec)
        root = r._last_layout_root
    else:
        root, w = _served(spec)
    spans = list(root.select({"type": Span}))
    return spans, w


def _hex(c):
    return (c or "").lower() if c else None


class TestTheFixture:
    def test_it_is_stamped(self):
        meta = _FIX["_meta"]
        assert set(meta) == {"stata_version", "born_date", "dash_commit",
                             "extracted"}
        assert meta["stata_version"].startswith("19.")
        want = ({f"P{i:02d}" for i in range(1, 16)}
                | {f"R{i:02d}" for i in range(1, 39)}
                | {f"S{i:02d}_{s}" for i in range(1, 17)
                   for s in ("s2color", "stcolor", "s1mono")}
                | {"L00", "L01", "L02", "L03", "L04", "O01", "B01"})
        assert want <= set(_P)


class TestPositions:
    @pytest.mark.parametrize("mode", MODES)
    def test_probe(self, mode):
        """P01-P14: every position and colour twoway draws, as a multiset
        per axis (P15 is the 5,000-line count; the limit tests bound it)."""
        bad = []
        for pid in [f"P{i:02d}" for i in range(1, 15)]:
            rec = _P[pid]
            spans, _ = _draw(_go(rec["opt"]), mode)
            got = sorted(("x" if s.dimension == "height" else "y",
                          round(s.location), _hex(s.line_color))
                         for s in spans)
            want = sorted((ln["axis"], round(ln["pos"]), ln["stroke"])
                          for ln in rec["lines"])
            if got != want:
                bad.append(f"{pid} {rec['opt']}: dash {got}, twoway {want}")
        assert not bad, "\n".join(bad)

    def test_a_copy_starts_at_any_position_run(self):
        assert dr._dash_refline_copies(
            "20, lcolor(red), 10(5)40, lcolor(blue)") == [
                ("20", ["lcolor(red)"]), ("10(5)40", ["lcolor(blue)"])]
        assert len(dr._dash_refline_copies(
            "3000, lcolor(red) noextend, 4000")) == 2
        assert len(dr._dash_refline_copies("(500)3000")) == 1

    def test_the_fallback_reads_as_numlist(self):
        for text, values, bad in (
                ("nan 3000", [3000.0], ["nan"]), ("inf", [], ["inf"]),
                ("1e400", [], ["1e400"]), ("1_000", [], ["1_000"]),
                ("1(1)2501", [], ["1(1)2501"]), ("abc", [], ["abc"]),
                ("3000 3000.0 3e3", [3000.0], [])):
            b = []
            assert dr._dash_refline_positions(text, b) == values, text
            assert b == bad, text
        t0 = time.perf_counter()
        b = []
        dr._dash_refline_positions(" ".join(["1"] * 10_000), b)
        assert time.perf_counter() - t0 < 0.5

    def test_routing_uses_the_same_copies(self):
        assert dr._dash_route_line_copies("20, 10(5)40, axis(2)") == (
            "20", "10(5)40", True)


class TestLstyle:
    @pytest.mark.parametrize("mode", MODES)
    def test_probe(self, mode):
        """S01-S16 under s2color, stcolor and s1mono: colour, width over
        the default line's (2 %), dashed and presence equal twoway's."""
        bad = []
        for scheme in ("s2color", "stcolor", "s1mono"):
            base_w = _P[f"Z1_{scheme}"]["lines"][0]["width"]
            dflt, _ = _draw({"xline": "3000"}, mode, scheme)
            dflt_w = dflt[0].line_width
            for i in range(1, 17):
                rec = _P[f"S{i:02d}_{scheme}"]
                spans, _ = _draw(_go(rec["opt"]), mode, scheme)
                if not rec["lines"]:
                    if spans:
                        bad.append(f"{scheme} {rec['opt']}: drawn")
                    continue
                if len(spans) != 1:
                    bad.append(f"{scheme} {rec['opt']}: {len(spans)} spans")
                    continue
                s, ln = spans[0], rec["lines"][0]
                ratio, want = s.line_width / dflt_w, ln["width"] / base_w
                if (_hex(s.line_color) != ln["stroke"]
                        or abs(ratio - want) > 0.02 * want
                        or bool(s.line_dash) != ln["dashed"]):
                    bad.append(
                        f"{scheme} {rec['opt']}: dash {s.line_color} "
                        f"{ratio:.3f} {list(s.line_dash)}, twoway "
                        f"{ln['stroke']} {want:.3f} {ln['dashed']}")
        assert not bad, "\n".join(bad)

    @pytest.mark.parametrize("mode", MODES)
    def test_an_unknown_name_is_noted(self, mode):
        for name in ("p16", "P1", "nosuch"):
            spans, w = _draw({"xline": f"3000, lstyle({name})"}, mode)
            note = (f"dash: named style {name} not found in class "
                    "linestyle, default attributes used")
            assert w.count(note) == 1, (name, w)
            assert [_hex(s.line_color) for s in spans] == ["#000000"]


class TestLalign:
    @pytest.mark.parametrize("mode", MODES)
    def test_silent_and_noted(self, mode):
        plain, _ = _draw({"xline": "3000"}, mode)
        key = [(s.location, s.line_color, s.line_width, list(s.line_dash))
               for s in plain]
        for v in ("inside", "outside", "center"):
            spans, w = _draw({"xline": f"3000, lalign({v})"}, mode)
            assert not [m for m in w if "alignstroke" in m or "xline()" in m]
            assert [(s.location, s.line_color, s.line_width,
                     list(s.line_dash)) for s in spans] == key
        spans, w = _draw({"xline": "3000, lalign(nosuch)"}, mode)
        assert [m for m in w if "class alignstroke" in m] == [
            "dash: named style nosuch not found in class alignstroke, "
            "default attributes used"]
        assert len(spans) == 1


class TestStillNamed:
    @pytest.mark.parametrize("mode", MODES)
    def test_extent_is_s50s(self, mode):
        # Flipped (WP-30 P1.21b): noextend, extend and style(unextended)
        # were named; that was wrong because twoway draws them
        # (refline_extent_truth.json E02, E03, E04), abbreviated or not.
        _, w = _draw({"xline": "3000, noex ex st(unextended) "
                               "lstyle(p1) lalign(inside)"}, mode)
        assert not [m for m in w if "sub-option" in m], w


class TestDrawing:
    @pytest.mark.parametrize("mode", MODES)
    def test_level_and_bulk(self, mode, monkeypatch):
        """Every Span is under the glyphs (twoway draws added lines after
        the grid and before the plots, refline_truth.json O01), and one
        copy's 2,500 Spans arrive in one ``center`` assignment."""
        assert _P["O01"]["above_grid"] and _P["O01"]["below_markers"]
        calls = []
        real = dr._dash_refline_draw

        def spy(fig, *a, **k):
            before = len(fig.center)
            out = real(fig, *a, **k)
            calls.append(len(fig.center) - before)
            return out

        if mode == "saved":
            monkeypatch.setattr(dr, "_dash_refline_draw", spy)
        t0 = time.perf_counter()
        spans, _ = _draw({"xline": "1(1)2500", "yline": "20"}, mode)
        # A loose bound (one-at-a-time add_layout took 4.4-5.5 s for 2,500
        # alone); the spy below is the exact check, so a loaded parallel
        # run does not make this flaky.
        assert time.perf_counter() - t0 < 15
        assert len(spans) == 2501
        assert {s.level for s in spans} == {"underlay"}
        if mode == "saved":
            assert calls == [2500, 1]
        if mode == "saved":
            # No add_layout: the copy's Spans are one center assignment.
            add = []
            fig = bokeh_figure()
            monkeypatch.setattr(type(fig), "add_layout",
                                lambda self, *a, **k: add.append(a))
            real(fig, "xline", "height", [1.0, 2.0, 3.0], {}, None, Span)
            assert add == []
            assert sum(isinstance(c, Span) for c in fig.center) == 3

    @pytest.mark.parametrize("mode", MODES)
    def test_a_line_never_widens_an_axis(self, mode):
        def x_range(go):
            spec = _spec([_sc()], {"scheme": "s2color"}, go)
            if mode == "saved":
                root = _standalone(spec)[0]._last_layout_root
            else:
                root = _served(spec)[0]
            f = [p for p in root.select({"type": Plot})
                 if getattr(p, "x_range", None) is not None]
            return [(p.x_range.start, p.x_range.end) for p in f]
        assert x_range({"xline": "100000"}) == x_range({})
        # An unextended line neither (WP-30 P1.21b).
        assert x_range({"xline": "100000, noextend"}) == x_range({})


class TestAfterAFilterMove:
    @pytest.mark.parametrize("mode", MODES)
    def test_lines_survive(self, mode):
        go = {"xline": "2000(500)3000, lc(red)", "yline": "20"}
        bo = {"scheme": "s2color", "filter": "price, type(range)"}
        spec = _spec([_sc()], bo, go)
        move = ("RangeSlider", (4500.0, 11385.0))
        want = [("height", 2000.0), ("height", 2500.0), ("height", 3000.0),
                ("width", 20.0)]
        if mode == "saved":
            r = _render(spec)
            _move(r, move)
            got = sorted((s.dimension, s.location)
                         for s in r._last_layout_root.select({"type": Span}))
        else:
            figs, _ = _served_after_move(spec, move)
            got = sorted((a["dimension"], a["location"]) for f in figs
                         for a in f["annotations"] if a["kind"] == "Span")
        assert got == want


class TestTheLimit:
    @pytest.mark.parametrize("mode", MODES)
    def test_the_renderer_ceiling(self, mode):
        seen, other = set(), set()
        assert dr._dash_refline_tally(seen, 3) == 3
        assert dr._dash_refline_tally(seen, 4) == 7
        assert dr._dash_refline_tally(other, 2) == 2
        assert dr._dash_refline_tally(None, 5) == 5
        # 41 copies of 2,440 positions: 100,040 past the 100,000 ceiling.
        go = {"xline": ", ".join(["1(1)2440"] * 41)}
        spec = _spec([_sc()], {"scheme": "s2color"}, go)
        # The saved renderer wraps a figure's error in its RuntimeError;
        # the served app raises it as it is.
        msg = "more than 100,000 reference lines"
        if mode == "saved":
            with pytest.raises(RuntimeError, match=msg) as ei:
                _standalone(spec)
            assert isinstance(ei.value.__cause__, dr.DashLimitError)
        else:
            with pytest.raises(ValueError, match=msg) as ei:
                _served(spec)
            assert type(ei.value).__name__ == "DashLimitError"

    def test_the_row(self):
        assert dr._DASH_LIMITS["reflines"] == (10_000, 100_000,
                                                "dash_max_reflines")
        ado = open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8").read()
        assert "reflines=10000,100000" in ado


class TestTheServedCopy:
    def test_the_app_carries_the_helpers(self, tmp_path):
        spec = _spec([_sc()], {"scheme": "s2color"}, {"xline": "1/3"})
        from test_mode_parity import _write
        _, sp, dp = _write(spec)
        ap = tmp_path / "app.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(str(ap))
        src = ap.read_text(encoding="utf-8")
        for name in ("_dash_refline_copies", "_dash_refline_positions",
                     "_dash_refline_tally"):
            assert f"def {name}(" in src, name


class TestTheHelp:
    def test_the_help_documents_it(self):
        h = open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8").read()
        i = h.index("{title:Axis and Display Options}")
        assert "{cmdab:xli:ne(}{it:linearg}" in h[i:]
        assert "{cmdab:yli:ne(}{it:linearg}" in h[i:]
        assert "{it:Reference lines.}" in h[i:]
        assert "{synopt:{cmd:$dash_max_reflines}}" in h
