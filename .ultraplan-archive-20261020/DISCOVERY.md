# UltraPlan Discovery: dash -- close the GAPS3 drop-in gaps

> Generated: 2026-10-10
> Phase: 1/6 - UNDERSTAND
> Mode: focused (GAPS3.md is the discovery record; questions cover only what it leaves open)

---

## Project Idea

Develop a plan to address the remaining gaps between dash and a drop-in
`twoway`, as recorded in `GAPS3.md` (audit of 10 October 2026 at `1a78bb9`,
committed with the heatmap removal as `6370ca4` on `s3-bugs` = `main`).
Include `contour`, `contourline`, `rpcap` and `rpspike` if Bokeh can draw
them; otherwise say why and exclude them. Every task must be specified so that
the least capable agent codes it correctly on the first attempt. Prefer many
small batches over few large ones.

The previous ultraplan (WP-28, WP-29, WP-30; all landed) was archived to
`.ultraplan-archive-20261010/`; `.ultraplan/handoff/` (the DROPIN-REMAINING
register and run logs) stays in place because `test_tracking_documents.py`
reads it.

---

## Codebase Detection

**Codebase found:** Yes -- mature Stata package at `6370ca4`.

- **Stack:** Stata ado/Mata (`dash.ado` 11,039 lines, `dash_parse.mata` 9,789,
  `dash_setup.ado`, `dash_setup_lib.py`) + Python (`dash_render.py` 52,280
  lines) + Bokeh 3.8-3.9 / pandas / numpy, Python 3.11-3.13, StataNow 19.5 on
  Apple silicon. One glyph layer (`GlyphMapper`) shared by the saved page
  (`DashRenderer`) and the served app (`ServerAppBuilder` emits a self-contained
  `bokeh serve` file by copying the glyph layer's source). The saved page's
  filter logic is JavaScript (`_FILTER_JS`); the served app's twin is Python.
- **Tests:** 299 pytest modules (21,124 tests, ~7 min parallel), 68 `.cscript`
  certification scripts under the console binary, 83 Stata truth fixtures from
  `scripts/extract_*_truth.do`; a node harness runs the saved page's JS; a
  mode-parity guard compares saved and served profiles in the batch tier.
- **Conventions from WP-29/WP-30:** one BUGS.md entry per item opened by a
  tracking-foundation section and closed in place by its fix section; a
  per-section Stata truth block in `test/test_wp<NN>_truth.cscript`; GAPS2
  "Tracked:" lines; `test_tracking_documents.py` pins the registers; batches
  run three Stata sessions at once (`scripts/stata_slot.sh`); full pytest only
  at batch end; `make cert` at batch ends; commit messages never name the
  tooling; worktree agents merged with `patch -p1`.
- **Register:** GAPS3.md sections 4.A-4.K (gap IDs A1..K6), 5 (partially
  finished work), 6 (register corrections), 7 (open decisions).

---

## Discovery Q&A

## Category 1: Core Requirements

### Q1: Which GAPS3 areas should the plan cover?
- Options: twoway-facing + docs/tests/packaging basics (recommended); only 4.A-4.G; every row incl. dashboard extensions, platform package, module split.
- **Answer (Other):** everything twoway-facing, plus docs, tests, packaging basics, **accessibility (K6)** and **dashboard extensions (H2)**.

### Q2: Should the platform package be in this plan?
- **Answer:** No, keep it deferred as WP-30 left it.

### Q3: Definition of done for the whole plan?
- **Answer:** every in-scope GAPS3 row closed with a BUGS.md entry and a pinning test; full pytest suite, `make cert` and `make gate` green (the WP-29/WP-30 bar).

### Q4: Route for contour/contourline if Bokeh can draw contours from a grid?
- **Answer:** reimplement twoway's interpolation (thin-plate spline, Shepard) in Python and JavaScript so the layer refits after a filter move. Verified against Stata's own grid (twoway__contour_gen output) as truth.

### Q5: sunflower and matamatrix()?
- **Answer:** refuse both by name with advice (as contour is today) and list them in the help; drawing them is deferred.

### Q6: Batch ordering?
- **Answer:** silent drops (S1) first, then values twoway accepts but dash refuses, then named-not-drawn options, then fidelity, then docs/tests. Each batch leaves the tree releasable.

## Category 2: Users & Context

### Q7: Who executes the sections?
- **Answer:** autonomous coding agents in parallel worktrees, merged by an orchestrator with `patch -p1`, as WP-29/WP-30 ran; the orchestrator runs the batch-end gates.

### Q8: Parallelism within a batch?
- **Answer:** up to three sections at once, matching `scripts/stata_slot.sh`.

### Q9: Batch size?
- **Answer:** two to three sections per batch, each one to four tasks, so a batch lands in one session; many small batches.

### Q10: The user the plan optimises for?
- **Answer:** a Stata user pasting an existing twoway command after `dash`, expecting the same picture and numbers; fidelity to twoway's output and refusals first, dash's extensions second.

## Category 3: Integration Points

### Q11: New Python dependencies allowed?
- **Answer:** any dependency that helps, declared in dash_setup (e.g. scipy for thin-plate-spline interpolation). dash_setup, dash.pkg, the help and the requirements files must learn each one.

### Q12: Source of Stata truth for new fixtures?
- **Answer:** measured on this machine's StataNow 19.5 with a committed `scripts/extract_*_truth.do` per fixture, as WP-30 did; no hand-typed truth.

### Q13: Which twin for new computed work (saved-page JS vs served Python)?
- **Answer:** both, with one shared truth fixture and a parity entry in `test_mode_parity.py`; no saved/served divergence introduced.

### Q14: Where is tracking kept?
- **Answer:** in GAPS3.md: a "Tracked:" line per row, with `test_tracking_documents.py` taught to read it (the WP-28 reader pattern); GAPS2.md and DROPIN-REMAINING.md stay read-only.

## Category 4: Edge Cases

### Q15: Options twoway refuses on a type (GAPS3 C3)?
- **Answer:** refuse with twoway's rc and wording on every type, measured per option x type pair; a per-type applicability column in the rules table.

### Q16: Tests that pin today's picture?
- **Answer:** flip each to twoway's picture with the reason in its docstring; never delete (the WP-29 rule).

### Q17: Edge cases twoway has not been measured on?
- **Answer:** measure first with a committed extract script; match twoway; if twoway errors, copy its return code and message. **Scheme files use only RGB values and Stata's RGBA syntax (`"r g b"` with `%opacity`); other colour spaces (CMYK, HSV, intensity forms) are out of scope for scheme files** -- the D1 residual and GAPS3 E5's scheme half are closed by decision.

### Q18: Where the saved page cannot match the served app?
- **Answer:** a visible cue naming what is frozen, as fits have today; never a silent difference.

## Category 5: Quality Attributes

### Q19: Test tier a section runs before hand-back?
- **Answer:** only its own new and directly covering tests plus the cscript it changed; the full suite and `make cert` run once at batch end.

### Q20: Performance bound for new computed layers?
- **Answer:** no slower than the existing estimators: under 2 s for 100,000 rows in Python, with a timing test (the test_estimator_cost.py bound).

### Q21: Security guards?
- **Answer:** no section may weaken a guard; new HTML or JS goes through the existing escaping and nonce paths; test_csp.py and test_serve_token.py stay green.

### Q22: Findings a section cannot fix?
- **Answer:** a BUGS.md entry marked open, a GAPS3 Tracked line saying so, and a one-line note in the hand-back; never silently dropped.

## Category 6: Existing Patterns

### Q23: Test shape?
- **Answer:** one `test/test_wp31_truth.cscript` with a block per section, plus a pytest file per item (the WP-30 shape the cert runner already knows).

### Q24: Tracking-foundation section first?
- **Answer:** yes: Section 01 adds the GAPS3 "Tracked:" reader, opens one BUGS.md entry per in-scope row, and pins them; the closeout proves none is left open.

### Q25: Where new drawing code lands?
- **Answer:** in the shared glyph layer and helpers the server copies by name, so both modes get it; never in the template alone; test_mode_parity.py proves the copy.

### Q26: What a section updates when it draws an option?
- **Answer:** the pending list in dash.ado, the help's Unsupported section and TWOWAY_COVERAGE_AUDIT.md in the same commit; test_help_conformance.py proves it.

## Category 7: Preferences & Tradeoffs

### Q27: Port the eleven estimators to JavaScript (GAPS3 F1)?
- **Answer:** yes, all eleven (lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband, mspline), one or two per section, each pinned to its Python twin; this retires decision WP-29 M3.

### Q28: Plot-type abbreviation superset (GAPS3 A2)?
- **Answer:** refuse them with twoway's "is not a twoway plot type" r(198); existing tests and examples that use the short names change.

### Q29: Module split (GAPS3 K5)?
- **Answer:** out of scope; noted as a follow-up.

### Q30: Fidelity bar for cosmetic defaults?
- **Answer:** match twoway's scheme-driven layout where Bokeh can express it; where it cannot, document the difference in the help with a measured example.

## Category 8: Business Model (release and distribution)

### Q31: Licence?
- **Answer:** do not write a LICENSE file. GAPS3 I2's licence part is closed by decision; README, dash.pkg Author/KW lines and the install line remain.

### Q32: Distribution?
- **Answer:** GitHub (`net install` from the repository) now; SSC later. README carries the install line; dash.pkg gains the Author and KW lines SSC needs.

### Q33: Version at closeout?
- **Answer:** stay at 0.1.0; only the date moves (every shipped file and dash.pkg's Distribution-Date), and the pin test extends to the `v2.0`/`1.0.0` headers GAPS3 I5 found.

## Category 9: Visual & UX Vision

### Q34: Accessibility deliverable (GAPS3 K6)?
- **Answer:** keyboard-reachable widgets, ARIA labels on every filter, KPI card and tab, an accessible name on each figure, colour-contrast checks for the shipped schemes; verified with an automated checker in headless Chrome.

### Q35: Dashboard extensions to include (GAPS3 H2)?
- **Answer (all, plus one new):** (a) **formatted tables containing the data displayed in the graph** (new requirement, detailed in Q38-Q40); (b) KPI weights and kurtosis/semean/range; (c) multi-select dropdown, a "(missing)" option, slider direction and a reset button; (d) more than one link group and brush-as-filter; (e) print stylesheet and PNG/SVG export including KPI cards, title, filters and tabs.

### Q36: Message style?
- **Answer:** twoway's own wording and return code where twoway has one; otherwise one plain sentence naming the option and what dash did instead.

### Q37: Minor-tick labels?
- **Answer:** a second label set drawn along the axis at the minor positions, in the scheme's minor-label size (Bokeh extra ticker + LabelSet).

### Q38: Data table placement (new requirement)?
- **Answer:** below its graph, opened by a per-graph option such as `table()`, folded away by default with a toggle; the layout is unchanged until opened.

### Q39: Table content?
- **Answer:** the rows the graph currently draws (after filters, brush and qualifiers) and the variables it plots plus `hover()` variables, each in its Stata display format and value labels; the CSV download's column rules apply; follows every move as the glyphs do.

### Q40: Table size behaviour?
- **Answer:** virtual scrolling through all drawn rows, sortable by column, a per-table row cap that falls back to the first N rows plus a note (Bokeh DataTable, both modes).

---

## Discovery Summary
- Total questions asked: 40
- Categories fully covered: all 9 (Business Model read as release/distribution)
- Categories partially covered: none
- Categories skipped: none
- Key themes:
  - Scope = GAPS3 4.A-4.G, 4.J-4.K, accessibility (K6), dashboard extensions (H2) plus a new **per-graph data table**; the platform package and the module split stay out.
  - contour/contourline drawn via a Python+JavaScript reimplementation of twoway's interpolation if Bokeh can draw contours (research confirms); rpcap/rpspike drawn; sunflower/matamatrix refused by name.
  - All eleven estimators ported to JavaScript so the saved page refits (retires WP-29 M3); every new computed layer ships both twins with one shared truth fixture and a parity entry.
  - Refuse like twoway: inapplicable options per type, the abbreviation superset, measured first with committed extract scripts; copy twoway's rc and words.
  - Scheme files: RGB and Stata's RGBA syntax only.
  - Many small batches (2-3 sections of 1-4 tasks), three in parallel, each batch ending with the full suite and `make cert`; done = every row closed with a BUGS entry and a pinning test, gates green.
  - Tracking moves to GAPS3.md "Tracked:" lines read by test_tracking_documents.py; Section 01 is the tracking foundation.
  - New dependencies allowed if declared in dash_setup; no LICENSE; version stays 0.1.0 with a new date; GitHub distribution now.
