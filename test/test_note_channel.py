"""Regression tests for WP-30 P1.26a: dash prints its notes as twoway does.

Measured at c96facd (StataNow 19.5, section 06 Evidence E2): every note the
renderer raised reached Stata as a raw Python warning -- in red, with the
path of ``dash_render.py``, a line number, ``UserWarning`` and a Python
source line.  A session ``warnings`` filter of "ignore" silenced it, and one
of "error" turned it into r(7102) with a 60-line traceback;
``PYTHONWARNINGS=error::UserWarning`` did the same outside Stata.

What these tests pin (ratification item 13, A82/A84):

* ``_dash_smcl_escape`` is the Python twin of Mata ``_dash_smcl_text``:
  braces become SMCL codes, control characters ``?``, NUL is dropped, so
  user text in a note is never read as SMCL (a ``{stata ...}`` link);
* ``_dash_emit_note`` prints one ``(note:  dash: ...)`` line in text colour
  through ``SFIToolkit.errprintln`` (the channel twoway's notes take:
  shown under ``quietly``, hidden by ``capture``), at most 4,000 characters,
  never raising; dash's copies of twoway's own estimator and scheme notes
  print as twoway prints them, through ``displayln``;
* ``_dash_note_scope`` holds the session's filters off dash's notes, prints
  each once, leaves every other warning to those filters, and restores
  ``warnings.filters`` and ``warnings.showwarning`` on any exit;
* the renderer's ``__main__`` block runs ``main()`` inside that scope in
  both build modes, while ``main()`` called directly still warns.

Each test reaches a new name through the module inside the test, so on a
tree without the fix it fails on that test, never at collection.
"""
import json
import os
import runpy
import subprocess
import sys
import threading
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, make_spec  # noqa: E402

_RENDER = os.path.join(_ROOT, "dash_render.py")
_NOTE = "(note:  dash: "


class _Rec:
    """A stand-in ``sfi`` whose ``SFIToolkit`` records what it is asked to
    print: ``("err", s)`` from ``errprintln``, ``("txt", s)`` from
    ``displayln``."""

    def __init__(self):
        self.calls = []
        rec = self

        class SFIToolkit:
            @staticmethod
            def errprintln(s):
                rec.calls.append(("err", s))

            @staticmethod
            def displayln(s):
                rec.calls.append(("txt", s))

        self.SFIToolkit = SFIToolkit


def _spec(tmp_path):
    """A spec with two stable build-time notes (mcolor() and by()'s
    style(econ), which stays named and not drawn; Flipped: WP-31 D10 draws
    by()'s graphregion(), which was the example, and WP-31 D10b its
    shrink, which was the next),
    and its data; returns the two paths."""
    sp = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                     "options": {"mcolor": "notacolor"}}])
    sp["graphs"][0]["graph_options"]["by"] = "foreign, style(econ)"
    df = pd.DataFrame({"mpg": [20.0, 22.0, 30.0, 18.0],
                       "weight": [3000.0, 2500.0, 2000.0, 3500.0],
                       "foreign": [0.0, 0.0, 1.0, 1.0]})
    spec_path = tmp_path / "spec.json"
    data_path = tmp_path / "data.json"
    spec_path.write_text(json.dumps(sp), encoding="utf-8")
    data_path.write_text(json.dumps(make_data_json(df)), encoding="utf-8")
    return str(spec_path), str(data_path)


def _argv(tmp_path, mode):
    sp, dp = _spec(tmp_path)
    out = str(tmp_path / ("o.html" if mode == "standalone" else "o.py"))
    return ["dash_render.py", "--spec", sp, "--data", dp, "--output", out,
            "--mode", mode], out


def _stderr_show(message, category, filename, lineno, file=None, line=None):
    # What Stata's embedded Python does with a warning by default: Python's
    # own format, on stderr (pytest's recorder would hide it otherwise).
    sys.stderr.write(warnings.formatwarning(message, category, filename,
                                            lineno, line))


def _run(tmp_path, mode, flt, monkeypatch, capsys):
    """Run the renderer as dash.ado does (``runpy`` as ``__main__``) under
    the session filter *flt* (``None``: the defaults); return whether the
    output was written, what reached stderr, and whether the session's
    filters and showwarning were the same objects afterwards."""
    argv, out = _argv(tmp_path, mode)
    monkeypatch.setattr(sys, "argv", argv)
    # Outside Stata: no sfi, so a note goes to stderr.
    monkeypatch.setitem(sys.modules, "sfi", None)
    capsys.readouterr()
    with warnings.catch_warnings():
        warnings.showwarning = _stderr_show
        if flt is not None:
            warnings.simplefilter(flt)
        before, copy = warnings.filters, list(warnings.filters)
        show = warnings.showwarning
        runpy.run_path(_RENDER, run_name="__main__")
        restored = (warnings.filters is before
                    and list(warnings.filters) == copy
                    and warnings.showwarning is show)
    return os.path.exists(out), capsys.readouterr().err, restored


