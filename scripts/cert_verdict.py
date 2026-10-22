"""Judge a certification-suite run from its log, or from the logs of its
shards: pass only when every script the runner registers passed, exactly
once, and none skipped.

Stata's batch mode does not hand the runner's `exit 1' back as the process's
exit status, so `make cert' reads the log instead.  The runner,
test/run_all_cscripts.do, prints one line per script -- `[ PASS] name',
`[ FAIL] name  (rc=N)' or `[ SKIP] name  (dependency unavailable)' -- and a
summary line.  A skip is not a pass (the certification-suite rule): a
script skips when Stata has lost its Python or bokeh, and a run of skips
has verified nothing.

A run split into N sessions (WP-30 test performance, C; DASH_CERT_SHARD=k/N
in each, scripts/run_cert_suite.sh) leaves N logs, each saying which shard
it is (`[SHARD] k/N: ...').  They are judged together: shards 1 to N each
exactly once, every registered script reported in exactly one of them and
passed, and each log's own summary agreeing with its results.  A script
whose shard table row says "*" (it splits itself across the sessions, as
test_wp30_truth.cscript does) is reported, and passed, in every one of them.

The scripts the runner's ``local _cert_release`` line names (in its shard
table) are the release tier (22oct2026): the closed work packages' truth
scripts, which run in the release gate and at a work package's closeout but
not in a default run.  A run is of one tier (DASH_CERT_TIER, each log saying
which: ``[ TIER] <tier>``): default, every script but the release tier's;
release, the release tier's alone; all, every script.  The run is judged
against its tier's scripts: each must pass exactly once, and a script of
another tier that reports fails it.

Usage:  python3 scripts/cert_verdict.py [--only "<names>"] [--tier <tier>] <log> [<log> ...] <run_all_cscripts.do>
        --only judges just the scripts it names (a DASH_CERT_ONLY run),
        whatever their tier; --tier names the run's tier (default, release
        or all; default when it is not given).
Exit:   0 when every registered script passed; 1 otherwise, naming each
        script that failed, skipped, never reported or reported twice.
"""
import re
import sys

# A script is registered by a `do' of its file, from test/ or -- one of them,
# which must run from the package root -- as test/<name>.
_REGISTERED = re.compile(r'^\s*do "(?:[^"]*/)?([^"/]+\.cscript)"\s*$', re.M)
_RESULT = re.compile(r"^\[ (PASS|FAIL|SKIP)\] (\S+\.cscript)\b", re.M)
_SUMMARY = re.compile(r"^ALL TESTS PASSED \((\d+) passed, (\d+) skipped\)\s*$",
                      re.M)
_SHARD = re.compile(r"^\[SHARD\] ([1-9])/([1-9]):", re.M)
# A shard-table row whose shards are "*": the script runs in every shard.
_TIER = re.compile(r"^\[ TIER\] (\S+)", re.M)
_RELEASE = re.compile(r"^local _cert_release\b([ \t\w.]*)$", re.M)
#: The tiers a run can be of.
TIERS = ("default", "release", "all")
_EVERY = re.compile(r"^\s+(test_\w+\.cscript)\s+[0-9.]+\s+[01]\s+\*\s+\*"
                    r"\s+\*\s*(?:///)?\s*$", re.M)


def registered_scripts(runner_text):
    """The certification scripts the runner runs, in its order."""
    return _REGISTERED.findall(runner_text)


def every_shard_scripts(runner_text):
    """The scripts the runner's shard table runs in every shard (``*``)."""
    return _EVERY.findall(runner_text)


def release_scripts(runner_text):
    """The release tier: the scripts the runner's ``local _cert_release``
    line names, in its order."""
    out = []
    for m in _RELEASE.finditer(runner_text):
        out += m.group(1).split()
    return out


def tier_scripts(runner_text, tier):
    """The registered scripts a run of *tier* runs, in the runner's order."""
    if tier not in TIERS:
        raise ValueError("the tier must be one of %s, not %r"
                         % (", ".join(TIERS), tier))
    scripts = registered_scripts(runner_text)
    release = set(release_scripts(runner_text))
    if tier == "default":
        return [s for s in scripts if s not in release]
    if tier == "release":
        return [s for s in scripts if s in release]
    return scripts


def verdict(log_text, runner_text, only=None, tier="default"):
    """(ok, lines) for a run in one session: see verdict_logs."""
    return verdict_logs([log_text], runner_text, only, tier)


