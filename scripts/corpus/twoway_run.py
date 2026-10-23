"""Run every corpus example under twoway and record its picture (WP-33 33-03).

    python3 scripts/corpus/twoway_run.py --run <run> [--jobs N] [--timeout S] [--only id,id]

Reads <run>/examples.jsonl, writes one do-file per chunk of examples
(<run>/tw/c<k>/twoway.do), runs each through scripts/stata_slot.sh (at most
--jobs at once), and writes <run>/twoway.jsonl -- per example its return
code, the first line twoway printed, the SVG twoway exported (moved to
<run>/twoway/<id>.svg, unedited) and the size twoway drew it at -- plus
<run>/stata_version.txt.  An example whose dataset the offline cache lacks
is run in no chunk; each such dataset is named once (DECISIONS A-26).  An
example twoway refuses joins <run>/extract_dropped.tsv with the reason
"twoway refuses (rc N)" and the later stages skip it (DECISIONS D52).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import json
import re
import shutil
import signal
import subprocess
import time

from scripts.corpus import datasets

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLOT_CMD = ["sh", os.path.join(REPO, "scripts", "stata_slot.sh")]

ROW_KEYS = ("id", "rc", "first_line", "setup_rc", "export_rc", "svg", "width_in",
            "height_in", "skip")

_MARK_RE = re.compile(r"^##(VERSION|BEGIN|SETUP|RC|EXPORT)\s+(\S+)(?:\s+(-?\d+))?\s*$")
_ECHO_RE = re.compile(r"^(?:\. |\.$|> |\s*\d+\. )")
_CONTOUR_RE = re.compile(r"\bcontour(?:line)?\b")
_SVG_ROOT_RE = re.compile(r"<svg\b[^>]*>", re.S)


def _row(i, **kw):
    r = dict.fromkeys(ROW_KEYS)
    r["id"] = i
    r.update(kw)
    return r


INVALID = "invalid pair: the commands differ beyond twoway/dash (D57)"


def invalid_pairs(examples):
    """D57: {id: reason} of every example whose twoway and dash commands differ
    by more than the leading word; neither runner runs them."""
    from scripts.corpus import calibrate, extract
    out = {}
    for e in examples:
        dash_cmd = e.get("dash_cmd") or ""
        if e.get("mutation"):
            # A calibration copy: its twin plus the recorded mutation, nothing else.
            twin = extract.to_dash(e["cmd"])
            if calibrate.mutate(twin, e["mutation"]) == dash_cmd:
                dash_cmd = twin
        if extract.twin_mismatch(e["cmd"], dash_cmd):
            out[e["id"]] = INVALID
    return out


def do_text(examples, out_dir, cache):
    """The do-file that runs one chunk of examples between ## markers; refuses
    (ValueError) an example whose pair differs beyond twoway/dash (D57)."""
    bad = invalid_pairs(examples)
    if bad:
        raise ValueError("%s: %s" % (INVALID, ", ".join(sorted(bad))))
    out = ["version 19", "set more off", "set linesize 255",
           'display "##VERSION " c(stata_version)']
    for e in examples:
        i = e["id"]
        setup = datasets.rewrite_setup(e.get("setup") or [], cache)[0]
        out += ['display "##BEGIN %s"' % i, "clear", "capture graph drop _all",
                "capture noisily {"]
        out += list(setup)
        out += ["}", 'display "##SETUP %s " _rc' % i, "if _rc == 0 {",
                "capture noisily %s" % e["cmd"],
                'display "##RC %s " _rc' % i,
                'if _rc == 0 capture noisily graph export "%s/%s.svg", as(svg) replace'
                % (out_dir, i),
                'display "##EXPORT %s " _rc' % i, "}"]
    return "\n".join(out) + "\n"


def parse_log(text):
    """id -> {setup_rc, rc, first_line, export_rc} of each reported example, and "_version".

    An example is reported once its setup failed or its ##RC line printed.
    The first line is the first non-blank, non-echo, non-marker line after
    ##SETUP and before ##RC (D-33-03.a).
    """
    out, cur, version = {}, None, None
    st = {}
    for raw in text.splitlines():
        ln = raw.rstrip()
        m = _MARK_RE.match(ln)
        if m:
            kind, i, n = m.group(1), m.group(2), m.group(3)
            if kind == "VERSION":
                version = version or i
            elif kind == "BEGIN":
                cur = i
                st[i] = {"setup_rc": None, "rc": None, "first_line": None,
                         "export_rc": None, "_open": False}
            elif i in st and n is not None:
                e = st[i]
                if kind == "SETUP":
                    e["setup_rc"] = int(n)
                    e["_open"] = int(n) == 0
                elif kind == "RC":
                    e["rc"] = int(n)
                    e["_open"] = False
                elif kind == "EXPORT":
                    e["export_rc"] = int(n) if e["rc"] == 0 else None
            continue
        if cur in st:
            e = st[cur]
            if e["_open"] and e["first_line"] is None and ln.strip() \
                    and not _ECHO_RE.match(ln):
                e["first_line"] = ln
    for i, e in st.items():
        if e["rc"] is not None or (e["setup_rc"] not in (None, 0)):
            del e["_open"]
            out[i] = e
    out["_version"] = version
    return out


def svg_size(path):
    """(width, height) in inches from the root <svg>'s width/height, or None."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        m = _SVG_ROOT_RE.search(fh.read(65536))
    if not m:
        return None
    dims = []
    for key in ("width", "height"):
        a = re.search(r'\s%s="\s*([0-9.]+)\s*(in|px)\s*"' % key, m.group(0))
        if not a:
            return None
        v = float(a.group(1))
        dims.append(v if a.group(2) == "in" else v / 96.0)
    return tuple(dims)


