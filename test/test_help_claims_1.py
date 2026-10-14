"""dash.sthlp, Title to "Differences from twoway": each claim held to the code.

ROADMAP WP-23, AC-23.1: every claim in the help is verified by a test or
corrected.  This file is the Python half for the help's first sections --
the header, Syntax, Description, Plot types and "Differences from twoway"
(dash.sthlp lines 1-316 at 4ede074, and the legend() sub-option sentence of
the Option values item).  The Stata half, measured against twoway in the same
run, is ``test_help_claims_1.cscript`` (HC1-01 .. HC1-23).

What was measured false on 23sep2026 at 4ede074, and what each test here
pins:

* The Syntax section showed a ``{weight}`` after the plot specifications,
  where neither twoway nor dash takes one (both r(198)), called a weight
  "one variable, [aweight=varname]" although fweight and pweight are
  honoured too, and left ``csv`` out of dash build's diagram and
  ``name(..., replace)`` out of dash kpi's.
* "Every figure includes ... hover tooltips": a figure whose only layers
  were a fit or smooth other than lfit and qfit, function, a
  paired-coordinate type or rcapsym had none, in either mode -- seventeen
  plot types.  The fallback tooltip read only columns named x and y, and
  only from the figure's first renderer.
* "abbreviated as twoway allows": dash refused twoway's own spellings
  mbands and fn, and took twenty-nine shorter ones twoway refuses without
  the help saying so.
* "the two twoway plot types it refuses": there are four.
* "a command copy-pasted from a do-file runs whenever dash draws its plot
  type": degree(8) and bin(2000) run in twoway and are refused.
* "scheme() is fully supported", beside a scheme section that says the
  range, fit and immediate layers do "not yet" take a scheme's opacity.
* "The registry holds at most 100 items": $dash_max_graphs moves it.
* Half the "see also" links went to no help file (connected, area, bar,
  spike, qfit, lfitci, qfitci, fpfit), and ``help lfit`` opens an
  out-of-date command's page rather than twoway lfit's.
* A qualifier written after the plot groups reached neither renderer; the
  renderers' half of the fix -- a graph's own qualifier applied to every
  layer, on top of a layer's own -- is held to twoway's arithmetic here in
  both modes.  The served app counted an ``in`` over the rows the graph's
  qualifier or a filter move had left rather than over the dataset's
  observations: a layer's own ``in`` at the first draw, and the graph's and
  the layer's after a filter move.
* "Launch Bokeh Server (blocking -- press Ctrl+C to stop)" had no test: the
  launcher is run here, found waiting while the server answers, and
  stopped with SIGINT.
"""
import html.parser
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import warnings

import pytest
from bokeh.models import HoverTool, Plot

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_abbreviations import _program_body, _syntax_options  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from conftest import stata_base, stata_plus  # noqa: E402

_HELP = os.path.join(_ROOT, "dash.sthlp")
_ADO = os.path.join(_ROOT, "dash.ado")
_MATA = os.path.join(_ROOT, "dash_parse.mata")

#: Stata's own directories, where the help files a "see also" link names
#: live: the base ado tree, one directory per first letter, and PLUS
#: (DASH_STATA_BASE and DASH_STATA_PLUS, WP-30 P1.34).
_STATA_BASE = stata_base()
_STATA_PLUS = stata_plus()
_TWOWAY_CLASS = os.path.join(_STATA_BASE, "t", "twowaygraph_g.class")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _help():
    return _read(_HELP)


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _syntax():
    return _between(_help(), "{marker syntax}", "{marker description}")


def _plot_types():
    return _between(_help(), "{marker plottypes}", "{marker differences}")


def _differences():
    return _between(_help(), "{marker differences}", "{marker subcommands}")


def _prose(text):
    """SMCL reduced to its words: directives unwrapped, lines joined."""
    t = re.sub(r"\{(?:cmd|it|opt|bf|ul|cmdab)[: ]([^{}]*)\}", r"\1", text)
    t = re.sub(r"\{helpb? [^:}]*:([^}]*)\}", r"\1", t)
    t = re.sub(r"\{helpb? ([^:}]*)\}", r"\1", t)
    return re.sub(r"\s+", " ", t)


# ===========================================================================
# 1. The header
# ===========================================================================

def _help_aliases():
    """Stata's help aliases, {topic: help file name}: the
    <letter>/<letter>help_alias.maint tables `help' consults when no
    <topic>.sthlp exists (`twoway' -> graph_twoway)."""
    out = {}
    if not os.path.isdir(_STATA_BASE):
        return out
    for letter in sorted(os.listdir(_STATA_BASE)):
        p = os.path.join(_STATA_BASE, letter, letter + "help_alias.maint")
        if os.path.exists(p):
            with open(p, encoding="latin-1") as fh:
                for ln in fh:
                    parts = ln.split()
                    if len(parts) >= 2:
                        out.setdefault(parts[0], parts[1])
    return out


def _help_file(topic, aliases=None):
    """The path of the help file `help topic' opens, or None."""
    for name in (topic, (aliases or {}).get(topic)):
        if not name:
            continue
        for d in (_ROOT, os.path.join(_STATA_BASE, name[0]),
                  os.path.join(_STATA_PLUS, name[0])):
            p = os.path.join(d, name + ".sthlp")
            if os.path.exists(p):
                return p
    return None


