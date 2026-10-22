"""Count a corpus run: the last stage of make corpus (WP-33 33-08).

    python3 scripts/corpus/summary.py --run <run> [--out <json>]

Reads <run>/examples.jsonl, extract_duplicates.tsv and verdicts.jsonl and
prints one line: the examples, the duplicates removed, the verdicts and how
many examples twoway draws for the gallery.  With --out it also writes the
counts with a _meta stamp; section 33-14 writes test/fixtures/
corpus_baseline.json this way.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import datetime
import json
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = "scripts/corpus/summary.py"
_VERDICTS = ("Same", "Close", "Differs", "skipped")


def _jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def _sorted(d):
    return {k: (_sorted(v) if isinstance(v, dict) else v) for k, v in sorted(d.items())}


def summarise(run_dir):
    """The run's counts: examples, duplicates, verdicts, refusals, gallery, per plot type,
    per ledger id and the differences outside tolerance no ledger row explains."""
    examples = _jsonl(os.path.join(run_dir, "examples.jsonl"))
    dup = 0
    path = os.path.join(run_dir, "extract_duplicates.tsv")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            dup = max(0, sum(1 for ln in fh if ln.strip()) - 1)
    verdicts = dict.fromkeys(_VERDICTS, 0)
    refused = {"twoway": 0, "dash": 0}
    by_type, led, unexplained = {}, {}, {}
    gallery = 0
    for v in _jsonl(os.path.join(run_dir, "verdicts.jsonl")):
        said = v.get("verdict") or "skipped"
        verdicts[said] += 1
        t = by_type.setdefault(v.get("plottype") or "", dict.fromkeys(_VERDICTS, 0))
        t.setdefault("examples", 0)
        t["examples"] += 1
        t[said] += 1
        rc_tw, rc_da = v.get("rc_twoway"), v.get("rc_dash")
        if not v.get("skip") and rc_tw not in (0, None):
            refused["twoway"] += 1
        if not v.get("skip") and rc_tw == 0 and rc_da not in (0, None):
            refused["dash"] += 1
        gallery += bool(v.get("gallery"))
        for lid in v.get("ledger") or []:
            led[lid] = led.get(lid, 0) + 1
        for d in v.get("differences") or []:
            if not d.get("within_tol") and not d.get("gaps4"):
                unexplained[d["check"]] = unexplained.get(d["check"], 0) + 1
    return _sorted({"examples": len(examples), "duplicates": dup, "verdicts": verdicts,
                    "refused": refused, "gallery": gallery, "by_plottype": by_type,
                    "ledger": led, "unexplained": unexplained})


def _git_head():
    p = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def write_fixture(summary, out_path, run_dir):
    """Write summary plus its _meta stamp to out_path (2-space indent, sorted keys)."""
    path = os.path.join(run_dir, "stata_version.txt")
    version = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            version = fh.read().strip() or None
    day = datetime.date.fromtimestamp(os.path.getmtime(os.path.join(run_dir, "examples.jsonl")))
    stamp = day.strftime("%d %b %Y")
    d = dict(summary)
    d["_meta"] = {"stata_version": version, "born_date": stamp, "extracted": stamp,
                  "dash_commit": _git_head(), "source": SOURCE}
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(d, indent=2, sort_keys=True) + "\n")
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, metavar="RUN_DIR")
    ap.add_argument("--out", default=None, metavar="JSON")
    a = ap.parse_args(argv)
    s = summarise(a.run)
    v = s["verdicts"]
    print("corpus: %d examples (%d duplicates removed): %d Same, %d Close, %d Differs, "
          "%d skipped; %d twoway draws for the gallery"
          % (s["examples"], s["duplicates"], v["Same"], v["Close"], v["Differs"],
             v["skipped"], s["gallery"]))
    if a.out:
        write_fixture(s, a.out, a.run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
