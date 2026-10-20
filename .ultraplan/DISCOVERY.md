# UltraPlan Discovery: dash -- close the drop-in audit of 19oct2026 (WP-33)

> Generated: 2026-10-20
> Phase: 1/6 - UNDERSTAND
> Mode: focused. The audit (`review/DROPIN-AUDIT-19oct2026.md`) and the
> maintainer's rulings D40/D41 are the discovery record; questions cover only
> what they leave open.

---

## Project Idea

Plan the work that makes dash's drop-in-replacement-for-twoway claim true, as
measured by the drop-in audit of 19oct2026 (s3-bugs `7dced3a`; 21 area
auditors with adversarial verifiers; 403 verified findings deduplicated into 17
work packages). The maintainer's rulings D40 and D41 (20oct2026, recorded in
the audit's decisions section and in
`.ultraplan-archive-20261020/review/DECISIONS.md`) are binding:

- heatmap and sunflower are not twoway plot types; never listed as gaps.
- P13 (verification corpus, README gallery) is first; then 1, 11, 2, 12, 3,
  4, 5, 6-10, 14-17.
- P1: resolve all ten items; never a 0 px plot; verify ts operators in
  twoway before L./D. work; the zero label is 0.
- P2: use whichever Python Stata finds or the user sets.
- P3: resolved by help documentation (a dashboard is not a Stata graph).
- P5: document every observation cap in the help.
- P6-P10: resolve where Bokeh supports it.
- P11: compatible with twoway (accept/refuse as twoway, its rc and words).
- P12: one Stata-side zero-observation check for all types before Python;
  document where twoway differs.
- P14-P17: resolve.

The previous plan (WP-31, WP-32; landed) is archived to
`.ultraplan-archive-20261020/`. `.ultraplan/handoff/` stays because
`test_tracking_documents.py` reads `handoff/DROPIN-REMAINING.md`.

---

## Codebase Detection

**Codebase found:** Yes -- mature Stata package at `090d928` (s3-bugs = main).

- **Stack:** `dash.ado` 13,952 lines, `dash_parse.mata` 12,499,
  `dash_render.py` 73,586, `dash_setup.ado` 1,256, `dash_setup_lib.py` 1,133.
  Bokeh 3.8 (make test) / 3.9 (make test-all), pandas, numpy, Python 3.11+,
  StataNow 19.5 console on macOS arm64. One glyph layer shared by the saved page and
  the served app; the saved page's moves are JavaScript twins.
- **Tests:** 414 pytest modules, 69 `.cscript` scripts, 134 JSON truth
  fixtures from 126 `scripts/extract_*_truth.do`; headless Chrome via
  `test/responsive_probe.find_chrome()` (DevTools protocol, no Playwright);
  node harness for the page JS; mode-parity guard. Batch gate `make test-all`
  takes about 40 minutes (CLAUDE.md target: 5).
- **Conventions (WP-29..WP-32):** a register with a "Tracked:" line per row
  read by `test_tracking_documents.py`; one BUGS.md entry per item, closed in
  place; per-WP truth cscript with a block per section; worktree agents merged
  by cherry-pick (`../dash-wt/_tools/picks.sh`); three Stata slots
  (`scripts/stata_slot.sh`); full suite only at batch end; commit messages
  never name the tooling.
- **Corpus available locally:** twoway help files (46 `twoway_*.sthlp`, about
  128 example commands, 27 `gr_example2` named examples in the twoway files,
  97 across all help), `docs/g.pdf`; `gr_example` loads data by `sysuse`,
  `webuse` for the rest.

---

## Discovery Q&A

## Category 1: Core Requirements

### Q1: Which audit items should the plan cover?
- Options: all 17 packages (recommended); only items D40/D41 ruled on; P13 in full now, the rest as outlines.
- **Answer:** all 17 packages, every deduplicated item, including those D40 left without a ruling; each is fixed, or documented where its ruling says documenting resolves it.

### Q2: Plan structure?
- Options: one WP-33 in the D40 order (recommended); one WP per package; WP-33 + WP-34.
- **Answer:** one work package per audit package (seventeen WPs), each with its own register and closeout.

