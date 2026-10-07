"""dash.ado compiles the renderer once a session, not once a build (WP-30
test performance, B1).

dash.ado ran ``runpy.run_path(dash_render.py, run_name="__main__")`` for
every build, and run_path compiled the 38,000-line file each time: 0.22 s
of a 0.26 s build (measured 07oct2026 under Stata's Python 3.13), 1,079
times in a certification run and once in every build a user makes.
``_dash_do_render`` and ``_dash_serve`` now run it through
``_dash_run_renderer`` in the module dash already keeps loaded
(``_dash_render_export``, which survives ``clear all``).  It keeps the
compiled code, keyed by the path, its realpath and the SHA-256 of the bytes
read, and runs that code, as run_path ran the file, in a new ``__main__``
every time.

These tests hold it to run_path: the same globals; ``__main__`` and
``argv[0]`` the same while it runs and put back after it, an exception
included; a fresh module every run; the bytes on disk always the bytes
run; what run_path does not compile handed to run_path; and the page the
real renderer writes the same either way.  test_render_log_clean.cscript
RC-01..RC-03 certify the same through Stata.
"""
import builtins
import json
import os
import py_compile
import re
import runpy
import sys

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, make_spec  # noqa: E402

_RENDER = os.path.join(_ROOT, "dash_render.py")

#: What a run sees of itself, recorded at module level.  The annotation
#: tells whether the file was compiled under this module's own
#: ``from __future__ import annotations`` (a string) or as run_path
#: compiles it (the class).
_PROBE = '''\
"""the probe's docstring"""
import sys
SEEN = {
    "name": __name__,
    "file": __file__,
    "argv0": sys.argv[0],
    "main_is_this_run": sys.modules["__main__"].__dict__ is globals(),
    "package": __package__,
    "spec": __spec__,
    "loader": __loader__,
    "cached": __cached__,
    "doc": __doc__,
    "given": globals().get("GIVEN"),
}
def f(x: int):
    return x
ANN = f.__annotations__["x"]
RUNS = globals().get("RUNS", 0) + 1
'''

#: Bokeh's per-run model ids and document UUID, and the CSP's sha256 of
#: each inline script (which carries them): all a page varies by between
#: two renders (test_varlist_expansion.cscript V2-05's normaliser).
_PER_RUN = [
    (re.compile(r"'sha256-[A-Za-z0-9+/]{43}='"), "HASH"),
    (re.compile(r"\bp[0-9]{3,7}\b"), "ID"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "UUID"),
]


def _norm(text):
    for pat, rep in _PER_RUN:
        text = pat.sub(rep, text)
    return text


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return str(path)


@pytest.fixture
def compiles(monkeypatch):
    """An empty code cache, and the paths the helper compiles, in order."""
    monkeypatch.setattr(dr, "_DASH_RENDER_CODE", {})
    seen = []

    def _compile(src, filename, *args, **kwargs):
        seen.append(filename)
        return builtins.compile(src, filename, *args, **kwargs)

    monkeypatch.setattr(dr, "compile", _compile, raising=False)
    return seen


@pytest.fixture
def argv(monkeypatch):
    """dash.ado's argv: the first item is what run_path replaces."""
    a = ["dash_render.py", "--mode", "standalone"]
    monkeypatch.setattr(sys, "argv", list(a))
    return a


