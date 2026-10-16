"""Reference lines beyond the frame and through a zoom (WP-31 D12,
section 38).

The defect (GAPS3 D12; register rows P2.54, P2.82): an unextended
xline()/yline() end (the scheme's ``yesno xyline_extend_low/high`` no, or
``noextend``) is written once at the finish (``_dash_refline_extents`` in
Python, ``dash_refline_extent`` on the saved page) and stayed where the
last finish put it after a wheel zoom or a pan: the zoom callback
(``_DASH_AXIS_FINISH_JS + _DASH_AXIS_ZOOM_JS``) re-ticked the counted axes
and never moved the lines, and was attached only to counted axes' ranges.

twoway's truth: test/fixtures/refline_frame_truth.json, written by
scripts/extract_refline_frame_truth.do.  ``_meta.arrow_unclipped`` is the
headless-Chrome probe of section 38's D-38.a: whether BokehJS paints a
data-unit Arrow beyond the frame.

While iterating run only this file (CLAUDE.md rule 10):
``python3 -m pytest test/test_refline_frame.py -q``.
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.models import (Arrow, CustomJS, FixedTicker, Plot,  # noqa: E402
                          Range1d)
from js_runner import run_js  # noqa: E402
from test_mode_parity import (_fire, _sc, _served, _spec,  # noqa: E402
                              _standalone, _widgets_of)

_FIX = json.load(open(os.path.join(_ROOT, "test", "fixtures",
                                   "refline_frame_truth.json"),
                      encoding="utf-8"))
_P = _FIX["probes"]
MODES = ("saved", "served")
#: The statement _DASH_AXIS_ZOOM_JS ends with (WP-31 D12, D-38.b).
_STATEMENT = ("for (const grp of plan) for (const p of grp.panels) "
              "if (p.lines && p.lines.some(l => l.range === ri)) "
              "dash_refline_extent(p, models);")


def _root(spec, mode):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r, _ = _standalone(spec)
            return r._last_layout_root, r
        doc, _ = _served(spec)
        return doc, None


def _plots(root):
    return [p for p in root.select({"type": Plot})
            if not str(p.name or "").startswith("dash_by_")]


def _zoom_cbs(rng):
    """The zoom CustomJS objects on *rng*'s change:start and change:end."""
    cbs = rng.js_property_callbacks or {}
    return [[c for c in cbs.get("change:" + a, ())
             if isinstance(c, CustomJS)
             and "dash_refline_extent" in (c.code or "")]
            for a in ("start", "end")]


def _go(**kw):
    return {"xline": "3000, noextend", **kw}


class TestTheFixture:
    def test_meta(self):
        assert sorted(_FIX["_meta"]) == [
            "arrow_unclipped", "born_date", "dash_commit", "extracted",
            "source", "stata_version"]
        assert _FIX["_meta"]["source"] == \
            "scripts/extract_refline_frame_truth.do"
        assert _FIX["_meta"]["arrow_unclipped"] in (True, False)

    def test_keys(self):
        assert set(_P) == {
            "outside.x_5100", "outside.x_5200", "outside.x_10000",
            "outside.x_neg", "outside.y_60", "outside.mixed",
            "outside.noextend", "inside.control", "zoom.asym"}
        assert all(rec["rc"] == 0 for rec in _P.values())

    def test_twoway_never_widens(self):
        """An added line never changes twoway's axes (D-38.c)."""
        for key, rec in _P.items():
            assert rec["axes_as_baseline"], key

    def test_twoway_draws_where_the_axis_maps(self):
        """A position the axis maps onto the canvas is drawn there, beyond
        the plot region when it lies outside the range (xline(5100));
        one mapped off the canvas is not seen there (xline(5200),
        xline(-500), yline(60)); twoway writes a far one at a wrapped
        coordinate (xline(10000) inside the plot region), which dash does
        not copy."""
        for key in ("outside.x_5100", "outside.x_5200", "outside.x_neg",
                    "outside.y_60", "inside.control"):
            rec = _P[key]
            (ln,) = rec["lines"]
            assert abs(ln["px"] - rec["axis_px"][0]) < 0.5, key
        assert _P["outside.x_5100"]["lines"][0]["outside"]
        assert _P["outside.x_5100"]["lines"][0]["on_canvas"]
        for key in ("outside.x_5200", "outside.x_neg", "outside.y_60"):
            assert not _P[key]["lines"][0]["on_canvas"], key
        far = _P["outside.x_10000"]
        assert far["axis_px"][0] > far["canvas"]["w"]
        assert not far["lines"][0]["outside"]

    def test_asymmetric_scheme_insets_the_low_end(self):
        """zoom.asym (``yesno xyline_extend_low no``): the xline's top
        reaches the frame and its bottom (the low end) is inset by the
        margin -- the geometry the zoom keeps."""
        rec = _P["zoom.asym"]
        (ln,) = rec["lines"]
        top, bottom = rec["region"][1], rec["region"][3]
        assert abs(ln["ends"][0] - top) < 0.5
        assert ln["ends"][1] < bottom - 1


