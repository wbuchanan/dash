# Section 57: Served recompute off the event loop (P1.31 part b)

> Part of: WP-30 · Items: P1.31 part b (entry `P1.31b`; GAPS2-F3d, GAPS2-C-intro-served-cost; the lpolyci half closed by WP-29 P0.9) · Risk: red · Batch: 20 (alone; merge order [57]) · Depends on: 27, 35, 44, 45, 46, 47, 50, 52, 55 · Blocks: none (58 closeout only) · Tasks: 9, 1 commit (`(WP-30 P1.31b)`) · Case prefix: WK

## Review amendments

- Resolved Q-57.1 by the orchestrator's ruling. S46 now holds `state.memo_lock` around every memo get and put (TR-46.3, TR-46.8, checked in this pass), with the estimator outside the lock. S57 relies on it and edits nothing outside `_generate_app_source`. The stop-and-ask in 57-04, the conditional landing and AC lines, and the "must be under a lock" audit row are gone. 57-01 stops if the lock is missing at the base.
- Fixed (major, thread safety): the compute step read the module global `_DASH_SCHEME` on the worker. S34's `_dash_under_graph_scheme` rebinds that global on the loop during another session's build, so the worker could draw with that session's graph scheme. The plan now captures the scheme on the loop. The mapper copy gets fresh `z_options`, `z_context` and `colorvar_domain`, because a shallow copy shares those dicts with the global mapper. New tripwire `test_the_scheme_is_the_plans`, and the mapper tripwire now compares the dict contents.
- Fixed (major, BR-57.6): the cue Div was added whenever filters existed. That would change every in-process document, including the parity corpus. It is now added only when `_dash_worker_wanted(doc)`.
- Fixed (major, Bokeh): TR-57.8 said the worker calls no Bokeh function but constructors, which is false: the redraw adds glyphs to a throwaway figure. The pinned rule is now that the worker creates or writes only models whose `document is None`. The three bokeh interpreters (3.8, 3.9, and 3.10 if verified) are named in TR-57.8 and 57-06.
- Fixed (major): S46's API was misnamed. The holder is `_DASH_STATE` (a SimpleNamespace, so `.recompute`, `.warn_lock` and `.cap`, not dict keys). The idle close is the periodic callback in `make_document`, so the forget call goes before its `doc.clear()`, which is template text.
- Fixed (major, correctness): "latest per session wins" is exact only because the base's move recomputes every target whatever widget triggered it (:35838-35846). 57-01 re-checks this. If it fails, the queue keys by (slot, widget). New test `test_two_widgets_with_exclude`.
- Fixed (minor): the lock order is stated (document lock, `warn_lock`, `memo_lock`, never nested). There is a guard against function-local `import warnings`. The audit rule is defined for idempotent GIL-atomic caches, with rows for SchemeParser and S34 caches, pandas `_item_cache` and the label dicts. A brush made while a move waits is pinned and listed as a residual, and the loop-side re-finish is also a residual. `_dash_copy_redraw_geometry` is marked as deleted by S14. S55 is described as editing no move-path line. The truth block uses `_w30_expect`/`_w30_done`, helpers above the header, and checks `ALL CHECKS PASSED` with no SKIP. 57-05's "except" is now `-k`. The health test's n is checked against the base.
- Checked at `c96facd`: template `_make_filter_cb` 35828, `_on_filter_change` 35854, `_masks` 35837, `_DASH_SCHEME`/`_DASH_MAPPER` 33478-33479 (referenced only in template text), `make_document` 34712, the filter callback call 36077, the CSV list 36225, help :1773-1780, `TestOneRecomputationAtATime` :1623, and E6's ten `catch_warnings` sites (all on the module-level `warnings`). Bokeh 3.8.0: `_wrap_document_callback`/`with_document_locked`, the `_document_patched` RuntimeError (session.py:240-244), and `Document.add_next_tick_callback` → `IOLoop.add_callback` (tornado.py:224-247).
- Rejected: Bokeh's documented `doc.add_next_tick_callback` from the worker thread. The hop through `IOLoop.add_callback` keeps every Bokeh call on the loop (Notes).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:165 (P1.31): "One event loop is blocked by recomputes: lowess takes 27.7 s and lpolyci 8.7 s at N=100k." GAPS2 F3 (GAPS2.md:1325-1331) asks that "/health answers within 1 s during a 200k recompute", and the C intro (GAPS2.md:711) says the lowess and lpolyci recomputes "block a served page at large N". The help states the design outright (dash.sthlp:1779-1780): "the server -- one process, one event loop -- runs one recomputation at a time for every session together."

