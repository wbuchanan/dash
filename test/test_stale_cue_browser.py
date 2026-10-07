"""The saved page's stale cue as BokehJS draws it (WP-29 P0.17).

Node runs the page's script against stand-ins; whether ``renderer.muted``,
``Title.visible`` and ``LegendItem.label = {value}`` do what the cue needs
is only proved in a browser.  Each case builds the saved page of a scatter
and an lfit with a ``foreign`` dropdown, appends a probe script, and runs
headless Chrome with ``--dump-dom``.  The probe snapshots the page, moves
the dropdown to Foreign, snapshots again, moves it back, and snapshots a
third time, in both layouts and both filter positions.

Chrome is found as ``test/responsive_probe.py`` finds it (``DASH_CHROME``
first).  Without it these tests skip, and a skip is red under
``DASH_STRICT=1``.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import responsive_probe  # noqa: E402

#: Headless Chrome: the release tier, not the default run (WP-30 D).
pytestmark = pytest.mark.release
from test_mode_parity import _spec  # noqa: E402
from test_saved_filter_layers import _write  # noqa: E402
from test_mode_parity import _DF  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_PROBE = r"""
<script>
(function () {
  function snap() {
    const out = {muted: [], caption: [], labels: [], status: null};
    for (const doc of window.Bokeh.documents) {
      for (const m of doc.all_models) {
        const t = m.constructor.__name__ || m.type;
        if (m.type === "GlyphRenderer" || t === "GlyphRenderer") {
          if (m.glyph && (m.glyph.type === "Line")) out.muted.push(m.muted);
        } else if (m.type === "Title" || t === "Title") {
          if ((m.tags || []).indexOf("dash_stale_cue") >= 0)
            out.caption.push(m.visible);
        } else if (m.type === "LegendItem" || t === "LegendItem") {
          const lab = m.label;
          out.labels.push(lab && typeof lab === "object" && "value" in lab
                          ? lab.value : lab);
        }
      }
    }
    function walk(root) {
      if (!root) return null;
      const hit = root.querySelector && root.querySelector('[role="status"]');
      if (hit) return hit.textContent;
      const all = root.querySelectorAll ? root.querySelectorAll("*") : [];
      for (const el of all) {
        if (el.shadowRoot) {
          const r = walk(el.shadowRoot);
          if (r !== null) return r;
        }
      }
      return null;
    }
    out.status = walk(document);
    return out;
  }
  function select() {
    for (const doc of window.Bokeh.documents)
      for (const m of doc.all_models)
        if (m.type === "Select") return m;
    return null;
  }
  function wait() {
    if (!window.Bokeh || !window.Bokeh.documents ||
        !window.Bokeh.documents.length || !select()) {
      setTimeout(wait, 100);
      return;
    }
    setTimeout(function () {
      const res = {before: snap()};
      const sel = select();
      const opt = sel.options.find((o) => (Array.isArray(o) ? o[1] : o)
                                    === "Foreign");
      sel.value = Array.isArray(opt) ? opt[0] : opt;
      setTimeout(function () {
        res.after = snap();
        const first = sel.options[0];
        sel.value = Array.isArray(first) ? first[0] : first;
        setTimeout(function () {
          res.back = snap();
          const pre = document.createElement("pre");
          pre.id = "r";
          pre.textContent = JSON.stringify(res);
          document.body.appendChild(pre);
        }, 300);
      }, 300);
    }, 500);
  }
  wait();
})();
</script>
"""


def _page(layout, pos):
    spec = _spec([plot_for("scatter"), plot_for("lfit")],
                 {"filter": "foreign, type(dropdown)", "layout": layout,
                  "filter_position": pos},
                 {"title": "T", "subtitle": "S", "legend": "position(12)"})
    sp, dp = _write(spec, _DF)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        page = dr.DashRenderer(sp, dp).render()
    # Admitted under the page's own policy, which runs only the scripts it
    # names (WP-30 P1.29).
    return responsive_probe.admit_script(page, _PROBE)


def _run_chrome(page, timeout=90):
    chrome = responsive_probe.find_chrome()
    work = tempfile.mkdtemp(prefix="dash_stale_")
    try:
        path = os.path.join(work, "page.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(page)
        out = os.path.join(work, "out.html")
        prof = tempfile.mkdtemp(prefix="prof_", dir=work)
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check", "--allow-file-access-from-files",
               "--user-data-dir=" + prof, "--virtual-time-budget=9000",
               "--dump-dom", "file://" + path]
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
        assert m, "the probe reported nothing: %r" % text[-300:]
        return json.loads(html.unescape(m.group(1)))
    finally:
        shutil.rmtree(work, ignore_errors=True)


class TestInChrome:

    @pytest.mark.parametrize("layout,pos", [("auto", "top"),
                                            ("auto", "left"),
                                            ("bs", "top"), ("bs", "left")],
                             ids=["auto-top", "auto-left", "bs-top",
                                  "bs-left"])
    def test_bokehjs_marks_and_clears(self, layout, pos):
        if responsive_probe.find_chrome() is None:
            pytest.skip("headless Chrome is not installed; set DASH_CHROME "
                        "(a skip is red under DASH_STRICT=1)")
        got = _run_chrome(_page(layout, pos))
        text = re.sub("<[^>]+>", "", dr._DASH_STALE_STATUS_HTML) \
            if hasattr(dr, "_DASH_STALE_STATUS_HTML") else None
        b, a, k = got["before"], got["after"], got["back"]
        assert (b["muted"], b["caption"]) == ([False], [False]), b
        assert "Fitted values" in b["labels"], b
        assert b["status"] is None, b
        assert (a["muted"], a["caption"]) == ([True], [True]), a
        assert "Fitted values (unfiltered)" in a["labels"], a
        assert a["status"] == text, a
        assert (k["muted"], k["caption"]) == ([False], [False]), k
        assert "Fitted values" in k["labels"], k
        assert "Fitted values (unfiltered)" not in k["labels"], k
        assert k["status"] is None, k
