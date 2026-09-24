"""test_setup_sandbox.py -- the sandbox dash_setup is run in installs nothing.

test/setup_sandbox.py lets test_program_coverage.cscript run dash_setup end
to end (PC-14..26) without pip or ssc touching the machine.  Its promise is
the reason that is safe to do, so each part of it is held here on its own,
in plain Python: every process start is recorded and none is made, the
recording stubs lead nowhere real, the simulated states appear and vanish,
and restore() puts back every object it replaced.
"""
import asyncio
import importlib
import importlib.metadata
import json
import os
import subprocess
import sys
import types

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import setup_sandbox as sb  # noqa: E402

_REAL_RUN = subprocess.run
_REAL_POPEN = subprocess.Popen
_REAL_SYSTEM = os.system
_REAL_EXE = sys.executable


@pytest.fixture(autouse=True)
def _always_restored():
    """Whatever a test does, nothing it patched outlives it: the process
    functions, sys.executable, sys.version, sys.path and PATH."""
    sb.restore()
    path0, syspath0 = os.environ.get("PATH"), list(sys.path)
    version0 = sys.version
    yield
    sb.restore()
    assert subprocess.run is _REAL_RUN
    assert subprocess.Popen is _REAL_POPEN
    assert os.system is _REAL_SYSTEM
    assert sys.executable == _REAL_EXE
    assert sys.version == version0
    assert os.environ.get("PATH") == path0
    assert sys.path == syspath0


def _marker_code(path):
    return "open(%r, 'w').close()" % str(path)


class TestNoProcessIsStarted:

    def test_run_is_recorded_and_not_made(self, tmp_path):
        sb.install()
        mk = tmp_path / "m"
        r = subprocess.run([sys.executable, "-c", _marker_code(mk)],
                           capture_output=True, text=True)
        assert not mk.exists()
        assert r.returncode == sb._STUB_RC
        assert "no process was started" in r.stdout
        assert sb.calls() == [{"via": "subprocess.run",
                               "argv": ["PYTHON", "-c", _marker_code(mk)]}]

    @pytest.mark.parametrize("how", [
        "call", "check_call", "check_output", "Popen", "getoutput",
        "getstatusoutput", "system", "popen", "execv", "spawnv",
        "posix_spawn", "create_subprocess_exec"])
    def test_every_way_to_start_a_process_is_recorded(self, tmp_path, how):
        sb.install()
        mk = tmp_path / "m"
        argv = [_REAL_EXE, "-c", _marker_code(mk)]
        cmd = " ".join(argv[:2]) + " " + json.dumps(argv[2])
        try:
            if how == "call":
                assert subprocess.call(argv) == sb._STUB_RC
            elif how == "check_call":
                with pytest.raises(subprocess.CalledProcessError):
                    subprocess.check_call(argv)
            elif how == "check_output":
                with pytest.raises(subprocess.CalledProcessError):
                    subprocess.check_output(argv)
            elif how == "Popen":
                with subprocess.Popen(argv) as p:
                    assert p.wait() == sb._STUB_RC
            elif how == "getoutput":
                subprocess.getoutput(cmd)
            elif how == "getstatusoutput":
                assert subprocess.getstatusoutput(cmd)[0] == sb._STUB_RC
            elif how == "system":
                assert os.system(cmd) != 0
            elif how == "popen":
                with pytest.raises(OSError):
                    os.popen(cmd)
            elif how == "execv":
                with pytest.raises(OSError):
                    os.execv(argv[0], argv)
            elif how == "spawnv":
                with pytest.raises(OSError):
                    os.spawnv(os.P_WAIT, argv[0], argv)
            elif how == "posix_spawn":
                with pytest.raises(OSError):
                    os.posix_spawn(argv[0], argv, dict(os.environ))
            elif how == "create_subprocess_exec":
                with pytest.raises(OSError):
                    asyncio.run(asyncio.create_subprocess_exec(*argv))
        finally:
            recorded = sb.calls()
        assert not mk.exists()
        assert len(recorded) == 1
        assert how in recorded[0]["via"]

    def test_sys_executable_and_path_lead_to_recording_stubs(self):
        sb.install()
        stubdir = os.path.dirname(sys.executable)
        assert os.environ["PATH"].split(os.pathsep)[0] == stubdir
        for name in ("pip", "pip3", "python", "python3", "conda", "uv"):
            p = os.path.join(stubdir, name)
            assert os.access(p, os.X_OK), name
        # Even the original subprocess.run starts nothing in the sandbox:
        # it builds on subprocess.Popen, which is replaced too.
        r = _REAL_RUN([os.path.join(stubdir, "pip"), "install", "x"],
                      capture_output=True, text=True)
        assert r.returncode == sb._STUB_RC
        assert sb.stub_calls() == []
        assert sb.calls()[-1]["via"] == "subprocess.Popen"
        # Through the original Popen the stub really runs: it records its
        # arguments and fails, and installs nothing.
        p = _REAL_POPEN([os.path.join(stubdir, "pip"), "install", "x"])
        assert p.wait() == sb._STUB_RC
        assert len(sb.stub_calls()) == 1
        assert sb.stub_calls()[0].endswith("pip install x")

    def test_self_test_catches_a_recorder_that_is_not_there(self, tmp_path):
        sb.install()
        # As if neither patch had taken: the probe then runs for real, makes
        # its marker, and the self-test says so.
        subprocess.run = _REAL_RUN
        subprocess.Popen = _REAL_POPEN
        with pytest.raises(RuntimeError, match="a process ran"):
            sb.self_test()

    def test_a_failed_install_leaves_nothing_patched(self, monkeypatch):
        def broken():
            raise RuntimeError("probe")
        monkeypatch.setattr(sb, "self_test", broken)
        with pytest.raises(RuntimeError, match="probe"):
            sb.install()
        assert not sb.is_installed()
        assert subprocess.run is _REAL_RUN
        assert sys.executable == _REAL_EXE

    def test_install_twice_is_refused(self):
        sb.install()
        with pytest.raises(RuntimeError, match="already installed"):
            sb.install()
        assert sb.is_installed()

    def test_restore_twice_is_harmless(self):
        sb.install()
        sb.restore()
        sb.restore()
        assert not sb.is_installed()


