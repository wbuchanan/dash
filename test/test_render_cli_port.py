"""``--port`` never reached the generated app.

``dash_render.py``'s ``__main__`` parses ``--port`` and then calls
``main(args.spec, args.data, args.output, args.mode)`` — four arguments, no
port. ``main`` therefore called ``builder.build(output_path)``
with the default, and every generated app embedded ``_port = 5006`` whatever
the user asked for.

`dash serve` did not notice, because it passes ``--port`` again to the app it
launches and the app's own argparse overrides the embedded value. The command
that does notice is the documented non-blocking one::

    . dash build, saving(app.py) server
    . * Run outside Stata:  python app.py

which serves on 5006 regardless.
"""
import os
import subprocess
import sys
import tempfile

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import json

import dash_render as dr
from conftest import make_data_json

_DF = pd.DataFrame({"mpg": [22.0, 18.0, 25.0],
                    "weight": [2930.0, 3350.0, 2200.0]})

_SPEC = {
    "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                "plots": [{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight", "options": {}}],
                "options": {}}],
    "kpis": [],
    "build_options": {"layout": "auto", "registry": "g1", "level": "95",
                      "formats": {}},
}


def _bound_port(source: str, monkeypatch, argv=("app.py",)) -> int:
    """The port the generated app, run as ``python app.py``, hands the
    server -- read from the launcher itself, with bokeh's Server replaced
    by a recorder so nothing listens.

    These tests used to read the ``_port = N`` line out of the app's text.
    That line is the parser's default; what reaches the socket is the
    launcher's own reading of it, which it clamps again, so the text could
    say one port while the app bound another (WP-24)."""
    import warnings
    import bokeh.server.server as bss
    seen = {}

    class _Loop:
        def add_callback(self, fn, *a):
            pass

        def call_later(self, delay, fn):
            pass

        def start(self):
            pass

        def stop(self):
            pass

    class _Server:
        def __init__(self, apps, **kw):
            seen["kw"] = kw
            self.io_loop = _Loop()

        def start(self):
            pass

        def show(self, *a):
            pass

        def stop(self):
            pass

    monkeypatch.setattr(bss, "Server", _Server)
    monkeypatch.setattr(sys, "argv", list(argv))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec(compile(source, "app.py", "exec"), {"__name__": "__main__"})
    assert "kw" in seen, "the launcher never built a server"
    return int(seen["kw"]["port"])


def _write_inputs(tmp_path):
    spec = tmp_path / "spec.json"
    data = tmp_path / "data.json"
    spec.write_text(json.dumps(_SPEC))
    data.write_text(json.dumps(make_data_json(_DF)))
    return str(spec), str(data)


class TestPortReachesTheGeneratedApp:
    def test_the_cli_port_is_embedded(self, tmp_path, monkeypatch):
        spec, data = _write_inputs(tmp_path)
        out = tmp_path / "app.py"
        r = subprocess.run(
            [sys.executable, os.path.join(_ROOT, "dash_render.py"),
             "--spec", spec, "--data", data, "--output", str(out),
             "--mode", "server", "--port", "8123"],
            capture_output=True, text=True, timeout=180,
        )
        assert r.returncode == 0, r.stderr
        assert _bound_port(out.read_text(), monkeypatch) == 8123

    def test_the_default_is_still_5006(self, tmp_path, monkeypatch):
        spec, data = _write_inputs(tmp_path)
        out = tmp_path / "app2.py"
        r = subprocess.run(
            [sys.executable, os.path.join(_ROOT, "dash_render.py"),
             "--spec", spec, "--data", data, "--output", str(out),
             "--mode", "server"],
            capture_output=True, text=True, timeout=180,
        )
        assert r.returncode == 0, r.stderr
        assert _bound_port(out.read_text(), monkeypatch) == 5006

    def test_a_port_in_build_options_still_wins_for_the_ado_path(
            self, tmp_path, monkeypatch):
        """build_options['port'] is the older route and must keep working."""
        spec = tmp_path / "spec3.json"
        data = tmp_path / "data3.json"
        s = json.loads(json.dumps(_SPEC))
        s["build_options"]["port"] = "9001"
        spec.write_text(json.dumps(s))
        data.write_text(json.dumps(make_data_json(_DF)))
        out = tmp_path / "app3.py"
        dr.main(str(spec), str(data), str(out), mode="server",
                            port=7777)
        assert _bound_port(out.read_text(), monkeypatch) == 9001

    def test_main_takes_a_port(self, tmp_path, monkeypatch):
        spec, data = _write_inputs(tmp_path)
        out = tmp_path / "app4.py"
        dr.main(spec, data, str(out), mode="server", port=8500)
        assert _bound_port(out.read_text(), monkeypatch) == 8500

    def test_an_out_of_range_port_is_refused_not_embedded(
            self, tmp_path, monkeypatch):
        """GAPS2 F1: a port below 1024 or above 65535 used to be clamped
        to the nearest bindable one -- so `python app.py --port 80' served
        on 1024, silently -- instead of being refused.  Whatever main() is
        handed, it now raises and writes nothing."""
        import argparse
        spec, data = _write_inputs(tmp_path)
        for given in (99999, 80):
            out = tmp_path / ("app5_%d.py" % given)
            with pytest.raises(argparse.ArgumentTypeError):
                dr.main(spec, data, str(out), mode="server", port=given)
            assert not out.exists(), given

    def test_an_out_of_range_port_in_build_options_is_refused_too(
            self, tmp_path, monkeypatch):
        """build_options['port'] takes the other road into the app: the
        builder used to read it with int() alone, not through main()'s
        clamp (WP-24), and pass it straight through unbound-checked.  It
        now raises the same way (GAPS2 F1)."""
        import argparse
        data = tmp_path / "data6.json"
        data.write_text(json.dumps(make_data_json(_DF)))
        for given in ("99999", "80"):
            spec = tmp_path / ("spec6_%s.json" % given)
            s = json.loads(json.dumps(_SPEC))
            s["build_options"]["port"] = given
            spec.write_text(json.dumps(s))
            out = tmp_path / ("app6_%s.py" % given)
            with pytest.raises(argparse.ArgumentTypeError):
                dr.main(str(spec), str(data), str(out), mode="server")
            assert not out.exists(), given
