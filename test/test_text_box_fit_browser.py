"""
test_text_box_fit_browser.py -- text()'s fixed box (width(), height(),
WP-43 LT-20) is fitted in the browser.

The defect: ``_DASH_TEXT_BOX_JS`` split the text into lines with
``.split("\\n")`` written in a plain Python string, so the page received a
raw newline inside a JavaScript string literal.  The callback never
compiled, BokehJS logged a SyntaxError, and every box kept the padding of
its margin: ``text(30 3000 "Peak" "two", box width(40))`` was drawn as
wide as its text, where twoway draws it 40 relative units wide.

Read in headless Chrome over CDP: the callback's code is compiled with
``new Function``, page errors are counted from before the first script,
and the Label's padding is read once the page has settled.  Without
Chrome these tests skip.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
import test_added_text as tat  # noqa: E402
import test_by_axes_keys as bk  # noqa: E402
import test_by_axes_keys_browser as bkb  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

from scripts.corpus import dash_run  # noqa: E402

# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release

#: Page errors from the first script on (CDP, so the page's CSP does not
#: apply).
_ERRORS_JS = r"""
window.__dashErrors = [];
window.addEventListener("error", (e) => {
  window.__dashErrors.push(String(e.message || e.error));
});
const dashOwnError = console.error;
console.error = function (...a) {
  window.__dashErrors.push(a.map(String).join(" "));
  return dashOwnError.apply(this, a);
};
"""

#: [does the box callback compile, the Peak Label's padding].
_READ_JS = r"""new Promise((resolve) => setTimeout(() => {
  const models = [];
  for (const d of Bokeh.documents) { for (const m of d.all_models) models.push(m); }
  const cb = models.find((m) => m.type === "CustomJS"
                         && String(m.code).includes("text_line_height"));
  let compiles = null;
  if (cb != null) {
    try { new Function(cb.code); compiles = true; }
    catch (e) { compiles = String(e); }
  }
  const lab = models.find((m) => m.type === "Label"
                          && String(m.text).startsWith("Peak"));
  resolve([compiles, lab == null ? null : lab.padding]);
}, 1500))"""


def _box(mode, opts, tmp_path):
    """(page errors, [compiles, padding]) of one graph holding
    text(30 3000 "Peak" "two", <opts>)."""
    go = {"added_text": [tat._at(30, 3000, ["Peak", "two"], opts)],
          "added_text_n": "1"}
    spec = bk._spec([bk._graph("g0", bk._ONE, go)])
    page = tmp_path / ("%s_box.html" % mode)
    page.write_text(bkb._page(mode, spec), encoding="utf-8")
    blank = tmp_path / "blank.html"
    blank.write_text("<html><body></body></html>", encoding="utf-8")
    probe = dash_run.CorpusProbe(
        str(blank), timeout=300,
        ready="document.readyState === 'complete'").__enter__()
    try:
        probe._send("Page.addScriptToEvaluateOnNewDocument",
                    {"source": _ERRORS_JS})
        probe.navigate(str(page))
        got = probe.eval_async(_READ_JS)
        return probe._eval("window.__dashErrors"), got
    finally:
        probe.__exit__(None, None, None)


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_a_fixed_width_box_is_fitted(mode, tmp_path):
    """The box callback compiles and runs: no page error, and width(40)
    widens the padding past the plain box's on both sides (the spare
    width split by the text's centre justification)."""
    errors, (compiles, pad) = _box(mode, "box width(40)", tmp_path)
    assert compiles is True, compiles
    assert errors == [], errors
    _e0, (_c0, plain) = _box(mode, "box", tmp_path)
    assert pad is not None and plain is not None
    plain = plain if isinstance(plain, dict) else {k: plain for k in (
        "left", "right", "top", "bottom")}
    assert pad["left"] > plain["left"] + 10, (pad, plain)
    assert pad["right"] > plain["right"] + 10, (pad, plain)
    assert abs(pad["left"] - pad["right"]) <= 1, pad
    assert pad["top"] == plain["top"] and pad["bottom"] == plain["bottom"]
