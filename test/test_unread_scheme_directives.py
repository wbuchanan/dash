"""Scheme directives dash does not draw are kept, without a note (WP-30
P1.4b, ratification row 4 of 06oct2026).

twoway draws ``clockdir p``, the ``textboxstyle`` of a title or of tick
labels and other keys dash does not draw yet.  By the maintainer's answer
the parser keeps every directive it parses -- a user file's, a file it
includes and every shipped file's -- so a later version can draw them from
the scheme, and none is noted.  Every test here is a guard: it held before
section 33 and must hold after it.
"""

import ast
import glob
import os
import sys
import time
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_served_linked_views as tlv  # noqa: E402
from test_scheme_resolution import MODES, _draw  # noqa: E402
from test_scheme_review_fixes import _user_scheme  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

#: twoway draws each of these differently from s2color (measured, plan
#: section 33 E6); dash draws none of them yet.
W33S = ["#include s2color", "textboxstyle title subheading",
        "textboxstyle axis_title heading", "clockdir p 9",
        "yesno plabelboxed yes", "textboxstyle key_label heading",
        "textboxstyle tick heading"]
W33Q = ["#include s2color", "clockdir p1 9", "yesno p1labelboxed yes",
        "textboxstyle subtitle heading", "textboxstyle caption heading"]
W33M = (["#include s2color"] + [f"clockdir p{i} 9" for i in range(1, 16)]
        + ["clockdir p 9", "textboxstyle tick heading"])
W33INC = ["clockdir p 9", "textboxstyle tick heading"]

#: Keys the shipped files carry that dash does not read.
_SHIPPED_UNREAD = ("color foreground", "gsize text", "yesno draw_major_grid",
                   "yesno draw_minor_grid", "linepattern plotregion")


def _directives(lines):
    """{key: value} of *lines* as ``_parse_lines`` stores them (no
    #include), the last of a repeated key winning."""
    out = {}
    for raw in lines:
        line = raw.replace("\t", " ").strip()
        if not line or line.startswith(("*", "//", "#")):
            continue
        t = dr.SchemeParser._scheme_tokens(line)
        if len(t) < 2 or t[0] in ("sequence", "label"):
            continue
        if len(t) == 2:
            out[t[0]] = t[1]
        else:
            out[f"{t[0]} {t[1]}"] = t[2]
    return out


def _missing(props, lines):
    return {k: v for k, v in _directives(lines).items()
            if props.get(k) != v}


class TestUnreadDirectivesAreRetained:

    def test_a_user_schemes_directives_are_kept(self, tmp_path, monkeypatch):
        for name, lines in (("w33s", W33S), ("w33q", W33Q)):
            _user_scheme(tmp_path, monkeypatch, f"{name}.scheme", lines)
            sp = dr.SchemeParser(name)
            assert _missing(sp._props, lines) == {}, name

    def test_a_class_default_line_is_kept(self, tmp_path, monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "w33d2.scheme",
                     ["#include s2color", "w33default zz"])
        assert dr.SchemeParser("w33d2")._props["w33default"] == "zz"

    def test_an_included_user_files_directives_are_kept(self, tmp_path,
                                                        monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "w33inc.scheme", W33INC)
        _user_scheme(tmp_path, monkeypatch, "w33i.scheme",
                     ["#include s2color", "#include w33inc"])
        assert _missing(dr.SchemeParser("w33i")._props, W33INC) == {}

    def test_a_shipped_schemes_unread_keys_are_kept(self):
        files = sorted(glob.glob(os.path.join(_ROOT, "dash-*.scheme")))
        assert len(files) == 26
        bad = {}
        for path in files:
            name = os.path.basename(path)[len("dash-"):-len(".scheme")]
            with open(path, encoding="utf-8") as fh:
                lines = fh.readlines()
            miss = _missing(dr.SchemeParser(name)._props, lines)
            if miss:
                bad[name] = (sorted(miss)[:5],
                             [k for k in _SHIPPED_UNREAD if k in miss])
        assert bad == {}

    def test_the_served_app_carries_them(self, tmp_path, monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "w33s.scheme", W33S)
        spec = tp._spec([plot_for("scatter")], {"scheme": "w33s"})
        sp, dp = tlv._write_inputs(tmp_path, spec)
        app = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(app)
        with open(app, encoding="utf-8") as fh:
            [line] = [ln for ln in fh if ln.startswith("_SCHEME_PROPS = ")]
        props = ast.literal_eval(line.split("=", 1)[1].strip())
        assert _missing(props, W33S) == {}


def _scheme_notes(caught):
    return [str(getattr(w, "message", w)) for w in caught
            if str(getattr(w, "message", w)).startswith("dash scheme:")]


class TestNoNoteForUnreadDirectives:

    def test_parsing_is_silent(self, tmp_path, monkeypatch):
        for name, lines in (("w33s", W33S), ("w33q", W33Q), ("w33m", W33M)):
            _user_scheme(tmp_path, monkeypatch, f"{name}.scheme", lines)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                dr.SchemeParser(name)
            assert [str(w.message) for w in caught] == [], name

    @pytest.mark.parametrize("mode", MODES)
    def test_builds_are_silent(self, mode, tmp_path, monkeypatch):
        """A saved build, and a served build with its document, print no
        scheme note for w33s's unread directives."""
        _user_scheme(tmp_path, monkeypatch, "w33s.scheme", W33S)
        d = _draw(tp._spec([plot_for("scatter", {"mlabel": "mpg"})],
                           {"scheme": "w33s"}), mode)
        assert _scheme_notes(d.warnings) == []


class TestHostileSchemes:

    def test_a_large_file_is_kept_and_silent(self, tmp_path, monkeypatch):
        lines = [f"clockdir p{i % 15 + 1} 9" for i in range(30000)]
        _user_scheme(tmp_path, monkeypatch, "w33big.scheme", lines)
        t0 = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sp = dr.SchemeParser("w33big")
        assert time.perf_counter() - t0 < 2.0
        assert [str(w.message) for w in caught] == []
        assert all(sp._props.get(f"clockdir p{i}") == "9"
                   for i in range(1, 16))


class TestTheHelpSaysTheyAreKept:

    def test_kept_without_a_note(self):
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            text = fh.read()
        assert "kept with the scheme, without a note" in " ".join(
            text.split())
        assert "twoway draws and dash does not" not in text
