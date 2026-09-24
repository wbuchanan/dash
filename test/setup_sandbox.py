"""setup_sandbox.py -- run dash_setup end to end without installing anything.

``test_program_coverage.cscript`` loads this module into Stata's embedded
Python and calls it through single-line ``python:`` statements.  Standard
library only: it runs inside the interpreter dash_setup checks, and must
work whatever that interpreter lacks.

WHY
---
dash_setup was never executed by any test (GAPS.md L7): it installs Python
packages into the user's real environment, so every earlier test drove its
subprograms one at a time.  dash_setup installs through exactly two doors,
both of which this sandbox closes before the command runs:

* Python packages: ``subprocess.run([sys.executable, "-m", "pip", ...])``
  inside ``python:``.  Every process-starting function of ``subprocess``,
  ``os`` and ``asyncio`` is replaced by a recorder that records the argument
  vector and starts nothing; ``sys.executable`` is pointed at a recording
  stub; and a directory of recording ``pip``/``python`` stubs is put first
  on ``PATH``, so a process started some other way -- a Stata ``shell``, a
  future change -- still reaches no real installer.
* jsonio: ``ssc install``.  The certification script defines its own
  ``ssc`` program for the duration (a program in memory is found before an
  ado-file), which records the call and installs nothing.

``install()`` refuses to report success until ``self_test()`` has shown a
process start being recorded and not run.  ``restore()`` undoes everything,
and is safe to call twice.

The states dash_setup reacts to are simulated without touching the
environment: a package is made unimportable by ``sys.modules[name] = None``
(the import system's own "halted" marker), a package version by a fake
``.dist-info`` directory first on ``sys.path``, the interpreter's version by
``sys.version``.  ``unblock_on_install`` lets a recorded ``pip install``
lift the block, which is what a successful install would do.
"""
import asyncio
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

#: The stub every recorded process "returns", and the stubs' exit status.
_STUB_RC = 97
_STUB_NOTE = "[dash test sandbox] no process was started"

_MISSING = object()
_state = None


class _Recorded:
    """What a recorded process start hands back: a failed, finished process.

    Duck-typed for the attributes dash_setup and ``subprocess`` callers read:
    ``args``, ``returncode``, ``stdout``, ``stderr``; ``wait``/``poll``/
    ``communicate`` for ``Popen`` users.
    """

    def __init__(self, args, text=False):
        self.args = args
        self.returncode = _STUB_RC
        self.pid = 0
        empty = "" if text else b""
        self.stdout = _STUB_NOTE if text else _STUB_NOTE.encode()
        self.stderr = empty
        self.stdin = None

    def wait(self, timeout=None):
        return self.returncode

    def poll(self):
        return self.returncode

    def communicate(self, input=None, timeout=None):
        return self.stdout, self.stderr

    def kill(self):
        pass

    terminate = kill

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _argv(args):
    if isinstance(args, (list, tuple)):
        return [str(a) for a in args]
    return [str(args)]


