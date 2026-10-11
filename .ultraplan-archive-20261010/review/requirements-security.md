# WP-28 plan review — completeness, decisions, security, edge cases

> Reviewed 2026-09-25 against `.ultraplan/PRD.md`, `DISCOVERY.md` (23 answers, 4 amendments, exclusions), `RESEARCH.md`, `PLAN.md`, `sections/BRIEF.md`, `sections/index.md`, all nineteen `sections/section-*.md`, and the 22 GAPS2.md entries in scope. Anchors are `file:line` in the plan files; codebase anchors were spot-checked at `91d97be`.
>
> Severity: **critical** = the plan as written cannot be executed to its own exit criterion or breaks a CLAUDE.md rule; **major** = a gap step, decision or guard is missed and the closeout would fail or a defect would ship; **minor** = a boundary, test or wording that should be added before execution.

Totals: **1 critical, 6 major, 17 minor.** No plan step is EXCLUDED without a DISCOVERY decision except D1 step 2's D7 forms (recorded as a residual by S06, but not in PRD §7 or S19's residual list — minor). One GAPS2 plan step is MISSING an owner (E3 step 4, the twoway `%tm` axis-label truth).

---

## 1. GAPS2 plan-step coverage (22 gaps)

Status key: **covered** (every step has a task), **amended** (a DISCOVERY decision replaced the step and the replacement has a task), **excluded** (a DISCOVERY decision removes the step), **partial** (a task delivers part; the rest is named), **MISSING** (no task delivers it).

