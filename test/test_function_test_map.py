"""Every function dash_render.py defines names the test that exercises it.

WP-24, AC-24.3, and CLAUDE.md rule 4: "Every function for every feature must
have a unit test."  ``test/function_test_map.py`` holds the names:

* ``FUNCTIONS`` maps every function to one pytest node id -- every ``def`` in
  dash_render.py at any depth (module-level functions, methods, functions
  nested in either), and every function the generated server app defines
  for itself (the template's ``make_document``, its callbacks, the rate
  limiter; keyed ``app:<qualname>``).  The app's other functions are copies
  of dash_render.py's, written by ``inspect.getsource``, and are the same
  entries.
* ``DEAD`` lists the functions nothing calls in either mode and no test
  runs, each with the evidence -- for WP-26 (dead code removal), not for a
  test.
* ``TEST_ONLY`` lists the functions only tests call: no code that runs in
  either mode reaches them.  Each has a test, so each is in ``FUNCTIONS``
  too; the list is WP-26's, which removes them or moves them to the tests.

This file keeps the map honest on every ordinary run, in a second or two:

* a function added to dash_render.py -- or to the app template -- without an
  entry fails ``test_every_function_has_an_entry``;
* an entry for a function that is gone fails ``test_no_entry_is_stale``;
* an entry naming a test file, class or function that does not exist fails
  ``test_every_named_test_exists``;
* a ``DEAD`` or ``TEST_ONLY`` function that code which runs in either mode
  has started to reach fails ``test_dead_and_test_only_stay_unreachable``:
  it needs a behavioural test (and a ``FUNCTIONS`` entry) now.

Whether each named test really executes its function is MEASURED, not
checked here: ``scripts/fncov/run_fncov.sh`` runs the whole suite under a
standard-library recorder and lists every function never executed;
``DASH_FNCOV_PER_TEST=1`` with ``scripts/fncov/fncov_report.py --check-map``
lists every entry whose test did not execute it; and
``scripts/fncov/fncov_mutate.py`` breaks each function and runs the tests
that execute it.
"""
import ast
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts", "fncov"))
sys.path.insert(0, _HERE)

import fncov_reach  # noqa: E402
import fncov_report as fr  # noqa: E402
from function_test_map import DEAD, FUNCTIONS, TEST_ONLY  # noqa: E402

_RENDER = os.path.join(_ROOT, "dash_render.py")
_NODE = re.compile(r"^test/(test_\w+\.py)::(\w+)(?:::(\w+))?$")


@pytest.fixture(scope="module")
def universe():
    """Every function key, dash_render.py's inventory, the template's
    functions, and the keys code that runs in either mode can reach."""
    render = fr.render_inventory(_RENDER)
    app_src = fr.sample_app_source()
    amap = fr.app_map(render, app_src)
    template = {fr.TEMPLATE + q for q, t in amap.items() if t is None}
    with open(_RENDER, encoding="utf-8") as fh:
        render_reach, _ = fncov_reach.reachable(ast.parse(fh.read()))
    app_reach, _ = fncov_reach.reachable(ast.parse(app_src))
    reach = set(render_reach)
    for q in app_reach:
        if q in amap:
            reach.add(amap[q] or fr.TEMPLATE + q)
    return {"everything": set(render) | template, "render": render,
            "template": template, "reach": reach}


def test_the_universe_is_the_whole_file(universe):
    """Guards the guard: a walk that found nothing would pass the rest."""
    everything, render = universe["everything"], universe["render"]
    kinds = {info["kind"] for info in render.values()}
    assert kinds == {"module", "method", "nested"}, kinds
    assert len(render) >= 400, len(render)
    assert len(universe["template"]) >= 30, sorted(universe["template"])
    for key in ("DashRenderer.render", "GlyphMapper.map_scatter",
                "ServerAppBuilder._generate_app_source",
                "_dash_build_hover.<locals>._cols_of",
                "app:make_document",
                "app:make_document.<locals>._make_filter_cb."
                "<locals>._on_filter_change",
                "app:_RateLimiter.is_allowed"):
        assert key in everything, key
    # A copy is not a template function: the app's GlyphMapper is
    # dash_render.py's, and so is the static method it writes as a plain
    # function.
    assert "app:GlyphMapper.map_scatter" not in everything
    assert "app:_histogram_grid" not in everything
    # And the call graph reaches what production obviously runs, so an
    # empty one cannot pass the unreachability check below.
    for key in ("main", "DashRenderer.render", "ServerAppBuilder.build",
                "app:make_document", "GlyphMapper.map_scatter"):
        assert key in universe["reach"], key


