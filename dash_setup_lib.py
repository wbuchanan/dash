"""dash_setup_lib -- the mechanics of dash_setup's pip and venv steps (WP-29 P0.19),
and dash clear's pruning without the packages (WP-30 P1.32).
dash_setup.ado decides and counts; this module runs children and formats commands.
Stdlib only; parses as Python 3.8; nothing runs at import.

Every child process dash_setup starts goes through run_child: the interpreter
Stata is linked to (c(python_exec), resolved; never sys.executable), argv
lists only, from a fresh private directory, without an inherited PYTHONPATH,
with PEP 668's protection forced on, output decoded as UTF-8, and a time
limit.  The linked Python is inspected in a child (DETECT_CODE), because the
in-process view under Stata cannot see what a venv's own interpreter has.
Environment-derived text is printed with print(), which Stata shows as plain
text, never through SMCL.
"""
import ast
import importlib
import json
import ntpath
import os
import re
import shlex
import shutil
import site
import stat
import subprocess
import sys
import tempfile

TIMEOUT = 1800

#: A requirement dash_setup will hand pip: a name and an optional minimum
#: and ceiling (P1.30's `bokeh>=3.8,<4' is admitted now).
_SPEC_RE = re.compile(r"^[A-Za-z0-9._-]+(>=[0-9][0-9.]*)?(,<[0-9][0-9.]*)?$")

#: Variables a child must not inherit: an inherited PYTHONPATH (the user's,
#: or the one Stata exports under a venv link) must not decide what pip or
#: venv imports.
_ENV_DROP = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT",
             "PYTHONEXECUTABLE", "__PYVENV_LAUNCHER__")

#: Set in every child: UTF-8 output, no bytecode written, PEP 668's check on
#: whatever a pip config file says, and no --user from a config file.
_ENV_SET = {"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1",
            "PIP_BREAK_SYSTEM_PACKAGES": "0", "PIP_USER": "0"}

#: The venv() path stata_venv_check validated, held for the stata_venv call
#: that follows it, so the path never passes through Stata's parser again.
_PENDING = {}

#: stdlib_entry's compiled slices, keyed by the file's realpath, size, time
#: and the entry's name, so a file is compiled once per version.
_SLICES = {}

_PIP_FIXED = ["--disable-pip-version-check", "--no-input", "--only-binary=:all:"]

#: Run as [exe, "-c", DETECT_CODE], without -P (3.9 refuses it).  Python 3.4
#: syntax.  Prints one JSON line.
DETECT_CODE = (
    "import json, os, site, sys, sysconfig\n"
    "def _has(name):\n"
    "    try:\n"
    "        import importlib.util\n"
    "        return importlib.util.find_spec(name) is not None\n"
    "    except Exception:\n"
    "        return False\n"
    "_p = sys.prefix\n"
    "_s = sysconfig.get_path('stdlib') or ''\n"
    "try:\n"
    "    _us = site.getusersitepackages()\n"
    "except Exception:\n"
    "    _us = ''\n"
    "print(json.dumps({'tag': 'DASH_DETECT_V1', 'prefix': _p,\n"
    "    'base_prefix': getattr(sys, 'base_prefix', _p), 'stdlib': _s,\n"
    "    'marker': os.path.isfile(os.path.join(_s, 'EXTERNALLY-MANAGED')),\n"
    "    'pyvenv_cfg': os.path.isfile(os.path.join(_p, 'pyvenv.cfg')),\n"
    "    'pip': _has('pip'), 'ensurepip': _has('ensurepip'), 'venv': _has('venv'),\n"
    "    'user_site_enabled': bool(site.ENABLE_USER_SITE), 'user_site': _us or '',\n"
    "    'version': list(sys.version_info[:3]), 'executable': sys.executable or ''}))\n"
)

#: Run as [exe, *safe_flags, "-c", VERIFY_CODE, <minimums JSON>, <dash_render.py>].
#: Prints one JSON line.
VERIFY_CODE = (
    "import json, sys, warnings\n"
    "_mins = json.loads(sys.argv[1])\n"
    "_render = sys.argv[2]\n"
    "def _t(s):\n"
    "    return tuple(int(x) for x in str(s).split('.') if x.isdigit())\n"
    "_out = {'tag': 'DASH_VERIFY_V1', 'ok': False, 'version': list(sys.version_info[:3]),\n"
    "        'packages': {}, 'schemes': False, 'why': ''}\n"
    "if tuple(sys.version_info[:3]) < _t(_mins.get('python', '0')):\n"
    "    _out['why'] = 'python'\n"
    "else:\n"
    "    import importlib\n"
    "    try:\n"
    "        import importlib.metadata as _md\n"
    "        from packaging.version import Version as _V\n"
    "    except Exception:\n"
    "        _V = None\n"
    "    _bad = []\n"
    "    for _n in ('packaging', 'bokeh', 'numpy', 'pandas'):\n"
    "        _v = ''\n"
    "        try:\n"
    "            importlib.import_module(_n)\n"
    "            _v = _md.version(_n)\n"
    "        except Exception:\n"
    "            _v = ''\n"
    "        _out['packages'][_n] = _v\n"
    "        _need = _mins.get(_n, '')\n"
    "        if not _v or _V is None:\n"
    "            _bad.append(_n)\n"
    "        elif _need:\n"
    "            try:\n"
    "                if _V(_v) < _V(_need):\n"
    "                    _bad.append(_n)\n"
    "            except Exception:\n"
    "                _bad.append(_n)\n"
    "    try:\n"
    "        import importlib.util\n"
    "        _sp = importlib.util.spec_from_file_location('_dash_verify_render', _render)\n"
    "        _mod = importlib.util.module_from_spec(_sp)\n"
    "        with warnings.catch_warnings():\n"
    "            warnings.simplefilter('ignore')\n"
    "            _sp.loader.exec_module(_mod)\n"
    "            _out['schemes'] = not _mod.SchemeParser.resolve_or_fallback(\n"
    "                's2color', 'dash_setup').is_fallback\n"
    "    except Exception:\n"
    "        _out['schemes'] = False\n"
    "    _out['above'] = []\n"
    "    _c = _mins.get('bokeh_ceil', '')\n"
    "    if _c and _out['packages'].get('bokeh') and \\\n"
    "            _t(_out['packages']['bokeh'])[:2] >= _t(_c)[:2]:\n"
    "        _out['above'].append('bokeh')\n"
    "    if _bad:\n"
    "        _out['why'] = 'packages: ' + ', '.join(_bad)\n"
    "    elif not _out['schemes']:\n"
    "        _out['why'] = 'schemes'\n"
    "    _out['ok'] = not _bad and bool(_out['schemes'])\n"
    "print(json.dumps(_out))\n"
)


