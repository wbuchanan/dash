# UltraPlan: dash WP-31 -- Master Technical Plan

> Generated: 2026-10-10 | Phase 3/6 - PLAN (Step 3b)
> Sections: 61 | Tasks: 239 | Parallel batches: 22 (0-21)
> Base: branch `s3-bugs` at `6370ca4` (= `main` 1a78bb9 plus the heatmap removal and GAPS3.md)
> For the plain-English requirements see PRD.md; for the per-section briefs see sections/.

---

## Project Overview

### Summary

dash renders Stata `twoway` commands as interactive Bokeh HTML: a saved page
whose callbacks are JavaScript, or a served `bokeh serve` app whose callbacks
are Python. GAPS3.md (10oct2026) lists what still separates dash from a drop-in
`twoway`. WP-31 closes every in-scope row in 59 fix sections grouped into 20
small batches between a tracking foundation (S01) and a closeout (S61), in the
order silent drops → values twoway accepts → named-not-drawn options →
fidelity → dashboard extensions → documents and tests, with one JavaScript
estimator port per batch from batch 3 so the offline page gains refits
steadily.

### Goals

1. A pasted twoway command draws what twoway draws, with twoway's legend keys,
   axis titles, numbers and refusals, in both the saved page and the served app.
2. Nothing is dropped in silence: every accepted option is drawn or named;
   every option twoway refuses on a type is refused with twoway's words.
3. The offline page refits every computed layer after a filter move (eleven
   estimators and contour within its cap), so the saved and served pages agree.
4. The dashboard extensions the maintainer asked for ship with both twins, and
   every page is accessible and prints as it looks.
5. The documents, help, examples, tests and registers tell the truth about the
   code at closeout; `make cert` and `make gate` pass.

### Constraints

- Apple-silicon macOS, StataNow 19.5, Python 3.11-3.13, bokeh 3.8-3.9; tests
  stay on bokeh 3.8's property set; no new Python dependency (M22).
- Three Stata sessions at once (`scripts/stata_slot.sh`); the full pytest suite
  and `make cert` only at batch ends (M9).
- One editor per batch for each hot function (R12); worktree agents merged with
  `patch -p1`; GitNexus re-indexed after each landing (R13).
- Scheme files hold RGB and Stata's RGBA forms only (M7); no security guard is
  weakened (M11); no tooling names in commit messages (CLAUDE.md rule 6).
- Version stays 0.1.0; the date moves at closeout (M18).

---

## Architecture Overview

```
 Stata (dash.ado, dash_parse.mata)                 Python (dash_render.py)                         Browser
 ─────────────────────────────────                 ────────────────────────                        ───────
 twoway syntax → _dash_parse_*_opts  ─spec.json─▶  OptionTranslator / SchemeParser / GlyphMapper ─▶ saved page: BokehJS + _FILTER_JS
   rules table (_dash_option_rules)                  (shared glyph layer, copied by source into        (JS twins of every estimator,
   applicability column (S04)                         the served app: ServerAppBuilder template)        contour isobands, data table,
   pending lists → "ignoring" note      ─data.json─▶ DashRenderer (saved)  |  _generate_app_source      error banner, ARIA)
   Stata-side truth: twoway__*_gen,                   (served: Python refit per move)                 served app: Python callbacks,
   regress/lowess/lpoly at registration                                                                 Tornado, token, CSP
 Tests: test/*.py (pytest), test/*.cscript (console Stata), test/fixtures/*_truth.json ← scripts/extract_*_truth.do
 Registers: GAPS3.md §9 Tracked lines ← BUGS.md entries ← test_tracking_documents.py
```

### Architecture Notes

- New drawing code lands in `GlyphMapper`/`OptionTranslator`/`SchemeParser`
  methods or module helpers on the served copy lists (R2), never in the template
  alone (M14).
- A computed layer is refit on the saved page when its mapper tags
  `_dash_agg_source/_dash_agg_config/_dash_agg_rows` and `_FILTER_JS` has a
  branch for its type; the served app refits any layer whose mapper builds its
  own source. S10 generalises the JS prelude; S13-S29 add the twins.
- Contour (S23/S26/S29): twoway's interpolation (kernel √(x²+y²) + linear
  trend; Shepard 1/d²) on twoway's unique-x × unique-y grid, exact to 1,000
  points, bounded 100×100 grid above with the stale cue; Bokeh `figure.contour`
  in Python, marching squares and isobands in JS.
- Refusals (S04-S09): a per-type applicability table generated from Stata's
  parse classes and measured messages; the abbreviation superset removed.
- Tracking (S01): GAPS3 §9 Tracked lines, 93 BUGS.md entries, CHANGELOG
  markers, `test_wp31_truth.cscript`, the tracking test's GAPS3 reader.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Command | Stata ado + Mata (`dash.ado`, `dash_parse.mata`) | parse twoway syntax, validate, write spec/data JSON, run Stata-side truth |
