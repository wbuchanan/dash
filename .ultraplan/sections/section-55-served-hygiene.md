# Section 55: Served and session hygiene

> Part of: WP-31 · GAPS3 rows: H3 (mathjax component; the off-loop build stays a documented residual), H4, H7 · Risk: green · Batch: 18 · Depends on: 01 · Blocks: -- · Tasks: 4, 3 commits · Case-id prefix: U55

## Overview

**What is wrong today.** GAPS3 H3 (GAPS3.md:240): "the bundle ships bokeh-mathjax (1.79 MB per session) though dash no longer uses it"; `_dash_served_template` builds the page with `Resources(mode="server", root_url="/")` (dash_render.py:5101) which lists every Bokeh component, mathjax included. GAPS3 H4 (:241): "`BOKEH_RESOURCES=cdn` blanks the served page silently; `BOKEH_MINIFIED/DEV` change the saved page silently; `/health` reports only ok/timestamp; the browser-launch return code is captured and never read" -- `_HealthHandler.get` (template :48386, `def get`; REVIEW-4 R4-30 -- re-read before editing) writes `{"status": "ok", "timestamp": ...}`; `_dash_open_browser` captures `_op_rc` (dash.ado:8166) and returns `opened` without reading it. GAPS3 H7 (:244): "four unprefixed Mata functions (`_json_escape`, `_is_utf8`, `_expand_plottype_str`, `_first_comma_pos`) dropped by name on repair; `sys.argv` overwritten and never restored; `_dash_xm`, `_dash_render_ns`, `_dash_priv_argv` left in `__main__`" -- `_dash_require_mata`'s repair (dash.ado:524-528) drops them by a hand list; `python: sys.argv = [...]` (dash.ado:665, :10997) replaces the interpreter's argv for the rest of the Stata session; `_dash_xm`, `_dash_render_ns` (:676, :681) and `_dash_priv_argv` (:669) persist in Stata's Python `__main__`.

**After this section** the served `Resources` exclude the `bokeh-mathjax` component; the launcher refuses `BOKEH_RESOURCES` set to anything but `inline`/`server` (and `BOKEH_RESOURCES=cdn` in particular) with one sentence and `exit 2`, and both renderers print one note when `BOKEH_MINIFIED` or `BOKEH_DEV` is set (the saved page then still inlines Bokeh but says which bundle); `/health` reports `{"status":"ok","timestamp":...,"sessions":<n>,"max_sessions":<n>,"bokeh":"<version>","dash":"<version>","uptime_s":<n>}` (no `rows`: DECISIONS A30, REVIEW-4 R4-23); `_dash_open_browser` reads `_op_rc` and prints `dash: the browser command returned <rc>; open <path> yourself` when it is non-zero; the four Mata functions are renamed `_dash_json_escape`, `_dash_is_utf8`, `_dash_expand_plottype_str`, `_dash_first_comma_pos` (the repair's hand list deleted); `sys.argv` is saved before each render and restored after; and the three `__main__` names are deleted after use.

**Why one section.** Three S3 hygiene rows with no twoway content, each a small, local edit; the index places them together in batch 18 beside S53 and S54 as the "served template env/health/bundle" owner.

**Test order and commit rule.** Three cycles, three commits in row order H3, H4, H7: each row's failing tests are written against the tree the previous row's commit leaves (BRIEF). 55-01 writes H3's tests red and its fix and commit; 55-02 H4; 55-03 H7 (Stata side) with its cscript cases; 55-04 the help/notes and the three closings (each row's closing is part of its own commit -- 55-04 is a checklist step that confirms the three closings happened and runs the covering tests once; it makes no fourth commit).

### Section decisions (binding on the executor)

