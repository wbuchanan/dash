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

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **dash** (19939 symbols, 32014 relationships, 108 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/dash/context` | Codebase overview, check index freshness |
| `gitnexus://repo/dash/clusters` | All functional areas |
| `gitnexus://repo/dash/processes` | All execution flows |
| `gitnexus://repo/dash/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