| Gap | Plan step (GAPS2 numbering) | Task id(s) | Status |
|---|---|---|---|
| B1 | 1 tokenise with `_textbox_string_end`; strings are label lines | S14 TR-14.2/14.3, 14-03 | covered |
| B1 | 2 expand numeric parts in dash.ado with `numlist`; write expansion into the spec; keep `_MAX_AXIS_TICKS` | S14 TR-14.11..14.13, 14-04 (ado); TR-14.1, 14-03 (Python bound) | covered |
| B1 | 3 pytest each form in both modes | 14-01 `TestNumlistForms`, `TestLabelledTicks`, `TestTheBound` | covered |
| B1 | 4 cscript reading twoway's tick positions and label text (SVG) | 14-02 (`b1_label` probes), 14-05 (AL-05..AL-16) | covered |
| B2 | 1 hull of data ∪ label/tick positions (unless `norescale`) ∪ `range()` after the layers | S18 TR-18.6..18.10, 18-04, 18-05 | covered |
| B2 | 2 `range(#)` is a value; accept `r()`, missing; log/date; `yscale2`/`xscale2` | 18-03 (TR-18.1..18.3), 18-05 (TR-18.7), 18-06 (TR-18.12) | covered |
| B2 | 3 pytest both modes | 18-01 | covered |
| B2 | 4 cscript recording `.Graph.yaxis1` min/max for ~20 combos into a fixture | 18-02 (25 SVG-fitted probes + `.Graph` candidates + verdict), 18-10 (AE-01..06) | amended (Q14 amendment: SVG is the truth, `.Graph` probed once) |
| B3 | 1 `_TEXTBOX_SUBOPTS` → (full, minimum) table | S13 TR-13.1, 13-03 | covered |
| B3 | 2 canonicalise names in `_parse_textbox_opt`; name the rest; route `axis(2)` | 13-03, 13-04 (TR-13.3/13.4), 13-05 (Python route), 13-06 (Mata route) | covered |
| B3 | 3 pytest table over every spelling on all six text options, both modes | 13-01 `TestEverySpellingOnEveryOption::test_spelling` | covered |
| B3 | 4 cscript comparing twoway's title text and colour (SVG) | 13-01 TBG-01, 13-02 fixture | covered |
| B5 | 1 parse `order()` with `_textbox_string_end`/`_textbox_lines` | S15 TR-15.1, 15-05 | covered |
| B5 | 2 key text by number (default → label → order → lastlabel), then select/order | TR-15.3, 15-06 | covered |
| B5 | 3 `-` entries as `LegendItem`s (placeholder renderer if needed) | TR-15.3, 15-06 (research W §1a: `renderers=[]` draws; no placeholder) | covered |
| B5 | 4 pytest both modes; cscript vs twoway's SVG legend | 15-01 (py + LO-01..08), 15-04 fixture | covered |
| B6 | 1 empty ≠ absent in `_dash_axis_labels`; same for `{n}title2` | S13 TR-13.7, 13-04, 13-07 | covered |
| B6 | 2 pytest both modes: `xtitle("")`, `ytitle("")`, `xtitle("", size(large))`, histogram/kdensity default | 13-01 `TestEmptyTitles` (4 tests) | covered |
| B6 | 3 cscript: twoway SVG has no axis-title text; dash `axis_label` empty | 13-01 TBG-04 | covered |
| B7 | 1 read `{n}title2` through `_dash_textbox`, join lines, name the rest | S13 TR-13.8, 13-09 | covered |
| B7 | 2 apply `size()`/`color()` to the y2/x2 axis | TR-13.8, 13-09 | covered |
| B7 | 3 pytest both modes: quoted, multi-line, compound-quoted, sub-option | 13-01 `TestSecondAxisTitleIsATextbox::test_text_lines_size_colour` (compound-quoted case not listed — minor, F-19) | partial |
| B7 | 4 extend JSE-46 to compare the right-axis label with twoway's SVG | 13-01 (`jg46l`) | covered |
| C2 | 1 floor/clamp count; last edge `start + h*bin`; drop tolerance edge | S05 TR-05.1..05.3, 05-03 | covered |
| C2 | 2 same rule in `_FILTER_JS` recount; served follows | TR-05.5, 05-03 | covered |
| C2 | 3 property test (random, bin 1..100, `width()`, `start()` just above min) summing to N saved/served/node; nlsw88 and census regressions | 05-01 (`TestEveryFrequencyHistogramSumsToN`, `TestNlsw88AndCensusRegressions`, `TestBothModes`, `TestTheJavaScriptRecountAgrees`) | covered |
| C2 | 4 `twoway__histogram_gen generate()` output into `extract_stat_truth.do`; pin in `test_statistical_truth.py` | 05-02 | covered |
| D1 | 1 tokenise as Stata does (category, key, quoted value with ` %NN`) | S06 TR-06.1/06.2, 06-02 | covered |
| D1 | 2 accept `"R G B"`, `"R G B %NN"`, CMYK, `"hsv h s v"`, `colour*#` (shared with D7) | 06-02 for the RGB/%NN forms; CMYK/hsv/`*#` declared D7's (S06 Boundaries :250-252) | partial — no DISCOVERY decision excludes the D7 forms; recorded as a residual in the D1 entry only (F-11) |
| D1 | 3 warn once per unreadable line, naming it; never store a malformed key | TR-06.4, 06-02 | covered |
| D1 | 4 all 129 local files parse; pin d3colors p1-p15 | TR-06.8 (`DASH_LOCAL_SCHEMES=1` sweep), `test_d3colors_p1_to_p15_are_the_files_rgb_values` | covered |
| D1 | 5 compare with Stata's SVG export under d3colors | 06-05 (optional; deferred to S19 if `cert_svg.do` absent) | covered (conditional) |
| E1 | 1 shared formatter: `%w.dg`, comma, `%x`/`%H` refused, `%t`; use in `_dash_format_kpi_value` and `dash_numfmt`; carry own `%g` | S04 04-03..04-05; S11 11-02, 11-03 | covered |
| E1 | 2 refuse r(198) in `_dash_validate_value 'format'` | 04-08 | covered |
| E1 | 3 cert test: card equals Stata's kpi display per accepted format, both modes, after a move | 11-06 (KF-01..05) | covered |
| E1 | 4 fixture of `display` outputs; compare Python and node | 04-02 (`format_truth.json`), 04-01 `TestPythonWriter`, `TestJavaScriptTwin` | covered |
| E2 | 1 per-target mask = AND of non-excluding filters; link group one target; panels follow owner | S17 TR-17.9, TR-17.11, 17-06, 17-07 | covered |
| E2 | 2 saved: one mask per exclusion set; rewrite every target; targets + sets in callback args | TR-17.9/17.10, 17-07 | covered |
| E2 | 3 served: `_on_filter_change` with per-target widget subsets | TR-17.11, 17-06 | covered |
| E2 | 4 replace `TestExcludeHoldsWhileItsOwnFilterMoves` with multi-move sequences both modes | 17-01 stubs, 17-07 rewrite; S03 03-05 pin | covered |
| E2 | 5 Stata truth on auto (`count`, `summarize`); rewrite dash.sthlp:1135-1138 | 17-02, 17-08 | covered |
| E3 | 1 one formatter (all `%t` kinds, numeric with `c` and comma) with JS twin | S04 | covered |
| E3 | 2 use for dropdown labels, KPI first paint/`dash_apply_kpis`, tooltips (`CustomJSHover`), date-axis ticks (`CustomJSTickFormatter`), slider labels | 12-02, 11-02/11-03, 12-04, 12-05, 12-02 | covered |
| E3 | 3 period kinds on a numeric slider (step 1) with the formatter; served shares | 12-03 | covered |
| E3 | 4 record Stata truth: `display %tm 480`, `%tq 160`, `%tdDD/NN/CCYY 15000`, a `%tC` value, `%9.0fc 4099`, **and the twoway axis labels of a `%tm` variable**; compare Python/node and widget/card/axis/tooltip text both modes | display values: 04-02 (`format_truth.json` covers `%tm 480`, `%tq 160`, `%tdDD/NN/CCYY`, `%tC` pre-1972, `%9.0fc`); site texts: S12 12-01 stubs | **MISSING** for the twoway `%tm` axis-label probe: S12 hands it to S14 (S12:436-438, :798-802) but S14's probe tables (:458-497) do not register it (F-02) |
| E14 | 1 viewport meta in the served template | S10 10-03 | covered |
| E14 | 2 dimming from the generated app for linked figures | 10-04 | covered |
| E14 | 3 rspike/rconnected from the group's rows in the app | 10-05 (shared source + view, as the saved page does; S10:1014-1016 records the wording difference) | covered |
| E14 | 4 served bs stylesheet (992 px rule, KPI min heights); saved bar below the header; drop the ALLOWED exemption | 10-06, 10-07, 10-01 (TR-10.11) | covered |
| E14 | 5 tests in `test_mode_parity.py`, `test_served_bs_layout.py`, Chrome at 375/900/1440 | 10-01, 10-02 (runner widths 375/768/1440; recorded S10:1011-1013) | covered |
| E14 | — `filterposition(left)` header placement | `test_filterposition_left_is_recorded_not_changed`, dash.sthlp | excluded (research amendment) |
| F1 | 1 launcher treats non-zero exit as failure, captures stderr; `dash serve` errors naming the port | S09 TR-09.2/09.3/09.4, 09-03, 09-05 | covered |
| F1 | 2 poll `/health` up to 30 s; print the URL once it answers | TR-09.2 step 5, 09-03 | covered |
| F1 | 3 optional test-bind | TR-09.2 step 2 (`prebind`), 09-03 | covered |
| F1 | 4 argparse refuses `--port` outside 1024-65535; drop the unreachable clamp | TR-09.1, 09-03, 09-04 (all three clamps) | covered |
| F1 | 5 pytest against a held socket; cscript `_rc != 0` | 09-01 (`test_serve_launcher.py`, SPU-01..03), 09-02 | covered |
| G1 | 1 rename internals / reserve `__dash` and refuse r(110) | S07 TR-07.1/07.2/07.5, 07-03, 07-07 | covered (Q7: reserve) |
| G1 | 2 build qualifier/by()-order/ustrfix columns in a temporary frame | — | excluded (Q7; residual recorded 07-07, S19) |
| G1 | 3 pytest: `__dash_row__` and `__mlabel__y` drawn with own values | `test_a_name_dash_no_longer_makes_is_drawn_with_its_own_values` (`__mlabel__y`, `_x_jit`, …); `__dash_row__` is now refused by decision | covered (amended by Q7) |
| G1 | 4 cscript at `c(k)==c(maxvar)` | — | excluded (Q7 residual) |
| G2 | 1 `numeric` in the four parsers, twoway's message, r(109) | S08 TR-08.1, 08-04 | covered |
| G2 | 2 keep `colorvar()`, `mlabel()`, `hover()`, `by()` accepting strings | S08 Boundaries; `test_a_string_in_an_option_is_not_refused` | covered |
| G2 | 3 cscript over every type and position vs twoway | 08-02 (generated, 89 cases), 08-04 | covered (Q16: 40 types) |
| G2 | 4 pytest: hand-written spec with a string plot column → named refusal | 08-01 `TestAStringPlotVariableIsRefused`, 08-05 | covered |
| G3 | 1 count only what the page embeds | S08 TR-08.6..08.8, 08-07, 08-08 | covered |
| G3 | 2 binary export | — | excluded (Q9) |
| G3 | 3 size note on what is embedded | TR-08.10, 08-09 | covered |
| G3 | 4 6M-obs histogram builds, bins equal `twoway__histogram_gen`'s, page under 2 MB; 6M scatter refused | `TestTheCount::test_a_histogram_over_six_million_rows_passes_and_a_scatter_is_refused` (row count as a number), DL-01 (74 obs, bins vs generator) | partial — no build at 6M rows and no page-size assertion (F-12) |
| G5 | 1 `ustrregexm("^[\p{L}_][\p{L}\p{N}_]*$")` + `ustrlen<=32`, then `unab`/`confirm` | S07 TR-07.6/07.7, 07-08 | covered |
| G5 | 2 correct the refusal messages | TR-07.6 (echo class), 07-08 | covered |
| G5 | 3 cscript: `dash kpi mean(größe)` = `summarize`; range and dropdown widgets | 07-02 UN-01..UN-03 | covered |
| G5 | 4 pytest: renderer builds a filter widget over a Unicode column | `TestFilterOnAUnicodeName::test_a_range_widget_is_built_in_both_modes` (+ by/hover/colorvar widening) | covered |
| G6 | 1 export storage type; floats as shortest float32 repr | 04-06, `_dash_float32_text` (04-03; the fixture decides), 12-07 | covered |
| G6 | 2 `%w.dg`/`%w.dgc` in Python and JS | 04-03, 04-05 | covered |
| G6 | 3 use in marker labels, tooltips, KPI cards, dropdown labels, CSV | 12-06, 12-04, S11, 12-02, 12-07 | covered |
| G6 | 4 fixture of ~200 values (`%9.0g`, `%8.0gc`, `%10.0g`); test on auto price and floats | 04-02 (~1,300 rows incl. float storage), S12 `TestDropdown`/`TestMarkerLabels` on `f` and `price` | covered |
| G16 | 1 read `valuelabel`; fill `major_label_overrides` from the label set | S14 TR-14.4/14.5/14.7/14.8, 14-08 | covered |
| G16 | 2 `hover()` derived text column | TR-14.9/14.10/14.14, 14-09 | covered |
| G16 | 3 compare with twoway's SVG for `xlabel(1/5, valuelabel)` | 14-02 (`g16_valuelabel` probes), 14-10 (AL-17..19) | covered |
| K2 | 1 measure the floor in 3.10 venvs | — | excluded (Q8) |
| K2 | 2 raise the minimums everywhere | S09 09-08, 09-11 (TR-09.5..09.8) | covered |
| K2 | 3 `from __future__ import annotations`; ast-scan pytest | 09-07, `TestTheGeneratedAppEvaluatesNoAnnotationAtImport` | covered |
| K2 | 4 launcher checks `returncode`; pytest with a non-zero app | 09-03, `test_a_non_zero_exit_names_the_status_and_carries_stderr` | covered |
| K2 | 5 Stata against a 3.10 venv; downgrade to bokeh 3.5 | replaced by sandbox fakes HON-29/HON-30 (09-09) | excluded (Q8) / amended |
| X1 | 1 keep exact text; numbers compared as numbers | S17 TR-17.2/17.5/17.6, 17-03, 17-04 | covered (Q10) |
| X1 | 2 remove the 'nan'/'None'/'NaT' exclusion; colorvar string path; `""` as missing string | TR-17.3, TR-17.8, 17-03 | covered (Q13) |
| X1 | 3 one rule for both masks, pinned by a node+pandas pytest | TR-17.6, `TestOneRule::test_node_and_pandas_agree` (S03 `mask_parity`) | covered |
| X1 | 4 cscript with `str fips`, '1', '1.0', 'None', 'nan', 5e-05 vs `count if` | 17-05 | covered |
| X2 | 1 `colordiscrete` + `colorcuts()` → cuts are levels, rest gray; drop cuts below min | S16 TR-16.3/16.4, 16-05 | covered |
| X2 | 2 `colorlevels(#)` and `colorvarminmax` | TR-16.1/16.2/16.4, 16-03, 16-05 | covered |
| X2 | 3 bin at z ticks with `colorrule(hue)` | — | excluded (Q5) |
| X2 | 4 declare `zlabel()`, `ztitle()`, `zscale()`; draw on the key | TR-16.5..16.7, 16-04, 16-06 | covered |
| X2 | 5 SVG fixture of marker fill groups on auto and nlsw88; pytest compares factor per observation and level count | 16-02, `test_every_probe_partitions_the_observations_as_twoway_does` | covered |

