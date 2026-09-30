"""A registered name cannot take the place of a piece dash names itself.

dash stores what it generates under names it builds from the user's: a by()
graph g1's panels are ``g1__by__0``, ``g1__by__1``, ... in the figures, a
KPI's per-panel cards the same in the cards, and the saved layout(bs) page
keys its tab strip ``__tabs__`` and its filters ``__fw_0__``, ``__fw_1__``.
dash.ado accepted any Stata name, so a name of one of those forms shared
their namespace.  Measured 23sep2026 at 679050e, with nothing reported in
either mode:

* g1 ``by(foreign)`` beside a plain graph ``g1__by__0``: the plain graph
  took the place of g1's first panel, on the saved page and in the served
  app, under layout(auto), layout(bs) and with tabs().  Through Stata,
  ``dash build`` drew the plain graph and g1's Foreign panel; the Domestic
  panel was gone.
* a KPI k1 with per-panel cards beside a KPI ``k1__by__0``: the second
  replaced k1's first card on the saved page.
* a KPI ``g2__by__0`` beside a graph g2: ``_dash_kpi_keys`` matches by
  prefix, so g2 was laid out as a KPI card under layout(bs), in both modes.
* under layout(bs), a graph ``__tabs__`` replaced the tab strip on the saved
  page -- the tabbed graphs vanished -- and a graph ``__fw_0__`` was
  replaced by the first filter.
* a spec that names two items alike -- two graphs, two KPI cards, or a
  graph and a card -- drew one of them in both modes.

Every name dash generates holds two underscores in a row, so a registered
name may not.  dash.ado refuses one (test_adversarial.cscript P20-32), and
the one pass both modes run on a spec before anything is built from it
(``_dash_cap_spec``) refuses one, and a repeated name, aloud, for a spec
that did not come through dash.ado.
"""
import itertools
import os
import re
import sys
import time
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Div, GridBox, Select, Tabs
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr
from dash_render import DashRenderer
from test_adversarial_matrix import _SCATTER, _load_app, _write_inputs

_SEQ = itertools.count()


# ---------------------------------------------------------------------------
# Specs, the saved page and the served session
# ---------------------------------------------------------------------------

def _graph(name, **go):
    """A scatter titled with its own name unless *go* says otherwise."""
    opts = {"name": name, "title": name}
    opts.update(go)
    return {"plots": [dict(_SCATTER)], "graph_options": opts,
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
             "registry": " ".join(dict.fromkeys(names))}
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
    """(document, build warnings, session warnings) from the served app."""
    sp, dp = _write_inputs(tmp_path, spec)
    app = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(app)
    with open(app, encoding="utf-8") as fh:
        ns = _load_app(fh.read(), "reserved_%d" % next(_SEQ))
    with warnings.catch_warnings(record=True) as session:
        warnings.simplefilter("always")
        doc = Document()
        ns["make_document"](doc)
    return (doc, [str(w.message) for w in built],
            [str(w.message) for w in session])


_FIGURE = type(figure())


def _figures(doc):
    return list(doc.select({"type": _FIGURE}))


def _titles(figs):
    return sorted(f.title.text for f in figs)


def _cards(models):
    """``[(card name, title)]`` of the KPI cards among *models*."""
    out = []
    for m in models:
        text = getattr(m, "text", None) or ""
        k = re.search(r'id="kpi_val_([^"]+)"', text)
        if isinstance(m, Div) and k:
            words = [w for w in re.split(r"<[^>]+>", text) if w.strip()]
            out.append((k.group(1), words[0].strip() if words else ""))
    return sorted(out)


def _refusals(msgs):
    """The renderer's name refusals among *msgs*."""
    return [m for m in msgs
            if re.match(r"dash: (graph|KPI) names? ", m)
            and (" refused: " in m or " already name" in m)]


def _one_refusal(msgs, kind, name):
    """Exactly one refusal, and it names *name* as a *kind* name."""
    got = _refusals(msgs)
    assert len(got) == 1, f"refusals: {got}\n  all warnings: {msgs}"
    assert got[0].startswith(f"dash: {kind} name {name!r}"), got[0]
    return got[0]


