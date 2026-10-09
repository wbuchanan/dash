"""
responsive_probe.py -- measure a saved dashboard page in headless Chrome at
exact viewport widths (TR-27.2).

Headless Chrome's window cannot be narrower than 500 px, so the page is
loaded into an iframe exactly *width* px wide inside a host page -- one
iframe per width, all in one Chrome run.  A probe script appended to the
dashboard walks the DOM, shadow roots included, after the page has laid
out, and posts to the host:

    W          the iframe's innerWidth (the viewport the page saw)
    sw         document.documentElement.scrollWidth -- > W means the page
               scrolls sideways
    canvases   the figure canvases (width >= 120, height >= 60), deduped
    kpis       the KPI cards (.db-kpi-card), deduped
    cells      for each retained KPI card (same order, same dedup as
               `kpis`): [cellWidth, cellHeight, cellClass] of the nearest
               ancestor -- crossing a shadow root via getRootNode().host --
               whose class list has one starting with `db-cell-h-`, or
               [-1, -1, ""] when none is found (WP-28 E14, TR-10.12)
    offscreen  how many canvases and cards reach past 0..W
    overlap    pairs of distinct canvases or cards that intersect by more
               than 2 px
    min_width  the narrowest canvas; min_height the shortest
    widths     the distinct canvas widths
    past       up to six elements whose right edge is past W (diagnostic)

The host page is dumped with ``--dump-dom``; Chrome does not always exit by
itself after a dump, so the output file is polled and the process killed.
Each run gets a fresh temporary profile directory, removed afterwards.
"""
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import time

#: Where Chrome is looked for, in order; DASH_CHROME overrides.
CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
)

PROBE_JS = r"""
<script>
window.addEventListener('load', () => setTimeout(() => {
  const c = [], k = [], kc = [];
  const cellOf = (start) => {
    let el = start.parentElement, cur = start;
    while (true) {
      if (!el) {
        const root = cur.getRootNode();
        if (root && root.host) { el = root.host; cur = el; continue; }
        return [-1, -1, ''];
      }
      const cls = [...(el.classList || [])].find(x => x.startsWith('db-cell-h-'));
      if (cls) { const r = el.getBoundingClientRect();
        return [Math.round(r.width), Math.round(r.height), cls]; }
      cur = el; el = el.parentElement;
    }
  };
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.tagName === 'CANVAS') { const r = el.getBoundingClientRect();
      if (r.width >= 120 && r.height >= 60) c.push([r.left, r.top, r.width, r.height]); }
    if (el.classList && el.classList.contains('db-kpi-card')) { const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) { k.push([r.left, r.top, r.width, r.height]);
        kc.push(cellOf(el)); } } } };
  walk(document);
  const same = (q, r) => Math.abs(q[0]-r[0]) < 1 && Math.abs(q[1]-r[1]) < 1
      && Math.abs(q[2]-r[2]) < 1 && Math.abs(q[3]-r[3]) < 1;
  const u = [], kk = [], cells = [];
  for (const r of c) if (!u.some(q => same(q, r))) u.push(r);
  for (let i = 0; i < k.length; i++) if (!kk.some(q => same(q, k[i]))) {
    kk.push(k[i]); cells.push(kc[i]); }
  const W = innerWidth;
  const all = u.concat(kk);
  const off = all.filter(r => r[0] < -1 || r[0] + r[2] > W + 1).length;
  let overlap = 0;
  for (let i = 0; i < all.length; i++) for (let j = i + 1; j < all.length; j++) {
    const a = all[i], b = all[j];
    const ix = Math.min(a[0]+a[2], b[0]+b[2]) - Math.max(a[0], b[0]);
    const iy = Math.min(a[1]+a[3], b[1]+b[3]) - Math.max(a[1], b[1]);
    if (ix > 2 && iy > 2) overlap++;
  }
  const past = [];
  const walk2 = (root) => { for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) walk2(el.shadowRoot);
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.right > W + 1 && past.length < 6)
      past.push(el.tagName.toLowerCase() + '.' + String(el.className || '').split(' ')[0]
                + ':' + Math.round(r.left) + '+' + Math.round(r.width)); } };
  walk2(document);
  const res = {W, sw: document.documentElement.scrollWidth, canvases: u.length,
    kpis: kk.length, cells, offscreen: off, overlap,
    min_width: u.length ? Math.round(Math.min(...u.map(r => r[2]))) : 0,
    min_height: u.length ? Math.round(Math.min(...u.map(r => r[3]))) : 0,
    widths: [...new Set(u.map(r => Math.round(r[2])))].sort((a, b) => a - b), past};
  parent.postMessage('DASHPROBE' + JSON.stringify(res), '*');
}, 2500));
</script>
"""

#: The host page: one iframe per width, stacked, each exactly that wide;
#: each posts its result, keyed by its innerWidth, into the <pre>.
HOST_HEAD = ("<html><body style='margin:0'><pre id='r'>pending</pre>"
             "<script>const R={};addEventListener('message',e=>{"
             "if(typeof e.data==='string'&&e.data.startsWith('DASHPROBE')){"
             "const o=JSON.parse(e.data.slice(9));R[o.W]=o;"
             "document.getElementById('r').textContent=JSON.stringify(R)}})"
             "</script>")
