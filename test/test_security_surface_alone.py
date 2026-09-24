"""test_security_surface.py must work run on its own, in any order.

Its helpers imported ``make_data_json`` from conftest before test/ was on
sys.path: ``_build_served_module`` imported first and inserted test/ after,
and the hostile-bgcolor test inserted the repository root instead.  Each
therefore worked only when an earlier test in the same process had put
test/ there.  The full suite always had one; ``python3 -m pytest
test/test_security_surface.py`` run alone did not, and under xdist every
worker whose first test built a served app failed with
``ModuleNotFoundError: No module named 'conftest'`` -- 26 tests, measured
23sep2026 at 4ede074 and 68327a8 (25 under ``-n 4``), while a serial run,
whose first test happened to insert test/, passed.  The file now puts test/
on the path once, at the top, before it imports conftest.

The helper runs here as such a worker ran it: in a fresh interpreter no
earlier test has touched, with the module loaded from its file and the
working directory somewhere else, so no ordering can mask it.
"""
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SUBJECT = os.path.join(_HERE, "test_security_surface.py")

# Load the module from its file, then build a served app through the helper
# 25 of its tests share.  Loading runs the module's own imports -- conftest
# among them -- and the build runs the helper's.
_PROBE = (
    "import importlib.util, pathlib, sys\n"
    "spec = importlib.util.spec_from_file_location('_sec_alone', sys.argv[1])\n"
    "m = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(m)\n"
    "plot = {'type': 'scatter', 'yvar': 'y', 'xvar': 'x', 'options': {}}\n"
    "app = m._build_served_module(pathlib.Path(sys.argv[2]),\n"
    "                             m._sec_spec([plot]), m._sec_df())\n"
    "print('BUILT', callable(getattr(app, 'make_document', None)))\n"
)


def test_its_served_app_helper_needs_no_earlier_test(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE, _SUBJECT, str(tmp_path)],
        cwd=str(tmp_path), env=env, capture_output=True, text=True,
        timeout=300)
    assert proc.returncode == 0 and "BUILT True" in proc.stdout.split("\n"), (
        f"test_security_surface.py's helper needs an earlier test to have "
        f"set sys.path up: rc {proc.returncode}\n{proc.stdout[-500:]}\n"
        f"{proc.stderr[-2000:]}")
