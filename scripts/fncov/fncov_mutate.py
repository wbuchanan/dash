"""Does any test notice when a function of dash_render.py stops working?

    python3 scripts/fncov/fncov_mutate.py REPORT.json [--keys K,K | --all]
        [--lanes N] [--cap N] [--out RESULTS.json]
    python3 scripts/fncov/fncov_mutate.py --map [--keys ...] ...

With ``--map`` the tests are not a report's: each function's is the one
test/function_test_map.py names for it, so the question becomes "does the
map's own test fail when its function breaks?".

WP-24's second question after "was it executed?" (``fncov_report.py``):
"would an assertion fail if it broke?" -- AC-24.1 at function granularity.
Slow and not run by default: one pytest run per function.

For each function (a dash_render.py qualname, or ``app:<qualname>`` for a
function of the server app's template) it writes a mutant of dash_render.py
whose function returns None before its first statement -- the body skipped,
so its value and every effect it has are gone -- into a scratch copy of the
repository, and runs the tests that executed that function (REPORT.json is
``fncov_report.py --json`` over a ``DASH_FNCOV_PER_TEST=1`` run), the most
focused first, stopping at the first failure.

* ``killed``    a test failed: something checks the function;
* ``survived``  every test that runs it passed with its body skipped: it is
  executed only incidentally, with no assertion that would fail if it
  broke -- it needs a behavioural test (or it is a no-op);
* ``error``     the mutant or the run could not be made (reported).

A template mutant is checked before it is run: an app is generated from the
mutated module and the function's first statement must be the inserted
``return None``, so a mutation that broke the whole template cannot pass as
``killed``.
"""
import argparse
import ast
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import fncov_report as fr  # noqa: E402

MUTANT = "return None  # fncov mutant"


def _nodeid(t):
    """``test/test_x.py::T::t[p]`` relative to the repository, params kept."""
    return fr.plain_nodeid(t)


# ---------------------------------------------------------------------------
# Mutants
# ---------------------------------------------------------------------------

def mutate_render(src, key):
    """*src* with the dash_render.py function *key* returning at once."""
    tree = ast.parse(src)
    node = dict(fr.walk_defs(tree)).get(key)
    if node is None:
        raise KeyError("no function %s" % key)
    body = node.body
    first = body[0]
    doc = (isinstance(first, ast.Expr) and isinstance(
        getattr(first, "value", None), ast.Constant)
        and isinstance(first.value.value, str))
    if first.lineno == node.lineno:
        raise ValueError("one-line def")
    lines = src.split("\n")
    if doc and len(body) > 1:
        at, col = body[1].lineno, body[1].col_offset
    elif doc:
        at, col = first.end_lineno + 1, first.col_offset
    else:
        at, col = first.lineno, first.col_offset
    if body[-1] is first and doc:
        raise ValueError("docstring-only body")
    lines.insert(at - 1, " " * col + MUTANT)
    out = "\n".join(lines)
    ast.parse(out)
    return out


def _template_methods(src):
    """For each ServerAppBuilder method, the string elements of its lists
    in source order: [[(lineno, end_lineno, value)], ...].  Each method's
    block of emitted lines starts at the app's top level."""
    tree = ast.parse(src)
    out = []
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef) and cls.name == "ServerAppBuilder":
            for meth in cls.body:
                if not isinstance(meth, ast.FunctionDef):
                    continue
                elems = []
                for n in ast.walk(meth):
                    if isinstance(n, ast.List):
                        for e in n.elts:
                            if (isinstance(e, ast.Constant)
                                    and isinstance(e.value, str)):
                                elems.append((e.lineno, e.end_lineno,
                                              e.value))
                out.append(sorted(elems))
    return out


_DEF = re.compile(r"^(\s*)(def|class)\s+(\w+)")


def mutate_template(src, key):
    """*src* with the app template's function *key* (``app:...``) returning
    at once: a ``return None`` element inserted after its signature."""
    want = key[len(fr.TEMPLATE):]
    for elems in _template_methods(src):
        out = _mutate_in(src, elems, want)
        if out is not None:
            return out
    raise KeyError("no template function %s" % key)