| Renderer | Python 3.11-3.13, numpy, pandas, bokeh 3.8-3.9 (contourpy via bokeh) | build figures, estimators, interpolation, HTML with CSP |
| Saved page | BokehJS + dash's `_FILTER_JS`/`_BRUSH_JS`/`_DASH_FMT_JS` | filters, brushing, KPI recompute, estimator and contour twins, data table, error banner |
| Served app | generated `bokeh serve` file (Tornado) | Python refits per move, token, rate limits, headers |
| Tests | pytest 8.4/9 (`-n auto`), node (js_runner), headless Chrome (DevTools), console Stata cscripts | unit, parity, JS, browser, certification |
| Truth | `scripts/extract_*_truth.do` → `test/fixtures/*_truth.json` | measured twoway/Stata values |

---

## Section Index

See `sections/index.md` for the manifest (61 sections, batches 0-21, dependencies,
risk, effort, tasks, case-id prefixes), the decision record (M1-M25, A1-A10),
the batch order with hot-function owners, the merge rules R1-R13 and the gates
G1-G3.

### Dependency graph (batches)

```
B0  [01]
B1  [04] [02] [03]
B2  [05] [07] then [06]                05,06 ← 04 (06 cut after 05 lands)
B3  [10] [08] [09]                     09 ← 06
B4  [16] [11] [12]                     16 ← 10; 11,12 ← 04
B5  [13] [14] [15]                     13 ← 10
B6  [19] [17] [18]                     19 ← 10; 17 ← 15; 18 ← 03
B7  [22] [20] [21]                     22 ← 19
B8  [25] [23] [24]                     25 ← 10
B9  [28] [26] [27]                     28 ← 13; 26 ← 23
B10 [29] [30] [31]                     29 ← 26, 10
B11 [32] [33] [34]                     33 ← 24
B12 [35] [36] [37]                     35 ← 09
B13 [38] [39] [40]                     39 ← 31
B14 [41] [42] [43]
B15 [44] [45] [46]                     44 ← 40
B16 [47] [48] [49]
B17 [50] [51] [52]                     52 ← 10
B18 [53] [54] [55]                     53 ← 48; 54 ← 48, 49
B19 [56] [57] [58]                     56 ← 02-55; 57 ← 21, 26
B20 [59] [60]                          60 ← 10, 51
B21 [61]                               ← all
```

Critical path: 01 → 04 → 05 → 06 → 09 → 35 (batch 12); 01 → 10 → 13 → 28 (fpfit JS, batch 9) and 01 → 23 → 26 → 29 (contour, batch 10); 48 → 53/54 by batch 18.

Phase 4 decisions that bind every section: `.ultraplan/review/DECISIONS.md`.

---

## Execution Strategy

- 61 sections across 22 batches; 2-3 sections per batch (Q9), at most three
  Stata sessions at once (Q8); each batch lands in one session and ends with
  the full pytest suite and `make cert` (M2, M9).
- Per section: cut a worktree `wp31-s<NN>`; task 1 writes the failing tests and
  saves the failure text; the fix; flips; fixture; BUGS entry closed; GAPS3
  Tracked line; CHANGELOG marker replaced; one commit per GAPS3 row; hand back
  with the section's own tests green (G1).
- Per batch: merge in the index order with `patch -p1`; full suite; `make cert`;
  fix on `s3-bugs` if red; re-index GitNexus (G2).
- Closeout S61: dates, CHANGELOG release line, ROADMAP WP-31 DONE with
  measurements, full suite, `make cert`, `make gate`, residuals filed (G3).

## Risk Summary

- **Red (11):** 09 axes 3-9, 10 JS prelude, 19 JS lpoly, 22 JS lpolyci, 23
  contour interpolation, 26 contour drawing, 28 JS fpfit, 29 JS contour, 44
  style-file resolver, 45 date ticks, 51 link groups/brush, and the batch-11
  trio's shared axis/size surface (32). Each red section sits with lighter
  partners and owns its hot functions for the batch.
- **Yellow (36):** the option, geometry, data and dashboard sections.
- **Green (14):** 01, 03, 05, 08, 34, 39, 41, 50, 52, 55, 57, 58, 59, 61 (the
  count in the manifest is the one that binds).

## File Map (where the work lands)

- `dash.ado`: option declarations and `sreturn`, the rules/applicability tables,
  pending lists, `_dash_fold_typed`, type families and var-count branches, the
  seven graph key lists, weight/operator evaluation, Stata-side truth programs,
  `dash kpi` weights, `table()`/`link()` parsing, the browser rc, `sys.argv`.
