"""WP-30 P1.20b (section 47): the plot-region margin and inner box.

BUGS.md "plotregion(margin()) and the plot region's inner box options
have no effect": ``plotregion(margin(zero))`` kept twoway's 2.2% default
margin and ``plotregion(margin(l+10))`` and ``plotregion(ifcolor(red))``
changed nothing, with no note, in both modes.

Every expectation is twoway's own, from ``test/fixtures/margin_truth.json``
(``scripts/extract_margin_truth.do``): one test per (fixture, mode) loops
over every probe row and reports every mismatch.

While iterating: ``python3 -m pytest test/test_region_margins.py -q``.
"""
import glob
import json
import math
import os
import random
import sys
import time

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_scales as tb  # noqa: E402
import test_default_axes as tda  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "margin_truth.json")
_MODES = ("saved", "served")
_SC = tda._SC
_P = "plotregion"

#: probe -> (scheme, graph options, plots) as dash is given them.
_PROBES = {
    "DEF": ("s2color", {}, _SC),
    "ZERO": ("s2color", {_P: "margin(zero)"}, _SC),
    "BOGUS": ("s2color", {_P: "margin(bogus)"}, _SC),
    "L10": ("s2color", {_P: "margin(l+10)"}, _SC),
    "LM5": ("s2color", {_P: "margin(l-5)"}, _SC),
    "LEQ0": ("s2color", {_P: "margin(l=0)"}, _SC),
    "LEQ10": ("s2color", {_P: "margin(l=10)"}, _SC),
    "L5": ("s2color", {_P: "margin(l5)"}, _SC),
    "L5L5": ("s2color", {_P: "margin(l+5 l+5)"}, _SC),
    "LSP": ("s2color", {_P: "margin(l +10)"}, _SC),
    "Q3": ("s2color", {_P: "margin(1 2 3)"}, _SC),
    "Q4": ("s2color", {_P: "margin(1 2 3 4)"}, _SC),
    "Q5": ("s2color", {_P: "margin(1 2 3 4 5)"}, _SC),
    # S38's merge joins the copies in order (TR-38.6).
    "COPY": ("s2color", {_P: "margin(zero) margin(l+10)"}, _SC),
    "COPYR": ("s2color", {_P: "margin(l+10) margin(zero)"}, _SC),
    "MIX": ("s2color", {_P: "margin(zero) color(red) mar(t+5)"}, _SC),
    "XS": ("s2color", {"xsize": "10", "ysize": "3",
                       _P: "margin(l+10)"}, _SC),
    "REV": ("s2color", {"xscale": "reverse", _P: "margin(l+10)"}, _SC),
    "LOG": ("s2color", {"yscale": "log", _P: "margin(b+10)"}, _SC),
    "Y2": ("s2color", {_P: "margin(t+10)"}, tb.DUAL_Y),
    "ST_L10": ("stcolor", {_P: "margin(l+10)"}, _SC),
    "G1": ("s2color", {"graphregion": "margin(l+10)"}, _SC),
    "BY_B10": ("s2color", {"by": "foreign", _P: "margin(b+10)"}, _SC),
    "BY_ZERO": ("s2color", {"by": "foreign", _P: "margin(zero)"}, _SC),
    "I1": ("s2color", {_P: "ifcolor(red)"}, _SC),
    "I2": ("s2color", {_P: "icolor(red)"}, _SC),
    "I3": ("s2color", {_P: "ilcolor(red) ilwidth(thick)"}, _SC),
    "I4": ("s2color", {_P: "ifcolor(red%50) ilpattern(dash)"}, _SC),
    "I5": ("s2color", {_P: "istyle(none) ifcolor(red)"}, _SC),
    "I6": ("s2color", {_P: "ifcolor(red) margin(zero)"}, _SC),
    "I7": ("s2color", {_P: "ifc(red) ilc(blue)"}, _SC),
}
for _n in getattr(dr.SchemeParser, "_MARGINSTYLES", {}):
    _PROBES["NM_" + _n.replace("-", "_")] = ("s2color",
                                             {_P: "margin(%s)" % _n}, _SC)
#: twoway's own drawing of these is not reproduced (residual): L+10 is
#: noted and drawn as zero; allsides-ms is r(7) in twoway.
_RESIDUAL = {"CAPL", "NM_allsides_ms"}


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _spec(pid, filt=""):
    scheme, go, plots = _PROBES[pid]
    return tda._spec(plots, dict(go), scheme=scheme, filt=filt)


