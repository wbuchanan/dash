# Section 08: Private files and serve lifecycle

> Part of: WP-29 · P0: P0.12b, P0.14 (one commit), P0.13 (two commits: F2, then F4) · Sources: GAPS2-I3-b, GAPS2-I3-c (file part), AUDIT-87, GAPS2-X3-a/b/c, GAPS2-F2a, GAPS2-F2b, GAPS2-F4, GAPS2-H2a, GAPS2-H2b, GAPS2-F9c · Units: u11b-file-perms, u12-serve-lifecycle · Risk: red · Batch: 1 (merges last) · Depends on: 01 · Blocks: 13, 14 · Case prefixes: PF, LC · Tasks: 19, 3 commits

**Files.**
- **Product and records:** `dash.ado`, `dash_render.py`, `dash.sthlp`, `CHANGELOG.md`, `BUGS.md`.
- **New tests:** `test/test_private_files.py`, `test/test_serve_lifecycle.py`.
- **Changed pytest files:** `test/test_string_value_export.py`, `test/test_immediate_dashboards.py`, `test/test_serve_launcher.py`, `test/test_help_claims_2.py` (fake stdin only, R-9), `test/test_help_claims_4.py`, `test/test_server.py` (docstring only), `test/test_server_rate_limit.py`, `test/test_resource_limits.py`, `test/function_test_map.py`, `test/program_coverage_map.py`, `test/test_tracking_documents.py`.
- **Changed cscripts:** `test/test_wp29_truth.cscript`, `test/test_serve_launch.cscript`, `test/test_help_claims_4.cscript`, `test/test_adversarial.cscript`, `test/test_env_guards.cscript`.
- **Differences from the manifest's list:**
  - added `test_immediate_dashboards.py`, `test_server.py` and `test_env_guards.cscript`, because they pin the moved sites (Evidence §6);
  - added `test_help_claims_2.py`, whose `_FakeProc` needs a `stdin` once the launcher hands the app over on the pipe (R-9, round 2);
  - dropped `test_clear_registry.cscript` (R-5);
  - tracking documents are left to S15 (index A5).

## Review amendments (binding; they override any conflicting text below)

**Ratified 01oct2026:** the maintainer answered index row "S08 codes" with answer 2, which index.md's verbatim record (line 69) gives as "Allow "unsafe" temp directory locations and do not refuse writing the app files into a directory of the user's that is not private." (copied into `<scratch>/wp29-ratified.txt` by step 0f). S08 R-1, R-3, R-5 and R-6 are ratified as written, and R-7's reading of M4 (the folder the user names is the user's) is ratified. What changed in this file (new reconciliation R-8 holds the design):
- **No privacy refusal remains.** A `c(tmpdir)` other accounts can change, a `dash-<uid>` dash cannot use, and a folder or file whose permissions the disk will not keep are never refused. The old r(603) "unsafe root" refusal and the r(198) "data file could not be written privately" refusal are gone. dash proceeds, creates every file 0600 where the disk allows, and prints one `dash: note: …` per command naming each location that is not private and its remedy (R-8, TR-08.2, TR-08.10).
- **A planted `dash-<uid>` is left alone.** A link, a non-folder or another account's folder at that name is neither used nor followed. dash keeps its copies in a fallback root `dash-<uid>-<8 chars>` beside it, made by `tempfile.mkdtemp` (0700, its own), and reuses that folder on later commands (TR-08.2a).
- **The anti-hijack guards stay, labelled as such.** dash still never writes through a symbolic link, into a FIFO or device, over a file with other hard links, or over another account's file at the target name, and never runs an app that was replaced after it was written (new launch identity check, TR-08.8; since round 2 the launch from the open file, R-9, TR-08.8a). These guards stop a planted name. They are not privacy rules. Every such refusal ends r(7102) with the message as the traceback's last line (M4a), on every route. The ado-side writes now raise rather than return text.
- **r(603) remains for one case only.** It is used when the operating system will not let dash create the folder at all (c(tmpdir) missing, read-only or full). Stata's own `file open` gives the same code there (measured, Evidence §3a S1). This is not a refusal.
- **The user-named folder** of `dash build, server saving(<file>.py)` is never refused, never re-moded and never noted. Only a `.py` the disk will not keep at 0600 is noted, once, by the renderer.
- **Task 08-01** now copies the ratified rows instead of asking. The tests that asserted a refusal now assert proceed, one note and 0600 files: PF-09 (flipped), new PF-12, and `TestThePrivateRoot`, `TestTheRunDir`, `TestTheNote` and `TestTheLaunchIdentity` (since round 2, `TestTheLaunchFromTheOpenFile`).

