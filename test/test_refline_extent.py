"""xline()/yline() extend, noextend and style() as twoway draws them
(WP-30 P1.21b, section 50).

The defect (DROPIN-REMAINING.md P1.21; GAPS2.md B22 d/e): ``noextend``,
``extend`` and ``style()`` were named as sub-options dash does not draw, and
every line spanned the whole frame.  twoway stops an unextended end at the
axis's scale, inset from the frame by the plot-region margin; the scheme's
``yesno xyline_extend_low/high`` set the default; ``style()`` then
``noextend`` then ``extend`` decide each copy, whatever order they are typed
in (_gs_parse_and_log_lines.ado 1.1.6).

twoway's truth: test/fixtures/refline_extent_truth.json, written by
scripts/extract_refline_extent_truth.do (insets are fractions of the plot
region along the line; 0 is the frame).  dash's ends are checked against
the inverse of its own pad, ``_dash_range_hull`` -- the axis's scale.

While iterating run only this file (CLAUDE.md rule 10):
``python3 -m pytest test/test_refline_extent.py -q``.
"""
import json
import os
import random
import re
import sys
import types
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.models import Arrow, Plot, Range1d, Span  # noqa: E402
from bokeh.plotting import figure as bokeh_figure  # noqa: E402
from js_runner import run_js  # noqa: E402
from test_mode_parity import (_P123A_W, _fire, _sc, _served,  # noqa: E402
                              _spec, _standalone, _widgets_of, plot_for)
from test_saved_filter_layers import _move, _render  # noqa: E402

_FIX = json.load(open(os.path.join(_ROOT, "test", "fixtures",
                                   "refline_extent_truth.json"),
                      encoding="utf-8"))
_P = _FIX["probes"]
MODES = ("saved", "served")
_SCHEME = {"s2color": (True, True), "dashxlow": (False, True),
           "dashxhigh": (True, False)}
_EPS = 1e-3


def _flags_of(line):
    """twoway's (low, high) extension of one fixture line."""
    return line["low_inset"] < _EPS, line["high_inset"] < _EPS


def _subs(opt, name):
    """The sub-options of the first ``name(...)`` in *opt*."""
    m = re.search(r"\b%s\(" % name, opt)
    i, depth = m.end(), 1
    while depth:
        depth += {"(": 1, ")": -1}.get(opt[i], 0)
        i += 1
    body = opt[m.end():i - 1]
    return body.split(",", 1)[1].strip() if "," in body else ""


def _style(subs):
    """The copy's recorded sub-options, as the renderer reads them."""
    bad = []
    inst = dr._dash_refline_instances("3000" + (", " + subs if subs else ""),
                                      bad)
    return inst[0][1], bad


#: probe -> (plots, build options, graph options); the probes a user
#: scheme file draws (E12-E14, E19) are TestTheFlags' and TestTheEnds'.
def _probe_spec(pid):
    rec = _P[pid]
    opt = rec["opt"]
    xs, ys = _subs(opt, "xline"), _subs(opt, "yline")
    c = lambda s: ", " + s if s else ""  # noqa: E731
    bo = {"scheme": rec["scheme"]}
    go = {"xline": "3000" + c(xs), "yline": "25" + c(ys)}
    plots = [_sc()]
    if pid == "E20":
        ys = ys.replace("axis(2)", "").strip()
        go = {"xline": "3000" + c(xs), "yline2": "5000" + c(ys)}
        plots = [_sc(), plot_for("scatter", {"yaxis": "2"}, yvar="price",
                                 xvar="weight")]
    elif pid == "E25":
        bo.update(_P123A_W)
        go["xline"] = "15345" + c(xs)
        plots = [plot_for("scatter", yvar="mpg", xvar="when")]
    for word, key in (("yscale(log)", "yscale"),
                      ("plotregion(margin(zero))", "plotregion"),
                      ("plotregion(margin(large))", "plotregion"),
                      ("plotregion(margin(l=10 b=0))", "plotregion"),
                      ("xscale(range(1000 6000))", "xscale"),
                      ("by(foreign)", "by")):
        if word in opt:
            go[key] = word[len(key) + 1:-1]
    return _spec(plots, bo, go)


_BUILT = ["E01", "E02", "E03", "E04", "E05", "E06", "E09", "E10", "E11",
          "E15", "E16", "E17", "E18", "E20", "E21", "E22", "E24", "E25",
          "E26"]


def _root(spec, mode):
    if mode == "saved":
        r, w = _standalone(spec)
        return r._last_layout_root, w
    return _served(spec)


