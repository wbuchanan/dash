"""test_scheme_coercion.py — S11/TR-11.7: SchemeParser's coercion layer.

Eight of ``SchemeParser``'s coercion helpers had no direct test, and that is
exactly where the silent-black failure lived: ``_color`` swallowed an
unresolvable colour token and returned its ``#000000`` default, so the whole
``stcolor`` scheme rendered every series black and nothing said why.

``_color`` and ``_lpattern`` were taught to warn in an earlier batch. These
tests pin that behaviour so it cannot regress, and cover the rest of the layer
for the first time.

The distinction every one of these functions has to get right:

  * an **absent** key falls back silently — that is ordinary scheme
    inheritance, and every scheme leaves most keys unset;
  * a key that is **present and unresolvable** is a defect in the scheme or in
    dash's translation table, and must say so.

Conflating the two is what made the failure invisible.
"""
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import SchemeParser


@pytest.fixture
def sp():
    """A parser whose property dict the test controls directly."""
    parser = SchemeParser("s2color")
    parser._props = {}
    return parser


def _set(sp, **props):
    sp._props = {k.replace("__", " "): v for k, v in props.items()}
    return sp


def _scheme_truth(name):
    """One scheme's record in fixtures/scheme_truth.json, the ground truth
    extracted from Stata's own scheme and style files."""
    import json
    with open(os.path.join(_HERE, "fixtures", "scheme_truth.json"),
              encoding="utf-8") as fh:
        return json.load(fh)[name]


def _scheme_warnings(caught):
    """The messages of the warnings a scheme's own tokens raised.

    Every token emitter in SchemeParser starts its message "dash scheme:"
    (colour, size, line pattern, line width, a bounded count, an #include
    too deep), and the shipped-scheme check below keeps only those.  The
    filter is one function so that the positive control,
    test_the_filter_sees_every_token_emitter, exercises the very predicate
    the absence check relies on.
    """
    return [str(w.message) for w in caught
            if "dash scheme" in str(w.message)]


# ======================================================================
# _color — where the silent-black failure lived
# ======================================================================

class TestColor:

    def test_an_absent_key_falls_back_silently(self, sp):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = sp._color("color p1", default="#123456")
        assert got == "#123456"
        assert not caught, (
            "an absent key is ordinary inheritance and must not warn — every "
            "scheme leaves most keys unset"
        )

    def test_a_blank_value_also_falls_back_silently(self, sp):
        _set(sp, **{"color p1": "   "})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert sp._color("color p1", default="#abcdef") == "#abcdef"
        assert not caught

    def test_a_resolvable_colour_is_translated(self, sp):
        _set(sp, **{"color p1": "navy"})
        assert sp._color("color p1").startswith("#")

    def test_a_hex_value_passes_through(self, sp):
        _set(sp, **{"color p1": "#1a2b3c"})
        assert sp._color("color p1").lower() == "#1a2b3c"

    def test_an_unresolvable_colour_WARNS_and_names_the_token(self, sp):
        """The regression that turned stcolor black."""
        _set(sp, **{"color p1": "stc99"})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = sp._color("color p1", default="#000000")
        assert got == "#000000"
        assert caught, "an unresolvable colour degraded silently"
        msg = " ".join(str(w.message) for w in caught)
        assert "stc99" in msg, f"the warning does not name the token: {msg}"
        assert "color p1" in msg, f"the warning does not name the key: {msg}"

    def test_the_warning_says_the_output_will_not_match_stata(self, sp):
        _set(sp, **{"color p1": "notacolour"})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sp._color("color p1")
        assert any("match Stata" in str(w.message) for w in caught)


# ======================================================================
# _lpattern
# ======================================================================

class TestLinePattern:

    def test_absent_defaults_to_solid(self, sp):
        assert sp._lpattern("linepattern p1") in ([], "solid")

    def test_a_known_pattern_translates(self, sp):
        _set(sp, **{"linepattern p1": "dash"})
        assert sp._lpattern("linepattern p1")

    def test_an_unknown_pattern_WARNS_rather_than_raising(self, sp):
        """A scheme must not be able to abort the whole render."""
        _set(sp, **{"linepattern p1": "squiggle"})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = sp._lpattern("linepattern p1")
        assert got == []
        assert any("squiggle" in str(w.message) for w in caught), (
            "an unknown line pattern vanished silently"
        )


