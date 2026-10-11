# Section 46: Served session capacity and memory (P1.31 part a)

> Part of: WP-30 · Items: P1.31 (entry `P1.31a`; GAPS2-F3a, GAPS2-F3b, GAPS2-F3c, GAPS2-I4-a, GAPS2-I4-b, GAPS2-G14-d) · Risk: yellow · Batch: 16 (merge order S45, S46, S47) · Depends on: 04, 23, 25, 41 · Blocks: 57 · Tasks: 11, 1 commit · Case prefix: MS

## Review amendments

- Fixed (orchestrator ruling Q-57.1): the estimator memo's get and put now run under `state.memo_lock` (a `threading.Lock` in the process holder), in this section's commit, with `fn` called outside the lock; S57's worker relies on it. TR-46.3, TR-46.8, 46-04, a new `TestEstimatorMemo::test_the_lock_guards_get_and_put` and the Resolution say so.
- Fixed (major): TR-46.9 shares move snapshots through `_DASH_STATE.snapshots`, which the holder (TR-46.3) did not define and nothing reset. It is now a holder field, emptied whenever the payload entry is replaced, so a second payload in one process (pytest workers, `bokeh serve` reloads) never reads the first one's rows.
- Fixed (major): the copied helpers use `sys`, `types`, `copy`, `threading` and `hashlib`, which neither dash_render.py's header (no `import sys`) nor the generated app's (template :34101-34106) imports. Each helper now imports them in its own body, as dash_render.py's helpers do (:4240).
- Fixed (major): `$S` was "as in section 45", which made S46 share S45's directory while both run in parallel; it is now `<scratch>/s46`, with the batch files read from `<scratch>`.
- Fixed (minor): `_DASH_IDLE_HTML` held the placeholder text "<no number>"; it now holds the `%d` that TR-46.9 fills. The truth stub's header and its comment-only body are stated against `_wp30_blocks`' check.
- Checked: the session gate and decode anchors (template :34712-34754), `_dash_token_auth` (:4083), `_dash_launch_app` (:37206) and its argv, the renderer's argparse (:37553), `_stata_if_to_pandas` as the last `_shared_stat_lines` entry (:33590), and `_dash_serve_spec`'s digit checks. S46 is batch 16's only `_generate_app_source` editor and shares no function with S45 or S47. The cap check runs after the key gate, and the busy and idle bodies are constants (rule 1).
- Rejected: 46-10's `<files>none</files>`. It is a measurement step whose numbers go into the commit body, and it edits nothing.
- The review pass applied both lenses.
- Ratified (ratification 06oct2026; index row 22, A116/A117, P1.31.7-8, CHANGED "allow 80MB RAM for 200k rows"): the per-session RSS growth bound is 80 MB at 200k rows × 3 layers (was 40 MB); the 64 MB per-process LRU memo is unchanged. Overview, BR-46.5, AC-46.5, TR-46.17, 46-10's verify, the completion criteria, the Resolution and the CHANGELOG Security line now say 80 MB.
- Flipped to guard (ratification 06oct2026): `TestPerSessionMemory::test_growth_at_most_40_mb` (red at about 70-100 MB) is now `test_growth_at_most_80_mb`, expected to pass at the base (60.7 MB retained, about 72 MB mean RSS growth from m2): a regression pin, not a fix. 46-01 records it under "Guards", the commit body lists it as `Guard:`, and the Resolution still names it as a pin. 46-01's `FAILED` floor of 30 still holds without it.
- Dropped (ratification 06oct2026): the shared move snapshot (TR-46.9's `_DASH_STATE.snapshots.setdefault(...)` tuples and TR-46.3's `snapshots` field, with 46-04's and 46-05's mentions). Its only purpose was cutting m7's 22.9 MB of `_orig_src_data` copies to reach 40 MB; at 80 MB no requirement needs it (BR-46.1 needs only the decoded frame shared; no 20-session memory budget is set, the cap bounds the total; the memo is unaffected), and dropping it removes a shared structure from the move path S57 rewrites. `_orig_src_data` stays per session and moves to P2.41 with `.tolist()` and the index lists. The earlier "Fixed (major)" snapshot amendment is superseded. Task count unchanged (11).
- Derived figures (ratification 06oct2026): at the default cap, 20 × 80 MB + 221 MB server + 64 MB memo is about 1.9 GB at 200k × 3 (was about 1.1 GB at 40 MB); TR-46.17 puts that sizing advice in the help's Resource limits.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:165 (P1.31) reads: "There is no concurrent-session cap and no unused-session lifetime. Each session re-decodes the whole dataset. One event loop is blocked by recomputes." This section closes the first three claims; S57 (batch 20) moves recomputes off the loop. Measured at `c96facd` (research `.ultraplan/wp30/research/p1-31.md` §2, Stata's Python 3.13.9, bokeh 3.8.0):

```
m2_live.py   (python app.py, 200k rows x 3, one scatter, 25 held pull_sessions)
  server up, rss=221MB ; session 1 rss=357MB ; session 10 rss=1061MB ; session 24 rss=2016MB     (all 25 served)
m3_expiry.py (Bokeh defaults: unused_session_lifetime_ms 15000, check_unused_ms 17000)
  a page-only session goes at ~20 s; a connected session (an open or background tab) is never discarded
m1_cost.py   _load_spec_and_data 0.39s per session ; make_document 0.96-1.03s ; doc retained 60.7 MB
m7_mem.py    retained per session: 22.9 MB _orig_src_data list copies, 12.2 MB .tolist(), 7.6 MB index list, 4.6 MB frame
k1.py        3 make_documents: decode_calls = 1, 2, 3
```

Nothing in dash_render.py names `on_session_destroyed`, `max_sessions` or `unused_session`; the only session gate after the key is the per-minute `_SESSION_LIMITER` (template :34335, :34741-34752).

**After this section**, under `dash serve`, `python app.py` and `bokeh serve`:
- the embedded dataset is decoded once per app process, held read-only and shared by every session (one cache entry; never in Stata's process or a trial render);
- at most `maxsessions()` sessions are open at once (default 20, `--max-sessions N`, 0 refused); beyond it the page request gets a static HTTP 503 with `Retry-After: 30` and no script or refresh, under S04's policy (`python app.py`, `dash serve`), or the same text with no figure when no HTTP hook exists (`bokeh serve`);
- a session with no filter, brush or CSV activity for `idletimeout()` minutes (default 60, `--idle-timeout M`, 0 never) is closed: its document is cleared, it shows a reload message and frees its place; Bokeh's own unused-session lifetimes are set explicitly (15 s, checked every 5 s);
- lowess, fpfit and lpoly/lpolyci results are memoised per process (at most 64 MB, LRU, read-only results), and the app warms up before it listens, first printing `preparing the dashboard (N rows, <estimators>)` so a long warm-up is not read as a failure;
- per-session memory growth stays at most 80 MB at 200k rows × 3 layers (ratified 06oct2026, A116; 60.7 MB retained today already meets it, so the bound is a regression guard, not a reduction this section makes);
- the saved page is unchanged.

**Why one section.** The cap, the idle close, the shared payload and the warm-up all live in the generated app's session life cycle (`make_document`, `_dash_server_app`, the app's `__main__`) and its launcher flags; S57's worker restructures only the move path afterwards (A138: P1.31a S46, its worker S57).

**Test order and commit rule (rule 7).** One cycle on `wp30-s46`: 46-01 and 46-02 write every regression test and run them against the unmodified batch-16 base, saving `$S/46-P1.31a-failure.txt` (no commit); 46-03 to 46-10 fix, measure and document; 46-11 closes the entry and makes the one commit. No test-only commit exists, and no commit is red.

