# UltraPlan Discovery: dash — close 23 GAPS2 gaps

> Generated: 2026-09-25
> Phase: 1/6 - UNDERSTAND
> Mode: focused (GAPS2.md is the discovery record; questions cover only what it leaves open)

---

## Project Idea

Develop a plan to address the following items from `GAPS2.md` (audit of
25 September 2026 at commit `91d97be`, branch `s3-bugs`):

| Set | Items |
|---|---|
| S1 (silently wrong output) | B1, B2, B3, B5, B6, B7, C2, D1, E1, E2, F1, G1, K2, X1, X2 |
| S2/S3 | C4, E3, E14, G2, G3, G5, G6, G16 |

Each GAPS2 entry already records the gap, its evidence (file:line), whether it
is closable, a numbered plan and its tracking status. This discovery therefore
does not re-derive the gaps; it settles the decisions those plans leave open.

The previous ultraplan (phase 01 per-plot qualifiers, landed in commits
3130fba/639a475) was archived to `.ultraplan-archive-20260925/`.

---

## Codebase Detection

**Codebase found:** Yes — mature Stata package, branch `s3-bugs` at `91d97be`.

- **Stack:** Stata ado/Mata (`dash.ado` 7,439 lines, `dash_parse.mata` 5,103,
  `dash_setup.ado` 638) + Python (`dash_render.py` 27,715 lines) + Bokeh /
  pandas / numpy. Two renderers: `DashRenderer` (saved offline page, line 20935)
  and `ServerAppBuilder` (emits a `bokeh serve` app, line 24207). The saved page's
  filter logic is JavaScript embedded as `_DASH_FILTER_MASK_JS` / `_FILTER_JS`
  (lines 14110/14177); the served app's twin is Python.
- **Tests:** 168 pytest modules + 65 `.cscript` certification scripts
  (`test/`), 21 Stata-measured truth fixtures in `test/fixtures/*.json`
  produced by `scripts/extract_*_truth.do`. A node harness runs the saved page's
  JavaScript (`test_statistical_helpers.py:810`); node v24 is installed.
  pytest is parallel by default (`-n auto --dist loadgroup`), ~2 minutes.
