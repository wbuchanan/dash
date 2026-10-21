"""The corpus's dataset cache (WP-33 33-02, DECISIONS A-26).

    python3 scripts/corpus/datasets.py --fetch <run>

Fills a git-ignored cache (scripts/corpus/.cache, or $DASH_CORPUS_CACHE) with
the webuse datasets <run>/examples.jsonl names, fetching only those the cache
lacks, in one Stata session run through scripts/stata_slot.sh.  A corpus run
rewrites `webuse <name>' to `use "<cache>/<name>.dta", clear' (rewrite_setup)
and names each dataset the cache lacks, so it works offline.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import glob
import json
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_LOAD_RE = re.compile(r"^\s*(?:(?:quietly|qui|noisily|noi)\s+)*(sysuse|webuse|use)\s+"
                      r"\"?([^\s,\"]+)\"?\s*(?:,\s*(\w+))?\s*$")


def shipped(stata_dir):
    """Stems of the datasets Stata ships (<stata_dir>/ado/base/*/*.dta)."""
    return {os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(stata_dir, "ado", "base", "*", "*.dta"))}


def datasets_of(setup):
    """The dataset names a setup loads (sysuse/webuse/use), in order, each once."""
    out = []
    for c in setup:
        m = _LOAD_RE.match(c)
        if m:
            name = os.path.splitext(m.group(2).split("/")[-1])[0]
            if name not in out:
                out.append(name)
    return out


def cache_dir():
    """The dataset cache: $DASH_CORPUS_CACHE or <repo>/scripts/corpus/.cache."""
    return os.environ.get("DASH_CORPUS_CACHE") or os.path.join(REPO, "scripts", "corpus", ".cache")


def fetch_do(names, cache):
    """The do-file that fetches names with webuse and saves each into cache."""
    out = ["version 19", "set more off"]
    for n in names:
        out.append("capture noisily webuse %s, clear" % n)
        out.append('if _rc == 0 save "%s/%s.dta", replace' % (cache, n))
        out.append('display "CORPUS-FETCH %s " _rc' % n)
    return "\n".join(out) + "\n"


def fetch(names, run_dir):
    """Fetch names in one Stata session; {name: rc}."""
    cache = cache_dir()
    os.makedirs(cache, exist_ok=True)
    os.makedirs(run_dir, exist_ok=True)
    do = os.path.join(run_dir, "fetch.do")
    with open(do, "w", encoding="utf-8") as fh:
        fh.write(fetch_do(names, cache))
    subprocess.run(["sh", os.path.join(REPO, "scripts", "stata_slot.sh"), run_dir, do],
                   check=False)
    res = {n: None for n in names}
    log = os.path.join(run_dir, "fetch.log")
    if os.path.exists(log):
        with open(log, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                m = re.match(r"^CORPUS-FETCH (\S+) (-?\d+)\s*$", ln.strip())
                if m and m.group(1) in res:
                    res[m.group(1)] = int(m.group(2))
    return res


def rewrite_setup(setup, cache):
    """(setup with webuse lines read from the cache, the webuse names it lacks)."""
    out, missing = [], []
    for c in setup:
        m = _LOAD_RE.match(c)
        if m and m.group(1) == "webuse":
            name = m.group(2)
            out.append('use "%s/%s.dta", clear' % (cache, name))
            if not os.path.exists(os.path.join(cache, name + ".dta")) and name not in missing:
                missing.append(name)
            continue
        out.append(c)
    return out, missing


def uncached(names, cache):
    """The names, sorted and each once, whose <cache>/<name>.dta does not exist."""
    return sorted({n for n in names if not os.path.exists(os.path.join(cache, n + ".dta"))})


def _stata_dir():
    return os.environ.get("DASH_STATA_DIR") or "/Applications/StataNow"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fetch", required=True, metavar="RUN_DIR")
    a = ap.parse_args(argv)
    path = os.path.join(a.fetch, "examples.jsonl")
    with open(path, encoding="utf-8") as fh:
        recs = [json.loads(ln) for ln in fh if ln.strip()]
    ship = shipped(_stata_dir())
    names = []
    for r in recs:
        for n in r.get("datasets", []):
            if n not in ship and n not in names:
                names.append(n)
    cache = cache_dir()
    need = uncached(names, cache)
    for n in sorted(set(names) - set(need)):
        print("corpus: %s already cached" % n)
    if not need:
        return 0
    res = fetch(need, a.fetch)
    for n in need:
        rc = res.get(n)
        if rc == 0 and os.path.exists(os.path.join(cache, n + ".dta")):
            print("corpus: %s cached" % n)
        else:
            print("corpus: %s not fetched (rc %s)" % (n, rc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
