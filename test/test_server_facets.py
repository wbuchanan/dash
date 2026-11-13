"""``by()`` must work for every plot type in both render modes.

GAPS.md D4.  The generated server app had its own facet dispatch -- two
near-duplicate ``if/elif`` chains, one for the per-group panels and one for
the ``total`` panel -- that handled 18 of the 38 plot types.  The other
twenty fell off the end with no ``else`` and no warning, so ``by(foreign)``
on a ``rarea``, an ``lfitci``, a ``pci`` or a ``function`` served a titled,
axed, EMPTY panel per group.  Measured before this work, all 38 types
differed between the two modes under ``by(foreign)``: the twenty drew
nothing; the eighteen that drew carried no hover tool, a visible Bokeh
default legend at 13px keyed "lfit mpg", ``lpolyci`` and ``fpfitci`` had no
band, and ``fpfit`` drew 200 points where the saved dashboard draws five.

The saved dashboard had a defect of its own at the same spot, in the
opposite direction to D3: it grouped the UNQUALIFIED frame, so
``dash scatter mpg weight if price > 4500, by(foreign)`` faceted every
observation when saved and only the qualified ones when served.

And a regression of WP-09's, found here because facets ride the same path:
once computed layers went through the mapper, the served app stopped
registering them for live recompute, and the raw-source refresh then
"restored" a fitted line's ``x``/``y`` columns by row index -- so after any
filter move a served ``lfit`` was ten points of the OLD line, not a refit.

Every comparison below is against the saved renderer running the same
spec, because "what the saved dashboard does" is the specification.
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import time
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import (ColumnDataSource, HoverTool, LabelSet, Legend,
                          Select)

# WP-50 50-03: the batch tier, run at batch ends (make test-all), ruled 13nov2026 at 50-01-04.
pytestmark = pytest.mark.batch

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json, load_app, memo_build
from by_panel_probe import by_grid, chrome_texts, panel_label
from test_server_layer_defects import ALL_TYPES, plot_for, make_spec, _walk
from test_server_layer_defects import _once_dir

_SEQ = itertools.count()

#: Ten observations, five per group, one with a missing group value when the
#: test asks for it.
_DF = pd.DataFrame({
    "mpg":     [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight":  [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
                2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "rep":     [3.0, 4.0, 3.0, 5.0, 4.0, 3.0, 5.0, 4.0, 3.0, 4.0],
    "price":   [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
                10372.0, 4082.0, 11385.0],
})
_VALUE_LABELS = {"origin": {"0": "Domestic", "1": "Foreign"}}
_LABEL_NAMES = {"foreign": "origin"}


from conftest import render_models  # noqa: E402
from conftest import drawn_renderers  # noqa: E402

# WP-47 MS-15: the marker labels are Text glyph renderers; a reader of the
# LabelSets they were reads them as conftest.MarkerLabels, beside any
# other LabelSet.
from bokeh.models import LabelSet  # noqa: E402
from conftest import MarkerLabels, mlabel_sets  # noqa: E402
_MLS = (LabelSet, MarkerLabels)


def _mls_center(fig):
    return list(fig.center) + mlabel_sets(fig)


def _mls_select(doc):
    return list(doc.select({"type": LabelSet})) + mlabel_sets(doc)


def _mls_all(objs):
    objs = list(objs)
    return objs + mlabel_sets(objs)



def _write(tmp_path, spec, df=_DF):
    tag = next(_SEQ)
    sp = tmp_path / f"fspec_{tag}.json"
    dp = tmp_path / f"fdata_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(df, _VALUE_LABELS, _LABEL_NAMES)))
    return tag, str(sp), str(dp)


def standalone(tmp_path, spec, df=_DF, dataset=None):
    """``{figure_key: figure}`` from the saved-dashboard renderer, and its
    warnings.  *dataset*, when given, is the frame the mapper treats as
    Stata's data in memory (GlyphMapper.dataset) in place of *df*."""
    _, sp, dp = _write(tmp_path, spec, df)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        if dataset is not None:
            r.mapper.dataset = dataset
        render_models(r)
    return dict(r.figures), [str(w.message) for w in caught]