- **D-55a. H3's off-loop `make_document` build stays a residual.** GAPS3 H3's first clause ("`make_document` builds on the event loop (1.6-4.6 s at 100-200k rows)") is a design change the index does not schedule (no section owns the worker/`make_document` restructuring); S55 closes the mathjax clause, re-states the `catch_warnings` and "brush cleared while a move waits" clauses as open in the BUGS.md residual entry "Served build on the event loop" (S2) and writes the H3 Tracked line as "Partly closed".
- **D-55b. `BOKEH_RESOURCES`: refuse, do not override.** The launcher (template `__main__`, :50985 region) reads `os.environ.get('BOKEH_RESOURCES', '')`; a value other than `''`, `'server'` or `'inline'` prints `dash: BOKEH_RESOURCES is set to '<value>'; this app serves Bokeh from itself (mode server) and cannot run with another resource mode. Unset it and start again.` (value through `_dash_display`, 40 characters) and exits 2 before `Server` is built. `BOKEH_MINIFIED` and `BOKEH_DEV`: both renderers print (once per process, `_dash_warn_once`) `dash: <NAME> is set, so Bokeh's <minified|development> bundle is used; the page is larger/smaller than the shipped one but behaves the same` at the first page build; the saved page's seal (`_dash_seal_saved_page`) already hashes whatever bundle is inlined, so nothing else changes. (Refusing them would break a legitimate debugging use; reporting makes the difference visible, Q18/M8.)
- **D-55c. `/health` fields.** `status`, `timestamp` (as today), `sessions` (the holder's open-session count, WP-30 P1.31a `_DASH_SESSIONS`), `max_sessions` (the limit), `bokeh` (`bokeh.__version__`), `dash` (the `*! version` line's number, read from `_DASH_VERSION` if present else `"0.1.0"`), `uptime_s` (integer seconds since module import). No `rows` (the handler is unauthenticated, rate-limited only, and the dataset size is not liveness or load data: DECISIONS A30, REVIEW-4 R4-23). No request data, no paths, no hostnames (rule 1: nothing an unauthenticated probe should learn beyond liveness and load; the handler stays behind `_HEALTH_LIMITER`).
- **D-55d. Mata renames are mechanical and complete.** `sed`-style rename of the four names in dash_parse.mata (definitions and every call), the header index (`*!` lines :25, :365-369 region), dash.ado's `_needed` list (`_json_escape` → `_dash_json_escape`, alphabetical place), the repair block (delete the `foreach f in ...` loop :525-527, keep `capture mata: mata drop _dash_*()`), test/program_coverage_map.py keys (:413, :418, :450, :487) and every cscript or pytest that names them (`grep -rn "_json_escape\|_is_utf8\|_expand_plottype_str\|_first_comma_pos" test/ scripts/`). The cscript ids that cover them stay (the map's values are unchanged).
- **D-55e. argv and `__main__`.** Before `python: sys.argv = [...]` (dash.ado:665 and :10997) insert `python: _dash_saved_argv = list(sys.argv)`; the render line (:681) becomes `capture noisily python: _dash_render_ns = _dash_xm._dash_run_renderer("`_py_renderpy'")` followed by `local _rrc = _rc`, then `python: sys.argv = _dash_saved_argv` and `python: del _dash_saved_argv`, then `if `_rrc' exit `_rrc'` -- the restore PRECEDES every exit, because a `python:` line that errors exits the program at once and would leave argv overwritten (REVIEW-4 R4-24); the same shape (`capture noisily python:` / save `_rc` / restore / `exit`) after the serve launch at :10997; after `_dash_render_ns` has been read (the lines that read it -- grep `_dash_render_ns` in dash.ado, the readers follow :681), `python: del _dash_xm, _dash_render_ns` and, when set, `python: del _dash_priv_argv` (guard with `python: globals().pop('_dash_priv_argv', None)` so the no-`private` path needs no branch). The `_dash_dv` at :6139 is deleted the same way after its reading.

## Risk: [green] -- local edits, each with a direct test

**Risk factors.** (1) The `Resources` component list API: `Resources(mode="server", components=[...])` must still list `bokeh`, `bokeh-widgets`, `bokeh-tables`, `bokeh-gl`, `bokeh-api`? -- read `bokeh.resources.Resources.components` at both installed versions; (2) a missed rename leaves a Mata call unresolved at run time (r(3499)); (3) `del` of a name a code path never set raises `NameError` in Stata's Python.

**Mitigation.** (1) `test_the_served_resources_list_every_component_but_mathjax` compares with `Resources(mode="server").components` minus `bokeh-mathjax` on the installed Bokeh; (2) `grep -c` verify steps and `make`-free cscript runs of test_json_escaping, test_utf8_validation, test_parser, test_tokenizer through `scripts/stata_slot.sh`; (3) `globals().pop` form (D-55e).

