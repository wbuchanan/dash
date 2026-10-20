# Section 59: README, package and versions

> Part of: WP-31 · GAPS3 rows: I2, I3, I4, I5, I7 · Risk: green · Batch: 20 · Depends on: 01 · Blocks: -- · Tasks: 8, 5 commits · Case-id prefix: U59

## Overview

**What is wrong today** (GAPS3 4.I, re-read at `6370ca4`). **I2:** `ls README* LICENSE*` is empty; `dash.pkg` (61 lines, REVIEW-4 R4-30: `v 3`, `d` lines, `d Version: 0.1.0  09oct2026`, `d Distribution-Date: 20261009`, then the `F` lines) has no `d Author:` or `d KW:` line; dash.sthlp has no `net install` instruction; its last section is `{marker author}{title:Also see}` (:5203-5204) listing `{helpb dash_setup}, {helpb twoway}, {helpb python}` and no author; the Jump To list (:3-21) names 19 sections where the file has 32 `{marker ...}` titles. The LICENSE part is closed by decision (Q31). **I3:** a failed `dash_setup` leaves installed packages in place and does not say what it installed (dash_setup.ado:89-93 fails out after `_dash_setup_summary`; :825-829 prints `Unmet:` from `items` that mixes failures and warnings); no hash-pinned installs; the served child is `sys.executable` (dash_render.py:51842 `_cmd = [sys.executable, "-P", "-c", _DASH_BOOT, ...]`), Homebrew's base Python under a venv link, working only through Stata's exported `PYTHONPATH`; a `dash_setup_lib.py` or `bokeh.py` in the working directory is found first. **I4:** `_dash_dep_versions()` (dash_render.py:189-210) is returned and printed only through dash.ado:6139 (`python: _dash_dv = _dash_xm._dash_dep_versions()`); the renderer's `__main__` (:52121) and the app's `__main__` print no note, so a hand-run renderer or app with a sub-floor numpy or pandas is silent; Python below 3.7 dies at the parser. **I5:** dash_render.py:60 `Version: 1.0.0  25mar2026`; dash.ado:1 `*! dash.ado  v2.0`, :5 `Architecture (v2.0)`, :13 `_dash_plot  — parse and route a plot definition (v2.0)`, :6638 region; dash_parse.mata:1 `*! dash_parse.mata  v2.0`; `test/test_pkg_metadata.py:48-57` `VERSION_SOURCES` pins only the `*! Version:` lines of six files. **I7:** the dash_setup_lib load is guarded (`sys.dont_write_bytecode` saved, set and restored at dash.ado:6296-6299 and dash_setup.ado:1080-1083) but the renderer load at dash.ado:6118-6133 (`spec_from_file_location` + `exec_module`) is not, so the 1.2 MB `dash_render` bytecode is written under PLUS/py and `ado uninstall` leaves `__pycache__` behind.

