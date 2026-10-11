# Section Index — WP-30: close the drop-in P1 gaps

> Architect pass, 03oct2026, on branch `wp30-p1`, cut from main `c96facd` ("Merge branch 'wp29-p0'"). Source: `.ultraplan/handoff/DROPIN-REMAINING.md` §3 "### P1: common `twoway` usage not honoured" (lines 64-170), 35 items (P1.1-P1.35). Each item was researched at `c96facd`, with measured twoway truth, in `.ultraplan/wp30/research/p1-NN.md`. Beside this file: `manifest.json` (the 58 sections, 22 batches and 22 residuals in machine-readable form; every table below that lists sections is drawn from it), `PLAN.md` (package-level context, goals, user stories, business requirements, risks and exit gates), `decisions.md` (the maintainer's binding answers M1-M12) and `decision-register.md` (235 per-question rulings, 5 cross-cutting rulings, the new P2 residuals and the ratification list).
>
> WP-30 reuses `.ultraplan/sections/BRIEF.md` (WP-28's writing brief, which WP-29 also used) **unchanged except where "Deltas from BRIEF.md (WP-30 forms)" below says otherwise**. A WP-30 section file is `section-NN-<slug>.md`, with the slug from `manifest.json`. It is written to BRIEF.md's layout: Review amendments, Overview, Risk, Dependencies, Evidence, User stories, Business requirements, Technical requirements, Boundaries, Stata truth, TDD test stubs, Test plan, Tasks in BRIEF's XML schema, Section completion criteria, Notes. Where a section file, `PLAN.md`, `manifest.json` or a research note disagrees with this index, this index wins ("Index reconciliations", the merge rules and the gates).

## Overview

- **Total sections:** 58: S01 tracking foundation, S02-S57 (56 fix sections), S58 closeout. "Sn" means section n everywhere in this plan.
- **P1 items:** 35, tracked as 56 BUGS.md entries that S01 opens, one per fix section.
  - 15 items are one section each: P1.5, P1.6, P1.7, P1.10, P1.16, P1.19, P1.22, P1.24, P1.27, P1.29, P1.30, P1.32, P1.33, P1.34 and P1.35.
  - 19 items are split into parts a and b, and P1.15 into a, b and c (A138).
  - Two items shrink under the maintainer's decisions: P1.34 to runner portability (M4) and P1.35 to the Stata 19 floor (M2). P1.22 closes by disposition (M12).
- **Commit units:** 63 fix commits, one per fix section, except that S05, S19, S37, S41, S42, S51 and S56 land as two. Add the plan commit (S00, step 0a), S01's commit and the closeout's five or six commits (S58.1-S58.4 and S58.7, plus S58.6 only if the release date must move; S58.5 commits nothing). That makes 70 or 71 commits on `wp30-p1`.
- **Parallel batches:** 22, numbered 0-21 as in `manifest.json`.
  - Batch 0 is S01 alone.
  - Batches 1-19 hold two or three sections each (two in batches 1 and 13).
  - Batch 20 is S57 alone, and batch 21 is the closeout, in the main checkout.
  - Every dependency lies in an earlier batch, so no batch has a second wave. WP-29's batch 2 had one.
- **Full-suite runs planned:** 100 pytest runs (101 if the release is re-dated), 4 certification runs and 1 release-gate run. All of them go through the machine-wide queue at 6 CPUs ("Full-suite runs").
- **Risk:** 4 green (S01, S07, S26, S58), 51 yellow, 3 red (S21, S44, S57). **Effort:** 5 S, 42 M, 11 L.
- **Decisions:**
  - 12 maintainer decisions (M1-M12, binding).
  - 235 register rulings plus 5 cross-cutting ones (architect ids A1-A137, `decision-register.md`).
  - 19 index decisions (A138-A156, below) and 17 index reconciliations of manifest and register (IR-1..IR-17).
  - The 44 ratification items (the register's 28 rulings, the precondition P-1 and 15 section maintainer questions, "Decisions for maintainer ratification") were answered 06oct2026: 35 as recommended, rows 4, 8, 12, 22, 25, 27, 32 and 36 CHANGED, row 29 otherwise than recommended. The section files, the register, manifest.json and PLAN.md carry the answers (A151).

## Decision record

### Maintainer decisions (binding; recorded 03oct2026 in `decisions.md`, copied verbatim)

A section must not contradict these.

| Id | Item | Question | Answer (verbatim choice) | Binding reading |
|---|---|---|---|---|
| M1 | P1.2, P1.3, P1.12 | Match Stata's default look and size units? | "Match Stata (Recommended)" | dash adopts each scheme's look (centred, unbolded title; natscale ticker and padding; no default alpha 0.8) and Stata's relative size units (numbers and keywords in Stata units, #pt, *#, the full keyword ladder). Every look change gets a CHANGELOG line under "Results that change". |
| M2 | P1.35 | Stata floor | "Raise floor to 19" | dash declares version 19 and refuses an older Stata with a clear message. Only /usr/local/bin/stata-mp (StataNow 19.5) is run; the Stata 14-18.5 binaries on this Mac are never run. |
| M3 | P1.33 | Python floor | "Measure, then lower (Recommended)" | Both pytest suites run under Python 3.11 and 3.12 in scratch virtual environments; the floor becomes the lowest version that passes, with 3.13-only code given a fallback or guard. |
| M4 | P1.34 | Platforms | "Defer P1.34" | WP-30 only makes the runners portable (no hard-coded `arch -arm64` or maintainer paths). Measuring Linux, Windows and Intel Mac moves to a later package. |
| M5 | DROPIN §4 Refuse vs note (P1.1, 5, 6, 8, 9, 10, 13, 15, 18, 19, 20, 21, 24, 27) | Which rule should WP-30's new code follow? | "Refuse like twoway (Recommended)" | Input twoway refuses (malformed sub-options, out-of-range values, a misplaced `..`, wrong-case keywords, bad by() arguments, unknown saving() sub-options, options on types twoway refuses them for) is refused with twoway's return code and words, in the areas WP-30 touches. A valid twoway option dash cannot draw is still named in a note, never refused. The rest of the option surface (P2.21) is not swept by WP-30. Every newly refused form gets a CHANGELOG line under "Changed behaviour (may need your do-files changed)". |
| M6 | A11/C8 (P1.26, P1.18) | Notes where twoway is silent? | "Match twoway: silent" | Where twoway draws the same picture and prints nothing (a layer whose own if/in keeps no row; scale(off), nolabels, noticks, titlegap ignored under by()), dash prints nothing in either mode. Notes remain only for what dash draws differently from twoway. |
| M7 | P1.25 (DISCOVERY Q30) | Third-party and PLUS schemes | "Whole ado-path (Recommended)" | dash resolves scheme(NAME) and an inherited c(scheme) along Stata's whole ado-path (BASE, SITE, PLUS, PERSONAL, OLDPLACE, added dirs, cwd) under both file names, with name, per-directory realpath containment and size guards; scheme files are parsed as data, never executed. |
| M8 | P1.28 | graph export route | "Document + SVG button (Recommended)" | dash returns r(filename); notes once when a Stata graph in memory would be what graph export writes; the help documents the limit; both modes gain a client-side "Save as SVG" toolbar action. A Chrome-driven `dash export` waits for the deferred platform package. No output_backend(svg). |
| M9 | P1.30 | bokeh ceiling | "Cap at next unverified (Recommended)" | dash_setup installs bokeh>=3.8,<3.10 (raised only after re-verification; to <3.11 if 3.10 is verified inside WP-30). At run time above the window: a note and continue; below the floor: refused. |
| M10 | P1.33, P1.30 | Network downloads | "Approve downloads (Recommended)" | pip wheels and an arm64 Python 3.11 may be downloaded, only into scratch virtual environments during execution, never installed elsewhere. |
| M11 | P1.27 | saving() path characters | "Allow; keep sink checks (Recommended)" | saving() accepts `..` and ; & \| < > as twoway does; it keeps refusing double quote, backquote, $, control characters and a leading `-`. On Windows a path holding cmd metacharacters (including % and !) is written but not opened, and its path is printed. Pinned tests P2-80 and PV-04/05/14 are flipped with the reason, never deleted. |
| M12 | P1.22 | function fallback | "Close by disposition (Recommended)" | The ten-function points-free fallback stays; anything else it meets gets a "needs Stata's points" note; P1.22 is recorded closed by WP-29 P0.6 plus that note. |

### Architect decisions (this pass; the section files inherit them)

The register's architect ids run A1-A137 (the X rows included); this index continues at A138.

| Id | Decision | Why |
|---|---|---|
| A138 | **Grouping.** The sections are those of `manifest.json`. These 20 items are split into parts, each part its own section and BUGS.md entry: P1.1 (a S11, b S20); P1.2 (a S15, b S16); P1.3 (a S21, b S44); P1.4 (a S24, b S33); P1.8 (a S40, b S45); P1.9 (a S49, b S55); P1.11 (a S09, b S29); P1.12 (a S08, b S13); P1.13 (a S30, b S43); P1.14 (a S32, b S36); P1.15 (a S28, b S48, c S53); P1.17 (a S14, b S27); P1.18 (a S31, b S52); P1.20 (a S38, b S47); P1.21 (a S39, b S50); P1.23 (a S35, b S17); P1.25 (a S07, b S34); P1.26 (a S06, b S23); P1.28 (a S22, b S54); P1.31 (a S46, b S57). The register's part labels map to sections as follows. P1.2a/b: S15/S16. P1.3-A: S21; P1.3's date part: S44. P1.4 (a-f, h, i): S24; P1.4 (g, ColorBar, unread directives): S33. P1.5a: S18. P1.6a/6b: S51's two commits. P1.8a/b: S40/S45. P1.9a/b: S49/S55 (IR-13). P1.11's TeX half: S09; its SMCL half: S29. P1.12a/b: S08/S13. P1.13a/b: S30/S43. P1.14 A/B: S32/S36. P1.15c: S53. P1.17a/b: S14/S27. P1.20a/b: S38/S47. P1.21a/b: S39/S50. P1.23's partition and step 5: S35; P1.23b: S17. P1.25A/25B: S07/S34. P1.26-A: S06; P1.26's served half: S23. P1.28a: S22; P1.28 B1 (Save as SVG): S54. P1.31a: S46; its worker: S57. P1.33 A/B: S05's two commits. P1.34b: S02. P1.35's sweep: S03. | The manifest's symbol-level model: an L/XL item, or a pair of parts forced apart by a dependency (P1.17, P1.25), is split so that no two sections of one batch edit the same function. |
| A139 | **Batch rules.** There are 22 batches (0-21), each with at most 3 sections and 3 items. No two sections of a batch edit the same function. A batch has at most one `ServerAppBuilder._generate_app_source` editor, one `_make_figure_body` editor, one scheme regenerator (merged last; R7) and one axis-finisher editor (R11). Every dependency lies in an earlier batch. The red sections (S21, S44, S57) sit one per batch with lighter partners, and S57 and S58 run alone. **Exceptions, each in disjoint hunks applied in merge order with `git apply --index -3`:** batch 2, S04 and S06 each add one name to `_dash_require_mata`'s `_needed` data list (:242, :247; an R6 in-place data line, recorded by the review); batch 4, `_dash_plot` (S10, S12) and `_needed` (S10, S11, S12), ratification row 31; batch 7, `_dash_process_segment` (S19 :3679-3683 and :4309-4312, S20 the `_dash_validate_opts` call at :4121-4126; recorded by the review, S19 lands first); batch 11, the `color_idx=` keyword in seven mappers S32 edits (S33), row 37; batch 12, S34's four one-line `_generate_app_source` edits beside S35 (an R12 exception), row 38. A struck row is re-planned before that batch's base is recorded. | Parallel worktrees then merge in distinct hunks. With no second wave, no batch needs an interim full run or a second cut (WP-29 batch 2 needed both). |
| A140 | **Entry and marker ids.** An entry is `P1.<n>` for a whole item, `P1.<n>a`/`P1.<n>b` for a part, and `P1.15c` for P1.15's third part (the only `c`). S01 opens 56 entries. The CHANGELOG marker is `<!-- WP-30 P1.<n>[a\|b\|c] -->`, matched by `<!-- WP-30 (P1\.\d{1,2}[abc]?) -->`. The task brief's `[a\|b]` form is extended by `c` for P1.15c alone. | One id per entry, used alike by BUGS.md, `WP30_OPEN`, `WP30_LISTS`, the markers and the commit subjects. |
| A141 | **Commit subjects** end `(WP-30 P1.<n>)`, `(WP-30 P1.<n>a)` (or `b`, or `P1.15c`), `(WP-30 S00)` (the plan), `(WP-30 S01)` or `(WP-30 S58.<k>)`. Both commits of a two-commit section end with the section's one entry id, and their subject text says which half each is. A security section's body names the threat it closes (G9). No subject, body, BUGS line, CHANGELOG line or help line names a tool or vendor (G7). | This is BRIEF's D1 rule with WP-30 ids, and project rule 6 (commit messages). |
| A142 | **One truth script** (register X.4/A136). `test/test_wp30_truth.cscript` is created by S01 and registered as runner block `// 69.`, which makes 68 scripts. It holds S01's scaffold block and one stub block per fix section (S02-S57) in section order, followed by the marker line. No section registers another runner block. | WP-28/WP-29 precedent; the hygiene pins live in one section (R1). |
| A143 | **Area scripts and case ids.** Refusal, message, return-code and setup checks join the existing cscript for their area (WP-29 rule R1). Each section's new cases use the prefix the manifest table gives; every prefix was checked unused at `c96facd`. Cases added to an existing prefix take the ranges allocated in that table (register X.3/A135: SB, PV, ENV, HON and NC). | Ids stay unique across parallel worktrees, and the colliding research ids (SB-21..24, PV-28, HON-3x, SL, DA) are resolved before any section writes. |
| A144 | **Tracking test.** S01 adds the following to `test/test_tracking_documents.py`, mirroring WP-29's block (:1240-1525): `WP30_OPEN` (56 keys, entry id to title, one per line, in entry order), `WP30_LISTS`, `WP30_ALL`, `_WP30_MARKER`, `_WP30_OPEN_FORM` (`^  - Resolution: Not fixed because WP-30 section \d{2} has not landed\. Graded S[1-3] \(WP-30\): \S`) and `TestWp30Tracking`. It also extends `TestNoOpenEntryBlocksARelease::test_no_open_entry_is_s1_or_s2`'s allowance (:512-516) to `set(WP29_OPEN.values()) \| set(WP30_OPEN.values())`. | S01's open S1/S2 entries would otherwise turn the suite red (rule 4). The precedent is `WP29_OPEN`. |
| A145 | **Tracking documents are the closeout's.** Only S58 edits ROADMAP.md, the GAPS2.md "Tracked" lines, GAPS.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, `.ultraplan/handoff/DROPIN-REMAINING.md`, AGENTS.md and the closeout rows of `test/fixtures/rejected_options.json`. A fix section that has text for them writes it in a "Notes for the closeout" paragraph of its section file. S51 still updates the stale `rejected_options.json` rows its own options make wrong (manifest scope). | A Tracked line must name the landed commit's sha on `wp30-p1`, and a single editor removes every tracking-document conflict. |
| A146 | **Entries beyond the 56.** The register asks for its own BUGS.md entry for P1.5.7 (the narrow-width display-format writer, S18) and for P1.25.6 (per-graph schemes in the served app, S34). Each section adds that entry already closed, in its fix commit, after its own failing-first test has been saved under G1. Such an entry needs no `WP30_OPEN` key, because it is never open on `wp30-p1`. P1.12.6 (nonselection and muted glyphs keep their creation values) is fixed by S08 under its own entry P1.12a (ratification row 27, 06oct2026): P2.49 is not filed, no extra entry is opened, and S58 writes the register's P2.49 row closed. | This satisfies rule 7 and the register without changing the manifest's one-entry-per-section count. |
| A147 | **CHANGELOG lists.** S01 places 84 markers, in the six lists of the "P1 coverage" table: Results that change (34), Changed behaviour (24; P1.17a carries one for S14's new refusal), Fixed in WP-30 (10), New (7), Security (5) and Requirements (4). `### New` is added to the manifest's five lists because S07, S22, S42, S46, S51, S54 and S56 add things a user can now do. Two sections widen their own row in their closing commit (R4): S20 adds a Results that change line for P1.1b and S34 a Changed behaviour line for P1.25b, so the landed lists hold 35 and 25 WP-30 lines; S58 counts from the landed `WP30_LISTS`, never from these figures. | A capability that was missing is reported where users look for new things. Its refusals still go under Changed behaviour. |
| A148 | **Map anchors.** S01 places one comment anchor per section, `# WP-30 S<NN> (P1.<n>[abc]): <section name>`, in four places: (1) at the end of `test/function_test_map.py` `FUNCTIONS`, after `'main'` (:800); (2) at the end of `SETUP_FUNCTIONS` (:867-895), for S05, S25 and S41 only; (3) at the ends of `test/program_coverage_map.py` `COVERAGE["dash.ado"]` (before :298) and `COVERAGE["dash_parse.mata"]` (before :608); (4) at the end of `COVERAGE["dash_setup.ado"]` (before :338), for S03, S05, S25 and S41 only. A section adds its keys under its own anchor, in alphabetical order. S58 deletes the anchors left empty. | `FUNCTIONS` is not globally sorted (762 keys) and `COVERAGE` follows source order, so a global alphabetical place would make parallel inserts collide. Anchors give each section its own hunk. |
| A149 | **Served copy lists are append-only** (register X.1/A133), at the anchors of R2. In its one commit S01 adds `test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName::test_every_listed_name_exists`, which asserts that every name in both `_glyph_layer_lines` tuples is defined in `dash_render.py`. Measured green at `c96facd`: all 145 constants and all 312 functions are defined. | The copy loop (`getattr(_mod, _name, None)`, then `continue`) skips a misspelt name silently, and the fault would show only on the served page. |
| A150 | **One note channel first** (register X.2/A134). S06 lands in batch 2, merged last, and migrates the 29 `UserWarning` needles. Every note added later uses `_dash_emit_note` and the `(note: …)` form (A82, A84), and its tests count note text through S06's helpers. | Otherwise the needles would migrate twice. |
| A151 | **Ratification before batch 1.** The 44 rows under "Decisions for maintainer ratification" (28 register rulings, the precondition P-1 and 15 section maintainer questions) are put to the maintainer at plan time. Row 29 (P-1) is acted on before step 0a, because G0 is red without it. Step 0f copies the answered record into `<scratch>/wp30-ratified.txt`. S01 (batch 0) may run first, because it changes no shipped file and no listed ruling changes its form. Batch 1 is not cut while any row reads "pending". | WP-29's lesson: a stop inside a parallel batch halts its worktrees mid-batch. |
| A152 | **Scheme regeneration.** One regenerator per batch: S07 (3), S15 (5), S21 (7), S24 (8), S30 (10), S33 (11), S36 (12), S37 (13, in its second commit), S47 (16), S50 (17), S53 (18) and S56 (19). Each runs `scripts/extract_scheme_truth.py` and rewrites all 26 `dash-<name>.scheme` files (20 tracked at `c96facd`, 26 after S07) and `test/fixtures/scheme_truth.json` inside its own fix commit, and lands last in its batch. S07 (batch 3) and S37 (batch 13) are the exceptions and land first, because no partner of their batch touches the extractor, a scheme file or `scheme_truth.json` (S08/S09; S38). A regeneration that turns a shipped-file pin red (the directive count and `test_no_directive_for_what_dash_does_not_draw`, R10) moves it in the same commit. Generated files are never patched by hand. | Two regenerations in one batch would conflict in every generated file. |
| A153 | **The axis-finisher chain.** S21 creates the served `_dash_refinish_axes`, the saved `_DASH_AXIS_FINISH_JS`, `_dash_default_ticker`, `_dash_plot_margin`, `_dash_axis_plan`, `_dash_layer_extent` and `_dash_tag_hull_roles`. One section per batch then extends them: S27 (batch 9), S35 (12), S44 (15), S47 (16), S50 (17) and S52 (18). The saved re-finish is appended to `_FILTER_JS` by a module-level statement placed directly after `_DASH_AXIS_FINISH_JS`'s assignment (`_FILTER_JS = _FILTER_JS + _DASH_AXIS_FINISH_JS + <guarded call>`, S21 TR-21.11), never inside `_FILTER_JS`'s literal and never by moving `_DASH_AXIS_FINISH_JS` above `_FILTER_JS` (S44 defines its port before the finisher); `_FILTER_JS` is not otherwise edited for axes, and every later extender keeps that form. A layer the saved page leaves unfiltered stays in the saved hull as drawn, so saved equals served only where both draw the same layers (S21 D-21e2; R8). S21's call sites cover dates, so S44 never edits `_generate_app_source`. S55 never edits `_dash_axis_plan` (its 55-04 is a guard check that stops and reports). S57 (batch 20) audits the final served move path. | Each extension lands on the previous one's text, one at a time. |
| A154 | **The guard order at the top of `dash`.** S03's Stata guard, then the Mata guard, then S25's dependency guard, then S12's prefix strip, then S22's rclass dispatch. Each section inserts its statement at its place in that order and edits no other guard's lines. | Five sections in five batches edit the first lines of one program. |
| A155 | **Help paragraph ownership** (R3): a section edits only the `dash.sthlp` and `dash_setup.sthlp` paragraphs its scope names. Prose counts belong to their mover (R10). | Parallel sections then edit the help in distinct hunks. |
| A156 | **Two-commit sections** (S05, S19, S37, S41, S42, S51, S56). The first commit adds its own failing-first tests and its half of the fix, leaving the BUGS.md entry, its `WP30_OPEN` key and its markers in place. The second commit closes all three, and its CHANGELOG lines cover both halves. Each commit runs the whole per-entry cycle, including a full run. | No commit is red, and the tracking test sees one closure per entry. |

### Per-question rulings (`decision-register.md`)

`decision-register.md` is the authority for every per-question ruling, and a section file cites the register row it implements by id (P1.n.k, X.n). It holds:

- 235 rulings: 135 research questions, 95 critic-raised ones marked [C] and 5 research residuals;
- 5 cross-cutting rulings (X.1-X.5);
- the strict readings of M decisions: P1.12.1 option B, P1.35.3 `version 19`, P1.20.7 `bgcolor()`, P1.3.6 re-hulled explicit axes, 26 M5 refusals and 11 M6 silences;
- 16 new P2 residuals (P2.42-P2.57; P2.49 withdrawn by ratification row 27, because S08 fixes it);
- the scope changes of P2.11-P2.14, P3.2, P3.7, P3.9 and P3.11.

Where the register and `manifest.json` differ, "Index reconciliations" below decides.

### Deltas from BRIEF.md (WP-30 forms; everything not listed applies as written)

| BRIEF rule | WP-30 form |
|---|---|
| Base commit for "fails at" | The `wp30-p1` HEAD a section's worktree was cut from is recorded in `<scratch>/batch-<k>-base.txt`. Step 0d writes `batch-0-base.txt` (the step-0a plan commit, which is S01's "failed at" sha). After batch k is green, step k.5 writes `batch-<k+1>-base.txt`. Regression lines read `-- failed at <sha> with <text>`. `<scratch>` is the orchestrator's scratch directory for WP-30 (`.../scratchpad/wp30/`). It does not survive the session, so a section file quotes the measurements it relies on and never cites a scratch path as its only evidence. |
| Integration branch / worktree branch | `wp30-p1` / `wp30-s<NN>`, with the worktree at `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s<NN>`. |
| Commit subjects (D1) | A subject ends `(WP-30 P1.<n>)`, `(WP-30 P1.<n>a)` (`b`, or `P1.15c`), `(WP-30 S00)`, `(WP-30 S01)` or `(WP-30 S58.<k>)` (A141). Each commit closes at most one entry; the two commits of a two-commit section share it (A156). |
| Truth script | `test/test_wp30_truth.cscript` is gated by the environment variable `WP30_ONLY=S<NN>`. A block header is `* ==== S<NN> P1.<n>[a\|b\|c]: <what> ====` and a block closes with `* ==== end S<NN> ====`. The gate's first two lines are `local only : env WP30_ONLY` and `` if inlist("`only'", "", "S<NN>") { ``. Helper programs sit directly above their section's header, never inside another section's block. Blocks run in section order (TestTheWp30TruthScript). The marker line `* ==== append new blocks above this line ====` stays last. The script is runner block `// 69.` (68 scripts). R1 has the hygiene pins. |
| CHANGELOG markers | `<!-- WP-30 P1.<n>[a\|b\|c] -->` markers, 84 in all (A147), are placed by S01 in the existing release `## 0.1.0, 02oct2026 (release candidate)`. Placement and replacement are in R4. A closing commit replaces only its own markers, in place, with lines ending `(WP-30, P1.<n>[a\|b\|c])`. |
| BUGS.md | Entries are opened by S01 (A144) and closed in place by the closing commit: `- [x]`, then `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.<n>[abc]). <what changed, where, both modes>. Pinned by test/<file>.py::<Class>::<test>[, test/<script>.cscript <CASE-ID>][; fixture test/fixtures/<name>.json]. [Residual, deferred (WP-30): …]`. S58 appends `(WP-30, <GAPS2 id>)` to a Resolution only when it marks that GAPS2 id Closed (the Tracked-line rules of `test/test_tracking_documents.py` from :681). |
| `WP30_OPEN` | A closing commit deletes only its own key line (A144, R5). S58.1 leaves the map empty and pins it so. |
| Tracking docs | S58 only (A145). |
| Copy-list anchors | The R2 table, measured at `c96facd`: `ServerAppBuilder` (class 32760); `_glyph_layer_lines` (def 32834) with its constants tuple at dash_render.py:32884-33039 and functions tuple at 33077-33425; `_emitted_names` at 33074; `_shared_stat_lines` (def 33485) with its function tuple at 33536-33590 and staticmethod tuple at 33606-33610. |
| Case ids | Each section's prefix, or its range of an existing prefix, as the manifest table gives. Before first use the section greps `test/*.cscript test/*.py test/*.do` for the prefix. |
| Research ids | Research notes that used another section's prefix are renamed in the section file: p1-16's `SL-nn` becomes `KT-nn` (SL is S11's) and p1-03's `DA-nn` becomes `NS-nn` (DA is S35's). p1-26's `NC-01..06` stay S06's, and S23 continues at NC-07. p1-27's `SB`/`PV` ids move into S04's and S12's ranges. |
| Stata invocation and browsers | Stata runs only as `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch> <file>.do` (project rule 10), from worktrees too. A cscript runs through the driver ("The cscript driver"). Every non-cscript do-file a section writes (an extractor, probe or driver) opens with `adopath ++ "<repo>/"` and then `global dash_nobrowser 1`; the environment variable `dash_nobrowser` has no effect. A cscript gets the global from `test/cert_helpers.do:51`. S02 rewrites `stata_slot.sh` itself. Its own tests use its worktree copy; everyone else uses the main checkout's copy, which on this Mac keeps the same effective command after S02 lands. |
| Plan files | `.ultraplan/wp30/` is committed on `wp30-p1` by step 0a, in its own commit, before any worktree is cut. `git add -f` is needed for `manifest.json`, because `.git/info/exclude:58` ignores `*.json`. Agents read the plan at its absolute main-checkout path, which governs. No section commit edits or stages a plan file (G6). An orchestrator amendment is committed alone on `wp30-p1`, with a message that names no tool, before the next batch base is recorded. |
| Full suite | "Full-suite runs" replaces every section's "run the full suite once": one run per commit, through the queue, never relaunched to check on it. |
| Pull from main (rule 4) | Before each pre-commit full run: `git -C <wt> merge --no-edit main`, expecting `Already up to date.`. If main moved, stop and report without committing. The merger does the same in the main checkout before each landing. |
| GitNexus | One index, of the main checkout, rebuilt after each landing (E4). `gitnexus analyze` never runs in a worktree. |
| Evidence from the research | The research notes are committed with the plan (step 0a), so a section file may cite `.ultraplan/wp30/research/p1-NN.md` by path. Scratch-only measurements are quoted with their command and output. |

### Execution conventions learned in WP-29 (binding)

| Id | Rule |
|---|---|
| E1 | **Full-suite runs are serialised machine-wide through the queue script** `<scratch>/full_suite_queue.sh` (step 0g). It waits for the queue lock and for a free suite, then runs `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q -n 6` (or, in its `cert`, `test`, `test-dev` and `gate` modes, the `make` target with `PYTEST_ARGS='-q -p no:cacheprovider -n 6'`). It never uses more than 6 CPUs; the machine has 12. A run is launched in the background and waited for with Monitor, or with an until-loop on the log's `exit=` line. It is never relaunched to check on it: read its log. A refused launch is not a run. |
| E2 | **Landing a section commit** on `wp30-p1` is `git -C <wt> format-patch -1 --stdout <sha> \| git apply --index -3`, then `git commit -F <scratch>/msg-<sha>.txt` with the worktree commit's message copied. Conflicts are resolved by hand under the merge rules, and each resolved path is staged with `git add -f <path>`. A plain `git add` refuses a new `*.json` fixture (`.git/info/exclude:58`), and `patch -p1` drops mode changes. The full routine is under "Landing routine". |
| E3 | **`git branch --show-current` prints `wp30-p1`** in the main checkout before every landing and every closeout commit, and prints `wp30-s<NN>` in a worktree before its commit. Any other output stops the step. Nothing is ever committed to `main`, and no agent checks out, switches branches or stashes in the main checkout. |
| E4 | **GitNexus.** There is one index, of the main checkout. After each landing it is rebuilt there with `gitnexus analyze --index-only --max-file-size 8192`. `gitnexus status` then shows `Indexed commit` equal to `git rev-parse --short HEAD`, and `git status --porcelain` is unchanged by it. **Impact** runs at each batch base, before any worktree is cut, for every symbol a section edits: `gitnexus impact <symbol> -d upstream -r dash`. The output goes to `<scratch>/batch-<k>-impact.txt`, every HIGH or CRITICAL result is reported to the maintainer in one message, and the approval is recorded in that file. `UNKNOWN` (every Stata and Mata program, and dispatch through `map_*`) is confirmed by `grep -n` and recorded as unresolved, never read as low. **Detect-changes** runs at each landing, after `git apply` and before `git commit`: `gitnexus detect-changes --scope all --repo dash > <scratch>/detect-<sha>.txt`. It must show the section's symbols only; a `partial` or `truncated` result is re-run. `gitnexus analyze` never runs in a worktree. |
| E5 | **Stata** runs only through `scripts/stata_slot.sh` (three slots, `STATATMP=<dir>/tmp/` with the trailing slash). A cscript runs through the two-line driver; every other do-file sets `global dash_nobrowser 1` right after `adopath ++ "<repo>/"`. The GUI binary is never run (project rule 10; the block-stata-gui hook stays as it is). |
| E6 | **Known flaky tests** are the four serve/SIGINT timing tests (in `test_serve_lifecycle.py`, `test_serve_token.py`, `test_private_files.py` and `test_help_claims_4.py`/`_5.py`) and port collisions ("Address already in use"). One of them failing in a full run is re-run once, in isolation: `python3 -m pytest '<node id>' -q -n0`. A pass is recorded in `<scratch>/batch-<k>-flaky.txt`, and a second failure is red. They are never ignored, deselected or marked xfail. |
| E7 | **The maintainer's uncommitted edits are never staged.** These are `CLAUDE.md` (the project instructions), `.gitignore` and `AGENTS.md`, whenever `git diff --quiet <file>` fails for them. `git diff --cached --name-only` is checked before every commit (G6). S58 edits AGENTS.md only if it has no uncommitted edits; otherwise it hands the text to the maintainer. |
| E8 | **Never commit to `main`.** S58 reports `git checkout main && git merge --no-ff wp30-p1` without running it (rule 5). |
| E9 | **Pull from main before each pre-commit full run** (rule 4): `git -C <wt> merge --no-edit main`, expecting `Already up to date.`. In the main checkout, `git merge --no-edit main` runs before each landing. If main moved, stop and report. |
| E10 | **Message check (G7).** `grep -Eic 'claude\|anthropic'` on the message file must print 0 before `git commit` and again on `git log -1 --format=%B` after it. |
| E11 | **Scratch evidence** is quoted, with its command and output, in the section file or commit body, and never cited as the only evidence. |
| E12 | **Downloads** (S05's wheels and arm64 Python 3.11, S41's bokeh 3.10 wheels) go only into scratch virtual environments under `<scratch>/venv-*` (M10), and nothing is installed elsewhere. Stata is linked to a scratch interpreter only for one run and never `permanently`. Afterwards `~/.stata19/console/stata19.rc` must still hold the maintainer's `python_exec`. |

### Index reconciliations of `manifest.json` and `decision-register.md` (binding)

The manifest's text is kept as written, and these rows say how a section file reads it. A section file that follows the binding form satisfies both documents.

| Id | Topic | Manifest text | Register ruling | Binding form |
|---|---|---|---|---|
| IR-1 | Size units (P1.12.1, M1 strict) | S08: "the full keyword ladder (vtiny .. ehuge, vhuge) with the D1 per-class anchors" | Option B: one Stata unit for every class at the 4-inch reference (rs = 2.88pt). Default markers go from 8 to 5.87 px and lines from 1.5 to 1.15 px. | S08 and S13 implement option B, and "the D1 per-class anchors" reads "D1's one unit". The CHANGELOG "Results that change" lines name the new default sizes. |
| IR-2 | `bgcolor()` (P1.20.7, M1 strict) | S38 notes: "The deliberate bgcolor difference (dash.sthlp:2717-2721) stays documented"; residual (item 20): bgcolor() painting kept as "a documented deliberate difference" | twoway's semantics: it paints under the graph region. A region `none` shows `bgcolor()` if given, else `color background`. | S38 adopts twoway's semantics and flips dash.sthlp:2717-2721 and `test/test_option_validation.py:1089-1094` with the reason. A lone `bgcolor(red)` no longer shows (CHANGELOG "Results that change"). The second half of the item-20 residual is struck; S58 files only the first half (P2.53). |
| IR-3 | Stairstep hover (P1.8.6, A24) | S40: "J/stairstep/stepstair draw as Step"; notes: "hover on stairsteps is a residual"; residual (item 8) "hover on stairstep glyphs" | Pre-expanded stair vertices on a Line, rebuilt by `_FILTER_JS` after a move; the c(i) line stays out of HoverTool | S40 draws stairsteps as a Line over pre-expanded vertices in both modes and after saved and served moves, so today's tooltips are kept. The stairstep-hover residual is struck. |
| IR-4 | sm* sizes (P1.4.6, A12) | Residual (item 4): "User msymbol(sm*) and the lower-case shorthands drawn small … S24 applies the sm* factor to scheme symbols only" | Option (b): the factor also applies to `msymbol(sm*)`, after `msize()`, inside `_apply_marker_opts`. This closes P2.11's sm* size sub-claim. | S24 applies the 0.707 factor to the scheme's sm* symbols and to a user's `msymbol(sm*)`. Only the lower-case shorthands stay with P2.11. |
| IR-5 | Anglestyle case (P1.18.3, P1.18.4) | S31: "angle(400) and angle(Vertical) refused, M5" | A wrong-case or unknown anglestyle is noted and drawn at 0, as twoway does (twoway does not refuse it). Bound violations and capitalised NOLABELS/OFF/Alt are refused r(198). | `angle(Vertical)` gets twoway's note and is drawn at 0; `angle(400)` is refused r(198). Under M5, dash refuses only what twoway refuses. |
| IR-6 | British colour names (P1.13.3) | S30: "the dash-only British spellings (grey, dimgrey, bluishgrey, ltbluishgrey) per D3" | They become unknown colours: twoway's note, drawn black. `"255,0,128"` is refused r(198) in twoway's words (HC2-16p flipped). A short or invalid hex draws the default silently. The KPI's CSS leniency is kept. | The register's ruling. |
| IR-7 | The two option generators (P1.34.3, A129; ratification item 26) | S02: `regen_option_surface.py` and `wire_option_reporting.py` take "REPO from __file__; both refuse a missing /tmp inventory"; S03 edits wire_option_reporting.py's emitted version line; S56: "regen_option_surface.py updated" | Retire both ("historical, do not run" and a refusal); no WP-30 item runs them | **If ratified**, S02 retires both: a header line and a refusal before any write. S03 still rewrites the emitted `version 16.0` text, so the repository holds none. S56, and every section that adds an option, edits dash.ado's five option-surface places by hand, kept in agreement by the declared/pending pins (R10). **If struck**, the manifest's S02 form applies, and S56 runs the updated generator. |
| IR-8 | Old extractors (P1.34.4, P1.34.5) | S02 converts "every scripts/extract_*_truth.do that hard-codes them (15 at HEAD)"; its guard covers scripts/, test/ and the Makefile | Old extractors are left to P3.7; the guard covers runners and new extractors | The manifest's form. At `c96facd`, 27 files under `scripts/`, `test/` and the Makefile hold `arch -arm64` or the maintainer path, 15 of them extractors. S02 clears all 27, so the guard needs no exemption list and every later section copies a converted extractor. P3.7 loses its extractor-path part, and S58 records that. |
| IR-9 | by()'s overall regions (P1.20.6, A66) | S38 notes and residual (item 15): `by(, graphregion() plotregion())` is a residual | P1.15c owns them, with P1.20a's reader | The manifest's form. S53 does not draw them, S38 and S53 keep naming them as not drawn, and S58 files a P2 item. |
| IR-10 | Trial render for `dash serve` (P1.26.3, A83) | S23: a build-time trial "so dash build, server and dash serve print the saved build's … notes" | `dash build, server` always runs the trial. For `dash serve` the child's warm-up is the trial, never run twice. | S23 runs the trial for `dash build, server`. For `dash serve` it relays the notes of the child's own first render through `_dash_launch_app`, and S46's warm-up (P1.31.5) later makes that render happen before the server listens. From batch 8 to batch 16, `dash serve`'s notes arrive with the first session. |
| IR-11 | P1.2b's batch and the regeneration commit (P1.2.4, P1.2.7) | S16 in batch 6, S24 in 8, S30 in 10; S07 is the first regenerator | P1.2b is batched with P1.4 and P1.13. P1.2a owns the extractor and regenerates first, in one regeneration commit per batch. | The manifest's batches. The order S16 → S24 → S30 is kept. S07 regenerates first, and each regeneration is part of its section's fix commit (A152), never a commit of its own. |
| IR-12 | When P1.17b lands (P1.3.7) | S21 in batch 7, S27 in batch 9 | P1.17b lands in the same batch as P1.3-A or the next | The manifest's batches. In batch 8 only, default bases stay out of the tick input and hull (S21's D7 a) and may be drawn beyond the axis. That state exists only on `wp30-p1`, since no release is cut before S58. S21's tests pin the hull rule, not that drawing. |
| IR-13 | P1.9's parts and order (P1.9.2-P1.9.4, A26, A27) | S49 (part a: drawing, and the refusals judged on S45's recast type), S55 (part b: after a move); S19 (P1.16) lands before both | P1.9a, P1.16, P1.8b, P1.9b; P1.9a swaps only the first layer's titles | The manifest's order, S19 → S45 → S49 → S55. S49 swaps the default titles through S19's helper (the first-layer swap rule kept), so `_dash_axis_labels` stays at one editor per batch. P1.9.2's refusals land in S49, after S45, as the register requires, and P1.17.3's cancellation of P1.9's step 5 stands. |
| IR-14 | Linestyle names (P1.14.1 B, P1.21.5 A70) | S36 builds "a curated table of Stata-known non-p style names"; the residual (item 14) is "a general resolver for all 161 Stata style files" | Every linestyle name, through all 76 linestyle files, shared by P1.14 and P1.21 | S36's curated table carries every name of the 76 shipped linestyle files, transcribed by its extractor from 19.5. S39's `lstyle()` and S32/S36's style options resolve all 76 through `style_bundle`. The general 161-file resolver stays a residual. |
| IR-15 | Extra BUGS.md entries (P1.5.7, P1.25.6, P1.12.6) | One entry per fix section | P1.5.7 and P1.25.6 each get "its own BUGS.md entry and failing test"; P2.49 gets "its BUGS.md entry and failing test" | A146. P2.49 is withdrawn by ratification row 27: S08 fixes P1.12.6 under P1.12a with failing-first tests. |
| IR-16 | Requirements files (P1.30.5) | S05 writes `test/requirements-dev.txt` and `test/requirements-stata.txt` with the matrix pins; S41 extends them | `requirements-dev.txt` goes to P3.9 | The two files hold only the floor-matrix pins (S05) and the bokeh window (S41). The wider dev-dependency declaration (xdist, node, Chrome, scipy; GAPS2-K5-d) stays with P3.9, as the manifest's item-30 residual says. |
| IR-17 | Register fold-ins and limits that the manifest's scopes do not name | — | — | Each binds the section named. **P1.3.6** (S21): explicit-value axes re-hull their data part after a move, and dash.sthlp:2852 is rewritten. **P1.3.8** (S21; every later finisher extender keeps it): a served re-finish adds at most 0.2 s per figure per move at 500k rows. **P1.5.5** (S18): `xvarformat()`/`yvarformat()` are read, and P3.2 loses them. **P1.10.3** (S56): the `added_text` limit row (default 1,000, ceiling 100,000, `$dash_max_added_text`, r(134)). **P1.15.3** (S53): the stacked-panel CustomJS runs under S04's hashed CSP. **P1.17.4-5** (S14): `rcap barwidth()` is refused r(198), and cap markers are tagged `dash_cap` for S49 to rotate. **P1.21.3** (S39): the `reflines` limit row (default 10,000, ceiling 100,000, `$dash_max_reflines`, r(134)). **P1.25.6** (S34): one served property dict per distinct graph scheme. **P1.27.7** (S12): `saving(my file.html)` and the `twow`/`gra` prefixes are refused in twoway's words (r(199) for the prefixes). **P1.29.8** (S04): `default-src 'none'` on the empty and redirect pages. **P1.32.3** (S25): `dash clear` prunes, with packages missing, through a stdlib-only path. **P1.33.4-5** (S05): the release gate's floor-Python leg (ratification item 25) and a fresh-resolve leg per floor Python. **P1.35.6** (S03): "Measured on MP only". |

### Decisions for maintainer ratification (consolidated 06oct2026; answered 06oct2026)

One numbered list of everything the maintainer must answer before batch 1 is cut (A151): rows 1-28 are the register's architect rulings that users will notice (security trade-offs, numeric limits, accepted approximations; `decision-register.md` "Architect rulings for maintainer ratification"); rows 29-44 are the precondition P-1 and every "Maintainer question" standing in a section file after the review pass (`grep -n "Maintainer question" section-*.md`, plus S36's "Open question for the maintainer"). Each section file was written on the recommendation shown; the answers of 06oct2026 (last column) are applied, and every changed section records them under "(ratification 06oct2026)" in its Review amendments. Step 0f copies this subsection, from its heading to the last row, into `<scratch>/wp30-ratified.txt` once the maintainer has answered, with each row's last column filled with `<ddmonyyyy> ratified` or `<ddmonyyyy> struck: <the maintainer's words>`. Batch 1 is not cut while any row reads `pending` (A151); row 29 must be done before step 0a. A struck row is re-planned in the section file it binds before that section's batch base is recorded; IR-7 already says what a strike of row 26 changes, and rows 30-41 each name what a strike changes in their section's Notes.

| # | Source (register ids / section question) | Question (one line) | Recommendation | Sections affected | Ratified |
|---|---|---|---|---|---|
| 1 | A6 (P1.3.1, P1.20.4) | Accept the plot-region margin as a build-time per-axis fraction, up to about 0.8% of the width (about 11 px at 1400x560) off twoway, documented? | Ratify | S21, S47 | ratified 06oct2026 as recommended |
| 2 | A8 (P1.3.5) | Accept the fitted tsnatscale model on default %td-%th axes (agrees with twoway on 52-66% of ranges, 98% on %ty; the rest stays in P2.19)? | Ratify | S44 | ratified 06oct2026 as recommended |
| 3 | A9 (P1.3.8) | Accept the re-finish budget: served at most 0.2 s per figure per filter move at 500k rows; saved 100 by() panels settle within 1 s of HEAD's time? | Ratify | S21 (S27, S35, S44, S47, S50, S52 keep it) | ratified 06oct2026 as recommended |
| 4 | A10 (P1.4.4) | Note an unread user-scheme key only if it is on a committed list of keys twoway draws and dash does not (at most 10 names plus a count; others silent)? | Ratify | S33 (S34 for ado-path schemes) | answered 06oct2026, CHANGED: "Do nothing. Future versions of dash may expand to include those graphs, so processing those elements from the scheme files is important." No unread-key note at all; the parser keeps reading and retaining every directive (none discarded) for later use |
| 5 | A28 (P1.10.3) | New limit `added_text`: default 1,000, ceiling 100,000, `$dash_max_added_text`, texts x by() panels, r(134)? | Ratify | S56 | ratified 06oct2026 as recommended |
| 6 | A68 (P1.21.3) | New limit `reflines`: default 10,000, ceiling 100,000, `$dash_max_reflines`, positions x panels, r(134)? | Ratify | S39 | ratified 06oct2026 as recommended |
| 7 | A35 (P1.11.5) | Draw `$$…$$` and `\(…\)` in user text as typed (twoway), with no opt-in, so existing TeX titles change? | Ratify | S09 | ratified 06oct2026 as recommended |
| 8 | A34 (P1.11.4) | Drop `{c 0}` and C0/C1 control codes rather than mirror them (a small documented difference kept for safety)? | Ratify | S29 | answered 06oct2026, CHANGED: "Mirror twoway" (a label holding {c 0} is emptied; C0/C1 codes kept, escaped at every HTML/JS sink per rule 1) |
| 9 | A53, A54 (P1.15.5-6) | Keep dash's date text in date by() panel titles (twoway shows 14610), and honour `cols()` up to the by_groups limit (100, ceiling 1,000), then clamp with a note? | Ratify | S28, S48 | ratified 06oct2026 as recommended |
| 10 | A56, A58 (P1.16.1, .3) | Adopt twoway's "first equals last" axis-title rule, so fit keys change (e.g. "lowess mpg weight", "Median bands") with no opt-out? | Ratify | S19 | ratified 06oct2026 as recommended |
| 11 | A76 (P1.23.3) | Draw a mixed date axis through a CustomJSTransform (one more `new Function` consumer under `'unsafe-eval'`)? | Ratify | S35 | ratified 06oct2026 as recommended |
| 12 | A77 (P1.23.4) | Drop, with a note, a literal coordinate outside 0100-9999 on a date axis (twoway draws it)? | Ratify | S35 | answered 06oct2026, CHANGED: "Draw it anyway" (no drop; the literal is drawn, dates outside 0100-9999 included) |
| 13 | A82, A84 (P1.26.2, .4) | Notes take twoway's form `(note: …)` in text colour, show under `quietly`, hidden by `capture`, no longer red Python warnings? | Ratify | S06 (S23 and every later note) | ratified 06oct2026 as recommended |
| 14 | A83 (P1.26.3) | `dash build, server` always runs the trial render (up to the saved build's own time); for `dash serve` the child's warm-up is the trial, never run twice? | Ratify | S23, S46 (IR-10) | ratified 06oct2026 as recommended |
| 15 | A88, A89 (P1.27.1, .4) | No browser opens in batch mode or under `set graphics off`, while interactive console Stata still opens one (a deliberate asymmetry)? | Ratify | S12 | ratified 06oct2026 as recommended |
| 16 | A93, A96 (P1.28.3, .6) | Stale-graph note once per dash command, only when a Stata graph is in memory; `r(filename)` absolute, transient for previews? | Ratify, read as row 35 says | S22 | ratified 06oct2026 as recommended |
| 17 | A99, A101, A102 (P1.29.3, .5, .6) | `python app.py` header keeps `'unsafe-inline'` (meta nonce governs); script-src drops `'unsafe-inline'` with no CSP1 fallback; served script-src nonce-only if the browser test is clean, else keeps `'self'`? | Ratify | S04 | ratified 06oct2026 as recommended |
| 18 | A104 (P1.30.3) | "Verified" means major.minor, so patch releases inherit the minor's text-sink XSS verification? | Ratify | S41 | ratified 06oct2026 as recommended |
| 19 | A107, A109 (P1.30.6, .9) | Never downgrade a venv dash did not create; internals guards fail closed, so the server refuses to start if a Bokeh release changes the hooks (S41 also hardens `bokeh serve`'s origin check, Q-41.1)? | Ratify | S41 | ratified 06oct2026 as recommended |
| 20 | A110, A111 (P1.31.1-2) | At most 20 concurrent sessions by default (`maxsessions()`); idle sessions close after 60 minutes with no filter, brush or CSV activity? | Ratify | S46 | ratified 06oct2026 as recommended |
| 21 | A113 (P1.31.4) | One recompute worker (worst documented wait about 3 min at 20 x 8.7 s for lowess at 100k)? | Ratify | S57 | ratified 06oct2026 as recommended |
| 22 | A116, A117 (P1.31.7-8) | Per-session RSS growth at or below 40 MB at 200k x 3 (60.7 MB today); a 64 MB per-process LRU estimator memo, out of Stata's process? | Ratify | S46 | answered 06oct2026, CHANGED: "allow 80MB RAM for 200k rows" (per-session growth bound 80 MB at 200k rows x 3; the 64 MB memo unchanged) |
| 23 | A119 (P1.31.10) | The busy page is a static HTTP 503 with Retry-After and no auto-refresh? | Ratify | S46 | ratified 06oct2026 as recommended |
| 24 | A121 (P1.32.1) | numpy or pandas below dash_setup's minimums gets a note, not a refusal? | Ratify | S25 | ratified 06oct2026 as recommended |
| 25 | A125 (P1.33.4) | The release gate gains a floor-Python leg (a time cost on every release)? | Ratify | S05 (S58's `make gate`) | answered 06oct2026, CHANGED: "Manual only" (the floor Python is measured once in WP-30 by S05; no release-gate leg) |
| 26 | A129 (P1.34.3) | Retire `regen_option_surface.py` and `wire_option_reporting.py` (they refuse to run)? | Ratify (IR-7 plans a strike) | S02 (S03, S56; IR-7) | ratified 06oct2026 as recommended |
| 27 | A37 (P1.12.6) | Leave the brushed-glyph styling bug (nonselection and muted glyphs keep creation values) to P2.49, although it is wrong output today? | Ratify | S08 (A146) | answered 06oct2026, CHANGED: "Fix in WP-30" (the brushed-glyph nonselection/muted styling bug joins S08; P2.49 is not filed for it) |
| 28 | A80 (P1.25.6) | Served dashboards with per-graph schemes change: each graph gets its own scheme, as on the saved page? | Ratify | S34 | ratified 06oct2026 as recommended |
| 29 | P-1 (section-01 Notes; precondition of step 0a) | `PhilSchummSuggestion.md` is tracked in the package root (76e32d7), so `test/test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own` is red at `c96facd` (re-run 06oct2026: `python3 -m pytest test/test_packaging.py -q -n0 -k root` gives 1 failed, 1 passed, 11 deselected, stray file `PhilSchummSuggestion.md`) and G0 cannot pass. Move it, or widen `_ROOT_ALSO`? | The maintainer runs `git mv PhilSchummSuggestion.md .ultraplan/handoff/` in a commit of their own on `wp30-p1` before step 0a; do not widen `_ROOT_ALSO` | Step 0a (G0), S01, every full run | answered 06oct2026: "Ignore the file in the packaging root test" (`PhilSchummSuggestion.md` added to `test/test_packaging.py::_ROOT_ALSO`; the root test passes; uncommitted, lands before step 0a) |
| 30 | S08 Q1 (register P1.12.4) | Should `#pt`/`#in`/`#cm` also follow a graph's `xsize()`/`ysize()` (option (a): an R12/A139 exception in batch 3 that must also reach the GlyphMapper sites), or only the scheme's `graphsize` (option (b))? | (b): narrow P1.12.4 to the scheme's `graphsize`; S58 files a P2 row for `xsize()`/`ysize()` | S08 (S58) | ratified 06oct2026 as recommended |
| 31 | S10/S11/S12 (section-12 Notes; A139 exception, batch 4) | May batch 4 edit `_dash_plot` in two sections (S10 one hunk at :5323-5325; S12 at :5540 and :5560-5568) and `_dash_require_mata`'s `_needed` list in three (S10, S11, S12)? | Grant: distinct hunks over 200 lines apart, merge order S10, S11, S12 with `git apply -3`, every `_needed` name kept; if refused, S10 re-plans TR-10.6 into Mata before batch 4's base | S10, S11, S12 | ratified 06oct2026 as recommended |
| 32 | S11 Q-11.1 (M5 exception) | Read a used blank quoted stylelist element (`mcolor(" " blue)`) as `.` and document that twoway refuses it, instead of refusing r(198) with twoway's per-option internal class-path words? | Ratify the lenient default as a documented M5 exception | S11 | answered 06oct2026, CHANGED: "Refuse r(198)" (a blank quoted stylelist element is refused r(198) with dash's own clear message) |
| 33 | S12 (register P1.27.6, A91) | May the `$dash__display` seam also fence `test_serve_browser.cscript` SB-07..SB-11, beyond "the HC2 controls"? | Ratify the wider reading (same stub-control kind, same hygiene fence) | S12 | ratified 06oct2026 as recommended |
| 34 | S13 D-13b (M5 exception) | Positive `*#` or absolute line widths that pass 10,000 Stata units only at draw time: note and draw the site's default, instead of a twoway-equal r(198) that needs a new renderer return-code channel? | Ratify D-13b | S13 | ratified 06oct2026 as recommended |
| 35 | S22 Q-22.1 (with row 16; register P1.28.3) | Read "one line per dash command" as "per file-writing command" (the one-line form, `dash build`, `dash build, server`), so registrations, `dash kpi`, `dash clear` and `dash serve` print no stale-graph note? | Ratify | S22 | ratified 06oct2026 as recommended |
| 36 | S28 Q-28.1 (D-28e) | twoway draws each by() panel label in a filled box; file it as a P2 item, or assign it to S53? | File as a P2 item (S58); S53 ruled it out of its scope | S28, S53, S58 | answered 06oct2026, CHANGED: "Add to S53" (S53 draws twoway's filled box behind each by() panel label) |
| 37 | S33 Q1 (A139 exception, batch 11) | May S33 add the one keyword `color_idx=color_idx` to the `_apply_mlabel_opts` call line in seven mappers S32 also edits (`map_bar`, `map_dropline`, `map_rcapsym`, `map_scatteri`, `map_pcarrow`, `map_pcbarrow`, `map_pccapsym`; `map_scatter` if S32 moves a read)? | Grant (option (a)); S33 lands after S32 and the merger re-adds the keyword on any conflict | S32, S33 | ratified 06oct2026 as recommended |
| 38 | S34 Q1 (R12 exception, batch 12) | May S34 make four one-line `_generate_app_source` edits (:35093, :35562, :35584, :35646) while S35 is batch 12's template editor? | Grant at 12.0 (disjoint from S35's hunks; S34 lands first); if refused, P1.25.6's served half moves to S38 (batch 13) | S34, S35 (S38) | ratified 06oct2026 as recommended |
| 39 | S36 D-36c (open question 1) | Draw the 57 Stata-known style names outside the curated table in their class's default attributes and name them as not drawn, keeping the general 161-file resolver a residual? | Ratify (a new P2 row by S58) | S36 (S58) | ratified 06oct2026 as recommended |
| 40 | S45 Q-45.1 (register A60, P1.16.5) | Write the drawn type into `type` for base/range/pc/ts recasts and keep the typed one as `recast_from` (read first by the label helpers), instead of A60's "keep `type`, write `recast`"? | Ratify (judged sound by the review); if struck, S45 moves to a batch holding both routing editors | S45 (S19, S40, S49) | ratified 06oct2026 as recommended |
| 41 | S48 Q-48.2 (D-48d) | Refuse `iscale()` above 10,000 r(198) in twoway's `gm_linewidth` words, an over-refusal between 10,000 and twoway's scheme-dependent draw-time bound? | Ratify the 10,000 bound | S48 | ratified 06oct2026 as recommended |
| 42 | S58 Q1 (58-07) | Where does the deferred platform package (P1.34's Linux/Windows/Intel measurement, M4) live in ROADMAP: a `###` subsection inside WP-30's entry, or its own future package heading? | A `###` subsection inside WP-30's entry | S58 | ratified 06oct2026 as recommended |
| 43 | S58 Q2 (R58-11) | The release re-date moves CHANGELOG lines 3 and 5 in S58.7 (as WP-29 did), where index.md lists "the release heading" under S58.6: confirm S58.7 | Confirm S58.7 | S58 | ratified 06oct2026 as recommended |
| 44 | S58 Q3 (R58-14) | Leave dash.sthlp's "named in a warning" unreworded (three tests pin it) and file a P3.3 note, instead of the rewording S06's note allowed? | Leave it; file the P3.3 note | S58, S06 | ratified 06oct2026 as recommended |

## Section manifest

| # | Section | Item / part (entry) | Batch | Depends on | Blocks | Risk | Effort | Case-id prefix |
|---|---|---|---|---|---|---|---|---|
| 01 | Tracking foundation | — | 0 | none (after step 0) | every section | green | S | TF |
| 02 | Portable runners (P1.34 under M4) | P1.34 | 1 | 01 | 04, 05, 10, 11, 19, 40, 42, 56 | yellow | M | RR |
| 03 | Stata 19 floor declared and enforced (P1.35 under M2) | P1.35 | 1 | 01 | 05, 12, 25 | yellow | M | SF; ENV-24..29 |
| 04 | CSP without 'unsafe-inline'; safe Windows opener (P1.29, M11) | P1.29 | 2 | 02 | 12, 41, 46, 54 | yellow | M | CSP; SB-21..30, PV-28..34 |
| 05 | Measured Python floor (P1.33, M3/M10) | P1.33 | 2 | 02, 03 | 25, 41 | yellow | M | PYF; HON-31..39 |
| 06 | One note channel (P1.26 part a) | P1.26a | 2 | 01 | 22, 23, 26, 29, 33, 34, 41 | yellow | M | NC-01..06 |
| 07 | Ship the six StataCorp schemes (P1.25 part a) | P1.25a | 3 | 01 | 15, 24, 34 | green | M | SX |
| 08 | Stata size units for markers, text and gaps (P1.12 part a, M1) | P1.12a | 3 | 01 | 13, 14, 15, 18, 21, 30, 31, 32, 33, 37, 47, 48, 56 | yellow | M | SU |
| 09 | TeX delimiters inert on every canvas sink (P1.11 part a) | P1.11a | 3 | 01 | 29 | yellow | S | TX |
| 10 | Sub-option abbreviations (P1.19) | P1.19 | 4 | 02 | 18, 31, 38, 39, 51, 53, 56 | yellow | M | SA |
| 11 | Stylelists of style options across an expanded varlist (P1.1 part a) | P1.1a | 4 | 02 | 20, 32, 37, 40 | yellow | M | SL |
| 12 | Drop-in command form and saving() grammar (P1.27, M5/M11) | P1.27 | 4 | 03, 04 | 22 | yellow | M | CF; SB-31..40, PV-35..44 |
| 13 | Stata line-width ladder (P1.12 part b, M1) | P1.12b | 5 | 08 | 31, 32, 38, 39 | yellow | M | LN |
| 14 | Bar widths and range caps (P1.17 part a) | P1.17a | 5 | 08 | 27, 49 | yellow | M | BG |
| 15 | Scheme chrome: titles, ticks, grid, economist axes (P1.2 part a, M1) | P1.2a | 5 | 07, 08 | 16, 21, 28, 29, 31, 53, 56 | yellow | M | LK |
| 16 | Intensity as an opaque blend (P1.2 part b, M1) | P1.2b | 6 | 15 | 24, 30, 43 | yellow | M | OB |
| 17 | Date and format text in keys and tooltips (P1.23 part b) | P1.23b | 6 | 01 | — | yellow | M | DK |
| 18 | Axis format fallbacks (P1.5) | P1.5 | 6 | 08, 10 | 21, 49, 51 | yellow | M | AF |
| 19 | Legend keys and default axis titles (P1.16) | P1.16 | 7 | 02 | 28, 42, 45, 49, 53 | yellow | M | KT |
| 20 | Per-series value lists (P1.1 part b) | P1.1b | 7 | 11 | — | yellow | S | PS |
| 21 | natscale ticker and twoway margin on non-date axes (P1.3 part a, M1) | P1.3a | 7 | 08, 15, 18 | 27, 35, 44, 47, 49, 50, 52, 53 | red | L | NS |
| 22 | r(filename) and the stale-graph note (P1.28 part a, M8) | P1.28a | 8 | 06, 12 | 54 | yellow | S | GE |
| 23 | Served notes reach Stata (P1.26 part b, M6) | P1.26b | 8 | 06 | 26, 46 | yellow | M | NC-07..19 |
| 24 | Scheme opacity, histogram style and symbols reach every layer (P1.4 part a) | P1.4a | 8 | 07, 16 | 30, 32, 33, 45, 49 | yellow | M | SK |
| 25 | Render-time dependency guards (P1.32) | P1.32 | 9 | 03, 05 | 41, 46 | yellow | M | RG; ENV-30..39, HON-40..49 |
| 26 | function: closed by disposition (P1.22 under M12) | P1.22 | 9 | 06, 23 | — | green | S | FN |
| 27 | twoway's default base and axis extent (P1.17 part b) | P1.17b | 9 | 14, 21 | 35, 57 | yellow | M | DB |
| 28 | by() panel labels and overall text (P1.15 part a) | P1.15a | 10 | 15, 19 | 48 | yellow | M | BP |
| 29 | SMCL in graph text (P1.11 part b) | P1.11b | 10 | 06, 09, 15 | 56 | yellow | M | GT |
| 30 | Stata colour grammar (P1.13 part a) | P1.13a | 10 | 08, 16, 24 | 31, 33, 34, 38, 39, 43, 56 | yellow | M | CG |
| 31 | Axis look sub-options (P1.18 part a, M5/M6) | P1.18a | 11 | 08, 10, 13, 15, 30 | 43, 52, 53 | yellow | L | AXL |
| 32 | Named styles p1-p15 (P1.14 part a) | P1.14a | 11 | 08, 11, 13, 24 | 36, 38, 39, 43 | yellow | L | NP |
| 33 | Marker-label and colour-key chrome; unread directives retained (P1.4 part b) | P1.4b | 11 | 06, 08, 24, 30 | 34, 37 | yellow | M | MK |
| 34 | Stata's scheme lookup along the ado-path (P1.25 part b, M7) | P1.25b | 12 | 06, 07, 30, 33 | — | yellow | M | SP |
| 35 | Date positions on every axis (P1.23 part a) | P1.23a | 12 | 21, 27 | 44, 49, 51, 56, 57 | yellow | L | DA |
| 36 | Other style names (P1.14 part b) | P1.14b | 12 | 32 | — | yellow | M | OS |
| 37 | mlabvposition() and mlabtextstyle() (P1.24) | P1.24 | 13 | 08, 11, 33 | — | yellow | M | MV |
| 38 | plotregion()/graphregion() styling (P1.20 part a) | P1.20a | 13 | 10, 13, 30, 32 | 43, 47 | yellow | M | RS |
| 39 | xline/yline positions, refusals and lstyle (P1.21 part a) | P1.21a | 14 | 10, 13, 30, 32 | 43, 50 | yellow | M | XP |
| 40 | connect() and cmissing() (P1.8 part a) | P1.8a | 14 | 02, 11 | 45 | yellow | M | CM |
| 41 | Verified bokeh window; internals fail closed (P1.30, M9/M10) | P1.30 | 14 | 04, 05, 06, 25 | 46, 54 | yellow | M | BK; HON-50..59 |
| 42 | Time-series operators in plot varlists (P1.7) | P1.7 | 15 | 02, 19 | — | yellow | L | TSO |
| 43 | Default colour and opacity at every colour site (P1.13 part b) | P1.13b | 15 | 16, 30, 31, 32, 38, 39 | 56 | yellow | M | BI |
| 44 | tsnatscale on %td-%ty default axes (P1.3 part b, M1) | P1.3b | 15 | 21, 35 | 52, 57 | red | L | TN |
| 45 | recast() (P1.8 part b) | P1.8b | 16 | 19, 24, 40 | 49, 57 | yellow | L | RC |
| 46 | Served session capacity and memory (P1.31 part a) | P1.31a | 16 | 04, 23, 25, 41 | 57 | yellow | M | MS |
| 47 | Plot-region margin and inner box (P1.20 part b) | P1.20b | 16 | 08, 21, 38 | 50, 57 | yellow | M | RM |
| 48 | by() grid and size (P1.15 part b) | P1.15b | 17 | 08, 28 | 53, 56 | yellow | M | BYG |
| 49 | horizontal drawn (P1.9 part a, M5) | P1.9a | 17 | 14, 18, 19, 21, 24, 35, 45 | 55 | yellow | M | HZ |
| 50 | xline/yline extend, noextend and style() (P1.21 part b) | P1.21b | 17 | 21, 39, 47 | 57 | yellow | M | XE |
| 51 | tsline time-axis options (P1.6) | P1.6 | 18 | 10, 18, 35 | 56 | yellow | L | TA |
| 52 | The add sub-option (P1.18 part b) | P1.18b | 18 | 21, 31, 44 | 57 | yellow | M | AD |
| 53 | Shared axes and keys under by() (P1.15 part c) | P1.15c | 18 | 10, 15, 19, 21, 31, 48 | — | yellow | L | BYA |
| 54 | Client-side Save as SVG (P1.28 part b, M8) | P1.28b | 19 | 04, 22, 41 | — | yellow | M | SVA |
| 55 | horizontal after a filter move (P1.9 part b) | P1.9b | 19 | 49 | 57 | yellow | M | HM |
| 56 | text() and ttext() annotations (P1.10) | P1.10 | 19 | 02, 08, 10, 15, 29, 30, 35, 43, 48, 51 | — | yellow | L | AT |
| 57 | Served recompute off the event loop (P1.31 part b) | P1.31b | 20 | 27, 35, 44, 45, 46, 47, 50, 52, 55 | — | red | L | WK |
| 58 | Closeout | — | 21 | all (01-57) | none | green | M | CO |

How to read the table:

- **Item / part (entry)** is the BUGS.md entry id, which is also the commit-subject id and the CHANGELOG marker id (A140).
- **Blocks** lists the sections whose `depends_on` names this one. S58 depends on every section and is not listed.
- **Case-id prefix.** Each section's own prefix is new. Every one was checked unused at `c96facd` with `grep -E '(^|[^A-Za-z0-9_])<P>-[0-9]' test/*.cscript test/*.py test/*.do`, which found 0 hits each. One candidate, `SO`, had 312 hits and was replaced by `OS`.
- **Ranges.** A range given after a prefix continues an existing prefix (register X.3/A135). At `c96facd` the highest existing ids were SB-20, PV-27, ENV-23 and HON-30, and NC was unused.
- **Scope, notes and every edge's reason** are in `manifest.json` (`scope`, `notes`, `depends_on`), as amended by IR-1..IR-17.

Why the dependencies (the chains every batch follows; every edge sits between batches):

- **Foundation.** Every fix section depends on S01's entry, key, markers and stub block.
- **Runners and floor.** S02 lands before any section copies an extractor (S04, S05, S10, S11, S19, S40, S42, S56). S03's floor constant and guard come before S05's Python floor, S12's prefix strip and S25's dependency guard (A154).
- **Security first.** S04's CSP and opener come before S12, which widens `saving()` under M11, and before S41, S46 and S54, whose pages and actions run under its hashes and nonce.
- **One note channel.** S06 comes before S22, S23, S26, S29, S33, S34 and S41, and before every other note (A150).
- **Units.** S08 is the size resolver behind S13, S14, S15, S18, S21, S30, S31, S32, S33, S37, S47, S48 and S56. S13's line ladder feeds S31, S32, S38 and S39.
- **Schemes and colour.** S07 (26 files) → S15 (chrome, naturally_white, the p#bar/p#area chains) → S16 (one opaque blend) → S24 (scheme keys on every layer) → S30 (colour grammar) → S33/S34 (key chrome, scheme lookup), S31, S38, S39 → S43 (bare `*#`/`%#` at every site, last).
- **Axes.**
  - S10's sub-option tables feed S18, S31, S38, S39, S51, S53 and S56.
  - S18's formats lead to S21, the red one: the ticker, the margin and the finishers. S21 leads to S27 (default base), then S35 (dates on every axis), then S44 (the date ticker, red), then S52 (`add`).
  - S47 (margins) and S50 (reference-line extent) extend S21's finishers.
  - S35 leads to S49, S51 and S56.
- **Text.** S09's document pass leads to S29 (SMCL), then S56. S19's key and title helpers lead to S28, S42, S45, S49 and S53.
- **Types.** S11's splitter leads to S20, S32, S37 and S40. S40 (`connect()`) leads to S45 (`recast()`), then S49 (horizontal drawn), then S55 (horizontal after a move).
- **Served.** S23's relay leads to S26 and S46. S25's guard leads to S41's window, which leads to S46 (capacity) and S54 (Save as SVG). S46 leads to S57 (the worker, red), which comes last of all fix sections.

## P1 coverage

| Entry | Section | Batch | Commits | Commit subject ends | CHANGELOG list(s) (`WP30_LISTS`) |
|---|---|---|---|---|---|
| P1.1a | 11 Stylelists of style options across an expanded varlist (P1.1 part a) | 4 | 1 | `(WP-30 P1.1a)` | Results that change; Changed behaviour |
| P1.1b | 20 Per-series value lists (P1.1 part b) | 7 | 1 | `(WP-30 P1.1b)` | Changed behaviour; Fixed in WP-30 |
| P1.2a | 15 Scheme chrome: titles, ticks, grid, economist axes (P1.2 part a, M1) | 5 | 1 | `(WP-30 P1.2a)` | Results that change |
| P1.2b | 16 Intensity as an opaque blend (P1.2 part b, M1) | 6 | 1 | `(WP-30 P1.2b)` | Results that change |
| P1.3a | 21 natscale ticker and twoway margin on non-date axes (P1.3 part a, M1) | 7 | 1 | `(WP-30 P1.3a)` | Results that change |
| P1.3b | 44 tsnatscale on %td-%ty default axes (P1.3 part b, M1) | 15 | 1 | `(WP-30 P1.3b)` | Results that change |
| P1.4a | 24 Scheme opacity, histogram style and symbols reach every layer (P1.4 part a) | 8 | 1 | `(WP-30 P1.4a)` | Results that change |
| P1.4b | 33 Marker-label and colour-key chrome; unread directives retained (P1.4 part b) | 11 | 1 | `(WP-30 P1.4b)` | Results that change |
| P1.5 | 18 Axis format fallbacks (P1.5) | 6 | 1 | `(WP-30 P1.5)` | Results that change; Changed behaviour |
| P1.6 | 51 tsline time-axis options (P1.6) | 18 | 2 | `(WP-30 P1.6)` | New; Changed behaviour |
| P1.7 | 42 Time-series operators in plot varlists (P1.7) | 15 | 2 | `(WP-30 P1.7)` | New; Changed behaviour |
| P1.8a | 40 connect() and cmissing() (P1.8 part a) | 14 | 1 | `(WP-30 P1.8a)` | Results that change; Changed behaviour |
| P1.8b | 45 recast() (P1.8 part b) | 16 | 1 | `(WP-30 P1.8b)` | Results that change; Changed behaviour |
| P1.9a | 49 horizontal drawn (P1.9 part a, M5) | 17 | 1 | `(WP-30 P1.9a)` | Results that change; Changed behaviour |
| P1.9b | 55 horizontal after a filter move (P1.9 part b) | 19 | 1 | `(WP-30 P1.9b)` | Fixed in WP-30 |
| P1.10 | 56 text() and ttext() annotations (P1.10) | 19 | 2 | `(WP-30 P1.10)` | New; Changed behaviour |
| P1.11a | 09 TeX delimiters inert on every canvas sink (P1.11 part a) | 3 | 1 | `(WP-30 P1.11a)` | Security; Results that change |
| P1.11b | 29 SMCL in graph text (P1.11 part b) | 10 | 1 | `(WP-30 P1.11b)` | Results that change |
| P1.12a | 08 Stata size units for markers, text and gaps (P1.12 part a, M1) | 3 | 1 | `(WP-30 P1.12a)` | Results that change; Changed behaviour |
| P1.12b | 13 Stata line-width ladder (P1.12 part b, M1) | 5 | 1 | `(WP-30 P1.12b)` | Results that change; Changed behaviour |
| P1.13a | 30 Stata colour grammar (P1.13 part a) | 10 | 1 | `(WP-30 P1.13a)` | Results that change; Changed behaviour |
| P1.13b | 43 Default colour and opacity at every colour site (P1.13 part b) | 15 | 1 | `(WP-30 P1.13b)` | Results that change |
| P1.14a | 32 Named styles p1-p15 (P1.14 part a) | 11 | 1 | `(WP-30 P1.14a)` | Results that change |
| P1.14b | 36 Other style names (P1.14 part b) | 12 | 1 | `(WP-30 P1.14b)` | Results that change |
| P1.15a | 28 by() panel labels and overall text (P1.15 part a) | 10 | 1 | `(WP-30 P1.15a)` | Results that change |
| P1.15b | 48 by() grid and size (P1.15 part b) | 17 | 1 | `(WP-30 P1.15b)` | Results that change; Changed behaviour |
| P1.15c | 53 Shared axes and keys under by() (P1.15 part c) | 18 | 1 | `(WP-30 P1.15c)` | Results that change |
| P1.16 | 19 Legend keys and default axis titles (P1.16) | 7 | 2 | `(WP-30 P1.16)` | Results that change |
| P1.17a | 14 Bar widths and range caps (P1.17 part a) | 5 | 1 | `(WP-30 P1.17a)` | Results that change; Changed behaviour |
| P1.17b | 27 twoway's default base and axis extent (P1.17 part b) | 9 | 1 | `(WP-30 P1.17b)` | Results that change |
| P1.18a | 31 Axis look sub-options (P1.18 part a, M5/M6) | 11 | 1 | `(WP-30 P1.18a)` | Results that change; Changed behaviour |
| P1.18b | 52 The add sub-option (P1.18 part b) | 18 | 1 | `(WP-30 P1.18b)` | Results that change |
| P1.19 | 10 Sub-option abbreviations (P1.19) | 4 | 1 | `(WP-30 P1.19)` | Changed behaviour; Fixed in WP-30 |
| P1.20a | 38 plotregion()/graphregion() styling (P1.20 part a) | 13 | 1 | `(WP-30 P1.20a)` | Results that change; Changed behaviour |
| P1.20b | 47 Plot-region margin and inner box (P1.20 part b) | 16 | 1 | `(WP-30 P1.20b)` | Results that change |
| P1.21a | 39 xline/yline positions, refusals and lstyle (P1.21 part a) | 14 | 1 | `(WP-30 P1.21a)` | Results that change; Changed behaviour |
| P1.21b | 50 xline/yline extend, noextend and style() (P1.21 part b) | 17 | 1 | `(WP-30 P1.21b)` | Results that change |
| P1.22 | 26 function: closed by disposition (P1.22 under M12) | 9 | 1 | `(WP-30 P1.22)` | Fixed in WP-30 |
| P1.23a | 35 Date positions on every axis (P1.23 part a) | 12 | 1 | `(WP-30 P1.23a)` | Results that change |
| P1.23b | 17 Date and format text in keys and tooltips (P1.23 part b) | 6 | 1 | `(WP-30 P1.23b)` | Results that change |
| P1.24 | 37 mlabvposition() and mlabtextstyle() (P1.24) | 13 | 2 | `(WP-30 P1.24)` | Fixed in WP-30; Changed behaviour |
| P1.25a | 07 Ship the six StataCorp schemes (P1.25 part a) | 3 | 1 | `(WP-30 P1.25a)` | New |
| P1.25b | 34 Stata's scheme lookup along the ado-path (P1.25 part b, M7) | 12 | 1 | `(WP-30 P1.25b)` | Results that change; Security |
| P1.26a | 06 One note channel (P1.26 part a) | 2 | 1 | `(WP-30 P1.26a)` | Changed behaviour; Fixed in WP-30 |
| P1.26b | 23 Served notes reach Stata (P1.26 part b, M6) | 8 | 1 | `(WP-30 P1.26b)` | Changed behaviour; Fixed in WP-30 |
| P1.27 | 12 Drop-in command form and saving() grammar (P1.27, M5/M11) | 4 | 1 | `(WP-30 P1.27)` | Changed behaviour; Fixed in WP-30 |
| P1.28a | 22 r(filename) and the stale-graph note (P1.28 part a, M8) | 8 | 1 | `(WP-30 P1.28a)` | New; Changed behaviour |
| P1.28b | 54 Client-side Save as SVG (P1.28 part b, M8) | 19 | 1 | `(WP-30 P1.28b)` | New |
| P1.29 | 04 CSP without 'unsafe-inline'; safe Windows opener (P1.29, M11) | 2 | 1 | `(WP-30 P1.29)` | Security |
| P1.30 | 41 Verified bokeh window; internals fail closed (P1.30, M9/M10) | 14 | 2 | `(WP-30 P1.30)` | Requirements; Security |
| P1.31a | 46 Served session capacity and memory (P1.31 part a) | 16 | 1 | `(WP-30 P1.31a)` | New; Security |
| P1.31b | 57 Served recompute off the event loop (P1.31 part b) | 20 | 1 | `(WP-30 P1.31b)` | Fixed in WP-30 |
| P1.32 | 25 Render-time dependency guards (P1.32) | 9 | 1 | `(WP-30 P1.32)` | Requirements |
| P1.33 | 05 Measured Python floor (P1.33, M3/M10) | 2 | 2 | `(WP-30 P1.33)` | Requirements |
| P1.34 | 02 Portable runners (P1.34 under M4) | 1 | 1 | `(WP-30 P1.34)` | Fixed in WP-30 |
| P1.35 | 03 Stata 19 floor declared and enforced (P1.35 under M2) | 1 | 1 | `(WP-30 P1.35)` | Requirements; Changed behaviour |

**What S01 writes for each entry:**

- the title in full, with no `"` in it;
- the Description: the DROPIN text and its source ids. The REM-08-04 ids are matched to REMAINING.md:1935-2110 by content (S35), the REM-08-05 ids to :2111-2290 (S17), DROPIN's GAPS2-B16-a..e letters to B16's parts (S28/S48/S53), and GAPS2-D3-a..e to D3's TeX half (S09) and SMCL half (S29). An id whose bullet belongs to the other part moves with it;
- the Suggested fix, one sentence that names its section;
- `- Resolution: Not fixed because WP-30 section <NN> has not landed. Graded S<n> (WP-30): <why>.`, where the grade is S01's, given with a reason.

A two-commit section cites its one entry in both commits (A156).

**Entry counts:**

- At `c96facd`, BUGS.md has 4 open entries, all `S3 (WP-27)`: the titles at BUGS.md:2523 (the tsnatscale model, which S44 closes), :2559, :2595 and :2601.
- After S01: 60 open. S08 adds no open entry (P2.49 is not filed; ratification row 27).
- S18 and S34 each add one entry already closed (A146).
- After the closeout: 3 open, namely :2559, :2595 and :2601.

## Batch execution order and dependency graph

```
Step 0 (main checkout, wp30-p1): 0a commit .ultraplan/wp30/ (G0)  0b cert baseline (queue, cert mode)  0c GitNexus index at HEAD
                                 0d batch-0 base  0e hand-off  0f ratified record (44 rows)  0g queue script
Batch  0 │ S01                        tracking foundation                 (S01 may run before 0f is answered; A151)
Batch  1 │ S02 S03                    platform floor                      + make cert after both land (the version sweep)
Batch  2 │ S04 S05 S06                hardening I                         + S05's floor matrix: 6 pytest runs, 1 cert run
Batch  3 │ S07 S08 S09                schemes, size units, TeX inert      (S07 regenerates; merges first: R7)
Batch  4 │ S10 S11 S12                input grammar
Batch  5 │ S13 S14 S15                default look I                      (S15 regenerates, last)
Batch  6 │ S16 S17 S18                default look II, formats            (S18: template and figure-body editor)
Batch  7 │ S19 S20 S21●               default axes, keys, value lists     (S21 red: finishers, template, figure body; last)
Batch  8 │ S22 S23 S24                scheme reach, notes reach Stata     (S23: template, figure body; S24 regenerates, last)
Batch  9 │ S25 S26 S27                default base, failing clearly       (S25: template; S27: finisher, last)
Batch 10 │ S28 S29 S30                by() text, SMCL, colour grammar     (S28: template; S30 regenerates, last)
Batch 11 │ S31 S32 S33                axis look, named styles, label chrome (S33 regenerates, last)
Batch 12 │ S34 S35 S36                scheme lookup, dates, style names   (S35: template, figure body, finisher; S36 regenerates)
Batch 13 │ S37 S38                    marker labels, region styling       (S37 regenerates in commit 2, first; S38: template, figure body)
Batch 14 │ S39 S40 S41                lines, bokeh window                 (S40: figure body; S41: template) + S41's 3.10 leg
Batch 15 │ S42 S43 S44●               operators, colour sites, date ticks (S42: template; S44 red: finisher, last)
Batch 16 │ S45 S46 S47                recast, sessions, margins           (S47: figure body, finisher, regenerates, last)
Batch 17 │ S48 S49 S50                horizontal, by() grid, line extent  (S49: figure body; S50: finisher, regenerates)
Batch 18 │ S51 S52 S53                axis options                        (S52: finisher; S53 regenerates, last)
Batch 19 │ S54 S55 S56                SVG, horizontal after move, text()  (S56: template, figure body, regenerates)
Batch 20 │ S57●                       served worker                       alone
Batch 21 │ S58                        closeout, main checkout             alone
```

● marks a red section. Merge order within each batch is left to right, as in `manifest.json` `merge_order`.

### The step list of a batch (batches 1-20; batch 0 and the closeout are in "How to execute")

For batch k, whose base is `<scratch>/batch-<k>-base.txt`:

- **k.0 Impact at the batch base**, in the main checkout before any worktree is cut (E4).
  - Run `gitnexus impact <symbol> -d upstream -r dash` for every symbol each section file names in its blast-radius list, and write the results to `<scratch>/batch-<k>-impact.txt`.
  - Report every HIGH or CRITICAL result to the maintainer in one message, naming the expected ones listed under the batch below, and record the approval in that file.
  - Confirm `UNKNOWN` (the Stata and Mata programs, and dispatch through `map_*`) by `grep -n` and record it as unresolved.
  - A section that later must edit a symbol not in that file runs `impact` itself and reports any HIGH or CRITICAL result before editing.
- **k.1 Cut the worktrees.** For each section, `git worktree add /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s<NN> -b wp30-s<NN> wp30-p1`. Each section's first task checks that `git -C <wt> rev-parse HEAD` equals `batch-<k>-base` and that `git -C <wt> branch --show-current` prints `wp30-s<NN>`.
- **k.2 Run the sections** in parallel, each through the per-entry cycle ("How to execute", step 2).
- **k.3 Land** each commit in merge order with the landing routine. The GitNexus index is rebuilt after each landing (E4).
- **k.4 G8, the batch gate**, in the main checkout:
  - the full suite once, through the queue;
  - the registry tests (R2);
  - `test/test_wp30_truth.cscript` with every block (`WP30_ONLY` unset), and every area cscript the batch touched (`git diff --name-only $(cat <scratch>/batch-<k>-base.txt) HEAD -- 'test/*.cscript'`), each through the driver;
  - `gitnexus status`, which must show the indexed commit equal to HEAD.

  A red result belongs to the section that owns the test (step 2).
- **k.5 Close the batch.** Remove the worktrees (`git worktree remove <wt>`, then `git branch -d wp30-s<NN>`, which succeeds only because the commit's patch landed; check with `git log --format=%s wp30-p1 | grep -F "<subject>"` first and use `-D` only after that check). Then run `git rev-parse HEAD > <scratch>/batch-<k+1>-base.txt`. The next batch is cut only after this one is green.

### Batch 0: S01 alone (tracking foundation)
- **S01** Tracking foundation [green, S]: `TF`.
- **Why alone:** every later gate needs four things S01 creates: the section's BUGS.md entry, its `WP30_OPEN` key, its CHANGELOG markers and its own stub block in the truth script. None of them is on the step-0a tree. S01 changes no shipped file.
- **0.0** Impact at `batch-0-base` for the test-module symbols S01 edits: `TestNoOpenEntryBlocksARelease`, `_wp29_*` (mirrored, not edited) and `TestTheWp29TruthScript` (mirrored). No HIGH or CRITICAL is expected.
- **0.1** `git worktree add …/dash-wt/wp30-s01 -b wp30-s01 wp30-p1`.
- **0.2** S01's one commit `(WP-30 S01)`, which:
  - opens the 56 entries and the 84 markers;
  - writes `WP30_OPEN`, `WP30_LISTS` and `TestWp30Tracking`;
  - writes the truth script's scaffold and 56 stubs, the runner block `// 69.` and the hygiene pins;
  - adds `TestTheWp30TruthScript`, the map anchors (A148) and `test_every_listed_name_exists` (A149).
- **0.3** Land it.
- **0.4** G8. The truth script runs all 57 blocks, and each stub prints its start and end lines.
- **0.5** Record `batch-1-base.txt`. Batch 1 also waits for the ratified record (A151).

### Batch 1: platform floor (S02, S03)
- **Theme (manifest):** Platform floor: portable runners and the Stata 19 floor.
- **Steps:**
  - **1.0** Impact at `batch-1-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **1.1** Cut `wp30-s02`, `wp30-s03`.
  - **1.2** 2 commits.
  - **1.3** Land them in the order S02, S03, rebuilding the index after each landing.
  - **1.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD. Then `make cert` once through the queue (cert mode).
  - **1.5** Remove the worktrees and record `batch-2-base.txt`.
- **S02** Portable runners (P1.34 under M4) [yellow, M]; **S03** Stata 19 floor (P1.35 under M2) [yellow, M].
- **Merge order: S02, S03.** Both edit `scripts/wire_option_reporting.py`: S02 its repository/refusal lines (IR-7) and S03 its emitted version line, so S02 lands first. S03's sweep rewrites the 91 `version 16.0` lines (79 in dash.ado and 12 in dash_setup.ado at `c96facd`), which S02 does not touch.
- **1.0 expected HIGH/CRITICAL:** none in `dash_render.py`. S03's programs are all Stata (`UNKNOWN`; grep).
- **1.4 G8, plus `make cert` once through the queue (cert mode)** after both have landed, timed against `wp30-cert-baseline.log`. This is the sweep's full certification run (BUGS.md:568: the language level changes behaviour), and S03's pin that the callerver fallback (dash.ado:5995-5999) leaves function points unchanged runs inside it. Then `grep -c 'version 16.0' dash.ado dash_setup.ado` prints 0 and 0, and S02's guard test passes in the main checkout. Before S02 lands, `make cert` in a worktree would test the main checkout (S02's sub-claim 6), so no worktree runs it.

### Batch 2: hardening I (S04, S05, S06)
- **Theme (manifest):** Hardening I: a CSP without 'unsafe-inline' and a safe Windows opener, the measured Python floor, notes through Stata's channel.
- **Steps:**
  - **2.0** Impact at `batch-2-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **2.1** Cut `wp30-s04`, `wp30-s05`, `wp30-s06`.
  - **2.2** 4 commits (S05 lands as two), plus S05's floor matrix (commit A: 6 pytest runs) and its one floor certification run (commit B), through the queue.
  - **2.3** Land them in the order S04, S05, S06, rebuilding the index after each landing.
  - **2.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **2.5** Remove the worktrees and record `batch-3-base.txt`.
- **S04** CSP without 'unsafe-inline'; safe Windows opener [yellow, M]; **S05** Measured Python floor [yellow, M, two commits]; **S06** One note channel [yellow, M].
- **Merge order: S04, S05, S06.** They share no program: S04 has the page assembly, the served template line and `_dash_open_page`; S05 has dash_setup's floor, conftest and the floor script; S06 has `__main__` and the 11 txt note sites. They do share files: S05 and S06 both edit `scripts/release_verdict.py` (S05: `FLOOR_REQUIRED`, `declared_floor`, `floor_verdict` and `main`'s `--floor` form; S06: `DIAGNOSTICS`) and `test/test_release_verdict.py` (different classes); S04 and S06 each add one name to `_dash_require_mata`'s `_needed` (:242 / :247; A139's recorded exception). S06 lands last so it can migrate any `UserWarning` needle a partner adds (A150).
- **2.0 expected HIGH/CRITICAL:** S04 `_assemble_layout`, `_render_bootstrap_html` (CRITICAL) and `ServerAppBuilder._generate_app_source` (HIGH, one generated `doc.template` line). S06 `main` (HIGH). S06 does not edit `_dash_warn_once`, `_dash_style_note` or `_dash_reset_notes` (CRITICAL).
- **2.2 S05's commit A runs the floor matrix**, every leg through the queue:
  - six pytest runs in scratch venvs: 3.11 and 3.12, each with the dev pins and with the Stata pins, plus one fresh-resolve leg per Python;
  - the Stata venv-link leg per Python.

  **S05's commit B runs the one floor certification run**, with Stata linked to the floor interpreter for that run only (E12). It cannot run at commit A: at commit A's floor 3.13 the setup cscripts refuse a linked 3.11 by construction (S05 D-05a).

  Downloads go only into `<scratch>/venv-*` (M10). S04 allocates SB-21..30 and PV-28..34 before S12 writes (X.3).

### Batch 3: what every graph is drawn from (S07, S08, S09)
- **Theme (manifest):** What every graph is drawn from: the 26 StataCorp schemes, Stata size units, TeX drawn as typed.
- **Steps:**
  - **3.0** Impact at `batch-3-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **3.1** Cut `wp30-s07`, `wp30-s08`, `wp30-s09`.
  - **3.2** 3 commits.
  - **3.3** Land them in the order S07, S08, S09, rebuilding the index after each landing.
  - **3.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **3.5** Remove the worktrees and record `batch-4-base.txt`.
- **S07** Ship the six StataCorp schemes [green, M]; **S08** Stata size units for markers, text and gaps [yellow, M]; **S09** TeX delimiters inert on every canvas sink [yellow, S].
- **Merge order: S07, S08, S09.** S07 regenerates (20 → 26 scheme files) and still lands first: no partner touches the extractor, a scheme file or `scheme_truth.json`, so R7's "regenerator last" protects nothing here (A152). S08 cannot sit with S10, because both edit `_dash_apply_legend` and `_dash_apply_z_options`.
- **3.0 expected HIGH/CRITICAL:** S08 `_dash_dim_nonselection` (CRITICAL, 8 impacted; ratification row 27, the brushed copies; `_dash_add_glyph` and `_dash_add_pc_glyph` show LOW but their served callers are template lines the index does not resolve). S08 `translate_msize`, `_textbox_size`, `_mlabel_gap_px`, `_apply_marker_opts` and `_apply_mlabel_opts` (CRITICAL; the 11 `_apply_mlabel_opts` call sites are `map_*`, `UNKNOWN` through dispatch). S09 `DashRenderer._build_sources_and_figures` (CRITICAL, one call) and `_generate_app_source` (HIGH, one generated line). The page-baseline digest moves with S08 and S09 (R10).

### Batch 4: twoway's input grammar (S10, S11, S12)
- **Theme (manifest):** twoway's input grammar: sub-option abbreviations, stylelists, the drop-in command form and saving().
- **Steps:**
  - **4.0** Impact at `batch-4-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **4.1** Cut `wp30-s10`, `wp30-s11`, `wp30-s12`.
  - **4.2** 3 commits.
  - **4.3** Land them in the order S10, S11, S12, rebuilding the index after each landing.
  - **4.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **4.5** Remove the worktrees and record `batch-5-base.txt`.
- **S10** Sub-option abbreviations [yellow, M]; **S11** Stylelists across an expanded varlist [yellow, M]; **S12** Drop-in command form and the `saving()` grammar [yellow, M].
- **Merge order: S10, S11, S12.**
  - S10 edits the renderer's sub-option readers, Mata `_dash_rep_subkey` and its own `_dash_axreq_clear`/`_dash_axreq_add`, and one 3-line hunk of `_dash_plot` at the axis check (:5323-5325). The title and axis-title refusals (TR-10.6a) are S10's.
  - S11 edits `_dash_parse_plot_opts`, `_dash_plot_opts_to_json`, `_dash_process_segment` and the folds.
  - S12 edits the `dash` dispatcher (after S03's guard; A154), the browser deciders, the saving blocks, `_dash_plot` (the as-typed saving paragraph above :5540 and the fold at :5560-5568), `_dash_validate_path` and `_dash_launch_app`'s `--show` path. It comes after S04's opener (batch 2), as M11 requires.
  - **A139 exception, granted 06oct2026 (ratification row 31; S12 Notes):** `_dash_plot` is edited by S10 and S12 in hunks more than 200 lines apart, and `_dash_require_mata`'s `_needed` by S10 (after :255), S11 (after :250) and S12 (after :255), on separate continuation lines. The conflict is context only: the merger applies each later patch with `git apply --index -3` and keeps every section's names in `_needed` (R6).
- **4.0 expected HIGH/CRITICAL:** S10 `_dash_parse_axis_spec` and `_parse_axis_angle` (CRITICAL). S12 `_dash_launch_app` (HIGH). The Stata and Mata programs are `UNKNOWN`.

### Batch 5: default look I (S13, S14, S15)
- **Theme (manifest):** Default look I: line widths, bar widths and caps, scheme chrome.
- **Steps:**
  - **5.0** Impact at `batch-5-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **5.1** Cut `wp30-s13`, `wp30-s14`, `wp30-s15`.
  - **5.2** 3 commits.
  - **5.3** Land them in the order S13, S14, S15, rebuilding the index after each landing.
  - **5.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **5.5** Remove the worktrees and record `batch-6-base.txt`.
- **S13** Stata line-width ladder [yellow, M]; **S14** Bar widths and range caps [yellow, M]; **S15** Scheme chrome: titles, ticks, grid, economist axes [yellow, M].
- **Merge order: S13, S14, S15.** S15 regenerates the 26 scheme files and lands last. S15 reads the scheme's tick widths through the existing line translator, so S13's ladder applies on merge without a declared dependency. S13 does not edit `SchemeParser._init_properties`; S15 replaces its two pixel-literal width defaults (S13 D-13g). S14 is batch 5's one `_generate_app_source` editor (deletion only, D-14b).
- **5.0 expected HIGH/CRITICAL:** S13 `_apply_line_opts` (CRITICAL, about 40 impacted). S14 `_build_filter_widgets` and `FilterBuilder.build_dropdown` (CRITICAL; two default arguments removed), `ServerAppBuilder._generate_app_source` (HIGH; four emitted lines deleted, D-14b) and `ServerAppBuilder._glyph_layer_lines` (HIGH; one name removed); S14 deletes `GlyphMapper._tag_spacing` (dash_render.py:10293), `_dash_copy_redraw_geometry` and the `_FILTER_JS` spacing writer, and does not edit `_make_figure_body`. S15 `ServerAppBuilder._glyph_layer_lines` (HIGH; one name appended); its `SchemeParser.apply_to_figure`/`apply_to_axis`, `_dash_add_secondary_axes` and `_dash_finish_secondary_axes` measured LOW (S15 E10) and are still run at 5.0.

### Batch 6: default look II and display formats (S16, S17, S18)
- **Theme (manifest):** Default look II and display formats: intensity as an opaque blend, date and format text in keys and tooltips, axis label formats.
- **Steps:**
  - **6.0** Impact at `batch-6-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **6.1** Cut `wp30-s16`, `wp30-s17`, `wp30-s18`.
  - **6.2** 3 commits.
  - **6.3** Land them in the order S16, S17, S18, rebuilding the index after each landing.
  - **6.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **6.5** Remove the worktrees and record `batch-7-base.txt`.
- **S16** Intensity as an opaque blend [yellow, M]; **S17** Date and format text in keys and tooltips [yellow, M]; **S18** Axis format fallbacks [yellow, M].
- **Merge order: S16, S17, S18.** S18 is the batch's one `_generate_app_source` and `_make_figure_body` editor, and its one editor of dash.ado's `_dash_option_rules` and `_dash_validate_value`: S17 edits no Stata file (its `zlabel()` refusal moved to S18's TR-18.13 (e)). S18 lands a batch before S21, whose FixedTicker reuses its `_dash_axis_tick_formats`. S16 and S18 both move the single-y page digest; the merger re-derives it after S18 lands (R10).
- **6.0 expected HIGH/CRITICAL:** S16 `_scheme_alpha`, `_apply_fill_opts`, `_blend_intensity` and `_ci_band_style` (HIGH). S17 `_apply_colorvar` and `_dash_apply_z_options` (HIGH); the colorvar callers (`map_scatter`, `map_connected`, `map_dot`, `map_rconnected`) are not edited. S18 `_make_figure_body` (CRITICAL), `_generate_app_source`, `ServerAppBuilder._glyph_layer_lines` and `_dash_apply_axis_spec` (HIGH). S18 adds the closed P1.5.7 entry (A146) and regenerates `format_truth.json` through its extractor.

### Batch 7: default axes and series text (S19, S20, S21)
- **Theme (manifest):** Default axes and series text: natscale ticker and twoway margin, legend keys and default titles, per-series value lists.
- **Steps:**
  - **7.0** Impact at `batch-7-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **7.1** Cut `wp30-s19`, `wp30-s20`, `wp30-s21`.
  - **7.2** 4 commits (S19 lands as two).
  - **7.3** Land them in the order S19, S20, S21, rebuilding the index after each landing.
  - **7.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **7.5** Remove the worktrees and record `batch-8-base.txt`.
- **S19** Legend keys and default axis titles [yellow, M, two commits]; **S20** Per-series value lists [yellow, S]; **S21** natscale ticker and twoway margin on non-date axes [red, L].
- **Merge order: S19, S20, S21.** S21 is red. It is the batch's finisher, template, figure-body and scheme regenerator (`numticks_g` and the margin keys), and it lands last. Its partners touch no axis function: S19 the key and title helpers, S20 Stata-only value checks. S19 and S20 both edit dash.ado's `_dash_process_segment` in disjoint hunks (S19 :3679-3683 and :4309-4312, S20 the `_dash_validate_opts` call at :4121-4126): a recorded A139 exception; S19 lands first and S20's patch applies with `git apply --index -3`.
- **7.0 expected HIGH/CRITICAL:** S19 `_dash_axis_labels` (HIGH). S21 `_make_figure_body`, `_dash_padded_range`, `_dash_common_count_ticks`, `_dash_share_by_scales` and `build_dropdown` (CRITICAL; each warned before editing), plus `DashRenderer.render` (CRITICAL, 13 impacted; S21 step 5b), `build_slider`, `build_range`, `_dash_limit_ranges_to_primary`, `_dash_keep_primary_ranges` and `_generate_app_source` (HIGH). S19 and S21 `ServerAppBuilder._glyph_layer_lines` (HIGH; distinct R2 anchors).
- **7.2 extra:** S21 measures, at `batch-7-base`, HEAD's 100-panel settle time and the served re-finish cost at 500k rows, and pins both budgets (A9; IR-17). It re-hulls explicit-value axes after a move (P1.3.6) and must not land without its after-move re-finish in both modes.

### Batch 8: scheme keys on every layer; notes and r(filename) reach Stata (S22, S23, S24)
- **Theme (manifest):** Scheme keys on every layer; served notes and r(filename) reach Stata.
- **Steps:**
  - **8.0** Impact at `batch-8-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **8.1** Cut `wp30-s22`, `wp30-s23`, `wp30-s24`.
  - **8.2** 3 commits.
  - **8.3** Land them in the order S22, S23, S24, rebuilding the index after each landing.
  - **8.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **8.5** Remove the worktrees and record `batch-9-base.txt`.
- **S22** r(filename) and the stale-graph note [yellow, S]; **S23** Served notes reach Stata [yellow, M]; **S24** Scheme opacity, histogram style and symbols reach every layer [yellow, M].
- **Merge order: S22, S23, S24.**
  - S22 edits the `dash` dispatcher (the rclass dispatch, last in A154's order) and the ends of `_dash_render_immediate` and `_dash_build`.
  - S23 is the batch's template and figure-body editor: one argument on `_make_figure_body`, the trial (IR-10) and `_dash_launch_app`'s relay.
  - S24 regenerates and lands last.
  - S22's stale-graph note fires on every file-writing dash command while a Stata graph (a `nodraw` one included) is in memory; partners that count notes (S23's NC-07..NC-10) clear graph memory before their dash calls.
- **8.0 expected HIGH/CRITICAL:** S23 `_make_figure_body` (CRITICAL), `_generate_app_source` and `ServerAppBuilder._glyph_layer_lines` (HIGH; three names at R2's S23 anchor and the hook's install line); S23 measured `_dash_launch_app` LOW (7) and still runs it at 8.0. S24 `_apply_marker_opts` and `_empty_fit_line` (CRITICAL), `_scheme_alpha`, `_render_ci_band`, `_ci_line_restyle` and `_add_arrow_heads` (HIGH) and about 30 mappers (`UNKNOWN`). S24 does not edit `_apply_line_opts`.

### Batch 9: twoway's default bar base; failing clearly (S25, S26, S27)
- **Theme (manifest):** twoway's default bar base; failing clearly: render-time dependency guards and the function needs-points note.
- **Steps:**
  - **9.0** Impact at `batch-9-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **9.1** Cut `wp30-s25`, `wp30-s26`, `wp30-s27`.
  - **9.2** 3 commits.
  - **9.3** Land them in the order S25, S26, S27, rebuilding the index after each landing.
  - **9.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **9.5** Remove the worktrees and record `batch-10-base.txt`.
- **S25** Render-time dependency guards [yellow, M]; **S26** function: closed by disposition [green, S]; **S27** twoway's default base and axis extent [yellow, M].
- **Merge order: S25, S26, S27.** S25 is the template editor: the guard in the generated header, which is not on a copy list. S26 edits `map_function` and is kept apart from S24, S35, S40, S45 and S49. S27 hooks into S21's finishers (R11) and lands last.
- **9.0 expected HIGH/CRITICAL:** S25 `_generate_app_source` (HIGH). S26 `ServerAppBuilder._glyph_layer_lines` (HIGH), only if it adds a helper. S27 `_dash_common_count_ticks` (CRITICAL), `_dash_finish_count_ticks`, and S21's `_dash_axis_plan`, `_dash_layer_extent`, `_dash_tag_hull_roles` and `_DASH_AXIS_FINISH_JS` (measured at 9.0); `_dash_refinish_axes` is expected unedited. S27 retires S21's `_dash_auto_base` for the renderer tag `dash_base:` and adds `autobase`/`bases` keys to `_dash_axis_plan`'s per-axis plan.

### Batch 10: colour grammar and graph text (S28, S29, S30)
- **Theme (manifest):** Colour grammar and graph text: by() panel labels and overall text, SMCL in graph text, Stata's colour grammar.
- **Steps:**
  - **10.0** Impact at `batch-10-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **10.1** Cut `wp30-s28`, `wp30-s29`, `wp30-s30`.
  - **10.2** 3 commits.
  - **10.3** Land them in the order S28, S29, S30, rebuilding the index after each landing.
  - **10.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **10.5** Remove the worktrees and record `batch-11-base.txt`.
- **S28** by() panel labels and overall text [yellow, M]; **S29** SMCL in graph text [yellow, M]; **S30** Stata colour grammar [yellow, M].
- **Merge order: S28, S29, S30.** S28 is the template editor (the by() titles). S29 extends S09's pass and edits neither `_build_sources_and_figures` nor `_generate_app_source`; it lands after S28 so its pass tests see S28's new sinks. S30 edits the colour reader, SchemeParser's colour methods and the extractor (no applier, no mapper), regenerates, and lands last.
- **10.0 expected HIGH/CRITICAL:** S28 `_build_sources_and_figures`, `_dash_parse_by`, `_dash_by_groups`, `DashRenderer._expand_by_groups`, `_dash_layout_cell` and `DashRenderer._facet_label` (CRITICAL), `_generate_app_source`, `_glyph_layer_lines` and `ServerAppBuilder._plan_by_groups` (HIGH) (section-28 E11). S29 `_apply_mlabel_opts`, `_dash_filter_title` and `_dash_filter_widget` (CRITICAL) and `_glyph_layer_lines` (HIGH); `_mlabel_column_kind` is read, not edited. S30 `translate_mcolor` (CRITICAL, 26 impacted), `_textbox_color` (CRITICAL, 9), `_resolve_kpi_color` (CRITICAL, 7), `_apply_intensity` (CRITICAL, 9), `ColorResolver.resolve_with_opacity` (CRITICAL, 13), `SchemeParser._color` (HIGH, 7), and `GlyphMapper.__init__`/`parse_color_alpha` treated as HIGH (section-30 E7).

### Batch 11: styles from the scheme and the axis look (S31, S32, S33)
- **Theme (manifest):** Styles from the scheme and the axis look: axis look sub-options, named styles p1-p15, marker-label and colour-key text styles.
- **Steps:**
  - **11.0** Impact at `batch-11-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **11.1** Cut `wp30-s31`, `wp30-s32`, `wp30-s33`.
  - **11.2** 3 commits.
  - **11.3** Land them in the order S31, S32, S33, rebuilding the index after each landing.
  - **11.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **11.5** Remove the worktrees and record `batch-12-base.txt`.
- **S31** Axis look sub-options [yellow, L]; **S32** Named styles p1-p15 [yellow, L]; **S33** Marker-label and colour-key chrome; unread directives retained [yellow, M].
- **Merge order: S31, S32, S33.** S31 edits the axis parse and apply functions. S32 edits the appliers, the ten colour-reading mappers and the plot syntax. S33 edits `_apply_mlabel_opts`, `_apply_colorvar` and SchemeParser's read-recording, adds `color_idx=color_idx` to the `_apply_mlabel_opts` call line in seven mappers S32 also edits (A139 exception, ratification row 37; the merger re-adds the keyword by hand on any conflict and runs `TestEveryLabelledTypeTakesItsLayersColour` on the merged tree), regenerates, and lands last.
- **11.0 expected HIGH/CRITICAL:** S31 `_dash_parse_axis_spec`, `_parse_axis_angle` and `_dash_scale_spec` (CRITICAL) and `_dash_apply_z_options` (HIGH). S32 `_apply_marker_opts` and `_apply_line_opts` (CRITICAL). S33 `_apply_mlabel_opts` (CRITICAL) and `_apply_colorvar` (HIGH).

### Batch 12: resolved as Stata resolves it (S34, S35, S36)
- **Theme (manifest):** Resolved as Stata resolves it: scheme lookup along the ado-path, date positions on every axis, other style names.
- **Steps:**
  - **12.0** Impact at `batch-12-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **12.1** Cut `wp30-s34`, `wp30-s35`, `wp30-s36`.
  - **12.2** 3 commits.
  - **12.3** Land them in the order S34, S35, S36, rebuilding the index after each landing.
  - **12.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **12.5** Remove the worktrees and record `batch-13-base.txt`.
- **S34** Stata's scheme lookup along the ado-path [yellow, M]; **S35** Date positions on every axis [yellow, L]; **S36** Other style names [yellow, M].
- **Merge order: S34, S35, S36.** S34 regenerates nothing; its four one-line `_generate_app_source` edits (TR-34.13) are an R12 exception granted 06oct2026 (ratification row 38): the orchestrator records the approval in `<scratch>/batch-12-impact.txt` at 12.0, and 34-01 stops if it is absent. S35 is the batch's template, figure-body and finisher editor, and does not touch S34's four lines. S36 extends `SchemeParser.style_bundle` and its table (IR-14), and also edits `GlyphMapper._STYLE_FACTORS`, `_style_plan`, `_style_restyle` (retirement), `_ci_pstyle`, `_ci_band_style` and `_ci_line_restyle`, dash.ado's plot declarations, sreturn and JSON key list and Mata `_dash_stylelist_keys`; none is a partner's symbol. S36 regenerates and lands last.
- **12.0 expected HIGH/CRITICAL:** S34 `SchemeParser._resolve_path`, `resolve_or_fallback` and `_include` (HIGH), and `DashRenderer._scheme_for` and `DashRenderer._make_figure` (CRITICAL). S36 `_ci_pstyle`, `_ci_band_style` and `_ci_line_restyle` (HIGH). S35 `_dash_axis_date_kind`, `GlyphMapper._on_axis`, `_make_figure_body`, `_build_sources_and_figures` and `_dash_common_count_ticks` (CRITICAL).
- **12.2 extra:** S34 adds the closed P1.25.6 entry (A146). S35's headless-Chrome check renders the CustomJSTransform under S04's CSP.

### Batch 13: region styling and marker-label placement (S37, S38)
- **Theme (manifest):** Region styling and marker-label placement: mlabvposition() and mlabtextstyle(), plotregion()/graphregion() styling.
- **Steps:**
  - **13.0** Impact at `batch-13-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **13.1** Cut `wp30-s37`, `wp30-s38`.
  - **13.2** 3 commits (S37 lands as two).
  - **13.3** Land them in the order S37, S38, rebuilding the index after each landing.
  - **13.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **13.5** Remove the worktrees and record `batch-14-base.txt`.
- **S37** mlabvposition() and mlabtextstyle() [yellow, M, two commits]; **S38** plotregion()/graphregion() styling [yellow, M].
- **Merge order: S37, S38.** Only two sections fit: every other ready section edits `_dash_parse_plot_opts`, `_make_figure_body`, `_generate_app_source` or a mapper that one of these two edits. S38 is the template and figure-body editor. S37 regenerates the scheme files in its second commit and still lands first, the S07-style exception (A152): S38 touches no extractor, scheme file or `scheme_truth.json`.
- **13.0 expected HIGH/CRITICAL:** S37 `_apply_mlabel_opts` and `_dash_option_columns` (CRITICAL). S38 `_make_figure_body` (CRITICAL). S38's region readers replace `_extract_region_*` on the copy list (R2), and it flips `bgcolor()` (IR-2).

### Batch 14: lines and the verified bokeh window (S39, S40, S41)
- **Theme (manifest):** Lines: xline/yline positions and lstyle, connect() and cmissing(); the verified bokeh window.
- **Steps:**
  - **14.0** Impact at `batch-14-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **14.1** Cut `wp30-s39`, `wp30-s40`, `wp30-s41`.
  - **14.2** 4 commits (S41 lands as two), plus S41's bokeh 3.10 leg: 1 pytest run through the queue.
  - **14.3** Land them in the order S39, S40, S41, rebuilding the index after each landing.
  - **14.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **14.5** Remove the worktrees and record `batch-15-base.txt`.
- **S39** xline/yline positions, refusals and lstyle [yellow, M]; **S40** connect() and cmissing() [yellow, M]; **S41** Verified bokeh window; internals fail closed [yellow, M, two commits].
- **Merge order: S39, S40, S41.** S40 edits `_FILTER_JS` and `_make_figure_body`, which neither partner touches. S41 is the template editor (the launcher part) and lands last.
- **14.0 expected HIGH/CRITICAL:** S39 calls `_dash_expand_numlist` (CRITICAL) but does not edit it. S40 `_make_figure_body` and `_build_filter_widgets` (CRITICAL). S41 `main` and `_generate_app_source` (HIGH), `_dash_served_template`, `_dash_harden_origin_check` and `_dash_token_auth`.
- **14.2 extra:** S41 verifies bokeh 3.10 in a scratch venv: one pytest run through the queue plus the text-sink checks (E12). The ceiling rises to `<3.11` only if both are green.

### Batch 15: time series and colour sites (S42, S43, S44)
- **Theme (manifest):** Time series and colour sites: time-series operators, bare *# at every colour site, tsnatscale date axes.
- **Steps:**
  - **15.0** Impact at `batch-15-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **15.1** Cut `wp30-s42`, `wp30-s43`, `wp30-s44`.
  - **15.2** 4 commits (S42 lands as two).
  - **15.3** Land them in the order S42, S43, S44, rebuilding the index after each landing.
  - **15.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **15.5** Remove the worktrees and record `batch-16-base.txt`.
- **S42** Time-series operators in plot varlists [yellow, L, two commits]; **S43** Default colour and opacity at every colour site [yellow, M]; **S44** tsnatscale on %td-%ty default axes [red, L].
- **Merge order: S42, S43, S44.** S42 is the one template editor. S43 reaches every colour site once, after S30, S31, S32, S38 and S39. S44 extends S21's helpers and JS on the date path only, and lands last.
- **15.0 expected HIGH/CRITICAL:** S42 `_dash_csv_meta` (CRITICAL). S43 `_apply_marker_opts`, `_apply_line_opts`, `_apply_mlabel_opts`, `_textbox_color` and `_resolve_kpi_color` (CRITICAL); it does not edit `_shared_stat_lines`. S44 `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS` (S21's).
- **15.2 extra:** S44 tests JS-Python parity over the fixture's 12,000 answers, with the agreement floors pinned (A8), and closes BUGS.md:2523.

### Batch 16: recast(), served session limits, plot-region margins (S45, S46, S47)
- **Theme (manifest):** recast(), served session limits, plot-region margins.
- **Steps:**
  - **16.0** Impact at `batch-16-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **16.1** Cut `wp30-s45`, `wp30-s46`, `wp30-s47`.
  - **16.2** 3 commits.
  - **16.3** Land them in the order S45, S46, S47, rebuilding the index after each landing.
  - **16.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **16.5** Remove the worktrees and record `batch-17-base.txt`.
- **S45** recast() [yellow, L]; **S46** Served session capacity and memory [yellow, M]; **S47** Plot-region margin and inner box [yellow, M].
- **Merge order: S45, S46, S47.**
  - S45 edits `_dash_glyph_dispatch`, the ten derived mappers' tails, the plot syntax, the pending list and the folds.
  - S46 edits `__main__`'s argparse, `_dash_launch_app` and the served session hooks.
  - S47 is the figure-body and finisher editor; it regenerates and lands last.
- **16.0 expected HIGH/CRITICAL:** S46 `_dash_launch_app` (HIGH); S46 does not edit `_dash_limits` (CRITICAL). S47 `_dash_padded_range` (CRITICAL), S38's `_dash_region_spec` and S21's finishers (impact at 16.0); `_make_figure_body` (CRITICAL) only if 47-08 finds it must edit it.
- **16.2 extra:** S46 measures per-session RSS at 200k x 3 (A116) and the warm-up line (IR-10).

### Batch 17: horizontal drawn, by() grid and size, reference-line extent (S48, S49, S50)
- **Theme (manifest):** horizontal drawn, by() grid and size, reference-line extent.
- **Steps:**
  - **17.0** Impact at `batch-17-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **17.1** Cut `wp30-s48`, `wp30-s49`, `wp30-s50`.
  - **17.2** 3 commits.
  - **17.3** Land them in the order S48, S49, S50, rebuilding the index after each landing.
  - **17.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **17.5** Remove the worktrees and record `batch-18-base.txt`.
- **S48** by() grid and size [yellow, M]; **S49** horizontal drawn [yellow, M]; **S50** xline/yline extend, noextend and style() [yellow, M].
- **Merge order: S48, S49, S50.** S49 is the figure-body editor and swaps titles through S19's helper (IR-13). S50 edits `_DASH_AXIS_FINISH_JS` and `_dash_refinish_axes`, never `_FILTER_JS`; it regenerates and lands last.
- **17.0 expected HIGH/CRITICAL:** S48 `_dash_parse_by`, `_dash_layout_cell` and `_dash_reflow` (CRITICAL; `_dash_by_groups` is read only). S49 `_make_figure_body` (CRITICAL), `_dash_axis_labels`, `_generate_app_source` and `_glyph_layer_lines` (HIGH). S50 reads `_dash_range_hull` and does not edit it.

### Batch 18: axis options (S51, S52, S53)
- **Theme (manifest):** Axis options: tsline time-axis options, add, shared axes and keys under by().
- **Steps:**
  - **18.0** Impact at `batch-18-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **18.1** Cut `wp30-s51`, `wp30-s52`, `wp30-s53`.
  - **18.2** 4 commits (S51 lands as two).
  - **18.3** Land them in the order S51, S52, S53, rebuilding the index after each landing.
  - **18.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **18.5** Remove the worktrees and record `batch-19-base.txt`.
- **S51** tsline time-axis options [yellow, L, two commits]; **S52** The add sub-option [yellow, M]; **S53** Shared axes and keys under by() [yellow, L].
- **Merge order: S51, S52, S53.**
  - S51 is Stata and Mata only.
  - S52 is the only finisher editor of the batch. The `tlabel(..., add)` cross case is S51's TA-02 fold pin plus S52's drawing of `xlabel(492, add)` (AD-22, against twoway's `tlabel(2001m1, add)`), since S52's worktree is cut without S51; G8 runs both on the merged tree. S51 and S52 edit adjacent hunks of Mata `_dash_rep_subs`/`_dash_rep_merge` (context only; the merger keeps both).
  - S53 edits the by() legend and axes, regenerates, and lands last.
- **18.0 expected HIGH/CRITICAL:** S52 `_dash_parse_axis_spec` (CRITICAL), `_dash_apply_axis_spec` and `_dash_apply_z_options` (HIGH). S53 `_build_sources_and_figures`, `_dash_reflow`, `_dash_layout_cell` and `_dash_parse_by` (CRITICAL), `_generate_app_source` and `_glyph_layer_lines` (HIGH). S51's and S52's Mata functions are `UNKNOWN`.

### Batch 19: the last drawing pieces (S54, S55, S56)
- **Theme (manifest):** Last drawing pieces: Save as SVG, horizontal after a filter move, text() and ttext().
- **Steps:**
  - **19.0** Impact at `batch-19-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **19.1** Cut `wp30-s54`, `wp30-s55`, `wp30-s56`.
  - **19.2** 4 commits (S56 lands as two).
  - **19.3** Land them in the order S54, S55, S56, rebuilding the index after each landing.
  - **19.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **19.5** Remove the worktrees and record `batch-20-base.txt`.
- **S54** Client-side Save as SVG [yellow, M]; **S55** horizontal after a filter move [yellow, M]; **S56** text() and ttext() annotations [yellow, L, two commits].
- **Merge order: S54, S55, S56.**
  - S54 edits the toolbar helper and the copy list.
  - S55 edits the hover builder (`_dash_build_hover`) only; the redraw work is cancelled (IR-13, S14 D-14b).
  - S56 is the template, figure-body and scheme editor, and lands last.
- **19.0 expected HIGH/CRITICAL:** S54 `_dash_name_save` (CRITICAL, 11 impacted). S55 `_dash_build_hover` (LOW in the index; copied into the served app, treated as MEDIUM); S55 does not edit `_build_filter_widgets` (IR-13). S56 `_make_figure_body` (CRITICAL) and `_generate_app_source` (HIGH). S54 and S56 `ServerAppBuilder._glyph_layer_lines` (HIGH; distinct R2 anchors).

### Batch 20: served recompute off the event loop (S57)
- **Theme (manifest):** Served recompute off the event loop.
- **Steps:**
  - **20.0** Impact at `batch-20-base.txt`. The expected HIGH and CRITICAL symbols are listed below.
  - **20.1** Cut `wp30-s57`.
  - **20.2** 1 commit.
  - **20.3** Land them in the order S57, rebuilding the index after each landing.
  - **20.4** G8: the full suite once through the queue; the R2 registry tests; `test_wp30_truth.cscript` with all blocks, plus the area cscripts the batch touched; `gitnexus status` at HEAD.
  - **20.5** Remove the worktrees and record `batch-21-base.txt`.
- **S57** [red, L], alone. It restructures the served move path that S21, S27, S35, S44, S45, S47, S50, S52 and S55 edited.
- **20.0 expected HIGH/CRITICAL:** `_generate_app_source` (HIGH; only the move path). S57 does not edit `_dash_event_throttle` or `_dash_limits`.
- **20.2 extra:** S57 audits the final move path for thread safety, verifies Bokeh's thread rules across S41's window, and measures latency at N=100k under the session cap (A113).

## Test-writing rule (maintainer, 07oct2026; binding on every remaining section)

No duplicative tests. Each section adds one test per distinct behaviour or code branch, in each mode where the modes differ. Measured data -- fixture rows, probes, schemes, sizes -- is checked by ONE test per (fixture, mode) that loops over every row and reports every mismatch, never by one parametrized test per row. Parametrize over schemes or values only where they take different branches of the code. Before adding a test, grep for one with the same inputs and assertion. Where a section file's test plan says otherwise, this rule wins. A commit that only removes tests needs no full-suite run; only the rewritten files are run.

## How to execute

0. **Before any section runs, the orchestrator does seven things in the main checkout on `wp30-p1`.** Step 0g comes first, because 0a's G0 run and 0b use the queue; 0a then comes before everything else that commits. Step 0c waits for 0b. Steps 0d-0f use no CPU.

   0g. **Write the queue script** `<scratch>/full_suite_queue.sh`. It is not committed.
   ```sh
   #!/bin/sh
   # full_suite_queue.sh <repo> <log> [pytest|cert|test|test-dev|gate]
   # Wait for the machine-wide queue and a free suite, then run ONE full run in <repo>, at most 6 CPUs.
   set -u
   repo="$1"; log="$2"; mode="${3:-pytest}"; q=/tmp/dash-wp30-suite-queue.d
   until mkdir "$q" 2>/dev/null; do sleep 15; done
   trap 'rmdir "$q"' EXIT INT TERM
   hook=/Users/billy/Desktop/Programs/StataPrograms/d/dash/.claude/hooks/guard-full-suite.sh
   until python3 -c "from importlib.machinery import SourceFileLoader as L; g=L('g','$hook').load_module(); raise SystemExit(1 if g.full_run_in_progress() else 0)"; do sleep 15; done
   cd "$repo" || exit 2
   case "$mode" in
     pytest) FULL_SUITE_RERUN=1 python3 -m pytest test/ -q -n 6 > "$log" 2>&1; echo "exit=$?" >> "$log" ;;
     *) { date +%s; make "$mode" PYTEST_ARGS='-q -p no:cacheprovider -n 6'; echo "exit=$?"; date +%s; } > "$log" 2>&1 ;;
   esac
   ```
   - The hook's check printed `None` and exited 0 when the machine was idle (03oct2026).
   - A queue directory left behind by a dead holder (`/tmp/dash-wp30-suite-queue.d` exists and `pgrep -f full_suite_queue.sh` finds nothing) is removed by the orchestrator, after it checks that no run is in progress.

   0a. **Commit the plan.** This is the final plan, with this index, `PLAN.md`, `manifest.json`, `decisions.md`, `decision-register.md`, `open-questions.md`, `STATUS.md`, the 35 research notes, the 10 files of `review-notes/` and the 58 section files.
   1. `git branch --show-current` prints `wp30-p1`.
   2. Run `git add .ultraplan/wp30/`, then `git add -f .ultraplan/wp30/manifest.json` (`.git/info/exclude:58` ignores `*.json`). Stage nothing else: never `CLAUDE.md`, `.gitignore` or `AGENTS.md`.
   3. Check the staged set:
      - `git diff --cached --name-only | grep -vc '^\.ultraplan/wp30/'` prints 0;
      - `git diff --cached --name-only | wc -l` equals `find .ultraplan/wp30 -type f ! -name .DS_Store | wc -l` (110 once `section-58-closeout.md` is written: 58 section files, 7 plan documents, 35 research notes and 10 review notes).
   4. Precondition P-1 (ratification row 29, answered 06oct2026: "Ignore the file in the packaging root test"; section-01 Notes): `PhilSchummSuggestion.md` stays in the package root and `test/test_packaging.py::_ROOT_ALSO` names it. That one-line change is in the working tree (uncommitted); after one full run is green it is committed on `wp30-p1` in a commit of its own, before step 0a. Without it `test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own` is red at `c96facd` (re-measured 06oct2026: 1 failed) and G0 cannot pass. Check: `git diff --quiet -- test/test_packaging.py` succeeds, `grep -c '"PhilSchummSuggestion.md"' test/test_packaging.py` prints 1, and `python3 -m pytest test/test_packaging.py -q -n0 -k root` passes.
   5. G0: one full run through the queue (`<scratch>/full_suite_queue.sh <main> <scratch>/s00-full.log`) must be green. The commit holds documents only, and the directory walks skip `.ultraplan` (`test/test_tracking_documents.py` `_SKIP_DIRS`, :99).
   6. Commit with the subject `Record the WP-30 plan for the drop-in P1 fixes (WP-30 S00)` and a body naming the files. Run G7 before and after.
   7. Then `git status --porcelain --ignored .ultraplan/wp30` prints nothing.

   0b. **Record the certification baseline** on the step-0a tree: `<scratch>/full_suite_queue.sh <main> <scratch>/wp30-cert-baseline.log cert`, launched in the background. Wait for its `exit=` line and read the log (E1). It must finish before step 1. S58 compares its time against this log.

   0c. **The GitNexus index.** `gitnexus status` showed the index at `c96facd` on 03oct2026. After 0a and 0b:
   - Run `gitnexus analyze --index-only --max-file-size 8192` in the main checkout.
   - `gitnexus status` must show `Indexed commit` equal to `git rev-parse --short HEAD`.
   - `git status --porcelain` is unchanged; `.gitnexus/` is ignored by the tracked `.gitignore:8`.
   - `python3 -m pytest test/test_tracking_documents.py -q -n0 -k nothing_links_them` passes with `.gitnexus/` present.

   0d. **Record the batch-0 base:** `git rev-parse HEAD > <scratch>/batch-0-base.txt`, which is the step-0a commit.

   0e. **Hand each section agent its inputs by absolute path.** The plan is tracked from 0a, and the main checkout's copy governs. The inputs:
   - its section file, `index.md`, `PLAN.md`, `manifest.json`, `decisions.md` and `decision-register.md` under `/Users/billy/Desktop/Programs/StataPrograms/d/dash/.ultraplan/wp30/`;
   - its research note `research/p1-NN.md`;
   - `.ultraplan/sections/BRIEF.md`;
   - the project instructions file;
   - `<scratch>/wp30-ratified.txt` and `<scratch>/batch-<k>-impact.txt`.

   A section agent never edits a plan file.

   0f. **Copy the ratified record** (A151). Copy "Decisions for maintainer ratification" from its heading through its last row, verbatim and with every row's last column filled, into `<scratch>/wp30-ratified.txt`. Check:
   - `grep -c '| pending |' <scratch>/wp30-ratified.txt` prints 0;
   - `grep -cE '^\| [0-9]+ \| ' <scratch>/wp30-ratified.txt` prints 44.

   Batch 1 is not cut until both checks pass.

1. **Batch 0: S01 alone, in its own worktree.** Follow "Batch 0" above. Afterwards:
   - remove the worktree;
   - the index has already been rebuilt after the landing (E4);
   - run `git rev-parse HEAD > <scratch>/batch-1-base.txt`.

   Batch 1's worktrees are cut from that commit and no earlier one.

2. **Batches 1-20, one agent per section, each in its own worktree,** by the step list of a batch (k.0-k.5).

   **The per-entry cycle** (rule 7; one pass per commit; twice for a two-commit section, A156):
   1. Write the commit's failing tests and run them against the unmodified tree. Save the failure text to `<scratch>/<NN>-<entry>[-<k>]-failure.txt` (G1). Tests of behaviour that is already right are listed separately as guard tests.
   2. Make the fix. Flip each pinned test in place, with a `Flipped:` line (R9). Add the fixtures, through an extractor in S02's form (R7), and fill the section's stub block in the truth script (R1).
   3. On the closing commit: close the BUGS.md entry in place, delete its `WP30_OPEN` key line, and replace its CHANGELOG markers in place (R4, R5).
   4. Run the changed test files with pytest (`-n0` for single files), and the section's cscripts through the driver with `WP30_ONLY=S<NN>`.
   5. Run `git -C <wt> merge --no-edit main`, expecting `Already up to date.` (E9).
   6. Run one full suite in the worktree through the queue: `<scratch>/full_suite_queue.sh <wt> <scratch>/<NN>-full-<k>.log`. It must show 0 failed (E6 for the known flaky tests).
   7. Check scope (G6) and the message (G7), confirm `git -C <wt> branch --show-current` prints `wp30-s<NN>`, and commit once on `wp30-s<NN>`.

   No test-only commit exists, and no commit is red.

   **The landing routine** (by the merger, in the main checkout; never `cd` into a worktree). For each commit `<sha>` of each section, oldest first, in the batch's merge order:
   1. `git branch --show-current` prints `wp30-p1` (E3). Run `git merge --no-edit main`, expecting `Already up to date.`.
   2. `git -C <wt> log -1 --format=%B <sha> > <scratch>/msg-<sha>.txt` and `git -C <wt> show --name-status --format= <sha> > <scratch>/names-<sha>.txt`.
   3. `git -C <wt> format-patch -1 --stdout <sha> | git apply --index -3` (E2). A conflict is resolved by hand under R1-R13, each resolved path is staged with `git add -f <path>`, and the resolution is written to `<scratch>/batch-<k>-merge.log`.
   4. `git diff --cached --name-status` equals `<scratch>/names-<sha>.txt`. `gitnexus detect-changes --scope all --repo dash > <scratch>/detect-<sha>.txt` names only the section's symbols (G6).
   5. G7 on `<scratch>/msg-<sha>.txt`. Then `git commit -F <scratch>/msg-<sha>.txt`, then G7 on `git log -1 --format=%B`.
   6. `diff <(git show --name-status --format= HEAD) <scratch>/names-<sha>.txt` prints nothing, and `git show --stat --format= HEAD` matches the worktree commit's stat line for line. A hand-resolved path may differ only in its counts, and is named in the merge log.
   7. If the commit touched a registry (R2) or a combined pin (R10), run the registry tests and that pin's test file on the merged tree now.
   8. Rebuild the index (E4).

   **A red result belongs to the section that owns the test.**
   1. Fix it in a fresh worktree of that section, cut from `wp30-p1`.
   2. Commit there with that entry's id, after steps 5-7 of the cycle.
   3. Land the commit by the routine.
   4. Re-run the failed file, then the full suite once more, through the queue.

3. **S58, the closeout,** in the main checkout on `wp30-p1` (batch 21, no worktree). Before each commit: `git branch --show-current`, `git merge --no-edit main`, one full run through the queue, `gitnexus detect-changes --scope all --repo dash`, and G7 before and after.
   - **S58.1 tracking.** Every WP-30 entry is closed with its commit. `WP30_OPEN = {}` gets a docstring like WP-29's. `TestWp30Tracking::test_no_wp30_entry_remains_open` is added. The map anchors left empty are removed (A148). BUGS.md then holds exactly 3 open entries ("P1 coverage"; P2.49 not filed, ratification row 27).
   - **S58.2 tracking documents** (A145):
     - GAPS2.md "Tracked" lines: `- **Tracked:** Closed in WP-30, BUGS.md "<title>", commit <sha>`, with `(WP-30, <GAPS2 id>)` appended to the Resolution;
     - GAPS.md and REMAINING.md (the REM ids);
     - ROADMAP.md: the WP-30 entry; the scope changes of P2.11-P2.14, P3.2, P3.7, P3.9 and P3.11; and the deferred platform package of P1.34.6 with the manifest's item-34, item-28 and item-35 residuals;
     - DROPIN-REMAINING.md's P1 rows;
     - AGENTS.md (E7).
   - **S58.3 residuals and the audit.**
     - The manifest's 22 residuals, as amended by IR-2, IR-3, IR-4 and IR-9, are filed as P2/P3 rows or in the platform package.
     - The register's P2.42-P2.57 get their rows.
     - TWOWAY_COVERAGE_AUDIT.md is tagged.
     - The stale `test/fixtures/rejected_options.json` rows S51 did not own are fixed.
   - **S58.4 CHANGELOG consolidated.** The lists are Results that change, Changed behaviour, New, Requirements (Stata 19, the measured Python floor, the bokeh window), Security, and Fixed in WP-30. No marker remains: `grep -c '<!-- WP-30' CHANGELOG.md` prints 0.
   - **S58.5 release gates (G10; nothing is committed).** `make test`, `make test-dev`, `make cert` and `make gate` run once each, in that order, serialised through the queue (`test`, `test-dev`, `cert` and `gate` modes).
   - **S58.6** happens only if the release date must move: the release heading, `dash.pkg`'s Distribution-Date and the files the release pins.
   - **S58.7 release measurements:**
     - the saved page size with and without MathJax;
     - render times;
     - served memory and latency under the session cap;
     - the certification run's duration and its change from `wp30-cert-baseline.log`;
     - per-block times from `test_wp30_truth.cscript`'s `S<NN> start/end` lines.
   - **Then:**
     - `gitnexus detect-changes --scope compare --base-ref main --repo dash > <scratch>/wp30-detect-compare.txt`, and a re-index;
     - S02's path guard and S03's version pin are re-checked;
     - `git log --format=%B main..wp30-p1 | grep -Eic 'claude|anthropic'` prints 0, as does `git diff main..wp30-p1 -- BUGS.md CHANGELOG.md dash.sthlp dash_setup.sthlp | grep '^+' | grep -Eic 'claude|anthropic'`.

     S58 reports `git checkout main && git merge --no-ff wp30-p1` without running it (E8).

### Full-suite runs (project rules 4 and 11; the lock, the hook and the queue)

**Facts that bind the schedule:**

- **The lock** (`test/conftest.py:64`, `/tmp/dash-full-suite-<uid>.lock`) is per user and machine-wide. A second whole-suite run exits at once; the lock does not queue.
- **The hook** (`.claude/hooks/guard-full-suite.sh`, `full_run_in_progress` at :49) refuses a full launch while the lock is held, or while a full pytest or a `run_all_cscripts.do` Stata process runs. It refuses the third launch in a session unless the command carries `FULL_SUITE_RERUN=1` (`MAX_FREE_LAUNCHES = 2`, :27).
- **The queue** adds the machine-wide ordering that the lock lacks. It caps every run at 6 workers (12 CPUs on this machine) and runs certification and gate runs through the same lock, so no two full runs of any kind overlap.

**Rules:**

1. Every planned run goes through the queue (E1), including G0, each commit's run, each batch's G8, S05's matrix, S41's 3.10 leg, the certification runs and S58's gates.
2. A run is waited for and its log read. It is never relaunched to check on it. A launch the lock or the hook refuses is not a run, and records nothing.
3. A section never runs `make cert` or `run_all_cscripts.do`. Certification runs are the orchestrator's: step 0b, batch 1's G8 and S58.5. The one exception is S05's one floor certification run, through the queue (batch 2); it is not a release-gate leg (ratification row 25).
4. **Time.** No run has been measured at 6 workers yet. The first planned run (G0) records its wall time in `<scratch>/queue-times.txt`. At `-n auto` a clean run took 1:16-1:52 (22sep2026), so expect about 2-3 minutes at 6 workers: roughly 3.5-5 hours of serial suite time across WP-30, plus the certification runs.

**Schedule** (planned runs, not counting reruns after a red result; a red result adds at least two):

| When | Pytest full runs | Certification / gate runs |
|---|---|---|
| Step 0a (G0) | 1 | — |
| Step 0b | — | 1 cert (baseline) |
| Batch 0 | 2 (S01; G8) | — |
| Batch 1 | 3 (2 commits; G8) | 1 cert (after S03's sweep) |
| Batch 2 | 11 (4 commits: S04 1, S05 2, S06 1; G8; S05's 6 matrix runs) | 1 cert (S05's floor certification run) |
| Batches 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 16, 17 | 4 each (3 commits; G8): 48 | — |
| Batch 7 | 5 (4 commits: S19 2, S20 1, S21 1; G8) | — |
| Batch 14 | 6 (4 commits: S39 1, S40 1, S41 2; G8; S41's bokeh 3.10 leg) | — |
| Batch 15 | 5 (4 commits: S42 2, S43 1, S44 1; G8) | — |
| Batch 18 | 5 (4 commits: S51 2, S52 1, S53 1; G8) | — |
| Batch 19 | 5 (4 commits: S54 1, S55 1, S56 2; G8) | — |
| Batch 20 | 2 (S57; G8) | — |
| Batch 21 (S58) | 7 (before S58.1, S58.2, S58.3, S58.4 and S58.7; `make test` and `make test-dev` in S58.5); 8 if S58.6 | 1 cert + 1 gate (S58.5) |
| **Total** | **100** (101 with S58.6) | **4 cert + 1 gate** |

Batch 13 has two sections but three commits (S37 lands as two), so it is among the four-run batches.

### The cscript driver

A cscript is never handed to the wrapper directly. It runs through a two-line driver, the WP-29 form:

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "<script>.cscript" > <scratch>/run_<script>.do
WP30_ONLY=S<NN> /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch> <scratch>/run_<script>.do   # log: <scratch>/run_<script>.log
```

- `<repo>` is the worktree while a section runs, and the main checkout for the merger and S58. The cscripts load `../dash_parse.mata` and `../dash.ado` relative to `test/`, so the worktree's code is the code tested.
- Only `test_wp30_truth.cscript` reads `WP30_ONLY`; leave it unset to run every block.
- A cscript sets `global dash_nobrowser 1` itself, through `test/cert_helpers.do:51`.
- An extractor or probe do-file runs directly through the wrapper, and opens with `adopath ++ "<repo>/"` then `global dash_nobrowser 1` (E5).

### Merge rules within a batch

- **R1 cscripts and the truth script.**
  - **Ownership.**
    - Only S01 creates and registers a script: `test/test_wp30_truth.cscript`, as runner block `// 69.` after `// 68.` (`test/run_all_cscripts.do:1744`), in block 68's form (comment header, RUN, PASS, SKIP on rc 222, FAIL).
    - Only S01 moves the hygiene pins in `test/test_cscript_hygiene.py`: `len(_CSCRIPTS) == 67 → 68` (:294) and `len(names) == 49 → 50` (:313; the scaffold gates on `c(python_exec)` as `test_wp29_truth` does), each with its comment extended.
    - `len(with_probes) == 13` (:322) moves only if S05 (batch 2), S25 (batch 9) or S41 (batch 14) adds a captured `python:` import probe to a script.
    - S01 also adds `TestTheWp30TruthScript`, a copy of WP-29's reader (:874-975) with `_WP30_TRUTH`, `_W30_OPEN`, `_W30_CLOSE`, `_W30_MARK` and the `WP30_ONLY` gate lines.
    - `test/test_cert_verdict.py::test_the_real_runner_registers_every_script_in_test` then passes on its own.
  - **The scaffold**, in this order:
    - `cscript "WP-30 truth …"`;
    - the `c(python_exec)` skip;
    - `do "cert_helpers.do"`, `do "cert_svg.do"`;
    - S01's scaffold block;
    - 56 stub blocks, S02-S57 in section order. Each stub's body is two lines, `display as text "S<NN> start " c(current_date) " " c(current_time)` and the same with `end`;
    - the marker line;
    - `display "test_wp30_truth: ALL CHECKS PASSED"`.
  - **Writing into the script.**
    - A section writes its cases between its own start and end lines.
    - A second block of its own goes directly below its own end line, with the same `S<NN>`.
    - Its helper programs go directly above its own header line.
    - A section never writes inside another section's block.
  - **Area scripts.**
    - Refusal, message, return-code and setup checks join the existing script for their area, as one contiguous run at the end of its last case block.
    - An in-place flip edits only its named case.
    - Two sections of one batch that append to one script keep merge order.
    - At k.0 the merger derives the batch's table from the section files' `<files>` lists (`grep -o '<files>[^<]*</files>' .ultraplan/wp30/section-*.md`) and writes it to `<scratch>/batch-<k>-scripts.txt`.
    - Known from the manifest: `test_env_guards.cscript` (S03 in batch 1, S25 in batch 9) and the setup scripts (`test_setup_honesty`, `test_setup_python_gate`: S03, S05, S25 and S41, in batches 1, 2, 9 and 14). Each of these is in a different batch.
  - **Case ids** follow the manifest table (A143).
- **R2 served copy lists and maps.**
  - **What each section adds.** Its own names, at its own anchor below, never re-ordering an existing entry (X.1). `_glyph_layer_lines` skips any def that `_shared_stat_lines` already emits (`_emitted_names`, :33074). Methods of `OptionTranslator` (class at 5098), `SchemeParser` (5646) and `GlyphMapper` (7879) travel with their class (the class loop at 33436) and need no entry.
  - **Registry tests after every landing that touches them, and in G8:**
    - `test_function_test_map.py`;
    - `test_program_coverage_map.py`;
    - `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, with S01's `test_every_listed_name_exists`;
    - `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` (:1194);
    - `test_cscript_hygiene.py`;
    - `test_tracking_documents.py`.
  - **Anchors at `c96facd`.** "+" adds after the anchor; "−" removes. A name already listed that a section edits in place needs no change. No two sections of one batch share an anchor (checked against the batches); a later batch's names go after the earlier batch's names at the same anchor.

  | Section | Constants tuple (dash_render.py:32884-33039) | Functions tuple (33077-33425) | `_shared_stat_lines` (def 33485; function tuple 33536-33590) | Not copied |
  |---|---|---|---|---|
  | S01-S03, S05, S07, S11, S12, S20, S22, S51 | — | — | — | No copy-list change: runners, Stata, scheme files, or launcher-only code (S12's `_dash_launch_app` `--show` path) |
  | S04 | + the meta's own base constant (A99) after `"_DASH_CSP_SERVED", "_DASH_SECURITY_HEADERS",` (32955) | + any nonce helper after `"_dash_csp_meta", "_dash_served_template",` (33289) | — | The saved page's hash builder (saved only); `_dash_open_page` (opener) |
  | S06 | — | — | — | `_dash_smcl_escape`, `_dash_emit_note` and `_dash_note_scope` (the renderer's `__main__`; S23 copies the first two) |
  | S08 | — | — (`_textbox_size` at 33360 changes in place) | — | `resolve_size` and the `*#` parser (OptionTranslator methods); `_mlabel_gap_px` (GlyphMapper) |
  | S09 | — | + `"_dash_finish_graph_text"` and its helpers after `"_dash_inert_tex",` (33278) | — | — |
  | S10 | + the sub-option tables after `"_DASH_TEXTBOX_DEFAULTS", "_DASH_SCALE_SUBOPTS",` (32934) | + `"_dash_subopt_canon"` after `"_dash_subopt_name",` (33370) | — | — |
  | S13 | — | — | — | `_LWIDTH_MAP` (OptionTranslator, 5324) and `SchemeParser._lwidth` travel with their classes |
  | S14 | — | − `"_dash_copy_redraw_geometry",` (33332; deleted with the function, register P1.17.3/A61) | — | `GlyphMapper._tag_spacing` (10293) is deleted with its callers |
  | S15 | — | + `"_dash_textbox_place"` after `"_dash_textbox_or_default",` (33372) | — | — |
  | S16 | — | — | — | `_blend_intensity` (8293) and `_scheme_alpha` (9727) are GlyphMapper methods |
  | S17 | — | + any colour-key helper after `"_dash_colorvar_domain", "_dash_colorvar_field",` (33368) | — | — |
  | S18 | — | + `"_dash_axis_tick_formats"` after `"_dash_fmt", "_dash_fmt_text",` (33213) | — | — |
  | S19 | + `"_DASH_FIT_KEYS"` (new) after `"_DASH_FIT_TYPES", "_DASH_CI_TYPES",` (32895; commit 1) | + `"_dash_layer_series"` after `"_dash_legend_key", "_dash_legend_entries",` (33175; commit 1); + `"_dash_axis_default_titles"` after `"_dash_axis_labels",` (33228; commit 2) | — | — |
  | S21 | + `"_DASH_DEFAULT_TAG", "_DASH_MARGIN_RS", "_DASH_BY_GMETRIC", "_DASH_AXIS_FINISH_JS", "_DASH_AXIS_ZOOM_JS"` after `"_DASH_TICK_EVERY_JS",` (32943) | + `"_dash_default_ticker", "_dash_plot_margin", "_dash_axis_plan", "_dash_layer_extent", "_dash_tag_hull_roles", "_dash_refinish_axes"` after `"_dash_count_of", "_dash_finish_count_ticks",` (33251; `_dash_refinish_axes` stays last, so later finishers' "after S21's names" anchor holds; TR-21.14) | — | — |
  | S23 | — | + `"_dash_smcl_escape", "_dash_emit_note"` and the app's note hook after `"_dash_note_empty_layer",` (33137) | — | The trial's driver (build time); `_dash_launch_app`'s relay (launcher only) |
  | S24, S30, S32, S33, S34, S36 | — | — | — | Mapper, OptionTranslator and SchemeParser methods; S34's per-graph property dicts are data the builder writes, never paths |
  | S25 | — | — | — | `_dash_dep_fail` and `_DASH_MIN_PYTHON` are written into the generated header ahead of the imports by `_generate_app_source`, not through a copy list |
  | S26 | — | + any helper after `"_dash_function_points",` (33126) | — | — |
  | S27 | — | + `"_dash_finish_auto_bases"` after S21's `"_dash_refinish_axes"` | — | — |
  | S28 | — | + any by()-title helper after `"_dash_facet_label", "_dash_stata_date_text",` (33201) | — | — |
  | S29 | + the graph-text tables after `"_DASH_ASCII_BLANKS",` (33001) | + `"_dash_graph_text"` and its helpers after S09's names | — | — |
  | S31 | + `"_DASH_SCALE_LOOK_SUBOPTS",` after `"_DASH_SCALE2_SUBOPTS",` (32938) | + `"_dash_tick_geometry", "_dash_tick_position", "_dash_tick_look", "_dash_scale_look", "_dash_apply_scale_look", "_dash_axis_alternate"` after `"_dash_apply_axis_options",` (33243); in place: `_parse_axis_angle` 33223, `_dash_parse_axis_spec` 33230, `_dash_scale_spec` 33375; `_DASH_ANGLESTYLES` 32929 in place | — | — |
  | S43, S55 | — | — (in place: `_textbox_color` 33360, `_resolve_kpi_color` 33393, `_dash_refline_draw` 33383 for S43; `_dash_build_hover` 33171 for S55) | — (`_dash_graph_color`, 33542: no region caller after S38; S43 edits it only if 43-09's grep finds a colour-site caller, otherwise S58 removes it with its entry) | — |
  | S35 | + `"_DASH_DATE_UNITS_TAG", "_DASH_DATE_UNITS_JS"` after `"_STATA_MS_MAX", "_STATA_EPOCH_UNIX_MS",` (33024; D-35h) | + the date-transform helpers after `"_dash_axis_date_kind", "_dash_axis_positions",` (33105) | — | — |
  | S37 | — | + the mlabvposition helpers after `"_dash_mlabel_names", "_dash_option_columns",` (33356) | — | — |
  | S38 | — | − `"_extract_region_lwidth"` (33388), `"_extract_region_color"` and `"_extract_region_lcolor"` (33391-33392); + the region reader in their place | — | — |
  | S39 | — | + the renderer's numlist fallback after `"_dash_refline_draw",` (33383) | — | `_dash_line_expand` (dash.ado) |
  | S40 | — | + `"_dash_join_glyph"` after `"_dash_sort_cols_named", "_dash_take_sort_columns",` (33093) | — | — |
  | S41 | + the internals list and window constants after `"_DASH_LINK_UNWRITTEN",` (32968) | + the guard helpers after `"_dash_harden_origin_check",` (33299) | — | dash_setup_lib.py's gate |
  | S42 | + the operator-column constants after `"_DASH_QUAL_PREFIX", "_DASH_QUAL_NAME_RE",` (32979) | + the operator-column helpers after `"_dash_qual_cols_named", "_dash_take_qual_columns",` (33153) | — | — |
  | S44 | + the date-ticker constants after `"_DASH_TS_GRIDS", "_DASH_TS_YEARS", "_DASH_TS_LIMITS",` (32998) | + the date-ticker helpers after S27's names (S21's anchor) | — | — |
  | S45 | — | + the draw-as helper, if module-level, after `"_dash_glyph_dispatch",` (33130) | — | — |
  | S46 | + the session-cap and idle constants after `"_DASH_EVENT_RATE", "_DASH_EVENT_BURST",` (32950) | + the cap and idle helpers after `"_dash_limits", "_dash_limit_hint",` (33302) | + the estimator memo as the new last entry, after `_stata_if_to_pandas` (33590) | The launcher flags (`__main__` argparse, `_dash_launch_app`) |
  | S47 | — | + the inner-box helper after S44's names (S21's anchor) | — | — |
  | S48 | — | + the by()-grid helpers after `"_dash_by_rescale",` (33200) | — | — |
  | S49 | — | + the transposition helper after `"_dash_add_pc_glyph", "_dash_note_no_second_y",` (33132) | — | — |
  | S50 | — | + the extent helper after S39's names (after `"_dash_refline_draw",`, 33383) | — | — |
  | S52 | — | + the `add` union helper after S47's names (S21's anchor) | — | — |
  | S53 | — | + the by() legend and axis helpers after `"_dash_reflow",` (33354) | — | — |
  | S54 | + `"_DASH_SVG_SAVE_JS", "_DASH_SVG_SAVE_ICON",` after `"_DASH_SAVE_NAME_RE",` (33028; the continuation of `"_DASH_FIGURE_TOOLS", "_DASH_SAVE_NAME",` at 33027) | — (`_dash_name_save`, 33352, in place) | — | — |
  | S56 | + the added-text defaults after `"_DASH_TEXTBOX_HONOURED",` (32933) | + `"_dash_added_text"` after `"_dash_text_annotations", "_dash_scale_spec",` (33375) | — | — |
  | S57 | — | — | — | The worker lives in the generated move path (`_generate_app_source`) |

  - **Maps** (A148): `test/function_test_map.py` and `test/program_coverage_map.py`. Entries go under the section's own anchor, alphabetical by key. A Mata function also gets its `_needed` entry in the same commit (X.5/A137). Adjacent anchors conflict in context only: the merger keeps every entry, by hand.
- **R3 dash.sthlp and dash_setup.sthlp** (A155). A section edits only the paragraphs its scope names. Where two sections of one batch touch one paragraph, the later in merge order rewrites the sentence and keeps the earlier one's text. Paragraph owners by help title, with the line ranges at `c96facd`:

  | Help title (dash.sthlp) | Lines | Sections (batch) |
  |---|---|---|
  | Jump list | 3-21 | S22 (8: the Exporting and Stored results jump entries) |
  | Syntax, Description | 45-207 | S12 (4), S22 (8), S42 (15) |
  | Plot types | 208-443 | S14 (5), S26 (9: :413-418), S27 (9), S40 (14), S42 (15), S49 (17), S56 (19) |
  | Differences from twoway | 444-814 | S06 (2: :594-604), S08 (3: :690-691), S10 (4: :548-556, :615-632, :780-786), S11 (4: Stylelists, :786-788; S10 and S11 share :780-788, S10 first), S12 (4: :452-470), S13 (5: the bounds sentence :690-693 and the every-type sentence :744-752), S16 (6: the fill-intensity clause :660-664), S19 (7: :635-637, :809-811), S20 (7: :740-742), S31 (11: :784-788), S56 (19: the example at :598-599 in S06's paragraph; R3 exception) |
  | Subcommands | 815-915 | S12 (4), S46 (16: `maxsessions()`, `idletimeout()`) |
  | Dashboard Options | 916-980 | S04 (2: creates the `saving()` character-rule paragraph, with Windows' written-not-opened rule), S12 (4: rewrites that paragraph to the final rule; the browser rule under batch and `set graphics off`, :966-975), S22 (8: image extensions in `saving()`) |
  | Exporting; The toolbar | 981-1034; 1184-1235 | S21 (7: the Reset row's one sentence, :1203-1204), S22 (8: Stored results, Exporting text), S54 (19: the toolbar row, the "Saving an image" sentence and one sentence in S22's "Images" paragraph; R3 exception) |
  | Linking and Brushing | 1147-1183 | S08 (3: one sentence on the brushed copies following the glyph, ratification row 27) |
  | Server Mode; Temporary files and privacy | 1483-1806; 1807-1888 | S04 (2: what the CSP does and does not protect), S09 (3: one sentence on canvas text and TeX, :1721-1725), S23 (8), S41 (14), S46 (16), S54 (19: the "Toolbar, save as SVG" row of the mode table, :1505; R3 exception), S57 (20: the "Recomputation." paragraph, :1773-1780) |
  | Resource limits | 1889-2002 | S39 (14: `reflines`), S46 (16: Limits), S56 (19: `added_text`) |
  | Faceting with by() | 2055-2137 | S21 (7: the zoom/filter sentence, :2084-2086), S28 (10: :2070, :2096), S48 (17), S53 (18) |
  | Marker Label Options | 2138-2238 | S08 (3), S33 (11), S37 (13) |
  | Statistical Layer Options | 2239-2612 | S16 (6: the CI band's intensity sentence, :2583-2584), S19 (7), S32 (11: :2282), S45 (16) |
  | Region Styling Options | 2688-2734 | S38 (13: :2717-2721, IR-2), S47 (16) |
  | Axis and Display Options | 2735-3075 | S10 (4), S15 (5), S17 (6: the `zlab:el()` synopt :2753 and the Tooltips sentences :3057-3062), S18 (6), S19 (7: the second-axis title sentence, :3010-3013), S21 (7: Axis labels :2811, :2852), S31 (11), S35 (12: :2909), S39 (14), S44 (15), S50 (17), S51 (18), S52 (18) |
  | Mapping a Variable to Colour | 3076-3178 | S08 (3: :3155-3162), S17 (6), S33 (11) |
  | Figure proportions | 3179-3227 | S48 (17) |
  | Marker and Transparency Options | 3228-3290 | S13 (5), S16 (6), S20 (7: :3233), S30 (10), S43 (15) |
  | Stata scheme support | 3291-3600 | S07 (3: "twenty" at :3300, :3501, :3505, :3573 → twenty-six), S08 (3: the Units paragraph, :3424-3434), S10 (4: :3352-3353, :3414-3415), S15 (5), S16 (6: one sentence, :3369-3372), S24 (8: :3363-3365), S33 (11), S34 (12: the remedy), S36 (12), S37 (13: the directive-count sentence of "What the shipped files are"). That sentence's numbers belong to the R10 directive-count movers (S15, S21 if red, S24, S33, S36, S37, S50 if red, S53), each in its own batch |
  | Unsupported Stata twoway options | 3601-3779 | the pending-list movers (R10): S32 (11), S36 (12: the "Dot and marker back-line styles" paragraph), S37 (13), S45 (16), S49 (17), S51 (18), S56 (19); also S31 (11: :3757-3760) and S40 (14: the "Not drawn" sentences :3728-3735, which keep naming the residuals) |
  | Dependencies (and dash_setup.sthlp's) | 3780-3818 | S03 (1), S05 (2), S25 (9), S41 (14): one per batch |

  Batches where two sections share a title edit different paragraphs or lines, and the later in merge order keeps the earlier one's text: batch 3 (S07 and S08 in Stata scheme support), batch 4 (S10, S11 and S12 in Differences; S10 and S11 share :780-788, S10 first), batch 6 (S17 and S18 in Axis and Display), batch 7 (S19 and S20 in Differences; S19 and S21 in Axis and Display), batch 9 (S26 and S27 in Plot types), batch 11 (S31 and S32 in Unsupported), batch 12 (S34 and S36 in scheme support), batch 18 (S51 and S52 in Axis and Display, S52 landing second). The R3 exceptions (S54 in S22's "Images" paragraph and the mode table, S56 in S06's paragraph) are each the only editor of those lines in their batch. A new "Text in graphs" paragraph (S29) goes under Axis and Display Options, after the axis-title paragraphs.
- **R4 CHANGELOG.md.**
  - **Placement.** S01 places the 84 markers (A147) in the release `## 0.1.0, 02oct2026 (release candidate)`, in entry order within each list:
    - a `**WP-30 (drop-in P1, 03oct2026)**` group at the end of `### Results that change` (:10), after WP-29's last line and before `### Security` (:315);
    - the end of `### Security`, before `### New` (:411);
    - the end of `### New`, before `### Fixed` (:452);
    - the end of `### Changed behaviour (may need your do-files changed)` (:513), before `### Removed` (:598);
    - the end of `### Requirements` (:607);
    - a new `### Fixed in WP-30`, with a one-line introduction, directly above `### Fixed in WP-29` (:653).
  - **Replacement.** A closing commit replaces only its own markers, in place, with lines ending `(WP-30, <entry>)`. A section that needs another list edits its own `WP30_LISTS` row and adds or removes its own line in the same commit (S20 adds Results that change for P1.1b; S34 adds Changed behaviour for P1.25b; A147).
  - **In-place correction.** CHANGELOG.md:522 (the `msize(abc)` note) is corrected in place by S08 (manifest N2).
- **R5 BUGS.md and `test/test_tracking_documents.py`.**
  - A section edits only its own entry, in place, and deletes only its own `WP30_OPEN` key line. The keys sit one per line in entry order, so adjacent deletions conflict in context only, and the merger applies both by hand.
  - The extra entries are A146's. GAPS2 Tracked lines are S58's.
- **R6 dash.ado, dash_setup.ado and dash_parse.mata.**
  - No two sections of one batch add the same option key or the same Mata function.
  - `_dash_require_mata`'s `_needed` list is data: sections of one batch add names on separate continuation lines (batch 2: S04, S06; batch 4: S10, S11, S12), and the merger keeps every name (A139's recorded exceptions).
  - In batch 6, S18 is the one editor of `_dash_option_rules` and `_dash_validate_value`; S17 edits no Stata file.
  - Every program written after S03 opens with `version 19`.
  - The guard order is A154's.
  - The export-block paragraphs of `_dash_render_immediate`, `_dash_prepare_spec` and `_dash_build` are separate paragraphs owned by S12, S22, S34 and S42.
  - A Mata function goes in the part of `dash_parse.mata` its section names. The header index (`dash_parse.mata:1-303`) gains one entry per new function, in place.
  - If ratification item 26 stands, an option is added in dash.ado's five option-surface places by hand (IR-7).
- **R7 fixtures and scheme files.**
  - No hand patches. Every new fixture carries the D12 `_meta` stamp (including `stata_version`), is named by the test that reads it, and is added with `git add -f`. `test/test_fixtures_are_committed.py` is not edited.
  - A new extractor copies S02's path-free form (`DASH_REPO`, A130) and is never run by another section.
  - Shared fixtures: `saving_chars_truth.json` (S04 creates it, S12 reads it), `scheme_truth.json` and the 26 scheme files (the regenerators, A152) and `format_truth.json` (S18).
  - A conflict in a generated file is never resolved by hand: the merger re-runs that section's extractor on the merged tree and records the run in the merge log.
- **R8 parity corpus** (`test/test_mode_parity.py`).
  - Sections append `CORPUS` cases.
  - A `_MUST_WARN` entry is edited only by the section whose fix silences it. S23 restores the own-if entries under M6.
  - `ALLOWED` is never edited: a saved/served difference is a defect of the section that caused it.
  - Notes the served app must print are decided at build time or relayed by S23.
  - A saved-vs-served axis assertion follows S21's D-21e2: a layer the saved page leaves unfiltered stays in the saved hull as drawn, so saved equals served only where both draw the same layers (S27, S35, S44, S47, S50 and S52 adopt it).
- **R9 pinned tests.** A test that pins today's wrong behaviour is flipped in the fix commit with a `Flipped:` line, never deleted. A research note's list of red-first tests is re-measured by the section, not trusted. Flips named by the manifest and register:
  - S02: `test_cert_verdict`, `test_release_verdict`/gate and `test_measure_stata_coverage`'s literal-command pins.
  - S09: TestTextSinks' TeX rows.
  - S11: `test_abbreviations.py`'s count pin.
  - S12: P2-80 and PV-04/05/14.
  - S15: `test_server.py:4001`; `test_help_claims_8.py::TestTheShippedFiles::test_no_directive_for_what_dash_does_not_draw` (its `tick(?!_label)` pattern) and the directive-count pin (R10).
  - S17: `test_date_range`'s colour-scale rows and `histogram_gets_the_bin_tooltip`.
  - S20: HC2-18b and its `test_help_claims_2.py` mirror.
  - S24: TestTheSchemeOpacityStopsWhereTheHelpSays, `test_80_to_140_directives` (renamed `test_the_directive_count_is_what_the_help_says`; R10) and TestMarkColourIsForMarkers.
  - S30: `test_options.py:284-299`, `test_security_surface`'s unreadable background and HC2-16p.
  - S38: `test_option_validation.py:1089-1094`.
  - S36: the directive-count pin and three sibling `TestTheShippedFiles` pins its regeneration turns red (S36 E12).
  - S40: `test_unsupported_report_is_true.py:95/99` and HC8-02's cmissing, connect and sort; `:137` (recast) and HC8-02's recast are S45's (Q-40.1).
  - S45: `test_unsupported_report_is_true.py:137` and HC8-02's recast.
  - S53: `test_no_directive_for_what_dash_does_not_draw` (exempts its by() group) and the directive-count pin.
  - S54: `_assert_nine_tools`.
- **R10 combined pins and counts** (help and test counts combined). A section that moves a pin measures the new value on its worktree and writes it with a trailing comment `# <old> -> <new>: <entry> <why>`. On a conflict, or when two commits of one batch each move a value, the merger re-derives the value by running that pin's test on the merged tree after the later landing, writes it, and names it in the merge log. The expected movers, from the manifest's scopes:

  | Pin at `c96facd` | Value | Movers (batch) |
  |---|---|---|
  | `test_cscript_hygiene.py:294` / `:313` / `:322` | 67 / 49 / 13 | S01 → 68 / 50; `:322` only as R1 says |
  | `test_unsupported_report_is_true.py:240` plot pending | 48 | S32 (11), S36 (12, +3), S37 (13), S45 (16), S49 (17), S51 (18), S56 (19). S40 leaves its pending lines (the sort precedent), so it does not move this pin |
  | `test_unsupported_report_is_true.py:241` graph pending | 23 | S51 (18), S56 (19) |
  | `test_unsupported_report_is_true.py:607` declared plot | 169 | S18 (6, +2: `xvarformat()`/`yvarformat()`), S32 (11), S36 (12, +3), S40 (14, +1: `CMISSINGS`), S45 (16), S49 (17, re-measured), S51 (18, +7), S56 (19, +1 only if measured). S37 declares no option and does not move it |
  | `test_unsupported_report_is_true.py:608` declared graph | 72 | S51 (18), S56 (19) |
  | `test_help_claims_8.py::TestTheShippedFiles::test_80_to_140_directives` (renamed `test_the_directive_count_is_what_the_help_says` by S24), with dash.sthlp's directive-count sentence in "What the shipped files are" | 80-140 | S15 (5, its ~24 chrome directives pass 140 at s2gmanual's 139), S21 (7, only if its keys cross the bound), S24 (8, renames and re-measures), S33 (11), S36 (12), S37 (13, commit 2), S50 (17, only if red), S53 (18). The directive-count chain runs S15 → S21 → S24 → S33 → S36 → S37 → S50/S53, one mover per batch; any other regenerator re-measures it on its worktree |
  | `test_help_claims_8.py::TestTheShippedFiles::test_no_directive_for_what_dash_does_not_draw` | pattern | S15 (5: new tick keys), S36 (12), S53 (18: exempts its by() group) |
  | `test_help_conformance.py::TestTheParsersFoundSomething::test_the_entry_parser_cuts_the_help_into_entries` (definition entries) | 339 | S07 (3, +6), and every later section that adds a `{synopt}`/`{phang}` help entry; the merger re-derives it on the merged tree |
  | `test_help_claims_8.py`'s Unsupported equality pin, with dash.sthlp's Unsupported section (3601-3779) | — | every pending-list mover, in the same commit |
  | The scheme count: `test_scheme_fidelity.py:119` `EXPECTED_SCHEMES`, `SchemeParser._BUILTIN_NAMES` (dash_render.py:5704), `_dash_shipped_schemes`, `dash.pkg`, dash.sthlp's "twenty" | 20 | S07 → 26 |
  | `test_varlist_expansion.py` `_SINGLE_Y_BASELINE_SHA256` (the single-y page digest, :393-403) | digest | every section whose commit changes the single-y page. These are expected among S04, S08, S09, S13, S15, S16, S18, S21, S24, S30 and S47 (the axis plan's margin becomes a pair), so two can share a batch (batches 3, 5 and 6). The merger re-derives the digest on the merged tree after each such landing, and each commit message says why. |

  The pending-list, declared-count and directive-count movers are each in a different batch, so those pins conflict only if a section moves one unexpectedly.
- **R11 axis finishers** (A153). Only the batch's one finisher editor touches `_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS`, `_dash_default_ticker` or `_dash_plot_margin`: S21 (7), S27 (9), S35 (12), S44 (15), S47 (16), S50 (17) and S52 (18). The saved re-finish is appended to `_FILTER_JS` by the module-level statement directly after `_DASH_AXIS_FINISH_JS`'s assignment (A153; never inside `_FILTER_JS`'s literal) and reads its per-figure plans from the CustomJS args of `build_dropdown`/`build_slider`/`build_range`. A finisher change keeps A9's budgets (ratification item 3).
- **R12 one-editor symbols.** One section per batch edits each of `_generate_app_source`, `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets` and the four appliers (`_apply_marker_opts`, `_apply_line_opts`, `_apply_mlabel_opts`, `_apply_fill_opts`), as the batch subsections name them. The `_make_figure_body` editors are S18, S21, S23, S35, S38, S40, S47 (only if 47-08 finds it must), S49 and S56. The `_generate_app_source` editors include S14 (5, deletion only) and S35 (12), with S34's four one-line edits in batch 12 as the one R12 exception (ratification row 38). A section that finds it must edit one of these outside its listed scope stops and reports before editing.
- **R13 GitNexus** (E4). Impact runs at the batch base, `detect-changes` runs at each landing, and the index is rebuilt after each landing, all in the main checkout only. An index's stale notice inside a worktree is ignored.

## Verification gates

| Gate | When | Command / check | Pass condition |
|---|---|---|---|
| G0 | Step 0a | One full run through the queue on the staged plan | Green. `git show --name-only --format= HEAD` lists only `.ultraplan/wp30/` files (all of them). The message passes G7. |
| G1 red-first | Each commit's cycle, before the fix | The commit's new tests at the cycle's base | Every new regression test FAILS, and the failure text is saved. Guard tests are listed separately. |
| G2 green | Each commit, before committing | The changed test files; the section's cscripts through the driver with `WP30_ONLY=S<NN>`; `git -C <wt> merge --no-edit main`; one full run through the queue | 0 failed. Every case of the section's truth block prints PASS. No new SKIP (a skip is not a pass). Flaky tests are handled by E6. |
| G3 parity | Each section that changes a drawing | `python3 -m pytest test/test_mode_parity.py -q -n0` | Green, with the section's CORPUS cases. Both modes draw the same, before and after a filter move. |
| G4 served guards | Each section that adds a module name | `TestTheServedAppCarriesEveryName` (with `test_every_listed_name_exists`) and `TestTheServedAppDefinesEveryNameItReads` | Green |
| G5 tracking | Each commit | `python3 -m pytest test/test_tracking_documents.py -q -n0` | Green: a closed entry names tests that exist, and its key and markers are gone. A first commit of a two-commit section leaves all three in place. |
| G6 scope | Each commit: in the worktree, the name check; at landing, both checks | `git diff --cached --name-status`; `gitnexus detect-changes --scope all --repo dash` (main checkout only) | Only the section's files and symbols, and the landed names equal the worktree commit's. No `CLAUDE.md`, `.gitignore`, `AGENTS.md` (outside E7's S58 rule), `.gitnexus/`, `.ultraplan/wp30/`, scratch file or `*.html`. |
| G7 message | Each commit | `grep -Eic 'claude\|anthropic'` on the message, before and after committing | 0 |
| G8 batch | After each batch's last landing (batch 0 included) | The full suite once through the queue; the registry tests (R2); `test_wp30_truth.cscript` with all blocks and every area cscript the batch touched, through the driver; `gitnexus status` | Green, with the index at HEAD. Batch 1 also runs `make cert` (green, timed). |
| G9 security | S04, S06, S09, S12, S23, S29, S34, S38, S39, S41, S46, S51, S54, S55, S56, S57 | The section's security tests: the CSP browser test, SMCL escaping of notes, TeX payloads, path rules and the launch line, redacted relays, linear-time hostile SMCL, the scheme-path guards, CSS-sanitised colours, the `reflines`/`added_text` limits, internals that fail closed, session caps, no `_stata()` on user text, the SVG action under CSP, no property name read from JSON, thread safety | Green, and the threat each closes is named in its commit body |
| G10 release | S58.5 | `make test`, `make test-dev`, `make cert` (timed against `wp30-cert-baseline.log`) and `make gate` (no floor-Python leg: ratification row 25), each once, through the queue | All green. The certification time and its change are recorded in S58.7. |
| G11 exit | S58 | `PLAN.md`'s exit gates | Every gate met. 3 open BUGS.md entries (P2.49 not filed, ratification row 27). No `<!-- WP-30` marker left. `WP30_OPEN` empty. |

## Risk register summary

| Id | Risk | Where | Mitigation |
|---|---|---|---|
| RK-1 | The red ticker and margin: five CRITICAL symbols, and a re-finish in both modes after every move | S21 (batch 7) | It is the batch's only finisher, template and figure-body editor, and it lands last, with light partners. Impact runs at the base, with a warning before each CRITICAL edit. Timed budgets (A9) and the 100-panel bound are pinned. It does not land without the after-move re-finish. |
| RK-2 | The red date ticker: about 350 lines of calendar JS that must agree with the Python model | S44 (batch 15) | Parity over the fixture's 12,000 answers, with the floors pinned (A8). No BokehJS view internals. Date path only; lands last. |
| RK-3 | The red served worker: thread safety of the final move path | S57 (batch 20) | Alone, after every served section. A thread-safety audit, Bokeh's rules verified across S41's window, and latency measured at N=100k. |
| RK-4 | Every dashboard's look changes (M1): sizes, chrome, opacity, ticks, margins | S08, S13, S15, S16, S21, S24, S30, S43 | CHANGELOG "Results that change" lines with before and after values. G3 parity. The page digest is re-derived on merged trees (R10). Ratification items 1-3 and 10. |
| RK-5 | The version sweep changes the language level of 91 programs | S03 (batch 1) | One commit; a full certification run in batch 1's G8; the callerver pin; and `test_version_floor.py`. |
| RK-6 | Dropping `'unsafe-inline'` can blank a page, and later JS must run under hashes or a nonce | S04, then S21, S35, S53, S54 | S04's headless-Chrome test in both modes. A98 fails closed on an unhashed script. S35 and S54 re-run the browser check. Ratification item 17. |
| RK-7 | Twelve scheme regenerations | A152 | One per batch, landing last (S07 and S37 excepted, with reasons). Never hand-patched; a conflict means a re-run (R7). |
| RK-8 | CRITICAL symbols edited by many sections: `_make_figure_body` (9 editors), `_apply_marker_opts`, `_apply_mlabel_opts`, `_apply_line_opts`, `_build_filter_widgets`, `_build_sources_and_figures` | R12 | One editor per batch, impact at each base, and the empty-option identity tests (S08, S13, S32). |
| RK-9 | A name missing from a served copy list fails only on the served page | R2 | `test_every_listed_name_exists` (A149), G4 and distinct anchors. |
| RK-10 | Notes and their test needles migrate twice | S06 | S06 lands in batch 2, last in its batch (A150). |
| RK-11 | Downloads and interpreter links | S05, S41 | Scratch venvs only (M10). No `permanently` link, and `stata19.rc` is checked after each run (E12). |
| RK-12 | Machine contention: 100 pytest runs and 4 certification runs | All | The queue at 6 CPUs (E1). Runs are never relaunched to check on them, and flaky tests get one isolated re-run (E6). |
| RK-13 | 44 ratification rows (28 rulings, P-1, 15 section questions); closed: all answered 06oct2026 | Batch 1 onward | The answers are applied to the plan ("(ratification 06oct2026)" in each changed section's Review amendments); step 0f still copies the record and checks it holds no `pending` (A151). Row 26 was ratified, so IR-7's strike plan is not used; P-1 (row 29) lands before step 0a. |
| RK-14 | The manifest and the register disagree in places | IR-1..IR-17 | The index's reconciliations bind every section file, and the section files' Review amendments quote the IR rows that apply. |

Package-level risks, mitigations and the exit gates are in `PLAN.md`. This summary covers what the batch plan itself must control.
