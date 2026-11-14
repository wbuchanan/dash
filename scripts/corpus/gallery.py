"""Publish a corpus run as the gallery and the README block (WP-33 33-08).

    python3 scripts/corpus/gallery.py --run <run> [--gallery <dir>] [--readme <path>]
                                      [--ids <file>] [--pages-url <url>] [--jobs N]
                                      [--skip-build]
    python3 scripts/corpus/gallery.py --run <run> --suggest-ids

Reads the run's examples.jsonl, twoway.jsonl, dash.jsonl and verdicts.jsonl
and writes, into a staging folder <run>/gallery/out/ first: svg/<id>-twoway.svg
and svg/<id>-dash.svg for every example twoway draws but those of a plot type
in LEFT_OUT; one dash page per plot type, <plottype>.html (in parts
<plottype>-2.html, ... when one Stata session cannot hold its rows or frames,
or when a built page is over PAGE_BYTES_MAX), each row twoway's SVG in an image
panel beside the live dash graph drawn in the frame of its own setup, each
side then put in a frame of its own by panel_page ("Stata on twoway" above
and the twoway command below, orange; "Stata on dash" and the dash command,
blue; no verdict, which corpus.json and the README block keep); and
index.html, whose panels link to the pages.  Each page is one `dash build'
in its own Stata session through scripts/stata_slot.sh.  Every page is timed
in headless Chrome.  Only when every page has built are the SVGs and pages
moved into --gallery, corpus.json written there (every example compared; one
twoway refuses is dropped from the comparison, DECISIONS D52) and, with
--readme, the README block written between its markers.
The gallery is built only at WP-50's closeout (DECISIONS P4-8).

FRAME_LIMIT: measured 22oct2026, one Stata session created 99 frames besides
`default' (100 in all), so a page holds at most FRAME_LIMIT - 2 setup frames
with a live graph (one for `default', one for the stack frame dash build
makes) and a plot type with more setups is built in parts.

PAGE_BYTES_MAX and LEFT_OUT (DECISIONS D78, 13nov2026, in place of P5-3's
"nothing split on size"): the gallery is committed to GitHub and served by
GitHub Pages, which refuse a file over 100 MB.  A built page over the cap is
split again by its bytes a row and its plot type rebuilt (build_capped).
contour is left out: its 16 examples made a 107 MB page, each twoway SVG
5.6 MB; corpus.json keeps their comparison, on no page.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import base64
import concurrent.futures
import datetime
import html
import json
import re
import shutil
import subprocess
import time
import urllib.parse

from scripts.corpus import dash_run, datasets, twoway_run

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IDS_PATH = os.path.join(REPO, "scripts", "corpus", "readme_examples.txt")

#: Frames one Stata session held, `default' included (measured 22oct2026: 99 created).
FRAME_LIMIT = 100
#: Rows on one page: 2 cells and at most 2 image panels a row, within the
#: page's $dash_max_graphs and $dash_max_images of 1000.
ROWS_PER_PART = 500
#: Bytes a gallery file may hold (D78): GitHub refuses a file over 100 MB and
#: warns over 50 MB; a 10 MB page loads in about 10 s.
PAGE_BYTES_MAX = 10 * 1000 * 1000
#: Plot types the gallery leaves out (D78).
LEFT_OUT = ("contour",)
#: Rounds of build_capped's re-splitting before it gives up.
SPLIT_ROUNDS = 5
CAPTION_MAX = 400
ALT_MAX = 200
START = "<!-- dash-gallery:start -->"
END = "<!-- dash-gallery:end -->"
#: The promise that resolves once two animation frames have run (the first paint).
TWO_FRAMES_JS = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
#: README candidates' groups, in order (D-33-08.k).
GROUPS = ("scatter", "line", "connected", "fit", "by()", "histogram", "kdensity", "bar",
          "area", "pcarrow", "colorvar()")
_FITS = ("lfit", "lfitci", "qfit", "qfitci")
_PLACEHOLDER = "__dash_gallery_name__"

_PLOTTYPE_RE = re.compile(r"^[a-z0-9]+$")
_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_GAPS4_RE = re.compile(r"(?<![A-Za-z0-9])(?:[a-z]+:)?[A-Z]{2,4}-[0-9]+(?![0-9])")
_CHECK_RE = re.compile(r"(?<![A-Za-z0-9_])[a-z]+(?:_[a-z]+)+(?![A-Za-z0-9_])")
_FRAME_RE = re.compile(r"\bgf[0-9]+\b")
_MARK_RE = re.compile(r"^##(FRAME|IMAGE|GRAPH|STATIC|BUILD)\s+(\S+)(?:\s+(-?\d+))?\s*$")
_DATA_URI_RE = re.compile(r"data:image/([^;,\"'\s)]+)((?:;[^,\"'\s)]*)?),([^\"'\s)<>]*)", re.I)
_IMAGE_RE = re.compile(r"<image\b[^>]*>", re.I)
_HREF_RE = re.compile(r"(?:^|\s)(?:xlink:)?href\s*=\s*(\"[^\"]*\"|'[^']*')", re.I)


# ---- reading a run ------------------------------------------------------------

def _jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def load_run(run_dir):
    """(the joined rows in id order, the ids missing from any of the four files)."""
    parts = {}
    for key, name in (("example", "examples"), ("twoway", "twoway"), ("dash", "dash"),
                      ("verdict", "verdicts")):
        parts[key] = {r["id"]: r for r in _jsonl(os.path.join(run_dir, name + ".jsonl"))}
    every = set().union(*(set(v) for v in parts.values()))
    # D52: an example twoway refuses is dropped from the comparison.
    every -= {i for i, r in parts["twoway"].items()
              if not r.get("skip") and r.get("rc") not in (0, None)}
    rows, missing = [], []
    for i in sorted(every):
        if all(i in v for v in parts.values()):
            row = {"id": i}
            row.update({k: v[i] for k, v in parts.items()})
            rows.append(row)
        else:
            missing.append(i)
    return rows, missing


def read_ids(path):
    """The ids of an id list: one a line, blank lines and # comments skipped."""
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]


