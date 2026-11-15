"""The certification suite's shard table (WP-30 test performance, C).

test/run_all_cscripts.do runs every certification script in one Stata
session, or -- with DASH_CERT_SHARD=k/N -- only the scripts of shard k of N,
so that scripts/run_cert_suite.sh can run N sessions side by side.  Which
script is in which shard is the table between the runner's
``// ---- shards: begin`` and ``// ---- shards: end`` lines: one row a
script, with the seconds it took in a timed run, whether it runs
``dash serve`` on a fixed port, and its shard for N = 2 to 8.

The shards are balanced by longest processing time first: the scripts, from
the longest, each go to the least loaded shard (the lowest numbered of
equals).  Every script that runs ``dash serve`` on one of the fixed ports
5006, 5097, 5098 and 5099 -- the default port is 5006 -- is one unit, so
they always share a shard and never serve at once: a logical line (``///``
continuations joined, comments dropped) whose command, after any capture,
noisily or quietly, is ``dash serve`` or ``_dash_serve`` and which names one
of those ports or no port().

A script that splits itself -- it reads DASH_CERT_SHARD (``local <name> :
env[ironment] DASH_CERT_SHARD``) and runs only its own part of N, as
test_wp30_truth.cscript does with its blocks -- runs in every shard when
the split rule stars it: its row's shards are ``*``.  The rule (WP-50
50-02, D-50-02.b): SPLIT_MIN is SPLIT_SHARE (a half) of one session's
balanced load, the table's seconds summed over SESSIONS (the batch-end
gate's sessions, scripts/run_all_tests.sh's DASH_CERT_SESSIONS default).
A WP truth script made from test/templates/wp_truth_template.cscript can
run whole (its head calls ``_w<NN>_whole()``, which reads its row): it is
starred only when its seconds are at least SPLIT_MIN, and otherwise is
placed whole, one shard number for each N like any other script, so that
the one session that runs it clears and loads dash once.  A script that
splits itself and cannot run whole (test_wp30_truth.cscript and
test_wp31_truth.cscript) is always starred.

A starred script's parts are the same longest-first rule over its blocks'
seconds (its ``parts`` section, which split_parts mirrors), so part 1 is
always its longest; with eight sessions every script's longest part fell
to session 1, which ran 542 s while session 8 ran 168 s (11nov2026).  So
the table turns each split script's parts: ``*r`` for N sessions has
session k run part ((k - 1 - r) mod N) + 1, and the turns are chosen,
longest parts first, to even the sessions' loads (each part counted at its
blocks' share of the script's seconds) before the other scripts are placed
on top.  cert_helpers.do's cert_split_part reads the turn from this table.
Without the scripts' texts (the parts unknown), a split script counts its
seconds divided by N in every shard, as before.

The template-made scripts' block seconds live in the runner too, in a
second generated block directly after the shard table (between
``// ---- block seconds: begin`` and ``// ---- block seconds: end``): one
``// secs <script> S00 1 S01 12 ...`` line a script, which the script's
``_w<NN>_secs()`` reads (no line: ``S00 1``; a block not listed counts
1 s).  test_wp30 and test_wp31 keep their own seconds tables.

The release tier (22oct2026; the ``local _cert_release`` line under the
table, which cert_verdict.release_scripts reads) is left out of a default
run: the shards balance the default tier's scripts as if they were alone,
then place the release tier's on top -- a fixed-port one in the fixed-port
scripts' shard, a split one in every shard, the rest longest first onto the
least loaded -- so that a release or all run keeps the fixed-port rule.

Usage:
  python3 scripts/cert_shards.py write <timed run log> [<source>]
          rewrite the table from a run's ``[ TIME] <script> timer=<s>
          wall=<s>`` lines (a script timed more than once, as a split
          script is in the shards' logs put together, counts their
          sum), and the block seconds from its ``S<MM> start`` and
          ``S<MM> end`` lines; <source> says in the table where the
          seconds come from (default: the log's file name).  The
          release tier is kept, and a release-tier script the log does
          not time (a default run's) keeps its seconds
  python3 scripts/cert_shards.py check                   exit 1 unless the
          table holds every registered script, marks exactly the fixed-port
          scripts and, with *, exactly the scripts the split rule stars,
          gives each N the balanced assignment of its seconds, and every
          part of every starred script has a block
  python3 scripts/cert_shards.py rebalance               rewrite the
          table from its own seconds and block seconds: the split rule,
          the shards and the split scripts' turns placed again, as after a
          split script's blocks or their seconds changed (11nov2026)
  python3 scripts/cert_shards.py add <script>            give a registered
          script with no row (a new WP's truth script) a row at 1.0 s and
          place the table again, so that check passes
  python3 scripts/cert_shards.py show                    each N's loads
          (the default tier's and every script's when there is a release
          tier)
"""
import datetime
import math
import os
import re
import sys
import textwrap

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
RUNNER = os.path.join(_REPO, "test", "run_all_cscripts.do")

