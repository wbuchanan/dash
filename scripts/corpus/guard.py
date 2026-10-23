"""The certification suite's corpus guard (WP-33 33-09).

    python3 scripts/corpus/guard.py --select <run>

About twenty help-file examples, one per common plot type
(scripts/corpus/guard_examples.txt, chosen once by D-33-09.b), are drawn by
twoway and by dash inside the certification session (block S09 of
test/test_wp33_truth.cscript), dash's page is exported at twoway's size and
judged by 33-05's judge, and the rows must equal
test/fixtures/corpus_guard_truth.json, which
scripts/extract_corpus_guard_truth.do writes.  This module writes no do-file
text, log reader, exporter or comparison of its own: it wraps 33-03's and
33-04's do-file texts and calls 33-04's and 33-05's functions.

--select prints the chosen list lines over a candidate run's
examples.jsonl, twoway.jsonl and verdicts.jsonl, then the types with no
example.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import json

from scripts.corpus import twoway_run, dash_run, verdict, datasets, extract
from scripts.corpus import ledger as corpus_ledger

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIST_PATH = os.path.join(REPO, "scripts", "corpus", "guard_examples.txt")
SCRIPT = "scripts/extract_corpus_guard_truth.do"

#: The guard's types, in the order they choose (D-33-09.b).
TYPES = ("scatter", "line", "connected", "area", "bar", "spike", "dropline", "dot",
         "lfit", "qfitci", "lfitci", "lpoly", "lowess", "kdensity", "histogram",
         "function", "rarea", "rcap", "pcarrow", "contour", "tsline", "by", "colorvar")
#: Types chosen by an option of the example rather than by a plot.
OPTION_TYPES = ("by", "colorvar")
#: A setup line's first word must be one of these (generate and label abbreviated).
SETUP_WORDS = frozenset({"sysuse", "use", "replace", "tsset", "sort"}
                        | {"generate"[:n] for n in range(1, 9)}
                        | {"label"[:n] for n in range(2, 6)})
#: The fields measure() returns per example (TR-33-09.1).
MEASURED = ("rc_twoway", "first_twoway", "rc_dash", "first_dash", "verdict", "checks",
            "summary", "ledger", "ssim", "size_matched")
#: The fields compare() compares (D-33-09.c); the other four are recorded only.
COMPARED = ("rc_twoway", "first_twoway", "rc_dash", "verdict", "checks", "summary")
#: Verdicts from worst to best.
RANK = {"Differs": 0, "Close": 1, "Same": 2}
#: The SSIM margin from T_same an example keeps (DECISIONS A-4).
SSIM_MARGIN = 0.01

#: The wrapper (D-33-09.d).  It draws under twoway's default scheme,
#: stcolor, whatever the session's is (cscript sets c(scheme_cscript)), and
#: restores the session's scheme, line size, ado-path and data after.
GUARD_DO = """\
* guard.do -- written by scripts/corpus/guard.py (WP-33 33-09); leaves the session as it found it
local _g_scheme "`c(scheme)'"
local _g_ls = c(linesize)
local _g_ado `"$S_ADO"'
local _g_nb `"$dash_nobrowser"'
preserve
set scheme stcolor
capture log close s09tw
log using "<run>/tw/guard.log", text replace name(s09tw)
capture noisily do "<run>/tw/guard_tw.do"
local _g_rc1 = _rc
log close s09tw
capture graph drop _all
capture log close s09da
log using "<run>/dash/guard.log", text replace name(s09da)
capture noisily do "<run>/dash/guard_dash.do"
local _g_rc2 = _rc
log close s09da
restore
set scheme `_g_scheme'
set linesize `_g_ls'
global S_ADO `"`_g_ado'"'
global dash_nobrowser `"`_g_nb'"'
capture graph drop _all
capture serset clear
dash clear
display "GUARD-DONE `_g_rc1' `_g_rc2'"
"""


def _jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def read_list(path=LIST_PATH):
    """The guard's example ids (comments after # and blank lines ignored)."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            s = ln.split("#", 1)[0].strip()
            if s:
                out.append(s)
    return out


def candidates(examples, shipped):
    """The help-file records whose setup words and datasets D-33-09.b allows."""
    out = []
    for r in examples:
        if r.get("source") != "help":
            continue
        if not all((s.split() or [""])[0] in SETUP_WORDS for s in r.get("setup") or []):
            continue
        if not all(n in shipped for n in r.get("datasets") or []):
            continue
        out.append(r)
    return out


