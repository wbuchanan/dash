"""
range_probe.py -- read a Bokeh page's figure ranges from headless Chrome in
real time, over the DevTools protocol (WP-29 S10, P0.2, TR-10.21).

A by() graph's panels share one DataRange1d per axis; what the shared range
spans is decided by BokehJS (``DataRange1d.update`` unions the bounds of
every plot that shares it), which no Python model can show.  So the page is
loaded into a real Chrome, a filter is moved the way a user moves it (its
widget's ``value`` set from the page's own JavaScript, so its own callbacks
run), and the ranges BokehJS settles on are read back -- in real time, as a
browser repaints, never by forcing an update.

``responsive_probe.py`` reads a page once, under virtual time with
``--dump-dom``, which cannot observe a repaint after a move; this probe
keeps one page open and asks it again.

    with RangeProbe("/path/page.html") as p:
        before = p.wait_settled(3)
        p.move_range_slider(0.3)
        after = p.wait_settled(3)
        assert p.js_errors() == []

Chrome is ``responsive_probe.find_chrome()``'s; each probe gets a fresh
profile directory and a free local port, and kills Chrome and removes the
profile on exit.  The connection is tornado's websocket client.
"""
import asyncio
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request

import responsive_probe

#: The page's figures: [title, y.start, y.end, x.start, x.end, y range id,
#: x range id], one per model with an x_range, a y_range and renderers,
#: in document order.
_RANGES_JS = r"""
(() => {
  const out = [];
  for (const d of (window.Bokeh ? Bokeh.documents : [])) {
    for (const m of d.all_models) {
      if (m && m.x_range !== undefined && m.y_range !== undefined
          && m.renderers !== undefined && m.toolbar !== undefined) {
        const t = m.title && m.title.text !== undefined ? m.title.text : "";
        out.push([String(t), m.y_range.start, m.y_range.end,
                  m.x_range.start, m.x_range.end,
                  String(m.y_range.id), String(m.x_range.id)]);
      }
    }
  }
  return JSON.stringify(out);
})()
"""

#: Every RangeSlider set to [start, start + fraction * (end - start)].
_MOVE_JS = r"""
((fraction) => {
  let n = 0;
  for (const d of (window.Bokeh ? Bokeh.documents : [])) {
    for (const m of d.all_models) {
      if (m && m.constructor && m.constructor.__name__ === "RangeSlider") {
        m.value = [m.start, m.start + fraction * (m.end - m.start)];
        n += 1;
      }
    }
  }
  return n;
})
"""

#: Every RangeSlider moved as _MOVE_JS moves it, the clock started once the
#: models are found; resolves with the milliseconds until every figure's y
#: range has left its old value and all agree, read once per animation
#: frame (or -1 at the timeout).  BokehJS updates the ranges itself.
_MOVE_TIMED_JS = r"""
((fraction, timeout_ms) => new Promise((resolve) => {
  const sliders = [], plots = [];
  for (const d of (window.Bokeh ? Bokeh.documents : [])) {
    for (const m of d.all_models) {
      if (m && m.constructor && m.constructor.__name__ === "RangeSlider") sliders.push(m);
      if (m && m.x_range !== undefined && m.y_range !== undefined
          && m.renderers !== undefined && m.toolbar !== undefined) plots.push(m);
    }
  }
  const key = () => plots.map(p => p.y_range.start + "," + p.y_range.end);
  const old = key();
  const t0 = performance.now();
  for (const m of sliders) m.value = [m.start, m.start + fraction * (m.end - m.start)];
  const tick = () => {
    const k = key();
    const done = k.every(v => v === k[0]) && k.some((v, i) => v !== old[i]);
    const ms = performance.now() - t0;
    if (done) return resolve(ms);
    if (ms > timeout_ms) return resolve(-1);
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}))
"""

_READY_JS = ("document.readyState === 'complete' && !!window.Bokeh && "
             "Bokeh.documents.length > 0")


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


