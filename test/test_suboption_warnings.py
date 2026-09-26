"""A sub-option dash does not implement is named, in both render modes.

ROADMAP WP-14 / GAPS.md E3.  ``dash.sthlp`` promises "Nothing is ever
dropped without being named".  It held for options (the ignoring note) and,
since WP-11, for by()'s sub-options.  Measured 22sep2026, it did not hold
for the sub-options of legend(), xlabel()/ylabel(), xscale()/yscale(),
xtitle()/ytitle(), xline()/yline() or filter(): every probe below rendered
with no warning in either mode, and xtitle("Weight", orientation(vertical))
put the sub-option TEXT into the axis title.  A filter() group whose label
contained ``__`` or the word ``open`` vanished whole, with rc 0 and no
message, because the injection pattern read the label; an unknown type()
and a variable not in the data vanished the same way.

The warning has the shape by() already uses -- one line per option per
render naming the sub-options as written -- and comes from shared code, so
the two modes raise the same one; ``test_mode_parity.py`` compares the
warnings as well.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402


def _both(bo=None, go=None, plots=None):
    spec = tp._spec(plots or [plot_for("scatter")], bo, go)
    r, std_w = tp._standalone(spec)
    doc, srv_w = tp._served(spec)
    return r, doc, std_w, srv_w


def _the_one(warnings_, option):
    hits = [w for w in warnings_ if f"{option}() sub-option" in w]
    assert len(hits) == 1, (
        f"expected exactly one {option}() sub-option warning, got {hits}")
    return hits[0]


SUBOPTIONS = [
    # (id, graph options, plots, option, named tokens, honoured tokens)
    ("legend span stack holes", {"legend": "span stack holes(1) position(6)"},
     [plot_for("scatter"), plot_for("lfit")], "legend",
     ["span", "stack", "holes(1)"], ["position"]),
    ("legend keygap symxsize textwidth bmargin",
     {"legend": "keygap(2) symxsize(3) textwidth(20) bmargin(small) cols(2)"},
     [plot_for("scatter"), plot_for("lfit")], "legend",
     ["keygap(2)", "symxsize(3)", "textwidth(20)", "bmargin(small)"],
     ["cols"]),
    ("legend colfirst", {"legend": "colfirst on"}, None, "legend",
     ["colfirst"], ["on"]),
    ("ylabel labcolor", {"ylabel": ", labcolor(red)"}, None, "ylabel",
     ["labcolor(red)"], []),
    ("ylabel labgap tlength", {"ylabel": "10(10)30, labgap(2) tlength(3)"},
     None, "ylabel", ["labgap(2)", "tlength(3)"], []),
    ("yscale reverse noline titlegap",
     {"yscale": "reverse noline titlegap(2)"}, None, "yscale",
     ["noline", "titlegap(2)"], ["reverse"]),
    ("xscale log range and off", {"xscale": "log range(1000 5000) off"},
     None, "xscale", ["off"], ["log", "range"]),
    ("xtitle orientation", {"xtitle": "Weight, orientation(vertical)"}, None,
     "xtitle", ["orientation(vertical)"], []),
    ("ytitle size and justification",
     {"ytitle": "Miles, size(large) justification(left)"}, None, "ytitle",
     ["justification(left)"], ["size"]),
    ("xline lstyle noextend",
     {"xline": "3000, lcolor(red) lstyle(foreground) noextend"}, None,
     "xline", ["lstyle(foreground)", "noextend"], ["lcolor"]),
    ("yline axis", {"yline": "20 25, lpattern(dash) axis(2)"}, None, "yline",
     ["axis(2)"], ["lpattern"]),
    # WP-28 B3: abbreviations are canonicalised before the honoured check,
    # so a bare "c" is not named beside a "bc" it does not abbreviate.
    ("title c and bc", {"title": "T, c(red) bc(red)"}, None, "title",
     ["bc(red)"], ["c"]),
    ("xtitle orient", {"xtitle": "Weight, orient(vertical)"}, None,
     "xtitle", ["orient(vertical)"], []),
    ("ytitle axis 3", {"ytitle": "M, axis(3)"}, None, "ytitle",
     ["axis(3)"], []),
]


@pytest.mark.parametrize("name,go,plots,option,named,honoured", SUBOPTIONS,
                         ids=[c[0] for c in SUBOPTIONS])
class TestAnUnimplementedSuboptionIsNamed:
    def test_once_in_both_modes(self, name, go, plots, option, named,
                                honoured):
        _, _, std_w, srv_w = _both(None, go, plots)
        assert std_w == srv_w, (name, std_w, srv_w)
        line = _the_one(std_w, option)
        assert "not implemented and ignored: " in line
        listed = line.split("not implemented and ignored: ", 1)[1].split()
        for tok in named:
            assert listed.count(tok) == 1, (
                f"{name}: {tok} is not named exactly once in {line!r}")
        for tok in honoured:
            assert not [t for t in listed if t.split("(")[0] == tok], (
                f"{name}: the honoured {tok} is named in {line!r}")


class TestTheHonouredOnesStayQuiet:
    @pytest.mark.parametrize("go,plots", [
        ({"legend": "position(6) cols(2) size(small) order(2 1) on"},
         [plot_for("scatter"), plot_for("lfit")]),
        ({"legend": 'label(1 "Cars") rows(1) ring(0) pos(12)'},
         [plot_for("scatter"), plot_for("lfit")]),
        ({"xlabel": "2000(1000)4000, format(%9.0fc) nogrid labsize(small) "
                    "angle(45)", "ylabel": "#5, grid"}, None),
        ({"xlabel": 'minmax', "ylabel": "none"}, None),
        # G16 (WP-28 S14): valuelabel is drawn, so it is no longer named.
        ({"xlabel": ", valuelabel"}, None),
        ({"xscale": "log", "yscale": "reverse range(10 40)"}, None),
        ({"xtitle": "Weight", "ytitle": "Miles, size(large) color(red)"},
         None),
        ({"xline": "3000, lcolor(red) lpattern(dash) lwidth(thick)",
          "yline": "20 25"}, None),
        # WP-28 B3: every honoured spelling stays quiet, together.
        ({"ytitle": "M, si(large) c(red) prefix"}, None),
        ({"xtitle": "W, axis(1)"}, None),
    ])
    def test_no_warning(self, go, plots):
        _, _, std_w, srv_w = _both(None, go, plots)
        assert std_w == srv_w
        assert not [w for w in std_w if "sub-option" in w], std_w


class TestAxisTitlesSplitTheirSuboptions:
    """The text is the text; size() and color() are honoured as the figure
    title already honours them; the rest is named."""

    def test_the_title_is_the_bare_text(self):
        r, doc, _, _ = _both(None, {"xtitle": "Weight, orientation(vertical)"})
        fig = list(r.figures.values())[0]
        assert fig.xaxis[0].axis_label == "Weight"
        srv = [m for m in tp._walk_models(doc)
               if type(m).__name__ == "figure"][0]
        assert srv.xaxis[0].axis_label == "Weight"

    def test_size_and_color_reach_the_axis_title(self):
        r, doc, _, _ = _both(None, {"ytitle": "Miles, size(large) color(red)"})
        fig = list(r.figures.values())[0]
        assert fig.yaxis[0].axis_label == "Miles"
        assert fig.yaxis[0].axis_label_text_color == "#ff0000"
        srv = [m for m in tp._walk_models(doc)
               if type(m).__name__ == "figure"][0]
        assert srv.yaxis[0].axis_label_text_font_size == \
            fig.yaxis[0].axis_label_text_font_size
        assert srv.yaxis[0].axis_label_text_color == "#ff0000"


class TestAFilterIsRefusedAloud:
    """BR-14.2: a security filter may refuse input, but never silently."""

    def _widgets(self, r, doc):
        std = [w.title for w in r.filter_widgets]
        srv = [w.title for w in tp._widgets_of(doc)]
        return std, srv

    # "a; b" and "a || b" too: a ";" or "||" separates filter() groups only
    # outside quotes and parentheses, on the Stata side as well as here
    # (_dash_filter_split), and the help says a label may hold either.
    @pytest.mark.parametrize("label", [
        "R&D __ spend", "open the door", "import duties", "eval sheet",
        "exec summary", "cost ($)", "back\\slash", "Size (in)", "a; b",
        "a || b",
    ])
    def test_a_benign_label_produces_the_widget(self, label):
        r, doc, std_w, srv_w = _both(
            {"filter": f'price, type(range) label("{label}")'})
        std, srv = self._widgets(r, doc)
        assert std == [label] and srv == [label], (label, std, srv, std_w)
        assert not [w for w in std_w if "filter" in w.lower()], std_w
        assert std_w == srv_w

    def test_an_unknown_type_is_named_with_the_accepted_ones(self):
        r, doc, std_w, srv_w = _both({"filter": "price, type(bogus)"})
        std, srv = self._widgets(r, doc)
        assert std == [] and srv == []
        assert std_w == srv_w
        hits = [w for w in std_w if "type(bogus)" in w]
        assert len(hits) == 1, std_w
        for t in ("dropdown", "range", "slider"):
            assert t in hits[0]

    def test_a_variable_not_in_the_data_is_named(self):
        r, doc, std_w, srv_w = _both({"filter": "nosuchvar, type(dropdown)"})
        std, srv = self._widgets(r, doc)
        assert std == [] and srv == []
        assert std_w == srv_w
        assert len([w for w in std_w if "nosuchvar" in w]) == 1, std_w

    @pytest.mark.parametrize("bad", [
        "pr`ice, type(range)", "123bad, type(dropdown)",
        "price, type(range) exclude(g$1)",
    ])
    def test_a_refused_group_is_named(self, bad):
        """A name that is not a name -- the variable's or an exclude()'s
        -- refuses the group, and says so."""
        r, doc, std_w, srv_w = _both({"filter": bad})
        std, srv = self._widgets(r, doc)
        assert std == [] and srv == []
        assert std_w == srv_w
        hits = [w for w in std_w if "filter(" in w and "refused" in w]
        assert len(hits) == 1, std_w

    @pytest.mark.parametrize("spec,tokens", [
        ("price, type(range) $x", ["$x"]),
        ('price, type(range) label("a") \\ b', ["\\", "b"]),
        ("price, type(range) foo(1) bar", ["foo(1)", "bar"]),
    ])
    def test_a_stray_token_is_named_and_the_widget_still_built(self, spec,
                                                               tokens):
        r, doc, std_w, srv_w = _both({"filter": spec})
        std, srv = self._widgets(r, doc)
        assert len(std) == 1 and std == srv
        assert std_w == srv_w
        hits = [w for w in std_w if "filter() sub-option" in w]
        assert len(hits) == 1, std_w
        listed = hits[0].split("ignored: ", 1)[1].split()
        assert listed == tokens

    def test_comma_separated_suboptions_are_the_documented_form(self):
        """filter(foreign, type(dropdown), exclude(g1)): the commas between
        sub-options are separators, not parts of the tokens.  Measured on
        the first shared parser: `type(dropdown),' read as a type of ""
        and the group was refused (test_server's BUG-21e caught it)."""
        import dash_render
        r, doc, std_w, srv_w = _both(
            {"filter": "price, type(range), exclude(g1), label(Price)"})
        std, srv = self._widgets(r, doc)
        assert std == ["Price"] and srv == ["Price"], (std, srv, std_w)
        assert not [w for w in std_w if "filter" in w.lower()], std_w
        assert std_w == srv_w
        got = dash_render._dash_parse_filter_raw(
            "foreign, type(dropdown), exclude(g1) || weight, type(range)")
        assert [(g["varname"], g["type"], g["exclude"]) for g in got] == [
            ("foreign", "dropdown", ["g1"]), ("weight", "range", [])]

    def test_the_semicolon_separates_groups(self):
        """`price; import os' is two groups: a widget for price, and a
        named refusal for the variable `import', which is not in the data.
        The Stata side rejects that command earlier (r(111))."""
        r, doc, std_w, srv_w = _both({"filter": "price; import os"})
        std, srv = self._widgets(r, doc)
        assert std == ["price"] and srv == ["price"]
        assert std_w == srv_w
        assert len([w for w in std_w if "filter(import)" in w]) == 1, std_w