class VenvPathError(ValueError):
    """A venv() path dash_setup refuses; .path is the path as resolved."""

    def __init__(self, message, path=""):
        ValueError.__init__(self, message)
        self.path = path


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def resolve_exe(exe, cwd, which=shutil.which):
    """The linked interpreter as an absolute path, or None.  A relative
    c(python_exec) is relative to Stata's working directory.  Symlinks are
    never resolved: a venv's bin/python is a symlink to its base."""
    if not exe:
        return None
    if os.path.isabs(exe):
        return exe
    if os.sep not in exe and not (os.altsep and os.altsep in exe):
        return which(exe)
    path = os.path.abspath(os.path.join(cwd, exe))
    return path if os.path.isfile(path) else None


def version_tuple(text):
    """'3.13.9' -> (3, 13, 9); the first word only; () when unreadable."""
    words = str(text or "").split()
    if not words:
        return ()
    m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", words[0])
    if not m:
        return ()
    return tuple(int(g) for g in m.groups() if g is not None)


def safe_flags(version):
    """["-P"] (safe path) where the interpreter knows it, 3.11 and later."""
    v = tuple(version[:2]) if version else ()
    return ["-P"] if v and v >= (3, 11) else []


def child_env(environ):
    """A copy of environ minus _ENV_DROP, with _ENV_SET.  PIP_* (an index,
    a proxy, PIP_NO_INDEX), PYTHONUSERBASE, PATH and the rest are kept."""
    env = dict(environ)
    for k in _ENV_DROP:
        env.pop(k, None)
    env.update(_ENV_SET)
    return env


def run_child(argv, timeout=TIMEOUT, runtime=None):
    """(rc, out, err) of one child; never raises.  rc -1: it could not be
    started; rc -2: it did not finish within `timeout' seconds."""
    work = tempfile.mkdtemp(prefix="dash_setup_")
    try:
        kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE, cwd=work, env=child_env(os.environ),
                  shell=False, encoding="utf-8", errors="replace",
                  timeout=timeout)
        runtime = sys.version_info if runtime is None else runtime
        if os.name == "posix" and tuple(runtime[:2]) >= (3, 9):
            kw["umask"] = 0o022
        try:
            r = subprocess.run(list(argv), **kw)
        except subprocess.TimeoutExpired:
            return (-2, "", "dash_setup: the command did not finish within %s seconds" % timeout)
        except OSError as exc:
            return (-1, "", "dash_setup: could not start %s: %s" % (argv[0], exc.strerror or exc))
        return (r.returncode, r.stdout or "", r.stderr or "")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def interpret_detect(text):
    """DETECT_CODE's reply, read from its last non-empty line."""
    lines = [l for l in str(text or "").splitlines() if l.strip()]
    if not lines:
        return {"ok": False, "why": "no reply"}
    try:
        d = json.loads(lines[-1])
    except ValueError:
        return {"ok": False, "why": "a reply that is not JSON"}
    if not isinstance(d, dict) or d.get("tag") != "DASH_DETECT_V1":
        return {"ok": False, "why": "a reply without its tag"}
    for k in ("prefix", "base_prefix", "stdlib", "user_site", "executable"):
        if not isinstance(d.get(k), str):
            return {"ok": False, "why": "a reply whose %s is not text" % k}
    for k in ("marker", "pyvenv_cfg", "pip", "ensurepip", "venv", "user_site_enabled"):
        if not isinstance(d.get(k), bool):
            return {"ok": False, "why": "a reply whose %s is not true or false" % k}
    v = d.get("version")
    if not (isinstance(v, list) and len(v) == 3 and
            all(isinstance(x, int) and not isinstance(x, bool) for x in v)):
        return {"ok": False, "why": "a reply whose version is not three numbers"}
    in_venv = d["prefix"] != d["base_prefix"] or d["pyvenv_cfg"]
    return {"ok": True, "in_venv": in_venv,
            "externally_managed": (not in_venv) and d["marker"],
            "pip": d["pip"], "ensurepip": d["ensurepip"], "venv": d["venv"],
            "user_site_enabled": d["user_site_enabled"] and not in_venv,
            "user_site": d["user_site"], "version": tuple(v),
            "executable": d["executable"]}


def detect_environment(exe):
    """Inspect an interpreter in a child process."""
    rc, out, err = run_child([exe, "-c", DETECT_CODE])
    if rc != 0:
        return {"ok": False, "why": classify_failure(rc, err)}
    return interpret_detect(out)