class RangeProbe:
    """One page held open in headless Chrome, read over DevTools."""

    def __init__(self, path, chrome=None, timeout=60):
        self.path = os.path.abspath(path)
        self.chrome = chrome or responsive_probe.find_chrome()
        self.timeout = timeout
        self._proc = None
        self._profile = None
        self._loop = None
        self._ws = None
        self._seq = 0
        self._errors = []

    # ---- lifecycle --------------------------------------------------------
    def __enter__(self):
        if not self.chrome:
            raise RuntimeError("no Chrome binary (set DASH_CHROME)")
        port = _free_port()
        self._profile = tempfile.mkdtemp(prefix="dash_range_probe_")
        self._proc = subprocess.Popen(
            [self.chrome, "--headless=new", "--no-first-run",
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
            self._send("Page.navigate", {"url": "file://" + self.path})
            self._wait_for(_READY_JS)
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *exc):
        try:
            if self._ws is not None:
                self._ws.close()
        finally:
            self._ws = None
            if self._loop is not None:
                self._loop.close()
                asyncio.set_event_loop(None)
                self._loop = None
            if self._proc is not None:
                self._proc.kill()
                try:
                    self._proc.wait(10)
                except subprocess.TimeoutExpired:
                    pass
                self._proc = None
            if self._profile:
                shutil.rmtree(self._profile, True)
                self._profile = None
        return False

    def _page_ws(self, port):
        end = time.time() + self.timeout
        while time.time() < end:
            try:
                with urllib.request.urlopen(
                        "http://127.0.0.1:%d/json" % port, timeout=2) as r:
                    targets = json.loads(r.read().decode("utf-8"))
                for t in targets:
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                        return t["webSocketDebuggerUrl"]
            except (OSError, ValueError):
                pass
            time.sleep(0.1)
        raise RuntimeError("Chrome's DevTools endpoint did not answer")

    # ---- the protocol -----------------------------------------------------
    def _run(self, coro):
        return self._loop.run_until_complete(
            asyncio.wait_for(coro, self.timeout))

    async def _connect(self, url):
        from tornado.websocket import websocket_connect
        return await websocket_connect(url, max_message_size=1 << 28)

    async def _call(self, method, params):
        self._seq += 1
        mid = self._seq
        await self._ws.write_message(json.dumps(
            {"id": mid, "method": method, "params": params or {}}))
        while True:
            raw = await self._ws.read_message()
            if raw is None:
                raise RuntimeError("Chrome closed the DevTools connection")
            msg = json.loads(raw)
            if msg.get("method") == "Runtime.exceptionThrown":
                d = msg.get("params", {}).get("exceptionDetails", {})
                self._errors.append(
                    (d.get("exception") or {}).get("description")
                    or d.get("text") or "exception")
            if msg.get("id") == mid:
                return msg

    def _send(self, method, params=None):
        return self._run(self._call(method, params))

    def _eval(self, expression):
        msg = self._send("Runtime.evaluate",
                         {"expression": expression, "returnByValue": True})
        res = msg.get("result", {})
        if "exceptionDetails" in res:
            d = res["exceptionDetails"]
            raise RuntimeError((d.get("exception") or {}).get("description")
                               or d.get("text") or "evaluation failed")
        return res.get("result", {}).get("value")

    def _wait_for(self, expression):
        end = time.time() + self.timeout
        while time.time() < end:
            if self._eval(expression):
                return
            time.sleep(0.1)
        raise RuntimeError("the page did not load: " + expression)

    # ---- what a test reads ------------------------------------------------
    def ranges(self):
        """``[[title, y.start, y.end, x.start, x.end, y id, x id], ...]``."""
        return json.loads(self._eval(_RANGES_JS) or "[]")

    def move_range_slider(self, fraction):
        """Move every RangeSlider's upper handle to *fraction* of its span,
        as a user's drag would; returns how many were moved."""
        return self._eval("(%s)(%r)" % (_MOVE_JS.strip(), float(fraction)))

    def move_and_time(self, fraction, timeout=3.0):
        """Move every RangeSlider as :meth:`move_range_slider` does and
        return the seconds, measured in the page, until every figure's y
        range has moved and all agree (BokehJS's own update, read once per
        animation frame); None when that does not happen by *timeout*."""
        msg = self._send("Runtime.evaluate", {
            "expression": "(%s)(%r, %r)" % (_MOVE_TIMED_JS.strip(),
                                           float(fraction),
                                           float(timeout) * 1000.0),
            "awaitPromise": True, "returnByValue": True})
        ms = msg.get("result", {}).get("result", {}).get("value")
        return None if ms is None or ms < 0 else ms / 1000.0

    def wait_settled(self, timeout=3.0):
        """The ranges once two readings 100 ms apart agree (and every range
        has a start and an end), or the last reading at *timeout*."""
        end = time.time() + timeout
        last = None
        while True:
            cur = self.ranges()
            done = all(r[1] is not None and r[2] is not None for r in cur)
            if done and cur == last:
                return cur
            if time.time() >= end:
                return cur
            last = cur
            time.sleep(0.1)

    def js_errors(self):
        """Every exception the page threw, as Chrome described it."""
        self._send("Runtime.evaluate", {"expression": "0"})
        return list(self._errors)
