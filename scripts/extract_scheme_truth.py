#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract ground truth from Stata's own scheme and style files.

WHAT THIS IS
------------
Stata stores every graph scheme as a plain-text file
``<STATA>/ado/base/s/scheme-<name>.scheme``.  Schemes chain with ``#include``
and a child's later directives override whatever the parent set.  Named colours,
sizes, line widths and intensities are *themselves* indirections into
``<STATA>/ado/base/style/<class>-<name>.style``.

This script walks that whole graph and emits a single JSON document of fully
resolved values, which is the specification the translated ``dash`` scheme files
are written from -- and it then brings those twenty files
(``dash-<name>.scheme`` in the package root) up to date with it: every directive the fixture pins
is checked against the file, a value that disagrees is corrected on its own
line and reported, a directive the file lacks is appended in a dated block
after the file's last directive, and a file that does not exist is created
with the same writer.  The files' hand-written comments are left untouched,
the generated provenance block at the end of each file is rewritten only when
it differs, and a second run changes nothing.

DIRECTIVE VALUES ARE STATA'S THIRD TOKEN
----------------------------------------
Stata's own reader (``ado/base/s/scheme.class``, ``setscheme``) does
``tokenize`` then ``args style id stylename``: a directive's value is its THIRD
token, a double-quoted string is one token, and anything after the third token
is ignored.  ``scheme-sttrans.scheme`` writes ``symbolsize p small *medium``,
which Stata reads as ``small`` (measured 22sep2026: its marker radius in an SVG
export equals s2color's ``msize(small)``, 19.29, not medium's 26.35).  The
resolver tokenises the same way; joining every token after the key, as it once
did, would have shipped ``small *medium``.

OPACITY
-------
A colour token may carry Stata's ``%NN`` opacity suffix; sttrans writes every
p# colour as ``"r g b %20"`` and draws it at fill-opacity 0.20.  The fixture
keeps the hex in ``p_colors`` (what every consumer compares) and the percentage
beside it in ``p_colors_opacity`` (and the line/bar/mark/lineplot twins), and
the translated file writes the directive as ``#rrggbb%20``, which
``SchemeParser`` reads (``translate_mcolor`` strips the suffix) without
mistaking the colour for an opaque one.

