"""Generated server apps are compiled once per block of text (WP-30 A3).

``conftest.load_app`` and ``conftest.exec_app`` run a generated app's exact
text, compiled in blocks that each process compiles once: an app differs
from the next in its embedded spec and data lines, and compiling all
26,000 lines of every app was a third of a served render in the tests.
These pin that the blocks are the file -- every function and class code
object equal to the whole compile's, the module the one ``exec_module``
makes -- that a second app compiles only what differs, that the texts the
blocks cannot carry are compiled whole as before, that a traceback names
the file and line, and that the caches are bounded.
"""
import importlib.util
import os
import sys
import traceback
import types
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import conftest as C  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402


def _built(tmp_path, plots, name):
    """(path, text) of the app built for a one-graph spec of *plots*."""
    spec = tp._spec(plots)
    _tag, sp, dp = tp._write(spec)
    path = str(tmp_path / (name + ".py"))
    import dash_render as dr
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(path)
    with open(path, encoding="utf-8") as fh:
        return path, fh.read()


def _codes(codes):
    """Every code object nested in *codes*, in a stable order."""
    out = []

    def walk(code):
        for c in code.co_consts:
            if isinstance(c, types.CodeType):
                out.append(c)
                walk(c)

    for code in codes:
        walk(code)
    return sorted(out, key=lambda c: (c.co_firstlineno, c.co_qualname))


def _run(codes, filename):
    ns = {"__name__": "_loader_probe", "__file__": filename}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for code in codes:
            exec(code, ns)
    return ns


def _public(ns):
    return [k for k in ns if k != "__builtins__"]


# Python 3.12 made an invalid escape a SyntaxWarning; 3.11, the floor, says
# DeprecationWarning (GitHub's runner, 15nov2026).
_ESCAPE_WARNING = (SyntaxWarning if sys.version_info >= (3, 12)
                   else DeprecationWarning)


def _class_lines(cls):
    """Where a class sits in its file: ``__firstlineno__`` (Python 3.13+,
    else None) and its methods' first lines (every version)."""
    return (getattr(cls, "__firstlineno__", None),
            sorted(f.__code__.co_firstlineno for f in vars(cls).values()
                   if isinstance(f, types.FunctionType)))


class TestTheBlocksAreTheFile:

    @pytest.mark.parametrize("plots", [[plot_for("scatter")],
                                       [plot_for("lfitci"),
                                        plot_for("rarea")]],
                             ids=["scatter", "lfitci-rarea"])
    def test_every_code_object_equals_the_whole_compile(self, tmp_path,
                                                        plots):
        path, text = _built(tmp_path, plots, "app")
        blocks = C.compile_app(text, path)
        whole = compile(text, path, "exec", dont_inherit=True)
        assert len(blocks) > 100, "the app was compiled whole"
        got, want = _codes(blocks), _codes([whole])
        assert len(got) == len(want) > 500
        for a, b in zip(got, want):
            assert a == b, (a.co_qualname, a.co_firstlineno)
            assert (a.co_qualname, a.co_filename) == (b.co_qualname, path)

    def test_the_blocks_cover_the_text_exactly(self, tmp_path):
        _path, text = _built(tmp_path, [plot_for("line")], "app")
        spans, imported = C._app_blocks(text)
        assert spans[0][0] == 0 and spans[-1][1] == len(text)
        assert all(a[1] == b[0] for a, b in zip(spans, spans[1:]))
        assert "".join(text[a:b] for a, b in spans) == text
        assert {"np", "pd", "json", "math"} <= imported

    def test_the_module_is_the_one_exec_module_makes(self, tmp_path):
        path, _text = _built(tmp_path, [plot_for("bar")], "app")
        ms = importlib.util.spec_from_file_location("_loader_a", path)
        want = importlib.util.module_from_spec(ms)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ms.loader.exec_module(want)
            got = C.load_app(path, "_loader_a")
        assert _public(vars(got)) == _public(vars(want))
        for attr in ("__name__", "__file__", "__doc__", "__annotations__",
                     "__package__"):
            assert getattr(got, attr) == getattr(want, attr), attr
        assert got.__spec__.origin == want.__spec__.origin == path
        assert type(got.__loader__) is type(want.__loader__)
        classes = [k for k, v in vars(want).items()
                   if isinstance(v, type) and v.__module__ == "_loader_a"]
        assert len(classes) >= 3
        for k in classes:
            assert (_class_lines(vars(got)[k])
                    == _class_lines(vars(want)[k])), k
        assert "_loader_a" not in sys.modules