def pip_install_argv(exe, specs, version, user=False):
    """The one pip vector dash_setup runs."""
    for spec in specs:
        if not isinstance(spec, str) or not _SPEC_RE.fullmatch(spec):
            raise ValueError("dash_setup: refusing the requirement %r" % (spec,))
    return ([exe] + safe_flags(version) + ["-m", "pip", "install"] + _PIP_FIXED +
            (["--user"] if user else []) + list(specs))


_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def pip_uninstall_argv(exe, names):
    """The pip line that removes what a failed dash_setup run installed
    (WP-31 I3): package names only, no flags."""
    for name in names:
        if not isinstance(name, str) or not _NAME_RE.fullmatch(name):
            raise ValueError("dash_setup: refusing the package name %r" % (name,))
    return [exe, "-m", "pip", "uninstall"] + list(names)


#: The hash-pinned lock dash_setup installs from (WP-32, I3), shipped
#: beside this file; written by scripts/make_requirements_lock.py, never by
#: hand.
LOCK_NAME = "dash_requirements.txt"

#: One lock entry, its continuation lines joined: a pinned name, an optional
#: environment marker, and one or more sha256 hashes.
_LOCK_ENTRY_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>[0-9][0-9A-Za-z.!+_-]*)"
    r"(?: ?; ?(?P<marker>[^\\]+?))?(?P<hashes>(?: --hash=sha256:[0-9a-f]{64})+)$")

#: A marker is these variables compared with quoted words, nothing else.
_LOCK_MARKER_RE = re.compile(
    r"^(?:[() ]|and|or|python_version|sys_platform|platform_machine|"
    r"==|!=|\"[A-Za-z0-9_.]+\")+$")

#: Run as [exe, "-c", INSTALLED_CODE]: every installed distribution, its
#: name normalised as pip compares it, and its version, as one JSON line.
INSTALLED_CODE = (
    "import json, re\n"
    "try:\n"
    "    import importlib.metadata as m\n"
    "    ds = list(m.distributions())\n"
    "except Exception:\n"
    "    ds = []\n"
    "out = {}\n"
    "for d in ds:\n"
    "    n = d.metadata['Name'] or ''\n"
    "    if n:\n"
    "        out[re.sub(r'[-_.]+', '-', n).lower()] = str(d.version)\n"
    "print(json.dumps({'tag': 'DASH_INSTALLED_V1', 'dists': out}))\n")


def normalize_name(name):
    """A distribution name as pip compares it (PEP 503)."""
    return re.sub(r"[-_.]+", "-", str(name)).lower()


def read_lock(text):
    """The entries of a lock file's text (WP-32, I3): a list of dicts with
    name (normalised), version, marker ("" when none), hashes and line (the
    entry as one requirement line pip reads).  Comments and blank lines are
    skipped; a line ending in a backslash continues on the next.

    Raises:
        ValueError: if an entry is not ``name==version [; marker]`` followed
            by sha256 hashes, a marker uses anything but python_version,
            sys_platform and platform_machine, or the file has no entry.
    """
    entries, cur = [], ""
    for raw in str(text).splitlines() + [""]:
        ln = raw.strip()
        if not cur and (not ln or ln.startswith("#")):
            continue
        cur = (cur + " " + ln).strip() if cur else ln
        if cur.endswith("\\"):
            cur = cur[:-1].rstrip()
            continue
        if not cur:
            continue
        m = _LOCK_ENTRY_RE.fullmatch(re.sub(r"\s+", " ", cur))
        if not m:
            raise ValueError("dash_setup: the lock entry %r is not a pinned, "
                             "hashed requirement" % cur[:80])
        marker = (m.group("marker") or "").strip()
        if marker and not _LOCK_MARKER_RE.fullmatch(marker):
            raise ValueError("dash_setup: the lock marker %r is not one "
                             "dash_setup reads" % marker[:80])
        hashes = m.group("hashes").split()
        entries.append({
            "name": normalize_name(m.group("name")),
            "version": m.group("version"), "marker": marker,
            "hashes": [h[len("--hash=sha256:"):] for h in hashes],
            "line": "%s==%s%s %s" % (m.group("name"), m.group("version"),
                                     " ; " + marker if marker else "",
                                     " ".join(hashes))})
        cur = ""
    if not entries:
        raise ValueError("dash_setup: the lock holds no requirement")
    return entries


def _spec_window(spec):
    """(name, minimum tuple, ceiling tuple or None) of a _SPEC_RE spec."""
    if not isinstance(spec, str) or not _SPEC_RE.fullmatch(spec):
        raise ValueError("dash_setup: refusing the requirement %r" % (spec,))
    m = re.match(r"^([A-Za-z0-9._-]+)(?:>=([0-9.]+))?(?:,<([0-9.]+))?$", spec)
    lo = version_tuple(m.group(2)) if m.group(2) else ()
    hi = version_tuple(m.group(3)) if m.group(3) else None
    return normalize_name(m.group(1)), lo, hi


def _in_window(version, lo, hi):
    v = version_tuple(version)
    return bool(v) and v >= lo and (hi is None or v < hi)


