"""Merge dash_fncov_recorder's per-process files into a function-coverage
report for dash_render.py and the server app it generates.

    python3 scripts/fncov/fncov_report.py OUTDIR [--json REPORT.json]

Run by ``scripts/fncov/run_fncov.sh`` after the suite; read that file
first.  Standard library, plus dash_render itself (imported from the
repository root) to generate one sample app.

The universe is every ``def`` in dash_render.py -- module-level functions,
methods, and functions nested in either -- and every function the generated
app defines that is not a copy of one of those: the template's own
(``make_document``, ``make_document.<locals>._on_filter_change``,
``_RateLimiter.is_allowed``, ...).

The app's copies are mapped back to dash_render.py by comparing source:
``ServerAppBuilder`` writes them with ``inspect.getsource``, so a copied
function's text in the app equals its text in dash_render.py, except for the
five static methods written as module-level functions with ``GlyphMapper._``
and ``DashRenderer._`` stripped (``_histogram_grid`` is
``GlyphMapper._histogram_grid``).  A function nested in a copy is a copy of
the function nested in the original.

A dash_render.py function counts as executed if a process ran it from
dash_render.py (the saved-dashboard path, the CLI, the builder) or ran its
copy from a generated app (the served path); the report says which.
"""
import argparse
import ast
import glob
import json
import os
import sys
import tempfile
import textwrap

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
_RENDER = os.path.join(_ROOT, "dash_render.py")

#: A qualname that only a generated app defines.
_APP_MARKERS = ("_dash_build_scheme", "make_document")


def walk_defs(tree):
    """Yield (qualname, node) for every def in *tree*, in co_qualname form."""
    def _walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = prefix + child.name
                yield q, child
                yield from _walk(child, q + ".<locals>.")
            elif isinstance(child, ast.ClassDef):
                yield from _walk(child, prefix + child.name + ".")
            else:
                yield from _walk(child, prefix)
    yield from _walk(tree, "")


def kind_of(qualname):
    """"module", "method" or "nested" for a dash_render.py qualname."""
    if "<locals>" in qualname:
        return "nested"
    return "method" if "." in qualname else "module"


def segment(lines, node):
    """A def's own lines (``ast.get_source_segment`` is quadratic here)."""
    return textwrap.dedent("\n".join(lines[node.lineno - 1:node.end_lineno]))


def render_inventory(path=_RENDER):
    """{qualname: {"line", "end", "kind", "src"}} for dash_render.py."""
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    lines = src.splitlines()
    out = {}
    for q, node in walk_defs(ast.parse(src)):
        out[q] = {"line": node.lineno, "end": node.end_lineno,
                  "kind": kind_of(q), "src": segment(lines, node)}
    return out


def _norm(text):
    return textwrap.dedent(text).replace("GlyphMapper._", "_") \
        .replace("DashRenderer._", "_").strip()


def sample_app_source():
    """The source of one generated app (a scatter with a filter and a KPI).

    Which template functions an app defines does not depend on the spec:
    ``_generate_app_source`` writes every one of them unconditionally.
    """
    with tempfile.TemporaryDirectory(prefix="fncov_app_") as tmp:
        return _sample_app_source(tmp)