class TestTheImportTimeDrawIsTheCallers:
    """``load_app(draw=False)``: the app's import-time
    ``make_document(curdoc())`` is skipped and nothing else changes."""

    def test_draw_false_leaves_curdoc_empty_and_the_rest_whole(self,
                                                               tmp_path):
        from bokeh.document import Document
        from bokeh.io import curdoc
        path, text = _built(tmp_path, [plot_for("scatter")], "app")
        undrawn = C.undrawn_app(text)
        assert undrawn.count("\n") == text.count("\n")
        assert undrawn != text
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            curdoc().clear()
            drawn = C.load_app(path, "_loader_d")
            assert len(curdoc().roots) == 1
            curdoc().clear()
            got = C.load_app(path, "_loader_n", draw=False)
            assert curdoc().roots == []
            assert sorted(_public(vars(got))) == sorted(_public(vars(drawn)))
            mine, theirs = Document(), Document()
            got.make_document(mine)
            drawn.make_document(theirs)
        assert ([type(r).__name__ for r in mine.roots]
                == [type(r).__name__ for r in theirs.roots])
        assert len(mine.models) == len(theirs.models)

    def test_a_text_without_the_draw_is_refused(self):
        with pytest.raises(ValueError):
            C.undrawn_app("x = 1\n")


class TestTheTrialByBlocks:
    """``trial_by_blocks``: ``build(trial=True)`` raises the same notes,
    in order, with the trial's text run through ``exec_app``."""

    def test_the_trial_notes_and_namespace_are_the_whole_compiles(
            self, tmp_path):
        import dash_render as dr
        spec = tp._spec([plot_for("scatter")],
                        graph_options={"xlabel": "1(1)3, nolabel bogus"})
        _tag, sp, dp = tp._write(spec)

        def trial(path, by_blocks):
            with warnings.catch_warnings(record=True) as got:
                warnings.simplefilter("always")
                if by_blocks:
                    with C.trial_by_blocks(dr):
                        dr.ServerAppBuilder(sp, dp).build(path, trial=True)
                else:
                    dr.ServerAppBuilder(sp, dp).build(path, trial=True)
            return [str(w.message) for w in got]

        whole = trial(str(tmp_path / "w.py"), False)
        before = dict(C.APP_LOADER_STATS)
        blocks = trial(str(tmp_path / "b.py"), True)
        assert blocks == whole and whole, whole
        assert C.APP_LOADER_STATS["whole"] == before["whole"]
        assert (C.APP_LOADER_STATS["compiled"] + C.APP_LOADER_STATS["reused"]
                > before["compiled"] + before["reused"])
        assert not hasattr(dr, "compile") and not hasattr(dr, "exec")

    def test_other_compiles_and_execs_pass_through(self):
        import dash_render as dr
        ns = {}
        with C.trial_by_blocks(dr):
            dr.exec(dr.compile("y = 2", "<probe>", "exec"), ns)
        assert ns["y"] == 2


class TestASecondAppReusesTheBlocks:

    def test_a_second_spec_compiles_only_what_differs(self, tmp_path):
        path_a, text_a = _built(tmp_path, [plot_for("scatter")], "a")
        path_b, text_b = _built(tmp_path, [plot_for("dropline")], "b")
        C.compile_app(text_a, path_a)
        before = dict(C.APP_LOADER_STATS)
        codes = C.compile_app(text_b, path_b)
        compiled = C.APP_LOADER_STATS["compiled"] - before["compiled"]
        reused = C.APP_LOADER_STATS["reused"] - before["reused"]
        assert C.APP_LOADER_STATS["whole"] == before["whole"]
        assert compiled + reused == len(codes)
        assert compiled <= 2, compiled
        assert {c.co_filename for c in codes} == {path_b}


class TestTheTextsCompiledWhole:

    def test_a_bare_carriage_return(self):
        before = C.APP_LOADER_STATS["whole"]
        ns = C.exec_app("x = 1\ry = x + 1\n", "cr.py", {})
        assert (ns["x"], ns["y"]) == (1, 2)
        assert C.APP_LOADER_STATS["whole"] == before + 1

    @pytest.mark.parametrize("load", [1, 2])
    def test_a_warning_is_raised_on_every_load(self, load):
        with pytest.warns(_ESCAPE_WARNING, match="invalid escape sequence"):
            ns = C.exec_app('import os\nx = "\\d"\ny = 2\n', "warns.py", {})
        assert ns["x"] == "\\d" and ns["y"] == 2

    def test_a_syntax_error_is_the_compilers(self):
        source = "import os\n\ndef f(:\n    pass\n"
        with pytest.raises(SyntaxError) as want:
            compile(source, "bad.py", "exec", dont_inherit=True)
        with pytest.raises(SyntaxError) as got:
            C.compile_app(source, "bad.py")
        assert (got.value.msg, got.value.lineno, got.value.filename) == (
            want.value.msg, want.value.lineno, want.value.filename)


_AWKWARD = '''"""The module's docstring."""
from __future__ import annotations

import os.path as osp

LIMIT: int = 3


def dec(fn):
    return fn


@dec
def f(x: int) -> str:
    return osp.join(str(x), "a")


try:
    import json
except ImportError:
    json = None
else:
    LOADED = True
finally:
    DONE = 1

if DONE:
    BRANCH = "if"
elif LOADED:
    BRANCH = "elif"
else:
    BRANCH = "else"

TEXT = """
name = 1
@not_a_decorator
def not_a_function():
"""
r"a raw string, not the module's docstring"


@dec
class K:
    """A class."""
    value: int = 3

    def g(self):
        return json.dumps([self.value])


TOTAL = len(TEXT)
'''