def lock_lines(entries, specs, installed):
    """The lock lines one install needs (WP-32, I3).

    For each requirement in *specs* (``bokeh>=3.8,<3.10``): its lock
    entries, unless the version in *installed* (``{normalised name:
    version}``) is already inside the requirement's window, and each locked
    version must be inside it.  Then every other entry whose package is not
    installed -- the dependencies -- so an installed package is never
    replaced: pip, with --require-hashes, refuses a dependency that is
    missing from the lines and not installed, and leaves one that is.

    Raises:
        ValueError: if a requirement has no entry, or a locked version is
            outside its window (the lock is older than dash_setup).
    """
    out, wanted = [], set()
    for spec in specs:
        name, lo, hi = _spec_window(spec)
        wanted.add(name)
        mine = [e for e in entries if e["name"] == name]
        if not mine:
            raise ValueError("dash_setup: %s has no %s; regenerate it with "
                             "scripts/make_requirements_lock.py" % (LOCK_NAME, name))
        for e in mine:
            if not _in_window(e["version"], lo, hi):
                raise ValueError("dash_setup: %s pins %s %s, outside %s; "
                                 "regenerate it with "
                                 "scripts/make_requirements_lock.py"
                                 % (LOCK_NAME, name, e["version"], spec))
        have = installed.get(name)
        if not (have and _in_window(have, lo, hi)):
            out += [e["line"] for e in mine]
    out += [e["line"] for e in entries
            if e["name"] not in wanted and e["name"] not in installed]
    return out


def lock_path():
    """The lock shipped beside this file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), LOCK_NAME)


def installed_dists(exe, version=()):
    """{normalised name: version} of what interpreter *exe* has installed,
    read in a child (INSTALLED_CODE), or None when it cannot be read."""
    rc, out, _err = run_child([exe] + safe_flags(version) + ["-c", INSTALLED_CODE])
    lines = [l for l in str(out or "").splitlines() if l.strip()]
    try:
        d = json.loads(lines[-1]) if (rc == 0 and lines) else None
    except ValueError:
        d = None
    if not isinstance(d, dict) or d.get("tag") != "DASH_INSTALLED_V1" or \
            not isinstance(d.get("dists"), dict):
        return None
    return {normalize_name(k): str(v) for k, v in d["dists"].items()}


def pip_lock_argv(exe, req_path, version, user=False):
    """The hash-checked pip vector (WP-32, I3): pip_install_argv's, with
    --require-hashes and ``-r`` the lines lock_lines chose."""
    return ([exe] + safe_flags(version) + ["-m", "pip", "install"] + _PIP_FIXED +
            ["--require-hashes"] + (["--user"] if user else []) +
            ["-r", str(req_path)])


def lock_install(exe, specs, version, user=False, lock=None, run=None):
    """Install *specs* into *exe* from the hash-pinned lock (WP-32, I3).

    Reads the lock (*lock*, else :func:`lock_path`), what *exe* has
    installed (:func:`installed_dists`), and runs :func:`pip_lock_argv`
    over the lines :func:`lock_lines` chose, written 0600 to a private
    folder removed afterwards.  Nothing is installed by version range.

    Returns:
        (rc, out, err) as run_child gives them; (0, ..., "") without running
        pip when everything is installed; (1, "", reason) when the lock is
        missing or malformed or the installed packages cannot be read.
    """
    run = run_child if run is None else run
    path = lock_path() if lock is None else lock
    try:
        with open(path, encoding="utf-8") as fh:
            entries = read_lock(fh.read())
    except OSError as exc:
        return (1, "", "dash_setup: cannot read %s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        return (1, "", str(exc))
    installed = installed_dists(exe, version)
    if installed is None:
        return (1, "", "dash_setup: could not list the packages %s has installed"
                % exe)
    try:
        lines = lock_lines(entries, specs, installed)
    except ValueError as exc:
        return (1, "", str(exc))
    if not lines:
        return (0, "  already installed: " + " ".join(specs), "")
    work = tempfile.mkdtemp(prefix="dash_setup_req_")
    try:
        req = os.path.join(work, "requirements.txt")
        fd = os.open(req, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        return run(pip_lock_argv(exe, req, version, user=user))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def bokeh_requirement(installed, floor, ceil):
    """The bokeh requirement dash_setup installs (WP-30 P1.30, M9, A107).

    ``bokeh>=<floor>,<<ceil>`` -- the verified window -- unless the bokeh
    already installed is at or above the ceiling, when it is
    ``bokeh>=<floor>``: a bokeh someone installed is never downgraded
    (critic C5: a reused venv with bokeh 3.10).  ``floor`` and ``ceil``
    are dash's own literals and must be dotted numbers.

    Raises:
        ValueError: if floor or ceil is not a dotted number.
    """
    for v in (floor, ceil):
        if not isinstance(v, str) or not re.fullmatch(r"[0-9]+(\.[0-9]+)*", v):
            raise ValueError("dash_setup: refusing the bokeh bound %r" % (v,))
    m = re.match(r"(\d+)\.(\d+)", str(installed or "")[:40])
    if m and (int(m.group(1)), int(m.group(2))) >= version_tuple(ceil)[:2]:
        return "bokeh>=" + floor
    return "bokeh>=%s,<%s" % (floor, ceil)


def classify_failure(rc, err):
    """What a child's exit status and stderr mean (the measured texts)."""
    err = err or ""
    if rc == 0:
        return "ok"
    if rc == -2:
        return "timeout"
    if rc == -1:
        return "missing-interpreter"
    if "externally-managed-environment" in err:
        return "externally-managed"
    if "No module named pip" in err:
        return "no-pip"
    if "Can not perform a '--user' install" in err:
        return "user-unavailable"
    if "ensurepip" in err and ("not available" in err or "No module named ensurepip" in err):
        return "no-ensurepip"
    return "other"


