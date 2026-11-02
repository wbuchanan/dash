"""scripts/gate_timing.py: where a batch-end gate's time went."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "scripts"))
import gate_timing as gt  # noqa: E402

_PYTEST = """\
...................................   [100%]
============================= slowest durations =============================
12.50s call     test/test_a.py::TestX::test_one
3.25s setup    test/test_a.py::TestX::test_one
2.00s call     test/test_b.py::test_two[p1]
1.00s teardown test/test_b.py::test_two[p1]
(4000 durations < 1s hidden.  Use -vv to show these durations.)
38840 passed in 1150.78s (0:19:10)
"""

_SESSION = """\
. display "[ TIME] test_x.cscript ..."
[ TIME] test_tokenizer.cscript timer=    1.234s wall=     2s
[ PASS] test_tokenizer.cscript
[ TIME] test_parser.cscript timer=  101.500s wall=   103s
"""


def test_pytest_durations():
    d = gt.pytest_durations(_PYTEST)
    assert d[0] == (12.5, "call", "test/test_a.py::TestX::test_one")
    assert [p for _, p, _ in d] == ["call", "setup", "call", "teardown"]


def test_by_file():
    assert gt.by_file(gt.pytest_durations(_PYTEST)) == {
        "test/test_a.py": 15.75, "test/test_b.py": 3.0}


def test_by_test():
    t = gt.by_test(gt.pytest_durations(_PYTEST))
    assert t["test/test_a.py::TestX::test_one"] == 15.75
    assert t["test/test_b.py::test_two[p1]"] == 3.0


def test_cert_times():
    assert gt.cert_times(_SESSION) == [(2, "test_tokenizer.cscript"),
                                       (103, "test_parser.cscript")]


def test_cert_logs():
    text = ("verdict: PASS\ncertification log: /t/s1/run_all_cscripts.log\n"
            "certification log: /t/s2/run_all_cscripts.log\n")
    assert gt.cert_logs(text) == ["/t/s1/run_all_cscripts.log",
                                  "/t/s2/run_all_cscripts.log"]


def test_report_and_main(tmp_path, capsys):
    s1 = tmp_path / "c" / "s1"
    s1.mkdir(parents=True)
    (s1 / "run_all_cscripts.log").write_text(_SESSION)
    (tmp_path / "pytest.log").write_text(_PYTEST)
    (tmp_path / "pytest.rc").write_text("rc=0 wall=1162\n")
    (tmp_path / "cert.log").write_text(
        "certification log: %s\n" % (s1 / "run_all_cscripts.log"))
    text = gt.report(str(tmp_path), 5)
    assert "pytest: rc=0 wall=1162" in text and "cert: no .rc file" in text
    assert "4 test phases of 1 s or more, 19 s of worker time" in text
    assert text.index("test/test_a.py") < text.index("test/test_b.py")
    assert "cert session s1: 2 scripts, 105 s summed wall" in text
    assert text.index("test_parser.cscript") < text.index("test_tokenizer")
    assert gt.main(["gate_timing.py", str(tmp_path)]) == 0
    assert (tmp_path / "timing.txt").read_text() == gt.report(str(tmp_path))
    assert "timing.txt" in capsys.readouterr().out


def test_missing_logs_are_named(tmp_path):
    text = gt.report(str(tmp_path))
    assert "pytest.log: missing" in text and "cert.log: missing" in text
    assert gt.main(["gate_timing.py"]) == 2


_SUITE = ('{"wall_seconds": 10.0, "test_seconds": 30.5, "tests": 3, '
          '"files": [{"file": "test/test_b.py", "seconds": 20.25, "tests": 1}, '
          '{"file": "test/test_a.py", "seconds": 10.25, "tests": 2}]}')


def test_suite_files():
    """Every file's worker seconds over all its phases, from the suite's
    DASH_SUITE_TIMING report; None when the text is not that report."""
    assert gt.suite_files(_SUITE) == (30.5, [(20.25, 1, "test/test_b.py"),
                                             (10.25, 2, "test/test_a.py")])
    assert gt.suite_files("not json") is None
    assert gt.suite_files("[]") is None


def test_report_ranks_every_file_from_the_suite_report(tmp_path):
    (tmp_path / "pytest_timing.json").write_text(_SUITE)
    text = gt.report(str(tmp_path), 5)
    assert "every test file, all phases: 30 s of worker time" in text
    assert text.index("test/test_b.py") < text.index("test/test_a.py")
    assert "pytest_timing.json: missing" in gt.report(str(tmp_path / "x"))