def with_name(cmd, name):
    """cmd with name(<name>) appended by dash_run.with_saving's comma rule."""
    return dash_run.with_saving(cmd, _PLACEHOLDER).replace(
        'saving("%s", replace)' % _PLACEHOLDER, "name(%s)" % name)


def on_gallery(row):
    """True for a row twoway draws (verdict gallery true) of a plot type not left out."""
    return bool(row["verdict"].get("gallery")) and (
        row["example"].get("plottype") not in LEFT_OUT)


def pages(rows):
    """{plottype: rows} of the rows on the gallery (on_gallery), id order."""
    out = {}
    for r in sorted(rows, key=lambda r: r["id"]):
        if not on_gallery(r):
            continue
        pt = r["example"].get("plottype") or ""
        if not _PLOTTYPE_RE.match(pt):
            raise ValueError("gallery: %s has the plot type %r, not [a-z0-9]+" % (r["id"], pt))
        out.setdefault(pt, []).append(r)
    return out


def _setup(row, cache):
    lines, missing = datasets.rewrite_setup(row["example"].get("setup") or [], cache)
    return "\n".join(lines), missing


def setup_frames(rows, cache):
    """({rewritten setup text: gf<j>}, {gf<j>: the datasets it lacks})."""
    frames, missing = {}, {}
    for r in rows:
        key, miss = _setup(r, cache)
        if key not in frames:
            frames[key] = "gf%d" % (len(frames) + 1)
            missing[frames[key]] = miss
    return frames, missing


def _kind(row, missing):
    if missing:
        return "static"
    if row["dash"].get("rc") not in (0,) or row["verdict"].get("rc_dash") not in (0,):
        return "refused"
    return "live"


def page_parts(page, rows, cache, frame_limit=FRAME_LIMIT):
    """[(page name, rows)] of one plot type: a new part before the row that
    would give a part more than ROWS_PER_PART rows or, with a frame limit,
    more than frame_limit - 2 setup frames holding a live graph."""
    parts, cur, live = [], [], set()
    for r in rows:
        key, miss = _setup(r, cache)
        new_frame = _kind(r, miss) == "live" and key not in live
        if cur and (len(cur) + 1 > ROWS_PER_PART
                    or (frame_limit is not None and new_frame
                        and len(live) + 1 > frame_limit - 2)):
            parts.append(cur)
            cur, live = [], set()
            new_frame = _kind(r, miss) == "live"
        cur.append(r)
        if new_frame:
            live.add(key)
    if cur:
        parts.append(cur)
    return [(page if k == 0 else "%s-%d" % (page, k + 1), p) for k, p in enumerate(parts)]


def _plottype(page):
    return page.split("-")[0]