- **Tracking documents:** `BUGS.md` (checkbox entries: Title / File Names and
  Line Numbers / Description / Suggested fix / Resolution; release guard = no open
  S1 or S2), `ROADMAP.md` (WP-01..WP-27, all DONE), `CHANGELOG.md` ("Results that
  change" section lists every numeric change with before/after), `phases/`
  (PHASE-01..29 specs from the earlier REMAINING.md audit).
- **Conventions (CLAUDE.md):** security first; a unit test per function and
  end-to-end tests; a failing regression test before every bug fix (rule 7);
  never commit to main; no AI references in commit messages; Stata only via
  `arch -arm64 /usr/local/bin/stata-mp -b do`; full pytest once before commit.
- **Relevant anchors named by GAPS2:** `_dash_parse_axis_label_opt` (16041),
  `_dash_apply_scale_ranges` (19017), `_TEXTBOX_SUBOPTS` (2438), `_dash_textbox`
  (18861), `_dash_axis_labels` (16003), `GlyphMapper` (5351), `SchemeParser`
  (3383), `_dash_format_kpi_value` (19609), `_parse_stata_numeric_fmt` (839),
  `_ROW_ID_COLUMN` (2008), `_dash_option_value` (17413), `_dash_dropdown_values`
  (1806), `_dash_pymin`/`min_bokeh` (dash_setup.ado 285/146).

---

## Discovery Q&A

<!-- Categories reinterpreted for a defect-closure plan:
     1 Scope & approach · 2 Behaviour decisions · 3 Shared components ·
     4 Edge cases · 5 Quality & verification · 6 Existing patterns ·
     7 Tradeoffs · 8 Release & tracking (stands in for business model) ·
     9 User-facing behaviour (stands in for visual/UX) -->

### Category 1 — Scope & approach (batch 1)

**Q1. How should discovery run, given GAPS2.md already records each gap's evidence, closability and plan?**
A: *Focused on open decisions.* GAPS2.md is the discovery record; ask only what its plans leave open (~16-24 questions).
→ Consequence: DISCOVERY.md cites GAPS2 entries rather than re-deriving them. Categories are reinterpreted for a defect-closure plan.

**Q2. How should the gaps be grouped into work units?**
A: *By shared code path.* Gaps that touch one component ship together (the Stata display-format writer E1/E3/G6; the textbox family B3/B6/B7; the axis family B1/B2/G16; the filter family E2/X1; ...).
→ Consequence: sections are components, not severities. Fewest conflicts inside `dash_render.py`; widest parallel batch.

**Q3. How far should C4 (saved page never refits computed layers after a filter move) go?**
A: *Omit C4 from the plan.* (User-supplied answer.)
→ Consequence: **C4 is out of scope.** The plan covers 22 gaps: B1, B2, B3, B5, B6, B7, C2, D1, E1, E2, F1, G1, K2, X1, X2, E3, E14, G2, G3, G5, G6, G16. C4 stays recorded in GAPS2.md (and its duplicate E4) with no work here; the plan must not add estimator ports to `_FILTER_JS` on C4's account. C2's JavaScript recount change is unaffected (it is C2's own plan step 2).

**Q4. Where should the gaps be tracked so the release guard sees them?**
A: *BUGS.md entries plus one ROADMAP WP.* Open a `BUGS.md` entry per gap up front (`- [ ] Title:` form, with File Names and Line Numbers / Description / Suggested fix; Resolution filled at close), and record the plan as **WP-28** in `ROADMAP.md` with user stories, BRs, TRs, ACs and a test plan in the WP-01..27 style.
→ Consequence: the plan carries a "tracking" deliverable at its start (22 open entries) and its end (22 resolutions + WP-28 marked DONE), and the release guard (no open S1/S2) is the plan's exit criterion.

```
Phase 1/6: UNDERSTAND [=         ] 11% - Category: Scope & approach (1/9 categories)
Questions asked: 4/~20 | Current batch: 1
```

### Category 2 — Behaviour decisions the GAPS2 plans leave open (batch 2)

**Q5. X2: the unbinned `colorvar()` default is a documented continuous map. What changes?**
A: *Fix the explicit forms; keep the default.* Under `colordiscrete` with `colorcuts()` each cut is a level and other values are drawn gray with missing; cuts below the column minimum are dropped (the minimum is used if all are below it); add `colorlevels(#)` and `colorvarminmax`; declare `zlabel()`, `ztitle()` and `zscale()` and draw them on the colour key. The continuous default and dash.sthlp:2503-2507 stay.
→ Consequence: X2 closes to the extent GAPS2 calls closable; no CHANGELOG "results that change" entry for the default. `colorrule()`, `colorstart()`, `colorend()` stay named-only (documented) unless trivially honoured by the same mapper edit.

**Q6. E1/E3/G6: which Stata display formats does the shared writer (Python + JavaScript twin) write?**
A: *`%f`/`%g`/`%e` with `c` and the European comma, and every `%t` picture; refuse `%x`/`%H`.* `%w.dg` follows Stata's width-driven rule; dates cover %td, %tc, %tC, %tw, %tm, %tq, %th, %ty with default and custom pictures. `%21x`/`%16H` are refused with r(198) at build time, naming the format.
→ Consequence: one formatter module used by KPI cards (first paint and after a move), dropdown labels, slider labels, tooltips (CustomJSHover), date-axis ticks (CustomJSTickFormatter), marker labels and the CSV; a Stata-measured fixture of `display` outputs pins both twins.

**Q7. G1: which remedy for internal column names colliding with user variables?**
A: *Reserve a `__dash` prefix and refuse it.* Any user variable whose name starts with `__dash` is refused at export with r(110), as `__dashq` already is; internal columns keep their names and the qualifier/by()-order/ustrfix columns stay generated in the user's dataset.
→ Consequence: the overwrite half of G1 closes. The "room at c(maxvar)" half (temporary-frame export) is **deferred by this choice** and must be recorded as a residual in the BUGS.md entry and the plan's exclusions, not silently dropped. `__mlabel__*` columns are not under the `__dash` prefix: the plan renames them under it (e.g. `__dash_mlabel_*`) so one rule covers every internal column in both twins.

**Q8. K2: how is the real Python/Bokeh floor set?**
A: *Declare only what is tested today.* The minimums become the lowest interpreter and Bokeh the suites actually run under (both interpreters of WP-25: Stata's bundled Python and the system one); `dash_setup` refuses anything below.
→ Consequence: no venv matrix is built. The plan's research step must read the exact versions from the suite logs/CI so the declared floor is a measured fact. `from __future__ import annotations` in the generated app and the launcher's `returncode` check are still done (they are K2's steps 3-4 and overlap F1).

```
Phase 1/6: UNDERSTAND [==        ] 22% - Category: Behaviour decisions (2/9 categories)
Questions asked: 8/~22 | Current batch: 2
```

### Category 3 — Shared components and transport (batch 3)

**Q9. G3: how far does the data-limit fix go?**
A: *Count only what the page embeds; keep the JSON export.* `_dash_cell_cap` counts the columns the page will hold; a computed-only graph (histogram, kdensity, fits) that no filter, link, csv or hover touches counts only its drawn output. The size note reports embedded bytes.
→ Consequence: no binary transport change; the hardened JSON path and its security tests are untouched. G3 closes to the extent GAPS2 calls closable (row-drawing layers stay bounded).

**Q10. X1: one dropdown matching rule for both modes.**
A: *Compare numbers as numbers in both modes.* Numeric columns carry numeric option values and the JavaScript and pandas masks use numeric equality (NaN explicit); string columns keep exact text ('01' stays '01'); one pytest runs node and pandas on the same columns and compares masks.
→ Consequence: `_dash_option_value` stops integer-rewriting strings; `_DASH_FILTER_MASK_JS` and `_dash_dropdown_mask` become one rule; `_dash_dropdown_values` keeps 'nan'/'None'/'NaT' as ordinary strings.

**Q11. E14 item 5: which bs filter-bar placement wins?**
A: *The saved page moves its bar below the header.* Matches the served app and the non-bs layouts; the ALLOWED exemption in test_mode_parity.py is removed.
→ Consequence: a visible change to saved bs pages; CHANGELOG notes it (layout, not numbers).

**Q12. F1: port already in use.**
A: *Refuse with a message naming the port.* The launcher reads the child's exit status and stderr, polls /health for up to 30 s and prints the URL only once it answers; `dash serve` errors "no server started on port N: the port is in use" with non-zero rc; `--port` outside 1024-65535 is refused, not clamped.
→ Consequence: shares the launcher `returncode` step with K2; the cscript asserts `_rc != 0` against a held socket.

```
Phase 1/6: UNDERSTAND [===       ] 33% - Category: Shared components (3/9 categories)
Questions asked: 12/~23 | Current batch: 3
```

### Category 4 — Edge cases (batch 4a)

**Q13. X1: how do missing values appear in a dropdown once 'nan'/'None'/'NaT' are ordinary strings?**
A: *Numeric missing not listed; the empty string listed as a blank entry.* A numeric NaN (Stata's `.`) is not offered, as today; `""` (Stata's missing string, a real value) is offered as a blank row and selects rows equal to `""`.
→ Consequence: missingness is decided from dtype and None/NaN only; the `colorvar` string path follows the same rule ('nan' text is a category, not missing).

### Category 5 — Quality & verification (batch 4b)

**Q14. How is twoway's drawn truth read for B1, B3, B5, B6, B7, D1, G16, X2?**
A: *One SVG helper plus `.Graph` properties.* A shared cert helper exports twoway's graph to SVG and extracts text elements and fill colours; axis extents (B2) come from the `.Graph` object's axis properties. Truth is recorded into `test/fixtures/` by an `extract_*_truth.do` script in the existing pattern, so pytest pins it too.
→ Consequence: a new shared cert helper (SVG text/fill reader) is a prerequisite section for several others; fixtures are produced once by Stata and consumed by both suites.

**Q15. E2 needs a multi-move test on the saved page. Which harness?**
A: *Extend the node harness to carry state across moves.* The node runner keeps ColumnDataSource state between calls so a sequence can be asserted; no browser needed.
→ Consequence: `TestFilterJavaScript`'s runner (test_statistical_helpers.py:810) gains a stateful mode reused by E2, X1 and C2's recount tests.

**Q16. G2: how wide is the string-variable cscript?**
A: *Every plot type, every varlist position.* One generated cscript loop over the 38 types asserts dash's rc and message equal twoway's.
→ Consequence: the cscript is generated from the plot-type table so a missed parser is caught; pytest keeps the spec-level refusal test.

```
Phase 1/6: UNDERSTAND [======    ] 55% - Category: Quality & verification (5/9 categories)
Questions asked: 16/~23 | Current batch: 4
```

### Category 6 — Existing patterns (batch 5a)

**Q17. Which branch?**
A: *Continue on `s3-bugs`.* Commits go to the current branch; GAPS2.md and the fixes share its history. The merge command into `main` is reported at the end, never run (CLAUDE.md rule 5).

**Q18. How are commits cut?**
A: *One commit per gap: its failing test, then its fix.* Shared components (the format writer, the SVG helper, the stateful node harness) land in their own commit first. Commit messages name the gap and the regression test; no AI references (rule 6).

### Category 7 — Preferences & tradeoffs (batch 5b)

**Q19. Parallel execution?**
A: *Yes, one agent per section in a worktree.* Each agent's diff is merged with `patch -p1` from its worktree (never `cd` into it), worktrees removed after; the full suites run once on the merged tree. Concurrent Stata runs get their own `STATATMP=<dir>/`.
→ Consequence: the section index must mark which sections are independent (batch 1) and which wait on shared components.

**Q20. Documentation per gap?**
A: *dash.sthlp update plus a CHANGELOG entry per gap.* Each closed gap updates the help paragraph GAPS2 cites; gaps that change drawn numbers or pictures go under "Results that change" with the command, the old value and the new one.

```
Phase 1/6: UNDERSTAND [========  ] 78% - Category: Preferences & tradeoffs (7/9 categories)
Questions asked: 20/~23 | Current batch: 5
```

### Category 8 — Release & tracking (batch 6a)

**Q21. Exit criterion?**
A: *Re-run the WP-27 release gate from an installed package.* Both suites green under both interpreters, `net install` into a clean PLUS, every example at rc 0, no open S1 or S2 in BUGS.md, working tree clean, merge command reported.

**Q23. Is GAPS2.md edited as gaps close?**
A: *Update each closed entry's Tracked line.* Each entry gains "Closed in WP-28, BUGS.md <title>, commit <hash>"; C4 and the G1 residual are marked deferred with the reason. The audit text is not rewritten.

### Category 9 — User-facing behaviour (batch 6b)

**Q22. When dash starts honouring an option it used to misread silently, does it say anything?**
A: *Silent, as twoway is.* Honoured options print nothing; only options dash still cannot draw are named in the note. The CHANGELOG records each change once.

```
Phase 1/6: UNDERSTAND [==========] 100% - COMPLETE
Questions asked: 23 across 9 categories (focused mode)
```

---

## Discovery Summary

### Coverage

| # | Category (reinterpreted) | Questions | Status |
|---|---|---|---|
| 1 | Scope & approach | 4 | covered |
| 2 | Behaviour decisions | 4 | covered |
| 3 | Shared components & transport | 4 | covered |
| 4 | Edge cases | 1 | covered (focused) |
| 5 | Quality & verification | 3 | covered |
| 6 | Existing patterns | 2 | covered |
| 7 | Preferences & tradeoffs | 2 | covered |
| 8 | Release & tracking | 2 | covered |
| 9 | User-facing behaviour | 1 | covered (focused) |

**Total questions asked:** 23 · **Follow-ups:** 1 (Q13) · **Early stop:** no.
Categories 4 and 9 were deliberately shallow: GAPS2's entries already list the
boundary cases and the drawn result for each gap.

### Key Themes

1. **Scope is 22 gaps, not 23.** C4 (offline re-estimation) is omitted; nothing is ported to `_FILTER_JS` on its account.
2. **Sections are components.** One Stata display-format writer (E1/E3/G6), one textbox grammar (B3/B6/B7), one axis pipeline (B1/B2/G16), one filter rule (E2/X1), one launcher/floor fix (F1/K2).
3. **Truth comes from Stata, once.** An SVG-plus-`.Graph` cert helper and `extract_*_truth.do` scripts write fixtures both suites pin; the K2 floor is the tested version, not a modelled one.
4. **Every gap is tracked twice and closed loudly.** 22 open BUGS.md entries and WP-28 at the start; resolutions, CHANGELOG lines, dash.sthlp edits and GAPS2 Tracked lines at the end; the release guard is the exit.
5. **Behaviour stays twoway-quiet.** Fixes honour options silently; refusals (string plot variables r(109), `__dash` names r(110), unwritable formats r(198), held port non-zero rc) are loud and named.

### Critical Requirements

1. The 15 S1 gaps in scope produce the numbers, text and rows twoway produces, proven by a Stata-measured fixture or SVG comparison and asserted in both modes.
2. Each fix lands as a failing regression test first, then the fix, one commit per gap on `s3-bugs`.
3. The plan ends with the WP-27 gate re-run from an installed package and no open S1/S2 in BUGS.md.

### Deliberate exclusions (record in the plan)

- **C4 / E4**: out of scope by decision (Q3).
- **G1 residual**: qualifier/by()-order/ustrfix columns stay in the user's dataset; the c(maxvar) room issue is recorded as deferred (Q7).
- **X2 residual**: the continuous colour default and `colorrule()`/`colorstart()`/`colorend()` stay as documented (Q5).
- **G3 residual**: row-drawing layers stay bounded; no binary transport (Q9).
- **E1/E3**: `%x`/`%H` formats are refused, not written (Q6).
- **D1 (Q30)**: third-party scheme files are out of scope: no sweep of the locally installed schemes, no copied d3colors fixture; the CMYK/hsv/`colour*#` colour forms stay D7's.

### Open Questions for Research

1. Exact Python and Bokeh versions both suites run under today (K2 floor).
2. Whether BokehJS draws a label-only `LegendItem` (B5 `-` lines) and how `major_label_overrides`, `CustomJSTickFormatter`, `CustomJSHover` behave in the installed Bokeh.
3. Current line anchors for every function GAPS2 names (the file has moved since the audit's numbering may drift).
4. How `release_verdict.py` reads BUGS.md severity, so new entries carry a severity it parses.
5. The plot-type table and the four varpart parsers in dash.ado (G2), `_dash_cell_cap` (G3), `_dash_is_name` and the KPI pattern (G5).

---

## Amendments from Phase 2 research (2026-09-25)

Four discovery answers were revised after research contradicted them (see RESEARCH.md "Conflicts Found"):

- **Q4 amended.** BUGS.md entries are **not** opened up front: `test_tracking_documents.py::TestNoOpenEntryBlocksARelease` fails pytest on any open S1/S2 entry. Each gap's entry lands **closed, in its fix commit**, naming its regression test. WP-28 in ROADMAP.md lists all 22 gaps from the start.
- **Q4/Q23 amended.** `test_tracking_documents.py` is extended to resolve GAPS2 ids (including X-prefixed) against GAPS2.md; WP-28 carries its own `#### GAPS2 traceability` table (heading must not contain "## Traceability matrix"); GAPS2.md is added to `test_packaging.py` `_ROOT_ALSO` and committed.
- **Q7 amended.** The jitter columns `_x_jit`/`_y_jit` are renamed under the `__dash` prefix with the other internals; the derived glyph-field collision (`x`, `y`, `top`, `count`, …) is recorded as a G1 residual in BUGS.md and dash.sthlp, not fixed.
- **Q14 amended for B2.** Axis-extent truth comes from SVG-fitted extents (the `extract_axis_truth.do` method, through the shared helper); `.Graph.plotregion1.yscale.curmin/curmax` is probed once in the same script and used only where it matches the SVG.

Scope widenings folded in without a question (they do not contradict a decision): X1 keeps string columns as text in every saved snapshot (`_dash_json_value`); G5 widens the renderer's ASCII-only `_DASH_VARNAME_RE` and the colorvar regex; G3's relaxed count applies to the saved page only (the served app embeds every row); the KPI JS card escapes its format text (security); the tooltip `_PLACEHOLDER` test pattern is widened deliberately for `{custom}`; all three port clamps become refusals and the tests requiring them are inverted; G2 covers 40 types; B1 also accepts `#N` followed by a labelled numlist; E14's `filterposition(left)` difference is recorded, not fixed.

---

## Refinement answers from Phase 4 review (2026-09-25)

**Q24. Where do the old (wrong) values for CHANGELOG "Results that change" come from?**
A: *Captured from the failing test's first run against the unmodified tree.* The fix commit's message and the CHANGELOG entry quote the value the failing test printed at 91d97be. No re-checkout.
→ Apply to: every section's task 1 (record the failure output), every closing task, S19's CHANGELOG reconciliation.

**Q25. Checked-in demo pages after the fixes change drawn output?**
A: *Regenerate them all in closeout.* S19 runs `scripts/regen_dashboards.py`, `regen_comprehensive.py`, `regen_bootstrap_examples.py` (and any other `regen_*.py`) once on the merged tree and commits the pages (dashboard.html, comprehensive_demo.html, bs_*.html, kelly22ex_dashboard.html, sp500_dates.html, testing.html, scatter.html, full_dashboard.html and the copies under test/).
→ Apply to: S19 gains a task before the release gate.

**Q26. Two distinct numeric dropdown values that format to the same label (float 0.1 vs double 0.1000000015 under %9.0g; Bokeh requires unique labels)?**
A: *Merge into one entry that selects both.* One label per distinct display text; the mask matches every value whose display text equals the entry's. The format decides the grouping, in both modes.
→ Apply to: S12 (labels: dedupe by display text) and S17 (the numeric rule compares display text when a label groups several values; `mask_parity` gains a case with two values sharing a label).

**Q27. dash_setup on a below-floor Bokeh (3.6/3.7 would render)?**
A: *Refuse and print the exact pip command* for the interpreter Stata uses (`<python_exec> -m pip install 'bokeh>=3.8'`); nothing is installed by dash_setup.
→ Apply to: S09's K2 tasks and dash_setup.sthlp text; a cscript asserts the printed command names `c(python_exec)`.

Refinement questions still to ask (batch B): cert-suite runtime budget; an "invariants" paragraph in AGENTS.md; the third-party scheme sweep in the release gate; a Stata-version stamp in every new fixture's `_meta`.

**Q28. Runtime budget for the certification suite?**
A: *Cap the growth at about five minutes.* Only Stata-truth comparisons get new cscript code, consolidated into one new script; refusal and message checks join existing scripts (review D11).

**Q29. Record the new invariants for future agents?**
A: *Add a short invariants section to AGENTS.md* (review D14; S19).

**Q30. Third-party scheme files in the release gate?**
A: *Ignore all third-party scheme files; they are out of scope.* (User-supplied answer.) S06 drops the PLUS sweep and the copied d3colors fixture; D1 is pinned with a scheme file the test writes (review D13). Added to the deliberate exclusions.

**Q31. Stamp every new fixture with the Stata build it was measured with?**
A: *Yes: `_meta` carries the Stata version, born date and dash commit* (review D12).
