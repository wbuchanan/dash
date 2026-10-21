"""One rule for every list of known differences from twoway (WP-33 33-10).

A truth table that compares dash with twoway key by key keeps a
module-level ``<NAME>_KNOWN`` dict ``{key: "<GAPS4 lead id>"}``, whose value
is ``"<id>"`` (an item to be fixed), ``"<id> (documented)"`` (a Kind
Document item) or ``"<id> (residual)"`` (the residual of a Partly item),
and a companion ``<NAME>_DELIBERATE`` dict ``{key: "<ruling id>: <what is
kept>"}`` for differences a ruling keeps on purpose (D-33-10.a).

``known_problems`` fails a comparison on
  (1) a key that differs from twoway and is not listed;
  (2) a listed key that now agrees with twoway;
  (3) a listed key whose row is not live: ``"<id>"`` needs the item open,
      ``"<id> (documented)"`` open or Documented, ``"<id> (residual)"``
      open or Partly closed (GAPS4.md's Tracked lines);
  (4) a listed key the comparison no longer produces.

Run as a script (D-33-10.h), ``python3 test/known_differences.py <lead
id> [--all]`` prints every row of every ``*_KNOWN`` table under test/
whose value is the id (with ``--all`` its documented and residual rows
too) and the one command that runs every table's hygiene test.
"""
import ast
import os
import re
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TRACKED = re.compile(r"^- \*\*(?P<id>\S+) Tracked:\*\* (?P<text>\S.*)$")
_ROW = re.compile(r"^(?P<id>\S+?)(?: \((?P<form>documented|residual)\))?$")
_HYGIENE = "test_every_known_difference_is_open"


def _tracked(path):
    path = path or os.path.join(_REPO, "GAPS4.md")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "%s is missing: WP-33 section 33-01 writes GAPS4.md" % path)
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            m = _TRACKED.match(ln.rstrip("\n"))
            if m:
                yield m.group("id"), m.group("text")


def gaps4_open_ids(path=None):
    """The GAPS4 lead ids whose Tracked line is ``Open (...``."""
    return frozenset(i for i, t in _tracked(path) if t.startswith("Open ("))


def gaps4_documented_ids(path=None):
    """The GAPS4 lead ids whose Tracked line is ``Documented in WP-...``."""
    return frozenset(i for i, t in _tracked(path)
                     if t.startswith("Documented in WP-"))


def gaps4_partly_ids(path=None):
    """The GAPS4 lead ids whose Tracked line is ``Partly closed in WP-...``."""
    return frozenset(i for i, t in _tracked(path)
                     if t.startswith("Partly closed in WP-"))


def _dead(known, label, open_ids, documented, partly):
    out = []
    for key, value in known.items():
        m = _ROW.match(value) if isinstance(value, str) else None
        if not m:
            out.append("%s: %s: row %r is not '<id>', '<id> (documented)' "
                       "or '<id> (residual)'" % (label, key, value))
            continue
        iid, form = m.group("id"), m.group("form")
        live = iid in open_ids or (
            form == "documented" and iid in documented) or (
            form == "residual" and iid in partly)
        if not live:
            out.append("%s: %s: %s is not live: the row should have gone "
                       "with %s's fix" % (label, key, value, iid))
    return out


def dead_rows(known, label, path=None):
    """Rule 3 alone, over every row of ``known``: sorted problem strings."""
    return sorted(_dead(known, label, gaps4_open_ids(path),
                        gaps4_documented_ids(path), gaps4_partly_ids(path)))


def known_problems(results, known, label, open_ids=None, deliberate=None,
                   path=None):
    """Every problem of a comparison against its known-differences table.

    ``results`` is ``{key: None | "<difference>"}`` (None: dash agrees with
    twoway); ``known`` the ``<NAME>_KNOWN`` table; ``deliberate`` its
    ``<NAME>_DELIBERATE`` companion, whose keys are dropped from the
    results first.  ``open_ids`` overrides the open ids read from GAPS4.md
    (``path``, default the repository's).  Returns sorted strings.
    """
    res = dict(results)
    for key in (deliberate or {}):
        res.pop(key, None)
    if open_ids is None:
        open_ids = gaps4_open_ids(path)
    probs = []
    for key, diff in res.items():
        if diff is not None and key not in known:
            probs.append("%s: %s differs from twoway and is not listed: %s"
                         % (label, key, diff))
    for key, value in known.items():
        if key in res and res[key] is None:
            m = _ROW.match(value) if isinstance(value, str) else None
            probs.append("%s: %s now agrees with twoway: delete its row: "
                         "%s fixed it" % (label, key,
                                          m.group("id") if m else value))
    probs.extend(_dead(known, label, open_ids, gaps4_documented_ids(path),
                       gaps4_partly_ids(path)))
    for key in known:
        if key not in res:
            probs.append("%s: %s is listed but the comparison no longer "
                         "produces it" % (label, key))
    return sorted(probs)


def _tables(test_dir):
    for name in sorted(os.listdir(test_dir)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(test_dir, name), encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=name)
        yield name, tree


def rows_for(lead_id, test_dir=None, every_form=False):
    """``"<file>:<line>: <key>: <value>"`` for each row of each module-level
    ``*_KNOWN`` dict literal under ``test_dir`` whose value is ``lead_id``
    (with ``every_form``, also its documented and residual forms)."""
    test_dir = test_dir or os.path.join(_REPO, "test")
    want = {lead_id}
    if every_form:
        want |= {lead_id + " (documented)", lead_id + " (residual)"}
    out = []
    for name, tree in _tables(test_dir):
        for node in tree.body:
            if not (isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.Dict)
                    and any(isinstance(t, ast.Name) and t.id.endswith("_KNOWN")
                            for t in node.targets)):
                continue
            for k, v in zip(node.value.keys, node.value.values):
                if (isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
                        and v.value in want):
                    out.append("%s:%d: %s: %s" % (name, k.lineno, k.value,
                                                  v.value))
    return out


def hygiene_files(test_dir=None):
    """The ``test/*.py`` files that define ``test_every_known_difference_is_open``."""
    test_dir = test_dir or os.path.join(_REPO, "test")
    out = []
    for name, tree in _tables(test_dir):
        if any(isinstance(n, ast.FunctionDef) and n.name == _HYGIENE
               for n in ast.walk(tree)):
            out.append(os.path.join(test_dir, name))
    return sorted(out)


def main(argv):
    args = [a for a in argv if a != "--all"]
    if len(args) != 1:
        print("usage: python3 test/known_differences.py <lead id> [--all]",
              file=sys.stderr)
        return 2
    for line in rows_for(args[0], every_form="--all" in argv):
        print(line)
    print("python3 -m pytest %s -q -n0 -k every_known_difference_is_open"
          % " ".join(os.path.relpath(f, _REPO) for f in hygiene_files()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
