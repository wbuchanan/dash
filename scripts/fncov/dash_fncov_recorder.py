"""Record which functions of dash_render.py -- and of the Bokeh server apps
it generates -- a process executes.  Standard library only.

This is the recorder behind ``scripts/fncov/run_fncov.sh`` (read that file
first).  It is not a line-coverage tool: it answers one question, "was this
function ever called?", for WP-24's AC-24.3 ("every function has a
behavioural test"), and it answers it for every process the test suite
starts:

* the pytest process and each pytest-xdist worker, through the plugin
  ``dash_fncov_plugin.py`` (loaded with ``-p dash_fncov_plugin``);
* every Python subprocess a test launches (``python dash_render.py ...``,
  ``python app.py``, ``bokeh serve app.py``, ``python -c ...``), through
  ``site/usercustomize.py``, which Python imports at start-up from
  ``PYTHONPATH`` -- the runner puts ``site/`` there, and the plugin does too.

How: ``sys.monitoring`` (PEP 669, Python 3.12+) with one PY_START callback.
The callback returns ``DISABLE`` for every code object it sees, so each code
object costs one call per process and nothing after -- the suite runs at
close to its normal speed.  (``sys.setprofile``/``threading.setprofile`` is
the fallback on an older interpreter; it is correct and much slower.)

What is written: one JSON-lines file per process in ``DASH_FNCOV_DIR``,
named ``fncov-<pid>-<random>.jsonl``.  The first line is a header
``{"pid": ..., "argv": [...], "python": "3.14.5"}``; every other line is

    [kind, file, co_qualname, co_firstlineno]

where *file* is a number standing for a ``co_filename`` that an earlier
line ``["F", number, co_filename]`` of the same file defines (paths repeat
on every record, and a per-test run writes millions), and *kind* is

* ``"R"``  a code object compiled from a file named ``dash_render.py``;
* ``"A"``  one compiled from a real file whose first bytes carry the
  generated app's banner (``_APP_BANNER``);
* ``"M"``  one compiled from a name that is not a readable file
  (``"<test>"``, ``"app.py"`` in another directory, ...).  Some tests
  ``exec(compile(app_source, "<test>", "exec"))``; whether a given name was
  an app is decided afterwards, by ``fncov_report.py``, from the functions
  recorded under it (an app defines ``_dash_build_scheme``);
* ``"CR"``, ``"CA"``, ``"CM"``  (only with ``DASH_FNCOV_CALLERS=1``) the
  same function called, at least once, by something that is not a module
  of the repository's ``test/`` directory: dash's own code, the app, or a
  library calling back.  A function with no such record is one that only
  the tests call directly.

Each line is written with one ``os.write`` on an ``O_APPEND`` descriptor the
moment the function is first called, so a subprocess a test kills
(``bokeh serve`` is stopped with SIGTERM) loses nothing it had recorded.

Per-test attribution (``DASH_FNCOV_PER_TEST=1``): the plugin calls
``set_test(nodeid)`` as each test starts, which re-arms every event, and each
record then carries a fifth field, the test -- a number that an earlier
``["T", number, nodeid]`` line defines -- so a code object is recorded once
per TEST instead of once per process.  A subprocess started during a test
inherits ``DASH_FNCOV_TEST`` and tags its records with it.  This is how
``test/function_test_map.py`` was first filled in (``fncov_report.py
--suggest-map``).
"""
import json
import os
import sys

#: The generated app's banner, the second line of every app
#: ``ServerAppBuilder._generate_app_source`` writes.
_APP_BANNER = b"# Auto-generated Bokeh Server dashboard"

_STATE = {"fd": None, "pid": None, "files": {}, "tool": None,
          "test": None, "fids": {}, "tids": {}}


def _library_prefixes():
    """Directories whose files are never dash's: the interpreter's own."""
    out = set()
    for p in (getattr(sys, "prefix", ""), getattr(sys, "base_prefix", ""),
              getattr(sys, "exec_prefix", ""),
              getattr(sys, "base_exec_prefix", "")):
        if p:
            out.add(os.path.realpath(p) + os.sep)
            out.add(p.rstrip(os.sep) + os.sep)
    for p in sys.path:
        if p and ("site-packages" in p or "dist-packages" in p):
            out.add(p.rstrip(os.sep) + os.sep)
    return tuple(sorted(out))


_LIB = _library_prefixes()


def classify(filename):
    """Return "R", "A", "M" or None for a code object's ``co_filename``."""
    if not filename:
        return None
    if os.path.basename(filename) == "dash_render.py":
        return "R"
    if filename.startswith("<frozen") or filename.startswith(_LIB):
        return None
    if filename.startswith("<"):
        return "M"
    try:
        with open(filename, "rb") as fh:
            head = fh.read(512)
    except OSError:
        return "M"
    return "A" if _APP_BANNER in head else None


def _intern(table, tag, value, out):
    """The number standing for *value*, defining it in *out* the first
    time this file sees it."""
    n = table.get(value)
    if n is None:
        n = table[value] = len(table)
        out.append(json.dumps([tag, n, value]))
    return n


