# Section 23: Served notes reach Stata (P1.26 part b, M6)

> Part of: WP-30 · Items: P1.26 part b (entry `P1.26b`) · Risk: yellow · Batch: 8 · Depends on: 06 · Blocks: 26, 46 · Tasks: 11, 1 commit · Case ids: NC-07..NC-10 (range NC-07..19)

## Review amendments

- Fixed (major, batch 8): S22 lands first and prints `(note:  dash: graph export writes …)` on every file-writing dash command while a Stata graph is in memory; NC-09/NC-10 draw `twoway …, nodraw` first and NC-09 requires no `(note:` line, so they would fail at G8 after the merge. NC-07..NC-10 now clear Stata's graphs (`quietly graph drop _all`) before their dash calls.
- Fixed (major): 23-11 checked G6 without any staging step; it now stages the 13 files of the completion criteria, then checks the staged list.
- Fixed (minor): the Resolution line is written with BUGS.md's two-space indent (`  - Resolution:`), as TR-01.10 item 1 gives it.
- Checked: anchors E2.1-E2.8 (dash_render.py :28349, :30447-30500, :30638-30645, :33133-33137, :33467-33479, :34101-34109, :33797-33817, :36410-36413, :36823-36892 with `launch`, :37206, :37338-37356, :37626-37677, :4333-4337) match `c96facd`; M6 (an emptied own-qualifier layer silent in both modes, the estimator note kept), IR-10 (trial for `dash build, server` only) and A83/A85 obeyed; R8's own-if CORPUS restoration is this section's, as index R8 says.
- Checked (batch 8): S23 is the batch's only `_make_figure_body`/`_generate_app_source` editor, edits no dash.ado line, and its `_glyph_layer_lines` additions sit at R2's S23 anchor; S24 (methods only) adds no copy-list entry.
- Checked (rule 1): the trial compiles only dash's generated source in a `_dash_trial_app` namespace under `patch_curdoc`, catches every exception inside that block, and never installs the note hook in Stata's process; relayed lines are redacted before printing and bounded.
- Rejected: "the trial should run for `dash serve` too" (IR-10: the child's warm-up is that trial, S46).
- (cross-file pass) 23-11 verify: the prose "the `WP30_OPEN` block no longer holds" became the runnable key-deletion check `grep -c '^    "P1.26b": "' test/test_tracking_documents.py` prints 0 (S01 TR-01.10.1).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md P1.26 (lines 147-153) says that "`dash build, server` reports no option or empty-layer notes" and that "The served child's stderr never reaches Stata", and its WP-29 note (S12) adds: "the served app still prints no empty-layer note where the saved page notes "drew nothing" (bar/rbar/rarea with its own if keeping no row; CORPUS entries dropped by S12)". GAPS2 F5 (GAPS2.md:1341) records the same as F5a (the build reports 0 notes) and F5b (the child's output bypasses Stata); F5c (URL and banner not flushed) is closed at `c96facd` (research p1-26 §2, m2.log).

Measured at `c96facd` (StataNow 19.5 console, probe `s23probe.do` quoted under Evidence E1):
- One registration, `dash (scatter mpg weight, mcolor(notacolor) msymbol(weird)) (lfit mpg weight if price > 20000) (bar mpg weight if price > 20000) (line mpg weight if price > 20000), name(nc07)`: `dash build, saving(…html)` prints five notes (mcolor, msymbol, `(note:  regress could not fit model)`, and "drew nothing from 74 observations." for the bar and the line); `dash build, saving(…py) replace server` prints none. Both rc 0.
- `dash serve` on the same kind of graph logs the banner, the "server answers" line and the link path, and none of the notes. They go to the child's stderr as raw `…/b2.py:17447: UserWarning: dash: mcolor(notacolor) …` lines and a source line each, which the launcher keeps only in a 20-line deque quoted when a launch fails (research m2, `app.err`).
- `twoway (scatter mpg weight) (<t> … if price > 20000), nodraw` is rc 0 and prints nothing for all 18 types measured (line connected area spike dropline bar scatter rbar rarea rcap rline rscatter rconnected rspike pcspike histogram kdensity lowess). dash's saved page notes "drew nothing" for 11 of them (line area spike dropline rcap rline rscatter pcspike bar rbar rarea) and the served app for none (research p3). Only `lfit` gets twoway's `(note:  regress could not fit model)`.

**After this section.** `dash build, server` prints exactly the notes `dash build` prints for the same graphs, in S06's `(note:  dash: …)` form, from one trial render of the app it just wrote (A83, IR-10). A trial that fails is one note, and the app is still written (A85). `dash serve` relays the served app's own notes, ERROR lines, uncaught-request lines and tracebacks to Stata while it serves (A86): redacted, each note once per server and never one its build already printed, at most 100 notes and 200 other lines, with no access-log line. In this batch the app's notes arrive when the first session draws the dashboard; S46's warm-up later moves that render before the server listens (IR-10). The app run by itself (`python app.py`, `bokeh serve`, `dash serve`'s child) prints each distinct note once per process as `(note:  dash: …)` on its stderr, whatever `PYTHONWARNINGS` says, through a process-wide hook that an importing process (a test, a user's script, the build's trial) never gets. Under M6, a layer whose own `if`/`in` keeps no row is drawn in silence in both modes, as twoway draws it; the estimator note twoway prints for such an `lfit` stays, in both modes.

**Why one section.** F5a, F5b and the S12 note are one defect: a note decided while the served app draws never reaches the Stata session that asked for it. The trial (F5a), the app's hook (what the child prints) and the launcher's relay (F5b) are three ends of one pipe, and the M6 rule decides which empty-layer note travels through it at all. M6 lands here because the S12 note is only a "served is silent" defect until the saved side is made silent too (D1 (a), P1.26.1), and because the parity corpus can only take back its dropped own-if entries once both modes agree (R8).

**Test order and commit rule (rule 7, A141).** One cycle, one commit `(WP-30 P1.26b)`.
- 23-01 to 23-03 write every regression test, run them against the unmodified worktree (the batch-8 base), and save `<scratch>/23-P1.26b-failure.txt`. They never commit.
- 23-04 to 23-09 make the fix (M6, the trial, the hook, the relay, the link note), flip the two pinned tests with `Flipped:` lines, add the map entries and update the help.
- 23-10 certifies (changed files, G3, G4, the registries, both cscripts through the driver).
- 23-11 closes the BUGS.md entry in place, deletes its `WP30_OPEN` key, replaces both CHANGELOG markers in place, runs the full suite once through the queue and commits.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — a CRITICAL figure body, two HIGH generators, and dash's own app run inside Stata's process

**Why.**
- `DashRenderer._make_figure_body` is CRITICAL (GitNexus: 4 upstream, `_build_sources_and_figures`, `_make_figure`, `render` and the regen scripts). The edit is one keyword argument on the `_dash_note_empty_layer` call plus the count it passes (two lines in the own-qualifier branch).
- `ServerAppBuilder._generate_app_source` (HIGH, 5) and `ServerAppBuilder._glyph_layer_lines` (HIGH, 4) change the generated app: the `_DASH_TRIAL` flag, its guards on the logger filter, the fallback note and the hook's install line, three copied names, and the served `_dash_note_empty_layer` call.
- The trial executes the whole generated app (`exec` of dash's own source) inside Stata's Python. Done carelessly it would attach roots to the global `curdoc()`, add filters to Tornado's loggers, leave a process-wide `showwarning` in the user's session (research critic, item 1, measured with `hookprobe.py`), or start a server.
- `dash build, server` takes one more render: 0.19 s per corpus case on average (prototype, E5), up to a saved build's own render time at large N (~28 s for lowess at 100k; ratification item 14). It also imports `bokeh.server.server` and `tornado.web` into Stata's Python (critic item 9).
- The relay decides which child lines reach the user's log, and the child's stderr carries the key (a session error's `HTTPServerRequest(… uri='/?token=…')` line, E3).
- A process-wide hook in a process the app does not own would change how a test or a user's script sees warnings.

**Risk factors.**
1. A wrong layer-row count on the saved side (a linked or by() graph) would silence a note the served app prints, or the reverse.
2. The trial's own notes could double the planners' (`_plan_graph_notes`, `_plan_by_groups`) or the scheme note.
3. A user's session filter of "error" could turn a non-dash warning inside the trial into a false "could not draw" note.
4. A relayed traceback could also appear in the failure message (critic item 6), or a pre-ready traceback could stop being quoted, breaking the "port is in use" detection.
5. A refused-request flood (P2.38) could crowd out notes.
6. A note relayed through `errprintln` could carry a `{stata …}` directive.

**Mitigation.**
1. The saved count is taken after the facet/linked intersection, which is exactly the served `len(g_df)` (E2.3); the 13 restored own-if CORPUS entries and `TestTheServedBuildNamesTheSavedNotes` (272 cases) pin it.
2. The trial re-issues only the notes its one render raises; the app suppresses the planners' notes in sessions (`warn=False`), and the module-level scheme-fallback warning is not raised under `_DASH_TRIAL`. The prototype matched the saved build's warnings exactly on all 259 corpus cases (E5).
3. The trial records under `simplefilter("always")` inside `catch_warnings(record=True)`, so no warning is escalated and nothing is de-duplicated by the registry.
4. Each stderr line is either relayed or kept for the tail, never both; ERROR lines and tracebacks are relayed only once `/health` has answered, so a launch failure's tail is today's.
5. Notes have their own budget (100 distinct), separate from the 200 lines other output shares.
6. Every relayed line passes `_clean` and `_dash_redact_query(…, token)`; notes then pass `_dash_emit_note`, which SMCL-escapes and bounds them (S06); other lines are `print`ed, which Stata shows literally (critic, c2.smcl).
- The hook installs only when the app module is `__main__` or `bokeh_app_*` and `_DASH_TRIAL` is false; a test asserts an imported app and a trial leave `warnings.showwarning`, `warnings.filters`, `curdoc().roots`, Tornado's filters and `sys.modules` as they were.
- 8.0 runs impact at the batch base; the executor warns before the `_make_figure_body` edit (CRITICAL) and before the `_generate_app_source`/`_glyph_layer_lines` edits (HIGH) and records the approval.

## Dependencies

- **Depends on: 06** (batch 2). S06 provides `_dash_smcl_escape(text, braces=True)`, `_dash_emit_note(text, sfi=None)` and `_dash_note_scope(sfi=None)`, and wraps the `__main__` call of `main()` in `with _dash_note_scope() as _dash_said:` (S06 TR-06.1-06.4). S23 copies the first two into the app, calls the emitter from the launcher and the hook, and passes `said=_dash_said`. S06's hand-offs to S23 (S06 Notes) are taken in full: the copy-list names, `said=`, the estimator note kept for an own-if `lfit`, the launcher's link-file note and help lines 1584 and 1622.
- **S01** opened the BUGS.md entry `P1.26b` ("dash build, server and dash serve report no option or empty-layer notes, and the served child's stderr never reaches Stata"), its `WP30_OPEN` key, the markers `<!-- WP-30 P1.26b -->` in `### Changed behaviour (may need your do-files changed)` and `### Fixed in WP-30`, the stub block `* ==== S23 P1.26b: Served notes reach Stata ====` in `test/test_wp30_truth.cscript`, and the anchor `# WP-30 S23 (P1.26b): Served notes reach Stata (P1.26 part b, M6)` at the end of `FUNCTIONS` in `test/function_test_map.py` (A148).
- **Ratification.** Items 13 (A82, A84: the note's form, S06's) and 14 (A83: the trial for `dash build, server`, the child's render for `dash serve`) bind this section. It is written on both as stated.
- **Blocks: 26, 46.**
  - S26 (batch 9) adds `map_function`'s fallback mark, read by `_dash_note_empty_layer`, and its note reaches Stata through this section's trial and relay. The function branch of `_dash_note_empty_layer` is not changed here.
  - S46 (batch 16) adds the warm-up, which is `dash serve`'s trial (P1.31.5, IR-10), reuses `_DASH_TRIAL` to skip its memo (P1.31.8), and adds the launcher flags to `_dash_launch_app`.
- **Parallel batch 8** (S22, S23, S24; merge order S22, S23, S24). S23 is the batch's `_generate_app_source` and `_make_figure_body` editor (A139, R12). No function is shared with a partner (Boundaries).

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines; dash.sthlp 3,822). Sixteen sections land before batch 8 and several edit dash_render.py (S04, S06, S08, S09, S13-S21), so every number drifts. Find each site by the quoted text; record the shift in the task's output.

### E1. Measured at `c96facd`

Probe `s23probe.do` (03oct2026), run as `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s23/st <scratch>/s23/st/s23probe.do`, opening with `adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"`, `global dash_nobrowser 1`, `set graphics off`, `set linesize 255`, `sysuse auto, clear`:

```
TW line .. TW lowess (18 types, `twoway (scatter mpg weight) (<t> <vars> if price > 20000), nodraw`)
    -> every TWRC 0, no line printed between TW and TWRC
TW lfit
(note:  regress could not fit model)
TWRC lfit 0
DASH SAVED BUILD   (dash build, saving("s23_saved.html") replace)
…/dash_render.py:8679: UserWarning: dash: mcolor(notacolor) is not a recognised colour; using the scheme's default.
…/dash_render.py:9847: UserWarning: dash: msymbol(weird) is not a recognised marker symbol; using the scheme's default.
…/dash_render.py:30643: UserWarning: dash: graph 'nc07' plot 2 (lfit): (note:  regress could not fit model)
…/dash_render.py:28408: UserWarning: dash: graph 'nc07' plot 3 (bar) drew nothing from 74 observations.
…/dash_render.py:28408: UserWarning: dash: graph 'nc07' plot 4 (line) drew nothing from 74 observations.
DASHRC saved 0
DASH SERVER BUILD  (dash build, saving("s23_app.py") replace server)
  Access:    the app makes a new key for each launch …       <- the only output; no note
DASHRC server 0
```

At the batch-8 base the five saved notes read `(note:  dash: …)` (S06), and the two "drew nothing" lines are still there; the server build still prints none.

### E2. The code

**E2.1 The one empty-layer rule** (dash_render.py:28349-28409, `_dash_note_empty_layer`, LOW: 3 upstream; the served call is a string in `_generate_app_source`, which the graph does not see):

```python
28349  def _dash_note_empty_layer(gname, index, ptype, rows, renderers):
…
28373      pt = str(ptype or "").lower()
28374      if pt in _DASH_LITERAL_TYPES and pt != "function":
28375          return
28376      if _dash_layer_drew_anything(renderers):
28377          return
…
28385      if unfit in ("regress", "fracpoly"):          # twoway's estimator note, kept
…
28405      if pt == "function":
28406          _dash_report_empty_layer(gname, index, ptype)
28407      elif rows:
28408          _dash_report_empty_layer(gname, index, ptype, rows)
```

Its docstring already states M6's rule ("an `if` qualifier that selects none is the user's doing, not a broken layer"); the two callers pass different `rows`, which is the defect.

**E2.2 The saved caller** (`DashRenderer._make_figure_body`, CRITICAL). The layer's own qualifier becomes a `CDSView` over the graph's source, intersected with a facet or linked view (dash_render.py:30447-30500):

```python
30456              source_for_plot = source
30457              _plot_view = facet_view
…
30488                      _wanted = set(self._row_ids_kept(_pdf))
30489                      _mask = [bool(r in _wanted) for r in _ids]
…
30496                      if _prev_bools is not None and len(_prev_bools) == len(_mask):
30497                          _mask = [bool(a and b)
30498                                   for a, b in zip(_prev_bools, _mask)]
30499                      _pf = BooleanFilter(booleans=_mask)
30500                      _plot_view = CDSView(filter=_pf)
```

and the report passes the whole source's length (dash_render.py:30638-30645):

```python
30638              try:
30639                  _rows_here = len(source_for_plot.data.get(
30640                      next(iter(source_for_plot.data), ""), []))
30641              except (AttributeError, TypeError, StopIteration):
30642                  _rows_here = 0
30643              _dash_note_empty_layer(
30644                  graph_opts.get("name", "") or graph_spec.get("name", ""),
30645                  pi + 1, ptype, _rows_here, _layer_renderers)
```

`_dash_layer_drew_anything` reads source data, not the view, so a view-drawn type (scatter, connected) counts as drawn and is silent while a source-filtered type (line, bar) is noted (research p4).

**E2.3 The served caller** (generated text inside `_generate_app_source`, dash_render.py:35337-35345 and 35405-35406):

```python
35337              '            if ptype not in _DASH_LITERAL_TYPES and (',
35338              '                    (_p_if and _p_if != _g_if) or (_p_in and _p_in != _g_in)',
35339              '                    or (_p_qc and _p_qc != _g_qc)):',
35340              '                g_df = _dash_layer_frame(',
35341              "                    df, _g_df_graph, _p_if, _p_in,",
…
35345              '                g_df = _g_df_graph',
…
35405              "            _dash_note_empty_layer(gname, pi + 1, ptype, len(g_df),",
35406              "                                   list(fig.renderers[_r_before:]))",
```

`_g_df_graph` is the figure's frame (`"        _g_df_graph = g_df"`, :35126): the graph's rows, or one by() panel's rows, since `_dash_figure_for` is called once per panel (:35562, :35584, :35646). So the served layer count is "the figure's rows that the layer's own qualifier keeps", which is the saved `_mask` after the intersection at :30496-30498, not before it.

**E2.4 The served copy list** (`_glyph_layer_lines`, functions tuple; the anchor of R2 row S23, dash_render.py:33133-33137):

```python
33133                           # A layer that drew nothing has to say so in BOTH
33134                           # modes, in the same words.
33135                           "_dash_layer_drew_anything",
33136                           "_dash_report_empty_layer",
33137                           "_dash_note_empty_layer",
```

The copy loop skips a missing name silently (`getattr(_mod, _fn_name, None)` then `continue`, :33428-33430), so S01's `test_every_listed_name_exists` guards a misspelling.

**E2.5 The generated module's side effects.** The scheme-fallback warning closes `_glyph_layer_lines`' output (dash_render.py:33467-33479):

```python
33467              "if _DASH_SCHEME_IS_FALLBACK:",
33468              "    warnings.warn(",
33469              "        \"dash: this app was built where no .scheme file \"",
…
33478              "_DASH_SCHEME = _dash_build_scheme()",
33479              "_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)",
```

and `_generate_app_source` ends the module body with (dash_render.py:36406-36414):

```python
36406              "# WP-29 P0.12a: Tornado's logs never carry a query string (the",
…
36410              "_dash_install_access_log_redaction()",
36411              "",
36412              "if __name__ != '__main__':",
36413              "    make_document(curdoc())",
```

The attach line is pinned by text: 17 literal copies of `"if __name__ != '__main__':\n    make_document(curdoc())"` in 14 test files (`_ATTACH`, `_CURDOC_ATTACH` or a local `attach` in `test_adversarial_matrix`, `test_date_range`, `test_export`, `test_help_claims_2`, `test_help_claims_8`, `test_function_audit`, `test_kpi_security`, `test_qualifier_columns`, `test_qualifier_logic`, `test_scheme_fallback_provenance`, `test_scheme_consumption`, `test_server`, `test_string_value_export`, `test_textbox_multiline`) assert it is present and replace it to exec an app without attaching. Prototype 2 (E5) changed it to `if __name__ != '__main__' and not _DASH_TRIAL:` and turned `212 failed, 11 errors` red over the 15 files it ran, every one on "the generated app's curdoc attach moved". So the attach is never edited; the trial draws through it instead (TR-23.3).

The header's imports end at (dash_render.py:34101-34109):

```python
34101              "from bokeh.io import curdoc",
34102              "from bokeh.plotting import figure as bokeh_figure",
34103              "from bokeh.server.server import Server",
…
34108              "from bokeh.models import Button as _DashButton, CustomJS as _DashCustomJS",
34109              "",
```

**E2.6 The build** (`ServerAppBuilder.build`, dash_render.py:33698-33814; LOW, 10 upstream, but 211 `.build(` calls in `test/`). The planners raise their notes at build, then the source is generated and the caches freed (dash_render.py:33797-33817):

```python
33797          try:
…
33802              self._plan_by_groups()
33803              self._plan_graph_notes()
33804              source = self._generate_app_source(port)
33805          finally:
…
33808              self._data_cache = None
33809              self._frame_cache = None
33810          if private:
33811              _dash_private_clear_name(output_path)
33812              st = _dash_private_write(output_path, source, exclusive=True)
33813              return _DashWrittenApp(
33814                  st, hashlib.sha256(source.encode("utf-8")).hexdigest())
33815          with open(output_path, "w", encoding="utf-8") as f:
33816              f.write(source)
33817          return None
```

`main()`'s server route (dash_render.py:36883-36892) builds with `private=True` on both routes; `launch` is true only for `dash serve` (`_launching = args.mode == "server" and args.launch`, :37626):

```python
36890          builder = ServerAppBuilder(master_spec_path, data_json_path)
36891          written = builder.build(output_path, port=_dash_port_value(port),
36892                                  private=True)
```

**E2.7 The launcher** (`_dash_launch_app`, dash_render.py:37206; LOW, 7). Both pipes are read by daemon threads; stdout is printed by the main thread, stderr only kept (dash_render.py:37338-37356):

```python
37338      # One structure per pipe: stdout lines go to the queue the main thread
37339      # prints from (under the bound below); stderr lines go to the deque
37340      # the failure message quotes (its last 20 lines).  Nothing is tagged
37341      # into the other's structure.
37342      _out_q = queue.Queue()
37343      _err_dq = collections.deque(maxlen=20)
…
37352      _t_out = threading.Thread(target=_pump, args=(proc.stdout, _out_q.put),
37353                                daemon=True)
37354      _t_err = threading.Thread(target=_pump,
37355                                args=(proc.stderr, _err_dq.append),
37356                                daemon=True)
```

and quoted only in a failure (the hand-over tail at :37516, and dash_render.py:37534-37537):

```python
37534      _tail = _dash_redact_query(_clean("".join(_err_dq)), token)
37535      if any(s in _tail for s in
37536            ("Address already in use", "EADDRINUSE", "already in use")):
37537          _reason = "no server started on port %d: the port is in use" % port
```

The `__main__` block calls `main()` at :37628 and launches after it returns (dash_render.py:37674-37677), outside S06's scope:

```python
37674              _dash_launch_app(args.output, args.port, args.timeout,
37675                               args.no_browser, expect=_written,
37676                               link_dir=_dash_private_run_of(args.output),
37677                               erase_app_when_ready=_erase)
```

**E2.8 The link-file note** (`_dash_private_page`, dash_render.py:4333-4337; LOW, 6; copied into the app at :33423):

```python
4333          if loose:
4334              print("dash: note: " + p + " holds the dashboard's link, but "
4335                    "its disk keeps no file permissions, so other accounts of "
4336                    "this machine may read it; set TMPDIR to a folder on a "
4337                    "disk that keeps them.", file=out, flush=True)
```

`out` is used for nothing else in the function (:4305-4306 set it to stdout when None).

### E3. What the child's stderr carries (probe `probe_session_error.py`, 03oct2026)

The research app `b2.py` (built at `c96facd`) run by hand, one session opened through its link and one keyless request:

```
default filters:
…/b2.py:8888: UserWarning: dash: xlabel() sub-option(s) not implemented and ignored: nosuchsub
  _dash_report_suboptions(ax_key, spec.get("unsupported", []),
…/b2.py:17447: UserWarning: dash: mcolor(notacolor) is not a recognised colour; …
…/b2.py:24949: UserWarning: dash: graph 'g1' plot 2 (lfit): (note:  regress could not fit model)
403 GET /?<query redacted> (127.0.0.1) 0.49ms          <- tornado.access, no level prefix
PYTHONWARNINGS=error::UserWarning (the session fails, HTTP 500):
Uncaught exception GET /?<query redacted> (127.0.0.1)
HTTPServerRequest(protocol='http', host='127.0.0.1:5961', method='GET', uri='/?token=sdAm3ryX…', …)
Traceback (most recent call last):
  File "…/tornado/web.py", line 1880, in _execute
…
UserWarning: dash: xlabel() sub-option(s) not implemented and ignored: nosuchsub
500 GET /?<query redacted> (127.0.0.1) 19.59ms
```

Logger formats under bokeh 3.9.0 (Python 3.14.5): the `bokeh` logger has a `StreamHandler` with `%(levelname)s:%(name)s:%(message)s`; Tornado's loggers have no handler and reach Python's last-resort handler, which prints the message alone (no level). So an ERROR is either `ERROR:bokeh…:` or an unprefixed `Uncaught exception …` followed by a traceback. The `HTTPServerRequest(…)` line holds the key in `uri='/?token=…'`; `_dash_redact_query` turns it into `uri='/?<query redacted> version=…` (checked), and the launcher also replaces the key itself with `<key>`.

### E4. twoway truth (research m1/m3/m4, re-run in E1)

- A layer whose own `if` keeps no row is drawn in silence, rc 0, for all 18 types; `lpoly` is refused "no observations" r(2000) and `mspline`/`mband` "bands must be between 1 and 200" r(198), which dash draws (P2.37 territory, not this section's).
- `lfit` on no observations prints `(note:  regress could not fit model)`. M6 silences only the "drew nothing" note; the estimator note is twoway's own and stays in both modes (S06 hand-off; NC-02 pins it on the saved side).

### E5. Prototypes (scratch, outside git; never committed)

1. **Trial over the parity corpus** (`proto_trial.py`): for each of the 259 CORPUS cases, the saved `render()` warnings against `ServerAppBuilder.build()` warnings, and against `build()` plus a trial of the generated source (exec under `_DASH_TRIAL = True` in a `_dash_trial_app` namespace, `catch_warnings(record=True)` with `simplefilter("always")`, module-phase warnings dropped, then `make_document(Document())`):

   ```
   cases 259 head build!=saved 10 proto build+trial!=saved 0
   module-level warnings seen []
   curdoc roots added 0
   build s 45.4 trial s 49.0
   showwarning restored True
   ```

2. **M6 alone** (the TR-23.1 edit in an exported copy of `c96facd`): the 25 test files that hold "drew nothing" (all but `test_help_examples.py`), with `test_emptied_layer_style.py` and `test_server.py`: `8913 passed, 50 warnings in 410.36s`. No pinned pytest node asserts the own-if "drew nothing" note; the cscript pins of that text (`test_conformance.cscript` C-03's `ctl2`, `test_parser.cscript` P1A-73) are all-missing layers with no own qualifier (A11, BUGS.md:2559), which M6 does not touch (`layer_rows` is None there).
3. **Trial, hook and guards, first form** (an explicit `make_document(Document())` and the attach changed to `… and not _DASH_TRIAL`, with S06 stand-ins): over the 15 test files most likely to see it, `212 failed, 5485 passed, 11 errors`, every failure and error on "the generated app's curdoc attach moved" (E2.5). Hence TR-23.2 keeps the attach and TR-23.3 renders through it.
4. **Trial, hook and guards, final form**, 5. **the relay** and 6. **end to end**: counts and output under E6.

### E6. Tests that pin today's behaviour (flip in place, never delete; 23-01 re-measures)

Measured on the prototypes of E5 (an exported `c96facd` with S06's emitter and escape as stand-ins), then re-measured by 23-08 at the batch-8 base, where S06's real channel is in place.

**Flipped in 23-08 (each with a `Flipped:` line):**

| Node (at `c96facd`) | Pins today | Becomes | Why the old expectation was wrong |
|---|---|---|---|
| `test/test_serve_token.py::TestTheTokenHelpers::test_a_page_the_disk_will_not_keep_private_is_written_with_a_note` (:703-726) | one line on `out` starting `dash: note: ` | `out.getvalue() == ""`; `capsys.readouterr().err` holds one line starting `(note:  dash: `, holding the path and `TMPDIR`, not the key | the link-file note is a note, and S06's channel prints notes in twoway's form (S06 hand-off, TR-23.10) |
| `test/test_serve_token.py::TestTheLauncherPassesTheToken::test_a_link_no_folder_can_keep_private_is_written_with_a_note` (:1615-1648) | one stdout line starting `dash: note: ` | one stderr line starting `(note:  dash: `, holding the path, not the key or `?token=` | the same note, reached through `_dash_write_link` |

**Pinned, and kept by the design (no flip):**
- The 17 attach literals of E2.5: the attach is never edited (TR-23.2).
- `test/test_serve_lifecycle.py::TestTheEraseRule::test_outside_a_private_run_folder_nothing_is_erased` (:636-637) reads `erase_app_when_ready=_erase)` from dash_render.py's source. Prototype 5 appended `said=` after it and turned this node red; TR-23.9 therefore puts `said=_dash_said,` before it.
- The launcher's failure tail: `TestTheLauncherRefusesAHeldPort::test_the_childs_bind_failure_is_reported_with_its_stderr` ("Address already in use" from a pre-ready traceback), `TestTheLauncherReportsTheExitStatus` (both nodes), `TestTheLauncherForwardsBoundedStdout::test_lines_are_filtered_cut_and_capped`, and `test/test_serve_token.py::TestTheLauncherPassesTheToken::test_the_stderr_tail_and_forwarded_lines_are_redacted` ("boom" before ready stays in the tail). All stay green unchanged (prototype 5).
- `test/test_mode_parity.py`'s `_served`, `test_same_warnings`, `_MUST_WARN` and `ALLOWED`: unchanged; `_served` builds without the trial, so its sum of build and session notes is still today's.
- `test/test_immediate_dashboards.py::TestTheReportHelpers::test_a_data_layer_is_reported_only_when_there_are_rows`: no `layer_rows`, so the old rule.
- S06's `test/test_note_channel.py::TestTheRendererEntryPoint` runs `--mode server` through the `__main__` block, so the trial runs inside it; its tests are relational (filtered run against the control) and must stay green (23-05 runs them).

**Prototype counts.**
- Prototype 4 (final form of TR-23.1-23.6 with S06 stand-ins; 17 files: `test_help_claims_1/2/4/5`, `test_render_cli_port`, `test_private_files`, `test_resource_limits`, `test_serve_lifecycle`, `test_serve_launcher`, `test_server_build_returns`, `test_scheme_fallback_provenance`, `test_serve_token`, `test_mode_parity` with the 13 restored entries and `TestTheServedBuildNamesTheSavedNotes`, `test_statistical_helpers`, `test_immediate_dashboards`, `test_csp`, `test_bokeh_document_hygiene`): `1 failed, 5775 passed in 293.22s`. The failure was a port collision, `Cannot start Bokeh server, port 63156 is already in use`, in `test_serve_token.py::TestBokehServeAlwaysHasAKey::test_a_websocket_first_session_leaves_the_link_to_the_first_page` (E6's flaky class). The run held 168 own-if parity nodes (14 entries x 12 comparisons) and 272 trial-parity nodes, all green.
- Prototype 5 (the relay of TR-23.7-23.10 added; `test_serve_launcher`, `test_serve_token`, `test_serve_lifecycle`, `test_private_files`, `test_help_claims_4/5`, `test_statistical_helpers`, `test_resource_limits`): `3 failed, 859 passed` = the two flips above and the erase-literal node.
- Prototype 6 (end to end, `relay_e2e.py`: build with the trial off, `_dash_launch_app` with `said={"dash: note: something the build said."}`, a thread opening two sessions with the key and one without, then SIGTERM): `rc=0`, the stdout lines unchanged (banner, ready line, link path), and on stderr, once each over two sessions:

  ```
  (note:  dash: mcolor(notacolor) is not a recognised colour; using the scheme's default.)
  (note:  dash: msymbol(weird) is not a recognised marker symbol; using the scheme's default.)
  dash: graph 'g1' plot 2 (lfit): (note:  regress could not fit model)
  ```

  No `403 GET` line, no `UserWarning`, no path, and no "drew nothing" for the own-if `bar` (M6). Outside Stata the stand-in emitter wrote to stderr; inside Stata S06's emitter uses `errprintln`.

### E7. Blast radius (GitNexus, main checkout, index at `c96facd`)

| Symbol | Risk (upstream) | Edit |
|---|---|---|
| `DashRenderer._make_figure_body` | **CRITICAL** (4: `_build_sources_and_figures`, `_make_figure`, `render`, regen scripts) | one keyword argument and the count it passes (TR-23.1) |
| `ServerAppBuilder._generate_app_source` | **HIGH** (5: `build`, `main`, `sample_app_source`) | `_DASH_TRIAL`, two guards, the served empty-layer call |
| `ServerAppBuilder._glyph_layer_lines` | **HIGH** (4) | three copied names; the hook's install line in its tail |
| `ServerAppBuilder.build` | LOW (10; the name is ambiguous, resolve with `file_path: dash_render.py`) | `trial=` keyword |
| `main` (dash_render.py) | LOW (7; ambiguous, 14 matches) | passes `trial=not launch` |
| `_dash_launch_app` | LOW (7; index 8.0 expected HIGH: record the measured value) | stderr relay, `said=` |
| `_dash_private_page` | LOW (6) | the note through the emitter |
| `_dash_note_empty_layer` | LOW (3) | `layer_rows=None` |
| `__main__` block | not a graph symbol | `said=_dash_said` |
| New: `_dash_trial_render`, `_dash_app_note_hook`, `_dash_relay_kind` | — | — |
| Not edited: `_dash_layer_drew_anything` (D1 (b) not taken), `_dash_warn_once`, `_dash_style_note`, `_dash_reset_notes`, `_plan_graph_notes`, `_plan_by_groups`, `_dash_emit_note`, `_dash_smcl_escape`, `_dash_note_scope` | | |

## User stories

- **US-23.1** As a dashboard publisher who runs `dash build, server`, I want the notes the saved build would print, so that I learn at build time what the app I hand on draws differently.
- **US-23.2** As a dashboard publisher who runs `dash serve`, I want the served app's notes, errors and tracebacks in my Results window and log, each note once and the dashboard's key never shown, so that a problem in a session is not invisible.
- **US-23.3** As a twoway user, I want a layer whose own `if` or `in` keeps no observation drawn in silence in both modes, as twoway draws it, so that a qualifier I chose does not produce a warning.
- **US-23.4** As someone who runs `python app.py` or `bokeh serve app.py`, I want each note once per process in twoway's `(note: …)` form, whatever `PYTHONWARNINGS` says, so that a filter cannot break a session and my terminal is not full of Python paths.
- **US-23.5** As a dashboard publisher, I want `dash build, server` to say so when the app it wrote cannot draw my dashboard, so that I do not hand on an app that fails for every reader.

## Business requirements

- **BR-23.1** `dash build, server` prints the same note lines as `dash build` for the same registration (an option drawn differently, twoway's estimator note, a by() sub-option, an axis-2 option), each once, in S06's form and visibility.
- **BR-23.2** When the app cannot draw the dashboard, `dash build, server` prints one note naming the error's kind and message, writes the app, and returns 0 (A85).
- **BR-23.3** While `dash serve` serves, each note the app's sessions raise is printed once per server, never one the command's build already printed; ERROR lines, uncaught-request lines and tracebacks are printed once the server answers; at most 100 notes and 200 other lines are printed; no access-log line is printed; no printed line holds a query string or the key.
- **BR-23.4** A launch that fails reports today's reason and quotes the child's last stderr lines that were not already printed, at most 20 lines and 4,096 characters.
- **BR-23.5** The app, run on its own, prints each distinct note once per process on its standard error as `(note:  dash: …)` (or in twoway's own words for the two text-class notes), never `UserWarning` or a path, and no warnings filter makes a session fail on a note.
- **BR-23.6** A layer whose own `if`/`in` keeps no row of its figure is drawn with no note in either mode, before and after a filter move; an `lfit` (or `qfit`, `fpfit` and their CIs) on no observation still gets twoway's estimator note in both modes.
- **BR-23.7** The check `dash build, server` makes leaves Stata's Python as it found it: its warnings filters and `showwarning`, the global Bokeh document, Tornado's loggers, `sys.modules` (no note hook), and no server started.
- **BR-23.8** The help states what `dash build, server`, `dash serve`, `python app.py` and `bokeh serve` print, and that an emptied own-qualifier layer is silent.

## Technical requirements

- **TR-23.1 M6, one rule in both modes** (P1.26.1, D1 (a)).
  - `_dash_note_empty_layer(gname, index, ptype, rows, renderers, layer_rows=None)`. Docstring gains: "*layer_rows*: the rows of the figure the layer's own `if`/`in` keeps, or None when it has none; 0 is drawn in silence, as twoway draws it (M6)." The last branch becomes `elif rows and layer_rows != 0:`. Nothing else changes: the literal-type return, `_dash_layer_drew_anything`, the estimator branch (`unfit`, kept whatever `layer_rows`), `_mark_silent`, and the function branch (which S26 extends) keep their order.
  - Saved (`_make_figure_body`, **CRITICAL: warn and record before editing**): after `_plot_view = facet_view` (:30457) add `_layer_rows = None`; directly before `_pf = BooleanFilter(booleans=_mask)` (:30499), after the intersection, add `_layer_rows = int(sum(_mask))`; the call at :30643-30645 gains `layer_rows=_layer_rows` as its last argument. The rows and the renderers it passes are unchanged. No other line of `_make_figure_body` changes.
  - Served (`_generate_app_source`, :35405-35406): the call becomes `_dash_note_empty_layer(gname, pi + 1, ptype, len(_g_df_graph),` / `list(fig.renderers[_r_before:]),` / `layer_rows=len(g_df))`. A layer without its own qualifier has `g_df is _g_df_graph`, so `layer_rows == rows` and nothing changes for it; the "from N observations" count now names the figure's rows, as the saved page names them.
  - After a filter move neither mode raises the note: the saved page moves in JavaScript, and the served redraw (`_dash_redraw_for`) does not call `_dash_note_empty_layer`. No JS twin exists or is needed.
- **TR-23.2 `_DASH_TRIAL` in the generated app** (`_generate_app_source` and the tail of `_glyph_layer_lines`).
  - In the header, after `"from bokeh.models import Button as _DashButton, CustomJS as _DashCustomJS",` and its `""` (:34108-34109), insert a three-line comment ("True only when ServerAppBuilder.build(trial=True) runs this module in the building process to hear its notes (WP-30 P1.26b); the app then touches no logger, raises no fallback note and installs no note hook, and its one drawing goes to the document the trial patched in.") and `"_DASH_TRIAL = bool(globals().get('_DASH_TRIAL', False))",` then `""`.
  - At the tail (:36410): `_dash_install_access_log_redaction()` becomes `if not _DASH_TRIAL:` / `    _dash_install_access_log_redaction()`.
  - The attach `if __name__ != '__main__':` / `    make_document(curdoc())` (:36412-36413) is **not changed** (E2.5: 17 test pins). Under the trial it is the trial's one render, into the document `patch_curdoc` supplies (TR-23.3).
  - In `_glyph_layer_lines`' tail, `"if _DASH_SCHEME_IS_FALLBACK:",` (:33467) becomes `"if _DASH_SCHEME_IS_FALLBACK and not _DASH_TRIAL:",`: that note is for whoever later runs the app, and the build has already printed the scheme's own note.
  - The `__main__` launcher block is untouched (the trial's module name is never `__main__`).
  - S46 reads the same flag to skip its memo (P1.31.8); S25 writes its guard ahead of the imports, a different hunk.
- **TR-23.3 `_dash_trial_render(source)`** (new; dash_render.py, directly above `class ServerAppBuilder:` (:32760); build time only, never copied).
  1. Local imports `re`, `warnings`, `from bokeh.document import Document` and `from bokeh.io.doc import patch_curdoc` (public: `bokeh.io.doc.__all__`; `test_csp.py:58` uses it the same way). `pat = re.compile(r"dash(?:_render| scheme| kpi| build| serve)?: ")`, the pattern of S06's scope.
  2. `ns = {"__name__": "_dash_trial_app", "_DASH_TRIAL": True}`; `rec = []`; `failure = stop = None`; `doc = Document()` (a named local: `patch_curdoc` holds the document by weak reference only).
  3. `with patch_curdoc(doc):` then, inside it, `try:` `code = compile(source, "<dash served app>", "exec")`; `with warnings.catch_warnings(record=True) as rec:` `warnings.simplefilter("always")`; `exec(code, ns)`. The source is dash's own generated text, the same string `build` wrote; user values travel inside it as base64 data and are never compiled. The module's own attach, `make_document(curdoc())`, is the one render, drawn into `doc`, never into Stata's global document.
  4. `except Exception as exc:` `failure = "dash: the served app could not draw this dashboard when dash build tried it (%s: %s); the app was written, and its sessions may fail the same way." % (type(exc).__name__, " ".join(str(exc).split())[:300])`. `except BaseException as exc:` `stop = exc`. `finally:` `ns.clear()`. Both are caught **inside** the `with`: Bokeh's `patch_curdoc` has no `try/finally` around its `yield`, so an exception leaving the block would leave a dead weak reference on its stack and every later `curdoc()` in the session would raise "Patched curdoc has been previously destroyed". After the block: `del doc`, and `raise stop` if set (Break during `dash build, server` stays r(1)).
  5. `notes = [str(w.message) for w in rec if issubclass(w.category, UserWarning) and pat.match(str(w.message))]`. Each is re-raised in order with `warnings.warn(n, UserWarning, stacklevel=2)` (not de-duplicated here: S06's scope prints each text once in Stata, and the parity test compares lists as `render()` raises them); then `failure`, if any, the same way. Return `notes` plus the failure. Non-dash warnings recorded in the trial are dropped: the trial is a check, and the user's filters still govern them in the saved render and the app.
  - Inside Stata the re-raised warnings reach S06's `_show` and print as notes; called directly they are ordinary warnings, so tests read them with `catch_warnings(record=True)`.
- **TR-23.4 `ServerAppBuilder.build(output_path, port=5006, private=False, trial=False)`.**
  - Docstring: "*trial*: after the app is written, draw it once in this process (`_dash_trial_render`) and raise the notes a session would raise (WP-30 P1.26b, A83). Off by default for the tests that call `build` directly."
  - The write (:33810-33817) is restructured so both branches fall through: `written = None`; the private branch sets `written = _DashWrittenApp(…)`; the other writes the file; then `if trial: _dash_trial_render(source)`; then `return written`. The trial runs after the `finally` that frees `_data_cache` and `_frame_cache`, so its peak is the source plus one session's frame and document, not two datasets.
  - `main()`'s server route (:36891-36892) passes `trial=not launch`: `dash build, server` and a command-line `--mode server` without `--launch` always trial (A83); `dash serve` never does (IR-10). The docstring's *launch* paragraph says so.
  - The planners stay (P1.26.7): `_plan_by_groups` and `_plan_graph_notes` still raise their notes before the source is generated, and the app keeps `warn=False` in sessions.
- **TR-23.5 `_dash_app_note_hook()`** (new; dash_render.py, directly after `_dash_note_empty_layer`, before `_dash_note_hover_unreached` (:28411); copied into the app).
  - Local imports `re`, `sys`, `types`, `warnings`. `pat = r"dash(?:_render| scheme| kpi| build| serve)?: "`.
  - The once-per-process state lives in `sys.modules["_dash_app_notes"]`, a `types.ModuleType` with `said` (a set), in `_dash_process_key`'s form (:4370-4390): `bokeh serve` runs the app in a fresh module per session and `sys.modules` persists (critic item 5). A holder of another shape is replaced. The name is a literal inside the function, so no constant is copied. S41's run-time sentinel may add attributes to the same holder.
  - If `getattr(warnings.showwarning, "_dash_app_note_hook", False) is True`, return the holder (idempotent). Otherwise keep `orig = warnings.showwarning` and install `_show(message, category, filename, lineno, file=None, line=None)`: a `UserWarning` whose text matches `pat` is printed through `_dash_emit_note(text)` only if not in `said` and `len(said) < 1000` (a bound: the launcher shows at most 100), and added to `said`; any other warning goes to `orig(…)` unchanged. Mark `_show._dash_app_note_hook = True`, assign `warnings.showwarning = _show`, and call `warnings.filterwarnings("always", message=pat, category=UserWarning)`, which puts the filter first so `PYTHONWARNINGS=error` cannot raise a note and the registry cannot hide a repeat across modules. Return the holder.
  - Re-installing after a `catch_warnings` exit restored `showwarning` keeps the same `said`.
  - In the child there is no `sfi`, so `_dash_emit_note` writes one `(note:  dash: …)` line (or a text-class line) to stderr, braces kept, controls replaced (S06 TR-06.2).
  - **Install line** (`_glyph_layer_lines`, its closing `out += [` block): directly before the scheme-fallback warning's `if` line (:33467, guarded by TR-23.2) insert a comment ("WP-30 P1.26b: a process this app owns -- python app.py, dash serve's child, bokeh serve -- prints each of its dash notes once as a (note:  dash: ...) line on stderr, whatever its warnings filters say; a process that imports the app, and a build's trial, keep their own warnings.") and the lines `"if not _DASH_TRIAL and (__name__ == '__main__'",` / `"                        or __name__.startswith('bokeh_app_')):",` / `"    _dash_app_note_hook()",` / `"",`. It sits after the copied functions (so `_dash_emit_note` exists) and before the module's first note (the fallback warning). `dash serve`'s child runs the app as `__main__` (`_DASH_BOOT`, :36985); bokeh serve names it `bokeh_app_<id>` (bokeh/application/handlers/code_runner.py:185).
- **TR-23.6 The served copy list** (R2 row S23; X.1 append only). In `_glyph_layer_lines`' functions tuple, directly after `"_dash_note_empty_layer",` (:33137 at `c96facd`), add `"_dash_smcl_escape", "_dash_emit_note",` and `"_dash_app_note_hook",` with a two-line comment ("WP-30 P1.26b: the note channel and the hook that sends this process's notes through it."). Nothing else in either tuple changes; `_shared_stat_lines` is not touched. `_dash_trial_render` and `_dash_relay_kind` are not copied (R2: build time, launcher only). `_dash_private_page` (already copied) now reads `_dash_emit_note`, which is copied.
- **TR-23.7 `_dash_relay_kind(line, in_traceback=False)`** (new; dash_render.py, directly above `def _dash_launch_app(` (:37206); launcher only, never copied). Returns `(kind, text, in_traceback)`:
  1. `s = str(line).rstrip("\r\n")`.
  2. `re.match(r"\(note:  (dash(?:_render| scheme| kpi| build| serve)?: .*)\)$", s)` gives `("note", <group 1>, False)`.
  3. S06's text-class pattern, `re.match(r"dash: .*: \(note:  (?:regress|fracpoly) could not fit model\)$|dash scheme: \(note: scheme \S+ not found, using s2color\)", s)`, gives `("note", s, False)`.
  4. `s.startswith("Traceback (most recent call last):")` gives `("show", s, True)`.
  5. With `in_traceback`: a line starting with a blank or tab gives `("show", s, True)`; a non-empty line gives `("show", s, False)` (the exception line ends it); an empty line gives `("keep", s, False)`.
  6. `re.match(r"(?:ERROR|CRITICAL):|Uncaught exception ", s)` gives `("show", s, False)` (bokeh's handler format and Tornado's last-resort ERROR, E3).
  7. Anything else, the access-log lines included, gives `("keep", s, False)` (P1.26.6; P2.38 owns the flood).
- **TR-23.8 The relay** (`_dash_launch_app(…, link_dir=None, said=())`).
  - Add `import re` to its local imports. The stderr pump pushes to a new `_err_q = queue.Queue()`; `_err_dq = collections.deque(maxlen=20)` now holds only the lines not relayed (raw, as today), so the failure message never repeats a printed line (critic item 6). Rewrite the comment at :37338-37341 to say so.
  - `_said = {re.sub(r"^dash: note: ", "dash: ", str(t)) for t in (said or ())}`; `_noted = set()`; `_in_tb = False`; `_notes_cut = False`.
  - New nested `_drain_stderr()` beside `_drain_stdout()`, main thread only (the pumps only queue): for each queued line, `text = _dash_redact_query(_clean(line), token).rstrip("\n")`; `kind, body, _in_tb = _dash_relay_kind(text, _in_tb)`.
    - `note`: skipped if `body in _said or body in _noted`; when `len(_noted) == 100`, print `dash: (further app notes not shown)` once and skip; otherwise add it to `_noted` and call `_dash_emit_note(body)` (S06: SMCL-escaped, 4,000-character bound, `errprintln` in Stata).
    - `show` when `_ready`: printed as `body[:500]` against the existing 200-line `_forwarded` budget shared with stdout (the same "dash: (further app output not shown)" line closes both).
    - Otherwise, a `show` line before the server answers or a `keep` line: `_err_dq.append(line)`.
  - Call `_drain_stderr()` in the wait loop directly after `_drain_stdout()` (:37433) and once after the pumps are joined, before the final `_drain_stdout()` (:37509-37511), so the tail is complete before either failure path reads it.
  - Unchanged: the `_handover_exc` and exit-status messages, the "port is in use" detection (a bind failure is a pre-ready traceback, kept in the tail), `_drain_stdout`, the ready line, the link, the erase rule, Break handling.
- **TR-23.9 `__main__`.** The launch call (:37674-37677) gains `said=_dash_said,` on its own line **before** `erase_app_when_ready=_erase)`, which stays the last argument: `test_serve_lifecycle.py:636-637` reads that text from the source (E6). `_dash_said` is the set S06's scope yields, bound by the `with` statement even when `main()` raises.
- **TR-23.10 The link-file note** (`_dash_private_page`, :4333-4337): the `print(…, file=out, flush=True)` becomes `_dash_emit_note("dash: note: " + p + " holds the dashboard's link, but its disk keeps no file permissions, so other accounts of this machine may read it; set TMPDIR to a folder on a disk that keeps them.")` (same words; the emitter shortens the prefix). The `if out is None: out = sys.stdout` lines go; the parameter stays (two callers, `_dash_open_tokenized` and `_dash_announce_key`, and five calls in `test_serve_token.py` pass it) and the docstring says it is no longer written to since WP-30 P1.26b. In `dash serve` this note is printed in Stata's process (`_dash_write_link`); under `python app.py` it goes to the child's stderr.
- **TR-23.11 Help** (R3: S23 owns "Server Mode" paragraphs at dash.sthlp:1483-1806 in batch 8). Exact text under Stata truth, "Help text".
- **TR-23.12 Maps (X.5, A148).** `test/function_test_map.py`, under S23's anchor, alphabetically:
  - `'_dash_app_note_hook': 'test/test_served_notes.py::TestTheAppNoteHook::test_each_note_prints_once_per_process'`
  - `'_dash_app_note_hook.<locals>._show': 'test/test_served_notes.py::TestTheAppNoteHook::test_other_warnings_go_to_the_previous_hook'`
  - `'_dash_launch_app.<locals>._drain_stderr': 'test/test_serve_launcher.py::TestTheLauncherRelaysNotesAndStderr::test_a_note_is_relayed_once_through_the_emitter'`
  - `'_dash_relay_kind': 'test/test_serve_launcher.py::TestTheRelayKind::test_each_kind_of_line'`
  - `'_dash_trial_render': 'test/test_served_notes.py::TestTheTrial::test_the_trial_raises_the_sessions_notes'`
  - No ado or Mata program is added, so `test/program_coverage_map.py` does not change.
- **TR-23.13 Both modes.** Saved page: the M6 rule at render; a filter move runs `_FILTER_JS` and raises no note. Served app: the same rule at each figure build (per panel under by()), the trial at `dash build, server`, the hook in the app's own process, the relay under `dash serve`; a served move redraws through `_dash_redraw_for`, which raises the same texts the hook already printed. G3 (`test_mode_parity.py`) runs with the 13 restored entries. No page changes for a layer that has rows, so `_SINGLE_Y_BASELINE_SHA256` (R10) does not move; 23-10 shows it.
- **TR-23.14 Security (rule 1, G9; the commit body names the threats).**
  - The key in a log: every relayed stderr line passes `_clean` and `_dash_redact_query(…, token)` before it is printed or emitted, including the `HTTPServerRequest(… uri='/?token=…')` line, which is not relayed at all (it is neither a note, an ERROR line nor a traceback line).
  - Clickable SMCL from a child: relayed notes go through `_dash_emit_note`'s `_dash_smcl_escape`; other lines are `print`ed, which Stata shows literally.
  - Exhaustion: notes bounded at 100 per launch (and 1,000 texts per app process), other lines at 200 shared with stdout and cut at 500 characters, the tail at 20 lines and 4,096 characters, the trial's failure text at 300.
  - Code execution: the trial compiles only the source `build` generated and wrote, in a namespace it clears; no user value is compiled, no `shell=True`, no `eval` of user text; the trial starts no server (its module is never `__main__`, so the launcher block never runs).
  - Process hygiene: the hook never installs in Stata's process (`_DASH_TRIAL`, the module name), and `catch_warnings` restores the session's filters and `showwarning` on every exit of the trial.

## Boundaries

- **S06's functions are called and copied, never edited:** `_dash_smcl_escape`, `_dash_emit_note`, `_dash_note_scope` and the `__main__` scope. The CRITICAL note helpers `_dash_warn_once`, `_dash_style_note` and `_dash_reset_notes` are not edited, and no `warnings.warn` message text changes.
- **Not taken:** D1 (b) (`_dash_layer_drew_anything` reading the view) and any change to the planners' `warn=False`.
- **Batch partners (batch 8).**
  - S22 owns the `dash` dispatcher's rclass line, `r(filename)`, the stale-graph note, `_dash_saving_parse`'s image extensions, and the ends of `_dash_render_immediate` and `_dash_build` (dash.ado), with the help's Syntax, Dashboard Options and Exporting paragraphs. S23 edits no dash.ado line.
  - S24 owns the mappers' construction alphas, `_apply_marker_opts`, `_empty_fit_line`, `_scheme_alpha`, `symbol_traits`, the extractor, the 26 scheme files, `_FALLBACK_PROPS` and dash.sthlp:3363-3365. S23 does not touch `GlyphMapper`, `SchemeParser` or `OptionTranslator`, nor `_scheme_lines`.
- **Later sections.**
  - S26 (batch 9): `map_function`'s fallback mark and the function note in `_dash_note_empty_layer`'s function branch.
  - S41 (batch 14): the bokeh-window note and the internals guards; its once-per-process sentinel may share `sys.modules["_dash_app_notes"]`.
  - S46 (batch 16): the warm-up that makes `dash serve`'s first render happen before the server listens (P1.31.5), the "Preparing the dashboard" line, `maxsessions()`/`idletimeout()` and their launcher flags, the memo skipped under `_DASH_TRIAL`, and P1.26.5's `dash serve` half: when the warm-up raises, stop the child and refuse r(198) (A85). S23 builds no trial for `dash serve` (IR-10).
  - S57 (batch 20): the recompute worker in the generated move path.
  - P2.38 (refused requests log one line each) and P2.26 (environment checks visible to Stata) stay residuals; they build on this relay.
- **Not this section's:** A11/C8 (BUGS.md:2559, an all-missing scatter, a constant-x lowess and a constant kdensity keep their "drew nothing" note; no own qualifier is involved), P2.37 (lpoly/mspline/mband drawn where twoway refuses an empty own-if layer), the launcher's status lines and `_DASH_LINK_UNWRITTEN`, `_dash_stop_child`, `_dash_hand_over`, and the generated `__main__` launcher.
- **Tracking documents** (GAPS2, DROPIN, ROADMAP) are S58's (A145); this file hands it their text under Notes.

## Stata truth

**No fixture and no extractor.** The truth is that twoway prints nothing for an emptied own-qualifier layer and prints the estimator note for `lfit`, which is output, not a value. As in S06, the S23 block of `test/test_wp30_truth.cscript` runs twoway live beside dash (NC-09, NC-10), so there is no `_meta` stamp and no `git add -f`.

**Probe (E1), for the record.** `s23probe.do`, run through `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s23/st <scratch>/s23/st/s23probe.do`:

```
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"
global dash_nobrowser 1
set graphics off
set linesize 255
sysuse auto, clear
log using "s23probe_t.log", text replace name(t1)
foreach t in line connected area spike dropline bar scatter {
    capture noisily twoway (scatter mpg weight) (`t' mpg weight if price > 20000), nodraw
}
foreach t in rbar rarea rcap rline rscatter rconnected rspike {
    capture noisily twoway (scatter mpg weight) (`t' mpg price weight if price > 20000), nodraw
}
capture noisily twoway (scatter mpg weight) (pcspike mpg weight price length if price > 20000), nodraw
foreach t in histogram kdensity {
    capture noisily twoway (scatter mpg weight) (`t' mpg if price > 20000), nodraw
}
capture noisily twoway (scatter mpg weight) (lowess mpg weight if price > 20000), nodraw
capture noisily twoway (scatter mpg weight) (lfit mpg weight if price > 20000), nodraw
dash clear
dash (scatter mpg weight, mcolor(notacolor) msymbol(weird)) (lfit mpg weight if price > 20000) ///
     (bar mpg weight if price > 20000) (line mpg weight if price > 20000), name(nc07)
capture noisily dash build, saving("s23_saved.html") replace
capture noisily dash build, saving("s23_app.py") replace server
log close t1
```

Output under E1. The block NC-09/NC-10 below repeats the twoway half live on every certification run.

**The type table NC-09 loops over** (variables as `plot_for` and the probe give them):

| Types | Variables |
|---|---|
| line connected area spike dropline bar scatter lowess | `mpg weight` |
| rbar rarea rcap rline rscatter rconnected rspike | `mpg price weight` |
| pcspike | `mpg weight price length` |
| histogram kdensity | `mpg` |

**Help text** (TR-23.11; R3; exact SMCL).
1. In `{ul:What a filter move redraws.}`, dash.sthlp:1547-1549, replace "legend key, as twoway draws it." with "legend key, as twoway draws it, and in silence: neither mode prints a note for it, as {cmd:twoway} prints none."
2. dash.sthlp:1584 and 1621-1622: "a line beginning {cmd:dash: note:} names it" becomes "a note, {cmd:(note: dash:} ...{cmd:)}, names it" (twice).
3. Insert after the paragraph ending "instead of blocking." (dash.sthlp:1586-1589), before the `{pstd}` that opens `{ul:Running the generated .py file independently.}` (:1591-1592):

```
{pstd}
{ul:Notes.}  {cmd:dash build, server} prints the notes {cmd:dash build}
prints for a saved page -- an option it draws differently, a fit
{cmd:twoway} could not fit, a {cmd:by()} sub-option it ignores -- in the
same {cmd:(note: dash:} ...{cmd:)} form, once each: after writing the app it
draws the dashboard once, as a session of the app would, and names what
that drawing noted.  This costs one more drawing of the dashboard.  If that
drawing fails, a note says so, and the app is still written.
{cmd:dash serve} prints its build's notes at once and, while it serves,
the app's own notes, error lines and Python tracebacks: each note once,
never one its build already printed, at most 100 notes and 200 other lines,
with the link's key and every query string removed.  The app's notes
appear when the first session draws the dashboard.  Run as
{cmd:python app.py} or under {cmd:bokeh serve}, the app prints each note
once per process on its standard error, as {cmd:(note: dash:} ...{cmd:)},
whatever Python's warnings filters or {cmd:PYTHONWARNINGS} say.

```

SMCL collapses the two blanks of `(note:  dash:`; the help writes one (S06 TR-06.12). S46 later rewrites "The app's notes appear when the first session draws the dashboard." for its warm-up.

## TDD test stubs

### Regression tests (23-01, 23-02; each fails at the batch-8 base unless marked guard)

`test/test_served_notes.py` (new). It imports `dash_render as dr`, `make_data_json` from `conftest`, and `make_spec`, `plot_for` from `test_server_layer_defects`. `_DF` is eight rows of `mpg`, `weight`, `price` (all below 20000), `length`, `foreign`. `_SPEC` = `make_spec([plot_for("scatter", {"mcolor": "notacolor", "msymbol": "weird"}), plot_for("lfit", if_expr="price > 20000"), plot_for("bar", if_expr="price > 20000")])`; `_SPEC_BY` is `_SPEC` with `graph_options={"by": "foreign, graphregion(color(red))"}`. `_saved(spec)` and `_built(spec, trial)` return sorted warning texts recorded under `catch_warnings(record=True)` + `simplefilter("always")`, from `DashRenderer.render()` and from `ServerAppBuilder.build(ap, private=False, trial=trial)`. `_main_server(spec, tmp_path)` runs `dr.main(sp, dp, str(tmp_path / "a.py"), mode="server")` under the same recorder.

- Test: `test/test_served_notes.py::TestTheServerBuildNamesTheSavedNotes::test_main_names_what_the_saved_build_names` — parametrized over `_SPEC` and `_SPEC_BY`. First asserts the saved list holds at least two `dash: ` notes (so an empty equality cannot pass), then `_main_server(...) == _saved(...)`. Fails at base: the server list holds only the planner's by() note, or nothing.
- Test: `…::TestTheTrial::test_the_trial_raises_the_sessions_notes` — `_built(_SPEC_BY, True) == _saved(_SPEC_BY)`. Fails at base: `TypeError: … unexpected keyword argument 'trial'`.
- Test (guard): `…::TestTheTrial::test_a_build_without_the_trial_is_unchanged` — `_built(_SPEC, False)` holds no `mcolor` note (the planners only).
- Test: `…::TestTheTrial::test_the_trial_leaves_the_session_as_it_found_it` — snapshots `warnings.showwarning`, `list(warnings.filters)`, `len(curdoc().roots)`, the filters of `tornado.access`/`tornado.general`/`tornado.application`, and `"_dash_app_notes" in sys.modules`; after `build(trial=True)` each is equal (and the module absent). Fails at base on the keyword.
- Test: `…::TestTheTrial::test_a_session_error_filter_does_not_fail_the_trial` — `_SPEC` (no by(), so no planner note), under `warnings.simplefilter("error")` and inside S06's `dr._dash_note_scope(sfi=rec)` (as the `__main__` block runs it): `build(trial=True)` raises nothing, and the stand-in recorded the mcolor and msymbol notes once each. The trial's own `simplefilter("always")` is what keeps its exec from raising; without the scope the re-raised notes would follow the test's "error" filter, which is S06's business (measured on the prototype: a direct call under "error" raised on the first planner note).
- Test: `…::TestTheTrial::test_a_trial_that_raises_is_one_note_and_the_app_is_written` — monkeypatch `ServerAppBuilder._generate_app_source` to wrap the real one and replace its one `"\ndef make_document(doc):\n"` with `"\ndef make_document(doc):\n    raise RuntimeError('probe')\n"` (asserting the text occurs once), so the module's own attach raises; `build(trial=True)` raises no exception, records exactly one note containing `"could not draw this dashboard"` and `"RuntimeError: probe"`, the file exists, and `curdoc()` still returns a document afterwards (the patched-document stack was unwound).
- Test: `…::TestTheTrial::test_the_fallback_scheme_note_is_not_repeated` — a builder whose `scheme.is_fallback` is set True before `build(trial=True)`: no recorded note contains `"this app was built where no .scheme file"`.
- Test: `…::TestTheAppNoteHook::test_each_note_prints_once_per_process` — inside `warnings.catch_warnings()`, with `monkeypatch.delitem(sys.modules, "_dash_app_notes", raising=False)` and `monkeypatch.setitem(sys.modules, "sfi", None)`: after `dr._dash_app_note_hook()`, `warnings.warn("dash: a.")` three times and `warnings.warn("dash: b.")` give stderr lines exactly `["(note:  dash: a.)", "(note:  dash: b.)"]` (capsys). Fails at base: `AttributeError: … '_dash_app_note_hook'`.
- Test: `…::TestTheAppNoteHook::test_it_is_installed_once` — a second call returns the same holder and leaves `warnings.showwarning` the same object; after a `catch_warnings()` block restores `showwarning`, a call re-installs it and `said` still holds `"dash: a."`.
- Test: `…::TestTheAppNoteHook::test_other_warnings_go_to_the_previous_hook` — a recorder installed as `warnings.showwarning` before the hook receives `FutureWarning("x")` and `UserWarning("not dash")`, and none of the dash notes.
- Test: `…::TestTheAppNoteHook::test_an_error_filter_raises_no_note` — `simplefilter("error")` first (as `PYTHONWARNINGS=error` is set at interpreter start), then the hook: `warnings.warn("dash kpi: k.")` raises nothing and prints one line, and `warnings.warn("x", FutureWarning)` still raises (the session's filter governs it). Measured on the prototype: `['(note:  dash: a.)', '(note:  dash: b.)', '(note:  dash kpi: k.)']`, the FutureWarning raised.
- Test: `…::TestTheGeneratedApp::test_an_app_process_prints_each_note_once_under_pythonwarnings_error` — build `_SPEC` (no trial); `subprocess.run([sys.executable, "-c", DRIVER, app], env=dict(os.environ, PYTHONWARNINGS="error::UserWarning"), capture_output=True, text=True, timeout=180)`, where `DRIVER` execs the app's text in a `types.ModuleType("bokeh_app_probe")` namespace (which runs `make_document(curdoc())` at import) and then calls `make_document(Document())` twice. rc 0; stderr holds the mcolor and msymbol notes exactly once each as `(note:  dash: …)`, the regress note once as text, and no `UserWarning`, `Traceback` or `.py:` path. Fails at base: rc 1, `UserWarning: dash: mcolor(notacolor)…`.
- Test: `…::TestTheGeneratedApp::test_an_imported_app_installs_no_hook` (guard) — exec of the app under the name `_probe_import`, inside `warnings.catch_warnings()`: `warnings.showwarning` is unchanged and `"_dash_app_notes" not in sys.modules`.
- Test: `…::TestTheGeneratedApp::test_the_trial_flag_installs_nothing` — first take dash's redaction filter off the three Tornado loggers (`monkeypatch.setattr(lg, "filters", [f for f in lg.filters if not getattr(f, "_dash_redacts_queries", False)])`, so an earlier test in the worker cannot make this pass), then exec the app text in `{"__name__": "bokeh_app_probe", "_DASH_TRIAL": True}` under `patch_curdoc(throwaway)` and `catch_warnings(record=True)`, with `scheme.is_fallback` forced on the builder before `build`: no filter is added, no hook is installed, no fallback warning is recorded, the global `curdoc()` gains no root, and `throwaway` holds the drawn roots. Fails at base: the three filters are added.
- Test: `…::TestTheGeneratedApp::test_the_note_channel_is_copied_in` — the generated source defines `_dash_smcl_escape`, `_dash_emit_note` and `_dash_app_note_hook`, and holds `_DASH_TRIAL = bool(globals().get('_DASH_TRIAL', False))`.
- Test: `…::TestAnEmptiedOwnQualifierIsSilent::test_both_modes_are_silent` — parametrized over `bar`, `line`, `rarea`, `pcspike`, `spike`: `make_spec([plot_for("scatter"), plot_for(t, if_expr="price > 20000")])`; the saved list and the served session list (exec the app under `catch_warnings(record=True)`, then `make_document(Document())`) hold no `"drew nothing"`. Fails at base on the saved side (`… plot 2 (bar) drew nothing from 8 observations.`).
- Test (guard): `…::TestAnEmptiedOwnQualifierIsSilent::test_the_estimator_note_stays_in_both_modes` — `lfit` with `if_expr="price > 20000"`: each mode holds one `(note:  regress could not fit model)`.
- Test (guard): `…::TestAnEmptiedOwnQualifierIsSilent::test_a_layer_without_its_own_qualifier_is_still_named` — a scatter of a variable missing everywhere: both modes keep "drew nothing from 8 observations." (A11 stays BUGS.md:2559's).
- Test: `test/test_immediate_dashboards.py::TestTheReportHelpers::test_a_layer_whose_own_qualifier_keeps_no_row_is_silent` — `self._notes("g1", 2, "bar", 74, [], layer_rows=0) == []`; with `layer_rows=None` and `layer_rows=5` the drew-nothing text is returned; `self._notes("g1", 2, "function", 74, [], layer_rows=0)` still gives the function note. Fails at base: `TypeError: … unexpected keyword argument 'layer_rows'`. (The class's `_notes(self, *args)` helper, test_immediate_dashboards.py:424-428, takes positional arguments only; 23-01 gives it `**kw` and passes them on, which leaves the existing callers unchanged.)
- Test: `test/test_mode_parity.py` — the 13 restored entries, `_case("<t> with its own if that keeps no row", [_sc(), plot_for(t, if_expr="price > 20000")])` for `bar rbar rarea line area spike dropline rcap rline rscatter pcspike scatter connected`, directly after the `rspike` entry, whose comment ("bar, rbar and rarea are left out …") is rewritten to say they are restored under M6 (WP-30 P1.26b). At base `TestTheTwoModesAgree::test_same_warnings` fails for the 11 noted types ("warnings differ … drew nothing"); `scatter` and `connected` pass (guards). No `_MUST_WARN` entry is added and `ALLOWED` is untouched (R8).
- Test: `test/test_mode_parity.py::TestTheServedBuildNamesTheSavedNotes::test_the_trial_names_what_the_saved_build_names` — parametrized over `CORPUS` (grouped per entry by conftest, so `_render_pair(name, spec)["std"]["warnings"]` is reused): `build(ap, trial=True)`'s sorted warnings equal the saved list. Fails at base on the keyword for every case.

`test/test_serve_launcher.py` (`_fake_popen_class`; `monkeypatch.setattr(dr, "_dash_emit_note", rec)` where `rec` appends its argument):
- Test: `…::TestTheRelayKind::test_each_kind_of_line` — the table of TR-23.7, including `"(note:  dash: a {b})"` → note `"dash: a {b}"`; the text-class regress line → note, whole; `"ERROR:bokeh.server.views.ws:x"` and `"Uncaught exception GET /?<query redacted> (127.0.0.1)"` → show; a traceback header, two indented lines and `"UserWarning: dash: x"` → show with the state carried and cleared; `"403 GET /?<query redacted> (127.0.0.1) 0.5ms"` and `"HTTPServerRequest(…)"` → keep. Fails at base: `AttributeError`.
- Test: `…::TestTheLauncherRelaysNotesAndStderr::test_a_note_is_relayed_once_through_the_emitter` — stderr `"(note:  dash: a.)\n(note:  dash: a.)\n"`, rc 0: `rec == ["dash: a."]`. Fails at base: `rec == []`.
- Test: `…::test_a_note_the_build_printed_is_not_repeated` — `said={"dash: note: a."}` and the same stderr: `rec == []`. Fails at base: `TypeError: … 'said'`.
- Test: `…::test_twoways_own_words_are_relayed_as_notes` — stderr `"dash: graph 'g' plot 2 (lfit): (note:  regress could not fit model)\n"`: `rec` holds that line once.
- Test: `…::test_notes_have_their_own_budget` — 150 distinct notes and 300 other `keep` lines: `len(rec) == 100`, stdout holds `dash: (further app notes not shown)` once.
- Test: `…::test_error_lines_and_tracebacks_show_once_the_server_answers` — the `/health` server of `TestTheLauncherPrintsTheUrlOnceHealthAnswers` and a stderr stream that yields its lines only after `/health` was hit (the `_LateStream` form of `test_serve_token.py`): `ERROR:bokeh.x:y`, a three-line traceback and a `403 GET …` line. stdout holds the ERROR line and the traceback once each and no `403 GET`.
- Test (guard): `…::test_a_failed_launch_keeps_its_tail` — rc 3, stderr `"Traceback (most recent call last):\n  File \"a.py\"\nOSError: boom\n(note:  dash: n.)\n"`: the RuntimeError holds the traceback and `boom`, not `(note:`; `rec == ["dash: n."]`.
- Test: `…::test_a_relayed_line_never_holds_the_key` — `dr._dash_new_token` monkeypatched to a fixed 43-character key `K`; after ready, stderr `"(note:  dash: x K)\n"`, `"ERROR:bokeh.x: GET /?token=K&y=1\n"`: neither `rec` nor stdout holds `K`, and stdout holds `<query redacted>`.

`test/test_serve_token.py` (flip, E6): `TestTheTokenHelpers::test_a_page_the_disk_will_not_keep_private_is_written_with_a_note`.

### Certification cases (23-03 writes them; `grep -rn 'NC-0[7-9]\|NC-1[0-9]' test/` prints nothing before)

`test/test_serve_launch.cscript`: one contiguous run directly above the `// SRV-19` comment block (after TOK-04 and any case an earlier WP-30 section put there, S22's GE-20 included; SRV-19 must stay last). NC-07 and NC-08 open with `quietly graph drop _all`, so S22's stale-graph note (batch 8, merged first) never enters their note lists. A Python helper `_nc_notes(log)` reads a text log through `Macro.getLocal`, re-joins Stata's `> ` continuation lines, and returns the sorted lines holding `(note:`; it sets locals, never reads a macro inside a Python string literal.

- **NC-07** `dash build, server` names what `dash build` names.
  - Registration `dash (scatter mpg weight, mcolor(notacolor) msymbol(weird)) (lfit mpg weight if price > 20000) (bar mpg weight if price > 20000) (line mpg weight if price > 20000), name(nc07)` (the E1 probe's).
  - (a) `dash build, saving(<tmp>nc07.html) replace` and `dash build, saving(<tmp>nc07.py) replace server`, each under its own text log at linesize 255: both rc 0; the saved log has at least three `(note:` lines and no `drew nothing`; the server log's sorted `(note:` lines equal the saved log's.
  - (b) The same two builds under `quietly`: the server log's `(note:  dash: ` lines equal the saved log's (S06's visibility holds for the trial's notes).
  - Fails at base: the saved log holds two `drew nothing` lines, and the server log holds no `(note:` line.
- **NC-08** a real `dash serve` relays the app's notes. TOK-02's pattern (a daemon thread started in Stata's Python before `dash serve` blocks): it waits for `/health`, reads the key from the run folder's `link.html`, GETs the page with the key twice (two sessions) and once without it (a 403 access-log line), waits 3 s, and stops the listener with `lsof`/SIGTERM as TOK-02 does. `capture noisily dash serve, port(<free>) timeout(1) nobrowser` with the NC-07 registration, under a text and an SMCL log.
  - rc 0, under 60 s; the sorted `(note:` lines of the text log equal NC-07's saved list (each note once over two sessions); no line holds `UserWarning`, `Traceback`, `.py:` or `403 GET`; neither log holds the key (read only in Python, as TOK-03 does).
  - Fails at base: no `(note:` line in the log.

`test/test_wp30_truth.cscript`, S23's block, between its start and end lines (files under `` `w30_work' ``, erased before the end line):
- **NC-09** an emptied own-qualifier layer is silent, as twoway draws it. For each type of the Stata-truth table: `twoway (scatter mpg weight) (<t> <vars> if price > 20000), nodraw` under a text log has rc 0 and no `(note:` line (truth, live); then `quietly graph drop _all` (a `nodraw` graph is in memory, and S22, landing first in this batch, notes `graph export` on every file-writing dash command while one is); `dash (scatter mpg weight) (<t> <vars> if price > 20000), saving(…, replace)` has rc 0 and no `drew nothing` or `(note:` line; `dash build, saving(…py) replace server` after registering the same graph has rc 0 and no such line. One `_w30_expect` per type and mode, one `_w30_done NC-09`.
  - Fails at base: the saved run of 11 types logs `drew nothing`.
- **NC-10** the estimator note stays: `twoway (scatter mpg weight) (lfit mpg weight if price > 20000), nodraw` logs one `could not fit model` line; then `quietly graph drop _all` (as in NC-09); the dash saved build and `dash build, server` of the same graph log one each.
  - Fails at base on the server build (0).

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| M6 rule (unit) | pytest `test_immediate_dashboards.py::TestTheReportHelpers` | arguments | n/a |
| M6 in both modes, estimator note kept | pytest `TestAnEmptiedOwnQualifierIsSilent`; `test_mode_parity.py` 13 restored entries (all eleven comparisons, `TestAFilterMoveAgrees` where an entry has a filter) | `plot_for`, parity `_DF` | yes, saved and served |
| Trial: notes, leaves no trace, filters, failure, fallback | pytest `TestTheServerBuildNamesTheSavedNotes`, `TestTheTrial`; `TestTheServedBuildNamesTheSavedNotes` over 272 cases | `_SPEC`, `_SPEC_BY`, CORPUS | served build vs saved |
| The app's hook | pytest `TestTheAppNoteHook`, `TestTheGeneratedApp` (a subprocess under `PYTHONWARNINGS=error::UserWarning`) | built app | served |
| The relay | pytest `TestTheRelayKind`, `TestTheLauncherRelaysNotesAndStderr`; the two flipped `test_serve_token.py` nodes | fake children | served |
| Stata: build and serve | `test_serve_launch.cscript` NC-07, NC-08 through the driver | `sysuse auto` | saved build vs server build vs `dash serve` |
| Stata: twoway truth | `test_wp30_truth.cscript` NC-09, NC-10, `WP30_ONLY=S23` | `sysuse auto`; twoway live | saved and served builds |
| No drawing change for layers with rows (R10) | `test_varlist_expansion.py` | — | yes |
| Copy lists and registries (G4, R2) | `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_mode_parity.py::TestTheCopiedHelpersBringTheirCallees`, `test_function_test_map.py`, `test_no_orphans.py`, `test_tracking_documents.py`, `test_cscript_hygiene.py` | — | — |
| Help | `test_help_examples.py`, `test_help_conformance.py`, `test_help_claims_1.py`-`_8.py`; `test_help_examples.cscript` through the driver | dash.sthlp | — |

**Acceptance criteria.**
- **AC-23.1** (BR-23.1) NC-07 (a) and (b) pass; `TestTheServerBuildNamesTheSavedNotes` passes for both specs; `TestTheServedBuildNamesTheSavedNotes` passes for all 272 cases.
- **AC-23.2** (BR-23.2) `test_a_trial_that_raises_is_one_note_and_the_app_is_written` passes.
- **AC-23.3** (BR-23.3) NC-08 passes; every `TestTheLauncherRelaysNotesAndStderr` test passes, including the key and budget tests.
- **AC-23.4** (BR-23.4) `test_a_failed_launch_keeps_its_tail`, and the unchanged `TestTheLauncherRefusesAHeldPort`, `TestTheLauncherReportsTheExitStatus` and `test_serve_token.py::TestTheLauncherPassesTheToken::test_the_stderr_tail_and_forwarded_lines_are_redacted`, pass.
- **AC-23.5** (BR-23.5) `TestTheAppNoteHook` and `test_an_app_process_prints_each_note_once_under_pythonwarnings_error` pass.
- **AC-23.6** (BR-23.6) NC-09 and NC-10 print PASS; `TestAnEmptiedOwnQualifierIsSilent` passes; `test_mode_parity.py` is green with the 13 restored entries and `ALLOWED` unchanged.
- **AC-23.7** (BR-23.7) `test_the_trial_leaves_the_session_as_it_found_it`, `test_an_imported_app_installs_no_hook` and `test_the_trial_flag_installs_nothing` pass.
- **AC-23.8** (BR-23.8) `grep -c '{ul:Notes.}' dash.sthlp` prints 1; `grep -c 'line beginning {cmd:dash: note:}' dash.sthlp` prints 0; `grep -c 'in silence: neither mode prints a note' dash.sthlp` prints 1; the help tests pass.
- **AC-23.9** Tracking (G5): the entry is closed naming existing tests, the `"P1.26b"` key is gone, and `grep -c '<!-- WP-30 P1.26b -->' CHANGELOG.md` prints 0.

## Tasks

**Commit boundary.** Tasks 23-01 to 23-11 form the one commit of entry `P1.26b`, subject `Name the served app's notes in Stata and draw an emptied own-qualifier layer in silence (WP-30 P1.26b)`, made by 23-11 on `wp30-s23` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s23`, after one full run through the queue. `$S` is `<scratch>/s23`; `$R` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash`. The body, in order: `$S/23-P1.26b-failure.txt` (paths cut to their last component, Notes trap 9); the measured defect (E1); what changed and where (TR-23.1-23.10, both modes); the threats closed (TR-23.14); then one line each of the forms `Regression: test/<file>.py::<Class>::<test> -- failed at <batch-8 base sha> with <text>` (one per regression node and cscript case), `Guard: <node> -- passed at <sha>`, `Flipped: <node> -- <old expectation> was wrong because <why>`, and `BUGS.md: "dash build, server and dash serve report no option or empty-layer notes, and the served child's stderr never reaches Stata" (closed)`. No `Fixture:` line.

<task type="auto" id="23-01">
  <name>Write the failing served-note pytest tests</name>
  <files>test/test_served_notes.py, test/test_immediate_dashboards.py, test/test_mode_parity.py</files>
  <action><![CDATA[Check `git -C $WT rev-parse HEAD` equals `<scratch>/batch-8-base.txt` and `git -C $WT branch --show-current` prints `wp30-s23`. Run `gitnexus impact _make_figure_body -d upstream -r dash` in the main checkout only if `<scratch>/batch-8-impact.txt` lacks it, and confirm the CRITICAL approval is recorded there before any later edit. Create `test/test_served_notes.py` with the classes `TestTheServerBuildNamesTheSavedNotes`, `TestTheTrial`, `TestTheAppNoteHook`, `TestTheGeneratedApp` and `TestAnEmptiedOwnQualifierIsSilent` exactly as "TDD test stubs" lists them; every test that touches `warnings` runs inside `warnings.catch_warnings()` and removes `sys.modules["_dash_app_notes"]` with monkeypatch. Add `test_a_layer_whose_own_qualifier_keeps_no_row_is_silent` to `TestTheReportHelpers` in `test/test_immediate_dashboards.py` (its `_notes(self, *args)` helper at :424-428 gains `**kw`, passed on to `dr._dash_note_empty_layer`). In `test/test_mode_parity.py` add the 13 own-if entries directly after the `rspike` own-if entry (find it by the text "rspike with its own if that keeps no row"), rewrite that entry's comment to say bar, rbar and rarea are restored under M6 (WP-30 P1.26b), and append class `TestTheServedBuildNamesTheSavedNotes` reusing `_render_pair`.]]></action>
  <verify><![CDATA[`cd $WT && python3 -m pytest test/test_served_notes.py test/test_immediate_dashboards.py -q -n0 2>&1 | tail -3` shows failures, every one from the stubs marked "Fails at base", and the four guards (`test_a_build_without_the_trial_is_unchanged`, `test_an_imported_app_installs_no_hook`, `test_the_estimator_note_stays_in_both_modes`, `test_a_layer_without_its_own_qualifier_is_still_named`) passing. `python3 -m pytest test/test_mode_parity.py -q -k "own if that keeps no row or TestTheServedBuildNamesTheSavedNotes" 2>&1 | tail -3` shows `test_same_warnings` failing for exactly the 11 noted types and every `TestTheServedBuildNamesTheSavedNotes` case failing on the keyword.]]></verify>
  <done>Every pytest regression test of the trial, the hook and the M6 rule existed in the worktree and failed against the unmodified tree, with the guards green.</done>
</task>

<task type="auto" id="23-02">
  <name>Write the failing launcher relay tests</name>
  <files>test/test_serve_launcher.py</files>
  <action><![CDATA[Append classes `TestTheRelayKind` and `TestTheLauncherRelaysNotesAndStderr` to `test/test_serve_launcher.py` as "TDD test stubs" lists them, using `_fake_popen_class` for the rc-only cases and the `/health` server of `TestTheLauncherPrintsTheUrlOnceHealthAnswers` with a late stderr stream (a class whose `readline` blocks on the `hit` event, then yields its lines) for the after-ready cases. Record emitted notes with `monkeypatch.setattr(dr, "_dash_emit_note", rec)`; fix the key with `monkeypatch.setattr(dr, "_dash_new_token", lambda: K)` where `K = "k" * 43`. Do not edit any existing test of the file.]]></action>
  <verify><![CDATA[`cd $WT && python3 -m pytest test/test_serve_launcher.py -q -n0 2>&1 | tail -3`: the existing tests pass; of the new ones `test_a_failed_launch_keeps_its_tail` may pass or fail on its `rec` assertion only, and all others fail (`AttributeError` on `_dash_relay_kind`, `TypeError` on `said`, or `rec == []`).]]></verify>
  <done>The relay's regression tests existed and failed against the unmodified tree, and every pre-existing launcher test still passed.</done>
</task>

<task type="auto" id="23-03">
  <name>Write the certification cases and save failures</name>
  <files>test/test_serve_launch.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[Grep `test/*.cscript test/*.py test/*.do` for `NC-0[7-9]` and `NC-1[0-9]` and stop if any exists. In `test/test_serve_launch.cscript` insert NC-07 and NC-08 as one contiguous run directly above the `// SRV-19` comment block, in TOK-02's thread form, with the `_nc_notes` Python helper defined first; each case prints `NC-0k PASS: ...` and asserts. Fill S23's stub in `test/test_wp30_truth.cscript` between its own start and end lines with NC-09 (the type table of Stata truth) and NC-10, through `_w30_expect`/`_w30_done`, writing only under `` `w30_work' ``; helper programs, if any, go directly above S23's header and declare `version 19`. Then run both scripts through the driver of index.md ("The cscript driver"), `WP30_ONLY=S23` for the truth script, and append their FAIL lines to the pytest failures of 23-01 and 23-02 in `$S/23-P1.26b-failure.txt`.]]></action>
  <verify><![CDATA[`grep -c 'FAIL' $S/run_test_wp30_truth.log` is at least 1 (NC-09 on the saved side, NC-10 on the server build); `grep -E 'NC-07|NC-08' $S/run_test_serve_launch.log` shows NC-07 failing (two `drew nothing` lines; no server note) and NC-08 failing (no `(note:` line). `$S/23-P1.26b-failure.txt` holds the pytest summary lines of 23-01 and 23-02 and these FAIL lines. `git -C $WT status --porcelain` lists only the six test files, untracked or modified.]]></verify>
  <done>The failure text of every regression test and case was saved at the batch-8 base, and nothing was committed.</done>
</task>

<task type="auto" id="23-04">
  <name>Draw an emptied own-qualifier layer silently</name>
  <files>dash_render.py</files>
  <action><![CDATA[Warn in the task output that `DashRenderer._make_figure_body` is CRITICAL (4 upstream) and cite the recorded approval. Apply TR-23.1: `_dash_note_empty_layer` gains `layer_rows=None`, its docstring line, and `elif rows and layer_rows != 0:`; in `_make_figure_body` add `_layer_rows = None` after `_plot_view = facet_view` and `_layer_rows = int(sum(_mask))` directly before `_pf = BooleanFilter(booleans=_mask)`, and pass `layer_rows=_layer_rows` to the `_dash_note_empty_layer` call; in `_generate_app_source` change the served call to pass `len(_g_df_graph)` as rows and `layer_rows=len(g_df)`. Change no other line of the three functions.]]></action>
  <verify><![CDATA[`cd $WT && python3 -m pytest test/test_immediate_dashboards.py test/test_served_notes.py -q -n0 -k "Report or Emptied" 2>&1 | tail -2` shows them passing; `python3 -m pytest test/test_mode_parity.py -q -k "own if that keeps no row" 2>&1 | tail -2` shows 0 failed; `git -C $WT diff --stat dash_render.py` shows a small change (under 20 lines).]]></verify>
  <done>Both modes drew a layer whose own if or in kept no row in silence, and the estimator note and the notes of layers without an own qualifier were unchanged.</done>
</task>

<task type="auto" id="23-05">
  <name>Add the build-time trial render</name>
  <files>dash_render.py</files>
  <action><![CDATA[Warn that `ServerAppBuilder._generate_app_source` is HIGH and cite the approval. Apply TR-23.2 (the `_DASH_TRIAL` header line after the CSV-button import, the guard on the module-level `_dash_install_access_log_redaction()` and the guard on the fallback warning; the attach line is left exactly as it is), TR-23.3 (`_dash_trial_render` directly above `class ServerAppBuilder:`, docstring naming WP-30 P1.26b, A83, A85 and the threats of TR-23.14) and TR-23.4 (`build(..., trial=False)` with the write restructured so the trial runs after the file is written, and `main()` passing `trial=not launch`, docstring updated). Keep `_plan_by_groups` and `_plan_graph_notes` where they are.]]></action>
  <verify><![CDATA[`cd $WT && python3 -m pytest test/test_served_notes.py -q -n0 -k "Trial or ServerBuild or trial_flag" 2>&1 | tail -2` shows 0 failed; `python3 -m pytest test/test_note_channel.py -q -n0 2>&1 | tail -1` (S06's) shows 0 failed; `python3 -m pytest test/test_mode_parity.py -q -k TestTheServedBuildNamesTheSavedNotes 2>&1 | tail -2` shows 272 passed; `python3 -m pytest test/test_server_build_returns.py test/test_render_cli_port.py -q 2>&1 | tail -1` shows 0 failed.]]></verify>
  <done>dash build, server raised the notes the saved build raises, from one trial render that left the building process as it found it.</done>
</task>

<task type="auto" id="23-06">
  <name>Install the served app's note hook</name>
  <files>dash_render.py</files>
  <action><![CDATA[Warn that `ServerAppBuilder._glyph_layer_lines` is HIGH and cite the approval. Add `_dash_app_note_hook` (TR-23.5) directly after `_dash_note_empty_layer`, self-contained except for `_dash_emit_note`. In `_glyph_layer_lines` append `"_dash_smcl_escape", "_dash_emit_note",` and `"_dash_app_note_hook",` with their comment directly after `"_dash_note_empty_layer",` (TR-23.6), and insert the install lines directly before the scheme-fallback warning's `if` line (guarded by 23-05). Route `_dash_private_page`'s note through `_dash_emit_note` as TR-23.10 says, keeping its signature.]]></action>
  <verify><![CDATA[`cd $WT && python3 -m pytest test/test_served_notes.py -q -n0 2>&1 | tail -1` shows 0 failed; `python3 -m pytest test/test_statistical_helpers.py -q -k TestTheServedAppCarriesEveryName test/test_resource_limits.py -k TestTheServedAppDefinesEveryNameItReads 2>&1 | tail -1` and `python3 -m pytest test/test_mode_parity.py -q -k TestTheCopiedHelpersBringTheirCallees 2>&1 | tail -1` show 0 failed.]]></verify>
  <done>A process the app owns printed each of its notes once as a (note:  dash: ...) line whatever its warnings filters said, and an importing process and the trial were left alone.</done>
</task>

<task type="auto" id="23-07">
  <name>Relay the child's notes and errors</name>
  <files>dash_render.py</files>
  <action><![CDATA[Add `_dash_relay_kind` directly above `def _dash_launch_app(` (TR-23.7). In `_dash_launch_app` add the `said=()` keyword and its docstring paragraph, `import re`, the stderr queue, `_drain_stderr` and its two call sites, with `_err_dq` holding only lines not relayed (TR-23.8). In the `__main__` block pass `said=_dash_said,` to the launch call, before `erase_app_when_ready=_erase)` (TR-23.9). Leave every other line of the launcher as it is.]]></action>
  <verify><![CDATA[`cd $WT && python3 -m pytest test/test_serve_launcher.py test/test_serve_token.py -q -n0 2>&1 | tail -1` shows only the two nodes of E6's flip table failing (flipped in 23-08); `python3 -m pytest test/test_serve_lifecycle.py test/test_private_files.py -q 2>&1 | tail -1` shows 0 failed (E6 for the known flaky nodes).]]></verify>
  <done>dash serve printed the app's notes once each, its error lines and tracebacks once the server answered, within their budgets and redacted, and a failed launch quoted only the lines it had not printed.</done>
</task>

<task type="auto" id="23-08">
  <name>Flip the pinned tests and map functions</name>
  <files>test/test_serve_token.py, test/function_test_map.py</files>
  <action><![CDATA[Re-measure the pinned list: run every test file that names `_dash_private_page`, `_dash_launch_app`, `ServerAppBuilder(` with `main(`, or `drew nothing` (the commands of E6) and confirm only the nodes of E6 fail. Flip each in place with a comment `# Flipped (WP-30 P1.26b): ...` and record its `Flipped:` line for the body, as E6's table says: both read the note from `capsys.readouterr().err` as one line starting `(note:  dash: `, holding the path and not the key (and `TMPDIR` in the first; `out.getvalue() == ""` there). Add the five keys of TR-23.12 under S23's anchor in `test/function_test_map.py`, alphabetically. Any other node that turns red is a defect of this section: stop and report it.]]></action>
  <verify><![CDATA[`cd $WT && python3 -m pytest test/test_serve_token.py test/test_function_test_map.py test/test_no_orphans.py -q -n0 2>&1 | tail -1` shows 0 failed.]]></verify>
  <done>The two pinned nodes read the note through the channel with their Flipped lines, and every new function was mapped to a test that exercises it.</done>
</task>

<task type="auto" id="23-09">
  <name>Update the Server Mode help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Apply the three edits of "Help text" under Stata truth: the silence sentence at the end of the "What a filter move redraws" paragraph, the two "line beginning dash: note:" phrases (near dash.sthlp:1584 and :1622, found by text), and the new `{ul:Notes.}` paragraph after "instead of blocking.". Edit no paragraph outside Server Mode (R3); keep the SMCL wrap near 76 columns.]]></action>
  <verify><![CDATA[The three `grep -c` checks of AC-23.8 print 1, 0 and 1. `cd $WT && python3 -m pytest test/test_help_examples.py test/test_help_conformance.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_3.py test/test_help_claims_4.py test/test_help_claims_5.py test/test_help_claims_6.py test/test_help_claims_7.py test/test_help_claims_8.py -q 2>&1 | tail -1` shows 0 failed.]]></verify>
  <done>The help said what each served route prints and that an emptied own-qualifier layer is silent, and no help test moved.</done>
</task>

<task type="auto" id="23-10">
  <name>Certify both modes and the registries</name>
  <files>none</files>
  <action><![CDATA[Run the changed pytest files with `-n0` where single, then G3 (`python3 -m pytest test/test_mode_parity.py -q`), G4 and the R2 registries (`test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_function_test_map.py`, `test_no_orphans.py`, `test_cscript_hygiene.py`, `test_tracking_documents.py`) and `test_varlist_expansion.py`. Run `test_serve_launch.cscript` and `test_wp30_truth.cscript` (`WP30_ONLY=S23`) through the driver, then `test_help_examples.cscript`. Mutation checks by hand, reverted after each: drop `layer_rows=_layer_rows` (NC-09 and the parity entries go red); drop the hook's `filterwarnings` line (`test_an_error_filter_raises_no_note` goes red); relay ERROR lines before ready (`test_a_failed_launch_keeps_its_tail` goes red); skip `_dash_redact_query` in `_drain_stderr` (`test_a_relayed_line_never_holds_the_key` goes red).]]></action>
  <verify><![CDATA[Every pytest command shows 0 failed; `grep -cE 'NC-0[789] PASS|NC-10 PASS' $S/run_test_serve_launch.log $S/run_test_wp30_truth.log` sums to 4, with no FAIL and no SKIP line; `test_wp30_truth: ALL CHECKS PASSED` is in the truth log; each mutation turned its named test red and `git -C $WT diff --stat` was restored after it.]]></verify>
  <done>Both modes, the relay, the hook, the trial and every registry were green, and each guard was shown to bite.</done>
</task>

<task type="auto" id="23-11">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[Close entry P1.26b in place: `- [x]` and the Resolution line of Notes, verbatim apart from the date and indented two spaces as every BUGS.md Resolution line is (`  - Resolution: Fixed …`, TR-01.10 item 1). Delete the `"P1.26b"` line of `WP30_OPEN`. Replace the two `<!-- WP-30 P1.26b -->` markers in place with the two CHANGELOG lines of Notes. Run `test_tracking_documents.py`, then `git -C $WT merge --no-edit main` (expect `Already up to date.`), then one full suite through the queue (`<scratch>/full_suite_queue.sh $WT <scratch>/23-full-1.log`, waited for, never relaunched). Stage the 13 files of "Section completion criteria" (`git -C $WT add` each), then check G6 (`git -C $WT diff --cached --name-only` lists exactly those 13), write the body to `$S/msg-23.txt`, run G7 before and after, confirm the branch, and commit.]]></action>
  <verify><![CDATA[`tail -2 <scratch>/23-full-1.log` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.26b -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.26b": "' test/test_tracking_documents.py` prints 0 (only `WP30_OPEN`'s row has that form; the permanent `WP30_LISTS` and `WP30_SECTION` rows stay); `grep -Eic 'claude|anthropic' $S/msg-23.txt` and on `git -C $WT log -1 --format=%B` print 0; `git -C $WT log -1 --format=%s` ends `(WP-30 P1.26b)`.]]></verify>
  <done>P1.26b was closed in BUGS.md naming existing tests, its key and both markers were gone, and one green commit on wp30-s23 carried the section.</done>
</task>

## Section completion criteria

- One commit on `wp30-s23`, subject ending `(WP-30 P1.26b)`, whose full run through the queue showed 0 failed; its body opens with the saved failure text and carries the Regression, Guard, Flipped and BUGS.md lines and names the threats.
- `dash build, server` prints the saved build's notes (NC-07, `TestTheServedBuildNamesTheSavedNotes` over 272 cases); `dash serve` relays the app's notes once each and no key (NC-08); a layer whose own qualifier keeps no row is silent in both modes and twoway's estimator note stays (NC-09, NC-10, the 13 restored corpus entries).
- The trial leaves Stata's Python as it found it; the hook installs only in a process the app owns; the relay keeps a failed launch's tail.
- `test_mode_parity.py` (with `ALLOWED` untouched), the registries, the served name guards and `test_varlist_expansion.py` are green.
- BUGS.md entry `P1.26b` is closed, `WP30_OPEN["P1.26b"]` is gone, both markers are replaced, and the help states the behaviour.
- Nothing staged outside: `dash_render.py`, `dash.sthlp`, `BUGS.md`, `CHANGELOG.md`, `test/test_served_notes.py`, `test/test_immediate_dashboards.py`, `test/test_mode_parity.py`, `test/test_serve_launcher.py`, `test/test_serve_token.py`, `test/function_test_map.py`, `test/test_tracking_documents.py`, `test/test_serve_launch.cscript`, `test/test_wp30_truth.cscript`. No plan file, `CLAUDE.md`, `.gitignore`, `AGENTS.md` or `*.html`.

## Notes

**Traps for the executor.**
1. **Count after the intersection.** `_layer_rows` is taken from `_mask` after the facet/linked intersection (:30496-30498), not before: the served count is the figure's rows (one by() panel, or a linked graph's own rows) that the layer's qualifier keeps. Counted before, a linked graph whose shared source holds another graph's rows would stay noted on the saved page and be silent when served.
2. **The estimator branch comes first.** M6 silences only "drew nothing"; keep the new condition in the last `elif`, below the `unfit` branch and the `_mark_silent` return, or `lfit` would lose twoway's own note (NC-10, S06's NC-02).
3. **The trial never runs as `__main__`, and never edits the attach.** Its namespace is `_dash_trial_app`; under `__main__` the source would start a server inside Stata. Its render is the module's own `make_document(curdoc())`, drawn into the document `patch_curdoc` supplies; do not change that line (17 test pins, E2.5), and catch every exception inside the `patch_curdoc` block (TR-23.3 step 4), or a failed trial breaks `curdoc()` for the rest of the Stata session.
4. **Never install the hook in Stata's process.** The critic measured that a module-level hook execed outside `catch_warnings(record=True)` leaves Stata's `showwarning` replaced, and inside it records nothing. The install line's `_DASH_TRIAL` and module-name conditions are both required, and the leave-no-trace test pins them.
5. **The hook must come after the copied helpers.** Its install line sits in `_glyph_layer_lines`' tail, below the copy loop and the classes and above the fallback warning; placed in the header it would call `_dash_emit_note` before it exists, and placed after `_glyph_layer_lines()` it would miss the fallback note.
6. **Each stderr line is relayed or kept, never both.** A traceback before `/health` answers stays in `_err_dq` (the port-in-use detection reads it); after, it is printed and not quoted again.
7. **Main thread only.** `_dash_emit_note` falls back to stderr off the main thread (S06). The pump threads only queue; `_drain_stderr` runs in the wait loop.
8. **Copy-list names are append-only and checked.** A misspelt name is a served-only `NameError`; `test_every_listed_name_exists` (S01) and `TestTheServedAppDefinesEveryNameItReads` are the guards. S06's `_dash_emit_note` must stay self-contained (S06 trap 2): do not make it read a new module constant.
9. **The failure text goes into the commit body.** Pytest and Stata print absolute paths and the scratch path holds a word G7 forbids: cut every path in `23-P1.26b-failure.txt` and the body to its last component before G7.
10. **Anchors drift.** Find each site by its quoted text; S08-S21 (batches 3-7) edited `_make_figure_body` and `_generate_app_source` before this batch (R12 lists S18 and S21 among the figure-body editors).
11. **Time.** `TestTheServedBuildNamesTheSavedNotes` adds about 0.2-0.4 s per corpus entry on one worker per group (E5); the full run grows by well under a minute at 6 workers. NC-09 runs 18 types three ways (about 2 minutes).
12. **Merge rules.**
    - R1: NC-07/NC-08 as one contiguous run above `// SRV-19` in `test_serve_launch.cscript` (if S22 appends to the same script, merge order S22 then S23 keeps both); NC-09/NC-10 inside S23's own block of the truth script.
    - R2: row S23's anchor only (after `"_dash_note_empty_layer",`); the map keys under S23's anchor.
    - R3: Server Mode paragraphs only (S22 edits Syntax, Dashboard Options and Exporting; S24 edits :3363-3365).
    - R4: two markers, in place. R5: only S23's entry and key.
    - R8: the own-if CORPUS entries are restored by this section (index R8 names it); appended next to the `rspike` entry, not at CORPUS's end, so S24's appended cases merge in a different hunk; `_MUST_WARN` and `ALLOWED` untouched.
    - R9: the two flips of E6. R10: no pin moves. R12: S23 is batch 8's only editor of `_generate_app_source` and `_make_figure_body`. R13: impact at the base, `detect-changes` at landing (it must name only the symbols of E7 and the three new functions).

**Commit-body line forms** are those of the Commit boundary paragraph above (BRIEF, with WP-30's base sha).

**BUGS.md Resolution (23-11, verbatim apart from the date):**

`- Resolution: Fixed <ddmonyyyy> (WP-30, P1.26b). dash build, server now prints the notes the saved build prints: ServerAppBuilder.build(trial=True), which main() uses on every server route but dash serve's, runs the app it wrote once in the building process through _dash_trial_render (exec of the generated source under _DASH_TRIAL, whose own make_document(curdoc()) draws into a throwaway Document through bokeh's patch_curdoc, inside catch_warnings(record=True)) and re-raises the notes that render raised, so S06's channel prints them; a trial that fails is one note and the app is still written. The generated app installs _dash_app_note_hook when it owns its process (python app.py, dash serve's child, bokeh serve), which prints each distinct dash note once per process as (note:  dash: ...) on stderr whatever PYTHONWARNINGS says; the trial and an importing process get no hook. _dash_launch_app relays the child's notes through _dash_emit_note (once each, never one its build printed, at most 100) and its ERROR lines and tracebacks once the server answers (within the 200-line budget), all redacted, and quotes only unrelayed lines when a launch fails; the launcher's link-file note takes the same channel. A layer whose own if or in keeps no row is drawn in silence in both modes, as twoway draws it (M6): _dash_note_empty_layer takes the layer's own row count from _make_figure_body and from the served figure builder. Pinned by test/test_served_notes.py::TestTheServerBuildNamesTheSavedNotes::test_main_names_what_the_saved_build_names, test/test_served_notes.py::TestTheTrial::test_the_trial_leaves_the_session_as_it_found_it, test/test_served_notes.py::TestTheGeneratedApp::test_an_app_process_prints_each_note_once_under_pythonwarnings_error, test/test_served_notes.py::TestAnEmptiedOwnQualifierIsSilent::test_both_modes_are_silent, test/test_mode_parity.py::TestTheServedBuildNamesTheSavedNotes::test_the_trial_names_what_the_saved_build_names, test/test_serve_launcher.py::TestTheLauncherRelaysNotesAndStderr::test_a_note_is_relayed_once_through_the_emitter, test/test_serve_launcher.py::TestTheLauncherRelaysNotesAndStderr::test_a_relayed_line_never_holds_the_key, test/test_serve_launch.cscript NC-07, test/test_serve_launch.cscript NC-08, test/test_wp30_truth.cscript NC-09, test/test_wp30_truth.cscript NC-10. Residual, deferred (WP-30): dash serve's notes arrive when the first session draws the dashboard until S46's warm-up draws it before the server listens, and a warm-up that fails is refused r(198) there (P1.26.5).`

**CHANGELOG lines (23-11, in place of the two markers):**

- `### Changed behaviour (may need your do-files changed)`:
  `- A layer whose own if or in keeps no observation is drawn in silence in both modes, as twoway draws it. Before, the saved page printed "dash: graph 'g1' plot 3 (bar) drew nothing from 74 observations." for line, area, spike, dropline, rcap, rline, rscatter, pcspike, bar, rbar and rarea layers, and the served app printed nothing. twoway's own "(note:  regress could not fit model)" for such an lfit is still printed, in both modes. The served app run by python app.py, bokeh serve or dash serve prints each of its notes once per process, as (note:  dash: ...) on its standard error, where each session printed Python warnings with the app's path and source lines. (WP-30, P1.26b)`
- `### Fixed in WP-30`:
  `- dash build, server prints the notes dash build prints for the same graphs (an option drawn differently, a fit twoway could not fit, a by() sub-option), from one drawing of the app it wrote; it printed none. dash serve relays the served app's notes, error lines and tracebacks to Stata while it serves, each note once and none its build already printed, with the key and query strings removed; before, the app's output reached Stata only when the launch failed. A served session no longer fails when PYTHONWARNINGS=error turns a dash note into an exception. (WP-30, P1.26b)`

**Hand-offs.**
- **S26.** The function note joins `_dash_note_empty_layer`'s function branch, above the `layer_rows` condition; it then reaches Stata through the trial (`dash build, server`) and the relay (`dash serve`) with no further work. A new helper goes after `"_dash_function_points",` (R2 row S26), not after S23's names. The hook never installs in a process that imports or execs the app under another module name, so test helpers such as `test_function_expr._render`'s served branch keep recording warnings as they do today (S26 Notes, trap 2).
- **S46.** The warm-up runs `make_document` before the server listens; its notes leave through the hook and the relay unchanged. Under `_DASH_TRIAL` the memo is skipped. When the warm-up raises, the child must exit non-zero so `_dash_launch_app` reports r(198) through the existing failure path (A85; the traceback is pre-ready, so it is quoted in the tail); S46 rewrites the help sentence "The app's notes appear when the first session draws the dashboard."
- **S41.** Its run-time window note must be raised inside `make_document` or `main()`, or emitted directly, so it takes the hook (served) or the scope (Stata); its once-per-process sentinel may live in `sys.modules["_dash_app_notes"]`.

**Notes for the closeout (S58; A145).**
- **GAPS2.md F5** (GAPS2.md:1341): `- **Tracked:** Closed in WP-30, BUGS.md "dash build, server and dash serve report no option or empty-layer notes, and the served child's stderr never reaches Stata", commit <sha>` for F5a and F5b; F5c recorded closed at `c96facd` (research p1-26 §2: banner, "server answers" line and link path reach the Stata log; prints carry `flush=True`). Append `(WP-30, F5)` to the Resolution.
- **GAPS2 I summary** (GAPS2.md:1590): its Tracked line names S06's commit and this one (the served half).
- **DROPIN-REMAINING.md P1.26** (lines 147-153): the first two bullets and the WP-29 S12 note are closed by this commit; the S12 note closes under M6 (silent in both modes), not by adding a served note.
- **ROADMAP.md**: P2.38 (refused-request lines) and P2.26 (environment checks visible to Stata) can now name this relay as their route; record that dash serve's notes move before listening with S46.
- **GAPS2 A11/C8** stays open (BUGS.md:2559): M6's other reading (an all-missing scatter, a constant-x lowess, a constant kdensity) has no own qualifier and was not changed here.