def _notes(err):
    return [ln for ln in err.splitlines() if ln.startswith(_NOTE)]


class TestTheSmclEscape:

    def test_braces_become_smcl_codes(self):
        esc = dr._dash_smcl_escape
        assert esc("{stata display 1:x}") == "{c -(}stata display 1:x{c )-}"
        assert esc("a}b{c") == "a{c )-}b{c -(}c"

    def test_control_characters_become_question_marks(self):
        assert dr._dash_smcl_escape("a\x01\x1b[2J\x7f\x85b\x00c") == "a??[2J??bc"

    def test_other_text_is_unchanged(self):
        s = "café % $x \x60q' \"r\" é"
        assert dr._dash_smcl_escape(s) == s
        assert dr._dash_smcl_escape("{a}\x01", braces=False) == "{a}?"


class TestTheNoteLine:

    def test_a_note_is_one_errprintln_in_text_colour(self):
        rec = _Rec()
        got = dr._dash_emit_note("dash: x is odd.", sfi=rec)
        assert rec.calls == [("err", "{txt}(note:  dash: x is odd.)")]
        assert got == "(note:  dash: x is odd.)"

    def test_the_line_is_smcl_escaped(self):
        rec = _Rec()
        dr._dash_emit_note("dash: msymbol({stata display 1:x}) is not a "
                           "symbol.", sfi=rec)
        assert len(rec.calls) == 1
        kind, s = rec.calls[0]
        assert kind == "err"
        assert "{c -(}stata display 1:x{c )-}" in s
        assert "{stata" not in s

    def test_a_note_note_prefix_is_said_once(self):
        rec = _Rec()
        got = dr._dash_emit_note("dash: note: /t/x could not be made private.",
                                 sfi=rec)
        assert got == "(note:  dash: /t/x could not be made private.)"
        assert rec.calls == [("err", "{txt}" + got)]

    def test_twoways_own_text_notes_print_as_text(self):
        for text in ("dash: graph 'g1' plot 2 (lfit): (note:  regress could "
                     "not fit model)",
                     "dash scheme: (note: scheme zz not found, using s2color) "
                     "-- '#include zz' in 'a.scheme'."):
            rec = _Rec()
            dr._dash_emit_note(text, sfi=rec)
            assert rec.calls == [("txt", "{txt}" + text)]
        rec = _Rec()
        text = ("dash: mcolor((note:  regress could not fit model)) is not a "
                "recognised colour; using the scheme's default.")
        dr._dash_emit_note(text, sfi=rec)
        assert rec.calls == [("err", "{txt}(note:  " + text + ")")]

    def test_a_long_note_is_cut_at_4000(self):
        rec = _Rec()
        got = dr._dash_emit_note("x" * 10000, sfi=rec)
        assert len(got) == len("(note:  ") + 4000 + 1
        assert got.endswith("...)")

    def test_outside_stata_one_plain_line_on_stderr(self, monkeypatch, capsys):
        monkeypatch.setitem(sys.modules, "sfi", None)
        capsys.readouterr()
        dr._dash_emit_note("dash: {a}")
        out, err = capsys.readouterr()
        assert err == "(note:  dash: {a})\n"
        assert out == ""

    def test_off_the_main_thread_it_goes_to_stderr(self, capsys):
        rec = _Rec()
        capsys.readouterr()
        t = threading.Thread(target=dr._dash_emit_note,
                             args=("dash: from a thread.",),
                             kwargs={"sfi": rec})
        t.start()
        t.join(30)
        assert rec.calls == []
        assert "(note:  dash: from a thread.)" in capsys.readouterr().err

    def test_it_never_raises(self, capsys):
        class _Raises:
            class SFIToolkit:
                @staticmethod
                def errprintln(s):
                    raise RuntimeError("no Stata here")

        class _Bare:
            pass

        for stand_in in (_Raises, _Bare):
            capsys.readouterr()
            got = dr._dash_emit_note("dash: y.", sfi=stand_in)
            assert got == "(note:  dash: y.)"
            assert capsys.readouterr().err == "(note:  dash: y.)\n"