def resplit(page_rows, sizes, cache, cap=PAGE_BYTES_MAX, frame_limit=FRAME_LIMIT):
    """(page_rows split again, {plot types split}) for built pages of *sizes*
    ({page: bytes}) over *cap* (D78).  A page's fixed bytes are taken as the
    smallest page's, at most a quarter of the cap; the rest is shared evenly
    by its rows.  Each plot type with a page over the cap has its rows, in
    order, cut where a part would pass 90% of the cap, each cut then held to
    page_parts' rules, and its parts renumbered.  ValueError for a page of
    one row over the cap."""
    base = min(min(sizes.values()), cap // 4)
    redo = set()
    for page, rows in page_rows.items():
        if sizes[page] > cap:
            if len(rows) < 2:
                raise ValueError("gallery: %s.html holds one example in %d bytes, over "
                                 "the %d-byte cap" % (page, sizes[page], cap))
            redo.add(_plottype(page))
    if not redo:
        return dict(page_rows), redo
    out = {}
    for pt in dict.fromkeys(_plottype(p) for p in page_rows):
        mine = [(p, rows) for p, rows in page_rows.items() if _plottype(p) == pt]
        if pt not in redo:
            out.update(mine)
            continue
        cuts, cur, used = [], [], 0.0
        for p, rows in mine:
            each = max(sizes[p] - base, 0) / len(rows)
            for r in rows:
                if cur and base + used + each > 0.9 * cap:
                    cuts.append(cur)
                    cur, used = [], 0.0
                cur.append(r)
                used += each
        cuts.append(cur)
        parts = [rows for cut in cuts
                 for _name, rows in page_parts(pt, cut, cache, frame_limit)]
        out.update((pt if k == 0 else "%s-%d" % (pt, k + 1), rows)
                   for k, rows in enumerate(parts))
    return out, redo


def build_capped(page_rows, run_dir, out_dir, repo, jobs, cache, cap=PAGE_BYTES_MAX):
    """Build every page, then split again and rebuild each plot type with a
    page over *cap* until every page fits (D78); (page_rows, build_pages'
    {page: {log, shown}})."""
    built = build_pages(page_rows, run_dir, out_dir, repo, jobs)
    for rnd in range(SPLIT_ROUNDS + 1):
        sizes = {p: os.path.getsize(os.path.join(out_dir, p + ".html")) for p in page_rows}
        new, redo = resplit(page_rows, sizes, cache, cap)
        if not redo:
            return page_rows, built
        if rnd == SPLIT_ROUNDS:
            break
        for p in page_rows:
            if _plottype(p) in redo:
                os.remove(os.path.join(out_dir, p + ".html"))
                del built[p]
        page_rows = new
        print("gallery: split %s again, over %d bytes a page" % (", ".join(sorted(redo)), cap))
        built.update(build_pages({p: r for p, r in page_rows.items() if _plottype(p) in redo},
                                 run_dir, out_dir, repo, jobs))
    raise RuntimeError("gallery: a page is still over %d bytes after %d rounds"
                       % (cap, SPLIT_ROUNDS))


# ---- texts --------------------------------------------------------------------

def stata_terms_only(text):
    """False when text holds a GAPS4 id, a harness check name or a frame name (A-24)."""
    return not (_GAPS4_RE.search(text) or _CHECK_RE.search(text) or _FRAME_RE.search(text))


def _clean(text, bound):
    text = (text or "").replace("\r", " ").replace("\n", " ")
    return text if len(text) <= bound else text[:bound - 3] + "..."


def _missing_names(row):
    return datasets.rewrite_setup(row["example"].get("setup") or [], datasets.cache_dir())[1]


def captions(row, kind):
    """(caption, alt) of a row's twoway image ("twoway") or its static dash
    image.  The twoway image has no caption: its command is its panel's
    (panel_texts) and a page shows no verdict, which corpus.json and the
    README block keep."""
    cmd = row["example"]["cmd"]
    if kind == "static":
        return (_clean("dash's exported SVG (static: dataset not in the cache: %s)"
                       % " ".join(_missing_names(row)), CAPTION_MAX),
                _clean("dash: " + cmd, ALT_MAX))
    return "", _clean("twoway: " + cmd, ALT_MAX)


# ---- panels -------------------------------------------------------------------

PANEL_LABELS = {"twoway": "Stata on twoway", "dash": "Stata on dash"}
#: (background, border colour) of each side's panel: a light frame round
#: the picture, orange for twoway and blue for dash.  The rest is shared, so
#: both sides keep the same room for their pictures.
PANEL_COLOURS = {"twoway": ("#fdeedf", "#eda25c"), "dash": ("#e8f1fb", "#7fb0e0")}
PANEL_STYLES = (("padding", "10px"), ("box-sizing", "border-box"),
                ("border-radius", "6px"))
_PANEL_NAME = "gallery-panel-"
_LABEL_HTML = ('<div style="margin:0 0 6px 0;font:600 15px/1.3 -apple-system,'
               "BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;"
               'color:#1f2328">%s</div>')
_CMD_HTML = ('<code style="display:block;margin:6px 0 0 0;font:13px/1.45 ui-monospace,'
             'SFMono-Regular,Menlo,Consolas,monospace;color:#1f2328;'
             'white-space:pre-wrap;overflow-wrap:anywhere">%s</code>')
_NOTE_HTML = ('<div style="margin:6px 0;font:14px/1.4 -apple-system,BlinkMacSystemFont,'
              "'Segoe UI',Helvetica,Arial,sans-serif;color:#9a3412\">%s</div>")
_DOC_RE = re.compile(r'(<script type="application/json" id="[^"]+">)(.*?)(</script>)', re.S)


def panel_texts(row, side, kind):
    """(label, command, note) of a row's "twoway" or "dash" panel.  The note
    says why a refused row has no dash graph; it is empty otherwise."""
    if side not in PANEL_LABELS:
        raise ValueError("gallery: a panel is twoway's or dash's, not %r" % (side,))
    ex = row["example"]
    cmd = _clean(ex["cmd"] if side == "twoway" else ex["dash_cmd"], CAPTION_MAX)
    note = ""
    if side == "dash" and kind == "refused":
        v = row["verdict"]
        rc = v.get("rc_dash")
        note = ("dash r(%d): %s" % (rc, v.get("first_dash") or "") if rc not in (0, None)
                else "dash did not draw this graph on this page")
        note = _clean(note, CAPTION_MAX)
    return PANEL_LABELS[side], cmd, note


def _div(ident, text):
    return {"type": "object", "name": "Div", "id": ident,
            "attributes": {"text": text, "sizing_mode": "stretch_width",
                           "disable_math": True}}


def _panel(ident, side, children):
    bg, edge = PANEL_COLOURS[side]
    styles = list(PANEL_STYLES) + [("border", "1px solid " + edge), ("background-color", bg)]
    return {"type": "object", "name": "Column", "id": ident,
            "attributes": {"name": _PANEL_NAME + side,
                           "css_classes": ["gallery-panel", _PANEL_NAME + side],
                           "children": children, "sizing_mode": "stretch_width",
                           "styles": {"type": "map", "entries": [list(s) for s in styles]}}}


def _aria_label(model):
    attrs = (model.get("attributes") or {}).get("html_attributes") or {}
    return dict(attrs.get("entries") or []).get("aria-label")


def _dash_name(alt):
    """The accessible name dash gives a picture whose alt() is *alt*: its
    rule (dash_render._dash_aria), which cuts a name to 120 characters."""
    import types
    import dash_render
    return dash_render._dash_aria(types.SimpleNamespace(html_attributes={}),
                                  alt).html_attributes.get("aria-label")


def panel_page(path, rows, shown):
    """Put each cell of a built page in its panel: the label above, the
    command below, twoway's at column 1 and dash's, shaded, at column 2;
    a refused row's dash panel holds its note in place of a graph.  Only
    the page's layout JSON changes (its scripts, and their hashes in the
    page's Content-Security-Policy, do not).  The number of panels written;
    0, the page untouched, when it is panelled already.  ValueError naming
    the page, which is left as it was, when its grid is not rows' (one row
    each, twoway's image first, a dash cell exactly when the row is not
    refused)."""
    name = os.path.basename(path)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = _DOC_RE.search(text)
    try:
        docs = json.loads(html.unescape(m.group(2))) if m else None
        root = list(docs.values())[0]["roots"][0]
        grid = [c for c in root["attributes"]["children"] if c.get("name") == "GridPlot"][0]
        cells = grid["attributes"]["children"]
    except (TypeError, ValueError, KeyError, IndexError, AttributeError):
        raise ValueError("gallery: %s holds no dash build grid" % name)
    if any(isinstance(c[0], dict) and str((c[0].get("attributes") or {}).get("name", ""))
           .startswith(_PANEL_NAME) for c in cells):
        return 0
    at = {}
    for c in cells:
        if len(c) != 3 or (c[1], c[2]) in at or c[2] not in (0, 1):
            raise ValueError("gallery: %s's grid is not one twoway and one dash cell a row"
                             % name)
        at[(c[1], c[2])] = c[0]
    want = {(k, 0) for k in range(len(rows))} | {
        (k, 1) for k, r in enumerate(rows) if shown.get(r["id"]) != "refused"}
    if set(at) != want:
        raise ValueError("gallery: %s's grid holds %d cells, not its %d rows' %d"
                         % (name, len(at), len(rows), len(want)))
    for k, r in enumerate(rows):
        if _aria_label(at[(k, 0)]) != _dash_name(captions(r, "twoway")[1]):
            raise ValueError("gallery: %s's row %d is not %s" % (name, k + 1, r["id"]))
    out = []
    for k, r in enumerate(rows):
        kind = shown.get(r["id"])
        for col, side in enumerate(("twoway", "dash")):
            label, cmd, note = panel_texts(r, side, kind)
            ident = "gallery-%d-%s" % (k + 1, side)
            inner = at.get((k, col)) or _div(ident + "-note", _NOTE_HTML % html.escape(note))
            out.append([_panel(ident, side, [
                _div(ident + "-label", _LABEL_HTML % html.escape(label)), inner,
                _div(ident + "-command", _CMD_HTML % html.escape(cmd))]), k, col])
    grid["attributes"]["children"] = out
    body = html.escape(json.dumps(docs, separators=(",", ":")), quote=False)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text[:m.start(2)] + body + text[m.end(2):])
    return len(out)


