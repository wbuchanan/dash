# -*- coding: utf-8 -*-
"""test_scheme_fidelity.py — fidelity of dash's translated Stata schemes.

WHAT THIS FILE IS
-----------------
Section 03 of the plan translates Stata's 14 shipped graph schemes into dash
``.scheme`` files; section 11 makes ``dash_render`` consume them; WP-17 adds
the six user-selectable StataCorp schemes that were still missing (s2manual,
s1manual, s2gmanual, s2color8, sttrans, stgcolor_alt), making twenty; WP-30
P1.25a adds StataCorp's six internal schemes (meta, stcolor_meta, stcolor_mv,
stcoloralias, stgcolor_meta, stgcolor_mv), making twenty-six.  This file is
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
   symbols and line patterns.  The fixture's ``_meta.units`` records Stata's
   own ladders for these (style-file value and the point size at Stata's
   4-inch reference), but dash's pt/px *translation* of them is the renderer's
   business and is pinned by the rendered-output tests, not here.  So for
   these the test compares the Stata style *name* the translated ``.scheme``
   file declares against the name Stata's own scheme declares — exact string
   match, which is exactly what the translation controls.

   ``p_line_dash_patterns`` is therefore excluded from the comparison entirely:
   it is the same information as ``p_line_patterns`` expressed in Stata's
   undocumented dash units, and no unit mapping to Bokeh's pixel dash arrays
   exists in the fixture.  ``p_line_patterns`` (the names) carries the fidelity.

COVERAGE HARNESS
----------------
``test_scheme_coverage`` reports two fractions per scheme over the same 133
property units (``expected_units``):

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
SCHEMES_DIR = REPO_ROOT

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

#: The 26 schemes Stata ships in BASE/s, every one of which dash translates.
EXPECTED_SCHEMES = (
    "stcolor", "stcolor_alt", "stgcolor", "stmono1", "stmono2", "stsj",
    "s2color", "s2mono", "s2gcolor", "s1color", "s1mono", "s1rcolor",
    "economist", "sj",
    # WP-17: the six that were missing.
    "s2manual", "s1manual", "s2gmanual", "s2color8", "sttrans", "stgcolor_alt",
    # WP-30 P1.25a: StataCorp's six internal schemes
    "meta", "stcolor_meta", "stcolor_mv", "stcoloralias", "stgcolor_meta",
    "stgcolor_mv",
)

#: The six WP-17 added, kept apart so their tests can name them.
WP17_SCHEMES = (
    "s2manual", "s1manual", "s2gmanual", "s2color8", "sttrans", "stgcolor_alt",
)

#: WP-17 sanity anchors, read off Stata's own files and one SVG export.
ANCHOR_S2COLOR8_P1 = "#273f6f"           # color-navy8.style: 39 63 111
ANCHOR_S2COLOR8_BACKGROUND = "#e1e6f0"   # color-ltbluishgray8.style: 225 230 240
ANCHOR_S2GMANUAL_P2LINEPLOT = "#a0a0a0"  # scheme-s2gmanual.scheme: color p2lineplot gs10
ANCHOR_STTRANS_P1 = "#1a476f"            # scheme-sttrans.scheme: "26 71 111 %20"
ANCHOR_STTRANS_OPACITY = 20.0            # ... and the %20 is a real 0.20 fill-opacity
ANCHOR_MANUAL_GRAPHSIZE = (3.12, 2.392)  # s2manual, s1manual, s2gmanual

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

#: Scheme names to test.  Driven by the fixture; falls back to the expected 20
#: so that a missing fixture produces 20 honest failures rather than 0 tests.
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
    # One colour per textbox style.  style/textboxstyle-<name>.style reads
    # `color <name>': subtitle() is subheading, caption() body, legend keys
    # key_label, axis titles axis_title, tick labels tick_label.  (note() is
    # small_body, whose colour key `color small_body' the fixture also
    # records; the parser exposes no attribute for it yet.)
    "subheading_color":    ["color subheading"],
    "body_color":          ["color body"],
    "small_body_color":    ["color small_body"],
    "text_color":          ["color text"],
    "axis_title_color":    ["color axis_title"],
    "tick_label_color":    ["color tick_label"],
    "key_label_color":     ["color key_label"],
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
    # No Stata base scheme sets "intensity area"; all 20 resolve it through the
    # bare "intensity" class default (see _meta.sources).  Either spelling in a
    # translated scheme supplies it.
    "area_alpha": ["intensity area", "intensity"],
}

#: Graph bar's intensity keys, which twoway's bar and area ignore (measured,
#: WP-30 P1.2b): SchemeParser no longer parses them into an attribute, so
#: the file's transcription is checked through the declared directive,
#: read by SchemeParser._intensity, instead.
RETIRED_INTENSITY = {"bar_alpha", "area_alpha"}

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
    # The textbox sizes Stata draws subtitle(), caption(), note() and the
    # legend keys with.  Stata's note textbox uses small_body, not `gsize
    # note'; both are recorded so the file is checked for what it declares.
    "subheading_size":    ["gsize subheading"],
    "body_size":          ["gsize body"],
    "small_body_size":    ["gsize small_body"],
    "key_label_size":     ["gsize key_label"],
    "minor_grid_line_width": ["linewidth minor_grid"],
    "axis_line_width":    ["linewidth axisline"],
}

#: fixture key -> directive chain; fixture value is "yes"/"no"
YESNO_SCALARS = {
    "draw_major_hgrid": ["yesno draw_major_hgrid"],
    # The y-axis key is `draw_major_vgrid'.  `draw_major_grid' is dead at
    # scheme level and is `no' in every scheme, so keying on it made this
    # fidelity check agree with a wrong value rather than catch it.
    "draw_major_vgrid": ["yesno draw_major_vgrid"],
    # Minor grid switches, same axis mapping.  The fixture holds the
    # EFFECTIVE per-axis value, resolved through the scheme's `axisstyle'
    # indirection (economist's y axis is `vertical_nolinetick', whose style
    # file reads draw_major_nlt_vgrid / draw_minor_nlt_vgrid), and the
    # translated file must carry that effective value under the key dash
    # reads.  The two bare keys are dead at scheme level and are checked
    # only as faithful transcriptions.
    "draw_minor_hgrid": ["yesno draw_minor_hgrid"],
    "draw_minor_vgrid": ["yesno draw_minor_vgrid"],
    "draw_major_grid":  ["yesno draw_major_grid"],
    "draw_minor_grid":  ["yesno draw_minor_grid"],
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
    "legend_rows":     ["numstyle legend_rows"],
}

#: Total property units per scheme: 6 lists x 15 + 43 scalars = 133
#: (expected_units(); it read 132 before a colour scalar was added).
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
    return os.path.join(SCHEMES_DIR, "dash-" + name + ".scheme")


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
            base = target[:-len(".scheme")] if target.endswith(".scheme") else target
            fname = "dash-" + base + ".scheme"
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
        if prop in RETIRED_INTENSITY:
            key = next((k for k in chain if declared(sp, [k]) is not None),
                       None)
            actual = sp._intensity(key) if key is not None else MISSING
        else:
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


def expected_units(truth):
    """How many Check records evaluate_scheme must return for *truth*.

    One unit per list entry and per scalar the property maps name: 6 lists
    x 15 + 43 scalars = 133, and each of the twenty schemes returned exactly
    133 (measured 24sep2026).  The one unit evaluate_scheme may rightly
    skip is a colour Stata writes as 'none', which the fixture records as a
    PRESENT JSON null (_meta.color_none).  A missing key, a missing
    'alpha' / 'name' sub-key or a list shorter than 15 is fixture drift,
    and evaluate_scheme skips those in silence -- so they count here, and a
    check that silently fell away shows up as a short total.
    """
    n = (len(COLOR_LISTS) + len(NAME_LISTS)) * N_PLOTS + sum(
        len(m) for m in (COLOR_SCALARS, ALPHA_SCALARS, STYLE_NAME_SCALARS,
                         YESNO_SCALARS, NUMERIC_SCALARS, INT_SCALARS))
    n -= sum(1 for p in COLOR_SCALARS if p in truth and truth[p] is None)
    for p in COLOR_LISTS:
        entries = truth.get(p)
        if isinstance(entries, list) and len(entries) == N_PLOTS:
            n -= sum(1 for v in entries if v is None)
    return n


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
    """The ground-truth fixture exists and covers exactly the 26 schemes."""
    assert _FIXTURE_ERROR is None, (
        f"cannot read {FIXTURE_PATH}: {_FIXTURE_ERROR}"
    )
    assert "_meta" in TRUTH, "fixture is missing its _meta block"
    names = sorted(k for k in TRUTH if k != "_meta")
    assert names == sorted(EXPECTED_SCHEMES), (
        f"fixture covers {names}, expected {sorted(EXPECTED_SCHEMES)}"
    )

    # Every fixture key the property maps name must be present for every
    # scheme.  evaluate_scheme() skips a property whose fixture value is
    # absent, so a key missing from a regenerated fixture would turn its
    # check into a silent pass rather than a failure.
    wanted = sorted(set(COLOR_SCALARS) | set(COLOR_LISTS) | set(NAME_LISTS)
                    | set(ALPHA_SCALARS) | set(STYLE_NAME_SCALARS)
                    | set(YESNO_SCALARS) | set(NUMERIC_SCALARS)
                    | set(INT_SCALARS))
    missing = {
        name: [k for k in wanted if TRUTH[name].get(k) is None]
        for name in names
    }
    missing = {n: ks for n, ks in missing.items() if ks}
    assert not missing, (
        "fixture entries lack keys the property maps check: "
        f"{missing}; regenerate with scripts/extract_scheme_truth.py"
    )

    # The unit ladders the renderer's size translation is measured against.
    units = TRUTH["_meta"].get("units") or {}
    for ladder in ("gsize", "symbolsize", "linewidth"):
        table = (units.get(ladder) or {}).get("ladder")
        assert isinstance(table, dict) and "medium" in table, (
            f"fixture _meta.units.{ladder}.ladder is missing or has no "
            "'medium' entry"
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
# 1. All 26 schemes resolve, with no silent fallback
# ===========================================================================

@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_scheme_resolves(name):
    """Every one of Stata's 26 schemes is a real, parseable dash scheme.

    "Without falling back" means three things: the file dash-<name>.scheme exists, the
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

    # Every unit must have been checked: an empty or shortened list of
    # checks has no unfaithful entry either, and passed below.
    want = expected_units(truth_for(name))
    assert len(checks) == want, (
        f"scheme '{name}': {len(checks)} properties were evaluated, not "
        f"{want}; evaluate_scheme skipped fixture entries in silence"
    )
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
    """p1-p15 must be supplied for colour, symbol and line pattern.

    ``color p{i}`` is spelled out.  The marker symbol follows Stata's chain
    ``symbol p{i} -> symbol p`` in the parser (S3 batch): the shipped files
    carry only the key the chain declares (s2color's bare ``symbol p``,
    s1mono's and s2mono's ``symbol p1``..``p15``), so one step of it must be
    present for every p#.  The connecting line's pattern follows Stata's chain
    ``linepattern p{i}line -> pline -> p{i} -> p`` in the parser (S3 batch),
    and the shipped files carry only the key the chain declares, so some
    step of that chain must be present for every p#.
    """
    try:
        sp = parser_for(name)
    except Exception as exc:
        pytest.fail(f"SchemeParser('{name}') raised {type(exc).__name__}: {exc}")

    props = raw_props(sp)
    missing = []
    for i in range(1, N_PLOTS + 1):
        if not str(props.get(f"color p{i}", "")).strip():
            missing.append(f"color p{i}")
        if declared(sp, NAME_LISTS["p_symbols"], i) is None:
            missing.append(f"symbol p{i} (or p)")
        if declared(sp, NAME_LISTS["p_line_patterns"], i) is None:
            missing.append(f"linepattern p{i}line (or pline, p{i}, p)")
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

    Both halves are asserted as measured (24sep2026).  This used to catch
    any exception and return -- "reporting the bad token is an acceptable
    outcome" -- so a ``_color`` that crashed passed; ``_color`` reports an
    unresolvable token with a warning, not an exception, and resolves stc1.
    """
    import warnings

    sp = SchemeParser("s2color")
    sp._props = dict(sp._props)
    sp._props["color p1"] = "stc1"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        resolved = sp._color("color p1")

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
    assert not [str(w.message) for w in caught], (
        "stc1 resolved, and a note still claimed it could not be: %r"
        % [str(w.message) for w in caught])

    # A token no colour table knows is reported by name, not recoloured in
    # silence.
    sp._props["color p1"] = "definitely_not_a_colour"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        sp._color("color p1")
    notes = [str(w.message) for w in caught]
    assert any("'definitely_not_a_colour'" in m and "'color p1'" in m
               for m in notes), notes


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
    # `total' alone passed one check out of 133 -- and a fraction is only
    # as honest as its denominator.
    want = expected_units(truth_for(name))
    assert total == want, (
        f"scheme '{name}': {total} properties were evaluated, not {want}; "
        "evaluate_scheme skipped fixture entries in silence"
    )

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

    # A missing or empty fixture list made both loops run zero times and
    # the test pass having translated nothing (24sep2026).
    for key in ("p_symbols", "p_line_patterns"):
        assert len(truth.get(key) or []) == N_PLOTS, (
            f"scheme '{name}': fixture {key} is {truth.get(key)!r}, not a "
            f"{N_PLOTS}-entry list"
        )

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

# Was xfail pending section 11.  It now passes: _BUILTIN_NAMES lists all 20
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


# ===========================================================================
# 8. WP-17: the six added schemes, provenance, and the extractor itself
# ===========================================================================
#
# These were written before the six files and the provenance block existed
# (project rule 8), against scripts/extract_scheme_truth.py, which the fixture
# and the shipped files are generated from.

import importlib.util
import shutil

EXTRACTOR_PATH = os.path.join(REPO_ROOT, "scripts", "extract_scheme_truth.py")

_PROVENANCE_BEGIN = "* BEGIN provenance (WP-17)"
_PROVENANCE_END = "* END provenance (WP-17)"
_PROVENANCE_LINE = re.compile(r"^\* provenance: (\S+) (\S+) -- (.*)$")


def _extractor():
    """The extractor as a module (it is a script, not a package).

    Bytecode writing is suppressed while it loads so the import does not
    leave a scripts/__pycache__/ behind (which .gitignore does not cover).
    """
    spec = importlib.util.spec_from_file_location("extract_scheme_truth",
                                                  EXTRACTOR_PATH)
    mod = importlib.util.module_from_spec(spec)
    was = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = was
    return mod


def _file_directives(path):
    """``(class, key) -> value`` for every directive line of a shipped file,
    read the way SchemeParser reads them (the last token is the value)."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if (not line or line.startswith("*") or line.startswith("#include")
                    or line.startswith("label")):
                continue
            tokens = line.split()
            if len(tokens) < 3:
                continue
            out[(tokens[0].lower(), tokens[1].lower())] = tokens[-1]
    return out