sys.path.insert(0, _HERE)
import cert_verdict  # noqa: E402

#: The shard counts the table assigns (run_cert_suite.sh runs at most 8;
#: 11nov2026, so that the certification leg fits beside pytest's).
COUNTS = (2, 3, 4, 5, 6, 7, 8)
FIXED_PORTS = ("5006", "5097", "5098", "5099")
BEGIN = "// ---- shards: begin (scripts/cert_shards.py writes this block) ----"
END = "// ---- shards: end ----"
#: The block seconds of the template-made truth scripts (D-50-02.d).
SECS_BEGIN = ("// ---- block seconds: begin (scripts/cert_shards.py writes "
              "this block) ----")
SECS_END = "// ---- block seconds: end ----"
#: The split rule (D-50-02.b): a script that can run whole is starred only
#: at SPLIT_SHARE of one session's balanced load or more, over the gate's
#: SESSIONS (scripts/run_all_tests.sh's DASH_CERT_SESSIONS default, 8 since
#: 11nov2026).
SPLIT_SHARE = 0.5
SESSIONS = 8

_PREFIX = re.compile(r"^(?:(?:capture|cap|noisily|noi|quietly|qui)\s+)+")
_SERVE = re.compile(r"^(?:dash\s+serve|_dash_serve)(?=$|[\s,])")
_FIXED = re.compile(r"\bport\(\s*0*(%s)\s*\)" % "|".join(FIXED_PORTS))
_SPLITS = re.compile(r"^local\s+\w+\s*:\s*env(?:ironment)?\s+DASH_CERT_SHARD$")
EVERY = "*"
_WHOLE = re.compile(r"\b_w\d\d_whole\(")
_BLOCK = re.compile(r"^(S\d+) (start|end)\s+"
                    r"(?:(\d{1,2} [A-Z][a-z]{2} \d{4})\s+)?"
                    r"(\d\d):(\d\d):(\d\d)\s*$")
_SECS_LINE = re.compile(r"^// secs (\S+\.cscript)((?: S\d+ [0-9.]+)*)\s*$",
                        re.M)
WP30 = os.path.join(_REPO, "test", "test_wp30_truth.cscript")
WP30_BEGIN = "// ---- parts: begin"
WP30_END = "// ---- parts: end ----"
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


def splits_itself(text):
    """Whether a script reads DASH_CERT_SHARD to run only its own part."""
    return any(_SPLITS.match(_PREFIX.sub("", ln))
               for ln in logical_lines(text))


def runs_whole(text):
    """Whether a script can run whole: it calls ``_w<NN>_whole(`` (the
    template's head), which reads its row and, for a shard number, runs
    every block (D-50-02.c)."""
    return bool(_WHOLE.search(text))


def split_min(seconds):
    """The seconds at which a script that can run whole is starred: half
    of one session's balanced load over SESSIONS (D-50-02.b)."""
    return SPLIT_SHARE * math.fsum(seconds.values()) / SESSIONS


def starred_by_rule(seconds, text_of):
    """The scripts the split rule stars, of *seconds*' scripts:
    ``text_of(name)`` is a script's text, or None when it cannot be read
    (such a script is not starred)."""
    low = split_min(seconds)
    out = set()
    for s in seconds:
        text = text_of(s)
        if text is None or not splits_itself(text):
            continue
        if not runs_whole(text) or seconds[s] >= low:
            out.add(s)
    return out


def is_every(v):
    """Whether a table entry runs its script in every shard: ``*`` or
    ``*r`` (the script's parts turned by r)."""
    return isinstance(v, str) and v.startswith(EVERY)


def turn_of(v):
    """The turn r of an entry ``*r`` (0 for ``*``)."""
    return int(v[1:] or 0)


