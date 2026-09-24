#!/usr/bin/env python3
"""Measure which Stata programs and Mata functions the certification suite runs.

    python3 scripts/measure_stata_coverage.py units
    python3 scripts/measure_stata_coverage.py prepare --work DIR [--scripts A,B]
    python3 scripts/measure_stata_coverage.py run     --work DIR [--scripts A,B]
    python3 scripts/measure_stata_coverage.py report  --work DIR [--json FILE]

``units`` lists every ``program define`` in the shipped ado files and every
function in dash_parse.mata.  ``run`` does ``prepare``, builds the recorder,
runs every certification script test/run_all_cscripts.do names (through a
generated copy of that runner, never the committed one) and prints
``report``.  ``--scripts`` runs only the scripts named, which may include one
the runner does not name yet.  WORK must be a scratch directory outside the
repository; nothing under the repository is written.  Run it only when no
other full certification run is going: it is one.

WHY NOT STATA'S PROFILER
------------------------
``profiler on`` ... ``profiler report`` counts ado-program calls, but
``clear all``, ``clear`` and ``discard`` each destroy its store.  Measured
24sep2026 on StataNow 19.5: after any one of them ``profiler report`` shows a
count of 0 and every later profiled call prints "class system failure".
Every certification script begins with ``cscript``, which runs ``clear all``,
and 17 scripts clear again later, so a profiled run of the suite reports
nothing.  Stata has no Mata profiler at all.

HOW IT MEASURES INSTEAD
-----------------------
A scratch copy of the tree is instrumented: every ado program's first line
becomes ``mata: _pc_rec("ado:<name>")`` and every Mata function's first
statement ``_pc_rec("mata:<name>")`` (Mata accepts a statement before the
declarations, measured).  ``_pc_rec`` lives in a Mata library, lpcrec.mlib,
built into WORK/lib and put on the ado-path, so Mata autoloads it again after
every ``clear all`` / ``mata clear`` a script runs (measured: it survives
``clear all``, ``cscript`` and ``mata clear``).  It counts calls in an
external associative array and appends ``+<unit><TAB><count>`` to
WORK/hits.log when a count reaches a power of two; the generated runner
writes ``== <script>`` before each script and, after it, ``=<unit><TAB>
<count>`` for every unit counted since the last reset.  A reset (a new
external after ``clear all``) writes ``## lifetime``.  So: executed or not is
exact; which scripts executed a unit is exact; a call count is exact for the
last lifetime of a script and at least half the true count for a lifetime
cut short by a ``clear all``.

The recorder writes nothing to the Results window (the hits file exists
before the run, so ``fopen(, "a")`` has nothing to announce), and neither
the ``mata:`` line nor the call changes ``_rc``, ``r()`` or ``s()``.

Python-side tests do not enter this measure: no pytest file starts Stata
(they read dash.ado and dash_parse.mata as text at most), so the Stata-side
units are executed by the certification scripts alone.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The shipped Stata sources whose units are measured (dash.pkg ships these).
ADO_FILES = ("dash.ado", "dash_setup.ado")
MATA_FILES = ("dash_parse.mata",)

#: The console binary (CLAUDE.md: never the GUI application).
STATA = ["arch", "-arm64", "/usr/local/bin/stata-mp", "-b", "do"]

_PROGRAM = re.compile(r"^\s*program\s+(?:define\s+)?([A-Za-z_]\w*)")
_NOT_A_DEFINITION = {"drop", "dir", "list"}
_MATA_TYPES = ("real", "string", "void", "transmorphic", "pointer",
               "numeric", "complex", "matrix", "struct", "class")
_MATA_FUNC = re.compile(
    r"^(?:%s)\b[^(=;]*?\b([A-Za-z_]\w*)\s*\(" % "|".join(_MATA_TYPES))


# ---------------------------------------------------------------------------
# The inventory
# ---------------------------------------------------------------------------

def _program_lines(lines):
    """``{index: name}`` for each line of *lines* that defines a program.

    ``program`` alone at the start of a line defines a program too; ``program
    drop/dir/list`` do not.  Lines inside ``/* */`` comments and ``*`` or
    ``//`` comment lines are skipped.
    """
    defined = {}
    in_block = False
    for i, line in enumerate(lines):
        code = line
        if in_block:
            if "*/" not in code:
                continue
            code = code.split("*/", 1)[1]
            in_block = False
        if "/*" in code and "*/" not in code.split("/*", 1)[1]:
            in_block = True
            code = code.split("/*", 1)[0]
        if code.lstrip().startswith(("*", "//")):
            continue
        m = _PROGRAM.match(code)
        if m and m.group(1) not in _NOT_A_DEFINITION:
            defined[i] = m.group(1)
    return defined


def ado_programs(path):
    """``[(name, line_number)]`` for every ``program define`` in *path*."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    return [(name, i + 1) for i, name in sorted(_program_lines(lines).items())]