def _box(f):
    return [r for r in f.renderers + f.center
            if "dash_inner_box" in (getattr(r, "tags", None) or [])]


def _frame_fracs(f, letter, name="default"):
    """The page's (start side, end side) frame fractions on an axis: the
    distance from each end of the range to its inner hull over the span."""
    rng = tda._range(f, letter, name)
    ax = tda._axis(f, letter, name)
    log = type(ax).__name__ == "LogAxis"
    m = (f._dash_margin[letter] if name == "default"
         else f._dash_margin[letter])
    lo, hi = dr._dash_range_hull(rng, "log" if log else None, margin=m)
    tr = math.log10 if log else float
    s, e = tr(float(rng.start)), tr(float(rng.end))
    lo, hi = tr(lo), tr(hi)
    span = abs(e - s)
    if s <= e:
        return (lo - s) / span, (e - hi) / span
    return (s - hi) / span, (lo - e) / span


# ---------------------------------------------------------------------------
# The grammar, the ladder and the bounds (pure)
# ---------------------------------------------------------------------------

class TestTheMarginGrammar:
    def test_form(self):
        """Every form of D-47c against literal answers; measured forms as
        twoway draws them (margin_truth.json)."""
        sch = dr.SchemeParser("s2color")
        st = [2.2] * 4
        cases = [
            ("zero", [0, 0, 0, 0], None), ("sides", [3.5, 3.5, 0, 0], None),
            ("10-pt", [10 / 2.88] * 4, None),
            ("1 2 3 4", [1, 2, 3, 4], None), ("1 2 3", [1, 2, 3, 2.2], None),
            ("1 2 3 4 5", [5, 2, 3, 4], None),
            ("l+10", [12.2, 2.2, 2.2, 2.2], None),
            ("l +10", [12.2, 2.2, 2.2, 2.2], None),
            ("l-5", [-2.8, 2.2, 2.2, 2.2], None),
            ("l=0", [0, 2.2, 2.2, 2.2], None),
            ("l+5 l+5", [12.2, 2.2, 2.2, 2.2], None),
            ("t+5 b=1", [2.2, 2.2, 1, 7.2], None),
            ("", st, None),
            ("bogus", [0] * 4, "bogus"), ("l5", [0] * 4, "l5"),
            ("L+10", [0] * 4, "L+10"), ("1;x:y", [0] * 4, "1;x:y"),
            ("1e400 1 1 1", [0] * 4, "1e400 1 1 1"),
            ("x" * 3000, [0] * 4, "x" * 80),
        ]
        bad = []
        for text, want, note in cases:
            got, noted = dr._dash_margin_sides(text, st, sch, 4.0)
            if noted != note or any(abs(a - b) > 1e-9
                                    for a, b in zip(got, want)):
                bad.append((text[:20], got, noted))
        assert not bad, bad


class TestTheSchemeLadder:
    def test_styles(self):
        """The 28 marginstyles and the ladder equal Stata's files."""
        meta = _truth()["_meta"]
        bad = []
        for name, sides in meta["marginstyles"].items():
            ours = dr.SchemeParser._MARGINSTYLES.get(name)
            want = tuple(0 if v in ("0", "zero") else
                         ("pt", float(v[:-3])) if v.endswith("-pt") else v
                         for v in sides)
            if ours != want:
                bad.append((name, ours, want))
        if len(meta["marginstyles"]) != len(dr.SchemeParser._MARGINSTYLES):
            bad.append("count")
        for scheme, lad in meta["ladders"].items():
            if dr.SchemeParser(scheme).margin_ladder != lad:
                bad.append(scheme)
        assert not bad, bad

    def test_every_shipped_scheme_carries_it(self):
        files = sorted(glob.glob(os.path.join(_HERE, "..", "dash-*.scheme")))
        assert len(files) == 26
        bad = []
        for path in files:
            with open(path, encoding="utf-8") as fh:
                keys = {ln.split()[1] for ln in fh
                        if ln.startswith("gsize ") and len(ln.split()) > 2}
            missing = set(dr.SchemeParser._MARGIN_LADDER) - keys
            if missing:
                bad.append((os.path.basename(path), sorted(missing)))
        assert not bad, bad

    def test_a_scheme_override_changes_the_margin(self, tmp_path,
                                                 monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "mt47.scheme").write_text(
            "#include s2color\ngsize medsmmargin relative5\n",
            encoding="utf-8")
        sch = dr.SchemeParser("mt47")
        assert sch.margin_ladder["medsmmargin"] == 5.0
        assert sch.plot_margin_sides == [5.0] * 4
        m = dr._dash_plot_margin(sch, {})
        assert m["y"] == pytest.approx((0.05, 0.05))


