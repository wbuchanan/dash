"""The suite refuses to run twice at once.

conftest.py takes an advisory lock when an invocation covers the whole
suite.  These tests pin down what counts as the whole suite, and that a
second full run exits immediately naming the holder while a targeted run
is left alone.  The subprocesses use their own lock file so that the
session running these tests, which holds the real lock, does not interfere.
"""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from conftest import _covers_whole_suite  # noqa: E402

fcntl = pytest.importorskip("fcntl")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))


class TestWhatCountsAsTheWholeSuite:
    @pytest.mark.parametrize("args", [
        [], ["test/"], ["test"], [_ROOT], [os.path.join(_ROOT, "test")],
        ["test/", "."],
    ])
    def test_the_root_or_the_test_directory_is_the_whole_suite(self, args):
        assert _covers_whole_suite(args, _ROOT)

    @pytest.mark.parametrize("args", [
        ["test/test_kpi.py"],
        ["test/test_kpi.py::TestKpi::test_mean"],
        ["test/", "test/test_kpi.py"],
        [os.path.join(_ROOT, "test", "fixtures")],
    ])
    def test_a_file_a_node_id_or_a_subdirectory_is_not(self, args):
        assert not _covers_whole_suite(args, _ROOT)

    def test_k_last_failed_and_collect_only_are_not(self):
        assert not _covers_whole_suite(["test/"], _ROOT, keyword="kpi")
        assert not _covers_whole_suite(["test/"], _ROOT, lastfailed=True)
        assert not _covers_whole_suite(["test/"], _ROOT, collectonly=True)


def _run(args, lock_path, workers="0"):
    env = dict(os.environ, DASH_SUITE_LOCK=str(lock_path))
    env.pop("PYTEST_PLUGINS", None)
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args, "-q", "-p", "no:cacheprovider",
         "-n", workers],
        cwd=_ROOT, env=env, capture_output=True, text=True, timeout=180,
    )


@pytest.mark.release  # nested pytest runs of the whole suite (WP-30 D)
class TestASecondFullRunIsRefused:
    def test_it_exits_at_once_naming_the_holder(self, tmp_path):
        lock = tmp_path / "suite.lock"
        with open(lock, "a+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh.write("pid 424242, started 2026-01-01 00:00:00")
            fh.flush()
            p = _run(["test/"], lock)
        assert p.returncode == pytest.ExitCode.USAGE_ERROR, p.stdout + p.stderr
        assert "already in progress" in p.stderr
        assert "424242" in p.stderr
        # It refused before collecting anything.
        assert "collected" not in p.stdout

    def test_a_targeted_run_is_left_alone(self, tmp_path):
        lock = tmp_path / "suite.lock"
        with open(lock, "a+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh.write("pid 424242, started 2026-01-01 00:00:00")
            fh.flush()
            p = _run([
                "test/test_suite_lock.py::TestWhatCountsAsTheWholeSuite"
                "::test_k_last_failed_and_collect_only_are_not"], lock)
        assert p.returncode == 0, p.stdout + p.stderr
        assert "1 passed" in p.stdout

    def test_the_lock_is_released_when_the_run_ends(self, tmp_path):
        lock = tmp_path / "suite.lock"
        # A full run that collects nothing: the lock is taken, then released
        # at session finish.  -k would skip the lock, so deselect instead.
        p = _run(["test/", "--deselect", "test/"], lock)
        assert p.returncode in (0, pytest.ExitCode.NO_TESTS_COLLECTED), p.stderr
        with open(lock, "a+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)   # would raise if held
            fh.seek(0)
            assert fh.read().startswith("pid "), "the finished run left no holder record"

    def test_the_xdist_controller_takes_it_and_the_workers_do_not(self, tmp_path):
        lock = tmp_path / "suite.lock"
        with open(lock, "a+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh.write("pid 424242, started 2026-01-01 00:00:00")
            fh.flush()
            p = _run(["test/"], lock, workers="2")
        assert p.returncode == pytest.ExitCode.USAGE_ERROR, p.stdout + p.stderr
        assert "424242" in p.stderr
        # And with the lock free, two workers run a full (empty) selection
        # without fighting over it: the controller holds it for them.
        p = _run(["test/", "--deselect", "test/"], lock, workers="2")
        assert p.returncode in (0, pytest.ExitCode.NO_TESTS_COLLECTED), p.stderr
