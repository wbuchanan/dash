#!/usr/bin/env python3
"""make_requirements_lock.py -- write dash_requirements.txt, the hash-pinned
lock dash_setup installs from (WP-32, I3; BUGS.md "dash_setup installs by
version, not by hash").

Usage (from the repository root; needs network access to PyPI):

    python3 scripts/make_requirements_lock.py [--out dash_requirements.txt]

Regenerate it at each release, and whenever dash_setup.ado's windows
(min_bokeh, max_bokeh, min_numpy, max_numpy, min_pandas, max_pandas),
_dash_pymin or the suites' pins (test/requirements-dev.txt,
test/requirements-stata.txt) change; commit the file it writes.  Nothing
is installed.

1. The requirements are read from dash_setup.ado -- packaging,
   bokeh>=min_bokeh,<max_bokeh, numpy>=min_numpy,<max_numpy,
   pandas>=min_pandas,<max_pandas -- and the Pythons from _dash_pymin up to
   PYTHONS' last.  Each of the four is pinned to the newest version the
   suites run under (:func:`tested_pins`; the maintainer's ruling of
   19oct2026: the lock pins what was tested).
2. For each target (a Python of PYTHONS and a platform of PLATFORMS) pip
   resolves them as that target would: ``pip install --dry-run
   --ignore-installed --only-binary=:all: --platform ... --python-version
   ... --implementation cp --report``, which reads PyPI's metadata.  pip
   evaluates a dependency's environment marker against this machine, not
   the target, so the resolved set is walked again from the requirements
   with each marker evaluated for the target (:func:`needed`); a
   dependency the target needs and pip left out is added to the roots and
   the target resolved again.
3. Every pinned release's wheels' sha256 digests are read from PyPI's JSON
   API (``https://pypi.org/pypi/<name>/<version>/json``): every wheel of
   that release is hashed, so the wheel pip picks on the real machine is
   among them.
4. A package pinned at one version for every target is written without a
   marker; one pinned differently, or needed by some targets only, carries
   a marker naming its targets (:func:`target_marker`).

The writer's pure parts (:func:`ado_requirements`, :func:`needed`,
:func:`combine`, :func:`render`, :func:`wheel_hashes`) are tested offline
by test/test_requirements_lock.py; the lock itself is checked there with
dash_setup_lib.read_lock, the reader dash_setup uses.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

try:
    from packaging.markers import Marker
    from packaging.requirements import Requirement
except ImportError:  # pip's own copy, which every pip carries
    from pip._vendor.packaging.markers import Marker
    from pip._vendor.packaging.requirements import Requirement

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The Pythons the lock covers: _dash_pymin's to the newest released.
PYTHONS = ("3.11", "3.12", "3.13", "3.14")

#: The platforms the lock covers: (name, pip --platform tags, marker env).
PLATFORMS = (
    ("macos-arm64",
     ["macosx_15_0_arm64", "macosx_14_0_arm64", "macosx_13_0_arm64",
      "macosx_12_0_arm64", "macosx_11_0_arm64"],
     {"sys_platform": "darwin", "platform_system": "Darwin",
      "platform_machine": "arm64", "os_name": "posix"}),
    ("macos-x86_64",
     ["macosx_15_0_x86_64", "macosx_14_0_x86_64", "macosx_13_0_x86_64",
      "macosx_12_0_x86_64", "macosx_11_0_x86_64", "macosx_10_13_x86_64",
      "macosx_10_9_x86_64"],
     {"sys_platform": "darwin", "platform_system": "Darwin",
      "platform_machine": "x86_64", "os_name": "posix"}),
    ("linux-x86_64",
     ["manylinux_2_28_x86_64", "manylinux_2_17_x86_64",
      "manylinux2014_x86_64"],
     {"sys_platform": "linux", "platform_system": "Linux",
      "platform_machine": "x86_64", "os_name": "posix"}),
    ("linux-aarch64",
     ["manylinux_2_28_aarch64", "manylinux_2_17_aarch64",
      "manylinux2014_aarch64"],
     {"sys_platform": "linux", "platform_system": "Linux",
      "platform_machine": "aarch64", "os_name": "posix"}),
    ("windows-amd64", ["win_amd64"],
     {"sys_platform": "win32", "platform_system": "Windows",
      "platform_machine": "AMD64", "os_name": "nt"}),
)

_PYPI = "https://pypi.org/pypi/%s/%s/json"


def normalize(name):
    """A distribution name as pip compares it (PEP 503)."""
    return re.sub(r"[-_.]+", "-", str(name)).lower()


def ado_requirements(ado_text):
    """(requirements, pymin) read from dash_setup.ado's text: the four
    requirements dash_setup installs, in its order, and _dash_pymin's
    Python.

    Raises:
        ValueError: if a constant is missing.
    """
    got = {}
    for key in ("min_bokeh", "max_bokeh", "min_numpy", "max_numpy",
                "min_pandas", "max_pandas"):
        m = re.search(r'^\s*local %s\s+"([0-9.]+)"' % key, ado_text, re.M)
        if not m:
            raise ValueError("dash_setup.ado sets no %s" % key)
        got[key] = m.group(1)
    m = re.search(r'program define _dash_pymin.*?return local pymin "([0-9.]+)"',
                  ado_text, re.S)
    if not m:
        raise ValueError("dash_setup.ado's _dash_pymin returns no pymin")
    return (["packaging", "bokeh>=%s,<%s" % (got["min_bokeh"], got["max_bokeh"]),
             "numpy>=%s,<%s" % (got["min_numpy"], got["max_numpy"]),
             "pandas>=%s,<%s" % (got["min_pandas"], got["max_pandas"])],
            m.group(1))


#: The packages whose tested version the lock pins.
TESTED = ("packaging", "bokeh", "numpy", "pandas")

#: The suites' pin files, read by :func:`tested_pins`.
PIN_FILES = ("test/requirements-stata.txt", "test/requirements-dev.txt")


def _vt(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def tested_pins(texts):
    """{name: version}: for each of TESTED, the newest ``name==version``
    the pin files' *texts* hold."""
    out = {}
    for text in texts:
        for ln in text.splitlines():
            m = re.match(r"^([A-Za-z0-9._-]+)==([0-9][0-9.]*)\s*$", ln.strip())
            if m and normalize(m.group(1)) in TESTED:
                n = normalize(m.group(1))
                if n not in out or _vt(m.group(2)) > _vt(out[n]):
                    out[n] = m.group(2)
    return out