def _every_entry(r):
    return EVERY if r == 0 else "%s%d" % (EVERY, r)


def _turn(load, parts, n):
    """The turn r (0..n-1) that adds *parts* (part 1's seconds first) to
    *load* most evenly: the least largest load, then the least sum of
    squares, then the least r.  Session k runs part ((k - 1 - r) mod n) + 1,
    so part p lands on session ((p - 1 + r) mod n) + 1."""
    best = None
    for r in range(n):
        new = list(load)
        for p, sec in enumerate(parts):
            new[(p + r) % n] += sec
        key = (round(max(new), 6), round(math.fsum(v * v for v in new), 6), r)
        if best is None or key < best[0]:
            best = (key, r, new)
    return best[1], best[2]


def _place_split(out, load, split, n, parts):
    """Turn each script in *split* onto *load*, the longest parts first:
    with *parts* ({script: [part seconds]}) each gets its turn, without
    them its seconds are shared out evenly (``*``)."""
    if parts is None:
        share = math.fsum(split.values()) / n
        for s in split:
            out[s] = EVERY
        return [v + share for v in load]
    order = sorted(split, key=lambda s: (-max(parts[s] or [0.0]), s))
    for s in order:
        r, load = _turn(load, parts[s], n)
        out[s] = _every_entry(r)
    return load


def _place_units(out, load, units, n):
    units.sort(key=lambda u: (-u[0], u[1][0]))
    for sec, scripts in units:
        k = min(range(n), key=lambda i: (load[i], i))
        load[k] += sec
        for s in scripts:
            out[s] = k + 1
    return load


def assign(seconds, port, n, every=frozenset(), release=frozenset(),
           parts=None):
    """{script: shard (1..n)}: longest first onto the least loaded shard,
    the fixed-port scripts one unit; each script in *every* is ``*r``,
    placed first (see _place_split; *parts* maps each to its part seconds
    for this n, or None to share its seconds out evenly).  The scripts in
    *release* are placed after the others, on their loads: see the
    module's docstring.  Its sums are math.fsum, exactly rounded, so the
    assignment is the same under every Python (3.12 changed what sum()
    of floats returns, and 3.11 read the table as unbalanced)."""
    if release:
        base = {s: v for s, v in seconds.items() if s not in release}
        out = _assign(base, port, n, every, parts)
        load = loads(base, out, n, parts)
        rel = {s: v for s, v in seconds.items() if s in release}
        load = _place_split(out, load, {s: v for s, v in rel.items()
                                        if s in every}, n, parts)
        rest = {s: v for s, v in rel.items() if s not in every}
        held = sorted(s for s in rest if s in port)
        at = sorted({out[s] for s in base if s in port and s not in every})
        units = [(rest[s], [s]) for s in rest if s not in port]
        if held and at:
            for s in held:
                out[s] = at[0]
                load[at[0] - 1] += rest[s]
        elif held:
            units.append((math.fsum(rest[s] for s in held), held))
        _place_units(out, load, units, n)
        return out
    return _assign(seconds, port, n, every, parts)


def _assign(seconds, port, n, every=frozenset(), parts=None):
    """assign with no release tier."""
    units = []
    together = sorted(s for s in seconds if s in port and s not in every)
    if together:
        units.append((math.fsum(seconds[s] for s in together), together))
    units += [(seconds[s], [s]) for s in seconds
              if s not in port and s not in every]
    out = {}
    load = _place_split(out, [0.0] * n, {s: v for s, v in seconds.items()
                                         if s in every}, n, parts)
    _place_units(out, load, units, n)
    return out


def loads(seconds, shards, n, parts=None):
    """The seconds of each shard of n (a turned split script's parts where
    *parts* has them, else its seconds shared out evenly)."""
    out = [0.0] * n
    for s, k in shards.items():
        if is_every(k):
            if parts is not None and s in parts:
                r = turn_of(k)
                for p, sec in enumerate(parts[s]):
                    out[(p + r) % n] += sec
            else:
                out = [v + seconds[s] / n for v in out]
        else:
            out[k - 1] += seconds[s]
    return out