# ---------------------------------------------------------------------------
# The collisions, in both modes
# ---------------------------------------------------------------------------

_LAYOUTS = [("auto", ""), ("bs", ""), ("bs", "A: g1"), ("auto", "A: g1")]

#: g1 by(foreign)'s two panels, by title.
#: Titled as twoway writes the values, 0 and 1 (dash wrote 0.0 and 1.0).
_PANELS = ["g1 \u2014 0", "g1 \u2014 1"]


class TestAGraphNamedLikeAPanel:
    """g1 by(foreign) and a plain graph g1__by__0: g1 keeps both panels,
    and the plain graph is refused aloud rather than drawn in the place of
    g1's first one."""

    @staticmethod
    def _spec(layout, tabs):
        return _spec([_graph("g1", by="foreign"), _graph("g1__by__0")],
                     layout=layout, tabs=tabs)

    @pytest.mark.parametrize("layout, tabs", _LAYOUTS)
    def test_the_saved_page(self, tmp_path, layout, tabs):
        r, page, msgs = _saved(tmp_path, self._spec(layout, tabs))
        assert sorted(r.figures) == ["g1__by__0", "g1__by__1"]
        assert _titles(r.figures.values()) == _PANELS
        _one_refusal(msgs, "graph", "g1__by__0")

    @pytest.mark.parametrize("layout, tabs", _LAYOUTS)
    def test_the_served_app(self, tmp_path, layout, tabs):
        doc, built, session = _served(tmp_path, self._spec(layout, tabs))
        assert _titles(_figures(doc)) == _PANELS
        _one_refusal(built, "graph", "g1__by__0")
        # Reported once, when the app is built: not again on each session.
        assert _refusals(session) == []

    def test_the_two_modes_say_the_same(self, tmp_path):
        spec = self._spec("auto", "")
        _, _, saved = _saved(tmp_path, spec)
        _, built, _ = _served(tmp_path, spec)
        assert len(_refusals(saved)) == 1
        assert _refusals(saved) == _refusals(built)


class TestAKpiNamedLikeACard:
    """A KPI k1 whose update() names the by() graph, and a KPI k1__by__0:
    the second is refused aloud.  The saved page drew k1 as a card per
    panel under names of that form, and k1__by__0 replaced the first; k1 is
    one card now (test_keyword_names.py), and the name is refused all the
    same."""

    @staticmethod
    def _spec():
        return _spec([_graph("g1", by="foreign")],
                     [_kpi("k1", update="g1", title="K1"),
                      _kpi("k1__by__0", title="PLAIN")])

    def test_the_saved_page(self, tmp_path):
        r, page, msgs = _saved(tmp_path, self._spec())
        assert _cards(r.kpi_divs.values()) == [("k1", "K1")]
        assert "PLAIN" not in page
        _one_refusal(msgs, "KPI", "k1__by__0")

    def test_the_served_app(self, tmp_path):
        doc, built, session = _served(tmp_path, self._spec())
        assert all(title != "PLAIN"
                   for _, title in _cards(doc.select({"type": Div})))
        # ...and k1 is drawn, as on the saved page: the all() above held
        # for a served document with no card at all.
        assert _cards(doc.select({"type": Div})) == [("k1", "K1")]
        _one_refusal(built, "KPI", "k1__by__0")
        assert _refusals(session) == []


