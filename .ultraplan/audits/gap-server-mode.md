# Audit: `dash_render.py` lines 7800–10455 (`ServerAppBuilder`) + `dash.ado` server paths

Scope: `ServerAppBuilder` (dash_render.py:7738–10328), the generated app's rate limiter /
`/health` handler, the `__main__` launcher (dash_render.py:10367–10455), `dash.ado`
`_dash_build` server branch + `_dash_serve` (dash.ado:1158–1649), and `dash.sthlp`.

All findings were verified against the code. Empirical verification was performed by
generating an app from a synthetic spec and running it under both launch paths
(bokeh 3.9.0, Python 3.14). Evidence is noted inline where it exists.

---

## EXECUTIVE SUMMARY — the one thing that matters

**`bokeh serve <app.py>` serves a completely empty document, and `/health` returns 404.**
This is the launch path that `dash serve` actually uses (dash_render.py:10419), that
`dash.ado` instructs users to use (dash.ado:1471), and that `dash.sthlp` documents
(dash.sthlp:438). Every feature in the 2,600 lines audited is unreachable through it.

The generated file wires `make_document` to a `Server` only inside
`if __name__ == '__main__':` (dash_render.py:10305–10313). Bokeh's `CodeRunner` executes
an app script under a synthetic module name (`bokeh_app_<uuid>`,
`bokeh/application/handlers/code_runner.py:185`), never `__main__`, and the generated file
never calls `curdoc()` — grep for `curdoc` in dash_render.py returns zero hits. So under
`bokeh serve` the module defines `make_document` and exits; nothing is added to the
document, and `extra_patterns=[('/health', _HealthHandler)]` (dash_render.py:10312) is
never registered.

Empirical confirmation:

```
$ python3 -m bokeh serve app.py --port 5199
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:5199/health   → 404
$ curl -s http://localhost:5199/app | grep -A1 'application/json'
      <script type="application/json" id="ff87f30c-...">
      {}                     ← docs_json is EMPTY
$ grep -c MyTitle app.html   → 0
```

Running the same file as `python app.py` works correctly (`/health` → `200
{"status": "ok", "timestamp": "2026-09-18T15:04:32Z"}`, page contains the title). Only the
`bokeh serve` path is broken — and it is the only path any documented workflow uses.

---

# JOB 1 — Hardcoded values

## 1.1 Port / host / websocket origin

| # | Finding | Citation | Sev |
|---|---|---|---|
| 1 | `main()` calls `builder.build(output_path)` and **never forwards `args.port`**, so the generated file's `__main__` always embeds `_port = 5006` regardless of `--port`. Verified: `--port 7777` → subprocess runs on 7777 but generated `p2.py` contains `_port = 5006`. A user who ships `app.py` and later runs `python app.py` gets 5006, not the port they asked for. | `dash_render.py:10356` (call), `:7779` (`port: int = 5006`), `:10306` (`f"    _port = {port}"`) | **HIGH** |
| 2 | `build()` reads an override from `build_options["port"]` — but **no code path ever writes that key**. `dash.ado:1433` (build) and `dash.ado:1603` (serve) both emit `build_options` without `port`. Dead code. | `dash_render.py:7786–7792`; `dash.ado:1433`, `:1603` | MEDIUM |
| 3 | `allow_websocket_origin` is hardcoded to `localhost:<port>` in **both** the embedded server (`allow_websocket_origin=[f'localhost:{_port}']`) and the `bokeh serve` subprocess (`"--allow-websocket-origin", f"localhost:{_port}"`). No user option. A user reaching the dashboard at `127.0.0.1:5006`, via hostname, or over a LAN gets a websocket rejection and a permanently blank page. `dash serve` has no `host()`/`origin()` option (`dash.ado:1487`). | `dash_render.py:10310`, `:10422` | **HIGH** |
| 4 | Listen address is never specified — Bokeh's default binds all interfaces. Combined with #3 the app is *reachable* from the network but *unusable* there. No `address`/`bind` option exists. | `dash_render.py:10307–10313`, `:10418–10423` | MEDIUM |
| 5 | `num_procs=1` hardcoded. | `dash_render.py:10311` | LOW |
| 6 | Browser URL hardcoded to `http://localhost:{_port}` (scheme + host). | `dash_render.py:10439`, `:10316–10317` | LOW |
| 7 | Port clamp `max(1024, min(args.port, 65535))` silently coerces instead of erroring. `dash serve` validates first (`dash.ado:1492–1497`) so it is unreachable there, but `dash build ... server` and direct CLI use hit it. | `dash_render.py:10417` | LOW |

## 1.2 Timing constants

| # | Finding | Citation | Sev |
|---|---|---|---|
| 8 | `_time.sleep(1.5)` before `webbrowser.open()` — a fixed guess with no readiness probe. On a cold `bokeh serve` start (import of pandas/scipy/bokeh + base64 decode of the whole dataset) 1.5 s is frequently too short; the user gets a connection-refused tab. Not user-tunable. | `dash_render.py:10437–10441` | MEDIUM |
| 9 | `_RateLimiter._window = 60.0` seconds — hardcoded, not derived from `_RATE_LIMIT_RPM` and not user-settable. | `dash_render.py:7932` | MEDIUM |
| 10 | `--timeout` is honoured (`_time.sleep(args.timeout * 60)` then `_proc.terminate()`), so `dash serve, timeout()` **does** reach the launcher — but only as a whole-process kill. There is no per-session timeout, no `--unused-session-lifetime`, no `--session-token-expiration`. | `dash_render.py:10444–10449`; `dash.ado:1644` | LOW (works as a blunt instrument) |
| 11 | `--timeout` is **not** passed by `_dash_do_render`, so `dash build ... server` always gets `timeout=0` = block forever. See JOB 2 BLOCKER-2. | `dash.ado:142` | **HIGH** |

