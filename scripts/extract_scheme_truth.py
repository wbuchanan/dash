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
are written from -- and it then brings those fourteen files
(``schemes/<name>.scheme``) up to date with it: every directive the fixture pins
is checked against the file, a value that disagrees is corrected on its own
line and reported, and a directive the file lacks is appended in a dated block
after the file's last directive.  The files' hand-written provenance comments
are left untouched, and a second run changes nothing.

GRID SWITCHES ARE RECORDED AS *EFFECTIVE* PER-AXIS VALUES
---------------------------------------------------------
twoway builds its x axis with ``axisstyle horizontal_default`` and its y axis
with ``axisstyle vertical_default``.  The scheme maps each of those roles to a
style name, and ``style/axisstyle-<name>.style`` then names the ``yesno`` key
that is actually read (``set draw_major_grid scheme draw_major_hgrid``).  For
thirteen schemes the roles map to themselves, so the keys are
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
        --out test/fixtures/scheme_truth.json          # also updates schemes/*.scheme
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
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

DEFAULT_STATA_BASE = "/Applications/StataNow/ado/base"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SCHEMES_DIR = os.path.join(REPO_ROOT, "schemes")

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
    """

    def __init__(self, stata_base: str):
        self.stata_base = stata_base
        self.scheme_dir = os.path.join(stata_base, "s")
        self.style_dir = os.path.join(stata_base, "style")
        # (class, key) -> value.  key "" is the class-level default.
        self.settings: dict[tuple[str, str], str] = {}
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
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("*"):
                    continue
                if line.startswith("#include"):
                    parts = line.split()
                    if len(parts) >= 2:
                        # Parent is applied HERE, so anything below this line in
                        # the child file overwrites it.  Last write wins.
                        self._load(parts[1], stack, depth + 1)
                    continue
                # Drop a trailing inline comment introduced by " *" ... Stata
                # schemes do not use those, so we deliberately do NOT strip
                # anything that could be part of a value (e.g. "navy*0.5").
                tokens = line.split()
                if len(tokens) < 2:
                    continue
                cls = tokens[0]
                if len(tokens) == 2:
                    # Class-level default, e.g. "intensity full".
                    self.settings[(cls, "")] = tokens[1]
                else:
                    self.settings[(cls, tokens[1])] = " ".join(tokens[2:])

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


def _round_half_up(x: float) -> int:
    return int(Decimal(repr(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _apply_intensity(rgb: tuple[int, int, int], f: float) -> tuple[int, int, int]:
    """Stata's ``colorstyle*#`` intensity adjustment.

    Empirically verified against Stata 19.5 SVG output (see module docstring):
    f <= 1 blends towards white, f > 1 scales towards black.
    """
    out = []
    for c in rgb:
        if f <= 1.0:
            v = 255.0 - (255.0 - c) * f
        else:
            v = c / f
        out.append(max(0, min(255, _round_half_up(v))))
    return tuple(out)  # type: ignore[return-value]


class ColorResolver:
    """Turns a scheme colour token into ``#rrggbb`` (or None for ``none``)."""

    def __init__(self, resolver: SchemeResolver):
        self.r = resolver
        self.unresolved: list[str] = []

    def resolve(self, token: str | None, _depth: int = 0) -> str | None:
        if token is None:
            return None
        tok = token.strip().strip('"').strip()
        if not tok or _depth > 8:
            return None

        # Opacity suffix (%NN) is recorded separately; strip it for the hex.
        opacity = None
        if "%" in tok:
            tok, _, op = tok.partition("%")
            opacity = op

        # Intensity multiplier (*N).
        mult = None
        if "*" in tok:
            base, _, m = tok.partition("*")
            tok = base
            try:
                mult = float(m)
            except ValueError:
                self.unresolved.append(
                    f"unparseable intensity multiplier in colour token {token!r}"
                )
                mult = None

        tok = tok.strip()
        low = tok.lower()

        if low == "none":
            # color-none.style carries "0 0 0" but its own comment says the
            # values should not matter: 'none' means "do not draw".
            return None

        rgb: tuple[int, int, int] | None = None

        if _RGB_LITERAL.match(tok):
            parts = [int(p) for p in tok.split()]
            rgb = (parts[0], parts[1], parts[2])
        elif low in ("background", "bg"):
            return self.resolve(self.r.get("color", "background"), _depth + 1)
        elif low in ("foreground", "fg"):
            return self.resolve(self.r.get("color", "foreground"), _depth + 1)
        else:
            st = self.r.style("color", low)
            if st and "rgb" in st:
                parts = st["rgb"].split()
                if len(parts) == 3:
                    rgb = (int(parts[0]), int(parts[1]), int(parts[2]))

        if rgb is None:
            self.unresolved.append(f"unknown colour token {token!r}")
            return None

        if mult is not None:
            rgb = _apply_intensity(rgb, mult)

        hexval = "#%02x%02x%02x" % rgb
        if opacity is not None:
            # Recorded, not folded into the hex; no scheme key we extract uses
            # one today, but flag it rather than silently dropping it.
            self.unresolved.append(
                f"opacity suffix %{opacity} on colour token {token!r} not folded "
                f"into hex"
            )
        return hexval


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


