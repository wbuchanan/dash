"""What the last-resort scheme is, and what a served dashboard says about it.

``SchemeParser.fallback()`` is the last line of defence: it returns a usable
scheme without reading any file, so a render on an install whose scheme files
cannot be read ends in a dashboard rather than a traceback.  Two things about
it were not true.

1.  It does not mirror s2color, though it says it does
-------------------------------------------------------
Its comment reads "Mirrors s2color so the output stays recognisable."
Measured against ``SchemeParser("s2color")`` parsed from the shipped file:
23 properties against 118, and **12 public attributes differ** --
``draw_major_vgrid`` (True -> False), ``grid_line_width`` (1.5 -> 0.8),
``area_alpha`` and ``bar_alpha`` (1.0 -> 0.8), ``heading_font_size``
(14pt -> 13pt), ``text_font_size`` (11pt -> 10pt), ``note_font_size``
(8pt -> 9pt), ``symbolsize`` ('medium' -> ''), ``graphsize_x``/``graphsize_y``
and ``legend_cols``/``legend_position`` (values -> None).

"Recognisable" is the whole justification for having a fallback at all, so
these tests hold it to its own claim rather than to a weaker one.  They
compare *attributes*, not the raw property dict: the fallback is written in
Stata colour names and s2color's file in resolved hex, so the dicts cannot be
compared directly and it is the translated values that reach a figure.

2.  A served dashboard built on the fallback said nothing
----------------------------------------------------------
``ServerAppBuilder`` bakes the parent's parsed properties into the generated
app and rebuilds a ``SchemeParser`` from them with ``_s.is_fallback = False``
written literally.  The standalone path warns at resolution time, in the
parent, so the *builder's* user is told.  Nobody who later runs the generated
app is: it is byte-indistinguishable in provenance from an app built on a
healthy install, and ``is_fallback`` has no reader anywhere in dash -- ``grep
-rn is_fallback`` over ``dash.ado``, ``dash_parse.mata``, ``scripts/`` and
``test/`` returned nothing before this file.

So the hardcoded ``False`` is not itself the defect: correcting it to ``True``
would change nothing observable.  The defect is that the app is silent, and
the fix is a notice the app emits, naming the scheme that was *requested* --
not ``self.scheme.name``, which is provably the literal ``"s2color"`` whenever
``is_fallback`` is true, and so would tell the user they asked for the thing
they got.

Tests: FBP-01 through FBP-09.
"""
from __future__ import annotations

import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402

#: Attributes whose value is provenance, not style -- excluded from the
#: mirroring comparison because they are *meant* to differ.
PROVENANCE_ATTRS = frozenset({"is_fallback"})


def _public_attrs(scheme):
    out = {}
    for name in dir(scheme):
        if name.startswith("_") or name in PROVENANCE_ATTRS:
            continue
        try:
            value = getattr(scheme, name)
        except Exception:                                  # pragma: no cover
            continue
        if callable(value):
            continue
        out[name] = value
    return out


# ==========================================================================
# FBP-01..04 — the fallback keeps the promise its comment makes
# ==========================================================================

class TestTheFallbackMirrorsS2color:

    def test_every_style_attribute_matches(self):
        """FBP-01. The claim, asserted whole.

        Twelve attributes differed when this was written.  Listing them
        individually would let the next one through.
        """
        real = _public_attrs(dr.SchemeParser("s2color"))
        fake = _public_attrs(dr.SchemeParser.fallback())
        assert set(real) == set(fake), (
            "the two schemes do not even expose the same attributes: "
            "%r" % (set(real) ^ set(fake),)
        )
        differing = {k: (real[k], fake[k]) for k in real if real[k] != fake[k]}
        assert not differing, (
            "SchemeParser.fallback() claims to mirror s2color but differs on "
            "%d attribute(s): %s"
            % (len(differing),
               ", ".join("%s (s2color=%r, fallback=%r)" % (k, a, b)
                         for k, (a, b) in sorted(differing.items())))
        )

    def test_it_still_reports_its_name_as_s2color(self):
        """FBP-02. The name is what it renders as; is_fallback is how it got there."""
        assert dr.SchemeParser.fallback().name == "s2color"

    def test_it_still_reports_that_it_is_a_fallback(self):
        """FBP-03. Mirroring s2color must not erase the provenance."""
        assert dr.SchemeParser.fallback().is_fallback is True
        assert dr.SchemeParser("s2color").is_fallback is False

    def test_it_needs_no_file(self):
        """FBP-04. The one thing the fallback exists for.

        Asserted by watching ``open``: a fallback that reached the disk would
        be useless on the install it is meant to rescue.
        """
        import builtins
        opened = []
        real_open = builtins.open

        def spy(path, *args, **kwargs):
            opened.append(str(path))
            return real_open(path, *args, **kwargs)

        builtins.open = spy
        try:
            scheme = dr.SchemeParser.fallback()
            scheme.default_color(0, "scatter")
        finally:
            builtins.open = real_open
        assert not [p for p in opened if p.endswith(".scheme")], (
            "fallback() read scheme file(s): %r" % (opened,)
        )