# ======================================================================
# _gsize
# ======================================================================

class TestGsize:

    def test_absent_returns_the_default(self, sp):
        assert sp._gsize("gsize axis_title", default="11pt") == "11pt"

    @pytest.mark.parametrize("name", ["small", "medium", "large"])
    def test_a_named_size_maps_to_points(self, sp, name):
        _set(sp, **{"gsize axis_title": name})
        got = sp._gsize("gsize axis_title")
        assert got.endswith("pt")

    def test_named_sizes_are_ordered(self, sp):
        def pt(name):
            _set(sp, **{"gsize k": name})
            return float(sp._gsize("gsize k").rstrip("pt"))
        assert pt("small") < pt("medium") < pt("large")

    def test_a_numeric_value_is_a_stata_relative_size(self, sp):
        """A bare number in a gsize directive is Stata's relative unit:
        100 = the graph's smaller dimension, so at Stata's 4-inch reference
        one unit is 2.88 pt (style/gsize-medium.style: 3.8194 is "11 pt
        based on a 4 inch high graph").  It was read as ``int(val * 1.2)``
        pt, which made economist's ``gsize heading 6.0`` a 7 pt title under
        its 11 pt subtitle.  WP-16 (GAPS G5)."""
        _set(sp, **{"gsize k": "5.0"})
        assert sp._gsize("gsize k") == "14.4pt"

    def test_a_tiny_numeric_value_is_not_floored(self, sp):
        """This asserted a 6 pt floor -- dash's invention, not Stata's.  A
        scheme that asks for 0.1 (0.288 pt) gets 0.288 pt."""
        _set(sp, **{"gsize k": "0.1"})
        assert sp._gsize("gsize k") == "0.288pt"

    def test_an_unparseable_value_returns_the_default(self, sp):
        _set(sp, **{"gsize k": "enormous"})
        assert sp._gsize("gsize k", default="9pt") == "9pt"


# ======================================================================
# _intensity
# ======================================================================

class TestIntensity:

    def test_absent_returns_the_default(self, sp):
        assert sp._intensity("intensity k", default=0.4) == 0.4

    def test_a_percentage_becomes_a_fraction(self, sp):
        _set(sp, **{"intensity k": "50"})
        assert sp._intensity("intensity k") == pytest.approx(0.5)

    @pytest.mark.parametrize("raw,want", [("0", 0.0), ("100", 1.0)])
    def test_the_endpoints(self, sp, raw, want):
        _set(sp, **{"intensity k": raw})
        assert sp._intensity("intensity k") == pytest.approx(want)

    @pytest.mark.parametrize("raw", ["-20", "500"])
    def test_out_of_range_values_are_clamped(self, sp, raw):
        _set(sp, **{"intensity k": raw})
        got = sp._intensity("intensity k")
        assert 0.0 <= got <= 1.0

    def test_an_unparseable_value_returns_the_default(self, sp):
        _set(sp, **{"intensity k": "quite a lot"})
        assert sp._intensity("intensity k", default=0.3) == 0.3


# ======================================================================
# _lwidth, _symbol
# ======================================================================

class TestLineWidth:

    def test_absent_returns_the_default(self, sp):
        assert sp._lwidth("linewidth p1", default=2.5) == 2.5

    def test_a_numeric_value_is_a_stata_linewidth_unit(self, sp):
        """A bare number in a linewidth directive is Stata's unit, the one
        the keywords are defined in (style/linewidth-medium.style sets
        .30).  dash anchors medium at 1.5 px, so a number is 5 px per unit:
        economist's ``linewidth p 1.2`` is 6.0 px, four medium widths, not
        the 1.2 px this test used to pin.  WP-16 (GAPS G5)."""
        _set(sp, **{"linewidth p1": "3.5"})
        assert sp._lwidth("linewidth p1") == pytest.approx(17.5)
        _set(sp, **{"linewidth p1": "0.30"})
        assert sp._lwidth("linewidth p1") == pytest.approx(1.5)

    def test_a_named_width_is_translated(self, sp):
        _set(sp, **{"linewidth p1": "thick"})
        assert sp._lwidth("linewidth p1") > 0

    def test_named_widths_are_ordered(self, sp):
        def w(name):
            _set(sp, **{"linewidth p1": name})
            return sp._lwidth("linewidth p1")
        assert w("thin") < w("medium") < w("thick")

    def test_an_unresolvable_width_returns_the_default(self, sp):
        _set(sp, **{"linewidth p1": "chunky"})
        assert sp._lwidth("linewidth p1", default=1.25) == 1.25