def _provenance_lines(path):
    """``(class, key) -> text`` from the file's provenance block, plus whether
    the block's sentinels were both found."""
    lines = open(path, encoding="utf-8").read().split("\n")
    if _PROVENANCE_BEGIN not in lines or _PROVENANCE_END not in lines:
        return {}, False
    start, end = lines.index(_PROVENANCE_BEGIN), lines.index(_PROVENANCE_END)
    out = {}
    for line in lines[start + 1:end]:
        m = _PROVENANCE_LINE.match(line)
        if m:
            out[(m.group(1).lower(), m.group(2).lower())] = m.group(3)
    return out, start < end


def test_extractor_schemes_list_is_the_twenty():
    """One list: the extractor's SCHEMES is exactly EXPECTED_SCHEMES."""
    mod = _extractor()
    assert sorted(mod.SCHEMES) == sorted(EXPECTED_SCHEMES), (
        f"extractor SCHEMES {sorted(mod.SCHEMES)} != {sorted(EXPECTED_SCHEMES)}"
    )
    assert len(mod.SCHEMES) == 26  # 20 -> 26: P1.25a ships the six StataCorp schemes


def test_extractor_reads_a_directive_value_as_stata_does(tmp_path):
    """Stata's scheme.class ``setscheme`` does ``tokenize`` then
    ``args style id stylename``: the value is the THIRD token, a quoted
    string is one token, and anything after the third token is ignored.
    scheme-sttrans.scheme has ``symbolsize p small *medium``, which Stata
    reads as ``small`` (measured: its marker radius in an SVG export equals
    s2color's ``msize(small)``, 19.29, not medium's 26.35).  The extractor
    used to join every token after the key, giving ``small *medium``."""
    mod = _extractor()
    base = tmp_path / "base"
    (base / "s").mkdir(parents=True)
    (base / "style").mkdir()
    (base / "s" / "scheme-t.scheme").write_text(
        "* a comment\n"
        "symbolsize p       small *medium\n"
        "color p1  \"26 71 111 %20\"\n"
        "gsize text 3.9\n"
        "intensity full\n"
        "label \"t label\"\n",
        encoding="utf-8")
    r = mod.SchemeResolver(str(base))
    r.load("t")
    assert r.get("symbolsize", "p") == "small"
    assert r.get("color", "p1") == '"26 71 111 %20"'
    assert r.get("gsize", "text") == "3.9"
    assert r.get("intensity", "") == "full"
    # Where each value came from: (scheme, 1-based line).
    assert r.origins[("symbolsize", "p")] == ("t", 2)
    assert r.origins[("color", "p1")] == ("t", 3)
    assert r.origins[("intensity", "")] == ("t", 5)
    # The quoted RGB token with an opacity suffix resolves to hex + pct.
    c = mod.ColorResolver(r)
    assert c.resolve_with_opacity(r.get("color", "p1")) == ("#1a476f", 20.0)
    assert not c.unresolved, c.unresolved
    # The plain resolver still flags an opacity it cannot carry (scalar
    # colours have no opacity slot in the fixture), so nothing is dropped
    # in silence.
    assert c.resolve(r.get("color", "p1")) == "#1a476f"
    assert any("opacity" in m for m in c.unresolved), c.unresolved