def _sample_app_source(tmp):
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    import warnings
    import dash_render as dr
    spec = {"graphs": [{"plots": [{"type": "scatter", "yvar": "y",
                                   "xvar": "x", "options": ""}],
                        "graph_options": {"name": "g1"},
                        "if_expr": "", "in_expr": ""}],
            "kpis": [{"name": "k1", "varname": "y", "stat": "mean",
                      "label": "Mean"}],
            "build_options": {"layout": "auto", "link": "", "title": "t",
                              "filters": [{"varname": "x",
                                           "type": "range"}]}}
    data = {"StataJSON": {"variableNames": ["y", "x"],
                          "variableLabels": {}, "valueLabels": {},
                          "valueLabelNames": {},
                          "variableIsString": {"y": False, "x": False},
                          "values": [{"y": float(i), "x": float(i % 3)}
                                     for i in range(6)]}}
    sp, dp, ap = (os.path.join(tmp, n)
                  for n in ("spec.json", "data.json", "app.py"))
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(data, fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        return fh.read()


def app_map(render, app_src):
    """{app qualname: dash_render qualname, or None for a template function}.

    Also returns the set of dash_render qualnames the app carries a copy of.
    """
    tree = ast.parse(app_src)
    app_lines = app_src.splitlines()
    out = {}
    by_norm = {}
    for q, info in render.items():
        by_norm.setdefault(_norm(info["src"]), []).append(q)
    for q, node in walk_defs(tree):
        if "<locals>" in q:
            continue                          # resolved from the parent
        seg = _norm(segment(app_lines, node))
        hits = by_norm.get(seg, [])
        # Prefer the same qualname, then the one static-method rename.
        exact = [h for h in hits if h == q]
        renamed = [h for h in hits if h.rsplit(".", 1)[-1] == q]
        target = (exact or renamed or [None])[0]
        out[q] = target
    # Nested functions: a copy's children are the original's children.
    for q, node in walk_defs(tree):
        if "<locals>" not in q:
            continue
        top = q.split(".<locals>.")[0]
        parent = out.get(top)
        out[q] = (parent + q[len(top):]) if parent else None
    return out


def iter_records(outdir, headers=None):
    """Yield (process_file, kind, filename, qualname, test) from every file.

    *test* is the node id of the test that ran it, or None when the run was
    not per-test (or the code ran outside any test, e.g. at collection).
    Streamed: a per-test run writes hundreds of megabytes.  Each file's
    header line is appended to *headers* if given.
    """
    for path in sorted(glob.glob(os.path.join(outdir, "fncov-*.jsonl"))):
        files, tests = {}, {}     # this file's ["F", n, name] / ["T", n, id]
        with open(path, encoding="utf-8") as fh:
            first = True
            for ln in fh:
                if first:
                    first = False
                    if headers is not None:
                        try:
                            headers.append(json.loads(ln))
                        except ValueError:
                            headers.append({})
                    continue
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue                  # a line cut by a kill
                if not isinstance(r, list) or len(r) < 3:
                    continue
                if r[0] == "F":
                    files[r[1]] = r[2]
                    continue
                if r[0] == "T":
                    tests[r[1]] = r[2]
                    continue
                if len(r) < 4:
                    continue
                fn = files.get(r[1], "") if isinstance(r[1], int) else r[1]
                t = r[4] if len(r) > 4 else None
                if isinstance(t, int):
                    t = tests.get(t)
                yield (path, r[0], fn, r[2], t)


#: A template function is keyed apart from dash_render.py's own.
TEMPLATE = "app:"


def analyse(outdir, render_path=_RENDER, exclude=()):
    """The report as a dict; ``tests_of`` maps each function to its tests.

    *exclude*: substrings of node ids whose records are left out -- in a
    per-test run, the coverage the suite had without those tests.
    """
    render = render_inventory(render_path)
    amap = app_map(render, sample_app_source())
    template = sorted(q for q, t in amap.items() if t is None)
    copied = sorted({t for t in amap.values() if t})

    procs = []
    apps = set()
    for path, k, fn, q, _t in iter_records(outdir, procs):
        if k in ("A", "M") and q in _APP_MARKERS:
            apps.add(fn if k == "A" else (path, fn))

    direct, served, tmpl_run = set(), set(), set()
    tests_of = {}
    not_by_tests = set()      # keys a non-test caller called (CALLERS=1)
    callers_run = False
    for path, k, fn, q, test in iter_records(outdir):
        if test and exclude and any(x in test for x in exclude):
            continue
        if k[:1] == "C":
            callers_run = True
            k = k[1:]
            if k == "R":
                if q in render:
                    not_by_tests.add(q)
                continue
            gkey = fn if k == "A" else (path, fn)
            if gkey in apps and q in amap:
                not_by_tests.add(amap[q] or TEMPLATE + q)
            elif gkey in apps and q in render:
                not_by_tests.add(q)
            continue
        if k == "R":
            if q not in render:
                continue
            direct.add(q)
            key = q
        else:
            gkey = fn if k == "A" else (path, fn)
            if gkey not in apps:
                continue
            if q in amap:
                t = amap[q]
                if t is None:
                    tmpl_run.add(q)
                    key = TEMPLATE + q
                else:
                    served.add(t)
                    key = t
            elif q in render:                 # a copy the sample lacks
                served.add(q)
                key = q
            else:
                continue
        if test:
            tests_of.setdefault(key, set()).add(test)

    run = direct | served
    never = sorted(q for q in render if q not in run)
    counts = {}
    for q, info in render.items():
        c = counts.setdefault(info["kind"], {"total": 0, "never": 0})
        c["total"] += 1
        c["never"] += q not in run
    counts["template"] = {"total": len(template),
                          "never": sum(q not in tmpl_run for q in template)}
    return {
        "processes": len(procs),
        "app_sources": len(apps),
        "counts": counts,
        "never_executed": [
            {"qualname": q, "line": render[q]["line"],
             "kind": render[q]["kind"]} for q in never],
        "template_never_executed": [q for q in template
                                    if q not in tmpl_run],
        "copied": copied,
        "copied_never_served": [q for q in copied if q not in served],
        "copied_served_only": sorted(served - direct),
        "template_functions": template,
        "executed_direct": sorted(direct),
        "executed_served": sorted(served),
        "tests_of": {k: sorted(v) for k, v in sorted(tests_of.items())},
        # With DASH_FNCOV_CALLERS=1: executed, but only ever called
        # directly by a test -- no dash code, app or library called it.
        "called_only_by_tests": (sorted(
            [q for q in run if q not in not_by_tests]
            + [TEMPLATE + q for q in tmpl_run
               if TEMPLATE + q not in not_by_tests])
            if callers_run else None),
    }


def plain_nodeid(nodeid):
    """*nodeid* relative to the repository, whatever directory pytest took
    as its rootdir (a git worktree inside another checkout gets that
    checkout's), and without the ``@group`` pytest-xdist's ``--dist
    loadgroup`` appends -- a plain run does not know that name."""
    import re
    nodeid = re.sub(r"@[^@\[\]]*$", "", nodeid)
    i = nodeid.find("test/test_")
    return nodeid[i:] if i > 0 else nodeid


def base_nodeid(nodeid):
    """``test/test_x.py::T::t``: :func:`plain_nodeid` without its
    parametrization."""
    return plain_nodeid(nodeid).split("[", 1)[0]


def _test_texts(root=_ROOT):
    """{base node id: the test function's source} for every test file."""
    out = {}
    for path in glob.glob(os.path.join(root, "test", "test_*.py")):
        rel = os.path.relpath(path, root)
        try:
            with open(path, encoding="utf-8") as fh:
                src = fh.read()
            tree = ast.parse(src)
        except (OSError, SyntaxError, ValueError):
            continue
        lines = src.splitlines()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[rel + "::" + node.name] = segment(lines, node)
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef,
                                        ast.AsyncFunctionDef)):
                        out["%s::%s::%s" % (rel, node.name, sub.name)] = \
                            segment(lines, sub)
    return out


