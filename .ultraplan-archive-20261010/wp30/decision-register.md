# WP-30 decision register

Built 03oct2026 at c96facd (branch wp30-p1). Sources: every `decisions` entry in the WP-30 research (135 questions, ids P1.n.1..k in research order) and every decision raised in the research notes' "Critic additions" (ids continue the item's numbering and are marked [C]). Binding answers: `.ultraplan/wp30/decisions.md` M1-M12.

- **Source column.** M1..M12: answered by that maintainer decision. A1..A137: architect ruling, taken from the researcher's (or critic's) recommendation unless the "why" says it differs. `M5`-refusals use twoway's return code and words; each newly refused form gets a CHANGELOG line under "Changed behaviour (may need your do-files changed)".
- **Counts.** 235 rulings on P1 items (135 research questions, 95 critic-raised [C], 5 research residuals), plus 5 cross-cutting (X). 115 rest on an M decision (100 on M alone, 15 with an architect detail) and 120 are architect rulings A1..A137 (137 ids include the X rows). 26 rows refuse under M5; 11 apply M6 (no note where twoway is silent).
- **Fold rule.** A proposed scope addition is folded in when it has the same root cause and the same code; otherwise it is filed as a new P2 residual (P2.42-P2.57 below; P2.49 withdrawn by ratification row 27) or sent to the existing item that owns it.
- **Every "defer to the §4 Refuse vs note decision"** answer is resolved by M5; every "drew nothing / note where twoway is silent" answer by M6; every "run Stata 16-18.5" answer is NO (M2).

## For ratification

