"""test_setup_pep668.py -- dash_setup on PEP 668 (externally managed) Pythons.

WP-29 P0.19, GAPS2 H7a-g, and the four defects measured on the same path:

* N1  a non-ASCII byte in pip's PEP 668 message ended dash_setup with
      r(7102) under Stata's batch locale (US-ASCII);
* N2  pip ran ``sys.executable``, which under a Homebrew venv link is the
      base interpreter, not the one Stata is linked to;
* N3  pip ran from Stata's working directory, so a ``pip/`` package there
      ran instead of pip (a security defect);
* N4  the "To upgrade" line printed on a managed Python was itself refused.

dash_setup's mechanics live in ``dash_setup_lib.py`` (stdlib only, parses as
Python 3.8).  Each of its functions is held here; ``SETUP_FUNCTIONS`` in
test/function_test_map.py names the test of each.  pip's measured refusal
texts are the fixture ``test/fixtures/pip_refusals.json``
(scripts/extract_pip_refusals.py).  Real venvs are made offline
(``PIP_NO_INDEX=1``), four of them at most.
"""
import ast
import importlib
import importlib.util
import json
import os
import re
import shutil
import site
import stat
import subprocess
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "dash_setup_lib.py")
RENDER = os.path.join(ROOT, "dash_render.py")
with open(os.path.join(ROOT, "test", "fixtures", "pip_refusals.json"),
          encoding="utf-8") as _fh:
    FIX = json.load(_fh)

PIP_FLAGS = ["--disable-pip-version-check", "--no-input", "--only-binary=:all:"]


def _load(name="dash_setup_lib_under_test"):
    spec = importlib.util.spec_from_file_location(name, LIB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Missing:
    """Stands in for the module while it does not exist: the first use of
    any name fails that test (not its setup), with the reason."""

    def __getattr__(self, name):
        pytest.fail("dash_setup_lib.py is missing (WP-29 P0.19)")


@pytest.fixture(scope="module")
def lib():
    if not os.path.isfile(LIB):
        return _Missing()
    return _load()


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setenv("PIP_NO_INDEX", "1")


def _detect_line(**over):
    d = {"tag": "DASH_DETECT_V1", "prefix": "/p", "base_prefix": "/p",
         "stdlib": "/p/lib", "marker": False, "pyvenv_cfg": False,
         "pip": True, "ensurepip": True, "venv": True,
         "user_site_enabled": True, "user_site": "/u",
         "version": [3, 13, 9], "executable": "/p/bin/python3"}
    d.update(over)
    return json.dumps(d)


def _purelib(py):
    r = subprocess.run([py, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()


def _bare_venv(path):
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(path)],
                   check=True, capture_output=True)
    return os.path.join(str(path), "bin", "python")


class TestResolveExe:

    def test_an_absolute_path_is_unchanged(self, lib, tmp_path):
        assert lib.resolve_exe("/opt/x/bin/python3", str(tmp_path)) == "/opt/x/bin/python3"

    def test_a_bare_name_goes_to_which(self, lib, tmp_path):
        seen = []

        def which(name):
            seen.append(name)
            return "/found/" + name
        assert lib.resolve_exe("python3", str(tmp_path), which=which) == "/found/python3"
        assert seen == ["python3"]

    def test_a_relative_path_is_resolved_against_the_stata_directory(self, lib, tmp_path):
        (tmp_path / "v" / "bin").mkdir(parents=True)
        (tmp_path / "v" / "bin" / "python").write_text("")
        got = lib.resolve_exe(os.path.join("v", "bin", "python"), str(tmp_path))
        assert got == os.path.join(str(tmp_path), "v", "bin", "python")
        assert lib.resolve_exe(os.path.join("w", "bin", "python"), str(tmp_path)) is None


class TestVersionAndFlags:

    @pytest.mark.parametrize("text, want", [
        ("3.13.9", (3, 13, 9)), ("3.12.11 (x)", (3, 12, 11)), ("abc", ()), ("", ())])
    def test_version_tuple(self, lib, text, want):
        assert lib.version_tuple(text) == want

    def test_safe_flags_only_from_3_11(self, lib):
        assert lib.safe_flags((3, 8)) == []
        assert lib.safe_flags((3, 10, 9)) == []
        assert lib.safe_flags((3, 11, 0)) == ["-P"]
        assert lib.safe_flags((3, 13, 9)) == ["-P"]
        assert lib.safe_flags(()) == []


class TestChildEnv:

    def test_python_variables_are_dropped_and_protections_set(self, lib):
        env = {k: "x" for k in lib._ENV_DROP}
        env.update({"PIP_BREAK_SYSTEM_PACKAGES": "1", "PIP_USER": "1",
                    "PIP_INDEX_URL": "https://m/simple", "PIP_NO_INDEX": "1",
                    "PYTHONUSERBASE": "/ub", "HTTPS_PROXY": "http://p:1",
                    "PATH": "/bin"})
        before = dict(env)
        out = lib.child_env(env)
        assert env == before
        for k in lib._ENV_DROP:
            assert k not in out
        assert out["PIP_BREAK_SYSTEM_PACKAGES"] == "0"
        assert out["PIP_USER"] == "0"
        assert out["PYTHONIOENCODING"] == "utf-8"
        assert out["PYTHONDONTWRITEBYTECODE"] == "1"
        for k in ("PIP_INDEX_URL", "PIP_NO_INDEX", "PYTHONUSERBASE", "HTTPS_PROXY", "PATH"):
            assert out[k] == env[k]


_A4_CODE = r'''
import importlib.util, json, locale, subprocess, sys
path, hexbytes = sys.argv[1], sys.argv[2]
s = importlib.util.spec_from_file_location("dsl_a4", path)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
fake = [sys.executable, "-c",
        "import sys; sys.stderr.buffer.write(bytes.fromhex(%r)); sys.exit(1)" % hexbytes]
control = "ok"
try:
    subprocess.run(fake, capture_output=True, text=True)
except UnicodeDecodeError:
    control = "raised"
rc, out, err = m.run_child(fake)
print(json.dumps({"enc": locale.getpreferredencoding(False), "control": control,
                  "rc": rc, "err": err}))
'''


def _evil_pip(root, marker):
    pkg = root / "pip"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "__main__.py").write_text("open(%r, 'w').close()\n" % str(marker))