class TestTheRendererRun:

    def test_it_runs_the_file_as_run_path_runs_it(self, tmp_path, argv,
                                                  compiles):
        p = _write(tmp_path / "probe.py", _PROBE)
        main = sys.modules["__main__"]
        old = runpy.run_path(p, init_globals={"GIVEN": 7},
                             run_name="__main__")
        new = dr._dash_run_renderer(p, {"GIVEN": 7})
        assert new["SEEN"] == old["SEEN"]
        assert set(new) == set(old)
        assert new["SEEN"] == {
            "name": "__main__", "file": p, "argv0": p,
            "main_is_this_run": True, "package": "", "spec": None,
            "loader": None, "cached": None,
            "doc": "the probe's docstring", "given": 7}
        # Compiled as run_path compiles it: not under this module's
        # `from __future__ import annotations'.
        assert new["ANN"] is int and old["ANN"] is int
        assert sys.modules["__main__"] is main
        assert sys.argv == argv
        assert compiles == [p]

    def test_the_file_is_compiled_once_while_its_bytes_are_unchanged(
            self, tmp_path, argv, compiles):
        p = _write(tmp_path / "probe.py", _PROBE)
        for _ in range(3):
            dr._dash_run_renderer(p)
        assert compiles == [p]
        assert len(dr._DASH_RENDER_CODE) == 1

    def test_every_run_starts_from_a_new_module(self, tmp_path, argv,
                                                compiles):
        p = _write(tmp_path / "probe.py", _PROBE)
        runs = [dr._dash_run_renderer(p) for _ in range(3)]
        # Nothing a run leaves at module level reaches the next: each
        # counts itself the first, and defines its own function.
        assert [r["RUNS"] for r in runs] == [1, 1, 1]
        assert len({id(r["f"]) for r in runs}) == 3
        assert all(r["SEEN"]["main_is_this_run"] for r in runs)

    def test_main_and_argv0_come_back_after_an_error(self, tmp_path, argv,
                                                     compiles):
        p = _write(tmp_path / "boom.py",
                   "import sys\nARGV0 = sys.argv[0]\n"
                   "raise ValueError('boom ' + __name__)\n")
        main = sys.modules["__main__"]
        for run in (lambda: runpy.run_path(p, run_name="__main__"),
                    lambda: dr._dash_run_renderer(p),
                    lambda: dr._dash_run_renderer(p)):
            with pytest.raises(ValueError, match="^boom __main__$"):
                run()
            assert sys.modules["__main__"] is main
            assert sys.argv == argv
        assert compiles == [p]

    def test_a_file_changed_in_place_runs_its_new_bytes(self, tmp_path,
                                                        argv, compiles):
        # Same size and the same modification time: only the bytes tell
        # the two apart, and the bytes are what is run.
        p = _write(tmp_path / "v.py", "X = 1\n")
        st = os.stat(p)
        assert dr._dash_run_renderer(p)["X"] == 1
        _write(p, "X = 2\n")
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
        assert os.stat(p).st_size == st.st_size
        assert os.stat(p).st_mtime_ns == st.st_mtime_ns
        assert dr._dash_run_renderer(p)["X"] == 2
        assert compiles == [p, p]

    def test_a_link_moved_to_another_file_runs_that_file(self, tmp_path,
                                                         argv, compiles):
        a = _write(tmp_path / "a.py", "X = 'a'\n")
        b = _write(tmp_path / "b.py", "X = 'b'\n")
        link = str(tmp_path / "dash_render.py")
        os.symlink(a, link)
        assert dr._dash_run_renderer(link)["X"] == "a"
        os.unlink(link)
        os.symlink(b, link)
        assert dr._dash_run_renderer(link)["X"] == "b"
        # The path dash.ado gave stays the file's name in tracebacks.
        assert dr._dash_run_renderer(link)["__file__"] == link
        assert compiles == [link, link]

    def test_what_run_path_does_not_compile_goes_to_run_path(self, tmp_path,
                                                             argv, compiles):
        # A missing path fails as it did.
        gone = str(tmp_path / "gone.py")
        with pytest.raises(FileNotFoundError):
            runpy.run_path(gone, run_name="__main__")
        with pytest.raises(FileNotFoundError):
            dr._dash_run_renderer(gone)
        # A folder with a __main__.py runs that file, as it did.
        d = tmp_path / "folder"
        d.mkdir()
        _write(d / "__main__.py", "X = 'folder'\n")
        assert dr._dash_run_renderer(str(d))["X"] == "folder"
        # A compiled file runs as compiled code, as it did.
        src = _write(tmp_path / "c_src.py", "X = 'compiled'\n")
        pyc = str(tmp_path / "compiled.py")
        py_compile.compile(src, cfile=pyc, doraise=True)
        assert runpy.run_path(pyc, run_name="__main__")["X"] == "compiled"
        assert dr._dash_run_renderer(pyc)["X"] == "compiled"
        # None of them was compiled here or kept.
        assert compiles == [] and dr._DASH_RENDER_CODE == {}

    def test_the_cache_is_bounded_and_drops_the_oldest(self, tmp_path, argv,
                                                       compiles):
        paths = [_write(tmp_path / ("p%d.py" % k), "X = %d\n" % k)
                 for k in range(dr._DASH_RENDER_CODE_MAX + 2)]
        for p in paths:
            dr._dash_run_renderer(p)
        kept = [k[0] for k in dr._DASH_RENDER_CODE]
        assert kept == paths[-dr._DASH_RENDER_CODE_MAX:]
        # The newest is still compiled once; the oldest is compiled again.
        dr._dash_run_renderer(paths[-1])
        dr._dash_run_renderer(paths[0])
        assert compiles == paths + [paths[0]]

    def test_the_key_is_the_path_its_realpath_and_the_bytes(self, tmp_path,
                                                            argv, compiles):
        p = _write(tmp_path / "k.py", "X = 1\n")
        dr._dash_run_renderer(p)
        (key,) = dr._DASH_RENDER_CODE
        import hashlib
        with open(p, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        assert key == (p, os.path.realpath(p), digest)


class TestTheRealRenderer:

    def test_the_page_is_the_page_run_path_writes(self, tmp_path,
                                                  monkeypatch, compiles):
        """The renderer run through the helper twice, and through run_path
        once, from one spec: one compile, and the same page each time once
        Bokeh's per-run ids and the CSP's script hashes are set aside."""
        sp = make_spec([{"type": "scatter", "yvar": "mpg",
                         "xvar": "weight"}])
        df = pd.DataFrame({"mpg": [20.0, 22.0, 30.0, 18.0],
                           "weight": [3000.0, 2500.0, 2000.0, 3500.0]})
        spec = _write(tmp_path / "spec.json", json.dumps(sp))
        data = _write(tmp_path / "data.json",
                      json.dumps(make_data_json(df)))
        # Outside Stata: no sfi, so a note goes to stderr.
        monkeypatch.setitem(sys.modules, "sfi", None)
        pages = []
        for k, run in enumerate(
                (lambda: runpy.run_path(_RENDER, run_name="__main__"),
                 lambda: dr._dash_run_renderer(_RENDER),
                 lambda: dr._dash_run_renderer(_RENDER))):
            out = str(tmp_path / ("page%d.html" % k))
            monkeypatch.setattr(sys, "argv", [
                "dash_render.py", "--spec", spec, "--data", data,
                "--output", out, "--mode", "standalone"])
            run()
            with open(out, encoding="utf-8") as fh:
                pages.append(fh.read())
        assert compiles == [_RENDER]
        assert "bokeh" in pages[0].lower() and len(pages[0]) > 10000
        assert _norm(pages[1]) == _norm(pages[0])
        assert _norm(pages[2]) == _norm(pages[0])


class TestDashAdoUsesIt:

    def test_no_python_line_of_dash_ado_runs_run_path(self):
        """Both routes go through the helper; run_path, which compiles the
        file on every call, is not called from dash.ado any more."""
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            src = fh.read()
        py = [ln.strip() for ln in src.splitlines()
              if ln.strip().startswith("python:")]
        assert not [ln for ln in py if "runpy" in ln]
        for prog in ("_dash_do_render", "_dash_serve"):
            body = src.split("program define %s\n" % prog, 1)[1]
            body = body.split("\nend\n", 1)[0]
            assert "_dash_xm._dash_run_renderer(" in body, prog
            assert body.index("_dash_xm_load") < \
                body.index("_dash_xm._dash_run_renderer("), prog
