"""The suite profile report (scripts/suite_profile.py, WP-50 50-01)."""

import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "scripts", "suite_profile.py")
sys.path.insert(0, os.path.dirname(SCRIPT))
import suite_profile as sp  # noqa: E402


def _timing(**over):
    """A synthetic test/suite_timing.py report."""
    d = {
        "wall_seconds": 400.0,
        "test_seconds": 2720.0,
        "tests": 5,
        "phases": {"call": 2500.0, "teardown": 150.0, "setup": 70.0},
        "workers": [{"worker": "gw1", "seconds": 350.0},
                    {"worker": "gw0", "seconds": 340.5}],
        "files": [{"file": "test/test_b.py", "seconds": 2000.0, "tests": 3},
                  {"file": "test/test_a.py", "seconds": 720.0, "tests": 2}],
        "slowest_tests": [{"test": "test/test_b.py::t1@grp", "seconds": 90.0},
                          {"test": "test/test_a.py::t2", "seconds": 12.5}],
        "groups": [{"group": "grp", "seconds": 300.0, "tests": 2},
                   {"group": "small", "seconds": 4.0, "tests": 1}],
        "session_start": 1000.0,
        "first_test_start": 1031.5,
    }
    d.update(over)
    return d


#: one session log: a plain script and a truth script with three blocks,
#: in both block-line forms (date and time, time only).
CERT_LOG = """\
[ RUN ] test_plain.cscript
. display "S01 start 10:00:00"
[ TIME] test_plain.cscript timer=    7.250s wall=     7s
[ PASS] test_plain.cscript
[ RUN ] test_wp44_truth.cscript
S00 start 12 Nov 2026 10:00:10
S00 end 12 Nov 2026 10:00:11
S03 start 12 Nov 2026 10:00:11
S03 end 12 Nov 2026 10:00:41
S07 start 23:59:50
S07 end 00:00:15
[ TIME] test_wp44_truth.cscript timer=   80.000s wall=    80s
[ PASS] test_wp44_truth.cscript
"""


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text if isinstance(text, str) else json.dumps(text))
    return str(p)


class TestParsers:
    def test_block_seconds_reads_both_forms_and_wraps_midnight(self):
        assert sp.block_seconds("12 Nov 2026 10:00:11",
                                "12 Nov 2026 10:00:41") == 30
        assert sp.block_seconds("23:59:50", "00:00:15") == 25

    def test_cert_scripts_reads_timer_and_blocks(self):
        scripts = sp.cert_scripts(CERT_LOG)
        assert [s["script"] for s in scripts] == [
            "test_plain.cscript", "test_wp44_truth.cscript"]
        assert scripts[0]["seconds"] == 7.25 and scripts[0]["blocks"] == {}
        assert scripts[1]["seconds"] == 80.0
        assert scripts[1]["blocks"] == {"S00": 1, "S03": 30, "S07": 25}

    def test_a_missing_timer_falls_back_to_wall(self):
        # test_examples_run.cscript logs "timer=        .s" (WP-49 gate)
        log = ("[ RUN ] test_examples_run.cscript\n"
               "[ TIME] test_examples_run.cscript timer=        .s wall=    27s\n")
        assert sp.cert_scripts(log)[0]["seconds"] == 27.0

    def test_longest_group_is_the_largest_summed_group(self):
        assert sp.longest_group(_timing()) == ("grp", 300.0, 2)
        assert sp.longest_group(_timing(groups=[])) is None
        t = _timing()
        del t["groups"]
        assert sp.longest_group(t) is None

    def test_collection_seconds(self):
        assert sp.collection_seconds(_timing()) == 31.5
        t = _timing()
        del t["session_start"]
        assert sp.collection_seconds(t) is None

    def test_projection_arithmetic(self):
        assert sp.projection(2720.0, [300.0, 100.0]) == pytest.approx(
            (2720.0 - 400.0) / (8 * 0.85))


class TestReport:
    def _report(self, tmp_path, *extra, timing=None):
        t = _write(tmp_path, "t.json", timing or _timing())
        s1 = tmp_path / "s1"
        s1.mkdir(exist_ok=True)
        log = _write(s1, "run_all_cscripts.log", CERT_LOG)
        return sp.report([t], [log], [float(e) for e in extra])

    def test_pytest_totals(self, tmp_path):
        text = self._report(tmp_path)
        assert "wall 400.0 s, 5 tests, 2720.0 test-seconds" in text
        assert "setup 70.0 s, call 2500.0 s, teardown 150.0 s" in text
        assert "busiest gw1 350.0 s, least busy gw0 340.5 s, imbalance 9.5 s" in text
        assert "collection: 31.5 s" in text
        assert "2000.0 s      3  test/test_b.py" in text
        assert "90.00 s  test/test_b.py::t1@grp" in text

    def test_longest_group(self, tmp_path):
        assert "longest xdist group: grp 300.0 s (2 tests)" in self._report(tmp_path)
        t = _timing()
        del t["groups"], t["session_start"]
        text = self._report(tmp_path, timing=t)
        assert "longest xdist group: not recorded" in text
        assert "collection: not recorded" in text

    def test_cert_tables(self, tmp_path):
        text = self._report(tmp_path)
        assert "cert session s1: 2 scripts, 87.2 s summed" in text
        assert "80.0 s  test_wp44_truth.cscript" in text
        assert "test_wp44_truth.cscript S03 30 s" in text
        assert "test_wp44_truth.cscript S07 25 s" in text
        assert "S00 1 s" not in text  # blocks of 20 s or less are left out
        assert ("s1 test_wp44_truth.cscript: 80.0 s, blocks 56 s, fixed 24.0 s"
                in text)
        assert "test_plain.cscript: 7.2" not in text.split("fixed cost")[1]

    def test_target_line(self, tmp_path):
        assert "make test: 400 s against 300 s" in self._report(tmp_path)

    def test_projection_line(self, tmp_path):
        text = self._report(tmp_path, "300", "100")
        assert ("projection: (2720 - 400) / (8 x 0.85) = 341 s against 300 s"
                in text)
        # no --estimate, no projection line
        assert "projection:" not in sp.report(
            [_write(tmp_path, "u.json", _timing())], [], [])


class TestMain:
    def test_no_files_is_usage_and_2(self):
        r = subprocess.run([sys.executable, SCRIPT, "report"],
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 2 and r.stdout.startswith("usage:")

    def test_a_missing_file_is_2(self, tmp_path, capsys):
        assert sp.main(["report", str(tmp_path / "none.json")]) == 2
        assert "none.json" in capsys.readouterr().out

    def test_report_prints_and_returns_0(self, tmp_path, capsys):
        t = _write(tmp_path, "t.json", _timing())
        log = _write(tmp_path, "c.log", CERT_LOG)
        assert sp.main(["report", t, "--cert", log, "--estimate", "20"]) == 0
        out = capsys.readouterr().out
        assert "make test: 400 s against 300 s" in out
        assert "projection: (2720 - 20) / (8 x 0.85) = 397 s" in out