def _options(r):
    sig = r.get("signature") or ""
    return set(sig.split("|", 1)[1].split(",")) if "|" in sig else set()


def _choose(run_dir, rules, shipped=None):
    """[(type, record)] in TYPES order and the types with no example."""
    if shipped is None:
        shipped = datasets.shipped(os.environ.get("DASH_STATA_DIR") or "/Applications/StataNow")
    examples = _jsonl(os.path.join(run_dir, "examples.jsonl"))
    tw = {r["id"]: r for r in _jsonl(os.path.join(run_dir, "twoway.jsonl"))}
    vd = {r["id"]: r for r in _jsonl(os.path.join(run_dir, "verdicts.jsonl"))}
    t_same = rules.get("T_same")
    ok = []
    for r in candidates(examples, shipped):
        if (tw.get(r["id"]) or {}).get("rc") != 0:
            continue
        if t_same is not None:
            s = (vd.get(r["id"]) or {}).get("ssim")
            if s is None or abs(s - t_same) < SSIM_MARGIN:
                continue
        ok.append(r)
    ok.sort(key=lambda r: r["id"])
    chosen, taken, skipped = [], set(), []
    for t in TYPES:
        if t in OPTION_TYPES:
            tiers = [[r for r in ok if t in _options(r)]]
        else:
            from scripts.corpus import extract
            tiers = [[r for r in ok if r.get("plottype") == t],
                     [r for r in ok if t in extract.plot_types(r["cmd"])]]
        pick = None
        for tier in tiers:
            if tier:
                pick = next((r for r in tier if r["id"] not in taken), None)
                break
        if pick is None:
            skipped.append(t)
            continue
        taken.add(pick["id"])
        chosen.append((t, pick))
    return chosen, skipped


def select(run_dir, rules, shipped=None):
    """D-33-09.b over run_dir: (the chosen ids in id order, the types skipped)."""
    chosen, skipped = _choose(run_dir, rules, shipped)
    return sorted(r["id"] for _t, r in chosen), skipped


def records_from_run(run_dir, ids, fixture=None):
    """id -> record: the fixture's frozen record, else run_dir's (D-33-09.g)."""
    frozen = (fixture or {}).get("examples") or {}
    out, need = {}, []
    for i in ids:
        if i in frozen:
            # D58: a record frozen before D58 is read twoway-first.
            rec = dict(frozen[i]["record"])
            rec["cmd"] = extract.twoway_form(rec["cmd"])
            rec["dash_cmd"] = extract.to_dash(rec["cmd"])
            out[i] = rec
        else:
            need.append(i)
    if need:
        found = {}
        if run_dir is not None:
            found = {r["id"]: r for r in _jsonl(os.path.join(run_dir, "examples.jsonl"))}
        missing = [i for i in need if i not in found]
        if missing:
            raise ValueError("guard examples in neither the fixture nor the run: %s"
                             % ", ".join(missing))
        for i in need:
            out[i] = found[i]
    return {i: out[i] for i in ids}


def write_examples(records, run_dir):
    """Write <run_dir>/examples.jsonl, one record per line in id order; its path."""
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, "examples.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in sorted(records):
            fh.write(json.dumps(records[i], ensure_ascii=False) + "\n")
    return path


