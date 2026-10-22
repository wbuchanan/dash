"""The corpus's known-differences ledger (WP-33 33-05, DECISIONS A-10).

    python3 scripts/corpus/ledger.py [--run <run>]

Compiles scripts/corpus/ledger.tsv into test/fixtures/corpus_ledger.json.
A row is `gaps4_id<TAB>check<TAB>plottype or *<TAB>when<TAB>note`, its
gaps4_id `<id>` (an open item), `<id> (documented)` or `<id> (residual)`.
A row is live when its form agrees with its item's state in GAPS4.md: a
plain row while the item is open, a documented row while it is open or
Documented, a residual row while it is open or Partly closed.  Every item's
closing commit deletes its plain rows and keeps the other two forms.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import json
import re
import subprocess
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TSV_PATH = os.path.join(REPO, "scripts", "corpus", "ledger.tsv")
OUT_PATH = os.path.join(REPO, "test", "fixtures", "corpus_ledger.json")
SOURCE = "scripts/corpus/ledger.py"

ROW_KEYS = ("gaps4_id", "id", "form", "check", "plottype", "when", "note")

_ID = re.compile(r"^(?P<id>[A-Za-z]+(?::[A-Za-z]+)?-\d+[a-z]?)(?: \((?P<form>documented|residual)\))?$")
_TRACKED = re.compile(r"^- \*\*(?P<id>\S+) Tracked:\*\* (?P<text>\S.*)$")
_STATES = (("Open (", "open"), ("Closed in ", "closed"), ("Documented in ", "documented"),
           ("Partly closed in ", "partly"))
_LIVE = {"plain": ("open",), "documented": ("open", "documented"),
         "residual": ("open", "partly")}


def read_tsv(path=TSV_PATH):
    """The ledger rows of path; a malformed line raises ValueError naming its line."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for n, raw in enumerate(fh, 1):
            ln = raw.rstrip("\n")
            if not ln.strip() or ln.lstrip().startswith("#"):
                continue
            parts = ln.split("\t")
            if len(parts) != 5 or not all(p.strip() for p in parts[:4]):
                raise ValueError("%s line %d: expected 5 tab-separated fields" % (
                    os.path.basename(path), n))
            m = _ID.match(parts[0].strip())
            if not m:
                raise ValueError("%s line %d: %r is not <id>, <id> (documented) or "
                                 "<id> (residual)" % (os.path.basename(path), n, parts[0]))
            when = parts[3].strip()
            if when != "*":
                try:
                    re.compile(when)
                except re.error as exc:
                    raise ValueError("%s line %d: bad regex: %s" % (
                        os.path.basename(path), n, exc)) from None
            rows.append({"gaps4_id": parts[0].strip(), "id": m.group("id"),
                         "form": m.group("form") or "plain", "check": parts[1].strip(),
                         "plottype": parts[2].strip(), "when": when, "note": parts[4].strip()})
    return rows


def gaps4_states(path=None):
    """{lead id: open | closed | documented | partly} from GAPS4.md's Tracked lines."""
    path = path or os.path.join(REPO, "GAPS4.md")
    out = {}
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            m = _TRACKED.match(ln.rstrip("\n"))
            if not m:
                continue
            for prefix, state in _STATES:
                if m.group("text").startswith(prefix):
                    out[m.group("id")] = state
                    break
    return out


def live(row, states):
    """True when the row's form agrees with its item's state (D-33-05.e)."""
    return states.get(row["id"]) in _LIVE.get(row["form"], ())


def _git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip() or None


def _stata_version(run_dir):
    p = os.path.join(run_dir, "stata_version.txt")
    with open(p, encoding="utf-8") as fh:
        return fh.read().strip()


def write_json(rows, out_path=OUT_PATH, run_dir=None):
    """Write the fixture {"_meta", "rows"}; _meta.stata_version from the run, or kept."""
    old = {}
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as fh:
            old = json.load(fh).get("_meta") or {}
    today = time.strftime("%d %b %Y")
    if run_dir is not None:
        version, born = _stata_version(run_dir), today
    else:
        version, born = old.get("stata_version"), old.get("born_date") or today
    meta = {"born_date": born, "dash_commit": _git_head(), "extracted": today,
            "source": SOURCE, "stata_version": version,
            "tsv": "scripts/corpus/ledger.tsv"}
    doc = {"_meta": meta, "rows": [{k: r[k] for k in ROW_KEYS} for r in rows]}
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", default=None, metavar="RUN_DIR")
    ap.add_argument("--tsv", default=TSV_PATH, help=argparse.SUPPRESS)
    ap.add_argument("--out", default=OUT_PATH, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    rows = read_tsv(a.tsv)
    write_json(rows, a.out, a.run)
    print("corpus: ledger %d rows -> test/fixtures/corpus_ledger.json" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