def _emit(kind, code):
    fd = _STATE["fd"]
    if fd is None:
        return
    if _STATE["pid"] != os.getpid():
        # A child forked without exec: its own file, its own numbers.
        _STATE["fd"] = None
        start(_STATE["outdir"])
        fd = _STATE["fd"]
    lines = []
    rec = [kind, _intern(_STATE["fids"], "F", code.co_filename, lines),
           getattr(code, "co_qualname", code.co_name), code.co_firstlineno]
    if _STATE["test"] is not None:
        rec.append(_intern(_STATE["tids"], "T", _STATE["test"], lines))
    lines.append(json.dumps(rec))
    try:
        os.write(fd, ("\n".join(lines) + "\n").encode("utf-8"))
    except OSError:
        pass


def _kind(code):
    """*code*'s file classified, once per file."""
    files = _STATE["files"]
    fn = code.co_filename
    kind = files.get(fn, 0)
    if kind == 0:
        kind = classify(fn)
        files[fn] = kind
    return kind


def _seen(code):
    """Record *code* if its file is wanted (the setprofile fallback)."""
    kind = _kind(code)
    if kind is not None:
        _emit(kind, code)


def is_test_file(filename):
    """A module of the repository's test/ directory (a test, conftest.py,
    or a helper the tests import) -- not the standard library's test/."""
    return (filename.endswith(".py") and not filename.startswith(_LIB)
            and os.path.basename(os.path.dirname(filename)) == "test")


def _open(outdir):
    os.makedirs(outdir, exist_ok=True)
    name = "fncov-%d-%s.jsonl" % (os.getpid(), os.urandom(4).hex())
    fd = os.open(os.path.join(outdir, name),
                 os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    head = {"pid": os.getpid(), "argv": [str(a)[:200] for a in sys.argv[:8]],
            "python": sys.version.split()[0]}
    os.write(fd, (json.dumps(head) + "\n").encode("utf-8"))
    return fd


def set_test(nodeid):
    """Attribute what runs from now on to *nodeid* (None: to no test).

    Re-arms every PY_START event, so each function the test calls is
    recorded for it even if an earlier test already called it.
    """
    _STATE["test"] = nodeid
    mon = getattr(sys, "monitoring", None)
    if nodeid is not None and mon is not None and isinstance(
            _STATE["tool"], int):
        _STATE["watch"] = set()
        mon.restart_events()


def start(outdir=None):
    """Start recording in this process.  Idempotent; returns True if on."""
    outdir = outdir or os.environ.get("DASH_FNCOV_DIR")
    if not outdir:
        return False
    if _STATE["fd"] is not None and _STATE["pid"] == os.getpid():
        return True
    _STATE["fd"] = _open(outdir)
    _STATE["pid"] = os.getpid()
    _STATE["outdir"] = outdir
    # Numbers are defined per file: a forked child starts its own.
    _STATE["fids"], _STATE["tids"] = {}, {}
    # A subprocess a test started records for that test.
    if os.environ.get("DASH_FNCOV_TEST"):
        _STATE["test"] = os.environ["DASH_FNCOV_TEST"]
    if _STATE["tool"] is not None:          # a forked child: same hooks
        return True
    mon = getattr(sys, "monitoring", None)
    if mon is not None:
        disable = mon.DISABLE
        # DASH_FNCOV_CALLERS=1: also record, as kind "C" + kind, the first
        # call of each function from code that is NOT a test module --
        # dash's own code, the generated app, or a library calling back
        # (bokeh on a widget change, re.sub, Tornado).  A function recorded
        # but never so is one only the tests call directly.  A function a
        # test calls stays armed until a caller that is not a test appears;
        # only those are remembered, by name, so no generated app's code
        # objects are kept alive.
        callers = os.environ.get("DASH_FNCOV_CALLERS") == "1"
        _STATE["watch"] = set()
        getframe = sys._getframe

        def _on_start(code, _offset):
            try:
                # A module body, lambda or comprehension is not a def.
                if code.co_name[:1] == "<":
                    return disable
                kind = _kind(code)
                if kind is None:
                    return disable
                if not callers:
                    _emit(kind, code)
                    return disable
                # Frame 1 is the function starting; frame 2 its caller.
                try:
                    caller = getframe(2).f_code.co_filename
                except ValueError:
                    caller = ""
                key = (code.co_filename, code.co_firstlineno,
                       getattr(code, "co_qualname", code.co_name))
                watch = _STATE["watch"]
                if is_test_file(caller):
                    if key not in watch:
                        watch.add(key)
                        _emit(kind, code)
                    return None           # keep watching this one
                if key not in watch:
                    _emit(kind, code)
                _emit("C" + kind, code)   # a caller that is not a test
                return disable
            except Exception:
                return disable

        for tool in (mon.COVERAGE_ID, 3, 4, mon.PROFILER_ID):
            try:
                mon.use_tool_id(tool, "dash-fncov")
            except ValueError:
                continue                      # that id is taken
            mon.register_callback(tool, mon.events.PY_START, _on_start)
            mon.set_events(tool, mon.events.PY_START)
            _STATE["tool"] = tool
            return True
    # Fallback: a profile hook on every thread, one record per code object.
    import threading
    done = set()

    def _prof(frame, event, _arg):
        if event == "call":
            code = frame.f_code
            if code not in done:
                done.add(code)
                try:
                    _seen(code)
                except Exception:
                    pass

    sys.setprofile(_prof)
    threading.setprofile(_prof)
    _STATE["tool"] = "setprofile"
    return True