def mata_functions(path):
    """``[(name, line_number)]`` for every function defined in *path*.

    A definition starts at column 0 with a Mata type keyword and a name
    followed by ``(``; the body's opening brace follows on that line or a
    later one.  Indented lines (statements, declarations) never match.
    """
    out = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            m = _MATA_FUNC.match(line)
            if m:
                out.append((m.group(1), n))
    return out


def inventory(root=REPO):
    """``[(file, kind, name, line)]`` for every measured unit, in file order."""
    units = []
    for f in ADO_FILES:
        units += [(f, "ado", n, l) for n, l in ado_programs(os.path.join(root, f))]
    for f in MATA_FILES:
        units += [(f, "mata", n, l) for n, l in mata_functions(os.path.join(root, f))]
    return units


# ---------------------------------------------------------------------------
# Instrumentation
# ---------------------------------------------------------------------------

_CONTINUED = re.compile(r"(^|\s)///")
_PARSES_ARGS = re.compile(r"^    (?:syntax|args)\b")


def instrument_ado(src):
    """*src* with ``mata: _pc_rec("ado:<name>")`` after each program's
    ``program define`` line (after its ``///`` continuations), and
    ``mata: _pc_rec("ado+:<name>")`` after the program's own ``syntax`` or
    ``args`` line when it has one at the body's top level.

    The second probe separates a program that was entered from one whose
    body ran: ``capture dash_setup, garbage(1)`` enters dash_setup and is
    refused by its ``syntax`` line, which is all two certification cases
    ever did with it.
    """
    lines = src.split("\n")
    names = {}
    bodies = set()
    defined = _program_lines(lines)
    out = []
    i = 0
    current = None
    while i < len(lines):
        out.append(lines[i])
        if i in defined:
            current = defined[i]
            j = i
            while _CONTINUED.search(lines[j]) and j + 1 < len(lines):
                j += 1
                out.append(lines[j])
            out.append('    mata: _pc_rec("ado:%s")' % current)
            names[current] = names.get(current, 0) + 1
            i = j + 1
            continue
        if current and re.match(r"^end\s*$", lines[i]):
            current = None
        elif current and _PARSES_ARGS.match(lines[i]):
            j = i
            while _CONTINUED.search(lines[j]) and j + 1 < len(lines):
                j += 1
                out.append(lines[j])
            out.append('    mata: _pc_rec("ado+:%s")' % current)
            bodies.add(current)
            current = None      # one body probe per program
            i = j + 1
            continue
        i += 1
    return "\n".join(out), names, bodies


def instrument_mata(src):
    """*src* with ``_pc_rec("mata:<name>")`` as each function's first
    statement, inserted right after the body's opening brace."""
    lines = src.split("\n")
    out = []
    names = {}
    i = 0
    while i < len(lines):
        m = _MATA_FUNC.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        name = m.group(1)
        # Find the body's opening brace: this line or a later one.
        j = i
        while "{" not in lines[j]:
            out.append(lines[j])
            j += 1
            if j >= len(lines):
                raise ValueError("no opening brace for %s" % name)
        line = lines[j]
        k = line.index("{")
        rest = line[k + 1:]
        call = '_pc_rec("mata:%s")' % name
        if rest.strip() == "" or rest.strip().startswith("//"):
            out.append(line)
            out.append("    " + call)
        else:
            out.append(line[:k + 1] + " " + call + "; " + rest)
        names[name] = names.get(name, 0) + 1
        i = j + 1
    return "\n".join(out), names


# ---------------------------------------------------------------------------
# The recorder library and the generated runner
# ---------------------------------------------------------------------------

def _stata_path_ok(p):
    return not any(c in p for c in '"`$\'\n\r')