def target_env(python, platform_env):
    """The marker environment of a target."""
    env = dict(platform_env)
    env.update(python_version=python, python_full_version=python + ".0",
               implementation_name="cpython",
               platform_python_implementation="CPython")
    return env


def target_marker(targets):
    """The marker true on exactly *targets*, (python, platform name) pairs;
    "" for every target."""
    every = {(p, n) for p in PYTHONS for n, _t, _e in PLATFORMS}
    targets = set(targets)
    if targets == every:
        return ""
    env = {n: e for n, _t, e in PLATFORMS}

    def plat(n):
        return ('sys_platform == "%s" and platform_machine == "%s"'
                % (env[n]["sys_platform"], env[n]["platform_machine"]))

    def pys(ps):
        return " or ".join('python_version == "%s"' % p for p in sorted(ps))

    by_plat = {}
    for p, n in targets:
        by_plat.setdefault(n, set()).add(p)
    names = [n for n, _t, _e in PLATFORMS]
    # Every platform with the same Pythons: a Python marker alone.
    if set(by_plat) == set(names) and len({frozenset(v) for v in by_plat.values()}) == 1:
        return pys(next(iter(by_plat.values())))
    parts = []
    for n in names:
        if n not in by_plat:
            continue
        if by_plat[n] == set(PYTHONS):
            parts.append("(%s)" % plat(n))
        else:
            parts.append("(%s and (%s))" % (plat(n), pys(by_plat[n])))
    return " or ".join(parts)


def needed(report, roots, env):
    """The names (normalised) the target *env* installs from pip's
    *report*: those reachable from *roots* through each resolved package's
    Requires-Dist whose marker holds in *env* (extras followed as asked).
    A name reached that the report does not hold is returned too, so the
    caller can add it to the roots."""
    meta = {normalize(i["metadata"]["name"]): i["metadata"]
            for i in report.get("install", [])}
    seen, todo = set(), [(Requirement(r), ()) for r in roots]
    while todo:
        req, extras = todo.pop()
        name = normalize(req.name)
        if req.marker is not None:
            ok = any(req.marker.evaluate(dict(env, extra=x)) for x in (extras or ("",)))
            if not ok:
                continue
        key = (name, tuple(sorted(req.extras)))
        if key in seen:
            continue
        seen.add(key)
        for dep in (meta.get(name, {}).get("requires_dist") or []):
            todo.append((Requirement(dep), tuple(sorted(req.extras))))
    return {n for n, _x in seen}


def combine(per_target):
    """[(name, version, marker)] from {target: {name: version}}, sorted by
    name and version: one entry for each pinned version, its marker naming
    the targets that install it ("" for all of them)."""
    groups = {}
    for target, pins in per_target.items():
        for name, version in pins.items():
            groups.setdefault((name, version), set()).add(target)
    return [(n, v, target_marker(t)) for (n, v), t in sorted(groups.items())]