class _Sandbox:
    def __init__(self, workdir):
        self.workdir = workdir
        self.calls = []
        self.saved_attrs = []
        self.saved_modules = {}
        self.saved_path = list(sys.path)
        self.saved_env_path = os.environ.get("PATH", _MISSING)
        self.saved_executable = sys.executable
        self.saved_version = sys.version
        self.fake_dirs = []
        self.unblock_on_install = set()
        self.stub_log = os.path.join(workdir, "stub_calls.log")
        self.stubdir = os.path.join(workdir, "bin")

    # -- recording -------------------------------------------------------
    def record(self, kind, args):
        argv = _argv(args)
        self.calls.append({"via": kind, "argv": argv})
        # A recorded `pip install X' lifts X's block when the case asked for
        # that: the install "succeeded".
        if "install" in argv:
            for name in list(self.unblock_on_install):
                if any(a == name or a.startswith(name + ">") or
                       a.startswith(name + "=") for a in argv):
                    self.unblock(name)
                    self.unblock_on_install.discard(name)

    def _patch(self, owner, name, value):
        self.saved_attrs.append((owner, name, getattr(owner, name, _MISSING)))
        setattr(owner, name, value)

    def _install_recorders(self):
        sb = self

        def run(args, *a, **k):
            sb.record("subprocess.run", args)
            return _Recorded(args, text=bool(k.get("text") or
                                              k.get("universal_newlines") or
                                              k.get("encoding")))

        def call(args, *a, **k):
            sb.record("subprocess.call", args)
            return _STUB_RC

        def check_call(args, *a, **k):
            sb.record("subprocess.check_call", args)
            raise subprocess.CalledProcessError(_STUB_RC, args)

        def check_output(args, *a, **k):
            sb.record("subprocess.check_output", args)
            raise subprocess.CalledProcessError(_STUB_RC, args)

        def getoutput(cmd, *a, **k):
            sb.record("subprocess.getoutput", cmd)
            return _STUB_NOTE

        def getstatusoutput(cmd, *a, **k):
            sb.record("subprocess.getstatusoutput", cmd)
            return _STUB_RC, _STUB_NOTE

        class Popen(_Recorded):
            def __init__(self, args, *a, **k):
                sb.record("subprocess.Popen", args)
                _Recorded.__init__(self, args, text=bool(k.get("text")))

        def system(cmd):
            sb.record("os.system", cmd)
            return _STUB_RC << 8

        def popen(cmd, *a, **k):
            sb.record("os.popen", cmd)
            raise OSError(_STUB_NOTE)

        def refuse(name):
            def f(*a, **k):
                sb.record("os." + name, list(a[:2]))
                raise OSError(_STUB_NOTE)
            return f

        async def create_subprocess_exec(*a, **k):
            sb.record("asyncio.create_subprocess_exec", list(a))
            raise OSError(_STUB_NOTE)

        async def create_subprocess_shell(cmd, *a, **k):
            sb.record("asyncio.create_subprocess_shell", cmd)
            raise OSError(_STUB_NOTE)

        for name, fn in (("run", run), ("call", call),
                         ("check_call", check_call),
                         ("check_output", check_output),
                         ("getoutput", getoutput),
                         ("getstatusoutput", getstatusoutput),
                         ("Popen", Popen)):
            self._patch(subprocess, name, fn)
        self._patch(os, "system", system)
        self._patch(os, "popen", popen)
        for name in ("execv", "execve", "execl", "execle", "execlp",
                     "execlpe", "execvp", "execvpe", "spawnv", "spawnve",
                     "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnvp",
                     "spawnvpe", "posix_spawn", "posix_spawnp", "fork",
                     "forkpty"):
            if hasattr(os, name):
                self._patch(os, name, refuse(name))
        self._patch(asyncio, "create_subprocess_exec", create_subprocess_exec)
        self._patch(asyncio, "create_subprocess_shell", create_subprocess_shell)

    def _install_stubs(self):
        """Recording stand-ins for every installer name, first on PATH,
        and for sys.executable."""
        os.makedirs(self.stubdir, exist_ok=True)
        body = ("#!/bin/sh\n"
                "printf '%%s\\n' \"$0 $*\" >> '%s'\n"
                "exit %d\n") % (self.stub_log.replace("'", ""), _STUB_RC)
        for name in ("pip", "pip3", "python", "python3", "conda", "mamba",
                     "uv", "easy_install"):
            p = os.path.join(self.stubdir, name)
            with open(p, "w") as fh:
                fh.write(body)
            os.chmod(p, 0o755)
        old = os.environ.get("PATH", "")
        os.environ["PATH"] = self.stubdir + (os.pathsep + old if old else "")
        sys.executable = os.path.join(self.stubdir, "python3")

    # -- simulated states -------------------------------------------------
    def block(self, name):
        if name not in self.saved_modules:
            self.saved_modules[name] = sys.modules.get(name, _MISSING)
        sys.modules[name] = None

    def unblock(self, name):
        if name in self.saved_modules:
            old = self.saved_modules.pop(name)
            if old is _MISSING:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old

    def fake_dist(self, name, version):
        root = tempfile.mkdtemp(prefix="dash_fake_dist_", dir=self.workdir)
        info = os.path.join(root, "%s-0.0.dist-info" % name)
        os.makedirs(info)
        with open(os.path.join(info, "METADATA"), "w", encoding="utf-8") as fh:
            fh.write("Metadata-Version: 2.1\nName: %s\nVersion: %s\n"
                     % (name, version))
        sys.path.insert(0, root)
        self.fake_dirs.append(root)
        importlib.invalidate_caches()

    def set_python_version(self, text):
        sys.version = text

    # -- undo ---------------------------------------------------------------
    def restore(self):
        for owner, name, value in reversed(self.saved_attrs):
            if value is _MISSING:
                try:
                    delattr(owner, name)
                except AttributeError:
                    pass
            else:
                setattr(owner, name, value)
        self.saved_attrs = []
        for name in list(self.saved_modules):
            self.unblock(name)
        sys.path[:] = self.saved_path
        importlib.invalidate_caches()
        if self.saved_env_path is _MISSING:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = self.saved_env_path
        sys.executable = self.saved_executable
        sys.version = self.saved_version