def recorder_do(work):
    """A do-file that builds WORK/lib/lpcrec.mlib, which appends to
    WORK/hits.log (a path fixed into the library, since the scripts drop
    every global)."""
    hits = os.path.join(work, "hits.log")
    lib = os.path.join(work, "lib")
    return r"""
clear all
mata:
mata set matastrict on
void _pc_write(string scalar line)
{
    real scalar fh
    fh = fopen("%(hits)s", "a")
    fput(fh, line)
    fclose(fh)
}
pointer(transmorphic) scalar _pc_counts()
{
    pointer(transmorphic) scalar p
    p = findexternal("_pc_counts_aa")
    if (p == NULL) {
        p = crexternal("_pc_counts_aa")
        *p = asarray_create()
        asarray_notfound(*p, 0)
        _pc_write("## lifetime")
    }
    return(p)
}
void _pc_rec(string scalar nm)
{
    pointer(transmorphic) scalar p
    real scalar c, k
    p = _pc_counts()
    c = asarray(*p, nm) + 1
    asarray(*p, nm, c)
    k = round(ln(c) / ln(2))
    if (2^k == c) _pc_write("+" + nm + char(9) + strofreal(c, "%%18.0f"))
}
void _pc_mark(string scalar script)
{
    rmexternal("_pc_counts_aa")
    _pc_write("== " + script)
}
void _pc_flush()
{
    pointer(transmorphic) scalar p
    transmorphic colvector keys
    real scalar i
    p = findexternal("_pc_counts_aa")
    if (p == NULL) {
        _pc_write("## flush-empty")
        return
    }
    keys = asarray_keys(*p)
    for (i = 1; i <= rows(keys); i++) {
        _pc_write("=" + keys[i] + char(9) + strofreal(asarray(*p, keys[i]), "%%18.0f"))
    }
    _pc_write("## flushed")
}
mata mlib create lpcrec, dir("%(lib)s") replace
mata mlib add lpcrec _pc_write() _pc_counts() _pc_rec() _pc_mark() _pc_flush(), dir("%(lib)s")
end
""" % {"hits": hits, "lib": lib}


_SEP = "// " + "-" * 64
_SCRIPT_NAME = re.compile(r"^test_[A-Za-z0-9_]+\.cscript$")


def _generic_block(name):
    """A runner block for a script the committed runner does not name yet:
    run from test/, as the runner runs the others, and tallied the same."""
    return [
        _SEP,
        "// (not in test/run_all_cscripts.do) %s" % name,
        _SEP,
        'display as text "[ RUN ] %s"' % name,
        'cd "`testdir\'"',
        "capture noisily {",
        '    do "%s"' % name,
        "}",
        "local rc = _rc",
        "capture file close _all",
        "capture log close _all",
        'cd "`dashdir\'"',
        "if `rc' == 222 {",
        '    display as text "[ SKIP] %s  (dependency unavailable)"' % name,
        "    local n_skip = `n_skip' + 1",
        "}",
        "else if `rc' == 0 {",
        '    display as text "[ PASS] %s"' % name,
        "    local n_pass = `n_pass' + 1",
        "}",
        "else {",
        '    display as error "[ FAIL] %s  (rc=`rc\')"' % name,
        "    local n_fail = `n_fail' + 1",
        "}",
        "",
    ]


def select_scripts(runner_src, scripts):
    """The committed runner, running only *scripts*, in the order given.

    A script the runner names keeps its own block verbatim -- its cd, its
    do line and the cleanup after it; one it does not name (a script not
    wired in yet) gets a generic block.  The setup before the first block
    and the summary after the last are kept.
    """
    lines = runner_src.split("\n")
    starts = []
    for i, line in enumerate(lines[:-1]):
        if line.strip() == _SEP:
            m = re.match(r"^// \d+\. (\S+\.cscript)", lines[i + 1])
            if m:
                starts.append((i, m.group(1)))
    summary = [i for i, l in enumerate(lines)
               if l.strip() == "// Summary" and i > 0
               and lines[i - 1].strip() == _SEP]
    if not starts or not summary:
        raise ValueError("runner: no numbered script blocks or no summary")
    end_all = summary[0] - 1
    blocks = {}
    for k, (i, name) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else end_all
        blocks[name] = lines[i:end]
    out = lines[:starts[0][0]]
    for s in scripts:
        if not _SCRIPT_NAME.match(s):
            raise ValueError("not a certification script name: %r" % s)
        out += blocks.get(s) or _generic_block(s)
    return "\n".join(out + lines[end_all:])