class TestTheHeader:

    def test_stata_is_installed_where_the_links_are_checked(self):
        """The checks below read Stata's own help files; without them they
        would check nothing, so their absence is a failure, not a skip."""
        assert os.path.isdir(_STATA_BASE), _STATA_BASE

    def test_every_see_also_link_opens_a_current_help_file(self):
        targets = re.findall(r'\{vieweralsosee "[^"]*"\s+"help ([^"]+)"\}',
                             _help())
        assert len(targets) >= 15
        aliases = _help_aliases()
        assert aliases.get("twoway") == "graph_twoway", (
            "Stata's help alias tables were not read")
        bad = []
        for t in targets:
            p = _help_file(t.strip(), aliases)
            if p is None:
                bad.append(f"{t}: no help file")
            elif "Out-of-date command" in _read(p)[:600]:
                bad.append(f"{t}: an out-of-date command's page")
        assert not bad, bad

    def test_each_twoway_plot_type_links_to_its_own_page(self):
        """`help connected' finds no file; twoway's pages are
        twoway_<type>, as graph_twoway.sthlp itself links them."""
        links = dict(re.findall(
            r'\{vieweralsosee "([^"]*)"\s+"help ([^"]+)"\}', _help()))
        for ptype in ("connected", "area", "bar", "spike", "lfit", "qfit",
                      "lfitci", "qfitci", "lowess", "lpoly", "fpfit",
                      "histogram", "kdensity"):
            assert links.get(ptype) == "twoway_" + ptype, (ptype,
                                                           links.get(ptype))

    def test_plot_types_is_in_the_jump_list(self):
        assert re.search(r'\{viewerjumpto "Plot types"\s+"dash##plottypes"\}',
                         _help())

    def test_the_version_line_is_dash_ados(self):
        m = re.search(r"\{\* \*! version (\S+)\s+([0-9a-z]+)\}", _help())
        assert m, "the help's version line moved"
        ado = _read(_ADO)
        assert re.search(r"^\*! Version: %s\s+%s$" % (re.escape(m.group(1)),
                                                       re.escape(m.group(2))),
                         ado, re.MULTILINE), m.groups()


# ===========================================================================
# 2. The Syntax section
# ===========================================================================

class TestTheSyntaxDiagram:

    def test_no_weight_follows_the_plot_specifications(self):
        """`twoway (lfit y x) [aw=w]' is r(198), "[ is not a twoway plot
        type", and so is dash's (HC1-06): a weight belongs to a plot."""
        for ln in _syntax().split("\n"):
            if "{it:plot_specs} {ifin}" in ln:
                assert "{weight}" not in ln, ln
        # The loop above asserts only on a line that reads exactly
        # "{it:plot_specs} {ifin}", so a diagram rewritten as
        # "{it:plot_specs} {weight} {ifin}" was never looked at.  Measured
        # 24sep2026: two diagrams write {it:plot_specs} (the single graph
        # and the named graph), each a {p} paragraph of two lines; each
        # whole paragraph is read, and there must be two.
        paras = [p for p in re.split(r"\n\s*\n", _syntax())
                 if "{cmd:dash} {it:plot_specs}" in p]
        assert len(paras) == 2, (
            f"{len(paras)} Syntax diagrams write {{cmd:dash}} "
            f"{{it:plot_specs}}, two measured: {paras}")
        for p in paras:
            assert "{weight}" not in p, p

    def test_the_plot_specification_carries_the_weight(self):
        assert re.search(r"\{it:plottype varlist\} \{ifin\} \{weight\}",
                         _syntax())

    def test_every_weight_type_dash_honours_is_named(self):
        """_dash_parse_varpart_std declares aweight fweight pweight (and
        iweight, which every plot type refuses, as twoway refuses it)."""
        text = _syntax()
        for w in ("aweight", "fweight", "pweight"):
            assert "{cmd:[%s=}" % w in text, w
        # Flipped (WP-31 A5b): "one variable" was wrong because twoway
        # evaluates a weight expression (WP-31 A5) and so does dash.
        assert "or an expression, as in twoway" in _prose(text)

    def test_the_kpi_diagram_shows_name_with_replace(self):
        kpi = _between(_syntax(), "{ul:KPI card}", "{ul:Build dashboard")
        assert ("{cmdab:nam:e}{cmd:(}{it:identifier} [{cmd:, replace}]"
                "{cmd:)}") in kpi

    def test_the_build_diagrams_name_every_build_option(self):
        """Both directions: every option _dash_build declares (and filter(),
        which it takes before -syntax- runs) is in its diagrams, and the
        diagrams name nothing it does not declare."""
        src = _read(_ADO)
        declared = {full for _mn, full in
                    _syntax_options(_program_body(src, "_dash_build"))}
        declared.add("filter")
        block = _between(_syntax(), "{ul:Build dashboard",
                         "{ul:Launch Bokeh Server")
        shown = set()
        for head, tail in re.findall(r"\{cmdab:([a-z]+):([a-z]*)", block):
            shown.add(head + tail)
        shown |= set(re.findall(r"\{cmd:([a-z]+)[(}]", block))
        # asis is saving()'s sub-option (saving(f, asis), WP-30 P1.27), not
        # an option of dash build.
        shown -= {"dash", "build", "top", "left", "type", "exclude",
                  "label", "_all", "asis"}
        assert declared - shown == set(), declared - shown
        assert shown - declared == set(), shown - declared

    def test_the_serve_diagram_names_serves_own_options(self):
        src = _read(_ADO)
        own = {full for _mn, full in
               _syntax_options(_program_body(src, "_dash_serve_spec"))}
        # An empty set asserts nothing below: _syntax_options returns []
        # when no line of the body begins with `syntax' (a `capture
        # syntax', say), and the diagram was then held to nothing.
        # Measured 24sep2026: specpath() and datapath() -- the plumbing
        # every version declares -- and port(), nobrowser and timeout().
        # The plumbing proves the declaration was read; the three are the
        # floor of what it must yield, and any option added later is held
        # to the diagram by the loop.
        assert {"specpath", "datapath"} <= own, (
            f"_dash_serve_spec's syntax statement was not read: {own}")
        own -= {"specpath", "datapath", "*"}
        assert {"port", "nobrowser", "timeout"} <= own, own
        block = _between(_syntax(), "{ul:Launch Bokeh Server", "{ul:Clear")
        for opt in own:
            assert "{cmd:%s" % opt in block, opt


