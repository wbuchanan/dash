"""G5 (WP-28): a Unicode Stata variable name works wherever an ASCII one
does.

Stata 14+ names may hold Unicode letters ([U] 11.3), and dash already
accepted them in most places (the by() rule of dash_parse.mata:2916 is
``\\p{L}``, and ``test_statistical_options.cscript`` SO-30u already builds
a weight expression on a variable named ``größe``).  But ``_dash_is_name``
in dash_parse.mata (used only by ``filter()``'s Mata caller until this
change) was ASCII-only, so ``filter(größe)`` was refused "not a valid Stata
variable name"; the KPI pattern in dash.ado was ASCII-only, so
``dash kpi mean(größe)`` was refused "syntax is stat(varname)"; and the
renderer's own ``_DASH_VARNAME_RE`` was ASCII-only in five places, so a
Unicode ``by()`` drew no panels, a Unicode ``hover()`` field was left out
of the tooltip, a Unicode ``filter()`` built no widget, and
``_apply_colorvar`` silently drew no colours.

Every one of those sites now calls one Unicode-aware check: Mata's
``_dash_is_varname`` (dash_parse.mata, the 2916 rule) for ``filter()`` and
dash.ado's own ``dash kpi`` pattern; ``dash_render.py``'s
``_dash_is_stata_name`` (``str.isidentifier()``, already used by
``_dash_write_stata_data``) for by(), filter(), exclude(), hover(),
``_drawn_field`` and colorvar().  A name that is not a Stata name -- a
brace, a quote, a blank, ``$``, a backtick, or 33 characters -- is refused
at every one of those sites exactly as an invalid ASCII name always was.
"""
import os
import sys

import pytest
from bokeh.models import RangeSlider, Select

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import make_spec, plot_for  # noqa: E402
from conftest import drawn_renderers  # noqa: E402

#: A non-ASCII scatter (yvar größe, price's values) and by/colorvar's own
#: binary variable renamed ausländisch (foreign's values).
_RENAMES = {"price": "größe", "foreign": "ausländisch"}


@pytest.fixture
def unicode_df(monkeypatch):
    """test_mode_parity's frame with price -> größe, foreign -> ausländisch;
    reverted automatically (monkeypatch) so other tests see the original."""
    df = tp._DF.rename(columns=_RENAMES)
    monkeypatch.setattr(tp, "_DF", df)
    return df


class TestTheNameCheck:
    """_dash_is_stata_name (dash_render.py:1183) is the predicate every
    renderer site now calls; this pins it directly, before anything built
    on it is trusted."""

    @pytest.mark.parametrize("name", [
        "größe", "ausländisch", "_x", "a1", "a" * 32,
    ])
    def test_unicode_letters_and_plain_ascii_pass(self, name):
        assert dr._dash_is_stata_name(name) is True

    @pytest.mark.parametrize("name", [
        "x}<img src=x onerror=alert(1)>", "a b", 'a"b', "$m", "a`b",
        "1a", "", "a" * 33, None,
    ])
    def test_markup_and_overlong_names_are_refused(self, name):
        assert dr._dash_is_stata_name(name) is False


class TestFilterOnAUnicodeName:

    def test_the_parser_keeps_the_name(self):
        specs = dr._dash_parse_filter_raw("größe, type(range)")
        assert len(specs) == 1
        assert specs[0]["varname"] == "größe"

    def test_a_range_widget_is_built_in_both_modes(self, unicode_df):
        spec = make_spec([plot_for("scatter")],
                         build_options={"filter": "größe, type(range)"})
        r, saved_w = tp._standalone(spec)
        [w] = [x for x in r.filter_widgets if isinstance(x, RangeSlider)]
        assert "größe" in w.title
        assert not [m for m in saved_w if "refused" in m or "not a valid" in m]
        doc, served_w = tp._served(spec)
        [sw] = list(doc.select({"type": RangeSlider}))
        assert "größe" in sw.title
        assert not [m for m in served_w
                   if "refused" in m or "not a valid" in m]

    def test_a_dropdown_is_built_in_both_modes(self, unicode_df):
        spec = make_spec([plot_for("scatter")],
                         build_options={"filter": "größe, type(dropdown)"})
        r, saved_w = tp._standalone(spec)
        [w] = [x for x in r.filter_widgets if isinstance(x, Select)]
        assert "größe" in w.title
        doc, served_w = tp._served(spec)
        [sw] = list(doc.select({"type": Select}))
        assert "größe" in sw.title
        assert not [m for m in saved_w + served_w
                   if "refused" in m or "not a valid" in m]


