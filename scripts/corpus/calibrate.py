"""Measure the verdict's thresholds on the calibration set (WP-33 33-05).

    python3 scripts/corpus/calibrate.py --prepare <run>
    python3 scripts/corpus/calibrate.py --write <run>

scripts/corpus/calibration.tsv lists 32 examples `id<TAB>label<TAB>mutation`:
Same and Close rows are corpus examples as they are; each Differs row is a
Same example whose dash command gets one option more (the mutation).
--prepare appends the mutated copies (`cal-<id>-<n>`) to <run>/examples.jsonl
before the twoway and dash runners run; --write judges every row and writes
test/fixtures/corpus_verdict_rules.json: the tolerances and image-score
thresholds measured from the rows (D-33-05.d), recorded, never gating
(DECISIONS A-4), and each row's measurements.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import json
import math
import subprocess
import time

from scripts.corpus import dash_run, verdict
from scripts.corpus import ledger as ledger_mod

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TABLE_PATH = os.path.join(REPO, "scripts", "corpus", "calibration.tsv")
#: The fixture this script writes.
OUT_PATH = os.path.join(REPO, "test", "fixtures", "corpus_verdict_rules.json")
SOURCE = "scripts/corpus/calibrate.py"

LABELS = ("Same", "Close", "Differs")
TICK_REL = 1e-6
EXTENT_REL = 0.01
ASPECT_MAX = 0.05
#: D49: text size and marker/line sizes agree within this share of
#: twoway's; the plot region's insets within this share of the canvas.
TEXT_REL = 0.05
SIZE_REL = 0.05
#: D56: line widths closer than half a pixel of a 720-pixel-wide picture
#: (as a share of the canvas width) look the same.
LINE_ABS = 0.0007
INSET_ABS = 0.005
#: A colour farther than this from every colour on the other side is a
#: colour difference, never agreement (an eighth of a channel's range).
COLOUR_BOUND = 32
STEP = 0.005
#: D56: the checks that can make a pair Close, never Differs, by themselves.
CLOSE_ONLY = ["line_width", "margins", "marker_size", "text_size"]
#: D56: a "slight" colour shift keeps the hue family (hues within HUE_DEG
#: degrees, or two greys below GREY_SAT saturation) and moves lightness by at
#: most LIGHT; the calibration's colour-mutated Differs rows must exceed it.
COLOUR_SLIGHT = {"hue_deg": 30, "light": 0.2, "grey_sat": 0.15}


def _floor(x):
    return round(math.floor(x / STEP + 1e-9) * STEP, 3)


def _ceil(x):
    return round(math.ceil(x / STEP - 1e-9) * STEP, 3)


def read_table(path=TABLE_PATH):
    """The calibration rows {id, label, mutation, case}; case is the judged id."""
    rows, n = [], 0
    with open(path, encoding="utf-8") as fh:
        for k, raw in enumerate(fh, 1):
            ln = raw.rstrip("\n")
            if not ln.strip() or ln.startswith("#"):
                continue
            parts = ln.split("\t")
            if len(parts) != 3 or parts[1] not in LABELS:
                raise ValueError("%s line %d: expected id<TAB>label<TAB>mutation"
                                 % (os.path.basename(path), k))
            mut = parts[2].strip()
            mut = None if mut in ("", "-") else mut
            # A mutation makes a Differs row; a corpus pair the maintainer
            # labelled Differs (D58) needs none.
            if mut is not None and parts[1] != "Differs":
                raise ValueError("%s line %d: only a Differs row has a mutation"
                                 % (os.path.basename(path), k))
            case = parts[0]
            if mut is not None:
                n += 1
                case = "cal-%s-%d" % (parts[0], n)
            rows.append({"id": parts[0], "label": parts[1], "mutation": mut, "case": case})
    return rows


def mutate(cmd, mutation):
    """cmd with the mutation appended as its last option (33-04's comma rule)."""
    marked = dash_run.with_saving(cmd, "\x00")
    return marked.replace('saving("\x00", replace)', mutation)


def _jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def prepare(run_dir, table_path=TABLE_PATH):
    """Append each Differs row's mutated copy to <run_dir>/examples.jsonl; the count."""
    path = os.path.join(run_dir, "examples.jsonl")
    examples = _jsonl(path)
    have = {e["id"]: e for e in examples}
    added = 0
    with open(path, "a", encoding="utf-8") as fh:
        for r in read_table(table_path):
            if r["mutation"] is None or r["case"] in have:
                continue
            if r["id"] not in have:
                raise KeyError("calibration id %s is not in %s" % (r["id"], path))
            e = dict(have[r["id"]])
            e["id"] = r["case"]
            e["dash_cmd"] = mutate(e["dash_cmd"], r["mutation"])
            e["mutation"] = r["mutation"]  # the one difference the runners allow (D57)
            e["duplicates"] = []
            fh.write(json.dumps(e) + "\n")
            added += 1
    return added


def thresholds(rows):
    """The rules measured from calibration rows (D-33-05.d); never raises.

    Each row: label, ssim (or None), aspect_diff (or None), checks (the
    checks outside tolerance at the base tolerances) and colour_dists (each
    readable colour's distance to its nearest colour on the other side).
    """
    same = [r for r in rows if r.get("label") == "Same"]
    aspects = [abs(r["aspect_diff"]) for r in same if r.get("aspect_diff") is not None]
    aspect_abs = min(ASPECT_MAX, _ceil(max(aspects))) if aspects else ASPECT_MAX
    clean = [r for r in same if r.get("ssim") is not None
             and set(r.get("checks") or []) - {"colours"} <= {"frame_aspect"}]
    dists = [d for r in clean for d in (r.get("colour_dists") or []) if d <= COLOUR_BOUND]
    if dists:
        colour_tol = int(math.ceil(max(dists) - 1e-9))
    else:
        colour_tol = 0
        print("calibrate: colour_tol 0: no clean Same row has a readable colour within "
              "%d of the other side" % COLOUR_BOUND)
    if len(clean) >= 3:
        # The lowest clean Same score (ruling D47): no clean pair moves to Close.
        t_same = min(r["ssim"] for r in clean)
    else:
        t_same = None
        print("calibrate: T_same null: %d clean Same rows with an image score, fewer than 3"
              % len(clean))
    close = [r["ssim"] for r in rows if r.get("label") == "Close" and r.get("ssim") is not None]
    t_close = _floor(min(close)) if close else None
    # D56: the plot region shapes the Close rows show are Close at most.
    shapes = [abs(r["aspect_diff"]) for r in rows if r.get("label") == "Close"
              and r.get("aspect_diff") is not None]
    aspect_close = _ceil(max(shapes)) if shapes else aspect_abs
    return {"T_same": t_same, "T_close": t_close, "tick_rel": TICK_REL,
            "extent_rel": EXTENT_REL, "aspect_abs": aspect_abs, "colour_tol": colour_tol,
            "text_rel": TEXT_REL, "inset_abs": INSET_ABS, "size_rel": SIZE_REL,
            "aspect_close": max(aspect_close, aspect_abs), "close_only": list(CLOSE_ONLY),
            "line_abs": LINE_ABS,
            "colour_slight": dict(COLOUR_SLIGHT)}


def _git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip() or None


def _measure(run_dir, table, rules, probe, ledger=(), states=None):
    examples = {e["id"]: e for e in _jsonl(os.path.join(run_dir, "examples.jsonl"))}
    tws = {r["id"]: r for r in _jsonl(os.path.join(run_dir, "twoway.jsonl"))}
    das = {r["id"]: r for r in _jsonl(os.path.join(run_dir, "dash.jsonl"))}
    out = []
    for t in table:
        e, tw, da = examples[t["case"]], tws.get(t["case"]), das.get(t["case"])
        # D56: each row's verdict is the whole engine's, its ledger included.
        row = verdict.judge(e, tw, da, run_dir, rules, list(ledger), states or {}, probe=probe)
        aspect, dists = None, []
        if tw and da and tw.get("rc") == 0 and da.get("rc") == 0 and tw.get("svg") \
                and da.get("view"):
            g_tw = verdict.twoway_geometry(os.path.join(run_dir, tw["svg"]))
            with open(os.path.join(run_dir, da["view"]), encoding="utf-8") as fh:
                g_da = verdict.dash_geometry(json.load(fh), os.path.join(run_dir, da["svg"]))
            if g_tw["frame_aspect"] is not None and g_da["frame_aspect"] is not None:
                aspect = round(g_da["frame_aspect"] - g_tw["frame_aspect"], 4)
            dists = verdict.colour_distances(g_tw["colours"]["set"], g_da["colours"]["set"])
        out.append({"id": t["case"], "label": t["label"], "ssim": row["ssim"],
                    "aspect_diff": aspect, "colour_dists": dists, "verdict": row["verdict"],
                    "checks": [c for c in row["checks"] if c != "image"]})
    return out


def write_rules(run_dir, out_path=OUT_PATH, table_path=TABLE_PATH):
    """Judge every calibration row of run_dir and write the rules fixture."""
    table = read_table(table_path)
    base = {"T_same": None, "T_close": None, "tick_rel": TICK_REL, "extent_rel": EXTENT_REL,
            "aspect_abs": ASPECT_MAX, "colour_tol": 0, "text_rel": TEXT_REL,
            "inset_abs": INSET_ABS, "size_rel": SIZE_REL, "aspect_close": None,
            "line_abs": LINE_ABS,
            "close_only": list(CLOSE_ONLY), "colour_slight": dict(COLOUR_SLIGHT)}
    try:
        probe = verdict._open_probe(run_dir)
    except Exception:  # noqa: BLE001 -- no Chrome: no image score
        probe = None
    try:
        p = probe if probe is not None else verdict._NO_PROBE
        first = _measure(run_dir, table, base, p)
        rules = thresholds(first)
        final = _measure(run_dir, table, dict(rules), p, verdict.load_ledger(verdict.LEDGER_PATH),
                         ledger_mod.gaps4_states(os.path.join(REPO, "GAPS4.md")))
    finally:
        if probe is not None:
            probe.__exit__(None, None, None)
    with open(os.path.join(run_dir, "stata_version.txt"), encoding="utf-8") as fh:
        version = fh.read().strip()
    day = time.strftime("%d %b %Y", time.localtime(
        os.path.getmtime(os.path.join(run_dir, "twoway.jsonl"))))
    doc = {"_meta": {"born_date": day, "dash_commit": _git_head(), "extracted": day,
                     "source": SOURCE, "stata_version": version,
                     "table": "scripts/corpus/calibration.tsv"}}
    doc.update(rules)
    doc["calibration"] = [{"id": r["id"], "label": r["label"], "ssim": r["ssim"],
                           "aspect_diff": r["aspect_diff"],
                           "colour_dist": max(r["colour_dists"]) if r["colour_dists"] else None,
                           "checks_differing": r["checks"], "verdict": r.get("verdict")}
                          for r in final]
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prepare", metavar="RUN_DIR")
    g.add_argument("--write", metavar="RUN_DIR")
    ap.add_argument("--table", default=TABLE_PATH, help=argparse.SUPPRESS)
    ap.add_argument("--out", default=OUT_PATH, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.prepare:
        print("calibrate: %d mutated examples added" % prepare(a.prepare, a.table))
        return 0
    d = write_rules(a.write, a.out, a.table)
    wrong = [c["id"] for c in d["calibration"] if c["verdict"] != c["label"]]
    print("calibrate: T_same %s, T_close %s, aspect_abs %s, aspect_close %s, extent_rel %s, "
          "colour_tol %s on %d rows (%d judged against their label%s) -> "
          "test/fixtures/corpus_verdict_rules.json"
          % (d["T_same"], d["T_close"], d["aspect_abs"], d["aspect_close"], d["extent_rel"],
             d["colour_tol"], len(d["calibration"]), len(wrong),
             (": " + ", ".join(wrong)) if wrong else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