# ===========================================================================
# 3. The Plot types section
# ===========================================================================

#: twoway's plot-type spellings, from twowaygraph_g.class, program _unab_cmd:
#:     syntax [ , SCatter LIne CONnected HISTogram RSCatter RLine ///
#:                RCONnected MBANDs FN FUNction *]
#: Each declared name may be written from its capitals to its full length;
#: MBANDs is the plot type mband and FN is function.  Every other plot
#: type is its full name only (its twoway_<name>_parse.class).  Measured
#: against twoway itself in test_help_claims_1.cscript HC1-07 and HC1-08.
_TWOWAY_UNAB = (("SCatter", "scatter"), ("LIne", "line"),
                ("CONnected", "connected"), ("HISTogram", "histogram"),
                ("RSCatter", "rscatter"), ("RLine", "rline"),
                ("RCONnected", "rconnected"), ("MBANDs", "mband"),
                ("FN", "function"), ("FUNction", "function"))


def _twoway_spellings():
    """{spelling: plot type} for every plot type dash draws."""
    out = {name: name for name in dr._dash_plot_type_names()}
    for decl, ptype in _TWOWAY_UNAB:
        mn = re.match(r"[A-Z]+", decl).group(0).lower()
        full = decl.lower()
        for k in range(len(mn), len(full) + 1):
            out[full[:k]] = ptype
    return out


def _mata_table():
    """(full, minimum) rows of _expand_plottype_str's table."""
    mata = _read(_MATA)
    body = mata[mata.index("string scalar _expand_plottype_str("):]
    body = body[:body.index("\n}\n")]
    return re.findall(r'\("([a-z]+)","([a-z]+)"\)', body)


def _dash_spellings():
    """{spelling: plot type} dash's table takes: any prefix at least as long
    as a row's minimum, the first row that takes it, as the Mata loop reads
    it (no prefix is taken by two rows: test_no_orphans.py); and the twoway
    spellings it maps by name."""
    rows = _mata_table()
    out = {}
    for full, _mn in rows:
        for k in range(1, len(full) + 1):
            p = full[:k]
            hits = [f for f, m in rows if len(p) >= len(m) and f.startswith(p)]
            if hits:
                out[p] = hits[0]
    mata = _read(_MATA)
    body = mata[mata.index("string scalar _expand_plottype_str("):]
    body = body[:body.index("\n}\n")]
    for sp, ptype in re.findall(
            r'if \(name == "([a-z]+)"\) return\("([a-z]+)"\)', body):
        out[sp] = ptype
    return out


class TestThePlotTypeSpellings:

    def test_the_twoway_list_is_twoways_own(self):
        """The list above is the declaration in twoway's class file."""
        assert os.path.exists(_TWOWAY_CLASS), _TWOWAY_CLASS
        cls = _read(_TWOWAY_CLASS)
        m = re.search(r"program _unab_cmd.*?syntax \[ , (.*?)\*\]", cls, re.S)
        assert m, "twowaygraph_g.class has no _unab_cmd syntax line"
        decl = re.sub(r"///", " ", m.group(1)).split()
        assert decl == [d for d, _p in _TWOWAY_UNAB], decl

    def test_the_help_names_twoways_own_abbreviations(self):
        """The section says which shorter names are twoway's own: its
        intro names exactly the minimum of each declaration above, and the
        two other names, each beside its type."""
        intro = _between(_plot_types(), "{marker plottypes}", "{synoptset")
        named = dict((a, t) for a, t in re.findall(
            r"\{cmd:([a-z]+)\}\s+for\s+\{cmd:([a-z]+)\}", intro))
        want = {}
        for decl, ptype in _TWOWAY_UNAB:
            mn = re.match(r"[A-Z]+", decl).group(0).lower()
            want[mn if decl.lower() != "mbands" else "mbands"] = ptype
        assert named == want, (named, want)

    def test_dash_takes_every_twoway_spelling_as_the_same_type(self):
        dash = _dash_spellings()
        bad = {sp: (ptype, dash.get(sp))
               for sp, ptype in _twoway_spellings().items()
               if dash.get(sp) != ptype}
        assert not bad, bad

    def test_dash_takes_no_spelling_twoway_refuses(self):
        """Flipped (WP-31 A2): the section listed the shorter names only
        dash took (ar .. tsrlin) under Synonyms; twoway refuses each, "ar
        is not a twoway plot type", r(198), and so does dash now
        (test/fixtures/bare_prefix_truth.json extras.*), so there is no
        table and no spelling dash alone takes."""
        tw = _twoway_spellings()
        only_dash = {sp: p for sp, p in _dash_spellings().items()
                     if sp not in tw}
        assert only_dash == {}, only_dash
        assert "{ul:Synonyms.}" not in _plot_types()
        assert '"{it:word} is not a twoway plot' in _plot_types()

    def test_the_case_examples_are_spellings_read_lower_cased(self):
        """dash reads the name through strlower(); the capitals the help
        gives -- SC and Hist, which twoway refuses (HC1-08) -- are that,
        each a dash spelling once lower-cased, of the type it is said to
        draw."""
        # Flipped (WP-31 A2): the paragraph is Case, after the Synonyms
        # table went.
        tail = _between(_plot_types(), "{ul:Case.}", "{ul:pccapsym.}")
        caps = [c for c in re.findall(r"\{cmd:([A-Za-z]+)\}", tail)
                if not c.islower()]
        assert set(caps) == {"SC", "Hist"}, caps
        dash = _dash_spellings()
        assert dash.get("sc") == "scatter" and dash.get("hist") == "histogram"
        assert "a scatter and a histogram" in _prose(tail)
        ado = _read(_ADO)
        assert ('_dash_expand_plottype(strlower(st_local("plottype"))'
                in ado)


