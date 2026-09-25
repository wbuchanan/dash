"""Regression tests for the declared Python/Bokeh/pandas/numpy floor
(GAPS2 K2).

``dash_setup.sthlp:70``, ``dash.pkg:17`` and ``dash_setup.ado:60,73,146``
declared and enforced Python 3.8+ and bokeh>=3.0 -- but every render,
saved or served, imports ``CustomJSTicker``, present only from bokeh
3.6.0, so an installed bokeh 3.0-3.5 passed ``dash_setup`` and then every
``dash`` command failed with r(7102); the generated server app had no
``from __future__ import annotations`` and 55 annotations Python
evaluates at import, raising ``TypeError`` on Python 3.8 and 3.9.

DISCOVERY Q8 settles the floor as what is tested today: the ``stata``
baseline of ``test/conftest.py`` -- Python 3.13, bokeh 3.8, pandas 2.3,
numpy 2.3 -- declared in every file that names a minimum, with pandas
declared by dash itself because bokeh 3.9 dropped it as a required
dependency.
"""
import ast
import json
import os
import re
import sys
import warnings

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import _BASELINES, make_data_json  # noqa: E402


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def _flat(text):
    return " ".join(text.split())


def _stata_baseline():
    b = _BASELINES["stata"]
    return b["python"], b["bokeh"], b["numpy"], b["pandas"]


def _setup_ado_floor():
    text = _read("dash_setup.ado")
    pymin = re.search(r'return local pymin "([^"]+)"', text)
    bokeh = re.search(r'local\s+min_bokeh\s+"([^"]+)"', text)
    numpy = re.search(r'local\s+min_numpy\s+"([^"]+)"', text)
    pandas = re.search(r'local\s+min_pandas\s+"([^"]+)"', text)
    assert pymin and bokeh and numpy and pandas, (
        "the floor lines were not found in dash_setup.ado")
    return pymin.group(1), bokeh.group(1), numpy.group(1), pandas.group(1)


class TestTheFloorIsTheTestedBaseline:
    def test_dash_setup_declares_the_stata_baseline(self):
        py, bo, nu, pa = _setup_ado_floor()
        want_py, want_bo, want_nu, want_pa = _stata_baseline()
        assert py == want_py, (py, want_py)
        assert bo == want_bo, (bo, want_bo)
        assert nu == want_nu, (nu, want_nu)
        assert pa == want_pa, (pa, want_pa)

    def test_every_declaration_agrees_with_dash_setup(self):
        py, bo, nu, pa = _setup_ado_floor()

        pkg = _read("dash.pkg")
        assert ("Requires: Python %s+, bokeh>=%s, numpy>=%s, pandas>=%s."
                % (py, bo, nu, pa)) in pkg, pkg

        ado = _read("dash.ado")
        assert ("Python %s+" % py) in ado, ado

        help_ = _flat(_read("dash.sthlp"))
        assert ("{ul:Python %s+}" % py) in help_, help_
        assert ("bokeh>=%s, numpy>=%s, pandas>=%s"
                % (bo, nu, pa)) in help_, help_

        shelp = _flat(_read("dash_setup.sthlp"))
        assert ("Python %s or later" % py) in shelp, shelp
        assert ("{opt bokeh}}%s or later" % bo) in shelp, shelp
        assert ("{opt numpy}}%s or later" % nu) in shelp, shelp
        assert ("{opt pandas}}%s or later" % pa) in shelp, shelp
        assert ("below %s" % py) in shelp, shelp
        assert ("one below %s is reported" % bo) in shelp, shelp

        changelog = _flat(_read("CHANGELOG.md"))
        rq_start = changelog.index("### Requirements")
        rq_end = changelog.index("### ", rq_start + 10)
        rq = changelog[rq_start:rq_end]
        assert ("Python %s" % py) in rq, rq
        assert ("bokeh >= %s" % bo) in rq, rq

    def test_the_old_floor_is_named_nowhere_it_matters(self):
        """Precise patterns, not bare substrings: several files carry
        narrative comments that mention old numbers as historical or
        illustrative examples (a docstring's "e.g. 3.8", the story of a
        version() bug measured against "2.4" and "3.0"), which are not
        the declared floor and must not make this test fail."""
        ado_setup = _read("dash_setup.ado")
        for pattern in (r'local\s+min_bokeh\s+"3\.0"',
                        r'local\s+min_numpy\s+"1\.23"',
                        r'local\s+min_pandas\s+"2\.0"',
                        r'return local pymin "3\.8"'):
            assert not re.search(pattern, ado_setup), pattern
        assert "Python 3.8+" not in _read("dash.ado")
        for rel in ("dash.pkg", "dash.sthlp", "dash_setup.sthlp"):
            text = _read(rel)
            for needle in ("Python 3.8", "bokeh>=3.0", "3.0 or later",
                          "1.23 or later", "2.0 or later"):
                assert needle not in text, (rel, needle)

    def test_the_upgrade_line_names_the_linked_interpreter(self):
        """Q27: dash_setup's below-minimum branch prints the pip command
        for the interpreter Stata is linked to, never the bare word
        'python' -- installing with a different interpreter than the one
        Stata runs against would upgrade the wrong Python."""
        ado = _read("dash_setup.ado")
        m = re.search(r"program define _dash_pip_command.*?\bend\b", ado,
                      re.S)
        assert m, "no _dash_pip_command program in dash_setup.ado"
        body = m.group(0)
        assert "c(python_exec)" in body, body
        assert "-m pip install" in body, body
        assert ">=" in body, body
        below = ado[ado.find('"below"'):]
        below = below[:below.find("else", 1)] if "else" in below[1:] \
            else below
        assert "_dash_pip_command" in below, below
        assert "python -m pip install --upgrade" not in below, below


