"""Run every corpus example under dash and export its picture (WP-33 33-04).

    python3 scripts/corpus/dash_run.py --run <run> [--jobs N] [--timeout S] [--only id,id]
                                       [--stata-only | --chrome-only]

The Stata half reads <run>/examples.jsonl and <run>/twoway.jsonl, writes one
do-file per chunk of examples (<run>/dash/c<k>/dash.do) running each dash
command with saving("<run>/dash/<id>.html", replace), runs each through
scripts/stata_slot.sh (at most --jobs at once) and writes <run>/dash.jsonl.
An example whose dataset the offline cache lacks is run in no chunk; each
such dataset is named once (DECISIONS A-26).

The Chrome half opens every saved page in one headless Chrome held over
DevTools, sizes a lone figure to twoway's size (anything else is exported at
its natural size and letterboxed into twoway's box), exports Bokeh's own SVG,
dumps the drawn views, normalises the SVG and writes <run>/dash/<id>.svg and
<run>/dash/<id>.view.json, then adds their fields to <run>/dash.jsonl.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import asyncio
import json
import pathlib
import re
import subprocess
import tempfile
import time

from scripts.corpus import datasets, twoway_run

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "test"))

from range_probe import RangeProbe, _READY_JS, _free_port  # noqa: E402
import responsive_probe  # noqa: E402

ROW_KEYS = ("id", "rc", "first_line", "setup_rc", "html", "skip")
CHROME_KEYS = ("svg", "view", "size_matched", "js_errors", "w", "h", "export_error")
JSONL_KEYS = ROW_KEYS + CHROME_KEYS

#: Seconds a page settles after it is sized: (plain, a page holding TeX).
SETTLE_S = (1.5, 2.5)
#: A held Chrome is restarted after this many pages.
PAGES_PER_CHROME = 100
#: px per inch, the factor dash's _dash_apply_frame_aspect uses.
PX_PER_IN = 96
#: The line dash prints for the saving() the harness adds.
_SAVED_LINE = "dash: dashboard saved to "


def _row(i, **kw):
    r = dict.fromkeys(JSONL_KEYS)
    r["id"] = i
    r.update(kw)
    return r


# ---- the Stata half ---------------------------------------------------------

def _top_level(cmd):
    """(index, char) of each character of cmd at parenthesis depth 0 outside
    "..." and `"..."' strings."""
    depth, i, n = 0, 0, len(cmd)
    while i < n:
        c = cmd[i]
        if cmd.startswith('`"', i):
            j, level = i + 2, 1
            while j < n and level:
                if cmd.startswith('`"', j):
                    level, j = level + 1, j + 2
                elif cmd.startswith('"\'', j):
                    level, j = level - 1, j + 2
                else:
                    j += 1
            i = j
            continue
        if c == '"':
            j = cmd.find('"', i + 1)
            i = n if j < 0 else j + 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            yield i, c
        i += 1


def with_saving(cmd, path):
    """cmd with saving("<path>", replace) appended as its last option
    (D-33-04.a): after the last plot's top-level comma, or after a new one.
    D57: nothing else changes; a command ending in || gets `|| , saving(...)`,
    which twoway and dash both take (measured 23oct2026)."""
    cmd = cmd.rstrip()
    opt = 'saving("%s", replace)' % path
    if cmd.endswith("||"):
        return "%s , %s" % (cmd, opt)
    last, comma = 0, False
    for i, c in _top_level(cmd):
        if c == "|" and cmd.startswith("||", i):
            last, comma = i + 2, False
        elif c == "," and i >= last:
            comma = True
    return "%s %s" % (cmd, opt) if comma else "%s, %s" % (cmd, opt)


