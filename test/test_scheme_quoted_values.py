"""WP-28 GAPS2 D1: a scheme's quoted values (RGB colours, %opacity) were
dropped without a warning.

``SchemeParser._parse_lines`` (dash_render.py) took ``tokens[-1]`` as a
directive's value, so ``color p1 "31 119 180"`` -- Stata's own way to write
an RGB triplet -- split on whitespace into ``color``, ``p1``, ``"31``,
``119``, ``180"``, landing the value under the malformed key
``color p1 "31 119`` and leaving ``color p1`` unset.  Every series then
drew the scheme's ``color p`` default in its place, with no warning; the
same reader stored every shipped scheme's ``label "s2 color"`` line under
the key ``label "s2`` and never skipped a ``sequence`` line.

Third-party scheme files are out of scope (DISCOVERY Q30, review D13): no
test here reads, copies, sweeps or names one.  Every test reads a scheme
file it writes itself -- a copy of the shipped ``dash-s1rcolor.scheme``
edited to add the odd line forms Stata's own ``scheme.class`` (:189-226)
must read: quoted RGB with and without ``%opacity``, an unclosed quote, a
``label`` line and a tab-separated directive.
"""
import json
import os
import sys
import warnings

import pandas as pd
import pytest
from bokeh.models import GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402
from test_server_scheme import _build_doc, _first_glyph_colour  # noqa: E402


def _props_scheme(props):
    """A SchemeParser rebuilt from a property dict with no file behind it,
    exactly as the generated server app rebuilds its scheme
    (test_scheme_resolution.py:574-581)."""
    s = dr.SchemeParser.__new__(dr.SchemeParser)
    s._props = dict(props)
    s.name = "props"
    s.is_fallback = False
    s._init_properties()
    return s


def _write_scheme(tmp_path, name="myquoted"):
    """Copy ``dash-s1rcolor.scheme`` to ``<name>.scheme`` in *tmp_path*
    (the working-directory form dash.sthlp:2813 documents), replace its
    ``color background`` line with a quoted RGB triplet, and append every
    odd line form the reader must accept: quoted RGB with %opacity, an
    unclosed quote, a ``label`` line and a tab-separated directive.  No
    third-party file is copied or read (DISCOVERY Q30, review D13)."""
    src = os.path.join(_ROOT, "dash-s1rcolor.scheme")
    with open(src, encoding="utf-8") as fh:
        lines = fh.readlines()
    out = []
    replaced = False
    for ln in lines:
        if not replaced and ln.strip().startswith("color background"):
            out.append('color background      "255 0 0"\n')
            replaced = True
        else:
            out.append(ln)
    assert replaced, "s1rcolor.scheme has no `color background' line"
    out.append('color p1 "26 71 111 %20"\n')
    out.append('color p2 "0 255 0%50"\n')
    out.append('color p3 "0 0 255\n')          # unclosed quote: reads to EOL
    out.append('label "written by the test"\n')
    out.append('color\tp4\t"1 2 3"\n')          # tab-separated
    path = tmp_path / f"{name}.scheme"
    path.write_text("".join(out), encoding="utf-8")
    return str(path)


def _old_parse(path):
    """The reader before this fix, verbatim (dash_render.py's former
    ``_parse_lines`` tail): ``tokens[-1]`` as the value.  Used only as the
    before/after snapshot's baseline; #include lines are skipped here (both
    readers are compared on a copy with them stripped, see
    ``_strip_includes``)."""
    props = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("*"):
            continue
        if line.startswith("#include"):
            continue
        tokens = line.split()
        if len(tokens) < 2:
            continue
        category = tokens[0]
        value = tokens[-1]
        subcats = tokens[1:-1]
        key = (category + " " + " ".join(subcats)).strip() if subcats else category
        props[key] = value
    return props


