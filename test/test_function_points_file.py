"""A named graph's function points kept in a private file, not a macro
(WP-36 plat:PT-4, DECISIONS A-7).

dash kept a named graph's function points in one global,
``$dash_fpts_<name>``, and refused a graph whose points were longer than
``c(macrolen)``, r(134), advising ``set maxvar`` -- while twoway draws two
or four 10,000-point function layers.  The points now live in the file
``fp-<hex of the name>.txt`` of this Stata session's folder
``<tmpdir>dash-<uid>/points-<pid>/`` (0700, the file 0600), reached through
five Mata accessors and the ado program ``_dash_fpts_open``.  A file
outlives ``clear all`` as the registry's globals do; ``dash clear`` empties
the folder and the sweep removes the folders of ended Stata sessions.

The ado, Mata and help sources are read as text with their comments
dropped; the Python helpers are reached with ``getattr`` inside each test,
so a tree without them fails on an assertion, never at collection.
"""

import os
import re
import shutil
import stat
import subprocess
import sys
import json

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

import dash_render as dr  # noqa: E402

_ADO = os.path.join(_ROOT, "dash.ado")
_MATA = os.path.join(_ROOT, "dash_parse.mata")
_HELP = os.path.join(_ROOT, "dash.sthlp")
_ACCESSORS = ("_dash_fpts_path", "_dash_fpts_put", "_dash_fpts_get",
              "_dash_fpts_drop", "_dash_fpts_clear")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _code(src):
    """Source with // comments and *! header lines removed."""
    out = []
    for line in src.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*!"):
            continue
        out.append(line.split("//", 1)[0])
    return "\n".join(out)


def _program(src, name):
    m = re.search(r"(?ms)^program define %s\b[^\n]*\n(.*?)^end\b"
                  % re.escape(name), src)
    return m.group(1) if m else None


def _umask(mask):
    import contextlib

    @contextlib.contextmanager
    def _cm():
        old = os.umask(mask)
        try:
            yield
        finally:
            os.umask(old)
    return _cm()


def _dead_pid():
    p = subprocess.Popen([sys.executable, "-c", "pass"],
                         env={k: v for k, v in os.environ.items()
                              if not k.startswith("PYTHON")})
    p.wait()
    return p.pid


class TestOffTheMacro:

    def test_no_ado_line_stores_points_in_a_global(self):
        code = _code(_read(_ADO))
        assert 'st_global("dash_fpts_' not in code
        assert "strlen global dash_fpts_" not in code
        mata = _code(_read(_MATA))
        assert 'st_global("dash_fpts_' not in mata

    def test_no_macrolen_refusal(self):
        body = _program(_read(_ADO), "_dash_register_graph")
        assert body is not None
        assert "macrolen" not in _code(body)
        assert "set maxvar" not in body

    def test_the_accessors_exist(self):
        mata = _read(_MATA)
        for name in _ACCESSORS:
            assert re.search(r"(?m)^\S.*\b%s\(" % name, mata), name
        assert _program(_read(_ADO), "_dash_fpts_open") is not None


class TestTheFolder:

    def test_made_0700_for_this_pid(self, tmp_path):
        fd = getattr(dr, "_dash_fpts_dir", None)
        assert fd is not None, "dash_render.py has no _dash_fpts_dir"
        for mask in (0o022, 0o002):
            tmp = tmp_path / ("m%03o" % mask)
            tmp.mkdir()
            with _umask(mask):
                out = fd(str(tmp) + os.sep)
            assert out["err"] == "" and out["note"] == "", out
            d = out["dir"]
            assert os.path.basename(d) == "points-%d" % os.getpid()
            assert os.path.basename(os.path.dirname(d)) == dr._dash_root_name()
            assert stat.S_IMODE(os.lstat(d).st_mode) == 0o700
            # A second call keeps the same folder.
            assert fd(str(tmp) + os.sep)["dir"] == d

    def test_a_planted_link_is_refused(self, tmp_path):
        fd = getattr(dr, "_dash_fpts_dir", None)
        assert fd is not None, "dash_render.py has no _dash_fpts_dir"
        root, _ = dr._dash_private_root(str(tmp_path) + os.sep)
        target = tmp_path / "elsewhere"
        target.mkdir()
        os.symlink(str(target), os.path.join(root, "points-%d" % os.getpid()))
        with pytest.raises(dr._DashUnsafePath):
            fd(str(tmp_path) + os.sep)