# --------------------------------------------------------------------------- #
# Per-scheme extraction
# --------------------------------------------------------------------------- #

def extract(stata_base: str, scheme: str) -> dict:
    r = SchemeResolver(stata_base)
    r.load(scheme)
    c = ColorResolver(r)
    unresolvable: list[str] = []
    # Provenance: output key -> the "<class> <key>" directive that actually
    # supplied the value, or "<class> <class-default>" when the value came from
    # a bare two-token class default line rather than a named key.
    sources: dict[str, object] = {}

    def getsrc(cls: str, keys: list[str], class_default: bool):
        """First matching key in ``keys``; returns (value, provenance string)."""
        for k in keys:
            v = r.get(cls, k, class_default=False)
            if v is not None:
                return v, f"{cls} {k}"
        if class_default:
            v = r.settings.get((cls, ""))
            if v is not None:
                return v, f"{cls} <class-default>"
        return None, None

    def color_of(out_key: str, keys: list[str]):
        tok, src_s = getsrc("color", keys, class_default=False)
        if tok is None:
            unresolvable.append(
                f"{out_key}: none of [" + ", ".join("color " + k for k in keys)
                + "] is set anywhere in the #include chain")
            sources[out_key] = None
            return None
        sources[out_key] = src_s
        return c.resolve(tok)

    # --- the p1..p15 cycle, with Stata's p#stub -> pstub -> p# -> p chain --- #
    def p_chain(cls: str, n: int, stub: str = ""):
        keys = []
        if stub:
            keys += [f"p{n}{stub}", f"p{stub}"]
        keys += [f"p{n}", "p"]
        return getsrc(cls, keys, class_default=False)

    def p_series(out_key, cls, stub, conv):
        vals, srcs = [], []
        for i in range(1, N_PLOTS + 1):
            tok, s = p_chain(cls, i, stub)
            if tok is None:
                unresolvable.append(
                    f"{out_key}[{i}]: no value for p{i}{stub} and no fallback")
            vals.append(conv(tok))
            srcs.append(s)
        sources[out_key] = srcs
        return vals

    p_colors = p_series("p_colors", "color", "", c.resolve)
    p_line_colors = p_series("p_line_colors", "color", "line", c.resolve)
    p_bar_colors = p_series("p_bar_colors", "color", "bar", c.resolve)
    p_mark_colors = p_series("p_mark_colors", "color", "mark", c.resolve)
    p_symbols = p_series("p_symbols", "symbol", "", lambda t: t)
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
    # schemes declares any ``lineplot`` key; everywhere else these resolve
    # through the ordinary p#stub -> pstub -> p# -> p fallback, which is why
    # ``lineplot_declared`` below is recorded separately: it says whether the
    # value was WRITTEN by a scheme or merely INHERITED by fallback, and a
    # translation must not present the second as though it were the first.
    p_lineplot_colors = p_series("p_lineplot_colors", "color", "lineplot",
                                 c.resolve)
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

    def scalar(out_key, cls, keys, conv, class_default=True):
        tok, s = getsrc(cls, keys, class_default=class_default)
        sources[out_key] = s
        if tok is None:
            unresolvable.append(
                f"{out_key}: none of [" + ", ".join(f"{cls} {k}" for k in keys)
                + "] set and no class default")
            return None
        return conv(tok)

    # --- graph size: "graphsize x" / "graphsize y", then bare "graphsize" --- #
    def graphsize(axis):
        tok, s = getsrc("graphsize", [axis], class_default=True)
        sources[f"graphsize_{axis}"] = s
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
                return None
            sources[out_key] = f"{info['style_file']}: set draw_{which}_grid {lit}"
            return lit
        tok = r.get("yesno", key, class_default=False)
        if tok is None:
            unresolvable.append(
                f"{out_key}: yesno {key} (named by {info['style_file']}) is "
                "not set anywhere in the #include chain")
            sources[out_key] = None
            return None
        via = ""
        if info["axisstyle"].lower() != info["role"]:
            via = (f" (via axisstyle {info['role']} = {info['axisstyle']}, "
                   f"{info['style_file']})")
        sources[out_key] = f"yesno {key}{via}"
        return tok.strip()

    out = {
        # root -> ... -> child: the order the directives are applied, the
        # child's last.  (The resolver opens the files child-first.)
        "include_chain": list(reversed(r.include_chain)),
        "p_colors": p_colors,
        "p_line_colors": p_line_colors,
        "p_bar_colors": p_bar_colors,
        "p_mark_colors": p_mark_colors,
        "p_symbols": p_symbols,
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
            lambda t: resolve_linewidth(r, t), class_default=True),
        "minor_grid_line_width": scalar(
            "minor_grid_line_width", "linewidth", ["minor_grid"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        "axis_line_width": scalar(
            "axis_line_width", "linewidth", ["axisline"],
            lambda t: resolve_linewidth(r, t), class_default=True),

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

        "graphsize_x": graphsize("x"),
        "graphsize_y": graphsize("y"),
        "symbolsize": scalar("symbolsize", "symbolsize", ["p"],
                             lambda t: resolve_sized(r, "symbolsize", t)),

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

    out["sources"] = sources

    # Anything that came back None because a token could not be resolved.
    for msg in c.unresolved:
        if msg not in unresolvable:
            unresolvable.append(msg)
    out["unresolvable"] = unresolvable
    return out


# --------------------------------------------------------------------------- #
# The translated scheme files (schemes/<name>.scheme)
# --------------------------------------------------------------------------- #
#
# A translated file is Stata's own one-directive-per-line grammar with every
# colour pre-resolved to #rrggbb and the p#stub -> pstub -> p# -> p fallback
# flattened into explicit p1..p15 lines, because SchemeParser reads by exact
# key.  The files carry hand-written provenance comments, so they are UPDATED
# IN PLACE rather than rewritten: every directive the fixture pins is checked
# against the file; a directive whose value disagrees is corrected on its own
# line and reported on stderr; a directive the file lacks is appended, in a
# dated block, after the file's last directive.  A second run changes nothing.

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


def expected_directives(e: dict) -> "list[tuple[list[str], list[tuple[str, str, str]]]]":
    """The directives a translated file must carry for fixture entry *e*.

    Returns ordered groups ``(comment_lines, [(class, key, value), ...])``;
    the comment is written above the group when any of it has to be appended.
    A ``None`` value (Stata colour ``none``, or an unresolvable entry) is
    skipped rather than written.
    """
    groups: list = []

    def group(comment, items):
        items = [(c, k, _fmt(v)) for c, k, v in items if v is not None]
        if items:
            groups.append((comment, items))

    def name_of(spec):
        return (spec or {}).get("name")

    group(["Background and region colours."], [
        ("color", "background", e.get("background_color")),
        ("color", "plotregion", e.get("plotregion_color")),
        ("color", "legend", e.get("legend_bg_color")),
        ("color", "legend_line", e.get("legend_border_color")),
        ("color", "major_grid", e.get("grid_color")),
        ("color", "minor_grid", e.get("minor_grid_color")),
        ("color", "heading", e.get("title_color")),
        ("color", "axisline", e.get("axis_line_color")),
    ])
    for stub, key in (("", "p_colors"), ("line", "p_line_colors"),
                      ("bar", "p_bar_colors"), ("mark", "p_mark_colors")):
        vals = e.get(key) or []
        group([f"Per-plot colour cycle p#{stub} (Stata's p#stub -> pstub -> p# -> p chain, flattened)."],
              [("color", f"p{i}{stub}", vals[i - 1]) for i in range(1, N_PLOTS + 1)
               if len(vals) >= i])
    decl = e.get("lineplot_declared") or {}
    if decl.get("color"):
        vals = e.get("p_lineplot_colors") or []
        group(["Per-plot `twoway line' colour (Stata: color p#lineplot; declared by this chain)."],
              [("color", f"p{i}lineplot", vals[i - 1]) for i in range(1, N_PLOTS + 1)
               if len(vals) >= i])
    vals = e.get("p_symbols") or []
    group(["Marker symbol cycle."],
          [("symbol", f"p{i}", vals[i - 1]) for i in range(1, N_PLOTS + 1)
           if len(vals) >= i])
    vals = e.get("p_line_patterns") or []
    group(["Line patterns of the connecting line (Stata: linepattern p#line)."],
          [("linepattern", f"p{i}line", vals[i - 1]) for i in range(1, N_PLOTS + 1)
           if len(vals) >= i])
    if decl.get("linepattern"):
        vals = e.get("p_lineplot_patterns") or []
        group(["Line patterns of `twoway line' (Stata: linepattern p#lineplot; declared by this chain)."],
              [("linepattern", f"p{i}lineplot", vals[i - 1])
               for i in range(1, N_PLOTS + 1) if len(vals) >= i])
    group(["Line widths (Stata linewidth style names)."], [
        ("linewidth", "p", name_of(e.get("default_line_width"))),
        ("linewidth", "major_grid", name_of(e.get("grid_line_width"))),
    ])
    group(["Fill intensities."], [
        ("intensity", "p", name_of(e.get("fill_alpha"))),
        ("intensity", "bar", name_of(e.get("bar_alpha"))),
        ("intensity", "area", name_of(e.get("area_alpha"))),
    ])
    group(["Font sizes (Stata gsize style names, relative units)."], [
        ("gsize", "text", name_of(e.get("text_size"))),
        ("gsize", "heading", name_of(e.get("heading_size"))),
        ("gsize", "axis_title", name_of(e.get("axis_title_size"))),
        ("gsize", "tick_label", name_of(e.get("tick_label_size"))),
        ("gsize", "note", name_of(e.get("note_size"))),
    ])
    group(["Graph dimensions, in inches."], [
        ("graphsize", "x", e.get("graphsize_x")),
        ("graphsize", "y", e.get("graphsize_y")),
    ])
    group(["Marker size and legend placement."], [
        ("symbolsize", "p", name_of(e.get("symbolsize"))),
        ("clockdir", "legend_position", e.get("legend_position")),
        ("numstyle", "legend_cols", e.get("legend_cols")),
    ])
    group(["Major grid switches (effective per-axis values; see the minor-grid note)."], [
        ("yesno", "draw_major_hgrid", e.get("draw_major_hgrid")),
        ("yesno", "draw_major_vgrid", e.get("draw_major_vgrid")),
        ("yesno", "draw_major_grid", e.get("draw_major_grid")),
    ])
    # --- the directives the first translation did not carry ---------------- #
    group(_grid_comment(e), [
        ("yesno", "draw_minor_hgrid", e.get("draw_minor_hgrid")),
        ("yesno", "draw_minor_vgrid", e.get("draw_minor_vgrid")),
        ("yesno", "draw_minor_grid", e.get("draw_minor_grid")),
    ])
    group([
        "Text colours, one per textbox style: style/textboxstyle-<name>.style",
        "reads `color <name>'.  title() is heading (above), subtitle()",
        "subheading, caption() body, note() small_body, legend keys key_label,",
        "axis titles axis_title, tick labels tick_label.  `color text' and",
        "`color foreground' are the scheme's general text and foreground",
        "colours.",
    ], [
        ("color", "subheading", e.get("subheading_color")),
        ("color", "body", e.get("body_color")),
        ("color", "small_body", e.get("small_body_color")),
        ("color", "text", e.get("text_color")),
        ("color", "axis_title", e.get("axis_title_color")),
        ("color", "tick_label", e.get("tick_label_color")),
        ("color", "key_label", e.get("key_label_color")),
        ("color", "foreground", e.get("foreground_color")),
    ])
    group([
        "Text sizes, one per textbox style (Stata gsize style names; the",
        "fixture's _meta.units gives each name's relative value and its points",
        "at Stata's 4-inch reference).  note() is drawn with small_body: the",
        "`gsize note' line above is not the key Stata's note textbox reads.",
    ], [
        ("gsize", "subheading", name_of(e.get("subheading_size"))),
        ("gsize", "body", name_of(e.get("body_size"))),
        ("gsize", "small_body", name_of(e.get("small_body_size"))),
        ("gsize", "key_label", name_of(e.get("key_label_size"))),
    ])
    group(["Minor grid and axis line widths (Stata linewidth style names)."], [
        ("linewidth", "minor_grid", name_of(e.get("minor_grid_line_width"))),
        ("linewidth", "axisline", name_of(e.get("axis_line_width"))),
    ])
    group(["Legend rows; 0 means not fixed, so the column count above decides."], [
        ("numstyle", "legend_rows", e.get("legend_rows")),
    ])
    return groups


def _file_directives(lines: list[str]) -> dict:
    """``(class, key) -> (line index, value)`` for every directive line."""
    out = {}
    for i, raw in enumerate(lines):
        line = raw.strip()
        if (not line or line.startswith("*") or line.startswith("#include")
                or line.startswith("label")):
            continue
        tokens = line.split()
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


def _render_block(name: str, e: dict, groups, stamp: str) -> list[str]:
    rule = "* " + "-" * 75
    out = [
        rule,
        f"* Added {stamp} by scripts/extract_scheme_truth.py (WP-16): directives",
        "* Stata consumes that the translation above did not carry.  Values are",
        "* resolved from the same Stata #include chain and style files as the",
        f"* rest of this file (chain: {_chain_text(name, e)}); colours are",
        "* pre-resolved #rrggbb.  Re-running the script re-checks every directive",
        "* in this file and appends only what is missing.",
        rule,
    ]
    for comment, items in groups:
        out.append("")
        out.extend("* " + c if c else "*" for c in comment)
        width = max(len(k) for _, k, _ in items)
        for cls, key, value in items:
            out.append(f"{cls} {key:<{width}}  {value}")
    return out


def _new_file_header(name: str, e: dict, stata_base: str, stamp: str) -> list[str]:
    chain = _chain_text(name, e)
    rule = "* " + "-" * 75
    return [
        f"* {name}.scheme",
        rule,
        f"* dash translation of Stata's {name} scheme, written {stamp} by",
        "* scripts/extract_scheme_truth.py from Stata's own scheme-*.scheme and",
        "* style/*.style files.",
        f"*   Source Stata scheme : {os.path.join(stata_base, 's', f'scheme-{name}.scheme')}",
        f"*                         (Stata #include chain: {chain})",
        "* Every colour is a RESOLVED #rrggbb value; every p#stub is spelled out",
        "* p1..p15 because SchemeParser reads by exact key with no fallback.",
        rule,
        "",
        f'label "{name}"',
    ]


def update_scheme_file(path: str, name: str, e: dict, stata_base: str,
                       stamp: str) -> dict:
    """Bring ``schemes/<name>.scheme`` into line with fixture entry *e*.

    Returns ``{"changed": [...], "added": [...], "created": bool}`` describing
    what was written; an empty result means the file already agreed.
    """
    created = not os.path.exists(path)
    if created:
        lines = _new_file_header(name, e, stata_base, stamp)
    else:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().split("\n")
    present = _file_directives(lines)
    changed, added, append_groups = [], [], []
    for comment, items in expected_directives(e):
        missing = []
        for cls, key, value in items:
            hit = present.get((cls, key.lower()))
            if hit is None:
                missing.append((cls, key, value))
                continue
            idx, old = hit
            if not _same(old, value):
                lines[idx] = _replace_value(lines[idx], value)
                changed.append(f"{cls} {key}: {old} -> {value}")
        if missing:
            append_groups.append((comment, missing))
            added.extend(f"{c} {k}" for c, k, _ in missing)
    if append_groups:
        if present:
            insert_at = max(i for i, _ in present.values()) + 1
        else:
            insert_at = len(lines)
        block = _render_block(name, e, append_groups, stamp)
        lines[insert_at:insert_at] = [""] + block
    if created or changed or added:
        text = "\n".join(lines)
        if not text.endswith("\n"):
            text += "\n"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    return {"changed": changed, "added": added, "created": created}


# --------------------------------------------------------------------------- #

SCHEMES = [
    "stcolor", "stcolor_alt", "stgcolor", "stmono1", "stmono2", "stsj",
    "s2color", "s2mono", "s2gcolor", "s1color", "s1mono", "s1rcolor",
    "economist", "sj",
]


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
                    help="write the fixture only; leave schemes/*.scheme alone")
    args = ap.parse_args(argv)

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
            "stata_version": "StataNow 19.5 (MP), born 12 Aug 2026",
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
                "(s2mono, stmono2, stsj, sj) declares any lineplot key; for "
                "every other scheme p_lineplot_* is the p#stub->pstub->p#->p "
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
                        "a numeric linewidth is px = value * 5.0 (medium .30 "
                        "anchored at dash's 1.5px); keywords still go through "
                        "OptionTranslator._LWIDTH_MAP, whose ratios are not "
                        "this ladder's -- recorded as a follow-up"),
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
                           "note": "Stata's note textbox does not read gsize note"},
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

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    sys.stderr.write(f"wrote {args.out} ({len(args.schemes)} schemes)\n")

    if args.no_scheme_files:
        return 0
    for s in args.schemes:
        path = os.path.join(args.schemes_dir, f"{s}.scheme")
        result = update_scheme_file(path, s, doc[s], base, stamp)
        for line in result["changed"]:
            sys.stderr.write(f"{path}: CHANGED {line}\n")
        if result["created"]:
            sys.stderr.write(f"{path}: created\n")
        elif result["added"]:
            sys.stderr.write(
                f"{path}: added {len(result['added'])} directive(s): "
                + ", ".join(result["added"]) + "\n")
        elif not result["changed"]:
            sys.stderr.write(f"{path}: up to date\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
