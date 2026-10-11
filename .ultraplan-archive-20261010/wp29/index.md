# Section Index — WP-29: close the drop-in P0 gaps

> Architect pass, 30sep2026, on branch `wp29-p0` (main `357c368` + the report commit `7421d3d`). Source: `.ultraplan/handoff/DROPIN-REMAINING.md` §3 "### P0" (lines 35-62), 20 items, each verified at HEAD with source ids into `GAPS2.md`, `REMAINING.md` and `TWOWAY_COVERAGE_AUDIT.md`. Package-level context, goals, user stories, business requirements, risks and exit gates are in `PLAN.md` beside this file.
>
> WP-29 reuses `.ultraplan/sections/BRIEF.md` (WP-28's writing brief) **unchanged except where the "Deltas from BRIEF.md" table below says otherwise**. A section file for WP-29 is written to BRIEF.md's layout (Review amendments, Overview, Risk, Dependencies, Evidence, User stories, Business requirements, Technical requirements, Boundaries, Stata truth, TDD test stubs, Test plan, Tasks in BRIEF's XML schema, Section completion criteria, Notes).

## Overview

- **Total sections:** 15 (01 tracking foundation, 13 fix sections, 15 closeout)
- **Work units:** 16 reviewed designs (u01-u15, u07 and u11 split a/b), all "sound with amendments"; every amendment is binding on the section that carries the unit.
- **P0 items:** 20, tracked as 21 BUGS.md entries (P0.12 splits into P0.12a credential and P0.12b files, because two sections in two batches close them).
- **Fix commits:** 21 (one per P0 entry, except P0.13, which lands as two: F2 then F4), plus two S00 commits (the plan, round 2 answer C, and the audit), S01 and five or six closeout commits (S15.1, S15.2, S15.3, S15.4, S15.6 only if the release date must move, S15.7; S15.5 commits nothing).
- **Parallel batches:** 5 (batch 0: S01 alone; batch 1: 8 sections; batch 2: 4, with S12 cut in a second wave after S10 and S11 land; batch 3: 1; batch 4: the closeout).
- **Full-suite runs planned:** 35 pytest runs and 2 certification runs, serialised machine-wide (see "Full-suite runs").
- **Risk:** 2 green, 6 yellow, 7 red.

## Decision record

### Maintainer decisions (binding; a section must not contradict them)

| Id | Item | Decision |
|---|---|---|
| M1 | P0.1 line order | MATCH twoway. line, connected, area, rline, rarea, rconnected (and every other connecting type) join in data order unless `sort` or `sort(varlist)` is given; `sort(varlist)` is honoured. Existing tests that pin x order are FLIPPED (with the reason), never deleted. |
| M2 | P0.7 / P0.9 lpoly | PORT Stata's arithmetic to Python: the per-kernel, per-degree rule-of-thumb default bandwidth, and lpolyci's analytic CI band with `pwidth()` and `var()`. Verified against Stata truth fixtures. Must hold in served recomputes after a filter move. The bootstrap band is removed. |
| M3 | P0.17 saved-page refit | A VISIBLE STALE CUE on computed layers (fits, smooths, densities that are frozen) on the saved page after a filter move. The served app keeps refitting. No JavaScript estimator port. |
| M4 | P0.12 served auth | A per-launch secret TOKEN required by the served app (Stata opens the tokenized URL); the app, spec and data files are written 0600 inside a 0700 directory. *Ratified answers of 01oct2026 (binding reading):* the token is never missing, because an app started by hand makes its own (S13 K-1..K-8); and "0600 inside a 0700 directory" holds wherever the location allows: a location that is not private is noted, never refused, and a folder the user names is never refused or re-moded (S08 R-8). *Round 2 (01oct2026, binding):* the key is never printed, except once, after a warning line, when no link file can be written anywhere, and the server keeps serving (S13 K-9, answer A); dash starts its served app only from the bytes it read through a descriptor it opened and verified, never by path (S08 R-9, answer B). |

### Architect decisions (this pass; the section files inherit them)

| Id | Decision | Why |
|---|---|---|
| A1 | Units are grouped into 13 fix sections (table below). u03+u04, u05+u02, u07a+u07b, u11b+u12 and u13 are combined or kept whole by shared symbols; every other unit is its own section. | Shared functions (`_dash_axis_labels`; `_dash_apply_scale_ranges`/`_dash_add_secondary_axes`; the lpoly helpers and `_stata_invsym_keep`; the serve launcher and private temp root) would otherwise be edited by two parallel worktrees. |
| A2 | The u02 ↔ u05 dependency cycle is broken by putting both in section 10, P0.5 committed first, then P0.2. | u02 needs u05's axis(2) routing of `range()` on y2/x2; u05's "depends on u02" is only `_dash_apply_scale_ranges` merge order. |
| A3 | One new certification script only: `test/test_wp29_truth.cscript`, created and registered by S01 as runner block `// 68.`. u11a's planned `test/test_serve_token.cscript` is NOT created; its TOK cases go into the existing `test/test_serve_launch.cscript`. Every design's "block in `test_gaps2_truth.cscript`" goes into `test_wp29_truth.cscript` instead. | BRIEF R1 (one script per package, owned by the foundation); keeps the runner and the hygiene pins in one section. |
| A4 | S01 opens one BUGS.md entry per P0 entry (21) in the open form, graded, and an allowance `WP29_OPEN` in `test/test_tracking_documents.py` exempts exactly those titles from `TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2` (test_tracking_documents.py:503-510). Each fix section closes ITS entry IN PLACE (`- [ ]` → `- [x]`, Resolution rewritten) and deletes its own key from `WP29_OPEN` in the same commit. | Without the allowance S01's open S1 entries turn the suite red (rule 4). In-place closure gives each section disjoint BUGS.md hunks instead of end-of-file append conflicts. Precedent: `WP23_OPEN_UNTIL_INTEGRATION` (test_tracking_documents.py:60-65). |
| A5 | Only S15 edits the cross-package tracking documents: `ROADMAP.md` (beyond S01's entry), `GAPS2.md` Tracked lines, `GAPS.md`, `REMAINING.md`, `TWOWAY_COVERAGE_AUDIT.md`, `.ultraplan/handoff/DROPIN-REMAINING.md` and `AGENTS.md`. Designs that list these files (u02, u05, u07a, u08, u09, u10, u11a, u11b, u12, u13, u14, u15) hand their text to S15 through their section file's "Notes for the closeout" paragraph instead. | GAPS2 Tracked lines must name the fix commit's sha on `wp29-p0`, which exists only after merge; one editor removes every tracking-document conflict. |
| A6 | `TWOWAY_COVERAGE_AUDIT.md` (untracked at plan time, 214 lines; the P0 sources cite its AUDIT-nn rows) is committed by step 0a on `wp29-p0` together with its name in `test/test_packaging.py::_ROOT_ALSO` (test_packaging.py:426-430), before any worktree is cut. Step 0a also commits `.ultraplan/wp29/`, in its own commit (round 2, answer C; "Plan files" delta). The maintainer's uncommitted `CLAUDE.md` and `.gitignore` edits are never staged by any step. | `test_the_package_root_holds_only_what_ships_and_the_repositorys_own` refuses an unlisted root file; worktrees are cut from HEAD and must carry the cited audit. |
| A7 | S03 changes `test/conftest.py::make_data_json` so variables are unlabelled unless a test passes labels. Every other batch-1 section's NEW tests pass `var_labels` explicitly wherever they assert label text, so they are independent of S03's change. S03 merges first among the renderer sections. | u03 amendment A1 measured 11 failures in 15 files beyond the 3 the design named, from 96 files that use the helper. |
| A8 | lpolyci's option key for `var()` is `lpvar`, never `var` (u07b blocker). | `_dash_extract_vars` (dash_parse.mata:2148) treats every `"var":` in a plot's JSON as a variable name. |
| A9 | Every tokenized URL uses `127.0.0.1` (or the explicit `--address`), never `localhost` (u11a A1, A2). | An IPv6 squatter on `[::1]:P` receives a `localhost` token (measured, `wp29/r-u11a/squat.py`). |
| A10 | Commit subjects end `(WP-29 P0.<n>)` (`(WP-29 P0.12b, P0.14)` for the private-files commit; `(WP-29 P0.13 F2)` / `(WP-29 P0.13 F4)` for the two lifecycle commits; `(WP-29 S00)`, `(WP-29 S01)`, `(WP-29 S15.<k>)` for the non-fix commits). | BRIEF's D1 rule with WP-29 ids. |

### Deltas from BRIEF.md (everything not listed applies as written)

| BRIEF rule | WP-29 form |
|---|---|
| Base commit for "fails at" | The `wp29-p0` HEAD a section's worktree was cut from, recorded in `<scratch>/batch-<k>-base.txt`: `batch-0-base.txt` by step 0d (the step-0a commit; S01's "failed at" sha), `batch-1-base.txt` by step 1 after S01 has landed, and `batch-<k+1>-base.txt` after batch k is green. One exception, S12 (section-12 critic amendment C1, 12 ← 11): its base is `<scratch>/batch-2-s12-base.txt`, recorded by the merger once S10 and S11 have landed and the interim full run is green ("Batch 2"); it is S12's worktree base and its P0.17 "failed at" sha. Regression lines read `-- failed at <sha> with <text>`. |
| Integration branch / worktree branch | `wp29-p0` / `wp29-s<NN>`, worktree path `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s<NN>`. |
| Truth script | `test/test_wp29_truth.cscript`, gated by env `WP29_ONLY=S<NN>`; block header `* ==== S<NN> P0.<n>: <what> ====`; marker line `* ==== append new blocks above this line ====`; blocks in section-number order. |
| CHANGELOG markers | `<!-- WP-29 P0.<n> -->` (and `P0.12a`, `P0.12b`), placed by S01 in the release `## 0.1.0, 30sep2026 (release candidate)`: a `**WP-29 (drop-in P0, 30sep2026)**` group at the end of `### Results that change` (CHANGELOG.md:10), the ends of `### Security` (:238), `### Changed behaviour (may need your do-files changed)` (:376) and `### Requirements` (:448), and a new `### Fixed in WP-29` heading placed directly above `### Fixed in WP-28` (:466). A closing task replaces only its own marker(s) in place with line(s) ending `(WP-29, P0.<n>)`. |
| BUGS.md | Entries are OPENED by S01 (A4) and closed in place by the fix section: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.<n>). <what changed, where, both renderers>. Pinned by test/<file>.py::<Class>::<test>[, test/<script>.cscript <CASE-ID>][; fixture test/fixtures/<name>.json]. [Residual, deferred (WP-29): ...]` S15 appends `(WP-29, <GAPS2 id>)` to a Resolution only when it marks that GAPS2 id Closed (test_tracking_documents.py:1139-1184 requires that text). |
| Tracking docs | A5: S15 only. |
| Copy-list anchors | The R2 table below (HEAD `7421d3d`: `ServerAppBuilder._glyph_layer_lines` (def 28312) holds the constants tuple dash_render.py:28362-28497 and the functions tuple 28535-28829; `ServerAppBuilder._shared_stat_lines` (def 28889) holds its own function tuple, with `_dash_lpoly_weights` at 28965). |
| Section numbers in case ids | Each section's new cscript case ids use the prefix the manifest assigns (checked unused at `7421d3d`); a section greps `test/*.cscript test/*.py` for its prefix before first use. |
| Evidence from the design reviews | The reviewers' scratch evidence lives under the session scratchpad `.../scratchpad/wp29/<unit>[-review]/`, which does not survive the session. A section file QUOTES the measurements it relies on (command and output); it never cites a scratch path as the only evidence. |
| Stata invocation and browsers | Stata runs only as `scripts/stata_slot.sh <scratch> <file>.do` (rule 10). dash reads only the GLOBAL `$dash_nobrowser` (`if "${dash_nobrowser}" != ""`, dash.ado:5184, 5226, 5306); no ado, do, cscript, mata or py file maps an environment variable to it, so `dash_nobrowser=1` in the environment has NO effect (harmless where a section's command line still carries it). Every non-cscript do-file that runs dash (an extract script, a probe, a driver such as S08 task 08-19's signal driver) sets `global dash_nobrowser 1` on the line right after `adopath ++ "<repo>/"`. A cscript gets the global from `test/cert_helpers.do:51`. |
| Plan files | `.ultraplan/wp29/` is committed on `wp29-p0` by step 0a, in its own commit, before any worktree is cut (ratified 01oct2026, round 2, answer C: "Commit them"), so every worktree holds the plan as it stood at that worktree's base. Agents may still read `index.md`, `PLAN.md` and the section files (with their verbatim appendices, e.g. S01 Appendices A-G, S15 Appendices A-F) by absolute path under `/Users/billy/Desktop/Programs/StataPrograms/d/dash/.ultraplan/wp29/` (step 0e); the files are tracked, and the main checkout's copy governs. No section commit edits or stages a plan file (G6). If the orchestrator amends a plan file after step 0a, it commits that amendment alone on `wp29-p0`, with a message that has no AI reference (G7), before the next batch base is recorded. `.ultraplan/sections/BRIEF.md` is tracked and is in every worktree. |
| Full suite | "Full-suite runs" below replaces every section's "run the full suite once" wording: one run per commit, serialised machine-wide, waited for, never relaunched to check on, and prefixed `FULL_SUITE_RERUN=1`. |
| Pull from main (rule 4) | Before each pre-commit full run: `git -C <wt> merge --no-edit main` (expect `Already up to date.`; if main moved, stop and report). The merger does the same in the main checkout before each landed commit. |
| GitNexus (CLAUDE.md) | R8: one index, of the main checkout, built by the maintainer (step 0c only checks it) and rebuilt after each batch lands; `gitnexus analyze` never runs in a worktree. |

### Decisions for maintainer ratification (ratified 01oct2026, at plan time; round 2 the same day)

The section files used to leave these decisions to a checkpoint inside a parallel batch. A stop there would halt a worktree mid-batch, and D05-1's alternative changes pins that S10, S11 and S12 build on. So they were settled before any section runs: the maintainer answered on 01oct2026, every row's last column is filled below, and each struck decision has already been applied to its section file (section-05, -08, -13 and -14 each open their "Review amendments" with a "Ratified 01oct2026:" line) and to this file, PLAN.md, section-01, section-11 LW-05 and section-15. A second round on 01oct2026 answered three more questions (round 2, below); its rows are the last three of the table, and section-08 and -13 open their "Review amendments" with a "Ratified 01oct2026 (round 2):" line, and this file, PLAN.md, section-01 and section-15 are reconciled with it. Step 0f only copies this record into `<scratch>/wp29-ratified.txt`. **Step 1 does not start until that file exists and holds every row below with no "pending".**

**The maintainer's answers, 01oct2026, verbatim** (the numbering is the maintainer's):

1. "Keep the date axis."
2. "Allow "unsafe" temp directory locations and do not refuse writing the app files into a directory of the user's that is not private."
3. "Ensure that the token will never be missing."
4. "Resolve the server app's index known gap."

How they map to the rows: answer 1 strikes D05-1; answer 2 strikes "S08 codes"; answer 3 strikes item (1) of "S13 1-8"; answer 4 strikes SD3's served half (the served `index` residual) of "S14 SD1-SD6". The answers name no other row, and the orchestrator recorded every other row as ratified as written.

**The maintainer's answers, round 2, 01oct2026, verbatim** (each question's short name, then the choice; the lettering is the maintainer's):

A. Token link failure: "Print the URL once".
B. App swap in a shared non-sticky temp folder: "Launch from open file".
C. Commit the plan: "Commit them".

How they map to the rows: A strikes row "S13 K-8" (the stop when no link file can be written) and amends item (5) of "S13 1-8" and item (a) of "S13 (a)-(e)" to "never printed, except this fallback"; B strikes row "S08 launch route" (launch by path after an identity check, with the app-substitution window as a residual) in favour of the launch from the open, verified file; C strikes row "S00 plan files" (the plan never committed). Round 1 stays in force.

| Id | Section (checkpoint that used to ask) | Decision as the section takes it | If struck | Ratified |
|---|---|---|---|---|
| D05-1 | S05 (none; "may strike at plan review") | twoway's first-plot axis rule (A9): when every layer is computed and the first is `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci`, the axis is numeric and the layers are drawn in Stata units. A computed type first followed by a plotted variable keeps dash's date axis (documented divergence, P1.23). | S05 drops TR-05.10's second rule, the A9 cases of `TestTheAxisRule` and the A9 halves of the 05-07 flips, and its help names lone `kdensity <date>` as a divergence. S10, S11 and S12 re-derive any date-axis pin at their batch base. | 01oct2026 struck (answer 1): keep the date axis. dash keeps its date axis when every layer is computed and the first is `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci` over a date; those layers are still COMPUTED in Stata units (P0.8) and drawn at their dates. The 12 measured cases where twoway labels numbers are one documented divergence, pinned by `TestTheAxisRule::test_a_unit_labelled_first_layer_keeps_the_date_axis` and named in the help, as is a lone `kdensity <date>, range()` dropping points before 01jan0100. Applied in section-05 (TR-05.10's second rule dropped, no `_DASH_UNIT_LABELLED_TYPES`) and section-11 LW-05 (drawn x in epoch ms); S10 and S12 need no text change. |
| S08 R-1 | S08 (08-01) | One erase rule, `_dash_private_run_of`; no `--ephemeral` renderer flag. A command-line user's files are never erased. | The orchestrator re-plans S08's commit 1 and F2 before batch 1. | 01oct2026 ratified |
| S08 R-3 | S08 (08-01) | Only `_dash_watch_parent` joins the served copy list. The private-file helpers are not copied, because the app writes no file (R2). | R2's S08 row is changed to add the named helpers. | 01oct2026 ratified for S08's three commits. Answer 3 later makes the app write its own `link.html`; S13 does that with its own copied `_dash_private_page` (TR-13.8a), not S08's helpers, and flips S08's no-file guard ("Index overrides", row "Served app writes"). |
| S08 R-5 | S08 (08-01) | `test_clear_registry.cscript` is not edited (it has no `c(python_exec)` gate). CLR-07 becomes PF-02 in `test_wp29_truth.cscript`. | S08 adds the case to `test_clear_registry.cscript` with no Python skip. | 01oct2026 ratified |
| S08 R-6 | S08 (08-01) | Bounded preview retention: 0600 pages in a 0700 folder, five per session, removed by `dash clear` except one opened in the last 60 s, and removed once their session is dead. PLAN.md BR-29.11 and E6 already carry this text (amended 01oct2026), and S01 writes it into ROADMAP. | PLAN.md BR-29.11/E6 and S01's ROADMAP text revert to "deleted when the command ends" before step 1. | 01oct2026 ratified (PLAN.md BR-29.11/E6 and S01's ROADMAP text keep the bounded retention) |
| S08 codes | S08 (08-01) | An unsafe private root is refused with r(603). A data file that cannot be written privately ends r(198) through `_dash_write_data`'s existing branch. | Codes named by the maintainer. | 01oct2026 struck (answer 2): proceed and note (section-08 R-8). No privacy condition is refused: a shared or foreign `c(tmpdir)`, a folder or file the disk will not keep private, and a user-named folder that is not private all give rc 0; dash still creates every file 0600 where it can and prints one `dash: note: …` per command naming the location (a user-named folder is never refused, re-moded or noted). A planted `dash-<uid>` is left alone for a 0700 fallback `dash-<uid>-<8 chars>`. Kept as ANTI-HIJACK, not privacy: no write through a symbolic link, into a FIFO or device, over a hard-linked file or another account's file at the target name, or of a name that appears mid-write, and no launch of an `app.py` replaced after it was written; each ends r(7102) (M4a). Since round 2, the launch reads and verifies the app through a descriptor it opened and never starts it by path (row "S08 launch route"). The r(198) branch is gone. Only an operating-system failure to create the folder at all ends r(603) (Stata's own `file open` code; not a refusal). |
| S13 1-8 | S13 (13-02, item 2(f)) | (1) Unset `DASH_SERVE_TOKEN` under `bokeh serve` fails closed. (2) There is no opt-out. (3) Stata opens the tokenized URL through the child's `--show`, under the existing nobrowser/`$dash_nobrowser`/`nodraw` rule. (4) The Linux opener is a 0600 redirect file in a fresh `mkdtemp` folder. (5) The key is never printed, except (round 2, answer A, "Print the URL once") when no link file can be written anywhere: then the full link is printed once, after one warning line, to the output of whoever started the server, and the server keeps serving (section-13 K-9). (6) There is no throttling of 403 log lines (a recorded residual). (7) The parameter is named `token`. (8) A fixed `DASH_SERVE_TOKEN` for `python app.py` is validated at start and popped from the environment. | Each struck item is re-planned in section-13 before batch 2 is cut. | 01oct2026: item (1) struck (answer 3): the served app never runs without a token. Started with no `DASH_SERVE_TOKEN` and no `--token-stdin` (`python app.py` or `bokeh serve app.py` by hand), it makes its own `secrets.token_urlsafe(32)` key, installs it for both gates, writes the link to a 0600 `link.html` in a fresh 0700 `mkdtemp` folder and prints only that file's path (section-13 K-1..K-9, TR-13.8a). An invalid supplied key is still refused at start (item 8). Items (2)-(8) ratified. |
| S13 (a)-(e) | S13 (13-02, item 2(a)-(e)) | (a) Stata never prints the key, except section-13 K-9's warned once-only print when no link file can be written; `dash serve` prints the path of a 0600 `link.html`. (b) `::` maps to `[::1]`. (c) The auth-provider class is nested in `_dash_token_auth`. (d) The key line is read in `__main__`, and the stdin pipe stays open. (e) S08's LC-01 is flipped to allow `link.html`. | As for S13 1-8. | 01oct2026 ratified |
| S14 SD1-SD6 | S14 (14-01) | SD1: `csv` keeps today's contract. SD2: a cleared or after-move brush card counts the rows its graph shows. **Results change:** 23.4 → 25.66667, 21.5 → 22.83333 and 21.2973 → 22.13333. SD3: dense ranks on the saved page; the served `index` is a residual. SD4: an empty reach uses the shared builder's existing widgets. SD5: the follow-ups are S15 residuals. SD6: P0.16 belongs to S07. | Each struck item is re-planned in section-14 before batch 3 is cut. | 01oct2026: SD1, SD2, SD4, SD5, SD6 ratified; SD3's saved half ratified, its served half struck (answer 4): the served `index` of the shared source and of every per-layer source carries the saved page's dense ranks, never original observation labels, through one relabel of the served frame (section-14 TR-14.16, TR-14.18; `_dash_page_index`, `_dash_relabel`). No residual, no BUGS.md entry, no `TestTheServedIndexResidual`; failing-first `TestTheServedIndexIsARank` instead. |
| S13 K-8 | S13 (13-02 step 3a; round 2, question "Token link failure") | Round 1's K-8 stop: if the served app cannot write its private `link.html` in any folder dash tries (under `dash serve` the run folder, then a fresh private temp folder; an app that made its own key, its fresh private temp folder), the server is stopped (exit status 2) rather than leave the key where others can read it. | The server keeps serving and the link is printed once with a warning (section-13 K-9). | 01oct2026 (round 2): struck (answer A, "Print the URL once"). K-8's stop path is struck under `dash serve`, `python app.py` and `bokeh serve`. When no folder dash tries takes the link file (the fresh private temp folder fallback included), nothing is stopped: dash prints one warning line, `_DASH_LINK_UNWRITTEN`, saying the key now appears in that output and any log of it, then the full tokenized URL alone on the next line, exactly once (per launch under `dash serve`, per process under `python app.py`, per app path per process under `bokeh serve`), to the console or Results window of whoever started the server, and keeps serving. This is the only case in which the key is ever printed; item (5) of "S13 1-8" and item (a) of "S13 (a)-(e)" now read "never printed, except this fallback". The one remaining stop is an `--address` no link can name (exit status 2). Section-13 K-9, K-2, K-3, K-4, K-8, TR-13.8a and TR-13.12 item 6; tests `test_an_unwritable_link_is_printed_once_with_a_warning`, `test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served` and their live forms. |
| S08 launch route | S08 (08-01 step 3a; round 2, question "App swap in a shared non-sticky temp folder") | dash starts the served app by path after a launch identity check (`_dash_same_file`, TR-08.8 as ratified in round 1); in a `c(tmpdir)` others can write that has no sticky bit, another account can swap in its own `app.py` between the check and the child's open, recorded as a residual (section-08 R-8, TR-08.21). | dash launches the app from a file it opened and verified, so a swap after the check cannot change what runs (section-08 R-9). | 01oct2026 (round 2): struck (answer B, "Launch from open file"); the gap is closed fully. On every launcher route dash itself uses, `_dash_launch_app` (`dash serve` and the renderer's `--launch`; dash has no preview server), dash opens `app.py` with `O_NOFOLLOW` where available, checks the open descriptor (a regular file, owned by this account, the `(st_dev, st_ino)` and size recorded when `main()` wrote it) and the SHA-256 of the bytes read through it, and starts `[sys.executable, "-P", "-c", _DASH_BOOT, app_path, …]`, handing those bytes over as one `DASHAPP1 <n> <sha256>` frame on the child's stdin. The bootstrap compiles them under `app_path`, so tracebacks name the file, runs them as `__main__` and never opens a path. The route is the same on macOS, Linux and Windows (no `/dev/fd`). `_dash_same_file` is withdrawn. Every launcher test that pins the command line is updated, and failing-first tests (`TestTheLaunchFromTheOpenFile`, among them a path swapped after verification) show that the swap cannot change the code that runs. A `python app.py` or `bokeh serve app.py` the user runs is outside dash's control and is documented, not changed (section-08 R-9, TR-08.8, TR-08.8a, TR-08.11; section-13 L-1..L-5). |
| S00 plan files | Index ("Plan files" delta, step 0a; round 2, question "Commit the plan") | `.ultraplan/wp29/` is untracked and never committed in WP-29; no worktree holds it, and agents read it by absolute path only. | The plan is committed before any worktree is cut. | 01oct2026 (round 2): struck (answer C, "Commit them"). Step 0a commits `.ultraplan/wp29/` on `wp29-p0`, in its own commit with a message that has no AI reference, before any worktree is cut, so worktrees carry it. Agents may still use the absolute paths; the files are tracked ("Plan files" delta). |

**Points the re-plans raised (recorded for the maintainer; they do not block step 1, because each follows from an answer above):**
- **S13 K-8 (stop path struck in round 2, answer A).** Round 1 stopped the server (exit status 2) when the link file could not be written even in a fresh `mkdtemp` folder. Round 2 strikes that stop: the link file is still written 0600 wherever the disk allows, and otherwise written with one `dash: note:` (K-8); when no folder takes it at all, one warning line and the full link are printed exactly once to the output of whoever started the server, which keeps serving (section-13 K-9; rows "S13 K-8", "S13 1-8" item (5)). This is the only case in which the key is ever printed.
- **S08 hard links.** A target with other hard links is refused r(7102) as anti-hijack (writing through it would change the linked file). Answer 2 does not name hard links; this is section 08's reading.
- **S08 app substitution (closed in round 2, answer B).** In a `c(tmpdir)` others can write that has no sticky bit, another account could swap in its own `app.py` between the launch identity check and the child's open. Round 2 closes it: `_dash_launch_app` reads the app through a descriptor opened with `O_NOFOLLOW` and verified (regular, this account's, `(st_dev, st_ino)`, size, SHA-256) and hands the bytes to `python -P -c _DASH_BOOT` on stdin, so the child never opens a path (section-08 R-9, TR-08.8a; measured, §3b). What remains in that case is in section-08 R-8: the spec and data read by path, denial of the launch, and a `.py` the user runs by hand.
- **S05 divergence.** In 12 measured cases the page shows dates where twoway shows numbers (`(lfit …)(scatter …)` among them).

The checkpoint tasks no longer ask mid-batch:
- **08-01, 13-02 item 2 and 14-01's SD part.** Each copies its rows of the ratified record of 01oct2026 (the table above, as step 0f wrote it to `<scratch>/wp29-ratified.txt`) verbatim into its own `<scratch>/<NN>-decisions.txt`, checks that the record says what its section was re-planned on (08-01: R-1, R-3, R-5, R-6 ratified, "S08 codes" struck for R-8, and, round 2, "S08 launch route" struck for R-9 by answer B; 13-02: item (1) struck for a self-made key, (2)-(8) and (a)-(e) ratified, and, round 2 (its step 3a), "S13 K-8" struck for K-9 by answer A; 14-01: SD3's served half struck for the relabel, the rest ratified), and proceeds. It asks the maintainer nothing. If a row is missing, reads "pending", or differs from that, the task stops before any edit and reports, because step 0f has been broken.
- **The impact checkpoints (02-02, 04-02, 13-02 item 1 and 14-01's impact part).** Each verifies the per-batch impact approval that step k.0 records (R8).
- **Unchanged.** 08-18 (the manual GUI Break check) does not block; its "not run" path writes the residual. 15-06 runs in S15, which runs alone.

## Section manifest

| # | Section | Units | P0 entries | Risk | Batch | Depends on | Blocks | Case prefix | Tasks | Fix commits |
|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Tracking foundation | — | all (opens 21) | green | 0 (alone) | none (after step 0) | every section | — | 8 | 1 (S01) |
| 02 | Line join order | u01 | P0.1 | red | 1 | 01 (landed) | 14 | JO | 17 | 1 |
| 03 | Default and empty titles | u03, u04 | P0.3, P0.4 | yellow | 1 | 01 (landed) | 10 | UL, ET | 19 | 2 |
| 04 | `function` evaluated by Stata | u06 | P0.6 | yellow | 1 | 01 (landed) | — | FX | 17 | 1 |
| 05 | Date computations in Stata units | u08 | P0.8, P0.20 | red | 1 | 01 (landed) | 10, 11, 12 | DU, KD | 18 | 2 |
| 06 | hover() variables exported | u09 | P0.10 | yellow | 1 | 01 (landed) | 14 | HX | 11 | 1 |
| 07 | Saved filter rows and colorvar domain | u13 | P0.15, P0.16 | yellow | 1 | 01 (landed) | 12, 14 | QF, CQV | 16 | 2 |
| 08 | Private files and serve lifecycle | u11b, u12 | P0.12b, P0.14, P0.13 | red | 1 | 01 (landed) | 13, 14 | PF, LC | 19 | 3 |
| 09 | dash_setup on PEP 668 Pythons | u15 | P0.19 | yellow | 1 | 01 (landed) | — | PEP | 19 | 1 |
| 10 | axis(#) routing and by() shared scales | u05, u02 | P0.5, P0.2 | red | 2 | 03, 05 | — | AX, BSC | 23 | 2 |
| 11 | lpoly port: bandwidth and analytic band | u07a, u07b | P0.7, P0.9 | red | 2 | 05 | 12, 14 | LW, LB | 24 | 2 |
| 12 | Stale cue and served redraw widths | u14 | P0.17, P0.18 | yellow | 2 (second wave) | 05, 07, 11 | — | SCU, EW | 20 | 2 |
| 13 | Served-app token | u11a | P0.12a | red | 2 | 08 | — | TOK | 16 | 1 |
| 14 | Embed only the rows a consumer reads | u10 | P0.11 | red | 3 | 02, 06, 07, 08, 11 | 15 | ER | 16 | 1 |
| 15 | Closeout | — | all | green | 4 | all | none | — | 17 | 5 or 6 (S15.1-S15.4, S15.6 only if re-dated, S15.7) |

"Tasks" is the count of `<task>` elements in each section file at plan time (`grep -c '<task ' section-<NN>-*.md`).

Why the dependencies:
- **10 ← 03:** u04 rewrites `_TEXTBOX_SUBOPT_RE`/`_textbox_split_point` and u03 `_dash_axis_labels`; u05 routes `ytitle(, axis(2))`-style options through `_dash_route_axis_titles` and `_dash_add_secondary_axes`, and the "unlabelled + `ytitle(, size(large))`" case is tested by whichever lands second (S10).
- **10 ← 05, 11 ← 05:** u05 and u07a/u07b need date axes in Stata units (u08) for their `%td`/`%tc` truth; u07a's default bandwidth on a date x is only correct in units.
- **12 ← 07, 05:** u14's stale rule reads the rows u13 registers (P0.15) and shares the saved page's aggregate recompute with u08.
- **12 ← 11:** u14's cue must mark lpolyci's band, outline and line sources, which u07b creates (u07b open question 5); 12-17 restyles `map_lpoly`'s empty branch on u07a's text. A worktree cut at `batch-2-base` sees neither, so S12 is cut only after S11 lands (section-12 critic amendment C1; "Batch 2"). The graph stays acyclic: 11 depends only on 05.
- **13 ← 08:** the token is written into the private 0700 root and passed to the app over u12's parent pipe; u11a's design depends on u11b and u12.
- **14 ← 02, 06, 07, 08, 11:** u10 restricts each consumer to the rows it reads, so every consumer's final row rule must exist first: line order (u01's `_join_order` reads drawn rows), hover columns (u09), the colorvar view-row domain (u13; u10 amendment A1 is a blocking regression without it), the private writer (u11b), and lpoly/lpolyci's whole-data inputs (u07a/u07b).

## P0 coverage

| P0 | BUGS.md entry (S01) | Section | Commit subject ends | CHANGELOG list(s) | Grade |
|---|---|---|---|---|---|
| P0.1 | line types joined in x order; sort(varlist) ignored | 02 | `(WP-29 P0.1)` | Results; Changed behaviour | S1 |
| P0.2 | by() panels independently scaled | 10 | `(WP-29 P0.2)` | Results | S1 |
| P0.3 | unlabelled variables give blank titles, type-named keys, blank tooltips | 03 | `(WP-29 P0.3)` | Results | S1 |
| P0.4 | xtitle(, size()) with no text deletes the title | 03 | `(WP-29 P0.4)` | Results | S1 |
| P0.5 | axis(2) on ylabel/yscale/yline/xtick applied to axis 1 | 10 | `(WP-29 P0.5)` | Results; Changed behaviour | S1 |
| P0.6 | function: ^ right-associative, pi and e accepted | 04 | `(WP-29 P0.6)` | Results; Changed behaviour | S1 |
| P0.7 | lpoly/lpolyci default bandwidth wrong | 11 | `(WP-29 P0.7)` | Results | S1 |
| P0.8 | computed layers on a date run in ms | 05 | `(WP-29 P0.8)` | Results | S1 |
| P0.9 | lpolyci band is a bootstrap, not Stata's | 11 | `(WP-29 P0.9)` | Results | S1 |
| P0.10 | hover()-only variable never exported | 06 | `(WP-29 P0.10)` | Fixed in WP-29 | S1 |
| P0.11 | saved page embeds rows if/in exclude | 14 | `(WP-29 P0.11)` | Security | S1 |
| P0.12a | served app has no credential | 13 | `(WP-29 P0.12a)` | Security; Changed behaviour | S1 |
| P0.12b | served app files world-readable | 08 | `(WP-29 P0.12b, P0.14)` | Security | S1 |
| P0.13 | served app outlives Stata; Break cannot stop serve | 08 | `(WP-29 P0.13 F2)`, `(WP-29 P0.13 F4)` | Security; Fixed in WP-29 | S1 |
| P0.14 | one-line preview pages never deleted, 0644 | 08 | `(WP-29 P0.12b, P0.14)` | Security | S2 |
| P0.15 | saved filter registers per-plot rows, not the intersection | 07 | `(WP-29 P0.15)` | Results | S1 |
| P0.16 | colorvar range ignores qualifiers | 07 | `(WP-29 P0.16)` | Results | S1 |
| P0.17 | saved fits stale after a filter move, no cue | 12 | `(WP-29 P0.17)` | Fixed in WP-29 | S1 |
| P0.18 | served redraw keeps build-time bar widths | 12 | `(WP-29 P0.18)` | Results | S1 |
| P0.19 | dash_setup fails on PEP 668 Pythons | 09 | `(WP-29 P0.19)` | Requirements | S2 |
| P0.20 | KPI sd/var/iqr/cv/sum of a date in ms | 05 | `(WP-29 P0.20)` | Results | S1 |

S01 writes each title in full (no `"` in a title), the Description (the DROPIN text and its source ids), the Suggested fix (one sentence naming the section) and `- Resolution: Not fixed because WP-29 section <NN> has not landed. Graded S<n> (WP-29): <why>.` The grade column is S01's starting grade; S01 may change it with a reason in the entry.

**Entry counts (after the 01oct2026 ratification).** WP-29 adds exactly these 21 entries and no other. S14 no longer opens an S3 entry for the served `index` (answer 4 struck that residual), and S05, S08 and S13 open none. So BUGS.md after S01 holds 25 open entries (21 WP-29 plus the 4 `S3 (WP-27)` entries open at `7421d3d`), and after the closeout 4 (S15 AC-15.1).

## Batch execution order and dependency graph

```
Step 0 (main checkout, wp29-p0): 0a commit .ultraplan/wp29/, then TWOWAY_COVERAGE_AUDIT.md + _ROOT_ALSO   0b cert baseline (runs to the end)
                                 0c check the maintainer's GitNexus index   0d batch-0 base   0e hand-off   0f copy the ratified record
                                          │
Batch 0 (1 worktree):   01                (lands on wp29-p0; then batch-1-base.txt is recorded and 02-09 are cut)
                         │
Batch 1 (8 worktrees):  09   03   02   04   06   07   05   08      (merge order left to right)
                         │    │              │    │    │    │
Batch 2 (4 worktrees):   │    └──► 10 ◄──────┼────┼────┤    └────┐     10 (03, 05)
                         │                   │    │    ├──► 11   │     11 (05)
                         │                   │    │    │    ▼    │
                         │                   │    └────┴──► 12   │     12 (05, 07, 11): second wave, cut after 10 and 11 land
                         │                   │                   │
                         │                   │              13 ◄─┘     13 (08)
Batch 3 (1 worktree):    │      14 ◄── 02, 06, 07, 08, 11
Batch 4 (main checkout): 15 ◄── all
```

### Batch 0: S01 alone
- **S01** Tracking foundation [green]

S01 runs alone (section-01 R-05). Gate G5 of every later section needs four things S01 creates: its open BUGS.md entry, its `WP29_OPEN` key, its CHANGELOG marker(s) and the `test_wp29_truth.cscript` scaffold. None of these is on the step-0a tree. S01 changes no shipped file. The merger lands its one commit on `wp29-p0`, and gate G8 runs. Only then are the batch-1 worktrees cut, from that commit, and `<scratch>/batch-1-base.txt` is recorded. S01's own "failed at" sha is `batch-0-base.txt`.

### Batch 1: independent fixes (eight sections)
- **S02** Line join order (P0.1) [red]
- **S03** Default and empty titles (P0.3, P0.4) [yellow]
- **S04** `function` evaluated by Stata (P0.6) [yellow]
- **S05** Date computations in Stata units (P0.8, P0.20) [red]
- **S06** hover() variables exported (P0.10) [yellow]
- **S07** Saved filter rows and colorvar domain (P0.15, P0.16) [yellow]
- **S08** Private files and serve lifecycle (P0.12b, P0.14, P0.13) [red]
- **S09** dash_setup on PEP 668 Pythons (P0.19) [yellow]

**Merge order:** `S09, S03, S02, S04, S06, S07, S05, S08` (S01 has already landed in batch 0).
- S09 first: it is disjoint from the renderer (no `dash_render.py` change and no copy-list entry). Its `test_cscript_hygiene.py` edit, the `_ALLOWED_INLINE_PY_MACROS` entry, applies to the pins S01 already moved. Its `test_help_claims_8.py` edit (the dash_setup class) is its own: S02 lists `test_help_claims_8.py` and `test_help_claims_8.cscript` as verified unchanged.
- S03 second: it changes `conftest.make_data_json` (A7); landing it before the other renderer sections makes the batch's full-suite run show any label dependence at once.
- S02 before S04 and S06: all three edit `dash.ado` and `dash_parse.mata`; S02's `sort()` validation sits in the plot-option parse, S04's evaluation sits after the segment loop (`dash.ado:4755-4821`) and S06's in the export path (`dash.ado:5981-6060`), so later hunks apply to the earlier text.
- S07 before S05: both touch `_make_figure_body` and the `_FILTER_JS` aggregate loop region (S07 changes no JavaScript, S05 does), so the JS-changing section goes second.
- S08 last: it rewrites every temp-file writer (`dash.ado` serve and export paths, the launcher at `dash_render.py:31888-32205`), which S04 and S06 also touch.

### Batch 2: consumers of batch 1 (four sections)
- **S10** axis(#) routing and by() shared scales (P0.5 then P0.2), depends on 03, 05 [red]
- **S11** lpoly port (P0.7 then P0.9), depends on 05 [red]
- **S12** Stale cue and served redraw widths (P0.17 then P0.18), depends on 05, 07, 11 [yellow], second wave
- **S13** Served-app token (P0.12a), depends on 08 [red]

**Worktree cuts (section-12 critic amendment C1, 12 ← 11).** S10, S11 and S13 are cut from `wp29-p0` at `<scratch>/batch-2-base.txt` (step 2). S12 is not:
1. The merger lands S10's commits, then S11's, by the merge routine (merge order unchanged).
2. It then runs, in the main checkout, the R2 registry tests and the full suite once, under "Full-suite runs" (the interim run: `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q > <scratch>/batch-2-interim-full.log 2>&1`). A red result is handled as step 2's "A red result", and S12 waits for the green rerun.
3. Only when that run is green does it record `git rev-parse HEAD > <scratch>/batch-2-s12-base.txt` and cut `git worktree add /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s12 -b wp29-s12 wp29-p0`. Task 12-01 checks that the worktree is on that sha and holds S11's commits.
4. S12 then runs alongside whatever of S13 remains. S13 may finish first, but it lands after S12.

**Merge order:** `S10, S11, S12, S13`.
- S10 before S11: both edit `dash.ado` option validation and `dash_parse.mata`; S10's `_dash_route_axis2` (dash_parse.mata:4884) region is larger.
- S12 before S13: both edit `ServerAppBuilder` (S12 the session redraw of bar/rbar widths, S13 the template's auth hook and launcher). S13 lands last so its served-name guard additions see the final app text.

### Batch 3
- **S14** Embed only the rows a consumer reads (P0.11), depends on 02, 06, 07, 08, 11 [red]

### Batch 4
- **S15** Closeout, in the main checkout on `wp29-p0`, depends on all [green]

## How to execute

0. **Before any section runs, the orchestrator does six things in the main checkout on `wp29-p0`.** 0a comes first. 0c waits until 0b has finished. 0d, 0e and 0f may run while 0b runs.

   0a. **Commit the plan (round 2, answer C), then the cited audit (A6).** Two commits, in this order, both before any worktree is cut.
   1. **The plan.** This is the final plan: every round-2 reconciliation is already in the files.
      - `git add .ultraplan/wp29/` (17 files: `index.md`, `PLAN.md`, `section-01-*.md` … `section-15-*.md`). Stage nothing else: never `CLAUDE.md`, `.gitignore` or `TWOWAY_COVERAGE_AUDIT.md`.
      - Check: `git diff --cached --name-only | grep -vc '^\.ultraplan/wp29/'` prints 0, and `git diff --cached --name-only | wc -l` prints 17.
      - The commit holds documents only, and tracking them changes no test's input: the only tests that ask git which files are tracked look at root files (`test/test_packaging.py:438`) and `test/fixtures` (`test/test_fixtures_are_committed.py:64`), and the directory walks skip `.ultraplan` (`test/test_packaging.py:55`, `test/test_tracking_documents.py:88`). G0's full run below runs on the tree that holds the commit.
      - Commit with the subject `Record the WP-29 plan for the drop-in P0 fixes (WP-29 S00)` and a body naming what the files are (the index, PLAN.md and the fifteen section files), with no AI reference. Grep the message for `claude|anthropic` before and after committing (G7). The file contents are the maintainer's plan and are committed as they are.
      - Then `git ls-files .ultraplan/wp29 | wc -l` prints 17 and `git status --porcelain .ultraplan/wp29` prints nothing.
   2. **The audit (A6).**
      - `git add TWOWAY_COVERAGE_AUDIT.md`, and add `"TWOWAY_COVERAGE_AUDIT.md"` to `_ROOT_ALSO` in `test/test_packaging.py` (426-430, alphabetical: after `"ROADMAP.md"`).
      - Run `python3 -m pytest test/test_packaging.py -q -n0`, then the full suite once, under "Full-suite runs".
      - Stage only those two paths, never `CLAUDE.md`, `.gitignore` or a plan file.
      - Commit with the subject `Record the twoway coverage audit the WP-29 sources cite (WP-29 S00)` and no AI reference. Grep the message for `claude|anthropic` before and after committing.
   - `scripts/stata_slot.sh` already exists (mode 755, three `/tmp/dash-stata-slot-<n>.d` slots, `STATATMP=<dir>/tmp/`) and needs no change.

   0b. **Record the certification baseline** on the step-0a tree: `{ date +%s; make cert; date +%s; } > <scratch>/wp29-cert-baseline.log 2>&1`.
   - Run it in the background. Wait for it with a background until-loop or Monitor, and read the log when it exits. Never relaunch it to check on it.
   - It must finish before step 1 starts. While it runs, the hook refuses every full pytest launch (`run_all_cscripts.do` is running). Any concurrent Stata, pytest or indexing load would also distort the baseline that S15 compares against, so step 0c (indexing) waits for it. Steps 0d-0f use no CPU and may proceed meanwhile.

   0c. **Use the maintainer's GitNexus index (R8). Do not build it.** The maintainer runs `gitnexus analyze` in the main checkout themselves; on 01oct2026 a rerun was in progress. Step 0c builds nothing. Before step 1, run check 4 below. A `lastCommit` behind `git rev-parse HEAD` only by step 0a's documentation-only commits is accepted. If `dash` is not listed, or the index is behind by more than that, stop and ask the maintainer to finish or rerun `gitnexus analyze`. Then run check 5. Steps 1-3 below are used only for the after-batch rebuilds (R8), always as `gitnexus analyze`, never `npx`.
   1. `mkdir -p <scratch>/gitnexus-pre && cp CLAUDE.md AGENTS.md <scratch>/gitnexus-pre/`. `analyze` rewrites the CLAUDE.md/AGENTS.md context blocks, and this checkout's `CLAUDE.md` holds the maintainer's uncommitted edits.
   2. Run `gitnexus analyze`.
   3. Put back any file it rewrote: `cmp -s CLAUDE.md <scratch>/gitnexus-pre/CLAUDE.md || cp <scratch>/gitnexus-pre/CLAUDE.md CLAUDE.md`, and the same for `AGENTS.md`. `git status --porcelain` then prints exactly ` M .gitignore` and ` M CLAUDE.md` (the plan is tracked since step 0a; a ` M .ultraplan/wp29/…` line means an amendment that the "Plan files" delta says to commit before the next batch base). `.gitnexus/` does not appear, because the maintainer's uncommitted `.gitignore` line ignores it.
   4. Check that `mcp__gitnexus__list_repos` lists `dash` with path `/Users/billy/Desktop/Programs/StataPrograms/d/dash` and `lastCommit` equal to `git rev-parse HEAD`. On 01oct2026 at 06:53, after the maintainer's analyze run, it still listed only `TYME` and `PhotoShootPlannerPro`.
   5. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -k nothing_links_them`. That test walks every directory except those in `_SKIP_DIRS` (test_tracking_documents.py:90-91), so it reads `.gitnexus/`. It passed on 01oct2026 with the maintainer's `.gitnexus/` present (1 passed). If the test fails on a `.gitnexus/` path, stop and report to the maintainer before step 1.

   The index is rebuilt the same way after each batch lands. It is never built in a worktree.

   0d. **Record the batch-0 base:** `git rev-parse HEAD > <scratch>/batch-0-base.txt` (the step-0a audit commit, the later of step 0a's two commits; its tree holds the plan).

   0e. **Hand each section agent its inputs by absolute path.** The plan directory is tracked since step 0a, so each worktree also holds it at its base; the absolute main-checkout paths below are the governing copy ("Plan files" delta). The inputs:
   - `/Users/billy/Desktop/Programs/StataPrograms/d/dash/.ultraplan/wp29/section-<NN>-*.md`, with its appendices;
   - `.../.ultraplan/wp29/index.md` and `.../.ultraplan/wp29/PLAN.md`;
   - `/Users/billy/Desktop/Programs/StataPrograms/d/dash/.ultraplan/sections/BRIEF.md`;
   - its reviewed design with every amendment;
   - `CLAUDE.md`;
   - `<scratch>/wp29-ratified.txt` and `<scratch>/batch-<k>-impact.txt`.

   A section agent never edits a plan file.

   0f. **Copy the ratified record.** Ratification was done at plan time (01oct2026, two rounds; "Decisions for maintainer ratification"). Copy that subsection, from its heading through the last row of its table, verbatim into `<scratch>/wp29-ratified.txt` (the maintainer's four round-1 answers, the three round-2 answers and every row with its filled last column). Check:
   - `grep -c '| pending |' <scratch>/wp29-ratified.txt` prints 0;
   - `grep -c '^| [DS].*| 01oct2026' <scratch>/wp29-ratified.txt` prints 12 (one per row: nine of round 1, three of round 2);
   - `grep -c '| 01oct2026 (round 2): struck' <scratch>/wp29-ratified.txt` prints 3 (rows `S13 K-8`, `S08 launch route`, `S00 plan files`);
   - `grep -c -F -e '"Print the URL once"' -e '"Launch from open file"' -e '"Commit them"' <scratch>/wp29-ratified.txt` prints at least 3.

   Nothing is asked. Step 1 waits until the file exists and passes every check.

1. **Batch 0: S01 alone, in its own worktree.**
   - **Impact first (step 1.0, R8).** At `batch-0-base`, run `gitnexus_impact({target, direction: "upstream", repo: "dash"})` for each symbol S01 edits (section-01 task 01-02). Write the results to `<scratch>/batch-0-impact.txt`. Report any HIGH or CRITICAL result to the maintainer and record the approval in that file.
   - **Cut the worktree:** `git worktree add /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s01 -b wp29-s01 wp29-p0`.
   - **Run S01.** S01 runs its tasks. Before its one commit `(WP-29 S01)`, it runs steps 5-8 of the per-entry cycle below.
   - **Land it.** The merger lands the commit with the merge routine below and runs "After the batch" (G8).
   - **Then** remove the S01 worktree (`git worktree remove`), rebuild the GitNexus index (step 0c, all five checks), and run `git rev-parse HEAD > <scratch>/batch-1-base.txt`. Batch 1's worktrees are cut from this commit and no earlier one, so every section starts from S01's entries, keys, markers and scaffold.
2. **Batch 1, then batch 2, then batch 3, one agent per section, each in its own worktree.** For batch k:
   - **k.0 Impact at the batch base, before any worktree is cut (R8).**
     - For every symbol each section's file says it edits (its R8 or blast-radius list), run `gitnexus_impact({target, direction: "upstream", repo: "dash"})` and write the results to `<scratch>/batch-<k>-impact.txt`.
     - Report every HIGH or CRITICAL result to the maintainer in one message (R8 names the expected ones) and record the approval in that file.
     - A section that later must edit a symbol not in that file runs `gitnexus_impact` with `repo: "dash"` itself. It reports a HIGH or CRITICAL result before editing.
   - **Cut** each worktree from `wp29-p0` at `batch-<k>-base`: `git worktree add /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s<NN> -b wp29-s<NN> wp29-p0`.
     - **Batch 2 exception (12 ← 11).** Only S10, S11 and S13 are cut at `batch-2-base`. S12 is cut after S10 and S11 have landed and the merger's interim full run is green, at `<scratch>/batch-2-s12-base.txt` ("Batch 2", "Worktree cuts").
   - **Per P0 entry cycle (rule 7, D1):**
     1. Write the entry's failing tests and run them against the unmodified tree.
     2. Save the failure text to `<scratch>/<NN>-<P0>-failure.txt`.
     3. Make the fix, flip the pinned tests with their reasons, and add the fixture and truth block.
     4. Close the BUGS.md entry in place, delete its `WP29_OPEN` key, and replace its CHANGELOG marker(s).
     5. Run the changed files with pytest, and the section's cscripts through the driver below.
     6. Pull from main (rule 4): `git -C <wt> merge --no-edit main`. Expect `Already up to date.` If main moved, stop and report to the orchestrator without committing.
     7. Run the full suite once in the worktree, under "Full-suite runs": wait for a free suite, then `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q > <scratch>/<NN>-full-<P0>.log 2>&1`. It must show 0 failed.
     8. Check scope (G6 in a worktree): `git -C <wt> diff --cached --name-status` names only the section's files, with no `CLAUDE.md`, `.gitignore`, `.gitnexus/`, `.ultraplan/wp29/`, scratch or `*.html`. Check the message (G7). Commit once on `wp29-s<NN>`. `gitnexus_detect_changes` for this commit runs when the merger lands it (G6), because the index covers only the main checkout.

     A second entry in the same section repeats the cycle on the tree the first commit leaves. No test-only commit exists, and no commit is red.
   - **Stata:** only `scripts/stata_slot.sh <scratch> <file>.do`. The do-file opens with `adopath ++ "<worktree>/"`. If it runs dash, the next line is `global dash_nobrowser 1` ("Stata invocation and browsers"; the environment variable has no effect). Never the GUI and never a bare `stata-mp`.
   - **Merging (by the merger, in the main checkout on `wp29-p0`; never `cd` into a worktree).** Follow the batch's merge order. For each commit `<sha>` of each section, oldest first:
     1. Run `git merge --no-edit main`. Expect `Already up to date.` If main moved, stop and report.
     2. Run `git -C <wt> log -1 --format=%B <sha> > <scratch>/msg-<sha>.txt` and `git -C <wt> show --name-status --format= <sha> > <scratch>/names-<sha>.txt`.
     3. Run `git -C <wt> format-patch -1 --stdout <sha> | git apply --index -3`. This stages exactly the commit's paths, including new files and file modes.
        - Why not a plain `git add`: it refuses a new fixture, because `.git/info/exclude:58` ignores `*.json` (`git check-ignore -v test/fixtures/new_x.json` matches that line).
        - Why not `patch -p1`: it drops mode changes.
        - Measured on two scratch clones whose `exclude` holds `*.json`: the pipe staged `A test/fixtures/x.json` as `create mode 100644` and `A s.sh` as `create mode 100755`, with exit 0.
        - A conflict is resolved by hand under R1-R8, and each resolved path is staged with `git add -f <path>`.
     4. Check that `git diff --cached --name-status` equals `<scratch>/names-<sha>.txt`. Run `gitnexus_detect_changes({scope: "staged", repo: "dash"})` and save the output to `<scratch>/detect-<sha>.txt` (G6). The changed symbols must be the section's.
     5. Run G7 on `<scratch>/msg-<sha>.txt`. Then `git commit -F <scratch>/msg-<sha>.txt`, then G7 on `git log -1 --format=%B`.
     6. Verify the landing:
        - `diff <(git show --name-status --format= HEAD) <scratch>/names-<sha>.txt` prints nothing;
        - `git show --stat --format= HEAD` matches `git -C <wt> show --stat --format= <sha>` line for line. A hand-resolved path may differ only in its counts, and is named in `<scratch>/batch-<k>-merge.log`.
   - **After the batch (G8):**
     1. Run the full suite once, under "Full-suite runs".
     2. Run the R2 registry tests.
     3. Run `test/test_wp29_truth.cscript` and every existing cscript the batch touched, through the driver.

     The batch is complete only when that run is green.
   - **A red result belongs to the section that owns the test.**
     1. Fix it in a fresh worktree of that section cut from `wp29-p0`.
     2. Commit there with that entry's id, after steps 6-8 of the cycle.
     3. Land it the same way.
     4. Rerun the failed file, then the full suite once more, under "Full-suite runs".

     Then:
     - remove the worktrees (`git worktree remove`);
     - rebuild the GitNexus index (step 0c, all five checks);
     - record `git rev-parse HEAD > <scratch>/batch-<k+1>-base.txt`.

     The next batch is cut only after this one is green.
3. **S15**, in the main checkout on `wp29-p0` (no worktree).
   - **Commits.** It makes five or six commits: S15.1, S15.2, S15.3, S15.4, S15.6 (only if the release date must move) and S15.7. S15.5 commits nothing.
   - **Before each commit:** `git merge --no-edit main`, `gitnexus_detect_changes({scope: "staged", repo: "dash"})`, and one full run, under "Full-suite runs".
   - **Cert wall time.** It is recorded in S15.7 (task 15-17), after S15.6's release run has measured it. S15.3 writes `<to be measured in 15-17>` placeholders.
   - **Merge command.** S15 reports `git checkout main && git merge --no-ff wp29-p0` without running it (rule 5).

### Full-suite runs (CLAUDE.md rules 4 and 11; the lock and the hook)

**Facts that bind the schedule:**
- **The lock.** It is per user and machine-wide (`test/conftest.py:62-64`, `/tmp/dash-full-suite-<uid>.lock`). A second whole-suite run exits at once with "a full test-suite run is already in progress". It does not queue.
- **The hook.** `.claude/hooks/guard-full-suite.sh` (`full_run_in_progress`) refuses a full launch in two cases: the lock is held, or any full pytest or `run_all_cscripts.do` Stata process is running anywhere on the machine. So a worktree's run, another worktree's run, the merger's run and a `make cert` can never overlap.
- **The ledger.** The hook's launch ledger is per session (`/tmp/claude-full-suite-runs-<session_id>`, `MAX_FREE_LAUNCHES = 2`). Every section agent and the merger run inside the orchestrator's session, whose ledger already read 3 on 30sep2026. Without the override, every launch is refused.

**Rules:**
1. **One planned run per commit, plus G0, each batch's G8 and batch 2's interim run (before S12 is cut).** Every planned run carries the override: `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q > <scratch>/<NN>-full-<k>.log 2>&1`. The override is for planned runs only. A run is never relaunched to check on it; read its log.
2. **Wait, then launch.** Before launching, wait until no full run is in progress. Use Monitor, or a background until-loop (one notification), polling the hook's own check, and never poll by launching:
   ```sh
   until python3 -c "from importlib.machinery import SourceFileLoader as L; g=L('g','/Users/billy/Desktop/Programs/StataPrograms/d/dash/.claude/hooks/guard-full-suite.sh').load_module(); raise SystemExit(1 if g.full_run_in_progress() else 0)"; do sleep 15; done
   ```
   - It exits 0 when the lock is free and no full pytest or certification run is listed. Measured idle on 01oct2026: it printed `None`, exit 0.
   - `.claude/` is untracked, so a worktree uses this absolute main-checkout path too.
3. **A refused launch is not a run.** If two agents see the suite free at once, the lock or the hook refuses one of them. That agent waits again (rule 2) and records nothing as a result.
4. **Certification runs.** Step 0b's `make cert` finishes before step 1, and nothing else runs Stata or a full suite while it runs. S15.6's `make cert` follows the same rule. A section never runs `make cert` or `run_all_cscripts.do`.
5. **Schedule.** The planned runs, not counting reruns after a red result:

   | When | Pytest full runs | Certification runs |
   |---|---|---|
   | Step 0a (G0) | 1 | — |
   | Step 0b | — | 1 (`make cert`, the baseline) |
   | Batch 0 | 2 (S01's commit; G8) | — |
   | Batch 1 | 14 (13 fix commits: S02 1, S03 2, S04 1, S05 2, S06 1, S07 2, S08 3, S09 1; G8) | — |
   | Batch 2 | 9 (7 fix commits: S10 2, S11 2, S12 2, S13 1; the interim run after S10 and S11 land; G8) | — |
   | Batch 3 | 2 (S14's commit; G8) | — |
   | Batch 4 (S15) | 7 (before S15.1, S15.2, S15.3, S15.4 and S15.7; `make test` and `make test-dev` in S15.6) | 1 (`make cert`, S15.6) |
   | **Total** | **35** | **2** |

   - **Time.** At about two minutes a run (CLAUDE.md rule 11), batch 1 needs at least 28 minutes of serial suite time and batch 2 at least 18, however many worktrees run. In batch 2, S12's work also waits for S10's and S11's commits and the interim run.
   - **Red results.** Each red result adds at least two runs: one in the fix worktree and the G8 rerun.

### The cscript driver (BRIEF step 0a)

A cscript is never handed to the wrapper directly. Run it through a two-line driver:

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "<script>.cscript" > <scratch>/run_<script>.do
WP29_ONLY=S<NN> scripts/stata_slot.sh <scratch> <scratch>/run_<script>.do   # log: <scratch>/run_<script>.log
```

- `<repo>` is the worktree while a section runs, and the main checkout for the merger and S15.
- `WP29_ONLY` is only read by `test_wp29_truth.cscript`. Leave it unset to run every block.
- A cscript sets `global dash_nobrowser 1` itself, through `test/cert_helpers.do:51`. The section files put `dash_nobrowser=1` on this line; that environment variable has no effect.
- An extract script under `scripts/` runs directly through the wrapper only if its own text sets its directories. If it runs dash, it sets `global dash_nobrowser 1` right after `adopath ++`.

### Merge rules within a batch

- **R1 cscripts.**
  - **Ownership.** Only S01 creates and registers a script: `test/test_wp29_truth.cscript`, as runner block `// 68.` after `// 67.` (`test/run_all_cscripts.do:1716`), copying block 67's form. Only S01 moves the hygiene pins: `len(_CSCRIPTS) == 66 → 67` (`test/test_cscript_hygiene.py:295`) and `len(names) == 48 → 49` (:313, because the scaffold gates on `c(python_exec)` the way `test_gaps2_truth` does). The import-probe count `13` (:320-324) is not touched by S01; only S09 may change it, and only if its setup scripts add a captured import probe.
  - **Truth blocks.** Each section appends its blocks above the marker in section-number order, gated `if inlist("`only'", "", "S<NN>")` on `local only : env WP29_ONLY`.
  - **Area scripts (refusals, messages, setup, flips).** Refusal, message and setup checks go into the existing script for their area. The table is re-derived from the sections' `<files>` lists (`grep -o '<files>[^<]*</files>' section-*.md`, 01oct2026):

    | Script | Sections (what) | Batch |
    |---|---|---|
    | `test_adversarial.cscript` | S02, S06, S08 (PF-09, flipped by the 01oct2026 ratification: a planted root is left alone and the command proceeds with one note) | 1 |
    | `test_twoway_option_parity.cscript` | S02 | 1 |
    | `test_twoway_option_parity.cscript` | S10 | 2 |
    | `test_parser.cscript` | S04 | 1 |
    | `test_parser.cscript` | S11 | 2 |
    | `test_json_escaping.cscript` | S04 (JSE-47 flipped in place) | 1 |
    | `test_conformance.cscript` | S04 (the C-03 control rewritten in place) | 1 |
    | `test_serve_launch.cscript` | S08 (PF-07, LC-02..LC-04) | 1 |
    | `test_serve_launch.cscript` | S13 (TOK, A3; before SRV-19, after S08's LC cases) | 2 |
    | `test_help_claims_4.cscript` | S08 (HC4-18..21 strengthened, PF-08, LC-01) | 1 |
    | `test_help_claims_4.cscript` | S13 (LC-01 flipped to allow `link.html`) | 2 |
    | `test_env_guards.cscript` | S08 (ENV-12, PF-10) | 1 |
    | `test_e2e_filters.cscript` | S07 | 1 |
    | `test_e2e_filters.cscript` | S12 | 2 |
    | `test_e2e_serve.cscript` | S13 (P4-82 gains the provider check) | 2 |
    | `test_by_suboptions.cscript` | S10 | 2 |
    | `test_statistical_options.cscript`, `test_help_claims_6.cscript` | S11 | 2 |
    | `test_setup_honesty.cscript`, `test_setup_python_gate.cscript`, `test_program_coverage.cscript`, `test_help_examples.cscript` | S09 (`test_help_examples.cscript:549-553`, the `_hx_pin shown` pins) | 1 |

    Not edited by any section:
    - `test_help_claims_8.cscript`: S02 lists it, with `test_help_claims_8.py`, as verified unchanged.
    - `test_clear_registry.cscript`: dropped by S08 R-5. Its CLR-07 case becomes PF-02 in the truth script.
    - `test_qualifier_literals.cscript`: S04 only re-runs QL-20.

    Within a batch, each section appends its new cases as one contiguous run at the end of the script's last case block, and the merger keeps the runs in merge order. An in-place flip edits only its named case.
  - **`test_gaps2_truth.cscript`.** It gets two in-place edits, both in batch 1, in disjoint hunks:
    - S06 flips `AL-19`;
    - S07 rewrites `CV-01`'s colour-field lookup (four lines, task 07-14). This is S07's recorded "R1 exception", which is now part of R1.

    S06 lands before S07. Each checks its own hunk with `git diff -U0 test/test_gaps2_truth.cscript | grep -c '^@@'`, which prints 1. No other section edits the script.
  - **Shared pytest files within a batch.** R2, R3 and R6 govern `function_test_map.py`, `program_coverage_map.py`, `test_tracking_documents.py` and `test_mode_parity.py`. Beyond those, the sections' `<files>` lists show these test files edited by more than one section of one batch:

    | Batch | File | Sections, in merge order |
    |---|---|---|
    | 1 | `test/test_server.py` | S04, S07, S08 |
    | 1 | `test/test_server_layer_defects.py` | S03, S02, S05 |
    | 1 | `test/test_glyphs.py` | S02, S07 |
    | 1 | `test/test_saved_filter_layers.py` | S02, S07 |
    | 1 | `test/test_colorvar_forms.py` | S03, S07 |
    | 1 | `test/test_date_range.py` | S07, S05 |
    | 1 | `test/test_resource_limits.py` | S04, S08 |
    | 2 | `test/test_option_validation.py` | S10, S11 |
    | 2 | `test/test_help_claims_4.py` | S12, S13 |
    | 2 | `test/test_server.py` | S11, S13 |

    In each of these files, a section appends its new tests at the end: new classes after the file's last class, and new methods at the end of a class only where the section owns that class. A flip edits only the pinned test, in place. On a conflict the merger keeps both sides in merge order and runs the file before committing. A file shared across batches needs no rule, because the later batch is cut from the merged tree.
- **R2 copy lists and maps.**
  - **What each section adds.** Its own names to the served copy lists, `test/function_test_map.py` and `test/program_coverage_map.py`, with keys in alphabetical place.
  - **Conflicts.** The merger resolves append conflicts by hand and keeps every entry. Adjacent anchors can conflict in context only: S13's sixteen names placed after S08's `"_dash_watch_parent"`.
  - **Registry tests after every batch.** `test_function_test_map.py`, `test_program_coverage_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` and `test_cscript_hygiene.py`.
  - **Names the served guard does not walk.** A name the served app reads only in its module-level `if __name__ == '__main__':` block is not walked by the guard (u12 amendment A3). S08 extends `TestTheServedAppDefinesEveryNameItReads` to cover that block before adding names used there.
  - **Anchors at `7421d3d`.** The table is re-derived from each section's technical requirements, and every anchor line was checked by grep on dash_render.py at `7421d3d`. "+" adds a name after the anchor, and "−" removes one. Both tuples of the first two columns are in `ServerAppBuilder._glyph_layer_lines` (def 28312). `_glyph_layer_lines` skips any def that `_shared_stat_lines` already emits (`_emitted_names`, 28532).

  | Section | Constants tuple (28362-28497) | Functions tuple (28535-28829) | `_shared_stat_lines` function tuple (def 28889) | Not copied |
  |---|---|---|---|---|
  | S01 | — | — | — | — |
  | S02 | + `"_DASH_SORT_PREFIX", "_DASH_SORT_NAME_RE", "_DASH_JOIN_TYPES"` after `"_DASH_QUAL_PREFIX", "_DASH_QUAL_NAME_RE"` (28441) | + `"_dash_join_key", "_dash_sort_col_of", "_dash_sort_cols_named", "_dash_take_sort_columns"` after `"_dash_float_values"` (28546) | — | `GlyphMapper._join_order` travels with the class; `_masked_order` is deleted and is in no list |
  | S03 | — (`_TEXTBOX_SUBOPT_RE`, 2751, changes in place and is already copied; no `_TEXTBOX_EMPTY_TAIL_RE`, per u04 A1) | + `"_textbox_has_text"` after `"_textbox_split_point"` (28535); + `"_dash_var_label", "_dash_clean_var_labels"` after `"_dash_legend_key", "_dash_legend_entries"` (28619); + `"_dash_filter_base_title"` after `"_dash_filter_title"` (28716); + `"_dash_textbox_or_default"` after `"_dash_textbox"` (28799) (D-03c) | — | — |
  | S04 | + `"_FN_EXPR_MAX_NEST"` after `"_MAX_EXPR_CHARS"` (28365) | + `"_dash_function_points"`, then `"_stata_fn_parse", "_stata_fn_eval"`, after `"_dash_function_args"` (28575); − `"_floats_only"` (28562) | − `_stata_expr_to_python` (28981) | `_dash_attach_function_points` (builder side, called before `_dash_cap_spec`) |
  | S05 | — (D05-1 struck 01oct2026: `_DASH_UNIT_LABELLED_TYPES` is never created and the served axis rule does not read `_DASH_COMPUTED_ONLY_TYPES`; section-05 TR-05.3) | + `"_dash_date_units", "_dash_units_to_axis", "_dash_axis_vars"` after `"_dash_period_values"` (28613); P0.20: + `"_dash_kpi_unit_kind"` after `"_dash_kpi_date_valued"` (28636) | — | — |
  | S06 | — | + `"_dash_note_hover_missing",` on its own line after `"_dash_csv_payload", "_dash_frame_filter_mask",` (28629) | — | — |
  | S07 | + `"_DASH_CVAR_PREFIX"` after `"_DASH_JITTER_Y"` (28383) | + `"_dash_colorvar_domain", "_dash_colorvar_field"` after `"_dash_colorvar_bins"` (28796) | — | — |
  | S08 | — | + `"_dash_watch_parent"` as the new LAST entry, after `"_dash_port_value"` (28829) | — | `_dash_private_root`, `_dash_private_write`, `_dash_private_run_of`, `_dash_run_open` and the other private-file helpers, among them R-8's `_dash_root_name`, `_dash_fallback_root`, `_dash_own_root`, `_dash_mode_private`, `_dash_chosen_path` (R-3: the app writes no file through them; S13's own `link.html` write uses its copied `_dash_private_page`); `_DashServeInterrupted`, `_dash_stata_poller`, `_dash_stop_child` (launcher only); round 2: `_DashWrittenApp`, `_DASH_BOOT`, `_dash_read_verified_app`, `_dash_app_frame`, `_dash_child_stdin`, `_dash_hand_over` (launcher only; section-08 R-9) |
  | S09 | — | — | — | (no dash_render.py change) |
  | S10 | — (`_DASH_AXIS2_KEYS` is build-time only; `_TEXTBOX_SUBOPTS` changes in place and is already copied) | P0.2: + `"_dash_by_rescale"` after `"_dash_by_tokens", "_dash_parse_by"` (28638); + `"_dash_share_by_scales"` after `"_dash_common_count_ticks"` (28708). P0.5 adds none; if the app is found to call a new name, it goes after `"_dash_apply_scale_ranges"` (28803) | — | `_dash_by_range_notes`, `_dash_route_axis_options`, `_dash_axis_number`, `_dash_unused_second_axis_notes`, `ServerAppBuilder._plan_graph_notes` (build time) |
  | S11 | − `"_LPOLY_ROT_C"` (28364), not replaced in the tuple: `_LPOLY_ROT_GRID`, `_LPOLY_ROT_CONSTANTS` and `_LPOLY_DF_TOL` are literal-safe and travel through `_shared_stat_lines`' constant scan (SD-11) | — | P0.7: + `_lpoly_rot_constant, _stata_invsym_keep, _lpoly_rot_detail, _lpoly_rot_float, _lpoly_kept_columns` after `_dash_lpoly_weights` (28965; section-11 cites 28975, which is wrong); P0.9: + `_lpoly_kernel_weights, _lpoly_local_wls, _lpoly_se, _dash_invnormal` after them. `_default_lpoly_bwidth` and `_compute_lpoly_fit` stay in the staticmethod tuple. | `GlyphMapper._bootstrap_ci` is KEPT (SD-12: qfitci's fallback still calls it); only its lpolyci mention goes |
  | S12 | — | + `"_dash_copy_redraw_geometry",` after `"_dash_keep_jitter",` (28761, the `"_dash_refresh_unlinked"` line) | — | `_DASH_STALE_*`, `_dash_stale_kind`, `_dash_stale_glyph` (saved page only; the served app has no cue, M3) |
  | S13 | + the fourteen TR-13.1 names (`_DASH_TOKEN_ARG`, `_DASH_TOKEN_ENV`, `_DASH_TOKEN_RE`, `_DASH_TOKEN_LINE_MAX`, `_DASH_TOKEN_REFUSAL`, `_DASH_TOKEN_REFUSED_HTML`, `_DASH_WS_PROTOCOL_MAX`, `_DASH_JWT_PAYLOAD_MAX`, `_DASH_QUERY_RE`, `_DASH_REDIRECT_TTL_S`, `_DASH_KEY_HOLDER`, `_DASH_LINK_SAID`, `_DASH_BS_ORIGIN_HINT`, `_DASH_LINK_UNWRITTEN`; `_DASH_KEY_HOLDER`, `_DASH_LINK_SAID` and `_DASH_BS_ORIGIN_HINT` ratified 01oct2026, answer 3; `_DASH_LINK_UNWRITTEN` round 2, answer A, K-9) after `"_DASH_CSP_SERVED", "_DASH_SECURITY_HEADERS",` / `"_DASH_VIEWPORT_META",` (28429-28430) | + `"_dash_new_token", "_dash_token_valid", "_dash_token_matches", "_dash_tokenized_url"` after `"_dash_server_transforms",` (28725); + `"_dash_one_value", "_dash_env_token", "_dash_ws_payload", "_dash_request_token", "_dash_token_auth", "_dash_session_token_ok", "_dash_redact_query", "_dash_redact_access_record", "_dash_install_access_log_redaction", "_dash_redirect_page", "_dash_open_tokenized", "_dash_read_token_line", "_dash_private_page", "_dash_announce_key", "_dash_process_key", "_dash_bokeh_serve_key"` after S08's `"_dash_watch_parent"` (sixteen; the last four are TR-13.8a's self-made key, answer 3) | — | `_dash_write_link` (launcher only); S08's `_dash_private_write`, `_dash_private_msg`, `_dash_root_name`, `_dash_mode_private` (section-08's Notes for S13 asked for them; S13's TR-13.8a uses its own `_dash_private_page` instead, so they stay uncopied); S08's `_dash_child_stdin`, which the launcher calls to write the key line (launcher only, round 2) |
  | S14 | + `"_DASH_PLOT_VAR_KEYS"` after `"_DASH_OPT_VAR_KEYS"` (28393) | + `"_dash_embed_rows_of", "_dash_embed_plan", "_dash_embed_values", "_dash_embed_frame", "_dash_page_index", "_dash_relabel"` on one line after `"_dash_layer_frame",` (28597; the last two are TR-14.18's served relabel, answer 4) | — | — |

  - **Correction to section-02 D-g.** Its sentence "no other batch-1 section adds constants" is wrong. In batch 1, S04 (28365) and S07 (28383) also add constants, each at its own anchor. (S05 adds none since D05-1 was struck, 01oct2026.)
- **R3 dash.sthlp, CHANGELOG.md, BUGS.md, test_tracking_documents.py.**
  - **dash.sthlp.** Each section edits only the help paragraphs its P0 entries concern. Where two sections in one batch touch one paragraph (S05 and S11 on lpoly with dates are in different batches, so none at plan time), the later section in merge order rewrites the sentence and the earlier section's text is kept.
  - **CHANGELOG.md.** A section replaces only its own `<!-- WP-29 P0.n -->` marker(s), in place.
  - **BUGS.md.** A section edits only its own entries, in place (A4).
  - **`test_tracking_documents.py`.** A section deletes only its own `WP29_OPEN` key line(s). The keys sit one per line in P0 order, so adjacent deletions from two sections conflict only in context. The merger applies both deletions by hand.
- **R4 `dash.ado` / `dash_parse.mata`.**
  - **Option keys.** No two sections in one batch add the same option key or the same Mata function. New lpolyci keys belong to S11 only (`pwidth`, `lpvar`; A8).
  - **Ownership.** `sort()` validation belongs to S02, axis-word routing to S10, the hover extraction to S06, and the function-layer collection to S04.
  - **Location.** Each section's Mata functions go in the section of `dash_parse.mata` its design names, and the header index (dash_parse.mata:150-260) gains one line per new function in place.
- **R5 fixtures.**
  - **No hand patches.** A regenerated fixture is never patched by hand.
  - **New fixtures.** Every new fixture carries the D12 `_meta` stamp and is added with `git add -f`, because `.git/info/exclude:58` ignores `*.json`. It is named by the test file or cscript that reads it.
  - **`test/test_fixtures_are_committed.py` is NOT edited.** It holds no fixture list. It scans `test/fixtures` and asks git (test_fixtures_are_committed.py:68-77), and its docstring says it "is not one of the files that can name them". It passes once git tracks the file and a reader names it.
  - **Section text this overrides.** The file leaves the `<files>` lists and actions of S02 task 02-03 (the added `assert any(... "join_order_truth.json" ...)`), S10 tasks 10-01 and 10-14, and S11 tasks 11-01 and 11-13 ("add it to the committed-fixture list"). S03, S05, S07, S09, S12 and S14 already say that no edit is needed.
  - **Regeneration.** S03 is the only WP-29 section that regenerates an existing fixture: `text_truth.json` through `scripts/extract_text_truth.do`. It verifies the result probe by probe outside `_meta`.
- **R6 parity corpus.**
  - **Appends.** Sections append `CORPUS` cases to `test/test_mode_parity.py`.
  - **`_MUST_WARN`.** An entry is edited only by the section whose fix silences it, and every key keeps naming a corpus case.
  - **`ALLOWED`.** Nobody edits `ALLOWED`. A saved/served difference is a defect of the section that caused it.
  - **What the guard misses.** The parity guard merges build-time and session warnings (`test_mode_parity._served`, test_mode_parity.py:233-252), so it cannot catch a note that only a session prints. Any note that the served app must print at build time is decided at build time (u02 amendment, HC5-08 precedent at `ServerAppBuilder._plan_by_groups`, dash_render.py:29209).
- **R7 pinned tests.** A test that pins today's wrong behaviour is flipped in the fix commit with a `Flipped:` line, never deleted. A design's red-first list is re-measured by the section, not trusted. u03's list must be complete: run all 96 `make_data_json` users under the flipped helper at the batch base.
  - **The SHA-256 page baseline.** `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` is never re-baselined. It goes red under S03's helper flip and returns to its existing baseline with the fix.
- **R8 GitNexus (CLAUDE.md).**
  - **One index, of the main checkout.** The `dash` repository was not indexed at plan time: on 01oct2026, `mcp__gitnexus__list_repos` listed only `TYME` and `PhotoShootPlannerPro`.
    - The maintainer builds the index in the main checkout (step 0c only checks it), and it is rebuilt there with `gitnexus analyze` after each batch lands.
    - `gitnexus analyze` NEVER runs in a worktree. There it would register a second repository or re-index concurrently, write a `.gitnexus/` that the worktree's committed `.gitignore` does not ignore, and rewrite CLAUDE.md/AGENTS.md.
    - This overrides the "run `gitnexus analyze` in the worktree" step of tasks 02-01, 03-01, 04-01, 06-01, 07-03, 08-02, 09-01, 10-01, 10-14, 11-01, 11-13, 12-01, 13-01 and 14-01, and S05's "if the index is stale". Each of those tasks instead confirms that `list_repos` shows `dash` at its batch base.
    - S01 task 01-02's main-checkout run is already done by step 0c. S15 task 15-01 runs it in the main checkout with step 0c's five checks.
    - In a worktree, the GitNexus PostToolUse hook's "index is stale" notice (`~/.claude/hooks/gitnexus/gitnexus-hook.cjs`, which only notifies) is ignored.
  - **Impact.** Call `gitnexus_impact({target, direction: "upstream", repo: "dash"})`; `repo` is required because several repositories are indexed.
    - It runs at the batch base (step 1.0 / k.0), before the batch's worktrees are cut, for every symbol a section's file names.
    - Each section copies its own results into its Evidence. Every HIGH or CRITICAL result is reported to the maintainer before editing, and the approval is recorded in `<scratch>/batch-<k>-impact.txt`. The section's impact checkpoint (02-02, 04-02, 13-02 item 1, 14-01) verifies that record.
    - Expected HIGH: `GlyphMapper.map_line`/`map_area`/`map_rline`/`map_rarea` (S02), `_dash_axis_labels` (S03, S10), `_make_figure_body` (S07, S12, S14), `_dash_launch_app`/`main` (S08, S13), `ServerAppBuilder._generate_app_source` (S13, S14; the self-made key and the served relabel), `make_data_json` (S03).
    - A grep-based blast radius in a section file is interim evidence and does not replace the impact run.
  - **Detect changes.** `gitnexus_detect_changes({scope: "staged", repo: "dash"})` runs in the main checkout:
    - for every landed commit, after `git apply --index -3` and before `git commit` (merge step 4, G6);
    - before each S15 commit.

    A worktree cannot use it, because the index covers the main checkout: it would report the main checkout's diff, not the worktree's.

## Index overrides of section and PLAN.md text (binding)

Where a section file or `PLAN.md` says otherwise, this table wins. A later edit of a section file or PLAN.md that matches a row satisfies it.

| Topic | Section or PLAN.md text overridden | Binding form |
|---|---|---|
| Batch 0 | section-01's header "Batch: 1 (lands first)"; section-08's Dependencies bullet "The batch-1 worktrees are cut from `wp29-p0` before S01 merges" and task 08-02's preflight `git -C <wt> cherry-pick ... wp29-s01`; every section's merge order that starts `S01, S09, ...` | S01 is batch 0 and lands before any batch-1 worktree is cut (R-05). There is no cherry-pick. 08-02's preflight keeps only its check (`grep -c '<!-- WP-29 P0.12b -->' CHANGELOG.md` prints 1, and `test/test_wp29_truth.cscript` exists); if the check fails, the section stops and reports. Batch 1's merge order is `S09, S03, S02, S04, S06, S07, S05, S08`. |
| Full suite | Every section's "run the full suite once" wording, and every "prefix `FULL_SUITE_RERUN=1` only on the third launch" or "only if the hook refuses" (e.g. section-08 Notes "The full suite", section-15 R15-9) | "Full-suite runs": wait for a free suite, one planned run per commit, always with `FULL_SUITE_RERUN=1`. |
| Browsers | Every `dash_nobrowser=1` placed in the environment of a Stata run | That variable has no effect. S08 task 08-19's signal driver do-file sets `global dash_nobrowser 1` after `adopath ++`. So does every probe, driver or extract do-file a section writes that runs dash (new extract scripts among them). Scripts that already set the global, such as S07's, S12's and S09's `release_gate_venv.do`, are unchanged. |
| Merging | Every section's "the merger lands them with `patch -p1`" (e.g. section-10 Notes) | The merge routine of step 2: `format-patch` piped into `git apply --index -3`, name check, `detect_changes`, `git commit -F`, stat check. |
| Pull from main | The commit tasks of sections 02-14, which have no merge-from-main step | Step 6 of the per-entry cycle, `git -C <wt> merge --no-edit main`, runs before each pre-commit full run. S01 (task 01-08) and S15 (R15-9) already do this. |
| Fixtures | `test/test_fixtures_are_committed.py` in tasks 02-03, 10-01, 10-14, 11-01 and 11-13 | R5: that file is not edited. |
| Copy lists | section-02 D-g ("no other batch-1 section adds constants"); section-11 SD-11/TR-11.8's anchor line 28975; the old R2 row for S11 (`_LPOLY_ROT_C` "replaced in place", helpers after `"_t_ppf"`, `_bootstrap_ci` removed); section-08's Notes for S13 (copy `_dash_private_write`, `_dash_private_msg`, `_dash_root_name`, `_dash_mode_private`) | The R2 table above: S04 and S07 also add constants (S05 adds none); S13 copies TR-13.11's sixteen functions and none of S08's private-file helpers; S11's helpers go after `_dash_lpoly_weights` at 28965, `"_LPOLY_ROT_C"` leaves the constants tuple and is not replaced there, and `_bootstrap_ci` stays (SD-12). |
| cscripts | section-07's "R1 exception" for `test_gaps2_truth.cscript` CV-01 | It is part of R1 now. |
| GitNexus | The `gitnexus analyze` worktree step of tasks 02-01, 03-01, 04-01, 06-01, 07-03, 08-02, 09-01, 10-01, 10-14, 11-01, 11-13, 12-01, 13-01 and 14-01; every "run `gitnexus_detect_changes()` before every commit" made in a worktree | R8: one main-checkout index; impact at the batch base with `repo: "dash"`; `detect_changes` at landing. |
| Plan files | Section text that cites `index.md`, `PLAN.md`, BRIEF or a sibling section file by a relative path; any text that says `.ultraplan/wp29/` is untracked, is never committed, or is read only by absolute path | The plan is tracked: step 0a commits `.ultraplan/wp29/` on `wp29-p0` before any worktree is cut (round 2, answer C), so worktrees carry it. Read it at the absolute main-checkout path (step 0e), which governs. No section commit stages or edits a plan file (G6); only step 0a, and an orchestrator amendment committed alone ("Plan files" delta), commit `.ultraplan/wp29/`. |
| Checkpoints | 08-01, 13-02 item 2 and 14-01's SD part ask the maintainer mid-batch; 02-02, 04-02, 13-02 item 1 and 14-01's impact part ask after the worktree is cut | Each verifies the record made before its batch (the ratified record of 01oct2026, copied by step 0f into `<scratch>/wp29-ratified.txt`; step k.0's impact record) and stops only if that record is missing, reads "pending", or differs from what its section was re-planned on. |
| Closeout | PLAN.md §7 S15's heading "one commit per step", and S15.3's "including the cert wall time" | S15 makes five or six commits: S15.1, S15.2, S15.3, S15.4, S15.6 (only if the release date must move) and S15.7. S15.5 commits nothing. S15.3 writes `<to be measured in 15-17>` placeholders. The cert wall time and its delta are recorded in S15.7 (task 15-17), after S15.6's release run has measured them. |
| Date axis (answer 1, 01oct2026) | Any section text that puts a lone `lfit`, `qfit`, `lfitci`, `qfitci`, `kdensity`, `lpoly` or `lpolyci` over a date on a numeric axis; section-11 LW-05's "(S05 units)" and any S11 pytest that compares a date lpoly's drawn x with Stata's `gx`; the D05-1 row's "S10, S11 and S12 re-derive any date-axis pin" | dash keeps its date axis (section-05 D05-1 struck). Section-11 LW-05 is edited to match: each drawn x of a `%td` lpoly is compared with `(gx - td(01jan1970))*86400000`, of a `%tc` one with `gx - tc(01jan1970 00:00:00)`, never with `gx`; every S11 pytest that compares a date lpoly's drawn x does the same, while bandwidths (`r(bwidth)`, `bwidth()`, `pwidth()`) stay in Stata units. S10 (its c23 is a plain date x) and S12 (its lone-lfit test checks only the stale cue) need no text change; each still re-derives at its batch base any date-axis pin it finds. |
| Private locations (answer 2, 01oct2026) | Any text in a section file, PLAN.md, section-01's appendices or section-15 that refuses an unsafe private root or location with r(603), ends a data write that cannot be made private with r(198), or refuses, re-modes or notes a folder the user names | Section-08 R-8: a privacy shortfall proceeds (rc 0) with one `dash: note: …` per command; a planted `dash-<uid>` is left alone for a 0700 fallback; the anti-hijack guards (a link, FIFO or device, hard-linked or foreign file at the target, a name that appears mid-write, a replaced `app.py`) end r(7102) and are documented as anti-hijack, not privacy; only an operating-system failure to create a folder ends r(603). |
| Served app writes (answers 2 and 3) | section-08 R-3's "the app writes no file"; its guard `TestTheServedAppWritesNoFile::test_the_generated_app_has_no_file_writing_call`; its Notes for S13 ("allow exactly one `_dash_private_write(…, exclusive=True)` call", copy `_dash_private_write`, `_dash_private_msg`, `_dash_root_name`, `_dash_mode_private`, "print the R-8 note itself") | R-3 holds for S08's three commits. S13 owns the app's own writes: in task 13-06 (which adds TR-13.8a's functions; `test/test_private_files.py` joins its `<files>`) it flips that guard in place under R7, with a `Flipped:` line. **Writes:** the generated source may write only through `_dash_private_page` (one `tempfile.mkdtemp` folder, one `os.open` with `O_CREAT`, `O_EXCL` and `O_NOFOLLOW` at `0o600`, its `os.fdopen` write). Both files the app writes go through it: `_dash_announce_key`'s `link.html` (TR-13.8a) and `_dash_open_tokenized`'s `open.html` redirect page (TR-13.8 step 3). **Removals:** `shutil.rmtree` (under any alias, such as `__main__`'s `_shutil`, whether called or passed as a callback) may remove only a folder returned by `_dash_private_page`, at exactly these sites: (1) `_dash_private_page`'s own failure path, `shutil.rmtree(d, True)`; (2) `_dash_bokeh_serve_key`'s `atexit.register(shutil.rmtree, d, True)`, `d` from `_dash_announce_key`; (3) TR-13.10's redirect cleanup in `__main__`, `_server.io_loop.call_later(_DASH_REDIRECT_TTL_S, _shutil.rmtree, _dash_open_dir, True)`, `_dash_open_dir` from `_dash_open_tokenized`; (4) `__main__`'s `finally:`, `_shutil.rmtree(_dash_open_dir, True)` and `_shutil.rmtree(_DASH_LINK_DIR, True)`, `_DASH_LINK_DIR` from `_dash_announce_key` through `_dash_server_app`. The flipped guard names each site by its enclosing function (or the `__main__` block) and its folder argument (`d`, `_dash_open_dir`, `_DASH_LINK_DIR`). 13-06's flip already admits 13-07's two `__main__` sites, so 13-07 needs no second flip. Any other write-mode `open(`, `os.open`, `write_text`/`write_bytes`, `tempfile.` or `shutil.` call or reference, and any `rmtree` at another site or of another folder, still fails it. S13 copies none of S08's private-file helpers (R2 row S13). The link file follows section-13 K-8 and K-9, not R-8's command note: it is written 0600 wherever the disk allows, otherwise written with its own `dash: note:`, and, when no folder takes it at all, the link is printed once after `_DASH_LINK_UNWRITTEN` and the server keeps serving (round 2, answer A; no link failure stops the server). R-8 governs copies of the data and the user's folder; the link file holds the credential. |
| Served index (answer 4, 01oct2026) | Any text that names the served `index` as a residual, `TestTheServedIndexResidual`, an S3 BUGS.md entry opened by S14, or five open BUGS.md entries after the closeout | Section-14 TR-14.16/TR-14.18: every served source's `index` carries the saved page's dense ranks, pinned failing-first by `TestTheServedIndexIsARank`; S14 opens no entry; S15 expects 4 open entries (AC-15.1). |
| Link that cannot be written (round 2, answer A, 01oct2026) | section-13 round-1 K-8's stop ("the server on port %d was stopped: its link was not written", exit status 2) and its tests `test_a_key_that_cannot_be_announced_is_not_served` and `test_a_link_that_cannot_be_written_stops_the_server`; section-08's Notes for S13 that say S13 "stops the server only if that fails too" or name that failure text; any text in a section file, PLAN.md, section-01's appendices or section-15 that says the key is never printed without K-9's exception | Section-13 K-9: when no folder dash tries takes the link file, nothing is stopped; `_DASH_LINK_UNWRITTEN` and the full link alone are printed exactly once (per launch under `dash serve`, per process under `python app.py`, per app path per process under `bokeh serve`) to the output of whoever started the server, which keeps serving. It is the only case in which the key is printed. The only stop left is an `--address` no link can name (exit status 2). |
| Launch from the open file (round 2, answer B) | section-08 R-8's app-substitution residual and `_dash_same_file`; section-13's "check, Popen, then key" and any `proc.stdin.write` of bytes | section-08 R-9/TR-08.8a: verified read, then Popen of `python -P -c _DASH_BOOT`, then the framed hand-over, then S13's key line, both through `_dash_child_stdin` |
| S12 second wave (section-12 critic amendment C1) | section-11's header "Blocks: 14, 15 (closeout)"; section-11 Dependencies' "**Parallel batch:** 2, with S10, S12 and S13" (section-11:130); any text that cuts every batch-2 worktree at `batch-2-base` | 12 ← 11. S11's header reads "Blocks: 12, 14, 15 (closeout)", and its "Parallel batch" line reads "2, with S10 and S13; S12 is cut after this section lands (12 ← 11, section-12 C1). Merge order: S10, S11, S12, S13." S10, S11 and S13 are cut at `batch-2-base`; S12 is cut after S10 and S11 land and the merger's interim full run is green, at `<scratch>/batch-2-s12-base.txt` ("Batch 2", step 2). |
| Closeout and ratification | section-15 R15-8, TR-15.7 and 15-10's "D.10, if R-6 was approved", 15-06 item 4 and Appendix D.10 | R-6 is ratified and S01 writes ROADMAP's BR-29.10, BR-29.11 and AC-29.6 in their final, ratified form (PLAN.md §7 S01 item 1). S15 applies no D.10 rewording and asks nothing about it (section-15 is edited to match). |

## Verification gates

| Gate | When | Command / check | Pass condition |
|---|---|---|---|
| G0 | Step 0a | `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q` under "Full-suite runs" | green; `git show --stat HEAD` lists exactly `TWOWAY_COVERAGE_AUDIT.md`, `test/test_packaging.py`; `git show --name-only --format= HEAD~1` lists exactly the 17 files of `.ultraplan/wp29/` (round 2, answer C); both messages pass G7 |
| G1 red-first | Each P0 cycle, before the fix | the entry's new tests at the cycle's base | every new regression test FAILS, with the failure text saved; new tests of behaviour already right are listed separately as "guard" tests |
| G2 green | Each P0 cycle, before its commit | changed test files; the section's cscripts through the driver with `WP29_ONLY=S<NN>`; `git -C <wt> merge --no-edit main` (`Already up to date.`); then one full run under "Full-suite runs" | 0 failed; every case of the section's truth block prints `PASS`; no new SKIP |
| G3 parity | Each section that changes a drawing | `python3 -m pytest test/test_mode_parity.py -q -n0` | green, with the section's CORPUS cases added; both modes draw the same before and after a filter move |
| G4 served guards | Each section that adds a module name | `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` | green |
| G5 tracking | Each commit | `python3 -m pytest test/test_tracking_documents.py -q -n0` | green: the closed entry names tests that exist; its `WP29_OPEN` key is gone; its marker(s) are gone |
| G6 scope | Each commit: in the worktree, the name check; at landing (merge step 4) and before each S15 commit, both | `git diff --cached --name-status`; `gitnexus_detect_changes({scope: "staged", repo: "dash"})` in the main checkout only (R8) | only the section's files and symbols; the landed names equal the worktree commit's (`<scratch>/names-<sha>.txt`); no `CLAUDE.md`, `.gitignore`, `.gitnexus/`, `.ultraplan/wp29/`, scratch or `*.html` |
| G7 message | Each commit | `git log -1 --format=%B \| grep -Ei 'claude\|anthropic'` | no match, before and after committing |
| G8 batch | After each batch merge (batch 0 included) | full suite once under "Full-suite runs"; R2 registry tests; `test_wp29_truth.cscript` (all blocks) and every touched area cscript through the driver; then the GitNexus rebuild of step 0c | green; `list_repos` shows `dash` at the new HEAD |
| G8a interim | Batch 2, after S10 and S11 land, before S12 is cut (C1) | R2 registry tests; full suite once under "Full-suite runs" (`<scratch>/batch-2-interim-full.log`) | green; then `<scratch>/batch-2-s12-base.txt` is recorded and S12's worktree is cut |
| G9 security | S08, S13, S14, S05, S04 | the section's security tests (listed in PLAN.md risk register) | green; the threat each closes is named in the commit body |
| G10 release | S15.6 | `make test`, `make test-dev`, `make cert` (timed against `wp29-cert-baseline.log`), `make gate`, each once, serialised under "Full-suite runs" | all green; the cert wall time and its delta are recorded in S15.7 (task 15-17), after this run |
| G11 exit | S15 | PLAN.md "Exit gates" E1-E12 | every gate met |