def wheel_hashes(release_json):
    """The sorted sha256 digests of a PyPI release's wheels."""
    return sorted({u["digests"]["sha256"] for u in release_json.get("urls", [])
                   if u.get("packagetype") == "bdist_wheel"
                   and re.fullmatch(r"[0-9a-f]{64}", u.get("digests", {}).get("sha256", ""))})


def render(entries, hashes, requirements, today, tested=None):
    """The lock's text: a header, then each entry as pip reads it."""
    out = [
        "# dash_requirements.txt -- the Python packages dash_setup installs, pinned by",
        "# version and sha256 hash (pip install --require-hashes; WP-32, I3).",
        "# Written by scripts/make_requirements_lock.py on %s; do not edit by hand." % today,
        "# Regenerate: python3 scripts/make_requirements_lock.py (network access to PyPI).",
        "# requirements: " + " ".join(requirements),
        "# pythons: " + " ".join(PYTHONS),
        "# platforms: " + " ".join(n for n, _t, _e in PLATFORMS),
    ]
    if tested:
        out.append("# tested: " + " ".join("%s==%s" % kv for kv in sorted(tested.items())))
    for name, version, marker in entries:
        hs = hashes[(name, version)]
        if not hs:
            raise ValueError("%s %s has no wheel on PyPI" % (name, version))
        head = "%s==%s" % (name, version) + (" ; " + marker if marker else "")
        out.append(head + " \\")
        out += ["    --hash=sha256:%s%s" % (h, " \\" if i < len(hs) - 1 else "")
                for i, h in enumerate(hs)]
    return "\n".join(out) + "\n"


def resolve(python_exe, python, tags, requirements):
    """pip's report for one target (network)."""
    with tempfile.TemporaryDirectory(prefix="dash_lock_") as work:
        rep = os.path.join(work, "report.json")
        argv = [python_exe, "-m", "pip", "install", "--dry-run", "--ignore-installed",
                "--only-binary=:all:", "--disable-pip-version-check", "--no-input",
                "-q", "--python-version", python, "--implementation", "cp",
                "--report", rep]
        for t in tags:
            argv += ["--platform", t]
        subprocess.run(argv + list(requirements), check=True, cwd=work,
                       stdout=subprocess.DEVNULL)
        with open(rep, encoding="utf-8") as fh:
            return json.load(fh)


def fetch_release(name, version):
    """PyPI's JSON for one release (network)."""
    with urllib.request.urlopen(_PYPI % (name, version), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, "dash_requirements.txt"))
    ap.add_argument("--python", default=sys.executable,
                    help="the Python whose pip resolves (default: this one)")
    a = ap.parse_args(argv)
    with open(os.path.join(ROOT, "dash_setup.ado"), encoding="utf-8") as fh:
        requirements, pymin = ado_requirements(fh.read())
    if PYTHONS[0] != pymin:
        raise SystemExit("PYTHONS starts at %s but _dash_pymin is %s" % (PYTHONS[0], pymin))
    texts = []
    for rel in PIN_FILES:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            texts.append(fh.read())
    tested = tested_pins(texts)
    pinned = ["%s==%s" % kv for kv in sorted(tested.items())]
    per_target, names = {}, {}
    for python in PYTHONS:
        for pname, tags, penv in PLATFORMS:
            env = target_env(python, penv)
            roots = list(requirements) + pinned
            for _round in range(5):
                report = resolve(a.python, python, tags, roots)
                pins = {normalize(i["metadata"]["name"]): i["metadata"]["version"]
                        for i in report["install"]}
                for i in report["install"]:
                    names[normalize(i["metadata"]["name"])] = i["metadata"]["name"]
                want = needed(report, requirements, env)
                extra = sorted(want - set(pins))
                if not extra:
                    break
                roots = list(requirements) + pinned + extra
            else:
                raise SystemExit("%s %s did not settle" % (python, pname))
            per_target[(python, pname)] = {n: pins[n] for n in sorted(want)}
            print("%s %s: %d packages" % (python, pname, len(want)), flush=True)
    entries = combine(per_target)
    hashes = {(n, v): wheel_hashes(fetch_release(names.get(n, n), v))
              for n, v, _m in entries}
    text = render([(names.get(n, n), v, m) for n, v, m in entries],
                  {(names.get(n, n), v): h for (n, v), h in hashes.items()},
                  requirements, datetime.date.today().strftime("%d%b%Y").lower(),
                  tested)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote %s: %d entries" % (a.out, len(entries)))


if __name__ == "__main__":
    main()