class TestRunChild:

    def test_non_ascii_output_under_an_ascii_locale_is_decoded(self, lib):
        assert callable(lib.run_child)
        hexbytes = FIX["externally_managed"]["stderr"].encode("utf-8").hex()
        env = {k: v for k, v in os.environ.items()
               if k != "LANG" and not k.startswith("LC_")
               and k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
        env.update({"LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"})
        r = subprocess.run([sys.executable, "-c", _A4_CODE, LIB, hexbytes],
                           capture_output=True, env=env, check=True)
        got = json.loads(r.stdout.decode("ascii").strip().splitlines()[-1])
        assert "ascii" in got["enc"].lower()
        assert got["control"] == "raised"
        assert got["rc"] == 1
        assert "\u00d7" in got["err"]
        assert "externally-managed-environment" in got["err"]

    def test_a_pip_package_in_the_working_directory_is_not_run(self, lib, tmp_path, monkeypatch):
        evil = tmp_path / "evil"
        marker = tmp_path / "marker"
        _evil_pip(evil, marker)
        subprocess.run([sys.executable, "-m", "pip", "--version"], cwd=str(evil),
                       capture_output=True)
        assert marker.exists()
        marker.unlink()
        monkeypatch.chdir(evil)
        rc, out, err = lib.run_child([sys.executable, *lib.safe_flags(sys.version_info),
                                      "-m", "pip", "--version"])
        assert not marker.exists()
        assert rc == 0, err
        assert "pip" in out

    def test_an_inherited_pythonpath_does_not_reach_the_child(self, lib, tmp_path, monkeypatch):
        evil = tmp_path / "evil"
        marker = tmp_path / "marker"
        _evil_pip(evil, marker)
        monkeypatch.setenv("PYTHONPATH", str(evil))
        subprocess.run([sys.executable, "-m", "pip", "--version"], cwd=str(tmp_path),
                       capture_output=True)
        assert marker.exists()
        marker.unlink()
        rc, out, err = lib.run_child([sys.executable, "-m", "pip", "--version"])
        assert not marker.exists()
        assert rc == 0, err

    def test_the_child_runs_in_a_private_directory_that_is_removed(self, lib):
        rc, out, err = lib.run_child([sys.executable, "-c",
                                      "import os; print(os.getcwd()); print(oct(os.stat('.').st_mode & 0o777))"])
        assert rc == 0, err
        where, mode = out.split()
        assert os.path.realpath(where) != os.path.realpath(os.getcwd())
        assert mode == "0o700"
        assert not os.path.exists(where)

    def test_a_missing_interpreter_and_a_timeout_are_reported_not_raised(self, lib, tmp_path):
        nope = str(tmp_path / "nope")
        rc, out, err = lib.run_child([nope])
        assert rc == -1
        assert nope in err
        rc, out, err = lib.run_child([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.5)
        assert rc == -2
        assert "did not finish within" in err

    def test_the_call_is_shell_free_and_umask_only_where_popen_takes_it(self, lib, monkeypatch):
        seen = []

        def rec(argv, **kw):
            seen.append(kw)
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        monkeypatch.setattr(lib.subprocess, "run", rec)
        monkeypatch.setenv("PYTHONPATH", "/x")
        monkeypatch.setenv("PIP_BREAK_SYSTEM_PACKAGES", "1")
        assert lib.run_child(["/py", "-c", "1"], runtime=(3, 8, 0)) == (0, "", "")
        lib.run_child(["/py", "-c", "1"], runtime=(3, 9, 0))
        assert "umask" not in seen[0]
        if os.name == "posix":
            assert seen[1]["umask"] == 0o022
        for kw in seen:
            assert kw["shell"] is False
            assert kw["stdin"] is subprocess.DEVNULL
            assert kw["encoding"] == "utf-8"
            assert kw["errors"] == "replace"
            assert "PYTHONPATH" not in kw["env"]
            assert kw["env"]["PIP_BREAK_SYSTEM_PACKAGES"] == "0"
            assert kw["cwd"] != os.getcwd()


class TestDetectEnvironment:

    @pytest.mark.parametrize("over, want", [
        ({"marker": True}, {"ok": True, "externally_managed": True, "in_venv": False}),
        ({"marker": True, "prefix": "/v"}, {"ok": True, "externally_managed": False, "in_venv": True}),
        ({"pyvenv_cfg": True}, {"ok": True, "in_venv": True}),
        (None, {"ok": False}),
        ({"tag": "OTHER"}, {"ok": False}),
        ({"version": "3"}, {"ok": False}),
        ({"prefix": "/v", "user_site_enabled": True}, {"ok": True, "user_site_enabled": False}),
    ])
    def test_interpret_detect_rules(self, lib, over, want):
        text = "noise\n{not json" if over is None else "noise\n" + _detect_line(**over) + "\n"
        got = lib.interpret_detect(text)
        for k, v in want.items():
            assert got[k] == v, (k, got)
        if not want["ok"]:
            assert got["why"]

    def test_the_test_interpreter_reports_itself(self, lib):
        import sysconfig
        got = lib.detect_environment(sys.executable)
        assert got["ok"], got
        assert got["version"] == tuple(sys.version_info[:3])
        marker = os.path.isfile(os.path.join(sysconfig.get_path("stdlib"), "EXTERNALLY-MANAGED"))
        in_venv = sys.prefix != sys.base_prefix
        assert got["externally_managed"] == (marker and not in_venv)

    def test_a_venv_without_pip_is_reported_without_pip(self, lib, tmp_path):
        vpy = _bare_venv(tmp_path / "vnp")
        got = lib.detect_environment(vpy)
        assert got["ok"], got
        assert got["in_venv"] is True
        assert got["pip"] is False
        assert importlib.util.find_spec("pip") is not None


class TestPipArgv:

    def test_the_exact_vector_and_safe_path_flag(self, lib):
        assert lib.pip_install_argv("/e", ["bokeh>=3.8"], (3, 13, 9)) == \
            ["/e", "-P", "-m", "pip", "install"] + PIP_FLAGS + ["bokeh>=3.8"]
        assert lib.pip_install_argv("/e", ["bokeh>=3.8"], (3, 10, 0)) == \
            ["/e", "-m", "pip", "install"] + PIP_FLAGS + ["bokeh>=3.8"]
        assert lib.pip_install_argv("/e", ["a", "b>=1"], (3, 13, 9), user=True) == \
            ["/e", "-P", "-m", "pip", "install"] + PIP_FLAGS + ["--user", "a", "b>=1"]

    @pytest.mark.parametrize("bad", ["bokeh; rm -rf ~", "-e .", "--index-url=x",
                                     "bokeh>=3.8 ", "bokeh==3.8", "../x"])
    def test_the_whitelist(self, lib, bad):
        with pytest.raises(ValueError, match="refusing the requirement"):
            lib.pip_install_argv("/e", [bad], (3, 13, 9))
        assert lib.pip_install_argv("/e", ["bokeh>=3.8,<4"], (3, 13, 9))[-1] == "bokeh>=3.8,<4"


class TestTheUndoLine:
    """WP-31 I3: a failed dash_setup names what it installed and the pip
    line that removes it."""

    def test_the_uninstall_vector(self, lib):
        assert lib.pip_uninstall_argv("/e", ["packaging", "numpy"]) == \
            ["/e", "-m", "pip", "uninstall", "packaging", "numpy"]

    @pytest.mark.parametrize("bad", ["numpy; rm -rf ~", "-y", "", "../x",
                                     "bokeh>=3.8"])
    def test_only_names_are_taken(self, lib, bad):
        with pytest.raises(ValueError, match="refusing the package name"):
            lib.pip_uninstall_argv("/e", ["numpy", bad])


class TestClassifyFailure:

    @pytest.mark.parametrize("record, kind", [
        ("externally_managed", "externally-managed"), ("user_in_venv", "user-unavailable"),
        ("user_disabled", "user-unavailable"), ("no_pip", "no-pip"),
        ("offline_no_match", "other")])
    def test_each_measured_refusal_is_classified(self, lib, record, kind):
        r = FIX[record]
        assert r["rc"] != 0
        assert lib.classify_failure(r["rc"], r["stderr"]) == kind

    def test_codes_and_debian(self, lib):
        assert lib.classify_failure(0, "anything") == "ok"
        assert lib.classify_failure(-1, "") == "missing-interpreter"
        assert lib.classify_failure(-2, "") == "timeout"
        assert lib.classify_failure(1, "The virtual environment was not created successfully "
                                       "because ensurepip is not available.") == "no-ensurepip"


class TestShellLine:

    @staticmethod
    def _stub(path, out):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!%s\nimport json, sys\nopen(%r, 'w').write(json.dumps(sys.argv[1:]))\n"
                        % (sys.executable, str(out)))
        path.chmod(0o755)

    def test_the_posix_line_survives_sh(self, lib, tmp_path):
        out = tmp_path / "argv.json"
        stub = tmp_path / "My Python" / "bin" / "python3"
        self._stub(stub, out)
        line = lib.shell_line([str(stub), "-m", "pip", "install", "bokeh>=3.8"], False)
        subprocess.run(["/bin/sh", "-c", line], cwd=str(tmp_path), check=True)
        assert json.loads(out.read_text()) == ["-m", "pip", "install", "bokeh>=3.8"]
        assert not (tmp_path / "=3.8").exists()
        # The line dash_setup printed before: the shell reads > as a redirection.
        plain = tmp_path / "plain" / "python3"
        self._stub(plain, out)
        subprocess.run(["/bin/sh", "-c", "%s -m pip install bokeh>=3.8" % plain],
                       cwd=str(tmp_path), check=True)
        assert json.loads(out.read_text()) == ["-m", "pip", "install", "bokeh"]
        assert (tmp_path / "=3.8").exists()

    def test_windows_double_quotes_metacharacters(self, lib):
        argv = ["C:\\Program Files\\Python313\\python.exe", "-m", "pip", "install", "bokeh>=3.8"]
        assert lib.shell_line(argv, True) == \
            '"C:\\Program Files\\Python313\\python.exe" -m pip install "bokeh>=3.8"'
        assert lib.shell_line(["C:\\P\\python.exe", "-m", "ensurepip", "--upgrade"], True) == \
            '"C:\\P\\python.exe" -m ensurepip --upgrade'

    @pytest.mark.parametrize("bad", ['a"b', "100%"])
    def test_windows_refuses_a_quote_or_percent(self, lib, bad):
        with pytest.raises(ValueError, match="cmd.exe"):
            lib.shell_line(["C:\\P\\python.exe", bad], True)
        assert lib.shell_line(["/p/python3", bad], False).startswith("/p/python3 ")


class TestAddUserSite:

    def test_a_user_site_made_after_start_becomes_importable(self, lib, tmp_path, monkeypatch):
        us = tmp_path / "us"
        monkeypatch.setattr(sys, "path", list(sys.path))
        monkeypatch.setattr(site, "ENABLE_USER_SITE", True)
        monkeypatch.setattr(site, "getusersitepackages", lambda: str(us))
        us.mkdir()
        (us / "dashzzusersiteprobe.py").write_text("X = 1\n")
        try:
            with pytest.raises(ModuleNotFoundError):
                importlib.import_module("dashzzusersiteprobe")
            assert lib.add_user_site() is True
            assert importlib.import_module("dashzzusersiteprobe").X == 1
        finally:
            sys.modules.pop("dashzzusersiteprobe", None)
            importlib.invalidate_caches()

    def test_nothing_changes_when_disabled_or_already_present(self, lib, tmp_path, monkeypatch):
        us = tmp_path / "us"
        us.mkdir()
        monkeypatch.setattr(sys, "path", list(sys.path))
        monkeypatch.setattr(site, "getusersitepackages", lambda: str(us))
        monkeypatch.setattr(site, "ENABLE_USER_SITE", False)
        assert lib.add_user_site() is False
        monkeypatch.setattr(site, "ENABLE_USER_SITE", True)
        sys.path.append(str(us))
        n = len(sys.path)
        assert lib.add_user_site() is False
        assert len(sys.path) == n
        monkeypatch.setattr(site, "getusersitepackages", lambda: str(tmp_path / "missing"))
        assert lib.add_user_site() is False


def _mkvenv_dir(path, mode=0o755, bin_mode=0o755):
    os.makedirs(os.path.join(path, "bin"))
    open(os.path.join(path, "pyvenv.cfg"), "w").close()
    open(os.path.join(path, "bin", "python"), "w").close()
    os.chmod(os.path.join(path, "bin"), bin_mode)
    os.chmod(path, mode)


_REFUSALS = ["empty", "control", "quote", "backtick", "dollar", "symlink", "file",
             "nonempty", "venv775", "bin775", "owner", "wwparent", "outside", "dotdot"]


class TestValidateVenvPath:

    @pytest.mark.parametrize("case", _REFUSALS)
    def test_refusals(self, lib, tmp_path, case):
        t = str(tmp_path)
        home = os.path.join(t, "h")
        os.mkdir(home)
        getuid = None
        raw, want = {
            "empty": ("  ", "venv\\(\\) names no directory"),
            "control": ("a\x01b", "holds a character"),
            "quote": ('a"b', "holds a character"),
            "backtick": ("a`b", "holds a character"),
            "dollar": ("a$b", "holds a character"),
            "symlink": ("ln", "is a symbolic link"),
            "file": ("f", "exists and is not a directory"),
            "nonempty": ("ne", "is not empty and is not a virtual environment"),
            "venv775": ("v775", "can be written by other users"),
            "bin775": ("b775", "can be written by other users"),
            "owner": ("own", "is not owned by you"),
            "wwparent": (os.path.join("ww", "v"), "can be written by other users and is not sticky"),
            "outside": (os.path.join("a", "b", "v"), "its parent directory does not exist"),
            "dotdot": (os.path.join("x", ".."), "names no directory of its own"),
        }[case]
        if case == "symlink":
            os.mkdir(os.path.join(t, "real"))
            os.symlink(os.path.join(t, "real"), os.path.join(t, "ln"))
        elif case == "file":
            open(os.path.join(t, "f"), "w").close()
        elif case == "nonempty":
            os.mkdir(os.path.join(t, "ne"))
            open(os.path.join(t, "ne", "x"), "w").close()
        elif case == "venv775":
            _mkvenv_dir(os.path.join(t, "v775"), mode=0o775)
        elif case == "bin775":
            _mkvenv_dir(os.path.join(t, "b775"), bin_mode=0o775)
        elif case == "owner":
            _mkvenv_dir(os.path.join(t, "own"))
            getuid = lambda: os.getuid() + 1  # noqa: E731
        elif case == "wwparent":
            os.mkdir(os.path.join(t, "ww"))
            os.chmod(os.path.join(t, "ww"), 0o777)
        with pytest.raises(lib.VenvPathError, match=want):
            lib.validate_venv_path(raw, t, windows=False, getuid=getuid, home=home)

    def test_resolutions(self, lib, tmp_path):
        t = str(tmp_path)
        rt = os.path.realpath(t)
        home = os.path.join(t, "h")
        os.mkdir(home)
        v = lambda raw: lib.validate_venv_path(raw, t, windows=False, home=home)  # noqa: E731
        assert v("v") == (os.path.join(rt, "v"), "new", [])
        assert v("-h")[0] == os.path.join(rt, "-h")
        assert v("~/v") == (os.path.join(os.path.realpath(home), "v"), "new", [])
        os.mkdir(os.path.join(t, "e"))
        assert v("e")[1] == "empty"
        _mkvenv_dir(os.path.join(t, "ve"))
        assert v("ve")[1] == "venv"
        os.mkdir(os.path.join(t, "st"))
        os.chmod(os.path.join(t, "st"), 0o1777)
        assert v(os.path.join("st", "v")) == (os.path.join(rt, "st", "v"), "new", [])
        os.mkdir(os.path.join(t, "real"))
        os.symlink(os.path.join(t, "real"), os.path.join(t, "link"))
        assert v(os.path.join("link", "v"))[0] == os.path.join(os.path.realpath(os.path.join(t, "real")), "v")
        assert v(os.path.join("link", "..", "v"))[0] == \
            os.path.join(os.path.realpath(os.path.join(t, "link", "..")), "v")

    def test_the_suggested_default_is_accepted_on_a_home_without_dash(self, lib, tmp_path):
        home = tmp_path / "h"
        home.mkdir()
        rh = os.path.realpath(str(home))
        got = lib.validate_venv_path("~/.dash/venv", str(tmp_path), windows=False, home=str(home))
        assert got == (os.path.join(rh, ".dash", "venv"), "new", [os.path.join(rh, ".dash")])


def _fake_venv_run(argv, *a, **k):
    if "venv" in argv:
        path = argv[-1]
        os.makedirs(os.path.join(path, "bin"), exist_ok=True)
        open(os.path.join(path, "pyvenv.cfg"), "w").close()
        open(os.path.join(path, "bin", "python"), "w").close()
    return 0, "", ""


class TestCreateVenv:

    def test_a_real_venv_is_created_offline_with_mode_0755(self, lib, tmp_path, offline):
        abs_, state, create = lib.validate_venv_path("v", str(tmp_path), windows=False)
        assert lib.create_venv(sys.executable, abs_, state, create, sys.version_info) == (True, "")
        assert os.path.isfile(os.path.join(abs_, "pyvenv.cfg"))
        assert os.path.exists(os.path.join(abs_, "bin", "python"))
        assert stat.S_IMODE(os.stat(abs_).st_mode) == 0o755
        assert stat.S_IMODE(os.stat(os.path.join(abs_, "bin")).st_mode) == 0o755

    def test_missing_ancestors_inside_home_are_created_private(self, lib, tmp_path, monkeypatch):
        home = tmp_path / "h"
        home.mkdir()
        monkeypatch.setattr(lib, "run_child", _fake_venv_run)
        abs_, state, create = lib.validate_venv_path("~/.dash/venv", str(tmp_path),
                                                     windows=False, home=str(home))
        assert not (home / ".dash").exists()
        assert lib.create_venv("/py", abs_, state, create, (3, 13, 9)) == (True, "")
        assert stat.S_IMODE(os.stat(str(home / ".dash")).st_mode) == 0o700

    def test_a_path_created_after_validation_is_refused(self, lib, tmp_path):
        abs_, state, create = lib.validate_venv_path("r", str(tmp_path), windows=False)
        os.mkdir(abs_)
        ok, why = lib.create_venv("/py", abs_, state, create, (3, 13, 9))
        assert ok is False
        assert "appeared after it was checked" in why

    def test_a_failed_venv_module_is_reported(self, lib, tmp_path, monkeypatch):
        os.mkdir(str(tmp_path / "e"))
        monkeypatch.setattr(lib, "run_child",
                            lambda *a, **k: (1, "", "Error: ... ensurepip is not available"))
        abs_, state, create = lib.validate_venv_path("e", str(tmp_path), windows=False)
        assert state == "empty"
        ok, why = lib.create_venv("/py", abs_, state, create, (3, 13, 9))
        assert ok is False
        assert "python3-venv" in why


MINS = {"python": "3.13", "packaging": "", "bokeh": "3.8", "numpy": "2.3", "pandas": "2.3"}
# WP-30 P1.33: the Python minimum is dash_setup.ado's own floor, never a copy.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_version_floor import _setup_ado_floor  # noqa: E402
MINS = dict(MINS, python=_setup_ado_floor()[0])


class TestVerifyIn:

    def test_a_bare_venv_reports_each_missing_package(self, lib, tmp_path):
        """Under any interpreter: the Python minimum is the running one's
        major.minor (WP-30 P1.33, D-05d), so the packages are reached."""
        vpy = _bare_venv(tmp_path / "bare")
        mins = dict(MINS, python="%d.%d" % sys.version_info[:2])
        got = lib.verify_in(vpy, RENDER, mins, sys.version_info)
        assert got["ok"] is False
        assert got["packages"] == {"packaging": "", "bokeh": "", "numpy": "", "pandas": ""}

    def test_a_venv_seeing_the_packages_passes_versions_and_schemes(self, lib, tmp_path):
        """The pass path of the packages and schemes, under any interpreter:
        the Python minimum is the running one's major.minor (WP-30 P1.33,
        D-05d); the floor has its own tests."""
        vpy = _bare_venv(tmp_path / "seeing")
        with open(os.path.join(_purelib(vpy), "dash_base.pth"), "w") as fh:
            fh.write(_purelib(sys.executable) + "\n")
        mins = dict(MINS, python="%d.%d" % sys.version_info[:2])
        got = lib.verify_in(vpy, RENDER, mins, sys.version_info)
        assert got["ok"] is True, got
        assert got["schemes"] is True
        assert all(got["packages"][n] for n in ("packaging", "bokeh", "numpy", "pandas"))

    def test_the_python_minimum_is_dash_setups_floor(self):
        assert MINS["python"] == _setup_ado_floor()[0]

    def test_a_venv_below_the_python_floor_is_refused(self, lib):
        got = lib.verify_in(sys.executable, RENDER, dict(MINS, python="99.0"), sys.version_info)
        assert got["ok"] is False
        assert got["why"] == "python"
        assert got["version"] == list(sys.version_info[:3])

    @pytest.mark.parametrize("reply", ["garbage", '{"tag": "OTHER", "ok": true}', ""])
    def test_a_malformed_reply_is_a_failure(self, lib, monkeypatch, reply):
        monkeypatch.setattr(lib, "run_child", lambda *a, **k: (0, reply, ""))
        assert lib.verify_in("/py", RENDER, MINS, (3, 13, 9)) == {"ok": False, "why": "malformed"}


class TestMessages:

    def test_below_the_floor_the_guidance_names_the_floor_and_never_venv(self, lib):
        """WP-30 P1.33: a private environment made from a Python below the
        floor is below it too, so the guidance points at a newer Python."""
        exe = "/opt/homebrew/bin/python3.10"
        for kind, what in (("managed", "externally managed (PEP 668)"),
                           ("nopip", "has no pip")):
            text, cmd = lib.below_floor_message(exe, "3.11", kind)
            assert cmd == ""
            for needle in (exe, "3.11 or later", "help python",
                           "restart Stata", what):
                assert needle in text, (kind, needle)
            assert "venv(" not in text
            assert "break-system-packages" not in text

    def test_the_managed_message_names_the_python_and_never_the_override_flag(self, lib):
        text, cmd = lib.managed_message("/opt/homebrew/bin/python3.13", False, {})
        assert cmd == 'dash_setup, venv("~/.dash/venv")'
        assert "externally managed (PEP 668)" in text
        assert "/opt/homebrew/bin/python3.13" in text and cmd in text
        assert "break-system-packages" not in text
        text, cmd = lib.managed_message("C:\\P\\python.exe", True, {"LOCALAPPDATA": "C:\\L"})
        assert cmd == 'dash_setup, venv("C:\\L\\dash\\venv")'
        assert "break-system-packages" not in text
        _, cmd = lib.managed_message("C:\\P\\python.exe", True, {"LOCALAPPDATA": "C:\\$x"})
        assert cmd == "dash_setup, venv(<a directory of your choice>)"

    def test_the_nopip_message_offers_ensurepip_only_where_it_works(self, lib):
        text, cmd = lib.nopip_message("/opt/My Python/python3", True, False, False)
        assert "This Python has no pip: /opt/My Python/python3" in text
        assert cmd == "'/opt/My Python/python3' -m ensurepip --upgrade"
        assert cmd in text
        for ens, man in ((False, False), (True, True)):
            text, cmd = lib.nopip_message("/p/python3", ens, man, False)
            assert cmd == ""
            assert "python3-pip" in text and "ensurepip" not in text

    def test_default_venv_path(self, lib):
        assert lib.default_venv_path(False, {}) == "~/.dash/venv"
        assert lib.default_venv_path(True, {"LOCALAPPDATA": "C:\\L"}) == "C:\\L\\dash\\venv"
        assert lib.default_venv_path(True, {}).endswith("AppData\\Local\\dash\\venv")


_INSTALLED_NONE = json.dumps({"tag": "DASH_INSTALLED_V1", "dists": {}})


def _installed_child(argv):
    """True for dash_setup_lib's installed-packages child (WP-32, I3)."""
    return "-c" in argv and "DASH_INSTALLED_V1" in argv[list(argv).index("-c") + 1]


@pytest.fixture
def fake_sfi(monkeypatch, tmp_path):
    store = {"local": {}, "exec": "/opt/x/bin/python3", "pwd": str(tmp_path)}

    class Macro:
        @staticmethod
        def getLocal(k):
            return store["local"].get(k, "")

        @staticmethod
        def setLocal(k, v):
            assert isinstance(v, str), (k, v)
            store["local"][k] = v

    class SFIToolkit:
        @staticmethod
        def macroExpand(s):
            return {"\x60c(python_exec)'": store["exec"], "\x60c(pwd)'": store["pwd"]}[s]

    mod = types.ModuleType("sfi")
    mod.Macro = Macro
    mod.SFIToolkit = SFIToolkit
    monkeypatch.setitem(sys.modules, "sfi", mod)
    return store


class TestStataEntryPoints:

    def test_stata_detect_sets_every_local(self, lib, fake_sfi, monkeypatch):
        monkeypatch.setattr(lib, "run_child", lambda argv, **k: (0, _detect_line(marker=True), ""))
        lib.stata_detect()
        loc = fake_sfi["local"]
        assert loc["det_ok"] == "1"
        assert loc["det_managed"] == "1"
        assert loc["det_in_venv"] == "0"
        assert loc["det_pip"] == "1" and loc["det_ensurepip"] == "1"
        assert loc["det_user"] == "0"
        assert loc["det_version"] == "3.13.9"
        assert loc["det_python"] == "/opt/x/bin/python3"
        monkeypatch.setattr(lib, "run_child", lambda argv, **k: (1, "", "boom"))
        lib.stata_detect()
        assert loc["det_ok"] == "0"

    def test_stata_pip_resolves_a_relative_exec(self, lib, fake_sfi, tmp_path, monkeypatch):
        (tmp_path / "vnp" / "bin").mkdir(parents=True)
        (tmp_path / "vnp" / "bin" / "python").write_text("")
        fake_sfi["exec"] = os.path.join("vnp", "bin", "python")
        fake_sfi["local"].update(spec="bokeh>=3.8", user="0", ver="3.13.9")
        seen = []
        # Flipped (WP-32, I3): the installed-packages child answers first.
        monkeypatch.setattr(lib, "run_child", lambda argv, **k: (
            seen.append(argv), (0, _INSTALLED_NONE, "") if _installed_child(argv)
            else (0, "", ""))[1])
        lib.stata_pip()
        assert seen[0][0] == str(tmp_path / "vnp" / "bin" / "python")
        assert seen[-1][0] == str(tmp_path / "vnp" / "bin" / "python")
        assert fake_sfi["local"]["pip_outcome"] == "ok"

    def test_stata_pip_retries_with_user_only_when_allowed_and_adds_the_user_site(
            self, lib, fake_sfi, monkeypatch, capsys):
        seen, added = [], []
        answers = []
        # Flipped (WP-32, I3): pip's vectors are recorded; the
        # installed-packages child before each is answered apart.
        monkeypatch.setattr(lib, "run_child", lambda argv, **k: (
            (0, _INSTALLED_NONE, "") if _installed_child(argv)
            else (seen.append(argv), answers.pop(0))[1]))
        monkeypatch.setattr(lib, "add_user_site", lambda: added.append(1) or True)
        loc = fake_sfi["local"]
        loc.update(spec="bokeh>=3.8", user="1", ver="3.13.9")
        answers[:] = [(1, "", "ERROR: something"), (0, "done", "")]
        lib.stata_pip()
        assert "--user" not in seen[0] and "--user" in seen[1]
        assert loc["pip_user"] == "1" and loc["pip_outcome"] == "ok"
        assert added == [1]
        assert "retrying with --user..." in capsys.readouterr().out
        seen[:] = []
        loc["user"] = "0"
        answers[:] = [(1, "", "ERROR: something")]
        lib.stata_pip()
        assert len(seen) == 1 and loc["pip_user"] == "0" and loc["pip_outcome"] == "other"
        seen[:] = []
        loc["user"] = "1"
        answers[:] = [(1, "", FIX["externally_managed"]["stderr"])]
        lib.stata_pip()
        assert len(seen) == 1
        assert loc["pip_outcome"] == "externally-managed"
        out = capsys.readouterr().out
        assert "error: externally-managed-environment" in out
        assert "break-system-packages" not in out

    def test_stata_pip_never_raises_into_stata(self, lib, fake_sfi, monkeypatch, capsys):
        seen = []
        monkeypatch.setattr(lib, "run_child", lambda argv, **k: (seen.append(argv), (0, "", ""))[1])
        fake_sfi["local"].update(spec="x; y", user="1", ver="3.13.9")
        lib.stata_pip()
        assert seen == []
        assert fake_sfi["local"]["pip_outcome"] == "other"
        assert "refusing the requirement" in capsys.readouterr().out

        def broken(argv, **k):
            raise RuntimeError("probe")
        monkeypatch.setattr(lib, "run_child", broken)
        fake_sfi["local"].update(spec="bokeh>=3.8", pip_outcome="ok")
        lib.stata_pip()
        assert fake_sfi["local"]["pip_outcome"] == "other"
        assert "dash_setup: internal error: RuntimeError: probe" in capsys.readouterr().out

    def test_stata_shell_line_names_the_linked_interpreter_quoted(self, lib, fake_sfi, capsys):
        fake_sfi["exec"] = "/opt/My Python/bin/python3"
        fake_sfi["local"].update(spec="bokeh>=3.8", how="upgrade")
        lib.stata_shell_line()
        want = "'/opt/My Python/bin/python3' -m pip install 'bokeh>=3.8'"
        assert fake_sfi["local"]["pip_cmd"] == want
        assert fake_sfi["local"]["pip_note"] == ""
        assert "To upgrade: " + want in capsys.readouterr().out

    def test_stata_undo_line_names_the_linked_interpreter(self, lib, fake_sfi, capsys):
        fake_sfi["exec"] = "/opt/My Python/bin/python3"
        fake_sfi["local"].update(pkgs=" packaging  numpy")
        lib.stata_undo_line()
        want = "'/opt/My Python/bin/python3' -m pip uninstall packaging numpy"
        assert fake_sfi["local"]["pip_cmd"] == want
        assert "To undo: " + want in capsys.readouterr().out
        fake_sfi["local"].update(pkgs="numpy {bf:x}")
        lib.stata_undo_line()
        assert fake_sfi["local"]["pip_cmd"] == ""
        assert "To undo:" not in capsys.readouterr().out

    def test_stata_guide_prints_plain_text(self, lib, fake_sfi, capsys):
        fake_sfi["exec"] = "/opt/{bf:X}/python3"
        fake_sfi["local"].update(kind="managed", ensurepip="1", managed="1")
        lib.stata_guide()
        out = capsys.readouterr().out
        assert "/opt/{bf:X}/python3" in out
        assert fake_sfi["local"]["guide_cmd"] == 'dash_setup, venv("~/.dash/venv")'
        assert not hasattr(sys.modules["sfi"].SFIToolkit, "display")
        fake_sfi["local"].update(kind="nopip", ensurepip="1", managed="0")
        lib.stata_guide()
        assert fake_sfi["local"]["guide_cmd"] == "'/opt/{bf:X}/python3' -m ensurepip --upgrade"

    def test_stata_guide_below_the_floor_suggests_no_venv(self, lib, fake_sfi, capsys):
        """WP-30 P1.33: below the floor neither guidance kind suggests
        venv(), and the command handed back is empty."""
        fake_sfi["local"].update(kind="managed", ensurepip="1", managed="1",
                                 pyok="0", pymin="3.11")
        lib.stata_guide()
        out = capsys.readouterr().out
        assert fake_sfi["local"]["guide_cmd"] == ""
        assert "venv(" not in out
        assert "3.11 or later" in out
        fake_sfi["local"].update(kind="nopip", ensurepip="1", managed="0")
        lib.stata_guide()
        out = capsys.readouterr().out
        assert fake_sfi["local"]["guide_cmd"] == ""
        assert "venv(" not in out and "has no pip" in out
        fake_sfi["local"].update(kind="managed", pyok="1")
        lib.stata_guide()
        assert fake_sfi["local"]["guide_cmd"] == 'dash_setup, venv("~/.dash/venv")'
        capsys.readouterr()
        fake_sfi["local"].update(pyok="0", pymin="abc")
        lib.stata_guide()
        out = capsys.readouterr().out
        assert fake_sfi["local"]["guide_cmd"] == 'dash_setup, venv("~/.dash/venv")'
        assert "externally managed (PEP 668)" in out

    def test_stata_venv_check_and_stata_venv_with_a_recorded_run(self, lib, fake_sfi, tmp_path,
                                                                 monkeypatch, capsys):
        seen = []

        def run(argv, **k):
            seen.append(list(argv))
            if "venv" in argv:
                return _fake_venv_run(argv)
            code = argv[argv.index("-c") + 1] if "-c" in argv else ""
            if "DASH_DETECT_V1" in code:
                return 0, _detect_line(prefix="/v", base_prefix="/b"), ""
            if "DASH_VERIFY_V1" in code:
                return 0, json.dumps({"tag": "DASH_VERIFY_V1", "ok": True, "version": [3, 13, 9],
                                      "packages": {}, "schemes": True, "why": ""}), ""
            if "DASH_INSTALLED_V1" in code:
                return 0, _INSTALLED_NONE, ""
            return 0, "Successfully installed", ""
        monkeypatch.setattr(lib, "run_child", run)
        loc = fake_sfi["local"]
        loc["venv"] = "env"
        lib.stata_venv_check()
        absp = os.path.join(os.path.realpath(str(tmp_path)), "env")
        assert loc["venv_ok"] == "1"
        # WP-30 P1.30: _dash_setup_venv passes bokeh's ceiling as maxb.
        loc.update(pymin="3.13", minb="3.8", minn="2.3", minp="2.3", maxb="3.10")
        lib.stata_venv()
        vpy = os.path.join(absp, "bin", "python")
        assert loc["venv_step"] == ""
        assert loc["venv_cmd"] == 'python set exec "%s", permanently' % vpy
        assert loc["venv_linked"] == "0"
        assert loc["venv_python"] == vpy
        assert loc["venv_base"] == "/opt/x/bin/python3"
        # Flipped (WP-32, I3): the installed-packages child runs before pip.
        assert [a[0] for a in seen] == ["/opt/x/bin/python3", vpy, vpy, vpy, vpy]
        assert "--require-hashes" in seen[3]
        assert "Restart Stata" in capsys.readouterr().out
        loc["venv"] = 'a"b'
        lib.stata_venv_check()
        assert loc["venv_ok"] == "0"
        lib.stata_venv()
        assert loc["venv_step"] == "internal"


class TestModuleShape:

    def test_stdlib_only_python38_parseable_and_run_looked_up_at_call_time(self, lib, monkeypatch):
        assert lib.TIMEOUT == 1800
        with open(LIB, encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src, feature_version=(3, 8))
        names = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module.split(".")[0])
        assert names and names <= set(sys.stdlib_module_names), names - set(sys.stdlib_module_names)
        assert "from subprocess import" not in src
        assert "from site import" not in src
        assert "shell=True" not in src
        assert "break-system-packages" not in src
        assert src.count("PIP_BREAK_SYSTEM_PACKAGES") == 1
        assert '"PIP_BREAK_SYSTEM_PACKAGES": "0"' in src
        lines = [l.strip() for l in src.splitlines() if l.strip()]
        um = [i for i, l in enumerate(lines) if "umask" in l]
        assert len(um) == 1
        assert lines[um[0] - 1] == 'if os.name == "posix" and tuple(runtime[:2]) >= (3, 9):'

        def boom(*a, **k):
            raise AssertionError("a process was started at import")
        monkeypatch.setattr(subprocess, "run", boom)
        monkeypatch.setattr(subprocess, "Popen", boom)
        assert _load("dash_setup_lib_import_check").TIMEOUT == 1800


