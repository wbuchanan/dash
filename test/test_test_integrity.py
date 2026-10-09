"""test_test_integrity.py -- a green suite must mean the code works.

WP-24 (GAPS.md L5, ROADMAP.md AC-24.2) found tests that could not fail:

* ``test_filter_label.py``'s injection test wrapped the render in
  ``except Exception: return`` -- "rejected outright is also a correct
  outcome" -- so any exception at all, a crash included, was green;
* ``test_options.py`` caught ``(ValueError, AssertionError)`` around its own
  assertion, so it passed by construction;
* ``test_filters.py`` ran its assertion inside ``try`` and answered a
  ``ValueError`` or ``KeyError`` with ``pass``, so a refusal it never looked
  at counted as a pass;
* twenty-three test functions verified nothing at all -- among them a
  resource-exhaustion test, "a power tower does not hang the served app",
  with no assertion and no timeout.

Each was a review finding; nothing stopped the next one.  Run against the
suite as it stood (a2c7502), this file found all twenty-six and four more of
the same kind -- thirty -- and every one was fixed rather than excused.  It
reads the syntax tree of every test file and fails on six shapes:

1. **A handler that catches ``AssertionError`` and neither re-raises nor
   fails the test** -- by name, or through a bare ``except:``,
   ``except Exception:`` or ``except BaseException:`` wrapped around code
   that asserts (an ``AssertionError`` *is* an ``Exception``).  Anywhere in a
   test file, helpers included: a helper that swallows its own failure makes
   every caller unable to fail.
2. **Inside a test function, a bare / ``Exception`` / ``BaseException``
   handler that returns, passes or continues** -- the test ends green, or
   carries on as if the subject had worked, whatever went wrong -- **or that
   keeps the exception in a test that then returns early**, which is the
   same green ending one statement later (``test_scheme_fidelity.py`` had
   ``except Exception as exc: raised = exc`` ... ``if raised: return``).
3. **Inside a test function, a handler that answers an exception from a
   ``try`` holding the test's assertions with no assertion of its own** --
   a refusal accepted without being looked at.  A refusal is a behaviour:
   assert it with ``pytest.raises(..., match=...)``.
4. **A test function with no verification**: no ``assert``, no explicit
   ``raise``, no ``pytest.raises`` / ``warns`` / ``fail`` /
   ``deprecated_call``, no ``numpy.testing`` / ``pandas.testing`` check,
   and no call to a helper that does one of those (followed through the test
   modules, ``conftest.py`` and ``help_examples.py``, to any depth).  An
   honest "does not crash" test still asserts what it built.
5. **A test that returns before anything has verified** -- ``if fw is None:
   return  # nothing to check`` -- is green exactly when the thing it exists
   to check is missing.  A ``return`` counts as early unless an assertion (or
   a skip / xfail) is certain to have run before it: earlier in its own
   block, or before the statement that holds it.  A search loop that asserts
   and then returns is fine; a precondition that does not hold is a failure,
   or an explicit ``pytest.skip`` with its reason when it is environmental.
6. **An assertion that cannot fail**: a truthy constant (``assert True``), a
   non-empty tuple (``assert (x, "message")``, the misplaced-comma
   classic), or an ``or`` with a truthy constant alternative (``assert x or
   True``).  Such an assert is no verification for rule 4 either.

Rule 6 is as far as ``assert A or B`` can be judged from the syntax: whether
a B like ``"bgcolor" in source`` holds whatever the subject does depends on
what the subject generates, which only a run can show.  (Measured
24sep2026: a saved page embeds BokehJS whole, so ``"Scatter"``, ``"Quad"``,
``"Segment"``, ``"VArea"`` and ``"LogScale"`` are on the page of a graph
drawing none of them; a page-text search for a model name cannot fail.)
The narrower shape where one alternative implies another --
``"g1__by__0" in source or "__by__" in source`` is just its second half --
is precise, but an implied alternative is not a failure by itself, so it is
left to review rather than enforced.

A handler that re-raises or calls ``pytest.fail`` is none of these.  For
rules 2 and 3, neither is a handler that asserts, or that skips / xfails
(reporting an outcome that is not a pass); rule 1 wants the re-raise --
assert on an expected ``AssertionError`` with ``pytest.raises``.
``with contextlib.suppress(...)`` is read as the handler it is.
``pytest.raises(AssertionError)`` is not rule 1: it asserts that a check
*fails*, and fails itself when the check stops failing
(``test_mode_parity.py`` uses it to keep a recorded gap's comparisons
failing).

Which functions are tests follows pytest's own defaults, which nothing in
this repository overrides: files ``test_*.py`` / ``*_test.py``, classes
``Test*`` without an ``__init__`` (nested ones too, inherited methods
included), functions and methods ``test*`` that are not fixtures.  The
enumeration is checked against the items pytest actually collected in the
running session, so a test the reader missed fails here instead of going
unexamined.
"""
import ast
import os
import re
from dataclasses import dataclass

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))