class TestTheHelpers:
    def test_padded_range_takes_a_pair(self):
        r = dr._dash_padded_range(10, 41, margin=(0.1, 0.02))
        whole = 31 / (1 - 0.12)
        assert r.start == pytest.approx(10 - 0.1 * whole, rel=1e-12)
        assert r.end == pytest.approx(41 + 0.02 * whole, rel=1e-12)
        assert r._dash_margin_f == (0.1, 0.02)
        rv = dr._dash_padded_range(10, 41, reverse=True, margin=(0.1, 0.02))
        assert (rv.start, rv.end) == (pytest.approx(41 + 0.1 * whole),
                                      pytest.approx(10 - 0.02 * whole))

    def test_range_hull_inverts_any_pair(self):
        rnd = random.Random(4705)
        bad = []
        for _ in range(200):
            pair = (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4))
            kind = rnd.choice([None, "log"])
            lo = rnd.uniform(0.5, 100.0)
            hi = lo * rnd.uniform(1.01, 50.0)
            rev = rnd.random() < 0.5
            r = dr._dash_padded_range(lo, hi, kind, rev, margin=pair)
            a, b = dr._dash_range_hull(r, kind)
            if abs(a - lo) > 1e-9 * hi or abs(b - hi) > 1e-9 * hi:
                bad.append((pair, kind, rev, lo, hi, a, b))
        assert not bad, bad[:3]

    def test_bounds(self):
        assert dr._dash_margin_pair((0.9, -0.9)) == (0.45, -0.45)
        a, b = dr._dash_margin_pair((0.45, 0.45))
        assert a + b == pytest.approx(0.9)
        assert dr._dash_margin_pair((0.6, 0.4)) == (0.45, 0.4)
        assert dr._dash_margin_pair(0.1) == (0.1, 0.1)
        assert dr._dash_margin_pair(float("nan")) is None


class TestHostileMargins:
    def test_bounded_and_fast(self):
        sch = dr.SchemeParser("s2color")
        for text, noted in (("l+1e308", False), ("l-1e308 l-1e308", False),
                            ("x" * 100000, True), ("l+" * 5000 + "1", True),
                            ("nan nan nan nan", True)):
            dr._dash_reset_notes()
            t0 = time.perf_counter()
            with pytest.warns(UserWarning) if noted else _no_warning():
                m = dr._dash_plot_margin(sch, {_P: "margin(%s)" % text})
            assert time.perf_counter() - t0 < 0.1, text[:20]
            for pair in m.values():
                assert all(math.isfinite(v) and -0.45 <= v <= 0.45
                           for v in pair) and sum(pair) <= 0.9 + 1e-12


class _no_warning:
    def __enter__(self):
        import warnings
        self._w = warnings.catch_warnings(record=True)
        self._caught = self._w.__enter__()
        warnings.simplefilter("always")

    def __exit__(self, *exc):
        self._w.__exit__(*exc)
        assert not [w for w in self._caught if "margin" in str(w.message)]
        return False


# ---------------------------------------------------------------------------
# Against twoway
# ---------------------------------------------------------------------------

class TestThePlotMargin:
    def test_probe(self):
        """_dash_plot_margin, as a fraction of min(W, H), equals twoway's
        margin_rel on every side of every probe within 0.0005."""
        rows, bad = _truth()["probes"], []
        for pid, row in sorted(rows.items()):
            if pid in _RESIDUAL or pid not in _PROBES or row["rc"] != 0:
                continue
            scheme, go, _plots = _PROBES[pid]
            sch = dr.SchemeParser(scheme)
            panels = len(row.get("panels") or [1])
            m = dr._dash_plot_margin(sch, go, panels=panels)
            w = float(go.get("xsize") or sch.graphsize_x)
            h = float(go.get("ysize") or sch.graphsize_y)
            short = min(w, h)
            for letter, ext in (("x", w), ("y", h)):
                if "margin_rel" not in (row.get(letter) or {}):
                    continue
                want = row[letter]["margin_rel"]
                got = [v * ext / short for v in m[letter]]
                if abs(got[0] - want["lo"]) > 5e-4 \
                        or abs(got[1] - want["hi"]) > 5e-4:
                    bad.append("%s %s dash %r twoway %r" % (pid, letter, got,
                                                            want))
        assert not bad, "\n".join(bad)