def test_the_six_have_every_key_and_nothing_unresolved():
    """The six WP-17 schemes carry every key the fourteen carry, and no
    scheme reports an unresolvable token."""
    reference = set(truth_for("s2color"))
    for name in WP17_SCHEMES:
        entry = truth_for(name)
        missing = sorted(reference - set(entry))
        extra = sorted(set(entry) - reference)
        assert not missing and not extra, (
            f"{name}: fixture keys differ from s2color's -- missing {missing}, "
            f"extra {extra}"
        )
    bad = {n: truth_for(n)["unresolvable"] for n in EXPECTED_SCHEMES
           if truth_for(n).get("unresolvable")}
    assert not bad, f"unresolvable tokens: {bad}"


def test_fixture_anchors_for_the_six():
    """Hand-verified anchors for the added schemes (see the constants)."""
    assert truth_for("s2color8")["p_colors"][0] == ANCHOR_S2COLOR8_P1
    assert truth_for("s2color8")["background_color"] == ANCHOR_S2COLOR8_BACKGROUND
    assert truth_for("s2gmanual")["p_lineplot_colors"][1] == ANCHOR_S2GMANUAL_P2LINEPLOT
    assert truth_for("sttrans")["p_colors"][0] == ANCHOR_STTRANS_P1
    for name in ("s2manual", "s1manual", "s2gmanual"):
        t = truth_for(name)
        assert (t["graphsize_x"], t["graphsize_y"]) == ANCHOR_MANUAL_GRAPHSIZE, name
    assert (truth_for("stgcolor_alt")["graphsize_x"],
            truth_for("stgcolor_alt")["graphsize_y"]) == (3.588, 2.392)
    assert (truth_for("sttrans")["graphsize_x"],
            truth_for("sttrans")["graphsize_y"]) == (7.5, 4.5)
    assert truth_for("sttrans")["legend_position"] == 3
    # Stata reads `symbolsize p small *medium' as small (measured, see
    # test_extractor_reads_a_directive_value_as_stata_does).
    assert truth_for("sttrans")["symbolsize"]["name"] == "small"
    assert truth_for("s1manual")["symbolsize"]["name"] == "2.2"
    # The include chains, root -> child.
    assert truth_for("s2gmanual")["include_chain"] == ["s2color", "s2mono", "s2gmanual"]
    assert truth_for("s2manual")["include_chain"] == ["s2color", "s2mono", "s2manual"]
    assert truth_for("s1manual")["include_chain"][-2:] == ["s1mono", "s1manual"]
    assert truth_for("s2color8")["include_chain"] == ["s2color", "s2color8"]
    assert truth_for("sttrans")["include_chain"] == ["s2color", "sttrans"]
    assert truth_for("stgcolor_alt")["include_chain"][-2:] == ["stcolor_alt", "stgcolor_alt"]


