*! extract_by_grid_truth.do
*! WP-30 section 48 (P1.15b): ground truth for how twoway lays out, sizes
*! and refuses a by() graph's grid -- rows(), cols(), holes(), colfirst,
*! compact, style(compact), iscale(), imargin() -- for
*! test/fixtures/by_grid_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash named rows(), holes(), colfirst, compact, iscale() and imargin() as
*! ignored, drew every panel at the plain graph's size in a ceil(sqrt(n))
*! grid, gave each panel the whole xsize()/ysize() ratio and accepted every
*! by() word twoway refuses.  bygraph_g.class places the panels
*! (full_n, set_rows_cols, set_placement), scales them and refuses its
*! bad arguments in three parse stages.
*!
*! Output: test/fixtures/by_grid_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_grid_truth.do
*!
*! METHOD
*!
*! `bg kind id "options"' reloads the data and runs
*! `twoway scatter mpg weight, <options> name(Graph, replace)' under a text
*! log.  A drawn graph is exported to SVG (a draw-time refusal is the
*! export's rc); its rows and columns (.Graph.rows, .Graph.cols), each
*! panel's label and the panel margin (.Graph.style.indiv_margin) are
*! written to a record file.  The trailing python: block reads files only
*! (never calls Stata; a backtick is spelled \x60): panel cells from the
*! label texts' positions in the SVG, the size multiplier from the marker
*! label font, the scheme files' margin by_indiv through their #include
*! chains, and the by() option names declared in bygraph_g.class and
*! graph_g.class.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_by_grid_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zr_rc' | _rc {
    local _zr_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_by_grid_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global BG_REPO "`repo'"
global BG_OUT  "`repo'/test/fixtures/by_grid_truth.json"
local scratch "`c(tmpdir)'dash_by_grid_probe"
capture mkdir "`scratch'"
global BG_WORK "`scratch'"
global BG_REC  "`scratch'/by_grid_records.txt"
global BG_BASE "`c(sysdir_base)'"

global BG_SVER = c(stata_version)
global BG_BORN = c(born_date)
global BG_DATE = c(current_date) + " " + c(current_time)

tempfile bggitrev
quietly shell git -C "${BG_REPO}" rev-parse HEAD > "`bggitrev'"
tempname bggfh
file open `bggfh' using "`bggitrev'", read text
file read `bggfh' bggitline
file close `bggfh'
global BG_COMMIT = trim(`"`bggitline'"')
capture assert ustrregexm(`"${BG_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_by_grid_truth.do: git rev-parse HEAD did not print a 40-character commit: ${BG_COMMIT}"
    exit 498
}

sysuse auto, clear
generate g10 = mod(_n, 10)
generate g3 = mod(_n, 3)
keep mpg weight foreign rep78 g10 g3
quietly save "${BG_WORK}/bg.dta", replace

// ---------------------------------------------------------------------------
// bg kind id "options": one probe.  kind is grid, sizes, refusals or
// accepted; the record line carries it so the python block files it.
// ---------------------------------------------------------------------------
capture program drop bg
program define bg
    version 19
    args kind id opts
    use "${BG_WORK}/bg.dta", clear
    quietly log using "${BG_WORK}/`id'.log", text replace name(bglog)
    capture noisily twoway scatter mpg weight, `opts' name(Graph, replace)
    local rc = _rc
    local xrc = 0
    if !`rc' {
        capture noisily graph export "${BG_WORK}/`id'.svg", name(Graph) replace
        local xrc = _rc
    }
    quietly log close bglog
    file write bgrec "R|`kind'|`id'|`rc'|`xrc'|" `"`opts'"' _n
    if `rc' | `xrc' exit
    capture local np = `.Graph.graphs.arrnels'
    if _rc | "`np'" == "" exit
    file write bgrec "G|`id'|`np'|`.Graph.rows'|`.Graph.cols'|" ///
        "`.Graph.style.indiv_margin.left'|`.Graph.style.indiv_margin.right'|" ///
        "`.Graph.style.indiv_margin.bottom'|`.Graph.style.indiv_margin.top'" _n
    forvalues k = 1/`np' {
        file write bgrec "P|`id'|`k'|" `"`.Graph.graphs[`k'].subtitle.text[1]'"' _n
    }
