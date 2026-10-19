"""test_requirements_lock.py -- dash_setup installs from a hash-pinned lock
(WP-32, I3; BUGS.md "dash_setup installs by version, not by hash").

dash_setup ran ``pip install "bokeh>=3.8,<3.10"`` and the like: whatever the
index served in the window, unchecked.  It now installs from
``dash_requirements.txt``, which scripts/make_requirements_lock.py writes
from dash_setup.ado's minimums (every package pinned with ``==`` and the
sha256 of every wheel of that release, for Python 3.11 to 3.14 on macOS,
Linux and Windows), with ``pip install --require-hashes -r``: the
requirement's lines, and each dependency's that is not installed.  No test
here reaches the network: pip is a recorded stand-in, and the generator's
network parts (``resolve``, ``fetch_release``) are not run.
"""
import importlib.util
import json
import os
import re
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "dash_setup_lib.py")
LOCK = os.path.join(ROOT, "dash_requirements.txt")
GEN = os.path.join(ROOT, "scripts", "make_requirements_lock.py")
ADO = os.path.join(ROOT, "dash_setup.ado")

_H = "0123456789abcdef" * 4


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def lib():
    return _load(LIB, "dash_setup_lib_lock_test")


@pytest.fixture(scope="module")
def gen():
    return _load(GEN, "make_requirements_lock_test")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _entry(name, version, marker="", n=1):
    head = "%s==%s" % (name, version) + (" ; " + marker if marker else "")
    return head + " \\\n" + " \\\n".join(
        "    --hash=sha256:" + ("%x" % (i + 1)) * 64 for i in range(n)) + "\n"


_SPECS = ["packaging", "bokeh>=3.8,<3.10", "numpy>=2.3", "pandas>=2.3"]


# ===========================================================================
# The committed lock
# ===========================================================================

class TestTheCommittedLock:

    def test_it_is_well_formed(self, lib):
        entries = lib.read_lock(_read(LOCK))
        assert entries
        for e in entries:
            assert e["hashes"] and all(re.fullmatch(r"[0-9a-f]{64}", h)
                                       for h in e["hashes"]), e["name"]
            assert len(set(e["hashes"])) == len(e["hashes"]), e["name"]
        keys = [(e["name"], e["marker"]) for e in entries]
        assert len(set(keys)) == len(keys)

    def test_it_is_generated_from_dash_setups_requirements(self, gen):
        text = _read(LOCK)
        assert "Written by scripts/make_requirements_lock.py" in text
        assert "do not edit by hand" in text
        reqs, pymin = gen.ado_requirements(_read(ADO))
        assert reqs == _SPECS
        assert "# requirements: " + " ".join(reqs) + "\n" in text
        assert "# pythons: " + " ".join(gen.PYTHONS) + "\n" in text
        assert gen.PYTHONS[0] == pymin
        assert "# platforms: " + " ".join(
            n for n, _t, _e in gen.PLATFORMS) + "\n" in text

    def test_every_requirement_is_pinned_inside_its_window(self, lib, gen):
        entries = lib.read_lock(_read(LOCK))
        reqs, _p = gen.ado_requirements(_read(ADO))
        # Raises when a requirement is missing or pinned outside its window.
        lines = lib.lock_lines(entries, reqs, {})
        assert len(lines) == len(entries)

    def test_the_package_ships_it(self):
        assert "f dash_requirements.txt" in _read(os.path.join(ROOT, "dash.pkg"))


# ===========================================================================
# The reader dash_setup uses
# ===========================================================================