def _lines(root):
    """Per drawn reference line: (axis "x"/"y", (low, high) extended, the
    ends' mismatch with the scale or frame, or None)."""
    out = []
    for p in root.select({"type": Plot}):
        if p.name in ("dash_by_head", "dash_by_foot"):
            continue                    # by()'s cells carry no axes
        for a in p.center:
            if isinstance(a, Span):
                out.append(("x" if a.dimension == "height" else "y",
                            (True, True), None))
            elif isinstance(a, Arrow) and a.end is None and a.start is None:
                vert = a.x_start == a.x_end
                rng = p.y_range if vert else p.x_range
                log = type(p.y_scale if vert else p.x_scale).__name__ \
                    == "LogScale"
                hull = dr._dash_range_hull(rng, "log" if log else None)
                s, e = rng.start, rng.end
                lo_in, hi_in = (hull if s <= e else hull[::-1])
                got = ((a.y_start, a.y_end) if vert
                       else (a.x_start, a.x_end))
                low = abs(got[0] - s) <= 1e-9 * max(1.0, abs(s))
                high = abs(got[1] - e) <= 1e-9 * max(1.0, abs(e))
                want = (s if low else lo_in, e if high else hi_in)
                ok = all(abs(g - w_) <= 1e-9 * max(1.0, abs(w_))
                         for g, w_ in zip(got, want))
                out.append(("x" if vert else "y", (low, high),
                            None if ok else (got, want)))
    return out


class TestTheFixture:
    def test_it_is_stamped_and_measures_the_margin(self):
        meta = _FIX["_meta"]
        assert {"stata_version", "born_date", "dash_commit",
                "extracted"} <= set(meta)
        assert {f"E{i:02d}" for i in range(1, 27)} <= set(_P)
        # 63.36 of the plot region's 2,388.33 SVG units (s2color).
        assert round(_P["E02"]["xline"][0]["low_inset"], 4) == 0.0265
        assert _P["E01"]["xline"][0]["low_inset"] == 0


class TestTheFlags:
    def test_rule(self):
        """Every s2color and user-scheme probe: the copy's two ends as
        twoway draws them (scheme, then style(), then noextend, then
        extend)."""
        bad = []
        for pid in sorted(_P):
            rec = _P[pid]
            # A margin moves where an unextended end lies, not whether it
            # is one (E16-E18).
            if rec["scheme"] not in _SCHEME or "by(" in rec["opt"] \
                    or "plotregion(" in rec["opt"]:
                continue
            lo, hi = _SCHEME[rec["scheme"]]
            scheme = types.SimpleNamespace(xyline_extend_low=lo,
                                           xyline_extend_high=hi)
            for axis in ("xline", "yline"):
                st, _ = _style(_subs(rec["opt"], axis).replace("axis(2)",
                                                               ""))
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    got = dr._dash_refline_extent_flags(st, scheme)
                for ln in rec[axis]:
                    if got != _flags_of(ln):
                        bad.append(f"{pid} {axis} {rec['opt']}: dash {got},"
                                   f" twoway {_flags_of(ln)}")
        assert not bad, "\n".join(bad)
        assert dr._dash_refline_extent_flags({}, None) == (True, True)

    def test_unknown_style_note(self):
        """style(nosuch) and style(Unextended): twoway's note, once per
        name, echoing at most 80 characters."""
        for pid in ("E07", "E08"):
            want = _P[pid]["notes"][0]
            name = re.search(r"named style (\S+) ", want).group(1)
            dr._DASH_NOTED.clear()
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                for _ in range(2):
                    assert dr._dash_refline_extent_flags(
                        {"style": name}, None) == (True, True)
            got = [str(m.message) for m in w if "gridlinestyle" in
                   str(m.message)]
            assert got == ["dash: " + want[len("(note: "):-1].strip()], got
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            dr._dash_refline_extent_flags({"style": "q" * 10000}, None)
        msg = [str(m.message) for m in w if "gridlinestyle" in
               str(m.message)]
        assert msg and max(len(t) for t in re.findall(r"q+", msg[0])) <= 80

    def test_the_words_are_drawn_not_named(self):
        """noextend, extend and their abbreviations are recorded, never
        appended to the named list."""
        for subs, key in (("noextend", "noextend"), ("noex", "noextend"),
                          ("ex", "extend"), ("st(extended)", "style")):
            st, bad = _style(subs)
            assert key in st and bad == [], (subs, st, bad)