def shell_line(argv, windows):
    """A command line that runs as printed: POSIX shells, or cmd.exe."""
    if not windows:
        return shlex.join([str(a) for a in argv])
    out = []
    for i, a in enumerate(argv):
        a = str(a)
        if '"' in a or "%" in a:
            raise ValueError("dash_setup: %r cannot be quoted for cmd.exe" % a)
        if i == 0 or a == "" or any(c in a for c in " \t&|<>^()!,;="):
            out.append('"%s"' % a)
        else:
            out.append(a)
    return " ".join(out)


def add_user_site():
    """Put a user site made after start-up on sys.path (a --user install
    is then importable in the same run).  True when it was added."""
    if not site.ENABLE_USER_SITE:
        return False
    us = site.getusersitepackages()
    if not us or not os.path.isdir(us) or us in sys.path:
        return False
    site.addsitedir(us)
    importlib.invalidate_caches()
    return True


def default_venv_path(windows, environ):
    """The venv() path dash_setup suggests."""
    if not windows:
        return "~/.dash/venv"
    base = environ.get("LOCALAPPDATA") or ntpath.join(os.path.expanduser("~"), "AppData", "Local")
    return ntpath.join(base, "dash", "venv")


def validate_venv_path(raw, cwd, windows=None, getuid=None, home=None):
    """(abs_path, state, create) for a venv() path, or VenvPathError.
    state: "new", "empty" or "venv"; create: the missing ancestors inside
    the home directory, outermost first."""
    windows = (os.name == "nt") if windows is None else windows
    raw = "" if raw is None else str(raw)
    if not raw.strip():
        raise VenvPathError("venv() names no directory", raw)
    if any(ord(c) < 0x20 or c in '\x7f"`$' for c in raw):
        raise VenvPathError("holds a character dash_setup will not put in a command", raw)
    home = os.path.expanduser("~") if home is None else home
    path = raw
    if path == "~" or path.startswith("~" + os.sep) or (os.altsep and path.startswith("~" + os.altsep)):
        path = home + path[1:]
    elif path.startswith("~"):
        path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    head, name = os.path.split(path.rstrip(os.sep) or os.sep)
    if name in ("", ".", ".."):
        raise VenvPathError("names no directory of its own", path)
    parent = os.path.realpath(head)
    final = os.path.join(parent, name)
    uid = (getuid or getattr(os, "getuid", lambda: -1))()
    try:
        st = os.lstat(final)
    except FileNotFoundError:
        st = None
    state = "new"
    if st is not None:
        if stat.S_ISLNK(st.st_mode):
            raise VenvPathError("is a symbolic link", final)
        if not stat.S_ISDIR(st.st_mode):
            raise VenvPathError("exists and is not a directory", final)
        if os.path.isfile(os.path.join(final, "pyvenv.cfg")):
            state = "venv"
        elif not os.listdir(final):
            state = "empty"
        else:
            raise VenvPathError("is not empty and is not a virtual environment", final)
    create = []
    if st is not None:
        if not windows:
            checks = [st]
            if state == "venv" and os.path.isdir(os.path.join(final, "bin")):
                checks.append(os.stat(os.path.join(final, "bin")))
            for s in checks:
                if s.st_uid != uid:
                    raise VenvPathError("is not owned by you", final)
                if s.st_mode & 0o022:
                    raise VenvPathError("can be written by other users", final)
        return final, state, create
    anc = parent
    while not os.path.exists(anc):
        create.insert(0, anc)
        up = os.path.dirname(anc)
        if up == anc:
            break
        anc = up
    if create:
        rhome = os.path.realpath(home)
        for m in create:
            if not m.startswith(rhome.rstrip(os.sep) + os.sep):
                raise VenvPathError("its parent directory does not exist", final)
    if not windows:
        ps = os.stat(anc)
        if ps.st_uid not in (uid, 0):
            raise VenvPathError("its parent directory is not owned by you", final)
        if ps.st_mode & 0o022 and not ps.st_mode & stat.S_ISVTX:
            raise VenvPathError("its parent directory can be written by other users and is not sticky", final)
    return final, state, create


def venv_python(path, windows):
    """A venv's interpreter."""
    if windows:
        return ntpath.join(path, "Scripts", "python.exe")
    return os.path.join(path, "bin", "python")


def create_venv(base_exe, path, state, create, version):
    """Create the venv validate_venv_path checked: (ok, why)."""
    try:
        for a in create:
            os.mkdir(a, 0o700)
        if state == "new":
            os.mkdir(path, 0o755)
            os.chmod(path, 0o755)
    except FileExistsError:
        return False, "%s appeared after it was checked; run dash_setup again" % path
    if state == "venv":
        return True, ""
    rc, out, err = run_child([base_exe] + safe_flags(version) + ["-m", "venv", path])
    if rc != 0:
        kind = classify_failure(rc, err)
        if kind == "no-ensurepip":
            return False, ("the venv module cannot make an environment with pip here: "
                           "install python3-venv with your system's package manager")
        tail = (err.strip().splitlines() or [""])[-1]
        return False, "the venv module failed (%s): %s" % (kind, tail)
    if not (os.path.isfile(os.path.join(path, "pyvenv.cfg")) and
            os.path.exists(venv_python(path, os.name == "nt"))):
        return False, "the venv module ran but left no environment at %s" % path
    return True, ""


def verify_in(exe, render_py, minimums, version):
    """Run VERIFY_CODE in an interpreter: its JSON reply, or
    {"ok": False, "why": "malformed"}."""
    rc, out, err = run_child([exe] + safe_flags(version) +
                             ["-c", VERIFY_CODE, json.dumps(minimums), render_py])
    lines = [l for l in str(out or "").splitlines() if l.strip()]
    try:
        d = json.loads(lines[-1]) if lines else None
    except ValueError:
        d = None
    if not isinstance(d, dict) or d.get("tag") != "DASH_VERIFY_V1":
        return {"ok": False, "why": "malformed"}
    return d