Measured at `c96facd` (research `.ultraplan/wp30/research/p1-31.md` §2d and "Critic additions"; Stata's Python 3.13.9, bokeh 3.8.0, tornado 6.5.1, load average 10-23):

```
m1_cost.py   lowess , 100k rows: make_document #1 28.38s ; filter move to 0.0: recompute 8.72s
             lpolyci, 100k rows: make_document #1 1.31s  ; filter move to 0.0: recompute 0.92s
m5_move_health.py (in-process server, lowess 100k): /health took 8.11s at 8.1s after the move
k1.py        lowess 20k, dropdown move: estimator threads=['MainThread'], the assignment returned after the 0.43s recompute
m8_thread.py lowess 50k in a worker thread: loop ticked 1080 times, worst delay 78 ms, median 1.5 ms
             (on the loop thread the same fit blocked it 7.4 s; in the thread it took 13.1 s at load 13)
```

lpolyci is FIXED (WP-29 P0.9, `e32be3a`, analytic band). lowess is not: one reader's move stops `/health`, every other session's moves, brushes, CSV downloads and session opens for the whole fit. Stata itself takes 11.83 s for the same half-sample lowess (`t1_cost.do`), so the fit's cost is not the gap; the shared loop is.

**After this section**, in a served session (`python app.py`, `dash serve`, `bokeh serve`):
- a filter move reads the widgets and builds its row masks on the loop, runs every layer redraw and KPI statistic on one process-wide worker thread, and writes the results into the document in one next-tick callback under the document lock;
- a newer move of the same session replaces its waiting one, sessions are served first come first served, and a result overtaken by a newer move, an idle close or a closed session is dropped;
- while a recompute is waiting or running, the session shows "Updating..." and keeps its previous drawing;
- `/health`, other sessions' opens and their brushes keep answering (`/health` within 1 s during a 100k lowess move and a 200k recompute);
- the worker shares no mutable state with the loop: the mapper and scheme it draws with are its own, captured on the loop when the move is planned, KPI text is formatted on the loop, dash's `catch_warnings` blocks are serialised, and a test fails when a new global reaches the worker path unaudited;
- an in-process document (tests, the warm-up, S23's trial) recomputes synchronously, exactly as today, so the saved page and every existing served test keep their meaning.

**Why one section.** Sub-claim d of P1.31 is one mechanism in one function (`ServerAppBuilder._generate_app_source`'s move path). It is red and runs alone, last of all fix sections, because S21, S27, S35, S44, S45, S47, S50, S52 and S55 all edited that path; S46 (part a) supplied the process holder, the session cap that bounds the queue, the idle close and the memo.

**Test order and commit rule (rule 7).** One cycle on `wp30-s57`: 57-01 writes every regression test and runs it against the unmodified batch-20 base, saving `$S/57-P1.31b-failure.txt` (no commit); 57-02 adds the truth block (guards); 57-03 to 57-08 fix, audit, measure and document; 57-09 closes the entry, deletes its key, replaces its marker, runs the full suite through the queue and makes the one commit. No test-only commit exists, and no commit is red.

## Risk: [red] — concurrency inside a HIGH-risk code generator whose module state was written for one thread

**Why.**
- `ServerAppBuilder._generate_app_source` is HIGH (research §6: 5 impacted, 3 processes). Every template function (`make_document`, `_dash_draw_layer`, `_dash_redraw_for`, `_make_filter_cb`) is a string inside it and UNKNOWN to the index; they are reached only through generated apps.
- The move path was edited by nine sections after the research was measured; its text at the batch-20 base is not the text quoted here.
- The app keeps per-render state in module globals that the redraw reads or writes: `_DASH_MAPPER` (`colorvar_domain` set and reset per layer, `z_options`, `z_context`, `scheme`), `_DASH_SCHEME` (rebound by S34's `_dash_under_graph_scheme`), `_STORAGE_TYPES` (cleared and refilled by every `make_document`), `_DASH_NOTED`, and `warnings.filters` through ten `catch_warnings` sites.
- A model written outside the document lock raises in Bokeh (`ServerSession._document_patched`, bokeh/server/session.py:240-244: "_pending_writes should be non-None when we have a document lock"), and a data race between a session's build and another's redraw draws one session's scheme, colour domain or storage type into the other's figure.

**Risk factors.**
1. Under `bokeh serve` the app module runs afresh for every session, so a module-level executor would be one worker per session.
2. `ThreadPoolExecutor`'s work queue is unbounded (rule 1).
3. `add_next_tick_callback` does nothing for a document with no server session (bokeh/document/document.py:272-275), so the in-process documents the suite builds would never be redrawn.
4. `warnings.catch_warnings` swaps process-global state; two overlapping blocks can leave an `ignore` filter installed for good, silencing every later note (S06/S23's channel).
5. A recompute can outlive its session (idle close, a closed tab) and its result would be written into a cleared or destroyed document.
6. Windows and Linux threading are unmeasured (M4).

**Mitigation.**
1. The worker lives in S46's process holder, `_DASH_STATE = _dash_served_state()` (TR-46.3: the `types.SimpleNamespace` kept as `sys.modules["_dash_served_state"]`), as its attribute `recompute`. That gives one thread per process under every launch path; `--num-procs N` gives N (documented).
2. A bounded queue of one pending job per session slot. Its ceiling is S46's resolved session cap, `_DASH_STATE.cap`, read when the worker is first created, after `__main__` has applied `--max-sessions`. Past the ceiling the move runs synchronously, as today: never dropped, never queued without bound.
3. `_dash_worker_wanted(doc)` sends only documents with a server session to the worker; every other document runs plan, compute and apply inline.
4. `_DashWarnings`, a proxy bound to the app's own name `warnings`, serialises dash's `catch_warnings` blocks with one lock (each block is a vectorised step, never an estimator: E6); a test pins the hold time.
5. A per-session generation counter, bumped by every new move, by S46's idle close and by `on_session_destroyed`; the apply step drops any result whose generation is not the latest, and the worker skips a job already stale.
6. Portable stdlib only (`threading`, `collections`, `copy`); the worker's only cross-thread call is Tornado's `IOLoop.add_callback`, documented as the one IOLoop method safe from another thread (the app already relies on it: `_dash_watch_parent`, dash_render.py:36812).

## Dependencies

- **Depends on (manifest):** S27, S35, S44, S45, S47, S50, S52, S55 (their move-path edits: `_dash_finish_auto_bases`, `_dash_layer_in_axis_units` and the `_fmt_cache` transforms, the date ticker, recast's dispatch, the inner box, reference-line extent, `add`, and S55's turned-layer tooltips (S55 edits only `_dash_build_hover`, no move-path line, IR-13), all landed and re-read at the base), S46 (the process holder `_DASH_STATE` with `cap`, `memo` and `memo_lock`; `--max-sessions`; the idle close, which is a periodic callback written inside `make_document` (TR-46.9); `on_session_destroyed` use; the decode cache; and the estimator memo, whose every get and put already runs under `state.memo_lock` with the estimator itself outside the lock (TR-46.8, the orchestrator's Q-57.1 ruling, so S57 adds no memo lock); in-process documents exempt).
- **Landed earlier and read here:** S04 (served CSP: the cue carries no script or inline style), S21 (`_dash_refinish_axes`, run in the apply step), S23 (served note hook; the worker's notes reach it), S34 (`_dash_under_graph_scheme`; its Notes ask S57 to serialise its swap), S41 (the verified bokeh window and its scratch venvs), S01 (entry `P1.31b`, key, marker `<!-- WP-30 P1.31b -->` under `### Fixed in WP-30`, the stub `* ==== S57 P1.31b: Served recompute off the event loop ====`, map anchor `# WP-30 S57 (P1.31b): Served recompute off the event loop (P1.31 part b)`).
- **Blocks:** none; S58 records the closure.
- **Parallel batch:** 20, alone (A139).

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines, dash.sthlp 3,822). Batches 7-19 move every template line; the executor re-finds each by its text at `batch-20-base` and treats the numbers as approximate.

### E1. The move recomputes inline in the filter callback (template, `_make_filter_cb`)

`_make_filter_cb` (35828) returns `_on_filter_change` (35854). Step 2 refreshes raw sources (`_dash_refresh_unlinked`, 35946; `_dash_refresh_linked`, 35973), step 3 redraws every aggregated layer through its mapper and copies the result onto the live source, step 4 recomputes and formats KPI cards:

```python
36020                _fresh = agg['redraw'](agg_fdf)
36021                for _live, _new in zip(agg['sources'], _fresh):
36030                    _live.data = _dash_keep_jitter(
36031                        dict(_new.data), _orig_src_data.get(id(_live), {}))
36042                    _dash_copy_redraw_geometry(_live, _new)
36065                val = _compute_kpi(_k_fdf, kpi.get('stat', 'mean'), kpi.get('var', ''), _date_vars)
36066                disp = _format_kpi(val, kpi.get('fmt', ''),
36073                _kpi_divs[kname].text = _dash_kpi_card(ktitle, disp, ksub, kcolor, kbg, kname)
```

S14's D-14b deletes `_dash_copy_redraw_geometry` and its emitted call (:36042) in batch 5. A no-op call remains only under its maintainer fallback, and the apply then keeps it in place.

`agg['redraw']` is `_dash_redraw_for(...)`'s `_redraw` (35039-35093): `_dash_layer_frame`, then a throwaway `bokeh_figure()`, `_dash_mark_date_axes`, `_dash_draw_layer(_tfig, ...)`, returning the drawn sources. S34 wraps it (`return lambda frame: _dash_under_graph_scheme(g, _redraw, frame)`).

### E2. The throttle calls the callback on the loop (`_dash_event_throttle`, 24330; not edited)

```python
24384    def _on_change(attr, old, new):
24392            fn(attr, old, new)                 # a token: at once, inline
24394        doc.add_timeout_callback(              # none: one trailing call, under the session lock
```

Its three call sites: filters (template 36098), brushes (36186), CSV (36218). Brushes only recount KPI cards (36101-36155) and CSV builds one payload; neither redraws a layer, so both stay on the loop (Boundaries).

### E3. Module state the redraw path shares (template)

- `_DASH_SCHEME = _dash_build_scheme()` and `_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)` (33478-33479), one per app module. `make_document` sets `_dash_attach_labels(_DASH_MAPPER, ...)`, `default_level`, `dataset` (34794-34806; equal values for every session of one app). `_dash_draw_layer` (34922) sets `_DASH_MAPPER.colorvar_domain` per layer (34945, reset at 35006) and calls `_DASH_MAPPER.map_*`; `_dash_figure_for` (35095) sets `z_options`/`z_context` (35111-35113, reset 35410-35411).
- `_STORAGE_TYPES.clear(); _STORAGE_TYPES.update(_storage_types)` in every `make_document` (34786-34787), read by `_format_kpi` (34703).
- `_DASH_NOTED` (dash_render.py:15350), cleared by `_dash_reset_notes()` at the top of every `make_document` (34727).
- `_graph_qualifiers` is `make_document`-local (35660), not a module global (the research's §4.4 item is withdrawn).
- `curdoc()` appears only at template 36413 (`make_document(curdoc())`), never on the move path (critic 14).

### E4. GlyphMapper, OptionTranslator and SchemeParser instance writes

An awk scan of `self.<attr> =`/`.add(`/`.update(` inside each class at `c96facd`: GlyphMapper (7879-) writes only `colorvar_domain`, `dataset`, `scheme`, `tr` (constructor and setters); OptionTranslator (5098-5645) none; SchemeParser (5646-7878) `name`, `_props`, `ci_band_styles`, `p_other_band_styles`, `_plot_lwidth_memo`: lazily filled caches with idempotent values. External writers are the template lines of E3 and `_dash_attach_labels` (25736-25746: `variable_labels`, `value_labels`, `value_label_names`, `date_vars`, `numeric_formats`, `storage_types`, `formats`).

### E5. Bokeh's thread rules, verified at bokeh 3.8.0 (Stata's Python)

- `Document.add_next_tick_callback` (bokeh/document/document.py:262-280) → `DocumentCallbackManager.add_session_callback` (document/callbacks.py:152-193: raises `RuntimeError("Attempting to add session callback to already-destroyed Document")`, adds to a set, emits `SessionCallbackAdded`) → `ServerSession._session_callback_added` (server/session.py:259-261, not under `_needs_document_lock`) → `_CallbackGroup.add_next_tick_callback` → `IOLoop.add_callback` (util/tornado.py:224-247).
- Session callbacks run through `ServerSession._wrap_document_callback` → `with_document_locked` (session.py:228-233) unless marked `nolock`.
- `make_id` takes `_simple_id_lock` (util/serialization.py:248-265, 390-391), so models built on the worker get unique ids.
- `curdoc()` in `bokeh/plotting/__init__.py` is an export only; no model constructor calls it.
- The F3 plan's `without_document_lock` is not used: the loop-side steps are short and must hold the lock.

### E6. dash's `catch_warnings` sites (dash_render.py; each wraps a vectorised step)

`_dash_units_to_axis` 592, `_dash_axis_positions` 872, `_dash_stale_kind` 1122, `_dash_by_panel_dropped` 3526, `SchemeParser.can_resolve` 6062, `_dash_csv_payload` 17362, `_dash_fmt` 21085, `_dash_axis_count_ticks` 22585, `_dash_embed_rows_of` 28099, `ServerAppBuilder._plan_by_groups` 33888 (build time). None wraps an estimator.

### E7. Tests that pin today's behaviour

- `test/test_help_claims_4.py::TestOneRecomputationAtATime` (:1623): docstring "one process with one event loop, so the recomputations of every session run one at a time"; its assertion (`num_procs == 1`, loopback) stays true. Docstring changed in place (`Changed:` line).
- `dash.sthlp:1773-1780` ("Recomputation."), the only text claim; no cscript pins it (`grep -rn "one event loop" test/` → test_help_claims_4.py:1624 only).
- No test moves a widget over a live `pull_session` (`grep -ln pull_session test/*.py` → six files, none sets a widget value), so no live test assumes a synchronous apply. 57-01 re-greps at the base.
- Guards that must stay green: `test_served_throttle.py`, `test_mode_parity.py`, `test_served_filter_move.py`, `test_served_linked_views.py`, `test_server_brush.py`, `test_help_claims_1..8.py` move cases, `test_estimator_cost.py`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` (:1194), S46's `test_served_resources.py`.

### E8. Blast radius

`gitnexus impact _generate_app_source -d upstream -r dash`: HIGH (research §6). `_dash_event_throttle`, `_dash_limits`, `_glyph_layer_lines`: not edited. Template functions: UNKNOWN (strings); covered by `app:` map entries and generated-app tests. S46's estimator memo is not edited: it is already locked (TR-46.8).

## User stories

- **US-57.1** As a dashboard reader, I want another reader's slow refit not to freeze my dashboard, so that my own moves, brushes and downloads keep answering.
- **US-57.2** As a dashboard reader, I want to see that my move is being recomputed, so that a slow lowess does not look like a dead page.
- **US-57.3** As a dashboard publisher, I want `/health` and new sessions to answer while a recompute runs, so that the launcher and monitors do not read a busy server as a failed one.
- **US-57.4** As a dashboard publisher, I want the worst wait documented, so that I can set `maxsessions()` for my data size.
- **US-57.5** As a maintainer, I want every global the worker reaches to be audited by a test, so that a later change cannot reintroduce a race silently.

## Business requirements

- **BR-57.1** During one session's filter-move recompute, `/health` answers within 1.0 s, other sessions open, and their brushes and moves are accepted (US-57.1, US-57.3).
- **BR-57.2** After any sequence of moves, a served session draws exactly what the synchronous path draws for its latest widget values: the same source data, glyph geometry, axes and KPI text (US-57.1).
- **BR-57.3** A session's newer move replaces its waiting move; sessions are served in the order they asked; a result overtaken by a newer move, an idle close or a closed session is never drawn (US-57.1).
- **BR-57.4** While a session's move waits or runs, the page shows "Updating..." and keeps its previous drawing; the cue clears when the latest result is drawn or the recompute fails (US-57.2).
- **BR-57.5** At most one recompute runs per server process, and at most one waits per open session; the help states the worst wait (about the session cap times one recomputation: about 3 minutes at 20 sessions for lowess at 100,000 observations) (US-57.4).
- **BR-57.6** The saved page, documents built in process, Stata's process and the warm-up behave exactly as before (no worker, no cue).
- **BR-57.7** No session's figures, KPI text or notes are drawn from another session's state, and dash's notes are never silenced by a recompute (US-57.5).

## Technical requirements

All edits are in `ServerAppBuilder._generate_app_source`'s template text unless named; no copy-list change (R2 row S57).

- **TR-57.1 The worker block** (new template block `# ---- The recompute worker (WP-30 P1.31b) ----`, directly above `def make_document(doc):`, 34712 at `c96facd`):
  - `class _DashRecomputeWorker`: `__init__(self, ceiling)` holds `threading.Condition()`, an `collections.OrderedDict` `_pending` (slot → job), `_thread=None`, `ceiling=int(ceiling)`; `submit(slot, job)` under the condition: a slot already waiting has its job replaced in place (latest per session wins, its FIFO place kept); a new slot past `ceiling` returns False; otherwise appends, starts the thread lazily (`threading.Thread(target=self._run, name='dash-recompute', daemon=True)`) if none is alive, notifies, returns True; `forget(slot)` removes a waiting job; `_run()` waits on the condition, pops the oldest (`popitem(last=False)`), releases the condition, runs `job()` and catches `Exception` only (the job reports its own error, TR-57.4). The condition is never held while a job runs.
  - `_dash_recompute_worker()` returns the one instance kept as `_DASH_STATE.recompute`. It is created on first use with `ceiling=_DASH_STATE.cap` and is called only on the loop thread, so the lazy creation cannot race. Under `bokeh serve` every module execution shares it; a job is a closure of the module that planned it, so it reads that module's `_DASH_CTX`.
  - `_dash_worker_wanted(doc)`: True only when `getattr(doc, 'session_context', None) is not None`, the trial flag S23/S46 use (`_DASH_TRIAL` per register P1.31.8) is unset, and `getattr(sys, '_is_gil_enabled', lambda: True)()` is true (a free-threaded interpreter falls back to inline: the audit's verdicts assume the GIL's atomic dict and set operations).
  - `class _DashSlot` (`__slots__ = ('gen', 'cue', 'alive')`): one per session, made in `make_document` after the key gate, the limiter and S46's cap. `gen` and `alive` are written only on the loop thread (the plan, `_dash_worker_forget`, S46's idle callback); the worker only reads `gen` to skip a stale job early, which is a benign read of an int, because the apply check on the loop decides.
  - **One slot per session, trigger-independent.** At `c96facd` every move recomputes every target with its own mask, "whichever widget triggered it" (template :35838-35846); `_trig_widget` is not read inside `_on_filter_change`. So a session's newer plan, which reads every widget's current value, supersedes its waiting one, and "latest per session wins" is exact. 57-01 re-checks this at the base. If a statement of `_on_filter_change` reads `_trig_widget`, or a write set differs by widget, the queue key becomes `(slot, id(_trig_widget))`, so that a waiting move of another widget is never replaced.
- **TR-57.2 Worker-private mapper and scheme** (E3, E4; S34's Notes):
  - `_DASH_CTX = threading.local()`; `_dash_cur_mapper()` returns `_DASH_CTX.mapper` when set, else `_DASH_MAPPER`; `_dash_cur_scheme()` likewise for `_DASH_SCHEME`. Both compare with `is None`, never truthiness.
  - In `_dash_draw_layer`, bind `_m = _dash_cur_mapper()` once at its top and replace every `_DASH_MAPPER` there with `_m` (the `colorvar_domain` set and reset, the `map_*` calls, the mapper passed to the pc/range/else helpers); every `_DASH_SCHEME` read on the redraw path (`_dash_redraw_for`, `_dash_draw_layer`, and what S27/S35/S44/S47/S50/S52/S55 added there) becomes `_dash_cur_scheme()`.
  - `_dash_under_graph_scheme` (S34): when `_DASH_CTX.mapper` is set, it swaps `_DASH_CTX.scheme` and `_DASH_CTX.mapper.scheme` (restored in `finally`) and never rebinds the module global; on the loop thread its code path is unchanged.
  - The plan step (TR-57.3) runs on the loop thread, inside a widget handler, where no `make_document` is part-way through (the loop runs one handler at a time, and S34's swap is restored before a build returns). There it captures `plan.scheme = _DASH_SCHEME` and `plan.mapper = copy.copy(_DASH_MAPPER)`, then gives the copy fresh mutable state: `plan.mapper.z_options = {}`, `plan.mapper.z_context = None`, `plan.mapper.colorvar_domain = None`, `plan.mapper.scheme = plan.scheme`. A shallow copy would otherwise share these dicts with the global mapper. `_dash_attach_labels` (25724) rebinds the label dicts on the global mapper rather than mutating them, so the copy keeps the build's dicts unchanged.
  - The compute step sets `_DASH_CTX.mapper = plan.mapper` and `_DASH_CTX.scheme = plan.scheme` and clears both in `finally`. It never reads the module global `_DASH_SCHEME` on the worker thread. Reading it there would race with S34's `_dash_under_graph_scheme`, which rebinds that global on the loop for the length of another session's build, and the worker would draw with that session's graph scheme.
- **TR-57.3 The move path split** (inside `_make_filter_cb`): `_on_filter_change(attr, old, new)` keeps its name and becomes: `_plan = _dash_move_plan()`; if `_dash_worker_wanted(doc)` (with `doc` passed into `_make_filter_cb` by a new keyword, `_doc=None`, at its call at 36077) submit, else `_dash_move_apply(_plan, _dash_move_compute(_plan))` inline.
  - `_dash_move_plan()` (loop): every statement of the base's `_on_filter_change` that reads a widget or a mask: a fresh mask cache per plan (replacing the shared `_masks` dict, so a waiting plan is never altered by a later one), each target's boolean mask as a numpy array, the step-3 `agg_fdf` row selections and the step-4 KPI row selections as boolean masks over `_df_ref` (masks, not frames, so a waiting plan holds kilobytes), the mapper copy and scheme of TR-57.2, the slot's new generation (`slot.gen += 1`) and `IOLoop.current()`. Shows the cue when the worker path is taken.
  - `_dash_move_compute(plan)` (worker, or inline): for each aggregated key, `agg['redraw'](_df_ref[mask])` under the plan's mapper context; for each KPI, `_compute_kpi(...)` only. Returns `{'fresh': {key: [sources]}, 'kpi': {kname: float}}`. It builds and writes only models that belong to no document: the throwaway figure `_dash_redraw_for` makes, with its sources and glyphs. It writes no model attached to a document, and calls no `_format_kpi`, `curdoc` or document method.
  - `_dash_move_apply(plan, res)` (loop, under the document lock): returns at once unless `plan.gen == slot.gen and slot.alive`; then, in the base's order, step 2 and 2b (raw and linked refresh, selections cleared, `_brush_rows`), step 3's copy loop (`_dash_keep_jitter`, hover text, selection clear, the redrew-count warning, and `_dash_copy_redraw_geometry` only if S14's fallback kept it), S27's `_dash_finish_auto_bases` and S21's `_dash_refinish_axes` call sites in the same tick (S27 Notes), step 4's `_format_kpi` and `_dash_kpi_card` text, then hides the cue. Every statement of the base's `_on_filter_change` that writes a model lands here, unchanged in text except the plan's masks and the worker's results.
  - The submitted job: `def _job(): ...` skips at once when stale; otherwise runs `_dash_move_compute(plan)` and hands `(plan, res, None)` or `(plan, None, exc)` to `_dash_move_post`.
  - `_dash_move_post(loop, plan, res, exc)` (worker side): `loop.add_callback(_hop, ...)`, wrapped so a closed loop (`RuntimeError`) drops the result; the loop is `tornado.ioloop.IOLoop.current()` captured in `_dash_move_plan` on the loop thread. `_hop` (loop) calls `doc.add_next_tick_callback(functools.partial(_dash_move_apply_or_raise, plan, res, exc))`, catching the destroyed-document `RuntimeError` (E5). On `exc`, the next-tick callback hides the cue when the generation is latest, then re-raises `exc` so Bokeh logs it as it logs a callback's error today; the old drawing stays.
  - When `submit` returns False (ceiling), the move runs inline as today.
- **TR-57.4 The cue** (BR-57.4): only when `_dash_worker_wanted(doc)` and `filter_widgets` is non-empty, after the CSV block (after `filter_widgets = list(filter_widgets) + [_csv_btn]`, 36225), `slot.cue = Div(text='Updating...', name='dash_updating', visible=False)` and `filter_widgets = list(filter_widgets) + [slot.cue]` (a new list, as the CSV button is added, so the recompute callbacks keep the filters' own). Constant text, no style attribute, no script (S04's CSP; the same form as S46's busy page). Shown by the plan only on the worker path; hidden by the apply or the error path only when the generation is latest. An in-process document (the parity corpus, the warm-up, S23's trial) gets no cue Div, so its layout and `test_mode_parity.py` stay as they are (BR-57.6).
- **TR-57.5 Session teardown** (register P1.31.4: "An idle close bumps the generation"): `doc.on_session_destroyed(_dash_worker_forget)` registered in `make_document` when `_dash_worker_wanted(doc)`; `_dash_worker_forget(ctx=None)` sets `slot.alive = False`, bumps `slot.gen` and calls `_dash_recompute_worker().forget(slot)`. S46's idle close is template text: the periodic callback TR-46.9 writes inside `make_document`. It gains one statement, `_dash_worker_forget()`, directly before its `doc.clear()`, guarded by `_dash_worker_wanted(doc)`. Bokeh calls `on_session_destroyed` callbacks on the loop thread, and the periodic callback runs there under the document lock.
- **TR-57.6 Warnings** (E6): directly after the worker block, `class _DashLockedCatchWarnings(warnings.catch_warnings)` whose `__enter__` acquires the module `_DASH_WARN_LOCK = threading.RLock()` (kept in S46's holder so every module execution shares it) before `super().__enter__()` and whose `__exit__` releases it after `super().__exit__()`, recording the longest hold in `_DASH_WARN_LOCK_STATS['max_hold']`; `class _DashWarnings` delegates `__getattr__` and `__setattr__` to the real module except `catch_warnings`; then `warnings = _DashWarnings(warnings)` at app module level. Every copied helper resolves `warnings` in the app's globals, so dash's sites serialise without editing them or the stdlib; `warnings.showwarning = …` set through the proxy reaches the real module (S23's hook). The lock is kept as `_DASH_STATE.warn_lock`, created at module level if absent; module code runs on the loop thread or at import, so its creation cannot race.
  - **Lock order (no deadlock).** Three locks meet on the move path: Bokeh's document lock, which only the loop holds; `_DASH_STATE.warn_lock`; and S46's `memo_lock`. The worker never takes the document lock. No code takes `memo_lock` inside a `catch_warnings` block, because E6's blocks wrap vectorised steps and never an estimator, and the memo's `fn` runs outside `memo_lock`. No code enters a `catch_warnings` block while holding `memo_lock`. Each lock is therefore held alone, and the loop waits on `warn_lock` at most for one vectorised step (`test_hold_time`).
  - The proxy reaches only a module-level `warnings`. `TestTheWarningFilters::test_no_local_warnings_import` walks the generated app with `ast` and fails on any `import warnings` or `from warnings import` inside a function. Ten sites use the module name at `c96facd` (E6), and later sections may add more.
- **TR-57.7 The audit** (BR-57.7; index 20.2): the verdict table below is the module docstring of `test/test_served_worker.py` and the allowlist `_WORKER_AUDIT` of `TestTheWorkerTouchesOnlyAuditedNames`, which walks the generated app with `symtable`/`ast` (as `TestTheServedAppDefinesEveryNameItReads` does) from `_dash_move_compute` through every app function it can reach and collects every global and free variable named; any name not in `_WORKER_AUDIT` fails with its path. A name may be allowlisted when the worker only reads it after the build, when it is thread-private (`_DASH_CTX`, the plan), or when every cross-thread write is one GIL-atomic dict or set operation storing a value equal to any other thread's and no code iterates the container while the other thread can write it. Any other name written by both threads is fixed by TR-57.2 or TR-57.3, never allowlisted.

  | Name reached by the worker | Verdict |
  |---|---|
  | `_DASH_MAPPER`, `_DASH_SCHEME` | never: read through `_dash_cur_mapper()`/`_dash_cur_scheme()` (TR-57.2) |
  | `_STORAGE_TYPES`, `_format_kpi`, `_dash_kpi_card` | never: apply only |
  | `df`/`_df_ref`, `_qual_masks`, `_date_vars`, `_sort_keys`, spec dicts | read only after the build; S46's arrays are read-only |
  | `_DASH_NOTED` | GIL-atomic `in`/`add`/`clear`; at worst one note printed twice (accepted) |
  | `_fmt_cache` (S35's transforms) | GIL-atomic get/set; a model the worker adds is held only by throwaway figures until a loop write uses it (accepted; tripwire) |
  | S46's estimator memo (`_DASH_STATE.memo`) | every get and put under `_DASH_STATE.memo_lock` (S46 TR-46.8; Q-57.1 ruling); the estimator runs outside it |
  | `_DASH_STATE.recompute`, `.warn_lock`, `.cap` | created on the loop or at import; the worker reads none of them |
  | SchemeParser's lazy caches (`ci_band_styles`, `p_other_band_styles`, `_plot_lwidth_memo`) and S34's per-scheme served property dict | GIL-atomic get/set of idempotent values, never iterated (57-01 greps the base for iteration over them; one found is a fix, not an allowlist) |
  | pandas' per-frame `_item_cache` on `_df_ref` (pandas 2.3.3 in Stata's Python; gone under 3.0's copy-on-write) | filled by GIL-atomic setitem of equal column views by the worker and by the session's own loop handlers (accepted; `TestTheLoopAnswersDuringARecompute::test_other_sessions_answer` brushes during a recompute) |
  | the global mapper's label dicts | `_dash_attach_labels` rebinds them on the global mapper and never mutates them in place (25724-25746), so the plan's copy keeps the build's dicts |
  | `warnings` | `_DashWarnings` (TR-57.6) |
  | `curdoc`, live sources, KPI divs, views, `_brush_rows`, `_orig_src_data` | never (tripwire tests) |
  | Bokeh model constructors | `make_id` is locked (E5); throwaway figures never join a document |
- **TR-57.8 Bokeh across S41's window:** the thread-rule tests (`TestBokehThreadRules`) run under every bokeh minor S41 verified: 3.8 with `/opt/anaconda3/bin/python3` (Stata's Python), 3.9 with the suite's `python3`, and 3.10 with `$S/venv-s41-bk310/gatevenv/bin/python` only if `$S/41-ceiling.txt` reads 3.11. They pin three things. First, the apply runs on the loop thread with the server session's `_pending_writes is not None`, so the lock is held. Second, every Bokeh model the worker creates or sets an attribute on has `document is None`: it touches only the throwaway figure, its sources and glyphs, and `make_id` is locked (E5). Third, `IOLoop.add_callback` from the worker thread runs on the loop. `ServerSession._pending_writes` is read only by this test, as a probe of the lock, and nothing in dash_render.py depends on it.
- **TR-57.9 Help** (dash.sthlp:1773-1780, "Recomputation."; an R3 addition: Server Mode's owners in index.md do not list S57, and batch 20 has no other section, so nothing conflicts; reported in review-notes g09.md): replace "and the server -- one process, one event loop -- runs one recomputation at a time for every session together." with sentences saying: recomputations run on one worker thread per server process, one at a time and in the order sessions asked; the page shows "Updating..." and keeps its drawing meanwhile, and other sessions and /health keep answering; a newer move replaces a session's waiting one and an overtaken result is discarded; the worst wait is about the session limit times one recomputation (about 3 minutes with 20 sessions for lowess at 100,000 observations); opening a session still pauses the server while its page is built. Lines at most 79 characters; no tool or vendor name.
- **TR-57.10 Maps:** `test/function_test_map.py` under the S57 anchor, alphabetical: `app:_DashLockedCatchWarnings.__enter__`, `.__exit__`, `app:_DashRecomputeWorker.__init__`, `._run`, `.forget`, `.submit`, `app:_DashWarnings.__getattr__`, `.__setattr__`, `app:_dash_cur_mapper`, `app:_dash_cur_scheme`, `app:_dash_recompute_worker`, `app:_dash_worker_wanted`, `app:make_document.<locals>._dash_worker_forget`, `app:make_document.<locals>._make_filter_cb.<locals>._dash_move_apply`, `._dash_move_compute`, `._dash_move_plan`, `._dash_move_post`, `._job`, `._hop` (exact qualnames as `co_qualname` reports them; `_DashSlot` has no function). No `program_coverage_map.py` change.

## Boundaries

- Not edited: `_dash_event_throttle`, `_dash_limits`, `_glyph_layer_lines`/`_shared_stat_lines` copy lists, `DashRenderer` or any saved-page code, `_FILTER_JS`, dash.ado, dash_parse.mata, `_dash_launch_app`, `__main__`.
- Inside the template, S57 edits only: the new worker and warnings blocks, `make_document`'s slot/cue/teardown lines, `_make_filter_cb` and `_on_filter_change`, `_dash_draw_layer`'s and the redraw path's mapper/scheme reads, S34's `_dash_under_graph_scheme`, and one call in S46's idle close. A model write or estimator change elsewhere is not S57's.
- Brushes and CSV stay on the loop (E2: no layer redraw); session open stays on the loop (register P1.31.11; P2.57, filed by S58).
- No `without_document_lock`, no process pool (research §4: `dash serve` hands the app over as text, and fork is unavailable on Windows), no per-client cap (P1.31.6), no new flag or option (P1.31.9).

## Stata truth

None for the mechanism (twoway has no server or event loop; research §3). The S57 block of `test/test_wp30_truth.cscript` (R1) holds two guards, written by 57-02 between S01's S57 start and end lines:
- **WK-01:** `set obs 2000`, `set seed 57`, `x` uniform, `y = sin(4*x) + rnormal()/4`, `g = mod(_n,2)`; `lowess y x if g == 0, generate(wk_s) nograph`; the build form of `test/test_server_build.cscript` SB-01 with the graph `(scatter y x) (lowess y x)` and `filter(g, type(dropdown))` writes an app under `` `w30_work' ``; the helper `_wk_app_lowess` (Python, above the S57 header) loads it with `importlib` under a fresh name, builds `make_document(Document())` (in process, so the inline path), moves the dropdown to 0 the way `test/test_mode_parity.py:2158` `_fire` does, and compares the redrawn lowess `y` with Stata's `wk_s` over the same `x`: largest absolute difference below 1e-6 prints `WK-01 PASS`.
- **WK-02:** after WK-01, no thread named `dash-recompute` exists in Stata's process and `threading.active_count()` equals its value before WK-01: `WK-02 PASS`.

Both pass at the base (guards: the move path restructured by 57-05 must still equal twoway's lowess, and nothing starts a thread in Stata). Run through the driver with `WP30_ONLY=S57`.

## TDD test stubs

New `test/test_served_worker.py` (red at the batch-20 base unless marked guard; 57-01). Module docstring: the defect (Overview), TR-57.7's table. Helpers: `_app(tmp_path, spec)` (the generated app loaded as a module, `test_resource_limits._served`'s form); `_Live` (an in-process server from the app's own `_dash_server_app` on a free port with `serve_token_probe.TEST_TOKEN`, its IOLoop on a thread, S46's harness reused if it exists at the base); `_on_loop(srv, fn)` (runs `fn` on the server loop through `add_callback` and a `concurrent.futures.Future`, so tests never read a server document off its loop); `_spec_lowess(n)` (scatter plus lowess on `n` rows and a dropdown, data from `np.random.default_rng(57)`).

- Test: `_DashRecomputeWorker` keeps one job per slot, replaced in place, FIFO across slots; `forget` removes; past `ceiling` `submit` returns False — `TestTheQueue::test_latest_per_session_fifo_across_sessions`, `::test_the_ceiling_refuses`, `::test_forget`
- Test: a job that raises leaves the thread alive and the next job runs; the condition is not held while a job runs (a job that calls `submit` returns) — `TestTheQueue::test_a_failing_job_does_not_stop_the_worker`, `::test_no_lock_is_held_while_a_job_runs`
- Test: two module executions of one app in one process (as `bokeh serve` does) share one worker and at most one `dash-recompute` thread exists — `TestOneWorkerPerProcess::test_bokeh_serve_reexecution`
- Test: `_dash_worker_wanted` is False for `Document()`, under the trial flag and with `sys._is_gil_enabled` patched to return False; True for a document with a session context — `TestWhoUsesTheWorker::test_the_rule`
- Test: an in-process move never starts the thread and never shows the cue — `TestWhoUsesTheWorker::test_in_process_stays_inline` (guard on the cue's absence: fails only on its missing attribute)
- Test (serve): lowess at 30k, client 1 moves; `/health` polled every 0.1 s answers within 1.0 s at worst (base: 8.11 s at 100k, m5). 57-01 records the base's worst latency at 30k; if it is under 1.5 s, the test uses 50k so that it is red at the base for the right reason — `TestTheLoopAnswersDuringARecompute::test_health`
- Test (serve): during that recompute a second session opens and its brush recounts its card — `::test_other_sessions_answer`
- Test (serve): the apply runs on the loop thread with the session's `_pending_writes is not None`; the compute runs on `dash-recompute` — `TestBokehThreadRules::test_apply_under_the_lock` (guard: true of today's inline move), `::test_compute_off_the_loop`
- Test (serve): two quick moves: the final sources equal the synchronous result of the second; generation 1 is never applied (an apply counter on the slot) — `TestStaleResultsAreDropped::test_two_moves`
- Test (serve): two filters, one with `exclude()` of a graph, moved one after the other within one recompute: the final state equals the synchronous result of both moves — `TestStaleResultsAreDropped::test_two_widgets_with_exclude`
- Test (serve): a brush made while a move waits is cleared by that move's apply, as a move clears any brush today, and the cards then show the move's values — `TestTheCue::test_a_brush_while_waiting`
- Test (serve): over `test_mode_parity`'s served move corpus (`_served_after_move`'s moves), the async final state equals the inline state, source by source and card by card — `TestAsyncEqualsSync::test_corpus` (guard at the base, where both are inline; it carries the change once the worker exists)
- Test (serve): the cue is visible on the client while a recompute waits and hidden after; a redraw made to raise hides it, Bokeh logs the error, the drawing is unchanged and the next move works — `TestTheCue::test_shown_then_hidden`, `::test_a_failed_recompute_clears_it`
- Test (serve): three sessions move together: results apply in submission order — `TestFifoAcrossSessions::test_order` (guard at the base)
- Test (serve): a session closed, and one idle-closed through S46's hook with a short lifetime, mid-recompute: no apply, no exception, the worker serves the next session — `TestAClosedSessionDropsItsResult::test_closed`, `::test_idle_closed`
- Test: the walk of TR-57.7 finds only `_WORKER_AUDIT` names — `TestTheWorkerTouchesOnlyAuditedNames::test_the_walk`
- Test: during a worker redraw no attribute is set on a model whose `document` is not None (a `HasProps.__setattr__` recorder by thread), `curdoc` patched to raise off the loop is never called, and the global `_DASH_MAPPER`/`_DASH_SCHEME` are never written from the worker. A recording subclass is swapped onto `_DASH_MAPPER.__class__`, and the identity and contents of each dict-valued attribute of `_DASH_MAPPER.__dict__` are compared before and after a worker redraw. A worker compute started while the loop is inside `_dash_under_graph_scheme` for another session's build (forced with two `threading.Event`s) still draws with its plan's scheme — `TestTheTripwires::test_no_live_write_off_the_loop`, `::test_no_curdoc`, `::test_no_shared_mapper_write`, `::test_the_scheme_is_the_plans`
- Test: KPI text is formatted on the loop (`_STORAGE_TYPES` replaced by a dict recording the reading thread) — `TestTheTripwires::test_storage_types_read_on_the_loop`
- Test: while one thread holds the app's `warnings.catch_warnings()`, another's `__enter__` waits (two `threading.Event`s); after 200 interleaved blocks `warnings.filters` equals its value before (red at the base through its first assertion, that the app's `warnings` is a `_DashWarnings`); during a 30k lowess move the longest hold is under 0.25 s — `TestTheWarningFilters::test_blocks_serialise`, `::test_filters_survive`, `::test_hold_time`
- Test: a note raised by a redraw on the worker still reaches the served note channel (S23's needle) — `TestTheWarningFilters::test_a_note_still_prints` (guard)
- Test: no function of the generated app imports `warnings` locally (ast walk) — `TestTheWarningFilters::test_no_local_warnings_import` (guard at the base)
- Test: dash.sthlp's Recomputation paragraph says "one worker thread", "Updating..." and "about 3 minutes", and no longer "one event loop -- runs one" — `TestTheHelp::test_the_paragraph`

Pinned tests to change (R9; re-measured at the base, never trusted): `test/test_help_claims_4.py::TestOneRecomputationAtATime` docstring only (`Changed:`); no assertion is flipped unless 57-01's grep finds one.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Queue, ceiling, one worker | pytest `TestTheQueue`, `TestOneWorkerPerProcess` | none | served |
| Inline for in-process documents | pytest `TestWhoUsesTheWorker`; the whole existing served suite | `_DF`, fixtures | served (saved untouched) |
| Loop responsiveness | pytest serve `TestTheLoopAnswersDuringARecompute`; 57-07 measurement at 100k and 200k | generated | served |
| Correctness after moves | pytest serve `TestStaleResultsAreDropped`, `TestAsyncEqualsSync`, `TestFifoAcrossSessions`; `test_mode_parity.py` | parity corpus | both (parity) |
| Cue and failure | pytest serve `TestTheCue` | generated | served |
| Teardown | pytest serve `TestAClosedSessionDropsItsResult` | generated | served |
| Thread safety | pytest `TestTheWorkerTouchesOnlyAuditedNames`, `TestTheTripwires`, `TestTheWarningFilters`, `TestBokehThreadRules` (each bokeh minor of S41's window) | generated | served |
| twoway's lowess after the restructure; no thread in Stata | cscript WK-01, WK-02 | generated in Stata | served (inline) |
| Help | `TestTheHelp`, `test_help_claims_4.py`, `test_help_conformance.py` | dash.sthlp | n/a |
| Registries, tracking | `test_function_test_map.py`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_tracking_documents.py`, `test_cscript_hygiene.py` | — | n/a |

**Acceptance criteria.**
- **AC-57.1** (BR-57.1) `TestTheLoopAnswersDuringARecompute` passes; 57-07 records `/health` worst latency at most 1.0 s during a lowess move at 100k and during a 200k recompute (GAPS2 F3 test 5), against 8.11 s at the base (m5).
- **AC-57.2** (BR-57.2, BR-57.3) `TestAsyncEqualsSync`, `TestStaleResultsAreDropped`, `TestFifoAcrossSessions` pass on bokeh 3.8 and every other verified minor; `test_mode_parity.py` passes with `ALLOWED`/`_MUST_WARN` untouched.
- **AC-57.3** (BR-57.4) `TestTheCue` passes, including the failure path.
- **AC-57.4** (BR-57.5) `TestTheQueue` and `TestOneWorkerPerProcess` pass; 57-07 records the apply order and the last session's wait for 3 sessions at 100k (about 3 times one recomputation); `TestTheHelp` passes.
- **AC-57.5** (BR-57.6) the existing served suite, `test_served_throttle.py` and `test_estimator_cost.py` pass unchanged; WK-01 and WK-02 PASS; `gitnexus detect-changes` at landing names `_generate_app_source` and test symbols only.
- **AC-57.6** (BR-57.7) `TestTheWorkerTouchesOnlyAuditedNames`, `TestTheTripwires`, `TestTheWarningFilters`, `TestBokehThreadRules` pass; no test is deleted; the full suite through the queue reports 0 failed; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 57-01 to 57-09 form one commit, made by 57-09 on `wp30-s57` with the subject `Run served filter-move recomputes on one worker thread (WP-30 P1.31b)`. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s57`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`; every command uses `git -C "$WT"` or `$WT` paths. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "test_wp30_truth.cscript" > "$S/run_test_wp30_truth.do"`, then `WP30_ONLY=S57 "$SLOT" "$S" "$S/run_test_wp30_truth.do"` (log `$S/run_test_wp30_truth.log`). Each task appends the files it changed to `$S/57-files.txt`.

<task type="auto" id="57-01">
  <name>Write the failing worker tests</name>
  <files>test/test_served_worker.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-20-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s57`; stop otherwise. Read `$S/batch-20-impact.txt` and confirm the maintainer's approval of `_generate_app_source` (HIGH) is recorded; stop if absent. At the base, re-find by text and write to `$S/57-anchors.txt`: `_make_filter_cb`, `_on_filter_change` and every statement in it (classify each as widget/mask read, `agg['redraw']`/`_compute_kpi` call, or model write), `_dash_redraw_for`, `_dash_draw_layer`, `_dash_under_graph_scheme`, S46's holder name, session-cap value, idle-close function, trial flag and memo, S41's verified bokeh minors and venv paths; re-run `grep -ln pull_session test/*.py` and `grep -rn "one event loop" test/ dash.sthlp`. Also record whether `_trig_widget` is read inside `_on_filter_change` (TR-57.1's queue key), whether any code iterates SchemeParser's lazy caches or S34's per-scheme dict, and the count of `catch_warnings` sites and of function-local `import warnings` in the template's copied names. Confirm `_DASH_STATE.memo_lock` exists and that `_dash_memo_wrap` takes it around get and put (S46 TR-46.8); if not, stop and report to the orchestrator (the Q-57.1 ruling put it in S46). Create `test/test_served_worker.py` with every stub of "TDD test stubs", naming the new app symbols (`_DashRecomputeWorker`, `_dash_worker_wanted`, `_dash_cur_mapper`, `_DashWarnings`, the `dash_updating` Div) so they fail with KeyError or AttributeError now. Run `python3 -m pytest test/test_served_worker.py -q -n 6 -p no:cacheprovider -rf > "$S/57-new.log" 2>&1`. Write `$S/57-P1.31b-failure.txt`: the base sha, one line per failing node with its first error line, then "Guards (pass at the base)" with the passing nodes, then the m5 and m1 measurements quoted from the research note. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/57-new.log"` is at least 20 and every node not marked guard in "TDD test stubs" is among them; `git -C "$WT" diff --name-only -- dash_render.py dash.sthlp` prints nothing; `test -s "$S/57-anchors.txt"` succeeds.]]></verify>
  <done>Every worker regression test was shown failing on the unmodified tree, with the failure text and the re-found anchors saved.</done>
</task>

<task type="auto" id="57-02">
  <name>Fill the S57 truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Between S01's `S57 start` and `S57 end` lines of the `* ==== S57 P1.31b: Served recompute off the event loop ====` block write WK-01 and WK-02 exactly as "Stata truth" describes, each reporting through `_w30_expect`/`_w30_done` (`WK-0n PASS: …`, or the failure with the case and the largest difference), writing only under `` `w30_work' `` and erasing what they wrote before the end line. The Python helpers (`_wk_app_lowess`, `_wk_threads`) sit in one `python:` block directly above the S57 header and are called through one-line `python:` statements that return through `sfi.Macro.setLocal`. Any Stata helper program declares `version 19` (TR-01.10 item 4). Before first use, `grep -nE '(^|[^A-Za-z0-9_])WK-[0-9]' "$WT"/test/*.cscript "$WT"/test/*.py "$WT"/test/*.do` must print nothing. Run the block through the driver on the unmodified shipped files and record both PASS lines under "Guards" in `$S/57-P1.31b-failure.txt`. After the run, check `~/.stata19/console/stata19.rc` still holds `python_exec` (a SKIP is not a pass). Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "WK-0[12] PASS" "$S/run_test_wp30_truth.log"` prints 2; `grep -c "ALL CHECKS PASSED" "$S/run_test_wp30_truth.log"` prints 1; `grep -c "SKIP" "$S/run_test_wp30_truth.log"` prints 0; `grep -c "^r([0-9]*);" "$S/run_test_wp30_truth.log"` prints 0.]]></verify>
  <done>The S57 block compared the served move's lowess with Stata's lowess and checked that Stata's process starts no thread, both passing on the base as guards.</done>
</task>

<task type="auto" id="57-03">
  <name>Add the bounded worker and slot</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Write in the task log that `_generate_app_source` is HIGH (5 impacted, 3 processes) and that only template text changes. Apply TR-57.1: the worker block directly above `"def make_document(doc):",` with `import threading`, `import copy`, `import functools` and `from tornado.ioloop import IOLoop as _DashIOLoop` added to the template's import lines beside `"import collections as _collections",` if absent; `_DashRecomputeWorker`, `_dash_recompute_worker` (stored as `_DASH_STATE.recompute`, ceiling `_DASH_STATE.cap`), `_dash_worker_wanted`, `_DashSlot`; in `make_document`, after S46's cap check, `_slot = _DashSlot()` with `gen=0`, `cue=None`, `alive=True`. Each new function gets a docstring stating its thread (loop or worker). Do not touch `_dash_event_throttle`, `_dash_limits` or any copy list.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_worker.py -q -n0 -p no:cacheprovider -k "TestTheQueue or TestOneWorkerPerProcess or TestWhoUsesTheWorker and test_the_rule"` passes; `python3 -m pytest "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_served_throttle.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every generated app carried one bounded, lazily started recompute worker per process and a per-session slot, used by nothing yet.</done>
</task>

<task type="auto" id="57-04">
  <name>Isolate mapper, scheme and warnings state</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-57.2: `_DASH_CTX`, `_dash_cur_mapper`, `_dash_cur_scheme` in the worker block; in `_dash_draw_layer` bind `_m = _dash_cur_mapper()` first and replace each `_DASH_MAPPER` in its body with `_m`; replace each `_DASH_SCHEME` read in `_dash_redraw_for`, `_dash_draw_layer` and the helpers the redraw calls inside the template (listed in `$S/57-anchors.txt`) with `_dash_cur_scheme()`; give S34's `_dash_under_graph_scheme` its context branch. Apply TR-57.6 (`_DASH_WARN_LOCK` kept as `_DASH_STATE.warn_lock`, `_DASH_WARN_LOCK_STATS`, `_DashLockedCatchWarnings`, `_DashWarnings`, the rebinding of `warnings` after the worker block). Do not edit S46's memo: its lock is S46's (TR-46.8, Q-57.1 ruling), and 57-01 confirmed it. Run the whole served suite: `python3 -m pytest test/test_mode_parity.py test/test_served_filter_move.py test/test_served_linked_views.py test/test_server_layer_defects.py test/test_server_scheme.py test/test_server_brush.py -q -n 6 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[The suite files of the action report 0 failed; `python3 -m pytest test/test_served_worker.py -q -n0 -p no:cacheprovider -k "TestTheWarningFilters and (blocks_serialise or filters_survive)"` passes; `grep -c "_DASH_MAPPER\." "$WT/dash_render.py"` is lower than at the base by the count of replaced reads recorded in the task log.]]></verify>
  <done>The redraw path read its mapper and scheme through a thread context, S34's swap left module state alone off the loop, and dash's catch_warnings blocks were serialised, with every served test still green.</done>
</task>

<task type="auto" id="57-05">
  <name>Split the move into plan, compute, apply</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-57.3 to `_make_filter_cb` at the base text: add `_doc=None` and `_slot=None` keywords and pass `_doc=doc, _slot=_slot` at its call site; write `_dash_move_plan`, `_dash_move_compute`, `_dash_move_apply`, `_dash_move_post`, `_job` and `_hop` as closures in it; move every statement of `_on_filter_change` into plan or apply by the classification in `$S/57-anchors.txt`, keeping each statement's text and order and changing only where masks and results are read from; `_on_filter_change` then chooses the worker or the inline path. The plan captures the scheme and the fresh-state mapper copy of TR-57.2. Apply TR-57.4 (the cue after the CSV block, only when `_dash_worker_wanted(doc)`) and TR-57.5 (`_dash_worker_forget`, `on_session_destroyed`, and the one statement before `doc.clear()` in S46's idle periodic callback). Use no `without_document_lock`. Re-run 57-04's served suite plus `test_served_throttle.py`, `test_help_claims_1.py`, `test_help_claims_3.py`, `test_help_claims_4.py`, `test_estimator_cost.py` with `-n 6`.
  ]]></action>
  <verify><![CDATA[The action's files report 0 failed; `python3 -m pytest test/test_served_worker.py -q -n 6 -p no:cacheprovider -k "not TestTheWorkerTouchesOnlyAuditedNames and not TestTheHelp"` reports 0 failed (those two pass after 57-06 and 57-08).]]></verify>
  <done>A served move planned on the loop, recomputed on the worker, and applied in one next-tick callback under the document lock, with stale results dropped, a cue shown, and in-process documents unchanged.</done>
</task>

<task type="auto" id="57-06">
  <name>Audit the worker path and Bokeh window</name>
  <files>test/test_served_worker.py</files>
  <action><![CDATA[
    Run `TestTheWorkerTouchesOnlyAuditedNames::test_the_walk` and give every name it reports a row in `_WORKER_AUDIT` and in the module docstring's table with its verdict from TR-57.7; a name whose verdict would be "written by both threads" is not allowlisted: fix it in `dash_render.py` by the TR-57.2 or TR-57.3 rule and record it in the task log. Run `TestTheTripwires`, `TestTheWarningFilters` and `TestBokehThreadRules`. Then, for each interpreter of TR-57.8 (3.8 `/opt/anaconda3/bin/python3`, 3.9 `python3`, and 3.10 `$S/venv-s41-bk310/gatevenv/bin/python` only if `$S/41-ceiling.txt` reads 3.11), run `<python> -m pytest test/test_served_worker.py -q -n0 -p no:cacheprovider -k "TestBokehThreadRules or TestAsyncEqualsSync or TestStaleResultsAreDropped or TestTheTripwires"` from `$WT` and append its output, headed by `<python> -c 'import bokeh; print(bokeh.__version__)'`, to `$S/57-bokeh-window.txt`. Install nothing outside `$S/venv-*` (M10).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_worker.py -q -n 6 -p no:cacheprovider -k "not TestTheHelp"` reports 0 failed; `$S/57-bokeh-window.txt` shows `0 failed` once per verified minor.]]></verify>
  <done>Every global and free name the worker reaches had an audited verdict pinned by a test, and the thread rules held on every verified bokeh minor.</done>
</task>

<task type="auto" id="57-07">
  <name>Measure latency at N=100k</name>
  <files>none</files>
  <action><![CDATA[
    Write `$S/57-latency.py` (not committed), using `test/test_served_worker.py`'s `_Live` harness with S46's default cap: (a) scatter plus lowess at 100k rows and a dropdown, one session moves to half the rows, `/health` polled every 0.1 s: worst latency, the move's apply time; (b) 200k rows x 3 layers with lfit, one move: `/health` worst latency (GAPS2 F3 test 5); (c) three sessions on (a) move within 0.2 s: their apply order and the last one's wait; (d) the same three moves on the base tree (a checkout of `batch-20-base` in `$S/s57-base`, removed afterwards) for the before values. Run it with the suite's `python3` at most twice per case and write `$S/57-latency.txt` with command, interpreter, bokeh version, load average and every number.
  ]]></action>
  <verify><![CDATA[`$S/57-latency.txt` holds cases (a)-(d); in (a) and (b) the after-tree `/health` worst latency is at most 1.0 s; in (c) the apply order equals the move order.]]></verify>
  <done>The loop's responsiveness, the per-move cost and the cap-times-recompute wait were measured at 100k and 200k rows before and after the change.</done>
</task>

<task type="auto" id="57-08">
  <name>Document the worker and map functions</name>
  <files>dash.sthlp, test/test_help_claims_4.py, test/function_test_map.py</files>
  <action><![CDATA[
    Rewrite the "Recomputation." paragraph's last sentence (dash.sthlp:1779-1780 at c96facd) by TR-57.9, using the 100k numbers of `$S/57-latency.txt` only if they change "about 3 minutes"; every line at most 79 characters. Change `TestOneRecomputationAtATime`'s docstring in place to "The launcher's server is one process with one recompute worker, so the recomputations of every session run one at a time, off the event loop." and record the `Changed:` line in `$S/57-flips.txt`. Add TR-57.10's keys under `# WP-30 S57 (P1.31b): Served recompute off the event loop (P1.31 part b)`, alphabetical, each naming its `test_served_worker.py` node; read each qualname from the generated app with `co_qualname`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_worker.py test/test_help_claims_4.py test/test_help_conformance.py test/test_function_test_map.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "one event loop -- runs one" "$WT/dash.sthlp"` prints 0.]]></verify>
  <done>The help stated the worker, the cue and the worst wait, and every new app function named its test.</done>
</task>

<task type="auto" id="57-09">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.31b"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution", today's date as `ddmonyyyy` and the numbers of `$S/57-latency.txt`. Delete the `"P1.31b"` key line of `WP30_OPEN`. Replace `<!-- WP-30 P1.31b -->` in place with "Notes: CHANGELOG line". Run `test_tracking_documents.py test_cscript_hygiene.py test_served_worker.py test_mode_parity.py` with `-n 6` and the S57 block through the driver; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/57-full-1.log"` in the background, read when `exit=` appears (E6 for the known flaky tests). Stage exactly `$S/57-files.txt` plus these three; check `git -C "$WT" diff --cached --name-only` equals that list (G6). Write `$S/57-message.txt` by "Notes: commit message", check G7, confirm the branch, commit, check G7 again, and report the sha and message to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/57-full-1.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.31b -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.31b": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.31b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.31b was closed naming existing tests, its marker carried the measured before and after, and one green commit on wp30-s57 was ready for the merger.</done>
</task>

## Section completion criteria

- A served filter move recomputes on one daemon worker thread per process; `/health`, other sessions and their brushes answer during it (AC-57.1).
- The queue holds at most one waiting move per session and never more than S46's cap; a newer move replaces a session's waiting one; sessions are served in order; stale, idle-closed and closed-session results are dropped.
- Every model write of a move happens in one next-tick callback under the document lock; the worker's only cross-thread call is `IOLoop.add_callback`.
- In-process documents, the warm-up, the trial, the saved page and Stata's process recompute inline exactly as before (WK-01, WK-02, the existing suite).
- The worker reads its mapper and scheme through `_DASH_CTX`, formats nothing, and every name it reaches is audited by a test; dash's `catch_warnings` blocks are serialised and notes still print.
- The help states the worker, the cue and the worst wait; the new functions are mapped; the entry, key and marker are closed in one green commit `(WP-30 P1.31b)`.

## Notes

- **Q-57.1 (resolved by the orchestrator's ruling).** S46's estimator memo (64 MB LRU, `_shared_stat_lines`' last entry) is read and written by `make_document` on the loop and by the worker's lowess. S46 now holds `state.memo_lock` (a `threading.Lock`; TR-46.3, TR-46.8). Every get (lookup and `move_to_end`) and every put (insert, byte total, eviction) runs under it, and the estimator runs outside it. Its test is `TestEstimatorMemo::test_the_lock_guards_get_and_put`. S57 relies on that lock, adds none, and edits nothing outside `_generate_app_source`. 57-01 stops if the lock is missing at the base.
- **Why the hop through `IOLoop.add_callback`.** The register asks for "add_next_tick_callback". It is still the call that applies the result, but it is made on the loop thread. Called from the worker, `Document.add_next_tick_callback` would add to the document's callback set and emit a change event from a second thread (E5). Bokeh documents that as safe, but it is internal code that changes between minors. Tornado's `add_callback` is the one documented cross-thread entry, and the app already uses it for the parent watch.
- **Residuals, deferred (WP-30), for S58.**
  - Library-internal `catch_warnings` blocks (pandas, numpy) are not covered by `_DashWarnings`. An overlap of one of them with a dash block can still swap `warnings.filters` for one block's length. `TestTheWarningFilters::test_filters_survive` reports any drift seen. Python 3.14's `-X context_aware_warnings` removes the hazard.
  - A free-threaded interpreter recomputes inline.
  - Opening a session stays on the loop (P2.57). So do S21's re-finish and S27's base finish in the apply step, because they write Range1d and glyph models (at most 0.2 s per figure per move at 500k rows, IR-17 P1.3.8).
  - A brush made while a session's move waits is cleared when that move is drawn, as any move clears a brush; the cue shows the move is pending (`TestTheCue::test_a_brush_while_waiting`).
  - Linux and Windows are unmeasured (M4).
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. WK-01 then SKIPs, and a SKIP is not a pass. Check the file after each slot run.
- **Live tests** are marked `serve` (`test/conftest.py:41`). They bind loopback on a free port with `serve_token_probe.TEST_TOKEN` and stop their server in `finally`. Each asserts at teardown that the worker has no waiting job, so a leaked job fails the test that left it. Port collisions follow E6.
- **Merge rules for the shared files.**
  - R1: WK-01/02 only inside S57's block.
  - R2: no copy-list entry; map keys only under S57's anchor.
  - R3: the Recomputation paragraph of Server Mode. S57 is not in R3's owner table, and batch 20 has no other section.
  - R4/R5: the one `P1.31b` marker, the entry and its key.
  - R9: one docstring change.
  - R12: S57 is batch 20's only `_generate_app_source` editor.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `ServerAppBuilder._generate_app_source` only, plus the test symbols of `test_served_worker.py`, `test_help_claims_4.py` and `test_tracking_documents.py`.
- **Commit message.**
  - Subject: as in "Commit boundary".
  - Body, in order: `$S/57-P1.31b-failure.txt`; the measured defect (Overview's block); what changed and where (TR-57.1-TR-57.9: the worker block, the context helpers, `_DashWarnings`, the plan/compute/apply split in `_make_filter_cb`, the cue, the teardown, the help); the latency table of `$S/57-latency.txt`; the threat closed (G9: one session's recompute no longer denies service to every other session and `/health`; cross-thread writes are confined to the document lock).
  - Then one line each:
    - `Regression: test/test_served_worker.py::<Class>::<test> -- failed at <base sha> with <text>` for each regression node;
    - `Guard: test/test_wp30_truth.cscript WK-01` and `WK-02`;
    - `Changed: test/test_help_claims_4.py::TestOneRecomputationAtATime -- docstring now names the worker; assertion unchanged`;
    - `BUGS.md: "<WP30_OPEN["P1.31b"] title>" (closed)`.
  - No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.31b). A served filter move now reads the widgets and builds its masks on the event loop, recomputes every layer redraw and KPI statistic on one worker thread per server process (ServerAppBuilder._generate_app_source: _DashRecomputeWorker, a queue of one waiting move per session bounded by the session cap, latest move per session wins, sessions first come first served), and applies the result in one next-tick callback under the document lock, dropping results overtaken by a newer move, an idle close or a closed session; the page shows Updating... meanwhile; the redraw draws with a worker-private mapper and scheme (_dash_cur_mapper, _dash_cur_scheme), formats KPI text only on the loop, and dash's catch_warnings blocks are serialised (_DashWarnings); documents built in process, the warm-up and Stata's process recompute inline as before. /health answered within <x> s during a lowess move at 100,000 rows (8.11 s before) and within <y> s during a 200,000-row recompute. lpolyci's 8.7 s was closed by WP-29 P0.9. Pinned by test/test_served_worker.py::TestTheLoopAnswersDuringARecompute::test_health, test/test_served_worker.py::TestAsyncEqualsSync::test_corpus, test/test_served_worker.py::TestStaleResultsAreDropped::test_two_moves, test/test_served_worker.py::TestTheWorkerTouchesOnlyAuditedNames::test_the_walk, test/test_served_worker.py::TestTheTripwires::test_no_live_write_off_the_loop, test/test_wp30_truth.cscript WK-01. Residual, deferred (WP-30): opening a session still runs on the event loop (P2.57); pandas' and numpy's own catch_warnings blocks are not serialised; free-threaded Python recomputes inline; Linux and Windows unmeasured (M4).
  ```
- **CHANGELOG line** (replaces `<!-- WP-30 P1.31b -->` under `### Fixed in WP-30`):

  ```
  - A filter move in a served dashboard no longer freezes the server for everyone: a lowess move at 100,000 observations held `/health`, every other session's moves, brushes and downloads, and new sessions for 8.1 s; recomputations now run on one worker thread per server process, one at a time in the order sessions asked, while the page shows "Updating..." and keeps its drawing, and `/health` answered within <x> s. A session's newer move replaces its waiting one; the longest wait is about the session limit times one recomputation (about 3 minutes with 20 sessions for lowess at 100,000 observations). (WP-30, P1.31b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md F3:** F3d is closed by `<sha>`. F3 is Closed when P1.31a (S46) is also closed; S58.2's list carries F3: P1.31a, P1.31b. Plan item 4's `without_document_lock` was not used, on purpose (E5).
  - **GAPS2.md C intro** (:711): the served-cost sentence is closed by `<sha>`; the lpolyci part by WP-29 P0.9 (`e32be3a`).
  - **DROPIN-REMAINING.md:165:** "Recompute part closed by `<sha>` (WP-30 S57); lpolyci by WP-29 P0.9."
  - **P2.57** (register): file it with S57's 100k measurement of session open.
  - **New P2 row:** library-internal `catch_warnings` races (Residuals above).
  - **AGENTS.md invariant:** "A served move writes models only in its next-tick apply step; the recompute worker reads its mapper and scheme through `_dash_cur_mapper()`/`_dash_cur_scheme()`, and every name it reaches is in `test_served_worker._WORKER_AUDIT`."
  - **Unverified:** Linux, Windows and Intel Mac threading (M4).