## 1.3 Rate limiter

| # | Finding | Citation | Sev |
|---|---|---|---|
| 12 | `_RATE_LIMIT_RPM = 60` (session), `_HEALTH_LIMIT_RPM = 600` (health), `_MAX_IPS = 10000`, `_RateLimiter.__init__(max_rpm=60)`, window `60.0` — every parameter is a literal in the emitted source. No `dash serve` option and no `build_options` key exposes any of them. | `dash_render.py:7921`, `:7922`, `:7929`, `:7930`, `:7932` | MEDIUM |
| 13 | **X-Forwarded-For is trusted unconditionally.** `_client_ip_from_request` returns the first XFF token with no trusted-proxy allowlist. Any client can send `X-Forwarded-For: <random>` on each request and bypass the limiter entirely. The trusted-proxy set is exactly the kind of thing that must be configuration, not a literal. | `dash_render.py:7965–7982` (esp. `:7975–7979`) | **HIGH** (security) |
| 14 | Eviction comment says "evicts the oldest tracked IP" but `next(iter(self._store))` returns the *first-inserted* key; reassigning `self._store[ip] = ts` does not reorder a dict. Under churn this can evict an actively rate-limited IP, resetting its budget. | `dash_render.py:7947–7950` vs comment `:7926–7929` | LOW |
| 15 | `ts.pop(0)` on a list is O(n) per prune; `import collections as _collections` is emitted (`:7916`) and never used — a `deque` was evidently intended. Verified in generated output: `grep -c _collections app.py` → 1 (the import line only). | `dash_render.py:7916`, `:7941–7942` | LOW |
| 16 | The rate limiter and the 429 Div are **entirely dead under `bokeh serve`** because `make_document` is never invoked. All of §1.3 is unreachable in the shipped launch path. | `dash_render.py:8353–8367` + BLOCKER-1 | (see BLOCKER-1) |

## 1.4 `/health` response shape and timestamp

| # | Finding | Citation | Sev |
|---|---|---|---|
| 17 | Response body is a hand-built JSON string literal: `'{"status": "ok", "timestamp": "' + ts + '"}'`. No app version, bokeh version, uptime, session count, or dataset row count — nothing that makes a health check diagnostic. Shape is not configurable. | `dash_render.py:7996–7999` | MEDIUM |
| 18 | Timestamp uses `datetime.utcnow()`, deprecated since Python 3.12 and scheduled for removal. Confirmed at runtime: `app.py:131: DeprecationWarning: datetime.datetime.utcnow() is deprecated`. Format `%Y-%m-%dT%H:%M:%SZ` is second-granularity and tz-naive. | `dash_render.py:7998` | MEDIUM |
| 19 | The 429 body is a second hand-built literal with a different shape (`status`/`message`) from the 200 body (`status`/`timestamp`). Two divergent response schemas on one endpoint. | `dash_render.py:7993` vs `:7999` | LOW |
| 20 | `/health` path is a literal in `extra_patterns`; no option to relocate or disable it. And it is only registered in the `__main__` block → **404 under `bokeh serve`** (verified). | `dash_render.py:10312` | **HIGH** |

## 1.5 Hardcoded module-scope imports

| # | Finding | Citation | Sev |
|---|---|---|---|
| 21 | `from scipy import stats as scipy_stats` at module scope, **unguarded**. Every generated app hard-requires scipy even when the dashboard contains only a scatter plot. The standalone renderer imports scipy lazily inside the methods that need it (`dash_render.py:2404`, `:3055`, `:4001`). Straight divergence. | `dash_render.py:7882` | **HIGH** |
| 22 | statsmodels is soft-guarded, but the fallback is a **silent wrong answer**: when statsmodels is absent `_compute_lowess` returns the raw `(x, y)` points as the "lowess curve" — it draws a jagged connect-the-dots line labelled as a smoother, with no warning. The standalone path imports statsmodels unguarded (`:2547`) and raises. Opposite failure modes for the same missing dependency. | `dash_render.py:7883–7887`, `:8144–8148` | **HIGH** |
| 23 | `IndexFilter` imported and never used in the generated app (`grep -c IndexFilter app.py` → 1, the import line). | `dash_render.py:7900` | LOW |

## 1.6 Statistical constants that should come from user input

