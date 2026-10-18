"""extract_pip_refusals.py -- capture pip's refusal texts for dash_setup's tests (WP-29 P0.19).

Usage:
    python3 scripts/extract_pip_refusals.py --managed <python with EXTERNALLY-MANAGED> \
        --plain <python without it> --out test/fixtures/pip_refusals.json

Every child runs from an argv list (never a shell), offline (PIP_NO_INDEX=1),
without an inherited PYTHONPATH, inside one tempfile.mkdtemp() folder that is
removed at the end. The folder's path is written "<tmp>" in the records.
The fixture is regenerated only by this script (never patched by hand).
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile

_STDLIB_MARKER = (
    "import os, sysconfig; "
    "print(os.path.isfile(os.path.join(sysconfig.get_path('stdlib'), 'EXTERNALLY-MANAGED')))"
)


def _env():
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["PIP_NO_INDEX"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return env


def _run(argv, cwd):
    r = subprocess.run(argv, cwd=cwd, env=_env(), stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def _is_managed(exe, cwd):
    rc, out, _ = _run([exe, "-c", _STDLIB_MARKER], cwd)
    return rc == 0 and out.strip() == "True"


def _record(argv, tmp, cwd):
    rc, _, err = _run(argv, cwd)
    return {
        "argv": [a.replace(tmp, "<tmp>") for a in argv],
        "rc": rc,
        "stderr": err.replace(tmp, "<tmp>"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--managed", required=True)
    ap.add_argument("--plain", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    tmp = tempfile.mkdtemp(prefix="dash_pip_refusals_")
    try:
        if not _is_managed(a.managed, tmp):
            sys.stderr.write("--managed %s has no EXTERNALLY-MANAGED marker\n" % a.managed)
            return 2
        if _is_managed(a.plain, tmp):
            sys.stderr.write("--plain %s has an EXTERNALLY-MANAGED marker\n" % a.plain)
            return 2
        venv = os.path.join(tmp, "venv")
        vnp = os.path.join(tmp, "vnp")
        _run([a.plain, "-m", "venv", venv], tmp)
        _run([a.plain, "-m", "venv", "--without-pip", vnp], tmp)
        vpy = os.path.join(venv, "bin", "python")
        npy = os.path.join(vnp, "bin", "python")
        recs = {
            "externally_managed": _record(
                [a.managed, "-m", "pip", "install", "--dry-run", "--no-index", "bokeh>=3.8"], tmp, tmp),
            "user_in_venv": _record(
                [vpy, "-m", "pip", "install", "--dry-run", "--no-index", "--user", "zzdashnope"], tmp, tmp),
            "user_disabled": _record(
                [a.plain, "-s", "-m", "pip", "install", "--dry-run", "--no-index", "--user", "zzdashnope"],
                tmp, tmp),
            "no_pip": _record([npy, "-m", "pip", "--version"], tmp, tmp),
            "offline_no_match": _record(
                [vpy, "-m", "pip", "install", "--no-index", "zzdashnope"], tmp, tmp),
        }
        _, pipv, _ = _run([a.managed, "-m", "pip", "--version"], tmp)
        words = pipv.split()
        pip_version = words[words.index("pip") + 1] if "pip" in words[:-1] else ""
        _, pyv, _ = _run([a.managed, "-c", "import sys; print('%d.%d.%d' % sys.version_info[:3])"], tmp)
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=here, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL)
        now = datetime.datetime.now()
        out = {"_meta": {
            "stata_version": "not used (pip output)",
            "pip_version": pip_version,
            "python_version": pyv.strip(),
            "born_date": "not used (pip output)",
            "dash_commit": r.stdout.decode().strip(),
            "extracted": now.isoformat(timespec="seconds"),
            "source": "scripts/extract_pip_refusals.py",
        }}
        out.update(recs)
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
