"""The certification suite's shard table (WP-30 test performance, C).

test/run_all_cscripts.do runs every certification script in one Stata
session, or -- with DASH_CERT_SHARD=k/N -- only the scripts of shard k of N,
so that scripts/run_cert_suite.sh can run N sessions side by side.  Which
script is in which shard is the table between the runner's
``// ---- shards: begin`` and ``// ---- shards: end`` lines: one row a
script, with the seconds it took in a timed run, whether it runs
``dash serve`` on a fixed port, and its shard for N = 2, 3 and 4.

The shards are balanced by longest processing time first: the scripts, from
the longest, each go to the least loaded shard (the lowest numbered of
equals).  Every script that runs ``dash serve`` on one of the fixed ports
5006, 5097, 5098 and 5099 -- the default port is 5006 -- is one unit, so
they always share a shard and never serve at once: a logical line (``///``
continuations joined, comments dropped) whose command, after any capture,
noisily or quietly, is ``dash serve`` or ``_dash_serve`` and which names one
of those ports or no port().

Usage:
  python3 scripts/cert_shards.py write <timed run log> [<source>]
          rewrite the table from a run's ``[ TIME] <script> timer=<s>
          wall=<s>`` lines; <source> says in the table where the seconds
          come from (default: the log's file name)
  python3 scripts/cert_shards.py check                   exit 1 unless the
          table holds every registered script, marks exactly the fixed-port
          scripts, and gives each N the balanced assignment of its seconds
  python3 scripts/cert_shards.py show                    each N's loads
"""
import os
import re
import sys
import textwrap

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
RUNNER = os.path.join(_REPO, "test", "run_all_cscripts.do")

sys.path.insert(0, _HERE)
import cert_verdict  # noqa: E402

#: The shard counts the table assigns (run_cert_suite.sh runs at most 4).
COUNTS = (2, 3, 4)
FIXED_PORTS = ("5006", "5097", "5098", "5099")
BEGIN = "// ---- shards: begin (scripts/cert_shards.py writes this block) ----"
END = "// ---- shards: end ----"

_PREFIX = re.compile(r"^(?:(?:capture|cap|noisily|noi|quietly|qui)\s+)+")
_SERVE = re.compile(r"^(?:dash\s+serve|_dash_serve)(?=$|[\s,])")
_FIXED = re.compile(r"\bport\(\s*0*(%s)\s*\)" % "|".join(FIXED_PORTS))
_TIME = re.compile(r"^\[ TIME\] (\S+\.cscript) timer=\s*([0-9.]+|\.)s "
                   r"wall=\s*([0-9.]+)s", re.M)


def logical_lines(text):
    """The do-file's logical lines: `///' continuations joined, `//' and
    `*' comment lines dropped (a `//' inside a string is rare enough in
    these scripts to be taken as a comment: the rule only ever widens)."""
    out, cur = [], []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not cur and line.lstrip().startswith("*"):
            continue
        cont = line.endswith("///")
        if cont:
            line = line[:-3]
        cur.append(line.split("//", 1)[0].strip())
        if not cont:
            joined = " ".join(p for p in cur if p)
            if joined:
                out.append(joined)
            cur = []
    joined = " ".join(p for p in cur if p)
    if joined:
        out.append(joined)
    return out


def serves_on_a_fixed_port(text):
    """Whether a script runs dash serve on a fixed port (see the module's
    docstring)."""
    for line in logical_lines(text):
        cmd = _PREFIX.sub("", line)
        if not _SERVE.match(cmd):
            continue
        if _FIXED.search(cmd) or "port(" not in cmd.replace(" ", ""):
            return True
    return False


def assign(seconds, port, n):
    """{script: shard (1..n)}: longest first onto the least loaded shard,
    the fixed-port scripts one unit."""
    units = []
    together = sorted(s for s in seconds if s in port)
    if together:
        units.append((sum(seconds[s] for s in together), together))
    units += [(seconds[s], [s]) for s in seconds if s not in port]
    units.sort(key=lambda u: (-u[0], u[1][0]))
    load = [0.0] * n
    out = {}
    for sec, scripts in units:
        k = min(range(n), key=lambda i: (load[i], i))
        load[k] += sec
        for s in scripts:
            out[s] = k + 1
    return out


def loads(seconds, shards, n):
    """The seconds of each shard of n."""
    out = [0.0] * n
    for s, k in shards.items():
        out[k - 1] += seconds[s]
    return out


def read_table(runner_text):
    """[(script, seconds, port, {N: shard})] from the runner's block."""
    if runner_text.count(BEGIN) != 1 or runner_text.count(END) != 1:
        raise ValueError("the runner has no single shard table")
    block = runner_text[runner_text.index(BEGIN):runner_text.index(END)]
    rows = []
    for m in re.finditer(r"^\s+(test_\w+\.cscript)\s+([0-9.]+)\s+([01])"
                         r"\s+([1-4])\s+([1-4])\s+([1-4])\s*(?:///)?\s*$",
                         block, re.M):
        rows.append((m.group(1), float(m.group(2)), m.group(3) == "1",
                     dict(zip(COUNTS, (int(m.group(4)), int(m.group(5)),
                                       int(m.group(6)))))))
    return rows


