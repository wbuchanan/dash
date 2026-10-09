"""The served app's notes reach the Stata session that asked for them
(WP-30 P1.26b, M6).

* ``dash build, server`` printed none of the notes ``dash build`` prints for
  the same graphs: the app decides them when a session draws.  The build now
  draws the app once (``_dash_trial_render``) and raises what it noted.
* The app run on its own (``python app.py``, ``bokeh serve``, ``dash
  serve``'s child) printed each note as a Python warning with its path, and
  ``PYTHONWARNINGS=error`` failed the session; ``_dash_app_note_hook`` prints
  each once as ``(note:  dash: ...)``.
* A layer whose own ``if``/``in`` keeps no row is drawn in silence in both
  modes, as twoway draws it (M6); twoway's estimator note stays.

The relay of ``dash serve``'s child is tested in test_serve_launcher.py.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import warnings

import pytest
from bokeh.document import Document
from bokeh.io import curdoc
from bokeh.io.doc import patch_curdoc

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from test_server_layer_defects import (make_spec, plot_for, served,
                                       standalone, _write)

_SPEC = make_spec([
    plot_for("scatter", {"mcolor": "notacolor", "msymbol": "weird"}),
    plot_for("lfit", if_expr="price > 20000"),
    plot_for("bar", if_expr="price > 20000"),
])
_SPEC_BY = make_spec(_SPEC["graphs"][0]["plots"],
                     graph_options={"by": "foreign, graphregion(color(red))"})
_TORNADO = ("tornado.access", "tornado.general", "tornado.application")


def _record(fn, *a, **k):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fn(*a, **k)
    return sorted(str(w.message) for w in caught)


def _saved(tmp_path, spec):
    return sorted(standalone(tmp_path, spec)[2])


def _built(tmp_path, spec, trial, builder=None):
    _, sp, dp = _write(tmp_path, spec)
    b = builder(sp, dp) if builder else dr.ServerAppBuilder(sp, dp)
    ap = str(tmp_path / "app.py")
    return _record(b.build, ap, private=False, trial=trial), ap


@pytest.fixture
def no_holder(monkeypatch):
    monkeypatch.delitem(sys.modules, "_dash_app_notes", raising=False)
    monkeypatch.setitem(sys.modules, "sfi", None)


class TestTheServerBuildNamesTheSavedNotes:
    def test_main_names_what_the_saved_build_names(self, tmp_path):
        """by() adds the planner's build-time note to the session's."""
        saved = _saved(tmp_path, _SPEC_BY)
        assert len([w for w in saved if w.startswith("dash: ")]) >= 3, saved
        _, sp, dp = _write(tmp_path, _SPEC_BY)
        got = _record(dr.main, sp, dp, str(tmp_path / "a.py"), mode="server")
        assert got == saved


class TestTheTrial:
    def test_a_build_without_the_trial_is_unchanged(self, tmp_path):
        got, _ = _built(tmp_path, _SPEC, False)
        assert not [w for w in got if "mcolor" in w], got

    def test_the_trial_leaves_the_session_as_it_found_it(self, tmp_path,
                                                         monkeypatch):
        # A served app run earlier in this worker installs the holder;
        # the trial must not.
        monkeypatch.delitem(sys.modules, "_dash_app_notes", raising=False)

        def snap():
            return (warnings.showwarning, list(warnings.filters),
                    len(curdoc().roots),
                    [list(logging.getLogger(n).filters) for n in _TORNADO],
                    "_dash_app_notes" in sys.modules)
        with warnings.catch_warnings():
            before = snap()
            got, _ = _built(tmp_path, _SPEC, True)
            after = snap()
        assert [w for w in got if "mcolor" in w], got
        assert after == before
        assert before[4] is False

    def test_a_session_error_filter_does_not_fail_the_trial(self, tmp_path):
        said = []

        class _Tk:
            @staticmethod
            def errprintln(s):
                said.append(s)
            displayln = errprintln

        class _Sfi:
            SFIToolkit = _Tk
        _, sp, dp = _write(tmp_path, _SPEC)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with dr._dash_note_scope(sfi=_Sfi):
                dr.ServerAppBuilder(sp, dp).build(
                    str(tmp_path / "a.py"), trial=True)
        assert len([s for s in said if "mcolor(notacolor)" in s]) == 1, said
        assert len([s for s in said if "msymbol(weird)" in s]) == 1, said

    def test_a_trial_that_raises_is_one_note_and_the_app_is_written(
            self, tmp_path, monkeypatch):
        real = dr.ServerAppBuilder._generate_app_source
        head = "\ndef make_document(doc):\n"

        def broken(self, port):
            src = real(self, port)
            assert src.count(head) == 1
            return src.replace(head, head + "    raise RuntimeError('probe')\n")
        monkeypatch.setattr(dr.ServerAppBuilder, "_generate_app_source",
                            broken)
        got, ap = _built(tmp_path, _SPEC, True)
        bad = [w for w in got if "could not draw this dashboard" in w]
        assert len(bad) == 1 and "RuntimeError: probe" in bad[0], got
        assert os.path.isfile(ap)
        assert curdoc() is not None


class TestTheAppNoteHook:
    def test_each_note_prints_once_per_process(self, capsys, no_holder):
        with warnings.catch_warnings():
            dr._dash_app_note_hook()
            for _ in range(3):
                warnings.warn("dash: a.")
            warnings.warn("dash: b.")
        assert capsys.readouterr().err.splitlines() == [
            "(note:  dash: a.)", "(note:  dash: b.)"]

    def test_it_is_installed_once(self, capsys, no_holder):
        with warnings.catch_warnings():
            h = dr._dash_app_note_hook()
            hook = warnings.showwarning
            assert dr._dash_app_note_hook() is h
            assert warnings.showwarning is hook
            warnings.warn("dash: a.")
            with warnings.catch_warnings():
                warnings.showwarning = lambda *a, **k: None
                assert dr._dash_app_note_hook() is h
                assert warnings.showwarning is not hook
                assert "dash: a." in h.said
                warnings.warn("dash: a.")
        assert capsys.readouterr().err.splitlines() == ["(note:  dash: a.)"]

    def test_other_warnings_go_to_the_previous_hook(self, capsys, no_holder):
        seen = []
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            warnings.showwarning = (
                lambda m, c, f, l, file=None, line=None: seen.append(str(m)))
            dr._dash_app_note_hook()
            warnings.warn("x", FutureWarning)
            warnings.warn("not dash")
            warnings.warn("dash: a.")
        assert seen == ["x", "not dash"]

    def test_an_error_filter_raises_no_note(self, capsys, no_holder):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            dr._dash_app_note_hook()
            warnings.warn("dash kpi: k.")
            with pytest.raises(FutureWarning):
                warnings.warn("x", FutureWarning)
        assert capsys.readouterr().err.splitlines() == [
            "(note:  dash kpi: k.)"]


_DRIVER = r"""
import sys, types
from bokeh.document import Document
src = open(sys.argv[1], encoding="utf-8").read()
mod = types.ModuleType("bokeh_app_probe")
exec(compile(src, sys.argv[1], "exec"), mod.__dict__)
mod.make_document(Document())
mod.make_document(Document())
"""


class TestTheGeneratedApp:
    def test_an_app_process_prints_each_note_once_under_pythonwarnings_error(
            self, tmp_path):
        _, ap = _built(tmp_path, _SPEC, False)
        r = subprocess.run(
            [sys.executable, "-c", _DRIVER, ap],
            env=dict(os.environ, PYTHONWARNINGS="error::UserWarning"),
            capture_output=True, text=True, timeout=180)
        err = r.stderr.splitlines()
        assert r.returncode == 0, r.stderr[-2000:]
        assert len([l for l in err if l.startswith("(note:  dash: mcolor(notacolor)")]) == 1, err
        assert len([l for l in err if l.startswith("(note:  dash: msymbol(weird)")]) == 1, err
        assert err.count("dash: graph 'g1' plot 2 (lfit): "
                         "(note:  regress could not fit model)") == 1, err
        for bad in ("UserWarning", "Traceback", ".py:"):
            assert bad not in r.stderr, r.stderr

    def test_an_imported_app_installs_no_hook(self, tmp_path, monkeypatch):
        monkeypatch.delitem(sys.modules, "_dash_app_notes", raising=False)
        _, ap = _built(tmp_path, _SPEC, False)
        src = open(ap, encoding="utf-8").read()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            hook = warnings.showwarning
            doc = Document()  # patch_curdoc holds it by weak reference
            with patch_curdoc(doc):
                exec(compile(src, ap, "exec"), {"__name__": "_probe_import"})
            assert warnings.showwarning is hook
        assert "_dash_app_notes" not in sys.modules

    def test_the_trial_flag_installs_nothing(self, tmp_path, monkeypatch):
        for n in _TORNADO:
            lg = logging.getLogger(n)
            monkeypatch.setattr(lg, "filters", [
                f for f in lg.filters
                if not getattr(f, "_dash_redacts_queries", False)])
        before = [list(logging.getLogger(n).filters) for n in _TORNADO]
        monkeypatch.delitem(sys.modules, "_dash_app_notes", raising=False)

        class _Fallback(dr.ServerAppBuilder):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                self.scheme.is_fallback = True
        _, ap = _built(tmp_path, _SPEC, False, builder=_Fallback)
        src = open(ap, encoding="utf-8").read()
        assert "_DASH_SCHEME_IS_FALLBACK = True" in src
        throwaway = Document()
        roots = len(curdoc().roots)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            hook = warnings.showwarning
            with patch_curdoc(throwaway):
                exec(compile(src, ap, "exec"),
                     {"__name__": "bokeh_app_probe", "_DASH_TRIAL": True})
            assert warnings.showwarning is hook
        assert [list(logging.getLogger(n).filters) for n in _TORNADO] == before
        assert "_dash_app_notes" not in sys.modules
        assert not [w for w in caught
                    if "no .scheme file" in str(w.message)]
        assert len(curdoc().roots) == roots
        assert throwaway.roots


class TestAnEmptiedOwnQualifierIsSilent:
    def test_both_modes_are_silent_and_keep_the_estimator_note(
            self, tmp_path):
        """One spec per layer family (source-filtered bar and line, range,
        pc, spike); each also holds an own-if lfit, whose twoway note
        stays (M6)."""
        bad = []
        for t in ("bar", "line", "rarea", "pcspike", "spike"):
            spec = make_spec([plot_for("scatter"),
                              plot_for(t, if_expr="price > 20000"),
                              plot_for("lfit", if_expr="price > 20000")])
            for mode, got in (("saved", standalone(tmp_path, spec)[2]),
                              ("served", served(tmp_path, spec)[2])):
                if [w for w in got if "drew nothing" in w]:
                    bad.append((t, mode, got))
                if len([w for w in got if "(note:  regress could not fit "
                        "model)" in w]) != 1:
                    bad.append((t, mode, "estimator note", got))
        assert not bad, bad
