# Traceability Matrix — WP-28 (22 GAPS2 gaps)

> Phase 5 (VALIDATE), 2026-09-25. Bidirectional check: every GAPS2 plan step of the 22 gaps in scope
> traces to a task of the fixed section files (ids after the Phase 4 renumbering), and every task
> traces to a gap, a shared component, a checkpoint or the closeout. Status values: **covered** (a
> task delivers the step), **amended** (a DISCOVERY decision replaced the step and the replacement
> has a task), **excluded** (a DISCOVERY decision removes the step; recorded in PRD §7 and in the
> gap's BUGS.md residual clause). The source of the step list is `review/requirements-security.md`
> §1, re-read against the section files after the fixer pass.

## Summary

| | Count |
|---|---|
| Gaps in scope | **22** (15 S1, 4 S2, 3 S3); C4/E4 out by decision (Q3) |
| GAPS2 plan steps traced | **93** |
| Covered by a task | **82** |
| Amended by a decision, replacement covered | **2** (B2 step 4 by Q14's amendment; D1 step 2 by Q30/D13) |
| Excluded by a decision | **9** (G1 steps 2 and 4; G3 step 2; K2 steps 1 and 5; X2 step 3; D1 steps 4 and 5; E14's `filterposition(left)` difference) |
| Partial or missing | **0** (E3 step 4, missing at the first review pass, is now 14-03; B7 step 3 and G3 step 4, partial then, are now covered) |
| Measured symptoms with a regression test that fails at 91d97be | **49 of 49** (§2) |
| Sections / tasks / batches | 19 / **205** / 4 (160 tasks before the fixer pass) |
| Commits the plan produces | **32**: 21 gap commits (section 12 closes E3 and G6 in one), S00 (the slot wrapper), S01, S02, S03, S04, and six closeout commits |
| Tasks beyond the gap set | 46, all approved (§5) |
| Review findings | 111 raised → 102 applied as written or as DECISIONS adjusted, 9 superseded by a later decision, 0 rejected (§6) |
| Mechanical validation | 0 errors, 14 warnings (all line-range false positives) over 205 tasks (§9) |

## 1. Plan-step coverage (GAPS2 numbering; task ids after renumbering)

| Gap | Plan step (GAPS2 numbering) | Task id(s) | Status |
|---|---|---|---|
| B1 | 1 tokenise with `_textbox_string_end`; strings are label lines | S14 TR-14.2/14.3, 14-04 | covered |
| B1 | 2 expand numeric parts in dash.ado with `numlist`; write expansion into the spec; keep `_MAX_AXIS_TICKS` | S14 TR-14.11..14.13, 14-07 (ado); TR-14.1, 14-04 (Python bound) | covered |
| B1 | 3 pytest each form in both modes | 14-01 `TestNumlistForms`, `TestLabelledTicks`, `TestTheBound` | covered |
| B1 | 4 cscript reading twoway's tick positions and label text (SVG) | 14-02 (`b1_label` probes), 14-08 (AL-05..AL-16) | covered |
| B2 | 1 hull of data ∪ label/tick positions (unless `norescale`) ∪ `range()` after the layers | S18 TR-18.6..18.10, 18-05, 18-06 | covered |
| B2 | 2 `range(#)` is a value; accept `r()`, missing; log/date; `yscale2`/`xscale2` | 18-04 (TR-18.1..18.3), 18-06 (TR-18.7), 18-09 (TR-18.12) | covered |
| B2 | 3 pytest both modes | 18-01 | covered |
| B2 | 4 cscript recording `.Graph.yaxis1` min/max for ~20 combos into a fixture | 18-02 (25 SVG-fitted probes + `.Graph` candidates + verdict), 18-13 (AE-01..06) | amended (Q14 amendment: SVG is the truth, `.Graph` probed once) |
| B3 | 1 `_TEXTBOX_SUBOPTS` → (full, minimum) table | S13 TR-13.1, 13-07 | covered |
| B3 | 2 canonicalise names in `_parse_textbox_opt`; name the rest; route `axis(2)` | 13-07, 13-08 (TR-13.3/13.4), 13-09 (Python route), 13-10 (Mata route) | covered |
| B3 | 3 pytest table over every spelling on all six text options, both modes | 13-01 `TestEverySpellingOnEveryOption::test_spelling` | covered |
| B3 | 4 cscript comparing twoway's title text and colour (SVG) | 13-01 TBG-01, 13-06 fixture | covered |
| B5 | 1 parse `order()` with `_textbox_string_end`/`_textbox_lines` | S15 TR-15.1, 15-05 | covered |
| B5 | 2 key text by number (default → label → order → lastlabel), then select/order | TR-15.3, 15-06 | covered |
| B5 | 3 `-` entries as `LegendItem`s (placeholder renderer if needed) | TR-15.3, 15-06 (research W §1a: `renderers=[]` draws; no placeholder) | covered |
| B5 | 4 pytest both modes; cscript vs twoway's SVG legend | 15-01 (py + LO-01..08), 15-04 fixture | covered |
| B6 | 1 empty ≠ absent in `_dash_axis_labels`; same for `{n}title2` | S13 TR-13.7, 13-08, 13-14 | covered |
| B6 | 2 pytest both modes: `xtitle("")`, `ytitle("")`, `xtitle("", size(large))`, histogram/kdensity default | 13-01 `TestEmptyTitles` (4 tests) | covered |
| B6 | 3 cscript: twoway SVG has no axis-title text; dash `axis_label` empty | 13-01 TBG-04 | covered |
| B7 | 1 read `{n}title2` through `_dash_textbox`, join lines, name the rest | S13 TR-13.8, 13-02 | covered |
| B7 | 2 apply `size()`/`color()` to the y2/x2 axis | TR-13.8, 13-02 | covered |
| B7 | 3 pytest both modes: quoted, multi-line, compound-quoted, sub-option | 13-01 `TestSecondAxisTitleIsATextbox::test_text_lines_size_colour` (the compound-quoted case `` ytitle2(`"c "q" d"') `` added, F-18) | covered |
| B7 | 4 extend JSE-46 to compare the right-axis label with twoway's SVG | 13-01 (`jg46l`) | covered |
| C2 | 1 floor/clamp count; last edge `start + h*bin`; drop tolerance edge | S05 TR-05.1..05.3, 05-03 | covered |
| C2 | 2 same rule in `_FILTER_JS` recount; served follows | TR-05.5, 05-03 | covered |
| C2 | 3 property test (random, bin 1..100, `width()`, `start()` just above min) summing to N saved/served/node; nlsw88 and census regressions | 05-01 (`TestEveryFrequencyHistogramSumsToN`, `TestNlsw88AndCensusRegressions`, `TestBothModes`, `TestTheJavaScriptRecountAgrees`) | covered |
| C2 | 4 `twoway__histogram_gen generate()` output into `extract_stat_truth.do`; pin in `test_statistical_truth.py` | 05-02 | covered |
| D1 | 1 tokenise as Stata does (category, key, quoted value with ` %NN`) | S06 TR-06.1/06.2, 06-02 | covered |
| D1 | 2 accept `"R G B"`, `"R G B %NN"`, CMYK, `"hsv h s v"`, `colour*#` (shared with D7) | 06-02 for the RGB/%NN forms; CMYK, hsv and `colour*#` stay GAPS2 D7's | amended (Q30/D13; the residual is written in the D1 BUGS.md entry, S19's deferred list and PRD §7, F-11) |
| D1 | 3 warn once per unreadable line, naming it; never store a malformed key | TR-06.4, 06-02 | covered |
| D1 | 4 all 129 local files parse; pin d3colors p1-p15 | the quoted-value tests write their own scheme file instead: `test_a_scheme_written_with_quoted_values_is_read`, `test_both_modes_draw_the_quoted_background_and_p1` (06-01, 06-02) | excluded (Q30/D13: third-party scheme files are out of scope) |
| D1 | 5 compare with Stata's SVG export under d3colors | the former task 06-05 was deleted | excluded (Q30/D13) |
| E1 | 1 shared formatter: `%w.dg`, comma, `%x`/`%H` refused, `%t`; use in `_dash_format_kpi_value` and `dash_numfmt`; carry own `%g` | S04 04-04..04-08; S11 11-02, 11-03 | covered |
| E1 | 2 refuse r(198) in `_dash_validate_value 'format'` | 04-15 | covered |
| E1 | 3 cert test: card equals Stata's kpi display per accepted format, both modes, after a move | 11-06 (KF-01..05) | covered |
| E1 | 4 fixture of `display` outputs; compare Python and node | 04-03 (`format_truth.json`), 04-01 `TestPythonWriter`, `TestJavaScriptTwin` | covered |
| E2 | 1 per-target mask = AND of non-excluding filters; link group one target; panels follow owner | S17 TR-17.9, TR-17.11, 17-09, 17-11 | covered |
| E2 | 2 saved: one mask per exclusion set; rewrite every target; targets + sets in callback args | TR-17.9/17.10, 17-11 | covered |
| E2 | 3 served: `_on_filter_change` with per-target widget subsets | TR-17.11, 17-09 | covered |
| E2 | 4 replace `TestExcludeHoldsWhileItsOwnFilterMoves` with multi-move sequences both modes | 17-01 stubs, 17-11 rewrite; S03 03-05 pin | covered |
| E2 | 5 Stata truth on auto (`count`, `summarize`); rewrite dash.sthlp:1135-1138 | 17-08, 17-15 | covered |
| E3 | 1 one formatter (all `%t` kinds, numeric with `c` and comma) with JS twin | S04 | covered |
| E3 | 2 use for dropdown labels, KPI first paint/`dash_apply_kpis`, tooltips (`CustomJSHover`), date-axis ticks (`CustomJSTickFormatter`), slider labels | 12-03, 11-02/11-03, 12-05, 12-06, 12-03 | covered |
| E3 | 3 period kinds on a numeric slider (step 1) with the formatter; served shares | 12-04 | covered |
| E3 | 4 record Stata truth: `display %tm 480`, `%tq 160`, `%tdDD/NN/CCYY 15000`, a `%tC` value, `%9.0fc 4099`, **and the twoway axis labels of a `%tm` variable**; compare Python/node and widget/card/axis/tooltip text both modes | display values: 04-03 (`format_truth.json`); the twoway `%tm` axis labels: 14-03 (probes `e3_tm_axis` and `e3_tm_axis_lab`: `twoway line close m` on sp500, ticks 492(3)501, texts `2001m1 2001m4 2001m7 2001m10`), read by S12's `TestDateAxis::test_ticks_read_as_stata_in_both_modes` (12-01, 12-06; fails when the probe is absent); site texts: 12-01, 12-02 | covered (F-02 closed) |
| E14 | 1 viewport meta in the served template | S10 10-04 | covered |
| E14 | 2 dimming from the generated app for linked figures | 10-05 | covered |
| E14 | 3 rspike/rconnected from the group's rows in the app | 10-06 (shared source + view, as the saved page does; S10:1014-1016 records the wording difference) | covered |
| E14 | 4 served bs stylesheet (992 px rule, KPI min heights); saved bar below the header; drop the ALLOWED exemption | 10-07, 10-08, 10-01 (TR-10.11) | covered |
| E14 | 5 tests in `test_mode_parity.py`, `test_served_bs_layout.py`, Chrome at 375/900/1440 | 10-01, 10-03 (runner widths 375/768/1440; recorded S10:1011-1013) | covered |
| E14 | — `filterposition(left)` header placement | `test_filterposition_left_is_recorded_not_changed`, dash.sthlp | excluded (research amendment) |
| F1 | 1 launcher treats non-zero exit as failure, captures stderr; `dash serve` errors naming the port | S09 TR-09.2/09.3/09.4, 09-03, 09-06 | covered |
| F1 | 2 poll `/health` up to 30 s; print the URL once it answers | TR-09.2 step 5, 09-03 | covered |
| F1 | 3 optional test-bind | TR-09.2 step 2 (`prebind`), 09-03 | covered |
| F1 | 4 argparse refuses `--port` outside 1024-65535; drop the unreachable clamp | TR-09.1, 09-03, 09-05 (all three clamps) | covered |
| F1 | 5 pytest against a held socket; cscript `_rc != 0` | 09-01 (`test_serve_launcher.py`, SPU-01..03), 09-02 | covered |
| G1 | 1 rename internals / reserve `__dash` and refuse r(110) | S07 TR-07.1/07.2/07.5, 07-04, 07-09 | covered (Q7: reserve) |
| G1 | 2 build qualifier/by()-order/ustrfix columns in a temporary frame | — | excluded (Q7; residual recorded 07-09, S19) |
| G1 | 3 pytest: `__dash_row__` and `__mlabel__y` drawn with own values | `test_a_name_dash_no_longer_makes_is_drawn_with_its_own_values` (`__mlabel__y`, `_x_jit`, …); `__dash_row__` is now refused by decision | covered (amended by Q7) |
| G1 | 4 cscript at `c(k)==c(maxvar)` | — | excluded (Q7 residual) |
| G2 | 1 `numeric` in the four parsers, twoway's message, r(109) | S08 TR-08.1, 08-03 | covered |
| G2 | 2 keep `colorvar()`, `mlabel()`, `hover()`, `by()` accepting strings | S08 Boundaries; `test_a_string_in_an_option_is_not_refused` | covered |
| G2 | 3 cscript over every type and position vs twoway | 08-02 (generated, 89 cases), 08-03 | covered (Q16: 40 types) |
| G2 | 4 pytest: hand-written spec with a string plot column → named refusal | 08-01 `TestAStringPlotVariableIsRefused`, 08-04 | covered |
| G3 | 1 count only what the page embeds | S08 TR-08.6..08.8, 08-08, 08-09 | covered |
| G3 | 2 binary export | — | excluded (Q9) |
| G3 | 3 size note on what is embedded | TR-08.10, 08-10 | covered |
| G3 | 4 6M-obs histogram builds, bins equal `twoway__histogram_gen`'s, page under 2 MB; 6M scatter refused | `TestTheCount::test_a_histogram_over_six_million_rows_passes_and_a_scatter_is_refused` (row count as a number), DL-01 (74 obs, bins vs generator), and 08-11's one 6,000,000-row run through the slot wrapper with rc and page size recorded in the G3 commit body and Resolution (F-12) | covered (the 6M-row run is measured once, not a committed test) |
| G5 | 1 `ustrregexm("^[\p{L}_][\p{L}\p{N}_]*$")` + `ustrlen<=32`, then `unab`/`confirm` | S07 TR-07.6/07.7, 07-13 | covered |
| G5 | 2 correct the refusal messages | TR-07.6 (echo class), 07-13 | covered |
| G5 | 3 cscript: `dash kpi mean(größe)` = `summarize`; range and dropdown widgets | 07-03 UN-01..UN-03 | covered |
| G5 | 4 pytest: renderer builds a filter widget over a Unicode column | `TestFilterOnAUnicodeName::test_a_range_widget_is_built_in_both_modes` (+ by/hover/colorvar widening) | covered |
| G6 | 1 export storage type; floats as shortest float32 repr | 04-11, `_dash_float32_text` (04-04; the fixture decides), 12-10 | covered |
| G6 | 2 `%w.dg`/`%w.dgc` in Python and JS | 04-04, 04-08 | covered |
| G6 | 3 use in marker labels, tooltips, KPI cards, dropdown labels, CSV | 12-07, 12-05, S11, 12-03, 12-10 | covered |
| G6 | 4 fixture of ~200 values (`%9.0g`, `%8.0gc`, `%10.0g`); test on auto price and floats | 04-03 (~1,300 rows incl. float storage), S12 `TestDropdown`/`TestMarkerLabels` on `f` and `price` | covered |
| G16 | 1 read `valuelabel`; fill `major_label_overrides` from the label set | S14 TR-14.4/14.5/14.7/14.8, 14-12 | covered |
| G16 | 2 `hover()` derived text column | TR-14.9/14.10/14.14, 14-13 | covered |
| G16 | 3 compare with twoway's SVG for `xlabel(1/5, valuelabel)` | 14-02 (`g16_valuelabel` probes), 14-14 (AL-17..19) | covered |
| K2 | 1 measure the floor in 3.10 venvs | — | excluded (Q8) |
| K2 | 2 raise the minimums everywhere | S09 09-11, 09-14 (TR-09.5..09.8) | covered |
| K2 | 3 `from __future__ import annotations`; ast-scan pytest | 09-10, `TestTheGeneratedAppEvaluatesNoAnnotationAtImport` | covered |
| K2 | 4 launcher checks `returncode`; pytest with a non-zero app | 09-03, `test_a_non_zero_exit_names_the_status_and_carries_stderr` | covered |
| K2 | 5 Stata against a 3.10 venv; downgrade to bokeh 3.5 | replaced by sandbox fakes HON-29/HON-30 (09-12) | excluded (Q8) / amended |
| X1 | 1 keep exact text; numbers compared as numbers | S17 TR-17.2/17.5/17.6, 17-02, 17-03 | covered (Q10) |
| X1 | 2 remove the 'nan'/'None'/'NaT' exclusion; colorvar string path; `""` as missing string | TR-17.3, TR-17.8, 17-02 | covered (Q13) |
| X1 | 3 one rule for both masks, pinned by a node+pandas pytest | TR-17.6, `TestOneRule::test_node_and_pandas_agree` (S03 `mask_parity`) | covered |
| X1 | 4 cscript with `str fips`, '1', '1.0', 'None', 'nan', 5e-05 vs `count if` | 17-05 | covered |
| X2 | 1 `colordiscrete` + `colorcuts()` → cuts are levels, rest gray; drop cuts below min | S16 TR-16.3/16.4, 16-06 | covered |
| X2 | 2 `colorlevels(#)` and `colorvarminmax` | TR-16.1/16.2/16.4, 16-04, 16-06 | covered |
| X2 | 3 bin at z ticks with `colorrule(hue)` | — | excluded (Q5) |
| X2 | 4 declare `zlabel()`, `ztitle()`, `zscale()`; draw on the key | TR-16.5..16.7, 16-05, 16-07 | covered |
| X2 | 5 SVG fixture of marker fill groups on auto and nlsw88; pytest compares factor per observation and level count | 16-03, `test_every_probe_partitions_the_observations_as_twoway_does` | covered |

## 2. Symptom-to-test map (the GAPS2 **Gap** line, and the test that fails at 91d97be)

| Gap | Symptom (GAPS2 **Gap** line) | Test |
|---|---|---|
| B1 | `xlabel(1 "2019" 2 "2020" 3 "2021")` → six unlabelled ticks | `test_axis_label_grammar.py::TestLabelledTicks::test_value_text_pairs_draw_three_labelled_ticks` |
| B1 | second label line lost; compound quote → lone backtick | `::test_a_second_string_is_a_second_line`, `::test_a_compound_string_is_one_label` |
| B1 | `10 20 to 40` loses 30; `1 2 : 5` uses `:` | `::TestNumlistForms::test_each_form_draws_statas_values[10 20 to 40 / 1 2 : 5]` |
| B1 | `1/5`, `1[1]3` named | same, `[1/5]`, `[1[1]3]` |
| B1 | `xlabel2`/`ylabel2`/`xtick`/`ytick` share the parser | `::test_xlabel2_ytick_and_a_date_axis_share_the_grammar` |
| B2 | `ylabel(0(20)100)` never shows 60-100 | `test_axis_extents.py::TestLabelValuesWidenTheAxis::test_ylabel_0_20_100_reaches_100` |
| B2 | `range(100)` inverts; `range(20 30)` hides; `range(0)` ends at max | `TestRangeOnlyWidens::test_range_100_widens_up_and_never_inverts`, `::test_range_20_30_never_narrows`, `::test_range_0_reaches_0_and_keeps_the_top` |
| B2 | `r(0 100)` named | `::test_r_is_range` |
| B3 | `title("T", c(red))` drawn as text | `test_textbox_grammar.py::TestAbbreviationsAreSubOptions::test_c_red_is_a_red_title` |
| B3 | `ytitle("Volume", axis(2))` titles the left axis | `TestAxisTwoRouting::test_axis_2_titles_the_right_axis` |
| B3 | after a full name, a later abbreviation is only named | not a stub as such — `test_spelling` covers each spelling alone; add `size(large) c(red)` (F-18) |
| B5 | `order(1 "Group 2" 3 "Three")` texts ignored | `test_legend_order.py::TestOrderText::test_text_after_a_number_retitles_that_key` |
| B5 | `order(2 1) label(1 "Data")` relabels the fit | `TestLabelByNumber::test_label_names_the_plot_not_the_position` |
| B5 | `-` lines dropped; `lastlabel()` named | `TestTextOnlyRows::test_a_dash_inserts_a_text_row`, `TestLastLabel::*` |
| B6 | `xtitle("")` draws `weight`, `ytitle("")` draws `mpg` | `TestEmptyTitles::test_empty_text_removes_the_title` |
| B7 | `ytitle2("P2")` quotes; `"a" "b"` one line; `size(large)` verbatim | `TestSecondAxisTitleIsATextbox::test_text_lines_size_colour` |
| C2 | 2245/2246, 49/50, ~4% random | `TestNlsw88AndCensusRegressions`, `TestEveryFrequencyHistogramSumsToN` |
| C2 | density bars rescaled to remaining rows | `::test_density_bars_integrate_to_one_on_ttl_exp_bin_27` |
| C2 | `start()` within reldif 1e-5 drops rows | `TestStartTolerance::test_rows_below_a_tolerated_start_land_in_bar_zero` |
| D1 | `color background "255 0 0"` malformed key | `TestQuotedValuesAreRead::test_a_quoted_rgb_with_opacity_reaches_the_alpha_reader`, CQ-01 |
| D1 | d3colors draws #606060 with 0 warnings | `::test_a_scheme_written_with_quoted_values_is_read`, `::test_both_modes_draw_the_quoted_background_and_p1` (a scheme file the test writes; third-party files are out of scope, Q30) |
| E1 | `fmt(%10.0g)` → `6e+03` | `test_kpi_format.py::TestFirstPaint::*` (fixture row) |
| E1 | `%9,2f`, `%21x`, `%16H` raw | `%9,2f`: fixture row; `%21x`/`%16H`: OV-121/122, `TestRefusedOnACard` |
| E1 | `%td` of 15000 → `15000.0`; date KPIs ignore `fmt()` | KF-01 (`%td` on `max(when)`), `TestEffectiveFormat::test_the_rule` |
| E1 | own `%g` dropped (6165.26 vs 6165.257) | `TestEffectiveFormat` (`%8.0gc`), KF-02 |
| E2 | served g1=3, g2=5, k1=3 where 5 implied | `test_filter_exclusion_sets.py::TestAnExclusionHoldsAgainstEveryMove::test_saved_state_…`, `::test_served_state_…` |
| E3 | `%td` dropdown `2001-12-31 00:00:00`; `%9.0fc` dropdown `3799` | `test_display_format_sites.py::TestDropdown::test_labels_are_statas_text_in_both_modes` |
| E3 | date sliders `%d %b %Y`, step span/100; period sliders stop mid-period; `0[.]00` | `TestSliders::*` |
| E3 | tooltips `{%F}`; `%tC` loses time | `TestTooltips::test_fields_carry_custom_and_a_formatter_with_the_format` (`%tc` case; add `%tC`, F-22) |
| E3 | KPI dates fixed picture | S11 `TestFirstPaint` date rows |
| E3 | `%tm` axis `Jan 2000` | `TestDateAxis::test_ticks_read_as_stata_in_both_modes` against `axis_truth.json` probe `e3_tm_axis_lab` recorded by 14-03 (F-02 closed) |
| E14 | items 1-5 | `TestTheServedPageDeclaresTheSavedPagesViewport`, `TestALinkedFigureDimsAlike`, `TestALinkedRangeLayerDrawsTheGroupsSource`, `TestTheBsGridStylesheet` + Chrome, `TestTheSavedBsPagePutsItsFilterBarBelowTheHeader` |
| F1 | rc 0 after 1.7 s with the port held; errno 48 on stderr | SPU-01; `test_the_childs_bind_failure_is_reported_with_its_stderr` |
| F1 | leftover `app.py` on 5006 "succeeds" | SPU-01 (same mechanism) |
| F1 | `--port 80` serves on 1024 | `TestPortRefusals`, `test_the_port_is_refused_in_every_place_it_is_read` |
| G1 | `__dash_row__` overwritten; y 100..140 drawn 0..4 | `test_reserved_names.py::TestTheDashPrefix::test_a_column_under_the_prefix_is_refused_in_both_modes`, QS-06 |
| G1 | `__dash_pc_row__`, `__mlabel__*` share the namespace | `test_internal_column_names.py`, `test_a_name_dash_no_longer_makes_is_drawn_with_its_own_values` |
| G1 | `__dashq<k>`/ustrfix need room at `c(maxvar)` | excluded (Q7 residual; recorded 07-07) |
| G2 | string x → nonsense glyphs; lfit/histogram crash | `TestAStringPlotVariableIsRefused::test_in_both_modes`, SV-* |
| G3 | 5,000,001-obs histogram r(134); note "72 MB" for 1.4 MB | `TestTheCount::…six_million_rows…`, `test_the_note_reports_embedded_bytes` |
| G5 | `filter(größe)` r(198); `dash kpi mean(größe)` r(198) | `TestFilterOnAUnicodeName`, UN-01, UN-02/03 |
| G6 | float 0.1 → 17 digits in labels and dropdowns | `TestMarkerLabels`, `TestDropdown` (`f`) |
| G6 | tooltip 12345.67 → 1.235e+4 | `TestTooltips` (4099 → `4,099`; add 12345.67 for parity with the audit, minor) |
| G6 | `_dash_format_kpi_value(1234567.5,'%9.0g')` → 1.23457e+06 | `test_display_format_writer.py::TestPythonWriter::test_every_numeric_display_matches_stata_exactly` (1234567.5 row), S11 |
| G16 | `valuelabel` named; hover shows numbers | `TestValueLabelsOnAxes::test_valuelabel_draws_the_label_set`, `TestHoverShowsValueLabels::test_hover_foreign_shows_domestic_and_foreign` |
| K2 | false floors; CustomJSTicker; annotations at import; launcher ignores rc; no test below the floor | `test_version_floor.py::*`, `test_serve_launcher.py`; the last is the recorded residual (09-12) |
| X1 | '01'/'1.0'/' 2' → '1'; 'nan'/'None'/'NaT' dropped; saved keeps none for '1'; 5e-05 unselectable; colorvar 'nan' | `TestOptionValues::*`, `test_nan_none_nat_and_blank_are_listed…`, `TestBothModes::test_both_modes_select_the_same_rows`, `TestColorvarStrings` |
| X2 | interval path under `colordiscrete`; `colorcuts(0 2 4)` keeps `≤0`; `colorlevels` etc. named; no z options | `TestColordiscreteWithCuts`, `TestCutsBelowTheMinimum`, `TestColorlevels`, `TestColorvarminmax`, `TestZOptions`, CV-03/05 |
| X2 | continuous default is documented | excluded (Q5) |

## 3. Closure records (one row per gap; what the closing task writes and S19 reads)

| Gap | Section, closing task | Commit subject ends | CHANGELOG list (D2) | BUGS.md title (no `"`) | Residual clause |
|---|---|---|---|---|---|
| B1 | S14, 14-09 | `(GAPS2 B1)` | Results that change | Axis-label rules misread quoted numeric text, multi-line labels and numlist forms | none |
| B2 | S18, 18-14 | `(GAPS2 B2)` | Results that change | Label and tick values do not widen the axis and xscale/yscale range() narrows or inverts it | Stata's 2.2 % margin versus Bokeh's padding (inner hulls compared) |
| B3 | S13, 13-12 | `(GAPS2 B3)` | Results that change | Textbox sub-option abbreviations are drawn as title text | none |
| B5 | S15, 15-09 | `(GAPS2 B5)` | Results that change | legend order() text and label() after order() are applied to the wrong keys | a layer that drew nothing has no key, so order() naming its number draws nothing |
| B6 | S13, 13-15 | `(GAPS2 B6)` | Results that change | An empty xtitle() or ytitle() does not remove the axis title | none |
| B7 | S13, 13-03 | `(GAPS2 B7)` | Results that change | ytitle2() and xtitle2() draw their quote marks and ignore textbox grammar | none |
| C2 | S05, 05-06 | `(GAPS2 C2)` | Results that change | A continuous histogram dropped the observation at its last edge, and the rows a tolerated start() lies above | none |
| D1 | S06, 06-04 | `(GAPS2 D1)` | Results that change | A scheme's quoted values (RGB colours, %opacity) were dropped without a warning | CMYK, hsv and colour*# values stay GAPS2 D7's; third-party scheme files out of scope (Q30) |
| E1 | S11, 11-07 | `(GAPS2 E1)` | Results that change | KPI fmt() accepts formats the card then does not apply, and %w.0g rounds the card to one significant digit | none |
| E2 | S17, 17-15 | `(GAPS2 E2)` | Results that change | An excluded graph or card keeps the rows of the last move made by a filter that does not exclude it | none |
| E3 | S12, 12-15 | `(GAPS2 E3, G6)` | Results that change | Dates and formatted numbers on date axes, filter widgets, KPI cards and tooltips ignore the variable's Stata display format | none |
| E14 | S10, 10-09 | `(GAPS2 E14)` | Results that change (bar move) and Fixed in WP-28 (served items) | The saved page and the served app present the dashboard differently | the `filterposition(left)` layout difference is recorded, not fixed |
| F1 | S09, 09-07 | `(GAPS2 F1)` | Fixed in WP-28 | dash serve returns rc 0 when no server ran, and an out-of-range --port is clamped instead of refused | none |
| G1 | S07, 07-10 | `(GAPS2 G1)` | Changed behaviour | An internal column name could overwrite a user variable, and only __dashq was reserved | qualifier/by()-order/ustrfix columns stay in the dataset (room at c(maxvar)); a variable named like a Bokeh glyph field is still shadowed |
| G2 | S08, 08-05 | `(GAPS2 G2)` | Changed behaviour | String variables are accepted as plot variables where twoway refuses them | a family whose r(109) wording cannot be matched through syntax is pinned by rc only (both texts recorded) |
| G3 | S08, 08-11 | `(GAPS2 G3)` | Fixed in WP-28 | The data limit counts exported values, so large histograms, densities and fits are refused although the page would be small | the export stays JSON; row-drawing layers stay bounded; the served app embeds every row |
| G5 | S07, 07-15 | `(GAPS2 G5)` | Fixed in WP-28 | Unicode variable names are refused by filter() and dash kpi and ignored by the renderer | none |
| G6 | S12, 12-15 | `(GAPS2 E3, G6)` | Results that change | %g formats (Stata's default) and float storage are not reproduced, so values show full double expansions | none |
| G16 | S14, 14-15 | `(GAPS2 G16)` | Results that change | Value labels are never drawn on axes or in tooltips | none |
| K2 | S09, 09-15 | `(GAPS2 K2)` | Requirements | The declared minimums (Python 3.8, bokeh 3.0) are false: every render needs bokeh 3.6+, and the served app crashes at import on 3.8/3.9 | no Python 3.10 venv matrix: the floor is the tested baseline (Q8) |
| X1 | S17, 17-06 | `(GAPS2 X1)` | Results that change | A dropdown rewrites string codes to numbers, drops the categories nan None and NaT, and cannot select small numbers on the saved page | none |
| X2 | S16, 16-10 | `(GAPS2 X2)` | Results that change | colordiscrete with colorcuts() is read as intervals, cuts below the minimum are kept, and colorlevels(), colorvarminmax and the z options are not drawn | the continuous default and colorrule()/colorstart()/colorend() stay as documented (Q5) |

Every title is unique and holds no `"`; every Resolution is written `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). … Pinned by …` and appended at the end of BUGS.md (D3); S19's inventory (19-01) reads exactly these forms, and its residual checkpoint (19-03) approves the clauses above plus C4/E4 before 19-04 writes the GAPS2 Tracked lines.

## 4. Decision compliance (DISCOVERY.md Q1-Q31 and the four research amendments)

| Decision | Implemented by | Contradiction after the fixer pass |
|---|---|---|
| Q1 focused discovery | n/a | none |
| Q2 sections by component | `sections/index.md`, all sections | none |
| Q3 omit C4/E4; no estimator ports to `_FILTER_JS` | S01 (no marker), S05, S10, S17, S18, S19 (deferred line) | none |
| Q4 (amended) entries land closed in the fix commit; WP-28 lists all 22 up front | S01 TR-01.6/01.8; every closing task (D3 form) | none |
| Q4/Q23 amendment: `**GAPS2 closed:**`, `#### GAPS2 traceability`, GAPS2.md in `_ROOT_ALSO` | S01 TR-01.1..01.6, S19 | none |
| Q5 X2 explicit forms; continuous default kept | S16 | none |
| Q6 formats written/refused (`%x`, `%H`, `%L` refused) | S04, S11, S12; PRD §7 | none |
| Q7 (amended) `__dash` prefix, r(110); jitter and mlabel columns renamed; residuals recorded | S07, S19 | none |
| Q8 declare the tested floor; no venv matrix | S09 | none |
| Q9 count what the page embeds; JSON stays | S08 | none |
| Q10 numbers as numbers in both modes; node+pandas parity | S17, S03 | none |
| Q11 saved bs bar below the header; ALLOWED exemption removed | S10 | none |
| Q12 held port refused; /health 30 s; URL once it answers; range refused | S09 | none |
| Q13 numeric missing unlisted; `""` blank row; colorvar string path | S17 | none |
| Q14 (amended) SVG helper; B2 from SVG-fitted extents; `.Graph` probed once | S02, S18 | none |
| Q15 stateful node runner, no browser | S03 | none |
| Q16 G2 cscript over every type and position, generated | S08 (generated block in `test_adversarial.cscript`, D11) | none |
| Q17 branch `s3-bugs`; merge reported, never run | all; S19 | none |
| Q18 one commit per gap; shared components in their own commits | D1; every section's commit boundary | none |
| Q19 parallel worktrees; `patch -p1`; own `STATATMP` | PLAN.md, index.md step 0/1; `scripts/stata_slot.sh` | none |
| Q20 help + CHANGELOG per gap; before/after values | D2; every closing task; S19 | none |
| Q21 exit = WP-27 gate from an installed package | S19 | none |
| Q22 silent when honoured | every section's Boundaries | none |
| Q23 GAPS2 Tracked lines updated; audit text kept | S19 | none |
| Q24 old values from the recorded failing output | every task 1 and closing task; S19 | none |
| Q25 demo pages regenerated at closeout | S19 (regenerate, not commit: the pages are untracked) | corrected by measurement, see §3 |
| Q26 dropdown labels merged by display text | S12, S17 | none |
| Q27 below-floor Bokeh: refuse, print the pip command | S09 | none |
| Q28 cert-suite growth ≤ about five minutes | D11: one new script; S19 measures | none |
| Q29 invariants in AGENTS.md | D14: S19 | none |
| Q30 third-party scheme files out of scope | D13: S06; PRD §7 | none |
| Q31 fixture provenance stamp | D12: every fixture-writing section | none |
| Amendment 3 (jitter renamed; glyph-field residual) | S07 | none |
| Amendment 4 (B2 SVG-fitted) | S18 | none |
| CLAUDE.md rule 10 (console Stata only) | `scripts/stata_slot.sh` everywhere (D6) | none |
| CLAUDE.md rule 11 (full suite once before a commit) | D1; S08 corrected (F-05) | none |


## 5. Tasks beyond the gap set (all approved)

| Tasks | What they add | Traces to | Why kept |
|---|---|---|---|
| S01 01-01..01-03 (3) | The tracking guards learn GAPS2.md; WP-28 opened in ROADMAP.md; the CHANGELOG markers; the BUGS.md and commit forms | PRD §8-§9; DISCOVERY Q4 (amended), Q23; D2, D3 | Without them no closure can be proven or counted (CLAUDE.md rule 2). |
| S02 02-01..02-07 (7) | `scripts/svg_truth.py`, `test/cert_svg.do`, the smoke fixture, and the one new certification script `test/test_gaps2_truth.cscript` | DISCOVERY Q14, Q28, Q31; D11, D12 | Truth for B1, B2, B3, B5, B6, B7, D1, G16 and X2 is measured once through one reader (research decision 5). |
| S03 03-01..03-05 (5) | The stateful node runner `test/js_runner.py` (`JsSession`, `mask_parity`) | DISCOVERY Q10, Q15 | E2, X1 and C2 need chained moves and node-versus-pandas parity that no browser is required for. |
| S04 04-01..04-16 (16) | The display-format writer and its JavaScript twin, storage types, the format fixture | DISCOVERY Q6; research decision 1 | E1, E3 and G6 all write through it; it lands first so three sections share one implementation. |
| 10-10, 18-15, 19-03 (3 checkpoints) | Maintainer approval of the one deliberate picture change (the bs filter bar), of the axis-extent changes and the `.Graph` verdict, and of the deferred residuals | D8 | A human sees each visible change and each deferral once, before it is written into the documents. |
| S19 19-01..19-12 (12) | Inventory, CHANGELOG reconciliation, AGENTS.md invariants (D14), GAPS2 Tracked lines, WP-28 DONE, demo pages regenerated (Q25 as corrected), the release dated, both pytest suites, the timed certification suite (Q28), the release gate, the measurements and the merge command | PRD §8-§9; DISCOVERY Q21, Q23, Q25, Q28, Q29 | The exit criterion is measured on the merged tree, once, and recorded. |

Total: 46 tasks; the other 159 tasks belong to the gap sections 05-18.

## 6. Review findings resolution

| Report | Raised | Applied as written or as DECISIONS adjusted | Superseded by a later decision | Rejected |
|---|---|---|---|---|
| `review/consistency.md` | 36 | 32 | 4: #6 option B (D4 keeps S15 on S13's script, batch 3); #7's per-section registrations (D11: one script, S02 registers); #18's label suffixes (Q26: entries merged by display text); #19's 06-05b (D13: 06-05 deleted) | 0 |
| `review/feasibility.md` | 51 | 47 | 4: #4's present-tense `<done>` (D7: past tense); #14's two-wave batch 2 (D4); #16's `until mkdir` loop (index.md step 0's wrapper); #18's CV-08 and #42's trimmed d3colors fixture (D13, third-party out) | 0 |
| `review/requirements-security.md` | 24 | 23 | 1: F-02's probe values (sp500 is 2001: ticks 492(3)501, not 480(3)491) | 0 |
| Total | 111 | 102 | 9 | 0 |

Compliant findings (feasibility #10, #19 in part, #26, #35, #36; consistency #35, #36) needed no edit and are counted as applied.

## 7. Gap resolution log (what validation itself found and fixed)

| # | Found | Resolution | Where |
|---|---|---|---|
| 1 | E3 plan step 4 (twoway's `%tm` axis-label truth) had no owner (F-02) | S14 task 14-03 records probes `e3_tm_axis`/`e3_tm_axis_lab`; S12 reads them by id and fails when absent | section-14, section-12 |
| 2 | Decision D2 had been misread in the resumed session's first brief (markers in sub-lists under one heading) | The markers sit in the release's existing lists plus a new `### Fixed in WP-28`; every WP-28 line ends `(WP-28, <ID>)`; S01 TR-01.7, S19 and every closing task rewritten | all sections, index.md R3, BRIEF.md |
| 3 | A single certification script cannot be handed to `scripts/stata_slot.sh` (the runner changes into `test/` first) | The two-line driver do-file (BRIEF.md "Running one cscript", index.md step 0a); `<repo>` is the tree under test (the section's worktree) | BRIEF.md, index.md, every section with a cscript run |
| 4 | `s3-bugs` cannot be checked out in a second worktree, so "commit on s3-bugs" from a worktree was impossible | Sections commit on `wp28-s<NN>`; the merger lands each commit with `format-patch | patch -p1` and `git commit -F` in the batch's merge order | index.md step 1, every closing task |
| 5 | A third hygiene pin (`with_probes == 13`, :315) existed and the runner's blocks run to 66 | S02 registers block `// 67.`, sets 66/48 and states :315 unchanged | section-02, section-19 |
| 6 | `_MUST_WARN` was misspelled in R6 and its "only S18 edits" rule would have S12 and S14 commit red trees | An entry is edited only by the section whose gap silences it (S12, S14, S18), every key kept | index.md R6, sections 12, 14, 18 |
| 7 | The mechanical CDATA pass had corrupted five files (a `<name>` in prose matched as a tag) | Repaired in sections 01, 02, 07, 08, 11; 205 of 205 tasks parse | §9 |
| 8 | Section 12 closes E3 and G6 through one code path in one commit, which a `grep -F "(GAPS2 <ID>)"` inventory would miss | The inventory regex accepts a subject naming several ids; index.md counts 21 fix commits for 22 gaps | section-19 19-01, section-01 TR-01.9, index.md |
| 9 | Refinement Q25 assumed the demo pages were checked in; none is tracked (`.gitignore` `*.html`) and a root `.html` would fail the packaging allowlist | S19 regenerates the pages and does not commit them (19-07); PRD §7 says so | section-19, PRD.md |
| 10 | The wrapper must exist before worktrees are created, and D11's "before" wall time had no source | index.md step 0a commits `scripts/stata_slot.sh` as `(WP-28 S00)`; step 0b times a `make cert` baseline that 19-10 compares against | index.md, PLAN.md, section-19 |

## 8. Deliberately excluded or deferred (recorded in PRD §7, the BUGS.md residual clauses and S19's deferred list)

| Exclusion | Decision | Where recorded |
|---|---|---|
| C4/E4: the saved page never re-estimates fitted or smoothed lines after a filter move | Q3 | GAPS2.md Tracked line `Deferred (WP-28)` (S19); PRD §7 |
| G1: qualifier, by()-order and ustrfix columns stay in the user's dataset (room at `c(maxvar)`); a user variable named like a Bokeh glyph field is still shadowed in `hover()`/`mlabel()` | Q7 amended | G1 BUGS.md residual; GAPS2 Tracked residual; PRD §7 |
| G3: the export stays JSON; row-drawing layers stay bounded; the served app embeds every row | Q9 | G3 residual; PRD §7 |
| X2: the continuous default and `colorrule()`, `colorstart()`, `colorend()` stay as documented | Q5 | X2 residual; PRD §7 |
| E14: the `filterposition(left)` layout difference is recorded, not fixed | research amendment | E14 residual; dash.sthlp |
| E1/E3: `%x`, `%H` and `%L` are refused with r(198), not written | Q6, F-15 | PRD §7; S04 help text |
| D1: third-party scheme files are neither swept nor pinned; CMYK, hsv and `colour*#` values stay GAPS2 D7's | Q30, D13, F-11 | S06; D1 residual; PRD §7 |
| K2: no Python 3.10 venv matrix; the floor is the tested baseline | Q8 | S09 |
| The other 100 GAPS2 gaps and any new plot type | PRD §7 | — |


## 9. Mechanical validation (scratch validator, read-only, run after the fixer pass)

| Check | Rule | Result |
|---|---|---|
| XML | every `<task>` block parses with `xml.etree`; no `<![CDATA[`/`]]>` outside a task; no entity escapes | 205 of 205 parse (5 failed before the repair) |
| Ids | `NN-01..NN-k` sequential, no gaps, no letter suffixes | 19 of 19 sections |
| Names | 3-8 words, verb first | 0 violations (49 before) |
| Files | ≤ 3 paths, no annotations; checkpoints `none` | 0 violations (18 ` (new)` and 7 hidden fourth files before) |
| Done | one past-tense sentence | 0 violations |
| Headings | BRIEF.md's fourteen sections in order | 19 of 19 |
| Amendments block | closing sentence says the text conforms | 19 of 19 |
| Naming drift | `MUST_WARN`, `font_size` from `svg_texts`, `_DASH_VARNAME_RE` in S14, `meta` key, `__mlabel__` in S17, old Resolution form, `(WP-28)` without an id, retired script names, `flock`, `.mlib`, `15341.0`, `:294`, pre-D11 counts, `_dash_fmt_tick_code`, sub-list wording, `480(3)491`, brief citations, container paths | 0 errors |
| Stata runs | no `arch -arm64`/`make cert`/`make gate` inside S02-S18 tasks | 0 errors |
| Certification blocks | S05, S11, S13-S18 name `test_gaps2_truth.cscript` and the `GAPS2_ONLY` gate | 8 of 8 |
| Checkpoints | last task of S10 and S18; exactly one in S19; none elsewhere | as required |
| Cross-references | every `NN-MM` task id cited in any plan file exists | 0 unresolved (14 warnings are line ranges such as `mpg 12-41`, `scale.class:19-27`) |
| Manifest | risk, batch, dependencies, blocks and task counts in index.md and PLAN.md equal every section header | 19 of 19; totals 205; 4 green, 9 yellow, 6 red |
| Contracts | the shared signatures and names appear identically in every section that uses them (hover row and builder, axis spec, `_dash_colorvar_bins`, the KPI marker comment and call, `_dash_dropdown_mask`, `NODE`, `e3_tm_axis_lab`, the legend-probe region, the truth script's block form) | verified by grep across the sections |
| Symptom tests | every test name cited in §2 exists in its section's stubs | 49 of 49 rows |

Baseline before the pass: 207 errors, 43 warnings. After: 0 errors, 14 warnings (all false positives).

## 10. Validation result

**93 of 93 GAPS2 plan steps are covered, amended by a recorded decision, or excluded by a recorded decision; 0 partial, 0 missing. 49 of 49 measured symptoms have a regression test that fails at 91d97be. 46 tasks beyond the gap set, all approved as shared components, checkpoints or the closeout. 111 review findings applied or superseded, none rejected. 205 tasks, all mechanically valid.** The plan is ready to execute from `sections/index.md` step 0.
