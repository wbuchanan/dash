"""WP-33 section 33-11 (GW-11): dash's plot region under scale() against
twoway's, in headless Chrome (release tier, DECISIONS A-10).

twoway's truth is test/fixtures/scale_frame_truth.json
(scripts/extract_scale_frame_truth.do): for two commands and scale(0.5,
0.75, 1, 1.5, 2) the plot region in SVG units, 720 to the inch.  dash's
lone figure is drawn on a 528 px wide page (s2color's 1.375 ratio gives
384 px, the fixture's 5.5 x 4 inches at 96 px to the inch), and each side's
inset -- the figure view's frame bbox against its own bbox -- is fitted
against the factor by least squares.  Per command and side (D-33-11.e):
dash's residuals within 1.5 px; the slope within 15 % of twoway's or 2 px
per unit, whichever is larger; the intercept within 3 px.  Each failing
check is listed in test/scale_frame_known.py under the item that fixes
it.  Both modes: the served app's document is written with file_html.
"""
import json
import os
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import range_probe  # noqa: E402
import responsive_probe  # noqa: E402
import scale_frame_known as sfk  # noqa: E402
from conftest import auto_df, load_app, make_data_json  # noqa: E402
from known_differences import known_problems  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME)",
                allow_module_level=True)

pytestmark = pytest.mark.release

_FIX = os.path.join(_HERE, "fixtures", "scale_frame_truth.json")
_KS = ("0.5", "0.75", "1", "1.5", "2")
_SIDES = ("top", "left", "bottom", "right")
_SC = {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}
_LF = {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}
_COMMANDS = {
    "A": ([_SC], {"title": '"T"'}),
    "B": ([_SC, _LF], {"title": '"T"', "subtitle": '"S"', "ytitle": '"Y"',
                       "xtitle": '"X"', "note": '"N"'}),
}

#: The figure view's bbox and frame bbox [top, left, bottom, right], in
#: CSS px (test-only use of BokehJS view internals): the Plot view is
#: found under the root views Bokeh.index holds.
_INSETS_JS = r"""
(() => {
  const seen = new Set();
  let hit = null;
  const walk = (v) => {
    if (!v || seen.has(v) || hit) return;
    seen.add(v);
    if (v.model && (v.model.type === "Plot" || v.model.type === "Figure")
        && v.frame) { hit = v; return; }
    for (const k of ["child_views", "renderer_views"]) {
      const c = v[k];
      if (!c) continue;
      const xs = typeof c.values === "function" ? [...c.values()]
        : (Array.isArray(c) ? c : []);
      for (const x of xs) walk(x);
    }
  };
  for (const v of Object.values(Bokeh.index)) walk(v);
  if (!hit) return null;
  const b = hit.bbox, f = hit.frame.bbox;
  return JSON.stringify([b.top, b.left, b.bottom, b.right,
                         f.top, f.left, f.bottom, f.right].map(Math.round));
})()
"""


class _ScaleProbe(range_probe.RangeProbe):
    def viewport(self, w, h):
        """Set the page to *w* x *h* CSS px and reload it."""
        self._send("Emulation.setDeviceMetricsOverride",
                   {"width": w, "height": h, "deviceScaleFactor": 1,
                    "mobile": False})
        self._eval("window.__dashOld = true")
        self._send("Page.reload", {})
        self._wait_for("!window.__dashOld && (" + range_probe._READY_JS
                       + ")")


def _spec(plots, go):
    g = {"name": "g1"}
    g.update(go)
    b = {"layout": "auto", "link": "", "filter": "", "theme": "",
         "scheme": "s2color", "session_scheme": "", "title": "",
         "subtitle": "", "registry": "g1", "tabs": "",
         "filter_position": "top", "csv": "0", "level": "95",
         "formats": {}, "limits": {}}
    return {"graphs": [{"plots": plots, "graph_options": g, "if_expr": "",
                        "in_expr": ""}], "kpis": [], "build_options": b}


