"""scripts/run_all_tests.sh: the whole default suite on at most 8 workers."""

import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "run_all_tests.sh")


def _dry(**env):
    e = dict(os.environ, DRY_RUN="1")
    for k in ("PYTEST_WORKERS", "DASH_CERT_SESSIONS", "DASH_MAX_WORKERS"):
        e.pop(k, None)
    e.update(env)
    return subprocess.run(["sh", SCRIPT], env=e, capture_output=True,
                          text=True, timeout=30)


class TestTheWorkerBudget:
    def test_the_default_is_eight_pytest_workers_then_eight_sessions(self):
        # Eight sessions since 11nov2026 (the shard table turns the split
        # scripts' parts so that eight finish together).
        r = _dry()
        assert r.returncode == 0, r.stdout + r.stderr
        assert "-n 8" in r.stdout
        assert "DASH_CERT_SESSIONS=8" in r.stdout
        # The batch-end suite keeps the batch tier (test_mode_parity.py
        # and the files test_test_tiers.py lists).
        assert "DASH_TEST_TIER=batch" in r.stdout

    def test_more_than_eight_pytest_workers_is_refused_and_runs_nothing(self):
        r = _dry(PYTEST_WORKERS="9")
        assert r.returncode == 2
        assert "exceed 8 workers" in r.stdout
        assert "pytest:" not in r.stdout

    def test_eight_exactly_is_allowed(self):
        r = _dry(PYTEST_WORKERS="8", DASH_CERT_SESSIONS="8")
        assert r.returncode == 0 and "-n 8" in r.stdout

    def test_more_than_eight_sessions_is_refused(self):
        r = _dry(PYTEST_WORKERS="1", DASH_CERT_SESSIONS="9")
        assert r.returncode == 2

    def test_a_count_that_is_not_a_number_is_refused(self):
        r = _dry(PYTEST_WORKERS="6; rm -rf /")
        assert r.returncode == 2
        assert "whole numbers" in r.stdout


class TestTheWiring:
    def test_make_test_all_runs_the_script(self):
        with open(os.path.join(ROOT, "Makefile"), encoding="utf-8") as fh:
            mk = fh.read()
        assert "test-all:\n\t@PYTHON='$(PYTHON)' STATA_BIN='$(STATA_BIN)' " \
               "sh scripts/run_all_tests.sh" in mk

    def test_the_halves_run_one_after_the_other(self):
        # Side by side, pytest's serve tests and the fixed-port
        # certification scripts fought over ports (07oct2026).
        with open(SCRIPT, encoding="utf-8") as fh:
            sh = fh.read()
        assert " &\n" not in sh and "wait " not in sh
        assert sh.index("-m pytest test/") < sh.index("run_cert_suite.sh >")


class TestTheTiming:
    """The gate records where its time goes (the maintainer, 22oct2026:
    the whole suite takes about 33 minutes against the five-minute target)."""

    def test_pytest_reports_its_slowest_tests(self):
        r = _dry()
        assert r.returncode == 0, r.stdout + r.stderr
        assert "--durations=0" in r.stdout
        assert "--durations-min=1" in r.stdout

    def test_pytest_writes_every_tests_time(self):
        """Phases under a second hold most of the suite's time (02nov2026:
        1,403 of about 4,900 worker seconds were listed), so pytest also
        writes the per-test report test/suite_timing.py keeps."""
        r = _dry()
        assert "DASH_SUITE_TIMING=" in r.stdout
        with open(SCRIPT, encoding="utf-8") as fh:
            assert 'DASH_SUITE_TIMING="$out/pytest_timing.json"' in fh.read()

    def test_the_timing_report_is_written_beside_the_logs(self):
        with open(SCRIPT, encoding="utf-8") as fh:
            sh = fh.read()
        assert 'scripts/gate_timing.py "$out"' in sh
        assert sh.index('scripts/gate_timing.py "$out"') > \
            sh.index("run_cert_suite.sh >")