**Ratified 01oct2026 (round 2):** the maintainer answered "App swap in a shared non-sticky temp folder" with "Launch from open file" (answer B), and the plan files will be committed on `wp29-p0` before step 0a's worktrees are cut (answer C). Answer A (the token link) is section 13's. Round 1 stays in force. What changed in this file (new reconciliation R-9 holds the design):
- **The app-substitution residual is closed, not recorded.** dash no longer starts its app by name. `_dash_launch_app` opens the `app.py` that `main()` wrote with `O_NOFOLLOW` where it exists, checks the open file (a regular file, this account's, the `(st_dev, st_ino)` and size `main()` recorded), and reads it through that descriptor. It then checks the bytes' SHA-256 against the digest `main()` recorded and starts `python -P -c <_DASH_BOOT> <app_path> …`. It hands the bytes to the child as one framed block on the child's stdin. The bootstrap compiles them under the app's own file name, so tracebacks are unchanged, and runs them as `__main__`. The child never opens a path, so a swap of the path or of its folder after the check cannot change what runs (measured, Evidence §3b). This is one route for macOS, Linux and Windows: no `/dev/fd`, which Windows lacks and which on macOS shares the file offset (§3b D1).
- **The import path is closed with it.** `python app.py` puts the app's folder first on `sys.path`, and `python -c` puts the working folder there. Measured at 3.13.9: a `linecache.py` planted beside the app ran before the app did (§3b C), and so did one planted in the working folder under `-c` without `-P` (§3b F, before the fix). `-P` (Python 3.11+; dash requires 3.13, `_dash_pymin`) puts neither on the path (§3b D, F, G).
- **What changed where.** New R-9. TR-08.8 (the build and `main()` return `_DashWrittenApp(st, sha256)`; `_dash_same_file` is withdrawn) and new TR-08.8a (`_DASH_BOOT`, `_dash_read_verified_app`, `_dash_app_frame`, `_dash_child_stdin`, `_dash_hand_over`). The child's stdin pipe moves from F2 into commit 1, and TR-08.14 and TR-08.17 are re-anchored on it. Also changed: the R-8 table and residual, risk 9, BR-08.2 and BR-08.10, TR-08.11 (help), TR-08.20 (maps), TR-08.21 (threats), Boundaries, the TDD stubs (`TestTheLaunchFromTheOpenFile` and `TestTheBootstrap` replace `TestTheLaunchIdentity`, with a deterministic swap-after-verify test), the mutation table, the test plan, AC-08.1, AC-08.4a and new AC-08.4b, tasks 08-02, 08-05, 08-06, 08-08 to 08-10, 08-13 and 08-16, the completion criteria and the Notes (CHANGELOG, BUGS.md, S13, closeout).
- **Launcher fakes.** Every fake child now needs a `stdin` that records the bytes written to it (`_RecStdin`; no `buffer` attribute, so `_dash_child_stdin` returns it itself), from commit 1: `test/test_serve_launcher.py`'s three fakes and `test/test_help_claims_2.py::_FakeProc`. This is an adjustment, not an assertion change. `test_help_claims_2.py` joins the changed files.
- **Routes.** dash starts a Python process at one site only: `_dash_launch_app`, used by `dash serve` and by the renderer's command-line `--launch`. At 7421d3d, `grep -n "subprocess.Popen(" dash_render.py` prints 31999 only, and dash.ado starts no Python process: `_dash_open_page` hands a page to the OS opener. The one-line form and `dash build` start no server. A `python app.py` or `bokeh serve app.py` that a user runs is outside dash's control. The help documents it (TR-08.11) and it is not changed.
- **Plan files are tracked (answer C).** Nothing in this file says the plan is untracked. Absolute paths to `.ultraplan/wp29/` stay valid.
- **The Windows branch is unit-tested (rule 3).** No Windows machine is available, so the Windows-only code of the launch is run on macOS by monkeypatching. `TestWindowsPortability` gains `test_the_verified_read_works_without_O_NOFOLLOW_and_getuid` and `test_a_reparse_point_is_refused_on_windows`. `TestTheBootstrap` gains `test_a_crlf_translated_frame_runs_nothing`, which runs the claim that a CRLF translation fails the SHA-256 check. TR-08.8a step 3 now reads `os.getuid` through `getattr`. Each new test has a mutation-table row, and tasks 08-02, 08-05 and 08-06 name them. A run on Windows itself is still unmeasured (A10).

Both unit designs were reviewed "sound with amendments". Every amendment is applied below. Where the two designs disagreed, or where they narrowed index decision M4, this section settles it (R-1 to R-7; R-8 and R-9 apply the ratifications).

**u11b-file-perms (P0.12b, P0.14)**

| Id | Amendment | Where it is applied |
|---|---|---|
| A1 | `c(pid)` does not exist in StataNow 19.5. `` display "CPID `c(pid)'" `` printed `CPID ` with rc 0. The pid comes only from Python's `os.getpid()`. | Every PF/LC cscript case reads the pid through `Macro.setLocal` from `os.getpid()`. No new line expands `` `c(pid)' ``. |
| A2 | `realpath(c(tmpdir))` breaks the `c(tmpdir)` prefix. On this Mac, TMPDIR `/var/folders/cr/…/T/` has realpath `/private/var/folders/…/T` ("prefix holds: False", re-measured). | TR-08.2: every path is spelled `os.path.join(<c(tmpdir) as given>, …)` and never passed through realpath, abspath or normpath. `tempfile.mkdtemp` normalises `//` (measured), so only its basename is used. Pinned by `TestThePrivateRoot::test_a_base_reached_through_a_symlink_gives_paths_the_caller_can_match`. |
| A3 | Opening a FIFO without `O_NONBLOCK` blocks (re-measured: "TimeoutError blocked" under a 2 s alarm; with `O_NONBLOCK`: ENXIO). | TR-08.3: the writer opens with `O_NONBLOCK`, checks `S_ISREG`, then clears `O_NONBLOCK`. `O_EXCL` is used for names that are always fresh (the preview page, and the app in a run folder). |
| A4 | `os.kill(pid, 0)` raises PermissionError for another account's live process (re-measured: `os.kill(1, 0)` gives PermissionError). | TR-08.4 `_dash_pid_alive`: only ProcessLookupError means dead; any other OSError means alive. |
| A5 | A 24 h age rule would delete a live long-running server's folder. | TR-08.5: on POSIX, a run folder of a live pid is never removed by age. The age rule applies only on Windows, where liveness is never probed. |
| A6 | Pruning previews by count alone deletes another live session's page. | TR-08.7: keep-five and `dash clear` touch only this pid's pages. Another pid's page goes only when that pid is dead (POSIX) or the page is more than 24 h old. A ceiling of 25 pages across all sessions bounds the disk. |
| A7 | No `python:` line may run before the Python guard. | TR-08.10: every program holding a `python:` line calls `_dash_require_python` as a command before its first `python:` line. `test_env_guards.cscript` ENV-12's program list is flipped (see Evidence §6). PF-10 asserts that no route makes a run folder when Python is absent. |
| A8 | `_dash_empty_data` writes a trailing newline (P1A-75 reads one line, then `r(eof)`). The spec has none. | TR-08.10, pinned by `TestTheAdoUsesThePrivateDir::test_empty_data_keeps_its_trailing_newline_and_the_spec_has_none` and P1A-75. |
| A9 | Stata's `file write` expands macro references found inside a value a second time (rev/r1.log: "R1 identical: False"). | PF-05 and `TestTheSpecWriter::test_the_python_writer_keeps_backtick_and_dollar_sequences_literal` assert that the Python writer reproduces `Macro.getLocal` exactly. The move is recorded as a hardening. |
| A10 | `main()` needs an exact rule for erasing inputs. | TR-08.8 `_dash_private_run_of`. Pinned by `TestTheServedAppIsPrivate::test_main_unlinks_only_when_all_three_paths_share_a_run_dir_under_dash_uid`. The rule holds under `runpy.run_path(…, run_name="__main__")` (dash.ado:7688) because it reads only the filesystem. |
| A11 | A bare single-line `python:` expression echoes its value into the log. | Every new `python:` line is an import, an assignment or a `Macro.setLocal(` call. Pinned by `TestTheAdoUsesThePrivateDir::test_every_new_python_line_is_an_assignment_or_a_setlocal`. |
| A12 | rclass calls clobber `r()`. | Callers copy `r(rundir)`, `r(spec)`, `r(data)` and `r(app)` into locals on the very next line. In `_dash_serve` the run is opened before `_dash_serve_spec`. Pinned by `test_the_run_paths_are_read_from_r_on_the_next_line`. |
| A13 | `os.O_NOFOLLOW`, `os.O_CLOEXEC`, `os.fchmod` and `os.getuid` are Unix-only. | They are read with `getattr(os, name, 0/None)`. Pinned by `TestWindowsPortability`: the writer and the root, and since round 2 the launcher's verified read and its reparse-point refusal. |
| A14 | A STATATMP folder made under umask 002 is 0775. The original design refused it; since ratification (01oct2026, R-8) dash proceeds instead. | dash proceeds, and the command's one note names `chmod go-w` and `STATATMP` (Evidence §3a R6). The help says only `c(tmpdir)` itself is checked, not its ancestors. Pinned by `TestThePrivateRoot::test_a_writable_non_sticky_base_proceeds_with_a_note_naming_chmod` and PF-12. |
| A15 | `dash clear` should not load the 32k-line module when there is no root. | TR-08.10 `_dash_tmp_clear`: a Mata `dir(c("tmpdir"), "dirs", "dash*")` test, with no Python run, decides whether to load. |
| A16 | The sweep must not remove files a later section keeps in a run folder while a server outlives its command. | After commit F2 no server outlives the Stata process that started it. Notes for S13 state the invariant: a run folder holds only what its own command needs, and nothing outlives that command's server. |

**u12-serve-lifecycle (P0.13)**

| Id | Amendment | Where it is applied |
|---|---|---|
| A1 | `sfi.BreakError` is an `Exception` (sfi.py:5709, 5723). `poll()` must not sit inside the `/health` probe's `except Exception:` (dash_render.py:32069). | TR-08.17. Pinned by `TestTheLauncherPollsStata::test_break_before_health_answers_is_not_swallowed`. |
| A2 | `_DashServeInterrupted` must not be a RuntimeError (`except RuntimeError` at 32200 maps to r(198)). | `class _DashServeInterrupted(Exception)`. Pinned by `TestTheLaunchReportBox::test_the_interrupt_is_not_a_runtime_error`. |
| A3 | The served-name guard does not walk the module level, and the copy loop skips a missing name (28833). | F2 extends `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` to the top-level scope (dunder names skipped: Python 3.14's symtable reports `__conditional_annotations__`, measured) and adds `"_dash_watch_parent"` to its explicit tuple. |
| A4 | Everything from Popen to the final wait must sit inside one try/finally. A second interrupt during the stop goes straight to kill. | TR-08.17 `_dash_stop_child`. Pinned by `test_an_interrupt_between_popen_and_the_loop_stops_the_child` and `test_a_second_interrupt_during_the_stop_still_kills`. |
| A5 | Make console Ctrl+C give r(1) deterministically. | (a) The child stays in Stata's process group: no `start_new_session`/`process_group`, pinned in F2. (b) Under `--parent-watch` the app exits 130 on KeyboardInterrupt, and the launcher maps 130 and `-SIGINT` to interrupted (F4). |
| A6 | Erase the app only after `/health` answers AND the child's own flushed banner has been read. | TR-08.14. Pinned by `TestTheEraseRule::test_health_without_the_banner_leaves_the_app`. |
| A7 | "Port is free" is asserted by binding with SO_REUSEADDR. | The test helper `_port_free`. |
| A8 | The in-run poll for the files is bounded and reports names. | LC-01 polls up to 5 s, reports the names left, and looks only at this session's run folder. |
| A9 | End-to-end after the erase. | Measured during planning: a `pull_session` client that set `RangeSlider.value`, and `value_throttled` through `set_from_json`, produced no observable recompute within 10 s (the server's fit source was unchanged). So the literal live-move test is not reliable. The section pins three things instead (see Evidence §5). (a) A new live session after the erase is served. (b) The served recompute runs from the app's source with no file on disk: `make_document` plus a filter move, `test_help_claims_4._served_filter_move`'s method. (c) A source guard: the app never reads its own file. |
| A10 | Honesty about hosts. | Help, CHANGELOG and BUGS say "measured on macOS; Linux and Windows have not been measured". |
| A11 | LC-03 tests dash's catch-and-`error 1` path with a patched `pollstd`, not Stata's own Break handling. | Said in LC-03's comment and in the BUGS.md Resolution. Task 08-18 asks for the manual GUI check. |
| A12 | The token and real-server tests. | Every real-server test builds its URL through one helper, `_url(port, path)`, for S13. Run folders are removed by `_dash_tmp_close` on every path dash.ado controls. |
| A13 | Mutation-check the new map entries. | Tasks 08-05, 08-12 and 08-16 run `scripts/fncov/fncov_mutate.py --map` on the new keys. |

**Reconciliations between the two designs (this section's decisions)**

- **R-1. One erase mechanism, no `--ephemeral` flag.** u12 proposed a new renderer flag, `--ephemeral`. u11b proposed erasing inputs only inside a validated run folder (A10). This section keeps u11b's rule, `_dash_private_run_of`, as the only rule. It gates both the erase of the spec and data in `main()` (commit 1) and the erase of the app once ready (commit F2). Only dash's own private run folders are ever erased. A command-line user's files never are, whatever flags they pass. Every u12 test that used `--ephemeral` builds its paths with `dr._dash_run_open(str(tmp_path))` instead. `test_serve_browser.cscript` SB-07..SB-10 see no new argv flag.
- **R-2. Commit order:** P0.12b+P0.14, then F2, then F4.
  - F2 builds on commit 1's run folder.
  - F4 builds on F2's stdin pipe.
  - S13, the token (batch 2), builds on all three.
- **R-3. Copy list.** The served app writes no file and calls none of the private-file helpers. So only `"_dash_watch_parent"` joins the functions tuple, at the END after `"_dash_port_value"` (dash_render.py:28829).
  - index.md's R2 row also named `_dash_private_root` and the writer. Copying them would put dead code in the app.
  - S13's "after S08's last END entry" anchor is therefore `"_dash_watch_parent"`.
  - Ratified 01oct2026. S13's ratified answer 3 makes an app started by hand, with no `DASH_SERVE_TOKEN`, write its own `link.html`. That write is S13's (batch 2). R-3 stays true for S08's three commits, and `TestTheServedAppWritesNoFile` stays green here. S13 writes that file with its own copied `_dash_private_page`, copies none of S08's private-file helpers, and flips that guard (Notes for S13; index.md R2 row S13 and "Index overrides", row "Served app writes").
- **R-4. Case ids.** Every new cscript case uses the manifest's prefixes: PF (P0.12b/P0.14) and LC (P0.13). u11b's FP-xx, CLR-07 and HC4-22, and u12's SPU-04..06 and HC4-22, are renumbered PF-01..PF-10 and LC-01..LC-04. R-7 adds PF-11. At 7421d3d, `grep -n "\bPF-[0-9]\|\bLC-[0-9]" test/*.cscript test/*.py` printed nothing.
- **R-5. `test_clear_registry.cscript` is not edited.** It has no `c(python_exec)` gate (grep count 0). BRIEF forbids adding a Python skip to a script that has none. So the preview-and-clear case (u11b's CLR-07) is PF-02 in the Python-gated `test_wp29_truth.cscript`.
- **R-6. Preview retention (plan delta, ratified 01oct2026).**
  - PLAN.md BR-29.11 said "One-line preview pages are deleted when the command ends", and E6 said "no preview page survives the command" (both before PLAN.md's 01oct2026 amendment).
  - That cannot hold. The browser reads the page asynchronously after `open`/`xdg-open` returns (`_dash_open_page`). Under `$dash_nobrowser` the page path is printed for the user to open by hand (dash.ado:6177).
  - P0.14's own text asks for pruning, privacy and documentation ("never deleted and are 0644 … Nothing prunes them and nothing documents them").
  - This section implements bounded retention:
    - the page is 0600, in a 0700 folder;
    - each session keeps at most five pages;
    - `dash clear` removes the session's pages, except a page a browser was asked to open in the last 60 s;
    - a dead session's pages are removed.
  - Ratified 01oct2026 (task 08-01 copies the row). PLAN.md BR-29.11 and E6 already carry this retention (PLAN.md preamble, amended 01oct2026), so S15 rewords nothing here.
- **R-7. `dash build, server`'s `.py` is the app, so M4 applies to it (index M4).**
  - M4 (index.md decision record) says "the app, spec and data files are written 0600 inside a 0700 directory". u11b kept the user-named server app on the umask, as twoway's `saving()` (D6: `build server app: 0o644`). That narrowed M4 and is withdrawn.
  - The `.py` embeds every observation in base64 (dash.sthlp:1434-1436, 1574-1575), so it is a copy of the data like the run-folder app.
  - Every server app dash writes is written 0600, on every route: `dash serve`'s launch, `dash build, server` and the command line `--mode server`. `ServerAppBuilder.build(private=True)` first removes an existing file of this account at the name with `_dash_private_clear_name` (TR-08.6a), which never follows a link. It then creates the file with `O_CREAT|O_EXCL|O_NOFOLLOW` through `_dash_private_write(…, exclusive=True)`. So a `replace` makes a new 0600 file, and a reader holding the old file open never sees the new data.
  - **Anti-hijack, not privacy (ratified 01oct2026).** A symbolic link, a non-regular file or another account's file at the named `.py` is refused with r(7102) (M4a), and so is a name that reappears between the removal and the create. These refusals stop a planted name from redirecting the write. They do not depend on whether the folder or disk is private. This changes what a user-named `.py` did: `ServerAppBuilder.build`'s `open(output_path, "w")` (dash_render.py:29182) followed a link at the name and wrote its target. The help and CHANGELOG say so. A folder at the name is still refused earlier by `_dash_saving_clobber` (r(198) without `replace`, r(608) with it).
  - **What stays with the user:** the folder. A `.py` the user names sits in the folder the user names. dash never changes the mode of a folder it did not make, as twoway never changes the folder of a `saving()` file. For every folder dash chooses (run folders, `previews/`, the root), M4's "inside a 0700 directory" holds wherever the disk keeps permissions. The maintainer ratified this reading (01oct2026, answer 2: "do not refuse writing the app files into a directory of the user's that is not private"). A folder the user names that others can read or write is never refused, never re-moded and never noted. Only a `.py` that the disk will not keep at 0600 is noted (R-8).
  - Pages the user names with `saving(.html)` keep the umask (BR-08.5). M4 names the app, spec and data, not the saved page, and twoway's `saving()` and `graph export` write 0644 (T4).
- **R-8. Proceed and note; anti-hijack guards kept (ratified 01oct2026, answer 2).** Each condition dash meets when it writes falls into one of three classes. A condition is never moved from one class to another.

  | Class | Conditions | What dash does | Code |
  |---|---|---|---|
  | **Privacy shortfall** (never refused) | (a) `c(tmpdir)` is writable by others with no sticky bit, or belongs to another account (not root). (b) `dash-<uid>` is a link, not a folder, or another account's. (c) A folder dash chose (the root, a fallback root, `previews/`, a run folder) still has group or other bits after `fchmod(0o700)`, or `fchmod` fails. (d) A file still has group or other bits after `fchmod(0o600)`, or `fchmod` fails. | For (a), (c) and (d) dash goes on in the same place. For (b) it leaves the planted object alone (never used, never followed: that half is the anti-hijack guard) and uses a fallback root `dash-<uid>-<8 chars>` (TR-08.2a). Every file is still created with mode 0600 and `fchmod`ed to 0600 wherever the disk allows. The command prints **one** note (below). | rc unchanged (0 on success) |
  | **Anti-hijack refusal** (kept; not about privacy) | At the target name: a symbolic link (ELOOP), a FIFO or device (ENXIO, or not `S_ISREG`), a file with other hard links (`st_nlink != 1`), another account's file, or a name that appears between `_dash_private_clear_name` and the `O_EXCL` create (EEXIST). Also, at the launch, an `app.py` whose open file is not the one `main()` wrote: a link, not a regular file, another account's, another `(st_dev, st_ino)` or size, or other bytes (SHA-256) (TR-08.8a, round 2). | Nothing is written through the name and the target is untouched. `_DashUnsafePath` is raised with `dash: refused to write <path> (<why>); dash never writes through a link, into a pipe or device, or over another account's file.` | r(7102), with the message as the traceback's last line (M4a), on every route: the renderer's writes and the ado-side writes alike (the ado-side writers raise; they no longer return text) |
  | **Operating-system failure** (not a refusal) | Creating the root, a fallback root, `previews/` or a run folder fails with an OSError (c(tmpdir) missing, not a folder, read-only, full, or unreadable). | `_dash_run_open`/`_dash_preview_path` return the message in `err`, and the ado prints it with `_dash_say("err", …)`. | r(603), the code Stata's own `file open` gives for a path it cannot create (measured, Evidence §3a S1). A later OSError while writing a file propagates out of the `python:` line, which gives r(7102), as `open()` failures do today. |

  - **The note.** It is one paragraph that starts with `dash: note: ` once. It joins, with two spaces, one sentence per location found in the command:
    - (a) `Stata's temporary directory <tmpdir> can be changed by other accounts (<why>), so another account could move or replace the folders that hold dash's copies of your data, though not read them.  To keep them private, run chmod go-w on it, or start Stata with STATATMP set to a folder only you can write.` `<why>` is `other accounts can write to it and it has no sticky bit` or `it belongs to another account`.
    - (b) `<root> is not yours to use (<why>), so dash left it alone and kept its copies of your data in <fallback>, which only you can open.  Remove <root> to stop this note.` `<why>` is `it is a link`, `it is not a folder` or `it belongs to another account`.
    - (c) `<folder> could not be made private (<why>), so other accounts may read the copies of your data dash keeps there.  To keep them private, start Stata with STATATMP set to a folder on a disk that keeps permissions.` `<why>` is `its permissions stay 0o<NNN> after dash set them to 0700` or `its permissions could not be set: <strerror>`. A run folder or `previews/` adds this sentence only when its root did not.
    - (d) The note for a file is printed only for a file outside every folder dash chose. That is the user-named `dash build, server` `.py` (and an output named on the command line). The renderer prints it to stdout with `print(…, flush=True)`: `dash: note: <path> could not be made private (its permissions stay 0o<NNN> after dash set them to 0600); it holds every observation of the dashboard's variables, so keep it where other accounts cannot read it.` Python's printed text is shown literally, not as SMCL (Evidence §3a P1). Files inside folders dash chose are covered by their folder's sentence. On a POSIX disk, a file that the writer creates with mode 0600 is 0600 whatever the umask, even when `fchmod` fails (§3a R7). So a file inside a private folder cannot be loose. A disk that keeps no file permissions keeps no folder permissions either, and sentence (c) names that folder. That last claim is unmeasured here, because no such disk was mounted.
  - **Where and how often it prints.** A command prints at most one note line per location. Every route prints at most one in all, with one exception: `dash build, server` on a disk that keeps no permissions names two locations.
    - **One-line form.** `_dash_tmp_open` prints the note with `mata: _dash_say("txt", "", st_local("_to_note"), "")` (SMCL-safe, measured §3a S3) and returns `r(noted) = "1"`. `_dash_plot` copies it into `_dash_noted` on the next line (A12) and passes `` noted(`_dash_noted') `` to `_dash_tmp_preview`. `_dash_tmp_preview` prints its own note only when `noted` is not `1`. The renderer is silent for the preview page, because the page sits in `previews/`.
    - **`dash build`.** `_dash_tmp_open` prints the note. A `server saving(<file>.py)` adds sentence (d) only when the disk will not keep that `.py` at 0600. That is a second location, so it gets a second line.
    - **`dash serve` (the served path).** `_dash_tmp_open` prints the note before the `starting Bokeh Server` announcement. The renderer is silent for `app.py` in the run folder. The launcher and the app print nothing about privacy.
    - **`dash clear`.** It prints no note.
    - **`quietly`.** Under `quietly dash …` the note is not shown, like dash's other notes (measured §3a S4, P2).
    - **Windows.** No base or mode check runs, so only sentence (b) can appear (a `dash` that is a link or not a folder). Privacy there rests on the per-user TEMP folder, which has not been tested.
  - **Residual (named in the help, BUGS.md and TR-08.21; rewritten by the round-2 ratification).** Take a `c(tmpdir)` that others can write and that has no sticky bit. Another account can rename dash's folders, but it cannot read their 0600 files. The old residual was that it could substitute `app.py` between the identity check and the child's own open. That is closed (R-9): the child never opens a path, and runs only the bytes dash read through the descriptor it verified. Three things remain, all only in the case the note names:
    - **Inputs.** Such an account could replace `dash-<uid>` with a folder of its own between dash.ado's write of `spec.json`/`data.json` and the renderer's read of them by path. That changes what the dashboard shows. Its own file is refused by the writer only when it is planted before the write. The builder puts spec values into the generated source through `%r` and base64, as at 7421d3d; this plan did not audit every such value.
    - **Denial.** It could delete or move the app, which makes the launch fail with r(7102) (a different file) or r(198) (no file). Nothing of the user's runs or leaks.
    - **Hand-run apps.** A `python app.py` or `bokeh serve app.py` the user runs opens the file by name and imports from its folder (§3b C). The help says to keep such a file in a folder only the user can write (TR-08.11).

- **R-9. Launch from the open file (ratified 01oct2026, round 2, answer B: "Launch from open file").** This applies to every route on which dash itself starts the app. There is one: `_dash_launch_app`, reached from `dash serve` and from the renderer's `--launch` (`__main__`).
  1. **What is verified.** `main()` writes the app with `_dash_private_write(…, exclusive=True)` and returns `_DashWrittenApp(st, sha256)`: the writer's `os.fstat` result and the SHA-256 of the UTF-8 bytes it wrote. Right before Popen, `_dash_read_verified_app(app_path, expect)` opens the path with `O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC | O_BINARY` (each through `getattr(os, name, 0)`). It checks the open descriptor with `os.fstat`: `S_ISREG`; on POSIX, `st_uid == os.getuid()`; and, when `expect` is given, `(st_dev, st_ino, st_size)` equal to `expect.st`'s. It reads exactly `st_size` bytes through that descriptor, then one more read must return `b""`. With `expect`, the bytes' SHA-256 must equal `expect.sha256`. Each failure raises `_DashUnsafePath` (anti-hijack, r(7102), M4a), and no child is started. An OSError from the open or the read (the file is gone, say) is the launch-failure class: `RuntimeError`, r(198) through the box, as a child that cannot start is today.
  2. **What runs.** `[sys.executable, "-P", "-c", _DASH_BOOT, app_path, "--port", str(port), …]` with `stdin=subprocess.PIPE`. The launcher writes `_dash_app_frame(data)` to the pipe: the ASCII line `DASHAPP1 <n> <sha256>\n` followed by exactly *n* bytes. The bootstrap:
     - reads the frame with `os.read(0, …)` only, so nothing after it is consumed: S13's key line and F2's watch read the same pipe afterwards;
     - checks *n* and the SHA-256, exiting 1 with `dash: the app was not handed over on standard input` or `… was damaged` and running nothing;
     - registers the source with `linecache` under `app_path`;
     - compiles it with `compile(src, app_path, "exec", dont_inherit=True)`;
     - installs a fresh `types.ModuleType("__main__")` whose `__file__` is `app_path`;
     - sets `sys.argv = [app_path, …]`, so argparse's program name stays `app.py`;
     - and `exec`s it.

     The app's tracebacks, exit statuses (2 for an argparse error, 130, -SIGINT for an uncaught KeyboardInterrupt), banner and `/health` are those of `python app.py` (§3b 1-3, B).
  3. **Why `-P`.** Under `-c`, Python 3.13 puts `''` (the working folder) first on `sys.path` and imports `linecache` from it before the command runs (§3b F). `python app.py` puts the app's folder there instead (§3b C). `-P` puts neither (measured: `sys.flags.safe_path` True, `sys.path[0]` the stdlib zip). dash's minimum Python is 3.13 (`_dash_pymin`), and `-P` exists from 3.11. `sys.executable` is the launcher's own interpreter, so the flag and the bootstrap always match the version that runs them (§3b ST1, ST3).
  4. **Portability.** One route on every system: a pipe on stdin, `os.read(0, n)` and a self-checking frame. `/dev/fd/N` was rejected. Windows has none, and on macOS it shares the descriptor's offset (§3b D1); it would also make `__file__`, the tracebacks and `sys.path[0]` read `/dev/fd`. `_DASH_BOOT` holds no `"` and no `\`, so `subprocess.list2cmdline` only wraps it in double quotes on Windows (pinned). Python sets its standard descriptors to binary mode on Windows at start-up, and a CRLF translation would fail the SHA-256 check rather than run altered code. Windows has no `O_NOFOLLOW`. There `_dash_read_verified_app` first refuses an `lstat` that is a link or a reparse point (`st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT`). A swap between that `lstat` and the open is then caught by the identity, size and SHA-256 checks on the descriptor. Linux and Windows have not been measured (A10). The Windows code paths are still run by tests on macOS: `TestWindowsPortability` runs the read without `O_NOFOLLOW`, `O_NONBLOCK`, `O_CLOEXEC` or `os.getuid`, and runs the reparse-point refusal under `os.name == "nt"`. `TestTheBootstrap::test_a_crlf_translated_frame_runs_nothing` runs the CRLF claim. Measured with §3b's `boot.py` at 3.13.9 and 3.14.5: a frame whose body had every `\n` translated to `\r\n` exits 1 with `was damaged`, and so does one translated in its header too. The same frames with the digest check removed print `SHOULD NOT RUN` with rc 0 (`<scratch>/wp29r2/s08-crit3/crlf.py`, `crlf2.py`).
  5. **Order and the pipe.** The child's stdin pipe moves from F2 into commit 1, because the hand-over needs it. In commit 1 the launcher never closes the pipe after the frame (the app does not read it before F2), and closes it after the final `proc.wait()`. F2 adds `--parent-watch`. F4's single try/finally holds the hand-over as its first statement. S13's key line follows the frame (Notes for S13).
  6. **Memory.** The launcher holds the app's bytes only between the read and the hand-over. Measured: a 100 MB app was handed over in 0.10 s (§3b 4). `del` runs on both once the frame is written.
  7. **Withdrawn:** `_dash_same_file` (the path-based `lstat` identity check of round 1) and the R-8 residual "the instant between the identity check and the child's open".
  8. **Unchanged:** F2's erase of `app.py` once `/health` and the banner have both arrived (A6). The child no longer reads the file, so the erase no longer races the child's open. The rule is kept as written, because S13 reads the banner detection. Erasing at the hand-over instead is left to a later package (Notes for the closeout).

## Overview

dash writes three kinds of temporary copy of the user's data:
- the spec and data files of every render;
- `dash serve`'s generated app, which embeds every observation in base64;
- the one-line form's preview page.

Measured at 7421d3d:
- **Every copy follows the umask.** Copies are 0644, or 0664 under umask 002. They sit at a predictable Stata tempfile name (`St<pid>.<n>`) directly in `c(tmpdir)`. A symbolic link at that name is followed, and a pre-created 0666 file keeps its mode. Under umask 002 the app another group member could rewrite is the very script `python <path>` then runs. GAPS2 I3: "The app file and the spec/data JSON are written with the default umask".
- **The preview page is never deleted.** Its name is unregistered. A second preview overwrites the first. One 1.3 MB copy per session stays for good. GAPS2 X3 counted 66 such orphans.
- **The served app outlives Stata.**
  - A SIGKILL or SIGTERM of Stata leaves it answering `/health` with ppid 1, holding its port, beside three 0644 data-bearing files (GAPS2 F2).
  - Break in GUI Stata cannot stop it: the launcher never calls `sfi.SFIToolkit.pollstd()` (GAPS2 F4, H2).
  - A console Ctrl+C returns rc 0 rather than Stata's r(1).
  - Every message tells GUI users to press Ctrl+C (F9c).

After this section:
- **Private copies.** Every temporary copy lives in `c(tmpdir)dash-<uid>/run-<pid>-<random>/`. The folder is 0700, owned and checked. Its files are created 0600 through a writer that, as an anti-hijack guard, follows no link, opens no FIFO and refuses another account's file. dash removes the folder when the command ends.
- **Unsafe locations proceed (R-8).** Some locations cannot be made private: a `c(tmpdir)` other accounts can change, or a disk that keeps no permissions. dash still writes there, 0600 wherever it can, and prints one `dash: note: …` per command naming the location and the remedy. A `dash-<uid>` planted as a link, a non-folder or another account's folder is left alone. dash uses a fallback root `dash-<uid>-<8 chars>` (0700) beside it and names both in the note. No privacy condition ends a command with an error. A folder left by an error, Break or crash is swept by the next dash command of the session, or by any later session once the Stata that made it is dead.
- **Previews.** They go to `dash-<uid>/previews/` under unique names (0600). Each session keeps five; `dash clear` removes them.
- **Served app.**
  - The app stops within five seconds of its Stata process ending, however Stata ends: a pipe on its stdin reaches end of file.
  - Its spec and data are erased once it is written, and the app file once the server answers, so no copy of the data stays on disk while it serves.
  - Break stops it from every front end. The launcher polls Stata, stops the child and ends `dash serve` with r(1).
  - The messages name Break.
- **User-named pages keep the umask.** A `saving()` page keeps twoway's umask semantics. twoway's own `saving()` and `graph export` are 0644 under umask 022 (measured T4).
- **Every server app is 0600 (M4, R-7).** `dash build, server`'s `.py` embeds the data, so it is written 0600 like `dash serve`'s app. A `replace` creates a new file. A link, a non-regular file or another account's file at the name is refused (anti-hijack, r(7102)). The folder the user names is left as it is: it is not refused, re-moded or noted (ratified).
- **dash runs only what it wrote (R-9, round 2).** `dash serve` never starts its app by name. It reads the `app.py` it wrote through a descriptor it opened and checked, and hands those bytes to `python -P` on the child's stdin. So a file or folder swapped in afterwards is never run, and no module beside the app or in the working folder is imported.

**Why one section.** The two units edit the same sites:
- the temp-file writers of `_dash_plot`, `_dash_build` and `_dash_serve`;
- `main()`, `ServerAppBuilder.build` and `_dash_launch_app`;
- the emitted app's `__main__`;
- the Server Mode help.

The lifecycle fix's "erase the app once it answers" needs the private run folder to decide what dash may erase. Index A1 groups them.

**Test order (CLAUDE.md rule 7) and commit rule (D1).** There are three cycles, each a full red-then-green loop. No test-only commit exists, and no commit is red.
- **Cycle 1 (tasks 08-02..08-10, commit `(WP-29 P0.12b, P0.14)`).**
  - Tasks 08-02..08-04 write every P0.12b/P0.14 regression test, run it against the batch-1 base and save the failure text to `<scratch>/08-P0.12b-failure.txt`. Nothing is committed.
  - 08-05..08-09 turn the tests green and flip the pins.
  - 08-10 closes both entries and commits.
- **Cycle 2 (08-11..08-14, commit `(WP-29 P0.13 F2)`)** writes its tests against the tree commit 1 leaves and saves `<scratch>/08-P0.13-F2-failure.txt`.
- **Cycle 3 (08-15..08-19, commit `(WP-29 P0.13 F4)`)** does the same on F2's tree and saves `<scratch>/08-P0.13-F4-failure.txt`.

## Risk: [red] — the write path of every render and the life of every served process change, on security-sensitive code, in a file 13 sections edit

**Why.**
- `_dash_write_stata_data`, the spec writers, `main()`, `ServerAppBuilder.build` and `_dash_launch_app` run on every dashboard. A mistake breaks every render, or leaves data readable.
- `dash serve` blocks Stata, so a launcher that swallows Break hangs the session.
- Two of the target behaviours cannot be measured here: GUI Break (CLAUDE.md rule 10), and Linux/Windows hosts.

**Risk factors.**
1. Moving the spec and empty-data writes from Stata's `file write` to Python makes those paths need Python. 15 cscripts call `_dash_prepare_spec` and 13 call `_dash_serve_spec` directly with their own tempfiles (grep counts).
2. The Python guard's placement is certified by ENV-12. Its pinned program list (`test_env_guards.cscript:509`) must be flipped, not weakened.
3. A deferred cleanup (the sweep) replaces Stata's immediate erase on the error path.
4. The path spelling must keep `c(tmpdir)` as a prefix (A2).
5. A broad `except` can swallow `BreakError` (A1), and a RuntimeError subclass turns Break into r(198) (A2).
6. Real-kill tests on a red tree create orphan servers.
7. dash.ado `_dash_plot` 5955-6182 and `_dash_prepare_spec` are also edited by S04 (function evaluation) and S06 (hover export) in the same batch.
8. GitNexus has no index for this repository. `list_repos` lists only TYME and PhotoShootPlannerPro, so impact must be computed after `npx gitnexus analyze`.
9. **Proceeding where others can write (R-8, ratified).** Take a `c(tmpdir)` that others can write and that has no sticky bit. Another account can rename `dash-<uid>` or a run folder and put its own folder at the name. Path-based writes would then land in a folder that account controls. It cannot read them: they are 0600 files owned by the user. But it could swap in its own `app.py` before `python app.py` runs, or plant a module that `python app.py` imports from the app's folder (§3b C). The old r(603) refusal ruled that out, and ratification removed it.
10. **The fallback root** adds a second folder name to the sweep, the close and the erase rule. A slip there would leave copies behind, or erase outside dash's own layout.
11. **The launch from the open file (R-9, round 2)** changes how every served app starts: `python -P -c <bootstrap>` plus a framed stdin hand-over replaces `python app.py`. A bootstrap that differs from a script run (sys.path, `__main__`, argv, tracebacks, exit codes) would break every served dashboard, and a hand-over that blocks would hang `dash serve`.

**Mitigation.**
1. The Python requirement is new only on paths that already need Python. P1A-72 (`test_parser.cscript`) already runs `dash build`. `test_serve_options.cscript` already runs `dash build` and `_dash_write_data`. Every render route calls `_dash_require_python` today.
2. ENV-12's list is flipped with a `Flipped:` line, and its "guard before the first `python:` line" assertion is kept for every program on the new list.
3. Leftover run folders are 0700 with 0600 files. They are swept by pid (same pid at the next command; dead pid at any later command).
4. Paths are spelled from `c(tmpdir)` (A2) and pinned by a symlinked-base test.
5. `poll()` runs outside every `except Exception` (A1). `_DashServeInterrupted(Exception)` is caught before RuntimeError.
6. Every real-kill test uses `--timeout 1`, and a `finally` kills the port's listener.
7. S08 merges last in batch 1 (index merge order) and re-applies its hunks by symbol, never by line (R4).
8. Task 08-02 runs `npx gitnexus analyze` in the worktree, then `gitnexus_impact` on each edited symbol, and reports any HIGH/CRITICAL to the maintainer before editing (CLAUDE.md, index R8). `_dash_launch_app` and `main` are expected HIGH (index R8).
9. The anti-hijack guards are kept on every write: `O_NOFOLLOW`, `O_NONBLOCK`, fstat type, owner and nlink, and `O_EXCL` for fresh names. The launch from the open file (R-9, TR-08.8a) reads the app through a descriptor checked for type, owner, `(st_dev, st_ino)`, size and SHA-256. Measured in §3a R9: a renamed and replaced folder gives a different identity. The child runs those bytes under `-P` and never opens a path, so there is no window between the check and the child's open (measured, §3b A/B and G). The command's note names the shared folder and the remedy. What remains is recorded in R-8's residual: the inputs read by path, denial, and hand-run apps.
10. Every root, whether `dash-<uid>` or a fallback, is recognised by one helper, `_dash_own_root`: the name, `lstat` showing a folder that is not a link and is owned by the uid, and a parent spelled as `c(tmpdir)`. The sweep, the close, `dash clear` and `_dash_private_run_of` all use it. Each has a test with a fallback root (`TestTheRunDir`, `TestThePrivateRoot`, PF-09).
11. The bootstrap's behaviour is pinned against a script run (`TestTheBootstrap`: `__name__`, `__file__`, argv, program name, traceback file, line and text, exit statuses 2, 130 and -SIGINT, and bytes after the frame left on stdin), and every real-server test (`TestServeBlocksUntilCtrlC`, `TestTheRealHandoffServes`, HC4-19, `TestTheServerDiesWithItsLauncher`) now runs through it. The hand-over writes 1 MiB per bootstrap read: 100 MB took 0.10 s (§3b 4). A child that dies first gives BrokenPipeError, which is caught. Stata's Python ignores SIGPIPE (§3b ST2, ST4), so the failure is reported and the child stopped.

## Dependencies

- **Depends on: 01.**
  - S01 supplies:
    - the open BUGS.md entries for P0.12b, P0.13 and P0.14;
    - their `WP29_OPEN` keys in `test/test_tracking_documents.py`;
    - the CHANGELOG markers `<!-- WP-29 P0.12b -->` and `<!-- WP-29 P0.14 -->` (end of `### Security`), and `<!-- WP-29 P0.13 -->` (end of `### Security` and under `### Fixed in WP-29`);
    - `test/test_wp29_truth.cscript`, with its tally helpers and the marker `* ==== append new blocks above this line ====`.
  - **The batch-1 worktrees are cut from `wp29-p0` before S01 merges** (index "How to execute" step 1). So task 08-02 first checks that S01's artifacts are in the worktree. If they are absent, it cherry-picks S01's one commit from branch `wp29-s01`: `git -C <wt> cherry-pick $(git -C <wt> log -1 --format=%H wp29-s01)`. The merger later lands only this section's three commits (`format-patch` per commit), and S01's patch is already on `wp29-p0` by then.
- **Blocks:**
  - **13 (served-app token).** It writes into the private root, reads `_dash_private_root`/`_dash_private_write`, and adds names after `"_dash_watch_parent"`. It may carry its token on F2's stdin pipe, which needs the watch to read one bounded line first (see Notes).
  - **14 (embed rows).** u10 changes `_dash_write_stata_data`, whose final write this section routes through `_dash_private_write` (index "14 ← 08").
- **Parallel batch: 1.** Can run with 02, 03, 04, 05, 06, 07, 09. Merge order: `S01, S09, S03, S02, S04, S06, S07, S05, S08`.
- **Why last.** S08 rewrites every temp-file writer in `dash.ado` (`_dash_plot` export and render, `_dash_build`, `_dash_prepare_spec`, `_dash_serve`) and the launcher (dash_render.py:31888-32205). S04 and S06 also touch the export region (index "S08 last").

## Evidence

All anchors are at 7421d3d. Later batch-1 merges shift them, so symbols are authoritative. Every Stata measurement was made with `scripts/stata_slot.sh` on StataNow 19.5 MP, console, `c(os)=Unix`, Mac (Apple Silicon). The scratch logs do not outlive the planning session, so the outputs are quoted here.

### 1. twoway truth and Stata's own temp files

- **T5: twoway leaves no file.** After `twoway scatter mpg weight` and `twoway line mpg weight, sort` with no `saving()`, `c(tmpdir)` held 4 entries before and 4 after ("T5 after n= 4 new= []").
- **T4: named outputs follow the umask.** Under umask 022, `twoway …, saving(g_saved)` and `graph export` .svg/.png were each 0644 ("T4 gph: 0o644 … svg: 0o644 … png: 0o644").
- **T1: tempfile names.** `tempfile t1` names `<c(tmpdir)>/St30194.000001` (m2.log:54: `…/m2/tmp//St30194.000001`). `c(tmpdir)` ends in `/` (m2.log:49: `TMPDIR=…/m2/tmp/`) and follows STATATMP. `tempfile` does not create the file (`confirm file` rc 601).
- **T2, T3: Stata resets the mode.** `file open … write` creates 0644 under umask 022. A file pre-created 0600 from Python and then written with Stata's `file open … write replace` comes back 0644. Pre-creating a file Stata writes cannot protect it.
- **T6, T6b: Stata erases a Python-written file at a registered name**, whether the program ended normally or with an error ("exists: False" both; m3.log:74, 94). It does not erase a directory made at a tempfile name, empty or full (m3.log:66: `True ['x.json']`).
- **Stata reuses tempfile names.** The next program got the same `St35269.000001` (m3.log:80).
- **atexit does not run at batch Stata exit** ("NO atexit marker", m3).
- **T8: mkdtemp mode.** `tempfile.mkdtemp(dir=c(tmpdir))` gives 0700, owned (m3.log:100: "T8 mkdtemp mode: 0o700 own True").
- **m7: quietly and capture.**
  - Under `quietly`, an inner error message still prints (Q2).
  - `quietly { capture noisily … }` prints normal output again (Q3).
  - A wrapper using plain `capture` loses the error message under `quietly` (Q5: "capture noisily quietly _wrap err" printed nothing and gave rc 198).
  - r() survives a wrapping capture (Q4).
  - So the routes are not wrapped in a capture-based cleanup. The sweep covers errors.
- **`preserve`.** With auto loaded, `preserve` created no file in `c(tmpdir)`: the PRE and DURING lists were identical, and `c(max_preservemem)` is 1073741824 (rev/r1.log:91-99). The help says Stata's own files go to disk only above that.
- **Break conventions.** `display "before"` then `error 1` logs `--Break--` and `r(1);` (t2/p2g). `capture noisily error 1` gives `_rc=1`. When a program ends with r(1), Stata erases its tempfiles, silently, even after an early erase (P2e, P2f).
- **A BreakError raised by hand out of a `python:` line is r(7102)**, not r(1) (p2.log:54 "P2a … _rc=7102"; :62 P2b the same for KeyboardInterrupt).
  - This is a synthetic raise with no Break pressed.
  - sfi.py:5737-5742 says a BreakError from a real Break "stops execution and a return code of 1 is sent back to Stata". That could not be measured (rule 10).
  - Stata's own `sleep` ignored SIGINT in batch. SIGINT to the Stata pid raised KeyboardInterrupt in running Python ("P1C: KeyboardInterrupt after 3.06 s").
  - `` sfi.SFIToolkit.macroExpand("`c(console)'") `` is `console` in console Stata (p2.log:46).
- **Crash leftovers.** After a SIGKILL of Stata, its own `St56911.000001-.000003` and `SQ56911.000001` stayed in STATATMP, and a new session did not remove them (t3).

### 2. dash today, saved page and every render route

Measured with `c(tmpdir)` chmod 1777 to stand in for a shared /tmp (m4.log). m6 adds umask 002.

- **D1: the preview overwrites itself.** Three one-line previews left one file: `('St43889.000001.html', '0o644', 1300384)`. Each preview overwrote the last, because the name is reused.
- **D2: `dash clear` leaves it**, and it is still there after Stata exits.
- **D3: it embeds the data.** The preview is 1,300,383 bytes and holds the data (`has 'mpg': True`).
- **D4: spec and data follow the umask.** `D4 spec: 0o644 size=465 data: 0o644 size=2490`.
- **D5: so does the served app.** `D5 served app (dash serve route): 0o644 size=1254439`.
  - **U2 (umask 002):** `U2 spec: 0o664 … data: 0o664 … served app: 0o664 … name: St01984.000003`. Under umask 002 the app is group-writable at a predictable name before `python <path>` runs it.
- **D6: user-named outputs follow the umask.** `D6 build html: 0o644 … build server app: 0o644`, the same as twoway (T4). The page matches twoway, but the server app embeds every observation (`_DATA_B64`), so the 0644 `.py` is the M4 defect that R-7 fixes.
- **D7: the empty data file follows it too.** `D7 empty data: 0o644 size=155`.
- **D8: a pre-existing file keeps its mode.** `D8 pre-created 0666 then _dash_write_data: 0o666`.
- **D9: a link is followed.** `D9 symlink followed; victim now starts: {"values":[{"mpg":22.0},{"mpg"`.

The code (7421d3d):

```stata
5955    else {
5956        tempfile saving_path_tmp
5957        local saving_path = "`saving_path_tmp'.html"
5958        local open_browser = 1
```
The `.html` name is never registered, so Stata never erases it.

```stata
6038    tempfile data_json_path spec_json_path
...
6143    quietly file open `fh' using "`spec_json_path'", write replace text
6144    file write `fh' `"`master_json'"'
6145    file close `fh'
```
The same pattern is at `_dash_prepare_spec` 7286-7288. In `_dash_empty_data` it is 4281-4283, with `_n` at 4282. The `tempfile` lines are `_dash_build` 7395 and `_dash_serve` 7598 and 7652 (`tempfile serve_app_path`).

```python
1482    with open(path, "w", encoding="utf-8", newline="\n") as fh:   # _dash_write_stata_data
1483        fh.write(text)
29182        with open(output_path, "w", encoding="utf-8") as f:         # ServerAppBuilder.build
29183            f.write(source)
31940        with open(output_path, "w", encoding="utf-8") as f:         # main(), standalone
```

`_DASH_ADO_ENTRY_POINTS = (_dash_write_stata_data,)` is at 1493. The module loader is `_dash_write_data` 4315-4350 (`sys.modules["_dash_render_export"]`, keyed by realpath, size and mtime). The served app embeds `_SPEC_B64`/`_DATA_B64` and holds no reference to the temp spec or data paths (grep count 0). Its only file reads are a scheme file and the `/health` write. Elsewhere, dash_parse.mata has no `fopen`/`fput`, and dash_setup.ado writes no files.

### 3. Re-measured during this plan (scratch `wp29/s08`)

```
A without O_NONBLOCK: TimeoutError blocked              # os.open(FIFO, O_WRONLY|O_CREAT|O_NOFOLLOW|O_CLOEXEC), 2 s alarm
B with O_NONBLOCK: ENXIO
C TMPDIR /var/folders/cr/…/T/ realpath /private/var/folders/cr/…/T prefix holds: False
D kill(1,0): PermissionError
E mkdtemp abspath of a // dir: …/scratchpad/wp29/s08/run-1-e4o9ko78     # the "//" was normalised away
```

The privacy prototype (u11b `proto.py`, rerun under umask 002 and 277 in a fresh base):

```
P1 root dash-501 0o700 under umask 002
P2 file mode under umask 002: 0o600
P3 file mode under umask 277: 0o600
P4 symlink refused: ELOOP victim still V
P5 hard link refused; victim still V
P6 loose root tightened to 0o700
P7 symlinked root refused: dash-501 is not a directory (or is a symbolic link)
P8 refused: c(tmpdir) is world-writable without the sticky bit
```

P7 and P8 show the prototype's original refusal design. Since ratification (R-8), P7's planted root gives a fallback root and a note, and P8's base gives a note. §3a has the measurements.

How a renderer refusal reaches Stata (re-measured for R-7, scratch `wp29/s08-m4fix`, through `scripts/stata_slot.sh`). A program ran `python: _ns = runpy.run_path("<file>", run_name="__main__")` under `capture noisily`:
- **M4a.** The file raises `_DashUnsafePath("dash: /x/app.py could not be written privately (it is a link).")`. The log shows a traceback ending `_DashUnsafePath: dash: /x/app.py could not be written privately (it is a link).`, and `M4P rc=7102`. This is the same r(7102) that `_validate_output_path`'s refusals give today (its docstring, dash_render.py:31794-31815). The probe's message is the original wording. Since ratification the refusal reads `dash: refused to write <path> (<why>); dash never writes through a link, into a pipe or device, or over another account's file.` (R-8). The class and the code are the same.
- **M4b.** The file prints the message to stderr, then `raise SystemExit(1)`. The log shows the message and `SystemExit: 1`, and `M4E rc=0`. A SystemExit would turn the refusal into a silent success, so the renderer never uses one for it.

`c(pid)` (rev/r1.log:42-46): `` capture noisily display "CPID `c(pid)'" `` printed `CPID ` and `CPID_RC 0`, while `os.getpid()` (84772) equalled the `St84772.*` prefix. The `file write` re-expansion (rev/r1.log:80): `R1 identical: False`. The macro held `` `c(pid)' `y' `` and `file write` dropped both. Real specs agree byte for byte only because `_json_escape` writes `` ` `` and `$` as ``` and `$` (dash_parse.mata:301-302). m5 showed `M5 identical bytes: True len 300031 300031` for a 300 KB spec with compound quotes, backslashes and CJK text.

### 3a. Re-measured for the ratification (01oct2026, scratch `wp29r/s08`)

**Python.** `python3 <scratch>/wp29r/s08/proto.py <scratch>/wp29r/s08` built a base with `dash-501` as a symlink to an empty 0700 victim folder. It made a fallback with `tempfile.mkdtemp(prefix="dash-501-", dir=base)`, wrote a file there, and then probed the note conditions and the identity check:

```
R1 mkdtemp chars: abcdefghijklmnopqrstuvwxyz0123456789_ len 8      # so the fallback regex is ^dash-<uid>-[a-z0-9_]{8}$
R2 planted root: ENOTDIR islink True                                # O_RDONLY|O_DIRECTORY|O_NOFOLLOW on a link to a folder: ENOTDIR on macOS, not ELOOP; classify by lstat
R3 fallback dash-501-nijreyo8 matches True 0o700 own True
R4 file 0o600 victim entries []                                     # O_CREAT|O_EXCL|O_NOFOLLOW in the fallback run folder; nothing reached the link's target
R5 candidates 2 reusable True                                       # a 0755 dash-501-zzzzzzzz beside it is skipped; the 0700 fallback of ours is reused
R6 base 0o775 shared: True                                          # A14: a umask-002 STATATMP is "can be changed by other accounts"
R7 umask 022 fchmod failed (Operation not supported) -> created mode 0o600
R7 umask 002 fchmod failed (Operation not supported) -> created mode 0o600   # a fresh file is 0600 even when fchmod fails
R8 pre-existing 0644 reopened without fchmod: 0o644                 # only a pre-existing file of the user's can stay loose
R9 same file after substitution: False                              # rename the folder, plant a new app.py: (st_dev, st_ino) differs
```

R7 sets the umask inside `try/finally` and raises the ENOTSUP OSError by hand in place of `fchmod`.

**Stata.** Each do-file ran through `scripts/stata_slot.sh <scratch>/wp29r/s08/stata <file>.do`, with `adopath ++` and `global dash_nobrowser 1`.

```
. capture file open `fh' using "`c(tmpdir)'no_such_dir_s08/x.json", write replace text
. display "S1 file open in a missing folder rc=" _rc
S1 file open in a missing folder rc=603                             # Stata's own code for a file it cannot create
. quietly mata: printf("{txt}S2 SHOULD NOT PRINT\n")                # printed nothing
. mata: _dash_say("txt", "dash: note: ", "S3 a{bf:b}", "")
dash: note: S3 a{bf:b}                                              # user text shown literally, not as SMCL
. quietly mata: _dash_say("txt", "dash: note: ", "S4 SHOULD NOT PRINT", "")   # printed nothing
. python: print("P1 {bf:x} {err}y {c 36}")
P1 {bf:x} {err}y {c 36}                                             # Python's print is shown literally, not as SMCL
. quietly python: print("P2 SHOULD NOT PRINT")                      # printed nothing
```

### 3b. Re-measured for the round-2 ratification (01oct2026, scratch `wp29r2/s08`)

The prototype is `<scratch>/wp29r2/s08/boot.py` (the bootstrap text, 1,363 characters, no `"` and no `\`), `proto.py`, `proto2.py`, `proto3.py` and `devfd.py`. The apps are real ones: `dr.ServerAppBuilder(sp, dp).build(<run>/app.py)` at 7421d3d from `test_serve_launcher`'s `_SPEC`/`_DF`, chmod 0600. The interpreter is `/opt/anaconda3/bin/python3` 3.13.9 (bokeh 3.8.0, tornado 6.5.1), which is Stata's `c(python_exec)`. "swap" means: after the verified read, rename the run folder and create a new one at the same path holding an `app.py` that writes `EVIL RAN` to a marker and exits 3. "plant" means `hashlib.py`, `bokeh.py`, `tornado.py`, `linecache.py` and `types.py`, each appending its name to the marker and exiting 4. "path" is today's `[python, app_path, --port P, --timeout 1]`. "boot" is `[python, -P, -c, BOOT, app_path, --port P, --timeout 1]`, followed by the frame on stdin.

```
A_path_swap                  health=None  rc=3 marker='EVIL RAN'   banner=False   # today's launch runs the swapped-in app
B_boot_swap                  health=0.95s rc=0 marker=''           banner=True    # the verified bytes run; the swap is never opened
C_path_rundir_module         health=None  rc=4 marker='linecache ' banner=False   # python app.py imports linecache from the app's folder
D_boot_rundir_module         health=0.95s rc=0 marker=''           banner=True
E_path_cwd_module            health=0.84s rc=0 marker=''           banner=True    # python app.py does not put the working folder on sys.path
F_boot_cwd_module (no -P)    BrokenPipeError; marker 'linecache '                 # python -c imports linecache from the working folder at start-up (3.13)
F_boot_cwd_module (-P)       health=0.94s rc=0 marker=''           banner=True
G_boot_swap_and_plants       health=0.95s rc=0 marker=''           banner=True    # swap plus plants in the run folder and the working folder
```

Under `-P`: `sys.flags.safe_path` was True and `sys.path[0]` was the stdlib zip, on 3.13.9 and on 3.14.5. `linecache` came from the stdlib.

```
1 rc 1 | File ".../w2/tb_app.py", line 4, in f |     raise ValueError('boom in app') | ValueError: boom in app   # traceback: app path, line and text; the file never existed
2 rc 2 | out: __main__ True ['--port', 'x'] | err: usage: argv_app.py [-h] [--port PORT]                       # __name__, __file__ == sys.argv[0], argv, argparse prog
2b SystemExit(130) rc 130
2c uncaught KeyboardInterrupt rc -2 ['KeyboardInterrupt']
3 rc 0 | LINE 43 | EOF after 10 more bytes          # frame, then a 43-byte line read one byte at a time, then a read to EOF: nothing was over-read
4 100MB rc 0 BIG OK write took 0.10s
5 damaged rc 1 b'' b'dash: the app handed over on standard input was damaged'       # SHA-256 mismatch: nothing ran
5b truncated rc 1 b'dash: the app was not handed over on standard input'
6 BrokenPipeError 32                                 # writing to a child that already exited
S1 app file absent before launch; health 0.85s; GET / 200; session roots 1        # proto3: the app unlinked before Popen still serves sessions
S2 rc 0 tracebacks in stderr: 0
D1 offset 5: 1 SyntaxError                           # python /dev/fd/N with pass_fds: macOS shares the offset
D2 offset 0: 0 FD RAN /dev/fd/3 /dev/fd/3            # and __file__/argv[0] read /dev/fd/3
```

**Stata** (`scripts/stata_slot.sh <scratch>/wp29r2/s08/stata inst.do`, `python script inst.py`):

```
c(python_exec)=/opt/anaconda3/bin/python3
ST1 executable /opt/anaconda3/bin/python3 version 3.13.9
ST2 SIGPIPE 1 SIG_IGN is 1                           # Stata's embedded Python ignores SIGPIPE
ST3 child 3.13.9 True rc 0                           # sys.executable -P: same version, safe_path True
ST4 BrokenPipeError errno 32 and Stata is still here
ST5 ran __main__ True True rc 0                      # the bootstrap from inside Stata
STATA ALIVE AFTER
```

### 4. The served lifecycle today

Each probe ran `dash scatter mpg weight` then `capture noisily dash serve, port(free) timeout(2) nobrowser`. A signal was sent once `/health` answered.

- **SIGKILL of Stata** (t3/out.txt):
  ```
  POST: health: 200
  56912     1 /opt/anaconda3/bin/python3 …/t3/tmp//St56911.000003 --port 547…
  -rw-r--r--@ 1 billy  wheel     2490 … St56911.000001        # data JSON
  -rw-r--r--@ 1 billy  wheel      465 … St56911.000002        # spec JSON
  -rw-r--r--@ 1 billy  wheel  1254440 … St56911.000003        # app with _DATA_B64
  ```
  This was re-measured by the u12 review (k1: 'health after: 200', listener ppid 1, the same three files). SIGTERM (t4) gave the same result.
- **SIGINT to the Stata pid** (t5): `POST: health: 000`, no files, and `U12: dash serve returned rc=0`.
  - SIGINT to Stata's whole process group (review g1) also gave rc 0.
  - The app listener's pgid equals Stata's (99003). The child gets the terminal's SIGINT itself, and the app's `except KeyboardInterrupt: pass` (dash_render.py:31725) exits 0.
- **The launcher never polls Stata.** This is p7/probe.py, re-run at 7421d3d in this plan, with a stub sfi whose `pollstd` raises BreakError on call 3:
  ```
  (a) … returned normally after 1.58 s; pollstd calls: 0 ; terminate called: False
  (b) Popen kwargs: ['errors', 'stderr', 'stdout', 'text'] ; stdin kw: None ; cmd flags: ['--port']
  (c) hasattr _dash_watch_parent: False
  ```
- **The code at 7421d3d:**
  ```python
  31992    _cmd = [sys.executable, app_path, "--port", str(port)]
  31999        proc = subprocess.Popen(_cmd, stdout=subprocess.PIPE,
  32000                                stderr=subprocess.PIPE, text=True,
  32001                                errors="replace")
  32069                except Exception:          # around the /health urlopen -- a BreakError would be eaten here
  32079    except KeyboardInterrupt:
  32080        proc.terminate()
  32088    if _stopped_by_launcher or proc.returncode in (
  32089            0, -signal.SIGINT, -signal.SIGTERM):
  32200        except RuntimeError as _exc:       # __main__: report["error"] -> dash.ado exit 198
  ```
- **The app's `__main__`** (31706-31729):
  - it builds `_server = _dash_server_app(…)`;
  - prints the unflushed banner `Bokeh Server running at http://localhost:{_port}/` … `Press Ctrl+C to stop.`;
  - runs `try: _server.io_loop.start() except KeyboardInterrupt: pass finally: _server.stop()`.
- **The messages:**
  - dash.ado:7660-7661: `dash serve: starting Bokeh Server on port N.  Stata is blocked until the server stops (Ctrl+C).`
  - dash_render.py:32066-32068: `…; press Ctrl+C to stop.`
  - dash_render.py:32072-32075: `(Ctrl+C stops it)`.
  - The help says Ctrl+C at dash.sthlp:97, 751-752, 777, 1421-1424 and 1719, and says Stata erases the app at 1574-1578.
- **The fix's prototype** (u12 p6, bokeh 3.9.0, tornado 6.5.5): a daemon thread read stdin to end of file and called `io_loop.add_callback(io_loop.stop)`.
  - After a SIGKILL of the parent, `/health` stopped answering within one 0.1 s poll.
  - A graceful `stdin.close()` gave child rc 0 after 0.08 s.
  - Deleting the app file after `/health` answered left GET / at 200 (a new session) and `/health` at 200.
  - A watch hooked to the wrong loop exited only through the 10 s hard-exit timer (rc 3), so the backstop works.

### 5. Why A9's live filter move is replaced (measured in this plan, scratch `wp29/s08/a9`)

The setup:
1. An app with `scatter` plus `lfit` of mpg on weight and a range filter on weight was launched with `python app.py --port P`.
2. Its file was unlinked once `/health` answered.
3. `pull_session` gave a document with 1 RangeSlider `(1817.0, 4788.0)` and a fit source of 100 points.

Setting `value`, and then `set_from_json("value_throttled", …)` (plain assignment raises "RangeSlider.value_throttled is a readonly property"), and looping `session.force_roundtrip()` for 10 s, gave `changed False in 10.05s`. The fit source was unchanged, and the server printed no error.

The client protocol, not the app, is the obstacle. So the section pins three things instead:
- a new live session after the erase;
- the recompute from source with no file;
- a source guard that the app never reads its own file.

### 6. Tests that pin today's behaviour (flip, never delete)

| Test | Today | Flip (commit) |
|---|---|---|
| `test/test_string_value_export.py::TestDashAdoUsesTheWriter::test_every_entry_point_is_called_by_the_ado_and_no_other` (:550-553) | `called == declared == {"_dash_write_stata_data"}` | The six entry points of TR-08.9 (1) |
| `test/test_immediate_dashboards.py::TestTheDataFileIsTheOneDashAdoWrites::test_dash_ado_writes_this_text` (:209-220) | regex ``file write `fh' `"(.*?)"'`` in `_dash_empty_data` | regex ``local _ed `"(.*?)"'``; still `== _EMPTY_DATA` (1) |
| `test/test_serve_launch.cscript` SRV-19 (:612-672) | app is a tempfile with the session prefix `St<pid>` | app is `<c(tmpdir)>dash-<uid>/run-<pid>-*/app.py`, spec/data beside it, folder gone after (1) |
| `test/test_help_claims_4.cscript` HC4-18 (:476-478) | `strpos(app, c(tmpdir)) == 1`, file gone | kept, plus its run folder gone (1) |
| `test/test_help_claims_4.cscript` HC4-21 (:540-564) | top-level `os.listdir` of `c(tmpdir)` (would pass vacuously) | recursive walk limited to this session's files, plus no `run-<pid>-*` left (1) |
| `test/test_env_guards.cscript` ENV-12 (:509) | `"_dash_do_render _dash_write_data _dash_serve"` | the new list of programs holding `python:` lines, each guarded first (1) |
| `test/test_help_claims_4.py::TestTheRealHandoffServes::test_it_serves_and_stops` (:1366-1426) | `assert os.path.exists(out), "the app was not written"` while serving | paths from `dr._dash_run_open`; app, spec and data gone within 5 s of the first `/health` 200 (F2) |
| `test/test_server_rate_limit.py::TestTheLauncherFlags::test_the_launcher_help_lists_every_flag` (:989-995) | 6 flags + `_NEW_FLAGS` | adds `--parent-watch` (F2) |
| `test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` (:1155-1190) | walks child scopes only | also the top-level scope; `"_dash_watch_parent"` in the tuple (F2) |
| `test/test_serve_launcher.py:_fake_popen_class` (:99-131) and the two inline `_FakeProc`s (:241-312) | `wait(self)`, no `stdin`, no `kill` | commit 1: `self.stdin = _RecStdin()`, which records the bytes the launcher hands over (R-9); F4: `wait(self, timeout=None)`, `stdin.close()` recorded, `kill()` (adjustments, not assertion changes) |
| `test/test_help_claims_2.py::_FakeProc` (:765-790), used by `TestTheLauncherBehindDashServe` | no `stdin` | commit 1: `self.stdin = _RecStdin()` (R-9). Its assertions stay: `--show` and `--timeout 7` are still in the command, after `app_path` (an adjustment) |

These stay green and unchanged:
- HC4-19 (`timeout(1)` gives rc 0) and HC4-20;
- `test_help_claims_1.py::TestServeBlocksUntilCtrlC` and `test_help_claims_5.py` "Serving blocks until interrupted": they assert the server stops, not the exit code;
- `test_serve_browser.cscript` SB-07..SB-10: no new renderer argv flag (R-1);
- `test_help_claims_2.py`'s assertions (`--show`, `--timeout`): only its `_FakeProc` gains a `stdin` (row above);
- `test_server_build_returns.py::TestBuildingDoesNotLaunch::test_no_process_is_left_running`: `pgrep -f <app path>` still matches, because the bootstrap's argv carries the app path;
- `test_help_claims_1.py::TestServeBlocksUntilCtrlC` and `test_help_claims_5.py`'s real launches: they run the renderer's `--launch`, so they now exercise the bootstrap end to end (R-9);
- `test_server.py::TestServeUniqueAppPath` (BUG-47-1b..1d): `build()` defaults to `private=False`; only its docstring changes.

Comment-only updates:
- `test/test_help_claims_4.py:1305-1320`: `TestTheOutputPathRule` stays, because the CLI launch rule is kept;
- `test/test_help_claims_4.cscript:436-437`.

BUGS.md:1579's WP-23 note ("rc 0 within 0.7 s") is history and is not edited.

### 7. Blast radius (grep; GitNexus not indexed)

| Symbol | Callers |
|---|---|
| `main` | 1 (the CLI, dash_render.py:32163) + `dr.main(` in 9 test call sites / 3 files |
| `ServerAppBuilder.build` | 1 (dash_render.py:31936) + `.build(` in 192 test lines / 86 files, all on the `private=False` default |
| `_dash_launch_app` | 1 (32198) + 7 test lines |
| `_dash_write_stata_data` | 1 ado site |
| `_validate_output_path` | 2 |
| `_dash_empty_data` | 2 ado calls, 1 cscript |
| `_dash_write_data` | 2 ado calls, 5 cscripts |
| `_dash_do_render` | 2 ado calls, 9 cscripts |
| `_dash_prepare_spec` | 2 ado calls, 15 cscripts |
| `_dash_serve_spec` | 1 ado call, 13 cscripts |
| `_dash_clear` | 1 ado call, 2 cscripts |

Expected risk: HIGH for `_dash_launch_app` and `main` (index R8); MEDIUM elsewhere.

## User stories

- **US-08.1** As a dashboard publisher on a shared machine, I want every temporary copy of my data that dash writes to be readable only by me, so no other account can read my dataset from `/tmp` while dash runs, or after it crashes.
- **US-08.2** As a dashboard publisher, I want dash to refuse rather than write my data through a link, a FIFO, a hard-linked file or another account's file. I want it never to use a `dash-<uid>` folder someone else planted, and never to run an app that was swapped after dash wrote it. Then a planted name cannot redirect, expose or hijack my data (anti-hijack).
- **US-08.10** As a user whose Stata temporary folder is shared, or sits on a disk that keeps no permissions (a STATATMP made under umask 002, say), I want dash to keep working. I want it to tell me once per command which location is not private and how to fix it, so a setting I may not control does not stop my work (ratified 01oct2026).
- **US-08.3** As a twoway user who previews with the one-line form, I want each preview to be its own private page and the old ones pruned. I want `dash clear` to remove them, so previews neither overwrite a tab I am reading nor pile up copies of my data.
- **US-08.4** As a twoway user, I want pages I name with `saving()` written exactly as twoway's `saving()` and `graph export` write theirs, so dash changes nothing I asked for.
- **US-08.5** As a dashboard publisher, I want a served dashboard to stop when the Stata that started it ends, however it ends, so no orphan keeps serving my data or holding my port.
- **US-08.6** As a dashboard publisher, I want no copy of my data left on disk while `dash serve` runs, so a crash leaves nothing behind.
- **US-08.7** As a GUI Stata user, I want Break to stop `dash serve` and end it with r(1), as it ends every other command, and the messages to tell me to press Break.
- **US-08.8** As the maintainer, I want each of these behaviours pinned by a test that failed before the fix, in both pytest and the certification scripts, so none can return unnoticed.
- **US-08.9** As a dashboard publisher who builds a server app with `dash build, server` to run later, I want the `.py`, which embeds every observation, to be readable and writable only by me. I want `replace` to make a new file and never write through a link, so no other account can read my data from it or redirect it.

## Business requirements

- **BR-08.1** Every file dash writes holding a copy of the data, other than a page the user names with `saving()`, is readable and writable only by the user's account. Each such file in a folder dash chooses sits in a folder only that account can open. This holds whatever the umask, wherever the disk keeps permissions, in every route: the one-line form, `dash build`, `dash build, server` and `dash serve`. It includes the `.py` that `dash build, server` writes to the path the user names (M4, R-7). Where a location cannot be private, BR-08.2a applies.
- **BR-08.2 (anti-hijack; kept, not about privacy)** dash never writes such a copy through a symbolic link, into a FIFO or device, over a file another account owns, or over a file with other hard links. It never writes into a `dash-<uid>` that is a link, not a folder, or another account's. It never starts an app it did not write: it runs the bytes it read through a descriptor it opened and verified (type, owner, `(st_dev, st_ino)`, size and SHA-256), never a path, so a file or folder swapped in after the check cannot change what runs (R-9, ratified 01oct2026 round 2). A refusal names the path and the reason and ends r(7102) (M4a) on every route. The target of a link is never written.
- **BR-08.2a (proceed and note; ratified 01oct2026)** No privacy condition stops a command. Each of these is met by proceeding:
  - a `c(tmpdir)` other accounts can change;
  - a planted `dash-<uid>` (dash uses a fallback root `dash-<uid>-<8 chars>` it makes itself, 0700);
  - a folder dash chose that the disk will not keep at 0700;
  - a file the disk will not keep at 0600.

  dash still creates every file 0600 wherever the disk allows. It prints one note per command, `dash: note: …`, naming each such location and its remedy (R-8). A folder the user names is never refused, re-moded or noted.
- **BR-08.2b** When the operating system will not let dash create its folder at all (c(tmpdir) missing, not a folder, read-only or full), the command ends r(603), with the system's reason, as Stata's own `file open` does there. This is not a refusal.
- **BR-08.3** No such copy outlives its command except:
  - the newest five preview pages of a session, so a browser can still read them;
  - a folder left by an error, Break or crash, which the next dash command of the session, or any later session once its Stata has ended, removes.
- **BR-08.4** The one-line preview never overwrites an earlier preview. `dash clear` removes the session's previews, except one a browser was asked to open in the last minute. Another live session's previews are never removed. Every session's previews together are bounded.
- **BR-08.5** A page the user names (`saving()` of the one-line form and of `dash build`) is written with the user's umask, as twoway's `saving()` and `graph export` are.
- **BR-08.5a** The server app the user names with `dash build, server saving(<file>.py)` is written 0600, whatever the umask (M4, R-7):
  - it is created afresh: an existing file of this account at the name, which `replace` allows, is removed first, and the new file is created exclusively;
  - a symbolic link, a non-regular file or another account's file at the name is refused, and so is a name that reappears before the create (anti-hijack, BR-08.2). The target of a link is never written. The refusal names the path and the reason and ends r(7102), as the renderer's other `--output` refusals do (M4a);
  - the folder the user names is left as it is: it is not refused, re-moded or noted, whoever else can read it (ratified);
  - a `.py` that the disk will not keep at 0600 is written, and the renderer prints one note naming it (R-8 (d));
  - any refusal raised before the app's source is complete (a refused `port()` or `build_options` port, for instance) leaves an existing file at the name untouched.
- **BR-08.6** A server started by `dash serve` stops by itself within the grace period (about 5 s, 10 s with a recompute in flight) once the Stata process that started it ends, by exit, crash, SIGTERM or SIGKILL. This was measured on macOS.
- **BR-08.7** While `dash serve` runs and its server answers, no file holding the data is left on disk. A crash before the server first answers can leave a private copy, which the sweep removes.
- **BR-08.8** Break stops `dash serve` in every front end:
  - the GUI's Break button or menu item, and Command+. on a Mac;
  - Ctrl+C in console Stata;
  - Break before the server is up.

  The server stops, its port is freed, and the command ends with r(1). `timeout()` expiry still ends with rc 0. A server that fails to start still ends with r(198).
- **BR-08.9** Every message and help passage about stopping `dash serve` names Break. Ctrl+C appears only as console Stata's Break key.
- **BR-08.10** The help documents where temporary copies go, their modes, when they are removed, the note for a location that is not private and its remedies, the fallback root, the anti-hijack refusal (r(7102)), the folder failure (r(603)), the residual for a shared `c(tmpdir)` (since round 2: the inputs read by path, not the app), that `dash serve` runs the application text it checked rather than the file by name, that a `.py` the user runs by hand is opened by name and imports from its folder, the umask rule for named pages, the 0600 rule for a named server app (which holds the data), and the hosts that were not measured.

## Technical requirements

### Commit 1 — P0.12b and P0.14: the private root, the writer, the run folder, the previews

**TR-08.1 Constants and the error class (dash_render.py).** These go after `_dash_write_stata_data` (ends 1484), before `_DASH_ADO_ENTRY_POINTS`:
- `_DASH_PREVIEW_KEEP = 5`
- `_DASH_PREVIEW_GRACE_S = 60`
- `_DASH_STALE_AGE_S = 86400`
- `_DASH_PREVIEW_CEILING = 25`
- `_DASH_RUN_RE = re.compile(r"^run-(\d+)-[A-Za-z0-9_]+$")`
- `_DASH_PREVIEW_RE = re.compile(r"^dash-preview-\d{8}-\d{6}-(\d+)-[0-9a-f]{8}-([bq])\.html$")`
- `class _DashUnsafePath(Exception)`, carrying the user-facing message. Its docstring says it is raised only for the anti-hijack refusals of R-8, never for privacy.
- `_dash_root_name()` returns `"dash-%d" % os.getuid()` when `hasattr(os, "getuid")`, else `"dash"`.
- `_DASH_FALLBACK_FMT = r"^%s-[a-z0-9_]{8}$"`, formatted with `re.escape(_dash_root_name())` at the point of use. The 8 characters are `tempfile`'s alphabet (§3a R1).
- `_dash_mode_private(st)` returns True when `os.name == "nt"`, else `stat.S_IMODE(st.st_mode) & 0o077 == 0`.

**TR-08.2 `_dash_private_root(tmpdir, create=True)`** returns `(root, note)`. `note` is `""` or the R-8 sentences, (a) to (c), without the `dash: note: ` prefix. It raises only OSError, which is the operating-system class. It never raises for privacy.
- **The name.** The root is `os.path.join(tmpdir, _dash_root_name())`, with no realpath, abspath or normpath (A2).
- **Base checks (POSIX only).** These add sentence (a) and never raise for privacy.
  - `bst = os.stat(tmpdir)`. This follows links, so the target is what is checked. An OSError propagates; it is the operating-system class.
  - Not a directory: `raise NotADirectoryError(errno.ENOTDIR, os.strerror(errno.ENOTDIR), tmpdir)`, also the operating-system class.
  - `bst.st_uid not in (0, os.getuid())` gives `<why>` = `it belongs to another account`.
  - `bst.st_mode & 0o022 and not bst.st_mode & stat.S_ISVTX` gives `<why>` = `other accounts can write to it and it has no sticky bit`.
- **Creating.** With `create`: `os.mkdir(root, 0o700)`, ignoring FileExistsError. Without it, `return (None, "")` when `not os.path.lexists(root)`.
- **Then** `why = _dash_private_dir_ok(root)`:
  - `""`: the root is used.
  - Non-empty: the root is used and sentence (c) is added.
  - It raises `_DashUnsafePath` for a planted root (link, not a folder, another account's): sentence (b) is added and the root becomes `_dash_fallback_root(tmpdir)` (TR-08.2a). With `create=False` it returns the existing fallback root of the user, or `(None, "")` when there is none.
- **Never** call `os.umask` (process-wide; Stata shares the process).

**TR-08.2a `_dash_fallback_root(tmpdir, create=True)` and `_dash_own_root(path, tmpdir=None)`.**
- **`_dash_fallback_root`.**
  - `pat = re.compile(_DASH_FALLBACK_FMT % re.escape(_dash_root_name()))`.
  - It loops over `sorted(os.listdir(tmpdir))`. It returns `os.path.join(tmpdir, name)` for the first `name` that matches `pat` and whose `os.lstat` is a directory, not a link, owned by the uid (POSIX) and of mode exactly 0700. Anything else that matches is never touched (§3a R5).
  - When none is found and `create` holds: `mk = tempfile.mkdtemp(prefix=_dash_root_name() + "-", dir=tmpdir)`, then `return os.path.join(tmpdir, os.path.basename(mk))` (A2). `mkdtemp` creates with `O_EXCL` semantics and mode 0700, so the name cannot be pre-planted (§3a R3).
  - Otherwise it returns None.
- **`_dash_own_root(path, tmpdir=None)`** returns True only when all of these hold:
  - the basename is `_dash_root_name()` or matches `pat`;
  - `os.lstat(path)` is a directory, not a link, and on POSIX owned by the uid;
  - when `tmpdir` is given, `os.path.dirname(path) == os.path.dirname(os.path.join(tmpdir, "x"))` (the spelling, A2).

  It never raises; an OSError gives False. The sweep, `_dash_run_close`, `_dash_tmp_clear` and `_dash_private_run_of` use it to recognise a root.

**TR-08.3 `_dash_private_dir_ok(path)` and `_dash_private_write(path, text, exclusive=False)`.**
- **`_dash_private_dir_ok` on POSIX** returns `""` or a privacy `<why>`, and raises `_DashUnsafePath` only for the anti-hijack cases:
  - `fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))`.
  - On OSError, classify with `os.lstat` (macOS gives ENOTDIR for a link, not ELOOP: §3a R2). A link gives `it is a link`, and anything else `it is not a folder`. Raise `_DashUnsafePath`.
  - `os.fstat(fd)` must be a directory with `st_uid == os.getuid()`, else raise `_DashUnsafePath` with `it belongs to another account`.
  - If `stat.S_IMODE(st.st_mode) != 0o700`, call `os.fchmod(fd, 0o700)`. An OSError there returns `its permissions could not be set: <strerror>`. Then `os.fstat(fd)` again: group or other bits still set return `its permissions stay 0o<NNN> after dash set them to 0700`.
  - Close the fd in `finally`.
  - On Windows: missing, not `os.path.isdir`, or `os.path.islink` raises `_DashUnsafePath`. Otherwise it returns `""`.
- **The writer** returns `os.fstat(fd)` taken after the write. Callers read `_dash_mode_private(st)` and the identity `(st.st_dev, st.st_ino)` from it.
  - **Open.** `flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0) | (os.O_EXCL if exclusive else 0)`, then `fd = os.open(path, flags, 0o600)`.
  - **Check (anti-hijack).** `st = os.fstat(fd)`:
    - `stat.S_ISREG`, else `it is not a regular file`;
    - on POSIX, `st.st_uid == os.getuid()`, else `it belongs to another account`;
    - `st.st_nlink == 1`, else `it has other links`.

    Each failure raises `_DashUnsafePath`.
  - **Clear `O_NONBLOCK`** with `fcntl.fcntl(fd, F_SETFL, flags & ~O_NONBLOCK)` when `fcntl` imports.
  - **Write.**
    - `os.ftruncate(fd, 0)`;
    - `os.fchmod(fd, 0o600)` when `hasattr(os, "fchmod")`. An OSError from this one call is caught and ignored: privacy class, the file is still written, R-8 (d). A fresh file is 0600 anyway (§3a R7);
    - `data = text.encode("utf-8")`;
    - `with os.fdopen(fd, "wb") as fh: fh.write(data)` (fd ownership moves). `st = os.fstat(fh.fileno())` before the `with` block closes.
  - **Errors.** Any failure before `fdopen` closes the fd. `_DashUnsafePath` (anti-hijack) and every other OSError (operating system) propagate.
- **Messages.** The anti-hijack refusal is `dash: refused to write <path> (<why>); dash never writes through a link, into a pipe or device, or over another account's file.` An OSError is `dash: <path> could not be written: <strerror>.` `<why>` is one of:

  | Condition | `<why>` |
  |---|---|
  | ELOOP | `it is a link` |
  | ENXIO | `it is a pipe` |
  | EEXIST (exclusive create) | `it appeared while dash was writing it` |
  | not `S_ISREG` | `it is not a regular file` |
  | another account's | `it belongs to another account` |
  | `st_nlink != 1` | `it has other links` |

  `_dash_private_msg(exc, path)` builds them: the refusal form for an ELOOP, ENXIO or EEXIST OSError or a `_DashUnsafePath`, and the `could not be written` form for any other OSError. The open's ELOOP, ENXIO and EEXIST are converted to `_DashUnsafePath` inside the writer, so a caller sees one class per kind.

**TR-08.4 `_dash_pid_alive(pid)`.**
- `pid < 1`: return True. It is never signalled (`os.kill(0, …)` would signal the group).
- `os.name == "nt"`: return True. Never call `os.kill` on Windows: CTRL_C_EVENT or TerminateProcess.
- Otherwise `os.kill(pid, 0)`:
  - ProcessLookupError: False;
  - any other OSError, PermissionError included: True;
  - no error: True.

**TR-08.5 The run folder.**
- **`_dash_run_open(tmpdir)`** returns `{"rundir", "spec", "data", "app", "err", "note"}`.
  1. `root, note = _dash_private_root(tmpdir)`. This is the root in use: `dash-<uid>`, or the fallback root.
  2. `_dash_run_sweep(root)`.
  3. `mk = tempfile.mkdtemp(prefix="run-%d-" % os.getpid(), dir=root)` and `rundir = os.path.join(root, os.path.basename(mk))` (A2).
  4. `why = _dash_private_dir_ok(rundir)`. A non-empty `why` adds sentence (c) for the run folder only when `note` holds no sentence (c) for its root.
  5. `spec = join(rundir, "spec.json")`, `data = join(rundir, "data.json")`, `app = join(rundir, "app.py")`.
  6. `note` is returned with the `dash: note: ` prefix when non-empty, and as `""` otherwise.
  - **OSError** (operating-system class): all paths are `""` and `err` = `dash: dash could not make its temporary folder in <tmpdir>: <strerror>.` `note` is still returned. It never raises an OSError.
  - **`_DashUnsafePath`** is not caught. It can only come from a fresh `mkdtemp` folder that failed its owner check, which is anti-hijack, so it ends r(7102) (R-8).
- **`_dash_run_sweep(root, now=None)`** returns the count removed. For each name in `os.listdir(root)` matching `_DASH_RUN_RE`:
  - pid = group 1; `lst = os.lstat(path)`.
  - **Remove when:**
    - `pid == os.getpid()`. No dash command of this process can be running: Stata is single-threaded and `dash serve` blocks.
    - On POSIX, `not _dash_pid_alive(pid)`.
    - On Windows only, `now - lst.st_mtime > _DASH_STALE_AGE_S`.
  - **Never** remove a live POSIX pid's folder by age (A5).
  - **How:** a link or non-folder of that name is `os.unlink`ed, never followed. A folder goes through `shutil.rmtree(path, ignore_errors=True)` (`rmtree.avoids_symlink_attacks` is True on this host).
  - Any OSError is ignored. The sweep never fails a render.
- **`_dash_run_close(rundir, tmpdir)`** returns `""` or text.
  - `""` when `rundir == ""`.
  - It returns `dash: <rundir> is not a dash run folder; nothing was removed.` when `not _dash_own_root(os.path.dirname(rundir), tmpdir)` (`dash-<uid>` or a fallback root of the user's, TR-08.2a), or when the basename does not match `_DASH_RUN_RE`.
  - `""` when `not os.path.lexists(rundir)`: the folder may already be gone.
  - A link is unlinked. Otherwise `shutil.rmtree(rundir, ignore_errors=True)`.
  - When the root is a fallback root, `os.rmdir(root)` follows, with every OSError ignored. It removes only an empty folder, so a kept preview keeps its fallback root.
  - It returns `""`.

**TR-08.6 `_dash_erase_quietly(path)` and `_dash_private_run_of(output_path)`.**
- **`_dash_erase_quietly`:** `os.unlink(path)`, ignoring every OSError. unlink removes a link, not its target, and never removes a directory.
- **`_dash_private_run_of`** returns the run folder or None (A10). The output path qualifies only when:
  - `basename(output_path) == "app.py"`;
  - `rundir = dirname(output_path)` has a basename matching `_DASH_RUN_RE`;
  - `root = dirname(rundir)` satisfies `_dash_own_root(root)`. Its basename is `_dash_root_name()` (`dash-<getuid>`, or `dash` on Windows) or a fallback root's name (TR-08.2a, ratified 01oct2026);
  - both `os.lstat(root)` and `os.lstat(rundir)` show a directory, not a link, owned by `getuid()`, with `S_IMODE & 0o077 == 0` (POSIX). The mode clause is R-1's as ratified. On a disk that keeps no permissions it fails, so nothing is erased early, and `_dash_tmp_close` removes the folder when the command ends (R-8 residual; that location is already in the command's note).

  It reads only the filesystem, so it holds under `runpy.run_path(…, run_name="__main__")`.

**TR-08.6a `_dash_private_clear_name(path)`** (R-7; anti-hijack) returns None or raises `_DashUnsafePath` carrying TR-08.3's refusal, `dash: refused to write <path> (<why>); dash never writes through a link, into a pipe or device, or over another account's file.` It makes room for an exclusive create at a path the user names. It never looks at the mode of the path's folder (ratified: a folder the user names is never refused).
- `not os.path.lexists(path)`: return. Nothing is created.
- `st = os.lstat(path)`. It never follows a link.
  - `stat.S_ISLNK`: refuse, `it is a link`. The link and its target are both left.
  - not `stat.S_ISREG` (a folder, a FIFO, a device): refuse, `it is not a regular file`.
  - On POSIX, `st.st_uid != os.getuid()`: refuse, `it belongs to another account`.
- Otherwise `os.unlink(path)`. OSError propagates.
- A file or link planted at the name after the unlink makes the following `O_EXCL` create fail with EEXIST (`it appeared while dash was writing it`), so a race ends in a refusal, never in a write through a planted name.
- It is called only by `ServerAppBuilder.build(private=True)`, right before the write.

**TR-08.7 Previews.**
- **`_dash_preview_path(tmpdir, opened)`** returns `{"path", "err", "note"}`, with `err` and `note` built as `_dash_run_open` builds them (OSError → `err`; `note` prefixed `dash: note: `).
  1. `root, note = _dash_private_root(tmpdir)`.
  2. `prev = join(root, "previews")`; `os.mkdir(prev, 0o700)` (ignore exists); `why = _dash_private_dir_ok(prev)`, which adds sentence (c) only when the root's did not.
     - On `_DashUnsafePath` (a `previews` planted inside the root, which needs a root others can write): do not touch it. Set `root = _dash_fallback_root(tmpdir)`, add sentence (b) naming `prev`, and repeat step 2 once in the fallback root. A second `_DashUnsafePath` propagates (anti-hijack, r(7102)).
  3. `_dash_prune_previews(prev, "preview")`.
  4. The name is `"dash-preview-%s-%d-%s-%s.html" % (time.strftime("%Y%m%d-%H%M%S"), os.getpid(), secrets.token_hex(4), "b" if str(opened).strip() == "1" else "q")`.
  - The file is not created here: `main(private_output=True)` creates it with `exclusive=True`.
- **`_dash_prune_previews(prev, trigger, now=None)`** returns the count removed.
  - **Entries:** names matching `_DASH_PREVIEW_RE` whose `lstat` is a regular file. Anything else, including a link, is never touched.
  - **mine** = pid group equals `os.getpid()`, sorted by `(mtime, name)`, newest first. **young** = `now - mtime < _DASH_PREVIEW_GRACE_S`.
  - **`"preview"` trigger:** among mine, keep the newest `_DASH_PREVIEW_KEEP - 1` (so at most five once the new page is written). Of the rest, drop every `q` page and every `b` page that is not young.
  - **`"clear"` trigger:** drop every page of mine except young `b` pages.
  - **Other pids, both triggers:** drop when `now - mtime > _DASH_STALE_AGE_S`, or on POSIX when `not _dash_pid_alive(pid)` (A6).
  - **Ceiling:** if more than `_DASH_PREVIEW_CEILING` pages remain, drop the oldest beyond it, skipping young `b` pages.
  - Unlink with every OSError ignored.

**TR-08.8 `main()`, `ServerAppBuilder.build`, the CLI.**
- **`ServerAppBuilder.build(self, output_path, port=5006, private=False)`** (29088). When `private`, the write (29182-29183) becomes, after `source` is complete (so a port refusal or any earlier raise leaves an existing file untouched): `_dash_private_clear_name(output_path)`, then `st = _dash_private_write(output_path, source, exclusive=True)`, and `return _DashWrittenApp(st, hashlib.sha256(source.encode("utf-8")).hexdigest())` (round 2; the writer encodes the same text as UTF-8, TR-08.3). In a fresh run folder the clear finds nothing. Otherwise it uses `open(…, "w")` and returns None, unchanged for the 86 test files that call `.build(` directly. Today it returns None, so no caller reads the value.
- **`_DashWrittenApp`** (round 2) is `collections.namedtuple("_DashWrittenApp", ["st", "sha256"])`, beside `_DashUnsafePath` (TR-08.1). `st` is the writer's `os.stat_result` and `sha256` the hex digest of the bytes written. `import collections` and `import hashlib` go at module top if absent (at 7421d3d neither is imported at module level).
- **`_dash_chosen_path(path)`** is pure: it reads names only and never touches the filesystem. It is True when `basename(dirname(path))` matches `_DASH_RUN_RE` or equals `"previews"`, and `basename(dirname(dirname(path)))` is `_dash_root_name()` or matches the fallback pattern. The renderer prints the R-8 (d) note only when this is False.
- **`main(master_spec_path, data_json_path, output_path, mode="standalone", port=5006, launch=False, private_output=False)`** (31888):
  1. After `_validate_output_path(…)`: `run = _dash_private_run_of(output_path) if launch else None`.
  2. **Server mode:** `written = builder.build(output_path, port=_dash_port_value(port), private=True)` on every server route: `dash serve`'s launch, `dash build, server` and the command line (M4, R-7). No flag is needed, so `_dash_build` and PF-06's `--private-output` expectation are unchanged.
     - Then, if `run` is set and `dirname(master_spec_path) == run == dirname(data_json_path)` with the basenames `spec.json` and `data.json`, `_dash_erase_quietly` both.
     - The app embeds them (`_SPEC_B64`/`_DATA_B64`).
     - When `not _dash_mode_private(written.st) and not _dash_chosen_path(output_path)`, it prints the R-8 (d) note once with `print(…, flush=True)`. That is the user's `.py` on a disk that keeps no permissions.
     - `return written`. `main` returns None in standalone mode, as today.
     - A `_DashUnsafePath` from the build is not caught: under Stata it ends r(7102) with the message as the traceback's last line (M4a). It is never turned into a SystemExit, which Stata reports as rc 0 (M4b).
  3. **Standalone mode:** `_dash_private_write(output_path, html, exclusive=True)` when `private_output`. The preview's folder is `previews/`, so `_dash_chosen_path` holds and no note is printed. Otherwise `open(…, "w")`, unchanged: twoway's umask semantics for user-named pages (T4, D6).
  - Docstring: every server app is written 0600 where the disk allows and never through a link (M4, anti-hijack); `private_output` makes the standalone page private; inputs are erased only inside a validated run folder; the return value is the written app's `_DashWrittenApp` (its `os.stat_result` and SHA-256), which the launcher verifies before it hands the bytes to Python (TR-08.8a).
- **The launch identity check (anti-hijack, R-8)** is replaced by TR-08.8a (round 2). `_dash_launch_app` gains the keyword `expect=None` as before, and `__main__` passes `expect=_written`. The existing calls and tests pass no `expect` and keep working: the file is still opened without following a link and checked for type and owner, and only the identity, size and digest comparisons are skipped.
- **`_validate_output_path`** (31794-31815): docstring only. `dash serve` now hands `<c(tmpdir)>dash-<uid>/run-<pid>-<x>/app.py`. The extension-less launch rule is kept for command-line users, and `TestTheOutputPathRule` stays.
- **`__main__`** (32111ff): `parser.add_argument("--private-output", dest="private_output", action="store_true", default=False, help="Write the output readable by this account only (0600) and never through a link.  dash.ado passes this for the one-line form's preview page.")` and pass `private_output=args.private_output` to `main`. Keep `main`'s result as `_written = main(…)`. The launch block passes `expect=_written` to `_dash_launch_app`.

**TR-08.8a Launch from the open file (anti-hijack; ratified 01oct2026, round 2, answer B; R-9).** Launcher-only module-level names sit beside `_dash_launch_app`. None is copied into the app (R-3), and each docstring names the threat (U2, §3b A and C), its R-8 class (anti-hijack) and the measurement (§3b).
- **`_DASH_BOOT`** is a module constant: the bootstrap text run by `python -P -c`. It is §3b's `boot.py` text, with its messages as given here. In order:
  1. `import sys`. A guard: when `not getattr(sys.flags, "safe_path", False)` and `sys.path[:1] == [""]`, `del sys.path[0]`. That is a second line of defence: `-P` already keeps `''` off the path.
  2. `def _dash_boot():`, with local `import os, hashlib, linecache, types, builtins`.
  3. Read the header with `os.read(0, 1)` until a newline, at most 128 bytes. It must be three ASCII fields: `DASHAPP1`, a decimal *n* and a 64-hex digest.
  4. Read exactly *n* bytes with `os.read(0, min(left, 1048576))`. Never touch `sys.stdin`.
  5. Compare `hashlib.sha256(data).hexdigest()` with the digest.
  6. `src = data.decode("utf-8")`; `code = compile(src, app, "exec", dont_inherit=True)`, where `app = sys.argv[1]`.
  7. `linecache.cache[app] = (len(src), None, src.splitlines(True), app)`. An mtime of None is never checked, so tracebacks show the handed-over text even after the file is erased or swapped.
  8. `mod = types.ModuleType("__main__")`; `mod.__file__ = app`; `mod.__builtins__ = builtins`; keep a reference to the old `sys.modules["__main__"]` for the life of the call, then `sys.modules["__main__"] = mod`; `sys.argv = sys.argv[1:]`; `del data, src`; `exec(code, mod.__dict__)`.
  9. Then `_dash_boot()`.

  A short, missing or malformed frame raises `SystemExit("dash: the app was not handed over on standard input")`, and a digest mismatch `SystemExit("dash: the app handed over on standard input was damaged")`. Both exit 1 and run nothing (§3b 5, 5b). The text holds no `"` and no `\` (asserted at import: `assert '"' not in _DASH_BOOT and "\\" not in _DASH_BOOT`), so `subprocess.list2cmdline` only wraps it in double quotes (Windows). It holds no secret: argv is visible to other local accounts through `ps`.
- **`_dash_read_verified_app(app_path, expect=None)`** returns the app's bytes, or raises `_DashUnsafePath` or OSError.
  1. On Windows (`os.name == "nt"`): `lst = os.lstat(app_path)`. If `stat.S_ISLNK(lst.st_mode)` or `getattr(lst, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)`, refuse with `it is a link`.
  2. `fd = os.open(app_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_BINARY", 0))`. An ELOOP, or an ENOTDIR or EMLINK that `os.lstat` shows to be a link, refuses with `it is a link`. Any other OSError propagates.
  3. Inside `try/finally: os.close(fd)`, `st = os.fstat(fd)`:
     - `not stat.S_ISREG(st.st_mode)` refuses with `it is not a regular file`; a FIFO opened `O_NONBLOCK` for reading does not block (A3);
     - where `os.getuid` exists (read as `getattr(os, "getuid", None)`; Windows has none, A13), `st.st_uid != os.getuid()` refuses with `it belongs to another account`. A bare `os.getuid()` is an AttributeError on Windows; `test_the_verified_read_works_without_O_NOFOLLOW_and_getuid` pins this;
     - with `expect`, `(st.st_dev, st.st_ino) != (expect.st.st_dev, expect.st.st_ino)` refuses with `it was replaced after dash wrote it`, and `st.st_size != expect.st.st_size` with `it changed after dash wrote it`;
     - read `st.st_size` bytes in a loop of `os.read(fd, min(left, 1 << 20))`. An early end of file, or a further `os.read(fd, 1)` that returns bytes, refuses with `it changed after dash wrote it`.
  4. With `expect`, `hashlib.sha256(data).hexdigest() != expect.sha256` refuses with `it changed after dash wrote it`.
  - Every refusal is `_DashUnsafePath("dash: refused to run %s (%s); dash runs only the application it wrote." % (app_path, why))`.
  - It never reads the path a second time. Every check after the open is on the descriptor (§3a R9, §3b B).
- **`_dash_app_frame(data)`** is pure: `("DASHAPP1 %d %s\n" % (len(data), hashlib.sha256(data).hexdigest())).encode("ascii") + data`.
- **`_dash_child_stdin(proc)`** returns the binary writer of the child's stdin: `getattr(proc.stdin, "buffer", proc.stdin)`. The launcher's Popen stays `text=True`, because the pump threads read text. Every write to the child's stdin goes through this binary writer and is bytes: S08's frame here, and S13's key line (Notes for S13). The text wrapper is never written to. That avoids its locale encoding (on Windows not UTF-8) and its newline translation (`\n` to `\r\n` on Windows), either of which would break the frame. A fake child's stdin that has no `buffer` is used as it is.
- **`_dash_hand_over(proc, frame)`**: `raw = _dash_child_stdin(proc)`; `raw.write(frame)`; `raw.flush()`. It never closes the pipe.
- **In `_dash_launch_app`** (31944), commit 1:
  1. After the prebind and before Popen: `data = _dash_read_verified_app(app_path, expect)`; `frame = _dash_app_frame(data)`; `del data`. An OSError raises `RuntimeError("no server started on port %d: the app could not be read (%s)" % (port, exc.strerror or exc))`. `_DashUnsafePath` propagates (r(7102)).
  2. `_cmd = [sys.executable, "-P", "-c", _DASH_BOOT, app_path, "--port", str(port)]`, then `--show` and `--timeout` as today. This replaces `[sys.executable, app_path, "--port", str(port)]` (31992).
  3. Popen gains `stdin=subprocess.PIPE`. It still gets no `start_new_session`/`process_group` (A5a; F2 pins it).
  4. Right after the two pump threads start (so a child that writes while it reads cannot fill a pipe), the hand-over runs in a try:
     - `try: _dash_hand_over(proc, frame)`;
     - on `BaseException`: if `proc.poll() is None`, `proc.kill()`; then `proc.wait()`, `_t_err.join(1)`, `proc.stdin.close()` (errors ignored);
     - an OSError, ValueError or AttributeError then raises `RuntimeError("no server started on port %d: the app could not be handed to Python (%s)" % (port, exc))` plus the stderr tail, cut as today, and anything else (a `KeyboardInterrupt`, say) is re-raised;
     - then `del frame`.

     A BrokenPipeError from a child that exited first is caught (§3b 6). Stata's Python ignores SIGPIPE, so Stata is not killed (§3b ST2, ST4).
  5. After the final `proc.wait()`, `proc.stdin.close()` with errors ignored. The pipe is not leaked into Stata's process.
  - F2 (TR-08.14) adds `--parent-watch` to `_cmd`. F4 (TR-08.17) moves item 4 inside its single try/finally as the first statement after the pumps start. The finally's `_dash_stop_child` then replaces item 4's own stop, and a second Break during the hand-over goes to kill (A4).
- **No other route starts the app.** At 7421d3d, `grep -n "subprocess.Popen(" dash_render.py` prints only 31999, and `dash.ado` runs no Python process (its one shell call opens a page). After commit 1, `grep -n "sys.executable, app_path" dash_render.py` prints nothing (AC-08.4b).

**TR-08.9 The ado entry points.**
- **`_dash_tmp_write_text(path, text)`** calls `_dash_private_write(path, text)` and returns `""`. It never returns a refusal as text (ratified 01oct2026). A `_DashUnsafePath` (anti-hijack) or another OSError propagates out of the `python:` line, which ends r(7102) with the message as the traceback's last line (M4a). A loose mode is the privacy class: the file is written, and the command's note names its folder (R-8 (d)).
- **`_dash_tmp_clear(tmpdir)`** returns `""` or text. It works on each root of the user's in turn: `dash-<uid>` when `_dash_own_root` accepts it, and every fallback root that `_dash_own_root` accepts (TR-08.2a). It never creates a root, and it returns `""` when there is none. For each root:
  1. `_dash_run_sweep(root)`;
  2. if `previews` exists and `_dash_private_dir_ok` does not raise, `_dash_prune_previews(prev, "clear")`. A planted `previews` is skipped, never followed;
  3. for a fallback root, `os.rmdir(prev)` and `os.rmdir(root)`, each with OSError ignored. Only empty folders go.

`_DASH_ADO_ENTRY_POINTS = (_dash_write_stata_data, _dash_run_open, _dash_run_close, _dash_preview_path, _dash_tmp_write_text, _dash_tmp_clear)`. `_dash_write_stata_data`'s final write (1482-1483) becomes:

```python
    _dash_private_write(path, text)
    return ""
```

Nothing is caught there. An anti-hijack refusal or an OSError leaves the `python:` line of `_dash_write_data` as an exception. That gives r(7102), as an `open()` failure does at 7421d3d, and `_dash_plot`'s `capture noisily _dash_write_data …` / `` if `_dash_jrc' exit `_dash_jrc' `` passes the code through. The old "cannot be written privately, r(198)" branch is not added (ratified). `_dash_write_data`'s `exit 198` stays for the refusals it already makes, such as a binary strL.

**TR-08.10 dash.ado.** No `python:` line is reached before a direct `_dash_require_python` command in its program (A7, ENV-12). Every new `python:` line is an import, an assignment or `_dash_M.setLocal(` (A11). Every path and text crosses by value through `Macro.getLocal`/`setLocal` (no backtick or `$` on a `python:` line).

1. **`_dash_xm_load`** (new, placed after `_dash_write_data`).
   - It begins with `_dash_require_python`.
   - It moves the locator and module loader verbatim out of `_dash_write_data` (4315-4350): the copy beside dash.ado first, then `_dash_find_render`, keyed by realpath, size and mtime into `sys.modules["_dash_render_export"]`.
   - `_dash_write_data` keeps `_dash_require_python` (4314), then calls `_dash_xm_load`, then `python: import sys` / `python: from sfi import Macro as _dash_M` / `python: _dash_xm = sys.modules["_dash_render_export"]`, then its `setLocal("_dw_err", …)` line, still reading `getLocal("_dw_path")` and `getLocal("_dw_vars")`.
2. **New programs, each re-binding** `sys`, `_dash_M` and `_dash_xm` in its own `python:` lines (names at do-file level were not visible inside a program, m1):
   - `_dash_tmp_open` (rclass). `_dash_require_python`; `_dash_xm_load`; `` local _to_tmp `"`c(tmpdir)'"' ``; `python: _dash_to = _dash_xm._dash_run_open(_dash_M.getLocal("_to_tmp"))`; one `setLocal` each for `_to_err`, `_to_note`, `_to_dir`, `_to_spec`, `_to_data`, `_to_app`.
     - A non-empty `_to_note` gives `mata: _dash_say("txt", "", st_local("_to_note"), "")`, printed first (the privacy class; never an error, R-8).
     - A non-empty `_to_err` gives `mata: _dash_say("err", "", st_local("_to_err"), "")` and `exit 603`. Its comment says this is the operating-system class (the folder could not be made at all; Stata's own `file open` gives 603 there, §3a S1) and never a privacy refusal.
     - Otherwise it returns locals `rundir`, `spec`, `data`, `app`, and `noted` (`"1"` when a note was printed, else `""`).
   - `_dash_tmp_preview, OPENED(string) [NOTED(string)]` (rclass). The same pattern with `_dash_preview_path(…, _dash_M.getLocal("opened"))`. It prints `_tp_note` only `` if "`noted'" != "1" `` (one note per command), returns `path`, and exits 603 only on `_tp_err`.
   - `_dash_tmp_close, DIR(string)`. `_dash_require_python`; `_dash_xm_load`; `` local _tc_tmp `"`c(tmpdir)'"' ``; `_dash_run_close(getLocal("dir"), getLocal("_tc_tmp"))` into `_tc_err`. A non-empty text is shown as a note (`_dash_say("txt", …)`) and never changes the return code.
   - `_dash_tmp_clear`.
     1. `_dash_require_python`.
     2. `mata: st_local("_tcl_has", strofreal(rows(dir(c("tmpdir"), "dirs", "dash*")) > 0))`, with `exit` when it is not `1` (A15: no Python runs, no module loads, when there is no root).
     3. `_dash_xm_load`, then `` local _tcl_tmp `"`c(tmpdir)'"' ``, then the three re-binding lines.
     4. `python: _dash_tcl = _dash_xm._dash_tmp_clear(_dash_M.getLocal("_tcl_tmp"))`.
3. **`_dash_empty_data`** (4276-4284).
   - It begins with `_dash_require_python` and `_dash_xm_load`.
   - The text moves to ``local _ed `"{"values":[],"variableIsString":{},"variableNames":[],"variableLabels":{},"valueLabelNames":{},"valueLabels":{},"numberOfRecords":0,"numberOfVariables":0}"'``.
   - Then `python: _dash_ed = _dash_xm._dash_tmp_write_text(_dash_M.getLocal("path"), _dash_M.getLocal("_ed") + chr(10))`, keeping the trailing newline (A8). It is an assignment (A11).
   - There is no error branch. An anti-hijack refusal or an OSError ends the `python:` line with r(7102) (R-8).
4. **`_dash_plot`.**
   - **The preview.** 5955-5963 change. The `else` branch holds only `local _dash_preview 1` and `local open_browser = 1`, with no `tempfile`. The `.html` suffix check that follows runs only `` if "`_dash_preview'" != "1" ``.
   - **Opening the run.** Delete `tempfile data_json_path spec_json_path` (6038). Directly after `_dash_formats_json … _dash_date_vars` (6088), so every limit refusal before it leaves nothing:
     ```
     _dash_tmp_open
     local _dash_run      `"`r(rundir)'"'
     local spec_json_path `"`r(spec)'"'
     local data_json_path `"`r(data)'"'
     local _dash_noted    `"`r(noted)'"'
     ```
   - **The two error exits.** `` if `_dash_jrc' exit `_dash_jrc' `` (6121) becomes a block that runs `` _dash_tmp_close, dir(`"`_dash_run'"') `` on its own line, then `` exit `_dash_jrc' ``. The "data could not be written" branch (6125-6129) gets the same close before its `exit(198)`.
   - **The spec write (6140-6145)** becomes: `_dash_require_python`, the three re-binding lines, then `python: _dash_wsp = _dash_xm._dash_tmp_write_text(_dash_M.getLocal("spec_json_path"), _dash_M.getLocal("master_json"))`. There is no error branch: a refusal or an OSError ends r(7102), and the run folder it leaves is swept later (Notes, "Error-path cleanup").
   - **Naming the preview.** Before `_dash_do_render`: `` if "`_dash_preview'" == "1" ``, then `` _dash_browser_wanted, spec(`"`json_spec'"') `` (pure, dash.ado:5179-5187); `local open_browser = r(open)`; `` _dash_tmp_preview, opened(`open_browser') noted(`_dash_noted') ``; `` local saving_path `"`r(path)'"' ``; `local _dash_priv "private"`.
   - **The render.** `` _dash_do_render, … `_dash_priv' ``, then `` _dash_tmp_close, dir(`"`_dash_run'"') ``. Delete the later `_dash_browser_wanted` call (6166-6169). The open/announce branch (6170-6178) is unchanged.
5. **`_dash_do_render`** (394) takes `[MODE(string) PRIVate]`. With `private`, add `python: sys.argv.append("--private-output")` after the argv line (425).
6. **`_dash_prepare_spec`** (7283-7288). The spec write becomes the same `_dash_require_python` / re-bind / `python: _dash_wsp = _dash_xm._dash_tmp_write_text(_dash_M.getLocal("specpath"), _dash_M.getLocal("master_json"))` lines, with no error branch (r(7102) on a refusal or an OSError). It is called directly by test seams with their own tempfiles, so it opens no run and prints no note.
7. **`_dash_build`.** Replace `tempfile data_json_path master_json_path` (7395) with `_dash_tmp_open` plus three locals: `_dash_run`, `master_json_path` from `r(spec)`, `data_json_path` from `r(data)`. `_dash_tmp_open` prints the command's note. A `server saving(<file>.py)` on a disk that keeps no permissions gets the renderer's (d) line as well (R-8). Add `_dash_tmp_close, dir(…)` right after `_dash_do_render` (7449-7450). No new `python:` line is added here, so ENV-12's list does not gain `_dash_build`.
8. **`_dash_serve`.**
   - Replace `tempfile data_json_path master_json_path` (7598) with `_dash_tmp_open` and four locals (`_dash_run`, `master_json_path`, `data_json_path`, `serve_app_path` from `r(app)`), before `_dash_serve_spec` (A12). The command's note prints here, before the `starting Bokeh Server` announcement, and is the served route's only note.
   - Delete `tempfile serve_app_path` (7652) and rewrite its comment (7640-7651): the app is `app.py` in the private run folder; `main()` erases spec and data once it is written; dash removes the folder.
   - In the `_srv_err` branch (7691-7694), close before `exit 198`.
   - Close at the end.
9. **`_dash_clear`** (6185-6228). `capture _dash_tmp_clear` before `display as text "dash: registry cleared."`. Its message is unchanged, and so is its behaviour with no Python (the guard's r(198) is captured).

**TR-08.11 Help (dash.sthlp).**
- **New section.** Add `{viewerjumpto "Temporary files"   "dash##tempfiles"}{...}` after the Server Mode jump line (14). Add a new section `{marker tempfiles}{...}` / `{title:Temporary files and privacy}` directly above `{marker limits}` (1581), so `test_toolbar.py:753`'s server_mode-to-limits slice keeps its table. It has six paragraphs:
  1. **Run folders.** Each render's spec and data go into `{cmd:c(tmpdir)}{cmd:dash-}{it:uid}{cmd:/run-}{it:pid}{cmd:-}{it:random}`, which only you can open (0700), with files readable only by you (0600). dash removes it when the command ends. A folder left by an error, Break, crash or killed Stata is removed by the next dash command of that session, or of any session once that Stata has ended (on Windows, after a day).
  2. **`dash serve`.** It writes its application there and erases the specification and data once the application is written. The F2 commit adds: "and the application once the server answers, so no copy of the data stays on disk while the server runs".
  3. **Previews.** Pages go to `…/previews/` under unique names, readable only by you. The newest five of a session are kept. `{cmd:dash clear}` removes the session's pages except one a browser was asked to open in the last minute.
  4. **When a location is not private (ratified 01oct2026).** This paragraph has three parts.
     - **The note.** dash never stops a command for privacy. Three cases are covered: a `{cmd:c(tmpdir)}` other accounts can change (writable by others with no sticky bit, as a `STATATMP` folder made under umask 002 is, or another account's); a `dash-`*uid* that is a link, not a folder or another account's; and a folder the disk will not keep private. In each, dash goes on. It writes each file readable only by you wherever the disk allows and prints one note per command, beginning `dash: note:`, that names the location and the remedy (`chmod go-w`, or `STATATMP` set to a folder only you can write). A `dash-`*uid* dash cannot use is left alone: dash keeps its copies in a folder `dash-`*uid*`-`*xxxxxxxx* beside it that only you can open, and the note names both. Under `{cmd:quietly}` the note is not shown, like dash's other notes. Only `{cmd:c(tmpdir)}` itself is checked, not the folders above it. In a `{cmd:c(tmpdir)}` others can write without a sticky bit, another account could move dash's folders, though not read the files in them. It cannot change what `{cmd:dash serve}` runs: dash does not start its application by name. It opens the file it wrote, checks that it is that file with the same contents, and hands the text to Python itself, so a file swapped in afterwards is never run, and no module beside it or in your working folder is imported (round 2; measured on macOS, Linux and Windows have not been measured).
     - **The anti-hijack guard.** This guard stops a planted name and does not depend on privacy. dash never writes through a symbolic link, into a pipe or device, over a file with other hard links or over another account's file, and never runs an application other than the one it wrote. In each case it stops with r(7102) and names the path.
     - **Folder failure.** If dash cannot create its folder at all (`{cmd:c(tmpdir)}` missing, read-only or full), it stops with r(603), as Stata's own file commands do.
  5. **Named files.** A page you name with `saving()` is written with your umask, as twoway's `saving()` and `graph export` write theirs (usually 0644). It embeds the data. The server app you name with `{cmd:dash build, server saving(}{it:file}{cmd:.py)}` also embeds every observation, so it is written readable only by you (0600), whatever your umask. If your disk does not keep that permission, dash still writes the file and prints a note naming it. `{cmd:replace}` writes a new file rather than rewriting the old one. As a guard against a planted name, dash refuses, r(7102), a symbolic link or another account's file at that name, and never writes to a link's target. The folder you name keeps its own permissions. dash neither refuses nor notes a folder of yours that others can read; choose one other accounts cannot list if the file's name is itself private.
  6. **Stata's own files and Windows.** Stata's own temporary files (a `preserve` larger than `max_preservemem`, for instance) follow your umask. On Windows, privacy rests on your per-user TEMP folder, which has not been tested.
- **Edits elsewhere:**
  - 806-813 (`dash clear`): it also removes the session's preview pages; link to the section.
  - 863-869 (nobrowser): "writes its dashboard to a page in `{cmd:c(tmpdir)}{cmd:dash-}{it:uid}{cmd:/previews/}`"; link.
  - 1364-1366: "writes the application into a private temporary folder (see …)".
  - 1434-1436 ("Running the generated .py file independently"): after "every observation of the variables the dashboard uses.", add "dash writes it readable only by you (0600); see {help dash##tempfiles:Temporary files and privacy}." (R-7). Then add (round 2, R-9): "When you run the file yourself, with {cmd:python} or {cmd:bokeh serve}, Python opens it by its name and imports modules from the folder that holds it, so keep it in a folder only you can write. {cmd:dash serve} does not run its own copy that way: it hands Python the text it wrote and checked."
  - 1424: "Stata erases its temporary copy of the application" becomes "dash removes its temporary folder".
  - 1468, the Security paragraph: add the sentence `The files {cmd:dash serve} writes are readable only by you wherever your disk keeps permissions, and dash notes any location where they are not; see {help dash##tempfiles:Temporary files and privacy}.` as its own sentence at the paragraph's end. S13 later rewrites the "only this machine" sentence and keeps this one (R3).
  - 1575-1578: "`{cmd:dash serve}` writes its copy into a folder only you can open and removes it when the command ends", and "a file you name with `{cmd:saving()}` is written readable only by you (0600) and is yours to manage" (R-7).

### Commit 2 — P0.13 F2: the server dies with Stata; no copy on disk while it serves

**TR-08.12 `_dash_watch_parent(io_loop, fd=None, grace=5.0, _exit=None)`** is module-level, beside `_dash_port_value` (31866). Its imports (`os`, `sys`, `threading`) are local.
- **No stdin.** If `fd is None`: `sys.stdin is None` or `fileno()` raising gives one printed line, `dash: no standard input to watch; the server will not stop with the program that started it.`, and `return None`.
- **The thread target `_watch`** loops `while True: b = os.read(fd, 4096); if not b: break`, breaking on OSError too. Bytes are discarded and never kept. Then:
  - `io_loop.add_callback(io_loop.stop)`, Tornado's one thread-safe IOLoop call;
  - `t = threading.Timer(grace, _exit or os._exit, (0,)); t.daemon = True; t.start()`, a hard backstop for a loop stuck in a recompute.
- **The thread itself** is daemon `threading.Thread(target=_watch, name="dash-parent-watch", daemon=True)`. It is started and returned.
- **Copy list.** Add `"_dash_watch_parent"` to `ServerAppBuilder`'s functions tuple after `"_dash_port_value"` (28829), with a comment naming F2.

**TR-08.13 The emitted app** (`_dash_arg_parser` 29787-29824; `__main__` 31662-31730).
- **The flag.** Add `p.add_argument('--parent-watch', action='store_true', dest='parent_watch', help='Stop when standard input reaches end of file.  dash serve passes this so the server ends with the Stata session that started it; started by hand, the server stops on Ctrl+D.')`.
- **The watch call.** After `_server = _dash_server_app(…)` (31706-31707): `if _a.parent_watch: _dash_watch_parent(_server.io_loop)`.
- **The banner.** Every banner `print` gets `flush=True`. `Bokeh Server running at …` must reach the launcher before `/health` answers (A6).
- **Without the flag** stdin is never read: the `python app.py` route is unchanged.

**TR-08.14 `_dash_launch_app(app_path, port, timeout, no_browser, *, ready_seconds=30.0, prebind=True, erase_app_when_ready=False)`** (31944).
- **The child.** `_cmd` (since commit 1 `[sys.executable, "-P", "-c", _DASH_BOOT, app_path, "--port", P, …]`, TR-08.8a) always appends `"--parent-watch"` after the app's own arguments. Popen has had `stdin=subprocess.PIPE` since commit 1 (the hand-over), and has no `start_new_session` or `process_group` (A5a). After the frame, which the bootstrap consumes exactly (§3b 3), the launcher writes nothing more to the pipe (S13 later adds one key line) and never closes it while the server runs. Popen's pipe fds are non-inheritable (PEP 446), so only Stata's process holds the write end, and the OS closes it on any exit.
- **Banner tracking.** `_drain_stdout` sets `_banner = True` when a forwarded line contains `Bokeh Server running at`. It checks this before the 200-line cap.
- **The erase.** In the loop, once `erase_app_when_ready and _ready and _banner and not _erased`: `_dash_erase_quietly(app_path)` and `_erased = True`. Since commit 1 the child never opens `app.py` (R-9), so this no longer guards the child's read. The rule is kept as A6 states it (R-9 item 8).
- **Docstring:** the stdin pipe, `--parent-watch`, erase-on-ready.
- **`__main__`'s launch block** (32196-32205) passes `erase_app_when_ready=_dash_private_run_of(args.output) is not None` (R-1). The spec and data were erased by `main()` (TR-08.8).

**TR-08.15 Help (F2).**
- 1421-1424: add after the Ctrl+C sentence: "If Stata exits, crashes or is killed, the server stops by itself within a few seconds and frees its port (measured on macOS; Linux and Windows have not been measured)."
- 1575-1578, and the tempfiles paragraph 2: "erases the specification and data once the application is written, and the application once the server answers; only a crash in the seconds before the server answers can leave a private copy, which the next dash command removes".

### Commit 3 — P0.13 F4: Break stops `dash serve`, r(1), and messages name Break

**TR-08.16 New launcher-only helpers** sit beside `_dash_launch_app`. They are not copied into the app.
- **`class _DashServeInterrupted(Exception)`.** Not a RuntimeError (A2).
- **`_dash_stata_poller(sfi=None)`** returns `(sfi.SFIToolkit.pollstd, (sfi.BreakError,))` when `sfi` is None and `import sfi` succeeds, or `sfi` is given, and both attributes exist. Otherwise it returns `(None, ())`.
- **`_dash_stop_child(proc, grace=5.0, interrupts=(KeyboardInterrupt,))`:**
  1. Close `getattr(proc, "stdin", None)`, ignoring errors. The app's watch stops it cleanly (0.08 s measured).
  2. `proc.wait(timeout=grace)`. On TimeoutExpired: `proc.terminate()`, then `proc.wait(timeout=grace)`.
  3. On TimeoutExpired, or on any of `interrupts` raised during a wait (a second Break, A4): `proc.kill()` (OSError ignored), then `proc.wait()`.
  4. It never calls `poll()` (Stata's) while stopping.

**TR-08.17 The launcher loop.**
- **Setup.** `poll, brk = _dash_stata_poller()`; `interrupts = (KeyboardInterrupt,) + brk`.
- **Before prebind.** If `poll`, call it once inside `try/except interrupts`. A Break there prints `dash: stopped by Break; no server was started.` (inside Stata) and raises `_DashServeInterrupted`. Popen is never constructed.
- **From Popen to the final `proc.wait()`**, inside one `try/except interrupts/finally`:
  - the first statements start the two pump threads and then hand the app over (`_dash_hand_over(proc, frame)`, TR-08.8a). An OSError, ValueError or AttributeError there raises TR-08.8a's `RuntimeError` ("could not be handed to Python"), and the `finally` stops the child. Commit 1's own small stop around the hand-over is folded into this try. S13's key line follows the hand-over;
  - each loop pass calls `poll()` first, outside the `urlopen` try (A1);
  - after the loop ends on its own, `poll()` is called once more: a Break pending when the child exited;
  - `except interrupts:` → `_dash_stop_child(proc, interrupts=interrupts)`; `_interrupted = True`;
  - `finally:` → if `proc.poll() is None`, `_dash_stop_child(proc, interrupts=interrupts)`. Thread joins and the drain follow.
- **Mapping the exit.** `_interrupted`, or `proc.returncode in (130, -signal.SIGINT)` (A5b), prints the stop line and raises `_DashServeInterrupted`:
  - `dash: stopped by Break; the server has stopped.` when `poll` is not None;
  - `dash_render: interrupted; the server has stopped.` otherwise.

  `0` and `-signal.SIGTERM` still return normally: a `timeout()` expiry. Anything else still raises RuntimeError.
- **Messages.**
  - Inside Stata: the ready line ends `…; press Break (Ctrl+C in console Stata) to stop.`, and the no-answer line ends `(press Break, or Ctrl+C in console Stata, to stop it).`
  - Outside Stata both keep `Ctrl+C`.
  - The `dash: the server answers at http://localhost:%d/` prefix is unchanged; S13 owns the host.
- **`__main__`.**
  - Only when `args.mode == "server" and args.launch`, wrap `main(…)` in `except KeyboardInterrupt`:
    - with the box, `_report["interrupted"] = True` and skip the launch;
    - without it, print `dash_render: interrupted; nothing was served.` to stderr and `raise SystemExit(130)`.
  - Around `_dash_launch_app`, put `except _DashServeInterrupted:` before `except RuntimeError`:
    - with the box, `_report["interrupted"] = True`;
    - without it, `raise SystemExit(130)`.
- **The emitted app** (31723-31729):
  ```
  _dash_int = False
  try: _server.io_loop.start()
  except KeyboardInterrupt: _dash_int = True
  finally: _server.stop(); print('Server stopped.', flush=True)
  if _dash_int and _a.parent_watch: raise SystemExit(130)
  ```
  The banner's last line under `--parent-watch` is `Stops when the program that started it ends.`; without the flag it stays `Press Ctrl+C to stop.`

**TR-08.18 dash.ado `_dash_serve`.**
- **The announcement** (7660-7661): `dash serve: starting Bokeh Server on port N.  Stata waits while it runs; press Break (Ctrl+C in console Stata) to stop it.` The `starting Bokeh Server` prefix is kept: test_env_guards.cscript:443 and test_render_locate.cscript:524 assert its absence.
- **Reading the interrupt.** After the `_srv_err` setLocal (7690): `python: _dash_srv_M.setLocal("_srv_brk", "1" if _dash_srv_rep.get("interrupted") else "")`.
- **The ending.** After the `_srv_err` branch: `_dash_tmp_close, dir(…)`, then `` if "`_srv_brk'" == "1" error 1 ``. `error 1` prints `--Break--` and r(1) (measured), and Stata erases what is left at program end (P2f).

**TR-08.19 Help (F4).**
- 97: `{pstd}{ul:Launch Bokeh Server (blocking -- press Break to stop)}{p_end}`. The `{ul:Launch Bokeh Server` prefix is kept: test_help_claims_1.py:251, 277 slice on it.
- 750-753: "Stata waits until you press Break (Ctrl+C in console Stata), the optional `{cmd:timeout()}` expires, or Stata itself exits."
- 777: "0 means run until Break (default)".
- 1421-1424, rewritten whole: "`{ul:Blocking behavior.}` `{cmd:dash serve}` blocks Stata until the server stops. `{cmd:timeout(}{it:#}{cmd:)}` stops it after *#* minutes, and the command returns 0. Break -- the Break button or menu item, or Ctrl+C in console Stata -- stops it at once, and the command ends with r(1), as any command interrupted by Break does. If Stata exits, crashes or is killed, the server stops by itself within a few seconds and frees its port (measured on macOS; Linux and Windows have not been measured). dash then removes its temporary folder; see …".
- 1719: `{pstd}{ul:Live Bokeh Server (blocking — Break to stop)}{p_end}`.

**TR-08.20 Maps.** Each commit adds its own keys in alphabetical place (R2).

`test/function_test_map.py`:
- **commit 1:** `_dash_private_root`, `_dash_private_dir_ok`, `_dash_private_write`, `_dash_private_msg`, `_dash_pid_alive`, `_dash_run_open`, `_dash_run_sweep`, `_dash_run_close`, `_dash_preview_path`, `_dash_prune_previews`, `_dash_tmp_write_text`, `_dash_tmp_clear`, `_dash_private_run_of`, `_dash_erase_quietly`, `_dash_private_clear_name` (→ `test_private_files.py::TestThePrivateClearName::test_a_link_is_refused_and_kept`), and, ratified 01oct2026:
  - `_dash_root_name` → `TestThePrivateRoot::test_windows_root_is_named_dash`;
  - `_dash_fallback_root` → `TestThePrivateRoot::test_a_symlinked_root_is_left_alone_and_a_fallback_is_used`;
  - `_dash_own_root` → `TestTheRunDir::test_close_refuses_a_path_outside_the_root`;
  - `_dash_mode_private` → `TestTheNote::test_mode_private_reads_group_and_other_bits_and_is_true_on_windows`;
  - `_dash_chosen_path` → `TestTheNote::test_a_file_in_a_folder_dash_chose_is_never_noted_by_the_renderer`;
  - (round 2, R-9; replaces round 1's `_dash_same_file`, which is withdrawn) `_dash_read_verified_app` → `TestTheLaunchFromTheOpenFile::test_a_substituted_app_is_not_started`, `_dash_child_stdin` → `TestTheLaunchFromTheOpenFile::test_the_child_is_handed_the_verified_bytes_not_the_path`, `_dash_app_frame` → `TestTheLaunchFromTheOpenFile::test_the_child_is_handed_the_verified_bytes_not_the_path`, `_dash_hand_over` → `TestTheLaunchFromTheOpenFile::test_a_child_that_cannot_take_the_app_is_stopped_and_reported`. `_DASH_BOOT` (a constant) and `_DashWrittenApp` (a namedtuple) are not functions and get no key; `TestTheBootstrap` pins the first, `test_main_returns_the_written_apps_identity` the second;
  - the map holds one test per key, the one that dies when the function's body is skipped (`fncov_mutate.py --map`), so `_dash_read_verified_app` keeps `test_a_substituted_app_is_not_started`. Its Windows-only branches are pinned by other tests, each with a mutation-table row: `TestWindowsPortability::test_the_verified_read_works_without_O_NOFOLLOW_and_getuid` (no `O_NOFOLLOW`, `O_NONBLOCK`, `O_CLOEXEC` or `os.getuid`) and `TestWindowsPortability::test_a_reparse_point_is_refused_on_windows` (step 1's `lstat`). The bootstrap's CRLF claim is pinned by `TestTheBootstrap::test_a_crlf_translated_frame_runs_nothing`;
- **F2:** `_dash_watch_parent`, `_dash_watch_parent.<locals>._watch`;
- **F4:** `_dash_stata_poller`, `_dash_stop_child`.

`test/program_coverage_map.py` (commit 1):
- `_dash_xm_load` → `test_wp29_truth.cscript:PF-05`;
- `_dash_tmp_open` → `test_wp29_truth.cscript:PF-06`;
- `_dash_tmp_preview` → `test_wp29_truth.cscript:PF-04`;
- `_dash_tmp_close` → `test_wp29_truth.cscript:PF-06`, `test_serve_launch.cscript:PF-07`;
- `_dash_tmp_clear` → `test_wp29_truth.cscript:PF-02`;
- `_dash_empty_data` gains `test_wp29_truth.cscript:PF-05`.

**TR-08.21 Security summary (rule 1).** Each threat and what closes it. "Privacy" items proceed with a note when the location cannot be private (R-8); "anti-hijack" items always refuse.
- **Cross-account read** (D4-D6), privacy: 0700 folder, 0600 files. Where the disk or `c(tmpdir)` cannot give that, the command's one note names the location and the remedy (ratified 01oct2026).
- **Group-write code injection on the app** (U2), anti-hijack: 0600, `O_EXCL` in the run folder, and the launch from the open file (TR-08.8a): the child runs only the bytes read through a descriptor checked for type, owner, identity, size and SHA-256.
- **A swap of `app.py` or its folder after the check** (§3b A; round 2, R-9), anti-hijack: closed. The child never opens a path; it is handed the verified bytes on its stdin (§3b B, G). Pinned by a deterministic swap between verification and Popen (`test_a_path_swapped_after_verification_does_not_change_what_runs`).
- **Module hijack through `sys.path`** (§3b C, F; round 2): `python app.py` imported a `linecache.py` planted beside the app, and `python -c` one planted in the working folder. Closed by `-P` and the bootstrap's guard: neither folder is on the child's `sys.path` (§3b D, F with `-P`, G).
- **Cross-account read of a user-named server app** (D6, M4, R-7), privacy: 0600 on every server route, created by `O_EXCL|O_NOFOLLOW` after `_dash_private_clear_name`. A link, a foreign or non-regular file, or a name planted between the removal and the create is refused (anti-hijack, r(7102)), and a reader holding the old file open never sees the new data. Residual: the folder the user names is not refused, re-moded or noted (ratified), so its listing (the file's name) is as private as that folder.
- **Symlink, hard-link and pre-created-file attacks on predictable names** (D8, D9), anti-hijack: `O_NOFOLLOW` plus fstat type, owner and nlink checks, r(7102).
- **FIFO hang** (A3), anti-hijack: `O_NONBLOCK`.
- **Squatting a predictable root** (P7), anti-hijack plus availability: the planted `dash-<uid>` is neither used nor followed. A fallback root made by `mkdtemp` (0700, its own, unguessable) takes its place, and the note names it. This costs nothing: the old r(603) refusal is gone (ratified).
- **A `c(tmpdir)` others can write without a sticky bit** (P8, A14), privacy, proceed and note. Another account can rename dash's folders but cannot read their 0600 files. A swapped `app.py` cannot run (R-9, §3b B). Residual (R-8): another account that replaces `dash-<uid>` between dash.ado's write of `spec.json`/`data.json` and the renderer's read of them by path can change what the dashboard shows. It can also deny the launch. The remedy is in the note.
- **A disk that keeps no permissions**, privacy, proceed and note. The note names the folder. `_dash_private_run_of`'s mode clause then fails, so `dash serve`'s copies stay until the command ends rather than being erased once written (residual).
- **An orphan serving the data after Stata dies** (t3, t4): the stdin watch plus the hard exit.
- **Data at rest while serving:** erase on ready.
- **Break swallowed:** poll outside broad excepts.

Other properties:
- No `shell=True`. No user text in a `python:` line. Bytes on the app's stdin are bounded per read and discarded. The frame's header is bounded at 128 bytes and its body at the declared length, which the launcher sets.
- `os.kill` is never called on Windows, nor with a pid below 1.
- The watch's stop is Tornado's thread-safe `add_callback`.

## Boundaries

- **The token (P0.12a, S13).** Do not touch the "only this machine" sentence (dash.sthlp:1463-1464), `make_document`'s session admission, or the ready line's host. S13 adds them on this tree.
- **Stata's own tempfiles.** Do not change `preserve`/`SQ*` behaviour (outside dash's control; documented).
- **No copy-list entry except `"_dash_watch_parent"`** (R-3). No change to the saved page's JavaScript. No change to `dash_parse.mata`: it does no file I/O, and no option is added.
- **User-named pages keep `open(…, "w")`.** That is one-line `saving()` and `dash build, saving()` (BR-08.5). `dash build, server saving(.py)` does not: it is the app, written 0600 (BR-08.5a, R-7). `ServerAppBuilder.build`'s `private=False` default stays for direct `.build(` callers (tests).
- **Sibling sections' code.** Do not edit `_dash_extract_vars`/hover export (S06), the function-layer evaluation after the segment loop (S04), or `_dash_write_stata_data`'s row selection (S14). Only its final write changes here.
- **Tracking documents.** Do not edit GAPS2.md, ROADMAP.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, DROPIN-REMAINING.md or AGENTS.md (index A5). The text for them is in "Notes for the closeout".
- **Untouched files.** `test_clear_registry.cscript` (R-5), `test/run_all_cscripts.do` and `test/test_cscript_hygiene.py` (S01's only).
- **No privacy refusal (R-8, ratified 01oct2026).** No code path raises, exits or returns an error because a location is not private. The anti-hijack guards are not relaxed: no `O_NOFOLLOW`, `O_NONBLOCK`, type, owner or nlink check is removed, and no planted `dash-<uid>` is used or followed. The new helpers (`_dash_root_name`, `_dash_fallback_root`, `_dash_own_root`, `_dash_mode_private`, `_dash_chosen_path`, and since round 2 `_DashWrittenApp`, `_DASH_BOOT`, `_dash_read_verified_app`, `_dash_app_frame`, `_dash_child_stdin` and `_dash_hand_over`) are not copied into the served app (R-3). `_dash_same_file` is withdrawn (R-9).
- **Launch from the open file (R-9, round 2).** No route of dash's starts the app by path, and none drops `-P`. The bootstrap reads stdin only with `os.read(0, …)` and never through `sys.stdin`, so S13's key line and F2's watch see every byte after the frame. A `python app.py` or `bokeh serve app.py` the user runs is not changed. It is documented (TR-08.11).
- **No `--ephemeral` flag** (R-1). No `atexit` (it does not run at Stata exit, m3). No `os.umask` call in product code; tests may set it inside `try/finally`. No capture-based wrapper around the render routes (m7 Q3/Q5).

## Stata truth

- **No fixture.** Modes depend on the host's umask, so frozen values would be wrong elsewhere. The twoway comparisons are made live, in the same session, in the S08 block of `test/test_wp29_truth.cscript`:
  - **PF-01:** twoway leaves nothing.
  - **PF-03:** dash's `saving(.html)` mode equals twoway's `saving(.gph)` and `graph export .svg` under the runner's umask.
  - **PF-11:** dash's `dash build, server saving(.py)` is 0600 whatever the runner's umask, unlike twoway's named files (M4, R-7).
  - **PF-12:** a `c(tmpdir)` other accounts can change does not stop dash, as twoway is not stopped. Every route gives rc 0 and one note (R-8, ratified).
- **The block** is appended above `* ==== append new blocks above this line ====`, after S07's block (section order, R1):

```
* ==== S08 P0.12b, P0.14: private temporary files ====
local only : env WP29_ONLY
if inlist("`only'", "", "S08") {
    display as text "S08 start `c(current_time)'"
    ... PF-01 .. PF-06, PF-11 and PF-12, each through the scaffold's tally helpers ...
    display as text "S08 end `c(current_time)'"
}
* ==== end S08 ====
```

- **Running it.** Every Stata run goes through the driver (index "The cscript driver"), with `<wt>` = `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s08`:

```sh
mkdir -p <scratch>/stata
printf 'cd "%s/test"\ndo "%s/test/%s"\n' <wt> <wt> test_wp29_truth.cscript > <scratch>/stata/run_test_wp29_truth.do
dash_nobrowser=1 WP29_ONLY=S08 <wt>/scripts/stata_slot.sh <scratch>/stata <scratch>/stata/run_test_wp29_truth.do
# read <scratch>/stata/run_test_wp29_truth.log; never relaunch to check
```

  The same form runs `test_serve_launch`, `test_help_claims_4`, `test_adversarial` and `test_env_guards` (unset `WP29_ONLY`). The scripts gate on `c(python_exec)` and exit 222 without it. A SKIP is not a pass: check `c(python_exec)` before trusting one (many concurrent sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`).
- **Inside the block:**
  - the uid and pid come from `python: Macro.setLocal("…", str(os.getuid()))` / `os.getpid()` (A1);
  - paths are compared as spelled from `c(tmpdir)`;
  - no path is interpolated into Python source.

## TDD test stubs

"Fails at" means:
- the batch-1 base (`<scratch>/batch-1-base.txt`) for cycle 1;
- commit 1's sha for cycle 2;
- commit 2's sha for cycle 3.

Helpers:
- `test/test_string_value_export.py`'s `FakeSfi`, `_fake_auto` and `_write`;
- `test/test_serve_launcher.py`'s `_write_inputs`, `_SPEC`, `_DF`, `_free_port` and `_HeldSocket`;
- `test/test_server_serves.py`'s `_Launched` and `_build_app`;
- `test/test_help_claims_4.py`'s `_served_filter_move`.

### Cycle 1, `test/test_private_files.py` (new; task 08-02)

- Test: `TestTheDataFileIsPrivate::test_the_data_file_is_0600_under_umask_022`. Fails: `0o644`.
- Test: `TestTheDataFileIsPrivate::test_the_data_file_is_0600_under_umask_002`. Fails: `0o664`.
- Test: `TestTheDataFileIsPrivate::test_a_symlink_at_the_path_is_not_followed`. `_dash_write_stata_data` raises `getattr(dr, "_DashUnsafePath")` whose message holds `refused to write` and `(it is a link)`; the victim is unchanged. Fails: no raise, victim overwritten.
- Test: `TestTheDataFileIsPrivate::test_a_preexisting_world_readable_file_of_ours_is_made_0600`. Fails: `0o666`.
- Test: `TestTheDataFileIsPrivate::test_a_hard_linked_file_is_refused`. Raises `_DashUnsafePath` (`it has other links`). Fails: written through the link.
- Test: `TestTheDataFileIsPrivate::test_a_fifo_at_the_path_is_refused_without_blocking`. Uses `os.mkfifo` and a 2 s SIGALRM guard; raises `_DashUnsafePath` (`it is a pipe`). Fails: blocks, and the alarm raises.
- Test: `TestTheDataFileIsPrivate::test_a_file_of_another_account_is_refused`. Monkeypatches `os.getuid` to `real + 1`; raises `_DashUnsafePath`. Fails: written.
- Test (guard, ratified 01oct2026): `TestTheDataFileIsPrivate::test_a_file_whose_mode_cannot_be_set_is_written`. A pre-existing 0644 data file of the user's, with `os.fchmod` monkeypatched to raise `OSError(errno.ENOTSUP, …)`, makes `_dash_write_stata_data` return `""`. The file holds the new JSON and stays 0644 (§3a R8): the privacy class is never refused. It passes at the base, where `open(…, "w")` writes, and pins that the new writer does not turn a failed `fchmod` into a refusal.
- Test: `TestTheServedAppIsPrivate::test_the_launch_route_writes_the_app_0600`. Uses `dr.main(sp, dp, <tmp>/S_1.000003, mode="server", launch=True)` under umask 022 and 002. Fails: `0o644`/`0o664`.
- Test: `TestTheServedAppIsPrivate::test_the_launch_route_deletes_spec_and_data_inside_a_run_dir_and_never_elsewhere`. Fails: AttributeError (`_dash_run_open`).
- Test: `TestTheServedAppIsPrivate::test_main_unlinks_only_when_all_three_paths_share_a_run_dir_under_dash_uid`. Three negative cases keep their inputs: a `run-*` dir under a parent not named `dash-<uid>`; a parent of mode 0755; spec in another folder. Fails: AttributeError.
- Test: `TestTheServedAppIsPrivate::test_private_run_of_accepts_only_dash_s_own_layout`. It accepts a run folder under `dash-<uid>` and under a fallback root `dash-<uid>-abcdefgh` (0700, the user's). It rejects one under `dash-<uid>-ABC` (wrong pattern) and one under a fallback-named folder of mode 0755. Fails: AttributeError.
- Test: `TestTheServedAppIsPrivate::test_erase_quietly_never_follows_a_link_and_ignores_a_missing_file`. Fails: AttributeError.
- Test: `TestTheServedAppIsPrivate::test_a_dash_build_server_app_is_0600`. Uses `dr.main(sp, dp, <tmp>/app.py, mode="server")` (no launch: `dash build, server`'s route) under umask 022 and 002. Fails: `0o644`/`0o664` (D6). Replaces u11b's guard `test_a_dash_build_server_app_follows_the_umask`, which pinned the M4 defect (R-7).
- Test: `TestTheServedAppIsPrivate::test_replacing_a_server_app_writes_a_new_0600_file`. Pre-creates `<tmp>/app.py` at 0644 holding `OLD`, keeps a read handle open on it, then runs the same `main` call. Asserts the path is 0600 and holds `_DATA_B64`, and the old handle still reads `OLD`: a new file was created, the old one was not rewritten. Fails: `0o644`.
- Test: `TestTheServedAppIsPrivate::test_a_link_at_a_server_app_path_is_refused_and_its_target_kept`. `<tmp>/app.py` is a symlink to a 0644 victim holding `V`. `main` raises `getattr(dr, "_DashUnsafePath")` with `refused to write` and `it is a link`; the victim still holds `V` at 0644 and the link is still a link. Fails: the victim is overwritten with the app.
- Test (ratified 01oct2026): `TestTheServedAppIsPrivate::test_a_user_named_folder_that_others_can_read_is_neither_refused_nor_remoded`. `<tmp>/pub` at 0755 (and again at 0777), then `main(sp, dp, <tmp>/pub/app.py, mode="server")`. It returns, `app.py` is 0600, the folder's mode is unchanged, and `capsys` holds no `dash: note:`. Fails: `0o644` (the base already leaves the folder alone).
- Test: `TestTheServedAppIsPrivate::test_another_accounts_file_at_a_server_app_path_is_refused`. Monkeypatches `os.getuid` to `real + 1`; the existing file is unchanged. Fails: overwritten.
- Test (guard): `TestTheServedAppIsPrivate::test_a_refused_port_leaves_an_existing_server_app_untouched`. An existing `app.py` holding `OLD`, then `main(…, mode="server", port=99999)` and a spec with `build_options` port `"99999"`, each raising `argparse.ArgumentTypeError`. The file still holds `OLD`. It passes at the base and pins that the clear sits after the source is complete.
- Tests: `TestThePrivateClearName::{test_a_missing_name_is_left_missing, test_an_own_regular_file_is_removed, test_a_link_is_refused_and_kept, test_a_folder_or_fifo_is_refused, test_another_accounts_file_is_refused}`. The link test checks that both the link and its target survive. All fail: AttributeError (`_dash_private_clear_name`).
- Test (guard): `TestTheServedAppWritesNoFile::test_the_generated_app_has_no_file_writing_call`. An AST scan of the generated source finds no `open(` in a write mode, no `os.open`, no `write_text`/`write_bytes`, no `tempfile.` and no `shutil.` writes.
- Test: `TestTheSavedPreviewIsPrivate::test_a_private_output_page_is_0600`. Fails: TypeError (`private_output`).
- Test: `TestTheSavedPreviewIsPrivate::test_the_cli_flag_reaches_main`. Uses runpy with `--private-output`. Fails: SystemExit 2 (unrecognized argument).
- Test (guard): `TestTheSavedPreviewIsPrivate::test_a_user_named_page_follows_the_umask`.
- Tests: `TestThePrivateRoot::{test_created_0700_under_umask_002_and_277, test_a_loose_root_of_ours_is_tightened, test_a_symlinked_root_is_left_alone_and_a_fallback_is_used, test_a_root_of_another_account_is_left_alone_and_a_fallback_is_used, test_a_root_that_is_a_file_is_left_alone_and_a_fallback_is_used, test_a_fallback_root_is_reused_only_when_it_is_ours_and_0700, test_a_writable_non_sticky_base_proceeds_with_a_note_naming_chmod, test_a_base_owned_by_another_account_proceeds_with_a_note, test_a_root_that_cannot_be_tightened_proceeds_with_a_note, test_a_sticky_world_writable_base_is_accepted_without_a_note, test_a_base_that_is_not_a_folder_raises_an_os_error, test_a_base_reached_through_a_symlink_gives_paths_the_caller_can_match, test_windows_root_is_named_dash, test_create_false_returns_none_when_absent}`. Ratified 01oct2026: each "left alone" or "proceeds" case asserts that no exception is raised. They also assert:
  - `_dash_private_root` returns `(root, note)` with the expected root: `dash-<uid>`, or a path matching `^dash-<uid>-[a-z0-9_]{8}$` that is 0700 and the user's;
  - the note names the location and holds the R-8 sentence's key words (`chmod go-w` and `STATATMP` for the base; `is not yours to use` and the fallback's path for a planted root; `could not be made private` for a root kept loose by an `os.fchmod` monkeypatched to raise ENOTSUP, or to do nothing);
  - a planted symlink's target folder stays empty;
  - a 0755 `dash-<uid>-zzzzzzzz` or another account's fallback-named folder is never reused (§3a R5).

  All fail: AttributeError.
- Tests: `TestTheRunDir::{test_open_makes_a_0700_run_named_for_this_pid, test_open_sweeps_this_pids_stale_runs, test_open_sweeps_a_dead_pids_run, test_open_keeps_a_live_other_pids_run, test_the_sweep_treats_permission_error_as_alive, test_age_never_removes_a_live_pids_run_on_posix, test_age_removes_a_run_on_windows, test_the_sweep_never_signals_on_windows, test_the_sweep_never_signals_pid_zero, test_close_removes_the_run, test_close_refuses_a_path_outside_the_root, test_close_removes_a_link_inside_the_run_not_its_target, test_close_of_a_missing_run_is_silent, test_open_reports_an_unsafe_root_as_a_note_and_still_opens, test_open_reports_an_os_failure_as_err, test_close_removes_an_empty_fallback_root_and_keeps_one_holding_a_preview}`.
  - Ratified 01oct2026: `test_open_reports_an_unsafe_root_as_a_note_and_still_opens` plants a symlinked `dash-<uid>`. `err` is `""`, `note` starts `dash: note: ` exactly once, and `rundir` is a 0700 `run-<pid>-*` inside the fallback root.
  - `test_open_reports_an_os_failure_as_err` gives a `tmpdir` that is a regular file. `err` holds `could not make its temporary folder` and every path is `""`.
  - A dead pid is a finished subprocess's pid. A live other pid is `os.getppid()`. Ages are set with `os.utime`.
  - The Windows cases monkeypatch `os.name = "nt"` and `os.kill` to raise `AssertionError("signalled")`.
  - All fail: AttributeError.
- Tests: `TestThePreviews::{test_names_are_unique_and_inside_previews, test_the_newest_five_are_kept, test_a_page_opened_in_the_last_minute_is_kept, test_clear_removes_every_page_but_a_young_opened_one, test_a_live_other_sessions_pages_survive_prune_and_clear, test_a_dead_sessions_pages_are_removed, test_the_ceiling_bounds_all_sessions_together, test_files_dash_did_not_name_are_never_touched, test_clear_never_creates_the_root, test_a_planted_previews_folder_moves_the_preview_to_a_fallback_root, test_clear_prunes_and_removes_an_emptied_fallback_root}`. The planted case is a symlink `previews` inside the root, pointing at an empty folder. The path lands in `<fallback>/previews/`, the target stays empty, `note` names the planted path, and no exception is raised. All fail: AttributeError.
- Tests (new, ratified 01oct2026): `TestTheNote::{test_one_note_names_every_location_once, test_mode_private_reads_group_and_other_bits_and_is_true_on_windows, test_a_server_app_on_a_disk_without_permissions_is_written_and_noted, test_a_file_in_a_folder_dash_chose_is_never_noted_by_the_renderer, test_the_note_holds_no_data}`.
  - The first combines a group-writable non-sticky base with a planted root. `_dash_run_open`'s `note` has `dash: note: ` once (`note.count("dash: note: ") == 1`) and names both `tmpdir` and the planted path.
  - The disk without permissions is simulated by monkeypatching `dr._dash_private_write` to write and then return an `os.stat_result` whose mode is `0o100644`. `main(…, <tmp>/user/app.py, mode="server")` writes the file and `capsys.readouterr().out` holds exactly one `dash: note: ` line naming the path and `every observation`. The same call with the app path from `dr._dash_run_open(str(tmp_path))["app"]` prints none.
  - `test_the_note_holds_no_data` asserts that the note holds no value from `_DF` and no `_DATA_B64`.
  - All fail: AttributeError.
- Tests (round 2, ratified 01oct2026; they replace round 1's `TestTheLaunchIdentity`): `TestTheLaunchFromTheOpenFile`. A module helper `_RecStdin` records `write(b)` calls (bytes, appended to `.writes`), `flush()` and `close()`, and has no `buffer` attribute, so `_dash_child_stdin` returns it itself. It has the same shape as S13's `serve_token_probe.FakeStdin`. Fakes construct one as `self.stdin`. `_parse_frame(b)` splits `DASHAPP1 <n> <sha>\n` from the body.
  - `test_a_path_swapped_after_verification_does_not_change_what_runs` [serve, skipif win32]. This is the deterministic race test, and it uses only base APIs, so it fails at the base for the defect itself.
    - Build `<tmp>/run-1-x/app.py` with `dr.ServerAppBuilder(sp, dp).build(out)` and chmod it 0600.
    - Monkeypatch `subprocess.Popen` with a wrapper. Before it calls the real Popen, it renames `<tmp>/run-1-x` aside and recreates it holding an `app.py` that writes `EVIL RAN` to a marker and exits 3, plus a `linecache.py` that appends `linecache` to the marker and exits 4. Then it calls the real Popen and keeps the process. That is the window between dash's verification and the child's start (§3b A).
    - A helper thread waits up to 40 s for `/health` (`_wait_health`) or for the process to exit, whichever comes first, then terminates it if it still runs.
    - Call `dr._dash_launch_app(out, port, 0, True)`.
    - Asserts: no RuntimeError; the marker does not exist; `/health` answered; `capsys` holds `Bokeh Server running at`.
    - A `finally` kills the process and `_kill_listeners(port)`.
    - Fails at the base: `marker == "EVIL RAN"`, and RuntimeError `the app exited with status 3` (§3b A).
  - `test_the_child_is_handed_the_verified_bytes_not_the_path`. A fake Popen records `cmd` and `kw`, sets `self.stdin = _RecStdin()`, makes the same swap in its `__init__`, and has `poll()` return 0.
    - `cmd[:5] == [sys.executable, "-P", "-c", getattr(dr, "_DASH_BOOT"), out]`;
    - `kw["stdin"] is subprocess.PIPE`;
    - the recorded bytes are one frame whose body equals the original `app.py` bytes read before the swap, with a matching SHA-256;
    - the evil text is nowhere in the frame.

    Fails at the base: `cmd[1] == out`, and no `stdin` keyword.
  - `test_a_substituted_app_is_not_started`.
    - Write the app with `written = dr.main(sp, dp, run["app"], mode="server", launch=True)` at a `dr._dash_run_open(str(tmp_path))` path.
    - Rename the run folder and recreate it holding a different `app.py` (§3a R9).
    - `dr._dash_launch_app(run["app"], port, 0, True, expect=written)` with a fake Popen raises `_DashUnsafePath` with `refused to run` and `(it was replaced after dash wrote it)`. The fake Popen is never constructed.
    - Fails at the base: AttributeError (`_dash_run_open`).
  - `test_the_written_app_is_started`. The unmodified path: the fake Popen is constructed once with the bootstrap command, and its frame's digest equals `written.sha256`. Fails: AttributeError.
  - `test_main_returns_the_written_apps_identity`. `written.st` is an `os.stat_result` whose `(st_dev, st_ino)` equal `os.lstat(app)`'s, and `written.sha256 == hashlib.sha256(open(app, "rb").read()).hexdigest()`. Fails: AttributeError.
  - `test_a_swap_between_open_and_read_reads_the_original`. `os.fstat` is monkeypatched with a wrapper that calls the real `fstat`. On its first call for a regular file of size `written.st.st_size`, it first swaps the run folder as above. `dr._dash_read_verified_app(app, written)` returns bytes whose SHA-256 is `written.sha256`. Fails: AttributeError.
  - `test_the_same_file_rewritten_in_place_is_refused`. Flip one byte of `app.py` in place: same inode, same size. `_dash_launch_app(…, expect=written)` raises `_DashUnsafePath` `(it changed after dash wrote it)`, and Popen is never constructed. This is the SHA-256 check. Fails: AttributeError.
  - `test_a_link_or_fifo_at_the_app_path_is_refused_without_expect`.
    - A symlink at the app path, to a copy of the app, gives `(it is a link)`.
    - An `os.mkfifo` at the app path, under a 2 s SIGALRM guard, gives `(it is not a regular file)` without blocking.
    - Both run with `expect=None`, and the fake Popen is never constructed.
    - Fails at the base: the fake Popen is constructed (`python <link>` would follow it).
  - `test_another_accounts_app_is_refused`. `os.getuid` is monkeypatched to `real + 1`, giving `(it belongs to another account)`. Fails: constructed.
  - `test_a_child_that_cannot_take_the_app_is_stopped_and_reported`. A fake whose `stdin.write` raises `BrokenPipeError`, and whose `poll()` returns None until `kill()` (and 0 after 20 calls, so the base cannot hang). The launcher raises RuntimeError holding `no server started on port <P>: the app could not be handed to Python`. `kill` was recorded, and no `dash: the server answers` line was printed. Fails at the base: DID NOT RAISE, because the base never writes to stdin.
  - `test_an_app_that_cannot_be_read_is_a_launch_failure`. Unlink the written app, then call `_dash_launch_app(…, expect=written)`. It raises RuntimeError (`the app could not be read`), not `_DashUnsafePath`. Fails: AttributeError.
  - `test_no_module_beside_the_app_or_in_the_working_folder_is_imported` [real subprocess, no server].
    - A tiny app, `import hashlib, types; print("TINY OK")`, written 0600 with `open`.
    - `linecache.py`, `hashlib.py` and `types.py`, each appending its name to a marker and exiting 4, are planted beside the app and in a folder entered with `monkeypatch.chdir`.
    - `dr._dash_launch_app(app, port, 0, True)` returns: the child exits 0.
    - Asserts: the marker does not exist, and `capsys` holds `TINY OK`.
    - Fails at the base: marker `linecache`, RuntimeError `status 4` (§3b C).
- Tests (round 2): `TestTheBootstrap`. Each runs `[sys.executable, "-P", "-c", dr._DASH_BOOT, <tmp>/never/app.py, …]` with `stdin=PIPE` and writes `dr._dash_app_frame(src.encode())`. The path is never created.
  - `test_it_runs_the_text_as_main_with_the_apps_name_and_argv`: it prints `__main__ True ['--port', 'x']`, and argparse's error names `usage: app.py` (rc 2) (§3b 2).
  - `test_a_traceback_names_the_apps_file_line_and_text`: `File "<path>", line 4, in f`, then `raise ValueError('boom in app')` (§3b 1).
  - `test_exit_statuses_are_those_of_a_script_run`: `SystemExit(130)` gives 130, and an uncaught KeyboardInterrupt gives `-signal.SIGINT` (skipif win32) (§3b 2b, 2c).
  - `test_bytes_after_the_frame_are_left_on_stdin`: the app reads one line a byte at a time and then reads to end of file; it prints `LINE 43` and `EOF after 10 more bytes` (§3b 3). This pins S13's key line and F2's watch.
  - `test_a_damaged_or_short_frame_runs_nothing`: a wrong digest gives rc 1 with `was damaged`; a short body gives rc 1 with `was not handed over`; `SHOULD NOT RUN` never prints (§3b 5, 5b).
  - `test_neither_the_working_folder_nor_the_apps_folder_is_on_sys_path`: the child prints `sys.flags.safe_path` True, `"" not in sys.path`, and the app's folder not in `sys.path`.
  - `test_the_text_survives_windows_quoting`: `'"' not in dr._DASH_BOOT`, `"\\" not in dr._DASH_BOOT`, and `subprocess.list2cmdline([sys.executable, "-c", dr._DASH_BOOT]).endswith(' "' + dr._DASH_BOOT + '"')`.
  - `test_a_large_app_is_handed_over_whole`: a 20 MB comment line, then `print("BIG OK")`, finishes within 30 s (§3b 4: 100 MB in 0.10 s).
  - `test_a_crlf_translated_frame_runs_nothing`. This is what a Windows text-mode pipe would do to the frame (R-9 item 4).
    - `src = b'print("SHOULD NOT RUN")\n# padding\n'`, and `good = dr._dash_app_frame(src)`, split once at its first `b"\n"` into header and body.
    - First leg: the header unchanged, then the body with every `b"\n"` replaced by `b"\r\n"`. It gives rc 1, stderr holding `was damaged`, and stdout without `SHOULD NOT RUN`.
    - Second leg: the whole frame translated, header included. It gives rc 1 and stdout without `SHOULD NOT RUN`; stderr holds `was damaged` or `was not handed over`, whichever the header parse gives.
    - The source is chosen so that the first *n* bytes of the translated body still compile and print. With the digest check removed, both legs printed `SHOULD NOT RUN` with rc 0 (measured, `<scratch>/wp29r2/s08-crit3/crlf2.py`), so the test dies under that mutation.
  - All fail at the base: AttributeError (`_DASH_BOOT`, `_dash_app_frame`).
- Tests: `TestTheSpecWriter::{test_text_is_written_exactly_and_0600, test_the_python_writer_keeps_backtick_and_dollar_sequences_literal, test_a_link_at_the_path_raises_and_its_target_is_kept}`. The last (ratified 01oct2026) expects `_dash_tmp_write_text` to raise `_DashUnsafePath` (`refused to write`, `it is a link`), not to return text.
  - The text is 300 KB with compound quotes, backslashes and CJK.
  - The literal is `` "`x' $y `c(pid)'" ``.
  - All fail: AttributeError.
- Test: `TestWindowsPortability::test_writer_and_root_work_without_O_NOFOLLOW_O_CLOEXEC_fchmod_getuid`. Uses `monkeypatch.delattr` on each. Fails: AttributeError.
- Tests (round 2, R-9; answer B requires the launch to work on Windows): `TestWindowsPortability`. They run `_dash_read_verified_app`'s Windows code on macOS. Each reaches the new name with `getattr(dr, "_dash_read_verified_app")` inside the test, so it fails on an assertion, never at collection.
  - `test_the_verified_read_works_without_O_NOFOLLOW_and_getuid`.
    - Write the app with `written = dr.main(sp, dp, run["app"], mode="server", launch=True)` at a `dr._dash_run_open(str(tmp_path))` path, before any patching.
    - Then `monkeypatch.delattr(os, n, raising=False)` for `O_NOFOLLOW`, `O_NONBLOCK`, `O_CLOEXEC` and `getuid`.
    - `dr._dash_read_verified_app(run["app"], written)` returns bytes equal to `open(run["app"], "rb").read()`, and their SHA-256 equals `written.sha256`.
    - Fails at the base: AttributeError (`_dash_run_open`). Fails under a bare `os.O_NOFOLLOW` or `os.getuid()` in the function: AttributeError (measured on a prototype, `<scratch>/wp29r2/s08-crit3/test/`).
  - `test_a_reparse_point_is_refused_on_windows`.
    - Write `app` and `written` as above.
    - Monkeypatch `os.lstat` to return, for `app` only, `types.SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)`, and to call the real `lstat` for any other path. A stand-in is needed because on macOS `os.stat_result` takes no `st_file_attributes` field (measured: `got duplicate or unexpected field name(s)`). The mode is regular, so only the attribute arm can refuse.
    - Monkeypatch `os.open` with a wrapper that records its path, and `subprocess.Popen` with a fake that records construction.
    - Then `monkeypatch.setattr(os, "name", "nt")`, as the other Windows cases do (TestThePrivateRoot). Every path is a `str` and no `pathlib.Path` is built while it is patched: from Python 3.13, `Path()` reads `os.name` and would build a `WindowsPath`, which raises on macOS.
    - `dr._dash_read_verified_app(app, None)` raises `_DashUnsafePath` holding `refused to run` and `(it is a link)`, and `os.open` was never called for `app`.
    - `dr._dash_launch_app(app, port, 0, True, expect=written)` raises the same, and the fake Popen is never constructed.
    - The `S_ISLNK` arm: with `O_NOFOLLOW` also deleted, a real symlink `<tmp>/link.py` to a copy of the app (the patched `lstat` passes it to the real one) gives `(it is a link)` from `_dash_read_verified_app(link, None)`. Without step 1 the open would follow the link, as on Windows.
    - Fails at the base: AttributeError. Fails with step 1 dropped: DID NOT RAISE (measured on the prototype).
- Tests: `TestTheAdoUsesThePrivateDir`. Comments are stripped first: WP-24 measured a comment satisfying a text test.
  - `test_no_render_route_names_a_stata_tempfile_for_data`. Fails: `tempfile saving_path_tmp`, `data_json_path`, `serve_app_path`.
  - `test_every_render_route_opens_then_closes_a_run`.
  - `test_the_spec_and_empty_data_are_written_by_python`. Fails at 4281, 6143, 7286.
  - `test_python_reads_paths_by_value`.
  - `test_every_new_python_line_is_an_assignment_or_a_setlocal`.
  - `test_each_python_program_calls_dash_require_python_first`.
  - `test_the_run_paths_are_read_from_r_on_the_next_line`.
  - `test_dash_clear_prunes_through_a_captured_call`.
  - `test_empty_data_keeps_its_trailing_newline_and_the_spec_has_none`.
  - `test_exit_603_follows_only_an_os_failure_of_the_folder` (ratified 01oct2026). In the comment-stripped text of `_dash_tmp_open`, `_dash_tmp_preview`, `_dash_empty_data`, `_dash_plot` and `_dash_prepare_spec`, `exit 603` appears exactly twice: once in `_dash_tmp_open` and once in `_dash_tmp_preview`, each inside the block guarded by its `_to_err`/`_tp_err` length test. No `_dash_tmp_write_text` call is followed by an error branch.
  - `test_the_note_is_printed_once_per_command` (ratified 01oct2026):
    - `_dash_tmp_open` prints `_to_note` through `_dash_say("txt"` and returns `noted`;
    - `_dash_plot` copies `r(noted)` on the line after `r(data)` and passes `` noted(`_dash_noted') `` to `_dash_tmp_preview`;
    - `_dash_tmp_preview` prints `_tp_note` only under `` if "`noted'" != "1" ``;
    - `_dash_build`, `_dash_serve` and `_dash_clear` print no note of their own.
- Tests: `TestTheHelpDocumentsTheTempfiles::{test_the_section_exists_and_is_linked, test_it_states_the_modes_the_folder_and_the_pruning, test_it_states_the_note_and_the_anti_hijack_guard, test_no_passage_says_stata_erases_the_app, test_it_says_a_named_server_app_holds_the_data_and_is_0600, test_it_says_dash_serve_runs_the_text_it_checked}`. The note test (ratified 01oct2026) reads the tempfiles section. It expects `dash: note:`, `chmod go-w`, `STATATMP`, `never stops a command for privacy`, `r(7102)`, `never writes through a symbolic link` and `r(603)`. It also asserts that the one sentence holding `r(603)` holds `read-only` and none of `private`, `link` or `another account`. The last one reads the tempfiles section and the "Running the generated .py file independently" passage, and expects `every observation`, `0600`, `replace` and `symbolic link`. The round-2 test reads the same two places. It expects `hands the text to Python` and `never run` in the tempfiles section, and `by its name` and `imports modules from the folder` in the passage. It also asserts that no sentence in the tempfiles section holds `instant`, the struck residual. Fail: no `{marker tempfiles}`.
- Flipped:
  - `test/test_string_value_export.py::TestDashAdoUsesTheWriter::test_every_entry_point_is_called_by_the_ado_and_no_other`;
  - `test/test_immediate_dashboards.py::TestTheDataFileIsTheOneDashAdoWrites::test_dash_ado_writes_this_text`.

### Cycle 1, certification cases

- **PF-01 to PF-06**, in the S08 block of `test/test_wp29_truth.cscript` (task 08-03):
  - **PF-01 (truth guard):** `twoway scatter mpg weight` and `twoway line mpg weight, sort` add no file anywhere under `c(tmpdir)`, walked recursively.
  - **PF-02:** three one-line previews under `$dash_nobrowser`, then `dash clear`, leave no `St<pid>*.html` of this session in `c(tmpdir)` and no `dash-preview-*-<pid>-*.html`. The root and `previews/` are 0700. Only this session's names are checked: the slot's `STATATMP` folder persists across runs, and the red run of 08-03 leaves its own `St<pid>.000001.html` there. Fails: `St<pid>.000001.html` remains.
  - **PF-03 (parity guard):** the mode of dash's `saving(pf03.html)` equals twoway's `saving(pf03.gph)` and `graph export pf03.svg`.
  - **PF-04:** after one one-line render, the newest page in `dash-<uid>/previews/` whose name carries this pid (pid from Python) is 0600 and owned by the uid. `previews/` and the root are 0700, and the page's path starts with `c(tmpdir)` as spelled. The `dash: dashboard saved to` line of a log captured around the render names the page's basename once SMCL line-wrap continuations (newline followed by `> `) are joined: long paths wrap even at `set linesize 255`. Fails: no such page; the render wrote `St<pid>.<n>.html` at 0644.
  - **PF-05:** `_dash_xm_load` then `_dash_tmp_write_text` reproduces `Macro.getLocal` exactly, for a local holding `` `x' $y `` (built in Mata from `char(96)`/`char(36)`) and for a 300 KB local with compound quotes, a backslash and CJK. `_dash_empty_data` writes the JSON plus one `\n`. Fails: no such program/function.
  - **PF-06:** a stand-in renderer first on the ado-path records, for the one-line form, `dash build, saving()`, `dash build, server saving(.py)` and `dash serve, nobrowser timeout(1)`:
    - the modes of `--spec`/`--data` and of their folder;
    - the folder's name;
    - whether `--private-output` was passed.

    The case asserts:
    - spec and data are 0600, in one 0700 `run-<pid>-*` folder;
    - `--private-output` is passed on the one-line route only;
    - after each command the folder is gone.

    Fails: top-level tempfiles at 0644.
  - **PF-11:** the real renderer (no stand-in) in a folder `dash_pf11_<pid>` named from `c(tmpdir)` plus the Python pid. Modes, inodes and link targets are read from Python by value.
    0. Setup: `sysuse auto, clear`, `dash clear`, then `dash scatter mpg weight` under `$dash_nobrowser`, so the registry holds one graph. The runner's umask is read from Python (`os.umask` set and restored at once) and logged.
    1. `dash build, server saving(<dir>/pf11.py) replace` gives rc 0 and a 0600 `pf11.py` owned by the uid.
    2. A `pf11r.py` pre-created from Python at 0644 holding `OLD`, then the same command with `saving(<dir>/pf11r.py) replace`, gives rc 0 and a 0600 file holding `_DATA_B64`.
    3. A `pf11l.py` symlink to a 0644 victim `pf11v.txt` holding `V`: `capture noisily dash build, server saving(<dir>/pf11l.py) replace` gives rc 7102 (anti-hijack, M4a), the log names `refused to write` and `(it is a link)`, the victim still holds `V`, and `pf11l.py` is still a link.
    4. (Ratified 01oct2026.) The folder `<dir>` is set to 0777 from Python. `dash build, server saving(<dir>/pf11o.py) replace` gives rc 0 and a 0600 `pf11o.py`. `<dir>` is still 0777, so dash did not re-mode it. The command's log segment holds no `dash: note:` line naming `<dir>`.

    The folder is removed in every path. Fails: `0o644` in step 1, and in step 3 rc 0 with the victim overwritten.
  - **PF-12 (ratified 01oct2026): a shared `c(tmpdir)` proceeds with one note.**
    - **Setup.** The case reads `c(tmpdir)`'s mode from Python and logs it. It adds group write (`os.chmod(t, m | 0o020)`), which stands in for a STATATMP made under umask 002 (A14, §3a R6). The original mode is restored inside a `capture noisily { }` / restore / assert layout, so it comes back whatever fails. A log is captured around each command through the scaffold's helper.
    - **The routes:**
      1. the one-line form `dash scatter mpg weight` under `$dash_nobrowser`;
      2. `dash build, saving(<dir>/pf12.html) replace`;
      3. `dash build, server saving(<dir>/pf12.py) replace`, with the real renderer;
      4. `dash serve, nobrowser timeout(1)`, with PF-06's stand-in renderer first on the ado-path (removed after).
    - **Asserts for each route:**
      - rc 0;
      - exactly one line starting `dash: note:` in its segment, once SMCL wrap continuations are joined (PF-04's method);
      - that line holds the `c(tmpdir)` spelling, `chmod go-w` and `STATATMP`;
      - no `r(603)` and no `r(198)`.
    - **Further asserts.** For route 1, the newest preview of this pid is 0600 in a 0700 `previews/`. For route 3, `pf12.py` is 0600. For route 4, the stand-in's recorded `--spec`/`--data` are 0600 in a 0700 `run-<pid>-*`.
    - **Fails at the base:** no `dash: note:` line on any route.
- **PF-07**, `test/test_serve_launch.cscript`, after SPU-02 (task 08-04): on the `_srv_err` branch (SPU-02's stub, r(198)) no `run-<pid>-*` folder remains.
- **SRV-19 (flipped):** the stub saw `--output` = `<c(tmpdir)>dash-<uid>/run-<pid>-[A-Za-z0-9_]+/app.py`, and `--spec`/`--data` beside it as `spec.json`/`data.json`. After `dash serve` returns, the folder is gone. Fails: `St<pid>.<n>`.
- **PF-08**, `test/test_help_claims_4.cscript`, inside HC4-19's run: a second thread polls every 50 ms.
  1. It finds the new `run-<pid>-*` folder (absent from a snapshot taken before `dash serve`).
  2. It records `app.py`'s mode when first seen.
  3. Once `/health` answers, it records the folder's and the root's modes and whether `spec.json`/`data.json` exist.

  Asserts: the app was seen and was 0600; the folder and root are 0700; there is no spec or data. Fails: no run folder.
- **HC4-18 (strengthened):** also the app's folder is gone.
- **HC4-21 (strengthened):** a recursive walk of `c(tmpdir)`, limited to top-level `St<pid>.*` files and this session's `run-<pid>-*` folders and previews, finds no file newer than t0 holding `_DATA_B64 = `, `"graphs":` or `"variableNames"`, and no `run-<pid>-*` folder.
- **PF-09**, `test/test_adversarial.cscript`, after DL-06 (task 08-03). Flipped by the ratification (01oct2026): the planted root is no longer refused. It is left alone, which is the anti-hijack guard, and the command proceeds with one note.
  - **Setup.** Move `dash-<uid>` aside to `dash-<uid>-pf09-<pid>`. That name does not match the fallback pattern (the `-pf09-<pid>` suffix is not 8 characters from `[a-z0-9_]`), so it is never reused as a fallback. Then plant a symlink `dash-<uid>` pointing at an empty 0700 victim folder. Snapshot the `dash-<uid>-*` names first.
  - **Asserts:**
    - `capture noisily dash scatter mpg weight` under `$dash_nobrowser` gives rc 0;
    - the log has exactly one `dash: note:` line, joined as in PF-04, holding the planted path and `is not yours to use (it is a link)`;
    - the victim folder is still empty, and `dash-<uid>` is still a link;
    - one new `dash-<uid>-[a-z0-9_]{8}` folder exists. It is 0700, owned by the uid, and holds `previews/` with this pid's page at 0600;
    - `capture dash clear` returns 0 and leaves the victim empty;
    - afterwards the fallback holds no page of this pid, and it is gone once empty.
  - **Restore in every case**, and remove the new fallback folder with `shutil.rmtree` from Python.
  - **Fails at the base:** no `dash: note:` line. The base never looks at `dash-<uid>`, so the victim stays empty there too, and the note assertion is the failing one.
- **PF-10**, `test/test_env_guards.cscript`, after ENV-19 (task 08-03): with the probe answering "no Python", the three routes and `dash clear` add no `run-*` folder. The check compares `dir()` listings of every `c(tmpdir)dash-*` folder before and after, in Mata. Guard: it passes at the base, where routes make no run folder, and must stay green.
- **ENV-12 (flipped, task 08-08):** the program list becomes the programs holding `python:` lines in file order. Expected: `_dash_do_render _dash_empty_data _dash_write_data _dash_xm_load _dash_tmp_open _dash_tmp_preview _dash_tmp_close _dash_tmp_clear _dash_plot _dash_prepare_spec _dash_serve`. Copy the exact list from the script's own `ENV-12: programs running python:` log line, and keep the guard-before-first-python assertion for each.

### Cycle 2 (F2), `test/test_serve_lifecycle.py` (new; task 08-11)

- Tests: `TestTheParentWatch::{test_eof_on_stdin_asks_the_loop_to_stop, test_a_loop_that_does_not_stop_is_exited_after_the_grace, test_bytes_on_stdin_are_discarded_and_do_not_stop_it, test_no_stdin_prints_one_line_and_returns_none}`.
  - They use `os.pipe()` and a fake loop recording `add_callback(stop)`.
  - The grace test uses `grace=0.2` and an `_exit` recorder.
  - The bytes test writes 1 MiB including NUL and newlines.
  - All fail: AttributeError (`_dash_watch_parent`).
- Tests [serve]: `TestTheGeneratedAppWatchesStdin::{test_closing_stdin_stops_a_real_app, test_without_the_flag_stdin_is_ignored}`. Run `python app.py --port P --parent-watch` with `stdin=PIPE`; once `/health` answers, close it. Expect rc 0 within 5 s and `_port_free(P)`. Fails: rc 2, unrecognized argument.
- Tests: `TestTheLauncherStartsTheChildWatched::{test_the_child_gets_a_stdin_pipe_and_parent_watch, test_the_child_stays_in_statas_process_group}`. A fake Popen (with a `_RecStdin`) records the kwargs. The first test asserts `kw["stdin"] is subprocess.PIPE`, `cmd[:5] == [sys.executable, "-P", "-c", dr._DASH_BOOT, app]` and `"--parent-watch" in cmd[5:]`. Fails at commit 1: no `--parent-watch` (the stdin pipe and the bootstrap are already there, R-9).
- Tests [serve, skipif win32]: `TestTheServerDiesWithItsLauncher::{test_sigkill_of_the_launcher_stops_the_server, test_sigterm_of_the_launcher_stops_the_server}`.
  - A parent `python -c` runs runpy on `dash_render.py` with `_dash_serve`'s argv. The paths come from `dr._dash_run_open(str(tmp_path))`, with `--timeout 1` as a safety net and the box.
  - Once `/health` answers, signal the parent.
  - Expect `/health` refused within 5 s and `_port_free` within 5 s.
  - A `finally` kills any listener from `lsof -t -iTCP:<port> -sTCP:LISTEN`.
  - Fails: `/health` still 200.
- Tests [serve]: `TestNoCopyOfTheDataWhileServing::{test_spec_data_and_app_are_gone_once_health_answers, test_a_new_session_after_the_erase_is_served}`. The second uses `pull_session` with roots non-empty. Fails: `app.py` still there.
- Tests: `TestNoCopyOfTheDataWhileServing::{test_the_recompute_needs_no_file, test_the_app_never_reads_its_own_file}`. Both are guards that pass at commit 1 (A9 b, c).
  - The first execs the app source from a string after deleting the file, builds `make_document`, and moves a filter as `test_help_claims_4._served_filter_move` does.
  - The second asserts that the AST has no `__file__`, `sys.argv[0]`, `inspect.`, `linecache.`, `runpy.` or `open(`.
- Tests: `TestTheEraseRule::{test_the_app_is_erased_once_health_and_the_banner_arrive, test_health_without_the_banner_leaves_the_app, test_outside_a_private_run_folder_nothing_is_erased}`. They use a local `http.server` `/health` stub and a fake child whose stdout carries, or omits, `Bokeh Server running at`. Fails: TypeError (`erase_app_when_ready`).
- Test: `TestTheHelpSaysTheServerStopsWithStata::test_blocking_and_app_paragraphs`. Expects `stops by itself`, `measured on macOS` and `once the server answers`. Fails: absent.
- Extended (guard red until F2):
  - `test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads::test_no_function_in_the_app_reads_an_undefined_global`: a top-level walk skipping `^__\w+__$`, plus `"_dash_watch_parent"` in the tuple. Fails: `_dash_watch_parent` not defined.
  - `test/test_server_rate_limit.py::TestTheLauncherFlags::test_the_launcher_help_lists_every_flag`: `--parent-watch`.
- **LC-01**, `test/test_help_claims_4.cscript`, in HC4-19's run: within 5 s of the first `/health` 200, while `dash serve` still blocks, the session's run folder holds no file. Polled every 0.1 s; the names left are reported. Fails: `app.py` left.
- Flipped: `test/test_help_claims_4.py::TestTheRealHandoffServes::test_it_serves_and_stops`.

### Cycle 3 (F4), `test/test_serve_lifecycle.py` (task 08-15)

- Tests: `TestTheStataPoller::{test_inside_stata_it_returns_pollstd_and_break_error, test_outside_stata_it_returns_nothing}`.
- Tests: `TestTheLauncherPollsStata::{test_pollstd_is_called_while_it_waits, test_break_closes_stdin_stops_the_child_and_raises_interrupted, test_a_child_that_ignores_the_close_is_terminated_then_killed, test_break_during_the_build_starts_no_child, test_a_break_pending_when_the_child_exits_is_reported, test_keyboard_interrupt_outside_stata_stops_the_same_way, test_break_before_health_answers_is_not_swallowed, test_an_interrupt_between_popen_and_the_loop_stops_the_child, test_a_second_interrupt_during_the_stop_still_kills, test_a_child_exiting_130_is_an_interrupt_and_a_timeout_is_not}`.
  - A stub `sfi` goes in through `monkeypatch.setitem(sys.modules, "sfi", stub)`.
  - Fakes record `stdin.close`, `wait(timeout)`, `terminate` and `kill`.
  - Fails: 0 `pollstd` calls; the launcher returned normally.
- Test [serve]: `TestTheLauncherPollsStata::test_a_real_server_stops_on_break`. The stub `pollstd` raises once `/health` answers. Expect interrupted within 10 s, `/health` refused and `_port_free`.
- Tests: `TestTheLaunchReportBox::{test_an_interrupt_lands_in_the_box, test_without_a_box_an_interrupt_exits_130, test_the_interrupt_is_not_a_runtime_error, test_keyboard_interrupt_during_the_build_lands_in_the_box}`.
- Tests: `TestTheStopHint::{test_inside_stata_the_ready_line_names_break, test_outside_stata_it_names_ctrl_c}`.
- Tests [serve]: `TestTheAppBanner::{test_parent_watch_prints_no_ctrl_c_line, test_parent_watch_exits_130_on_sigint}`.
- Test: `TestTheHelpNamesBreak::test_syntax_description_timeout_and_blocking_paragraph`.
- Test: `TestTheAdoEndsWithROne::test_serve_reads_interrupted_closes_and_errors_1`.
- **LC-02**, `test/test_serve_launch.cscript`: a stub renderer sets `_dash_launch_report["interrupted"] = True`. `dash serve` gives rc 1; the log has no `Traceback` and no `r(7102)`; there is no `run-<pid>-*` folder. Fails: rc 0.
- **LC-03:** a real launch.
  - A `python:` block replaces `sfi.SFIToolkit.pollstd` with a function that raises `sfi.BreakError` once a thread has seen `/health` answer. It restores the original first; the case also restores it after.
  - `capture noisily dash serve, port(p) timeout(1) nobrowser` gives rc 1 in under 40 s.
  - Afterwards the port binds with SO_REUSEADDR, and no run folder of this session remains.
  - This tests dash's catch and `error 1`, not Stata's Break key (A11).
  - Fails: rc 0 after about 60 s.
- **LC-04:** with a stub renderer, the log holds `press Break (Ctrl+C in console Stata)` and not `Stata is blocked until the server stops (Ctrl+C)`. Fails.
- LC-02 to LC-04 go after PF-07 and before SRV-19, which replaces `_dash_find_render` for good. Names are built from `c(tmpdir)` and the Python pid: no `tempfile`/`tempname` draws (the SPU-01 note at :513-516).
- Adjusted: `test/test_serve_launcher.py` fakes (Evidence §6).

### Mutation table

| Break this | Test that must die |
|---|---|
| drop `O_NOFOLLOW` from the writer | `TestTheDataFileIsPrivate::test_a_symlink_at_the_path_is_not_followed` |
| drop `O_NONBLOCK` | `…::test_a_fifo_at_the_path_is_refused_without_blocking` |
| skip `fchmod(0o600)` | `…::test_a_preexisting_world_readable_file_of_ours_is_made_0600` |
| `main()` builds the server app with `private=launch` (u11b's narrowing of M4) | `TestTheServedAppIsPrivate::test_a_dash_build_server_app_is_0600`, PF-11 |
| skip `_dash_private_clear_name` and write in place without `O_EXCL` | `TestTheServedAppIsPrivate::test_replacing_a_server_app_writes_a_new_0600_file` |
| `os.stat` instead of `os.lstat` in `_dash_private_clear_name` | `TestThePrivateClearName::test_a_link_is_refused_and_kept`, `TestTheServedAppIsPrivate::test_a_link_at_a_server_app_path_is_refused_and_its_target_kept` |
| clear the name before the source is complete | `TestTheServedAppIsPrivate::test_a_refused_port_leaves_an_existing_server_app_untouched` |
| realpath the root | `TestThePrivateRoot::test_a_base_reached_through_a_symlink_gives_paths_the_caller_can_match`, HC4-18 |
| sweep by age on POSIX | `TestTheRunDir::test_age_never_removes_a_live_pids_run_on_posix` |
| treat PermissionError as dead | `TestTheRunDir::test_the_sweep_treats_permission_error_as_alive` |
| prune other pids' young pages | `TestThePreviews::test_a_live_other_sessions_pages_survive_prune_and_clear` |
| `_dash_tmp_close` omitted in `_dash_serve`'s error branch | PF-07 |
| `poll()` inside the urlopen try | `TestTheLauncherPollsStata::test_break_before_health_answers_is_not_swallowed` |
| `_DashServeInterrupted(RuntimeError)` | `TestTheLaunchReportBox::test_the_interrupt_is_not_a_runtime_error`, LC-02 |
| erase on `/health` alone | `TestTheEraseRule::test_health_without_the_banner_leaves_the_app` |
| watch thread not started | `TestTheServerDiesWithItsLauncher::test_sigkill_of_the_launcher_stops_the_server` |
| raise for a shared base instead of noting it (the struck r(603)) | `TestThePrivateRoot::test_a_writable_non_sticky_base_proceeds_with_a_note_naming_chmod`, PF-12 |
| use (follow) a planted `dash-<uid>` instead of the fallback | `TestThePrivateRoot::test_a_symlinked_root_is_left_alone_and_a_fallback_is_used`, PF-09 |
| reuse any `dash-<uid>-*` without the owner and 0700 check | `TestThePrivateRoot::test_a_fallback_root_is_reused_only_when_it_is_ours_and_0700` |
| let a failed `fchmod` propagate from the writer (the struck r(198)) | `TestTheDataFileIsPrivate::test_a_file_whose_mode_cannot_be_set_is_written` |
| `_dash_tmp_preview` prints its note whatever `noted()` says | `TestTheAdoUsesThePrivateDir::test_the_note_is_printed_once_per_command`, PF-12 (route 1) |
| renderer notes a file in a folder dash chose | `TestTheNote::test_a_file_in_a_folder_dash_chose_is_never_noted_by_the_renderer` |
| drop the identity comparison in `_dash_read_verified_app` | `TestTheLaunchFromTheOpenFile::test_a_substituted_app_is_not_started` |
| start the child by path again (`[sys.executable, app_path, …]`) | `TestTheLaunchFromTheOpenFile::test_a_path_swapped_after_verification_does_not_change_what_runs`, `…::test_the_child_is_handed_the_verified_bytes_not_the_path` |
| re-open the path after the checks (read with `open(app_path)` instead of the descriptor) | `TestTheLaunchFromTheOpenFile::test_a_swap_between_open_and_read_reads_the_original` |
| skip the SHA-256 comparison | `TestTheLaunchFromTheOpenFile::test_the_same_file_rewritten_in_place_is_refused` |
| drop `O_NOFOLLOW` (or `O_NONBLOCK`) from the launcher's open | `TestTheLaunchFromTheOpenFile::test_a_link_or_fifo_at_the_app_path_is_refused_without_expect` |
| drop `-P` from `_cmd` | `TestTheLaunchFromTheOpenFile::test_no_module_beside_the_app_or_in_the_working_folder_is_imported`, `TestTheBootstrap::test_neither_the_working_folder_nor_the_apps_folder_is_on_sys_path` |
| read the frame through `sys.stdin` (buffered) in the bootstrap | `TestTheBootstrap::test_bytes_after_the_frame_are_left_on_stdin` |
| skip the bootstrap's digest check | `TestTheBootstrap::test_a_damaged_or_short_frame_runs_nothing`, `TestTheBootstrap::test_a_crlf_translated_frame_runs_nothing` |
| drop the Windows `lstat` check (TR-08.8a step 1) from `_dash_read_verified_app` | `TestWindowsPortability::test_a_reparse_point_is_refused_on_windows` |
| read `os.O_NOFOLLOW` (or another `O_` flag) or call `os.getuid()` without `getattr` in `_dash_read_verified_app` | `TestWindowsPortability::test_the_verified_read_works_without_O_NOFOLLOW_and_getuid` |
| a hand-over failure leaves the child running | `TestTheLaunchFromTheOpenFile::test_a_child_that_cannot_take_the_app_is_stopped_and_reported` |
| `_dash_run_close` skips the fallback root's `rmdir` | `TestTheRunDir::test_close_removes_an_empty_fallback_root_and_keeps_one_holding_a_preview` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Data, spec, app and preview are 0600, never through a link, FIFO or foreign file | pytest `test_private_files.py` | none | saved (preview) and served (app) |
| Private root and run-folder rules, sweep, close | pytest | none | n/a (shared) |
| Preview naming, keep-five, grace, other sessions, ceiling, clear | pytest; PF-02, PF-04 | none | saved |
| Ado routes open, write by value and close; guard placement; log noise | pytest source tests; PF-06; ENV-12; PF-10 | none | both routes |
| Unsafe locations proceed with one note per command; a planted root is left alone for a 0700 fallback (ratified 01oct2026) | pytest `TestThePrivateRoot`, `TestTheRunDir`, `TestThePreviews`, `TestTheNote`; PF-09, PF-12 | none | saved (one-line, build) and served (`dash serve` in PF-12 route 4; pytest) |
| Anti-hijack refusals r(7102) on every route; launch from the open file (round 2) | pytest `TestTheDataFileIsPrivate`, `TestThePrivateClearName`, `TestTheLaunchFromTheOpenFile`, `TestTheBootstrap`; PF-11 step 3 | none | both |
| A user-named folder that others can read is not refused, re-moded or noted | pytest `test_a_user_named_folder_that_others_can_read_is_neither_refused_nor_remoded`; PF-11 step 4 | none | served (the `.py`) |
| dash runs only what it wrote (round 2, R-9). It covers a deterministic swap between verification and Popen, a swap between open and read, an in-place rewrite, a link, FIFO or foreign app, and modules planted beside the app or in the working folder. The bootstrap behaves as a script run: `__main__`, argv, tracebacks, exit statuses and stdin left after the frame. The Windows branch (no `O_NOFOLLOW` or `os.getuid`; a link or reparse point refused by `lstat`) and a CRLF-translated frame are run on macOS | pytest `TestTheLaunchFromTheOpenFile` (one [serve] test), `TestTheBootstrap`, `TestWindowsPortability`; every real launch (`TestServeBlocksUntilCtrlC`, `TestServingBlocksUntilInterrupted`, `TestTheRealHandoffServes`, HC4-19, PF-08, LC-01, LC-03, `TestTheServerDiesWithItsLauncher`) now goes through the bootstrap | none | served |
| twoway parity: twoway leaves nothing; named-page modes equal | PF-01, PF-03 | none (live Stata) | saved |
| A user-named server app is 0600, replaced by a new file, never written through a link or a foreign file (M4, R-7) | pytest `TestTheServedAppIsPrivate`, `TestThePrivateClearName`; PF-11 | none | served (the `.py` is the served app) |
| dash serve app in the run folder, removed after; files private while serving | SRV-19, PF-07, PF-08, HC4-18, HC4-21 | none | served |
| The served app writes no file after a filter move | pytest AST guard | none | served |
| Server dies with its launcher (KILL, TERM), stdin EOF, hard exit | pytest [serve] | none | served |
| No data on disk while serving; new session and recompute after the erase | pytest [serve]; LC-01 | none | served |
| Break polled, swallowed nowhere, r(1), stop escalation, messages | pytest; LC-02..LC-04 | none | served |
| Help text | pytest | none | n/a |
| Acceptance outside the suite: real KILL, TERM and INT against batch Stata | `run_sig.py`/`post.sh` re-created in `<scratch>` (task 08-19) | none | served |

Acceptance criteria:
- **AC-08.1** `python3 -m pytest test/test_private_files.py test/test_serve_lifecycle.py test/test_string_value_export.py test/test_immediate_dashboards.py test/test_serve_launcher.py test/test_help_claims_2.py test/test_help_claims_4.py test/test_server_rate_limit.py test/test_resource_limits.py test/test_function_test_map.py test/test_program_coverage_map.py test/test_tracking_documents.py test/test_server_build_returns.py -q` passes with no new skips.
- **AC-08.2** Through the driver, the following print every PASS line, with 0 `FAIL` and 0 `^r([0-9]*);` lines:
  - the S08 block of `test_wp29_truth.cscript` (PF-01..PF-06, PF-11, PF-12);
  - `test_serve_launch.cscript` (PF-07, LC-02..LC-04, SRV-19);
  - `test_help_claims_4.cscript` (HC4-18..21, PF-08, LC-01);
  - `test_adversarial.cscript` (PF-09);
  - `test_env_guards.cscript` (ENV-12, PF-10).
- **AC-08.3** In BUGS.md the P0.12b, P0.14 and P0.13 entries are closed in place, with `(WP-29, P0.12b)`, `(WP-29, P0.14)` and `(WP-29, P0.13)` Resolutions naming existing tests. Their `WP29_OPEN` keys are gone. `grep -c '<!-- WP-29 P0.1[234]b\? -->' CHANGELOG.md` prints 0.
- **AC-08.4** The re-run acceptance after commit 3 prints, for KILL and TERM, `health: 000`, no listener and no file holding the data under `c(tmpdir)`, and for INT `dash serve returned rc=1`.
- **AC-08.4a (ratified 01oct2026)** No privacy condition ends a command with an error:
  - `grep -c "exit 603" dash.ado` prints 3. At 7421d3d it printed 1 (measured: `584:    exit 603`, the `saving()` path check after "could not be opened"). The two new lines are the `_to_err`/`_tp_err` exits of `_dash_tmp_open` and `_dash_tmp_preview`;
  - `python3 -m pytest test/test_private_files.py -q -n0 -k "proceeds or left_alone or Note or mode_cannot_be_set or LaunchFromTheOpenFile or Bootstrap or neither_refused"` passes;
  - PF-09 and PF-12 print `PASS`.
- **AC-08.4b (ratified 01oct2026, round 2)** dash runs only the application it wrote:
  - `grep -c "subprocess.Popen(" dash_render.py` prints 1, the launcher's;
  - `grep -n "sys.executable, app_path" dash_render.py` prints nothing, and `grep -c '"-P", "-c", _DASH_BOOT' dash_render.py` prints 1;
  - `python3 -m pytest test/test_private_files.py -q -n0 -k "LaunchFromTheOpenFile or Bootstrap"` passes, including the [serve] test `test_a_path_swapped_after_verification_does_not_change_what_runs`;
  - the help states it: `TestTheHelpDocumentsTheTempfiles::test_it_says_dash_serve_runs_the_text_it_checked` passes;
  - every real launch still serves: `python3 -m pytest test/test_help_claims_1.py -q -k ServeBlocksUntilCtrlC` and `python3 -m pytest test/test_help_claims_4.py -q -k RealHandoff` pass, and HC4-19 and PF-08 print `PASS`.
- **AC-08.5** `git log -3 --format=%s wp29-s08` shows the three subjects ending `(WP-29 P0.12b, P0.14)`, `(WP-29 P0.13 F2)` and `(WP-29 P0.13 F4)`, oldest first. No message matches `claude|anthropic`.

## Tasks

Commit boundary. There are three commits on the worktree branch `wp29-s08` (worktree `<wt>` = `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s08`), each made after one full pytest run in the worktree:

| Commit | Tasks | Subject ends | Body opens with |
|---|---|---|---|
| 1 | 08-02..08-10 | `(WP-29 P0.12b, P0.14)` | `<scratch>/08-P0.12b-failure.txt` |
| 2 | 08-11..08-14 | `(WP-29 P0.13 F2)` | `<scratch>/08-P0.13-F2-failure.txt` |
| 3 | 08-15..08-19 | `(WP-29 P0.13 F4)` | `<scratch>/08-P0.13-F4-failure.txt` |

- **Gate.** 08-01 gates the section. It copies the rows ratified on 01oct2026 and no longer asks the maintainer.
- **Commit bodies** then carry `Regression:`, `Flipped:` and `BUGS.md: "<title>" (closed)` lines (index BR form). No AI reference anywhere.
- **The full suite.** The hook `.claude/hooks/guard-full-suite.sh` refuses a third full launch in one session, so the third run is prefixed `FULL_SUITE_RERUN=1`. The full-suite lock `/tmp/dash-full-suite-<uid>.lock` is shared by every worktree: if another section's full run holds it, wait for it and do not start a second.
- **Stata** runs only through the driver in "Stata truth".

<task type="auto" id="08-01">
  <name>Copy the ratified decisions</name>
  <files>none (writes only `<scratch>/08-decisions.txt`)</files>
  <action><![CDATA[
    The maintainer ratified this section's decisions on 01oct2026, before step 1 (index "Decisions for maintainer ratification"). Do not ask again.
    1. Read `<scratch>/wp29-ratified.txt`.
    2. Copy into `<scratch>/08-decisions.txt`, verbatim, the rows `S08 R-1`, `S08 R-3`, `S08 R-5`, `S08 R-6` and `S08 codes`, together with the maintainer's answer 2. Do not retype the answer: copy its line from the record with `grep -F 'Allow "unsafe" temp directory locations' <scratch>/wp29-ratified.txt >> <scratch>/08-decisions.txt`. It must read exactly as index.md's verbatim record (line 69): 2. "Allow "unsafe" temp directory locations and do not refuse writing the app files into a directory of the user's that is not private."
    3. Below them, add one line per decision this section applies:
       - `R-1 ratified`, `R-3 ratified`, `R-5 ratified`, `R-6 ratified`;
       - `R-7 ratified: every server app is 0600; the folder the user names is never refused, re-moded or noted`;
       - `S08 codes struck -> R-8: no privacy refusal (proceed, 0600 where the disk allows, one note per command); a planted dash-<uid> is left alone for a 0700 fallback root; anti-hijack refusals (link, FIFO/device, other hard links, another account's file, replaced app) end r(7102); only an operating-system failure to create the folder ends r(603)`.
    3a. (Round 2.) Copy the row `S08 launch route` and the round-2 answer B line verbatim (`grep -F 'Launch from open file' <scratch>/wp29-ratified.txt >> <scratch>/08-decisions.txt`), then add `S08 launch route struck -> R-9: launch from the open, verified file (python -P -c _DASH_BOOT, framed stdin hand-over); _dash_same_file withdrawn`. If the row is missing, reads "pending", or its answer is not "Launch from open file", stop before any edit and report it, because R-9 and its tests were planned on that answer.
    4. If any of the five rows or answer 2's line is missing from `<scratch>/wp29-ratified.txt`, or a row reads "pending", stop before any edit and report "step 1 has been broken: <row> is not ratified".
  ]]></action>
  <verify><![CDATA[For each of `S08 R-1`, `S08 R-3`, `S08 R-5`, `S08 R-6`, `S08 codes` and `S08 launch route`, `grep -c -F '<id>' <scratch>/08-decisions.txt` prints at least 1, and `grep -c 'S08 launch route struck -> R-9' <scratch>/08-decisions.txt` prints 1. `grep -c 'pending' <scratch>/08-decisions.txt` prints 0. `grep -c 'S08 codes struck -> R-8' <scratch>/08-decisions.txt` prints 1. `diff <(grep -F 'Allow "unsafe" temp directory locations' <scratch>/08-decisions.txt) <(grep -F 'Allow "unsafe" temp directory locations' <scratch>/wp29-ratified.txt)` prints nothing and exits 0, and that line ends `not private."` (the answer is the record's line, not a retyped one).]]></verify>
  <done>The ratified rows and the section's reading of them were on record before any file was edited.</done>
</task>

<task type="auto" id="08-02">
  <name>Write the failing private-file pytest</name>
  <files>test/test_private_files.py</files>
  <action><![CDATA[
    Preflight, in `<wt>`: `grep -c '<!-- WP-29 P0.12b -->' CHANGELOG.md` must print 1 and `test/test_wp29_truth.cscript` must exist; if not, run `git -C <wt> cherry-pick $(git -C <wt> log -1 --format=%H wp29-s01)` (S01's commit; wait for it if branch wp29-s01 has no commit yet). Record `git -C <wt> rev-parse HEAD` as the cycle base in `<scratch>/08-cycle1-base.txt`. Run `npx gitnexus analyze` in `<wt>`, then `gitnexus_impact({target, direction: "upstream"})` for `main`, `ServerAppBuilder.build`, `_dash_write_stata_data`, `_validate_output_path` and `_dash_launch_app`; save the output to `<scratch>/08-impact.txt` and report any HIGH or CRITICAL to the maintainer before task 08-05 edits that symbol. Create `test/test_private_files.py` with every test of "TDD test stubs, Cycle 1, test/test_private_files.py" under exactly those class and test names. Use `FakeSfi`, `_fake_auto` and `_write` from `test_string_value_export`, and `_SPEC`/`_DF`/`make_data_json` as `test_serve_launcher` does. Set umasks only through a `try/finally` helper `_umask(mask)`. Make each test fail on an assertion, never a collection error: reach new names with `getattr(dr, "<name>")` inside the test. Run `python3 -m pytest test/test_private_files.py -q -n0 -p no:cacheprovider 2>&1 | tail -60 > <scratch>/08-P0.12b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_private_files.py -q -n0 2>&1 | tail -3` shows failures and no `error` during collection. Exactly four tests pass, the guards `test_the_generated_app_has_no_file_writing_call`, `test_a_user_named_page_follows_the_umask`, `test_a_refused_port_leaves_an_existing_server_app_untouched` and `test_a_file_whose_mode_cannot_be_set_is_written` (ratified 01oct2026). `test_a_symlinked_root_is_left_alone_and_a_fallback_is_used` and `test_a_writable_non_sticky_base_proceeds_with_a_note_naming_chmod` fail with AttributeError. In `TestTheLaunchFromTheOpenFile` (round 2), `test_a_path_swapped_after_verification_does_not_change_what_runs` fails with the marker holding `EVIL RAN`, `test_no_module_beside_the_app_or_in_the_working_folder_is_imported` with the marker holding `linecache`, `test_the_child_is_handed_the_verified_bytes_not_the_path` on `cmd[1] == out`, and no listener is left (`lsof -iTCP -sTCP:LISTEN | grep -c python` is unchanged from before the run). `TestTheBootstrap` fails with AttributeError (`_DASH_BOOT`), `test_a_crlf_translated_frame_runs_nothing` included. In `TestWindowsPortability`, `test_the_verified_read_works_without_O_NOFOLLOW_and_getuid` and `test_a_reparse_point_is_refused_on_windows` fail with AttributeError. `test_a_dash_build_server_app_is_0600` fails with `0o644`/`0o664`, and `test_a_link_at_a_server_app_path_is_refused_and_its_target_kept` with the victim overwritten. No test named `test_a_dash_build_server_app_follows_the_umask` exists (R-7). Every `TestTheAdoUsesThePrivateDir` test first asserts that the programs it reads exist (`_dash_xm_load`, `_dash_tmp_open`, `_dash_tmp_preview`, `_dash_tmp_close`, `_dash_tmp_clear`), so none passes vacuously. The data-file tests fail with `0o644` and `0o664`, and the symlink, hard-link, FIFO and foreign-file tests with `DID NOT RAISE` (the victim overwritten). `<scratch>/08-P0.12b-failure.txt` and `<scratch>/08-impact.txt` exist.]]></verify>
  <done>Every P0.12b/P0.14 pytest regression test existed and failed for its recorded reason on the unmodified tree, with the blast radius recorded and nothing committed.</done>
</task>

<task type="auto" id="08-03">
  <name>Write the failing PF certification cases</name>
  <files>test/test_wp29_truth.cscript, test/test_adversarial.cscript, test/test_env_guards.cscript</files>
  <action><![CDATA[
    In `test/test_wp29_truth.cscript`, append the S08 block of "Stata truth" above `* ==== append new blocks above this line ====`, after any earlier section's block. It holds PF-01 to PF-06, PF-11 and PF-12 exactly as "TDD test stubs, Cycle 1, certification cases" specify, each through the scaffold's tally helpers (read the scaffold's header for their names) and never `exit`ing on a failure. PF-06's stand-in renderer is written with `file write`, into a folder named from `c(tmpdir)` plus the Python pid (`dash_pf06_<pid>`). It parses argv by `index()` and writes the output with a plain `open`. It is put first with `adopath ++` and removed with `adopath -` in every path. PF-12 reuses that stand-in only for its `dash serve` route. Its `c(tmpdir)` chmod is made and undone from Python inside `capture noisily { }`, followed by the restore and then the asserts, so the slot's folder always gets its mode back. In `test/test_adversarial.cscript`, append PF-09 (the ratified form: rc 0, one note, the victim empty, a 0700 fallback root) after DL-06 (before `// Final summary`) and its summary line at the end; the restore runs whether or not the check failed (the check sits in `capture noisily { }`, then restore, then asserts). In `test/test_env_guards.cscript`, add PF-10 directly after `ENV-19 PASS` (:468), comparing Mata `dir()` listings of the `run-*` folders under every `c(tmpdir)dash-*` folder, taken before the stubbed routes run and after them. Wrap every call to a program that does not exist on the unmodified tree (`_dash_xm_load`, `_dash_tmp_*`) in `capture noisily` and record a nonzero rc as that case's FAIL, so each block runs to its end. Run each script through the driver (`WP29_ONLY=S08` for the truth script) and append the FAIL and PASS lines to `<scratch>/08-P0.12b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[In `<scratch>/stata/run_test_wp29_truth.log`: PF-02, PF-04, PF-05, PF-06, PF-11 and PF-12 print `FAIL` (PF-11 with `0o644` and the victim overwritten; PF-12 with no `dash: note:` line), and PF-01 and PF-03 print `PASS`. The log also shows `c(tmpdir)`'s mode restored after PF-12: the logged before and after modes are equal. In the adversarial log PF-09 fails with no `dash: note:` line. In the env-guards log `PF-10 PASS` appears and the script otherwise ends as before.]]></verify>
  <done>The PF certification cases existed in their scripts and failed where the defect lives, with the twoway guards passing.</done>
</task>

<task type="auto" id="08-04">
  <name>Flip and add the serve cscript cases</name>
  <files>test/test_serve_launch.cscript, test/test_help_claims_4.cscript</files>
  <action><![CDATA[
    In `test/test_serve_launch.cscript`, add PF-07 right after `SPU-02 PASS` (:592), checking from Python that no `run-<pid>-*` folder is left under `c(tmpdir)dash-<uid>`. Rewrite SRV-19 (:612-672) to assert "TDD test stubs"' SRV-19 form. Keep its stub and its `_dash_find_render` replacement. Take uid and pid from Python, `tmpdir` from a global set to `c(tmpdir)`, and match with `re.fullmatch(re.escape(os.path.join(tmpdir, "dash-%d" % uid)) + re.escape(os.sep) + r"run-%d-[A-Za-z0-9_]+" % pid + re.escape(os.sep) + r"app\.py", out)`. Update the header comment lines 33-41. In `test/test_help_claims_4.cscript`, strengthen HC4-18 (:476-478; add the folder-gone check) and HC4-21 (:540-564; the recursive, session-limited walk with the three needles). Add PF-08 to HC4-19's python block (:510-533) as a second daemon thread `_pf08_watch` that snapshots existing `run-<pid>-*` names before `dash serve`, and assert it after `HC4-21 PASS`. Update the HC4-16..18 header comment (:436-437). Run both scripts through the driver and append their FAIL lines to `<scratch>/08-P0.12b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[In `<scratch>/stata/run_test_serve_launch.log` SRV-19 fails, with the app shown as `…/St<pid>.<n>`, and PF-07 fails because no root exists. In `<scratch>/stata/run_test_help_claims_4.log` PF-08 fails (no run folder seen) and HC4-18 fails on the folder check.]]></verify>
  <done>SRV-19, HC4-18 and HC4-21 pinned the private layout, PF-07 and PF-08 existed, and all failed on the unmodified tree with their reasons recorded.</done>
</task>

<task type="auto" id="08-05">
  <name>Add the private-file helpers to the renderer</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    After `_dash_write_stata_data` (ends at about :1484) and before `_DASH_ADO_ENTRY_POINTS`, add TR-08.1 to TR-08.7 and TR-08.9's two text entry points exactly as specified: the constants, `_DashUnsafePath`, `_dash_root_name`, `_dash_mode_private`, `_dash_private_msg`, `_dash_private_root`, `_dash_fallback_root`, `_dash_own_root`, `_dash_private_dir_ok`, `_dash_private_write`, `_dash_pid_alive`, `_dash_run_open`, `_dash_run_sweep`, `_dash_run_close`, `_dash_erase_quietly`, `_dash_private_run_of`, `_dash_private_clear_name` (TR-08.6a), `_dash_chosen_path`, `_dash_preview_path`, `_dash_prune_previews`, `_dash_tmp_write_text` and `_dash_tmp_clear`. Each gets a docstring naming the threat it closes, its R-8 class (privacy: proceed and note; anti-hijack: refuse; operating system: error) and the measurement (D4-D9, U2, A2-A6, §3a). No privacy condition raises. Import `errno`, `secrets`, `shutil`, `stat` and `tempfile` at module top if they are absent, and `fcntl` inside the writer in a try. Replace the final write of `_dash_write_stata_data` (1482-1483) with TR-08.9's block and set `_DASH_ADO_ENTRY_POINTS` to the six entry points. Add the commit-1 keys of TR-08.20 to `test/function_test_map.py`, each naming its focused `test_private_files.py` test. Then run `python3 scripts/fncov/fncov_mutate.py --map` limited to the new keys (see its `--help` for the key filter) and replace any entry whose test survives the mutation.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_private_files.py -q -k "DataFileIsPrivate or PrivateRoot or RunDir or Previews or SpecWriter or writer_and_root_work_without or erase_quietly or private_run_of or PrivateClearName or mode_private" -n0` passes. (`TestWindowsPortability`'s two round-2 tests need `_dash_read_verified_app`, which lands in task 08-06, and are verified there.) `grep -n "raise _DashUnsafePath" dash_render.py` lists only the anti-hijack sites of TR-08.3, TR-08.6a and TR-08.8. None of them is in `_dash_private_root` or `_dash_fallback_root`. `python3 -m pytest test/test_function_test_map.py -q -n0` passes, and the mutation run reports every new key's test failing under mutation.]]></verify>
  <done>The renderer had a private root, a link- and FIFO-proof 0600 writer, run folders with a pid-safe sweep and close, and pruned private previews, each unit-tested and mutation-checked.</done>
</task>

<task type="auto" id="08-06">
  <name>Write the app and preview privately, and launch it from the open file</name>
  <files>dash_render.py, test/function_test_map.py, test/test_server.py, test/test_help_claims_4.py, test/test_serve_launcher.py, test/test_help_claims_2.py</files>
  <action><![CDATA[
    Apply TR-08.8. `ServerAppBuilder.build` (29088) gains `private=False`; when private, once the source is complete, it calls `_dash_private_clear_name(output_path)` and then `st = _dash_private_write(output_path, source, exclusive=True)` and returns `_DashWrittenApp(st, <sha256 of source's UTF-8>)`. `main()` returns that value in server mode and prints the R-8 (d) note when `not _dash_mode_private(written.st) and not _dash_chosen_path(output_path)`. Apply TR-08.8a (round 2, R-9): add `_DashWrittenApp`, `_DASH_BOOT` (its import-time assert included), `_dash_read_verified_app`, `_dash_app_frame`, `_dash_child_stdin` and `_dash_hand_over` beside `_dash_launch_app`, each with a docstring naming U2, §3b A/C and the anti-hijack class. In `_dash_launch_app` (31944): the keyword `expect=None`; the verified read and the frame right before Popen; `_cmd = [sys.executable, "-P", "-c", _DASH_BOOT, app_path, "--port", str(port)]` in place of 31992; `stdin=subprocess.PIPE`; the hand-over right after the pump threads start, with its stop-and-raise on failure; and `proc.stdin.close()` after the final wait. Rewrite its docstring: the child runs the verified bytes, never the path. `__main__` keeps `_written = main(…)` and passes `expect=_written` in its launch block. Add the four round-2 keys of TR-08.20 to `test/function_test_map.py` and mutation-check them. Give the launcher fakes a stdin, an adjustment with no assertion changed: `test/test_serve_launcher.py`'s `_fake_popen_class` (:99-131) and the two inline `_FakeProc`s (:241-312), and `test/test_help_claims_2.py::_FakeProc` (:765-790), each get `self.stdin = _RecStdin()` (a local copy of `test_private_files._RecStdin`). Record each as `Adjusted: <node> -- the launcher now hands the app to the child on its stdin (R-9)` in `<scratch>/08-c1-flips.txt`. `main()` (31888) gains `private_output=False`. It builds every server app with `private=True`: launch, `dash build, server` and the command line (M4, R-7). When launch, it also computes `run = _dash_private_run_of(output_path)` and erases spec and data only under the TR-08.8 rule. The standalone page goes through the private writer only when `private_output`. `main()` does not catch `_DashUnsafePath` and never raises SystemExit for it (M4a, M4b). Update the docstrings of `main` and `_validate_output_path` (31794-31815) to describe the run folder and keep the extension-less launch rule. Add `--private-output` to `__main__`'s parser (after `--launch`, about 32148-32157) and pass it to `main`. Change nothing else in `__main__`. Then update two descriptions; they are comments, not assertions. First, the docstring of `test/test_server.py::TestServeUniqueAppPath` (:10750-10764): SRV-19 now requires `app.py` in a run folder of the session, and `build()` still writes wherever it is told. Second, the comment at `test/test_help_claims_4.py:1305-1320`: `dash serve` hands the renderer `app.py` in a private run folder, and `TestTheOutputPathRule` stays for command-line users.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_private_files.py -q -k "ServedAppIsPrivate or SavedPreviewIsPrivate or WritesNoFile or TestTheNote or LaunchFromTheOpenFile or Bootstrap or WindowsPortability" -n0` passes, and no listener is left (`lsof -iTCP -sTCP:LISTEN | grep -c python` is unchanged from before the run). `python3 -m pytest test/test_serve_launcher.py test/test_help_claims_2.py test/test_server_build_returns.py -q` passes. The real launches pass through the bootstrap: `python3 -m pytest test/test_help_claims_1.py test/test_help_claims_5.py test/test_help_claims_4.py -q -k "ServeBlocksUntilCtrlC or RealHandoff or ServingBlocksUntilInterrupted"`. `python3 -m pytest test/test_serve_launcher.py test/test_help_claims_4.py -q -k "OutputPathRule or LaunchReportBox or PortRefusals"` passes. `python3 -m pytest test/test_server.py -q -k UniqueAppPath` passes. The tests that call `dr.main(…, mode="server")` on paths of their own, now on the private route, pass unchanged: `python3 -m pytest test/test_render_cli_port.py::TestPortReachesTheGeneratedApp test/test_resource_limits.py -q -k "PortReachesTheGeneratedApp or port_is_refused_in_every_place"`.]]></verify>
  <done>Every server app was written 0600 by an exclusive, link-refusing create: dash serve's in its run folder, with its spec and data erased only inside dash's own run folder, and dash build, server's at the path the user named. The preview page was 0600 behind `--private-output`, and named pages still followed the umask. A `.py` the disk would not keep at 0600 was written and noted once. A user-named folder was never refused or re-moded. dash started its app from the bytes it read through a descriptor it verified, under `python -P`, so a file or folder swapped in afterwards never ran and no planted module was imported.</done>
</task>

<task type="auto" id="08-07">
  <name>Route dash.ado through the private folder</name>
  <files>dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-08.10 items 1-9 in dash.ado. Factor `_dash_xm_load` out of `_dash_write_data` (4315-4350, moved verbatim). Add `_dash_tmp_open`, `_dash_tmp_preview`, `_dash_tmp_close` and `_dash_tmp_clear` after `_dash_write_data`, each with a header comment citing D1-D9, A7, A11 and R-8. `_dash_tmp_open` prints `_to_note` (privacy, never an error) and returns `noted`. `_dash_tmp_preview` takes `NOTED(string)` and prints its note only when `noted` is not `1`. The only `exit 603` lines are their `_to_err`/`_tp_err` exits, commented as the operating-system class. The spec and empty-data writes are assignments with no error branch (r(7102) on a refusal). Rewrite `_dash_empty_data` (4276-4284). Edit `_dash_plot` (5955-5963, 6038, after 6088, 6116-6129, 6140-6145, 6150-6178), `_dash_do_render` (394-434: the `PRIVate` option), `_dash_prepare_spec` (7283-7288), `_dash_build` (7395, after 7450), `_dash_serve` (7598, 7640-7652, 7691-7694, end) and `_dash_clear` (before 6226). Every new `python:` line is an import, an assignment or `_dash_M.setLocal(`; no backtick or `$` appears on any of them; each program with a `python:` line calls `_dash_require_python` as a command before its first one. Add the commit-1 entries of TR-08.20 to `test/program_coverage_map.py`. Run `test_parser.cscript` (P1A-72, P1A-75), `test_render_log_clean.cscript` and `test_string_values.cscript` through the driver. In each log, check that no `dash: note:` line appears: the slot's `STATATMP` is private, so a note there would be a false positive.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_private_files.py -q -n0` passes, except `TestTheHelpDocumentsTheTempfiles` (08-09). `python3 -m pytest test/test_program_coverage_map.py test/test_no_orphans.py test/test_file_headers.py -q` passes. The driver logs of test_parser, test_render_log_clean and test_string_values end with their ALL-PASSED lines and contain no `^r([0-9]*);` line.]]></verify>
  <done>Every render route opened a private run folder, wrote its spec, data and empty data through Python by value, named previews privately, printed at most one note per command where a location was not private, closed its folder on every path dash.ado controls, and dash clear pruned, fallback roots included, without loading the module when no root existed.</done>
</task>

<task type="auto" id="08-08">
  <name>Flip the pins the private folder moved</name>
  <files>test/test_string_value_export.py, test/test_immediate_dashboards.py, test/test_env_guards.cscript</files>
  <action><![CDATA[
    Flip, never delete. `TestDashAdoUsesTheWriter::test_every_entry_point_is_called_by_the_ado_and_no_other` (:550-553) now expects the six names of TR-08.9. `TestTheDataFileIsTheOneDashAdoWrites::test_dash_ado_writes_this_text` (:209-220) reads the text from ``local _ed `"(.*?)"'`` and still compares it to `_EMPTY_DATA`. In ENV-12 (`test_env_guards.cscript:494-515`) set the expected program list to the one the script logs on its `ENV-12: programs running python:` line, keep the guard-before-first-python loop, and update the comment above it (why each program runs Python). Record one `Flipped: <node> -- <old expectation> was wrong because <why>` line per flip in `<scratch>/08-c1-flips.txt`, covering also SRV-19, HC4-18 and HC4-21 from 08-04.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_string_value_export.py test/test_immediate_dashboards.py -q -k "Writer or DataFileIsTheOne"` passes. The test_env_guards driver log shows `ENV-12 PASS` and `PF-10 PASS`. `<scratch>/08-c1-flips.txt` holds 6 `Flipped:` lines, and the 4 `Adjusted:` lines of task 08-06 (round 2).]]></verify>
  <done>Every test that pinned the old temp-file layout pinned the private one instead, none was deleted, and each flip was recorded for the commit body.</done>
</task>

<task type="auto" id="08-09">
  <name>Document temporary files and privacy</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-08.11, its round-2 sentences included (paragraph 4's "hands the text to Python" and the addition to 1434-1436 about a `.py` run by hand): the `viewerjumpto` line after Server Mode's (14), and the new `{marker tempfiles}{...}` / `{title:Temporary files and privacy}` section with its six paragraphs directly above `{marker limits}` (1581). Edit 806-813, 863-869, 1364-1366, 1424, 1434-1436 (R-7), the Security paragraph's closing sentence (about 1468), and 1575-1578. Use SMCL only (`{cmd:}`, `{it:}`, `{help dash##tempfiles:…}`). Keep every existing `{marker}` and the `{ul:Launch Bokeh Server` prefix. Then grep `test/test_help_claims_*.py`, `test/test_help_conformance.py`, `test/test_toolbar.py`, `test/test_csp.py` and `test/test_security_surface.py` for slices that end at `{marker limits}` or pin the edited sentences, and run them.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_private_files.py -q -k Help -n0` passes. `python3 -m pytest test/test_help_conformance.py test/test_toolbar.py test/test_csp.py test/test_security_surface.py test/test_resource_limits.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_5.py -q` passes.]]></verify>
  <done>The help documented where dash keeps its temporary copies, their modes and removal, the preview rule, the note for a location that is not private with its remedies, the fallback root, the anti-hijack refusal r(7102), the r(603) folder failure, the shared-`c(tmpdir)` residual, the umask rule for named pages, the 0600 rule and link refusal for a named server app that holds the data, and the untested hosts.</done>
</task>

<task type="auto" id="08-10">
  <name>Close P0.12b and P0.14 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the two open entries by their `WP29_OPEN` titles (keys `"P0.12b"`, `"P0.14"`). In place, change `- [ ]` to `- [x]` and rewrite only the Resolution, as `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.12b). …` and `… (WP-29, P0.14). …`. The text says what changed and where, in both renderers (the "BUGS.md text" in Notes), and names in full form `test/test_private_files.py::TestTheDataFileIsPrivate::test_the_data_file_is_0600_under_umask_002`, `test/test_private_files.py::TestTheDataFileIsPrivate::test_a_symlink_at_the_path_is_not_followed`, `test/test_private_files.py::TestTheServedAppIsPrivate::test_the_launch_route_writes_the_app_0600`, `test/test_private_files.py::TestTheServedAppIsPrivate::test_a_dash_build_server_app_is_0600`, `test/test_private_files.py::TestTheServedAppIsPrivate::test_a_link_at_a_server_app_path_is_refused_and_its_target_kept`, `test/test_private_files.py::TestThePrivateRoot::test_a_symlinked_root_is_left_alone_and_a_fallback_is_used`, `test/test_private_files.py::TestThePrivateRoot::test_a_writable_non_sticky_base_proceeds_with_a_note_naming_chmod`, `test/test_private_files.py::TestTheLaunchFromTheOpenFile::test_a_path_swapped_after_verification_does_not_change_what_runs`, `test/test_private_files.py::TestTheLaunchFromTheOpenFile::test_a_substituted_app_is_not_started`, `test/test_private_files.py::TestTheLaunchFromTheOpenFile::test_no_module_beside_the_app_or_in_the_working_folder_is_imported`, `test/test_wp29_truth.cscript PF-06`, `test/test_wp29_truth.cscript PF-11`, `test/test_wp29_truth.cscript PF-12`, `test/test_adversarial.cscript PF-09` and `test/test_help_claims_4.cscript PF-08` (P0.12b), and `test/test_private_files.py::TestThePreviews::test_the_newest_five_are_kept`, `test/test_private_files.py::TestThePreviews::test_a_live_other_sessions_pages_survive_prune_and_clear` and `test/test_wp29_truth.cscript PF-02` (P0.14). Each ends with a `Residual, deferred (WP-29): …` sentence (Linux and Windows unmeasured; the deferred sweep). P0.12b's residual also names the cases ratified on 01oct2026. In a `c(tmpdir)` others can write without a sticky bit, another account that replaces `dash-<uid>` can replace the spec or data between dash.ado's write and the renderer's read, or deny the launch. It can no longer change what `dash serve` runs: the app is started from the bytes read through a verified descriptor (round 2). On a disk that keeps no permissions, the copies are not private and `dash serve`'s copies stay until the command ends. Both are noted to the user. A `.py` the user runs by hand with `python` or `bokeh serve` is opened by name and imports from its folder, as the help says. Delete the `"P0.12b"` and `"P0.14"` lines from `WP29_OPEN`. In CHANGELOG.md replace `<!-- WP-29 P0.12b -->` and `<!-- WP-29 P0.14 -->` (end of `### Security`) in place with the "CHANGELOG text" lines in Notes. Run, in this order: the changed pytest files; the full suite once (`python3 -m pytest test/ -q`); the five touched cscripts through the driver; `gitnexus_detect_changes()`, saving the output. Then stage exactly the files of tasks 08-02..08-10, check `git diff --cached --name-only`, grep the message for `claude|anthropic`, and commit. The subject is `Keep dash's temporary copies of the data private and prune the previews (WP-29 P0.12b, P0.14)`; the body is `<scratch>/08-P0.12b-failure.txt`, the measured defect (D1-D9, U2), what changed and where, one `Regression:` line per failing-first test (`-- failed at <cycle-1 base sha> with <text>`), the lines of `<scratch>/08-c1-flips.txt`, and the two `BUGS.md: "<title>" (closed)` lines. Grep the message again after committing.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports 0 failed and no new skips. `python3 -m pytest test/test_tracking_documents.py -q -n0` passes. `grep -c '<!-- WP-29 P0.12b -->\|<!-- WP-29 P0.14 -->' CHANGELOG.md` prints 0. `git -C <wt> log -1 --format=%s | grep -c '(WP-29 P0.12b, P0.14)$'` prints 1. `git -C <wt> log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0. `git -C <wt> show --stat HEAD` lists no `CLAUDE.md`, `.gitignore`, `GAPS2.md`, `ROADMAP.md` or `*.html`.]]></verify>
  <done>P0.12b and P0.14 were closed in place with tests that exist, their markers and allowance keys were gone, and one green commit carried the private-files fix.</done>
</task>

<task type="auto" id="08-11">
  <name>Write the failing F2 lifecycle tests</name>
  <files>test/test_serve_lifecycle.py, test/test_resource_limits.py, test/test_help_claims_4.cscript</files>
  <action><![CDATA[
    Record `git -C <wt> rev-parse HEAD` (commit 1) in `<scratch>/08-cycle2-base.txt`. Create `test/test_serve_lifecycle.py` with every test of "Cycle 2 (F2)", plus module helpers. `_url(port, path)` returns `http://127.0.0.1:%d%s`. `_port_free(port)` binds 127.0.0.1 with SO_REUSEADDR. `_wait_health(port, seconds)` waits for `/health`. `_kill_listeners(port)` uses `lsof -t -iTCP:<port> -sTCP:LISTEN` and returns quietly when lsof is absent. Real-server tests carry `@pytest.mark.serve`; the kill tests also carry `skipif(sys.platform == "win32")` and always pass `--timeout 1`. Use paths from `dr._dash_run_open(str(tmp_path))` wherever a test plays `dash serve` (R-1). In `test/test_resource_limits.py`, extend `TestTheServedAppDefinesEveryNameItReads::test_no_function_in_the_app_reads_an_undefined_global` (:1163-1190): add every top-level symbol that is referenced and neither assigned nor imported, skipping names matching `^__\w+__$`, and add `"_dash_watch_parent"` to the explicit tuple. Add LC-01 to HC4-19's run in `test/test_help_claims_4.cscript`, using the thread of PF-08. Run the pytest files and the script on the commit-1 tree and save the failures to `<scratch>/08-P0.13-F2-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_serve_lifecycle.py -q -n0 2>&1 | tail -3` shows failures and no collection error. The sigkill test fails with `/health` still 200, and no listener is left on its port afterwards (`lsof -iTCP -sTCP:LISTEN | grep -c python` is unchanged from before the run). The resource-limits test fails naming `_dash_watch_parent`. LC-01 prints `FAIL` naming `app.py`.]]></verify>
  <done>Every F2 regression test existed and failed on the commit-1 tree for its recorded reason, without leaving an orphan server.</done>
</task>

<task type="auto" id="08-12">
  <name>Add the parent watch to the app</name>
  <files>dash_render.py, test/function_test_map.py, test/test_server_rate_limit.py</files>
  <action><![CDATA[
    Add `_dash_watch_parent` beside `_dash_port_value` (31866), as TR-08.12 specifies, with a docstring citing the t3/t4 measurements and the p6 prototype. Append `"_dash_watch_parent"` after `"_dash_port_value"` in ServerAppBuilder's functions tuple (28829), with a comment naming F2. Apply TR-08.13: the `--parent-watch` argument in the emitted `_dash_arg_parser` (29787-29824), the call after `_server = _dash_server_app(…)` (31706-31707), and `flush=True` on every banner print (31717-31722). Add the two F2 keys of TR-08.20 to `test/function_test_map.py` and mutation-check them. Extend `test/test_server_rate_limit.py::TestTheLauncherFlags::test_the_launcher_help_lists_every_flag` (:992-995) with `"--parent-watch"`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_serve_lifecycle.py -q -k "ParentWatch or AppWatchesStdin" -n0` passes. `python3 -m pytest test/test_resource_limits.py test/test_statistical_helpers.py test/test_server_rate_limit.py test/test_function_test_map.py -q -k "DefinesEveryName or CarriesEveryName or LauncherFlags or function"` passes.]]></verify>
  <done>The generated app watched a pipe on its stdin under `--parent-watch` and stopped, with a hard-exit backstop, when the pipe closed; the served-name guard covered the app's module level.</done>
</task>

<task type="auto" id="08-13">
  <name>Erase the app once it answers</name>
  <files>dash_render.py, test/test_help_claims_4.py</files>
  <action><![CDATA[
    Apply TR-08.14 in `_dash_launch_app` (31944-32108). The changes: no new-session kwargs on Popen (the `stdin=subprocess.PIPE` and the bootstrap command are commit 1's, TR-08.8a; keep them); `--parent-watch` always appended to `_cmd`, after the app's own arguments; banner tracking in `_drain_stdout`; the erase gated on `_ready and _banner`; the docstring. In `__main__`'s launch block (32196-32205) pass `erase_app_when_ready=_dash_private_run_of(args.output) is not None`. Flip `test/test_help_claims_4.py::TestTheRealHandoffServes::test_it_serves_and_stops` (:1366-1426). Its paths come from `dr._dash_run_open(str(tmp_path))`, and `assert os.path.exists(out)` becomes: within 5 s of the first `/health` 200, `out`, the spec and the data no longer exist. Rewrite its docstring. Record the flip in `<scratch>/08-c2-flips.txt`, together with the two extended guards of 08-11 and 08-12.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_serve_lifecycle.py -q -n0 -k "not HelpSays"` passes, and so does `python3 -m pytest test/test_serve_launcher.py test/test_help_claims_4.py test/test_help_claims_1.py test/test_help_claims_5.py -q -k "Launcher or RealHandoff or ServeBlocks or Interrupted or LaunchReport"`. `lsof -iTCP -sTCP:LISTEN | grep -c python` is unchanged from before the run.]]></verify>
  <done>dash serve's child ran watched on a stdin pipe in Stata's process group, and its app file was erased once the server's own banner and `/health` had both arrived, so no copy of the data stayed on disk while it served.</done>
</task>

<task type="auto" id="08-14">
  <name>Close F2's half and commit</name>
  <files>dash.sthlp, CHANGELOG.md, BUGS.md</files>
  <action><![CDATA[
    Apply TR-08.15 to dash.sthlp: 1421-1424; 1575-1578; and the tempfiles section's paragraph 2. In CHANGELOG.md, replace in place only the `<!-- WP-29 P0.13 -->` that sits under `### Security`: the first one after that heading and before the next `### `. Leave the one under `### Fixed in WP-29`. The replacement is the "CHANGELOG text" F2 line. Leave the P0.13 BUGS.md entry open, and leave its `WP29_OPEN` key. Rewrite its Resolution in place as `- Resolution: Not fixed because the second of section 08's two P0.13 commits (Break stops dash serve, r(1)) has not landed; the first, which stops the server when Stata ends and keeps no copy of the data on disk while it serves, landed as "<F2 subject>". Graded S1 (WP-29): GUI Break still cannot stop dash serve.` It names no test. Run the changed files, then the full suite once, `test_help_claims_4.cscript` through the driver and `gitnexus_detect_changes()`. Commit with the subject `Stop the served app when Stata ends and keep no copy of the data on disk while it serves (WP-29 P0.13 F2)`. The body is `<scratch>/08-P0.13-F2-failure.txt`, the measured defect (t3, t4), what changed, the `Regression:` lines (`failed at <commit-1 sha>`) and `<scratch>/08-c2-flips.txt`. It has no `BUGS.md: … (closed)` line, since the entry stays open. Grep the message for `claude|anthropic` before and after committing.
  ]]></action>
  <verify><![CDATA[The full suite reports 0 failed. `python3 -m pytest test/test_tracking_documents.py -q -n0` passes, because the open entry still has its marker under Fixed and says why it is open. `grep -c '<!-- WP-29 P0.13 -->' CHANGELOG.md` prints 1. The log shows `LC-01 PASS`. `git -C <wt> log -1 --format=%s | grep -c '(WP-29 P0.13 F2)$'` prints 1.]]></verify>
  <done>The server-dies-with-Stata and no-data-at-rest half of P0.13 landed as one green commit, with the entry still open and explaining why.</done>
</task>

<task type="auto" id="08-15">
  <name>Write the failing Break tests</name>
  <files>test/test_serve_lifecycle.py, test/test_serve_launch.cscript</files>
  <action><![CDATA[
    Record `git -C <wt> rev-parse HEAD` (commit 2) in `<scratch>/08-cycle3-base.txt`. Add every test of "Cycle 3 (F4)" to `test/test_serve_lifecycle.py`. The stub `sfi` is a `types.ModuleType` with `BreakError(Exception)` and `SFIToolkit.pollstd`, installed with `monkeypatch.setitem(sys.modules, "sfi", stub)`. The fakes record `stdin.close`, `wait(timeout)`, `terminate` and `kill`. `TestTheAdoEndsWithROne` reads `_dash_serve`'s text with comments stripped. Add LC-02, LC-03 and LC-04 to `test/test_serve_launch.cscript` after PF-07 and before SRV-19. Their stub folders are named from `c(tmpdir)` and the Python pid, with no `tempfile` or `tempname` draws. Add their summary in the script's header comment. Run both on the commit-2 tree and save the failures to `<scratch>/08-P0.13-F4-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_serve_lifecycle.py -q -n0 -k "Poller or PollsStata or LaunchReportBox or StopHint or AppBanner or NamesBreak or ROne"` fails. `test_pollstd_is_called_while_it_waits` fails with 0 calls; nothing errors at collection. In `<scratch>/stata/run_test_serve_launch.log` LC-02 fails with rc 0, LC-03 with rc 0 after at least 50 s, and LC-04 on the message.]]></verify>
  <done>Every F4 regression test existed and failed on the commit-2 tree for its recorded reason.</done>
</task>

<task type="auto" id="08-16">
  <name>Poll Stata and stop on Break</name>
  <files>dash_render.py, test/function_test_map.py, test/test_serve_launcher.py</files>
  <action><![CDATA[
    Add TR-08.16's `_DashServeInterrupted`, `_dash_stata_poller` and `_dash_stop_child` beside `_dash_launch_app`. They are not added to any copy list. Rewrite `_dash_launch_app`'s waiting part as TR-08.17 specifies:
    - the poll before prebind;
    - a poll each pass, outside the `urlopen` try (32060-32077);
    - the final poll;
    - one try/except/finally from Popen to the final `proc.wait()`;
    - the 130/-SIGINT mapping;
    - the stop and hint messages, inside and outside Stata.

    Apply TR-08.17's `__main__` changes (32158-32205; `except _DashServeInterrupted` before `except RuntimeError`) and the emitted app's exit-130 and banner text (31717-31729). Adjust the fakes in `test/test_serve_launcher.py` (`_fake_popen_class` :99-131 and the two inline `_FakeProc`s :241-312) to `wait(self, timeout=None)`, `kill()`, and a recorded `close()` on the `_RecStdin` they have had since commit 1 (task 08-06); change no assertion, and record the adjustment in `<scratch>/08-c3-flips.txt`. Add the F4 keys of TR-08.20 to `test/function_test_map.py` and mutation-check them.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_serve_lifecycle.py -q -n0 -k "not NamesBreak and not ROne"` passes. `python3 -m pytest test/test_serve_launcher.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_4.py test/test_help_claims_5.py test/test_function_test_map.py -q -k "Launcher or Serve or RealHandoff or Interrupted or function"` passes. `lsof -iTCP -sTCP:LISTEN | grep -c python` is unchanged from before the run.]]></verify>
  <done>The launcher polled Stata while it waited, let no Break be swallowed, stopped its child by close, terminate then kill, and reported an interruption instead of an error, inside Stata and on the command line.</done>
</task>

<task type="auto" id="08-17">
  <name>End dash serve with r(1)</name>
  <files>dash.ado, dash.sthlp</files>
  <action><![CDATA[
    Apply TR-08.18 to `_dash_serve`: the announcement (7660-7661, keeping the `starting Bokeh Server on port N.` prefix), the `_srv_brk` setLocal line after the `_srv_err` one, then the run-folder close and `if "`_srv_brk'" == "1" error 1` after the `_srv_err` branch. Apply TR-08.19 to dash.sthlp: 97, 750-753, 777, 1421-1424 (rewritten whole) and 1719. Run `test_serve_launch.cscript`, `test_env_guards.cscript` (ENV-17's absence of `starting Bokeh Server`) and `test_render_locate.cscript` through the driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_serve_lifecycle.py test/test_help_claims_1.py test/test_help_claims_2.py -q -n0 -k "NamesBreak or ROne or syntax or diagram"` passes. The driver logs show `LC-02 PASS`, `LC-03 PASS`, `LC-04 PASS`, `SRV-19 PASS`, `ENV-17 PASS` and `LOC-12 PASS`, with no `FAIL`.]]></verify>
  <done>dash serve stopped by Break ended with r(1), its run folder removed, and every message and help passage named Break.</done>
</task>

<task type="checkpoint" id="08-18">
  <name>Record the manual GUI Break check</name>
  <files>none</files>
  <action><![CDATA[
    CLAUDE.md rule 10 forbids launching GUI Stata, so ask the maintainer to run this check in StataNow's GUI on the worktree's dash and paste the Results window:
    1. `adopath ++ "<wt>/"`
    2. `sysuse auto, clear`
    3. `dash scatter mpg weight, name(g1)`
    4. `dash serve, port(5123) nobrowser`
    5. Wait for the ready line, then press Break (toolbar button or Command+.).

    Expected: `dash: stopped by Break; the server has stopped.`, `--Break--`, `r(1);`, and `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5123/health` printing `000`. Record the answer verbatim in `<scratch>/08-gui-break.txt`. If the maintainer declines or is unavailable, record "not run" there and continue; task 08-19 then writes the residual.
  ]]></action>
  <verify><![CDATA[`<scratch>/08-gui-break.txt` exists and holds either the pasted output or "not run".]]></verify>
  <done>The manual GUI Break check was run and recorded, or its absence was recorded for the Resolution's residual.</done>
</task>

<task type="auto" id="08-19">
  <name>Close P0.13 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Acceptance outside the suite comes first. Re-create the signal driver in `<scratch>/sig/`: a do-file running `dash scatter mpg weight` and `capture noisily dash serve, port(<free>) timeout(2) nobrowser`, then `display "U12: dash serve returned rc=" _rc`. A Python driver starts it through `scripts/stata_slot.sh`, waits for `/health`, sends KILL, TERM or INT to the Stata pid, and prints the health code, the listeners and the data-bearing files under the slot's `tmp/`. Run it once per signal and save the output to `<scratch>/08-acceptance.txt`. Expect `000`, no listener and no file each time, and `rc=1` for INT. Close the P0.13 entry in place: `- [x]`, and `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.13). …` (the "BUGS.md text" in Notes). The Resolution pastes the acceptance lines and the GUI check result, or the residual `Residual, deferred (WP-29): GUI Break verified only through a patched pollstd (test/test_serve_launch.cscript LC-03); manual GUI check not run.` It also states that Linux and Windows are unmeasured. It names, in full form, `test/test_serve_lifecycle.py::TestTheServerDiesWithItsLauncher::test_sigkill_of_the_launcher_stops_the_server`, `test/test_serve_lifecycle.py::TestNoCopyOfTheDataWhileServing::test_spec_data_and_app_are_gone_once_health_answers`, `test/test_serve_lifecycle.py::TestTheLauncherPollsStata::test_break_closes_stdin_stops_the_child_and_raises_interrupted`, `test/test_serve_lifecycle.py::TestTheLauncherPollsStata::test_break_before_health_answers_is_not_swallowed`, `test/test_help_claims_4.cscript LC-01` and `test/test_serve_launch.cscript LC-03`. Delete `"P0.13"` from `WP29_OPEN`. Replace the remaining `<!-- WP-29 P0.13 -->` (under `### Fixed in WP-29`) with the "CHANGELOG text" F4 line. Run the changed files, then the full suite as `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q` (the session's third full launch), `test_serve_launch.cscript` through the driver and `gitnexus_detect_changes()`. Commit with the subject `Let Break stop dash serve and end it with r(1) (WP-29 P0.13 F4)`. The body is `<scratch>/08-P0.13-F4-failure.txt`, the measured defect (p7, t5, g1), what changed, the `Regression:` lines (`failed at <commit-2 sha>`), `<scratch>/08-c3-flips.txt` and `BUGS.md: "<title>" (closed)`. Grep the message for `claude|anthropic` before and after.
  ]]></action>
  <verify><![CDATA[The full suite reports 0 failed. `python3 -m pytest test/test_tracking_documents.py -q -n0` passes. `grep -c '<!-- WP-29 P0.13 -->' CHANGELOG.md` prints 0. `grep -c '(WP-29, P0.13)' BUGS.md CHANGELOG.md` prints at least 3. `<scratch>/08-acceptance.txt` shows `000` three times and `rc=1` for INT. `git -C <wt> log -3 --format=%s` ends, newest first, with `(WP-29 P0.13 F4)`, `(WP-29 P0.13 F2)` and `(WP-29 P0.12b, P0.14)`, and `git -C <wt> log -3 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>P0.13 was closed in place naming tests that exist, its last marker and allowance key were gone, the real-signal acceptance was recorded, and the section's third green commit landed on `wp29-s08`.</done>
</task>

## Section completion criteria

- **Files.** Every temporary copy of the data that dash writes is 0600, in a checked 0700 `c(tmpdir)dash-<uid>/` folder (or its fallback root), wherever the disk keeps permissions:
  - spec, data and empty data on every route;
  - the `dash serve` app;
  - the preview.

  Pinned in pytest and by PF-02..PF-09. Pages the user names keep the umask (PF-03). Every server app, `dash build, server`'s `.py` included, is 0600, created exclusively and never through a link (PF-11, `TestTheServedAppIsPrivate`; M4, R-7).
- **Unsafe locations (ratified 01oct2026).**
  - No privacy condition ends a command with an error. A shared `c(tmpdir)`, a planted `dash-<uid>` and a disk without permissions each give rc 0 and one `dash: note:` per command (PF-09, PF-12, `TestThePrivateRoot`, `TestTheNote`).
  - A planted root is left alone for a 0700 fallback root.
  - A user-named folder is never refused, re-moded or noted (PF-11 step 4).
  - r(603) remains only for an operating-system failure to create the folder (AC-08.4a).
- **Lifetimes.**
  - No run folder outlives its command on any path dash.ado controls.
  - Leftovers are swept by pid.
  - Previews are bounded per session and removed by `dash clear`.
  - Nothing is ever written through a link, a FIFO or device, a hard-linked file or a foreign file, and no app runs but the bytes dash wrote, read through a descriptor it verified and handed to `python -P` on stdin (R-9, round 2). These are the anti-hijack guards, r(7102).
- **The server.**
  - It stops within the grace period after its Stata dies.
  - No data file exists while it answers.
  - Break ends `dash serve` with r(1) from every front end dash can test, plus the recorded manual GUI check or its residual.
  - Messages and help name Break.
- **Commits.** Three green commits on `wp29-s08` with the subjects of AC-08.5. Each body opens with its saved failure text and carries `Regression:` and `Flipped:` lines. No test-only commit. No AI reference.
- **Tracking.** BUGS.md P0.12b, P0.13 and P0.14 are closed in place. Their `WP29_OPEN` keys and CHANGELOG markers are gone.
- **Guards.** `TestTheServedAppDefinesEveryNameItReads` (module level included) and `TestTheServedAppCarriesEveryName` are green. ENV-12 is flipped and green. The full suite is green with no new skips.

## Notes

- **Line numbers** are 7421d3d's. S01, S09, S03, S02, S04, S06, S07 and S05 merge before S08 and shift `dash.ado` (`_dash_plot` export 5981-6182, `_dash_prepare_spec`) and `dash_render.py`. Locate every site by its symbol and quoted text (R4); a rejected hunk is applied by hand.
- **Shared registries (R1-R3).**
  - **R1:** the S08 block goes in `test_wp29_truth.cscript` in section order. PF-09 is appended to `test_adversarial.cscript` after S02's and S06's runs, in merge order. PF-07 and LC-02..04 go in `test_serve_launch.cscript` before SRV-19; S13's TOK cases (batch 2) follow them. Nothing is added to the runner or the hygiene pins.
  - **R2:** `"_dash_watch_parent"` is the functions tuple's new last entry. The map keys go in alphabetical place.
  - **R3:** this section edits only its own BUGS.md entries, its own markers and its own `WP29_OPEN` keys. In dash.sthlp it edits only the passages named in TR-08.11/15/19. The Security paragraph's last sentence is S13's to keep.
- **The two P0.13 markers have the same text.** F2 replaces the one under `### Security` and F4 the one under `### Fixed in WP-29`. Locate them by heading, never by first match.
- **Stand-in renderers stay unchanged.** Those on the ado-path parse argv by `index()` and write with plain `open()`:
  - test_bug_regressions.cscript:422-428;
  - test_json_escaping.cscript:2508-2514 and 3934-3940;
  - test_serve_browser.cscript:116-121;
  - test_serve_launch.cscript:260, 440, 639;
  - test_help_claims_4.cscript:451.

  They ignore `--private-output` and need no change. `_dash_tmp_close` succeeds after them because it removes the folder whatever is in it. The J5/J7 stubs copy the 0600 spec as the same user.
- **Paths, not realpaths.** Never print or compare a realpath. `dash: dashboard saved to <path>` (6177) shows the `c(tmpdir)` spelling, so a test matching `c(tmpdir)` as a prefix keeps working (A2).
- **The pid.** It is `os.getpid()` in Stata's Python, which equals the `St<pid>` prefix (measured). Never use `` `c(pid)' ``.
- **Error-path cleanup is deferred by design.** m7 measured that wrappers change `quietly dash …` output (Q3, Q5). A route that errors after `_dash_tmp_open` leaves a 0700 folder, which the next `_dash_tmp_open` or `dash clear` of the session removes (same pid). That includes an anti-hijack r(7102) from a spec, data or empty-data write. A folder left in a fallback root is swept the same way, and the fallback root goes once it is empty.
- **The three classes (R-8) are not mixed.** Never raise for a privacy condition. Never note an anti-hijack one. Never print a second note in one command for the same location. A reviewer greps `_DashUnsafePath` raises (AC-08.4a, task 08-05 verify) and `exit 603` lines.
- **Commit-body forms** (index):
  - `Regression: test/<file>.py::<Class>::<test> -- failed at <sha> with <text>`
  - `Flipped: <node> -- <old expectation> was wrong because <why>`
  - `BUGS.md: "<title>" (closed)`

  There is no `Fixture:` line (no fixture).
- **CHANGELOG text** (each line replaces its marker in place):
  - **P0.12b (Security):** "dash's working copies of your data -- the specification and data files of every render, and `dash serve`'s application -- were written into c(tmpdir) with your umask (0644; 0664 under umask 002, which let another member of your group rewrite the application before it ran), under predictable names, and a symbolic link at such a name was followed. They are now written 0600, never through a link, a FIFO or another account's file, inside c(tmpdir)dash-<uid>/run-<pid>-<random>/, a folder only you can open (0700) that dash removes when the command ends. Where a location cannot be private -- a c(tmpdir) other accounts can change, or a disk that keeps no permissions -- dash still writes, 0600 wherever it can, and prints one note per command naming the location and the remedy; a dash-<uid> that is a link, not a folder or another account's is left alone and dash uses a private dash-<uid>-<random> folder beside it. As a guard against planted names, dash refuses (r(7102)) to write through a link, into a pipe or device, or over a hard-linked or another account's file, and `dash serve` no longer starts its application by name: it reads the file it wrote through a descriptor it checked (type, owner, identity, size and SHA-256) and hands that text to Python on the server's standard input, with neither the application's folder nor the working folder on Python's import path, so an application or module planted beside it is never run. The .py that dash build, server writes, which embeds every observation, was written with your umask too (0644); it is now written 0600 whatever the umask, replace creates a new file, and a symbolic link or another account's file at that name is refused (r(7102)) where it used to be written through. (WP-29, P0.12b)"
  - **P0.14 (Security):** "The one-line form without saving() left its preview page (1.3 MB holding every row of the graph's variables, 0644) in c(tmpdir) for good, one per session, and a second preview overwrote the first. Previews now go to c(tmpdir)dash-<uid>/previews/ (0600 in 0700) under unique names; a session keeps its newest five, `dash clear` removes them except a page a browser was asked to open in the last minute, and the path printed under $dash_nobrowser moves there. (WP-29, P0.14)"
  - **P0.13 F2 (Security):** "A server started by `dash serve` kept running after Stata was killed or crashed -- answering /health, holding its port and the data -- and left three copies of the data in c(tmpdir) (the specification, the data and a 1.25 MB application, 0644). It now stops within about five seconds of the Stata that started it ending, however Stata ends, and dash erases the specification and data once the application is written and the application once the server answers (measured on macOS; Linux and Windows have not been measured). (WP-29, P0.13)"
  - **P0.13 F4 (Fixed in WP-29):** "Break stops `dash serve` in every front end: the launcher polls Stata's interface while it waits, stops the server and ends the command with r(1), as any command interrupted by Break does; Ctrl+C in console Stata used to return 0, and GUI Stata's Break was never seen. Messages and the help name Break. (WP-29, P0.13)"
- **BUGS.md text** (the Resolutions, before the test names):
  - **P0.12b:** "Every temporary copy of the data -- the spec and data files of the one-line form, dash build and dash serve, and dash serve's app -- is written by dash_render.py's _dash_private_write (O_NOFOLLOW, O_NONBLOCK, created 0600, fstat-checked regular, single-link and owned, fchmod 0600 whatever the umask) into c(tmpdir)dash-<uid>/run-<pid>-<random>/ (0700; _dash_private_root notes a c(tmpdir) others can change and a folder the disk will not keep private, and leaves a linked, foreign or non-folder dash-<uid> alone for a dash-<uid>-<random> fallback made by _dash_fallback_root -- no privacy condition is refused, as ratified 01oct2026; the anti-hijack refusals end r(7102), and only a failure to create the folder at all ends r(603)), opened by dash.ado's _dash_tmp_open and removed by _dash_tmp_close, with folders left by an error or crash swept by _dash_run_sweep; the spec and empty-data files are written from Python (_dash_tmp_write_text) because Stata's file write resets the mode to the umask; dash serve's spec and data are erased once its app is written; every server app, dash build, server's user-named .py included (M4), is written 0600 by ServerAppBuilder.build(private=True), which removes an existing file of the user's at the name with _dash_private_clear_name (lstat, refusing a link, a non-regular or a foreign file) and then creates the file with O_EXCL; pages the user names keep the umask, as twoway's saving() and graph export; _dash_launch_app no longer runs `python <app>`: _dash_read_verified_app opens the app with O_NOFOLLOW and checks the open descriptor's type, owner, (st_dev, st_ino) and size and the bytes' SHA-256 against the _DashWrittenApp main() returned, and _dash_hand_over writes those bytes as one DASHAPP1 frame to the stdin of `python -P -c _DASH_BOOT <app>`, which compiles them under the app's name and runs them as __main__, so a path or folder swapped in after the check cannot change what runs and no module beside the app or in the working folder is imported (ratified 01oct2026, round 2); S08's commits add no file write to the served app (S13 later adds the hand-started app's private link.html)."
  - **P0.14:** "The one-line preview is named by _dash_preview_path in c(tmpdir)dash-<uid>/previews/ (unique, 0600 through --private-output), and _dash_prune_previews keeps a session's newest five, removes the session's pages on dash clear except a page opened in the last minute, removes a dead session's pages, and bounds all sessions at 25."
  - **P0.13:** "_dash_launch_app starts the app with a stdin pipe and --parent-watch, and the app's _dash_watch_parent stops its loop when the pipe closes, with a 5 s hard exit; the app file is erased once /health and the app's own banner have both arrived; the launcher calls sfi's pollstd each pass outside every broad except, stops the child by closing its stdin, then terminate, then kill, and reports an interruption, which dash.ado ends with error 1; messages and help name Break." Then the acceptance lines and the GUI result or its residual.
- **Notes for S13 (served-app token, batch 2).**
  - **Where S13's files go: index.md governs (R2 row S13; "Index overrides", row "Served app writes"; section-13 K-3, K-8, TR-13.8a, TR-13.12 item 9).** The opener's `open.html` (ratified item (4)) and a hand-started app's `link.html` (answer 3) are written by S13's own `_dash_private_page`, 0600 in a fresh 0700 `tempfile.mkdtemp` folder, never in a run folder. Only the launcher-side `_dash_write_link` (not copied into the app) writes `dash serve`'s `link.html` in the command's run folder, through `_dash_private_write(…, exclusive=True)`, which since ratification returns an `os.stat_result` and raises only `_DashUnsafePath` (anti-hijack, M4a) or an OSError (operating system); a loose mode is not raised. The link file holds the credential, so K-8 governs it, not R-8's note: when the written file is not a regular 0600 file of this account, S13 erases it and writes `link.html` through `_dash_private_page` in a fresh mkdtemp folder instead, and, if that fails too, prints the link once after a warning line and keeps serving (section-13 K-9, round 2 answer A); no link failure stops the server.
  - S13's round-1 failure texts ("its link could not be written privately (%s)" and "the server on port %d was stopped: its link was not written (%s)") are struck by round 2 answer A; S13 prints _DASH_LINK_UNWRITTEN and the link once instead (section-13 K-9).
  - **The served app's own write: index.md governs ("Index overrides", row "Served app writes"; R2 row S13).** Answer 3 (an app started by hand with no `DASH_SERVE_TOKEN` makes its own key and a private `link.html`) makes the served app write a file. In task 13-06, S13 flips S08's `TestTheServedAppWritesNoFile::test_the_generated_app_has_no_file_writing_call` in place (R7, with a `Flipped:` line) so that the generated source may write only through its own copied `_dash_private_page` and remove only that function's folder; any other file-writing call still fails the guard. S13 copies none of S08's private-file helpers: `_dash_private_write`, `_dash_private_msg`, `_dash_root_name`, `_dash_mode_private` and the root helpers stay off the served copy list. The app prints no R-8 note: K-8 and K-9 govern the link file. R-3 stays true for S08's commits.
  - **The launch from the open file (R-9, round 2).** The order in `_dash_launch_app` is: F4's pre-prebind poll; prebind; `_dash_read_verified_app(app_path, expect)` and `_dash_app_frame`; Popen of `[sys.executable, "-P", "-c", _DASH_BOOT, app_path, "--port", P, …, "--parent-watch"]` with `stdin=PIPE`; inside F4's single try, the two pump threads, then `_dash_hand_over(proc, frame)`, then S13's key line, written as bytes through the same binary writer (`raw = _dash_child_stdin(proc)`; `raw.write((token + "\n").encode("ascii"))`; `raw.flush()`; S13 L-3), then the loop. Both are flushed in that order, so the child reads the frame, then the key line one byte at a time (S13 Q-1), then the watch reads to end of file (§3b 3 measured exactly this). S13's `--token-stdin` is added to `_cmd` after `app_path`. No argv element holds the key, and `_DASH_BOOT` holds no secret. S13's fake stdin (`serve_token_probe.FakeStdin`) records bytes through `write` and has no `buffer`, as S08's `_RecStdin`; `_dash_child_stdin` returns either as it is, so S13's `.writes` holds S08's one frame write and then the key line. `_dash_read_verified_app`, `_dash_app_frame`, `_dash_child_stdin`, `_dash_hand_over`, `_DASH_BOOT` and `_DashWrittenApp` are launcher-only and never copied into the app. The app reads the key with `os.read` on fd 0, which the bootstrap leaves exactly after the frame.
  - A run folder holds only what its own command needs, and nothing in it is needed after that command's server stops. Since F2, no server outlives its Stata, so the dead-pid sweep is safe.
  - The key line is read in `__main__` by S13's `_dash_read_token_line` (at most `_DASH_TOKEN_LINE_MAX` = 256 bytes), after the bootstrap's frame and before the watch starts; `_dash_watch_parent` is not changed (section-13 Q-1, L-2).
  - Build real-server URLs through `test_serve_lifecycle._url`.
  - `/health` stays open, because the launcher probes it.
  - Add the token names after `"_dash_watch_parent"`.
- **Notes for S14 (embed rows, batch 3).** `_dash_write_stata_data` now ends in `_dash_private_write`. Restrict rows before that call. There is no error branch to keep (ratified 01oct2026): an anti-hijack refusal or an OSError raises out of the `python:` line as r(7102). Do not add a `try`/`return` that turns a refusal into text, and do not refuse a loose mode.
- **Notes for the closeout (S15; index A5).**
  - **GAPS2 X3 and F2:** Tracked `Closed in WP-29, BUGS.md "<P0.14 title>", commit <sha>` and `Closed in WP-29, BUGS.md "<P0.13 title>", commits <F2 sha>, <F4 sha>`.
  - **GAPS2 F4:** closed by the F4 commit; H2 points to F4.
  - **GAPS2 I3:** partly closed (P0.12b, commit 1); open: the token (S13).
  - **GAPS2 F9:** stays open, with a note that bullet c (the Ctrl+C message) is closed by the F4 commit and a, b, d and e remain.
  - **AUDIT-87:** the file half is closed here.
  - **ROADMAP WP-29 `**GAPS2 closed:**`:** X3, F2, F4 (I3 only after S13).
  - **PLAN.md BR-29.11, E6 and AC-29.6, and S01's AC-29.6 text:** already applied 01oct2026 (PLAN.md preamble; section-01 Appendix D carries the same text). S15 rewords none of them.
  - **AGENTS.md invariants:** the private root and the 0600 writer (`TestTheDataFileIsPrivate`); the parent watch (`TestTheServerDiesWithItsLauncher`); Break ends `dash serve` with r(1) (LC-03); and, round 2, dash starts its app only from the bytes it verified, never by path (`TestTheLaunchFromTheOpenFile::test_a_path_swapped_after_verification_does_not_change_what_runs`).
  - **Residuals for S15.7's report (round 2).** The app-substitution window is closed (R-9). Do not list it. List instead:
    - in a shared non-sticky `c(tmpdir)`, the spec and data are still read by path between dash.ado's write and the renderer's read, so another account that replaces `dash-<uid>` can change what the dashboard shows or deny the launch;
    - a `.py` the user runs by hand is opened by name and imports from its folder (documented);
    - the launch from the open file has not been measured on Linux or Windows;
    - F2's erase of `app.py` still waits for `/health` and the banner, although the child no longer reads the file. Erasing at the hand-over would shorten the time the app is on disk, and is a candidate for a later package.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The scripts then exit 222, and a SKIP is not a pass. Check `c(python_exec)` before trusting a skip.
