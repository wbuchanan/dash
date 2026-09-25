# Section 09: Serve launcher and version floor (F1, K2)

> Part of: WP-28 · Gaps: F1, K2 · Risk: red · Batch: 1 · Depends on: none · Blocks: 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **1** · Depends on **none** · Blocks **19** · Risk **red** · Commits: two commits: F1 → CHANGELOG `Fixed in WP-28`; K2 → `Requirements`

- D9: risk is red (child-process plumbing, three refusal sites plus the embedded `_port` road, inverted tests).
- D10: forwarded child stdout/stderr is bounded (last 20 lines, ≤ 4 KB); `communicate()` cannot serve the poll — reader threads, as the section says.
- Q27: on a below-floor Bokeh, dash_setup refuses and prints the exact `<c(python_exec)> -m pip install 'bokeh>=3.8'` line; it never installs; a cscript asserts the printed command names `c(python_exec)`.
- D7: split 09-01 and 09-03.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

**F1, today.** `dash serve` reports success when no server ran. GAPS2 measured it: "Probe with
the port held by another socket: rc 0 after 1.7 s. The only trace was the child's `OSError:
[Errno 48] Address already in use` on process stderr, which never reaches Stata." The launcher
(`dash_render.py:27670-27715`) starts the generated app with `Popen(_cmd)` and `wait()`s, never
reads `returncode`, and nothing tests the port first; both routes default to 5006, "so a leftover
`app.py` makes a new `dash serve` 'succeed' while the browser shows the old dashboard".
Separately, "`python app.py --port 80` serves on 1024 because of the clamp at
`dash_render.py:27371`" — and there are two more clamps, in `main()` (27603) and in the launcher
(27680). After this section: `dash serve, port(N)` against a held port returns r(198) with one
line, `dash serve: no server started on port N: the port is in use`; any other non-zero exit of
the app is reported with its status and the app's last error lines; the launcher polls the
app's own `/health` for up to 30 s and prints the address only once it answers; and every
`--port` outside 1024-65535 is refused with a message, at all three sites, never moved.

**K2, today.** "`dash_setup.sthlp:70`, `dash.pkg:17` and `dash_setup.ado:60,73,146` declare and
enforce Python 3.8+ and bokeh>=3.0." But "every render, saved or served, imports `CustomJSTicker`
… That class exists only from Bokeh 3.6", so "an installed Bokeh 3.0-3.5 passes dash_setup, and
then every dash command fails with r(7102)"; and "the generated served app lacks `from
__future__ import annotations` and has 55 annotations Python evaluates at import … It raises
TypeError on 3.8 and 3.9." No test runs below Python 3.13 or Bokeh 3.8. DISCOVERY Q8 settles
the floor as *what is tested today*: the `stata` baseline of `test/conftest.py:207-209` —
**Python 3.13, bokeh 3.8, pandas 2.3, numpy 2.3** — declared in every place report C §6 lists,
with pandas declared by dash itself because Bokeh 3.9 dropped it as a dependency (report W §1h),
and the generated app opening with `from __future__ import annotations`.

**Why one section.** Both gaps live on the serve/setup surface and nowhere else: the launcher
and the app template's header and `__main__` in `dash_render.py`, `_dash_serve` and
`_dash_require_python` in `dash.ado`, and `dash_setup.ado`. K2's step 4 ("check
`_proc.returncode` in the launcher") *is* F1's step 1, so the two fixes share one function. No
other batch-1 section touches these regions (the one shared edit point is the served-app copy
list; see Notes).

**Test order (CLAUDE.md rule 7).** Task 09-01 writes every failing pytest and the failing
cscript; 09-02 registers the cscript and records its failure. 09-03 to 09-06 close F1;
09-07 to 09-12 close K2. The suite is red between 09-03 and 09-04 only for the three clamp
tests being inverted, and green from 09-06 on.

## Risk: [yellow] — the launcher runs inside Stata's embedded Python, where an escaping exception is r(7102) and a thread must never print; Ctrl+C must still stop the child; three tests require the clamp and five scripts assert the old floor

**Why.** The behaviour to change sits on a process boundary (Stata → its Python → a child) and
the failure must travel back across it as text, not as an exception. The port clamp is pinned
by `test_render_cli_port.py`, `test_resource_limits.py` and the adversarial registry; the old
minimums are asserted by four cscripts and one pytest.

**Risk factors.**
1. A `RuntimeError` escaping `runpy.run_path` inside `python:` is r(7102) plus a traceback —
   the opposite of the clean message required (GAPS2 F1, report C §5).
2. The child's stdout and stderr become pipes; a pipe nobody drains blocks the server once it
   fills (Bokeh logs every session to stderr).
3. Under Stata, output written from a non-main thread may never reach the Results window.
4. macOS lets a wildcard bind succeed beside a loopback listener; a test that holds the wrong
   address passes for the wrong reason (report W §5).
5. A pre-bind test without `SO_REUSEADDR` refuses a port in TIME_WAIT that the real server
   (Tornado sets `SO_REUSEADDR`) would bind: a false refusal right after a restart.
6. Renaming a test that the adversarial registry names fails the registry's meta-tests
   (`test_adversarial_matrix.py:943-1000`, every node id must resolve).
7. The served app imports `argparse as _argparse`; a copied helper that says `argparse.…`
   is a NameError in the app.

**Mitigation.** A shared dict handed through `runpy`'s `init_globals` carries the failure text
back (TR-09.3/09.4); daemon reader threads drain both pipes into a bounded buffer and only the
main thread prints (TR-09.2); the cscript holds `127.0.0.1`, the address the app binds
(`dash_render.py:27320`), and listens; the tester socket sets `SO_REUSEADDR`; every renamed test
is renamed in the registry in the same commit; the copied helper imports `argparse` locally.

## Dependencies
- Depends on: none
- Blocks: section-19 (closeout: CHANGELOG consolidation, GAPS2 Tracked lines, release gate)
- Parallel batch: 1
- Can run with: sections 01-08 and 10. Their `dash_render.py` regions (formatters, axes,
  legends, filters, the served layout CSS) and `dash.ado` regions (export, varlists, names) are
  disjoint from the launcher, the app header/`__main__`, `_dash_serve`, `_dash_require_python`
  and `dash_setup.ado`.

## Evidence

All anchors at `91d97be` (RESEARCH: no source file changed since the audit).

### F1.1 The launcher never reads the exit status — `dash_render.py:27670-27715`

```python
27680        _port = max(1024, min(args.port, 65535))
   …
27692        _cmd = [
27693            _sys.executable, args.output,
27694            "--port", str(_port),
27695        ]
   …
27701            _proc = _sp.Popen(_cmd)
27702        except FileNotFoundError:
   …