# ---- page do-files ------------------------------------------------------------

def _header(repo):
    return ["version 19", "set more off", "set linesize 255",
            'adopath ++ "%s/"' % repo.rstrip("/"), "global dash_nobrowser 1",
            "global dash_max_graphs 1000", "global dash_max_images 1000", "dash clear"]


def _image(path, name, cell, marker, label):
    return ["file read _cap cap", "file read _cap alt",
            "capture noisily dash image using \"%s\", name(%s) "
            "caption(`\"`macval(cap)'\"') alt(`\"`macval(alt)'\"')" % (path, name),
            "local rc = _rc",
            "if `rc' == 0 local lay `\"`lay' %s:%s\"'" % (name, cell),
            'display "##%s %s `rc\'"' % (marker, label)]


def write_page(page, rows, out_dir, page_dir, repo):
    """Write page.do, setup_<j>.do and captions.txt for one page; (page.do, {id: kind})."""
    cache = datasets.cache_dir()
    os.makedirs(page_dir, exist_ok=True)
    frames, missing = setup_frames(rows, cache)
    kinds, frame_of = {}, {}
    for r in rows:
        if not _ID_RE.match(r["id"]):
            raise ValueError("gallery: the id %r cannot be written into a do-file" % r["id"])
        key, _ = _setup(r, cache)
        frame_of[r["id"]] = frames[key]
        kinds[r["id"]] = _kind(r, missing[frames[key]])
    used = [gf for gf in frames.values() if any(
        kinds[i] == "live" and frame_of[i] == gf for i in kinds)]
    lines = _header(repo)
    for key, gf in frames.items():
        if gf not in used:
            continue
        j = gf[2:]
        setup_path = os.path.join(page_dir, "setup_%s.do" % j)
        with open(setup_path, "w", encoding="utf-8") as fh:
            fh.write(key + "\n" if key else "")
        lines += ["frame create %s" % gf,
                  'frame %s: capture noisily do "%s"' % (gf, setup_path),
                  'display "##FRAME %s " _rc' % gf]
    caps = []
    cap_path = os.path.join(page_dir, "captions.txt")
    lines += ['file open _cap using "%s", read text' % cap_path, 'local lay ""']
    svg = os.path.join(out_dir, "svg")
    for k, r in enumerate(rows, 1):
        i, kind = r["id"], kinds[r["id"]]
        lines.append("* row %d: %s (%s)" % (k, i, kind))
        caps += list(captions(r, "twoway"))
        lines += _image("%s/%s-twoway.svg" % (svg, i), "t%d" % k, "%d,1" % k, "IMAGE", i)
        if kind == "live":
            lines += ["frame %s: capture noisily %s"
                      % (frame_of[i], with_name(r["example"]["dash_cmd"], "g%d" % k)),
                      "local rc = _rc",
                      "if `rc' == 0 local lay `\"`lay' g%d:%d,2\"'" % (k, k),
                      'display "##GRAPH %s `rc\'"' % i]
        elif kind == "static" and r["dash"].get("svg"):
            caps += list(captions(r, "static"))
            lines += _image("%s/%s-dash.svg" % (svg, i), "d%d" % k, "%d,2" % k, "STATIC", i)
    lines += ["file close _cap",
              'capture noisily dash build, saving("%s/%s.html") replace '
              'title("dash beside twoway: %s") layout(`lay\') nobrowser' % (out_dir, page, page),
              'display "##BUILD " _rc']
    with open(cap_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(caps) + "\n")
    path = os.path.join(page_dir, "page.do")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path, kinds