class TestAKpiNamedLikeAGraphsPanel:
    """A KPI g2__by__0 beside a graph g2: _dash_kpi_keys took the card for
    g2's own, so the automatic layout(bs) put the graph in the KPI row.
    Refused, the graphs are laid out as graphs -- two to a row -- in both
    modes."""

    @staticmethod
    def _spec():
        return _spec([_graph("g1"), _graph("g2")],
                     [_kpi("g2__by__0", title="PLAIN")], layout="bs")

    def test_the_saved_page(self, tmp_path):
        r, page, msgs = _saved(tmp_path, self._spec())
        ids = {f.id: k for k, f in r.figures.items()}
        body = page[page.index('<div class="db-container">'):]
        cells = [(ids.get(root, "?"), int(span)) for span, root in
                 re.findall(r'db-col-lg-(\d+)[^"]*"><div id="[^"]*" '
                            r'data-root-id="([^"]+)"', body)]
        assert cells == [("g1", 6), ("g2", 6)]
        assert "PLAIN" not in page
        _one_refusal(msgs, "KPI", "g2__by__0")

    def test_the_served_app(self, tmp_path):
        doc, built, _ = _served(tmp_path, self._spec())
        [box] = list(doc.select({"type": GridBox}))
        cells = [(getattr(getattr(m, "title", None), "text", "card"),
                  r, c, cs) for m, r, c, _rs, cs in box.children]
        assert cells == [("g1", 0, 0, 6), ("g2", 0, 6, 6)]
        _one_refusal(built, "KPI", "g2__by__0")


class TestTheBootstrapPagesOwnKeys:
    """The saved layout(bs) page keys its tab strip __tabs__ and its
    filters __fw_0__, ...  A graph of either name replaced the part, or the
    part the graph; refused, each part is on the page once."""

    @staticmethod
    def _roots(r, page):
        """What the page embeds, in page order."""
        ids = {f.id: "figure:" + k for k, f in r.figures.items()}
        ids.update({w.id: "filter" for w in r.filter_widgets})
        body = page[page.index('<div class="db-container">'):]
        return [ids.get(x, "other") for x in
                re.findall(r'data-root-id="([^"]+)"', body)]

    def test_a_graph_named_like_the_tab_strip(self, tmp_path):
        spec = _spec([_graph("g1"), _graph("__tabs__")], layout="bs",
                     tabs="A: g1")
        r, page, msgs = _saved(tmp_path, spec)
        roots = self._roots(r, page)
        assert roots.count("other") == 1          # the tab strip, once
        assert "figure:__tabs__" not in roots
        _one_refusal(msgs, "graph", "__tabs__")
        doc, built, _ = _served(tmp_path, spec)
        tabs = list(doc.select({"type": Tabs}))
        assert len(tabs) == 1 and [p.title for p in tabs[0].tabs] == ["A"]
        assert _titles(_figures(doc)) == ["g1"]
        _one_refusal(built, "graph", "__tabs__")

    def test_a_graph_named_like_a_filter(self, tmp_path):
        spec = _spec([_graph("g1"), _graph("__fw_0__")], layout="bs",
                     filter="foreign, type(dropdown)")
        r, page, msgs = _saved(tmp_path, spec)
        roots = self._roots(r, page)
        assert roots == ["filter", "figure:g1"]
        _one_refusal(msgs, "graph", "__fw_0__")
        doc, built, _ = _served(tmp_path, spec)
        assert _titles(_figures(doc)) == ["g1"]
        assert len(list(doc.select({"type": Select}))) == 1
        _one_refusal(built, "graph", "__fw_0__")


class TestARepeatedName:
    """A spec that names two items alike drew one of them, in both modes.
    The first is drawn and the repeat is refused aloud -- graphs are read
    before KPI cards, so a card named like a graph is the repeat."""

    @pytest.mark.parametrize("graphs, kpis, kind, name, figs, cards", [
        ([("g1", "FIRST"), ("g1", "SECOND")], [], "graph", "g1",
         ["FIRST"], []),
        ([("g0", "g0")], [("k1", "FIRST"), ("k1", "SECOND")], "KPI", "k1",
         ["g0"], [("k1", "FIRST")]),
        ([("g1", "GRAPH")], [("g1", "CARD")], "KPI", "g1", ["GRAPH"], []),
    ])
    def test_the_first_is_drawn_in_both_modes(self, tmp_path, graphs, kpis,
                                              kind, name, figs, cards):
        spec = _spec([_graph(n, title=t) for n, t in graphs],
                     [_kpi(n, title=t) for n, t in kpis])
        r, page, msgs = _saved(tmp_path, spec)
        assert _titles(r.figures.values()) == figs
        assert _cards(r.kpi_divs.values()) == cards
        _one_refusal(msgs, kind, name)
        doc, built, _ = _served(tmp_path, spec)
        assert _titles(_figures(doc)) == figs
        assert _cards(doc.select({"type": Div})) == cards
        _one_refusal(built, kind, name)