# ---------------------------------------------------------------------------
# The interface the certification script calls
# ---------------------------------------------------------------------------

#: What dash_setup imports to check.  Imported (when installed) before any
#: block is applied, so that blocking one -- `packaging', say -- cannot break
#: the import of another that uses it internally; each is then a cached
#: module whose `import' dash_setup's check still performs.
PREIMPORT = ("packaging", "packaging.version", "numpy", "pandas", "bokeh")


def install(block=(), unblock_on_install=(), fake=(), pyversion=None):
    """Close both install doors, then set up the simulated state.

    block              names made unimportable (``sys.modules[name] = None``)
    unblock_on_install names whose block a recorded ``pip install`` lifts
    fake               ``(name, version)`` pairs of fake distributions
    pyversion          a replacement ``sys.version`` (its first word is what
                       dash_setup reads)

    Returns the sandbox's working directory.  Raises if a sandbox is already
    installed or the self-test fails -- in which case nothing stays patched.
    """
    global _state
    if _state is not None:
        raise RuntimeError("a dash_setup sandbox is already installed")
    for name in PREIMPORT:
        try:
            importlib.import_module(name)
        except ImportError:
            pass            # absent here: dash_setup will say so
    sb = _Sandbox(tempfile.mkdtemp(prefix="dash_setup_sandbox_"))
    _state = sb
    try:
        sb._install_recorders()
        sb._install_stubs()
        self_test()
        for name in block:
            sb.block(name)
        sb.unblock_on_install = set(unblock_on_install)
        for name, version in fake:
            sb.fake_dist(name, version)
        if pyversion is not None:
            sb.set_python_version(pyversion)
    except BaseException:
        restore()
        raise
    return sb.workdir


def self_test():
    """Show that a process start is recorded and not run.

    Asks the replaced ``subprocess.run`` and ``os.system`` to create a marker
    file through the real interpreter; neither may create it, and both must
    be recorded.  The two probe calls are then forgotten.
    """
    sb = _state
    marker = os.path.join(sb.workdir, "self_test_marker")
    code = "open(%r, 'w').close()" % marker
    n = len(sb.calls)
    subprocess.run([sb.saved_executable, "-c", code], capture_output=True)
    os.system("%s -c %s" % (sb.saved_executable, json.dumps(code)))
    if os.path.exists(marker):
        raise RuntimeError("sandbox self-test: a process ran")
    if len(sb.calls) != n + 2:
        raise RuntimeError("sandbox self-test: a process start was not "
                           "recorded")
    del sb.calls[n:]
    return True