class TestByOnAUnicodeName:

    def test_the_parser_keeps_the_name(self):
        assert dr._dash_parse_by("ausländisch")[0] == "ausländisch"

    def test_panels_are_drawn_in_both_modes(self, unicode_df):
        spec = make_spec([plot_for("scatter")],
                         graph_options={"by": "ausländisch"})
        r, saved_w = tp._standalone(spec)
        assert len(r.figures) == 2, r.figures
        assert not [m for m in saved_w if "drawn without panels" in m]
        doc, served_w = tp._served(spec)
        from bokeh.plotting import figure as _fig
        figs = [f for root in doc.roots for f in root.select({"type": _fig})]
        assert len(figs) == 2, figs
        assert not [m for m in served_w if "drawn without panels" in m]


class TestHoverOnAUnicodeName:

    def test_the_tooltip_field_is_kept_in_both_modes(self, unicode_df):
        spec = make_spec([plot_for("scatter")],
                         graph_options={"hover": "größe"})
        r, saved_w = tp._standalone(spec)
        [fig] = list(r.figures.values())
        from bokeh.models import HoverTool
        [ht] = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert any("größe" in f for _lbl, f in ht.tooltips)
        assert not [m for m in saved_w if "not a plain name" in m]
        doc, served_w = tp._served(spec)
        from bokeh.plotting import figure as _fig
        [sfig] = [f for root in doc.roots for f in root.select({"type": _fig})]
        [sht] = [t for t in sfig.tools if isinstance(t, HoverTool)]
        assert any("größe" in f for _lbl, f in sht.tooltips)
        assert not [m for m in served_w if "not a plain name" in m]


class TestColorvarOnAUnicodeName:

    @staticmethod
    def _has_mapper(renderer):
        fc = renderer.glyph.fill_color
        if isinstance(fc, dict):
            return "transform" in fc
        return getattr(fc, "transform", None) is not None

    def test_colours_are_drawn_in_both_modes(self, unicode_df):
        spec = make_spec([plot_for("scatter",
                                   {"colorvar": "ausländisch"})])
        r, saved_w = tp._standalone(spec)
        [fig] = list(r.figures.values())
        # Flipped (WP-42 CV-7): not the layer's hidden legend proxy.
        [sc] = [rr for rr in drawn_renderers(fig)
               if type(rr.glyph).__name__ == "Scatter"]
        assert self._has_mapper(sc)
        doc, served_w = tp._served(spec)
        from bokeh.plotting import figure as _fig
        [sfig] = [f for root in doc.roots for f in root.select({"type": _fig})]
        [ssc] = [rr for rr in drawn_renderers(sfig)
                if type(rr.glyph).__name__ == "Scatter"]
        assert self._has_mapper(ssc)


class TestAdversarialUnicodeNames:
    """Every ASCII adversarial case passed before this change (they hit
    the ASCII-only regex the same way); a 33-character Unicode name is new
    -- Stata cannot make one through ``rename``, so this is the boundary
    the predicate itself pins."""

    @pytest.mark.parametrize("name", [
        "x}<img src=x onerror=alert(1)>", 'a"b', "größe$x", "ä" * 33,
    ])
    def test_a_non_name_is_still_refused_at_every_site(self, name):
        specs = dr._dash_parse_filter_raw(f"{name}, type(range)", warn=False)
        assert specs == []
        by_names, _n, _t, _f, _u = dr._dash_parse_by(name, warn=False)
        assert by_names == ""
        assert not dr._dash_is_stata_name(name)


class TestTheServedAppCarriesTheCheck:

    def test_the_generated_app_defines_dash_is_stata_name(self):
        spec = make_spec([plot_for("scatter")])
        _tag, sp, dp = tp._write(spec)
        ap = os.path.join(tp._TMP, "app_carries_check_%s.py" % _tag)
        dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert "_dash_is_stata_name" in src
        assert "_DASH_VARNAME_RE" not in src
