# Section 25: Render-time dependency guards (P1.32)

> Part of: WP-30 · Items: P1.32 (entry `P1.32`) · Risk: yellow · Batch: 9 · Depends on: 03, 05 · Blocks: 41, 46 · Tasks: 12, 1 commit · Case prefixes: RG; ENV-30..39, HON-40..49

## Review amendments

- Fixed (major, rule 1): TR-25.8 tested `_dd_err`, `_dd_refuse` and `_dd_note` with `` if `"`_dd_err'"' != "" ``, expanding import-exception and version text from the environment into a Stata expression (a `'"` in it ends the string; the rest is parsed as expression code). Each is now tested by `: length local` and shown only through `_dash_say`/`_dash_note`; `test_the_loader_and_the_render_run_the_guard_first` pins that no line of `_dash_xm_load` expands them.
- Fixed (minor): `_old(ver)` set `sys.version_info` to a plain tuple, which breaks any stdlib import that reads `.major`; it is now a namedtuple of the five fields.
- Fixed (minor): TR-25.3 now says where a non-bokeh line an earlier section added among the header's bokeh lines goes (above the guard, unchanged, recorded).
- Checked at `c96facd`: dash_render.py:61/:82-118, `_generate_app_source` :33915 and header :34025-34110, dash.ado :84-92, :189-215, `_dash_xm_load` :4576-4610 (exec_module :4606), `_dash_tmp_clear` :4724-4735, dash_setup.ado :92 and :924-928, `_DASH_ADO_ENTRY_POINTS` :2553: all as quoted. `_env_is_cmd` counts `capture python:` as a python site, so ENV-12's flip (gains `_dash_require_deps`) and ENV-30 hold; `_import_probes` reads cscripts only, so the guard's captured import lines in dash.ado move no pin; the copied dash_setup loader lines pass `test_every_new_python_line_is_an_assignment_or_a_setlocal` (prefix match on `import`). No top-level `Try` holds an import at HEAD, so the AST pin's handler rule is satisfiable.
- Checked: batch 9 partners. S25 is the batch's only `_generate_app_source` editor (R12); S26 (`map_function`, its copy-list helper) and S27 (finishers, auto bases) share no function with S25; dash.ado programs edited here (`dash`, `_dash_require_python`, `_dash_do_render`, `_dash_xm_load`, `_dash_tmp_clear`, new `_dash_pyfloor`/`_dash_require_deps`) are edited by neither.
- Checked: tracking forms. Title, `WP30_OPEN["P1.32"]`, the Requirements marker, the stub header text and the commit subject match section-01 Appendix B and TR-01.10; 30 regression nodes counted (21 + 4 + 5).
- Rejected: refusing registration without Python is a behaviour change, not a defect: register P1.32.3 and BR-07.1 require it, CHANGELOG Requirements states it, and `dash clear` is spared (ENV-37, ENV-39).
- (cross-file pass) 25-12 verify: added the key-deletion check `grep -c '^    "P1.32": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:166 (P1.32) reads: "A missing numpy, pandas or bokeh gives a bare ModuleNotFoundError. An old Python gives a SyntaxError. `dash_setup`'s first Python call is uncaptured." GAPS2.md:1537-1543 (H6) adds that `_dash_python_ok` checks only that `c(python_exec)` is non-empty, so ROADMAP BR-07.1 ("Every external dependency is verified before use, with a message naming the remedy", ROADMAP.md:703) is unmet for the packages and the version. The four sub-claims, as the research note names them (`.ultraplan/wp30/research/p1-32.md` §1-2), were all re-measured open at `c96facd`:

- **H6a.** With numpy blocked, `dash scatter mpg weight, saving(m1.html)` stops with a traceback ending `File ".../dash_render.py", line 82 ... ModuleNotFoundError: No module named 'numpy'` and `RC=7102`; `dash build, server` the same (pandas at :83, bokeh at :88, both routes). No line names `dash_setup` or the interpreter. `dash serve` with a child that lacks pandas prints `dash serve: no server started on port 5987: the app exited with status 1?Traceback ... line 26 ... ModuleNotFoundError: No module named 'pandas'?` (r(198), a traceback tail, no remedy).
- **H6b.** A hand run under `/usr/local/bin/python3.6` stops at `dash_render.py:61` with `SyntaxError: future feature annotations is not defined`; under 3.7 at :88 with `ModuleNotFoundError: No module named 'bokeh'`; under 3.10 at :83 (measured again 03oct2026, see Evidence E11). No line names the floor.
- **H6c.** `dash_setup.ado:92` is an uncaptured `python:` line. With `sys.modules["sfi"] = None` the run prints `ModuleNotFoundError: import of sfi halted; None in sys.modules` and stops, `RC_A=7102`, before its summary: no "dash_setup did not complete", no `Unmet:`, no remedy.
- **H6d.** `_dash_python_ok` (dash.ado:189-194) returns `ok = (strtrim(probe) != "")`; nothing checks the version or the packages before Python runs.

**What will be true after.** Every `dash` command but `dash clear` runs one dependency guard, `_dash_require_deps`, right after the Mata guard (A154). It starts the linked Python (a first call that fails is tried once more) and reads its version and the packages' presence as values. A Python that cannot start, a Python below the floor, or a missing numpy, pandas or bokeh ends the command with r(198) and one message naming what is wrong, `c(python_exec)` and `dash_setup`, before anything is written or announced. A package that is present but will not import is caught where the renderer loads (`_dash_xm_load`), by value, with the renderer's own one-line reason. The renderer and the served app's header check the floor and import numpy, pandas and bokeh inside guards that stop in that same one line: an ImportError under Stata or `bokeh serve`, and a SystemExit with exit status 1 when run as a program (`python dash_render.py`, `python app.py`, `dash serve`'s child). A Python too old to parse the file (before 3.7) is shown the remedy on the `from __future__` line it stops at. numpy or pandas below `dash_setup`'s minimum is named in one note per load, and the command goes on (A121). `dash clear` still clears the registry with no Python at all, and prunes dash's temporary files with the packages missing, through a standard-library slice of the renderer's own pruning code (A122). `dash_setup` captures its first Python call, retries it once, and reports a Python that cannot start in its summary, with its path and, on a Mac, the processor rule. One floor number is held by `_dash_pymin` (dash_setup.ado), `_dash_pyfloor` (dash.ado), `_DASH_MIN_PYTHON` (dash_render.py) and the generated app, pinned equal (A123).

**Why one section.** The four sub-claims are one defect, "a missing dependency surfaces as an internal error", at the four places Python first runs: dash.ado's entry, the renderer's import block, the generated app's header and `dash_setup`'s first call. They share one message form, one floor constant and one set of blocking helpers in the tests. Splitting them would leave a commit where the Stata guard passes a package the renderer then fails on with a traceback.

**Test order and commit rule.** Task 25-01 writes every pytest regression test, runs it on the unmodified batch-9 base and saves the failure text to `<scratch>/25-P1.32-failure.txt`; 25-02 and 25-03 add the cscript cases and append their measured base values to the same file. Nothing is committed until 25-12. The fixes (25-04 to 25-09) turn the tests green; the three pinned tests that assert today's state are flipped in place, with a `Flipped:` line, never deleted. The section makes one commit, closing entry `P1.32`, after one full run through the queue (index E1).

## Risk: [yellow] — the guard becomes the first Python call of every dash command, and the served template's header is rewritten

**Why yellow.** The changes are additive and the healthy path draws the same pages, but they sit on every route: `dash`'s entry, `_dash_xm_load` (8 callers), the renderer's module import (191 test files import it) and `ServerAppBuilder._generate_app_source` (GitNexus HIGH: impactedCount 5, 3 processes, measured at `c96facd`).

**Risk factors.**
1. Registration (`dash scatter …, name(g1)`) ran no Python before; it now runs two captured `python:` lines and is refused when Python or a package is missing. A do-file that registered graphs on a machine without Python now stops at the first registration.
2. A test that blocks a package in Stata's Python and then runs `dash` now gets r(198) at entry. Measured at `c96facd`: the only cscripts that block bokeh, numpy or pandas (`test_program_coverage.cscript` PC sandboxes, `test_setup_honesty.cscript` HON-27) run `dash_setup`, never `dash`, while blocked.
3. The renderer cached in `sys.modules["_dash_render_export"]` hides a missing package from `_dash_xm_load` for the rest of the session: a test that blocks a package must take the cached renderer out too, or it measures nothing.
4. A `SystemExit` raised under Stata's `python:` ends the line with rc 0 (RG-01): a guard that raised SystemExit inside Stata would let the command go on.
5. The prune slice compiles definitions from dash_render.py by name; a later edit that makes a pruning helper read a name bound by a guarded package import would make the slice refuse, and `dash clear` would stop pruning.
6. The floor number is S05's measured value; if S05 declared 3.12 or 3.13 (PLAN K15), every literal below reads that value.
7. Ratification item 24 (A121, the numpy/pandas note) is pending at writing.

**Mitigation.**
1. CHANGELOG Requirements states the registration refusal; `dash clear` is exempt and pinned so (ENV-37, ENV-39).
2. Every ENV and HON case restores Python's state before it asserts (the ENV-17..19 form), through `test/dep_block.py`, which returns `rg_clean`.
3. `dep_block.block` always takes `_dash_render_export` out and `restore` puts the same object back.
4. `_dash_dep_fail` raises ImportError whenever `sfi` is loaded, and writes its line to the caller's local `_dd_err`, so Stata decides from the value (RG-03).
5. `test_every_unguarded_top_level_import_is_the_standard_library` holds the file layout the slice relies on, and `test_the_slice_prunes_as_the_renderer_does` fails if the slice stops pruning.
6. Task 25-04 reads `_dash_pymin` at the base and writes that number everywhere; `TestThePythonFloorIsOneNumber` pins the agreement.
7. If item 24 is struck, the orchestrator re-plans TR-25.2 before `batch-9-base.txt` is recorded (index "Decisions for maintainer ratification").

## Dependencies

- **Depends on: 03, 05.**
  - **S03** (batch 1): `_dash_require_stata` and `version 19` open `dash`; `_dash_require_mata` follows; every new program declares `version 19`; ENV-24..29 sit at the end of `test_env_guards.cscript`; `TestTheStataFloor` in `test/test_version_floor.py`. S03 inserted `_dash_stata_ok` and `_dash_require_stata` after `_dash_require_python`'s `end`.
  - **S05** (batch 2): `_dash_pymin` holds the measured floor (`<FLOOR>`, 3.11 expected); `_dash_require_python`'s message holds the literal `Python <FLOOR>+`, which this section replaces with its constant (A123); HON-31/32 end `test_setup_honesty.cscript`'s HON run; `TestTheFloorAdmitsTheServedLauncher` stays the pin of the `-P` flag.
  - Earlier batches this section lands on (not edited here): S06's note channel (`mata: _dash_note(...)`, `_dash_emit_note`; A150), S12's prefix strip after the Mata guard, S22's rclass dispatch, S23's relay of the served child's stderr and its build-time trial.
- **Blocks: 41, 46.** S41 adds bokeh's version window as the tail of this guard (`_dash_dep_versions`' refusal slot and the app-start check). S46 verifies its session APIs on a header S41 has finished.
- **Parallel batch: 9**, merge order S25, S26, S27.
- **Can run with:** S26 and S27. They edit no program or function this section edits (Boundaries).

## Evidence

All anchors are at `c96facd` (HEAD of `wp30-p1` when this was written). Earlier batches move them: find each by its quoted text at the batch-9 base.

**E1. The renderer's import block is unguarded** (dash_render.py:61, :82-90, :117-118).

```python
61  from __future__ import annotations
...
82  import numpy as np
83  import pandas as pd
84
85  # ---------------------------------------------------------------------------
86  # Bokeh imports — grouped by sub-module for clarity
87  # ---------------------------------------------------------------------------
88  from bokeh.embed import components, file_html
89  from bokeh.layouts import column, gridplot, row
90  from bokeh.models import (
...
117 from bokeh.plotting import figure as bokeh_figure
118 from bokeh.resources import CDN, INLINE  # noqa: F401 — CDN kept for server mode
```

The stdlib imports are :63-80 (`argparse` … `from typing import Any`); `sys` is not imported at module level. An AST scan of the top level (Evidence E11) finds exactly these seven package imports (lines 82, 83, 88, 89, 90, 117, 118) and no other non-stdlib import. The module docstring's "Dependencies" (:48-52) still says `bokeh >= 3.0`, `numpy >= 1.23`, `pandas >= 1.5`.

**E2. The generated app's header is unguarded** (`ServerAppBuilder._generate_app_source`, dash_render.py:33915; header list :34025-34110).

```python
34037            "from __future__ import annotations",
...
34058            "from typing import Any, Callable, Iterable, List",
34059            "import numpy as np",
34060            "import warnings",
34061            "import pandas as pd",
...
34069            "from bokeh.application import Application",
...
34103            "from bokeh.server.server import Server",
34104            "import collections as _collections",
34105            "import time as _time",
34106            "from tornado.web import RequestHandler as _RequestHandler",
34107            "# The CSV download's button and its page-side writer (WP-21).",
34108            "from bokeh.models import Button as _DashButton, CustomJS as _DashCustomJS",
```

In a built sample app the non-stdlib top-level imports are lines 24 (numpy), 26 (pandas), 34-37, 66-68 and 73 (bokeh) and 71 (tornado), nothing else (measured, E11). The child runs it as `__main__` (`_DASH_BOOT`, dash_render.py:36945-36994: `mod = types.ModuleType('__main__')`). The copy loop of `_glyph_layer_lines` writes a function with `_textwrap.dedent(_inspect.getsource(_fn)).rstrip("\n").split("\n")` (:33431-33432).

**E3. dash's entry** (dash.ado:84-92 at `c96facd`; S03 later puts `_dash_require_stata` first and `version 19` second, S12 its strip after `_dash_require_mata`, S22 its dispatch after the strip).

```stata
84  program define dash
85      version 16.0
86
87      // Every subcommand parses through Mata, so this is the one place that
...
92      _dash_require_mata
```

The routing reads the subcommand with `mata: st_local("_subcmd", ustrregexm(st_local("0"), "^[a-zA-Z][a-zA-Z0-9_]*") ? ustrregexs(0) : "")` (:115-116) and sends `clear` to `_dash_clear` (:128-131).

**E4. The Python guard checks configuration only** (dash.ado:189-194, :206-215).

```stata
189 program define _dash_python_ok, rclass
190     version 16.0
191     args probe
192     local probe = strtrim(`"`probe'"')
193     return scalar ok = cond(`"`probe'"' == "", 0, 1)
194 end
...
206 program define _dash_require_python
207     version 16.0
208     _dash_python_ok `"`c(python_exec)'"'
209     if r(ok) != 1 {
210         display as error "dash: Python is required but is not available to Stata."
211         display as error "      Run {cmd:dash_setup} first, or link Stata to " ///
212             "Python 3.13+: {help python}"
213         exit 198
```

(S05 changes `3.13` to `<FLOOR>` in :212.) It is called first in 11 programs (`grep -c '^\s*_dash_require_python\s*$' dash.ado` = 11).

**E5. The renderer load is uncaptured** (`_dash_xm_load`, dash.ado:4576-4610).

```stata
4576 program define _dash_xm_load
4577     version 16.0
4578     _dash_require_python
...
4593     python: import sys, os, importlib.util
4594     python: from sfi import Macro as _dash_M
...
4603     python: _dash_ok = _dash_xm is not None and getattr(_dash_xm, "_dash_export_key", None) == _dash_key
4604     python: _dash_xs = None if _dash_ok else importlib.util.spec_from_file_location("_dash_render_export", _dash_rp)
4605     python: _dash_xm = _dash_xm if _dash_ok else importlib.util.module_from_spec(_dash_xs)
4606     python: _dash_xr = _dash_ok or _dash_xs.loader.exec_module(_dash_xm)
4607     python: _dash_xm._dash_export_key = _dash_key
4608     python: sys.modules["_dash_render_export"] = _dash_xm
```

Its 8 callers (`grep -c '^\s*_dash_xm_load\s*$' dash.ado` = 8): `_dash_empty_data`, `_dash_write_data`, `_dash_tmp_open`, `_dash_tmp_preview`, `_dash_tmp_close`, `_dash_tmp_clear`, `_dash_render_immediate`, `_dash_prepare_spec`. `_dash_do_render` (:402) runs `runpy.run_path` after `_dash_require_python` (:413) and is reached after a load; `_dash_serve` reaches the load through `_dash_tmp_open`.

**E6. dash clear prunes through the renderer** (dash.ado:4724-4735, :6880-6885).

```stata
4724 program define _dash_tmp_clear
4725     version 16.0
4726     _dash_require_python
4727     mata: st_local("_tcl_has", strofreal(rows(dir(c("tmpdir"), "dirs", "dash*")) > 0))
4728     if "`_tcl_has'" != "1" exit
4729     _dash_xm_load
...
4734     python: _dash_tcl = _dash_xm._dash_tmp_clear(_dash_M.getLocal("_tcl_tmp"))
...
6883     capture _dash_tmp_clear
6885     display as text "dash: registry cleared."
```

With a package missing, the load fails inside `capture`: the registry is cleared and nothing is pruned. The renderer's `_dash_tmp_clear` (dash_render.py:2510-2543) and every definition it reaches are standard-library code: an AST closure from `_dash_tmp_clear` reaches 18 top-level names (`_DASH_ERRNO_WHY`, `_DASH_FALLBACK_FMT`, `_DASH_PREVIEW_CEILING`, `_DASH_PREVIEW_GRACE_S`, `_DASH_PREVIEW_KEEP`, `_DASH_PREVIEW_RE`, `_DASH_RUN_RE`, `_DASH_STALE_AGE_S`, `_DASH_WRITE_REFUSAL`, `_DashUnsafePath`, `_dash_own_root`, `_dash_pid_alive`, `_dash_private_dir_ok`, `_dash_private_msg`, `_dash_prune_previews`, `_dash_root_name`, `_dash_run_sweep`, `_dash_tmp_clear`), 292 lines between :1803 and :2543, none of them a package name.

**E7. The ado entry points** (dash_render.py:2546-2555).

```python
#: The functions dash.ado calls by name on this module, loaded as
#: ``_dash_render_export`` ... Named here so the call graph of the dead-code audit
#: (scripts/fncov/fncov_reach.py), whose roots are this module's own code,
#: counts them as run; test_string_value_export.py holds this tuple and
#: dash.ado's calls to the same names.
_DASH_ADO_ENTRY_POINTS = (_dash_write_stata_data, _dash_run_open,
                          _dash_run_close, _dash_preview_path,
                          _dash_tmp_write_text, _dash_tmp_clear)
```

**E8. dash_setup's first Python call** (dash_setup.ado:84-92, the summary :672-689, the lib loader :924-928).

```stata
92      python: import sys; from sfi import Macro; Macro.setLocal("pyver", sys.version.split()[0])
93      _dash_pyver_ok "`pyver'" "`c_pymin'"
...
672 program define _dash_setup_summary
...
678     if `failures' > 0 {
679         display as error "dash_setup did not complete: `failures' unmet " ///
680             "requirement(s)."
681         if `"`items'"' != "" {
682             display as error "  Unmet: `items'"
...
689         exit 198
...
924     mata: st_local("lib", pathresolve(pwd(), st_local("lib")))
925     python: import sys, sfi; sfi.Macro.setLocal("_dwb", "1" if sys.dont_write_bytecode else "0"); sys.dont_write_bytecode = True
926     capture python: import importlib.util as _dsl_iu, sys, sfi; _dsl_p = sfi.Macro.getLocal("lib"); ... sys.modules["_dash_setup_lib"] = _dsl_m
927     local _lrc = _rc
928     python: import sys, sfi; sys.dont_write_bytecode = sfi.Macro.getLocal("_dwb") == "1"
```

The minimums are `local min_bokeh "3.8"`, `min_numpy "2.3"`, `min_pandas "2.3"` (:48-50); dash.pkg:17 reads `Requires: Python 3.13+, bokeh>=3.8, numpy>=2.3, pandas>=2.3.` dash_setup.ado displays no path anywhere today (`grep -n python_exec dash_setup.ado`: :5, :74, :589, all configuration checks or comments).

**E9. dash_setup_lib.py** is "Stdlib only; parses as Python 3.8; nothing runs at import" (:1-3), loaded by dash_setup.ado's `_dash_setup_lib` (:901) as `sys.modules["_dash_setup_lib"]`; every function it defines is a key of `test/function_test_map.py` `SETUP_FUNCTIONS` (`test_every_dash_setup_lib_function_names_its_test`).

**E10. The rules the new lines must keep** (read at `c96facd`):
- `test/test_private_files.py::TestTheAdoUsesThePrivateDir::test_each_python_program_calls_dash_require_python_first` (:1995): in any program with a line starting `python:`, a line `_dash_require_python` comes first.
- `::test_every_new_python_line_is_an_assignment_or_a_setlocal` (:1980) and `::test_python_reads_paths_by_value` (:1967): the `python:` lines of `_dash_xm_load` and the `_dash_tmp_*` programs are imports, assignments or `_dash_*M.setLocal(` calls, with no backtick or `$`.
- `::test_dash_clear_prunes_through_a_captured_call` (:2018): `capture _dash_tmp_clear` precedes "registry cleared".
- `test/test_cscript_hygiene.py::TestTheShippedAdoFilesFollowTheSameRule` (:434-560): no `capture python query`, no bare `python: pass` warm-up deciding availability, `c(python_exec)` read, no macro inside a Python string literal on a `python:` line (allowlist `_ALLOWED_INLINE_PY_MACROS`, :53-67).
- `test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_import_probes_are_found` (:315-322): `len(with_probes) == 13`, the cscripts holding a `capture python:` line with `import` in it.
- `test/test_env_guards.cscript` ENV-12 (:518-550): the exact list `"_dash_do_render _dash_empty_data _dash_write_data _dash_xm_load _dash_tmp_open _dash_tmp_preview _dash_tmp_close _dash_tmp_clear _dash_render_immediate _dash_prepare_spec _dash_serve"` of programs holding a `python:` line, each with `_dash_require_python` before its first; ENV-13 (:552-565) the Mata guard before every route; ENV-16 (:568-603) counts captured `python query` and captured `python:` with nothing or `pass` and wants 0 in both ado files.
- `test/test_security_surface.py::TestUserTextIsEchoedAsText` (:1099): no `display` in dash.ado expands user text; echoes go through Mata `_dash_say` (dash_parse.mata:676-680, which turns `{`, `}` and control characters into SMCL-safe text).

**E11. Measurements for this section** (03oct2026, StataNow 19.5 through `scripts/stata_slot.sh`; scratch `<scratch>/s25/`).
- `p25a.do`:
  ```
  Q1 asis:
    path: {bf:B}{stata exit}                       <- display as error "  path: " _asis "{bf:B}{stata exit}"
  Q2 machine_type=[Mac (Apple Silicon)] os=[Unix] pyexec=[/opt/anaconda3/bin/pyth...
  Q3 rc=0 _dd_v=[3.13.9]                          <- capture python: import sys; from sfi import Macro as _dash_M; _dash_M.setLocal("_dd_v", "%d.%d.%d" % tuple(sys.version_info[:3]))
  Q4 rc=7102 _dd_err=[dash: could not import numpy (test)]   <- a module run by exec_module inside a program sets that program's local, then raises
  Q5 numpy=2.3.5 pandas=2.3.3 bokeh=3.8.0 nosuchpkg=
  SystemExit: x / Q6 SystemExit rc=0              <- capture noisily python: raise SystemExit("x")
  Q7 blocked-reads-missing=True                   <- sys.modules[m] = None, then sys.modules.get(m) is None and find_spec(m) is None
  ```
  `c(os)` is `Unix` on this Mac, so a Mac is recognised from `c(machine_type)`, never from `c(os)`.
- `p25b.do`: `mata: display("  asis: {bf:B}" + char(34) + char(39) + "{stata exit}", 1)` printed `  asis: {bf:B}"'{stata exit}`. The two guard lines (version, then presence) as a program: first call 0.068 s, 1,000 repeats 0.274 s (0.27 ms each).
- Old interpreters on this Mac (`/usr/local/bin/python3.N -B dash_render.py --spec s.json --data d.json --output o.html`): 3.6 `SyntaxError: future feature annotations is not defined` at `from __future__ import annotations`; 3.7 `line 88 ... ModuleNotFoundError: No module named 'bokeh'`; 3.9 `ImportError: Error importing numpy: you should not try to import numpy from its source directory`; 3.10 `line 83 ... ModuleNotFoundError: No module named 'pandas'`.
- `ast.parse(..., feature_version=(3, 7))` succeeds for dash_render.py and for `scripts/fncov/fncov_report.sample_app_source()` (26,144 lines), so Pythons 3.7-3.10 reach a guard placed after the stdlib imports.
- A prototype of the slice (`slice_proto.py`, under `python3.11` with numpy, pandas, bokeh, tornado and jinja2 set to None in `sys.modules`) compiled the 18 names in 0.196 s, removed a `run-999999-abc` folder of a dead pid from `dash-<uid>`, and left `sys.modules["numpy"]` None.

**E12. Pinned tests this section changes** (flipped in place, never deleted).
- `test/test_version_floor.py::TestTheFloorIsTheTestedBaseline::test_every_declaration_agrees_with_dash_setup`: the assertion `assert ("Python %s+" % py) in ado, ado` (:76 at `c96facd`). After this section dash.ado writes the floor once, as `return local pyfloor "<FLOOR>"`, and the message reads it.
- `test/test_string_value_export.py::TestDashAdoUsesTheWriter::test_every_entry_point_is_called_by_the_ado_and_no_other` (:550-559): it reads only `_dash_xm\.(_dash_\w+)\(` calls and expects exactly six names. dash clear now reaches `_dash_tmp_clear` through `stdlib_entry(..., "_dash_tmp_clear")`, and `_dash_dep_versions` joins the tuple.
- `test/test_env_guards.cscript` ENV-12's list literal (:544): `_dash_require_deps` runs Python and joins it, first in file order.

## User stories

- **US-25.1** As an installer whose numpy, pandas or bokeh is missing or broken, I want the first `dash` command to stop with one message naming the package, the Python it looked in and `dash_setup`, before it writes anything, so that I know what to run instead of reading a Python traceback.
- **US-25.2** As an installer with an old Python linked to Stata, I want `dash` to tell me my version and the oldest one it runs under, so that I link the right Python.
- **US-25.3** As an installer on Apple Silicon whose linked Python is built for Intel, I want `dash` and `dash_setup` to say that Python could not be started and that Stata and Python must be built for the same processor, so that I do not reinstall packages that were never the problem.
- **US-25.4** As a dashboard publisher who runs a generated `app.py` on another machine, or lets `dash serve` start it, I want a missing package or an old Python to stop the app with one line naming `dash_setup`, so that the server log says what to fix.
- **US-25.5** As a twoway user whose packages broke, I want `dash clear` to clear the registry and prune dash's temporary files anyway, so that I can clean up before repairing.
- **US-25.6** As an installer with numpy or pandas older than `dash_setup` installs, I want a note rather than a refusal, so that a dashboard that renders is not blocked.
- **US-25.7** As the maintainer, I want one floor number held by every file that states it, and a test that fails if a package import is added outside a guard, so that the guard cannot drift.

## Business requirements

- **BR-25.1** A missing numpy, pandas or bokeh ends every `dash` command but `dash clear` with r(198) and one message that names the package, the linked Python (`c(python_exec)`) and `dash_setup`: the one-line form with `saving()`, a registration, `dash build`, `dash build, server` and `dash serve`. No page or app is written, no server is announced and no traceback is shown.
- **BR-25.2** A package that is installed but fails to import (a missing dependency of its own, an extension built for another Python or processor) is refused the same way, and the message carries the import error's own text.
- **BR-25.3** A Python below the floor is refused with r(198), naming its version, the floor and `dash_setup`, before any package is imported.
- **BR-25.4** A linked Python that cannot be started is refused with r(198), naming `c(python_exec)` and `dash_setup`, and on a Mac the rule that Stata and Python must be built for the same processor. A first start that fails is tried once more before that.
- **BR-25.5** The generated app (`dash serve`'s child, `python app.py`, `bokeh serve`) and the renderer run by hand stop with the same one line naming `dash_setup` when a package is missing or broken or Python is below the floor: exit status 1 as a program, an ImportError under `bokeh serve`. `dash serve` then ends r(198) with that line, not a traceback.
- **BR-25.6** A Python too old to read the file (before 3.7) is shown the floor and the remedy on the line where it stops.
- **BR-25.7** numpy or pandas below `dash_setup`'s minimum is named in one note per load of the renderer, and the command goes on [R24].
- **BR-25.8** `dash clear` needs no Python to clear the registry, and prunes dash's temporary files with numpy, pandas and bokeh missing, with the same safety checks as before (own root, no link followed).
- **BR-25.9** `dash_setup`'s first Python call is captured and retried once; a Python that still cannot start is counted as unmet and reported in the summary, with its path shown as typed and the processor rule on a Mac, r(198), before any process starts.
- **BR-25.10** The floor is one number: `dash_setup`, `dash`, the renderer, the generated app and both help files state the same.
- **BR-25.11** With every dependency present nothing a user sees changes except the new checks: pages, served documents and filter moves draw as before. The checks cost at most 0.1 s on a session's first command and under 1 ms after.
- **BR-25.12** Text from the environment (paths, version strings, exception text) reaches Stata's display escaped and bounded; nothing is run through a shell; only dash's own shipped file is compiled.

## Technical requirements

Throughout, `<FLOOR>` is the value `_dash_pymin` returns at the batch-9 base (S05's measured floor, "3.11" expected) and `(<FMAJ>, <FMIN>)` its two parts as integers. Task 25-04 reads it once and writes it everywhere below.

**TR-25.1 The renderer's import guard (dash_render.py, module top).**
- :61 becomes `from __future__ import annotations  # dash needs Python <FLOOR> or later: link a newer Python, then run dash_setup`. It stays the first statement after the docstring.
- The docstring's "Dependencies" lines (:48-52) become: `Python <FLOOR> or later; bokeh >= 3.8, numpy >= 2.3, pandas >= 2.3 (dash_setup's minimums), each import checked by _dash_dep_fail.`
- After `from typing import Any` (:80) and before :82, add a `#:` comment block and `_DASH_MIN_PYTHON = (<FMAJ>, <FMIN>)`, then `_dash_dep_fail`, then the guards.
- **`_dash_dep_fail(what, err=None)`** (new). The docstring states the four contexts and the rule "written for Python 3.7; nothing here may need a newer one". Body, in this order:
  1. `import sys`; `exe = str(sys.executable or "python")[:300]`.
  2. `what == "python"`: `msg = "dash: Python %s at %s is older than dash needs (Python %d.%d or later); link a newer Python to Stata, then run dash_setup" % ((".".join(str(p) for p in tuple(sys.version_info)[:3]), exe) + tuple(_DASH_MIN_PYTHON))`.
  3. Otherwise: `why = ("%s: %s" % (type(err).__name__, err))[:300] if err is not None else "not found"`; `msg = "dash: could not import %s for the Python at %s (%s); run dash_setup" % (what, exe, why)`.
  4. `msg = " ".join(msg.split())` (one line, whatever the exception text holds).
  5. `sfi = sys.modules.get("sfi")`; if not None, `sfi.Macro.setLocal("_dd_err", msg)` inside `try/except Exception: pass`.
  6. `exc = SystemExit(msg) if (__name__ == "__main__" and sfi is None) else ImportError(msg)`; `exc.__suppress_context__ = True`; `raise exc`.
  Why: under Stata a SystemExit ends a `python:` line with rc 0 (RG-01), so inside Stata it is always an ImportError plus the value; imported as a module (`bokeh serve`, a test) an ImportError is the honest answer; run as a program the line alone on stderr and exit status 1.
- The guards, after `_dash_dep_fail`:
  ```python
  if tuple(__import__("sys").version_info[:2]) < _DASH_MIN_PYTHON:
      _dash_dep_fail("python")

  try:
      import numpy as np
  except Exception as _dash_e:
      _dash_dep_fail("numpy", _dash_e)
  try:
      import pandas as pd
  except Exception as _dash_e:
      _dash_dep_fail("pandas", _dash_e)

  # Bokeh imports — grouped by sub-module for clarity
  try:
      from bokeh.embed import components, file_html
      ...                                   (:89-118, each indented four spaces, unchanged)
  except Exception as _dash_e:
      _dash_dep_fail("bokeh", _dash_e)
  ```
  `except Exception`, not `ImportError`: a pandas built against another numpy raises `ValueError: numpy.dtype size changed`. A comment above the first guard states the layout rule: only the standard library is imported outside a `try`, because `dash_setup_lib.stdlib_entry` compiles dash clear's pruning from this file with those imports alone.
- No other import moves, and no module-level `sys` is added (a copied helper must never come to rely on one; the app header imports none).

**TR-25.2 The numpy/pandas note (dash_render.py).** Directly after the bokeh guard, before the "Optional scientific dependencies" banner:
- `_DASH_MIN_PACKAGES = (("numpy", (2, 3)), ("pandas", (2, 3)))`, with a `#:` comment: dash_setup.ado's `min_numpy` and `min_pandas` hold the same (test_version_floor); below them is noted, not refused (register P1.32.1, A121); bokeh's window is P1.30's (S41).
- `_dash_dep_versions()` (new) returns `(refusal, note)`. `refusal` is `""` (S41 fills it for bokeh). For each `(name, floor)`, `got = str(getattr({"numpy": np, "pandas": pd}[name], "__version__", "") or "")[:40]`; `m = re.match(r"(\d+)\.(\d+)", got)`; when `m` and `(int(m.group(1)), int(m.group(2))) < floor`, it adds `"%s %s is older than %d.%d, the oldest dash is tested with" % (name, got, floor[0], floor[1])`. `note = "dash: " + "; ".join(parts) + "; dash goes on, and dash_setup prints the command that upgrades it"` when any, else `""`. A version not starting with two numbers is not judged.
- `_DASH_ADO_ENTRY_POINTS` (:2553) gains `_dash_dep_versions` as its last member (dash.ado calls it by name; E7).

**TR-25.3 The served app's header (`ServerAppBuilder._generate_app_source`, the "1. Header + imports" list :34025-34110). GitNexus HIGH: warn before editing.**
- The future line becomes `"from __future__ import annotations  # dash needs Python %d.%d or later: link a newer Python, then run dash_setup" % _DASH_MIN_PYTHON`.
- The stdlib lines stay where they are, then `"import warnings"`, `"import collections as _collections"` and `"import time as _time"` move up to follow `"from typing import Any, Callable, Iterable, List"`.
- Then: a two-line comment (`# WP-30 P1.32: a Python older than dash needs, or a missing or broken`, `# package, stops here in one line naming dash_setup.`), `"_DASH_MIN_PYTHON = %r" % (_DASH_MIN_PYTHON,)`, a blank line, the lines of `_textwrap.dedent(_inspect.getsource(_dash_dep_fail)).rstrip("\n").split("\n")` (the copy loop's form, E2; `import inspect as _inspect, textwrap as _textwrap` locally), a blank line, and the guards: `"if tuple(__import__('sys').version_info[:2]) < _DASH_MIN_PYTHON:"`, `"    _dash_dep_fail('python')"`, the numpy and pandas `try`/`except Exception as _dash_e:` pairs as in TR-25.1, the scipy comment lines, and one `try:` holding every bokeh line and the tornado line (each indented four spaces, the WP-21 comment kept inside) with `except Exception as _dash_e:` / `    _dash_dep_fail('bokeh', _dash_e)`.
- The copy is `_dash_dep_fail`'s exact source, so `scripts/fncov/fncov_report.app_map` maps it to the renderer's function: no `app:` key is needed in `function_test_map.py`.
- A line an earlier section added among the bokeh lines that is not a bokeh or tornado import (a stdlib import or a comment) moves above the guard, unchanged, so the `try` holds only package imports and comments; record any such move in `$S/25-impact.txt`.
- Nothing else in `_generate_app_source` changes. It is not on a copy list (R2 row S25).

**TR-25.4 The floor constant (dash.ado, new `_dash_pyfloor`).** Insert, with a header comment in the file's form, after `_dash_require_python`'s `end` and before S03's `_dash_stata_ok` header:
```stata
program define _dash_pyfloor, rclass
    version 19
    return local pyfloor "<FLOOR>"
end
```
The header says: the oldest Python dash runs under; dash_setup.ado's `_dash_pymin` and dash_render.py's `_DASH_MIN_PYTHON` hold the same number (a program of one ado-file cannot be called from another), pinned by `test_version_floor.py::TestThePythonFloorIsOneNumber` (register P1.32.4, A123).

**TR-25.5 `_dash_require_python`'s message (dash.ado).** In the refusal branch only, before its displays: `_dash_pyfloor` and `local _dd_floor "`r(pyfloor)'"`; the second display reads `"Python `_dd_floor'+: {help python}"`. No other line changes.

**TR-25.6 The dependency guard (dash.ado, new `_dash_require_deps`).** Insert after `_dash_pyfloor`, with a header comment naming WP-30 P1.32, GAPS2 H6, BR-07.1 and the decide-by-value rule. Body, in order (non-rclass; it uses only its own locals):
1. `version 19`; `_dash_require_python`.
2. `local _dd_v ""`; `capture python: import sys; from sfi import Macro as _dash_M; _dash_M.setLocal("_dd_v", "%d.%d.%d" % tuple(sys.version_info[:3]))`; if `_dd_v` is still empty, the same line once more (comment: the first python call of a session can fail where Python works, test_cscript_hygiene.py's docstring; the line is valid Python 2.7).
3. `_dd_v` empty: `mata: _dash_say("err", "dash: the Python linked to Stata could not be started (", c("python_exec"), ").")`; then `if strpos(c(machine_type), "Mac") {` `mata: _dash_say("err", "      Stata reports this computer as ", c("machine_type"), "; on a Mac, Stata and Python must be built for the same processor, both arm64 (Apple Silicon) or both x86_64 (Intel).")` `}`; `display as error "      Link Stata to a Python that starts here ({help python}), then run {cmd:dash_setup}."`; `exit 198`.
4. `_dash_pyfloor`; `local _dd_floor "`r(pyfloor)'"`; split `_dd_v` and `_dd_floor` at the dots with `subinstr(…, ".", " ", .)` and `: word 1 of` / `: word 2 of` into `_dd_vmaj`, `_dd_vmin`, `_dd_fmaj`, `_dd_fmin` (the version is digits only, built by `%d`); when `(`_dd_vmaj' < `_dd_fmaj') | (`_dd_vmaj' == `_dd_fmaj' & `_dd_vmin' < `_dd_fmin')`: `mata: _dash_say("err", "dash: Python " + st_local("_dd_v") + " is linked to Stata (", c("python_exec"), "); dash needs Python " + st_local("_dd_floor") + " or later.")`, `display as error "      Link a newer Python ({help python}), then run {cmd:dash_setup}."`, `exit 198`.
5. `local _dd_miss ""`, `local _dd_chk ""`; `capture python: import sys, importlib.util; from sfi import Macro as _dash_M; _dash_M.setLocal("_dd_miss", " ".join(m for m in ("numpy", "pandas", "bokeh") if sys.modules.get(m) is None and importlib.util.find_spec(m) is None)); _dash_M.setLocal("_dd_chk", "1")`. `sys.modules.get(m) is None` first: a blocked entry (`None`) reads as missing, an imported module as present (E11 Q7).
6. When `"`_dd_chk'" == "1"` and `_dd_miss` is not empty: `local _dd_list = subinstr("`_dd_miss'", " ", ", ", .)`; `mata: _dash_say("err", "dash: " + st_local("_dd_list") + " not installed for the Python Stata uses (", c("python_exec"), ").")`; `display as error "      Run {cmd:dash_setup} to install what is missing."`; `exit 198`. When `_dd_chk` is empty the line failed; the renderer's load decides (TR-25.8).
- Decisions are made from the locals the lines set, never from `_rc` (no `_rc` is read in the body). The two captured lines carry statements, so ENV-16's probe count stays 0 and the warm-up reader of `test_cscript_hygiene.py` finds nothing. No macro is expanded inside a Python string. Every text from the environment goes through `_dash_say`; the SMCL links are in `display` lines that expand no macro.

**TR-25.7 The call sites (dash.ado).**
- `dash`: directly after the `_dash_require_mata` statement and its comment, before S12's comment paragraph and `mata: _dash_strip_prefix()` (A154), a four-line comment (WP-30 P1.32, A154's order; every subcommand but clear: dash clear clears the registry with no Python and prunes through a standard-library path, register P1.32.3) and:
  ```stata
  mata: st_local("_dd_sub", ustrregexm(st_local("0"), "^[a-zA-Z][a-zA-Z0-9_]*") ? ustrregexs(0) : "")
  if "`_dd_sub'" != "clear" {
      _dash_require_deps
  }
  ```
  The guard call is a line of its own, so `_env_first_in` and the pytest readers find it. The subcommand is read with the routing's own expression (E3).
- `_dash_do_render`: `_dash_require_deps` on the line after `_dash_require_python` (:413), before `if `"`mode'"' == ""`.
- `_dash_xm_load`: `_dash_require_deps` on the line after `_dash_require_python` (:4578). `_dash_serve`, `_dash_render_immediate`, `_dash_prepare_spec` and the private-folder programs reach it through `_dash_xm_load` or `_dash_tmp_open`; no other call site is added.

**TR-25.8 The renderer load decides by value (`_dash_xm_load`).** Replace :4606 by:
```stata
    local _dd_err ""
    capture python: _dash_xr = _dash_ok or _dash_xs.loader.exec_module(_dash_xm)
    if _rc {
        local _dd_n : length local _dd_err
        if `_dd_n' > 0 {
            mata: _dash_say("err", "", st_local("_dd_err"), "")
            exit 198
        }
        python: _dash_xr = _dash_xs.loader.exec_module(_dash_xm)
    }
```
with a comment: the renderer's import guard puts its one line in `_dd_err` (E11 Q4); a failure that is not a dependency runs again uncaptured so its traceback shows as it did. After :4608 (the store), add:
```stata
    python: _dash_dv = _dash_xm._dash_dep_versions()
    python: _dash_M.setLocal("_dd_refuse", _dash_dv[0])
    python: _dash_M.setLocal("_dd_note", "" if _dash_ok else _dash_dv[1])
    local _dd_n : length local _dd_refuse
    if `_dd_n' > 0 {
        mata: _dash_say("err", "", st_local("_dd_refuse"), "")
        exit 198
    }
    local _dd_n : length local _dd_note
    if `_dd_n' > 0 {
        mata: _dash_note("", st_local("_dd_note"), "")
    }
```
The note prints when the renderer was loaded afresh (`_dash_ok` false): once per session and renderer version. The refusal slot is read on every load; S41 fills it. `_dd_err`, `_dd_refuse` and `_dd_note` hold exception and version text from the environment, so they are tested by their length (`: length local`) and shown only through `_dash_say`/`_dash_note`; none is ever expanded into a Stata statement (rule 1; an expanded `'"` would end the string and the rest would be read as an expression).

**TR-25.9 dash clear prunes without the packages (`_dash_tmp_clear`, dash.ado; register P1.32.3, A122).** Keep `version 19`, `_dash_require_python` and the Mata `dash*` check with its `exit` (A15: no folder, no Python). Replace `_dash_xm_load` and the four lines after it by:
1. A comment naming WP-30 P1.32 and the rule: the pruning code is compiled from dash_render.py's own text with the standard-library imports alone, so the same code and the same checks run with numpy, pandas or bokeh missing.
2. `local _tcl_dir ""`; `capture findfile dash.ado`; on rc 0 `mata: st_local("_tcl_dir", substr(st_global("r(fn)"), 1, strlen(st_global("r(fn)")) - strlen("dash.ado")))`; `local lib `"`_tcl_dir'dash_setup_lib.py"'`, `local _tcl_py `"`_tcl_dir'dash_render.py"'`; when `confirm file` fails for `lib`, `capture findfile dash_setup_lib.py` and take `r(fn)`; for `_tcl_py`, `capture _dash_find_render` and take `r(fn)`; if either is still missing, `exit` (rc 0: dash clear goes on).
3. dash_setup.ado's lines :924-928 copied (`pathresolve`, `sys.dont_write_bytecode` saved and set, the one `capture python:` loader line reading the local `lib`, `local _lrc = _rc`, the restore line), then `if `_lrc' != 0 exit`.
4. `local _tcl_tmp `"`c(tmpdir)'"'`; `python: import sys`; `python: from sfi import Macro as _dash_M`; `python: _dash_sl = sys.modules.get("_dash_setup_lib")`; `python: _dash_xp = _dash_sl.stdlib_entry(_dash_M.getLocal("_tcl_py"), "_dash_tmp_clear") if _dash_sl is not None else None`; `python: _dash_tcl = _dash_xp(_dash_M.getLocal("_tcl_tmp")) if _dash_xp is not None else ""`.
- Every `python:` line is an import, an assignment or reads by value (E10). `_dash_clear` keeps `capture _dash_tmp_clear`: a failure still clears the registry silently, as today.

**TR-25.10 The slice (dash_setup_lib.py, new `stdlib_entry(path, entry)` and `_SLICES = {}`).**
- The module docstring's first line gains "and dash clear's pruning without the packages (WP-30 P1.32)"; `import ast` joins the imports; 3.8-parseable, no nested function.
- `stdlib_entry` never raises (one `try/except Exception: return None` around the body). It:
  1. keys `_SLICES` by `(os.path.realpath(path), st.st_size, st.st_mtime_ns, entry)` and returns a hit;
  2. reads the file as UTF-8 and parses it with `ast.parse(text, filename=path)`;
  3. walks the top level: `Import`/`ImportFrom` nodes are kept as the slice's imports; `FunctionDef`/`ClassDef` nodes are definitions by name; `Assign`/`AnnAssign` nodes are definitions of every `Name` in their targets (a list per name, so a name assigned twice keeps both); every import inside a top-level `Try` binds a foreign name (`(alias.asname or alias.name).split(".")[0]`); other statements are ignored;
  4. returns None unless `entry` names a top-level `FunctionDef`;
  5. walks the closure from `entry` over `ast.Name` nodes: a name that is a definition is added; a foreign name returns None;
  6. compiles `ast.Module(body=imports + [the closure's nodes in file order], type_ignores=[])` with `compile(module, path, "exec", dont_inherit=True)` into `{"__name__": "_dash_stdlib_slice", "__file__": path}`, stores and returns `ns[entry]`.
- Line numbers stay the file's, so a traceback from the slice points at dash_render.py. It compiles only the file dash.ado located beside itself or on the ado-path, never user text, and `entry` is a constant in dash.ado.

**TR-25.11 dash_setup's first call (dash_setup.ado).**
- New `_dash_setup_pystart, rclass`, after `_dash_pyver_ok`'s `end` and before `_dash_pip_command`'s header, `version 19`, docstring in the file's `/* */` form: returns `r(pyver)` (`sys.version`'s first word, or `""` when Python could not be started) and `r(tries)` (1 or 2); the first python call of a session can fail where Python works, so a line that set nothing is run once more; the value decides, never the return code. Body: `local pyver ""`, `capture python: import sys; from sfi import Macro; Macro.setLocal("pyver", sys.version.split()[0])`, `local tries 1`; if `pyver` is empty, the same line again and `local tries 2`; `return local pyver `"`pyver'"'`, `return scalar tries = `tries'`. (`sys.version`, as :92 reads it, so the sandbox's `pyversion` stub keeps working.)
- In `dash_setup`, :92 becomes `_dash_setup_pystart` and `local pyver `"`r(pyver)'"'`, followed by the not-started branch:
  ```stata
  if `"`pyver'"' == "" {
      display as error "  Python ............. could not be started:"
      mata: display("    " + c("python_exec"), 1)
      if strpos(c(machine_type), "Mac") {
          mata: display("    Stata reports this computer as " + c("machine_type") + ".", 1)
          display as error "    On a Mac, Stata and Python must be built for the same processor:"
          display as error "    both arm64 (Apple Silicon) or both x86_64 (Intel)."
      }
      display as error "    Link Stata to a Python that starts here: {help python}"
      local n_fail = `n_fail' + 1
      local fail_items `"`fail_items' Python (could not be started)"'
      _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
          items(`"`fail_items'`warn_items'"')
      exit 198
  }
  ```
  The path and the machine type are printed as typed (Mata `display(s, 1)`, E11), never parsed as SMCL; the `Unmet:` item names no path. No `python: pass` warm-up is used, and nothing after it says "not available".
- Nothing else in `dash_setup` changes.

**TR-25.12 Both modes.** No page, figure, CustomJS or served callback changes, so there is no JS twin and no parity corpus case: the saved page's bytes are unchanged (`test_varlist_expansion.py`'s single-y digest does not move) and `test_mode_parity.py` stays green as a no-change check (G3). Saved route: the guard runs at `dash`'s entry and at the renderer load, before `_dash_do_render`. Served route: the same guard runs in Stata before `dash build, server` writes the app or `dash serve` announces; the app's header checks again in the child, under `python app.py` and under `bokeh serve`. A filter move imports nothing new: the per-session `from bokeh.models import …` lines name bokeh, already imported by the guarded header; a bokeh lacking a name every render needs is S41's start-up refusal (register P1.32.2).

**TR-25.13 Copy lists and maps.**
- Served copy lists: no entry (R2 row S25): `_dash_dep_fail` and `_DASH_MIN_PYTHON` are written into the header by `_generate_app_source`; `_dash_dep_versions` is never called by the app.
- `test/function_test_map.py` `FUNCTIONS`, under `# WP-30 S25 (P1.32): Render-time dependency guards (P1.32)`, alphabetical: `'_dash_dep_fail': 'test/test_dependency_guards.py::TestTheRendererRefusesWithTheRemedy::test_a_missing_package_is_one_line_naming_dash_setup'`, `'_dash_dep_versions': 'test/test_dependency_guards.py::TestTheVersionNote::test_numpy_or_pandas_below_the_minimum_is_noted'`.
- `SETUP_FUNCTIONS`, under the S25 anchor: `"stdlib_entry": "test/test_private_files.py::TestDashClearPrunesWithoutThePackages::test_the_slice_prunes_as_the_renderer_does"`.
- `test/program_coverage_map.py` `COVERAGE["dash.ado"]`, under the S25 anchor: `"_dash_pyfloor": ("test_env_guards.cscript:ENV-33", "test_env_guards.cscript:ENV-30")`, `"_dash_require_deps": ("test_env_guards.cscript:ENV-31", "test_env_guards.cscript:ENV-34", "test_env_guards.cscript:ENV-35")`. `COVERAGE["dash_setup.ado"]`, under the S25 anchor: `"_dash_setup_pystart": ("test_setup_honesty.cscript:HON-42", "test_setup_honesty.cscript:HON-40", "test_setup_honesty.cscript:HON-41")`.
- No Mata function is added: `_dash_say` and `_dash_note` are already in `_needed`.

**TR-25.14 Help (R3: dash.sthlp "Dependencies" and dash_setup.sthlp, S25's in batch 9).**
- dash.sthlp, Dependencies (:3779-3815 at `c96facd`), a new `{pstd}` paragraph after the packages list and before the PEP 668 paragraph: every `dash` command but `dash clear` checks, before it starts, that the linked Python starts (a first call that fails is tried once more), that it is Python <FLOOR> or later, and that numpy, pandas and bokeh are installed and import; if not, it stops with r(198) and one message naming what is missing, the Python it looked in (`c(python_exec)`) and `dash_setup`, and writes nothing; numpy or pandas older than the minimum is named in a note and the command goes on; `dash clear` clears the registry with no Python and prunes dash's temporary files with the packages missing; an app run by hand (`python app.py`, `bokeh serve`) checks the same and stops with the same one line.
- dash_setup.sthlp, step 1 of Description (:41-45 as S05 left it): one sentence after the version comparison: Python is started to read its version; a first start that fails is tried once more, and a Python that still cannot be started is reported in the summary with its path and, on a Mac, a reminder that Stata and Python must be built for the same processor (both arm64 or both x86_64), r(198).
- dash_setup.sthlp, Troubleshooting: a new `{pstd}{ul:Python could not be started}` entry after "Python not found": on a Mac with Apple Silicon an arm64 Stata cannot start an x86_64 Python, nor the reverse; link a Python built for the same processor (`{helpb python}`), then run `dash_setup` again.
- The phrases `test_every_declaration_agrees_with_dash_setup` reads (`{ul:Python <FLOOR>+}`, `Python <FLOOR> or later`, `below <FLOOR>`, the package lines) stay as S05 left them.

**TR-25.15 Security (rule 1).**
- Every environment-derived text shown in dash goes through `_dash_say` (SMCL braces and control characters made inert); dash_setup shows the path through Mata `display(s, 1)`; the `Unmet:` item holds no path.
- `_dash_dep_fail` bounds the exe and the exception text at 300 characters each and joins the message onto one line; the served relay keeps its own redaction and 4,096-character bound (`_dash_launch_app`, read only).
- No new `python:` line inlines a macro; paths cross by `Macro.getLocal`.
- `stdlib_entry` compiles only dash's shipped `dash_render.py` (located as `_dash_xm_load` locates it), with a constant entry name; it never `eval`s user text, never runs a shell, and refuses a closure that would need a package rather than importing one.
- `test/dep_block.py` writes only a stub `pandas.py` into a fresh `tempfile.mkdtemp()` folder (0700) and removes it on restore; no `shell=True` anywhere.

**TR-25.16 The guard order and costs.** A154's order holds in `dash`: S03's guard, `version 19`, the Mata guard, this guard, S12's strip, S22's dispatch. Measured cost (E11): first command 0.068 s, then 0.27 ms per guard. The renderer import cost (3.2 s on a session's first render) is unchanged and is not moved to registration.

## Boundaries

- **Batch partners (batch 9).**
  - S26 owns `GlyphMapper.map_function`'s fallback mark, the needs-points note read by S23's `_dash_note_empty_layer`, any helper it adds after `"_dash_function_points",` (33126) in the served copy list, dash.sthlp:413-418 and its `FN` cases.
  - S27 owns `_dash_finish_auto_bases`, `_dash_finish_count_ticks`, S21's `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS`, `_dash_units_to_axis`, the auto-base column, dash.sthlp's Plot types paragraphs for bar, area, spike and dropline, its CHANGELOG "Results that change" lines and its `DB` cases.
  - This section touches none of them. Shared files: dash_render.py (module top, `_generate_app_source`'s header, `_DASH_ADO_ENTRY_POINTS`: distinct hunks), dash.sthlp (Dependencies only), CHANGELOG.md (its Requirements marker only), BUGS.md and `test_tracking_documents.py` (its own entry and key), the map files (its own anchors), `test_wp30_truth.cscript` (its own block).
- **Earlier sections, read and not edited:** S03's guard lines, `_dash_stata_ok`, `_dash_require_stata`, `_dash_statamin`, `_dash_setup_stata`, ENV-24..29; S05's `_dash_pymin` value, `_dash_pyver_ok`, `stata_guide`, `below_floor_message`, HON-31/32, `TestTheFloorAdmitsTheServedLauncher`; S06's `_dash_emit_note`, `_dash_smcl_escape`, Mata `_dash_note`; S12's `_dash_strip_prefix` paragraph; S22's dispatch; S23's trial and relay in `_dash_launch_app`.
- **Later sections:**
  - S41 owns bokeh's version window: the refusal slot of `_dash_dep_versions`, the app-start bokeh check, `VERIFIED_BOKEH`, the dash_setup gate and pip specs, the internals guards and the requirements files. Until S41 lands, a bokeh 3.0-3.5 (no `CustomJSTicker`) still fails with r(7102) at its first render (critic error 1); that state exists only on `wp30-p1`.
  - S46 owns `_dash_launch_app`'s new flags and the warm-up; S57 the served move path.
  - S58 owns every tracking document (A145).
- **Not changed.** `_dash_python_ok` (pure; ENV-01..04); `_dash_launch_app` (read only: its stderr tail already carries the child's one line); `_dash_find_render`; the `version` lines; `_dash_require_mata`'s `_needed`; the renderer's `_dash_tmp_clear` and its helpers (compiled by the slice, never edited); `dash_setup`'s package loop (its `capture python: import <pkg>` probes stay); the served copy lists; `rejected_options.json`.
- **Out of scope.** P2.40 (the served child is `sys.executable` with Stata's exported PYTHONPATH): its failure now ends in one line naming `dash_setup`, and the residual stays P2.40's. Windows, Linux, Intel Macs and x86_64 Stata (M4; the platform package P1.34.6).

## Stata truth

twoway has no Python dependency, so there is no twoway truth and no fixture (`Fixture: none`), as in WP-29 S09. The Stata facts the design rests on are measured live in S25's block of `test/test_wp30_truth.cscript` (stub header `* ==== S25 P1.32: Render-time dependency guards ====`), between its own start and end lines, through `_w30_expect`/`_w30_done`. The helper goes directly above the header:

```stata
capture program drop _s25_scope
program define _s25_scope
    version 19
    args path
    local _dd_err ""
    python: import importlib.util as _s25u
    python: from sfi import Macro as _s25M
    python: _s25s = _s25u.spec_from_file_location("_s25_probe", _s25M.getLocal("path"))
    python: _s25m = _s25u.module_from_spec(_s25s)
    capture python: _s25r = _s25s.loader.exec_module(_s25m)
    c_local s25rc = _rc
    c_local s25err `"`_dd_err'"'
end
```

The cases:
- **RG-01** `capture python: raise SystemExit("dash: s25 probe")`, `local rg01 = _rc`; expect `rg01 == 0` ("a SystemExit ends a python: line with rc 0, so the guard raises ImportError under Stata").
- **RG-02** `capture python: raise ImportError("dash: s25 probe")`, `local rg02 = _rc`; expect 7102.
- **RG-03** `file write` into `` `w30_work'/s25_probe.py `` three lines (`import sfi`, `sfi.Macro.setLocal("_dd_err", "dash: s25 probe")`, `raise ImportError("dash: s25 probe")`), then `_s25_scope "<that path>"`; expect `s25rc == 7102` and `s25err == "dash: s25 probe"` ("a module run by exec_module sets the calling program's local before it fails, so the load decides by value"). Erase the file.
- **RG-04** `quietly log using "`w30_work'/s25.log", text replace name(s25l)`, `mata: display(char(123) + "bf:s25" + char(125), 1)`, close; `cert_file_has "`w30_work'/s25.log", needle("{bf:s25}")` finds it, and `r(found)` is read into a local on the next line (`cert_file_has` clobbers `r()`). The braces are built with `char()` so the echoed command line cannot hold the needle; only the printed line can ("Mata display(s, 1) prints SMCL as typed: dash_setup shows the path so"). Erase the log.

No `capture python:` line in the block holds the word `import` (RG-02's `ImportError` is capitalised), so `len(with_probes) == 13` does not move. All four pass on the unmodified tree; they are guard truths, listed so in the failure file.

Run: `WP30_ONLY=S25 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_wp30_truth.do"` (the two-line driver of index "The cscript driver", `<repo>` = `$WT`).

## TDD test stubs

The first stubs are the regression tests; each fails on the unmodified batch-9 base (G1). Python subprocess tests use `sys.executable` (the suite's Python) with `-B`, a `PRE` string that blocks or patches, and `cwd=tmp_path`; they never touch Stata.

### test/test_dependency_guards.py (new classes, appended)

Helpers at module level after the existing ones: `_RENDER` (absolute path of dash_render.py), `_run(code, *args)` (subprocess, 120 s timeout, returns `(rc, stdout, stderr)`), `_block(pkg)` (the PRE text `import sys; sys.modules[%r] = None`), `_old(ver)` (`import sys, collections; sys.version_info = collections.namedtuple("version_info", "major minor micro releaselevel serial")(*%r)`, so a stdlib module that reads `sys.version_info.major` still imports), `_build_app(tmp_path)` (the `test_version_floor._built` spec, one scatter), `_body(name)` (dash.ado's logical lines of one program, from `test_program_coverage_map`'s `_ado_programs` and `_logical_lines`).

`TestTheRendererRefusesWithTheRemedy`
- Test: `test_a_missing_package_is_one_line_naming_dash_setup` (parametrized numpy, pandas, bokeh) — `_block(pkg)` then `runpy.run_path(_RENDER, run_name="__main__")` with `--spec x --data y --output z.html`; rc 1; `stderr.strip()` is one line starting `dash: could not import <pkg> for the Python at `, containing `sys.executable` and ending `; run dash_setup`; no `Traceback`. Fails at base: traceback, `ModuleNotFoundError`.
- Test: `test_a_package_that_will_not_import_is_named_with_its_reason` — `_block("jinja2")` (a dependency of bokeh's, not of numpy or pandas at import); the line names `bokeh` and contains `jinja2`. Fails at base. If the base run shows pandas importing jinja2 first, the test asserts the package the base traceback names and says why in its docstring.
- Test: `test_a_python_below_the_floor_is_refused_before_any_import` — `_old((3, 6, 15, "final", 0))` plus `_block("numpy")`; the one line names `Python 3.6.15`, `Python <FLOOR> or later` and `dash_setup`, not `numpy`. Fails at base.
- Test: `test_under_stata_the_refusal_is_an_import_error_and_a_local` — PRE installs a stand-in `sfi` (`types.ModuleType`, `Macro = types.SimpleNamespace(setLocal=LOC.__setitem__, getLocal=…)`) and blocks pandas; loads the file twice, as `_dash_render_export` through `importlib.util` and with `runpy.run_path(..., run_name="__main__")`, printing JSON of `type(e).__name__`, `str(e)` and `LOC`; both are exactly `ImportError` and `LOC["_dd_err"] == str(e)`, naming pandas and dash_setup. Fails at base (`ModuleNotFoundError`, no `_dd_err`).
- Test: `test_the_old_interpreters_here_get_the_remedy` — `skipif` when `/usr/local/bin/python3.6` or `/usr/local/bin/python3.7` is absent (present on the maintainer's Mac; a skip is recorded, never counted a pass); 3.6's stderr holds `SyntaxError` and `dash needs Python <FLOOR> or later: link a newer Python, then run dash_setup`; 3.7's is one line `dash: Python 3.7.` … `older than dash needs`. Fails at base.

`TestTheGuardKeepsAHealthyImport`
- Test: `test_every_unguarded_top_level_import_is_the_standard_library` — over dash_render.py's AST: every top-level `Import`/`ImportFrom` names `__future__` or a member of `sys.stdlib_module_names`; every top-level `Try` holding an import has one handler, `except Exception as _dash_e`, whose body is one `_dash_dep_fail(...)` call; the version `If` precedes the first such `Try`. Fails at base (numpy at :82).
- Test: `test_the_future_line_carries_the_remedy` — line 61's text equals TR-25.1's. Fails at base.
- Guard: `test_both_files_parse_at_python_3_7` — `ast.parse(..., feature_version=(3, 7))` of dash_render.py and of `fncov_report.sample_app_source()`. Passes at base.

`TestTheServedAppGuardsItsImports`
- Test: `test_the_app_refuses_a_missing_package_in_one_line` (parametrized numpy, pandas, bokeh) — `_build_app`, then `_block(pkg)` and `runpy.run_path(app, run_name="__main__")` with `--port 5999`; rc 1, one line naming the package and dash_setup, no `Traceback`. Fails at base.
- Test: `test_under_bokeh_serve_the_refusal_is_an_import_error` — `_block("pandas")`, `run_name="bokeh_app_s25"`; prints `ImportError` exactly and a message naming dash_setup. Fails at base (`ModuleNotFoundError`).
- Test: `test_the_app_refuses_a_python_below_the_floor` — `_old((3, 6, 15, "final", 0))` plus `_block("numpy")`, so the unguarded base stops at its numpy import instead of starting a server; the one line names `Python 3.6.15` and the floor, not numpy. Fails at base (a numpy traceback).
- Test: `test_the_header_guards_before_any_package_import` — the app's AST: body[1] is the future import and its source line carries the comment; `_DASH_MIN_PYTHON` is assigned before the first `Try`; the `_dash_dep_fail` def's source equals `textwrap.dedent(inspect.getsource(dr._dash_dep_fail))`; every top-level import outside a `Try` is stdlib; `tornado` is imported inside the bokeh `Try`. Fails at base.

`TestTheVersionNote` (A121)
- Test: `test_the_installed_versions_need_no_note` — `dr._dash_dep_versions() == ("", "")`. Fails at base (`AttributeError`).
- Test: `test_numpy_or_pandas_below_the_minimum_is_noted` — `monkeypatch.setattr(dr.np, "__version__", "2.1.3")`: refusal `""`, note names `numpy 2.1.3` and `2.3`; pandas `2.2.0` likewise; both together in one note. Fails at base.
- Test: `test_an_unreadable_version_is_not_noted` — `"dev"` and `""` give `("", "")`. Fails at base.

`TestTheGuardOrder` (dash.ado text)
- Test: `test_the_dependency_guard_follows_the_mata_guard_and_spares_clear` — in `dash`'s body, in order: `_dash_require_mata`, the `_dd_sub` line, `if "`_dd_sub'" != "clear" {`, `_dash_require_deps`, `mata: _dash_strip_prefix()`, the first `"`_subcmd'" ==`. Fails at base.
- Test: `test_the_loader_and_the_render_run_the_guard_first` — `_dash_xm_load`'s statements after `version 19` start `_dash_require_python`, `_dash_require_deps`; its `exec_module` line is `capture python:` followed by the `_dd_err` length test, and no line of `_dash_xm_load` expands `_dd_err`, `_dd_refuse` or `_dd_note` (no `` `_dd_err' ``, `` `_dd_refuse' `` or `` `_dd_note' `` in its text); `_dash_do_render` has `_dash_require_deps` after `_dash_require_python` and before its first `python:`. Fails at base.
- Test: `test_the_guard_decides_from_values` — `_dash_require_deps` exists; its `python:` lines are all `capture python:`; it sets `_dd_v`, `_dd_miss`, `_dd_chk`; no line reads `_rc`; it calls `_dash_pyfloor` and holds no literal `\b3\.\d+\b`. Fails at base.

`TestTheBlockHelper` (added with the helper in 25-02; not a regression test)
- Test: `test_missing_and_broken_restore_every_module` — in a subprocess: `block("json", "missing")` makes `import json` raise; `restore()` returns True and `sys.modules["json"]` is the original object; `block("json", "broken")` leaves `find_spec("json")` not None and makes `import json` raise `ImportError` naming it; `fake_version`, `fake_package_version`, `sfi_flaky` (with a stand-in real `sfi`), `plant_run` and `child_stub` each put back exactly what they changed.

### test/test_version_floor.py

`TestThePythonFloorIsOneNumber` (after the classes S03 and S05 added, before `TestTheGeneratedAppEvaluatesNoAnnotationAtImport`)
- Test: `test_dash_ado_names_the_floor_once` — `re.findall(r'return local pyfloor "([^"]+)"', dash.ado)` has one match, equal to `_setup_ado_floor()[0]`. Fails at base.
- Test: `test_the_renderer_and_the_app_hold_the_same_floor` — `dr._DASH_MIN_PYTHON == tuple(int(p) for p in pymin.split("."))`; dash_render.py's line 61 and the built app's future line both contain `dash needs Python %s or later` % pymin; the app holds `_DASH_MIN_PYTHON = (%d, %d)`. Fails at base.
- Test: `test_the_package_minimums_agree_with_dash_setup` — `dict(dr._DASH_MIN_PACKAGES) == {"numpy": v(min_numpy), "pandas": v(min_pandas)}`. Fails at base.
- Test: `test_the_refusals_read_the_constant` — the bodies of `_dash_require_python` and `_dash_require_deps` call `_dash_pyfloor` and hold no `\b3\.\d+\b`. Fails at base.
- Flip: `TestTheFloorIsTheTestedBaseline::test_every_declaration_agrees_with_dash_setup` — `("Python %s+" % py) in ado` becomes `('return local pyfloor "%s"' % py) in ado`. `Flipped: … -- the literal "Python <FLOOR>+" in dash.ado was the one place dash.ado stated the floor; it is now the constant _dash_pyfloor, which the message reads.`

### test/test_private_files.py

`TestDashClearPrunesWithoutThePackages`
- Test: `test_the_slice_prunes_as_the_renderer_does` — two twin trees under `tmp_path` (`a`, `b`), each with `dash-<uid>` at 0700 holding `run-<os.getpid()>-s25`, `run-<a dead pid>-s25` (the pid of a finished `subprocess.run([sys.executable, "-c", "0"])`), a fallback root and a `previews` folder with more previews than `_DASH_PREVIEW_KEEP` (planted as `TestThePreviews` plants them); `dr._dash_tmp_clear(a)` and `dash_setup_lib.stdlib_entry(<dash_render.py>, "_dash_tmp_clear")(b)` both return `""` and leave equal sorted walks. Fails at base (`AttributeError: stdlib_entry`).
- Test: `test_the_slice_imports_no_package` — a subprocess with numpy, pandas, bokeh, tornado and jinja2 set to None: `stdlib_entry` returns a function that prunes a planted `run-<pid>-s25`; afterwards none of those names is a real module in `sys.modules`. Fails at base.
- Test: `test_a_slice_that_would_import_a_package_is_refused` — a temp file `try:\n    import json as np\nexcept Exception:\n    pass\ndef f():\n    return np\n` gives None for `f`; an absent entry, a class entry and a file of invalid UTF-8 give None; nothing raises. Fails at base.
- Test: `test_the_slice_is_built_once_per_file_version` — two calls return the same object; after `os.utime(path, ns=(…, st_mtime_ns + 10**9))` a new one. Fails at base.
- Test: `test_dash_clear_prunes_through_the_slice` — `_dash_tmp_clear`'s body: `_dash_require_python` first, the Mata `dash*` check before the first `python:` line, `stdlib_entry(` with `"_dash_tmp_clear"`, no `_dash_xm_load`. Fails at base.

### test/test_string_value_export.py (flip)

- `TestDashAdoUsesTheWriter::test_every_entry_point_is_called_by_the_ado_and_no_other`: `called = set(re.findall(r"_dash_xm\.(_dash_\w+)\(", ado)) | set(re.findall(r'stdlib_entry\([^)]*"(_dash_\w+)"\)', ado))`; the expected set gains `"_dash_dep_versions"`; the docstring gains one sentence. `Flipped: … -- dash clear now reaches _dash_tmp_clear through dash_setup_lib.stdlib_entry, so it runs without the packages, and _dash_xm_load calls _dash_dep_versions.`

### test/dep_block.py (new test helper)

A module docstring in `setup_sandbox.py`'s manner (what it changes, that it starts no process and writes only into its own temporary folder). State kept in module globals (`_KEPT`, `_BLOCKED`, `_FINDERS`, `_ENV`, `_DIRS`, `_HITS`, `_ATTRS`). Functions:
- `block(name, how)`: `how` is `"missing"` (`sys.modules[name] = None`) or `"broken"` (a `MetaPathFinder` at the front of `sys.meta_path` whose `find_spec` answers `importlib.util.spec_from_loader(fullname, loader)` for `name` and its submodules, the loader's `exec_module` raising `ImportError("dash test: %s is installed but cannot be imported" % module.__name__)`); first every `sys.modules` key equal to `name` or under `name.`, and `_dash_render_export`, is taken out and kept. `stata_block(local_name, how)` reads the package from a Stata local by `sfi.Macro.getLocal`.
- `forget_renderer()`: takes `_dash_render_export` out and keeps it.
- `fake_version(info)`: keeps and replaces `sys.version_info`.
- `fake_package_version(name, text)`: keeps and replaces `sys.modules[name].__version__`.
- `sfi_flaky()`: replaces `sys.modules["sfi"]` with a module whose `__getattr__` counts the call, puts the real `sfi` back and raises `AttributeError`, so the first `from sfi import Macro` fails and the next succeeds; `stata_hits()` sets the local `rg_hits`.
- `plant_run(tmpdir)`: `os.mkdir(<tmpdir>/dash-<uid>/run-<os.getpid()>-rg37, 0o700)` when that root exists; `stata_plant_run()` reads the local `tmp`, sets `rg_run`.
- `child_stub()`: `tempfile.mkdtemp()`, writes `pandas.py` raising `ModuleNotFoundError("No module named 'pandas' (dash test stub)", name="pandas")`, keeps and sets `os.environ["PYTHONPATH"]` to that folder.
- `restore()`: removes its finders, deletes every `sys.modules` entry it blocked or that was imported under a blocked name, puts back every kept module, `sys.version_info`, `__version__`, `PYTHONPATH` (removed when it was unset), removes its folders (`shutil.rmtree`), clears its state, and returns True when every kept object is back by identity. `stata_restored()` calls it and sets the local `rg_clean` to `"1"` or `""`.

### test/test_env_guards.cscript (ENV-30..39, appended after S03's ENV-29, before the closing display)

Header `*! Tests:` line: "ENV-01 through ENV-39", plus one sentence: ENV-30..39 are the dependency guard of WP-30 P1.32. The run opens with `python: import os as _rg_os, sys as _rg_sys`, `python: _rg_sys.path.insert(0, _rg_os.getcwd())`, `python: import dep_block` (uncaptured; the driver's working folder is `test/`). Every case measures, restores through `dep_block.stata_restored()`, and displays `ENV-3n measured: …` with its values before any assert; the asserts and `ENV-3n PASS: …` lines follow, in id order, after the last case. Logs go to `` `c(tmpdir)'dash_env3n*.log `` and are read with `_env_log_has` (wrapped lines rejoined, case-blind), then erased; every file a case checks for absence is erased first (the ENV-17 rule). The model, ENV-31:

```stata
sysuse auto, clear
capture dash clear
quietly dash scatter mpg weight, name(e31g)
tempfile e31
foreach pkg in numpy pandas bokeh {
    foreach sfx in "_i.html" ".html" ".py" {
        capture erase "`e31'_`pkg'`sfx'"
    }
    local rg_pkg "`pkg'"
    python: dep_block.stata_block("rg_pkg", "missing")
    local lg "`c(tmpdir)'dash_env31_`pkg'.log"
    capture erase "`lg'"
    quietly log using "`lg'", replace text name(e31l)
    capture noisily dash scatter mpg weight, saving("`e31'_`pkg'_i.html") replace
    local e31i_`pkg' = _rc
    capture noisily dash scatter mpg weight, name(e31r)
    local e31r_`pkg' = _rc
    capture noisily dash build, saving("`e31'_`pkg'.html") replace nobrowser
    local e31b_`pkg' = _rc
    capture noisily dash build, saving("`e31'_`pkg'.py") server replace
    local e31s_`pkg' = _rc
    capture noisily dash serve, port(5932) timeout(1) nobrowser
    local e31v_`pkg' = _rc
    quietly log close e31l
    python: dep_block.stata_restored()
    local e31c_`pkg' "`rg_clean'"
    ... confirm file for the three outputs into e31w_`pkg'; _env_log_has for "`pkg'",
        "dash_setup", c(python_exec), "not installed" (each 1) and "Traceback",
        "starting Bokeh Server" (each 0) into locals ...
    display "ENV-31 measured: `pkg' rc `e31i_`pkg'' `e31r_`pkg'' `e31b_`pkg'' `e31s_`pkg'' `e31v_`pkg'' written `e31w_`pkg'' clean `e31c_`pkg''"
}
```

- Test: **ENV-30** (wiring, Mata over dash.ado's text): in `dash`, `_env_first_in` of `_dash_require_mata` < `_dash_require_deps` < each of `_dash_kpi _dash_build _dash_clear _dash_serve _dash_plot`; for every program of `_env_progs_with("../dash.ado", "python")` but `_dash_require_deps` and `_dash_tmp_clear`, the first positive ordinal among `_dash_require_deps`, `_dash_xm_load` and `_dash_tmp_open` is below its first `python` ordinal; in `_dash_xm_load`, `_dash_require_python` < `_dash_require_deps` < the first `python`; `_dash_tmp_clear` has no `_dash_xm_load` (ordinal 0). Fails at base (ordinal -1).
- Test: **ENV-31** (every route, each package missing): all 15 return codes 198; nothing written; the log names the package, `dash_setup` and `c(python_exec)`, says "not installed", holds no `Traceback` and no "starting Bokeh Server"; `rg_clean` is 1 after each. Fails at base (one-line r(7102) with a traceback; registration rc 0).
- Test: **ENV-32** (installed but broken): `block("numpy", "broken")`; the one-line form gives 198, the log has "could not import numpy", "cannot be imported" and `dash_setup`, no `Traceback`; not written. Fails at base (r(7102)).
- Test: **ENV-33** (below the floor): `python: dep_block.fake_version((3, 6, 15, "final", 0))`; the one-line form gives 198, the log has "Python 3.6.15", "Python <FLOOR> or later" (read `_dash_pyfloor` before the case) and `dash_setup`; not written. Fails at base.
- Test: **ENV-34** (cannot start): `block("sfi", "missing")`; the one-line form gives 198, the log has "could not be started", `c(python_exec)`, "Apple Silicon" (this machine's `c(machine_type)` holds "Mac") and `dash_setup`, no `Traceback`; not written. Fails at base (r(7102) at `from sfi import`).
- Test: **ENV-35** (a first failed start is retried): `dep_block.sfi_flaky()`; `dash scatter mpg weight, name(e35)` gives rc 0 and `${dash_json_e35}` is not empty; `rg_hits` is 1. Fails at base (no Python runs at registration: `rg_hits` 0).
- Test: **ENV-36** (the A121 note): `fake_package_version("numpy", "2.1.3")` and `forget_renderer()`; a one-line render gives rc 0 and writes its page, and its log holds `(note:` and `numpy 2.1.3` once; a second one-line render's log holds no `numpy 2.1.3`. Fails at base (no note).
- Test: **ENV-37** (dash clear prunes without the packages): one unblocked one-line render (the root exists), `stata_plant_run()`, `block("numpy", "missing")`; `dash clear` gives rc 0, the log has "registry cleared", and `mata: direxists(st_local("rg_run"))` is 0. Fails at base (the planted folder stays: the load fails inside `capture`).
- Test: **ENV-38** (the served child): register `e38`, `dep_block.child_stub()`; `dash serve, port(5931) timeout(5) nobrowser` gives 198, the log has "run dash_setup" and "pandas", no `Traceback`. Fails at base (a traceback tail). Before writing, `grep -rn "port(5931)\|port(5932)" test/` must print nothing; otherwise take the next free literal.
- Guard: **ENV-39** (dash clear is spared by the guard): `block("sfi", "missing")`; `dash clear` gives rc 0 and the log has "registry cleared". Passes at base.

### test/test_setup_honesty.cscript (HON-40..42, appended after S05's HON-32, before the cleanup `macro drop HON_SB_SPEC …`)

The run imports `dep_block` as ENV-30..39 do. HON-40 and HON-41 run `dash_setup` in `setup_sandbox`'s sandbox, written inline in `_hon_sb_setup`'s order with the dep_block call between install and run and `dep_block.stata_restored()` between run and verdict: `global HON_SB_SPEC "{}"`, `HON_SB_EXPECT` as HON-28 sets it for a run that installs nothing; measure, restore, then assert.
- Test: **HON-40** — `block("sfi", "missing")` during `dash_setup`: rc 198; the log holds "could not be started", the path as typed, "dash_setup did not complete", "Unmet:" and "Python (could not be started)", and (this Mac) "both arm64"; r(match) 1, so no process started. Fails at base (r(7102), no summary).
- Test: **HON-41** — `sfi_flaky()`: rc 0, "Python ............. OK", `rg_hits` 1, r(match) 1. Fails at base (r(7102)).
- Test: **HON-42** — `capture _dash_setup_pystart` (dash_setup.ado is in memory after HON-40/41 ran `dash_setup`) gives rc 0, `r(pyver)` equal to `sys.version.split()[0]` read separately into a local, and `r(tries)` 1. Fails at base (rc 199, unrecognized).

### Pinned tests that stay as they are (measured compatible)

`test_private_files.py::TestTheAdoUsesThePrivateDir::{test_each_python_program_calls_dash_require_python_first, test_every_new_python_line_is_an_assignment_or_a_setlocal, test_python_reads_paths_by_value, test_dash_clear_prunes_through_a_captured_call}`; `test_cscript_hygiene.py::TestTheShippedAdoFilesFollowTheSameRule` (all), `::TestTheChecksReachEveryScript::test_the_import_probes_are_found` (13); `test_env_guards.cscript` ENV-01..11, ENV-13..23, ENV-24..29, PF-10; `test_version_floor.py::TestTheGeneratedAppEvaluatesNoAnnotationAtImport` (both), S03's `TestTheStataFloor`, S05's `TestTheFloorAdmitsTheServedLauncher`; S12's `test_the_prefix_strip_follows_the_guards`; `test_server_optional_deps.py::TestScipyDoesNotKillTheWholeApp`; `test_security_surface.py::TestUserTextIsEchoedAsText`; `test_varlist_expansion.py`'s single-y digest.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Renderer refuses a missing, broken or old dependency in one line | pytest `TestTheRendererRefusesWithTheRemedy` (subprocess) | none | saved route (the renderer); served route via the app tests |
| Under Stata the refusal is an ImportError and a local | pytest stand-in `sfi`; RG-01..03 live | none | both (one renderer) |
| The app header refuses the same (child, `python app.py`, `bokeh serve`) | pytest `TestTheServedAppGuardsItsImports`; ENV-38 through `dash serve` | none | served |
| The guard runs first on every route and spares `dash clear` | pytest `TestTheGuardOrder`; ENV-30 | none | both |
| Every route refuses each missing package, nothing written or announced | ENV-31 | none | both (one-line, registration, build, build server, serve) |
| Broken package, old Python, Python that cannot start, retry | ENV-32..35 | none | both (one-line form; registration) |
| numpy/pandas below the minimum is a note | pytest `TestTheVersionNote`; ENV-36 | none | saved route (the served route shares `_dash_xm_load`) |
| `dash clear` prunes without the packages and with no Python | pytest `TestDashClearPrunesWithoutThePackages`; ENV-37, ENV-39 | none | n/a (no page) |
| dash_setup captures, retries and reports its first call | HON-40..42 (sandbox) | none | n/a |
| One floor number | pytest `TestThePythonFloorIsOneNumber` | none | both (renderer and app) |
| Nothing drawn changes | `test_mode_parity.py`, `test_varlist_expansion.py`, the full suite | existing | both, before and after filter moves |
| Registries | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_cscript_hygiene.py`, `test_tracking_documents.py` | none | — |

**Acceptance criteria.**
- **AC-25.1** With numpy, pandas or bokeh missing, the one-line form, a registration, `dash build`, `dash build, server` and `dash serve` each end r(198) with a log naming the package, `c(python_exec)` and `dash_setup`, no traceback, no file and no announcement (ENV-31).
- **AC-25.2** An installed package that fails to import ends r(198) with its import error's text (ENV-32; pytest jinja2 case).
- **AC-25.3** Python 3.6.15 (patched) is refused naming 3.6.15 and `<FLOOR>`, in Stata (ENV-33), by the renderer and by the app (pytest).
- **AC-25.4** A Python that cannot start is refused naming `c(python_exec)`, the processor rule and `dash_setup` (ENV-34); a first failed start is retried and the command runs (ENV-35, HON-41).
- **AC-25.5** `python app.py`, the served child and the renderer run as a program exit 1 with one line naming `dash_setup`; `bokeh serve` raises ImportError with it (pytest); `dash serve` ends r(198) with it (ENV-38).
- **AC-25.6** Python 3.6 shows the remedy on the future line; 3.7 gets the floor message (pytest, on this Mac).
- **AC-25.7** numpy 2.1.3 gives one note per renderer load and the page is written (ENV-36).
- **AC-25.8** `dash clear` prunes a planted run folder with numpy missing (ENV-37) and clears the registry when Python cannot start (ENV-39); the slice prunes exactly as the renderer does (pytest).
- **AC-25.9** `dash_setup` with `sfi` blocked ends r(198) with the summary, the path as typed and the processor rule, starting no process (HON-40).
- **AC-25.10** `_dash_pymin`, `_dash_pyfloor`, `_DASH_MIN_PYTHON`, both future lines and the app's constant agree (pytest).
- **AC-25.11** The full suite, the parity corpus and the single-y digest are green with no expectation changed beyond the three flips.

## Tasks

**Commit boundary.** Tasks 25-01 to 25-12 form the one commit of entry `P1.32`. Its subject is `Check Python and its packages before dash starts, naming dash_setup (WP-30 P1.32)`, made by 25-12 on `wp30-s25` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s25` (`$WT`), after one full run through the queue. The body opens with `<scratch>/25-P1.32-failure.txt`, then the measured defect (E11, the H6a-d symptoms of the Overview), then what changed and where, then the `Regression:`, `Flipped:`, `Fixture: none (Stata facts measured live: test_wp30_truth.cscript RG-01..RG-04)` and `BUGS.md: "<title>" (closed)` lines (Notes). Every command runs from `$WT`; `S=<scratch>/s25` (`mkdir -p "$S"`). A cscript runs only through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`), prefixed `WP30_ONLY=S25` for the truth script. Every probe do-file opens with `adopath ++ "$WT/"` and `global dash_nobrowser 1`.

<task type="auto" id="25-01">
  <name>Write the failing pytest regression tests</name>
  <files>test/test_dependency_guards.py, test/test_version_floor.py, test/test_private_files.py</files>
  <action><![CDATA[
    Check the base: `git -C "$WT" rev-parse HEAD` equals `cat <scratch>/batch-9-base.txt` and `git -C "$WT" branch --show-current` prints `wp30-s25`; stop and report otherwise. Read `_dash_pymin`'s value at the base (`grep -n 'return local pymin' dash_setup.ado`) and write it to `$S/floor.txt`; it is `<FLOOR>` below.
    Append to `test/test_dependency_guards.py` the helpers and the classes `TestTheRendererRefusesWithTheRemedy`, `TestTheGuardKeepsAHealthyImport`, `TestTheServedAppGuardsItsImports`, `TestTheVersionNote` and `TestTheGuardOrder` exactly as "TDD test stubs" gives them (subprocesses with `sys.executable -B`, no `shell=True`, 120 s timeouts). Add `TestThePythonFloorIsOneNumber` to `test/test_version_floor.py` after the classes S03 and S05 added and before `TestTheGeneratedAppEvaluatesNoAnnotationAtImport`. Add `TestDashClearPrunesWithoutThePackages` to `test/test_private_files.py` after `TestTheAdoUsesThePrivateDir`, loading `dash_setup_lib.py` through `importlib.util` as `test_version_floor.py` does.
    Run `python3 -m pytest test/test_dependency_guards.py test/test_version_floor.py test/test_private_files.py -q -n0 -p no:cacheprovider -rf > "$S/25-01-pytest.log" 2>&1`.
    Write `<scratch>/25-P1.32-failure.txt`: the base sha, each FAILED node with its first assertion or exception line, and the guard that passed (`test_both_files_parse_at_python_3_7`). Copy the batch-9 impact rows for `_generate_app_source` (HIGH), `_DASH_ADO_ENTRY_POINTS`, `_dash_tmp_clear` and dash.ado/dash_setup.ado (UNKNOWN) into `$S/25-impact.txt` with the grep confirmations of Evidence E4-E6, and report the HIGH row to the orchestrator before 25-05. Do not commit. Edit no shipped file.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED ' "$S/25-01-pytest.log"` prints 30 (29 if `/usr/local/bin/python3.6` or `python3.7` is absent, when `test_the_old_interpreters_here_get_the_remedy` is reported SKIPPED and that is written in the failure file); `grep -c '^FAILED.*test_both_files_parse_at_python_3_7' "$S/25-01-pytest.log"` prints 0; no FAILED line ends in a timeout (every base failure is an assertion or an import error); `test -s <scratch>/25-P1.32-failure.txt && test -s "$S/25-impact.txt"`.]]></verify>
  <done>Every pytest regression test of the section existed and was shown failing on the unmodified tree, with the failure text and the impact record saved.</done>
</task>

<task type="auto" id="25-02">
  <name>Write the blocking helper and ENV cases</name>
  <files>test/dep_block.py, test/test_env_guards.cscript, test/test_dependency_guards.py</files>
  <action><![CDATA[
    Create `test/dep_block.py` with the docstring and functions of "TDD test stubs / test/dep_block.py" (stdlib only; no process; files only in its own `tempfile.mkdtemp()` folder). Add `TestTheBlockHelper::test_missing_and_broken_restore_every_module` to `test/test_dependency_guards.py`.
    In `test/test_env_guards.cscript`, before writing check `grep -rn "port(5931)\|port(5932)" test/` prints nothing (else take the next free literal and say so in the failure file). Append ENV-30..ENV-39 after ENV-29's last display and before `display "All environment guard tests PASSED."`, as one contiguous run in the measure-restore-display-then-assert form of "TDD test stubs", and update the header's `Tests:` line. Read `_dash_pyfloor`'s expected value from `$S/floor.txt` for ENV-33's needle. Each assert is followed by its literal `display "ENV-3n PASS: …"`.
    Run `python3 -m pytest test/test_dependency_guards.py -q -n0 -p no:cacheprovider -k BlockHelper` and the driver for `test_env_guards.cscript`. Append to `<scratch>/25-P1.32-failure.txt` the ten `ENV-3n measured:` lines of the base log and the first failing assert.
  ]]></action>
  <verify><![CDATA[The pytest run prints `1 passed`; in `$S/run_test_env_guards.log` `grep -c 'ENV-3[0-9] measured:'` prints at least 10, `grep -c 'ENV-3[0-8] PASS'` prints 0, and `grep -c 'ENV-29 PASS'` prints 1; every `measured:` line shows `clean 1` where it reports one; `grep -c 'ENV-3' <scratch>/25-P1.32-failure.txt` is at least 10.]]></verify>
  <done>The ENV regression cases and their blocking helper existed, put Python back after every case, and were shown failing on the unmodified tree, with ENV-39 shown holding.</done>
</task>

<task type="auto" id="25-03">
  <name>Write the HON cases and RG truths</name>
  <files>test/test_setup_honesty.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Append HON-40..HON-42 to `test/test_setup_honesty.cscript` after S05's HON-32 and before `macro drop HON_SB_SPEC HON_SB_EXPECT HON_SB_WHY`, as "TDD test stubs" gives them: the sandbox steps of `_hon_sb_setup` written inline with the `dep_block` call after `setup_sandbox.stata_install` and `dep_block.stata_restored()` before `setup_sandbox.stata_verdict`; measure, restore, display `HON-4n measured: …`, then assert and display `HON-4n PASS: …`. Copy `HON_SB_EXPECT` from HON-28.
    In S25's stub block of `test/test_wp30_truth.cscript`, write RG-01..RG-04 between its start and end display lines and `_s25_scope` directly above its header, exactly as "Stata truth" gives them; files only under `w30_work`, erased before the end line.
    Run both drivers (`WP30_ONLY=S25` for the truth script). Append to `<scratch>/25-P1.32-failure.txt` the three `HON-4n measured:` lines and the first failing assert, and the four RG PASS lines as guard truths.
  ]]></action>
  <verify><![CDATA[`grep -c 'HON-4[0-2] measured:' "$S/run_test_setup_honesty.log"` prints 3 and `grep -c 'HON-4[0-2] PASS' "$S/run_test_setup_honesty.log"` prints 0; `grep -cE 'RG-0[1-4] PASS' "$S/run_test_wp30_truth.log"` prints 4 and `grep -c 'ALL CHECKS PASSED' "$S/run_test_wp30_truth.log"` prints 1; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider` reports 0 failed (13 import-probe scripts unchanged).]]></verify>
  <done>dash_setup's capture, retry and report were shown failing on the unmodified tree, and the four Stata facts the design rests on were measured holding.</done>
</task>

<task type="auto" id="25-04">
  <name>Guard the renderer's imports and note versions</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-25.1 and TR-25.2 to dash_render.py with the floor from `$S/floor.txt`: the future-line comment (:61), the docstring's Dependencies lines, `_DASH_MIN_PYTHON`, `_dash_dep_fail`, the version check, the three guarded `try` blocks around :82-118 (each bokeh line indented four spaces, no line otherwise changed), `_DASH_MIN_PACKAGES`, `_dash_dep_versions`, and `_dash_dep_versions` as the last member of `_DASH_ADO_ENTRY_POINTS` (:2553).
    Add `_dash_dep_fail` and `_dash_dep_versions` to `test/function_test_map.py` `FUNCTIONS` under the S25 anchor, alphabetical (TR-25.13).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_dependency_guards.py -q -n0 -p no:cacheprovider -k "Renderer or HealthyImport or VersionNote"` reports 0 failed (the old-interpreter test included); `python3 -m pytest test/test_function_test_map.py test/test_version_floor.py test/test_glyphs.py -q -n0 -p no:cacheprovider -k "not refusals_read_the_constant and not names_the_floor_once and not the_renderer_and_the_app"` reports 0 failed; `python3 -c "import sys; sys.path.insert(0,'.'); import dash_render as d; print(d._DASH_MIN_PYTHON, d._dash_dep_versions())"` prints the floor tuple and `('', '')`.]]></verify>
  <done>The renderer checked the floor and imported numpy, pandas and bokeh inside guards that stopped in one line naming dash_setup, and could name an old numpy or pandas in a note.</done>
</task>

<task type="auto" id="25-05">
  <name>Guard the generated app's header</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    `_generate_app_source` is GitNexus HIGH (impactedCount 5, 3 processes): confirm the orchestrator has the warning recorded in `<scratch>/batch-9-impact.txt` before editing. Apply TR-25.3 to the "1. Header + imports" list only: the future line from `_DASH_MIN_PYTHON`, the three stdlib lines moved up, the comment, the constant, `_dash_dep_fail`'s exact source through `_textwrap.dedent(_inspect.getsource(...))`, the version check, the numpy and pandas guards and one guard around every bokeh and tornado line. Change nothing else in the method.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_dependency_guards.py -q -n0 -p no:cacheprovider -k "ServedApp or HealthyImport"` reports 0 failed; `python3 -m pytest test/test_version_floor.py test/test_server_optional_deps.py test/test_function_test_map.py test/test_resource_limits.py -q -n0 -p no:cacheprovider -k "not refusals_read_the_constant and not names_the_floor_once"` reports 0 failed; `python3 -m pytest test/test_statistical_helpers.py -q -n0 -p no:cacheprovider -k TestTheServedAppCarriesEveryName` reports 0 failed.]]></verify>
  <done>The generated app checked the floor and its packages before any package import and stopped in one line naming dash_setup, as an ImportError under bokeh serve and with exit status 1 as a program.</done>
</task>

<task type="auto" id="25-06">
  <name>Add the standard-library prune slice</name>
  <files>dash_setup_lib.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-25.10 to dash_setup_lib.py: the docstring's first line, `import ast` in alphabetical place, `_SLICES = {}` with its `#:` comment after `_PENDING`, and `stdlib_entry(path, entry)` after `verify_in` with the docstring and the six steps exactly as given, no nested function, 3.8 syntax. Add `"stdlib_entry"` to `SETUP_FUNCTIONS` under the S25 anchor (TR-25.13). Record the closure the slice compiles at this tree: `python3 -c "import ast,sys; sys.path.insert(0,'.'); import dash_setup_lib as L; f=L.stdlib_entry('dash_render.py','_dash_tmp_clear'); print(f is not None, sorted(k for k in f.__globals__ if not k.startswith('__')))" > "$S/25-slice.txt"`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_private_files.py -q -n0 -p no:cacheprovider -k "TestDashClearPrunesWithoutThePackages and not dash_clear_prunes_through_the_slice"` reports 0 failed; `python3 -m pytest test/test_function_test_map.py test/test_setup_pep668.py -q -n0 -p no:cacheprovider` reports 0 failed; `head -c 4 "$S/25-slice.txt"` prints `True`.]]></verify>
  <done>dash_setup_lib compiled dash_render.py's own pruning code with the standard library alone, refused a closure that needed a package, and pruned exactly as the renderer does.</done>
</task>

<task type="auto" id="25-07">
  <name>Add dash's floor constant and guard</name>
  <files>dash.ado, test/program_coverage_map.py, test/test_version_floor.py</files>
  <action><![CDATA[
    In dash.ado, after `_dash_require_python`'s `end` and before S03's `_dash_stata_ok` header, add `_dash_pyfloor` (TR-25.4) and `_dash_require_deps` (TR-25.6) with their headers, `version 19` first in each. Apply TR-25.5 to `_dash_require_python`'s refusal branch. Do not wire the guard yet.
    Add `_dash_pyfloor` and `_dash_require_deps` to `COVERAGE["dash.ado"]` under the S25 anchor (TR-25.13). Flip `test_every_declaration_agrees_with_dash_setup`'s dash.ado assertion as "TDD test stubs" gives it, recording the `Flipped:` line in `$S/25-flips.txt`.
    Create `$S/p25c.do` (adopath and dash_nobrowser lines first; `qui do "$WT/dash_parse.mata"`, `qui do "$WT/dash.ado"`), which runs `capture noisily _dash_require_deps` and displays `P25C rc=` and `_rc`, then patches `sys.version_info` to `(3, 6, 15, "final", 0)` with the original kept in a Python variable, runs it again, restores, and displays `P25C old rc=` and `_rc`. Run it through the slot.
  ]]></action>
  <verify><![CDATA[`grep -c 'P25C rc=0' "$S/p25c.log"` prints 1 and `grep -c 'P25C old rc=198' "$S/p25c.log"` prints 1, and the log holds `is linked to Stata` and `dash_setup`; `python3 -m pytest test/test_version_floor.py test/test_program_coverage_map.py test/test_cscript_hygiene.py test/test_security_surface.py test/test_file_headers.py -q -n0 -p no:cacheprovider` reports 0 failed (`test_no_orphans.py` waits for 25-08: `_dash_require_deps` has no caller yet); `python3 -m pytest test/test_dependency_guards.py -q -n0 -p no:cacheprovider -k test_the_guard_decides_from_values` passes.]]></verify>
  <done>dash.ado held the floor once and a guard that read Python's start, version and packages as values and refused r(198) in words naming dash_setup.</done>
</task>

<task type="auto" id="25-08">
  <name>Wire the guard and the stdlib prune</name>
  <files>dash.ado, test/test_env_guards.cscript, test/test_string_value_export.py</files>
  <action><![CDATA[
    Apply TR-25.7 (the `dash` paragraph after `_dash_require_mata` and before S12's strip paragraph; `_dash_require_deps` in `_dash_do_render` and `_dash_xm_load`), TR-25.8 (the captured load decided by `_dd_err`, then `_dash_dep_versions`' refusal and note) and TR-25.9 (`_dash_tmp_clear` through `stdlib_entry`) to dash.ado. Edit no other program.
    In `test/test_env_guards.cscript` flip ENV-12 in place: print its list at this tree first; the literal gains `_dash_require_deps` as its first word, and any other difference stops the task; add one comment line `// Flipped (WP-30 P1.32): _dash_require_deps runs python: (its two captured lines) and joins the list.` Flip `test/test_string_value_export.py`'s entry-point test as "TDD test stubs" gives it. Record both `Flipped:` lines in `$S/25-flips.txt`.
  ]]></action>
  <verify><![CDATA[Through the driver, `test_env_guards.cscript` prints `ENV-30 PASS` through `ENV-39 PASS` and `All environment guard tests PASSED.`; `python3 -m pytest test/test_dependency_guards.py test/test_private_files.py test/test_string_value_export.py test/test_version_floor.py test/test_program_coverage_map.py test/test_no_orphans.py test/test_cscript_hygiene.py test/test_security_surface.py -q -n0 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every dash command but dash clear ran the dependency guard after the Mata guard, the renderer load refused by value with the renderer's own line, and dash clear pruned through the standard-library slice.</done>
</task>

<task type="auto" id="25-09">
  <name>Capture dash_setup's first Python call</name>
  <files>dash_setup.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-25.11 to dash_setup.ado: `_dash_setup_pystart` after `_dash_pyver_ok`'s `end`, and :92 replaced by the call, the `pyver` local and the not-started branch exactly as given. Change nothing else in `dash_setup`. Add `_dash_setup_pystart` to `COVERAGE["dash_setup.ado"]` under the S25 anchor.
  ]]></action>
  <verify><![CDATA[Through the driver, `test_setup_honesty.cscript` prints `HON-40 PASS`, `HON-41 PASS`, `HON-42 PASS` and `All dash_setup honesty tests PASSED.`; `test_program_coverage.cscript`, `test_setup_python_gate.cscript` and `test_setup_version_gate.cscript` report no FAIL; `python3 -m pytest test/test_cscript_hygiene.py test/test_program_coverage_map.py test/test_no_orphans.py test/test_setup_pep668.py -q -n0 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>dash_setup captured and retried its first Python call and reported a Python that could not start in its summary, with the path shown as typed and the processor rule, before any process started.</done>
</task>

<task type="auto" id="25-10">
  <name>State the guard in both help files</name>
  <files>dash.sthlp, dash_setup.sthlp</files>
  <action><![CDATA[
    Apply TR-25.14: the new `{pstd}` paragraph in dash.sthlp's Dependencies (after the packages list, before the PEP 668 paragraph), the sentence in dash_setup.sthlp's step 1, and the Troubleshooting entry "Python could not be started" after "Python not found". Keep every phrase `test_every_declaration_agrees_with_dash_setup` reads. No tool or vendor is named.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_version_floor.py test/test_help_claims_8.py test/test_help_examples.py -q -n0 -p no:cacheprovider` reports 0 failed (each file that exists); `grep -c 'every {cmd:dash} command but {cmd:dash clear}' dash.sthlp` prints 1; `grep -c 'could not be started' dash_setup.sthlp` is at least 2; `grep -Eic 'claude|anthropic' dash.sthlp dash_setup.sthlp` prints 0 for each.]]></verify>
  <done>Both help files stated what dash and dash_setup check, what they say when a dependency is missing, and that dash clear needs none of it.</done>
</task>

<task type="auto" id="25-11">
  <name>Run the section's checks in the worktree</name>
  <files>none</files>
  <action><![CDATA[
    Run `python3 -m pytest test/test_dependency_guards.py test/test_version_floor.py test/test_private_files.py test/test_string_value_export.py test/test_function_test_map.py test/test_program_coverage_map.py test/test_statistical_helpers.py test/test_resource_limits.py test/test_cscript_hygiene.py test/test_mode_parity.py test/test_varlist_expansion.py test/test_server_optional_deps.py test/test_no_orphans.py test/test_security_surface.py -q -n0 -p no:cacheprovider > "$S/25-11-pytest.log" 2>&1`.
    Run the drivers for `test_env_guards.cscript`, `test_setup_honesty.cscript`, `test_program_coverage.cscript`, `test_clear_registry.cscript`, `test_render_locate.cscript`, `test_json_escaping.cscript` and (`WP30_ONLY=S25`) `test_wp30_truth.cscript`. Afterwards `~/.stata19/console/stata19.rc` must still hold the maintainer's `python_exec` (E12 of index): compare its hash with the one taken before the first run.
  ]]></action>
  <verify><![CDATA[`grep -E ' passed| failed' "$S/25-11-pytest.log" | tail -1` shows 0 failed and no new skip; each cscript log ends with its own all-passed line and holds no `FAIL` and no new `SKIP`; the `stata19.rc` hash is unchanged.]]></verify>
  <done>The changed tests, the registries, the parity corpus, the page digest and every cscript the section touches were green in the worktree.</done>
</task>

<task type="auto" id="25-12">
  <name>Close P1.32 and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP30_OPEN["P1.32"]`. Close that BUGS.md entry in place: `- [x]`, and the Resolution line of Notes "BUGS.md Resolution" with today's date and the tests that exist. Delete only the `"P1.32"` key line of `WP30_OPEN`. Replace the one `<!-- WP-30 P1.32 -->` marker under `### Requirements` in place with the CHANGELOG line of Notes; add nothing elsewhere.
    Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`; stop and report otherwise), and one full run through the queue: `<scratch>/full_suite_queue.sh "$WT" <scratch>/25-full-1.log`, launched in the background and waited for on its `exit=` line (E1; E6 for the known flaky tests).
    Check scope: `git -C "$WT" status --porcelain` lists only the files of tasks 25-01..25-12 (`test/dep_block.py` new); no `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.ultraplan/`, `.gitnexus/`, scratch file or `*.html`. Write the message to `$S/msg.txt` (Notes "Commit body"), run G7 (`grep -Eic 'claude|anthropic' "$S/msg.txt"` prints 0), confirm `git -C "$WT" branch --show-current` prints `wp30-s25`, `git -C "$WT" add` the files by name, commit with `git -C "$WT" commit -F "$S/msg.txt"`, and run G7 on `git -C "$WT" log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`grep -c '^exit=0' <scratch>/25-full-1.log` prints 1 and the log shows 0 failed; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` reports 0 failed; `grep -c '<!-- WP-30 P1.32 -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.32": "' test/test_tracking_documents.py` prints 0; `grep -c '(WP-30, P1.32)' CHANGELOG.md` prints 1; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.32)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.32 was closed with its tests named, its CHANGELOG line written in place, and the section's one commit made on wp30-s25 after a green full run.</done>
</task>

## Section completion criteria

- All 30 pytest regression nodes of 25-01 pass (29 and a recorded skip where the old interpreters are absent); `TestTheBlockHelper` passes.
- `test_env_guards.cscript` prints ENV-30..ENV-39 PASS; `test_setup_honesty.cscript` prints HON-40..HON-42 PASS; `test_wp30_truth.cscript` with `WP30_ONLY=S25` prints RG-01..RG-04 PASS and `ALL CHECKS PASSED`; no new SKIP anywhere.
- The three pinned tests are flipped with `Flipped:` lines, none deleted; `len(with_probes) == 13` unchanged.
- `function_test_map.py` holds `_dash_dep_fail`, `_dash_dep_versions` and `stdlib_entry`; `program_coverage_map.py` holds `_dash_pyfloor`, `_dash_require_deps` and `_dash_setup_pystart`; no copy-list entry was added.
- One commit on `wp30-s25`, subject ending `(WP-30 P1.32)`, after one green full run; BUGS.md entry closed in place; its `WP30_OPEN` key gone; its Requirements marker replaced; G7 prints 0 before and after.
- At landing, `gitnexus detect-changes --scope all --repo dash` names only this section's symbols (`_dash_dep_fail`, `_dash_dep_versions`, `_DASH_MIN_PYTHON`, `_DASH_MIN_PACKAGES`, `_DASH_ADO_ENTRY_POINTS`, `ServerAppBuilder._generate_app_source`, `stdlib_entry`, `_SLICES`, the dash_render.py module node and the test functions).

## Notes

**Traps.**
1. **The cached renderer.** `_dash_xm_load` reuses `sys.modules["_dash_render_export"]` when the file's key matches, so blocking `numpy` alone in a session that has rendered changes nothing at the load. `dep_block.block` always takes the renderer out and `restore` puts the same object back; ENV-36 uses `forget_renderer()` for the same reason.
2. **SystemExit is rc 0 inside Stata** (RG-01, research m3). Never raise it where `sfi` is loaded; `_dash_dep_fail` decides by `sys.modules.get("sfi")`.
3. **`sfi.Macro.setLocal` lands in the program running the `python:` line** (RG-03): `_dd_err` is set in `_dash_xm_load` (or `_dash_do_render`), which is why the load decides there.
4. **The slice's layout rule.** Package imports stay inside top-level `try` blocks and nothing else in dash_render.py may be a package import at top level; a pruning helper must not reuse a name a package import binds (`row`, `column`, `Span`, `Div` …), even as a local, or `stdlib_entry` refuses and `test_the_slice_prunes_as_the_renderer_does` fails.
5. **No captured import line in a cscript.** `_import_probes` counts `capture python:` lines containing `import`; every helper line in ENV/HON/RG is an uncaptured `python:` line, so the pin at test_cscript_hygiene.py:322 stays 13 (R1, R10).
6. **Restore before asserting.** Each case puts Python back before any `assert`; an assert that fails with numpy blocked would break every later script in the runner.
7. **Never `set python_exec`.** An old or unstartable Python is simulated in-process (`fake_version`, `block("sfi", …)`), never by linking another interpreter (index E12).
8. **`c(os)` is `Unix` on this Mac** (E11): recognise a Mac from `c(machine_type)` only.
9. **The `dash` insertion point** at the batch-9 base: after the `_dash_require_mata` statement and its comment; S12's comment paragraph and `mata: _dash_strip_prefix()` come right after; S22's dispatch later still. Edit no line of theirs (A154, R6).
10. **The floor.** Every `<FLOOR>`, `(<FMAJ>, <FMIN>)` and needle reads `$S/floor.txt`; never type 3.11 from memory (PLAN K15).

**Shared files and merge rules.** R1: ENV-30..39 one contiguous run after S03's ENV-29 in `test_env_guards.cscript` (S03 in batch 1, S25 in batch 9); HON-40..42 after S05's HON-32; ENV-12 flipped in place; RG cases inside S25's own block with `_s25_scope` above its header; no runner or hygiene pin moves. R2: no copy-list entry; map keys only under the S25 anchors (FUNCTIONS, SETUP_FUNCTIONS, `COVERAGE["dash.ado"]`, `COVERAGE["dash_setup.ado"]`). R3: dash.sthlp Dependencies and dash_setup.sthlp step 1 and Troubleshooting only. R4: the one Requirements marker. R5: the one entry and its one key line. R6: every new program opens `version 19`; A154's order. R10: no combined pin moves (with_probes 13; the single-y digest unchanged). R12: `_generate_app_source` is edited by S25 alone in batch 9.

**Commit body** (A141, S01 TR-01.10 item 7). Opens with the text of `<scratch>/25-P1.32-failure.txt`; then the defect (the Overview's four measured symptoms); then what changed and where (TR-25.1-25.11 in one paragraph each sentence); then:
- `Regression: test/test_dependency_guards.py::TestTheRendererRefusesWithTheRemedy::test_a_missing_package_is_one_line_naming_dash_setup -- failed at <batch-9 base sha> with <its line>`, one such line per regression node of 25-01, and `Regression: test/test_env_guards.cscript ENV-3n -- failed at <sha> with <measured line>` for ENV-30..38, and the same for HON-40..42;
- `Flipped:` lines from `$S/25-flips.txt` (three);
- `Fixture: none (Stata facts measured live: test_wp30_truth.cscript RG-01..RG-04)`;
- `BUGS.md: "A missing numpy, pandas or bokeh or an old Python fails with a bare ModuleNotFoundError or SyntaxError, and dash_setup's first Python call is uncaptured" (closed)`.

**BUGS.md Resolution** (one line, in place): `  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.32). Every dash command but dash clear runs _dash_require_deps (dash.ado) after the Mata guard: it starts the linked Python (a first failed call retried once) and reads its version and the packages' presence by value, and refuses r(198), naming c(python_exec) and dash_setup, a Python that cannot start (with the processor rule on a Mac), one below _dash_pyfloor, or a missing numpy, pandas or bokeh; _dash_xm_load runs it, captures the renderer's load and refuses r(198) with the renderer's own line when an import fails, and notes numpy or pandas below dash_setup's minimum once per load (_dash_dep_versions). dash_render.py and the generated app's header (ServerAppBuilder._generate_app_source) check _DASH_MIN_PYTHON and import numpy, pandas and bokeh inside guards that stop in one line naming dash_setup through _dash_dep_fail, an ImportError with the line in _dd_err under Stata or bokeh serve and exit status 1 run as a program, so the saved page, dash build, server, dash serve's child and an app run by hand all name the remedy; the future line names the floor for a Python older than 3.7. dash clear prunes through dash_setup_lib.stdlib_entry, which compiles dash_render.py's own _dash_tmp_clear and what it reaches with the standard library only. dash_setup captures its first Python call (_dash_setup_pystart), retries it once, and reports a Python that cannot start in its summary with its path and the processor rule, r(198). Pinned by test/test_dependency_guards.py::TestTheRendererRefusesWithTheRemedy::test_a_missing_package_is_one_line_naming_dash_setup, test/test_dependency_guards.py::TestTheServedAppGuardsItsImports::test_the_app_refuses_a_missing_package_in_one_line, test/test_dependency_guards.py::TestTheVersionNote::test_numpy_or_pandas_below_the_minimum_is_noted, test/test_version_floor.py::TestThePythonFloorIsOneNumber::test_the_renderer_and_the_app_hold_the_same_floor, test/test_private_files.py::TestDashClearPrunesWithoutThePackages::test_the_slice_prunes_as_the_renderer_does, test/test_env_guards.cscript ENV-31, ENV-32, ENV-33, ENV-34, ENV-35, ENV-37, ENV-38, test/test_setup_honesty.cscript HON-40, HON-41. Residual, deferred (WP-30): a renderer or app run by hand prints no numpy/pandas version note (Stata's routes do); a Python older than 3.7 run by hand still stops with a SyntaxError, whose shown line carries the remedy; the processor hint is measured on Apple Silicon only (the platform package, P1.34.6).`

**CHANGELOG line** (replaces `<!-- WP-30 P1.32 -->` under `### Requirements`, one item, `<FLOOR>` filled):

```markdown
- Python and its packages are checked before a dash command starts. Every command but `dash clear` stops with r(198) and one message naming what is missing, the Python it looked in and `dash_setup` when the linked Python cannot be started, is older than <FLOOR>, or lacks numpy, pandas or bokeh or has one that fails to import; it used to stop with r(7102) and a Python traceback (`ModuleNotFoundError: No module named 'numpy'`) that named no remedy. A registration such as `dash scatter mpg weight, name(g1)` is now refused the same way. numpy or pandas below `dash_setup`'s minimum is named in a note and the command goes on. `dash serve` and a dashboard app run by hand (`python app.py`, `bokeh serve`) stop with the same one line instead of a traceback. `dash_setup` tries a first Python call that fails once more and reports a Python that cannot be started, with its path and, on a Mac, the processor it must be built for, instead of stopping before its summary. `dash clear` prunes dash's temporary files with the packages missing. (WP-30, P1.32)
```

**Notes for the closeout (S58; A145).**
- **GAPS2.md H6** (:1537-1543): `- **Tracked:** Closed in WP-30, BUGS.md "A missing numpy, pandas or bokeh or an old Python fails with a bare ModuleNotFoundError or SyntaxError, and dash_setup's first Python call is uncaptured", commit <sha>`, and `(WP-30, GAPS2-H6)` appended to the Resolution. The sub-ids H6a-H6d are the research note's (p1-32.md §1), not GAPS2's; all four are closed by this commit.
- **ROADMAP.md WP-07**: BR-07.1 ("Every external dependency is verified before use, with a message naming the remedy") is now met for the Python version and the three packages; BR-07.2 ("availability is probed without running Python") still holds (`c(python_exec)` decides availability; the guard runs native `python:` only once Python is configured).
- **DROPIN-REMAINING.md** P1.32 row (:166): closed, with the commit.
- **AGENTS.md** invariants: every `dash` command but `clear` runs `_dash_require_deps` right after the Mata guard; dash_render.py and the generated app import packages only inside top-level `try` blocks that call `_dash_dep_fail`, and the standard library outside them; `dash clear` prunes through `dash_setup_lib.stdlib_entry`; `_dash_pymin`, `_dash_pyfloor` and `_DASH_MIN_PYTHON` are one number.
- **Residuals to file:** the hand-run version note and the pre-3.7 SyntaxError (P2, low), the processor hint off Apple Silicon (platform package P1.34.6). P2.40 keeps its text, adding that its failure now ends in one line naming `dash_setup`.
- **For S41:** the refusal slot is `_dash_dep_versions()[0]`, read on every load by `_dash_xm_load`; the app header's guarded imports end before S41's start-up check; `TestThePythonFloorIsOneNumber` and `TestTheVersionNote` are the pins to keep.
