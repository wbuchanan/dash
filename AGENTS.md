1. **Security is paramount.** Any feature, function, data object, input, output, or other application surface that could be vulnerable to exploitation should be hardened as much as possible at the initial stages of development and should be verified throughout the application development process.
2. **Honesty.** You will only ever provide true, correct, and honest responses. When asked to do something you will do it completely and will not report that a task is complete until the entire task is finished.
3. **Prevent abuse and exploitation.** Any API calls made from the application should be reasonably rate limited to prevent abuse and cost overruns.
4. **Testing.** Every function for every feature must have a unit test.  The application should have comprehensive end to end tests to verify that users can navigate in the application freely without error and be able to use all the features without error.
5. **Before Committing Code.** Pull from the local main branch, then run the full test suite including the newly developed code. If there are errors or failing tests, fix the issue in the code base and rerun the test suite.  Do this until all tests pass.
6. **Committing.** Always commit to your local branch and provide the command to merge those changes into the local main branch.  Never commit directly to the main branch unless explicitly requested for that time only.
7. **Commit Messages.** Never include any information about Codex or anthropic in commit messages.  Just provide information about the changes being made to the code base.
8. **Bugs**. Everytime you get a report about some feature or functionality not working correctly, you must develop an additional test to prevent the same bug from being reintroduced into the codebase in the future after diagnosing the issue and before developing code to fix the issue.  
9. **Payments.** Any payment webhooks must verify and validate signatures.
10. **Authentication.** Never store authentication tokens in localStorage.  Authentication tokens should be encrypted in transit and at rest whenever possible.  
11. **Data management.** Although developing the application starts with no users, the database architecture should be designed to support a significant number of users per month so the same architecture can grow and scale seamlessly with user growth.  This means adding appropriate indices on tables and modeling the data in the database to provide efficient read and write operations based on the application needs.
12. **API keys.** Avoid storing API keys client side unless it is absolutely necessary to do so.  
13. **Scrub the codebase.** Periodically check the code base for potential security vulnerabilities and recommend solutions to harden any vulnerabilities. Ensure that no private keys are ever committed into the code base. Avoid storing keys directly in the codebase.
14. **Logging.** The application should have robust logging that will make it easier to debug issues that users may encounter in the future without creating a performance penalty on the application. 
15. **Environmental variables.** Verify environmental variables on application start up.  
16. **Data inputs.** Harden all data inputs to prevent injection attacks and other types of vulnerabilities (e.g., string encoding to bypass standard injection attack vectors). Ensure all data input is UTF-8 before allowing it to pass from the front end to any back end component of the application.
17. **Health checks.** If this is a web application, ensure there is a health check end point to verify the status of the application and ensure a minimum of 95% up time.
18. **Adversarial tests.** Periodically, generate 3 adversarial test cases targeting auth bypass, injection, and resource exhaustion for each API end point and/or user input. If any of the test cases are able to gain any form of unauthorized access, take immediate steps to address the security vulnerabilities.
19. **Elevation.** For the limited users that have administrative privledges to web-based applications, it is critical to verify the users identity.  Only the select users with adminstrative privledges should ever be provided with access to administrative components of the application.
20. **Agents.** Use the largest number of agents the system will support when working on multiple tasks to parallelize the work load and complete it efficiently.
21. **Plans.** When developing plans for features or applications provide a combination of high level information and extremely detailed information.  Develop user stories, business requirements, and technical requirements for each feature, functionality, component, or other organizational unit for the code base. Additionally, develop a test plan in a similar manner. The goal is to ensure that any human or agent developer can quickly and easily build and ship the code correctly the first time based on the detailed information contained in the plan.

## Invariants introduced by WP-28

**The `__dash` column prefix.** Every column the renderer or the ado creates is named under `__dash`, and a user variable whose name begins `__dash` is refused with r(110) in both modes. Guarded by `test/test_reserved_names.py::TestTheDashPrefix`.

**The served copy lists.** The served app's constants and functions tuples in `dash_render.py` must name every module-level name the served template reads, and every new function is entered in `test/function_test_map.py`. Guarded by `test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName` and `test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`.

