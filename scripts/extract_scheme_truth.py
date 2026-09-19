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
are written from.

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
        --out test/fixtures/scheme_truth.json

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
        # Ordered list of scheme names actually spliced in, parent-first.
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


def resolve_sized(r: SchemeResolver, cls: str, token: str | None):
    """Resolve a gsize/symbolsize token to {name, value, sztype}.

    A token is either a literal number (a relative size) or a style name such as
    ``medsmall`` that indirects into ``style/<cls>-<name>.style`` which carries
    ``set val`` and ``set sztype``.
    """
    if token is None:
        return None
    tok = token.strip().strip('"')
    lit = _as_number(tok)
    if lit is not None:
        return {"name": tok, "value": float(lit), "sztype": "relative"}
    st = r.style(cls, tok.lower())
    if not st or "val" not in st:
        return {"name": tok, "value": None, "sztype": None}
    val = _as_number(st["val"])
    return {
        "name": tok,
        "value": float(val) if val is not None else None,
        "sztype": st.get("sztype"),
    }


def resolve_linewidth(r: SchemeResolver, token: str | None):
    if token is None:
        return None
    tok = token.strip().strip('"')
    lit = _as_number(tok)
    if lit is not None:
        return {"name": tok, "value": float(lit)}
    st = r.style("linewidth", tok.lower())
    if not st or "val" not in st:
        return {"name": tok, "value": None}
    val = _as_number(st["val"])
    return {"name": tok, "value": float(val) if val is not None else None}


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

    out = {
        "include_chain": list(reversed(r.include_chain)),  # child -> ... -> root
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
        # Not requested, but grid_color is meaningless without it: s2color (and
        # therefore the whole s1* family) sets both of these to "no", so those
        # schemes never draw a grid at all.
        "draw_major_hgrid": scalar("draw_major_hgrid", "yesno",
                                   ["draw_major_hgrid"], lambda t: t.strip(),
                                   class_default=False),
        "draw_major_vgrid": scalar("draw_major_vgrid", "yesno",
                                   ["draw_major_grid"], lambda t: t.strip(),
                                   class_default=False),
        "title_color": color_of("title_color", ["heading"]),
        "axis_line_color": color_of("axis_line_color", ["axisline"]),

        "default_line_width": scalar(
            "default_line_width", "linewidth", ["p"],
            lambda t: resolve_linewidth(r, t), class_default=True),
        "grid_line_width": scalar(
            "grid_line_width", "linewidth", ["major_grid", "grid"],
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
    }

    out["sources"] = sources

    # Anything that came back None because a token could not be resolved.
    for msg in c.unresolved:
        if msg not in unresolvable:
            unresolvable.append(msg)
    out["unresolvable"] = unresolvable
    return out


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
    args = ap.parse_args(argv)

    base = args.stata_base
    if not os.path.isdir(os.path.join(base, "s")):
        sys.stderr.write(f"error: no scheme directory under {base}\n")
        return 2

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
                "*_size.value": "Stata relative size units (sztype gives the kind)",
                "default_line_width/grid_line_width.value": "Stata linewidth units",
                "*_alpha.pct": "percent as written in the scheme; alpha = pct/100",
                "legend_position": "clock direction (0-12)",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