## Dependencies

- **Depends on: 01.** **Blocks: none.**
- **Parallel batch: 18** with S53 and S54. S55 edits `_dash_served_template`'s `Resources` call (:5101) and `_dash_check_served_template` if it counts components, the launcher `__main__` lines (:50985 region), `_HealthHandler.get` (:48386), `_dash_dep_versions`' caller for the env note, dash.ado's `_dash_open_browser`, `_dash_require_mata`, the two `sys.argv` sites, and dash_parse.mata's four names. S53/S54 touch none of these.

## Evidence

```python
5101    page = file_html(Div(text=""), Resources(mode="server", root_url="/"),
5102                     "dash", template=_dash_served_template(nonce))
```

`grep -n "mathjax" dash_render.py` at `6370ca4` prints one docstring line (:33643) -- no code excludes the component.

```
48386            "    def get(self):",
48390            "        self.write('{\"status\": \"ok\", \"timestamp\": \"' + ts + '\"}')",   (the write line four lines below `def get`; re-read, R4-30)
```

```
8166        mata: st_local("_op_rc", strofreal(_stata("shell " + st_local("cmd"), 0, 1)))
8167        local opened 1
```

```
524        capture mata: mata drop _dash_*()
525        foreach f in _expand_plottype_str _first_comma_pos _is_utf8 ///
526                _json_escape {
527            capture mata: mata drop `f'()
528        }
```

```
665    python: sys.argv = ["dash_render.py", "--spec", "`_py_spec'", ...]
669        python: _dash_priv_argv = sys.argv.append("--private-output")
676    python: _dash_xm = sys.modules["_dash_render_export"]
681    python: _dash_render_ns = _dash_xm._dash_run_renderer("`_py_renderpy'")
10997   python: sys.argv = ["dash_render.py", "--spec", "`_py_master'", ..., "--launch", ...]
```

dash_render.py's own `_dash_run_renderer` saves and restores `sys.argv[0]` only (:3426-3431).

### Existing tests that pin today's behaviour

- test/test_help_claims_4.py::TestTheRealHandoffServes::test_it_serves_and_stops (names `app:_HealthHandler.get` in function_test_map) -- reads `/health` and asserts `status == "ok"`: unchanged; add a field test beside it.
- test/test_server.py::TestRateLimiterEnforcement::test_health_handler_prepare_blocks_and_returns_429 -- unchanged.
- test/test_program_coverage_map.py (the four Mata keys) -- flipped by rename (D-55d).
- test/test_env_guards.cscript ENV-xx (python/mata guards) -- the repair path PC-30 in test_program_coverage.cscript loads a half library; it keeps passing when the hand list is gone because `mata drop _dash_*()` now covers every name.
- Any test asserting the served page's script count (test_csp.py `scripts == 0` guard in `_dash_check_served_template`, :5108) -- the count drops by one bundle; the guard asks for `> 0`.

## User stories

- **US-55.1** As an operator I want a served session not to ship 1.8 MB of MathJax it never uses.
- **US-55.2** As an operator I want a clear refusal when my environment would blank the page, and a note when it changes the bundle.
- **US-55.3** As an operator I want `/health` to tell me sessions, versions and uptime so that a probe can alert on load.
- **US-55.4** As a Stata user I want dash to leave my Python session's `sys.argv` and namespace as it found them.

## Business requirements

- **BR-55.1** The served page's resources exclude `bokeh-mathjax`; everything else is unchanged.
- **BR-55.2** `BOKEH_RESOURCES` set to an unsupported mode stops `dash serve` with one sentence; `BOKEH_MINIFIED`/`BOKEH_DEV` print one note per process.
- **BR-55.3** `/health` returns the D-55c fields; nothing else.
- **BR-55.4** A failed browser command is reported with its return code and the path.
- **BR-55.5** After `dash build` or `dash serve`, `sys.argv` equals its value before, and `__main__` holds none of `_dash_xm`, `_dash_render_ns`, `_dash_priv_argv`, `_dash_saved_argv`, `_dash_dv`.
- **BR-55.6** Every Mata function of dash_parse.mata starts with `_dash_`.

## Technical requirements

- **TR-55.1 (H3)** `_dash_served_resources()` (new, shared? NO -- `_dash_served_template`'s caller is the saved-side `_dash_check_served_template` and the served `make_document` uses Bokeh's own resources through `bokeh serve`; the served page is Bokeh's, built from the template -- the component list is set on the `Server`/application via `BOKEH_RESOURCES`? Read :5095-5115 and the template's `_dash_server_app` to find where `Resources` reaches the served handler; the component exclusion must be applied where the SERVER builds its resources (`Server(..., resources=...)` is not a Server argument; Bokeh reads `settings.resources()`; the documented route is a custom `Resources` subclass or `bokeh.settings.settings.resources_mode`). Executable rule: in the template's `_dash_server_app`, after the `Server` is built, set `_server._tornado.resources = Resources(mode='server', root_url='/', components=[c for c in Resources(mode='server').components if c != 'bokeh-mathjax'])` if `_tornado` exposes `resources` (verify on the installed Bokeh with `python3 -c "from bokeh.server.server import Server; ..."`); else the template's `{% block js_resources %}` override (`_dash_served_template`) filters `bokeh-mathjax` from `bokeh_js` text by regex on the `<script src=".../bokeh-mathjax...">` element -- the second route is certain and local; use it, and pin it with `test_the_served_page_names_no_mathjax_script`. Also drop the same component from :5101's `Resources` for the check.
- **TR-55.2 (H4 env)** Launcher: D-55b's check before `_dash_server_app(...)` (:51009), after the `BOKEH_ALLOW_WS_ORIGIN` block; a module-level `_dash_env_bundle_note()` (shared, copy list after `_dash_reference_lines`) called once at the top of `main()` (saved) and `make_document` (served): the `_dash_warn_once` note for `BOKEH_MINIFIED`/`BOKEH_DEV`.
- **TR-55.3 (H4 health)** `_HealthHandler.get` writes `json.dumps({...})` of D-55c's dict (import json in the template head if absent); `_DASH_START = time.monotonic()` at module level; sessions from the WP-30 holder (`_DASH_SESSIONS`/the holder's count attribute, grep `max_sessions` in the template to find the names).
- **TR-55.4 (H4 rc)** dash.ado `_dash_open_browser`: after :8166, `if `_op_rc' != 0 { mata: _dash_say("txt", "dash: ", "the browser command returned " + st_local("_op_rc") + "; open " + st_local("path") + " yourself", "") }`; `return scalar rc = `_op_rc'` (0 when not run).
- **TR-55.5 (H7 Mata)** D-55d renames; dash_parse.mata header index lines updated; `_dash_require_mata` `_needed` alphabetical; repair loop deleted; program_coverage_map keys renamed in place.
- **TR-55.6 (H7 argv/names)** D-55e at :665/:681 and :10997/the serve return; :6139 `_dash_dv`.
- **TR-55.7 Maps.** function_test_map: `_dash_env_bundle_note`, `app:_HealthHandler.get` (existing entry updated to the new field test). program_coverage_map: the four renamed keys.
- **TR-55.8 Help.** dash_serve.sthlp (or dash.sthlp's serve section): the `/health` fields, the `BOKEH_RESOURCES` refusal and the bundle note; owned paragraph "Environment" (R3).

## Boundaries

- No worker/`make_document` restructuring (D-55a); no change to the rate limiter, the key, the CSP policies.
- No change to dash_render.py's `_dash_run_renderer` argv handling (:3426-3431, already restored).
- No `bokeh-mathjax` removal from the SAVED page's INLINE bundle (file_html INLINE inlines what Bokeh decides; the saved page is not H3's claim).