27709            raise SystemExit(1)
27710
27711        try:
27712            _proc.wait()
27713        except KeyboardInterrupt:
27714            _proc.terminate()
27715            _proc.wait()
```

No pipes: the child's stderr is Stata's process stderr. `returncode` is never read. The
`FileNotFoundError` branch raises `SystemExit(1)`, which under Stata is also an escaping
exception. `_time`, `_threading` and `_wb` are imported at 27674-27676 and unused.

### F1.2 Three clamps, and the road argparse does not guard

- CLI parser, `dash_render.py:27625-27630`: `parser.add_argument("--port", type=int,
  default=5006, …)`. No range.
- `main()`, 27603: `builder.build(output_path, port=max(1024, min(int(port), 65535)))`.
- Launcher, 27680 (above); unreachable from `dash serve`, which refuses the range first
  (`dash.ado:7307-7310`), but reachable from `python dash_render.py --launch`.
- App template `__main__`, 27371: `_port = max(1024, min(int(_a.port), 65535))`.
- App template `_dash_arg_parser`, 25614: `p.add_argument('--port', type=int, default=_port, …)`.
  **argparse applies `type=` to string input only, never to a non-string default**, so an
  embedded `_port = 80` (from `build_options["port"]`, read with `int()` alone at
  24950-24955 and taking precedence over `main()`'s port) passes the parser untouched.
- The refusal pattern to copy is the app's own `_dash_limit_value`, 25594-25606: ASCII digits
  only, then range, then `raise _argparse.ArgumentTypeError('%r is not an integer from 1 to
  1,000,000' % (s[:40],))`.

### F1.3 The Stata side — `dash.ado`

`_dash_serve`, 7349-7439:

```stata
7421    display as text "dash serve: starting Bokeh Server on port `port_int'." ///
7422        "  Stata is blocked until the server stops (Ctrl+C)."
   …
7425    python: import sys, runpy
   …
7430    python: sys.argv = ["dash_render.py", "--spec", "`_py_master'", … "--port", "`port_int'", "--timeout", "`timeout'"]
7431    if "`no_browser_flag'" != "" {
7432        python: sys.argv.append("--no-browser")
7433    }
   …
7438    python: _dash_serve_ns = runpy.run_path("`_py_render'", run_name="__main__")
```

Nothing after 7438 reads anything. A `python:` inside an ado program takes one statement per
line and no compound statement (the comment at 4192-4193), so a `try/except` cannot be written
here. The pattern that does work is `_dash_write_data`, 4212-4216:

```stata
4212    python: _dash_M.setLocal("_dw_err", _dash_xm._dash_write_stata_data(…))
4213    if `: length local _dw_err' {
4214        mata: _dash_say("err", st_local("_dw_err"), "", "")
4215        exit 198
4216    }
```

`_dash_say(style, before, value, after)` (`dash_parse.mata`, ~584) prints one line as literal
text through `_dash_smcl_text`, so nothing in the message is read as SMCL. `_dash_serve_spec`
(7252-7345) already refuses a non-digit port (7299-7303) and one outside 1024-65535
(7307-7310, r(198)); `timeout()` is in **minutes** (7311-7315).

### F1.4 What the app offers: `/health`, loopback, and prints nobody sees

- `_HealthHandler`, template lines 25563-25582: `GET /health` → 200
  `{"status": "ok", "timestamp": …}`; `prepare()` returns 429 when `_HEALTH_LIMITER`
  (`_HEALTH_LIMIT_RPM = 600` per IP per minute, 25330) refuses. It is registered by
  `_dash_server_app` (27296-27355) through `extra_patterns=[('/health', _HealthHandler)]`
  (27353), which only the self-serving launcher has; `bokeh serve` has no such route (W §5).
- `_kw = {'address': address or '127.0.0.1'}` (27320): with no `--address` the app binds
  loopback, and the launcher passes none.
- The app prints `Bokeh Server running at http://localhost:{_port}/`, `Health check: …`, the
  session limits and `Press Ctrl+C to stop.` at 27408-27412 **to its own stdout**, and the
  `BOKEH_ALLOW_WS_ORIGIN` warnings at 27381-27395 likewise. None of it reaches the Results
  window today.
- A normal stop exits 0: `except KeyboardInterrupt: pass`, then `finally: _server.stop()`
  (27417-27423); `--timeout N` stops the loop after N minutes (27405-27407), also exit 0.

### F1.5 Platform facts (report W §5, measured on this machine)

- A bare `Server(...)` (what the app builds) has no port handler: `bind_sockets` raises
  `OSError`, errno **48** on macOS, **98** on Linux, text `Address already in use`; an
  uncaught exception ends the interpreter with status 1. (`bokeh serve` would print `Cannot
  start Bokeh server, port N is already in use` and exit 1; the app is not run that way.)
- Holder on `127.0.0.1:P`: `Server(port=P, address="127.0.0.1")` → rc 1. **But `Server(port=P)`
  with the wildcard address starts** beside it on macOS (BSD allows a wildcard bind beside a
  specific one when the new socket sets `SO_REUSEADDR`, which Tornado does). So the fixture
  must hold **the address the app binds**, `127.0.0.1`, and must `listen()` — the measured
  case is a listening holder.
- A pre-launch `socket.bind(("127.0.0.1", port))` raises `EADDRINUSE` when held; it is
  inherently racy, so the child's exit status stays the authority.
- **Reasoned, not measured, from the BSD and Linux bind rules — the executor verifies it in
  09-03's verify step:** a tester socket *without* `SO_REUSEADDR` also fails against a port
  whose last connections are in TIME_WAIT, which Tornado's `SO_REUSEADDR` server would bind;
  a tester *with* `SO_REUSEADDR` ignores TIME_WAIT and still fails against a live listener on
  the same address and port on both platforms. The tester therefore sets `SO_REUSEADDR`.
- Readiness: after `Bokeh app running at:` the first `GET` of `/health` answers within a
  second on this machine; 30 s is generous.

### F1.6 Existing tests that pin today's behaviour (flip, never delete)

| test | pins | becomes |
|---|---|---|
| `test/test_render_cli_port.py::TestPortReachesTheGeneratedApp::test_an_out_of_range_port_is_clamped_not_embedded_raw` (151) | `main(port=99999/80)` embeds 65535/1024 | `…::test_an_out_of_range_port_is_refused_not_embedded`: `main(port=80)` and `70000` raise, no file written |
| `…::test_an_out_of_range_port_in_build_options_is_clamped_too` (160) | `build_options["port"]="80"` binds 1024 | `…::test_an_out_of_range_port_in_build_options_is_refused_too`: `main()` raises, no file written |
| `test/test_resource_limits.py::TestTheBoundsThatAlreadyWorkedAreKept::test_the_port_is_clamped_in_every_place_it_is_read` (1278, parametrised `(99999,65535),(80,1024)`, driving `main()`, the app's `--port` with `bokeh.server.server.Server` replaced, and the launcher with `Popen` replaced) | all three sites clamp | `…::test_the_port_is_refused_in_every_place_it_is_read`, parametrised over `80` and `70000`: `main()` raises `argparse.ArgumentTypeError`; the app exits 2 and constructs no `Server`; the launcher exits 2 and calls no `Popen`; each message names 1024 and 65535 |
| `test/test_adversarial_matrix.py` registry lines 860 (`served_app_cli_flags` / exhaustion) and 878 (`renderer_cli` / exhaustion) | name the first test above | renamed to the new node id in the same commit (the registry meta-tests resolve every node id) |
| `test/test_help_claims_2.py::_FakeProc` (756-764: `__init__(self, cmd)`, `wait()` only) and `TestTheLauncherBehindDashServe` (767-808, `_launch` at 781 with `--port 5123`) | `Popen(cmd)` positional, no `returncode` | `_FakeProc(cmd, **kw)` with `returncode = 0`, `stdout`/`stderr` empty text streams, `poll()`, `wait()`, `terminate()`, `communicate()`; `_launch` takes a free port |

Real launches that must stay green untouched: `test/test_help_claims_1.py:576
TestServeBlocksUntilCtrlC`, `test/test_help_claims_5.py:1348
TestServingBlocksUntilInterrupted`, `test/test_help_claims_4.py:1315 TestTheRealHandoffServes`
(all poll `/health`, then SIGINT), `test/test_help_claims_4.cscript HC4-19..21` (a real
`dash serve, timeout(1)`, rc 0 after ≥ 50 s, `/health` 200 seen by a thread started in Stata's
Python — proof that a thread inside Stata's Python works when it only stores state),
`test/test_serve_launch.cscript SRV-17..20` and `test/test_serve_browser.cscript` (stub
`dash_render.py` first on the ado-path, run by `runpy` with `run_name="__main__"`),
`test/test_adversarial_matrix.py::TestRendererOutputPath::test_the_launcher_runs_the_app_without_a_shell`
(AST walk: a `Popen` call exists and none says `shell=True`).

### K2.1 Where the old minimums appear (report C §6)

| file | lines | text |
|---|---|---|
| `dash_setup.ado` | 44-45 | `_dash_pymin` read into `c_pymin` before any message |
| | 60 | `"Please install Python 3.8+ and link it to Stata:"` |
| | 73 | comment "verifies Python 3.8+" |
| | 146, 147, 150 | `local min_bokeh "3.0"`, `min_numpy "1.23"`, `min_pandas "2.0"` |
| | 285-296 | `_dash_pymin` returns `"3.8"` (295) |
| `dash_setup.sthlp` | 40-42 | "compared with the 3.8 minimum … below 3.8" |
| | 70 | "Python 3.8 or later" |
| | 80-82 | `{opt bokeh}}3.0 or later`, numpy 1.23, pandas 2.0 |
| | 97-98 | the manual pip line, bare names |
| | 110-113 | "one below 3.0 is reported as an unmet requirement" |
| `dash.pkg` | 17 | `d Requires: Python 3.8+, bokeh>=3.0, numpy>=1.23, pandas>=2.0.` |
| `dash.ado` | 205-207 | `_dash_require_python`: "link Stata to Python 3.8+" |
| `dash.sthlp` | 3131-3134 | `{ul:Python 3.8+}`; "bokeh>=3.0, numpy>=1.23, pandas>=2.0" |
| `CHANGELOG.md` | 330-334 | `### Requirements` |

`dash.ado` cannot call `_dash_pymin`: it is a subprogram of `dash_setup.ado`, which Stata loads
only when `dash_setup` itself runs. The number is written in `dash.ado` and tied to
`dash_setup.ado` by a test (TR-09.11).

### K2.2 The measured floor (report C §6, RESEARCH "Stack measured")

| interpreter | Python | bokeh | pandas | numpy |
|---|---|---|---|---|
| Stata's `c(python_exec)` = `/opt/anaconda3/bin/python3` (`~/.stata19/console/stata19.rc`: `pyver_64 3.13.9`) | 3.13.9 | 3.8.0 | 2.3.3 | 2.3.5 |
| development `python3` (`make test-dev`) | 3.14.5 | 3.9.0 | 3.0.1 | 2.4.3 |

`test/conftest.py:207-209`:

```python
    "stata": {"python": "3.13", "bokeh": "3.8", "pandas": "2.3",
              "numpy": "2.3", "scipy": "1.16"},
```

**Floor to declare: Python 3.13, bokeh 3.8, numpy 2.3, pandas 2.3.** Bokeh's own floors (W §1h):
3.0-3.1 need Python ≥ 3.8, 3.2-3.4 ≥ 3.9, 3.5-3.9 ≥ 3.10, 3.10.0 ≥ 3.12; `CustomJSTicker`
since 3.6.0; Bokeh 3.9.0 "Removed `pandas` as a required dependency", so dash's own pandas floor
is the only one there is; pandas 3 with Bokeh 3.8 is a combination Bokeh never tested.

### K2.3 The generated app's header — template lines 25198-25222

```python
25198        lines += [
25199            '"""',
25200            '# Auto-generated Bokeh Server dashboard — do not edit manually.',
   …
25204            '"""',
25205            "",
25206            "import argparse as _argparse",
   …
25216            # GlyphMapper's signatures annotate with Any, Callable and List.
25217            # Annotations are evaluated when the class body runs on any
   …
25222            "from typing import Any, Callable, Iterable, List",
```

No `from __future__ import annotations` (dash_render.py itself has one at line 61). A future
statement may follow only the docstring, comments and blank lines (W §3); measured there: on
3.8 `list[int]` and `int | None` both raise at import, on 3.9 only `|`, and with the future
import both import cleanly on 3.8 and 3.9.

### K2.4 `CustomJSTicker`

Imported at `dash_render.py:16877` and 17217 (inside `_dash_count_axes`, reached by
`_dash_finish_count_ticks` on every render). Present from Bokeh 3.6.0. **No change once the
floor is 3.8.**

### K2.5 How dash_setup is driven without installing anything

- `test/setup_sandbox.py::install(block=(), unblock_on_install=(), fake=(), pyversion=None)`:
  `fake` is `(name, version)` pairs written as fake `.dist-info` distributions (what
  `_dash_pkg_version` reads); `pyversion` replaces `sys.version`. Driven from Stata by
  `_pc_setup` (`test_program_coverage.cscript:517-556`, spec in `$PC_SB_SPEC`) and
  `_hon_sb_setup` (`test_setup_honesty.cscript`, spec in `$HON_SB_SPEC`). PC-21 (728-741) is
  the template: `{"fake": [["bokeh", "2.4.3"]]}` → r(198), `"2.4.3 (below minimum 3.0)"`,
  `"To upgrade: python -m pip install --upgrade 'bokeh>=3.0'"`, `"Unmet:  bokeh 2.4.3 (needs
  3.0)"`; PC-16 (622-637) fakes `pyversion "3.7.9 …"` → `"version 3.7.9 is below the minimum
  3.8."`, `"Unmet:  Python 3.7.9 (needs 3.8)"`.
- HON-19 (`test_setup_honesty.cscript:~470`) monkeypatches `_dash_pymin` to `"99.0"` and runs
  `dash_setup` with pip replaced by a recorder (`_hon_run_setup`).
- `_dash_setup_gate` (`dash_setup.ado:499`) and `_dash_pyver_ok` (298) take the versions as
  arguments; their cases (HON-06..13, `test_setup_python_gate.cscript`) test the comparator
  with literal numbers and do not assert the floor.

### K2.6 Existing tests that assert the old floor (flip, never delete)

- `test/test_setup_python_gate.cscript`: header (11-15) and the comparator cases use "3.8" as
  the *want* argument (comparator inputs — keep them; add cases at the new floor); 80-93 reads
  `r(pymin)` and requires `dash_setup.sthlp` to state it (dynamic — flips itself).
- `test/test_setup_honesty.cscript`: HON-20 (504-506: "(below minimum 3.0)", "--upgrade
  'bokeh>=3.0'", "bokeh 2.4 (needs 3.0)"), HON-21 (524-526: "(not verified against 3.0 /
  1.23 / 2.0)"), HON-22 (547-550: "-m pip install bokeh>=3.0 | … --user bokeh>=3.0"),
  HON-26 (700-701), HON-27 (719); header lines 11 and 16.
- `test/test_program_coverage.cscript`: PC-16 (628-637), PC-17 (648), PC-18 (668-669),
  PC-19 (682, 694, 701), PC-20 (708), PC-21 (735-741).
- `test/test_help_claims_8.cscript:786`: `items(bokeh 2.4 (needs 3.0))`.
- `test/test_help_claims_8.py::TestDashSetupHelpMatchesTheAdo::test_a_package_below_its_minimum_is_unmet_not_a_warning`
  (1640-1660): asserts the sentence "one below 3.0 is reported as an unmet requirement -- it is
  not upgraded for you -- and the run ends with r(198)." is in `dash_setup.sthlp`.
- `test/test_help_claims_8.py::…::test_it_names_every_step` (1620-1639) requires
  `{cmd:packaging}`, `{cmd:dash_render.py}`, `{cmd:--user}` and `r(198)` in the help, and
  `test_a_package_below_its_minimum…` requires "An installed package below its minimum is
  reported, with the command that upgrades it, and counted as unmet." and the Tornado sentence
  verbatim — keep those sentences when editing.

## User stories

- **US-09.1** As a dash serve operator, I want `dash serve, port(N)` to fail with a non-zero
  return code and a message naming the port when another program holds it, so that a do-file
  stops there instead of carrying on beside a browser showing someone else's server.
- **US-09.2** As a dash serve operator, I want the server's address printed only once the
  server answers, so that the line I copy into a browser is one that works.
- **US-09.3** As a dash serve operator running `python app.py --port 80`, I want the app to
  refuse the port and tell me the range, so that it never quietly serves on 1024.
- **US-09.4** As a Stata user running `dash_setup`, I want a Python, bokeh, numpy or pandas
  older than the versions dash is tested on refused by name with the upgrade command, so that I
  never pass setup and then fail on every `dash` command with r(7102).
- **US-09.5** As the maintainer, I want one declared floor, equal to the baseline the suites run
  under, held in every file by a test, so that the help, the package and the check cannot drift
  apart again.
- **US-09.6** As an operator running the generated app under another interpreter, I want its
  annotations deferred at import, so that an annotation is never the reason the app fails to
  start.

## Business requirements

- **BR-09.1** `dash serve, port(N)` while `127.0.0.1:N` is held by a listening socket returns
  r(198), prints exactly one error line `dash serve: no server started on port N: the port is
  in use`, prints no traceback and no "running at" line, and returns within 35 s (in practice
  under 3 s) whatever `timeout()` says.
- **BR-09.2** When the app stops with any status other than 0 before or after answering
  `/health`, `dash serve` returns r(198) and its message names the status
  (`… the app exited with status S`) and carries the app's last error lines.
- **BR-09.3** When the app comes up, one line naming the address is printed after `/health`
  has answered and not before; the command then blocks until Ctrl+C or `timeout()` and returns
  0, as today (HC4-19, `test_help_claims_1/4/5`).
- **BR-09.4** `--port` below 1024, above 65535, or not written in ASCII digits is refused with a
  message naming 1024 and 65535 — by `dash_render.py`'s own command line (exit status 2,
  nothing written), by `main()` (raises, nothing written), by a `build_options` port (raises,
  nothing written) and by the generated app (exit status 2, nothing bound).
- **BR-09.5** `dash_setup` declares Python 3.13, bokeh 3.8, numpy 2.3 and pandas 2.3; a version
  below any of them is reported `(below minimum X)`, counted `(needs X)`, ends the run with
  r(198) and installs nothing; the same four numbers appear in `dash_setup.sthlp`, `dash.sthlp`,
  `dash.pkg`, `dash.ado`'s message and CHANGELOG's `### Requirements`, and equal
  `test/conftest.py`'s `stata` baseline.
- **BR-09.6** The generated server app's first statement after its docstring is `from
  __future__ import annotations`.
- **BR-09.7** Nothing else changes: the rate limiters, CSP and headers, the session flags, the
  app's other options, stub renderers on the ado-path, and every real-launch test keep their
  behaviour.

## Technical requirements

- **TR-09.1 `_dash_port_value(value)`**, module-level in `dash_render.py`, placed immediately
  above `def main(`: `s = str(value).strip()`; accept only `s` non-empty and every character
  in `"0"…"9"` (no `re`, no `isdigit()` — `isdigit` takes non-ASCII digits); `n = int(s)`;
  require `1024 <= n <= 65535`; otherwise `import argparse as _ap` **inside the function** and
  `raise _ap.ArgumentTypeError("--port must be an integer from 1024 to 65535 (got: %r)" %
  (s[:40],))`. Return `n`. It is: the CLI parser's `type=` (27625-27630, keep `default=5006`);
  applied in `main()` (`port=_dash_port_value(port)` at 27603); applied in
  `ServerAppBuilder.build` (24950-24955: `if bo.get("port"): port =
  _dash_port_value(bo["port"])`, replacing the silent `except`); applied in the launcher
  (TR-09.2); and copied into the app through the function copy list (24466-24687), where the
  template's `_dash_arg_parser` says `type=_dash_port_value` (25614) and `__main__` replaces
  the clamp at 27371 with `try: _port = _dash_port_value(_a.port) except
  _argparse.ArgumentTypeError as _e: _p.error(str(_e))` (`_p = _dash_arg_parser(); _a =
  _p.parse_args()`), which covers an embedded non-string default the parser never sees.
  Local `argparse` import because the app binds the module as `_argparse` (risk factor 7).
- **TR-09.2 `_dash_launch_app(app_path, port, timeout, no_browser, *, ready_seconds=30.0,
  prebind=True)`**, module-level in `dash_render.py` between `main()` and the `__main__` block,
  replacing the inline launch code at 27670-27715 (`__main__` then calls it). Behaviour:
  1. `port = _dash_port_value(port)`.
  2. If `prebind`: `s = socket.socket(AF_INET, SOCK_STREAM)`, `s.setsockopt(SOL_SOCKET,
     SO_REUSEADDR, 1)`, `s.bind(("127.0.0.1", port))` inside `with s:`; on `OSError` raise
     `RuntimeError("no server started on port %d: the port is in use" % port)` — no child is
     started.
  3. `_cmd = [sys.executable, app_path, "--port", str(port)]` + `["--show"]` unless
     `no_browser` + `["--timeout", str(timeout)]` when `timeout > 0` (as today, 27692-27699).
     `proc = subprocess.Popen(_cmd, stdout=PIPE, stderr=PIPE, text=True, errors="replace")`
     looked up as `subprocess.Popen` at call time (tests monkeypatch it). `FileNotFoundError`
     → `RuntimeError("no server started on port N: could not launch the dashboard app (…)")`.
  4. Two daemon threads (`_pump(stream, sink)`), one per pipe, `readline()` into
     `queue.Queue` (stdout) and `collections.deque(maxlen=50)` plus the same queue tagged
     (stderr). **Threads only store; nothing prints off the main thread** (risk factor 3).
  5. Main loop until `proc.poll()` is not `None`: drain the stdout queue and `print` each
     line (`end=""`, `flush=True`) so the app's own messages (its URL, the
     `BOKEH_ALLOW_WS_ORIGIN` warnings, `Server stopped.`) reach the Results window; every
     0.25 s while not yet ready and `time.monotonic() < t0 + ready_seconds`, `GET
     http://127.0.0.1:<port>/health` with `urllib.request.urlopen(timeout=1.0)`; an HTTP
     response of any status (200, or 429 from the limiter) means ready — then print once
     `dash: the server answers at http://localhost:<port>/ (health check
     http://localhost:<port>/health); press Ctrl+C to stop.`; a connection error means not
     yet. Past `ready_seconds` with the child alive, print once `dash: no answer from
     http://127.0.0.1:<port>/health after <n> s; still waiting for the app (Ctrl+C stops
     it).` and keep waiting — the exit status decides. `time.sleep(0.25)` between turns.
  6. `KeyboardInterrupt` in the loop → `proc.terminate()`, `stopped_by_launcher = True`.
  7. Always finish with `proc.wait()` (so "the launcher waits on the app" stays literally
     true for `_FakeProc.waited`), join the pumps (1 s), drain and print the remaining stdout.
  8. Verdict: clean when `stopped_by_launcher`, or `returncode in (0, -signal.SIGINT,
     -signal.SIGTERM)`. Otherwise build the message: if any of `"Address already in use"`,
     `"EADDRINUSE"`, `"already in use"` is in the stderr tail → `"no server started on port
     N: the port is in use"`; else `"no server started on port N: the app exited with status
     S"`; append `"\n"` + the last 5 stderr lines with control characters other than `\n`
     removed (`c.isprintable() or c == "\n"`), whole message cut to 2000 characters; `raise
     RuntimeError(message)`. Print nothing else on failure: the caller prints.
- **TR-09.3 `__main__` (27670-27715 →)**: `_report = globals().get("_dash_launch_report")`;
  `try: _dash_launch_app(args.output, args.port, args.timeout, args.no_browser) except
  RuntimeError as _exc: if _report is None: print("dash_render: error -- " + str(_exc),
  file=sys.stderr, flush=True); raise SystemExit(1)` else `_report["error"] = str(_exc)` and
  return normally. `_report` exists only when the caller passed it through `runpy.run_path(…,
  init_globals=…)`: dash.ado does; a command line does not; stub renderers ignore it.
- **TR-09.4 `_dash_serve` (dash.ado 7425-7438)**: before 7438 add `python: _dash_srv_rep = {}`;
  change 7438 to `python: _dash_serve_ns = runpy.run_path("`_py_render'",
  init_globals={"_dash_launch_report": _dash_srv_rep}, run_name="__main__")` (keep the
  assignment: `test_render_log_clean.cscript` holds that `run_path`'s dict is never echoed);
  then `python: from sfi import Macro as _dash_M` and `python: _dash_M.setLocal("_srv_err",
  str(_dash_srv_rep.get("error", ""))[:2000])`; then

  ```stata
      if `: length local _srv_err' {
          mata: _dash_say("err", "dash serve: ", st_local("_srv_err"), "")
          exit 198
      }
  ```

  `_py_render` is already in `test_cscript_hygiene.py`'s `_ALLOWED_INLINE_PY_MACROS`; the new
  lines put no macro inside a Python string. The "starting Bokeh Server on port" line
  (7421-7422) stays: it announces an attempt, not a result.
- **TR-09.5 K2 floors in `dash_setup.ado`**: `_dash_pymin` returns `"3.13"` (295); 146-150
  become `local min_bokeh "3.8"`, `local min_numpy "2.3"`, `local min_pandas "2.3"` with a
  comment naming the source (the `stata` baseline of `test/conftest.py`, measured 25sep2026:
  Python 3.13.9, bokeh 3.8.0, numpy 2.3.5, pandas 2.3.3; bokeh 3.6 introduced
  `CustomJSTicker`, which every render imports; pandas is declared by dash because bokeh 3.9
  no longer requires it); line 60 reads `"Please install Python `c_pymin' or later and link it
  to Stata:"` (`c_pymin` is set at 45); the comment at 73 loses its number. Every message
  keeps its shape (`(below minimum X)`, `(needs X)`, `(not verified against X)`, `To upgrade:
  python -m pip install --upgrade 'pkg>=X'`) so only the numbers in the tests change.
- **TR-09.6 `dash.ado:205-207`**: `"Python 3.13+: {help python}"`.
- **TR-09.7 `dash.pkg:17`**: `d Requires: Python 3.13+, bokeh>=3.8, numpy>=2.3, pandas>=2.3.`
- **TR-09.8 help and CHANGELOG** — `dash_setup.sthlp` 40-42, 70, 80-82, 97-98 (`"bokeh>=3.8",
  "numpy>=2.3", "pandas>=2.3"`), 110-113 (`one below 3.8 …`), plus one new `{pstd}` under
  `{ul:Python packages (minimum versions)}`: "These minimums are the versions {cmd:dash}'s
  own test suites run under (Python 3.13.9, bokeh 3.8.0, numpy 2.3.5, pandas 2.3.3 when this
  was written); nothing older is tested. bokeh before 3.6 lacks {cmd:CustomJSTicker}, which
  every {cmd:dash} render imports, and {cmd:pandas} is required by {cmd:dash} itself: bokeh
  3.9 no longer installs it." Keep verbatim the sentences `test_help_claims_8.py` asserts
  (K2.6). `dash.sthlp` 3131-3134 (`{ul:Python 3.13+}`; `bokeh>=3.8, numpy>=2.3, pandas>=2.3`);
  727-729 port(): add "; a port another program holds is refused with r(198) and named";
  1353-1357: add "{cmd:dash serve} prints the server's address once it answers
  {cmd:/health}. If no server starts -- the port is in use, or the app stops before it
  answers -- {cmd:dash serve} says why and returns r(198) instead of blocking."; 1367-1374:
  add "{cmd:--port} outside 1024 to 65535 is refused (exit status 2), not moved to the
  nearest port." CHANGELOG `### Requirements` (330-334) rewritten for the new floor with the
  old numbers and the reason, and two lines (F1, K2) under a `### Fixed in WP-28` heading
  placed immediately before `### Fixed after WP-27` (338), created if absent.
- **TR-09.9 the app's future import**: insert `"from __future__ import annotations",` and
  `""` between template lines 25204 (`'"""'`) and 25206 (`"import argparse as _argparse"`),
  so it is the first statement after the docstring; keep `from typing import …` (25222): the
  names are still read by the annotations and by
  `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`; reword the comment at
  25216-25221 to say the import is kept for the names, not for evaluation.
- **TR-09.10 `_FakeProc`** (`test_help_claims_2.py:756`): `__init__(self, cmd, **kw)`,
  `returncode = 0`, `stdout = io.StringIO()`, `stderr = io.StringIO()`, `poll()` →
  `returncode`, `wait()` sets `waited` and returns `returncode`, `terminate()` no-op,
  `communicate()` → `("", "")`; `_launch` binds a free port instead of 5123.
- **TR-09.11 new tests**: `test/test_serve_launcher.py`, `test/test_version_floor.py`,
  `test/test_serve_port_in_use.cscript` (registered in `test/run_all_cscripts.do`; SPU-01
  added to `program_coverage_map.py`'s `_dash_serve` references).
- **TR-09.12 `test/function_test_map.py`** gains `_dash_port_value`, `_dash_launch_app` and
  `_dash_launch_app.<locals>._pump` (and any other nested def), each naming a test in
  `test_serve_launcher.py`; the app's copy of `_dash_port_value` shares the original's entry.
- **TR-09.13** No `shell=True`, no user text in `exec`/`eval`; the child's stderr reaches
  Stata only through `_dash_say`, which neutralises SMCL, and with control characters removed
  (TR-09.2 step 8).

## Boundaries

- **No venv matrix** (DISCOVERY Q8): no test runs Python 3.8-3.12 or Bokeh below 3.8. The
  interpreters at `/usr/local/bin/python3.8`, `3.9`, `3.10` are not used.
- **No change to the rate limiters, CSP, security headers, session flags or `_HealthHandler`**;
  the launcher polls `/health` at 4 requests a second, well under `_HEALTH_LIMIT_RPM = 600`.
- **`CustomJSTicker` (16877, 17217) is not touched.**
- `_dash_serve_spec` (7252-7345) keeps its own port and timeout checks; the launcher's refusal
  is a second gate for the command-line routes, not a replacement.
- `bokeh serve app.py` (no `/health`) is documented as-is; the readiness poll belongs to the
  self-serving launcher only.
- The `__main__` block of the generated app keeps printing its own URL line; the launcher
  forwards it. No wording of the app's messages changes except the port refusal.
- `GAPS2.md` Tracked lines and ROADMAP WP-28 are sections 01 and 19; this section does not
  edit them.
- Nothing in DISCOVERY is contradicted: Q12 (refuse, poll 30 s, print once answered, refuse
  the range) and Q8 (tested versions only) are implemented as written.

## Stata truth

None. No fixture is written. The floor is read from `test/conftest.py` `_BASELINES["stata"]`
(measured 25sep2026 from `~/.stata19/console/stata19.rc`), not from a probe. The cscript
measures rc and message in the run.

Stata is run only as `cd <dir> && STATATMP=<dir>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do
<file>.do` from a scratch directory (CLAUDE.md rule 10; trailing slash; `STATATMP` apart from
the log's directory), at most three sessions at once, and `display c(python_exec)` is checked
before trusting a skip.

## TDD test stubs

Regression tests that fail at `91d97be` come first.

**`test/test_serve_launcher.py` (new, 09-01)**
- Test: a listening socket on `127.0.0.1:P` makes the real launcher raise —
  `test_serve_launcher.py::TestTheLauncherRefusesAHeldPort::test_a_socket_on_loopback_makes_the_launcher_raise`:
  `dr._dash_launch_app(app, P, 0, True)` raises `RuntimeError` whose text is exactly
  `no server started on port P: the port is in use`; no child ran (`Popen` wrapped to count).
  Pre-fix failure: `AttributeError: module 'dash_render' has no attribute '_dash_launch_app'`.
- Test: with `prebind=False` the child's own bind failure is reported —
  `…::TestTheLauncherRefusesAHeldPort::test_the_childs_bind_failure_is_reported_with_its_stderr`
  (`@pytest.mark.serve`): a real app built by `ServerAppBuilder`, socket held; the
  `RuntimeError` names the port, says `the port is in use`, and carries `Address already in
  use` from the child's stderr; elapsed under 30 s.
- Test: a stub app that writes `boom` to stderr and exits 3 —
  `…::TestTheLauncherReportsTheExitStatus::test_a_non_zero_exit_names_the_status_and_carries_stderr`:
  message starts `no server started on port P: the app exited with status 3` and contains
  `boom`.
- Test: a stub app that answers `/health` and then exits 0 —
  `…::TestTheLauncherPrintsTheUrlOnceHealthAnswers::test_the_ready_line_follows_the_first_health_answer`:
  the stub (`http.server`, `127.0.0.1:P`, answers `/health` 200 then exits 0 within 2 s of
  the first request) makes the launcher print exactly one `dash: the server answers at
  http://localhost:P/` line, and return without error.
- Test: a stub that exits 0 without ever answering prints no ready line and raises nothing —
  `…::TestTheLauncherPrintsTheUrlOnceHealthAnswers::test_no_answer_no_ready_line` (the
  control).
- Test: the `__main__` block reports through the box when one is given —
  `…::TestTheLaunchReportBox::test_a_failure_lands_in_the_report_dict`: `runpy.run_path(…,
  init_globals={"_dash_launch_report": box}, run_name="__main__")` with `subprocess.Popen`
  replaced by a fake whose `returncode` is 3 and whose `stderr` holds `boom`: no exception,
  `box["error"]` starts `no server started on port P: the app exited with status 3`.
- Test: without a box the command line exits 1 with the message on stderr —
  `…::TestTheLaunchReportBox::test_without_a_box_the_cli_exits_1_with_the_message`:
  `pytest.raises(SystemExit)` with `code == 1`; `capsys.readouterr().err` contains
  `exited with status 3`.
- Test: `--port 80` and `--port 70000` on `dash_render.py --launch` exit 2 before writing —
  `…::TestPortRefusals::test_the_renderer_cli_refuses[80|70000]`: `SystemExit` code 2, the
  `--output` file does not exist, the fake `Popen` was never constructed, stderr names 1024
  and 65535.
- Test: `_dash_port_value` unit — `…::TestPortRefusals::test_port_value_accepts_the_range_and_refuses_the_rest`
  (`"1024"`, `65535`, `" 5006 "` accepted; `"80"`, `"70000"`, `"٥٠٠٦"`, `"5_006"`, `""`,
  `"5006x"` raise `argparse.ArgumentTypeError`). Pre-fix: `AttributeError`.

**`test/test_version_floor.py` (new, 09-01)**
- Test: `test_version_floor.py::TestTheFloorIsTheTestedBaseline::test_dash_setup_declares_the_stata_baseline`:
  regex-read `return local pymin "X"` and `local min_bokeh|numpy|pandas "X"` from
  `dash_setup.ado`; equal to `conftest._BASELINES["stata"]` for python, bokeh, numpy, pandas.
  Pre-fix failure: `3.8 != 3.13`.
- Test: `…::TestTheFloorIsTheTestedBaseline::test_every_declaration_agrees_with_dash_setup`:
  `dash.pkg:17` (`Requires: Python P+, bokeh>=B, numpy>=N, pandas>=D.`), `dash.ado`'s
  `_dash_require_python` message (`Python P+`), `dash.sthlp` (`{ul:Python P+}`,
  `bokeh>=B, numpy>=N,` … `pandas>=D`, flattened as `test_help_claims_8.py::_flat` does),
  `dash_setup.sthlp` (`Python P or later`, `{opt bokeh}}B or later`, numpy, pandas, `below
  P`, `one below B is reported`), CHANGELOG's `### Requirements` block (`Python P`, `bokeh >=
  B`) — all equal the four read from `dash_setup.ado`.
- Test: `…::TestTheFloorIsTheTestedBaseline::test_the_old_floor_is_named_nowhere_it_matters`:
  none of `dash.pkg`, `dash.sthlp`, `dash_setup.sthlp`, the code lines of `dash.ado` and
  `dash_setup.ado` contains `Python 3.8`, `bokeh>=3.0`, `3.0 or later`, `1.23`, `2.0 or
  later`.
- Test: `…::TestTheGeneratedAppEvaluatesNoAnnotationAtImport::test_the_future_import_is_the_first_statement`:
  build an app, `ast.parse`; `tree.body[0]` is the docstring `Expr`, `tree.body[1]` is
  `ImportFrom(module="__future__")` naming `annotations`. Pre-fix failure: `body[1]` is
  `Import(argparse)`.
- Test: `…::TestTheGeneratedAppEvaluatesNoAnnotationAtImport::test_pep585_and_pep604_annotations_are_deferred`:
  walk every `FunctionDef`/`AsyncFunctionDef` argument and return annotation and every
  `AnnAssign`; collect those holding `BinOp(op=BitOr)` or a `Subscript` whose value is `list`,
  `dict`, `tuple`, `set`, `frozenset` or `type`; assert `found == [] or future_import_present`;
  as the control that the walker sees annotations, assert the walk visited more than 20
  annotations (55 at `91d97be`).

**`test/test_serve_port_in_use.cscript` (new, 09-01; registered 09-02)**
- Test: SPU-01 — a socket bound and listening on `127.0.0.1:P` from Stata's Python; one graph
  registered; log captured; `capture noisily dash serve, port(P) timeout(1) nobrowser`:
  `_rc == 198`, the log holds `no server started on port P` and `the port is in use`, holds
  no `Traceback` and no `Server running at`, and the elapsed time (`timer 92`) is under 40 s.
  Pre-fix: `_rc == 0` after about 2 s.
- Test: SPU-02 — a stub `dash_render.py` first on the ado-path (SRV-17's pattern) that only
  writes `globals().get("_dash_launch_report")["error"]` when the dict is present: `dash
  serve, timeout(1) nobrowser` gives `_rc == 198` and the log holds the stub's text
  (`the app exited with status 3` and `stub: boom`). Pre-fix: `_rc == 0`.
- Test: SPU-03 — the same stub told to write nothing: `_rc == 0` (the control: SPU-02's rc
  comes from the box, not from the stub itself).

**Flips (same commit as the fix)**
- `test_render_cli_port.py::TestPortReachesTheGeneratedApp::test_an_out_of_range_port_is_clamped_not_embedded_raw`
  → `…_is_refused_not_embedded`; `…_in_build_options_is_clamped_too` →
  `…_in_build_options_is_refused_too` (09-04).
- `test_resource_limits.py::TestTheBoundsThatAlreadyWorkedAreKept::test_the_port_is_clamped_in_every_place_it_is_read`
  → `…_is_refused_in_every_place_it_is_read` (09-04).
- `test_adversarial_matrix.py` lines 860 and 878 → the new node id (09-04).
- `test_help_claims_2.py::_FakeProc` (09-03).
- `test_setup_python_gate.cscript` (floor cases added: `3.13.9 >= 3.13` → 1, `3.13 >= 3.13`
  → 1, `3.12.11 < 3.13` → 0, `3.10.10 < 3.13` → 0, and the same four through `_gate16`;
  header numbers), `test_setup_honesty.cscript` HON-20/21/22/26/27 plus new HON-29 (sandbox
  `{"fake": [["bokeh", "3.7.3"]]}` → r(198), `3.7.3 (below minimum 3.8)`, `--upgrade
  'bokeh>=3.8'`, `Unmet:  bokeh 3.7.3 (needs 3.8)`, no pip call) and HON-30 (`{"pyversion":
  "3.12.11 (dash test sandbox)"}` → r(198), `version 3.12.11 is below the minimum 3.13.`,
  `Unmet:  Python 3.12.11 (needs 3.13)`), `test_program_coverage.cscript` PC-16..21 numbers
  (09-09); `test_help_claims_8.cscript:786` and `test_help_claims_8.py:1647-1660` (09-10).

**Mutation table — proof the tests are not vacuous.** Apply, confirm the named test fails,
revert:

| break this | test that must die |
|---|---|
| in `_dash_launch_app`, drop the returncode verdict (always return) | `TestTheLauncherReportsTheExitStatus::test_a_non_zero_exit_names_the_status_and_carries_stderr`, SPU-02 |
| print the ready line before the first `/health` answer | `TestTheLauncherPrintsTheUrlOnceHealthAnswers::test_no_answer_no_ready_line` |
| hold the cscript's socket on `0.0.0.0` instead of `127.0.0.1` (a fixture mutation) | SPU-01 passes for the wrong reason on macOS only if the app bound the wildcard; it binds loopback, so SPU-01 must still fail — this row documents why the address is fixed |
| in `_dash_serve`, drop the `exit 198` after `_dash_say` | SPU-01, SPU-02 |
| in `_dash_port_value`, use `int(s)` without the ASCII check | `TestPortRefusals::test_port_value_accepts_the_range_and_refuses_the_rest` (`"٥٠٠٦"`, `"5_006"`) |
| restore the clamp at any one of the three sites | the matching case of `test_the_port_is_refused_in_every_place_it_is_read` |
| set `min_bokeh "3.8"` but leave `_dash_pymin "3.8"` | `test_dash_setup_declares_the_stata_baseline` |
| put the future import after `import argparse` | `test_the_future_import_is_the_first_statement` (and the app would raise `SyntaxError` at import) |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| held port → `RuntimeError` text, no child | pytest, real `_dash_launch_app` | none | served only (the launcher) |
| held port, `prebind=False` → child's errno 48 reported | pytest (`serve` mark), real app | none | served |
| exit 3 named, stderr tail carried | pytest, stub app | none | served |
| ready line after `/health`, none without | pytest, stub http app, capsys | none | served |
| box protocol through `runpy` (with/without box) | pytest, fake `Popen` | none | served |
| `--port 80`/`70000` refused at the CLI, `main()`, `build_options`, the app, the launcher | pytest (new + inverted) | none | served |
| `dash serve` r(198) + message against a held port; box via stub renderer; control | cscript `test_serve_port_in_use.cscript` | none | Stata |
| real launches still block, answer `/health`, stop on SIGINT/timeout | existing pytest (`test_help_claims_1/4/5`) and HC4-19 | none | served |
| floor in `dash_setup.ado` equals conftest's `stata` baseline; every file agrees | pytest `test_version_floor.py` | `test/conftest.py` | n/a |
| future import first; PEP 585/604 annotations deferred | pytest, `ast` on a built app | none | served |
| `dash_setup` refuses bokeh 3.7.3 and Python 3.12.11 by name, installs nothing | cscript HON-29/30 (sandbox), PC-16/21 flipped | `test/setup_sandbox.py` | Stata |
| help and CHANGELOG say the floor and the refusal | pytest `test_version_floor.py`, `test_help_claims_8.py` flipped | none | n/a |

**Acceptance criteria**
- **AC-09.1** `test/test_serve_launcher.py` and `test/test_version_floor.py` fail at `91d97be`
  for the reasons recorded in 09-01's commit message and pass after 09-06 / 09-11.
- **AC-09.2** `test_serve_port_in_use.cscript` SPU-01..03 fail at `91d97be` (SPU-01/02 with
  `_rc == 0`) and pass after 09-05; `run_all_cscripts.do` runs it; no SKIP.
- **AC-09.3** The three inverted clamp tests and the two registry lines are renamed, not
  deleted; `grep -c "max(1024, min(" dash_render.py` is 0.
- **AC-09.4** HC4-19..21, `TestServeBlocksUntilCtrlC`, `TestServingBlocksUntilInterrupted`,
  `TestTheRealHandoffServes`, SRV-17..20 and `test_serve_browser.cscript` pass unchanged.
- **AC-09.5** `dash_setup` on this machine still ends `dash_setup complete` (the installed
  versions meet the floor); HON-29 and HON-30 refuse with the texts above.
- **AC-09.6** The full pytest suite under both interpreters (`make test`, `make test-dev`)
  and the flipped cscripts pass; BUGS.md holds the two closed entries naming their tests;
  `test_tracking_documents.py` passes.

## Tasks

Each task is one commit on `s3-bugs`; the F1 group is 09-03..09-06 and the K2 group
09-07..09-12, so the PRD's one-commit-per-gap form can be produced by squashing each group
before merge if the maintainer prefers. No AI references in any message. Line numbers are
those of `91d97be`; once a task inserts lines, later anchors in the same file are given as
symbols too, and the symbol is authoritative. "The full suite" below means the one whole-suite
run CLAUDE.md rule 11 allows before a commit (`pytest test/ -q`, never two at once).

<task type="auto" id="09-01">
  <name>Write the failing tests for both gaps</name>
  <files>test/test_serve_launcher.py, test/test_version_floor.py, test/test_serve_port_in_use.cscript</files>
  <action>
    Create the three files with every test named in "TDD test stubs", under exactly those
    names; write tests only, touch no source file. `test_serve_launcher.py`: copy the header
    pattern of `test/test_render_cli_port.py:17-30` (`_HERE`, `sys.path` inserts, `import
    dash_render as dr`, `make_data_json`), a `_free_port()` as in `test_help_claims_1.py:565`,
    a `_held_port()` context manager that binds `127.0.0.1:0` with `SO_REUSEADDR` unset,
    calls `listen(1)` and yields the port, a `_build_app(tmp_path)` through
    `dr.ServerAppBuilder(...).build(...)`, and two stub apps written to `tmp_path` (one
    writes `boom` to stderr and `sys.exit(3)`; one is an `http.server` answering `/health`
    with 200 JSON then exiting 0 within 2 s of the first request); the box tests replace
    `subprocess.Popen` with a fake carrying `returncode`, `stdout`/`stderr` `io.StringIO`,
    `poll`, `wait`, `terminate`, `communicate`. `test_version_floor.py`: read the floor from
    `dash_setup.ado` with `re.search(r'return local pymin "([^"]+)"')` and
    `r'local min_(bokeh|numpy|pandas)\s+"([^"]+)"'`, import `_BASELINES` from `conftest`,
    flatten SMCL as `test_help_claims_8.py::_flat` does, build an app for the `ast` tests.
    The cscript follows `test/test_e2e_serve.cscript:1-53` (header, `c(python_exec)` guard,
    a warmed-up and retried `capture python: import bokeh` probe, `do ../dash_parse.mata`,
    `do ../dash.ado`, `do cert_helpers.do`), holds the socket in a `python:` block
    (`socket.socket(AF_INET, SOCK_STREAM)`, `bind(("127.0.0.1", 0))`, `listen(1)`, port to
    `$spu_port` via `sfi.Macro.setGlobal`), times the call with `timer 92`, reads the captured
    log with `cert_log_has`, closes the socket in every path (`capture noisily {` … `}` then
    `python: _spu_s.close()`), and builds SPU-02/03's stub exactly as
    `test_serve_launch.cscript:249-265` does. Run the two pytest files against the
    unmodified tree and paste the failure summary into the commit message; the cscript is
    run in 09-02.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_serve_launcher.py test/test_version_floor.py -q 2>&1 | tail -30` collects without error and reports 0 passed apart from the pure-comparator `test_port_value…` case, which also fails (`AttributeError`); the floor test fails with `'3.8' != '3.13'`; the future-import test fails naming `Import`. `python3 -m pytest test/test_cscript_hygiene.py -q -k "serve_port_in_use"` passes every rule except `TestEveryCscriptIsWiredIntoTheRunner` (09-02).]]></verify>
  <done>The two pytest files and the cscript exist, collect cleanly and fail on the unmodified tree for the reasons recorded in the commit message; no source file changed.</done>
</task>

<task type="auto" id="09-02">
  <name>Register the cscript and record its failure</name>
  <files>test/run_all_cscripts.do, test/program_coverage_map.py</files>
  <action><![CDATA[
    Append a block for `test_serve_port_in_use.cscript` to `test/run_all_cscripts.do`, copied
    from the `test_serve_launch.cscript` block at 737-760 (numbered after the last script;
    `[ RUN ]`/`[ PASS]`/`[ FAIL]`/`[ SKIP]` lines, rc 222 as SKIP). Add
    `"test_serve_port_in_use.cscript:SPU-01"` to the `_dash_serve` tuple in
    `test/program_coverage_map.py` (~251). Run the cscript alone from a scratch directory:
    `d=$(mktemp -d) && cd "$d" && cp -R <repo>/test ./test && cd test && STATATMP="$d/tmp/"
    arch -arm64 /usr/local/bin/stata-mp -b do test_serve_port_in_use.cscript` (the script
    loads `../dash.ado`, so copy the tree or run from `<repo>/test` with `STATATMP` elsewhere);
    read the log: SPU-01 must fail on `assert `spu_rc' != 0` after about 2 s and SPU-02 on the
    same assertion. Check `display c(python_exec)` in the log before believing a skip. Record
    both failures in the commit message.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_cscript_hygiene.py test/test_program_coverage_map.py -q 2>&1 | tail -3` passes; the batch log of the cscript ends with an assertion failure at SPU-01 and `r(9)`, not a SKIP.]]></verify>
  <done>The cscript is wired into the runner and the coverage map, and its failure on the unmodified tree is recorded.</done>
</task>

<task type="auto" id="09-03">
  <name>Build the launcher that reads exit status and health</name>
  <files>dash_render.py, test/function_test_map.py, test/test_help_claims_2.py</files>
  <action><![CDATA[
    In `dash_render.py`: add `_dash_port_value` (TR-09.1) immediately above `def main(`; make
    the CLI parser's `--port` (27625-27630) use `type=_dash_port_value`; change `main()`'s
    build call (27603) to `port=_dash_port_value(port)`; in `ServerAppBuilder.build`
    (24950-24955) replace the `try/except` with `port = _dash_port_value(bo["port"])` under the
    existing `if bo.get("port"):`; add `_dash_launch_app` (TR-09.2) between `main()` and the
    `__main__` block, moving the launch code out of 27670-27715 and dropping the unused `_wb`
    import; rewrite the `__main__` launch block as TR-09.3; add `"_dash_port_value"` at the
    END of the function copy tuple (24466-24687) and, in the app template, `type=_dash_port_value`
    at 25614 and the `__main__` validation of TR-09.1 in place of the clamp at 27371. Add
    `function_test_map.py` entries for `_dash_port_value`, `_dash_launch_app` and every nested
    def in it (`_dash_launch_app.<locals>._pump`), naming tests in `test_serve_launcher.py`.
    Update `_FakeProc` and `_launch` in `test_help_claims_2.py` as TR-09.10. Verify the
    TIME_WAIT reasoning of F1.5 once: start and stop a real app on a port, then call
    `_dash_launch_app` on the same port within a second — it must not report the port in use.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_serve_launcher.py test/test_help_claims_2.py -q -k "Launcher or Report or Refusals or LaunchReportBox" 2>&1 | tail -3` passes; `grep -c "max(1024, min(" dash_render.py` prints 0; `python3 -m pytest test/test_function_test_map.py test/test_statistical_helpers.py test/test_resource_limits.py -q -k "map or CarriesEveryName or DefinesEveryName or clamped" 2>&1 | tail -3` shows only the parametrised clamp test failing (inverted in 09-04).]]></verify>
  <done>`dash_render._dash_launch_app` raises `RuntimeError` naming the port and the child's status, polls `/health` and prints the address once it answers; every `--port` site refuses through `_dash_port_value`; the served app carries the same helper; the fake process in `test_help_claims_2.py` matches the new `Popen` call.</done>
</task>

<task type="auto" id="09-04">
  <name>Invert the tests that required the clamp</name>
  <files>test/test_render_cli_port.py, test/test_resource_limits.py, test/test_adversarial_matrix.py</files>
  <action>
    Rename and invert, never delete: in `test_render_cli_port.py` the two tests at 151 and 160
    become `test_an_out_of_range_port_is_refused_not_embedded` and
    `test_an_out_of_range_port_in_build_options_is_refused_too`, each asserting
    `pytest.raises(argparse.ArgumentTypeError)` for 80 and 70000 and that the output file does
    not exist afterwards; keep `_bound_port` for the in-range tests. In `test_resource_limits.py`
    the test at 1278 becomes `test_the_port_is_refused_in_every_place_it_is_read`, parametrised
    over `given in (80, 70000)`: `main()` raises; the app run with `sys.argv = ["app.py",
    "--port", str(given)]` raises `SystemExit` with `code == 2` and the `_Server` recorder saw
    nothing; the launcher run through `runpy` with `--port str(given)` raises `SystemExit` code
    2 and the `_Proc` recorder was never constructed; `capsys.readouterr().err` names `1024`
    and `65535` for the app and launcher cases. Rewrite each docstring to say why the clamp was
    wrong (80 served on 1024, silently). In `test_adversarial_matrix.py` replace the node id at
    860 and 878 with `test/test_render_cli_port.py::TestPortReachesTheGeneratedApp::test_an_out_of_range_port_is_refused_not_embedded`.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_render_cli_port.py test/test_resource_limits.py test/test_adversarial_matrix.py -q 2>&1 | tail -3` passes, and `grep -rn "is_clamped_not_embedded\|is_clamped_in_every" test/` prints nothing.]]></verify>
  <done>The three clamp tests assert refusal at every site and the adversarial registry names the renamed test; no test was deleted.</done>
</task>

<task type="auto" id="09-05">
  <name>Make dash serve report the launcher's failure</name>
  <files>dash.ado</files>
  <action>
    In `_dash_serve` (7349-7439) apply TR-09.4: create `_dash_srv_rep` before the `runpy`
    line, pass it as `init_globals={"_dash_launch_report": _dash_srv_rep}`, read
    `_dash_srv_rep.get("error", "")` into the local `_srv_err` through `sfi.Macro.setLocal`,
    and on a non-empty value print it with `mata: _dash_say("err", "dash serve: ",
    st_local("_srv_err"), "")` and `exit 198`. Add a comment above the block explaining the
    box: a `python:` line inside a program takes no compound statement, an exception escaping
    `run_path` is r(7102) with a traceback, and the dict is the one object the executed
    module and this program share. Run the new cscript and the three stub-renderer scripts
    from a scratch directory as in 09-02 (`test_serve_port_in_use.cscript`,
    `test_serve_launch.cscript`, `test_serve_browser.cscript`, `test_render_log_clean.cscript`;
    at most three Stata sessions at once, each with its own `STATATMP`).
  </action>
  <verify><![CDATA[The batch logs show `SPU-01 PASS`, `SPU-02 PASS`, `SPU-03 PASS` with SPU-01's elapsed time under 40 s, and `test_serve_launch.cscript`, `test_serve_browser.cscript` and `test_render_log_clean.cscript` end in their PASS lines; `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -3` passes (no macro inside a Python string on the new lines).]]></verify>
  <done>`dash serve, port(N)` against a held loopback port returns r(198) with `dash serve: no server started on port N: the port is in use`, and any launcher failure reaches the Results window as one message with no traceback.</done>
</task>

<task type="auto" id="09-06">
  <name>Document F1 and close its BUGS.md entry</name>
  <files>dash.sthlp, CHANGELOG.md, BUGS.md</files>
  <action>
    `dash.sthlp`: the port() synopt (727-729), the blocking-behaviour paragraph (1353-1357) and
    the independent-run paragraph (1367-1374) as TR-09.8. `CHANGELOG.md`: under `### Fixed in
    WP-28` (create it immediately before `### Fixed after WP-27` at 338 if no other section
    has yet; keep one heading after merge) add: "`dash serve` returns r(198) and says why when
    no server started -- the port is in use, or the app stopped before it answered `/health`
    -- where it returned 0 after the app had died on process stderr; the server's address is
    printed once `/health` answers; `--port` outside 1024-65535 is refused by `dash_render.py`,
    `main()`, a `build_options` port and the generated app instead of being moved (80 served
    on 1024). (WP-28, GAPS2 F1)". `BUGS.md`: append a closed entry, five fields in order:
    Title "`dash serve' returns rc 0 when no server ran, and an out-of-range --port is clamped
    instead of refused"; File Names and Line Numbers `dash_render.py` (the --launch block
    27670-27715 at 91d97be, the clamps at 27371, 27603 and 27680, `_dash_arg_parser`),
    `dash.ado` (`_dash_serve` 7349-7439); Description quoting GAPS2 F1's measurement (rc 0
    after 1.7 s with the port held; errno 48 on process stderr; `--port 80` served on 1024);
    Suggested fix (read the child's exit status and stderr, refuse in dash.ado naming the port,
    poll /health, refuse the range at every site); Resolution "Fixed 25sep2026 (WP-28)."
    describing `_dash_launch_app`, `_dash_port_value` and the `_dash_launch_report` box, and
    naming `test/test_serve_launcher.py::TestTheLauncherRefusesAHeldPort::test_a_socket_on_loopback_makes_the_launcher_raise`,
    `test/test_serve_launcher.py::TestTheLauncherReportsTheExitStatus::test_a_non_zero_exit_names_the_status_and_carries_stderr`,
    `test/test_resource_limits.py::TestTheBoundsThatAlreadyWorkedAreKept::test_the_port_is_refused_in_every_place_it_is_read`
    and `test_serve_port_in_use.cscript` SPU-01 and SPU-02, each of which failed at 91d97be.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_1.py test/test_help_claims_4.py test/test_help_claims_5.py -q 2>&1 | tail -3` passes (the entry is well formed and names existing tests; the real launches still block and stop); `grep -ci "claude\|anthropic" BUGS.md CHANGELOG.md dash.sthlp` prints 0 for the new text.]]></verify>
  <done>The help states the refusal and the readiness line, CHANGELOG records F1 under WP-28, and BUGS.md holds F1 closed with its regression tests named.</done>
</task>

<task type="auto" id="09-07">
  <name>Defer the generated app's annotations</name>
  <files>dash_render.py</files>
  <action>
    Apply TR-09.9: insert `"from __future__ import annotations",` and `""` between the
    template's closing docstring line (25204, `'"""'`) and `"import argparse as _argparse"`
    (25206; find them by text — 09-03 moved lines below 27000 but not here). Reword the
    comment at 25216-25221: the `typing` import stays because the annotations name `Any`,
    `Callable`, `Iterable` and `List` and the served-app name checks read them, not because
    Python evaluates them. Build an app and import it under the development interpreter to
    show the future statement is accepted in that position.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_version_floor.py -q -k "Annotation" 2>&1 | tail -3` passes both annotation tests; `python3 -m pytest test/test_server.py test/test_resource_limits.py -q -k "DefinesEveryName or source or health" 2>&1 | tail -3` passes.]]></verify>
  <done>Every generated server app opens with `from __future__ import annotations` as its first statement after the docstring.</done>
