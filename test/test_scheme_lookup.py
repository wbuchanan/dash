"""Stata's scheme lookup along the ado-path (WP-30 P1.25b, section 34) and
each graph's own scheme in both renderers (P1.25.6).

Measured (research p1-25 at c96facd, section 34's probes, StataNow 19.5):

* Stata's setscheme runs ``findfile scheme-NAME.scheme`` and then
  ``findfile NAME.scheme`` (BASE/s/scheme.class:172-173).  Each walks the
  ado-path directory by directory, every directory followed by its
  subdirectory named by the file name's first character: an earlier
  directory's letter subdirectory beats a later directory, a directory
  beats its own subdirectory, SITE's subdirectory beats the working
  directory, and the walk is form-major (``scheme-w34q.scheme`` in a later
  ``adopath +`` directory beats ``w34q.scheme`` in the working directory).
  test/fixtures/scheme_lookup_truth.json holds 22 such placements
  (scripts/extract_scheme_lookup_truth.do).
* dash looked in two places only: ``dash scatter mpg weight, scheme(w30x)``
  with ``scheme-w30x.scheme`` in the working directory was refused r(198)
  where twoway draws it red; after ``set scheme`` of a scheme on an added
  ado-path directory an unschemed dashboard was drawn s2color (#eaf2f3)
  with a warning; a working-directory ``s1mono.scheme`` replaced the
  shipped s1mono, which twoway never allows.
* E7: a graph-level ``scheme(mono)`` drew the saved figure s2color
  (border #eaf2f3) with a false "not found" note, the served one s1mono.
* E8: ``g1 scheme(s1mono)`` with ``g2 scheme(s1rcolor)`` drew #ffffff and
  #000000 saved but #ffffff and #ffffff served, and both modes warned
  that a dashboard draws one scheme.
"""

import json
import os
import sys
import time
import warnings

import pytest
from bokeh.models import Plot

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import _served as _served_mod  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = ("standalone", "served")
R = "#include s2color\ncolor background red\ncolor p1 green\n"
B = R.replace("red", "blue")
RED = "#ff0000"
FIXTURE = os.path.join(_HERE, "fixtures", "scheme_lookup_truth.json")
_ORDER = ("base", "site", "cwd", "personal", "plus", "oldplace", "add")


def _bg(name):
    return dr.SchemeParser(name).background_color


@pytest.fixture
def ado(tmp_path, monkeypatch):
    """A tmp ado-path: base/, site/, cwd/ (the working directory),
    personal/, plus/, oldplace/, add/, and outside/, which is on no path."""
    d = {k: tmp_path / k for k in _ORDER + ("outside",)}
    for p in d.values():
        p.mkdir()
    monkeypatch.chdir(d["cwd"])
    return d


def _dirs(ado):
    return [str(ado[k]) for k in _ORDER]


def _spec(ado, bo=None, go=None, graphs=None):
    bo = dict(bo or {})
    bo["scheme_dirs"] = _dirs(ado)
    if graphs is not None:
        return tp._spec(None, bo, None, graphs)
    return tp._spec([plot_for("scatter")], bo, go or {})


def _draw(spec, mode):
    """(figure borders in graph order, warnings) in *mode*."""
    if mode == "standalone":
        r, msgs = tp._standalone(spec)
        return [f.border_fill_color for f in r.figures.values()], msgs
    doc, msgs = tp._served(spec)
    return [p.border_fill_color for p in _plots_in_order(doc)], msgs


