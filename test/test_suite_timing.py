"""The suite timing report (test/suite_timing.py): unit and end-to-end tests."""

import json
import os
import subprocess
import sys
import textwrap
from types import SimpleNamespace

from test import suite_timing as st

HERE = os.path.dirname(os.path.abspath(__file__))


class TestTheHelpers:
    def test_file_of_strips_the_test_path(self):
        assert st._file_of("test/test_a.py::TestX::test_y") == "test/test_a.py"
        assert st._file_of("test/test_a.py") == "test/test_a.py"

    def test_worker_of_reads_the_xdist_gateway(self):
        rep = SimpleNamespace(node=SimpleNamespace(
            gateway=SimpleNamespace(id="gw3")))
        assert st._worker_of(rep) == "gw3"

    def test_worker_of_is_main_without_xdist(self):
        assert st._worker_of(SimpleNamespace()) == "main"

    def test_summarise_totals_by_test_file_worker_and_phase(self):
        recs = [
            ("t/a.py::x", "setup", "gw0", 1.0),
            ("t/a.py::x", "call", "gw0", 2.0),
            ("t/a.py::y", "call", "gw1", 0.5),
            ("t/b.py::z", "call", "gw1", 4.0),
            ("t/b.py::z", "teardown", "gw1", 0.25),
        ]
        s = st.summarise(recs, wall=10.0)
        assert s["wall_seconds"] == 10.0
        assert s["tests"] == 3
        assert s["test_seconds"] == 7.75
        assert s["phases"] == {"call": 6.5, "setup": 1.0, "teardown": 0.25}
        assert s["workers"] == [{"worker": "gw1", "seconds": 4.75},
                                {"worker": "gw0", "seconds": 3.0}]
        assert s["files"][0] == {"file": "t/b.py", "seconds": 4.25, "tests": 1}
        assert s["files"][1] == {"file": "t/a.py", "seconds": 3.5, "tests": 2}
        assert s["slowest_tests"][0] == {"test": "t/b.py::z", "seconds": 4.25}

    def test_summarise_of_nothing_is_empty(self):
        s = st.summarise([], wall=0.0)
        assert s["tests"] == 0 and s["files"] == [] and s["workers"] == []

    def test_format_summary_names_wall_workers_files_and_tests(self):
        s = st.summarise([("t/a.py::x", "call", "gw0", 2.0)], wall=3.0)
        text = "\n".join(st.format_summary(s))
        assert "wall 3.0s" in text and "gw0 2.0" in text
        assert "t/a.py" in text and "t/a.py::x" in text


class TestTheRegistration:
    def _config(self, worker=False):
        reg = []
        cfg = SimpleNamespace(pluginmanager=SimpleNamespace(
            register=lambda p, name: reg.append((p, name))))
        if worker:
            cfg.workerinput = {}
        return cfg, reg

    def test_nothing_is_registered_without_the_variable(self, monkeypatch):
        monkeypatch.delenv(st.ENV, raising=False)
        cfg, reg = self._config()
        assert st.register(cfg) is None and reg == []

    def test_a_worker_never_registers(self, monkeypatch, tmp_path):
        monkeypatch.setenv(st.ENV, str(tmp_path / "t.json"))
        cfg, reg = self._config(worker=True)
        assert st.register(cfg) is None and reg == []

    def test_the_controller_registers_one_plugin(self, monkeypatch, tmp_path):
        monkeypatch.setenv(st.ENV, str(tmp_path / "t.json"))
        cfg, reg = self._config()
        plugin = st.register(cfg)
        assert reg == [(plugin, "dash-suite-timing")]
        assert plugin.path == str(tmp_path / "t.json")

    def test_a_report_without_a_duration_is_ignored(self, tmp_path):
        p = st.SuiteTiming(str(tmp_path / "t.json"))
        p.pytest_runtest_logreport(SimpleNamespace(nodeid="a", when="call"))
        assert p.records == []


class TestEndToEnd:
    """Run a two-test throwaway suite through pytest with the variable set."""

    def _run(self, tmp_path, *extra):
        (tmp_path / "conftest.py").write_text(textwrap.dedent("""
            import sys
            sys.path.insert(0, %r)
            from test import suite_timing
            def pytest_configure(config):
                suite_timing.register(config)
        """ % os.path.dirname(HERE)))
        (tmp_path / "test_sample.py").write_text(textwrap.dedent("""
            import time
            def test_fast():
                pass
            def test_slow():
                time.sleep(0.2)
        """))
        out = tmp_path / "timing.json"
        env = dict(os.environ, **{st.ENV: str(out)})
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             "-o", "addopts=", *extra, str(tmp_path)],
            cwd=str(tmp_path), env=env, capture_output=True, text=True,
            timeout=120)
        assert r.returncode == 0, r.stdout + r.stderr
        return json.loads(out.read_text()), r.stdout

    def test_one_process_writes_the_report(self, tmp_path):
        s, stdout = self._run(tmp_path)
        assert s["tests"] == 2
        assert s["slowest_tests"][0]["test"].endswith("test_slow")
        assert s["slowest_tests"][0]["seconds"] >= 0.2
        assert "suite timing" in stdout

    def test_xdist_workers_are_named(self, tmp_path):
        s, _ = self._run(tmp_path, "-n", "2")
        assert s["tests"] == 2
        assert {w["worker"] for w in s["workers"]} <= {"gw0", "gw1"}