**The Python/JavaScript twins.** The display-format writer (`_dash_fmt` and its JavaScript twin), the filter mask and the histogram recount each have a Python and a JavaScript implementation pinned against each other under node (read from `DASH_NODE` or `PATH`; the tests skip without node except under `DASH_STRICT`). Guarded by `test/test_display_format_writer.py::TestJavaScriptTwin`, `test/test_js_runner.py::TestMaskParity`, `test/test_dropdown_values.py` (`test_node_and_pandas_agree`) and `test/test_histogram_edge_rule.py::TestTheJavaScriptRecountAgrees`.

**One way to run Stata from agent work.** `scripts/stata_slot.sh <scratch-dir> <file>.do` runs the console binary in batch in one of three `mkdir` slots with `STATATMP` under the scratch directory. A cscript is never passed to it directly: a two-line driver does `cd "<repo>/test"` then `do "<repo>/test/<script>.cscript"` (with `adopath ++ "<repo>/"` first), and `GAPS2_ONLY=S<NN>` limits `test/test_gaps2_truth.cscript` to one block. Guarded by `test/test_cscript_hygiene.py`.

**The CHANGELOG marker convention.** A package's tracking section places `<!-- WP-nn <ID> -->` markers in the release's existing lists where each gap's line belongs, and each fix replaces its own marker with a line ending `(WP-nn, <ID>)`; the closeout greps zero markers. No test reads CHANGELOG.md beyond the retired-link scan of `test/test_tracking_documents.py::TestTodoAndPlanAreRetired`.

**The BUGS.md Resolution form.** A closed gap's entry reads `- Resolution: Fixed <ddmonyyyy> (WP-nn, <ID>). ... Pinned by test/... .`, the id inside the text and the field name unchanged. Guarded by `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree::test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit`.

**The fixture `_meta` stamp.** Every Stata-measured fixture's `_meta` holds `stata_version`, `born_date`, `dash_commit` and `extracted`, asserted by the test of the section that wrote it (for example `test/test_statistical_truth.py::TestHistogramEdgeAgainstStata::test_the_meta_stamp_holds_the_four_provenance_keys`, `test/test_axis_extents.py::TestAgainstTwoway::test_the_fixture_meta_carries_the_four_provenance_keys`, `test/test_legend_order.py::TestTheFixture::test_meta_carries_the_four_provenance_keys` and `test/test_colorvar_truth.py::TestAgainstTwoway::test_the_fixture_meta_carries_the_four_provenance_keys`), and every fixture is tracked and named by a test (`test/test_fixtures_are_committed.py`).

## Invariants introduced by WP-29

**The join order.** `GlyphMapper._join_order` in `dash_render.py` is the only place a joining layer's rows are ordered: data order by default, `sort`/`sort(varlist)` by a rank, time-series types in time order. The rank columns `__dashs<k>` are made in Stata and taken out before any source exists. Guarded by `test/test_join_order.py::TestTheJoinOrderRule`, `test/test_join_order.py::TestTheSortColumnsNeverReachTheUser`, and `test/test_wp29_truth.cscript` JO-01.

**Variable labels.** Every text that names a variable goes through `_dash_var_label`, both loaders clean labels with `_dash_clean_var_labels`, and the test helper `make_data_json` in `test/conftest.py` writes `""` for an unlabelled variable, as jsonio does. Guarded by `test/test_unlabelled_variables.py::TestTheVarLabelRule`, `test/test_unlabelled_variables.py::TestCleanVarLabels`, and `test/test_conftest_helpers.py::TestTheHelperIsJsonioFaithful`.

**Function points come from Stata.** A function layer's points are Stata's (`$dash_fpts_<name>`, spec key `function_points`), and a renderer never evaluates an expression that has points. Guarded by `test/test_function_expr.py::TestStoredPoints::test_an_unevaluable_expression_beside_points_is_never_parsed`.