def split_parts(text, n, total=None, secs=None):
    """[seconds of part 1, ..., part n] of a split script's text for n
    sessions: its blocks (header lines ``* ==== S<NN> ...``, in file
    order) longest first onto the least loaded part, the lowest numbered
    of equals, by the seconds of its ``local w<NN>_secs`` table (a block
    it does not list counting the script's default, ``sec = J(rows(ids),
    1, <d>)``) -- what the script's own Mata computes.  With *total* the
    parts are scaled to sum to it (the table's measured seconds).  With
    *secs* ({block: seconds}, a template-made script's line of the
    runner's block seconds) those seconds stand for the script's table."""
    ids = []
    for m in re.finditer(r"^\* ==== (S\d+) ", text, re.M):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    m = re.search(r"sec = J\(rows\(ids\), 1, ([0-9.]+)\)", text)
    default = float(m.group(1)) if m else 1.0
    if secs is None:
        secs = {}
        for line in logical_lines(text):
            m = re.match(r"^local w\w+_secs\s+(.*)$", line)
            if m:
                toks = m.group(1).split()
                secs = {toks[i]: float(toks[i + 1])
                        for i in range(0, len(toks) - 1, 2)}
                break
    sec = [secs.get(i, default) for i in ids]
    order = sorted(range(len(ids)), key=lambda i: (-sec[i], i))
    load = [0.0] * n
    for i in order:
        k = min(range(n), key=lambda j: (load[j], j))
        load[k] += sec[i]
    if total is not None:
        raw = math.fsum(load)
        load = ([v * total / raw for v in load] if raw > 0
                else [total / n] * n)
    return load


def parts_of(seconds, every, n, text_of, block_secs=None):
    """{split script: its part seconds for n} at the table's seconds, from
    each script's text (``text_of(name)``); a script that can run whole
    takes its blocks' seconds from *block_secs* (the runner's block
    seconds, {script: {block: seconds}}; none listed: S00 1)."""
    block_secs = block_secs or {}
    out = {}
    for s in every:
        text = text_of(s)
        secs = (block_secs.get(s, {"S00": 1.0}) if runs_whole(text)
                else None)
        out[s] = split_parts(text, n, seconds[s], secs)
    return out


def block_ids(text):
    """A script's block ids (header lines ``* ==== S<NN> ...``), in file
    order."""
    ids = []
    for m in re.finditer(r"^\* ==== (S\d+) ", text, re.M):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    return ids


def parts_check(text, secs, name):
    """The problems with a starred template-made script's parts: a part of
    some N that holds no block (it would clear and load dash for nothing).
    Blocks count their *secs* ({block: seconds}) or 1 s, as the script's
    own Mata does."""
    ids = block_ids(text)
    probs = []
    for n in COUNTS:
        parts = assign({i: float(secs.get(i, 1.0)) for i in ids}, set(), n)
        if set(parts.values()) != set(range(1, n + 1)):
            probs.append("%s: a part of %d has no block (%d blocks)"
                         % (name, n, len(ids)))
    return probs


def block_seconds_from_log(log_text):
    """{script: {block: seconds}} from a timed run's ``S<MM> start <date>
    <time>`` and ``S<MM> end <date> <time>`` lines (the date may be
    missing): each block's lines between the previous ``[ TIME]`` line and
    its script's own, end minus start (a midnight wrap adding 86,400 s),
    summed over a block id's repeats and over the logs put together,
    rounded up, at least 1."""
    out, here, open_at = {}, {}, {}

    def stamp(m):
        hms = int(m.group(4)) * 3600 + int(m.group(5)) * 60 + int(m.group(6))
        if m.group(3):
            day = datetime.datetime.strptime(m.group(3), "%d %b %Y")
            return day.toordinal() * 86400 + hms, True
        return hms, False

    for line in log_text.splitlines():
        t = _TIME.match(line)
        if t:
            got = out.setdefault(t.group(1), {})
            for b, v in here.items():
                got[b] = got.get(b, 0.0) + v
            here, open_at = {}, {}
            continue
        m = _BLOCK.match(line)
        if not m:
            continue
        at, dated = stamp(m)
        if m.group(2) == "start":
            open_at[m.group(1)] = (at, dated)
        elif m.group(1) in open_at:
            was, was_dated = open_at.pop(m.group(1))
            if dated and was_dated:
                d = at - was
            else:
                d = (at % 86400) - (was % 86400)
            if d < 0:
                d += 86400
            here[m.group(1)] = here.get(m.group(1), 0.0) + d
    return {s: {b: max(1, int(math.ceil(v - 1e-9))) for b, v in d.items()}
            for s, d in out.items() if d}