def runner_do(work, tree, runner_src, jsonio_dir=None):
    """The committed runner rewritten to run *tree*'s scripts with the
    recorder on the ado-path, marking each script and flushing after it."""
    lib = os.path.join(work, "lib")
    src = runner_src
    dash_line = re.compile(r'^adopath \+\+ "([^"]*)"\s*$', re.M)
    dirs = dash_line.findall(src)
    if len(dirs) < 2:
        raise ValueError("runner: expected the jsonio and dash adopath lines")
    for d in dirs:
        if os.path.isfile(os.path.join(d, "jsonio.ado")) or "StataJSON" in d:
            if jsonio_dir:
                src = src.replace('adopath ++ "%s"' % d,
                                  'adopath ++ "%s/"' % jsonio_dir.rstrip("/"))
        else:
            src = src.replace('adopath ++ "%s"' % d,
                              'adopath ++ "%s/"' % tree.rstrip("/"))
    src, n = re.subn(r'^local dashdir "[^"]*"\s*$',
                     'local dashdir "%s"' % tree.rstrip("/"), src, flags=re.M)
    if n != 1:
        raise ValueError("runner: expected one `local dashdir' line")
    setup = ('adopath ++ "%s/"\nmata: mata mlib index\n'
             'mata: _pc_mark("(runner setup)")\n' % lib)
    src = src.replace('cd "`dashdir\'"\n', 'cd "`dashdir\'"\n' + setup, 1)
    src, n = re.subn(r'^(display as text "\[ RUN \] ([^"]+)")\s*$',
                     lambda m: m.group(1) + '\nmata: _pc_mark("%s")' % m.group(2),
                     src, flags=re.M)
    if n == 0:
        raise ValueError("runner: no [ RUN ] lines found")
    src, n2 = re.subn(r"^local rc = _rc\s*$",
                      "local rc = _rc\nmata: _pc_flush()", src, flags=re.M)
    if n2 != n:
        raise ValueError("runner: %d scripts but %d rc captures" % (n, n2))
    return src, n


def prepare(work, repo=REPO, jsonio_dir=None, scripts=None):
    """Copy *repo* to WORK/tree, instrument it, and write the recorder's
    build file and the runner (every script, or only *scripts*)."""
    work = os.path.abspath(work)
    for s in scripts or ():
        if not _SCRIPT_NAME.match(s) or not os.path.isfile(
                os.path.join(repo, "test", s)):
            raise SystemExit("no such certification script: %s" % s)
    if os.path.commonpath([work, repo]) == repo:
        raise SystemExit("--work must be outside the repository")
    for p in (work,):
        if not _stata_path_ok(p):
            raise SystemExit("--work may not hold a quote, backtick or dollar")
    tree = os.path.join(work, "tree")
    if os.path.isdir(tree):
        shutil.rmtree(tree)
    shutil.copytree(repo, tree, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "*.pyc", ".claude"))
    os.makedirs(os.path.join(work, "lib"), exist_ok=True)
    os.makedirs(os.path.join(work, "stata_tmp"), exist_ok=True)
    counts = {}
    for f in ADO_FILES:
        p = os.path.join(tree, f)
        with open(p, encoding="utf-8") as fh:
            new, names, _bodies = instrument_ado(fh.read())
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(new)
        counts[f] = names
    for f in MATA_FILES:
        p = os.path.join(tree, f)
        with open(p, encoding="utf-8") as fh:
            new, names = instrument_mata(fh.read())
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(new)
        counts[f] = names
    # Every unit of the inventory must have been instrumented exactly once.
    for f, kind, name, _line in inventory(repo):
        if counts[f].get(name) != 1:
            raise SystemExit("not instrumented once: %s %s" % (f, name))
    with open(os.path.join(work, "build_recorder.do"), "w") as fh:
        fh.write(recorder_do(work))
    with open(os.path.join(repo, "test", "run_all_cscripts.do"),
              encoding="utf-8") as fh:
        src = fh.read()
    if scripts:
        src = select_scripts(src, scripts)
    runner, nscripts = runner_do(work, tree, src, jsonio_dir)
    with open(os.path.join(work, "run_measure.do"), "w") as fh:
        fh.write(runner)
    open(os.path.join(work, "hits.log"), "w").close()
    return tree, nscripts


def _stata(work, dofile):
    env = dict(os.environ)
    env["STATATMP"] = os.path.join(work, "stata_tmp") + "/"
    subprocess.run(STATA + [dofile], cwd=work, env=env, check=False)
    log = os.path.splitext(os.path.join(work, os.path.basename(dofile)))[0] + ".log"
    return log


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