- `dash_parse.mata`: abbreviation table, `_dash_undrawn_plottype`, repeat and
  foreign tables, stylelist tokeniser, layout cell checks, prefixed helpers.
- `dash_render.py`: `OptionTranslator` (symbols, patterns, colours, sizes),
  `SchemeParser` (stubs, style resolver), `GlyphMapper` (every mapper, arrows,
  dot rows, colorvar, weights, rpcap/rpspike, contour), module helpers
  (interpolation, legend geometry, textbox placement, minor ticks, edge titles,
  reference lines, data table cell), `_FILTER_JS`/`_BRUSH_JS` (twins, error
  banner, throttle, links, export), `ServerAppBuilder` template (copy lists,
  move apply, health, resources, ARIA).
- `dash.sthlp`, `dash_setup.sthlp`, `TWOWAY_COVERAGE_AUDIT.md`, `README.md`
  (new), `dash.pkg`, `CHANGELOG.md`, `BUGS.md`, `GAPS3.md` (§9), `ROADMAP.md`
  (WP-31), `examples/*.do`.
- `dash-*.scheme` (26, regenerated with the new stubs).
- `test/`: one new pytest file per item, `test_wp31_truth.cscript`, area
  cscript cases `U<NN>-<k>`, parity corpus entries, flipped pins,
  `function_test_map.py`/`program_coverage_map.py`, `js_runner.py`,
  `test_tracking_documents.py` (GAPS3 reader), fixtures with generators under
  `scripts/extract_*_truth.do`, `Makefile` targets (`truth`, `lint`), a CI
  workflow.

---

## Review Notes

### Review Date: 2026-10-10

### Self-Review Results
- Four reviewers over all 61 section files, the index and BRIEF, plus five
  deep passes (S30-S33, S34-S37, S38-S41, S42-S46): about 200 findings
  recorded in `.ultraplan/review/REVIEW-1.md` .. `REVIEW-4.md` and
  `REVIEW-3b..3e`.
- Critical: 6 (A3 missing from the tracking foundation; the Tracked-line sha
  convention could never pass the tracking test under `patch -p1` landings;
  the contour JS pushed interior segments with the wrong orientation so rings
  never chained; S32's aspect-ratio callback hung on a property BokehJS sets
  without a change event; S37's margin helper zeroed every figure's automatic
  borders; S38 contradicted itself and S39 on a template edit).
- Auto-fixed: about 190, applied by four fixer passes to the section files
  under the rulings A11-A34 of `.ultraplan/review/DECISIONS.md`.
- Maintainer decisions: 8 (D1-D8 in DECISIONS.md).

### Category Results
| Category | Result |
|---|---|
| Completeness | WARN → fixed: A3 entry, G3d and D10 bystyle residuals, axe on example pages (S61) |
| Consistency | WARN → fixed: batch-11 rules owner, batch 4/5 swap (S13↔S16), B5a/B5b and B4a/b/c ids, owner table for batches 11-17, same-line scheme regeneration split |
| Feasibility | WARN → fixed: contour segment orientation, `inner_width` callback replaced, `min_border_bottom`, function names, `_dash_graph_margin` guards, style-reader guard call |
| Security | pass; three hardenings added (MultiChoice label escaping, hover text as carried columns, TOCTOU `expect=` on the style reader) |
| Scalability | pass; unique-value formatting and a memoised style reader added |
| Edge cases | WARN → fixed: one Arrow path for extended reference lines, embedded style rows for hosts without Stata's files, saved-page re-bridging and weighted sizes after a move handled in S52 |
| User experience | pass (M17 documentation where Bokeh cannot express; D5 refusal for tabs()) |
| Cost & complexity | pass; S38 and S32 simplified to one path each |

### Refinement Questions Asked (maintainer answers)
1. Arrowheads: custom rotated head honouring mangle()/barbsize() (D1).
2. mlabel minimum becomes `mlab`; `mla()` is mlalign() with a Changed-behaviour line (D2).
3. estopts()/predopts()/estcmd() layers frozen in both modes with the cue (D3).
4. Contour above the cap: seeded 1,000-point subsample, 100×100 grid, cue and note (D4).
5. tabs() unknown name refused r(198) like layout() (D5).
6. by() graphs get one data table under the grid with a panel column (D6).
7. BUGS.md "Not fixed" preambles rewritten; reopen as S3 when no closer is found (D7).
8. "(release candidate)" dropped at closeout (D8).

### Sections Modified
All 61 section files were re-edited by the fixer passes; index.md gained the
owner-table entries for batches 11-17, the batch 4/5 swap, S09's dependency on
S06, rows 40/41's ids, step k.3b and the DECISIONS pointer; BRIEF.md gained
the `<files>` rule, the `commit pending` form and the one-block-per-row rule;
PLAN.md's dependency graph follows the swap.