The one list the maintainer answers before batch 1 is index.md "Decisions for maintainer ratification" (44 rows, consolidated 06oct2026; A151). **Answered 06oct2026:** 35 rows ratified as recommended; rows 4, 8, 12, 22, 25, 27, 32 and 36 CHANGED, and row 29 answered otherwise than recommended. Each changed ruling below and in the table carries its ratified answer, which binds over the original text (index.md holds the maintainer's words). Rows 1-28 are the architect rulings listed in the next section, in the same order. Rows 29-41:

29. **P-1 (precondition of step 0a).** `PhilSchummSuggestion.md` is tracked in the package root, so `test_packaging.py`'s root test is red at `c96facd` (re-run 06oct2026: 1 failed, 1 passed, 11 deselected). Recommendation: the maintainer runs `git mv PhilSchummSuggestion.md .ultraplan/handoff/` in a commit of their own before step 0a. Affects step 0a (G0), S01 and every full run. **Answered 06oct2026:** ignore the file in the packaging root test (`PhilSchummSuggestion.md` added to `test/test_packaging.py::_ROOT_ALSO`, uncommitted; it lands before step 0a after one full run). 
30. **S08 Q1 (P1.12.4).** Should absolute units also follow a graph's `xsize()`/`ysize()`? Recommendation (b): no; P1.12.4 narrows to the scheme's `graphsize`, and S58 files a P2 row. Affects S08 (S58).
31. **Batch-4 A139 exception.** `_dash_plot` edited by S10 and S12; `_needed` by S10, S11 and S12, in disjoint hunks. Recommendation: grant. Affects S10, S11, S12.
32. **S11 Q-11.1.** A blank quoted stylelist element is read as `.` where twoway refuses it (an M5 exception). Recommendation: ratify. Affects S11. **Ratified 06oct2026, CHANGED:** refuse r(198) with dash's own clear message; the element is not read as `.` and there is no M5 exception.
33. **S12, P1.27.6.** `$dash__display` also fences SB-07..SB-11. Recommendation: ratify. Affects S12.
34. **S13 D-13b.** Line widths over 10,000 units known only at draw time are noted and drawn at the default, not refused (an M5 exception). Recommendation: ratify. Affects S13.
35. **S22 Q-22.1, P1.28.3 (with row 16).** The stale-graph note only on file-writing commands. Recommendation: ratify. Affects S22.
36. **S28 Q-28.1.** The by() panel label's filled box: a P2 item, or S53's? Recommendation: P2 item (S58). Affects S28, S53, S58. **Ratified 06oct2026, CHANGED:** add to S53 (S53 draws twoway's filled box behind each by() panel label); S58 files no P2 row for it.
37. **S33 Q1 (A139, batch 11).** `color_idx=` on one call line in seven mappers S32 edits. Recommendation: grant. Affects S32, S33.
38. **S34 Q1 (R12, batch 12).** Four one-line `_generate_app_source` edits beside S35. Recommendation: grant. Affects S34, S35 (S38 if refused).
39. **S36 D-36c.** 57 Stata-known style names outside the table drawn in default attributes and named. Recommendation: ratify. Affects S36 (S58).
40. **S45 Q-45.1 (A60, P1.16.5).** `type` is the drawn type and `recast_from` the typed one. Recommendation: ratify. Affects S45 (S19, S40, S49).
41. **S48 Q-48.2.** `iscale()` above 10,000 refused r(198). Recommendation: ratify. Affects S48.

## Architect rulings for maintainer ratification

Only rulings users will notice, security trade-offs, numeric limits and accepted approximations.

1. **A6** (P1.3.1, P1.20.4): plot-region margin converted at build to a per-axis fraction; up to about 0.8% of the width (about 11 px at 1400x560) off twoway. Accepted as exact enough, documented.
2. **A8** (P1.3.5): default %td-%th axes take the fitted tsnatscale model, which agrees with twoway on 52-66% of ranges (98% on %ty). The rest stays tracked in P2.19.
3. **A9** (P1.3.8): re-finish budget. Served: at most 0.2 s added per figure per filter move at 500k rows. Saved: 100 by() panels settle within 1 s of HEAD's measured time.
4. **A10** (P1.4.4): an unread user-scheme key is noted only if it is on a committed list of keys twoway draws and dash does not. At most 10 names plus a count; every other key is silent. **Ratified 06oct2026, CHANGED:** no unread-key note at all; the scheme parser keeps reading and retaining every directive (none discarded) so later versions can draw them.
5. **A28** (P1.10.3): new limit `added_text`: default 1,000, ceiling 100,000, `$dash_max_added_text`. It counts texts x by() panels over the dashboard and refuses r(134) beyond the limit.
6. **A68** (P1.21.3): new limit `reflines`: default 10,000, ceiling 100,000, `$dash_max_reflines`. It counts positions x panels over the dashboard and refuses r(134). The researcher proposed a note; this follows the existing limit framework instead.
7. **A35** (P1.11.5): `$$…$$` and `\(…\)` in user text are drawn as typed (twoway), with no opt-in. Existing TeX titles change.
8. **A34** (P1.11.4): `{c 0}` and C0/C1 control codes are dropped, not mirrored. This is a small documented difference kept for safety. **Ratified 06oct2026, CHANGED:** mirror twoway: a label holding `{c 0}` is emptied; C0/C1 codes are kept and escaped at every HTML/JS sink (rule 1).
9. **A53, A54** (P1.15.5-6): date by() panel titles keep dash's date text (twoway shows 14610). cols() is honoured up to the by_groups limit (100, ceiling 1,000), then clamped with a note.
10. **A56, A58** (P1.16.1, .3): twoway's "first equals last" axis-title rule. Fit keys change (e.g. "lowess mpg weight", "Median bands"); there is no opt-out.
11. **A76** (P1.23.3): a mixed date axis is drawn through a CustomJSTransform, one more `new Function` consumer under `'unsafe-eval'`.
12. **A77** (P1.23.4): a literal coordinate outside 0100-9999 on a date axis is dropped with a note; twoway draws it. **Ratified 06oct2026, CHANGED:** draw it, with no note; S35's Python and JS date conversion handles such values safely.
13. **A82, A84** (P1.26.2, .4): notes take twoway's form `(note: …)` in text colour. They are shown under `quietly`, hidden by `capture`, and no longer red Python warnings.
14. **A83** (P1.26.3): `dash build, server` always runs the trial render (up to the saved build's own time, e.g. ~28 s for lowess at 100k). For `dash serve`, the child's warm-up is the trial and is never run twice; this differs from the researcher.
15. **A88, A89** (P1.27.1, .4): no browser opens in batch mode or under `set graphics off`. Interactive console Stata still opens one, which is a deliberate asymmetry.
16. **A93, A96** (P1.28.3, .6): the stale-graph note prints once per dash command, only when a Stata graph is in memory. `r(filename)` is an absolute path, and for previews it is transient.
17. **A99, A101, A102** (P1.29.3, .5, .6):
    - The `python app.py` header keeps `'unsafe-inline'`; the meta nonce governs.
    - script-src drops `'unsafe-inline'` with no CSP1 fallback, so CSP1-only browsers show a blank page.
    - The served script-src is nonce-only if the browser test is clean; otherwise it keeps `'self'`.
18. **A104** (P1.30.3): "verified" means major.minor, so patch releases inherit the minor's text-sink XSS verification.
19. **A107, A109** (P1.30.6, .9): a venv dash did not create is never downgraded. The internals guards fail closed, so the server refuses to start if a Bokeh changes the hooks.
20. **A110, A111** (P1.31.1-2): at most 20 concurrent sessions by default (`maxsessions()`). Idle sessions close after 60 minutes of no filter, brush or CSV activity, so a tab only being looked at can need a reload.
21. **A113** (P1.31.4): one recompute worker. The worst documented wait is cap x recompute, about 3 min at 20 x 8.7 s for lowess at 100k.
22. **A116, A117** (P1.31.7-8): per-session RSS growth must stay at or below 40 MB at 200k x 3 (60.7 MB today). The estimator memo holds 64 MB per process (LRU) and stays out of Stata's process. **Ratified 06oct2026, CHANGED:** the per-session growth bound is 80 MB at 200k rows x 3; the 64 MB memo is unchanged.
23. **A119** (P1.31.10): the busy page is a static HTTP 503 with Retry-After and no auto-refresh.
24. **A121** (P1.32.1): numpy or pandas below dash_setup's minimums gets a note, not a refusal.
25. **A125** (P1.33.4): the release gate gains a floor-Python leg (time cost on every release). **Ratified 06oct2026, CHANGED:** manual only: S05 measures the floor Python once in WP-30; the release gate gains no leg.
26. **A129** (P1.34.3): `regen_option_surface.py` and `wire_option_reporting.py` are retired. They refuse to run.
27. **A37** (P1.12.6): the brushed-glyph styling bug (nonselection and muted glyphs keep creation values) is left to P2.49 although it is wrong output today. **Ratified 06oct2026, CHANGED:** fix in WP-30: S08 syncs the nonselection and muted copies; P2.49 is not filed (its id is withdrawn, not reused).
28. **A80** (P1.25.6): served dashboards with per-graph schemes change: each graph gets its own scheme, as on the saved page.

## Strict readings of M decisions that differ from the research recommendation

- **P1.12.1 (M1):** size units take option B, one Stata unit for every class (researcher: A, per-class anchors). Default markers go from 8 to 5.87 px and lines from 1.5 to 1.15 px.
- **P1.35.3 (M2):** all 91 `version 16.0` lines become `version 19` (researcher: keep 16.0).
- **P1.20.7 (M1):** `bgcolor()` takes twoway's canvas semantics (critic: keep the documented difference). A lone `bgcolor(red)` no longer shows.
- **P1.3.6 (M1):** explicit-value axes re-hull their data part after a move. dash.sthlp:2852 "holds across filter moves" is rewritten.
- **M5 refusals where the research said "note until §4":**
  - P1.5.1 `format(bogus)`;
  - P1.6.4 x-option date literals;
  - P1.9.2 `horizontal` on refusing types;
  - P1.10.1 unknown text() sub-options;
  - P1.19.1, P1.19.2 and P1.19.4 capitals, spellings and bad legend values;
  - P1.20.1 region typos;
  - P1.27.7 `saving(my file.html)` and the `twow`/`gra` prefixes;
  - P1.8.2 uses twoway's words, not reworded ones.
- **M5 for the comma form:** `"255,0,128"` is refused (P1.13.3), so HC2-16p and the P1.1 "comma extension" are dropped.
- **M6 silences:**
  - P1.1.1's transition note (critic option d);
  - P1.18.1's once-per-graph note;
  - P1.15.8's dropped-level note;
  - P1.13.3's short-hex note.
- **P1.30.8 (M9):** the served app refuses below bokeh 3.8 (critic: note only).

## New P2 residuals filed by this register

| Id | Residual | From |
|---|---|---|
| P2.42 | cmissing(n) on area/rarea and connect() (incl. c(J)) on rarea are noted, not drawn | P1.8.3 |
| P2.43 | cmissing(n) at missing points generated by lowess, fpfit, lpoly, mband, mspline | P1.8.7 |
| P2.44 | recast() from histogram to range types stays noted | P1.8.7 |
| P2.45 | Each distinct tick format ships its own 33 KB format-writer model; share one per page | P1.5.3 |
| P2.46 | An empty trailing `\|\| , options` segment is refused r(198); twoway accepts it | P1.10.6 |
| P2.47 | SMCL beyond graph_text's documented tags ({hline}, {space}, {dup}, {cmd:}/{hi:}, {ccl}, {center:}, links) drawn as typed | P1.11.2 |
| P2.48 | The served bundle still ships bokeh-mathjax (1.79 MB per session) | P1.11.6 |
| P2.49 | Withdrawn (ratification row 27, 06oct2026): fixed by S08 in WP-30, not filed. Was: option appliers leave nonselection/muted glyphs at creation size, width, colour and alpha | P1.12.6 |
| P2.50 | Keys with the same text and style are not merged into one | P1.16.2 |
| P2.51 | Histogram-only graphs draw a legend; twoway draws none | P1.16.2 |
| P2.52 | The first-used axis is not drawn left/bottom | P1.16.2 |
| P2.53 | graphregion(margin()) noted, not drawn (exact outer margin) | P1.20.2 |
| P2.54 | An out-of-range xline/yline is clipped at the frame; twoway draws it outside the plot region | P1.21.7 |
| P2.55 | User-written and third-party `*.style` files on the ado-path (textboxstyle, color) are not read | P1.24.3, P1.25.7 |
| P2.56 | `dash twoway` with nothing after it is refused; twoway draws an empty graph | P1.27.8 |
| P2.57 | A served session's make_document runs on the event loop (1.6-4.6 s at 100-200k rows) | P1.31.11 |

Existing items whose scope changes:
- **Closed by WP-30:** P2.11's sm* sizes (P1.4.6), P2.12's `lwidth(none)` (P1.12.7) and P2.13's "4-inch reference" (P1.12.4).
- **Removed:** P3.2 loses `xvarformat()`/`yvarformat()` (P1.5.5).
- **Gains work:**
  - P3.9 gains `requirements-dev.txt` (P1.30.5).
  - P3.11 gains the beforeprint JS (P1.28.5).
  - P3.7 keeps the old extractors' paths (P1.34.5).
  - P2.14 keeps weights with operators (P1.7.3).

## Cross-cutting rulings

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| X.1 | [C] The served copy lists in `_glyph_layer_lines` are a hot spot (P1.2, 7, 10, 14, 19, 21, 28, 30) | Append only. One test asserts that every listed name exists, since the copy loop skips a missing name silently. | A133 | A misspelt name is a served-only NameError. |
| X.2 | [C] Items that add or reword notes | P1.26-A lands first. Every new note uses its channel, and tests use its needles. | A134 | Otherwise the needles migrate twice. |
| X.3 | [C] Case-id and fixture collisions (P1.27/P1.29 SB-21..24, PV-28; HON-3x in P1.30/32/33) | The plan assigns id ranges per item and keeps one saving-characters fixture (P1.29's `saving_chars_truth.json`). | A135 | Avoids duplicate ids. |
| X.4 | [C] Where new twoway-truth cscript cases go | `test/test_wp30_truth.cscript` (one script per package; hygiene count pinned). | A136 | WP-28/WP-29 precedent. |
| X.5 | [C] New functions and programs | Each gets its `function_test_map.py` / `program_coverage_map.py` entry, and Mata ones their `_needed` entry, in the same commit. | A137 | The registries fail the suite otherwise. |

## Register

### P1.1 Stylelists

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.1.1 | One style value on several y: style the first y only? | Match twoway: pad with `.`, so only y1 takes it. Silent: the critic's option (d), a transition note, is rejected. CHANGELOG "Results that change". | M1, M6 | twoway styles y1 only and prints nothing. |
| P1.1.2 | Unquoted `mcolor(255 0 0)`? | Three elements, as twoway reads it; `255` is an unknown colour (note, P1.13.1's black). Help: quote RGB; fix dash.sthlp:786-788. CHANGELOG before/after (single y changes too). The comma form goes per P1.13.3. | M1, M5 | twoway's reading; the comma form is r(198) in twoway. |
| P1.1.3 | malpha/lalpha/falpha/jseed: lists or scalars? | Scalars applied to every series, as today; documented. | A1 | dash-only options; no twoway truth. |
| P1.1.4 | What does an unknown element draw? | twoway's default attributes (black, circle, medium), with a note naming the element. | M1 | twoway draws defaults and notes. |
| P1.1.5 | Misplaced `..`; dash's stricter jitter/barwidth checks? | Refuse a misplaced `..` r(198) `<opt>(<value>):  invalid syntax`. Keep the documented jitter 0-100 and barwidth>0 checks, on used elements only, after resolving `.`, `=` and `..`. | M5, A2 | M5 covers the refusal. "dash refuses what twoway accepts" stays P2.14. |
| P1.1.6 | [C] mlabel shorthands? | Refuse `..` r(198) `.. not allowed in option mlabel()` and `=` r(101) `=exp not allowed`. `.` is allowed and omits that series' labels. | M5 | Measured twoway refusals. |
| P1.1.7 | [C] Validate elements past the number of y? | Style kinds only for used elements (extras ignored, silent); every mlabel variable is checked, r(111) `variable X not found`. | M5, M6 | twoway's measured split. |

### P1.2 Default look

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.2.1 | Vertical y tick labels as the schemes draw them? | Yes; `ylabel(, angle(0))` is the escape. Flip test_server.py:4001 with the reason. | M1 | Scheme look. |
| P1.2.2 | Opaque markers? | Opaque unless `%NN` or malpha(), including rconnected's markers. | M1 | M1 names "no default alpha 0.8". |
| P1.2.3 | Accept that every dashboard's look changes? | Accept, no option; CHANGELOG "Results that change". | M1 | Binding. |
| P1.2.4 | Split P1.2? | P1.2a chrome; P1.2b intensity, batched with P1.4 and P1.13. | A3 | Batches stay at 3 items or fewer; the shared blend edits stay together. |
| P1.2.5 | [C] fintensity above 5000? | Never refused. One shared intensity function with P1.13's measured f>1 clamp (navy at 6000 and above gives #010304). | M1 | twoway accepts any number. |
| P1.2.6 | [C] Economist's note: own row or title band? | Title band, as twoway draws it. | M1 | Scheme look. |
| P1.2.7 | [C] Owners of shared work? | P1.3 owns the minor-tick bullet and the test_help_claims_8 BasicTicker flips. P1.2a owns the extractor and scheme regeneration first. P1.4, P1.13, P1.3, P1.12 and P1.25A add keys and regenerate in landing order, one regeneration commit per batch, never hand-edited. | A4 | One owner per shared file. |
| P1.2.8 | [C] User schemes' `intensity bar`/`intensity area`? | No longer read, and silent. | M1, M6 | twoway ignores both (measured). |
| P1.2.9 | [C] dash's own `.db-title` header? | Unchanged. | A5 | A dash-only DOM header, not a twoway element. |

### P1.3 Default ticker and padding

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.3.1 | How to express twoway's plot-region margin? | (b): r x min(W,H) (r=0.022; economist 0.006) converted at build to a per-axis fraction from xsize/ysize or graphsize. The error is documented. | M1, A6 | M1 binds the padding. (a) depends on BokehJS internals (P1.30). |
| P1.3.2 | Default and #N axes after a filter move? | Re-tick and re-range over the kept rows in both modes, including y2/x2 (fixed Range1d today). | M1 | twoway's answer for the same `if`. |
| P1.3.3 | Ticks on zoom/pan? | natscale over the visible range (the same JS port). | A7 | twoway has no zoom; keeps labels at any depth. |
| P1.3.4 | Accept changed default axes, no opt-out? | Accept; CHANGELOG. | M1 | Already decided by M1. |
| P1.3.5 | Fitted tsnatscale model on %td-%th? | Adopt it as the default; agreement rates stated in help/BUGS; P2.19 keeps the remainder. | M1, A8 | Beats Bokeh's DatetimeTicker on the measured case. |
| P1.3.6 | [C] Explicit-value axes after a move? | Re-hull the data part and keep the label positions; rewrite dash.sthlp:2852; CHANGELOG. | M1 | twoway's `if` behaviour. |
| P1.3.7 | [C] Default bases before P1.17b? | (a): P1.3-A drops default-base constants from the tick input and hull, and an explicit base() stays. P1.17b lands in the same or the next batch. Taken jointly with P1.17.2. | M1 | twoway's scale ignores default bases (B01-B06). |
| P1.3.8 | [C] Re-finish time budget? | Served: at most 0.2 s added per figure per move at 500k rows, through a vectorised reader, with a timed test. Saved: 100 panels within 1 s of HEAD's settle time. | A9 | Today's reader takes 0.58 s per 500k figure. |

### P1.4 Scheme keys on every layer

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.4.1 | Unit of the default marker-label size? | Stata's text ladder via `_gsize`; mlabsize() follows in P1.12. | M1 | Size units. |
| P1.4.2 | twoway's histogram style on every histogram layer? | Yes. | M1 | Scheme look. |
| P1.4.3 | rarea opacity? | area's rule (opaque; 0.2 under sttrans). | M1 | Scheme look. |
| P1.4.4 | Verbosity of the unread user-scheme note? | Critic option (d): a committed allow-list of twoway-visible keys dash does not draw. At most 10 names plus a count, once per build. Silent for the shipped schemes and the 5 shipped-but-unread keys. PLUS and third-party schemes count as user schemes. **Ratified 06oct2026 (row 4), CHANGED:** no note; every directive is retained in the parsed scheme. | M6, A10 | Note only what dash draws differently; a copied s2color has 1,981 unread keys. |
| P1.4.5 | Fold in the symbol cycle, the p#mark key fix and the malpha-refills-hollow bug? | Fold in all three. The p#mark change flips TestMarkColourIsForMarkers, the p_mark_colors chain and dash.sthlp:3363-3365, each with the reason. | A11 | Same root cause and helpers. |
| P1.4.6 | [C] Scope of the sm* factor? | (b): also apply it to msymbol(sm*), after msize() inside `_apply_marker_opts`. Closes P2.11's sm* size sub-claim. | M1, A12 | Same helper; one graph must not mix scheme-small and user-full sm*. |
| P1.4.7 | [C] Side finding (h) reverses a tested fix? | Fold in (P1.4.5), before or with P1.13's step 2 (P1.13.7). | M1 | twoway does not read `color p#mark` (measured). |

### P1.5 Axis format fallbacks

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.5.1 | format(bogus) on an axis? | Refuse r(198) `invalid format, bogus`. | M5 | twoway refuses. |
| P1.5.2 | format(%12s) on a numeric axis? | Write %9.0g with one note. | M5, M6 | twoway accepts; the text can differ (1.200e+08 vs 1.20e+08). |
| P1.5.3 | Page size of per-format writers? | Accept one 33,408-char model per distinct format; file P2.45. | A13 | +70-100 KB on a 1.3 MB page; sharing touches both templates and P1.29. |
| P1.5.4 | Stata floor for this truth? | 19.5 only; the fixture records stata_version. | M2 | No old binaries. |
| P1.5.5 | [C] xvarformat()/yvarformat()? | Fold into P1.5a (the new helper reads the layer option); remove from P3.2. | A14 | Same root cause and helper. |
| P1.5.6 | [C] Colour-key label format? | Fold into P1.23b. First measure twoway's fixed key format (UNCLEAR: %7.0gc or %8.0gc); honour zlabel(, format()) for any format. | A15 | Same code and root cause as P1.23.2. |
| P1.5.7 | [C] Narrow-width writer defect (%e, %g, %f fallback)? | Its own BUGS.md entry and failing test, landed first in P1.5a. format_truth.json is regenerated by its extractor. | A16 | Silent wrong output in KPI, mlabel, hover and axes (rule 7). |
| P1.5.8 | [C] One rule for refused formats? | A format twoway refuses is refused with its rc and words. One twoway accepts but dash cannot write exactly draws %9.0g with one note. | M5, M6 | One stated rule. |

### P1.6 tsline time-axis options

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.6.1 | Date literals in t-options when the first plot is lfit/kdensity/…? | Refuse r(198), as twoway does. | M5 | twoway refuses. |
| P1.6.2 | Left-aligned %-t quirk? | Match: accept in tlabel/ttick, refuse in tline/tscale(range()). | M5 | twoway's refusals. |
| P1.6.3 | format() overrides of the date unit? | Model the tickset format state machine, in 6b. | M5 | Refuse exactly what twoway refuses. |
| P1.6.4 | x-options with date literals? | Refuse in P1.6 with twoway's codes (r198/r198/r121), through the same validator. | M5 | In the area P1.6 touches. |
| P1.6.5 | Too-short tm(), ts()? | Refuse r(198). | M5 | twoway refuses. |
| P1.6.6 | [C] How to evaluate date tokens? | Mata's string functions (`date()`, `weekly()`, `monthly()`, `quarterly()`, `halfyearly()`, `yearly()`); never `_stata()` on user text. Number-first; whitelist gate; the test asserts that no `_stata` call takes user text. | A17 | Removes a command-injection path (rule 1); same values on 78 tokens. |
| P1.6.7 | [C] Unit frozen at registration, format read at build? | Store each axis's registration unit; at build, note when the axis variable's date kind differs. | A18 | Matches P0.6's frozen points and tells the user. |
| P1.6.8 | [C] tscale(log) on a date axis? | Keep the note; list it as an inherited divergence. | M5 | A valid option dash cannot draw is noted. |
| P1.6.9 | [C] Mixed axis if P1.23 lands later? | Land P1.23 step 5 before P1.6a. | A19 | (b) would refuse what twoway accepts. |

### P1.7 Time-series operators

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.7.1 | by() with an operated plot variable? | Refuse r(5) `not sorted`, followed by one dash hint line. | M5 | twoway refuses. |
| P1.7.2 | CSV header for an operator column? | The expression as typed, `L.close`. | A20 | What the user wrote; no name collision. |
| P1.7.3 | Weights with operators? | Leave them to P2.14 (not P1.14), reusing P1.7's generator. | A21 | Different root cause. |
| P1.7.4 | Stata floor for this behaviour? | 19.5 only. | M2 | No old binaries. |
| P1.7.5 | [C] Format of D./S. of a %t base? | Carry the base's %t format, as twoway; add a help sentence. | M1 | Drop-in look. |

### P1.8 connect(), cmissing(), recast()

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.8.1 | Reproduce recast()'s out-of-group fallbacks? | Mimic them (yx→scatter, range→rspike, pc→pcspike; function and dot ignore it), with twoway's note. | A22 | A cheap ptype rewrite; same picture. |
| P1.8.2 | recast() on *ci fits; unknown cmissing()? | Refuse r(198) `recastas() option not allowed`. Unknown cmissing: r(101) in twoway's words; a dash hint line may follow. | M5 | twoway refuses. |
| P1.8.3 | cmissing(n) on area/rarea, connect() on rarea? | Keep them noted; file P2.42. | M5, A23 | A valid option dash cannot draw is noted; Patches would be new JS. |
| P1.8.4 | function bridges interior missing regions? | Yes, by default; it breaks under cmissing(n). | M1 | twoway's picture. |
| P1.8.5 | connect()/cmissing() where twoway draws the same picture? | Silent. | M6 | twoway is silent. |
| P1.8.6 | [C] Stairsteps lose hover (Step has no hit test)? | Pre-expanded stair vertices on a Line, rebuilt by `_FILTER_JS` after a move. The c(i) line stays out of HoverTool. | A24 | No loss of today's tooltips, in both modes. |
| P1.8.7 | Research residuals: estimator-generated missing points; histogram→range recasts | File P2.43 and P2.44. | A25 | Different code. |

### P1.9 horizontal

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.9.1 | `horizontal vertical` together? | Refuse r(198) `may not combine options horizontal and vertical`. | M5 | twoway refuses. |
| P1.9.2 | horizontal on the 16 refusing types; vertical on kdensity/function? | Refuse r(198) in twoway's words, on the effective (recast) type, in P1.9b after P1.8b. | M5 | twoway refuses; `recast(bar) horizontal` is rc 0. |
| P1.9.3 | How far on default axis titles? | First-layer swap only; P1.16 does the multi-layer rule. | A26 | Avoids two edits of HIGH `_dash_axis_labels`. |
| P1.9.4 | [C] Order against P1.5, P1.17a, P1.23? | P1.5, P1.17a and P1.23's partition first, then P1.9a, P1.16, P1.8b, P1.9b. | A27 | Matches the three sibling notes. |

### P1.10 text() and ttext()

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.10.1 | Malformed points, missing axis pairs, unknown sub-options? | Refuse all r(198) in twoway's words (e.g. `invalid point, BAD 30`). | M5 | twoway refuses. |
| P1.10.2 | Textbox sub-options Bokeh cannot draw? | Note them and list them in the help. | M5 | Valid option, cannot draw. |
| P1.10.3 | Cap the number of added texts? | `added_text` row (default 1,000, ceiling 100,000, global), counted as texts x panels over the dashboard; r(134) beyond. | A28 | A per-graph cap does not bound by() (1,000 x 1,000 Labels). |
| P1.10.4 | How do copies reach the renderer? | Structured `added_text` JSON built in Stata. Sub-options stay in one `opts` string; x, y and axis are JSON numbers. | A29 | Stata's own tokenizer; avoids substring key hits. |
| P1.10.5 | [C] Where are added-text notes raised? | In Stata, once, for both modes. | A30 | Served renderer notes never reach Stata. |
| P1.10.6 | [C] `\|\| , opts` refused? | File P2.46; AT-04 must not use that form. | A32 | Different code (segment parser). |

### P1.11 SMCL and TeX

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.11.1 | Inline styles and sup/sub that Unicode cannot express? | Unicode only, plus one note otherwise. | A31 | No MathJax (+1.79 MB, TeX parser). |
| P1.11.2 | SMCL beyond the documented tags? | Documented set only; the rest drawn as typed and listed in the help; file P2.47. | A32 | Bounded scope. |
| P1.11.3 | SMCL in dash-only DOM sinks? | Translate characters and symbols and strip style tags. KPI/dashboard titles and tabs() stay raw. Data-borne text (string tooltips, value-label tooltip columns, CSV) stays raw, as the help states. | A33 | Consistent labels. |
| P1.11.4 | `{c 0}` and C0/C1 codes? | Drop them; documented. **Ratified 06oct2026 (row 8), CHANGED:** mirror twoway: `{c 0}` empties its label; C0/C1 codes are kept and escaped at every HTML/JS sink. | A34 | Keeps control characters out of the page (rule 1). |
| P1.11.5 | [C] User-typed TeX? | Drawn as typed, as twoway does, with no opt-in; CHANGELOG "Changed". | A35 | Matches twoway and closes MathJax's parser. |
| P1.11.6 | [C] bokeh-mathjax in the served bundle? | Left out of P1.11; file P2.48. | A36 | Different code (server resources). |

### P1.12 Size units

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.12.1 | How do Stata's relative units map to pixels? | B: one unit for every class at the 4-inch reference (rs = 2.88pt); CHANGELOG. | M1 | A keeps markers 36% and lines 30% too large against text. |
| P1.12.2 | Unknown size name? | The class's medium, with twoway's note. | M1 | twoway's picture. |
| P1.12.3 | Line-width keyword ladder? | Stata's linear ratios (adding vvvthin and none) on D1's unit; hairline floor 0.3pt. | M1 | Size units. |
| P1.12.4 | [C] Reference length for #pt/#in/#cm? | Convert to rs at min(xsize or graphsize x, ysize or graphsize y), then draw on D1's unit. Closes P2.13's "4-inch reference". Pending ratification row 30: under the recommended (b) this narrows to the scheme's `graphsize` and the `xsize()`/`ysize()` half is a P2 row S58 files. | M1 | twoway's ratios (economist 14pt = 1.82x heading). |
| P1.12.5 | [C] mlabgap redesign moves every default label? | Accept (radius + `gsize label_gap`). Measure the diagonal clocks and the no-marker origins (bar, pcarrow, pcbarrow, pci) first; flip the 4px pins with the reason. | M1 | Scheme look. |
| P1.12.6 | [C] N1 nonselection/muted glyph sync? | Not in P1.12: file P2.49 with its BUGS.md entry and failing test. P1.2/P1.12 tests must not depend on it. **Ratified 06oct2026 (row 27), CHANGED:** fixed by S08 in WP-30; P2.49 is not filed. | A37 | Different root cause (Bokeh's creation-time copies). |
| P1.12.7 | [C] `lwidth(none)` sub-claim? | Closed by P1.12b; removed from P2.12. | A38 | One owner. |

### P1.13 Colour syntax

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.13.1 | Unknown or out-of-range colour? | Black (bars #333333) with the note, at every site (mlabcolor, refline, textbox, graph colour, colormissing); CHANGELOG. | M1 | Measured twoway picture. |
| P1.13.2 | Case-sensitive names? | Yes, in options and in every scheme file; an unknown name gets a note and black. The KPI path keeps a case-insensitive Stata lookup ahead of CSS. | M1, A39 | twoway notes `Navy`; KPI is dash-only. |
| P1.13.3 | Comma form, short/invalid hex, British names? | `"255,0,128"` refused r(198) in twoway's words (flip HC2-16p). Short/invalid hex draws the default silently. `grey`/`dimgrey`/`bluishgrey`/`ltbluishgrey` become unknown (note, black). KPI CSS leniency is kept. | M5, M6, M1 | twoway's three answers, measured. |
| P1.13.4 | Bare *# on filled layers before P1.2's blend? | With or after P1.2b. | A40 | Avoids redoing the colours. |
| P1.13.5 | [C] `%#` at direct `translate_mcolor` sites? | Fold into P1.13a: every site takes (hex, alpha) from `stata_colour`; a bare `%#` uses the site's base colour; drop the `""`→black map. | A41 | Same reader; P1.20 reuses it. |
| P1.13.6 | [C] Owner of naturally_white and the intensity function? | P1.2 adds them; P1.13a builds on the one function with the f>1 clamp. | A42 | One function. |
| P1.13.7 | [C] Step 2 relative to P1.4(h)? | P1.4(h) first, or in the same batch. | A43 | Otherwise `color p1mark bogus` turns markers black. |

### P1.14 Named styles

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.14.1 | Which style names resolve? | A: p1-p15 for every style option. B: linestyle names through P1.21's resolver of all 76 linestyle files, other classes through a curated table, the rest per P1.14.3. | A44 | Consistent with P1.21.5. |
| P1.14.2 | Named styles vs explicit options? | twoway's factor order, documented. | A45 | Drop-in parity. |
| P1.14.3 | A name Stata does not know? | twoway's per-class default attributes with twoway's note, once per layer. | M1 | twoway notes; it never refuses. |
| P1.14.4 | blstyle()/clstyle()? | Include. | A46 | Same mechanism. |
| P1.14.5 | dstyle before P2.9? | Declare and serialise now; noted until P2.9. | A47 | Nothing to style yet. |
| P1.14.6 | [C] p()? | Match twoway: its own key, applied last over every style option; the first copy wins; the value is one name. New first-copy category in `_dash_rep_cat`; fix dash.sthlp:2282. | A48 | Measured c3-c5. |
| P1.14.7 | [C] area/rarea outlines? | Stay noted until P2.12. | A49 | P2.12's root cause and code. |
| P1.14.8 | [C] pc arrowheads? | Stay noted until P2.8. | A50 | P2.8's root cause. |
| P1.14.9 | [C] dlstyle(), bmlinestyle()? | Declare and serialise; noted until P2.9 / P2.8. | A51 | Same pattern as dstyle. |

### P1.15 by() sub-options and chrome

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.15.1 | xsize/ysize size the whole array? | Yes. | M1 | Size. |
| P1.15.2 | twoway's iscale shrink? | Default and explicit iscale, after P1.12. | M1 | Size. |
| P1.15.3 | Stacked panels lose axis labels? | CustomJS turns every panel's axes on when stacked, in both modes; the script is hashed under P1.29. | A52 | No twoway truth; phones need labels. |
| P1.15.4 | by() argument errors? | Refuse rows()+cols() r(198), out-of-range rows/cols/holes r(125), and capitals and repeated style() r(198), in twoway's words. | M5 | twoway refuses. |
| P1.15.5 | Date by() panel titles? | Keep dash's date text (WP-28 S12). | A53 | Documented and ratified. |
| P1.15.6 | cols() beyond the panels? | Honour up to the by_groups limit; clamp with a note beyond it. | A54 | Resource bound (rule 1). |
| P1.15.7 | Split quoted value labels? | Do not copy; document. | A55 | A parsing quirk. |
| P1.15.8 | [C] Content of the one clegend? | Panel 1's levels, silent, as twoway. First test that a level has the same colour in every panel in both modes. | M1, M6 | twoway draws panel 1's key silently. |

### P1.16 Legend keys and axis titles

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.16.1 | Which default axis-title rule? | twoway's measured first-equals-last rule per axis; stated in the help. | A56 | 264/272 probes match. |
| P1.16.2 | Fold in key merging, histogram-only legends, first-used axis? | File P2.50, P2.51 and P2.52; the scatteri legend fix stays. | A57 | Different code. |
| P1.16.3 | Accept the changed text? | Accept; CHANGELOG; no opt-out. | A58 | twoway parity. |
| P1.16.4 | [C] Function names outside ASCII? | Key them as twoway (`_y`, `ü`): a Unicode identifier of at most 32 characters, validated in Stata and Python. | A59 | Text nodes; no injection surface. |
| P1.16.5 | [C] Owner of the recast label rule? | P1.16 first. P1.8b keeps `type`, writes `recast`, and adds TestRecastKeepsTheSeriesLabel. S45 reads this as ratification row 40 states (drawn type in `type`, typed type in `recast_from`; derived layers write `recast`); pending. | A60 | twoway keeps the original type's label. |

### P1.17 Bar and range geometry

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.17.1 | Default bar/rbar width? | 1 x unit (the variable's units on date axes). Help and CHANGELOG point sparse date bars to barwidth(). | M1 | Look. |
| P1.17.2 | Default base when 0 is off the axis? | twoway's clamp into the axis scale, with P1.3-A. by(): the common curmin; yrescale per panel; never 0 on a log axis. | M1 | Measured; joint with P1.3.7. |
| P1.17.3 | [C] Remove the spacing machinery? | Remove it (deletions, with the CRITICAL/HIGH warnings); this cancels P1.9 step 5. | A61 | Dead under P1.17.1. |
| P1.17.4 | [C] rcap barwidth()? | Refuse r(198) `option barwidth() not allowed`. | M5 | twoway refuses; dash is silent today. |
| P1.17.5 | [C] Cap angle under horizontal? | P1.17a tags cap markers `dash_cap`; P1.9's transpose rotates them. | A62 | One owner for orientation. |

### P1.18 Common axis sub-options

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.18.1 | scale(off)/nolabels/noticks/titlegap under by()? | Drawn as if absent, silently. | M6 | twoway is silent. |
| P1.18.2 | Units of tlength()/titlegap()? | P1.12's resolve_size, after P1.12. | M1 | Size units. |
| P1.18.3 | Wrong-case or unknown anglestyle? | Note and draw 0, as twoway; CHANGELOG. | M1 | twoway notes; it does not refuse. |
| P1.18.4 | Bound violations; capitalised NOLABELS/OFF/Alt? | Refuse both r(198) in twoway's words. | M5 | twoway refuses. |
| P1.18.5 | [C] xtick()/ytick()'s own look? | Honour noticks/tlength/tposition on tick-only positions, from the scheme geometry. | M1 | twoway's separate style. |

### P1.19 Sub-option abbreviations

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.19.1 | Lower case only? | Capitalised sub-option names are refused r(198) in twoway's words. | M5 | twoway refuses. |
| P1.19.2 | Spellings twoway refuses; duplicates in one copy? | Refuse r(198) in twoway's words. | M5 | twoway refuses. |
| P1.19.3 | Fold in lab(1 ..) loss, textbox s(), rows() vs cols()? | Fold in. rows beats cols inside the Mata merge (TP-14a stays green); the option key is passed down to `_dash_rep_subkey`. | A63 | Same root cause and lines. |
| P1.19.4 | [C] Honoured legend sub-option with a bad value? | Refuse as twoway: `c(red)` r(121) `cols() invalid`; others with twoway's code. | M5 | No silent drop. |
| P1.19.5 | [C] Notes name the canonical or the typed sub-option? | The typed one. | A64 | Users see what they wrote (as P1.18 gap 3). |

### P1.20 plotregion() and graphregion()

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.20.1 | Region typos; a sub-option repeated in one copy? | Refuse r(198) in twoway's words. | M5 | twoway refuses. |
| P1.20.2 | graphregion(margin())? | Note it; file P2.53. Any later CSS path emits only computed numbers and sanitised colours. | M5, A65 | Cannot draw it exactly yet. |
| P1.20.3 | graphregion i* options? | Note them and re-disposition. | M5 | BoxAnnotation is clipped to the frame. |
| P1.20.4 | plotregion(margin()) exactness? | A static per-side fraction through P1.3's `_dash_plot_margin` (a Range1d re-set by the re-finish); exact for zero. | M1, A6 | Same approximation as P1.3.1. |
| P1.20.5 | lalign()/ilalign()? | Note them. | M5 | Bokeh has no stroke alignment. |
| P1.20.6 | Who owns by() regions? | P1.15c, using P1.20a's region reader; both notes updated. | A66 | Today nobody owns it. |
| P1.20.7 | [C] bgcolor() semantics? | twoway's: it paints under the graph region. A region `none` shows bgcolor() if given, else `color background`. Flip dash.sthlp:2717-2721 and test_option_validation.py:1089-1094 with the reason; CHANGELOG. | M1 | Look follows twoway. |
| P1.20.8 | [C] Owner of section B (margins)? | P1.3-A owns `_dash_plot_margin`, which reads `margin twoway`. P1.20b extends its grammar: l/r/b/t with + - =, copies that add, the inner box and the graphregion margin. | A67 | No second parser. |

### P1.21 xline/yline

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.21.1 | Input twoway refuses? | Refuse r(198)/r(100)/r(123) in twoway's words and order, including nan, inf, 1e400 and `1_000` (`invalid line argument`). | M5 | twoway refuses. |
| P1.21.2 | Capitals (NOEXTEND, LSTYLE())? | Refuse, as twoway does. | M5 | twoway refuses. |
| P1.21.3 | Ceiling beyond twoway's 2,500 per copy? | A `reflines` row (default 10,000, ceiling 100,000, global), counted as positions x panels over the dashboard; r(134); bulk add. | A68 | 70 s for 10,000 Spans; by() multiplies (rule 1). |
| P1.21.4 | noextend and style(unextended)? | Exact: an Arrow over P1.3's hull (P1.21b), re-finished after moves. | M1, A69 | Look; must follow P1.3. |
| P1.21.5 | Scope of lstyle() names? | Every linestyle (76 files) via the style-file chain, shared with P1.14. | A70 | The help's own examples use non-p# names. |
| P1.21.6 | [C] Draw order? | `level="underlay"`: above the grid, below the glyphs. | M1 | twoway's order. |
| P1.21.7 | Research residual: out-of-range line unclipped in twoway | File P2.54. | A71 | Different code. |

### P1.22 function fallback

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.22.1 | What does the points-free fallback evaluate? | Keep the ten functions and close the item by WP-29 P0.6 plus the note. The disposition reads "a hand-written spec is drawn by the documented ten-function fallback". Update GAPS2.md:228 and ROADMAP. Name range(varname), droplines() and horizontal as residuals (P2.14, P2.7, P1.9). | M12 | Binding. |
| P1.22.2 | A Stata-side note too? | Renderer note only. | A72 | One note per cause. |
| P1.22.3 | [C] Wording of the note? | Neutral: it needs Stata's points, lists what the fallback knows and names the one it does not. True for pi, e and `sin (x)`. | M12, A73 | No false remedy. |
| P1.22.4 | [C] Reword "not dash's … drawn from its expression"? | Yes, in the same section. | A74 | It promises a draw that cannot happen. |
| P1.22.5 | [C] Sequencing with P1.26? | After P1.26-A, using `_dash_emit_note`. | A75 | The served note must reach Stata. |

### P1.23 Date-axis residuals

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.23.1 | Labels of a mixed date+number axis? | Stata units with the first layer's date format; build-time date ticks refreshed by P1.3. | M1 | twoway's picture. |
| P1.23.2 | Text of a date colorvar key? | Comma general numbers; honour zlabel(, format()) in 23b, together with P1.5.6. | M1 | twoway's text. |
| P1.23.3 | [C] How is the mixed axis drawn? | A CustomJSTransform plus the Python twin in `_dash_secondary_values`, with a headless check under the shipped CSP. | A76 | No per-refresh column writes. |
| P1.23.4 | [C] Literals outside 0100-9999 on a date axis? | Drop them with a note; a help line beside dash.sthlp:2909. **Ratified 06oct2026 (row 12), CHANGED:** drawn as twoway draws them, no note; S35 converts them safely in Python and JS. | A77 | They cannot be dates in the browser. |

### P1.24 mlabvposition(), mlabtextstyle()

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.24.1 | mlabvposition() on the 21 refusing types? | Refuse r(103) in twoway's words (naming the label variable when mlabel() is given), on the recast type, after P1.8b. | M5 | twoway refuses. |
| P1.24.2 | Size units of mlabtextstyle? | `_gsize` pt now; P1.12's unit later. | M1 | Size units. |
| P1.24.3 | [C] User `textboxstyle-NAME.style` files? | Keep noting them; file P2.55. Add a committed table of all 37 shipped textboxstyle names from 19.5. | A78 | A new read surface; M7 covers schemes only. |

### P1.25 Scheme resolution

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.25.1 | Read third-party and PLUS schemes? | The whole ado-path. | M7 | Binding. |
| P1.25.2 | The six internal StataCorp schemes? | Ship translations (26 files). Measure the six in Stata for the twenty-scheme tables (effort M). | A79 | Verified; no install dependence. |
| P1.25.3 | A cwd file named like a StataCorp scheme? | The shipped translation wins; CHANGELOG. | M7 | BASE is first on the ado-path. |
| P1.25.4 | Paths in scheme()? | Keep refusing separators, `..` and quotes; documented. | M7 | M7's name guard. |
| P1.25.5 | [C] Theme alias vs a same-named file? | An inherited c(scheme) always walks. An explicit alias with a file of that name: the file wins; the alias works when no file exists. | M7 | twoway's result. |
| P1.25.6 | [C] Per-graph schemes differ between saved and served? | Folded into 25B: the served app carries one property dict per distinct graph scheme. The false warning goes; BUGS.md entry and failing parity test first. | A80 | Same root cause and code; the modes must agree. |
| P1.25.7 | [C] Third-party colour-*.style lookup? | Unmeasured. The help claims fidelity only as measured; the lookup is filed in P2.55. | A81 | No measured rule. |

### P1.26 Notes

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.26.1 | A 'drew nothing' note on a layer whose own if/in keeps no row? | Silent in both modes. | M6 | twoway is silent. |
| P1.26.2 | How does a note look and behave? | Like twoway's: text colour, shown under quietly and set output error, hidden by capture, SMCL-escaped. | A82 | twoway's measured visibility. |
| P1.26.3 | Trial render for served builds? | `dash build, server`: always. `dash serve`: the child's warm-up (P1.31.5) is the trial, and its notes are forwarded. | A83 | Avoids a ~56 s doubled wait. |
| P1.26.4 | [C] How is a note recognised in a log? | twoway's `(note: …)` form. `help_examples.FLAGGED` and `release_verdict.DIAGNOSTICS` match it. | A84 | The gates go blind otherwise. |
| P1.26.5 | [C] The trial raises? | `dash serve`: stop the child and refuse r(198). `dash build, server`: note. | A85 | Do not report a server that cannot draw. |
| P1.26.6 | [C] Which child stderr reaches Stata? | dash notes, ERROR lines and tracebacks, within the 200-line budget. | A86 | Access-log noise stays out (P2.38). |
| P1.26.7 | [C] The existing build-time planners? | Keep `_plan_graph_notes` and `_plan_by_groups`; the parity test counts planner and trial notes, each once. | A87 | Sessions run with warn=False. |

### P1.27 Command-form gaps

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.27.1 | No browser in batch and under set graphics off? | Suppress in both; print the path. | A88 | twoway displays nothing then. |
| P1.27.2 | saving() characters? | Allow `..` and `; & \| < >`. Keep refusing `"`, backquote, `$`, control characters and a leading `-`. The internal --launch route keeps refusing `..`. P2-80 and PV-04/05/14 are flipped with the reason. The rationale names the `To launch:` sink. | M11 | Binding. |
| P1.27.3 | Unknown saving() sub-option? | Refuse r(198) `option X not allowed`. | M5 | twoway refuses. |
| P1.27.4 | [C] Interactive console Stata? | It keeps opening the browser. | A89 | No other view there. |
| P1.27.5 | [C] Preview in batch/graphics off? | Keep writing it; the line says it is a temporary preview and to use saving(). | A90 | `r(filename)` finds it. |
| P1.27.6 | [C] Shape of the test seam? | A pure-argument program for the SB/ND cases; `$dash__display` only for the HC2 controls, with a hygiene rule. S12 also fences SB-07..SB-11 (ratification row 33; pending). | A91 | Smallest user-reachable seam. |
| P1.27.7 | Research residuals under M5: `saving(my file.html)` unquoted; `twow`/`twowa`/`gra`/`grap` | Refuse with twoway's rc and words (measured); the prefixes give r(199) `command X is unrecognized`. | M5 | Inside the saving()/prefix area P1.27 touches. |
| P1.27.8 | Research residual: `dash twoway` alone | File P2.56. | A92 | dash refuses what twoway accepts; outside M5. |

### P1.28 graph export

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.28.1 | Export route? | A + B1. B3 waits for the deferred platform package; no B4. | M8 | Binding. |
| P1.28.2 | output_backend(svg)? | Rejected; client-side `export('svg')` instead. | M8 | The backend breaks the grid PNG save. |
| P1.28.3 | Note when Stata holds a graph? | One line per dash command, only when a graph is in memory. S22 reads "dash command" as a file-writing command (ratification row 35; pending). | M8, A93 | Any later graph export writes the stale graph. |
| P1.28.4 | Image extensions in saving()? | Replace with .html plus a note on both routes, inside P1.27's `_dash_saving_parse`. | A94 | One grammar. |
| P1.28.5 | Inactive tabs do not print? | Document "prints the active tab"; the JS goes to P3.11. | A95 | P3.11 owns printing. |
| P1.28.6 | [C] Form and lifetime of r(filename)? | Absolute, set last after the write, copied by value. Previews are documented as transient; a refused dash leaves it empty. | A96 | Survives cd; no macro re-expansion. |
| P1.28.7 | [C] SVG save on layout(bs) bare figures? | Flip `_assert_nine_tools` with the reason. The action is idempotent and added only beside a SaveTool. | M8 | Both modes gain SVG on every figure. |
| P1.28.8 | [C] Other r() leaks (kpi summarize, build-server r(fn))? | Fold into P1.28a. | A97 | Same root cause and code. |

### P1.29 Security hardening

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.29.1 | Windows path with % or !? | Write it, do not open it, print the path (previews included). | M11 | Binding. |
| P1.29.2 | An unhashed executable inline script? | Raise a named error and write nothing. | A98 | Fail closed (rule 1). |
| P1.29.3 | The `python app.py` header keeps 'unsafe-inline'? | Yes. `_DASH_CSP_SERVED` stays byte-identical as the header source; the meta gets its own base constant. | A99 | Measured to block injection; the meta's nonce governs. |
| P1.29.4 | [C] The `To launch:` hint with ! or %? | Mac/Unix: single-quoted path. Windows: a warning line. | A100 | Pasted lines fail in bash/zsh. |
| P1.29.5 | [C] Drop 'unsafe-inline' from script-src? | Drop it, with no CSP1 fallback. | A101 | CSP2+ browsers ignore it anyway. |
| P1.29.6 | [C] 'self' next to the nonce? | Nonce-only if the browser test shows zero violations (MathJax, GL >10k rows, formatters, hover, KPI brush); otherwise keep 'self' and record why. | A102 | Stricter when it is measured safe. |
| P1.29.7 | [C] Treat % and ! separately? | No: one rule. | M11 | Binding. |
| P1.29.8 | [C] CSP on the empty page and the redirect page? | Add `default-src 'none'`. | A103 | No scripts there; free hardening. |

### P1.30 Dependency window

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.30.1 | bokeh ceiling? | `bokeh>=3.8,<3.10`; `<3.11` if 3.10.0 is verified in a scratch venv inside WP-30. | M9, M10 | Binding. |
| P1.30.2 | Outside the window at run time? | Above: a note, then continue. Below 3.8: refused. | M9 | Binding. |
| P1.30.3 | Granularity of "verified"? | major.minor; patches inherit. | A104 | Matches conftest's baselines. |
| P1.30.4 | dash_setup verdict above the range? | A warning (rc 0). A managed Python gets the managed guidance, never a pip line. | A105 | No downgrade behind the user's back. |
| P1.30.5 | Lock file, matrix, dev requirements, hashes? | No constraints file and no hash pinning. requirements-dev.txt goes to P3.9 (with scipy); the matrix goes with P1.33. | A106 | Fold rule: P3.9 owns dev dependencies. |
| P1.30.6 | [C] The venv route would downgrade? | Ceiling only in a venv dash created. A reused venv is checked and reported `above`. | A107 | Never downgrade silently. |
| P1.30.7 | [C] numpy/pandas ceilings? | bokeh only, stated in the help. | A108 | Only bokeh's internals carry guards. |
| P1.30.8 | [C] The served app below the floor? | Refused at app start (python app.py and bokeh serve). | M9 | Run time, below the floor. |
| P1.30.9 | [C] Internals guards? | Fail closed. The template guard checks "preamble" in FILE.blocks plus one CSP. The origin guard asserts that check_allowlist rejects the probe. The AuthProvider hook is checked at launch. Otherwise the server refuses to start. | A109 | The security line M9 relies on (rule 1). |

### P1.31 Served-app resource limits

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.31.1 | Session cap? | `--max-sessions` and `dash serve maxsessions(#)`, default 20, 0 refused; in-process documents exempt. | A110 | About 2 GB at 200k x 3. |
| P1.31.2 | Idle lifetime? | 60 minutes of server-observed activity (filter, brush, CSV), with a reload message; `idletimeout()`, where 0 means never. | A111 | No client JS under CSP. |
| P1.31.3 | Under bokeh serve? | Yes, through a sys.modules holder. Build-time defaults, overridable by environment variables; --num-procs caps per process (documented). | A112 | Bounds both launch paths. |
| P1.31.4 | Recompute off the event loop? | One worker with an "updating" cue. The latest request per session wins, FIFO across sessions, and the bound is documented. An idle close bumps the generation. | A113 | /health no longer freezes. |
| P1.31.5 | Warm up before listening? | Yes. "Preparing the dashboard (N rows, estimator)" prints first; this is P1.26's trial. | A114 | No session pays the build. |
| P1.31.6 | Per-client cap? | Global cap only. | A115 | Clients are all loopback. |
| P1.31.7 | [C] Owner of per-session memory? | 31a: decode once plus the shared payload, including `_orig_src_data`. P2.41 keeps `.tolist()` and the index lists. RSS test: per-session growth at most 40 MB at 200k x 3 (60.7 MB today). **Ratified 06oct2026 (row 22), CHANGED:** at most 80 MB at 200k x 3, which today's 60.7 MB meets (the RSS test is a guard); 31a keeps decode-once and drops the shared move snapshot, so `_orig_src_data` stays per session and joins P2.41's list (section-46). | A116 | Fold rule split. |
| P1.31.8 | [C] Memo budget and estimators? | lowess, fpfit and lpoly/lpolyci; 64 MB LRU. The decode cache holds one entry. Both are skipped under `_DASH_TRIAL` and in Stata's process. | A117 | Bounded; no leak into Stata. |
| P1.31.9 | [C] dash serve's other rate limits? | Only maxsessions() and idletimeout() in WP-30. | A118 | Scope. |
| P1.31.10 | [C] Busy page retry? | A static 503 with Retry-After and no auto-refresh. | A119 | No script; no retry storm. |
| P1.31.11 | [C] Session open on the loop? | The bound is documented; file P2.57. | A120 | Different code. |

### P1.32 Render-time dependency guards

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.32.1 | Refuse, note or ignore versions? | Refuse a missing or unimportable package, a Python below the floor, and bokeh below 3.8. numpy/pandas below the minimums: a note. | M9, A121 | M9 binds bokeh; the rest follows M3's spirit. |
| P1.32.2 | [C] Hard bokeh floor (no CustomJSTicker)? | Covered by M9's refusal below 3.8, in both modes and at app start. | M9 | Binding. |
| P1.32.3 | [C] dash clear with missing packages? | Prune without loading the renderer (a stdlib-only path with the same guards). | A122 | Users can still clean up. |
| P1.32.4 | [C] The floor constant's name and home? | One dash.ado constant, pinned equal to `_dash_pymin` by test_version_floor. | A123 | One number. |

### P1.33 Python floor

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.33.1 | Approve downloads? | Into scratch venvs only. | M10 | Binding. |
| P1.33.2 | What counts as passing? | Strict pytest with both pin sets on 3.11 and 3.12, the Stata venv-link leg per Python, and one full cscript run on the floor. | M3 | Binding. |
| P1.33.3 | Minor or patch floor? | Minor (the lowest passing). The Windows patch caveat goes to the deferred platform package. | A124 | M4 defers Windows. |
| P1.33.4 | [C] One-time or recurring evidence? | A floor leg in the release gate. **Ratified 06oct2026 (row 25), CHANGED:** manual only; measured once by S05, no gate leg. | A125 | A declared floor must stay tested. |
| P1.33.5 | [C] Pinned vs resolved stacks? | One fresh-resolve leg per floor Python, installing as dash_setup does, with P1.30's ceiling. | A126 | Users get resolved stacks. |
| P1.33.6 | [C] The venv() advice loop? | Fold in: with pyok==0 the guidance says "link Python <floor>+" and never suggests venv(); the rule-7 test comes first. | A127 | Same root cause and code. |

### P1.34 Portable runners

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.34.1 | Change the project instructions' rule 10 and the GUI-block hook text? | No. | M4 | Runners only; maintainer text. |
| P1.34.2 | DASH_REPO unset? | Use c(pwd) when it holds dash.ado and test/run_all_cscripts.do; otherwise r(601). | A128 | Never silently tests another tree. |
| P1.34.3 | [C] The two generators? | Retire both: "historical, do not run" and a refusal. No WP-30 item runs them. | A129 | One rewrites main's dash.ado, then crashes. |
| P1.34.4 | [C] Extractor root convention? | env DASH_REPO for every new WP-30 extractor; the four W29_REPO extractors move with P3.7. | M4, A130 | One form to copy. |
| P1.34.5 | [C] Scope of 34b? | Runners only. Old extractors are left to P3.7; the guard covers runners and new extractors. | M4 | Binding scope. |
| P1.34.6 | The deferred remainder? | One ROADMAP platform package: Linux, Windows, Intel Mac, GUI Stata, the WP-29 S08/S09/S13 paths, critic item 10, P1.28 B3, P1.29 option B, the P1.33 Windows patch. | M4 | Binding. |

### P1.35 Stata floor

| Id | Question | Ruling | Source | Why |
|---|---|---|---|---|
| P1.35.1 | Stata floor? | 19; an older Stata is refused with a clear message. | M2 | Binding. |
| P1.35.2 | Run the 16-18.5 binaries, set python_exec? | No. | M2 | Binding. |
| P1.35.3 | Raise the 91 `version 16.0` lines? | Sweep all to `version 19` (not 19.5), plus the guard, as one first-batch commit. Exempt the guard programs; full cert and pytest after. | M2, A131 | "Declares version 19"; the guard and the level are one number. |
| P1.35.4 | Stata 16/17 refuse or note? | Moot. | M2 | Refused at entry. |
| P1.35.5 | [C] Admit 19.0? | Yes. The help says "Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64". | M2 | M2 says 19. |
| P1.35.6 | [C] BE/SE wording? | "Measured on MP only". | A132 | Honest. |
| P1.35.7 | [C] CHANGELOG? | Requirements, and "Changed behaviour (may need your do-files changed)". | M2, M5 | Users of 16-18.5 are refused. |
