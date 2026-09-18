# -*- coding: utf-8 -*-
"""test_scheme_fidelity.py — fidelity of dash's translated Stata schemes.

WHAT THIS FILE IS
-----------------
Section 03 of the plan translates Stata's 14 shipped graph schemes into dash
``.scheme`` files; section 11 makes ``dash_render`` consume them.  This file is
the *test-first* half of that work (project rule 8): every assertion below is
driven by ``test/fixtures/scheme_truth.json``, the ground truth another agent
extracted from Stata's own ``scheme-*.scheme`` and ``style/*.style`` files with
``scripts/extract_scheme_truth.py``.

Nothing here hardcodes an expected scheme value except the handful of sanity
anchors in ``test_fixture_sanity_anchors`` — those exist to catch a corrupted or
regenerated-wrong fixture, so that a green run of the rest of the file cannot be
green against a fixture that has quietly changed underneath it.

WHAT "MATCHES" MEANS, PROPERTY BY PROPERTY
------------------------------------------
The fixture stores two different kinds of value, and they are checked two
different ways.  This distinction is not cosmetic — it is the difference between
a test that measures translation quality and a test that asserts a number the
extractor explicitly said it could not derive.

1. RESOLVED VALUES — colours (``#rrggbb``), intensities (alpha 0-1), graph size
   (inches), legend position (clock direction) and legend columns.  These are in
   the same representation dash uses, so they are compared against the value
   ``SchemeParser`` actually parsed out.  Colours are compared per RGB channel
   with a tolerance of ``COLOR_CHANNEL_TOL``.

2. DECLARED STYLE NAMES — line widths, ``gsize`` font sizes, symbol size, marker
   symbols and line patterns.  ``_meta.units`` and the extractor's own
   "unresolvable" notes state plainly that Stata's mapping from these style names
   to points/pixels was NOT derived from the style files (e.g. ``linewidth
   medium`` is ``.30`` in unknown units; ``gsize medsmall`` is ``3.4722``
   *relative* units).  Asserting dash's pt/px translation against those numbers
   would assert an invented conversion.  So for these the test compares the
   Stata style *name* the translated ``.scheme`` file declares against the name
   Stata's own scheme declares — exact string match, which is exactly what the
   translation controls.

   ``p_line_dash_patterns`` is therefore excluded from the comparison entirely:
   it is the same information as ``p_line_patterns`` expressed in Stata's
   undocumented dash units, and no unit mapping to Bokeh's pixel dash arrays
   exists in the fixture.  ``p_line_patterns`` (the names) carries the fidelity.

COVERAGE HARNESS
----------------
``test_scheme_coverage`` reports two fractions per scheme over the same 115
property units:

  * ``supplied``  — the translated ``.scheme`` file contains a directive that
                    resolves the property through Stata's documented stub
                    fallback chain (``_meta.fallback_chain``).  Presence only.
  * ``faithful``  — the property is supplied *and* the value dash ends up with
                    equals the fixture.

The threshold is asserted on ``faithful``.  Presence alone is far too lenient to
be the gate: measured on the five schemes dash ships today it scores 0.939,
because those five supply a full 15-entry colour/symbol/pattern cycle — just
largely the wrong entries.  Both numbers are printed on failure so the gap
between "supplies something" and "supplies the right thing" stays visible.

HOW THIS FILE READS THE TRANSLATED SCHEMES
------------------------------------------
Declared style names are read from ``SchemeParser._props``, the flat
``"<class> <key>" -> value`` dict the parser builds after following ``#include``.
That is a private attribute; ``test_scheme_parser_exposes_props`` guards the
assumption so a refactor of the parser fails loudly here instead of silently
turning every name comparison into "not supplied".
"""

import json
import os
import re
import sys
from collections import namedtuple

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dash_render import OptionTranslator, SchemeParser


# ===========================================================================
# Module-level constants
# ===========================================================================

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURE_PATH = os.path.join(REPO_ROOT, "test", "fixtures", "scheme_truth.json")
SCHEMES_DIR = os.path.join(REPO_ROOT, "schemes")