_RANGE_PROBES = ("ZERO", "L10", "COPY", "Q4", "REV", "LOG", "Y2", "XS")


class TestTheRangesTakeTheMargin:
    @pytest.mark.parametrize("mode", _MODES)
    def test_probe(self, mode):
        """Every range of the page leaves its figure's margin pair on each
        side, in visual order (REV: the l+10 side is the left), so a side
        twoway draws with no margin has none.  The pair is twoway's
        margin_rel (TestThePlotMargin) over the whole graph's side: a frame
        narrower than the graph, as twoway's plot region is, makes a wide
        margin a little narrower on the page than twoway's (residual;
        measured L10 left: 0.089 of the frame against twoway's 0.101)."""
        rows, bad = _truth()["probes"], []
        for pid in _RANGE_PROBES:
            f = tda._figs(mode, _spec(pid))[0]
            names = [("x", "default"), ("y", "default")] + [
                ("y", n) for n in f.extra_y_ranges]
            for letter, name in names:
                rng = tda._range(f, letter, name)
                m = f._dash_margin[letter]
                if tuple(rng._dash_margin_f) != tuple(m):
                    bad.append("%s %s carries %r" % (pid, letter,
                                                     rng._dash_margin_f))
                got = _frame_fracs(f, letter, name)
                if any(abs(a - b) > 1e-9 for a, b in zip(got, m)):
                    bad.append("%s %s page %r margin %r" % (pid, letter, got,
                                                            m))
                want = rows[pid][letter]["frame_frac"]
                for side, w in zip(got, (want["lo"], want["hi"])):
                    # twoway's zero is zero to its SVG's rounding.
                    if (abs(w) < 5e-4) != (abs(side) < 1e-12) or (
                            abs(w) >= 5e-4 and (side > 0) != (w > 0)):
                        bad.append("%s %s page %r twoway %r" % (
                            pid, letter, got, want))
        assert not bad, "\n".join(bad)


_MOVE = ("price, type(range)", "RangeSlider", (3291.0, 7075.5))


class TestAfterAFilterMove:
    @pytest.mark.parametrize("mode", _MODES)
    def test_margin_holds(self, mode):
        """After a move (saved: the page's callback under node) the
        re-finished ranges keep L10's per-side margin, and the Reset
        extent is the range."""
        f = tda._after(mode, _spec("L10", _MOVE[0]), *_MOVE[1:])[0]
        m = f._dash_margin["x"]
        got = _frame_fracs(f, "x")
        assert got == pytest.approx(m, abs=1e-9)
        rng = tda._range(f, "x")
        assert (rng.reset_start, rng.reset_end) == (rng.start, rng.end)


class TestByPanels:
    @pytest.mark.parametrize("mode", _MODES)
    def test_probe(self, mode):
        """by() scales a user margin with the default by f(G) (measured
        BY_B10: (2.2 + 10)% x .85): each panel's y frame fraction is its
        margin, which equals twoway's margin_rel within 0.0005."""
        rows, bad = _truth()["probes"], []
        for pid in ("BY_B10", "BY_ZERO"):
            figs = [f for f in tda._figs(mode, _spec(pid))
                    if hasattr(f, "_dash_margin")]
            want = rows[pid]["y"]["margin_rel"]
            sch = dr.SchemeParser("s2color")
            short = min(sch.graphsize_x, sch.graphsize_y)
            for f in figs:
                m = f._dash_margin["y"]
                got = [v * sch.graphsize_y / short for v in m]
                if abs(got[0] - want["lo"]) > 5e-4 \
                        or abs(got[1] - want["hi"]) > 5e-4:
                    bad.append("%s margin %r twoway %r" % (pid, got, want))
                if _frame_fracs(f, "y") != pytest.approx(m, abs=1e-9):
                    bad.append("%s page %r" % (pid, _frame_fracs(f, "y")))
        assert figs and not bad, "\n".join(bad)


# ---------------------------------------------------------------------------
# The inner box
# ---------------------------------------------------------------------------

def _hex(c):
    return None if c is None else str(c).lower()


