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
* SSC: dash_setup ran ``ssc install jsonio`` until dash stopped using
  jsonio (24sep2026) and runs no ``ssc`` now.  The certification script
  still defines its own ``ssc`` program for the duration (a program in
  memory is found before an ado-file), which records any call and installs
  nothing.

``install()`` refuses to report success until ``self_test()`` has shown a
process start being recorded and not run.  ``restore()`` undoes everything,
and is safe to call twice.

The states dash_setup reacts to are simulated without touching the
environment: a package, and each submodule of it already imported, is made
unimportable by ``sys.modules[name] = None`` (the import system's own
"halted" marker), a package version by a fake ``.dist-info`` directory
first on ``sys.path``, the interpreter's version by ``sys.version``.  ``unblock_on_install`` lets a recorded ``pip install``
lift the block, which is what a successful install would do (it then
returns rc 0, as a successful install does).

WP-29 P0.19: dash_setup now starts its children through dash_setup_lib.py,
which inspects the linked Python in a child first (a ``-c`` probe whose code
holds ``DASH_DETECT_V1``), may build a venv (``-m venv <path>``) and verify
it (``DASH_VERIFY_V1``).  The recorder answers each of these from the case's
spec instead of starting anything:

* the DETECT probe gets the JSON line a real interpreter would print --
  ``env`` for the linked interpreter (the one ``c(python_exec)`` names),
  ``venv_env`` for any other -- so "externally managed", "in a venv" and
  "no pip" are answers, and no real stdlib is touched;
* ``-m venv <path>`` creates ``<path>/pyvenv.cfg`` and ``<path>/bin/python``;
* the VERIFY probe gets ``verify``'s JSON line;
* a pip install gets the ``pip`` response, its stderr one of the measured
  refusals in test/fixtures/pip_refusals.json;
* ``user_site_gate`` keeps a package blocked until ``site.addsitedir`` is
  called on the sandbox's user site, which a ``--user`` install of it makes.