#: Minimum acceptable *faithful* coverage of a scheme's fixture properties.
#:
#: VALUE TO BE CONFIRMED.  0.90 is a starting stake in the ground, not a
#: measured number: it says "a translated scheme must reproduce the large
#: majority of what Stata's own scheme declares".  Once section 03's deepened
#: translations exist, re-measure what they actually achieve and reset this
#: constant to that floor — deliberately, in a commit that says so.  It must
#: never be lowered to accommodate a translation that fell short; that would
#: turn the harness into a rubber stamp.  See the COVERAGE HARNESS note above
#: for why the weaker presence-only fraction is not what is gated.
COVERAGE_THRESHOLD = 0.90

#: Per-channel RGB tolerance when comparing colours (0-255 scale).
COLOR_CHANNEL_TOL = 2

#: Tolerance for intensity/alpha comparisons (fixture stores pct/100 exactly).
ALPHA_TOL = 1e-6

#: Tolerance for graph size in inches.
SIZE_TOL = 1e-9

#: The 14 schemes Stata ships and dash must translate.
EXPECTED_SCHEMES = (
    "stcolor", "stcolor_alt", "stgcolor", "stmono1", "stmono2", "stsj",
    "s2color", "s2mono", "s2gcolor", "s1color", "s1mono", "s1rcolor",
    "economist", "sj",
)

# --- Sanity anchors: the only hardcoded expected values in this file --------
BLACK = "#000000"
ANCHOR_STCOLOR_P1 = "#1a85ff"        # color-stc1.style
ANCHOR_S2COLOR_P1 = "#1a476f"        # color-navy.style
ANCHOR_STCOLOR_GRAPHSIZE = (7.5, 4.5)
ANCHOR_SJ_GRAPHSIZE = (3.575, 2.6)


# ===========================================================================
# Fixture loading
# ===========================================================================

def _load_truth():
    """Load the ground-truth fixture, or return ({}, error-string)."""
    try:
        with open(FIXTURE_PATH, encoding="utf-8") as fh:
            return json.load(fh), None
    except Exception as exc:                                  # pragma: no cover
        return {}, f"{type(exc).__name__}: {exc}"


TRUTH, _FIXTURE_ERROR = _load_truth()

#: Scheme names to test.  Driven by the fixture; falls back to the expected 14
#: so that a missing fixture produces 14 honest failures rather than 0 tests.
SCHEME_NAMES = (
    [k for k in TRUTH if k != "_meta"] if TRUTH else list(EXPECTED_SCHEMES)
)


def truth_for(name):
    """Return the fixture entry for *name*, failing the test if absent."""
    if _FIXTURE_ERROR is not None:
        pytest.fail(f"ground-truth fixture {FIXTURE_PATH} unreadable: {_FIXTURE_ERROR}")
    if name not in TRUTH:
        pytest.fail(f"ground-truth fixture has no entry for scheme '{name}'")
    return TRUTH[name]


# ===========================================================================
# Property specification — every entry is driven by the fixture's own
# ``sources`` map (the exact "<class> <key>" directive Stata resolved through).
# Chain templates implement _meta.fallback_chain: p#stub -> pstub -> p# -> p.
# ===========================================================================

#: fixture key -> directive chain (first hit wins)
COLOR_SCALARS = {
    "background_color":    ["color background"],
    "plotregion_color":    ["color plotregion"],
    "legend_bg_color":     ["color legend"],
    "legend_border_color": ["color legend_line"],
    "grid_color":          ["color major_grid", "color grid"],
    "minor_grid_color":    ["color minor_grid"],
    "title_color":         ["color heading"],
    "axis_line_color":     ["color axisline"],
}

#: fixture key -> per-index directive chain templates
COLOR_LISTS = {
    "p_colors":      ["color p{i}", "color p"],
    "p_line_colors": ["color p{i}line", "color pline", "color p{i}", "color p"],
    "p_bar_colors":  ["color p{i}bar", "color pbar", "color p{i}", "color p"],
    "p_mark_colors": ["color p{i}mark", "color pmark", "color p{i}", "color p"],
}