#: pytest's defaults for python_files, python_classes and python_functions.
_TEST_FILE = re.compile(r"^(test_.*|.*_test)\.py$")
_TEST_CLASS_PREFIX = "Test"
_TEST_FUNC_PREFIX = "test"

#: Handlers that catch AssertionError without naming it.
_BROAD = frozenset({"<bare>", "Exception", "BaseException"})

#: pytest calls that verify, and the ones that report a non-pass outcome.
_PYTEST_VERIFY = frozenset({"raises", "warns", "fail", "deprecated_call"})
_PYTEST_NOT_A_PASS = frozenset({"skip", "xfail", "importorskip", "exit"})

#: Library namespaces whose functions are assertions.
_ASSERTING_NAMESPACES = ("numpy.testing.", "pandas.testing.",
                         "pandas._testing.")

#: Deliberate exceptions to the rules, keyed by
#: ``(file, qualified test name, rule)``, each with the reason it is sound.
#: Empty: nothing in the suite needs one.  An entry is a claim that a test
#: which looks unable to fail can fail; write down why, or fix the test.
ALLOWLIST = {}


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    where: str
    rule: str
    detail: str

    def __str__(self):
        return "%s:%d %s [%s] %s" % (self.file, self.line, self.where,
                                     self.rule, self.detail)


# ---------------------------------------------------------------------------
# Reading the modules
# ---------------------------------------------------------------------------

_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _dotted(node):
    """``a.b.c`` as ``("a", "b", "c")``; None for anything else."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return tuple(reversed(parts))
    return None


def _is_fixture(fn):
    for dec in fn.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        d = _dotted(target)
        if d and d[-1] == "fixture":
            return True
    return False


class _Module:
    """One parsed file: its functions, classes, bases and imports."""

    def __init__(self, name, source, path=""):
        self.name = name
        self.path = path or name + ".py"
        self.file = os.path.basename(self.path)
        self.tree = ast.parse(source, self.path)
        self.funcs = {n.name: n for n in self.tree.body
                      if isinstance(n, _FUNCS)}
        self.classes = {}      # name -> ClassDef (module level and nested)
        self.imports = {}      # local name -> (module, attribute or None)
        self.parent = {}
        for node in ast.walk(self.tree):
            for child in ast.iter_child_nodes(node):
                self.parent[child] = node
            if isinstance(node, ast.ClassDef):
                self.classes.setdefault(node.name, node)
            elif isinstance(node, ast.ImportFrom) and node.module:
                for a in node.names:
                    self.imports[a.asname or a.name] = (node.module, a.name)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.asname:
                        self.imports[a.asname] = (a.name, None)
                    else:
                        root = a.name.split(".")[0]
                        self.imports[root] = (root, None)
        self._methods = {}

    def methods(self, cls_name, _seen=None):
        """*cls_name*'s methods, inherited ones included (bases defined in
        this module), nearest definition winning -- Python's own lookup for
        the single-inheritance classes the suite uses."""
        if _seen is None and cls_name in self._methods:
            return self._methods[cls_name]
        seen = set() if _seen is None else _seen
        if cls_name in seen or cls_name not in self.classes:
            return {}
        seen.add(cls_name)
        out = {}
        for base in reversed(self.classes[cls_name].bases):
            d = _dotted(base)
            if d:
                out.update(self.methods(d[-1], seen))
        for node in self.classes[cls_name].body:
            if isinstance(node, _FUNCS):
                out[node.name] = node
        if _seen is None:
            self._methods[cls_name] = out
        return out

    def qualify(self, dotted):
        """The imported name behind the first part of *dotted*, spelled out."""
        head, rest = dotted[0], dotted[1:]
        if head in self.imports:
            mod, attr = self.imports[head]
            base = mod if attr is None else mod + "." + attr
            return ".".join((base,) + rest)
        return ".".join(dotted)

    def context(self, node):
        """``(qualified name, class)`` of the function *node* sits in."""
        names, cls, cur = [], None, self.parent.get(node)
        while cur is not None:
            if isinstance(cur, _FUNCS + (ast.ClassDef,)):
                names.append(cur.name)
                if isinstance(cur, ast.ClassDef) and cls is None:
                    cls = cur.name
            cur = self.parent.get(cur)
        return "::".join(reversed(names)) or "<module>", cls


def _load(paths):
    mods = {}
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            mods[name] = _Module(name, fh.read(), path)
    return mods


def _local_walk(nodes):
    """Walk *nodes* without entering nested functions, lambdas or classes:
    a ``return`` there is not the enclosing handler's."""
    stack = list(nodes)
    while stack:
        node = stack.pop()
        if isinstance(node, _SCOPES):
            continue
        yield node
        stack.extend(ast.iter_child_nodes(node))


def _walk(nodes):
    for n in nodes:
        yield from ast.walk(n)