class TestLiveRefusal:

    def test_a_real_externally_managed_python_is_detected_and_refused(self, lib, offline):
        for exe in (sys.executable, "/opt/homebrew/bin/python3.13", "/usr/bin/python3"):
            if os.path.exists(exe) and lib.detect_environment(exe).get("externally_managed"):
                rc, out, err = lib.run_child([exe, "-m", "pip", "install", "--dry-run",
                                              "--no-index", "bokeh>=3.8"])
                assert lib.classify_failure(rc, err) == "externally-managed"
                break
        else:
            pytest.skip("no externally managed Python on this host")


class TestTheFixture:

    def test_pip_refusals_has_its_meta_and_records(self):
        assert sorted(FIX) == ["_meta", "externally_managed", "no_pip", "offline_no_match",
                               "user_disabled", "user_in_venv"]
        assert sorted(FIX["_meta"]) == ["born_date", "dash_commit", "extracted", "pip_version",
                                        "python_version", "source", "stata_version"]
        for k, rec in FIX.items():
            if k != "_meta":
                assert isinstance(rec["argv"], list) and isinstance(rec["rc"], int)
                assert rec["stderr"]


class TestTheBokehWindow:
    """WP-30 P1.30 (M9, A107): dash_setup installs bokeh inside the
    verified window, and never downgrades a bokeh at or above its ceiling
    (critic C5: a reused venv's newer bokeh)."""

    def test_the_requirement_never_downgrades(self, lib):
        rows = {"": "bokeh>=3.8,<3.10", None: "bokeh>=3.8,<3.10",
                "3.7.3": "bokeh>=3.8,<3.10", "3.9.2": "bokeh>=3.8,<3.10",
                "garbage": "bokeh>=3.8,<3.10", "3.10.0": "bokeh>=3.8",
                "3.10.0rc1": "bokeh>=3.8", "4.1": "bokeh>=3.8"}
        bad = {v: lib.bokeh_requirement(v, "3.8", "3.10") for v in rows
               if lib.bokeh_requirement(v, "3.8", "3.10") != rows[v]}
        assert not bad, bad
        assert all(lib._SPEC_RE.fullmatch(s) for s in rows.values())
        with pytest.raises(ValueError):
            lib.bokeh_requirement("", "3.8; rm", "3.10")

    def test_the_venv_route_downgrades_nothing(self, lib, fake_sfi, tmp_path,
                                               monkeypatch, capsys):
        def run_with(have, state):
            seen, reqs = [], []

            def run(argv, **k):
                seen.append(list(argv))
                if "venv" in argv:
                    return _fake_venv_run(argv)
                code = argv[argv.index("-c") + 1] if "-c" in argv else ""
                if "DASH_DETECT_V1" in code:
                    return 0, _detect_line(prefix="/v", base_prefix="/b"), ""
                if "DASH_VERIFY_V1" in code:
                    above = ["bokeh"] if have.startswith("3.10") else []
                    return 0, json.dumps({
                        "tag": "DASH_VERIFY_V1", "ok": True,
                        "version": [3, 13, 9], "packages": {"bokeh": have},
                        "schemes": True, "why": "", "above": above}), ""
                if "DASH_INSTALLED_V1" in code:
                    return 0, json.dumps({"tag": "DASH_INSTALLED_V1",
                                          "dists": {"bokeh": have} if have else {}}), ""
                if "-r" in argv:
                    with open(argv[argv.index("-r") + 1], encoding="utf-8") as fh:
                        reqs.append(fh.read())
                return 0, "Successfully installed", ""
            monkeypatch.setattr(lib, "run_child", run)
            absp = str(tmp_path / ("env_%s_%s" % (state, have)))
            if state == "venv":
                _fake_venv_run(["venv", absp])
            lib._PENDING["venv"] = (absp, state, [])
            fake_sfi["local"].update(pymin="3.11", minb="3.8", minn="2.3",
                                     minp="2.3", maxb="3.10")
            lib.stata_venv()
            assert fake_sfi["local"]["venv_step"] == "", capsys.readouterr()
            pip = [a for a in seen if "pip" in a]
            assert len(pip) == 1, seen
            # Flipped (WP-32, I3): pip reads the lock's lines, hash-checked;
            # an installed bokeh inside the requirement's window has none.
            assert "--require-hashes" in pip[0]
            assert not [a for a in pip[0] if a.startswith("bokeh")]
            return [ln.split(" ")[0] for ln in reqs[0].splitlines()
                    if ln.startswith("bokeh==")], capsys.readouterr().out

        rows = [("", "new", True, False),
                ("3.10.0", "venv", False, True),
                ("3.9.0", "venv", False, False)]
        for have, state, listed, left in rows:
            spec, out = run_with(have, state)
            assert bool(spec) is listed, (have, state, spec)
            assert all(re.fullmatch(r"bokeh==3\.(8|9)\.\d+", s) for s in spec), spec
            assert ("it was left as it is" in out) is left, (have, out)

    def test_verify_reports_above_without_failing(self, lib):
        import bokeh
        mm = tuple(int(x) for x in bokeh.__version__.split(".")[:2])
        mins = dict(MINS, python="%d.%d" % sys.version_info[:2])
        rows = {"%d.%d" % mm: ["bokeh"], "%d.%d" % (mm[0], mm[1] + 1): []}
        for ceil, want in rows.items():
            got = lib.verify_in(sys.executable, RENDER,
                                dict(mins, bokeh_ceil=ceil), sys.version_info)
            assert got["above"] == want, (ceil, got)
            assert got["ok"] is True, got


