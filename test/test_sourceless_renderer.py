"""A renderer installed without its source file writes a served app
(WP-32, BUGS.md "A renderer without its source file cannot write a served
app"; GAPS3 K2).

``ServerAppBuilder`` copies the renderer's functions and classes into the
app as their source text (``_dash_source_of``).  Imported from a ``.pyc``
with no ``.py`` beside it, ``inspect.getsource`` has nothing to read and
the build failed with "OSError: source code not available".  Such a build
now writes each copied object as a stub bound to its compiled code, which
travels in the app (``_dash_stub_source``, ``_dash_stub_prelude``): the
app draws the same document, runs only on the Python that wrote it, and a
renderer with its source writes the app as before.
"""
import importlib.util
import os
import py_compile
import shutil
import sys
import warnings

import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import exec_app, load_app  # noqa: E402
from test_date_axis_residuals import _digest  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402


@pytest.fixture(scope="module")
def sourceless(tmp_path_factory):
    """dash_render compiled to a legacy .pyc, its .py removed, imported."""
    d = tmp_path_factory.mktemp("pyc")
    name = "dash_render_sourceless_probe"
    py = d / (name + ".py")
    shutil.copyfile(os.path.join(_ROOT, "dash_render.py"), py)
    for f in os.listdir(_ROOT):
        if f.startswith("dash-") and f.endswith(".scheme"):
            shutil.copyfile(os.path.join(_ROOT, f), d / f)
    pyc = d / (name + ".pyc")
    py_compile.compile(str(py), cfile=str(pyc), doraise=True)
    py.unlink()
    spec = importlib.util.spec_from_file_location(name, str(pyc))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # as an import enters it
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        spec.loader.exec_module(mod)
    yield mod
    sys.modules.pop(name, None)


def _spec():
    return tp._spec(graphs=[
        ("g1", [plot_for("scatter"), plot_for("lfit"), plot_for("lowess")],
         None, {}),
        ("g2", [plot_for("histogram")], None, {})],
        build_options={"filter": "foreign, type(dropdown)"})


def _app(renderer, tmp_path, tag):
    _t, sp, dp = tp._write(_spec())
    out = tmp_path / ("app_%s.py" % tag)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        renderer.ServerAppBuilder(sp, dp).build(str(out))
    return out


def _document(path, tag):
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        load_app(str(path), "_sourceless_app_%s" % tag, draw=False).make_document(doc)
    return doc


class TestASourcelessRendererWritesTheApp:

    def test_its_source_is_gone(self, sourceless):
        import inspect
        with pytest.raises(OSError):
            inspect.getsource(sourceless._fit_grid)

    def test_the_app_draws_the_same_document(self, sourceless, tmp_path):
        stub = _app(sourceless, tmp_path, "stub")
        text = _app(dr, tmp_path, "text")
        assert "_dash_stub_fn(" in stub.read_text(encoding="utf-8")
        a = _document(stub, "stub")
        b = _document(text, "text")
        assert len(a.roots) == len(b.roots) == 1
        assert _digest(a.roots[0]) == _digest(b.roots[0])

    def test_it_runs_only_under_the_python_that_wrote_it(self, sourceless,
                                                          tmp_path):
        src = _app(sourceless, tmp_path, "ver").read_text(encoding="utf-8")
        assert ("_DASH_STUB_PYTHON = %r" % (tuple(sys.version_info[:2]),)
                in src)
        other = src.replace("_DASH_STUB_PYTHON = %r" % (
            tuple(sys.version_info[:2]),), "_DASH_STUB_PYTHON = (3, 1)", 1)
        with pytest.raises(SystemExit, match="Python 3.1"):
            exec_app(other, "<app>", {"__name__": "_ver_probe"})

    def test_a_renderer_with_its_source_writes_text(self, tmp_path):
        src = _app(dr, tmp_path, "plain").read_text(encoding="utf-8")
        assert "_dash_stub_" not in src
        assert "def _fit_grid(" in src

    def test_a_stub_names_the_globals_its_code_reads(self, sourceless):
        sink = {}
        tok = sourceless._DASH_STUB_SINK.set(sink)
        try:
            line = sourceless._dash_source_of(sourceless._fit_grid)
        finally:
            sourceless._DASH_STUB_SINK.reset(tok)
        assert line.startswith("_fit_grid = _dash_stub_fn(")
        assert "_FIT_GRID" in line  # the scan for constants reads it
