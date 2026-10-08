"""dep_block -- make numpy, pandas, bokeh or sfi look missing, broken or old
inside the Python Stata runs, and put everything back (WP-30 P1.32).

test_env_guards.cscript (ENV-30..39) and test_setup_honesty.cscript
(HON-40..42) drive dash's dependency guard through these functions, from
uncaptured ``python:`` lines.  Each change is kept: ``restore()`` (or
``stata_restored()``, which sets the Stata local ``rg_clean`` to "1" when
every kept object is back by identity) undoes all of them, and every case
calls it before it asserts.

What it changes: entries of ``sys.modules``, a finder at the front of
``sys.meta_path``, ``sys.version_info``, a package's ``__version__`` and
``os.environ["PYTHONPATH"]``.  It starts no process and writes only into
its own ``tempfile.mkdtemp()`` folder (a stub ``pandas.py``) and, through
``plant_run``, one run folder in dash's own private root.  Standard library
only.
"""
import importlib.abc
import importlib.util
import os
import shutil
import sys
import tempfile
import types

_MISSING = object()

_KEPT = {}       # sys.modules name -> the object taken out (or _MISSING)
_BLOCKED = []    # names blocked, so a submodule imported later goes too
_FINDERS = []    # finders put on sys.meta_path
_ENV = {}        # environment variable -> kept value (or _MISSING)
_DIRS = []       # folders this module made
_HITS = [0]      # sfi_flaky's counted lookups
_ATTRS = []      # (object, attribute, kept value)


def _keep_module(name):
    if name not in _KEPT:
        _KEPT[name] = sys.modules.get(name, _MISSING)


def forget_renderer():
    """Take dash's cached renderer out of sys.modules, kept for restore()."""
    _keep_module("_dash_render_export")
    sys.modules.pop("_dash_render_export", None)


class _BrokenLoader(importlib.abc.Loader):
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        raise ImportError("dash test: %s is installed but cannot be imported"
                          % module.__name__)


class _BrokenFinder(importlib.abc.MetaPathFinder):
    def __init__(self, name):
        self.name = name

    def find_spec(self, fullname, path=None, target=None):
        if fullname == self.name or fullname.startswith(self.name + "."):
            return importlib.util.spec_from_loader(fullname, _BrokenLoader())
        return None


def block(name, how):
    """Make ``name`` missing (``sys.modules[name] = None``) or broken (found,
    but its import raises ImportError).  ``name`` and its submodules, and
    the cached renderer, are taken out first and kept."""
    if how not in ("missing", "broken"):
        raise ValueError(how)
    for key in [k for k in list(sys.modules)
                if k == name or k.startswith(name + ".")]:
        _keep_module(key)
        del sys.modules[key]
    _keep_module(name)
    forget_renderer()
    _BLOCKED.append(name)
    if how == "missing":
        sys.modules[name] = None
    else:
        finder = _BrokenFinder(name)
        sys.meta_path.insert(0, finder)
        _FINDERS.append(finder)


def stata_block(local_name, how):
    """block() of the package named in the Stata local ``local_name``."""
    from sfi import Macro
    block(Macro.getLocal(local_name), how)


def fake_version(info):
    """Replace sys.version_info by a named tuple of the five fields."""
    import collections
    vi = collections.namedtuple(
        "version_info", "major minor micro releaselevel serial")(*info)
    _ATTRS.append((sys, "version_info", sys.version_info))
    sys.version_info = vi


def fake_package_version(name, text):
    """Replace sys.modules[name].__version__ by ``text``."""
    mod = sys.modules.get(name)
    if mod is None:
        mod = importlib.import_module(name)
    _ATTRS.append((mod, "__version__", getattr(mod, "__version__", _MISSING)))
    mod.__version__ = text


def sfi_flaky():
    """The next ``from sfi import ...`` fails once: the stand-in counts the
    lookup, puts the real sfi back and raises AttributeError."""
    real = sys.modules["sfi"]
    _keep_module("sfi")
    _HITS[0] = 0
    flaky = types.ModuleType("sfi")

    def _getattr(attr):
        if attr.startswith("__"):
            raise AttributeError(attr)
        _HITS[0] += 1
        sys.modules["sfi"] = real
        raise AttributeError("dash test: sfi is not ready (%s)" % attr)

    flaky.__getattr__ = _getattr
    sys.modules["sfi"] = flaky


def stata_hits():
    """Set the Stata local ``rg_hits`` to sfi_flaky's counted lookups,
    through the real sfi sfi_flaky kept (a stand-in nothing has looked up
    yet must not count this lookup)."""
    n = _HITS[0]
    real = _KEPT.get("sfi")
    if not isinstance(real, types.ModuleType):
        real = sys.modules["sfi"]
    real.Macro.setLocal("rg_hits", str(n))


def plant_run(tmpdir):
    """A run folder of this process in dash's own root, when that root
    exists; returns its path or ""."""
    root = os.path.join(tmpdir, "dash-%d" % os.getuid())
    if not os.path.isdir(root):
        return ""
    path = os.path.join(root, "run-%d-rg37" % os.getpid())
    os.mkdir(path, 0o700)
    return path


def stata_plant_run():
    """plant_run() of the Stata local ``tmp``; sets the local ``rg_run``."""
    from sfi import Macro
    Macro.setLocal("rg_run", plant_run(Macro.getLocal("tmp")))


def child_stub():
    """A folder holding a ``pandas.py`` that raises ModuleNotFoundError, put
    first on PYTHONPATH, so a child Python dash starts lacks pandas."""
    d = tempfile.mkdtemp(prefix="dash_rg_")
    _DIRS.append(d)
    with open(os.path.join(d, "pandas.py"), "w") as fh:
        fh.write('raise ModuleNotFoundError("No module named \'pandas\' '
                 '(dash test stub)", name="pandas")\n')
    if "PYTHONPATH" not in _ENV:
        _ENV["PYTHONPATH"] = os.environ.get("PYTHONPATH", _MISSING)
    os.environ["PYTHONPATH"] = d
    return d


def restore():
    """Undo every change; True when every kept object is back by identity."""
    for finder in _FINDERS:
        while finder in sys.meta_path:
            sys.meta_path.remove(finder)
    for name in _BLOCKED:
        for key in [k for k in list(sys.modules)
                    if k == name or k.startswith(name + ".")]:
            if key not in _KEPT:
                del sys.modules[key]
    for name, obj in _KEPT.items():
        if obj is _MISSING:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = obj
    for obj, attr, kept in reversed(_ATTRS):
        if kept is _MISSING:
            try:
                delattr(obj, attr)
            except AttributeError:
                pass
        else:
            setattr(obj, attr, kept)
    for var, kept in _ENV.items():
        if kept is _MISSING:
            os.environ.pop(var, None)
        else:
            os.environ[var] = kept
    for d in _DIRS:
        shutil.rmtree(d, ignore_errors=True)
    ok = all((sys.modules.get(n, _MISSING) is o) for n, o in _KEPT.items())
    ok = ok and all(getattr(o, a, _MISSING) is k for o, a, k in _ATTRS)
    ok = ok and not any(f in sys.meta_path for f in _FINDERS)
    _KEPT.clear()
    del _BLOCKED[:]
    del _FINDERS[:]
    _ENV.clear()
    del _DIRS[:]
    del _ATTRS[:]
    return ok


def stata_restored():
    """restore(); set the Stata local ``rg_clean`` to "1" or ""."""
    ok = restore()
    from sfi import Macro
    Macro.setLocal("rg_clean", "1" if ok else "")