def _strip_includes(path, tmp_path, name):
    """A temp copy of *path* with every ``#include`` line removed, so the
    old and new readers can be compared on the keys the file itself
    writes rather than on a spliced-in parent scheme's keys too."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    kept = [ln for ln in lines if not ln.strip().startswith("#include")]
    out = tmp_path / name
    out.write_text("".join(kept), encoding="utf-8")
    return str(out)


def _served_build_options(build_options):
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": "g1", "tabs": "", "filter_position": "top",
          "level": "95", "formats": {}}
    bo.update(build_options)
    return bo


class TestQuotedValuesAreRead:
    def test_a_scheme_written_with_quoted_values_is_read(self, tmp_path):
        path = _write_scheme(tmp_path)
        sp = dr.SchemeParser.__new__(dr.SchemeParser)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            props = sp._parse_file(path, set())
        assert props["color background"] == "255 0 0"
        assert props["color p1"] == "26 71 111 %20"
        assert props["color p2"] == "0 255 0%50"
        assert props["color p3"] == "0 0 255"
        assert props["color p4"] == "1 2 3"
        assert not any(k.startswith("label") for k in props), props
        assert not any('"' in k for k in props), props
        assert caught == [], [str(w.message) for w in caught]

        rebuilt = _props_scheme(props)
        assert rebuilt.background_color == "#ff0000"
        assert rebuilt.p_colors[:2] == ["#1a476f", "#00ff00"]
        assert rebuilt.p_alphas[:2] == [pytest.approx(0.2), pytest.approx(0.5)]

    def test_both_modes_draw_the_quoted_background_and_p1(self, tmp_path,
                                                           monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_scheme(tmp_path)
        plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                  "options": {}}]
        df = pd.DataFrame({"mpg": [22.0, 18.0, 25.0],
                           "weight": [2930.0, 3350.0, 2200.0]})
        spec = {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                            "plots": plots, "options": {}}],
                "kpis": [],
                "build_options": _served_build_options({"scheme": "myquoted"})}
        sp_path = tmp_path / "spec.json"
        dp_path = tmp_path / "data.json"
        sp_path.write_text(json.dumps(spec))
        dp_path.write_text(json.dumps(make_data_json(df)))

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            renderer = dr.DashRenderer(str(sp_path), str(dp_path))
            renderer.render()
        assert caught == [], [str(w.message) for w in caught]
        assert renderer.scheme.background_color == "#ff0000"
        assert renderer.scheme.p_colors[0] == "#1a476f"
        fig = renderer.figures["g1"]
        colours = [getattr(r.glyph, "fill_color", None).lower()
                   for r in fig.renderers if isinstance(r, GlyphRenderer)
                   and isinstance(getattr(r.glyph, "fill_color", None), str)]
        assert "#1a476f" in colours, colours

        doc = _build_doc(tmp_path, {"scheme": "myquoted"}, plots=plots)
        assert _first_glyph_colour(doc) == "#1a476f"

        app_path = tmp_path / "app_probe.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp_path), str(dp_path)).build(str(app_path))
        app_src = app_path.read_text(encoding="utf-8")
        import importlib.util
        mspec = importlib.util.spec_from_file_location("_s06_app", str(app_path))
        mod = importlib.util.module_from_spec(mspec)
        mspec.loader.exec_module(mod)
        assert mod._SCHEME_PROPS["color p1"] == "26 71 111 %20"
        del app_src

    def test_a_quoted_rgb_with_opacity_reaches_the_alpha_reader(self, tmp_path):
        path = tmp_path / "three.scheme"
        path.write_text(
            'color p1 "26 71 111 %20"\n'
            'color p2 "0 255 0%50"\n'
            'color background "  0 255   0"\n',
            encoding="utf-8")
        sp = dr.SchemeParser.__new__(dr.SchemeParser)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            props = sp._parse_file(str(path), set())
        assert caught == [], [str(w.message) for w in caught]
        rebuilt = _props_scheme(props)
        assert rebuilt.p_colors[:2] == ["#1a476f", "#00ff00"]
        assert rebuilt.p_alphas[:2] == [pytest.approx(0.2), pytest.approx(0.5)]
        assert rebuilt.background_color == "#00ff00"


class TestTheTokeniserIsStatas:
    def test_a_quoted_value_is_one_token(self):
        assert dr.SchemeParser._scheme_tokens(
            'color p1 "31 119 180"') == ["color", "p1", "31 119 180"]

    def test_tabs_compound_quotes_and_an_unclosed_quote(self):
        assert dr.SchemeParser._scheme_tokens(
            'color\tp1\t"1 2 3"') == ["color", "p1", "1 2 3"]
        assert dr.SchemeParser._scheme_tokens(
            'special fpfmt_es `"%6.2f"\'') == [
            "special", "fpfmt_es", "%6.2f"]
        assert dr.SchemeParser._scheme_tokens(
            'color background "255 0 0') == [
            "color", "background", "255 0 0"]
        toks = dr.SchemeParser._scheme_tokens('symbolsize p small *medium')
        assert toks == ["symbolsize", "p", "small", "*medium"]
        assert len(toks) == 4


class TestTheReaderSkipsWhatStataSkips:
    def _parse_text(self, tmp_path, text, name="t.scheme"):
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        sp = dr.SchemeParser.__new__(dr.SchemeParser)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            props = sp._parse_file(str(path), set())
        return props, caught

    def test_comment_sequence_and_label_lines_store_nothing(self, tmp_path):
        text = "* c\n*! v\n// c\nsequence 1210\nlabel \"x y\"\ncolor p1 navy\n"
        props, caught = self._parse_text(tmp_path, text)
        assert props == {"color p1": "navy"}
        assert caught == [], [str(w.message) for w in caught]

    def test_a_two_token_line_is_a_class_default_and_a_fourth_token_is_ignored(
            self, tmp_path):
        props, caught = self._parse_text(
            tmp_path, "intensity full\ncolor p1 red blue\n")
        assert props == {"intensity": "full", "color p1": "red"}
        assert caught == [], [str(w.message) for w in caught]


class TestUnreadableLinesWarnOnceEach:
    def test_each_bad_line_is_named_with_its_number_then_the_bound_holds(
            self, tmp_path):
        lines = [f"junk{i}\n" for i in range(1, 13)] + ["#include\n"]
        path = tmp_path / "bad.scheme"
        path.write_text("".join(lines), encoding="utf-8")
        sp = dr.SchemeParser.__new__(dr.SchemeParser)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            props = sp._parse_file(str(path), set())
        assert props == {}
        msgs = [str(w.message) for w in caught]
        assert len(msgs) == 11, msgs
        for i in range(10):
            assert f"line {i + 1} of 'bad.scheme'" in msgs[i], msgs[i]
        assert "no more are noted" in msgs[10], msgs[10]

        # A hostile line and a hostile basename are both bounded (F-10):
        # a 500-character bad line is echoed as at most 80 printable
        # characters, and a 200-character basename of which 100 are
        # non-printable is named by at most 80 printable characters.
        basename = ("h" * 100 + "\x01\x02" * 50) + ".scheme"
        assert len(basename) == 207
        hostile_path = tmp_path / basename
        hostile_path.write_text(("x" * 500) + "\n", encoding="utf-8")
        sp2 = dr.SchemeParser.__new__(dr.SchemeParser)
        with warnings.catch_warnings(record=True) as caught2:
            warnings.simplefilter("always")
            sp2._parse_file(str(hostile_path), set())
        assert len(caught2) == 1, [str(w.message) for w in caught2]
        msg = str(caught2[0].message)
        printable_name_part = "".join(
            ch for ch in basename if ch.isprintable())[:80]
        assert printable_name_part in msg, msg
        assert "\x01" not in msg and "\x02" not in msg, msg
        assert "x" * 500 not in msg, msg


class TestShippedSchemesParseAsBefore:
    _SCHEMES_DIR = _ROOT
    _FILES = sorted(f for f in os.listdir(_SCHEMES_DIR)
                    if f.startswith("dash-") and f.endswith(".scheme"))

    @pytest.mark.parametrize("fname", _FILES)
    def test_every_shipped_scheme_gives_the_old_props_minus_label_and_sequence(
            self, fname, tmp_path):
        path = os.path.join(self._SCHEMES_DIR, fname)
        stripped = _strip_includes(path, tmp_path, f"noinc_{fname}")

        old = _old_parse(stripped)
        old_filtered = {
            k: v.strip('"\'`') for k, v in old.items()
            if not (k == "sequence" or k.startswith("label"))
        }

        sp = dr.SchemeParser.__new__(dr.SchemeParser)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            new = sp._parse_file(stripped, set())
        assert caught == [], (fname, [str(w.message) for w in caught])
        assert new == old_filtered, fname