#: fixture key -> per-index directive chain templates, compared as style names
NAME_LISTS = {
    "p_symbols":        ["symbol p{i}", "symbol p"],
    "p_line_patterns":  ["linepattern p{i}line", "linepattern pline",
                         "linepattern p{i}", "linepattern p"],
}

#: fixture key -> directive chain; fixture value is {"name","pct","alpha"}
ALPHA_SCALARS = {
    "fill_alpha": ["intensity p"],
    "bar_alpha":  ["intensity bar"],
    # No Stata base scheme sets "intensity area"; all 14 resolve it through the
    # bare "intensity" class default (see _meta.sources).  Either spelling in a
    # translated scheme supplies it.
    "area_alpha": ["intensity area", "intensity"],
}

#: fixture key -> directive chain; fixture value is {"name", "value", ...}
STYLE_NAME_SCALARS = {
    "default_line_width": ["linewidth p"],
    "grid_line_width":    ["linewidth major_grid"],
    "text_size":          ["gsize text"],
    "heading_size":       ["gsize heading"],
    "axis_title_size":    ["gsize axis_title"],
    "tick_label_size":    ["gsize tick_label"],
    "note_size":          ["gsize note"],
    "symbolsize":         ["symbolsize p"],
}

#: fixture key -> directive chain; fixture value is "yes"/"no"
YESNO_SCALARS = {
    "draw_major_hgrid": ["yesno draw_major_hgrid"],
    "draw_major_vgrid": ["yesno draw_major_grid"],
}

#: fixture key -> directive chain; fixture value is a float (inches)
NUMERIC_SCALARS = {
    "graphsize_x": ["graphsize x"],
    "graphsize_y": ["graphsize y"],
}

#: fixture key -> directive chain; fixture value is an int
INT_SCALARS = {
    "legend_position": ["clockdir legend_position"],
    "legend_cols":     ["numstyle legend_cols"],
}

#: Total property units per scheme: 6 lists x 15 + 25 scalars = 115.
N_PLOTS = 15


# ===========================================================================
# Helpers
# ===========================================================================

class _Missing:
    """Sentinel: SchemeParser exposes no attribute for this property."""

    __slots__ = ()

    def __repr__(self):
        return "<no SchemeParser attribute>"


MISSING = _Missing()

_PARSER_CACHE = {}


def parser_for(name):
    """Construct (and cache) a SchemeParser, re-raising any parse failure."""
    if name not in _PARSER_CACHE:
        try:
            _PARSER_CACHE[name] = (SchemeParser(name), None)
        except Exception as exc:
            _PARSER_CACHE[name] = (None, exc)
    sp, exc = _PARSER_CACHE[name]
    if exc is not None:
        raise exc
    return sp


def scheme_path(name):
    """Absolute path of the bundled .scheme file for *name*."""
    return os.path.join(SCHEMES_DIR, name + ".scheme")


def raw_props(sp):
    """The parser's flat directive dict (see module docstring)."""
    return getattr(sp, "_props", {})


def declared(sp, chain, index=None):
    """First directive value along *chain*, or None if the scheme supplies none."""
    props = raw_props(sp)
    for template in chain:
        key = template.format(i=index) if index is not None else template
        val = props.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def attr(sp, name):
    """SchemeParser attribute *name*, or MISSING."""
    return getattr(sp, name, MISSING)


def hex_to_rgb(value):
    """Parse '#rrggbb' to (r, g, b), or None if not a hex colour string."""
    if not isinstance(value, str):
        return None
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", value.strip())
    if not m:
        return None
    h = m.group(1)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def colors_close(expected, actual, tol=COLOR_CHANNEL_TOL):
    """True when two hex colours agree within *tol* on every RGB channel."""
    e, a = hex_to_rgb(expected), hex_to_rgb(actual)
    if e is None or a is None:
        return False
    return all(abs(x - y) <= tol for x, y in zip(e, a))