class TestReadLock:

    def test_entries_markers_and_continuations(self, lib):
        text = ("# header\n\n" + _entry("NumPy", "2.4.6", n=2)
                + _entry("tzdata", "2026.5", 'sys_platform == "win32"'))
        a, b = lib.read_lock(text)
        assert (a["name"], a["version"], a["marker"]) == ("numpy", "2.4.6", "")
        assert a["hashes"] == ["1" * 64, "2" * 64]
        assert a["line"] == ("NumPy==2.4.6 --hash=sha256:%s --hash=sha256:%s"
                             % ("1" * 64, "2" * 64))
        assert b["marker"] == 'sys_platform == "win32"'
        assert b["line"].startswith('tzdata==2026.5 ; sys_platform == "win32" --hash')

    @pytest.mark.parametrize("text", [
        "",
        "# only a comment\n",
        "numpy==2.4.6\n",
        "numpy>=2.4 --hash=sha256:%s\n" % _H,
        "numpy --hash=sha256:%s\n" % _H,
        "numpy==2.4.6 --hash=sha256:%s\n" % _H[:63],
        "numpy==2.4.6 --hash=md5:%s\n" % _H[:32],
        "numpy==2.4.6 --index-url http://x --hash=sha256:%s\n" % _H,
        'numpy==2.4.6 ; os.system("x") --hash=sha256:%s\n' % _H,
        'numpy==2.4.6 ; extra == "a" --hash=sha256:%s\n' % _H,
        "-e git+https://x/y.git --hash=sha256:%s\n" % _H,
    ], ids=["empty", "comment_only", "no_hash", "a_range", "unpinned",
            "short_hash", "md5", "an_option", "a_call_in_the_marker",
            "an_unread_marker_variable", "editable"])
    def test_anything_else_is_refused(self, lib, text):
        with pytest.raises(ValueError):
            lib.read_lock(text)


class TestLockLines:

    def _entries(self, lib):
        return lib.read_lock(_entry("bokeh", "3.9.2") + _entry("numpy", "2.4.6")
                             + _entry("tornado", "6.5.10")
                             + _entry("packaging", "26.3"))

    def test_the_requirement_and_each_missing_dependency(self, lib):
        got = lib.lock_lines(self._entries(lib), ["bokeh>=3.8,<3.10"],
                             {"numpy": "2.3.5"})
        names = [ln.split("==")[0] for ln in got]
        assert names == ["bokeh", "tornado", "packaging"]

    def test_an_installed_requirement_inside_its_window_is_left(self, lib):
        """A reused venv's bokeh 3.10 under bokeh_requirement's bokeh>=3.8
        is never downgraded (WP-30 P1.30)."""
        got = lib.lock_lines(self._entries(lib), ["bokeh>=3.8"],
                             {"bokeh": "3.10.0", "numpy": "2.4.6",
                              "tornado": "6.5", "packaging": "25"})
        assert got == []

    def test_a_lock_older_than_dash_setup_is_refused(self, lib):
        with pytest.raises(ValueError, match="outside bokeh>=3.10"):
            lib.lock_lines(self._entries(lib), ["bokeh>=3.10"], {})
        with pytest.raises(ValueError, match="has no pandas"):
            lib.lock_lines(self._entries(lib), ["pandas>=2.3"], {})


# ===========================================================================
# dash_setup passes --require-hashes
# ===========================================================================

@pytest.fixture
def fake_sfi(monkeypatch, tmp_path):
    store = {"local": {}, "exec": str(tmp_path / "py"), "pwd": str(tmp_path)}
    (tmp_path / "py").write_text("")

    class Macro:
        @staticmethod
        def getLocal(k):
            return store["local"].get(k, "")

        @staticmethod
        def setLocal(k, v):
            store["local"][k] = v

    class SFIToolkit:
        @staticmethod
        def macroExpand(s):
            return {"\x60c(python_exec)'": store["exec"],
                    "\x60c(pwd)'": store["pwd"]}[s]

    mod = types.ModuleType("sfi")
    mod.Macro, mod.SFIToolkit = Macro, SFIToolkit
    monkeypatch.setitem(sys.modules, "sfi", mod)
    return store


def _recorder(installed):
    """A run_child stand-in: the installed-packages child answers
    *installed*; pip's vector and its requirement file are recorded."""
    seen = []

    def run(argv, **k):
        argv = list(argv)
        if "-c" in argv and "DASH_INSTALLED_V1" in argv[argv.index("-c") + 1]:
            return 0, json.dumps({"tag": "DASH_INSTALLED_V1",
                                  "dists": installed}), ""
        req = argv[argv.index("-r") + 1] if "-r" in argv else None
        seen.append((argv, _read(req) if req else None,
                     oct(os.stat(req).st_mode & 0o777) if req else None))
        return 0, "Successfully installed", ""
    return run, seen


