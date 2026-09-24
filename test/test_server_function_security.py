"""The served `function` validator let keyword arguments through, and they run.

`twoway function y = <expr>` evaluates a user expression. Both renderers parse
it to an AST and walk it against a whitelist before `eval`. The standalone
walk rejects a call that carries keyword arguments:

    if node.keywords:
        raise ValueError("Keyword arguments are not allowed ...")

The copy emitted into the generated server app walked ``node.args`` and
stopped. A keyword VALUE is an arbitrary expression that Python evaluates
before the call, so

    function y = sin(x, out=[c for c in ().__class__.__bases__[0]
                             .__subclasses__() if c.__name__=='_wrap_close'
                            ][0].__init__.__globals__['__builtins__']
                            ['open']('/tmp/PWN','w').write('PWNED'))

wrote the file when the document was built. `{'__builtins__': {}}` does not
help: the escape reaches builtins through `object.__subclasses__()`.

Measured before the fix: the standalone renderer refused the expression and
the served app executed it, so the two modes disagreed about what was safe --
and the generated `.py` is the artefact a user is told to keep and re-run.

test/test_phase4_plots.py::test_function_rejects_keyword_args covered the
standalone side only.
"""
import importlib.util
import itertools
import json
import os
import sys
import warnings

import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_SEQ = itertools.count()

# A payload that reaches `open` through object.__subclasses__(), the standard
# escape from a namespace whose __builtins__ is empty. It is parked in a
# keyword argument, which is the part the emitted walk never inspected.
_ESCAPE = (
    "[c for c in ().__class__.__bases__[0].__subclasses__() "
    "if c.__name__ == '_wrap_close'][0].__init__.__globals__"
    "['__builtins__']['open'](%r, 'w').write('PWNED')"
)


def _spec(expr):
    return {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": "scatter", "yvar": "yv",
                                   "xvar": "x", "options": {}},
                                  {"type": "function", "expr": expr,
                                   "options": {}}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""}}


class _ValidatorVerdict:
    """Counts the function() expressions map_function's whitelist ACCEPTED.

    map_function parses the expression, walks it against the whitelist,
    and only then hands the tree to ``_floats_only`` and compiles it; a
    refusal returns an empty layer before ``_floats_only`` is reached.  So a
    call of ``_floats_only`` is the validator's "accepted", read without
    evaluating anything it refused.

    "Drew nothing" cannot tell the two apart: map_function swallows an
    evaluation error into the same empty layer, and ``_floats_only`` turns
    every integer literal into a float, so a subscript such as ``[0]`` fails
    at evaluation whatever the validator said (measured 24sep2026: with the
    ``node.keywords`` branch deleted, every keyword expression below still
    drew nothing and wrote no marker, and the old tests stayed green).
    """

    def __init__(self):
        self.real = None
        self.accepted = 0

    def __call__(self, tree):
        self.accepted += 1
        return self.real(tree)


def _build_and_run(tmp_path, expr, verdict=None):
    """Build the server app for *expr* and execute its make_document.

    With *verdict*, the app's own ``_floats_only`` -- the copy its
    GlyphMapper calls -- is wrapped for the document build, so the served
    validator's verdict is counted in the served code itself.
    """
    tag = next(_SEQ)
    sp = tmp_path / f"s_{tag}.json"
    dp = tmp_path / f"d_{tag}.json"
    sp.write_text(json.dumps(_spec(expr)))
    dp.write_text(json.dumps(make_data_json(
        __import__("pandas").DataFrame({"x": [0.0, 0.5, 1.0],
                                        "yv": [1.0, 2.0, 3.0]}))))
    ap = tmp_path / f"a_{tag}.py"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
    ms = importlib.util.spec_from_file_location(f"_fnsec_{tag}", str(ap))
    mod = importlib.util.module_from_spec(ms)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ms.loader.exec_module(mod)
        if verdict is not None:
            verdict.real = mod._floats_only
            mod._floats_only = verdict
        doc = Document()
        mod.make_document(doc)
    return doc


def _standalone(tmp_path, expr, verdict=None):
    tag = next(_SEQ)
    sp = tmp_path / f"ss_{tag}.json"
    dp = tmp_path / f"sd_{tag}.json"
    sp.write_text(json.dumps(_spec(expr)))
    dp.write_text(json.dumps(make_data_json(
        __import__("pandas").DataFrame({"x": [0.0, 0.5, 1.0],
                                        "yv": [1.0, 2.0, 3.0]}))))
    if verdict is not None:
        verdict.real = dr._floats_only
        dr._floats_only = verdict
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.DashRenderer(str(sp), str(dp)).render()
    finally:
        if verdict is not None:
            dr._floats_only = verdict.real


