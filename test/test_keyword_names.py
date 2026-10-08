"""A keyword is not a graph's name, and a graph's name is not a keyword.

Measured 23sep2026 at 9f48cf7, each in both render modes and through Stata:

1. The saved renderer read a KPI's ``update`` value -- filter, brush or
   both, the only values dash.ado writes -- as the name of a by() graph,
   and drew one card per panel when a graph had that name.  A by() graph a
   user names ``filter`` turned every default KPI into cards ``k1__by__0``
   and ``k1__by__1`` on the saved page (19.60 and 23.40 on the test data)
   where the served app, which builds no per-panel cards, drew one card
   ``k1`` (21.50).  The filter callback carried those cards with no
   variable, so they never recomputed, and over a LINKED by() graph they
   showed the placeholder: linked panels have no source of their own.
   dash.ado never offered a way to ask for such cards -- update() took only
   filter, brush or both before they were written.  A KPI is one card now,
   in both modes, and update() names a mode, never a graph.
2a. ``link(_all g2)``: the saved renderer linked every graph whenever _all
   was among the names, the served app only when _all was the whole value:
   with graphs g1 g2 g3 all three were linked saved and none served.
   dash.ado refused ``link(_all g2)`` -- "link() name '_all' not found in
   registry" -- but registered a graph named ``_all``, after which it built:
   all three linked saved, ``_all`` and g2 served.
2b. ``layout(bsales:1,1 g2:1,2)``, a placement whose first name is a graph
   ``bsales``, was refused by dash.ado and drawn as layout(bs) by the
   renderer: every reader took a value starting with ``bs`` for the
   Bootstrap form.  ``layout(g2:1,1 bsales:1,2)`` was drawn as written.
2c. ``filter(price, exclude(g1))`` did not exclude an unlinked by() graph
   g1: its panels' sources are keyed ``g1__by__0``, ``g1__by__1``, and both
   modes matched exclude() against those keys alone -- the served panels
   went from 5 and 5 rows to 3 and 1 on a price move, as with no exclude().
"""
import itertools
import json
import os
import re
import sys
import warnings

import pytest
from bokeh.document import Document
from bokeh.models import Div, GridBox, GridPlot, RangeSlider
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr
from dash_render import DashRenderer
from test_adversarial_matrix import _SCATTER, _load_app, _write_inputs

_SEQ = itertools.count()
_FIGURE = type(figure())

#: mean(mpg) over the test data's ten rows, as a card shows it.
_MEAN_MPG = "21.50"


# ---------------------------------------------------------------------------
# Specs, the saved page and the served session
# ---------------------------------------------------------------------------

def _graph(name, plots=None, **go):
    opts = {"name": name, "title": name}
    opts.update(go)
    return {"plots": plots or [dict(_SCATTER)], "graph_options": opts,
            "if_expr": "", "in_expr": ""}


def _kpi(name, **kw):
    k = {"name": name, "stat": "mean", "var": "mpg", "fmt": "%9.2f",
         "title": name, "subtitle": "", "color": "", "bgcolor": "",
         "update": "filter", "if_expr": "", "in_expr": ""}
    k.update(kw)
    return k


def _spec(graphs, kpis=(), **bo):
    names = ([g["graph_options"]["name"] for g in graphs]
             + [k["name"] for k in kpis])
    build = {"layout": "auto", "link": "", "theme": "", "title": "",
             "subtitle": "", "tabs": "", "filter_position": "top",
             "filter": "", "registry": " ".join(dict.fromkeys(names))}
    build.update(bo)
    return {"graphs": graphs, "kpis": list(kpis), "build_options": build}