def _mutate_in(src, elems, want):
    stack = []                        # [(indent, name, "def" | "class")]
    for i, (ln, end, val) in enumerate(elems):
        m = _DEF.match(val)
        if not m:
            # Any code line closes the blocks it is not indented into.
            for text in val.split("\n"):
                body = text.strip()
                if body and not body.startswith("#"):
                    ind = len(text) - len(text.lstrip())
                    while stack and stack[-1][0] >= ind:
                        stack.pop()
                    break
            continue
        ind = len(m.group(1))
        while stack and stack[-1][0] >= ind:
            stack.pop()
        prefix = ""
        for _ind, part, kind in stack:
            prefix += part + (".<locals>." if kind == "def" else ".")
        q = prefix + m.group(3)
        stack.append((ind, m.group(3), m.group(2)))
        if q != want or m.group(2) != "def":
            continue
        j = i
        while not elems[j][2].rstrip().endswith(":"):
            j += 1
        lines = src.split("\n")
        at = elems[j][1]                      # after the element's last line
        pad = re.match(r"\s*", lines[elems[j][0] - 1]).group(0)
        lines.insert(at, "%s%r," % (pad, " " * (ind + 4) + MUTANT))
        out = "\n".join(lines)
        ast.parse(out)
        return out
    return None


_CHECK = textwrap.dedent('''
    import ast, sys
    sys.path.insert(0, sys.argv[1])
    import dash_render                  # the lane's mutant, cached first
    sys.path.append(sys.argv[2])
    import fncov_report as fr
    assert dash_render.__file__.startswith(sys.argv[1]), dash_render.__file__
    src = fr.sample_app_source()
    compile(src, "app", "exec")
    tree = ast.parse(src)
    node = dict(fr.walk_defs(tree))[sys.argv[3]]
    first = node.body[0]
    if not (isinstance(first, ast.Return) and first.value is not None
            and isinstance(first.value, ast.Constant)
            and first.value.value is None):
        # A docstring may come first in the template; the mutant follows it.
        second = node.body[1] if len(node.body) > 1 else None
        ok = (isinstance(first, ast.Expr) and isinstance(second, ast.Return))
        if not ok:
            raise SystemExit("mutant not first")
    print("ok")
''')


def check_template_mutant(lane, key):
    """Generate an app from the lane's mutated module; is the mutant there?"""
    p = subprocess.run(
        [sys.executable, "-c", _CHECK, lane, _HERE, key[len(fr.TEMPLATE):]],
        capture_output=True, text=True, timeout=300)
    return p.returncode == 0 and p.stdout.strip() == "ok", p.stderr[-800:]


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------

