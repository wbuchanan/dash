"""Where the suite's time goes: a per-test, per-file and per-worker report.

Set ``DASH_SUITE_TIMING`` to a file path and run the suite as usual::

    DASH_SUITE_TIMING=/tmp/timing.json python3 -m pytest test/ -q

The controller (or the only process, under ``-n0``) collects every test's
setup, call and teardown durations from the reports xdist forwards, then
writes them to that path as JSON and prints a short summary: the wall time,
the busiest workers, and the slowest files and tests.  The worker lines show
imbalance: when one worker is busy long after the others finish, the
wall time is that worker's time, not the suite's.

Nothing is recorded unless the variable is set.
"""

import json
import os
import time
from collections import defaultdict

ENV = "DASH_SUITE_TIMING"
TOP = 25


def _file_of(nodeid):
    """The test file a node id belongs to: the part before the first ``::``."""
    return nodeid.split("::", 1)[0]


def _worker_of(report):
    """The xdist worker id that ran ``report`` ("main" without xdist)."""
    node = getattr(report, "node", None)
    gateway = getattr(node, "gateway", None)
    return getattr(gateway, "id", None) or "main"


def summarise(records, wall):
    """Aggregate ``records`` into the report's dict.

    ``records`` is a list of ``(nodeid, when, worker, seconds)``; ``wall`` is
    the session's elapsed seconds.  Returns per-test totals (setup + call +
    teardown), per-file totals with test counts, and per-worker busy time,
    each sorted slowest first.
    """
    tests = defaultdict(float)
    files = defaultdict(float)
    counts = defaultdict(set)
    workers = defaultdict(float)
    phases = defaultdict(float)
    for nodeid, when, worker, seconds in records:
        tests[nodeid] += seconds
        files[_file_of(nodeid)] += seconds
        counts[_file_of(nodeid)].add(nodeid)
        workers[worker] += seconds
        phases[when] += seconds
    by = lambda d: sorted(d.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "wall_seconds": round(wall, 3),
        "test_seconds": round(sum(tests.values()), 3),
        "tests": len(tests),
        "phases": {k: round(v, 3) for k, v in by(phases)},
        "workers": [{"worker": w, "seconds": round(s, 3)}
                    for w, s in by(workers)],
        "files": [{"file": f, "seconds": round(s, 3), "tests": len(counts[f])}
                  for f, s in by(files)],
        "slowest_tests": [{"test": t, "seconds": round(s, 3)}
                          for t, s in by(tests)[:200]],
    }


def format_summary(summary, top=TOP):
    """The terminal lines for ``summary`` (the dict ``summarise`` returns)."""
    lines = [
        "suite timing: wall %.1fs, %d tests, %.1fs of test time"
        % (summary["wall_seconds"], summary["tests"],
           summary["test_seconds"]),
        "phases: " + ", ".join("%s %.1fs" % kv
                               for kv in summary["phases"].items()),
        "workers (busy seconds): " + ", ".join(
            "%s %.1f" % (w["worker"], w["seconds"])
            for w in summary["workers"]),
        "slowest files:",
    ]
    lines += ["  %8.1fs %5d  %s" % (f["seconds"], f["tests"], f["file"])
              for f in summary["files"][:top]]
    lines.append("slowest tests:")
    lines += ["  %8.2fs  %s" % (t["seconds"], t["test"])
              for t in summary["slowest_tests"][:top]]
    return lines


class SuiteTiming:
    """The plugin: registered by conftest only when ``ENV`` is set."""

    def __init__(self, path):
        self.path = path
        self.records = []
        self.start = time.monotonic()

    def pytest_runtest_logreport(self, report):
        if getattr(report, "duration", None) is None:
            return
        self.records.append(
            (report.nodeid, report.when, _worker_of(report),
             float(report.duration)))

    def pytest_sessionfinish(self, session):
        if hasattr(session.config, "workerinput"):
            return  # an xdist worker: the controller writes the report
        summary = summarise(self.records, time.monotonic() - self.start)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=1)
        self.summary = summary

    def pytest_terminal_summary(self, terminalreporter):
        summary = getattr(self, "summary", None)
        if summary is None:
            return
        terminalreporter.section("suite timing")
        for line in format_summary(summary):
            terminalreporter.write_line(line)
        terminalreporter.write_line("full report: %s" % self.path)


def register(config):
    """Register the plugin on ``config`` when ``DASH_SUITE_TIMING`` is set."""
    path = os.environ.get(ENV, "").strip()
    if not path or hasattr(config, "workerinput"):
        return None
    plugin = SuiteTiming(path)
    config.pluginmanager.register(plugin, "dash-suite-timing")
    return plugin