# ---------------------------------------------------------------------------
# The rule, directly
# ---------------------------------------------------------------------------

class TestTheRule:

    @pytest.mark.parametrize("name, reserved", [
        ("g1__by__0", True), ("__tabs__", True), ("__fw_0__", True),
        ("a__b", True), ("__", True), ("a___b", True),
        ("a_b", False), ("_g1", False), ("g1_", False), ("g_1_2", False),
        ("g1", False), ("", False),
    ])
    def test_two_underscores_in_a_row_are_reserved(self, name, reserved):
        assert dr._dash_reserved_name(name) is reserved

    def test_every_name_dash_generates_is_reserved(self, tmp_path):
        """The rule holds only while every name dash makes up holds "__":
        each figure and card the renderer keys under a name nobody
        registered -- a by() graph's panels.  (A KPI is one card, under its
        own name, since the saved page stopped splitting one per panel.)"""
        spec = _spec([_graph("g1", by="foreign")],
                     [_kpi("k1", update="g1")], layout="bs", tabs="A: g1",
                     filter="foreign, type(dropdown)")
        r, _, _ = _saved(tmp_path, spec)
        made_up = [k for k in list(r.figures) + list(r.kpi_divs)
                   if k not in ("g1", "k1")]
        assert len(made_up) == 2, made_up
        assert all(dr._dash_reserved_name(k) for k in made_up)

    @pytest.mark.parametrize("names, shown", [
        (["a__b"], "'a__b'"),
        (["a__b", "c__d"], "'a__b', 'c__d'"),
        ([f"n__{i}" for i in range(7)],
         "'n__0', 'n__1', 'n__2', 'n__3', 'n__4' and 2 more"),
        (["x\u202e__y"], "'x?__y'"),
    ])
    def test_the_names_are_listed_bounded_and_printable(self, names, shown):
        assert dr._dash_listed_names(names) == shown

    def test_the_spec_pass_refuses_them_and_leaves_the_caller_s_spec(self):
        import json
        spec = _spec([_graph("g1"), _graph("a__b"), _graph("g1")],
                     [_kpi("k1"), _kpi("k__1"), _kpi("g1")])
        before = json.dumps(spec, sort_keys=True)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out = dr._dash_cap_spec(spec, dr._dash_limits({}))
        assert json.dumps(spec, sort_keys=True) == before
        assert [g["graph_options"]["name"] for g in out["graphs"]] == ["g1"]
        assert [k["name"] for k in out["kpis"]] == ["k1"]
        assert _refusals([str(w.message) for w in caught]) == [
            "dash: graph name 'a__b' refused: two underscores in a row are "
            "kept for the names dash generates, such as a by() graph's "
            "panels; that graph is not drawn.",
            "dash: graph name 'g1' already names an earlier graph or KPI "
            "card; that graph is not drawn.",
            "dash: KPI name 'k__1' refused: two underscores in a row are "
            "kept for the names dash generates, such as a by() graph's "
            "panels; that card is not drawn.",
            "dash: KPI name 'g1' already names an earlier graph or KPI "
            "card; that card is not drawn.",
        ]

    def test_a_refused_item_takes_no_place_under_the_graphs_limit(self):
        spec = _spec([_graph("a__0"), _graph("g1"), _graph("g2")])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out = dr._dash_cap_spec(spec, dr._dash_limits(
                {"limits": {"graphs": 2}}))
        assert [g["graph_options"]["name"] for g in out["graphs"]] == \
            ["g1", "g2"]
        assert not [w for w in caught if "a dashboard draws" in
                    str(w.message)]

    def test_a_spec_without_them_is_untouched(self):
        spec = _spec([_graph("g1", by="foreign"), _graph("g2")],
                     [_kpi("k1")])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out = dr._dash_cap_spec(spec, dr._dash_limits({}))
        assert out["graphs"] == spec["graphs"] and out["kpis"] == spec["kpis"]
        assert _refusals([str(w.message) for w in caught]) == []


