"""Stata's style files, read as twoway reads them (WP-31 section 44, E10).

twoway draws every style name of its four option classes from that name's
``style/<class>-<name>.style`` file on the ado-path: the 57 names outside
dash's transcribed table (``pstyle(fpall)``, ``mstyle(refmarker)``,
``astyle(plotregion)`` ...), a package's or a user's own
``linestyle-mine.style``, and the file a scheme's class directive
(``linestyle ci mine``) points a hop at.  dash drew the 57 in default
attributes with a note and could not read any file.  Every expectation is
twoway's, measured in StataNow 19.5 by scripts/extract_style_files_truth.do
into test/fixtures/style_files_truth.json.
"""

from __future__ import annotations

import json
import os
import sys
import time
import warnings

import pytest
from bokeh.models import GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_scheme_resolution as tsr  # noqa: E402
import test_style_names as tsn  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

SP = dr.SchemeParser
T = dr.OptionTranslator
MODES = tsr.MODES

with open(os.path.join(_HERE, "fixtures", "style_files_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

BASE = TRUTH["find_base"]
HAVE_BASE = os.path.isdir(os.path.join(BASE, "style"))
needs_base = pytest.mark.skipif(not HAVE_BASE,
                                reason="Stata's style files are not here")

#: u44b as the extractor wrote it.
U44B = "set width thick\nset color red\nset pattern dash\n"
RED_W = T.translate_lwidth("thick")
RED_DASH = list(T.translate_lpattern("dash"))


def _user_dir(tmp_path, files):
    """A directory on the ado-path holding *files* {relpath: text}."""
    d = tmp_path / "ado"
    for rel, text in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return str(d)


def _draw(plots, scheme, mode, dirs=(), bo=None, graph=None):
    """(renderers, dash notes) one mode drew, along the ado-path *dirs*."""
    if isinstance(plots, dict):
        plots = [plots]
    b = {"scheme": scheme, "scheme_dirs": list(dirs)}
    b.update(bo or {})
    d = tsr._draw(tp._spec(list(plots), b, graph or {}), mode)
    rs = [r for f in d.figures for r in f.renderers
          if isinstance(r, GlyphRenderer)]
    return rs, [m for m in d.warnings if m.startswith("dash")]


def _red_line(g):
    return (tsn._hex(g.line_color), round(g.line_width, 3),
            list(g.line_dash))


RED = ("#ff0000", round(RED_W, 3), RED_DASH)


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_meta(self):
        assert sorted(TRUTH["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]

    def test_161(self):
        f = TRUTH["all.files"]
        assert sum(len(f[c]) for c in ("linestyle", "areastyle",
                                       "markerstyle", "seriesstyle")) == 161
        assert {c: sorted(v) for c, v in SP._STYLE_KNOWN.items()} == {
            c: f[c] for c in SP._STYLE_KNOWN}

    def test_57(self):
        names = {k.split("|", 1)[1] for k in TRUTH["draw"]}
        assert len(names) == 57
        assert all(r["rc"] == 0 and not r["notes"]
                   for r in TRUTH["draw"].values())


# ---------------------------------------------------------------------------
# The walk
# ---------------------------------------------------------------------------

def _walk_dir(tmp_path):
    return _user_dir(tmp_path, {
        "linestyle-u44a.style": U44B, "style/linestyle-u44b.style": U44B,
        "linestyle-u44c.style": "set width thin\n",
        "style/linestyle-u44c.style": "set width vthick\n",
        "l/linestyle-u44d.style": "set width thin\n"})


class TestTheWalk:
    def test_order_is_findfiles(self, tmp_path):
        """Each ado-path directory, then its style/ subdirectory (findfile
        finds u44c in the directory, not in style/, and never looks in
        the l/ letter subdirectory)."""
        d = _walk_dir(tmp_path)
        sp = SP("s2color", ado_dirs=(d, BASE))
        got = {}
        for n in ("u44a", "u44b", "u44c", "u44d"):
            p = sp._style_file_path("linestyle", n)
            got[f"linestyle-{n}"] = (None if p is None else
                                     "USER/" + os.path.relpath(p, d))
        assert got == {k: v for k, v in TRUTH["find"].items()
                       if "u44" in k}
        assert [x for _r, x in sp._style_walk()][:2] == [
            d, os.path.join(d, "style")]

    @needs_base
    def test_base_files(self):
        sp = SP("s2color", ado_dirs=(BASE,))
        for k, want in TRUTH["find"].items():
            if "u44" in k:
                continue
            c, n = k.split("-", 1)
            assert sp._style_file_path(c, n) == want, k

    def test_user_root_vs_style_dir(self, tmp_path):
        d = _walk_dir(tmp_path)
        rows = SP("s2color", ado_dirs=(d,))._style_file_rows("linestyle",
                                                             "u44c")
        assert rows == (("width", "literal", "thin"),)


# ---------------------------------------------------------------------------
# Every untranscribed name
# ---------------------------------------------------------------------------

_TOK = {"pstyle": ("series.marker", "series.line", "series.area"),
        "mstyle": ("marker",), "astyle": ("area",)}

#: Rows dash does not draw as twoway does, each for a reason.
_EXCLUDED: dict = {}


def _compare_draw():
    bad = []
    parsers: dict = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for rid, rec in sorted(TRUTH["draw"].items()):
            scheme, opt, name = rid.split("|")
            if (opt, name) in _EXCLUDED:
                continue
            sp = parsers.setdefault(scheme, SP(scheme, ado_dirs=(BASE,)))
            for tok in _TOK[opt]:
                role = tok.rsplit(".", 1)[-1]
                want = tsn._want(rec, role)
                b = sp.style_bundle(tok, name)
                got = tsn._got(b, role, want)
                # A #-pt symbolsize: .Graph's size.val is the points as
                # written (fpall's `symbolsize fpall 11-pt'), which dash
                # draws as points at the scheme's size reference.
                mrows = sp._style_rows("markerstyle", name) or ()
                skey = next((v for a, _k, v in mrows if a == "size"), name)
                raw = sp._props.get(f"@stata symbolsize {skey}", "")
                if role == "marker" and raw.endswith("-pt") and \
                        "size" in want:
                    want = dict(want, size=round(
                        rec["marker"]["size"] * 4.0 / 3.0 * 4.0
                        / sp.size_ref_in, 3))
                if got != want:
                    bad.append((rid, tok, want, got))
    return bad


@needs_base
class TestEveryKnownNameDraws:
    def test_every_record(self):
        bad = _compare_draw()
        assert not bad, "\n".join(map(str, bad[:30])) + f"\n({len(bad)})"

    def test_no_note(self):
        sp = SP("stcolor", ado_dirs=(BASE,))
        notes = tsn._notes(lambda: [sp.style_bundle(_TOK[o][0], n)
                                    for o, n in (("pstyle", "fpall"),
                                                 ("mstyle", "refmarker"),
                                                 ("astyle", "plotregion"))])
        assert not [n for n in notes if "named style" in n], notes

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn_in_both_modes(self, mode):
        rec = TRUTH["draw"]["stcolor|mstyle|refmarker"]
        rs, notes = _draw(plot_for("scatter", {"mstyle": "refmarker"}),
                          "stcolor", mode, (BASE,))
        g = tsn._one(rs, "Scatter")
        assert tsn._hex(g.fill_color) == rec["marker"]["fill"]
        assert not [n for n in notes if "named style" in n]


# ---------------------------------------------------------------------------
# User files
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestUserFiles:
    def test_drawn(self, mode, tmp_path):
        rec = TRUTH["user"]["s2color|lstyle|u44b"]["line"]
        assert (rec["color"], rec["width"], rec["pattern"]) == (
            "#ff0000", 0.8, "dash")
        d = _user_dir(tmp_path, {"style/linestyle-mine.style": U44B})
        rs, notes = _draw(plot_for("line", {"lstyle": "mine"}), "s2color",
                          mode, (d,))
        assert _red_line(tsn._one(rs, "Line")) == RED
        assert not [n for n in notes if "named style" in n], notes

    def test_a_user_seriesstyle(self, mode, tmp_path):
        """pstyle(u44p): `set line u44b' (a literal hop to a user file),
        `set marker scheme p2'."""
        rec = TRUTH["user"]["s2color|pstyle|u44p"]
        d = _user_dir(tmp_path, {
            "style/linestyle-u44b.style": U44B,
            "style/seriesstyle-u44p.style":
                "set marker scheme p2\nset line u44b\nset area scheme p3\n"})
        rs, _ = _draw(plot_for("connected", {"pstyle": "u44p"}), "s2color",
                      mode, (d,))
        assert _red_line(tsn._one(rs, "Line")) == RED
        assert tsn._hex(tsn._one(rs, "Scatter").fill_color) == \
            rec["marker"]["fill"]


# ---------------------------------------------------------------------------
# Hostile files
# ---------------------------------------------------------------------------

def _style_notes(fn):
    dr._dash_reset_notes()
    with warnings.catch_warnings(record=True) as got:
        warnings.simplefilter("always")
        out = fn()
    return out, [str(w.message) for w in got
                 if "style file" in str(w.message)
                 or "named style" in str(w.message)]


class TestHostileStyleFiles:
    def test_symlink_out(self, tmp_path):
        out = tmp_path / "outside.style"
        out.write_text(U44B, encoding="utf-8")
        d = tmp_path / "ado" / "style"
        d.mkdir(parents=True)
        os.symlink(out, d / "linestyle-u44x.style")
        sp = SP("s2color", ado_dirs=(str(tmp_path / "ado"),))
        b, notes = _style_notes(lambda: sp.style_bundle("line", "u44x"))
        assert b == sp.style_bundle("line", "foreground")
        assert len([n for n in notes if "u44x" in n]) == 1, notes
        # Asked again: memoised, no second note, no exception.
        _, again = _style_notes(lambda: sp.style_bundle("line", "u44x"))
        assert len([n for n in again if "style file" in n]) <= 1

    def test_two_mib(self, tmp_path):
        d = _user_dir(tmp_path, {"style/linestyle-big.style":
                                 U44B + "*" * (2 * 1024 * 1024) + "\n"})
        sp = SP("s2color", ado_dirs=(d,))
        b, notes = _style_notes(lambda: sp.style_bundle("line", "big"))
        assert b == sp.style_bundle("line", "foreground")
        assert [n for n in notes if "style file" in n]

    def test_ten_thousand_lines_are_cut(self, tmp_path):
        body = "*\n" * 9999 + "set color red\n"
        d = _user_dir(tmp_path, {"style/linestyle-long.style":
                                 "set width thick\n" + body})
        sp = SP("s2color", ado_dirs=(d,))
        rows = sp._style_file_rows("linestyle", "long")
        assert rows == (("width", "literal", "thick"),)

    def test_a_path_like_value_is_skipped(self, tmp_path):
        d = _user_dir(tmp_path, {"style/linestyle-pv.style":
                                 "set color ../../x\nset width thick\n"
                                 "set pattern scheme /etc/hosts\n"})
        rows = SP("s2color", ado_dirs=(d,))._style_file_rows("linestyle",
                                                             "pv")
        assert rows == (("width", "literal", "thick"),)

    def test_no_path_from_a_bad_name(self, tmp_path, monkeypatch):
        d = _walk_dir(tmp_path)
        asked = []
        real = os.listdir

        def spy(p="."):
            asked.append(str(p))
            return real(p)
        monkeypatch.setattr(os, "listdir", spy)
        sp = SP("s2color", ado_dirs=(d,))
        for bad in ("a/b", "../x", "a\\b", 'a"b', "a b", "x" * 100, ""):
            assert sp._style_file_path("linestyle", bad) is None
        assert sp._style_file_path("nosuchclass", "u44a") is None
        assert all(p.startswith(d) for p in asked), asked

    def test_swapped_after_check(self, tmp_path, monkeypatch):
        """A file swapped between _admit and the read is refused by the
        (dev, inode) check in _read_scheme_lines (A24)."""
        d = _user_dir(tmp_path, {"style/linestyle-sw.style": U44B})
        sp = SP("s2color", ado_dirs=(d,))
        real_admit = SP._admit

        def admit_then_swap(self, root, path, safe):
            out = real_admit(self, root, path, safe)
            os.replace(path, path + ".old")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("set color blue\n")
            return out
        monkeypatch.setattr(SP, "_admit", admit_then_swap)
        dr._DASH_STYLE_FILE_MEMO.clear()
        rows, notes = _style_notes(lambda: sp._style_file_rows("linestyle",
                                                               "sw"))
        assert rows is None
        assert [n for n in notes if "changed after it was checked" in n]


# ---------------------------------------------------------------------------
# The memo
# ---------------------------------------------------------------------------

def _count_reads(monkeypatch):
    seen = []
    real = SP._read_scheme_lines.__func__

    def spy(cls, path, *a, **k):
        seen.append(os.path.basename(path))
        return real(cls, path, *a, **k)
    monkeypatch.setattr(SP, "_read_scheme_lines", classmethod(spy))
    return seen


class TestTheReaderIsMemoised:
    def test_one_read_per_file(self, tmp_path, monkeypatch):
        d = _user_dir(tmp_path, {"style/linestyle-m1.style": U44B})
        dr._DASH_STYLE_FILE_MEMO.clear()
        seen = _count_reads(monkeypatch)
        sp = SP("s2color", ado_dirs=(d,))
        for _ in range(5):
            sp._style_file_rows("linestyle", "m1")
        assert seen.count("linestyle-m1.style") == 1

    def test_second_parser_reads_nothing(self, tmp_path, monkeypatch):
        d = _user_dir(tmp_path, {"style/linestyle-m2.style": U44B})
        dr._DASH_STYLE_FILE_MEMO.clear()
        SP("s2color", ado_dirs=(d,))._style_file_rows("linestyle", "m2")
        seen = _count_reads(monkeypatch)
        SP("s2color", ado_dirs=(d,))._style_file_rows("linestyle", "m2")
        assert "linestyle-m2.style" not in seen

    def test_modified_file_is_reread(self, tmp_path, monkeypatch):
        d = _user_dir(tmp_path, {"style/linestyle-m3.style": U44B})
        dr._DASH_STYLE_FILE_MEMO.clear()
        assert ("color", "literal", "red") in SP(
            "s2color", ado_dirs=(d,))._style_file_rows("linestyle", "m3")
        p = os.path.join(d, "style", "linestyle-m3.style")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("set color blue\nset width thin\n")
        os.utime(p, (time.time() + 5, time.time() + 5))
        assert SP("s2color", ado_dirs=(d,))._style_file_rows(
            "linestyle", "m3") == (("color", "literal", "blue"),
                                   ("width", "literal", "thin"))

    def test_bounded(self):
        assert SP._STYLE_FILE_MEMO_MAX == 400


# ---------------------------------------------------------------------------
# Directives
# ---------------------------------------------------------------------------

def _scheme_dir(tmp_path, lines, files=None):
    f = {"scheme-u44x.scheme": "\n".join(["#include s2color"] + lines)
         + "\n"}
    f.update(files or {})
    return _user_dir(tmp_path, f)


@pytest.mark.parametrize("mode", MODES)
class TestDirectives:
    def test_redefines(self, mode, tmp_path):
        """`linestyle ci u44b': pstyle(ci)'s line hops to the user file
        (twoway: red, .8, dash)."""
        rec = TRUTH["scheme"]["u44h|ci"]["line"]
        assert (rec["color"], rec["pattern"]) == ("#ff0000", "dash")
        d = _scheme_dir(tmp_path, ["linestyle ci u44b"],
                        {"style/linestyle-u44b.style": U44B})
        rs, notes = _draw(plot_for("line", {"pstyle": "ci"}), "u44x", mode,
                          (d,))
        assert _red_line(tsn._one(rs, "Line")) == RED
        assert not [n for n in notes if "named style" in n], notes

    def test_missing_notes_as_twoway(self, mode, tmp_path):
        """A directive naming no file: twoway's note once, the class
        default drawn (scheme u44m)."""
        want = TRUTH["scheme"]["u44m|scatter"]["notes"]
        assert want == ["(note: named style nosuch not found in class "
                        "linestyle, default attributes used)"]
        d = _scheme_dir(tmp_path, ["linestyle ci nosuch"])
        rs, notes = _draw(plot_for("line", {"pstyle": "ci"}), "u44x", mode,
                          (d,))
        assert [n for n in notes if "named style" in n] == [
            "dash: " + want[0][len("(note: "):-1]]

    def test_shadestyle(self, mode, tmp_path):
        """`shadestyle ci u44s' redefines astyle(ci)'s fill side (u44s:
        red at inten50, as twoway draws scheme u44s's area)."""
        rec = TRUTH["scheme"]["u44s|area"]["area"]
        assert (rec["fill"], rec["intensity"]) == ("#ff0000", 50.0)
        d = _scheme_dir(tmp_path, ["shadestyle ci u44s"], {
            "style/shadestyle-u44s.style":
                "set color red\nset intensity inten50\n"})
        rs, _ = _draw(plot_for("area", {"astyle": "ci"}), "u44x", mode,
                      (d,))
        assert tsn._hex(tsn._one(rs, "VArea").fill_color) == \
            dr.GlyphMapper._blend_intensity("#ff0000", 0.5)


# ---------------------------------------------------------------------------
# The fallback and both modes
# ---------------------------------------------------------------------------

class TestTheFallback:
    def test_table_when_no_files(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        a, b = SP("s2color", ado_dirs=(str(empty),)), SP("s2color")
        bad = []
        for c, tok in (("linestyle", "line"), ("markerstyle", "marker"),
                       ("areastyle", "area")):
            for f in SP._STYLE_TABLE[c]:
                n = f.replace("#", "3")
                if a.style_bundle(tok, n) != b.style_bundle(tok, n):
                    bad.append((tok, n))
        assert not bad
        for i in range(1, 16):
            assert a.style_bundle("line", f"p{i}") == \
                b.style_bundle("line", f"p{i}")


class TestBothModesReadTheSameFile:
    @pytest.mark.parametrize("mode", MODES)
    def test_paths(self, mode, tmp_path):
        d = _user_dir(tmp_path, {"style/linestyle-mine.style": U44B})
        rs, _ = _draw(plot_for("line", {"lstyle": "mine"}), "s2color", mode,
                      (d,))
        assert _red_line(tsn._one(rs, "Line")) == RED

    @pytest.mark.parametrize("mode", MODES)
    def test_served_without_files_draws_embedded_rows(self, mode, tmp_path):
        d = _user_dir(tmp_path, {"style/linestyle-mine.style": U44B})
        spec = tp._spec([plot_for("line", {"lstyle": "mine"})],
                        {"scheme": "s2color"})
        rows = SP.style_rows_for_spec(spec, (d,))
        assert rows == {"linestyle mine": [["width", "literal", "thick"],
                                           ["color", "literal", "red"],
                                           ["pattern", "literal", "dash"]]}
        empty = tmp_path / "empty"
        empty.mkdir()
        rs, notes = _draw(plot_for("line", {"lstyle": "mine"}), "s2color",
                          mode, (str(empty),), {"_style_rows": rows})
        assert _red_line(tsn._one(rs, "Line")) == RED
        assert not [n for n in notes if "named style" in n], notes

    def test_the_spec_text_gains_the_rows(self, tmp_path):
        """dash.ado's writers hand the spec text (its last } still to
        come) through _dash_embed_style_rows."""
        d = _user_dir(tmp_path, {"style/linestyle-mine.style": U44B})
        spec = tp._spec([plot_for("line", {"lstyle": "mine"})],
                        {"scheme": "s2color", "scheme_dirs": [d]})
        text = json.dumps(spec)[:-1]
        out = json.loads(dr._dash_embed_style_rows(text) + "}")
        assert out["build_options"]["_style_rows"]["linestyle mine"][1] == \
            ["color", "literal", "red"]
        # Nothing to embed, or text that is not a spec: unchanged.
        plain = json.dumps(tp._spec([plot_for("line")], {}))[:-1]
        assert dr._dash_embed_style_rows(plain) == plain
        assert dr._dash_embed_style_rows("{not json") == "{not json"

    def test_bad_embedded_rows_are_dropped(self):
        got = dr._dash_style_rows_of({"_style_rows": {
            "linestyle ok": [["color", "literal", "red"]],
            "linestyle ../x": [["color", "literal", "red"]],
            "nosuch ok": [["color", "literal", "red"]],
            "linestyle bad": [["color", "literal", "a/b"]],
            "linestyle many": [["color", "literal", "red"]] * 500}})
        assert got == {"linestyle ok": (("color", "literal", "red"),)}


@needs_base
class TestCost:
    def test_under_50ms_per_render(self):
        SP("stcolor", ado_dirs=(BASE,)).style_bundle("series.line", "fpall")
        t0 = time.perf_counter()
        for _ in range(5):
            sp = SP("stcolor", ado_dirs=(BASE,))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                for o, n in (("series.marker", "fpall"),
                             ("series.line", "fpall"),
                             ("marker", "refmarker"),
                             ("area", "plotregion")):
                    sp.style_bundle(o, n)
        assert (time.perf_counter() - t0) / 5 < 0.05 + 0.2


class TestAdoArchive:
    def test_measured_branch(self, tmp_path):
        """c(adoarchive) does not exist in StataNow 19.5 (r(133)), so
        dash.ado writes "" and nothing is noted; a "1" would be named
        once, the table drawn."""
        assert TRUTH["adoarchive"]["c_rc"] == 133
        _, notes = _draw(plot_for("line", {"lstyle": "refline"}), "s2color",
                         "standalone", (), {"adoarchive": "1"})
        assert [n for n in notes if "compressed ado archive" in n] == [
            "dash: style files inside a compressed ado archive are not "
            "read; dash's transcribed styles are drawn"]
        _, notes = _draw(plot_for("line", {"lstyle": "refline"}), "s2color",
                         "standalone", (), {"adoarchive": ""})
        assert not [n for n in notes if "compressed ado archive" in n]
