"""
test_corpus_functions.py -- the corpus tooling's own guards (WP-33 33-02).

Every public function of scripts/corpus/*.py is named by a test in another
test/test_corpus_*.py file (CLAUDE.md rule 3), and the lists the corpus
commits under scripts/corpus are not hidden by an ignore rule while its
dataset cache is.
"""
import ast
import glob
import os
import re
import subprocess

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _public_functions():
    out = []
    for path in sorted(glob.glob(os.path.join(_ROOT, "scripts", "corpus", "*.py"))):
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                out.append((os.path.basename(path), node.name))
    return out


class TestEveryCorpusFunctionHasATest:

    def test_every_public_function_is_named(self):
        here = os.path.abspath(__file__)
        text = ""
        for path in sorted(glob.glob(os.path.join(_ROOT, "test", "test_corpus_*.py"))):
            if os.path.abspath(path) != here:
                with open(path, encoding="utf-8") as fh:
                    text += fh.read()
        funcs = _public_functions()
        assert funcs, "no function found under scripts/corpus"
        missing = ["%s:%s" % (f, n) for f, n in funcs
                   if not re.search(r"\b%s\b" % re.escape(n), text)]
        assert missing == []


class TestTheCorpusFilesAreTracked:

    def test_the_lists_are_not_ignored(self):
        for name in ("audit_probes.txt", "calibration.tsv", "ledger.tsv",
                     "readme_examples.txt", "guard_examples.txt"):
            path = "scripts/corpus/" + name
            r = subprocess.run(["git", "check-ignore", "-q", "--no-index", path], cwd=_ROOT)
            assert r.returncode == 1, path
        r = subprocess.run(["git", "check-ignore", "-q", "--no-index",
                            "scripts/corpus/.cache/x.dta"], cwd=_ROOT)
        assert r.returncode == 0
