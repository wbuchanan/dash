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
                 (e + 1.0, e + 7.0e9, 4, "tC"),
                 # Flipped: test_log_and_tc_rules -- a held (null) %td answer
                 # was wrong because twoway ticks date axes by tsnatscale
                 # over the data (P1.3b, M1).
                 (0.0, 1.0e12, 5, "td")]
        got = _ticks_js(cases)
        bad = _mismatches(cases, got, dr._dash_axis_count_ticks)
        assert not bad, bad
        assert got[-1]


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


def _ts_js(cases):
    """dash_tsnatscale over *cases* ``(lo, hi, n, unit)`` in one node run."""
    return _js("for (const c of DATA) out.push(dash_tsnatscale(c[0], c[1], "
               "c[2], c[3]));", cases)


def _ts_ranges(rnd, unit, count):
    """*count* seeded ``(lo, hi, n, unit)`` inside 0100-9999, n 2-62: whole
    and fractional ends, one period, and ranges at either limit."""
    a, b = dr._DASH_TS_LIMITS[unit]
    out = []
    for i in range(count):
        span = (b - a) * 10 ** rnd.uniform(-6.5, -0.3)
        lo = rnd.uniform(a, b - span)
        if i % 7 == 0:
            lo = a if i % 2 else b - span
        hi = lo + span
        if i % 3 == 0:
            lo, hi = float(math.ceil(lo)), float(math.floor(hi))
        if i % 11 == 0:
            hi = lo + 1.0
        out.append((lo, hi, rnd.randint(2, 62), unit))
    return out


class TestJsTsnatscaleEqualsPython:
    """WP-30 P1.3b (D-44a): the saved page's date model is the Python one."""

    def test_the_fixture(self):
        with open(os.path.join(_HERE, "fixtures", "natscale_axes_truth.json"),
                  encoding="utf-8") as fh:
            t = json.load(fh)
        cases = [(r[1], r[2], r[3], r[0]) for part in
                 ("tsnatscale", "tsnatscale_sweeps", "date_graph")
                 for r in t[part]]
        assert len(cases) == 12000 + 15711 + 280
        bad = _mismatches(cases, _ts_js(cases),
                          lambda lo, hi, n, u:
                          dr._dash_tsnatscale_ticks(lo, hi, n, u))
        assert not bad, (len(bad), bad[:5])

    def test_random_ranges(self):
        rnd = random.Random(4401)
        cases = [c for u in ("d", "w", "m", "q", "h", "y")
                 for c in _ts_ranges(rnd, u, 2000)]
        bad = _mismatches(cases, _ts_js(cases),
                          lambda lo, hi, n, u:
                          dr._dash_tsnatscale_ticks(lo, hi, n, u))
        assert not bad, (len(bad), bad[:5])

    def test_the_calendar(self):
        """ms -> unit and unit -> ms at month firsts 0100-9999 (every
        seventh month) and seeded instants, every unit."""
        e = dr._STATA_EPOCH_UNIX_MS
        rnd = random.Random(4402)
        months = list(range((100 - 1960) * 12, (9999 - 1960) * 12 + 12, 7))
        firsts = dr._stata_dates_to_datetime(
            __import__("pandas").Series(months, dtype="float64"), "tm")
        stamps = [float(v) for v in firsts.astype("int64").tolist()]
        stamps += [rnd.uniform(dr._STATA_MS_MIN, dr._STATA_MS_MAX) + e
                   for _ in range(10000)]
        stamps += [dr._STATA_MS_MIN + e - 1.0, dr._STATA_MS_MAX + e + 1.0]
        units = ("d", "w", "m", "q", "h", "y")
        to_unit = _js("for (const c of DATA) out.push(dash_ms_to_ts_unit("
                      "c[0], c[1]));", [(m, u) for m in stamps[::3]
                                         for u in units])
        bad = [(c, g) for c, g in zip(((m, u) for m in stamps[::3]
                                       for u in units), to_unit)
               if dr._dash_unix_ms_to_unit(*c) != g]
        kinds = ("td", "tw", "tm", "tq", "th", "ty")
        vals = {k: [rnd.uniform(*dr._DASH_TS_LIMITS[u]) for _ in range(2000)]
                + list(dr._DASH_TS_LIMITS[u])
                + [dr._DASH_TS_LIMITS[u][1] + 1.0]
                for k, u in zip(kinds, units)}
        vals["td"] += [v / 86400000.0 for v in stamps[:500]]
        cases = [(v, k) for k in kinds for v in vals[k]]
        to_ms = _js("for (const c of DATA) { const v = dash_ts_unit_to_ms("
                    "c[0], c[1]); out.push(isFinite(v) ? v : null); }", cases)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            want = []
            for k in kinds:
                s = dr._stata_dates_to_datetime(
                    __import__("pandas").Series(vals[k], dtype="float64"), k)
                want += [None if v is None or v != v else float(v)
                         for v in (s.astype("int64").where(s.notna(), None)
                                   .tolist())]
        bad += [(c, g, w) for c, g, w in zip(cases, to_ms, want) if g != w]
        assert not bad, (len(bad), bad[:5])

    def test_the_float_helpers(self):
        rnd = random.Random(4403)
        xs = [rnd.uniform(-1e7, 1e7) for _ in range(5000)]
        xs += [rnd.randint(-10 ** 6, 10 ** 6) + 0.5 for _ in range(2500)]
        xs += [rnd.randint(1, 10 ** 7) + rnd.randint(0, 63) / 64.0
               for _ in range(2500)]
        xs += [12345678901.25, 1234567.890625, -1234567.890625, 0.0]
        got = _js("for (const x of DATA) out.push([dash_round_half_even(x), "
                  "dash_g12(x)]);", xs)
        bad = [(x, g) for x, g in zip(xs, got)
               if g != [round(x), float("%.12g" % x)]]
        assert not bad, (len(bad), bad[:5])

    def test_the_axis_rule(self):
        """dash_axis_ticks equals _dash_axis_count_ticks for the six date
        kinds (epoch ms) and the six "su:" kinds (Stata units)."""
        rnd = random.Random(4404)
        e = dr._STATA_EPOCH_UNIX_MS
        cases = []
        for k, u in dr._DASH_TS_UNITS.items():
            for lo, hi, n, _ in _ts_ranges(rnd, u, 300):
                cases.append((lo, hi, 5, "su:" + k))
            for _ in range(300):
                a = rnd.uniform(dr._STATA_MS_MIN, dr._STATA_MS_MAX) + e
                b = min(a + 86400000.0 * 10 ** rnd.uniform(0, 5),
                        dr._STATA_MS_MAX + e)
                cases.append((a, b, rnd.randint(2, 12), k))
        cases.append((-1.0e6, 10.0, 5, "su:td"))
        past = (dr._STATA_MS_MAX + e - 1.0e12, dr._STATA_MS_MAX + e + 1.0e12,
                5, "td")
        got = _ticks_js(cases + [past])
        bad = _mismatches(cases, got, dr._dash_axis_count_ticks)
        assert not bad, (len(bad), bad[:5])
        # Past 31dec9999 the page keeps S35's off-date ticks (null: hold).
        assert got[-1] is None
