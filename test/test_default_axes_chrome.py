"""WP-30 P1.3a (section 21): default axes in a real browser.

The saved page's re-finish (``_DASH_AXIS_FINISH_JS`` at the end of the
filter callback) and zoom code run in BokehJS; these read what headless
Chrome draws -- each axis view's ``tick_coords`` -- before and after a
filter move and a zoom, and time a 100-panel move against the batch-7
base.  Without Chrome these tests skip, as test_by_scales_chrome.py's do.
"""
import json
import os
import sys
import tempfile
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import range_probe  # noqa: E402
import responsive_probe  # noqa: E402
import test_by_scales as tb  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME)",
                allow_module_level=True)

pytestmark = pytest.mark.release

#: HEAD's 100-panel shared settle at the batch-7 base 41d6e10 (median of
#: three, Apple M2 Max, 07oct2026): the A9 budget is this plus 1 s.
_BASE_SETTLE_S = 0.484

_TMP = tempfile.mkdtemp(prefix="dash_ns_chrome_")

#: The drawn major ticks of every continuous axis, per plot, read from the
#: axis views (test-only use of BokehJS view internals): [[title, side,
#: [ticks...]], ...].
_TICKS_JS = r"""
(() => {
  const out = [];
  const seen = new Set();
  const walk = (v) => {
    if (!v || seen.has(v)) return;
    seen.add(v);
    if (v.model && v.model.ticker !== undefined && v.tick_coords !== undefined) {
      const tc = v.tick_coords;
      const dim = v.dimension;
      const t = v.parent && v.parent.model && v.parent.model.title
        ? String(v.parent.model.title.text || "") : "";
      out.push([t, v.model.y_range_name + "/" + v.model.x_range_name, dim,
                Array.from(tc.major[dim] || [])]);
    }
    const kids = [];
    for (const k of ["child_views", "renderer_views", "axis_views"]) {
      const c = v[k];
      if (!c) continue;
      if (typeof c.values === "function") for (const x of c.values()) kids.push(x);
      else if (Array.isArray(c)) kids.push(...c);
    }
    for (const x of kids) walk(x);
  };
  for (const v of Object.values(Bokeh.index)) walk(v);
  return JSON.stringify(out);
})()
"""


def _page(spec, df=None):
    import test_default_axes as tda
    if df is None:
        _tag, sp, dp = tda._write(spec)
    else:
        from conftest import make_data_json
        tag = next(tb._SEQ)
        sp = os.path.join(_TMP, "spec_%d.json" % tag)
        dp = os.path.join(_TMP, "data_%d.json" % tag)
        with open(sp, "w") as fh:
            json.dump(spec, fh)
        with open(dp, "w") as fh:
            json.dump(make_data_json(df), fh)
    out = os.path.join(_TMP, "page_%d.html" % next(tb._SEQ))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        html = dr.DashRenderer(sp, dp, out).render()
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out


def _drawn(p):
    return json.loads(p._eval(_TICKS_JS))


def _axis_ticks(rows, dim):
    """The y (dim 1) or x (dim 0) axis's drawn ticks of the first plot."""
    return [round(v, 6) for v in [r for r in rows if r[2] == dim][0][3]]


class TestTheBrowserDrawsTwowaysAxes:
    def test_saved_before_and_after_a_move(self):
        import test_default_axes as tda
        out = _page(tda._spec(tda._SC, filt="price, type(range)"))
        with range_probe.RangeProbe(out, timeout=120) as p:
            p.wait_settled(10)
            rows = _drawn(p)
            assert _axis_ticks(rows, 1) == [10, 20, 30, 40]
            assert _axis_ticks(rows, 0) == [2000, 3000, 4000, 5000]
            p.move_range_slider(0.3)
            p.wait_settled(10)
            rows = _drawn(p)
            assert _axis_ticks(rows, 1) == [15, 20, 25, 30, 35, 40]
            # Q01: twoway under `if price<=7075.5` draws x 1500(500)4000.
            assert _axis_ticks(rows, 0) == [1500, 2000, 2500, 3000, 3500, 4000]
            assert p.js_errors() == []

    def test_a_zoom_keeps_labels(self):
        import test_default_axes as tda
        out = _page(tda._spec(tda._SC))
        with range_probe.RangeProbe(out, timeout=120) as p:
            p.wait_settled(10)
            p._eval("(() => { for (const d of Bokeh.documents) for (const m "
                    "of d.all_models) if (m && m.x_range !== undefined && "
                    "m.toolbar !== undefined) m.y_range.setv({start: 20, "
                    "end: 30}); return 1; })()")
            p.wait_settled(10)
            assert _axis_ticks(_drawn(p), 1) == [20, 22, 24, 26, 28, 30]
            assert p.js_errors() == []


class TestTheHundredPanelBudget:
    def test_settles_within_the_budget(self):
        t = [float((i * 7) % 113) for i in range(500)]
        df = pd.DataFrame({"g": [float(i % 100) for i in range(500)],
                           "y": [v + (i % 5) / 10.0 for i, v in enumerate(t)],
                           "t": t})
        spec = tb._spec([tb._plot("scatter", "y", "t")], {"by": "g"},
                        filt="t, type(range)")
        out = _page(spec, df)
        with range_probe.RangeProbe(out, timeout=120) as p:
            before = p.wait_settled(10)
            ys = {(r[1], r[2]) for r in before}
            secs = p.move_and_time(0.3, timeout=30.0)
            after = p.ranges()
            assert p.js_errors() == []
        print("hundred panels (default axes): shared %s s" % secs)
        assert secs is not None and secs <= _BASE_SETTLE_S + 1.0, secs
        assert {(r[1], r[2]) for r in after} != ys


_FRAME_LEFT_JS = r"""
(() => {
  const out = [];
  const seen = new Set();
  const walk = (v) => {
    if (!v || seen.has(v)) return;
    seen.add(v);
    if (v.frame && v.frame.bbox && v.model && v.model.renderers) {
      out.push(v.frame.bbox.left);
    }
    for (const k of ["child_views", "renderer_views"]) {
      const c = v[k];
      if (!c) continue;
      if (typeof c.values === "function") for (const x of c.values()) walk(x);
      else if (Array.isArray(c)) c.forEach(walk);
    }
  };
  for (const v of Object.values(Bokeh.index)) walk(v);
  return JSON.stringify(out);
})()
"""


class TestOffFill:
    def test_painted(self):
        """WP-44 AX-7: in BokehJS, yscale(off fill) keeps the plain axis's
        space -- its frame starts where the plain graph's does, the clear
        labels and title still measured -- and yscale(off) gives it up."""
        import test_default_axes as tda
        left = {}
        for case, go in (("plain", {}), ("fill", {"yscale": "off fill"}),
                         ("off", {"yscale": "off"})):
            out = _page(tda._spec(tda._SC, go))
            with range_probe.RangeProbe(out, timeout=120) as p:
                p.wait_settled(10)
                left[case] = json.loads(p._eval(_FRAME_LEFT_JS))[0]
                assert p.js_errors() == []
        assert abs(left["fill"] - left["plain"]) < 1.0, left
        assert left["off"] < left["plain"] - 10, left