class TestTheGeneratedAppEvaluatesNoAnnotationAtImport:
    def _built(self, tmp_path):
        import pandas as pd
        df = pd.DataFrame({"mpg": [22.0], "weight": [2930.0]})
        spec = {
            "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                       "plots": [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight", "options": {}}],
                       "options": {}}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}},
        }
        sp = tmp_path / "spec.json"
        dp = tmp_path / "data.json"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(df)))
        out = tmp_path / "app.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(out))
        return out.read_text()

    def test_the_future_import_is_the_first_statement(self, tmp_path):
        src = self._built(tmp_path)
        tree = ast.parse(src)
        assert isinstance(tree.body[0], ast.Expr)  # the module docstring
        assert isinstance(tree.body[1], ast.ImportFrom), ast.dump(
            tree.body[1])
        assert tree.body[1].module == "__future__"
        assert any(a.name == "annotations" for a in tree.body[1].names)

    def test_pep585_and_pep604_annotations_are_deferred(self, tmp_path):
        src = self._built(tmp_path)
        tree = ast.parse(src)
        future_ok = (isinstance(tree.body[1], ast.ImportFrom)
                    and tree.body[1].module == "__future__"
                    and any(a.name == "annotations"
                           for a in tree.body[1].names))

        def _is_deferred_shape(node):
            if isinstance(node, ast.BinOp) and isinstance(node.op,
                                                           ast.BitOr):
                return True
            if isinstance(node, ast.Subscript):
                base = node.value
                name = getattr(base, "id", None)
                if name in ("list", "dict", "tuple", "set", "frozenset",
                           "type"):
                    return True
            return False

        found = []
        seen = 0
        for node in ast.walk(tree):
            annots = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                annots.append(node.returns)
                for a in (list(node.args.args)
                         + list(node.args.posonlyargs)
                         + list(node.args.kwonlyargs)):
                    annots.append(a.annotation)
            elif isinstance(node, ast.AnnAssign):
                annots.append(node.annotation)
            for a in annots:
                if a is None:
                    continue
                seen += 1
                if _is_deferred_shape(a):
                    found.append(a)
        assert seen > 20, seen  # the walker actually saw annotations
        assert found == [] or future_ok