class TestSymbol:

    def test_absent_returns_the_default(self, sp):
        assert sp._symbol("symbol p1", default="square") == "square"

    def test_a_known_symbol_is_translated(self, sp):
        _set(sp, **{"symbol p1": "diamond"})
        assert sp._symbol("symbol p1") == "diamond"

    def test_a_stata_abbreviation_is_translated(self, sp):
        _set(sp, **{"symbol p1": "Dh"})
        assert sp._symbol("symbol p1") == "diamond"

    def test_an_unknown_symbol_returns_the_default(self, sp):
        _set(sp, **{"symbol p1": "octagon"})
        assert sp._symbol("symbol p1", default="circle") == "circle"


# ======================================================================
# _float, _int, _yesno
# ======================================================================

class TestScalarCoercions:

    @pytest.mark.parametrize("raw,want", [("5.5", 5.5), ("0", 0.0),
                                          ("-2.25", -2.25)])
    def test_float_parses(self, sp, raw, want):
        _set(sp, **{"k": raw})
        assert sp._float("k", None) == pytest.approx(want)

    def test_float_absent_and_unparseable_return_the_default(self, sp):
        assert sp._float("k", 1.5) == 1.5
        _set(sp, **{"k": "lots"})
        assert sp._float("k", 1.5) == 1.5

    @pytest.mark.parametrize("raw,want", [("7", 7), ("7.9", 7), ("-3", -3)])
    def test_int_parses_and_truncates(self, sp, raw, want):
        _set(sp, **{"k": raw})
        assert sp._int("k", None) == want

    def test_int_absent_and_unparseable_return_the_default(self, sp):
        assert sp._int("k", 4) == 4
        _set(sp, **{"k": "many"})
        assert sp._int("k", 4) == 4

    @pytest.mark.parametrize("raw", ["yes", "y", "1", "true", "on", "YES"])
    def test_yesno_true_forms(self, sp, raw):
        _set(sp, **{"k": raw})
        assert sp._yesno("k", False) is True

    @pytest.mark.parametrize("raw", ["no", "n", "0", "false", "off", "NO"])
    def test_yesno_false_forms(self, sp, raw):
        _set(sp, **{"k": raw})
        assert sp._yesno("k", True) is False

    @pytest.mark.parametrize("default", [True, False])
    def test_yesno_absent_or_unrecognised_returns_the_default(self, sp,
                                                              default):
        assert sp._yesno("k", default) is default
        _set(sp, **{"k": "maybe"})
        assert sp._yesno("k", default) is default


# ======================================================================
# _parse_file
# ======================================================================