class TestTheSchemeKeys:
    def test_every_scheme(self):
        """Every shipped scheme carries yes, yes, as scheme_truth.json; a
        scheme's `no' is read."""
        truth = json.load(open(os.path.join(
            _ROOT, "test", "fixtures", "scheme_truth.json"),
            encoding="utf-8"))
        schemes = {k: v for k, v in truth.items() if k != "_meta"}
        bad = []
        for name, rec in sorted(schemes.items()):
            sp = dr.SchemeParser(name)
            got = (sp.xyline_extend_low, sp.xyline_extend_high)
            want = (rec["xyline_extend_low"] == "yes",
                    rec["xyline_extend_high"] == "yes")
            if got != want:
                bad.append(f"{name}: dash {got}, twoway {want}")
        assert not bad and len(schemes) >= 26, bad
        fb = dr.SchemeParser.fallback()
        assert (fb.xyline_extend_low, fb.xyline_extend_high) == (True, True)
        fb._props["yesno xyline_extend_low"] = "no"
        fb._init_properties()
        assert (fb.xyline_extend_low, fb.xyline_extend_high) == (False, True)


class TestTheExtent:
    @pytest.mark.parametrize("mode", MODES)
    def test_probe(self, mode):
        """Every built probe: a Span where twoway reaches the frame at both
        ends, else an Arrow whose unextended ends sit at the axis's scale
        and extended ends at the frame -- by() panels, y2, log and date
        axes, margins, schemes."""
        bad = []
        for pid in _BUILT:
            rec = _P[pid]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                root, _ = _root(_probe_spec(pid), mode)
            got = _lines(root)
            for axis, letter in (("xline", "x"), ("yline", "y")):
                want = sorted(_flags_of(ln) for ln in rec[axis])
                have = sorted(f for a, f, _ in got if a == letter)
                if have != want:
                    bad.append(f"{pid} {axis}: dash {have}, twoway {want}")
            bad += [f"{pid}: ends {m}" for _, _, m in got if m]
        assert not bad, "\n".join(bad)


class TestTheEnds:
    def test_low_is_physical_and_log_is_log(self):
        """The low end is Bokeh's start (the bottom or left) on a reversed
        axis too (E19), and a log axis is inset in log10 units."""
        bad = []
        for rev, kind, low, high in ((True, None, False, True),
                                     (False, None, True, False),
                                     (False, "log", False, False),
                                     (True, "log", False, True)):
            fig = bokeh_figure(y_axis_type="log" if kind else "linear")
            fig.y_range = dr._dash_padded_range(
                10, 40, kind=kind, reverse=rev, margin=(0.03, 0.01))
            a = Arrow(start=None, end=None, x_start=1, x_end=1, y_start=1,
                      y_end=1)
            fig._dash_refline_arrows = [(a, "y", low, high)]
            dr._dash_refline_extents(fig)
            s, e = fig.y_range.start, fig.y_range.end
            h = dr._dash_range_hull(fig.y_range, kind)
            h = h if s <= e else h[::-1]
            want = (s if low else h[0], e if high else h[1])
            if abs(a.y_start - want[0]) > 1e-9 * abs(want[0]) \
                    or abs(a.y_end - want[1]) > 1e-9 * abs(want[1]):
                bad.append((rev, kind, (a.y_start, a.y_end), want))
        assert not bad, bad


def _move_spec():
    return _spec([_sc()], {"scheme": "s2color",
                           "filter": "foreign, type(dropdown)"},
                 {"xline": "3000, noextend", "yline": "25, noextend",
                  "by": "foreign"})


_MOVE = ("Select", "Foreign")


class TestAfterAFilterMove:
    @pytest.mark.parametrize("mode", MODES)
    def test_move(self, mode):
        """After a move that changes the by() graph's shared ranges, every
        panel's ends sit at the new scale."""
        spec = _move_spec()
        if mode == "saved":
            r = _render(spec)
            before = [(p.x_range.start, p.y_range.start) for p in
                      r._last_layout_root.select({"type": Plot})]
            _move(r, _MOVE)
            root = r._last_layout_root
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                root, _ = _served(spec)
            before = [(p.x_range.start, p.y_range.start)
                      for p in root.select({"type": Plot})]
            w = [x for x in _widgets_of(root)
                 if type(x).__name__ == "Select"][0]
            _fire(w, [v for v, lab in w.options if lab == _MOVE[1]][0])
        after = [(p.x_range.start, p.y_range.start)
                 for p in root.select({"type": Plot})]
        assert after != before
        got = _lines(root)
        assert len([g for g in got if g[1] == (False, False)]) == 4, got
        assert not [m for _, _, m in got if m], got


def _plan_of(spec):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r, _ = _standalone(spec)
    figs = {i: p for i, p in enumerate(
        r._last_layout_root.select({"type": Plot}))}
    plan, models = dr._dash_axis_plan(figs, {}, zoom=False)
    return json.loads(plan), models


