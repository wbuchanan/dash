0. **Brevity.** Only explain what is necessary and make sure your explanations are as succinct as possible without compromising the accuracy of your communications.  Be as efficiency as possible when communicating.
1. **Security is paramount.** Any feature, function, data object, input, output, or other application surface that could be vulnerable to exploitation should be hardened as much as possible at the initial stages of development and should be verified throughout the application development process.
2. **Honesty.** You will only ever provide true, correct, and honest responses. When asked to do something you will do it completely and will not report that a task is complete until the entire task is finished.
3. **Testing.** Every function for every feature must have a unit test.  The application should have comprehensive end to end tests to verify that users can navigate in the application freely without error and be able to use all the features without error.
4. **Before Committing Code.** Pull from the local main branch, then run the full test suite including the newly developed code. If there are errors or failing tests, fix the issue in the code base and rerun the failed tests.  Do this until all tests pass.
5. **Committing.** Always commit to your local branch and provide the command to merge those changes into the local main branch.  Never commit directly to the main branch unless explicitly requested for that time only.
6. **Commit Messages.** Never include any information about claude or anthropic in commit messages.  Just provide information about the changes being made to the code base.
7. **Bugs**. Everytime you get a report about some feature or functionality not working correctly, you must develop an additional test to prevent the same bug from being reintroduced into the codebase in the future after diagnosing the issue and before developing code to fix the issue.  
8. **Agents.** Use the largest number of agents the system will support when working on multiple tasks to parallelize the work load and complete it efficiently.
9. **Plans.** When developing plans for features or applications provide a combination of high level information and extremely detailed information.  Develop user stories, business requirements, and technical requirements for each feature, functionality, component, or other organizational unit for the code base. Additionally, develop a test plan in a similar manner. The goal is to ensure that any human or agent developer can quickly and easily build and ship the code correctly the first time based on the detailed information contained in the plan.
10. **Stata invocation.** Run Stata only through the console binary: `arch -arm64 /usr/local/bin/stata-mp -b do <file>.do`. Never launch the GUI application (`/Applications/StataNow/StataMP.app/Contents/MacOS/StataMP`, `stataMP`, or `open -a StataMP`): in batch mode it runs the do-file and then parks on a modal "has completed" alert that only a human can dismiss. A PreToolUse hook in `.claude/settings.json` (`.claude/hooks/block-stata-gui.sh`) blocks such commands.
11. **Running the Python test suite.** While iterating, run only the tests you changed: a file (`python3 -m pytest test/test_x.py`), a node id, `-k`, or `--lf`. Run the full suite once, before committing, as `python3 -m pytest test/ -q`; `pyproject.toml` makes it parallel (`-n auto`) by default and it finishes in about two minutes (pass `-n0` only to debug with `--pdb`). Never launch a second full run while one is executing, and never relaunch a run to check on it: read its log. A session-start lock in `test/conftest.py` refuses a concurrent full run, and the PreToolUse hook `.claude/hooks/guard-full-suite.sh` refuses a third full launch in one session unless the command is prefixed with `FULL_SUITE_RERUN=1`.

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