class TestThePlotTypesSection:

    def test_it_says_four_types_are_refused_and_so_does_item_5(self):
        refused = ("contour", "contourline", "rpcap", "rpspike")
        assert "Four {cmd:twoway} plot types are not drawn" in _plot_types()
        diff = _prose(_differences())
        assert "the four twoway plot types it refuses" in diff
        assert "the two twoway plot types" not in diff
        for name in refused:
            assert name not in dr._dash_plot_type_names()

    def test_the_unrecognised_message_lists_the_table(self):
        """"the message lists the plot types above": the words dash.ado
        displays after "Supported:" are the table's, in both directions."""
        ado = _read(_ADO)
        i = ado.index('"Supported: ')
        j = ado.index("exit(198)", i)
        words = set(re.findall(r"[A-Za-z]+", " ".join(
            re.findall(r'"([^"]*)"', ado[i:j]))))
        words.discard("Supported")
        table = _plot_types().split("{synoptline}")[1]
        listed = set(re.findall(r"\{cmd:([a-z]+)\}", table))
        assert words == listed, sorted(words ^ listed)

    def test_the_time_series_row_is_twoways_rule(self):
        """tsline and tsrline draw against the tsset time variable, as
        twoway does (HC1-09); dash takes no time variable in the varlist."""
        sec = _prose(_plot_types())
        assert "when none is given" not in sec
        assert "the time variable tsset set" in sec

    def test_the_operator_paragraph_is_twoways_rule(self):
        """WP-30 P1.7: the types the paragraph names as taking and refusing
        operators are twoway's (fixtures/ts_operator_truth.json, A and R
        probes), and so are the refusals' words."""
        with open(os.path.join(_HERE, "fixtures", "ts_operator_truth.json"),
                  encoding="utf-8") as fh:
            probes = json.load(fh)["probes"]
        sec = _prose(_plot_types())
        para = sec[sec.index("Time-series operators."):]
        para = para[:para.index("sysuse sp500")]
        cut, lead = para.index("refuse them"), para.index("fpfit")
        refused = {p["body"].split()[0] for k, p in probes.items()
                   if k[0] == "R" and p["twoway"]["rc"] == 101}
        taken = {p["body"].split()[0] for k, p in probes.items()
                 if k[0] == "A" and p["twoway"]["rc"] == 0}
        for t in refused:
            assert re.search(r"\b%s\b" % t, para[lead:cut]), t
        for t in taken - set(_RANGE_AND_PC):
            assert re.search(r"\b%s\b" % t, para[:lead]), t
        assert "eight range types, the five paired-coordinate types" in para
        for k in ("E01", "E02", "E03", "E06", "R01", "B01"):
            words = probes[k]["twoway"]["err"][0].replace("make:  ", "")
            assert words in para, (k, words)
        # The bare sort: both of twoway's lines, and the types it refuses
        # it on (the O probes twoway answers r(198)).
        for line in probes["O01"]["twoway"]["err"]:
            assert line in para, line
        tail = para[para.index("A bare sort"):]
        for k, p in probes.items():
            if k[0] == "O" and p["twoway"]["rc"] == 198:
                t = p["body"].split()[0]
                assert re.search(r"\b%s\b" % t, tail) or (
                    t in _RANGE_AND_PC and "eight range types" in tail), t
        assert "headed by the expression" in para


#: The range and paired-coordinate types the operator paragraph counts.
_RANGE_AND_PC = ("rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
                 "rcapsym", "rscatter", "pcspike", "pcarrow", "pcbarrow",
                 "pcscatter", "pccapsym")


# ===========================================================================
# 4. The Differences section
# ===========================================================================

class TestTheDifferencesSection:

    def test_item_5_names_the_values_dash_refuses(self):
        """HC1-16: degree(8), bin(2000) run in twoway and are refused by
        dash.  Flipped (WP-31 C10b): degree(4) is drawn.  Flipped (WP-31
        C10c): yaxis(3) is drawn, so the help names bin(2000)."""
        diff = _prose(_differences())
        assert ("runs whenever dash draws its plot type (see" not in diff)
        assert "bin(2000)" in diff and "Option values" in diff
        assert "yaxis(3)" not in diff

    def test_scheme_is_not_claimed_fully_supported(self):
        """The scheme section says where a scheme's opacity stops: at the
        confidence band, which twoway draws in `color ci_area' with no
        opacity.  Flipped (WP-30 P1.4a): it said the range, fit and
        immediate layers did not yet take the opacity; they do."""
        scheme = " ".join(_between(_help(), "{marker scheme}",
                                   "{marker ").split())
        assert "not yet its opacity" not in scheme
        assert "except the confidence band" in scheme
        assert "fully supported" not in _prose(_differences())

    def test_the_registry_limit_is_the_limit_table(self):
        m = re.search(r"graphs=(\d+),(\d+)", _read(_ADO))
        default, ceiling = int(m.group(1)), int(m.group(2))
        diff = _prose(_differences())
        assert (f"holds {default} items" in diff
                and f"{ceiling:,}" in diff and "$dash_max_graphs" in diff)

    def test_serve_is_among_the_new_subcommands(self):
        item = _between(_differences(), "{ul:New subcommands.}",
                        "{ul:Where a graph-level option")
        for sub in ("kpi", "build", "clear", "serve"):
            assert "{cmd:dash %s}" % sub in item, sub

    def test_every_figure_is_promised_tooltips(self):
        """Pinned by TestEveryFigureHasTooltips below."""
        assert "hover tooltips" in _prose(_differences())


