"""WP-17 TR-17.1: one scheme rule on every entry point, and one shipped list.

Measured 22sep2026 (scratchpad wp17/probe, `mytheme.scheme` = a copy of
s1rcolor in the working directory):

* ``dash scatter mpg weight, scheme(mytheme)`` warned that 'mytheme' "is not
  a known theme or scheme", drew the FIGURE with mytheme (the per-graph swap
  resolves the file) and the page chrome with s2color: the body was
  ``#eaf2f3`` and the heading rule ``#1e2d53``.  Half applied.
* ``dash build, scheme(mytheme)`` warned and drew s2color everywhere.
* ``scheme(mytheme.scheme)`` worked on both.
* ``set scheme s2color8`` then any dash: warned, s2color -- and cscript sets
  s2color8 for every session, so eleven of twelve certification logs carried
  the warning.

Cause: ``_resolve_scheme_name`` rejected any name that was neither a theme
alias nor a builtin unless it ended in ".scheme", before
``SchemeParser._resolve_path`` -- whose bare-name branch tries
``<cwd>/<name>.scheme`` first -- could run.

The contract (DESIGN §2): a scheme is named by one of the twenty shipped
translations, a theme alias, or a ``.scheme`` file in the working directory
given by bare name or with the extension; the same rule on every entry
point.  An explicit unresolvable name is refused in Stata before Python
(Owner C, test_custom_scheme.cscript); when a name still reaches the
renderer unresolved -- the session's ``c(scheme)``, or a spec built without
dash.ado -- ONE warning names that cause and s2color is drawn.  The gate
asks ``SchemeParser.can_resolve`` before it warns.

Rendering goes through test_mode_parity's spec and file helpers, in both
modes, in a tmp working directory that holds the custom file.
"""
import ast
import inspect
import json
import os
import re
import sys
import warnings

import pytest
from bokeh.document import Document
from bokeh.io import curdoc
from bokeh.models import Div, GlyphRenderer, Plot

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

#: The twenty-six StataCorp schemes dash ships as translations (DESIGN §2):
#: the fourteen of WP-16, the six user-selectable ones that were missing,
#: plus StataCorp's six internal schemes (WP-30 P1.25a).
SHIPPED = (
    "economist", "s1color", "s1manual", "s1mono", "s1rcolor",
    "s2color", "s2color8", "s2gcolor", "s2gmanual", "s2manual", "s2mono",
    "sj", "stcolor", "stcolor_alt", "stgcolor", "stgcolor_alt",
    "stmono1", "stmono2", "stsj", "sttrans",
    # WP-30 P1.25a: StataCorp's six internal schemes
    "meta", "stcolor_meta", "stcolor_mv", "stcoloralias", "stgcolor_meta",
    "stgcolor_mv",
)
THEMES = ("clean", "dark", "default", "economist", "mono", "sj")
MODES = ("standalone", "served")

#: The custom file is s1rcolor with one line changed, so its every other
#: value is a shipped one and only this colour can prove it was read.
CUSTOM_BG = "#123456"
#: s2color's `color heading': what the half-applied page chrome carried.
S2COLOR_HEADING = "#1e2d53"

#: The one sentence the unknown-name warning must add (DESIGN §3 B).
INHERITED = (
    "it was inherited from the session (c(scheme)) because no scheme() or "
    "theme() was given, or came from a spec built without dash.ado"
)

_SENTINEL_BEGIN = "// BEGIN shipped schemes (WP-17)"


def each(argnames, values):
    """Run a check once per value inside ONE test, each value a subtest.

    The decorated function takes *argnames* (comma-separated, like
    ``pytest.mark.parametrize``) plus any fixtures; the test pytest sees
    takes the fixtures and ``subtests`` instead.  Every value is still
    checked and every mismatch reported, without a test item per value --
    for checks that run the same code path for every value."""
    names = [n.strip() for n in argnames.split(",")]

    def deco(check):
        sig = inspect.signature(check)
        params = [q for q in sig.parameters.values() if q.name not in names]
        if "subtests" not in sig.parameters:
            params.append(inspect.Parameter(
                "subtests", inspect.Parameter.POSITIONAL_OR_KEYWORD))

        def run(*args, **kwargs):
            sub = kwargs["subtests"]
            if "subtests" not in sig.parameters:
                del kwargs["subtests"]
            for v in values:
                vals = dict(zip(names, v if len(names) > 1 else (v,)))
                with sub.test(msg=", ".join(f"{k}={x!r}"
                                            for k, x in vals.items())):
                    check(*args, **vals, **kwargs)
        run.__name__ = check.__name__
        run.__qualname__ = check.__qualname__
        run.__doc__ = check.__doc__
        run.__signature__ = sig.replace(parameters=params)
        return run
    return deco
_SENTINEL_END = "// END shipped schemes (WP-17)"


# ---------------------------------------------------------------------------
# The working directory with a custom scheme in it
# ---------------------------------------------------------------------------

