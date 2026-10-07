"""WP-30 P1.3a (section 21): the saved page's finisher twin against Python.

``dash_render._DASH_AXIS_FINISH_JS`` re-finishes the saved page's axes
after every filter move and on zoom; it must equal the Python finisher the
served app runs, or the two modes disagree after a move (RK-1).  Each
check here runs every input through ONE node process and reports every
mismatch.  Node is required (a skip is red under DASH_STRICT=1).

While iterating: ``python3 -m pytest test/test_natscale_js.py -q``.
"""
import json
import math
import os
import random
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402

pytestmark = js_runner.requires_node


def _js(body, data):
    """Run *body* after the finish JS with ``DATA`` bound; return what it
    prints (``out``)."""
    src = ("const DATA = JSON.parse(" + json.dumps(json.dumps(data)) + ");\n"
           + dr._DASH_AXIS_FINISH_JS + "\nconst out = [];\n" + body
           + "\nprocess.stdout.write(JSON.stringify(out));\n")
    return js_runner.run_js(src)


def _mismatches(cases, got, want_fn):
    bad = []
    for c, g in zip(cases, got):
        w = want_fn(*c)
        if w != g:
            bad.append((c, g, w))
    return bad


def _ticks_js(cases):
    return _js("for (const c of DATA) out.push(dash_axis_ticks(c[0], c[1], "
               "c[2], c[3]));", cases)


class TestJsNatscaleEqualsPython:
    def test_the_fixture(self):
        with open(os.path.join(_HERE, "fixtures", "natscale_truth.json"),
                  encoding="utf-8") as fh:
            t = json.load(fh)
        cases = [(r[0], r[1], r[2], None) for r in t["natscale"]]
        cases += [(r["min"], r["max"], r["n"], None) for r in t["drawn"]]
        bad = _mismatches(cases, _ticks_js(cases), dr._dash_axis_count_ticks)
        assert not bad, bad[:5]

    def test_random_ranges(self):
        rnd = random.Random(2130)
        cases = []
        for _ in range(5000):
            mag = 10.0 ** rnd.randint(-6, 9)
            a = rnd.uniform(-1, 1) * mag
            b = a + abs(rnd.gauss(0, 1)) * mag * rnd.choice([1e-3, 0.1, 1])
            cases.append((a, b, rnd.randint(1, 12), None))
        bad = _mismatches(cases, _ticks_js(cases), dr._dash_axis_count_ticks)
        assert not bad, (len(bad), bad[:5])

    def test_overflow(self):
        with open(os.path.join(_HERE, "fixtures", "natscale_axes_truth.json"),
                  encoding="utf-8") as fh:
            rows = json.load(fh)["overflow"]
        cases = [(r[0], r[1], r[2], None) for r in rows]
        bad = _mismatches(cases, _ticks_js(cases), dr._dash_axis_count_ticks)
        assert not bad, bad[:5]

    def test_log_and_tc_rules(self):
        e = dr._STATA_EPOCH_UNIX_MS
        cases = [(3291.0, 15906.0, 5, "log"), (0.5, 2.0, 5, "log"),
                 (-5.0, -1.0, 5, "log"),
                 (1.293951600e12 + e, 1.296e12 + e, 5, "tc"),
                 (e + 1.0, e + 7.0e9, 4, "tC")]
        got = _ticks_js(cases + [(0.0, 1.0e12, 5, "td")])
        bad = _mismatches(cases, got, dr._dash_axis_count_ticks)
        assert not bad, bad
        # A %td-%ty axis's ticks are held after a move (S44 ports them).
        assert got[-1] is None


class TestJsPaddingEqualsPython:
    def test_padded_ranges(self):
        rnd = random.Random(2131)
        cases = []
        for _ in range(2000):
            kind = rnd.choice([None, "log", "td", "tm", "tq", "tw", "ty"])
            lo = (rnd.uniform(0.1, 1e5) if kind == "log" else
                  rnd.uniform(-1e12, 1e12) if kind else rnd.uniform(-50, 50))
            hi = lo if rnd.random() < 0.2 else (
                lo * rnd.uniform(1, 30) if kind == "log"
                else lo + abs(rnd.gauss(0, 1)) * max(abs(lo), 1.0))
            if kind in ("tm", "tq", "ty", "td", "tw"):
                lo = hi = float(round(lo / 86400000.0) * 86400000.0)
            f = rnd.choice([None, 0.0, 0.006, 0.0132, 0.022, 0.3])
            cases.append((lo, hi, kind, rnd.random() < 0.3, f))
        got = _js("for (const c of DATA) out.push(dash_axis_pad(c[0], c[1], "
                  "c[2], c[3], c[4]));", cases)
        bad = []
        for c, g in zip(cases, got):
            r = dr._dash_padded_range(c[0], c[1], c[2], c[3], margin=c[4])
            w = (float(r.start), float(r.end))
            if not all(abs(x - y) <= 1e-9 * max(abs(y), 1.0)
                       for x, y in zip(g, w)):
                bad.append((c, g, w))
        assert not bad, (len(bad), bad[:5])


class TestJsFinishEqualsPython:
    def test_random_moves(self):
        """Seeded moves over built saved pages: the page's filter callback
        (node) re-finishes the axes as the Python finisher does over the
        same written data."""
        import test_default_axes as tda
        import test_by_scales as tb
        P = tb._plot
        rnd = random.Random(2132)
        bad = []
        pages = [
            tda._spec(tda._SC, filt="price, type(range)"),
            tda._spec(tb.DUAL_Y, {"by": "foreign"},
                      filt="price, type(range)"),
            tda._spec([P("scatter", "price", "weight"),
                       P("lfit", "price", "weight")], {"yscale": "log"},
                      filt="price, type(range)"),
            tda._spec([P("bar", "mpg", "weight")], {"ylabel": "#4"},
                      filt="price, type(range)"),
        ]
        for spec in pages:
            r = tda._saved(spec)
            w = r.filter_widgets[0]
            sess = js_runner.JsSession(r.filter_callbacks)
            for _ in range(10):
                a = rnd.uniform(3291, 15906)
                b = rnd.uniform(a, 15906)
                w.value = (a, b)
                sess.run(r.filter_callbacks[0])
                got = tda._axes_of(list(r.figures.values()))
                dr._dash_refinish_axes(r.figures, r._facet_map)
                want = tda._axes_of(list(r.figures.values()))
                if not tda._same_axes(got, want):
                    bad.append((spec["graphs"][0]["plots"][0]["type"],
                                (a, b), got, want))
        assert not bad, bad[:3]
