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
each entry cross-checked against the serset of the plotted ``.gph``.  It is
NOT consumed here: these tests assert that the qualifier reaches the
computation, which is WP-02, whereas comparing dash's estimator against
Stata's is statistical fidelity and belongs with ``stat_truth.json`` and
``test_statistical_truth.py``.  The fixture is committed so that work has
measured ground truth to start from -- ``test/fixtures/data/auto.csv`` carries
only ``mpg`` and ``weight``, so reproducing the ``foreign==1`` subset needs
the ``lowess_x`` row list the fixture records.
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

from bokeh.models import BooleanFilter, CDSView, ColumnDataSource
from bokeh.plotting import figure

import dash_render as dr
from conftest import make_data_json

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

_NEEDS_STATSMODELS = {"lowess"}


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
                    and not isinstance(vals[0], str)})
    return out


def _skip_if_unavailable(name):
    if name in _NEEDS_STATSMODELS:
        try:
            import statsmodels.api  # noqa: F401
        except Exception as exc:                       # pragma: no cover
            pytest.skip("%s needs statsmodels (%s)" % (name, exc))


@pytest.mark.parametrize("name,kind", _LAYERS, ids=[n for n, _ in _LAYERS])
class TestAQualifierReachesTheComputation:

    def test_the_qualified_result_differs_from_the_unqualified_one(
            self, name, kind):
        """The bug signature: the qualifier used to change nothing."""
        _skip_if_unavailable(name)
        src = _source(_DF)
        allrows = _call(name, kind, src, None)
        qualified = _call(name, kind, src, _mask_view(_DF, _DF.g == 0))
        assert qualified != allrows, (
            "%s ignored its view: the qualified layer is identical to the "
            "all-rows layer" % name
        )

    def test_the_qualified_result_equals_the_prefiltered_one(self, name, kind):
        """Correctness, not merely difference.

        Masking the input must give exactly what the same mapper gives when
        handed a source containing only those rows.
        """
        _skip_if_unavailable(name)
        via_view = _call(name, kind, _source(_DF),
                         _mask_view(_DF, _DF.g == 0))
        via_subset = _call(name, kind, _source(_SUBSET), None)
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
        _skip_if_unavailable(name)
        src = _source(_DF)
        a = _call(name, kind, src, None)
        b = _call(name, kind, _source(_DF), None)
        assert a == b

    def test_an_all_true_mask_matches_no_view(self, name, kind):
        """A view that selects everything is the same as no view."""
        _skip_if_unavailable(name)
        none_view = _call(name, kind, _source(_DF), None)
        all_true = _call(name, kind, _source(_DF),
                         _mask_view(_DF, np.ones(len(_DF), dtype=bool)))
        assert len(none_view) == len(all_true), name
        for got, want in zip(all_true, none_view):
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
        assert tops[0] != tops[1], (
            "the two by() panels drew identical bars; each should describe "
            "its own group"
        )

    def test_linked_by_panels_differ_from_each_other(self, tmp_path):
        tops = _render_by_panels(tmp_path, linked=True)
        assert len(tops) >= 2, tops
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
        renderer.render()
    panels = []
    for fig in renderer.figures.values():
        for rend in fig.renderers:
            src = getattr(rend, "data_source", None)
            if src is not None and "top" in src.data:
                panels.append([round(float(t), 6) for t in src.data["top"]])
    return panels
