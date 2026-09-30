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