def stdlib_entry(path, entry):
    """dash_render.py's top-level function ``entry`` compiled with the
    standard library alone, or None (WP-30 P1.32, register P1.32.3).

    dash clear prunes dash's temporary files through the renderer's own
    _dash_tmp_clear; this compiles that function and every top-level
    definition it reaches, with the file's top-level imports outside a
    `try', so the same code and checks run with numpy, pandas or bokeh
    missing.  A name bound by an import inside a top-level `try' (the
    guarded package imports) is foreign: a closure reaching one is refused
    (None), never imported.  Line numbers stay the file's.  Only dash's own
    shipped file is compiled; ``entry`` is a constant in dash.ado.  Never
    raises.
    """
    try:
        st = os.stat(path)
        key = (os.path.realpath(path), st.st_size, st.st_mtime_ns, entry)
        if key in _SLICES:
            return _SLICES[key]
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8")
        tree = ast.parse(text, filename=path)
        imports = []
        defs = {}
        foreign = set()
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                defs.setdefault(node.name, []).append(node)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for tgt in targets:
                    for sub in ast.walk(tgt):
                        if isinstance(sub, ast.Name):
                            defs.setdefault(sub.id, []).append(node)
            elif isinstance(node, ast.Try):
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.Import, ast.ImportFrom)):
                        for alias in sub.names:
                            foreign.add((alias.asname or alias.name).split(".")[0])
        if not any(isinstance(n, ast.FunctionDef) for n in defs.get(entry, [])):
            return None
        keep = {}
        todo = [entry]
        seen = set()
        while todo:
            name = todo.pop()
            if name in seen:
                continue
            seen.add(name)
            for node in defs[name]:
                keep[id(node)] = node
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Name):
                        if sub.id in foreign:
                            return None
                        if sub.id in defs and sub.id not in seen:
                            todo.append(sub.id)
        body = imports + [n for n in tree.body if id(n) in keep]
        module = ast.Module(body=body, type_ignores=[])
        code = compile(module, path, "exec", dont_inherit=True)
        ns = {"__name__": "_dash_stdlib_slice", "__file__": path}
        exec(code, ns)
        _SLICES[key] = ns[entry]
        return ns[entry]
    except Exception:
        return None

def managed_message(exe, windows, environ):
    """(text, cmd) for an externally managed Python.  It never names the
    flag that overrides the protection."""
    default = default_venv_path(windows, environ)
    if any(c in default for c in '`$"'):
        cmd = "dash_setup, venv(<a directory of your choice>)"
    else:
        cmd = 'dash_setup, venv("%s")' % default
    text = ("  This Python is externally managed (PEP 668):\n"
            "    %s\n"
            "  It refuses pip installs, so dash_setup ran none, and dash_setup does not\n"
            "  override that protection. Install dash's packages into a private\n"
            "  environment instead:\n"
            "    %s\n"
            "  then restart Stata and, before anything else uses Python, type the\n"
            "  python set exec line that command prints.\n") % (exe, cmd)
    return text, cmd


def nopip_message(exe, ensurepip, managed, windows):
    """(text, cmd) for a Python without pip."""
    text = ("  This Python has no pip: %s\n"
            "  dash_setup did not try to install anything with it.\n") % exe
    if ensurepip and not managed:
        cmd = shell_line([exe, "-m", "ensurepip", "--upgrade"], windows)
        text += "  Install pip into it first:\n    %s\n" % cmd
    else:
        cmd = ""
        text += ("  Install pip with your system's package manager (on Debian and Ubuntu: "
                 "python3-pip and python3-venv), or use dash_setup, venv(path).\n")
    return text, cmd


def below_floor_message(exe, pymin, kind):
    """(text, "") for a managed (kind "managed") or pip-less Python below
    dash's floor *pymin*.  WP-30 P1.33: both other messages suggested
    dash_setup, venv(), which refuses a Python below the floor too -- an
    advice loop.  This one names the floor and suggests no command."""
    what = ("is externally managed (PEP 668)" if kind == "managed"
            else "has no pip")
    text = ("  This Python %s and is below dash's minimum, Python %s:\n"
            "    %s\n"
            "  A private environment made from it would be below the minimum too,\n"
            "  so dash_setup suggests none. Install Python %s or later, link Stata\n"
            "  to it (help python), restart Stata and run dash_setup again.\n"
            ) % (what, pymin, exe, pymin)
    return text, ""


# ---------------------------------------------------------------------------
# Stata entry points: inputs from the calling program's locals, results back
# as its locals, environment text printed as plain text.  None raises.
# ---------------------------------------------------------------------------

def _linked():
    """(resolved c(python_exec) or None, c(python_exec) as Stata holds it)."""
    import sfi
    raw = sfi.SFIToolkit.macroExpand("\x60c(python_exec)'")
    pwd = sfi.SFIToolkit.macroExpand("\x60c(pwd)'")
    return resolve_exe(raw, pwd), raw


def _internal(exc):
    print("  dash_setup: internal error: %s: %s" % (type(exc).__name__, exc))