class TestTheBlocksOfAnAwkwardText:

    def test_the_namespace_and_the_code_are_the_whole_compiles(self):
        blocks = C.compile_app(_AWKWARD, "awkward.py")
        whole = compile(_AWKWARD, "awkward.py", "exec", dont_inherit=True)
        assert len(blocks) > 1
        got, want = _run(blocks, "awkward.py"), _run([whole], "awkward.py")
        assert _public(got) == _public(want)
        assert got["__doc__"] == "The module's docstring."
        assert got["__annotations__"] == want["__annotations__"] \
            == {"LIMIT": "int"}
        assert got["f"].__annotations__ == {"x": "int", "return": "str"}
        assert got["f"](1) == want["f"](1)
        assert (got["BRANCH"], got["TEXT"]) == (want["BRANCH"], want["TEXT"])
        assert got["K"]().g() == "[3]"
        assert _class_lines(got["K"]) == _class_lines(want["K"])
        got_codes, want_codes = _codes(blocks), _codes([whole])
        assert got_codes == want_codes

    def test_a_late_annotation_puts_everything_before_it_in_one_block(self):
        """The compiler sets a module's annotations up at its top, so the
        block that annotates and every block before it are compiled as
        one."""
        source = _AWKWARD + "LATE: str = TEXT\n"
        spans, _imported = C._app_blocks(source)
        assert len(spans) == 1
        got = _run(C.compile_app(source, "late.py"), "late.py")
        want = _run([compile(source, "late.py", "exec", dont_inherit=True)],
                    "late.py")
        assert _public(got) == _public(want)
        assert got["__annotations__"] == {"LIMIT": "int", "LATE": "str"}


class TestATracebackNamesTheFileAndLine:

    def test_an_error_in_a_late_block(self, tmp_path):
        path = str(tmp_path / "boom.py")
        source = ("import math\n\n\ndef ok():\n    return 1\n\n\n"
                  "def boom():\n    x = 1\n    return math.sqrt(-x)\n")
        ns = C.exec_app(source, path, {})
        with pytest.raises(ValueError) as err:
            ns["boom"]()
        last = traceback.extract_tb(err.value.__traceback__)[-1]
        assert (last.filename, last.lineno, last.name) == (path, 10, "boom")


class TestTheCachesAreBounded:

    def test_neither_cache_outgrows_its_maximum(self, monkeypatch):
        monkeypatch.setattr(C, "_APP_CACHE_MAX", 4)
        monkeypatch.setattr(C, "_APP_BLOCK_INFO", {})
        monkeypatch.setattr(C, "_APP_BLOCK_CODE", {})
        for i in range(10):
            C.exec_app("A = %d\nB = A + 1\n" % i, "bound.py", {})
            assert len(C._APP_BLOCK_INFO) <= 4
            assert len(C._APP_BLOCK_CODE) <= 4
        assert C.exec_app("A = 7\nB = A + 1\n", "bound.py", {})["B"] == 8


class TestTheFilenameRewrite:
    """11nov2026: each block's nested code objects are walked once (a plan
    kept per block) and each load only puts its own file name on them."""

    SRC = ("def f():\n    def g():\n        return [x for x in (1, 2)]\n"
           "    return g\n\nclass K:\n    def m(self):\n"
           "        return lambda: 3\n")

    def _all(self, code):
        out = [code]
        for c in code.co_consts:
            if isinstance(c, types.CodeType):
                out += self._all(c)
        return out

    def test_every_nested_code_object_gets_the_file_name(self):
        code = compile(self.SRC, C._APP_PLACEHOLDER, "exec")
        for fn in ("/a/app_1.py", "/b/app_2.py"):
            got = C._app_code_in(code, fn)
            want = compile(self.SRC, fn, "exec")
            assert [c.co_filename for c in self._all(got)] == \
                [fn] * len(self._all(want))
            assert [c.co_name for c in self._all(got)] == \
                [c.co_name for c in self._all(want)]
            assert got == want

    def test_the_plan_is_walked_once_per_block(self):
        code = compile(self.SRC, C._APP_PLACEHOLDER, "exec")
        plan = C._app_code_plan(code)
        assert C._app_code_plan(code) is plan
        # Children before parents; the block itself last.
        assert plan[-1][0] is code
        assert len(plan) == len(self._all(code))

    def test_a_text_without_a_carriage_return_is_read_as_the_import_reads_it(
            self, tmp_path):
        for text in ("X = 'caf\u00e9'\nY = 2\n", "\ufeffX = 'a'\r\nY = 2\r\n",
                     "# -*- coding: latin-1 -*-\nX = 'caf\u00e9'\n"):
            enc = "latin-1" if "latin-1" in text else "utf-8"
            p = tmp_path / "m.py"
            p.write_bytes(text.encode(enc))
            mod = C.load_app(str(p), "_crtest")
            spec = importlib.util.spec_from_file_location("_crref", str(p))
            ref = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ref)
            assert _public(vars(mod)) == _public(vars(ref)), text
            assert (mod.X, getattr(mod, "Y", None)) == \
                (ref.X, getattr(ref, "Y", None)), text