def test_sttrans_opacity_is_recorded_not_flagged():
    """sttrans is the transparency scheme: every p# colour is written as
    ``"r g b %20"`` and Stata really draws it at fill-opacity 0.20.  The
    fixture keeps the hex in p_colors (what every consumer compares) and the
    percentage in p_colors_opacity, and reports nothing as unresolvable."""
    t = truth_for("sttrans")
    for key in ("p_colors", "p_line_colors", "p_bar_colors", "p_mark_colors",
                "p_lineplot_colors"):
        assert t[key + "_opacity"] == [ANCHOR_STTRANS_OPACITY] * N_PLOTS, key
        # Fifteen hex colours beside the fifteen opacities: all() over an
        # empty list passed (24sep2026).
        assert len(t[key]) == N_PLOTS, (key, t[key])
        assert all(hex_to_rgb(v) is not None for v in t[key]), key
    assert t["unresolvable"] == []
    # An opaque scheme records None, not 100.
    s = truth_for("s2color")
    assert s["p_colors_opacity"] == [None] * N_PLOTS


def test_sttrans_shipped_file_carries_the_opacity():
    """The shipped directive keeps Stata's ``%20`` (``#1a476f%20``): the
    file is the translation, and it must not say the colour is opaque.
    SchemeParser._color strips the suffix (OptionTranslator.translate_mcolor
    does), so the parsed hex is still what the fixture pins -- dash drawing
    sttrans opaque is a renderer gap, recorded in the final report, not a
    translation error."""
    sp = parser_for("sttrans")
    props = raw_props(sp)
    for i in range(1, N_PLOTS + 1):
        raw = props.get(f"color p{i}", "")
        assert raw.endswith("%20"), f"color p{i} = {raw!r}"
        # sttrans declares no p#line/bar/mark colour (Stata's chain lands on
        # p#), so the file carries none and the parser's chain carries the
        # %20 to all three (S3 batch).
        for stub in ("line", "bar", "mark"):
            assert f"color p{i}{stub}" not in props, (i, stub)
    for key in ("p_alphas", "p_line_alphas", "p_bar_alphas", "p_mark_alphas",
                "p_lineplot_alphas"):
        assert getattr(sp, key) == [ANCHOR_STTRANS_OPACITY / 100.0] * N_PLOTS, key
    assert colors_close(sp.p_colors[0], ANCHOR_STTRANS_P1)


