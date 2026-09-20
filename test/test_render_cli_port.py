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
import re
import subprocess
import sys
import tempfile

import pandas as pd

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


def _embedded_port(source: str) -> int:
    m = re.search(r"^_port = (\d+)$", source, re.MULTILINE)
    assert m, "the generated app has no _port literal"
    return int(m.group(1))


def _write_inputs(tmp_path):
    spec = tmp_path / "spec.json"
    data = tmp_path / "data.json"
    spec.write_text(json.dumps(_SPEC))
    data.write_text(json.dumps(make_data_json(_DF)))
    return str(spec), str(data)


class TestPortReachesTheGeneratedApp:
    def test_the_cli_port_is_embedded(self, tmp_path):
        spec, data = _write_inputs(tmp_path)
        out = tmp_path / "app.py"
        r = subprocess.run(
            [sys.executable, os.path.join(_ROOT, "dash_render.py"),
             "--spec", spec, "--data", data, "--output", str(out),
             "--mode", "server", "--port", "8123"],
            capture_output=True, text=True, timeout=180,
        )
        assert r.returncode == 0, r.stderr
        assert _embedded_port(out.read_text()) == 8123

    def test_the_default_is_still_5006(self, tmp_path):
        spec, data = _write_inputs(tmp_path)
        out = tmp_path / "app2.py"
        r = subprocess.run(
            [sys.executable, os.path.join(_ROOT, "dash_render.py"),
             "--spec", spec, "--data", data, "--output", str(out),
             "--mode", "server"],
            capture_output=True, text=True, timeout=180,
        )
        assert r.returncode == 0, r.stderr
        assert _embedded_port(out.read_text()) == 5006

    def test_a_port_in_build_options_still_wins_for_the_ado_path(
            self, tmp_path):
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
        assert _embedded_port(out.read_text()) == 9001

    def test_main_takes_a_port(self, tmp_path):
        spec, data = _write_inputs(tmp_path)
        out = tmp_path / "app4.py"
        dr.main(spec, data, str(out), mode="server", port=8500)
        assert _embedded_port(out.read_text()) == 8500

    def test_an_out_of_range_port_is_clamped_not_embedded_raw(self, tmp_path):
        """A port below 1024 or above 65535 cannot be bound."""
        spec, data = _write_inputs(tmp_path)
        out = tmp_path / "app5.py"
        dr.main(spec, data, str(out), mode="server", port=99999)
        assert 1024 <= _embedded_port(out.read_text()) <= 65535
