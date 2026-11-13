"""Profile the test suite from the logs a run left (WP-50 50-01).

Reads test/suite_timing.py's JSON reports (DASH_SUITE_TIMING; the first
one given is ``make test``, the five-minute target) and the certification
runner's session logs (run_all_cscripts.log: one ``[ TIME] <script>
timer=<t>s wall=<w>s`` line per script and, inside a truth script, its
``S<MM> start``/``S<MM> end`` lines; a script whose timer reads ``.``
counts its wall seconds), and prints one table: pytest's wall,
test-seconds, phases, worker imbalance, collection, the longest xdist group
(the wall floor under ``--dist loadgroup``), the slowest files and tests;
each cert session's scripts, the truth-script blocks over 20 s, each
truth script's fixed cost (its seconds minus its blocks'); the target line
and, given ``--estimate`` values (the seconds each lever is expected to
save), the projection of ``make test`` on 8 workers at 0.85 efficiency.

Usage:  python3 scripts/suite_profile.py report <timing.json> [<timing.json>]
            [--cert <run_all_cscripts.log>...] [--estimate <seconds>]...
Exit:   0; 2 on a usage error or a file that cannot be read.
"""
import json
import os
import re
import sys

TOP = 30
TARGET = 300
WORKERS = 8
EFFICIENCY = 0.85
SLOW_BLOCK = 20
USAGE = ("usage: suite_profile.py report <timing.json> [<timing.json>] "
         "[--cert <run_all_cscripts.log>...] [--estimate <seconds>]...")

_RUN = re.compile(r"^\[ RUN \] (\S+)")
_TIME = re.compile(r"^\[ TIME\] (\S+) timer=\s*([0-9.]+)s wall=\s*([0-9]+)s")
_BLOCK = re.compile(r"^(S\d\d) (start|end) ((?:\d{1,2} \w{3} \d{4} )?\d\d:\d\d:\d\d)\s*$")
_CLOCK = re.compile(r"(\d\d):(\d\d):(\d\d)$")


def _clock(stamp):
    """Seconds since midnight of a ``[DD Mon YYYY ]HH:MM:SS`` stamp."""
    h, m, s = map(int, _CLOCK.search(stamp).groups())
    return h * 3600 + m * 60 + s


def block_seconds(start, end):
    """Whole seconds from *start* to *end*; a block that crosses midnight
    (the time-only form) wraps."""
    return (_clock(end) - _clock(start)) % 86400


def cert_scripts(text):
    """[{script, seconds, blocks}] for each script one session log ran:
    its ``[ TIME]`` timer seconds and {block id: seconds} of the block
    lines between its ``[ RUN ]`` and ``[ TIME]`` lines."""
    out, cur, starts = [], None, {}
    for line in text.splitlines():
        m = _RUN.match(line)
        if m:
            cur, starts = {"script": m.group(1), "blocks": {}}, {}
            continue
        if cur is None:
            continue
        m = _BLOCK.match(line)
        if m:
            sid, edge, stamp = m.groups()
            if edge == "start":
                starts[sid] = stamp
            elif sid in starts:
                cur["blocks"][sid] = (cur["blocks"].get(sid, 0)
                                      + block_seconds(starts.pop(sid), stamp))
            continue
        m = _TIME.match(line)
        if m and m.group(1) == cur["script"]:
            # a script that clears the timers logs "timer=   .s": use wall
            try:
                cur["seconds"] = float(m.group(2))
            except ValueError:
                cur["seconds"] = float(m.group(3))
            out.append(cur)
            cur = None
    return out


def longest_group(timing):
    """(group, seconds, tests) of the xdist group with the most summed time,
    or None when the report records no groups."""
    groups = timing.get("groups") or []
    if not groups:
        return None
    g = max(groups, key=lambda r: r["seconds"])
    return g["group"], g["seconds"], g["tests"]


def collection_seconds(timing):
    """Seconds from the session's start to its first test, or None."""
    a, b = timing.get("session_start"), timing.get("first_test_start")
    if a is None or b is None:
        return None
    return round(b - a, 3)


def projection(test_seconds, estimates):
    """``make test``'s projected wall once the levers save *estimates*."""
    return (test_seconds - sum(estimates)) / (WORKERS * EFFICIENCY)