def names_equal(expected, actual):
    """Exact style-name comparison (scheme files are case-insensitive)."""
    if not isinstance(expected, str) or not isinstance(actual, str):
        return False
    return expected.strip().lower() == actual.strip().lower()


def include_targets(path, _seen=None):
    """Return (resolved, unresolved) #include names reachable from *path*."""
    resolved, unresolved = [], []
    _seen = _seen if _seen is not None else set()
    real = os.path.realpath(path)
    if real in _seen or not os.path.isfile(path):
        return resolved, unresolved
    _seen.add(real)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("#include"):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                unresolved.append(line)
                continue
            target = parts[1].strip()
            fname = target if target.endswith(".scheme") else target + ".scheme"
            tpath = os.path.join(SCHEMES_DIR, fname)
            if os.path.isfile(tpath):
                resolved.append(target)
                sub_r, sub_u = include_targets(tpath, _seen)
                resolved.extend(sub_r)
                unresolved.extend(sub_u)
            else:
                unresolved.append(target)
    return resolved, unresolved


# ===========================================================================
# The evaluation core — one pass produces both the fidelity mismatches and
# the coverage numbers, so the two can never disagree about what was checked.
# ===========================================================================

Check = namedtuple("Check", "prop label expected actual supplied faithful note")


def _check(prop, label, expected, actual, supplied, faithful, note=""):
    return Check(prop, label, expected, actual, supplied, faithful, note)


def evaluate_scheme(name):
    """Return the list of Check records for *name*.

    Raises whatever SchemeParser raises; callers decide how to report it.
    """
    sp = parser_for(name)
    truth = truth_for(name)
    checks = []

    # --- colour scalars ---------------------------------------------------
    for prop, chain in COLOR_SCALARS.items():
        expected = truth.get(prop)
        if expected is None:
            continue                      # Stata colour 'none'; nothing to match
        supplied = declared(sp, chain) is not None
        actual = attr(sp, prop)
        faithful = supplied and colors_close(expected, actual)
        note = "" if actual is not MISSING else f"no attribute '{prop}'"
        checks.append(_check(prop, prop, expected, actual, supplied, faithful, note))

    # --- colour cycles ----------------------------------------------------
    for prop, chain in COLOR_LISTS.items():
        expected_list = truth.get(prop) or []
        actual_list = attr(sp, prop)
        for i in range(1, N_PLOTS + 1):
            expected = expected_list[i - 1] if len(expected_list) >= i else None
            if expected is None:
                continue
            supplied = declared(sp, chain, index=i) is not None
            if isinstance(actual_list, list) and len(actual_list) >= i:
                actual = actual_list[i - 1]
            else:
                actual = MISSING
            faithful = supplied and colors_close(expected, actual)
            checks.append(_check(prop, f"{prop}[p{i}]", expected, actual,
                                 supplied, faithful))

    # --- style-name cycles (symbols, line patterns) -----------------------
    for prop, chain in NAME_LISTS.items():
        expected_list = truth.get(prop) or []
        for i in range(1, N_PLOTS + 1):
            expected = expected_list[i - 1] if len(expected_list) >= i else None
            if expected is None:
                continue
            actual = declared(sp, chain, index=i)
            supplied = actual is not None
            faithful = supplied and names_equal(expected, actual)
            checks.append(_check(prop, f"{prop}[p{i}]", expected,
                                 actual if supplied else MISSING,
                                 supplied, faithful))

    # --- intensities ------------------------------------------------------
    for prop, chain in ALPHA_SCALARS.items():
        spec = truth.get(prop) or {}
        expected = spec.get("alpha")
        if expected is None:
            continue
        supplied = declared(sp, chain) is not None
        actual = attr(sp, prop)
        faithful = (
            supplied
            and isinstance(actual, (int, float))
            and abs(float(actual) - float(expected)) <= ALPHA_TOL
        )
        checks.append(_check(prop, prop, expected, actual, supplied, faithful))

    # --- declared style names (line widths, gsize, symbolsize) ------------
    for prop, chain in STYLE_NAME_SCALARS.items():
        spec = truth.get(prop) or {}
        expected = spec.get("name")
        if expected is None:
            continue
        actual = declared(sp, chain)
        supplied = actual is not None
        faithful = supplied and names_equal(expected, actual)
        checks.append(_check(prop, prop, expected,
                             actual if supplied else MISSING,
                             supplied, faithful,
                             note="compared as declared style name"))

    # --- yes/no switches --------------------------------------------------
    for prop, chain in YESNO_SCALARS.items():
        expected = truth.get(prop)
        if expected is None:
            continue
        actual = declared(sp, chain)
        supplied = actual is not None
        faithful = supplied and names_equal(expected, actual)
        checks.append(_check(prop, prop, expected,
                             actual if supplied else MISSING,
                             supplied, faithful))

    # --- numeric scalars (graph size, inches) -----------------------------
    for prop, chain in NUMERIC_SCALARS.items():
        expected = truth.get(prop)
        if expected is None:
            continue
        supplied = declared(sp, chain) is not None
        actual = attr(sp, prop)
        faithful = (
            supplied
            and isinstance(actual, (int, float))
            and abs(float(actual) - float(expected)) <= SIZE_TOL
        )
        note = "" if actual is not MISSING else f"SchemeParser exposes no '{prop}'"
        checks.append(_check(prop, prop, expected, actual, supplied, faithful, note))

    # --- integer scalars (legend position / columns) ----------------------
    for prop, chain in INT_SCALARS.items():
        expected = truth.get(prop)
        if expected is None:
            continue
        supplied = declared(sp, chain) is not None
        actual = attr(sp, prop)
        faithful = (
            supplied
            and isinstance(actual, (int, float))
            and int(actual) == int(expected)
        )
        note = "" if actual is not MISSING else f"SchemeParser exposes no '{prop}'"
        checks.append(_check(prop, prop, expected, actual, supplied, faithful, note))

    return checks