| # | Finding | Citation | Sev |
|---|---|---|---|
| 24 | LOWESS bandwidth hardcoded `frac=0.5`; `bwidth()` is never read. Standalone uses `float(options.get("bwidth", "0.8"))` — **Stata's actual default is 0.8**. Same command, two different smoothers. | `dash_render.py:8145` vs `:2559–2561` | **HIGH** |
| 25 | CI level hardcoded to 95% in two places (`t.ppf(0.975, ...)`). No `level()` support. | `dash_render.py:8101`, `:8123` | MEDIUM |
| 26 | lfit/qfit evaluate on `np.linspace(min, max, 100)` with no range padding. Standalone uses **200** points with **10 % padding** on each side (`x.min() - 0.1*dx`). Fit lines are visibly shorter and coarser in server mode. | `dash_render.py:8072`, `:8082` vs `:2324`, `:2371` | MEDIUM |
| 27 | kdensity: server uses 200 points over `[min, max]` with scipy's default bandwidth; standalone uses **400** points over `[min − 3bw, max + 3bw]` with an explicit bandwidth. Different curves, different support. | `dash_render.py:8135` vs `:3069` | MEDIUM |
| 28 | mband band count `np.clip(ceil(n/5), 2, 20)` — hardcoded, and **re-implemented inline twice more** in the facet and total loops with the same literals. | `dash_render.py:8263`, `:9744`, `:9843` | MEDIUM |
| 29 | `_compute_lpoly(bwidth=0.5, degree=0, n_grid=200)` defaults; grid sizes `200` for lfitci/qfitci/fpfit/mspline. | `dash_render.py:8151`, `:8175`, `:8096`, `:8117`, `:8233`, `:8248` | LOW |
| 30 | Histogram: default `bins=20` in `_compute_histogram` and in the `bin()` fallback at `:8810`. **Standalone defaults to 10** (`options.get("bin", 10)`). Same `dash histogram` command → different bar counts in HTML vs server. | `dash_render.py:8056`, `:8810` vs `:3001` | **HIGH** |
| 31 | In `by()` facet and `by(total)` panels the histogram bin count is **hardcoded to 20 and the user's `bin()` option is discarded**: `_compute_histogram(_fac_gdf, _hvar)` with no bins argument, and the agg record stores `'bins': 20`. A faceted histogram therefore uses different bins than the same unfaceted histogram. | `dash_render.py:9692–9694`, `:9791–9793` | **HIGH** |
| 32 | `lpoly` in facet/total paths uses `float(opts.get('bwidth', 0.5))` with **no clamping and no try/except**, unlike the main loop (`:8868–8873`). A non-numeric `bwidth()` raises `ValueError` and kills document creation for the whole dashboard. | `dash_render.py:9718–9719`, `:9817–9818` | MEDIUM |

## 1.7 Hardcoded colors, sizes, CSS, layout — and where they DIVERGE from standalone