</task>

<task type="auto" id="09-08">
  <name>Raise the floor in the check, the message and the package</name>
  <files>dash_setup.ado, dash.ado, dash.pkg</files>
  <action>
    Apply TR-09.5 (`_dash_pymin` "3.13"; `min_bokeh "3.8"`, `min_numpy "2.3"`, `min_pandas
    "2.3"` with the sourcing comment; line 60 through `c_pymin`; the comment at 73), TR-09.6
    (`dash.ado:205-207`, "Python 3.13+") and TR-09.7 (`dash.pkg:17`). Change no message
    shape. Run `dash_setup` once on this machine from a scratch directory to confirm it still
    ends `dash_setup complete` against the installed 3.13.9 / 3.8.0 / 2.3.5 / 2.3.3.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_version_floor.py -q -k "declares_the_stata_baseline" 2>&1 | tail -3` passes; `grep -n '"3.8"\|"3.0"\|"1.23"\|"2.0"' dash_setup.ado` prints no floor line; the `dash_setup` batch log ends `dash_setup complete`.]]></verify>
  <done>`dash_setup` refuses Python below 3.13, bokeh below 3.8, numpy and pandas below 2.3; `dash.ado` and `dash.pkg` name the same floor.</done>
</task>

<task type="auto" id="09-09">
  <name>Flip the cscripts that asserted the old floor</name>
  <files>test/test_setup_python_gate.cscript, test/test_setup_honesty.cscript, test/test_program_coverage.cscript</files>
  <action><![CDATA[
    `test_setup_python_gate.cscript`: update the header's numbers (11-15) and add the floor
    cases listed under "Flips" (direct and through `_gate16`); keep every existing comparator
    case. `test_setup_honesty.cscript`: change 3.0 → 3.8, 1.23 → 2.3, 2.0 → 2.3 in HON-20
    (504-506), HON-21 (524-526), HON-22 (547-550), HON-26 (700-701), HON-27 (719) and the
    header (11, 16); add HON-29 and HON-30 after HON-28 using `_hon_sb_setup` with
    `$HON_SB_SPEC` `{"fake": [["bokeh", "3.7.3"]]}` and `{"pyversion": "3.12.11 (dash test
    sandbox)"}`, `$HON_SB_EXPECT "[]"`, asserting r(198), the "(below minimum 3.8)" /
    "is below the minimum 3.13." lines, the "Unmet:" lines, no "All dependencies are
    satisfied" and no pip call; extend the header's "Tests:" line. `test_program_coverage.cscript`:
    PC-16 (628-637: needs 3.13), PC-17 (648), PC-18 (668-669), PC-19 (682, 694, 701), PC-20
    (708), PC-21 (735-741: below minimum 3.8, `'bokeh>=3.8'`, needs 3.8). Run the three
    scripts from a scratch directory (three sessions at most, own `STATATMP` each) and check
    `c(python_exec)` in each log before reading a skip as a skip.
  ]]></action>
  <verify><![CDATA[The three batch logs end in their PASS lines with `HON-29 PASS`, `HON-30 PASS`, `PC-16 PASS` and `PC-21 PASS` present and no SKIP; `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_cscript_hygiene.py test/test_program_coverage_map.py -q 2>&1 | tail -3` passes.]]></verify>
  <done>The three certification scripts assert the new floor, and two new cases prove `dash_setup` refuses bokeh 3.7.3 and Python 3.12.11 by name without installing anything.</done>