def format_check(chk):
    """One-line human-readable rendering of a failed Check."""
    tail = f"  [{chk.note}]" if chk.note else ""
    if not chk.supplied:
        return f"    {chk.label}: NOT SUPPLIED by the .scheme file (Stata: {chk.expected!r}){tail}"
    return f"    {chk.label}: expected {chk.expected!r}, got {chk.actual!r}{tail}"


def coverage(checks):
    """Return (n_total, n_supplied, n_faithful)."""
    return (
        len(checks),
        sum(1 for c in checks if c.supplied),
        sum(1 for c in checks if c.faithful),
    )


# ===========================================================================
# 0. Fixture integrity and harness assumptions
# ===========================================================================

def test_fixture_is_present_and_complete():
    """The ground-truth fixture exists and covers exactly the 14 schemes."""
    assert _FIXTURE_ERROR is None, (
        f"cannot read {FIXTURE_PATH}: {_FIXTURE_ERROR}"
    )
    assert "_meta" in TRUTH, "fixture is missing its _meta block"
    names = sorted(k for k in TRUTH if k != "_meta")
    assert names == sorted(EXPECTED_SCHEMES), (
        f"fixture covers {names}, expected {sorted(EXPECTED_SCHEMES)}"
    )


def test_fixture_sanity_anchors():
    """Hand-verified anchors, so a bad regeneration cannot pass silently.

    These are the only hardcoded expected values in this file.  Each was
    cross-checked against Stata's own style files and against an SVG render
    (see the fixture's _meta and the extractor's cross-check notes).
    """
    assert TRUTH["stcolor"]["p_colors"][0] == ANCHOR_STCOLOR_P1     # color-stc1.style
    assert TRUTH["s2color"]["p_colors"][0] == ANCHOR_S2COLOR_P1     # color-navy.style
    assert (TRUTH["stcolor"]["graphsize_x"],
            TRUTH["stcolor"]["graphsize_y"]) == ANCHOR_STCOLOR_GRAPHSIZE
    assert (TRUTH["sj"]["graphsize_x"],
            TRUTH["sj"]["graphsize_y"]) == ANCHOR_SJ_GRAPHSIZE
    assert TRUTH["stcolor"]["p_colors"][0] != BLACK


