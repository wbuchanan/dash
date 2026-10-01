"""Regression tests for WP-29 P0.12b and P0.14: dash's temporary copies of
the data are private, and the one-line previews are pruned.

Measured at 7421d3d (section 08, Evidence §2): the spec and data files of
every render, ``dash serve``'s application and the one-line preview page
were written with the user's umask (0644; 0664 under umask 002) at a
predictable Stata tempfile name directly in ``c(tmpdir)``; a symbolic link
at such a name was followed, a pre-created 0666 file kept its mode, and the
preview was never deleted.  ``dash build, server``'s ``.py``, which embeds
every observation, followed the umask too (D6).

What these tests pin (section 08, ratified 01oct2026, both rounds):

* every copy is created 0600 by ``_dash_private_write``, which, as an
  anti-hijack guard, never writes through a link, into a FIFO or device,
  over a hard-linked file or over another account's file (r(7102));
* copies live in ``c(tmpdir)dash-<uid>/run-<pid>-<random>/`` (0700),
  swept by pid and removed when the command ends;
* a location that cannot be private is never refused: dash proceeds and
  notes it once (R-8), and a planted ``dash-<uid>`` is left alone for a
  0700 fallback root;
* previews go to ``previews/`` under unique names, five per session;
* ``dash serve`` starts its app only from the bytes it read through a
  descriptor it opened and verified, handed to ``python -P`` on stdin
  (R-9), so a file or folder swapped in afterwards never runs.

Each test reaches a new name through ``getattr`` inside the test, so on a
tree without the fix it fails on an assertion, never at collection.
"""
import contextlib
import errno
import hashlib
import io
import json
import os
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import types
import urllib.request
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402
from test_serve_launcher import _DF, _SPEC, _free_port  # noqa: E402
from test_string_value_export import _fake_auto, _write  # noqa: E402

_ADO = os.path.join(_ROOT, "dash.ado")
_HLP = os.path.join(_ROOT, "dash.sthlp")
_UID = os.getuid()
_PID = os.getpid()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def _umask(mask):
    """Set the process umask for the block only (try/finally)."""
    old = os.umask(mask)
    try:
        yield
    finally:
        os.umask(old)


def _mode(path):
    return stat.S_IMODE(os.lstat(path).st_mode)


def _unsafe():
    return getattr(dr, "_DashUnsafePath")