def read_block_seconds(runner_text):
    """{script: {block: seconds}} from the runner's block seconds (none:
    {})."""
    if runner_text.count(SECS_BEGIN) != 1 or runner_text.count(SECS_END) != 1:
        return {}
    block = runner_text[runner_text.index(SECS_BEGIN):
                        runner_text.index(SECS_END)]
    out = {}
    for m in _SECS_LINE.finditer(block):
        toks = m.group(2).split()
        out[m.group(1)] = {toks[i]: float(toks[i + 1])
                           for i in range(0, len(toks) - 1, 2)}
    return out


def render_block_seconds(block_secs, source):
    """The block seconds' text: one ``// secs`` line a script, by name,
    its blocks by id."""
    lines = [
        SECS_BEGIN,
        "// The blocks' seconds of each WP truth script made from",
        "// test/templates/wp_truth_template.cscript, which its _wNN_secs()",
        "// reads to balance its parts when the shard table stars it (no",
        "// line: S00 1; a block not listed counts 1 s).",
    ]
    lines += ["// " + ln for ln in textwrap.wrap(
        "Seconds: " + " ".join(source.split()), 72)]

    def num(v):
        return "%d" % v if float(v) == int(v) else "%g" % v
    for s in sorted(block_secs):
        d = block_secs[s]
        lines.append("// secs %s %s" % (s, " ".join(
            "%s %s" % (b, num(d[b])) for b in sorted(d))))
    lines.append(SECS_END)
    return "\n".join(lines) + "\n"


def put_block_seconds(runner_text, new):
    """The runner with its block seconds replaced by *new*, or put
    directly after the shard table's end marker."""
    if runner_text.count(SECS_BEGIN) == 1 and \
            runner_text.count(SECS_END) == 1:
        a = runner_text.index(SECS_BEGIN)
        b = runner_text.index(SECS_END) + len(SECS_END)
        if runner_text[b:b + 1] == "\n":
            b += 1
        return runner_text[:a] + new + runner_text[b:]
    at = runner_text.index(END) + len(END)
    if runner_text[at:at + 1] == "\n":
        at += 1
    return runner_text[:at] + new + runner_text[at:]


def wp30_parts(text, n):
    """{block id: part (1..n)} for test_wp30_truth.cscript's text: its
    blocks (header lines ``* ==== S<NN> ...``) longest first by the seconds
    of its parts section, a block it does not list counting 0 s -- what the
    script's own Mata computes."""
    ids = []
    for m in re.finditer(r"^\* ==== (S\d+) ", text, re.M):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    secs = wp30_seconds(text)
    return assign({i: secs.get(i, 0.0) for i in ids}, set(), n)


def wp30_seconds(text):
    """{block id: seconds} from test_wp30_truth.cscript's parts section."""
    if text.count(WP30_BEGIN) != 1 or text.count(WP30_END) != 1:
        raise ValueError("test_wp30_truth.cscript has no single parts "
                         "section")
    sect = text[text.index(WP30_BEGIN):text.index(WP30_END)]
    m = re.search(r"^local w30_secs ///\n((?:.*///\n)*.*)$", sect, re.M)
    if not m:
        raise ValueError("test_wp30_truth.cscript's parts section has no "
                         "w30_secs")
    toks = m.group(1).replace("///", " ").split()
    return {toks[i]: float(toks[i + 1]) for i in range(0, len(toks) - 1, 2)}


def read_table(runner_text):
    """[(script, seconds, port, {N: shard})] from the runner's block."""
    if runner_text.count(BEGIN) != 1 or runner_text.count(END) != 1:
        raise ValueError("the runner has no single shard table")
    block = runner_text[runner_text.index(BEGIN):runner_text.index(END)]
    rows = []
    cols = r"\s+([1-8]|\*[0-7]?)" * len(COUNTS)
    for m in re.finditer(r"^\s+(test_\w+\.cscript)\s+([0-9.]+)\s+([01])"
                         + cols + r"\s*(?:///)?\s*$", block, re.M):
        rows.append((m.group(1), float(m.group(2)), m.group(3) == "1",
                     dict(zip(COUNTS, (k if is_every(k) else int(k)
                                       for k in m.groups()[3:])))))
    return rows