def test_scheme_parser_exposes_props():
    """Guard the private ``_props`` dict this harness reads style names from."""
    sp = SchemeParser("s2color")
    props = getattr(sp, "_props", None)
    assert isinstance(props, dict) and props, (
        "SchemeParser._props is no longer a populated dict; the declared-style-name "
        "comparisons in this file need updating to the parser's new internals."
    )
    assert "color p1" in props, (
        "SchemeParser._props no longer keys directives as '<class> <key>'; "
        "update the chain templates in this file."
    )


# ===========================================================================
# 1. All 14 schemes resolve, with no silent fallback
# ===========================================================================

@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_scheme_resolves(name):
    """Every one of Stata's 14 schemes is a real, parseable dash scheme.

    "Without falling back" means three things: the file exists in schemes/, the
    parser does not raise, and no ``#include`` in the chain was silently skipped
    (SchemeParser._parse_file swallows an unresolvable include with a bare
    ``except ValueError: pass``, which would leave a child scheme parented on
    nothing).  The name must also be in the parser's declared built-in set.
    """
    path = scheme_path(name)
    file_exists = os.path.isfile(path)
    assert file_exists, (
        f"dash ships no translated scheme for '{name}': {path} does not exist"
    )

    _resolved, unresolved = include_targets(path)
    assert not unresolved, (
        f"scheme '{name}' #includes {unresolved}, which do not exist in "
        f"{SCHEMES_DIR}; SchemeParser would silently skip them"
    )

    try:
        sp = parser_for(name)
    except Exception as exc:
        pytest.fail(f"SchemeParser('{name}') raised {type(exc).__name__}: {exc}")

    assert raw_props(sp), f"scheme '{name}' parsed to zero directives"
    assert name in SchemeParser._BUILTIN_NAMES, (
        f"'{name}' is not in SchemeParser._BUILTIN_NAMES "
        f"({sorted(SchemeParser._BUILTIN_NAMES)}); dash does not advertise it as "
        "a supported scheme"
    )


# ===========================================================================
# 2. Every captured property matches the fixture
# ===========================================================================

@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_scheme_property_fidelity(name):
    """Each fixture property matches what dash resolves for that scheme."""
    try:
        checks = evaluate_scheme(name)
    except Exception as exc:
        pytest.fail(f"SchemeParser('{name}') raised {type(exc).__name__}: {exc}")

    bad = [c for c in checks if not c.faithful]
    if bad:
        total, supplied, faithful = coverage(checks)
        lines = "\n".join(format_check(c) for c in bad)
        pytest.fail(
            f"scheme '{name}': {len(bad)} of {total} properties do not match "
            f"Stata's own scheme (faithful {faithful}/{total}, "
            f"supplied {supplied}/{total}):\n{lines}"
        )


# ===========================================================================
# 3. Full 15-entry cycles for colour, symbol and line pattern
# ===========================================================================

@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_scheme_defines_all_15_p_entries(name):
    """p1-p15 must be spelled out for colour, symbol and line pattern.

    SchemeParser reads ``color p{i}``, ``symbol p{i}`` and ``linepattern
    p{i}line`` by exact key — it implements no stub fallback — so a translated
    scheme that relies on Stata's bare ``symbol p`` default would silently give
    every plot the parser's hardcoded default instead.
    """
    try:
        sp = parser_for(name)
    except Exception as exc:
        pytest.fail(f"SchemeParser('{name}') raised {type(exc).__name__}: {exc}")

    props = raw_props(sp)
    missing = []
    for i in range(1, N_PLOTS + 1):
        for key in (f"color p{i}", f"symbol p{i}", f"linepattern p{i}line"):
            if not str(props.get(key, "")).strip():
                missing.append(key)
    assert not missing, (
        f"scheme '{name}' does not define {len(missing)} of the 45 required "
        f"p1-p15 entries: {missing}"
    )

    for prop in ("p_colors", "p_line_colors", "p_bar_colors", "p_mark_colors",
                 "p_symbols", "p_line_patterns"):
        value = attr(sp, prop)
        assert isinstance(value, list) and len(value) == N_PLOTS, (
            f"scheme '{name}': SchemeParser.{prop} is {value!r}, expected a "
            f"{N_PLOTS}-element list"
        )