Each call's ``cwd``, ``env`` and ``umask`` are recorded with its argv, the
linked interpreter is written ``PYTHON_EXEC`` in ``calls()``, and
``site.getusersitepackages``, ``site.ENABLE_USER_SITE``, ``site.addsitedir``
and ``PYTHONPATH`` are put back by ``restore()``.
"""
import asyncio
import importlib
import importlib.metadata
import json
import os
import shutil
import site
import subprocess
import sys
import tempfile

#: pip's measured refusal texts (scripts/extract_pip_refusals.py).
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fixtures", "pip_refusals.json")

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

    def __init__(self, args, text=False, rc=_STUB_RC, stdout=None,
                 stderr=""):
        self.args = args
        self.returncode = rc
        self.pid = 0
        out = _STUB_NOTE if stdout is None else stdout
        self.stdout = out if text else out.encode()
        self.stderr = stderr if text else stderr.encode()
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
        self.usersite = os.path.join(workdir, "usersite")
        self.env = {}
        self.venv_env = {}
        self.pip = None
        self.verify = {}
        self.user_site_gate = None
        self.python_exec = ""
        self.saved_pythonpath = os.environ.get("PYTHONPATH", _MISSING)

    # -- recording -------------------------------------------------------
    def record(self, kind, args, kw=None):
        """Record one process start.  Returns True when the call lifted a
        block (a recorded install of a package unblock_on_install names)."""
        argv = _argv(args)
        kw = kw or {}
        env = kw.get("env")
        self.calls.append({"via": kind, "argv": argv, "cwd": kw.get("cwd"),
                           "env": dict(env) if env is not None else None,
                           "umask": kw.get("umask")})
        lifted = False
        # A recorded `pip install X' lifts X's block when the case asked for
        # that: the install "succeeded".
        if "install" in argv:
            for name in list(self.unblock_on_install):
                if _names(argv, name):
                    self.unblock(name)
                    self.unblock_on_install.discard(name)
                    lifted = True
        return lifted

    # -- answers ----------------------------------------------------------
    def is_python_exec(self, exe):
        pe = self.python_exec
        return bool(pe) and exe in (pe, os.path.abspath(pe))

    def detect_answer(self, exe):
        over = self.env if self.is_python_exec(exe) else dict(
            {"in_venv": True, "pip": True}, **self.venv_env)
        d = {"tag": "DASH_DETECT_V1", "prefix": "/dash-sandbox/prefix",
             "base_prefix": "/dash-sandbox/prefix",
             "stdlib": "/dash-sandbox/prefix/lib/stdlib", "marker": False,
             "pyvenv_cfg": False, "pip": True, "ensurepip": True,
             "venv": True, "user_site_enabled": True,
             "user_site": self.usersite,
             "version": list(sys.version_info[:3]), "executable": exe}
        if over.get("managed"):
            d["marker"] = True
        if over.get("in_venv"):
            d["base_prefix"] = "/dash-sandbox/base"
        for k in ("pip", "ensurepip", "user_site_enabled", "version"):
            if k in over:
                d[k] = over[k]
        return json.dumps(d)

    def verify_answer(self):
        pk = {}
        for name in ("packaging", "bokeh", "numpy", "pandas"):
            try:
                pk[name] = importlib.metadata.version(name)
            except Exception:
                pk[name] = ""
        d = {"tag": "DASH_VERIFY_V1", "ok": True,
             "version": list(sys.version_info[:3]), "packages": pk,
             "schemes": True, "why": ""}
        d.update(self.verify)
        return json.dumps(d)

    def answer(self, args, lifted, text):
        """What a recorded process start hands back."""
        argv = _argv(args)
        if "-c" in argv[:-1]:
            code = argv[argv.index("-c") + 1]
            if "DASH_DETECT_V1" in code:
                return _Recorded(args, text, 0, self.detect_answer(argv[0]) + "\n")
            if "DASH_VERIFY_V1" in code:
                return _Recorded(args, text, 0, self.verify_answer() + "\n")
        if _module(argv) == "venv":
            path = argv[-1]
            os.makedirs(os.path.join(path, "bin"), exist_ok=True)
            open(os.path.join(path, "pyvenv.cfg"), "w").close()
            py = os.path.join(path, "bin", "python")
            open(py, "w").close()
            os.chmod(py, 0o755)
            return _Recorded(args, text, 0, "")
        if _module(argv) == "pip" and "install" in argv:
            gate = self.user_site_gate
            if gate and "--user" in argv and _names(argv, gate):
                os.makedirs(self.usersite, exist_ok=True)
                return _Recorded(args, text, 0, "")
            if self.pip is not None:
                err = ""
                if self.pip.get("stderr"):
                    with open(FIXTURE, encoding="utf-8") as fh:
                        err = json.load(fh)[self.pip["stderr"]]["stderr"]
                return _Recorded(args, text, int(self.pip.get("rc", 0)), "", err)
            if lifted:
                return _Recorded(args, text, 0, "")
        return _Recorded(args, text)

    def _patch(self, owner, name, value):
        self.saved_attrs.append((owner, name, getattr(owner, name, _MISSING)))
        setattr(owner, name, value)

    def _install_recorders(self):
        sb = self

        def run(args, *a, **k):
            lifted = sb.record("subprocess.run", args, k)
            return sb.answer(args, lifted, bool(k.get("text") or
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

    def _install_site(self):
        """The user site: where it is, that it is enabled, and an addsitedir
        that lifts the user_site_gate block when given that directory."""
        sb = self
        real_addsitedir = site.addsitedir

        def addsitedir(sitedir, known_paths=None):
            if sb.user_site_gate and os.path.abspath(sitedir) == sb.usersite:
                sb.unblock(sb.user_site_gate)
            return real_addsitedir(sitedir, known_paths)

        self._patch(site, "getusersitepackages", lambda: sb.usersite)
        self._patch(site, "ENABLE_USER_SITE", True)
        self._patch(site, "addsitedir", addsitedir)

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
        # The package and every submodule of it already imported: the
        # import system looks a dotted name up in sys.modules before it
        # looks at the name's parent, so with the package alone blocked,
        # `from packaging.version import Version' still succeeded from the
        # cache (measured 24sep2026; test_setup_sandbox.py).
        keys = [name] + [k for k in list(sys.modules)
                         if k.startswith(name + ".")]
        for key in keys:
            if key not in self.saved_modules:
                self.saved_modules[key] = sys.modules.get(key, _MISSING)
            sys.modules[key] = None

    def unblock(self, name):
        # The package and the submodules block() took with it.
        for key in [k for k in list(self.saved_modules)
                    if k == name or k.startswith(name + ".")]:
            old = self.saved_modules.pop(key)
            if old is _MISSING:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = old

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
        if self.saved_pythonpath is _MISSING:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = self.saved_pythonpath


# ---------------------------------------------------------------------------
# The interface the certification script calls
# ---------------------------------------------------------------------------

#: What dash_setup imports to check.  Imported (when installed) before any
#: block is applied, so that blocking one -- `packaging', say -- cannot break
#: the import of another that uses it internally; each is then a cached
#: module whose `import' dash_setup's check still performs.
PREIMPORT = ("packaging", "packaging.version", "numpy", "pandas", "bokeh")


def _names(argv, name):
    """Does an argument vector name the package `name' as a requirement?"""
    return any(a == name or a.startswith(name + ">") or
               a.startswith(name + "=") or a.startswith(name + ",")
               for a in argv)


def _module(argv):
    """The module a `-m' argument vector runs, else None."""
    if "-m" in argv[:-1]:
        return argv[argv.index("-m") + 1]
    return None


