"""Judge a certification-suite run from its log: pass only when every script
the runner registers passed and none skipped.

Stata's batch mode does not hand the runner's `exit 1' back as the process's
exit status, so `make cert' reads the log instead.  The runner,
test/run_all_cscripts.do, prints one line per script -- `[ PASS] name',
`[ FAIL] name  (rc=N)' or `[ SKIP] name  (dependency unavailable)' -- and a
summary line.  A skip is not a pass (the certification-suite rule): a
script skips when Stata has lost its Python or bokeh, and a run of skips
has verified nothing.

Usage:  python3 scripts/cert_verdict.py <run_all_cscripts.log> <run_all_cscripts.do>
Exit:   0 when every registered script passed; 1 otherwise, naming each
        script that failed, skipped or never reported.
"""
import re
import sys

# A script is registered by a `do' of its file, from test/ or -- one of them,
# which must run from the package root -- as test/<name>.
_REGISTERED = re.compile(r'^\s*do "(?:[^"]*/)?([^"/]+\.cscript)"\s*$', re.M)
_RESULT = re.compile(r"^\[ (PASS|FAIL|SKIP)\] (\S+\.cscript)\b", re.M)
_SUMMARY = re.compile(r"^ALL TESTS PASSED \((\d+) passed, (\d+) skipped\)\s*$",
                      re.M)


def registered_scripts(runner_text):
    """The certification scripts the runner runs, in its order."""
    return _REGISTERED.findall(runner_text)


def verdict(log_text, runner_text):
    """(ok, lines): whether the run passed, and a report to print.

    ok is True only when every registered script reported PASS, none
    reported FAIL or SKIP, no script reported twice, and the runner's own
    summary says all passed with none skipped.
    """
    scripts = registered_scripts(runner_text)
    results = {}
    twice = []
    for status, name in _RESULT.findall(log_text):
        if name in results:
            twice.append(name)
        results[name] = status
    failed = [s for s in scripts if results.get(s) == "FAIL"]
    skipped = [s for s in scripts if results.get(s) == "SKIP"]
    missing = [s for s in scripts if s not in results]
    stray = sorted(set(results) - set(scripts))
    passed = [s for s in scripts if results.get(s) == "PASS"]
    m = _SUMMARY.search(log_text)
    summary_ok = bool(m) and int(m.group(1)) == len(scripts) \
        and int(m.group(2)) == 0
    ok = bool(scripts) and not (failed or skipped or missing or stray
                                or twice) and summary_ok
    lines = ["certification suite: %d of %d registered scripts passed"
             % (len(passed), len(scripts))]
    for label, names in (("failed", failed), ("skipped", skipped),
                         ("never reported", missing),
                         ("reported but not registered", stray),
                         ("reported twice", twice)):
        if names:
            lines.append("  %s: %s" % (label, " ".join(names)))
    if not scripts:
        lines.append("  the runner registers no script")
    if not summary_ok:
        lines.append("  the runner's summary does not say all %d passed "
                     "with none skipped" % len(scripts))
    lines.append("verdict: " + ("PASS" if ok else "FAIL"))
    return ok, lines


def main(argv):
    if len(argv) != 3:
        sys.stderr.write(__doc__)
        return 2
    try:
        with open(argv[1], encoding="utf-8", errors="replace") as fh:
            log_text = fh.read()
    except OSError as exc:
        print("certification suite: no log to judge (%s)" % exc)
        print("verdict: FAIL")
        return 1
    with open(argv[2], encoding="utf-8") as fh:
        runner_text = fh.read()
    ok, lines = verdict(log_text, runner_text)
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