def suggest_map(rep, root=_ROOT):
    """{function key: base node id} -- the most focused test that ran it.

    Preference: a test whose own source names the function, then the test
    that ran the fewest dash functions (the most unit-like), then the node
    id.  A suggestion only: the committed map is reviewed by hand.
    """
    import re
    texts = _test_texts(root)
    width = {}
    for key, tests in rep["tests_of"].items():
        for t in tests:
            width[t] = width.get(t, 0) + 1
    out = {}
    for key, tests in rep["tests_of"].items():
        name = key.rsplit(".", 1)[-1].replace(TEMPLATE, "")
        pat = re.compile(r"\b%s\b" % re.escape(name))
        best = sorted(tests, key=lambda t: (
            not pat.search(texts.get(base_nodeid(t), "")),
            width.get(t, 0), t))
        if best:
            out[key] = base_nodeid(best[0])
    return out


def load_map(path=os.path.join(_ROOT, "test", "function_test_map.py")):
    """(FUNCTIONS, DEAD) from the committed map."""
    import runpy
    ns = runpy.run_path(path)
    return ns["FUNCTIONS"], ns["DEAD"]


def check_map(rep, functions):
    """Entries whose named test did not execute their function, in a
    per-test run: [(key, named test, how many tests did run it)]."""
    out = []
    for key, node in sorted(functions.items()):
        ran = {base_nodeid(t) for t in rep["tests_of"].get(key, ())}
        if node not in ran:
            out.append((key, node, len(ran)))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("outdir")
    ap.add_argument("--json", help="write the whole report here")
    ap.add_argument("--render", default=_RENDER)
    ap.add_argument("--suggest-map", metavar="FILE",
                    help="write {function: most focused test} here (needs "
                         "a DASH_FNCOV_PER_TEST=1 run)")
    ap.add_argument("--check-map", action="store_true",
                    help="list every test/function_test_map.py entry whose "
                         "test did not execute its function (needs a "
                         "DASH_FNCOV_PER_TEST=1 run)")
    ap.add_argument("--exclude-tests", action="append", default=[],
                    metavar="TEXT",
                    help="leave out the records of every test whose node id "
                         "contains TEXT (repeatable; needs a "
                         "DASH_FNCOV_PER_TEST=1 run) -- the coverage the "
                         "suite had without them")
    a = ap.parse_args(argv)
    rep = analyse(a.outdir, a.render, tuple(a.exclude_tests))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1)
    if a.suggest_map:
        with open(a.suggest_map, "w", encoding="utf-8") as fh:
            json.dump(suggest_map(rep), fh, indent=1, sort_keys=True)
    if a.check_map:
        functions, _dead = load_map()
        wrong = check_map(rep, functions)
        print("map entries whose test did not execute the function: %d of %d"
              % (len(wrong), len(functions)))
        for key, node, n in wrong:
            print("  %s -> %s (%d other tests did)" % (key, node, n))
    print("processes recorded: %d; generated app sources seen: %d"
          % (rep["processes"], rep["app_sources"]))
    for k, c in sorted(rep["counts"].items()):
        print("  %-9s %4d functions, %4d never executed"
              % (k, c["total"], c["never"]))
    print("\ndash_render.py functions never executed (%d):"
          % len(rep["never_executed"]))
    for r in rep["never_executed"]:
        print("  %6d  %-7s %s" % (r["line"], r["kind"], r["qualname"]))
    print("\napp template functions never executed (%d):"
          % len(rep["template_never_executed"]))
    for q in rep["template_never_executed"]:
        print("          %s" % q)
    print("\ncopied into the app and never run there: %d of %d"
          % (len(rep["copied_never_served"]), len(rep["copied"])))
    for q in rep["copied_never_served"]:
        print("          %s" % q)
    if rep["called_only_by_tests"] is not None:
        print("\nexecuted, but only ever called directly by a test (%d):"
              % len(rep["called_only_by_tests"]))
        for q in rep["called_only_by_tests"]:
            print("          %s" % q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