# ===========================================================================
# 5. Description: the saved page needs no network
# ===========================================================================

class _Tags(html.parser.HTMLParser):
    """Every element's name and attributes, outside script and style text
    (HTMLParser reads those as character data, never as markup)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.scripts = []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag == "script":
            self._in_script = True
            self.scripts.append("")

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False

    def handle_data(self, data):
        if self._in_script:
            self.scripts[-1] += data


class TestTheSavedPageNeedsNoNetwork:
    """"The HTML file works offline in any modern browser -- no server,
    internet connection, or special software is required."  Nothing in the
    page is fetched: no element names a URL, BokehJS is in the page, and
    the page's own policy forbids every fetch (default-src 'none')."""

    @pytest.fixture(scope="class")
    def page(self):
        spec = tp._spec([plot_for("scatter"), plot_for("lfit")],
                        build_options={"filter": "foreign, type(dropdown)",
                                       "csv": "csv"},
                        kpis=[{"name": "k1", "stat": "mean", "var": "mpg",
                               "fmt": "%9.2f", "title": "Mean",
                               "subtitle": "", "color": "", "bgcolor": "",
                               "update": "filter", "if_expr": "",
                               "in_expr": ""}])
        _r, _w, page = tp._standalone_page(spec)
        return page

    def test_no_element_loads_anything(self, page):
        p = _Tags()
        p.feed(page)
        bad = []
        for tag, attrs in p.tags:
            for key in ("src", "href", "data", "srcset", "poster"):
                v = (attrs.get(key) or "").strip().lower()
                if re.match(r"^(https?:|//|ftp:|file:)", v):
                    bad.append((tag, key, v[:80]))
            if tag == "script" and attrs.get("src"):
                bad.append((tag, "src", attrs["src"][:80]))
            if tag == "link" and "stylesheet" in (attrs.get("rel") or ""):
                bad.append((tag, "rel", attrs.get("href", "")[:80]))
        assert not bad, bad

    def test_bokehjs_is_in_the_page(self, page):
        p = _Tags()
        p.feed(page)
        big = [s for s in p.scripts if len(s) > 300_000]
        assert big, "no inline script large enough to be BokehJS"
        assert any("Bokeh" in s for s in big)

    def test_the_page_forbids_every_fetch(self, page):
        m = re.search(r'<meta http-equiv="Content-Security-Policy" '
                      r'content="([^"]*)">', page)
        assert m, "the saved page carries no policy"
        policy = m.group(1)
        assert "default-src 'none'" in policy
        assert "connect-src 'none'" in policy


# ===========================================================================
# 5b. Syntax: "Launch Bokeh Server (blocking -- press Ctrl+C to stop)"
# ===========================================================================

def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _health(port):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health",
                                timeout=3) as r:
        return r.status


@pytest.mark.serve
class TestServeBlocksUntilCtrlC:
    """dash serve runs dash_render.py with --launch inside Stata's Python,
    so the command returns when that returns.  It must not return while
    the server runs, and Ctrl+C -- SIGINT -- must stop the server with it.
    No browser opens: --no-browser, as $dash_nobrowser passes it."""

    def test_the_launcher_waits_and_ctrl_c_stops_the_server(self, tmp_path):
        _tag, sp, dp = tp._write(tp._spec([plot_for("scatter")]))
        port = _free_port()
        proc = subprocess.Popen(
            [sys.executable, os.path.join(_ROOT, "dash_render.py"),
             "--spec", sp, "--data", dp,
             "--output", str(tmp_path / "app.py"), "--mode", "server",
             "--launch", "--no-browser", "--port", str(port)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            deadline = time.time() + 90
            up = False
            while time.time() < deadline:
                assert proc.poll() is None, (
                    "the launcher returned while it should be serving:\n"
                    + (proc.stdout.read() or "")[-2000:])
                try:
                    up = _health(port) == 200
                    break
                except Exception:
                    time.sleep(0.5)
            assert up, "the served app never answered /health"
            time.sleep(1.0)
            assert proc.poll() is None, "the launcher did not block"
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=30)
            time.sleep(0.5)
            with pytest.raises(Exception):
                _health(port)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)


# ===========================================================================
# 6. Differences item 1: tooltips on every figure, in both modes
# ===========================================================================

def _saved_figures(r):
    return list(r.figures.values())


def _served_figures(doc):
    return list(doc.select({"type": Plot}))


def _fields(tool):
    out = set()
    tips = tool.tooltips or []
    for _label, value in tips:
        out |= set(re.findall(r"@\{([^}]+)\}", str(value)))
    return out


def _check_tooltips(figs, where):
    assert figs, f"{where}: no figure"
    for fig in figs:
        tools = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert tools, f"{where}: a figure with no tooltips"
        for t in tools:
            fields = _fields(t)
            assert fields, f"{where}: a HoverTool with no fields"
            rends = t.renderers if isinstance(t.renderers, list) else []
            assert rends, f"{where}: a HoverTool bound to no renderer"
            for rd in rends:
                cols = set(rd.data_source.data)
                missing = fields - cols
                assert not missing, (
                    f"{where}: the tooltip reads {sorted(missing)}, which "
                    f"its renderer does not carry, so it would print ???")