def test_every_fixture_key_has_provenance():
    """Per scheme, ``provenance`` says for every sourced key whether the
    value was transcribed (which Stata file and directive) or inferred by
    dash (which rule), and the two maps cover the same keys."""
    for name in EXPECTED_SCHEMES:
        t = truth_for(name)
        prov = t.get("provenance")
        assert isinstance(prov, dict) and prov, f"{name}: no provenance map"
        assert set(prov) == set(t["sources"]), (
            f"{name}: provenance keys {sorted(set(prov) ^ set(t['sources']))} "
            "differ from sources keys"
        )
        for key, entry in prov.items():
            entries = entry if isinstance(entry, list) else [entry]
            for e in entries:
                if e is None:
                    assert t["sources"][key] is None or (
                        isinstance(t["sources"][key], list)
                        and None in t["sources"][key]), (name, key)
                    continue
                assert e["kind"] in ("transcribed", "inferred"), (name, key, e)
                assert e["file"] and e["directive"], (name, key, e)
                if e["kind"] == "inferred":
                    assert e.get("rule"), (name, key, e)


def test_s2gmanual_lineplot_comes_from_its_declared_directive():
    """s2gmanual is one of only two StataCorp schemes (with s2mono) that
    WRITES a ``lineplot`` directive.  Its p_lineplot_* values must be the
    declared ones -- transcribed from scheme-s2gmanual.scheme -- not the
    p#stub -> pstub -> p# -> p inference, and the shipped file must carry
    them as real directives; s2color, which declares none, must be marked
    inferred and ship none."""
    t = truth_for("s2gmanual")
    assert t["lineplot_declared"] == {"color": True, "linepattern": True}
    for i in range(1, N_PLOTS + 1):
        assert t["sources"]["p_lineplot_colors"][i - 1] == f"color p{i}lineplot"
        assert t["sources"]["p_lineplot_patterns"][i - 1] == f"linepattern p{i}lineplot"
        pc = t["provenance"]["p_lineplot_colors"][i - 1]
        pp = t["provenance"]["p_lineplot_patterns"][i - 1]
        assert (pc["kind"], pc["file"]) == ("transcribed", "scheme-s2gmanual.scheme"), pc
        assert (pp["kind"], pp["file"]) == ("transcribed", "scheme-s2gmanual.scheme"), pp
        assert pc["directive"] == f"color p{i}lineplot"
        assert pp["directive"] == f"linepattern p{i}lineplot"
    # The declared values differ from what inference would give: s2mono's
    # p2lineplot pattern is not solid, s2gmanual overrides it to solid.
    assert t["p_lineplot_patterns"] == ["solid"] * N_PLOTS
    assert truth_for("s2mono")["p_lineplot_patterns"][1] != "solid"
    assert t["p_lineplot_colors"][1] == ANCHOR_S2GMANUAL_P2LINEPLOT
    # And the shipped file writes them out.
    directives = _file_directives(scheme_path("s2gmanual"))
    for i in range(1, N_PLOTS + 1):
        assert directives.get(("color", f"p{i}lineplot")) == t["p_lineplot_colors"][i - 1]
        assert directives.get(("linepattern", f"p{i}lineplot")) == "solid"
    sp = parser_for("s2gmanual")
    assert colors_close(raw_props(sp).get("color p2lineplot"), ANCHOR_S2GMANUAL_P2LINEPLOT)

    # The contrast: s2color infers, and ships no lineplot directive.
    s = truth_for("s2color")
    assert s["lineplot_declared"] == {"color": False, "linepattern": False}
    assert s["sources"]["p_lineplot_colors"][0] == "color p1"
    assert s["provenance"]["p_lineplot_colors"][0]["kind"] == "inferred"
    assert ("color", "p1lineplot") not in _file_directives(scheme_path("s2color"))
    # And s2mono declares its own.
    m = truth_for("s2mono")
    assert m["provenance"]["p_lineplot_patterns"][0]["file"] == "scheme-s2mono.scheme"
    assert m["provenance"]["p_lineplot_patterns"][0]["kind"] == "transcribed"