## Stata truth

None. Cases in area scripts: test_setup_*.cscript / test_env_guards.cscript gain `U55-1` (after `dash scatter mpg weight, saving(x.html)`, `python: assert sys.argv == <saved>` through a `python:` one-liner comparing with a value captured before; and `python: assert '_dash_xm' not in dir()`), `U55-2` (`_dash_open_browser, dryrun` returns `r(rc)` 0; with `global dash_nobrowser 1` the rc is 0 and nothing printed), `U55-3` (test_program_coverage.cscript: the repair path PC-30 still passes with the hand list gone), `U55-4` (test_json_escaping.cscript: `_dash_json_escape` answers as `_json_escape` did -- rename the existing JSE-01 call site; the id stays). Truth block `* ==== S55 H4: served environment and health ====` (one block per row, A14; H3 and H7 have no block -- their checks are the pytest files and the area cscript cases above), appended by 55-02: `U55-5` a `dash serve, dryrun`-style generated app source holds `uptime_s` and `BOKEH_RESOURCES` (`cert_file_has`).

## TDD test stubs

H3 (red at 6370ca4), `test/test_served_resources.py`: `TestNoMathjax::test_the_served_page_names_no_mathjax_script` (render the served template page through `_dash_check_served_template`'s path or the `_Served` fixture's first GET), `::test_every_other_component_is_present` (`bokeh`, `bokeh-widgets`, `bokeh-tables`, `bokeh-gl` as the installed `Resources(mode="server").components` lists them, minus mathjax).