_TYPES = sorted(dr._dash_plot_type_names())


@pytest.mark.parametrize("ptype", _TYPES)
class TestEveryFigureHasTooltips:

    def test_saved(self, ptype):
        r, _w = tp._standalone(tp._spec([plot_for(ptype)]))
        _check_tooltips(_saved_figures(r), f"saved {ptype}")

    def test_served(self, ptype):
        doc, _w = tp._served(tp._spec([plot_for(ptype)]))
        _check_tooltips(_served_figures(doc), f"served {ptype}")

    def test_the_modes_word_them_alike(self, ptype):
        r, _w = tp._standalone(tp._spec([plot_for(ptype)]))
        doc, _w2 = tp._served(tp._spec([plot_for(ptype)]))
        saved = sorted(str(t.tooltips) for f in _saved_figures(r)
                       for t in f.tools if isinstance(t, HoverTool))
        served = sorted(str(t.tooltips) for f in _served_figures(doc)
                        for t in f.tools if isinstance(t, HoverTool))
        assert saved == served


class TestTheFallbackTooltipIsSafe:
    """Adversarial (CLAUDE.md rule 18), injection: the fallback reads the
    columns a glyph draws, and a paired-coordinate glyph draws the data's
    own columns by name.  Stata cannot name a variable with markup, but a
    hand-written data file can; such a name must never become a tooltip
    field, where BokehJS parses `@{...}' as HTML."""

    _BAD = "x}<img src=x onerror=alert(1)>"

    def _spec_and_df(self, name=None):
        name = name or self._BAD
        df = tp._DF.copy()
        df[name] = df["price"]
        plot = {"type": "pcspike", "y1var": "mpg", "x1var": "weight",
                "y2var": name, "x2var": "foreign", "options": {}}
        return tp._spec([plot]), df

    def test_no_field_holds_the_name(self, tmp_path, monkeypatch):
        # The control: the same pcspike with a plain name where the hostile
        # one goes is given the segment's tooltip, its four ends as fields,
        # in both modes -- so the reading below does see a segment's fields
        # when dash writes them.
        spec, df = self._spec_and_df("y2plain")
        monkeypatch.setattr(tp, "_DF", df)
        r, _w = tp._standalone(spec)
        doc, _w2 = tp._served(spec)
        for figs in (_saved_figures(r), _served_figures(doc)):
            tools = [t for f in figs for t in f.tools
                     if isinstance(t, HoverTool)]
            assert len(tools) == 1, tools
            assert _fields(tools[0]) == {"mpg", "weight", "y2plain",
                                         "foreign"}, tools[0].tooltips
        spec, df = self._spec_and_df()
        monkeypatch.setattr(tp, "_DF", df)
        r, _w = tp._standalone(spec)
        doc, _w2 = tp._served(spec)
        for figs in (_saved_figures(r), _served_figures(doc)):
            for fig in figs:
                for t in fig.tools:
                    if isinstance(t, HoverTool):
                        assert "<img" not in str(t.tooltips), t.tooltips
                        # `self._BAD not in _fields(t)' stood here, and
                        # could not fail: _fields reads up to the first
                        # `}', so it never returns a string holding one,
                        # and _BAD holds one.  A field built from the name
                        # reads what BokehJS would, "x" -- a column no
                        # renderer carries.  Every field must be one its
                        # renderers carry, and never the hostile column.
                        # (Measured 24sep2026 at a2c7502: dash built no
                        # tooltip for this figure at all, in either mode;
                        # it now builds one of the three plain ends --
                        # test_the_tooltip_is_kept_and_the_column_named.)
                        carried = set()
                        for rd in (t.renderers
                                   if isinstance(t.renderers, list) else []):
                            carried |= set(rd.data_source.data)
                        fields = _fields(t)
                        assert fields and fields <= carried - {self._BAD}, (
                            f"tooltip fields {sorted(fields)} beside the "
                            f"columns its renderers carry {sorted(carried)}"
                            f": {t.tooltips}")


    # BUGS.md "A column name holding markup gets no tooltip and no note":
    # measured at a2c7502, the hostile pcspike above got no HoverTool in
    # either mode and nothing said so, where dash.sthlp says every figure
    # has tooltips.  The layer keeps its tooltip with the three plain ends,
    # and a note names the column left out, in both modes.
    _NOTE = "is not a plain name; leaving it out of the tooltip"

    def _run(self, monkeypatch, name):
        spec, df = self._spec_and_df(name)
        monkeypatch.setattr(tp, "_DF", df)
        r, w_saved, page = tp._standalone_page(spec)
        doc, w_served = tp._served(spec)
        return (r, w_saved, page), (doc, w_served)

    def test_the_tooltip_is_kept_and_the_column_named(self, monkeypatch):
        (r, w_saved, page), (doc, w_served) = self._run(monkeypatch,
                                                        self._BAD)
        for where, figs, warned in (("saved", _saved_figures(r), w_saved),
                                    ("served", _served_figures(doc),
                                     w_served)):
            tools = [t for f in figs for t in f.tools
                     if isinstance(t, HoverTool)]
            assert len(tools) == 1, f"{where}: {tools}"
            assert _fields(tools[0]) == {"mpg", "weight", "foreign"}, (
                f"{where}: {tools[0].tooltips}")
            notes = [w for w in warned if self._NOTE in w]
            assert len(notes) == 1, f"{where}: {warned}"
            assert "x}<img src=x onerror=alert(1)>" in notes[0], notes
        # Never markup on the page: the name is data there, not HTML.
        assert "<img src=x onerror" not in page

    def test_a_long_or_control_laden_name_is_named_bounded(self,
                                                           monkeypatch):
        """Adversarial (rule 18), resource exhaustion and injection: a
        100,000-character name holding a newline, an escape character and
        markup is named in a note of bounded length, with no control
        character, and the tooltip keeps the plain ends."""
        bad = "a}\n\x1b[31m<script>alert(1)</script>" + "z" * 100_000
        (r, w_saved, _page), (doc, w_served) = self._run(monkeypatch, bad)
        for where, figs, warned in (("saved", _saved_figures(r), w_saved),
                                    ("served", _served_figures(doc),
                                     w_served)):
            notes = [w for w in warned if self._NOTE in w]
            assert len(notes) == 1, f"{where}: {[w[:200] for w in warned]}"
            assert len(notes[0]) < 300, len(notes[0])
            assert "\n" not in notes[0] and "\x1b" not in notes[0]
            tools = [t for f in figs for t in f.tools
                     if isinstance(t, HoverTool)]
            assert len(tools) == 1
            assert _fields(tools[0]) == {"mpg", "weight", "foreign"}
            assert "<script" not in str(tools[0].tooltips)