def do_text(examples, out_dir, cache, repo):
    """The do-file that runs one chunk of dash commands between ## markers;
    refuses (ValueError) an example whose pair differs beyond twoway/dash (D57)."""
    bad = twoway_run.invalid_pairs(examples)
    if bad:
        raise ValueError("%s: %s" % (twoway_run.INVALID, ", ".join(sorted(bad))))
    out = ["version 19"]
    # A session-only python_exec when the console's own setting is missing
    # (DASH_CORPUS_PYTHON_EXEC); never `permanently' (no persistent preference).
    if os.environ.get("DASH_CORPUS_PYTHON_EXEC"):
        out.append('set python_exec "%s"' % os.environ["DASH_CORPUS_PYTHON_EXEC"])
    out += ['adopath ++ "%s/"' % repo.rstrip("/"), "global dash_nobrowser 1",
           "set more off", "set linesize 255", 'display "##VERSION " c(stata_version)']
    for e in examples:
        i = e["id"]
        setup = datasets.rewrite_setup(e.get("setup") or [], cache)[0]
        cmd = with_saving(e["dash_cmd"], "%s/%s.html" % (out_dir, i))
        out += ['display "##BEGIN %s"' % i, "clear", "capture graph drop _all",
                "capture quietly dash clear", "capture noisily {"]
        out += list(setup)
        out += ["}", 'display "##SETUP %s " _rc' % i, "if _rc == 0 {",
                "capture noisily %s" % cmd, 'display "##RC %s " _rc' % i, "}"]
    return "\n".join(out) + "\n"