### Q3: Definition of done for the whole plan?
- **Answer:** every item closed with a BUGS entry and a pinning test (or documented as its ruling allows); `make test-all` green; the P13 corpus re-run and the README gallery regenerated at the final closeout.

### Q4: P4's remaining items (no separate ruling)?
- **Answer:** carried under the P11 ruling: draw matamatrix() plots; accept `(scatter ..) line ..` and an option-less `||` inside a group; draw the empty graph with no axes and refuse its axis options as twoway does.

### Q5 (follow-up to Q2): WP numbering and location?
- **Answer:** WP-33..WP-49 in the D40 order, all in this `.ultraplan/`; sections numbered per WP (`33-01` ...). Mapping: WP-33 = P13, WP-34 = P1, WP-35 = P11, WP-36 = P2, WP-37 = P12, WP-38 = P3, WP-39 = P4, WP-40 = P5, WP-41 = P6, WP-42 = P7, WP-43 = P8, WP-44 = P9, WP-45 = P10, WP-46 = P14, WP-47 = P15, WP-48 = P16, WP-49 = P17.

### Q6 (follow-up to Q2): What a WP closeout requires?
- **Answer:** its items closed in BUGS and the register with pins, `make test-all` green, a ROADMAP line. The corpus re-run and gallery refresh happen only at the final WP's closeout (Q3).

### Q7: Capitalised plot-type names?
- Options: measure and match on this machine (recommended); refuse all capitals; keep any case.
- **Answer:** refuse all capitals. Accept only lower-case plot-type spellings, whatever the file system; note it under Differences.

### Q8: The ~35 dash-only words accepted where twoway refuses?
- Options: drop shadow synonyms only (recommended); keep all and list them; measure first.
- **Answer:** measure first. The research phase lists each word with twoway's answer; the maintainer decides per word in Phase 4.

## Category 2: Users & Context

### Q9: Who is the README gallery for?
- **Answer:** Stata users evaluating dash: they paste a twoway command and want the same picture. Captions in Stata terms, no internals.

### Q10: Who executes the sections?
- **Answer:** as WP-31/32: worktree agents under `../dash-wt/_tools/agent-rules.md`, merged by cherry-pick with `picks.sh`, three Stata slots; the orchestrator runs the gates.

### Q11: Batch size within a WP?
- **Answer:** 2-3 sections per batch, 1-4 tasks each, up to three sections in parallel.

### Q12: Who reviews corpus verdicts before the README?
- **Answer:** the harness assigns verdicts automatically; the maintainer signs off on the generated gallery once per refresh before it is committed.

## Category 3: Integration Points

### Q13: Which examples form the P13 corpus?
- Options: help files + g.pdf (recommended); help files only; help + g.pdf + repo.
- **Answer:** help files + g.pdf + repo: every example command in the twoway help files (about 128 plus the `gr_example2` named ones), every twoway example in g.pdf's [G-2] graph twoway and [G-3] option entries, the repository's `examples/` folder, and the audit's probe commands.

### Q14: Datasets fetched by webuse?
- **Answer:** downloaded once into a git-ignored local cache; an offline run uses the cache and names any missing dataset.

### Q15: Picture format?
- Options: PNG both (recommended); SVG twoway + PNG dash.
- **Answer (Other):** twoway as SVG, and the twoway SVG embedded in the dash HTML output.

### Q16 (follow-up to Q15): What "embedded in the dash HTML output" means?
- Options: one comparison page per example (recommended); one gallery page for all; a dash feature.
- **Answer:** one gallery page for all: a single HTML page, built with dash itself, holding every example's twoway SVG beside its live dash graph.