def _truthy_constant(expr):
    """A value true whatever runs: a truthy literal or a non-empty display."""
    if isinstance(expr, ast.Constant):
        return bool(expr.value)
    if isinstance(expr, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
        return bool(expr.keys if isinstance(expr, ast.Dict) else expr.elts)
    return False


def _cannot_fail(test):
    """Whether an ``assert`` with this condition can never fail (rule 6)."""
    if _truthy_constant(test):
        return True
    return (isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or)
            and any(_truthy_constant(v) for v in test.values))


def _ran_before(mod, fn, node):
    """The statements certain to have run before *node* in function *fn*:
    earlier siblings in each block that holds it, up to *fn*.  An ``except``
    or ``finally`` block cannot count on its ``try`` having finished, an
    ``else`` branch on its ``if`` body, so neither counts; a ``try``'s
    ``else`` runs only after its body did."""
    out, cur = [], node
    while cur is not fn and cur in mod.parent:
        parent = mod.parent[cur]
        for field, seq in ast.iter_fields(parent):
            if isinstance(seq, list) and cur in seq:
                if field != "handlers":
                    out.extend(seq[:seq.index(cur)])
                if isinstance(parent, (ast.Try, getattr(ast, "TryStar",
                                                        ast.Try))) \
                        and field == "orelse":
                    out.extend(parent.body)
                break
        cur = parent
    return out


# ---------------------------------------------------------------------------
# What verifies
# ---------------------------------------------------------------------------

class _Index:
    """Every function of every module, and which of them verify."""

    def __init__(self, mods):
        self.mods = mods
        self.funcs = {}            # (module, class or None, name) -> node
        for m in mods.values():
            for n, f in m.funcs.items():
                self.funcs[(m.name, None, n)] = f
            for c in m.classes:
                for n, f in m.methods(c).items():
                    self.funcs[(m.name, c, n)] = f
        self.verifying = {k for k, f in self.funcs.items()
                          if self.verifies_directly(f.body, mods[k[0]])}
        changed = True
        while changed:
            changed = False
            for k, f in self.funcs.items():
                if k not in self.verifying and any(
                        c in self.verifying
                        for c in self.callees(f.body, mods[k[0]], k[1])):
                    self.verifying.add(k)
                    changed = True

    @staticmethod
    def call_kind(call, mod):
        d = _dotted(call.func)
        if not d:
            return None
        q = mod.qualify(d)
        if q.startswith("pytest."):
            leaf = q.split(".", 1)[1]
            if leaf in _PYTEST_VERIFY:
                return "verify"
            if leaf in _PYTEST_NOT_A_PASS:
                return "not-a-pass"
        if q.startswith(_ASSERTING_NAMESPACES):
            return "verify"
        return None

    def verifies_directly(self, nodes, mod):
        for node in _walk(nodes):
            if isinstance(node, ast.Assert) and not _cannot_fail(node.test):
                return True
            if isinstance(node, ast.Raise) and node.exc is not None:
                return True
            if isinstance(node, ast.Call) and \
                    self.call_kind(node, mod) == "verify":
                return True
        return False

    def reports_not_a_pass(self, nodes, mod):
        return any(isinstance(n, ast.Call)
                   and self.call_kind(n, mod) == "not-a-pass"
                   for n in _walk(nodes))

    def callees(self, nodes, mod, cls):
        """The suite's own functions that *nodes* call, where they resolve."""
        for node in _walk(nodes):
            if not isinstance(node, ast.Call):
                continue
            d = _dotted(node.func)
            if not d:
                continue
            if len(d) == 1:
                name = d[0]
                if name in mod.funcs:
                    yield (mod.name, None, name)
                elif name in mod.imports:
                    src, orig = mod.imports[name]
                    if src in self.mods and orig in self.mods[src].funcs:
                        yield (src, None, orig)
            elif len(d) == 2:
                base, attr = d
                if base in ("self", "cls") and cls:
                    if attr in mod.methods(cls):
                        yield (mod.name, cls, attr)
                elif base in mod.classes:
                    if attr in mod.methods(base):
                        yield (mod.name, base, attr)
                elif base in mod.imports:
                    src, orig = mod.imports[base]
                    if orig is None and src in self.mods \
                            and attr in self.mods[src].funcs:
                        yield (src, None, attr)

    def verifies(self, nodes, mod, cls):
        return self.verifies_directly(nodes, mod) or any(
            c in self.verifying for c in self.callees(nodes, mod, cls))


# ---------------------------------------------------------------------------
# Where exceptions are caught
# ---------------------------------------------------------------------------

@dataclass
class _Catch:
    node: ast.AST            # the handler, or the with-statement
    caught: frozenset        # exception names; "<bare>" for a bare except
    guarded: list            # the statements whose exceptions it catches
    handler: list            # what runs instead ([] for suppress)
    swallows: list           # "return" / "pass" / "continue" / "suppress"
    fails: bool              # the handler raises, or calls pytest.fail


def _names(expr):
    elts = expr.elts if isinstance(expr, ast.Tuple) else [expr]
    return frozenset(d[-1] for d in map(_dotted, elts) if d)