</task>

<task type="auto" id="09-10">
  <name>Flip the help-claims tests for dash_setup</name>
  <files>test/test_help_claims_8.cscript, test/test_help_claims_8.py</files>
  <action>
    `test_help_claims_8.cscript:786`: `items(bokeh 2.4 (needs 3.8))`.
    `test_help_claims_8.py::TestDashSetupHelpMatchesTheAdo::test_a_package_below_its_minimum_is_unmet_not_a_warning`
    (1640-1660): the docstring's `(needs 3.0)` and the asserted sentence become "one below 3.8
    is reported as an unmet requirement -- it is not upgraded for you -- and the run ends with
    r(198)." (the sentence itself is changed in `dash_setup.sthlp` in 09-11, so this test is
    red until then — record that in the commit message). Run `test_help_claims_8.cscript`
    from a scratch directory.
  </action>
  <verify><![CDATA[The cscript's batch log ends in its PASS line with `HC8-19` present; `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_help_claims_8.py -q -k "below_its_minimum" 2>&1 | tail -3` fails only on the 3.8 sentence.]]></verify>
  <done>Both help-claims tests state the new floor; the pytest is red only until the help is edited.</done>
</task>

<task type="auto" id="09-11">
  <name>Document the floor in the help files and CHANGELOG</name>
  <files>dash_setup.sthlp, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Apply TR-09.8's K2 parts: `dash_setup.sthlp` 40-42, 70, 80-82, 97-98, 110-113 and the new
    `{pstd}` on the tested baseline, keeping verbatim the sentences `test_help_claims_8.py`
    asserts; `dash.sthlp` 3131-3134; CHANGELOG `### Requirements` (330-334) rewritten:
    "- Python 3.13 or later, linked to Stata (`dash_setup` checks this). Was 3.8: bokeh 3.8
    needs 3.10, and 3.13 is the Python Stata links and both suites run under. (WP-06, WP-28)"
    and "- bokeh >= 3.8, numpy >= 2.3 and pandas >= 2.3, the versions the suites run under.
    Were 3.0, 1.23 and 2.0: every render imports `CustomJSTicker`, added in bokeh 3.6, so an
    installed 3.0-3.5 passed `dash_setup` and then failed every command; pandas is declared by
    dash itself because bokeh 3.9 no longer requires it. (WP-25, WP-28)"; and under `### Fixed
    in WP-28` a K2 line: "The declared minimums are the tested ones -- Python 3.13, bokeh
    3.8, numpy 2.3, pandas 2.3 -- everywhere they appear, `dash_setup` refuses anything below
    them, and the generated server app opens with `from __future__ import annotations`.
    (WP-28, GAPS2 K2)".
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_version_floor.py test/test_help_claims_8.py -q 2>&1 | tail -3` passes; the `test_setup_python_gate.cscript` batch log (re-run from a scratch directory) shows "dash_setup.sthlp states the same minimum (3.13)".]]></verify>
  <done>Every help passage and the CHANGELOG state the tested floor and the reason, and the floor-consistency test is green.</done>