def continuation_problems(runner_text):
    """The table is one Stata command over many lines: every row but the
    last ends in `///' and the last does not.  A row after an unfinished
    last row is read by Stata as a command of its own (r(199), and no
    script runs), though read_table takes it."""
    if runner_text.count(BEGIN) != 1 or runner_text.count(END) != 1:
        return []
    block = runner_text[runner_text.index(BEGIN):runner_text.index(END)]
    rows = [ln for ln in block.splitlines()
            if re.match(r"^\s+test_\w+\.cscript\s", ln)]
    names = [ln.split()[0] for ln in rows]
    probs = []
    for i, ln in enumerate(rows[:-1]):
        if not ln.rstrip().endswith("///"):
            probs.append("%s's row ends the table's command, but %s's row "
                         "follows it" % (names[i], names[i + 1]))
    if rows and rows[-1].rstrip().endswith("///"):
        probs.append("the table's last row, %s's, continues into the next "
                     "line" % names[-1])
    return probs


def read_release(runner_text):
    """The release tier the runner's table names (its order)."""
    return cert_verdict.release_scripts(runner_text)


def render_table(seconds, port, source, every=frozenset(),
                 release=frozenset(), text_of=None, block_secs=None):
    """The block's text for these seconds, fixed-port scripts, scripts
    that split themselves over every shard and release-tier scripts; with
    *text_of* (a script's name -> its text) the split scripts' parts are
    turned (see the module's docstring; *block_secs*, the runner's block
    seconds, for the template-made ones).  The shards are those of the
    seconds as the table writes them, to a tenth, so that check agrees."""
    seconds = {s: float("%.1f" % v) for s, v in seconds.items()}
    shards = {n: assign(seconds, port, n, every, release,
                        None if text_of is None
                        else parts_of(seconds, every, n, text_of,
                                      block_secs))
              for n in COUNTS}
    lines = [
        BEGIN,
        "// Each certification script: the seconds it takes, 1 when it runs",
        "// dash serve on a fixed port (5006, 5097, 5098, 5099), and its shard",
        "// when DASH_CERT_SHARD splits the run in 2 to 8 (a column each):",
        "// longest first onto the least loaded shard, the fixed-port scripts",
        "// as one unit so that they never serve at once; *r when a script",
        "// runs in every shard and splits itself (it reads DASH_CERT_SHARD),",
        "// its parts turned by r (cert_helpers.do's cert_split_part: session",
        "// k runs part ((k - 1 - r) mod N) + 1), the turns chosen to even the",
        "// sessions before the other scripts are placed.  A WP truth script",
        "// made from the template is * only when it takes at least half of",
        "// one session's balanced load over the gate's sessions",
        "// (scripts/cert_shards.py's split rule); with a shard number it",
        "// runs every block in that one session.  Unset, the run is every",
        "// script, in this session.",
    ]
    lines += ["// " + ln for ln in textwrap.wrap(
        "Seconds: " + " ".join(source.split()), 72)]
    lines.append("local _cert_shards ///")
    width = max(len(s) for s in seconds)
    names = sorted(seconds)
    for i, s in enumerate(names):
        lines.append("    %-*s %7.1f %d  %s%s"
                     % (width, s, seconds[s], 1 if s in port else 0,
                        " ".join(str(shards[n][s]) for n in COUNTS),
                        " ///" if i < len(names) - 1 else ""))
    if release:
        lines += [
            "// The release tier: the closed work packages' truth scripts,",
            "// which a default run (make cert, make test-all) leaves out and",
            "// DASH_CERT_TIER=release or all runs (make cert-release, make",
            "// cert-all, make gate); their shards are placed on top of the",
            "// default tier's balance.",
            "local _cert_release " + " ".join(sorted(release))]
    return "\n".join(lines) + "\n"


def seconds_from_log(log_text):
    """{script: seconds} from a timed run's `[ TIME]' lines: the timer, or
    the wall clock where a script's own clear all reset the timer.  A script
    timed more than once (a split script in its shards' logs put together)
    counts the sum."""
    out = {}
    for name, timer, wall in _TIME.findall(log_text):
        out[name] = out.get(name, 0.0) + (float(wall) if timer == "."
                                          else float(timer))
    return out


def _cscript_text(name):
    with open(os.path.join(_REPO, "test", name), encoding="utf-8",
              errors="replace") as fh:
        return fh.read()


