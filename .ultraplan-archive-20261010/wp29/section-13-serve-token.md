# Section 13: Served-app token

> Part of: WP-29 · P0: P0.12a · Sources: GAPS2-I3-a, GAPS2-I3-c (the credential and the help wording), AUDIT-87 (TWOWAY_COVERAGE_AUDIT.md:162, 183) · Unit: u11a-serve-token · Risk: red · Batch: 2 (merges last: S10, S11, S12, S13) · Depends on: 08 · Blocks: none (15 closeout only) · Case prefix: TOK · Tasks: 16, 1 commit (P0.12a)

**Files.**
- **Product and records:** `dash_render.py`, `dash.ado`, `dash.sthlp`, `CHANGELOG.md`, `BUGS.md`.
- **New tests:**
  - `test/test_serve_token.py`;
  - `test/serve_token_probe.py`, which holds the suite's shared test key and TOK-02's out-of-process probe.
- **Changed tests:**
  - **Registries and maps:** `test/function_test_map.py`, `test/program_coverage_map.py`, `test/test_tracking_documents.py` (the `WP29_OPEN` key only).
  - **Session helpers and fakes:** `test/test_server_serves.py`, `test/test_csp.py`, `test/test_adversarial_matrix.py`, `test/test_server_rate_limit.py`, `test/test_server.py`, `test/test_serve_launcher.py`, `test/test_help_claims_2.py`, `test/test_help_claims_4.py`.
  - **Guards and claims:** `test/test_resource_limits.py`, `test/test_security_surface.py`, `test/test_private_files.py` (S08's guard `TestTheServedAppWritesNoFile::test_the_generated_app_has_no_file_writing_call`, flipped in place by 13-06; index override "Served app writes").
- **Changed cscripts:** `test/test_serve_launch.cscript` (TOK-01..TOK-04).
- **Differences from the manifest's list:**
  - **Added:**
    - `test/test_serve_lifecycle.py` (S08's real-server tests and fake children);
    - `test/test_help_claims_4.cscript` (S08's LC-01 asserts an empty run folder while serving);
    - `test/test_e2e_serve.cscript` (P4-82 gains the provider check, review missed-site).
  - **Dropped:**
    - `test/test_serve_token.cscript` and `test/run_all_cscripts.do`, because index A3 puts the TOK cases in the existing `test_serve_launch.cscript`;
    - `GAPS.md`, `GAPS2.md` and `ROADMAP.md`, which are S15's (index A5).

## Review amendments (design review u11a, 30sep2026) — binding; they override any conflicting text below

**Ratified 01oct2026:** the maintainer ratified decisions 2-8 and (a)-(e) as written and STRUCK decision 1 ("Ensure that the token will never be missing"). The app now never runs without a key: started with no `DASH_SERVE_TOKEN` and no `--token-stdin` (a hand-run `python app.py` or `bokeh serve app.py`), it makes its own `secrets.token_urlsafe(32)` key once per server process, installs it for both gates, writes the link to a 0600 `link.html` in a fresh 0700 `tempfile.mkdtemp(prefix="dash-link-")` folder, and prints only that file's path (never the key; item 5). An invalid supplied key is still refused (item 8): at start (exit status 2) under `python app.py` and `dash serve`; under `bokeh serve`, which has no start hook, by one warning and the refusal of every session (K-1). Applied as K-1..K-8 below, in Evidence §6 (measured 01oct2026), TR-13.1/13.7/13.8/13.8a/13.10/13.12/13.14/13.18, the TDD stubs (the fail-closed tests replaced by failing-first "makes a key" tests), the test plan, AC-13.6, tasks 13-02 (now copies the ratified rows), 13-03..13-08, 13-13, 13-16 and Notes. New findings: under `bokeh serve` the script first runs at the first session (no earlier hook), and plain `bokeh serve` refuses the 127.0.0.1 link's websocket (403) unless started with `--allow-websocket-origin 127.0.0.1:<port>` (Evidence §6). Answer 2 (S08 codes struck) is reconciled for the link file in K-8: the link is written 0600 wherever the disk allows and otherwise written with one `dash: note:`, never refused on a privacy condition.

**Ratified 01oct2026 (round 2):** the maintainer answered three more questions, with the verbatim choices "Print the URL once" (A), "Launch from open file" (B) and "Commit them" (C). Round 1 stays in force.
- **A, applied as K-9 (new) and in K-2, K-3, K-4, K-8.** K-8's stop-the-server path is STRUCK. When the link file cannot be written in any folder dash tries, nothing is stopped. Under `dash serve` dash tries the run folder, then a fresh private temp folder. An app that made its own key tries its fresh private temp folder. In that case dash prints two lines to the output of whoever started the server, then keeps serving:
  - one warning line, `_DASH_LINK_UNWRITTEN`, saying that the key is now in that output and in any log of it;
  - on the next line, alone, the full tokenized URL.

  This happens exactly once:
  - once per launch under `dash serve`;
  - once per process under `python app.py`;
  - once per app path per process under `bokeh serve`.

  No later session prints it again. This is the only case in which the key is ever printed. Decision 5 and A3 now read "never printed, except K-9's fallback". Also applied in:
  - decision 5, the Overview and Risk;
  - BR-13.4..13.6;
  - TR-13.1 (`_DASH_LINK_UNWRITTEN`; fourteen constants), TR-13.8 step 3 (the opener's page that cannot be written opens nothing and stops nothing), TR-13.8a, TR-13.10 items 5 and 7, TR-13.11, TR-13.12 items 6 and 9, TR-13.14, TR-13.15 and TR-13.18;
  - the stubs: `test_a_key_that_cannot_be_announced_is_not_served` and `test_a_link_that_cannot_be_written_stops_the_server` are struck before they were ever written, and failing-first replacements are named below;
  - the mutation table, AC-13.1, AC-13.6 and the new AC-13.7;
  - tasks 13-01, 13-02, 13-07, 13-08, 13-13 and 13-16;
  - Notes, the CHANGELOG text and the closeout notes.
- **B, applied as L-1..L-5.** S08 (round 2) launches the app from a file descriptor that dash opened (`O_NOFOLLOW` where available) and verified (a regular file, owned by this account, with the identity S08 recorded when it wrote the file). It hands the verified text to the child, which compiles it under the app's path as its filename. A swap of the path after the check therefore cannot change what runs. S08 owns that hand-over, its command line and its swap tests. S13 changes only where the key goes: the key line follows S08's hand-over on the stdin pipe, and the pipe stays open (TD-4). The order is: open and verify (S08), Popen (S08), app text (S08), then the key line (S13). `python app.py` and `bokeh serve app.py` run by hand are outside dash's control: their routes are unchanged here, and S08 documents them. Applied in Q-1, Risk 8, Dependencies, Evidence §4 and §7 (measured), TR-13.12 items 3 and 4, TR-13.15 (`FakeStdin` records bytes), `test_the_token_goes_to_stdin_not_argv`, the mutation table, task 13-01 step 7 and Notes.
- **C.** `.ultraplan/wp29/` is committed on `wp29-p0` before step 0a's worktrees are cut, so `$WT` carries this file. Nothing in this section depended on the plan being untracked.

The reviewed design (u11a-serve-token, verdict "sound with amendments") is carried with every amendment applied.

| Id | Amendment | Where it is applied |
|---|---|---|
| A1 | Every tokenized URL uses `127.0.0.1`, never `localhost`: another account can bind `[::1]:P` beside dash's `127.0.0.1:P` and receive a `localhost` link (measured, Evidence §1). | TR-13.7 `_dash_tokenized_url`. Every printed, written and opened link and every help example uses it. Pinned by `TestTheTokenHelpers::test_the_tokenized_url`, `TestTheLauncherPassesTheToken::test_the_ready_line_and_the_link_file` and `TestTheServedAppRequiresItsToken::test_the_link_never_reaches_an_ipv6_squatter`. |
| A2 | The URL follows `--address`. | TR-13.7, with one correction (truth dispute TD-1): `::` maps to `[::1]`, not `127.0.0.1`. |
| A3 | The ready line put the key in every Stata log, and batch logs are 0644. | Decided, and widened (TD-2): **Stata never prints the key**, in any mode, except K-9's fallback (round 2, answer A): when no folder takes the link file, the launcher prints the link once, after a warning line. The launcher writes the link to `link.html` (0600) in the command's private run folder and prints only that file's path. The browser is opened with the full link by the child's `--show`. TOK-03 asserts that neither a text log nor an SMCL log holds the key. |
| A4 | A prefixed link wraps mid-token at `c(linesize)` 79. | No line carries the key, except K-9's one fallback line (round 2). The link-file path is printed on a line of its own. The app never prints its link either (ratified 01oct2026, K-3): a self-made key's link goes to a 0600 `link.html` whose path is printed on a line of its own with no prefix. K-9's fallback prints the link alone on a line of its own with no prefix, so it is not wrapped: a 73-character URL alone stayed whole. TOK-03 matches through `cert_log_has`, which undoes the `> ` wrapping. |
| A5 | Gate A and Gate B need one source of truth. | `_dash_server_app` assigns the module global `_DASH_SERVE_TOKEN` from the key it resolved, generated keys included (and announces a key it generated, K-2). Gate B reads that global. Under `bokeh serve`, where the module re-runs per session, Gate B's one source is the process holder (K-4). Pinned by `TestTheGeneratedAppIsGated::test_every_server_the_app_builds_has_the_token_provider` and the live `TestTheServedAppRequiresItsToken::test_gate_a_and_gate_b_agree_in_process`. |
| A6 | A `/health` flood answering 429 hid the link. | TR-13.12: an HTTPError with code 429 counts as "answering". Other codes do not, so a squatter's 404 never triggers the link. Pinned by `TestTheLauncherPassesTheToken::test_a_429_from_health_still_counts_as_answering`. |
| A7 | On darwin a set `$BROWSER` puts the URL in argv. | TR-13.8: the osascript route is taken only on darwin with `BROWSER` unset. Every other case goes through the 0600 redirect file. Pinned by `test_opening_never_puts_the_token_in_argv`. |
| A8 | The redirect file outlived a hard exit. | TR-13.10: the app removes its redirect folder 60 s after opening it (`io_loop.call_later`) and again at stop. Under `dash serve`, S08's parent watch ends the app within 5 s of Stata ending, so a key left on disk is dead. The self-made key's link folder (K-3) is removed in `__main__`'s `finally` (`python app.py`) or by `atexit` (`bokeh serve`; measured removed after SIGINT, Evidence §6); after a hard kill the file outlives a dead key. Pinned by `TestTheGeneratedAppIsGated::test_show_opens_the_tokenized_loopback_link`. |
| A9 | Map nested classes, add the imports, keep the bokeh/tornado imports lazy. | **Classes, applied with a measured deviation:** `import dash_render` imports no tornado, and a module-level `class X(AuthProvider)` would import `tornado.web` (both measured, Evidence §3). So the provider class is built inside `_dash_token_auth`, with lazy imports. This follows the existing precedent `_dash_server_transforms.<locals>._DashSecurityHeaders` (function_test_map.py:550). Its methods are mapped under `<locals>` keys. The log filter is a module-level function (logging accepts a callable filter), so no class copy path is needed. **Imports:** every copied helper imports `hmac`, `tempfile`, `webbrowser`, `HTTPError`, `AuthProvider` and `get_token_payload` locally. The app's import block is not edited. |
| A10 | TOK-02 had no precedent. | Measured (TD-3): a daemon thread started in Stata's Python before `dash serve` runs while it blocks, reaches the server, and stops it. S08 adds the same pattern (PF-08, LC-03). TOK-02 reads the key from the 0600 link file, never from a log. |
| A11 | The ordering of u11a, u11b and u12. | Superseded by index.md: S13 lands after S08 (batch 2). After S08 the app, spec and data are 0600 in a 0700 run folder and erased once the server answers. So `_DATA_B64` at rest is S08's and closed, and this section closes the network path. |
| A12 | Token-less user-facing lines. | Every user-facing line about the served dashboard changes: the child's banner, its health line, the launcher's ready line and dash.ado's `dash build, server` lines. The `Bokeh Server running at` prefix is kept (S08 TR-08.14 tracks it). The help says `bokeh serve --show` opens the address without the key. |

**Truth disputes, resolved by re-measuring at 7421d3d.**
- **TD-1 (A2).** `--address ::` is not reachable at 127.0.0.1. Measured with tornado 6.5.1 (Stata's Python) and 6.5.5 using `tornado.netutil.bind_sockets(0, address)`, then connecting:
  - `'::' ['AF_INET6:::'] {'127.0.0.1': 'ConnectionRefusedError', '::1': 'connects'}`
  - `'0.0.0.0' → 127.0.0.1 connects, ::1 refused`
  - `'localhost' → both families bound, both connect`

  So `::` and `::1` map to `[::1]`.
- **TD-2 (A3).** A clickable SMCL link would still leak the key. `python: _S.displayln('{browse "http://127.0.0.1:1/?token=SECRETSMCL":LINKTEXT}')` was run with a text log and an SMCL log open (`m1.do`):
  - the batch log and the text log hold only `LINKTEXT`;
  - the SMCL log holds `{res}{browse "http://127.0.0.1:1/?token=SECRETSMCL":LINKTEXT}`;
  - all three logs are `-rw-r--r--`.

  So the key is never displayed, not even inside a `{browse}` target.
- **TD-3 (A10).** A probe thread runs and sees the log while `dash serve` blocks. In `m1.do` the thread started in a `python:` line before `dash serve, port(54177) timeout(1) nobrowser`:
  - It printed `THREAD_RESULT {'health': 200, 't_health': 2.63, 'root': 200, ...}`.
  - It read the batch log while `dash serve` was still running, and the text it read held `dash: the server answers at http://localhost:54177/`.
  - It sent SIGTERM to the listener from `lsof -ti tcp:54177 -sTCP:LISTEN`, and the log shows `SERVE_RC=0` and `ELAPSED=4`.
- **TD-4 (design).** The design said "write token+'\n' and close stdin". After S08 the child's stdin pipe is its parent watch: end of file stops the server (S08 TR-08.12, and TR-08.16 step 1 closes it to stop the child). So the launcher writes one line and keeps the pipe open.

**Reconciliations with section 08 (on the tree this section starts from).**
- **Q-1. Read the key in `__main__`, before the watch.** S08's Notes suggest reading the key line inside `_dash_watch_parent`. The Server needs its `auth_provider` when it is constructed, and the watch starts only after `_dash_server_app` returns. So `__main__` reads the line with `_dash_read_token_line` (one byte at a time, at most 256 bytes, nothing after the newline consumed) before building the Server. The watch then reads the rest of the pipe, unchanged. Under round 2's answer B, S08's child has already read exactly the app text from the same pipe before the app's code runs, so the key line is the next thing `__main__` reads (L-2).
- **Q-2. Where the link file lives.** `link.html` goes in the command's run folder through `_dash_private_write(..., exclusive=True)` (S08 Notes for S13). The launcher's `finally` unlinks it, and `_dash_tmp_close` removes the folder. Without a run folder (a command-line `--launch` with its own `--output`), it goes in a fresh `tempfile.mkdtemp()` folder (0700) that the launcher removes.
- **Q-3. Tests that assert an empty run folder.** LC-01 (S08, in HC4-19's run of `test_help_claims_4.cscript`) asserts that the run folder holds no file once the server answers. It is flipped to "no file but `link.html`, which is 0600 and holds none of `_DATA_B64 = `, `"graphs":`, `"variableNames"`". So is any `test_serve_lifecycle.py` test asserting an empty folder (task 13-10 greps for them).
- **Q-4. The banner prefix.** The `Bokeh Server running at` prefix stays, because S08's launcher erases the app on that banner. The rest of the line changes.
- **Q-5. S08's sentence in the Security paragraph.** "The files dash serve writes are readable only by you; see ..." is kept (S08 R3).
- **Q-6. Fake children.** S08's fake children (in `test_serve_launcher.py` and `test_serve_lifecycle.py`) record `stdin.close`. They also get `write` and `flush` (`serve_token_probe.FakeStdin`). S08 commit 1 already gives these fakes `_RecStdin` (bytes `write`, `flush`, `close`, no `buffer`); replace it with `FakeStdin()`, recorded as `Adjusted:`.

**Answer 3: the app always has a key (ratified 01oct2026; measured in Evidence §6).**
- **K-1. Which start makes a key.** A supplied key wins: the `--token-stdin` line (`dash serve`), else a valid `DASH_SERVE_TOKEN`. An invalid supplied key is still refused, its value never shown (item 8): refused at start (exit status 2) under `python app.py` and `dash serve`; under `bokeh serve`, which has no start hook (K-4), one warning and every session refused, and no key is made (TR-13.8a `_dash_bokeh_serve_key` step 3). With neither, the app makes `_dash_new_token()` (`secrets.token_urlsafe(32)`: 43 characters, 256 bits, the strength `dash serve` uses). No path builds a Server or admits a session without a valid key, and there is no opt-out (item 2).
- **K-2. `python app.py`, and any caller of `_dash_server_app` without a key.** The key is made once per process inside `_dash_server_app`, after `Server(...)` has bound the port (Bokeh binds in the constructor, measured) and before `start()`, so before any session. The same call installs it for both gates: Gate A's `_dash_token_auth(key)` and the global `_DASH_SERVE_TOKEN` that Gate B reads (A5). It then calls `_dash_announce_key(_dash_tokenized_url(_p, key, address))` and keeps the returned folder in the global `_DASH_LINK_DIR`.
  - **A link that cannot be written at all** (an operating-system failure, or the anti-hijack check of `_dash_private_page`) no longer stops anything (round 2, answer A; the stop-and-exit-2 path is struck). `_dash_announce_key` prints K-9's warning line and the URL, once. `_DASH_LINK_DIR` stays None, and the Server is served as usual.
  - **A URL that cannot be formed** (an `--address` that `_dash_tokenized_url` refuses) is the one remaining stop, because there is no link to print. The app stops the Server (measured: `stop()` before `start()` releases the port) and raises RuntimeError, which `__main__` turns into `_p.error` (exit status 2).
  - `_dash_resolve_token` no longer makes keys; it returns the supplied key or None.
- **K-3. How the user reaches it.** `_dash_announce_key(url)` writes `_dash_redirect_page(url)` to `link.html` in a fresh `tempfile.mkdtemp(prefix="dash-link-")` folder (0700) through `_dash_private_page` (`O_CREAT|O_EXCL|O_NOFOLLOW`, 0600, fstat-checked; on a disk that keeps no file permissions the file is still written and one `dash: note:` names it, K-8). It then prints, to the process's stdout and flushed, `_DASH_LINK_SAID` and, on the next line alone, the path. While the file can be written, it never prints the key or the link. When no file can be written, K-9 prints the link once instead (round 2). This replaces the design's "`python app.py` prints its link". `dash serve` prints the same two lines (TR-13.12), so the user meets one form everywhere.
- **K-4. `bokeh serve app.py` without the variable.** Measured on 3.8.0 and 3.9.0: `bokeh serve` runs the script only when a session is made, never at start (a script gets no `on_server_loaded` hook), and runs it again for every session in a fresh module; `sys.modules` persists across sessions.
  - So the key is made by the first session's Gate B, in `_dash_process_key()`, which keeps it on a holder module at `sys.modules[_DASH_KEY_HOLDER]` (`"_dash_serve_key"`). Every later session reads the same key.
  - The session that made the key carries none and is refused, so no session is admitted before the key exists.
  - The link names the server-side address and port of the page request that made the session (`request.connection.stream.socket.getsockname()`, which the client cannot choose; never the `Host` header) and the app's path (`session_context.server_context.application_context.url`). Loopback in either family becomes `127.0.0.1` (A1).
  - A session made over a websocket (`bokeh.client`) has no such address (measured: `AttributeError`, the stream is detached). It still makes the key, and the link waits for the first page request.
  - The link is announced once per app path per process (`holder.linked`), and K-9's fallback print obeys the same limit: the path is marked before the attempt, so a failed write is never retried and never printed twice. Its folder is removed by `atexit` at the process's exit (measured after SIGINT).
- **K-5. The websocket origin under `bokeh serve`.** Measured: plain `bokeh serve` admits only `localhost:<port>`, so it answers the 127.0.0.1 link's websocket 403 (a blank page); with `--allow-websocket-origin 127.0.0.1:<port>` it answers 101. A1 forbids a localhost link, so under `bokeh serve` the announcement adds a third line, `_DASH_BS_ORIGIN_HINT % port`, and the help names the flag (as it already did for the variable case).
- **K-6. Exhaustion.** A client without the key can cause at most one key per process and one link file per app path, and it spends no session budget (Gate B stays before the limiter). The refusal page stays constant: it names neither the path nor the key, and reflects nothing from the request.
- **K-7. Unchanged.** Item 8's start-time refusal; the environment pop; `dash serve`'s `--token-stdin` handover, its `link.html` in the run folder and its ready lines. Under `--token-stdin` the app makes no key and prints no path.
- **K-8. Answer 2 and the link file: proceed and note.** S08's codes are struck: a run folder under a root that is not private is used, with a note, not refused. The link file holds the credential, so dash writes it 0600 wherever the disk allows, and never refuses a location for a privacy condition:
  - `_dash_write_link` checks what it wrote in the run folder (`os.lstat`: a regular file owned by `os.geteuid()` with no group or other permission bits). Two cases send the link to a fresh mkdtemp folder of the system temp directory instead, written through `_dash_private_page`:
    - the check fails (a disk that cannot hold 0600): it erases that file first;
    - the run-folder write itself raises (an anti-hijack refusal or an OSError; round 2): it erases nothing, because it wrote nothing at the name.
  - `_dash_private_page` (every writer of a key-holding page: `_dash_write_link`'s fallback, `_dash_announce_key` and the opener's `open.html`) still makes the file 0600 in a fresh 0700 folder. When the disk will not keep that mode even after `fchmod`, it keeps the file, prints one line, `dash: note: <file> holds the dashboard's link, but its disk keeps no file permissions, so other accounts of this machine may read it; set TMPDIR to a folder on a disk that keeps them.` (flushed; the key and the link are never printed), and returns as usual. The server runs.
  - This note is the link file's own. It names the link file, which S08's R-8 command note (printed earlier, naming the run folder's root) does not, and it is printed only when no folder dash tried could hold the file at 0600.
  - The server is never stopped over the link file (round 2, answer A: this item's stop path is struck). K-9 applies when the link cannot be written at all in every folder dash tries, through an operating-system failure or an anti-hijack refusal. The anti-hijack guards are kept, and are documented as anti-hijack, not privacy (M4a): `_dash_private_write(..., exclusive=True)` in the run folder (no link, FIFO, device or other account's file at the name), and `_dash_private_page`'s `O_EXCL|O_NOFOLLOW` open with its regular-file and owner check on the fresh file.
  - The user's location is never refused, and no folder dash did not make is re-moded.
- **K-9. No link file anywhere: print the URL once (ratified 01oct2026, round 2, answer A, "Print the URL once").**
  - **When.** The link cannot be written in any folder dash tries. A privacy shortfall is not this case: K-8 writes the file and notes it.
    - Under `dash serve`, dash tries the run folder, then a fresh `dash-link-*` folder of the system temp directory; `_dash_write_link` raises.
    - Under `python app.py` and `bokeh serve`, it tries the app's fresh `dash-link-*` folder; `_dash_private_page` raises inside `_dash_announce_key`.
  - **What.** Two lines, each flushed:
    1. `_DASH_LINK_UNWRITTEN % <the exception's type name>`;
    2. on the next line, alone and unprefixed, the full tokenized URL (`http://127.0.0.1:<port>/?token=<key>`, or the app path under `bokeh serve`).
  - **Where.** To the output of whoever started the server:
    - under `dash serve`, Stata's Results, and so any open Stata log. The launcher prints the lines itself, in Stata's Python, not through its redacted forwarding of the child's output;
    - under `python app.py` and `bokeh serve`, the app's own stdout. Under `bokeh serve`, K-5's hint line follows the URL.
    - **The browser opener does not undo it.** Under `--show` (`dash serve` without `nobrowser`, and `python app.py --show`) the app's `_dash_open_tokenized` writes its own page, `open.html`, through `_dash_private_page` (TR-13.8 step 3), except on darwin with `BROWSER` unset. In K-9's case that write fails too. The opener then opens nothing and prints one key-free line, `dash: the browser was not opened: its page could not be written (<type name>); open the dashboard's link instead.`, to the app's stdout (under `dash serve`, forwarded to Results through the launcher's redaction). It returns None, and `__main__` serves on (TR-13.10 item 7). It never falls back to the URL in argv or to `webbrowser.open(url)`, so the user opens the link K-9 printed.
  - **The server keeps serving.** Nothing is stopped, and no exit status changes.
  - **Exactly once.** No session ever prints it.
    - Per launch under `dash serve`: the launcher's first-answer block runs once.
    - Per process under `python app.py`: the key is made once, and `_dash_server_app` makes and announces none while `_DASH_SERVE_TOKEN` holds one.
    - Per app path per process under `bokeh serve`: `holder.linked` is marked before the attempt (TR-13.8a `_dash_bokeh_serve_key` step 5).
  - **Only here.** This is the one case in which the key is printed. The forwarded-output redaction, the access-log filter, the banner, the ready lines, the opener and every error message still never carry it. Under `dash serve` the child received the key on its pipe and prints nothing, so exactly one copy reaches Results.
  - **Form.** The URL is plain text, never an SMCL `{browse}` target (TD-2). It sits on a line of its own, so `c(linesize)` 79 does not wrap it (A4).

**Answer B: the launch from an open file (ratified 01oct2026, round 2, "Launch from open file"; S08 owns the launch).**
- **L-1. Order.** Every step sits inside S08's one Popen-to-final-wait `try:` (S08 A4), except the first:
  1. S08 opens the app with `O_NOFOLLOW` where available and verifies the open descriptor (`_dash_read_verified_app`, TR-08.8a: type, owner, `(st_dev, st_ino)`, size and SHA-256 checked on the descriptor). Nothing is started on a mismatch (r(7102), M4a).
  2. S08 calls Popen.
  3. S08 hands the verified bytes to the child as one `DASHAPP1 <n> <sha256>\n` frame (`_dash_hand_over`).
  4. S13 writes the key line on the same stdin pipe (TR-13.12 item 4).
  5. The pipe stays open, because its end of file is S08's parent watch (TD-4).

  The earlier order (check, Popen, then key) is kept, with S08's hand-over between Popen and the key.
- **L-2. One pipe, three readers in turn.**
  1. When S08 sends the app text over stdin, the child's bootstrap reads exactly that text with unbuffered `os.read` on descriptor 0, before the app's code runs.
  2. `__main__`'s `_dash_read_token_line(sys.stdin.fileno())` then reads the key line (Q-1).
  3. Then `_dash_watch_parent` waits for end of file.

  A bootstrap that read through a buffered `sys.stdin` or `sys.stdin.buffer` would swallow the key line. 13-01 checks for this and STOPs.
- **L-3. Bytes.** Every write to the child's stdin goes through S08's binary writer `_dash_child_stdin(proc)` (Popen stays `text=True`), so the key line is written as `(token + "\n").encode("ascii")`. On Windows a text pipe would turn `\n` into `\r\n` and break S08's framing. `_dash_read_token_line` still strips one trailing `\r`. `serve_token_probe.FakeStdin` records bytes (TR-13.15).
- **L-4. Command line.** `_cmd` is S08's open-file launch command. S13 adds only `"--token-stdin"` among the app's own arguments, after the app path and next to S08's `"--parent-watch"`. No argv element holds the key. S08 flips its own pins of the command line and writes the swap tests. S13's one pin of the command line, `test_the_token_goes_to_stdin_not_argv`, asserts only what S13 adds (TDD stubs).
- **L-5. If S08 sends the text over another inherited handle instead of stdin,** the key line is the first thing on stdin, and L-2 step 1 does not apply. 13-01 records which route is on the tree. `test_the_token_goes_to_stdin_not_argv` then asserts that the key line is stdin's only write. S08 round 2 uses stdin (section-08 R-9); L-5 does not apply on the planned tree.

**Decisions on the design's open questions** (ratified 01oct2026, except row 1, struck and replaced by K-1..K-8; rows 3 and 5 amended in round 2 by K-9):

| # | Question | Decision |
|---|---|---|
| 1 | `bokeh serve` (or `python app.py`) with `DASH_SERVE_TOKEN` unset | **Struck 01oct2026** ("Ensure that the token will never be missing"). Was: fail closed with a refusal page. Now: the app makes its own key (K-1..K-6), installs it for both gates, writes its link to a 0600 `link.html` in a fresh 0700 folder and prints the path. Sessions without the key are still refused. |
| 2 | An opt-out | None. The key passes through a reverse proxy unchanged. |
| 3 | "Stata opens the tokenized URL" | Through the child's `--show`, under the existing nobrowser / `$dash_nobrowser` / `nodraw` rule. Results shows the link file's path, never the key (A3, TD-2), except K-9's once-only fallback (round 2). |
| 4 | The Linux opener | A 0600 redirect file in a fresh `mkdtemp` folder. `XDG_RUNTIME_DIR` is not used (`tempfile` follows `TMPDIR`). A snap-confined browser that cannot read `/tmp` is a residual; the link file is the fallback. |
| 5 | The key in Results and logs | Never printed (A3, TD-2), except K-9's fallback (round 2, answer A): when no link file can be written anywhere, the link is printed once after a warning line, and the server keeps serving. |
| 6 | Throttling 403 log lines | Not in this section. Under `dash serve` stderr goes to a 20-line deque, so Stata is never flooded. Under a hand-run `python app.py` one redacted line per refused request is a recorded residual. |
| 7 | The parameter name | `token`. Bokeh reads no `token` argument; the research measured `/?token=T` reaching the page's JWT payload. |
| 8 | A fixed `DASH_SERVE_TOKEN` for `python app.py` | Yes, validated at start (rule 15). It is popped from the environment so no child inherits it. |

**Index deltas applied.**
- The BUGS.md entry is S01's open one, closed in place (A4).
- The TOK cases go in `test_serve_launch.cscript` before SRV-19, after S08's LC-02..LC-04 (A3, R1). No runner or hygiene-pin edit.
- `GAPS.md`, `GAPS2.md` and `ROADMAP.md` are S15's (A5). Their text is in "Notes for the closeout".
- The R2 anchors:
  - `_dash_new_token`, `_dash_token_valid`, `_dash_token_matches` and `_dash_tokenized_url` go after `"_dash_server_transforms"`;
  - the other copied helpers go after `"_dash_watch_parent"`, S08's last entry (S08 R-3).
- Commit subject: `Require a per-launch key to open the served dashboard (WP-29 P0.12a)`.

## Overview

`dash serve`, `python app.py` and `bokeh serve app.py` serve the dashboard with no credential. The app binds loopback, and the help draws the conclusion from that:
- "only this machine can reach it" (dash.sthlp:1464-1465);
- "There is no password" (:1476);
- "the generated app is a single-user tool" (:1496).

On a machine with more than one account, "this machine" is every account. Re-measured at 7421d3d (Evidence §1): a second local client with no Origin and no credential got `GET /` 200 and received, through `bokeh.client.pull_session`, a ColumnDataSource with all 74 values of auto's `mpg`. The app's source has 0 occurrences of `auth_provider`. The only gate in `make_document` is the rate limiter. Its bucket key is `remote_ip`, so every local account also shares the owner's `127.0.0.1` session budget. twoway has no network surface at all: while a twoway graph was drawn, `lsof` found no socket on the Stata process.

**After this section, every launch makes a new 256-bit key, and nothing is served without it.**
- **Gate A, the Tornado layer** (`python app.py` and `dash serve`). A Bokeh `AuthProvider` refuses every page, `/autoload.js`, `/metadata` and websocket request that lacks the key with a constant 403, before the handler runs.
- **Gate B, the document layer** (every mode, and the only gate under `bokeh serve`, which gives a script no Tornado hook). `make_document` refuses any session without the key, before the rate limiter and before the data is decoded.
- **What stays open.** `/health` and BokehJS's `/static` files answer as before; they hold no data.
- **How `dash serve` handles the key:**
  - it hands the key to the app on S08's stdin pipe, never in argv;
  - it writes the link (`http://127.0.0.1:P/?token=<key>`) to a 0600 file in its private run folder;
  - it prints only that file's path. When no file can be written anywhere, it prints a warning line and the link once, and keeps serving (K-9);
  - it opens the link through the child's `--show`, without putting it on any command line.
- **Other ways to run the app.** The app never runs without a key (ratified 01oct2026, K-1..K-8).
  - `python app.py` uses `DASH_SERVE_TOKEN` or a `--token-stdin` line when given (an invalid one stops it, exit status 2). Otherwise it makes a key before any session, writes the link to a 0600 `link.html` in a fresh 0700 folder, and prints only that file's path. If that file cannot be written, it prints a warning and the link once, and serves on (K-9).
  - `bokeh serve app.py` uses `DASH_SERVE_TOKEN` when set. Otherwise the first session makes one key for the process, and the first page request writes the link file and prints its path; every session without the key is refused.
- **No log holds the key,** except K-9's warned, once-only fallback. Neither Tornado's access log nor the launcher's forwarded output holds the key or any query string.
- **The help says what is true:** only holders of the link; where the key lives; and that plain HTTP beyond loopback needs a tunnel or a TLS proxy.

**Test order (CLAUDE.md rule 7) and commit rule (index step 1).**
- **Red first (13-03 to 13-05).** These tasks write every regression test (pytest and cscript) and run them against the batch-2 base (`<scratch>/batch-2-base.txt`). The failure text goes to `<scratch>/13-P0.12a-failure.txt`, and nothing is committed.
- **Fix (13-06 to 13-08).** These make the fix.
- **Flips (13-09 to 13-12).** These flip the pinned tests and helpers, never deleting one.
- **Help (13-13).** This updates `dash.ado`'s lines and the help.
- **Green (13-14 and 13-15).** These turn the cscripts and the changed pytest files green.
- **Close and commit (13-16).** This task closes the BUGS.md entry, replaces both CHANGELOG markers, deletes `WP29_OPEN["P0.12a"]`, runs the full suite once and makes the ONE commit. Its body opens with the saved failure text.

## Risk: [red] — a security control on every served session, in code 13 sections touch, that changes how every user opens a served dashboard

**Why.** Every served session now passes two gates. One that is too strict blanks every dashboard. One that is too lax is the defect itself.

**Risk factors.**
1. **Bokeh internals.** The gates rely on internals measured only on bokeh 3.8.0 (Stata's Python) and 3.9.0:
   - `AuthRequestHandler.prepare` awaiting `get_user_async` before `get()`;
   - `WSHandler.open` being `@web.authenticated`;
   - the session JWT's `arguments` payload;
   - `contexts.py` falling back to `request.arguments`.
2. **Test churn.** About 14 test files open sessions or fake requests without a key: helpers, fakes, in-process session documents and live servers.
3. **`_dash_launch_app` and the emitted `__main__`.** They are rewritten by S08 in batch 1, and S08's erase-on-ready, parent watch and Break handling must keep working: the banner prefix, the open stdin pipe, and `poll()` outside broad excepts.
4. **Where the key goes.** It can reach places it must not: argv (`ps`, `/proc/PID/cmdline`), the app file, logs (Tornado logs a 403 with its URI), Stata's SMCL log, the IPv6 loopback, and `$BROWSER`.
5. **Unauthenticated decoding.** A websocket JWT is decoded before the client is authenticated, and Bokeh's `get_token_payload` decompresses its zlib member without a bound.
6. **Users.** Bookmarks of `http://localhost:5006/` stop working. `bokeh serve app.py` without the variable serves only through the link file it writes, and only with `--allow-websocket-origin 127.0.0.1:<port>` (K-5).
7. **The self-made key (ratified 01oct2026).** Under `bokeh serve` it relies on two more measured Bokeh behaviours: `sys.modules` persisting across sessions, and `_RequestProxy` forwarding `connection` to Tornado's request (K-4).
8. **Round 2.**
   - Answer A puts the key in the starter's output and log in one case (K-9).
   - Answer B makes the key share the stdin pipe with S08's app-text hand-over (L-2). A buffered read in the child would lose the key, and a key line written before the text would break S08's framing.

**Mitigation.**
1. **Two independent gates,** each pinned live on the installed bokeh and in process. The research measured both gates on 3.8.0 and 3.9.0. Under `bokeh serve`, Gate B alone holds.
2. **Centralised keys in tests.** One shared key (`serve_token_probe.TEST_TOKEN`), with the helpers made key-aware (`_Launched.url`, `_Served`, `_pull`, `_Req`, `_load_app`, `_LiveApp`). Flips are mechanical and recorded, never deleted (R7).
3. **Stated invariants.**
   - The banner prefix is kept.
   - The key line is written after S08's app text, and the pipe is kept open (TD-4, L-1, L-2).
   - The write sits inside S08's one try/finally (S08 A4).
   - The 429 branch sits inside the `/health` try, with `poll()` still outside it (S08 A1).
4. **Each path to the key has a test:**
   - argv: `test_the_token_goes_to_stdin_not_argv`;
   - the app file: `test_the_app_source_holds_no_key`;
   - logs: `test_the_access_log_never_carries_the_token`, TOK-03;
   - the IPv6 squat: `test_the_link_never_reaches_an_ipv6_squatter`;
   - `$BROWSER`: `test_opening_never_puts_the_token_in_argv`.
5. **The JWT is bounded before Bokeh decodes it.** `_dash_ws_payload` refuses a protocol header over 16,384 characters, then a payload that inflates past 262,144 bytes (TR-13.3, `test_a_jwt_that_inflates_is_refused_quickly`).
6. **Users are told.** A CHANGELOG "Changed behaviour" line, a refusal page that says where the link is and names `DASH_SERVE_TOKEN`, the printed link-file path with the `--allow-websocket-origin` hint under `bokeh serve`, and a help Access row.
8. **The self-made key is pinned live** under both `python app.py` and `bokeh serve`, on the installed Bokeh (`TestTheServedAppRequiresItsToken::test_a_keyless_start_makes_a_key_and_a_private_link`, `TestBokehServeAlwaysHasAKey`), and in process (`TestTheSessionGate::test_no_configured_token_makes_one_and_still_refuses`).
9. **Round 2 is pinned.**
   - K-9 is pinned in process and live under all three routes: `test_an_unwritable_link_is_printed_once_with_a_warning`, `test_a_key_whose_link_cannot_be_written_is_printed_once_and_served`, `test_the_bokeh_serve_link_that_cannot_be_written_is_printed_once`, `test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served` and the four live `..._printed_once...` / `..._prints_it_once...` tests.
   - The browser opener cannot undo it: `test_an_opener_that_cannot_write_its_page_opens_nothing_and_returns_none`, and live under `--show`, `test_a_keyless_show_start_whose_link_cannot_be_written_prints_it_once_and_serves`.
   - L-2 is pinned by `test_the_token_goes_to_stdin_not_argv` and, live through S08's real launch, by TOK-02.
7. **Checkpoints.** 13-02 reports HIGH/CRITICAL impact (`_dash_launch_app` is expected HIGH, index R8) and these decisions before any product edit.

## Dependencies

- **Depends on: 08** (batch 1, merged before batch 2). This section uses S08's:
  - private run folder, from `_dash_private_root` and `_dash_run_open`;
  - `_dash_private_write(path, text, exclusive=True)` and `_dash_private_msg`;
  - `_dash_private_run_of` and `_dash_erase_quietly`;
  - the stdin pipe and `--parent-watch` (`_dash_watch_parent`);
  - `_dash_stop_child`, `_dash_stata_poller` and `_DashServeInterrupted`;
  - erase-on-ready, keyed on `Bokeh Server running at`;
  - the ready line's Break hint;
  - the test helper `test_serve_lifecycle._url`;
  - the TOK slot after LC-02..LC-04 in `test_serve_launch.cscript`;
  - (round 2, answer B) the launch from an open file: S08's verification of the open descriptor, its hand-over of the app text to the child, the child's unbuffered read of that text, and S08's flipped pins of the command line (L-1..L-5).

  It also uses S01's open BUGS.md entry `The served app has no credential, so any local account can open a session and read the data`, the `WP29_OPEN["P0.12a"]` key, and the two `<!-- WP-29 P0.12a -->` markers (end of `### Security` and end of `### Changed behaviour (may need your do-files changed)`).
- **Blocks:** nothing but S15.
- **Parallel batch: 2.** Can run with 10, 11 and 12. Merge order is `S10, S11, S12, S13`. S13 is last because S12 also edits `ServerAppBuilder`, and the served-name guard must see the final app text (index).
- **Why after 08:** the key is written into S08's private run folder and handed over S08's stdin pipe. The launcher S13 edits is S08's rewrite (index "13 ← 08").

## Evidence

### 1. Measured (Stata through `scripts/stata_slot.sh`; Python probes on the same tree)

| What | Command | Result |
|---|---|---|
| twoway has no listener | `tw.do`: `sysuse auto` / `twoway scatter mpg weight` / `sleep 12000`; while drawn, `lsof -a -p <pid> -iTCP -sTCP:LISTEN` and `lsof -a -p <pid> -i` on the stata-mp pid | `pids: 5906`; both lsof calls printed nothing |
| The app has no credential (GAPS2-I3-a) | `head_probe.py` (python 3.14.5, bokeh 3.9.0): `ServerAppBuilder` on auto's mpg and weight, `python app.py --port P`, then `GET /` and `pull_session(url)` with no token and no Origin | `app.py: auth_provider 0`; `GET / (no token): 200 3630`; `pull_session (no token, no Origin): CDS with mpg: 1 rows 74 first [22.0, 17.0, 22.0, 20.0, 15.0]` |
| The same on real `dash serve` (research) | `dash serve, port(54138) timeout(1) nobrowser` under Stata's Python (3.13.9, bokeh 3.8.0, tornado 6.5.1), probed from a second interpreter | `/health` 200; `GET /` 200 (3,787 bytes); `pull_session` got index, mpg and weight, 74 rows |
| SMCL logs keep link targets | `m1.do` (TD-2) | text log: `LINKTEXT`; SMCL log: `{res}{browse "http://127.0.0.1:1/?token=SECRETSMCL":LINKTEXT}`; logs `-rw-r--r--` |
| A probe thread runs during `dash serve` | `m1.do` (TD-3) | `THREAD_RESULT {'health': 200, 't_health': 2.63, 'root': 200, ...}`; listener SIGTERMed; `SERVE_RC=0`, `ELAPSED=4` |
| IPv6 squat (review, `squat.py`) | listeners on `127.0.0.1:54911` and `[::1]:54911`, then `urllib` and `curl` to `http://localhost:54911/?token=SECRET` | both reached the `[::1]` listener: `SQUATTER-v6 /?token=SECRET` |
| `::` is IPv6-only | `v6.py` (TD-1) | `'::' ['AF_INET6:::'] {'127.0.0.1': 'ConnectionRefusedError', '::1': 'connects'}` |
| Line wrap (review, `wrap.log:41`) | a ready line with a prefix at `c(linesize)` 79 | it wrapped mid-token (`...token=Ab_-Ab_-Ab_-Ab_-Ab_-A` / `> b_-...`); a 73-character URL alone stayed whole |
| `c(mode)` in batch | `m1.do` | `MODE=[batch] LINESIZE=79` |

**Bokeh capability.** The research ran `proto_server.py` and `proto_probe.py` with an `AuthProvider` that accepts `?token=` or the JWT payload's `arguments`. Results were identical on bokeh 3.8.0 and 3.9.0:

| Request | Result |
|---|---|
| `/health`, `/static/js/bokeh.min.js` | 200 |
| `/`, `/?token=<43 x>`, `/?token=T&token=T` | 403 |
| `/?token=T` | 200; the page JWT's payload `arguments` = `{token: T}` |
| `/autoload.js`, `/metadata` without the token | 403 |
| `pull_session` without the token, or with a wrong one | `OSError` 403 |
| `pull_session(arguments={'token': T})` | connected, has data |
| raw `/ws` with the page's JWT, Origin localhost | 101, then ACK |
| `/ws` with a forged unsigned JWT, no args or wrong args | 403 |
| the page JWT with Origin `http://evil.example` | 403 (the origin check still applies) |

Further facts from the same runs:
- `make_document` ran only for authenticated requests.
- The 403s keep dash's CSP, X-Frame-Options DENY, nosniff and no-referrer (`proto403.py`).
- `HTTPError(403, reason=const)` puts only that constant in the status and body.
- Tornado logs a 403 at WARNING with the raw request URI, token included.
- Under `bokeh serve app.py`, a `make_document` gate on `session_context.request.arguments['token']` against env `DASH_SERVE_TOKEN` refused an untokened pull, served a tokened one, and refused every session with the variable unset (`bs/probe.py`, both versions). The last behaviour is superseded by the ratified self-made key (Evidence §6).
- `sign_sessions` is not needed. It would also break `bokeh.client` with a token, because the client mints unsigned JWTs.

### 2. The code today (anchors at 7421d3d; S08 shifts the launcher and `__main__`: locate by symbol and quoted text)

**The session gate is the rate limiter alone.** `make_document`, dash_render.py:30006-30028:

```python
30006    "    doc.template = _dash_served_template()",
30009    "    _dash_reset_notes()",
30015    "    try:",
30016    "        _req = doc.session_context.request",
30017    "        _client_ip = _client_ip_from_request(_req)",
30020    "    if not _SESSION_LIMITER.is_allowed(_client_ip):",
30027    "        return",
30029    "    spec, df, meta = _load_spec_and_data()",
```

**The Server has no auth provider.** `_dash_server_app`, :31599-31657:

```python
31599    "def _dash_server_app(port=None, address=None, origins=None):",
31622    "    _kw = {'address': address or '127.0.0.1'}",
31651    "    return Server(",
31652    "        {'/': Application(FunctionHandler(make_document))},",
31655    "        num_procs=1,",
31656    "        extra_patterns=[('/health', _HealthHandler)],",
31657    "        **_kw",
```

**The emitted `__main__` opens `/` with no secret and prints localhost.** :31711-31718:

```python
31712    "    if _a.show:",
31713    "        _server.io_loop.add_callback(_server.show, '/')",
31717    "    print(f'Bokeh Server running at http://localhost:{_port}/')",
31718    "    print(f'Health check:  http://localhost:{_port}/health')",
```

**The `*` warning.** :31702-31705: `'dash: WARNING -- it holds *, so any web site can open a session with this dashboard and read what it draws. ...'`

**The launcher.** `_dash_launch_app`, :31944-32108:
- argv `[sys.executable, app_path, "--port", str(port)]` plus `--show`/`--timeout` (31992-31996);
- Popen without stdin (31999), which S08 changes in commit 1 to `[sys.executable, "-P", "-c", _DASH_BOOT, app_path, …]` with `stdin=subprocess.PIPE` and a framed hand-over (R-9), and in F2 adds `--parent-watch`;
- the ready line:

  ```python
  32064            urllib.request.urlopen(
  32065                "http://127.0.0.1:%d/health" % port, timeout=1.0)
  32067            print(
  32068                "dash: the server answers at http://localhost:%d/ "
  ```

- the stderr tail quoted raw into the RuntimeError (32094-32107).

**Bokeh's JWT decoding.** bokeh/util/token.py:152-156 (3.8.0):

```python
152    decoded = json.loads(_base64_decode(token.split('.')[0]))
153    if _TOKEN_ZLIB_KEY in decoded:
154        decompressed = zlib.decompress(_base64_decode(decoded[_TOKEN_ZLIB_KEY]))
```

The decompression has no bound. Bokeh itself calls it in `WSHandler.open` (ws.py:123-143), which is `@web.authenticated`. Once Gate A exists, only key holders reach Bokeh's call, and dash's own pre-auth decode must be bounded (TR-13.3).

**The opener.** `webbrowser` in Python 3.13.9:
- :556-557: `if "BROWSER" in os.environ: userchoices = ...`, so a set `$BROWSER` runs a command with the URL in argv;
- :597-615: `MacOSXOSAScript.open` writes `open location "<url>"` into `os.popen("osascript", "w")`, so on darwin the URL goes to osascript's stdin.

**The help.** dash.sthlp:
- 1464-1465: "binds the loopback interface, so by default only this machine can reach it";
- 1476: "There is no password.";
- 1494: "warns when the variable holds {cmd:*}, which lets any website open a session";
- 1496: "So the generated app is a single-user tool."

### 3. The import boundary (A9)

`python3 -c "import sys; sys.path.insert(0,'.'); import dash_render; print('tornado' in sys.modules)"` printed `False`. A following `import bokeh.server.auth_provider` put `tornado.web` in `sys.modules` (`after auth_provider import tornado: True`). `_dash_server_transforms` already keeps tornado lazy for this reason (dash_render.py:2425-2427), and its nested `_DashSecurityHeaders` is mapped as `_dash_server_transforms.<locals>._DashSecurityHeaders.transform_first_chunk` (test/function_test_map.py:550).

### 4. Tests that pin today's behaviour (flip, never delete; each with a `Flipped:` line)

**`test/test_help_claims_4.py`:**
- `TestTheLauncherServes::test_a_client_that_sends_no_origin_is_admitted` (:1675-1690) pins the I3 hole. It becomes: no Origin plus the key is admitted, and no Origin without the key is refused (OSError 403).
- `TestTheLauncherServes::test_a_refused_session_gets_the_refusal_page` (:1658-1673): the page GET and the pull gain the key, so it still pins the 429 page.
- `TestTheLauncherOpensABrowserOnlyWhenAsked::test_show_and_timeout` (:1603-1652) asserts `asked.get("callbacks") == ["show"]` and `asked["later"] == (60, "stop")`. It becomes: no `show` callback; one browser open with a `file://` URI (BROWSER set) or the osascript route; `(60, "stop")` among the recorded `call_later`s (a list now); `auth_provider` in the fake Server's kw.
- `TestUnderBokehServe::test_the_session_limits_do_not_hold` (:1519-1556): `monkeypatch.setenv("DASH_SERVE_TOKEN", TEST_TOKEN)` for the CodeHandler half; `_Req` carries the key.

**`test/test_server_serves.py`:**
- `TestTheLauncherOpensNoBrowser::test_show_is_opt_in` (:393-402) searches for `_server.io_loop.add_callback(_server.show`. It searches for `_dash_open_tokenized(` instead, with `_a.show` within 400 characters before it.
- Helpers `_Served`, `_Launched` and `_pull` (:92-214) carry the key (TR-13.15). This keeps green, without edits, the four classes `TestTheServedDocumentIsNotEmpty`, `TestTheServedDocumentHasTheContent`, `TestTheHtmlIsNotTheDocument` and `TestHealthOnTheLauncher` (`test_the_dashboard_is_served_too`, `test_loopback_by_either_name_is_accepted`).

**`test/test_csp.py`:**
- `TestThePythonLauncherServes::test_the_websocket_still_opens` (:686-695): the pull gains `arguments=token_args()`.
- `_fetch` (:309-315) goes through the key-aware `_Launched.url`.

**`test/test_adversarial_matrix.py`:**
- `_Req` (:1125-1128) and `_load_app` (:1100-1111) carry the key.
- `_LiveApp` (:2290-2378): env `DASH_SERVE_TOKEN`, and `session(origin, jwt=None)` fetches `/?token=`.
- `TestSessionOrigin::test_a_star_in_the_environment_is_warned_of` (:2558-2572) asserts `"any web site can open a session"`. It becomes `"the websocket origin check admits every web site"`.
- The module docstring (:18-40) says "dash has no authentication model".

**`test/test_server_rate_limit.py`:**
- `_Req` (:66-69) carries the key.
- The fixtures that exec the app set `ns["_DASH_SERVE_TOKEN"] = TEST_TOKEN`.
- `TestTheLauncherFlags::test_the_launcher_help_lists_every_flag` (:989-995) gains `--token-stdin`.

**`test/test_server.py`:** `TestRateLimiterEnforcement::test_make_document_adds_429_div_when_rate_limited` and `::test_make_document_proceeds_normally_when_allowed` (:4425-4505). `_FakeSessionContext.request` gains `arguments`, and the namespace gains `_DASH_SERVE_TOKEN`.

**Launcher fakes:**
- `test/test_serve_launcher.py`: `_fake_popen_class` (:99-131) and the inline `_FakeProc`s (:241-305) get `FakeStdin`.
- `test/test_serve_launcher.py::TestTheLauncherReportsReadiness` (or the class holding the needle at :276): the needle becomes `dash: the server answers at http://127.0.0.1:%d/`.
- `test/test_help_claims_2.py::_FakeProc` (:765-790) gets `FakeStdin`.
- `test/test_resource_limits.py::_Proc` (:1359-1366) needs no change: Popen is never reached there (port refusal). Verify only.

**S08's tests** (on the tree): S08's round-2 flips of the launcher's command-line pins are already on the base. S13 builds on S08's flipped form and re-pins none of it (L-4). `test/test_serve_lifecycle.py` fakes get `FakeStdin` (Q-6). `_url` gains a key argument. Any folder-empty assertion follows Q-3. `test/test_help_claims_4.cscript` LC-01 follows Q-3.

**`test/test_security_surface.py::TestServeBindsLoopbackByDefault::test_the_help_does_not_claim_an_access_control_it_has_not_got`** (:98-114) is kept. The Origin claim stays false, and the new help test sits beside it.

### 5. GitNexus

GitNexus has no index for this repository: S06 and S08 record that `list_repos` lists only TYME and PhotoShootPlannerPro. Task 13-01 runs `gitnexus analyze` in the worktree and impact analysis on:
- `_dash_launch_app` (expected HIGH, index R8);
- `ServerAppBuilder._glyph_layer_lines` (the copy lists);
- `ServerAppBuilder._generate_app_source` (the emitted app);
- `_dash_build` (dash.ado; grep callers if unresolved).

### 6. The self-made key (ratified 01oct2026; measured the same day)

Probes in `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp29r/s13/`, each run under `/opt/anaconda3/bin/python3` (Python 3.13.9, Bokeh 3.8.0, Tornado 6.5.1: Stata's Python) and `/opt/homebrew/bin/python3` (Python 3.14.5, Bokeh 3.9.0, Tornado 6.5.5), with identical results on both.

| What | Command | Result |
|---|---|---|
| `bokeh serve` runs a script only per session | `bsapp.py` (a `sys.modules` holder counting runs) under `python -m bokeh serve bsapp.py --port P`; `grep EXEC` after 6 s, then two `curl` GETs of `/bsapp` | before any request: `no EXEC before session`; then `EXEC 1 first True name bokeh_app_38b1… argv ['bsapp.py'] … url /bsapp` and `EXEC 2 first False name bokeh_app_b323…`: a fresh module per session, the holder kept, `sys.argv` replaced by the script's own |
| The server-side address of the session's request | `bsapp2.py` prints `req.connection.stream.socket.getsockname()`; `curl http://127.0.0.1:P/bsapp`, `curl -g "http://[::1]:P/bsapp"`, then `bokeh.client.pull_session` | `LOCAL ('127.0.0.1', P)`, `LOCAL ('::1', P, 0, 0)`, and for the pull `LOCAL ERR AttributeError: 'NoneType' object has no attribute 'socket'` |
| The ratified flow, end to end, under `bokeh serve` | `proto.py` (holder key, `mkdtemp` + `O_EXCL\|O_NOFOLLOW` 0600 `link.html`, `atexit` cleanup, Gate B) under `env -u DASH_SERVE_TOKEN python -m bokeh serve proto.py --port P`; `probe.py P <log> <pid>` | `ws_first_unkeyed div=['403 refused DASH_SERVE_TOKEN'] link_lines_after_ws_first 0`; `GET_unkeyed 200`; `GET_unkeyed_again 200`; `link_lines 1`; `file_mode 0o600 dir_mode 0o700`; `link_host True path /proto keylen 43`; `keyed_pull rows=74`; `wrong_pull div=['403 refused DASH_SERVE_TOKEN']`; `keyed_GET 200`; `key_in_server_output False`; `dir_exists_after_SIGINT False` |
| The websocket origin under `bokeh serve` | `wsprobe.py P <log>`: the keyed page's JWT, then a raw `/proto/ws` upgrade with `Origin: http://127.0.0.1:P` and with `Origin: http://localhost:P`; once without and once with `--allow-websocket-origin 127.0.0.1:P` | without the flag: `ws origin 127.0.0.1: 403 \| ws origin localhost: 101`; with it: `ws origin 127.0.0.1: 101 \| ws origin localhost: 403` |
| Bokeh's `Server` binds in its constructor; `stop()` before `start()` frees the port | a heredoc building `Server({'/': …}, port=P, address="127.0.0.1", num_procs=1)`, connecting, then `srv.stop()` and connecting again | `after Server() before start(): connects srv.port P`; `stop ok \| after stop: ConnectionRefusedError` |
| The key's form | `python3 -c "import secrets,re;k=[secrets.token_urlsafe(32) for _ in range(1000)];print(set(map(len,k)), all(re.fullmatch(r'[A-Za-z0-9_-]{43}',x) for x in k), len(set(k)))"` | `{43} True 1000` |
| No earlier hook for a script | `grep -n "on_server_loaded" bokeh/application/handlers/{code,script,handler}.py` and `sed -n 910,914p bokeh/command/subcommands/serve.py`, both versions | only `handler.py` defines it (:143 in 3.8.0, :141 in 3.9.0), as the base no-op; `CodeHandler` and `ScriptHandler` do not override it. `serve.py` sets `AuthModule(...)` only from `--auth-module` (or Bokeh's `auth_module` setting), else `NullAuth()`: no Gate A under `bokeh serve` |

### 7. Round 2 (ratified 01oct2026; measured the same day)

Probes in `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp29r2/s13/`. They are prototypes of S08's route, which S08 specifies: they show that the key line can share the pipe, not how S08 must write it.

| What | Command | Result |
|---|---|---|
| App text over stdin, then a key line, then end of file; a swap after verification | `fdlaunch.py d` under Python 3.13.9 and 3.14.5. It opens `app.py` with `O_RDONLY\|O_NOFOLLOW\|O_CLOEXEC`, checks `fstat` (regular, own uid, `st_nlink == 1`) and reads the text. It then replaces `app.py` with `print('EVIL')` and starts `[python, "-c", BOOT, app, "--port", "5006"]` with `stdin=PIPE`. It writes `b"%d\n" % len(text)`, the text and `b"KEYKEYKEY\n"`, then closes stdin. `BOOT` reads with `os.read(0, …)`, drops `sys.path[0]`, primes `linecache` and runs `exec(compile(src, app, "exec"), __main__.__dict__)` | `GOOD __main__ d/app.py ['d/app.py', '--port', '5006']`; `KEY KEYKEYKEY`; `EOF b''`; the traceback line shows the app's source (`raise ValueError('tb')`); no `EVIL`; rc 0 (both versions) |
| A real generated app through the same route | `realapp.py`: `test_adversarial_matrix._app_source` (1,252,167 bytes), `app.py` swapped for `print('EVIL')` before the launch, the text sent over stdin | `health,root (200, 200)` (the base app has no key yet); `EVIL` not in its output |
| A process-wide patch reaches every later `import tempfile` (the live K-9 tests) | `mk.py`: `tempfile.mkdtemp = _no`, then `importlib.import_module("tempfile").mkdtemp is _no` | `True`; `bokeh.__main__` has `main` on 3.8.0 and 3.9.0 (`True True`) |

## User stories

- **US-13.1** As a dashboard publisher on a shared machine, I want my served dashboard to open only for the link dash gives me, so that no other account on the machine can read my data while the server runs.
- **US-13.2** As a `dash serve` user, I want Stata to open the dashboard for me as before (unless I said `nobrowser`) and to tell me where its link is, so that opening it is no harder than before.
- **US-13.3** As a user running `python app.py` myself, I want the app to make its own key and tell me where its link is when I give none, or to use a key I choose (`DASH_SERVE_TOKEN`, `--token-stdin`), so that it is never served without a key and I can still script a long-running deployment.
- **US-13.4** As an operator using `bokeh serve app.py`, I want the app to make a key when I set none, write its link to a file only I can read and print that file's path, and show any session without the key a page saying where the link is and how to choose a key, so that the dashboard is never served openly and I can still open it.
- **US-13.5** As the maintainer, I want the key never to reach argv, the app file, a log or Stata's output, and the help to say where it does live, so that the protection is not undone by its own messages.
- **US-13.6** (round 2, answer A) As a user whose disk will not take the link file anywhere, I want dash to print the link once, warn me that it is now in my output and log, and keep serving, so that I can still open my dashboard and know what to protect.

## Business requirements

- **BR-13.1** Without the launch's key, no page, session, autoload script, metadata response or data row reaches any client, under `dash serve`, `python app.py` and `bokeh serve app.py`. `/health` and BokehJS's static files answer as before and hold no data.
- **BR-13.2** With the key, the dashboard is served exactly as before in every mode, including to a client that sends no Origin. The websocket Origin check still applies to browsers.
- **BR-13.3** Key rules:
  - The served app never runs without a key, in any mode (ratified 01oct2026).
  - A key is new at every launch (256 bits), unless the operator supplies one. The app makes it itself when none is supplied: before any session under `python app.py`, and at the first session (which it refuses) under `bokeh serve`, once per server process.
  - It is compared in constant time.
  - Its form is 32 to 128 of A-Z a-z 0-9 _ -. Any other value is refused where it is given, without echoing it: exit status 2 at start under `python app.py` and `dash serve`, one warning and every session refused under `bokeh serve` (K-1), or 403 on a request.
- **BR-13.4** The key never appears in the app file, the spec or data, argv, Stata's Results, any Stata log, Tornado's access log, the launcher's forwarded output, or anything the app itself prints. The one exception is K-9 (round 2, answer A): when no link file can be written anywhere, the full link is printed once, after a warning line, to the output of whoever started the server.
- **BR-13.5** `dash serve`:
  - writes the link to a file only the user can read, removed when the server stops (on a disk that keeps no file permissions the file is written anyway and one `dash: note:` names it; K-8);
  - prints that file's path;
  - when no file can be written (the run folder, then a fresh private folder), prints a warning line and the link once, and keeps serving (K-9);
  - opens the link unless `nobrowser`, `$dash_nobrowser` or a `nodraw` graph says not to;
  - names `127.0.0.1` (or an explicit `--address`) in every link it prints, writes or opens, never `localhost`.
- **BR-13.6** When the app made its own key (ratified 01oct2026):
  - it writes the link to `link.html`, 0600, in a fresh 0700 folder, and prints that file's path on a line of its own, never the key or the link;
  - under `python app.py` this happens before any session, and the folder is removed when the app stops;
  - under `bokeh serve app.py` this happens at the first page request, once per app path per process, with a line naming `--allow-websocket-origin 127.0.0.1:<port>`; the folder is removed at the process's exit;
  - a key whose link file cannot be written at all (an operating-system failure or an anti-hijack refusal) is still served (round 2, answer A). The app prints K-9's warning line and the link once: once per process under `python app.py`, once per app path under `bokeh serve`. No later session prints it again. Only an address no link can name still stops `python app.py` (exit status 2);
  - a link file the disk will not keep at 0600 is still written and served, with one `dash: note:` line naming it (K-8, answer 2); no privacy condition stops the app.

  When the key was given (`DASH_SERVE_TOKEN` or `--token-stdin`), the app writes and prints no link. An invalid given key stops `python app.py` with exit status 2 and refuses every `bokeh serve` session. Every session without the key gets a constant page saying where the link is and naming the variable.
- **BR-13.7** A client without the key spends no session budget, and a refusal reflects nothing from the request. The 403 carries dash's four security headers.
- **BR-13.8** The help states who can open the dashboard, where the key lives, and what plain HTTP beyond loopback exposes. It no longer says "only this machine can reach it", "There is no password" or "single-user tool".
- **BR-13.9** CHANGELOG lists the security change under `### Security`, and the changed addresses and `bokeh serve` rule under `### Changed behaviour`.

## Technical requirements

All new module-level code in `dash_render.py` goes after `_dash_harden_origin_check` (2498-2517) and before the `_DASH_VIEWPORT_META` comment (2520). No default argument reads a module constant: each is read in the body, so the copy order in the app cannot matter.

**TR-13.1 Constants.**

```python
_DASH_TOKEN_ARG = "token"
_DASH_TOKEN_ENV = "DASH_SERVE_TOKEN"
_DASH_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{32,128}")
_DASH_TOKEN_LINE_MAX = 256
_DASH_TOKEN_REFUSAL = ("Forbidden: this dashboard opens only through the "
                       "link that holds its key")
_DASH_TOKEN_REFUSED_HTML = (
    '<h2 style="font-family:sans-serif;color:#c00">403 Forbidden</h2>'
    '<p style="font-family:sans-serif">This dashboard opens only through '
    'the link that holds its key.  When it was started without a key, it '
    'made one, wrote the link to a file named link.html that only the '
    'account that started it can read, and printed that file\'s path where '
    'it was started: open that file.  To choose the key instead, set '
    'DASH_SERVE_TOKEN to 32 to 128 of the characters A-Z a-z 0-9 _ - before '
    'starting it, and open its address followed by ?token= and that '
    'value.</p>')
_DASH_WS_PROTOCOL_MAX = 16384
_DASH_JWT_PAYLOAD_MAX = 262144
_DASH_QUERY_RE = re.compile(r"(?<=\S)\?[^\s?#]*=[^\s#]*")
_DASH_REDIRECT_TTL_S = 60
_DASH_KEY_HOLDER = "_dash_serve_key"
_DASH_LINK_SAID = ("dash: the dashboard opens only through its link, which "
                   "holds a key made for this run; the link is in this file, "
                   "which only you can read:")
_DASH_BS_ORIGIN_HINT = ("dash: under bokeh serve the link's page stays blank "
                        "unless the server was started with "
                        "--allow-websocket-origin 127.0.0.1:%d (Bokeh admits "
                        "only localhost by default).")
_DASH_LINK_UNWRITTEN = ("dash: WARNING -- the dashboard's link could not be "
                        "written to a file (%s), so it is printed on the next "
                        "line, this once; it holds the dashboard's key, which "
                        "is now in this output and in any log of it, and "
                        "anyone who can read them can open the dashboard "
                        "while this server runs.")
```

Each has a comment naming P0.12a and its threat. The last four are new:
- `_DASH_KEY_HOLDER` (ratified 01oct2026, K-4): the `sys.modules` name of the `bokeh serve` process holder;
- `_DASH_LINK_SAID` (K-3): the line before a printed link-file path, which is also the launcher's ready line 2;
- `_DASH_BS_ORIGIN_HINT` (K-5): the `bokeh serve` origin hint;
- `_DASH_LINK_UNWRITTEN` (round 2, K-9): the warning line before the one printed link. `%s` takes only an exception's type name, never a path, a value or the key.

That makes fourteen constants.

**TR-13.2 The key.**
- **`_dash_new_token()`** returns `secrets.token_urlsafe(32)`: 43 characters, 256 bits. `secrets` is already imported at dash_render.py:70.
- **`_dash_token_valid(value)`:**
  - bytes or bytearray are decoded as ASCII; failure gives False;
  - then `isinstance(value, str) and len(value) <= 128 and _DASH_TOKEN_RE.fullmatch(value) is not None`.
- **`_dash_token_matches(given, expected)`:**
  - False unless both are valid;
  - bytes `given` are decoded;
  - then `import hmac; return hmac.compare_digest(given.encode("ascii"), expected.encode("ascii"))`.
  - No `==` or `!=` comparison on a key anywhere.
- **`_dash_one_value(values)`:** a list or tuple of exactly one element gives that element; any other list or tuple gives None; anything else is returned as is.
- **`_dash_env_token(environ=None)`:** `environ` defaults to `os.environ`. Returns `environ.get(_DASH_TOKEN_ENV)` when valid, else None.

**TR-13.3 Reading a request's key.**
- **`_dash_ws_payload(protocol)`** returns a dict or None. It never raises.
  1. Refuse when `len(protocol) > _DASH_WS_PROTOCOL_MAX`.
  2. `parts = [p.strip() for p in protocol.split(",")]`; it must be exactly `["bokeh", jwt]`.
  3. Decode `jwt.split(".")[0]` with `base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))` and `json.loads` it. It must be a dict.
  4. If it holds `"__bk__zlib_"`, probe the size: `zlib.decompressobj().decompress(<decoded member>, _DASH_JWT_PAYLOAD_MAX)`. If the object's `unconsumed_tail` is non-empty, return None.
  5. Only then `from bokeh.util.token import get_token_payload; return get_token_payload(jwt)`.
  6. Any exception gives None.

  Imports (`base64`, `json`, `zlib`) are local.
- **`_dash_request_token(handler)`:**
  - `req = getattr(handler, "request", None)`.
  - If `_DASH_TOKEN_ARG in (req.arguments or {})`, return `_dash_one_value(req.arguments[_DASH_TOKEN_ARG])`. This covers the page, `/autoload.js`, `/metadata` and `bokeh.client`'s `/ws?token=`.
  - Otherwise `payload = _dash_ws_payload(req.headers.get("Sec-WebSocket-Protocol", ""))` and return `_dash_one_value(((payload or {}).get("arguments") or {}).get(_DASH_TOKEN_ARG))`. This is the browser's websocket, carrying the page's own `?token=` in the JWT.
  - None on any missing piece.

**TR-13.4 Gate A, `_dash_token_auth(expected)`.**

```python
def _dash_token_auth(expected):
    """..."""
    from bokeh.server.auth_provider import AuthProvider
    from tornado.web import HTTPError
    if not _dash_token_valid(expected):
        raise ValueError("dash: the served app was given no valid key")

    async def _admit(handler):
        if _dash_token_matches(_dash_request_token(handler), expected):
            return "dash"
        raise HTTPError(403, reason=_DASH_TOKEN_REFUSAL)

    def _refuse(handler):
        raise HTTPError(403, reason=_DASH_TOKEN_REFUSAL)

    class _DashTokenAuth(AuthProvider):
        @property
        def get_user_async(self):
            return _admit

        @property
        def get_login_url(self):
            return _refuse

    return _DashTokenAuth()
```

`HTTPError` is raised in `prepare`, before any handler body, and before the websocket upgrade. The reason is constant: nothing from the request is reflected. `get_login_url` satisfies `AuthProvider._validate`. A falsy user also ends in 403.

**TR-13.5 Gate B, `_dash_session_token_ok(doc, expected)`.**
1. `ctx = getattr(doc, "session_context", None)`. None means True: an in-process build has no network path. Bokeh sets the context before `initialize_document` (bokeh/server/contexts.py:211-233).
2. `req = getattr(ctx, "request", None)`. None means False.
3. `args = getattr(req, "arguments", None)`. Not a dict means False.
4. Return `_dash_token_matches(_dash_one_value(args.get(_DASH_TOKEN_ARG)), expected)`. An `expected` of None or invalid fails closed.

**TR-13.6 Redaction.**
- **`_dash_redact_query(text, secret=None)`:** `out = _DASH_QUERY_RE.sub("?<query redacted>", text)`; if `secret`, `out = out.replace(secret, "<key>")`; return `out`. Pinned cases:
  - `'GET /?token=T&x=1 (127.0.0.1) 1.0ms'` → `'GET /?<query redacted> (127.0.0.1) 1.0ms'`;
  - `'is Python available on this PATH?'` is unchanged;
  - `'http://127.0.0.1:5/?token=T'` → `'http://127.0.0.1:5/?<query redacted>'`.
- **`_dash_redact_access_record(record)`:**
  - Rewrites `record.msg` (when a str) and each str element of a tuple `record.args`, or each str value of a dict `record.args`, through `_dash_redact_query`.
  - Any exception is ignored.
  - Always returns True (a filter returning a false value drops the record).
- **`_dash_install_access_log_redaction()`:**
  1. Sets `_dash_redact_access_record._dash_redacts_queries = True` on the CURRENT function object. In the app every `bokeh serve` session re-executes the module, and `getsource` does not copy a module-level attribute assignment.
  2. For each of `"tornado.access"`, `"tornado.general"` and `"tornado.application"`, adds the function as a filter unless some existing filter has that attribute.
  3. Returns the number added.

  This keeps filters from piling up across sessions (an exhaustion vector).

**TR-13.7 `_dash_tokenized_url(port, token, address=None, path="/")`.**
1. `port = _dash_port_value(port)`, which raises outside 1024-65535.
   - **`path`** (ratified 01oct2026, K-4: `bokeh serve`'s app path, such as `/app`): it must be a str starting with `/`, else ValueError; it is quoted with `urllib.parse.quote(path, safe="/")` (local import), so a space becomes `%20` and `?`/`#` cannot end it.
2. `if not _dash_token_valid(token): raise ValueError("dash: not a valid key")`.
3. The host:
   - `address` in `(None, "", "0.0.0.0", "127.0.0.1", "localhost")` → `127.0.0.1`;
   - `"::"` or `"::1"` → `[::1]` (TD-1);
   - otherwise `ipaddress.ip_address(address)`: IPv4 as written; IPv6 bracketed; an address holding `%` (zone) raises ValueError;
   - otherwise a hostname matching `^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$`;
   - otherwise ValueError.
4. Return `"http://%s:%d%s?%s=%s" % (host, port, <the quoted path>, _DASH_TOKEN_ARG, token)`; with the default path that is `http://<host>:<port>/?token=<key>`, as before.

**TR-13.8 Opening the link.**
- **`_dash_redirect_page(url)`.** `e = html.escape(url, quote=True)`, then return:

  ```html
  <!doctype html><html><head><meta charset="utf-8"><meta name="referrer" content="no-referrer"><meta http-equiv="refresh" content="0;url=E"><title>dash</title></head><body><p><a href="E">E</a></p></body></html>
  ```

  `E` is `e`.
- **`_dash_open_tokenized(url, platform=None, environ=None, opener=None, osa=None, out=None)`.** Imports `os`, `sys`, `tempfile`, `webbrowser` and `pathlib` locally.
  1. `platform` defaults to `sys.platform`, `environ` to `os.environ`, and `out` to `sys.stdout`.
  2. When `platform == "darwin"` and `not environ.get("BROWSER")` and (`osa` is given or `webbrowser` has `MacOSXOSAScript`): call `(osa or webbrowser.MacOSXOSAScript("default").open)(url)` and return None. The URL goes to osascript's stdin.
  3. Otherwise:
     - `d, p = _dash_private_page(_dash_redirect_page(url), "dash-open-", "open.html", out=out)` (TR-13.8a; 0600 in a fresh 0700 folder), inside `try:`;
     - **`except OSError as e:` the page could not be written (round 2, K-9).** In K-9's case no folder takes a file, so `tempfile.mkdtemp` fails for `open.html` too; an anti-hijack refusal or any other OSError of this write is treated the same. The opener then:
       - opens nothing: it never falls back to putting `url` in argv, to `webbrowser.open(url)`, to `opener(url)` or to `osa`;
       - prints exactly one line to `out`, flushed: `"dash: the browser was not opened: its page could not be written (" + type(e).__name__ + "); open the dashboard's link instead."`. The line names only the exception's type, never a path, the URL or the key. It is an inline literal, not a TR-13.1 constant, so the fourteen constants and the copy lists are unchanged;
       - returns None. It never raises over its page, so the server keeps serving (TR-13.10 item 7).
     - `(opener or webbrowser.open)(pathlib.Path(p).as_uri())`;
     - return `d`.

  Only a file path reaches any command line.

**TR-13.8a The self-made key (ratified 01oct2026; K-1..K-8).** Four module-level functions after `_dash_read_token_line`, each copied into the app (TR-13.11), each with local imports only and a docstring naming P0.12a, the ratification and the threat.
- **`_dash_private_page(text, prefix, name, out=None)`** returns `(folder, path)`. Imports `errno`, `os`, `shutil`, `stat`, `sys` and `tempfile` locally; `out` defaults to `sys.stdout`.
  1. `d = tempfile.mkdtemp(prefix=prefix)` (0700, a random name; `tempfile` follows `TMPDIR`).
  2. `p = os.path.join(d, name)`.
  3. `fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0), 0o600)`.
  4. `st = os.fstat(fd)`.
     - **Anti-hijack (kept; not a privacy check):** not `stat.S_ISREG`, or not owned by `os.geteuid()` where that exists, raises `OSError(errno.EPERM, "not a regular file of this account")`.
     - **Privacy (proceed and note; K-8, answer 2):** when `st.st_mode & 0o077`, call `os.fchmod(fd, 0o600)` where it exists (an OSError from this one call is ignored) and `fstat` again. Still loose: `loose = True`. Nothing is raised.
  5. Write `text` through `os.fdopen(fd, "w", encoding="utf-8")`.
  6. When `loose`: `print("dash: note: " + p + " holds the dashboard's link, but its disk keeps no file permissions, so other accounts of this machine may read it; set TMPDIR to a folder on a disk that keeps them.", file=out, flush=True)`. One line per call; it never holds `text`.
  7. Any exception from step 3 on: `shutil.rmtree(d, True)`, then re-raise. Return `(d, p)`.
- **`_dash_announce_key(url, out=None, hint=None)`** returns the folder, or None. It prints `url` only in K-9's case (round 2).
  - `out` defaults to `sys.stdout` (local `import sys`).
  - `d, p = _dash_private_page(_dash_redirect_page(url), "dash-link-", "link.html", out=out)`. On OSError, the link was not written at all (round 2, answer A, K-9). It then prints `_DASH_LINK_UNWRITTEN % type(e).__name__`, then `url` alone, then `hint` when given, each with `flush=True`, and returns None. The caller serves on. The round-1 line `dash: the dashboard's key was made but its link could not be written (…).` is struck.
  - Otherwise it prints `_DASH_LINK_SAID`, then `p` alone, then `hint` when given, each with `flush=True`, and returns `d`. A link file the disk would not keep private is announced like any other, after `_dash_private_page`'s one note.
- **`_dash_process_key()`** returns the `bokeh serve` process holder, a `types.ModuleType` with `.key` (a valid key), `.linked` (a set of app paths) and `.warned` (bool). Imports `sys` and `types` locally.
  - `h = sys.modules.get(_DASH_KEY_HOLDER)`. If `h` is a module whose `key` is `_dash_token_valid` and whose `linked` is a set, return it.
  - Otherwise make a new holder with `key = _dash_new_token()`, `linked = set()` and `warned = False`, store it at `sys.modules[_DASH_KEY_HOLDER]` (replacing anything malformed), and return it.
- **`_dash_bokeh_serve_key(doc, out=None)`** returns the key Gate B uses when neither the global nor the environment gives one, or None. It never raises. Imports `atexit`, `os` and `shutil` locally.
  1. `ctx = getattr(doc, "session_context", None)`. None returns None: an in-process build makes no key (the Notes' exemption), and Gate B admits it anyway.
  2. `h = _dash_process_key()`.
  3. **A variable that is set but invalid fails closed (item 8).** If `os.environ.get(_DASH_TOKEN_ENV) is not None` (it is set, and `_dash_env_token()` already found it invalid), print, once per process (`h.warned`, then set it), `"dash: " + _DASH_TOKEN_ENV + " is set but is not 32 to 128 of A-Z a-z 0-9 _ -; its value is not shown, and every session is refused."` and return None. No link is written.
  4. In one `try`: `app_path = ctx.server_context.application_context.url` and `local = ctx.request.connection.stream.socket.getsockname()`. Any exception returns `h.key`: a websocket-made session has no stream (Evidence §6), so its key is made but its link waits.
  5. If `app_path in h.linked`, return `h.key`. Else add it to `h.linked` first, so a failure below is never retried per session (K-6).
  6. If `local` is not a tuple of at least two items whose second is an int (a `--unix-socket` path is a str), take step 7's ValueError path. Else `host = "127.0.0.1" if local[0] in ("127.0.0.1", "::1", "::ffff:127.0.0.1") else local[0]` and `port = local[1]`.
  7. `url = _dash_tokenized_url(port, h.key, host, path=app_path)`. On ValueError (a port under 1024, an address holding a zone), print `"dash: the dashboard's key was made but no link can name this server's address; set " + _DASH_TOKEN_ENV + " and restart to choose the key."` and return `h.key`.
  8. `d = _dash_announce_key(url, out=out, hint=_DASH_BS_ORIGIN_HINT % port)`. If `d`: `atexit.register(shutil.rmtree, d, True)`. A None `d` means K-9 printed the link once. The function still returns `h.key`: the server serves on, and step 5 already marked the path, so no later session prints again.
  9. Return `h.key`.

**TR-13.9 `_dash_read_token_line(fd, limit=None)`.**
- `limit` defaults to `_DASH_TOKEN_LINE_MAX`.
- Loop `b = os.read(fd, 1)`:
  - EOF before a newline → None;
  - `b"\n"` → stop;
  - otherwise append, and more than `limit` bytes → None.
- Decode as ASCII (failure → None) and strip one trailing `\r`.
- It never reads past the newline, so S08's watch sees the rest of the pipe.

**TR-13.10 The emitted app (`ServerAppBuilder._generate_app_source`).**
1. **The module globals.** After `"_TRUST_FORWARDED_FOR = False",` (29695) add a comment and `"_DASH_SERVE_TOKEN = None",` and `"_DASH_LINK_DIR = None",`. The comment: the key `_dash_server_app` installed, which `make_document` reads, else the environment's, else (under `bokeh serve`) the process's own (K-4); and the folder of the link file the app wrote for a key it made (K-2).
2. **The flag.** In `_dash_arg_parser` (29787-29824) add `p.add_argument('--token-stdin', action='store_true', dest='token_stdin', help='Read the dashboard key as one line on standard input instead of making one.  dash serve passes this; it never puts the key on a command line.')`.
3. **The resolver.** After `_dash_apply_limits` emit the app-only `_dash_resolve_token(args, fd=None, environ=None)`:
   - `environ` defaults to `os.environ`;
   - `env = environ.pop(_DASH_TOKEN_ENV, None)`, always, so no child inherits it.
   - **With `args.token_stdin`:**
     - `fd` defaults to `sys.stdin.fileno()` (`import sys` locally); `sys.stdin` None or `fileno()` raising gives `ValueError('dash: --token-stdin was given but there is no standard input to read the key from')`;
     - `tok = _dash_read_token_line(fd)`;
     - not valid gives `ValueError('dash: the key on standard input is not 32 to 128 of A-Z a-z 0-9 _ -')`;
     - return `tok`.
   - **With `env` not None:** not valid gives `ValueError('dash: ' + _DASH_TOKEN_ENV + ' is set but is not 32 to 128 of A-Z a-z 0-9 _ -; its value is not shown')`. Return `env`.
   - **Otherwise:** return None. The resolver makes no key (ratified 01oct2026, K-2): `_dash_server_app` makes it, installs it and announces it.
4. **Gate B in `make_document`.** After `_dash_reset_notes()` (30009) and before the rate-limit block (30010), emit:

   ```python
   "    # ---- The dashboard's key (WP-29 P0.12a) ----",
   "    # Before the limiter, so a client without the key spends no",
   "    # session budget, and before the data is decoded.  With no key",
   "    # installed and none in the environment (bokeh serve), the",
   "    # process makes its own (ratified 01oct2026): never no key.",
   "    if not _dash_session_token_ok(doc, _DASH_SERVE_TOKEN or _dash_env_token() or _dash_bokeh_serve_key(doc)):",
   "        doc.add_root(Div(text=_DASH_TOKEN_REFUSED_HTML))",
   "        return",
   ```

   `or` short-circuits, so `_dash_bokeh_serve_key` runs only when neither the global nor a valid variable gives a key: never under `python app.py` (the global is set before the server starts).
5. **Gate A in `_dash_server_app`.** Its signature becomes `(port=None, address=None, origins=None, token=None)`, and its first lines (after `_p = int(port or _port)`):

   ```python
   "    global _DASH_SERVE_TOKEN, _DASH_LINK_DIR",
   "    if token is not None and not _dash_token_valid(token):",
   "        raise ValueError('dash: the key given to _dash_server_app is not 32 to 128 of A-Z a-z 0-9 _ -')",
   "    _dash_made = not (token or _DASH_SERVE_TOKEN or _dash_env_token())",
   "    _DASH_SERVE_TOKEN = token or _DASH_SERVE_TOKEN or _dash_env_token() or _dash_new_token()",
   ```

   - **The Server call** gains `auth_provider=_dash_token_auth(_DASH_SERVE_TOKEN),`, and its result is bound to `_dash_srv` instead of being returned at once. No path builds a Server without it.
   - **The announcement (K-2).** After the Server call:

     ```python
     "    if _dash_made:",
     "        try:",
     "            _dash_link_url = _dash_tokenized_url(_p, _DASH_SERVE_TOKEN, address)",
     "        except ValueError:",
     "            _dash_srv.stop()",
     "            raise RuntimeError('dash: the dashboard\\'s key was made but no link can name the address ' + repr(address) + '; set DASH_SERVE_TOKEN or pass --token-stdin to choose the key')",
     "        _DASH_LINK_DIR = _dash_announce_key(_dash_link_url)",
     "    return _dash_srv",
     ```

   - **The one remaining stop.** A ValueError from `_dash_tokenized_url` (an `--address` with a zone, or not a host name) runs `_dash_srv.stop()`, then raises a RuntimeError. The error names the address and the remedy (`DASH_SERVE_TOKEN`), never the key. No link can be formed, so there is nothing to print.
   - **A link that cannot be written** is printed once by `_dash_announce_key`, and the Server is returned and served (K-9). Round 2 struck round 1's stop-and-raise on `not _DASH_LINK_DIR`.
   - **The docstring says:**
     - with no key given, installed or in the environment, it makes one, installs it for both gates and announces its link file (ratified 01oct2026);
     - when no file can be written, it prints the link once after a warning and serves on (round 2, K-9);
     - the global is the one Gate B reads (A5).
6. **Module-level filter.** Before the `if __name__ != '__main__':` / `make_document(curdoc())` lines (31594-31595) emit `"_dash_install_access_log_redaction()"`. It is idempotent (TR-13.6), and it is the only hook `bokeh serve` gives.
7. **`__main__`** (on S08's text).
   - **Resolve the key.** After `_dash_apply_limits(_a)` and the port check:

     ```python
     "    _dash_install_access_log_redaction()",
     "    try:",
     "        _DASH_SERVE_TOKEN = _dash_resolve_token(_a)",
     "    except ValueError as _e:",
     "        _p.error(str(_e))",
     ```

   - **Reword the `*` warning** to `'dash: WARNING -- it holds *, so the websocket origin check admits every web site; only the dashboard's key, in its link, still keeps other pages out.  Unset BOKEH_ALLOW_WS_ORIGIN to admit only this app\\'s list.'`.
   - **Pass the key.** S08's `_server = _dash_server_app(...)` line becomes:

     ```python
     "    try:",
     "        _server = _dash_server_app(port=_port, address=_a.address, origins=_a.origins, token=_DASH_SERVE_TOKEN)",
     "    except RuntimeError as _e:",
     "        _p.error(str(_e))",
     ```

     With no key resolved, `_dash_server_app` makes one, sets `_DASH_SERVE_TOKEN` and `_DASH_LINK_DIR`, and prints the link file's path before `start()` (K-2). A link it cannot write at all is printed once after K-9's warning, and the app runs (round 2). An address no link can name ends the app with exit status 2. A link the disk will not keep at 0600 is written with one note, and the app runs (K-8). S08's `_dash_watch_parent` call follows unchanged (Q-1).
   - **Open the browser.** After `_server.start()`, replace the `add_callback(_server.show, '/')` block:

     ```python
     "    import shutil as _shutil",
     "    _dash_url = _dash_tokenized_url(_port, _DASH_SERVE_TOKEN, _a.address)",
     "    _dash_base = _dash_url.split('?', 1)[0]",
     "    _dash_open_dir = None",
     "    if _a.show:",
     "        _dash_open_dir = _dash_open_tokenized(_dash_url)",
     "        if _dash_open_dir:",
     "            _server.io_loop.call_later(_DASH_REDIRECT_TTL_S, _shutil.rmtree, _dash_open_dir, True)",
     ```

     **An opener that cannot write its page (round 2, K-9).** This call runs after `_server.start()`. In K-9's case `open.html` cannot be written either (TR-13.8 step 3), except on darwin with `BROWSER` unset, where osascript writes no file. `_dash_open_tokenized` catches that OSError, prints its one key-free line, opens nothing and returns None, so `if _dash_open_dir:` schedules nothing and the server keeps serving. Unguarded, the OSError would end `__main__` after `start()` and stop the server K-9 had just kept: `dash serve` without `nobrowser` (on Linux, on Windows, or on macOS with `BROWSER` set) would print K-9's link and then fail r(198), and `python app.py --show` would print it and exit. Pinned by `test_an_opener_that_cannot_write_its_page_opens_nothing_and_returns_none` and the live `test_a_keyless_show_start_whose_link_cannot_be_written_prints_it_once_and_serves`.
   - **The banner** replaces the two localhost prints. S08's `flush=True` and the `Bokeh Server running at` prefix are kept:

     ```python
     "    print(f'Bokeh Server running at {_dash_base} -- the dashboard opens only through the link that holds its key.', flush=True)",
     "    print(f'Health check:  {_dash_base}health', flush=True)",
     ```

     The app never prints `_dash_url` (ratified 01oct2026, K-3): a key it made has its link in the file whose path `_dash_server_app` printed. K-9's one print comes from `_dash_announce_key`, inside `_dash_server_app`, of the URL that call built.
   - **Cleanup.** In S08's `finally:`, after `_server.stop()`: `if _dash_open_dir: _shutil.rmtree(_dash_open_dir, True)` and `if _DASH_LINK_DIR: _shutil.rmtree(_DASH_LINK_DIR, True)`.

**TR-13.11 Copy lists (`ServerAppBuilder._glyph_layer_lines`).**
- **Constants tuple:** after `"_DASH_CSP_SERVED", "_DASH_SECURITY_HEADERS",` / `"_DASH_VIEWPORT_META",` (28429-28430), add the fourteen TR-13.1 names with a comment naming P0.12a: the ten of the design, plus `"_DASH_KEY_HOLDER", "_DASH_LINK_SAID", "_DASH_BS_ORIGIN_HINT"` (ratified 01oct2026) and `"_DASH_LINK_UNWRITTEN"` (round 2).
- **Functions tuple:**
  - after `"_dash_server_transforms",` (28725): `"_dash_new_token", "_dash_token_valid", "_dash_token_matches", "_dash_tokenized_url",`;
  - after `"_dash_watch_parent"` (S08's last entry; keep it last-but-these): `"_dash_one_value", "_dash_env_token", "_dash_ws_payload", "_dash_request_token", "_dash_token_auth", "_dash_session_token_ok", "_dash_redact_query", "_dash_redact_access_record", "_dash_install_access_log_redaction", "_dash_redirect_page", "_dash_open_tokenized", "_dash_read_token_line", "_dash_private_page", "_dash_announce_key", "_dash_process_key", "_dash_bokeh_serve_key"` (sixteen; the last four are TR-13.8a's);
  - each group with its comment.
- `_dash_write_link` is launcher-only and is NOT copied. Neither is S08's `_dash_child_stdin` (nor its other launcher-only round-2 names, section-08 TR-08.8a), which the launcher calls to write the key line (TR-13.12 item 4); it is never copied into the app.

**TR-13.12 The launcher (`_dash_launch_app`, on S08's text).**
1. **The signature** gains `link_dir=None`.
2. **The key.** After `port = _dash_port_value(port)`: `token = _dash_new_token()`.
3. **The command.** `_cmd` always gains `"--token-stdin"`, next to S08's `"--parent-watch"`. No argv element holds the key. Under round 2's answer B, `_cmd` is S08's open-file launch command, and `--token-stdin` goes among the app's own arguments, after the app path (L-4).
4. **Handing the key over.** Inside S08's Popen-to-final-wait `try:` (S08 A4), right after S08's hand-over of the verified app text (L-1, L-2), on the same pipe, through S08's binary writer `_dash_child_stdin(proc)` (L-3):

   ```python
   try:
       _raw = _dash_child_stdin(proc)
       _raw.write((token + "\n").encode("ascii"))
       _raw.flush()
   except (AttributeError, OSError, ValueError):
       raise RuntimeError("no server started on port %d: the dashboard's "
                          "key could not be handed to the app" % port)
   ```

   Popen stays `text=True` (S08's pumps read text); every write to the child's stdin goes through S08's `_dash_child_stdin(proc)` (TR-08.8a), its binary `buffer`, or a fake's stdin as it is.

   - S08's `finally` stops the child.
   - The pipe is NOT closed (TD-4).
   - A failure while S08 hands over the app text is S08's error. The key is never written before that text.
5. **429 counts as answering.** In the `/health` probe's `try:`, add `except urllib.error.HTTPError as _e:` before the generic `except Exception:`. Code 429 takes the same "answering" path as a 200; any other code falls through to the existing not-answering handling. S08's `poll()` stays outside this try (S08 A1). `import urllib.error` goes beside `urllib.request`.
6. **When the server first answers:**
   - **Where the link goes:** `_link_path, _link_tmp = _dash_write_link(link_dir, _dash_tokenized_url(port, token))` (item 9).
   - **On failure** (round 2, answer A, K-9): `_dash_write_link` raised `_DashUnsafePath` or OSError, because the run folder and the fresh private folder both refused or failed. A privacy shortfall is never this case: K-8 writes the file and notes it.
     - Nothing is stopped.
     - Print three lines, each flushed: line 1 below, then `_DASH_LINK_UNWRITTEN % type(exc).__name__`, then `_dash_tokenized_url(port, token)` alone.
     - Set `_link_path = _link_tmp = None`, and go on serving exactly as after a written link.
     - The block runs once per launch (the first answer), so the link is printed once.
     - Round 1's `raise RuntimeError("the server on port %d was stopped: its link was not written (%s)" …)` is struck, and so is its test, `test_a_link_that_cannot_be_written_stops_the_server`. The replacement test is `test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served`.
   - **Otherwise print three lines:**
     1. `"dash: the server answers at http://127.0.0.1:%d/ (health check http://127.0.0.1:%d/health)" + <S08's stop hint>`;
     2. `_DASH_LINK_SAID` (TR-13.1; the same line the app prints for a key it made, K-3);
     3. `_link_path` alone (A4).
7. **Redaction.** Every forwarded stdout line becomes `_dash_redact_query(_clean(line), token)`. The text S08's banner detection reads is the unredacted line, and the prefix is unaffected. The stderr tail becomes `_dash_redact_query(_clean("".join(_err_dq)), token)`.
8. **`finally:`** `_dash_erase_quietly(_link_path)` when written, and `shutil.rmtree(_link_tmp, ignore_errors=True)` when `_link_tmp` is a folder.
9. **`_dash_write_link(link_dir, url)`** (launcher-only, beside `_dash_launch_app`) returns `(path, made_folder_or_None)`. `page = _dash_redirect_page(url)`.
   - **No run folder** (`link_dir` None, a command-line `--launch`): return `_dash_private_page(page, "dash-link-", "link.html")` reversed to `(path, folder)`.
   - **The run folder** (Q-2): `path = os.path.join(link_dir, "link.html")`; `_dash_private_write(path, page, exclusive=True)` (the M4a anti-hijack guards: no link, FIFO or other account's file at the name). If that write raises `_DashUnsafePath` or OSError (round 2), fall back at once to the no-run-folder branch. Nothing is erased, because dash wrote no file at the name.
   - **The privacy check (K-8, answer 2).** `st = os.lstat(path)`. If it is a regular file, owned by `os.geteuid()` (where that exists), with `st.st_mode & 0o077 == 0`, return `(path, None)`. Otherwise `_dash_erase_quietly(path)` and fall back to the no-run-folder branch, so the key moves to a fresh 0700 folder where the disk allows it. When that folder's disk will not keep 0600 either, `_dash_private_page` keeps the file there, prints its one `dash: note:` naming it, and `_dash_write_link` returns that path and folder (proceed and note; nothing is raised). No location is refused for a privacy condition. When the no-run-folder branch raises too, `_dash_write_link` prints nothing and raises that exception, and the launcher prints the link once (item 6, K-9).
10. **Renderer `__main__`** (the launch block, :32196-32205 at 7421d3d): the `_dash_launch_app(...)` call gains `link_dir=_dash_private_run_of(args.output)`. The `--launch` help (32145-32153) gains: "The app needs a key made for each launch; the launcher writes the link that holds it to a file only you can read and prints the file's path; if no file can be written, it prints a warning and the link itself, once."

**TR-13.13 dash.ado.** In `_dash_build`'s server branch (7448-7459), after the `To launch:` line:

```stata
display as text `"  Access:    the app makes a new key for each launch unless DASH_SERVE_TOKEN gives one, writes the link that holds it to a file only you can read, and prints that file's path; only that link opens the dashboard"'
```

(Ratified 01oct2026, K-3: the app no longer prints the link itself. TOK-01's needle `a new key for each launch` is unchanged.)

Nothing else changes in dash.ado. `_dash_serve`'s announcement is S08's (LC-04 pins it), and the launcher's lines carry the link. No program is added, and no `python:` line.

**TR-13.14 Help (dash.sthlp, Server Mode).** Locate by text; S08 has shifted the lines.
1. **Table.** After `{col 5}Health endpoint{col 38}n/a{col 59}{cmd:/health}` add `{col 5}Who can open it{col 38}who has the file{col 59}who has its link`.
2. **Blocking behavior.** Replace the sentence `{cmd:dash serve} prints the server's address once it answers {cmd:/health}.` with:

   > {cmd:dash serve} makes a new key for each launch. Once the server answers {cmd:/health} it prints the server's address and the path of a file, readable only by you, holding the dashboard's link -- {cmd:http://127.0.0.1:}{it:port}{cmd:/?token=}{it:key} -- and, unless {cmd:nobrowser}, {cmd:$dash_nobrowser} or a {cmd:nodraw} graph says not to, opens that link in your browser. The key itself is never printed, so no Stata log holds it, with one exception: if no such file can be written anywhere, {cmd:dash serve} prints a warning line and then the link itself, once, and keeps serving. The key is then in Results and in any log you have open, so treat that log like the link. Open the file, or copy the link from it, to reach the dashboard again while the server runs; it is removed when the server stops. On a disk that keeps no file permissions the file is written anyway, and a line beginning {cmd:dash: note:} names it.

3. **Running the generated .py.** After `...usable from a script or a batch job.` add:

   > The app never runs without a key, and only a link holding it opens the dashboard: {cmd:http://127.0.0.1:}{it:N}{cmd:/?token=}{it:key}. Unless you choose the key, each start makes a new one, writes that link to a file named {cmd:link.html}, readable only by you, in a new folder only you can open, and prints the file's path on a line of its own before the server starts; the key itself is never printed. Open the file, or copy the link from it; the folder is removed when the app stops. On a disk that keeps no file permissions the file is written anyway, and a line beginning {cmd:dash: note:} names it; set {cmd:TMPDIR} to a folder on a disk that keeps them. If no such file can be written at all, the app prints a warning line and then the link itself, once, and keeps serving; the key is then in that output and in any log of it. To choose the key, set the environment variable {cmd:DASH_SERVE_TOKEN} to 32 to 128 of the characters A-Z, a-z, 0-9, _ and -, or pass {cmd:--token-stdin} and write it as one line on standard input; the app then writes no link file. A value of any other form stops the app at once (exit status 2), naming the variable but not the value.

4. **bokeh serve.** Append to the paragraph:

   > Under {cmd:bokeh serve} the app still never runs without a key. Start it as {cmd:bokeh serve app.py --allow-websocket-origin 127.0.0.1:5006}: Bokeh otherwise admits only {cmd:localhost}, and the link's page stays blank. With {cmd:DASH_SERVE_TOKEN} set as above, open {cmd:http://127.0.0.1:5006/app?token=}{it:key}. Without it, the app makes one key for the server when the first session is asked for, and at the first page request writes {cmd:http://127.0.0.1:}{it:port}{cmd:/app?token=}{it:key} to a {cmd:link.html} only you can read and prints that file's path (if no such file can be written, it prints a warning line and then the link itself, once for each app); the folder is removed when {cmd:bokeh serve} stops. Every session without the key gets a page saying where the link is. {cmd:bokeh serve --show} opens the address without the key, so it shows that page and makes the link: open the file it names. The link names no {cmd:--prefix}, and a session asked for only through {cmd:bokeh.client} leaves the link to the first page request.

5. **Security.** Replace `so by default only this machine can reach it.` with:

   > so by default only programs on this machine can reach it, and of those only one holding the dashboard's link opens it: every page, session, {cmd:/autoload.js} and {cmd:/metadata} request without the link's key is refused (403) before any data is read. The key is new at every launch, is compared in constant time, and travels only in the link's {cmd:?token=}; {cmd:/health} and BokehJS's own files under {cmd:/static} stay open and hold no data.

   Keep the `--address` sentence and S08's last sentence.
6. **Replace `There is no password.`** with:

   > The dashboard's key is the access control: a client without it gets nothing, whatever {cmd:Origin} it sends.

7. **The `BOKEH_ALLOW_WS_ORIGIN` paragraph.** Replace `{cmd:*}, which lets any website open a session with your dashboard.` with:

   > {cmd:*}: the origin check then admits every website, and only the dashboard's key keeps another site's page out.

8. **Replace the "single-user tool" paragraph** with:

   > The generated app embeds every observation of the variables the dashboard uses, and anyone who holds its link can read them. The key is in the link, so it is wherever the link is: the browser's address bar and history, the file {cmd:dash serve}, {cmd:python app.py} or {cmd:bokeh serve} names, the output and any log where one of them printed it because no file could be written, and anything you paste it into. Treat the link as a password while the server runs; a new launch makes a new key, and the old link stops working. The key travels in plain HTTP: on loopback that stays on this machine, but with {cmd:--address} beyond loopback anyone who can watch the network can read it, so reach such a server through an SSH tunnel or a reverse proxy that adds TLS. The browser is handed the link without it appearing on any command line: on macOS through {cmd:osascript}'s standard input, elsewhere (or when {cmd:BROWSER} is set) through a page only you can read that forwards to it. Linux and Windows have not been tested.

9. **`{dlgtab:dash serve}`.** Append to the first paragraph's end:

   > The dashboard opens only through a link holding a key made for each launch; see {help dash##server_mode:Server Mode}.

**TR-13.15 Test helpers (the key in tests).**
- **`test/serve_token_probe.py`** defines:
  - `TEST_TOKEN = "dashTestKey_0123456789abcdefghijklmnopqrstuvwxyz"` (48 characters);
  - `token_args(token=TEST_TOKEN)` → `{"token": [token.encode("ascii")]}`;
  - `class FakeStdin` (round 2, L-3). It has:
    - `write(b)`, which appends each write, as given, to `.writes` (bytes on round 2's binary pipe);
    - `key_line()`, which returns the last write, decoded from ASCII without its one trailing `\n`, when that write is bytes ending in exactly one newline, and None otherwise;
    - `flush()`, and `close()` setting `.closed = True`;
    - a constructor flag `broken=False` that makes `write` raise `BrokenPipeError`;
  - `main(argv)`, TOK-02's probe (TR-13.16);
  - (ratified 01oct2026) `LINK_RE = re.compile(r"http://(127\.0\.0\.1|\[::1\]):(\d+)(/[^?\"'<>\s]*)\?token=([A-Za-z0-9_-]{43})")`;
  - `LINK_SAID`, a literal copy of `dash_render._DASH_LINK_SAID` (kept equal by `test_the_probe_knows_the_announcement`);
  - `link_path_in(text)`: the stripped line that follows the first line equal to `LINK_SAID`, or None;
  - `read_link(path)`: `(mode, folder_mode, host, port, app_path, key)` from the file, modes as `oct(stat.S_IMODE(...))[-3:]`;
  - `drop_holder()`: `sys.modules.pop("_dash_serve_key", None)`, for fixtures around in-process `bokeh serve` tests.

  It imports nothing from pytest, so a script, Stata's Python and every test file can import it.
- **The key-aware helpers:**
  - `test_server_serves._Launched(app, extra_args=(), token=TEST_TOKEN)` and `_Served(app, extra_args=(), token=TEST_TOKEN)` start the child with `env = dict(os.environ)`, then `env["DASH_SERVE_TOKEN"] = token`. With `token=None` they `env.pop("DASH_SERVE_TOKEN", None)` instead, and the app makes its own key (ratified 01oct2026); `self.token` is then None until a test reads the key with `serve_token_probe.link_path_in` and `read_link` and sets it. Each keeps `self.token`. `url(path, token=True)` appends `?token=` (or `&token=` when `path` holds `?`) when `self.token` is set and `token` is True.
  - (ratified 01oct2026) `_Served` also gains `allow_127=False`, which adds `"--allow-websocket-origin", f"127.0.0.1:{self.port}"` (the port is chosen in `__init__`, so a caller cannot pass it in `extra_args`), and `ready_path="/app"`, the path its readiness loop GETs. Its readiness GET of `/app` makes a session, so with `token=None` it is the first page request that makes the app write its link (K-4); `test_a_websocket_first_session_leaves_the_link_to_the_first_page` passes `ready_path="/static/js/bokeh.min.js"`, which makes no session.
  - `_pull(srv)` passes `arguments={"token": srv.token}` when `srv.token`.
  - `test_adversarial_matrix._Req(remote_ip="10.0.0.1", arguments=None, **headers)` sets `self.arguments = token_args() if arguments is None else arguments`. `_load_app` sets `ns["_DASH_SERVE_TOKEN"] = TEST_TOKEN` after the exec.
  - `_LiveApp(app_path, env=None)` adds `DASH_SERVE_TOKEN=TEST_TOKEN` unless `env` maps it to None, which removes it. `session(origin, jwt=None)` fetches `/?token=TEST_TOKEN` for the page JWT unless `jwt` is given.
  - `test_server_rate_limit._Req` follows the same pattern, and the fixtures that exec the app set `_DASH_SERVE_TOKEN`.
  - `test_serve_lifecycle._url(port, path, token=None)` appends the key when given; `_token_in(rundir)` reads it from `rundir/link.html`.

**TR-13.16 Certification (`test/test_serve_launch.cscript`, TOK-01..TOK-04).**
- **Placement.** One contiguous run before the `// SRV-19` banner and after S08's LC-04 (R1), with its own banner comment. It needs the real `_dash_find_render`, which SRV-19 replaces for good.
- **Names.** Paths are built from `c(tmpdir)` and the Python pid (`Macro.setLocal("tokpid", str(os.getpid()))`). There is no `tempfile`/`tempname` (the SPU-01 note) and no `` `c(pid)' `` (S08 A1).
- **TOK-01: `dash build, server` writes an app that makes its own key.** `dash build, saving("<tmpdir>dash_tok_<pid>_01.py") server replace` runs inside a text log. Then:
  - `cert_log_has` finds `a new key for each launch`;
  - `cert_file_has` finds `--token-stdin`, `auth_provider=_dash_token_auth(` and `_DASH_SERVE_TOKEN = None`.

  Each `r(found)` is copied on the next line.
- **TOK-02: a real `dash serve` refuses without the key and serves with it.**
  - **Before the serve,** a multi-line `python:` block:
    - takes a free 127.0.0.1 port into local `tokport`;
    - reads `toktmp` (`c(tmpdir)`) and `tokres` (the result path) with `Macro.getLocal`;
    - sets `_tok_probe = os.path.abspath("serve_token_probe.py")`, since the driver `cd`s into `test/`;
    - starts a daemon thread `_tok_run` (TD-3). The thread calls no `sfi` function.
  - **The thread:**
    1. waits up to 60 s for `/health` 200;
    2. waits up to 10 s for `glob(os.path.join(tmp, "dash-%d" % os.getuid(), "run-%d-*" % os.getpid(), "link.html"))`.
    3. **When the link file is missing** (the base), it records the status of an unkeyed `GET /` itself as `root_without_key=<code>` and skips steps 4-6.
    4. records `link_mode` (`oct(S_IMODE)[-3:]`) and `link_dir_mode`;
    5. keeps the key, read with `re.search(r"\?token=([A-Za-z0-9_-]{43})", text)`, only in `_tok_state["token"]`;
    6. runs `subprocess.run([sys.executable, _tok_probe, str(port), link_path, res], timeout=120, capture_output=True, text=True)`, which passes the file's path, never the key. It appends `probe_stderr=<last 300 characters of stderr, newlines removed>` when stderr is not empty.
    7. appends `link=found|missing`, `link_mode=...`, `link_dir_mode=...` and `stopped=1` to `res`. The probe writes `res` first, and the thread appends only after `subprocess.run` returns.
    8. SIGTERMs every pid from `lsof -ti tcp:<port> -sTCP:LISTEN`, whatever happened before.
  - **The serve.** `capture noisily dash serve, port(`tokport') timeout(1) nobrowser` runs inside both a text log and an SMCL log, timed with timer 93. Then `python: _tok_thread.join(60)`.
  - **Asserts:**
    - `rc == 0` and elapsed < 60;
    - `cert_file_has` on `res` for each of `link=found`, `link_port=ok`, `health=200`, `root_without_key=403`, `near_miss=403`, `page_with_key=200`, `pull_without_key=refused`, `pull_with_key_rows=74`, `link_mode=600`, `link_dir_mode=700`, `stopped=1`.
  - **`serve_token_probe.main`:**
    - reads the key from the link file;
    - checks the link's host and port;
    - GETs `/health`, `/`, `/?token=<the key with its last character changed>` and `/?token=<key>`;
    - runs `bokeh.client.pull_session(url)` (`pull_without_key=refused` on any exception, `served` otherwise), then `pull_session(url, arguments={"token": key})`, counting the `mpg` rows (`pull_with_key_rows=<n>`, or `pull_with_key_error=<exception type name>`);
    - writes `key=value` lines and never the key.
- **TOK-03: no log holds the key.** A `python:` block reads both logs and joins `\n> ` continuations. It sets `tok03bad` to the number of logs holding `_tok_state["token"]` or matching `\?token=[A-Za-z0-9_-]{32,}`, `tok03len` to `len(token)` (43), and `tok03gone` to 1 when the link file no longer exists. `cert_log_has` on the text log finds `opens only through its link` and `link.html`. Asserts: `tok03bad == 0`, `tok03len == 43`, `tok03gone == 1`, and both needles found.
- **TOK-04: the help names the key.** `cert_file_has "../dash.sthlp"` needles `DASH_SERVE_TOKEN` (found), `?token=` (found), `--token-stdin` (found), `only this machine can reach it` (0) and `There is no password` (0).
- **Each case** ends `display "TOK-0n PASS: <what>"`. Logs and results are erased after use. The header comment's "Tests:" line gains `TOK-01..TOK-04 (WP-29 P0.12a)`.

**TR-13.17 Maps.**
- **`test/function_test_map.py`,** in alphabetical place, each naming its test from "TDD test stubs":
  - `_dash_env_token`, `_dash_install_access_log_redaction`, `_dash_new_token`, `_dash_one_value`;
  - `_dash_open_tokenized`, `_dash_read_token_line`, `_dash_redact_access_record`, `_dash_redact_query`, `_dash_redirect_page`;
  - `_dash_request_token`, `_dash_session_token_ok`;
  - `_dash_token_auth`, `_dash_token_auth.<locals>._admit`, `_dash_token_auth.<locals>._refuse`, `_dash_token_auth.<locals>._DashTokenAuth.get_user_async`, `_dash_token_auth.<locals>._DashTokenAuth.get_login_url`;
  - `_dash_token_matches`, `_dash_token_valid`, `_dash_tokenized_url`, `_dash_write_link`, `_dash_ws_payload`;
  - (ratified 01oct2026) `_dash_announce_key`, `_dash_bokeh_serve_key`, `_dash_private_page`, `_dash_process_key`;
  - `app:_dash_resolve_token`.
- **`test/program_coverage_map.py`:** `"_dash_serve"` gains `"test_serve_launch.cscript:TOK-02"` and `"_dash_build"` gains `"test_serve_launch.cscript:TOK-01"`, each with an `# e2e:` comment.

**TR-13.18 Security summary (rule 1).** Each threat, and what closes it:

| Threat | What closes it |
|---|---|
| Another account reads the data over loopback | Gate A + Gate B, fail closed |
| The app runs with no key (a hand-run `python app.py` or `bokeh serve app.py`; ratified 01oct2026) | it makes its own 256-bit key before any session is admitted (K-2, K-4); `_dash_server_app` never builds a Server without `auth_provider`, and Gate B's key expression always yields a key or fails closed |
| A self-made key reaches the wrong reader | the key goes only into `link.html`, 0600 (fstat-checked, `O_EXCL\|O_NOFOLLOW`), in a fresh 0700 mkdtemp folder; only the path is printed; the folder is removed at stop (`finally`) or exit (`atexit`). On a disk that keeps no file permissions the file is written anyway with one `dash: note:` naming it (K-8, answer 2; a recorded residual) |
| A client steers where the self-made link points | the link's host and port come from the server side of the connection (`getsockname`), never from the `Host` header; the path from Bokeh's application context |
| A keyless client floods key or link creation | one key per process and one link per app path (the `bokeh serve` holder); Gate B before the limiter |
| A set but invalid `DASH_SERVE_TOKEN` under `bokeh serve` replaced by a self-made key | a set variable is never overridden: invalid means every session refused and one warning line, no key made (item 8) |
| The run folder is not private (S08 codes struck, answer 2) | `_dash_write_link` checks the written link file and falls back to a fresh 0700 mkdtemp folder; where that disk cannot hold 0600 either, the link is written there with one `dash: note:` naming it, never refused (K-8) |
| A link, FIFO, device or another account's file planted at the link's name | kept as anti-hijack, not privacy (M4a): `_dash_private_write(..., exclusive=True)` in the run folder and `_dash_private_page`'s `O_EXCL\|O_NOFOLLOW` open and regular-file and owner check; such a refusal in the run folder sends the link to a fresh private folder, and a refusal there too gives K-9's warned print (round 2). Nothing is stopped |
| Bypass with a doubled, overlong, homoglyph or NUL key | `_dash_token_valid` before any use; exactly one value |
| A forged JWT | its payload arguments must hold the key |
| Timing | `hmac.compare_digest` |
| The key in argv, `ps` or `/proc` | the stdin pipe; the file-path opener on Linux and under `$BROWSER` |
| The key in a log or Results | never printed; access-log and forwarded-output redaction. The one exception is K-9 (round 2, answer A): when no folder takes the link file, the link is printed once, after a warning line naming the exposure, to the starter's output. It is a recorded residual: under `dash serve` a batch log is 0644 (TD-2) |
| No folder takes the link file (round 2, answer A) | nothing is stopped. The warning line and the link are printed exactly once: per launch (the launcher's first-answer block), per process (`_DASH_SERVE_TOKEN` already set) or per app path (`holder.linked` marked first). No session prints it, and redaction is unchanged |
| The key line lost or misread on the shared pipe (round 2, answer B) | the key line follows S08's app text, which the child reads unbuffered to its exact length (L-2), written as bytes through S08's binary writer `_dash_child_stdin(proc)` while Popen stays `text=True` (L-3). Pinned by `test_the_token_goes_to_stdin_not_argv` and TOK-02 |
| The key at rest | 0600 link file in the 0700 run folder, unlinked at stop; the 0600 redirect file, removed after 60 s and at stop; a self-made key's 0600 `link.html` in its own 0700 folder, removed at stop or exit |
| IPv6 squat | 127.0.0.1 links |
| Cookie leak across ports | no cookie (RFC 6265 §8.5) |
| Referer | `Referrer-Policy: no-referrer` (unchanged) and the redirect page's `no-referrer` meta |
| A decompression bomb before auth | the 16,384-character and 262,144-byte bounds |
| Budget exhaustion | Gate B before the limiter; Gate A before `make_document` |
| Reflection | constant reason and page |
| DNS rebinding | 403 without the key |

## Boundaries

- **The saved page.** No change: it has no server and no session (CSP `connect-src 'none'`). No change to the parity corpus, `ALLOWED` or `_MUST_WARN`.
- **S08's code.** Do not change:
  - S08's private-file helpers, run folder, sweep, previews and the parent watch's own logic;
  - Break handling and the erase rule;
  - the `Bokeh Server running at` prefix;
  - the announcement in `_dash_serve`.

  Only the sites TR-13.10 and TR-13.12 name are edited.
- **Other origin and rate-limit code.** Do not change `_dash_harden_origin_check`, `_dash_strict_match_host`, the origin allow-list, `_RateLimiter`, `_HealthHandler`, `/health`'s openness, or `_DASH_SECURITY_HEADERS`.
- **No cookie, no `sign_sessions`, no `secret_key`, and no opt-out flag.**
- **No new Stata option, Mata function or program.** No `dash_parse.mata` edit.
- **No new cscript.** No runner or hygiene-pin edit (index A3, R1). No fixture (twoway has no server).
- **Tracking documents** (GAPS.md, GAPS2.md, ROADMAP.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, DROPIN-REMAINING.md, AGENTS.md) are S15's (index A5).
- **Other sections' help paragraphs** are not edited (R3). Only TR-13.14's sentences are.

## Stata truth

None to extract. twoway has no network surface, so the truth is "no listener and no credential": while `twoway scatter mpg weight` was drawn, `lsof -a -p 5906 -iTCP -sTCP:LISTEN` and `lsof -a -p 5906 -i` printed nothing (Evidence §1). No fixture, no `test_wp29_truth.cscript` block.

Stata is used to certify dash's own behaviour in TOK-01..TOK-04 (TR-13.16), through the driver:

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_serve_launch.cscript > <scratch>/run_test_serve_launch.do
dash_nobrowser=1 "$WT"/scripts/stata_slot.sh <scratch> <scratch>/run_test_serve_launch.do
```

Read `<scratch>/run_test_serve_launch.log`; never relaunch to check on it. `test_serve_launch.cscript` uses `assert`, so the first failing case stops the script. A SKIP (exit 222, no `c(python_exec)`) is not a pass.

## TDD test stubs

All in **`test/test_serve_token.py`** (new) unless noted. It imports:
- `dash_render as dr`;
- `serve_token_probe` (`TEST_TOKEN`, `token_args`, `FakeStdin`);
- `test_adversarial_matrix` (`_app_source`, `_load_app`, `_SessionDoc`, `_Req`, `_LiveApp`, `_launcher_said`, `_free_port`);
- `test_server_serves` (`_Served`, `_build_app`);
- `conftest.make_spec`.

Markers:
- **RED:** fails at the batch-2 base. Its failure text goes to `<scratch>/13-P0.12a-failure.txt`.
- **GUARD:** passes at the base and must stay green.
- **[serve]:** live process, `@pytest.mark.serve`.

### `TestTheTokenHelpers` (all RED: `AttributeError` at the base)

- `test_new_tokens_are_43_urlsafe_and_unique`: 1,000 draws, each fullmatching `[A-Za-z0-9_-]{43}`, all distinct, each `_dash_token_valid`.
- `test_invalid_shapes_are_refused`. Refused: `""`, 31 and 129 characters, `+`, `/`, `=`, NUL, a Cyrillic `а`, leading space, trailing newline, None, 123, `b"\xff" * 40`, and 10,000 characters (under 50 ms). Accepted: 32 characters, `"A-_9" * 10`, and `b"a" * 40`.
- `test_the_right_token_matches_and_a_near_miss_does_not`:
  - T matches T and `T.encode()`;
  - T with its last character changed does not;
  - None and `""` do not;
  - an invalid `expected` never matches, even itself.
- `test_matching_is_constant_time`: the AST of `inspect.getsource(dr._dash_token_matches)` calls `compare_digest` and holds no `ast.Eq` or `ast.NotEq`.
- `test_one_value_takes_exactly_one`: `[x]` → x; `[x, y]` → None; `[]` → None; `"x"` → `"x"`.
- `test_the_environment_token_is_read_only_when_valid`: valid → the value; `"abc"` → None; missing → None.
- `test_the_request_token_is_read_from_query_or_ws_jwt`. Fake handlers (`types.SimpleNamespace(request=types.SimpleNamespace(arguments=..., headers=...))`):
  - a query `[b"T"]` → `b"T"`;
  - a doubled query → None;
  - the header `"bokeh, " + generate_jwt_token("A" * 44, extra_payload={"arguments": {"token": [T]}})` → T;
  - `"bokeh, x.y"` → None;
  - `"evil, <jwt>"` → None;
  - a 20,000-character header → None.
- `test_a_jwt_that_inflates_is_refused_quickly`: a hand-built JWT whose `__bk__zlib_` member inflates to 10 MB. `dr._dash_ws_payload("bokeh, " + jwt)` is None in under 0.5 s.
- `test_the_provider_refuses_with_403_and_admits_with_the_token`:
  - `prov = dr._dash_token_auth(T)` is an `AuthProvider`;
  - `asyncio.run(prov.get_user_async(ok)) == "dash"`;
  - a wrong key raises `tornado.web.HTTPError` with `status_code == 403` and `reason == dr._DASH_TOKEN_REFUSAL`;
  - `dr._dash_token_auth("short")` raises ValueError.
- `test_the_login_url_also_refuses`: `prov.get_login_url(h)` raises 403.
- `test_the_redaction_strips_every_query`: TR-13.6's three cases, plus `secret` replacement.
- `test_the_access_filter_rewrites_the_record`: a `logging.LogRecord("tornado.access", WARNING, __file__, 1, "%d %s %.2fms", (403, "GET /?token=" + T + " (127.0.0.1)", 1.0), None)`. The filter returns True, and `getMessage()` lacks T and holds `?<query redacted>`.
- `test_the_filter_installs_once`: install twice, then once from a second `_load_app` namespace (whose module-level line installs it too). Exactly one filter with `_dash_redacts_queries` is on `tornado.access`. A fixture removes every filter with that attribute from the three loggers before and after the test.
- `test_the_tokenized_url` (A1, A2, TD-1):
  - `(5006, T)` → `http://127.0.0.1:5006/?token=T`;
  - None, `""`, `0.0.0.0`, `localhost` and `127.0.0.1` → `127.0.0.1`;
  - `::` and `::1` → `[::1]`;
  - `192.168.1.5` stays as is;
  - `fe80::1` → `[fe80::1]`;
  - `fe80::1%en0`, `a b`, an invalid key, and ports 80 and 70000 raise;
  - (ratified 01oct2026) `path="/app"` → `http://127.0.0.1:5006/app?token=T`; `path="/my app"` → `.../my%20app?token=T`; `path="/a?x"` → `.../a%3Fx?token=T`; `path="app"` and `path=None` raise.
- `test_the_redirect_page_escapes_and_sends_no_referrer`:
  - the page has the referrer meta and the refresh meta, and its URL is escaped;
  - for a URL holding `"><script>` there is no raw `<script` and there is `&quot;&gt;&lt;script&gt;`.
- `test_opening_never_puts_the_token_in_argv` (A7):
  - `platform="linux"`: the recorder gets one `file://` URI without T; the file is 0600 in a 0700 folder and holds the escaped URL; the folder is returned.
  - `platform="darwin", environ={}`: `osa` gets the http URL, the opener is not called, and the return is None.
  - `platform="darwin", environ={"BROWSER": "x"}`: the file route.
- (round 2, answer A, K-9) `test_an_opener_that_cannot_write_its_page_opens_nothing_and_returns_none`. Setup:
  - `dr._dash_private_page` monkeypatched to raise `OSError(errno.ENOSPC, "No space left on device")`;
  - `opener` and `osa` recorders, and `webbrowser.open` monkeypatched to a third recorder, so a fallback to `webbrowser.open(url)` is caught even if `opener` were ignored;
  - `out = io.StringIO()`, `url = "http://127.0.0.1:5006/?token=" + T` and `tempfile.tempdir = tmp_path`.

  Asserts:
  - `dr._dash_open_tokenized(url, platform="linux", environ={}, opener=rec, osa=osa_rec, out=out)` raises nothing and returns None.
  - None of the three recorders was called.
  - `out.getvalue().splitlines()` is exactly `["dash: the browser was not opened: its page could not be written (OSError); open the dashboard's link instead."]`. No line holds T, `?token=` or `http`.
  - The same holds for `platform="darwin", environ={"BROWSER": "x"}` (the file route), and for `PermissionError(13, "Permission denied")`, whose line names `PermissionError`.
  - No `dash-open-*` folder exists under `tmp_path`.
  - Base: AttributeError (no `_dash_open_tokenized`). An opener without step 3's `try` raises the OSError, so the first assertion fails.
- `test_the_token_line_is_bounded` (`os.pipe`):
  - `T + "\n" + "more"` → T, and the next `os.read` gives `b"more"`;
  - 300 characters → None;
  - no newline then close → None;
  - non-ASCII → None;
  - CRLF → stripped.
- (ratified 01oct2026) `test_the_private_page_is_0600_in_a_0700_folder`: with `tempfile.tempdir` monkeypatched to `tmp_path` and `out = io.StringIO()`, `dr._dash_private_page("<p>x</p>", "dash-link-", "link.html", out=out)` returns a folder under `tmp_path` whose basename starts `dash-link-`, mode 700, holding `link.html` mode 600 with the text, and `out` stays empty (no note for a private file). Under `os.umask(0)` (restored in `finally`) the file is still 600. With `os.open` monkeypatched to raise `OSError`, it raises and leaves no `dash-link-*` folder.
- (ratified 01oct2026, K-8, answer 2) `test_a_page_the_disk_will_not_keep_private_is_written_with_a_note`: `tempfile.tempdir = tmp_path`; `os.fchmod` monkeypatched to a recorder that changes nothing; `os.fstat` wrapped to return `os.stat_result((st.st_mode | 0o044,) + tuple(st)[1:])` of the real result; `out = io.StringIO()`; text `"<p>" + T + "</p>"`.
  - `dr._dash_private_page(text, "dash-link-", "link.html", out=out)` raises nothing and returns `(d, p)`; `p` exists and holds the text; the recorder saw one `fchmod(fd, 0o600)`.
  - `out.getvalue().splitlines()` is exactly one line, starting `dash: note: `, holding `p` and `TMPDIR`, and not T.
  - With the wrapper also setting `st_uid` to `os.geteuid() + 1` (index 4 of the tuple), it raises `OSError` (the anti-hijack check, kept), prints nothing and leaves no `dash-link-*` folder.
  - Base: AttributeError (no `_dash_private_page`). A `_dash_private_page` that raises on a loose mode fails its first assertion.
- `test_the_announcement_names_the_file_never_the_key`: `out = io.StringIO()`; `d = dr._dash_announce_key("http://127.0.0.1:5006/?token=" + T, out=out)`:
  - `out.getvalue().splitlines()` is exactly `[dr._DASH_LINK_SAID, <d>/link.html]`; with `hint="H"` a third line `H`;
  - no line holds T or `?token=`;
  - the file holds the escaped link; mode 600, folder 700;
  - (round 2) the failure case moved to the next test; this one no longer asserts round 1's `could not be written` line.
- (ratified 01oct2026, round 2, answer A, K-9) `test_an_unwritable_link_is_printed_once_with_a_warning`. Setup: `_dash_private_page` monkeypatched to raise `PermissionError(13, "Permission denied")`; `out = io.StringIO()`; `url = "http://127.0.0.1:5006/?token=" + T`; `tempfile.tempdir = tmp_path`.
  - `dr._dash_announce_key(url, out=out)` returns None and raises nothing.
  - `out.getvalue().splitlines()` is exactly `[dr._DASH_LINK_UNWRITTEN % "PermissionError", url]`. With `hint="H"` a third line `H` follows.
  - T appears in exactly one line, the URL's, and that line is the URL alone.
  - No `dash-link-*` folder is left under `tmp_path`.
  - `dr._DASH_LINK_UNWRITTEN.count("%s") == 1`, and the formatted warning holds neither T nor `os.sep`.
  - Base: AttributeError (no `_dash_announce_key`). A round-1 implementation fails at the line list.
- `test_the_process_key_is_made_once` (fixture: `serve_token_probe.drop_holder()` before and after): two calls return the same holder; its key is `_dash_token_valid` and 43 characters; `sys.modules["_dash_serve_key"]` is it. After `sys.modules["_dash_serve_key"] = types.ModuleType("x")` (no key), the next call replaces it with a valid holder.
- `test_the_bokeh_serve_key_announces_once_from_a_page_request` (same fixture; fake docs as `types.SimpleNamespace`): `session_context=SimpleNamespace(server_context=SimpleNamespace(application_context=SimpleNamespace(url="/app")), request=SimpleNamespace(arguments={}, connection=SimpleNamespace(stream=SimpleNamespace(socket=SimpleNamespace(getsockname=lambda: ("::1", 5123, 0, 0)))))))`; `DASH_SERVE_TOKEN` deleted; `tempfile.tempdir = tmp_path`; `out = io.StringIO()`.
  - A doc with `session_context=None` returns None and makes no holder.
  - A websocket-made doc (`request.connection=None`) returns the holder key and prints nothing.
  - The page doc returns the same key; `out` has three lines, `_DASH_LINK_SAID`, a path ending `link.html`, and `_DASH_BS_ORIGIN_HINT % 5123`; the file holds `http://127.0.0.1:5123/app?token=<key>` (loopback `::1` mapped to 127.0.0.1); no line holds the key.
  - A second page doc prints nothing more and writes no second `dash-link-*` folder.
  - With `DASH_SERVE_TOKEN=weak!value`, after `drop_holder()`, it returns None, prints one line naming the variable without `weak!value`, and writes no folder; a second call prints nothing.
- (ratified 01oct2026, round 2, K-9) `test_the_bokeh_serve_link_that_cannot_be_written_is_printed_once`. The fixture and fake docs are those of the previous test, with `dr._dash_private_page` monkeypatched to raise `OSError(errno.ENOSPC, "No space left on device")` for every call (the fresh folder fails).
  - The first page doc returns the holder key.
  - `out` is then exactly three lines: `_DASH_LINK_UNWRITTEN % "OSError"`, `http://127.0.0.1:5123/app?token=<key>` alone, and `_DASH_BS_ORIGIN_HINT % 5123`.
  - A second page doc, a websocket-made doc and a third page doc each return the same key and add nothing to `out`: a second session does not print it again.
  - The key appears in exactly one line of `out`.
  - No `dash-link-*` folder exists.
  - Base: AttributeError.
- `test_the_probe_knows_the_announcement`: `serve_token_probe.LINK_SAID == dr._DASH_LINK_SAID`, and `link_path_in(LINK_SAID + "\n/x/link.html\n")` is `/x/link.html` (the probe cannot import `dash_render` in TOK-02's child without the repo path, so it keeps a literal).

### `TestTheSessionGate` (in-process, `_load_app`, `ns["_DASH_SERVE_TOKEN"] = TEST_TOKEN`; RED unless marked)

- `test_a_session_without_the_token_gets_only_the_refusal`: `_SessionDoc(_Req(arguments={}))` with `ns["_load_spec_and_data"]` replaced by a spy that raises. The roots are one Div holding `403` and `DASH_SERVE_TOKEN`, with no Plot, and the spy is never called.
- `test_the_gate_runs_before_the_limiter`: a spy `_SESSION_LIMITER` is not consulted for a refused session, and is consulted once for an admitted one.
- `test_no_configured_token_makes_one_and_still_refuses` (replaces the design's `test_no_configured_token_fails_closed`; ratified 01oct2026). `ns["_DASH_SERVE_TOKEN"] = None`, `monkeypatch.delenv("DASH_SERVE_TOKEN", raising=False)`, `serve_token_probe.drop_holder()` before and after, `tempfile.tempdir = tmp_path`, stdout captured with `capsys`. Sessions are a local `_ServedDoc(test_adversarial_matrix._SessionDoc)` whose `session_context` property returns `types.SimpleNamespace(request=self._matrix_request, server_context=SimpleNamespace(application_context=SimpleNamespace(url="/app")))`; each request is `_req(args)` plus a fake `connection` whose `stream.socket.getsockname()` gives `("127.0.0.1", 5123)`.
  - An unkeyed session gets only the refusal Div (no Plot), and afterwards `sys.modules["_dash_serve_key"].key` is a valid 43-character key: the token is never missing.
  - Exactly one `tmp_path/dash-link-*/link.html` exists, mode 600 in a 700 folder, holding `http://127.0.0.1:5123/app?token=<that key>`; captured stdout names its path and holds neither the key nor `?token=`.
  - A session with `TEST_TOKEN` is refused, and so is a second unkeyed one; still one link folder.
  - A session with the holder's key gets a Plot.
  - Base: the unkeyed session gets a Plot (the I3 hole), so the test fails at its first assertion.
- `test_a_context_without_a_request_is_refused`.
- `test_an_in_process_document_still_builds` (GUARD): `Document()` gets a Plot.
- `test_bytes_and_str_values_both_match`.
- `test_the_refusal_names_no_request_data`: arguments `{"token": ["<script>x</script>"]}` and an `X-Forwarded-For` marker. The refusal text holds no `<script` and no marker.
- `test_a_refused_session_keeps_the_policy`: `doc.template` is the served template, so the CSP meta is in its page (as `test_csp.py:531`).
- `test_the_env_token_is_the_gate_under_bokeh_serve`: `CodeHandler(source=src, filename=...)`. With `DASH_SERVE_TOKEN=TEST_TOKEN` a keyed `_SessionDoc` gets a Plot, and no holder is made. Without the variable (holder dropped), a `TEST_TOKEN` session gets the refusal and a holder key exists (the process made its own).

### `TestTheGeneratedAppIsGated` (RED)

- `test_every_server_the_app_builds_has_the_token_provider` (A5):
  - with `ns["Server"]` a recorder, both `_dash_server_app()` and `_dash_server_app(token=T)` pass an `auth_provider` whose class is `_DashTokenAuth`;
  - after `token=T`, `ns["_DASH_SERVE_TOKEN"] == T`, nothing is printed and `ns["_DASH_LINK_DIR"]` is None;
  - after a call with no key, no global and no variable (`tempfile.tempdir = tmp_path`, `capsys`): `ns["_DASH_SERVE_TOKEN"]` is a fresh valid 43-character key; the recorded `auth_provider` admits it; `ns["_DASH_LINK_DIR"]` is a 0700 `dash-link-*` folder holding a 0600 `link.html` with `http://127.0.0.1:<port>/?token=<that key>`; stdout is `_DASH_LINK_SAID` then that path, and holds no key.
- (ratified 01oct2026, round 2, answer A, K-9) `test_a_key_whose_link_cannot_be_written_is_printed_once_and_served`. It replaces round 1's `test_a_key_that_cannot_be_announced_is_not_served`, which is struck and never written. Setup:
  - `ns["_dash_private_page"]` is replaced by a function that raises `PermissionError(13, "Permission denied")` (the app's fresh folder is its only folder, so every folder fails);
  - a recorder Server whose `stop` records;
  - no key, no global (`ns["_DASH_SERVE_TOKEN"] = None`) and no variable;
  - `tempfile.tempdir = tmp_path`, and `capsys`.

  Asserts:
  - `_dash_server_app()` returns the recorder Server, raises nothing, and `stop` was never called.
  - `ns["_DASH_LINK_DIR"]` is None.
  - Stdout is exactly `[dr._DASH_LINK_UNWRITTEN % "PermissionError", "http://127.0.0.1:<port>/?token=" + ns["_DASH_SERVE_TOKEN"]]`.
  - The recorded `auth_provider` admits that key.
  - A second `_dash_server_app()` in the same namespace (the global now holds the key) prints nothing: once per process.
  - An in-process session made afterwards with `_SessionDoc(_Req(arguments={}))` gets the refusal and prints nothing.
  - Base: stdout is empty, because no key is made, so the line list fails.
- (round 2) `test_an_address_no_link_can_name_stops_the_server`: with the recorder Server and no key, `_dash_server_app(address="fe80::1%en0")` raises a RuntimeError naming `DASH_SERVE_TOKEN` and the address, not the key, and `stop` was called once. This is K-2's one remaining stop. Base: no RuntimeError.
- `test_an_invalid_token_argument_is_refused`.
- `test_the_app_source_holds_no_key`:
  - no AST string constant fullmatches `[A-Za-z0-9_-]{32,128}`, excluding the values assigned to `_SPEC_B64` and `_DATA_B64` (measured 0 at 7421d3d);
  - `_DASH_SERVE_TOKEN = None` is in the source.
- `test_the_launcher_resolves_the_token_before_it_serves`. In the `__main__` text with comments stripped (as `test_server_rate_limit.py:968-980`):
  - `_dash_resolve_token(` comes before `_dash_server_app(`;
  - `_dash_install_access_log_redaction()` comes before `_server.start()`;
  - there is no `_server.show`;
  - (ratified 01oct2026) there is no `print(_dash_url` and no `_dash_tok_made`, and `_DASH_LINK_DIR` appears in the `finally:` block.
- `test_show_opens_the_tokenized_loopback_link`. The harness:
  - execs `__main__` with a fake Server and loop (`call_later` records a list) and `--show`;
  - sets `BROWSER=x`;
  - monkeypatches `webbrowser.open` with a recorder that reads the file it is handed.

  Asserts:
  - the file holds `http://127.0.0.1:<port>/?token=` plus 43 characters;
  - `(dr._DASH_REDIRECT_TTL_S, shutil.rmtree, <dir>, True)` was recorded;
  - after the run the folder is gone (A8).
- `test_the_app_prints_its_link_files_path_never_the_key` (replaces the design's `test_the_app_prints_its_link_only_when_it_made_the_token`; ratified 01oct2026). With the same harness (a fake Server, so `_dash_server_app` runs for real around it) capturing stdout, and `tempfile.tempdir = tmp_path`:
  - without the variable: `serve_token_probe.link_path_in(stdout)` names a `link.html`, mode 600 in a 700 folder, holding `http://127.0.0.1:<port>/?token=` plus 43 characters; no stdout line holds `?token=` or that key; after the run the folder is gone (the `finally`);
  - with `DASH_SERVE_TOKEN=TEST_TOKEN`: no link line, no `dash-link-*` folder, no line holding `TEST_TOKEN` or `?token=`;
  - a `Bokeh Server running at http://127.0.0.1:` line exists;
  - no line holds `localhost`.

### `TestTheAppResolvesItsToken` (RED)

- `test_precedence_stdin_then_env_else_none` (ratified 01oct2026: the resolver no longer makes keys; `_dash_server_app` does, K-2):
  - stdin T1 with the env holding T2 and the flag → T1;
  - env only → T2;
  - neither → None;
  - the variable is popped in every case.
- `test_a_weak_env_token_is_refused_without_echo`: env `weak!value` raises ValueError naming `DASH_SERVE_TOKEN`, without `weak!value`.
- `test_a_bad_stdin_line_is_refused`: too long, empty or non-ASCII.
- `test_a_weak_env_token_stops_the_app` [serve]: `python app.py --port P` with `DASH_SERVE_TOKEN=weak!value` gives rc 2. stderr names the variable, and neither stream holds `weak!value`.

### `TestTheLauncherPassesTheToken` (fake Popen; RED)

- `test_the_token_goes_to_stdin_not_argv` (round 2: L-1..L-5):
  - `--token-stdin` is in cmd, after the element equal to the app path. No cmd element fullmatches the key pattern or contains the key.
  - `kw["stdin"] is subprocess.PIPE`.
  - `FakeStdin.key_line()` is one valid key, and that write is the last one. Every earlier write is S08's app-text hand-over: the earlier write is S08's one frame write, equal to `dr._dash_app_frame(<the app file's bytes>)`, and none of them holds the key. Under L-5's other-handle route, `.writes` is exactly `[key + b"\n"]`.
  - `closed` is False until the child has exited (TD-4).
  - It does not pin S08's part of the command line (L-4).
- `test_the_ready_line_and_the_link_file`. A local `http.server` `/health` stub, a fake child and a 0700 `link_dir`. stdout holds:
  - `dash: the server answers at http://127.0.0.1:<P>/`;
  - the "opens only through its link" line;
  - the line `<link_dir>/link.html`.

  The fake child's `poll` saw the file at mode 0600, holding `http://127.0.0.1:<P>/?token=` plus the key written to stdin. After return the file is gone, and stdout never holds the key.
- `test_without_a_run_folder_the_link_goes_to_a_private_temp_folder`: `link_dir=None`. The printed path's folder is 0700 during the run and gone after.
- `test_a_429_from_health_still_counts_as_answering` (A6): the stub answers 429, and the ready and link lines are printed.
- `test_the_stderr_tail_and_forwarded_lines_are_redacted`: the fake child prints `GET /?token=<key>&x=1 (127.0.0.1)` and the bare key, and exits 3 with the key in stderr. Neither the RuntimeError message nor stdout holds the key.
- `test_a_child_that_cannot_take_the_key_is_stopped`: `FakeStdin(broken=True)` raises a RuntimeError naming "key", and the child is stopped (S08's `_dash_stop_child` recorded).
- (ratified 01oct2026, round 2, K-8) `test_a_run_folder_that_refuses_the_link_moves_it_to_a_private_folder`. Setup: `dr._dash_private_write` monkeypatched to raise `dr._DashUnsafePath("x")`, then, in a second run, `OSError(errno.EACCES, "Permission denied")`; `tempfile.tempdir = tmp_path / "sys"`.
  - `dr._dash_write_link(run_dir, url)` returns `<tmp_path>/sys/dash-link-*/link.html`, mode 600 in a 700 folder, holding the escaped link, and that folder.
  - Captured stdout is empty.
  - With `dr._dash_private_page` also monkeypatched to raise `OSError(errno.ENOSPC, "No space left on device")`, `_dash_write_link` raises that OSError and prints nothing (the launcher prints, K-9).
  - Base: AttributeError (no `_dash_write_link`).
- (ratified 01oct2026, K-8) `test_a_link_file_that_cannot_be_private_moves_to_a_private_folder`: `dr._dash_write_link(run_dir, url)` with `os.lstat` monkeypatched to report mode `0o100644` for `<run_dir>/link.html` only, and `tempfile.tempdir = tmp_path / "sys"`: the returned path is `<tmp_path>/sys/dash-link-*/link.html`, mode 600 in a 700 folder; `<run_dir>/link.html` no longer exists; the returned folder is not None; captured stdout holds no `dash: note:` line (the fallback is private). Unpatched, the path is `<run_dir>/link.html` and the folder None.
- (ratified 01oct2026, K-8, answer 2) `test_a_link_no_folder_can_keep_private_is_written_with_a_note`: as the previous test, plus `os.fstat` wrapped to report the real result with `| 0o044` and `os.fchmod` monkeypatched to a no-op (the disk keeps no permissions anywhere). `dr._dash_write_link(run_dir, url)` raises nothing and returns `<tmp_path>/sys/dash-link-*/link.html`, holding the escaped link, and its folder; `<run_dir>/link.html` no longer exists; captured stdout is exactly one line, starting `dash: note: ` and naming the returned path, holding neither the key nor `?token=`. Base: AttributeError (no `_dash_write_link`).
- (ratified 01oct2026, round 2, answer A, K-9) `test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served`. It replaces round 1's `test_a_link_that_cannot_be_written_stops_the_server`, which is struck and never written.
  - **Setup.** The `/health` stub and fake child of `test_the_ready_line_and_the_link_file`. The stub answers 200 on every probe, and the fake child's `poll` returns None for five passes after the first answer, then 0. `dr._dash_private_write` is monkeypatched to raise `dr._DashUnsafePath("x")` (the run folder), and `dr._dash_private_page` to raise `OSError(errno.ENOSPC, "No space left on device")` (the fallback folder).
  - **Asserts:**
    - `_dash_launch_app` returns normally (no RuntimeError).
    - The fake child's `poll` ran all five passes after the ready line, so the server was kept.
    - S08's `_dash_stop_child` is not recorded before the child's own exit.
    - Stdout's lines, in order: the ready line `dash: the server answers at http://127.0.0.1:<P>/…`, `dr._DASH_LINK_UNWRITTEN % "OSError"`, and `http://127.0.0.1:<P>/?token=<the key line written to stdin>` alone.
    - The key appears in exactly one stdout line, although the fake child also prints `GET /?token=<key>`: that forwarded line is redacted.
    - No `_DASH_LINK_SAID` line is printed, and no `link.html` exists under `run_dir` or `tmp_path`.
    - The same holds when only `dr._dash_private_page` raises and the run-folder write is real but fails its privacy check (the fallback fails).
  - **Base:** TypeError (no `link_dir` keyword).

### `TestTheServedAppRequiresItsToken` ([serve]; `_LiveApp` with `TEST_TOKEN`; RED unless marked)

- `test_a_session_without_the_token_reads_no_rows`: `pull_session(url)` raises OSError, and no `mpg` ColumnDataSource is received. Base: 8 rows (the I3 probe).
- `test_the_page_without_the_token_is_403`: `GET /` gives 403 with reason `dr._DASH_TOKEN_REFUSAL`. Base: 200.
- `test_a_wrong_or_doubled_token_is_403`: 43 × `x`, T with its last character changed, and `?token=T&token=T`.
- `test_the_right_token_serves_the_dashboard`: `GET /?token=T` gives 200 with the title, and a keyed pull gets every row.
- `test_the_browser_path_opens_the_websocket`: `app.session("http://127.0.0.1:%d" % port) == (101, "ACK")`.
- `test_a_forged_session_jwt_is_refused`: `generate_jwt_token` unsigned, with no arguments and with a wrong key. `app.session(origin, jwt=forged) == (403, None)`.
- `test_autoload_and_metadata_need_the_token`: 403 without, 200 with.
- `test_health_and_static_stay_open` (GUARD).
- `test_a_refusal_carries_the_headers_and_reflects_nothing`: the 403 has the four headers (`test_csp._assert_headers`), and `?token=%3Cscript%3E` gives a body with no `<script`.
- `test_unauthenticated_requests_do_not_spend_the_session_budget`: `--sessions-per-client 1`, 50 unkeyed `GET /`, then one keyed pull admitted (no `429`).
- (ratified 01oct2026) `test_a_keyless_start_makes_a_key_and_a_private_link`: `_LiveApp(app, env={"DASH_SERVE_TOKEN": None})` (a hand-run `python app.py --port P`, no `--token-stdin`).
  - The output holds `_DASH_LINK_SAID` and, on the next line, a path; `serve_token_probe.read_link` gives mode `600`, folder mode `700`, host `127.0.0.1`, port P, path `/` and a 43-character key.
  - `GET /` is 403; `GET /?token=<key>` is 200; a pull with the key gets every row; a pull with `TEST_TOKEN` raises OSError.
  - The app's output (`_launcher_said(app)`) never holds the key.
  - After `send_signal(SIGINT)` and `wait(15)`, the link's folder is gone.
  - Base: `GET /` is 200 and no link line exists.
- (ratified 01oct2026, round 2, answer A, K-9) `test_a_keyless_start_whose_link_cannot_be_written_prints_it_once_and_serves`.
  - **Setup.** A local Popen of `[sys.executable, "-c", PATCH, app, "--port", P]`, where `PATCH` sets `tempfile.mkdtemp` to a function raising `PermissionError(13, "Permission denied")` (process-wide, Evidence §7), sets `sys.argv = sys.argv[1:]`, and runs `runpy.run_path(sys.argv[0], run_name="__main__")`. `DASH_SERVE_TOKEN` is removed from its environment, and its stdout is read by a thread into a list.
  - **The print.** The output holds `dr._DASH_LINK_UNWRITTEN % "PermissionError"`, then, on the next line alone, a URL matching `serve_token_probe.LINK_RE` with host `127.0.0.1`, port P and path `/`.
  - **It serves.** `GET /` is 403. `GET /?token=<key>` is 200, and a pull with the key gets every row.
  - **Once.** After two more keyed and two unkeyed GETs and a second keyed pull, the key appears in exactly one output line, and the warning appears once.
  - **No folder.** No `dash-link-*` folder was made.
  - **Stop.** `send_signal(SIGINT)` and `wait(15)` end it.
  - **Base:** `GET /` is 200 and no warning line exists.
- (round 2, answer A, K-9; the `--show` route) `test_a_keyless_show_start_whose_link_cannot_be_written_prints_it_once_and_serves`. The previous test with the browser opener on, because every other K-9 test runs without `--show` or with `nobrowser`.
  - **Setup.** As the previous test, with two changes:
    - The command is `[sys.executable, "-c", PATCH_SHOW, app, "--port", P, "--show"]`. `PATCH_SHOW` is `PATCH` plus `webbrowser.open` replaced by a recorder that prints the marker line `dash-test: opener called` (no URL) and returns True.
    - The environment sets `BROWSER=dash-test-no-browser`, so the file route is taken on every platform (on darwin with `BROWSER` unset the osascript route writes no file and would open a real browser).
  - **The print.** The output holds the warning, then on the next line alone the URL (as the previous test), each exactly once. It also holds the opener's line, `dash: the browser was not opened: its page could not be written (PermissionError); open the dashboard's link instead.`, exactly once. That line holds no key.
  - **It serves.** `GET /?token=<key>` is 200. Five seconds after the opener's line appeared, `proc.poll()` is None (the process is still alive), and a second `GET /?token=<key>` is 200.
  - **Nothing opened.** The output has no `dash-test: opener called` line. The key appears in exactly one output line, and no `dash-link-*` or `dash-open-*` folder was made.
  - **Stop.** `send_signal(SIGINT)` and `wait(15)` end it.
  - **Base:** `GET /` is 200 and no warning line exists. An opener without TR-13.8 step 3's `try` ends the process with an OSError traceback after `start()`, so `poll()` is not None and the second keyed GET fails.
  - `dash serve`'s child runs the same `__main__` and the same opener, so this test and the unit test above cover that route too. `test_dash_serve_prints_an_unwritable_link_once_and_keeps_serving` patches only the launcher's process, so it cannot make the child's `open.html` fail.
- (round 2, K-9, `dash serve`'s route) `test_dash_serve_prints_an_unwritable_link_once_and_keeps_serving`.
  - **Setup.** The real `dr._dash_launch_app(app_path, port, …, link_dir=run_dir)`, on an app built as S08's real-launch tests in `test/test_serve_lifecycle.py` build theirs, runs in a thread. In the test process, `dr._dash_private_write` is monkeypatched to raise `dr._DashUnsafePath("x")` and `dr._dash_private_page` to raise `OSError(errno.ENOSPC, "No space left on device")`. Stdout goes through `contextlib.redirect_stdout` into a lock-guarded buffer.
  - **The print.** The buffer gains the ready line, the warning and one URL line.
  - **It serves.** That URL's GET is 200 and a keyed pull gets every row. A second keyed pull adds no line holding the key.
  - **Stop.** The launch is stopped as S08's real-launch tests stop theirs. The key appears in exactly one buffer line.
  - **Base:** TypeError (no `link_dir` keyword).
- `test_the_token_is_per_launch`: two launches without the variable write link files with different keys (read with `read_link`), and the first key gets 403 from the second server.
- `test_the_access_log_never_carries_the_token`: after `/?token=T&token=T`, `/?token=T` and `/?token=<wrong>`, `_launcher_said(app)` holds no T and holds `<query redacted>`.
- `test_the_link_never_reaches_an_ipv6_squatter` (A1; skip only if binding `::1` fails):
  - a recorder listens on `[::1]:P`;
  - `python app.py --port P` (no variable) writes its link file and prints its path;
  - the link's host (from `read_link`) is `127.0.0.1`;
  - a GET on the link gives 200;
  - the recorder saw no request holding the key.
- `test_gate_a_and_gate_b_agree_in_process` (A5): a thread with its own asyncio loop runs `ns["_dash_server_app"](port=p, token=T)`, `.start()` and `io_loop.start()`. `pull_session(arguments={"token": T})` gets the rows. Stopped through `io_loop.add_callback(io_loop.stop)`.

### `TestBokehServeAlwaysHasAKey` ([serve]; RED; renamed from the design's `TestBokehServeNeedsTheToken`, ratified 01oct2026)

`_Served(app, token=None, allow_127=True)` unless a test says otherwise.

- `test_without_the_env_the_app_makes_a_key_and_announces_it` (replaces the design's `test_without_the_env_every_session_is_refused`):
  - an unkeyed `GET /<app>` is 200 and its pulled session holds only the refusal Div naming `DASH_SERVE_TOKEN` and `link.html`;
  - the server's output then holds `_DASH_LINK_SAID`, a path, and `_DASH_BS_ORIGIN_HINT % port`; `read_link` gives mode `600`, folder `700`, host `127.0.0.1`, the server's port, path `/<app>` and a 43-character key;
  - a pull with that key gets the Plot and 74 rows; a pull with `TEST_TOKEN` gets only the refusal;
  - a second unkeyed `GET` adds no link line;
  - the server's output never holds the key;
  - after SIGINT and `wait(15)`, the link's folder is gone (`atexit`).
  - Base: the unkeyed `GET` gets the Plot and no link line exists.
- `test_a_websocket_first_session_leaves_the_link_to_the_first_page`: an unkeyed `pull_session` first gets the refusal and adds no link line; a following unkeyed `GET` adds exactly one, whose key opens a pull.
- `test_with_the_origin_flag_the_link_opens_the_websocket` (GUARD: Bokeh's own origin rule, which passes at the base too; it pins the reason for K-5's hint): the key-bearing page's JWT upgrades `/<app>/ws` with `Origin: http://127.0.0.1:<port>` → 101; under a second `_Served` without the flag → 403 (why the help and the hint name the flag; Evidence §6).
- `test_a_set_but_invalid_env_refuses_every_session`: `DASH_SERVE_TOKEN=weak!value`. Unkeyed, `weak!value`-keyed and `TEST_TOKEN`-keyed pulls all get the refusal; the output holds one line naming the variable and no `weak!value`, and no link line.
- `test_with_the_env_the_link_needs_the_token`: an unkeyed pull is refused, and a keyed pull gets the Plot and rows; no link line is printed.
- (ratified 01oct2026, round 2, answer A, K-9) `test_an_unwritable_link_is_printed_once_per_app_path`.
  - **Setup.** `bokeh serve` started as `[sys.executable, "-c", PATCH_BS, app, "--port", P, "--allow-websocket-origin", "127.0.0.1:P"]`. `PATCH_BS` patches `tempfile.mkdtemp` as above, then calls `bokeh.__main__.main()` with `sys.argv = ["bokeh", "serve"] + sys.argv[1:]` (Evidence §7: `bokeh.__main__.main` exists on 3.8.0 and 3.9.0). `DASH_SERVE_TOKEN` is unset, readiness is on `/static/js/bokeh.min.js`, and the output is kept by a reader thread.
  - **The print.** The first unkeyed `GET /<app>` is 200, and its session gets the refusal. The output then holds the warning, the URL `http://127.0.0.1:P/<app>?token=<key>` alone on the next line, and `_DASH_BS_ORIGIN_HINT % P`.
  - **It serves.** A pull with that key gets the Plot and 74 rows.
  - **Once.** Three more unkeyed GETs and one keyed GET add no line: a second session does not print it again. The key appears in exactly one output line.
  - **Stop.** SIGINT, then `wait(15)`.
  - **Base:** the unkeyed GET gets the Plot, and no warning exists.

### Elsewhere

- **`test/test_security_surface.py::TestServeBindsLoopbackByDefault::test_the_help_names_the_key_and_its_limits`** (RED). The whitespace-collapsed `server_mode` section:
  - holds `DASH_SERVE_TOKEN`, `?token=`, `constant time`, `address bar`, `history`, `SSH tunnel`, `{cmd:http://127.0.0.1:`, `link.html`, `never runs without a key` and `--allow-websocket-origin 127.0.0.1` (the last three ratified 01oct2026);
  - holds none of `only this machine can reach it`, `There is no password`, `single-user tool` and `every session gets a page saying so`;
  - does not match `localhost[^ ]*\?token=`.
- **`test/test_security_surface.py::TestTheGeneratedAppBindsLoopbackAtRuntime::test_every_server_gets_the_key_check`** (RED): for no address, `""` and `0.0.0.0`, `seen[-1]["auth_provider"].__class__.__name__ == "_DashTokenAuth"`. Each call makes and announces a key (K-2), so the test sets `tempfile.tempdir` to `tmp_path` and resets `ns["_DASH_SERVE_TOKEN"]` to None between calls.
- **`test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads::test_no_function_in_the_app_reads_an_undefined_global`** (extended, RED): the explicit tuple gains `"_dash_token_auth"`, `"_dash_session_token_ok"`, `"_dash_open_tokenized"`, `"_dash_announce_key"`, `"_dash_bokeh_serve_key"`, `"_DASH_TOKEN_RE"`, `"_DASH_SERVE_TOKEN"` and `"_DASH_LINK_DIR"`.
- **`test/test_server_rate_limit.py::TestTheLauncherFlags::test_the_launcher_help_lists_every_flag`** (extended, RED): `--token-stdin`.
- **`test/test_adversarial_matrix.py::SURFACES["served_session_token"]`** (new). The key also goes in `_REQUIRED_SURFACES`:
  - **bypass:** `test/test_serve_token.py::TestTheServedAppRequiresItsToken::test_a_wrong_or_doubled_token_is_403`, `...::test_a_forged_session_jwt_is_refused`, `test/test_serve_token.py::TestTheTokenHelpers::test_invalid_shapes_are_refused`, `test/test_serve_token.py::TestTheSessionGate::test_no_configured_token_makes_one_and_still_refuses`, `test_serve_launch.cscript:TOK-02`;
  - **injection:** `...TestTheServedAppRequiresItsToken::test_a_refusal_carries_the_headers_and_reflects_nothing`, `...TestTheSessionGate::test_the_refusal_names_no_request_data`, `...TestTheTokenHelpers::test_the_redirect_page_escapes_and_sends_no_referrer`;
  - **exhaustion:** `...TestTheServedAppRequiresItsToken::test_unauthenticated_requests_do_not_spend_the_session_budget`, `...TestTheTokenHelpers::test_a_jwt_that_inflates_is_refused_quickly`, `...TestTheTokenHelpers::test_the_token_line_is_bounded`, `...TestTheTokenHelpers::test_the_bokeh_serve_key_announces_once_from_a_page_request`.

  The meta-tests (collection and `"TOK-02 PASS"` display) hold as soon as the nodes and the case exist.
- **Certification** (`test/test_serve_launch.cscript`, RED): TOK-01..TOK-04 as TR-13.16.

**Mutation table.**

| Break this | Test that must die |
|---|---|
| `_admit` returns `"dash"` always | `test_the_page_without_the_token_is_403`, TOK-02 `root_without_key=403` |
| Gate B returns True when `request` is None | `test_a_context_without_a_request_is_refused` |
| Gate B placed after the limiter | `test_the_gate_runs_before_the_limiter`, `test_unauthenticated_requests_do_not_spend_the_session_budget` |
| `_dash_token_matches` uses `==` | `test_matching_is_constant_time` |
| `_dash_one_value` takes the first of two | `test_a_wrong_or_doubled_token_is_403` |
| `_dash_server_app` passes no `auth_provider` | `test_every_server_the_app_builds_has_the_token_provider`, P4-82 |
| `_dash_server_app` does not set the global (A5) | `test_gate_a_and_gate_b_agree_in_process` |
| The key in argv | `test_the_token_goes_to_stdin_not_argv` |
| The launcher closes stdin after writing | `test_the_token_goes_to_stdin_not_argv` (`closed`), S08's real-launch tests |
| `localhost` in `_dash_tokenized_url` | `test_the_tokenized_url`, `test_the_link_never_reaches_an_ipv6_squatter` |
| The ready line prints the link | TOK-03, `test_the_ready_line_and_the_link_file` |
| No redaction filter | `test_the_access_log_never_carries_the_token` |
| No size probe in `_dash_ws_payload` | `test_a_jwt_that_inflates_is_refused_quickly` |
| `os.open` without `O_EXCL` or with 0644 | `test_opening_never_puts_the_token_in_argv` (mode), `test_the_private_page_is_0600_in_a_0700_folder` |
| Gate B admits when no key is configured (ratified 01oct2026) | `test_no_configured_token_makes_one_and_still_refuses`, `test_without_the_env_the_app_makes_a_key_and_announces_it` |
| `_dash_server_app` makes a key but does not announce it | `test_every_server_the_app_builds_has_the_token_provider`, `test_a_keyless_start_makes_a_key_and_a_private_link` |
| `_dash_server_app` stops, raises or prints nothing when the link cannot be written (round 2) | `test_a_key_whose_link_cannot_be_written_is_printed_once_and_served`, `test_a_keyless_start_whose_link_cannot_be_written_prints_it_once_and_serves` |
| `_dash_server_app` serves a key whose address no link can name | `test_an_address_no_link_can_name_stops_the_server` |
| `_dash_announce_key` prints the link when its file was written | `test_the_announcement_names_the_file_never_the_key`, `test_a_keyless_start_makes_a_key_and_a_private_link` |
| `_dash_announce_key`'s fallback drops the warning, prints the link before it, twice, with a prefix, or puts the path or key in the warning (K-9) | `test_an_unwritable_link_is_printed_once_with_a_warning` |
| `_dash_open_tokenized` lets its page's OSError escape (the app dies after `start()`), falls back to `webbrowser.open(url)`, `opener(url)` or the URL in argv, prints no line, or prints the key or URL in it (round 2, K-9) | `test_an_opener_that_cannot_write_its_page_opens_nothing_and_returns_none`, `test_a_keyless_show_start_whose_link_cannot_be_written_prints_it_once_and_serves` |
| `_dash_bokeh_serve_key` prints the fallback link per session, or marks `linked` after the attempt | `test_the_bokeh_serve_link_that_cannot_be_written_is_printed_once`, `test_an_unwritable_link_is_printed_once_per_app_path` |
| The key line is written before S08's app text, through `proc.stdin` (text) instead of `_dash_child_stdin(proc)`, or the pipe is closed after it (L-1..L-3) | `test_the_token_goes_to_stdin_not_argv`, TOK-02 |
| `_dash_process_key` makes a key per call | `test_the_process_key_is_made_once`, `test_without_the_env_the_app_makes_a_key_and_announces_it` (keyed pull) |
| `_dash_bokeh_serve_key` announces per session, or before marking `linked` | `test_the_bokeh_serve_key_announces_once_from_a_page_request` |
| `_dash_bokeh_serve_key` reads the `Host` header | `test_the_bokeh_serve_key_announces_once_from_a_page_request` (the fake request has no `Host`; the link names `getsockname`'s port) |
| A set but invalid variable makes a key instead | `test_a_set_but_invalid_env_refuses_every_session`, `test_the_bokeh_serve_key_announces_once_from_a_page_request` |
| `_dash_write_link` skips the privacy check | `test_a_link_file_that_cannot_be_private_moves_to_a_private_folder` |
| `_dash_write_link` raises on a refused run-folder write instead of falling back, or prints in the launcher's place | `test_a_run_folder_that_refuses_the_link_moves_it_to_a_private_folder` |
| `_dash_private_page` refuses a loose mode instead of noting it, prints no note, or prints the key in it (K-8) | `test_a_page_the_disk_will_not_keep_private_is_written_with_a_note` |
| `_dash_private_page` drops its anti-hijack type or owner check | `test_a_page_the_disk_will_not_keep_private_is_written_with_a_note` (the foreign-uid case) |
| `_dash_write_link` refuses when no folder can hold 0600 (K-8) | `test_a_link_no_folder_can_keep_private_is_written_with_a_note` |
| The launcher's link failure stops the child, prints the link twice, not at all or before the warning, or lets the forwarded copy through (round 2) | `test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served`, `test_dash_serve_prints_an_unwritable_link_once_and_keeps_serving` |
| The served app gains a file write outside `_dash_private_page` and its folders' removal | S08's `TestTheServedAppWritesNoFile::test_the_generated_app_has_no_file_writing_call`, as 13-06 flips it |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Key form, matching, URL, redaction, opener, stdin line, JWT bound | pytest unit (`TestTheTokenHelpers`) | none | n/a (served only) |
| Gate B in process; in-process builds unaffected | pytest (`TestTheSessionGate`) | none | served; the saved page has no session |
| Gate A on every Server; the app file holds no key; `__main__` order, opener and link print | pytest (`TestTheGeneratedAppIsGated`, `TestTheAppResolvesItsToken`) | none | served |
| The launcher: stdin, link file, 429, redaction, failure | pytest with a fake Popen (`TestTheLauncherPassesTheToken`) | none | served |
| A live `python app.py`: 403 everywhere without the key, 200 with it, browser websocket, forged JWT, budget, per-launch key, logs, IPv6 squat, gate agreement | pytest [serve] | none | served |
| `bokeh serve app.py` with the variable, with an invalid one, and without it (the app makes a key, announces a 0600 link once from the first page request, refuses every keyless session; the origin flag) | pytest [serve] (`TestBokehServeAlwaysHasAKey`) | none | served |
| The self-made key (ratified 01oct2026): private page, announcement, process holder, `bokeh serve` key, `_dash_server_app` generation and its failure path, the link-file privacy fallback and its note (K-8), the print-once fallback when no folder takes the link (K-9, round 2) under `python app.py`, `bokeh serve` and `dash serve`, the key line after S08's app text (L-2), and S08's no-other-write guard as flipped | pytest unit and in process (`TestTheTokenHelpers`, `TestTheSessionGate`, `TestTheGeneratedAppIsGated`, `TestTheLauncherPassesTheToken`; `test/test_private_files.py::TestTheServedAppWritesNoFile`) and live (`TestTheServedAppRequiresItsToken::test_a_keyless_start_makes_a_key_and_a_private_link`, `::test_a_keyless_start_whose_link_cannot_be_written_prints_it_once_and_serves`, `::test_a_keyless_show_start_whose_link_cannot_be_written_prints_it_once_and_serves`, `::test_dash_serve_prints_an_unwritable_link_once_and_keeps_serving`, `TestBokehServeAlwaysHasAKey::test_an_unwritable_link_is_printed_once_per_app_path`) | none | served |
| A real `dash serve` in Stata: refused without the key, 74 rows with it, a 0600 link in 0700, no key in text or SMCL logs | TOK-01..TOK-04 in `test_serve_launch.cscript` | none | served |
| The help's claims | pytest + TOK-04 | none | n/a |
| The saved page is unchanged | `test/test_csp.py` saved-page tests, `test/test_mode_parity.py` (GUARD runs) | none | saved |

**Acceptance criteria.**
- **AC-13.1** `python3 -m pytest test/test_serve_token.py -q -n0 -p no:cacheprovider` passes with no skip except `test_the_link_never_reaches_an_ipv6_squatter` on a host without IPv6 loopback. `grep -c "test_no_configured_token_fails_closed\|test_without_the_env_every_session_is_refused\|TestBokehServeNeedsTheToken\|test_a_key_that_cannot_be_announced_is_not_served\|test_a_link_that_cannot_be_written_stops_the_server" test/test_serve_token.py` prints 0 (the struck fail-closed and stop tests were never written).
- **AC-13.2** Every flipped file passes, and `python3 -m pytest test/ -q` is green once:
  - `test/test_server_serves.py`, `test/test_csp.py`, `test/test_adversarial_matrix.py`;
  - `test/test_server_rate_limit.py`, `test/test_server.py`;
  - `test/test_serve_launcher.py`, `test/test_help_claims_2.py`, `test/test_help_claims_4.py`;
  - `test/test_serve_lifecycle.py`, `test/test_security_surface.py`, `test/test_resource_limits.py`, `test/test_private_files.py` (S08's `TestTheServedAppWritesNoFile` guard, flipped by 13-06);
  - `test/test_function_test_map.py`, `test/test_program_coverage_map.py`, `test/test_tracking_documents.py`.
- **AC-13.3** `<scratch>/run_test_serve_launch.log` holds `TOK-01 PASS` … `TOK-04 PASS` and ends `All dash serve option tests PASSED.`. `test_help_claims_4.cscript` (LC-01 flipped) and `test_e2e_serve.cscript` (P4-82) pass.
- **AC-13.4** BUGS.md carries the P0.12a entry closed `(WP-29, P0.12a)`, naming tests that exist. Both `<!-- WP-29 P0.12a -->` markers are replaced. `WP29_OPEN` has no `"P0.12a"`.
- **AC-13.5** `grep -c "localhost:{_port}\|http://localhost:%d" dash_render.py` prints 0, and `grep -c "auth_provider=_dash_token_auth(" dash_render.py` prints 1.
- **AC-13.6** (ratified 01oct2026) The token is never missing: `python3 -m pytest test/test_serve_token.py -q -n0 -p no:cacheprovider -k "makes_one or makes_a_key or keyless or cannot_be_written or announce or process_key or private_page or invalid_env or websocket_first or origin_flag"` passes; `grep -c "print(_dash_url\|_dash_tok_made" dash_render.py` prints 0; and `grep -c "_dash_bokeh_serve_key(doc)" dash_render.py` prints 1 (Gate B's line).
- **AC-13.7** (ratified 01oct2026, round 2) Print once, and the key after the app text.
  - `python3 -m pytest test/test_serve_token.py -q -n0 -p no:cacheprovider -k "printed_once or prints_it_once or unwritable_link or refuses_the_link or no_link_can_name or stdin_not_argv or opener_that_cannot_write or keyless_show_start"` passes, with no skip. It includes `test_an_opener_that_cannot_write_its_page_opens_nothing_and_returns_none` and `test_a_keyless_show_start_whose_link_cannot_be_written_prints_it_once_and_serves`.
  - `grep -c "was stopped: its link was not written\|its link could not be written; set" dash_render.py` prints 0.
  - `grep -c "_DASH_LINK_UNWRITTEN" dash_render.py` prints at least 4: the definition, the copy list, `_dash_announce_key` and the launcher.
  - `grep -c '_raw.write((token' dash_render.py` prints 1, and that line ends `.encode("ascii"))`; `grep -c 'proc.stdin.write(' dash_render.py` prints 0: the key line is written as bytes through `_dash_child_stdin(proc)` (L-3).

## Tasks

**Commit boundary.** ONE commit, P0.12a, holding 13-03 to 13-16. Subject: `Require a per-launch key to open the served dashboard (WP-29 P0.12a)`. It is made by 13-16 on `wp29-s13` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s13` (`$WT`), after the section's one full pytest run there. The merger lands it on `wp29-p0` with the same message (index step 1).

The body:
1. opens with `<scratch>/13-P0.12a-failure.txt`;
2. then the measured defect (74 rows read with no credential) and what changed where;
3. then one `Regression: <node or script CASE> -- failed at <batch-2 base sha> with <text>` line per RED test;
4. one `Flipped: <node> -- <old expectation> was wrong because <why>` line per flip (from `<scratch>/13-flips.txt`);
5. `BUGS.md: "The served app has no credential, so any local account can open a session and read the data" (closed)`.

There is no `Fixture:` line. Run Stata only through `"$WT"/scripts/stata_slot.sh <scratch> <file>.do` with `dash_nobrowser=1`, and cscripts only through the driver of "Stata truth". Run git as `git -C "$WT"`. No AI references anywhere.

<task type="auto" id="13-01">
  <name>Check the base and measure impact</name>
  <files>none</files>
  <action><![CDATA[
    Check the base, then measure impact:
    1. Record `git -C "$WT" rev-parse HEAD` in `<scratch>/13-base.txt`. It must equal `<scratch>/batch-2-base.txt`.
    2. Check that S08 is on the tree. Each of these must print at least 1:
       - `grep -c "def _dash_private_write\|def _dash_private_run_of\|def _dash_watch_parent\|def _dash_stop_child\|def _dash_erase_quietly\|def _dash_private_msg" "$WT"/dash_render.py`;
       - `grep -c -- "--parent-watch" "$WT"/dash_render.py`;
       - `grep -c "def _url" "$WT"/test/test_serve_lifecycle.py`;
       - `grep -c "LC-04 PASS" "$WT"/test/test_serve_launch.cscript`.

       If any prints 0, STOP and report: this section's design depends on S08.
    3. Check that S01 is on the tree: `grep -n '"P0.12a"' "$WT"/test/test_tracking_documents.py` and `grep -c "<!-- WP-29 P0.12a -->" "$WT"/CHANGELOG.md`, which must print 2.
    4. Run `(cd "$WT" && gitnexus analyze)`. Then `git -C "$WT" status --porcelain`; restore `CLAUDE.md` and `AGENTS.md` with `git -C "$WT" checkout -- CLAUDE.md AGENTS.md` if changed. Never stage `.gitnexus/`.
    5. Run `gitnexus_impact({target, direction: "upstream"})` for `_dash_launch_app`, `_glyph_layer_lines`, `_generate_app_source` and `_dash_build`. Use `gitnexus_context` to disambiguate; for a Stata program the index cannot resolve, use `grep -n` callers.
    6. Write each target's direct callers, affected processes and risk level to `<scratch>/13-impact.txt`.
    7. (Round 2, answer B; L-2, L-5.) Read S08's launch in `_dash_launch_app` on the tree: TR-08.8a and TR-08.14 as amended in round 2. Write to `<scratch>/13-launch.txt`:
       - how the app text reaches the child: `stdin` or another handle;
       - the child-side code that reads it.
       If the text goes over stdin and the child reads it through `sys.stdin` or `sys.stdin.buffer` rather than `os.read` on descriptor 0 to the text's exact length, STOP and report "S08's bootstrap would swallow S13's key line (L-2)". If `_dash_launch_app` still runs `app_path` as the interpreter's script argument, or `_cmd` lacks `-P`, STOP and report "S08 round 2 (launch from an open file) is not on the base".
  ]]></action>
  <verify><![CDATA[`<scratch>/13-base.txt` equals `<scratch>/batch-2-base.txt`; every grep above printed the expected count; `<scratch>/13-impact.txt` has one block per target with a risk level; `<scratch>/13-launch.txt` names the route (`stdin` or `handle`) and the child's read; `git -C "$WT" status --porcelain` lists no modified tracked file.]]></verify>
  <done>The base was confirmed to carry S01 and S08, and the blast radius of every symbol this section edits was recorded.</done>
</task>

<task type="auto" id="13-02">
  <name>Copy the ratified decisions and verify the impact approval</name>
  <files>none</files>
  <action><![CDATA[
    The maintainer ratified this section's decisions on 01oct2026 (index "Decisions for maintainer ratification", step 0f), so this task no longer asks mid-batch. Before task 13-06:
    1. Copy the rows `S13 1-8` and `S13 (a)-(e)` of `<scratch>/wp29-ratified.txt`, verbatim, into `<scratch>/13-decisions.txt`: `grep '^| S13 1-8 |\|^| S13 (a)-(e) |' <scratch>/wp29-ratified.txt > <scratch>/13-decisions.txt`. The expected record, quoted from the ratification: answer 3, "Ensure that the token will never be missing.", strikes item (1) and replaces it with the app making its own key (K-1..K-8); items (2)-(8) and (a)-(e) are ratified as written.
    2. If either row is missing or reads "pending", STOP before any product edit and report "step 1 was broken: S13's ratified rows are missing from <scratch>/wp29-ratified.txt".
    3. If the recorded item (1) says anything other than struck in favour of a self-made key, STOP and report the difference: K-1..K-8, TR-13.8a and the "makes a key" tests were planned on that answer.
    3a. Copy round 2's record for this section verbatim, appending to `<scratch>/13-decisions.txt`: the row `S13 K-8` (`grep '^| S13 K-8 |' <scratch>/wp29-ratified.txt >> <scratch>/13-decisions.txt`), then the three answer lines A, B and C (`grep '^[ABC]\. ' <scratch>/wp29-ratified.txt >> <scratch>/13-decisions.txt`; 01oct2026: A "Print the URL once", B "Launch from open file", C "Commit them"). Copy nothing else of round 2. Row `S13 K-8` itself names `S13 1-8` and `S13 (a)-(e)`, which is why <verify> anchors its row checks at the line start.
       - If the `S13 K-8` row is missing or not struck (its last column does not begin `01oct2026 (round 2): struck`), STOP: K-9 and its tests were planned on that row being struck.
       - If A reads anything other than "Print the URL once", STOP: K-9 and its tests were planned on it.
    4. Verify that `<scratch>/batch-2-impact.txt` (index R8, step 2.0) records the maintainer's approval of every HIGH or CRITICAL target in `<scratch>/13-impact.txt` (index R8 expects `_dash_launch_app`). If a HIGH or CRITICAL target of `13-impact.txt` is missing there, STOP and report it with its callers and the exact edits TR-13.12 makes.
    Tasks 13-03 to 13-05 write tests only and may proceed meanwhile.
  ]]></action>
  <verify><![CDATA[`grep -c '^| S13 1-8 |\|^| S13 (a)-(e) |' <scratch>/13-decisions.txt` prints 2; `grep -c '^| S13 K-8 | .*| 01oct2026 (round 2): struck' <scratch>/13-decisions.txt` prints 1; `grep -c '^[ABC]\. ' <scratch>/13-decisions.txt` prints 3; `grep -ci "pending" <scratch>/13-decisions.txt` prints 0; `grep -ci "struck" <scratch>/13-decisions.txt` prints at least 1; `grep -c "Print the URL once" <scratch>/13-decisions.txt` prints at least 1; every HIGH/CRITICAL target named in `<scratch>/13-impact.txt` appears in `<scratch>/batch-2-impact.txt` with an approval.]]></verify>
  <done>The ratified rows, item (1) struck in favour of a self-made key and round 2's row `S13 K-8` struck for K-9 with answers A-C, were on record for this section, and every HIGH or CRITICAL target had its recorded approval before any product edit.</done>
</task>

<task type="auto" id="13-03">
  <name>Write the failing unit and in-process tests</name>
  <files>test/serve_token_probe.py, test/test_serve_token.py, test/test_resource_limits.py</files>
  <action><![CDATA[
    Write the helper module and the first test classes:
    1. Create `test/serve_token_probe.py` with:
       - a module docstring naming WP-29 P0.12a, the shared key and TOK-02;
       - `TEST_TOKEN`, `token_args` and `FakeStdin` exactly as TR-13.15;
       - `_status(url)` (urllib; HTTPError gives `e.code`);
       - `main(argv)` as TR-13.16;
       - `if __name__ == "__main__": raise SystemExit(main(sys.argv))`.

       Imports: os, re, sys at the top; urllib and bokeh inside `main`.
    2. Create `test/test_serve_token.py` with:
       - a module docstring naming P0.12a, the base measurement (`GET /` 200; `pull_session` read 74 rows of mpg with no credential) and the two gates;
       - `sys.path` inserts for the repo root and `test/`, as `test/test_value_labels_drawn.py:17-22` does;
       - the classes `TestTheTokenHelpers`, `TestTheSessionGate`, `TestTheGeneratedAppIsGated`, `TestTheAppResolvesItsToken` and `TestTheLauncherPassesTheToken`, with every test "TDD test stubs" names for them, exactly so.

       Every test that can make a `bokeh serve` key uses a fixture calling `serve_token_probe.drop_holder()` before and after, and sets `tempfile.tempdir` to a `tmp_path` folder (monkeypatch), so no link folder lands in the real temp directory and no key outlives its test (ratified 01oct2026).
    Build the in-process namespace with `test_adversarial_matrix._app_source(tmp_path, make_spec([...scatter mpg weight...]))` and `_load_app`, then set `ns["_DASH_SERVE_TOKEN"] = TEST_TOKEN` in the test itself; these explicit settings stay valid after 13-11 flips the helpers. Pass `arguments` to `_Req` explicitly, with a local `_req(args)` that builds `types.SimpleNamespace(remote_ip="10.0.0.1", headers={}, arguments=args)`. The launcher tests monkeypatch `subprocess.Popen` with a fake whose `stdin` is a `FakeStdin` and whose `poll` reads the link file it is told about.
    3. In `test/test_resource_limits.py`, extend `TestTheServedAppDefinesEveryNameItReads::test_no_function_in_the_app_reads_an_undefined_global`'s explicit tuple with `"_dash_token_auth"`, `"_dash_session_token_ok"`, `"_dash_open_tokenized"`, `"_dash_announce_key"`, `"_dash_bokeh_serve_key"`, `"_DASH_TOKEN_RE"`, `"_DASH_SERVE_TOKEN"` and `"_DASH_LINK_DIR"`.
    Do not touch any product file. Run `python3 -m pytest test/test_serve_token.py test/test_resource_limits.py -q -n0 -p no:cacheprovider -k "Token or token or DefinesEveryName" 2>&1 | tail -40` and keep the output for 13-05.
  ]]></action>
  <verify><![CDATA[No collection error; every test in these five classes fails except the GUARD `TestTheSessionGate::test_an_in_process_document_still_builds`; the helper tests fail with `AttributeError: module 'dash_render' has no attribute '_dash_...'`, and the gate tests fail because the unkeyed session is served (a Plot is found).]]></verify>
  <done>Every unit, in-process, app and launcher regression test existed and failed at the base for its recorded reason, with nothing committed.</done>
</task>

<task type="auto" id="13-04">
  <name>Write the failing live and claim tests</name>
  <files>test/test_serve_token.py, test/test_security_surface.py, test/test_adversarial_matrix.py</files>
  <action><![CDATA[
    Write the live and claim tests:
    1. Add `TestTheServedAppRequiresItsToken` and `TestBokehServeAlwaysHasAKey` to `test/test_serve_token.py`, every test `@pytest.mark.serve`, as "TDD test stubs" names them. Live apps run through `test_adversarial_matrix._LiveApp` and `test_server_serves._Served`.
       - Until 13-11 flips them, pass `env={"DASH_SERVE_TOKEN": TEST_TOKEN}` to `_LiveApp` explicitly, and use a local `_with_env(srv_cls, token)` wrapper for `_Served` that sets `os.environ` inside the `with` through `monkeypatch.setenv`.
       - Until 13-10 adds `allow_127` and `ready_path` to `_Served`, `TestBokehServeAlwaysHasAKey` starts `bokeh serve` through a local `_bs(app, port, env, extra)` context manager (the `_Served` command line plus `--allow-websocket-origin 127.0.0.1:<port>` when asked, readiness on `/static/js/bokeh.min.js`, SIGINT then `wait(15)` at exit, output kept in a list by a reader thread); 13-10 may switch it to `_Served` only if the tests stay byte-for-byte equivalent.
       - The forged-JWT and browser-path tests reuse `_LiveApp.session`'s raw handshake. Copy its frame reader into a local `_ws(port, origin, jwt)` helper, so the test does not depend on 13-11's refactor.
    2. In `test/test_security_surface.py`, add `TestServeBindsLoopbackByDefault::test_the_help_names_the_key_and_its_limits` and `TestTheGeneratedAppBindsLoopbackAtRuntime::test_every_server_gets_the_key_check`.
    3. In `test/test_adversarial_matrix.py`, add the `"served_session_token"` surface and its `_REQUIRED_SURFACES` name.
    Run them against the unmodified tree and append the output to the 13-03 output.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_serve_token.py test/test_security_surface.py test/test_adversarial_matrix.py -q -p no:cacheprovider -k "Token or token or key or Key or SURFACES or registry" 2>&1 | tail -30`:
- the live RED tests fail (for example `test_the_page_without_the_token_is_403`: `assert 200 == 403`);
- `test_health_and_static_stay_open` and the GUARD `TestBokehServeAlwaysHasAKey::test_with_the_origin_flag_the_link_opens_the_websocket` pass;
- the two help/provider claims fail;
- the registry meta-tests of `test_adversarial_matrix.py` (node collection and case display) pass.]]></verify>
  <done>Every live, help and registry regression test of this section existed and failed at the base, and the adversarial registry named the new surface.</done>
</task>

<task type="auto" id="13-05">
  <name>Write the failing certification cases</name>
  <files>test/test_serve_launch.cscript, test/test_server_rate_limit.py</files>
  <action><![CDATA[
    Write the certification cases and save the red evidence:
    0. In `test/test_server_rate_limit.py`, extend `TestTheLauncherFlags::test_the_launcher_help_lists_every_flag`'s flag list with `"--token-stdin"`, and run it: it fails at the base.
    1. In `test/test_serve_launch.cscript`, insert TOK-01..TOK-04 exactly as TR-13.16 specifies, before the `// SRV-19` banner and after LC-04, with a banner comment naming WP-29 P0.12a, the thread pattern (TD-3; S08's LC-03 and PF-08) and why the key stays in Python memory. Add `TOK-01..TOK-04` to the header comment's tests list.
       - Every result is copied out of `r()` on the next line (`cert_file_has` clobbers `r()`).
       - The thread calls no `sfi` function.
       - The listener is killed in the thread whatever happens, so a red run does not wait 60 s.
    2. Run the script through the driver of "Stata truth" against the unmodified product code, and read `<scratch>/run_test_serve_launch.log`. At the base TOK-01 fails first (no `a new key for each launch`).
    3. Comment out TOK-01's `assert` line in a scratch COPY of the script (never in `$WT`), run the copy, and record TOK-02's result lines, which must show `link=missing` and `root_without_key=200`.
    4. Write `<scratch>/13-P0.12a-failure.txt`: the pytest output of 13-03, 13-04 and step 0, then the TOK lines of both runs. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "TOK-0[1-4] PASS" <scratch>/run_test_serve_launch.log` prints 0; the log stops at TOK-01 with `assertion is false` and r(9); the scratch-copy run's result file holds `link=missing` and `stopped=1`; `<scratch>/13-P0.12a-failure.txt` exists and holds both.]]></verify>
  <done>The certification cases existed and failed at the base, a red run stopped its own server, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="13-06">
  <name>Add the key, gate and redaction helpers</name>
  <files>dash_render.py, test/function_test_map.py, test/test_private_files.py</files>
  <action><![CDATA[
    Add the helpers and register them:
    1. After `_dash_harden_origin_check` (2498-2517), add TR-13.1's fourteen constants and TR-13.2..TR-13.9's and TR-13.8a's functions, each with a docstring naming P0.12a and its threat (TR-13.8a's also name the 01oct2026 ratification):
       - `_dash_new_token`, `_dash_token_valid`, `_dash_token_matches`, `_dash_one_value`, `_dash_env_token`;
       - `_dash_ws_payload`, `_dash_request_token`, `_dash_token_auth`, `_dash_session_token_ok`;
       - `_dash_redact_query`, `_dash_redact_access_record`, `_dash_install_access_log_redaction`;
       - `_dash_tokenized_url` (with `path`), `_dash_redirect_page`, `_dash_open_tokenized`, `_dash_read_token_line`;
       - `_dash_private_page`, `_dash_announce_key`, `_dash_process_key`, `_dash_bokeh_serve_key` (TR-13.8a).

       Imports of `hmac`, `base64`, `zlib`, `errno`, `stat`, `shutil`, `types`, `atexit`, `urllib.parse`, `tempfile`, `webbrowser`, `pathlib`, `ipaddress`, `bokeh.server.auth_provider`, `bokeh.util.token` and `tornado.web` are local to the functions that use them.
    2. Apply TR-13.11's copy-list entries in `ServerAppBuilder._glyph_layer_lines`.
    3. Add TR-13.17's `function_test_map.py` entries for these functions (`_dash_write_link` and `app:_dash_resolve_token` come in 13-07/13-08).
    4. **Flip S08's guard in place (R7; index override "Served app writes").** TR-13.8a's functions, now copied into the app, write a file, so `test/test_private_files.py::TestTheServedAppWritesNoFile::test_the_generated_app_has_no_file_writing_call` turns red at this task. Edit that test in place (no new test, no deletion):
       - Its AST scan keeps S08's write family unchanged (a write-mode `open(`, `os.open`, `write_text`/`write_bytes`, `tempfile.` and `shutil.` calls, and `os.fdopen` in a write mode if the scan counts it), and now records each hit with its scope: the enclosing `def`'s name, or `__main__` for the body of `if __name__ == '__main__':`.
       - It passes only when every hit is in this allowlist, and fails naming any other hit:
         - in `_dash_private_page`: the one `tempfile.mkdtemp(prefix=prefix)`, the one `os.open(...)` whose flags hold `O_CREAT`, `O_EXCL` and `O_NOFOLLOW` and whose mode is `0o600`, its `os.fdopen(fd, "w", ...)` write, and `shutil.rmtree(d, True)` on failure;
         - in `_dash_bokeh_serve_key`: `shutil.rmtree` passed to `atexit.register` with first argument `d`;
         - in `__main__` (TR-13.10 item 7, added by 13-07): `shutil.rmtree` (spelled `_shutil`), called or passed to `_server.io_loop.call_later`, with first argument `_dash_open_dir` or `_DASH_LINK_DIR`.
       - It also asserts that the four `_dash_private_page` entries are found, so a scan that misses them fails instead of passing vacuously.
       - Every other write, in any scope (another `open(` in a write mode, `os.open`, `write_text`/`write_bytes`, `tempfile.` or `shutil.` call), still fails it.
       - Append to `<scratch>/13-flips.txt`: `Flipped: test/test_private_files.py::TestTheServedAppWritesNoFile::test_the_generated_app_has_no_file_writing_call -- "the served app writes no file" was wrong because the ratified answer 3 (01oct2026) makes an app started without a key write its own 0600 link.html; the guard now admits only _dash_private_page's writes and the removal of the folders it makes`.
  ]]></action>
  <verify><![CDATA[Checks:
- `python3 -m pytest test/test_serve_token.py -q -n0 -p no:cacheprovider -k TestTheTokenHelpers` passes;
- `python3 -m pytest test/test_private_files.py -q -n0 -k WritesNoFile` passes, and `grep -c "test_the_generated_app_has_no_file_writing_call" <scratch>/13-flips.txt` prints 1;
- `python3 -c "import sys; sys.path.insert(0,'$WT'); import dash_render; print('tornado' in sys.modules, '_dash_serve_key' in sys.modules)"` prints `False False` (importing dash_render makes no key);
- `python3 -m pytest test/test_statistical_helpers.py test/test_resource_limits.py -q -p no:cacheprovider -k "CarriesEveryName or DefinesEveryNameItReads"` shows only the 13-03 tuple's app globals `_DASH_SERVE_TOKEN` and `_DASH_LINK_DIR` still missing (13-07 adds them).]]></verify>
  <done>The key, gate, redaction, URL and opener helpers existed in dash_render.py without importing tornado at module load, were copied into the app, and their unit tests passed; S08's no-file-writing guard was flipped in place to admit only `_dash_private_page`'s writes and the removal of its folders, and stayed green.</done>
</task>

<task type="auto" id="13-07">
  <name>Gate the emitted app with the key</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-13.10 in `ServerAppBuilder._generate_app_source` on S08's text:
    1. the `_DASH_SERVE_TOKEN = None` and `_DASH_LINK_DIR = None` globals;
    2. the `--token-stdin` flag;
    3. `_dash_resolve_token`, returning the supplied key or None (it makes no key);
    4. Gate B in `make_document`, after `_dash_reset_notes()` and before the rate-limit block, with `_dash_bokeh_serve_key(doc)` as the last alternative of its key expression;
    5. `_dash_server_app(..., token=None)` with the `global` line, `_dash_made`, the resolution and `auth_provider=`. It also gets the announcement, whose print-once fallback lives in `_dash_announce_key` (K-9, round 2), and the stop-and-raise for an address no link can name (K-2);
    6. the module-level `_dash_install_access_log_redaction()` before the curdoc attach;
    7. the `__main__` changes: the resolve with `_p.error`, the reworded `*` warning, `token=` inside the `try`/`except RuntimeError` → `_p.error`, the opener with `call_later`, the banner keeping `Bokeh Server running at` and `flush=True` with no link print, and both `rmtree`s (`_dash_open_dir`, `_DASH_LINK_DIR`) in S08's `finally`.
    Keep every S08 line (`--parent-watch`, `_dash_watch_parent`, `_dash_int`, exit 130) and its order. Add `app:_dash_resolve_token` to `test/function_test_map.py` and repoint `app:_dash_server_app` to `test/test_serve_token.py::TestTheGeneratedAppIsGated::test_every_server_the_app_builds_has_the_token_provider`.
  ]]></action>
  <verify><![CDATA[Checks:
- `python3 -m pytest test/test_serve_token.py -q -p no:cacheprovider -k "TestTheSessionGate or TestTheGeneratedAppIsGated or TestTheAppResolvesItsToken or TestTheServedAppRequiresItsToken or TestBokehServeAlwaysHasAKey"` passes;
- `ls "${TMPDIR:-/tmp}" | grep -c "^dash-link-"` prints the same count before and after that run (no test leaves a link folder);
- `python3 -m pytest test/test_resource_limits.py test/test_statistical_helpers.py -q -p no:cacheprovider -k "DefinesEveryNameItReads or CarriesEveryName"` passes;
- `python3 -m pytest test/test_serve_lifecycle.py -q -p no:cacheprovider -k "ParentWatch or WatchesStdin or AppBanner"` passes (S08's watch and banner untouched);
- `python3 -m pytest test/test_private_files.py -q -n0 -k WritesNoFile` still passes (the `__main__` removals are in 13-06's allowlist).]]></verify>
  <done>Every Server the app builds required the key, a start with no key made one and announced only its private link file, every session without the key got only the refusal page before the limiter and the data, and S08's watch, banner and Break exit still held.</done>
</task>

<task type="auto" id="13-08">
  <name>Hand the key over from the launcher</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-13.12 to `_dash_launch_app` on S08's text:
    - `link_dir=None`;
    - the key;
    - `--token-stdin`;
    - the key line written as bytes right after S08's app-text hand-over inside S08's Popen-to-final-wait `try:`, with the pipe kept open (L-1..L-3, round 2);
    - the `urllib.error.HTTPError` 429 branch inside the `/health` try, with `poll()` still outside;
    - `_dash_write_link` (returning `(path, folder)`, with K-8's privacy check and its fallback on a refused or failed run-folder write), the three ready lines (line 2 is `_DASH_LINK_SAID`) and K-9's print-once fallback when no folder takes the link (round 2; no RuntimeError);
    - redaction of forwarded lines and of the stderr tail;
    - the `finally` cleanup.
    Then:
    1. Add `_dash_write_link` beside the launcher, as TR-13.12 item 9.
    2. Pass `link_dir=_dash_private_run_of(args.output)` in the renderer `__main__`'s launch call, and extend the `--launch` help text.
    3. Add `_dash_write_link` to `test/function_test_map.py`.
    4. Run `python3 scripts/fncov/fncov_mutate.py --map --keys` with every key TR-13.17 added, and record any key whose test survived in `<scratch>/13-mutate.txt`; a survivor needs a stronger test before 13-16.
  ]]></action>
  <verify><![CDATA[Checks:
- `python3 -m pytest test/test_serve_token.py -q -p no:cacheprovider` passes;
- `grep -c "http://localhost:%d" "$WT"/dash_render.py` prints 0;
- `python3 -m pytest test/test_serve_token.py -q -n0 -p no:cacheprovider -k "test_a_link_file_that_cannot_be_private_moves_to_a_private_folder or test_a_link_no_folder_can_keep_private_is_written_with_a_note or test_a_run_folder_that_refuses_the_link_moves_it_to_a_private_folder or test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served or test_dash_serve_prints_an_unwritable_link_once_and_keeps_serving or test_the_token_goes_to_stdin_not_argv"` passes;
- `grep -c "its link could not be written privately" "$WT"/dash_render.py` prints 0, `grep -c "was stopped: its link was not written" "$WT"/dash_render.py` prints 0 (round 2), and AC-13.7's greps hold;
- `<scratch>/13-mutate.txt` lists no surviving key.]]></verify>
  <done>dash serve's launcher handed the key to the app on its open stdin pipe, after S08's app text. It wrote the link to a 0600 file, or moved it to a fresh private folder when the run folder refused it or could not hold 0600, and wrote it there with one note when no folder could hold 0600; it was never refused for privacy. It printed only the file's path, or, when no folder took the file, a warning and the link once, and it kept serving. It treated 429 as answering and redacted everything it forwarded.</done>
</task>

<task type="auto" id="13-09">
  <name>Flip the launcher fakes</name>
  <files>test/test_serve_launcher.py, test/test_help_claims_2.py, test/test_resource_limits.py</files>
  <action><![CDATA[
    Flip the fakes:
    1. Give every fake child a writable stdin:
       - in `test/test_serve_launcher.py`, `_fake_popen_class` (:99-131) and the inline `_FakeProc` classes (:241-305) get `self.stdin = FakeStdin()`;
       - so does `test/test_help_claims_2.py::_FakeProc` (:765-790).

       S08 commit 1 already gives these fakes `_RecStdin` (bytes `write`, `flush`, `close`, no `buffer`); replace it with `FakeStdin()`, recorded as `Adjusted:`. Import `FakeStdin` from `serve_token_probe`.
    2. Flip the ready-line needle (`test_serve_launcher.py:276`) to `dash: the server answers at http://127.0.0.1:%d/`, and add an assertion that the next printed line names `link.html`.
    3. In `test/test_resource_limits.py`, confirm that `_Proc` (:1359-1366) is never constructed (port refusal) and leave it unchanged.
    4. Record each flip as a `Flipped:` line in `<scratch>/13-flips.txt`. For example: `Flipped: test/test_serve_launcher.py::...::test_health_ready_line_once -- the localhost ready line was wrong because a localhost link reaches an IPv6 squatter and the dashboard now needs its key (P0.12a)`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_serve_launcher.py test/test_help_claims_2.py test/test_resource_limits.py -q -p no:cacheprovider` passes; `<scratch>/13-flips.txt` has one line per changed assertion.]]></verify>
  <done>Every launcher fake accepted the key on stdin, the ready-line pin named 127.0.0.1 and the link file, and each flip was recorded.</done>
</task>

<task type="auto" id="13-10">
  <name>Flip the live server helpers</name>
  <files>test/test_server_serves.py, test/test_csp.py, test/test_serve_lifecycle.py</files>
  <action><![CDATA[
    Apply TR-13.15 to the live helpers:
    1. In `test/test_server_serves.py`, make `_Launched`, `_Served` and `_pull` key-aware, and flip `TestTheLauncherOpensNoBrowser::test_show_is_opt_in` to look for `_dash_open_tokenized(` with `_a.show` within 400 characters before it.
    2. In `test/test_csp.py`, `TestThePythonLauncherServes::test_the_websocket_still_opens` pulls with `arguments=token_args()`. `_fetch` keeps using `srv.url(path)`, which now carries the key.
    3. In `test/test_serve_lifecycle.py` (S08's):
       - `_url(port, path, token=None)` and `_token_in(rundir)`;
       - every fake child gets `FakeStdin`;
       - every real-server test that GETs `/` or pulls a session passes the key read from `rundir/link.html`;
       - run `grep -n "listdir\|== \[\]\|not os.listdir" test/test_serve_lifecycle.py`, and flip any assertion that the run folder is empty while the server runs to Q-3's form (only `link.html`, 0600, holding none of the three data needles).
    Record every flip in `<scratch>/13-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_server_serves.py test/test_csp.py test/test_serve_lifecycle.py test/test_served_bs_layout.py -q -p no:cacheprovider` passes, with no new skip.]]></verify>
  <done>Every live helper carried the test key, S08's lifecycle tests accepted the link file, and the websocket, page and bokeh serve tests passed under the gates.</done>
</task>

<task type="auto" id="13-11">
  <name>Flip the in-process session fakes</name>
  <files>test/test_adversarial_matrix.py, test/test_server_rate_limit.py, test/test_server.py</files>
  <action><![CDATA[
    Apply TR-13.15 to the in-process fakes:
    1. In `test/test_adversarial_matrix.py`:
       - `_Req` gains `arguments`, and `_load_app` sets `_DASH_SERVE_TOKEN`;
       - `_LiveApp` gains the variable (None removes it) and `session(origin, jwt=None)`;
       - flip `TestSessionOrigin::test_a_star_in_the_environment_is_warned_of` to `"the websocket origin check admits every web site"`;
       - rewrite the module docstring's "What the three categories mean" paragraph: the served app now has one credential, the per-launch key, and "auth bypass" includes getting past it. Keep the rule-19 standing note, reworded: still no accounts or administrators.
    2. In `test/test_server_rate_limit.py`, `_Req` gains `arguments`, and every fixture that execs the app sets `ns["_DASH_SERVE_TOKEN"] = TEST_TOKEN`.
    3. In `test/test_server.py` (:4425-4505), the two `_FakeSessionContext.request` classes gain `arguments = token_args()`, and the namespace gains `_DASH_SERVE_TOKEN`.
    `test/test_serve_token.py` keeps its explicit keys and environment from 13-03/13-04; they stay valid under the flipped helpers. Record every flip.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_adversarial_matrix.py test/test_server_rate_limit.py test/test_server.py test/test_serve_token.py -q -p no:cacheprovider` passes; the registry meta-tests of `test_adversarial_matrix.py` pass.]]></verify>
  <done>Every in-process session fake carried the key, the live adversarial helpers ran keyed, the origin warning pin said what is now true, and the registry docstring no longer claimed dash has no authentication.</done>
</task>

<task type="auto" id="13-12">
  <name>Flip the help-claim and serve cscript pins</name>
  <files>test/test_help_claims_4.py, test/test_help_claims_4.cscript, test/test_e2e_serve.cscript</files>
  <action><![CDATA[
    Flip the pins:
    1. In `test/test_help_claims_4.py`:
       - `TestTheLauncherServes::test_a_client_that_sends_no_origin_is_admitted` gets a second half: an unkeyed pull raises OSError;
       - `::test_a_refused_session_gets_the_refusal_page` uses the keyed `srv.get("/")` and `pull_session(..., arguments=token_args())`;
       - `TestTheLauncherOpensABrowserOnlyWhenAsked::test_show_and_timeout` becomes what Evidence §4 states (set `BROWSER=x` with monkeypatch and record `webbrowser.open`; `call_later` records a list);
       - `TestUnderBokehServe::test_the_session_limits_do_not_hold` sets `DASH_SERVE_TOKEN` for the CodeHandler half.
    2. In `test/test_help_claims_4.cscript`, flip LC-01 to Q-3's form: the run folder holds only `link.html`, mode 0600, holding none of `_DATA_B64 = `, `"graphs":`, `"variableNames"`.
    3. In `test/test_e2e_serve.cscript` P4-82 (:289-300), record `type(_p482kw.get("auth_provider")).__name__` into a second global and assert it equals `_DashTokenAuth` before the PASS line.
    Run both cscripts through the driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_4.py -q -p no:cacheprovider` passes; `grep -c "LC-01 PASS" <scratch>/run_test_help_claims_4.log` prints 1 and that log ends with no `r(` error; `grep -c "P4-82 PASS" <scratch>/run_test_e2e_serve.log` prints 1.]]></verify>
  <done>The help-claim tests pinned the keyed behaviour, LC-01 allowed only the private link file, and P4-82 asserted the key check on the launcher's Server.</done>
</task>

<task type="auto" id="13-13">
  <name>Document the key in dash.ado and help</name>
  <files>dash.ado, dash.sthlp, test/program_coverage_map.py</files>
  <action><![CDATA[
    Document the key:
    1. Apply TR-13.13 (the one `Access:` display line in `_dash_build`'s server branch).
    2. Apply TR-13.14's nine edits to dash.sthlp, located by their quoted text. Keep S08's sentences, and edit no other paragraph (R3).
    3. Run `grep -n "only this machine\|There is no password\|single-user tool\|any website open a session\|the app prints the link\|every session gets a page saying so" dash.sthlp`, which must print nothing (the last two are the design's wording the 01oct2026 ratification removed). Run `grep -c "prints a warning line and then the link itself" dash.sthlp`, which must print 3 (round 2, TR-13.14 items 2-4).
    4. Run `grep -rn "Ctrl+C\|localhost" test/test_help_claims_*.py test/test_security_surface.py test/test_csp.py | grep -i "server_mode\|serve"`, and update any pin of a sentence this task changed.
    5. Add TR-13.17's two `program_coverage_map.py` references.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_security_surface.py test/test_csp.py test/test_toolbar.py test/test_help_conformance.py test/test_help_claims_1.py test/test_help_claims_4.py test/test_program_coverage_map.py test/test_file_headers.py -q -p no:cacheprovider` passes; `grep -c "DASH_SERVE_TOKEN" dash.sthlp` prints at least 3; `grep -c "link.html" dash.sthlp` prints at least 2; `grep -c -- "--allow-websocket-origin 127.0.0.1" dash.sthlp` prints at least 1.]]></verify>
  <done>dash build, server named the per-launch key, the help stated who can open the dashboard and where the key lives with no stale claim left, and the coverage map named TOK-01 and TOK-02.</done>
</task>

<task type="auto" id="13-14">
  <name>Turn the certification cases green</name>
  <files>none</files>
  <action><![CDATA[
    Run through the driver, one at a time, reading each log before the next:
    - `test_serve_launch.cscript`;
    - `test_help_claims_4.cscript`;
    - `test_e2e_serve.cscript`;
    - `test_serve_browser.cscript`;
    - `test_server_build.cscript`;
    - `test_adversarial.cscript`.
    A failure in a case this section did not list is a regression of this section: fix the code, not the case. If TOK-02's result file holds `pull_with_key_error=<type>` instead of `pull_with_key_rows=74`, read that exception type and the probe's stderr (the thread appends it as `probe_stderr=<last 300 characters, newlines removed>`), fix the cause, and rerun the script through the driver. Never run Stata other than through `"$WT"/scripts/stata_slot.sh`.
  ]]></action>
  <verify><![CDATA[Checks:
- `grep -c "TOK-0[1-4] PASS" <scratch>/run_test_serve_launch.log` prints 4 and the log ends `All dash serve option tests PASSED.`;
- each of the other five logs has no `r(` error line and no SKIP;
- `grep -cE "\?token=[A-Za-z0-9_-]{32,}" <scratch>/run_test_serve_launch.log` prints 0.]]></verify>
  <done>Stata certified that a real dash serve refused every request without the key, served all 74 rows with it, kept the link in a 0600 file in a 0700 folder, and wrote the key into no log.</done>
</task>

<task type="auto" id="13-15">
  <name>Run the changed files and registries</name>
  <files>none</files>
  <action><![CDATA[
    First record `ls "$(python3 -c 'import tempfile;print(tempfile.gettempdir())')" | grep -c '^dash-link-'` in `<scratch>/13-linkdirs-before.txt`. Then run, as changed-file runs (rule 11):
    - `python3 -m pytest test/test_serve_token.py test/test_server_serves.py test/test_csp.py test/test_adversarial_matrix.py test/test_server_rate_limit.py test/test_server.py test/test_serve_launcher.py test/test_help_claims_2.py test/test_help_claims_4.py test/test_serve_lifecycle.py test/test_security_surface.py test/test_resource_limits.py test/test_private_files.py test/test_served_bs_layout.py -q -p no:cacheprovider`;
    - the R2 registry tests: `test/test_function_test_map.py`, `test/test_program_coverage_map.py`, `test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` and `test/test_cscript_hygiene.py`;
    - the guards `test/test_mode_parity.py` and `test/test_export.py`.
    Any failure outside the listed flips is fixed in code, or flipped only with a `Flipped:` line and its reason.
  ]]></action>
  <verify><![CDATA[Every command reports 0 failed and no new skip; `git -C "$WT" diff --stat` lists only this section's files; `ls "$(python3 -c 'import tempfile;print(tempfile.gettempdir())')" | grep -c '^dash-link-'` prints the count recorded before the first command (no test left a self-made key's link folder).]]></verify>
  <done>Every changed test file, every registry test and the parity guard passed on the section's tree.</done>
</task>

<task type="auto" id="13-16">
  <name>Close P0.12a and commit once</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Close the entry, run the suite and commit:
    1. In BUGS.md, find `- [ ] Title: The served app has no credential, so any local account can open a session and read the data` (S01's open entry). Change it to `- [x]` in place, keep the other fields, and rewrite its Resolution:
       - It starts `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.12a).`.
       - It names `_dash_token_auth` (Gate A, 403 before any handler), `_dash_session_token_ok` in `make_document` (Gate B, before the limiter and the data; the only gate under bokeh serve, where a start without DASH_SERVE_TOKEN makes its own key at the first session (_dash_process_key, _dash_bokeh_serve_key)), `_dash_new_token` (secrets, 256 bits), `_dash_token_valid`, `_dash_token_matches` (hmac.compare_digest), `_dash_ws_payload` (bounded), the `--token-stdin` handover on S08's pipe, `_dash_write_link` (0600 link.html in the run folder, or a fresh private folder when the run folder cannot hold 0600, or, where no folder can, that file written with one dash: note: naming it, as ratified 01oct2026; path printed, key never printed; where no file can be written at all, the link printed once after a warning line while the server keeps serving, as ratified 01oct2026 round 2), the self-made key of a start given none (`_dash_server_app` before any session under python app.py; `_dash_process_key` and `_dash_bokeh_serve_key` at the first session under bokeh serve; its link written by `_dash_announce_key` through `_dash_private_page`, 0600 in a fresh 0700 folder, only the path printed), `_dash_open_tokenized` (no key in argv), `_dash_tokenized_url` (127.0.0.1) and the redaction (`_dash_redact_query`, `_dash_install_access_log_redaction`).
       - It is pinned by `test/test_serve_token.py::TestTheServedAppRequiresItsToken::test_a_session_without_the_token_reads_no_rows`, `test/test_serve_token.py::TestTheServedAppRequiresItsToken::test_the_page_without_the_token_is_403`, `test/test_serve_token.py::TestBokehServeAlwaysHasAKey::test_without_the_env_the_app_makes_a_key_and_announces_it`, `test/test_serve_token.py::TestTheServedAppRequiresItsToken::test_a_keyless_start_makes_a_key_and_a_private_link`, `test/test_serve_token.py::TestTheSessionGate::test_a_session_without_the_token_gets_only_the_refusal`, `test/test_serve_token.py::TestTheSessionGate::test_no_configured_token_makes_one_and_still_refuses`, `test/test_serve_launch.cscript TOK-02`.
       - It ends `Residual, deferred (WP-29): ` listing: (1) Linux and Windows hosts are not measured (the redirect-file opener under a snap-confined browser; the stdin pipe on Windows); (2) under a hand-run `python app.py` each refused request logs one redacted WARNING line, with no throttle; (3) under bokeh serve only Gate B applies, so /autoload.js and /metadata answer 200 with the refusal page and no data; (4) a keyless websocket attempt may inflate up to 262,144 bytes before refusal; (5) under bokeh serve without DASH_SERVE_TOKEN the self-made link names no --prefix, waits for the first page request when the first session came over a websocket, cannot be made under --unix-socket or a port under 1024 (one line says so; every session stays refused), and its page stays blank unless the server was started with --allow-websocket-origin 127.0.0.1:<port> (the app prints that hint); (6) a link folder made for a self-made key outlives a hard kill (SIGKILL) of its process, holding a key that no longer opens anything; (7) on a disk that keeps no file permissions the link file holding the key is written anyway, readable by other accounts while the server runs, with one dash: note: naming it (ratified 01oct2026: no privacy condition is refused); (8) when no link file can be written anywhere, the link and its key are printed once, after a warning line, to the output of whoever started the server, and so into Stata's Results and any open Stata log under dash serve (batch logs are 0644), readable by whoever can read that output while the server runs (ratified 01oct2026 round 2, "Print the URL once").
    2. Delete the `"P0.12a": ...` line from `WP29_OPEN` in `test/test_tracking_documents.py`.
    3. In CHANGELOG.md, replace `<!-- WP-29 P0.12a -->` at the end of `### Security` with the line in Notes "CHANGELOG text (Security)". Replace the marker at the end of `### Changed behaviour (may need your do-files changed)` with the line in Notes "CHANGELOG text (Changed behaviour)". Locate each by its heading, never by first match.
    4. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Then run the section's ONE full run, `python3 -m pytest test/ -q`, in the worktree. Read its log and never launch a second. A failure is fixed in code or flipped with a `Flipped:` line, and only the failed file is rerun.
    5. Run `gitnexus_detect_changes()`. Check that `git -C "$WT" diff --cached --name-only` stages exactly the files of this section's header list, and no `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.gitnexus/` or `*.html`.
    6. Write the message to `<scratch>/13-commit-msg.txt` in the Commit boundary form. Run `grep -Ei 'claude|anthropic' <scratch>/13-commit-msg.txt` (it must print nothing), then `git -C "$WT" commit -F <scratch>/13-commit-msg.txt`, then grep `git -C "$WT" log -1 --format=%B` again.
  ]]></action>
  <verify><![CDATA[Checks:
- the full suite's tail reports 0 failed and no new skip;
- `grep -c '<!-- WP-29 P0.12a -->' CHANGELOG.md` prints 0 and `grep -c '(WP-29, P0.12a)' CHANGELOG.md` prints 2;
- `grep -c '(WP-29, P0.12a)' BUGS.md` prints 1;
- `python3 -m pytest test/test_tracking_documents.py -q -n0` passes;
- `git -C "$WT" log -1 --format=%s | grep -c '(WP-29 P0.12a)$'` prints 1 and `git -C "$WT" log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0.]]></verify>
  <done>P0.12a was closed in BUGS.md naming existing tests, both CHANGELOG markers were replaced, its WP29_OPEN key was gone, and one green commit on wp29-s13 carried the whole section.</done>
</task>

## Section completion criteria

- **Live, without the key.** Under `python app.py` and `dash serve`, every page, session, `/autoload.js`, `/metadata` and websocket request without the key gets 403, with dash's headers and a constant reason. No row is sent, and no session budget is spent. Under `bokeh serve`, every session without the key gets only the refusal page, which says where the link is and names `DASH_SERVE_TOKEN`.
- **Never without a key (ratified 01oct2026).** A start given no key makes one (43 characters) before any session is admitted, writes its link to a 0600 `link.html` in a fresh 0700 folder, prints only that path, and removes the folder at stop; a set but invalid key is refused. Pinned live under `python app.py` and `bokeh serve` and in process (AC-13.6).
- **No folder takes the link (round 2).** The server keeps serving. Under `dash serve`, `python app.py` and `bokeh serve` the starter's output gets K-9's warning line and the link exactly once (per launch, per process, per app path), and no session prints it again (AC-13.7).
- **The key after the app text (round 2).** On S08's open-file launch, the key line follows S08's app text on the same stdin pipe, written through `_dash_child_stdin(proc)`, and TOK-02 passes through that route.
- **Live, with the key.** The dashboard is served unchanged, including to a client that sends no Origin. `/health` and `/static` stay open.
- **Where the key goes.** The key is new per launch, compared with `hmac.compare_digest`, and handed over stdin. It is absent from argv, the app file, every log and Stata's output, except K-9's warned once-only print. Every link names `127.0.0.1` (or `[::1]` for `::`, or an explicit address).
- **TOK-01..TOK-04 PASS** in Stata, and the full pytest suite is green.
- **Flips.** Every flipped test has a `Flipped:` line. No test was deleted, and the node count never fell (`pytest --collect-only -q | wc -l` before and after).
- **One commit** on `wp29-s13`, subject ending `(WP-29 P0.12a)`. It carries the BUGS.md entry closed in place, both markers replaced and `WP29_OPEN["P0.12a"]` gone.

## Notes

- **Line numbers** are 7421d3d's. S01-S09 (batch 1) and S10-S12 (batch 2, merged first) shift `dash_render.py`, `dash.ado` and `dash.sthlp`. Locate every site by its symbol and quoted text, and apply a rejected hunk by hand (R4).
- **S08 is the base of every launcher edit.** Read `_dash_launch_app`, the emitted `__main__`, `_dash_arg_parser`, `make_document`'s head and `_dash_server_app` on the tree before editing them. Keep:
  - the `Bokeh Server running at` prefix;
  - `--parent-watch` and the open stdin pipe;
  - `poll()` outside every broad `except`;
  - the one try/finally from Popen to the last wait.
- **The in-process exemption.** `make_document(Document())` and `make_document(curdoc())` outside a server have `session_context` None and are built. KF-03 (WP-28), S06's HX cases, `test_mode_parity` and every `exec` + `make_document(Document())` test rely on this. A server session always has a context (bokeh/server/contexts.py:211-233), so the exemption is no bypass.
- **Tests that start the app without a key (ratified 01oct2026).** `_dash_server_app` and `bokeh serve` sessions now make and announce a key whenever none is given, writing a `dash-link-*` folder. Every test that execs `__main__`, calls `_dash_server_app` or runs a `CodeHandler` session without a key either sets `DASH_SERVE_TOKEN=TEST_TOKEN` (monkeypatch), or sets `tempfile.tempdir` to its `tmp_path` and calls `serve_token_probe.drop_holder()` around it. Live tests that let the app make its key stop it with SIGINT so its `finally`/`atexit` removes the folder. 13-15 checks that no folder is left behind.
- **Section-08's Notes for S13 (reconciled; round 2).**
  - Round 1 took TR-13.12's failure text from those Notes: `"the server on port %d was stopped: its link was not written (%s)"`. Round 2 (answer A) strikes it, and no failure to write the link stops the server (K-9). Those Notes' round-1 sentence "stops the server only if that fails too" is superseded the same way; section-08's Notes for S13 now carry K-9's wording.
  - Their "check, Popen, then key" order becomes "open and verify, Popen, app text, then key" (L-1).
  - The rest of this item is unchanged. Their "allow exactly one `_dash_private_write(…, exclusive=True)` call", the four S08 helpers to copy and "print the R-8 note itself" are superseded by index override "Served app writes": the app copies none of S08's private-file helpers, writes only through `_dash_private_page` (13-06 step 4 flips the guard), and its only note is K-8's. The launcher (Stata's Python, not the app) still uses S08's `_dash_private_write(…, exclusive=True)` in the run folder.
- **Answer B and S13 (round 2).** S08 owns the open-file launch: the descriptor, the verification, the hand-over, the child's bootstrap, and its command-line pins and swap tests. S13 owns only the key line's place on the pipe (L-1..L-5). S13 rewrites no S08 test.
- **Answer C (round 2).** The plan is committed on `wp29-p0`, so `$WT` holds this file at `.ultraplan/wp29/section-13-serve-token.md`. Its absolute path in the main checkout is equally valid.
- **Bytes and strings.** Tornado's `request.arguments` values are `list[bytes]`. The JWT payload's `arguments` come back through Bokeh's `_BytesDecoder`. `_dash_token_valid` and `_dash_token_matches` take both.
- **Shared registries.**
  - **R1:** TOK-01..TOK-04 is one contiguous run before SRV-19, after S08's LC-04. LC-01 is flipped in place. P4-82 is extended in place. No new script, and no runner or hygiene edit.
  - **R2:** copy-list entries as TR-13.11; map keys in alphabetical place; two coverage-map references.
  - **R3:** only TR-13.14's help sentences, only the P0.12a entry, markers and key.
  - **R7:** every flip in `<scratch>/13-flips.txt`.
  - **R8:** 13-01/13-02.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. `test_serve_launch.cscript` then exits 222, and a SKIP is not a pass: check `c(python_exec)` before trusting it.
- **Commit-body line forms.**
  - `Regression: test/test_serve_token.py::TestTheServedAppRequiresItsToken::test_the_page_without_the_token_is_403 -- failed at <base sha> with assert 200 == 403`
  - `Regression: test/test_serve_launch.cscript TOK-02 -- failed at <base sha> with link=missing, root_without_key=200`
  - `Flipped: ...` lines as recorded.
  - `BUGS.md: "The served app has no credential, so any local account can open a session and read the data" (closed)`.
- **CHANGELOG text (Security)** replaces the marker at the end of `### Security`:

  > The served app had no credential: while `dash serve`, `python app.py` or `bokeh serve app.py` ran, any program on the machine, under any local account, could open a session and read every row the dashboard draws (measured: `bokeh.client.pull_session`, with no credential and no Origin, received all 74 values of auto's `mpg`). The app now requires a key made new at every launch. Every page, session, /autoload.js and /metadata request without it is refused (403) before any data is read, and the key is compared in constant time. `dash serve` hands the key to the app over a pipe, never on a command line. It writes the link that holds it to a file only you can read, and opens that link at 127.0.0.1, never localhost, which another account can answer on ::1. The app never runs without a key: started by hand with none (`python app.py`, `bokeh serve app.py`), it makes its own and writes its link to a file only you can read, printing only that file's path. No Stata log and no server log holds the key, with one exception: when no file can be written anywhere to hold the link, dash prints the link once, after a warning that the key is now in that output and its log, and keeps serving. /health and BokehJS's static files stay open. (WP-29, P0.12a)

- **CHANGELOG text (Changed behaviour)** replaces the marker at the end of `### Changed behaviour (may need your do-files changed)`:

  > A served dashboard's address now needs its key: http://localhost:5006/, bookmarked or typed, answers 403. Open the link in the file `dash serve`, `python app.py` or `bokeh serve app.py` names (each prints the file's path, never the key), http://127.0.0.1:<port>/?token=<key>; under bokeh serve, start it with --allow-websocket-origin 127.0.0.1:<port> or the page stays blank. To choose the key, set DASH_SERVE_TOKEN (32 to 128 of A-Z a-z 0-9 _ -) and open /?token=<that value> (/app?token=<that value> under bokeh serve); the app then writes no link file. `python app.py` stops with exit status 2, and bokeh serve refuses every session, when DASH_SERVE_TOKEN holds anything else. If the link file cannot be written anywhere, the server is no longer stopped: the link is printed once, after a warning line, and the dashboard keeps serving. (WP-29, P0.12a)

### Notes for the closeout (S15; index A5: these documents are S15's alone)

- **GAPS2.md I3** (line 1641) is fully closed by S08 commit 1 (the files) and this section's commit (the credential and the help). Tracked: `Closed in WP-29, BUGS.md "The served app has no credential, so any local account can open a session and read the data", commit <S13 sha>; files: BUGS.md "<P0.12b title>", commit <S08 commit-1 sha>`. Its plan item 1's cookie was deliberately not used (RFC 6265 §8.5: cookies are not isolated by port), and its item 3's "relay the URL to the Stata log" was replaced by the 0600 link file (TD-2). Append `(WP-29, I3)` to this entry's Resolution only when I3 is marked Closed.
- **GAPS.md L10** (2417-2433): rewrite the standing note. dash now has one credential, the per-launch key of the served app. Rule 19 is still not applicable: there are no accounts, administrators or administrative components.
- **TWOWAY_COVERAGE_AUDIT.md** rows 162 and 183 (AUDIT-87): "No built-in authentication" and "It has no authentication" become "a per-launch key, which the app makes itself when it is given none (WP-29 P0.12a)". The "single-user tool" wording goes.
- **DROPIN-REMAINING.md P0.12:** annotate it with S08's commit 1 (files) and this commit (credential).
- **ROADMAP WP-29 `**GAPS2 closed:**`:** add I3 once both commits exist.
- **AGENTS.md invariant (S15.4):** "The served app admits nothing without its per-launch key (Gate A `_dash_token_auth`, Gate B `_dash_session_token_ok`); keys are compared with `hmac.compare_digest`; every link is 127.0.0.1; Stata never prints the key, except K-9's warned once-only print of the link when no link file can be written anywhere (round 2); the key line follows S08's app text on the launch pipe; the app never runs without a key: started with none, it makes one (`_dash_server_app`, or `_dash_bokeh_serve_key` under bokeh serve) and prints only the path of its 0600 link file". Tests: `test/test_serve_token.py::TestTheServedAppRequiresItsToken::test_the_page_without_the_token_is_403`, `test/test_serve_token.py::TestTheSessionGate::test_no_configured_token_makes_one_and_still_refuses`, `test/test_serve_token.py::TestTheLauncherPassesTheToken::test_a_link_that_cannot_be_written_anywhere_is_printed_once_and_served` and `test/test_serve_launch.cscript TOK-03`.
- **Residuals to list in S15.7:** the eight in the closed entry's Resolution (round 2 added the eighth, K-9's printed link).
- **Ratification record (S15):** decision S13 (1) was struck on 01oct2026 ("Ensure that the token will never be missing"); ROADMAP's WP-29 notes say the served app makes its own key when started without one, instead of refusing every session. Round 2 (01oct2026): "Print the URL once" struck K-8's stop: when no link file can be written anywhere, the link is printed once with a warning and the server keeps serving. "Launch from open file": `dash serve` runs the app text it verified (S08), and the key follows it on the pipe. "Commit them": the plan files are tracked.