### Q17 (follow-up to Q15): What the README itself shows per example?
- Options: twoway SVG + dash PNG + link (recommended); SVG + link only; static dash SVG.
- **Answer:** static dash SVG: the dash graph is exported as SVG too (Bokeh's SVG backend), so both README columns are vector.

### Q18: Verdict method?
- **Answer:** geometry first -- ticks, labels, titles, keys, glyph counts and extents, colours (twoway SVG against dash's Bokeh model) with a known-differences ledger -- and an image-similarity score as a secondary signal.

### Q19: New developer-only dependencies for the harness?
- **Answer:** allowed in the dev/test tier only; nothing new for dash users or in `dash_requirements.txt`.

### Q20: Where the interactive gallery page lives?
- **Answer:** committed in the repository (a `docs/gallery/` folder); enabling GitHub Pages is a separate step the maintainer takes.

## Category 4: Edge Cases

### Q21: Zero-observation check when one plot of several is empty?
- Options: refuse if any plot is empty (recommended); refuse only if all are empty; measure twoway first.
- **Answer:** measure twoway first. Research measures twoway per type and per case (one empty plot among several, all empty, graph-wide if/in, by() with empty panels); the single Stata-side check copies twoway's answer per case, and the help documents any remainder (the D40 rule).

### Q22: Return code and message for the zero-observation refusal?
- Options: r(2000) "no observations" (recommended); r(2000) plus the plot named.
- **Answer:** r(2000) "no observations", with a second line naming the plot (its number and type) that has none.

### Q23: P6-P10 items Bokeh cannot draw?
- **Answer:** documented under the help's Differences with a measured example; the note stays.

### Q24: What counts as "supported by Bokeh"?
- **Answer:** anything built from Bokeh's shipped glyphs, annotations, tickers and CustomJS, including composites (several glyphs or labels making one twoway element). Custom TypeScript extension models do not count.

### Q25: P14 RH-8 (histogram/rbar recast + horizontal)?
- **Answer:** keep dash's clean transpose; list twoway's broken picture under Differences with a measured example.

### Q26: P12 contour above 1,000 distinct points?
- **Answer:** run `twoway__contour_gen` at registration so the first drawing is twoway's grid; after a filter move dash refits with its own fit and shows the stale cue.

### Q27: P12 lpolyci at zero-df grid points?
- **Answer:** correct the help to describe the difference accurately (Stata's compiled round-off is out of reach).

### Q28: P1 item 8, if the direct probe shows twoway refuses an operator form dash accepts?
- **Answer:** match twoway's answer: refuse exactly where twoway refuses, with its rc and words (P11 ruling); work on the operator part only where twoway draws.

## Category 5: Quality Attributes

### Q29: Test-suite speed work (gate ~40 min against the 5-minute target)?
- Options: a section in WP-33 (recommended); a separate WP; not now.
- **Answer:** a separate WP-50 for suite speed, after the seventeen package WPs.

### Q30: Where the corpus comparison runs?
- **Answer:** its own make target (`make corpus` / `make gallery`), run at the final closeout and on demand; a small pinned subset (about 20 examples) runs in the cert tier as a regression guard.

### Q31: P2 large data (JSON number lists, ~2x base64)?
- Options: binary columns + bound (recommended); document only.
- **Answer:** document only: keep JSON columns; state the measured timings and memory (about 6-8 s and 1.4 GB Stata RSS per million rows) in the help.

### Q32: P2 browsers (verified on Chrome only)?
- **Answer:** add Firefox and WebKit (Safari's engine) runs of the CSP, browser and accessibility tests in the release tier, through a dev-only driver.

### Q33: P2 lock coverage (Python 3.15, Windows ARM64, offline)?
- Options: warn + win_arm64 + offline doc (recommended); regenerate per release; document only.
- **Answer:** document only: dash_setup's help states the covered Pythons and platform tags (the lock pins tested versions, the earlier ruling) and that Python 3.15 and Windows ARM64 are not covered.

### Q34: P2 WebGL dashed lines and row count?
- **Answer:** fix both: dashed lines stay on the canvas backend; the WebGL switch counts the rows the graph draws; a WebGL-vs-canvas pixel check pins it.

### Q35: P2 c(macrolen) limit on function layers in named graphs?
- **Answer:** keep the points off the macro (a strL scalar or a file, as the one-line route does); fix the message and the help. (Wording restated after Q48: no edition is referenced.)

### Q36: Gallery privacy?
- **Answer:** no absolute paths, user names or machine names in the gallery page or SVGs (`test_no_secrets.py` covers `docs/gallery/`); Stata's example data only.

## Category 6: Existing Patterns

### Q37: Tracking register?
- **Answer:** a new `GAPS4.md` lists every audit item by id (AX-4, VF-1 ...) under its package, each with a "Tracked:" line read by `test_tracking_documents.py`; one BUGS.md entry per item, closed in place.

### Q38: Truth cscripts?
- **Answer:** one per WP (`test/test_wp33_truth.cscript` ... `test_wp49_truth.cscript`), a block per section, selected by `WPnn_ONLY` as WP-30/31 do.

### Q39: Carry over WP-31's working rules?
- **Answer:** yes, all: committed `scripts/extract_*_truth.do` (no hand-typed truth); saved-page JS and served Python twins with one fixture and a parity entry; tests pinning today's picture flipped with the reason, never deleted; a failing test first; the pending list, the help's Unsupported section and TWOWAY_COVERAGE_AUDIT.md updated in the same commit.

### Q40: Where new help Differences notes go?
- **Answer:** a one-line entry in "Differences from twoway" linking to the full note in its topic section (Resource limits, Stata graph integration, ...).

### Q41: Where the tracking foundation is built?
- **Answer:** once, in WP-33's first section (33-01): it writes GAPS4.md for all seventeen packages, opens every BUGS entry and teaches `test_tracking_documents.py`; each WP's closeout proves its own rows closed.

### Q42: What proves an item resolved by documentation?
- **Answer:** its BUGS entry closes "Documented" with a test that reads the help sentence and, where measurable, a probe that dash does what the sentence says.

## Category 7: Preferences & Tradeoffs

### Q43: P17 refusal hint lines and the Supported list?
- Options: twoway's line alone (recommended); hints behind a global.
- **Answer (Other):** keep the existing behaviour. dash's extra lines stay; P16 corrects any help sentence that says refusals print only twoway's line.

### Q44: P5 caps that are not on observations?
- Options: match twoway's limits (recommended); document all.
- **Answer:** document all: keep every cap; each is documented in the help (Differences entry + Resource limits).

### Q45: P5 observation-cap counting?
- **Answer:** document and fix: document the caps (D40), and count only the rows if/in selects when no filter, link() or csv needs every row, exporting only those.

### Q46: P2 version floor?
- **Answer:** keep the Stata 19 floor; README and help state the drop-in claim is for Stata 19 and later.

### Q47: P2 platforms (Windows, Linux, Intel macOS, GUI Stata)?
- Options: platform-neutral code + checklist (recommended); document only; defer.
- **Answer:** document only: README and help state the tested platform (macOS arm64, StataNow 19.5, console); no code changes. This covers the runners, the opener and the `~` expansion item (plat:PT-5, PT-6, TR-20, ECO-17).

### Q48: P2 editions?
- **Answer (Other):** do nothing about this, and never reference differences between Stata editions again. plat:PT-3 is withdrawn; no plan text, test or help change may mention it.

### Q49: P2 Python requirement?
- Options: document beside the claim (recommended); also a venv() default.
- **Answer (Other):** list the dependencies in the help file and do nothing else.

### Q50: P15 jitter()?
- Options: match shape, document points (recommended); document only.
- **Answer (Other):** keep the current noise and do not document the difference: jitter is pseudorandom. basic:PT-7, DT-25, TR-15 and sil:SD-6 are withdrawn.

## Category 8: Business Model (release and distribution)

### Q51: Version at the final closeout?
- **Answer:** stay at 0.1.0; only the date moves, as WP-31 did.

### Q52: The README's drop-in claim until the work lands?
- **Answer:** keep the claim; P16 fixes the specific false sentences as their WPs land.

### Q53: Gallery size budget?
- **Answer:** no cap; commit what the corpus produces.

### Q54: Examples shown in the README?
- **Answer:** about 12 curated examples spanning the plot types and common options, with a link to the full gallery page.

## Category 9: Visual & UX Vision

### Q55: README gallery layout?
- Options: table rows (recommended); pairs with captions.
- **Answer:** side-by-side pairs (twoway SVG | dash SVG) with the command as a caption beneath each pair, and its verdict.

### Q56: Verdict scale?
- **Answer:** Same / Close / Differs; Close and Differs list the measured differences in one line.

### Q57: Picture size?
- **Answer:** the dash graph rendered at a fixed size in twoway's default 5.5 x 4 in shape, so each pair lines up; the gallery page uses the same size.

### Q58: How the one gallery page (built by dash) is organised?
- **Answer:** dash tabs by plot type; each example shows its command, twoway's SVG, the live dash graph and the verdict.

---

## Discovery Summary

- Total questions asked: 58 (Q1-Q58; focused mode, follow-ups included)
- Categories fully covered: all 9 (Business Model read as release and distribution)
- Categories partially covered: none
- Categories skipped: none
- Key themes:
  - Scope = all 17 audit packages, one WP each (WP-33..WP-49 in the D40 order: P13 first), plus WP-50 for test-suite speed after them. D40/D41 govern; Q-answers fill the no-ruling items.
  - WP-33 (P13) builds the tracking foundation (GAPS4.md + one BUGS entry per item) and the corpus harness: twoway help files + g.pdf [G-2]/[G-3] + `examples/` + audit probes, datasets in a git-ignored cache, twoway SVG vs dash SVG (Bokeh SVG backend) at twoway's 5.5x4 shape, geometry verdicts (Same/Close/Differs) with a known-differences ledger plus an image score, maintainer sign-off, ~12 curated pairs injected into README, one dash-built gallery page with tabs by plot type embedding each twoway SVG beside its live dash graph, committed under `docs/gallery/` with no size cap; `make corpus`/`make gallery`, a ~20-example cert-tier guard; no paths or names in outputs.
  - Withdrawn or no-change by ruling: heatmap/sunflower and the internal class names (D40); Stata editions (Q48, never referenced again); jitter's noise (Q50); dash's extra refusal lines (Q43, kept); large-data JSON columns (Q31, documented); platforms (Q47, documented); the lock's coverage (Q33, documented); Python requirement (Q49, help lists dependencies only).
  - Fix rules: refuse all capitalised plot-type spellings (Q7); dash-only words decided per word after measurement (Q8); zero-observation check copies twoway per measured case, r(2000) with the plot named (Q21-Q22); "supported by Bokeh" = shipped models + CustomJS + composites (Q24); contour at build from `twoway__contour_gen` (Q26); P5 caps documented, observation cap counts only the selected rows (Q44-Q45); WebGL fixes (Q34); function points off-macro (Q35); Firefox + WebKit runs (Q32).
  - Process carried over from WP-31/32 (Q10-Q11, Q37-Q42): worktree agents, picks.sh, three Stata slots, 2-3 sections per batch, committed truth scripts, saved/served twins with parity, flip-not-delete, per-WP truth cscript, help-claim pins for documented items.
  - Release: stay 0.1.0 (date only), keep the README claim while P16 fixes false sentences as WPs land.

---

## Amendments made during Phase 3 (PRD review, 20oct2026)

### A1 (supersedes Q32): browsers
- **Ruling:** no Firefox or WebKit runs. The help states dash is tested in Chrome; problems in other browsers are not dash's to solve. plat:PT-16 is resolved by that sentence.

### A2: matamatrix()
- **Ruling:** do not draw matamatrix(); it does not exist in Stata. plot:PT-10 is withdrawn; no plan, test or audit may list it. The help stops naming it (P16).

### A3 (amends Q4, Q5): WP-39 removed
- **Ruling:** WP-39 (P4) is removed. Its other items move: capitalised plot-type names (Q7), the empty graph's axes and options, `(scatter ..) line ..`, and `||` inside one group go to WP-35 (P11); the dash.sthlp:737-742 sunflower sentence goes to WP-48 (P16). The WP number 39 stays unused, so the other WP numbers keep their Q5 mapping.