def guard_do(examples, run_dir, cache, repo):
    """Write the twoway and dash do-files and guard.do under run_dir; guard.do's path."""
    tw_dir, da_dir = os.path.join(run_dir, "tw"), os.path.join(run_dir, "dash")
    os.makedirs(os.path.join(tw_dir, "svg"), exist_ok=True)
    os.makedirs(da_dir, exist_ok=True)
    with open(os.path.join(tw_dir, "guard_tw.do"), "w", encoding="utf-8") as fh:
        fh.write(twoway_run.do_text(examples, run_dir + "/tw/svg", cache))
    with open(os.path.join(da_dir, "guard_dash.do"), "w", encoding="utf-8") as fh:
        fh.write(dash_run.do_text(examples, run_dir + "/dash", cache, repo))
    path = os.path.join(run_dir, "guard.do")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(GUARD_DO.replace("<run>", run_dir))
    return path


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def measure(run_dir, examples, rules_path, ledger_path, gaps4_path=None):
    """id -> the ten MEASURED fields of 33-05's judge row, from guard.do's two logs."""
    examples = sorted(examples, key=lambda e: e["id"])
    parsed_tw = twoway_run.parse_log(_read(os.path.join(run_dir, "tw", "guard.log")))
    parsed_da = twoway_run.parse_log(_read(os.path.join(run_dir, "dash", "guard.log")))
    tw = twoway_run.records(examples, parsed_tw, os.path.join(run_dir, "tw", "svg"), run_dir)
    da = dash_run.records(examples, parsed_da, os.path.join(run_dir, "dash"), run_dir, tw)
    tw = {r["id"]: r for r in tw}
    da = {r["id"]: dict(dict.fromkeys(dash_run.CHROME_KEYS), **r) for r in da}
    pages, sizes = {}, {}
    for i, r in da.items():
        if r.get("rc") != 0 or not r.get("html"):
            continue
        t = tw.get(i) or {}
        wi, hi = t.get("width_in") or 7.5, t.get("height_in") or 4.5
        pages[i] = os.path.join(run_dir, r["html"])
        sizes[i] = (int(round(wi * dash_run.PX_PER_IN)), int(round(hi * dash_run.PX_PER_IN)))
    got = dash_run.export_pages(pages, sizes, os.path.join(run_dir, "dash")) if pages else {}
    for i, g in got.items():
        r = da[i]
        if "error" in g:
            r["export_error"] = twoway_run._hide_paths(g["error"], run_dir)
            continue
        r.update(svg="dash/%s.svg" % i, view="dash/%s.view.json" % i,
                 size_matched=g["size_matched"], w=g["w"], h=g["h"],
                 js_errors=[twoway_run._hide_paths(e, run_dir) for e in g["js_errors"]])
    with open(rules_path, encoding="utf-8") as fh:
        rules = json.load(fh)
    led = verdict.load_ledger(ledger_path)
    states = corpus_ledger.gaps4_states(gaps4_path)
    page = os.path.join(run_dir, "raster.html")
    with open(page, "w", encoding="utf-8") as fh:
        fh.write(verdict.RASTER_PAGE)
    out = {}
    with dash_run.CorpusProbe(page, ready=verdict.RASTER_READY) as probe:
        for e in examples:
            row = verdict.judge(e, tw.get(e["id"]), da.get(e["id"]), run_dir, rules, led,
                                states, probe)
            out[e["id"]] = {k: row.get(k) for k in MEASURED}
    return out


def _fmt(v):
    if isinstance(v, (list, tuple)):
        return "[%s]" % ", ".join(str(x) for x in v)
    return str(v)


def compare(want, got):
    """D-33-09.c: one message per listed id whose live row differs, sorted by id."""
    regen = "regenerate test/fixtures/corpus_guard_truth.json with %s" % SCRIPT
    out = []
    for i in sorted(want):
        w, g = want[i], got.get(i)
        if g is None:
            out.append("%s: no live row: if the commit under test changed it, %s in that "
                       "commit (a worse verdict is a regression: fix the code)" % (i, regen))
            continue
        if all(w.get(k) == g.get(k) for k in COMPARED):
            continue
        rw, rg = RANK.get(w.get("verdict"), -1), RANK.get(g.get("verdict"), -1)
        cw, cg = set(w.get("checks") or []), set(g.get("checks") or [])
        if rg > rw or (rg == rw and cg < cw):
            out.append("%s improved from %s (%s) to %s (%s): delete the fixed item's rows "
                       "from scripts/corpus/ledger.tsv, run python3 scripts/corpus/ledger.py "
                       "(D-33-05.i), and %s in the fixing commit"
                       % (i, w.get("verdict"), ", ".join(w.get("checks") or []),
                          g.get("verdict"), ", ".join(g.get("checks") or []), regen))
            continue
        k = next(k for k in COMPARED if w.get(k) != g.get(k))
        out.append("%s: %s was %s now %s: if the commit under test changed it, %s in that "
                   "commit (a worse verdict is a regression: fix the code)"
                   % (i, k, _fmt(w.get(k)), _fmt(g.get(k)), regen))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--select", required=True, metavar="RUN_DIR")
    ap.add_argument("--rules", default=verdict.RULES_PATH)
    a = ap.parse_args(argv)
    with open(a.rules, encoding="utf-8") as fh:
        rules = json.load(fh)
    chosen, skipped = _choose(a.select, rules)
    for t, r in sorted(chosen, key=lambda c: c[1]["id"]):
        print("%s  # %s: %s" % (r["id"], t, r["cmd"][:60]))
    print("skipped: %s" % (" ".join(skipped) if skipped else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