def records(examples, parsed, html_dir, run_dir, twoway_rows, unreported="chunk ended early"):
    """The dash.jsonl rows of one parsed log (twoway_run.parse_log)."""
    if not isinstance(twoway_rows, dict):
        twoway_rows = {r["id"]: r for r in twoway_rows}
    rows = []
    for e in examples:
        i = e["id"]
        tw = twoway_rows.get(i)
        if tw is None:
            rows.append(_row(i, skip="no twoway record"))
            continue
        if tw.get("skip"):
            rows.append(_row(i, skip=tw["skip"]))
            continue
        p = parsed.get(i)
        if not isinstance(p, dict):
            rows.append(_row(i, skip=unreported))
            continue
        first = p["first_line"]
        if first is not None and first.startswith(_SAVED_LINE):
            first = None  # the harness's own saving(), not the example's message
        r = _row(i, rc=p["rc"], first_line=twoway_run._hide_paths(first, run_dir),
                 setup_rc=p["setup_rc"])
        if p["rc"] is None:
            r["skip"] = "setup rc %d" % p["setup_rc"]
        page = os.path.join(html_dir, i + ".html")
        if p["rc"] == 0 and os.path.exists(page):
            r["html"] = os.path.relpath(page, run_dir).replace(os.sep, "/")
        rows.append(r)
    return [{k: r[k] for k in ROW_KEYS} for r in rows]


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def _write_rows(run_dir, rows):
    rows = sorted(rows, key=lambda r: r["id"])
    with open(os.path.join(run_dir, "dash.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({k: r.get(k) for k in JSONL_KEYS}) + "\n")


def run_stata(run_dir, jobs=3, timeout=1800, only=None):
    """Run the dash commands of <run_dir>/examples.jsonl; counts of the rows."""
    examples = _read_jsonl(os.path.join(run_dir, "examples.jsonl"))
    if only is not None:
        examples = [e for e in examples if e["id"] in only]
    tw = {r["id"]: r for r in _read_jsonl(os.path.join(run_dir, "twoway.jsonl"))}
    refused = twoway_run.refused_ids(run_dir)  # D52: compared only where twoway draws
    examples = [e for e in examples if e["id"] not in refused]
    cache = datasets.cache_dir()
    for name in twoway_run.missing_datasets(examples, cache):
        print("skip: dataset %s not cached" % name)
    rows = [_row(r["id"], skip=r["skip"]) for r in twoway_run.skip_rows(examples, cache)]
    rows += [_row(i, skip=why) for i, why in sorted(twoway_run.invalid_pairs(examples).items())
             if i not in {r["id"] for r in rows}]
    aside = {r["id"] for r in rows}
    left = [e for e in examples if e["id"] not in aside]
    unrun = {e["id"] for e in left if e["id"] not in tw or tw[e["id"]].get("skip")}
    rows += records([e for e in left if e["id"] in unrun], {}, "", run_dir, tw)
    todo = twoway_run.chunks([e for e in left if e["id"] not in unrun])
    html_dir = os.path.join(run_dir, "dash")
    pending = []
    for k, ch in enumerate(todo, 1):
        d = os.path.join(html_dir, "c%d" % k)
        os.makedirs(d, exist_ok=True)
        do = os.path.join(d, "dash.do")
        with open(do, "w", encoding="utf-8") as fh:
            fh.write(do_text(ch, os.path.abspath(html_dir), cache, REPO))
        pending.append((k, ch, d, do))
    active = []
    while pending or active:
        while pending and len(active) < max(1, jobs):
            k, ch, d, do = pending.pop(0)
            p = subprocess.Popen(twoway_run.SLOT_CMD + [d, do], start_new_session=True)
            active.append((k, ch, d, p, time.monotonic()))
        time.sleep(0.1)
        still = []
        for k, ch, d, p, t0 in active:
            status = p.poll()
            if status is None and time.monotonic() - t0 > timeout:
                twoway_run._stop(p)
                print("corpus: chunk %d timed out; if no stata-mp process is left, "
                      "remove a stale /tmp/dash-stata-slot-<n>.d" % k)
                why = "timeout"
            elif status is None:
                still.append((k, ch, d, p, t0))
                continue
            else:
                why = "chunk ended early (rc %d)" % status
            parsed = twoway_run.parse_log(twoway_run._read(os.path.join(d, "dash.log")))
            rows += records(ch, parsed, html_dir, run_dir, tw, unreported=why)
        active = still
    _write_rows(run_dir, rows)
    return {"rc0": sum(r["rc"] == 0 for r in rows),
            "refused": sum(r["rc"] not in (None, 0) for r in rows),
            "skipped": sum(r["skip"] is not None for r in rows)}


# ---- the Chrome half --------------------------------------------------------

#: (W, H) => {lone, tex}: finds the page's lone figure (the one root that is
#: a Plot, or a column/row/GridBox holding only one), fixes it and every
#: root at W x H (D-33-04.c), and keeps the model to export in
#: window.__dashCorpusTarget (the first root when there is no lone figure).
SIZE_JS = r"""(W, H) => {
  const doc = Bokeh.documents[0];
  const roots = doc.roots();
  const isPlot = (m) => !!m && m.x_range !== undefined && m.renderers !== undefined
    && m.toolbar !== undefined;
  const unwrap = (m) => {
    if (isPlot(m)) return m;
    const kids = m && m.children;
    if (kids && kids.length === 1) {
      const k = Array.isArray(kids[0]) ? kids[0][0] : kids[0];
      if (isPlot(k)) return k;
    }
    return null;
  };
  const fig = roots.length === 1 ? unwrap(roots[0]) : null;
  let tex = !!document.querySelector("mjx-container");
  for (const m of doc.all_models) if (m && m.type === "TeX") tex = true;
  if (fig) {
    for (const r of roots) { r.sizing_mode = "fixed"; r.width = W; r.height = H; }
    fig.min_height = null; fig.max_height = null; fig.aspect_ratio = null;
    fig.sizing_mode = "fixed"; fig.width = W; fig.height = H;
  }
  window.__dashCorpusTarget = fig || roots[0];
  return {lone: !!fig, tex: tex};
}"""

#: () => SVG text of window.__dashCorpusTarget's view, Bokeh's own export.
EXPORT_JS = r"""async () => {
  const m = window.__dashCorpusTarget || Bokeh.documents[0].roots()[0];
  const v = Bokeh.index.find_one(m);
  const layer = await v.export("svg");
  return layer.ctx.get_serialized_svg(true);
}"""

#: () => JSON text {"figures": [...]} of TR-33-04.2; never throws.
DUMP_JS = r"""() => {
  const safe = (f, d = null) => { try { const v = f(); return v === undefined ? d : v; }
                                  catch (e) { return d; } };
  const r1 = (x) => typeof x === "number" ? Math.round(x * 10) / 10 : null;
  const box = (b) => b ? [r1(b.x), r1(b.y), r1(b.width), r1(b.height)] : null;
  const kidsOf = (v) => {
    const out = [];
    for (const k of ["child_views", "renderer_views", "axis_views"]) {
      const c = safe(() => v[k]);
      if (!c) continue;
      if (typeof c.values === "function") for (const x of c.values()) out.push(x);
      else if (Array.isArray(c)) out.push(...c);
    }
    return out;
  };
  const isPlotView = (v) => !!(v && v.model && v.model.x_range !== undefined
    && v.model.renderers !== undefined && v.frame !== undefined);
  const written = (p) => {
    if (p === null || p === undefined) return null;
    if (typeof p !== "object") return p;
    if (Array.isArray(p)) return p.map(written);
    if ("value" in p) {
      const o = {value: written(p.value)};
      if (p.transform !== undefined && p.transform !== null)
        o.transform = safe(() => p.transform.type);
      if (p.units !== undefined) o.units = p.units;
      return o;
    }
    if ("field" in p) return {field: p.field};
    if ("expr" in p) return {expr: safe(() => p.expr.type)};
    return null;
  };
  const textOf = (t) => {
    if (t === null || t === undefined) return null;
    if (typeof t === "string") return t;
    if (typeof t === "object") {
      if ("value" in t) return typeof t.value === "string" ? t.value : null;
      if ("field" in t) return t.field;
      if (typeof t.text === "string") return t.text;
    }
    return null;
  };
  const column = (src, spec) => {
    if (spec === null || spec === undefined) return null;
    if (typeof spec === "number") return [spec];
    if (typeof spec === "object" && typeof spec.value === "number") return [spec.value];
    if (typeof spec === "object" && typeof spec.field === "string") {
      const c = safe(() => src.get_column(spec.field));
      if (c && typeof c.length === "number" && c.length > 0) {
        const a = Array.from(c);
        if (a.every((x) => typeof x === "number" || x === null)) return a;
      }
    }
    return null;
  };
  const extent = (src, gm, keys) => {
    let lo = Infinity, hi = -Infinity, any = false;
    for (const k of keys) {
      const a = column(src, safe(() => gm[k]));
      if (!a) continue;
      any = true;
      for (const x of a) if (typeof x === "number" && isFinite(x)) {
        if (x < lo) lo = x;
        if (x > hi) hi = x;
      }
    }
    return any && lo <= hi ? [lo, hi] : null;
  };
  const markerOf = (gm, src) => {
    if (safe(() => gm.type) !== "Scatter") return null;
    const m = safe(() => gm.marker);
    if (typeof m === "string") return m;
    if (m && typeof m === "object") {
      if ("value" in m) return m.value;
      if (typeof m.field === "string") {
        const c = safe(() => src.get_column(m.field));
        return c ? Array.from(new Set(Array.from(c))).sort() : null;
      }
    }
    return null;
  };
  const figure = (pv) => {
    const pm = pv.model;
    const axes = [], renderers = [];
    const seen = new Set();
    const walk = (v) => {
      if (!v || seen.has(v)) return;
      seen.add(v);
      if (v !== pv && isPlotView(v)) return;
      const m = v.model;
      if (m && m.ticker !== undefined && v.tick_coords !== undefined) {
        const dim = safe(() => v.dimension);
        const ticks = safe(() => Array.from(v.tick_coords.major[dim]));
        let labels = null;
        if (typeof v.compute_labels === "function" && ticks)
          labels = safe(() => v.compute_labels(ticks).items.map(
            (b) => typeof b.text === "string" ? b.text : null));
        // The axis's own scale (its range name's), a model: its type names it.
        const scale = safe(() => dim === 0 ? v.coordinates.x_scale : v.coordinates.y_scale);
        const kind = safe(() => {
          const t = scale.type;
          return t === "LogScale" ? "log" : t === "LinearScale" ? "linear"
            : t === "CategoricalScale" ? "categorical" : t;
        });
        const tickPx = safe(() => ticks.map((t) => r1(scale.compute(t))));
        axes.push({side: safe(() => m.side ?? v.panel?.side), dim: dim, ticks: ticks,
                   labels: labels, title: safe(() => textOf(m.axis_label)),
                   scale: kind, tick_px: tickPx});
      } else if (m && v.glyph !== undefined && m.data_source !== undefined) {
        const gm = safe(() => v.glyph.model);
        const src = safe(() => m.data_source);
        // D56: the points a Scatter draws -- the rows its view keeps whose
        // x and y are both numbers -- and their extents.
        const drawn = safe(() => {
          if (gm.type !== "Scatter") return null;
          const xs = column(src, gm.x), ys = column(src, gm.y);
          if (!xs || !ys) return null;
          const keep = safe(() => Array.from(m.view.indices)) ||
            Array.from({length: xs.length}, (_, i) => i);
          const ok = keep.filter((i) => typeof xs[i] === "number" && isFinite(xs[i]) &&
                                        typeof ys[i] === "number" && isFinite(ys[i]));
          const ext = (a) => ok.length ? [Math.min(...ok.map((i) => a[i])),
                                          Math.max(...ok.map((i) => a[i]))] : null;
          return {n: ok.length, x: ext(xs), y: ext(ys)};
        });
        renderers.push({
          glyph: safe(() => gm.type),
          n: safe(() => src.get_length()),
          drawn: drawn,
          x: safe(() => extent(src, gm, gm.x !== undefined ? ["x"] : ["left", "right"])),
          y: safe(() => extent(src, gm, gm.y !== undefined ? ["y"] : ["top", "bottom"])),
          marker: safe(() => markerOf(gm, src)),
          fill: safe(() => written(gm.fill_color)),
          line: safe(() => written(gm.line_color)),
          line_width: safe(() => written(gm.line_width)),
          size: safe(() => gm.type === "Scatter" ? written(gm.size) : null),
          fill_alpha: safe(() => written(gm.fill_alpha)),
          line_alpha: safe(() => written(gm.line_alpha)),
          visible: safe(() => typeof m.visible === "boolean" ? m.visible : null),
        });
      }
      for (const k of kidsOf(v)) walk(k);
    };
    walk(pv);
    const titles = [];
    const tseen = new Set();
    const addTitle = (t, side) => {
      if (!t || tseen.has(t) || t.type !== "Title") return;
      tseen.add(t);
      titles.push({text: safe(() => textOf(t.text)), align: safe(() => t.align),
                   side: side});
    };
    safe(() => addTitle(pm.title, pm.title_location));
    for (const side of ["above", "below", "left", "right", "center"])
      for (const t of (safe(() => pm[side]) || [])) addTitle(t, side);
    const legend = [];
    for (const side of ["center", "above", "below", "left", "right"])
      for (const l of (safe(() => pm[side]) || []))
        if (l && l.type === "Legend")
          for (const it of (safe(() => l.items) || []))
            legend.push({label: safe(() => textOf(it.label)),
                         glyphs: safe(() => it.renderers.map((r) => r.glyph.type)) || []});
    return {id: safe(() => pm.id), bbox: safe(() => box(pv.bbox)),
            frame: safe(() => box(pv.frame.bbox)), axes: axes, titles: titles,
            legend: legend, renderers: renderers};
  };
  const figures = [];
  const seen = new Set();
  const walk = (v) => {
    if (!v || seen.has(v)) return;
    seen.add(v);
    if (isPlotView(v)) { figures.push(safe(() => figure(v), {id: safe(() => v.model.id)})); return; }
    for (const k of kidsOf(v)) walk(k);
  };
  for (const v of (safe(() => Object.values(Bokeh.index)) || [])) walk(v);
  return JSON.stringify({figures: figures});
}"""


class CorpusProbe(RangeProbe):
    """One headless Chrome that serves every page of a run (D-33-04.f)."""

    def __init__(self, path, chrome=None, timeout=60, ready=None):
        super().__init__(path, chrome=chrome, timeout=timeout)
        self.ready = ready or _READY_JS

    def __enter__(self):
        # RangeProbe.__enter__'s body, waiting for self.ready.
        if not self.chrome:
            raise RuntimeError("no Chrome binary (set DASH_CHROME)")
        port = _free_port()
        self._profile = tempfile.mkdtemp(prefix="dash_range_probe_")
        self._proc = subprocess.Popen(
            responsive_probe.chrome_argv(self.chrome) + [
             "--headless=new", "--no-first-run",
             "--no-default-browser-check", "--disable-gpu",
             "--user-data-dir=" + self._profile,
             "--remote-debugging-port=%d" % port,
             "--window-size=1200,900", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            url = self._page_ws(port)
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._ws = self._run(self._connect(url))
            self._send("Runtime.enable")
            self._send("Page.enable")
            self._send("Page.navigate", {"url": pathlib.Path(self.path).as_uri()})
            self._wait_for(self.ready)
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def navigate(self, path, ready=None):
        """Load path; waits until the old page is gone and ready holds; its title."""
        self.path = os.path.abspath(path)
        self._eval("window.__dashCorpusOld = true")
        self._send("Page.navigate", {"url": pathlib.Path(self.path).as_uri()})
        self._wait_for("!window.__dashCorpusOld && (%s)" % (ready or _READY_JS))
        return self._eval("document.title")

    def eval_async(self, expr):
        """expr's value, awaiting a promise; raises on an exception."""
        msg = self._send("Runtime.evaluate", {"expression": expr, "awaitPromise": True,
                                              "returnByValue": True})
        res = msg.get("result", {})
        if "exceptionDetails" in res:
            d = res["exceptionDetails"]
            raise RuntimeError((d.get("exception") or {}).get("description")
                               or d.get("text") or "evaluation failed")
        return res.get("result", {}).get("value")

    def viewport(self, w=None, h=None):
        """Emulate a w x h viewport; with no size, clear the emulation."""
        if w is None:
            self._send("Emulation.clearDeviceMetricsOverride")
        else:
            self._send("Emulation.setDeviceMetricsOverride",
                       {"width": int(w), "height": int(h), "deviceScaleFactor": 1,
                        "mobile": False})

    def errors_since(self, n):
        """The page exceptions after the first n."""
        return self.js_errors()[n:]


_ROOT_RE = re.compile(r"<svg\b[^>]*>", re.S)
_XML_DECL_RE = re.compile(r"^\s*<\?xml[^>]*\?>\s*")


def _num(x):
    s = ("%.4f" % x).rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def letterbox(svg, w, h):
    """svg scaled to fit w x h and centred in a w x h root (D-33-04.c)."""
    svg = _XML_DECL_RE.sub("", svg)
    root = _ROOT_RE.search(svg).group(0)
    dims = []
    for key in ("width", "height"):
        m = re.search(r'\s%s="\s*([0-9.]+)\s*(?:px)?\s*"' % key, root)
        dims.append(float(m.group(1)))
    iw, ih = dims
    s = min(w / iw, h / ih)
    dx, dy = (w - iw * s) / 2.0, (h - ih * s) / 2.0
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d"><g transform="translate(%s,%s) scale(%s)">%s</g></svg>'
            % (w, h, w, h, _num(dx), _num(dy), _num(s), svg))


_STROKE_TEXT_RE = re.compile(
    r'<text\b(?=[^>]*\sfill="none")[^>]*?(?:/>|>.*?</text>)', re.S)
_ID_RE = re.compile(r'(\sid=")([^"]*)(")')
_REF_RE = re.compile(r'(\sid=")([^"]*)(")|(url\(#)([^)]*)(\))|(\shref="#|\sxlink:href="#)([^"]*)(")')


def normalise_svg(text):
    """Drop Bokeh's stroke-only text copies and number every id in order (D-33-04.e)."""
    text = _STROKE_TEXT_RE.sub("", text)
    ids = {}
    for m in _ID_RE.finditer(text):
        ids.setdefault(m.group(2), "d%d" % (len(ids) + 1))

    def sub(m):
        for k in (1, 4, 7):
            if m.group(k) is not None:
                old = m.group(k + 1)
                return m.group(k) + ids.get(old, old) + m.group(k + 2)
        return m.group(0)
    return _REF_RE.sub(sub, text)


def export_page(probe, path, w, h):
    """{svg, view, size_matched, js_errors} of one saved page at w x h px."""
    n0 = len(probe.js_errors())
    probe.viewport(None, None)
    probe.navigate(path)
    info = probe.eval_async("(%s)(%d, %d)" % (SIZE_JS, w, h)) or {}
    lone = bool(info.get("lone"))
    if not lone:
        probe.viewport(w, 2000)
    time.sleep(SETTLE_S[1] if info.get("tex") else SETTLE_S[0])
    svg = probe.eval_async("(%s)()" % EXPORT_JS)
    if not svg:
        raise RuntimeError("the export returned no SVG")
    if not lone:
        svg = letterbox(svg, w, h)
    view = json.loads(probe.eval_async("(%s)()" % DUMP_JS) or "{}")
    return {"svg": svg, "view": view, "size_matched": lone,
            "js_errors": probe.errors_since(n0)}


def export_pages(pages, sizes, out_dir, probe=None):
    """Export each page (id -> saved page) at sizes[id] into out_dir; per-id results."""
    os.makedirs(out_dir, exist_ok=True)
    own, held, used, out = probe is None, probe, 0, {}
    try:
        for i in sorted(pages):
            w, h = sizes[i]
            try:
                if own and (held is None or used >= PAGES_PER_CHROME):
                    if held is not None:
                        held.__exit__(None, None, None)
                    held, used = CorpusProbe(pages[i], timeout=120).__enter__(), 0
                used += 1
                got = export_page(held, pages[i], w, h)
            except Exception as exc:  # noqa: BLE001 -- recorded per page
                out[i] = {"error": str(exc) or type(exc).__name__}
                if own and held is not None:
                    held.__exit__(None, None, None)
                    held = None
                continue
            svg = os.path.join(out_dir, i + ".svg")
            view = os.path.join(out_dir, i + ".view.json")
            with open(svg, "w", encoding="utf-8") as fh:
                fh.write(normalise_svg(got["svg"]))
            with open(view, "w", encoding="utf-8") as fh:
                json.dump(got["view"], fh, sort_keys=True, indent=2)
                fh.write("\n")
            out[i] = {"svg": svg, "view": view, "size_matched": got["size_matched"],
                      "js_errors": got["js_errors"], "w": w, "h": h}
    finally:
        if own and held is not None:
            held.__exit__(None, None, None)
    return out


def run_chrome(run_dir, only=None):
    """Export every saved page of <run_dir>/dash.jsonl at twoway's size; counts."""
    rows = _read_jsonl(os.path.join(run_dir, "dash.jsonl"))
    tw = {r["id"]: r for r in _read_jsonl(os.path.join(run_dir, "twoway.jsonl"))}
    pages, sizes = {}, {}
    for r in rows:
        if only is not None and r["id"] not in only:
            continue
        if r.get("rc") != 0 or not r.get("html"):
            continue
        t = tw.get(r["id"]) or {}
        # twoway's default 7.5 x 4.5 in when twoway drew nothing to size by.
        wi, hi = t.get("width_in") or 7.5, t.get("height_in") or 4.5
        pages[r["id"]] = os.path.join(run_dir, r["html"])
        sizes[r["id"]] = (int(round(wi * PX_PER_IN)), int(round(hi * PX_PER_IN)))
    got = export_pages(pages, sizes, os.path.join(run_dir, "dash"))
    for r in rows:
        g = got.get(r["id"])
        if g is None:
            continue
        for k in CHROME_KEYS:
            r[k] = None
        if "error" in g:
            r["export_error"] = twoway_run._hide_paths(g["error"], run_dir)
            continue
        r["svg"] = "dash/%s.svg" % r["id"]
        r["view"] = "dash/%s.view.json" % r["id"]
        r["js_errors"] = [twoway_run._hide_paths(e, run_dir) for e in g["js_errors"]]
        r.update(size_matched=g["size_matched"], w=g["w"], h=g["h"])
    _write_rows(run_dir, rows)
    ok = [g for g in got.values() if "error" not in g]
    return {"exported": len(ok), "size_matched": sum(g["size_matched"] for g in ok),
            "letterboxed": sum(not g["size_matched"] for g in ok),
            "errors": len(got) - len(ok)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, metavar="RUN_DIR")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=1800)
    ap.add_argument("--only", default=None, metavar="ID,ID")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--stata-only", action="store_true")
    g.add_argument("--chrome-only", action="store_true")
    a = ap.parse_args(argv)
    only = None if a.only is None else {s.strip() for s in a.only.split(",") if s.strip()}
    if not a.chrome_only:
        c = run_stata(a.run, jobs=a.jobs, timeout=a.timeout, only=only)
        print("corpus: dash rc0 %d, refused %d, skipped %d"
              % (c["rc0"], c["refused"], c["skipped"]))
    if not a.stata_only:
        c = run_chrome(a.run, only=only)
        print("corpus: dash exported %d (size-matched %d, letterboxed %d), errors %d"
              % (c["exported"], c["size_matched"], c["letterboxed"], c["errors"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