def _is_contour(e):
    return e.get("plottype") in ("contour", "contourline") or \
        bool(_CONTOUR_RE.search(e.get("cmd", "")))


def chunks(examples, size=25):
    """Chunks of at most size examples in id order; then each contour example alone."""
    out, cur, alone = [], [], []
    for e in sorted(examples, key=lambda r: r["id"]):
        if _is_contour(e):
            alone.append([e])
            continue
        cur.append(e)
        if len(cur) == size:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out + alone


def missing_datasets(examples, cache):
    """Each dataset the cache lacks -> the sorted ids of the examples that need it."""
    out = {}
    for e in examples:
        for name in datasets.rewrite_setup(e.get("setup") or [], cache)[1]:
            out.setdefault(name, []).append(e["id"])
    return {k: sorted(out[k]) for k in sorted(out)}


def skip_rows(examples, cache):
    """The twoway.jsonl rows of the examples whose dataset the cache lacks, by id."""
    rows = []
    for e in sorted(examples, key=lambda r: r["id"]):
        miss = datasets.rewrite_setup(e.get("setup") or [], cache)[1]
        if miss:
            rows.append(_row(e["id"], skip="dataset %s not cached" % miss[0]))
    return rows


def _hide_paths(s, run_dir):
    if s is None:
        return None
    pairs = []
    for path, tag in ((datasets.cache_dir(), "<cache>"), (run_dir, "<run>")):
        for p in {path.rstrip("/"), os.path.realpath(path)}:
            if p:
                pairs.append((p, tag))
    for p, tag in sorted(pairs, key=lambda t: -len(t[0])):
        s = s.replace(p, tag)
    return s


def records(examples, parsed, svg_dir, run_dir, unreported="chunk ended early"):
    """The twoway.jsonl rows of one parsed log; moves each SVG to <run_dir>/twoway/."""
    rows = []
    for e in examples:
        i = e["id"]
        p = parsed.get(i)
        if not isinstance(p, dict):
            rows.append(_row(i, skip=unreported))
            continue
        r = _row(i, rc=p["rc"], first_line=_hide_paths(p["first_line"], run_dir),
                 setup_rc=p["setup_rc"], export_rc=p["export_rc"])
        if p["rc"] is None:
            r["skip"] = "setup rc %d" % p["setup_rc"]
        src = os.path.join(svg_dir, i + ".svg")
        if p["rc"] == 0 and p["export_rc"] == 0 and os.path.exists(src):
            dst_dir = os.path.join(run_dir, "twoway")
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, i + ".svg")
            shutil.move(src, dst)
            r["svg"] = "twoway/%s.svg" % i
            size = svg_size(dst)
            if size:
                r["width_in"], r["height_in"] = size
        rows.append(r)
    return rows


def _read(path):
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _stop(p):
    try:
        os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        p.wait()