class TestTheNoteScope:

    def test_an_ignore_filter_hides_no_note(self):
        rec = _Rec()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with dr._dash_note_scope(sfi=rec):
                warnings.warn("dash: a.")
        assert rec.calls == [("err", "{txt}(note:  dash: a.)")]

    def test_an_error_filter_raises_no_note(self):
        rec = _Rec()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with dr._dash_note_scope(sfi=rec):
                warnings.warn("dash: a.")
                warnings.warn("dash kpi: k.", UserWarning)
                warnings.warn("dash scheme: s.", UserWarning)
        assert rec.calls == [("err", "{txt}(note:  dash: a.)"),
                             ("err", "{txt}(note:  dash kpi: k.)"),
                             ("err", "{txt}(note:  dash scheme: s.)")]

    def test_a_note_raised_twice_prints_once(self):
        rec = _Rec()
        with warnings.catch_warnings():
            warnings.simplefilter("default")
            with dr._dash_note_scope(sfi=rec) as said:
                for _ in range(2):
                    warnings.warn("dash: a.")
                warnings.warn("dash: a.")
        assert rec.calls == [("err", "{txt}(note:  dash: a.)")]
        assert said == {"dash: a."}

    def test_other_warnings_keep_the_sessions_filters(self):
        rec = _Rec()
        with warnings.catch_warnings(record=True) as log:
            warnings.simplefilter("ignore")
            with dr._dash_note_scope(sfi=rec):
                warnings.warn("x", FutureWarning)
                warnings.warn("not dash", UserWarning)
        assert rec.calls == [] and log == []
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with dr._dash_note_scope(sfi=rec):
                with pytest.raises(FutureWarning):
                    warnings.warn("x", FutureWarning)
        assert rec.calls == []
        with warnings.catch_warnings(record=True) as log:
            warnings.simplefilter("always")
            with dr._dash_note_scope(sfi=rec):
                warnings.warn("not dash", UserWarning)
        assert rec.calls == []
        assert [str(w.message) for w in log] == ["not dash"]

    def test_the_filters_and_showwarning_are_restored(self):
        rec = _Rec()
        with warnings.catch_warnings():
            before, copy = warnings.filters, list(warnings.filters)
            show = warnings.showwarning
            with dr._dash_note_scope(sfi=rec):
                warnings.warn("dash: a.")
            assert warnings.filters is before
            assert list(before) == copy
            assert warnings.showwarning is show
            for exc in (ValueError, KeyboardInterrupt):
                with pytest.raises(exc):
                    with dr._dash_note_scope(sfi=rec):
                        raise exc("inside")
                assert warnings.filters is before
                assert list(before) == copy
                assert warnings.showwarning is show


MODES = ["standalone", "server"]


class TestTheRendererEntryPoint:

    @pytest.mark.parametrize("mode", MODES)
    def test_an_ignore_filter_hides_no_note(self, mode, tmp_path,
                                            monkeypatch, capsys):
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        _, err, _ = _run(tmp_path / "a", mode, None, monkeypatch, capsys)
        control = _notes(err)
        assert control, "no (note:  dash: line; stderr: %r" % err
        _, err2, _ = _run(tmp_path / "b", mode, "ignore", monkeypatch, capsys)
        assert _notes(err2) == control
        if mode == "server":
            assert any("econ" in n for n in control)

    @pytest.mark.parametrize("mode", MODES)
    def test_an_error_filter_raises_no_note(self, mode, tmp_path,
                                           monkeypatch, capsys):
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        _, err, _ = _run(tmp_path / "a", mode, None, monkeypatch, capsys)
        exists, err2, _ = _run(tmp_path / "b", mode, "error", monkeypatch,
                               capsys)
        assert exists
        assert _notes(err), "no (note:  dash: line; stderr: %r" % err
        assert _notes(err2) == _notes(err)

    @pytest.mark.parametrize("mode", MODES)
    def test_no_path_or_source_line_is_printed(self, mode, tmp_path,
                                              monkeypatch, capsys):
        _, err, _ = _run(tmp_path, mode, None, monkeypatch, capsys)
        for needle in ("UserWarning", "dash_render.py:", "parse_color_alpha("):
            assert needle not in err, (needle, err)
        assert _notes(err), err

    @pytest.mark.parametrize("mode", MODES)
    def test_the_sessions_filters_survive(self, mode, tmp_path, monkeypatch,
                                          capsys):
        for k, flt in enumerate((None, "ignore", "error")):
            (tmp_path / str(k)).mkdir()
            _, _, restored = _run(tmp_path / str(k), mode, flt, monkeypatch,
                                  capsys)
            assert restored, flt

    def test_pythonwarnings_in_the_environment(self, tmp_path):
        argv, out = _argv(tmp_path, "standalone")
        code = ("import json, runpy, sys; sys.argv = json.loads(sys.argv[1]); "
                "runpy.run_path(%r, run_name='__main__')" % _RENDER)
        env = dict(os.environ, PYTHONWARNINGS="error::UserWarning")
        r = subprocess.run([sys.executable, "-c", code, json.dumps(argv)],
                           env=env, cwd=str(tmp_path), capture_output=True,
                           text=True, timeout=180)
        assert r.returncode == 0, r.stderr[-2000:]
        assert _notes(r.stderr), r.stderr
        assert "Traceback" not in r.stderr
        assert os.path.exists(out)

    def test_main_called_directly_still_warns(self, tmp_path):
        """Guard: the scope wraps the ``__main__`` call, never ``main()``,
        so the tests that call ``main()`` or ``render()`` keep seeing dash's
        notes as warnings."""
        sp, dp = _spec(tmp_path)
        out = str(tmp_path / "o.html")
        with pytest.warns(UserWarning, match="econ"):
            dr.main(sp, dp, out)
        assert os.path.exists(out)