class TestTheSimulatedStates:

    def test_a_blocked_package_cannot_be_imported_and_comes_back(self):
        import colorsys
        sb.install(block=("colorsys",))
        with pytest.raises(ImportError):
            importlib.import_module("colorsys")
        sb.restore()
        assert importlib.import_module("colorsys") is colorsys

    def test_a_recorded_install_lifts_the_block(self):
        sb.install(block=("colorsys",), unblock_on_install=("colorsys",))
        with pytest.raises(ImportError):
            importlib.import_module("colorsys")
        subprocess.run([sys.executable, "-m", "pip", "install", "colorsys>=1"])
        importlib.import_module("colorsys")
        assert sb.calls()[0]["argv"] == ["PYTHON", "-m", "pip", "install",
                                         "colorsys>=1"]

    def test_an_install_of_another_package_lifts_nothing(self):
        sb.install(block=("colorsys",), unblock_on_install=("colorsys",))
        subprocess.run([sys.executable, "-m", "pip", "install", "colorsysx"])
        with pytest.raises(ImportError):
            importlib.import_module("colorsys")

    def test_a_fake_distribution_is_found_first_and_goes(self):
        sb.install(fake=[("dashzzsandboxfake", "9.9.9")])
        assert importlib.metadata.version("dashzzsandboxfake") == "9.9.9"
        sb.restore()
        with pytest.raises(importlib.metadata.PackageNotFoundError):
            importlib.metadata.version("dashzzsandboxfake")

    def test_the_python_version_is_replaced_and_restored(self):
        before = sys.version
        sb.install(pyversion="3.7.9 (sandbox)")
        assert sys.version.split()[0] == "3.7.9"
        sb.restore()
        assert sys.version == before


class TestTheStataWrappers:
    """stata_install / stata_verdict / stata_restored, against a stand-in
    for Stata's sfi.Macro."""

    @pytest.fixture
    def macro(self, monkeypatch):
        store = {"global": {}, "local": {}}
        fake = types.ModuleType("sfi")

        class Macro:
            @staticmethod
            def getGlobal(k):
                return store["global"].get(k, "")

            @staticmethod
            def setLocal(k, v):
                store["local"][k] = v

            @staticmethod
            def getLocal(k):
                return store["local"].get(k, "")
        fake.Macro = Macro
        monkeypatch.setitem(sys.modules, "sfi", fake)
        return store

    def test_install_reports_ok_and_verdict_matches(self, macro, tmp_path):
        macro["global"]["PC_SB_SPEC"] = json.dumps({"pyversion": "3.9.1 x"})
        sb.stata_install()
        assert macro["local"]["pc_sb_ok"] == "1"
        assert sys.version.startswith("3.9.1")
        subprocess.run([sys.executable, "-m", "pip", "install", "a>=1"])
        macro["global"]["PC_SB_EXPECT"] = json.dumps(
            [["PYTHON", "-m", "pip", "install", "a>=1"]])
        sb.stata_verdict()
        assert macro["local"]["pc_sb_match"] == "1"
        assert macro["local"]["pc_sb_n"] == "1"
        macro["global"]["PC_SB_EXPECT"] = "[]"
        sb.stata_verdict()
        assert macro["local"]["pc_sb_match"] == "0"
        assert "a>=1" in macro["local"]["pc_sb_mwhy"]
        sb.restore()
        sb.stata_restored()
        assert macro["local"]["pc_sb_clean"] == "1"

    def test_install_reports_a_failure_and_patches_nothing(self, macro):
        macro["global"]["PC_SB_SPEC"] = "{not json"
        sb.stata_install()
        assert macro["local"]["pc_sb_ok"] == "0"
        assert "JSONDecodeError" in macro["local"]["pc_sb_why"]
        assert not sb.is_installed()
        assert subprocess.run is _REAL_RUN

    def test_restored_is_zero_while_installed(self, macro):
        sb.install()
        sb.stata_restored()
        assert macro["local"]["pc_sb_clean"] == "0"

    def test_a_stub_that_ran_fails_the_verdict(self, macro):
        """A process that got past the recorders and reached a PATH stub is
        a mismatch even when the recorded calls are exactly as expected."""
        sb.install()
        stub = os.path.join(os.path.dirname(sys.executable), "pip")
        assert _REAL_POPEN([stub, "install", "y"]).wait() == sb._STUB_RC
        macro["global"]["PC_SB_EXPECT"] = "[]"
        sb.stata_verdict()
        assert macro["local"]["pc_sb_match"] == "0"
        assert "pip install y" in macro["local"]["pc_sb_mwhy"]
