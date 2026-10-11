# Section 09: dash_setup on PEP 668 Pythons

> Part of: WP-29 · P0: P0.19 (GAPS2 H7a-g, plus N1-N4 found while measuring) · Risk: yellow · Batch: 1 · Depends on: 01 · Blocks: none · Case prefix: PEP · Tasks: 19, 1 commit (P0.19)


## Review amendments (u15 review, 30sep2026) — binding; they override any conflicting text below

The reviewed design for unit u15 was "sound with amendments". Every amendment is applied in this file:

- **A1 relative `c(python_exec)`.** `resolve_exe(exe, cwd)` resolves the linked interpreter before any argv or printed line uses it (TR-09.3). It is tested by `TestResolveExe` and by `TestStataEntryPoints::test_stata_pip_resolves_a_relative_exec`. A relative exec cannot be produced inside one cscript session, because `python set exec` is r(7101) once Python has started (T2). So the end-to-end proof is the release-gate step: its second session links the gate venv by a **relative** path (TR-09.24).
- **A2 detection runs in a child.** `detect_environment` runs `DETECT_CODE` in `c(python_exec)` and reads one JSON line back (TR-09.7). `safe_flags` keys on the child's version. The sandbox answers the probe by argv and never patches the live interpreter's `sys.prefix` or `sysconfig`. There is a pytest test (`TestDetectEnvironment::test_a_venv_without_pip_is_reported_without_pip`) and a sandbox case (PEP-04).
- **A3 the PYTHONPATH rationale.** The scrub is kept, but for the correct reason: a user- or Stata-supplied `PYTHONPATH` must not reach pip. It does not close a PLUS/PERSONAL injection, because those directories are on the in-process `sys.path`, not in `PYTHONPATH`; re-measured below (M6). The test is named `test_an_inherited_pythonpath_does_not_reach_the_child`.
- **A4 the N1 test must fail at HEAD.** The child runs with `LC_ALL=C PYTHONUTF8=0 PYTHONCOERCECLOCALE=0`, and a control asserts that plain `text=True` raises there. Re-measured under the pytest interpreter (M8).
- **A5 the default venv path.** `~/.dash` does not exist here. Missing ancestors inside the user's home are created 0700, each one exclusively (TR-09.13, TR-09.14), and a test proves the suggested default is accepted on a home without `~/.dash`.
- **A6 the symlink rule** applies to the final component only. The parent is resolved with `realpath`; `bin/python` and ancestors such as `/tmp` and `/var` are never refused.
- **A7 a missing `packaging` on a managed Python is a warning,** with rc 0 when the required packages are met (PEP-02).
- **A8 a reused venv below the floor is refused.** The venv's own interpreter is probed and gated on `_dash_pymin` before pip runs, and VERIFY_CODE gates it again (PEP-14, `TestVerifyIn`).
- **A9 the PEP 668 override hole is wider than the review measured.** A pip config file with `break-system-packages = true` also bypasses PEP 668 (M5). `child_env` therefore **sets** `PIP_BREAK_SYSTEM_PACKAGES=0`, which overrides both the variable and the config file (measured), rather than only dropping it. It also sets `PIP_USER=0` (measured: it overrides a config `user = true`, and an explicit `--user` still wins).
- **A10 Python 3.8 and bytecode.** `umask=` is passed only when the running interpreter is 3.9 or later on POSIX. `PYTHONDONTWRITEBYTECODE=1` is set explicitly.
- **A11 the release gate.** It asserts the link, the saved page and `/health` in a venv-linked session. It makes no claim about which interpreter the served child is (`_dash_launch_app` is S08's), and it never uses `, permanently`.
- **A12 the helper loader uses `findfile`,** which searches `.` first. This is recorded as residual R4 next to OQ5, not claimed as immunity.
- **A13 test isolation.** `TestAddUserSite` snapshots and restores `sys.path`, `sys.modules` and the import caches. The sandbox's "managed" state is an answer to the DETECT probe and never touches a real stdlib.
- **A14 printed commands.** Every printed command is also returned in `r()` (`r(hint_cmd)`, `r(venv_python)`), and the cases assert on `r()` as well as on the log.
- **A15 the spec whitelist** admits an optional `,<N` ceiling now, so P1.30's `bokeh>=3.8,<4` merges without loosening it.
- **A16 the help sentence and its pin change together.** The sentence is pinned at test_help_claims_8.py:1652-1653.

Corrections made while writing this section, each measured (M-numbers in Evidence):

- **C1.** Under an **anaconda** venv link, `sys.executable` is the venv's own interpreter (M3). N2 ("pip runs the BASE interpreter") is therefore specific to Homebrew's framework build. The fix, `c(python_exec)` and never `sys.executable`, is right either way.
- **C2.** On this console, `c(os)` is `"Unix"`, not `"MacOSX"` (M10). Windows quoting keys on `os.name == "nt"` inside the helper, never on `c(os)`.
- **C3.** `test/test_fixtures_are_committed.py` is **not** edited. It excludes itself from the files that can name a fixture (its docstring and the `readers` fixture), and its parametrized test checks every file under `test/fixtures` automatically. The fixture is named by `test/setup_sandbox.py` and `test/test_setup_pep668.py`.
- **C4.** New cscript cases use the manifest's prefix `PEP-` (index.md "Section numbers in case ids"; `grep -rn "PEP-[0-9]" test/ scripts/` is empty at `7421d3d`), not the research's PC-32..39 and HON-31..33.
- **C5.** With detection in a child (A2), every run that installs or hints starts one DETECT probe. The pinned call vectors of PC-18..21, HON-20..22, HON-26, HON-27 and HON-29 therefore gain that probe. They are flipped with that reason (Evidence, "Tests that pin today's behaviour"). PC-15, PC-16, PC-17, PC-22 and HON-19, HON-28, HON-30 still start no process.
- **C6.** The venv path never travels through Stata's parser between programs. `stata_venv_check` validates it and holds `(abs, state)` in the helper module for the immediately following `stata_venv` call (TR-09.17).
- **C7.** The GitNexus MCP has no index for this repository: `impact` answered `Repository "dash" not found. Available: TYME, PhotoShootPlannerPro`. Task 09-01 runs `gitnexus analyze` before the impact queries (R8). The blast radius below was taken with `grep`.
- **C8.** Flipped tests keep their names and case ids. The closed K2 entry in BUGS.md (line 2644) cites `test_version_floor.py::...::test_the_upgrade_line_names_the_linked_interpreter`, `PC-21` and `HON-29`, and other closed entries cite PC-18 and HON-14. A rename would leave those references dangling (`test_tracking_documents.py::TestEveryClosedEntryNamesATestThatExists`).

Applies to this section as to every WP-29 section (index.md, PLAN.md, BRIEF.md with index.md's deltas):
- **One commit, P0.19.** It holds the failing tests, the fix, the flips, the fixture and the closed BUGS.md entry. It is committed on `wp29-s09` after one green full-suite run (rules 4 and 7).
- **BUGS.md.** S01 opened `dash_setup fails on PEP 668 Pythons`. It is closed in place, and the `"P0.19"` key is deleted from `WP29_OPEN` in the same commit (A4).
- **CHANGELOG.md.** Only the `<!-- WP-29 P0.19 -->` marker that S01 placed at the end of `### Requirements` is replaced (index.md "P0 coverage").
- **Stata** runs only through `scripts/stata_slot.sh <scratch> <file>.do`, with `dash_nobrowser=1`. A cscript runs through the two-line driver.
- **No commit message names an AI tool or vendor.** `CLAUDE.md` and `.gitignore` are never staged.

## Overview

`dash_setup` installs dash's Python packages with pip. GAPS2 H7 measured that it cannot do this on an externally managed Python (PEP 668: Homebrew's, the system Python of Debian 12, Ubuntu 23.04, Arch Linux and later). Every pip call is refused with `error: externally-managed-environment`, with or without `--user`. The only guidance printed is pip's own stderr tail, which recommends `--break-system-packages`. After that, `dash_setup` prints a manual command, `python -m pip install bokeh>=3.8`, which a shell runs as an unpinned install that writes a file named `=3.8`. The upgrade hint uses single quotes, which `cmd.exe` does not honour.

The research measured four more defects on the same path (N1-N4):
- **N1.** Under the batch default locale, the `×` in pip's PEP 668 message kills `dash_setup` with r(7102).
- **N2.** pip runs `sys.executable`, which in a Homebrew-venv-linked Stata is the base interpreter, so the remedy PEP 668 recommends (a venv) is refused too.
- **N3.** pip runs from Stata's working directory, so a `pip/` package there runs instead of pip. This is a security defect.
- **N4.** The "To upgrade" line printed on a managed Python is itself refused.

After this section, `dash_setup` inspects the linked Python once, in a child process, before any pip command:
- **On a managed Python** it starts no pip process. It names the reason, suggests `dash_setup, venv("~/.dash/venv")`, never suggests `--break-system-packages`, and ends r(198) when a required package is unmet.
- **On a Python without pip** it prints the `ensurepip` line, or the distribution packages to install.
- **`dash_setup, venv(path)`** creates or reuses a private environment, installs the minimums into it, and verifies the versions and dash's schemes inside it. It then prints the exact `python set exec "<venv python>", permanently` line and says Stata must be restarted first.
- **Every printed command** names the resolved `c(python_exec)` and is quoted to run as printed in POSIX shells and `cmd.exe`.
- **Every pip process** runs with that interpreter, from a fresh 0700 directory, with `-P` on 3.11 and later, without an inherited `PYTHONPATH`, from wheels only, with `PIP_BREAK_SYSTEM_PACKAGES=0`, never prompting, with a 30-minute timeout, and with output decoded as UTF-8.
- **A `--user` install** is added to `sys.path` in the same run.

All of the mechanics live in a new stdlib-only module, `dash_setup_lib.py`, shipped beside `dash_render.py`. `dash_setup.ado` keeps the decisions and the counting.

Neither the saved page nor the served app changes. Both were measured working under a venv-linked Stata (M3, research m11), and the new release-gate step keeps that true.

**Test order and commit rule (rule 7, D1).**
- Tasks 09-01 to 09-04 add test infrastructure only (the fixture, the sandbox states and the unit tests) and touch no shipped file.
- Task 09-05 writes the dash_setup cases and runs every new regression test against the unmodified production tree. It saves the failure text to `<scratch>/09-P0.19-failure.txt` and does not commit.
- Tasks 09-06 to 09-17 make the tests green, flip the pinned tests, ship the helper, rewrite the help and add the gate step.
- Task 09-19 closes the entry and makes the section's one commit. Its subject ends `(WP-29 P0.19)` and its body opens with the saved failure text.

## Risk: [yellow] — a new shipped file and a rewired installer, on hosts this machine cannot measure

**Why.** `dash_setup` is the first command a user runs. A missing helper, or one bad quoting rule, blocks every install. The change also touches the test sandbox that keeps the certification suite from installing anything.

**Risk factors.**
1. `dash_setup_lib.py` must reach `PLUS/py` through `dash.pkg`, the release gate and the packaging tests. If the helper is missing, every install fails.
2. Windows has not been measured. `cmd.exe` and PowerShell quoting, `Scripts\python.exe` and `python set exec` on a Windows venv are covered by pure-function tests only. The same holds for Debian's patched `venv` ("ensurepip is not available") and the GUI's locale.
3. Thirteen sandbox and honesty pins flip (C5). A pin deleted rather than flipped loses coverage.
4. The extended sandbox changes the recorder that PC-14..26 and HON-26..30 run under. A sandbox bug could turn those cases green for the wrong reason.
5. Real venv tests cost about 1.3-2 s each (M2), and the gate step about 65 s (`dash serve, timeout(1)`).
6. Later merges in `dash_setup.ado` (outside WP-29): P1.32 (H6c at :76), P1.30 (the bokeh ceiling), P3.29 (H8 rollback, H10 pyc).

**Mitigation.**
1. `findfile` plus beside-`dash_setup.ado` lookup, a named failure item `dash's own files (dash_setup_lib.py)` (PEP-16), `test_packaging.py` `_PACKAGE_FILES`, `release_gate.do`'s installed-file loop and `release_verdict.INSTALLED`.
2. Exact-string Windows tests, POSIX tests that run the printed line through `/bin/sh`, and the residuals handed to S15.
3. Every flip carries a `Flipped:` line, and the test node count never falls (`pytest --collect-only -q | wc -l` before and after).
4. Task 09-03 reruns test_program_coverage.cscript and test_setup_honesty.cscript at the base with the extended sandbox, and every existing case must still PASS before any production change. New sandbox behaviour has its own tests in `test_setup_sandbox.py`.
5. At most four real-venv pytest tests (offline, `PIP_NO_INDEX=1`), two real-venv honesty cases, and the gate step only in the release gate (S15) plus one dev-mode run in 09-17.
6. The A15 whitelist, and the help and ado comments naming the merge points.

## Dependencies

- **Depends on: S01.**
  - The open BUGS.md entry `dash_setup fails on PEP 668 Pythons`.
  - The `"P0.19"` key in `WP29_OPEN` (`test/test_tracking_documents.py`).
  - The `<!-- WP-29 P0.19 -->` marker at the end of `### Requirements` in CHANGELOG.md.
  - The hygiene pins S01 sets (`test_cscript_hygiene.py:295 → 67`, `:313 → 49`). This section leaves them alone, and leaves the import-probe pin `13` (:322) unchanged: no captured `python: import` probe is added to a script that has none.
- **Blocks:** none.
- **Parallel batch:** 1. It can run with S02-S08. **Merge order:** S01, **S09**, S03, S02, S04, S06, S07, S05, S08 (index.md).
- **Why second:**
  - S09 is disjoint from the renderer.
  - It edits `test_cscript_hygiene.py` (the `_ALLOWED_INLINE_PY_MACROS` entry) and `test_help_claims_8.py` (the dash_setup class at :1578-1701) before S02 touches `test_help_claims_8.py` elsewhere.
  - It is the only section that edits `test_program_coverage.cscript`, `test_setup_honesty.cscript`, `test_setup_python_gate.cscript`, the release-gate scripts, `dash.pkg` and `dash_setup.*`.

## Evidence

All measurements were taken on StataNow 19.5 MP console, macOS arm64, through `scripts/stata_slot.sh`, or outside Stata with the interpreters named. In shell commands, `S` is a scratch directory.

### M1: the PEP 668 refusal and its bytes

```
$ env -u PYTHONPATH PIP_NO_INDEX=1 /opt/homebrew/bin/python3.13 -P -m pip install --dry-run \
    --disable-pip-version-check --no-input --only-binary=:all: 'bokeh>=3.8' 2> hb.err; echo rc=$?
rc=1
$ head -c 120 hb.err | od -c | head -3
0000000    e   r   r   o   r   :       e   x   t   e   r   n   a   l   l
0000020    y   -   m   a   n   a   g   e   d   -   e   n   v   i   r   o
0000040    n   m   e   n   t  \n  \n 303 227       T   h   i   s       e
$ tail -c 220 hb.err
 your Python installation or OS distribution provider. You can override this, at the risk of breaking
 your Python installation or OS, by passing --break-system-packages.
hint: See PEP 668 for the detailed specification.
```

The marker exists at `/opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13/lib/python3.13/EXTERNALLY-MANAGED`. The pytest interpreter is also managed:

```
$ python3 -c "import sys,sysconfig,os;print(sys.executable);print(os.path.isfile(os.path.join(sysconfig.get_path('stdlib'),'EXTERNALLY-MANAGED')))"
/opt/homebrew/opt/python@3.14/bin/python3.14
True
```

### M2: an offline venv that can see the linked Python's packages

This is the mechanism behind PEP-18 and the release gate.

```
$ time /opt/anaconda3/bin/python3 -m venv va          # real 0m1.311s, rc=0, va and va/bin drwxr-xr-x
$ ls -l va/bin/python*                                 # python -> python3 -> /opt/anaconda3/bin/python3 (symlinks)
$ echo /opt/anaconda3/lib/python3.13/site-packages > va/lib/python3.13/site-packages/dash_base.pth
$ env -u PYTHONPATH PIP_NO_INDEX=1 va/bin/python -P -m pip install --disable-pip-version-check --no-input \
    --only-binary=:all: packaging 'bokeh>=3.8' 'numpy>=2.3' 'pandas>=2.3'; echo pip_rc=$?
Requirement already satisfied: packaging in /opt/anaconda3/lib/python3.13/site-packages (25.0)
Requirement already satisfied: bokeh>=3.8 in /opt/anaconda3/lib/python3.13/site-packages (3.8.0)
Requirement already satisfied: numpy>=2.3 in ... (2.3.5)
Requirement already satisfied: pandas>=2.3 in ... (2.3.3)
pip_rc=0
$ mkdir -m 755 pre && /opt/anaconda3/bin/python3 -P -m venv --without-pip pre; echo rc=$?   # rc=0: venv fills an existing empty directory
```

### M3: a fresh Stata session linked to that venv by a relative path

This is A1 end to end. `g2.do`, run from `S` by the slot wrapper:

```
set linesize 255
capture noisily python set exec "va/bin/python"
display "LINK rc=" _rc
python: <prints each PYTHONPATH entry, sys.base_prefix, sys.executable, site.ENABLE_USER_SITE, sys.path[0], the encoding>
```

```
LINK rc=0
EXEC [va/bin/python]                                   (g1.do: c(python_exec) stays relative)
PPENTRY 0 /opt/anaconda3/lib/python3.13
PPENTRY 1 /opt/anaconda3/lib/python3.13/lib-dynload
PPENTRY 2 <S>/va/lib/python3.13/site-packages
PPENTRY 3 /opt/anaconda3/lib/python3.13/site-packages  (from the .pth; no Stata ado/py or PLUS directory: A3)
BASEPREFIX <S>/va
SYSEXE <S>/va/bin/python                               (C1: anaconda's venv, not the base)
USERSITE False
PATH0 ''
ENC US-ASCII 0
PYVENV_LAUNCHER None
DWB 1
```

`g1.do` in the same state: `dash scatter mpg weight, saving("g1.html") replace nobrowser` gave `SAVED rc=0` and wrote a 1,301,182-byte page. The research measured `dash serve` and `GET /health → {"status": "ok"}` under a Homebrew venv link (m11). There, `_dash_launch_app` (dash_render.py:31992, `_cmd = [sys.executable, app_path, "--port", str(port)]`) started the base `Python.app`, which imports bokeh through Stata's exported `PYTHONPATH`.

### M4: the child's own state, which the in-process view cannot see (A2)

One-line JSON from the DETECT-style probe, run as a child of each interpreter with `PYTHONPATH` unset:

```
va/bin/python                {"prefix": "<S>/va", "base_prefix": "/opt/anaconda3", ..., "pip": true, "ensurepip": true,
                              "user_site_enabled": false, "version": [3, 13, 9]}
/opt/homebrew/bin/python3.13 {"prefix": ".../python@3.13/.../3.13", "base_prefix": <same>, "pip": true,
                              "user_site_enabled": true, "version": [3, 13, 11]}
/opt/anaconda3/bin/python3   {"prefix": "/opt/anaconda3", "base_prefix": "/opt/anaconda3", "user_site_enabled": true,
                              "version": [3, 13, 9]}
```

The review (r1) measured that under a link to a `--without-pip` venv, the in-process `find_spec('pip')` finds Homebrew's base pip, while `<venv>/bin/python -m pip --version` gives `No module named pip`. Re-measured: `vnp/bin/python -m pip --version` gives `<S>/vnp/bin/python: No module named pip` (rc=1), and `vnp/bin/python -m ensurepip --upgrade` installs pip-25.2 offline in 1.3 s.

### M5: pip's own overrides of PEP 668 and `--user` (A9)

```
PIP_CONFIG_FILE=bsp.conf (break-system-packages = true), Homebrew 3.13      -> ERROR: Could not find a version ... (check bypassed)
PIP_CONFIG_FILE=bsp.conf PIP_BREAK_SYSTEM_PACKAGES=0                        -> error: externally-managed-environment (restored)
PIP_BREAK_SYSTEM_PACKAGES=1                                                 -> ERROR: Could not find a version ... (bypassed)
PIP_USER=1, in a venv                                                       -> ERROR: Can not perform a '--user' install. User site-packages are not visible in this virtualenv.
PIP_USER=0 plus --user, in a venv                                           -> the same --user error (the explicit flag wins)
PIP_CONFIG_FILE=u.conf ([install] user = true) PIP_USER=0, in a venv        -> ERROR: Could not find a version ... (config overridden)
```

### M6: the fixture's refusal texts (pip 25.x)

```
--user in a venv:   ERROR: Can not perform a '--user' install. User site-packages are not visible in this virtualenv.
-s --user:          ERROR: Can not perform a '--user' install. User site-packages are disabled for this Python.
no pip:             <S>/vnp/bin/python: No module named pip
offline no match:   ERROR: Could not find a version that satisfies the requirement zzdashnope (from versions: none)
                    ERROR: No matching distribution found for zzdashnope
-P on 3.9:          /usr/bin/python3 -P -c 1 -> "Unknown option: -P"  (so the DETECT probe never passes -P)
```

### M7: shell quoting (research T9, re-run by the TestShellLine design)

In sh, `python -m pip install bokeh>=3.8` hands pip the bare argument `bokeh` and redirects the output into a file named `=3.8`. `shlex.join` gives `'/Applications/My Python/bin/python3' -m pip install 'bokeh>=3.8'`. `cmd.exe` and PowerShell have not been measured (no Windows host).

### M8: the ASCII-locale decode failure, under the pytest interpreter (A4)

```
$ env -u LANG LC_ALL=C python3 a4.py pep668_head.bin
enc utf-8 utf8 1
plain ok 'error: externally-managed-environment\n\n× This environment is'     <- does NOT reproduce
$ env -u LANG LC_ALL=C PYTHONUTF8=0 PYTHONCOERCECLOCALE=0 python3 a4.py pep668_head.bin
enc US-ASCII utf8 0
plain raised 'ascii' codec can't decode byte 0xc3 in position 39: ordinal not in range(128)
fixed ... (encoding="utf-8", errors="replace" decodes it; printing it from that child raised UnicodeEncodeError,
           so the test's child must report with json.dumps(ensure_ascii=True))
```

Stata's batch interpreter is in exactly this state (M3: `ENC US-ASCII 0`). Its `print()` writes non-ASCII and SMCL braces as plain text (`g3.do`: `NONASCII before × after {bf:X} {stata dir}`, rc 0; `sys.stdout` is `_StataDisplay`).

### M9: Stata-side parsing (g4.do)

```
SFIToolkit.macroExpand("\x60c(python_exec)'") -> '/opt/anaconda3/bin/python3'
SFIToolkit.macroExpand("\x60c(pwd)'")         -> '<S>'
program _pv, rclass / syntax [, VENV(string)]:
  _pv, venv(`"a"b"')   -> rc 0, strlen 3     (a double quote reaches the local: the helper must refuse it)
  _pv, venv(a$b`c'd)   -> rc 0, strlen 2     (Stata expands $b and `c' before dash_setup sees them)
  _pv, venv(~/.dash/venv) -> rc 0, the text as typed
  _pv, venv()          -> rc 0, strlen 0     (indistinguishable from no option)
```

The research measured `syntax [, VENV(string)]`: an unknown option is r(198) `option garbage() not allowed`, and a stray argument stays r(101) (T7). `python set exec` after Python has started is r(7101), even with `, permanently`, and nothing persists (T2).

### M10: `c(os)` on this console

`SFIToolkit.macroExpand("\x60c(os)'")` gave `'Unix'` (g4.do). The helper decides Windows with `os.name == "nt"` (C2).

### The current code (HEAD 7421d3d)

`dash_setup.ado:18-23` declares no options and is not rclass:

```stata
18  program define dash_setup
19      version 16.0
...
23      syntax
```

`dash_setup.ado:101-114`, step 2, uses `sys.executable`, the Stata working directory, `text=True` with no encoding, and no check for a managed Python:

```stata
101     capture python: import packaging
102     if _rc != 0 {
103         display as text "  packaging .......... {res}missing{txt} — installing via pip..."
107         python: ///
108             import subprocess, sys; ///
109             r = subprocess.run( ///
110                 [sys.executable, "-m", "pip", "install", "packaging"], ///
111                 capture_output=True, text=True ///
112             ); ///
113             print(r.stdout[-500:] if r.stdout else ""); ///
114             print(r.stderr[-200:] if r.stderr else "")
```

`dash_setup.ado:157-207`, step 3, has the same call at 169-176. It retries `--user` whenever the import still fails (177-192), re-imports without `site.addsitedir` (193-195) and prints the bare fallback (196-197):

```stata
196                 display as error "  Failed to install `pkg'. Please install manually:"
197                 display as error "    python -m pip install `_spec'"
```

`dash_setup.ado:225-240` (below the minimum) and `_dash_pip_command` at 404-408:

```stata
231             _dash_pip_command "`pkg'" "`minver'"
232             display as text "      To upgrade: `r(cmd)'"
...
404 program define _dash_pip_command, rclass
405     version 16.0
406     args pkg minver
407     return local cmd `"`c(python_exec)' -m pip install '`pkg'>=`minver''"'
408 end
```

`_dash_setup_summary` is at 458-494 and `_dash_setup_check_files` at 594-666. The latter locates `dash_render.py` by `findfile`, else beside `dash.ado`, and probes the schemes in-process.

Help:
- dash_setup.sthlp:18-22 reads "It takes no arguments and no options; either is r(101)."
- :49-54 promises a `--user` retry unconditionally.
- :100-112, :144-150 and :154-159 show three `python: subprocess.run([sys.executable, ...])` recipes, which are wrong under a venv link (D3).
- There is no PEP 668, venv or ensurepip text.

dash.sthlp:
- :113-116 has the Setup syntax line `{cmd:dash_setup}`.
- :3320-3347 has the Dependencies list.

dash.pkg ships `f dash_render.py` (line 30) and no helper.

### Saved and served modes

There is no renderer change. `dash_setup` has neither mode, and filter moves do not apply.

Under a venv-linked Stata:
- Saved: `dash scatter ..., saving()` gave rc 0 (M3).
- Served: the app launches and answers `/health` (research m11).

`_dash_launch_app` (dash_render.py:31944, `_cmd` at :31992) is **not** changed here. S08 owns it (index.md R8: `_dash_launch_app` is S08's and S13's). The served copy lists (constants dash_render.py:28362-28497, functions 28535-28829) and the guards in test_statistical_helpers.py and test_resource_limits.py are untouched.

### Blast radius (grep, because the GitNexus index lacks this repository: C7)

| Symbol | Callers / readers at 7421d3d |
|---|---|
| `dash_setup` (program) | dash.ado's "Run dash_setup first" messages (unchanged), 26 cscripts that name it. Of these, `test_program_coverage`, `test_setup_honesty`, `test_setup_python_gate`, `test_setup_injection`, `test_setup_version_gate`, `test_help_claims_8`, `test_env_guards` (ENV-15/16 read its text) and `test_help_examples` run or read it. |
| `_dash_pip_command` | dash_setup.ado:231; test_setup_python_gate.cscript:171; test_setup_honesty.cscript:414 (`_hon_reload`); program_coverage_map.py:283; test_version_floor.py:123-133 |
| `_dash_setup_summary` | dash_setup.ado (7 call sites); HON-01..05; HC8-19 |
| `setup_sandbox` (module) | test_program_coverage.cscript, test_setup_honesty.cscript, test_setup_sandbox.py; test_server.py:11237 (a comment only) |
| `release_verdict.verdict` / `main`, `INSTALLED` | scripts/run_release_gate.sh:40; test_release_verdict.py (`_gate_log` iterates `INSTALLED` at :34) |

Risk: **MEDIUM**. A HIGH/CRITICAL symbol per R8's list is not touched. Task 09-01 re-takes the radius with `gitnexus_impact` once the index exists, and reports any HIGH or CRITICAL result before editing.

### Tests that pin today's behaviour (flip, never delete; keep names and case ids, C8)

| Pin | Today | After, and why |
|---|---|---|
| test_program_coverage.cscript PC-18 (:661-681) | `[["PYTHON","-m","pip","install","packaging"]]` | `[DETECT, [PYTHON_EXEC,"-P","-m","pip","install","--disable-pip-version-check","--no-input","--only-binary=:all:","packaging"]]`. `sys.executable` is the wrong interpreter under a venv (N2). There was no `-P`, private cwd or flags (N3), and the environment is now probed first (A2). |
| PC-19 (:685-708) | two pip vectors; the log holds `python -m pip install bokeh>=3.8` | `[DETECT, pip bokeh>=3.8, pip --user bokeh>=3.8]` with the flags. The log and `r(hint_cmd)` hold the shlex oracle line, because the bare unquoted line breaks in a shell (H7c/d, M7). |
| PC-20 (:712-729) | one pip vector | `[DETECT, pip bokeh>=3.8]`, for the reasons PC-18 gives |
| PC-21 (:733-751) | `"[]"`, and the upgrade line built by concatenation | `[DETECT]`: the below verdict must know whether the Python is managed (N4). The line comes from the shlex oracle. On this machine it reads the same, because the path holds no space. |
| test_setup_honesty.cscript HON-14 (:254-266) | r(101) | r(198): dash_setup now declares `venv()` (T7). HON-15 stays r(101). |
| HON-20 (:492-521) | calls `""`; `h20wantcmd` by concatenation | calls `-c <code>` (a probe, not an install); the oracle line |
| HON-21 (:523-544) | `-m pip install packaging` | `-c <code> \| -P -m pip install --disable-pip-version-check --no-input --only-binary=:all: packaging` |
| HON-22 (:546-557) | `-m pip install bokeh>=3.8 \| -m pip install --user bokeh>=3.8` | `-c <code> \| -P -m pip install <flags> bokeh>=3.8 \| -P -m pip install <flags> --user bokeh>=3.8`. The HON recorder answers the probe with `HONPIPOUT`, so detection fails and the run proceeds as on an ordinary Python. |
| HON-26 (:689-721), HON-27 (:723-751) | `PYTHON` vectors | `[PYTHON_EXEC,"-c","<ANY>"]` first, then the `PYTHON_EXEC` vectors with the flags |
| HON-29 (:790-811) | `"[]"`; concatenated line | `[[PYTHON_EXEC,"-c","<ANY>"]]`; the oracle line |
| `_hon_reload` (:413-420), `_hon_run_setup` (:426-447) | the program list; calls joined raw | add the five new programs; render a `-c` call as `-c <code>` |
| test_setup_python_gate.cscript:166-178 | `_want_cmd` by concatenation | the shlex oracle, inside `if "`c(python_exec)'" != ""` with no SKIP text (R1: no new Python-skip line) |
| test_version_floor.py::TestTheFloorIsTheTestedBaseline::test_the_upgrade_line_names_the_linked_interpreter (:117-134) | `c(python_exec)` and `-m pip install` in `_dash_pip_command`'s body | the body calls `stata_shell_line`; the below branch calls `_dash_pip_command` with `upgrade`; `dash_setup_lib.stata_shell_line` with a fake sfi names the macro-expanded `c(python_exec)` quoted |
| test_help_claims_8.py::TestDashSetupHelpMatchesTheAdo::test_it_installs_only_what_is_missing (:1659-1675) | 3 lines holding `"pip", "install"` | 0 such lines in the ado. 2 `_dash_setup_pip` call lines, each in the branch a failed import opens. `pip_install_argv` is the only pip vector, in dash_setup_lib.py. |
| test_help_claims_8.py::...::test_a_package_below_its_minimum_is_unmet_not_a_warning (:1652-1653) | the sentence "...reported, with the command that upgrades it, and counted as unmet." | the A16 sentence (TR-09.21) |
| test_cscript_hygiene.py `_ALLOWED_INLINE_PY_MACROS["dash_setup.ado"]` (:66-70) | `{"_spec": ...}` | the key is removed: no macro sits in a Python string any more. The positive control at :528-534 then has nothing stale. |
| test_help_examples.py::TestTheShownCommands::test_how_many (:497-506), ::test_the_two_line_pip_commands_are_joined (:508-513) | dash_setup.sthlp 7 lines; 11 distinct; pip lines `[2,2,2]`, `pip[0]` the `sys.executable` recipe | 7 lines, 0 inline, **13** distinct; pip lines `[1,1,1,1]`; `pip[0]` = `"/path/to/python3" -m pip install "bokeh>=3.8" "numpy>=2.3" "pandas>=2.3"`. Measured on the draft help below. |
| test_help_examples.cscript:549-553 (`_hx_pin shown`) | four `python:` pins | the new shown lines, pinned `placeholder` (TR-09.22) |

## User stories

- **US-09.1** As an installer on Homebrew, Arch or Ubuntu 25.04+ Python, I want `dash_setup` to tell me that my Python refuses pip and give me one command that works, so that I can install dash without breaking my system Python.
- **US-09.2** As that installer, I want `dash_setup, venv(path)` to build a private environment with dash's packages, verify it, and tell me exactly how to link Stata to it.
- **US-09.3** As a Windows user, I want every printed fix to run as printed in Command Prompt, and to be told what to add in PowerShell.
- **US-09.4** As an installer whose packages went to the user site, I want them found in the same run.
- **US-09.5** As an installer without pip, I want the one command that restores it.
- **US-09.6** As a security-conscious user, I want dash_setup's pip immune to a `pip/` directory in my working directory and to an inherited `PYTHONPATH`. I also want to be told that dash's own helper is found by Stata's usual search, which looks in the working directory first (residual R4).
- **US-09.7** As an installer in a non-UTF-8 session (Stata's batch mode), I want dash_setup never to crash on pip's non-ASCII output.
- **US-09.8** As the maintainer, I want the release gate to prove that both modes work in a session linked to a venv that `dash_setup, venv()` verified.

## Business requirements

- **BR-09.1** On an externally managed Python, `dash_setup` starts no pip process. It says the Python is externally managed (PEP 668), names it, suggests `dash_setup, venv(...)`, never suggests overriding the protection, and ends r(198) when bokeh, numpy or pandas is missing or below its minimum. A missing `packaging` alone is a warning with rc 0 (A7).
- **BR-09.2** `dash_setup, venv(path)`:
  - refuses an unsafe or invalid path, a linked Python below 3.13, and a reused environment whose Python is below 3.13, before any install;
  - creates the environment, or reuses one;
  - installs packaging, bokeh, numpy and pandas at their minimums into it;
  - verifies the versions and dash's schemes inside it;
  - prints `python set exec "<venv python>", permanently`, says Stata must be restarted first, and returns the interpreter in `r(venv_python)`.

  When Stata is already linked to that environment, it then runs the normal checks.
- **BR-09.3** Every printed command names the resolved `c(python_exec)` and runs as printed in POSIX shells and `cmd.exe`. A command that cannot be quoted safely for `cmd.exe` is described in words instead.
- **BR-09.4** A successful `--user` install is importable in the same run. No `--user` retry happens in a venv, on a managed Python, or where the user site is disabled.
- **BR-09.5** On a Python without pip, no pip process starts. The run prints the `-m ensurepip --upgrade` line where that works, or the distribution packages to install.
- **BR-09.6** No locale makes `dash_setup` fail on a child's output.
- **BR-09.7** Every child process `dash_setup` starts:
  - runs the resolved interpreter Stata is linked to;
  - runs from a fresh private directory, without an inherited `PYTHONPATH` and with Python's safe-path flag where available;
  - for pip, installs from wheels only, never prompts, keeps PEP 668's protection on, and stops after 30 minutes.
- **BR-09.8** `dash_setup` never runs `sudo`, a shell, `--break-system-packages`, or `python set exec`.
- **BR-09.9** The help documents all of the above, and an unknown option is r(198).
- **BR-09.10** The release gate shows that a session linked to a venv that `dash_setup, venv()` verified builds a saved page and serves `/health`.

## Technical requirements

### A. `dash_setup_lib.py` (new, package root, shipped to `PLUS/py`)

Module rules:
- It uses the stdlib only.
- It must parse under `ast.parse(src, feature_version=(3, 8))`: no `X | Y` annotations, no `match`, no parenthesized context managers.
- It has no side effect at import.
- It reaches every process start through the module attribute (`import subprocess`, then `subprocess.run(...)`; never `from subprocess import run`), and likewise `site.addsitedir`, so that the sandbox records both.
- Every function has a unit test named in `SETUP_FUNCTIONS` (TR-09.20).

Docstring header:

```
"""dash_setup_lib -- the mechanics of dash_setup's pip and venv steps (WP-29 P0.19).
dash_setup.ado decides and counts; this module runs children and formats commands.
Stdlib only; parses as Python 3.8; nothing runs at import."""
```

- **TR-09.1 Constants.**
  - `TIMEOUT = 1800`.
  - `_SPEC_RE = re.compile(r"^[A-Za-z0-9._-]+(>=[0-9][0-9.]*)?(,<[0-9][0-9.]*)?$")` (A15).
  - `_ENV_DROP = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT", "PYTHONEXECUTABLE", "__PYVENV_LAUNCHER__")`.
  - `_ENV_SET = {"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "PIP_BREAK_SYSTEM_PACKAGES": "0", "PIP_USER": "0"}` (A9, A10, M5).
  - `_PENDING = {}`, which holds the validated venv between two entry calls (C6).
  - `DETECT_CODE` and `VERIFY_CODE`, below.
- **TR-09.2 `DETECT_CODE`** is a string of Python 3.4+ syntax (no f-strings), run as `[exe, "-c", DETECT_CODE]` **without** `-P` (M6: 3.9 rejects `-P`). The private cwd keeps `sys.path[0]` harmless. It prints one JSON line:

  ```
  {"tag": "DASH_DETECT_V1", "prefix": sys.prefix, "base_prefix": getattr(sys, "base_prefix", sys.prefix),
   "stdlib": sysconfig.get_path("stdlib"), "marker": isfile(stdlib/EXTERNALLY-MANAGED),
   "pyvenv_cfg": isfile(prefix/pyvenv.cfg), "pip": find_spec("pip") is not None,
   "ensurepip": ..., "venv": ..., "user_site_enabled": bool(site.ENABLE_USER_SITE),
   "user_site": site.getusersitepackages(), "version": list(sys.version_info[:3]), "executable": sys.executable}
  ```

  Each `find_spec` is wrapped in a `try` that returns False on any exception.
- **TR-09.3 `resolve_exe(exe, cwd, which=shutil.which)`** returns an absolute path or None:
  - an absolute path is returned unchanged;
  - a bare name (no `os.sep`, no `os.altsep`) goes to `which(exe)`;
  - otherwise `os.path.abspath(os.path.join(cwd, exe))`, which must be `os.path.isfile`, else None.

  Symlinks are never resolved: a venv's `bin/python` is a symlink to the base (M2).
- **TR-09.4 `version_tuple(text)`.** `"3.13.9"` gives `(3, 13, 9)`, `"3.12.11 (x)"` gives `(3, 12, 11)` (first word), and anything unreadable gives `()`. `safe_flags(version)` returns `["-P"]` when `tuple(version[:2]) >= (3, 11)`, else `[]` (an empty version gives `[]`).
- **TR-09.5 `child_env(environ)`** returns a new dict: a copy minus `_ENV_DROP`, updated with `_ENV_SET`. It keeps `PIP_*` (index, proxy, `PIP_NO_INDEX`), `PYTHONUSERBASE`, `PYTHONNOUSERSITE`, `HTTP(S)_PROXY`, `PATH` and the rest. The input is not modified. **Reason (A3):** an inherited `PYTHONPATH`, the user's or the one Stata exports under a venv link (base stdlib ahead of the venv's own, M3), must not decide what pip or venv imports.
- **TR-09.6 `run_child(argv, timeout=TIMEOUT, runtime=None)`** returns `(rc, out, err)` and never raises:
  - `work = tempfile.mkdtemp(prefix="dash_setup_")` (mode 0700);
  - `kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=work, env=child_env(os.environ), shell=False, encoding="utf-8", errors="replace", timeout=timeout)`;
  - `runtime = sys.version_info if runtime is None else runtime`; when `os.name == "posix" and tuple(runtime[:2]) >= (3, 9)`, add `kw["umask"] = 0o022` (A10);
  - `subprocess.run(list(argv), **kw)` returns `(r.returncode, r.stdout or "", r.stderr or "")`;
  - `TimeoutExpired` gives `(-2, "", "dash_setup: the command did not finish within %d seconds" % timeout)`;
  - `OSError` gives `(-1, "", "dash_setup: could not start %s: %s" % (argv[0], exc.strerror or exc))`;
  - `finally: shutil.rmtree(work, ignore_errors=True)`.
- **TR-09.7 Detection.**
  - `interpret_detect(text)` is pure. It reads the last non-empty line as JSON. It returns `{"ok": False, "why": ...}` on malformed JSON, a missing `"tag": "DASH_DETECT_V1"`, or wrong types (prefix, base_prefix and stdlib must be str; the flags bool; version a list of 3 ints).
  - Otherwise it returns `{"ok": True, "in_venv": prefix != base_prefix or pyvenv_cfg, "externally_managed": (not in_venv) and marker, "pip", "ensurepip", "venv", "user_site_enabled": user_site_enabled and not in_venv, "user_site", "version": tuple, "executable"}`.
  - `detect_environment(exe)` runs `run_child([exe, "-c", DETECT_CODE])`. A non-zero rc gives `{"ok": False, "why": classify_failure(rc, err)}`; otherwise it returns `interpret_detect(out)`.
- **TR-09.8 `pip_install_argv(exe, specs, version, user=False)`** returns `[exe, *safe_flags(version), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--only-binary=:all:"] + (["--user"] if user else []) + list(specs)`. Each spec must `_SPEC_RE.fullmatch`, else `ValueError("dash_setup: refusing the requirement %r" % spec)`. OQ1 is decided yes (Notes), and the printed manual line carries no `--only-binary`.
- **TR-09.9 `classify_failure(rc, err)`** returns, in this order:

  | Condition | Result |
  |---|---|
  | rc 0 | `"ok"` |
  | rc -2 | `"timeout"` |
  | rc -1 | `"missing-interpreter"` |
  | `"externally-managed-environment"` in err | `"externally-managed"` |
  | `"No module named pip"` in err | `"no-pip"` |
  | `"Can not perform a '--user' install"` in err | `"user-unavailable"` |
  | `"ensurepip"` in err and (`"not available"` in err or `"No module named ensurepip"` in err) | `"no-ensurepip"` |
  | anything else | `"other"` |

  The substrings are the measured texts (M1, M6) and the fixture's records.
- **TR-09.10 `shell_line(argv, windows)`.** POSIX uses `shlex.join(argv)`. Windows double-quotes `argv[0]` always, and any other argument containing a space, a tab or one of `& | < > ^ ( ) ! , ; =`. An argument holding `"` or `%` raises `ValueError`. Example: `["C:\\Program Files\\Python313\\python.exe", "-m", "pip", "install", "bokeh>=3.8"]` gives `"C:\Program Files\Python313\python.exe" -m pip install "bokeh>=3.8"`.
- **TR-09.11 `add_user_site()`.** If `site.ENABLE_USER_SITE` is true, `us = site.getusersitepackages()`, `os.path.isdir(us)` holds and `us not in sys.path`, then it calls `site.addsitedir(us)` and `importlib.invalidate_caches()` and returns True. Otherwise it returns False (H7f, D5).
- **TR-09.12 `default_venv_path(windows, environ)`.** POSIX gives `"~/.dash/venv"` (shown as typed). Windows gives `os.path.join(environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local"), "dash", "venv")`.
- **TR-09.13 `validate_venv_path(raw, cwd, windows=None, getuid=None, home=None)`** returns `(abs_path, state, create)`, where `state` is `"new"`, `"empty"` or `"venv"` and `create` lists the missing ancestors (outermost first). It raises `VenvPathError(ValueError)` with these messages:
  1. `raw.strip()` empty: `"venv() names no directory"`.
  2. Any character below 0x20, or 0x7f, `"`, a backtick or `$`: `"holds a character dash_setup will not put in a command"` (M9: a `"` reaches the local).
  3. Expand a leading `~` (with `home` when given, else `os.path.expanduser`). A relative path is joined to `cwd`, so the argv element always starts with a separator and never with `-`.
  4. `head, name = os.path.split(path.rstrip(os.sep))`. If name is in `("", ".", "..")`: `"names no directory of its own"`. Then `parent = os.path.realpath(head)` and `final = os.path.join(parent, name)` (A6: only the final component is lstat'ed; ancestors may be symlinks, such as macOS `/tmp` and `/var`).
  5. `os.lstat(final)`:
     - a symlink: `"is a symbolic link"`;
     - not a directory: `"exists and is not a directory"`;
     - a directory holding `pyvenv.cfg`: state `"venv"`;
     - an empty directory: `"empty"`;
     - otherwise: `"is not empty and is not a virtual environment"`.
  6. POSIX ownership and modes (skipped on Windows):
     - an existing `final`, and for a venv also its `bin`, must have `st_uid == getuid()`, else `"is not owned by you"`, and `st_mode & 0o022 == 0`, else `"can be written by other users"`;
     - for a new path, the parent (if it exists) must be owned by you or root and, if group- or world-writable, sticky, else `"its parent directory can be written by other users and is not sticky"`;
     - if the parent is missing, walk up to the first existing ancestor, which gets the same check. Every missing component must lie inside `os.path.realpath(home)`, else `"its parent directory does not exist"` (A5).
- **TR-09.14 `create_venv(base_exe, path, state, create, version)`** returns `(ok, why)`:
  - each `create` ancestor gets `os.mkdir(a, 0o700)`;
  - for `"new"`, `os.mkdir(path, 0o755)`, then `os.chmod(path, 0o755)`. A `FileExistsError` on any of these gives `(False, "<path> appeared after it was checked; run dash_setup again")` (the race);
  - for `"new"` and `"empty"`, `run_child([base_exe, *safe_flags(version), "-m", "venv", path])`. A non-zero rc gives `(False, ...)`, naming `no-ensurepip` as "install python3-venv with your system's package manager";
  - `os.path.isfile(join(path, "pyvenv.cfg"))` and `os.path.exists(venv_python(path, os.name == "nt"))` must hold, else `(False, "the venv module ran but left no environment at <path>")`;
  - `"venv"` does nothing.
- **TR-09.15 `venv_python(path, windows)`** returns `join(path, "Scripts", "python.exe")` on Windows and `join(path, "bin", "python")` elsewhere.
- **TR-09.16 `VERIFY_CODE` and `verify_in(exe, render_py, minimums, version)`.**
  - `VERIFY_CODE` (tag `DASH_VERIFY_V1`) reads `sys.argv[1]`, a JSON `{"python": "3.13", "packaging": "", "bokeh": "3.8", "numpy": "2.3", "pandas": "2.3"}`, and `sys.argv[2]`, the absolute `dash_render.py`.
  - If `sys.version_info` is below `python`, it sets `why = "python"` and checks nothing else (A8). Otherwise, for each package, it imports it and reads `importlib.metadata.version`, then gates with `packaging.version.Version`. A package that fails to import, or `packaging` itself missing, is recorded with version `""`.
  - It then loads `render_py` by `spec_from_file_location("_dash_verify_render", ...)` and sets `schemes = not SchemeParser.resolve_or_fallback("s2color", "dash_setup").is_fallback`, under `warnings.catch_warnings()`.
  - It prints one JSON line `{"tag", "ok", "version", "packages", "schemes", "why"}`.
  - `verify_in` runs `run_child([exe, *safe_flags(version), "-c", VERIFY_CODE, json.dumps(minimums), render_py])`. Inputs reach the child only through argv. A malformed reply or a wrong tag is `{"ok": False, "why": "malformed"}`.
- **TR-09.17 Guidance text.**
  - **`managed_message(exe, windows, environ)`** returns `(text, cmd)`. `cmd` is `'dash_setup, venv("%s")' % default_venv_path(...)`, or the words `dash_setup, venv(<a directory of your choice>)` when that path holds a backtick, `$` or `"`. The text is:

    ```
      This Python is externally managed (PEP 668):
        <exe>
      It refuses pip installs, so dash_setup ran none, and dash_setup does not
      override that protection. Install dash's packages into a private
      environment instead:
        <cmd>
      then restart Stata and, before anything else uses Python, type the
      python set exec line that command prints.
    ```

    The text never contains `break-system-packages` (PEP-01 asserts its absence from the whole log).
  - **`nopip_message(exe, ensurepip, managed, windows)`** returns `(text, cmd)`.
    - `"  This Python has no pip: <exe>\n  dash_setup did not try to install anything with it.\n"`.
    - Where `ensurepip and not managed`: `"  Install pip into it first:\n    <cmd>\n"` with `cmd = shell_line([exe, "-m", "ensurepip", "--upgrade"], windows)`.
    - Otherwise `cmd = ""` and `"  Install pip with your system's package manager (on Debian and Ubuntu: python3-pip and python3-venv), or use dash_setup, venv(path).\n"`.
- **TR-09.18 Stata entry points.**
  - They read inputs with `sfi.Macro.getLocal` (the calling program's locals) and `sfi.SFIToolkit.macroExpand("\x60c(python_exec)'")` / `("\x60c(pwd)'")` (M9; the source holds `\x60`, never a backtick).
  - They set results with `sfi.Macro.setLocal` and print every environment-derived string with `print()`, which Stata shows as plain text (M8). `SFIToolkit.display` is never used.
  - Each catches `Exception` around its body, prints `"  dash_setup: internal error: <type>: <msg>"` and sets its failure locals, so that nothing reaches Stata as r(7102).
  - `windows = os.name == "nt"`. `_linked()` returns `(resolve_exe(macroExpand c(python_exec), macroExpand c(pwd)), raw)`.

  | Entry | Reads | Sets / prints |
  |---|---|---|
  | `stata_detect()` | — | `det_ok`, `det_managed`, `det_in_venv`, `det_pip`, `det_ensurepip`, `det_user` (user site usable: enabled, not venv, not managed), `det_version` (`"3.13.9"`), `det_python` (resolved). On failure it prints `"  (could not inspect <exe>: <why>; continuing as for an ordinary Python)"` and sets `det_ok 0`. A missing exe gives why `the linked Python <raw> was not found`. |
  | `stata_pip()` | `spec`, `user` (`"1"` allows the retry), `ver` | It runs `pip_install_argv`. If the outcome is `ok`, or a failure other than externally-managed, it prints `out[-500:]` and `err[-200:]` as today. If externally-managed, it prints only `err.splitlines()[0]`. If the outcome is `other` and `user == "1"`, it prints `"      retrying with --user..."`, runs the `--user` vector, prints its tails, and on rc 0 calls `add_user_site()`. On any success it calls `importlib.invalidate_caches()`. It sets `pip_outcome` (the final kind) and `pip_user` (`"1"` when `--user` ran). A `ValueError` from the spec gives outcome `other` with the message printed. |
  | `stata_shell_line()` | `spec`, `how` (`""`, `"upgrade"`, `"manual"`) | `pip_cmd = shell_line([exe, "-m", "pip", "install", spec], windows)`. On `ValueError` it gives `pip_cmd = 'pip install "<spec>" with the Python at <exe>'`. `pip_note = "In PowerShell, put & and a space before it."` on Windows, else `""`. `upgrade` prints `"      To upgrade: " + pip_cmd`; `manual` prints `"    " + pip_cmd`; then the note if any. |
  | `stata_guide()` | `kind` (`managed`, `nopip`), `ensurepip`, `managed` | prints `managed_message` or `nopip_message`; `guide_cmd` = its `cmd` |
  | `stata_venv_check()` | `venv` | `validate_venv_path(venv, pwd)`. On success it stores `_PENDING["venv"] = (abs, state, create)`, prints `"  venv() ............ " + abs` and sets `venv_ok 1`. On `VenvPathError` it prints `"  venv() ............ refused: <abs or raw>: <message>"` and sets `venv_ok 0`. |
  | `stata_venv()` | `pymin`, `minb`, `minn`, `minp` | See below. |

  `stata_venv()` steps:
  1. Pop `_PENDING["venv"]`. If it is missing, `venv_step "internal"`.
  2. Create it (`create_venv(exe, abs, state, create, sys.version_info)`, printing `"  creating the environment..."`): on failure, `venv_step "create"`.
  3. `detect_environment(vpy)`:
     - `ok` false or not `in_venv`: `venv_step "inspect"`;
     - version below `pymin`: print `"  The environment's Python <v> is below <pymin>."` and set `venv_step "python"` (A8);
     - `pip` false: print the ensurepip line for `vpy` and set `venv_step "pip"`.
  4. pip: print `"  installing packaging, bokeh, numpy and pandas into it..."`, run `pip_install_argv(vpy, ["packaging", "bokeh>=" + minb, "numpy>=" + minn, "pandas>=" + minp], version)`, and print the tails. On failure, `venv_step "pip"`.
  5. `verify_in(vpy, render_py, {...}, version)`, where `render_py = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dash_render.py"))`. On failure it prints which package or check failed and sets `venv_step "verify"`.
  6. `linked = os.path.realpath(os.path.dirname(os.path.dirname(exe))) == os.path.realpath(abs)`. This compares the venv roots: a realpath of the interpreters themselves would equate the base and the venv (M2).
  7. On success, `venv_cmd = 'python set exec "%s", permanently' % vpy`. Unless `linked`, print:

     ```
       The environment is ready: <abs>
       Restart Stata and, before anything else uses Python, type:
         <venv_cmd>
       then run dash_setup again.
     ```

     If `linked`, print `"  Stata is already linked to this environment; checking it."`.
  8. Sets `venv_step` (`""` on success), `venv_linked`, `venv_python` (= vpy), `venv_cmd` and `venv_base` (= exe).

  On a failure after creation, print `"  The environment was left at <abs>; you may delete it."`.

### B. `dash_setup.ado`

- **TR-09.19 Programs, rclass, returns.**
  - `program define dash_setup, rclass` and `syntax [, VENV(string)]`. The header comment becomes `*! Usage: dash_setup [, venv(path)]`.
  - The returns are:
    - `r(python)`: the resolved interpreter, set when detection or `venv()` ran;
    - `r(externally_managed)`: `"1"`/`"0"` when detection succeeded, else empty;
    - `r(hint_cmd)`: the last command printed for the user to type (an upgrade, manual, ensurepip, `dash_setup, venv(...)` or `python set exec` line);
    - `r(venv_python)` and `r(venv_linked)`: after a successful `venv()`.
  - Each `return local` is issued as soon as its value is known, because `_dash_setup_summary` exits 198 (the review's r3/r4 measured that `return local` survives subcalls and `exit 198`).
  - The `local min_bokeh/min_numpy/min_pandas` lines move from :153-155 to directly after the counters, so that `venv()` can read them. Their text is unchanged; test_version_floor reads it.
  - New programs, appended after `_dash_setup_check_files` in this order: `_dash_setup_lib`, `_dash_setup_detect`, `_dash_setup_pip`, `_dash_setup_guide`, `_dash_setup_venv`. Each is called as a statement from `dash_setup` (test_no_orphans.py). No `capture python: pass` or `python query` appears anywhere (ENV-16, test_cscript_hygiene).

  **`_dash_setup_lib, rclass`** locates `dash_setup_lib.py` with `findfile`, else beside `dash_setup.ado` (the `_dash_setup_check_files` pattern at :599-612, with `dash_setup.ado`), and makes the path absolute with `mata: st_local("lib", pathresolve(pwd(), st_local("lib")))`.
  - Not found: `display as error "  dash_setup_lib.py .. {err}not found{txt}"` and `display as error "    dash_setup needs it to run pip. Reinstall dash, or put its directory on the ado-path."`, then `return scalar ok = 0`.
  - Found, it loads the file with three one-line statements, saving and restoring `sys.dont_write_bytecode` around the load:

    ```stata
    python: import sys, sfi; sfi.Macro.setLocal("_dwb", "1" if sys.dont_write_bytecode else "0"); sys.dont_write_bytecode = True
    capture python: import importlib.util as _dsl_iu, sys, sfi; _dsl_p = sfi.Macro.getLocal("lib"); _dsl_m = sys.modules.get("_dash_setup_lib"); _dsl_new = _dsl_m is None or getattr(_dsl_m, "__file__", None) != _dsl_p; _dsl_s = _dsl_iu.spec_from_file_location("_dash_setup_lib", _dsl_p) if _dsl_new else None; _dsl_m = _dsl_iu.module_from_spec(_dsl_s) if _dsl_new else _dsl_m; (_dsl_s.loader.exec_module(_dsl_m) if _dsl_new else None); sys.modules["_dash_setup_lib"] = _dsl_m
    local _lrc = _rc
    python: import sys, sfi; sys.dont_write_bytecode = sfi.Macro.getLocal("_dwb") == "1"
    ```

  - If `_lrc != 0`, it displays `"  dash_setup_lib.py .. {err}could not be loaded{txt}"` and returns `ok = 0`. Otherwise it returns `ok = 1`.

  **`_dash_setup_detect, rclass`** calls `_dash_setup_lib`. If `r(ok) != 1` it returns `lib = "0"`. Otherwise it runs `python: import sys; sys.modules["_dash_setup_lib"].stata_detect()` and returns `lib "1"`, `ok`, `managed`, `in_venv`, `pip`, `ensurepip`, `user`, `version` and `python` from the `det_*` locals.

  **`_dash_setup_pip, rclass`** takes `args spec user ver`, runs `python: import sys; sys.modules["_dash_setup_lib"].stata_pip()`, and returns `outcome` and `user_tried`.

  **`_dash_setup_guide, rclass`** takes `args kind ensurepip managed`, runs `stata_guide()`, and returns `cmd`.

  **`_dash_setup_venv, rclass`** takes `args pymin minb minn minp`, presets `local venv_step "internal"`, runs `stata_venv()`, and returns `step`, `linked`, `venv_python`, `link_cmd` (= `venv_cmd`) and `python` (= `venv_base`).

  **`_dash_pip_command, rclass`** takes `args pkg minver how`. It calls `_dash_setup_lib` and, if that fails, returns `cmd ""`. Otherwise it sets `local spec "`pkg'>=`minver'"`, runs `stata_shell_line()`, and returns `cmd` and `note`. The two-argument call (test_setup_python_gate) prints nothing.

  **`_dash_setup_summary`** gains `[VENVready]`. With `failures == 0` and `venvready`, it prints `"{res}dash_setup complete{txt} for the environment named above."` and `"Restart Stata, link it with the python set exec line above, and run {cmd:dash_setup} again."` instead of the "All dependencies are satisfied" line and the two "You can now use dash" lines. HON-18's count of "All dependencies are satisfied" stays 1.

- **TR-09.20 The body of `dash_setup`, in order.**
  - Step 1 (:36-94) is unchanged.
  - Then the detection state:

    ```stata
    local det_done 0
    local det_managed 0
    local det_pip 1
    local det_ensurepip 1
    local det_user 1
    local det_version "`pyver'"
    local hint_cmd ""
    local guide_shown 0
    ```

  - The block **"ensure detection"** below is written in full at its two sites (Stata has no local functions):

    ```stata
    if `det_done' == 0 {
        _dash_setup_detect
        if "`r(lib)'" != "1" {
            local n_fail = `n_fail' + 1
            local fail_items `"`fail_items' dash's own files (dash_setup_lib.py)"'
            _dash_setup_summary , failures(`n_fail') warnings(`n_warn') items(`"`fail_items'`warn_items'"')
        }
        local det_done 1
        return local python `"`r(python)'"'
        if "`r(ok)'" == "1" {
            local det_managed "`r(managed)'"
            local det_pip "`r(pip)'"
            local det_ensurepip "`r(ensurepip)'"
            local det_user "`r(user)'"
            local det_version "`r(version)'"
            return local externally_managed "`det_managed'"
        }
    }
    ```

  - **venv() (new, after step 1, before step 2).** The `pyok == 0` refusal comes first, so that no process starts (PEP-13):

    ```stata
    if `"`venv'"' != "" {
        if `pyok' == 0 {
            display as error "  venv() ............ not started: Python `pyver' is below `c_pymin'."
            local n_fail = `n_fail' + 1
            local fail_items `"`fail_items' venv() (Python `pyver' needs `c_pymin')"'
            _dash_setup_summary , failures(`n_fail') warnings(`n_warn') items(`"`fail_items'`warn_items'"')
        }
        _dash_setup_lib
        if r(ok) != 1 { <n_fail+1; fail item "dash's own files (dash_setup_lib.py)"; summary> }
        local venv_ok "0"
        python: import sys; sys.modules["_dash_setup_lib"].stata_venv_check()
        if "`venv_ok'" != "1" { <n_fail+1; fail item "venv() (path refused)"; summary> }
        _dash_setup_venv "`c_pymin'" "`min_bokeh'" "`min_numpy'" "`min_pandas'"
        local v_step "`r(step)'"
        local v_linked "`r(linked)'"
        local v_py `"`r(venv_python)'"'
        local hint_cmd `"`r(link_cmd)'"'
        return local python `"`r(python)'"'
        return local hint_cmd `"`hint_cmd'"'
        if "`v_step'" != "" { <n_fail+1; fail item "venv() (`v_step' failed)"; summary> }
        return local venv_python `"`v_py'"'
        return local venv_linked "`v_linked'"
        if "`v_linked'" != "1" {
            _dash_setup_summary , failures(`n_fail') warnings(`n_warn') items(`"`fail_items'`warn_items'"') venvready
            exit
        }
        python: import importlib; importlib.invalidate_caches()
    }
    ```

  - **Before step 2:**

    ```stata
    local _need 0
    foreach m in packaging bokeh numpy pandas {
        capture python: import `m'
        if _rc != 0 local _need 1
    }
    if `_need' {
        <ensure detection>
    }
    ```

  - **Step 2.** In `capture python: import packaging` / `if _rc != 0 {`:
    - **managed:** `display as text "  packaging .......... {err}not installed{txt} — this Python is externally managed"`. If `guide_shown == 0`, run `_dash_setup_guide managed "`det_ensurepip'" "`det_managed'"`, set `hint_cmd` from `r(cmd)`, return it, and set `guide_shown 1`. Then add today's warning lines (`pkg_has_packaging 0`; `n_warn+1`; `packaging (version checks approximate)`).
    - **`det_pip == 0`:** `"  packaging .......... {err}not installed{txt} — this Python has no pip"`, `_dash_setup_guide nopip ...`, and the same warning.
    - **else:** keep today's `missing — installing via pip...` line, then `_dash_setup_pip "packaging" 0 "`det_version'"` (no `--user` for packaging, as today), `python: import importlib; importlib.invalidate_caches()`, and today's re-check and warning (:116-126).
  - **Step 3.** For each missing package, with `local _spec "`pkg'>=`min_`pkg''"`:
    - **managed:** `display as text "  `pkg' ............. {err}missing{txt}"`, the guide once, fail item `"`pkg' (externally managed Python)"`, summary.
    - **no pip:** the same line, `_dash_setup_guide nopip ...` once, fail item `"`pkg' (no pip)"`, summary.
    - **else:** today's `missing — installing via pip...` line, then:

      ```stata
      local _user = ("`det_user'" == "1" & "`det_managed'" != "1")
      _dash_setup_pip "`_spec'" `_user' "`det_version'"
      local _outcome "`r(outcome)'"
      if "`_outcome'" == "externally-managed" & `guide_shown' == 0 { <guide managed; hint_cmd; guide_shown 1> }
      if "`_outcome'" == "no-pip" { <guide nopip; hint_cmd> }
      python: import importlib; importlib.invalidate_caches()
      capture python: import `pkg'
      if _rc != 0 {
          if inlist("`_outcome'", "externally-managed", "no-pip") {
              local fail_items `"`fail_items' `pkg' (`_outcome')"'
          }
          else {
              display as error "  Failed to install `pkg'. Please install manually:"
              _dash_pip_command "`pkg'" "`min_`pkg''" manual
              local hint_cmd `"`r(cmd)'"'
              return local hint_cmd `"`hint_cmd'"'
              local fail_items `"`fail_items' `pkg' (could not install)"'
          }
          local n_fail = `n_fail' + 1
          _dash_setup_summary , failures(`n_fail') warnings(`n_warn') items(`"`fail_items'`warn_items'"')
      }
      ```

      The `retrying with --user...` line is printed by `stata_pip`.

      Every `_dash_setup_guide` call, at every site, is followed by `local hint_cmd `"`r(cmd)'"'` and `return local hint_cmd `"`hint_cmd'"'`. PEP-01, PEP-04 and PEP-15 assert `r(hint_cmd)`.
  - **The below verdict (:225-240).** Keep the `(below minimum ...)` display. Then run `<ensure detection>`.
    - If `det_managed == 1`: the guide once, instead of an upgrade line (N4).
    - Else: `_dash_pip_command "`pkg'" "`minver'" upgrade`, then `local hint_cmd `"`r(cmd)'"'` and `return local hint_cmd`.

    The `display as text "      To upgrade: `r(cmd)'"` line is removed: the helper prints it as plain text.
  - **Steps 4 and 5** are unchanged. `return local hint_cmd `"`hint_cmd'"'` is issued before the final summary.

- **TR-09.21 Never.**
  - `shell=True`, `sudo`, `--break-system-packages`, `--user` in a venv or on a managed Python, index or trusted-host flags, `{stata}` links or SMCL holding environment text, `python set exec` run by dash, `SFIToolkit.display` of environment text.
  - Any Stata macro inside a Python string literal on a `python:` line (test_cscript_hygiene).
  - `capture python: pass`.

### C. Help, package, gate, maps

- **TR-09.22 dash_setup.sthlp.** These exact paragraphs were measured with `help_examples.shown_all` on a draft: 7 shown lines, 0 inline, 13 distinct texts with dash.sthlp, pip lines `[1, 1, 1, 1]`. Every existing pin in test_help_claims_8.py and test_version_floor.py still holds.
  - Add `{viewerjumpto "Options" "dash_setup##options"}` and `{viewerjumpto "Externally managed Pythons" "dash_setup##pep668"}`.
  - **Syntax (replaces :18-22):**

    ```
    {p 8 17 2}
    {cmd:dash_setup} [{cmd:,} {opt venv(path)}]

    {pstd}
    An option other than {opt venv()} is r(198), and an argument is r(101).
    {cmd:venv()} with nothing in it is the same as no option.
    ```

  - **Step 3 (replaces :49-54):**

    ```
    {phang2}3.  The required Python packages.  Each missing one is installed
        with {cmd:pip}, asking for at least its minimum version.  If that fails
        for any reason but the two below, it is tried once more with
        {cmd:--user}, except in a virtual environment or where the user site is
        disabled, and a package installed there is found in the same run.  A
        package that still cannot be imported stops the run, r(198).  An
        installed package below its minimum is reported and counted as unmet,
        with the command that upgrades it or, on an externally managed Python,
        the way to set up a private environment instead.
    ```

  - **Two new paragraphs after step 4, before "The run ends with a summary":**

    ```
    {pstd}
    Before it runs {cmd:pip} for the first time, {cmd:dash_setup} inspects the
    linked Python once, in a separate process: whether it is externally
    managed, whether it has {cmd:pip}, and whether it is a virtual environment.
    On an externally managed Python, or one without {cmd:pip}, no {cmd:pip}
    command is run at all; see
    {help dash_setup##pep668:Externally managed Pythons} and
    {help dash_setup##troubleshooting:No pip}.

    {pstd}
    {cmd:pip} is always run as {cmd:c(python_exec)} {cmd:-m pip}, never as a
    bare {cmd:python} or {cmd:pip}; from a new private directory, not Stata's
    working directory; without Stata's {cmd:PYTHONPATH}; in Python's safe-path
    mode (3.11 and later); from wheels only, so no package's build script runs;
    without prompting; and with a time limit of 30 minutes per command.  Your
    own {cmd:pip} settings -- an index, a proxy -- still apply.
    ```

  - **New `{marker options}{title:Options}`, after Description:**

    ```
    {phang}
    {opt venv(path)} sets up a Python virtual environment at {it:path} holding
    the packages {cmd:dash} needs, for a Python that refuses {cmd:pip}
    installs.  {it:path} may be relative to the working directory and may start
    with {cmd:~}.  {cmd:dash_setup} creates the environment with the linked
    Python's {cmd:venv} module, or reuses one already at {it:path}; installs
    packaging, bokeh, numpy and pandas at their minimums into it; checks their
    versions, and that {cmd:dash}'s schemes can be read, inside it; and prints
    the command that links Stata to it, such as

    {phang2}{cmd:python set exec "/path/to/venv/bin/python", permanently}

    {pmore}
    On Windows the interpreter is {it:path}{cmd:\Scripts\python.exe}.  Stata
    reads this setting only when it first starts Python, so restart Stata and
    type the line before anything else uses Python -- otherwise it is r(7101),
    which a {cmd:profile.do} that runs Python also causes -- then run
    {cmd:dash_setup} again.  {cmd:dash_setup} never changes the setting itself.

    {pmore}
    A {it:path} that exists must be an empty directory or a virtual environment,
    owned by you and writable by no one else.  A {it:path} that is a symbolic
    link, or that holds a double quote, a backtick, a dollar sign or a control
    character, is refused before anything runs, r(198); so is a linked Python
    below 3.13, or a reused environment whose Python is.  Missing directories
    above {it:path} inside your home directory are created, readable by you
    alone.  If a step fails, {cmd:dash_setup} names it and leaves the
    environment in place; you may delete it.
    ```

  - **The manual-install paragraph (replaces :103-112):**

    ```
    {pstd}Missing packages are installed automatically.  If automatic
    installation fails (e.g., in a restricted network environment), install
    manually.  The command {cmd:dash_setup} prints names the Python Stata is
    linked to, {cmd:c(python_exec)}, quoted for your system; in a terminal it
    reads like this, with that path in place of {it:/path/to/python3}:

    {phang2}{cmd:"/path/to/python3" -m pip install "bokeh>=3.8" "numpy>=2.3" "pandas>=2.3"}

    {pstd}The double quotes matter: without them a shell reads {cmd:>} as a
    redirection, installs bokeh unpinned and writes a file named {cmd:=3.8}.
    The line runs as written in a macOS or Linux shell and in Windows Command
    Prompt; in PowerShell, put {cmd:&} and a space before it.
    ```

  - **New `{marker pep668}{title:Externally managed Pythons}`, before Troubleshooting:**

    ```
    {pstd}
    Some Pythons are marked as managed by the operating system -- Homebrew's,
    and the system Python of Debian 12, Ubuntu 23.04, Arch Linux and later
    releases -- under PEP 668: a file named {cmd:EXTERNALLY-MANAGED} beside the
    standard library.  They refuse {cmd:pip} installs, with or without
    {cmd:--user}.  On such a Python {cmd:dash_setup} runs no {cmd:pip} command:
    it says why, names the Python, and ends with r(198) when a required
    package is missing or below its minimum (a missing {cmd:packaging} alone is
    a warning).  It never uses {cmd:--break-system-packages} or {cmd:sudo}, and
    a {cmd:pip} setting that turns that protection off is overridden.  Set up a
    private environment instead, which leaves the managed Python as it is:

    {phang2}{cmd:dash_setup, venv("~/.dash/venv")}

    {pstd}
    then restart Stata, type the {cmd:python set exec} line that command
    prints, and run {cmd:dash_setup} again.  On Windows, {cmd:dash_setup}
    suggests {cmd:%LOCALAPPDATA%\dash\venv}.
    ```

  - **Troubleshooting.** Keep "Python not found". After it, add:

    ```
    {pstd}{ul:No pip}

    {phang2}A Python without {cmd:pip} is not asked to run it.  Where the
    Python has its standard {cmd:ensurepip} module, {cmd:dash_setup} prints the
    command that installs {cmd:pip}:

    {phang2}{cmd:"/path/to/python3" -m ensurepip --upgrade}

    {phang2}Debian and Ubuntu remove {cmd:ensurepip}; there, install the
    {cmd:python3-pip} and {cmd:python3-venv} packages with the system's
    package manager, or use {opt venv()}.
    ```

    Replace the `python: subprocess.run(...)` recipes at :147-150 and :156-159 with:
    - `{phang2}{cmd:"/path/to/python3" -m pip install --index-url https://your.mirror/simple "bokeh>=3.8"}`;
    - under "Package version below minimum", the lead `{phang2}Upgrade a specific package, unless the Python is externally managed (see above):` and `{phang2}{cmd:"/path/to/python3" -m pip install --upgrade "bokeh>=3.8"}`.
  - Dependencies :99-101: after "prints the {cmd:pip} command for the Python Stata is linked to", insert ", or on an externally managed Python the way to set up a private environment,".
- **TR-09.23 dash.sthlp.**
  - :115 becomes `{cmd:dash_setup} [{cmd:,} {opt venv(path)}]` (Syntax section, not read by help_examples).
  - After the Dependencies list (after :3347, before `{marker author}`), add one paragraph:

    ```
    {pstd}
    On a Python that the operating system manages (PEP 668: Homebrew's, and
    recent Debian, Ubuntu and Arch Linux system Pythons), {cmd:dash_setup}
    installs nothing and says so; {cmd:dash_setup, venv(}{it:path}{cmd:)} sets
    up a private environment instead and prints the {cmd:python set exec} line
    that links Stata to it.  See
    {help dash_setup##pep668:Externally managed Pythons}.
    ```

- **TR-09.24 dash.pkg.**
  - Add `f dash_setup_lib.py` after `f dash_render.py` (line 30).
  - Description lines 19-20 become: `d Run -dash_setup- once after installation: it checks the`, `d dependencies and installs the missing Python packages; where the`, `d Python refuses pip installs (PEP 668), -dash_setup, venv(path)-`, `d sets up a private environment instead.`
- **TR-09.25 Release gate (A11, A1 end to end).**
  - **New `scripts/release_gate_venv.do`.**
    - Header: `*! release_gate_venv.do -- the venv-linked sessions of the release gate (WP-29 P0.19)`.
    - `version 18`, `args work adodir mode phase`, `set linesize 255`, `global dash_nobrowser 1`, and no `/*` anywhere (test_release_verdict.py:251).
    - Mode `plus`: `sysdir set PLUS "`adodir'"` and `mata: st_global("S_ADO", "BASE;SITE;PLUS")`. Mode `dev`: `adopath ++ "`adodir'"`.
    - Phase `venvmake`:
      1. `quietly cd "`work'"`.
      2. A python block makes `gatevenv` from `sys.executable` (the linked interpreter, M3) with `subprocess.run([...,"-m","venv","gatevenv"])`, and writes `dash_base.pth` holding `sysconfig.get_paths()["purelib"]` into its site-packages.
      3. `display "GATE venv-made rc=<rc>"`.
      4. `capture noisily dash_setup, venv("gatevenv")` and `display "GATE venv-setup rc=`rc' ready=<r(venv_python)!=""> linked=`r(venv_linked)'"`.
    - Phase `venvuse` (a fresh session):
      1. **First** `quietly cd "`work'"`, then `capture noisily python set exec "gatevenv/bin/python"` (relative, A1; never `, permanently`), and `display "GATE venv-link rc=`_rc'"`.
      2. Then `capture noisily dash_setup, venv("gatevenv")` and `display "GATE venv-setup2 rc=`rc' linked=`r(venv_linked)'"`.
      3. `sysuse auto, clear` and `capture noisily dash scatter mpg weight, saving("gatevenv.html") replace nobrowser`, then `display "GATE venv-saved rc=`rc' html=<file exists>"`.
      4. The HC4-20 pattern (test_help_claims_4.cscript:503-562): a free port from a bound socket, a polling thread on `http://127.0.0.1:<port>/health`, `capture noisily dash serve, port(<port>) timeout(1) nobrowser`, then `display "GATE venv-served rc=`rc' health=<1 when status 200 and the body holds "status": "ok">"`.
      5. `display "GATE venv-done"`.
  - **`scripts/run_release_gate.sh`.** After `log=...` (line 39) and before the verdict, add:

    ```sh
    # WP-29 P0.19: the venv-linked sessions, from $dir/work so the second links by a relative path.
    for phase in venvmake venvuse; do
        (cd "$dir/work" && PIP_NO_INDEX=1 STATATMP="$dir/tmp/" arch -arm64 "$STATA" -b do \
            "$REPO/scripts/release_gate_venv.do" "$dir/work" "$dir/work/plus/" plus "$phase" >/dev/null 2>&1)
    done
    ```

    The verdict becomes `"$PYTHON" "$REPO/scripts/release_verdict.py" "${log:-$dir/release_gate.log}" "$REPO" "$newest" "$dir/work/venvmake.log" "$dir/work/venvuse.log"`. Batch Stata names a log after the command line's last word, which is the phase.
  - **`scripts/release_verdict.py`.**
    - `INSTALLED` gains `"dash_setup_lib.py"` after `"dash_render.py"`.
    - A new `venv_verdict(make_text, use_text)` returns a list of problems. It requires `venv-made rc=0`, `venv-setup rc=0 ready=1 linked=0`, `venv-link rc=0`, `venv-setup2 rc=0 linked=1`, `venv-saved rc=0 html=1`, `venv-served rc=0 health=1` and `venv-done`, through the existing `parse`.
    - `main` accepts 4 or 6 argv entries; with 6, it adds `venv_verdict`'s problems and lines.
  - **`scripts/release_gate.do:62`.** The foreach list gains `dash_setup_lib.py`.
- **TR-09.26 Maps (R2).**
  - **`test/function_test_map.py`.** Append a new dict after `TEST_ONLY`: `SETUP_FUNCTIONS = {"<qualname>": "test/test_setup_pep668.py::<Class>::<test>", ...}`. It has one key per function and nested function defined in dash_setup_lib.py, in alphabetical order, with the tests named in "TDD test stubs".
  - **`test/test_function_test_map.py`.** Add `test_every_dash_setup_lib_function_names_its_test`. It parses dash_setup_lib.py with `ast` and collects the qualnames (as `test_the_universe_is_the_whole_file` does for dash_render.py, `<locals>` included). It requires the set to equal `SETUP_FUNCTIONS`'s keys, and requires every value to match `_NODE` and to exist (through the existing `_defs_of`).
  - **`test/program_coverage_map.py` `"dash_setup.ado"`** (source order):
    - `dash_setup` gains `"test_program_coverage.cscript:PEP-08"`.
    - `_dash_pip_command` becomes `("test_setup_python_gate.cscript", "test_program_coverage.cscript:PC-19", "test_program_coverage.cscript:PC-21")`.
    - New entries after `_dash_setup_check_files`:
      - `"_dash_setup_lib": ("test_program_coverage.cscript:PEP-16", "test_program_coverage.cscript:PEP-01")`;
      - `"_dash_setup_detect": ("test_program_coverage.cscript:PEP-04", "test_program_coverage.cscript:PEP-01")`;
      - `"_dash_setup_pip": ("test_program_coverage.cscript:PEP-07", "test_program_coverage.cscript:PEP-06", "test_program_coverage.cscript:PC-18")`;
      - `"_dash_setup_guide": ("test_program_coverage.cscript:PEP-01", "test_program_coverage.cscript:PEP-04")`;
      - `"_dash_setup_venv": ("test_program_coverage.cscript:PEP-08", "test_setup_honesty.cscript:PEP-18")`.
- **TR-09.27 Packaging tests.**
  - `test/test_packaging.py:51`: `SHIPPED_SOURCES` gains `"dash_setup_lib.py"`.
  - `:310-311`: `_PACKAGE_FILES` gains `"dash_setup_lib.py"`.
  - `test/test_installed_layout.py:11`: the layout block gains `PLUS/py/dash_setup_lib.py` under `PLUS/py/dash_render.py` (docstring only).
- **TR-09.28 Fixture.**
  - **New `scripts/extract_pip_refusals.py`.** It uses the stdlib only and argv lists, never a shell, and works in `tempfile.mkdtemp()`.
  - Usage: `python3 scripts/extract_pip_refusals.py --managed <python with EXTERNALLY-MANAGED> --plain <python without it> --out test/fixtures/pip_refusals.json`.
  - It runs, with `PIP_NO_INDEX=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1` and `PYTHONPATH` removed:
    - `externally_managed`: `[managed, "-m", "pip", "install", "--dry-run", "--no-index", "bokeh>=3.8"]`;
    - `user_in_venv`: `[<venv>/bin/python, "-m", "pip", "install", "--dry-run", "--no-index", "--user", "zzdashnope"]`, from `plain -m venv`;
    - `user_disabled`: `[plain, "-s", "-m", "pip", "install", "--dry-run", "--no-index", "--user", "zzdashnope"]`;
    - `no_pip`: `[<vnp>/bin/python, "-m", "pip", "--version"]`, from `plain -m venv --without-pip`;
    - `offline_no_match`: `[<venv>/bin/python, "-m", "pip", "install", "--no-index", "zzdashnope"]`.
  - Each record is `{"argv": [...] with the temp dir written "<tmp>", "rc": int, "stderr": str with "<tmp>" substituted}`.
  - `_meta`: `{"stata_version": "not used (pip output)", "pip_version": <managed -m pip --version, first word after "pip">, "python_version": <managed version>, "born_date": "<ddmonyyyy>", "dash_commit": <git rev-parse HEAD via an argv list>, "extracted": <ISO timestamp>}`.
  - The script refuses (exit 2) when `--managed` lacks the marker or `--plain` has it. It writes JSON with `ensure_ascii=False, indent=1` and a trailing newline. The fixture is `git add -f`'d.

## Boundaries

- No change to dash_render.py: not `_dash_launch_app`, the served copy lists or any JS. The served child's interpreter and its reliance on Stata's `PYTHONPATH` belong to S08 (u12) and are recorded for S15 (OQ4).
- No change to dash.ado (its "Run dash_setup first" messages stay) or to dash_parse.mata.
- No rollback of partial installs (GAPS2 H8, P3.29), no pyc handling beyond `PYTHONDONTWRITEBYTECODE` (H10), no bokeh ceiling (P1.30; the whitelist only admits one), and no retry or architecture hint at :76 (H6c, P1.32).
- No `--target`/`python set userpath` route (OQ3), no hash-pinned installs (OQ7), no change to `_dash_setup_summary`'s `Unmet:` list (OQ6).
- No edit to `test/run_all_cscripts.do`, the hygiene pins at :295/:313, the import-probe pin at :322, `test_gaps2_truth.cscript` or `test_wp29_truth.cscript`. No captured `python: import` probe and no `SKIP ... Python` text is added to any script that lacks one (R1).
- Tracking documents beyond BUGS.md, CHANGELOG.md and `WP29_OPEN` (GAPS2.md, ROADMAP.md, AGENTS.md) are S15's (A5). Their text is in Notes.
- The release gate is not run inside this section (S15.6). Only its new do-file is run, in dev mode, in 09-17.

## Stata truth

No twoway truth and no `test_wp29_truth.cscript` block: `dash_setup` has no twoway analogue. The truths are pip's, PEP 668's and Stata's Python integration. They are measured in Evidence M1-M10 and kept in two places:
- **`test/fixtures/pip_refusals.json`** (TR-09.28): pip's refusal texts, replayed by the sandbox and by `TestClassifyFailure`. It carries the D12 `_meta` stamp (`stata_version` is "not used") and is added with `git add -f`. `test_fixtures_are_committed.py` checks it automatically (C3).
- **Real-process cases.**
  - PEP-17, PEP-18 and PEP-19 in `test_setup_honesty.cscript` run real venvs, offline, under Stata's own interpreter, which is US-ASCII in batch (M3).
  - The release-gate step runs a real venv-linked session.

Every Stata run uses the slot wrapper, with a cscript through the two-line driver:

```sh
R=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s09      # the worktree
X=<scratch>/s09; mkdir -p "$X"
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$R" "$R" test_program_coverage.cscript > "$X/run_test_program_coverage.do"
dash_nobrowser=1 "$R/scripts/stata_slot.sh" "$X" "$X/run_test_program_coverage.do"     # log: $X/run_test_program_coverage.log
```

Read the log and never relaunch to check on it. A SKIP is not a pass: test_program_coverage and test_setup_honesty exit 222 when `c(python_exec)` is empty, and test_setup_honesty skips HON-19..30 and PEP-17..19 when packaging, bokeh, numpy or pandas is not importable. Check `c(python_exec)` before trusting either.

## TDD test stubs

All are new unless marked flipped. Each regression test names the failure it shows at the base (`<base>` = `<scratch>/batch-1-base.txt`, which is `wp29-p0` after step 0a). Tests that pass at the base are **guards** and are listed as such in 09-05's record.

**`test/test_setup_pep668.py`** (new, task 09-04). A module fixture `lib` loads `dash_setup_lib.py` from the repo root by `spec_from_file_location`, or calls `pytest.fail("dash_setup_lib.py is missing (WP-29 P0.19)")` if absent. Every test therefore fails individually at the base, and none errors at collection. `FIX = json.load(open("test/fixtures/pip_refusals.json"))`. Test-writing rules come from test_test_integrity.py: no broad `except` in a test, refusals asserted with `pytest.raises(..., match=...)`, every test asserts, and no early `return`.

- `TestResolveExe::test_an_absolute_path_is_unchanged`; `::test_a_bare_name_goes_to_which` (fake `which`); `::test_a_relative_path_is_resolved_against_the_stata_directory` (a file under tmp gives the absolute path; a missing one gives None) (A1).
- `TestVersionAndFlags::test_version_tuple`, parametrized: `"3.13.9"`, `"3.12.11 (x)"`, `"abc"`, `""`. `::test_safe_flags_only_from_3_11`: `(3,8)`, `(3,10,9)` give `[]`; `(3,11,0)`, `(3,13,9)` give `["-P"]`; `()` gives `[]`.
- `TestChildEnv::test_python_variables_are_dropped_and_protections_set`. The input holds all of `_ENV_DROP`, `PIP_BREAK_SYSTEM_PACKAGES=1`, `PIP_USER=1`, `PIP_INDEX_URL`, `PIP_NO_INDEX`, `PYTHONUSERBASE`, `HTTPS_PROXY` and `PATH`. The output drops the first, sets `"0"`/`"0"`/`utf-8`/`"1"`, and keeps the rest. The input is unchanged.
- `TestRunChild::test_non_ascii_output_under_an_ascii_locale_is_decoded` (N1, A4). A child `[sys.executable, "-c", CODE, lib_path, hexbytes]` runs with `env` minus `LANG`, `LC_*`, `PYTHONIOENCODING` and `PYTHONUTF8`, plus `LC_ALL=C PYTHONUTF8=0 PYTHONCOERCECLOCALE=0`. CODE loads the module and uses a fake interpreter writing `bytes.fromhex(hexbytes)` (the fixture's `externally_managed.stderr` in UTF-8) to stderr with exit 1. It tries plain `subprocess.run(fake, capture_output=True, text=True)` and records `"raised"` on `UnicodeDecodeError`, then calls `run_child(fake)`. It prints `json.dumps(...)` with the default `ensure_ascii=True` (M8). Assert: `"ascii"` in `enc.lower()`, control `"raised"`, rc 1, `"\u00d7"` and `"externally-managed-environment"` in err. At the base: `pytest.fail` (module missing).
- `TestRunChild::test_a_pip_package_in_the_working_directory_is_not_run` (N3). Write `evil/pip/__init__.py` (empty) and `evil/pip/__main__.py`, which creates `marker`.
  - Control: `subprocess.run([sys.executable, "-m", "pip", "--version"], cwd=evil, capture_output=True)` creates the marker. Remove it.
  - Then `monkeypatch.chdir(evil)` and `run_child([sys.executable, *lib.safe_flags(sys.version_info), "-m", "pip", "--version"])`: the marker is absent, rc 0, `"pip"` in out.
- `TestRunChild::test_an_inherited_pythonpath_does_not_reach_the_child` (A3). `monkeypatch.setenv("PYTHONPATH", evil)`. The control `subprocess.run([sys.executable, "-m", "pip", "--version"], cwd=tmp)` creates the marker; `run_child` does not.
- `TestRunChild::test_the_child_runs_in_a_private_directory_that_is_removed`. The child prints `os.getcwd()` and `oct(os.stat(".").st_mode & 0o777)`: the directory is not the test's cwd, its mode is `0o700`, and it no longer exists afterwards.
- `TestRunChild::test_a_missing_interpreter_and_a_timeout_are_reported_not_raised`. `[tmp/"nope"]` gives rc -1 with the path in err. `[sys.executable, "-c", "import time; time.sleep(5)"]` with `timeout=0.5` gives rc -2.
- `TestRunChild::test_the_call_is_shell_free_and_umask_only_where_popen_takes_it` (A10). Monkeypatch `lib.subprocess.run` to a recorder. With `runtime=(3,8,0)`, no `umask` key. With `(3,9,0)` on POSIX, `umask == 0o022`. Always `shell is False`, `stdin is subprocess.DEVNULL`, `encoding == "utf-8"`, `errors == "replace"`, `"PYTHONPATH" not in env`, `env["PIP_BREAK_SYSTEM_PACKAGES"] == "0"`, and `cwd != os.getcwd()`.
- `TestDetectEnvironment::test_interpret_detect_rules`, parametrized:
  - a marker with prefix equal to base_prefix and no cfg: managed;
  - a marker with prefix different from base: venv, not managed;
  - `pyvenv_cfg` with prefix equal to base: venv (Stata's emulation, T1);
  - malformed JSON: `ok` False;
  - a wrong tag: `ok` False;
  - version `"3"` (a string): `ok` False;
  - user site enabled in a venv: `user_site_enabled` False.
- `TestDetectEnvironment::test_the_test_interpreter_reports_itself`. `detect_environment(sys.executable)` is ok, its version equals `tuple(sys.version_info[:3])`, and `externally_managed` equals the marker check on this interpreter's stdlib (True here, M1).
- `TestDetectEnvironment::test_a_venv_without_pip_is_reported_without_pip` (A2). Make a venv with `subprocess.run([sys.executable, "-m", "venv", "--without-pip", v])`. Detect on `v/bin/python`: `in_venv` True and `pip` False, while `importlib.util.find_spec("pip")` in this process is not None.
- `TestPipArgv::test_the_exact_vector_and_safe_path_flag`. With version `(3,13,9)`: `[exe,"-P","-m","pip","install","--disable-pip-version-check","--no-input","--only-binary=:all:","bokeh>=3.8"]`. With `(3,10,0)`: no `-P`. With `user=True`: `--user` before the specs.
- `TestPipArgv::test_the_whitelist`. Rejected: `"bokeh; rm -rf ~"`, `"-e ."`, `"--index-url=x"`, `"bokeh>=3.8 "`, `"bokeh==3.8"`, `"../x"` (each `ValueError`). Accepted: `"bokeh>=3.8,<4"` (A15).
- `TestClassifyFailure::test_each_measured_refusal_is_classified`. Every fixture record's `(rc, stderr)` maps to its kind: `externally_managed` to `externally-managed`, `user_in_venv` and `user_disabled` to `user-unavailable`, `no_pip` to `no-pip`, `offline_no_match` to `other`.
- `TestClassifyFailure::test_codes_and_debian`: rc 0 gives `ok`, -1 `missing-interpreter`, -2 `timeout`; `"The virtual environment was not created successfully because ensurepip is not available."` gives `no-ensurepip`.
- `TestShellLine::test_the_posix_line_survives_sh` (H7c/d).
  - Write the stub `tmp/"My Python"/bin/python3` with the shebang `#!` + `sys.executable`. It writes `json.dumps(sys.argv[1:])` to `tmp/argv.json`, mode 0755.
  - `line = shell_line([stub, "-m", "pip", "install", "bokeh>=3.8"], False)`, then `subprocess.run(["/bin/sh", "-c", line], cwd=tmp)`: argv.json holds `["-m","pip","install","bokeh>=3.8"]` and `tmp/"=3.8"` does not exist.
  - Control, with a no-space copy of the stub: the HEAD form `<stub> -m pip install bokeh>=3.8` in sh writes `["-m","pip","install","bokeh"]` and creates `=3.8` (M7).
- `TestShellLine::test_windows_double_quotes_metacharacters` (H7e): the exact string of TR-09.10.
- `TestShellLine::test_windows_refuses_a_quote_or_percent`.
- `TestAddUserSite::test_a_user_site_made_after_start_becomes_importable` (H7f, A13).
  - Monkeypatch `sys.path` to a copy, `site.ENABLE_USER_SITE=True`, `site.getusersitepackages` to `lambda: str(us)`.
  - Create `us/dashzzusersiteprobe.py` after setup.
  - `importlib.import_module` raises `ModuleNotFoundError` before; after `add_user_site()` returns True it imports.
  - Finally pop the module from `sys.modules` and call `importlib.invalidate_caches()`.
- `TestAddUserSite::test_nothing_changes_when_disabled_or_already_present`.
- `TestValidateVenvPath::test_refusals`, parametrized over the ten TR-09.13 messages:
  - `""`, `"a\x01b"`, `'a"b'`, ``"a`b"``, `"a$b"`;
  - a symlinked final component;
  - a regular file;
  - a non-empty non-venv dir;
  - a venv dir chmod 0o775, and a venv whose `bin` is 0o775;
  - `getuid=lambda: os.getuid()+1` on an existing venv;
  - a world-writable non-sticky parent (`os.chmod(p, 0o777)`);
  - a missing parent outside `home`;
  - `"x/.."`.
- `TestValidateVenvPath::test_resolutions`:
  - `"v"` gives `<realpath cwd>/v`, `"new"`;
  - `"-h"` gives `<cwd>/-h`;
  - `"~/v"` with `home=tmp/h` gives `tmp/h/v`;
  - an existing empty dir gives `"empty"`, and a dir with `pyvenv.cfg` gives `"venv"`;
  - a sticky world-writable parent (0o1777) is accepted;
  - a path through a symlinked parent (`link -> real`, `link/v`) returns `realpath(real)/v` (A6);
  - `"link/../v"` resolves through `realpath` (A6).
- `TestValidateVenvPath::test_the_suggested_default_is_accepted_on_a_home_without_dash` (A5). With `home=tmp/h` (exists, no `.dash`), `"~/.dash/venv"` gives `("…/h/.dash/venv", "new", ["…/h/.dash"])`.
- `TestCreateVenv::test_a_real_venv_is_created_offline_with_mode_0755`. Real `sys.executable`: `pyvenv.cfg` and `bin/python` exist, and the dir and `bin` are `0o755` (umask 022 through run_child).
- `TestCreateVenv::test_missing_ancestors_inside_home_are_created_private`: `.dash` is `0o700` and is created only by this call.
- `TestCreateVenv::test_a_path_created_after_validation_is_refused`: validate, `os.mkdir` the path, then `create_venv` gives `(False, …"appeared after it was checked"…)`.
- `TestCreateVenv::test_a_failed_venv_module_is_reported`: monkeypatch `run_child` to `(1, "", "Error: ... ensurepip is not available")`, which gives `(False, …"python3-venv"…)`.
- `TestVerifyIn::test_a_bare_venv_reports_each_missing_package` (`--without-pip` venv): `ok` False, and every package version is `""`.
- `TestVerifyIn::test_a_venv_seeing_the_packages_passes_versions_and_schemes`. Use a venv plus a `.pth` holding `sysconfig.get_paths()["purelib"]` and the repo's `dash_render.py`, with the floor from the current mins: `ok` True and `schemes` True.
- `TestVerifyIn::test_a_venv_below_the_python_floor_is_refused` (A8): `python: "99.0"` gives `ok` False, `why == "python"`, and `version == list(sys.version_info[:3])`.
- `TestVerifyIn::test_a_malformed_reply_is_a_failure`.
- `TestMessages::test_the_managed_message_names_the_python_and_never_the_override_flag`. On POSIX, `cmd == 'dash_setup, venv("~/.dash/venv")'`. With Windows and `LOCALAPPDATA=C:\L`, it is `dash_setup, venv("C:\L\dash\venv")`. The text never holds `"break-system-packages"`.
- `TestMessages::test_the_nopip_message_offers_ensurepip_only_where_it_works`.
- `TestMessages::test_default_venv_path`.
- `TestStataEntryPoints`. A fake `sfi` is installed with `monkeypatch.setitem(sys.modules, "sfi", ...)`, holding `Macro.getLocal/setLocal` and `SFIToolkit.macroExpand`, which maps `` `c(python_exec)' `` and `` `c(pwd)' ``. `subprocess.run` is monkeypatched as needed.
  - `::test_stata_detect_sets_every_local`.
  - `::test_stata_pip_resolves_a_relative_exec` (A1): exec `"vnp/bin/python"` with pwd tmp and the file present gives argv[0] `== str(tmp/"vnp/bin/python")`.
  - `::test_stata_pip_retries_with_user_only_when_allowed_and_adds_the_user_site`.
  - `::test_stata_pip_never_raises_into_stata` (spec `"x; y"`).
  - `::test_stata_shell_line_names_the_linked_interpreter_quoted`: exec `"/opt/My Python/bin/python3"` gives `'/opt/My Python/bin/python3' -m pip install 'bokeh>=3.8'` in `pip_cmd`, printed after `To upgrade:` for `how="upgrade"`.
  - `::test_stata_guide_prints_plain_text`: an exe holding `{bf:X}` is printed literally (capsys), and the fake has no `SFIToolkit.display`.
  - `::test_stata_venv_check_and_stata_venv_with_a_recorded_run`: `run_child` monkeypatched to answers in order. Locals: `venv_ok`, `venv_step == ""`, `venv_cmd == 'python set exec "<abs>/bin/python", permanently'`, `venv_linked == "0"`.
- `TestModuleShape::test_stdlib_only_python38_parseable_and_run_looked_up_at_call_time`:
  - `ast.parse(src, feature_version=(3, 8))`;
  - every imported top-level name is in `sys.stdlib_module_names`;
  - no `from subprocess import` and no `from site import`;
  - no `shell=True`;
  - `break-system-packages` appears only as the `PIP_BREAK_SYSTEM_PACKAGES` key with value `"0"`;
  - `umask` appears only under the runtime check;
  - importing the module with `subprocess.run` patched to raise records nothing.
- `TestLiveRefusal::test_a_real_externally_managed_python_is_detected_and_refused`. Supplementary. The first of `(sys.executable, "/opt/homebrew/bin/python3.13", "/usr/bin/python3")` whose detection says managed: `run_child([...,"-m","pip","install","--dry-run","--no-index","bokeh>=3.8"])` classifies as `externally-managed`. `pytest.skip("no externally managed Python on this host")` otherwise. It is never the only proof (the fixture tests are).
- `TestTheFixture::test_pip_refusals_has_its_meta_and_records`: the five records and the six `_meta` keys.

**`test/test_setup_sandbox.py`** (task 09-03; guards for the new test infrastructure). The `_always_restored` fixture also asserts `os.environ.get("PYTHONPATH")` and `site.addsitedir`/`site.getusersitepackages`/`site.ENABLE_USER_SITE` are back.
- `TestTheSimulatedStates`:
  - `::test_the_detect_probe_is_answered_from_the_spec`
  - `::test_the_venv_probe_answers_differently_from_the_linked_one`
  - `::test_a_pip_response_is_replayed_from_the_fixture`
  - `::test_an_install_that_lifts_a_block_returns_zero`
  - `::test_the_venv_effect_creates_the_environment`
  - `::test_the_verify_probe_is_answered_from_the_spec`
  - `::test_the_user_site_gate_admits_a_package_only_after_addsitedir`
  - `::test_cwd_env_and_umask_are_recorded_and_python_exec_maps_to_PYTHON_EXEC`
  - `::test_an_inherited_pythonpath_is_set_and_restored`
- `TestTheStataWrappers`:
  - `::test_an_ANY_wildcard_matches_one_argument`
  - `::test_stata_pip_kwargs_reports_the_first_pip_install`

**Certification cases** (task 09-05). Each is wrapped so that all of them run and report (TR in 09-05):

```
capture noisily {
    ...assertions...
    display "PEP-nn PASS: ..."
}
if _rc _pep_fail PEP-nn `=_rc'
```

`_pep_fail` appends the id to `$PEP_FAILED` and prints `PEP-nn FAIL rc <rc>: $PC_WHY`. After the last PEP case: `if "$PEP_FAILED" != "" { display as error "PEP FAILED: $PEP_FAILED"; exit 9 }`. Expected vectors are built in a `python:` line with `json.dumps` and set by `sfi.Macro.setGlobal("PC_SB_EXPECT", ...)`. `DETECT` below means `["PYTHON_EXEC", "-c", "<ANY>"]`, and `F` means `"--disable-pip-version-check", "--no-input", "--only-binary=:all:"`.

`test/test_program_coverage.cscript` (sandbox), inserted after PC-26's PASS line (:830) and before `global PC_SB_ADO ""` (:832):

| Case | Spec / command | Expected | Base failure |
|---|---|---|---|
| PEP-01 | `{"block":["bokeh"],"env":{"managed":true}}` | `[DETECT]`; log has `externally managed (PEP 668)`, not `break-system-packages`; `Unmet:` names `bokeh (externally managed Python)`; rc 198; `r(externally_managed)=="1"`; `r(hint_cmd)=='dash_setup, venv("~/.dash/venv")'` | 2 pip calls (`PYTHON` …, `--user`) |
| PEP-02 | `{"block":["packaging","packaging.version"],"env":{"managed":true}}` | `[DETECT]`; `version checks approximate`; rc 0 (A7) | 1 pip call |
| PEP-03 | `{"block":["bokeh"],"pip":{"rc":1,"stderr":"externally_managed"}}` | `[DETECT, [PYTHON_EXEC,"-P","-m","pip","install",F…,"bokeh>=3.8"]]`; no `--user`; log has `error: externally-managed-environment` and the PEP 668 block, not `break-system-packages`; rc 198 | 2 calls; pip's `--break-system-packages` tail printed |
| PEP-04 | `{"block":["bokeh"],"env":{"pip":false}}` | `[DETECT]`; log `This Python has no pip`; `r(hint_cmd)` == shlex oracle of `[c(python_exec),"-m","ensurepip","--upgrade"]`; rc 198 (A2) | 2 pip calls |
| PEP-05 | `{"block":["bokeh"],"env":{"in_venv":true}}` | `[DETECT, pip bokeh]` with argv[0] `PYTHON_EXEC`; no `retrying with --user`; rc 198 (N2) | `PYTHON` vectors plus `--user` |
| PEP-06 | `{"block":["bokeh"],"user_site_gate":"bokeh"}` | `[DETECT, pip bokeh, pip --user bokeh]`; `bokeh ............. OK`; rc 0 (H7f) | r(198) after the `--user` retry |
| PEP-07 | `{"block":["bokeh"],"unblock_on_install":["bokeh"],"pythonpath":"/dash/hostile/pythonpath"}` | `r(pip_cwd)` non-empty, `!= c(pwd)`, and removed; `r(pip_pp)=="0"`, `r(pip_bsp)=="0"`, `r(pip_puser)=="0"`, `r(pip_dwb)=="1"`, `r(pip_umask)=="18"` (N3, A9, A10) | no `cwd`/`env` kwarg recorded |
| PEP-08 | `{"pip":{"rc":0}}` with `PC_SB_CMD = dash_setup, venv("<tmp>pep08 dir/venv")` (the parent pre-made) | `[[PYTHON_EXEC,"-P","-m","venv",A], [A/bin/python,"-c","<ANY>"], [A/bin/python,"-P","-m","pip","install",F…,"packaging","bokeh>=3.8","numpy>=2.3","pandas>=2.3"], [A/bin/python,"-P","-c","<ANY>","<ANY>",normpath(<repo>/dash_render.py)]]`, with A = realpath(parent)/venv; rc 0; `r(venv_python)==A+"/bin/python"`; `r(hint_cmd)=='python set exec "'+A+'/bin/python", permanently'`; log `dash_setup complete for the environment named above.` | r(101) |
| PEP-09 | venv() on a non-empty non-venv dir | `[]`; rc 198; log `is not empty and is not a virtual environment` | r(101) |
| PEP-10 | venv() on a 0775 venv dir | `[]`; rc 198; `can be written by other users` | r(101) |
| PEP-11 | venv() with a `"` in the path (the command built in Mata with `char(96)+char(34)` … `char(34)+char(39)`, M9) | `[]`; rc 198; `holds a character` | r(101) |
| PEP-12 | venv() on a symlink to a dir | `[]`; rc 198; `is a symbolic link` (A6) | r(101) |
| PEP-13 | `{"pyversion":"3.12.11 (dash test sandbox)"}` with venv() | `[]`; rc 198; `venv() ............ not started` | r(101) |
| PEP-14 | a pre-made venv dir (`pyvenv.cfg`, `bin/python`, 0755) with `{"venv_env":{"version":[3,12,1]}}` | `[[A/bin/python,"-c","<ANY>"]]`; rc 198; log `3.12.1` (A8) | r(101) |
| PEP-15 | `{"fake":[["bokeh","2.4.3"]],"env":{"managed":true}}` | `[DETECT]`; no `To upgrade:`; the PEP 668 block; `Unmet:  bokeh 2.4.3 (needs 3.8)`; rc 198 (N4) | the `To upgrade:` pip line, which pip refuses |
| PEP-16 | `{"block":["bokeh"]}` with `PC_SB_ADO = pc_ado_nodash` | `[]`; log `dash_setup_lib.py .. not found`; `Unmet:` names `dash's own files (dash_setup_lib.py)`; rc 198 | 2 pip calls |

`test/test_setup_honesty.cscript` (real processes, offline), inserted after HON-30's PASS line (:831) and before `macro drop HON_SB_SPEC …` (:833), inside the live region:

| Case | What | Expected | Base failure |
|---|---|---|---|
| PEP-17 | `PIP_NO_INDEX=1` in `os.environ` (restored after); `dash_setup, venv("<tmp>pep17 venv")` | rc 198; the venv exists with `pyvenv.cfg`, mode 0755 and the user as owner; log `No matching distribution`; `r(hint_cmd)==""`; log `you may delete it`; then `shutil.rmtree` | r(101) |
| PEP-18 | a venv made from `c(python_exec)` plus `dash_base.pth` to its purelib (M2); `dash_setup, venv("<tmp>pep18 venv")` | rc 0; log `Requirement already satisfied`; `r(venv_python)` is `<realpath>/bin/python`; `r(hint_cmd)` is that `python set exec` line; `r(venv_linked)=="0"` | r(101) |
| PEP-19 | in Stata's interpreter: `_dash_setup_lib`, then `run_child` of a fake interpreter writing the PEP 668 bytes | rc 1 and the text holds `\u00d7`. When `locale.getpreferredencoding(False)` is ASCII (batch, M3), the control (plain `text=True`) raises `UnicodeDecodeError`; otherwise the case prints that the control was not exercised | `_dash_setup_lib` undefined, r(199) |

**Flipped** (09-10, 09-11, 09-14, 09-15): the rows of Evidence "Tests that pin today's behaviour".

**Mutation table** (each break kills its test):

| Break this | Test that must die |
|---|---|
| `run_child` without `encoding="utf-8", errors="replace"` | `TestRunChild::test_non_ascii_output_under_an_ascii_locale_is_decoded`, PEP-19 |
| `run_child` with `cwd=None`, or drop `-P` and use the caller's cwd | `TestRunChild::test_a_pip_package_in_the_working_directory_is_not_run`, PEP-07 |
| `child_env` keeps `PYTHONPATH`, or drops instead of setting `PIP_BREAK_SYSTEM_PACKAGES=0` | `TestChildEnv`, `TestRunChild::test_an_inherited_pythonpath_does_not_reach_the_child`, PEP-07 |
| detection in-process (`find_spec("pip")` in Stata) | `TestDetectEnvironment::test_a_venv_without_pip_is_reported_without_pip`, PEP-04 |
| `stata_pip` uses `sys.executable` | PEP-05, flipped PC-18 |
| skip the managed check before pip | PEP-01, PEP-02 |
| retry `--user` after an externally-managed refusal or in a venv | PEP-03, PEP-05 |
| no `add_user_site` after a `--user` success | PEP-06, `TestAddUserSite` |
| `shell_line` POSIX as `" ".join` | `TestShellLine::test_the_posix_line_survives_sh` |
| the below branch prints an upgrade on a managed Python | PEP-15 |
| `validate_venv_path` lstat's every ancestor | `TestValidateVenvPath::test_resolutions` (the symlinked parent) |
| venv `linked` compares the realpath of the interpreters | `TestStataEntryPoints::test_stata_venv_check_and_stata_venv_with_a_recorded_run` (`linked` must be `"0"`) |
| `umask=` passed unconditionally | `TestRunChild::test_the_call_is_shell_free_and_umask_only_where_popen_takes_it` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Helper pure functions (resolve, flags, env, run, detect, argv, classify, quote, user site, path, venv, verify, messages) | pytest `test_setup_pep668.py` | pip_refusals.json | n/a (setup) |
| Stata entry points without Stata | pytest `TestStataEntryPoints` with a fake sfi | none | n/a |
| Module shape (3.8 grammar, stdlib, call-time lookup) | pytest `TestModuleShape` | none | n/a |
| Sandbox states (detect, venv, verify, pip replay, user-site gate, kwargs) | pytest `test_setup_sandbox.py` | pip_refusals.json | n/a |
| dash_setup decisions end to end, installing nothing | cscript PEP-01..16 plus flipped PC-18..21 (test_program_coverage) | pip_refusals.json via the sandbox | n/a |
| Real venv, offline, and N1 in Stata's own interpreter | cscript PEP-17..19, plus flipped HON-14, 20-22, 26, 27, 29 (test_setup_honesty) | none (built at run time) | n/a |
| `_dash_pip_command` quoting | cscript test_setup_python_gate (flipped) plus pytest | none | n/a |
| Help claims, shown commands | pytest test_help_claims_8, test_help_examples; cscript test_help_examples (pins) | none | n/a |
| Packaging and maps | pytest test_packaging, test_function_test_map, test_program_coverage_map, test_no_orphans, test_cscript_hygiene | none | n/a |
| Saved page and served `/health` in a venv-linked session | release_gate_venv.do (dev-mode run in 09-17; full gate at S15.6) plus pytest test_release_verdict | none | **yes**: saved page and served app |
| Tracking | pytest test_tracking_documents | none | n/a |

Acceptance criteria:
- **AC-09.1** `python3 -m pytest test/test_setup_pep668.py test/test_setup_sandbox.py -q -n0 -p no:cacheprovider` passes. Its only skip is `TestLiveRefusal` on a host with no managed Python, and here there is none (M1).
- **AC-09.2** Through the driver: `test_program_coverage.cscript` prints `PEP-01 PASS` … `PEP-16 PASS`, every PC case PASS, and `ALL CHECKS PASSED`. `test_setup_honesty.cscript` prints `PEP-17..19 PASS` and `All dash_setup honesty tests PASSED`. `test_setup_python_gate.cscript` prints `ALL TESTS PASSED`. `test_help_examples.cscript`, `test_env_guards.cscript`, `test_help_claims_8.cscript`, `test_setup_injection.cscript` and `test_setup_version_gate.cscript` pass. No new SKIP appears.
- **AC-09.3** In `grep -n '"pip", "install"\|sys.executable' dash_setup.ado`, only comments remain. `grep -c "dash_setup_lib.py" dash.pkg scripts/release_gate.do scripts/release_verdict.py` gives 1 in each file. `test_packaging.py`, `test_release_verdict.py` and `test_function_test_map.py` pass.
- **AC-09.4** The dev-mode gate run logs `GATE venv-made rc=0`, `GATE venv-setup rc=0 ready=1 linked=0`, `GATE venv-link rc=0`, `GATE venv-setup2 rc=0 linked=1`, `GATE venv-saved rc=0 html=1`, `GATE venv-served rc=0 health=1` and `GATE venv-done`. `release_verdict.venv_verdict` on those logs returns `[]`.
- **AC-09.5** The full suite (`python3 -m pytest test/ -q`) is green. BUGS.md closes `dash_setup fails on PEP 668 Pythons` naming existing tests. `WP29_OPEN` has no `"P0.19"`. `grep -c '<!-- WP-29 P0.19 -->' CHANGELOG.md` gives 0. One commit on `wp29-s09` ends `(WP-29 P0.19)`, and `git log -1 --format=%B | grep -ciE 'claude|anthropic'` gives 0.

## Tasks

**Commit boundary.** There is **one commit, P0.19**. It holds 09-01 to 09-19, has a subject ending `(WP-29 P0.19)`, and is made by 09-19 on the worktree branch `wp29-s09` (`/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s09`) after one full suite run there.

The body opens with `<scratch>/09-P0.19-failure.txt`, then carries:
- `Regression: test/<file>.py::<Class>::<test> -- failed at <base sha> with <text>`, one per regression test (the cscript cases as `Regression: test/test_program_coverage.cscript PEP-nn -- failed at <sha> with <text>`);
- `Flipped: <node> -- <old expectation> was wrong because <why>` (from `<scratch>/09-flips.txt`);
- `Fixture: test/fixtures/pip_refusals.json (scripts/extract_pip_refusals.py)`;
- `BUGS.md: "dash_setup fails on PEP 668 Pythons" (closed)`.

Path notes:
- `<scratch>` is the session scratchpad's `wp29/s09/`.
- `R` is the worktree root. Every path below is relative to it unless absolute.
- Stata runs only through `scripts/stata_slot.sh` with `dash_nobrowser=1`.

<task type="auto" id="09-01">
  <name>Record the base and the blast radius</name>
  <files>none</files>
  <action><![CDATA[
    In the worktree, record `git rev-parse HEAD` as the base. Check that it equals `<scratch>/batch-1-base.txt` (index.md step 0c) and write it to `<scratch>/09-base.txt`. Confirm that S01 landed:
    - BUGS.md holds an open `- [ ] Title: dash_setup fails on PEP 668 Pythons`;
    - `grep -n '"P0.19"' test/test_tracking_documents.py` finds the `WP29_OPEN` key;
    - `grep -n '<!-- WP-29 P0.19 -->' CHANGELOG.md` finds one marker under `### Requirements`.

    Run `gitnexus analyze` (the index has no `dash`: C7), then `gitnexus_impact({target: "_dash_pip_command", direction: "upstream"})`, the same for `dash_setup`, `install` (test/setup_sandbox.py) and `verdict` (scripts/release_verdict.py). If GitNexus still cannot index the Stata programs, record the Evidence grep table instead.

    Save the blast radius to `<scratch>/09-impact.txt` and report any HIGH or CRITICAL result to the maintainer before editing (R8). Also record `python3 -m pytest --collect-only -q 2>/dev/null | tail -1` (the node count) in `<scratch>/09-nodes-before.txt`.
  ]]></action>
  <verify><![CDATA[`cat <scratch>/09-base.txt` prints a 40-hex sha equal to `<scratch>/batch-1-base.txt`; `<scratch>/09-impact.txt` exists; the three S01 greps each print one line.]]></verify>
  <done>The base sha, the node count and the blast radius were recorded, and S01's entry, key and marker were confirmed present.</done>
</task>

<task type="auto" id="09-02">
  <name>Extract the pip refusal fixture</name>
  <files>scripts/extract_pip_refusals.py, test/fixtures/pip_refusals.json</files>
  <action><![CDATA[
    Create `scripts/extract_pip_refusals.py` as TR-09.28 specifies:
    - stdlib only (`argparse`, `json`, `os`, `subprocess`, `tempfile`, `shutil`, `datetime`, `sysconfig`), and `subprocess.run` with argv lists only;
    - each child's env is `os.environ` minus `PYTHONPATH`, plus `PIP_NO_INDEX=1` and `PIP_DISABLE_PIP_VERSION_CHECK=1`;
    - every command works under one `tempfile.mkdtemp()`, which is removed at the end;
    - the temp path is replaced with `<tmp>` in argv and stderr.

    It checks that `--managed` has `EXTERNALLY-MANAGED` in its `sysconfig.get_path("stdlib")` (asked of that interpreter with `-c`) and that `--plain` does not, exiting 2 otherwise. Run it:

    ```
    python3 scripts/extract_pip_refusals.py --managed /opt/homebrew/bin/python3.13 --plain /opt/anaconda3/bin/python3 --out test/fixtures/pip_refusals.json
    ```

    Then `git add -f test/fixtures/pip_refusals.json` (`.git/info/exclude` drops `*.json`). Never patch the fixture by hand: re-run the script (R5).
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/pip_refusals.json'));print(sorted(d));print(sorted(d['_meta']));print(d['externally_managed']['rc'], d['externally_managed']['stderr'].splitlines()[0]);print('\u00d7' in d['externally_managed']['stderr'])"` prints `['_meta', 'externally_managed', 'no_pip', 'offline_no_match', 'user_disabled', 'user_in_venv']`, the six `_meta` keys (`born_date dash_commit extracted pip_version python_version stata_version`), `1 error: externally-managed-environment`, and `True`; `git ls-files test/fixtures/pip_refusals.json` prints the path.]]></verify>
  <done>The measured pip refusals were captured by a stdlib-only extractor into a stamped, force-added fixture.</done>
</task>

<task type="auto" id="09-03">
  <name>Teach the setup sandbox the new states</name>
  <files>test/setup_sandbox.py, test/test_setup_sandbox.py</files>
  <action><![CDATA[
    Extend `test/setup_sandbox.py` (stdlib only, no change to anything it already does except the rc of an unblocking install).

    1. `install(..., env=None, venv_env=None, pip=None, verify=None, user_site_gate=None, pythonpath=None, python_exec=None)`:
       - `env`: overrides for the linked Python's DETECT answer: `managed`, `in_venv`, `pip`, `ensurepip`, `user_site_enabled`, `version`. The defaults are an ordinary Python: prefix == base_prefix == `"/dash-sandbox/prefix"`, marker False, pyvenv_cfg False, pip, ensurepip and venv True, user_site_enabled True, `user_site=<workdir>/usersite`, version `list(sys.version_info[:3])`. `managed` sets `marker` True. `in_venv` sets base_prefix `"/dash-sandbox/base"`. This never touches a real stdlib (A13).
       - `venv_env`: the same keys for any other interpreter's DETECT (default: in_venv True, pip True).
       - `pip`: `{"rc": int}` with an optional `"stderr": "<record name in fixtures/pip_refusals.json>"` (stdout empty, stderr the record's text), for every `-m pip install`. PEP-08 uses `{"rc": 0}` so that the install into the venv succeeds.
       - `verify`: overrides for the VERIFY answer (default `{"tag":"DASH_VERIFY_V1","ok":true,"version":<real>,"packages":{...},"schemes":true,"why":""}`).
       - `user_site_gate`: a package name kept blocked until `site.addsitedir(<workdir>/usersite)` is called.
       - `pythonpath`: a value put in `os.environ["PYTHONPATH"]` for the run and restored.
       - `python_exec`: the linked interpreter's text. `stata_install` takes it from `sfi.SFIToolkit.macroExpand("\x60c(python_exec)'")` when `sfi` has `SFIToolkit`, else from the spec's `"python_exec"`.

    2. The recorder `run(args, *a, **k)` records `{"via","argv","cwd": k.get("cwd"), "env": dict(k["env"]) if "env" in k else None, "umask": k.get("umask")}`. Then:
       - argv holding `-c` followed by code containing `DASH_DETECT_V1` returns rc 0 with stdout the JSON answer (`env` when `argv[0]` maps to `PYTHON_EXEC`, else `venv_env`);
       - `DASH_VERIFY_V1` returns the verify JSON;
       - `[..., "-m", "venv", path]` creates `path/pyvenv.cfg` and `path/bin/python` (an empty file, mode 0755) and returns rc 0 (the venv effect);
       - a pip install returns the `pip` response (stderr from the fixture), else rc 0 when the call lifted a block (`record` returns whether it unblocked), else today's rc 97 stub;
       - a `--user` install of the `user_site_gate` package creates `<workdir>/usersite` and returns rc 0.

    3. Patch, recording and restoring: `site.getusersitepackages` (returns `<workdir>/usersite`), `site.ENABLE_USER_SITE` (True), and `site.addsitedir` (a wrapper that unblocks the gate package when given the usersite path, then calls the real one).

    4. `calls()` maps an argv element equal to `python_exec` or to `os.path.abspath(python_exec)` to `"PYTHON_EXEC"`, keeping today's `"PYTHON"` stub mapping.

    5. `stata_verdict` treats an expected element `"<ANY>"` as matching any one element.

    6. New `stata_pip_kwargs()` sets the locals `pc_sb_cwd`, `pc_sb_cwdgone`, `pc_sb_pp`, `pc_sb_bsp`, `pc_sb_puser`, `pc_sb_dwb` and `pc_sb_umask` from the first recorded call holding `-m`, `pip`, `install`. With none, they are empty.

    7. The module reads the fixture as `os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "pip_refusals.json")`.

    Update the module docstring. Add the `test_setup_sandbox.py` tests named in "TDD test stubs", and extend `_always_restored` with the restored `PYTHONPATH` and `site` attributes.

    Then run test_program_coverage.cscript and test_setup_honesty.cscript **at the base** through the driver: every existing PC and HON case must still PASS (risk factor 4). The existing `_pc_setup` passes no new spec keys, so nothing it asserts changes.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_setup_sandbox.py -q -n0 -p no:cacheprovider` passes; `grep -c " PASS" <scratch>/s09/run_test_program_coverage.log` is unchanged from a run at the base before this task (record both) and the log ends `ALL CHECKS PASSED`; `<scratch>/s09/run_test_setup_honesty.log` ends `All dash_setup honesty tests PASSED`.]]></verify>
  <done>The sandbox answered the detect, venv and verify probes, replayed pip's refusals, gated the user site, recorded each call's cwd, env and umask, and left every existing case green at the base.</done>
</task>

<task type="auto" id="09-04">
  <name>Write the failing helper unit tests</name>
  <files>test/test_setup_pep668.py</files>
  <action><![CDATA[
    Create `test/test_setup_pep668.py` with every class and test named under "TDD test stubs" for this file, using exactly those names:
    - TestResolveExe
    - TestVersionAndFlags
    - TestChildEnv
    - TestRunChild
    - TestDetectEnvironment
    - TestPipArgv
    - TestClassifyFailure
    - TestShellLine
    - TestAddUserSite
    - TestValidateVenvPath
    - TestCreateVenv
    - TestVerifyIn
    - TestMessages
    - TestStataEntryPoints
    - TestModuleShape
    - TestLiveRefusal
    - TestTheFixture

    The module-scoped fixture `lib` loads `<repo>/dash_setup_lib.py` by `importlib.util.spec_from_file_location("dash_setup_lib_under_test", path)` and calls `pytest.fail("dash_setup_lib.py is missing (WP-29 P0.19)")` if the file is absent. Tests needing a real venv use `tmp_path` and `sys.executable`, offline (`monkeypatch.setenv("PIP_NO_INDEX", "1")`), and at most four create one (`TestCreateVenv` x1, `TestVerifyIn` x2, `TestDetectEnvironment` x1).

    The module docstring states P0.19, GAPS2 H7a-g and N1-N4, and that the fixture is `test/fixtures/pip_refusals.json`. Follow test_test_integrity.py's six rules.

    Do not create `dash_setup_lib.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_setup_pep668.py -q -n0 -p no:cacheprovider 2>&1 | tail -3` reports every test failed with "dash_setup_lib.py is missing (WP-29 P0.19)" (the TestTheFixture test passes: a guard) and no collection error.]]></verify>
  <done>Every helper unit test existed and failed at the base for the missing module, and none errored at collection.</done>
</task>

<task type="auto" id="09-05">
  <name>Write the failing dash_setup cases and record</name>
  <files>test/test_program_coverage.cscript, test/test_setup_honesty.cscript</files>
  <action><![CDATA[
    In `test/test_program_coverage.cscript`:
    - Extend `_pc_setup` (:524):
      - when `$PC_SB_CMD` is non-empty, run `capture noisily $PC_SB_CMD` instead of `capture noisily dash_setup`;
      - right after it, copy `r(hint_cmd)`, `r(venv_python)`, `r(venv_linked)` and `r(externally_managed)` into locals;
      - before `stata_verdict`, call `python: import setup_sandbox; setup_sandbox.stata_pip_kwargs()`;
      - return all of these as `r(hint_cmd)`, `r(venv_python)`, `r(venv_linked)`, `r(externally_managed)`, `r(pip_cwd)`, `r(pip_cwdgone)`, `r(pip_pp)`, `r(pip_bsp)`, `r(pip_puser)`, `r(pip_dwb)`, `r(pip_umask)`.
    - Define `_pep_fail` after `_pc_fail` (:142).
    - Insert PEP-01..PEP-16 exactly as the table in "TDD test stubs" specifies, after PC-26's PASS line and before `global PC_SB_ADO ""`. Each sets `global PC_SB_SPEC`, `PC_SB_CMD` and `PC_SB_EXPECT` (built with `json.dumps` in a `python:` line from `sfi.Macro.getLocal` values; oracles with `shlex.join` and `SFIToolkit.macroExpand("\x60c(python_exec)'")`), and is wrapped `capture noisily { ... }` / `if _rc _pep_fail PEP-nn `=_rc'`. Each case cleans its directories with a captured `python:` `shutil.rmtree`.
    - End the run with the `$PEP_FAILED` exit.
    - Add `PC_SB_CMD PEP_FAILED` to the closing `macro drop` (:989), and add the PEP range to the header comment.

    In `test/test_setup_honesty.cscript`, insert PEP-17..19 after HON-30's PASS line, in the same wrapper (`_pep_fail` defined there too). PEP-17/18 set `os.environ["PIP_NO_INDEX"]="1"` and restore its previous value in a captured `python:` line that always runs.

    Add no captured `python: import` probe and no `SKIP ... Python` text (R1).

    Run both scripts through the driver against the unmodified production tree, and run `python3 -m pytest test/test_setup_pep668.py -q -n0 -p no:cacheprovider`. Write into `<scratch>/09-P0.19-failure.txt`:
    - every `PEP-nn FAIL` line, with what was recorded;
    - the pytest summary.

    Also list the guard tests (passing at the base) separately at the end of that file. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "^PEP-[0-9][0-9] FAIL" <scratch>/s09/run_test_program_coverage.log` prints 16 and the log ends with `PEP FAILED:`; `grep -c "^PEP-[0-9][0-9] FAIL" <scratch>/s09/run_test_setup_honesty.log` prints 3; every PC-xx and HON-xx case before the PEP block still prints PASS; `<scratch>/09-P0.19-failure.txt` exists.]]></verify>
  <done>Nineteen dash_setup cases and the helper unit tests failed at the base for their recorded reasons, and the failure text was saved with nothing committed.</done>
</task>

<task type="auto" id="09-06">
  <name>Create the helper's pure functions</name>
  <files>dash_setup_lib.py</files>
  <action><![CDATA[
    Create `dash_setup_lib.py` in the package root with the docstring, constants and functions of TR-09.1 to TR-09.17, with exactly those names and signatures:
    - `DETECT_CODE`, `VERIFY_CODE`
    - `resolve_exe`, `version_tuple`, `safe_flags`, `child_env`, `run_child`
    - `interpret_detect`, `detect_environment`
    - `pip_install_argv`, `classify_failure`, `shell_line`, `add_user_site`
    - `default_venv_path`, `VenvPathError`, `validate_venv_path`, `venv_python`, `create_venv`, `verify_in`
    - `managed_message`, `nopip_message`

    Rules:
    - `import subprocess` and `import site` are module imports used as `subprocess.run` and `site.addsitedir`.
    - No f-string inside `DETECT_CODE`.
    - No annotation needs a Python newer than 3.8.
    - Every message is the TR's text.
    - `"break-system-packages"` appears only in `_ENV_SET`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_setup_pep668.py -q -n0 -p no:cacheprovider -k "not TestStataEntryPoints"` passes (TestLiveRefusal runs here, M1); `python3 -c "import ast;ast.parse(open('dash_setup_lib.py').read(), feature_version=(3,8))"` prints nothing.]]></verify>
  <done>The helper's pure functions ran children safely, detected the environment in a child, quoted commands for both shells, validated and built venvs, and verified them, each held by its unit test.</done>
</task>

<task type="auto" id="09-07">
  <name>Add the helper's Stata entry points</name>
  <files>dash_setup_lib.py</files>
  <action><![CDATA[
    Add `_PENDING`, `_linked()` and the entry points of TR-09.18 to `dash_setup_lib.py`:
    - `stata_detect`
    - `stata_pip`
    - `stata_shell_line`
    - `stata_guide`
    - `stata_venv_check`
    - `stata_venv`

    Each imports `sfi` inside its body (never at module level, so that the module imports outside Stata). Each reads only the locals the TR lists, sets the TR's locals with string values, prints with `print()` only, and catches `Exception` around its body (printing `"  dash_setup: internal error: <type>: <msg>"` and setting its failure locals: `det_ok 0`, `pip_outcome other`, `pip_cmd ""`, `guide_cmd ""`, `venv_ok 0`, `venv_step internal`).

    `stata_venv` follows the eight steps of TR-09.18. Its `linked` test compares `os.path.realpath` of the two venv roots, never of the interpreters.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_setup_pep668.py -q -n0 -p no:cacheprovider` passes in full.]]></verify>
  <done>Stata could drive every helper step through getLocal and setLocal, and no failure inside the helper could reach Stata as r(7102).</done>
</task>

<task type="auto" id="09-08">
  <name>Route installs through the helper</name>
  <files>dash_setup.ado</files>
  <action><![CDATA[
    In `dash_setup.ado`:
    - Make `dash_setup` rclass with `syntax [, VENV(string)]`, and move the three `min_*` locals up (TR-09.19).
    - Add the detection locals, the pre-step-2 `_need` loop and the "ensure detection" block, and rewrite step 2, step 3's missing-package branch and the below verdict exactly as TR-09.20 gives them (the venv() block comes in 09-09).
    - Remove both inline `subprocess.run([sys.executable, ...])` blocks (:107-114, :169-176, :184-191) and the bare fallback line :197.
    - Append `_dash_setup_lib`, `_dash_setup_detect`, `_dash_setup_pip` and `_dash_setup_guide` (TR-09.19) after `_dash_setup_check_files`, each with a header comment in the file's style naming WP-29 P0.19.
    - Rewrite `_dash_pip_command` with the `how` argument.
    - Update the `*!` header (`Usage: dash_setup [, venv(path)]`; dash_setup_lib.py among dash's own files).

    Keep every `display` that does not carry environment text as it is.
  ]]></action>
  <verify><![CDATA[Through the driver, `test_program_coverage.cscript` prints `PEP-01 PASS` … `PEP-07 PASS`, `PEP-15 PASS`, `PEP-16 PASS` (PEP-08..14 and the flipped PC-18..21 may still fail until 09-09 and 09-10); `grep -n '"pip", "install"' dash_setup.ado` prints nothing; `grep -n "sys.executable" dash_setup.ado | grep -v "//"` prints nothing.]]></verify>
  <done>dash_setup inspected the linked Python in a child before any pip run, refused to run pip on managed or pip-less Pythons, ran pip only through the helper with the resolved interpreter, and printed every command quoted.</done>
</task>

<task type="auto" id="09-09">
  <name>Add the venv option to dash_setup</name>
  <files>dash_setup.ado</files>
  <action><![CDATA[
    Insert TR-09.20's venv() block after step 1 and before the `_need` loop. Append `_dash_setup_venv` (TR-09.19) after `_dash_setup_guide`.

    Add the `venvready` option to `_dash_setup_summary` (syntax `[ITEMS(string) VENVready]`). With `failures == 0` and `venvready` it prints the two venv lines of TR-09.19 and neither "All dependencies are satisfied" nor the "You can now use dash" lines. Leave its failure and warning branches byte-for-byte as they are (HON-01..05, HC8-19).
  ]]></action>
  <verify><![CDATA[Through the driver, `test_program_coverage.cscript` prints `PEP-08 PASS` … `PEP-14 PASS`; `test_setup_honesty.cscript` prints `PEP-17 PASS`, `PEP-18 PASS`, `PEP-19 PASS` and `HON-18 PASS`.]]></verify>
  <done>dash_setup, venv(path) refused unsafe paths and below-floor Pythons before starting anything, created or reused the environment, installed and verified inside it, and printed the link line with r(venv_python).</done>
</task>

<task type="auto" id="09-10">
  <name>Flip the pinned dash_setup cases</name>
  <files>test/test_program_coverage.cscript, test/test_setup_honesty.cscript, test/test_setup_python_gate.cscript</files>
  <action><![CDATA[
    Flip, keeping every case id and adding a comment `// WP-29 P0.19: <why>`.

    In test_program_coverage.cscript:
    - PC-18, PC-19 and PC-20 get the C5 expectation vectors, built as JSON in a `python:` line with `"<ANY>"` for the probe's code.
    - PC-19's log needle `python -m pip install bokeh>=3.8` becomes the shlex oracle `shlex.join([macroExpand c(python_exec), "-m", "pip", "install", "bokeh>=3.8"])`, also asserted equal to `r(hint_cmd)`.
    - PC-21 expects `[DETECT]` and the oracle line.

    In test_setup_honesty.cscript:
    - HON-14 asserts `_rc == 198` and displays `HON-14 PASS: an unknown option on dash_setup is r(198)`.
    - `_hon_reload` (:413-420) gains `_dash_setup_lib _dash_setup_detect _dash_setup_pip _dash_setup_guide _dash_setup_venv`.
    - `_hon_run_setup` (:443) joins a call as `"-c <code>"` when `c[1:2] == ["-c"]`.
    - HON-20's calls become `"-c <code>"` and `h20wantcmd` becomes the oracle.
    - HON-21 and HON-22 get the C5 strings.
    - HON-26 and HON-27 get the `PYTHON_EXEC` vectors with `DETECT` first.
    - HON-29 expects `[DETECT]` and the oracle.

    In test_setup_python_gate.cscript:166-178, compute `_want_cmd` with the oracle inside `if "`c(python_exec)'" != "" { ... }`, with no SKIP text.

    Write one `Flipped:` line per case to `<scratch>/09-flips.txt`.
  ]]></action>
  <verify><![CDATA[Through the driver: `test_program_coverage.cscript` ends `ALL CHECKS PASSED` with `PC-18 PASS` … `PC-21 PASS` and `PEP-01 PASS` … `PEP-16 PASS`; `test_setup_honesty.cscript` ends `All dash_setup honesty tests PASSED` with no `SKIP`; `test_setup_python_gate.cscript` ends `ALL TESTS PASSED`; `grep -c "^Flipped:" <scratch>/09-flips.txt` is at least 13.]]></verify>
  <done>Every pinned setup case expected the probe, the resolved interpreter, the safe flags and the quoted line, kept its id, and had its flip recorded.</done>
</task>

<task type="auto" id="09-11">
  <name>Flip the pinned text guards</name>
  <files>test/test_version_floor.py, test/test_help_claims_8.py, test/test_cscript_hygiene.py</files>
  <action><![CDATA[
    **test_version_floor.py.** Rewrite `TestTheFloorIsTheTestedBaseline::test_the_upgrade_line_names_the_linked_interpreter` (:117-134) in place, under the same name (cited by the closed K2 entry):
    - `_dash_pip_command`'s body calls `stata_shell_line`;
    - the below branch calls `_dash_pip_command` with `upgrade` and holds no `python -m pip install --upgrade`;
    - `dash_setup_lib.stata_shell_line()`, run with a fake `sfi` whose `macroExpand` gives `/opt/My Python/bin/python3`, sets `pip_cmd` to `'/opt/My Python/bin/python3' -m pip install 'bokeh>=3.8'`.

    **test_help_claims_8.py.** Rewrite `TestDashSetupHelpMatchesTheAdo::test_it_installs_only_what_is_missing` (:1659-1675) in place:
    - no line of dash_setup.ado holds `"pip", "install"` or `ssc install`;
    - exactly two lines call `_dash_setup_pip`, and for each the nearest preceding `capture ` line is `capture python: import ...` followed by `if _rc != 0 {`;
    - `pip_install_argv` is defined in dash_setup_lib.py, and `"-m", "pip", "install"` occurs in no other function there.

    **test_cscript_hygiene.py.** Remove the `"dash_setup.ado"` key from `_ALLOWED_INLINE_PY_MACROS` (:66-70), with a comment that the spec now reaches Python by `getLocal` (WP-29 P0.19). Update the count comment at :519 by measuring it with `_python_command_sources`.

    Add the three `Flipped:` lines to `<scratch>/09-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_version_floor.py test/test_help_claims_8.py test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider` passes (ENV-15/16, which read dash_setup.ado's text, run in test_env_guards.cscript at 09-18).]]></verify>
  <done>The text guards held the new shape -- one pip vector in the helper, no inline macro, the linked interpreter quoted -- under their old names.</done>
</task>

<task type="auto" id="09-12">
  <name>Ship the helper in the package</name>
  <files>dash.pkg, test/test_packaging.py, scripts/release_gate.do</files>
  <action><![CDATA[
    - **dash.pkg:** add `f dash_setup_lib.py` after `f dash_render.py`, and rewrite description lines 19-20 as TR-09.24 gives them.
    - **test/test_packaging.py:** add `"dash_setup_lib.py"` to `SHIPPED_SOURCES` (:51) and `_PACKAGE_FILES` (:310-311), updating their comments.
    - **scripts/release_gate.do:62:** the `foreach f in` list gains `dash_setup_lib.py` after `dash_render.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_packaging.py test/test_help_claims_8.py -q -n0 -p no:cacheprovider -k "pkg or package or Package or manifest or root"` passes; `grep -c "dash_setup_lib.py" dash.pkg scripts/release_gate.do` prints 1 for each.]]></verify>
  <done>The helper was in the manifest, required by the packaging tests and checked by the release gate as an installed file.</done>
</task>

<task type="auto" id="09-13">
  <name>Map every new unit to its test</name>
  <files>test/function_test_map.py, test/test_function_test_map.py, test/program_coverage_map.py</files>
  <action><![CDATA[
    - **function_test_map.py:** add `SETUP_FUNCTIONS` (TR-09.26), with one entry per function and nested function in dash_setup_lib.py, each naming its `test/test_setup_pep668.py::<Class>::<test>`.
    - **test_function_test_map.py:** add `test_every_dash_setup_lib_function_names_its_test`, reusing `_NODE` and `_defs_of`.
    - **program_coverage_map.py `"dash_setup.ado"`:** add the five programs and extend `dash_setup` and `_dash_pip_command`, in source order (the map's own rule), as TR-09.26 lists.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py test/test_no_orphans.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Every helper function and every new Stata program named a test that exists and fails without it.</done>
</task>

<task type="auto" id="09-14">
  <name>Document PEP 668 and venv in help</name>
  <files>dash_setup.sthlp, dash.sthlp, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Apply TR-09.22 to `dash_setup.sthlp`: the two viewerjumpto lines, the Syntax block, step 3, the two new Description paragraphs, Options, the manual-install paragraph, the Dependencies insertion at :99-101, the Externally managed Pythons section, and the No pip / mirror / upgrade Troubleshooting blocks. The SMCL is given verbatim; keep the `{* *! version 0.1.0  30sep2026}` line.

    Apply TR-09.23 to `dash.sthlp`.

    In `test/test_help_claims_8.py`:
    - change the pinned sentence in `test_a_package_below_its_minimum_is_unmet_not_a_warning` (:1652-1653) to the A16 sentence;
    - add `TestDashSetupHelpMatchesTheAdo::test_the_help_explains_externally_managed_pythons`. It asserts `PEP 668`, `{opt venv(path)}`, `python set exec`, `permanently`, `restart Stata`, `ensurepip`, `{cmd:--break-system-packages}` (named as never used), `r(7101)` and `An option other than {opt venv()} is r(198)`; that `sys.executable` and `either is r(101)` are absent from dash_setup.sthlp; and that dash.sthlp holds `{help dash_setup##pep668:Externally managed Pythons}`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_8.py test/test_version_floor.py test/test_help_claims_*.py -q -n0 -p no:cacheprovider -k "setup or Setup or floor or Floor or Dependencies"` passes; `python3 -c "import sys;sys.path.insert(0,'test');import help_examples as hx;s=[x for x in hx.shown_all('.') if x.file=='dash_setup.sthlp'];print(len(s),[x.form for x in s].count('inline'))"` prints `7 0`.]]></verify>
  <done>Both help files explained PEP 668, venv(path), the restart and the safe pip invocation, with the shown commands quoted for every shell.</done>
</task>

<task type="auto" id="09-15">
  <name>Re-pin the shown help commands</name>
  <files>test/test_help_examples.py, test/test_help_examples.cscript</files>
  <action><![CDATA[
    **test/test_help_examples.py.** In `TestTheShownCommands`:
    - `test_how_many` keeps 7 lines and 0 inline for dash_setup.sthlp and changes the distinct count to 13, with the comment updated.
    - `test_the_two_line_pip_commands_are_joined` keeps its name. It asserts `[len(s.lines) for s in pip] == [1, 1, 1, 1]` and `pip[0].text == '"/path/to/python3" -m pip install "bokeh>=3.8" "numpy>=2.3" "pandas>=2.3"'`, with a comment that the recipes became one-line shell commands (WP-29 P0.19).

    **test/test_help_examples.cscript:549-553.** Replace the four `_hx_pin shown python` lines with `_hx_pin shown placeholder` pins for exactly these texts:
    - `"/path/to/python3" -m pip install "bokeh>=3.8" "numpy>=2.3" "pandas>=2.3"`
    - `"/path/to/python3" -m pip install --index-url https://your.mirror/simple "bokeh>=3.8"`
    - `"/path/to/python3" -m pip install --upgrade "bokeh>=3.8"`
    - `"/path/to/python3" -m ensurepip --upgrade`
    - `dash_setup, venv("~/.dash/venv")`
    - `python set exec "/path/to/venv/bin/python", permanently`

    Keep the existing `python set exec "/path/to/python3", permanently` pin. Change the reason comment: these are paths to fill in, and they install packages, create an environment or change a setting permanently.

    Add both flips to `<scratch>/09-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_examples.py -q -n0 -p no:cacheprovider` passes; through the driver, `test_help_examples.cscript` ends with its pass line and no `shown and not pinned`.]]></verify>
  <done>Every command the help shows was pinned with its reason, and the counts matched the new help.</done>
</task>

<task type="auto" id="09-16">
  <name>Add the venv-linked release gate step</name>
  <files>scripts/release_gate_venv.do, scripts/run_release_gate.sh, scripts/release_verdict.py</files>
  <action><![CDATA[
    Create `scripts/release_gate_venv.do` (TR-09.25). In phase `venvuse`, `cd` and `python set exec` are the first commands after `args` and the `set` lines; nothing before them runs Python. It has no `/*`, no `permanently` and no `set python_exec`. The `/health` poll copies the HC4-20 pattern (test_help_claims_4.cscript:503-562).

    Add the loop and the 6-argument verdict to `scripts/run_release_gate.sh` after line 39, keeping `ls -t "$dir"/*.log` for session 1's log.

    In `scripts/release_verdict.py`:
    - add `"dash_setup_lib.py"` to `INSTALLED`;
    - add `venv_verdict(make_text, use_text)`;
    - let `main` take 4 or 6 arguments (usage in the docstring), returning 1 when either verdict has a problem.
  ]]></action>
  <verify><![CDATA[`python3 -c "import ast;ast.parse(open('scripts/release_verdict.py').read())"` prints nothing; `sh -n scripts/run_release_gate.sh` prints nothing; `grep -c "permanently" scripts/release_gate_venv.do` prints 0.]]></verify>
  <done>The release gate gained two venv-linked sessions, the second linked by a relative path, and a verdict that requires the link, the saved page and the served health check.</done>
</task>

<task type="auto" id="09-17">
  <name>Test the gate step in dev mode</name>
  <files>test/test_release_verdict.py, test/test_installed_layout.py</files>
  <action><![CDATA[
    **test/test_release_verdict.py:**
    - `_gate_log` picks up `dash_setup_lib.py` through `rv.INSTALLED`, so check that it still builds.
    - Add `TestTheVenvSessions`:
      - `test_clean_venv_logs_pass`;
      - `test_each_bad_venv_line_fails`, parametrized over each of the seven required lines with one key changed;
      - `test_main_takes_three_or_five_logs`;
      - `test_the_venv_gate_never_links_permanently_and_reads_whole`: no `permanently` and no `/*` in release_gate_venv.do, `set linesize 255`, and `global dash_nobrowser 1`;
      - `test_the_runner_runs_both_phases_offline`: `PIP_NO_INDEX=1`, `venvmake`, `venvuse`, and the console binary.

    **test/test_installed_layout.py:** add `PLUS/py/dash_setup_lib.py` to the docstring layout (TR-09.27).

    Then run the do-file in dev mode against the worktree:

    ```
    W=<scratch>/s09/gate
    mkdir -p "$W"
    printf 'do "%s/scripts/release_gate_venv.do" "%s" "%s/" dev venvmake\n' "$R" "$W" "$R" > "$W/make.do"
    printf 'do "%s/scripts/release_gate_venv.do" "%s" "%s/" dev venvuse\n' "$R" "$W" "$R" > "$W/use.do"
    dash_nobrowser=1 PIP_NO_INDEX=1 scripts/stata_slot.sh "$W" "$W/make.do"
    dash_nobrowser=1 PIP_NO_INDEX=1 scripts/stata_slot.sh "$W" "$W/use.do"
    ```

    The second run is a fresh session that takes about 65 s. Then:

    ```
    python3 -c "import sys;sys.path.insert(0,'scripts');import release_verdict as rv;print(rv.venv_verdict(open('$W/make.log').read(), open('$W/use.log').read()))"
    ```
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_release_verdict.py test/test_installed_layout.py -q -n0 -p no:cacheprovider` passes; `grep -E "^GATE venv-" <scratch>/s09/gate/make.log <scratch>/s09/gate/use.log` shows the seven lines of AC-09.4; the venv_verdict command prints `[]`.]]></verify>
  <done>A fresh Stata session linked by a relative path to a venv that dash_setup had verified built a saved page and served /health, and the verdict code held it.</done>
</task>

<task type="auto" id="09-18">
  <name>Run the touched certification scripts</name>
  <files>none</files>
  <action><![CDATA[
    Through the two-line driver, one at a time (three slots; never relaunch to check), run:
    - `test_program_coverage.cscript`
    - `test_setup_honesty.cscript`
    - `test_setup_python_gate.cscript`
    - `test_setup_injection.cscript`
    - `test_setup_version_gate.cscript`
    - `test_env_guards.cscript`
    - `test_help_claims_8.cscript`
    - `test_help_examples.cscript`

    Each run is `dash_nobrowser=1 scripts/stata_slot.sh <scratch>/s09 <scratch>/s09/run_<script>.do`. Read each log's end. A SKIP, an `r(` error line or a FAIL is a failure of this section: fix the code (or a flip this section owns) and rerun that script.
  ]]></action>
  <verify><![CDATA[For each log: `tail -3 <scratch>/s09/run_<script>.log` shows its script's pass line; `grep -c "SKIP" <scratch>/s09/run_test_setup_honesty.log <scratch>/s09/run_test_program_coverage.log` prints 0 for both; `grep -c "PEP-[0-9][0-9] PASS" <scratch>/s09/run_test_program_coverage.log` prints 16 and `... run_test_setup_honesty.log` prints 3.]]></verify>
  <done>Every certification script the section touched or reads passed, with all nineteen PEP cases and no skip.</done>
</task>

<task type="auto" id="09-19">
  <name>Close P0.19 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    **BUGS.md.** Close S01's entry `dash_setup fails on PEP 668 Pythons` **in place** (`- [ ]` → `- [x]`). Update its File Names and Line Numbers to dash_setup.ado (dash_setup, `_dash_pip_command`, `_dash_setup_summary`, the five new programs), dash_setup_lib.py, dash_setup.sthlp and dash.sthlp, and add N1-N4 to the Description after S01's text. Write the Resolution:

    `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.19). dash_setup inspects the linked Python in a child process (dash_setup_lib.detect_environment) and on an externally managed or pip-less Python runs no pip, printing the PEP 668 or ensurepip guidance (H7a, H7g); dash_setup, venv(path) creates or reuses, installs into and verifies a private environment and prints the python set exec line (H7b); every printed command is the resolved c(python_exec) quoted by dash_setup_lib.shell_line for POSIX shells and cmd.exe, and a managed Python gets no upgrade line (H7c, H7d, H7e, N4); a --user install is added to sys.path in the same run (H7f); pip's output is decoded as UTF-8 (N1); pip runs c(python_exec), not sys.executable (N2), from a private directory with -P, without an inherited PYTHONPATH and with PIP_BREAK_SYSTEM_PACKAGES=0 (N3, security). No renderer change; a venv-linked session builds a saved page and serves /health (scripts/release_gate_venv.do). Pinned by test/test_setup_pep668.py::TestRunChild::test_a_pip_package_in_the_working_directory_is_not_run, test/test_setup_pep668.py::TestRunChild::test_non_ascii_output_under_an_ascii_locale_is_decoded, test/test_setup_pep668.py::TestShellLine::test_the_posix_line_survives_sh, test/test_setup_pep668.py::TestValidateVenvPath::test_refusals, test/test_program_coverage.cscript PEP-01, test/test_program_coverage.cscript PEP-08, test/test_setup_honesty.cscript PEP-18; fixture test/fixtures/pip_refusals.json. Residual, deferred (WP-29): Windows quoting, Scripts\python.exe and Debian's ensurepip-less venv are tested as pure functions only; dash's own helper and in-process imports are found in the working directory first (Stata's and Python's rule).`

    The title holds no `"`.

    **test_tracking_documents.py.** Delete the `"P0.19": ...` line from `WP29_OPEN`.

    **CHANGELOG.md.** Replace `<!-- WP-29 P0.19 -->` (end of `### Requirements`) with these five lines, each ending `(WP-29, P0.19)`:
    1. `dash_setup` works on externally managed (PEP 668) Pythons -- Homebrew's, and the system Python of Debian 12, Ubuntu 23.04, Arch Linux and later. It inspects the linked Python first and, where pip installs are refused, runs no pip command, says why, and suggests `dash_setup, venv("~/.dash/venv")`. It was refused three times and printed pip's advice to pass `--break-system-packages`.
    2. New option `dash_setup, venv(path)`. It creates or reuses a virtual environment, installs packaging, bokeh, numpy and pandas into it, verifies them and dash's schemes inside it, and prints the `python set exec "<path>/bin/python", permanently` line to type after restarting Stata.
    3. Printed pip commands name `c(python_exec)` and are quoted for the shell, `<python> -m pip install 'bokeh>=3.8'` on macOS and Linux and double quotes on Windows. The failure line was `python -m pip install bokeh>=3.8`, which a shell runs as an unpinned install writing a file named `=3.8`. A Python without pip gets the `-m ensurepip --upgrade` line, and a managed Python gets no upgrade line pip would refuse.
    4. pip runs with the interpreter Stata is linked to. It ran `sys.executable`, Homebrew's base interpreter under a venv-linked Stata. It now runs from a private temporary directory with Python's safe-path flag (a `pip/` package in Stata's working directory used to run in its place), without an inherited `PYTHONPATH`, from wheels only, never prompting, and with PEP 668's protection forced on. Its output is decoded as UTF-8: a non-ASCII byte in pip's message ended `dash_setup` with r(7102). A package that `--user` installs is found in the same run.
    5. `dash_setup, garbage(1)` is r(198), was r(101), because the command now takes an option.

    **Full run and commit.**
    1. Run `python3 -m pytest test/ -q` once in the worktree (rule 11). A pin it exposes is flipped in the owning task's files and that file rerun; use `FULL_SUITE_RERUN=1` only if the hook refuses.
    2. Check that the node count is at least `<scratch>/09-nodes-before.txt`.
    3. Run `gitnexus_detect_changes()` and `git diff --cached --name-only`: only this section's files, never `CLAUDE.md`, `.gitignore`, scratch or `*.html`.
    4. Grep the message file for `claude|anthropic`.
    5. Commit once on `wp29-s09`. The subject is `Make dash_setup work on externally managed Pythons and add venv() (WP-29 P0.19)`, and the body follows the commit boundary above.
    6. Grep the committed message again.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes; `grep -c '<!-- WP-29 P0.19 -->' CHANGELOG.md` prints 0; `grep -c '(WP-29, P0.19)' CHANGELOG.md` prints 5; `grep -c '"P0.19"' test/test_tracking_documents.py` shows only the WP29_ALL occurrence; `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0; `git log -1 --format=%s | grep -c '(WP-29 P0.19)'` prints 1.]]></verify>
  <done>P0.19 was closed in BUGS.md naming its tests, its allowance and marker were gone, and one green commit on wp29-s09 carried the section.</done>
</task>

## Section completion criteria

- On a managed Python, `dash_setup` starts no pip process. It prints the PEP 668 guidance without `--break-system-packages` and ends r(198) for an unmet required package, or rc 0 when only `packaging` is missing (PEP-01, 02, 03, 15).
- `dash_setup, venv(path)`:
  - refuses an unsafe path or a below-floor Python before any install (PEP-09..14);
  - creates or reuses, installs, verifies and prints the link line (PEP-08, PEP-18);
  - leaves a failed environment in place with a note (PEP-17).
- Every printed command is the resolved `c(python_exec)` quoted for the shell. pip runs with that interpreter from a private 0700 directory with `-P`, no inherited `PYTHONPATH`, `PIP_BREAK_SYSTEM_PACKAGES=0`, `--only-binary=:all:`, `--no-input` and a timeout. Output is decoded as UTF-8. A `--user` install is found in the same run.
- `dash_setup_lib.py` ships (dash.pkg, release gate, packaging tests), has a unit test per function (`SETUP_FUNCTIONS`), and every new program is in `program_coverage_map.py`.
- In a venv-linked session, a saved page builds and `/health` answers (dev-mode run of the gate step, AC-09.4).
- There is one commit on `wp29-s09` ending `(WP-29 P0.19)`, with every flip recorded and no test or case id deleted. The full suite and the eight certification scripts are green with no new SKIP.

## Notes

- **Open questions, decided here:**
  - **OQ1, `--only-binary=:all:`: yes.** No package's build script runs during setup (rule 1). packaging and bokeh are pure-Python wheels, and numpy and pandas publish wheels for macOS arm64/x86_64, manylinux, musllinux and Windows. On a platform without wheels, the failure is classified `other` and the printed manual line, which carries no `--only-binary`, lets the user build deliberately.
  - **OQ2:** the suggestion is `~/.dash/venv` on POSIX (missing ancestors made 0700) and `%LOCALAPPDATA%\dash\venv` on Windows. `venv()` empty means no venv, and there is no magic keyword.
  - **OQ3 (`--target` plus `python set userpath`): declined.** It defeats the distribution's protection on purpose (pip skips the PEP 668 check for `--target`, research), and `userpath` after initialisation has not been measured.
  - **OQ4, OQ5, OQ6 and OQ7** go to the closeout (below).
- **Merge rules.**
  - **R1:** PEP cases append to test_program_coverage.cscript after PC-26 and to test_setup_honesty.cscript after HON-30, which only S09 edits in batch 1. There is no runner, hygiene-pin or truth-script edit.
  - **R2:** `program_coverage_map.py`'s `"dash_setup.ado"` block is S09's alone. `function_test_map.py` gains a new dict after `TEST_ONLY` that no other section touches. No served copy list changes.
  - **R3:** dash.sthlp edits are confined to the Setup syntax line (:115) and one paragraph after the Dependencies list. CHANGELOG replaces only `<!-- WP-29 P0.19 -->`, BUGS.md closes only its own entry in place, and `test_tracking_documents.py` deletes only the `"P0.19"` line.
  - **R5:** the fixture is regenerated only by its script.
  - **R7:** flips keep names and ids (C8).
  - **R8:** GitNexus needs `gitnexus analyze` first (C7).
- **Sandbox traps.**
  - A recorded pip install that lifts a block now returns rc 0, not 97, so `stata_pip` does not retry `--user` after a "successful" install (PC-20).
  - The HON recorder (`_hon_run_setup`) answers the DETECT probe with `HONPIPOUT`, so detection fails and the run proceeds as for an ordinary Python. This is intended, and it exercises the detection-failure path.
  - The sandbox's paths under `c(tmpdir)` (`/var/folders/...`) resolve through `/private`, so expectations use `os.path.realpath` of the parent (A6).
- **Stata traps.**
  - Never use a `python:` … `end` block inside dash_setup.ado's loops (:286-288): one-line `python:` statements only.
  - Environment text is printed by Python `print()`, never by `display`, because `display` renders SMCL such as `{stata ...}` links.
  - `r()` from `dash_setup` is read right after the call. `_pc_setup` copies it before `stata_verdict`.
  - `return local` in `dash_setup` survives the summary's `exit 198` (review r3/r4).
  - PEP-11's command holds compound quotes around a path with a `"` in it. M9 measured that form typed directly, not expanded from a global. If `capture noisily $PC_SB_CMD` misparses it, run that case as `mata: st_local("rc", strofreal(_stata(st_global("PC_SB_CMD"))))` and read `r()` immediately after.
- **Python traps.**
  - `-P` is "Unknown option" before 3.11 (M6), so the DETECT probe never passes it.
  - `subprocess.run(umask=)` needs 3.9 (A10).
  - `shlex.join` needs 3.8.
  - Under `LC_ALL=C` a child is still UTF-8 unless `PYTHONUTF8=0 PYTHONCOERCECLOCALE=0` (M8).
  - In the A4 test, the child must emit ASCII-only JSON.
- **Commit-body line forms.**
  - `Regression: test/test_setup_pep668.py::TestRunChild::test_a_pip_package_in_the_working_directory_is_not_run -- failed at <sha> with dash_setup_lib.py is missing (WP-29 P0.19)`.
  - `Regression: test/test_program_coverage.cscript PEP-01 -- failed at <sha> with recorded [["PYTHON","-m","pip","install","bokeh>=3.8"],["PYTHON","-m","pip","install","--user","bokeh>=3.8"]]; expected [["PYTHON_EXEC","-c","<ANY>"]]`.
  - `Flipped: test/test_setup_honesty.cscript HON-14 -- r(101) was wrong because dash_setup now declares venv(), so an unknown option is r(198) (T7)`.
  - `Fixture: test/fixtures/pip_refusals.json (scripts/extract_pip_refusals.py)`.
  - `BUGS.md: "dash_setup fails on PEP 668 Pythons" (closed)`.
- **Notes for the closeout (A5; S15 writes these, this section does not).**
  - **GAPS2.md H7 Tracked:** `Closed in WP-29, BUGS.md "dash_setup fails on PEP 668 Pythons", commit <sha>`, if S15 judges H7 fully closed. All of H7's Plan items 1-5 are done: detection, venv(), quoted `c(python_exec)` commands, the user site, and sandbox plus dry-run tests.
  - **ROADMAP WP-29** lists H7 under `**GAPS2 closed:**`.
  - **AGENTS.md invariant:** "dash_setup starts every child through dash_setup_lib.run_child (private cwd, -P, scrubbed env, UTF-8); held by test_setup_pep668.py::TestRunChild and PEP-07".
  - **Residuals for S15.7:**
    - Windows `cmd.exe`/PowerShell quoting and `Scripts\python.exe` have not been measured on Windows.
    - Debian's ensurepip-less `venv` message has not been measured.
    - The GUI's locale has not been measured; the fix is locale-independent.
    - OQ4: the served child is `sys.executable`, Homebrew's base under a Homebrew venv link. It works through Stata's exported `PYTHONPATH`; S08/u12 owns `_dash_launch_app`.
    - R4/OQ5: `findfile` and in-process imports search the working directory first, so a `dash_setup_lib.py` or `bokeh.py` there is used. This is Stata's and Python's own rule, not new surface.
    - OQ6: `Unmet:` lists warnings when a failure also occurred.
    - OQ7: no hash-pinned installs.
    - P1.30/P1.32/P3.29 will merge into dash_setup.ado.
- **Line numbers** are `7421d3d`'s. S01's commit and step 0a do not touch dash_setup.* or the setup scripts, so they hold at the batch base, but symbols are authoritative.