def verdict_logs(log_texts, runner_text, only=None, tier="default"):
    """(ok, lines): whether the run passed, and a report to print.

    ok is True only when every script of the run's *tier* (or every one
    *only* names, whatever its tier) reported PASS, none reported FAIL or
    SKIP, no script reported twice, no script outside them reported, no
    log names another tier, and each log's own summary says all of its
    scripts passed with none skipped.  More than one log is a sharded run:
    each must name its shard, and together they must be shards 1 to N of
    one N, each once.
    """
    registered = registered_scripts(runner_text)
    scripts = tier_scripts(runner_text, tier)
    unknown = []
    if only is not None:
        want = [n if n.endswith(".cscript") else n + ".cscript"
                for n in only]
        unknown = sorted(set(want) - set(registered))
        scripts = [s for s in registered if s in want]
    results = {}
    twice = []
    log_probs = []
    shards = []
    # In a sharded run a "*" script reports once in each log.
    every = set(every_shard_scripts(runner_text)) if len(log_texts) > 1 \
        else set()
    every_seen = {s: [] for s in every}
    for i, text in enumerate(log_texts, 1):
        if only is None:
            for named in sorted(set(_TIER.findall(text)) - {tier}):
                log_probs.append("log %d ran the %s tier, not the %s tier"
                                 % (i, named, tier))
        found = _SHARD.findall(text)
        if len(log_texts) > 1:
            if len(found) != 1:
                log_probs.append("log %d names %d shards, not one"
                                 % (i, len(found)))
            else:
                shards.append((int(found[0][0]), int(found[0][1])))
        passed_here = 0
        here = set()
        for status, name in _RESULT.findall(text):
            if name in every:
                if name in here:
                    twice.append(name)
                here.add(name)
                every_seen[name].append(status)
                passed_here += status == "PASS"
                continue
            if name in results:
                twice.append(name)
            results[name] = status
            passed_here += status == "PASS"
        for name in sorted(every & set(scripts) - here):
            log_probs.append("log %d never reported %s, which runs in every "
                             "shard" % (i, name))
        m = _SUMMARY.search(text)
        if len(log_texts) > 1 and (not m or int(m.group(2)) != 0
                                   or int(m.group(1)) != passed_here):
            log_probs.append("log %d: the runner's summary does not say its "
                             "%d script(s) passed with none skipped"
                             % (i, passed_here))
    if len(log_texts) > 1 and len(shards) == len(log_texts):
        n = len(log_texts)
        if sorted(shards) != [(k, n) for k in range(1, n + 1)]:
            log_probs.append("the logs are shards %s, not 1 to %d of %d"
                             % (" ".join("%d/%d" % s for s in sorted(shards)),
                                n, n))
    for name, seen in every_seen.items():
        if seen:
            results[name] = ("FAIL" if "FAIL" in seen else
                             "SKIP" if "SKIP" in seen else "PASS")
    failed = [s for s in scripts if results.get(s) == "FAIL"]
    skipped = [s for s in scripts if results.get(s) == "SKIP"]
    missing = [s for s in scripts if s not in results]
    stray = sorted(set(results) - set(registered))
    outside = sorted(set(results) & set(registered) - set(scripts))
    passed = [s for s in scripts if results.get(s) == "PASS"]
    if len(log_texts) == 1:
        # One session ran everything: its count is the whole run's.
        m = _SUMMARY.search(log_texts[0])
        summary_ok = bool(m) and int(m.group(1)) == len(scripts) \
            and int(m.group(2)) == 0
    else:
        summary_ok = not log_probs
    ok = bool(scripts) and not (failed or skipped or missing or stray
                                or outside or twice or unknown
                                or log_probs) and summary_ok
    head = "certification suite: %d of %d registered scripts passed" % (
        len(passed), len(scripts))
    notes = []
    if len(log_texts) > 1:
        notes.append("%d sessions" % len(log_texts))
    if only is None and tier != "default":
        notes.append("%s tier" % tier)
    if notes:
        head += " (%s)" % ", ".join(notes)
    lines = [head]
    left = [s for s in release_scripts(runner_text) if s in registered]
    if only is None and tier == "default" and left:
        lines.append("  left to the release tier: " + " ".join(left))
    within = ("named by --only" if only is not None
              else "in the %s tier" % tier)
    for label, names in (("failed", failed), ("skipped", skipped),
                         ("never reported", missing),
                         ("reported but not registered", stray),
                         ("reported but not " + within, outside),
                         ("reported twice", twice),
                         ("named by --only but not registered", unknown)):
        if names:
            lines.append("  %s: %s" % (label, " ".join(names)))
    if not scripts:
        lines.append("  the runner registers no script")
    for p in log_probs:
        lines.append("  " + p)
    if len(log_texts) == 1 and not summary_ok:
        lines.append("  the runner's summary does not say all %d passed "
                     "with none skipped" % len(scripts))
    lines.append("verdict: " + ("PASS" if ok else "FAIL"))
    return ok, lines


def main(argv):
    args = list(argv[1:])
    only = None
    tier = "default"
    while args[:1] in (["--only"], ["--tier"]):
        if len(args) < 2:
            sys.stderr.write(__doc__)
            return 2
        if args[0] == "--only":
            only = args[1].split()
        else:
            tier = args[1]
            if tier not in TIERS:
                sys.stderr.write("cert_verdict.py: --tier must be one of %s\n"
                                 % ", ".join(TIERS))
                return 2
        args = args[2:]
    if len(args) < 2:
        sys.stderr.write(__doc__)
        return 2
    logs, runner = args[:-1], args[-1]
    texts = []
    for path in logs:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                texts.append(fh.read())
        except OSError as exc:
            print("certification suite: no log to judge (%s)" % exc)
            print("verdict: FAIL")
            return 1
    with open(runner, encoding="utf-8") as fh:
        runner_text = fh.read()
    ok, lines = verdict_logs(texts, runner_text, only, tier)
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