@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_shipped_file_carries_one_provenance_line_per_directive(name):
    """Every shipped file ends with a provenance block: one ``* provenance:``
    line for each directive it carries, saying ``transcribed from
    scheme-X.scheme:...`` or ``inferred: ...``, and no line for a directive
    it does not carry."""
    path = scheme_path(name)
    directives = _file_directives(path)
    prov, ok = _provenance_lines(path)
    assert ok, f"{name}: no `{_PROVENANCE_BEGIN}' ... `{_PROVENANCE_END}' block"
    missing = sorted(k for k in directives if k not in prov)
    stray = sorted(k for k in prov if k not in directives)
    assert not missing, f"{name}: directives without a provenance line: {missing}"
    assert not stray, f"{name}: provenance lines for absent directives: {stray}"
    for key, text in prov.items():
        assert text.startswith("transcribed from scheme-") or \
            text.startswith("transcribed from style/") or \
            text.startswith("inferred: "), (name, key, text)


def test_shipped_provenance_agrees_with_the_fixture():
    """Spot checks that the block says what the fixture says."""
    prov, _ = _provenance_lines(scheme_path("s2gmanual"))
    assert prov[("color", "p1lineplot")].startswith(
        "transcribed from scheme-s2gmanual.scheme:")
    assert prov[("color", "p1")].startswith("transcribed from scheme-s2mono.scheme:")
    prov, _ = _provenance_lines(scheme_path("s2color"))
    # s2color declares no `color p1line': Stata's chain lands on `color
    # p1', and the file carries no p1line for a child's p1 to be shadowed
    # by (S3 batch).  `linepattern p' is the key it does declare.
    assert ("color", "p1line") not in prov
    assert ("color", "p1line") not in _file_directives(scheme_path("s2color"))
    assert prov[("linepattern", "p")].startswith(
        "transcribed from scheme-s2color.scheme:")
    assert prov[("intensity", "area")].startswith("inferred: ")
    # s2mono's connecting-line colour is its declared `color pline'.
    prov_m, _ = _provenance_lines(scheme_path("s2mono"))
    assert prov_m[("color", "pline")].startswith(
        "transcribed from scheme-s2mono.scheme:")
    assert prov[("color", "background")].startswith(
        "transcribed from scheme-s2color.scheme:")
    prov, _ = _provenance_lines(scheme_path("economist"))
    assert "draw_major_nlt_vgrid" in prov[("yesno", "draw_major_vgrid")]