# ==========================================================================
# FBP-05..09 — a served app says how it was built
# ==========================================================================

def _server_source(tmp_path, scheme_name, break_schemes):
    """Build a Bokeh-server app source and return it as text.

    When *break_schemes* is set, the scheme search directories are pointed at
    an empty directory so resolution genuinely falls back -- the state a
    net-installed dash was in for every scheme it shipped.
    """
    spec = {
        "build_options": {"layout": "1 1", "level": "95", "formats": {},
                          "scheme": scheme_name, "title": "T"},
        "graphs": [{
            "name": "g1",
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"name": "g1"}, "if_expr": "", "in_expr": "",
        }],
        "kpis": [],
    }
    data = {
        "values": [{"x": 1.0, "y": 2.0}, {"x": 2.0, "y": 3.0}],
        "variableLabels": {}, "valueLabels": {}, "valueLabelNames": {},
        "variableTypeIsString": {"x": False, "y": False},
    }
    spec_path = tmp_path / "spec.json"
    data_path = tmp_path / "data.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    data_path.write_text(json.dumps(data), encoding="utf-8")

    empty = tmp_path / "empty"
    empty.mkdir(exist_ok=True)
    app_path = tmp_path / "app.py"

    saved_dirs = dr.SchemeParser._SCHEME_SEARCH_DIRS
    saved_root = dr.SchemeParser._PLUS_ROOT
    if break_schemes:
        dr.SchemeParser._SCHEME_SEARCH_DIRS = (str(empty),)
        dr.SchemeParser._PLUS_ROOT = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(spec_path), str(data_path)).build(
                str(app_path))
    finally:
        dr.SchemeParser._SCHEME_SEARCH_DIRS = saved_dirs
        dr.SchemeParser._PLUS_ROOT = saved_root
    return app_path.read_text(encoding="utf-8")


class TestAServedAppReportsHowItWasBuilt:

    def test_an_app_built_on_a_fallback_carries_a_notice(self, tmp_path):
        """FBP-05. Measured before: zero warnings at import, provenance lost."""
        source = _server_source(tmp_path, "economist", break_schemes=True)
        assert "_DASH_SCHEME_IS_FALLBACK = True" in source, (
            "the generated app does not record that it was built on the "
            "fallback scheme"
        )
        assert "warnings.warn" in source or "warn(" in source, (
            "the generated app records the fallback but never says so"
        )

    def test_the_notice_names_the_scheme_that_was_asked_for(self, tmp_path):
        """FBP-06. ``self.scheme.name`` is 's2color' whenever is_fallback is
        true, so a message built from it tells the user they got what they
        asked for. The REQUESTED name is what has to appear."""
        source = _server_source(tmp_path, "economist", break_schemes=True)
        assert "economist" in source, (
            "the notice does not name the requested scheme, so it cannot "
            "tell the user what they did not get"
        )

    def test_a_healthy_app_carries_no_notice(self, tmp_path):
        """FBP-07. The note must be silent on a working install."""
        source = _server_source(tmp_path, "economist", break_schemes=False)
        assert "_DASH_SCHEME_IS_FALLBACK = False" in source
        assert "could not be read" not in source, (
            "a healthy build emitted the fallback notice"
        )

    def test_the_rebuilt_scheme_does_not_misreport_its_provenance(self,
                                                                  tmp_path):
        """FBP-08. ``_s.is_fallback = False`` was written literally."""
        source = _server_source(tmp_path, "economist", break_schemes=True)
        assert "_s.is_fallback = False" not in source, (
            "the generated app hardcodes is_fallback=False even though the "
            "build fell back"
        )

    def test_the_generated_app_still_parses(self, tmp_path):
        """FBP-09. A notice that breaks the app is worse than no notice."""
        import ast
        for broken in (True, False):
            source = _server_source(tmp_path, "economist",
                                    break_schemes=broken)
            ast.parse(source)