@pytest.fixture
def custom_cwd(tmp_path, monkeypatch):
    """A tmp working directory holding ``mytheme.scheme``: dash-s1rcolor.scheme
    with its ``color background`` line replaced by CUSTOM_BG."""
    src = os.path.join(_ROOT, "dash-s1rcolor.scheme")
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    new, n = re.subn(r"(?m)^color background\s+\S+",
                     f"color background      {CUSTOM_BG}", text)
    assert n == 1, f"s1rcolor.scheme has {n} `color background' lines"
    (tmp_path / "mytheme.scheme").write_text(new, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Rendering, both modes, with every warning recorded
# ---------------------------------------------------------------------------

def _standalone(spec):
    """(renderer, page html, warnings) from the saved-dashboard renderer.

    test_mode_parity's ``_standalone`` discards the page; the page is where
    the half-application showed (the css block is written into it)."""
    _, sp, dp = tp._write(spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        page = r.render()
    curdoc().clear()
    return r, page, sorted(str(w.message) for w in caught)


def _served(spec):
    """(document, module, warnings) from the generated server app, built
    the way test_scheme_rendered_output's ``_served_with_module`` builds it
    but with the build-time and document-time warnings kept."""
    tag, sp, dp = tp._write(spec)
    ap = os.path.join(tp._TMP, f"app_{tag}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, f"_resolution_{tag}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    curdoc().clear()
    msgs = sorted(str(w.message) for w in list(built) + list(caught))
    return doc, mod, msgs


class _Drawn:
    """What one mode drew: its figures, its scheme, its KPI Divs' inline
    stylesheets and (standalone) its page."""

    def __init__(self, figures, scheme, div_css, page, warnings_):
        self.figures = figures
        self.scheme = scheme
        self.div_css = div_css
        self.page = page
        self.warnings = warnings_

    @property
    def fig(self):
        assert len(self.figures) == 1, f"{len(self.figures)} figures"
        return self.figures[0]

    @property
    def css(self):
        return self.scheme.css_block()


def _div_css(divs):
    return [ss.css for d in divs for ss in (d.stylesheets or [])
            if hasattr(ss, "css")]


def _draw(spec, mode):
    if mode == "standalone":
        r, page, msgs = _standalone(spec)
        return _Drawn(list(r.figures.values()), r.scheme,
                      _div_css(r.kpi_divs.values()), page, msgs)
    doc, mod, msgs = _served(spec)
    figs = list(doc.select(dict(type=Plot)))
    return _Drawn(figs, mod._DASH_SCHEME,
                  _div_css(doc.select(dict(type=Div))), None, msgs)


def _spec(build_options=None, graph_options=None, kpi=True):
    return tp._spec([plot_for("scatter")], build_options or {},
                    graph_options or {}, kpis=[tp._kpi()] if kpi else None)


# ---------------------------------------------------------------------------
# A .scheme file in the working directory, on every entry point
# ---------------------------------------------------------------------------

#: (id, build_options, graph_options): the three ways the probe named the
#: custom file.  A build-level scheme is build_options["scheme"]; a
#: graph-level one -- the immediate route, `dash scatter ..., scheme()' --
#: is graph_options["scheme"].
ENTRY_POINTS = [
    ("build_bare", {"scheme": "mytheme"}, {}),
    ("build_file", {"scheme": "mytheme.scheme"}, {}),
    ("graph_bare", {}, {"scheme": "mytheme"}),
]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("entry, bo, go", ENTRY_POINTS,
                         ids=[e[0] for e in ENTRY_POINTS])
class TestACustomSchemeInTheWorkingDirectory:
    def test_the_figure_is_drawn_with_it(self, custom_cwd, entry, bo, go,
                                         mode):
        d = _draw(_spec(bo, go), mode)
        assert d.fig.border_fill_color == CUSTOM_BG, (
            f"[{entry}, {mode}] the figure's canvas is "
            f"{d.fig.border_fill_color!r}, not the custom scheme's "
            f"{CUSTOM_BG}")

    def test_the_page_chrome_is_drawn_with_it(self, custom_cwd, entry, bo,
                                              go, mode):
        """The half-application: the css block -- body background, heading
        and KPI card rules -- came from s2color while the figure did not."""
        d = _draw(_spec(bo, go), mode)
        assert CUSTOM_BG in d.css, (
            f"[{entry}, {mode}] css_block() carries no {CUSTOM_BG}:\n{d.css}")
        assert S2COLOR_HEADING not in d.css, (
            f"[{entry}, {mode}] css_block() is s2color's:\n{d.css}")
        assert d.scheme.name == "mytheme", d.scheme.name
        assert d.div_css, f"[{entry}, {mode}] no KPI Div carries a stylesheet"
        assert all(CUSTOM_BG in c for c in d.div_css), (
            f"[{entry}, {mode}] a KPI Div's stylesheet is not the custom "
            f"scheme's: {d.div_css}")
        if d.page is not None:
            assert CUSTOM_BG in d.page
            assert S2COLOR_HEADING not in d.page, (
                f"[{entry}] the saved page still carries s2color's heading "
                f"colour {S2COLOR_HEADING}")

    def test_it_is_applied_without_a_warning(self, custom_cwd, entry, bo,
                                             go, mode):
        d = _draw(_spec(bo, go), mode)
        assert d.warnings == [], (
            f"[{entry}, {mode}] a resolvable scheme warned: {d.warnings}")


@pytest.mark.parametrize("entry, bo, go", ENTRY_POINTS,
                         ids=[e[0] for e in ENTRY_POINTS])
class TestBothModesAgreeOnTheCustomScheme:
    def test_same_chrome_and_same_figure(self, custom_cwd, entry, bo, go):
        a = _draw(_spec(bo, go), "standalone")
        b = _draw(_spec(bo, go), "served")
        assert a.css == b.css, (
            f"[{entry}] the two modes' css blocks differ:\n{a.css}\n--\n"
            f"{b.css}")
        assert (a.fig.border_fill_color, a.fig.background_fill_color) == \
            (b.fig.border_fill_color, b.fig.background_fill_color)
        assert a.scheme.name == b.scheme.name == "mytheme"


# ---------------------------------------------------------------------------
# can_resolve
# ---------------------------------------------------------------------------

class TestCanResolve:
    def _quiet(self, name):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ok = dr.SchemeParser.can_resolve(name)
        assert not caught, f"can_resolve({name!r}) warned: " + "; ".join(
            str(w.message) for w in caught)
        return ok

    def test_a_bare_name_in_the_working_directory(self, custom_cwd):
        assert self._quiet("mytheme") is True

    def test_a_file_name_in_the_working_directory(self, custom_cwd):
        assert self._quiet("mytheme.scheme") is True

    def test_a_traversal_is_false_and_raises_nothing(self, custom_cwd):
        assert self._quiet("../x") is False
        assert self._quiet("../mytheme") is False
        assert self._quiet("../mytheme.scheme") is False

    def test_an_absolute_path_is_false(self, custom_cwd):
        assert self._quiet("/etc/passwd") is False

    def test_an_unknown_name_is_false(self, custom_cwd):
        assert self._quiet("nosuchthing") is False
        assert self._quiet("nosuchthing.scheme") is False

    def test_an_empty_name_is_false(self):
        assert self._quiet("") is False
        assert self._quiet(None) is False

    @each("name", SHIPPED)
    def test_every_shipped_scheme_is_true(self, name):
        assert self._quiet(name) is True, f"{name} does not resolve"

    def test_a_theme_alias_is_not_a_scheme_name(self):
        """Aliases are the gate's business, not the parser's: no file is
        called dark.scheme."""
        assert self._quiet("dark") is False


# ---------------------------------------------------------------------------
# An unresolvable name: one warning that says why it can happen
# ---------------------------------------------------------------------------

def _resolve(build_options, graphs=None):
    bo = {"scheme": "", "theme": "", "session_scheme": ""}
    bo.update(build_options)
    spec = {"graphs": graphs or [], "kpis": [], "build_options": bo}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        name = dr._resolve_scheme_name(spec)
    return name, [str(w.message) for w in caught]


def _assert_unknown_warning(msg, raw):
    assert msg.startswith(
        f"dash: {raw!r} is not a known theme or scheme; "), msg
    assert INHERITED in msg, msg
    assert "; using s2color. " in msg, msg
    assert "Themes: " + ", ".join(THEMES) + ". " in msg, msg
    assert "Schemes: " + ", ".join(sorted(SHIPPED)) + "." in msg, msg
    assert "\n" not in msg, "the warning must be one line"


class TestAnUnresolvableNameIsReportedOnce:
    def test_scheme_nosuchthing_from_a_spec_dict(self, custom_cwd):
        name, msgs = _resolve({"scheme": "nosuchthing"})
        assert name == "s2color"
        assert len(msgs) == 1, msgs
        _assert_unknown_warning(msgs[0], "nosuchthing")

    def test_theme_nosuchtheme_from_a_spec_dict(self):
        name, msgs = _resolve({"theme": "nosuchtheme"})
        assert name == "s2color"
        assert len(msgs) == 1, msgs
        _assert_unknown_warning(msgs[0], "nosuchtheme")

    def test_the_session_scheme_is_the_case_the_sentence_names(self):
        """What the certification logs carried: cscript's s2color8 was the
        session scheme and dash did not ship it.  s2color8 ships now, so
        the case is made with a name that no package translates."""
        name, msgs = _resolve({"session_scheme": "zzdashtest"})
        assert name == "s2color"
        assert len(msgs) == 1, msgs
        _assert_unknown_warning(msgs[0], "zzdashtest")

    def test_a_scheme_file_that_does_not_exist(self, custom_cwd):
        """The old gate let any name ending in .scheme through untouched and
        the parser's fallback reported it later with different words; the
        gate now asks can_resolve, so the report is the same one."""
        name, msgs = _resolve({"scheme": "nosuch.scheme"})
        assert name == "s2color"
        assert len(msgs) == 1, msgs
        _assert_unknown_warning(msgs[0], "nosuch.scheme")

    def test_a_traversal_is_unresolvable_not_an_error(self, custom_cwd):
        name, msgs = _resolve({"scheme": "../mytheme"})
        assert name == "s2color"
        assert len(msgs) == 1, msgs
        _assert_unknown_warning(msgs[0], "../mytheme")

    def test_a_graph_level_unknown_name(self, custom_cwd):
        graphs = [{"name": "g1", "plots": [plot_for("scatter")],
                   "graph_options": {"name": "g1", "scheme": "nosuchthing"}}]
        name, msgs = _resolve({}, graphs)
        assert name == "s2color"
        assert len(msgs) == 1, msgs
        _assert_unknown_warning(msgs[0], "nosuchthing")

    @pytest.mark.parametrize("mode", MODES)
    def test_a_build_level_unknown_name_warns_once_through_a_render(
            self, custom_cwd, mode):
        d = _draw(_spec({"scheme": "nosuchthing"}), mode)
        assert d.scheme.name == "s2color"
        assert d.scheme.is_fallback is False
        unknown = [m for m in d.warnings if "nosuchthing" in m]
        assert len(unknown) == 1, d.warnings
        _assert_unknown_warning(unknown[0], "nosuchthing")

    def test_a_resolvable_name_is_not_reported(self, custom_cwd):
        for raw in ("mytheme", "mytheme.scheme", "s2color8", "dark",
                    "DARK", "Economist"):
            name, msgs = _resolve({"scheme": raw})
            assert msgs == [], f"{raw!r} warned: {msgs}"
            assert name, raw

    @pytest.mark.parametrize("raw, want", [
        ("Economist", "economist"), ("S2COLOR8", "s2color8"),
        ("StColor_Alt", "stcolor_alt"), ("mytheme", "mytheme"),
        # A shipped name with the extension, in any case: dash.ado's gate
        # strips ".scheme" before its shipped-list test, so these reach
        # Python; _resolve_path used to test the extension case-sensitively
        # and treat "S2COLOR.SCHEME" as a bare name no file answers to.
        ("s2color.scheme", "s2color"), ("S2COLOR.SCHEME", "s2color"),
        ("StColor_Alt.Scheme", "stcolor_alt"),
    ])
    def test_a_shipped_name_is_handed_on_in_lower_case(self, custom_cwd,
                                                       raw, want):
        """dash.ado's gate accepts a shipped name in any case (lower(V) in
        _dash_schemes) and passes V through unchanged.  The gate here
        accepted it the same way and then handed the raw spelling to the
        parser, which looks for a FILE of that name: on this machine's
        case-insensitive filesystem it resolved and `scheme.name' echoed
        the caller's spelling; on a case-sensitive one it would have fallen
        back with a warning.  A user file keeps its spelling."""
        name, msgs = _resolve({"scheme": raw})
        assert msgs == [], msgs
        assert name == want, (raw, name)


# ---------------------------------------------------------------------------
# One list, everywhere it is written
# ---------------------------------------------------------------------------

def _extractor_schemes():
    """The extractor's ``SCHEMES`` list, read from its source with ``ast``:
    executing the script would write scripts/__pycache__, which is not
    ignored, and the list is a literal."""
    path = os.path.join(_ROOT, "scripts", "extract_scheme_truth.py")
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "SCHEMES"):
            return ast.literal_eval(node.value)
    raise AssertionError("no module-level `SCHEMES = [...]' in the extractor")


def _ado_block():
    with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
        text = fh.read()
    i, j = text.find(_SENTINEL_BEGIN), text.find(_SENTINEL_END)
    if i < 0 or j < 0 or j < i:
        return None
    block = text[i + len(_SENTINEL_BEGIN):j]
    # Stata's `///' joins the next line; a list may be wrapped that way.
    return re.sub(r"\s*///[^\n]*\n\s*", " ", block)


def _ado_list(block, macro):
    m = re.search(r"c_local\s+%s\s+`?\"([^\"]*)\"'?" % macro, block)
    assert m, f"no `c_local {macro} \"...\"' between the WP-17 sentinels"
    return m.group(1).split()


class TestTheShippedListIsOneList:
    def test_the_parser_ships_the_twenty(self):
        assert set(dr.SchemeParser._BUILTIN_NAMES) == set(SHIPPED), (
            sorted(set(dr.SchemeParser._BUILTIN_NAMES) ^ set(SHIPPED)))
        assert len(SHIPPED) == 26  # 20 -> 26: P1.25a ships the six StataCorp schemes

    def test_the_extractor_agrees(self):
        assert set(_extractor_schemes()) == set(SHIPPED)

    def test_the_fidelity_suite_agrees(self):
        import test_scheme_fidelity as tf
        assert set(tf.EXPECTED_SCHEMES) == set(SHIPPED)

    def test_the_theme_map_agrees(self):
        assert set(dr._THEME_SCHEME_MAP) == set(THEMES)
        assert set(dr._THEME_SCHEME_MAP.values()) <= set(SHIPPED)

    def test_dash_ado_agrees(self):
        """A structural guard over dash.ado's text, deliberately: two lists
        of the same names, one in each language, held equal -- a name one
        side ships and the other's gate refuses shows in neither side's
        own tests (test_custom_scheme.cscript CS-12 runs one direction)."""
        block = _ado_block()
        # This skipped while Owner C's _dash_shipped_schemes had not landed.
        # It has (dash.ado carries both sentinels, measured 24sep2026), so a
        # skip now means only that someone edited a comment -- and it hid
        # the list from the one check that holds dash.ado to the parser.
        if block is None:
            pytest.fail(
                "dash.ado has no `// BEGIN shipped schemes (WP-17)' / "
                "`// END shipped schemes (WP-17)' sentinels around "
                "_dash_shipped_schemes, so its scheme list cannot be "
                "checked against SchemeParser._BUILTIN_NAMES")
        schemes = _ado_list(block, "_dash_schemes")
        themes = _ado_list(block, "_dash_themes")
        assert schemes == [s.lower() for s in schemes], schemes
        assert set(schemes) == set(SHIPPED), sorted(set(schemes) ^ set(SHIPPED))
        assert len(schemes) == len(set(schemes)), "a name is listed twice"
        assert set(themes) == set(THEMES), sorted(set(themes) ^ set(THEMES))

    @each("name", SHIPPED)
    def test_every_shipped_name_has_a_file(self, name):
        assert os.path.isfile(
            os.path.join(_ROOT, f"dash-{name}.scheme")), name


# ---------------------------------------------------------------------------
# Every shipped scheme resolves without a word, in both modes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestEveryShippedSchemeResolves:
    @each("name", SHIPPED)
    def test_by_name(self, name, mode):
        d = _draw(_spec({"scheme": name}, kpi=False), mode)
        assert d.scheme.name == name, (name, d.scheme.name)
        assert d.scheme.is_fallback is False
        assert d.warnings == [], f"{name} [{mode}] warned: {d.warnings}"

    @each("name", SHIPPED)
    def test_as_the_session_scheme(self, name, mode):
        """`set scheme <name>' then any dash: what cscript does with
        s2color8 in every certification session."""
        d = _draw(_spec({"session_scheme": name}, kpi=False), mode)
        assert d.scheme.name == name, (name, d.scheme.name)
        assert d.warnings == [], f"{name} [{mode}] warned: {d.warnings}"


# ---------------------------------------------------------------------------
# A colour's declared opacity is drawn: sttrans's %20, in both modes
# ---------------------------------------------------------------------------
#
# Measured 22sep2026 in Stata's own SVG export (scratchpad wp17/ownerA/a.svg,
# wp17/B2/{l,b,a,h,c,s,s2}.svg; `twoway <plot> ..., scheme(sttrans)'):
# scheme-sttrans.scheme declares every p# colour as `"26 71 111 %20"', and
# Stata draws a scatter's markers with fill-opacity 0.20 AND stroke-opacity
# 0.20, a line with stroke-opacity 0.20, a bar and an area with both at
# 0.20, a histogram's bars at fill-opacity 0.20, and connected's line and
# markers at 0.20.  `mcolor(red)' keeps the 0.20 (the opacity is not part
# of the colour the option replaces); `mcolor(red%50)' draws 0.50.
#
# The shipped schemes/sttrans.scheme writes the colours as `#1a476f%20',
# and the fixture records p_colors_opacity, but SchemeParser._color went
# through translate_mcolor, which strips the suffix, so dash drew sttrans
# opaque: a scatter at the intensity-derived 0.8 like every other scheme.
#
# Stata's `intensity p inten80' is a lightening towards the background,
# which dash approximates as alpha; a declared %NN IS an opacity.  When the
# scheme declares one it is the real value and wins over the approximation;
# a user colour with its own %NN still wins over both.

#: What Stata draws sttrans's p# colours at (fill-opacity 0.20).
STTRANS_ALPHA = 0.2
OTHER_SCHEMES = tuple(n for n in SHIPPED if n != "sttrans")

#: parser list -> fixture list (Stata's percent, or None) it must agree with.
ALPHA_LISTS = {
    "p_alphas":          "p_colors_opacity",
    "p_line_alphas":     "p_line_colors_opacity",
    "p_bar_alphas":      "p_bar_colors_opacity",
    "p_mark_alphas":     "p_mark_colors_opacity",
    "p_markline_alphas": "p_markline_colors_opacity",
    "p_lineplot_alphas": "p_lineplot_colors_opacity",
}

#: Glyph class -> (fill_alpha, line_alpha) every shipped scheme other than
#: sttrans drew on 22sep2026, captured before this change (scratchpad
#: wp17/B2/capture.py, both modes agreed): the intensity-derived values.
#: A Line has no fill and a VArea no line.  Since WP-30 P1.2b markers are
#: opaque, as twoway draws them (they were 0.8, the scheme's `intensity p'
#: read as an alpha), and an intensity is a colour, never an alpha, so
#: s1rcolor's bar and histogram (0.8 from graph bar's `intensity bar') are
#: opaque too: no scheme is an exception (twoway's SVG, plan section 16
#: Evidence E3).
PINNED_ALPHAS = {
    "Scatter": (1.0, 1.0),
    "Line":    (None, 1.0),
    "VBar":    (1.0, 1.0),
    "VArea":   (1.0, None),
    "Quad":    (1.0, 1.0),
}
PINNED_EXCEPTIONS = {}

#: The five plot types whose mapper site reads a scheme alpha, one graph
#: each, told apart afterwards by the glyph class they draw.
_ALPHA_PLOTS = ("scatter", "line", "bar", "area", "histogram")


def _fixture():
    path = os.path.join(_ROOT, "test", "fixtures", "scheme_truth.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _props_scheme(props):
    """A SchemeParser rebuilt from a property dict with no file behind it,
    exactly as the generated server app rebuilds its scheme."""
    s = dr.SchemeParser.__new__(dr.SchemeParser)
    s._props = dict(props)
    s.name = "props"
    s.is_fallback = False
    s._init_properties()
    return s


def _glyphs(fig):
    return [r.glyph for r in fig.renderers if isinstance(r, GlyphRenderer)]


def _alpha_of(glyph):
    return (getattr(glyph, "fill_alpha", None), getattr(glyph, "line_alpha", None))


def _alphas_by_glyph(name, mode):
    """{glyph class: (fill_alpha, line_alpha)} of the first glyph of each of
    the five plots, drawn under scheme *name* in *mode* as five graphs of
    one dashboard."""
    graphs = [(f"g_{p}", [plot_for(p)], {}, {}) for p in _ALPHA_PLOTS]
    spec = tp._spec(graphs=graphs, build_options={"scheme": name})
    d = _draw(spec, mode)
    assert d.warnings == [], f"{name} [{mode}] warned: {d.warnings}"
    assert len(d.figures) == len(_ALPHA_PLOTS), len(d.figures)
    out = {}
    for fig in d.figures:
        gs = _glyphs(fig)
        assert gs, f"{name} [{mode}] a figure drew nothing"
        out[type(gs[0]).__name__] = _alpha_of(gs[0])
    assert set(out) == set(PINNED_ALPHAS), set(out)
    return out


def _one_plot(ptype, options, mode, scheme="sttrans"):
    """The glyphs of one plot drawn with *options* under *scheme*."""
    spec = tp._spec([plot_for(ptype, options)], {"scheme": scheme}, {},
                    kpis=None)
    d = _draw(spec, mode)
    assert d.warnings == [], f"[{mode}] warned: {d.warnings}"
    gs = _glyphs(d.fig)
    assert gs, f"[{mode}] {ptype} drew nothing"
    return gs


class TestTheParserCarriesTheColourOpacity:
    def test_sttrans_declares_twenty_percent_on_every_cycle(self):
        sp = dr.SchemeParser("sttrans")
        for attr in ALPHA_LISTS:
            got = getattr(sp, attr)
            assert got == pytest.approx([STTRANS_ALPHA] * 15), (attr, got)
        # The colour itself is still the plain hex the fixture records.
        assert sp.p_colors[0] == "#1a476f"

    @each("name", OTHER_SCHEMES)
    def test_every_other_shipped_scheme_declares_none(self, name):
        sp = dr.SchemeParser(name)
        for attr in ALPHA_LISTS:
            assert getattr(sp, attr) == [None] * 15, (name, attr)

    @each("name", SHIPPED)
    def test_the_fixture_agrees(self, name):
        """The extractor's p_colors_opacity (Stata's percent) is what the
        parser carries, divided by 100."""
        truth = _fixture()[name]
        sp = dr.SchemeParser(name)
        for attr, key in ALPHA_LISTS.items():
            pcts = truth[key]
            got = getattr(sp, attr)
            assert len(got) == len(pcts) == 15, (name, attr)
            for i, (pct, alpha) in enumerate(zip(pcts, got)):
                if pct is None:
                    assert alpha is None, (name, attr, i, alpha)
                else:
                    assert alpha == pytest.approx(pct / 100.0), (
                        name, attr, i, pct, alpha)

    def test_default_alpha_reads_the_cycle_default_color_reads(self):
        sp = dr.SchemeParser("sttrans")
        for ptype in ("scatter", "dot", "line", "tsline", "connected", "bar",
                      "rbar", "area", "histogram", "spike", "rcap"):
            for i in (0, 7, 14, 15, 31):
                assert sp.default_alpha(i, ptype) == pytest.approx(
                    STTRANS_ALPHA), (ptype, i)
        s2 = dr.SchemeParser("s2color")
        for ptype in ("scatter", "line", "connected", "bar", "area", "spike"):
            assert s2.default_alpha(0, ptype) is None, ptype

    def test_the_fallback_declares_none(self):
        """SchemeParser.fallback() mirrors s2color, attribute for attribute
        (test_scheme_fallback_provenance FBP-01)."""
        fb = dr.SchemeParser.fallback()
        for attr in ALPHA_LISTS:
            assert getattr(fb, attr) == [None] * 15, attr
        assert fb.default_alpha(0, "scatter") is None

    def test_a_declared_opacity_falls_through_with_its_colour(self):
        """`color p1 red%50' and nothing else: p1line, p1bar, p1mark and
        p1lineplot take p1's colour, and its opacity with it."""
        sp = _props_scheme({"color p1": "red%50"})
        assert sp.p_colors[0] == "#ff0000"
        for attr in ALPHA_LISTS:
            got = getattr(sp, attr)
            assert got[0] == pytest.approx(0.5), (attr, got[0])
            assert got[1:] == [None] * 14, attr

    def test_a_cycle_declares_its_own_opacity(self):
        sp = _props_scheme({"color p1": "red", "color p1line": "blue%30"})
        assert sp.p_alphas[0] is None
        assert sp.p_line_alphas[0] == pytest.approx(0.3)
        assert sp.p_bar_alphas[0] is None
        assert sp.p_mark_alphas[0] is None
        assert sp.p_markline_alphas[0] is None
        assert sp.p_lineplot_alphas[0] is None
        assert sp.default_alpha(0, "connected") == pytest.approx(0.3)
        assert sp.default_alpha(0, "line") is None
        assert sp.default_alpha(0, "scatter") is None

    def test_an_unknown_colour_keeps_its_opacity(self):
        """An unknown colour is black with a warning, its own %NN kept, as
        twoway draws `color p1 bogus%50' (colour_grammar_truth.json
        sch_42).  Flipped (WP-30 P1.13a): the opacity was dropped."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sp = _props_scheme({"color p1": "nosuchcolour%20"})
        assert any("nosuchcolour%20" in str(w.message) for w in caught), [
            str(w.message) for w in caught]
        assert sp.p_colors[0] == "#000000"
        assert sp.p_alphas[0] == 0.2


@pytest.mark.parametrize("mode", MODES)
class TestSttransIsDrawnTranslucent:
    def test_every_scheme_alpha_site_draws_the_declared_opacity(self, mode):
        """Scatter (fill and outline), line, bar (fill and outline), area
        and histogram (fill): what Stata's SVG carries at 0.20."""
        got = _alphas_by_glyph("sttrans", mode)
        a = STTRANS_ALPHA
        assert got["Scatter"] == pytest.approx((a, a)), got
        assert got["Line"][1] == pytest.approx(a), got
        assert got["VBar"] == pytest.approx((a, a)), got
        assert got["VArea"][0] == pytest.approx(a), got
        assert got["Quad"][0] == pytest.approx(a), got

    def test_connected_draws_both_its_line_and_its_markers_at_it(self, mode):
        line, marks = _one_plot("connected", {}, mode)
        assert type(line).__name__ == "Line" and type(marks).__name__ == "Scatter"
        assert line.line_alpha == pytest.approx(STTRANS_ALPHA)
        assert _alpha_of(marks) == pytest.approx((STTRANS_ALPHA, STTRANS_ALPHA))

    def test_a_user_mcolor_with_its_own_alpha_wins(self, mode):
        g = _one_plot("scatter", {"mcolor": "red%50"}, mode)[0]
        assert g.fill_color == "#ff0000"
        assert _alpha_of(g) == pytest.approx((0.5, 0.5))

    def test_a_user_mcolor_without_alpha_keeps_the_scheme_opacity(self, mode):
        """Measured (wp17/B2/s.svg): `mcolor(red)' under sttrans is red at
        fill-opacity 0.20 and stroke-opacity 0.20."""
        g = _one_plot("scatter", {"mcolor": "red"}, mode)[0]
        assert g.fill_color == "#ff0000"
        assert _alpha_of(g) == pytest.approx((STTRANS_ALPHA, STTRANS_ALPHA))

    def test_a_user_fcolor_with_its_own_alpha_wins_on_a_bar(self, mode):
        g = _one_plot("bar", {"fcolor": "red%60"}, mode)[0]
        # Red at the bar's intensity, inten80, keeping its own %60
        # (twoway: fcolor(navy%50) is #486C8C at 0.50; WP-30 P1.2b, plan
        # section 16 Evidence E3).
        assert g.fill_color == "#ff3333"
        assert g.fill_alpha == pytest.approx(0.6)

    def test_a_user_lcolor_with_its_own_alpha_wins_on_a_line(self, mode):
        g = _one_plot("line", {"lcolor": "red%70"}, mode)[0]
        assert g.line_color == "#ff0000"
        assert g.line_alpha == pytest.approx(0.7)


class TestBothModesAgreeOnTheOpacity:
    def test_sttrans(self):
        assert _alphas_by_glyph("sttrans", "standalone") == \
            _alphas_by_glyph("sttrans", "served")

    def test_the_served_scheme_carries_the_lists(self):
        _, mod, msgs = _served(tp._spec([plot_for("scatter")],
                                        {"scheme": "sttrans"}, {}, kpis=None))
        assert msgs == []
        for attr in ALPHA_LISTS:
            assert getattr(mod._DASH_SCHEME, attr) == pytest.approx(
                [STTRANS_ALPHA] * 15), attr


@pytest.mark.parametrize("mode", MODES)
class TestEveryOtherSchemeIsUnchanged:
    @each("name", OTHER_SCHEMES)
    def test_the_alphas_are_what_they_were(self, name, mode):
        got = _alphas_by_glyph(name, mode)
        want = {cls: PINNED_EXCEPTIONS.get((name, cls), v)
                for cls, v in PINNED_ALPHAS.items()}
        assert got == want, (name, mode, got, want)


# ---------------------------------------------------------------------------
# WP-28: the shipped schemes are dash-<name>.scheme in the package root
# ---------------------------------------------------------------------------

def _layout(tmp_path, kind):
    """Stage dash_render.py with every shipped ``dash-<name>.scheme`` beside it
    (``kind == "source"``, the repo layout) or as a ``net install`` files
    them (``kind == "installed"``: ``PLUS/py/dash_render.py`` and
    ``PLUS/d/dash-<name>.scheme``).  Returns (module name, module, dir the
    shipped files are in, an empty working directory)."""
    import shutil
    from test_packaging import load_staged_render
    if kind == "source":
        code_dir = files_dir = tmp_path / "src"
        code_dir.mkdir()
    else:
        code_dir = tmp_path / "plus" / "py"
        files_dir = tmp_path / "plus" / "d"
        code_dir.mkdir(parents=True)
        files_dir.mkdir()
    shutil.copy2(os.path.join(_ROOT, "dash_render.py"),
                 str(code_dir / "dash_render.py"))
    for name in SHIPPED:
        shutil.copy2(os.path.join(_ROOT, f"dash-{name}.scheme"),
                     str(files_dir / f"dash-{name}.scheme"))
    cwd = tmp_path / "work"
    cwd.mkdir()
    mod_name, mod = load_staged_render(str(code_dir))
    return mod_name, mod, str(files_dir), cwd


@pytest.mark.parametrize("kind", ("source", "installed"))
class TestTheShippedFilesAreDashNameDotDash:

    def test_a_shipped_name_bare_or_with_scheme_reads_its_dash_file(
            self, tmp_path, monkeypatch, kind):
        mod_name, mod, files_dir, cwd = _layout(tmp_path, kind)
        monkeypatch.chdir(cwd)
        try:
            for name in SHIPPED:
                want = os.path.realpath(
                    os.path.join(files_dir, f"dash-{name}.scheme"))
                for spelling in (name, name + ".scheme",
                                 name.upper() + ".SCHEME"):
                    inst = mod.SchemeParser.__new__(mod.SchemeParser)
                    got = os.path.realpath(inst._resolve_path(spelling))
                    assert got == want, (spelling, got)
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    sch = mod.SchemeParser(name)
                assert sch.is_fallback is False and sch.name == name, (
                    name, sch.name)
        finally:
            sys.modules.pop(mod_name, None)

    def test_a_scheme_file_in_the_working_directory_still_wins(
            self, tmp_path, monkeypatch, kind):
        """A user's own mytheme.scheme still resolves from the working
        directory, but a file there named like a shipped scheme no longer
        replaces it: twoway draws BASE's scheme first (WP-30 P1.25b)."""
        mod_name, mod, files_dir, cwd = _layout(tmp_path, kind)
        (cwd / "mytheme.scheme").write_text(
            "#include s1rcolor\ncolor background #123456\n", encoding="utf-8")
        (cwd / "s2color.scheme").write_text(
            "color background #0f0f0f\n", encoding="utf-8")
        monkeypatch.chdir(cwd)
        try:
            inst = mod.SchemeParser.__new__(mod.SchemeParser)
            for spelling in ("mytheme", "mytheme.scheme"):
                assert os.path.realpath(inst._resolve_path(spelling)) == \
                    os.path.realpath(str(cwd / "mytheme.scheme"))
            # WP-30 P1.25b: the shipped translation wins.
            assert os.path.realpath(inst._resolve_path("s2color")) == \
                os.path.realpath(os.path.join(files_dir,
                                              "dash-s2color.scheme"))
            sch = mod.SchemeParser("mytheme")
            assert sch.name == "mytheme" and sch.is_fallback is False
            assert sch._props.get("color background") == "#123456"
        finally:
            sys.modules.pop(mod_name, None)

    def test_a_stray_name_dot_scheme_beside_the_renderer_is_not_read(
            self, tmp_path, monkeypatch, kind):
        mod_name, mod, files_dir, cwd = _layout(tmp_path, kind)
        code_dir = os.path.dirname(mod.__file__)
        for d in {files_dir, code_dir}:
            with open(os.path.join(d, "s2color.scheme"), "w",
                      encoding="utf-8") as fh:
                fh.write("color background #ff00ff\n")
        monkeypatch.chdir(cwd)
        try:
            inst = mod.SchemeParser.__new__(mod.SchemeParser)
            for spelling in ("s2color", "s2color.scheme"):
                got = os.path.basename(inst._resolve_path(spelling))
                assert got == "dash-s2color.scheme", (spelling, got)
            assert mod.SchemeParser("s2color")._props.get(
                "color background") != "#ff00ff"
        finally:
            sys.modules.pop(mod_name, None)

    def test_a_missing_dash_file_falls_back_rather_than_reading_a_stray(
            self, tmp_path, monkeypatch, kind):
        mod_name, mod, files_dir, cwd = _layout(tmp_path, kind)
        os.remove(os.path.join(files_dir, "dash-stcolor.scheme"))
        with open(os.path.join(files_dir, "stcolor.scheme"), "w",
                  encoding="utf-8") as fh:
            fh.write("color background #ff00ff\n")
        monkeypatch.chdir(cwd)
        try:
            assert mod.SchemeParser.can_resolve("stcolor") is False
        finally:
            sys.modules.pop(mod_name, None)


class TestTheRepoShipsDashNameDotDash:

    def test_there_is_no_schemes_directory(self):
        assert not os.path.exists(os.path.join(_ROOT, "schemes"))


class TestTheShippedFileHelpers:

    def test_shipped_file(self):
        assert dr.SchemeParser._shipped_file("s2color") == "dash-s2color.scheme"
        assert dr.SchemeParser._shipped_file("stcolor_alt") == \
            "dash-stcolor_alt.scheme"

    def test_shipped_base(self):
        sb = dr.SchemeParser._shipped_base
        assert sb("s2color") == "s2color"
        assert sb(" S2COLOR.Scheme ") == "s2color"
        assert sb("StColor_Alt") == "stcolor_alt"
        for name in ("mytheme", "mytheme.scheme", "", None, "s/s2color",
                     "../s2color.scheme", "dash-s2color.scheme",
                     "scheme-s2color"):
            assert sb(name) is None, name


@pytest.mark.parametrize("kind", ("source", "installed"))
class TestADashPrefixedNameIsTheUsersOwnFile:
    """scheme(dash-s2color) is not a way to name the shipped file: it is the
    user's dash-s2color.scheme in the working directory, or unresolvable."""

    def test_without_a_file_in_the_working_directory_it_does_not_resolve(
            self, tmp_path, monkeypatch, kind):
        mod_name, mod, _files_dir, cwd = _layout(tmp_path, kind)
        monkeypatch.chdir(cwd)
        try:
            for spelling in ("dash-s2color", "dash-s2color.scheme",
                             "DASH-S2COLOR.SCHEME"):
                assert mod.SchemeParser.can_resolve(spelling) is False, spelling
        finally:
            sys.modules.pop(mod_name, None)

    def test_with_a_file_in_the_working_directory_it_reads_that_file(
            self, tmp_path, monkeypatch, kind):
        mod_name, mod, _files_dir, cwd = _layout(tmp_path, kind)
        (cwd / "dash-s2color.scheme").write_text(
            "#include s2color\ncolor background #0a0b0c\n", encoding="utf-8")
        monkeypatch.chdir(cwd)
        try:
            for spelling in ("dash-s2color", "dash-s2color.scheme"):
                sch = mod.SchemeParser(spelling)
                assert sch.name == "dash-s2color", sch.name
                assert sch._props.get("color background") == "#0a0b0c"
        finally:
            sys.modules.pop(mod_name, None)
