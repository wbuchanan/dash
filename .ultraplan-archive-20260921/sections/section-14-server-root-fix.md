# Section 14: Server mode — root fix and option pass-through

## Overview
`bokeh serve app.py` serves a **completely empty document**. Verified by generating an app
from a spec and serving it: `docs_json` is literally `{}`, the title is absent, and `/health`
returns 404.

The cause: the generated file binds `make_document` to a `Server` and registers `/health`
only inside `if __name__ == '__main__':` (`:10305-10313`), and never calls `curdoc()` — zero
grep hits. Bokeh's `CodeRunner` executes app scripts under a synthetic module name
`bokeh_app_<uuid>`, so that guard is **always false**.

This is the path `dash serve` takes (`:10419`), the path `dash.ado:1471` tells the user to
run, and the path `dash.sthlp:438` documents. `python app.py` works — and no documented
workflow uses it.

Everything else in server mode is downstream of this, including the fact that nobody noticed:
448 server tests pass because they all exercise `make_document` directly.

## User story
> As a Stata user, `dash serve` gives me a live dashboard with my filters, my title and my
> scheme, and does not freeze my Stata session.

## Business requirements
- BR-14.1 `bokeh serve` on a generated app serves the dashboard.
- BR-14.2 `/health` responds (project rule 17).
- BR-14.3 `dash serve` honours the options the user set.
- BR-14.4 `dash build, server` writes a file and returns, as documented.

## The defect register