class TestParseFile:

    def test_a_missing_file_raises_an_error_that_names_the_path(self, sp):
        """The degradation S02 built lives in the CALLER, not here.

        _parse_file is the low-level reader and is allowed to fail loudly;
        resolve_or_fallback() is what turns a missing scheme directory into a
        warned fallback. Keeping the two apart is deliberate: a missing
        DIRECTORY is a degradation, and an unreadable file the caller asked
        for by name is an error.
        """
        with pytest.raises(ValueError) as exc:
            sp._parse_file("/nonexistent/nowhere.scheme", set())
        assert "nowhere.scheme" in str(exc.value)

    def test_the_caller_degrades_when_a_scheme_is_missing(self):
        """The other half of that contract."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = SchemeParser.resolve_or_fallback(
                "nosuchschemeanywhere", "test")
        assert got is not None
        assert isinstance(got, SchemeParser)

    def test_an_include_cycle_terminates(self, tmp_path):
        """A scheme that includes itself must not recurse forever."""
        a = tmp_path / "a.scheme"
        a.write_text("#include a\ncolor p1 navy\n")
        parser = SchemeParser("s2color")
        got = parser._parse_file(str(a), set())
        assert isinstance(got, dict)

    def test_directives_are_read(self, tmp_path):
        f = tmp_path / "x.scheme"
        f.write_text(
            "* a comment line\n"
            "color p1 navy\n"
            "linewidth p1 thick\n"
            "\n"
            "symbol p2 diamond\n"
        )
        parser = SchemeParser("s2color")
        props = parser._parse_file(str(f), set())
        assert props.get("color p1") == "navy"
        assert props.get("linewidth p1") == "thick"
        assert props.get("symbol p2") == "diamond"

    def test_comments_and_blank_lines_are_ignored(self, tmp_path):
        f = tmp_path / "y.scheme"
        f.write_text("* only a comment\n\n   \n")
        parser = SchemeParser("s2color")
        assert parser._parse_file(str(f), set()) == {}


# ======================================================================
# _init_properties
# ======================================================================

class TestInitProperties:

    def test_a_real_scheme_populates_the_documented_attributes(self):
        parser = SchemeParser("s2color")
        for attr in ("p_colors", "background_color", "graphsize_x",
                     "graphsize_y"):
            assert hasattr(parser, attr), attr

    def test_p_colors_is_a_non_trivial_cycle(self):
        parser = SchemeParser("s2color")
        # s2color's cycle is fifteen different colours, p1 navy through
        # p15, in Stata's own file and in fixtures/scheme_truth.json.  The
        # old floors (three entries, three distinct) passed a cycle cut to
        # three or repeating after the third (24sep2026).
        truth = _scheme_truth("s2color")["p_colors"]
        assert len(truth) == len(set(truth)) == 15
        assert len(parser.p_colors) == 15
        assert len(set(parser.p_colors)) == 15, (
            f"the colour cycle repeats itself: {parser.p_colors}"
        )

    @pytest.mark.parametrize("name", ["stcolor", "s2color", "economist",
                                      "s1mono"])
    def test_every_translated_scheme_parses_without_warnings(self, name):
        """An unresolvable token in a SHIPPED scheme is our bug, not the user's."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            SchemeParser(name)
        scheme_warnings = _scheme_warnings(caught)
        assert not scheme_warnings, (
            f"{name} contains tokens dash cannot resolve: {scheme_warnings}"
        )

    def test_the_filter_sees_every_token_emitter(self, tmp_path,
                                                 monkeypatch):
        """Positive control for the absence check above.

        That check keeps only messages holding "dash scheme", and nothing
        in this file asserted the emitters say it: renaming the prefix in
        any one of them would have let a shipped scheme's unresolvable
        token through it silently (measured 24sep2026 with the colour
        emitter's prefix changed and `color p1 stc99' planted in
        s2color.scheme: the check still passed).  A user scheme planting
        one bad token per emitter must raise six warnings, each seen by the
        same filter and naming its token.
        """
        monkeypatch.chdir(tmp_path)
        depth = dash_render._MAX_SCHEME_INCLUDE_DEPTH
        for i in range(depth + 1):
            (tmp_path / f"chain{i}.scheme").write_text(
                f"#include chain{i + 1}\n" if i < depth else "")
        (tmp_path / "bad.scheme").write_text(
            "#include chain0\n"
            "color background stc99\n"
            "gsize heading 1e9\n"
            "linepattern p1line squiggle\n"
            "linewidth major_grid -4\n"
            "clockdir legend_position 99\n")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            SchemeParser("bad")
        seen = _scheme_warnings(caught)
        assert len(seen) == 6, seen
        for needle in (f"nested more than {depth} files deep",
                       "colour 'stc99'", "size '1e9'",
                       "line pattern 'squiggle'", "line width '-4'",
                       "clock position '99'"):
            assert sum(needle in m for m in seen) == 1, (needle, seen)

    @pytest.mark.parametrize("name", ["stcolor", "s2color", "economist",
                                      "s1mono"])
    def test_no_translated_scheme_renders_everything_black(self, name):
        """The stcolor symptom -- every series drawn black -- as a standing
        check on the four schemes parametrized here: stcolor, s2color,
        economist and s1mono.  Each must give its first five series five
        different colours, as the fixture does, and all but s1mono must not
        draw them all black."""
        parser = SchemeParser(name)
        colours = [parser.default_color(i, "scatter") for i in range(5)]
        # Each of the four draws five different colours for its first five
        # series, as fixtures/scheme_truth.json records them (s1mono's are
        # five greys).  `> 1' passed a scheme whose cycle had collapsed to
        # two colours (24sep2026).
        truth = _scheme_truth(name)["p_colors"][:5]
        assert len(set(truth)) == 5
        assert len(set(colours)) == 5, (
            f"{name} gives every series the same colour: {colours}"
        )
        if name != "s1mono":
            assert not all(c.lower() in ("#000000", "black")
                           for c in colours), colours