| # | Finding | Citation | Sev |
|---|---|---|---|
| 33 | **Default series color is `'#1f77b4'`** (matplotlib's default), hardcoded in three places. The standalone renderer resolves every default through `self.scheme.default_color(color_idx, <glyph>)` driven by a parsed Stata `.scheme` file (`SchemeParser`, `dash_render.py:688`). The generated app contains **no `SchemeParser` and no scheme logic at all** — `scheme()`/`theme()` are completely inert in server mode. Also, because the literal is per-plot-index-blind, **every series in a multi-plot graph gets the same color** unless the user sets `mcolor()`/`lcolor()` explicitly. | `dash_render.py:8678`, `:9680`, `:9778`; contrast `:4990–5006`, `:1965` | **HIGH** |
| 34 | **KPI card CSS is hardcoded three times inside the generated app** (initial build, filter callback, brush callback) and **diverges from the standalone card**. | | **HIGH** |
| | *server:* `padding:16px`, no border, no min-width/min-height, value `font-size:28px`, title `color:#888`, subtitle `color:#aaa`, default text `#333333` | `dash_render.py:9869–9876`, `:10183–10190`, `:10222–10229` | |
| | *standalone:* `padding:20px`, `border:1px solid #dee2e6`, `min-width:160px; min-height:110px`, value `font-size:36px`, title/subtitle `color:#6c757d`, default text `#212529` | `dash_render.py:6293–6300`, `:4542–4548` | |
| 35 | KPI `color`/`bgcolor` are interpolated into `style="…"` with `html.escape()` only. The standalone *filter-callback* path routes them through `_sanitize_css_color(…)` (`dash_render.py:4356`, used at `:7292`, `:7295`). The generated app has **no CSS sanitizer anywhere** — `bgcolor("red;background-image:url(//evil/x)")` injects an extra CSS declaration. `html.escape` blocks attribute breakout but not CSS-property injection. | `dash_render.py:9870`, `:9873`, `:10184`, `:10187`, `:10223`, `:10226` | MEDIUM (security) |
| 36 | **Marker-size maps are duplicated 7× with two mutually inconsistent scales.** Scatter uses `{'tiny':4,'vsmall':5,'small':6,'medsmall':7,'medium':8,'medlarge':10,'large':12,'vlarge':16,'huge':20}`; connected/dot/rconnected/dropline/rcapsym/scatteri use `{'vvsmall':3,'vsmall':4,'small':6,'medsmall':7,'medium':8,'medlarge':9,'large':11,'vlarge':14,'huge':18}`. `msize(large)` therefore means 12 px on a scatter and 11 px on a connected plot; `msize(tiny)` silently falls back to the default on non-scatter types. Default sizes also differ: 8 (scatter/connected/dot/dropline/scatteri), 6 (rconnected), 7 (rcapsym), 6/8 hardcoded again in facets. | `dash_render.py:8734–8736`, `:8997`, `:9015`, `:9215`, `:9255`, `:9287`, `:9314`; facets `:9683`, `:9731`, `:9733`, `:9738` | **HIGH** |
| 37 | Marker-symbol maps duplicated 6× with **different key sets** — the scatter map includes `circle_cross/circle_x/square_cross/square_x/asterisk/cross`, the others include `hex`/`circle_dot` but not `asterisk`/`cross`. `msymbol()` accepts different vocabularies depending on plot type. | `dash_render.py:8728–8733`, `:8999`, `:9017`, `:9217`, `:9257`, `:9289`, `:9316` | MEDIUM |
| 38 | `_lw_map`/`_lp_map` line-width and dash-pattern tables with default `1.5`; `fintensity` parsing block (`float(v[5:])/100.0 if v.startswith('inten')`) copy-pasted **six times** verbatim. | `dash_render.py:8684–8690`; fintensity at `:8826–8830`, `:8938–8943`, `:9042–9047`, `:9068–9073`, `:9092–9097` | MEDIUM |
| 39 | Alpha literals scattered and inconsistent for the same glyph across paths: scatter `0.7` / facet scatter (none, opaque); histogram `0.8` / facet histogram `0.6`; area `0.4` / facet area `0.4`; CI band `0.2`; `nonselection_alpha=0.15`. | `dash_render.py:8743`, `:8745`, `:8824`, `:8937`, `:9041`, `:9067`, `:9689`, `:9695`, `:9794` | MEDIUM |
| 40 | Annotation styling literals: note/caption `'11px'` `'#555555'`, subtitle `'13px'` `'#444444'`, mlabel `'9px'` `'#333333'` `x_offset=5, y_offset=5`, xline/yline `'#888888'` dashed `1.0`. The `_mlabpos_map` clock-position table is duplicated verbatim at `:8761–8765` and `:9529–9533`. | `dash_render.py:8586–8592`, `:8599–8601`, `:8751–8752`, `:8761–8765`, `:9529–9533` | MEDIUM |
| 41 | `'white'` hardcoded as the default outline for histogram quads and bars — not scheme-derived. | `dash_render.py:8831`, `:8965`, `:9121` | LOW |
| 42 | WebGL switch threshold `n_rows > 10000` hardcoded in **three** places. | `dash_render.py:8505`, `:9669`, `:9770` | LOW |
| 43 | `sizing_mode='stretch_width'` forced on every figure/Div/grid; no `xsize()`/`ysize()` equivalent and `aspectratio()` is the only size lever. | `dash_render.py:8511`, `:9668`, `:9769`, `:9877`, `:10269`, `:10280–10293` | LOW |
| 44 | Grid layout is `cols_n = ceil(sqrt(n))` (with `n<=2 → cols_n=n`) — **the `layout()` option is never read by the generated app.** Standalone honours it via `self._compute_grid(all_names, layout_opt)` and additionally supports `bs` Bootstrap layouts. | `dash_render.py:10243–10250` vs `:7391`, `:6317`, `:6493` | **HIGH** |
| 45 | Title `<h2 style="font-family:sans-serif;">` and `doc.title = title_text or 'dash'` — fixed markup, fallback title literal `'dash'`. No subtitle support at all. | `dash_render.py:10289–10296` | MEDIUM |
| 46 | `Select` "All" sentinel `'__all__'` (with a `+= '_'` collision loop) and slider `step=(vmax - vmin) / 100` — the 100-step resolution is a literal, duplicated in the range and slider branches. | `dash_render.py:9924–9925`, `:9964`, `:9993` | LOW |
| 47 | Facet naming/labelling literals: `f'{gname}__by__{_fac_idx}'`, separator `' / '`, `'Missing'`, `'Total'`, and the em-dash join `f'{title} — {label}'`. | `dash_render.py:9638`, `:9637`, `:9630`, `:9658`, `:9756`, `:9767`, `:9852` | LOW |
| 48 | Legend position map `{'top':'top_center', … 'on':'top_right'}` hardcoded; `legend(position(N))` clock positions unsupported. | `dash_render.py:8609–8610` | LOW |
| 49 | 429 Div markup hardcoded with `color:#c00` and `font-family:sans-serif`. | `dash_render.py:8362–8366` | LOW |

## 1.8 Temp-file naming and directory

| # | Finding | Citation | Sev |
|---|---|---|---|
| 50 | `dash serve` builds the app path as `` local serve_app_path "`_serve_app_base'.py" `` — i.e. **Stata's tempfile name with `.py` appended**. Stata's automatic tempfile cleanup erases the exact registered name (`_serve_app_base`), *not* `<name>.py`. The generated file therefore **leaks and persists** in `c(tmpdir)` after the session ends. That file contains the entire analysis dataset base64-encoded (`_DATA_B64`), created with default umask in a shared temp directory. | `dash.ado:1633–1634`; payload at `dash_render.py:8006–8010` | **HIGH** (security / data leak) |
| 51 | The temp name also determines the **Bokeh mount path**: `bokeh serve /var/folders/…/ST_00000x.tmp.py` mounts the app at `/ST_00000x.tmp`, not `/`. Verified: `curl http://localhost:5200/` → `302 → http://localhost:5200/app`. It happens to work only because Bokeh redirects when a single app is served; the launcher does not pass `--index` or use a stable name. | `dash.ado:1634`; `dash_render.py:10419–10420` | LOW |
| 52 | `dash build ... server` writes to the user's `saving()` path, so there is no temp file there — but the same generated file is then *also* executed, so the user's deliverable and the running server are the same artifact. | `dash.ado:1462–1466` | LOW |

---

# JOB 2 — Functional gaps between server mode and what is advertised

## 2.1 BLOCKER-1 — `bokeh serve` serves an empty document and has no `/health`

**Verified empirically (see Executive Summary).**

| Claim | Where | Reality |
|---|---|---|
| "Launch with: `bokeh serve <this_file.py>`" | generated docstring, `dash_render.py:7871` | Serves `{}` — an empty document |
| "To launch: `bokeh serve `saving''" | `dash.ado:1471` | same |
| "`bokeh serve app.py --show`" | `dash.sthlp:438` | same |
| `dash serve` runs a live dashboard | `dash.sthlp:200–206` | `dash_render.py:10419` shells out to `bokeh serve` → blank page |
| Health-check endpoint exists | `dash_render.py:10312`, CLAUDE.md rule 17 | 404 under `bokeh serve` |

Root cause: `make_document` is only bound to a `Server` inside `if __name__ == '__main__':`
(`dash_render.py:10305–10313`), and the file never calls `curdoc()`. Bokeh's `CodeRunner`
names the module `bokeh_app_<uuid>` (`bokeh/application/handlers/code_runner.py:185`), so
the guard is always false. Every finding below about "server mode behaviour" describes the
`python app.py` path; none of it is reachable through any documented workflow.

**Severity: BLOCKER.**

## 2.2 BLOCKER-2 — `dash build, saving(app.py) server` blocks Stata and opens a browser

The help says the opposite, three times:

- `dash.sthlp:82` — `{pstd}{ul:Build Bokeh Server app (write .py file, do not block)}`
- `dash.sthlp:249–251` — "`server` … **does not block or open a browser**"
- `dash.sthlp:492` — `{pstd}{ul:Write server app to file (non-blocking)}`

The code does all three of the things the help denies:

1. `dash.ado:1462–1466` sets `local render_mode "server"` and calls `_dash_do_render`.
2. `_dash_do_render` sets `sys.argv` **without `--port`, `--timeout` or `--no-browser`**
   (`dash.ado:142`) and then `runpy.run_path(..., run_name="__main__")` (`dash.ado:143`) —
   which executes dash_render.py's `__main__` **inside the Stata Python session**.
3. `dash_render.py:10410` — `if args.mode == "server":` → `_sp.Popen(["-m","bokeh","serve", …])` at `:10418–10425`.
4. `args.no_browser` defaults to `False` (`dash_render.py:10400`), so
   `dash_render.py:10436–10441` starts the browser thread and opens
   `http://localhost:5006` after 1.5 s.
5. `args.timeout` defaults to `0` (`dash_render.py:10390`), so the auto-stop thread at
   `:10444` is skipped.
6. `dash_render.py:10452` — `_proc.wait()` blocks **forever** until the user finds the
   Stata console and sends Ctrl+C.

Consequence chain: `dash build, saving(app.py) server replace` hangs the Stata session
indefinitely, opens a browser tab pointing at a **blank** dashboard (BLOCKER-1), and the
two "success" messages at `dash.ado:1470–1471` only print *after* the user kills the
server. The help's own example at `dash.sthlp:495–496` is the exact command that hangs.

**Severity: BLOCKER.** Two independent bugs: (a) `_dash_do_render` must pass
`--no-browser` and must not trigger the launch branch at all for `build`; (b) the help text
is wrong.

## 2.3 BLOCKER-3 — `dash serve` discards every dashboard-level setting (verified)

`dash.ado:1603` is exactly as reported:

```stata
local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"auto","link":"","filter":"","theme":"default","title":"","subtitle":"","registry":"`registry'"}}"'
```

Compare `dash.ado:1433` (the `dash build` path), which emits real values for
`layout`, `link`, `filter`, `theme`, `title`, `subtitle`, plus two keys `dash serve`
does not emit at all (`tabs`, `filter_position`).

Compounding it, `_dash_serve`'s own syntax is `syntax [, PORT(string) NOBROWSER
TIMEOUT(string)]` (`dash.ado:1487`) — there is **no way to supply** any of these options to
`dash serve`, and it does not inherit them from a preceding `dash build`.

| Setting | `dash build` | `dash serve` | What the user sees |
|---|---|---|---|
| `filter()` | honoured (`:1425–1426`, `:1433`) | **`""`** | **No filter widgets at all.** `_filter_specs = []` is emitted (`dash_render.py:9901–9904`) and the widget loop iterates nothing |
| `link()` | honoured | `""` | No linked brushing; `linked_names` is empty (`dash_render.py:8386–8387`) |
| `title()` | honoured | `""` | No header Div (`dash_render.py:10288`); browser tab title falls back to the literal `'dash'` (`:10296`) |
| `subtitle()` | emitted | `""` | Never read by the generated app anyway (§2.5) |
| `layout()` | honoured | `"auto"` | Irrelevant — the generated app ignores `layout` entirely (§2.5) |
| `theme()` | honoured | `"default"` | Irrelevant — no scheme logic in the generated app (§2.5) |
| `tabs()` | emitted | **key absent** | No tabs |
| `filterposition()` | emitted | **key absent** | No sidebar |

Per-graph options (`${dash_json_<name>}`) **do** survive, so titles/axes/colors set on
individual `dash scatter` calls are preserved. The loss is strictly dashboard-level.

The damage is worst for `filter()`: `dash.sthlp:200–206` sells `dash serve` on the grounds
that "the server recalculates aggregated layers … **on every widget interaction**" — but
`dash serve` can never create a widget. The help's own example makes this concrete:

```
dash.sthlp:487  . dash build, saving(dashboard.html) filter(foreign, type(dropdown)) replace
dash.sthlp:489  . * -- or launch live server (filter recomputes aggregates) --
dash.sthlp:490  . dash serve, port(5006)
```

The `filter(foreign, …)` on line 487 is a `dash build` option; `dash serve` on line 490
does not see it. The documented headline feature of server mode is unreachable.

**Severity: BLOCKER.**

## 2.4 Standalone vs. generated-server feature matrix

Re-verified from source; "server" describes the `python app.py` path (under `bokeh serve`
everything is moot — BLOCKER-1).

| Feature | Standalone HTML | Generated server app | Severity |
|---|---|---|---|
| **KPI `update(brush)`** | **Not implemented.** No `selected` / `on_change` callback exists anywhere below line 7738 — `grep "on_change\|selected"` yields only `selected.indices = []` resets (`:4470`, `:4476`) and three `js_on_change("value", …)` widget bindings (`:4773`, `:4829`, `:4883`). `self._kpi_update_modes` (`:5030`) is written and **never read**. A KPI with `update(brush)` is also excluded from the filter callback (`:7273`), so it is **frozen forever**. | **Wired but dead.** `shared_source.selected.on_change('indices', …)` at `:10232–10234` is the only binding — but **no glyph renders from `shared_source`**. Every plot branch builds a fresh `ColumnDataSource(clean)` (scatter `:8696`, line `:8778`, area `:8927`, bar `:8950`, …) and appends it to `graph_sources`. `shared_source` is used for glyphs only in the `by()`-faceted + `link()`ed branch (`:9647`, `:9674`). So box/lasso selection lands on a CDS nobody listens to. | **SILENT** |
| ⇒ `dash.sthlp:424` "Brush/lasso KPI update — Yes / Yes" | **false** | **false (except by()+link())** | **SILENT** |
| **Linking / `link()`** | Real: `self.sources[name] = linked_source` for every linked graph (`:7587`), with per-graph `CDSView`+`BooleanFilter` for qualifiers (`:7591–7599`). Brushing dims across graphs via `nonselection_alpha` (`:108`). | **Effectively broken.** `graph_sources[gname] = [shared_source]` (`:8411`) and `src = _src_list[-1]` (`:8474`), but `src` is only used when a plot has no x *and* y. Every real plot substitutes its own CDS. Selections do not propagate between graphs. Works only in the `by()`+`link()` facet path. | **SILENT** |
| **Fit-line recompute under filtering** | No — `_FILTER_JS` handles only `histogram` and `kdensity` (`:4550–4629`); `_AGG_TYPES_RENDER = {"histogram","hist","kdensity"}` (`:7568`). Matches `dash.sthlp:423`. | Yes — `agg_sources` recompute covers `lfit, qfit, lfitci, qfitci, lowess, lpoly, fpfit, mspline, mband, rscatter, pcscatter, histogram, kdensity` (`:10138–10166`). | (as documented) |
| **Histogram recompute** | Counts recompute on **fixed** `bin_edges` baked at build time (`:3029`, `:4567–4591`). `dash.sthlp:422` says "No", which understates it — bars do update, edges do not. | Full `np.histogram` recompute including edges (`:8062`, `:10140`). **Bin count differs**: standalone default 10 (`:3001`), server default 20 (`:8056`); faceted/total panels force 20 and drop `bin()` (`:9694`, `:9793`). | **SILENT** |
| **`by()` panels** | Full fidelity — facet figures go through the same dispatch table of **38** `map_*` methods (`:6169–6230`, `:6994–7010`). | **Reduced to 16 plot types** (`:9682–9751`). Dropped: `lfitci, qfitci, lpolyci`(→plain lpoly)`, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, scatteri, pcspike, pcarrow, pcbarrow, pci, pcscatter, tsline, tsrline, mspline, rscatter, function`. Those plots **silently vanish** from faceted graphs. Per-plot options (`msize`, `msymbol`, `lwidth`, `lpattern`, `fcolor`, `mlabel`, `jitter`) are all ignored in facets — sizes are hardcoded 6/8, widths 1.5. | **SILENT** |
| **`by(total)` panel** | Same full dispatch. | Same 16-type subset (`:9781–9850`), plus a hardcoded `title='Total'` (`:9767`) that ignores the graph's `title()`, and **no axis labels at all** (`_tot_fig` is built without `x_axis_label`/`y_axis_label`, `:9766–9771`; facets at least set them, `:9663–9666`). | **SILENT** |
| **`tabs()`** | Honoured, Bootstrap layouts only (`:7365`, `:7372–7375`, `:6661`). | **Never read.** No `'tabs'` lookup exists below 7860. | **SILENT** |
| **`layout(bs …)` / `layout(N M)` / `layout(name:r,c)`** | Honoured — `_is_bootstrap_layout` (`:6317`), `_parse_bs_layout` (`:6367`), `_render_bootstrap_html` (`:7378–7388`), `_compute_grid` (`:7391`). | **Never read.** `layout_opt` is computed at `:7832` and **never used**. Grid is always `ceil(sqrt(n))` (`:10243–10250`). | **SILENT** |
| **`filterposition(left)`** | Honoured in Bootstrap mode (`:7366–7368`, `:6598`). | **Never read.** Filters are always a horizontal `row(...)` above the grid (`:10282–10284`). | **SILENT** |
| **`theme()` / `scheme()` / scheme CSS** | Full `SchemeParser` with `#include` inheritance and path-traversal guards (`:688–800`); theme→scheme map (`:4982–5006`); every default color comes from `self.scheme.default_color(...)`. | **No scheme support whatsoever.** `theme_opt` computed at `:7835` and **never used**. The only reuse is `repr(dict(OptionTranslator._COLOR_MAP))` embedded at `:8428` for *named-color lookup*; defaults are the literal `'#1f77b4'`. | **SILENT** |
| **Per-facet KPI cards (`update(<graphname>)`)** | Supported — one card per facet group with `title (label)` (`:7091–7120`). | Not supported. `kupdate` is only tested against `'filter'/'both'` (`:10170`) and `'brush'/'both'` (`:10211`); a graph name matches neither, so the KPI is **never updated and never faceted**. | **SILENT** |
| **KPI statistics** | JS: `count, mean, sum, min, max, median/p50, dcount, sd` (`:4504–4530`) — **no `p25`/`p75`**. | Python: adds `p25`, `p75` (`:8317–8318`). | COSMETIC |
| **KPI initial value** | Taken from Stata's precomputed `value`/`display` (`quietly summarize`, `dash.ado:1102–1103`), reformatted in Python (`:7118`). | Recomputed from pandas (`_compute_kpi`, `:8303`). Divergence risk on `if`/`in`-qualified KPIs. | COSMETIC |
| **KPI card styling** | `padding:20px`, bordered, min 160×110, value 36 px, `#6c757d`, default `#212529` | `padding:16px`, borderless, no min size, value 28 px, `#888`/`#aaa`, default `#333333` | **SILENT** |
| **CSS-injection sanitizing of KPI colors** | `_sanitize_css_color` in the filter callback (`:4356`, `:7292`, `:7295`) | none — `html.escape` only | **SILENT** (security) |
| **`mlabel()` / `mlabsize` / `mlabposition`** | Supported | Supported in the main loop (`:8747–8771`, `:9506–9539`); **dropped in facet/total panels** | **SILENT** |
| **`jitter()`** | Supported | Supported in the main loop (`:8697–8722`); **dropped in facets** | **SILENT** |
| **scipy dependency** | lazy, per-method (`:2404`, `:3055`, `:4001`) | hard, module-scope (`:7882`) | **SILENT** |
| **statsmodels missing** | raises `ImportError` (`:2547`) | silently draws raw points as a "lowess curve" (`:8147–8148`) | **SILENT** |
| **LOWESS bandwidth** | `bwidth()`, default 0.8 (Stata's default) (`:2559`) | hardcoded `frac=0.5`, `bwidth()` ignored (`:8145`) | **SILENT** |
| **Histogram default bins** | 10 (`:3001`) | 20 (`:8056`, `:8810`); 20 forced in facets (`:9694`, `:9793`) | **SILENT** |
| **`/health` endpoint** | n/a | exists under `python app.py`; **404 under `bokeh serve`** (`:10312`) | **BLOCKER** |
| **Rate limiting** | n/a | exists under `python app.py`; **dead under `bokeh serve`**; XFF trivially spoofable (`:7975–7979`) | **BLOCKER** / SILENT |

## 2.5 Build-time locals computed and thrown away

Direct evidence that server mode was never wired to the dashboard-level options.
In `_generate_app_source` these are assigned and **never referenced again**:

| Local | Line | Consumed? |
|---|---|---|
| `title_safe = html.escape(title_raw)` | `dash_render.py:7831` | no — the app re-escapes at runtime (`:8374`) |
| `layout_opt` | `dash_render.py:7832` | **no** |
| `theme_opt` | `dash_render.py:7835` | **no** |
| `kpis` | `dash_render.py:7838` | **no** |
| `linked_names` (build-time set) | `dash_render.py:7841–7848` | **no** — recomputed at runtime (`:8381–8387`) |

And the emitted app reads exactly **three** keys out of `build_options` — `link` (`:8373`),
`title` (`:8374`), `registry` (`:10237`). `layout`, `subtitle`, `theme`, `tabs`,
`filter_position` are never looked up. (`filter` is consumed at *build* time into
`_filter_specs`, `:9897`.)

## 2.6 ARCHITECTURAL FINDING — the duplication, quantified

**Stated plainly: every rendering behaviour in this package is implemented between two and
four times, in two different languages, with no shared source of truth. The two
implementations have already drifted, and the drift is user-visible.**

Counts, all verified by grep:

| Layer | Implementation | Count |
|---|---|---|
| Standalone Python | `GlyphMapper.map_*` methods | **38** |
| Generated server — main figure loop (`:8670–9539`) | `ptype ==` / `ptype in` branches | **37** distinct types |
| Generated server — `by()` facet loop (`:9682–9751`) | branches | **16** |
| Generated server — `by(total)` loop (`:9781–9850`) | branches | **16** |

⇒ **16 plot types are implemented 4 times** (standalone + server main + server facet +
server total). **21 more are implemented twice** and have no facet/total support in server
mode at all. Total plot-rendering implementations: **107** for 38 logical behaviours.

Statistical kernels are doubled a second way — 19 `_compute_*` helpers emitted as strings
(`dash_render.py:8056–8338`) shadow their standalone counterparts:

| Behaviour | # independent implementations | Locations |
|---|---|---|
| Histogram binning | **4** | standalone Python `:2985–3029`; standalone JS `:4567–4591`; server `_compute_histogram` `:8056`; server facet/total inline `:9692`, `:9791` |
| KPI statistic | **4** | Stata `quietly summarize` `dash.ado:1102`; standalone Python `_compute_kpi_stat_on_df`; standalone JS `:4504–4530`; server `_compute_kpi` `:8303` |
| KPI card HTML/CSS | **5** | standalone Div `:6293`; standalone JS `:4542`; server initial `:9869`; server filter cb `:10183`; server brush cb `:10222` |
| kdensity | **3** | standalone `:3055`; standalone JS `:4602–4628`; server `:8129` |
| mband | **3** | server `_compute_mband` `:8255`; server facet inline `:9739–9751`; server total inline `:9838–9850` (+ standalone `:4091`) |
| `fintensity` parsing | **6** | `:8826`, `:8938`, `:9042`, `:9068`, `:9092` (+ standalone translator) |
| Marker size map | **7** | `:8734`, `:8997`, `:9015`, `:9215`, `:9255`, `:9287`, `:9314` |
| `mlabposition` map | **2** | `:8761`, `:9529` |
| AST safety validator for `if_expr` | **2** | `_safe_g` `:8456`; `_safe_g_cb` re-declared *inside the per-event callback* `:10082` (re-created on every filter interaction) |
| WebGL threshold | **3** | `:8505`, `:9669`, `:9770` |
| `_resolve_color` | **2** | server `:8430`; standalone `OptionTranslator` (only `_COLOR_MAP` is shared, via `repr()` at `:8428`) |

**The drift is not hypothetical — it has already happened**, and every one of these is a
user-visible behaviour difference for an identical `dash` command:
histogram bins 10 vs 20 (#30); lowess `frac` 0.8 vs 0.5 (#24); lfit grid 200+padding vs
100+none (#26); kdensity 400 pts over an extended range vs 200 over the data range (#27);
default series color scheme-derived vs `#1f77b4` (#33); KPI card 36 px/bordered vs
28 px/borderless (#34); `msize(large)` = 12 px vs 11 px *within the same file* (#36); `p25`/`p75`
supported in one KPI engine and not the other.

The generated app is a ~2,400-line Python program assembled from a list of ~2,500 string
literals (`lines: list[str]` at `dash_render.py:7862`, joined at `:10328`). It is not
type-checked, not linted, not importable for unit testing, and — per CLAUDE.md rule 4 —
none of the 19 `_compute_*` functions or the `_RateLimiter` / `_HealthHandler` classes
inside it can have a unit test, because they do not exist until a dashboard is built.

**Recommended direction:** the generated app should import the shared kernels
(`dash_runtime.py` installed alongside `dash_render.py`) rather than re-emit them, and
should register itself with `curdoc()` so `bokeh serve` works. That collapses ~2,400
generated lines to roughly a spec blob plus a `make_document(curdoc())` call, removes 3 of
the 4 plot-dispatch copies, and makes the rate limiter and health handler testable.

---

## Fix priority

1. **BLOCKER-1** — add `make_document(curdoc())` (guarded so it does not double-run under
   `__main__`) and register `/health` via a Bokeh `Server` lifecycle hook or
   `--static`/`extra_patterns` equivalent that survives `bokeh serve`. Add an end-to-end
   test that runs `bokeh serve` and asserts a non-empty `docs_json` and `/health` = 200.
   Per CLAUDE.md rule 8, write the regression test before the fix.
2. **BLOCKER-2** — `_dash_do_render` must not trigger the launch branch for `build`
   (add a `--build-only` flag, or gate `dash_render.py:10410` on an explicit
   `--launch`); correct `dash.sthlp:82`, `:249–251`, `:492`.
3. **BLOCKER-3** — give `_dash_serve` the full `dash build` option set (or have it read the
   last `dash build` options from the registry) and stop hardcoding `dash.ado:1603`.
4. **HIGH / SILENT divergences** — reconcile #24, #30, #31, #33, #34, #36, #44, and wire the
   brush callback to the CDS the glyphs actually use.
5. **Security** — #13 (XFF spoofing), #50 (temp-file leak of the full dataset), #35 (CSS
   injection), #21/#22 (dependency behaviour).
6. **Architecture** — extract the shared runtime module (§2.6).