def _pytest_lines(label, t):
    w = t.get("workers") or []
    lines = ["pytest %s: wall %.1f s, %d tests, %.1f test-seconds"
             % (label, t["wall_seconds"], t["tests"], t["test_seconds"])]
    ph = t.get("phases", {})
    lines.append("  phases: " + ", ".join(
        "%s %.1f s" % (k, ph[k]) for k in ("setup", "call", "teardown") if k in ph))
    if w:
        hi, lo = w[0], w[-1]
        lines.append("  workers: %d, busiest %s %.1f s, least busy %s %.1f s, "
                     "imbalance %.1f s" % (len(w), hi["worker"], hi["seconds"],
                                           lo["worker"], lo["seconds"],
                                           hi["seconds"] - lo["seconds"]))
    c = collection_seconds(t)
    lines.append("  collection: " + ("not recorded" if c is None else "%.1f s" % c))
    g = longest_group(t)
    lines.append("  longest xdist group: " + (
        "not recorded" if g is None else "%s %.1f s (%d tests)" % g))
    lines.append("  slowest files (test-seconds, tests):")
    lines += ["    %8.1f s %6d  %s" % (f["seconds"], f["tests"], f["file"])
              for f in t.get("files", [])[:TOP]]
    lines.append("  slowest tests:")
    lines += ["    %8.2f s  %s" % (r["seconds"], r["test"])
              for r in t.get("slowest_tests", [])[:TOP]]
    return lines


def _cert_lines(logs):
    lines, slow, fixed = [], [], []
    for path, text in logs:
        session = os.path.basename(os.path.dirname(os.path.abspath(path)))
        scripts = cert_scripts(text)
        lines.append("cert session %s: %d scripts, %.1f s summed"
                     % (session, len(scripts), sum(s["seconds"] for s in scripts)))
        lines += ["    %8.1f s  %s" % (s["seconds"], s["script"])
                  for s in sorted(scripts, key=lambda s: -s["seconds"])]
        for s in scripts:
            for sid, sec in sorted(s["blocks"].items()):
                if sec > SLOW_BLOCK:
                    slow.append((sec, "    %s %s %d s" % (s["script"], sid, sec)))
            if s["blocks"]:
                b = sum(s["blocks"].values())
                fixed.append((s["seconds"] - b,
                              "    %s %s: %.1f s, blocks %d s, fixed %.1f s"
                              % (session, s["script"], s["seconds"], b,
                                 s["seconds"] - b)))
    if logs:
        lines.append("truth-script blocks over %d s:" % SLOW_BLOCK)
        lines += [t for _, t in sorted(slow, key=lambda r: -r[0])]
        lines.append("fixed cost (script seconds minus its blocks):")
        lines += [t for _, t in sorted(fixed, key=lambda r: -r[0])]
    return lines


def report(timing_paths, cert_paths, estimates):
    """The profile's text for the named files (each must be readable)."""
    timings = [(p, json.loads(_read(p))) for p in timing_paths]
    lines = []
    for p, t in timings:
        lines += _pytest_lines(os.path.basename(p), t)
    lines += _cert_lines([(p, _read(p)) for p in cert_paths])
    first = timings[0][1]
    lines.append("make test: %.0f s against %d s" % (first["wall_seconds"], TARGET))
    if estimates:
        lines.append("projection: (%.0f - %.0f) / (%d x %.2f) = %.0f s against %d s"
                     % (first["test_seconds"], sum(estimates), WORKERS,
                        EFFICIENCY, projection(first["test_seconds"], estimates),
                        TARGET))
    return "\n".join(lines) + "\n"


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def main(argv):
    if not argv or argv[0] != "report" or len(argv) < 2:
        print(USAGE)
        return 2
    timing, cert, est, dest = [], [], [], None
    for a in argv[1:]:
        if a in ("--cert", "--estimate"):
            dest = a
        elif dest == "--cert":
            cert.append(a)
        elif dest == "--estimate":
            try:
                est.append(float(a))
            except ValueError:
                print("suite_profile: --estimate takes seconds, not %r" % a)
                return 2
        else:
            timing.append(a)
    if not timing:
        print(USAGE)
        return 2
    for p in timing + cert:
        if not os.path.isfile(p):
            print("suite_profile: cannot read %s" % p)
            return 2
    try:
        text = report(timing, cert, est)
    except (ValueError, KeyError) as e:
        print("suite_profile: not a timing report (%s)" % e)
        return 2
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