### Symptom bullets → tests

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
| D1 | d3colors draws #606060 with 0 warnings | `::test_d3colors_p1_to_p15_are_the_files_rgb_values`, `::test_both_modes_draw_d3colors_p1` |
| E1 | `fmt(%10.0g)` → `6e+03` | `test_kpi_format.py::TestFirstPaint::*` (fixture row) |
| E1 | `%9,2f`, `%21x`, `%16H` raw | `%9,2f`: fixture row; `%21x`/`%16H`: OV-121/122, `TestRefusedOnACard` |
| E1 | `%td` of 15000 → `15000.0`; date KPIs ignore `fmt()` | KF-01 (`%td` on `max(when)`), `TestEffectiveFormat::test_the_rule` |
| E1 | own `%g` dropped (6165.26 vs 6165.257) | `TestEffectiveFormat` (`%8.0gc`), KF-02 |
| E2 | served g1=3, g2=5, k1=3 where 5 implied | `test_filter_exclusion_sets.py::TestAnExclusionHoldsAgainstEveryMove::test_saved_state_…`, `::test_served_state_…` |
| E3 | `%td` dropdown `2001-12-31 00:00:00`; `%9.0fc` dropdown `3799` | `test_display_format_sites.py::TestDropdown::test_labels_are_statas_text_in_both_modes` |
| E3 | date sliders `%d %b %Y`, step span/100; period sliders stop mid-period; `0[.]00` | `TestSliders::*` |
| E3 | tooltips `{%F}`; `%tC` loses time | `TestTooltips::test_fields_carry_custom_and_a_formatter_with_the_format` (`%tc` case; add `%tC`, F-22) |
| E3 | KPI dates fixed picture | S11 `TestFirstPaint` date rows |
| E3 | `%tm` axis `Jan 2000` | `TestDateAxis::test_ticks_read_as_stata_in_both_modes` (dash text only; twoway's text untested, F-02) |
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

---

## 2. Decision compliance

| Decision | Implemented by | Contradiction found |
|---|---|---|
| Q1 focused discovery | n/a | none |
| Q2 sections by component | `index.md`, all sections | none |
| Q3 omit C4/E4; no estimator ports | S01 :370 (no marker), S05 :325-326, S10 :532-533, S17 :205, S18 :427-428, S19 :142 | none — no section ports an estimator to `_FILTER_JS`; S17 TR-17.10 changes only which mask the recount reads |
| Q4 (amended) BUGS.md entry lands closed in the fix commit; WP-28 lists all 22 up front | S01 TR-01.6, TR-01.8; every closing task | **partial**: the Resolution qualifier `(WP-28, <ID>)` that S01 :332/:341-342 and S19 :196-199/:376 require is stated only by S16 :375 (and there in the text, not as the field qualifier); S05 :645, S06 :489, S09 :820/:932, S10 :927, S11 :549, S12 :749, S13 :376, S14 :707/:757, S15 :322, S17 :392, S18 :727 give a different or no form (F-03) |
| Q4/Q23 amendment: `**GAPS2 closed:**`; `#### GAPS2 traceability`; GAPS2.md in `_ROOT_ALSO` | S01 TR-01.1..01.6, S19 TR-19.3/19.4 | none — no section writes `**Gaps closed:**` (grep clean) |
| Q5 X2 explicit forms; keep the continuous default | S16 Boundaries :162-163 | none |
| Q6 formats: write f/g/e (+c, comma), every `%t`; refuse `%x`/`%H` r(198) | S04 TR-04.1/04.7, 04-08 | none; S04 also refuses `%L` (`%16L`, `%8L`), a widening PRD §7 :67 and S19 :153 do not name (F-15) |
| Q7 (amended) reserve `__dash`, r(110); rename `__mlabel__*` and jitter; glyph-field residual; no temp frame | S07 TR-07.1..07.5, Boundaries :206-207 | none |
| Q8 declare the tested floor; no venv matrix | S09 TR-09.5..09.8, Boundaries :500-501 | none |
| Q9 count what the page embeds; JSON stays | S08 TR-08.6..08.10, Boundaries :171 | none |
| Q10 numbers as numbers in both modes; node+pandas parity test | S17 TR-17.5/17.6; S03 `mask_parity` | none |
| Q11 saved bs bar below the header; ALLOWED exemption removed | S10 TR-10.10/10.11(e) | none; S10 :544-545 keeps the ALLOWED *key* and removes the guard clause — consistent with RESEARCH §9 ("the key stays"), the exemption itself goes |
| Q12 held port refused, naming the port; `/health` 30 s; URL once it answers; range refused not clamped | S09 TR-09.1..09.4 | none |
| Q13 numeric missing unlisted; `""` blank row; colorvar string path same rule | S17 TR-17.3, TR-17.8 | none |
| Q14 (amended) SVG helper; B2 from SVG-fitted extents; `.Graph` probed once | S02, S18 TR-18 "Stata truth" | none |
| Q15 stateful node runner, no browser | S03 | none |
| Q16 G2 cscript over every type and position, generated | S08 TR-08.3 | none |
| Q17 branch `s3-bugs`; merge reported, never run | all sections; S19 Boundaries :288-289 | none |
| Q18 one commit per gap (test then fix); shared components in their own commits | S01 TR-01.9, S07, S08, S14, S18 | **violated** by `BRIEF.md:34` ("each task = one commit"), S09 :676, S10 :1001, and the test-only commits at S02 :368, S03 :251, S04 :642, S05 :509, S06 :423, S16 :292, S17 :314 (F-01) |
| Q19 parallel worktrees; `patch -p1`; own `STATATMP` | PLAN.md :160-165; every section's invocation | none |
| Q20 dash.sthlp + CHANGELOG per gap; "Results that change" with before/after | every closing task | **partial**: sections write to the top-level CHANGELOG headings while S01's stub (`### Fixed in WP-28` with `<!-- WP-28 ID -->` markers, S01 :287-323) expects the marker replaced; S19 19-01 :378 fails if a marker survives (F-04) |
| Q21 exit = WP-27 gate from an installed package | S19 TR-19.5..19.8 | none |
| Q22 silent when honoured | every section's Boundaries | none — every new note is for a refusal, an unwritable value or a conflict (`ytitle(axis(2))` + `ytitle2()`) |
| Q23 GAPS2 Tracked lines updated; audit text kept | S19 TR-19.3 | none |
| Amendment 3 (jitter renamed; glyph-field residual) | S07 TR-07.2, 07-07 | none |
| Amendment 4 (B2 SVG-fitted) | S18 :430-464 | none |
| CLAUDE.md rule 10 (Stata only via `arch -arm64 /usr/local/bin/stata-mp -b do`) | every Stata-running section | none — no GUI, no bare `stata-mp` |
| CLAUDE.md rule 11 (full suite once before a commit; never two at once) | most sections | **violated** in S08: full runs at 08-05 :295-297, 08-06 :305, 08-09 :335-337 and 08-10 :345 (four launches; the hook refuses the third) (F-05) |

---

## 3. Security findings (CLAUDE.md rule 1)

Checked every place a section puts text into HTML, a Bokeh field, a JS string, a tooltip, CSS, a subprocess argument, a file path, or `exec`/`eval`.

| Section | Surface | Verdict |
|---|---|---|
| S04 `_DASH_FMT_JS` | format string → `args`, never `code`; `toFixed`/`toPrecision` clamped 0..100; widths ≤ 2045; regex `\d{1,4}`, ASCII, ≤ 60 chars (TR-04.1, TR-04.4, TR-04.10) | escaped/bounded — but `dash_html_escape` has no unit test of its own (F-16) |
| S04 dash.ado `regexm("^%-?[0-9]*[xHL]$")` after `confirm numeric format` (TR-04.7) | value echoed by `_dash_say` by value | ok (no quantifier that `version` changes) |
| S05 histogram config | three Python numbers | ok |
| S06 scheme warnings (TR-06.4) | line text through `_safe_name` (printable, ≤ 80); **file name `os.path.basename(path)` raw** | F-13: pass the basename through `_safe_name` too |
| S07 name checks | `_dash_is_stata_name` (`isidentifier`, ≤ 32) at every site; Mata echo `[^\p{L}\p{N}_.\-]` → `?` | ok |
| S08 refusal messages | `_dash_display` (bounded); Mata readers `strpos`/`ustrregexm`, `bin` digits only | ok; the generator reads repo files only |
| S09 Popen (TR-09.2) | list argv, no shell; `sys.executable`; stderr deque(50), last 5 lines, printable-only, ≤ 2000 chars, through `_dash_say`; report dict via `init_globals` | ok — **stdout lines are printed raw and unbounded** (F-14) |
| S09 `_dash_port_value` | ASCII-digit check (no `isdigit`), range | ok |
| S10 stylesheet, classes, meta | integers and fixed words; `re.fullmatch` on the CSS; `test_nothing_of_the_user_reaches_the_classes_or_css` | ok |
| S11 card rebuild (TR-11.4) | `dash_html_escape(text)`; `k.title`/`k.subtitle`/`name_html` already `html.escape`d at `_kpi_callback_config` (dash_render.py:23417, :23440-23441); colours via `_resolve_kpi_color`; `k.fmt` JSON-encoded, never in `code` | ok |
| S12 `CustomJSHover`/`CustomJSTickFormatter` (TR-12.1) | `fmt`/`kind`/`storage` in `args`; code is the fixed writer; `test_fields_carry_custom_and_a_formatter_with_the_format` asserts `code` lacks the format | ok |
| S12 `_PLACEHOLDER` widening | `(?:[0-9.,%FT ]+\|custom)` + a test that every `{custom}` has a formatter carrying the format | ok (deliberate, amendment) |
| S13 Mata `_dash_route_axis2` | reads/writes by value through `st_local`; no regex; `macval()` at the parser as today | ok |
| S14 `_dash_axis_expand` (TR-14.12) | `capture numlist "\`run'"` — the run holds no `"` by construction, but the section does not say what happens to a run holding `` ` `` or `$` | F-17: leave such runs as written (or `macval`) and say so |
| S14 hover column | tooltip field value, never `{safe}`; overrides/`args` canvas text | ok |
| S15 legend | `LegendItem.label` value sink; parser linear, numbers ≤ 6 digits | ok |
| S16 z options | `ztitle` as a property value; `zlabel` via the `args`/overrides route; CV-06 hostile case | ok |
| S17 options | `Select.options` values are data; `filter_specs_json`/`graph_use_json` JSON; `__proto__` listed through `dash_own_col`; hostile-text test | ok |
| S18 | numbers only; `range(abc)` through `_dash_display` | ok |
| S02/S03 | `Macro.getLocal` for every needle and path; `[node(), path]` argv | ok |
| S01/S19 | `git cat-file -e` after `re.fullmatch(r"[0-9a-f]{7,40}")`; `subprocess.run` list | ok |

No `shell=True`, no user-controlled `format()`/`str.format`, no `exec`/`eval` of user text anywhere in the plan. (`test_kpi_format.cscript` KF-03 and CV-01 `exec` the *generated app source*, the existing `_load_app` recipe, not user data.)

---

## 4. Edge cases and boundaries

Per section, what is covered and what is missing (only omissions are listed as findings).

| Section | Empty / missing | Boundary values | Log/date axes, by(), link groups | Both renderers | Copy lists + `function_test_map.py` | `git add -f` | `python_exec` hazard |
|---|---|---|---|---|---|---|---|
| S01 | n/a | n/a | n/a | n/a | n/a | GAPS2.md plain `git add` (:258) | none run |
| S02 | `svg_axis_extent` None with reason; empty `<text>` kept | tiny SVG log fit; U+00A0 | n/a | n/a | not a renderer module (documented :121) | :286 (three files) | :274 |
| S03 | NaN/inf → None; NaT; `__proto__` | 5e-05, 1e21 | dates as ms | both twins | test helper (documented :120) | none | none run |
| S04 | NaN → `.`; `.a` excluded (G12); `""` → `%9.0g` | `%20.15g`, 1e21, 1e-7, 1e100, float32 0.1, `-0.0`, year 100, 31dec9999 | period kinds via `_dash_stata_value_of` | loaders + copy lists (TR-04.9) | TR-04.1/04.9 | :494 | :870-873 |
| S05 | **NaN in `arr` not stated** (F-20); N=0 not stated | bin 1..100, `width()`, fweights, `start()` at reldif 5e-6 | n/a | `TestBothModes` | static method + map entry | :367 | :703-708 |
| S06 | empty line, tab-only, unclosed quote, compound quote, `#include` with no name, 500 non-printables | 12 bad lines vs the 10+1 bound | n/a | `_SCHEME_PROPS` | TR-06.7 | plain add (:149) | :570-572 |
| S07 | `""`, `None`, 33 chars, markup, `$`, backtick | n/a | by() Unicode name | yes | TR-07.2/07.8 | none | :219-221 |
| S08 | `nobs == 0` → 1 bin | 6M rows as a number; `width()`/`discrete`/lowess → N | by() → `by_groups` limit; link group touched rule | yes | none copied (documented :370); maps | none | :372 |
| S09 | `""`, `٥٠٠٦`, `5_006`, `5006x` | 1023/1024/65535/70000 | n/a | n/a | TR-09.12 | none | :1004-1008 |
| S10 | no filters → no bar; no subtitle; no tabs | spans 0 and 99 clamped | bs_facet (by()) in Chrome; link groups | yes | TR-10.2/10.8 | none | none run |
| S11 | missing → `.`; date past range → `.`; zero rows after a move | ties 20.5/1234567.5 (S04) | date KPIs; count of a date variable | yes | map updated (TR-11.8) | none | :602 |
| S12 | NaT dropped (S17); missing period → NaN; **all-missing / single-value period column not routed through `_dash_finite_column`** (F-21) | `%tdCCYY-NN-DD`, `%9.999999999f` bounded | date axes, by() titles | yes | TR-12.10 | none | :822-823 |
| S13 | `xtitle("")`, `xtitle("", size(large))`, `ytitle2("")`, lone-axis empty | `axis(3)` named | second axis both orders | yes | :387 | :227 | :398 |
| S14 | `xlabel()` default; string before any value named | `_MAX_AXIS_TICKS` in every form; numlist 1,600 cap left to the renderer (:799-802); negative/fractional steps; `1(0)5` measured | date axis `14977/14980`; `ylabel2`; **by() panels not covered for `valuelabel`** (F-23) | yes | TR-14.15 | :502-503 | :813-817 |
| S15 | `- ""` inserts nothing; `order(1 2 1)`; **`label(0 …)`/`order(0)` unstated** (F-24) | 100,000 tokens < 1 s; six-digit keys | CI layers; `legend(off)` under by() noted | yes | TR-15.5 | :194 | :347 |
| S16 | no finite values → `[]`; NaN → missing; `zscale(log)` with low ≤ 0 warns | `colorlevels(1)` refused by the rule; all cuts below min | by() warns once via `seen` | yes | TR-16.3/16.6 | :216 | :403 |
| S17 | `""` listed; NaN/NaT unlisted; `None`; sentinel | 5e-05, 1e21, float32 0.1 | by() panel, link group, aggregate, derived | yes | TR-17.13 | :233 | :419 |
| S18 | `range()` → `[]`; `.` ignored; degenerate hull ±1 unit | 1,600+ values bounded by `_dash_expand_numlist` | log (log10 pad), `%td` (ms), by() common hull, second axes, bars' half-width | yes; `_dash_limit_ranges_to_primary` shared | TR-18.13 | :498 | :783-787 |
| S19 | n/a | n/a | n/a | suites run both | n/a | none | :555-558 |

### Flip lists vs RESEARCH.md per-topic lists

| RESEARCH.md list | Section that flips it | Omission |
|---|---|---|
| §1 formats (:76) — `test_dates.py::TestNumericDisplayFormats`, `test_date_range.py ~944-958`, `@{date}{%F}` pins (`test_date_range.py:609`, `test_served_dates.py:129/229`, `test_help_claims_4.py:1706`), `test_saved_filter_layers.py` (`"2001-12-31 00:00:00"`, `_dash_option_value(1.0)=="1"`), `test_server_layer_defects.py:1080-1101`, `test_adversarial_matrix.py:1664-1695` | S04 (keeps 56 green, flips `TestTheWriter` key set), S12 12-08/12-10, S17 17-03, S11 11-04 | none |
| §2 axes (:82-86) — `test_graph_options.py::test_single_quoted_label`, `test_axis_options.py::TestAxisScale`, `test_suboption_warnings.py` valuelabel | S14 14-03, S18 18-08, S14 14-08 | none |
| §3 textbox (:90-94) — JSE-46 `jg46k` | S13 13-01 | none |
| §5 histogram (:102) — `test_histogram_spurious_bin.py` (revise) | S05 TR-05.9 | none |
| §7 colorvar (:110) — HC7-02 | S16 16-07 | none |
| §8 filters (:114-118) — `TestExcludeHoldsWhileItsOwnFilterMoves`; S03's pins | S17 17-07 | none |
| §9 presentation (:122) — `test_help_claims_4.py:1643`, dimming test, `test_mode_parity.py` ALLOWED | S10 10-03/10-04/10-01 | none |
| §10 serve/floor (:126-128) — clamp tests, `_FakeProc`, `test_setup_python_gate.cscript`, `test_setup_honesty.cscript`, PC-19..21, `test_help_claims_8.cscript:786`, `test_help_claims_8.py:1647` | S09 09-03/09-04/09-09/09-10 | none |
| §11 data (:132-138) — `__dashq` refusal tests, hygiene counts | S07 (16 files listed :153-169), S08 | none |
| §12 tracking (:142-148) | S01 (no flips) | none |

No RESEARCH.md flip is omitted by its section.

---

## 5. Findings

### F-01 — critical — commit model contradicts Q18, PRD §9, CLAUDE.md rule 4 and S19's inventory

**Where.** `sections/BRIEF.md:34` ("each task = one commit"); `section-09:676` ("Each task is one commit on `s3-bugs`"); `section-10:1001` ("One commit per task on `s3-bugs`"); test-only commits ordered at `section-02:368`, `section-03:251`, `section-04:642`, `section-05:509`, `section-06:423`, `section-16:292`, `section-17:314`; red intermediate commits at `section-09:891-896` (09-10) and `section-09:1001-1003`.

**Why.** DISCOVERY Q18 and PRD §9 :83 say one commit per gap with the entry landing closed in it; S01 TR-01.9 (:343-354) says "a red tree is never committed (rule 4): the regression tests are written and run first, their failure text saved to the scratch directory, and they land in the fix commit"; S19 TR-19.1 (:196-199) and 19-01 (:376-378) fail if an id has more than one commit with `(GAPS2 <ID>)` in its subject. Every task-01 that commits failing tests commits a red tree; S09/S10's per-task commits give F1, K2 and E14 four to eight commits each. S07, S08, S14 and S18 already follow the S01 model.

**Edit.** Replace `BRIEF.md:34` with:

> `## Tasks               XML tasks per xml-task-format.md; task 1 writes the failing tests and runs them, saving the failure text to the scratch directory — it does NOT commit (a red tree is never committed, CLAUDE.md rule 4); 1-3 files per task; ordered; one commit per gap (S01 TR-01.9): the gap's failing tests, its fix, its flipped tests and its closed BUGS.md entry land in that one commit, whose subject ends "(GAPS2 <ID>)"; a shared-component section (02, 03, 04) commits once per component with a subject ending "(WP-28 Snn)"; the final task of a gap group is the one that commits`

and in each affected section replace the task-01 sentence "Commit on `s3-bugs`" / "paste the failure summary into the commit message" with: "Do not commit; save the failure summary to `<scratch>/<NN>-01-failure.txt` for the gap's fix commit (S01 TR-01.9)." In S09 :676-678 replace "Each task is one commit … squashing … if the maintainer prefers" with "The F1 group (09-03..09-06) is one commit `… (GAPS2 F1)` and the K2 group (09-07..09-12) one commit `… (GAPS2 K2)`; 09-10 and 09-11 are the same commit so no intermediate tree is red." In S10 :1001 replace "One commit per task" with "One commit for E14 (10-03..10-08) with subject `… (GAPS2 E14)`". S13 must add: "B3 = 13-03..13-06 + its entry, one commit; B6 = 13-07 + its entry; B7 = 13-09 + JSE-46 + its entry" (its `git log -3` verify at :378 implies this but the tasks never say it).

### F-02 — major — E3 plan step 4's twoway `%tm` axis-label truth has no owner

**Where.** `section-12:436-438` ("hand it to section 14's extract script (one `%tm` probe)") and `:798-802` ("hand it over in the commit message of 12-05"); `section-14:458-497` (probe tables) contain no `%tm` probe; GAPS2 E3 plan step 4 (:1145) names it.

**Edit.** Add to S14 (after 14-02's tables, group `b1_label`) the probe row `| e3_tm_axis | sp500-like: \`gen m = mofd(date)\`, \`format m %tm\`, \`twoway scatter close m\` | — | the x tick texts (\`2000m1\` … ) |` — a `%tm` variable built in the export loop as `auto_vl` is — and the task:

```xml
<task type="auto" id="14-02b">
  <name>Record twoway's %tm axis-tick text for E3</name>
  <files>scripts/extract_axis_truth.do, test/fixtures/axis_truth.json</files>
  <action>
    In the export loop add a dataset branch `sp500_tm`: `sysuse sp500, clear`, `generate m = mofd(date)`, `format m %tm`. Register `zp "e3_tm_axis" "b1_label" "sp500_tm" "twoway scatter close m" "" ""` and `zp "e3_tm_axis_lab" "b1_label" "sp500_tm" "twoway scatter close m" "xlabel(480(3)491)" "480 483 486 489"`. The python block records `texts` for both as for every `b1_label` probe. Re-run the script once with Section 18's probes if both are ready (one regeneration), `git add -f test/fixtures/axis_truth.json`.
  </action>
  <verify>`python3 -c "import json;p=json.load(open('test/fixtures/axis_truth.json'))['probes'];print(p['e3_tm_axis_lab']['texts'])"` lists `2000m1`-style texts.</verify>
  <done>twoway's %tm tick text is a committed fixture Section 12's date-axis test can read.</done>
</task>
```

and in S12's `TestDateAxis::test_ticks_read_as_stata_in_both_modes` (:483-486) add: "the formatter's node output at the fixture's tick values equals `axis_truth.json` `e3_tm_axis_lab.texts` (fail, not skip, when the probe is absent)."

### F-03 — major — the BUGS.md Resolution qualifier `(WP-28, <ID>)` is not propagated to the closing tasks

**Where.** Required by `section-01:332` (`- Resolution (WP-28, <ID>): Fixed <ddmonyyyy>. …`), `:341-342`, `section-19:196-199`, `:359-360` (`grep -c '^  - Resolution (WP-28, '` = 22), `:376`. Stated by no closing task except S16 :375 (in the text, not as the field qualifier): S05 :645 (`Resolution "Fixed. Certified by …"`), S06 :489, S07 :357/:393, S08 :305/:345, S09 :820/:932 (`Fixed 25sep2026 (WP-28).`), S10 :927, S11 :549, S12 :749, S13 :376, S14 :707/:757, S15 :322, S17 :392, S18 :727.

**Why.** PLAN.md :162 hands each agent its section file, BRIEF, DISCOVERY and RESEARCH — not S01. `TestGaps2AndRoadmapAgree::test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit` and S19 19-01 both read the qualifier; every entry written as the sections describe would fail them at DONE.

**Edit.** Add to `BRIEF.md` "Rules of content" one line: "**BUGS.md entry and commit forms are S01 TR-01.8 and TR-01.9, verbatim**: the Resolution field is written `  - Resolution (WP-28, <ID>): Fixed <ddmonyyyy>. …`, the title holds no `"`, the commit subject ends `(GAPS2 <ID>)`." And in each closing task listed above replace the Resolution phrase with `- Resolution (WP-28, <ID>): Fixed <ddmonyyyy>. <what changed>. Pinned by <tests>.`

### F-04 — major — CHANGELOG placement: sections write to the top-level headings while S01/S19 expect the `### Fixed in WP-28` markers replaced

**Where.** S01 TR-01.7 (:287-323) creates `### Fixed in WP-28` with 23 `<!-- WP-28 <ID> -->` markers and says "A section replaces its gap's marker with its line(s)"; S19 19-01 (:378) fails if any marker survives, 19-02 (:403) reads the gap lines from inside that block. Sections instead write to the release's top-level sections: S05 :651-653 (`### Results that change` / `**Statistical layers…**` :16), S06 :494-496 (:113), S07 TR-07.9 :199 and 07-10 :392 (`### Changed behaviour`, `### Fixed`), S08 TR-08.12 :166, S09 TR-09.8 :475-477 and 09-06 :806-813 ("create it immediately before `### Fixed after WP-27` … if no other section has yet" — S01 already did), S10 :914-921, S11 :556-560, S12 :762-766, S13 :376, S14 :707 and :757 (G16 under `### Fixed` (or `### New`) where S01 :300 and S19 AC-19.1 :344-346 put G16 under "Results that change"), S15 :322, S16 :374, S17 :391, S18 :727.

**Edit.** Add to `BRIEF.md` "Rules of content": "**CHANGELOG**: a gap's line(s) replace the marker `<!-- WP-28 <ID> -->` under `### Fixed in WP-28` (S01 TR-01.7), in the list the marker sits in; nothing is written to the release's top-level `### Results that change` / `### Fixed` / … sections by a gap section (S19 consolidates); E14 replaces both of its markers." Correct S09 :806-808 to "replace the `<!-- WP-28 F1 -->` marker (S01 created the heading)"; S14 :757 to "replace the `<!-- WP-28 G16 -->` marker under `Results that change:`". Alternatively drop the marker scheme from S01 TR-01.7 and S19 TR-19.1/19.2 — but then S19's "each gap once" check needs another anchor; the marker scheme is the simpler fix.

### F-05 — major — S08 launches the full suite four times for two commits

**Where.** `section-08:295-297` (08-05 "Run the full suite once"), `:305` (08-06), `:335-337` (08-09), `:345` (08-10). CLAUDE.md rule 11 and `.claude/hooks/guard-full-suite.sh` (two free launches per session) — the third launch is refused unless `FULL_SUITE_RERUN=1`, which the section never mentions.

**Edit.** In 08-05 replace "Run the full suite once; any test that fed a string plot column … is flipped" with "Run `python3 -m pytest test/test_string_plot_variables.py test/test_mode_parity.py test/test_help_claims_4.py -q`; the full suite runs once in 08-06 before the G2 commit"; in 08-09 replace "then the full suite once" with "then `python3 -m pytest test/test_resource_limits.py test/test_dataset_size_warning.py test/test_adversarial_matrix.py -q`; the full suite runs once in 08-10 before the G3 commit".

### F-06 — major — S13's B6 BUGS.md title holds `"` and cannot be quoted in a GAPS2 Tracked line

**Where.** `section-13:376`: `B6 "xtitle("") and ytitle("") do not remove the axis title"`. S01 TR-01.8 (:337) forbids `"` in a title; `_GAPS2_CLOSED`'s `"([^"]+)"` cannot hold it; S19 19-01 (:377) fails the inventory.

**Edit.** Title: `xtitle() and ytitle() given empty text do not remove the axis title`.

### F-07 — major — S05 inserts its BUGS.md entry mid-file against S01's append rule and the merge rule

**Where.** `section-05:636-639` ("add, after the entry at :1215, a closed entry"); S01 TR-01.8 (:335) "appended at the end of BUGS.md"; S01 Notes (:528-531) "BUGS.md entries in section order at the end of the file".

**Edit.** "Append the closed entry at the end of BUGS.md (S01 TR-01.8); its Description names the :1215 entry it closes the residual of."

### F-08 — minor — S09's per-task commits would leave 09-10's flipped pytest red for one commit

**Where.** `section-09:891-896`, `:1001-1003` ("Squash the pair if a red intermediate commit is unwanted"). Rule 4: never wanted. Folded into F-01's edit (09-10 and 09-11 one commit).

### F-09 — minor — S04 does not unit-test `dash_html_escape`

**Where.** `section-04:381-391` defines it in `_DASH_FMT_JS` "for section 11's card rebuild"; the `TestJavaScriptTwin` stubs (:531-549) never call it; CLAUDE.md rule 3 wants a unit test per function, and S11's `TestEscaping` only proves the card path.

**Edit.** Add stub: "Test: `TestJavaScriptTwin::test_dash_html_escape_escapes_the_five_characters` — node: `dash_html_escape('<a href=\"x\">&\\'</a>')` equals `html.escape('<a href="x">&\'</a>', quote=True)`; a string without them is unchanged; `null`/`undefined` → `''`."

### F-10 — minor — S06 echoes the scheme file's basename unbounded

**Where.** `section-06:217-222` TR-06.4: `'{os.path.basename(path)}'` in the warning; only `line` goes through `_safe_name`. The path comes from the user's `scheme()` option via `_resolve_path`.

**Edit.** `f"dash scheme: line {lineno} of '{self._safe_name(os.path.basename(path))}' …"`.

### F-11 — minor — D1 plan step 2's D7 forms are a residual recorded only in the D1 entry

**Where.** `section-06:250-252` (CMYK, hsv, `colour*#` out of scope), :493-494 (entry text); PRD §7 (:61-70) and S19 TR-19.3 (:233-239, residual reasons for G1, G3, X2, E14 only) do not list it; no DISCOVERY decision covers it.

**Edit.** S19 TR-19.3: add "D1: `; residual deferred (WP-28): CMYK, hsv and colour*# scheme values are D7's (GAPS2 D7), not read here`"; PRD §7: add the same sentence.

### F-12 — minor — G3 plan step 4 is exercised only as arithmetic

**Where.** `section-08:207` (the count over 6,000,000 "as a number"), `:373` ("No test allocates six million rows … must not be committed"); GAPS2 G3 step 4 asks for a 6M-obs histogram that builds with bins equal to `twoway__histogram_gen`'s and a page under 2 MB.

**Edit.** Add to 08-10's action: "Run once, from a scratch directory and not committed, `set obs 6000000; gen x = rnormal(); dash histogram x, bin(50) saving(h6.html)` and `dash scatter x x, saving(s6.html)`; record rc 0 / r(134) and `h6.html`'s size in the G3 commit body and the BUGS.md Resolution (`measured, not a committed test`)."

### F-13 — minor — S05 TR-05.1 does not state the NaN precondition of `_histogram_counts`

**Where.** `section-05:256-261`. `np.floor(nan)` clipped and cast to `int64` is undefined and `np.bincount` raises; the continuous path today ignores NaN through `np.histogram`. `_layer_weights` is the only line between the source and the count (dash_render.py:9551).

**Edit.** TR-05.1: "`arr` and `w` are finite (the caller has dropped missing rows through `_layer_weights`); the function asserts `np.isfinite(arr).all()` in a comment-level precondition and `TestHistogramCounts` gains a case that a NaN-free input is required (or that NaN rows are dropped before counting, whichever `_layer_weights` guarantees — read it first and say which)."

### F-14 — minor — S09 prints the child's stdout lines raw and unbounded into the Results window

**Where.** `section-09:407-411` TR-09.2 step 5 (`print` each stdout line); the stderr tail is bounded and control-stripped (:422-427) but stdout is not; the app's stdout can echo spec text (a title in a warning).

**Edit.** Step 5: "each stdout line is printed after the same filter as step 8 (`c.isprintable() or c == "\n"`), cut to 500 characters, and at most 200 lines are forwarded before ready; later lines are dropped with one `dash: (further app output not shown)`."

### F-15 — minor — `%L` refusal is wider than Q6/PRD §7 state

**Where.** `section-04:333-334`, :472-473 (`%16L`, `%8L` refused); PRD §7 :67 and S19 :153 say "`%x` and `%H`".

**Edit.** PRD §7 and S19 :153: "`%x`, `%H` and `%L` (the IEEE byte dumps) are refused"; S04's help text (04-09) already says so.

### F-16 — minor — S13 B3 symptom "after a full name, a later abbreviation is only named" has no direct case

**Where.** `section-13:233-235` (`test_spelling` runs each spelling alone; `test_parse_canonicalises` uses abbreviation-first).

**Edit.** Add to `TestAbbreviationsAreSubOptions`: "`title("T", size(large) c(red))` and `title("T", color(red) si(large))` are red and large in both modes, nothing named."

### F-17 — minor — S14's `numlist "\`run'"` is safe only if a run cannot carry `` ` `` or `$`

**Where.** `section-14:388-397` TR-14.12, :412-415 TR-14.16 ("`run` cannot hold a quote").

**Edit.** TR-14.12: "A run holding `` ` ``, `$` or `'` is left as written without calling `numlist` (the renderer names it); every other run is passed as `` numlist `"`macval(run)'"' ``." Add AL-02 case: `xlabel(2000 $x 4000)` registers with the run untouched.

### F-18 — minor — S13 B7 compound-quoted second-axis title is not a stub

**Where.** `section-13:246` lists quoted, two-line, `size(large)`, `c(red)`, unknown sub-option; GAPS2 B7 plan step 3 names "compound-quoted".

**Edit.** Add to `test_text_lines_size_colour`: `` ytitle2(`"c "q" d"') `` draws `c "q" d`.

### F-19 — minor — S12 tooltip stub tests `%tc`, the symptom names `%tC`

**Where.** `section-12:471-476`; GAPS2 E3 (:1132) "so `%tC` loses its time"; S04 writes `%tC` on `%tc`'s epoch (:359-360).

**Edit.** Add a `%tC` variable (`whenC`) to the frame and assert its tooltip keeps the time in both modes.

### F-20 — minor — S12 period sliders bypass the empty/degenerate handling of `_dash_filter_widget`

**Where.** `section-12:337-348` TR-12.3 ("`start`/`end` the min/max of `_dash_stata_value_of` over the column"); the existing branch (dash_render.py:17627-17638) returns a disabled widget for an empty column and widens `vmin == vmax`.

**Edit.** TR-12.3: "the period branch derives `vmin`/`vmax` from the existing `arr` (`_dash_finite_column`) converted through `_dash_period_values`, so an all-missing column still yields the disabled widget and a single value the `+1` widening; add `test_a_period_column_with_one_value_or_none` to `TestSliders`."

### F-21 — minor — S14 does not cover `valuelabel` on by() panels

**Where.** `section-14:358-363` TR-14.7 (per-figure call sites); no by() stub in `TestValueLabelsOnAxes`.

**Edit.** Add `TestValueLabelsOnAxes::test_by_panels_each_carry_the_overrides` — `by(foreign)` with `xlabel(1/5, valuelabel)`: every panel's x axis has the five overrides in both modes.

### F-22 — minor — S15 does not say what `label(0 …)`, `order(0)` or a key beyond the count do

**Where.** `section-15:136-138` TR-15.1/15.3 (keys are 1..999999; `order()` "a number that is no key draws nothing").

**Edit.** TR-15.3: "`label(#)`/`lastlabel(#)` for a `#` that is no key is ignored silently (twoway ignores it); `TestTheParser::test_cases` gains `'0 "z"'` → `[(0, ["z"])]` and `TestLabelByNumber` gains `label(9 "x")` → no change, no note."

### F-23 — minor — G6 tooltip symptom value (12345.67) not in the stub

**Where.** `section-12:471-476` (4099 only); GAPS2 G6 :1437.

**Edit.** Add 12345.67 under `%10.0g` → `12345.67` to `TestTooltips`.

### F-24 — minor — S04 fixture lacks width-1 and width-2 formats

**Where.** `section-04:459-461` format list (narrowest is `%8.0g`); the derived rule's `w-2` significant digits and `w-6` mantissa go negative below `%7.0g`.

**Edit.** Add `%1.0f %2.0f %3.0g %4.0g %5.0g %6.0g %7.0g` to the numeric format list so the writer's floor is measured, not inferred.

---

## 6. Counts

| Severity | Count | Ids |
|---|---|---|
| critical | 1 | F-01 |
| major | 6 | F-02, F-03, F-04, F-05, F-06, F-07 |
| minor | 17 | F-08 … F-24 |

MISSING plan step: E3 step 4 (twoway `%tm` axis-label truth) — F-02. Decision violations: Q18/rule 4 (F-01), Q4-amended's entry form not propagated (F-03), Q20's CHANGELOG placement vs S01's stub (F-04), rule 11 in S08 (F-05). Security: no unescaped sink, no `shell=True`, no user text in `exec`/`eval`; three hardening gaps (F-09 escape helper untested, F-10 scheme basename unbounded, F-14 launcher stdout unbounded) and one safety statement to add (F-17).
