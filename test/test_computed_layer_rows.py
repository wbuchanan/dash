"""Every computed layer must compute from the rows it was given.

Thirteen ``map_*`` methods plus ``map_area`` accept a ``view=`` parameter and
never reference it: they read the whole ``source`` instead.  An AST scan names
them exactly -- ``map_area``, ``map_lfit``, ``map_qfit``, ``map_lfitci``,
``map_qfitci``, ``map_lowess``, ``map_lpoly``, ``map_lpolyci``, ``map_fpfit``,
``map_fpfitci``, ``map_histogram``, ``map_kdensity``, ``map_mspline`` and
``map_mband``.

Measured before the fix, on data where ``g==0`` is ``y = x`` and ``g==1`` is
``y ~= 50 + 2x``: a spec carrying ``{"type": "lfit", "if_expr": "g==0"}``
produced fitted endpoints 25.5 -> 30.0.  That is the *full-data* fit; the
subset answer is 1.0 -> 4.0.  The qualifier changed nothing and nothing warned.

These mappers cannot be fixed by attaching the view to the returned renderer:
each builds its OWN ``ColumnDataSource`` from a computed grid, so the view
would have nothing to filter.  The input arrays have to be masked before the
statistic is computed, which is what these tests assert.

Two assertions per layer, and the second is the one that matters:

* the qualified result DIFFERS from the unqualified one -- the bug signature;
* the qualified result EQUALS the same mapper run on a source built from the
  pre-filtered rows -- which is correctness, not merely "it changed".

``test/fixtures/qualified_stat_truth.json`` holds what Stata itself returns
for all fourteen layers on ``sysuse auto`` with and without ``if foreign==1``,
each entry cross-checked against the serset of the plotted ``.gph``.  The
mapper tests assert that the qualifier reaches the computation, which is
WP-02; comparing dash's estimators against Stata's is statistical fidelity
and belongs with ``stat_truth.json`` and ``test_statistical_truth.py``.  One
entry is consumed here, by ``TestTheAcceptanceCriteriaAsWritten``: AC-02.4
asks that ``(lfit mpg weight if foreign==1)`` draw the line
``regress mpg weight if foreign==1`` reports, and the fixture's lfit entry
is that regression, measured.

The mapper tests hand each mapper a view built by hand.  The acceptance
criteria are written against a SPEC, and between the spec and the mapper
stand the renderer, which builds the view from ``if_expr``, and the shared
glyph dispatch, which hands it on -- so ``TestAQualifiedSpecComputesFromItsRows``
renders the spec itself, in both render modes (ROADMAP WP-24's mutation
check of WP-02).
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from bokeh.document import Document
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource, GlyphRenderer
from bokeh.plotting import figure

import dash_render as dr
from conftest import make_data_json, make_spec
# The served app's own source, loaded as a namespace and given a Document --
# the helpers test_help_claims_6.py renders both modes with.
from test_adversarial_matrix import _app_source, _load_app, _write_inputs
# sysuse auto's mpg, weight and foreign, in the dataset's order.
from test_statistical_helpers import _AUTO_FOREIGN, _AUTO_MPG, _AUTO_WEIGHT

# g==0 is y = x exactly; g==1 is y ~= 50 + 2x.  Any statistic computed on the
# whole frame is far from the one computed on g==0 alone, so a layer that
# ignores its qualifier cannot accidentally produce the right answer.
_N = 24
_X = np.arange(1.0, _N / 2 + 1.0)
_DF = pd.DataFrame({
    "x": np.concatenate([_X, _X]),
    "y": np.concatenate([_X, 50.0 + 2.0 * _X]),
    "g": np.concatenate([np.zeros(len(_X)), np.ones(len(_X))]),
})
_SUBSET = _DF[_DF.g == 0].reset_index(drop=True)

# The 14 mappers under test, with the shape of call each one takes.
# "xy"   -> map_<name>(fig, source, yvar, xvar, options, view=, color_idx=)
# "dist" -> same signature, but xvar is ignored (histogram / kdensity)
_LAYERS = [
    ("lfit", "xy"), ("qfit", "xy"), ("lfitci", "xy"), ("qfitci", "xy"),
    ("lowess", "xy"), ("lpoly", "xy"), ("lpolyci", "xy"),
    ("fpfit", "xy"), ("fpfitci", "xy"),
    ("mspline", "xy"), ("mband", "xy"), ("area", "xy"),
    ("histogram", "dist"), ("kdensity", "dist"),
]

from conftest import render_models  # noqa: E402


def _source(frame):
    """A ColumnDataSource carrying the row-identity column the views use."""
    data = {c: list(frame[c]) for c in frame.columns}
    data[dr._ROW_ID_COLUMN] = list(range(len(frame)))
    return ColumnDataSource(data)


def _mask_view(frame, condition):
    """A CDSView whose BooleanFilter selects the rows *condition* selects.

    Built the way ``DashRenderer`` builds a per-plot qualifier view: a
    BooleanFilter aligned one-to-one with the source's rows.
    """
    mask = [bool(v) for v in condition]
    assert len(mask) == len(frame), "mask must align with the source rows"
    return CDSView(filter=BooleanFilter(booleans=mask))


def _call(name, kind, source, view):
    """Invoke one mapper and return the data of every renderer it produced."""
    mapper = dr.GlyphMapper()
    f = figure()
    fn = getattr(mapper, "map_" + name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if kind == "dist":
            # histogram and kdensity take options BEFORE xvar.
            result = fn(f, source, "y", {}, "", view=view, color_idx=0)
        else:
            result = fn(f, source, "y", "x", {}, view=view, color_idx=0)
    renderers = result if isinstance(result, (list, tuple)) else [result]
    out = []
    for r in renderers:
        src = getattr(r, "data_source", None)
        if src is None:
            continue
        out.append({k: [float(v) for v in vals]
                    for k, vals in src.data.items()
                    if vals is not None and len(vals)
                    # __dash_bin_rows (WP-31 H2l): each bar's member
                    # rows, a list per bar, not a computed number.
                    and not isinstance(vals[0], (str, list))})
    return out


@pytest.mark.parametrize("name,kind", _LAYERS, ids=[n for n, _ in _LAYERS])
class TestAQualifierReachesTheComputation:

    def test_the_qualified_result_differs_from_the_unqualified_one(
            self, name, kind):
        """The bug signature: the qualifier used to change nothing."""
        src = _source(_DF)
        allrows = _call(name, kind, src, None)
        qualified = _call(name, kind, src, _mask_view(_DF, _DF.g == 0))
        # A qualified layer that drew nothing differs too.  _call drops
        # empty columns, so a renderer that drew nothing is {}.
        assert qualified and all(qualified), (name, qualified)
        assert qualified != allrows, (
            "%s ignored its view: the qualified layer is identical to the "
            "all-rows layer" % name
        )

    def test_the_qualified_result_equals_the_prefiltered_one(self, name, kind):
        """Correctness, not merely difference.

        Masking the input must give exactly what the same mapper gives when
        handed a source containing only those rows.
        """
        via_view = _call(name, kind, _source(_DF),
                         _mask_view(_DF, _DF.g == 0))
        via_subset = _call(name, kind, _source(_SUBSET), None)
        # _call drops empty columns, so a layer that drew nothing on both
        # paths compared [{}] == [{}] and passed.  The 12 pre-filtered rows
        # draw on every renderer of all 14 layers (measured 24sep2026).
        assert via_subset and all(via_subset), (name, via_subset)
        assert len(via_view) == len(via_subset), (name, via_view, via_subset)
        for got, want in zip(via_view, via_subset):
            assert got.keys() == want.keys(), (name, got.keys(), want.keys())
            for key in want:
                np.testing.assert_allclose(
                    got[key], want[key], rtol=1e-9, atol=1e-9,
                    err_msg="%s: column %r differs from the pre-filtered run"
                            % (name, key),
                )

    def test_no_view_is_unchanged(self, name, kind):
        """The common case -- no qualifier -- must not move at all."""
        src = _source(_DF)
        a = _call(name, kind, src, None)
        b = _call(name, kind, _source(_DF), None)
        assert a == b

    def test_an_all_true_mask_matches_no_view(self, name, kind):
        """A view that selects everything is the same as no view."""
        none_view = _call(name, kind, _source(_DF), None)
        all_true = _call(name, kind, _source(_DF),
                         _mask_view(_DF, np.ones(len(_DF), dtype=bool)))
        assert len(none_view) == len(all_true), name
        # As above: a layer that drew nothing either way looped over no key.
        assert none_view and all(none_view), (name, none_view)
        for got, want in zip(all_true, none_view):
            assert got.keys() == want.keys(), (name, got.keys(), want.keys())
            for key in want:
                np.testing.assert_allclose(got[key], want[key],
                                           rtol=1e-9, atol=1e-9)


class TestTheMaskHelperDegradesSafely:
    """A malformed view must never take a layer down."""

    def test_none_view_yields_no_mask(self):
        assert dr.GlyphMapper._view_mask(None, 10) is None

    def test_a_boolean_filter_yields_its_mask(self):
        view = CDSView(filter=BooleanFilter(booleans=[True, False, True]))
        got = dr.GlyphMapper._view_mask(view, 3)
        np.testing.assert_array_equal(got, np.array([True, False, True]))

    def test_an_index_filter_is_expanded(self):
        from bokeh.models import IndexFilter
        view = CDSView(filter=IndexFilter(indices=[0, 2]))
        got = dr.GlyphMapper._view_mask(view, 3)
        np.testing.assert_array_equal(got, np.array([True, False, True]))

    def test_a_length_mismatch_warns_and_does_not_mask(self):
        view = CDSView(filter=BooleanFilter(booleans=[True, False]))
        with pytest.warns(UserWarning, match="does not match"):
            got = dr.GlyphMapper._view_mask(view, 5)
        assert got is None, "a mismatched mask must be ignored, not applied"

    def test_a_view_with_no_recognised_filter_yields_no_mask(self):
        class _Odd:
            filter = object()
        assert dr.GlyphMapper._view_mask(_Odd(), 3) is None


class TestLinkedFacetsComputeSeparately:
    """Linked ``by()`` panels used to draw byte-identical curves.

    Unlinked ``by()`` is correct because each panel gets its own
    ColumnDataSource.  Linked ``by()`` shares one source and distinguishes the
    panels with a CDSView, which these mappers discarded -- so the same command
    gave different answers depending on whether ``link()`` was present.
    """

    def test_unlinked_by_panels_differ_from_each_other(self, tmp_path):
        tops = _render_by_panels(tmp_path, linked=False)
        assert len(tops) >= 2, tops
        # g takes two values, so by(g) draws exactly two panels (measured
        # 24sep2026); a third -- a stray Total -- passed ">= 2".
        assert len(tops) == 2, tops
        assert tops[0] != tops[1], (
            "the two by() panels drew identical bars; each should describe "
            "its own group"
        )

    def test_linked_by_panels_differ_from_each_other(self, tmp_path):
        tops = _render_by_panels(tmp_path, linked=True)
        assert len(tops) >= 2, tops
        assert len(tops) == 2, tops
        assert tops[0] != tops[1], (
            "linked by() panels drew identical bars -- the per-panel view was "
            "discarded by the computed layer"
        )

    def test_linked_and_unlinked_by_agree(self, tmp_path):
        """The same command must not depend on link() for its numbers."""
        unlinked = _render_by_panels(tmp_path, linked=False)
        linked = _render_by_panels(tmp_path, linked=True)
        assert linked == unlinked, (linked, unlinked)


def _render_by_panels(tmp_path, linked):
    """Render ``histogram y, by(g)`` and return each panel's bar heights.

    ``link`` is a list of GRAPH NAMES, not a keyword -- an earlier draft of
    this helper passed "_all", which matches no graph, so the linked branch
    was never entered and the test passed against the unfixed code.
    """
    data_path = tmp_path / ("data_%s.json" % linked)
    data_path.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
    spec = {
        "graphs": [{
            "plots": [{"type": "histogram", "yvar": "y", "xvar": "",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"by": "g", "name": "g1"},
            "if_expr": "", "in_expr": "",
        }],
        "build_options": {"layout": "1 1", "level": "95", "formats": {},
                          "link": "g1" if linked else ""},
    }
    spec_path = tmp_path / ("spec_%s.json" % linked)
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    renderer = dr.DashRenderer(str(spec_path), str(data_path))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        render_models(renderer)
    panels = []
    for fig in renderer.figures.values():
        for rend in fig.renderers:
            src = getattr(rend, "data_source", None)
            if src is not None and "top" in src.data:
                panels.append([round(float(t), 6) for t in src.data["top"]])
    return panels


# ===========================================================================
# Through the renderer: a spec's own if_expr, saved and served
# ===========================================================================
#
# Measured under a WP-24 mutation that made the shared dispatch
# (_dash_add_glyph) hand the computed layers no view: every mapper test
# above stayed green, and of the eleven test files that cover qualified and
# faceted layers only the linked by() pair above and the saved kdensity and
# lpoly qualifier tests of test_help_claims_6.py went red -- a qualified
# lfit, qfit, lowess, mband or *ci layer drawing every row would have
# passed.  Likewise, with the served app never applying a layer's own
# qualifier, the only failures among those files were test_help_claims_6.py's
# two served tests; the served app's other guards (test_mode_parity.py,
# test_server_layer_defects.py) hold a qualified scatter, histogram and the
# ordinary types, not a qualified fit.  These render the spec.
#
# The reference is the same frame with the excluded rows' y set missing,
# not a frame without them: lpoly's grid follows the dataset's _N below 50
# observations, as twoway's does (test_statistical_helpers.py
# TestLpolyGridAgainstStata), so a shorter dataset draws a shorter grid for
# a reason that has nothing to do with the qualifier.  Measured in both
# modes: the qualified spec and this reference agree for all fourteen
# layers, and the qualified spec differs from the unqualified one for all
# fourteen.

_MODES = ["saved", "served"]

# The rows g==0 selects, the rest made missing: the dataset keeps its size.
# Both x and y (WP-31 C6b): a row with y alone missing is still in mband's
# and mspline's band count and x range, as in twoway, where an excluded
# row is not.
_MASKED_OUT = _DF.assign(y=np.where(_DF.g == 0, _DF.y, np.nan),
                         x=np.where(_DF.g == 0, _DF.x, np.nan))


def _spec_plot(name, kind, if_expr=""):
    """One plot of *name*, the way dash.ado writes it into the spec."""
    if kind == "dist":
        plot = {"type": name, "var": "y", "options": {}}
    else:
        plot = {"type": name, "yvar": "y", "xvar": "x", "options": {}}
    if if_expr:
        plot["if_expr"] = if_expr
    return plot


def _rendered(tmp_path, plots, frame, mode, tag, link="", graph_options=None):
    """The data of every source the graph's layers draw, each source once.

    *mode* "saved" renders through ``DashRenderer``; "served" builds the
    app ``ServerAppBuilder`` generates and gives its ``make_document`` a
    fresh Document -- the two routes a spec takes to a page.  *link* is
    ``build_options.link``; *graph_options* are added to the graph's own.
    """
    where = tmp_path / ("%s_%s" % (mode, tag))
    where.mkdir()
    spec = make_spec(plots, link=link)
    if graph_options:
        spec["graphs"][0]["graph_options"].update(graph_options)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            sp, dp = _write_inputs(where, spec, frame)
            renderer = dr.DashRenderer(sp, dp)
            render_models(renderer)
            rends = list(renderer._last_layout_root.select(
                {"type": GlyphRenderer}))
        else:
            ns = _load_app(_app_source(where, spec, frame),
                           "rows_%s_%s" % (tag, where.name))
            doc = Document()
            ns["make_document"](doc)
            rends = list(doc.select({"type": GlyphRenderer}))
    out, seen = [], set()
    for rend in rends:
        src = rend.data_source
        if src.id in seen:
            continue
        seen.add(src.id)
        out.append({k: [float(v) for v in vals]
                    for k, vals in src.data.items()
                    if vals is not None and len(vals)
                    # __dash_bin_rows (WP-31 H2l): each bar's member
                    # rows, a list per bar, not a computed number.
                    and not isinstance(vals[0], (str, list))})
    # Bokeh's select() walks a set of references, so the renderers of two
    # renders of one spec -- two by() panels, say -- come back in no fixed
    # order (measured: the same test passed and failed on one tree).  The
    # sources are put in an order read off their contents, repr() so that
    # a missing value sorts like any other.
    return sorted(out, key=lambda d: tuple(
        (k, tuple(repr(v) for v in d[k])) for k in sorted(d)))


def _assert_same_layers(got, want, what):
    assert got, "%s drew nothing" % what
    assert len(got) == len(want), (what, len(got), len(want))
    for g, w in zip(got, want):
        assert g.keys() == w.keys(), (what, sorted(g), sorted(w))
        for key in w:
            np.testing.assert_allclose(
                g[key], w[key], rtol=1e-9, atol=1e-9,
                err_msg="%s: column %r is not the one the selected rows "
                        "give" % (what, key))


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("name,kind", _LAYERS, ids=[n for n, _ in _LAYERS])
class TestAQualifiedSpecComputesFromItsRows:
    """AC-02.1 and AC-02.2 as written: a spec's own ``if_expr``."""

    def test_the_qualified_spec_draws_what_the_selected_rows_give(
            self, tmp_path, name, kind, mode):
        got = _rendered(tmp_path, [_spec_plot(name, kind, "g==0")], _DF,
                        mode, "q")
        want = _rendered(tmp_path, [_spec_plot(name, kind)], _MASKED_OUT,
                         mode, "m")
        _assert_same_layers(got, want, "%s if g==0 (%s)" % (name, mode))

    def test_the_qualified_spec_is_not_the_all_rows_layer(
            self, tmp_path, name, kind, mode):
        """The defect's signature: the qualifier used to change nothing."""
        got = _rendered(tmp_path, [_spec_plot(name, kind, "g==0")], _DF,
                        mode, "q")
        allrows = _rendered(tmp_path, [_spec_plot(name, kind)], _DF,
                            mode, "a")
        assert got != allrows, (
            "%s if g==0 (%s) drew the all-rows layer" % (name, mode))


