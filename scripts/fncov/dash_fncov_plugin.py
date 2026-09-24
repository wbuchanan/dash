"""pytest plugin: record the functions of dash_render.py the suite executes.

Loaded by ``scripts/fncov/run_fncov.sh`` as ``-p dash_fncov_plugin`` (with
``scripts/fncov`` on ``PYTHONPATH``); never loaded by default, and it does
nothing unless ``DASH_FNCOV_DIR`` names an output directory.

It starts ``dash_fncov_recorder`` in this process at import time -- before
``test/conftest.py`` imports dash_render -- and puts ``site/`` on the
``PYTHONPATH`` every child inherits, so each pytest-xdist worker and each
Python subprocess a test launches starts the recorder too (see
``site/usercustomize.py``).  The recorder's docstring says what is written;
``fncov_report.py`` reads it.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import dash_fncov_recorder as _rec  # noqa: E402


def _propagate(outdir):
    """Make every child process of this one record into *outdir*."""
    os.environ["DASH_FNCOV_DIR"] = outdir
    site_dir = os.path.join(_HERE, "site")
    parts = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep)
             if p]
    for p in (_HERE, site_dir):
        if p not in parts:
            parts.insert(0, p)
    os.environ["PYTHONPATH"] = os.pathsep.join(parts)


if os.environ.get("DASH_FNCOV_DIR"):
    _propagate(os.path.abspath(os.environ["DASH_FNCOV_DIR"]))
    _rec.start(os.environ["DASH_FNCOV_DIR"])

#: DASH_FNCOV_PER_TEST=1: tag every record with the test that ran it.
_PER_TEST = bool(os.environ.get("DASH_FNCOV_DIR")
                 and os.environ.get("DASH_FNCOV_PER_TEST") == "1")


def pytest_report_header(config):
    d = os.environ.get("DASH_FNCOV_DIR")
    if d:
        return "dash function coverage: recording into %s%s" % (
            d, " (per test)" if _PER_TEST else "")
    return None


if _PER_TEST:
    import pytest

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_protocol(item, nextitem):
        os.environ["DASH_FNCOV_TEST"] = item.nodeid
        _rec.set_test(item.nodeid)
        try:
            return (yield)
        finally:
            _rec.set_test(None)
            os.environ.pop("DASH_FNCOV_TEST", None)
