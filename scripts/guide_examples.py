"""Build the user's guide examples: run each docs/guide/examples/<name>.do in
its own batch Stata session and keep the page it writes as <name>.html.

    python3 scripts/guide_examples.py [--only NAME ...] [--jobs N]

make guide runs it.  Each example is a do-file a reader can copy as it
stands: it writes <name>.html, with saving(<name>.html, replace), into the
folder it runs in.  The builder runs it in a scratch folder through
scripts/stata_slot.sh, after a header that puts this checkout's dash first
on the ado-path and keeps every browser window shut ($dash_nobrowser),
reads the do-file's return code from the log, and copies the page into
docs/guide/examples/.  BUILD.md there records each do-file's SHA-256 and the
dash commit that built its page; test/test_guide.py fails while a do-file
differs from the one its page was built from.  Like the gallery, the pages
are built on the maintainer's machine (CI has no Stata) and committed.
"""
import argparse
import concurrent.futures
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(REPO, "docs", "guide", "examples")
RECORD = "BUILD.md"
SLOT_CMD = (os.path.join(REPO, "scripts", "stata_slot.sh"),)
#: dash's own files: a page built while one of them differs from HEAD is
#: recorded with the commit and -dirty.
DASH_FILES = ("dash.ado", "dash_parse.mata", "dash_render.py")

_NAME = re.compile(r"^[a-z][a-z0-9-]*$")
_ROW = re.compile(r"^\| ([a-z][a-z0-9-]*) \| ([0-9a-f]{64}) \| ([0-9a-f]+(?:-dirty)?) \|$")
_HEAD = ["# How each guide example was built", "",
         "Written by scripts/guide_examples.py (make guide); do not edit by hand.",
         "Each row is a do-file's SHA-256 when its page was built and the dash",
         "commit that built it.  test/test_guide.py fails while a do-file differs",
         "from its row: run make guide to rebuild its page.", "",
         "| Example | Do-file SHA-256 | dash commit |", "|---|---|---|"]


def names(folder=EXAMPLES):
    """The examples in *folder*, each <name>.do's name, sorted; a name that
    is not lower-case letters, digits and hyphens is refused."""
    out = sorted(f[:-3] for f in os.listdir(folder) if f.endswith(".do"))
    for n in out:
        if not _NAME.match(n):
            raise ValueError("guide: example %r is not named in lower case "
                             "letters, digits and hyphens" % n)
    return out


def sha256_of(path):
    """The SHA-256 of a file's bytes, in hex."""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def wrapper(repo, do_path):
    """The do-file that runs one example under the builder's header."""
    for p in (repo, do_path):
        if '"' in p or "`" in p or "$" in p:
            raise ValueError("guide: a path Stata would misread: %r" % p)
    return "\n".join(["version 19", "set more off", "set linesize 255",
                      'adopath ++ "%s/"' % repo.rstrip("/"),
                      "global dash_nobrowser 1",
                      'capture noisily do "%s"' % do_path,
                      'display "##RC " _rc', ""])


def rc_of(log_text):
    """The example's return code from the wrapper's ##RC line, or None when
    the log has none (Stata stopped before it)."""
    found = re.findall(r"^##RC (\d+)\s*$", log_text, re.M)
    return int(found[-1]) if found else None


def build_one(name, folder=EXAMPLES, repo=REPO, slot_cmd=SLOT_CMD):
    """Run <name>.do in a scratch folder and copy the <name>.html it writes
    into *folder*; None when it did, else why not."""
    do_path = os.path.join(folder, name + ".do")
    with tempfile.TemporaryDirectory(prefix="dash-guide-") as work:
        run = os.path.join(work, "run.do")
        with open(run, "w", encoding="utf-8") as fh:
            fh.write(wrapper(repo, do_path))
        subprocess.run(list(slot_cmd) + [work, run], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log_path = os.path.join(work, "run.log")
        log = ""
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8", errors="replace") as fh:
                log = fh.read()
        rc = rc_of(log)
        tail = "\n".join(log.rstrip().splitlines()[-25:])
        if rc != 0:
            return "%s.do ended with rc %s:\n%s" % (name, rc, tail)
        page = os.path.join(work, name + ".html")
        if not os.path.exists(page):
            return "%s.do wrote no %s.html:\n%s" % (name, name, tail)
        shutil.copyfile(page, os.path.join(folder, name + ".html"))
    return None


def dash_commit(repo=REPO):
    """The checkout's commit, eight hex digits, with -dirty when one of
    DASH_FILES differs from it."""
    head = subprocess.run(["git", "-C", repo, "rev-parse", "--short=8", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    diff = subprocess.run(["git", "-C", repo, "status", "--porcelain", "--", *DASH_FILES],
                          capture_output=True, text=True, check=True).stdout.strip()
    return head + ("-dirty" if diff else "")


def read_record(folder=EXAMPLES):
    """{name: (sha256, commit)} from BUILD.md; {} when there is none."""
    path = os.path.join(folder, RECORD)
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh.read().splitlines()[len(_HEAD):]:
            m = _ROW.match(line)
            if not m:
                raise ValueError("guide: %s holds a line it should not: %r" % (RECORD, line))
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


def write_record(rows, folder=EXAMPLES):
    """Write BUILD.md from {name: (sha256, commit)}, one row a name, sorted."""
    lines = _HEAD + ["| %s | %s | %s |" % (n, rows[n][0], rows[n][1]) for n in sorted(rows)]
    with open(os.path.join(folder, RECORD), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def main(argv=None, folder=EXAMPLES, repo=REPO, slot_cmd=SLOT_CMD):
    ap = argparse.ArgumentParser(description="Build the user's guide examples.")
    ap.add_argument("--only", nargs="+", metavar="NAME")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args(argv)
    every = names(folder)
    todo = a.only or every
    unknown = sorted(set(todo) - set(every))
    if unknown:
        print("guide: no such example: %s" % " ".join(unknown), file=sys.stderr)
        return 2
    shas = {n: sha256_of(os.path.join(folder, n + ".do")) for n in todo}
    commit = dash_commit(repo)
    with concurrent.futures.ThreadPoolExecutor(max(1, a.jobs)) as pool:
        why = dict(zip(todo, pool.map(
            lambda n: build_one(n, folder, repo, slot_cmd), todo)))
    rows = {n: r for n, r in read_record(folder).items() if n in every}
    for n in todo:
        if why[n] is None:
            rows[n] = (shas[n], commit)
            print("guide: built %s.html" % n)
        else:
            print("guide: %s" % why[n], file=sys.stderr)
    write_record(rows, folder)
    return 1 if any(why.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