def _one_line(layers):
    """The (x, y) arrays of the one line a lone lfit layer draws."""
    assert len(layers) == 1, layers
    return (np.asarray(layers[0]["x"], dtype=float),
            np.asarray(layers[0]["y"], dtype=float))


def _qualified_truth():
    with open(os.path.join(_HERE, "fixtures", "qualified_stat_truth.json"),
              encoding="utf-8") as fh:
        return json.load(fh)["layers"]["lfit"]


@pytest.mark.parametrize("mode", _MODES)
class TestTheAcceptanceCriteriaAsWritten:
    """ROADMAP WP-02's AC-02.1, AC-02.3 and AC-02.4, through the renderer."""

    def test_ac_02_3_linked_by_panels_are_the_unlinked_panels(
            self, tmp_path, mode):
        """``histogram mpg, by(foreign) link(_all)`` on sysuse auto draws
        two panels with different bars, and the same bars as without
        ``link()``.  TestLinkedFacetsComputeSeparately above links the graph
        by its name; this is the criterion's own ``link(_all)``, in both
        modes."""
        auto = pd.DataFrame({"mpg": np.asarray(_AUTO_MPG, dtype=float),
                             "foreign": np.asarray(_AUTO_FOREIGN, dtype=float)})
        plot = {"type": "histogram", "var": "mpg", "options": {}}

        def tops(link, tag):
            layers = _rendered(tmp_path, [plot], auto, mode, tag, link=link,
                               graph_options={"by": "foreign"})
            return [layer["top"] for layer in layers if "top" in layer]

        linked = tops("_all", "l")
        unlinked = tops("", "u")
        assert len(linked) == 2, linked
        assert linked[0] != linked[1], (
            "the two linked by() panels drew the same bars")
        assert len(unlinked) == 2, unlinked
        for got, want in zip(linked, unlinked):
            np.testing.assert_allclose(got, want, rtol=1e-12, atol=0)

    def test_ac_02_1_the_fit_of_y_equals_x_runs_from_1_to_4(
            self, tmp_path, mode):
        """``y = x`` for g==0 and ``y = 50 + 2x`` for g==1, x = 1..4: a spec
        with ``{"type": "lfit", "if_expr": "g==0"}`` draws the g==0 fit,
        1.0 at x = 1 to 4.0 at x = 4 -- not the fit of all eight rows."""
        x = np.arange(1.0, 5.0)
        frame = pd.DataFrame({"x": np.concatenate([x, x]),
                              "y": np.concatenate([x, 50.0 + 2.0 * x]),
                              "g": np.concatenate([np.zeros(4), np.ones(4)])})
        plot = {"type": "lfit", "yvar": "y", "xvar": "x", "options": {}}
        qx, qy = _one_line(_rendered(tmp_path, [dict(plot, if_expr="g==0")],
                                     frame, mode, "q"))
        ax, ay = _one_line(_rendered(tmp_path, [plot], frame, mode, "a"))
        np.testing.assert_allclose([qx[0], qx[-1]], [1.0, 4.0], atol=1e-12)
        np.testing.assert_allclose([qy[0], qy[-1]], [1.0, 4.0], atol=1e-9)
        # The fit of all eight rows is y = 25 + 1.5x: 26.5 to 31.0.
        np.testing.assert_allclose([ay[0], ay[-1]], [26.5, 31.0], atol=1e-9)

    def test_ac_02_4_lfit_if_foreign_is_statas_regression(
            self, tmp_path, mode):
        """``(lfit mpg weight if foreign==1)`` on sysuse auto draws the line
        Stata's ``regress mpg weight if foreign==1`` reports, over the
        foreign cars' weights -- the fixture's numbers, measured in Stata.
        Its unqualified twin is ``regress mpg weight``'s, so the two
        answers the comparison tells apart are both held."""
        auto = pd.DataFrame({"mpg": np.asarray(_AUTO_MPG, dtype=float),
                             "weight": np.asarray(_AUTO_WEIGHT, dtype=float),
                             "foreign": np.asarray(_AUTO_FOREIGN, dtype=float)})
        truth = _qualified_truth()
        plot = {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}
        for tag, extra, key in (("q", {"if_expr": "foreign==1"}, "foreign1"),
                                ("a", {}, "all")):
            reg = truth[key]["regress"]
            x, y = _one_line(_rendered(tmp_path, [dict(plot, **extra)], auto,
                                       mode, tag))
            slope = (y[-1] - y[0]) / (x[-1] - x[0])
            intercept = y[0] - slope * x[0]
            assert (x[0], x[-1]) == (reg["x_min"], reg["x_max"]), (key, x)
            np.testing.assert_allclose(slope, reg["slope"], rtol=1e-9,
                                       err_msg=key)
            np.testing.assert_allclose(intercept, reg["intercept"],
                                       rtol=1e-9, err_msg=key)
            np.testing.assert_allclose(
                [y[0], y[-1]], [reg["fit_at_x_min"], reg["fit_at_x_max"]],
                rtol=1e-9, err_msg=key)