HOST_FRAME = ("<div><iframe src='page.html' style='width:%dpx;height:1100px;"
              "border:0'></iframe></div>")


def find_chrome():
    """The Chrome binary to drive, or None when there is none."""
    env = os.environ.get("DASH_CHROME", "")
    for cand in ((env,) if env else ()) + CHROME_CANDIDATES:
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    for name in ("google-chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    return None


#: The page's CSP <meta>, in the form dash writes it.
_CSP_META_RE = re.compile(
    r'(<meta\s+http-equiv="Content-Security-Policy"\s+content=")([^"]*)(")',
    re.I)


def admit_script(page_html, script_html):
    """*page_html* with *script_html* -- one complete script element --
    placed before ``</body>`` (or appended), and admitted under the page's
    own policy (WP-30 P1.29), so a probe still runs on a page that runs
    only the scripts it names.

    * A policy naming ``'nonce-X'`` (a served page): the element's opening
      tag gains ``nonce="X"``.
    * Else a script-src without ``'unsafe-inline'`` (a saved page): the
      element's own ``'sha256-...'`` (its text, LF line endings) goes
      first in that script-src.
    * No policy: nothing but the placement changes.

    Test-only: the page copy under test is edited, never dash's text.
    """
    import base64
    import hashlib
    m = _CSP_META_RE.search(page_html)
    if m:
        policy = m.group(2)
        nonce = re.search(r"'nonce-([A-Za-z0-9_-]+)'", policy)
        src = re.search(r"(?:^|;)\s*script-src\s([^;]*)", policy)
        if nonce:
            script_html = re.sub(r"<script(?=[\s>/])",
                                 '<script nonce="%s"' % nonce.group(1),
                                 script_html, count=1, flags=re.I)
        elif src and "'unsafe-inline'" not in src.group(1).split():
            a = re.search(r"<script(?=[\s>/])[^>]*>", script_html, re.I)
            b = script_html.lower().find("</script", a.end())
            body = script_html[a.end():b if b >= 0 else len(script_html)]
            body = body.replace("\r\n", "\n").replace("\r", "\n")
            digest = base64.b64encode(hashlib.sha256(
                body.encode("utf-8")).digest()).decode("ascii")
            policy = policy.replace("script-src ",
                                    "script-src 'sha256-%s' " % digest, 1)
            page_html = (page_html[:m.start(2)] + policy
                         + page_html[m.end(2):])
    i = page_html.rfind("</body>")
    if i < 0:
        return page_html + script_html
    return page_html[:i] + script_html + page_html[i:]


def with_probe(page_html):
    """*page_html* with the probe script placed before ``</body>``, and
    admitted under the page's policy (:func:`admit_script`)."""
    return admit_script(page_html, PROBE_JS)


def measure(page_html, width, chrome=None, timeout=90):
    """The probe's result for *page_html* at *width* px, as a dict."""
    return measure_many(page_html, (width,), chrome, timeout)[int(width)]


def measure_many(page_html, widths, chrome=None, timeout=90):
    """``{width: result}`` for *page_html* at each of *widths*, from one
    Chrome run.

    Raises RuntimeError when Chrome is missing or a width reported nothing
    within *timeout* seconds.
    """
    widths = [int(w) for w in widths]
    chrome = chrome or find_chrome()
    if chrome is None:
        raise RuntimeError("no Chrome binary")
    workdir = tempfile.mkdtemp(prefix="dash_resp_")
    try:
        with open(os.path.join(workdir, "page.html"), "w",
                  encoding="utf-8") as fh:
            fh.write(with_probe(page_html))
        host = os.path.join(workdir, "host.html")
        with open(host, "w", encoding="utf-8") as fh:
            fh.write(HOST_HEAD + "".join(HOST_FRAME % w for w in widths)
                     + "</body></html>")
        out = os.path.join(workdir, "out.html")
        prof = tempfile.mkdtemp(prefix="prof_", dir=workdir)
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check", "--allow-file-access-from-files",
               "--user-data-dir=" + prof,
               "--window-size=%d,1100" % max(1500, max(widths) + 60),
               "--virtual-time-budget=9000", "--dump-dom",
               "file://" + host]
        with open(out, "w") as fo, open(os.devnull, "w") as fe:
            proc = subprocess.Popen(cmd, stdout=fo, stderr=fe)
            t0 = time.time()
            try:
                while time.time() - t0 < timeout:
                    time.sleep(0.3)
                    with open(out, encoding="utf-8", errors="replace") as fh:
                        if "</html>" in fh.read() or proc.poll() is not None:
                            break
            finally:
                if proc.poll() is None:
                    proc.kill()
                proc.wait()
        with open(out, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        m = re.search(r'<pre id="r">(.*?)</pre>', text, re.S)
        got = {}
        if m and m.group(1).startswith("{"):
            got = {int(k): v for k, v in
                   json.loads(html.unescape(m.group(1))).items()}
        missing = [w for w in widths if w not in got]
        if missing:
            raise RuntimeError("the probe reported nothing at %s px: %r"
                               % (missing, (m.group(1) if m else text)[:200]))
        return got
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