# ---------------------------------------------------------------------------
# CLAUDE.md rule 18, for a name in a spec that did not come through dash.ado
# ---------------------------------------------------------------------------

class TestAdversarialReservedNames:
    """Registered in test_adversarial_matrix's SURFACES under name_option."""

    @pytest.mark.parametrize("name, refused", [
        ("g1__by__0", True), ("G1__BY__0", True), ("g1__by__00", True),
        ("g1\u200b__by__0", True), ("\uff471__by__0", True),
        ("__tabs__", True), ("__fw_0__", True), ("g1__by__0 ", True),
        ("_g1", False), ("g1_", False), ("g1_by_0", False),
        ("g1_\uff3fby_\uff3f0", False),
    ])
    def test_bypass_no_spelling_takes_a_panel_s_place(self, tmp_path, name,
                                                      refused):
        """g1 keeps both its panels whatever the other graph is called: a
        name holding "__" is refused, and one that does not cannot equal a
        name dash generates, so it is drawn beside them."""
        spec = _spec([_graph("g1", by="foreign"), _graph(name)])
        r, page, msgs = _saved(tmp_path, spec)
        panels = {k: f.title.text for k, f in r.figures.items()
                  if k.startswith("g1__by__")}
        assert panels == dict(zip(["g1__by__0", "g1__by__1"], _PANELS))
        assert bool(_refusals(msgs)) is refused, msgs
        # Each graph here is titled with its own name.
        drawn = {f.title.text for f in r.figures.values()}
        assert (name in drawn) is (not refused)

    @pytest.mark.parametrize("name", [
        "{err}__x", "<img src=x onerror=alert(1)>__0", "a__\x1b[31mred",
        "a__\u202egnp.exe", "a__\x00b", "Q" * 5000 + "__",
    ])
    def test_injection_a_refused_name_is_inert_text(self, tmp_path, name):
        """The refusal shows the name as printable text, at most 80
        characters of it, and nothing of the name reaches the page."""
        spec = _spec([_graph("g1"), _graph(name, title="HOSTILE")])
        r, page, msgs = _saved(tmp_path, spec)
        [msg] = _refusals(msgs)
        assert msg.isprintable() and len(msg) < 300, msg
        assert sorted(r.figures) == ["g1"]
        assert "HOSTILE" not in page
        assert name[:40] not in page

    def test_exhaustion_many_refused_names_make_one_bounded_report(self):
        graphs = [_graph(f"g__{i}") for i in range(50_000)] + [_graph("ok")]
        spec = _spec(graphs, [_kpi(f"k__{i}") for i in range(50_000)])
        t = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out = dr._dash_cap_spec(spec, dr._dash_limits({}))
        took = time.perf_counter() - t
        msgs = _refusals([str(w.message) for w in caught])
        assert len(msgs) == 2, msgs
        assert all(len(m) < 400 for m in msgs)
        assert "and 49,995 more" in msgs[0] and "and 49,995 more" in msgs[1]
        assert [g["graph_options"]["name"] for g in out["graphs"]] == ["ok"]
        assert out["kpis"] == []
        assert took < 5, f"{took:.1f} s"


# ---------------------------------------------------------------------------
# G1 (WP-28): the __dash prefix is reserved for the columns dash makes, so
# it never collides with a user variable; every other Stata name -- even
# one dash used to make up itself -- is read as the user's data.
# ---------------------------------------------------------------------------

def _reserved_df(extra_col, values=None):
    """Four rows of mpg/weight, plus one column of the caller's choosing."""
    df = pd.DataFrame({
        "mpg": [22.0, 17.0, 25.0, 30.0],
        "weight": [2930.0, 3350.0, 2200.0, 1800.0],
    })
    df[extra_col] = values if values is not None else [1.0, 2.0, 3.0, 4.0]
    return df