class TestTooltipsBesideADataLayer:
    """A data layer's comprehensive tooltip is unchanged: a fit beside a
    scatter still answers through the scatter's tooltip alone (test_glyphs
    BF-11c), in both modes."""

    @pytest.mark.parametrize("fit", ["lowess", "lfitci"])
    def test_one_tooltip_bound_to_the_scatter(self, fit):
        spec = tp._spec([plot_for("scatter"), plot_for(fit)])
        r, _w = tp._standalone(spec)
        doc, _w2 = tp._served(spec)
        for figs in (_saved_figures(r), _served_figures(doc)):
            (fig,) = figs
            tools = [t for t in fig.tools if isinstance(t, HoverTool)]
            assert len(tools) == 1
            assert "mpg" in _fields(tools[0])

    def test_a_second_data_layer_names_its_own_variables(self):
        """A pcspike beside a scatter is a layer of observations with its
        own variables (mpg weight price foreign): it has a tooltip of its
        own naming them, where it was bound to the scatter's weight and
        mpg (BUGS.md, 24sep2026)."""
        spec = tp._spec([plot_for("scatter"), plot_for("pcspike")])
        r, _w = tp._standalone(spec)
        doc, _w2 = tp._served(spec)
        for figs in (_saved_figures(r), _served_figures(doc)):
            (fig,) = figs
            tools = [t for t in fig.tools if isinstance(t, HoverTool)]
            assert len(tools) == 2
            by_glyph = {type(t.renderers[0].glyph).__name__: _fields(t)
                        for t in tools}
            assert "mpg" in by_glyph["Scatter"]
            assert "price" not in by_glyph["Scatter"]
            for v in ("weight", "mpg", "foreign", "price"):
                assert v in by_glyph["Segment"], by_glyph


# ===========================================================================
# 7. Sub-options named one level down (item 5), in both modes
# ===========================================================================

def _warned(spec):
    _r, std_w = tp._standalone(spec)
    _doc, srv_w = tp._served(spec)
    return std_w, srv_w


@pytest.mark.parametrize("option", ["title", "subtitle", "note", "caption"])
def test_a_textbox_suboption_dash_lacks_is_named(option):
    """title(), subtitle(), note() and caption() are in the help's list of
    options whose unimplemented sub-options are named; the textbox options
    had no test of their own."""
    spec = tp._spec([plot_for("scatter")],
                    graph_options={option: "T, orientation(vertical)"})
    std_w, srv_w = _warned(spec)
    for where, ws in (("saved", std_w), ("served", srv_w)):
        hits = [w for w in ws if f"dash: {option}() sub-option(s) not "
                f"implemented and ignored: orientation(vertical)" in w]
        assert len(hits) == 1, (where, ws)


@pytest.mark.parametrize("ptype, option, value", [
    ("scatter", "bwidth", "3"),
    ("scatter", "n", "50"),
    ("scatter", "bands", "4"),
    ("line", "base", "2"),
])
def test_an_option_on_a_plot_type_that_does_not_take_it_is_ignored(
        ptype, option, value):
    """Item 5 names the one kind of option still dropped without a word
    (WP-23): an option dash honours on some plot types, given on one that
    does not take it.  Measured 23sep2026 on the WP-23 tree: twoway refuses
    each of these with r(198); dash registers it (rc 0, no note), the spec
    carries it, and both renderers draw the layer and say nothing.  When
    dash is made to refuse or name them, this test and the help's sentence
    change together.

    Flipped (WP-31 C3): twoway refuses bwidth(), n() and bands() on
    scatter and base() on line, r(198) "option <opt>() not allowed", and
    dash now refuses them there before any spec is written
    (test_option_validation.cscript U04-01).  A hand-written spec carrying
    one is still drawn in silence by both renderers; the help's sentence
    says the option is refused, not dropped."""
    spec = tp._spec([dict(plot_for(ptype), options={option: value})])
    std_w, srv_w = _warned(spec)
    for where, ws in (("saved", std_w), ("served", srv_w)):
        assert not [w for w in ws if option in w], (where, ws)
    text = _prose(_differences())
    assert "One kind of option is still dropped without a word" not in text
    assert ("is accepted only on the plot types twoway accepts it on and "
            "refused on any other") in text
    assert "Nothing is ever dropped without being named" not in text