| # | Defect | Citation | Rating |
|---|---|---|---|
| 1 | `bokeh serve` serves an empty document; `/health` 404 | `:10305-10313`, no `curdoc()` | **BLOCKER [measured]** |
| 2 | `dash serve`'s master JSON is hardcoded — `layout:"auto"`, `link:""`, `filter:""`, `theme:"default"`, `title:""`, `subtitle:""`, no `tabs`, no `filter_position` — and its syntax is only `[, PORT() NOBROWSER TIMEOUT()]`, so the options cannot be supplied at all and nothing is inherited from a prior `dash build`. **`dash serve` can never create a filter widget** — the one feature server mode is sold on (`dash.sthlp:200-206`), and the help's own example (`:487-490`) demonstrates the bug | `dash.ado:1487`, `:1603` | **BLOCKER** |
| 3 | `dash build, saving(app.py) server` **blocks Stata forever and opens a browser**: `sys.argv` is set with no `--no-browser` and no `--timeout` (`dash.ado:142`), then `runpy.run_path(..., run_name="__main__")` runs the launcher inside Stata — browser after 1.5s (`:10436-10441`), timeout defaults to 0, `_proc.wait()` (`:10452`) never returns. The help denies this at `:82`, `:249-251` and `:492` | `dash.ado:142`, `:10408-10455` | **BLOCKER** |
| 4 | `args.port` never forwarded to `builder.build()` — every app embeds `_port = 5006` **[measured with `--port 7777`]** | `:10356` | BLOCKER |
| 5 | `allow_websocket_origin` fixed to `localhost:<port>` — 127.0.0.1 or LAN access gets a blank page, no option | `:10310`, `:10422` | BLOCKER |
| 6 | `X-Forwarded-For` trusted unconditionally — the rate limiter is bypassable by header spoofing | `:7975-7979` | **SECURITY** |
| 7 | The temp app is written as `` `_serve_app_base'.py `` while Stata cleans up `_serve_app_base` — **a file containing the full dataset base64-encoded leaks into the temp directory permanently** | `dash.ado:1633-1634` | **SECURITY** |
| 8 | `saving()` in server mode bypasses the path validator entirely | `dash.ado:1198-1207` | SECURITY |
| 9 | `scipy` and `statsmodels` imported at module scope of the generated app (lazy in standalone), so a missing library breaks the whole app regardless of plot type; a missing `statsmodels` silently draws raw points and calls them a lowess curve | `:7882`, `:8147-8148` | SILENT |
| 10 | `/health` uses deprecated `datetime.utcnow()` — `DeprecationWarning` on Python 3.14 **[measured]** | `:7995` | LOW |
| 11 | `update(brush)` is bound to `shared_source` (`:10232`), which no glyph renders from, so it is dead in server mode too | `:10232` | SILENT |
| 12 | `link()` broken in server mode for the same reason | — | SILENT |
| 13 | `tabs()`, `layout()`, `filterposition()`, `theme()` never read by the generated app — `layout_opt` and `theme_opt` are computed at `:7832`/`:7835` and never used | `:7832`, `:7835` | SILENT |

## Risk: [red] — process lifecycle, a blocking subprocess wait, and a security surface. The failure modes are a hung Stata session and an orphaned `bokeh serve`.

## Dependencies
- Depends on: S13
- Blocks: S15
- Parallel batch: 5

## TDD test stubs
- Test: a generated app served by `bokeh serve` returns a non-empty `docs_json` containing the
  expected figure count. **This is the test the whole section exists for** and no existing
  test does it — all 448 call `make_document` directly.
- Test: `/health` returns 200 under `bokeh serve`, not only under `python app.py`.
- Test: `--port 7777` produces an app listening on 7777.
- Test: `dash serve` after a `dash build` with filters produces filter widgets.
- Test: `dash serve` honours `title()`, `layout()`, `theme()`, `link()`, `tabs()`.
- Test: `dash build, saving(app.py) server` returns control to Stata and opens no browser.
- Test: a spoofed `X-Forwarded-For` does not bypass the rate limiter.
- Test: no temp file survives a `dash serve` run.
- Test: server-mode `saving()` is path-validated.
- Test: a missing `statsmodels` does not break a server app that uses no `lowess`.
- Test: `dash build, nobrowser` writes the file and opens nothing.
- Test: a failed browser launch reports the output path instead of failing silently.

## Tasks

<task type="auto" id="14-01">
  <name>Write the test that would have caught the empty document</name>
  <files>test/test_server_serves.py</files>
  <action>
    Start a real `bokeh serve` against a generated app, fetch the page, and assert `docs_json`
    is non-empty and contains the expected number of figures. Assert `/health` returns 200.

    This must exercise `bokeh serve`, not `make_document`. Every one of the 448 existing
    server tests calls `make_document` directly, which is why a completely empty document
    shipped.

    Make the fixture robust: pick a free port, wait for readiness rather than sleeping, and
    tear the process down reliably even on failure. An orphaned `bokeh serve` in CI is its own
    problem.

    Run. Both assertions must fail — empty `docs_json`, 404 on `/health`.
  </action>
  <verify>docs_json is `{}` and /health is 404, exactly as measured.</verify>
  <done>The blocker is pinned by a test that exercises the path users actually take.</done>
</task>

<task type="auto" id="14-02">
  <name>Make the generated app work under bokeh serve</name>
  <files>dash_render.py</files>
  <action>
    Restructure the generated app so document construction and `/health` registration happen
    at module scope via `curdoc()`, not inside `if __name__ == '__main__':` (`:10305-10313`).

    Keep `python app.py` working too — it is the only thing that works today and someone may
    depend on it. The `__main__` block should remain, calling the same module-scope
    construction rather than duplicating it.

    `/health` under `bokeh serve` needs registering differently from the `extra_patterns`
    approach in the dead block. Establish how Bokeh exposes extra endpoints for a served app
    and implement it; if it genuinely cannot be done from within an app script, say so
    explicitly and provide the health check another way rather than quietly dropping project
    rule 17.

    Fix `datetime.utcnow()` (`:7995`) while in the endpoint.
  </action>
  <verify>All 14-01 assertions pass under `bokeh serve`; `python app.py` still works.</verify>
  <done>Server mode serves the dashboard on the documented path.</done>
</task>

<task type="auto" id="14-03">
  <name>Give dash serve the options it discards</name>
  <files>dash.ado</files>
  <action>
    `_dash_serve`'s syntax (`:1487`) is `[, PORT() NOBROWSER TIMEOUT()]` and its master JSON
    (`:1603`) is entirely hardcoded, so no build option can be supplied and nothing is
    inherited.

    Two changes. First, accept the full `dash build` option set on `dash serve` — the same
    options, the same validation, ideally the same helper, so they cannot diverge. Second,
    inherit from the registry: if a `dash build` already ran in this session, reuse its
    options unless overridden. That is what the help's own example (`:487-490`) assumes.

    Remove the hardcoded JSON at `:1603` and build it the way `dash build` does at `:1433`.
    Factor the assembly into one helper called by both, plus the immediate-render path at
    `:974` whose `{"layout":"1 1","theme":"default"}` is the third hardcoded copy.

    The immediate path's hardcoded `"theme":"default"` is why `dash scatter mpg weight` can
    never use a non-default scheme — S11 needs this fixed to deliver BR-11.1 on that path.
  </action>
  <verify>`dash serve` produces filter widgets, titles, layouts and themes; the help's documented example works.</verify>
  <done>Server mode honours what the user asked for, from one JSON assembly shared by three paths.</done>
</task>

<task type="auto" id="14-04">
  <name>Stop dash build, server from hijacking the Stata session</name>
  <files>dash.ado, dash_render.py</files>
  <action>
    `dash build, saving(app.py) server` must write the file and return, as `dash.sthlp:82`,
    `:249-251` and `:492` all promise.

    `_dash_do_render` (`dash.ado:142`) sets `sys.argv` without `--no-browser` or `--timeout`,
    then `runpy.run_path(..., run_name="__main__")` runs the launcher inside Stata. Separate
    the two responsibilities: `dash build, server` **generates**; `dash serve` **launches**.
    Only the launch path may block, and it must say so before it does.

    Forward `args.port` to `builder.build()` (`:10356`) — it is dropped today, so every app
    embeds `_port = 5006` regardless of `--port`.

    Make `allow_websocket_origin` (`:10310`, `:10422`) configurable instead of fixed to
    `localhost:<port>`, which gives 127.0.0.1 and LAN clients a blank page. Default to the
    current restrictive value; accept an option to widen it; document the security
    implication of widening.

    Also fix `dash.ado:143`'s `python: runpy.run_path(...)`: a single-line `python:` echoes
    the expression value, and `run_path` returns the module globals dict, so **every render
    dumps ~10 KB of `dash_render.py`'s namespace into the Stata log** **[measured]**. Assign
    the result. Contrary to project rule 14.

    Finally, add `nobrowser` to `dash build`. Every standalone build unconditionally shell-opens
    the file (`dash.ado:1475-1477`), and immediate render does the same when `saving()` is
    omitted (`:1012-1014`); only `dash serve` has a `nobrowser` option (`:1488`). A do-file
    that builds ten dashboards opens ten browser tabs. There is also no `_rc` check after any
    of the six `shell` lines, and the immediate path never displays the temp file path, so a
    failed `xdg-open` leaves the output unreachable — report the path on failure.
  </action>
  <verify>`dash build, server` returns immediately and opens no browser; `nobrowser` works on `dash build`; `--port` is honoured; the Stata log is clean.</verify>
  <done>Generating a server app no longer takes the Stata session hostage.</done>
</task>

<task type="auto" id="14-05">
  <name>Close the server security holes, then commit</name>
  <files>dash_render.py, dash.ado, test/</files>
  <action>
    Write the adversarial tests first, per project rule 18.

    Defect 6: `X-Forwarded-For` is trusted unconditionally (`:7975-7979`), so the rate limiter
    is bypassable by header spoofing. Trust it only from configured proxies; default to the
    socket address. Test with a spoofed header.

    Defect 7: the temp app is written as `` `_serve_app_base'.py `` while Stata cleans up
    `_serve_app_base` (`dash.ado:1633-1634`), so **a file containing the full dataset
    base64-encoded leaks into the temp directory permanently**. Clean up the file that is
    actually created, and test that nothing survives — including on the error path, which is
    where cleanup usually gets missed.

    Defect 8: server-mode `saving()` bypasses the path validator (`dash.ado:1198-1207`).
    Validate it with the same helper, adjusted for the `.py` extension.

    Defect 9: `scipy` and `statsmodels` are imported at module scope of the generated app
    (`:7882`), so a missing library breaks the whole app regardless of plot type — and a
    missing `statsmodels` silently draws raw points and calls them a lowess curve
    (`:8147-8148`). Make them lazy, matching the standalone path S01 fixed, and make the
    lowess degradation warn rather than lie.

    Adopt `test/test_e2e_serve.cscript`, which S01 marked xfail pending this section. It
    should now pass; if it does not, it is telling you something.

    Run all suites against the S01 baseline. Commit, security fixes in their own commits.
  </action>
  <verify>Spoofed headers do not bypass the limiter; no temp file survives; server `saving()` is validated; the xfail'd cscript passes.</verify>
  <done>Server mode works on the documented path, honours its options, and no longer leaks data or trusts spoofable headers.</done>
</task>