def install(block=(), unblock_on_install=(), fake=(), pyversion=None,
            env=None, venv_env=None, pip=None, verify=None,
            user_site_gate=None, pythonpath=None, python_exec=None):
    """Close both install doors, then set up the simulated state.

    block              names made unimportable, with each submodule
                       already imported (``sys.modules[name] = None``)
    unblock_on_install names whose block a recorded ``pip install`` lifts
    fake               ``(name, version)`` pairs of fake distributions
    pyversion          a replacement ``sys.version`` (its first word is what
                       dash_setup reads)
    env                the linked Python's DETECT answer: ``managed``,
                       ``in_venv``, ``pip``, ``ensurepip``,
                       ``user_site_enabled``, ``version`` (default: an
                       ordinary Python with pip)
    venv_env           the same, for any other interpreter (default: in a
                       venv, with pip)
    pip                ``{"rc": int, "stderr": <record in pip_refusals.json>}``
                       for every recorded ``-m pip install``
    verify             overrides of the VERIFY answer
    user_site_gate     a package kept blocked until ``site.addsitedir`` is
                       given the sandbox's user site
    pythonpath         ``os.environ["PYTHONPATH"]`` for the run
    python_exec        the linked interpreter's text (``c(python_exec)``),
                       written ``PYTHON_EXEC`` by ``calls()``

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
        sb._install_site()
        self_test()
        sb.env = dict(env or {})
        sb.venv_env = dict(venv_env or {})
        sb.pip = dict(pip) if pip is not None else None
        sb.verify = dict(verify or {})
        sb.user_site_gate = user_site_gate
        sb.python_exec = python_exec or ""
        if user_site_gate:
            sb.block(user_site_gate)
        if pythonpath is not None:
            os.environ["PYTHONPATH"] = pythonpath
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
    with the sandbox's stub interpreter written ``PYTHON`` and the linked
    interpreter (``python_exec``) ``PYTHON_EXEC``."""
    if _state is None:
        return []
    out = []
    stub = os.path.join(_state.stubdir, "python3")
    for c in _state.calls:
        argv = ["PYTHON" if a == stub else
                "PYTHON_EXEC" if _state.is_python_exec(a) else a
                for a in c["argv"]]
        out.append({"via": c["via"], "argv": argv})
    return out


def kwargs_calls():
    """Every recorded process start with its cwd, env and umask."""
    return [] if _state is None else [dict(c) for c in _state.calls]


def _match(got, want):
    """`want' with "<ANY>" matching any one argument."""
    if not isinstance(want, list) or len(got) != len(want):
        return False
    for g, w in zip(got, want):
        if not isinstance(w, list) or len(g) != len(w):
            return False
        if any(y != "<ANY>" and x != y for x, y in zip(g, w)):
            return False
    return True


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
    import sfi
    from sfi import Macro
    try:
        spec = json.loads(Macro.getGlobal(spec_global) or "{}")
        if hasattr(sfi, "SFIToolkit"):
            pe = sfi.SFIToolkit.macroExpand("\x60c(python_exec)'")
        else:
            pe = spec.get("python_exec")
        install(block=spec.get("block", ()),
                unblock_on_install=spec.get("unblock_on_install", ()),
                fake=[tuple(p) for p in spec.get("fake", ())],
                pyversion=spec.get("pyversion"),
                env=spec.get("env"), venv_env=spec.get("venv_env"),
                pip=spec.get("pip"), verify=spec.get("verify"),
                user_site_gate=spec.get("user_site_gate"),
                pythonpath=spec.get("pythonpath"), python_exec=pe)
        Macro.setLocal("pc_sb_ok", "1")
        Macro.setLocal("pc_sb_why", "")
    except BaseException as exc:  # reported to Stata, which fails the case
        Macro.setLocal("pc_sb_ok", "0")
        Macro.setLocal("pc_sb_why", "%s: %s" % (type(exc).__name__, exc))


