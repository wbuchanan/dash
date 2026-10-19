"""The verified bokeh window (WP-30 P1.30, M9, A104-A107).

The defect (DROPIN-REMAINING.md P1.30, GAPS2 H4b-e, I7, K5): dash_setup
installed ``bokeh>=3.8`` with no ceiling, which pip resolved to the
unverified 3.10.0; nothing read ``bokeh.__version__`` at run time, so a
bokeh newer than the text sinks were checked on drew with no word and one
older than the floor rendered with unknown behaviour; the text-sink
verification was pinned to two exact patch releases.

Now one window, ``bokeh>=3.8,<3.10``, is declared once
(``_DASH_BOKEH_FLOOR``, ``_DASH_BOKEH_CEIL``, ``_DASH_BOKEH_VERIFIED``;
dash_setup.ado's ``min_bokeh``/``max_bokeh``).  "Verified" means
major.minor (A104).  Below the floor every route refuses naming
dash_setup; above the window every route notes once and draws.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

# Bokeh reads its own version when bokeh.resources is first imported
# (SRI hashes); every patch below comes after these imports.
import bokeh  # noqa: E402
import bokeh.embed  # noqa: E402,F401
import bokeh.models  # noqa: E402,F401
import bokeh.plotting  # noqa: E402,F401
import bokeh.resources  # noqa: E402,F401
import bokeh.server.server  # noqa: E402,F401
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import curdoc  # noqa: E402

import dash_render as dr  # noqa: E402
from conftest import _BASELINES, load_app, make_data_json, make_spec  # noqa: E402

#: The ceiling this section fixed: bokeh 3.10 was not verified in WP-30
#: (no scratch-venv download), so the window ends before it.
CEIL = "3.10"
SPEC = "bokeh>=3.8,<%s" % CEIL


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def _files():
    df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 12),
                       "weight": np.linspace(1760.0, 4840.0, 12)})
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}])
    d = tempfile.mkdtemp(prefix="dash_bkw_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(df), fh)
    return d, sp, dp


@pytest.fixture(scope="module")
def app():
    """One generated app, built once for the module."""
    d, sp, dp = _files()
    op = os.path.join(d, "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    return op


_BOOT = """\
import os, runpy, sys
import bokeh, bokeh.embed, bokeh.resources, bokeh.plotting, bokeh.models
import bokeh.server.server
bokeh.__version__ = %r
app = %r
sys.argv = [app] + sys.argv[1:]
sys.path[0] = os.path.dirname(app)
runpy.run_path(app, run_name="__main__")
"""


def _boot(tmp_path, app_path, v):
    """A script that runs *app_path* as ``python app.py`` under bokeh *v*."""
    p = tmp_path / ("boot_%s.py" % v.replace(".", "_"))
    p.write_text(_BOOT % (v, app_path))
    return str(p)


def _notes(text, v):
    return [l for l in text.splitlines()
            if l.startswith("(note:  dash: bokeh %s" % v)]


class TestTheWindowVerdict:

    def test_each_version_gets_its_verdict(self):
        rows = {"2.4.3": "below", "3.7.3": "below", "3.8.0": "verified",
                "3.8.2": "verified", "3.9.0": "verified",
                "3.9.2": "verified", "3.9.0rc1": "verified",
                "3.10.0": "above", "3.10.0rc1": "above",
                "3.10.0.dev2": "above", "4.0.0": "above", "": "unknown",
                "x": "unknown", "3": "unknown", None: "unknown",
                "9" * 10000: "unknown"}
        bad = {v if v is None else v[:12]: (dr._dash_bokeh_window(v), want)
               for v, want in rows.items()
               if dr._dash_bokeh_window(v) != want}
        assert not bad, bad

    def test_the_constants_are_one_window(self):
        ver = list(dr._DASH_BOKEH_VERIFIED)
        assert dr._DASH_BOKEH_FLOOR == ver[0]
        assert all(b == (a[0], a[1] + 1) for a, b in zip(ver, ver[1:])), ver
        assert dr._DASH_BOKEH_CEIL == (ver[-1][0], ver[-1][1] + 1)
        assert "%d.%d" % dr._DASH_BOKEH_CEIL == CEIL


class TestTheWindowIsDeclaredOnce:

    def test_every_tested_pin_lies_inside_dash_setups_windows(self):
        """WP-32 (I3, the maintainer's ruling): dash_setup installs numpy
        and pandas below a ceiling too, the minor after the newest the
        suites run under, so the lock it installs from pins what was
        tested; every pin of test/requirements-*.txt lies inside."""
        ado = _read("dash_setup.ado")
        for pkg in ("bokeh", "numpy", "pandas"):
            lo = re.search(r'local\s+min_%s\s+"([0-9.]+)"' % pkg, ado).group(1)
            hi = re.search(r'local\s+max_%s\s+"([0-9.]+)"' % pkg, ado).group(1)
            pins = []
            for name in ("requirements-stata.txt", "requirements-dev.txt"):
                pins += [tuple(int(x) for x in l.split("==")[1].split("."))
                         for l in _read(os.path.join("test", name)).splitlines()
                         if l.startswith(pkg + "==")]
            lo, hi = (tuple(int(x) for x in v.split(".")) for v in (lo, hi))
            assert pins and all(lo <= p[:2] < hi for p in pins), (pkg, pins)
            # The ceiling is the minor after the newest tested one.
            newest = max(pins)
            assert hi == (newest[0], newest[1] + 1), (pkg, hi, newest)

    def test_every_declaration_names_the_window(self):
        """dash.pkg and dash.sthlp's Dependencies line are held by
        test_version_floor.py; the rest here."""
        floor = "%d.%d" % dr._DASH_BOKEH_FLOOR
        ado = _read("dash_setup.ado")
        assert re.search(r'local\s+min_bokeh\s+"%s"' % floor, ado)
        assert re.search(r'local\s+max_bokeh\s+"%s"' % CEIL, ado)
        sh = _read("dash_setup.sthlp")
        assert "{opt bokeh}}%s or later, before %s" % (floor, CEIL) in sh
        # Flipped (WP-32, I3): the hash-checked line names the lock, whose
        # bokeh pin test_requirements_lock.py holds to the window.
        pips = [l for l in sh.splitlines() if "-m pip install" in l
                and "--require-hashes -r" not in l]
        assert len(pips) == 3 and all('"%s"' % SPEC in l for l in pips), pips
        assert '"%s"' % SPEC in _read("scripts/floor_matrix.sh")
        import test_label_sinks
        verified = {"%d.%d" % p for p in dr._DASH_BOKEH_VERIFIED}
        assert test_label_sinks.VERIFIED_BOKEH == verified
        assert all(b["bokeh"] in verified for b in _BASELINES.values())
        for name in ("requirements-stata.txt", "requirements-dev.txt"):
            lines = _read(os.path.join("test", name)).splitlines()
            win = [l for l in lines if l.startswith("# bokeh window")]
            assert len(win) == 1 and SPEC in win[0], (name, win)
            pin = [l.split("==")[1] for l in lines
                   if l.startswith("bokeh==")]
            assert dr._dash_bokeh_window(pin[0]) == "verified", (name, pin)


class TestTheRuntimeCheck:

    def test_below_the_floor_is_refused_naming_dash_setup(self, monkeypatch,
                                                          tmp_path):
        monkeypatch.setattr(bokeh, "__version__", "3.7.3")
        refusal, note = dr._dash_bokeh_check()
        assert note == ""
        for word in ("bokeh 3.7.3", "3.8", "dash_setup"):
            assert word in refusal, refusal
        assert dr._dash_dep_versions()[0] == refusal
        _d, sp, dp = _files()
        out = tmp_path / "page.html"
        with pytest.raises(RuntimeError) as err:
            dr.main(sp, dp, str(out))
        assert str(err.value) == refusal
        assert not out.exists()

    @pytest.mark.parametrize("mode", ["standalone", "server"])
    def test_above_the_window_is_one_note_and_the_page_is_written(
            self, monkeypatch, tmp_path, mode):
        _d, sp, dp = _files()
        out = tmp_path / ("page.html" if mode == "standalone" else "app.py")
        monkeypatch.setattr(bokeh, "__version__", "3.10.0")
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                dr.main(sp, dp, str(out), mode=mode)
        finally:
            curdoc().clear()
        assert out.exists()
        mine = [str(w.message) for w in caught
                if str(w.message).startswith("dash: bokeh")]
        assert len(mine) == 1, mine
        assert mine[0].startswith("dash: bokeh 3.10.0 ")
        assert "(3.8, 3.9)" in mine[0] and "dash_setup" in mine[0]
        assert dr._dash_bokeh_check("3.9.0") == ("", "")

    def test_each_verdict_gets_its_message(self):
        hostile = "3.10.0\x1b[31m{res}" + "9" * 60
        _r, note = dr._dash_bokeh_check(hostile)
        shown = note.split("dash: bokeh ", 1)[1].split(" is newer")[0]
        assert len(shown) <= 40 and all(c.isprintable() for c in note), note
        _r, unknown = dr._dash_bokeh_check("x")
        assert _r == "" and "could not be read" in unknown
        assert "dash_setup" in unknown


class TestTheServedAppChecksAtStart:

    def test_the_app_carries_the_window(self, app):
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        check = src.index("_dash_bk_refuse, _dash_bk_note = _dash_bokeh_check()")
        assert check < src.index("if __name__ != '__main__':")
        try:
            mod = load_app(app, "dash_bkw_app")
        finally:
            curdoc().clear()
        for name in ("_DASH_BOKEH_FLOOR", "_DASH_BOKEH_CEIL",
                     "_DASH_BOKEH_VERIFIED"):
            assert getattr(mod, name) == getattr(dr, name), name
        for v in ("3.7.3", "3.9.1", "3.10.0", "x"):
            assert mod._dash_bokeh_check(v) == dr._dash_bokeh_check(v), v

    @pytest.mark.serve
    def test_python_app_py_below_the_floor_stops(self, app, tmp_path):
        from test_server_serves import TEST_TOKEN, _free_port
        p = subprocess.Popen(
            [sys.executable, _boot(tmp_path, app, "3.7.3"), "--port",
             str(_free_port())], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
            env=dict(os.environ, DASH_SERVE_TOKEN=TEST_TOKEN))
        try:
            out, err = p.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            p.kill()
            out, err = p.communicate()
        assert p.returncode == 1, (p.returncode, err[-2000:])
        assert dr._dash_bokeh_check("3.7.3")[0] in err
        assert "running" not in (out + err).lower()

    @pytest.mark.serve
    def test_python_app_py_above_the_window_notes_once_and_serves(
            self, app, tmp_path):
        from test_server_serves import _Launched
        srv = _Launched(_boot(tmp_path, app, "3.10.0"))
        with srv:
            assert srv.get("/health")[0] == 200
        out = srv.proc.stdout.read()
        assert len(_notes(out, "3.10.0")) == 1, out[-3000:]

    def test_bokeh_serve_notes_once_and_refuses_below_the_floor(
            self, app, monkeypatch, capsys):
        monkeypatch.delitem(sys.modules, "_dash_app_notes", raising=False)
        monkeypatch.setattr(bokeh, "__version__", "3.10.0")
        try:
            with warnings.catch_warnings():
                load_app(app, "bokeh_app_a")
                curdoc().clear()
                load_app(app, "bokeh_app_b")
        finally:
            curdoc().clear()
            sys.modules.pop("_dash_app_notes", None)
        assert len(_notes(capsys.readouterr().err, "3.10.0")) == 1
        monkeypatch.setattr(bokeh, "__version__", "3.7.3")
        try:
            with warnings.catch_warnings():
                with pytest.raises(RuntimeError) as err:
                    load_app(app, "bokeh_app_c")
            assert str(err.value) == dr._dash_bokeh_check("3.7.3")[0]
            assert curdoc().roots == []
        finally:
            curdoc().clear()
            sys.modules.pop("_dash_app_notes", None)

    def test_dash_serve_prints_the_note_once(self):
        """dash serve's scope records main()'s note in said=, and the
        relay skips the child's line only if it reads back the same text."""
        note = dr._dash_bokeh_check("3.10.0")[1]
        assert dr._dash_relay_kind("(note:  " + note + ")") == (
            "note", note, False)