def stata_detect():
    """Inspect the linked Python; sets det_ok, det_managed, det_in_venv,
    det_pip, det_ensurepip, det_user, det_version and det_python."""
    import sfi
    out = {"det_ok": "0", "det_managed": "0", "det_in_venv": "0", "det_pip": "1",
           "det_ensurepip": "1", "det_user": "1", "det_version": "", "det_python": ""}
    try:
        exe, raw = _linked()
        out["det_python"] = exe or raw
        if exe is None:
            d = {"ok": False, "why": "the linked Python %s was not found" % raw}
        else:
            d = detect_environment(exe)
        if not d.get("ok"):
            print("  (could not inspect %s: %s; continuing as for an ordinary Python)"
                  % (exe or raw, d.get("why")))
        else:
            b = lambda x: "1" if x else "0"  # noqa: E731
            out.update(det_ok="1", det_managed=b(d["externally_managed"]),
                       det_in_venv=b(d["in_venv"]), det_pip=b(d["pip"]),
                       det_ensurepip=b(d["ensurepip"]),
                       det_user=b(d["user_site_enabled"] and not d["externally_managed"]),
                       det_version=".".join(str(x) for x in d["version"]))
    except Exception as exc:
        _internal(exc)
        out["det_ok"] = "0"
    for k, v in out.items():
        sfi.Macro.setLocal(k, v)


def stata_pip():
    """pip install the local `spec' with the linked Python from the
    hash-pinned lock (WP-32, I3; lock_install); one --user retry when `user'
    is "1" and the failure was an ordinary one.  Sets pip_outcome and
    pip_user."""
    import sfi
    outcome, user_ran = "other", "0"
    try:
        spec = sfi.Macro.getLocal("spec")
        allow_user = sfi.Macro.getLocal("user") == "1"
        ver = version_tuple(sfi.Macro.getLocal("ver"))
        exe, raw = _linked()
        if exe is None:
            print("  dash_setup: the linked Python %s was not found" % raw)
            outcome = "missing-interpreter"
        else:
            try:
                _spec_window(spec)
                ok = True
            except ValueError as exc:
                print("  " + str(exc))
                ok = False
            if ok:
                rc, out, err = lock_install(exe, [spec], ver)
                outcome = classify_failure(rc, err)
                if outcome == "externally-managed":
                    print((err.splitlines() or [""])[0])
                else:
                    print(out[-500:])
                    print(err[-200:])
                if outcome == "other" and allow_user:
                    print("      retrying with --user...")
                    user_ran = "1"
                    rc, out, err = lock_install(exe, [spec], ver, user=True)
                    outcome = classify_failure(rc, err)
                    print(out[-500:])
                    print(err[-200:])
                    if rc == 0:
                        add_user_site()
                if outcome == "ok":
                    importlib.invalidate_caches()
    except Exception as exc:
        _internal(exc)
        outcome = "other"
    sfi.Macro.setLocal("pip_outcome", outcome)
    sfi.Macro.setLocal("pip_user", user_ran)


def stata_shell_line():
    """The pip line for the local `spec', naming the linked Python, quoted
    for the shell.  Sets pip_cmd and pip_note; prints it for `how'
    "upgrade" or "manual"."""
    import sfi
    cmd, note = "", ""
    try:
        spec = sfi.Macro.getLocal("spec")
        how = sfi.Macro.getLocal("how")
        exe, raw = _linked()
        exe = exe or raw
        windows = os.name == "nt"
        try:
            # The vector pip_install_argv builds, without -P and the fixed
            # flags: a line to type, which may build from source on purpose.
            cmd = shell_line([a for a in pip_install_argv(exe, [spec], ())
                              if a not in _PIP_FIXED], windows)
        except ValueError:
            cmd = 'pip install "%s" with the Python at %s' % (spec, exe)
        note = "In PowerShell, put & and a space before it." if windows else ""
        if how == "upgrade":
            print("      To upgrade: " + cmd)
        elif how == "manual":
            print("    " + cmd)
        if how and note:
            print("      " + note)
    except Exception as exc:
        _internal(exc)
        cmd, note = "", ""
    sfi.Macro.setLocal("pip_cmd", cmd)
    sfi.Macro.setLocal("pip_note", note)


def stata_undo_line():
    """The pip uninstall line for the local `pkgs' (what this run
    installed), naming the linked Python, quoted for the shell; sets
    pip_cmd and prints it after "To undo: " (WP-31 I3).  A name that is
    not a package name prints nothing."""
    import sfi
    cmd = ""
    try:
        names = sfi.Macro.getLocal("pkgs").split()
        exe, raw = _linked()
        try:
            cmd = shell_line(pip_uninstall_argv(exe or raw, names),
                             os.name == "nt")
        except ValueError:
            cmd = ""
        if cmd:
            print("  To undo: " + cmd)
    except Exception as exc:
        _internal(exc)
        cmd = ""
    sfi.Macro.setLocal("pip_cmd", cmd)


def stata_guide():
    """Print the guidance for a managed (kind "managed") or pip-less
    ("nopip") Python; sets guide_cmd.  Below the floor (local pyok "0",
    pymin a version) it is below_floor_message's, with no command."""
    import sfi
    cmd = ""
    try:
        kind = sfi.Macro.getLocal("kind")
        exe, raw = _linked()
        exe = exe or raw
        windows = os.name == "nt"
        pymin = sfi.Macro.getLocal("pymin")
        if sfi.Macro.getLocal("pyok") == "0" and version_tuple(pymin):
            text, cmd = below_floor_message(exe, pymin, kind)
        elif kind == "managed":
            text, cmd = managed_message(exe, windows, os.environ)
        else:
            text, cmd = nopip_message(exe, sfi.Macro.getLocal("ensurepip") == "1",
                                      sfi.Macro.getLocal("managed") == "1", windows)
        print(text.rstrip("\n"))
    except Exception as exc:
        _internal(exc)
        cmd = ""
    sfi.Macro.setLocal("guide_cmd", cmd)