def stata_verdict(expect_global="PC_SB_EXPECT"):
    """Compare the recorded argument vectors with the JSON list in
    $PC_SB_EXPECT (order matters; an element "<ANY>" matches any one
    argument), and require that no PATH stub ran.
    Sets the locals pc_sb_match ("1"/"0"), pc_sb_n (calls recorded) and
    pc_sb_mwhy (what was recorded, when it does not match)."""
    from sfi import Macro
    want = json.loads(Macro.getGlobal(expect_global) or "[]")
    got = [c["argv"] for c in calls()]
    stubs = stub_calls()
    ok = _match(got, want) and not stubs
    Macro.setLocal("pc_sb_match", "1" if ok else "0")
    Macro.setLocal("pc_sb_n", str(len(got)))
    Macro.setLocal("pc_sb_mwhy", "" if ok else
                   "recorded %s; expected %s; PATH stubs ran %s"
                   % (json.dumps(got), json.dumps(want), json.dumps(stubs)))


def stata_pip_kwargs():
    """Sets the locals pc_sb_cwd, pc_sb_cwdgone, pc_sb_pp, pc_sb_bsp,
    pc_sb_puser, pc_sb_dwb and pc_sb_umask from the first recorded
    ``-m pip install``: its working directory, whether that directory is
    gone, whether PYTHONPATH reached it ("1"/"0"), its
    PIP_BREAK_SYSTEM_PACKAGES, PIP_USER and PYTHONDONTWRITEBYTECODE, and
    its umask.  All empty when there was none (or no env was passed)."""
    from sfi import Macro
    first = None
    for c in kwargs_calls():
        if _module(c["argv"]) == "pip" and "install" in c["argv"]:
            first = c
            break
    vals = dict.fromkeys(("cwd", "cwdgone", "pp", "bsp", "puser", "dwb",
                          "umask"), "")
    if first is not None:
        cwd = first.get("cwd")
        if cwd:
            vals["cwd"] = str(cwd)
            vals["cwdgone"] = "0" if os.path.exists(cwd) else "1"
        env = first.get("env")
        if env is not None:
            vals["pp"] = "1" if "PYTHONPATH" in env else "0"
            vals["bsp"] = env.get("PIP_BREAK_SYSTEM_PACKAGES", "")
            vals["puser"] = env.get("PIP_USER", "")
            vals["dwb"] = env.get("PYTHONDONTWRITEBYTECODE", "")
        if first.get("umask") is not None:
            vals["umask"] = str(first["umask"])
    for k, v in vals.items():
        Macro.setLocal("pc_sb_" + k, v)


def stata_restored():
    """Sets the local pc_sb_clean to "1" when no sandbox is installed and
    every patched name is the original object again."""
    from sfi import Macro
    clean = (_state is None and subprocess.run is _ORIGINAL["run"]
             and subprocess.Popen is _ORIGINAL["Popen"]
             and os.system is _ORIGINAL["system"]
             and sys.executable == _ORIGINAL["executable"]
             and site.addsitedir is _ORIGINAL["addsitedir"]
             and site.getusersitepackages is _ORIGINAL["getusersitepackages"])
    Macro.setLocal("pc_sb_clean", "1" if clean else "0")


#: The objects install() replaces, captured when this module is imported --
#: before any sandbox exists -- so stata_restored() can prove restore().
_ORIGINAL = {"run": subprocess.run, "Popen": subprocess.Popen,
             "system": os.system, "executable": sys.executable,
             "addsitedir": site.addsitedir,
             "getusersitepackages": site.getusersitepackages}