def parse_page_log(text):
    """The ## markers of a page's log and its first error line."""
    out = {"frames": {}, "images": {}, "graphs": {}, "static": {}, "build": None,
           "error": None}
    keys = {"FRAME": "frames", "IMAGE": "images", "GRAPH": "graphs", "STATIC": "static"}
    for raw in text.splitlines():
        ln = raw.rstrip()
        m = _MARK_RE.match(ln)
        if m:
            if m.group(1) == "BUILD":
                out["build"] = int(m.group(2))
            elif m.group(3) is not None:
                out[keys[m.group(1)]][m.group(2)] = int(m.group(3))
            continue
        if out["error"] is None and (ln.startswith("r(") or ln.startswith("dash build:")):
            out["error"] = ln
    return out


def run_page(page_dir):
    """Run <page_dir>/page.do in its own Stata session; its parsed log."""
    log = os.path.join(page_dir, "page.log")
    if os.path.exists(log):
        os.remove(log)
    subprocess.run(list(twoway_run.SLOT_CMD) + [page_dir, os.path.join(page_dir, "page.do")],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(log):
        out = parse_page_log("")
        out["error"] = "no page.log"
        return out
    with open(log, encoding="utf-8", errors="replace") as fh:
        return parse_page_log(fh.read())


def _failed(page, parsed):
    return RuntimeError("gallery: %s.html did not build: r(%s): %s"
                        % (page, parsed["build"], parsed["error"]))


def build_pages(page_rows, run_dir, out_dir, repo, jobs=3):
    """Write and build every page once; {page: {"log": parsed, "shown": {id: kind}}}."""
    planned = {}
    for page, rows in page_rows.items():
        pdir = os.path.join(run_dir, "gallery", page)
        planned[page] = (pdir, write_page(page, rows, out_dir, pdir, repo)[1])
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        logs = dict(zip(planned, ex.map(lambda p: run_page(planned[p][0]), list(planned))))
    out = {}
    for page, (_pdir, kinds) in planned.items():
        parsed = logs[page]
        if parsed["build"] != 0:
            raise _failed(page, parsed)
        shown = dict(kinds)
        for i, k in kinds.items():
            if k == "live" and parsed["graphs"].get(i, 0) != 0:
                shown[i] = "refused"
        panel_page(os.path.join(out_dir, page + ".html"), page_rows[page], shown)
        out[page] = {"log": parsed, "shown": shown}
        print("gallery: %s.html built (%d examples)" % (page, len(page_rows[page])))
    return out


def _sha7(meta):
    return (meta.get("dash_commit") or "")[:7]


def write_index(page_rows, shown, out_dir, index_dir, repo, meta):
    """Write the index page's do-file (one linked panel per page) and captions; its path."""
    os.makedirs(index_dir, exist_ok=True)
    cap_path = os.path.join(index_dir, "captions.txt")
    lines = _header(repo) + ['file open _cap using "%s", read text' % cap_path]
    caps, total = [], 0
    by_type = {}
    for page in page_rows:
        by_type.setdefault(page.split("-")[0], []).append(page)
    for k, (page, rows) in enumerate(page_rows.items(), 1):
        pt = page.split("-")[0]
        live = [r for r in rows if shown.get(r["id"]) == "live"]
        first = (live or rows)[0]
        n, total = len(rows), total + len(rows)
        parts = by_type[pt]
        cap = ("%s: %d examples" % (pt, n) if len(parts) == 1 else
               "%s (part %d of %d): %d examples" % (pt, parts.index(page) + 1, len(parts), n))
        alt = "twoway %s: opens %s.html" % (pt, page)
        for t in (cap, alt):
            if not stata_terms_only(t):
                raise ValueError("gallery: the index caption %r names an internal id" % t)
        caps += [cap, alt]
        lines += ["file read _cap cap", "file read _cap alt",
                  "capture noisily dash image using \"%s/svg/%s-twoway.svg\", name(i%d) "
                  "caption(`\"`macval(cap)'\"') alt(`\"`macval(alt)'\"') link(\"%s.html\")"
                  % (out_dir, first["id"], k, page),
                  "local rc = _rc", 'display "##IMAGE %s `rc\'"' % page]
    caps.append("%d examples twoway draws, drawn on %s at dash commit %s"
                % (total, meta.get("generated"), _sha7(meta)))
    lines += ["file read _cap sub", "file close _cap",
              'capture noisily dash build, saving("%s/index.html") replace '
              'title("dash beside twoway") subtitle(`"`macval(sub)\'"\') layout(auto) '
              "nobrowser" % out_dir,
              'display "##BUILD " _rc']
    with open(cap_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(caps) + "\n")
    path = os.path.join(index_dir, "page.do")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


# ---- files --------------------------------------------------------------------

def copy_svgs(rows, run_dir, out_dir):
    """Copy each gallery row's SVGs into <out_dir>/svg/; {id: {twoway_svg, dash_svg}}."""
    svg = os.path.join(out_dir, "svg")
    os.makedirs(svg, exist_ok=True)
    out = {}
    for r in rows:
        if not on_gallery(r):
            continue
        i, got = r["id"], {"twoway_svg": None, "dash_svg": None}
        src = r["twoway"].get("svg")
        if src and os.path.exists(os.path.join(run_dir, src)):
            with open(os.path.join(run_dir, src), encoding="utf-8") as fh:
                text = dash_run.normalise_svg(fh.read())
            with open(os.path.join(svg, i + "-twoway.svg"), "w", encoding="utf-8") as fh:
                fh.write(text)
            got["twoway_svg"] = "svg/%s-twoway.svg" % i
        src = r["dash"].get("svg")
        if src and os.path.exists(os.path.join(run_dir, src)):
            shutil.copyfile(os.path.join(run_dir, src), os.path.join(svg, i + "-dash.svg"))
            got["dash_svg"] = "svg/%s-dash.svg" % i
        out[i] = got
    return out


def is_vector_svg(text):
    """False when the SVG embeds a raster image, its embedded SVGs' included (A-26)."""
    for m in _DATA_URI_RE.finditer(text):
        if m.group(1).lower() != "svg+xml":
            return False
        payload = m.group(3)
        if ";base64" in m.group(2).lower():
            try:
                inner = base64.b64decode(payload + "=" * (-len(payload) % 4)).decode(
                    "utf-8", "replace")
            except ValueError:
                return False
        else:
            inner = urllib.parse.unquote(payload)
        if not is_vector_svg(inner):
            return False
    for m in _IMAGE_RE.finditer(text):
        hrefs = [h[1:-1] for h in _HREF_RE.findall(m.group(0))]
        if not hrefs or any(not h.lower().startswith("data:image/svg+xml") for h in hrefs):
            return False
    return True


def measure_load(paths, probe=None):
    """{file name: seconds} each page takes in headless Chrome to draw (P5-3)."""
    out = {}
    own = probe is None
    try:
        for p in paths:
            if probe is None:
                probe = dash_run.CorpusProbe(p, timeout=300).__enter__()
            t0 = time.monotonic()
            probe.navigate(p)
            probe.eval_async(TWO_FRAMES_JS)
            out[os.path.basename(p)] = round(time.monotonic() - t0, 2)
    finally:
        if own and probe is not None:
            probe.__exit__(None, None, None)
    return out


def swap_in(out_dir, gallery_dir, html=True):
    """Replace <gallery_dir>/svg (and, with html, its pages) with the staged files."""
    os.makedirs(gallery_dir, exist_ok=True)
    new = os.path.join(gallery_dir, ".svg-new")
    if os.path.exists(new):
        shutil.rmtree(new)
    shutil.copytree(os.path.join(out_dir, "svg"), new)
    old = os.path.join(gallery_dir, "svg")
    if os.path.exists(old):
        shutil.rmtree(old)
    os.rename(new, old)
    wrote = ["svg/" + f for f in os.listdir(old)]
    if html:
        for f in os.listdir(gallery_dir):
            if f.endswith(".html"):
                os.remove(os.path.join(gallery_dir, f))
        for f in os.listdir(out_dir):
            if f.endswith(".html"):
                shutil.copyfile(os.path.join(out_dir, f), os.path.join(gallery_dir, f))
                wrote.append(f)
    return sorted(wrote)


def _shown_of(v):
    if v is None:
        return None, None
    return tuple(v) if isinstance(v, (tuple, list)) else (v, None)


def corpus_json(rows, shown, svgs, meta, root):
    """corpus.json's dict: _meta and every example (shown: {id: (kind, page)})."""
    cache = datasets.cache_dir()
    examples = []
    n = dict.fromkeys(("examples", "duplicates", "Same", "Close", "Differs", "skipped",
                       "refused_dash", "gallery", "live", "static", "refused_shown"), 0)
    for r in sorted(rows, key=lambda r: r["id"]):
        e, v = r["example"], r["verdict"]
        kind, page = _shown_of(shown.get(r["id"]))
        paths = svgs.get(r["id"]) or {"twoway_svg": None, "dash_svg": None}
        vector = None
        if paths.get("dash_svg"):
            with open(os.path.join(root, paths["dash_svg"]), encoding="utf-8",
                      errors="replace") as fh:
                vector = is_vector_svg(fh.read())
        examples.append({
            "id": r["id"], "source": e.get("source"), "file": e.get("file"),
            "line": e.get("line"), "entry": e.get("entry"), "command": e.get("cmd"),
            "dash_command": e.get("dash_cmd"), "plottype": e.get("plottype"),
            "duplicates": e.get("duplicates") or [], "rc": v.get("rc_pair"),
            "first_twoway": v.get("first_twoway"), "first_dash": v.get("first_dash"),
            "verdict": v.get("verdict"), "summary": v.get("summary"),
            "checks": v.get("checks"), "differences": v.get("differences"),
            "ledger": v.get("ledger"), "ssim": v.get("ssim"),
            "size_matched": v.get("size_matched"), "gallery": on_gallery(r),
            "shown": kind, "page": page, "twoway_svg": paths.get("twoway_svg"),
            "dash_svg": paths.get("dash_svg"), "dash_svg_vector": vector,
            "missing": (datasets.rewrite_setup(e.get("setup") or [], cache)[1]
                        if kind is not None else None)})
        n["examples"] += 1
        n["duplicates"] += len(e.get("duplicates") or [])
        n[v.get("verdict") or "skipped"] += 1
        rc_tw, rc_da = v.get("rc_twoway"), v.get("rc_dash")
        if not v.get("skip") and rc_tw == 0 and rc_da not in (0, None):
            n["refused_dash"] += 1
        n["gallery"] += on_gallery(r)
        if kind is not None:
            n["refused_shown" if kind == "refused" else kind] += 1
    m = dict(meta)
    m["counts"] = n
    m.setdefault("load_s", {})
    return {"_meta": {k: m[k] for k in sorted(m)}, "examples": examples}


def write_corpus_json(corpus, gallery_dir):
    """Write <gallery_dir>/corpus.json (2-space indent, sorted keys); its path."""
    os.makedirs(gallery_dir, exist_ok=True)
    path = os.path.join(gallery_dir, "corpus.json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return path


# ---- the README block ---------------------------------------------------------

def readme_block(corpus, ids, pages_url=None):
    """The README text between the markers: the listed pairs, twoway left."""
    meta = corpus["_meta"]
    by = {e["id"]: e for e in corpus["examples"]}
    lines = ["These pairs were drawn on %s at dash commit %s; each verdict is the corpus "
             "comparison's (make corpus)." % (meta.get("generated"), _sha7(meta)), ""]
    for i in ids:
        e = by.get(i)
        if e is None:
            raise ValueError("gallery: README id %s is not in corpus.json" % i)
        if not e.get("gallery") or not e.get("twoway_svg") or not e.get("dash_svg"):
            raise ValueError("gallery: README id %s is not on the gallery with both SVGs" % i)
        if e.get("dash_svg_vector") is not True:
            raise ValueError("gallery: README id %s has a dash SVG holding a raster image" % i)
        said = e.get("verdict") or ""
        tail = (": " + e["summary"]) if said in ("Close", "Differs") and e.get("summary") else ""
        if not stata_terms_only(said + tail):
            raise ValueError("gallery: README id %s's verdict names an internal id" % i)
        cmd = html.escape(e["command"], quote=True)
        lines.append('<p><img src="docs/gallery/%s" alt="twoway: %s" width="49%%"> '
                     '<img src="docs/gallery/%s" alt="dash: %s" width="49%%"><br>'
                     '<code>%s</code><br><b>%s</b>%s</p>'
                     % (e["twoway_svg"], cmd, e["dash_svg"], cmd, cmd,
                        html.escape(said, quote=True), html.escape(tail, quote=True)))
    lines.append("")
    if pages_url:
        u = html.escape(pages_url, quote=True)
        lines.append("Every example twoway draws, with its live dash graph, is on the gallery "
                     "pages: [%s](%s)." % (u, u))
    else:
        lines.append("Every example twoway draws, with its live dash graph, is on the gallery "
                     "pages: [docs/gallery/index.html](docs/gallery/index.html) (open them from "
                     "a downloaded copy of the folder, or on the project's GitHub Pages site "
                     "once the maintainer turns it on).")
    return "\n".join(lines)


def replace_block(readme_text, block):
    """readme_text with block between the markers, inserted above ## Documentation once."""
    s, e = readme_text.count(START), readme_text.count(END)
    if s == 0 and e == 0:
        m = re.search(r"^## Documentation\s*$", readme_text, re.M)
        if not m:
            raise ValueError("gallery: README.md has no ## Documentation heading")
        readme_text = (readme_text[:m.start()] + "## Gallery\n\n%s\n%s\n\n" % (START, END)
                       + readme_text[m.start():])
    elif s != 1 or e != 1:
        raise ValueError("gallery: README.md holds %d start and %d end markers" % (s, e))
    a, b = readme_text.index(START), readme_text.index(END)
    if b < a:
        raise ValueError("gallery: README.md's end marker comes before its start marker")
    return readme_text[:a + len(START)] + "\n" + block + "\n" + readme_text[b:]


def _groups_of(e):
    pt, cmd = e.get("plottype") or "", e.get("command") or ""
    g = []
    if pt in ("scatter", "line", "connected", "histogram", "kdensity", "bar", "pcarrow"):
        g.append(pt)
    if pt in _FITS or re.search(r"\b(?:%s)\b" % "|".join(_FITS), cmd):
        g.append("fit")
    if re.search(r"\bby\(", cmd):
        g.append("by()")
    if pt in ("area", "rarea"):
        g.append("area")
    if re.search(r"\bcolorvar\(", cmd):
        g.append("colorvar()")
    return g


def readme_candidates(corpus, root):
    """{group: ids} of the help examples on the gallery whose dash SVG is fully vector."""
    out = {g: [] for g in GROUPS}
    keyed = []
    for e in corpus["examples"]:
        if (not e.get("gallery") or e.get("plottype") in LEFT_OUT or e.get("source") != "help"
                or e.get("dash_svg_vector") is not True):
            continue
        small = all(e.get(k) and os.path.exists(os.path.join(root, e[k]))
                    and os.path.getsize(os.path.join(root, e[k])) < 300 * 1024
                    for k in ("twoway_svg", "dash_svg"))
        keyed.append(((not e.get("size_matched"), not small, e["id"]), e))
    for _key, e in sorted(keyed, key=lambda t: t[0]):
        for g in _groups_of(e):
            out[g].append(e["id"])
    return out


# ---- main ---------------------------------------------------------------------

def _git_head(repo):
    p = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def _meta(run_dir, repo):
    path = os.path.join(run_dir, "stata_version.txt")
    version = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            version = fh.read().strip() or None
    return {"generated": datetime.date.today().strftime("%d%b%Y").lower(),
            "dash_commit": _git_head(repo), "stata_version": version}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, metavar="RUN_DIR")
    ap.add_argument("--gallery", default=os.path.join(REPO, "docs", "gallery"))
    ap.add_argument("--readme", default=None)
    ap.add_argument("--ids", default=IDS_PATH)
    ap.add_argument("--pages-url", default=None)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--suggest-ids", action="store_true")
    a = ap.parse_args(argv)
    run_dir = os.path.abspath(a.run)
    rows, dropped = load_run(run_dir)
    if dropped:
        print("gallery: %d examples missing from a run file, left out" % len(dropped))
    meta = _meta(run_dir, REPO)
    if a.suggest_ids:
        svgs = {r["id"]: {"twoway_svg": r["twoway"].get("svg"), "dash_svg": r["dash"].get("svg")}
                for r in rows}
        corpus = corpus_json(rows, {}, svgs, meta, run_dir)
        for g, ids in readme_candidates(corpus, run_dir).items():
            print("%s: %s" % (g, " ".join(ids) if ids else "(none)"))
        return 0
    cache = datasets.cache_dir()
    page_rows = {}
    for pt, prow in pages(rows).items():
        for name, part in page_parts(pt, prow, cache):
            page_rows[name] = part
    out_dir = os.path.join(run_dir, "gallery", "out")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    svgs = copy_svgs(rows, run_dir, out_dir)
    shown, load_s = {}, {}
    if a.skip_build:
        for page, prow in page_rows.items():
            kinds = write_page(page, prow, out_dir, os.path.join(run_dir, "gallery", page),
                               REPO)[1]
            shown.update({i: (k, page) for i, k in kinds.items()})
    else:
        page_rows, built = build_capped(page_rows, run_dir, out_dir, REPO, a.jobs, cache)
        flat = {}
        for page, b in built.items():
            flat.update(b["shown"])
            shown.update({i: (k, page) for i, k in b["shown"].items()})
        idx = os.path.join(run_dir, "gallery", "_index")
        write_index(page_rows, flat, out_dir, idx, REPO, meta)
        parsed = run_page(idx)
        if parsed["build"] != 0:
            raise _failed("index", parsed)
        if os.path.getsize(os.path.join(out_dir, "index.html")) > PAGE_BYTES_MAX:
            raise RuntimeError("gallery: index.html is over %d bytes" % PAGE_BYTES_MAX)
        print("gallery: index.html built (%d pages)" % len(page_rows))
        files = [os.path.join(out_dir, p + ".html") for p in page_rows]
        load_s = measure_load(files + [os.path.join(out_dir, "index.html")])
    meta.update(pages=list(page_rows), load_s=load_s)
    corpus = corpus_json(rows, shown, svgs, meta, out_dir)
    new = None
    if a.readme:
        with open(a.readme, encoding="utf-8") as fh:
            new = replace_block(fh.read(), readme_block(corpus, read_ids(a.ids), a.pages_url))
    swap_in(out_dir, a.gallery, html=not a.skip_build)
    write_corpus_json(corpus, a.gallery)
    if new is not None:
        with open(a.readme, "w", encoding="utf-8") as fh:
            fh.write(new)
    counts = {p: len(r) for p, r in page_rows.items()}
    counts["index"] = sum(counts.values())
    for name, s in load_s.items():
        size = os.path.getsize(os.path.join(a.gallery, name)) / 1e6
        print("gallery: %s is %.2f MB, loads in %.2f s in headless Chrome (%d examples)"
              % (name, size, s, counts[name[:-5]]))
    print("gallery: " + ", ".join("%s %d" % (k, v) for k, v in corpus["_meta"]["counts"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