def _saved(tmp_path, spec):
    """(renderer, page, warnings) from the saved-dashboard renderer."""
    sp, dp = _write_inputs(tmp_path, spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = DashRenderer(sp, dp)
        page = r.render()
    return r, page, [str(w.message) for w in caught]


def _served(tmp_path, spec):
    """(document, build warnings) from one served session."""
    sp, dp = _write_inputs(tmp_path, spec)
    app = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(app)
    with open(app, encoding="utf-8") as fh:
        ns = _load_app(fh.read(), "keyword_%d" % next(_SEQ))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        doc = Document()
        ns["make_document"](doc)
    return doc, [str(w.message) for w in built]


def _cards(models):
    """``[(card name, value shown)]`` of the KPI cards among *models*."""
    out = []
    for m in models:
        text = getattr(m, "text", "") or ""
        k = re.search(r'id="kpi_val_([^"]+)"[^>]*>([^<]*)<', text)
        if isinstance(m, Div) and k:
            out.append((k.group(1), k.group(2)))
    return sorted(out)


def _linked(figs):
    """The groups of figures that draw from one data source."""
    src = {f.title.text: {id(r.data_source) for r in f.renderers
                          if getattr(r, "data_source", None) is not None}
           for f in figs}
    groups = []
    for name in sorted(src):
        for g in groups:
            if src[name] & src[g[0]]:
                g.append(name)
                break
        else:
            groups.append([name])
    return [g for g in groups if len(g) > 1]


def _callbacks(r):
    return [cb for w in r.filter_widgets
            for cb in (w.js_property_callbacks.get("change:value") or [])]


# ---------------------------------------------------------------------------
# 1. A KPI is one card; update() is a mode
# ---------------------------------------------------------------------------

class TestAKpiIsOneCard:

    @pytest.mark.parametrize("mode", ["filter", "brush", "both"])
    def test_a_by_graph_named_like_the_mode_does_not_split_it(
            self, tmp_path, mode):
        spec = _spec([_graph(mode, by="foreign")], [_kpi("k1", update=mode)])
        r, _, _ = _saved(tmp_path, spec)
        assert _cards(r.kpi_divs.values()) == [("k1", _MEAN_MPG)]
        doc, _ = _served(tmp_path, spec)
        assert _cards(doc.select({"type": Div})) == [("k1", _MEAN_MPG)]

    def test_an_update_naming_a_by_graph_is_still_one_card(self, tmp_path):
        """A spec that did not come through dash.ado, as P6-24's tests
        wrote it: the saved page split the card, the served app did not."""
        spec = _spec([_graph("g1", by="foreign")], [_kpi("k1", update="g1")])
        r, _, _ = _saved(tmp_path, spec)
        assert _cards(r.kpi_divs.values()) == [("k1", _MEAN_MPG)]
        doc, _ = _served(tmp_path, spec)
        assert _cards(doc.select({"type": Div})) == [("k1", _MEAN_MPG)]

    def test_over_a_linked_by_graph_the_card_shows_its_value(self, tmp_path):
        """The per-panel cards over a linked by() graph showed the
        placeholder, a panel of a linked graph having no source."""
        spec = _spec([_graph("g1", by="foreign"), _graph("g2")],
                     [_kpi("k1", update="g1")], link="g1 g2")
        r, _, _ = _saved(tmp_path, spec)
        assert _cards(r.kpi_divs.values()) == [("k1", _MEAN_MPG)]
        doc, _ = _served(tmp_path, spec)
        assert _cards(doc.select({"type": Div})) == [("k1", _MEAN_MPG)]

    def test_the_card_recomputes_when_a_filter_moves(self, tmp_path):
        """Its filter callback carries it with its statistic and variable
        -- the per-panel cards went with no variable and never moved."""
        spec = _spec([_graph("filter", by="foreign")], [_kpi("k1")],
                     filter="price, type(range)")
        r, _, _ = _saved(tmp_path, spec)
        [cb] = _callbacks(r)
        cfg = json.loads(cb.args["kpi_config_json"])
        assert [(c["name"], c["stat"], c["varname"]) for c in cfg] == [
            ("k1", "mean", "mpg")]


# ---------------------------------------------------------------------------
# 2a. link(_all)
# ---------------------------------------------------------------------------

class TestLinkAll:

    @pytest.mark.parametrize("link", ["_all", "_all g2", "g2 _all"])
    def test_all_links_every_graph_in_both_modes(self, tmp_path, link):
        spec = _spec([_graph("g1"), _graph("g2"), _graph("g3")], link=link)
        r, _, _ = _saved(tmp_path, spec)
        assert _linked(r.figures.values()) == [["g1", "g2", "g3"]]
        doc, _ = _served(tmp_path, spec)
        assert _linked(doc.select({"type": _FIGURE})) == [["g1", "g2", "g3"]]

    def test_names_link_those_graphs_only(self, tmp_path):
        spec = _spec([_graph("g1"), _graph("g2"), _graph("g3")],
                     link="g1 g3")
        r, _, _ = _saved(tmp_path, spec)
        assert _linked(r.figures.values()) == [["g1", "g3"]]
        doc, _ = _served(tmp_path, spec)
        assert _linked(doc.select({"type": _FIGURE})) == [["g1", "g3"]]

    def test_a_graph_named_all_is_refused_in_both_modes(self, tmp_path):
        """dash.ado refuses the name (test_registry_collision.cscript);
        a spec that did not come through it has the graph refused aloud,
        and link(_all g2) still means every graph."""
        spec = _spec([_graph("_all"), _graph("g2"), _graph("g3")],
                     link="_all g2")
        r, _, saved = _saved(tmp_path, spec)
        assert sorted(r.figures) == ["g2", "g3"]
        assert _linked(r.figures.values()) == [["g2", "g3"]]
        doc, built = _served(tmp_path, spec)
        assert _linked(doc.select({"type": _FIGURE})) == [["g2", "g3"]]
        for msgs in (saved, built):
            [msg] = [m for m in msgs
                     if m.startswith("dash: graph name '_all'")]
            assert "link(_all)" in msg

    @pytest.mark.parametrize("link, names, want", [
        ("", ["a", "b"], []),
        ("a", ["a", "b"], ["a"]),
        ("_all", ["a", "b", ""], ["a", "b"]),
        ("b _all", ["a", "b"], ["a", "b"]),
        ("a;b", ["a", "b", "c"], ["a", "b"]),
    ])
    def test_one_rule_reads_it(self, link, names, want):
        assert dr._dash_link_names(link, names) == want


# ---------------------------------------------------------------------------
# 2b. A placement naming a graph that starts with bs
# ---------------------------------------------------------------------------

def _saved_cells(r):
    """``[(title, row, col)]`` of the saved page's grid, or None for bs."""
    root = r._last_layout_root
    if root is None:
        return None
    return sorted((c[0].title.text, c[1], c[2])
                  for g in root.select({"type": GridPlot})
                  for c in g.children if isinstance(c[0], _FIGURE))


def _served_cells(doc):
    if list(doc.select({"type": GridBox})):
        return None
    return sorted((c[0].title.text, c[1], c[2])
                  for g in doc.select({"type": GridPlot})
                  for c in g.children if isinstance(c[0], _FIGURE))


class TestAPlacementNamingABsGraph:

    @pytest.mark.parametrize("first", ["bsales", "bs", "BS1"])
    def test_it_is_drawn_as_placed_in_both_modes(self, tmp_path, first):
        spec = _spec([_graph(first), _graph("g2")],
                     layout=f"{first}:1,1 g2:1,2")
        want = [(first, 0, 0), ("g2", 0, 1)]
        r, _, msgs = _saved(tmp_path, spec)
        assert _saved_cells(r) == want
        assert not [m for m in msgs if "layout(" in m]
        doc, built = _served(tmp_path, spec)
        assert _served_cells(doc) == want
        assert not [m for m in built if "layout(" in m]
        # Nor a word under any other spelling: a report on a layout quotes
        # it.  And the needles are live -- the same placement with a name
        # the registry lacks is reported, in both modes, as
        # "dash: layout(<it>): ...", so an emitter that changed its words
        # cannot leave the two checks above looking at nothing.
        placed = f"{first}:1,1"
        assert not [m for m in msgs + built if placed in m], msgs + built
        control = _spec([_graph(first), _graph("g2")],
                        layout=f"{first}:1,1 nosuch:1,2")
        _, _, c_msgs = _saved(tmp_path, control)
        _, c_built = _served(tmp_path, control)
        for got in (c_msgs, c_built):
            said = [m for m in got if "layout(" in m and placed in m]
            assert len(said) == 1, got

    @pytest.mark.parametrize("layout, bs", [
        ("bs", True), ("BS", True), (" bs ", True), ("bs:", True),
        ("bs: g1=6 g2=6", True), ("Bs : g1=12", True), ("bsx", True),
        ("bsales:1,1 g2:1,2", False), ("bs:1,1 g2:1,2", False),
        ("g2:1,1 bsales:1,2", False), ("2 1", False), ("auto", False),
        ("", False),
    ])
    def test_the_bootstrap_form_is_what_reads_as_no_other(self, layout, bs):
        assert dr._dash_is_bs_layout(layout) is bs

    def test_the_renderer_reads_the_placement_without_a_word(self):
        layout, problem = dr._dash_layout_check(
            "bsales:1,1 g2:1,2", {"bsales", "g2"})
        assert (layout, problem) == ("bsales:1,1 g2:1,2", None)


# ---------------------------------------------------------------------------
# 2c. exclude() of a by() graph
# ---------------------------------------------------------------------------

_HIST = {"type": "histogram", "var": "mpg", "options": {}}


def _rows(doc):
    """{figure title: what its renderers draw}: each source's length and
    the sum of its numeric values -- a histogram keeps its bins when the
    rows under them change, so a length alone would not show a filter."""
    out = {}
    for f in doc.select({"type": _FIGURE}):
        seen = []
        for r in f.renderers:
            ds = getattr(r, "data_source", None)
            if ds is None or not ds.data:
                continue
            total = 0.0
            for col, vals in ds.data.items():
                if col == dr._ROW_ID_COLUMN:
                    continue
                for v in vals:
                    try:
                        total += float(v)
                    except (TypeError, ValueError):
                        pass
            seen.append((len(next(iter(ds.data.values()))), round(total, 6)))
        # Flipped (WP-30 P1.15a): a by() panel is keyed by its title and
        # label row; the title alone no longer tells panels apart.
        from by_panel_probe import panel_label
        key = " ".join(t for t in (f.title.text, panel_label(f)) if t)
        out[key] = sorted(seen)
    return dict(sorted(out.items()))


def _move_price(doc, value):
    w = list(doc.select({"type": RangeSlider}))[0]
    old = w.value
    w.value = value
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for attr in ("value", "value_throttled"):
            for cb in w._callbacks.get(attr, []):
                cb(attr, old, value)


class TestExcludeAByGraph:

    @staticmethod
    def _spec(plots, excl):
        return _spec([_graph("g1", plots, by="foreign"), _graph("g2")],
                     filter=f"price, type(range) exclude({excl})")

    @pytest.mark.parametrize("plots", [None, [_HIST]],
                             ids=["scatter", "histogram"])
    def test_the_saved_filter_leaves_its_panels_alone(self, tmp_path, plots):
        r, _, _ = _saved(tmp_path, self._spec(plots, "g1"))
        panel_srcs = {id(r.sources[k]) for k in r.sources
                      if k.startswith("g1__by__")}
        panel_aggs = {id(cds) for k, lst in r.agg_source_registry.items()
                      if k.startswith("g1__by__") for cds, _ in lst}
        [cb] = _callbacks(r)
        filtered = {id(s) for s in cb.args["all_graph_sources"]}
        assert panel_srcs and not (panel_srcs & filtered)
        assert id(r.sources["g2"]) in filtered
        assert not (panel_aggs & {id(s) for s in cb.args["agg_sources"]})
        # A scatter panel has no aggregate, so for it the line above is
        # about nothing; the histogram's two panels each carry one, or it
        # is about nothing there too.
        assert len(panel_aggs) == (2 if plots else 0), len(panel_aggs)
        # The control: exclude(g2) leaves g1 filtered, and the same panels'
        # sources and aggregates ARE in the callback -- so their absence
        # above is exclude(g1)'s doing.
        r2, _, _ = _saved(tmp_path, self._spec(plots, "g2"))
        [cb2] = _callbacks(r2)
        srcs2 = {id(r2.sources[k]) for k in r2.sources
                 if k.startswith("g1__by__")}
        aggs2 = {id(cds) for k, lst in r2.agg_source_registry.items()
                 if k.startswith("g1__by__") for cds, _ in lst}
        assert srcs2 and srcs2 <= {id(s) for s in
                                   cb2.args["all_graph_sources"]}
        assert aggs2 <= {id(s) for s in cb2.args["agg_sources"]}
        assert len(aggs2) == len(panel_aggs)

    @pytest.mark.parametrize("plots", [None, [_HIST]],
                             ids=["scatter", "histogram"])
    def test_the_served_filter_leaves_its_panels_alone(self, tmp_path,
                                                       plots):
        doc, _ = _served(tmp_path, self._spec(plots, "g1"))
        before = _rows(doc)
        _move_price(doc, (3799.0, 4500.0))
        after = _rows(doc)
        g1 = [t for t in before if t.startswith("g1")]
        assert len(g1) == 2
        assert {t: after[t] for t in g1} == {t: before[t] for t in g1}
        # In both cases: g2 is a scatter in each, and a filter that moved
        # nothing leaves g1's panels alone as well.  It was asked of the
        # scatter case only (measured 24sep2026: g2 goes from 10 rows to 4
        # in the histogram case too).
        assert after["g2"] != before["g2"], "the filter moved nothing"

    @pytest.mark.parametrize("key, owner, want", [
        ("g1", {}, True), ("g1__by__0", {"g1__by__0": "g1"}, True),
        ("g2", {"g1__by__0": "g1"}, False), ("g1__by__0", {}, False),
    ])
    def test_one_rule_matches_it(self, key, owner, want):
        assert dr._dash_excluded(key, ["g1"], owner) is want