def _inputs(tmp_path, spec=None, sub="in"):
    d = tmp_path / sub
    d.mkdir(exist_ok=True)
    sp = d / "spec.json"
    dp = d / "data.json"
    sp.write_text(json.dumps(_SPEC if spec is None else spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    return str(sp), str(dp)


def _main(*a, **kw):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return dr.main(*a, **kw)


def _root_of(tmp_path):
    return os.path.join(str(tmp_path), "dash-%d" % _UID)


def _fallback_re():
    return re.compile(r"^dash-%d-[a-z0-9_]{8}$" % _UID)


class _RecStdin:
    """A fake child stdin: records every ``write(b)`` (bytes) and whether
    it was flushed or closed.  It has no ``buffer``, so the launcher's
    ``_dash_child_stdin`` returns it as it is (S13's FakeStdin has the
    same shape)."""

    def __init__(self, fail=None):
        self.writes = []
        self.flushed = 0
        self.closed = False
        self._fail = fail

    def write(self, b):
        if self._fail is not None:
            raise self._fail
        self.writes.append(bytes(b))
        return len(b)

    def flush(self):
        self.flushed += 1

    def close(self):
        self.closed = True


def _parse_frame(b):
    head, _, body = b.partition(b"\n")
    tag, n, sha = head.decode("ascii").split(" ")
    return tag, int(n), sha, body


def _fake_proc_class(on_init=None, stdin_fail=None):
    class _FakeProc:
        made = 0
        cmd = None
        kw = None
        last = None

        def __init__(self, cmd, **kw):
            type(self).made += 1
            type(self).cmd = list(cmd)
            type(self).kw = kw
            type(self).last = self
            if on_init is not None:
                on_init()
            self.stdin = _RecStdin(stdin_fail)
            self.stdout = io.StringIO("")
            self.stderr = io.StringIO("")
            self.returncode = 0
            self.killed = False

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            return self.returncode

        def terminate(self):
            pass

        def kill(self):
            self.killed = True

        def communicate(self):
            return ("", "")

    return _FakeProc


def _swap_run(rundir, evil_marker):
    """Rename *rundir* aside and put a folder at its name holding an
    ``app.py`` that writes EVIL RAN and exits 3, and a ``linecache.py``
    that appends its name to the marker and exits 4 (§3b A, C)."""
    os.rename(rundir, rundir + ".aside")
    os.mkdir(rundir, 0o700)
    with open(os.path.join(rundir, "app.py"), "w") as fh:
        fh.write("open(%r, 'w').write('EVIL RAN')\nraise SystemExit(3)\n"
                 % evil_marker)
    with open(os.path.join(rundir, "linecache.py"), "w") as fh:
        fh.write("open(%r, 'a').write('linecache ')\nraise SystemExit(4)\n"
                 % evil_marker)


def _health(port, timeout=1.0):
    try:
        urllib.request.urlopen("http://127.0.0.1:%d/health" % port,
                               timeout=timeout)
        return True
    except Exception:
        return False


def _wait_health(port, seconds, proc=None):
    t0 = time.monotonic()
    while time.monotonic() - t0 < seconds:
        if _health(port, 0.5):
            return True
        if proc is not None and proc.poll() is not None:
            return False
        time.sleep(0.1)
    return False


def _kill_listeners(port):
    try:
        out = subprocess.run(
            ["lsof", "-t", "-iTCP:%d" % port, "-sTCP:LISTEN"],
            capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return
    for tok in out.split():
        try:
            os.kill(int(tok), signal.SIGKILL)
        except (ValueError, OSError):
            pass


def _built_app(tmp_path, name="app.py", sub="build"):
    sp, dp = _inputs(tmp_path, sub=sub + "_in")
    d = tmp_path / sub
    d.mkdir(exist_ok=True)
    out = str(d / name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(out)
    return out


def _written_run_app(tmp_path):
    """``dash serve``'s route: the app written by main() into a run folder
    from ``_dash_run_open``; returns (run, written)."""
    run = getattr(dr, "_dash_run_open")(str(tmp_path))
    sp, dp = _inputs(tmp_path)
    written = _main(sp, dp, run["app"], mode="server", launch=True)
    return run, written


def _alarm(seconds):
    def _boom(*_a):
        raise TimeoutError("blocked")
    old = signal.signal(signal.SIGALRM, _boom)
    signal.alarm(seconds)
    return old


def _unalarm(old):
    signal.alarm(0)
    signal.signal(signal.SIGALRM, old)


# ===========================================================================
# The data file (_dash_write_stata_data's final write)
# ===========================================================================

class TestTheDataFileIsPrivate:

    def test_the_data_file_is_0600_under_umask_022(self, tmp_path):
        with _umask(0o022):
            path, msg = _write(tmp_path, _fake_auto(), "rowid y")
        assert msg == ""
        assert oct(_mode(path)) == oct(0o600)

    def test_the_data_file_is_0600_under_umask_002(self, tmp_path):
        with _umask(0o002):
            path, msg = _write(tmp_path, _fake_auto(), "rowid y")
        assert msg == ""
        assert oct(_mode(path)) == oct(0o600)

    def test_a_symlink_at_the_path_is_not_followed(self, tmp_path):
        victim = tmp_path / "victim.txt"
        victim.write_text("V")
        os.symlink(str(victim), str(tmp_path / "data.json"))
        with pytest.raises(Exception) as ei:
            _write(tmp_path, _fake_auto(), "rowid y")
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "refused to write" in str(ei.value)
        assert "(it is a link)" in str(ei.value)
        assert victim.read_text() == "V"
        assert os.path.islink(str(tmp_path / "data.json"))

    def test_a_preexisting_world_readable_file_of_ours_is_made_0600(
            self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text("old")
        os.chmod(str(p), 0o666)
        path, msg = _write(tmp_path, _fake_auto(), "rowid y")
        assert msg == ""
        assert oct(_mode(path)) == oct(0o600)
        assert json.loads(p.read_text())["variableNames"] == ["rowid", "y"]

    def test_a_hard_linked_file_is_refused(self, tmp_path):
        victim = tmp_path / "victim.txt"
        victim.write_text("V")
        os.link(str(victim), str(tmp_path / "data.json"))
        with pytest.raises(Exception) as ei:
            _write(tmp_path, _fake_auto(), "rowid y")
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "it has other links" in str(ei.value)
        assert victim.read_text() == "V"

    def test_a_fifo_at_the_path_is_refused_without_blocking(self, tmp_path):
        os.mkfifo(str(tmp_path / "data.json"))
        old = _alarm(2)
        try:
            with pytest.raises(Exception) as ei:
                _write(tmp_path, _fake_auto(), "rowid y")
        finally:
            _unalarm(old)
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "it is a pipe" in str(ei.value)

    def test_a_file_of_another_account_is_refused(self, tmp_path,
                                                  monkeypatch):
        p = tmp_path / "data.json"
        p.write_text("THEIRS")
        monkeypatch.setattr(os, "getuid", lambda: _UID + 1)
        with pytest.raises(Exception) as ei:
            _write(tmp_path, _fake_auto(), "rowid y")
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "it belongs to another account" in str(ei.value)
        assert p.read_text() == "THEIRS"

    def test_a_file_whose_mode_cannot_be_set_is_written(self, tmp_path,
                                                        monkeypatch):
        """Guard (ratified 01oct2026): a failed fchmod is the privacy
        class, never a refusal; the file is written (§3a R8)."""
        p = tmp_path / "data.json"
        p.write_text("old")
        os.chmod(str(p), 0o644)

        def _no(*_a):
            raise OSError(errno.ENOTSUP, "Operation not supported")
        monkeypatch.setattr(os, "fchmod", _no, raising=False)
        path, msg = _write(tmp_path, _fake_auto(), "rowid y")
        assert msg == ""
        assert json.loads(p.read_text())["variableNames"] == ["rowid", "y"]
        assert oct(_mode(path)) == oct(0o644)


# ===========================================================================
# The served app (main() in server mode)
# ===========================================================================

class TestTheServedAppIsPrivate:

    def test_the_launch_route_writes_the_app_0600(self, tmp_path):
        sp, dp = _inputs(tmp_path)
        for mask, name in ((0o022, "S_1.000003"), (0o002, "S_1.000004")):
            out = str(tmp_path / name)
            with _umask(mask):
                _main(sp, dp, out, mode="server", launch=True)
            assert oct(_mode(out)) == oct(0o600), (mask, name)

    def test_the_launch_route_deletes_spec_and_data_inside_a_run_dir_and_never_elsewhere(  # noqa: E501
            self, tmp_path):
        run = getattr(dr, "_dash_run_open")(str(tmp_path))
        with open(run["spec"], "w") as fh:
            json.dump(_SPEC, fh)
        with open(run["data"], "w") as fh:
            json.dump(make_data_json(_DF), fh)
        _main(run["spec"], run["data"], run["app"], mode="server",
              launch=True)
        assert os.path.exists(run["app"])
        assert not os.path.exists(run["spec"])
        assert not os.path.exists(run["data"])
        # Elsewhere: the user's files are never erased.
        sp, dp = _inputs(tmp_path, sub="mine")
        out = str(tmp_path / "mine" / "S_2.000001")
        _main(sp, dp, out, mode="server", launch=True)
        assert os.path.exists(sp) and os.path.exists(dp)

    def test_main_unlinks_only_when_all_three_paths_share_a_run_dir_under_dash_uid(  # noqa: E501
            self, tmp_path):
        run_of = getattr(dr, "_dash_private_run_of")

        def _case(root_name, root_mode, spec_elsewhere=False, sub="c"):
            base = tmp_path / sub
            base.mkdir()
            root = base / root_name
            root.mkdir()
            os.chmod(str(root), root_mode)
            rundir = root / ("run-%d-abc" % _PID)
            rundir.mkdir(mode=0o700)
            spec_dir = (base / "other") if spec_elsewhere else rundir
            spec_dir.mkdir(exist_ok=True)
            sp = spec_dir / "spec.json"
            dp = rundir / "data.json"
            sp.write_text(json.dumps(_SPEC))
            dp.write_text(json.dumps(make_data_json(_DF)))
            app = str(rundir / "app.py")
            _main(str(sp), str(dp), app, mode="server", launch=True)
            return sp, dp, app

        # A run-* folder under a parent not named dash-<uid>.
        sp, dp, app = _case("notdash", 0o700, sub="a")
        assert run_of(app) is None
        assert sp.exists() and dp.exists()
        # A dash-<uid> parent of mode 0755.
        sp, dp, app = _case("dash-%d" % _UID, 0o755, sub="b")
        assert run_of(app) is None
        assert sp.exists() and dp.exists()
        # The spec in another folder.
        sp, dp, app = _case("dash-%d" % _UID, 0o700, spec_elsewhere=True,
                            sub="d")
        assert run_of(app) == os.path.dirname(app)
        assert sp.exists() and dp.exists()

    def test_private_run_of_accepts_only_dash_s_own_layout(self, tmp_path):
        run_of = getattr(dr, "_dash_private_run_of")

        def _mk(root_name, mode=0o700):
            root = tmp_path / root_name
            root.mkdir()
            os.chmod(str(root), mode)
            rd = root / ("run-%d-xyz" % _PID)
            rd.mkdir(mode=0o700)
            return str(rd / "app.py"), str(rd)

        app, rd = _mk("dash-%d" % _UID)
        assert run_of(app) == rd
        app, rd = _mk("dash-%d-abcdefgh" % _UID)
        assert run_of(app) == rd
        app, _ = _mk("dash-%d-ABC" % _UID)
        assert run_of(app) is None
        app, _ = _mk("dash-%d-loose123" % _UID, 0o755)
        assert run_of(app) is None
        # Not app.py, or not a run-* folder.
        assert run_of(os.path.join(rd, "spec.json")) is None
        assert run_of(str(tmp_path / ("dash-%d" % _UID) / "app.py")) is None

    def test_erase_quietly_never_follows_a_link_and_ignores_a_missing_file(
            self, tmp_path):
        erase = getattr(dr, "_dash_erase_quietly")
        victim = tmp_path / "victim.txt"
        victim.write_text("V")
        link = tmp_path / "link"
        os.symlink(str(victim), str(link))
        erase(str(link))
        assert not os.path.lexists(str(link))
        assert victim.read_text() == "V"
        erase(str(tmp_path / "missing"))
        d = tmp_path / "adir"
        d.mkdir()
        erase(str(d))
        assert d.is_dir()

    def test_a_dash_build_server_app_is_0600(self, tmp_path):
        sp, dp = _inputs(tmp_path)
        for mask, name in ((0o022, "app.py"), (0o002, "app2.py")):
            out = str(tmp_path / name)
            with _umask(mask):
                _main(sp, dp, out, mode="server")
            assert oct(_mode(out)) == oct(0o600), (mask, name)

    def test_replacing_a_server_app_writes_a_new_0600_file(self, tmp_path):
        sp, dp = _inputs(tmp_path)
        out = tmp_path / "app.py"
        out.write_text("OLD")
        os.chmod(str(out), 0o644)
        with open(str(out)) as held:
            _main(sp, dp, str(out), mode="server")
            assert oct(_mode(str(out))) == oct(0o600)
            assert "_DATA_B64" in out.read_text()
            assert held.read() == "OLD"

    def test_a_link_at_a_server_app_path_is_refused_and_its_target_kept(
            self, tmp_path):
        sp, dp = _inputs(tmp_path)
        victim = tmp_path / "victim.txt"
        victim.write_text("V")
        os.chmod(str(victim), 0o644)
        link = tmp_path / "app.py"
        os.symlink(str(victim), str(link))
        with pytest.raises(Exception) as ei:
            _main(sp, dp, str(link), mode="server")
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "refused to write" in str(ei.value)
        assert "it is a link" in str(ei.value)
        assert victim.read_text() == "V"
        assert oct(_mode(str(victim))) == oct(0o644)
        assert os.path.islink(str(link))

    def test_a_user_named_folder_that_others_can_read_is_neither_refused_nor_remoded(  # noqa: E501
            self, tmp_path, capsys):
        sp, dp = _inputs(tmp_path)
        for mode in (0o755, 0o777):
            pub = tmp_path / ("pub%o" % mode)
            pub.mkdir()
            os.chmod(str(pub), mode)
            out = str(pub / "app.py")
            _main(sp, dp, out, mode="server")
            assert oct(_mode(out)) == oct(0o600)
            assert oct(_mode(str(pub))) == oct(mode)
        assert "dash: note:" not in capsys.readouterr().out

    def test_another_accounts_file_at_a_server_app_path_is_refused(
            self, tmp_path, monkeypatch):
        sp, dp = _inputs(tmp_path)
        out = tmp_path / "app.py"
        out.write_text("THEIRS")
        monkeypatch.setattr(os, "getuid", lambda: _UID + 1)
        with pytest.raises(Exception) as ei:
            _main(sp, dp, str(out), mode="server")
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "it belongs to another account" in str(ei.value)
        assert out.read_text() == "THEIRS"

    def test_a_refused_port_leaves_an_existing_server_app_untouched(
            self, tmp_path):
        """Guard: the name is cleared only once the source is complete."""
        import argparse
        sp, dp = _inputs(tmp_path)
        out = tmp_path / "app.py"
        out.write_text("OLD")
        with pytest.raises(argparse.ArgumentTypeError):
            _main(sp, dp, str(out), mode="server", port=99999)
        assert out.read_text() == "OLD"
        spec = json.loads(json.dumps(_SPEC))
        spec["build_options"]["port"] = "99999"
        sp2, dp2 = _inputs(tmp_path, spec=spec, sub="in2")
        with pytest.raises(argparse.ArgumentTypeError):
            _main(sp2, dp2, str(out), mode="server")
        assert out.read_text() == "OLD"


class TestThePrivateClearName:

    def test_a_missing_name_is_left_missing(self, tmp_path):
        clear = getattr(dr, "_dash_private_clear_name")
        p = str(tmp_path / "app.py")
        assert clear(p) is None
        assert not os.path.lexists(p)

    def test_an_own_regular_file_is_removed(self, tmp_path):
        clear = getattr(dr, "_dash_private_clear_name")
        p = tmp_path / "app.py"
        p.write_text("x")
        clear(str(p))
        assert not os.path.lexists(str(p))

    def test_a_link_is_refused_and_kept(self, tmp_path):
        clear = getattr(dr, "_dash_private_clear_name")
        victim = tmp_path / "victim.txt"
        victim.write_text("V")
        link = tmp_path / "app.py"
        os.symlink(str(victim), str(link))
        with pytest.raises(Exception) as ei:
            clear(str(link))
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "refused to write" in str(ei.value)
        assert "it is a link" in str(ei.value)
        assert os.path.islink(str(link))
        assert victim.read_text() == "V"

    def test_a_folder_or_fifo_is_refused(self, tmp_path):
        clear = getattr(dr, "_dash_private_clear_name")
        d = tmp_path / "app.py"
        d.mkdir()
        with pytest.raises(Exception) as ei:
            clear(str(d))
        assert isinstance(ei.value, _unsafe())
        assert "it is not a regular file" in str(ei.value)
        assert d.is_dir()
        f = tmp_path / "fifo.py"
        os.mkfifo(str(f))
        with pytest.raises(Exception) as ei:
            clear(str(f))
        assert isinstance(ei.value, _unsafe())
        assert "it is not a regular file" in str(ei.value)
        assert stat.S_ISFIFO(os.lstat(str(f)).st_mode)

    def test_another_accounts_file_is_refused(self, tmp_path, monkeypatch):
        clear = getattr(dr, "_dash_private_clear_name")
        p = tmp_path / "app.py"
        p.write_text("THEIRS")
        monkeypatch.setattr(os, "getuid", lambda: _UID + 1)
        with pytest.raises(Exception) as ei:
            clear(str(p))
        assert isinstance(ei.value, _unsafe())
        assert "it belongs to another account" in str(ei.value)
        assert p.read_text() == "THEIRS"


class TestTheServedAppWritesNoFile:

    def test_the_generated_app_has_no_file_writing_call(self, tmp_path):
        """Guard (R-3): the served app writes no file, so it needs none of
        the private-file helpers.  S13 flips this in place (index
        "Served app writes")."""
        import ast
        out = _built_app(tmp_path)
        with open(out, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        bad = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Name) and f.id == "open":
                    mode = None
                    if len(node.args) > 1 and isinstance(
                            node.args[1], ast.Constant):
                        mode = node.args[1].value
                    for k in node.keywords:
                        if k.arg == "mode" and isinstance(k.value,
                                                          ast.Constant):
                            mode = k.value.value
                    if mode and any(c in str(mode) for c in "wax+"):
                        bad.append("open(%r)" % mode)
                if isinstance(f, ast.Attribute):
                    if f.attr in ("write_text", "write_bytes"):
                        bad.append(f.attr)
                    if isinstance(f.value, ast.Name) and \
                            f.value.id == "os" and f.attr == "open":
                        bad.append("os.open")
            if isinstance(node, ast.Attribute) and \
                    isinstance(node.value, ast.Name) and \
                    node.value.id in ("tempfile", "shutil"):
                bad.append("%s.%s" % (node.value.id, node.attr))
        assert not bad, bad


class TestTheSavedPreviewIsPrivate:

    def test_a_private_output_page_is_0600(self, tmp_path):
        sp, dp = _inputs(tmp_path)
        out = str(tmp_path / "p.html")
        with _umask(0o022):
            _main(sp, dp, out, private_output=True)
        assert oct(_mode(out)) == oct(0o600)

    def test_the_cli_flag_reaches_main(self, tmp_path, monkeypatch):
        import runpy
        sp, dp = _inputs(tmp_path)
        out = str(tmp_path / "cli.html")
        monkeypatch.setattr(sys, "argv", [
            "dash_render.py", "--spec", sp, "--data", dp, "--output", out,
            "--private-output"])
        with _umask(0o022), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            runpy.run_path(os.path.join(_ROOT, "dash_render.py"),
                           run_name="__main__")
        assert oct(_mode(out)) == oct(0o600)

    def test_a_user_named_page_follows_the_umask(self, tmp_path):
        """Guard (BR-08.5): twoway's saving() follows the umask."""
        sp, dp = _inputs(tmp_path)
        for mask, want, name in ((0o022, 0o644, "u1.html"),
                                 (0o002, 0o664, "u2.html")):
            out = str(tmp_path / name)
            with _umask(mask):
                _main(sp, dp, out)
            assert oct(_mode(out)) == oct(want)


# ===========================================================================
# The private root
# ===========================================================================

class TestThePrivateRoot:

    def test_created_0700_under_umask_002_and_277(self, tmp_path):
        proot = getattr(dr, "_dash_private_root")
        for mask, sub in ((0o002, "a"), (0o277, "b")):
            base = tmp_path / sub
            base.mkdir()
            with _umask(mask):
                root, note = proot(str(base))
            assert root == os.path.join(str(base), "dash-%d" % _UID)
            assert note == ""
            assert oct(_mode(root)) == oct(0o700)

    def test_a_loose_root_of_ours_is_tightened(self, tmp_path):
        proot = getattr(dr, "_dash_private_root")
        os.mkdir(_root_of(tmp_path))
        os.chmod(_root_of(tmp_path), 0o755)
        root, note = proot(str(tmp_path))
        assert root == _root_of(tmp_path) and note == ""
        assert oct(_mode(root)) == oct(0o700)

    def test_a_symlinked_root_is_left_alone_and_a_fallback_is_used(
            self, tmp_path):
        proot = getattr(dr, "_dash_private_root")
        victim = tmp_path / "victim"
        victim.mkdir(mode=0o700)
        os.symlink(str(victim), _root_of(tmp_path))
        root, note = proot(str(tmp_path))
        assert _fallback_re().match(os.path.basename(root)), root
        assert os.path.dirname(root) == str(tmp_path)
        assert oct(_mode(root)) == oct(0o700)
        assert os.lstat(root).st_uid == _UID
        assert "is not yours to use" in note and "it is a link" in note
        assert _root_of(tmp_path) in note and root in note
        assert os.listdir(str(victim)) == []
        assert os.path.islink(_root_of(tmp_path))

    def test_a_root_of_another_account_is_left_alone_and_a_fallback_is_used(  # noqa: E501
            self, tmp_path, monkeypatch):
        proot = getattr(dr, "_dash_private_root")
        other = _UID + 1
        theirs = tmp_path / ("dash-%d" % other)
        theirs.mkdir(mode=0o700)
        monkeypatch.setattr(os, "getuid", lambda: other)
        root, note = proot(str(tmp_path))
        assert re.match(r"^dash-%d-[a-z0-9_]{8}$" % other,
                        os.path.basename(root)), root
        assert oct(_mode(root)) == oct(0o700)
        assert "is not yours to use (it belongs to another account)" in note
        assert os.listdir(str(theirs)) == []

    def test_a_root_that_is_a_file_is_left_alone_and_a_fallback_is_used(
            self, tmp_path):
        proot = getattr(dr, "_dash_private_root")
        with open(_root_of(tmp_path), "w") as fh:
            fh.write("F")
        root, note = proot(str(tmp_path))
        assert _fallback_re().match(os.path.basename(root)), root
        assert "it is not a folder" in note
        with open(_root_of(tmp_path)) as fh:
            assert fh.read() == "F"

    def test_a_fallback_root_is_reused_only_when_it_is_ours_and_0700(
            self, tmp_path):
        proot = getattr(dr, "_dash_private_root")
        os.symlink(str(tmp_path), _root_of(tmp_path))
        loose = tmp_path / ("dash-%d-zzzzzzzz" % _UID)
        loose.mkdir()
        os.chmod(str(loose), 0o755)
        root1, _ = proot(str(tmp_path))
        assert root1 != str(loose)
        assert _fallback_re().match(os.path.basename(root1))
        root2, _ = proot(str(tmp_path))
        assert root2 == root1
        assert oct(_mode(str(loose))) == oct(0o755)

    def test_a_writable_non_sticky_base_proceeds_with_a_note_naming_chmod(
            self, tmp_path):
        proot = getattr(dr, "_dash_private_root")
        base = tmp_path / "shared"
        base.mkdir()
        os.chmod(str(base), 0o775)
        root, note = proot(str(base))
        assert root == os.path.join(str(base), "dash-%d" % _UID)
        assert oct(_mode(root)) == oct(0o700)
        assert str(base) in note
        assert "chmod go-w" in note and "STATATMP" in note
        assert "other accounts can write to it and it has no sticky bit" \
            in note

    def test_a_base_owned_by_another_account_proceeds_with_a_note(
            self, tmp_path, monkeypatch):
        proot = getattr(dr, "_dash_private_root")
        base = str(tmp_path)
        real_stat = os.stat

        def _stat(p, *a, **kw):
            st = real_stat(p, *a, **kw)
            if isinstance(p, str) and p == base:
                return types.SimpleNamespace(st_mode=st.st_mode,
                                             st_uid=_UID + 7)
            return st
        monkeypatch.setattr(os, "stat", _stat)
        root, note = proot(base)
        assert root == _root_of(tmp_path)
        assert "it belongs to another account" in note
        assert "chmod go-w" in note

    def test_a_root_that_cannot_be_tightened_proceeds_with_a_note(
            self, tmp_path, monkeypatch):
        proot = getattr(dr, "_dash_private_root")
        os.mkdir(_root_of(tmp_path))
        os.chmod(_root_of(tmp_path), 0o755)

        def _no(*_a):
            raise OSError(errno.ENOTSUP, "Operation not supported")
        monkeypatch.setattr(os, "fchmod", _no)
        root, note = proot(str(tmp_path))
        assert root == _root_of(tmp_path)
        assert "could not be made private" in note
        assert "its permissions could not be set" in note
        monkeypatch.setattr(os, "fchmod", lambda *_a: None)
        root, note = proot(str(tmp_path))
        assert "could not be made private" in note
        assert "its permissions stay 0o755" in note

    def test_a_sticky_world_writable_base_is_accepted_without_a_note(
            self, tmp_path):
        proot = getattr(dr, "_dash_private_root")
        base = tmp_path / "tmp"
        base.mkdir()
        os.chmod(str(base), 0o1777)
        root, note = proot(str(base))
        assert note == ""
        assert oct(_mode(root)) == oct(0o700)

    def test_a_base_that_is_not_a_folder_raises_an_os_error(self, tmp_path):
        proot = getattr(dr, "_dash_private_root")
        f = tmp_path / "file"
        f.write_text("x")
        with pytest.raises(OSError):
            proot(str(f))

    def test_a_base_reached_through_a_symlink_gives_paths_the_caller_can_match(  # noqa: E501
            self, tmp_path):
        run_open = getattr(dr, "_dash_run_open")
        real = tmp_path / "real"
        real.mkdir()
        os.symlink(str(real), str(tmp_path / "via"))
        base = str(tmp_path / "via") + "/"
        run = run_open(base)
        assert run["err"] == ""
        for k in ("rundir", "spec", "data", "app"):
            assert run[k].startswith(base), (k, run[k])
        assert os.path.isdir(run["rundir"])

    def test_windows_root_is_named_dash(self, monkeypatch):
        name = getattr(dr, "_dash_root_name")
        assert name() == "dash-%d" % _UID
        monkeypatch.delattr(os, "getuid")
        assert name() == "dash"

    def test_create_false_returns_none_when_absent(self, tmp_path):
        proot = getattr(dr, "_dash_private_root")
        assert proot(str(tmp_path), create=False) == (None, "")
        assert os.listdir(str(tmp_path)) == []


# ===========================================================================
# Run folders
# ===========================================================================

def _dead_pid():
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


class TestTheRunDir:

    def test_open_makes_a_0700_run_named_for_this_pid(self, tmp_path):
        run = getattr(dr, "_dash_run_open")(str(tmp_path))
        assert run["err"] == "" and run["note"] == ""
        assert re.match(r"^run-%d-[A-Za-z0-9_]+$" % _PID,
                        os.path.basename(run["rundir"]))
        assert os.path.dirname(run["rundir"]) == _root_of(tmp_path)
        assert oct(_mode(run["rundir"])) == oct(0o700)
        assert run["spec"] == os.path.join(run["rundir"], "spec.json")
        assert run["data"] == os.path.join(run["rundir"], "data.json")
        assert run["app"] == os.path.join(run["rundir"], "app.py")

    def test_open_sweeps_this_pids_stale_runs(self, tmp_path):
        os.mkdir(_root_of(tmp_path), 0o700)
        stale = os.path.join(_root_of(tmp_path), "run-%d-old" % _PID)
        os.mkdir(stale, 0o700)
        getattr(dr, "_dash_run_open")(str(tmp_path))
        assert not os.path.exists(stale)

    def test_open_sweeps_a_dead_pids_run(self, tmp_path):
        os.mkdir(_root_of(tmp_path), 0o700)
        dead = os.path.join(_root_of(tmp_path), "run-%d-old" % _dead_pid())
        os.mkdir(dead, 0o700)
        getattr(dr, "_dash_run_open")(str(tmp_path))
        assert not os.path.exists(dead)

    def test_open_keeps_a_live_other_pids_run(self, tmp_path):
        os.mkdir(_root_of(tmp_path), 0o700)
        live = os.path.join(_root_of(tmp_path), "run-%d-x" % os.getppid())
        os.mkdir(live, 0o700)
        getattr(dr, "_dash_run_open")(str(tmp_path))
        assert os.path.isdir(live)

    def test_the_sweep_treats_permission_error_as_alive(self, tmp_path,
                                                        monkeypatch):
        sweep = getattr(dr, "_dash_run_sweep")
        root = tmp_path / "root"
        root.mkdir()
        kept = root / "run-999999-x"
        kept.mkdir()

        def _perm(*_a):
            raise PermissionError(errno.EPERM, "nope")
        monkeypatch.setattr(os, "kill", _perm)
        assert sweep(str(root)) == 0
        assert kept.is_dir()

    def test_age_never_removes_a_live_pids_run_on_posix(self, tmp_path):
        sweep = getattr(dr, "_dash_run_sweep")
        root = tmp_path / "root"
        root.mkdir()
        old = root / ("run-%d-x" % os.getppid())
        old.mkdir()
        t = time.time() - 3 * 86400
        os.utime(str(old), (t, t))
        sweep(str(root))
        assert old.is_dir()

    def test_age_removes_a_run_on_windows(self, tmp_path, monkeypatch):
        sweep = getattr(dr, "_dash_run_sweep")
        root = tmp_path / "root"
        root.mkdir()
        old = root / ("run-%d-x" % os.getppid())
        old.mkdir()
        young = root / ("run-%d-y" % os.getppid())
        young.mkdir()
        t = time.time() - 3 * 86400
        os.utime(str(old), (t, t))

        def _sig(*_a):
            raise AssertionError("signalled")
        monkeypatch.setattr(os, "kill", _sig)
        monkeypatch.setattr(os, "name", "nt")
        n = sweep(str(root))
        monkeypatch.setattr(os, "name", "posix")
        assert n == 1
        assert not old.exists() and young.is_dir()

    def test_the_sweep_never_signals_on_windows(self, tmp_path, monkeypatch):
        sweep = getattr(dr, "_dash_run_sweep")
        alive = getattr(dr, "_dash_pid_alive")
        root = tmp_path / "root"
        root.mkdir()
        (root / "run-424242-x").mkdir()

        def _sig(*_a):
            raise AssertionError("signalled")
        monkeypatch.setattr(os, "kill", _sig)
        monkeypatch.setattr(os, "name", "nt")
        try:
            assert alive(424242) is True
            assert sweep(str(root)) == 0
        finally:
            monkeypatch.setattr(os, "name", "posix")
        assert (root / "run-424242-x").is_dir()

    def test_the_sweep_never_signals_pid_zero(self, tmp_path, monkeypatch):
        sweep = getattr(dr, "_dash_run_sweep")
        alive = getattr(dr, "_dash_pid_alive")
        root = tmp_path / "root"
        root.mkdir()
        (root / "run-0-x").mkdir()

        def _sig(*_a):
            raise AssertionError("signalled")
        monkeypatch.setattr(os, "kill", _sig)
        assert alive(0) is True and alive(-1) is True
        assert sweep(str(root)) == 0
        assert (root / "run-0-x").is_dir()

    def test_close_removes_the_run(self, tmp_path):
        run = getattr(dr, "_dash_run_open")(str(tmp_path))
        with open(run["spec"], "w") as fh:
            fh.write("{}")
        assert dr._dash_run_close(run["rundir"], str(tmp_path)) == ""
        assert not os.path.exists(run["rundir"])

    def test_close_refuses_a_path_outside_the_root(self, tmp_path):
        close = getattr(dr, "_dash_run_close")
        own = getattr(dr, "_dash_own_root")
        other = tmp_path / "other" / ("run-%d-x" % _PID)
        other.mkdir(parents=True)
        msg = close(str(other), str(tmp_path))
        assert "is not a dash run folder; nothing was removed" in msg
        assert other.is_dir()
        os.mkdir(_root_of(tmp_path), 0o700)
        bad = os.path.join(_root_of(tmp_path), "notarun")
        os.mkdir(bad)
        assert "not a dash run folder" in close(bad, str(tmp_path))
        assert os.path.isdir(bad)
        assert own(_root_of(tmp_path), str(tmp_path)) is True
        assert own(str(tmp_path / "other"), str(tmp_path)) is False
        assert own(_root_of(tmp_path), str(tmp_path / "other")) is False
        assert close("", str(tmp_path)) == ""

    def test_close_removes_a_link_inside_the_run_not_its_target(
            self, tmp_path):
        run = getattr(dr, "_dash_run_open")(str(tmp_path))
        victim = tmp_path / "victim.txt"
        victim.write_text("V")
        os.symlink(str(victim), os.path.join(run["rundir"], "data.json"))
        assert dr._dash_run_close(run["rundir"], str(tmp_path)) == ""
        assert not os.path.lexists(run["rundir"])
        assert victim.read_text() == "V"

    def test_close_of_a_missing_run_is_silent(self, tmp_path):
        run = getattr(dr, "_dash_run_open")(str(tmp_path))
        shutil.rmtree(run["rundir"])
        assert dr._dash_run_close(run["rundir"], str(tmp_path)) == ""

    def test_open_reports_an_unsafe_root_as_a_note_and_still_opens(
            self, tmp_path):
        victim = tmp_path / "victim"
        victim.mkdir(mode=0o700)
        os.symlink(str(victim), _root_of(tmp_path))
        run = getattr(dr, "_dash_run_open")(str(tmp_path))
        assert run["err"] == ""
        assert run["note"].startswith("dash: note: ")
        assert run["note"].count("dash: note: ") == 1
        root = os.path.dirname(run["rundir"])
        assert _fallback_re().match(os.path.basename(root))
        assert re.match(r"^run-%d-" % _PID, os.path.basename(run["rundir"]))
        assert oct(_mode(run["rundir"])) == oct(0o700)
        assert os.listdir(str(victim)) == []

    def test_open_reports_an_os_failure_as_err(self, tmp_path):
        f = tmp_path / "file"
        f.write_text("x")
        run = getattr(dr, "_dash_run_open")(str(f))
        assert "could not make its temporary folder" in run["err"]
        for k in ("rundir", "spec", "data", "app"):
            assert run[k] == ""

    def test_close_removes_an_empty_fallback_root_and_keeps_one_holding_a_preview(  # noqa: E501
            self, tmp_path):
        os.symlink(str(tmp_path), _root_of(tmp_path))
        run = getattr(dr, "_dash_run_open")(str(tmp_path))
        root = os.path.dirname(run["rundir"])
        assert dr._dash_run_close(run["rundir"], str(tmp_path)) == ""
        assert not os.path.exists(root)
        prev = dr._dash_preview_path(str(tmp_path), "0")
        with open(prev["path"], "w") as fh:
            fh.write("page")
        run = dr._dash_run_open(str(tmp_path))
        root2 = os.path.dirname(run["rundir"])
        assert dr._dash_run_close(run["rundir"], str(tmp_path)) == ""
        assert os.path.isdir(root2)
        assert os.path.exists(prev["path"])


# ===========================================================================
# Previews
# ===========================================================================

def _page(prev, pid, opened="q", age=0.0, tag=None):
    tag = tag or os.urandom(4).hex()
    name = "dash-preview-20260101-000000-%d-%s-%s.html" % (pid, tag, opened)
    p = os.path.join(prev, name)
    with open(p, "w") as fh:
        fh.write("p")
    if age:
        t = time.time() - age
        os.utime(p, (t, t))
    return p


def _mine(prev):
    return sorted(n for n in os.listdir(prev)
                  if re.search(r"-%d-[0-9a-f]{8}-[bq]\.html$" % _PID, n))


class TestThePreviews:

    def _prev(self, tmp_path):
        p = os.path.join(_root_of(tmp_path), "previews")
        os.makedirs(p, mode=0o700, exist_ok=True)
        return p

    def test_names_are_unique_and_inside_previews(self, tmp_path):
        pp = getattr(dr, "_dash_preview_path")
        a = pp(str(tmp_path), "1")
        b = pp(str(tmp_path), "0")
        assert a["err"] == "" and b["err"] == "" and a["note"] == ""
        assert a["path"] != b["path"]
        prev = os.path.join(_root_of(tmp_path), "previews")
        for p, kind in ((a["path"], "b"), (b["path"], "q")):
            assert os.path.dirname(p) == prev
            assert re.match(
                r"^dash-preview-\d{8}-\d{6}-%d-[0-9a-f]{8}-%s\.html$"
                % (_PID, kind), os.path.basename(p)), p
        assert oct(_mode(prev)) == oct(0o700)

    def test_the_newest_five_are_kept(self, tmp_path):
        pp = getattr(dr, "_dash_preview_path")
        prev = self._prev(tmp_path)
        for i in range(7):
            _page(prev, _PID, "q", age=1000 - i * 10)
        new = pp(str(tmp_path), "0")["path"]
        with open(new, "w") as fh:
            fh.write("n")
        assert len(_mine(prev)) == 5

    def test_a_page_opened_in_the_last_minute_is_kept(self, tmp_path):
        prune = getattr(dr, "_dash_prune_previews")
        prev = self._prev(tmp_path)
        young_b = _page(prev, _PID, "b", age=30)
        for i in range(6):
            _page(prev, _PID, "q", age=5 + i)
        prune(prev, "preview")
        assert os.path.exists(young_b)

    def test_clear_removes_every_page_but_a_young_opened_one(self, tmp_path):
        prune = getattr(dr, "_dash_prune_previews")
        prev = self._prev(tmp_path)
        young_b = _page(prev, _PID, "b", age=10)
        old_b = _page(prev, _PID, "b", age=600)
        young_q = _page(prev, _PID, "q", age=10)
        prune(prev, "clear")
        assert os.path.exists(young_b)
        assert not os.path.exists(old_b) and not os.path.exists(young_q)

    def test_a_live_other_sessions_pages_survive_prune_and_clear(
            self, tmp_path):
        prune = getattr(dr, "_dash_prune_previews")
        prev = self._prev(tmp_path)
        theirs = [_page(prev, os.getppid(), k, age=a)
                  for k, a in (("q", 5), ("b", 5), ("q", 3600))]
        prune(prev, "preview")
        prune(prev, "clear")
        assert all(os.path.exists(p) for p in theirs)

    def test_a_dead_sessions_pages_are_removed(self, tmp_path):
        prune = getattr(dr, "_dash_prune_previews")
        prev = self._prev(tmp_path)
        dead = _page(prev, _dead_pid(), "b", age=5)
        stale = _page(prev, os.getppid(), "q", age=2 * 86400)
        prune(prev, "preview")
        assert not os.path.exists(dead) and not os.path.exists(stale)

    def test_the_ceiling_bounds_all_sessions_together(self, tmp_path):
        prune = getattr(dr, "_dash_prune_previews")
        prev = self._prev(tmp_path)
        for i in range(30):
            _page(prev, os.getppid(), "q", age=100 + i)
        prune(prev, "preview")
        left = [n for n in os.listdir(prev) if n.endswith(".html")]
        assert len(left) == 25

    def test_files_dash_did_not_name_are_never_touched(self, tmp_path):
        prune = getattr(dr, "_dash_prune_previews")
        prev = self._prev(tmp_path)
        other = os.path.join(prev, "notes.txt")
        with open(other, "w") as fh:
            fh.write("x")
        victim = tmp_path / "victim.html"
        victim.write_text("V")
        link = os.path.join(
            prev, "dash-preview-20200101-000000-%d-00000000-q.html"
            % _dead_pid())
        os.symlink(str(victim), link)
        prune(prev, "clear")
        assert os.path.exists(other) and os.path.islink(link)
        assert victim.read_text() == "V"

    def test_clear_never_creates_the_root(self, tmp_path):
        clear = getattr(dr, "_dash_tmp_clear")
        assert clear(str(tmp_path)) == ""
        assert os.listdir(str(tmp_path)) == []

    def test_a_planted_previews_folder_moves_the_preview_to_a_fallback_root(
            self, tmp_path):
        pp = getattr(dr, "_dash_preview_path")
        os.mkdir(_root_of(tmp_path), 0o700)
        victim = tmp_path / "victim"
        victim.mkdir()
        planted = os.path.join(_root_of(tmp_path), "previews")
        os.symlink(str(victim), planted)
        r = pp(str(tmp_path), "0")
        assert r["err"] == ""
        prev = os.path.dirname(r["path"])
        assert os.path.basename(prev) == "previews"
        assert _fallback_re().match(os.path.basename(os.path.dirname(prev)))
        assert planted in r["note"] and r["note"].startswith("dash: note: ")
        assert os.listdir(str(victim)) == []

    def test_clear_prunes_and_removes_an_emptied_fallback_root(
            self, tmp_path):
        clear = getattr(dr, "_dash_tmp_clear")
        os.symlink(str(tmp_path), _root_of(tmp_path))
        r = dr._dash_preview_path(str(tmp_path), "0")
        with open(r["path"], "w") as fh:
            fh.write("p")
        t = time.time() - 600
        os.utime(r["path"], (t, t))
        fb = os.path.dirname(os.path.dirname(r["path"]))
        assert clear(str(tmp_path)) == ""
        assert not os.path.exists(fb)
        assert os.path.islink(_root_of(tmp_path))


# ===========================================================================
# The note (R-8)
# ===========================================================================

class TestTheNote:

    def test_one_note_names_every_location_once(self, tmp_path):
        base = tmp_path / "shared"
        base.mkdir()
        os.chmod(str(base), 0o775)
        planted = os.path.join(str(base), "dash-%d" % _UID)
        os.symlink(str(tmp_path), planted)
        run = getattr(dr, "_dash_run_open")(str(base))
        note = run["note"]
        assert note.count("dash: note: ") == 1, note
        assert str(base) in note and planted in note
        assert "chmod go-w" in note and "is not yours to use" in note

    def test_mode_private_reads_group_and_other_bits_and_is_true_on_windows(
            self, monkeypatch):
        mp = getattr(dr, "_dash_mode_private")
        ns = types.SimpleNamespace
        assert mp(ns(st_mode=stat.S_IFREG | 0o600)) is True
        assert mp(ns(st_mode=stat.S_IFREG | 0o640)) is False
        assert mp(ns(st_mode=stat.S_IFREG | 0o604)) is False
        assert mp(ns(st_mode=stat.S_IFDIR | 0o700)) is True
        monkeypatch.setattr(os, "name", "nt")
        try:
            assert mp(ns(st_mode=stat.S_IFREG | 0o666)) is True
        finally:
            monkeypatch.setattr(os, "name", "posix")

    def test_a_server_app_on_a_disk_without_permissions_is_written_and_noted(  # noqa: E501
            self, tmp_path, monkeypatch, capsys):
        real = getattr(dr, "_dash_private_write")

        def _loose(path, text, exclusive=False):
            st = real(path, text, exclusive=exclusive)
            return os.stat_result((stat.S_IFREG | 0o644,) + tuple(st)[1:10])
        monkeypatch.setattr(dr, "_dash_private_write", _loose)
        sp, dp = _inputs(tmp_path)
        user = tmp_path / "user"
        user.mkdir()
        out = str(user / "app.py")
        capsys.readouterr()
        _main(sp, dp, out, mode="server")
        printed = capsys.readouterr().out
        lines = [ln for ln in printed.splitlines() if "dash: note: " in ln]
        assert len(lines) == 1, printed
        assert out in lines[0] and "every observation" in lines[0]
        assert os.path.exists(out)
        run = dr._dash_run_open(str(tmp_path))
        _main(sp, dp, run["app"], mode="server", launch=True)
        assert "dash: note: " not in capsys.readouterr().out

    def test_a_file_in_a_folder_dash_chose_is_never_noted_by_the_renderer(
            self, tmp_path):
        chosen = getattr(dr, "_dash_chosen_path")
        run = dr._dash_run_open(str(tmp_path))
        assert chosen(run["app"]) is True
        prev = dr._dash_preview_path(str(tmp_path), "0")["path"]
        assert chosen(prev) is True
        fb = os.path.join(str(tmp_path), "dash-%d-abcdefgh" % _UID,
                          "run-1-x", "app.py")
        assert chosen(fb) is True
        assert chosen(str(tmp_path / "user" / "app.py")) is False
        assert chosen(str(tmp_path / "run-1-x" / "app.py")) is False
        assert chosen(os.path.join(str(tmp_path), "other", "previews",
                                   "p.html")) is False

    def test_the_note_holds_no_data(self, tmp_path, monkeypatch, capsys):
        base = tmp_path / "shared"
        base.mkdir()
        os.chmod(str(base), 0o775)
        os.symlink(str(tmp_path), os.path.join(str(base),
                                               "dash-%d" % _UID))
        note = getattr(dr, "_dash_run_open")(str(base))["note"]
        real = dr._dash_private_write

        def _loose(path, text, exclusive=False):
            st = real(path, text, exclusive=exclusive)
            return os.stat_result((stat.S_IFREG | 0o644,) + tuple(st)[1:10])
        monkeypatch.setattr(dr, "_dash_private_write", _loose)
        sp, dp = _inputs(tmp_path)
        (tmp_path / "u").mkdir()
        _main(sp, dp, str(tmp_path / "u" / "app.py"), mode="server")
        printed = note + capsys.readouterr().out
        assert note
        assert "_DATA_B64" not in printed
        for v in ("2930", "3350", "2200"):
            assert v not in printed, v


# ===========================================================================
# The launch from the open file (R-9, round 2)
# ===========================================================================

class TestTheLaunchFromTheOpenFile:

    @pytest.mark.serve
    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX rename")
    def test_a_path_swapped_after_verification_does_not_change_what_runs(
            self, tmp_path, monkeypatch, capsys):
        rundir = tmp_path / "run-1-x"
        rundir.mkdir(mode=0o700)
        sp, dp = _inputs(tmp_path)
        out = str(rundir / "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(out)
        os.chmod(out, 0o600)
        marker = str(tmp_path / "marker.txt")
        port = _free_port()
        real_popen = subprocess.Popen
        procs = []
        answered = []

        def _watch():
            t0 = time.monotonic()
            while not procs and time.monotonic() - t0 < 40:
                time.sleep(0.05)
            if not procs:
                return
            p = procs[0]
            if _wait_health(port, 40, p):
                answered.append(True)
            if p.poll() is None:
                # The designed stop: the app's --parent-watch (WP-29 P0.13
                # F2) ends it, exit 0, on end of file of its stdin.  A
                # SIGINT, used before F4, now ends dash serve as a Break.
                try:
                    p.stdin.close()
                except (OSError, ValueError):
                    pass

        class _Swapping:
            def __new__(cls, cmd, **kw):
                _swap_run(str(rundir), marker)
                p = real_popen(cmd, **kw)
                procs.append(p)
                return p
        monkeypatch.setattr(subprocess, "Popen", _Swapping)
        th = threading.Thread(target=_watch, daemon=True)
        th.start()
        try:
            dr._dash_launch_app(out, port, 0, True)
        finally:
            th.join(45)
            for p in procs:
                if p.poll() is None:
                    p.kill()
                    p.wait()
            _kill_listeners(port)
        assert not os.path.exists(marker), open(marker).read()
        assert answered, "/health never answered"
        assert "Bokeh Server running at" in capsys.readouterr().out

    def test_the_child_is_handed_the_verified_bytes_not_the_path(
            self, tmp_path, monkeypatch):
        rundir = tmp_path / "run-1-x"
        rundir.mkdir(mode=0o700)
        sp, dp = _inputs(tmp_path)
        out = str(rundir / "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(out)
        with open(out, "rb") as fh:
            original = fh.read()
        marker = str(tmp_path / "marker.txt")
        Fake = _fake_proc_class(on_init=lambda: _swap_run(str(rundir),
                                                          marker))
        monkeypatch.setattr(subprocess, "Popen", Fake)
        dr._dash_launch_app(out, _free_port(), 0, True, prebind=False)
        assert Fake.cmd[:5] == [sys.executable, "-P", "-c",
                                getattr(dr, "_DASH_BOOT", None), out], \
            Fake.cmd[:3]
        assert Fake.kw.get("stdin") is subprocess.PIPE
        data = b"".join(Fake.last.stdin.writes)
        tag, n, sha, body = _parse_frame(data)
        assert tag == "DASHAPP1" and n == len(original)
        assert body == original
        assert sha == hashlib.sha256(original).hexdigest()
        assert b"EVIL RAN" not in data

    def test_a_substituted_app_is_not_started(self, tmp_path, monkeypatch):
        run, written = _written_run_app(tmp_path)
        os.rename(run["rundir"], run["rundir"] + ".aside")
        os.mkdir(run["rundir"], 0o700)
        with open(run["app"], "w") as fh:
            fh.write("print('other')\n")
        Fake = _fake_proc_class()
        monkeypatch.setattr(subprocess, "Popen", Fake)
        with pytest.raises(Exception) as ei:
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                expect=written)
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "refused to run" in str(ei.value)
        assert "(it was replaced after dash wrote it)" in str(ei.value)
        assert Fake.made == 0

    def test_the_written_app_is_started(self, tmp_path, monkeypatch):
        run, written = _written_run_app(tmp_path)
        Fake = _fake_proc_class()
        monkeypatch.setattr(subprocess, "Popen", Fake)
        dr._dash_launch_app(run["app"], _free_port(), 0, True,
                            expect=written)
        assert Fake.made == 1
        assert Fake.cmd[:5] == [sys.executable, "-P", "-c", dr._DASH_BOOT,
                                run["app"]]
        _, _, sha, _ = _parse_frame(b"".join(Fake.last.stdin.writes))
        assert sha == written.sha256

    def test_main_returns_the_written_apps_identity(self, tmp_path):
        run, written = _written_run_app(tmp_path)
        assert isinstance(written.st, os.stat_result)
        lst = os.lstat(run["app"])
        assert (written.st.st_dev, written.st.st_ino) == (lst.st_dev,
                                                          lst.st_ino)
        with open(run["app"], "rb") as fh:
            assert written.sha256 == hashlib.sha256(fh.read()).hexdigest()

    def test_a_swap_between_open_and_read_reads_the_original(
            self, tmp_path, monkeypatch):
        run, written = _written_run_app(tmp_path)
        read = getattr(dr, "_dash_read_verified_app")
        real_fstat = os.fstat
        swapped = []

        def _fstat(fd):
            st = real_fstat(fd)
            if not swapped and stat.S_ISREG(st.st_mode) and \
                    st.st_size == written.st.st_size:
                swapped.append(True)
                _swap_run(run["rundir"], str(tmp_path / "m.txt"))
            return st
        monkeypatch.setattr(os, "fstat", _fstat)
        data = read(run["app"], written)
        assert swapped
        assert hashlib.sha256(data).hexdigest() == written.sha256

    def test_the_same_file_rewritten_in_place_is_refused(self, tmp_path,
                                                         monkeypatch):
        run, written = _written_run_app(tmp_path)
        with open(run["app"], "r+b") as fh:
            fh.seek(10)
            c = fh.read(1)
            fh.seek(10)
            fh.write(b"X" if c != b"X" else b"Y")
        Fake = _fake_proc_class()
        monkeypatch.setattr(subprocess, "Popen", Fake)
        with pytest.raises(Exception) as ei:
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                expect=written)
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "(it changed after dash wrote it)" in str(ei.value)
        assert Fake.made == 0

    def test_a_link_or_fifo_at_the_app_path_is_refused_without_expect(
            self, tmp_path, monkeypatch):
        app = _built_app(tmp_path)
        copy = str(tmp_path / "copy.py")
        shutil.copy(app, copy)
        link = str(tmp_path / "link.py")
        os.symlink(copy, link)
        Fake = _fake_proc_class()
        monkeypatch.setattr(subprocess, "Popen", Fake)
        with pytest.raises(Exception) as ei:
            dr._dash_launch_app(link, _free_port(), 0, True)
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "(it is a link)" in str(ei.value)
        fifo = str(tmp_path / "fifo.py")
        os.mkfifo(fifo)
        old = _alarm(2)
        try:
            with pytest.raises(Exception) as ei:
                dr._dash_launch_app(fifo, _free_port(), 0, True)
        finally:
            _unalarm(old)
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "(it is not a regular file)" in str(ei.value)
        assert Fake.made == 0

    def test_another_accounts_app_is_refused(self, tmp_path, monkeypatch):
        app = _built_app(tmp_path)
        Fake = _fake_proc_class()
        monkeypatch.setattr(subprocess, "Popen", Fake)
        monkeypatch.setattr(os, "getuid", lambda: _UID + 1)
        with pytest.raises(Exception) as ei:
            dr._dash_launch_app(app, _free_port(), 0, True)
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "(it belongs to another account)" in str(ei.value)
        assert Fake.made == 0

    def test_a_child_that_cannot_take_the_app_is_stopped_and_reported(
            self, tmp_path, monkeypatch, capsys):
        app = _built_app(tmp_path)

        class _Stuck:
            killed = False
            made = 0

            def __init__(self, cmd, **kw):
                type(self).made += 1
                self.stdin = _RecStdin(BrokenPipeError(errno.EPIPE,
                                                       "Broken pipe"))
                self.stdout = io.StringIO("")
                self.stderr = io.StringIO("")
                self.returncode = None
                self._n = 0

            def poll(self):
                self._n += 1
                if type(self).killed or self._n > 20:
                    self.returncode = 0 if not type(self).killed else -9
                return self.returncode

            def wait(self, timeout=None):
                return self.poll()

            def terminate(self):
                pass

            def kill(self):
                type(self).killed = True

        monkeypatch.setattr(subprocess, "Popen", _Stuck)
        port = _free_port()
        with pytest.raises(RuntimeError) as ei:
            dr._dash_launch_app(app, port, 0, True)
        assert ("no server started on port %d: the app could not be "
                "handed to Python" % port) in str(ei.value)
        assert _Stuck.killed
        assert "dash: the server answers" not in capsys.readouterr().out

    def test_an_app_that_cannot_be_read_is_a_launch_failure(self, tmp_path,
                                                            monkeypatch):
        run, written = _written_run_app(tmp_path)
        os.unlink(run["app"])
        Fake = _fake_proc_class()
        monkeypatch.setattr(subprocess, "Popen", Fake)
        with pytest.raises(RuntimeError) as ei:
            dr._dash_launch_app(run["app"], _free_port(), 0, True,
                                expect=written)
        assert not isinstance(ei.value, _unsafe())
        assert "the app could not be read" in str(ei.value)
        assert Fake.made == 0

    def test_no_module_beside_the_app_or_in_the_working_folder_is_imported(
            self, tmp_path, monkeypatch, capsys):
        appdir = tmp_path / "appdir"
        appdir.mkdir(mode=0o700)
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        marker = str(tmp_path / "marker.txt")
        app = str(appdir / "app.py")
        with open(app, "w") as fh:
            fh.write("import hashlib, types\nprint('TINY OK', flush=True)\n")
        os.chmod(app, 0o600)
        for d in (appdir, cwd):
            for mod in ("linecache", "hashlib", "types"):
                (d / (mod + ".py")).write_text(
                    "open(%r, 'a').write(%r)\nraise SystemExit(4)\n"
                    % (marker, mod + " "))
        monkeypatch.chdir(str(cwd))
        try:
            dr._dash_launch_app(app, _free_port(), 0, True)
        finally:
            monkeypatch.chdir(_ROOT)
        assert not os.path.exists(marker), open(marker).read()
        assert "TINY OK" in capsys.readouterr().out


# ===========================================================================
# The bootstrap (_DASH_BOOT)
# ===========================================================================

def _boot(tmp_path, src, args=(), extra=b"", frame=None, cwd=None,
          timeout=60):
    app = os.path.join(str(tmp_path), "never", "app.py")
    boot = getattr(dr, "_DASH_BOOT")
    if frame is None:
        frame = getattr(dr, "_dash_app_frame")(src.encode("utf-8"))
    return subprocess.run(
        [sys.executable, "-P", "-c", boot, app] + list(args),
        input=frame + extra, capture_output=True, timeout=timeout,
        cwd=cwd or str(tmp_path)), app


class TestTheBootstrap:

    def test_it_runs_the_text_as_main_with_the_apps_name_and_argv(
            self, tmp_path):
        src = ("import argparse, sys\n"
               "print(__name__, __file__ == sys.argv[0], sys.argv[1:],"
               " flush=True)\n"
               "p = argparse.ArgumentParser()\n"
               "p.add_argument('--port', type=int)\n"
               "p.parse_args()\n")
        r, app = _boot(tmp_path, src, ["--port", "x"])
        assert "__main__ True ['--port', 'x']" in r.stdout.decode()
        assert r.returncode == 2
        assert "usage: app.py" in r.stderr.decode()

    def test_a_traceback_names_the_apps_file_line_and_text(self, tmp_path):
        src = ("import sys\nx = 1\ndef f():\n"
               "    raise ValueError('boom in app')\nf()\n")
        r, app = _boot(tmp_path, src)
        err = r.stderr.decode()
        assert r.returncode == 1
        assert 'File "%s", line 4, in f' % app in err, err
        assert "raise ValueError('boom in app')" in err, err

    def test_exit_statuses_are_those_of_a_script_run(self, tmp_path):
        r, _ = _boot(tmp_path, "raise SystemExit(130)\n")
        assert r.returncode == 130
        if sys.platform != "win32":
            r, _ = _boot(tmp_path, "raise KeyboardInterrupt\n")
            assert r.returncode == -signal.SIGINT

    def test_bytes_after_the_frame_are_left_on_stdin(self, tmp_path):
        src = ("import os\nb = b''\n"
               "while not b.endswith(b'\\n'):\n"
               "    c = os.read(0, 1)\n"
               "    if not c:\n        break\n"
               "    b += c\n"
               "print('LINE %d' % len(b))\n"
               "r = b''\nwhile True:\n"
               "    c = os.read(0, 4096)\n"
               "    if not c:\n        break\n"
               "    r += c\n"
               "print('EOF after %d more bytes' % len(r))\n")
        extra = b"k" * 42 + b"\n" + b"0123456789"
        r, _ = _boot(tmp_path, src, extra=extra)
        out = r.stdout.decode()
        assert "LINE 43" in out and "EOF after 10 more bytes" in out, \
            (out, r.stderr)

    def test_a_damaged_or_short_frame_runs_nothing(self, tmp_path):
        src = b'print("SHOULD NOT RUN")\n'
        good = getattr(dr, "_dash_app_frame")(src)
        head, _, body = good.partition(b"\n")
        bad = head[:-4] + b"0000" + b"\n" + body
        r, _ = _boot(tmp_path, "", frame=bad)
        assert r.returncode == 1
        assert b"was damaged" in r.stderr
        assert b"SHOULD NOT RUN" not in r.stdout
        r, _ = _boot(tmp_path, "", frame=good[:-5])
        assert r.returncode == 1
        assert b"was not handed over" in r.stderr
        assert b"SHOULD NOT RUN" not in r.stdout
        r, _ = _boot(tmp_path, "", frame=b"garbage\n")
        assert r.returncode == 1 and b"was not handed over" in r.stderr

    def test_neither_the_working_folder_nor_the_apps_folder_is_on_sys_path(
            self, tmp_path):
        src = ("import sys, os\n"
               "print(sys.flags.safe_path, '' in sys.path,"
               " os.path.dirname(sys.argv[0]) in sys.path,"
               " os.getcwd() in sys.path)\n")
        r, _ = _boot(tmp_path, src)
        assert r.stdout.decode().split() == ["True", "False", "False",
                                             "False"], r.stderr

    def test_the_text_survives_windows_quoting(self):
        boot = getattr(dr, "_DASH_BOOT")
        assert '"' not in boot and "\\" not in boot
        assert subprocess.list2cmdline(
            [sys.executable, "-c", boot]).endswith(' "' + boot + '"')

    def test_a_large_app_is_handed_over_whole(self, tmp_path):
        src = "# " + "x" * (20 * 1024 * 1024) + "\nprint('BIG OK')\n"
        t0 = time.monotonic()
        r, _ = _boot(tmp_path, src, timeout=60)
        assert r.returncode == 0 and b"BIG OK" in r.stdout
        assert time.monotonic() - t0 < 30

    def test_a_crlf_translated_frame_runs_nothing(self, tmp_path):
        src = b'print("SHOULD NOT RUN")\n# padding\n'
        good = getattr(dr, "_dash_app_frame")(src)
        head, _, body = good.partition(b"\n")
        leg1 = head + b"\n" + body.replace(b"\n", b"\r\n")
        r, _ = _boot(tmp_path, "", frame=leg1)
        assert r.returncode == 1
        assert b"was damaged" in r.stderr
        assert b"SHOULD NOT RUN" not in r.stdout
        leg2 = good.replace(b"\n", b"\r\n")
        r, _ = _boot(tmp_path, "", frame=leg2)
        assert r.returncode == 1
        assert b"SHOULD NOT RUN" not in r.stdout
        assert b"was damaged" in r.stderr or \
            b"was not handed over" in r.stderr


# ===========================================================================
# The spec writer (_dash_tmp_write_text)
# ===========================================================================

class TestTheSpecWriter:

    def test_text_is_written_exactly_and_0600(self, tmp_path):
        w = getattr(dr, "_dash_tmp_write_text")
        unit = '`"compound"\' \\back\\slash 中文 ' + "\u00e9 "
        text = (unit * (300_000 // len(unit) + 1))[:300_000]
        p = str(tmp_path / "spec.json")
        with _umask(0o022):
            assert w(p, text) == ""
        with open(p, "rb") as fh:
            assert fh.read() == text.encode("utf-8")
        assert oct(_mode(p)) == oct(0o600)

    def test_the_python_writer_keeps_backtick_and_dollar_sequences_literal(
            self, tmp_path):
        w = getattr(dr, "_dash_tmp_write_text")
        text = "`x' $y `c(pid)'"
        p = str(tmp_path / "s.json")
        assert w(p, text) == ""
        with open(p, encoding="utf-8") as fh:
            assert fh.read() == text

    def test_a_link_at_the_path_raises_and_its_target_is_kept(self,
                                                              tmp_path):
        w = getattr(dr, "_dash_tmp_write_text")
        victim = tmp_path / "victim"
        victim.write_text("V")
        link = str(tmp_path / "spec.json")
        os.symlink(str(victim), link)
        with pytest.raises(Exception) as ei:
            w(link, "{}")
        assert isinstance(ei.value, _unsafe()), repr(ei.value)
        assert "refused to write" in str(ei.value)
        assert "it is a link" in str(ei.value)
        assert victim.read_text() == "V"


# ===========================================================================
# Windows portability (run on macOS by monkeypatching)
# ===========================================================================

class TestWindowsPortability:

    def test_writer_and_root_work_without_O_NOFOLLOW_O_CLOEXEC_fchmod_getuid(  # noqa: E501
            self, tmp_path, monkeypatch):
        proot = getattr(dr, "_dash_private_root")
        write = getattr(dr, "_dash_private_write")
        for n in ("O_NOFOLLOW", "O_CLOEXEC", "fchmod", "getuid"):
            monkeypatch.delattr(os, n, raising=False)
        root, note = proot(str(tmp_path))
        assert os.path.basename(root) == "dash" and note == ""
        p = os.path.join(root, "x.json")
        st = write(p, "hello")
        assert stat.S_ISREG(st.st_mode)
        with open(p) as fh:
            assert fh.read() == "hello"

    def test_the_verified_read_works_without_O_NOFOLLOW_and_getuid(
            self, tmp_path, monkeypatch):
        run, written = _written_run_app(tmp_path)
        read = getattr(dr, "_dash_read_verified_app")
        for n in ("O_NOFOLLOW", "O_NONBLOCK", "O_CLOEXEC", "getuid"):
            monkeypatch.delattr(os, n, raising=False)
        data = read(run["app"], written)
        with open(run["app"], "rb") as fh:
            assert data == fh.read()
        assert hashlib.sha256(data).hexdigest() == written.sha256

    def test_a_reparse_point_is_refused_on_windows(self, tmp_path,
                                                   monkeypatch):
        run, written = _written_run_app(tmp_path)
        read = getattr(dr, "_dash_read_verified_app")
        app = run["app"]
        copy = str(tmp_path / "copy.py")
        shutil.copy(app, copy)
        link = str(tmp_path / "link.py")
        os.symlink(copy, link)
        port = _free_port()
        real_lstat = os.lstat
        real_open = os.open
        opened = []

        def _lstat(p, *a, **kw):
            if p == app:
                return types.SimpleNamespace(
                    st_mode=stat.S_IFREG | 0o600,
                    st_file_attributes=getattr(
                        stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
            return real_lstat(p, *a, **kw)

        def _open(p, *a, **kw):
            opened.append(p)
            return real_open(p, *a, **kw)
        Fake = _fake_proc_class()
        monkeypatch.setattr(os, "lstat", _lstat)
        monkeypatch.setattr(os, "open", _open)
        monkeypatch.setattr(subprocess, "Popen", Fake)
        monkeypatch.setattr(os, "name", "nt")
        try:
            with pytest.raises(Exception) as ei:
                read(app, None)
            e1 = ei.value
            with pytest.raises(Exception) as ei:
                dr._dash_launch_app(app, port, 0, True, expect=written,
                                    prebind=False)
            e2 = ei.value
            monkeypatch.delattr(os, "O_NOFOLLOW", raising=False)
            with pytest.raises(Exception) as ei:
                read(link, None)
            e3 = ei.value
        finally:
            monkeypatch.setattr(os, "name", "posix")
        for e in (e1, e2, e3):
            assert isinstance(e, _unsafe()), repr(e)
            assert "refused to run" in str(e) and "(it is a link)" in str(e)
        assert app not in opened
        assert Fake.made == 0


# ===========================================================================
# dash.ado routes everything through the private folder
# ===========================================================================

_NEW_PROGRAMS = ("_dash_xm_load", "_dash_tmp_open", "_dash_tmp_preview",
                 "_dash_tmp_close", "_dash_tmp_clear")


def _strip_comments(text):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("//") or s.startswith("*"):
            continue
        line = re.sub(r"\s+//.*$", "", line)
        if line.strip():
            out.append(line)
    return out


def _programs():
    with open(_ADO, encoding="utf-8") as fh:
        ado = fh.read()
    progs = {}
    for m in re.finditer(r"(?ms)^program define (\w+)[^\n]*\n(.*?)^end\b",
                         ado):
        progs[m.group(1)] = _strip_comments(m.group(2))
    return progs


def _need(progs, *names):
    for n in names:
        assert n in progs, "dash.ado has no program %s" % n


def _py_lines(lines):
    return [ln.strip() for ln in lines if ln.strip().startswith("python:")]


class TestTheAdoUsesThePrivateDir:

    def test_no_render_route_names_a_stata_tempfile_for_data(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        for p in ("_dash_render_immediate", "_dash_build", "_dash_serve"):
            text = "\n".join(progs[p])
            for bad in ("tempfile saving_path_tmp", "data_json_path spec",
                        "tempfile data_json_path", "tempfile serve_app_path"):
                assert bad not in text, (p, bad)

    def test_every_render_route_opens_then_closes_a_run(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        for p in ("_dash_render_immediate", "_dash_build", "_dash_serve"):
            text = "\n".join(progs[p])
            i = text.find("_dash_tmp_open")
            j = text.rfind("_dash_tmp_close")
            assert 0 <= i < j, p

    def test_the_spec_and_empty_data_are_written_by_python(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        for p in ("_dash_empty_data", "_dash_render_immediate", "_dash_prepare_spec"):
            text = "\n".join(progs[p])
            assert "file write" not in text, p
            assert "_dash_xm._dash_tmp_write_text(" in text, p

    def test_python_reads_paths_by_value(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        lines = []
        for p in _NEW_PROGRAMS + ("_dash_empty_data",):
            lines += _py_lines(progs[p])
        for p in ("_dash_render_immediate", "_dash_prepare_spec"):
            lines += [ln for ln in _py_lines(progs[p])
                      if "_dash_tmp_write_text" in ln]
        assert lines
        for ln in lines:
            assert "`" not in ln and "$" not in ln, ln

    def test_every_new_python_line_is_an_assignment_or_a_setlocal(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        ok = re.compile(r"^python:\s+(import\s|from\s\S+\simport\s|"
                        r"[A-Za-z_][\w\.]*(\[[^\]]*\])?\s*=[^=]|"
                        r"_dash_\w*M\.setLocal\()")
        lines = []
        for p in _NEW_PROGRAMS + ("_dash_empty_data",):
            lines += _py_lines(progs[p])
        for p in ("_dash_render_immediate", "_dash_prepare_spec", "_dash_do_render"):
            lines += [ln for ln in _py_lines(progs[p])
                      if "_dash_tmp_write_text" in ln or "private" in ln]
        for ln in lines:
            assert ok.match(ln), ln

    def test_each_python_program_calls_dash_require_python_first(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        for name, lines in progs.items():
            idx = [i for i, ln in enumerate(lines)
                   if ln.strip().startswith("python:")]
            if not idx:
                continue
            guard = [i for i, ln in enumerate(lines)
                     if ln.strip() == "_dash_require_python"]
            assert guard and guard[0] < idx[0], name

    def test_the_run_paths_are_read_from_r_on_the_next_line(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        for p in ("_dash_render_immediate", "_dash_build", "_dash_serve"):
            lines = [ln.strip() for ln in progs[p]]
            i = lines.index("_dash_tmp_open")
            assert "r(rundir)" in lines[i + 1], (p, lines[i + 1])
            for k in range(1, 4):
                assert lines[i + k].startswith("local "), (p, lines[i + k])
                assert "r(" in lines[i + k], (p, lines[i + k])

    def test_dash_clear_prunes_through_a_captured_call(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        text = "\n".join(progs["_dash_clear"])
        i = text.find("capture _dash_tmp_clear")
        assert 0 <= i < text.find("registry cleared")

    def test_empty_data_keeps_its_trailing_newline_and_the_spec_has_none(
            self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        ed = [ln for ln in _py_lines(progs["_dash_empty_data"])
              if "_dash_tmp_write_text" in ln]
        assert len(ed) == 1 and "+ chr(10)" in ed[0], ed
        for p in ("_dash_render_immediate", "_dash_prepare_spec"):
            sp = [ln for ln in _py_lines(progs[p])
                  if "_dash_tmp_write_text" in ln]
            assert len(sp) == 1 and "chr(10)" not in sp[0], (p, sp)

    def test_exit_603_follows_only_an_os_failure_of_the_folder(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        total = 0
        for p in ("_dash_tmp_open", "_dash_tmp_preview", "_dash_empty_data",
                  "_dash_render_immediate", "_dash_prepare_spec"):
            lines = [ln.strip() for ln in progs[p]]
            n = sum(1 for ln in lines if ln == "exit 603")
            total += n
            if p in ("_dash_tmp_open", "_dash_tmp_preview"):
                assert n == 1, p
                k = lines.index("exit 603")
                err = "_to_err" if p == "_dash_tmp_open" else "_tp_err"
                block = " ".join(lines[max(0, k - 3):k])
                assert "length local %s" % err in block, (p, block)
            else:
                assert n == 0, p
            for i, ln in enumerate(lines):
                if "_dash_tmp_write_text" in ln and i + 1 < len(lines):
                    assert "_err" not in lines[i + 1], (p, lines[i + 1])
        assert total == 2

    def test_the_note_is_printed_once_per_command(self):
        progs = _programs()
        _need(progs, *_NEW_PROGRAMS)
        to = "\n".join(progs["_dash_tmp_open"])
        assert '_dash_say("txt"' in to and "_to_note" in to
        assert re.search(r"return local noted\b", to)
        plot = [ln.strip() for ln in progs["_dash_render_immediate"]]
        i = [k for k, ln in enumerate(plot) if "r(data)" in ln][0]
        assert "r(noted)" in plot[i + 1], plot[i + 1]
        assert any("_dash_tmp_preview" in ln and "noted(`_dash_noted')" in ln
                   for ln in plot)
        tp = "\n".join(progs["_dash_tmp_preview"])
        assert re.search(r'if "`noted\'" != "1"', tp)
        for p in ("_dash_build", "_dash_serve", "_dash_clear"):
            text = "\n".join(progs[p])
            assert "dash: note:" not in text and "_to_note" not in text, p


# ===========================================================================
# The help
# ===========================================================================

def _help():
    with open(_HLP, encoding="utf-8") as fh:
        return fh.read()


def _tempfiles_section():
    h = _help()
    assert "{marker tempfiles}" in h, "dash.sthlp has no {marker tempfiles}"
    sec = h.split("{marker tempfiles}", 1)[1]
    return sec.split("{marker ", 1)[0]


def _flat(text):
    return re.sub(r"\s+", " ", text)


def _independent_passage():
    h = _help()
    i = h.find("Running the generated .py file independently")
    assert i >= 0
    return h[i:i + 4000]


class TestTheHelpDocumentsTheTempfiles:

    def test_the_section_exists_and_is_linked(self):
        h = _help()
        assert "{marker tempfiles}" in h
        assert "{title:Temporary files and privacy}" in h
        assert '{viewerjumpto "Temporary files"   "dash##tempfiles"}' in h
        assert h.count("dash##tempfiles") >= 4
        assert h.index("{marker tempfiles}") < h.index("{marker limits}")

    def test_it_states_the_modes_the_folder_and_the_pruning(self):
        sec = _flat(_tempfiles_section())
        for s in ("0700", "0600", "run-", "previews", "five",
                  "{cmd:dash clear}", "last minute"):
            assert s in sec, s

    def test_it_states_the_note_and_the_anti_hijack_guard(self):
        sec = _flat(_tempfiles_section())
        for s in ("dash: note:", "chmod go-w", "STATATMP",
                  "never stops a command for privacy", "r(7102)",
                  "never writes through a symbolic link", "r(603)"):
            assert s in sec, s
        sents = [x for x in re.split(r"(?<=\.)\s", sec) if "r(603)" in x]
        assert len(sents) == 1, sents
        assert "read-only" in sents[0]
        for bad in ("private", "link", "another account"):
            assert bad not in sents[0], (bad, sents[0])

    def test_no_passage_says_stata_erases_the_app(self):
        h = _flat(_help())
        assert "Stata erases its temporary copy" not in h
        assert "Stata erases the" not in h

    def test_it_says_a_named_server_app_holds_the_data_and_is_0600(self):
        both = _flat(_tempfiles_section() + _independent_passage())
        for s in ("every observation", "0600", "replace", "symbolic link"):
            assert s in both, s

    def test_it_says_dash_serve_runs_the_text_it_checked(self):
        sec = _flat(_tempfiles_section())
        assert "hands the text to Python" in sec
        assert "never run" in sec
        assert "instant" not in sec
        ind = _flat(_independent_passage())
        assert "by its name" in ind
        assert "imports modules from the folder" in ind