class TestDashSetupRequiresHashes:

    def test_stata_pip_installs_from_the_lock(self, lib, fake_sfi, monkeypatch):
        run, seen = _recorder({"numpy": "2.3.5"})
        monkeypatch.setattr(lib, "run_child", run)
        fake_sfi["local"].update(spec="bokeh>=3.8,<3.10", user="0", ver="3.13.9")
        lib.stata_pip()
        assert fake_sfi["local"]["pip_outcome"] == "ok"
        (argv, req, mode), = seen
        assert argv[:2] == [fake_sfi["exec"], "-P"]
        assert argv[2:5] == ["-m", "pip", "install"]
        assert "--require-hashes" in argv and "--only-binary=:all:" in argv
        assert not [a for a in argv if a.startswith("bokeh")]
        assert mode == "0o600"
        entries = lib.read_lock(_read(LOCK))
        want = lib.lock_lines(entries, ["bokeh>=3.8,<3.10"], {"numpy": "2.3.5"})
        assert req.splitlines() == want
        assert all("--hash=sha256:" in ln for ln in want)
        assert not [ln for ln in want if ln.startswith("numpy==")]

    def test_the_user_retry_requires_hashes_too(self, lib, fake_sfi, monkeypatch):
        answers = [(1, "", "ERROR: something"), (0, "done", "")]
        run, seen = _recorder({})

        def run2(argv, **k):
            got = run(argv, **k)
            return answers.pop(0) if "-r" in argv else got
        monkeypatch.setattr(lib, "run_child", run2)
        monkeypatch.setattr(lib, "add_user_site", lambda: True)
        fake_sfi["local"].update(spec="numpy>=2.3", user="1", ver="3.13.9")
        lib.stata_pip()
        assert [("--user" in a, "--require-hashes" in a) for a, _r, _m in seen] == [
            (False, True), (True, True)]
        assert fake_sfi["local"]["pip_outcome"] == "ok"

    def test_without_a_lock_nothing_is_installed(self, lib, tmp_path, monkeypatch):
        run, seen = _recorder({})
        monkeypatch.setattr(lib, "run_child", run)
        rc, _out, err = lib.lock_install("/x/python", ["numpy>=2.3"], (3, 13),
                                         lock=str(tmp_path / "none.txt"))
        assert rc == 1 and "cannot read" in err and seen == []
        (tmp_path / "bad.txt").write_text("numpy>=2.3\n")
        rc, _out, err = lib.lock_install("/x/python", ["numpy>=2.3"], (3, 13),
                                         lock=str(tmp_path / "bad.txt"))
        assert rc == 1 and "not a pinned, hashed requirement" in err and seen == []

    def test_an_unreadable_package_list_installs_nothing(self, lib, monkeypatch):
        seen = []
        monkeypatch.setattr(lib, "run_child",
                            lambda argv, **k: (seen.append(argv), (1, "", "x"))[1])
        rc, _o, err = lib.lock_install("/x/python", ["numpy>=2.3"], (3, 13))
        assert rc == 1 and "could not list" in err and len(seen) == 1

    def test_nothing_missing_runs_no_pip(self, lib, monkeypatch):
        entries = lib.read_lock(_read(LOCK))
        every = {e["name"]: "2.4.6" if e["name"] == "numpy" else e["version"]
                 for e in entries}
        run, seen = _recorder(every)
        monkeypatch.setattr(lib, "run_child", run)
        rc, out, _e = lib.lock_install("/x/python", ["numpy>=2.3"], (3, 13))
        assert rc == 0 and "already installed" in out and seen == []

    def test_no_install_vector_is_unhashed(self):
        """Every pip install dash_setup runs goes through lock_install;
        pip_install_argv is left to the printed line a user types."""
        src = _read(LIB)
        calls = re.findall(r"run_child\(\s*pip_install_argv", src)
        assert calls == []
        assert src.count("lock_install(") >= 4