def _text_or_none(name):
    """A script's text, or None when the runner's folder does not hold
    it."""
    if not os.path.exists(os.path.join(_REPO, "test", name)):
        return None
    return _cscript_text(name)


def _split_texts(every):
    """_cscript_text when every split script is there to read, else None
    (their seconds are then shared out evenly)."""
    if all(os.path.exists(os.path.join(_REPO, "test", s)) for s in every):
        return _cscript_text
    return None


def check(runner_text):
    """The problems with the runner's table, one line each."""
    probs = []
    try:
        rows = read_table(runner_text)
    except ValueError as exc:
        return [str(exc)]
    probs += continuation_problems(runner_text)
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
    release = read_release(runner_text)
    if len(release) != len(set(release)):
        probs.append("the release tier names a script twice")
    if set(release) - set(named):
        probs.append("the release tier names a script the runner does not "
                     "run: " + " ".join(sorted(set(release) - set(named))))
    release = set(release) & set(named)
    starred = {r[0] for r in rows if any(is_every(v)
                                         for v in r[3].values())}
    if any(not all(is_every(v) for v in r[3].values())
           for r in rows if r[0] in starred):
        probs.append("a row is * for some N and not for every N")
    rule = starred_by_rule(seconds, _text_or_none)
    if starred != rule:
        probs.append("* marks %s, the scripts the split rule stars %s "
                     "(SPLIT_MIN %.1f s)"
                     % (sorted(starred), sorted(rule), split_min(seconds)))
    if starred & marked:
        probs.append("a script that runs in every shard serves on a fixed "
                     "port: " + " ".join(sorted(starred & marked)))
    if "test_wp30_truth.cscript" in starred and os.path.exists(WP30):
        probs += wp30_check(_cscript_text("test_wp30_truth.cscript"))
    block_secs = read_block_seconds(runner_text)
    for s in sorted(starred):
        text = _text_or_none(s)
        if text is not None and runs_whole(text):
            probs += parts_check(text, block_secs.get(s, {}), s)
    text_of = _split_texts(starred)
    for n in COUNTS:
        want = assign(seconds, marked, n, starred, release,
                      None if text_of is None
                      else parts_of(seconds, starred, n, text_of,
                                    block_secs))
        got = {r[0]: r[3][n] for r in rows}
        if got != want:
            probs.append("the shards for N=%d are not the balanced "
                         "assignment of the seconds (a split script's "
                         "blocks changed? python3 scripts/cert_shards.py "
                         "rebalance)" % n)
    return probs