def _page(mode, command, k, wd):
    plots, go = _COMMANDS[command]
    go = dict(go, scale=k)
    stem = os.path.join(wd, "%s_%s_%s" % (mode, command, k))
    sp, dp, out = stem + "_s.json", stem + "_d.json", stem + ".html"
    with open(sp, "w") as fh:
        json.dump(_spec(plots, go), fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(auto_df.__wrapped__()), fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            html = dr.DashRenderer(sp, dp, out).render()
        else:
            from bokeh.document import Document
            from bokeh.embed import file_html
            from bokeh.io import curdoc
            from bokeh.resources import INLINE
            ap = stem + "_app.py"
            dr.ServerAppBuilder(sp, dp).build(ap)
            mod = load_app(ap, "_sf_app_%s_%s" % (command, k.replace(".", "_")))
            curdoc().clear()
            doc = Document()
            mod.make_document(doc)
            html = file_html(doc, resources=INLINE, title="scale frame")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out


def _dash_insets(mode, command, wd):
    """{k: {side: px}} of dash's figure for *command* in *mode*."""
    out = {}
    for k in _KS:
        with _ScaleProbe(_page(mode, command, k, wd), timeout=120) as p:
            p.viewport(528, 900)
            p.wait_settled(10)
            b = json.loads(p._eval(_INSETS_JS))
        out[k] = {"top": b[4] - b[0], "left": b[5] - b[1],
                  "bottom": b[2] - b[6], "right": b[3] - b[7]}
    return out


def _twoway_insets(command):
    """{k: {side: px}} of twoway's plot region, at 96 px to the inch."""
    with open(_FIX, encoding="utf-8") as fh:
        d = json.load(fh)
    out = {}
    for k in _KS:
        r = d["%s:%s" % (command, k)]
        p, w, h = r["plot"], r["canvas"]["w"], r["canvas"]["h"]
        out[k] = {s: v / 7.5 for s, v in (
            ("top", p["top"]), ("left", p["left"]),
            ("bottom", h - p["bottom"]), ("right", w - p["right"]))}
    return out


def _fit(ks, ys):
    """Least squares of ys on ks: (slope, intercept, largest residual)."""
    n = len(ks)
    mk, my = sum(ks) / n, sum(ys) / n
    slope = (sum((k - mk) * (y - my) for k, y in zip(ks, ys))
             / sum((k - mk) ** 2 for k in ks))
    icpt = my - slope * mk
    return slope, icpt, max(abs(y - icpt - slope * k) for k, y in zip(ks, ys))


def _compare(command, twoway, dash):
    """{"<command>:<side>:<check>": None | difference} (D-33-11.e)."""
    ks = [float(k) for k in _KS]
    out = {}
    for s in _SIDES:
        ts, ti, _ = _fit(ks, [twoway[k][s] for k in _KS])
        ds, di, dres = _fit(ks, [dash[k][s] for k in _KS])
        key = "%s:%s:" % (command, s)
        out[key + "linear"] = (None if dres <= 1.5 else
                               "dash's largest residual %.2f px" % dres)
        out[key + "slope"] = (None if abs(ds - ts) <= max(0.15 * abs(ts), 2)
                              else "twoway %.2f / dash %.2f px per unit"
                              % (ts, ds))
        out[key + "intercept"] = (None if abs(di - ti) <= 3 else
                                  "twoway %.2f / dash %.2f px" % (ti, di))
    return out


class TestTheComparison:
    def test_the_fit_and_the_three_checks(self):
        assert _fit([0, 1, 2], [1, 3, 5]) == pytest.approx((2, 1, 0))
        tw = {k: {s: 10 + 20 * float(k) for s in _SIDES} for k in _KS}
        same = _compare("A", tw, tw)
        assert len(same) == 12 and set(same.values()) == {None}
        off = {k: {s: v + 5 for s, v in tw[k].items()} for k in _KS}
        got = _compare("A", tw, off)
        assert [k for k, v in got.items() if v] == [
            "A:%s:intercept" % s for s in _SIDES]


class TestDashAgainstTwoway:
    def _check(self, mode, command):
        wd = tempfile.mkdtemp(prefix="dash_scale_frame_")
        res = _compare(command, _twoway_insets(command),
                       _dash_insets(mode, command, wd))
        known = {k: v for k, v in sfk.SCALE_FRAME_KNOWN.items()
                 if k.startswith(command + ":")}
        assert known_problems(
            res, known, "scale_frame",
            deliberate=sfk.SCALE_FRAME_DELIBERATE) == [], res

    @pytest.mark.parametrize("command", ("A", "B"))
    def test_the_insets(self, command):
        self._check("saved", command)

    @pytest.mark.parametrize("command", ("A", "B"))
    def test_the_insets_served(self, command):
        self._check("served", command)