## Risk: [yellow] — the generated app's session life cycle, a HIGH launcher, an auth hook in front of every page, and shared state across sessions

**Why.**
- `ServerAppBuilder._generate_app_source` is HIGH (5 impacted, 3 processes; research §6); S46 is batch 16's only editor of it (R12).
- `_dash_launch_app` is HIGH at the batch base (index 16.0); `main`'s `gitnexus impact` is UNKNOWN (four `main` symbols; research critic 2).
- `ServerAppBuilder._glyph_layer_lines` and `_shared_stat_lines` (the copy lists) are HIGH (4 impacted).
- `_dash_limits` is CRITICAL and is not edited (the new limits are launcher flags, not spec limits).
- The template's `make_document`, `_dash_server_app`, `_dash_arg_parser`, `_dash_apply_limits` and `__main__` are strings, not indexed (UNKNOWN); covered by the app tests and `app:` map entries.
- dash.ado `_dash_serve_spec` (8272), `_dash_serve` (8369) and `_dash_build` (8072) are UNKNOWN (not indexed); one definition each.

**Risk factors.**
1. A shared frame written in place by one session would leak into every other session.
2. In-process documents (the warm-up, S23's trial, every in-process test) never fire `on_session_destroyed` and would hold slots for ever.
3. A `sys.modules` cache keyed per payload grows without bound in a pytest worker and, through S23's trial, inside Stata's own Python.
4. A 503 raised as `HTTPError` loses `Retry-After` (tornado's `send_error` clears headers), and a busy check before the key check would tell a keyless client the session count.
5. A warm-up of about 28 s (lowess, 100k rows) runs past the launcher's 30 s "no answer" line.
6. The memo sits beside the saved renderer's estimators; a rebinding there would change saved pages.
7. Bokeh's session APIs (`unused_session_lifetime_milliseconds`, `check_unused_sessions_milliseconds`, `Document.on_session_destroyed`, AuthProvider `get_user_async` in `prepare`) must hold across S41's window.

**Mitigation.**
1. Every shared numpy array is made read-only (`flags.writeable = False`); each session gets `copy.deepcopy(spec)`, copies of the small meta dicts and a shallow `DataFrame.copy(deep=False)`; the move snapshot `_orig_src_data` stays per session, as today (not shared; ratification 06oct2026). `TestTheDataIsDecodedOncePerProcess::test_a_move_in_one_session_leaves_another_alone` pins it.
2. The cap counts only documents with a `session_context` (the rule of `_dash_session_token_ok`, dash_render.py:4114-4122); `test_in_process_documents_take_no_slot`.
3. One entry (replaced on a new key), skipped under S23's `_DASH_TRIAL` and when `sfi` is importable in the process (register P1.31.8); tests for each.
4. The busy response is written by the handler itself (status, `Retry-After`, S04's headers, constant body, then `tornado.web.Finish`), and the cap wrapper runs only after the key gate admitted the request (`_dash_cap_auth` wraps `_dash_token_auth`, which is not edited).
5. The `preparing …` line is printed before the warm-up starts, flushed; a launcher test pins its order before any `no answer` line.
6. The memo is applied only inside the generated app (rebinding the copied class and module names); `TestTheSavedPageIsUnchanged` compares a saved page's bytes with the base's.
7. `TestBokehLifetimesAreSet` and the live cap tests run on the batch's bokeh; 46-10 runs them under S41's 3.10 scratch venv when S41 left one (E12).

## Dependencies

- **Depends on: 04, 23, 25, 41.**
  - S04 (batch 2): the served CSP and security headers (`_DASH_CSP_SERVED`, `_DASH_SECURITY_HEADERS` at dash_render.py:3699/3714) and `default-src 'none'` on empty pages (IR-17 P1.29.8); the busy and idle pages are served under them.
  - S23 (batch 8): the build-time trial and its `_DASH_TRIAL` flag, and the relay of the child's notes through `_dash_launch_app` (IR-10: "S46's warm-up later makes that render happen before the server listens").
  - S25 (batch 9): the dependency guard at the top of the generated app; S46 adds nothing above it.
  - S41 (batch 14): the verified bokeh window and `_DASH_BOKEH_INTERNALS` (TR-41.18: `(internal, guard, test)` triples; "S46 and S57 verify theirs across the window"). S41 keeps no process holder; S23's is `sys.modules["_dash_app_notes"]` (notes only), so S46 creates its own.
  - S01 provides the open entry `P1.31a`, its `WP30_OPEN` key, the markers `<!-- WP-30 P1.31a -->` at the ends of `### New` and `### Security`, the S46 stub and the map anchors `# WP-30 S46 (P1.31a): Served session capacity and memory (P1.31 part a)`.
- **Blocks: 57.** S57 moves the recompute to a worker; an idle close (this section) must bump its generation, and S57 audits `_dash_touch` among the move path's call sites.
- **Parallel batch: 16**, merge order S45, S46, S47.
- **Can run with:** S45 (dash.ado plot parser and mappers) and S47 (S21's finishers, `_dash_plot_margin`, schemes) touch none of S46's symbols; S46 edits neither `_make_figure_body` nor a finisher.

## Evidence

Anchors are at `c96facd`; earlier batches move them. The executor re-finds each by symbol.

### E1. The session gates (template in `_generate_app_source`)

`make_document` (template :34712) sets the CSP template, resets notes, runs Gate B (`_dash_session_token_ok`, :34733), the per-minute limiter (:34741-34752, a 429 Div), then decodes:

```python
34754            "    spec, df, meta = _load_spec_and_data()",
```

Gate A is `_dash_token_auth` (dash_render.py:4083-4111), an AuthProvider whose `get_user_async` raises `HTTPError(403)` in `prepare`; the Server is built in `_dash_server_app` (template :36416; kwargs :36482-36490):

```python
            "    _dash_srv = Server(",
            "        {'/': Application(FunctionHandler(make_document))},",
            "        port=_p,", ... "        num_procs=1,",
            "        extra_patterns=[('/health', _HealthHandler)],",
            "        auth_provider=_dash_token_auth(_DASH_SERVE_TOKEN),",
            "        **_kw",
```

### E2. The app's command line and launcher

The app's flags are `_dash_arg_parser` (template :34457) with `_dash_limit_value` (:34440, ASCII digits 1..1,000,000) and `_dash_apply_limits` (:34509); its `__main__` (:36501) parses, applies the limits and starts the server (:36567). The banner line `Session limits per minute: …` is :36591. The launcher `_dash_launch_app` (37206; `ready_seconds=30.0`) builds the child's argv (:37318-37326):

```python
    _cmd = [sys.executable, "-P", "-c", _DASH_BOOT, app_path, "--port", str(port)]
    if not no_browser: _cmd.append("--show")
    if timeout > 0: _cmd += ["--timeout", str(timeout)]
```

and prints `no answer from …/health after 30 s; still waiting` (:37473-37480). The renderer's own `__main__` argparse starts at 37553.

### E3. Activity call sites and the snapshot (template)

`w.on_change(_attr, _dash_event_throttle(doc, _cb_for_w))` (:36098, filters), `_bsrc.selected.on_change('indices', _dash_event_throttle(` (:36186, brush), `_csv_send = _dash_event_throttle(doc, _send_csv,` (:36218, CSV). `_dash_event_throttle` (24330) is not edited (research §4a.3). The per-session snapshot: `_orig_src_data[id(_s)] = {c: list(v) for c, v in _s.data.items()}` (:35798).

### E4. dash serve's options (dash.ado)

`_dash_serve_spec` (8272) owns `PORT(string) NOBRowser TIMEOUT(string)` (:8294-8301), checks them byte by byte with `_dash_is_digits` (:8303-8337, never a regular expression: P20-14, P20-19), and returns `r(port)`/`r(timeout)` (:8356-8360); `_dash_serve` (8369) builds `sys.argv` (:8455). `dash build, server` prints `Limits:    --sessions-per-client N  --new-clients-per-minute N  --sessions-per-minute N` (:8240).

### E5. Help

dash.sthlp Subcommands' dash serve table (:857-874), Server Mode's flag list (:1606-1611) and the bokeh serve caveat (:1636-1641: the app's limits do not apply there), the limits text (:1740-1771, "one process, one event loop" :1779-1780), Resource limits (:1889-2002).

### E6. Existing tests that must stay green

`test_served_throttle.py`, `test_server_rate_limit.py`, `test_serve_token.py`, `test_serve_lifecycle.py`, `test_serve_launcher.py`, `test_server_serves.py`, `test_mode_parity.py`, `test_estimator_cost.py`, `test_stat_truth*` (lowess values unchanged), `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_serve_options.cscript`, `test_serve_launch.cscript`. No existing test pins the absence of a cap (research §5); none is flipped.

### E7. Blast radius (index 16.0 and research §6)

| Symbol | Risk | Edited? |
|---|---|---|
| `ServerAppBuilder._generate_app_source` | HIGH (5) | yes (template) |
| `_dash_launch_app` | HIGH | yes (two keywords, argv) |
| `ServerAppBuilder._glyph_layer_lines`, `_shared_stat_lines` | HIGH (4) | copy-list entries only |
| `_dash_limits` | CRITICAL | no |
| `_dash_event_throttle`, `_dash_token_auth`, `_dash_session_token_ok` | UNKNOWN / LOW | no (wrapped) |
| `GlyphMapper._stata_lowess`, `GlyphMapper._fp_fit`, `_compute_lpoly_fit`, `_lpoly_se` | LOW | no (rebound in the app only) |

## User stories

- **US-46.1** As a dashboard publisher, I want a cap on open sessions with a clear busy page, so that many readers cannot exhaust the machine's memory.
- **US-46.2** As a dashboard publisher, I want idle sessions closed after a set time, so that forgotten tabs do not hold memory for ever.
- **US-46.3** As a dashboard reader, I want the first page to open without paying the dataset decode and the slow fit, and a reload message when my idle session was closed.
- **US-46.4** As a Stata user running `dash serve`, I want to set the cap and the idle time with `maxsessions()` and `idletimeout()`, and to see why a large dashboard is slow to start.

## Business requirements

- **BR-46.1** The embedded data is decoded once per app process; sessions share it and cannot change what another session draws.
- **BR-46.2** At most N sessions are open at once (default 20; 1 to 1,000,000; 0 refused) under `dash serve`, `python app.py` and `bokeh serve` (per process under `--num-procs`); beyond N a page request gets HTTP 503 with `Retry-After: 30`, a constant message naming the setting, no script and no refresh; a client without the key still gets 403.
- **BR-46.3** A session with no filter, brush or CSV activity for M minutes (default 60; 0 never) is closed with a reload message and frees its place; a closed tab frees its place within about 20 s.
- **BR-46.4** The app prints `preparing the dashboard (N rows, …)` and builds one document before it listens; no session pays the first build.
- **BR-46.5** Per-session memory growth is at most 80 MB at 200k × 3 (a regression guard: 60.7 MB retained and about 72 MB mean RSS growth today already meet it); the estimator memo holds at most 64 MB per process and never runs in Stata's process or a trial render.
- **BR-46.6** `dash serve maxsessions(#) idletimeout(#)` set them, digits only, refused r(198) otherwise; `dash build, server` lists the flags.
- **BR-46.7** Saved pages are byte-identical to before.

## Technical requirements

### Module-level (dash_render.py; copied into the app)

- **TR-46.1 Constants** (beside `_DASH_EVENT_RATE`, 24326; copy list after `"_DASH_EVENT_RATE", "_DASH_EVENT_BURST",` (32950), R2): `_DASH_MAX_SESSIONS = 20`; `_DASH_IDLE_MINUTES = 60`; `_DASH_IDLE_MINUTES_MAX = 525600`; `_DASH_IDLE_CHECK_MS = 60000`; `_DASH_UNUSED_SESSION_MS = 15000`; `_DASH_CHECK_UNUSED_MS = 5000`; `_DASH_BUSY_RETRY_S = 30`; `_DASH_MEMO_BYTES = 64 * 1024 * 1024`; `_DASH_SESSION_ENV = ("DASH_MAX_SESSIONS", "DASH_IDLE_TIMEOUT")`; `_DASH_BUSY_HTML` (constant: "503 Server busy: this dashboard already has the most sessions open that it allows (dash serve maxsessions(), --max-sessions). Close another tab of it, or wait half a minute and reload."); `_DASH_IDLE_HTML` (constant: "This session was closed after %d minutes without a filter, brush or download; reload the page to open a new one."; the `%d` is filled only with the validated int `_DASH_STATE.idle`, and the constant holds no other `%`). Each comment names its threat (rule 1).
- **TR-46.2 Validators.** `_dash_session_cap_value(text)` (ASCII digits only, 1..1,000,000, else `argparse.ArgumentTypeError` quoting at most 40 characters) and `_dash_minutes_value(text)` (ASCII digits only, 0.._DASH_IDLE_MINUTES_MAX). `_dash_session_defaults(environ)` returns `(cap, idle)` from `_DASH_SESSION_ENV` through the two validators, else the constants; an invalid environment value raises ValueError naming the variable (fail closed: the app does not start with a cap it did not mean).
- **TR-46.3 The process holder.** `_dash_served_state()` returns the one per-process `types.SimpleNamespace` kept as `sys.modules["_dash_served_state"]` (S23's `_dash_app_notes` pattern), with `payload_key`, `payload`, `open` (dict doc id → True), `cap`, `idle`, `memo` and `memo_lock` (a `threading.Lock`, Q-57.1). It is created once, so `bokeh serve`, which runs the module per session, shares it.
- **TR-46.4 Slots.** `_dash_session_open(state, doc)` → False when `len(state.open) >= state.cap` and `doc.session_context` is not None; otherwise records `id(doc)` (only for a document with a session context), registers `doc.on_session_destroyed(lambda ctx: _dash_session_release(state, key))` and returns True. `_dash_session_release(state, key)` pops the key once (idempotent). A document with no session context takes no slot.
- **TR-46.5 `_dash_idle_due(last_active, now, minutes)`** → `minutes > 0 and now - last_active >= minutes * 60` (pure; clock passed in).
- **TR-46.6 `_dash_cap_auth(inner, state)`** returns an AuthProvider (built with lazy tornado/bokeh imports, as `_dash_token_auth`) whose `get_user_async` awaits the inner provider's (which raises 403 without the key), then, only when the handler is Bokeh's document page handler (`bokeh.server.views.doc_handler.DocHandler`) and the slots are full, calls `handler.clear()`, `handler.set_status(503)`, sets `Retry-After: 30`, every header of `_DASH_SECURITY_HEADERS` and `Content-Security-Policy: default-src 'none'`, `Content-Type: text/html; charset=utf-8`, writes `_DASH_BUSY_HTML`, `handler.finish()` and raises `tornado.web.Finish()`. It logs one refusal line per minute (as `_RateLimiter` does) with no request data. `get_login_url` delegates to the inner provider. Any other route that creates a session (Bokeh's autoload handler, a websocket naming a new session id) meets the in-document check of TR-46.9 instead, so the cap holds on every path.
- **TR-46.6a Internals (S41's list).** `_DASH_BOKEH_INTERNALS` gains two triples: `("bokeh.server.views.doc_handler.DocHandler", "_dash_cap_auth refuses to build without it", "test/test_served_resources.py::TestSessionsAreCapped::test_the_fourth_page_is_busy")` and `("AuthProvider.get_user_async awaited in prepare; tornado.web.Finish ends the request", "_dash_cap_auth checks the attribute at build", "test/test_served_resources.py::TestSessionsAreCapped::test_a_keyless_client_gets_403_not_503")`. When either is missing `_dash_cap_auth` raises RuntimeError and the server does not start (fail closed, A109).
- **TR-46.7 `_dash_shared_payload(state, spec_b64, data_b64, loader)`.** Key = sha256 of the two literals. When `state.payload_key` equals it, reuse; else call `loader()` once, make every numpy array of the frame's blocks and of `meta['qual_masks']` read-only, and store the entry (replacing any earlier one). Return `(copy.deepcopy(spec), df.copy(deep=False), {k: (dict(v) if isinstance(v, dict) else v) for k, v in meta.items()})`. When `_DASH_TRIAL` is set (S23) or `"sfi" in sys.modules`, call `loader()` and store nothing.
- **Imports in copied helpers.** Every TR-46.2-TR-46.8 function imports the standard modules it uses inside its own body (`import sys`, `types`, `copy`, `threading`, `hashlib`), as dash_render.py's own helpers do (`import sys` at :4240) and as `_dash_token_auth` imports tornado lazily: the generated app's header (template :34101-34106) imports none of them, and `TestTheServedAppDefinesEveryNameItReads` would otherwise fail on a copied name.
- **TR-46.8 The memo** (`_shared_stat_lines`' function tuple, new last entry after `_stata_if_to_pandas` (33590), R2): `_dash_memo_key(name, args, kwargs)` (blake2b over each numpy argument's dtype, shape and bytes, and `repr` of every other argument except `self`); `_dash_memo_wrap(fn, name, state, method=False)` returning a wrapper that looks the key up in `state.memo` (an `OrderedDict` with a byte total), returns copies marked read-only, inserts results whose `nbytes` total fits `_DASH_MEMO_BYTES` and evicts least-recently-used entries past it. **The lock (orchestrator ruling Q-57.1, in this section's commit):** every get (lookup plus `move_to_end`) and every put (insert, byte total, eviction) runs under `with state.memo_lock:`, and `fn` itself runs outside the lock, so a long fit never blocks another session's hit; two concurrent misses on one key may both compute, and the second put replaces the first without changing the byte total twice. S57's recompute worker relies on this lock and adds none of its own; it calls `fn` directly when `_DASH_TRIAL` is set or `"sfi" in sys.modules`. Results keep NaN bit patterns (copy, never recompute).

### The generated app (`_generate_app_source`; S46 is batch 16's only editor, R12)

- **TR-46.9 make_document.** After the limiter (E1) and before the decode: `if not _dash_session_open(_DASH_STATE, doc): doc.add_root(Div(text=_DASH_BUSY_HTML)); return` (the `bokeh serve` path and the race past Gate A). `spec, df, meta = _dash_shared_payload(_DASH_STATE, _SPEC_B64, _DATA_B64, _load_spec_and_data)` replaces :34754; `_load_spec_and_data` stays the loader. For a document with a session context: `_last = [time.monotonic()]`; `_dash_touch = lambda fn: (lambda *a, **k: (_last.__setitem__(0, time.monotonic()), fn(*a, **k))[1])`; the three call sites of E3 become `_dash_event_throttle(doc, _dash_touch(<fn>))` (the throttle itself unchanged); when `_DASH_STATE.idle > 0` a periodic callback every `_DASH_IDLE_CHECK_MS` checks `_dash_idle_due(_last[0], time.monotonic(), _DASH_STATE.idle)` and, when due, removes the document's periodic callbacks, calls `doc.clear()`, adds `Div(text=_DASH_IDLE_HTML % _DASH_STATE.idle)` and calls `_dash_session_release`. The snapshot :35798 is not edited: `_orig_src_data` stays a per-session `list` copy (P2.41 owns it with `.tolist()` and the index lists; ratification 06oct2026). `_DASH_STATE = _dash_served_state()` is set once at module level, with `cap, idle = _dash_session_defaults(os.environ)`.
- **TR-46.10 The app's command line.** `_dash_arg_parser` gains `--max-sessions N` (type `_dash_session_cap_value`, default `_DASH_STATE.cap`) and `--idle-timeout MINUTES` (type `_dash_minutes_value`, default `_DASH_STATE.idle`); `__main__` sets `_DASH_STATE.cap`/`.idle` from them right after `_dash_apply_limits(_a)`. The banner gains `Sessions open at once: N; idle sessions close after M minutes (0 = never)` beside :36591.
- **TR-46.11 Server lifetimes and the cap gate.** `_dash_server_app`'s `Server(...)` gains `unused_session_lifetime_milliseconds=_DASH_UNUSED_SESSION_MS`, `check_unused_sessions_milliseconds=_DASH_CHECK_UNUSED_MS` and `auth_provider=_dash_cap_auth(_dash_token_auth(_DASH_SERVE_TOKEN), _DASH_STATE)`.
- **TR-46.12 Warm-up.** In `__main__`, after the parse and before `_server.start()` (:36567): print, flushed, `preparing the dashboard (<rows> rows, <names>)`, `<rows>` from the decoded payload and `<names>` the estimator layers of the spec (lowess, lpoly, lpolyci, fpfit, fpfitci, kdensity) or `no estimators`; then `make_document(Document())` inside `try`, its notes relayed as S23 relays the first render's (IR-10). After the class copies the app rebinds `GlyphMapper._stata_lowess`, `GlyphMapper._fp_fit` (`method=True`), `_compute_lpoly_fit` and `_lpoly_se` through `_dash_memo_wrap` (P1.31.8).

### Launcher and Stata

- **TR-46.13 Launcher.** The renderer's `__main__` argparse (37553) gains `--max-sessions` and `--idle-timeout` with the same validators; `_dash_launch_app(..., max_sessions=None, idle_timeout=None)` appends `--max-sessions <int>` and `--idle-timeout <int>` to `_cmd` when given (ints, never text). The launcher's 30 s line is unchanged; the child's `preparing …` line reaches the user first (stdout forwarded, WP-29 P0.13).
- **TR-46.14 dash.ado.** `_dash_serve_spec` declares `MAXSESSIONS(string) IDLETIMEOUT(string)` (full names), checks each with `_dash_is_digits` (maxsessions at most 7 digits and 1..1,000,000; idletimeout at most 6 digits and 0..525,600), refuses with `dash serve: maxsessions() must be an integer from 1 to 1,000,000 (got: <as typed through _dash_say>)` or `dash serve: idletimeout() must be a whole number of minutes from 0 to 525600 (got: …)`, r(198), writes each as `strofreal(real(), "%12.0f")`, and returns `r(maxsessions)`, `r(idletimeout)` (empty when not given). `_dash_serve` appends `"--max-sessions", "<n>"` and `"--idle-timeout", "<m>"` to `sys.argv` when non-empty. `_dash_build`'s Limits line (:8240) gains `--max-sessions N  --idle-timeout MINUTES`. Every new line follows `version 19` programs' rules (R6).
- **TR-46.15 Copy lists (R2 row S46).** Constants: TR-46.1's names after `"_DASH_EVENT_RATE", "_DASH_EVENT_BURST",`. Functions: `"_dash_session_cap_value", "_dash_minutes_value", "_dash_session_defaults", "_dash_served_state", "_dash_session_open", "_dash_session_release", "_dash_idle_due", "_dash_cap_auth", "_dash_shared_payload",` after `"_dash_limits", "_dash_limit_hint",` (33302). `_shared_stat_lines`: `_dash_memo_key, _dash_memo_wrap` after `_stata_if_to_pandas`. `test_every_listed_name_exists` (A149) and `TestTheServedAppDefinesEveryNameItReads` guard them.
- **TR-46.16 Maps.** Under S46's anchors: `test/function_test_map.py` `FUNCTIONS` gains each TR-46.2-TR-46.8 function mapped to its `test/test_served_resources.py` test; `test/program_coverage_map.py` is unchanged: no Stata program is added, and `_dash_serve_spec` (:283) and `_dash_serve` (:291) are already mapped.
- **TR-46.17 Help** (R3: Subcommands, Server Mode, Resource limits). The dash serve table gains `maxsessions(#)` and `idletimeout(#)`; Server Mode's flag list gains the two flags; the bokeh serve caveat states that the cap, idle close, shared data and memo apply there with `DASH_MAX_SESSIONS`/`DASH_IDLE_TIMEOUT` (per process under `--num-procs`), the busy text then shown in the page; Resource limits gains "Sessions open at once" (the cap, 503, Retry-After), the idle rule (what counts as activity; a tab only being looked at can need a reload, A111), the memory bound (each session adds at most about 80 MB at 200k rows by 3 layers, measured by the test suite, not checked at run time; at the default cap of 20 that is up to about 1.9 GB with the server's own 221 MB and the 64 MB memo, so set maxsessions() to fit the machine), the warm-up line, and that opening a session still runs on the event loop (P2.57).
- **TR-46.18 Security (rule 1; G9, threat: memory exhaustion of the served app by open sessions).** Constant bodies with no request data; the cap check after the key gate; read-only shared arrays; one cache entry; the memo bounded and keyed by a cryptographic hash; digits-only values in Stata, the launcher, the app and the environment; no `shell=True`, no `eval`; no script in either page.

## Boundaries

- **Batch partners:** S45 (dash.ado plot parser, `_dash_recast_opt`, mapper tails, `_dash_layer_series`) and S47 (`_dash_plot_margin`, `_dash_padded_range`, S21's finishers, the scheme extractor and files). S46 edits none of them.
- **Not edited:** `_dash_limits`, `_dash_event_throttle`, `_dash_token_auth`, `_dash_session_token_ok`, `ServerAppBuilder.build`, `_make_figure_body`, the move path inside `_on_filter_change` (S57's), the saved renderer's estimators.
- **Later:** S57 (worker, generation counter; bumps on idle close through `_dash_session_release`); P2.41 (`.tolist()`, the index lists and the per-session `_orig_src_data` snapshot, register P1.31.7); P2.57 (session open on the loop).
- **Not this section's (register P1.31.6, P1.31.9):** a per-client cap; exposing the three rate limits on `dash serve`.

## Stata truth

None: twoway has no server, sessions or event loop (research §3). S46's stub block in `test/test_wp30_truth.cscript` (header `* ==== S46 P1.31a: Served session capacity and memory ====`, S01's) keeps its two lines and gains one comment line between them (comment lines are ignored by `_wp30_blocks`' first/last-statement check, TR-01.7), `* S46: no twoway counterpart (research p1-31 section 3); tested by test_served_resources.py and test_serve_options.cscript MS-01..MS-08.`

### Area cases, `test/test_serve_options.cscript` (R1; one contiguous run at the end of its last case block)

Each case calls `_dash_serve_spec` (or `dash build, server`) and checks rc, the error line and the returns, printing `MS-nn PASS: …`. Header `// MS: maxsessions() and idletimeout() (WP-30 P1.31a)`.
- **MS-01** `maxsessions(3) idletimeout(5)`: rc 0, `r(maxsessions)` "3", `r(idletimeout)` "5".
- **MS-02** `maxsessions(0)`, `maxsessions(-1)`, `maxsessions(1e3)`, `maxsessions(3.5)`, `maxsessions(1000001)`, `maxsessions(12345678901)`: r(198), the words of TR-46.14.
- **MS-03** `maxsessions(3` + char(10) + `)` and a 400-digit value: r(198), echoed as typed through `_dash_say`.
- **MS-04** `idletimeout(0)` rc 0; `idletimeout(525601)`, `idletimeout(-1)`, `idletimeout(5m)`: r(198).
- **MS-05** `maxsessions(007)` returns "7".
- **MS-06** neither given: both returns empty, and `_dash_serve`'s argv (read from the `python:` statement it builds, through the existing argv probe of `test_serve_launch.cscript`'s form) holds neither flag.
- **MS-07** `maxs(3)`: not a dash serve option, reaches the build options as today (the existing unknown-option behaviour, checked unchanged).
- **MS-08** `dash build, server saving(<tmp>/app.py)`: the log's Limits line contains `--max-sessions N  --idle-timeout MINUTES`.

## TDD test stubs

### Regression tests, new `test/test_served_resources.py` (red at the batch-16 base unless marked guard; 46-01)

Live tests use `test_serve_lifecycle.py`'s in-process server harness (`_dash_server_app` in a thread, `pull_session`, the test key) and its marker; unit tests import the generated app through `ServerAppBuilder` as `test_served_throttle.py` does.
- Test: `…::TestTheHelpers::test_idle_due` (fake clock: 0 never; 59.9 min not due; 60 due), `::test_cap_value[good|bad]` (`"20"`, `"1000000"`; `"0"`, `"-1"`, `"1_000"`, `" 20"`, `"２０"`, `"9"*400`), `::test_minutes_value[...]`, `::test_defaults_from_the_environment` (valid, invalid raises naming the variable). Red: AttributeError.
- Test: `…::TestTheDataIsDecodedOncePerProcess::test_five_documents_decode_once` (patch `_dash_read_data_json` in the app module: 1 call for 5 `make_document`s; 5 at the base). Red.
- Test: `…::TestTheDataIsDecodedOncePerProcess::test_shared_arrays_are_read_only` and `::test_a_move_in_one_session_leaves_another_alone` (a dropdown move in document 1, then document 2 draws the full data). Red: AttributeError / guard.
- Test: `…::TestTheDataIsDecodedOncePerProcess::test_two_module_runs_share_it` (exec the app source twice in one process, as `bokeh serve` does: one decode). Red.
- Test: `…::TestTheDataIsDecodedOncePerProcess::test_skipped_in_a_trial[_DASH_TRIAL|sfi]` and `::test_one_entry_only` (a second payload replaces the first). Red.
- Test: `…::TestSessionsAreCapped::test_the_fourth_page_is_busy` (`--max-sessions 3`, three held sessions; a fourth GET: status 503, `Retry-After: 30`, body equals `_DASH_BUSY_HTML`, `Content-Security-Policy: default-src 'none'`, no `<script`). Red: 200.
- Test: `…::TestSessionsAreCapped::test_a_keyless_client_gets_403_not_503`, `::test_a_closed_session_frees_its_place` (lifetimes patched short), `::test_in_process_documents_take_no_slot` (25 `make_document(Document())` with cap 3), `::test_bokeh_serve_path_shows_the_busy_text` (session context faked, slots full: the document holds one Div, no figure, and the payload was not decoded). Red.
- Test: `…::TestIdleSessionsAreClosed::test_closed_after_the_lifetime` (fake clock; the document then holds only the reload Div; the slot is released), `::test_activity_resets_the_clock` (a filter, a brush and a CSV call each), `::test_zero_means_never`, `::test_memory_is_freed` (tracemalloc: at least 80% of the document's data freed after `doc.models.flush_synced()`, research m10). Red.
- Test: `…::TestBokehLifetimesAreSet::test_server_kwargs` (the Server's tornado application carries 15000 and 5000). Red.
- Test: `…::TestTheLauncherFlags::test_app_parser`, `::test_launch_app_passes_them` (fake Popen: `--max-sessions 7 --idle-timeout 0` in argv), `::test_renderer_main_accepts_them`, `::test_banner_names_them`. Red.
- Test: `…::TestTheWarmUp::test_preparing_line_comes_first` (run the app's `__main__` with a fake Server: the first stdout line starts `preparing the dashboard (74 rows, lowess)` and the warm-up document was built before `start`), `::test_launcher_order` (a fake child printing the preparing line, then answering /health after 31 s: the preparing line precedes `no answer`). Red.
- Test: `…::TestEstimatorMemo::test_second_document_calls_lowess_zero_times` (lowess at 20k), `::test_results_bit_equal` (NaNs included), `::test_misses[array|bw|mean|noweight]`, `::test_budget_evicts_lru`, `::test_the_lock_guards_get_and_put` (8 threads, 2,000 mixed hits and misses on a small budget: the byte total equals the sum of the held entries, never exceeds `_DASH_MEMO_BYTES`, and no `RuntimeError: OrderedDict mutated during iteration`; `state.memo_lock` is a `threading.Lock`), `::test_never_in_stata_or_a_trial`, `::test_the_saved_renderer_is_untouched` (`dash_render.GlyphMapper._stata_lowess` is the original after an app is built). Red.
- Guard: `…::TestPerSessionMemory::test_growth_at_most_80_mb` (live, 200k × 3 layers, 6 held sessions, mean RSS growth of sessions 2-6 ≤ 80 MB; the measured value printed). Expected to pass at the base (m1: 60.7 MB retained; m2: (2016 − 357) / 23 ≈ 72 MB mean RSS growth), so it is a regression pin, not a fix; 46-01 records the base value under "Guards". Should it measure above 80 MB at the base, 46-01 lists it as failing instead and the decode-once of 46-05 must bring it under.
- Guard: `…::TestTheSavedPageIsUnchanged::test_digest` (a fixed spec's saved page sha256 equals the value 46-01 records at the base, with a comment naming the base sha).

## Test plan

| What | How | Fixture / data | Mode |
|---|---|---|---|
| Validators, holder, idle rule | pytest `TestTheHelpers` | literals | n/a |
| Decode once, read-only, isolation | pytest `TestTheDataIsDecodedOncePerProcess` | auto, generated rows | served |
| Cap, 503, key first, bokeh serve path | pytest `TestSessionsAreCapped` (live) | auto | served |
| Idle close, activity, memory freed | pytest `TestIdleSessionsAreClosed` | auto | served |
| Lifetimes, flags, banner, warm-up order | pytest `TestBokehLifetimesAreSet`, `TestTheLauncherFlags`, `TestTheWarmUp` | — | served, launcher |
| Memo | pytest `TestEstimatorMemo` | generated 20k | served; saved untouched |
| Memory bound (guard, ≤ 80 MB) | pytest `TestPerSessionMemory` (live) | 200k × 3 | served |
| Stata options | cscript MS-01..MS-08 | — | n/a |
| Saved page unchanged | `TestTheSavedPageIsUnchanged`; `test_mode_parity.py` | auto | saved |
| Copy lists, maps | `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads`, map tests | — | served |

**Acceptance criteria.**
- **AC-46.1** (BR-46.1) `TestTheDataIsDecodedOncePerProcess` passes (1 decode for 5 documents; isolation; one entry; skipped in a trial and in Stata).
- **AC-46.2** (BR-46.2) `TestSessionsAreCapped` passes: 503 with `Retry-After: 30` and the constant body at N+1, 403 without the key, in-process documents exempt.
- **AC-46.3** (BR-46.3) `TestIdleSessionsAreClosed` and `TestBokehLifetimesAreSet` pass.
- **AC-46.4** (BR-46.4) `TestTheWarmUp` passes; 46-10 records the warm-up line and time for lowess at 100k.
- **AC-46.5** (BR-46.5) `TestPerSessionMemory` passes (≤ 80 MB) and `TestEstimatorMemo` passes.
- **AC-46.6** (BR-46.6) MS-01..MS-08 PASS; `TestTheLauncherFlags` passes.
- **AC-46.7** (BR-46.7) `TestTheSavedPageIsUnchanged` and `test_mode_parity.py` pass; E6's files report 0 failed; the full suite reports 0 failed; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 46-01 to 46-11 form one commit, made by 46-11 on `wp30-s46` with the subject `Cap and expire served sessions and decode the data once per process (WP-30 P1.31a)`; its body names the threat (memory exhaustion by open sessions; G9). `<scratch>` and `$SLOT` as in section 45; `$S` is `<scratch>/s46` (46-01 runs `mkdir -p "$S"`; S45, S46 and S47 run in parallel, so no log or slot directory is shared); `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s46`; cscripts through the driver with `WP30_ONLY=S46`.

<task type="auto" id="46-01">
  <name>Write the served resource tests</name>
  <files>test/test_served_resources.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "<scratch>/batch-16-base.txt"` and the branch is `wp30-s46`; stop otherwise. `mkdir -p "$S"`. Check the prefix is free: `grep -lE '(^|[^A-Za-z0-9_])MS-[0-9]' "$WT"/test/*.cscript "$WT"/test/*.py "$WT"/test/*.do` prints nothing. Create `test/test_served_resources.py` with every stub of "TDD test stubs", naming new symbols through the generated app module and `dr.` so they fail with AttributeError now; record the guard digest of `TestTheSavedPageIsUnchanged` at this base in the test with a comment naming the sha. Run `python3 -m pytest test/test_served_resources.py -q -n 6 -p no:cacheprovider -rf > "$S/46-new.log" 2>&1`. Write `$S/46-P1.31a-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)" with `TestTheSavedPageIsUnchanged` and `TestPerSessionMemory` (its measured growth in MB against the 80 MB bound). Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/46-new.log"` is at least 30; `python3 -m pytest test/test_served_resources.py -q -n0 -p no:cacheprovider -k TestTheSavedPageIsUnchanged` passes; `git -C "$WT" diff --name-only -- dash.ado dash_render.py` prints nothing.]]></verify>
  <done>Every pytest regression test for the cap, the idle close, the shared payload, the memo and the warm-up was shown failing on the unmodified tree, with the saved-page guard passing and the 80 MB memory guard's base value recorded.</done>
</task>

<task type="auto" id="46-02">
  <name>Write the dash serve option cases</name>
  <files>test/test_serve_options.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    In `test/test_serve_options.cscript`, as one contiguous run at the end of its last case block, add the header `// MS: maxsessions() and idletimeout() (WP-30 P1.31a)` and MS-01..MS-08 of "Stata truth" in the script's own pass/fail form. In `test/test_wp30_truth.cscript` add only the one comment line of "Stata truth" between S01's S46 start and end lines. Run `test_serve_options.cscript` through the driver on the unmodified shipped files and append every `MS-nn FAIL` line to `$S/46-P1.31a-failure.txt` (MS-07 is a guard). Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "MS-0[1-6] FAIL|MS-08 FAIL" "$S/run_test_serve_options.log"` is at least 6; `grep -c "MS-07 PASS" "$S/run_test_serve_options.log"` prints 1.]]></verify>
  <done>The dash serve option cases were in place and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="46-03">
  <name>Add the session constants and helpers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_glyph_layer_lines` is HIGH (4 impacted). Apply TR-46.1 to TR-46.6 (constants beside `_DASH_EVENT_RATE`; `_dash_session_cap_value`, `_dash_minutes_value`, `_dash_session_defaults`, `_dash_served_state`, `_dash_session_open`, `_dash_session_release`, `_dash_idle_due`, `_dash_cap_auth` after `_dash_token_auth`'s family, each with a docstring naming its threat) and, in the same edit, TR-46.15's constants and functions entries at their anchors. Append to S41's `_DASH_BOKEH_INTERNALS` the triples of TR-46.6a. Do not edit `_dash_token_auth`, `_dash_session_token_ok` or `_dash_event_throttle`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_resources.py -q -n0 -p no:cacheprovider -k "TestTheHelpers"` passes; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_serve_token.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The cap, idle and busy-page building blocks existed, were pure or lazily imported, and travelled to the served app.</done>
</task>

<task type="auto" id="46-04">
  <name>Add the shared payload and memo</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-46.7 (`_dash_shared_payload`, read-only arrays, deep copies, one entry, replaced on a new key, skipped under `_DASH_TRIAL` and with `sfi` imported) and TR-46.8 (`_dash_memo_key`, `_dash_memo_wrap`, the byte budget and LRU, get and put under `state.memo_lock` per Q-57.1, `fn` outside it), each importing its standard modules in its body, adding `_dash_shared_payload` to the functions tuple after S46's other names and the memo pair to `_shared_stat_lines` after `_stata_if_to_pandas` (TR-46.15). Do not touch the saved renderer's estimators.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_resources.py -q -n 6 -p no:cacheprovider -k "test_skipped_in_a_trial or test_one_entry_only or test_results_bit_equal or test_misses or test_budget_evicts_lru or test_the_lock_guards_get_and_put or test_never_in_stata_or_a_trial"` passes; `python3 -m pytest test/test_estimator_cost.py test/test_stat_truth.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>A bounded one-entry payload cache and a 64 MB estimator memo existed, inert in Stata's process and in trial renders.</done>
</task>

<task type="auto" id="46-05">
  <name>Wire sessions into make_document</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `ServerAppBuilder._generate_app_source` is HIGH (5 impacted) and that S46 is batch 16's only editor of it (R12). Apply TR-46.9 in the template: `_DASH_STATE` at module level; the second cap check after the limiter; `_dash_shared_payload` in place of `_load_spec_and_data()` at :34754; `_dash_touch` at the three call sites of E3; the idle periodic callback. Leave the snapshot at :35798 per session. Leave `_on_filter_change`'s recompute steps as they are (S57's).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_resources.py -q -n 6 -p no:cacheprovider -k "TestTheDataIsDecodedOncePerProcess or TestIdleSessionsAreClosed or test_in_process_documents_take_no_slot or test_bokeh_serve_path_shows_the_busy_text"` passes; `python3 -m pytest test/test_served_throttle.py test/test_server_rate_limit.py test/test_mode_parity.py test/test_server_serves.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every served session shared the decoded data read-only, took a slot only with a session context, was stamped by filter, brush and CSV activity, and closed itself when idle.</done>
</task>

<task type="auto" id="46-06">
  <name>Gate pages and warm up</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-46.10 (the app's `--max-sessions` and `--idle-timeout`, set after `_dash_apply_limits`, and the banner line), TR-46.11 (the two lifetime keywords and `_dash_cap_auth` around `_dash_token_auth` in `_dash_server_app`) and TR-46.12 (the flushed `preparing the dashboard (...)` line, the warm-up document before `_server.start()`, the memo rebinding after the class copies). Verify on this tree's bokeh that `Server` accepts both keywords and that `prepare` honours `tornado.web.Finish` from `get_user_async`; record the bokeh version in `$S/46-notes.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_resources.py -q -n 6 -p no:cacheprovider -k "TestSessionsAreCapped or TestBokehLifetimesAreSet or test_app_parser or test_banner_names_them or test_preparing_line_comes_first or test_second_document_calls_lowess_zero_times or test_the_saved_renderer_is_untouched"` passes; `python3 -m pytest test/test_serve_token.py test/test_serve_lifecycle.py -q -n 6 -p no:cacheprovider` reports 0 failed (E6 for the flaky timing tests).]]></verify>
  <done>The app refused pages beyond its cap with a static 503 after the key check, set Bokeh's lifetimes explicitly, and warmed its cache and memo before listening, saying so first.</done>
</task>

<task type="auto" id="46-07">
  <name>Pass the flags through the launcher</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_launch_app` is HIGH (index 16.0). Apply TR-46.13: the renderer's `__main__` argparse (37553 at c96facd) gains `--max-sessions` and `--idle-timeout` with `_dash_session_cap_value` and `_dash_minutes_value`; `_dash_launch_app` gains `max_sessions=None, idle_timeout=None` and appends them to `_cmd` as ints; the `__main__` call passes them. Change nothing else in `_dash_launch_app`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_resources.py -q -n 6 -p no:cacheprovider -k "test_launch_app_passes_them or test_renderer_main_accepts_them or test_launcher_order"` passes; `python3 -m pytest test/test_serve_launcher.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The launcher accepted and forwarded the cap and idle time to the app, and the app's preparing line reached the user before any wait message.</done>
</task>

<task type="auto" id="46-08">
  <name>Add maxsessions and idletimeout to dash</name>
  <files>dash.ado</files>
  <action><![CDATA[
    `_dash_serve_spec`, `_dash_serve` and `_dash_build` are UNKNOWN to the index; confirm their callers with `grep -n` and record them. Apply TR-46.14: the two declarations, the byte-by-byte checks and words, the returns, the argv lines in `_dash_serve`, the Limits line in `_dash_build`. Values are tested by length and digits, never by a regular expression or an expression, and echoed only through `_dash_say`.
  ]]></action>
  <verify><![CDATA[`test_serve_options.cscript` through the driver prints MS-01..MS-08 PASS and its summary line; `test_serve_launch.cscript` through the driver prints no new FAIL.]]></verify>
  <done>dash serve took maxsessions() and idletimeout() with the same byte-level checks as port() and timeout(), and dash build, server listed the new flags.</done>
</task>

<task type="auto" id="46-09">
  <name>Document the limits and map them</name>
  <files>dash.sthlp, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-46.17 (find each place by its text in Subcommands, Server Mode and Resource limits; edit no other paragraph, R3; lines at most 79 characters; no tool or vendor name) and TR-46.16 (entries under S46's anchors, alphabetically; `app:` entries for template-only functions as `test_function_test_map.py` requires). Re-run the help-claim tests; no pin at c96facd counts these paragraphs' lines, so a failure there stops the task and is reported, never patched outside this task's files.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py test/test_help_conformance.py test/test_help_claims_4.py -q -n 6 -p no:cacheprovider` reports 0 failed; `awk 'length > 79' "$WT/dash.sthlp" | grep -ci "maxsessions\|idletimeout"` prints 0.]]></verify>
  <done>The help documented the cap, the idle close, the bokeh serve behaviour, the memory bound and the warm-up, and every new function was mapped to its test.</done>
</task>

<task type="auto" id="46-10">
  <name>Measure memory and the warm-up</name>
  <files>none</files>
  <action><![CDATA[
    Run `python3 -m pytest test/test_served_resources.py -q -n0 -p no:cacheprovider -k "TestPerSessionMemory" -s > "$S/46-rss.log" 2>&1` and record the measured mean growth. Build a served app for lowess at 100k rows (`test_estimator_cost.py`'s generator), run it as `python app.py --port <free>` with a 120 s limit, and record the time from start to the `preparing` line, to `/health` answering, and the second session's open time in `$S/46-measure.txt` (batch 16.2 extra; A116, IR-10). If S41 left a bokeh 3.10 scratch venv (E12), run `TestBokehLifetimesAreSet` and `TestSessionsAreCapped` once under it and record the result.
  ]]></action>
  <verify><![CDATA[`grep -c "passed" "$S/46-rss.log"` prints 1 and the recorded growth is at most 80 MB; `$S/46-measure.txt` holds the three times.]]></verify>
  <done>Per-session growth at 200k by 3 and the warm-up timings were measured and recorded for the commit body.</done>
</task>

<task type="auto" id="46-11">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.31a"]`. Close that BUGS.md entry in place (`- [x]`, the Resolution of Notes with 46-10's numbers). Delete the `"P1.31a"` key line of `WP30_OPEN`. Replace both `<!-- WP-30 P1.31a -->` markers in place with Notes' two lines (New; Security). Run `test_tracking_documents.py`, `test_served_resources.py`, `test_cscript_hygiene.py` and E6's files with `-n 6`, and `test_serve_options.cscript` through the driver. `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"<scratch>/full_suite_queue.sh" "$WT" "$S/46-full.log"` in the background, read when `exit=` appears. Stage exactly the files 46-01 to 46-11 changed; check `git -C "$WT" diff --cached --name-only` (G6). Write `$S/46-message.txt` in Notes' form, check G7, confirm the branch, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/46-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.31a -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.31a": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.31a)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.31a was closed naming existing tests, its markers named the new options and the threat closed, and one green commit on wp30-s46 was ready for the merger.</done>
</task>

## Section completion criteria

- The served app decodes its data once per process and shares it read-only; at most N sessions run, with a 503 busy page after the key check; idle sessions close with a reload message; Bokeh's lifetimes are explicit; the app warms up after printing its preparing line (AC-46.1..AC-46.4).
- Per-session growth is at most 80 MB at 200k × 3 and the memo is bounded, inert in Stata and in trials (AC-46.5).
- `dash serve maxsessions() idletimeout()` and the launcher flags work and refuse what they must (AC-46.6); saved pages are unchanged (AC-46.7).
- Every new name travels to the app and is mapped; one green commit `(WP-30 P1.31a)` on `wp30-s46` closes the entry, deletes its key and replaces both markers.

## Notes

- **Flag names.** `--idle-timeout` (minutes, 0 never) follows the app's existing `--timeout`; the research's `--session-idle-minutes` is not used. `--max-sessions` reuses the 1..1,000,000 range of the rate-limit flags.
- **What "set from dash serve maxsessions() and dash build, server" means here.** `dash serve` passes the flags; `dash build, server` lists them in its Limits line (research §4a.7); the built app's defaults are 20 and 60, overridable by `DASH_MAX_SESSIONS`/`DASH_IDLE_TIMEOUT` (register P1.31.3). No new `dash build` option is added.
- **The busy page has two forms.** `python app.py` and `dash serve`: HTTP 503 from `_dash_cap_auth` (A119). `bokeh serve`: dash has no HTTP hook there, so the same constant text is the page's only content, with HTTP 200; the help says so.
- **Measured numbers the commit quotes:** research m2 (rss 357 → 2016 MB over 24 sessions), m1 (0.39 s decode, 60.7 MB retained), m3 (the connected session never discarded) and 46-10's values.
- **python_exec hazard.** The cscripts need Stata's Python; check `~/.stata19/console/stata19.rc` after each slot run; a SKIP is not a pass.
- **Merge rules.** R1: MS-01..MS-08 in `test_serve_options.cscript`; one comment line in S46's stub. R2: S46's anchors (constants after `"_DASH_EVENT_RATE", "_DASH_EVENT_BURST",`; functions after `"_dash_limits", "_dash_limit_hint",`; the memo last in `_shared_stat_lines`). R3: Subcommands, Server Mode, Resource limits. R4/R5: the two `P1.31a` markers, the entry and its key. R6: no new program; the edited ones already declare `version 19` (S03). R10: none expected. R12: S46 is batch 16's only `_generate_app_source` editor.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `ServerAppBuilder._generate_app_source`, `_dash_launch_app`, the TR-46.2-TR-46.8 functions, the two copy-list builders and test symbols.
- **Commit message.** Subject as in "Commit boundary". Body: `$S/46-P1.31a-failure.txt`; the measured defect (Overview's block); the threat closed (memory exhaustion of the served app by open sessions, and a session reaching another's data through shared state, prevented by read-only sharing); what changed (TR-46.1-TR-46.17); 46-10's measurements; then `Regression: test/test_served_resources.py::<Class>::<test> -- failed at <base sha> with <text>` per failing node, `Guard: test/test_served_resources.py::TestPerSessionMemory::test_growth_at_most_80_mb -- passed at <base sha> with <n> MB` (bound 80 MB, ratified 06oct2026), and `test/test_serve_options.cscript MS-01`; `BUGS.md: "<WP30_OPEN["P1.31a"] title>" (closed)`. No fixture line (no Stata truth). No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.31a). The served app decodes its data once per process and shares it read-only (_dash_shared_payload, one entry, never in Stata's process or a trial), caps open sessions (default 20; --max-sessions, dash serve maxsessions(), DASH_MAX_SESSIONS) with a static HTTP 503 and Retry-After: 30 after the key check (_dash_cap_auth; in-page under bokeh serve), closes sessions idle for idletimeout() minutes (default 60, 0 never; filter, brush and CSV count as activity) with a reload message, sets Bokeh's unused-session lifetimes (15 s, checked every 5 s), memoises lowess, fpfit and lpoly within 64 MB under one lock (shared with section 57's worker), and warms up after printing "preparing the dashboard (N rows, ...)"; per-session growth at 200k rows by 3 layers measured <n> MB against an 80 MB bound (60.7 MB retained before). Pinned by test/test_served_resources.py::TestSessionsAreCapped::test_the_fourth_page_is_busy, test/test_served_resources.py::TestIdleSessionsAreClosed::test_closed_after_the_lifetime, test/test_served_resources.py::TestTheDataIsDecodedOncePerProcess::test_five_documents_decode_once, test/test_served_resources.py::TestPerSessionMemory::test_growth_at_most_80_mb, test/test_serve_options.cscript MS-01. Residual, deferred (WP-30): recomputes still run on the event loop (P1.31b, section 57); opening a session runs on the loop (P2.57); the per-session .tolist(), index lists and move snapshot stay (P2.41).
  ```
- **CHANGELOG lines** (each replaces its marker in place):

  ```
  ### New
  - `dash serve` takes `maxsessions(#)` (default 20) and `idletimeout(#)` minutes (default 60, 0 = never), and a served app takes `--max-sessions` and `--idle-timeout` (or `DASH_MAX_SESSIONS` and `DASH_IDLE_TIMEOUT` under `bokeh serve`); the app prints "preparing the dashboard (N rows, ...)" and builds once before it listens, so no reader pays the first build. (WP-30, P1.31a)

  ### Security
  - A served dashboard can no longer be exhausted by open sessions: it served every session (25 held sessions took 2 GB at 200k rows), and now admits at most `maxsessions()` at once, answering others with a static HTTP 503 after the key check, closes idle sessions, and decodes its data once and shares it read-only; each session's memory stays within 80 MB at 200k rows by 3 layers. (WP-30, P1.31a)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md F3** (F3a, F3b, F3c) and **I4** (I4-a, I4-b, "same gap as F3"): closed by `<sha>`; F3d stays with S57. **G14** (G14-d): closed by `<sha>`.
  - **ROADMAP:** P2.41 keeps `.tolist()`, the index lists and the per-session `_orig_src_data` snapshot (register P1.31.7); P2.57 records the session open on the loop.
  - **AGENTS.md invariant:** "served sessions share the decoded payload read-only through `_dash_shared_payload`; a session takes a slot only through `_dash_session_open` and releases it once; nothing in the generated app writes a shared array."
  - **Unverified:** Windows and Linux behaviour of the lifetimes and the 503 path (M4, P1.34); bokeh 3.10 unless 46-10 found S41's venv.