def make_lane(root, dest):
    """A scratch copy of the repository (no .git, no caches)."""
    shutil.copytree(root, dest, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", ".pytest_cache", "*.pyc", ".claude"))
    return dest


def order_tests(key, tests, texts, width):
    name = key.replace(fr.TEMPLATE, "").rsplit(".", 1)[-1]
    pat = re.compile(r"\b%s\b" % re.escape(name))
    return sorted({_nodeid(t) for t in tests}, key=lambda t: (
        not pat.search(texts.get(fr.base_nodeid(t), "")),
        width.get(t, 0), t))


def run_one(lane, pristine, key, tests, timeout, workers=0):
    try:
        src = (mutate_template(pristine, key) if key.startswith(fr.TEMPLATE)
               else mutate_render(pristine, key))
    except (KeyError, ValueError, SyntaxError) as e:
        return {"key": key, "status": "error", "why": "mutant: %s" % e}
    target = os.path.join(lane, "dash_render.py")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(src)
    try:
        if key.startswith(fr.TEMPLATE):
            ok, err = check_template_mutant(lane, key)
            if not ok:
                return {"key": key, "status": "error",
                        "why": "template mutant not verified: " + err}
        # In stages, most focused first: a mutant most tests notice dies in
        # the first few, without collecting every file the rest live in.
        ran = 0
        for n, stage in enumerate((tests[:4], tests[4:40], tests[40:])):
            if not stage:
                continue
            argfile = os.path.join(lane, "fncov_args.txt")
            with open(argfile, "w", encoding="utf-8") as fh:
                fh.write("\n".join(stage))
            whole_files = any("::" not in t for t in stage)
            par = ("-n%d" % workers) if (workers and (
                len(stage) > 200 or whole_files)) else "-n0"
            # The node ids are in the argument file, so nothing on the
            # command line says this is not the whole suite -- and the
            # project's full-suite guard (.claude/hooks/guard-full-suite.sh)
            # reads command lines, and would refuse every other session's
            # full run while a lane runs.  A --deselect of a node that does
            # not exist changes nothing and marks the run as narrowed.
            cmd = [sys.executable, "-m", "pytest", "-q", "-x", par,
                   "-p", "no:cacheprovider", "-p", "no:randomly",
                   "--deselect", "test/test_fncov_lane.py::not_the_suite",
                   "--tb=line", "-W", "ignore", "@" + argfile]
            try:
                p = subprocess.run(cmd, cwd=lane, capture_output=True,
                                   text=True, timeout=timeout)
            except subprocess.TimeoutExpired:
                return {"key": key, "status": "timeout", "tests": len(tests),
                        "ran": ran}
            ran += len(stage)
            tail = (p.stdout or "").strip().splitlines()[-3:]
            if p.returncode != 0:
                # pytest-xdist stopped by -x exits 2 ("interrupted") after
                # a failure; a plain run exits 1.  A mutant that breaks a
                # test module's import (a parametrization built from the
                # function) ends in "N errors": the suite is red, so that
                # is caught too -- "no tests ran" is a usage error.
                failed = any(re.search(r"\b\d+ failed\b", t) for t in tail)
                errors = any(re.search(r"\b\d+ errors?\b", t) for t in tail)
                # A function dash_render.py calls at import (a module-level
                # constant built by it) breaks the import itself: pytest
                # cannot load conftest.py and exits 4 -- every test is red.
                imported = "ImportError while loading conftest" in (
                    p.stderr or "")
                status = ("killed" if p.returncode == 1 or failed
                          else "killed (collection error)" if errors
                          else "killed (import error)" if imported
                          else "error")
                # The test that noticed: the summary's first FAILED line,
                # or an ERROR in a test's own setup (a fixture that builds
                # the broken object).
                killer = next((m.group(1) for m in (
                    re.match(r"(?:FAILED|ERROR) (test/\S+::\S+)", ln)
                    for ln in (p.stdout or "").splitlines()) if m), None)
                return {"key": key, "status": status, "rc": p.returncode,
                        "tests": len(tests), "ran": ran, "tail": tail,
                        "killer": killer}
        return {"key": key, "status": "survived", "rc": 0,
                "tests": len(tests), "ran": ran, "tail": tail}
    finally:
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(pristine)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("report", nargs="?")
    ap.add_argument("--map", action="store_true",
                    help="run each function's test/function_test_map.py test")
    ap.add_argument("--keys", default="",
                    help="comma-separated function keys, or @FILE holding "
                         "them")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--lanes", type=int, default=4)
    ap.add_argument("--cap", type=int, default=400,
                    help="run at most this many of a function's tests "
                         "(0: all of them)")
    ap.add_argument("--workers", type=int, default=0,
                    help="pytest-xdist workers for a stage of more than 200 "
                         "tests or of whole test files (0: one process)")
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument("--scratch", default=None)
    ap.add_argument("--out", default="fncov_mutants.json")
    a = ap.parse_args(argv)
    if a.map:
        functions, _dead = fr.load_map()
        tests_of = {k: [v] for k, v in functions.items()}
    else:
        if not a.report:
            ap.error("give REPORT.json or --map")
        with open(a.report, encoding="utf-8") as fh:
            tests_of = json.load(fh)["tests_of"]
    spec = a.keys
    if spec.startswith("@"):
        with open(spec[1:], encoding="utf-8") as fh:
            spec = fh.read().strip()
    keys = (sorted(tests_of) if a.all else
            [k for k in spec.split(",") if k])
    texts = fr._test_texts()
    width = {}
    for k, ts in tests_of.items():
        for t in ts:
            width[_nodeid(t)] = width.get(_nodeid(t), 0) + 1
    with open(fr._RENDER, encoding="utf-8") as fh:
        pristine = fh.read()
    scratch = a.scratch or tempfile.mkdtemp(prefix="fncov_mut_")
    lanes = [make_lane(fr._ROOT, os.path.join(scratch, "lane%d" % i))
             if not os.path.isdir(os.path.join(scratch, "lane%d" % i))
             else os.path.join(scratch, "lane%d" % i)
             for i in range(a.lanes)]
    free = list(lanes)
    results = []
    jobs = []
    for k in keys:
        ts = order_tests(k, tests_of.get(k, []), texts, width)
        if a.cap:
            ts = ts[:a.cap]
        if not ts:
            results.append({"key": k, "status": "error",
                            "why": "no test executed it"})
            continue
        jobs.append((k, ts))
    import threading
    lock = threading.Lock()

    def _work(job):
        with lock:
            lane = free.pop()
        try:
            return run_one(lane, pristine, job[0], job[1], a.timeout,
                           a.workers)
        finally:
            with lock:
                free.append(lane)

    with cf.ThreadPoolExecutor(max_workers=len(lanes)) as ex:
        for r in ex.map(_work, jobs):
            results.append(r)
            print("%-9s %s (%s tests)" % (r["status"], r["key"],
                                          r.get("tests", "-")), flush=True)
            with open(a.out, "w", encoding="utf-8") as fh:
                json.dump(results, fh, indent=1)
    surv = [r["key"] for r in results if r["status"] == "survived"]
    killed = sum(r["status"].startswith("killed") for r in results)
    print("\n%d functions: %d killed, %d survived, %d other"
          % (len(results), killed, len(surv),
             len(results) - killed - len(surv)))
    for k in surv:
        print("  survived: %s" % k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