def stata_venv_check():
    """Validate the local `venv'; holds it for stata_venv.  Sets venv_ok."""
    import sfi
    ok = "0"
    _PENDING.pop("venv", None)
    try:
        raw = sfi.Macro.getLocal("venv")
        pwd = sfi.SFIToolkit.macroExpand("\x60c(pwd)'")
        try:
            absp, state, create = validate_venv_path(raw, pwd)
        except VenvPathError as exc:
            print("  venv() ............ refused: %s: %s" % (exc.path or raw, exc.args[0]))
        else:
            _PENDING["venv"] = (absp, state, create)
            print("  venv() ............ " + absp)
            ok = "1"
    except Exception as exc:
        _internal(exc)
        ok = "0"
    sfi.Macro.setLocal("venv_ok", ok)


def stata_venv():
    """Create or reuse the venv stata_venv_check held, install dash's
    packages into it and verify them.  Sets venv_step ("" on success),
    venv_linked, venv_python, venv_cmd and venv_base."""
    import sfi
    res = {"venv_step": "internal", "venv_linked": "0", "venv_python": "",
           "venv_cmd": "", "venv_base": ""}
    absp, made = None, False
    try:
        pymin_text = sfi.Macro.getLocal("pymin")
        pymin = version_tuple(pymin_text)
        mins = {"python": pymin_text, "packaging": "",
                "bokeh": sfi.Macro.getLocal("minb"), "numpy": sfi.Macro.getLocal("minn"),
                "pandas": sfi.Macro.getLocal("minp"),
                "bokeh_ceil": sfi.Macro.getLocal("maxb")}
        pend = _PENDING.pop("venv", None)
        exe, raw = _linked()
        res["venv_base"] = exe or raw
        windows = os.name == "nt"
        if pend is None:
            print("  dash_setup: internal error: no checked venv() path")
        elif exe is None:
            print("  dash_setup: the linked Python %s was not found" % raw)
        else:
            absp, state, create = pend
            if state == "venv":
                print("  using the environment already there...")
            else:
                print("  creating the environment...")
            ok, why = create_venv(exe, absp, state, create, sys.version_info)
            if not ok:
                print("  " + why)
                res["venv_step"] = "create"
            else:
                made = state != "venv"
                vpy = venv_python(absp, windows)
                d = detect_environment(vpy)
                if not d.get("ok") or not d.get("in_venv"):
                    print("  could not inspect the environment's Python %s: %s"
                          % (vpy, d.get("why", "it is not a virtual environment")))
                    res["venv_step"] = "inspect"
                elif tuple(d["version"][:len(pymin)]) < pymin:
                    print("  The environment's Python %s is below %s."
                          % (".".join(str(x) for x in d["version"]), pymin_text))
                    res["venv_step"] = "python"
                elif not d["pip"]:
                    print("  The environment's Python has no pip. Install it first:\n    "
                          + shell_line([vpy, "-m", "ensurepip", "--upgrade"], windows))
                    res["venv_step"] = "pip"
                else:
                    render_py = os.path.normpath(os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "dash_render.py"))
                    # WP-30 P1.30 (A107): a reused environment is probed
                    # first, so a bokeh at or above the ceiling in it is
                    # never downgraded.
                    have = ""
                    if state == "venv":
                        pre = verify_in(vpy, render_py, mins, d["version"])
                        have = (pre.get("packages") or {}).get("bokeh", "")
                    print("  installing packaging, bokeh, numpy and pandas into it...")
                    # From the hash-pinned lock (WP-32, I3).
                    rc, out, err = lock_install(
                        vpy, ["packaging",
                              bokeh_requirement(have, mins["bokeh"], mins["bokeh_ceil"]),
                              "numpy>=" + mins["numpy"], "pandas>=" + mins["pandas"]],
                        d["version"])
                    print(out[-500:])
                    print(err[-200:])
                    if rc != 0:
                        res["venv_step"] = "pip"
                    else:
                        v = verify_in(vpy, render_py, mins, d["version"])
                        if not v.get("ok"):
                            print("  The environment did not verify: %s" % v.get("why"))
                            for n, pv in sorted((v.get("packages") or {}).items()):
                                print("    %s %s" % (n, pv or "(not importable)"))
                            if "schemes" in v and not v["schemes"]:
                                print("    dash's schemes could not be read in it")
                            res["venv_step"] = "verify"
                        else:
                            if "bokeh" in (v.get("above") or []):
                                print("  bokeh %s in it is outside the verified range (%s or "
                                      "later, before %s); it was left as it is, and dash "
                                      "notes it when it draws."
                                      % ((v.get("packages") or {}).get("bokeh", ""),
                                         mins["bokeh"], mins["bokeh_ceil"]))
                            linked = (os.path.realpath(os.path.dirname(os.path.dirname(exe)))
                                      == os.path.realpath(absp))
                            cmd = 'python set exec "%s", permanently' % vpy
                            res.update(venv_step="", venv_linked="1" if linked else "0",
                                       venv_python=vpy, venv_cmd=cmd)
                            if linked:
                                print("  Stata is already linked to this environment; checking it.")
                            else:
                                print("  The environment is ready: %s" % absp)
                                print("  Restart Stata and, before anything else uses Python, type:")
                                print("    " + cmd)
                                print("  then run dash_setup again.")
        if res["venv_step"] and made:
            print("  The environment was left at %s; you may delete it." % absp)
    except Exception as exc:
        _internal(exc)
        res["venv_step"] = "internal"
    for k, v in res.items():
        sfi.Macro.setLocal(k, v)
