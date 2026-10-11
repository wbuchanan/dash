# WP-29 Plan — close the drop-in P0 gaps

> Architect pass, 30sep2026. Branch `wp29-p0`, cut from `main` `357c368`; the report commit `7421d3d` adds `.ultraplan/handoff/DROPIN-REMAINING.md`. The section manifest, batches, merge order, merge rules R1-R8, the cscript driver and the verification gates are in `index.md`. Section files are written to `.ultraplan/sections/BRIEF.md` with the deltas `index.md` lists.
>
> **Amended 01oct2026, before execution (binding).** BR-29.6 and K4 now carry section 11's per-row tolerances (SD-1) and say degrees 0-3 are drawn and 4-7 only unit-tested (SD-7). BR-29.11 and E6 now carry section 08's bounded preview retention (R-6, TR-08.7). S01 writes these amended texts into ROADMAP.md (§7 S01 item 1), so no section records a requirement the plan does not meet. These amendments replace three things: the "Handed to S15 to restate BR-29.6" of section 11 SD-1 and its closeout note; section 08's closeout note "PLAN.md BR-29.11 and E6: reword per R-6"; and section 15's R15-8 and Appendix D.10 (see §7 S15).
>
> **Amended 01oct2026, after ratification (binding).** The maintainer answered index.md's "Decisions for maintainer ratification" (answers recorded there verbatim): (1) "Keep the date axis." (D05-1 struck); (2) "Allow "unsafe" temp directory locations and do not refuse writing the app files into a directory of the user's that is not private." (S08 codes struck: no privacy refusal, the r(603) unsafe-root and r(198) not-private refusals gone (r(603) remains only for an OS failure to create the folder), anti-hijack guards kept with r(7102)); (3) "Ensure that the token will never be missing." (S13 item 1 struck: an app started without a token makes its own); (4) "Resolve the server app's index known gap." (S14 SD3's served residual struck: the served `index` carries page ranks). Every other row is ratified, R-6 among them. This file now says so in G4, M4, BR-29.7, BR-29.9, BR-29.10, BR-29.11, §7 S01 item 1 (whose ROADMAP text section-01's Appendix D now carries in place), the risk register and E6.
>
> **Amended 01oct2026, round 2 (binding).** The maintainer answered three more questions (recorded verbatim in index.md's "Decisions for maintainer ratification", round 2): (A) token link failure: "Print the URL once" (S13 K-8's stop path struck: when the served app cannot write its private `link.html` anywhere, the fresh private temp folder included, it prints one warning line and the full tokenized URL once, to the output of whoever started it, and keeps serving; this is the only case where the key is ever printed; section 13 K-9); (B) app swap in a shared non-sticky temp folder: "Launch from open file" (dash starts its served app only from the bytes it read through a descriptor it opened with `O_NOFOLLOW` and verified, handed to `python -P -c` on stdin, on every route dash itself uses; the app-substitution residual is closed; section 08 R-9, TR-08.8a); (C) commit the plan: "Commit them" (`.ultraplan/wp29/` is committed on `wp29-p0` by step 0a, before any worktree is cut). Round 1 stays in force. This file now says so in G4, M4, BR-29.10, BR-29.11, §7 S01 item 1, §7 S15.4 and S15.7, the risk register (K5, new K16) and E6.

## 1. Context

dash is a Stata package that takes `twoway` syntax and draws interactive Bokeh dashboards in two modes that must agree:
- the **saved** standalone HTML page, where filters move through JavaScript callbacks;
- the **served** Bokeh app, written by `ServerAppBuilder`, where filters recompute in Python. The app receives the module-level helpers it needs through the served copy lists in `dash_render.py` (constants 28362-28497, functions 28535-28829, `_shared_stat_lines` 28889).

WP-28 closed 22 GAPS2 gaps and is the last package marked DONE (ROADMAP.md:4243).

A full re-audit at `357c368` (DROPIN-REMAINING.md) checked every open item in REMAINING.md, GAPS2.md and TWOWAY_COVERAGE_AUDIT.md against HEAD. Its verdict is that dash is not yet a drop-in replacement, and it ranks 20 items as **P0**, in four groups:
- **Silently wrong output in common use:** P0.1-P0.9, P0.15-P0.18, P0.20.
- **A variable silently dropped:** P0.10.
- **Security and lifecycle of the data:** P0.11-P0.14.
- **An installation that fails on common Pythons:** P0.19.

WP-29 closes all 20.

## 2. Goals

1. **G1.** Every P0 item is fixed in both modes, before and after any filter move, or is cued where the maintainer decided on a cue (P0.17).
2. **G2.** Wherever Stata computes or draws something, dash's number equals Stata's, checked against a fixture extracted from Stata. The pinned values are:
   - bandwidths and bands;
   - the function points;
   - the date-unit densities and KPIs;
   - the by() axis ranges;
   - the axis(#) refusals;
   - the title and line order.
3. **G3.** Every refusal dash adds matches twoway's return code and message text, measured in StataNow 19.5.
4. **G4.** The served app requires a per-launch secret and never runs without one (started without one, it makes its own). The key is never printed, except once, after a warning, when no link file can be written anywhere (round 2, answer A). Every temporary copy dash writes is private (0600 in a 0700 directory) wherever the location allows; a location that cannot be kept private is named in a note, never refused, and dash never writes through a link or over another account's file. dash starts its served app only from the bytes it wrote and verified, never by path (round 2, answer B). The app never outlives the Stata session that started it, and is stopped by Break.
5. **G5.** The saved page holds only the observations some consumer of the page reads.
6. **G6.** `dash_setup` works on, or gives one working command for, externally-managed (PEP 668) Pythons, on every shell it prints a command for.
7. **G7.** Each P0 entry is closed by a regression test that failed before its fix (rule 7), in one commit per entry, on a tree that was never red (rule 4).

## 3. Non-goals

- **P1-P3 of DROPIN-REMAINING.md are out of scope.** These include stylelists, scheme look, natscale tickers, horizontal, connect()/cmissing(), text(), SMCL/TeX, size units, colour syntax, named styles, by() chrome and legend text. A P0 fix that touches one of them must not change its current behaviour except where the P0 item requires it.
- **No JavaScript port of any estimator (M3).** On the saved page, fits stay as built and get a cue. The kdensity and histogram recounts that already exist keep running, with inputs now in Stata units (S05).
- **The bootstrap band is not kept** as an option or a fallback (M2).
- **No cookie** carries the served token (u11a: cookies are not isolated by port, RFC 6265 §8.5).
- **Windows, Linux and pre-19 Stata are not certified here.** S09 makes the commands it prints correct for `cmd.exe` and POSIX shells and tests them in the sandbox. Measuring real Windows and Linux hosts stays a residual for S15 to record.
- **No version bump and no new release heading.** WP-29's lines go into the existing `0.1.0, 30sep2026 (release candidate)` release of CHANGELOG.md.

## 4. Binding decisions

| Id | Decision |
|---|---|
| M1 | P0.1: MATCH twoway. Every connecting type joins in data order unless `sort` or `sort(varlist)` is given, and `sort(varlist)` is honoured. Ties keep the data order (stable sort; twoway's own tie order is random, measured). tsline/tsrline always join in time order. Pins that assert x order are flipped. |
| M2 | P0.7/P0.9: PORT Stata's math to Python: the per-kernel, per-degree rule-of-thumb bandwidth (Fan-Gijbels constants, Stata's `invsym` drop rule including the absolute 1e-19 pivot floor), and lpolyci's analytic band (eq. 4 of [R] lpoly) with `pwidth()` and `var()`. Verified against Stata truth fixtures. Works in served recomputes after a move. Bootstrap removed. |
| M3 | P0.17: a visible stale cue on the saved page's frozen computed layers after a move that removed at least one row of the layer's estimation sample. The served app keeps refitting. No JS estimator. |
| M4 | P0.12: a per-launch secret token is required by the served app, and Stata opens the tokenized URL. The app, spec and data files are written 0600 inside a 0700 directory. Ratified reading (01oct2026, answers 2 and 3): the token is never missing (a hand-started app makes its own), and "0600 inside a 0700 directory" holds wherever the location allows; a location that is not private is noted, never refused; a folder the user names is never refused, re-moded or noted (section 08 R-8). Round 2 (01oct2026, answers A and B): the key is never printed except once, after a warning, when no link file can be written anywhere (section 13 K-9), and dash launches its served app from the file it opened and verified (section 08 R-9). |
| A1-A10 | Architect decisions in `index.md` "Decision record": grouping; the u02/u05 cycle; the one truth script; open BUGS entries plus the `WP29_OPEN` allowance; tracking docs are S15's only; committing the audit at step 0a; conftest labels; the `lpvar` key; `127.0.0.1` URLs; commit subjects. |

## 5. User stories (package level)

Personas: the **twoway user** (pastes a twoway command and expects twoway's picture), the **dashboard publisher** (shares a saved page or a served app), the **installer** (runs `dash_setup` on their machine), the **maintainer** (keeps dash certified).

- **US-29.1** As a twoway user, I want `line`, `connected`, `area` and the range line types joined in my data's order, and in my `sort(varlist)` order, so a do-file draws the same path in dash as in Stata. (P0.1)
- **US-29.2** As a twoway user, I want `by()` panels to share one scale per axis unless I ask for `yrescale`/`xrescale`/`rescale`, so the panels can be compared at a glance as in Stata. (P0.2)
- **US-29.3** As a twoway user, I want my axis titles, legend keys and tooltips to show the variable name when the variable has no label, and `ytitle(, size(large))` to restyle the default title rather than delete it. (P0.3, P0.4)
- **US-29.4** As a twoway user, I want `ylabel(..., axis(2))`, `yscale(log axis(2))`, `yline(#, axis(2))` and `xtick(..., axis(2))` drawn on the axis they name, and an axis number no layer uses refused as twoway refuses it. (P0.5)
- **US-29.5** As a twoway user, I want `twoway function` to draw exactly Stata's curve and refuse exactly what Stata refuses (`2^3^x`, `pi`, `e`). (P0.6)
- **US-29.6** As an analyst, I want lpoly's default bandwidth and lpolyci's confidence band to equal Stata's, for every kernel, every degree dash draws (0-3), `pwidth()` and `var()`, so I can publish what dash draws. (P0.7, P0.9)
- **US-29.7** As an analyst with a date variable, I want histograms, densities, smooths and KPI statistics computed in the date's Stata units, so `width(7)` is a week and `sd` is in days. (P0.8, P0.20)
- **US-29.8** As a dashboard publisher, I want every variable I name in `hover()` to appear in the tooltip, in both modes. (P0.10)
- **US-29.9** As a dashboard publisher, I want the saved page to hold only the rows the dashboard shows or filters, so rows my `if`/`in` excluded are not shipped to every reader. (P0.11)
- **US-29.10** As a dashboard publisher on a shared machine, I want no other account to open my served app, read its files, or find its preview pages afterwards. (P0.12, P0.14)
- **US-29.11** As a dashboard publisher, I want the served app to stop when Stata stops or when I press Break, and the messages to tell me to press Break. (P0.13)
- **US-29.12** As a dashboard reader, I want a linked or `by()` layer with its own `if` to stay inside its panel after a filter move, and the colour key to span only the rows the layer draws. (P0.15, P0.16)
- **US-29.13** As a dashboard reader of a saved page, I want to see that a fit no longer matches the filtered points. As a reader of a served app, I want bar widths recomputed after a move. (P0.17, P0.18)
- **US-29.14** As an installer on Homebrew, Arch or Ubuntu 25.04+ Python, I want `dash_setup` to detect PEP 668, offer `venv(path)`, and print commands that work as printed in my shell. (P0.19)
- **US-29.15** As the maintainer, I want each P0 fix pinned by a test that failed before it and by Stata truth where Stata computes the value, so no P0 defect can return unnoticed.

## 6. Business requirements (package level)

- **BR-29.1** Join order: data order by default, x order under `sort`, varlist order under `sort(varlist)` (the rightmost copy wins), time order for ts types, ties stable. This holds in both modes and after a move. An invalid `sort()` name is refused with twoway's message and r(198). (P0.1)
- **BR-29.2** by() axes: one shared scale per axis by default (x, y, y2, x2, Total panel included), staying the union of drawn data after any move. The rescale forms and their abbreviations give per-panel scales. A `range()` that twoway ignores on a rescaled axis is named once, at build time, in both modes. (P0.2)
- **BR-29.3** Text: a variable's label is used when it is non-empty, else its name. A title sub-option with no text keeps the default text. A typed `""` empties the title. These apply wherever a title, key or tooltip names a variable. (P0.3, P0.4)
- **BR-29.4** axis(#): every routed option draws on the named axis. An axis number with no layer is refused with twoway's rc and message, and axis-number parsing follows twoway's integer bounds. Nothing is dropped unnamed. (P0.5)
- **BR-29.5** function: the points are Stata's own (`twoway__function_gen`), written so that they round-trip exactly (`%24.17g`). An expression Stata refuses is refused with Stata's rc, before graph-level options are checked. The RNG state matches twoway's. (P0.6)
- **BR-29.6** lpoly: the default bandwidth equals Stata's `r(bwidth)` within section 11's per-row tolerance (SD-1):
  - 1e-7 relative on `exact` rows (degree 0/1, x centre within 3 half-ranges of 0);
  - 5e-5 relative on `noisy` rows (degree 2/3, or an offset x such as years, dates or `weight+20000`), where Stata's own float64 arithmetic varies (measured up to 1.6e-5).

  A missing or zero `r(bwidth)` draws y=0 on every grid point, as twoway does. The lpolyci band at a given `bwidth()` and `pwidth()` (or `var()`) equals Stata's `lpoly, ci` band within 1e-8·max(1,|y|) wherever Stata's se is defined (BR-11.4). At the default bandwidths it is as exact as the bandwidth's tier: `noisy` cases are held at 1e-4 relative of the band half-width. This holds for every kernel, the degrees dash draws (0-3; `degree=int,0,3`, dash.ado:1900), `pwidth()`, `var()`, weights, and the small-x scales where Stata drops pivots. The degree 4-7 constants (SD-7) are unit-tested against the quadrature and recorded in the fixture at 5e-4, and no path draws them until P1.14. All of this holds in served recomputes, and the option checks run in twoway's order. The only exceptions are the divergences D1-D9 that section 11 measures, documents and pins. (P0.7, P0.9)
- **BR-29.7** Dates: computed layers and KPI statistics run in Stata units and draw on the date axis. Out-of-range bins or points are dropped and named in one note, consistently in both modes. No non-finite number reaches page JSON. When every layer is computed and the first is `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci` over a date, dash keeps its date axis where twoway labels numbers; that is a documented divergence (D05-1 struck, ratified 01oct2026: "Keep the date axis."). (P0.8, P0.20)
- **BR-29.8** hover(): every named variable is exported and counted against the data limits when some layer can show it. A name that is not a variable is refused before any Stata command text is built. (P0.10)
- **BR-29.9** Embedding: the saved page holds a cell only when a layer, a recomputed KPI card, a filter or the csv export reads that variable on that observation. Stata-computed results still use the whole data. Both modes number the rows they send 0..m-1 in data order: the saved page's row ids and the served `index` of the shared source and of every per-layer source, so no row number reveals an excluded observation (ratified 01oct2026, answer 4; section 14 TR-14.18). The help discloses the rule. (P0.11)
- **BR-29.10** Served access: without the per-launch token, no session, page, autoload, metadata or row reaches a client, under `dash serve`, `python app.py` and `bokeh serve app.py`. The served app never runs without a token: started with none, it makes its own (`secrets.token_urlsafe(32)`), writes its link to a 0600 file and prints only that file's path, never the key; a supplied token that is invalid is still refused at start (ratified 01oct2026, answer 3; section 13 K-1..K-8). The key is never printed, except in one case (round 2, answer A, "Print the URL once"; section 13 K-9): when the link file cannot be written in any folder dash tries (under `dash serve` the run folder, then a fresh private temp folder; an app that made its own key, its fresh private temp folder), nothing is stopped: one warning line saying the key now appears in that output and any log of it, then the full tokenized URL alone, are printed exactly once (per launch under `dash serve`, per process under `python app.py`, per app path per process under `bokeh serve`) to the output of whoever started the server, which keeps serving. The only remaining stop is an `--address` no link can name. There is no opt-out. `/health` and BokehJS static files stay open. Tokens are compared in constant time. (P0.12a)
- **BR-29.11** Private files: every temporary copy of the data lives in a per-user directory dash makes 0700, and every file is created 0600 (section 08 R-8, ratified 01oct2026, answer 2):
  - **No privacy refusal.** A location that cannot be kept private (a `c(tmpdir)` other accounts can change, a disk that keeps no permissions, a `dash-<uid>` that is not the user's own folder) is never refused. dash proceeds, leaves a planted `dash-<uid>` alone and uses a 0700 fallback `dash-<uid>-<8 chars>`, and prints one `dash: note: …` per command naming the location and its remedy. A folder the user names is never refused, re-moded or noted.
  - **Anti-hijack refusals, kept (not about privacy).** No write goes through a symbolic link, into a FIFO or device, or over a hard-linked or another account's file at the target name, or to a name that appears mid-write, and no `app.py` replaced after it was written is started. Each ends r(7102).
  - **Launch from the open file (round 2, answer B, "Launch from open file"; section 08 R-9, TR-08.8a).** dash's one launcher route, `_dash_launch_app` (`dash serve` and the renderer's `--launch`; dash has no preview server), opens `app.py` with `O_NOFOLLOW` where available, checks the open descriptor (a regular file, this account's, the `(st_dev, st_ino)` and size recorded when it was written) and the SHA-256 of the bytes read through it, and hands those bytes to `[sys.executable, "-P", "-c", _DASH_BOOT, app_path, …]` as one framed block on stdin; the child compiles them under the app's own file name and never opens a path. So a swap of the path or its folder after the check cannot change what runs, and no module planted beside the app or in the working folder is imported. The route is the same on macOS, Linux and Windows (no `/dev/fd`). A `python app.py` or `bokeh serve app.py` the user runs is outside dash's control and is documented, not changed. Only an operating-system failure to create a folder at all ends r(603), the code Stata's own `file open` gives.

  One-line preview pages are private and bounded (section 08 R-6, TR-08.7):
  - each has a unique name and is 0600, in the 0700 folder `dash-<uid>/previews/`;
  - a session keeps its newest five;
  - `dash clear` removes the session's pages, except a page a browser was asked to open in the last 60 s;
  - another session's pages are removed only once that session is dead (POSIX) or the page is more than 24 h old;
  - all sessions together keep at most 25.

  They are not deleted when the command ends, because the browser reads the page after `open` returns and `$dash_nobrowser` prints its path for the user to open. A server app the user names is written 0600 into the folder the user names (R-7); pages the user names keep twoway's umask semantics. R-6 and R-7 were ratified on 01oct2026. (P0.12b, P0.14)
- **BR-29.12** Lifecycle: the served app stops within the grace period after the parent Stata dies. No data file stays on disk while it serves. Break stops `dash serve` from every front end and ends the command with r(1). Messages name Break, not Ctrl+C, in the GUI. (P0.13)
- **BR-29.13** Saved filters: a linked or `by()` layer's view stays inside its panel or graph qualifier after any move. A colorvar's domain, levels and bins come from the layer's drawn rows, in both modes, for numeric, string and date colorvars. (P0.15, P0.16)
- **BR-29.14** Stale and redraw: after a move that removed a row of a frozen layer's estimation sample (weights as dash's `_layer_weights` applies them), the layer shows a visible cue. Moving back clears it. The served app recomputes bar and rbar widths, and an emptied layer's style, as the saved build does. (P0.17, P0.18)
- **BR-29.15** Setup: on a PEP 668 Python, `dash_setup` starts no pip process. It names the reason and the `venv()` route, never suggests `--break-system-packages`, and ends r(198). `venv(path)` creates, installs into and verifies a private environment and prints how to link Stata to it. Printed commands run as printed in `cmd.exe` and POSIX shells. pip runs from a private working directory with the resolved interpreter. (P0.19)
- **BR-29.16** Every P0 BUGS.md entry is closed with a Resolution naming existing tests. Every CHANGELOG marker is replaced. ROADMAP WP-29 is DONE, and the GAPS2 ids it lists are closed with commits that exist.

## 7. Foundation (S01) and closeout (S15) content

### S01 — Tracking foundation (one commit, `(WP-29 S01)`)

1. **ROADMAP.md.** Insert `## WP-29 · Close the drop-in P0 gaps` directly above `## Traceability matrix` (ROADMAP.md:4448), not headed DONE. It carries:
   - the header line `**GAPS2 closed:** (filled at closeout) · **Severity:** S1 (19), S2 (2) · **Effort:** XL · **Depends on:** WP-28`. The parenthetical yields no ids for `_parse_roadmap_gaps2` (test_tracking_documents.py:721-741);
   - the user story;
   - BR-29.1-BR-29.16, as amended in §6;
   - TRs pointing at `index.md`;
   - AC-29.1-AC-29.12, which mirror §9 below as amended (AC-29.6 = E6).

   **ROADMAP text (binding on section 01; applied in place 01oct2026).** Section 01's Appendix D used to carry the pre-amendment wording of BR-29.6 (`within 1e-9 relative`, `degrees 0-7`), BR-29.11 (`one-line preview pages are deleted when the command ends`, `refuses if unsafe`) and AC-29.6 (`no preview page survives the command`, `an unsafe root refused r(603)`). On 01oct2026 those bullets, and BR-29.7, BR-29.9 and BR-29.10 for the ratified answers, were replaced in Appendix D itself by the text below, verbatim. Task 01-05 inserts Appendix D as written; if the two ever differ, the text below wins.

   The six bullets grow from 6, 4, 4, 4, 5 and 5 lines to 14, 6, 6, 9, 20 and 15 (BR-29.10, BR-29.11 and AC-29.6 as amended again by round 2, 01oct2026: answers A and B), which adds 42 lines to Appendix D's 176, for 218. ROADMAP.md is 4590 lines at `7421d3d` (measured, `wc -l`), so:
   - task 01-05's verify expects `wc -l < ROADMAP.md` to print **4808** (section 01 now says so);
   - section 01's "documents after S01" line reads `ROADMAP.md: 4808 lines (+218)`.

   The readers' outputs (`_parse_roadmap`, `_parse_roadmap_gaps2`, `_matrix_gaps` 76) and the hazard greps are unchanged: the new text has no `Gaps closed`, no heading line, no `> **DONE` line and no Markdown link.

   ~~~~markdown
   - **BR-29.6** lpoly: the default bandwidth equals Stata's `r(bwidth)`
     within 1e-7 relative on exact rows (degree 0/1, x centred within three
     half-ranges of 0) and within 5e-5 relative on noisy rows (degree 2/3,
     or an offset x such as years, dates or `weight+20000`), where Stata's
     own float64 arithmetic varies; a missing or zero `r(bwidth)` draws y=0
     on every grid point, as twoway does; the lpolyci band at a given
     `bwidth()` and `pwidth()` or `var()` equals Stata's `lpoly, ci` band
     within 1e-8 times max(1,|y|), and at the default bandwidths within the
     bandwidth's tier; for every kernel, degrees 0-3 (the only degrees dash
     draws; the degree 4-7 constants are unit-tested, not drawn),
     `pwidth()`, `var()`, weights and the small-x scales where Stata drops
     pivots, in served recomputes too, with the option checks in twoway's
     order; the divergences D1-D9 that section 11 measures are documented
     and pinned (P0.7, P0.9).
   ~~~~

   ~~~~markdown
   - **BR-29.7** Dates: computed layers and KPI statistics run in Stata units
     and draw on the date axis; out-of-range bins or points are dropped and
     named in one note, alike in both modes; no non-finite number reaches page
     JSON; when every layer is computed and the first is lfit, qfit, lfitci,
     qfitci, kdensity, lpoly or lpolyci over a date, dash keeps its date axis
     where twoway labels numbers, a documented divergence (P0.8, P0.20).
   ~~~~

   ~~~~markdown
   - **BR-29.9** Embedding: the saved page holds a cell only when a layer, a
     recomputed KPI card, a filter or the csv export reads that variable on
     that observation; Stata-computed results still use the whole data; both
     modes number the rows they send 0..m-1 in data order (the saved page's
     row ids and the served sources' `index`), so no row number reveals an
     excluded observation; the help discloses the rule (P0.11).
   ~~~~

   ~~~~markdown
   - **BR-29.10** Served access: without the per-launch token no session,
     page, autoload, metadata or row reaches a client, under `dash serve`,
     `python app.py` and `bokeh serve app.py`; the app never runs without a
     token: started with none, it makes its own, writes its link to a 0600
     file and prints only that file's path; the key is never printed, except
     when no link file can be written in any folder dash tries: then one
     warning line and the link alone are printed once, to the output of
     whoever started the server, which keeps serving; `/health` and BokehJS
     static files stay open; tokens are compared in constant time (P0.12a).
   ~~~~

   ~~~~markdown
   - **BR-29.11** Private files: every temporary copy of the data lives in a
     per-user directory dash makes 0700, and every file is created 0600; a
     location that cannot be kept private (a `c(tmpdir)` other accounts can
     change, a disk that keeps no permissions, a `dash-<uid>` that is not the
     user's own folder) is never refused: dash proceeds, leaves a planted
     `dash-<uid>` alone for a 0700 fallback, and prints one note naming the
     location; as an anti-hijack guard, not for privacy, no write goes
     through a symbolic link, into a FIFO or device, or over a hard-linked or
     another account's file, and no replaced app file is started, each ending
     r(7102); dash starts its served app only from the bytes it wrote, read
     through a descriptor it opened and verified, never by path, so an app
     file swapped in after that check never runs; one-line preview pages are
     private and bounded (unique names, 0600 in a 0700 folder; a session
     keeps its newest five; `dash clear` removes the session's pages except
     one a browser was asked to open in the last 60 s; another session's
     pages are removed only once that session is dead or the page is more
     than 24 h old; all sessions together keep at most 25); a server app the
     user names is written 0600 into the folder the user names, which is
     never refused or re-moded, and pages the user names keep twoway's umask
     semantics (P0.12b, P0.14).
   ~~~~

   ~~~~markdown
   - **AC-29.6** The security tests are green: no session, page or data
     without the token, and an app started without one makes its own and
     prints only its link file's path, or, when no link file can be written
     anywhere, prints the link once after a warning line and keeps serving;
     0600 files in a 0700 root wherever the disk keeps permissions; a
     location that is not private proceeds with one note, never an error; a
     link, FIFO or device, hard-linked or foreign file at a target, or a
     replaced app, refused r(7102); an app path swapped after the launch's
     check runs nothing but the verified bytes; every preview page 0600 in a
     0700 folder, at most five per session and 25 in all, removed by `dash
     clear` (except a page a browser was asked to open in the last 60 s) and
     once its session is dead; the app exits within the grace period after
     its parent dies; Break ends `dash serve` with r(1); no non-finite number
     in page JSON; no saved-page cell outside BR-29.9, and no served `index`
     value that is an original observation number.
   ~~~~

   The bullets sit in ROADMAP.md at column 0 with a two-space continuation indent, as Appendix D's do. The three-space indent above belongs to this list only.
2. **CHANGELOG.md.** Place the 26 markers listed in `index.md` "P0 coverage": one per list cell; P0.1, P0.5, P0.6, P0.12a and P0.13 have two. Put the new `### Fixed in WP-29` heading above `### Fixed in WP-28` (CHANGELOG.md:466) and the group `**WP-29 (drop-in P0, 30sep2026)**` at the end of `### Results that change`.
3. **BUGS.md.** Append the 21 open entries (titles in `index.md`) at the end of the file, in P0 order, in the five-field form. Each entry's:
   - **File Names and Line Numbers** gives HEAD anchors from the reviewed design;
   - **Description** quotes the DROPIN text and its source ids;
   - **Resolution** reads `Not fixed because WP-29 section <NN> has not landed. Graded S<n> (WP-29): <why>.` That form satisfies `TestEveryOpenEntrySaysWhyItIsOpen` (:458) and `test_every_open_entry_is_graded_once` (:494).

   An open entry names no test file or case id, because the reference checker (:367) would read a test that does not exist yet as dangling.
4. **`test/test_tracking_documents.py`.**
   - Add `WP29_OPEN = {"P0.1": "<title>", ...}` (21 keys, one per line, in P0 order) and `WP29_ALL = (...)` (the 21 ids, permanent).
   - `test_no_open_entry_is_s1_or_s2` skips titles in `WP29_OPEN.values()`.
   - Add `TestWp29Tracking` with four tests:
     - `test_every_allowed_title_is_an_open_entry` (stale allowance → red);
     - `test_an_open_p0_keeps_its_marker` (every id in `WP29_OPEN` has at least one `<!-- WP-29 <id> -->` in CHANGELOG.md);
     - `test_a_closed_p0_has_no_marker_and_a_resolution` (every id in `WP29_ALL` but not in `WP29_OPEN` has no marker, and some closed entry's Resolution holds `(WP-29, <id>)`);
     - `test_the_marker_reader` (inline fixtures, both directions).
5. **`test/test_wp29_truth.cscript`.** The scaffold copies `test_gaps2_truth.cscript`'s frame:
   - the header comment listing blocks as they land;
   - the `cscript` line with `adodir ".."`;
   - `do "cert_helpers.do"` and `cert_svg.do`;
   - its own `c(python_exec)` gate line;
   - one smoke block `S01` (`W29-01 PASS`: the helper loads and one `twoway scatter` SVG is read);
   - the marker `* ==== append new blocks above this line ====`;
   - the failure summary, which exits 9.
6. **Runner and hygiene.** Add block `// 68.` to `test/run_all_cscripts.do` after `// 67.` (:1716-1740) and before `// Summary`. Set `test/test_cscript_hygiene.py` pins to 67 (:295) and 49 (:313), and update the comments.
7. **Verify:**
   - `test_tracking_documents.py`, `test_cscript_hygiene.py` and `test_packaging.py` are green;
   - the driver run of `test_wp29_truth.cscript` prints `W29-01 PASS`;
   - the full suite is green;
   - `gitnexus_detect_changes()` lists only these files.
8. **Commit** `Open the WP-29 P0 entries, markers and truth script (WP-29 S01)`.

### S15 — Closeout (main checkout, one commit per step, `(WP-29 S15.<k>)`)

1. **S15.1 Tracking.** Confirm the following:
   - `WP29_OPEN` is empty. Then replace the dict with `WP29_OPEN = {}` and add `test_no_wp29_entry_remains_open`.
   - No `<!-- WP-29 ` marker is left in CHANGELOG.md.
   - Every closed entry names tests that exist.
2. **S15.2 GAPS2 / REMAINING / AUDIT / DROPIN / GAPS.**
   - For each GAPS2 id a P0 source names, decide FULLY closed or PARTLY closed, citing the sub-items and the commits.
   - A fully closed id gets the Tracked line `Closed in WP-29, BUGS.md "<title>", commit <sha>`, is listed in ROADMAP's `**GAPS2 closed:**`, and gets `(WP-29, <id>)` appended to that entry's Resolution.
   - A partly closed id gets the Tracked line `Partly closed in WP-29 (P0.<n>, commit <sha>); open: <what>`, which matches neither `_GAPS2_CLOSED` nor `_GAPS2_DEFERRED`.
   - Mark the REMAINING.md and AUDIT rows the same way.
   - Annotate each P0 line of DROPIN-REMAINING.md with its commit.
   - Correct GAPS.md's served-auth status text if the token makes it false.
3. **S15.3 ROADMAP.** Head WP-29 `— DONE`, fill `**GAPS2 closed:**` and record the measured results, including the cert wall time. Check that ROADMAP's BR-29.6, BR-29.7, BR-29.9, BR-29.10, BR-29.11 and AC-29.6 read as §7 S01 item 1's text. Then run `test_tracking_documents.py`.
   - PLAN.md was amended before execution, so these no longer apply: section 15's R15-8 (PLAN.md left stale and named in the report), its Appendix D.10 rewording and step 15-10's "BR-29.11/AC-29.6 rewording".
   - S15 makes no ROADMAP rewording, and its report lists no superseded PLAN.md sentence.
   - If a section changes one of these requirements later, the change is made in PLAN.md and ROADMAP.md together, before that section's commit.
4. **S15.4 AGENTS.md.** Add "Invariants introduced by WP-29" (beside `## Invariants introduced by WP-28`, AGENTS.md:23), each with its test:
   - join order;
   - Stata units;
   - the private root and 0600 writer (a location that is not private is noted, never refused; the anti-hijack guards end r(7102)), and the launch from the verified bytes, never by path (round 2, answer B; `TestTheLaunchFromTheOpenFile::test_a_path_swapped_after_verification_does_not_change_what_runs`);
   - the token (never missing: a hand-started app makes its own; never printed except K-9's once-only warned fallback, round 2 answer A) and 127.0.0.1;
   - the parent watch;
   - embed rows (both modes number the rows they send by rank; the served `index` carries no observation number);
   - the `lpvar` key;
   - build-time served notes.
5. **S15.5 Help consistency.** Run `test_help_claims_*.py` and every `test_help_claims_*.cscript`. Read through dash.sthlp and dash_setup.sthlp for contradictions between the sections' sentences.
6. **S15.6 Release run.** Run each of these once: `make test`, `make test-dev`, `make cert` (timed against `<scratch>/wp29-cert-baseline.log`; report the delta), and `make gate`. A red result goes back to the owning section's fix cycle.
7. **S15.7 Report.** Report the merge command `git checkout main && git merge --no-ff wp29-p0` without running it (rule 5). List the residuals and the GAPS2 ids that are only partly closed, and the documented divergences and residuals the 01oct2026 ratification introduced (the kept date axis under a first computed date layer; the spec and data read by path in a shared non-sticky `c(tmpdir)` (the app-substitution window is closed by section-08 R-9, round 2); a `.py` the user runs by hand, opened by name; the launch from the open file unmeasured on Linux and Windows; the `bokeh serve` first session refused while the self-made key is made; the link printed once, after a warning, when no link file can be written anywhere (section 13 K-9, round 2), which puts the key in that output and its log). The served `index` is not a residual.

## 8. Risk register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| K1 | 13 sections edit `dash_render.py` (32,205 lines), and 9 of them in parallel | high | merge conflicts, lost hunks | Symbol-disjoint sections (A1); merge order with reasons; `patch -p1` per commit; R2 anchors spread across the tuples; the full suite and parity guard after every batch | merger |
| K2 | S03's `make_data_json` change silently alters what 96 test files see | high | false greens or reds in other sections | A7: new tests pass labels explicitly; S03 merges first among the renderer sections; R7 re-measures the complete red list; the SHA-256 page baseline is never re-baselined | S03 |
| K3 | Pins that assert x order or the bootstrap band are deleted rather than flipped | medium | lost coverage | R7; a `Flipped:` line per test in the commit body; the reviewer counts test nodes before and after (`pytest --collect-only -q \| wc -l` never falls) | S02, S11 |
| K4 | The lpoly port drifts from Stata at extreme scales | medium | wrong published numbers | Port invsym's relative AND absolute (1e-19) pivot rules (u07a A1/A2); fixture rows at weight×1e-5..1e-100 including Stata's `.`; per-row tolerances of S11 SD-1 (`exact` 1e-7 and `noisy` 5e-5 relative on `r(bwidth)`; the band at given widths 1e-8·max(1,|y|)); degrees 0-3 drawn and checked against Stata, degree 4-7 constants unit-tested only (SD-7; degree 4/5 fixture rows at 5e-4); the served recompute is tested after a move | S11 |
| K5 | Security regressions: token theft (IPv6 squat, Referer, logs), FIFO or symlink hang in the writer, `realpath` breaking prefix checks, NaN in page JSON, SMCL in echoed expressions; since the 01oct2026 ratification also: a spec or data file replaced in a shared non-sticky `c(tmpdir)` between dash.ado's write and the renderer's read (no r(603) refusal any more), a self-made key whose link file cannot be kept private, a link printed once when no link file can be written (round 2), and served `index` labels that are not relabelled | medium | data exposure, hang, broken page | A9; u11b A2/A3 (lstat/fstat, `O_NONBLOCK` then clear, never `os.umask`); u08 A1 (no non-finite JSON, tested with node `JSON.parse`); `_dash_say` for echoes; bounded lengths; `hmac.compare_digest`; S08 R-8's anti-hijack guards and the launch from the open file (R-9, TR-08.8a), with the inputs' residual named in the note; S13 K-8 (the link file 0600 wherever the disk allows, else written with one note) and K-9 (round 2: when no folder takes it, one warning line and the link printed exactly once, the server kept serving, pinned by its print-once tests); S14's `_dash_relabel` raises on a map not indexed like the frame, and 14-11 audits row-keyed captures; a security test per threat | S04, S05, S08, S13, S14 |
| K6 | A served-only note is printed in a session whose output never reaches the Stata log | medium | silent served divergence | R6: build-time decision helpers (u02 amendment); a cscript checks that `dash build, server` logs the note once | S10 |
| K7 | The served-name guard misses `__main__`-only names | medium | served app NameError at launch | S08 extends `TestTheServedAppDefinesEveryNameItReads` to the module-level `__main__` block before adding names (u12 A3) | S08 |
| K8 | Break is swallowed (`sfi.BreakError` is an `Exception`), or the interrupt turns into r(198) | medium | serve cannot be stopped | u12 A1/A2: poll outside `try/except Exception`; `_DashServeInterrupted(Exception)`, not RuntimeError; a test for Break on the first poll | S08 |
| K9 | Stata concurrency drops `python_exec` from `stata19.rc` | low | cscripts skip, a false green | `scripts/stata_slot.sh` (three slots); a SKIP is not a pass; G8 counts PASS lines | all |
| K10 | Evaluating `function` in Stata changes RNG state or validation order, or grows the spec (about 250 KB per n(10000) layer) | medium | RNG drift vs twoway; limit refusals | u06 A2: evaluate after the segment loop and by() checks, before graph options, matching twoway's measured order; `%24.17g`; count the points against the existing byte cap | S04 |
| K11 | Embed restriction breaks KPI text qualifiers or adds a "(missing)" colour key | high without S07 | wrong legend or cards | S14 depends on S07 (colorvar from view rows); restrict at embed points only, never frame-wide; csv keeps every row (u10 A1/A2) | S14 |
| K12 | The tracking allowance is forgotten, so the suite goes red or an entry is closed without its marker | medium | red merge | `TestWp29Tracking` fails the section's own G5 before its commit | each section |
| K13 | The cert suite gets slower | medium | release friction | Truth blocks are gated and timed per block; S15 reports the wall-time delta against step 0b | S15 |
| K14 | PEP 668 behaviour on hosts that were never measured (Windows, Linux) | high | wrong printed command | Sandbox tests for `cmd.exe` and POSIX quoting; `resolve_exe`; detection in a child process (u15 A1/A2); the residual is recorded by S15 | S09 |
| K15 | Data-order joins change users' published line plots | certain | do-files need `sort` | "Results that change" and "Changed behaviour" CHANGELOG lines; the help states twoway's rule | S02 |
| K16 | The launch from the open file (round 2, answer B) changes how every served app starts: a bootstrap that differs from a script run (`sys.path`, `__main__`, argv, tracebacks, exit codes), a hand-over that blocks, or a bootstrap that reads stdin through a buffer and swallows S13's key line; Linux and Windows are unmeasured | medium | every served dashboard broken, `dash serve` hangs, or the key line lost | Section 08 R-9/TR-08.8a: `python -P -c _DASH_BOOT`, the frame read with `os.read(0)` only, the hand-over inside F4's single try after the pumps start; `TestTheBootstrap` (script-run parity) and every real launch test (`TestServeBlocksUntilCtrlC`, HC4-19, LC-01, LC-03) run the bootstrap end to end; S13 task 13-01 step 7 stops if the child reads stdin through a buffer; S15.7 reports Linux and Windows as unmeasured | S08, S13 |

## 9. Success criteria and exit gates

- **E1 (AC-29.1)** 21 BUGS.md entries opened by S01 are closed. Each has a Resolution `(WP-29, P0.<n>)` naming tests that exist, and `WP29_OPEN` is empty.
- **E2 (AC-29.2)** Each P0 entry's fix commit body opens with its saved failure text. For every regression test there is a `Regression:` line, so the red-first evidence is on record.
- **E3 (AC-29.3)** `test/test_wp29_truth.cscript` runs every section block with every case `PASS` and no SKIP, on a machine with Python. Its fixtures carry the D12 `_meta` stamp and are committed.
- **E4 (AC-29.4)** `test/test_mode_parity.py` is green with every section's CORPUS cases, and `ALLOWED` is unchanged.
- **E5 (AC-29.5)** Both served-name guards are green, and the `__main__` block is covered.
- **E6 (AC-29.6)** These security tests are green:
  - a request without, or with a wrong, token gets no session, page or data; an app started without a token (`python app.py`, `bokeh serve app.py`) makes its own 43-character key, writes its link to a 0600 file in a 0700 folder, prints only that file's path and still refuses every session without the key; an invalid supplied token is refused at start (section 13 K-1..K-8, ratified 01oct2026); when no link file can be written anywhere, the link is printed once after `_DASH_LINK_UNWRITTEN` and the server keeps serving, under `dash serve`, `python app.py` and `bokeh serve` (section 13 K-9, round 2);
  - every file under the private root is 0600 and the root is 0700, wherever the disk keeps permissions;
  - a location that is not private (a shared `c(tmpdir)`, a planted `dash-<uid>`, a disk that keeps no permissions) is never refused: the command gives rc 0 and prints one note per command, and a planted root is left alone for a private fallback; a folder the user names is neither refused, re-moded nor noted (section 08 R-8, PF-09, PF-12);
  - the anti-hijack guards refuse with r(7102): a link, FIFO or device, hard-linked or foreign file at the target name, a name that appears mid-write, and an `app.py` replaced after it was written (section 08 R-8, TR-08.8); a path swapped after the launch's verification runs nothing but the verified bytes, and no module beside the app or in the working folder is imported (section 08 R-9, `TestTheLaunchFromTheOpenFile`, round 2);
  - every one-line preview page is 0600 in a 0700 folder. At most five are kept per session and 25 across sessions. `dash clear` removes them, except a page a browser was asked to open in the last 60 s, and so does the death of their session (BR-29.11; section 08 `TestThePreviews`, PF-02, PF-04);
  - the app exits within the grace period after its parent dies;
  - Break ends `dash serve` with r(1);
  - no non-finite number reaches page JSON;
  - the saved page holds no cell outside BR-29.9, and no `index` value either mode sends is an original observation number (section 14 `TestTheServedIndexIsARank`, ratified 01oct2026).
- **E7 (AC-29.7)** CHANGELOG.md holds no `<!-- WP-29 ` marker. Every WP-29 line ends `(WP-29, P0.<n>)`, and each Results line names the command, the old value and the new.
- **E8 (AC-29.8)** ROADMAP WP-29 is headed DONE. Its `**GAPS2 closed:**` ids each have `Closed in WP-29` Tracked lines with commits that exist. `test_tracking_documents.py` is green.
- **E9 (AC-29.9)** `make test`, `make test-dev`, `make cert` and `make gate` are each green once on `wp29-p0`, and the cert wall time is reported against the step-0b baseline.
- **E10 (AC-29.10)** No commit message on `wp29-p0` since `7421d3d` matches `claude|anthropic` (case-insensitive). `CLAUDE.md` and `.gitignore` are not in any WP-29 commit.
- **E11 (AC-29.11)** `gitnexus_detect_changes()` before each commit showed only the section's symbols, and every HIGH/CRITICAL impact was reported before its edit.
- **E12 (AC-29.12)** The merge command into `main` is reported and not run. Worktrees are removed.

## 10. Traceability

| P0 | Units | Section | Sources (DROPIN-REMAINING.md) |
|---|---|---|---|
| P0.1 | u01 | 02 | GAPS2-A1-a, AUDIT-08, REM-§2-S06-sort, REM-S06-b, GAPS2-A4-o, GAPS2-B12-e, AUDIT-10, GAPS2-G15-b, GAPS2-A1-c |
| P0.2 | u02 | 10 | GAPS2-B4-a, GAPS2-B4-b |
| P0.3 | u03 | 03 | REM-08-05-C3b, REM-08-05-C3a, REM-08-05-M3 |
| P0.4 | u04 | 03 | CRIT-01 |
| P0.5 | u05 | 10 | REM-09-02-AXIS-N, GAPS2-B15-a, AUDIT-27, GAPS2-B22-c |
| P0.6 | u06 | 04 | GAPS2-A6-d, GAPS2-C5-g, GAPS2-A6-c |
| P0.7 | u07a | 11 | GAPS2-A9-a, GAPS2-A9-b, GAPS2-C1, GAPS2-C13, AUDIT-24, GAPS2-C12-e |
| P0.8 | u08 | 05 | REM-08-05-C6d, REM-08-04-C2, REM-08-05-C6c, REM-08-04-C3a, REM-08-04-C12 |
| P0.9 | u07b | 11 | AUDIT-23, GAPS2-A10-a, GAPS2-C7-a, GAPS2-C7-b, GAPS2-A10-b, GAPS2-C7-c, GAPS2-C7-e |
| P0.10 | u09 | 06 | REM-09-07-HOVER-EXPORT, GAPS2-G16-res, REM-09-07-HOVER-TEST |
| P0.11 | u10 | 14 | GAPS2-I2-a, GAPS2-I2-b |
| P0.12a | u11a | 13 | GAPS2-I3-a, GAPS2-I3-c, AUDIT-87 |
| P0.12b | u11b | 08 | GAPS2-I3-b, GAPS2-I3-c, AUDIT-87 |
| P0.13 | u12 | 08 | GAPS2-F2a, GAPS2-F2b, GAPS2-F4, GAPS2-H2a, GAPS2-F9c, GAPS2-H2b |
| P0.14 | u11b | 08 | GAPS2-X3-a, GAPS2-X3-b, GAPS2-X3-c |
| P0.15 | u13 | 07 | REM-06-06-C7 |
| P0.16 | u13 | 07 | REM-06-06-C8b, REM-06-06-C8b-link |
| P0.17 | u14 | 12 | GAPS2-C4, GAPS2-E4a, GAPS2-E4c, AUDIT-38 |
| P0.18 | u14 | 12 | REM-15-03-C15 |
| P0.19 | u15 | 09 | GAPS2-H7a-g (sub-ids inferred from the item's text order), plus N1-N4 found during measurement |
| P0.20 | u08 | 05 | GAPS2-E1-residual |