def calls():
    """Every recorded process start, as ``[{"via": ..., "argv": [...]}]``,
    with the sandbox's stub interpreter written ``PYTHON``."""
    if _state is None:
        return []
    out = []
    for c in _state.calls:
        argv = ["PYTHON" if a == os.path.join(_state.stubdir, "python3")
                else a for a in c["argv"]]
        out.append({"via": c["via"], "argv": argv})
    return out


def stub_calls():
    """Lines the PATH stubs wrote: a process that got past the recorders."""
    if _state is None or not os.path.exists(_state.stub_log):
        return []
    with open(_state.stub_log) as fh:
        return [l.rstrip("\n") for l in fh]


def restore():
    """Undo everything ``install`` did.  Safe to call when nothing is
    installed."""
    global _state
    sb = _state
    _state = None
    if sb is None:
        return
    try:
        sb.restore()
    finally:
        shutil.rmtree(sb.workdir, ignore_errors=True)


def is_installed():
    return _state is not None


# ---------------------------------------------------------------------------
# Stata-facing wrappers.  Inputs are read from Stata globals by value
# (sfi.Macro.getGlobal: JSON with quotes in it cannot pass through a
# program's arguments intact); results go back as locals of the calling
# program (sfi.Macro.setLocal).
# ---------------------------------------------------------------------------

def stata_install(spec_global="PC_SB_SPEC"):
    """``install(**json.loads($PC_SB_SPEC))``; sets the locals pc_sb_ok
    ("1" or "0") and pc_sb_why (the reason)."""
    from sfi import Macro
    try:
        spec = json.loads(Macro.getGlobal(spec_global) or "{}")
        install(block=spec.get("block", ()),
                unblock_on_install=spec.get("unblock_on_install", ()),
                fake=[tuple(p) for p in spec.get("fake", ())],
                pyversion=spec.get("pyversion"))
        Macro.setLocal("pc_sb_ok", "1")
        Macro.setLocal("pc_sb_why", "")
    except BaseException as exc:  # reported to Stata, which fails the case
        Macro.setLocal("pc_sb_ok", "0")
        Macro.setLocal("pc_sb_why", "%s: %s" % (type(exc).__name__, exc))


def stata_verdict(expect_global="PC_SB_EXPECT"):
    """Compare the recorded argument vectors with the JSON list in
    $PC_SB_EXPECT (order matters), and require that no PATH stub ran.
    Sets the locals pc_sb_match ("1"/"0"), pc_sb_n (calls recorded) and
    pc_sb_mwhy (what was recorded, when it does not match)."""
    from sfi import Macro
    want = json.loads(Macro.getGlobal(expect_global) or "[]")
    got = [c["argv"] for c in calls()]
    stubs = stub_calls()
    ok = got == want and not stubs
    Macro.setLocal("pc_sb_match", "1" if ok else "0")
    Macro.setLocal("pc_sb_n", str(len(got)))
    Macro.setLocal("pc_sb_mwhy", "" if ok else
                   "recorded %s; expected %s; PATH stubs ran %s"
                   % (json.dumps(got), json.dumps(want), json.dumps(stubs)))


def stata_restored():
    """Sets the local pc_sb_clean to "1" when no sandbox is installed and
    every patched name is the original object again."""
    from sfi import Macro
    clean = (_state is None and subprocess.run is _ORIGINAL["run"]
             and subprocess.Popen is _ORIGINAL["Popen"]
             and os.system is _ORIGINAL["system"]
             and sys.executable == _ORIGINAL["executable"])
    Macro.setLocal("pc_sb_clean", "1" if clean else "0")


#: The objects install() replaces, captured when this module is imported --
#: before any sandbox exists -- so stata_restored() can prove restore().
_ORIGINAL = {"run": subprocess.run, "Popen": subprocess.Popen,
             "system": os.system, "executable": sys.executable}