def test_legend_garbage_is_named_in_both_modes():
    """Option values item: twoway refuses legend(garbage), r(198)
    (HC1-15); dash names it in its sub-option note and draws without."""
    spec = tp._spec([plot_for("scatter"), plot_for("lfit")],
                    graph_options={"legend": "garbage"})
    std_w, srv_w = _warned(spec)
    for where, ws in (("saved", std_w), ("served", srv_w)):
        hits = [w for w in ws if "dash: legend() sub-option(s) not "
                "implemented and ignored: garbage" in w]
        assert len(hits) == 1, (where, ws)


# ===========================================================================
# 8. A graph's own qualifier reaches every layer, in both modes
# ===========================================================================
#
# twoway, measured (test_help_claims_1.cscript HC1-01, HC1-05):
#     twoway (scatter mpg weight if mpg>25) (line mpg weight) if foreign==1
# draws 7 of auto's 22 foreign cars in the scatter and all 22 in the line: a
# qualifier after the plot groups applies to every plot, on top of a plot's
# own.  dash.ado now writes it as the graph's if_expr/in_expr.  Here, over
# test_mode_parity's ten rows (foreign==1 at rows 2 4 6 8 10, mpg 17 30 19
# 28 23), the renderers must draw the same arithmetic.

def _layer_mpgs(figs):
    """The mpg values each glyph renderer draws, per renderer, in order."""
    out = []
    for fig in figs:
        for rd in fig.renderers:
            data, idx = tp._drawn(rd)
            if not data or "mpg" not in data:
                continue
            out.append(sorted(float(data["mpg"][i]) for i in idx))
    return out


class TestTheGraphQualifierReachesEveryLayer:

    def _both(self, spec):
        r, _w = tp._standalone(spec)
        doc, _w2 = tp._served(spec)
        return _layer_mpgs(_saved_figures(r)), _layer_mpgs(
            _served_figures(doc))

    def test_an_if_after_the_plot_groups(self):
        spec = tp._spec([plot_for("scatter", if_expr="mpg>20"),
                         plot_for("line")], if_expr="foreign==1")
        for layers in self._both(spec):
            assert [17.0, 19.0, 23.0, 28.0, 30.0] in layers, layers
            assert [23.0, 28.0, 30.0] in layers, layers
            assert all(set(v) <= {17.0, 19.0, 23.0, 28.0, 30.0}
                       for v in layers), layers

    def test_an_in_after_the_plot_groups(self):
        """twoway (scatter y x in 1/5) (line y x) in 2/8: the scatter draws
        rows 2-5, the line rows 2-8 (HC1 measured 20 and 40 of auto's rows
        for in 1/30 and in 11/50)."""
        spec = tp._spec([plot_for("scatter", in_expr="1/5"),
                         plot_for("line")], in_expr="2/8")
        rows_2_8 = sorted(tp._DF["mpg"].iloc[1:8].tolist())
        rows_2_5 = sorted(tp._DF["mpg"].iloc[1:5].tolist())
        for layers in self._both(spec):
            assert rows_2_8 in layers, layers
            assert rows_2_5 in layers, layers


def _move_to_foreign(spec):
    """The served document after its dropdown is moved to Foreign."""
    doc, _w = tp._served(spec)
    (w,) = [x for x in tp._widgets_of(doc) if type(x).__name__ == "Select"]
    (raw,) = [v for v, lab in w.options if lab == "Foreign"]
    tp._fire(w, raw)
    return doc


class TestAFilterMoveCountsObservations:
    """A served filter move redraws a layer whose source the mapper built --
    a line in its join order, a fit -- from the rows the widget leaves.  An
    ``in`` must still count the dataset's observations there: the redraw
    applied the graph's ``in``, and a layer's own, by position to the
    filtered rows (measured 23sep2026: with in 2/8 and the dropdown on
    Foreign, the redrawn line took the foreign cars at positions 2-8 of the
    five left -- observations 4, 6, 8 and 10 -- where twoway's in 2/8 holds
    observations 2, 4, 6 and 8)."""

    _FOREIGN_2_8 = sorted(float(tp._DF["mpg"][i]) for i in range(1, 8)
                          if tp._DF["foreign"][i] == 1)
    _FOREIGN_1_5 = sorted(float(tp._DF["mpg"][i]) for i in range(0, 5)
                          if tp._DF["foreign"][i] == 1)

    def test_the_graphs_in(self):
        spec = tp._spec([plot_for("line")],
                        build_options={"filter": "foreign, type(dropdown)"},
                        in_expr="2/8")
        layers = _layer_mpgs(_served_figures(_move_to_foreign(spec)))
        assert self._FOREIGN_2_8 in layers, layers

    def test_a_layers_own_in(self):
        spec = tp._spec([plot_for("line", in_expr="1/5"),
                         plot_for("scatter")],
                        build_options={"filter": "foreign, type(dropdown)"})
        layers = _layer_mpgs(_served_figures(_move_to_foreign(spec)))
        assert self._FOREIGN_1_5 in layers, layers

    def test_the_saved_page_draws_the_same_rows_to_begin_with(self):
        """The saved renderer, given the widget's selection as an if, draws
        the rows the served move leaves: its own oracle for a move."""
        spec = tp._spec([plot_for("line")], in_expr="2/8",
                        if_expr="foreign==1")
        r, _w = tp._standalone(spec)
        assert self._FOREIGN_2_8 in _layer_mpgs(_saved_figures(r))