# ===========================================================================
# 4. THE REGRESSION THIS SECTION EXISTS FOR
# ===========================================================================

def test_color_does_not_swallow_unresolvable_token():
    """``SchemeParser._color`` must not turn an unknown colour token into black.

    dash_render.py:863 ``_color()`` catches ValueError from
    ``translate_mcolor`` and returns its ``default`` argument; dash_render.py:934
    calls it for every ``color p{i}`` with no default, so the default is
    ``"#000000"``.  Stata's stcolor names its palette ``stc1``-``stc15``, which
    dash's colour table does not know, so a faithful stcolor translation renders
    every single series black.  Swallowing the failure is the defect: an
    unresolvable colour token must either resolve or be reported, never be
    silently recoloured black.
    """
    sp = SchemeParser("s2color")
    sp._props = dict(sp._props)
    sp._props["color p1"] = "stc1"

    resolved = None
    raised = None
    try:
        resolved = sp._color("color p1")
    except Exception as exc:
        raised = exc

    if raised is not None:
        return          # reporting the bad token is an acceptable outcome

    assert resolved != BLACK, (
        "SchemeParser._color('color p1') silently returned "
        f"{resolved!r} for the unresolvable token 'stc1' instead of resolving "
        "it or reporting it (dash_render.py:863, default at the call site on "
        "line 934). This is why the real stcolor scheme renders every series "
        "black."
    )
    assert colors_close(ANCHOR_STCOLOR_P1, resolved), (
        f"'stc1' resolved to {resolved!r}, expected {ANCHOR_STCOLOR_P1} "
        "(color-stc1.style)"
    )


def test_stcolor_p1_is_not_black():
    """stcolor's first plot colour is Stata's stc1 blue, not black."""
    try:
        sp = parser_for("stcolor")
    except Exception as exc:
        pytest.fail(f"SchemeParser('stcolor') raised {type(exc).__name__}: {exc}")

    expected = truth_for("stcolor")["p_colors"][0]
    assert expected == ANCHOR_STCOLOR_P1          # fixture sanity
    actual = sp.p_colors[0]
    assert actual != BLACK, (
        "stcolor p1 is #000000 — the unresolvable-colour fallback in "
        "SchemeParser._color has swallowed 'stc1' and made every series black"
    )
    assert colors_close(expected, actual), (
        f"stcolor p1: expected {expected} (color-stc1.style), got {actual}"
    )


# ===========================================================================
# 5. Graph size (consumed by section 10)
# ===========================================================================

@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_scheme_defines_graphsize(name):
    """Every translated scheme declares graphsize x/y and dash exposes them."""
    try:
        sp = parser_for(name)
    except Exception as exc:
        pytest.fail(f"SchemeParser('{name}') raised {type(exc).__name__}: {exc}")

    truth = truth_for(name)
    props = raw_props(sp)
    for directive, prop in (("graphsize x", "graphsize_x"),
                            ("graphsize y", "graphsize_y")):
        declared_value = str(props.get(directive, "")).strip()
        assert declared_value, (
            f"scheme '{name}' declares no '{directive}' "
            f"(Stata: {truth[prop]} inches)"
        )
        value = attr(sp, prop)
        assert value is not MISSING, (
            f"SchemeParser exposes no '{prop}' attribute; section 10 cannot size "
            f"the figure from the scheme (Stata '{name}': {truth[prop]} inches)"
        )
        matches = (
            isinstance(value, (int, float))
            and abs(float(value) - float(truth[prop])) <= SIZE_TOL
        )
        assert matches, (
            f"scheme '{name}' {prop}: expected {truth[prop]}, got {value!r}"
        )