PROVENANCE
----------
Every fixture entry carries ``provenance`` beside ``sources``: for each
extracted key (per index for the p# cycles) whether the value was TRANSCRIBED
-- a Stata scheme file in the #include chain writes the very key the
translation carries, and ``file``/``line`` say which directive -- or INFERRED --
no file writes that key, and the value is what Stata itself falls back to: the
documented ``p#stub -> pstub -> p# -> p`` chain, a bare class default, the
generic ``color grid``, or an axisstyle indirection; ``rule`` says which.  The
same is written into every shipped file as a block of ``* provenance:`` lines,
one per directive, between ``* BEGIN provenance (WP-17)`` and ``* END
provenance (WP-17)``, so the distinction survives into what is shipped.

GRID SWITCHES ARE RECORDED AS *EFFECTIVE* PER-AXIS VALUES
---------------------------------------------------------
twoway builds its x axis with ``axisstyle horizontal_default`` and its y axis
with ``axisstyle vertical_default``.  The scheme maps each of those roles to a
style name, and ``style/axisstyle-<name>.style`` then names the ``yesno`` key
that is actually read (``set draw_major_grid scheme draw_major_hgrid``).  For
nineteen schemes the roles map to themselves, so the keys are
``draw_major_hgrid``/``draw_minor_hgrid`` (x) and ``draw_major_vgrid``/
``draw_minor_vgrid`` (y); economist maps ``vertical_default`` to
``vertical_nolinetick``, whose style file reads ``draw_major_nlt_vgrid`` and
``draw_minor_nlt_vgrid`` instead.  The fixture keys ``draw_major_hgrid``,
``draw_minor_hgrid``, ``draw_major_vgrid`` and ``draw_minor_vgrid`` therefore
hold the value Stata ends up with for that axis, whichever key supplied it, and
``grid_axes`` records the chain.  No style file reads the bare
``draw_major_grid``/``draw_minor_grid``; they are recorded only as transcribed.

UNITS
-----
help size: "relative size, where size 100 = minimum of width and height of
graph".  Every official gsize-/symbolsize-*.style sets ``sztype relative`` and
linewidth's numeric form is the same unit.  On Stata's 4-inch reference (s2color
is 5.5 x 4in) one unit is 2.88pt, and every sized value in the fixture carries
its ``pt_at_4in``; ``_meta.units`` holds the three keyword ladders read from the
style files.

SOURCE OF TRUTH (measured on this machine, 2026-09-18)
------------------------------------------------------
Stata version : StataNow 19.5 (MP), born 12 Aug 2026
Scheme files  : /Applications/StataNow/ado/base/s/scheme-<name>.scheme
Style files   : /Applications/StataNow/ado/base/style/<class>-<name>.style

The older /Applications/Stata/ado/base tree was byte-compared against the
StataNow tree: every scheme-*.scheme file and every style file present in both
is identical, so either tree yields the same answer.  Override the location with
``--stata-base`` if you are on a different install.

USAGE
-----
    /opt/homebrew/bin/python3.14 scripts/extract_scheme_truth.py \
        --out test/fixtures/scheme_truth.json          # also updates dash-*.scheme
    ... --no-scheme-files                             # fixture only
    ... --schemes-dir /elsewhere                      # files live elsewhere

COLOUR INTENSITY MULTIPLIERS (``navy*0.5``)
-------------------------------------------
[G-4] colorstyle documents ``color*#``: # of 1 leaves the colour unchanged,
# < 1 makes it lighter, # > 1 makes it darker, ``*0`` is "as light as possible"
and ``*255`` "as dark as possible".  The manual does not give the arithmetic, so
the arithmetic below was determined *empirically* by asking Stata itself: 24
colour/multiplier combinations were rendered with ``twoway scatter,
mcolor(<spec>)``, exported with ``graph export ... .svg`` (SVG carries literal
``#rrggbb``), and the emitted hex read back.  Every one of the 72 channel values
matches, exactly, this rule:

    f <= 1 :  c' = round(255 - (255 - c) * f)      # blend towards white
    f  > 1 :  c' = round(c / f)                    # scale towards black

with round-half-away-from-zero and clamping to [0, 255].  See
``_apply_intensity`` below.
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

DEFAULT_STATA_BASE = "/Applications/StataNow/ado/base"
STATA_VERSION = "StataNow 19.5 (MP), born 12 Aug 2026"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SCHEMES_DIR = REPO_ROOT

# Number of overlaid plots in a Stata scheme's colour cycle.
N_PLOTS = 15

# Hard stop on pathological #include chains (Stata's own deepest chain is 4).
MAX_INCLUDE_DEPTH = 32


# --------------------------------------------------------------------------- #
# Scheme file parsing
# --------------------------------------------------------------------------- #

class SchemeResolver:
    """Parses a scheme file, following #include, applying last-write-wins.

    Stata's scheme grammar, as used by the base schemes, is one directive per
    line::

        <class> <key> <value...>      e.g.  color p1   stc1
        <class> <value>               e.g.  intensity  full   (class default)

    Lines beginning with ``*`` are comments (``*!`` is the version stamp).
    ``#include <scheme>`` splices another scheme in at that point, so directives
    appearing *after* the include in the child override the parent.

    The value is the THIRD token, exactly as Stata's ``setscheme`` reads it
    (``tokenize`` + ``args style id stylename``): a double-quoted string is one
    token and anything after the value is ignored.  ``sequence`` and ``label``
    lines are skipped as Stata skips them (the label is kept aside).
    """

    def __init__(self, stata_base: str):
        self.stata_base = stata_base
        self.scheme_dir = os.path.join(stata_base, "s")
        self.style_dir = os.path.join(stata_base, "style")
        # (class, key) -> value.  key "" is the class-level default.
        self.settings: dict[tuple[str, str], str] = {}
        # (class, key) -> (scheme name, 1-based line) of the directive that
        # LAST wrote it, i.e. the one whose value stands.
        self.origins: dict[tuple[str, str], tuple[str, int]] = {}
        # Stata's `label "..."' line of the child scheme (the first seen).
        self.label: str | None = None
        # Scheme names in the order their files were OPENED: the child first,
        # then each #include as it is met (child -> ... -> root).
        self.include_chain: list[str] = []
        self._style_cache: dict[str, dict[str, str]] = {}

    # -- public ------------------------------------------------------------ #

    def load(self, scheme_name: str) -> None:
        self._load(scheme_name, stack=[], depth=0)

    def get(self, cls: str, key: str, class_default: bool = True):
        """Look up ``<class> <key>``; fall back to the class default if asked."""
        val = self.settings.get((cls, key))
        if val is not None:
            return val
        if class_default:
            return self.settings.get((cls, ""))
        return None

    def first(self, cls: str, keys: list[str], class_default: bool = False):
        """First hit walking ``keys`` in order; Stata's stub fallback chain."""
        for k in keys:
            val = self.get(cls, k, class_default=False)
            if val is not None:
                return val
        if class_default:
            return self.settings.get((cls, ""))
        return None

    # -- include walking --------------------------------------------------- #

    def _load(self, scheme_name: str, stack: list[str], depth: int) -> None:
        if depth > MAX_INCLUDE_DEPTH:
            raise RuntimeError(
                f"#include nesting deeper than {MAX_INCLUDE_DEPTH}: {stack}"
            )
        if scheme_name in stack:
            # Cycle guard: a scheme already open further up the chain.  Stata
            # would loop forever here; we stop and carry on with what we have.
            sys.stderr.write(
                f"warning: #include cycle ignored: {' -> '.join(stack)}"
                f" -> {scheme_name}\n"
            )
            return

        path = os.path.join(self.scheme_dir, f"scheme-{scheme_name}.scheme")
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        stack = stack + [scheme_name]
        self.include_chain.append(scheme_name)

        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for lineno, raw in enumerate(fh, 1):
                line = raw.strip()
                if not line or line.startswith("*") or line.startswith("//"):
                    continue
                if line.startswith("#include"):
                    parts = line.split()
                    if len(parts) >= 2:
                        # Parent is applied HERE, so anything below this line in
                        # the child file overwrites it.  Last write wins.
                        self._load(parts[1], stack, depth + 1)
                    continue
                # Stata's tokenize: a double-quoted string is one token.  A
                # value such as "navy*0.5" is a single token either way.
                tokens = _TOKEN.findall(line)
                if len(tokens) < 2:
                    continue
                cls = tokens[0]
                if cls in ("sequence", "label"):
                    # setscheme skips both; the child's own label (depth 0,
                    # not a parent's, which is read first because #include
                    # precedes the label line) is worth keeping.
                    if cls == "label" and depth == 0:
                        self.label = tokens[1].strip('"')
                    continue
                if len(tokens) == 2:
                    # Class-level default, e.g. "intensity full" (Stata
                    # stores it as the class's `_default').
                    key, value = "", tokens[1]
                else:
                    # The third token is the value; Stata ignores the rest
                    # (scheme-sttrans.scheme: `symbolsize p small *medium').
                    key, value = tokens[1], tokens[2]
                self.settings[(cls, key)] = value
                self.origins[(cls, key)] = (scheme_name, lineno)

    # -- style file lookup ------------------------------------------------- #

    def style(self, cls: str, name: str) -> dict[str, str] | None:
        """Read ``style/<cls>-<name>.style`` and return its ``set`` settings."""
        key = f"{cls}-{name}"
        if key in self._style_cache:
            return self._style_cache[key] or None
        path = os.path.join(self.style_dir, f"{key}.style")
        if not os.path.exists(path):
            self._style_cache[key] = {}
            return None
        out: dict[str, str] = {}
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                line = raw.strip()
                if not line.startswith("set "):
                    continue
                rest = line[4:].strip()
                bits = rest.split(None, 1)
                if len(bits) == 2:
                    out[bits[0]] = bits[1].strip().strip('"')
        self._style_cache[key] = out
        return out


# --------------------------------------------------------------------------- #
# Colour resolution
# --------------------------------------------------------------------------- #

_RGB_LITERAL = re.compile(r"^\d+\s+\d+\s+\d+$")

# Stata's tokenize, as far as scheme files need it: a double-quoted string is
# one token, otherwise whitespace separates tokens.
_TOKEN = re.compile(r'"[^"]*"|\S+')


def _round_half_up(x: float) -> int:
    return int(Decimal(repr(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _apply_intensity(rgb: tuple[int, int, int], f: float,
                     naturally_white: bool = True) -> tuple[int, int, int]:
    """Stata's ``colorstyle*#`` intensity, as twoway draws it (WP-30
    P1.13a; plan section 30 Evidence E3, StataNow 19.5 SVG export).

    Each channel, rounded half up: under ``naturally_white 1`` f <= 1
    gives ``255 - (255 - c) * f`` and f > 1 ``c / f``; under
    ``naturally_white 0`` ``c * f``, held to 255.  Then Stata's clamp: when
    a channel that was non-zero came out 0, every channel is ``c / m``, m
    the smallest non-zero channel.  The same rule as dash_render's
    ``GlyphMapper._blend_intensity`` (the extractor stays standalone);
    navy*52 (twoway #010304, this rule #010102) is UNCLEAR.
    """
    f = max(0.0, float(f))
    if not naturally_white:
        raw = [c * f for c in rgb]
    elif f <= 1.0:
        raw = [255.0 - (255.0 - c) * f for c in rgb]
    else:
        raw = [c / f for c in rgb]
    out = [max(0, min(255, _round_half_up(v))) for v in raw]
    if any(c > 0 and o == 0 for c, o in zip(rgb, out)):
        m = min(c for c in rgb if c > 0)
        out = [max(0, min(255, _round_half_up(c / m))) for c in rgb]
    return tuple(out)  # type: ignore[return-value]


_NUMBER = re.compile(r"[-+]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eEdD][-+]?[0-9]+)?")
_HEX6 = re.compile(r"#[0-9A-Fa-f]{6}")
_STYLE_NAME = re.compile(r"[a-z0-9_]+")


def _number(text: str):
    """Stata's spelling of a finite number, or None (64 characters at most)."""
    t = text.strip()
    if not t or len(t) > 64 or not _NUMBER.fullmatch(t):
        return None
    v = float(t.replace("d", "e").replace("D", "e"))
    return v if v == v and abs(v) != float("inf") else None


def _cmyk_hex(nums):
    """RGB of CMYK *nums* (proportions when all lie in [0, 1], else whole
    numbers 0-255), each channel ``max(0, 255 - (C + K))``; None out of
    range.  A private copy of dash_render's ``OptionTranslator._colour_cmyk``."""
    if len(nums) != 4:
        return None
    if all(0.0 <= x <= 1.0 for x in nums):
        v = [int(math.floor(x * 255 + 1e-9)) for x in nums]
    elif all(x == int(x) and 0 <= x <= 255 for x in nums):
        v = [int(x) for x in nums]
    else:
        return None
    c, m, y, k = v
    return tuple(max(0, 255 - (q + k)) for q in (c, m, y))


def _hsv_hex(h, s, v):
    """RGB of HSV (hue mod 360, S and V in [0, 1], ``floor(x*255)``); None
    out of range.  A private copy of ``OptionTranslator._colour_hsv``."""
    if not (0.0 <= s <= 1.0 and 0.0 <= v <= 1.0):
        return None
    h = h % 360.0
    k = int(h / 60.0) % 6
    f = h / 60.0 - int(h / 60.0)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    rgb = ((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v),
           (v, p, q))[k]
    return tuple(int(math.floor(x * 255 + 1e-9)) for x in rgb)


def _colour_parts(text: str):
    """(base, multiplier, opacity) text, ``*`` and ``%`` in either order."""
    cut = [k for k in (text.find("*"), text.find("%")) if k >= 0]
    if not cut:
        return text.strip(), None, None
    i = min(cut)
    base, rest = text[:i].strip(), text[i:]
    other = "%" if rest[0] == "*" else "*"
    j = rest.find(other, 1)
    one = rest[1:j] if j >= 0 else rest[1:]
    two = rest[j + 1:] if j >= 0 else None
    return (base, one, two) if rest[0] == "*" else (base, two, one)


class ColorResolver:
    """Turns a scheme colour token into ``#rrggbb`` (or None for ``none``)."""

    def __init__(self, resolver: SchemeResolver):
        self.r = resolver
        self.unresolved: list[str] = []

    def resolve(self, token: str | None, _depth: int = 0) -> str | None:
        """``#rrggbb`` for *token*; an opacity suffix is REPORTED, not kept.

        For a scalar colour key the fixture has nowhere to put an opacity, so
        one is flagged in ``unresolved`` rather than dropped in silence.  The
        p# cycles go through :meth:`resolve_with_opacity` instead.
        """
        hexval, opacity = self.resolve_with_opacity(token, _depth)
        if opacity is not None:
            self.unresolved.append(
                f"opacity suffix %{opacity:g} on colour token {token!r} not "
                f"folded into hex"
            )
        return hexval

    def resolve_with_opacity(
        self, token: str | None, _depth: int = 0,
    ) -> "tuple[str | None, float | None]":
        """``(#rrggbb, opacity percent or None)`` for *token*."""
        if token is None:
            return None, None
        tok = token.strip().strip('"').strip()
        if not tok or _depth > 8:
            return None, None

        # Stata's colour grammar (WP-30 P1.13a, plan section 30 E3): *# and
        # %# in either order; malformed and unknown tokens are REPORTED in
        # `unresolved' and give (None, None) -- the extractor reports, it
        # does not guess (Stata's shipped files contain neither).
        base, m, op = _colour_parts(tok)
        mult = opacity = None
        if m is not None and m.strip():
            mult = _number(m)
            if mult is None or mult < 0:
                self.unresolved.append(
                    f"unparseable intensity multiplier in colour token {token!r}")
                return None, None
        if op is not None and op.strip():
            opacity = _number(op)
            if opacity is None or not 0 <= opacity <= 100:
                self.unresolved.append(
                    f"unparseable opacity suffix in colour token {token!r}")
                return None, None

        if base == "none":
            # color-none.style carries "0 0 0" but its own comment says the
            # values should not matter: 'none' means "do not draw".
            return None, None

        rgb = None
        nums = None
        if base in ("background", "bg", "foreground", "fg"):
            # A named-style lookup of the scheme's own text: a style name
            # (exact lower case) or a hex code resolves; RGB, HSV, CMYK,
            # *# or %# text does not (twoway: black with a note).
            key = "background" if base[0] == "b" else "foreground"
            raw = (self.r.get("color", key) or "").strip().strip('"').strip()
            if _STYLE_NAME.fullmatch(raw) or _HEX6.fullmatch(raw):
                h, inner = self.resolve_with_opacity(raw, _depth + 1)
                if h is not None:
                    rgb = tuple(int(h[k:k + 2], 16) for k in (1, 3, 5))
                    if opacity is None:
                        opacity = inner
        elif base.startswith("#"):
            if _HEX6.fullmatch(base):
                rgb = tuple(int(base[k:k + 2], 16) for k in (1, 3, 5))
        elif "," in base:
            nums = [_number(x) for x in base.split(",")]
        elif base.split() and base.split()[0].lower() == "hsv":
            hv = [_number(x) for x in base.split()[1:]]
            if len(hv) == 3 and all(x is not None for x in hv):
                rgb = _hsv_hex(*hv)
        elif len(base.split()) in (3, 4):
            nums = [_number(x) for x in base.split()]
        elif _STYLE_NAME.fullmatch(base):
            # Names are case-sensitive: Stata's 92 color-*.style files are
            # all lower case, and a case-folding file system would find
            # color-navy.style for Navy (twoway: not found).
            st = self.r.style("color", base)
            if st and "rgb" in st:
                parts = st["rgb"].split()
                if len(parts) == 3:
                    rgb = (int(parts[0]), int(parts[1]), int(parts[2]))
        if nums is not None and all(x is not None for x in nums):
            if len(nums) == 3 and all(x == int(x) and 0 <= x <= 255
                                      for x in nums):
                rgb = tuple(int(x) for x in nums)
            elif len(nums) == 4:
                rgb = _cmyk_hex(nums)

        if rgb is None:
            self.unresolved.append(f"unknown colour token {token!r}")
            return None, None

        if mult is not None:
            nw = self.r.get("system", "naturally_white")
            rgb = _apply_intensity(
                rgb, mult, naturally_white=str(nw).strip() != "0")

        return "#%02x%02x%02x" % tuple(rgb), opacity


# --------------------------------------------------------------------------- #
# Scalar (size / width / intensity) resolution
# --------------------------------------------------------------------------- #

def _as_number(text: str):
    try:
        if re.fullmatch(r"[+-]?\d+", text):
            return int(text)
        return float(text)
    except (TypeError, ValueError):
        return None


# Stata's relative size: 100 = the graph's smaller dimension (help size).  The
# reference graph is s2color's 5.5 x 4 inches, so one unit is 4in/100 * 72pt.
REFERENCE_MIN_DIMENSION_IN = 4.0
PT_PER_UNIT_AT_REFERENCE = REFERENCE_MIN_DIMENSION_IN / 100.0 * 72.0   # 2.88

# The keyword ladders, in Stata's own order.  gsize has no `ehuge' style file
# (only symbolsize does); the fractional gsize names are real styles too.
GSIZE_KEYWORDS = (
    "zero", "minuscule", "quarter_tiny", "third_tiny", "half_tiny", "tiny",
    "vsmall", "small", "medsmall", "medium", "medlarge", "large", "vlarge",
    "huge", "vhuge", "default", "tenth", "quarter", "third", "half", "full",
)
SYMBOLSIZE_KEYWORDS = (
    "zero", "vtiny", "tiny", "vsmall", "small", "medsmall", "medium",
    "medlarge", "large", "vlarge", "huge", "vhuge", "ehuge",
)
LINEWIDTH_KEYWORDS = (
    "none", "vvvthin", "vvthin", "vthin", "thin", "medthin", "medium",
    "medthick", "thick", "vthick", "vvthick", "vvvthick",
)


def pt_at_reference(value, ndigits: int = 2):
    """Points at Stata's 4-inch reference for a relative-size *value*."""
    if value is None:
        return None
    return round(float(value) * PT_PER_UNIT_AT_REFERENCE, ndigits)


def resolve_sized(r: SchemeResolver, cls: str, token: str | None):
    """Resolve a gsize/symbolsize token to {name, value, sztype, pt_at_4in}.

    A token is either a literal number (a relative size) or a style name such as
    ``medsmall`` that indirects into ``style/<cls>-<name>.style`` which carries
    ``set val`` and ``set sztype``.  ``pt_at_4in`` is the size in points on
    Stata's 4-inch reference graph; None when the style is not relative.
    """
    if token is None:
        return None
    tok = token.strip().strip('"')
    lit = _as_number(tok)
    if lit is not None:
        return {"name": tok, "value": float(lit), "sztype": "relative",
                "pt_at_4in": pt_at_reference(lit)}
    st = r.style(cls, tok.lower())
    if not st or "val" not in st:
        return {"name": tok, "value": None, "sztype": None, "pt_at_4in": None}
    val = _as_number(st["val"])
    sztype = st.get("sztype")
    return {
        "name": tok,
        "value": float(val) if val is not None else None,
        "sztype": sztype,
        "pt_at_4in": pt_at_reference(val) if sztype == "relative" else None,
    }


#: WP-30 P1.20b: the gsize keys of Stata's margin ladder
#: (scheme-s2color.scheme:195-205), which style/margin-*.style name.
MARGIN_LADDER = ("sidemargin", "medmargin", "medsmmargin", "medlgmargin",
                 "largemargin", "vlargemargin", "smallmargin",
                 "vsmallmargin", "tinymargin", "emargin", "esubmargin")


def resolve_margin_rs(r: SchemeResolver, token: str | None):
    """WP-30 P1.3a (D-21a): a marginstyle name -> its one relative size.

    ``style/margin-<name>.style`` sets gleft/gright/gtop/gbottom to
    ``scheme <gsize key>`` (or a literal); each resolves through the
    scheme's ``gsize`` keys to ``relativeNpM`` (N.M).  All four sides must
    be equal -- twoway's plot-region margin is the same on every side in
    every shipped scheme -- else this raises."""
    if token is None:
        return None
    st = r.style("margin", token.strip().strip('"').lower())
    if not st:
        return None
    vals = []
    for side in ("gleft", "gright", "gtop", "gbottom"):
        raw = (st.get(side) or "").strip()
        if raw.startswith("scheme "):
            raw = (r.get("gsize", raw[len("scheme "):].strip(),
                         class_default=False) or "").strip()
        m = re.fullmatch(r"relative(\d+)(?:p(\d+))?", raw)
        if m:
            v = float(m.group(1) + ("." + m.group(2) if m.group(2) else ""))
        else:
            v = _as_number(raw)
        vals.append(None if v is None else float(v))
    if any(v is None for v in vals) or len(set(vals)) != 1:
        raise ValueError(f"margin {token}: sides differ or do not resolve: "
                         f"{vals}")
    return vals[0]


def resolve_linewidth(r: SchemeResolver, token: str | None):
    """Resolve a linewidth token to {name, value, pt_at_4in} (same unit)."""
    if token is None:
        return None
    tok = token.strip().strip('"')
    lit = _as_number(tok)
    if lit is not None:
        return {"name": tok, "value": float(lit),
                "pt_at_4in": pt_at_reference(lit, 3)}
    st = r.style("linewidth", tok.lower())
    if not st or "val" not in st:
        return {"name": tok, "value": None, "pt_at_4in": None}
    val = _as_number(st["val"])
    return {"name": tok, "value": float(val) if val is not None else None,
            "pt_at_4in": pt_at_reference(val, 3)}


def unit_ladders(r: SchemeResolver) -> dict:
    """The gsize / symbolsize / linewidth keyword ladders, read from style/.

    Each entry is ``{"value": <set val>, "pt_at_4in": ...}`` (plus ``sztype``
    for the sized classes); a keyword with no style file is recorded as None
    rather than invented.
    """
    def ladder(cls, names, ndigits):
        out = {}
        for name in names:
            st = r.style(cls, name)
            if not st or "val" not in st:
                out[name] = None
                continue
            val = _as_number(st["val"])
            entry = {"value": float(val) if val is not None else None}
            if cls != "linewidth":
                entry["sztype"] = st.get("sztype")
            relative = st.get("sztype", "relative") == "relative"
            entry["pt_at_4in"] = (
                pt_at_reference(val, ndigits) if relative and val is not None
                else None)
            out[name] = entry
        return out
    return {
        "gsize": ladder("gsize", GSIZE_KEYWORDS, 2),
        "symbolsize": ladder("symbolsize", SYMBOLSIZE_KEYWORDS, 2),
        "linewidth": ladder("linewidth", LINEWIDTH_KEYWORDS, 3),
    }


# --------------------------------------------------------------------------- #
# Grid switches: the axisstyle indirection
# --------------------------------------------------------------------------- #

# twoway builds its x axis with `axisstyle horizontal_default' and its y axis
# with `axisstyle vertical_default' (t/twowaygraph_g.class:870,914 and
# x/xygraph_g.class:149,212).  The scheme maps each role to a style name, and
# style/axisstyle-<name>.style then names the `yesno' key that is read --
# `set draw_major_grid scheme draw_major_hgrid' -- or gives a literal yes/no.
AXIS_ROLES = {"x": "horizontal_default", "y": "vertical_default"}
# A second axis (yaxis(2), xaxis(2)) is built with the _nogrid roles
# (t/twowaygraph_g.class adds axis 2 in the nogrid style): economist's
# measured y2 has a line and ticks (WP-30 P1.2a, E8), which `vertical_nogrid'
# gives and `vertical_default' (no line under economist) would not.
AXIS2_ROLES = {"x": "horizontal_nogrid", "y": "vertical_nogrid"}


def axis_grid_switches(r: SchemeResolver, axis: str) -> dict:
    """Which scheme key (or literal) each grid switch of *axis* comes from."""
    role = AXIS_ROLES[axis]
    tok = r.get("axisstyle", role, class_default=False)
    name = (tok if tok is not None else role).strip().strip('"')
    st = r.style("axisstyle", name.lower()) or {}
    info = {
        "role": role,
        "axisstyle": name,
        "axisstyle_declared": tok is not None,
        "style_file": f"style/axisstyle-{name.lower()}.style",
    }
    for which in ("major", "minor"):
        setting = st.get(f"draw_{which}_grid")
        parts = setting.split() if setting else []
        if len(parts) == 2 and parts[0] == "scheme":
            info[f"{which}_key"] = parts[1]
            info[f"{which}_literal"] = None
        else:
            info[f"{which}_key"] = None
            info[f"{which}_literal"] = parts[0] if parts else None
    return info


def resolve_intensity(r: SchemeResolver, token: str | None):
    """intensity token -> {name, pct, alpha}.  ``inten80`` -> 80 -> 0.80."""
    if token is None:
        return None
    tok = token.strip().strip('"')
    lit = _as_number(tok)
    if lit is not None:
        pct = float(lit)
    else:
        st = r.style("intensity", tok.lower())
        if not st or "val" not in st:
            return {"name": tok, "pct": None, "alpha": None}
        v = _as_number(st["val"])
        if v is None:
            return {"name": tok, "pct": None, "alpha": None}
        pct = float(v)
    return {"name": tok, "pct": pct, "alpha": round(pct / 100.0, 4)}


def resolve_linepattern(r: SchemeResolver, token: str | None):
    if token is None:
        return None
    tok = token.strip().strip('"')
    st = r.style("linepattern", tok.lower())
    dash = None
    if st and "pattern" in st:
        dash = [float(x) for x in st["pattern"].split()]
    return {"name": tok, "dash": dash}


def resolve_anglestyle(r: SchemeResolver, token: str | None):
    """anglestyle token -> {name, degrees}.

    A name is read from ``style/anglestyle-<name>.style``'s ``set val``
    (anglestyle-vertical.style: ``set val 90``); a bare number is degrees.
    """
    if token is None:
        return None
    tok = token.strip().strip('"')
    lit = _as_number(tok)
    if lit is not None:
        return {"name": tok, "degrees": float(lit)}
    st = r.style("anglestyle", tok.lower()) or {}
    v = _as_number(st.get("val", ""))
    return {"name": tok, "degrees": float(v) if v is not None else None}


def axis_style_flags(r: SchemeResolver, role_key: str) -> dict:
    """Whether the axisstyle *role_key* resolves to draws its line and ticks.

    ``axisstyle <role_key>`` names a style; ``style/axisstyle-<name>.style``
    gives ``set linestyle`` (``none``: no line) and ``set majorstyle scheme
    <tickset>``.  ``ticksetstyle <tickset>`` names
    ``style/ticksetstyle-<name>.style``, whose ``set tickstyle scheme <ts>``
    goes through ``tickstyle <ts>`` to ``style/tickstyle-<name>.style``'s
    ``set show_ticks`` (axisstyle-vertical_nolinetick.style ->
    ticksetstyle-major_vert_notickbig.style -> tickstyle-major_notickbig
    .style: ``show_ticks no``).
    """
    tok = r.get("axisstyle", role_key, class_default=False)
    name = (tok if tok is not None else role_key).strip().strip('"')
    st = r.style("axisstyle", name.lower()) or {}
    line = (st.get("linestyle") or "").strip().lower() != "none"
    ticks = True
    major = (st.get("majorstyle") or "").split()
    if len(major) == 2 and major[0] == "scheme":
        tset = r.get("ticksetstyle", major[1], class_default=False)
        tset = (tset if tset is not None else major[1]).strip().strip('"')
        tst = r.style("ticksetstyle", tset.lower()) or {}
        tsref = (tst.get("tickstyle") or "").split()
        if len(tsref) == 2 and tsref[0] == "scheme":
            ts = r.get("tickstyle", tsref[1], class_default=False)
            ts = (ts if ts is not None else tsref[1]).strip().strip('"')
            tick = r.style("tickstyle", ts.lower()) or {}
            ticks = (tick.get("show_ticks") or "yes").strip().lower() != "no"
    return {"role": role_key, "axisstyle": name, "declared": tok is not None,
            "line": line, "ticks": ticks,
            "style_file": f"style/axisstyle-{name.lower()}.style"}


# --------------------------------------------------------------------------- #
# Per-scheme extraction
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# Named styles (WP-30 P1.14b, section 36): the style table and the keys it
# reads along scheme.class's chain
# --------------------------------------------------------------------------- #

#: The option classes and the attrs of each style file S36 transcribes; a
#: value is the class the attr's name is read in (a style class: a hop) or
#: the scheme class its key is read in (a leaf).  label, dots, connect,
#: align, angle, back* and fill are not transcribed (D-36f).
NAMED_STYLE_CLASSES = {
    "seriesstyle": {"marker": "markerstyle", "line": "linestyle",
                    "area": "areastyle"},
    "markerstyle": {"symbol": "symbol", "size": "symbolsize",
                    "fillcolor": "color", "linestyle": "linestyle"},
    "areastyle": {"linestyle": "linestyle", "shadestyle": "shadestyle"},
    "shadestyle": {"color": "color", "intensity": "intensity"},
    "linestyle": {"width": "linewidth", "color": "color",
                  "pattern": "linepattern"},
}
#: The curated names per class (StataNow 19.5 style files, plan E7);
#: linestyle is every file but S32's p#.  shadestyle is the hops the
#: curated areastyles reach.
NAMED_STYLE_CURATED = {
    "seriesstyle": ("ci", "ci2", "histogram", "p#line", "p#bar", "p#area",
                    "p#box", "p#dot", "p#arrow"),
    "markerstyle": ("ci", "ci2", "histogram", "none", "p#box", "p#dot",
                    "p#arrow"),
    "areastyle": ("background", "ci", "ci2", "foreground", "histogram",
                  "none", "p#area", "p#bar", "p#box"),
    "shadestyle": ("background", "ci", "ci2", "foreground", "histogram",
                   "none", "p#area", "p#bar", "p#box"),
    "linestyle": None,
}
_STYLE_LEAVES = frozenset({"color", "linewidth", "linepattern", "symbol",
                           "symbolsize", "intensity"})


def _style_files(r: SchemeResolver, cls: str) -> list:
    """The file names of style/<cls>-*.style, sorted."""
    pre = cls + "-"
    return sorted(f[len(pre):-len(".style")] for f in os.listdir(r.style_dir)
                  if f.startswith(pre) and f.endswith(".style"))


def style_table(r: SchemeResolver) -> dict:
    """``{class: {file: [[attr, "scheme"|"literal", value], ...]}}`` for the
    names S36 resolves, transcribed from the style files."""
    out: dict = {}
    for cls, attrs in NAMED_STYLE_CLASSES.items():
        names = NAMED_STYLE_CURATED[cls]
        if names is None:
            names = [n for n in _style_files(r, cls) if n != "p#"]
        out[cls] = {}
        for n in names:
            path = os.path.join(r.style_dir, f"{cls}-{n}.style")
            rows = []
            with open(path, encoding="utf-8", errors="replace") as fh:
                for raw in fh:
                    bits = raw.split()
                    if len(bits) < 3 or bits[0] != "set" or bits[1] not in attrs:
                        continue
                    if bits[2] == "scheme":
                        rows.append([bits[1], "scheme",
                                     bits[3] if len(bits) > 3 else ""])
                    else:
                        rows.append([bits[1], "literal", bits[2]])
            out[cls][n] = rows
    return out


def style_known(r: SchemeResolver) -> dict:
    """``{class: sorted file names}`` for the four option classes."""
    return {cls: _style_files(r, cls) for cls in
            ("seriesstyle", "markerstyle", "areastyle", "linestyle")}


def _scheme_chain(key: str) -> list:
    """scheme.class's lookup steps for *key* (E8): a key starting ``p`` walks
    p<num><stub>, p<stub>, p<num>, p, then the key itself; any other key is
    exact."""
    if not key.startswith("p"):
        return [key]
    m = re.match(r"p(\d*)(.*)", key)
    num, stub = m.group(1), m.group(2)
    out = []
    for s in (f"p{num}{stub}", f"p{stub}", f"p{num}", "p", key):
        if s not in out:
            out.append(s)
    return out


def _style_file_of(name: str) -> "tuple[str, str]":
    """``(file name, number)`` of a style name: ``p3bar`` -> ``("p#bar",
    "3")``; a plain name is itself with no number."""
    m = re.fullmatch(r"p([1-9]|1[0-5])([a-z_]*)", name)
    if m:
        return "p#" + m.group(2), m.group(1)
    return name, ""


def named_style_directives(r: SchemeResolver, provenance: dict,
                           sources: dict) -> "tuple[dict, dict, list]":
    """The leaf keys the scheme DECLARES along each table name's chain,
    ``{"<class> <key>": value}``, the hops it declares, and the keys no step
    resolves.

    A scheme.class-faithful walk (E8), not ``linked()``'s class default: a
    leaf key walks the p#stub chain (or is exact) and a key no step declares
    is unresolvable; a hop (a style-name attr) takes the declared value of
    the first step that has one, else the first step that names a style of
    its class (D-36h).  A colour is spelled ``#rrggbb[%NN]``, Stata's ``none``
    as ``none``; any other value is Stata's own token.
    """
    c = ColorResolver(r)
    table = style_table(r)
    found: dict = {}
    hops: dict = {}
    bad: list = []
    known = {cls: set(_style_files(r, cls)) for cls in
             ("seriesstyle", "markerstyle", "areastyle", "linestyle",
              "shadestyle")}

    def names_style(hcls, step):
        f, _n = _style_file_of(step)
        return f in known[hcls]

    def walk(cls, name, depth=0):
        if depth > 6 or name == "none":
            return
        file, num = _style_file_of(name)
        if file == "p#" or file not in table.get(cls, {}):
            return
        for attr, kind, val in table[cls][file]:
            sub = NAMED_STYLE_CLASSES[cls][attr]
            if kind == "literal":
                if sub not in _STYLE_LEAVES:
                    walk(sub, val, depth + 1)
                continue
            key = val.replace("#", num)
            if sub in _STYLE_LEAVES:
                hit = None
                for step in _scheme_chain(key):
                    if (sub, step) in r.settings:
                        hit = step
                        break
                if hit is None and key == "" and (sub, "") in r.settings:
                    hit = ""
                if hit is None:
                    msg = (f"named style {cls} {name}: {sub} {key} is not "
                           "declared at any step of scheme.class's chain")
                    if msg not in bad:
                        bad.append(msg)
                    continue
                found[(sub, hit)] = r.settings[(sub, hit)]
                continue
            target = None
            for step in _scheme_chain(key):
                if (sub, step) in r.settings:
                    target = r.settings[(sub, step)].strip().strip('"')
                    hops[f"{sub} {step}"] = target
                    break
                if names_style(sub, step):
                    target = step
                    break
            if target is not None:
                walk(sub, target, depth + 1)

    for cls in ("seriesstyle", "markerstyle", "areastyle", "linestyle"):
        for file in table[cls]:
            nums = range(1, N_PLOTS + 1) if "#" in file else [None]
            for n in nums:
                walk(cls, file.replace("#", str(n)) if n else file)

    out: dict = {}
    for (cls, key) in sorted(found):
        tok = found[(cls, key)].strip().strip('"').strip()
        if cls == "color":
            if tok.split("%")[0].split("*")[0].strip() == "none":
                val = "none"
            else:
                hexval, pct = c.resolve_with_opacity(tok)
                val = _color_token(hexval, pct)
                if val is None:
                    bad.append(f"color {key}: {tok!r} is not a colour")
                    continue
        else:
            val = tok
        k = f"{cls} {key}" if key else cls
        out[k] = val
        o = r.origins.get((cls, key))
        sources[f"named_style_directives.{k}"] = k
        provenance[f"named_style_directives.{k}"] = {
            "kind": "transcribed", "directive": k, "value": tok,
            "file": f"scheme-{o[0]}.scheme" if o else None,
            "line": o[1] if o else None}
    return out, hops, bad


def extract(stata_base: str, scheme: str) -> dict:
    r = SchemeResolver(stata_base)
    r.load(scheme)
    c = ColorResolver(r)
    unresolvable: list[str] = []
    # Provenance, two ways.  ``sources``: output key -> the "<class> <key>"
    # directive that actually supplied the value, or "<class> <class-default>"
    # when the value came from a bare two-token class default line rather
    # than a named key.  ``provenance``: the same keys -> a record saying
    # whether the translation's directive was TRANSCRIBED (a Stata file in
    # the chain writes that very key; file:line names the directive) or
    # INFERRED (no file writes it; the value is Stata's own fallback, and
    # ``rule`` says which one).  The p# cycles hold one entry per index.
    sources: dict[str, object] = {}
    provenance: dict[str, object] = {}
    opacities: dict[str, list] = {}

    def where(cls: str, key: str):
        o = r.origins.get((cls, key))
        if o is None:
            return None, None
        return f"scheme-{o[0]}.scheme", o[1]

    def raw_value(cls: str, key: str):
        v = r.settings.get((cls, key))
        return v.strip().strip('"').strip() if v is not None else None

    def spelled(cls: str, key: str) -> str:
        """The directive as Stata's file writes it, for a rule sentence."""
        return f"{cls} {key} {raw_value(cls, key)}" if key else \
            f"{cls} {raw_value(cls, key)}"

    def prov_entry(kind: str, cls: str, key: str, rule=None, via=None) -> dict:
        file, line = where(cls, key)
        entry = {
            "kind": kind,
            "directive": f"{cls} {key}" if key else cls,
            "value": raw_value(cls, key),
            "file": file,
            "line": line,
        }
        if rule:
            entry["rule"] = rule
        if via:
            entry["via"] = via
        return entry

    def getsrc(cls: str, keys: list[str], class_default: bool,
               chain_name: str = "Stata's documented fallback"):
        """First matching key in ``keys``; (value, source, provenance).

        ``keys[0]`` is the key the translation carries; a hit on it is a
        transcription, a hit further down the list or on the class default
        is an inference, and ``chain_name`` says which rule was followed.
        """
        for k in keys:
            v = r.get(cls, k, class_default=False)
            if v is not None:
                if k == keys[0]:
                    prov = prov_entry("transcribed", cls, k)
                else:
                    prov = prov_entry("inferred", cls, k, rule=(
                        f"{chain_name}; `{cls} {keys[0]}' is not set anywhere "
                        f"in the #include chain, took `{spelled(cls, k)}'"))
                return v, f"{cls} {k}", prov
        if class_default:
            v = r.settings.get((cls, ""))
            if v is not None:
                prov = prov_entry("inferred", cls, "", rule=(
                    f"class default; `{cls} {keys[0]}' is not set anywhere in "
                    f"the #include chain, took the bare `{spelled(cls, '')}' "
                    "class default"))
                return v, f"{cls} <class-default>", prov
        return None, None, None

    def color_of(out_key: str, keys: list[str], required: bool = True):
        tok, src_s, prov = getsrc("color", keys, class_default=False,
                                  chain_name="Stata's generic colour fallback")
        if tok is None:
            if required:
                unresolvable.append(
                    f"{out_key}: none of [" + ", ".join("color " + k for k in keys)
                    + "] is set anywhere in the #include chain")
            sources[out_key] = None
            provenance[out_key] = None
            return None
        sources[out_key] = src_s
        provenance[out_key] = prov
        return c.resolve(tok)

    def color_alpha_of(out_key: str, keys: list[str], required: bool = True):
        """As ``color_of``, with Stata's %NN opacity (or None) recorded in
        ``<out_key>_opacity``."""
        tok, src_s, prov = getsrc("color", keys, class_default=False,
                                  chain_name="Stata's generic colour fallback")
        if tok is None:
            if required:
                unresolvable.append(
                    f"{out_key}: none of [" + ", ".join("color " + k for k in keys)
                    + "] is set anywhere in the #include chain")
            sources[out_key] = None
            provenance[out_key] = None
            opacities[f"{out_key}_opacity"] = None
            return None
        sources[out_key] = src_s
        provenance[out_key] = prov
        hexval, pct = c.resolve_with_opacity(tok)
        opacities[f"{out_key}_opacity"] = pct
        return hexval

    # --- the p1..p15 cycle, with Stata's p#stub -> pstub -> p# -> p chain --- #
    P_CHAIN = "p#stub -> pstub -> p# -> p"

    def p_chain(cls: str, n: int, stub: str = ""):
        keys = []
        if stub:
            keys += [f"p{n}{stub}", f"p{stub}"]
        keys += [f"p{n}", "p"]
        return getsrc(cls, keys, class_default=False, chain_name=P_CHAIN)

    def p_series(out_key, cls, stub, conv):
        vals, srcs, provs = [], [], []
        for i in range(1, N_PLOTS + 1):
            tok, s, prov = p_chain(cls, i, stub)
            if tok is None:
                unresolvable.append(
                    f"{out_key}[{i}]: no value for p{i}{stub} and no fallback")
            vals.append(conv(tok))
            srcs.append(s)
            provs.append(prov)
        sources[out_key] = srcs
        provenance[out_key] = provs
        return vals

    def p_color_series(out_key, stub):
        """The colour cycle, hex in *out_key* and Stata's %NN opacity (or
        None) beside it in ``<out_key>_opacity``."""
        pcts: list = []

        def conv(tok):
            if tok is None:
                pcts.append(None)
                return None
            hexval, pct = c.resolve_with_opacity(tok)
            pcts.append(pct)
            return hexval
        vals = p_series(out_key, "color", stub, conv)
        opacities[f"{out_key}_opacity"] = pcts
        return vals

    p_colors = p_color_series("p_colors", "")
    p_line_colors = p_color_series("p_line_colors", "line")
    p_bar_colors = p_color_series("p_bar_colors", "bar")
    # A marker's fill and outline (WP-30 P1.4a): style/markerstyle-p#
    # .style reads `set fillcolor scheme p#markfill' and `set linestyle
    # scheme p#mark', whose linestyle-p#mark.style reads `set color scheme
    # p#markline'.  `color p#mark' is never a marker colour.
    p_mark_colors = p_color_series("p_mark_colors", "markfill")
    p_markline_colors = p_color_series("p_markline_colors", "markline")
    # A marker label's colour and size (WP-30 P1.4b): style/textboxstyle-
    # p#.style reads `set color scheme p#label' and `set size scheme
    # p#label', so the chains are p#label -> plabel -> p# -> p.
    p_label_colors = p_color_series("p_label_colors", "label")
    p_label_sizes = p_series("p_label_sizes", "gsize", "label",
                             lambda t: resolve_sized(r, "gsize", t))
    p_symbols = p_series("p_symbols", "symbol", "", lambda t: t)
    # The marker size, per plot: style/markerstyle-p#.style says `set size
    # scheme p#', so `symbolsize p#' -> `symbolsize p'.  Only s1manual's
    # chain declares a `symbolsize p#' (scheme-s1manual.scheme:51-59).
    p_symbolsizes = p_series("p_symbolsizes", "symbolsize", "",
                             lambda t: resolve_sized(r, "symbolsize", t))
    p_line_patterns = p_series("p_line_patterns", "linepattern", "line",
                               lambda t: t)
    p_line_dash = [resolve_linepattern(r, t) for t in p_line_patterns]

    # --- the "lineplot" stub ------------------------------------------------ #
    # Stata distinguishes two per-plot line stubs, and conflating them is a real
    # rendering error rather than a nuance:
    #
    #   p#line      the CONNECTING line of a connected/scatter-with-lines plot
    #   p#lineplot  the line drawn by ``twoway line`` itself
    #
    # So a plain ``twoway line`` under s2mono takes its dash pattern from
    # ``linepattern p#lineplot`` (solid / dash / vshortdash / ...), not from
    # ``linepattern p#line`` (which s2mono leaves at the ``linepattern p solid``
    # class value inherited from s2color).  Only the s2mono branch of the base
    # schemes declares any ``lineplot`` key, and only s2mono and s2gmanual
    # write one themselves; everywhere else these resolve through the ordinary
    # p#stub -> pstub -> p# -> p fallback, which is why ``lineplot_declared``
    # below is recorded separately: it says whether the value was WRITTEN by a
    # scheme or merely INHERITED by fallback, and a translation must not
    # present the second as though it were the first.
    p_lineplot_colors = p_color_series("p_lineplot_colors", "lineplot")
    p_lineplot_patterns = p_series("p_lineplot_patterns", "linepattern",
                                   "lineplot", lambda t: t)
    p_lineplot_dash = [resolve_linepattern(r, t) for t in p_lineplot_patterns]

    def lineplot_declared(cls: str) -> bool:
        """True if any ``<cls> p*lineplot`` key is set in the #include chain."""
        return any(
            k == "plineplot" or (k.startswith("p") and k.endswith("lineplot"))
            for (c_, k) in r.settings
            if c_ == cls
        )

    def scalar(out_key, cls, keys, conv, class_default=True,
               chain_name="Stata's documented fallback", required=True):
        tok, s, prov = getsrc(cls, keys, class_default=class_default,
                              chain_name=chain_name)
        sources[out_key] = s
        provenance[out_key] = prov
        if tok is None:
            if required:
                unresolvable.append(
                    f"{out_key}: none of [" + ", ".join(f"{cls} {k}" for k in keys)
                    + "] set and no class default")
            return None
        return conv(tok)

    # --- graph size: "graphsize x" / "graphsize y", then bare "graphsize" --- #
    def graphsize(axis):
        tok, s, prov = getsrc("graphsize", [axis], class_default=True)
        sources[f"graphsize_{axis}"] = s
        provenance[f"graphsize_{axis}"] = prov
        if tok is None:
            unresolvable.append(
                f"graphsize_{axis}: neither 'graphsize {axis}' nor a bare "
                f"'graphsize' default is set")
            return None
        return _as_number(tok.strip())

    # --- grid switches, resolved through the axisstyle indirection ---------- #
    grid_axes = {"x": axis_grid_switches(r, "x"),
                 "y": axis_grid_switches(r, "y")}

    def effective_grid(out_key: str, axis: str, which: str):
        """The yes/no Stata ends up with for *which* grid of *axis*."""
        info = grid_axes[axis]
        key = info[f"{which}_key"]
        if key is None:
            lit = info[f"{which}_literal"]
            if lit is None:
                unresolvable.append(
                    f"{out_key}: {info['style_file']} sets no draw_{which}_grid")
                sources[out_key] = None
                provenance[out_key] = None
                return None
            sources[out_key] = f"{info['style_file']}: set draw_{which}_grid {lit}"
            provenance[out_key] = {
                "kind": "transcribed",
                "directive": f"set draw_{which}_grid",
                "value": lit,
                "file": info["style_file"],
                "line": None,
                "via": f"axisstyle {info['role']} = {info['axisstyle']}",
            }
            return lit
        tok = r.get("yesno", key, class_default=False)
        if tok is None:
            unresolvable.append(
                f"{out_key}: yesno {key} (named by {info['style_file']}) is "
                "not set anywhere in the #include chain")
            sources[out_key] = None
            provenance[out_key] = None
            return None
        via = ""
        if info["axisstyle"].lower() != info["role"]:
            via = (f" (via axisstyle {info['role']} = {info['axisstyle']}, "
                   f"{info['style_file']})")
        sources[out_key] = f"yesno {key}{via}"
        provenance[out_key] = prov_entry(
            "transcribed", "yesno", key,
            via=(f"axisstyle {info['role']} = {info['axisstyle']}, "
                 f"{info['style_file']}") if via else None)
        return tok.strip()

    # --- style-file indirections: a line or a text box ------------------- #
    # Stata draws a reference line, the plot region's border and note() by
    # following a chain of style files, each `set <attr> scheme <key>'
    # naming the scheme key the next link reads.  The translation carries
    # the EFFECTIVE value under the key dash reads; a hit on that very key
    # is a transcription, any other link is an inference whose rule spells
    # the chain out.
    def style_ref(setting):
        """``("scheme", key)`` or ``("literal", token)`` or None."""
        parts = setting.split() if setting else []
        if len(parts) == 2 and parts[0] == "scheme":
            return "scheme", parts[1]
        if len(parts) == 1:
            return "literal", parts[0].strip('"')
        return None

    def linked(out_key, dash_cls, dash_key, cls, ref, chain):
        """The value a style file's *ref* names, with its provenance.

        Sets ``sources``/``provenance`` for *out_key* and returns the raw
        token, or None (unresolvable, or no link)."""
        if ref is None:
            sources[out_key] = None
            provenance[out_key] = None
            unresolvable.append(f"{out_key}: {chain} sets no {cls}")
            return None
        if ref[0] == "literal":
            sources[out_key] = f"{chain}: {cls} {ref[1]}"
            provenance[out_key] = {
                "kind": "inferred", "directive": (f"{dash_cls} {dash_key}" if dash_key else dash_cls),
                "value": ref[1], "file": chain.rsplit(" -> ", 1)[-1], "line": None,
                "rule": f"{chain} sets the literal {cls} `{ref[1]}'"}
            return ref[1]
        key = ref[1]
        tok = r.get(cls, key, class_default=False)
        via_default = False
        if tok is None:
            tok = r.settings.get((cls, ""))
            via_default = tok is not None
        if tok is None:
            sources[out_key] = None
            provenance[out_key] = None
            unresolvable.append(
                f"{out_key}: {chain} reads `{cls} {key}', which is not set "
                "anywhere in the #include chain and has no class default")
            return None
        if via_default:
            sources[out_key] = f"{cls} <class-default>"
            provenance[out_key] = prov_entry("inferred", cls, "", rule=(
                f"{chain} reads `{cls} {key}', which is not set anywhere in "
                f"the #include chain; took the bare `{spelled(cls, '')}' "
                "class default"))
        elif (cls, key) == (dash_cls, dash_key):
            sources[out_key] = f"{cls} {key}"
            provenance[out_key] = prov_entry("transcribed", cls, key)
        else:
            sources[out_key] = f"{cls} {key}"
            provenance[out_key] = prov_entry("inferred", cls, key, rule=(
                f"{chain} reads `{spelled(cls, key)}'"))
        return tok

    def line_via(prefix, dash_key_color, dash_key_line, ls_name, chain):
        """Colour, width and pattern of linestyle *ls_name*: the effective
        border or line, recorded as <prefix>_color / _line_width /
        _pattern (and _drawn).  None colour means Stata draws no line."""
        st = r.style("linestyle", ls_name.lower())
        lchain = f"{chain} -> style/linestyle-{ls_name.lower()}.style"
        if st is None:
            unresolvable.append(f"{prefix}: no style/linestyle-"
                                f"{ls_name.lower()}.style")
            st = {}
        ctok = linked(f"{prefix}_color", "color", dash_key_color, "color",
                      style_ref(st.get("color")), lchain)
        wtok = linked(f"{prefix}_line_width", "linewidth", dash_key_line,
                      "linewidth", style_ref(st.get("width")), lchain)
        ptok = linked(f"{prefix}_pattern", "linepattern", dash_key_line,
                      "linepattern", style_ref(st.get("pattern")), lchain)
        hexval = c.resolve(ctok) if ctok is not None else None
        width = resolve_linewidth(r, wtok)
        drawn = (hexval is not None
                 and not (width and width.get("value") == 0))
        if not drawn:
            # The border is not drawn: the colour's provenance says why,
            # and a width or pattern of a line that is not drawn is not
            # carried.
            if provenance.get(f"{prefix}_color") is None:
                provenance[f"{prefix}_color"] = {
                    "kind": "inferred",
                    "directive": f"color {dash_key_color}", "value": "none",
                    "file": lchain.rsplit(" -> ", 1)[-1], "line": None,
                    "rule": f"{lchain} draws no line"}
        return {
            f"{prefix}_drawn": drawn,
            f"{prefix}_color": hexval if drawn else None,
            f"{prefix}_line_width": width if drawn else None,
            f"{prefix}_pattern": (ptok.strip().strip('"')
                                  if drawn and ptok is not None else None),
        }

    # Reference lines.  twoway's xline()/yline() build their gridline with
    # `.gridlinestyle.new, style(scheme)' (_gs_parse_and_log_lines.ado):
    # the `gridlinestyle' class default, whose style file sets `linestyle
    # scheme xyline'; `linestyle xyline' names style/linestyle-<name>.style,
    # which reads `color xyline', `linewidth xyline' and `linepattern
    # xyline'.
    def xyline_truth():
        gls = (r.settings.get(("gridlinestyle", "")) or "default").strip()
        gst = r.style("gridlinestyle", gls.lower()) or {}
        chain = (f"gridlinestyle {gls} -> "
                 f"style/gridlinestyle-{gls.lower()}.style")
        ref = style_ref(gst.get("linestyle"))
        if ref is not None and ref[0] == "scheme":
            ls = r.get("linestyle", ref[1], class_default=True)
            chain += f" -> linestyle {ref[1]} {ls}"
        else:
            ls = ref[1] if ref else None
        if not ls:
            unresolvable.append(f"xyline: {chain} names no linestyle")
            return {"xyline_drawn": False, "xyline_color": None,
                    "xyline_line_width": None, "xyline_pattern": None}
        return line_via("xyline", "xyline", "xyline", ls.strip(), chain)

    # The plot region's border.  twoway draws its plot region in
    # `plotregionstyle twoway', whose style file sets `boxstyle scheme
    # twoway_plotregion'; that areastyle sets `linestyle scheme plotregion'
    # (or `none'), and the linestyle file reads `color plotregion_line',
    # `linewidth plotregion' and `linepattern plotregion' (s2color), or
    # the foreground's (s1color), or draws none (economist).
    def plotregion_line_truth():
        prs = (r.get("plotregionstyle", "twoway", class_default=False)
               or "twoway").strip()
        pst = r.style("plotregionstyle", prs.lower()) or {}
        chain = (f"plotregionstyle twoway {prs} -> "
                 f"style/plotregionstyle-{prs.lower()}.style")
        ref = style_ref(pst.get("boxstyle"))
        area, area_key = None, None
        if ref is not None and ref[0] == "scheme":
            area_key = ref[1]
            area = r.get("areastyle", area_key, class_default=True)
            chain += f" -> areastyle {area_key} {area}"
        elif ref is not None:
            area = ref[1]
        ast = r.style("areastyle", (area or "").strip().lower()) or {}
        chain += f" -> style/areastyle-{(area or '').strip().lower()}.style"
        ref = style_ref(ast.get("linestyle"))
        if ref is not None and ref[0] == "scheme":
            ls = r.get("linestyle", ref[1], class_default=True)
            chain += f" -> linestyle {ref[1]} {ls}"
        else:
            ls = ref[1] if ref else None
        if not ls:
            unresolvable.append(f"plotregion_line: {chain} names no linestyle")
            return {"plotregion_line_drawn": False,
                    "plotregion_line_color": None,
                    "plotregion_line_line_width": None,
                    "plotregion_line_pattern": None}
        out_ = line_via("plotregion_line", "plotregion_line", "plotregion",
                        ls.strip(), chain)
        if (not out_["plotregion_line_drawn"] and area_key
                and r.origins.get(("areastyle", area_key))):
            # Where the chain ends in no line, name the directive that
            # took it there (economist: `areastyle twoway_plotregion none').
            provenance["plotregion_line_color"] = prov_entry(
                "inferred", "areastyle", area_key, rule=(
                    f"{chain}: Stata draws no border"))
        return out_

    # note().  Stata draws it in `textboxstyle note' (small_body in
    # s2color; economist reverse_big, s1manual key_label), whose style
    # file names the size, colour, box and fill keys.
    def note_truth():
        tb = r.get("textboxstyle", "note", class_default=False)
        name = (tb or "small_body").strip().strip('"')
        if tb is not None:
            sources["note_textbox"] = "textboxstyle note"
            provenance["note_textbox"] = prov_entry(
                "transcribed", "textboxstyle", "note")
        else:
            sources["note_textbox"] = None
            provenance["note_textbox"] = None
            unresolvable.append("note_textbox: `textboxstyle note' is not "
                                "set anywhere in the #include chain")
        st = r.style("textboxstyle", name.lower()) or {}
        chain = f"textboxstyle note {name} -> " \
                f"style/textboxstyle-{name.lower()}.style"
        size_ref = style_ref(st.get("size"))
        color_ref = style_ref(st.get("color"))
        draw_ref = style_ref(st.get("drawbox"))
        fill_ref = style_ref(st.get("fillcolor"))
        size_key = size_ref[1] if size_ref and size_ref[0] == "scheme" else None
        color_key = (color_ref[1] if color_ref and color_ref[0] == "scheme"
                     else None)
        draw_key = draw_ref[1] if draw_ref and draw_ref[0] == "scheme" else None
        fill_key = fill_ref[1] if fill_ref and fill_ref[0] == "scheme" else None
        size_tok = linked("note_text_size", "gsize", size_key, "gsize",
                          size_ref, chain)
        color_tok = linked("note_text_color", "color", color_key, "color",
                           color_ref, chain)
        if draw_ref is None:
            drawn = False
        elif draw_ref[0] == "literal":
            drawn = draw_ref[1].lower() == "yes"
        else:
            v = r.get("yesno", draw_key, class_default=False)
            drawn = (v or "no").strip().lower() == "yes"
        fill = None
        if drawn:
            ftok = linked("note_box_fill_color", "color", fill_key, "color",
                          fill_ref, chain)
            fill = c.resolve(ftok) if ftok is not None else None
        else:
            sources["note_box_fill_color"] = None
            provenance["note_box_fill_color"] = None
        return {
            "note_textbox": {"name": name, "size_key": size_key,
                             "color_key": color_key,
                             "drawbox": (True if draw_ref and
                                         draw_ref[0] == "literal" and drawn
                                         else draw_key),
                             "fill_key": fill_key},
            "note_text_size": resolve_sized(r, "gsize", size_tok),
            "note_text_color": (c.resolve(color_tok)
                                if color_tok is not None else None),
            "note_box_drawn": drawn,
            "note_box_fill_color": fill,
        }

    # The chrome (WP-30 P1.2a): tick-label angles, grid patterns, the tick's
    # colour, width, length and side, each axis role's line and tick flags,
    # the alt_xaxes/alt_yaxes switches, the text boxes' justification and
    # clock positions, `system naturally_white', and the p#bar/p#area
    # intensity chains.  Each key is the scheme key Stata's style file names
    # (style/tickstyle-major.style: `set length scheme tick', `set position
    # scheme axis_tick', `set linestyle scheme tick'; style/ticksetstyle-
    # major_vert_default.style: `set tickangle scheme vertical_tick';
    # style/gridstyle-major.style: `set linestyle scheme major_grid').
    def chrome_one(out_key, cls, key, conv, default=None, rule=None):
        tok, s_, prov = getsrc(cls, [key], class_default=False)
        if tok is None and default is not None:
            tok = default
            s_ = None
            prov = {"kind": "inferred", "directive": f"{cls} {key}",
                    "value": default, "file": None, "line": None,
                    "rule": rule or (f"`{cls} {key}' is not set anywhere in "
                                     f"the #include chain; Stata's default "
                                     f"`{default}'")}
        sources[out_key] = s_
        provenance[out_key] = prov
        return conv(tok) if tok is not None else None

    def by_chrome_truth():
        """WP-30 P1.15c: the keys twoway's by() reads for its shared axes,
        legend and colour key (bygraph_g.class parse_settings, SetLegend,
        SetClegend; bygraphstyle-default.style) and for the panel label's
        box (bygraphstyle-default.style draws the label as
        ``subtitle(, astextbox box blcolor(scheme bylabel_outline))``).
        A key the #include chain does not set is left unset."""
        res = {}
        tok_name = lambda t: t.strip().strip('"')
        for k in ("by_legend_position", "zyx2legend_position"):
            res[k] = scalar(k, "clockdir", [k],
                            lambda t: _as_number(t.strip()),
                            class_default=False, required=False)
        for k in ("by_legend_ring", "zyx2legend_ring"):
            res[k] = scalar(k, "gridringstyle", [k],
                            lambda t: _as_number(t.strip()),
                            class_default=False, required=False)
        for k in BY_YESNO_KEYS:
            res[k] = scalar(k, "yesno", [k],
                            lambda t: tok_name(t).lower() == "yes",
                            class_default=False, required=False)
        res["by_indiv_margin"] = scalar(
            "by_indiv_margin", "margin", ["by_indiv"], tok_name,
            class_default=False, required=False)
        res["margin_subheading"] = scalar(
            "margin_subheading", "margin", ["subheading"], tok_name,
            class_default=False, required=False)
        res["bylabel_outline_color"] = color_of(
            "bylabel_outline_color", ["bylabel_outline"], required=False)
        # The label box's fill: the scheme's `textboxstyle subtitle' names a
        # style file whose `set fillcolor scheme <key>' names the colour
        # (textboxstyle-subheading.style: textbox; -subheading_gs.style:
        # bylabel_outline).
        res["by_label_fill"] = None
        sty = r.get("textboxstyle", "subtitle", class_default=False)
        sty = tok_name(sty) if sty else None
        fill = (r.style("textboxstyle", sty) or {}).get("fillcolor", "") \
            if sty else ""
        if fill.startswith("scheme "):
            ck = fill[len("scheme "):].strip()
            tok = r.get("color", ck, class_default=False)
            if tok is not None:
                res["by_label_fill"] = c.resolve(tok)
                sources["by_label_fill"] = f"color {ck}"
                provenance["by_label_fill"] = prov_entry(
                    "inferred", "color", ck, rule=(
                        f"dash's derived key: `textboxstyle subtitle {sty}', "
                        f"style/textboxstyle-{sty}.style `set fillcolor "
                        f"scheme {ck}', then `{spelled('color', ck)}'"))
        return res

    def text_option_truth():
        """WP-30 P1.10: the keys `textboxstyle text_option' reads for
        text() and ttext() that no other group resolves -- its box's fill,
        the compass direction it is placed in from its point, whether it
        is boxed, its margin, its justification and its vertical
        alignment (scheme-s2color.scheme `color text_option_fill',
        `compass2dir text_option', `yesno text_option', `margin
        text_option', `horizontal text_option', `vertical_text
        text_option').  A key the #include chain does not set is left
        unset."""
        tok_name = lambda t: t.strip().strip('"')
        return {
            "text_option_fill": color_of(
                "text_option_fill", ["text_option_fill"], required=False),
            "text_option_placement": scalar(
                "text_option_placement", "compass2dir", ["text_option"],
                tok_name, class_default=False, required=False),
            "text_option_box": scalar(
                "text_option_box", "yesno", ["text_option"],
                lambda t: tok_name(t).lower() == "yes",
                class_default=False, required=False),
            "text_option_margin": scalar(
                "text_option_margin", "margin", ["text_option"], tok_name,
                class_default=False, required=False),
            "text_option_justification": scalar(
                "text_option_justification", "horizontal", ["text_option"],
                tok_name, class_default=False, required=False),
            "text_option_vertical": scalar(
                "text_option_vertical", "vertical_text", ["text_option"],
                tok_name, class_default=False, required=False),
        }

    def chrome_truth():
        tok_name = lambda t: t.strip().strip('"')
        res = {
            "tick_angle_x": chrome_one("tick_angle_x", "anglestyle",
                                       "horizontal_tick",
                                       lambda t: resolve_anglestyle(r, t),
                                       "horizontal"),
            "tick_angle_y": chrome_one("tick_angle_y", "anglestyle",
                                       "vertical_tick",
                                       lambda t: resolve_anglestyle(r, t),
                                       "horizontal"),
            "major_grid_pattern": chrome_one(
                "major_grid_pattern", "linepattern", "major_grid",
                lambda t: resolve_linepattern(r, t), "solid"),
            "minor_grid_pattern": chrome_one(
                "minor_grid_pattern", "linepattern", "minor_grid",
                lambda t: resolve_linepattern(r, t), "solid"),
            "tick_color": chrome_one(
                "tick_color", "color", "tick",
                lambda t: None if tok_name(t).lower() == "none"
                else c.resolve(t)),
            "minortick_color": chrome_one(
                "minortick_color", "color", "minortick",
                lambda t: None if tok_name(t).lower() == "none"
                else c.resolve(t)),
            "tick_line_width": chrome_one("tick_line_width", "linewidth",
                                          "tick",
                                          lambda t: resolve_linewidth(r, t)),
            "tick_length": chrome_one("tick_length", "gsize", "tick",
                                      lambda t: resolve_sized(r, "gsize", t)),
            "tick_position": chrome_one("tick_position", "tickposition",
                                        "axis_tick", tok_name, "outside"),
        }
        styles = {}
        for which, roles in (("", AXIS_ROLES), ("2", AXIS2_ROLES)):
            for axis, role in roles.items():
                f = axis_style_flags(r, role)
                key = f"axis_style_{axis}{which}"
                tok, s_, prov = getsrc("axisstyle", [role], class_default=False)
                if tok is None:
                    prov = {"kind": "inferred",
                            "directive": f"axisstyle {role}", "value": role,
                            "file": None, "line": None,
                            "rule": f"`axisstyle {role}' is not set; the "
                                    f"style of the same name"}
                sources[key] = s_
                provenance[key] = prov
                styles[axis + which] = f
        res["axis_styles"] = styles
        res["alt_axes"] = {
            a: chrome_one(f"alt_{a}axes", "yesno", f"alt_{a}axes",
                          lambda t: tok_name(t).lower() == "yes", "no")
            for a in ("x", "y")}
        res["justification"] = {
            k: chrome_one(f"justification_{k}", "horizontal", k, tok_name,
                          "center")
            for k in ("heading", "subheading", "body", "small_body")}
        res["text_positions"] = {
            k: chrome_one(f"text_position_{k}", "clockdir", f"{k}_position",
                          lambda t: int(_as_number(tok_name(t)) or 0), d)
            for k, d in (("title", "12"), ("subtitle", "12"),
                         ("note", "7"), ("caption", "7"))}
        res["naturally_white"] = chrome_one(
            "naturally_white", "system", "naturally_white",
            lambda t: int(_as_number(tok_name(t)) or 0), "1")
        for stub in ("bar", "area"):
            vals, srcs, provs = [], [], []
            for i in range(1, N_PLOTS + 1):
                tok, s_, prov = p_chain("intensity", i, stub)
                vals.append(resolve_intensity(r, tok))
                srcs.append(s_)
                provs.append(prov)
            sources[f"p_{stub}_intensity"] = srcs
            provenance[f"p_{stub}_intensity"] = provs
            res[f"p_{stub}_intensity"] = vals
        # The bare `symbolsize' class default: twoway's size for an msize()
        # name it does not know (S08; large in economist, medium in s2color).
        res["symbolsize_default"] = scalar(
            "symbolsize_default", "symbolsize", [""],
            lambda t: resolve_sized(r, "symbolsize", t), class_default=True,
            required=False)
        if sources.get("symbolsize_default"):
            sources["symbolsize_default"] = "symbolsize"
        return res

    out = {
        # Stata's own `label "..."' for the scheme.
        "label": r.label,
        # root -> ... -> child: the order the directives are applied, the
        # child's last.  (The resolver opens the files child-first.)
        "include_chain": list(reversed(r.include_chain)),
        "p_colors": p_colors,
        "p_line_colors": p_line_colors,
        "p_bar_colors": p_bar_colors,
        "p_mark_colors": p_mark_colors,
        "p_markline_colors": p_markline_colors,
        "p_label_colors": p_label_colors,
        "p_label_sizes": p_label_sizes,
        "p_symbols": p_symbols,
        "p_symbolsizes": p_symbolsizes,
        "p_line_patterns": p_line_patterns,
        "p_line_dash_patterns": [d["dash"] if d else None for d in p_line_dash],

        "p_lineplot_colors": p_lineplot_colors,
        "p_lineplot_patterns": p_lineplot_patterns,
        "p_lineplot_dash_patterns": [
            d["dash"] if d else None for d in p_lineplot_dash
        ],
        # Whether the chain actually WRITES a lineplot key, as opposed to
        # inheriting one by fallback.  See the note above p_lineplot_colors.
        "lineplot_declared": {
            "color": lineplot_declared("color"),
            "linepattern": lineplot_declared("linepattern"),
        },

        "background_color": color_of("background_color", ["background"]),
        "plotregion_color": color_of("plotregion_color", ["plotregion"]),
        "legend_bg_color": color_of("legend_bg_color", ["legend"]),
        "legend_border_color": color_of("legend_border_color", ["legend_line"]),
        # Stata draws the major grid; "color grid" is the generic fallback.
        "grid_color": color_of("grid_color", ["major_grid", "grid"]),
        # The generic `color grid' itself: SchemeParser reads it when a file
        # has no `color major_grid'.  Two hand-written translations carry it;
        # it is checked and given provenance where present, never appended.
        "grid_color_generic": color_of("grid_color_generic", ["grid"],
                                       required=False),
        "minor_grid_color": color_of("minor_grid_color", ["minor_grid"]),
        # Grid switches: the EFFECTIVE per-axis values (see the module
        # docstring).  A grid belongs to an axis and its key is named for that
        # axis's orientation: the x (horizontal) axis draws the VERTICAL
        # lines at the x ticks from draw_*_hgrid; the y axis draws the
        # horizontal lines from draw_*_vgrid -- or, where the scheme maps
        # `axisstyle vertical_default' elsewhere (economist), from whatever
        # key that style file names.  `sources' records which key it was.
        # The y-axis flag once came from `draw_major_grid', which nothing
        # under style/ reads; it is `no' in every scheme, so the fixture said
        # "no grid" for all fourteen where Stata gives yes for ten.
        "draw_major_hgrid": effective_grid("draw_major_hgrid", "x", "major"),
        "draw_minor_hgrid": effective_grid("draw_minor_hgrid", "x", "minor"),
        "draw_major_vgrid": effective_grid("draw_major_vgrid", "y", "major"),
        "draw_minor_vgrid": effective_grid("draw_minor_vgrid", "y", "minor"),
        # The bare keys, as transcribed: dead at scheme level, kept so the
        # translated file's faithful copy of them can be checked.
        "draw_major_grid": scalar("draw_major_grid", "yesno",
                                  ["draw_major_grid"], lambda t: t.strip(),
                                  class_default=False),
        "draw_minor_grid": scalar("draw_minor_grid", "yesno",
                                  ["draw_minor_grid"], lambda t: t.strip(),
                                  class_default=False),
        # WP-30 P1.21b: gridlinestyle-default's `set extend_low scheme
        # xyline_extend_low' (and _high): whether a reference line reaches
        # the frame at its low and high end.
        "xyline_extend_low": scalar("xyline_extend_low", "yesno",
                                    ["xyline_extend_low"],
                                    lambda t: t.strip(), class_default=False),
        "xyline_extend_high": scalar("xyline_extend_high", "yesno",
                                     ["xyline_extend_high"],
                                     lambda t: t.strip(),
                                     class_default=False),
        "grid_axes": grid_axes,

        "title_color": color_of("title_color", ["heading"]),
        "axis_line_color": color_of("axis_line_color", ["axisline"]),
        # One colour per textbox style: style/textboxstyle-<name>.style reads
        # `color <name>'.  title() is heading, subtitle() subheading,
        # caption() body, note() small_body (NOT body), legend keys
        # key_label, axis titles axis_title, tick labels tick_label.
        # `color text' and `color foreground' are the scheme's general text
        # and foreground colours.
        "subheading_color": color_of("subheading_color", ["subheading"]),
        "body_color": color_of("body_color", ["body"]),
        "small_body_color": color_of("small_body_color", ["small_body"]),
        "text_color": color_of("text_color", ["text"]),
        "axis_title_color": color_of("axis_title_color", ["axis_title"]),
        "tick_label_color": color_of("tick_label_color", ["tick_label"]),
        "key_label_color": color_of("key_label_color", ["key_label"]),
        "foreground_color": color_of("foreground_color", ["foreground"]),

        "default_line_width": scalar(
            "default_line_width", "linewidth", ["p"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        "grid_line_width": scalar(
            "grid_line_width", "linewidth", ["major_grid", "grid"],
            lambda t: resolve_linewidth(r, t), class_default=True,
            chain_name="Stata's generic grid fallback"),
        "minor_grid_line_width": scalar(
            "minor_grid_line_width", "linewidth", ["minor_grid"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        "axis_line_width": scalar(
            "axis_line_width", "linewidth", ["axisline"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        # A bar's and an area's outline: linestyle-p#bar.style and
        # linestyle-p#area.style read `linewidth p#bar' and `p#area', which
        # fall to `pbar' and `parea'.  Every Stata scheme sets `linewidth
        # pbar' (s2color thin, economist vvthin); only economist sets
        # `parea' (thin), so an absent one is ordinary (the chain goes on
        # to p# and p) and not unresolvable.  No Stata scheme sets a
        # numbered p#bar, p#area or any p#mark/pmark width.
        "bar_line_width": scalar(
            "bar_line_width", "linewidth", ["pbar"],
            lambda t: resolve_linewidth(r, t), class_default=False,
            required=False),
        "area_line_width": scalar(
            "area_line_width", "linewidth", ["parea"],
            lambda t: resolve_linewidth(r, t), class_default=False,
            required=False),

        # A ci fit's band and, under pstyle(ci) or pstyle(ci2), its line.
        # twoway draws the band in areastyle ci (style/areastyle-ci.style:
        # `set linestyle scheme ci_area', `set shadestyle scheme ci'), so
        # its fill is `color ci_area' at `intensity ci_area'
        # (shadestyle-ci.style) and its outline `color ci_arealine' at
        # `linewidth ci_area' and `linepattern ci_area'
        # (linestyle-ci_area.style); linestyle-ci.style reads `color
        # ci_line', `linewidth ci' and `linepattern ci'.  ci2 reads only
        # three keys of its own: shadestyle-ci2.style `color ci2_area' (at
        # `intensity ci_area'), linestyle-ci2_area.style `color
        # ci2_arealine' and `linewidth ci2_area' (at `linepattern
        # ci_area'), and linestyle-ci2.style is ci's line (measured
        # 24sep2026 from the graph object under all twenty schemes;
        # test/fixtures/ci_band_style_truth.json).  A width, intensity or
        # pattern no file in the chain writes is the class default, as
        # Stata's scheme.class returns it.
        "ci_area_color": color_of("ci_area_color", ["ci_area"]),
        "ci_arealine_color": color_of("ci_arealine_color", ["ci_arealine"]),
        "ci_line_color": color_of("ci_line_color", ["ci_line"]),
        "ci2_area_color": color_of("ci2_area_color", ["ci2_area"]),
        "ci2_arealine_color": color_of("ci2_arealine_color",
                                       ["ci2_arealine"]),
        "ci_area_alpha": scalar("ci_area_alpha", "intensity", ["ci_area"],
                                lambda t: resolve_intensity(r, t)),
        "ci_area_line_width": scalar(
            "ci_area_line_width", "linewidth", ["ci_area"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        "ci2_area_line_width": scalar(
            "ci2_area_line_width", "linewidth", ["ci2_area"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        "ci_line_width": scalar(
            "ci_line_width", "linewidth", ["ci"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        "ci_area_pattern": scalar(
            "ci_area_pattern", "linepattern", ["ci_area"],
            lambda t: t.strip().strip('"')),
        "ci_pattern": scalar(
            "ci_pattern", "linepattern", ["ci"],
            lambda t: t.strip().strip('"')),
        # The histogram's style (WP-30 P1.4a): shadestyle-histogram.style
        # (`set color scheme histogram', `set intensity scheme histogram')
        # and linestyle-histogram.style (`set color scheme histogram_line',
        # `set width scheme histogram').
        "histogram_color": color_alpha_of("histogram_color", ["histogram"]),
        "histogram_line_color": color_alpha_of("histogram_line_color",
                                               ["histogram_line"]),
        "histogram_intensity": scalar(
            "histogram_intensity", "intensity", ["histogram"],
            lambda t: resolve_intensity(r, t)),
        "histogram_line_width": scalar(
            "histogram_line_width", "linewidth", ["histogram"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        # A ci band under pstyle(p#) is areastyle p# (areastyle-p#.style:
        # linestyle and shadestyle p#other), whose outline width is
        # `linewidth p#other' -> `pother' -> p# -> p.  Only economist sets
        # `linewidth pother' (thick); an absent one is ordinary.
        "other_line_width": scalar(
            "other_line_width", "linewidth", ["pother"],
            lambda t: resolve_linewidth(r, t), class_default=False,
            required=False),

        "fill_alpha": scalar("fill_alpha", "intensity", ["p"],
                             lambda t: resolve_intensity(r, t)),
        "bar_alpha": scalar("bar_alpha", "intensity", ["bar"],
                            lambda t: resolve_intensity(r, t)),
        "area_alpha": scalar("area_alpha", "intensity", ["area"],
                             lambda t: resolve_intensity(r, t)),

        "text_size": scalar("text_size", "gsize", ["text"],
                            lambda t: resolve_sized(r, "gsize", t)),
        "heading_size": scalar("heading_size", "gsize", ["heading"],
                               lambda t: resolve_sized(r, "gsize", t)),
        "axis_title_size": scalar("axis_title_size", "gsize", ["axis_title"],
                                  lambda t: resolve_sized(r, "gsize", t)),
        "tick_label_size": scalar("tick_label_size", "gsize", ["tick_label"],
                                  lambda t: resolve_sized(r, "gsize", t)),
        "note_size": scalar("note_size", "gsize", ["note"],
                            lambda t: resolve_sized(r, "gsize", t)),
        # The textbox sizes: subtitle() subheading, caption() body, note()
        # small_body (Stata's note textbox does not read `gsize note'),
        # legend keys key_label.
        "subheading_size": scalar("subheading_size", "gsize", ["subheading"],
                                  lambda t: resolve_sized(r, "gsize", t)),
        "body_size": scalar("body_size", "gsize", ["body"],
                            lambda t: resolve_sized(r, "gsize", t)),
        "small_body_size": scalar("small_body_size", "gsize", ["small_body"],
                                  lambda t: resolve_sized(r, "gsize", t)),
        "key_label_size": scalar("key_label_size", "gsize", ["key_label"],
                                 lambda t: resolve_sized(r, "gsize", t)),
        # WP-30 P1.24: the size and colour keys of the remaining text box
        # styles (style/textboxstyle-*.style), read by mlabtextstyle().  A
        # key the scheme's #include chain does not set is left unset.
        **{f"textbox_{k}_size": scalar(
            f"textbox_{k}_size", "gsize", [k],
            lambda t: resolve_sized(r, "gsize", t), class_default=False,
            required=False) for k in TEXTBOX_KEYS},
        **{f"textbox_{k}_color": color_of(f"textbox_{k}_color", [k],
                                          required=False)
           for k in TEXTBOX_KEYS},

        "graphsize_x": graphsize("x"),
        "graphsize_y": graphsize("y"),
        # WP-30 P1.3a: twoway's default tick count and plot-region margin.
        "numticks_horizontal_major": scalar(
            "numticks_horizontal_major", "numticks_g", ["horizontal_major"],
            lambda t: _as_number(t.strip()), class_default=False),
        "numticks_vertical_major": scalar(
            "numticks_vertical_major", "numticks_g", ["vertical_major"],
            lambda t: _as_number(t.strip()), class_default=False),
        "margin_twoway": scalar("margin_twoway", "margin", ["twoway"],
                                lambda t: t.strip().strip('"'),
                                class_default=False),
        "symbolsize": scalar("symbolsize", "symbolsize", ["p"],
                             lambda t: resolve_sized(r, "symbolsize", t)),
        # WP-31 B5b: twoway dot's rows of dots, markerstyle dots
        # (style/markerstyle-dots.style: symbol, size and fill `scheme
        # dots', outline linestyle dotmark, whose linestyle-dotmark.style
        # reads `linewidth dotmark' and `color dotmarkline').
        "dots_color": color_of("dots_color", ["dots"]),
        "dotmarkline_color": color_of("dotmarkline_color", ["dotmarkline"]),
        "dots_symbol": scalar("dots_symbol", "symbol", ["dots"],
                              lambda t: t.strip()),
        "dots_symbolsize": scalar(
            "dots_symbolsize", "symbolsize", ["dots"],
            lambda t: resolve_sized(r, "symbolsize", t)),
        "dotmark_line_width": scalar(
            "dotmark_line_width", "linewidth", ["dotmark"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        # WP-30 P1.20b: Stata's margin ladder (`gsize <x>margin'), the
        # sizes the marginstyles of plotregion(margin()) name.
        **{f"margin_ladder_{k}": scalar(
            f"margin_ladder_{k}", "gsize", [k], lambda t: t.strip(),
            class_default=False, required=False) for k in MARGIN_LADDER},

        "legend_position": scalar("legend_position", "clockdir",
                                  ["legend_position"],
                                  lambda t: _as_number(t.strip()),
                                  class_default=False),
        "legend_cols": scalar("legend_cols", "numstyle", ["legend_cols"],
                              lambda t: _as_number(t.strip()),
                              class_default=False),
        "legend_rows": scalar("legend_rows", "numstyle", ["legend_rows"],
                              lambda t: _as_number(t.strip()),
                              class_default=False),
    }
    out["margin_twoway_rs"] = resolve_margin_rs(r, out.get("margin_twoway"))
    out.update(by_chrome_truth())
    out.update(xyline_truth())
    out.update(plotregion_line_truth())
    out.update(note_truth())
    out.update(chrome_truth())
    out.update(text_option_truth())
    out.update(opacities)
    # WP-30 P1.14b: the keys the named styles read (scheme.class chain).
    _nsd, _hops, _bad = named_style_directives(r, provenance, sources)
    out["named_style_directives"] = _nsd
    out["style_hops"] = _hops
    unresolvable.extend(_bad)

    out["sources"] = sources
    out["provenance"] = provenance

    # Anything that came back None because a token could not be resolved.
    for msg in c.unresolved:
        if msg not in unresolvable:
            unresolvable.append(msg)
    out["unresolvable"] = unresolvable
    return out


# --------------------------------------------------------------------------- #
# The translated scheme files (dash-<name>.scheme in the package root)
# --------------------------------------------------------------------------- #
#
# A translated file is Stata's own one-directive-per-line grammar with every
# colour pre-resolved to #rrggbb (plus Stata's %NN opacity suffix where the
# scheme carries one).  A p#stub cycle (p#line, p#bar, p#mark, p#lineplot)
# carries only the keys Stata's own chain declares, and SchemeParser follows
# p#stub -> pstub -> p# -> p itself; the marker symbols likewise carry only
# the `symbol p#' / `symbol p' keys the chain declares.  A resolved p#stub or
# `symbol p#' line an older translation carried is removed
# (_drop_undeclared_stubs).  The
# files carry hand-written comments, so they are UPDATED IN PLACE rather than
# rewritten: every directive the fixture pins is checked against the file; a
# directive whose value disagrees is corrected on its own line and reported on
# stderr; a directive the file lacks is appended, in a dated block, after the
# file's last directive; a file that does not exist is created.  Each file
# ends with a generated provenance block -- one `* provenance:' line per
# directive, transcribed-from or inferred-by -- that is rewritten only when
# it differs.  A second run changes nothing.

_RULE = "* " + "-" * 75
PROVENANCE_BEGIN = "* BEGIN provenance (WP-17)"
PROVENANCE_END = "* END provenance (WP-17)"

def _fmt(value) -> str:
    """A fixture value as the token a .scheme directive carries."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _same(old: str, new: str) -> bool:
    """Directive values agree: same token, or the same number."""
    a, b = old.strip().lower(), new.strip().lower()
    if a == b:
        return True
    na, nb = _as_number(a), _as_number(b)
    return na is not None and nb is not None and float(na) == float(nb)


def _grid_comment(e: dict) -> list[str]:
    """The minor-grid comment, naming this scheme's own axisstyle chain."""
    ax = e.get("grid_axes") or {}
    x, y = ax.get("x") or {}, ax.get("y") or {}

    def chain(label, a):
        return [
            f"  {label} axis: axisstyle {a.get('role')} = {a.get('axisstyle')}",
            f"          -> {a.get('style_file')}",
            f"          -> {a.get('major_key') or a.get('major_literal')} / "
            f"{a.get('minor_key') or a.get('minor_literal')}",
        ]
    return [
        "Minor grid switches -- EFFECTIVE per-axis values.  twoway builds the x",
        "axis with `axisstyle horizontal_default' and the y axis with `axisstyle",
        "vertical_default'; the scheme maps each role to a style name, and that",
        "style file names the `yesno' key Stata actually reads:",
        *chain("x", x),
        *chain("y", y),
        "The draw_major_hgrid / draw_major_vgrid lines above hold the same",
        "effective values.  `yesno draw_minor_grid' is transcribed from Stata's",
        "file but, like draw_major_grid, no style file reads it.",
    ]


def _color_token(hexval, opacity) -> "str | None":
    """A colour directive's token: ``#rrggbb``, with Stata's ``%NN`` opacity
    suffix when the scheme carries one (sttrans), or None for `none'."""
    if hexval is None:
        return None
    if opacity is None:
        return hexval
    return f"{hexval}%{opacity:g}"


def expected_directives(e: dict) -> "list[tuple[list[str], list[tuple], bool]]":
    """The directives a translated file must carry for fixture entry *e*.

    Returns ordered groups ``(comment_lines, items, optional)`` with each item
    ``(class, key, value, ref)`` where ``ref`` is ``(fixture key, index)`` --
    index None for a scalar, 1-based for a p# cycle -- pointing at the
    fixture's ``provenance`` record for that directive.  The comment is
    written above the group when any of it has to be appended.  An
    ``optional`` group is checked where a file carries it but never appended.
    A ``None`` value (Stata colour ``none``, or an unresolvable entry) is
    skipped rather than written.
    """
    groups: list = []

    def group(comment, items, optional=False):
        items = [(c, k, _fmt(v), ref) for c, k, v, ref in items if v is not None]
        if items:
            groups.append((comment, items, optional))

    def name_of(spec):
        return (spec or {}).get("name")

    def scalar(cls, key, fixture_key, value=None, use_name=False):
        v = e.get(fixture_key)
        if use_name:
            v = name_of(v)
        return (cls, key, v if value is None else value, (fixture_key, None))

    def color_cycle(stub, fixture_key):
        vals = e.get(fixture_key) or []
        pcts = e.get(f"{fixture_key}_opacity") or [None] * len(vals)
        return [("color", f"p{i}{stub}",
                 _color_token(vals[i - 1], pcts[i - 1] if len(pcts) >= i else None),
                 (fixture_key, i))
                for i in range(1, N_PLOTS + 1) if len(vals) >= i]

    group(["Background and region colours."], [
        scalar("color", "background", "background_color"),
        scalar("color", "plotregion", "plotregion_color"),
        scalar("color", "legend", "legend_bg_color"),
        scalar("color", "legend_line", "legend_border_color"),
        scalar("color", "major_grid", "grid_color"),
        scalar("color", "minor_grid", "minor_grid_color"),
        scalar("color", "heading", "title_color"),
        scalar("color", "axisline", "axis_line_color"),
    ])
    group(["Generic grid colour (Stata: color grid), the parser's fallback when",
           "color major_grid is absent.  Checked where a file carries it, never",
           "appended."], [
        scalar("color", "grid", "grid_color_generic"),
    ], optional=True)
    # A p#stub cycle carries only the keys Stata's own #include chain
    # DECLARES -- the key its p#stub -> pstub -> p# -> p lookup stopped at
    # -- and SchemeParser follows the chain itself.  Writing the chain out
    # resolved, `color p1mark' and the rest, made the translation declare
    # keys Stata's file does not, so a user's `#include s2color' then
    # `color p1 red' reached a line plot and not a marker, a bar or a
    # connecting line, where Stata reaches all four (measured 24sep2026).
    seen: set = set()

    def declared_cycle(cls, stub, fixture_key, colour, conv=None,
                       numbered_only=False):
        vals = e.get(fixture_key) or []
        pcts = e.get(f"{fixture_key}_opacity") or [None] * len(vals)
        prov = (e.get("provenance") or {}).get(fixture_key) or []
        items = []
        for i in range(1, min(N_PLOTS, len(vals)) + 1):
            entry = prov[i - 1] if len(prov) >= i else None
            tokens = ((entry or {}).get("directive") or "").split()
            if len(tokens) != 2 or tokens[0] != cls:
                continue
            key = tokens[1]
            if cls == "color" and re.fullmatch(r"p\d+", key):
                continue    # the p# cycle above carries it
            if numbered_only and not re.fullmatch(r"p\d+", key):
                continue    # the bare `p' is written as a scalar
            if (cls, key) in seen:
                continue
            seen.add((cls, key))
            value = (_color_token(vals[i - 1],
                                  pcts[i - 1] if len(pcts) >= i else None)
                     if colour else vals[i - 1])
            if conv is not None:
                value = conv(value)
            items.append((cls, key, value, (fixture_key, i)))
        return items

    def chain_comment(cls, stub):
        return [f"Per-plot {cls} p#{stub}: only the keys this scheme's #include chain",
                f"declares.  SchemeParser resolves p#{stub} -> p{stub} -> p# -> p",
                "itself, as Stata's scheme.class does, so nothing is written for a",
                "step the chain does not declare."]

    group(["Per-plot colour cycle p# (Stata: color p#)."],
          color_cycle("", "p_colors"))
    for stub, key in (("line", "p_line_colors"), ("bar", "p_bar_colors"),
                      ("markfill", "p_mark_colors"),
                      ("markline", "p_markline_colors"),
                      ("label", "p_label_colors"),
                      ("lineplot", "p_lineplot_colors")):
        group(chain_comment("color", stub),
              declared_cycle("color", stub, key, True))
    # The marker symbols follow the same rule: style/markerstyle-p#.style
    # reads `symbol p#', which falls back to `symbol p'.  Spelling the
    # fallback out as `symbol p1'..`symbol p15' made a user's `#include
    # s2color' then `symbol p diamond' reach no plot, where Stata draws
    # every marker a diamond (measured 24sep2026, S3 batch).
    group(["Marker symbol cycle: only the keys this scheme's #include chain",
           "declares.  SchemeParser resolves symbol p# -> symbol p itself, as",
           "Stata's scheme.class does (style/markerstyle-p#.style: `set symbol",
           "scheme p#'), so nothing is written for a step the chain does not",
           "declare."],
          declared_cycle("symbol", "", "p_symbols", False))
    for stub, key in (("line", "p_line_patterns"),
                      ("lineplot", "p_lineplot_patterns")):
        group(chain_comment("linepattern", stub),
              declared_cycle("linepattern", stub, key, False))
    group(["Line widths (Stata linewidth style names)."], [
        scalar("linewidth", "p", "default_line_width", use_name=True),
        scalar("linewidth", "major_grid", "grid_line_width", use_name=True),
    ])
    group(["Bar and area outline widths (Stata: linewidth pbar, linewidth",
           "parea), only where this scheme's #include chain declares them.",
           "SchemeParser.plot_line_width resolves p#bar -> pbar (a bar stops",
           "there) and p#area -> parea -> p# -> p itself."], [
        scalar("linewidth", "pbar", "bar_line_width", use_name=True),
        scalar("linewidth", "parea", "area_line_width", use_name=True),
    ])
    group(["Fill intensities."], [
        scalar("intensity", "p", "fill_alpha", use_name=True),
    ])
    group(["A ci fit's band: areastyle ci (style/areastyle-ci.style) fills",
           "it in `color ci_area' at `intensity ci_area' and outlines it in",
           "`color ci_arealine' at `linewidth ci_area' and `linepattern",
           "ci_area'.  pstyle(ci2) reads `color ci2_area', `color",
           "ci2_arealine' and `linewidth ci2_area' and ci's other keys.",
           "pstyle(ci) and pstyle(ci2) draw the fit line in linestyle ci:",
           "`color ci_line', `linewidth ci', `linepattern ci'.  A width,",
           "intensity or pattern no file in the #include chain writes is",
           "Stata's class default, written here."], [
        scalar("color", "ci_area", "ci_area_color"),
        scalar("color", "ci_arealine", "ci_arealine_color"),
        scalar("intensity", "ci_area", "ci_area_alpha", use_name=True),
        scalar("linewidth", "ci_area", "ci_area_line_width", use_name=True),
        scalar("linepattern", "ci_area", "ci_area_pattern"),
        scalar("color", "ci_line", "ci_line_color"),
        scalar("linewidth", "ci", "ci_line_width", use_name=True),
        scalar("linepattern", "ci", "ci_pattern"),
        scalar("color", "ci2_area", "ci2_area_color"),
        scalar("color", "ci2_arealine", "ci2_arealine_color"),
        scalar("linewidth", "ci2_area", "ci2_area_line_width",
               use_name=True),
    ])
    group(["A histogram's style: shadestyle-histogram.style fills it in",
           "`color histogram' at `intensity histogram', and",
           "linestyle-histogram.style outlines it in `color histogram_line'",
           "at `linewidth histogram'.  twoway draws every histogram layer in",
           "it."], [
        scalar("color", "histogram", "histogram_color",
               value=_color_token(e.get("histogram_color"),
                                  e.get("histogram_color_opacity"))),
        scalar("color", "histogram_line", "histogram_line_color",
               value=_color_token(e.get("histogram_line_color"),
                                  e.get("histogram_line_color_opacity"))),
        scalar("intensity", "histogram", "histogram_intensity",
               use_name=True),
        scalar("linewidth", "histogram", "histogram_line_width",
               use_name=True),
    ])
    group(["A ci band's outline under pstyle(p#) (Stata: linewidth pother),",
           "only where this scheme's #include chain declares it.",
           "SchemeParser resolves p#other -> pother -> p# -> p itself."], [
        scalar("linewidth", "pother", "other_line_width", use_name=True),
    ])
    group(["Font sizes (Stata gsize style names, relative units)."], [
        scalar("gsize", "text", "text_size", use_name=True),
        scalar("gsize", "heading", "heading_size", use_name=True),
        scalar("gsize", "axis_title", "axis_title_size", use_name=True),
        scalar("gsize", "tick_label", "tick_label_size", use_name=True),
        scalar("gsize", "note", "note_size", use_name=True),
    ])
    group(["Graph dimensions, in inches."], [
        scalar("graphsize", "x", "graphsize_x"),
        scalar("graphsize", "y", "graphsize_y"),
    ])
    group(["twoway's default tick count and plot-region margin (WP-30 P1.3a)."], [
        scalar("numticks_g", "horizontal_major", "numticks_horizontal_major"),
        scalar("numticks_g", "vertical_major", "numticks_vertical_major"),
        scalar("margin", "twoway", "margin_twoway"),
    ])
    group(["Stata's margin ladder, the sizes plotregion(margin()) names",
           "(WP-30 P1.20b)."],
          [scalar("gsize", k, f"margin_ladder_{k}") for k in MARGIN_LADDER])
    group(["The dots of twoway dot (WP-31 B5b): markerstyle dots, its",
           "outline linestyle dotmark."], [
        scalar("color", "dots", "dots_color"),
        scalar("color", "dotmarkline", "dotmarkline_color"),
        scalar("symbol", "dots", "dots_symbol"),
        scalar("symbolsize", "dots", "dots_symbolsize", use_name=True),
        scalar("linewidth", "dotmark", "dotmark_line_width", use_name=True),
    ])
    group(["Marker size and legend placement."], [
        scalar("symbolsize", "p", "symbolsize", use_name=True),
        scalar("clockdir", "legend_position", "legend_position"),
        scalar("numstyle", "legend_cols", "legend_cols"),
    ])
    # style/markerstyle-p#.style: `set size scheme p#', falling back to the
    # `symbolsize p' above.  Only the `symbolsize p#' keys the chain
    # declares are written (s1manual's p1..p9), so a user's `symbolsize p'
    # reaches the plots Stata's reaches.
    group(["Per-plot marker size symbolsize p#: only the keys this scheme's",
           "#include chain declares.  SchemeParser resolves symbolsize p# ->",
           "symbolsize p itself (style/markerstyle-p#.style: `set size scheme",
           "p#'), as Stata's scheme.class does."],
          declared_cycle("symbolsize", "", "p_symbolsizes", False,
                         conv=name_of, numbered_only=True))
    group(["Marker-label size gsize p#label: only the keys this scheme's",
           "#include chain declares (style/textboxstyle-p#.style: set size",
           "scheme p#label)."],
          declared_cycle("gsize", "label", "p_label_sizes", False,
                         conv=name_of))
    group(["Major grid switches (effective per-axis values; see the minor-grid note)."], [
        scalar("yesno", "draw_major_hgrid", "draw_major_hgrid"),
        scalar("yesno", "draw_major_vgrid", "draw_major_vgrid"),
        scalar("yesno", "draw_major_grid", "draw_major_grid"),
    ])
    # --- the directives the first translation did not carry ---------------- #
    group(_grid_comment(e), [
        scalar("yesno", "draw_minor_hgrid", "draw_minor_hgrid"),
        scalar("yesno", "draw_minor_vgrid", "draw_minor_vgrid"),
        scalar("yesno", "draw_minor_grid", "draw_minor_grid"),
    ])
    group([
        "Text colours, one per textbox style: style/textboxstyle-<name>.style",
        "reads `color <name>'.  title() is heading (above), subtitle()",
        "subheading, caption() body, note() small_body, legend keys key_label,",
        "axis titles axis_title, tick labels tick_label.  `color text' and",
        "`color foreground' are the scheme's general text and foreground",
        "colours.",
    ], [
        scalar("color", "subheading", "subheading_color"),
        scalar("color", "body", "body_color"),
        scalar("color", "small_body", "small_body_color"),
        scalar("color", "text", "text_color"),
        scalar("color", "axis_title", "axis_title_color"),
        scalar("color", "tick_label", "tick_label_color"),
        scalar("color", "key_label", "key_label_color"),
        scalar("color", "foreground", "foreground_color"),
    ])
    group([
        "Text sizes, one per textbox style (Stata gsize style names; the",
        "fixture's _meta.units gives each name's relative value and its points",
        "at Stata's 4-inch reference).  note() is drawn with small_body: the",
        "`gsize note' line above is not the key Stata's note textbox reads.",
    ], [
        scalar("gsize", "subheading", "subheading_size", use_name=True),
        scalar("gsize", "body", "body_size", use_name=True),
        scalar("gsize", "small_body", "small_body_size", use_name=True),
        scalar("gsize", "key_label", "key_label_size", use_name=True),
    ])
    group(["Minor grid and axis line widths (Stata linewidth style names)."], [
        scalar("linewidth", "minor_grid", "minor_grid_line_width", use_name=True),
        scalar("linewidth", "axisline", "axis_line_width", use_name=True),
    ])
    group(["Legend rows; 0 means not fixed, so the column count above decides."], [
        scalar("numstyle", "legend_rows", "legend_rows"),
    ])

    # --- style-file indirections, carried as their EFFECTIVE values -------- #
    def drawn_color(prefix):
        """A line's colour token: #rrggbb, or `none' where Stata draws no
        line (economist's plot region)."""
        if e.get(f"{prefix}_drawn") is False:
            return "none"
        return e.get(f"{prefix}_color")

    group([
        "Reference lines, xline() and yline(): twoway draws them in the",
        "`gridlinestyle' class default, whose style file reads `linestyle",
        "xyline'; that linestyle reads these three keys.",
    ], [
        scalar("color", "xyline", "xyline_color", value=drawn_color("xyline")),
        scalar("linepattern", "xyline", "xyline_pattern"),
        scalar("linewidth", "xyline", "xyline_line_width", use_name=True),
        # WP-30 P1.21b: gridlinestyle-default's two ends.
        scalar("yesno", "xyline_extend_low", "xyline_extend_low"),
        scalar("yesno", "xyline_extend_high", "xyline_extend_high"),
    ])
    group([
        "The plot region's border, EFFECTIVE: plotregionstyle twoway ->",
        "areastyle twoway_plotregion -> its linestyle.  `none' where Stata",
        "draws no border; a scheme whose border is the foreground line",
        "(s1color) carries the foreground's colour and width here.",
    ], [
        scalar("color", "plotregion_line", "plotregion_line_color",
               value=drawn_color("plotregion_line")),
        scalar("linewidth", "plotregion", "plotregion_line_line_width",
               use_name=True),
        scalar("linepattern", "plotregion", "plotregion_line_pattern"),
    ])
    tb = e.get("note_textbox") or {}
    note_items = [("textboxstyle", "note", tb.get("name"),
                   ("note_textbox", None))]
    if tb.get("size_key"):
        note_items.append(scalar("gsize", tb["size_key"], "note_text_size",
                                 use_name=True))
    if tb.get("color_key"):
        note_items.append(scalar("color", tb["color_key"], "note_text_color"))
    if e.get("note_box_drawn") and tb.get("fill_key"):
        note_items.append(scalar("color", tb["fill_key"],
                                 "note_box_fill_color"))
    group([
        "note()'s text box (Stata: textboxstyle note) and the keys that box",
        "reads for its size, text colour and, where it draws a box, fill.",
    ], note_items)
    # WP-30 P1.24: the keys the remaining text box styles read, where the
    # scheme's chain sets them and no group above writes them already.
    have = {(c, k) for _cm, its, _op in groups for c, k, _v, _r in its}
    tb_items = []
    for k in TEXTBOX_KEYS:
        for cls, sfx, use_name in (("gsize", "size", True),
                                   ("color", "color", False)):
            if (cls, k) not in have:
                tb_items.append(scalar(cls, k, f"textbox_{k}_{sfx}",
                                       use_name=use_name))
    group([
        "Text sizes and colours of the remaining text box styles, read by",
        "mlabtextstyle() (WP-30 P1.24).",
    ], tb_items)

    # --- the chrome (WP-30 P1.2a) ------------------------------------------ #
    # Effective values of the keys Stata's chrome styles read:
    # style/ticksetstyle-major_*_default.style (`set tickangle scheme
    # horizontal_tick|vertical_tick'), style/gridstyle-major|minor.style
    # (`linestyle major_grid|minor_grid'), style/tickstyle-major.style
    # (`set length scheme tick', `set position scheme axis_tick', `set
    # linestyle scheme tick'), style/axisstyle-<name>.style (line and tick
    # flags), style/textboxstyle-heading|subheading|body|small_body.style
    # (`set horizontal scheme <name>'), and twoway's clockdir positions.
    if e.get("tick_angle_x") is not None:
        def nm(k):
            return name_of(e.get(k))
        cl = []
        for k, fk in (("horizontal_tick", "tick_angle_x"),
                      ("vertical_tick", "tick_angle_y")):
            cl.append(("anglestyle", k, nm(fk), (fk, None)))
        cl += [
            ("linepattern", "major_grid", nm("major_grid_pattern"),
             ("major_grid_pattern", None)),
            ("linepattern", "minor_grid", nm("minor_grid_pattern"),
             ("minor_grid_pattern", None)),
            ("color", "tick", e.get("tick_color") or "none",
             ("tick_color", None)),
            ("color", "minortick", e.get("minortick_color") or "none",
             ("minortick_color", None)),
            ("linewidth", "tick", nm("tick_line_width"),
             ("tick_line_width", None)),
            ("gsize", "tick", nm("tick_length"), ("tick_length", None)),
            ("tickposition", "axis_tick", e.get("tick_position"),
             ("tick_position", None)),
        ]
        styles = e.get("axis_styles") or {}
        for ax in ("x", "y", "x2", "y2"):
            f = styles.get(ax)
            if f:
                cl.append(("axisstyle", f["role"], f["axisstyle"],
                           (f"axis_style_{ax}", None)))
        for a in ("x", "y"):
            v = (e.get("alt_axes") or {}).get(a)
            if v is not None:
                cl.append(("yesno", f"alt_{a}axes", bool(v),
                           (f"alt_{a}axes", None)))
        for k in ("heading", "subheading", "body", "small_body"):
            cl.append(("horizontal", k, (e.get("justification") or {}).get(k),
                       (f"justification_{k}", None)))
        for k in ("title", "subtitle", "note", "caption"):
            cl.append(("clockdir", f"{k}_position",
                       (e.get("text_positions") or {}).get(k),
                       (f"text_position_{k}", None)))
        cl.append(("system", "naturally_white", e.get("naturally_white"),
                   ("naturally_white", None)))
        # p#bar/pbar/p#area/parea only where Stata's chain declares them
        # (none of the 26 does; each resolves to `intensity p').
        for stub in ("bar", "area"):
            provs = (e.get("provenance") or {}).get(f"p_{stub}_intensity") or []
            vals = e.get(f"p_{stub}_intensity") or []
            for i, (pv, v) in enumerate(zip(provs, vals), 1):
                d = ((pv or {}).get("directive") or "").split()
                if (len(d) == 2 and d[1] in (f"p{i}{stub}", f"p{stub}")
                        and (pv or {}).get("kind") == "transcribed"):
                    cl.append(("intensity", d[1], name_of(v),
                               (f"p_{stub}_intensity", i)))
        group(["The chrome (WP-30 P1.2a): tick-label angles, grid patterns, the",
               "tick's colour, width, length and side, each axis role's style,",
               "the alt-axis switches, the text boxes' justification and clock",
               "positions, and system naturally_white.  Effective values, read",
               "through style/ticksetstyle-*, gridstyle-*, tickstyle-major,",
               "axisstyle-* and textboxstyle-* as the plot-region group's are."],
              cl)
    group(["twoway's size for an msize() name it does not know: the bare",
           "symbolsize class default.  Checked where a file carries it, never",
           "appended."], [
        ("symbolsize", "", name_of(e.get("symbolsize_default")),
         ("symbolsize_default", None)),
    ], optional=True)

    # WP-30 P1.15c: by()'s shared axes, legend and colour key, and the
    # panel label's box.
    group(["by() axes and keys (WP-30 P1.15c): the legend's and colour key's",
           "clock position and ring under by(), the outer- and individual-axis",
           "switches, the space between panels, and the panel label's box:",
           "`color by_label_fill' is dash's derived key, the fillcolor of the",
           "style `textboxstyle subtitle' names, resolved."], [
        scalar("clockdir", "by_legend_position", "by_legend_position"),
        scalar("gridringstyle", "by_legend_ring", "by_legend_ring"),
        scalar("clockdir", "zyx2legend_position", "zyx2legend_position"),
        scalar("gridringstyle", "zyx2legend_ring", "zyx2legend_ring"),
        *[scalar("yesno", k, k) for k in BY_YESNO_KEYS],
        scalar("margin", "by_indiv", "by_indiv_margin"),
        scalar("margin", "subheading", "margin_subheading"),
        scalar("color", "bylabel_outline", "bylabel_outline_color"),
        scalar("color", "by_label_fill", "by_label_fill"),
    ])
    # WP-30 P1.10: text() and ttext()'s text box (`textboxstyle
    # text_option'); its size, colour, outline colour and line width are
    # carried by the groups above.
    group(["text() and ttext() (WP-30 P1.10): the text box's fill, its",
           "compass direction from its point, whether it is boxed, its",
           "margin, justification and vertical alignment."], [
        scalar("color", "text_option_fill", "text_option_fill"),
        scalar("compass2dir", "text_option", "text_option_placement"),
        scalar("yesno", "text_option", "text_option_box"),
        scalar("margin", "text_option", "text_option_margin"),
        scalar("horizontal", "text_option", "text_option_justification"),
        scalar("vertical_text", "text_option", "text_option_vertical"),
    ])
    # WP-30 P1.14b: the keys Stata's style files read for the named styles,
    # as the scheme declares them along scheme.class's chain; last, so a key
    # an earlier group carries is not carried twice.
    _nsd = e.get("named_style_directives") or {}
    group(["Named styles (WP-30 S36): the keys Stata's style files read for the",
           "named styles dash draws"],
          [(k.split(" ", 1)[0], k.split(" ", 1)[1], _nsd[k],
            (f"named_style_directives.{k}", None))
           for k in sorted(_nsd) if " " in k])

    # A directive an earlier group already carries is not carried twice
    # (note()'s small_body box is `gsize small_body' above).
    # An optional group (checked where a file carries it, never appended)
    # gives way to a later group that must carry the same key (WP-30
    # P1.14b: the named styles read `color grid').
    must = {(i[0], i[1].lower()) for _c, its, opt in groups if not opt
            for i in its}
    groups = [(c, [i for i in its if not opt
                   or (i[0], i[1].lower()) not in must], opt)
              for c, its, opt in groups]
    seen: set = set()
    out_groups = []
    for comment, items, optional in groups:
        kept = []
        for item in items:
            ck = (item[0], item[1].lower())
            if ck in seen:
                continue
            seen.add(ck)
            kept.append(item)
        if kept:
            out_groups.append((comment, kept, optional))
    return out_groups


#: Classes whose bare two-token class default a translation carries.
_BARE_CLASSES = frozenset({"symbolsize"})


def _file_directives(lines: list[str]) -> dict:
    """``(class, key) -> (line index, value)`` for every directive line."""
    out = {}
    for i, raw in enumerate(lines):
        line = raw.strip()
        if (not line or line.startswith("*") or line.startswith("#include")
                or line.startswith("label")):
            continue
        tokens = line.split()
        if len(tokens) == 2 and tokens[0].lower() in _BARE_CLASSES:
            # A bare class default (`symbolsize large').
            out[(tokens[0].lower(), "")] = (i, tokens[1])
            continue
        if len(tokens) < 3:
            continue
        out[(tokens[0].lower(), tokens[1].lower())] = (i, " ".join(tokens[2:]))
    return out


def _replace_value(line: str, value: str) -> str:
    """The same directive line with only its value token replaced."""
    head = line.rstrip()
    old = head.split()[-1]
    return head[: head.rfind(old)] + value


def _chain_text(name: str, e: dict) -> str:
    """The #include chain as root -> ... -> child, whichever way it is stored."""
    chain = list(e.get("include_chain") or [name])
    if chain and chain[0] == name and len(chain) > 1:
        chain.reverse()
    return " -> ".join(chain)


def _render_block(name: str, e: dict, groups, stamp: str,
                  created: bool = False) -> list[str]:
    if created:
        out = [
            _RULE,
            f"* Directives, written {stamp} by scripts/extract_scheme_truth.py (WP-17)",
            "* from test/fixtures/scheme_truth.json.  Every value is resolved from",
            "* Stata's own #include chain and style files (chain:",
            f"* {_chain_text(name, e)}); colours are pre-resolved #rrggbb, a %NN",
            "* suffix being Stata's opacity kept as written; a p#stub cycle carries",
            "* only the keys Stata's chain declares, which SchemeParser follows.",
            "* Re-running the script re-checks every directive here.",
            _RULE,
        ]
    else:
        out = [
            _RULE,
            f"* Added {stamp} by scripts/extract_scheme_truth.py (WP-16): directives",
            "* Stata consumes that the translation above did not carry.  Values are",
            "* resolved from the same Stata #include chain and style files as the",
            f"* rest of this file (chain: {_chain_text(name, e)}); colours are",
            "* pre-resolved #rrggbb.  Re-running the script re-checks every directive",
            "* in this file and appends only what is missing.",
            _RULE,
        ]
    for comment, items in groups:
        out.append("")
        out.extend("* " + c if c else "*" for c in comment)
        width = max(len(k) for _, k, _, _ in items)
        for cls, key, value, _ref in items:
            out.append(f"{cls} {key:<{width}}  {value}")
    return out


def _new_file_header(name: str, e: dict, stata_base: str, stamp: str) -> list[str]:
    chain = _chain_text(name, e)
    src = os.path.join(stata_base, "s", f"scheme-{name}.scheme")
    label = e.get("label") or name
    return [
        f"* {name}.scheme",
        _RULE,
        f"* dash translation of Stata's {name} scheme.",
        "*",
        f"* Source Stata scheme file : {src}",
        f"* Stata version            : {STATA_VERSION}",
        f"* Stata #include chain     : {chain}",
        f"* Translated on            : {stamp}",
        "* Derived from             : test/fixtures/scheme_truth.json, generated by",
        "*                            scripts/extract_scheme_truth.py from Stata's own",
        "*                            scheme-*.scheme and style/*.style files.",
        "*",
        "* Every colour below is a RESOLVED #rrggbb value, not a Stata colour name",
        "* (a %NN suffix is Stata's opacity, kept as the scheme writes it), and",
        "* a p#stub cycle carries only the keys Stata's own chain declares, since",
        "* SchemeParser follows p#stub -> pstub -> p# -> p itself.  The",
        "* provenance block at the end says, for every",
        "* directive, which Stata directive it was transcribed from or which",
        "* fallback rule inferred it.",
        "*",
        "* Re-extract and re-check this file whenever Stata is upgraded: the header",
        "* above is only true as of the version and date recorded in it.",
        _RULE,
        "",
        f'label "{label}"',
    ]


# --- the provenance block ---------------------------------------------------- #

def _provenance_text(entry: "dict | None") -> "str | None":
    """One directive's provenance, as the `* provenance:' line carries it."""
    if not entry:
        return None
    directive, value = entry.get("directive"), entry.get("value")
    spelled = f"`{directive} {value}'" if value is not None else f"`{directive}'"
    where = entry.get("file") or "?"
    if entry.get("line"):
        where += f":{entry['line']}"
    if entry.get("kind") == "transcribed":
        text = f"transcribed from {where} {spelled}"
        if entry.get("via"):
            text += f" via {entry['via']}"
        return text
    return f"inferred: {entry.get('rule') or 'no rule recorded'} ({where})"


def provenance_block(name: str, e: dict, groups, present: dict) -> "list[str] | None":
    """The `* provenance:' block for the directives the file carries.

    One line per directive, in the order of ``expected_directives``; a
    directive the file does not carry gets no line.  None when the fixture
    entry has no ``provenance`` map (an older fixture), so nothing is
    written.
    """
    prov = e.get("provenance")
    if not isinstance(prov, dict):
        return None
    lines = []
    for _comment, items, _optional in groups:
        for cls, key, _value, (fixture_key, index) in items:
            if (cls, key.lower()) not in present:
                continue
            entry = prov.get(fixture_key)
            if isinstance(entry, list):
                entry = entry[index - 1] if index and len(entry) >= index else None
            # The fixture calls a p#stub value "inferred" when Stata's chain
            # stopped at a shorter key (`color pline').  A directive that IS
            # that key was transcribed, not inferred.
            if (isinstance(entry, dict) and entry.get("kind") == "inferred"
                    and (entry.get("directive") or "").lower()
                    == (f"{cls} {key}" if key else cls).lower()):
                entry = dict(entry, kind="transcribed")
            text = _provenance_text(entry)
            if text is None:
                continue
            spelled = f"{cls} {key}" if key else cls
            lines.append(f"* provenance: {spelled} -- {text}")
    if not lines:
        return None
    return [
        _RULE,
        PROVENANCE_BEGIN,
        "* Where every directive above comes from, written by",
        "* scripts/extract_scheme_truth.py from the fixture's per-scheme `provenance'",
        "* map (one line per directive, in the order of the groups above).",
        "*   transcribed from <file>:<line> `<directive>'  a Stata scheme file in",
        f"*       this chain ({_chain_text(name, e)}) writes the very key this",
        "*       translation carries; the value is that directive's, resolved.",
        "*   inferred: <rule>  no Stata file writes the key dash reads; the value",
        "*       is what Stata itself falls back to -- the documented",
        "*       p#stub -> pstub -> p# -> p chain, a bare class default, the",
        "*       generic `color grid', or an axisstyle indirection.",
        "* Do not hand-edit this block: a re-run rewrites it in place when it",
        "* differs, and leaves it alone when it does not.",
        *lines,
        PROVENANCE_END,
        _RULE,
    ]


def _upsert_provenance(lines: list[str], block: list[str]) -> "str | None":
    """Write *block* into *lines*: replace an existing one only if it differs,
    append one otherwise.  Returns "written", "updated" or None (unchanged)."""
    if PROVENANCE_BEGIN in lines and PROVENANCE_END in lines:
        b = lines.index(PROVENANCE_BEGIN)
        e = lines.index(PROVENANCE_END)
        if e > b:
            start = b - 1 if b > 0 and lines[b - 1] == _RULE else b
            stop = e + 2 if e + 1 < len(lines) and lines[e + 1] == _RULE else e + 1
            if lines[start:stop] == block:
                return None
            lines[start:stop] = block
            return "updated"
    while lines and lines[-1] == "":
        lines.pop()
    lines.extend([""] + block)
    return "written"


def update_scheme_file(path: str, name: str, e: dict, stata_base: str,
                       stamp: str) -> dict:
    """Bring ``dash-<name>.scheme`` into line with fixture entry *e*.

    Returns ``{"changed": [...], "added": [...], "created": bool,
    "provenance": "written" | "updated" | None}`` describing what was
    written; an all-empty result means the file already agreed.
    """
    created = not os.path.exists(path)
    if created:
        lines = _new_file_header(name, e, stata_base, stamp)
    else:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().split("\n")
    groups = expected_directives(e)
    removed = _drop_undeclared_stubs(lines, groups)
    present = _file_directives(lines)
    changed, added, append_groups = [], [], []
    for comment, items, optional in groups:
        missing = []
        for cls, key, value, ref in items:
            hit = present.get((cls, key.lower()))
            if hit is None:
                if not optional:
                    missing.append((cls, key, value, ref))
                continue
            idx, old = hit
            if not _same(old, value):
                lines[idx] = _replace_value(lines[idx], value)
                changed.append(f"{cls} {key}: {old} -> {value}")
        if missing:
            append_groups.append((comment, missing))
            added.extend(f"{c} {k}" for c, k, _, _ in missing)
    if append_groups:
        if present:
            insert_at = max(i for i, _ in present.values()) + 1
        else:
            insert_at = len(lines)
        block = _render_block(name, e, append_groups, stamp, created=created)
        lines[insert_at:insert_at] = [""] + block
    # The provenance block describes what the file NOW carries.
    present = _file_directives(lines)
    block = provenance_block(name, e, groups, present)
    prov_state = _upsert_provenance(lines, block) if block else None
    if created or changed or added or removed or prov_state:
        text = "\n".join(lines)
        if not text.endswith("\n"):
            text += "\n"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    return {"changed": changed, "added": added, "removed": removed,
            "created": created, "provenance": prov_state}


#: The resolved p#stub keys an older translation wrote out p1..p15.
_STUB_KEY = {
    "color": re.compile(r"p\d+(line|bar|mark|markfill|markline|lineplot|label)"),
    "gsize": re.compile(r"p\d+label"),
    "linepattern": re.compile(r"p\d+(line|lineplot)"),
    "symbol": re.compile(r"p\d+"),
    "symbolsize": re.compile(r"p\d+"),
}

#: Directives the files no longer carry: graph bar's `intensity bar' and
#: `intensity area', which twoway's bar and area do not read (register
#: P1.2.8; WP-30 P1.4a).
_RETIRED_DIRECTIVES = {("intensity", "bar"), ("intensity", "area")}


def _drop_undeclared_stubs(lines: list[str], groups) -> list[str]:
    """Remove, in place, every ``color p#line|bar|mark|lineplot``,
    ``linepattern p#line|lineplot`` and ``symbol p#`` directive that
    *groups* does not expect
    -- the chain an older translation wrote out resolved -- and return
    them as ``"<class> <key>"``.  A paragraph (the lines between blank
    lines) left with no directive goes whole, its comment with it, since
    the comment described the lines removed.  A directive in
    ``_RETIRED_DIRECTIVES`` is removed and reported likewise."""
    expected = {(c, k.lower()) for _cm, items, _o in groups
                for c, k, _v, _r in items}
    present = _file_directives(lines)
    drop = {}
    for (cls, key), (idx, _old) in present.items():
        pat = _STUB_KEY.get(cls)
        if ((pat and pat.fullmatch(key) and (cls, key) not in expected)
                or (cls, key) in _RETIRED_DIRECTIVES):
            drop[idx] = f"{cls} {key}"
    if not drop:
        return []
    directive_at = {idx for idx, _v in present.values()}
    kill = set(drop)
    start = 0
    for end in range(len(lines) + 1):
        if end < len(lines) and lines[end].strip():
            continue
        para = range(start, end)
        ds = [i for i in para if i in directive_at]
        if ds and all(i in drop for i in ds):
            kill.update(para)
            if end < len(lines):
                kill.add(end)       # and one blank line after it
        start = end + 1
    lines[:] = [ln for i, ln in enumerate(lines) if i not in kill]
    return [drop[i] for i in sorted(drop)]


# --------------------------------------------------------------------------- #

# The twenty-six schemes StataCorp ships in BASE/s, every one of them.
# SchemeParser._BUILTIN_NAMES, test_scheme_fidelity.EXPECTED_SCHEMES and
# dash.ado's _dash_shipped_schemes must list exactly these;
# test_scheme_resolution.py checks all four agree.  The order is
# append-only: scheme_truth.json's key order follows it.
#: The scheme keys the shipped textboxstyle files read that no other
#: directive group carries (WP-30 P1.24; test/fixtures/
#: mlabtextstyle_truth.json's _meta.table).
#: WP-30 P1.15c: the yesno keys twoway's by() reads for its axes and
#: titles (scheme-s2color.scheme:2191-2210; bygraph_g.class).
BY_YESNO_KEYS = (
    "by_edgelabel", "by_outer_xaxes", "by_outer_yaxes", "by_outer_xtitles",
    "by_outer_ytitles", "by_indiv_xaxes", "by_indiv_yaxes",
    "by_indiv_xlabels", "by_indiv_ylabels", "by_indiv_xticks",
    "by_indiv_yticks", "by_indiv_xtitles", "by_indiv_ytitles",
    "by_indiv_as_whole")

TEXTBOX_KEYS = (
    "label", "small_label", "filled_text", "text_option", "reverse_big",
    "reverse_big_text", "matrix_label", "matrix_marklbl", "minortick_label",
    "tick_biglabel", "sts_risk_label", "sts_risk_title", "fpbody",
    "fpcoltitle", "fpnulllefttext", "fpnullrighttext", "fpspacer",
    "pbarlabel", "pboxlabel",
)

SCHEMES = [
    "stcolor", "stcolor_alt", "stgcolor", "stmono1", "stmono2", "stsj",
    "s2color", "s2mono", "s2gcolor", "s1color", "s1mono", "s1rcolor",
    "economist", "sj",
    # WP-17: the six that were missing.
    "s2manual", "s1manual", "s2gmanual", "s2color8", "sttrans", "stgcolor_alt",
    # WP-30 P1.25a: StataCorp's six internal schemes, measured in twoway
    "meta", "stcolor_meta", "stcolor_mv", "stcoloralias", "stgcolor_meta",
    "stgcolor_mv",
]

# A scheme name is a plain token.  --schemes names reach os.path.join as
# "dash-<name>.scheme", so anything else (a "/" or "..") could write
# outside --schemes-dir; Stata's 26 names all match.
_SCHEME_TOKEN_RE = re.compile(r"^[a-z0-9_]{1,32}$")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stata-base", default=DEFAULT_STATA_BASE,
                    help="Stata ado/base directory (default: %(default)s)")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--schemes", nargs="*", default=SCHEMES)
    ap.add_argument("--schemes-dir", default=DEFAULT_SCHEMES_DIR,
                    help="directory of dash's translated <name>.scheme files "
                         "to update from the fixture (default: %(default)s)")
    ap.add_argument("--no-scheme-files", action="store_true",
                    help="write the fixture only; leave dash-*.scheme alone")
    args = ap.parse_args(argv)
    for name in args.schemes:
        if not _SCHEME_TOKEN_RE.match(name):
            sys.stderr.write(
                "error: --schemes takes scheme names (a-z, 0-9, _; at most "
                f"32), got: {repr(name)[:80]}\n")
            return 2

    base = args.stata_base
    if not os.path.isdir(os.path.join(base, "s")):
        sys.stderr.write(f"error: no scheme directory under {base}\n")
        return 2

    ladders = unit_ladders(SchemeResolver(base))
    stamp = datetime.date.today().strftime("%d%b%Y").lower()

    doc: dict = {
        "_meta": {
            "generated_by": "scripts/extract_scheme_truth.py",
            "do_not_hand_edit": (
                "This file is GENERATED ground truth extracted from Stata's own "
                "scheme and style files. Regenerate it by re-running "
                "scripts/extract_scheme_truth.py; do not hand-edit."
            ),
            "generated_utc": datetime.datetime.now(
                datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stata_version": STATA_VERSION,
            "scheme_dir": os.path.join(base, "s"),
            "style_dir": os.path.join(base, "style"),
            "also_identical_in": "/Applications/Stata/ado/base "
                                 "(byte-identical scheme-*.scheme and style files)",
            "n_plots": N_PLOTS,
            "fallback_chain": "p#stub -> pstub -> p# -> p",
            "lineplot_vs_line": (
                "Stata keeps two per-plot line stubs apart: 'p#line' is the "
                "connecting line of twoway connected, while 'p#lineplot' is the "
                "line twoway line itself draws. They are NOT interchangeable: "
                "under s2mono, 'linepattern p#line' resolves to the inherited "
                "'linepattern p solid' while 'linepattern p#lineplot' is "
                "solid/dash/vshortdash/..., so three overlaid twoway line plots "
                "are drawn with three different dashes. Only the s2mono branch "
                "(s2mono, s2manual, s2gmanual, stmono2, stsj, sj) declares any "
                "lineplot key, and only s2mono and s2gmanual write one "
                "themselves; for every other scheme p_lineplot_* is the "
                "p#stub->pstub->p#->p "
                "fallback result, not something the scheme wrote. "
                "'lineplot_declared' records which case a scheme is in, per "
                "class, so a translation can tell an inherited value from a "
                "declared one instead of presenting the two alike. "
                "The indirection is in Stata's own style files: "
                "style/seriesstyle-p#line.style points a line plot's line at "
                "linestyle p#line, and style/linestyle-p#line.style then sets "
                "width/color/pattern from 'scheme p#lineplot' -- whereas "
                "style/linestyle-p#.style (the connected-plot linestyle) sets "
                "color/pattern from 'scheme p#line'. Stata documents the three "
                "keys in scheme_line_plots.sthlp, and scheme_line_plots.sthlp "
                "plus scheme_shared_plots.sthlp give the fallback: a scheme "
                "without the line-plot-specific entries uses the entries shared "
                "among all plottypes, namely 'color p#' and 'linepattern p' -- "
                "NOT 'linepattern p#line', which is a different stub."
            ),
            "intensity_multiplier_rule": (
                "f<=1: c' = round(255-(255-c)*f); f>1: c' = round(c/f); "
                "clamp [0,255]; round half away from zero. Verified empirically "
                "against Stata 19.5 SVG export over 24 colour/multiplier cases."
            ),
            "color_none": "Stata colour 'none' is emitted as JSON null.",
            "label": "Per-scheme 'label' is Stata's own `label \"...\"' line.",
            "directive_value": (
                "Stata's scheme.class setscheme reads a directive with "
                "`tokenize' then `args style id stylename': the value is the "
                "THIRD token, a double-quoted string is one token, and "
                "anything after the value is ignored -- scheme-sttrans.scheme's "
                "`symbolsize p small *medium' is `small' (measured: its marker "
                "radius in an SVG export equals s2color's msize(small)). The "
                "resolver tokenises the same way."
            ),
            "opacity": (
                "A colour token's %NN suffix is Stata's opacity (0-100). It is "
                "recorded beside the hex it belongs to, per plot, in "
                "p_colors_opacity, p_line_colors_opacity, p_bar_colors_opacity, "
                "p_mark_colors_opacity and p_lineplot_colors_opacity (None when "
                "the scheme writes none); the hex lists stay plain #rrggbb. Only "
                "sttrans uses one (every p# colour is \"r g b %20\"). A scalar "
                "colour with an opacity suffix has no slot and is reported in "
                "'unresolvable' rather than dropped."
            ),
            "provenance": (
                "Per-scheme 'provenance' parallels 'sources': for every extracted "
                "key (one record per index for the p# cycles) {kind, directive, "
                "value, file, line[, rule][, via]}. kind 'transcribed': a Stata "
                "scheme file in the #include chain writes the very key the "
                "translation carries, and file:line is that directive (via names "
                "an axisstyle indirection, or the style file a grid literal came "
                "from). kind 'inferred': no file writes the key dash reads; the "
                "value is what Stata itself falls back to -- the documented "
                "p#stub -> pstub -> p# -> p chain, a bare class default, or the "
                "generic `color grid' -- and 'rule' says which. The shipped "
                "dash-<name>.scheme files carry the same as `* provenance:' "
                "lines between `* BEGIN provenance (WP-17)' and `* END "
                "provenance (WP-17)', one per directive."
            ),
            "grid_color_generic": (
                "Stata's `color grid', the generic fallback SchemeParser reads "
                "when a file has no `color major_grid'. Optional in the shipped "
                "files: checked and given provenance where a file carries it "
                "(s2color, sj), never appended."
            ),
            "sources": (
                "Per-scheme 'sources' records, for every extracted property, the "
                "exact '<class> <key>' directive that supplied the value after "
                "the #include chain and the p#stub->pstub->p#->p fallback were "
                "applied. '<class-default>' means the value came from a bare "
                "two-token class default line (e.g. 'intensity full'), not from "
                "a named key. Notably no Stata base scheme sets 'intensity "
                "area', so area_alpha always resolves to the intensity class "
                "default."
            ),
            "units": {
                "graphsize_x/graphsize_y": "inches",
                "*_size.value": (
                    "Stata relative size units (sztype gives the kind); "
                    "pt_at_4in is that value in points on Stata's 4-inch "
                    "reference graph"),
                "default_line_width/grid_line_width.value": (
                    "Stata linewidth units, the same relative size; "
                    "pt_at_4in likewise"),
                "*_alpha.pct": "percent as written in the scheme; alpha = pct/100",
                "legend_position": "clock direction (0-12)",
                "legend_cols/legend_rows": "integers; 0 rows = not fixed",
                "relative_size": {
                    "definition": (
                        "help size: 'relative size, where size 100 = minimum "
                        "of width and height of graph'; every official "
                        "gsize-/symbolsize-*.style sets sztype relative, and "
                        "linewidthstyle's numeric form is the same unit"),
                    "formula_pt": (
                        "pt = value / 100 * min(graphsize x, graphsize y) "
                        "[inches] * 72"),
                    "reference_min_dimension_in": REFERENCE_MIN_DIMENSION_IN,
                    "pt_per_unit_at_4in": PT_PER_UNIT_AT_REFERENCE,
                    "note": (
                        "pt_at_4in figures use Stata's 4-inch reference "
                        "(s2color is 5.5 x 4in); at a scheme's own graphsize "
                        "multiply by min(x, y) / 4"),
                },
                "gsize": {
                    "unit": "relative size (text height)",
                    "dash_rule": (
                        "a numeric gsize is pt = value * 2.88 (the 4-inch "
                        "reference), written f'{pt:g}pt' with no minimum and "
                        "no truncation; a keyword takes its pt_at_4in below"),
                    "no_style_file": [k for k, v in ladders["gsize"].items()
                                      if v is None] + ["ehuge"],
                    "ladder": ladders["gsize"],
                },
                "symbolsize": {
                    "unit": "relative size (marker diameter, outline excluded)",
                    "dash_rule": (
                        "a keyword takes its pt_at_4in below; a numeric "
                        "symbolsize is pt = value * 2.88; pixels anchor "
                        "medium (4.4pt) at 8px, i.e. px = pt * 8 / 4.4"),
                    "not_the_gsize_ladder": (
                        "large/medium = 1.59 here vs 1.27 for gsize; "
                        "small/medium = 0.68 vs 0.73"),
                    "ladder": ladders["symbolsize"],
                },
                "linewidth": {
                    "unit": "relative size (help linewidthstyle)",
                    "dash_rule": (
                        "a linewidth keyword or number is Stata units, "
                        "px = max(units x 2.88, 0.3) x 4/3 (WP-30 P1.12b)"),
                    "ladder": ladders["linewidth"],
                },
            },
            "grid_switches": (
                "draw_major_hgrid/draw_minor_hgrid (x axis, the vertical lines "
                "at the x ticks) and draw_major_vgrid/draw_minor_vgrid (y axis, "
                "the horizontal lines) are EFFECTIVE values: twoway builds the "
                "x axis with axisstyle horizontal_default and the y axis with "
                "axisstyle vertical_default, the scheme maps each role to a "
                "style name, and style/axisstyle-<name>.style names the yesno "
                "key that is read. Per-scheme 'grid_axes' records that chain "
                "and 'sources' the key that supplied each value (economist's y "
                "axis: draw_major_nlt_vgrid / draw_minor_nlt_vgrid via "
                "vertical_nolinetick). draw_major_grid/draw_minor_grid are the "
                "bare keys as transcribed; no style file reads them."
            ),
            "textbox_styles": {
                "title()": {"style": "heading", "size": "gsize heading",
                            "color": "color heading"},
                "subtitle()": {"style": "subheading", "size": "gsize subheading",
                               "color": "color subheading"},
                "caption()": {"style": "body", "size": "gsize body",
                              "color": "color body"},
                "note()": {"style": "small_body", "size": "gsize small_body",
                           "color": "color small_body",
                           "note": "Stata's note textbox does not read gsize "
                                   "note; the box is the scheme's "
                                   "`textboxstyle note' (small_body in "
                                   "s2color, reverse_big in economist, "
                                   "key_label in s1manual), resolved per "
                                   "scheme in note_textbox, note_text_size, "
                                   "note_text_color and note_box_fill_color"},
                "xline()/yline()": {
                    "style": "linestyle xyline",
                    "note": "the gridlinestyle class default's style file "
                            "reads `linestyle xyline'; resolved per scheme "
                            "in xyline_color, xyline_pattern and "
                            "xyline_line_width"},
                "plot region border": {
                    "style": "areastyle twoway_plotregion",
                    "note": "plotregionstyle twoway -> areastyle "
                            "twoway_plotregion -> its linestyle; resolved "
                            "per scheme in plotregion_line_drawn, "
                            "plotregion_line_color, "
                            "plotregion_line_line_width and "
                            "plotregion_line_pattern"},
                "legend keys": {"style": "key_label", "size": "gsize key_label",
                                "color": "color key_label"},
                "axis titles": {"style": "axis_title", "size": "gsize axis_title",
                                "color": "color axis_title"},
                "tick labels": {"style": "tick_label", "size": "gsize tick_label",
                                "color": "color tick_label"},
                "source": "style/textboxstyle-<name>.style: set size scheme "
                          "<name>; set color scheme <name>",
            },
        }
    }

    for s in args.schemes:
        doc[s] = extract(base, s)
    # WP-30 P1.14b: the style table, the known names and each scheme's
    # declared hops (D-36h), for test_scheme_fidelity.py and SchemeParser.
    _r = SchemeResolver(base)
    doc["_meta"]["style_files"] = style_table(_r)
    doc["_meta"]["style_known"] = style_known(_r)
    doc["_meta"]["style_hops"] = {s: doc[s].pop("style_hops")
                                  for s in args.schemes}

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    sys.stderr.write(f"wrote {args.out} ({len(args.schemes)} schemes)\n")

    if args.no_scheme_files:
        return 0
    for s in args.schemes:
        path = os.path.join(args.schemes_dir, f"dash-{s}.scheme")
        result = update_scheme_file(path, s, doc[s], base, stamp)
        for line in result["changed"]:
            sys.stderr.write(f"{path}: CHANGED {line}\n")
        if result["created"]:
            sys.stderr.write(f"{path}: created\n")
        elif result["added"]:
            sys.stderr.write(
                f"{path}: added {len(result['added'])} directive(s): "
                + ", ".join(result["added"]) + "\n")
        if result.get("provenance") and not result["created"]:
            sys.stderr.write(f"{path}: provenance {result['provenance']}\n")
        if not (result["created"] or result["added"] or result["changed"]
                or result.get("provenance")):
            sys.stderr.write(f"{path}: up to date\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