**Stata units for dates.** A computed layer and a KPI statistic of a date are computed in the variable's Stata units: inputs through `GlyphMapper._masked(units=)`/`_layer_units` and `_dash_kpi_column`, outputs through `_on_axis`/`_dash_units_to_axis`, which follows the figure's marked axis kinds (the served redraw's throwaway figure included). A computed position outside Stata's dates is dropped with one note, no non-finite number reaches page JSON, and dash keeps its date axis where twoway's first-plot rule labels numbers. Guarded by `test/test_date_units.py::TestEveryComputedLayer`, `test/test_date_units.py::TestKpiOfADate`, and `test/test_date_units.py::TestOutOfRange`.

**The hover export.** `hover()` variables are exported on both routes and counted on the saved page only where a layer can show them (or `csv` reads them). Mata's `_dash_spec_types_in(..., _pt_univar _pt_onefit _pt_literal)` and Python's `_DASH_COMPUTED_ONLY_TYPES | _DASH_LITERAL_TYPES` are the one rule. Guarded by `test/test_embedded_cells.py::TestTheTwoLanguagesAgree::test_the_types_hover_cannot_reach_agree`.

**A view's own rows.** A registered view's ids are exactly the source's row ids its filter keeps. Guarded by `test/test_per_plot_qualifier_linking.py::TestTheRegisteredRowsAreTheViewsOwn`.

**The colour key.** A colour key is drawn from the layer's colour rows and fixed at build; derived colour columns are named `__dash_cvar<k>_<var>`, and a missing colour value is None. Guarded by `test/test_colorvar_truth.py::TestTheKeyIsDrawnFromTheLayersRows` and `test/test_colorvar_forms.py::TestTheColourFieldName`.

**Private files and the verified launch.** Copies live under a private 0700 root (`c(tmpdir)dash-<uid>/run-<pid>-<random>/`) and are written by the 0600 writer; a location that is not private proceeds with one note and is never refused, while the anti-hijack guards (a hard-linked file, another account's file) refuse with r(7102). dash starts its served app only from the bytes it read through a descriptor it opened and verified, never by path. Guarded by `test/test_private_files.py::TestTheDataFileIsPrivate`, `test/test_private_files.py::TestThePrivateRoot`, and `test/test_private_files.py::TestTheLaunchFromTheOpenFile::test_a_path_swapped_after_verification_does_not_change_what_runs`.

**The parent watch.** A served app dies with the Stata session that launched it. Guarded by `test/test_serve_lifecycle.py::TestTheServerDiesWithItsLauncher`.

**Break ends dash serve.** Break ends `dash serve` with r(1), stopping the child, freeing the port and leaving no run folder. Guarded by `test/test_serve_lifecycle.py::TestTheLauncherPollsStata::test_break_closes_stdin_stops_the_child_and_raises_interrupted` and `test/test_serve_launch.cscript` LC-03.

**Setup's children.** `dash_setup` starts every child process through `dash_setup_lib.run_child` (a private working directory, `-P`, a scrubbed environment, UTF-8). Guarded by `test/test_setup_pep668.py::TestRunChild` and `test/test_program_coverage.cscript` PEP-07.

**by() sharing.** Whether by() panels share a scale is decided by `_dash_share_by_scales` after every panel is built and before `_dash_common_count_ticks`. Guarded by `test/test_by_scales.py::TestTheHelpers::test_share_by_scales_units` and `test/test_by_scales.py::TestPanelsShareOneScale`.

**Build-time served notes.** A note the served app must print is decided at build time, in `ServerAppBuilder._plan_graph_notes` and `ServerAppBuilder._plan_by_groups`, never in a session callback. Guarded by `test/test_axis2_suboptions.py::TestUnusedSecondAxisOptionsAreNamed::test_served_note_is_raised_at_build_time` and `test/test_resource_limits.py::TestTheHelpersOneByOne::test_the_by_plan_warns_over_the_limit_only`.

**The lpoly port and the lpvar key.** lpoly and lpolyci bandwidths come from `_lpoly_rot_detail` (NaN is Stata's missing and draws a zero line), local fits keep `_lpoly_kept_columns`, and the band is `_lpoly_se` with a pinch on rows without degrees of freedom. lpolyci's option key is `lpvar`, never `var`, which `_dash_extract_vars` would read as a variable. Guarded by `test/test_lpolyci_band.py::TestNoVarKey` and `test/test_parser.cscript` LB-41.

**Copied helpers read no computed constant.** No module-level non-literal constant may be read by a helper the served app copies from `dash_render.py`; a copied helper brings its callees and every name it reads. Guarded by `test/test_mode_parity.py::TestTheCopiedHelpersBringTheirCallees` and `test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`.

**The saved stale cue.** A saved page marks a frozen layer while a filter move has removed a row of its estimation sample, and the served app carries no cue. Guarded by `test/test_saved_stale_cue.py::TestTheCueAppearsOnAMove`.

**An empty layer keeps its style.** A layer left empty keeps its scheme style and its key entry in both modes. Guarded by `test/test_emptied_layer_style.py::TestAnEmptiedLayerKeepsItsStyle` and `test/test_emptied_layer_style.py::TestTheKeyIsTwoways`.

**The served redraw widths.** The served redraw copies spacing-derived glyph widths (bar widths) from its throwaway figure onto the live sources. Guarded by `test/test_served_filter_move.py::TestTheRedrawGeometry`.

**The per-launch key.** The served app admits nothing without its per-launch key (Gate A `_dash_token_auth`, Gate B `_dash_session_token_ok`), keys are compared with `hmac.compare_digest`, and every link is 127.0.0.1. The key is never missing: started without one, the app makes its own (`_dash_server_app`, or `_dash_bokeh_serve_key` under `bokeh serve`) and prints only the path of its 0600 link file; the key line follows the app text on the launch pipe. Stata never prints the key, except a warned, once-only print of the link when no link file can be written anywhere. Guarded by `test/test_serve_token.py::TestTheServedAppRequiresItsToken::test_the_page_without_the_token_is_403`, `test/test_serve_token.py::TestTheSessionGate::test_no_configured_token_makes_one_and_still_refuses`, `test/test_serve_token.py::TestTheLauncherPassesTheToken::test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served`, and `test/test_serve_launch.cscript` TOK-03.

**Embedded rows.** A page holds a cell only if a layer, a recomputed KPI, a filter or `csv` reads it (`_dash_embed_plan`, one function both modes run); whole-data rules read `self.df`/`df`, never a source. Both modes number the rows they send by rank: the served frame is relabelled by `_dash_page_index` right after the plan, and every served row-keyed map goes through `_dash_relabel`. Guarded by `test/test_embedded_rows.py::TestTheSavedPageHoldsOnlySelectedRows::test_no_excluded_value_is_embedded` and `test/test_embedded_rows.py::TestTheServedIndexIsARank::test_no_index_label_outside_the_pages_ranks`.

## Invariants introduced by WP-30

**Portable runners.** Stata is started only through `scripts/stata_batch.sh` (`STATA_BIN`, `STATA_ARCH`). Runners and extractors read the tree from `DASH_REPO`. `test/test_runner_portability.py` guards `scripts/`, `test/` and the Makefile against the fixed prefix and home paths. Guarded by `test/test_runner_portability.py::TestNoMaintainerPaths::test_no_home_directory_path`, `test/test_runner_portability.py::TestNoMaintainerPaths::test_no_arch_literal`.

**Stata 19 floor.** Every program in dash.ado and dash_setup.ado opens with `version 19`, except the Stata guards (`_dash_require_stata`, `_dash_stata_ok`, `_dash_setup_stata`: version 13) and the constants (`_dash_statamin`, `_dash_pymin`). The guard is the first statement of `dash` and `dash_setup` (test_version_floor.py::TestTheStataFloor). Guarded by `test/test_version_floor.py::TestTheStataFloor`, `test/test_version_floor.py::TestTheStataFloor::test_dash_setup_names_the_stata_floor_once`.

**Measured Python floor.** The declared Python floor is `_dash_pymin`; every `_BASELINES` entry is a stack both suites pass under and the floor is the lowest of their Pythons (test_version_floor); a new floor is measured by hand with `scripts/floor_matrix.sh` and `make test-floor` (the procedure is the script's header; `make gate` does not re-test it), never assumed. Guarded by `test/test_version_floor.py::TestTheFloorIsTheTestedBaseline::test_the_python_floor_is_the_lowest_baseline_python`, `test/test_version_floor.py::TestTheFloorInterpretersBehaveAlike::test_the_child_prints_tracebacks_from_the_handed_over_source`.

**One shipped scheme list.** The shipped scheme list is one list of twenty-six in dash.ado `_dash_shipped_schemes`, `SchemeParser._BUILTIN_NAMES`, the extractor's `SCHEMES`, dash.pkg and dash.sthlp, held equal by `test_scheme_resolution.py::TestTheShippedListIsOneList`; scheme files are generated, never hand-edited". Guarded by `test/test_scheme_resolution.py::TestTheShippedListIsOneList`, `test/test_twenty_six_schemes.py::TestTheSixResolveInBothModes::test_by_build_scheme`.

**Stata size units.** Every size an option gives goes through `OptionTranslator.resolve_size` on one unit (1 rs = 2.88 pt = 3.84 px); text sizes are written by `css_pt`; a figure's reference length is stamped by `SchemeParser.apply_to_figure`; a layer's brushed copies are synced from its glyph by `GlyphMapper._sync_brushed_copies` at the end of `_dash_add_glyph`/`_dash_add_pc_glyph` (ratification row 27). Guarded by `test/test_size_units.py::TestAbsoluteUnitsFollowTheSchemesReference::test_title_and_marker`, `test/test_size_units.py::TestAdversarialSizes::test_a_megabyte_value_is_judged_at_once`.

**Graph text is finished once (S09, S29).** Every canvas text sink is finished by `_dash_finish_graph_text`, last in each mode; a sink made after it is finished and marked by its maker; graph text is translated once: every canvas sink takes raw text and `_dash_finish_graph_text` (or its maker, then the mark) translates it; `_dash_graph_text` is not idempotent. Marker-label columns are decided over `GlyphMapper.dataset`, never the rows in view. Guarded by `test/test_canvas_tex.py::TestAfterAFilterMove::test_saved_key_after_the_move`, `test/test_canvas_tex.py::TestAfterAFilterMove::test_saved_stale_cue_carries_the_finished_key`, `test/test_graph_text.py::TestEverySinkBothModes::test_by_panel_labels_and_overall_text_are_translated`, `test/test_graph_text.py::TestGraphTextTruth::test_char_codes`.

**twoway's command form.** A dash command's prefix, saving() grammar and browser rule are twoway's: test/test_wp30_truth.cscript CF-01..08 compare them with test/fixtures/twoway_command_form_truth.json; `$dash__display` is a test seam, read only by the two browser deciders, never documented. Guarded by `test/test_packaging.py::TestNoUnsuppressableBrowserWindow::test_each_decision_reads_the_switches`, `test/test_adversarial_matrix.py::TestRendererOutputPath`.

**One line-width rule.** Line widths have one rule: OptionTranslator.translate_lwidth → resolve_size(kind "line") → line_px (Stata units × 3.84 px, 0.3 pt floor); scheme widths go through SchemeParser._lwidth, never a pixel literal. Guarded by `test/test_line_width_units.py::TestTheUnitFunctions::test_line_px_floors_and_converts`, `test/test_line_width_units.py::TestTheLadderIsStatas::test_each_keyword_is_its_stata_units`.

**Filter-free glyph geometry.** No glyph geometry depends on the rows a filter keeps: bar widths are one x unit or barwidth() (date units on date axes, per-row `__dash_bar_*` columns on period axes) and rcap caps are screen-unit markers tagged dash_cap". Guarded by `test/test_bar_range_geometry.py::TestBarIsOneXUnit::test_the_width_is_twoways`, `test/test_bar_range_geometry.py::TestRbarReadsBarwidth::test_the_option_is_drawn`.

**Axis writers at build time.** Every numeric axis gets a Stata writer at build time through `_dash_axis_tick_formats`; no callback rewrites an axis formatter; a date axis keeps its date writer unless `format()` or `x/yvarformat()` is given. Guarded by `test/test_display_format_writer.py::TestNarrowExplicitDigits::test_the_measured_rows_in_python`, `test/test_display_format_writer.py::TestNarrowFixture::test_every_row_under_node`.

**Legend keys and default titles.** Legend keys come only from `_dash_layer_series`; default axis titles only from `_dash_axis_default_titles` (twoway's first-equals-last rule per axis); both are raw text. Guarded by `test/test_series_labels.py::TestTheAxisTitleRule::test_first_equals_last`, `test/test_series_labels.py::TestTitlesMatchTwoway::test_titles`.

**Render-time dependency guards.** Every `dash` command but `clear` runs `_dash_require_deps` right after the Mata guard; dash_render.py and the generated app import packages only inside top-level `try` blocks that call `_dash_dep_fail`, and the standard library outside them; `dash clear` prunes through `dash_setup_lib.stdlib_entry`; `_dash_pymin`, `_dash_pyfloor` and `_DASH_MIN_PYTHON` are one number. Guarded by `test/test_dependency_guards.py::TestTheRendererRefusesWithTheRemedy`, `test/test_version_floor.py::TestThePythonFloorIsOneNumber`.

**Function layers that need points.** A function layer drawn empty for want of Stata's points carries `GlyphMapper._mark_needs_points`'s mark, and `_dash_note_empty_layer` words the reason; every edit of `map_function` keeps it. Guarded by `test/test_function_expr.py::TestTheFallbackSaysWhatItNeeds::test_each_refusal_names_what_it_met`, `test/test_function_expr.py::TestTheFallbackSaysWhatItNeeds::test_points_that_cannot_be_read_say_so`.

**Default bases.** A default base of bar, spike, dropline and area is a tagged data column (renderer tag dash_base:) that only _dash_finish_auto_bases and its JS twin write, from the finished unpadded scale; no value reader counts a base as data. Guarded by `test/test_bar_range_geometry.py::TestTheDefaultBaseIsTwoways::test_every_case`, `test/test_bar_range_geometry.py::TestTheDefaultBaseIsTwoways::test_auto`.

**by() panel text cells.** A by() graph's panel label is the Title named dash_by_label, and its overall text lives in the chrome cells dash_by_head/dash_by_foot of the panel grid; find panels with test/by_panel_probe.py, never by fig.title". Guarded by `test/test_by_text.py::TestPanelsMatchTwoway::test_panels`, `test/test_by_text.py::TestOverallTextMatchesTwoway::test_texts`.

**Scheme lookup.** A scheme is found by name along the ado-path dash.ado writes as build_options.scheme_dirs, shipped names first; a file is read only when it is a regular file of at most 1,048,576 bytes inside the directory it was found in; scheme files are data and the directories never reach a page or an app". Guarded by `test/test_scheme_lookup.py::TestThemeNamesAndFiles::test_a_graph_level_alias_is_the_alias_in_both_modes`, `test/test_scheme_lookup.py::TestPerGraphSchemes::test_no_one_scheme_warning`.

**Date units on every axis.** A date column stays epoch ms in every source. A layer on an axis that is not a date axis reads it through the one tagged dash_date_units transform per kind, and every Python and JS reader of glyph coordinates converts a field carrying that transform (_dash_spec_units with _dash_date_units, dash_date_units). Guarded by `test/test_date_axis_residuals.py::TestLiteralLayersOnADateAxis`, `test/test_mode_parity.py::TestTheTwoModesAgreeOnDateUnits`.

**Label positions and text box styles.** Per-row label positions live only in `__dash_mlabvpos_*` columns built by `GlyphMapper._mlabel_vpos_columns` from one Stata name; text box styles resolve only through `SchemeParser.textbox_style`'s table. Guarded by `test/test_mlabtextstyle.py::TestTheTable::test_every_name_resolves`, `test/test_mlabtextstyle.py::TestTheLabels::test_style`.

**Region styling.** Region colours and widths are resolved only by `_dash_region_spec`/`_dash_apply_regions`, which emit `#rrggbb`, `None` and numbers; `bgcolor()` is the canvas under the graph region. Guarded by `test/test_region_truth.py::TestAgainstTwoway::test_probe`, `test/test_region_truth.py::TestTheTable::test_it_is_twoways_parser`.

**Reference-line positions.** Reference-line positions are expanded once, by Stata's numlist, in `_dash_line_expand`; the renderer's `_dash_refline_positions` is the fallback; Spans are added in one assignment at level underlay. Guarded by `test/test_reference_lines.py::TestPositions::test_probe`, `test/test_reference_lines.py::TestLstyle::test_probe`.

**One join glyph.** Every connecting line is drawn through `_dash_join_glyph` from `_dash_join_vertices`' index pairs; synthetic rows carry a null row id; `dash_join_rebuild` is its saved-page twin. Guarded by `test/test_connect_options.py::TestDrawnAsTwowayDrawsThem::test_every_probe`, `test/test_connect_options.py::TestTheVertices::test_every_rule`.

**The bokeh window.** The bokeh window is declared once (`_DASH_BOKEH_*`; `min_bokeh`/`max_bokeh`), pinned by `TestTheWindowIsDeclaredOnce`; every Bokeh internal dash's security relies on is on `_DASH_BOKEH_INTERNALS` with a guard that fails closed. Guarded by `test/test_bokeh_window.py::TestTheWindowIsDeclaredOnce`, `test/test_bokeh_internals.py::TestTheTemplateFailsClosed::test_a_template_without_the_blocks_is_refused`.

**Time-series operators.** An operator expression reaches Stata only after `_dash_tsop_rewrite`'s and `_dash_tsop_gen`'s canonical-form checks, and the renderer reads __dasht columns only through `_dash_tsop_cols_named`. Guarded by `test/test_ts_operators.py::TestTheCsv::test_the_meta_carries_headers`, `test/test_ts_operators.py::TestTheCsv::test_the_header_is_the_expression`.

**One colour reader.** Every colour option is read through `OptionTranslator.stata_colour` with the site's own base; no applier or mapper calls `translate_mcolor` for a user colour. Guarded by `test/test_bare_intensity.py::TestTheRule::test_the_base_rule`, `test/test_bare_intensity.py::TestTheRule::test_the_base_is_never_text`.

**Date ticks.** Date ticks come only from `_dash_tsnatscale_ticks` (Python) and its line-for-line port `dash_tsnatscale` (JS); a change to either changes both, proved by `TestJsTsnatscaleEqualsPython`. Guarded by `test/test_natscale_js.py::TestJsTsnatscaleEqualsPython`, `test/test_date_axis_ticks.py::TestDefaultDateAxes::test_build`.

**recast() decided once.** A recast layer's drawn type is decided only by dash.ado `_dash_recast_opt`; the renderer reads `type` for drawing and `recast_from` first for labels; derived layers draw as a target only through `GlyphMapper._dash_draw_xy_as`. Guarded by `test/test_recast.py::TestTheDrawAsHelper::test_each_target`, `test/test_recast.py::TestDerivedRecast::test_type`.

**Shared served payload.** Served sessions share the decoded payload read-only through `_dash_shared_payload`; a session takes a slot only through `_dash_session_open` and releases it once; nothing in the generated app writes a shared array. Guarded by `test/test_served_resources.py::TestSessionsAreCapped::test_the_fourth_page_is_busy`, `test/test_served_resources.py::TestIdleSessionsAreClosed::test_closed_after_the_lifetime`.

**Plot-region margin.** A plot-region margin is a per-side frame-fraction pair from `_dash_plot_margin` only; ranges are padded only by `_dash_padded_range` and its JS twin; the inner box is written only by `_dash_inner_box` and `dash_axis_finish`. Guarded by `test/test_region_margins.py::TestTheMarginGrammar::test_form`, `test/test_region_margins.py::TestThePlotMargin::test_probe`.

**by() layout.** A by() graph's layout lives only in `_dash_layout_cell` (positions from `_dash_by_positions`, sizes from `_dash_by_scale_panel`, applied once per panel); dash.ado's `_dash_by_check` is the only place by() arguments are refused. Guarded by `test/test_by_grid.py::TestTheGrammar::test_python_equals_mata`, `test/test_by_grid.py::TestTheGrammar::test_every_spelling_is_twoways`.

**Turned layers.** A horizontal layer is drawn upright by its mapper and turned once by `_dash_transpose_layer`; every axis-variable reader goes through `_dash_role_letter`. Guarded by `test/test_horizontal.py::TestHorizontalIsTheTranspose::test_type`, `test/test_horizontal.py::TestTheAxesFollowTheLayer::test_titles_and_date_axes`.

**Reference-line extents.** An unextended reference line is an Arrow whose ends only `_dash_refline_extents` and `dash_refline_extent` write, from the finished range and its margin. Guarded by `test/test_refline_extent.py::TestTheExtent::test_probe`, `test/test_refline_extent.py::TestTheFlags::test_rule`.

**Date tokens.** A date token typed by the user is converted only by Mata's string date functions in `_dash_tdate_value`, behind its whitelist; the spec never carries a t key. Guarded by `test/test_taxis_options.py::TestTheDeclarations::test_the_axis2_forms`, `test/test_taxis_options.py::TestTheHelp::test_it_documents_axis2_format_and_left_aligned`.

**Added axis values.** Added axis values live only in `_dash_extra_ticks`, unioned by `_dash_place_count_ticks` and `_DASH_AXIS_FINISH_JS` from the plan's `extra`. Guarded by `test/test_axis_add.py::TestTheParser::test_add_is_read_from_the_tail`, `test/test_axis_add.py::TestAddUnionsWithTheDefault::test_probe`.

**by() chrome cells.** A by() graph's chrome cells are bare `Plot`s named `dash_by_*`; legend and key clones carry `_DASH_SWATCH_PREFIX` names and live only in those cells; the stacked view is the one `dash_by_stack` CustomJS per grid; a by() panel's label is drawn by the `ColorBar` named `dash_by_label_box`, and S28's `dash_by_label` Title stays hidden as its text record. Guarded by `test/test_by_axes_keys.py::TestOuterAxes::test_probe`, `test/test_by_axes_keys.py::TestAxisTitlesOnce::test_probe`.

**Vector export.** The vector export is a client-side CustomAction added only by `_dash_name_save`; never set `output_backend='svg'` on a figure in a grid. Guarded by `test/test_export_svg.py::TestTheConstants::test_the_code_is_fixed_and_plain`, `test/test_export_svg.py::TestTheConstants::test_the_icon_is_a_small_data_uri`.

**Filter moves write no glyph property.** No filter move writes a glyph property in either mode and no filter callback holds a glyph; a turned layer differs from the upright one only in its glyph bindings, and the tooltip builder reads them through `_role_prop`, deciding turned-ness from `layers` and `_dash_is_horizontal`. Guarded by `test/test_horizontal_moves.py::TestTheTooltipFollowsTheTurn::test_a_turned_histogram_answers_along_its_bins`, `test/test_horizontal_moves.py::TestTheTooltipFollowsTheTurn::test_a_turned_density_names_its_rows_as_upright`.

**Added text.** Added text reaches the renderer only as `added_text` records built by Mata from values read by value; the renderer draws each as a tagged data-unit `Label`, raw until the document pass. Guarded by `test/test_added_text.py::TestTtext::test_it_is_declared`, `test/test_added_text.py::TestTheTables::test_they_are_the_fixtures`.

**Served moves and the worker.** A served move writes models only in its next-tick apply step; the recompute worker reads its mapper and scheme through `_dash_cur_mapper()`/`_dash_cur_scheme()`, and every name it reaches is in `test_served_worker._WORKER_AUDIT`. Guarded by `test/test_served_worker.py::TestTheLoopAnswersDuringARecompute::test_health_and_a_new_session`, `test/test_served_worker.py::TestAsyncEqualsSync::test_corpus`.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **dash** (13732 symbols, 30999 relationships, 100 execution flows).

> Index stale? Run `node .gitnexus/run.cjs analyze --index-only` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? Bootstrap with `npx`, `bunx`, or `pnpm dlx` — e.g. `bunx gitnexus@latest analyze` (npm 11 npx crash; #1939).

## Always Do

- **MUST run impact before editing.** Use `impact({target: "symbolName", direction: "upstream"})` or `node .gitnexus/run.cjs impact "symbolName" --direction upstream --repo .`; report callers, processes, and risk. Never substitute grep for graph analysis.
- **MUST analyze graph changes before committing.** Use `detect_changes({scope: "all"})` (MCP) or `node .gitnexus/run.cjs detect-changes --scope all --repo .` (CLI fallback). `partial: true` or `truncated: true` is not a clean check — a zero means unseen, not unaffected; re-run it. For regression review: `detect_changes({scope: "compare", base_ref: "main"})` or `node .gitnexus/run.cjs detect-changes --scope compare --base-ref "main" --repo .`.
- MUST warn on HIGH/CRITICAL `risk` pre-edit; never use `riskSharedAxes` to waive a HIGH/CRITICAL `risk` warning. Compare File/symbol: MCP File omits axes; Graph-RAG expands File.
- **MUST treat `risk: UNKNOWN` as unresolved, not as low.** An empty caller set is not evidence the symbol is unused — it can also mean the callers are not resolvable by the index (plain-object property access, dynamic dispatch, cross-language calls). `impact` pairs `UNKNOWN` with a `riskNote` saying so. Confirm with a text search before treating the symbol as safe to change or delete; do not proceed on the strength of a zero.
- **MUST use `query({search_query: "concept"})` for concepts/flows, `context({name: "symbolName"})` for a named symbol, or `impact` for blast radius, on read-only callers, dependencies, imports, or execution flow.** Graph first; text search only for empty/`UNKNOWN`/literals.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method before MCP/CLI impact analysis.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis, and never read `UNKNOWN` as an all-clear — it means the walk could not answer, which is the one verdict that requires confirming by other means.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit before MCP/CLI graph change analysis.

## Resources

| Resource | Use for |
| --- | --- |
| `gitnexus://repo/dash/context` | Codebase overview, check index freshness |
| `gitnexus://repo/dash/clusters` | All functional areas |
| `gitnexus://repo/dash/processes` | All execution flows |
| `gitnexus://repo/dash/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
| --- | --- |
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
