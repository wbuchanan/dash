"""Which functions of dash_render.py can production code reach at all?

    python3 scripts/fncov/fncov_reach.py

The dead-code half of WP-24's function audit (for WP-26).  Static, over a
name-based call graph, from the only two places dash's code starts running:

* dash_render.py itself -- its module-level code, which includes the
  ``if __name__ == "__main__": main()`` block dash.ado runs through
  ``runpy.run_path(..., run_name="__main__")``;
* a generated server app (one is built here, as ``fncov_report`` builds it)
  -- its module-level code: ``make_document(curdoc())`` under ``bokeh
  serve``, and its own ``__main__`` launcher.

A reference to a name -- ``foo(...)``, ``x.foo``, ``foo`` passed as a
callback -- reaches EVERY function of that short name, and referencing a
class reaches its dunder methods (and all its methods, if it subclasses
something outside the file: Tornado calls a handler's ``get`` and a
transform's ``transform_first_chunk`` by protocol).  So the graph can only
err towards "reachable": a function it reports unreachable is referenced by
no code that runs in either mode.  Tests are not roots: a function only a
test calls is reported, with the tests that name it.
"""
import ast
import glob
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import fncov_report as fr  # noqa: E402


def _refs(nodes):
    """Names referenced by *nodes*, not descending into nested defs."""
    out = set()
    stack = list(nodes)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # A nested def is its own node; its decorators and defaults
            # run here, its body does not.
            stack.extend(n.decorator_list)
            stack.extend(n.args.defaults + n.args.kw_defaults)
            continue
        if isinstance(n, ast.ClassDef):
            stack.extend(n.decorator_list + n.bases)
            stack.extend(s for s in n.body if not isinstance(
                s, (ast.FunctionDef, ast.AsyncFunctionDef)))
            continue
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        stack.extend(x for x in ast.iter_child_nodes(n) if x is not None)
    return out


def graph(tree):
    """(functions {qualname: (short name, refs, class or None)},
    classes {qualname: (short name, external base?)}, root refs)."""
    funcs, classes = {}, {}
    local_classes = {n.name for n in ast.walk(tree)
                     if isinstance(n, ast.ClassDef)}

    def walk(node, prefix, cls):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = prefix + child.name
                funcs[q] = (child.name, _refs(child.body), cls)
                walk(child, q + ".<locals>.", None)
            elif isinstance(child, ast.ClassDef):
                q = prefix + child.name
                ext = any(not (isinstance(b, ast.Name)
                               and b.id in local_classes)
                          for b in child.bases)
                classes[q] = (child.name, ext)
                walk(child, q + ".", q)
            else:
                walk(child, prefix, cls)

    walk(tree, "", None)
    roots = _refs(tree.body)
    return funcs, classes, roots


def reachable(tree):
    """The qualnames of *tree* reachable from its module-level code."""
    funcs, classes, roots = graph(tree)
    by_name = {}
    for q, (short, _r, _c) in funcs.items():
        by_name.setdefault(short, []).append(q)
    cls_by_name = {}
    for q, (short, ext) in classes.items():
        cls_by_name.setdefault(short, []).append(q)
    seen, todo, done = set(), list(roots), set()
    while todo:
        name = todo.pop()
        if name in done:
            continue
        done.add(name)
        hits = list(by_name.get(name, ()))
        for cq in cls_by_name.get(name, ()):
            ext = classes[cq][1]
            for q, (short, _r, c) in funcs.items():
                if c == cq and (ext or (short.startswith("__")
                                        and short.endswith("__"))):
                    hits.append(q)
        for q in hits:
            if q not in seen:
                seen.add(q)
                todo.extend(funcs[q][1])
                todo.append(funcs[q][0])
    return seen, funcs


def analyse(render_path=fr._RENDER):
    with open(render_path, encoding="utf-8") as fh:
        rsrc = fh.read()
    render_reach, render_funcs = reachable(ast.parse(rsrc))
    app_src = fr.sample_app_source()
    app_reach, app_funcs = reachable(ast.parse(app_src))
    inv = fr.render_inventory(render_path)
    amap = fr.app_map(inv, app_src)
    served = {amap[q] for q in app_reach if amap.get(q)}
    template = {q for q, t in amap.items() if t is None}
    dead = sorted(q for q in inv if q not in render_reach
                  and q not in served)
    dead_tmpl = sorted(q for q in template if q not in app_reach)
    return dead, dead_tmpl


def _named_by_tests(name, root=fr._ROOT):
    out = []
    pat = re.compile(r"\b%s\b" % re.escape(name))
    for p in sorted(glob.glob(os.path.join(root, "test", "*.py"))):
        with open(p, encoding="utf-8", errors="replace") as fh:
            n = len(pat.findall(fh.read()))
        if n:
            out.append("%s (%d)" % (os.path.relpath(p, root), n))
    return out


def main():
    dead, dead_tmpl = analyse()
    print("dash_render.py functions no production code reaches: %d"
          % len(dead))
    for q in dead:
        tests = _named_by_tests(q.rsplit(".", 1)[-1])
        print("  %s%s" % (q, ("   -- named by " + ", ".join(tests))
                          if tests else "   -- named by no test"))
    print("app template functions nothing in the app reaches: %d"
          % len(dead_tmpl))
    for q in dead_tmpl:
        print("  app:%s" % q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