**After this section** `README.md` exists at the repository root with the `net install` line, what dash is, the requirements and `dash_setup`; `dash.pkg` carries `d Author: Billy Buchanan` and `d KW:` lines and `test_packaging.py` admits README.md to the root; the help ends with `{title:Author}` and a separate `{title:Also see}`, the Jump To list names every `{marker}` title, and an Installation paragraph gives the `net install` line; `dash_setup` records what it installed and prints the `pip uninstall` line on failure, separates `Unmet:` from `Warnings:`, pins hashes where pip supports `--require-hashes` (ratification item 1: hash pinning requires a lock file; this section records the pins in `test/requirements-stata.txt`'s `--hash` form only if the maintainer ratifies, else documents why not), launches the served child with the linked interpreter (`c(python_exec)` passed through the spec, falling back to `sys.executable`), and removes the working directory from `sys.path[0]` before importing dash_setup_lib and bokeh; the renderer's and the app's `__main__` print `_dash_dep_versions()`'s note and the future-statement guard catches the pre-3.7 SyntaxError with the floor message; every version header reads `0.1.0` and the metadata pin covers every file and header; the renderer load is wrapped in the same `dont_write_bytecode` guard and `test_installed_layout.py` pins that an install leaves no `__pycache__`.

**Test order and commit rule.** Five cycles, five commits `(WP-31 I2)`, `(WP-31 I3)`, `(WP-31 I4)`, `(WP-31 I5)`, `(WP-31 I7)`; each cycle's first task writes its failing tests to `<scratch>/59-0k-failure.txt` and never commits; I5's version renumbering comes before S61's date bump, which then touches every header the pin covers.

### Section decisions

- **D-59.a README content** (Q32: GitHub now, SSC later): title, one paragraph of what dash is (from dash.pkg's `d` lines 4-15), Requirements (dash.pkg:17-19 verbatim), Installation (`net install dash, from("https://github.com/wbuchanan/dash/raw/main/")` -- the exact URL is ratification item 2; the README states it once and `test_readme.py` pins it against `stata.toc`), `dash_setup` (dash.pkg:21-24), a two-line example, links to `help dash` and CHANGELOG.md. No licence section (Q31).
- **D-59.b dash.pkg lines**: after `d Distribution-Date: 20261009` insert `d Author: Billy Buchanan` and `d KW: twoway` / `d KW: dashboard` / `d KW: bokeh` / `d KW: interactive graphics` (four `d KW:` lines, SSC's form); `d Support: william@williambuchanan.net` is NOT added (ratification item 3: an email in a shipped file).
- **D-59.c Help Author section**: :5203 `{marker author}{title:Also see}` becomes `{marker author}` / `{title:Author}` / `{pstd}Billy Buchanan{p_end}` / blank / `{marker alsosee}` / `{title:Also see}` / the existing `{psee}` lines; the Jump To list gains one `{viewerjumpto}` per missing `{marker}` title in file order (the 13 missing: differences is present; add those of :583 added_text, :914 validation, :1066 stylelists, :1303 saving_chars, :1325 nobrowser_global, :1444 results (present), :1550 tabs, :2586 faceting, :2759 marker_labels, :2899 smoother_options, :3270 ciband, :3327 weights, :3402 region_options, :3511 axis_options, :3899 taxis, :4042 graph_text, :4140 colorvar, :4275 geometry, :4329 markers, :4455 namedstyles, :4519 scheme, :4967 unsupported, :5203 author, alsosee -- read the markers at the batch-20 base with `grep -n '{marker ' dash.sthlp` and the titles with the `{title:` line that follows each; add every one that has a `{title:}` and no `{viewerjumpto}`); an `{marker install}{title:Installation}` paragraph after Description with the `net install` line and `dash_setup`.
- **D-59.d I3's four legs**: (i) `_dash_setup_summary` prints `Installed by this run: <pkgs>` and `To undo: <python> -m pip uninstall <pkgs>` when the run installed anything and then failed (dash_setup.ado tracks installed names in a local `installed_now` appended by `_dash_pip_command`'s caller); (ii) `Unmet:` lists failures only, `Warnings:` the warnings; (iii) the served child: `_dash_serve_spec`/the spec gains `"python_exec": c(python_exec)` written by dash.ado, read by `_dash_launch_app` (dash_render.py:51842 region) as `_py = spec.get("python_exec") or sys.executable` after `_validate_output_path`-style checks (an absolute path to an existing file, no shell metacharacters; else `sys.executable` with a note); (iv) `sys.path`: in dash_setup_lib's `VERIFY_CODE` and in `_dash_require_deps`' python lines, `sys.path = [p for p in sys.path if p not in ("", os.getcwd())]` before the imports, restored after. Hash pinning: documented as deferred unless ratified (the setup installs from PyPI by version; a `--require-hashes` install needs every transitive wheel's hash per platform).
- **D-59.e I4**: in `dash_render.py`'s `if __name__ == "__main__":` (:52121) and in the generated app's `__main__` (`_generate_app_source`, the header's guard block :48005-48035 region), after the import guards: `_r, _n = _dash_dep_versions(); if _n: print(_n, file=sys.stderr)`; the SyntaxError leg: the module's first statement `from __future__ import annotations` already stops older Pythons with a SyntaxError whose shown line is that statement; add a comment line directly above it `# dash needs Python 3.11 or later (dash_setup); a SyntaxError here means an older Python` so the traceback's shown source carries the remedy (no code path can run before the parse).
- **D-59.f I5**: dash_render.py:60 → `Version: 0.1.0  09oct2026` (S61 bumps the date); dash.ado:1 `*! dash.ado  v0.1.0`; :5 `Architecture (0.1.0)`, :13 and :6638 `(v2.0)` → `(0.1.0)`; dash_parse.mata:1 `*! dash_parse.mata  v0.1.0`; `VERSION_SOURCES` gains `"dash_render.py": r"^Version:\s*(\S+)\s+(\S+)\s*$"` and a new `HEADER_SOURCES` map of `(file, regex)` for the `v<version>` headers (`dash.ado`: `^\*! dash\.ado\s+v(\S+)$`; `dash_parse.mata`: `^\*! dash_parse\.mata\s+v(\S+)$`) with `test_every_header_states_the_declared_version`; dash_setup.ado has no such header (verify with `sed -n 1,3p`).
- **D-59.g I7**: wrap dash.ado:6118-6133 (from the `python: _dash_ok = ...` line to `python: sys.modules["_dash_render_export"] = _dash_xm`) with the two lines used at :6296 and :6299: before, `python: import sys, sfi; sfi.Macro.setLocal("_dwb", "1" if sys.dont_write_bytecode else "0"); sys.dont_write_bytecode = True`; after, `python: import sys, sfi; sys.dont_write_bytecode = sfi.Macro.getLocal("_dwb") == "1"` (also on the `exit 198` path: place the restore before `exit 198`). `test_installed_layout.py` gains `TestNoBytecodeIsWritten::test_a_render_from_the_install_leaves_no_pycache` (renders through a scratch PLUS/py copy under `python3 -I` with `sys.dont_write_bytecode` False, then asserts no `__pycache__` under it) -- the Stata leg is cscript U59-1 in `test_setup_honesty.cscript`: after `dash scatter mpg weight`, `dir "<PLUS>/py/__pycache__"` fails.

## Risk: [green] -- documents, metadata, a guard and two prints; the served-child interpreter is the one behaviour change

**Risk factors.** 1. `test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own` refuses README.md unless `_ROOT_ALSO` admits it. 2. Launching the served child with `c(python_exec)` changes `dash serve`'s process; a venv-linked Stata must still serve. 3. The version header edits touch lines other tests read (`test_version_floor.py` reads `*! Version` lines? it reads the floor strings; check).

**Mitigation.** 1. 59-01 adds README.md to `_ROOT_ALSO` with a comment. 2. `test_serve_launch.cscript` and `test_e2e_serve.cscript` run through the driver in 59-04 (they serve on fixed ports: one at a time in a slot). 3. `grep -rn "v2.0\|1.0.0" test/` before editing; flip pins in place.

## Dependencies

- **Depends on:** 01. **Blocks:** none; S61's date bump (S61.1) follows I5's renumbering.
- **Parallel batch 20** with S60 (test harness, scripts, CI): S60 edits `test/conftest.py`, scripts/ and the Makefile; S59 edits none of them. Both may edit `test/requirements-stata.txt` only if D-59.d's hashes are ratified (then S59 owns it; S60 reads it).

## Evidence

- `dash.pkg` 61 lines (R4-30); :26 `d Version: 0.1.0  09oct2026`; :27 `d Distribution-Date: 20261009`; no `Author`/`KW`.
- dash.sthlp:3-21 nineteen `{viewerjumpto}` lines; `{marker ...}` with `{title:}` at :46, :154, :235, :629, :1144, :1252, :1353, :1444, :1472, :1584, :1622, :1679, :1792, :1926, :2308, :2390, :2534, :5136, :5203 (19 jumped) and the sub-section markers at :583, :914, :1303, :1325, :1550, :2586, :2759, :2899, :3270, :3327, :3402, :3511, :3899, :4042, :4140, :4275, :4329, :4455, :4519, :4967; :5203-5207 `{marker author}` / `{title:Also see}` / `{psee}` / `{helpb dash_setup}, {helpb twoway}, {helpb python}`.
- dash_setup.ado:89-93 (the Python-not-linked failure path calling `_dash_setup_summary , failures() warnings() items()` then `exit 198`); :825-829 (`"requirement(s)."`, `display as error "  Unmet: \`items'"`).
- dash_render.py:51842-51843 `_cmd = [sys.executable, "-P", "-c", _DASH_BOOT, app_path, "--port", str(port)]`; :189-210 `_dash_dep_versions`; :52121 `if __name__ == "__main__":`; :60 `Version: 1.0.0  25mar2026`.
- dash.ado:1 `*! dash.ado  v2.0`; :5 `*! Architecture (v2.0):`; :13 `// _dash_plot  — parse and route a plot definition (v2.0)`; :6118-6133 the renderer load; :6139 the one `_dash_dep_versions` call; :6296-6299 the guarded dash_setup_lib load. dash_parse.mata:1 `*! dash_parse.mata  v2.0`; :529 `*! Version: 0.1.0  09oct2026`.
- test_pkg_metadata.py:48-57 `VERSION_SOURCES` (dash.ado, dash_parse.mata, dash_setup.ado, dash.pkg, dash.sthlp, dash_setup.sthlp).
- test_installed_layout.py classes :198, :269, :410, :480, :539 (none about bytecode).
- Existing tests that pin today's state: `test_packaging.py` root test (README.md absent); any test asserting the `sys.executable` child (`grep -rn "sys.executable" test/test_serve*.py test/test_server*.py`); `test_pkg_metadata.py::test_every_file_declares_the_same_version` (passes today over the six files; the renderer's `1.0.0` is outside it). Flipped in place where they pin the old value.

## User stories

- **US-59.1** As a Stata user finding dash on GitHub, I want a README with the install line and requirements.
- **US-59.2** As a user whose `dash_setup` failed, I want to know what it installed and how to undo it.
- **US-59.3** As a user running the renderer or app by hand, I want the same version note Stata shows.
- **US-59.4** As a maintainer, I want every version header to agree and an install to leave no bytecode behind.

## Business requirements

- **BR-59.1** README.md, `d Author`/`d KW`, the help's Author and Installation sections and a complete Jump To list exist and are pinned.
- **BR-59.2** A failed setup names what it installed and the undo line; `Unmet:` lists failures only; the served child is the linked interpreter; a working-directory `dash_setup_lib.py` or `bokeh.py` is not imported.
- **BR-59.3** A hand-run renderer or app prints the version note; an old Python's SyntaxError shows the remedy line.
- **BR-59.4** Every version header reads 0.1.0 and the pin covers all of them.
- **BR-59.5** Rendering from an installed tree writes no `__pycache__`.

## Technical requirements

- **TR-59.1 (I2)** README.md (D-59.a); dash.pkg (D-59.b); dash.sthlp (D-59.c); `test/test_packaging.py` `_ROOT_ALSO` += `"README.md"`; new `test/test_readme.py`: `test_the_install_line_names_the_toc_host` (the URL in README equals the `from()` the repository's `stata.toc` or Makefile `gate` target uses), `test_requirements_match_dash_pkg`, `test_help_has_an_author_and_an_install_paragraph`, `test_every_help_title_is_in_the_jump_list`, `test_dash_pkg_has_author_and_kw`.
- **TR-59.2 (I3)** dash_setup.ado (D-59.d i, ii, iv); dash.ado writes `python_exec` into the spec (the `_dash_serve_spec` writer; find with `grep -n '"nobrowser"' dash.ado` for the spec key list and add `"python_exec"` beside it) and `_dash_require_deps` (iv); dash_render.py `_dash_launch_app` (iii) with `_dash_child_python(spec)` (new module-level function; served copy list: not needed, the launcher is the parent's code; add to `function_test_map.py`); `dash_setup_lib.py` `VERIFY_CODE` (iv). Tests: `test/test_setup_honesty.cscript` U59-2 (a failed run after an install prints `Installed by this run:` and `To undo:`), U59-3 (`Unmet:` has no warning item); `test/test_server_launch.py` (or the file holding the launcher's tests: `grep -ln "_DASH_BOOT" test/*.py`) `TestTheChildInterpreter::test_the_spec_python_is_used`, `::test_a_bad_path_falls_back_with_a_note`, `::test_a_relative_or_shell_path_is_refused`; `test/test_setup_pep668.py` or `test_dependency_guards.py` `test_the_working_directory_is_not_on_the_import_path`.
- **TR-59.3 (I4)** dash_render.py `__main__` and the app header (D-59.e); `test/test_dependency_guards.py::TestTheVersionNote::test_a_hand_run_renderer_prints_the_note` (runs `python3 -I dash_render.py` in a subprocess with a stub numpy of `__version__ = "1.0"` on `PYTHONPATH`... too invasive: instead monkeypatch `np.__version__` and call the `__main__` body factored into `_dash_main(argv)`), `::test_the_app_prints_the_note`, `::test_the_future_line_carries_the_remedy_comment` (reads the two source files).
- **TR-59.4 (I5)** D-59.f; `test_pkg_metadata.py` `VERSION_SOURCES["dash_render.py"]`, `HEADER_SOURCES`, `test_every_header_states_the_declared_version`.
- **TR-59.5 (I7)** D-59.g; `test_installed_layout.py::TestNoBytecodeIsWritten`; `test_setup_honesty.cscript` U59-1.
- **TR-59.6 Security (rule 1).** `python_exec` from the spec is validated (absolute, existing, no `;|&$\`` characters, basename starting `python`) before use, else ignored with a note; no `shell=True`; the README holds no secrets; `sys.path` pruning removes `""` and the cwd only.

## Boundaries

- Not edited: `scripts/`, `Makefile`, `test/conftest.py`, `.github/` (S60's); `test/requirements-*.txt` unless hashes are ratified; dash.sthlp paragraphs other than Author, Also see, Installation and the Jump To list (S56 owns the rest; S56 lands in batch 19, before S59); the date in any `*! Version` line (S61's).
- No LICENSE file (Q31). No `d Support:` email (D-59.b).

## Stata truth

None compared with twoway. cscript cases U59-1 (no `__pycache__` after a render from PLUS/py: the installed-tree leg exists in `test_program_coverage.cscript`'s dash_setup end-to-end block; add the case where that block renders), U59-2, U59-3 in `test/test_setup_honesty.cscript`. Driver per BRIEF. No block in test_wp31_truth.cscript.

## TDD test stubs

- I2 (59-01): `test/test_readme.py::test_the_install_line_names_the_toc_host` (FileNotFoundError README.md), `::test_dash_pkg_has_author_and_kw`, `::test_help_has_an_author_and_an_install_paragraph`, `::test_every_help_title_is_in_the_jump_list` (lists the 20 missing).
- I3 (59-03): `TestTheChildInterpreter` (3), `test_the_working_directory_is_not_on_the_import_path`; cscript U59-2, U59-3.
- I4 (59-05): `TestTheVersionNote::test_a_hand_run_renderer_prints_the_note`, `::test_the_app_prints_the_note`, `::test_the_future_line_carries_the_remedy_comment`.
- I5 (59-06): `test_pkg_metadata.py::test_every_header_states_the_declared_version` (`1.0.0 != 0.1.0`, `v2.0`).
- I7 (59-07): `TestNoBytecodeIsWritten::test_a_render_from_the_install_leaves_no_pycache`; cscript U59-1.
Pinned tests to flip: `test_packaging.py` root test (via `_ROOT_ALSO`), any `sys.executable` child pin. Parity corpus: none.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| README, pkg lines, help Author/Install/Jump To | pytest `test_readme.py` (5), `test_packaging.py` | -- | n/a |
| Setup reporting, undo line, Unmet/Warnings | cscript U59-2, U59-3 | -- | Stata |
| Child interpreter, import path | pytest `TestTheChildInterpreter`, `test_the_working_directory_is_not_on_the_import_path`; cscript test_serve_launch.cscript | -- | served |
| Version note by hand | pytest `TestTheVersionNote` (3) | -- | saved and served |
| Headers agree | pytest `test_pkg_metadata.py` | -- | n/a |
| No bytecode | pytest `TestNoBytecodeIsWritten`; cscript U59-1 | -- | n/a |

AC-59.1 `test -f README.md`; `grep -c '^d Author: ' dash.pkg` → 1; `grep -c '^d KW: ' dash.pkg` → 4. AC-59.2 `grep -c 'v2.0\|1\.0\.0' dash.ado dash_parse.mata dash_render.py` → 0 for each. AC-59.3 `grep -c 'sys.executable' dash_render.py` is one fewer than at the base and `_dash_child_python` exists. AC-59.4 all named pytest files 0 failed; U59-1..3 PASS.

## Tasks

**Commit boundary.** 59-01..59-02 → `(WP-31 I2)` `Add the README, the package author and keyword lines, and the help's author, install and jump sections`; 59-03..59-04 → `(WP-31 I3)` `Report what dash_setup installed, launch the served child with the linked Python and keep the working directory off the import path`; 59-05 → `(WP-31 I4)` `Print the dependency version note from a hand-run renderer or app`; 59-06 → `(WP-31 I5)` `Renumber every version header to 0.1.0 and pin them all`; 59-07..59-08 → `(WP-31 I7)` `Load the renderer without writing bytecode under PLUS/py`. Each closing task closes its entry, deletes its `WP31_OPEN` key, replaces its marker under `### Fixed in WP-31`, rewrites its Tracked line with `commit pending` (DECISIONS A11; the merger's step k.3b writes the sha; no amend). Worktree `<W>` = `.../dash-wt/wp31-s59`.

<task type="auto" id="59-01">
  <name>Write the failing README and metadata tests</name>
  <files>test/test_readme.py, test/test_packaging.py</files>
  <action><![CDATA[Create test/test_readme.py with the five tests of TR-59.1 (the install URL read from README.md's first fenced `net install` line; the host compared with the `from(` argument in Makefile's gate target or scripts/run_release_gate.sh -- find it with `grep -n 'net install' Makefile scripts/*.sh`; if none names a URL, the test compares README's URL against a constant `INSTALL_URL` at the top of the test with a comment naming ratification item 2). Add `"README.md"` to `_ROOT_ALSO` in test/test_packaging.py with the comment `# WP-31 I2: the repository's README`. Run `python3 -m pytest test/test_readme.py test/test_packaging.py -q -n0 -p no:cacheprovider -rf > <scratch>/s59/59-01.log 2>&1`; write <scratch>/59-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s59/59-01.log` prints 5 (test_packaging passes: README.md is admitted but absent); `test -s <scratch>/59-01-failure.txt`.]]></verify>
  <done>The README and metadata tests existed and failed on the unmodified tree.</done>
</task>

<task type="auto" id="59-02">
  <name>Write README, pkg lines, help sections</name>
  <files>README.md, dash.pkg, dash.sthlp</files>
  <action><![CDATA[Create README.md (D-59.a). Insert the five dash.pkg lines after :27 (D-59.b). Edit dash.sthlp: the Author/Also see split (D-59.c), the Installation paragraph after the Description section (before `{marker plottypes}` at :235: `{marker install}` / `{title:Installation}` / `{pstd}` with the `net install` line as `{cmd:. net install dash, from("<URL>")}` and `{cmd:. dash_setup}`), and one `{viewerjumpto "<title>" "dash##<marker>"}` per missing title in file order. Run `python3 -m pytest test/test_readme.py test/test_packaging.py test/test_help_conformance.py $(grep -l "Also see\|viewerjumpto" test/test_help_claims_*.py) -q -p no:cacheprovider`; flip pins of the old structure in place (`Flipped (WP-31 I2)`). Close the I2 entry (`Pinned by test/test_readme.py::test_the_install_line_names_the_toc_host, test/test_readme.py::test_every_help_title_is_in_the_jump_list, test/test_readme.py::test_dash_pkg_has_author_and_kw`), delete the `"I2": "` key, replace `<!-- WP-31 I2 -->` with `- README.md gives the net install line, the requirements and dash_setup; dash.pkg carries Author and KW lines; help dash has Installation and Author sections and its jump list names every section. (WP-31, I2)`; rewrite the I2 Tracked line to the Closed form with `commit pending` (A11); commit (BUGS.md, GAPS3.md, CHANGELOG.md, the tracking test and the two test files are further files).]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; `grep -c '^d KW: ' dash.pkg` prints 4; `grep -c '{title:Author}' dash.sthlp` prints 1 and `grep -c '{title:Also see}' dash.sthlp` prints 1; `grep -c '^    "I2": "' test/test_tracking_documents.py` prints 0; `git log -1 --format=%s` ends `(WP-31 I2)`.]]></verify>
  <done>The package had a README, author and keyword lines and a complete help jump list, and I2 was closed in one commit.</done>
</task>

<task type="auto" id="59-03">
  <name>Write the failing setup and launcher tests</name>
  <files>test/test_setup_honesty.cscript, test/test_dependency_guards.py</files>
  <action><![CDATA[Append U59-2 and U59-3 to test/test_setup_honesty.cscript before its summary (its existing HON-nn form; U59-2 forces a failure after an install by pointing dash_setup at a scratch venv that lacks pip's network -- copy HON-40's setup -- and asserts the log holds `Installed by this run:` and `To undo:`; U59-3 asserts the `Unmet:` line holds no item printed under `Warnings:`). Add `TestTheChildInterpreter` (3) and `test_the_working_directory_is_not_on_the_import_path` to test/test_dependency_guards.py (the launcher tests monkeypatch `subprocess.Popen` as the file's existing launcher tests do; find them with `grep -n "_DASH_BOOT" test/test_dependency_guards.py test/test_serve*.py`; if the launcher's tests live elsewhere, put the class there and name that file in the commit). Run them and the cscript through the driver; write <scratch>/59-03-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[The four pytest nodes fail (`_dash_child_python` NameError; the import-path test finds `""` or the cwd in the probed path); the driver log holds `U59-2 FAIL` and `U59-3 FAIL`.]]></verify>
  <done>The setup-reporting, child-interpreter and import-path tests existed and failed on the unmodified tree.</done>
</task>

<task type="auto" id="59-04">
  <name>Fix setup reporting, child interpreter, import path</name>
  <files>dash_setup.ado, dash.ado, dash_render.py</files>
  <action><![CDATA[Apply D-59.d: (i)-(ii) in dash_setup.ado (`_dash_setup_summary` gains an `installed()` argument; every caller passes the local); (iii) dash.ado writes `python_exec` into the served spec and dash_render.py gains `_dash_child_python(spec)` used at :51842 (`_cmd = [_dash_child_python(spec), "-P", ...]`), added to test/function_test_map.py under a `# WP-31 S59` comment (a fourth file: list it in the commit); (iv) dash_setup_lib.py `VERIFY_CODE` and dash.ado `_dash_require_deps` prune `sys.path` (dash_setup_lib.py is a fifth file). Run `python3 -m pytest test/test_dependency_guards.py test/test_setup_pep668.py test/test_function_test_map.py test/test_server_build_options.py -q -p no:cacheprovider`; through the driver: test_setup_honesty.cscript, test_serve_launch.cscript, test_env_guards.cscript. Close the I3 entry (`Pinned by test/test_dependency_guards.py::TestTheChildInterpreter::test_the_spec_python_is_used, ::test_a_bad_path_falls_back_with_a_note, test/test_dependency_guards.py::test_the_working_directory_is_not_on_the_import_path, test/test_setup_honesty.cscript U59-2, U59-3. Residual, deferred (WP-31): hash-pinned installs need a per-platform lock file; not done (GAPS3 I3 Tracked)` -- the Tracked line takes the Partly form naming a new open BUGS.md entry `dash_setup installs by version, not by hash` graded S3 (WP-31)), delete the `"I3": "` key, replace `<!-- WP-31 I3 -->` with `- A failed dash_setup names the packages the run installed and the pip uninstall line that undoes it, and lists Unmet requirements apart from Warnings; dash serve starts its app with the Python Stata is linked to, falling back to the renderer's interpreter with a note; and a dash_setup_lib.py or bokeh.py in the working directory is no longer imported. (WP-31, I3)`; the I3 Tracked line (Partly form) ends `commit pending` (A11); commit.]]></action>
  <verify><![CDATA[All pytest runs 0 failed; the three driver logs end `ALL CHECKS PASSED` with `U59-2 PASS` and `U59-3 PASS`; `grep -c '_dash_child_python' dash_render.py` is at least 2; `grep -c '^    "I3": "' test/test_tracking_documents.py` prints 0; `grep -c 'dash_setup installs by version, not by hash' BUGS.md` prints 1.]]></verify>
  <done>dash_setup reported its installs, the served child was the linked interpreter, the working directory left the import path, and I3 was closed with its hash residual filed.</done>
</task>

<task type="auto" id="59-05">
  <name>Print the version note by hand; close I4</name>
  <files>dash_render.py, test/test_dependency_guards.py, BUGS.md</files>
  <action><![CDATA[Write `TestTheVersionNote`'s three tests first (TR-59.3), run them red, save <scratch>/59-05-failure.txt. Then apply D-59.e: factor the `__main__` body at dash_render.py:52121 into `_dash_main(argv)` (added to function_test_map.py) that prints `_dash_dep_versions()[1]` to stderr when non-empty before running; the app header gets the same two lines after its import guards; the remedy comment above `from __future__ import annotations` in both the module and the emitted header. Run `python3 -m pytest test/test_dependency_guards.py test/test_version_floor.py test/test_function_test_map.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" -q -p no:cacheprovider`. Close the I4 entry (`Pinned by test/test_dependency_guards.py::TestTheVersionNote::test_a_hand_run_renderer_prints_the_note, ::test_the_app_prints_the_note, ::test_the_future_line_carries_the_remedy_comment`), delete the `"I4": "` key, replace `<!-- WP-31 I4 -->` with `- python dash_render.py and a served app run by hand print the same numpy and pandas version note Stata prints, and the first line of each carries the comment that a SyntaxError there means a Python older than 3.11. (WP-31, I4)`; rewrite the I4 Tracked line to the Closed form with `commit pending` (A11); commit (GAPS3.md, CHANGELOG.md, tracking test further files).]]></action>
  <verify><![CDATA[The pytest runs report 0 failed; `grep -c 'def _dash_main' dash_render.py` prints 1; `grep -c 'a SyntaxError here means an older Python' dash_render.py` prints 2 (module and emitted header); `grep -c '^    "I4": "' test/test_tracking_documents.py` prints 0.]]></verify>
  <done>A hand-run renderer or app printed the version note, the remedy comment headed both files, and I4 was closed.</done>
</task>

<task type="auto" id="59-06">
  <name>Renumber the headers and pin them; close I5</name>
  <files>dash_render.py, dash.ado, dash_parse.mata</files>
  <action><![CDATA[Write `test_every_header_states_the_declared_version` and `VERSION_SOURCES["dash_render.py"]` in test/test_pkg_metadata.py first (TR-59.4), run red, save <scratch>/59-06-failure.txt. Then D-59.f's edits (dash_render.py:60; dash.ado:1, :5, :13, :6638 region -- `grep -n 'v2\.0' dash.ado` for every occurrence; dash_parse.mata:1). Run `python3 -m pytest test/test_pkg_metadata.py test/test_version_floor.py -q -p no:cacheprovider`. Close the I5 entry (`Pinned by test/test_pkg_metadata.py::test_every_header_states_the_declared_version, test/test_pkg_metadata.py::test_every_file_declares_the_same_version`), delete the `"I5": "` key, replace `<!-- WP-31 I5 -->` with `- Every version header reads 0.1.0: dash_render.py said 1.0.0 25mar2026 and dash.ado and dash_parse.mata said v2.0; test_pkg_metadata.py pins the renderer's Version line and the v-headers with the six Version lines. (WP-31, I5)`; rewrite the I5 Tracked line to the Closed form with `commit pending` (A11); commit.]]></action>
  <verify><![CDATA[`grep -c 'v2\.0' dash.ado dash_parse.mata` prints 0 for each; `grep -c '^Version: 0.1.0' dash_render.py` prints 1; the pytest run reports 0 failed; `grep -c '^    "I5": "' test/test_tracking_documents.py` prints 0.]]></verify>
  <done>Every header agreed on 0.1.0 and the metadata pin covered all of them; I5 was closed.</done>
</task>

<task type="auto" id="59-07">
  <name>Write the failing bytecode tests</name>
  <files>test/test_installed_layout.py, test/test_setup_honesty.cscript</files>
  <action><![CDATA[Add `TestNoBytecodeIsWritten::test_a_render_from_the_install_leaves_no_pycache` (copy the scratch-install helper the file's `TestAnInstalledTreeResolvesItsOwnSchemes` uses; import the renderer from the scratch PLUS/py through the same `spec_from_file_location` + `exec_module` dash.ado uses, in a subprocess `python3 -I -c` with `sys.dont_write_bytecode = False`, then assert `not os.path.isdir(os.path.join(plus_py, "__pycache__"))`) and U59-1 to test_setup_honesty.cscript (after a `dash scatter mpg weight` with the renderer loaded from an installed scratch PLUS: `capture confirm file "<plus>/py/__pycache__/."` fails; copy the installed-tree setup from HON-40). Run both red; write <scratch>/59-07-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[The pytest node fails with `__pycache__` present; the driver log holds `U59-1 FAIL`.]]></verify>
  <done>The bytecode tests existed and failed on the unmodified loader.</done>
</task>

<task type="auto" id="59-08">
  <name>Guard the renderer load; close I7</name>
  <files>dash.ado, BUGS.md, GAPS3.md</files>
  <action><![CDATA[Apply D-59.g at dash.ado:6118-6133 (the save line before the first `python:` of the load, the restore line after `sys.modules[...] = _dash_xm` and before the `exit 198` inside the failure branch). Run `python3 -m pytest test/test_installed_layout.py test/test_dependency_guards.py -q -p no:cacheprovider`; through the driver: test_setup_honesty.cscript and test_env_guards.cscript. Close the I7 entry (`Pinned by test/test_installed_layout.py::TestNoBytecodeIsWritten::test_a_render_from_the_install_leaves_no_pycache, test/test_setup_honesty.cscript U59-1`), delete the `"I7": "` key, replace `<!-- WP-31 I7 -->` with `- Loading the renderer no longer writes dash_render's bytecode under PLUS/py, so ado uninstall leaves no __pycache__ behind; the dash_setup_lib load was already guarded. (WP-31, I7)`; rewrite the I7 Tracked line to the Closed form with `commit pending` (A11); commit (CHANGELOG.md, the tracking test and the two test files are further files).]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; both driver logs end `ALL CHECKS PASSED` with `U59-1 PASS`; `grep -c 'dont_write_bytecode' dash.ado` prints 4 (two saves, two restores); `grep -c '^    "I7": "' test/test_tracking_documents.py` prints 0; `git log -5 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The renderer loaded without writing bytecode, the install stayed clean, and I7 was closed.</done>
</task>

## Section completion criteria

- Five commits on `wp31-s59` ending `(WP-31 I2)`, `(WP-31 I3)`, `(WP-31 I4)`, `(WP-31 I5)`, `(WP-31 I7)`; no test-only commit; no tool names.
- README.md, dash.pkg lines, help sections; setup reporting; child interpreter; version note; headers 0.1.0; no bytecode -- each pinned as named.
- I2, I4, I5, I7 Tracked Closed; I3 Partly with the hash residual entry open.

## Notes

- **R6:** `version 19` in any new program; `_dash_require_deps`' `_needed` list untouched (no Mata function added).
- **R2:** `_dash_child_python` is parent-side launcher code, not copied into the app; no copy-list entry. `_dash_main` likewise.
- **R10:** no counts move.
- **Trap:** dash.sthlp's `{title:Also see}` is read by `test_help_claims_*`; the split keeps the `{psee}` lines verbatim.
- **Trap:** the served spec is written by dash.ado and read by the generated app too; `python_exec` is read only by the parent launcher (the app ignores unknown keys -- verify with `grep -n 'spec\[' dash_render.py | grep -c strict` → 0).
- **Trap:** S61 bumps every date after I5; S59 writes `09oct2026` in the renderer's new Version line so the pin is green now.
- **Tracked lines (A11):** the five closing tasks write `commit pending`; no amend anywhere. **A14:** no truth block. **Files (A13):** `<files>` lists primary files; the tracking documents, the `WP31_OPEN` key deletions and flipped tests are implied.
- **Decisions for maintainer ratification:** (1) hash-pinned installs deferred (D-59.d); (2) the `net install` URL (D-59.a); (3) no `d Support:` email line (D-59.b).