# ===========================================================================
# The generator's offline parts
# ===========================================================================

class TestTheGenerator:

    def test_the_requirements_come_from_dash_setup(self, gen):
        text = ('    local min_bokeh       "3.8"\n    local max_bokeh  "3.10"\n'
                '    local min_numpy "2.3"\n    local min_pandas "2.4"\n'
                'program define _dash_pymin, rclass\n    return local pymin "3.11"\nend\n')
        assert gen.ado_requirements(text) == (
            ["packaging", "bokeh>=3.8,<3.10", "numpy>=2.3", "pandas>=2.4"], "3.11")
        with pytest.raises(ValueError):
            gen.ado_requirements(text.replace("min_numpy", "min_nump"))

    def test_target_markers(self, gen):
        every = [(p, n) for p in gen.PYTHONS for n, _t, _e in gen.PLATFORMS]
        assert gen.target_marker(every) == ""
        assert gen.target_marker([t for t in every if t[0] == "3.11"]) == \
            'python_version == "3.11"'
        assert gen.target_marker([t for t in every if t[1] == "windows-amd64"]) == \
            '(sys_platform == "win32" and platform_machine == "AMD64")'
        assert gen.target_marker([("3.12", "linux-aarch64")]) == (
            '(sys_platform == "linux" and platform_machine == "aarch64" and '
            '(python_version == "3.12"))')

    def test_needed_evaluates_markers_for_the_target(self, gen):
        report = {"install": [
            {"metadata": {"name": "pandas", "version": "3.0.6", "requires_dist": [
                "numpy>=1.26", 'tzdata; sys_platform == "win32"',
                'pytest; extra == "test"']}},
            {"metadata": {"name": "NumPy", "version": "2.4.6"}}]}
        lin = gen.target_env("3.12", dict(gen.PLATFORMS[2][2]))
        win = gen.target_env("3.12", dict(gen.PLATFORMS[4][2]))
        assert gen.needed(report, ["pandas>=2.3"], lin) == {"pandas", "numpy"}
        assert gen.needed(report, ["pandas>=2.3"], win) == {"pandas", "numpy",
                                                           "tzdata"}

    def test_combine_and_render_round_trip_through_dash_setups_reader(self, gen, lib):
        per = {}
        for p in gen.PYTHONS:
            for n, _t, _e in gen.PLATFORMS:
                pins = {"numpy": "2.4.6" if p == "3.11" else "2.5.4"}
                if n == "windows-amd64":
                    pins["tzdata"] = "2026.5"
                per[(p, n)] = pins
        entries = gen.combine(per)
        assert [(n, v) for n, v, _m in entries] == [
            ("numpy", "2.4.6"), ("numpy", "2.5.4"), ("tzdata", "2026.5")]
        hashes = {(n, v): [_H, "f" * 64] for n, v, _m in entries}
        text = gen.render(entries, hashes, ["numpy>=2.3"], "19oct2026")
        got = lib.read_lock(text)
        assert [(e["name"], e["version"], e["marker"]) for e in got] == [
            (n, v, m) for n, v, m in entries]
        assert all(e["hashes"] == [_H, "f" * 64] for e in got)
        with pytest.raises(ValueError):
            gen.render(entries, {k: [] for k in hashes}, ["numpy>=2.3"], "x")

    def test_wheel_hashes_are_the_wheels_only(self, gen):
        rel = {"urls": [
            {"packagetype": "bdist_wheel", "digests": {"sha256": "b" * 64}},
            {"packagetype": "sdist", "digests": {"sha256": "c" * 64}},
            {"packagetype": "bdist_wheel", "digests": {"sha256": "a" * 64}},
            {"packagetype": "bdist_wheel", "digests": {"sha256": "nothex"}}]}
        assert gen.wheel_hashes(rel) == ["a" * 64, "b" * 64]