# ---------------------------------------------------------------------------
# WP-31 I3: dash_setup's wiring (read from dash_setup.ado)
# ---------------------------------------------------------------------------

def _setup_program(name):
    with open(os.path.join(ROOT, "dash_setup.ado"), encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    start = next(i for i, l in enumerate(lines)
                 if l == "program define " + name
                 or l.startswith("program define %s," % name))
    return [l.strip() for l in lines[start:lines.index("end", start)]]


#: The two lines that keep the working directory off the import path for
#: one probe, and put sys.path back (dash.ado uses the same pair).
PATH_PRUNE = ('python: import sys, os; _dash_sp = list(sys.path); '
              'sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]')
PATH_RESTORE = 'python: import sys; sys.path[:] = _dash_sp'


class TestTheSetupWiring:

    def test_every_summary_gets_the_warnings_and_the_installs_apart(self):
        body = " ".join(_setup_program("dash_setup"))
        calls = body.split("_dash_setup_summary ,")[1:]
        assert len(calls) >= 10
        for c in calls:
            head = c.split("_dash_setup_summary")[0][:400]
            assert 'items(`"`fail_items\'"\')' in head, head
            assert 'warnitems(`"`warn_items\'"\')' in head, head
            assert 'installed(`"`installed_now\'"\')' in head, head
        assert "`fail_items'`warn_items'" not in body

    def test_an_install_pip_reports_ok_is_recorded(self):
        body = _setup_program("dash_setup")
        pips = [i for i, l in enumerate(body) if l.startswith("_dash_setup_pip ")]
        assert len(pips) == 2
        for i in pips:
            nxt = body[i + 1:i + 4]
            assert any(l.startswith('if "`r(outcome)\'" == "ok" local installed_now')
                       for l in nxt), nxt

    def test_every_import_probe_runs_off_the_working_directory(self):
        body = _setup_program("dash_setup")
        probes = [i for i, l in enumerate(body)
                  if l.startswith("capture python: import ")]
        assert len(probes) == 5  # the any-missing loop, packaging twice, each package twice
        for i in probes:
            assert body[i - 1] == PATH_PRUNE, body[i - 1]
            assert body[i + 2] == PATH_RESTORE, body[i + 1:i + 3]

    def test_the_lib_beside_dash_setup_is_taken_before_the_ado_path(self):
        body = _setup_program("_dash_setup_lib")
        beside = next(i for i, l in enumerate(body) if "findfile dash_setup.ado" in l)
        search = next(i for i, l in enumerate(body) if "findfile dash_setup_lib.py" in l)
        assert beside < search