def wp30_check(text):
    """The problems with test_wp30_truth.cscript's parts: its section, a
    listed block it does not have, a part of some N with no timed block
    (a part that runs no case fails the script)."""
    try:
        secs = wp30_seconds(text)
    except ValueError as exc:
        return [str(exc)]
    probs = []
    ids = set(re.findall(r"^\* ==== (S\d+) ", text, re.M))
    if set(secs) - ids:
        probs.append("test_wp30_truth.cscript's parts list blocks it does "
                     "not have: " + " ".join(sorted(set(secs) - ids)))
    for n in COUNTS:
        parts = wp30_parts(text, n)
        timed = {k for b, k in parts.items() if secs.get(b, 0) > 0}
        if timed != set(range(1, n + 1)):
            probs.append("test_wp30_truth.cscript: a part of %d has no "
                         "timed block" % n)
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
        release = set(read_release(runner))
        tiers = [("", rows)]
        if release:
            tiers = [(" default", [r for r in rows if r[0] not in release]),
                     (" all", rows)]
        every = {r[0] for r in rows if is_every(r[3][COUNTS[0]])}
        text_of = _split_texts(every)
        block_secs = read_block_seconds(runner)
        for label, these in tiers:
            seconds = {r[0]: r[1] for r in these}
            for n in COUNTS:
                shards = {r[0]: r[3][n] for r in these}
                parts = (None if text_of is None else parts_of(
                    seconds, every & set(seconds), n, text_of, block_secs))
                print("N=%d%s: %s" % (n, label, "  ".join(
                    "%d: %.0f s" % (k + 1, v)
                    for k, v in enumerate(loads(seconds, shards, n,
                                                parts)))))
        if os.path.exists(WP30):
            text = _cscript_text("test_wp30_truth.cscript")
            secs = wp30_seconds(text)
            for n in COUNTS:
                parts = wp30_parts(text, n)
                print("test_wp30_truth N=%d: %s" % (n, "  ".join(
                    "%d: %.0f s" % (k, sum(secs.get(b, 0) for b, p in
                                           parts.items() if p == k))
                    for k in range(1, n + 1))))
        return 0
    if (argv[1:2] == ["rebalance"] and len(argv) == 2) or \
            (argv[1:2] == ["add"] and len(argv) == 3):
        rows = read_table(runner)
        seconds = {r[0]: r[1] for r in rows}
        port = {r[0] for r in rows if r[2]}
        if argv[1] == "add":
            name = argv[2]
            if name in seconds:
                print("cert_shards: %s already has a row" % name)
                return 1
            if name not in cert_verdict.registered_scripts(runner) or \
                    _text_or_none(name) is None:
                print("cert_shards: %s is not a script the runner runs "
                      "(register its block first)" % name)
                return 1
            seconds[name] = 1.0
            if serves_on_a_fixed_port(_cscript_text(name)):
                port.add(name)
        block = runner[runner.index(BEGIN):runner.index(END)]
        m = re.search(r"^// Seconds: (.*?)\nlocal _cert_shards", block,
                      re.M | re.S)
        source = " ".join(m.group(1).replace("//", " ").split()) if m \
            else "the table's own seconds"
        if argv[1] == "add":
            source += "; %s added at 1.0 s" % argv[2]
        # The split rule where the scripts are there to read, else the
        # table's own stars.
        if all(_text_or_none(s) is not None for s in seconds):
            every = starred_by_rule(seconds, _text_or_none)
        else:
            every = {r[0] for r in rows if is_every(r[3][COUNTS[0]])}
        new = render_table(seconds, port, source, every,
                           set(read_release(runner)), _split_texts(every),
                           read_block_seconds(runner))
        with open(RUNNER, "w", encoding="utf-8") as fh:
            fh.write(runner[:runner.index(BEGIN)] + new
                     + runner[runner.index(END):])
        if argv[1] == "add":
            print("cert_shards: added %s at 1.0 s and placed the table's "
                  "%d scripts again" % (argv[2], len(seconds)))
        else:
            print("cert_shards: placed the table's %d scripts again"
                  % len(seconds))
        return 0
    if argv[1:2] == ["write"] and len(argv) in (3, 4):
        with open(argv[2], encoding="utf-8", errors="replace") as fh:
            log_text = fh.read()
        seconds = seconds_from_log(log_text)
        scripts = cert_verdict.registered_scripts(runner)
        release = set(read_release(runner)) & set(scripts)
        # A default run times no release-tier script: it keeps its seconds.
        try:
            kept = {r[0]: r[1] for r in read_table(runner)}
        except ValueError:
            kept = {}
        for s in release - set(seconds):
            if s in kept:
                seconds[s] = kept[s]
        lacking = sorted(set(scripts) - set(seconds))
        if lacking:
            print("cert_shards: the log times no run of: " + " ".join(lacking))
            return 1
        seconds = {s: seconds[s] for s in scripts}
        port = {s for s in scripts
                if serves_on_a_fixed_port(_cscript_text(s))}
        every = starred_by_rule(seconds, _cscript_text)
        source = argv[3] if len(argv) == 4 else os.path.basename(argv[2])
        # The template-made scripts' blocks from the log; a script it
        # does not time keeps its line.
        block_secs = read_block_seconds(runner)
        logged = block_seconds_from_log(log_text)
        for s in scripts:
            if runs_whole(_cscript_text(s)) and s in logged:
                block_secs[s] = logged[s]
        block_secs = {s: v for s, v in block_secs.items() if s in scripts
                      and runs_whole(_cscript_text(s))}
        new = render_table(seconds, port, source, every, release,
                           _split_texts(every), block_secs)
        start = runner.index(BEGIN)
        stop = runner.index(END)
        runner = runner[:start] + new + runner[stop:]
        runner = put_block_seconds(runner, render_block_seconds(
            block_secs, source))
        with open(RUNNER, "w", encoding="utf-8") as fh:
            fh.write(runner)
        print("cert_shards: wrote the table for %d scripts" % len(seconds))
        return 0
    sys.stderr.write(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