def parse_hits(path):
    """``{unit: {"calls": n, "exact": bool, "scripts": {script: n}}}``."""
    per_script = {}      # script -> list of lifetimes (dict unit -> count)
    exact = {}           # script -> set of units whose last lifetime flushed
    script = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("== "):
                script = line[3:]
                per_script.setdefault(script, [{}])
                continue
            if script is None:
                continue
            lifetimes = per_script[script]
            if line == "## lifetime":
                if lifetimes[-1]:
                    lifetimes.append({})
                continue
            if line.startswith("##"):
                continue
            if line[:1] in "+=" and "\t" in line:
                unit, n = line[1:].rsplit("\t", 1)
                cur = lifetimes[-1]
                cur[unit] = max(cur.get(unit, 0), int(n))
                if line[0] == "=":
                    exact.setdefault(script, set()).add(unit)
    out = {}
    for s, lifetimes in per_script.items():
        for i, lt in enumerate(lifetimes):
            for unit, n in lt.items():
                d = out.setdefault(unit, {"calls": 0, "exact": True,
                                          "scripts": {}})
                d["calls"] += n
                d["scripts"][s] = d["scripts"].get(s, 0) + n
                if i < len(lifetimes) - 1 or unit not in exact.get(s, ()):
                    d["exact"] = False
    return out


def body_probed(repo=REPO):
    """``{(file, name)}`` for the ado programs that get a body probe."""
    out = set()
    for f in ADO_FILES:
        with open(os.path.join(repo, f), encoding="utf-8") as fh:
            _text, _names, bodies = instrument_ado(fh.read())
        out |= {(f, b) for b in bodies}
    return out


def report(work, repo=REPO, json_out=None):
    hits = parse_hits(os.path.join(work, "hits.log"))
    probed = body_probed(repo)
    rows = []
    for f, kind, name, line in inventory(repo):
        h = hits.get("%s:%s" % (kind, name))
        row = {"file": f, "kind": kind, "name": name, "line": line,
               "executed": h is not None,
               "calls": h["calls"] if h else 0,
               "exact": h["exact"] if h else True,
               "scripts": sorted(h["scripts"]) if h else []}
        if (f, name) in probed:
            b = hits.get("ado+:%s" % name)
            row["body_calls"] = b["calls"] if b else 0
            row["body_scripts"] = sorted(b["scripts"]) if b else []
        rows.append(row)
    if json_out:
        with open(json_out, "w") as fh:
            json.dump(rows, fh, indent=1)
    never = [r for r in rows if not r["executed"]]
    entered_only = [r for r in rows if r["executed"] and "body_calls" in r
                    and r["body_calls"] == 0]
    for r in rows:
        calls = ("%d" if r["exact"] else ">=%d") % r["calls"]
        body = ""
        if "body_calls" in r:
            body = "  body %s" % (r["body_calls"] or "NEVER")
        print("%-16s %-4s %-30s %6s  %9s  %2d script(s)%s" % (
            r["file"], r["kind"], r["name"], r["line"],
            calls if r["executed"] else "NEVER", len(r["scripts"]), body))
    by_kind = {}
    for r in rows:
        k = by_kind.setdefault(r["kind"], [0, 0])
        k[0] += 1
        k[1] += r["executed"]
    print()
    for k, (tot, ex) in sorted(by_kind.items()):
        print("%s: %d of %d executed" % (k, ex, tot))
    print("never executed: %s" % (", ".join(r["name"] for r in never) or "none"))
    print("entered, but refused before the body ran: %s" % (
        ", ".join(r["name"] for r in entered_only) or "none"))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=("units", "prepare", "run", "report"))
    ap.add_argument("--work", help="scratch directory outside the repository")
    ap.add_argument("--jsonio-dir", help="directory holding jsonio.ado "
                    "(default: the one test/run_all_cscripts.do names)")
    ap.add_argument("--json", help="also write the report as JSON here")
    ap.add_argument("--scripts", help="comma-separated certification "
                    "scripts to run instead of every one the runner names "
                    "(a script not in the runner yet may be named)")
    a = ap.parse_args(argv)
    if a.action == "units":
        for f, kind, name, line in inventory():
            print("%s\t%s\t%s\t%d" % (f, kind, name, line))
        return 0
    if not a.work:
        ap.error("--work is required")
    if a.action in ("prepare", "run"):
        scripts = [s.strip() for s in (a.scripts or "").split(",") if s.strip()]
        tree, n = prepare(a.work, jsonio_dir=a.jsonio_dir,
                          scripts=scripts or None)
        print("prepared %s (%d scripts)" % (tree, n))
    if a.action == "run":
        work = os.path.abspath(a.work)
        log = _stata(work, os.path.join(work, "build_recorder.do"))
        with open(log, encoding="utf-8", errors="replace") as fh:
            if re.search(r"^r\(\d+\);", fh.read(), re.M):
                raise SystemExit("building the recorder failed: see %s" % log)
        log = _stata(work, os.path.join(work, "run_measure.do"))
        print("runner log: %s" % log)
    if a.action in ("run", "report"):
        report(os.path.abspath(a.work), json_out=a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