@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_regenerating_a_shipped_file_is_a_no_op(name, tmp_path):
    """update_scheme_file on a copy of the shipped file, fed the fixture it
    was generated from, changes nothing: no CHANGED value, no added
    directive, and the provenance block is byte-identical."""
    mod = _extractor()
    src = scheme_path(name)
    dst = str(tmp_path / f"{name}.scheme")
    shutil.copyfile(src, dst)
    before = open(dst, "rb").read()
    result = mod.update_scheme_file(dst, name, truth_for(name),
                                    mod.DEFAULT_STATA_BASE, "01jan2000")
    assert result["changed"] == [], result
    assert result["added"] == [], result
    assert result["removed"] == [], result
    assert not result["created"]
    assert not result.get("provenance"), result
    assert open(dst, "rb").read() == before, f"{name}: file rewritten"


def test_an_older_translation_loses_its_resolved_stub_lines(tmp_path):
    """update_scheme_file on a file that still carries the p#stub chain
    written out resolved (`color p1mark' .. under s2color, as every shipped
    file did before the S3 batch) removes those lines and the comment
    paragraph that headed them, and adds the key Stata's chain declares
    (`linepattern p'); a second run changes nothing."""
    mod = _extractor()
    dst = str(tmp_path / "s2color.scheme")
    shutil.copyfile(scheme_path("s2color"), dst)
    extra = ["", "* Per-plot marker fill color (resolved, spelled out).",
             *[f"color p{i}mark   #1a476f" for i in range(1, N_PLOTS + 1)],
             "", "* Line patterns, spelled out.",
             *[f"linepattern p{i}line   solid" for i in range(1, N_PLOTS + 1)]]
    text = open(dst, encoding="utf-8").read()
    head, sep, tail = text.partition("* ---------------------------------------------------------------------------\n* BEGIN provenance")
    text = head.replace("linepattern p  solid\n", "") + "\n".join(extra) + "\n\n" + sep + tail
    open(dst, "w", encoding="utf-8").write(text)
    r = mod.update_scheme_file(dst, "s2color", truth_for("s2color"),
                               mod.DEFAULT_STATA_BASE, "01jan2000")
    assert len(r["removed"]) == 2 * N_PLOTS, r
    assert r["added"] == ["linepattern p"], r
    after = open(dst, encoding="utf-8").read()
    assert "Per-plot marker fill color (resolved" not in after
    assert "Line patterns, spelled out." not in after
    assert "color p1mark" not in after and "linepattern p1line" not in after
    r2 = mod.update_scheme_file(dst, "s2color", truth_for("s2color"),
                                mod.DEFAULT_STATA_BASE, "01jan2000")
    assert (r2["changed"], r2["added"], r2["removed"], r2["provenance"]) == (
        [], [], [], None), r2


# ===========================================================================
# S3 batch: the reference line, the plot region's border and note()'s text
# box, resolved through Stata's style files by the extractor.
# ===========================================================================

_S3_KEYS = ("xyline_drawn", "xyline_color", "xyline_pattern",
            "xyline_line_width", "plotregion_line_drawn",
            "plotregion_line_color", "plotregion_line_line_width",
            "plotregion_line_pattern", "note_textbox", "note_text_size",
            "note_text_color", "note_box_drawn", "note_box_fill_color")


@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_the_s3_keys_are_resolved(name):
    t = truth_for(name)
    missing = [k for k in _S3_KEYS if k not in t]
    assert not missing, f"{name}: {missing}; regenerate the fixture"
    assert t["xyline_drawn"] and t["xyline_color"], name
    assert t["note_text_size"]["value"] and t["note_text_color"], name
    assert t["note_box_drawn"] == (t["note_box_fill_color"] is not None)