def _plots_in_order(doc):
    """The served document's figures in layout order."""
    out, seen = [], set()

    def visit(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                visit(x)
            return
        if not hasattr(m, "properties") or id(m) in seen:
            return
        seen.add(id(m))
        if isinstance(m, Plot):
            out.append(m)
            return
        for a in ("children", "tabs", "child"):
            k = getattr(m, a, None)
            if k is not None:
                visit(k)

    for r in doc.roots:
        visit(r)
    return out


def _scheme_msgs(msgs):
    return [m for m in msgs if "scheme" in m]


def _spy_open(monkeypatch):
    """Every file dash_render opens: [realpath, [read sizes]]."""
    import builtins
    record = []
    real_open = builtins.open

    class _F:
        def __init__(self, fh, sizes):
            self._fh, self._sizes = fh, sizes

        def read(self, n=-1):
            self._sizes.append(n)
            return self._fh.read(n)

        def __getattr__(self, a):
            return getattr(self._fh, a)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return self._fh.__exit__(*a)

    def spy(path, *a, **k):
        sizes = []
        record.append((os.path.realpath(str(path)), sizes))
        return _F(real_open(path, *a, **k), sizes)

    monkeypatch.setattr(dr, "open", spy, raising=False)
    return record


# ---------------------------------------------------------------------------
# Stata's file name, on every entry point
# ---------------------------------------------------------------------------

class TestStatasFileName:
    @pytest.mark.parametrize("mode", MODES)
    def test_a_prefixed_file_is_found_in_both_modes(self, ado, mode):
        (ado["add"] / "scheme-w34x.scheme").write_text(R)
        borders, msgs = _draw(_spec(ado, {"scheme": "w34x"}), mode)
        assert borders == [RED] and not _scheme_msgs(msgs), (borders, msgs)

    @pytest.mark.parametrize("mode", MODES)
    def test_a_graph_level_name_is_found(self, ado, mode):
        (ado["add"] / "scheme-w34x.scheme").write_text(R)
        borders, msgs = _draw(_spec(ado, go={"scheme": "w34x"}), mode)
        assert borders == [RED] and not _scheme_msgs(msgs), (borders, msgs)

    @pytest.mark.parametrize("mode", MODES)
    def test_the_session_scheme_is_found(self, ado, mode):
        (ado["add"] / "scheme-w34x.scheme").write_text(R)
        borders, msgs = _draw(_spec(ado, {"session_scheme": "w34x"}), mode)
        assert borders == [RED] and not _scheme_msgs(msgs), (borders, msgs)

    def test_the_name_is_statas_not_the_file_name(self, ado):
        (ado["add"] / "scheme-w34x.scheme").write_text(R)
        assert dr.SchemeParser("w34x", ado_dirs=_dirs(ado)).name == "w34x"


# ---------------------------------------------------------------------------
# The walk, against twoway's measured placements
# ---------------------------------------------------------------------------

def _fixture():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _recreate(root, rec):
    """Build *rec*'s files under *root*; return its ado-path as dash reads
    it (REPO and BASE are empty directories, . is cwd, a relative entry
    is joined to cwd unless the case made it under the root)."""
    for k in ("cwd", "_repo", "_base"):
        (root / k).mkdir(parents=True, exist_ok=True)
    for rel, kind in rec["files"].items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if kind.startswith("->"):
            os.symlink(str(root / kind[2:]), str(p))
        else:
            p.write_text({"R": R, "B": B}.get(kind, kind))
    words = {"REPO": "_repo", "BASE": "_base", "SITE": "site",
             "PERSONAL": "personal", "PLUS": "plus", "OLDPLACE": "oldplace",
             ".": "cwd"}
    out = []
    for e in rec["adopath"]:
        if e in words:
            out.append(str(root / words[e]))
        elif (root / e).is_dir():
            out.append(str(root / e))
        else:
            out.append(str(root / "cwd" / e))
    return dr._dash_scheme_dirs_of({"scheme_dirs": out})


class TestTheWalkIsStatas:
    def test_the_fixture_is_stamped(self):
        d = _fixture()
        # Flipped: WP-32 regenerated the fixture; its generator now writes source.
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source", "stata_version"]
        assert len([k for k in d if k != "_meta"]) == 22

    def test_each_measured_placement(self, tmp_path, monkeypatch):
        """Every record: dash resolves the file findfile returned, except
        lk16 (a shipped name: dash's translation) and lk19 (a link out of
        its directory: refused); lk20 is found nowhere.  The colours drawn
        are twoway's."""
        bad = []
        for key, rec in sorted(_fixture().items()):
            if key == "_meta":
                continue
            root = tmp_path / key
            dirs = _recreate(root, rec)
            monkeypatch.chdir(root / "cwd")
            name = rec["name"]
            probe = dr.SchemeParser.__new__(dr.SchemeParser)
            probe._ado_dirs = dirs
            try:
                got = probe._resolve_path(name)
            except ValueError as exc:
                got = exc
            if key == "lk19":
                if not (isinstance(got, ValueError) and "symlink" in str(got)):
                    bad.append((key, got))
                continue
            if key == "lk20":
                if not (isinstance(got, ValueError) and "not found" in str(got)):
                    bad.append((key, got))
                continue
            if isinstance(got, ValueError):
                bad.append((key, str(got)))
                continue
            if key == "lk16":
                want = "dash-s1mono.scheme"
                if os.path.basename(got) != want:
                    bad.append((key, got))
            else:
                rel = rec["findfile_rel"]
                want = os.path.realpath(str(root / rel))
                if os.path.realpath(got) != want:
                    bad.append((key, got, rel))
            sch = dr.SchemeParser(name, ado_dirs=dirs)
            if sch.background_color.lower() != rec["twoway_bg"].lower():
                bad.append((key, "bg", sch.background_color, rec["twoway_bg"]))
            if key == "lk17" and \
                    sch.p_colors[0].lower() != rec["twoway_marker"].lower():
                bad.append((key, "marker", sch.p_colors[0],
                            rec["twoway_marker"]))
        assert not bad, bad


class TestShippedNamesComeFirst:
    def test_a_working_directory_file_never_replaces_a_shipped_scheme(
            self, tmp_path, monkeypatch):
        """Each spelling of a working-directory file named like s2color, in
        a fresh directory; every spelling of the name, with and without an
        ado-path, reads the shipped dash-s2color.scheme.  (Rendered in both
        modes by test_help_claims_8's TestAWorkingDirectorySchemeWinsOver
        AShippedOne.)"""
        bad = []
        for i, fname in enumerate(("s2color.scheme", "scheme-s2color.scheme",
                                   "S2COLOR.scheme")):
            wd = tmp_path / str(i)
            wd.mkdir()
            (wd / fname).write_text(R)
            monkeypatch.chdir(wd)
            for dirs in ((), (str(wd),)):
                for name in ("s2color", "s2color.scheme", "S2COLOR.scheme"):
                    p = dr.SchemeParser.__new__(dr.SchemeParser)
                    p._ado_dirs = dirs
                    got = os.path.basename(p._resolve_path(name))
                    if got != "dash-s2color.scheme":
                        bad.append((fname, dirs, name, got))
        assert not bad, bad


# ---------------------------------------------------------------------------
# #include
# ---------------------------------------------------------------------------

class TestIncludeWalksTheAdoPath:
    @pytest.mark.parametrize("mode", MODES)
    def test_an_include_of_a_prefixed_file(self, ado, mode):
        (ado["cwd"] / "mine.scheme").write_text("#include w34p\n")
        (ado["add"] / "scheme-w34p.scheme").write_text(R)
        borders, msgs = _draw(_spec(ado, {"scheme": "mine"}), mode)
        assert borders == [RED] and not _scheme_msgs(msgs), (borders, msgs)

    @pytest.mark.parametrize("mode", MODES)
    def test_an_include_nowhere_still_notes_once(self, ado, mode):
        (ado["cwd"] / "mine.scheme").write_text("#include w34nowhere\n")
        borders, msgs = _draw(_spec(ado, {"scheme": "mine"}), mode)
        notes = [m for m in msgs if "w34nowhere not found" in m]
        assert borders == [_bg("s2color")] and len(notes) == 1, msgs


# ---------------------------------------------------------------------------
# Theme names (P1.25.5)
# ---------------------------------------------------------------------------

class TestThemeNamesAndFiles:
    @pytest.mark.parametrize("mode", MODES)
    def test_an_inherited_theme_named_file_is_the_file(self, ado, mode):
        (ado["add"] / "scheme-mono.scheme").write_text(R)
        borders, msgs = _draw(_spec(ado, {"session_scheme": "mono"}), mode)
        assert borders == [RED] and not _scheme_msgs(msgs), (borders, msgs)

    @pytest.mark.parametrize("mode", MODES)
    def test_an_explicit_alias_loses_to_a_file(self, ado, mode):
        (ado["add"] / "scheme-mono.scheme").write_text(R)
        borders, msgs = _draw(_spec(ado, {"scheme": "mono"}), mode)
        assert borders == [RED] and not _scheme_msgs(msgs), (borders, msgs)

    @pytest.mark.parametrize("mode", MODES)
    def test_an_explicit_alias_without_a_file_is_the_alias(self, ado, mode):
        borders, msgs = _draw(_spec(ado, {"scheme": "mono"}), mode)
        assert borders == [_bg("s1mono")] and not _scheme_msgs(msgs), msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_a_graph_level_alias_is_the_alias_in_both_modes(self, ado, mode):
        borders, msgs = _draw(_spec(ado, go={"scheme": "mono"}), mode)
        assert borders == [_bg("s1mono")] and not _scheme_msgs(msgs), msgs


# ---------------------------------------------------------------------------
# The read guards (G9)
# ---------------------------------------------------------------------------

class TestTheGuards:
    def test_a_link_out_of_its_directory_is_not_read(self, ado, monkeypatch):
        (ado["outside"] / "x.scheme").write_text(R)
        os.symlink(str(ado["outside"] / "x.scheme"),
                   str(ado["add"] / "scheme-w34y.scheme"))
        record = _spy_open(monkeypatch)
        with pytest.raises(ValueError, match="symlink"):
            dr.SchemeParser("w34y", ado_dirs=_dirs(ado))
        assert record == [], record

    def test_a_file_over_the_cap_is_not_read(self, ado):
        (ado["add"] / "scheme-w34b.scheme").write_bytes(
            b"#include s2color\n" + b"*" * (1_048_577 - 17))
        assert os.path.getsize(ado["add"] / "scheme-w34b.scheme") == 1_048_577
        with pytest.raises(ValueError, match="larger than 1,048,576 bytes"):
            dr.SchemeParser("w34b", ado_dirs=_dirs(ado))

    def test_the_read_stops_at_the_cap(self, ado, monkeypatch):
        f = ado["add"] / "scheme-w34c.scheme"
        f.write_text(R)
        real_getsize = os.path.getsize

        def grow(p):
            n = real_getsize(p)
            if os.path.basename(str(p)) == "scheme-w34c.scheme":
                with open(str(f), "ab") as fh:
                    fh.write(b"*" * (2 * 1_048_576))
            return n

        monkeypatch.setattr(os.path, "getsize", grow)
        record = _spy_open(monkeypatch)
        with pytest.raises(ValueError, match="larger than"):
            dr.SchemeParser("w34c", ado_dirs=_dirs(ado))
        sizes = [n for _p, s in record for n in s]
        assert sizes and all(0 <= n <= 1_048_577 for n in sizes), sizes

    def test_a_swap_after_the_check_is_not_read(self, ado, monkeypatch):
        f = ado["add"] / "scheme-w34s.scheme"
        f.write_text(R)
        (ado["outside"] / "x.scheme").write_text(B)
        real_getsize = os.path.getsize

        def swap(p):
            n = real_getsize(p)
            if os.path.basename(str(p)) == "scheme-w34s.scheme" \
                    and not os.path.islink(str(f)):
                os.remove(str(f))
                os.symlink(str(ado["outside"] / "x.scheme"), str(f))
            return n

        monkeypatch.setattr(os.path, "getsize", swap)
        record = _spy_open(monkeypatch)
        with pytest.raises(ValueError, match="changed after it was checked"):
            dr.SchemeParser("w34s", ado_dirs=_dirs(ado))
        outside = os.path.realpath(str(ado["outside"] / "x.scheme"))
        assert not [s for p, s in record if p == outside and s], record

    def test_a_fifo_is_not_opened(self, ado):
        os.mkfifo(str(ado["add"] / "scheme-w34f.scheme"))
        t0 = time.monotonic()
        with pytest.raises(ValueError, match="not a regular file"):
            dr.SchemeParser("w34f", ado_dirs=_dirs(ado))
        assert time.monotonic() - t0 < 2

    def test_a_directory_named_like_a_scheme_is_not_read(self, ado):
        (ado["add"] / "scheme-w34d.scheme").mkdir()
        with pytest.raises(ValueError, match="not a regular file"):
            dr.SchemeParser("w34d", ado_dirs=_dirs(ado))

    def test_a_link_inside_its_directory_is_read(self, ado):
        (ado["add"] / "real.scheme").write_text(R)
        os.symlink(str(ado["add"] / "real.scheme"),
                   str(ado["add"] / "scheme-w34i.scheme"))
        sch = dr.SchemeParser("w34i", ado_dirs=_dirs(ado))
        assert sch.background_color == RED

    def test_scheme_dirs_input_is_bounded(self, tmp_path):
        good = [tmp_path / ("d%d" % i) for i in range(3)]
        for g in good:
            g.mkdir()
        afile = tmp_path / "f"
        afile.write_text("x")
        f = dr._dash_scheme_dirs_of
        for raw in ("a string", None, 7, {"a": 1}, ("tuple",)):
            assert f({"scheme_dirs": raw}) == ()
        assert f(None) == () and f("x") == ()
        many = [str(good[0])] * 1000
        assert f({"scheme_dirs": many}) == (os.path.realpath(str(good[0])),)
        mixed = ["x" * 5000, str(good[0]) + "\x00b", "relative/dir",
                 str(tmp_path / "missing"), str(afile), 3, "",
                 str(good[1]), str(good[0]), str(good[1]), str(good[2])]
        assert f({"scheme_dirs": mixed}) == tuple(
            os.path.realpath(str(g)) for g in (good[1], good[0], good[2]))
        home = f({"scheme_dirs": ["~"]})
        assert home == (os.path.realpath(os.path.expanduser("~")),)
        # 64 entries are read; the 65th is not.
        sixty = [tmp_path / ("e%02d" % i) for i in range(70)]
        for g in sixty:
            g.mkdir()
        assert len(f({"scheme_dirs": [str(g) for g in sixty]})) == 64

    def test_the_directories_never_reach_the_page_or_the_app(self, tmp_path,
                                                             monkeypatch):
        import base64
        import re
        mark = tmp_path / "zz_s34_dirmark"
        mark.mkdir()
        monkeypatch.chdir(tmp_path)
        spec = tp._spec([plot_for("scatter")],
                        {"scheme_dirs": [str(mark)]}, {})
        _r, _w, page = tp._standalone_page(spec)
        tag, sp, dp = tp._write(spec)
        ap = os.path.join(tp._TMP, "app_%s.py" % tag)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            app = fh.read()
        blobs = re.findall(r'_SPEC_B64 = "([A-Za-z0-9+/=]*)"', app)
        app += "".join(base64.b64decode(b).decode("utf-8") for b in blobs)
        assert "zz_s34_dirmark" not in page
        assert "zz_s34_dirmark" not in app

    def test_a_session_scheme_refused_by_a_guard_says_why(self, ado):
        (ado["outside"] / "x.scheme").write_text(R)
        os.symlink(str(ado["outside"] / "x.scheme"),
                   str(ado["add"] / "scheme-w34y.scheme"))
        spec = {"graphs": [], "build_options": {"session_scheme": "w34y"}}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            name = dr._resolve_scheme_name(spec, tuple(_dirs(ado)))
        msgs = [str(w.message) for w in caught]
        assert name == "s2color"
        assert len(msgs) == 1 and "was found but not read" in msgs[0], msgs

    def test_hostile_directives_are_data(self, ado, monkeypatch):
        import builtins
        import subprocess
        hostile = ("#include s2color\n#delimit ;\nprogram define x\n"
                   "shell rm -rf /\n`=exec(\"1\")'\npython: import os\n"
                   "color p1 <script>alert(1)</script>\n"
                   "color background \"</style><script>\"\n"
                   + " ".join(["x"] * 10000) + "\n\x00\x00color p2 red\x00\n")
        (ado["add"] / "scheme-w34h.scheme").write_text(hostile)
        spec = _spec(ado, {"scheme": "w34h"})

        marks = ("rm -rf", "alert(1)", 'exec("1")', "program define x",
                 "import os")

        def guard(real):
            # Imports run exec on their own code objects; only the scheme
            # file's text reaching one of these is code execution.
            def call(*a, **k):
                flat = []
                for x in a:
                    flat += list(x) if isinstance(x, (list, tuple)) else [x]
                text = " ".join(x for x in flat if isinstance(x, str))
                if any(t in text for t in marks):
                    raise AssertionError("a scheme file ran code: %r"
                                         % text[:80])
                return real(*a, **k)
            return call

        with monkeypatch.context() as m:
            for obj, attr in ((subprocess, "Popen"), (os, "system"),
                              (builtins, "exec"), (builtins, "eval")):
                m.setattr(obj, attr, guard(getattr(obj, attr)))
            _r, _w, page = tp._standalone_page(spec)
            tag, sp, dp = tp._write(spec)
            ap = os.path.join(tp._TMP, "app_%s.py" % tag)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            app = fh.read()
        doc, _mod, _msgs = _served_mod(spec)
        assert "<script>alert" not in page
        # The app carries the parsed directives as data (S33's D-33d): only
        # inside the %r literal of a property dict, never in the document
        # it serves.
        assert all(ln.startswith(("_SCHEME_PROPS = ",
                                  "_GRAPH_SCHEME_PROPS = "))
                   for ln in app.splitlines() if "<script>alert" in ln)
        assert "<script>alert" not in str(doc.to_json())

    def test_hostile_include_names_read_nothing_outside(self, ado,
                                                        monkeypatch):
        (ado["outside"] / "x.scheme").write_text(R)
        names = ("../../outside/x", "/etc/hosts", "a:b", "add/..")
        (ado["add"] / "scheme-w34n.scheme").write_text(
            "".join("#include %s\n" % n for n in names))
        record = _spy_open(monkeypatch)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr.SchemeParser("w34n", ado_dirs=_dirs(ado))
        allowed = [os.path.realpath(str(ado[k])) for k in _ORDER]
        allowed.append(os.path.realpath(_ROOT))
        outside = [p for p, _s in record
                   if not any(p.startswith(a + os.sep) for a in allowed)]
        assert outside == [], outside
        msgs = [str(w.message) for w in caught]
        for n in names:
            assert len([x for x in msgs
                        if "'#include %s'" % n in x]) == 1, (n, msgs)


# ---------------------------------------------------------------------------
# The name rule and the refusal
# ---------------------------------------------------------------------------

class TestTheNameRule:
    def test_the_parser_reads_the_name_rule(self):
        ok = ("w30x", "w30-h", "_GRSTYLE_", "9x", "a+b", ".x", "-x", "x.y",
              "grün", "x.SCHEME")
        refused = ("a b", "a/b", "a\\b", "a:b", "..", "a..b", 'a"b',
                   "a\x60b", "a$b", "\x01", "\x85", "x" * 88, "")
        P = dr.SchemeParser
        bad = [n for n in ok if not P._scheme_name_ok(n)]
        bad += [n for n in refused if P._scheme_name_ok(n)]
        bad += [n for n in refused if n.strip() and "never given as a path"
                not in P.unresolved_reason(n)]
        assert not bad, bad


class TestTheRefusalNamesTheSchemes:
    def test_the_help_shows_the_new_refusal(self):
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            text = " ".join(fh.read().split())
        want = ("dash build: scheme() must be one of "
                + ", ".join(sorted(dr.SchemeParser._BUILTIN_NAMES))
                + "; a theme (clean, dark, default, economist, mono, sj); or "
                "a scheme Stata finds along the ado-path as "
                "scheme-NAME.scheme or NAME.scheme (got: nosuchthing)")
        assert want in text


# ---------------------------------------------------------------------------
# Third-party schemes (S30's colour reader; S33's D-33d)
# ---------------------------------------------------------------------------

class TestThirdPartySchemes:
    def test_a_plus_layout_is_found(self, ado):
        (ado["plus"] / "s").mkdir()
        (ado["plus"] / "s" / "scheme-w34t.scheme").write_text(
            '#include s2mono\ncolor p2 "0 114 178"\n')
        sch = dr.SchemeParser("w34t", ado_dirs=_dirs(ado))
        want = dr.OptionTranslator.stata_colour("0 114 178",
                                                context="scheme")[1]
        assert sch.p_colors[1].lower() == want.lower()

    @pytest.mark.parametrize("mode", MODES)
    def test_an_ado_path_schemes_unread_directives_are_kept_silently(
            self, ado, mode):
        (ado["plus"] / "s").mkdir()
        (ado["plus"] / "s" / "scheme-w34u.scheme").write_text(
            "#include s2color\nclockdir p 9\ntextboxstyle tick heading\n")
        spec = _spec(ado, {"scheme": "w34u"})
        if mode == "standalone":
            r, msgs = tp._standalone(spec)
            props = r.scheme._props
        else:
            _doc, mod, msgs = _served_mod(spec)
            props = mod._SCHEME_PROPS
        assert props.get("clockdir p") == "9"
        assert props.get("textboxstyle tick") == "heading"
        assert not [m for m in msgs if m.startswith("dash scheme:")], msgs


class TestTheWalkStaysFast:
    def test_256_unresolvable_includes_over_64_dirs(self, tmp_path,
                                                    monkeypatch):
        dirs = []
        for i in range(64):
            d = tmp_path / ("d%02d" % i)
            d.mkdir()
            dirs.append(str(d))
        (tmp_path / "d00" / "scheme-w34w.scheme").write_text(
            "".join("#include nowhere%03d\n" % i for i in range(256)))
        monkeypatch.chdir(tmp_path)
        t0 = time.monotonic()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr.SchemeParser("w34w", ado_dirs=dirs)
        assert time.monotonic() - t0 < 2
        notes = [w for w in caught if "#include" in str(w.message)]
        assert len(notes) <= 11, len(notes)


# ---------------------------------------------------------------------------
# P1.25.6: each graph in its own scheme, in both renderers
# ---------------------------------------------------------------------------

_TWO = [("g1", [plot_for("scatter")], {"scheme": "s1mono"}),
        ("g2", [plot_for("scatter")], {"scheme": "s1rcolor"})]
_DRAWN = {}


def _two(mode):
    if mode not in _DRAWN:
        _DRAWN[mode] = _draw(tp._spec(graphs=_TWO), mode)
    return _DRAWN[mode]


class TestPerGraphSchemes:
    @pytest.mark.parametrize("mode", MODES)
    def test_each_graph_is_drawn_in_its_own_scheme(self, mode):
        borders, _msgs = _two(mode)
        assert borders == [_bg("s1mono"), _bg("s1rcolor")], borders

    @pytest.mark.parametrize("mode", MODES)
    def test_no_one_scheme_warning(self, mode):
        _borders, msgs = _two(mode)
        assert not [m for m in msgs if "draws one scheme" in m], msgs

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("bo, other", [
        ({"session_scheme": "stcolor"}, "stcolor"),
        ({"session_scheme": "stcolor", "scheme": "s1mono"}, "s1mono")],
        ids=["session", "build_scheme"])
    def test_a_graphs_scheme_draws_that_graph_only(self, mode, bo, other):
        """scheme() on one graph draws that graph and no other: a graph
        that names none is drawn in dash build's scheme(), else the
        session's c(scheme), whichever graph comes first.  Before, the
        first graph's scheme() was every unschemed graph's -- one example's
        scheme(economist) drew the gallery's scatter-3 page square."""
        alone, _m = _draw(tp._spec([plot_for("scatter")], dict(bo), {}), mode)
        for graphs in ([("g1", [plot_for("scatter")], {"scheme": "economist"}),
                        ("g2", [plot_for("scatter")], {})],
                       [("g1", [plot_for("scatter")], {}),
                        ("g2", [plot_for("scatter")], {"scheme": "economist"})]):
            borders, _m = _draw(tp._spec(None, dict(bo), None, graphs), mode)
            want = [_bg("economist") if g[2] else _bg(other) for g in graphs]
            assert borders == want, (graphs, borders)
            assert alone == [_bg(other)]
        if mode == "standalone":
            spec = tp._spec(None, dict(bo), None,
                            [("g1", [plot_for("scatter")], {"scheme": "economist"}),
                             ("g2", [plot_for("scatter")], {})])
            r, _m = tp._standalone(spec)
            sizes = [round(f.aspect_ratio, 3) for f in r.figures.values()]
            r1, _m = tp._standalone(tp._spec([plot_for("scatter")], dict(bo), {}))
            assert sizes[1] == round(list(r1.figures.values())[0].aspect_ratio, 3)
            assert sizes[0] != sizes[1]
            # The page takes the build's or the session's scheme, not a graph's.
            assert r.scheme.name == other

    @pytest.mark.parametrize("mode", MODES)
    def test_a_graphs_scheme_sets_that_graphs_size(self, mode):
        """A graph's scheme() gives it that scheme's size, in the served app
        as in the saved page: served, scheme(stcolor) under an s2color
        session drew stcolor's colours at s2color's 5.5 x 4 (aspect 1.375,
        not 1.667; wp30 SX-03), hidden while the first graph's scheme was
        the dashboard's."""
        bo = {"session_scheme": "s2color"}
        graphs = [("g1", [plot_for("scatter")], {"scheme": "stcolor"}),
                  ("g2", [plot_for("scatter")], {})]
        spec = tp._spec(None, bo, None, graphs)
        if mode == "standalone":
            r, _m = tp._standalone(spec)
            got = [round(f.aspect_ratio, 4) for f in r.figures.values()]
        else:
            doc, _m = tp._served(spec)
            got = [round(p.aspect_ratio, 4) for p in _plots_in_order(doc)]
        r_st, _m = tp._standalone(tp._spec([plot_for("scatter")],
                                           {"session_scheme": "stcolor"}, {}))
        r_s2, _m = tp._standalone(tp._spec([plot_for("scatter")],
                                           {"session_scheme": "s2color"}, {}))
        want = [round(list(r_st.figures.values())[0].aspect_ratio, 4),
                round(list(r_s2.figures.values())[0].aspect_ratio, 4)]
        assert want[0] != want[1]
        assert got == want, (mode, got, want)

    @pytest.mark.parametrize("mode", MODES)
    def test_a_graphs_unknown_scheme_is_reported_once_for_it_alone(self, mode):
        """An unknown name on a graph (a spec built by hand: dash.ado
        refuses one) is said once, for that graph, however many graphs
        name it, and drawn s2color on those graphs only."""
        bo = {"session_scheme": "stcolor"}
        graphs = [("g1", [plot_for("scatter")], {"scheme": "nosuchthing"}),
                  ("g2", [plot_for("scatter")], {}),
                  ("g3", [plot_for("scatter")], {"scheme": "nosuchthing"})]
        borders, msgs = _draw(tp._spec(None, bo, None, graphs), mode)
        assert borders == [_bg("s2color"), _bg("stcolor"), _bg("s2color")], borders
        said = [m for m in msgs if "nosuchthing" in m]
        assert len(said) == 1 and "was not found for graph g1; using s2color" \
            in said[0], msgs

    def test_the_served_move_keeps_each_graphs_scheme(self):
        _n, filt, action, oracle = tp._MOVES[0]
        spec = tp._spec(graphs=_TWO, build_options={"filter": filt})
        figs, _k = tp._served_after_move(spec, action)
        saved, _k2 = tp._saved_with_qualifier(spec, oracle)

        def fills(f):
            return [(g.get("fill_color"), g.get("line_color"))
                    for g in f["glyphs"]]

        assert len(figs) == len(saved) == 2
        assert fills(figs[1]) == fills(saved[1]), (fills(figs[1]),
                                                   fills(saved[1]))

    def test_one_parse_per_name_served(self, tmp_path, monkeypatch):
        (tmp_path / "b2inc.scheme").write_text("#include nowhere34\n")
        monkeypatch.chdir(tmp_path)
        graphs = [("g%d" % i, [plot_for("scatter")], {"scheme": "b2inc"})
                  for i in (1, 2, 3)]
        _doc, msgs = tp._served(tp._spec(graphs=graphs))
        assert len([m for m in msgs if "nowhere34 not found" in m]) == 1, msgs