class TestTheDashPrefix:
    """A variable named with the __dash prefix is refused, before any
    export, unless the spec names it as a qualifier column; every other
    Stata name is read as data (dash.sthlp:166-171; _dash_take_qual_columns;
    _dash_qual_gen in dash.ado)."""

    @pytest.mark.parametrize("name", [
        "__dash_row__", "__dash_mlabel_y", "__dash_xjit",
        "__dashfix0a1b2c3d4e5f", "__dash",
    ])
    def test_a_column_under_the_prefix_is_refused_in_both_modes(
            self, tmp_path, name):
        df = _reserved_df(name)
        spec = _spec([_graph("g1")])
        sp, dp = _write_inputs(tmp_path, spec, df=df)
        with pytest.raises(ValueError, match="reserved") as exc:
            DashRenderer(sp, dp)
        assert "__dash" in str(exc.value)
        ap = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
        with pytest.raises(ValueError, match="reserved") as exc2:
            dr.ServerAppBuilder(sp, dp).build(ap)
        assert "__dash" in str(exc2.value)

    def test_a_qualifier_column_the_spec_names_still_passes(self, tmp_path):
        df = _reserved_df("__dashq1", values=[1.0, 0.0, 1.0, 0.0])
        graph = _graph("g1")
        graph["qual_col"] = "__dashq1"
        spec = _spec([graph])
        sp, dp = _write_inputs(tmp_path, spec, df=df)
        r = DashRenderer(sp, dp)
        r.render()
        [fig] = list(r.figures.values())
        [sc] = [x for x in fig.renderers
               if type(x.glyph).__name__ == "Scatter"]
        # The qualifier keeps rows 0 and 2 (mpg 22.0, 25.0); the column
        # itself never reaches the source.
        assert list(sc.data_source.data["mpg"]) == [22.0, 25.0]
        assert "__dashq1" not in sc.data_source.data
        ap = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
        dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            assert "__dashq1" not in fh.read()

    @pytest.mark.parametrize("name, mode", [
        ("__mlabel__y", "mlabel"),
        ("_x_jit", "jitter"),
        ("__mlabel_values__", "mlabel"),
        ("_y_jit", "jitter"),
        ("x", "plain"),
        ("top", "plain"),
    ])
    def test_a_name_dash_no_longer_makes_is_drawn_with_its_own_values(
            self, tmp_path, name, mode):
        values = [22.0, 17.0, 25.0, 30.0]
        df = _reserved_df(name, values=values)
        options = {}
        if mode == "jitter":
            options["jitter"] = "5"
        elif mode == "mlabel":
            options["mlabel"] = name
        plot = {"type": "scatter", "yvar": name, "xvar": "weight",
                "options": options}
        spec = _spec([{"plots": [plot],
                       "graph_options": {"name": "g1", "title": "g1"},
                       "if_expr": "", "in_expr": ""}])
        sp, dp = _write_inputs(tmp_path, spec, df=df)

        r = DashRenderer(sp, dp)
        r.render()
        [fig] = list(r.figures.values())
        [renderer] = [x for x in fig.renderers
                      if type(x.glyph).__name__ == "Scatter"]
        src = renderer.data_source
        assert list(src.data[name]) == values
        if mode == "mlabel":
            text_col = dr._DASH_MLABEL_PREFIX + name
            assert text_col in src.data
            # the variable's %9.0g, as `display %9.0g 22' writes it
            assert list(src.data[text_col]) == ["22", "17", "25", "30"]

        ap = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            ns = _load_app(fh.read(), "own_%d" % next(_SEQ))
        doc = Document()
        ns["make_document"](doc)
        [sfig] = _figures(doc)
        [srenderer] = [x for x in sfig.renderers
                       if type(x.glyph).__name__ == "Scatter"]
        assert list(srenderer.data_source.data[name]) == values

    def test_the_stata_side_and_the_help_share_the_prefix(self):
        _root = os.path.dirname(_HERE)
        with open(os.path.join(_root, "dash.ado"), encoding="utf-8") as fh:
            ado_text = fh.read()
        assert "unab _dq_clash : __dash*" in ado_text
        with open(os.path.join(_root, "dash.sthlp"), encoding="utf-8") as fh:
            sthlp_text = fh.read()
        assert "{cmd:__dash}" in sthlp_text
        assert dr._DASH_RESERVED_PREFIX == "__dash"