class TestTheSweep:

    def test_ended_sessions_go_and_this_one_stays(self, tmp_path):
        sw = getattr(dr, "_dash_points_sweep", None)
        assert sw is not None, "dash_render.py has no _dash_points_sweep"
        dead = _dead_pid()
        names = ["points-%d" % dead, "points-%d" % os.getpid(),
                 "points-%d" % os.getppid()]
        for n in names:
            (tmp_path / n).mkdir()
            (tmp_path / n / "fp-6131.txt").write_text("{}")
        assert sw(str(tmp_path)) == 1
        assert not (tmp_path / names[0]).exists()
        assert (tmp_path / names[1] / "fp-6131.txt").exists()
        assert (tmp_path / names[2]).exists()

    def test_tmp_clear_sweeps_them(self, tmp_path):
        assert getattr(dr, "_dash_points_sweep", None) is not None
        tmp = str(tmp_path) + os.sep
        root, _ = dr._dash_private_root(tmp)
        dead = os.path.join(root, "points-%d" % _dead_pid())
        mine = os.path.join(root, "points-%d" % os.getpid())
        os.mkdir(dead, 0o700)
        os.mkdir(mine, 0o700)
        dr._dash_tmp_clear(tmp)
        assert not os.path.exists(dead)
        assert os.path.isdir(mine)

    def test_stdlib_entry_still_compiles(self):
        import dash_setup_lib
        fn = dash_setup_lib.stdlib_entry(os.path.join(_ROOT, "dash_render.py"),
                                         "_dash_tmp_clear")
        assert fn is not None


class TestTheHelp:

    def _function_n_paragraph(self):
        help_ = _read(_HELP)
        i = help_.find("{cmd:function}: 300 by\n    default")
        assert i > 0
        return help_[i:i + 600]

    def test_no_macrolen_advice(self):
        para = self._function_n_paragraph()
        assert "c(macrolen)" not in para
        assert "set maxvar" not in para
        assert "set maxvar" not in _read(_HELP)

    def test_the_points_home_is_named(self):
        help_ = " ".join(_read(_HELP).split())
        assert "$dash_fpts_" not in help_
        assert ("graph's points in a private file of {cmd:dash}'s temporary "
                "folder") in help_
        i = help_.find("graph's points in a private file")
        assert "{cmd:clear all} keeps it" in help_[i:i + 400]


@pytest.mark.release
class TestClearAll:

    def test_points_survive_clear_all(self, tmp_path):
        stata = os.environ.get("STATA_BIN", "/usr/local/bin/stata-mp")
        if not (os.path.isfile(stata) and os.access(stata, os.X_OK)):
            pytest.skip("STATA_BIN %s is not an executable file" % stata)
        do = tmp_path / "clearall.do"
        do.write_text(
            'adopath ++ "%s"\n'
            "global dash_nobrowser 1\n"
            "sysuse auto, clear\n"
            "dash function y = x, n(5) name(ca)\n"
            "clear all\n"
            "sysuse auto, clear\n"
            'quietly do "%s/dash.ado"\n'
            "_dash_require_mata\n"
            '_dash_serve_spec, specpath("spec.json") datapath("data.json")\n'
            "dash clear\n" % (_ROOT, _ROOT))
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("PYTHON")}
        subprocess.run(["sh", os.path.join(_ROOT, "scripts", "stata_slot.sh"),
                        str(tmp_path), str(do)], env=env, timeout=900,
                       check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        spec_p = tmp_path / "spec.json"
        log = tmp_path / "clearall.log"
        assert spec_p.exists(), log.read_text() if log.exists() else "no log"
        spec = json.loads(spec_p.read_text())
        y = spec["function_points"]["ca"]["1"]["y"]
        assert len(y) == 5
        shutil.rmtree(str(tmp_path / "tmp"), ignore_errors=True)