def served(tmp_path, spec, df=_DF):
    """``(figures_in_document_order, document, warnings)`` from the app.

    The import is outside the warning capture: a generated app calls
    ``make_document(curdoc())`` at import time, and counting its warnings
    twice would misreport them.
    """
    tag, sp, dp = _write(tmp_path, spec, df)
    ap = tmp_path / f"fapp_{tag}.py"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(str(ap))
        mod = load_app(str(ap), f"_wp11_{tag}", draw=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    figs = [m for m in _walk(doc) if type(m).__name__ == "figure"]
    return figs, doc, [str(w.message) for w in caught]


def app_source(tmp_path, spec, df=_DF):
    tag, sp, dp = _write(tmp_path, spec, df)
    ap = tmp_path / f"fsrc_{tag}.py"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(str(ap))
    return ap.read_text()


# ---------------------------------------------------------------------------
# Profiles: everything a panel shows that has drifted before
# ---------------------------------------------------------------------------

def _label_of(item):
    lab = item.label
    if isinstance(lab, dict):
        return lab.get("value", lab)
    return getattr(lab, "value", str(lab))


def panel_profile(fig):
    rows = []
    for r in drawn_renderers(fig):
        src = getattr(r, "data_source", None)
        if src is None:
            continue
        data = dict(src.data)
        first = next(iter(data), None)
        n = len(data[first]) if first else 0
        view = getattr(r, "view", None)
        filt = getattr(view, "filter", None) if view is not None else None
        idx = getattr(filt, "indices", None) if filt is not None else None
        if idx is None and filt is not None:
            bools = getattr(filt, "booleans", None)
            if bools is not None:
                idx = [i for i, b in enumerate(bools) if b]
        rows.append(len(idx) if idx is not None else n)
    f = fig
    return {
        # Flipped (WP-30 P1.15a): the panel's title held its label; twoway
        # draws the label as a row of its own (by_panel_probe).
        "title": panel_label(f),
        "glyphs": [type(r.glyph).__name__ for r in drawn_renderers(f)
                   if getattr(r, "glyph", None) is not None],
        "rows": rows,
        "hover": sorted(json.dumps(list(t.tooltips), default=str)
                        for t in f.tools
                        if isinstance(t, HoverTool) and t.tooltips),
        "labels": sorted(r.text for r in
                         _mls_center(f) + list(f.above) + list(f.below) +
                         list(f.left) + list(f.right)
                         if isinstance(r, _MLS)),
        "legend": [([_label_of(i) for i in lg.items],
                    lg.label_text_font_size, lg.visible)
                   for lg in list(f.center) + list(f.above) +
                   list(f.below) + list(f.right)
                   if isinstance(lg, Legend)],
    }


def profiles_std(tmp_path, spec, df=_DF):
    figs, _ = standalone(tmp_path, spec, df)
    return [panel_profile(figs[k]) for k in figs]


def profiles_srv(tmp_path, spec, df=_DF):
    figs, _, _ = served(tmp_path, spec, df)
    return [panel_profile(f) for f in figs]


def by_spec(ptype, by="foreign", options=None, **graph_extra):
    go = {"by": by}
    go.update(graph_extra)
    return make_spec([plot_for(ptype, options)], None, go)


# ===========================================================================
# AC-11.1 -- every plot type under by(), model for model
# ===========================================================================

#: The plot types the by() sweep compares served as well as saved (WP-30
#: test performance E), one per family: point, line, area/range, bar,
#: fit/smooth, pc.  Every type is still drawn saved (test_every_panel_draws);
#: the served app facets through the same code, test_mode_parity's corpus
#: has 23 by() entries, and the classes below compare by() in both modes.
_SERVED_TYPES = ("scatter", "line", "rarea", "bar", "lfitci", "pccapsym")


@memo_build()
def _standalone_once(spec):
    """``standalone`` kept per spec, for the sweep checks that only read it
    (WP-50 50-03: test_the_panels_agree and test_every_panel_draws drew
    each type's by() page twice)."""
    return standalone(_once_dir(), spec)


@memo_build()
def _served_once(spec):
    """``served`` kept per spec, as ``_standalone_once``."""
    return served(_once_dir(), spec)


#: The sweep checks that read _standalone_once/_served_once share one
#: worker per plot type, so each type's by() page is built once a mode.
_ONCE_TESTS = frozenset(["test_the_panels_agree", "test_every_panel_draws"])


def xdist_group_of(item):
    if item.name.split("[")[0] in _ONCE_TESTS:
        return "sf:" + str(item.callspec.params.get("ptype"))
    return None


class TestEveryTypeFacetsTheSameWayInBothModes:
    """The sweep GAPS.md D4 should have been: every type, not 18 -- saved
    for every type, compared with the served app for ``_SERVED_TYPES``."""

    @pytest.mark.parametrize("ptype", [t for t in ALL_TYPES
                                       if t in _SERVED_TYPES])
    def test_the_panels_agree(self, ptype):
        spec = by_spec(ptype)
        figs, _ = _standalone_once(spec)
        std = [panel_profile(figs[k]) for k in figs]
        srv = [panel_profile(f) for f in _served_once(spec)[0]]
        assert std == srv, (
            "%s under by(foreign): saved panels\n  %s\nserved panels\n  %s"
            % (ptype, std, srv)
        )

    @pytest.mark.parametrize("ptype,mode", [
        *[(t, "saved") for t in ALL_TYPES],
        *[(t, "served") for t in ALL_TYPES if t in _SERVED_TYPES]])
    def test_every_panel_draws(self, ptype, mode):
        """Stated positively: no panel is an empty plot region -- saved for
        every type, served for ``_SERVED_TYPES``."""
        if mode == "saved":
            figs, warns = _standalone_once(by_spec(ptype))
            figs = list(figs.values())
        else:
            figs, _, warns = _served_once(by_spec(ptype))
        assert len(figs) == 2, "by(foreign) should give two panels"
        for f in figs:
            assert any(getattr(r, "glyph", None) is not None
                       for r in drawn_renderers(f)), (
                "%s: %s panel %r has no glyph" % (ptype, mode, f.title.text))
        assert not [w for w in warns if "no glyph mapper" in w], warns

    def test_the_no_glyph_mapper_needle_is_live(self, tmp_path):
        """Positive control for the absence check above: an unknown plot
        type must actually emit "no glyph mapper", or that check could never
        fire (measured 24sep2026 -- the phrase is dash_render.py's own)."""
        spec = by_spec("scatter")
        spec["graphs"][0]["plots"][0]["type"] = "notaplottype"
        _, _, warns = served(tmp_path, spec)
        assert [w for w in warns if "no glyph mapper" in w], warns

    @pytest.mark.parametrize("ptype", ["scatter", "lfitci", "rarea", "pci",
                                       "function", "histogram", "pcspike",
                                       "rscatter"])
    def test_the_total_panel_agrees_too(self, tmp_path, ptype):
        spec = by_spec(ptype, by="foreign, total")
        std = profiles_std(tmp_path, spec)
        srv = profiles_srv(tmp_path, spec)
        assert std == srv, "%s: saved %s, served %s" % (ptype, std, srv)
        # by(foreign, total) draws three panels -- the two levels then the
        # pooled Total.  Checking only that the LAST title is "Total" passed
        # a run that dropped a level panel; pin the whole sequence.
        assert [p["title"] for p in srv] == ["Domestic", "Foreign", "Total"], (
            [p["title"] for p in srv])

    def test_two_by_variables_agree(self, tmp_path):
        spec = by_spec("scatter", by="foreign rep")
        assert profiles_std(tmp_path, spec) == profiles_srv(tmp_path, spec)

    def test_the_missing_panel_agrees(self, tmp_path):
        df = _DF.copy()
        df.loc[9, "foreign"] = float("nan")
        spec = by_spec("scatter", by="foreign, missing")
        std = profiles_std(tmp_path, spec, df)
        srv = profiles_srv(tmp_path, spec, df)
        assert std == srv
        # Flipped (WP-30 P1.15a): "Missing" was wrong; twoway writes
        # "(missing)".
        assert [p["title"] for p in srv] == ["Domestic", "Foreign",
                                             "(missing)"]

    def test_a_layered_graph_agrees(self, tmp_path):
        spec = make_spec([plot_for("scatter"), plot_for("lfit")], None,
                         {"by": "foreign"})
        assert profiles_std(tmp_path, spec) == profiles_srv(tmp_path, spec)

    def test_marker_labels_and_hover_reach_every_panel(self, tmp_path):
        spec = make_spec([plot_for("scatter", {"mlabel": "rep"})], None,
                         {"by": "foreign", "hover": "price"})
        std = profiles_std(tmp_path, spec)
        srv = profiles_srv(tmp_path, spec)
        assert std == srv
        for p in srv:
            # A numeric label is drawn from the column derived beside the
            # variable's (test_marker_label_parity.py): "." for a missing
            # value, and a column a served filter's redraw keeps.
            # G1 (WP-28): the marker-label column is named under the
            # __dash prefix.
            assert p["labels"] == [dr._DASH_MLABEL_PREFIX + "rep"], p
            assert any("price" in h for h in p["hover"]), p

    def test_a_linked_faceted_graph_agrees(self, tmp_path):
        spec = make_spec([plot_for("scatter")], {"link": "_all",
                                                 "registry": "g1 g2"},
                         {"by": "foreign"})
        spec["graphs"].append({
            "name": "g2", "graph_options": {"name": "g2"}, "options": {},
            "plots": [{"type": "scatter", "yvar": "price", "xvar": "weight",
                       "options": {}}]})
        std = profiles_std(tmp_path, spec)
        srv = profiles_srv(tmp_path, spec)
        assert std == srv, "saved %s\nserved %s" % (std, srv)

    def test_a_by_variable_that_does_not_exist_leaves_one_figure(
            self, tmp_path):
        spec = by_spec("scatter", by="nosuchvar")
        assert len(profiles_srv(tmp_path, spec)) == \
               len(profiles_std(tmp_path, spec)) == 1


# ===========================================================================
# The saved dashboard's own facet defect: it grouped the unqualified frame
# ===========================================================================

class TestAFacetedGraphHonoursItsQualifier:
    """``if price > 4500, by(foreign)`` must facet the qualified rows.

    Measured before the fix, with the ten-row frame above: the saved
    dashboard faceted 5 + 5 observations, the served one 2 + 4.  Stata's
    ``twoway scatter mpg weight if price > 4500, by(foreign)`` draws the
    six that qualify.  ``_expand_by_groups`` was handed ``self.df``.
    """

    def _rows(self, profiles):
        return [sum(p["rows"]) for p in profiles]

    def test_a_top_level_qualifier_is_applied_when_saved(self, tmp_path):
        spec = by_spec("scatter")
        spec["graphs"][0]["if_expr"] = "price > 4500"
        assert self._rows(profiles_std(tmp_path, spec)) == [2, 4]

    def test_both_modes_facet_the_same_rows(self, tmp_path):
        spec = by_spec("scatter")
        spec["graphs"][0]["if_expr"] = "price > 4500"
        assert profiles_std(tmp_path, spec) == profiles_srv(tmp_path, spec)

    def test_an_in_range_is_applied_before_grouping(self, tmp_path):
        spec = by_spec("scatter")
        spec["graphs"][0]["in_expr"] = "1/4"
        std = profiles_std(tmp_path, spec)
        assert self._rows(std) == [2, 2]
        assert std == profiles_srv(tmp_path, spec)

    def test_the_total_panel_is_the_qualified_total(self, tmp_path):
        spec = by_spec("scatter", by="foreign, total")
        spec["graphs"][0]["if_expr"] = "price > 4500"
        std = profiles_std(tmp_path, spec)
        assert self._rows(std) == [2, 4, 6]
        assert std == profiles_srv(tmp_path, spec)

    def test_a_linked_faceted_graph_honours_it_too(self, tmp_path):
        spec = make_spec([plot_for("scatter")], {"link": "_all",
                                                 "registry": "g1"},
                         {"by": "foreign"})
        spec["graphs"][0]["if_expr"] = "price > 4500"
        std = profiles_std(tmp_path, spec)
        assert self._rows(std) == [2, 4]
        assert std == profiles_srv(tmp_path, spec)


# ===========================================================================
# WP-09's regression: a served computed layer must recompute on a filter move
# ===========================================================================

class TestAServedComputedLayerRecomputesWhenAFilterMoves:
    """After a filter move, a served layer equals a saved one built from the
    filtered rows.

    The live recompute is the ONE difference the parity guard allows:
    ``test_mode_parity.ALLOWED`` says the server "recomputes histogram bins,
    fitted lines and kernel densities from the filtered rows on every widget
    move".  Since WP-09 it did not.  The mapper-built fit source sat in
    ``graph_sources``, and the raw-source refresh, finding ``x``/``y`` are
    not dataframe columns, "restored" them by the filtered ROW INDEX --
    measured, a 100-point ``lfit`` became ten points of the OLD line.  A
    served ``line`` came out in dataset order after the same move, crossing
    itself.

    The specification of "recomputed from the filtered rows" is the saved
    renderer run on those rows, so that is what each case compares against.
    Length is not compared on its own: ``lpoly``, ``fpfit`` and ``mband``
    size their grid from the data, and a refit on half the rows has a
    different, correct, length.
    """

    @staticmethod
    def _derived(figs):
        """``{column: sorted[(length, checksum)]}`` over the figures' sources."""
        out = {}
        seen = set()
        for f in figs:
            for r in drawn_renderers(f):
                src = getattr(r, "data_source", None)
                # Flipped (WP-34 PIC-1): an area's key swatch is one NaN
                # row drawn for the legend, no layer's data.
                if src is None or id(src) in seen \
                        or getattr(r, "_dash_key_glyph", False):
                    continue
                seen.add(id(src))
                for k, v in src.data.items():
                    if k in ("index", dr._ROW_ID_COLUMN) or not len(v):
                        continue
                    try:
                        vals = [float(x) for x in v]
                    except (TypeError, ValueError):
                        continue
                    out.setdefault(k, []).append((len(vals), round(sum(vals), 4)))
        return {k: sorted(v) for k, v in out.items()}

    @staticmethod
    def _fire(doc, value):
        """Move the dropdown to *value* and run its callbacks.

        The callback reads every widget's ``.value`` itself; the ``new``
        argument is not what it filters on.  A probe that only passed the
        argument measured a filter that selected every row, and the
        "recomputed" curve it saw was the same data redrawn.
        """
        sel = [m for m in doc.select({"type": Select})]
        assert sel, "no dropdown filter in the served document"
        w = sel[0]
        old = w.value
        w.value = value
        for cb in w._callbacks.get("value", []):
            cb("value", old, value)

    def _served_after_filter(self, tmp_path, plots, by=None):
        go = {"by": by} if by else None
        spec = make_spec(plots, {"filter": "foreign, type(dropdown)"}, go)
        figs, doc, warns = served(tmp_path, spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._fire(doc, "1.0")
        return self._derived(figs), warns

    def _saved_on_filtered_rows(self, tmp_path, plots, by=None):
        # The filtered rows are drawn, but the data in memory is still the
        # whole frame: a filter is an `if', and two rules read beyond the
        # layer's rows -- lpoly's grid follows _N and lowess's adjust the
        # mean of y over every observation (WP-18).  The served app keeps
        # the whole frame as its dataset after a filter move, so the
        # baseline must too.
        go = {"by": by} if by else None
        spec = make_spec(plots, None, go)
        figs, _ = standalone(tmp_path, spec, _DF[_DF["foreign"] == 1.0],
                             dataset=_DF)
        return self._derived(figs.values())

    @pytest.mark.parametrize("ptype", ["lfit", "qfit", "lfitci", "qfitci",
                                       "lowess", "lpoly", "lpolyci", "fpfit",
                                       "fpfitci", "mspline", "mband",
                                       "kdensity", "histogram", "rscatter",
                                       "pcscatter", "line", "area"])
    def test_the_layer_equals_a_saved_one_on_the_filtered_rows(
            self, tmp_path, ptype):
        plots = [plot_for(ptype)]
        if ptype not in ("histogram", "kdensity", "rscatter", "pcscatter"):
            plots = [plot_for("scatter")] + plots
        served_now, _ = self._served_after_filter(tmp_path, plots)
        want = self._saved_on_filtered_rows(tmp_path, plots)
        # This skipped when lowess (statsmodels) or mspline (scipy) came
        # out empty for want of an optional package.  Since WP-18 neither
        # layer needs one, so an empty served layer is a failure here.
        assert any(v for v in served_now.values()), (
            "%s drew nothing to compare after the filter" % ptype)
        assert served_now == want, (
            "%s after filtering to foreign==1:\n  served %s\n  saved  %s"
            % (ptype, served_now, want)
        )

    def test_a_faceted_curve_is_recomputed_per_panel(self, tmp_path):
        """Facets ride the same registration; every panel's fit must move.

        qfit, not lfit: the foreign cars leave rep 3 and rep 5 one car
        each, and a fresh render of those rows leaves out lfit's panel of
        one, as twoway does (_dash_by_panel_dropped, BUGS.md S3 batch),
        where a filter move keeps the panels the build drew.  qfit draws a
        panel of one with regress's note, so every panel is compared."""
        plots = [plot_for("scatter"), plot_for("qfit")]
        served_now, _ = self._served_after_filter(tmp_path, plots, by="rep")
        want = self._saved_on_filtered_rows(tmp_path, plots, by="rep")
        assert served_now == want, (
            "served %s\nsaved  %s" % (served_now, want))

    def test_a_histogram_is_rebinned(self, tmp_path):
        """Stated on its own: the bars move when the rows do."""
        plots = [plot_for("histogram")]
        spec = make_spec(plots, {"filter": "foreign, type(dropdown)"})
        figs, doc, _ = served(tmp_path, spec)
        before = self._derived(figs)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._fire(doc, "1.0")
        after = self._derived(figs)
        assert after != before, "the served histogram kept its bars: %s" % before
        assert after == self._saved_on_filtered_rows(tmp_path, plots)

    def test_a_qualified_layer_stays_qualified_after_a_filter_move(
            self, tmp_path):
        """The redraw applies the graph's if() and the layer's own."""
        plots = [plot_for("scatter"), plot_for("lfit", if_expr="price > 4500")]
        served_now, _ = self._served_after_filter(tmp_path, plots)
        go = None
        spec = make_spec(plots, None, go)
        figs, _ = standalone(tmp_path, spec, _DF[_DF["foreign"] == 1.0])
        assert served_now == self._derived(figs.values())


# ===========================================================================
# AC-11.2 -- a by() sub-option dash does not implement is named
# ===========================================================================

class TestAnUnimplementedBySuboptionIsNamed:
    """``_parse_by_raw`` matched cols(), total and missing and discarded the
    rest of Stata's by_option grammar without a word.

    Asked of ``_dash_parse_by``, the parser both modes run, which names the
    rest.  These called DashRenderer._parse_by_raw, a test-only delegate of
    it (dropping the list of unimplemented sub-options) that WP-26 deleted
    (24sep2026)."""

    def _warnings_for(self, by_raw):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_parse_by(by_raw)
        return [str(w.message) for w in caught if "by()" in str(w.message)]

    # Flipped (WP-30 P1.15b): rows(), compact, holes(), iscale() and
    # colfirst were the examples; they are drawn now (by_grid_truth.json),
    # so the still unimplemented subtitleformat() and shrink words are.
    # Flipped (WP-31 D10): subtitleformat() is drawn and ishrink/noishrink
    # change nothing twoway draws (by_remainder_truth.json), so shrink,
    # overallshrink and the bystyle stata7 are the words still named.
    # Flipped (WP-31 D10b): shrink and overallshrink are drawn
    # (_dash_by_shrink_factor), so the bystyles econ and stata7 are.
    @pytest.mark.parametrize("by_raw,names", [
        ("foreign, style(econ)", ["style(econ)"]),
        ("foreign, style(stata7)", ["style(stata7)"]),
        # Flipped (WP-41 BY-7): bgcolor() is taken in silence now.
        # Flipped (WP-49 basic:PT-12): spacers(ring(2)) is taken in silence,
        # as twoway draws the same picture with spacers() and prints nothing (noted_option_truth.json sub_probes by(foreign, spacers(ring(2)))).  style(econ) is named by this direct parse, as it was at
        # the WP-49 base (dash.ado writes econ as its options before the
        # renderer parses by(), _dash_bystyle_route; twoway prints nothing
        # for it, bygraphstyle-econ.style being shipped).
        ("foreign, style(econ) spacers(ring(2))", ["style(econ)"]),
        ("foreign, style(stata7) shrink", ["style(stata7)"]),
        # Flipped (WP-30 P1.15a): by()'s title() is drawn now, as twoway
        # draws it.
        ("foreign, title(\"By origin\") style(econ)", ["style(econ)"]),
        # Flipped (WP-29 P0.2): norescale is twoway's default and is
        # honoured, so only noixlabel is named.  Flipped (WP-30 P1.15c):
        # noixlabel is drawn too now (by_chrome_truth.json).
        ("foreign, norescale noixlabel style(econ)", ["style(econ)"]),
        ("foreign, cols(2) total style(econ)", ["style(econ)"]),
    ])
    def test_each_unimplemented_sub_option_is_named(self, by_raw, names):
        got = self._warnings_for(by_raw)
        assert len(got) == 1, got
        for n in names:
            assert n in got[0], "%r is not named in %r" % (n, got[0])

    @pytest.mark.parametrize("by_raw", [
        "foreign", "foreign, cols(2)", "foreign, total", "foreign, missing",
        "foreign rep, cols(1) total missing", "foreign, c(2) miss",
    ])
    def test_the_implemented_sub_options_are_not_named(self, by_raw):
        assert self._warnings_for(by_raw) == []

    def test_the_warning_does_not_name_the_supported_ones_beside_them(self):
        # Flipped (WP-30 P1.15b): rows(3) is drawn now.  Flipped (WP-31
        # D10b): shrink is drawn; style(econ) is not.
        got = self._warnings_for("foreign, cols(2) style(econ)")
        assert len(got) == 1 and "econ" in got[0] and "cols" not in got[0]

    def test_the_parsed_values_are_unchanged(self):
        assert dr._dash_parse_by("foreign, cols(2) rows(3) total")[:4] \
               == ("foreign", 2, True, False)

    def test_the_served_app_warns_the_same_way(self, tmp_path):
        """Named when the app is BUILT, where `dash build, server' shows it
        in the Stata log, and not again when a session opens (WP-23: the
        note came only from a session, whose output the Stata user never
        sees -- test_help_claims_5.cscript HC5-08)."""
        # Flipped (WP-30 P1.15b): rows(2) compact are drawn now.  Flipped
        # (WP-31 D10): subtitleformat() is drawn; overallshrink is not.
        # Flipped (WP-31 D10b): shrink is drawn; the bystyles are not.
        # Flipped (WP-41 BY-7): bgcolor() is taken in silence now;
        # spacers(ring(2)) is still ignored.
        spec = by_spec("scatter", by="foreign, style(econ) spacers(ring(2))")
        tag, sp, dp = _write(tmp_path, spec, _DF)
        with warnings.catch_warnings(record=True) as built:
            warnings.simplefilter("always")
            dr.ServerAppBuilder(sp, dp).build(str(tmp_path / f"b_{tag}.py"))
        # Flipped (WP-31 D10c): style(econ) is drawn as its options and
        # named in its own line (its label margin); spacers(ring(2)) is still
        # ignored -- each once, at build time.
        # Flipped again (WP-31 D10c follow-up): econ's label margin is
        # drawn too, so style(econ) is silent.
        msgs = [str(w.message) for w in built if "by()" in str(w.message)]
        assert len([m for m in msgs if "style(econ)" in m]) == 0, msgs
        # Flipped (WP-49 basic:PT-12): spacers(ring(2)) is taken in silence
        # (twoway draws the same picture with spacers() and prints nothing (noted_option_truth.json sub_probes by(foreign, spacers(ring(2))))), so it is not named at build time either; style(foo), whose
        # twoway note is the bygraphstyle one (lt25 by_style_foo), is named
        # once at build and not again in a session.
        assert len([m for m in msgs if "spacers(ring(2))" in m]) == 0, msgs
        _, _, warns = served(tmp_path, spec)
        assert not [w for w in warns if "by()" in w and "econ" in w], warns
        spec2 = by_spec("scatter", by="foreign, style(foo)")
        tag2, sp2, dp2 = _write(tmp_path, spec2, _DF)
        with warnings.catch_warnings(record=True) as built2:
            warnings.simplefilter("always")
            dr.ServerAppBuilder(sp2, dp2).build(str(tmp_path / f"b2_{tag2}.py"))
        foo = ("dash: named style foo not found in class bygraphstyle, "
               "default attributes used")
        assert [str(w.message) for w in built2].count(foo) == 1, \
            [str(w.message) for w in built2]

    def test_an_unsafe_by_string_still_facets_nothing(self, tmp_path):
        spec = by_spec("scatter", by='__import__("os")')
        assert len(profiles_srv(tmp_path, spec)) == \
               len(profiles_std(tmp_path, spec)) == 1


def _by_note(msgs):
    return [m for m in msgs if "by() variable list" in m]


def _built_warnings(tmp_path, spec):
    """The warnings ServerAppBuilder gives while it builds the app -- where
    `dash build, server' shows them in the Stata log."""
    tag, sp, dp = _write(tmp_path, spec, _DF)
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(str(tmp_path / f"bw_{tag}.py"))
    return [str(w.message) for w in built]


class TestAByTextHoldingMacroCharactersFacets:
    """BUGS.md "A by() whose text holds a backtick, a dollar sign or a
    backslash draws no panels, without a word".  _dash_parse_by held the
    WHOLE by() string to the injection pattern _DASH_UNSAFE_BY, so a
    title() or note() inside by() holding a backtick -- which every
    compound quote does -- a dollar sign, a backslash or a semicolon
    returned an empty variable list, and both modes drew one panel of every
    row and said nothing.  Measured 24sep2026 with the console binary:
    twoway scatter mpg weight, by(foreign, title(`"'90s bc"')), and the
    same with title("Cost in \\$US") and title("a\\b c"), each draw the two
    panels Domestic and Foreign.  Only the variable list is held to the
    pattern now; the sub-options are text.  Flipped (WP-30 P1.15a): the
    by() title was named as not implemented; twoway draws by()'s text once
    over the panels, so it is drawn, as typed, and not named."""

    _BT, _AP = "`", "'"

    @pytest.mark.parametrize("by_raw", [
        "foreign, title(`\"'90s bc\"')",
        'foreign, title("Cost in $US")',
        'foreign, title("a\\b c")',
        "foreign, note(\"tick `x\")",
        "foreign, title(`\"a `\"b\"' c\"')",
        'foreign, title("x; y") subtitle("__import__ eval exec open")',
    ], ids=["compound-quote", "dollar", "backslash", "backtick",
            "nested-compound", "semicolon-and-python-words"])
    def test_both_modes_draw_the_two_panels(self, tmp_path, by_raw):
        spec = by_spec("scatter", by=by_raw)
        figs, msgs = standalone(tmp_path, spec)
        srv = profiles_srv(tmp_path, spec)
        assert len(figs) == len(srv) == 2, (len(figs), len(srv))
        assert sorted(p["title"] for p in srv) == \
               sorted(panel_label(f) for f in figs.values()) == \
               ["Domestic", "Foreign"]
        assert not _by_note(msgs), msgs
        assert not [m for m in msgs if "by() sub-option" in m], msgs
        # The text is drawn in the chrome cells, as the user typed it.
        want = sorted(dr._dash_textbox(v, k)[0] for k, v in
                      dr._dash_by_text_options(by_raw).items() if v)
        cells = next(f for f in figs.values()
                     if getattr(f, "_dash_by_chrome", None))._dash_by_chrome
        got = sum((chrome_texts(c) for c in cells.values() if c), [])
        assert all(w in got for w in want), (want, got)

    def test_the_parse_keeps_the_implemented_sub_options(self):
        got = dr._dash_parse_by(
            "foreign rep, title(`\"$x `y' \\z\"') cols(1) total missing",
            warn=False)
        assert got[:4] == ("foreign rep", 1, True, True)

    @pytest.mark.parametrize("by_raw", [
        '__import__("os")',
        "foreign; import os",
        "for$eign",
        "foreign`x'",
        "foreign\\x",
        "eval(foreign)",
        'foreign "x"',
        "foreign-rep, title(x)",
    ])
    def test_a_variable_list_that_is_not_names_is_refused_with_a_note(
            self, tmp_path, by_raw):
        """What is refused is said, in both modes -- saved at render, served
        when the app is built -- and draws one panel, never a wrong one."""
        spec = by_spec("scatter", by=by_raw)
        figs, msgs = standalone(tmp_path, spec)
        assert len(figs) == 1
        assert len(_by_note(msgs)) == 1, msgs
        assert len(profiles_srv(tmp_path, spec)) == 1
        assert len(_by_note(_built_warnings(tmp_path, spec))) == 1
        # The note does not echo the refused text.
        assert by_raw not in _by_note(msgs)[0]


class TestAByTextAdversarial:
    """CLAUDE.md rule 18 for the by() text now let through: markup and code
    in a sub-option are text that runs nowhere, a variable list cannot ride
    in behind one, and a long text is read in bounded time."""

    def test_markup_and_code_in_a_title_run_nowhere(self, tmp_path):
        sentinel = tmp_path / "executed"
        payload = ("</script><script>alert(1)</script> <img src=x "
                   "onerror=alert(1)> __import__('os').system('touch %s'); "
                   "`=2+2' $HOME \\n" % sentinel)
        spec = by_spec("scatter", by='foreign, title(`"%s"\')' % payload)
        _, sp, dp = _write(tmp_path, spec, _DF)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            page = r.render()
        assert len(r.figures) == 2
        assert len(profiles_srv(tmp_path, spec)) == 2
        assert "<script>alert" not in page and "<img src=x" not in page
        assert not sentinel.exists()

    def test_a_sub_option_cannot_smuggle_a_variable_list(self):
        """Bypass: the variable list ends at the first comma, and a comma or
        a variable name inside a sub-option's string is text."""
        got = dr._dash_parse_by(
            'foreign, title("x", rep) note(`"a, "b", rep"\')', warn=False)
        assert got[0] == "foreign"

    def test_a_long_text_is_read_in_bounded_time(self, tmp_path):
        text = "`$\\; '( \"x\" " * 20000
        assert "\"'" not in text and "`\"" not in text
        by_raw = "foreign, title(`\"" + text + "\"') cols(1)"
        t0 = time.monotonic()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            got = dr._dash_parse_by(by_raw)
        assert time.monotonic() - t0 < 5
        assert got[:2] == ("foreign", 1)
        spec = by_spec("scatter", by=by_raw)
        t0 = time.monotonic()
        figs, _ = standalone(tmp_path, spec)
        assert len(figs) == 2
        assert time.monotonic() - t0 < 60


# ===========================================================================
# TR-11.1 -- one dispatch
# ===========================================================================

class TestTheGeneratedAppHasOneDispatch:
    def test_no_facet_chain_remains(self, tmp_path):
        src = app_source(tmp_path, by_spec("scatter"))
        # Positive control: the app must carry the ONE shared dispatch that
        # replaced the hand-written facet branches, or the absence of the
        # old markers proves only that the app is empty.
        assert "_dash_figure_for(" in src
        assert src.count("for pi, plot in enumerate(plots):") == 1
        for marker in ("_fac_fig.scatter(", "_tot_fig.scatter(",
                       "size=6, color=color", "width=0.8, color=color",
                       "legend_label=f'lfit", "_fac_gdf", "_tot_src"):
            assert marker not in src, (
                "the generated app still carries a hand-written facet "
                "branch: %r" % marker)

    def test_the_plot_loop_is_written_once(self, tmp_path):
        """A structural guard over the app's text, deliberately: ONE plot
        loop, through _dash_figure_for, for a graph and each of its panels.
        A second, equal loop draws the same panels, so no drawing shows it
        until the two drift; the drawing is this module's other classes."""
        src = app_source(tmp_path, by_spec("scatter"))
        assert src.count("for pi, plot in enumerate(plots):") == 1, (
            "more than one plot loop in the generated app")
        assert "_dash_figure_for(" in src

    def test_the_facet_panels_use_the_parsed_column_count(self, tmp_path):
        """``by(foreign, cols(1))`` -- documented, and inert in server mode:
        the grid read a ``by_cols`` graph option nothing writes and never
        the ``cols()`` it had just parsed."""
        from bokeh.models import GridPlot
        spec = by_spec("scatter", by="foreign, cols(1)")
        _, doc, _ = served(tmp_path, spec)
        # Flipped (WP-30 P1.15a): the sub-grid holds the overall text's
        # chrome cells beside its panels; the panels are read through
        # by_panel_probe.by_grid.
        (root,) = [x for x in doc.roots
                   if any(isinstance(m, GridPlot) for m in x.references())]
        panels = by_grid(root)[0]
        assert panels, "no facet sub-grid found"
        cols = max(c for _, c, _ in panels) + 1
        assert cols == 1, "cols(1) gave a %d-column facet grid" % cols