class TestAKeywordArgumentCannotExecute:
    def test_the_served_app_does_not_run_a_keyword_payload(self, tmp_path):
        marker = tmp_path / "PWN_SERVER.txt"
        expr = "sin(x, out=" + (_ESCAPE % str(marker)) + ")"
        verdict = _ValidatorVerdict()
        _build_and_run(tmp_path, expr, verdict)
        assert not marker.exists(), (
            f"`dash serve' executed arbitrary Python from a function() "
            f"expression: {marker} was written with "
            f"{marker.read_text() if marker.exists() else ''!r}"
        )
        # The marker cannot fail on its own (see _ValidatorVerdict): the
        # served validator must REFUSE the expression, and -- the positive
        # control -- the same count must see it accept a plain one.
        assert verdict.accepted == 0, (
            "the served validator accepted a keyword argument; only the "
            "evaluation failing kept the payload from running")
        control = _ValidatorVerdict()
        _build_and_run(tmp_path, "sin(x)", control)
        assert control.accepted == 1, control.accepted

    def test_the_standalone_renderer_does_not_either(self, tmp_path):
        """The control: the two modes must agree about what is safe."""
        marker = tmp_path / "PWN_STANDALONE.txt"
        expr = "sin(x, out=" + (_ESCAPE % str(marker)) + ")"
        verdict = _ValidatorVerdict()
        _standalone(tmp_path, expr, verdict)
        assert not marker.exists()
        assert verdict.accepted == 0, (
            "the standalone validator accepted a keyword argument")
        control = _ValidatorVerdict()
        _standalone(tmp_path, "sin(x)", control)
        assert control.accepted == 1, control.accepted

    @pytest.mark.parametrize("expr", [
        "sin(x, out=1)",
        "sin(x, out=().__class__)",
        "sin(x, **{'out': 1})",
        "abs(x, out=[c for c in ().__class__.__bases__[0].__subclasses__()][0])",
        # The one keyword call that DRAWS if accepted: `out=None' is numpy's
        # own default, so the curve check below is live for it.  The four
        # above raise inside numpy and draw nothing either way (24sep2026).
        "sin(x, out=None)",
    ])
    def test_no_call_with_keywords_is_accepted(self, tmp_path, expr):
        """A keyword value is an arbitrary expression; none may be walked."""
        verdict = _ValidatorVerdict()
        doc = _build_and_run(tmp_path, expr, verdict)
        from bokeh.models import ColumnDataSource
        fn = [m for m in doc.select({"type": ColumnDataSource})
              if "x_fn" in m.data and len(m.data["x_fn"])]
        assert not fn, (
            f"{expr!r} was accepted and evaluated by the served app"
        )
        assert verdict.accepted == 0, (
            f"{expr!r} was accepted by the served validator")

    @pytest.mark.parametrize("mode", ["served", "standalone"])
    def test_the_verdict_count_sees_an_accepted_expression(self, tmp_path,
                                                           mode):
        """Positive control for every ``accepted == 0`` above: the count
        is read where the served (or saved) mapper really calls it."""
        verdict = _ValidatorVerdict()
        if mode == "served":
            _build_and_run(tmp_path, "sin(x)", verdict)
        else:
            _standalone(tmp_path, "sin(x)", verdict)
        assert verdict.accepted == 1, verdict.accepted

    def test_the_emitted_validator_names_keywords(self):
        """Source-level guard: the branch must exist, not just happen to fail.

        It is checked on ``GlyphMapper.map_function``, which is where the
        validator now lives and which BOTH modes run. It used to be written
        as string literals inside ``ServerAppBuilder``, and reading that
        source for it now finds nothing -- not because the guard went away,
        but because the served app calls the shared implementation instead of
        carrying a second copy of it.
        """
        import inspect
        src = inspect.getsource(dr.GlyphMapper.map_function)
        assert "node.keywords" in src, (
            "the function validator does not inspect node.keywords, so a "
            "keyword argument's value is never walked"
        )
        # And the guard reaches the generated app, not just this module.
        assert "node.keywords" in inspect.getsource(dr.GlyphMapper), (
            "map_function's validator is not part of the GlyphMapper source "
            "the server app copies"
        )


class TestOrdinaryFunctionPlotsStillWork:
    """The fix must not close the option it is protecting."""

    @pytest.mark.parametrize("expr", [
        "x", "x^2", "sin(x)", "exp(-x) * cos(x)",
        "log(x + 1)", "sqrt(abs(x))", "2*pi*x",
    ])
    def test_a_plain_expression_still_draws(self, tmp_path, expr):
        doc = _build_and_run(tmp_path, expr)
        from bokeh.models import ColumnDataSource
        fn = [m for m in doc.select({"type": ColumnDataSource})
              if "x_fn" in m.data and len(m.data["x_fn"])]
        assert fn, f"{expr!r} draws nothing in server mode"