end

file open bgrec using "${BG_REC}", write text replace

// grid (s2color)
set scheme s2color
local i 0
foreach o in "by(foreign)" "by(rep78)" "by(rep78, total)" "by(rep78, rows(1))" ///
    "by(rep78, cols(1))" "by(rep78, holes(3) total)" "by(rep78, colfirst total)" ///
    "by(rep78, holes(1 2 3))" "by(foreign, cols(5))" "by(rep78, holes(9))" ///
    "by(rep78, rows(2) colfirst holes(1))" "by(rep78, cols(3) holes(2) colfirst)" ///
    "by(foreign, total cols(5))" "by(rep78, r(2))" "by(rep78, c(1) colf)" ///
    "by(rep78, hol(2 2 9))" "by(g10)" "by(g3, rows(5))" {
    local ++i
    bg grid grid`i' "`o'"
}

// sizes (three schemes)
foreach s in s2color stcolor economist {
    local i 0
    foreach o in "" "by(foreign)" "by(g10)" "by(foreign, iscale(.5))" ///
        "by(foreign, iscale(*2))" "by(foreign, iscale(0))" "by(foreign, iscale(abc))" ///
        "by(foreign, compact)" "by(foreign, style(compact))" "by(foreign, imargin(large))" ///
        "by(foreign, imargin(1 2 3 4))" "by(foreign, imargin(l=5))" ///
        "by(foreign, imargin(bogus))" "by(foreign, imargin(zero) compact)" ///
        "by(foreign) xsize(12) ysize(3)" "xsize(12) ysize(3)" {
        local ++i
        bg sizes `s'_`i' `"mlabel(rep78) `o' scheme(`s')"'
    }
}
set scheme s2color

// refusals
local i 0
foreach a in "rows(0) cols(0)" "cols(0) rows(2)" "rows(1.5)" "rows(2 3)" "rows(abc)" ///
    "rows(2) cols(2) YRESCALE" "rows(1) cols(1) holes(0)" "YRESCALE holes(0)" ///
    "holes(1.5)" "holes(abc)" "holes(1/301)" "rows(2) rows(3)" "rows(0) rows(2)" ///
    "cols(2) cols(0)" "colfirst colfirst rows(0)" ///
    "holes(1) holes(2) style(compact) style(default)" ///
    "style(compact) style(default) YRESCALE" `"TITLE("x") bogus"' ///
    `"bogus TITLE("x")"' "COMPACT" "Rows(2)" "total TOTAL" "compact compact" ///
    "iscale(.5) iscale(2)" "imargin(small) imargin(large)" "yrescale yrescale" ///
    "iscale(-1)" "iscale(*-1)" "iscale(1e5)" "iscale(-1) rows(0)" "iscale(-1) YRESCALE" ///
    "iscale(1e4)" "iscale(0)" "iscale(100)" "iscale(abc)" "iscale(.)" "iscale(1 2)" ///
    "imargin(bogus)" "rows()" "holes()" "iscale()" "holes(301)" "r(2)" "c(1) colf" ///
    "hol(2 2 9)" "imargin(-1)" "imargin(1 2 3 4)" "imargin(l=5)" "cols(0) rows(0)" ///
    "ixt" "legend(off) legend(on)" "clegend(on) clegend(off)" `"title("a") title("b")"' ///
    "graphregion(color(white)) graphregion(color(red))" "t1title(a) t1title(b)" ///
    "spacers(ring(1)) spacers(ring(2))" "bgcolor(white) bgcolor(red)" "TOTAL rows(0)" ///
    "bogus" "bogus rows(0)" "nolegend" "cols(500)" "missing missing" "total total" ///
    "rows(2) cols()" {
    local ++i
    bg refusals ref`i' `"by(foreign, `a')"'
}

// accepted: every by() word's minimum spelling and the one letter shorter
local i 0
foreach a in "total" "tot" "to" "missing" "miss" "mis" "rows(2)" "r(2)" ///
    "colfirst" "colf" "col" "cols(2)" "c(2)" "scale(1)" "scal(1)" "iscale(.5)" "iscal(.5)" ///
    "legend(off)" "leg(off)" "le(off)" "legloc(6)" "leglo(6)" "plegend(off)" "pleg(off)" "ple(off)" ///
    "plegloc(6)" "pleglo(6)" "clegend(on)" "cleg(on)" "cle(on)" "clegloc(3)" "cleglo(3)" ///
    "compact" "com" "co" "style(compact)" "styl(compact)" "norescale" "nor" "no" ///
    "rescale" "r" "noxrescale" "noxr" "noyrescale" "noyr" "xrescale" "xr" "x" "yrescale" "yr" "y" ///
    "holes(3)" "hol(3)" "ho(3)" "noedgelabel" "noedge" "noed" "edgelabel" "edge" "edg" ///
    "noixaxes" "noix" "noiyaxes" "noiy" "ixaxes" "ix" "iyaxes" "iy" "i" ///
    "noxtitles" "noxt" "noxtitle" "xtitles" "xt" "noytitles" "noyt" "ytitles" "yt" ///
    "noixlabels" "noixl" "noiylabels" "noiyl" "ixlabels" "ixl" "iylabels" "iyl" ///
    "noixticks" "noixt" "noiyticks" "noiyt" "ixticks" "ixt" "iyticks" "iyt" ///
    "noixtitles" "noixti" "noixtitle" "noiytitles" "noiyti" "ixtitles" "ixti" "iytitles" "iyti" ///
    "noindividual" "noind" "noin" "individual" "ind" "in" "ilegends" "ileg" "ile" ///
    "imargin(small)" "im(small)" "noshrink" "noshr" "noshrin" "noishrink" "noishr" ///
    "nooverallshrink" "nooverallshr" "shrink" "shr" "sh" "ishrink" "ishr" "ish" ///
    "overallshrink" "overallshr" "subtitleformat(%9s)" "subtitleforma(%9s)" ///
    "graphregion(color(white))" "graphr(color(white))" "graph(color(white))" ///
    "plotregion(margin(zero))" "plotr(margin(zero))" "plot(margin(zero))" ///
    `"r1title("a")"' `"r1("a")"' `"r2title("a")"' `"r2("a")"' `"l1title("a")"' `"l1("a")"' ///
    `"l2title("a")"' `"l2("a")"' `"t1title("a")"' `"t1("a")"' `"t2title("a")"' `"t2("a")"' ///
    `"b1title("a")"' `"b1("a")"' `"b2title("a")"' `"b2("a")"' `"note("a")"' `"not("a")"' ///
    `"caption("a")"' `"cap("a")"' `"ca("a")"' `"subtitle("a")"' `"sub("a")"' `"su("a")"' ///
    `"title("a")"' `"t("a")"' "spacers(ring(1))" "space(ring(1))" "spac(ring(1))" ///
    "bgcolor(white)" "bgc(white)" "bg(white)" {
    local ++i
    bg accepted acc`i' `"by(foreign, `a')"'
}
file close bgrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("BG_REPO")
WORK = Macro.getGlobal("BG_WORK")
BASE = Macro.getGlobal("BG_BASE").rstrip("/")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth
import extract_scheme_truth as est

_HEAD = re.compile(r"^\s*(name|log|log type|opened on|closed on):")
_NUM = re.compile(r"^[-+]?[0-9.,]+$")


def log_of(pid):
    try:
        with open(os.path.join(WORK, pid + ".log"), encoding="utf-8",
                  errors="replace") as fh:
            lines = [l.rstrip() for l in fh]
    except OSError:
        return [], ""
    keep = [l for l in lines if l.strip() and not _HEAD.match(l)
            and not set(l.strip()) <= set("-")
            and not l.lstrip().startswith(". ")
            and not re.match(r"^r\(\d+\);$", l.strip())]
    notes = [l.strip() for l in keep if l.strip().startswith("(note:")]
    errs = [l.strip() for l in keep if not l.strip().startswith("(note:")
            and not l.strip().startswith("file ")
            and not l.strip().startswith("(file ")]
    return notes, (errs[0] if errs else "")


recs, order, kinds = {}, [], {}
with open(Macro.getGlobal("BG_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "R":
            kind, pid, rc, xrc = f[1], f[2], int(f[3]), int(f[4])
            notes, msg = log_of(pid)
            recs[pid] = {"options": "|".join(f[5:]), "rc": rc or xrc,
                         "at_draw": bool(xrc and not rc),
                         "message": msg if (rc or xrc) else "",
                         "notes": notes}
            kinds[pid] = kind
            order.append(pid)
        elif f[0] == "G":
            p = recs[f[1]]
            p["n"] = int(f[2])
            p["rows"] = int(f[3])
            p["cols"] = int(f[4])
            p["indiv_margin"] = [float(v) if v not in ("", ".") else None
                                 for v in f[5:9]]
            p["labels"] = []
        elif f[0] == "P":
            recs[f[1]]["labels"].append(f[3])


def cells_of(pid, labels):
    doc = svg_truth.svg_document(os.path.join(WORK, pid + ".svg"))
    found = {}
    for lab in labels:
        hits = [t for t in doc["texts"] if t["text"] == lab]
        if not hits:
            return None
        # the panel label is the largest text with that string
        h = max(hits, key=lambda t: (t["size"] or 0, -t["y"]))
        found[lab] = (h["x"], h["y"])
    # A panel's label sits near the top of its cell and is centred over
    # its plot region, so with the pitch between distinct positions (or
    # the canvas over the count when there is one) floor(position / pitch)
    # is its row or column counted from the canvas edge: an empty first
    # row or column is counted, as twoway leaves it.
    canvas = doc.get("canvas") or {}

    def pitch(vals, extent, count):
        vals = sorted(set(vals))
        diffs = [b - a for a, b in zip(vals, vals[1:])]
        return min(diffs) if diffs else float(extent) / max(1, count)
    px = pitch([round(v[0], 1) for v in found.values()],
               canvas.get("w", 1), recs[pid]["cols"])
    py = pitch([round(v[1], 1) for v in found.values()],
               canvas.get("h", 1), recs[pid]["rows"])
    return [[lab, int(round(found[lab][1], 1) // py),
             int(round(found[lab][0], 1) // px)] for lab in labels]


def min_numeric_size(pid):
    doc = svg_truth.svg_document(os.path.join(WORK, pid + ".svg"))
    sizes = [t["size"] for t in doc["texts"] if t["text"]
             and _NUM.match(t["text"]) and t["size"] is not None]
    return (min(sizes) if sizes else None), doc.get("canvas")


out = {"grid": {}, "sizes": {}, "refusals": {}, "accepted": {}}
for pid in order:
    p, kind = recs[pid], kinds[pid]
    if kind == "grid":
        by = re.search(r"by\((.*)\)", p["options"]).group(1)
        rec = {"by": by, "rc": p["rc"]}
        if not p["rc"]:
            rec.update(rows=p["rows"], cols=p["cols"], n=p["n"],
                       cells=cells_of(pid, p["labels"]))
        out["grid"][by] = rec
    elif kind == "sizes":
        scheme, _, _ = pid.partition("_")
        opts = p["options"]
        m = re.search(r"by\((.*?)\)(?: xsize| scheme)", opts)
        key = "plain" if "by(" not in opts else (
            "by_" + re.sub(r"[^a-z0-9]+", "_",
                           (m.group(1) if m else "").lower()).strip("_"))
        if "xsize(12)" in opts:
            key += "_xsize12_ysize3"
        size, canvas = (None, None) if p["rc"] else min_numeric_size(pid)
        rec = {"options": opts, "rc": p["rc"], "notes": p["notes"],
               "label_size": size,
               "viewbox": [canvas["w"], canvas["h"]] if canvas else None}
        if "indiv_margin" in p:
            rec["indiv_margin"] = p["indiv_margin"]
            rec["col_gap"] = (p["indiv_margin"][0] or 0) + (p["indiv_margin"][1] or 0)
            rec["row_gap"] = (p["indiv_margin"][2] or 0) + (p["indiv_margin"][3] or 0)
            rec["rows"], rec["cols"] = p["rows"], p["cols"]
        out["sizes"].setdefault(scheme, {})[key] = rec
    else:
        args = re.match(r"by\(foreign, (.*)\)$", p["options"]).group(1)
        rec = {"rc": p["rc"], "message": p["message"], "notes": p["notes"],
               "at_draw": p["at_draw"]}
        out[kind][args] = rec

for scheme, recs_s in out["sizes"].items():
    for key, rec in recs_s.items():
        base = "plain_xsize12_ysize3" if key.endswith("xsize12_ysize3") else "plain"
        plain = recs_s.get(base, {}).get("label_size")
        if plain and rec.get("label_size") is not None:
            rec["mult"] = round(rec["label_size"] / plain, 4)

# margin by_indiv through each shipped scheme's #include chain (text only)
def sides_of(r, name):
    st = r.style("margin", name)
    if not st:
        return None
    vals = []
    for side in ("gleft", "gright", "gbottom", "gtop"):
        raw = (st.get(side) or "").strip()
        if raw.startswith("scheme "):
            raw = (r.get("gsize", raw[len("scheme "):].strip(),
                         class_default=False) or "").strip()
        mm = re.fullmatch(r"relative(\d+)(?:p(\d+))?", raw)
        if mm:
            vals.append(float(mm.group(1) + ("." + mm.group(2) if mm.group(2) else "")))
        else:
            try:
                vals.append(float(raw))
            except ValueError:
                vals.append(None)
    return vals

out["by_indiv"] = {}
for sch in est.SCHEMES:
    r = est.SchemeResolver(BASE)
    r.load(sch)
    name = (r.get("margin", "by_indiv", class_default=False) or "").strip()
    out["by_indiv"][sch] = {"margin": name, "sides": sides_of(r, name)}

# the by() option names bygraph_g.class and graph_g.class declare (text)
declared = []
with open(os.path.join(BASE, "b", "bygraph_g.class"), encoding="utf-8",
          errors="replace") as fh:
    cls = fh.read()
for prog in ("parse_make", "parse_settings"):
    body = cls.split("program " + prog, 1)[1]
    syn = body.split("syntax", 1)[1].split("* ]", 1)[0]
    syn = re.sub(r"//[^\n]*", "", syn)
    for w in re.findall(r"\b([A-Za-z][A-Za-z0-9]*)(\()?", syn):
        if w[0] in ("numlist", "integer", "min", "max", "string", "passthru",
                    "asis", "varlist"):
            continue
        declared.append(w[0] + ("()" if w[1] else ""))
declared += ["GRAPHRegion()", "PLOTRegion()", "BGColor()", "SPACErs()"]
with open(os.path.join(BASE, "g", "graph_g.class"), encoding="utf-8",
          errors="replace") as fh:
    gcls = fh.read()
for m in re.finditer(r"_fr_title_parse_and_log `log' \"`obj'\" \w+\s+(\w+)", gcls):
    declared.append(m.group(1) + "()")
seen = []
for d in declared:
    if d not in seen:
        seen.append(d)
out["declared"] = seen

out["_meta"] = {"stata_version": Macro.getGlobal("BG_SVER"),
                "born_date": Macro.getGlobal("BG_BORN"),
                "source": "scripts/extract_by_grid_truth.do",
                "dash_commit": Macro.getGlobal("BG_COMMIT"),
                "extracted": Macro.getGlobal("BG_DATE"),
                "script": "scripts/extract_by_grid_truth.do",
                "method": "twoway scatter mpg weight per probe; rows/cols and "
                          "indiv_margin from the .Graph object; panel cells "
                          "from the label texts of the SVG export, as drawn: "
                          "twoway draws no empty row or column, so cells are "
                          "counted over the rows and columns that hold a "
                          "panel (rows/cols are the object's, before that); "
                          "the size "
                          "multiplier from the smallest numeric text (the "
                          "marker labels) over the plain graph's; "
                          "by_indiv from the scheme files' #include chains"}
with open(Macro.getGlobal("BG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d" % (Macro.getGlobal("BG_OUT"), len(order)))
end

display as text "extract_by_grid_truth.do: done"