class TestJsEqualsPython:
    def test_random_moves(self):
        """200 seeded range moves on a linear and a log axis: the page's
        dash_refline_extent writes what _dash_refline_extents writes."""
        rnd = random.Random(50)
        bad = []
        for go in ({"xline": "3000, noextend", "yline": "25, noextend"},
                   {"xline": "3000, noextend", "yscale": "log"}):
            plan, models = _plan_of(_spec([_sc()], {"scheme": "s2color"},
                                          go))
            lines = [ln for g in plan for p in g["panels"]
                     for ln in p.get("lines", ())]
            assert lines
            cases = []
            for _ in range(100):
                lo = rnd.uniform(1, 50)
                cases.append([lo, lo + rnd.uniform(0.5, 5000)])
            js = (dr._DASH_AXIS_FINISH_JS
                  + "const P = " + json.dumps(plan) + ";\n"
                  + "const C = " + json.dumps(cases) + ";\n"
                  + "const M = " + json.dumps({str(ln["range"]): 0
                                               for ln in lines}) + ";\n"
                  + "const out = [];\n"
                  + "const models = [];\n"
                  + "for (const ln of P.flatMap(g => g.panels).flatMap(p => p.lines || [])) {\n"
                  + "  models[ln.range] = models[ln.range] || {};\n"
                  + "  models[ln.arrow] = {x_start: 0, x_end: 0, y_start: 0, y_end: 0};\n"
                  + "}\n"
                  + "for (const c of C) {\n"
                  + "  for (const k of Object.keys(M)) { models[k].start = c[0]; models[k].end = c[1]; }\n"
                  + "  for (const g of P) for (const p of g.panels) dash_refline_extent(p, models);\n"
                  + "  out.push(P.flatMap(g => g.panels).flatMap(p => p.lines || []).map(ln => [models[ln.arrow].x_start, models[ln.arrow].x_end, models[ln.arrow].y_start, models[ln.arrow].y_end]));\n"
                  + "}\n"
                  + "process.stdout.write(JSON.stringify(out));\n")
            out = run_js(js)
            for c, row in zip(cases, out):
                for ln, got in zip(lines, row):
                    rng, arrow = models[ln["range"]], models[ln["arrow"]]
                    rng.start, rng.end = c
                    fig = types.SimpleNamespace(
                        x_range=rng, y_range=rng,
                        x_scale=None, y_scale=types.new_class(
                            "LogScale" if ln["kind"] == "log"
                            else "LinearScale")(),
                        _dash_refline_arrows=[(arrow, ln["letter"],
                                               bool(ln["low"]),
                                               bool(ln["high"]))])
                    fig.x_scale = fig.y_scale
                    dr._dash_refline_extents(fig)
                    i = 2 if ln["letter"] == "y" else 0
                    py = ((arrow.y_start, arrow.y_end) if i
                          else (arrow.x_start, arrow.x_end))
                    if any(abs(a - b) > 1e-9 * max(1.0, abs(b))
                           for a, b in zip(got[i:i + 2], py)):
                        bad.append((c, ln["letter"], got[i:i + 2], py))
        assert not bad, bad[:5]


class TestThePlanCarriesNoUserText:
    def test_plan_and_code(self):
        """The plan's lines hold numbers, the letters x/y and kinds only;
        a plan naming another letter writes nothing (node)."""
        plan, _ = _plan_of(_spec(
            [_sc()], {"scheme": "s2color"},
            {"xline": "3000, noextend lcolor(red)",
             "yline": "25, style(unextended)"}))
        lines = [ln for g in plan for p in g["panels"]
                 for ln in p.get("lines", ())]
        assert len(lines) == 2
        for ln in lines:
            assert set(ln) == {"arrow", "range", "letter", "kind", "margin",
                               "low", "high"}
            assert ln["letter"] in ("x", "y") and ln["kind"] in (None, "log")
            assert all(isinstance(v, (int, float)) for v in
                       [ln["arrow"], ln["range"], ln["low"], ln["high"],
                        *ln["margin"]])
        js = (dr._DASH_AXIS_FINISH_JS
              + "const out = [];\n"
              + "for (const L of ['constructor', '__proto__', 'x_', 'z']) {\n"
              + "  const a = {x_start: 1, x_end: 1, y_start: 1, y_end: 1};\n"
              + "  const models = [a, {start: 0, end: 10}];\n"
              + "  dash_refline_extent({lines: [{arrow: 0, range: 1, letter: L,"
              + " kind: null, margin: [0.1, 0.1], low: 0, high: 0}]}, models);\n"
              + "  out.push(JSON.stringify(a) + Object.keys(Object.getPrototypeOf(a)).length);\n"
              + "}\n"
              + "process.stdout.write(JSON.stringify(out));\n")
        out = run_js(js)
        assert out == ['{"x_start":1,"x_end":1,"y_start":1,"y_end":1}0'] * 4
