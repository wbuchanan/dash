"""test_server_fixture.py -- the server fixtures leave no process behind.

GAPS3 K4 (WP-31 section 60): ``_Served.__enter__`` and ``_Launched.__enter__``
in test/test_server_serves.py raised "never answered" with the child still
running, so every failed start leaked a ``bokeh serve`` (or a launched app)
for the rest of the session. The fixture now terminates its process on every
failure path before it raises.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from test_server_serves import _Launched, _Served  # noqa: E402

pytestmark = pytest.mark.serve


def _app(tmp_path):
    p = tmp_path / "app.py"
    p.write_text("from bokeh.io import curdoc\n"
                 "from bokeh.models import Div\n"
                 "curdoc().add_root(Div(text='x'))\n")
    return str(p)


def _sleeper(tmp_path):
    """A launched "app" that never listens: it only sleeps."""
    p = tmp_path / "sleeper.py"
    p.write_text("import time\ntime.sleep(120)\n")
    return str(p)


class TestNoLeak:
    def test_a_never_ready_server_is_terminated(self, tmp_path):
        srv = _Served(_app(tmp_path), ready_path="/no-such-page",
                      deadline=2)
        with pytest.raises(AssertionError, match="never answered"):
            srv.__enter__()
        assert srv.proc is not None
        assert srv.proc.poll() is not None, "bokeh serve still running"

    def test_a_never_ready_launched_app_is_terminated(self, tmp_path):
        srv = _Launched(_sleeper(tmp_path), deadline=2)
        with pytest.raises(AssertionError, match="never answered"):
            srv.__enter__()
        assert srv.proc.poll() is not None, "the launched app still running"

    def test_an_early_exit_is_still_reported(self, tmp_path):
        srv = _Served(str(tmp_path / "missing.py"), deadline=30)
        with pytest.raises(AssertionError, match="exited early"):
            srv.__enter__()
        assert srv.proc.poll() is not None

    def test_the_default_deadline_is_sixty_seconds(self, tmp_path):
        assert _Served(_app(tmp_path)).deadline == 60
        assert _Launched(_app(tmp_path)).deadline == 60