H4 (red after H3's commit), `test/test_served_env.py`: `TestBokehResources::test_cdn_is_refused_with_exit_2` (run the generated app's `__main__` with `BOKEH_RESOURCES=cdn` through `subprocess` as test_server_rate_limit.py runs the launcher flags; assert rc 2 and the sentence), `::test_server_and_inline_pass`; `TestBundleNote::test_minified_prints_once_saved`, `::test_dev_prints_once_served`; `TestHealth::test_fields` (`_Served` fixture, GET `/health`, keys == D-55c's set, `sessions` int, `bokeh` == installed), `::test_no_extra_fields`; `test/test_browser_rc.cscript`? NO -- U55-2 in test_setup_*.cscript.

H7 (red after H4's commit), `test/test_session_hygiene.py`: `TestMataNames::test_every_mata_function_is_prefixed` (parse `^(string|real|void|...)\s+\w+\s+(\w+)\(` definitions in dash_parse.mata; all start `_dash_`), `::test_the_repair_has_no_hand_list` (dash.ado :524-528 holds only the wildcard drop); `TestArgv::test_dash_ado_saves_and_restores_argv` (static: every `sys.argv = [` line in dash.ado is preceded by `_dash_saved_argv = list(sys.argv)` and followed, before the program's `end` AND before any `exit` that follows the render or launch line, by `sys.argv = _dash_saved_argv`; the render and launch `python:` lines are `capture noisily`, R4-24), `::test_the_main_names_are_deleted` (static: each of the five names has a `del`/`pop` after its last read). Flips: test_program_coverage_map.py key renames (`Flipped:` lines, one per key).

Parity: none (no page content changes).

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| no mathjax component | pytest | none | served |
| env refusal/notes | pytest subprocess | none | both |
| /health fields | pytest `_Served` | none | served |
| browser rc | cscript U55-2 | none | n/a |
| Mata names, argv, namespace | pytest static + cscript U55-1, 3, 4 | none | n/a |

**AC-55.1** every stub green in its row's cycle; **AC-55.2** the four renamed Mata cscripts pass; **AC-55.3** test_csp.py, test_serve_token.py, test_server*.py green; **AC-55.4** three commits, subjects ending `(WP-31 H3)`, `(WP-31 H4)`, `(WP-31 H7)`.

## Tasks

**Commit boundary.** 55-01 is the H3 commit `Serve Bokeh without the mathjax component (WP-31 H3)`; 55-02 the H4 commit `Refuse an unsupported BOKEH_RESOURCES, note BOKEH_MINIFIED and BOKEH_DEV, deepen /health, report the browser return code (WP-31 H4)`; 55-03 the H7 commit `Prefix the four Mata functions, restore sys.argv and clear the render names from the Python session (WP-31 H7)`; 55-04 commits nothing.

<task type="auto" id="55-01">
  <name>Drop mathjax from the served bundle and commit H3</name>
  <files>test/test_served_resources.py, dash_render.py, BUGS.md</files>
  <action><![CDATA[Create test/test_served_resources.py (H3 stubs), run it on the unmodified tree, save <scratch>/55-01-failure.txt. Apply TR-55.1 (the template js_resources filter or the tornado resources assignment, whichever the installed Bokeh supports -- verify first with a python3 -c probe; also :5101). Run test/test_served_resources.py, test/test_csp.py, test/test_serve_token.py, test/test_server_serves.py. Close BUGS.md "Served app ships bokeh-mathjax" (the H3 entry S01 opened; keep its off-loop/catch_warnings/brush clauses in a new open residual entry "Served build on the event loop", graded S2), rewrite the GAPS3 H3 Tracked line to the Partly form with `commit pending` (DECISIONS A11; the merger's step k.3b writes the sha), replace the <!-- WP-31 H3 --> marker under "### Fixed in WP-31" with "The served page no longer ships Bokeh's MathJax component (WP-31, H3)". Commit on wp31-s55.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_served_resources.py test/test_csp.py test/test_serve_token.py -q passes; git log -1 --format=%s ends "(WP-31 H3)"; git log -1 --format=%B | grep -ci "claude\|anthropic" prints 0]]></verify>
  <done>H3's mathjax clause is closed and committed; the remainder is an open residual.</done>
</task>

<task type="auto" id="55-02">
  <name>Report the environment, deepen health, read the rc, commit H4</name>
  <files>test/test_served_env.py, dash_render.py, dash.ado</files>
  <action><![CDATA[Create test/test_served_env.py (H4 stubs) and add U55-2 to test_setup_*.cscript (the file holding the browser-launch cases; grep "_dash_open_browser" test/*.cscript); run the pytest file red, save <scratch>/55-02-failure.txt. Apply TR-55.2, TR-55.3, TR-55.4 and the copy-list entry for _dash_env_bundle_note; update function_test_map. Run test/test_served_env.py, test/test_server.py, test/test_server_rate_limit.py, test/test_help_claims_4.py -k Handoff, the setup cscript driver through scripts/stata_slot.sh. Close BUGS.md "Environment variables and /health", rewrite the GAPS3 H4 Tracked line to the Closed form with `commit pending` (A11), append the S55 H4 truth block (U55-5; A14: the row's closing task appends it) and run it through the driver, replace the <!-- WP-31 H4 --> marker (Requirements list: "dash serve refuses BOKEH_RESOURCES set to any mode but server or inline; BOKEH_MINIFIED and BOKEH_DEV are reported; /health reports sessions, versions and uptime; a failed browser launch is reported with its return code (WP-31, H4)"). Commit on wp31-s55.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_served_env.py test/test_server.py test/test_server_rate_limit.py -q passes; the cscript log shows U55-2 PASS; git log -1 --format=%s ends "(WP-31 H4)"]]></verify>
  <done>H4 is closed and committed.</done>
</task>

<task type="auto" id="55-03">
  <name>Prefix the Mata names, restore argv, clear the namespace, commit H7</name>
  <files>test/test_session_hygiene.py, dash_parse.mata, dash.ado</files>
  <action><![CDATA[Create test/test_session_hygiene.py (H7 stubs), run it red, save <scratch>/55-03-failure.txt. Apply TR-55.5 (rename the four functions everywhere: dash_parse.mata definitions, calls and header index; dash.ado _needed and the repair loop; test/program_coverage_map.py keys; every test/*.cscript and test/*.py that names them -- grep first, rename in place) and TR-55.6 (argv save/restore and the del/pop lines at :665-681, :6139, :10997 and the serve return). Add U55-1 (argv and namespace) to test_env_guards.cscript, U55-3 to test_program_coverage.cscript's PC-30 neighbourhood, U55-4 to test_json_escaping.cscript. Run test/test_session_hygiene.py, test/test_program_coverage_map.py, and the drivers for test_json_escaping, test_utf8_validation, test_parser, test_tokenizer, test_program_coverage and test_env_guards through scripts/stata_slot.sh (one slot each, sequentially). Close BUGS.md "Session hygiene", rewrite the GAPS3 H7 Tracked line to the Closed form with `commit pending` (A11), replace the <!-- WP-31 H7 --> marker ("dash leaves sys.argv and the Python session's namespace as it found them, and every Mata function is prefixed (WP-31, H7)"). Commit on wp31-s55 with one Flipped line per renamed map key.]]></action>
  <verify><![CDATA[grep -c "_json_escape\|_is_utf8\|_expand_plottype_str\|_first_comma_pos" dash_parse.mata dash.ado test/program_coverage_map.py | grep -v ":0$" | grep -vc "_dash_" prints 0; every cscript log ends PASS; python3 -m pytest test/test_session_hygiene.py test/test_program_coverage_map.py -q passes; git log -1 --format=%s ends "(WP-31 H7)"]]></verify>
  <done>H7 is closed and committed.</done>
</task>

<task type="auto" id="55-04">
  <name>Confirm the three closings and the help</name>
  <files>none</files>
  <action><![CDATA[Confirm, without committing, that the three commits exist on wp31-s55 in the order H3, H4, H7, that dash_serve.sthlp (or the serve section of dash.sthlp) names the /health fields, the BOKEH_RESOURCES refusal and the bundle note (added in 55-02's commit; if missing, amend is NOT allowed -- make a fourth commit "Document the served environment checks (WP-31 H4)" and report it), and that python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py test/test_fixtures_are_committed.py -q passes. Write the hand-back note listing the H3 residual.]]></action>
  <verify><![CDATA[git log --format=%s -3 prints the three subjects in reverse order; python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py -q passes]]></verify>
  <done>The three rows are closed on the branch with their documents in order.</done>
</task>

## Section completion criteria

- No `bokeh-mathjax` script in the served page; `BOKEH_RESOURCES=cdn` exits 2 with the sentence; `/health` has the D-55c keys; a non-zero browser rc is reported; dash_parse.mata has no unprefixed function; `sys.argv` and `__main__` are restored; three commits.

## Notes

- **Three cycles.** H4's tests are written on the tree after the H3 commit, H7's after H4's (BRIEF).
- **Security (rule 1).** `/health` adds load and version figures only -- no paths, no hostnames, no key; still rate-limited. The `BOKEH_RESOURCES` value is echoed through `_dash_display` (printable, 40 chars).
- **Copy lists (R2):** `_dash_env_bundle_note` after `_dash_reference_lines` (after batch 16-18 predecessors).
- **python_exec hazard:** running six cscripts in 55-03 -- one `scripts/stata_slot.sh` slot each, never concurrently from one task (project memory: many concurrent sessions can drop python_exec from stata19.rc).
- **Commit body forms:** `Regression: test/test_served_resources.py::TestNoMathjax::test_the_served_page_names_no_mathjax_script -- failed at 6370ca4 with AssertionError: bokeh-mathjax-3.x.min.js is listed`; `Flipped: test/test_program_coverage_map.py (key _json_escape) -- renamed _dash_json_escape because every library name is now prefixed`; `BUGS.md: "<title>" (closed)`; `GAPS3: H3 Tracked` / `H4 Tracked` / `H7 Tracked`.
- **Decisions for ratification:** H3's off-loop build left as a residual (D-55a); refuse-not-override for `BOKEH_RESOURCES`, report-only for `BOKEH_MINIFIED/DEV` (D-55b). **Decided:** `/health` omits `rows` (D-55c; A30, R4-23); the argv restore precedes every exit (D-55e; R4-24).
- **Tracked lines (A11):** every closing task writes `commit pending`; no amend anywhere. **A14:** one truth block (H4's, appended by 55-02); 55-01 appends none. **Files (A13):** `<files>` lists primary files; the tracking documents and flipped tests are implied.


## Addendum (17oct2026, DECISIONS D36): row G3c added to this section

**Gap.** BUGS.md "The strL binary check reads every observation one at a time" (found by WP-31 S43; graded S3: a time cost on large strL data, not a wrong picture).

**Requirement.** One Mata st_sview pass over the strL variables before the export, timed on 10^6 rows; failing tests first; close the BUGS entry, the GAPS3 G3c Tracked line (`commit pending`), the CHANGELOG `<!-- WP-31 G3c -->` marker in "Fixed in WP-31" and the WP31_OPEN line; one commit ending `(WP-31 G3c)`.


## Addendum (17oct2026, DECISIONS D36): row G3d added to this section

**Gap.** BUGS.md "Qualifier and working columns are generated in the user's data (r(900) possible at c(maxvar))" (found by WP-31 S43; graded S3: fails loudly at c(maxvar), never a wrong picture).

**Requirement.** Tempvars counted against c(maxvar) before any generate, refusing with dash's words before the user's data is touched; failing tests first; close the BUGS entry, the GAPS3 G3d Tracked line (`commit pending`), the CHANGELOG `<!-- WP-31 G3d -->` marker in "Fixed in WP-31" and the WP31_OPEN line; one commit ending `(WP-31 G3d)`.