class TestZoomCallback:
    def test_statement_present(self):
        """_DASH_AXIS_ZOOM_JS ends with the one statement, after its
        finishing guard."""
        code = dr._DASH_AXIS_ZOOM_JS
        assert _STATEMENT in code
        assert code.index("cb_obj._dash_finishing") < code.index(_STATEMENT)
        assert code.rstrip().endswith(_STATEMENT + "\n})();") or \
            code.rstrip().split(_STATEMENT, 1)[1].strip() == "})();"

    @pytest.mark.parametrize("mode", MODES)
    def test_attached_on_line_ranges(self, mode):
        """The y range an xline() spans carries one zoom callback on
        start and end, in both modes."""
        root, _ = _root(_spec([_sc()], {"scheme": "s2color"}, _go()), mode)
        (p,) = _plots(root)
        st, en = _zoom_cbs(p.y_range)
        assert len(st) == 1 and len(en) == 1 and st[0] is en[0]
        assert _STATEMENT in st[0].code

    @pytest.mark.parametrize("mode", MODES)
    def test_attached_without_count_axis(self, mode):
        """A fixed-tick axis (ylabel(10(5)40), no counted ticker) whose
        range a reference line spans still carries the callback."""
        root, _ = _root(_spec([_sc()], {"scheme": "s2color"},
                              _go(ylabel="10(5)40")), mode)
        (p,) = _plots(root)
        st, en = _zoom_cbs(p.y_range)
        assert len(st) == 1 and len(en) == 1

    @pytest.mark.parametrize("mode", MODES)
    def test_absent_without_lines(self, mode):
        """With fixed ticks and no reference line nothing is attached to
        the range."""
        root, _ = _root(_spec([_sc()], {"scheme": "s2color"},
                              {"ylabel": "10(5)40"}), mode)
        (p,) = _plots(root)
        assert _zoom_cbs(p.y_range) == [[], []]


def _node_zoom(fig, shift, finishing=False):
    """Run *fig*'s y-range zoom callback under node with the range moved
    by *shift* (start, end deltas); returns the arrows' (y_start, y_end)
    as the page writes them, in plan order."""
    (cb,), _ = _zoom_cbs(fig.y_range)
    plan = json.loads(cb.args["plan_json"])
    models = cb.args["models"]
    stubs = []
    for m in models:
        if isinstance(m, Range1d):
            stubs.append({"start": m.start, "end": m.end,
                          "_dash_finishing": bool(finishing)})
        elif isinstance(m, Arrow):
            stubs.append({k: getattr(m, k) for k in
                          ("x_start", "x_end", "y_start", "y_end")})
        elif isinstance(m, FixedTicker):
            stubs.append({"ticks": list(m.ticks)})
        else:
            stubs.append({})
    ri = models.index(fig.y_range)
    arrows = [ln["arrow"] for g in plan for p in g["panels"]
              for ln in p.get("lines", ()) if ln["range"] == ri]
    js = ("const plan_json = " + json.dumps(cb.args["plan_json"]) + ";\n"
          + "const models = " + json.dumps(stubs) + ";\n"
          + "const cb_obj = models[%d];\n" % ri
          + "cb_obj.start += %r; cb_obj.end += %r;\n" % shift
          + cb.code + "\n"
          + "process.stdout.write(JSON.stringify(%s.map(i => "
            "[models[i].y_start, models[i].y_end])));\n" % json.dumps(arrows))
    return run_js(js), [models[i] for i in arrows]


def _python_ends(fig, shift):
    rng = fig.y_range
    s0, e0 = rng.start, rng.end
    try:
        rng.start, rng.end = s0 + shift[0], e0 + shift[1]
        dr._dash_refline_extents(fig)
        return [(a.y_start, a.y_end) for a, *_ in fig._dash_refline_arrows]
    finally:
        rng.start, rng.end = s0, e0
        dr._dash_refline_extents(fig)


def _saved_fig(go):
    root, _ = _root(_spec([_sc()], {"scheme": "s2color"}, go), "saved")
    (p,) = _plots(root)
    return p


class TestZoomFollows:
    @pytest.mark.parametrize("shift", [(-10.0, 10.0), (4.0, -4.0),
                                       (5.0, 5.0)],
                             ids=["out", "in", "pan"])
    def test_ends_follow(self, shift):
        """A zoom out, a zoom in and a pan of the y range move an
        unextended xline's ends to the new range's margin, as
        _dash_refline_extents writes them (1e-9)."""
        fig = _saved_fig(_go())
        got, _ = _node_zoom(fig, shift)
        want = _python_ends(fig, shift)
        assert len(got) == len(want) == 1
        for g, w in zip(got, want):
            assert all(abs(a - b) <= 1e-9 * max(1.0, abs(b))
                       for a, b in zip(g, w)), (g, w)
        before = (fig._dash_refline_arrows[0][0].y_start,
                  fig._dash_refline_arrows[0][0].y_end)
        assert abs(got[0][0] - before[0]) > 1e-6

    def test_fixed_ticks_follow(self):
        """The same on an axis with fixed ticks (no counted ticker)."""
        fig = _saved_fig(_go(ylabel="10(5)40"))
        got, _ = _node_zoom(fig, (-10.0, 10.0))
        want = _python_ends(fig, (-10.0, 10.0))
        assert all(abs(a - b) <= 1e-9 * max(1.0, abs(b))
                   for a, b in zip(got[0], want[0]))

    def test_finishing_guard(self):
        """While a re-finish writes the range the callback returns before
        the statement: the arrow is untouched."""
        fig = _saved_fig(_go())
        a = fig._dash_refline_arrows[0][0]
        got, _ = _node_zoom(fig, (-10.0, 10.0), finishing=True)
        assert got == [[a.y_start, a.y_end]]


class TestServedAfterMove:
    def test_one_callback_per_range(self):
        """After a served filter move each line range still carries one
        zoom callback on start and end."""
        spec = _spec([_sc()], {"scheme": "s2color",
                               "filter": "foreign, type(dropdown)"}, _go())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            doc, _ = _served(spec)
        w = [x for x in _widgets_of(doc)
             if type(x).__name__ == "Select"][0]
        _fire(w, [v for v, lab in w.options if lab == "Foreign"][0])
        (p,) = _plots(doc)
        st, en = _zoom_cbs(p.y_range)
        assert len(st) == 1 and len(en) == 1