def test_the_s3_anchors():
    """Against Stata's SVG export (test/fixtures/scheme_visual/truth.json,
    measured 24sep2026) and BUGS.md's measurement of xline()."""
    s2, st = truth_for("s2color"), truth_for("stcolor")
    # twoway scatter mpg weight, xline(3000) yline(20): s2color one solid
    # #C10534 segment, stcolor black and dashed.
    assert (s2["xyline_color"], s2["xyline_pattern"]) == ("#c10534", "solid")
    assert (st["xyline_color"], st["xyline_pattern"]) == ("#000000", "dash")
    # plot_region_border: white (not visible) under s2color and stcolor,
    # none under economist, black under s1mono.
    for name, drawn, colour in (("s2color", True, "#ffffff"),
                                ("stcolor", True, "#ffffff"),
                                ("economist", False, None),
                                ("s1mono", True, "#000000")):
        t = truth_for(name)
        assert (t["plotregion_line_drawn"], t["plotregion_line_color"]) == (
            drawn, colour), name
    # fonts.note: economist medlarge #FFFFFF in reverse_big's emidblue box.
    e = truth_for("economist")
    assert (e["note_textbox"]["name"], e["note_text_size"]["name"],
            e["note_text_color"], e["note_box_fill_color"]) == (
        "reverse_big", "medlarge", "#ffffff", "#7b92a8")
    assert truth_for("s1manual")["note_textbox"]["name"] == "key_label"
    assert s2["note_textbox"]["name"] == "small_body"


@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_a_shipped_file_carries_each_directive_once(name):
    """note()'s small_body box is `gsize small_body', which an earlier
    group already carries; the extractor writes it once."""
    seen, dup = set(), []
    with open(scheme_path(name), encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith(("*", "#include", "label")):
                continue
            key = tuple(line.split()[:2])
            if key in seen:
                dup.append(key)
            seen.add(key)
    assert not dup, (name, dup)


# --- WP-30 P1.2a: the chrome keys ------------------------------------------ #

#: The fixture keys the chrome group adds (extract_scheme_truth.chrome_truth).
_CHROME_KEYS = ("tick_angle_x", "tick_angle_y", "major_grid_pattern",
                "minor_grid_pattern", "tick_color", "minortick_color",
                "tick_line_width", "tick_length", "tick_position",
                "axis_styles", "alt_axes", "justification", "text_positions",
                "naturally_white", "p_bar_intensity", "p_area_intensity")


@pytest.mark.parametrize("name", SCHEME_NAMES)
def test_the_chrome_keys_are_resolved(name):
    t = truth_for(name)
    for k in _CHROME_KEYS:
        assert t.get(k) is not None, (name, k)
    assert len(t["p_bar_intensity"]) == 15 and len(t["p_area_intensity"]) == 15


def test_the_chrome_anchors():
    """twoway's measured chrome (03oct2026): s2color's vertical y labels and
    black outside ticks, stcolor's dashed grid, s1rcolor's white ticks,
    economist's right-hand y axis with no line or ticks and inside ticks."""
    s2 = truth_for("s2color")
    assert s2["tick_angle_y"]["degrees"] == 90.0
    assert s2["tick_position"] == "outside" and s2["tick_color"] == "#000000"
    assert s2["tick_length"]["name"] == "tiny"
    assert s2["text_positions"] == {"title": 12, "subtitle": 12, "note": 7,
                                    "caption": 7}
    assert truth_for("stcolor")["major_grid_pattern"]["name"] == "dash"
    assert truth_for("s1rcolor")["tick_color"] == "#ffffff"
    assert truth_for("s1rcolor")["naturally_white"] == 0
    e = truth_for("economist")
    assert e["tick_position"] == "inside"
    assert e["alt_axes"] == {"x": False, "y": True}
    assert (e["axis_styles"]["y"]["line"], e["axis_styles"]["y"]["ticks"]) \
        == (False, False)
    assert e["text_positions"]["note"] == 1
    assert e["justification"]["heading"] == "left"


def test_resolve_anglestyle_reads_the_style_file():
    mod = _extractor()
    r = mod.SchemeResolver(mod.DEFAULT_STATA_BASE)
    r.load("s2color")
    assert mod.resolve_anglestyle(r, "vertical") == {"name": "vertical",
                                                     "degrees": 90.0}
    assert mod.resolve_anglestyle(r, "45")["degrees"] == 45.0


_AXISSTYLES = [f"{d}_{k}" for d in ("horizontal", "vertical")
               for k in ("default", "nogrid", "withgrid", "noline", "notick",
                         "nolinetick")]


def test_axis_style_flags_for_every_axisstyle_file():
    mod = _extractor()
    r = mod.SchemeResolver(mod.DEFAULT_STATA_BASE)
    r.load("s2color")
    for name in _AXISSTYLES:
        f = mod.axis_style_flags(r, name)
        assert f["axisstyle"] == name
        kind = name.split("_", 1)[1]
        assert f["line"] == (kind not in ("noline", "nolinetick")), name
        assert f["ticks"] == (kind not in ("notick", "nolinetick")), name


def test_the_parser_axisstyle_table_is_statas():
    mod = _extractor()
    r = mod.SchemeResolver(mod.DEFAULT_STATA_BASE)
    r.load("s2color")
    want = {n: (mod.axis_style_flags(r, n)["line"],
                mod.axis_style_flags(r, n)["ticks"]) for n in _AXISSTYLES}
    assert SchemeParser._AXISSTYLE_FLAGS == want