</task>

<task type="auto" id="09-12">
  <name>Close K2 in BUGS.md and run both suites</name>
  <files>BUGS.md</files>
  <action>
    Append the closed K2 entry: Title "The declared minimums (Python 3.8, bokeh 3.0) are
    false: every render needs bokeh 3.6+, and the served app crashes at import on 3.8/3.9";
    File Names and Line Numbers `dash_setup.ado` (60, 73, 146-150, 285-296 at 91d97be),
    `dash_setup.sthlp` (40-42, 70, 80-82, 110-113), `dash.pkg` (17), `dash.ado` (205-207),
    `dash.sthlp` (3131-3134), `dash_render.py` (the app header 25198-25222); Description
    quoting GAPS2 K2 (`CustomJSTicker` since bokeh 3.6, r(7102) on every command after a
    passing setup, 55 annotations evaluated at import); Suggested fix (declare the tested
    floor everywhere, refuse below it, defer the annotations); Resolution "Fixed 25sep2026
    (WP-28)." naming
    `test/test_version_floor.py::TestTheFloorIsTheTestedBaseline::test_dash_setup_declares_the_stata_baseline`,
    `test/test_version_floor.py::TestTheGeneratedAppEvaluatesNoAnnotationAtImport::test_the_future_import_is_the_first_statement`
    and `test_setup_honesty.cscript` HON-29 and HON-30, and stating the residual by decision
    (DISCOVERY Q8): no interpreter or bokeh below the floor is run by any test. Then run the
    full suite once under each interpreter (`make test`, then `make test-dev`; never two full
    runs at once) and the certification scripts this section touched
    (`test_serve_port_in_use`, `test_serve_launch`, `test_serve_browser`,
    `test_render_log_clean`, `test_setup_python_gate`, `test_setup_honesty`,
    `test_program_coverage`, `test_help_claims_8`, `test_help_claims_4` — the last takes about
    two minutes), at most three at once.
  </action>
  <verify><![CDATA[Both full-suite logs report no failures and no skips beyond the baseline; every named cscript's log ends in its PASS line with no SKIP; `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py -q 2>&1 | tail -3` passes; `git status` shows a clean tree after the commit.]]></verify>
  <done>BUGS.md holds K2 closed naming its tests, both full-suite runs and the touched certification scripts are green, and the section's twelve commits are on `s3-bugs`.</done>
</task>

## Section completion criteria

- AC-09.1 to AC-09.6 hold.
- `dash serve, port(N)` against a listening socket on `127.0.0.1:N` prints `dash serve: no
  server started on port N: the port is in use` and returns r(198) in under 40 s; a real
  `dash serve, timeout(1)` still returns 0 after about 60 s with `/health` answering (HC4-19).
- `grep -c "max(1024, min(" dash_render.py` is 0; `python app.py --port 80` exits 2 naming
  1024 and 65535.
- `dash_setup.ado`, `dash_setup.sthlp`, `dash.sthlp`, `dash.pkg`, `dash.ado` and CHANGELOG all
  say Python 3.13, bokeh 3.8, numpy 2.3, pandas 2.3, and `test_version_floor.py` ties them to
  `conftest._BASELINES["stata"]`.
- A generated app's second statement is `from __future__ import annotations`.
- No test was deleted: every renamed test exists under its new name; the adversarial registry
  resolves; `function_test_map.py` and `program_coverage_map.py` name the new units.
- BUGS.md has the two closed entries; no open S1/S2 entry was added.

## Notes

- **The box, not an exception.** `runpy.run_path(…, init_globals={…})` copies the entries into
  the fresh module's globals; a dict is shared by reference, so what `__main__` writes into it
  survives `run_path` returning. Do not try `sys.exit`/`SystemExit` under Stata for the
  failure path and do not try to detect Stata by `sys.argv[0]` or by importing `sfi` inside
  `dash_render.py`'s `__main__`: the box is the only protocol, and the stub renderers on the
  ado-path (SRV-17..20, HC4-16, `test_serve_browser.cscript`) ignore it unharmed.
- **Threads under Stata store, never print.** HC4-19 already runs a thread in Stata's Python
  that only records what it saw. Keep every `print` on the main thread of the `python:` line.
- **Drain both pipes always.** A `Popen` with `stdout=PIPE, stderr=PIPE` and no reader hangs
  the child once 64 KB accumulate; Bokeh logs each session to stderr. The pumps run for the
  life of the child, the deque bounds memory.
- **`SO_REUSEADDR` on the tester, `listen()` on the holder.** The tester without it refuses
  a port in TIME_WAIT that Tornado (which sets it) would bind — a false "in use" right after
  a restart; the holder must listen because that is the measured case, and it must be on
  `127.0.0.1`: a holder on `0.0.0.0` leaves a loopback bind free on macOS (W §5).
- **The holder's lifetime in the cscript.** `_spu_s` lives in Stata's Python namespace, which
  persists for the session; it is closed by name after the `capture noisily {}` block on every
  path. `Popen` on POSIX closes inherited descriptors by default (`close_fds=True`), so the
  child never inherits the holder, and the pre-bind test in the same process still sees the
  port held. A leaked holder would only pin an ephemeral port until the session ends.
- **`_dash_port_value` is copied by source.** The app imports `argparse` as `_argparse`; the
  helper imports `argparse` locally so the copied text runs in both modules. Add it at the
  end of the function copy tuple: section 04 adds its writer functions to the same tuple and
  `patch -p1` merges cleanly only when the two insertions do not overlap.
- **argparse never validates a non-string default**, so the app's `__main__` validates
  `_a.port` itself; without that, `build_options["port"] = 80` embedded at build time would
  bind 80 (and fail with EACCES) or, worse, an in-range hand edit would pass unchecked.
- **`test_help_claims_2.py` names 5123.** With the pre-bind test in the launcher, a machine
  with 5123 taken fails that test spuriously; take a free port there (09-03).
- **`test_render_log_clean.cscript`** holds that `run_path`'s returned dict is never echoed:
  keep the `_dash_serve_ns =` assignment on the `runpy` line.
- **Every renamed test is named elsewhere**: the adversarial registry (860, 878) and, for new
  functions, `function_test_map.py`; `test_tracking_documents.py` also resolves every
  `file::Class::test` in BUGS.md — spell them exactly.
- **Order of the 09-10/09-11 pair**: the pytest flipped in 09-10 is red until the help sentence
  changes in 09-11; the commit message of 09-10 says so. Squash the pair if a red intermediate
  commit is unwanted.
- **Stata sessions.** Three at most, each `cd <dir> && STATATMP=<dir>/tmp/ arch -arm64
  /usr/local/bin/stata-mp -b do …`; more can rewrite `~/.stata19/console/stata19.rc` without
  its `python` lines, after which every Python cscript skips in a second. Check
  `c(python_exec)` in the log; restore with `set python_exec /opt/anaconda3/bin/python3,
  permanently`.
- **HC4-19 takes about 62 s** and SPU-01 must take under 40: if SPU-01 approaches a minute the
  server started, which means the fixture held the wrong address or the app bound the wildcard.
- **CHANGELOG heading.** Other batch-1 sections may also create `### Fixed in WP-28`; after
  merge keep exactly one, before `### Fixed after WP-27`. Section 19 consolidates.