def test_every_function_has_an_entry(universe):
    missing = sorted(universe["everything"] - set(FUNCTIONS) - set(DEAD))
    assert not missing, (
        "%d function(s) in dash_render.py (or the app it generates) have no "
        "entry in test/function_test_map.py -- write a behavioural test for "
        "each and name it in FUNCTIONS (CLAUDE.md rule 4), or, if nothing "
        "calls it, list it in DEAD with the evidence:\n  %s"
        % (len(missing), "\n  ".join(missing)))


def test_no_entry_is_stale(universe):
    stale = sorted((set(FUNCTIONS) | set(DEAD) | set(TEST_ONLY))
                   - universe["everything"])
    assert not stale, (
        "test/function_test_map.py names function(s) dash_render.py no "
        "longer defines; remove or rename them:\n  %s" % "\n  ".join(stale))


def test_the_three_lists_agree():
    """DEAD has no test; TEST_ONLY has one, so it is in FUNCTIONS too."""
    assert not sorted(set(FUNCTIONS) & set(DEAD))
    assert not sorted(set(TEST_ONLY) - set(FUNCTIONS))
    assert not sorted(set(TEST_ONLY) & set(DEAD))
    for key, why in list(DEAD.items()) + list(TEST_ONLY.items()):
        assert "WP-26" in why and len(why) > 40, (
            "%s: say why, and for WP-26" % key)


_DEFS = {}


def _defs_of(rel):
    """{(class or None, function)} a test file defines, parsed once -- a
    class's methods including those it inherits from the file's own
    classes, as pytest collects them."""
    if rel not in _DEFS:
        path = os.path.join(_ROOT, rel)
        found = set()
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            own, bases = {}, {}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found.add((None, node.name))
                elif isinstance(node, ast.ClassDef):
                    own[node.name] = {
                        s.name for s in node.body
                        if isinstance(s, (ast.FunctionDef,
                                          ast.AsyncFunctionDef))}
                    bases[node.name] = [b.id for b in node.bases
                                        if isinstance(b, ast.Name)]

            def methods(cls, seen=()):
                if cls not in own or cls in seen:
                    return set()
                out = set(own[cls])
                for b in bases[cls]:
                    out |= methods(b, seen + (cls,))
                return out

            for cls in own:
                found |= {(cls, m) for m in methods(cls)}
        _DEFS[rel] = found
    return _DEFS[rel]


def test_every_named_test_exists():
    bad = []
    for key, node in sorted(FUNCTIONS.items()):
        m = _NODE.match(node)
        if not m:
            bad.append("%s: %r is not test/test_x.py::[Class::]test" % (
                key, node))
            continue
        rel = "test/" + m.group(1)
        cls, fn = (m.group(2), m.group(3)) if m.group(3) else (
            None, m.group(2))
        if not fn.startswith("test"):
            bad.append("%s: %s does not name a test function" % (key, node))
        elif (cls, fn) not in _defs_of(rel):
            bad.append("%s: %s does not exist" % (key, node))
    assert not bad, "\n".join(bad)


def test_dead_and_test_only_stay_unreachable(universe):
    """Nothing that runs in either mode -- dash_render.py's module code and
    ``main``, or a generated app's module code, ``make_document`` and its
    launcher -- reaches a DEAD or TEST_ONLY function, by a name-based call
    graph that can only err towards "reachable" (``fncov_reach.py``)."""
    revived = sorted((set(DEAD) | set(TEST_ONLY)) & universe["reach"])
    assert not revived, (
        "code that runs in either mode now reaches these; give each a "
        "behavioural test, name it in FUNCTIONS, and take it off DEAD or "
        "TEST_ONLY:\n  " + "\n  ".join(revived))