# ===========================================================================
# 6. Coverage harness
# ===========================================================================

@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_scheme_coverage(name):
    """Faithful coverage of each scheme's fixture properties clears the gate.

    See COVERAGE HARNESS in the module docstring: ``faithful`` is gated,
    ``supplied`` is reported alongside it so that "the file mentions the
    property" can never be mistaken for "the file gets it right".
    """
    try:
        checks = evaluate_scheme(name)
    except Exception as exc:
        pytest.fail(f"SchemeParser('{name}') raised {type(exc).__name__}: {exc}")

    total, n_supplied, n_faithful = coverage(checks)
    assert total, f"no properties were evaluated for scheme '{name}'"

    frac_faithful = n_faithful / total
    frac_supplied = n_supplied / total
    if frac_faithful < COVERAGE_THRESHOLD:
        worst = [c for c in checks if not c.faithful][:15]
        lines = "\n".join(format_check(c) for c in worst)
        more = len([c for c in checks if not c.faithful]) - len(worst)
        pytest.fail(
            f"scheme '{name}': faithful coverage {frac_faithful:.3f} "
            f"({n_faithful}/{total}) is below the {COVERAGE_THRESHOLD:.2f} "
            f"threshold; presence-only coverage {frac_supplied:.3f} "
            f"({n_supplied}/{total}).\n"
            f"  first {len(worst)} shortfalls"
            f"{f' (+{more} more)' if more > 0 else ''}:\n{lines}"
        )


# ===========================================================================
# 6b. dash must be able to express what the fixture declares
# ===========================================================================

@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_translator_can_express_scheme_symbols_and_patterns(name):
    """Every symbol / line-pattern name Stata's scheme uses is translatable.

    This is a precondition for section 03's translations, not a nicety:
    ``SchemeParser._lpattern`` calls ``translate_lpattern`` with no try/except,
    so a faithful ``s1mono`` that declares ``linepattern p3line vshortdash``
    makes ``SchemeParser('s1mono')`` raise outright.  ``_symbol`` is the quieter
    version of the same problem — it swallows the ValueError and silently
    substitutes a circle.
    """
    truth = truth_for(name)

    bad_symbols, bad_patterns = [], []
    for sym in dict.fromkeys(truth.get("p_symbols") or []):
        try:
            OptionTranslator.translate_msymbol(sym)
        except Exception as exc:
            bad_symbols.append(f"{sym} ({type(exc).__name__})")
    for pat in dict.fromkeys(truth.get("p_line_patterns") or []):
        try:
            OptionTranslator.translate_lpattern(pat)
        except Exception as exc:
            bad_patterns.append(f"{pat} ({type(exc).__name__})")

    assert not (bad_symbols or bad_patterns), (
        f"scheme '{name}' uses marker symbols dash cannot translate "
        f"{bad_symbols} and line patterns dash cannot translate {bad_patterns}; "
        "a faithful translation of this scheme cannot be parsed until "
        "OptionTranslator learns them"
    )


# ===========================================================================
# 7. Unknown scheme names are rejected by name
# ===========================================================================

# Was xfail pending section 11.  It now passes: _BUILTIN_NAMES lists all 14
# translated schemes, so the not-found message names the supported set.  The
# marker is removed rather than left in place, because an xfail that passes is
# itself a landmine -- it reports green while asserting nothing is expected.
# Section 11 still owns the REST of the restriction (refusing an arbitrary
# .scheme path outright rather than degrading to it).
def test_unknown_scheme_rejected_with_supported_set():
    """An unsupported scheme name fails loudly and names what IS supported."""
    with pytest.raises(ValueError) as excinfo:
        SchemeParser("not_a_real_stata_scheme")

    message = str(excinfo.value)
    missing = [n for n in EXPECTED_SCHEMES if n not in message]
    assert not missing, (
        "rejection message does not name the supported scheme set — missing "
        f"{missing}. Message was: {message}"
    )