class TestTheInnerBox:
    @pytest.mark.parametrize("mode", _MODES)
    def test_probe(self, mode):
        """I1-I7: one box at the axis hulls (twoway's inner rect), filled
        and outlined as twoway draws it."""
        rows, bad = _truth()["probes"], []
        thin = dr.OptionTranslator.translate_lwidth("thin")
        for pid in ("I1", "I2", "I3", "I4", "I5", "I6", "I7"):
            f = tda._figs(mode, _spec(pid))[0]
            boxes = _box(f)
            if len(boxes) != 1:
                bad.append("%s %d boxes" % (pid, len(boxes)))
                continue
            b = boxes[0]
            rects = rows[pid]["inner"]
            fill = [r for r in rects if r["fill"] not in (None, "none")]
            line = [r for r in rects if r["stroke"] not in (None, "none")]
            ref = (fill or line)[0]["data"]
            # A line-only box is read from its outline, which twoway
            # insets by half the line's width.
            tol = 0.002 if fill else 0.006
            for attr in ("left", "right", "bottom", "top"):
                span = 3240.0 if attr in ("left", "right") else 31.0
                if abs(getattr(b, attr) - ref[attr]) > tol * span:
                    bad.append("%s %s %r twoway %r" % (pid, attr,
                                                       getattr(b, attr),
                                                       ref[attr]))
            if fill:
                want_a = fill[0]["fill_opacity"] or 1.0
                if (_hex(b.fill_color), b.fill_alpha) != (fill[0]["fill"],
                                                          want_a):
                    bad.append("%s fill %r %r" % (pid, b.fill_color,
                                                  b.fill_alpha))
            elif b.fill_alpha != 0:
                bad.append("%s fill drawn" % pid)
            if line:
                want_w = line[0]["stroke_width"] / 5.76 * thin
                if _hex(b.line_color) != line[0]["stroke"] \
                        or b.line_alpha != 1.0 \
                        or abs(b.line_width - want_w) > 1e-9:
                    bad.append("%s line %r %r %r" % (pid, b.line_color,
                                                     b.line_alpha,
                                                     b.line_width))
            if ("ilpattern" in _PROBES[pid][1][_P]) != bool(b.line_dash):
                bad.append("%s dash %r" % (pid, b.line_dash))
        assert not bad, "\n".join(bad)

    @pytest.mark.parametrize("mode", _MODES)
    def test_follows_a_move(self, mode):
        """After a move the box's edges are the re-finished hulls (saved:
        written by the page's callback under node)."""
        f = tda._after(mode, _spec("I1", _MOVE[0]), *_MOVE[1:])[0]
        b = _box(f)[0]
        for letter, ends in (("x", ("left", "right")),
                             ("y", ("bottom", "top"))):
            lo, hi = tda._inner(f, letter)
            assert (getattr(b, ends[0]), getattr(b, ends[1])) \
                == pytest.approx((lo, hi), rel=1e-9)

    @pytest.mark.parametrize("mode", _MODES)
    def test_shared_by_ranges(self, mode):
        """Under by() every panel draws its own box over the one shared
        hull."""
        spec = tda._spec(_SC, {"by": "foreign", _P: "ifcolor(red)"},
                         scheme="s2color")
        figs = [f for f in tda._figs(mode, spec) if hasattr(f, "_dash_margin")]
        edges = set()
        for f in figs:
            b = _box(f)
            assert len(b) == 1
            assert (b[0].left, b[0].right) == pytest.approx(tda._inner(f, "x"))
            edges.add((b[0].left, b[0].right, b[0].bottom, b[0].top))
        assert len(figs) == 2 and len(edges) == 1


class TestNoBoxWithoutInnerOptions:
    @pytest.mark.parametrize("mode", _MODES)
    def test_no_annotation(self, mode):
        for go in ({}, {_P: "color(red) margin(zero)"},
                   {"graphregion": "ifcolor(red)"}):
            f = tda._figs(mode, tda._spec(_SC, go, scheme="s2color"))[0]
            assert not _box(f), go


class TestTheNotes:
    @pytest.mark.parametrize("mode", _MODES)
    def test_unknown_margin_noted_once(self, mode):
        """twoway's note for an unknown margin, once per graph although
        by() recomputes the margin per panel set."""
        spec = tda._spec(_SC, {"by": "foreign", _P: "margin(bogus)"},
                         scheme="s2color")
        _figs, msgs = tb._draw(mode, spec)
        notes = [m for m in msgs if "class margin" in m]
        assert notes == ["dash: named style bogus not found in class margin, "
                         "default attributes used"], msgs