def render_table(seconds, port, source):
    """The block's text for these seconds and fixed-port scripts."""
    shards = {n: assign(seconds, port, n) for n in COUNTS}
    lines = [
        BEGIN,
        "// Each certification script: the seconds it takes, 1 when it runs",
        "// dash serve on a fixed port (5006, 5097, 5098, 5099), and its shard",
        "// when DASH_CERT_SHARD splits the run in 2, 3 or 4: longest first",
        "// onto the least loaded shard, the fixed-port scripts as one unit so",
        "// that they never serve at once.  Unset, the run is every script, in",
        "// this session.",
    ]
    lines += ["// " + ln for ln in textwrap.wrap(
        "Seconds: " + " ".join(source.split()), 72)]
    lines.append("local _cert_shards ///")
    width = max(len(s) for s in seconds)
    names = sorted(seconds)
    for i, s in enumerate(names):
        lines.append("    %-*s %7.1f %d  %d %d %d%s"
                     % (width, s, seconds[s], 1 if s in port else 0,
                        shards[2][s], shards[3][s], shards[4][s],
                        " ///" if i < len(names) - 1 else ""))
    return "\n".join(lines) + "\n"


def seconds_from_log(log_text):
    """{script: seconds} from a timed run's `[ TIME]' lines: the timer, or
    the wall clock where a script's own clear all reset the timer."""
    out = {}
    for name, timer, wall in _TIME.findall(log_text):
        out[name] = float(wall) if timer == "." else float(timer)
    return out


def _cscript_text(name):
    with open(os.path.join(_REPO, "test", name), encoding="utf-8",
              errors="replace") as fh:
        return fh.read()


def check(runner_text):
    """The problems with the runner's table, one line each."""
    probs = []
    try:
        rows = read_table(runner_text)
    except ValueError as exc:
        return [str(exc)]
    scripts = cert_verdict.registered_scripts(runner_text)
    named = [r[0] for r in rows]
    if sorted(named) != sorted(set(named)):
        probs.append("a script has two rows")
    missing = sorted(set(scripts) - set(named))
    extra = sorted(set(named) - set(scripts))
    if missing:
        probs.append("no row for: " + " ".join(missing))
    if extra:
        probs.append("a row for a script the runner does not run: "
                     + " ".join(extra))
    seconds = {r[0]: r[1] for r in rows}
    marked = {r[0] for r in rows if r[2]}
    port = {s for s in named if os.path.exists(os.path.join(
        _REPO, "test", s)) and serves_on_a_fixed_port(_cscript_text(s))}
    if marked != port:
        probs.append("fixed-port marks %s, the scripts that serve on a fixed "
                     "port %s" % (sorted(marked), sorted(port)))
    for n in COUNTS:
        want = assign(seconds, marked, n)
        got = {r[0]: r[3][n] for r in rows}
        if got != want:
            probs.append("the shards for N=%d are not the balanced "
                         "assignment of the seconds" % n)
    return probs


def main(argv):
    with open(RUNNER, encoding="utf-8") as fh:
        runner = fh.read()
    if argv[1:2] == ["check"] and len(argv) == 2:
        probs = check(runner)
        for p in probs:
            print("cert_shards: " + p)
        return 1 if probs else 0
    if argv[1:2] == ["show"] and len(argv) == 2:
        rows = read_table(runner)
        seconds = {r[0]: r[1] for r in rows}
        for n in COUNTS:
            shards = {r[0]: r[3][n] for r in rows}
            print("N=%d: %s" % (n, "  ".join(
                "%d: %.0f s" % (k + 1, v)
                for k, v in enumerate(loads(seconds, shards, n)))))
        return 0
    if argv[1:2] == ["write"] and len(argv) in (3, 4):
        with open(argv[2], encoding="utf-8", errors="replace") as fh:
            seconds = seconds_from_log(fh.read())
        scripts = cert_verdict.registered_scripts(runner)
        lacking = sorted(set(scripts) - set(seconds))
        if lacking:
            print("cert_shards: the log times no run of: " + " ".join(lacking))
            return 1
        seconds = {s: seconds[s] for s in scripts}
        port = {s for s in scripts
                if serves_on_a_fixed_port(_cscript_text(s))}
        source = argv[3] if len(argv) == 4 else os.path.basename(argv[2])
        new = render_table(seconds, port, source)
        start = runner.index(BEGIN)
        stop = runner.index(END)
        with open(RUNNER, "w", encoding="utf-8") as fh:
            fh.write(runner[:start] + new + runner[stop:])
        print("cert_shards: wrote the table for %d scripts" % len(seconds))
        return 0
    sys.stderr.write(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
