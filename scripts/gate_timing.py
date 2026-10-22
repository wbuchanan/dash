"""Say where a batch-end gate's time went, from the logs it left.

scripts/run_all_tests.sh runs pytest with ``--durations=0
--durations-min=1`` (every test phase of a second or more) and the
certification runner prints one ``[ TIME] <script> timer=...s wall=...s``
line per script.  This reads both and writes ``timing.txt`` beside them:
pytest's total, the test files and tests that took the most worker time,
and each certification session's scripts by wall time.  The maintainer
asked for it on 22oct2026: the whole suite took about 33 minutes against
the five-minute target.

Worker time is summed over parallel workers, so the file totals add up to
more than the wall time; they rank where the work is, not the wait.

Usage:  python3 scripts/gate_timing.py <gate log folder> [<top n>]
Exit:   0, also when a log is missing (the report says so).
"""
import os
import re
import sys
from collections import defaultdict

# "12.34s call     test/test_x.py::TestY::test_z[p]"
_DURATION = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)s\s+(setup|call|teardown)\s+(\S+)")
# "[ TIME] test_x.cscript timer=   12.345s wall=    13s"
_CERT_TIME = re.compile(r"^\[ TIME\] (\S+) timer=\s*[0-9.]+s wall=\s*([0-9]+)s")
# "certification log: /.../s1/run_all_cscripts.log"
_CERT_LOG = re.compile(r"^certification log: (\S+)")


def pytest_durations(text):
    """[(seconds, phase, node)] for every duration line pytest printed."""
    out = []
    for line in text.splitlines():
        m = _DURATION.match(line)
        if m:
            out.append((float(m.group(1)), m.group(2), m.group(3)))
    return out


def by_file(durations):
    """{test file: summed seconds} over every phase of its tests."""
    tot = defaultdict(float)
    for sec, _, node in durations:
        tot[node.split("::", 1)[0]] += sec
    return dict(tot)


def by_test(durations):
    """{node: summed seconds} over setup, call and teardown."""
    tot = defaultdict(float)
    for sec, _, node in durations:
        tot[node] += sec
    return dict(tot)


def cert_times(text):
    """[(wall seconds, script)] for every [ TIME] line of one session log."""
    out = []
    for line in text.splitlines():
        m = _CERT_TIME.match(line)
        if m:
            out.append((int(m.group(2)), m.group(1)))
    return out


def cert_logs(cert_log_text):
    """The session logs cert.log names, in its order."""
    return [m.group(1) for m in map(_CERT_LOG.match, cert_log_text.splitlines()) if m]


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def _top(d, n):
    return sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def report(folder, n=25):
    """The timing report's text for the gate logs in *folder*."""
    lines = ["Gate timing for %s" % os.path.basename(folder.rstrip("/"))]
    for half in ("pytest", "cert"):
        rc = _read(os.path.join(folder, half + ".rc"))
        lines.append("%s: %s" % (half, rc.strip() if rc else "no .rc file"))
    text = _read(os.path.join(folder, "pytest.log"))
    if text is None:
        lines.append("pytest.log: missing")
    else:
        durs = pytest_durations(text)
        lines.append("")
        lines.append("pytest: %d test phases of 1 s or more, %.0f s of worker time"
                     % (len(durs), sum(d[0] for d in durs)))
        lines.append("Slowest test files (worker seconds, phases of 1 s or more):")
        lines += ["  %8.1f  %s" % (s, f) for f, s in _top(by_file(durs), n)]
        lines.append("Slowest tests:")
        lines += ["  %8.1f  %s" % (s, t) for t, s in _top(by_test(durs), n)]
    ctext = _read(os.path.join(folder, "cert.log"))
    if ctext is None:
        lines.append("cert.log: missing")
    else:
        for path in cert_logs(ctext):
            stext = _read(path)
            lines.append("")
            if stext is None:
                lines.append("%s: missing" % path)
                continue
            times = cert_times(stext)
            lines.append("cert session %s: %d scripts, %d s summed wall"
                         % (os.path.basename(os.path.dirname(path)), len(times),
                            sum(t for t, _ in times)))
            lines += ["  %6d  %s" % (t, s) for t, s in sorted(times, reverse=True)[:n]]
    return "\n".join(lines) + "\n"


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[-2])
        return 2
    n = int(argv[2]) if len(argv) > 2 else 25
    text = report(argv[1], n)
    with open(os.path.join(argv[1], "timing.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print("timing: %s" % os.path.join(argv[1], "timing.txt"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