def _fails(mod, body):
    """Whether *body* ends the test red: a ``raise`` (a bare re-raise
    included) or ``pytest.fail``."""
    for n in _local_walk(body):
        if isinstance(n, ast.Raise):
            return True
        if isinstance(n, ast.Call):
            d = _dotted(n.func)
            if d and mod.qualify(d) == "pytest.fail":
                return True
    return False


def _catches(mod, nodes):
    """Every ``except`` handler and ``suppress()`` block within *nodes*."""
    out = []
    for node in _walk(nodes):
        if isinstance(node, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            for h in node.handlers:
                caught = frozenset({"<bare>"}) if h.type is None \
                    else _names(h.type)
                out.append(_Catch(
                    h, caught, node.body, h.body,
                    sorted({type(n).__name__.lower()
                            for n in _local_walk(h.body)
                            if isinstance(n, (ast.Return, ast.Pass,
                                              ast.Continue))}),
                    _fails(mod, h.body)))
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                call = item.context_expr
                if isinstance(call, ast.Call):
                    d = _dotted(call.func)
                    if d and mod.qualify(d).endswith("suppress"):
                        caught = frozenset().union(
                            *(_names(a) for a in call.args))
                        out.append(_Catch(node, caught, node.body, [],
                                          ["suppress"], False))
    return out


# ---------------------------------------------------------------------------
# The rules
# ---------------------------------------------------------------------------

def _test_functions(mod):
    """``(qualified name, class or None, node)`` for every test pytest
    would collect from *mod*, by its default rules."""
    out = []
    for name, fn in mod.funcs.items():
        if name.startswith(_TEST_FUNC_PREFIX) and not _is_fixture(fn):
            out.append((name, None, fn))

    def visit(cls_node, prefix):
        if not cls_node.name.startswith(_TEST_CLASS_PREFIX):
            return
        methods = mod.methods(cls_node.name)
        if "__init__" in methods:
            return
        qual = prefix + cls_node.name
        for name, fn in sorted(methods.items()):
            if name.startswith(_TEST_FUNC_PREFIX) and not _is_fixture(fn):
                out.append((qual + "::" + name, cls_node.name, fn))
        for inner in cls_node.body:
            if isinstance(inner, ast.ClassDef):
                visit(inner, qual + "::")

    for node in mod.tree.body:
        if isinstance(node, ast.ClassDef):
            visit(node, "")
    return out


def analyse(mods, test_modules):
    """Every violation in *test_modules* (names), resolving helpers across
    every module in *mods*.  The allowlist is not applied here."""
    index = _Index(mods)
    found = []
    for name in test_modules:
        mod = mods[name]

        def add(node, where, rule, detail):
            found.append(Violation(mod.file, node.lineno, where, rule,
                                   detail))

        # Rule 1, module wide: helpers included.
        rule1 = set()
        for c in _catches(mod, mod.tree.body):
            if c.fails:
                continue
            where, cls = mod.context(c.node)
            label = "/".join(sorted(c.caught)) or "nothing"
            if "AssertionError" in c.caught:
                add(c.node, where, "catches-AssertionError",
                    "except %s does not re-raise" % label)
                rule1.add(id(c.node))
            elif c.caught & _BROAD and index.verifies(c.guarded, mod, cls):
                add(c.node, where, "catches-AssertionError",
                    "except %s around code that asserts, and does not "
                    "re-raise" % label)
                rule1.add(id(c.node))

        # Rule 6, module wide.
        for node in ast.walk(mod.tree):
            if isinstance(node, ast.Assert) and _cannot_fail(node.test):
                add(node, mod.context(node)[0], "assert-cannot-fail",
                    "`assert %s' is true whatever runs"
                    % ast.unparse(node.test)[:80])

        # Rules 2, 3 and 4, per test function.
        examined = set()
        for qual, cls, fn in _test_functions(mod):
            if id(fn) not in examined:
                examined.add(id(fn))
                returns = any(isinstance(n, ast.Return)
                              for n in _local_walk(fn.body))
                for r in _local_walk(fn.body):
                    if isinstance(r, ast.Return):
                        before = _ran_before(mod, fn, r)
                        if not (index.verifies(before, mod, cls)
                                or index.reports_not_a_pass(before, mod)):
                            add(r, qual, "returns-before-verifying",
                                "`%s' ends the test green before any "
                                "assertion has run" % ast.unparse(r))
                for c in _catches(mod, fn.body):
                    if c.fails or id(c.node) in rule1 \
                            or index.verifies(c.handler, mod, cls) \
                            or index.reports_not_a_pass(c.handler, mod):
                        continue
                    label = "/".join(sorted(c.caught)) or "nothing"
                    if c.caught & _BROAD and (c.swallows or returns):
                        add(c.node, qual, "broad-handler-swallows",
                            "except %s: %s" % (label, "/".join(c.swallows))
                            if c.swallows else
                            "except %s keeps the exception and the test "
                            "returns early" % label)
                    elif index.verifies(c.guarded, mod, cls):
                        add(c.node, qual, "refusal-not-asserted",
                            "except %s skips the assertions of its try and "
                            "asserts nothing itself" % label)
            if not index.verifies(fn.body, mod, cls):
                add(fn, qual, "no-verification",
                    "no assert, raise, pytest.raises/warns/fail or "
                    "asserting helper")
    return found


def _excused(violations, allowlist):
    return [v for v in violations
            if (v.file, v.where, v.rule) not in allowlist]


def _suite():
    paths = sorted(os.path.join(_HERE, f) for f in os.listdir(_HERE)
                   if f.endswith(".py"))
    mods = _load(paths)
    return mods, [m for m in mods if _TEST_FILE.match(m + ".py")]


@pytest.fixture(scope="module")
def suite():
    mods, tests = _suite()
    every = analyse(mods, tests)
    return {"mods": mods, "tests": tests, "every": every,
            "violations": _excused(every, ALLOWLIST)}


def _by_rule(violations, rule):
    return [str(v) for v in violations if v.rule == rule]


# ---------------------------------------------------------------------------
# The guard, over the whole suite
# ---------------------------------------------------------------------------

# One worker for the class, so the module's scan of the suite (the
# suite fixture) runs once, not once per worker its tests land on
# (WP-30 test performance A4; measured 07oct2026: 5.6 s on five).
@pytest.mark.xdist_group(name="test-integrity-suite")
class TestTheSuiteCanFail:

    def test_no_test_catches_assertion_error(self, suite):
        bad = _by_rule(suite["violations"], "catches-AssertionError")
        assert not bad, (
            "a handler swallows AssertionError, so the assertion it guards "
            "cannot fail:\n  " + "\n  ".join(bad))

    def test_no_broad_handler_swallows_inside_a_test(self, suite):
        bad = _by_rule(suite["violations"], "broad-handler-swallows")
        assert not bad, (
            "a bare/Exception/BaseException handler returns, passes or "
            "continues inside a test, so anything at all that goes wrong is "
            "green:\n  " + "\n  ".join(bad))

    def test_no_refusal_is_accepted_without_being_asserted(self, suite):
        bad = _by_rule(suite["violations"], "refusal-not-asserted")
        assert not bad, (
            "a handler skips the test's assertions and checks nothing about "
            "the exception; assert the refusal with pytest.raises(..., "
            "match=...):\n  " + "\n  ".join(bad))

    def test_every_test_verifies_something(self, suite):
        bad = _by_rule(suite["violations"], "no-verification")
        assert not bad, (
            "a test with no verification passes whatever its subject does:"
            "\n  " + "\n  ".join(bad))

    def test_no_test_returns_before_it_verifies(self, suite):
        bad = _by_rule(suite["violations"], "returns-before-verifying")
        assert not bad, (
            "a test returns before any assertion has run, so it is green "
            "exactly when its precondition fails; assert the precondition, "
            "or skip with the reason when it is environmental:\n  "
            + "\n  ".join(bad))

    def test_no_assert_is_true_whatever_runs(self, suite):
        bad = _by_rule(suite["violations"], "assert-cannot-fail")
        assert not bad, (
            "an assert that cannot fail:\n  " + "\n  ".join(bad))

    def test_every_allowlist_entry_still_excuses_a_live_finding(self, suite):
        """An entry for a test that no longer needs it would silently excuse
        the next test given that name."""
        live = {(v.file, v.where, v.rule) for v in suite["every"]}
        stale = sorted(set(ALLOWLIST) - live)
        assert not stale, "allowlist entries that excuse nothing: %r" % stale
        for key, reason in ALLOWLIST.items():
            assert isinstance(reason, str) and len(reason) > 20, key

    def test_the_reader_sees_every_test_pytest_collected(self, suite,
                                                         request):
        """Guards the guard: a test the enumeration misses is a test no rule
        examines.  Every collected function from test/ must be one the
        reader found -- the whole suite in a full run, this file at least in
        a targeted one."""
        seen = set()
        for name in suite["tests"]:
            for qual, _cls, _fn in _test_functions(suite["mods"][name]):
                parts = qual.split("::")
                seen.add((name, parts[-2] if len(parts) > 1 else "",
                          parts[-1]))
        collected = set()
        for item in request.session.items:
            path = str(getattr(item, "path", None)
                       or getattr(item, "fspath", ""))
            if os.path.dirname(os.path.abspath(path)) != _HERE:
                continue
            fn = getattr(item, "originalname", None) or item.name
            cls = getattr(item, "cls", None)
            collected.add((os.path.splitext(os.path.basename(path))[0],
                           cls.__name__ if cls else "", fn))
        assert ("test_test_integrity", "TestTheSuiteCanFail",
                "test_the_reader_sees_every_test_pytest_collected") \
            in collected, "the session's own items were not read"
        missed = sorted(collected - seen)
        assert not missed, (
            "pytest collected tests the reader did not enumerate: %r"
            % missed[:20])

    def test_the_suite_it_reads_is_the_real_one(self, suite):
        """Guards the guard: an empty scan passes every rule."""
        n_tests = sum(len(_test_functions(suite["mods"][m]))
                      for m in suite["tests"])
        assert len(suite["tests"]) >= 100, suite["tests"]
        assert n_tests >= 3000, n_tests
        assert "test_test_integrity" in suite["tests"]
        assert "conftest" in suite["mods"], "helpers are not being followed"


# ---------------------------------------------------------------------------
# The rules themselves, on sources written to break them
# ---------------------------------------------------------------------------

def _violations(files):
    """Analyse synthetic modules {name: source}; every ``test_*`` is a test
    file, the rest are helper modules."""
    mods = {n: _Module(n, src) for n, src in files.items()}
    return analyse(mods, [n for n in mods if _TEST_FILE.match(n + ".py")])


def _rules(files):
    return sorted((v.where, v.rule) for v in _violations(files))


class TestTheRulesFire:

    def test_catching_assertion_error_by_name(self):
        src = (
            "def test_a():\n"
            "    try:\n"
            "        assert 1 == 2\n"
            "    except (ValueError, AssertionError):\n"
            "        pass\n")
        assert _rules({"test_m": src}) == [("test_a",
                                            "catches-AssertionError")]

    def test_re_raising_assertion_error_is_allowed(self):
        src = (
            "def test_a():\n"
            "    try:\n"
            "        assert 1 == 2\n"
            "    except AssertionError as e:\n"
            "        raise AssertionError('context') from e\n")
        assert _rules({"test_m": src}) == []

    def test_a_broad_handler_around_an_assert_in_a_helper(self):
        src = (
            "def _check(x):\n"
            "    try:\n"
            "        assert x\n"
            "    except Exception:\n"
            "        print('never mind')\n"
            "def test_a():\n"
            "    _check(0)\n")
        assert ("_check", "catches-AssertionError") in \
            _rules({"test_m": src})

    def test_a_broad_handler_around_an_asserting_helper(self):
        src = (
            "def _check(x):\n"
            "    assert x\n"
            "def test_a():\n"
            "    try:\n"
            "        _check(0)\n"
            "    except BaseException as e:\n"
            "        print(e)\n")
        assert _rules({"test_m": src}) == [("test_a",
                                            "catches-AssertionError")]

    def test_suppress_is_a_handler(self):
        src = (
            "import contextlib\n"
            "def test_a():\n"
            "    with contextlib.suppress(AssertionError):\n"
            "        assert 1 == 2\n"
            "def test_b():\n"
            "    with contextlib.suppress(Exception):\n"
            "        subject()\n"
            "    assert ok()\n")
        assert _rules({"test_m": src}) == [
            ("test_a", "catches-AssertionError"),
            ("test_b", "broad-handler-swallows")]

    @pytest.mark.parametrize("handler", [
        "except Exception:\n        return",
        "except:\n        pass",
        "except BaseException:\n        pass",
        "except (OSError, Exception):\n        return",
    ])
    def test_a_broad_handler_that_swallows_in_a_test(self, handler):
        """A handler that returns is rule 5's early return as well."""
        src = (
            "def test_a():\n"
            "    try:\n"
            "        subject()\n"
            "    " + handler + "\n"
            "    assert ok()\n")
        want = [("test_a", "broad-handler-swallows")]
        if handler.endswith("return"):
            want.append(("test_a", "returns-before-verifying"))
        assert _rules({"test_m": src}) == want

    def test_a_broad_handler_that_continues_in_a_loop(self):
        src = (
            "class TestX:\n"
            "    def test_a(self):\n"
            "        for v in (1, 2):\n"
            "            try:\n"
            "                subject(v)\n"
            "            except Exception:\n"
            "                continue\n"
            "        assert ok()\n")
        assert _rules({"test_m": src}) == [("TestX::test_a",
                                            "broad-handler-swallows")]

    def test_a_kept_exception_and_an_early_return(self):
        """``raised = exc`` ... ``if raised: return`` is ``except: return``
        spelled over two statements."""
        src = (
            "def test_a():\n"
            "    raised = None\n"
            "    try:\n"
            "        out = subject()\n"
            "    except Exception as exc:\n"
            "        raised = exc\n"
            "    if raised is not None:\n"
            "        return\n"
            "    assert out\n")
        assert _rules({"test_m": src}) == [
            ("test_a", "broad-handler-swallows"),
            ("test_a", "returns-before-verifying")]

    def test_a_kept_exception_that_is_asserted_on_is_allowed(self):
        src = (
            "def test_a():\n"
            "    errors = []\n"
            "    for v in (1, 2):\n"
            "        try:\n"
            "            subject(v)\n"
            "        except Exception as exc:\n"
            "            errors.append(exc)\n"
            "    assert not errors, errors\n")
        assert _rules({"test_m": src}) == []

    def test_a_broad_handler_that_asserts_or_skips_is_allowed(self):
        src = (
            "import pytest\n"
            "def test_a():\n"
            "    try:\n"
            "        subject()\n"
            "    except Exception as exc:\n"
            "        assert 'refused' in str(exc)\n"
            "        return\n"
            "    assert False\n"
            "def test_b():\n"
            "    try:\n"
            "        import optional_thing\n"
            "    except Exception:\n"
            "        pytest.skip('optional_thing is not installed')\n"
            "    assert optional_thing\n")
        assert _rules({"test_m": src}) == []

    def test_a_handler_that_fails_the_test_is_allowed(self):
        src = (
            "import pytest\n"
            "def test_a():\n"
            "    try:\n"
            "        out = subject()\n"
            "        assert out\n"
            "    except Exception as exc:\n"
            "        pytest.fail('subject raised %r' % exc)\n")
        assert _rules({"test_m": src}) == []

    def test_a_broad_handler_in_a_helper_that_asserts_nothing(self):
        """Cleanup in a helper is not a test's verdict."""
        src = (
            "def _cleanup(p):\n"
            "    try:\n"
            "        remove(p)\n"
            "    except Exception:\n"
            "        pass\n"
            "def test_a():\n"
            "    _cleanup('x')\n"
            "    assert ok()\n")
        assert _rules({"test_m": src}) == []

    def test_a_narrow_refusal_swallowed_around_the_assertion(self):
        src = (
            "def test_a():\n"
            "    try:\n"
            "        out = subject()\n"
            "        assert 'DROP' not in out\n"
            "    except (ValueError, KeyError):\n"
            "        pass\n")
        assert _rules({"test_m": src}) == [("test_a",
                                            "refusal-not-asserted")]

    def test_a_refusal_that_is_asserted_is_allowed(self):
        src = (
            "def test_a():\n"
            "    try:\n"
            "        subject()\n"
            "        assert False, 'accepted'\n"
            "    except ValueError as e:\n"
            "        assert 'bad' in str(e)\n")
        assert _rules({"test_m": src}) == []

    def test_a_skip_in_the_handler_is_not_a_silent_pass(self):
        src = (
            "import pytest\n"
            "def test_a():\n"
            "    try:\n"
            "        assert subject()\n"
            "    except ImportError:\n"
            "        pytest.skip('optional dependency missing')\n")
        assert _rules({"test_m": src}) == []

    def test_a_test_that_verifies_nothing(self):
        src = (
            "class TestX:\n"
            "    def _render(self):\n"
            "        return subject()\n"
            "    def test_a(self):\n"
            "        self._render()\n")
        assert _rules({"test_m": src}) == [("TestX::test_a",
                                            "no-verification")]

    @pytest.mark.parametrize("body", [
        "assert subject()",
        "if not subject():\n        raise AssertionError('no')",
        "with pytest.raises(ValueError, match='x'):\n        subject()",
        "with pytest.warns(UserWarning):\n        subject()",
        "pytest.fail('always')",
        "np.testing.assert_allclose(subject(), 1.0)",
        "pd.testing.assert_frame_equal(subject(), subject())",
        "assert_array_equal(subject(), [1])",
        "_helper()",
        "_outer()",
        "shared_check()",
        "hx.check()",
        "TestY._check()",
    ])
    def test_every_form_of_verification_is_recognised(self, body):
        src = (
            "import pytest\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "from numpy.testing import assert_array_equal\n"
            "import helpers as hx\n"
            "from helpers import shared_check\n"
            "def _helper():\n"
            "    assert subject()\n"
            "def _outer():\n"
            "    _helper()\n"
            "class TestY:\n"
            "    @staticmethod\n"
            "    def _check():\n"
            "        assert ok()\n"
            "def test_a():\n"
            "    " + body + "\n")
        helpers = "def shared_check():\n    assert ok()\n" \
                  "def check():\n    assert ok()\n"
        assert _rules({"test_m": src, "helpers": helpers}) == []

    @pytest.mark.parametrize("body", [
        "pytest.skip('later')",
        "subject(check=True)",
        "np.allclose(subject(), 1.0)",
        "_quiet()",
        "hx.render()",
    ])
    def test_what_is_not_verification(self, body):
        src = (
            "import pytest\n"
            "import numpy as np\n"
            "import helpers as hx\n"
            "def _quiet():\n"
            "    return subject()\n"
            "def test_a():\n"
            "    " + body + "\n")
        helpers = "def render():\n    return 1\n"
        assert _rules({"test_m": src, "helpers": helpers}) == [
            ("test_a", "no-verification")]

    def test_a_bare_reraise_alone_is_not_verification(self):
        src = (
            "def test_a():\n"
            "    try:\n"
            "        subject()\n"
            "    except ValueError:\n"
            "        raise\n")
        assert _rules({"test_m": src}) == [("test_a", "no-verification")]

    def test_a_fixture_named_test_is_not_a_test(self):
        src = (
            "import pytest\n"
            "@pytest.fixture\n"
            "def tests_on_disk():\n"
            "    return 1\n"
            "@pytest.fixture(scope='module')\n"
            "def test_data():\n"
            "    return 2\n")
        assert _rules({"test_m": src}) == []

    def test_an_inherited_test_is_examined(self):
        src = (
            "class _Base:\n"
            "    def test_a(self):\n"
            "        subject()\n"
            "class TestConcrete(_Base):\n"
            "    pass\n")
        assert _rules({"test_m": src}) == [("TestConcrete::test_a",
                                            "no-verification")]

    def test_a_nested_test_class_is_examined(self):
        src = (
            "class TestOuter:\n"
            "    class TestInner:\n"
            "        def test_a(self):\n"
            "            subject()\n")
        assert _rules({"test_m": src}) == [
            ("TestOuter::TestInner::test_a", "no-verification")]

    def test_a_class_pytest_does_not_collect_is_not_examined(self):
        src = (
            "class Helper:\n"
            "    def test_a(self):\n"
            "        subject()\n"
            "class TestWithInit:\n"
            "    def __init__(self):\n"
            "        pass\n"
            "    def test_b(self):\n"
            "        subject()\n")
        assert _rules({"test_m": src}) == []

    def test_a_helper_module_is_not_a_test_file(self):
        src = "def test_a():\n    subject()\n"
        assert _rules({"helpers": src}) == []

    def test_a_return_in_a_nested_function_is_not_the_handlers(self):
        src = (
            "def test_a():\n"
            "    try:\n"
            "        subject()\n"
            "    except Exception as e:\n"
            "        def later():\n"
            "            return 1\n"
            "        raise AssertionError(later()) from e\n")
        assert _rules({"test_m": src}) == []

    def test_a_return_before_any_assertion(self):
        src = (
            "def test_a():\n"
            "    fw = subject()\n"
            "    if fw is None:\n"
            "        return  # nothing to check\n"
            "    assert fw.value\n")
        assert _rules({"test_m": src}) == [("test_a",
                                            "returns-before-verifying")]

    def test_a_search_loop_that_asserts_then_returns_is_allowed(self):
        src = (
            "def test_a():\n"
            "    for r in subject():\n"
            "        if not r.ok:\n"
            "            continue\n"
            "        for v in r.values:\n"
            "            assert v > 0\n"
            "        return\n"
            "    raise AssertionError('no renderer to compare')\n")
        assert _rules({"test_m": src}) == []

    def test_a_return_after_a_skip_is_allowed(self):
        src = (
            "import pytest\n"
            "def test_a():\n"
            "    if not subject():\n"
            "        pytest.skip('not a git working tree')\n"
            "        return\n"
            "    assert other()\n")
        assert _rules({"test_m": src}) == []

    def test_an_except_block_cannot_count_on_its_try(self):
        src = (
            "def test_a():\n"
            "    try:\n"
            "        assert subject()\n"
            "    except ValueError:\n"
            "        return\n")
        assert _rules({"test_m": src}) == [
            ("test_a", "refusal-not-asserted"),
            ("test_a", "returns-before-verifying")]

    def test_a_try_else_counts_its_try(self):
        src = (
            "def test_a():\n"
            "    try:\n"
            "        assert subject()\n"
            "    except KeyError:\n"
            "        raise\n"
            "    else:\n"
            "        return\n")
        assert _rules({"test_m": src}) == []

    def test_an_if_else_branch_cannot_count_on_its_if_body(self):
        src = (
            "def test_a(flag):\n"
            "    if flag:\n"
            "        assert subject()\n"
            "    else:\n"
            "        return\n")
        assert _rules({"test_m": src}) == [("test_a",
                                            "returns-before-verifying")]

    def test_a_return_in_a_nested_function_is_not_the_tests_own(self):
        src = (
            "def test_a():\n"
            "    def helper():\n"
            "        return 1\n"
            "    assert helper() == 1\n")
        assert _rules({"test_m": src}) == []

    @pytest.mark.parametrize("cond", [
        "subject() or True",
        "(subject(), 'message')",
        "True",
        "subject() or 'text'",
        "[subject()]",
    ])
    def test_an_assert_that_cannot_fail(self, cond):
        src = "def test_a():\n    assert " + cond + "\n"
        assert _rules({"test_m": src}) == [("test_a", "assert-cannot-fail"),
                                           ("test_a", "no-verification")]

    @pytest.mark.parametrize("cond", [
        "subject() or other()",
        "subject(), 'message'",
        "not subject() or other()",
        "subject() or []",
    ])
    def test_an_assert_that_can_fail(self, cond):
        src = "def test_a():\n    assert " + cond + "\n"
        assert _rules({"test_m": src}) == []

    def test_the_allowlist_excuses_exactly_its_entry(self):
        src = "def test_a():\n    subject()\n" \
              "def test_b():\n    subject()\n"
        every = _violations({"test_m": src})
        kept = _excused(every, {("test_m.py", "test_a", "no-verification"):
                                "a reason that is long enough"})
        assert [(v.where, v.rule) for v in kept] == [
            ("test_b", "no-verification")]
        assert len(every) == 2