def run(run_dir, jobs=3, timeout=1800, only=None):
    """Run the examples of <run_dir>/examples.jsonl under twoway; counts of the rows."""
    with open(os.path.join(run_dir, "examples.jsonl"), encoding="utf-8") as fh:
        examples = [json.loads(ln) for ln in fh if ln.strip()]
    if only is not None:
        examples = [e for e in examples if e["id"] in only]
    cache = datasets.cache_dir()
    miss = missing_datasets(examples, cache)
    for name in miss:
        print("skip: dataset %s not cached" % name)
    rows = skip_rows(examples, cache)
    bad = invalid_pairs(examples)
    rows += [_row(i, skip=why) for i, why in sorted(bad.items())
             if i not in {r["id"] for r in rows}]
    aside = {r["id"] for r in rows}
    todo = chunks([e for e in examples if e["id"] not in aside])
    pending = []
    for k, ch in enumerate(todo, 1):
        d = os.path.join(run_dir, "tw", "c%d" % k)
        os.makedirs(os.path.join(d, "svg"), exist_ok=True)
        do = os.path.join(d, "twoway.do")
        with open(do, "w", encoding="utf-8") as fh:
            fh.write(do_text(ch, os.path.join(d, "svg"), cache))
        pending.append((k, ch, d, do))
    versions, active = {}, []
    while pending or active:
        while pending and len(active) < max(1, jobs):
            k, ch, d, do = pending.pop(0)
            p = subprocess.Popen(SLOT_CMD + [d, do], start_new_session=True)
            active.append((k, ch, d, p, time.monotonic()))
        time.sleep(0.1)
        still = []
        for k, ch, d, p, t0 in active:
            status = p.poll()
            if status is None and time.monotonic() - t0 > timeout:
                _stop(p)
                print("corpus: chunk %d timed out; if no stata-mp process is left, "
                      "remove a stale /tmp/dash-stata-slot-<n>.d" % k)
                why = "timeout"
            elif status is None:
                still.append((k, ch, d, p, t0))
                continue
            else:
                why = "chunk ended early (rc %d)" % status
            parsed = parse_log(_read(os.path.join(d, "twoway.log")))
            versions[k] = parsed.get("_version")
            rows += records(ch, parsed, os.path.join(d, "svg"), run_dir, unreported=why)
        active = still
    if versions.get(1):
        with open(os.path.join(run_dir, "stata_version.txt"), "w", encoding="utf-8") as fh:
            fh.write(versions[1] + "\n")
    rows.sort(key=lambda r: r["id"])
    with open(os.path.join(run_dir, "twoway.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({k: r[k] for k in ROW_KEYS}) + "\n")
    drop_refused(run_dir, examples, rows)
    return {"rc0": sum(r["rc"] == 0 for r in rows),
            "refused": sum(r["rc"] not in (None, 0) for r in rows),
            "skipped": sum(r["skip"] is not None for r in rows)}


REFUSES = "twoway refuses (rc %d)"


def drop_refused(run_dir, examples, rows):
    """List each example twoway refuses in <run_dir>/extract_dropped.tsv (D52).

    The corpus compares only what twoway accepts: such an example is dropped
    with the reason "twoway refuses (rc N)", and the later stages skip it.
    The list's earlier refusal rows for these examples are replaced, so a
    rerun never repeats one.  Returns the dropped ids."""
    rc = {r["id"]: r.get("rc") for r in rows if not r.get("skip")}
    refused = [e for e in sorted(examples, key=lambda e: e["id"])
               if rc.get(e["id"]) not in (0, None)]
    path = os.path.join(run_dir, "extract_dropped.tsv")
    lines = ["source\twhere\treason\tcmd"]
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            lines = [ln.rstrip("\n") for ln in fh if ln.strip()] or lines
    def key(where, cmd):
        return where + "\t" + cmd
    mine = {key("%s:%s" % (e.get("file"), e.get("line")), e["cmd"]) for e in examples}
    kept = [ln for ln in lines[1:]
            if not (ln.split("\t")[2:3] and ln.split("\t")[2].startswith("twoway refuses (")
                    and key(ln.split("\t")[1], "\t".join(ln.split("\t")[3:])) in mine)]
    for e in refused:
        kept.append("\t".join(str(x).replace("\t", " ") for x in (
            e.get("source"), "%s:%s" % (e.get("file"), e.get("line")),
            REFUSES % rc[e["id"]], e["cmd"])))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join([lines[0]] + kept) + "\n")
    return [e["id"] for e in refused]


def refused_ids(run_dir):
    """The ids of <run_dir>/twoway.jsonl's examples twoway refused (D52)."""
    path = os.path.join(run_dir, "twoway.jsonl")
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(ln) for ln in fh if ln.strip()]
    return {r["id"] for r in rows if not r.get("skip") and r.get("rc") not in (0, None)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, metavar="RUN_DIR")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=1800)
    ap.add_argument("--only", default=None, metavar="ID,ID")
    a = ap.parse_args(argv)
    only = None if a.only is None else {s.strip() for s in a.only.split(",") if s.strip()}
    c = run(a.run, jobs=a.jobs, timeout=a.timeout, only=only)
    print("corpus: twoway rc0 %d, refused %d, skipped %d" % (c["rc0"], c["refused"], c["skipped"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
