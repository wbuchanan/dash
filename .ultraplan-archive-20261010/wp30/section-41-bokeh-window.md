# Section 41: Verified bokeh window; internals fail closed (P1.30, M9/M10)

> Part of: WP-30 · Items: P1.30 (entry `P1.30`; GAPS2-H4b, H4c, H4d, H4e, GAPS2-I7-a, I7-b, GAPS2-K5-a, K5-b, K5-c) · Risk: yellow · Batch: 14 (merge order S39, S40, S41; S41 last) · Depends on: 04, 05, 06, 25 · Blocks: 46, 54 · Tasks: 20, 2 commits (the window, then the internals) · Case prefix: BK; HON-50..59

## Review amendments

- Fixed (major, rule 1): Q-41.1 is resolved by hardening. Under `bokeh serve` and bokeh 3.8, inside the window, Bokeh's lenient origin matcher stayed in force, which is the fail-open case register P1.30.9/A109 rules closed. TR-41.19's bokeh-serve branch now also calls `_dash_harden_origin_check()`, which is idempotent and runs before each session's websocket. A red-first test is added (`::test_bokeh_serve_hardens_the_origin_check`, 41-14's count 11 → 12). TR-41.18 entry 3, TR-41.20's help sentence, the CHANGELOG Security line, the BUGS residual, Boundaries and the closeout note are aligned.
- Checked at HEAD: `_dash_harden_origin_check` :3879 with its probe :3893-3896, the launcher's `if __name__ != '__main__':`/`make_document(curdoc())` :36412-36413 and its harden call :36477, and dash.sthlp :1688-1694 (the sentence TR-41.20 rewrites). The HON-5x and BK ids are free, and SVG-05 exists (test_setup_version_gate.cscript :79-85).
- Checked the batch boundary: S41 is batch 14's only editor of `main`, `_generate_app_source`, `_dash_served_template`, `_dash_harden_origin_check`, `_dash_token_auth`, `_dash_seal_saved_page`, `_dash_dep_versions`, dash_setup.ado and dash_setup_lib.py. S39 and S40 edit none of these, `_glyph_layer_lines` takes appends at three distinct R2 anchors, and the help paragraphs are disjoint (Server Mode and Dependencies).
- Checked the forms: two commits (A156) with "part 1 of 2"/"part 2 of 2" subjects; tasks 41-01..41-20 hold 1-3 files each, with past-tense done text and CDATA; 41-01 and 41-02/41-03 write and run red-first and never commit; the markers are Requirements and Security, as Appendix A gives P1.30; the stub header drops "(P1.30, M9/M10)".
- Rejected: "verify bokeh 3.10 after the code changes". TR-41.1 runs the leg first on the unmodified base, so commit 1 writes the final window once, and 41-19 re-runs commit 2's guards under 3.10.
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:164 (P1.30): "There is no bokeh ceiling and no run-time `bokeh.__version__` check. Text-sink XSS safety is verified only on 3.8 and 3.9. The setup gate never reports 'outside the verified range'. dash depends on Bokeh internals (`match_host`, `templates.FILE`)." GAPS2.md:1529 (H4, also I7) and :1861 (K5) are the sources. Measured at `c96facd` (research `.ultraplan/wp30/research/p1-30.md` §2, critic additions; re-measured for this file where marked):

```
pip index versions bokeh  (Stata's Python 3.13.9)  -> bokeh (3.10.0); 3.9.2 ... 3.8.0     # pip install "bokeh>=3.8" lands on 3.10.0
_dash_setup_gate bokeh <v> 3.8 1   3.9.2 / 3.10.0 / 3.10.0rc1 / 4.0.0 / 99.0 -> ok           # no ceiling, ever
dash scatter mpg weight, saving(m4.html)   with bokeh.__version__ = "3.10.0"  -> rc 0, no word
dash build, server saving(m4.py) nobrowser with bokeh.__version__ = "3.10.0"  -> rc 0, no word
dr.main(..., mode=standalone|server) under 3.7.3 / 3.10.0 / 4.0.0             -> 0 warnings
no-preamble FILE: served page holds a CSP meta: False, raised: nothing        # fails OPEN
no match_host: AttributeError module 'bokeh.server.util' has no attribute 'match_host'
```

**After this section**, in both modes:
- one declared window, `bokeh>=3.8,<3.10` (raised to `<3.11` only if task 41-01 verifies bokeh 3.10 in a scratch venv, M9/M10), is what `dash_setup` installs, in place and into a venv it creates; a Python or venv dash did not create is never downgraded, and its newer bokeh is reported "outside the verified range" as a warning, rc 0 (A105, A107);
- every `dash` command reads `bokeh.__version__`: below 3.8 it is refused r(198) naming `dash_setup` (S25's refusal slot), above the window it prints one `(note:  dash: bokeh … )` line through S06's channel and draws; the served app does the same at start under `python app.py` (exit status 1 below the floor) and `bokeh serve` (every session refused below the floor), noting once per process (M9, register P1.30.2, P1.30.8);
- "verified" means major.minor (A104); `VERIFIED_BOKEH` is the window, and every minor in it has a recorded browser check of the text sinks;
- if a Bokeh release changes an internal dash's security rests on (the template blocks the CSP and nonce ride in, the saved page's `<head>`, `match_host`/`check_allowlist`, the AuthProvider hook, the JWT layout Gate A reads), the server refuses to start, or the page is not written, with a named error (A109); `_DASH_BOKEH_INTERNALS` lists each internal with its guard and test, and S54 extends it.

**Why one section, two commits.** All of it is one entry (P1.30) and one window. Commit 1 (the window) is the version policy: constants, run-time check, `dash_setup`, requirements files, help. Commit 2 (internals fail closed) is the security line M9 relies on: guards in `_dash_served_template`, `_dash_harden_origin_check`, `_dash_token_auth`, the saved seal, and the internals list (A156).

**Test order and commit rule (rule 7, A156).** Two cycles on `wp30-s41`.
- **Commit 1 (the window):** 41-01 verifies bokeh 3.10 on the unmodified batch-14 base and fixes the ceiling in `$S/41-ceiling.txt` (no commit); 41-02 and 41-03 write every commit-1 regression test and run them against the unmodified base, saving `$S/41-P1.30-1-failure.txt` (no commit); 41-04 to 41-12 fix, flip and document; 41-13 runs the full suite and makes commit 1, leaving the BUGS.md entry, its `WP30_OPEN` key and both markers in place.
- **Commit 2 (internals fail closed):** 41-14 writes the commit-2 tests against the tree commit 1 left and saves `$S/41-P1.30-2-failure.txt`; 41-15 to 41-19 fix, document and re-run under bokeh 3.10 if verified; 41-20 closes the entry, deletes the key, replaces both markers and makes commit 2.

No test-only commit exists, and no commit is red.

**Ceiling notation.** Below, `3.10` in a ceiling (`<3.10`, "before 3.10") is the ceiling `C` that `$S/41-ceiling.txt` holds after 41-01. If it reads `3.11`, write `3.11` there, the verified list is `3.8, 3.9, 3.10` and `_DASH_BOKEH_VERIFIED` gains `(3, 10)`; nothing else changes.

## Risk: [yellow] — two HIGH generator symbols, a ceiling that changes what dash_setup installs, and guards that stop the server if written wrong

**Why.**
- `main` and `ServerAppBuilder._generate_app_source` are HIGH at the batch base (index 14.0; research §7 measured `_generate_app_source` HIGH, 5 impacted; `main` LOW 7 only with `-f dash_render.py`, UNKNOWN bare). `ServerAppBuilder._glyph_layer_lines` is HIGH (4).
- `_dash_served_template`, `_dash_harden_origin_check`, `_dash_token_auth` are UNKNOWN to the index: they are called from the generated app's text (grep: `_dash_served_template` in `make_document` :34724; `_dash_harden_origin_check` :36477; `_dash_token_auth` in the launcher's `Server(auth_provider=…)` :36488). `_dash_dep_versions` (S25) and `_dash_seal_saved_page` (S04) do not exist at `c96facd`; impact is taken at `batch-14-base` (E4).
- Every dash_setup.ado program and every `dash_setup_lib.py` function S41 edits is UNKNOWN (ado not indexed; `stata_venv`, `VERIFY_CODE` reached from the ado). Callers by grep: `_dash_setup_gate` 5× in dash_setup.ado plus test_setup_honesty (4), test_setup_injection (5), test_adversarial (1); `_dash_pip_command` 5× plus test_setup_honesty, test_setup_python_gate, test_version_floor; `_dash_setup_venv` once (dash_setup.ado:156).

**Risk factors.**
1. A template guard that renders the template on an empty context raises `UndefinedError: 'macros' is undefined` on the real FILE (critic C1): the server would never start.
2. A script-tag scan that counts the text `<script` inside a script body flags a signed page as unsigned (S04 risk 4) and stops every server.
3. A ceiling passed into a reused venv downgrades the user's bokeh (critic C5).
4. `dash serve` would print the note twice: once in Stata, once relayed from the child (critic C4).
5. Patching `bokeh.__version__` before `bokeh.resources` is imported breaks Bokeh (`Missing SRI hash`, research M4); tests must patch after import.
6. A wrong origin probe leaves a lenient matcher in place (critic C2): fails open.
7. The served copy loop skips a misspelt name silently (RK-9).

**Mitigation.**
1. The template guard checks `FILE.blocks` (both verified Bokehs list `preamble`, `js_resources`, `inner_body` among 12 blocks, measured below) and renders one probe page through `file_html` with server resources (3 ms, measured).
2. The scan walks script elements as S04's `_dash_nonce_scripts` does (opening tag, then skip to `</script`); a unit test holds `"<script>"` inside a body.
3. `dash_setup_lib.bokeh_requirement` drops the ceiling when the installed bokeh is at or above it; a reused venv is probed first.
4. The app's note text is `_dash_bokeh_check()`'s, the same function and version as `main()`'s, so S23's relay skips it through `said=` (a test asserts equality).
5. Every test and the truth block import `bokeh.embed`, `bokeh.resources`, `bokeh.plotting`, `bokeh.models`, `bokeh.server.server` first.
6. The origin guard asserts after hardening that `bokeh.server.util.check_allowlist` rejects the probe; Bokeh's websocket handler imports that name at call time (`bokeh/server/views/ws.py:107`, both versions), so the probe is the handler's own path.
7. G4 guards and `TestTheServedAppDefinesEveryNameItReads` run in 41-05 and 41-17.

## Dependencies

- **Depends on: 04, 05, 06, 25.**
  - S04 (batch 2): `_dash_served_template(nonce=None)` with `preamble`, `js_resources`, `inner_body` overrides; `_dash_new_nonce`, `_dash_nonce_scripts`, `_dash_csp_served`; `_dash_saved_head`, `_dash_seal_saved_page`, `DashScriptPolicyError`; `test_csp_browser.py` and its `_CspProbe`. S04 names "S41: the FILE-block guard (`preamble`, `js_resources`, `inner_body`) and the internals list" (section-04 :426).
  - S05 (batch 2): `test/requirements-stata.txt`, `test/requirements-dev.txt` (`name==version` lines under a `#` header; any other line refused by `TestTheRequirementsFiles`), six `_BASELINES` each with bokeh 3.8 or 3.9, `scripts/floor_matrix.sh` (its `fresh` leg already installs `bokeh>=3.8,<3.10`) (IR-16; section-05 :1054-1057).
  - S06 (batch 2): `_dash_emit_note`, `_dash_note_scope`; a `warnings.warn("dash: …")` inside `main()` prints once per command as `(note:  dash: …)` (section-06 :458).
  - S25 (batch 9): `_dash_dep_fail`, `_DASH_MIN_PACKAGES`, `_dash_dep_versions() -> (refusal, note)` whose refusal slot "S41 fills", read by `_dash_xm_load` on every load (TR-25.8); the app header's guarded imports end before S41's start-up check (section-25 :839).
  - Landed before and read here: S23 (the app note hook `_dash_app_note_hook`, holder `sys.modules["_dash_app_notes"]`, the relay's `said=`), S03 (`version 19`), S01 (entry, key, markers, S41 stub block, map anchors `# WP-30 S41 (P1.30): Verified bokeh window; internals fail closed (P1.30, M9/M10)` in `FUNCTIONS`, `SETUP_FUNCTIONS`, `COVERAGE["dash.ado"]`, `COVERAGE["dash_parse.mata"]`, `COVERAGE["dash_setup.ado"]`), S21 and S35 (the BokehJS calls the internals list names).
- **Blocks: 46, 54.** S46 verifies its session APIs across this window; S54 appends its Save-as-SVG APIs to `_DASH_BOKEH_INTERNALS`; S57 verifies Bokeh's thread rules across it.
- **Parallel batch 14**, merge order S39, S40, S41. S41 is the batch's template editor (the launcher part of `_generate_app_source`) and lands last.
- **Can run with:** S39 (`_dash_refline_*`, dash.ado's graph-option parse, `_dash_line_expand`, Mata `_dash_axreq_check`, the `reflines` limit row) and S40 (`_make_figure_body`, `_FILTER_JS`, `_build_filter_widgets`, the mappers, `_dash_join_glyph`). S41 edits none of them; the one shared function is `_glyph_layer_lines`, where each appends at its own R2 anchor.

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines, dash_setup.ado 1,026, dash_setup_lib.py 724, dash.sthlp 3,822, dash_setup.sthlp 253). S03-S25 move many of them; the executor re-finds each by its text at `batch-14-base`.

### E1. pip gets no upper bound (dash_setup.ado, dash_setup_lib.py)

```stata
48      local min_bokeh       "3.8"
296             local _spec "`pkg'>=`min_`pkg''"            // in-place install, only when import fails
612     local spec "`pkg'>=`minver'"                        // _dash_pip_command (604): upgrade and manual lines
156         _dash_setup_venv "`c_pymin'" "`min_bokeh'" "`min_numpy'" "`min_pandas'"
```

```python
29  #: and ceiling (P1.30's `bokeh>=3.8,<4' is admitted now).
31  _SPEC_RE = re.compile(r"^[A-Za-z0-9._-]+(>=[0-9][0-9.]*)?(,<[0-9][0-9.]*)?$")
686                     rc, out, err = run_child(pip_install_argv(
687                         vpy, ["packaging", "bokeh>=" + mins["bokeh"],
```

`stata_venv` (636) pip-installs into a reused venv too (`state == "venv"`, "using the environment already there"); `validate_venv_path` (312) accepts any directory with a `pyvenv.cfg`. With a plain ceiling that downgrades an installed 3.10 (critic C5). `pip_install_argv` (246, HIGH 3) is not edited: `_SPEC_RE` already admits `bokeh>=3.8,<3.10` and refuses `bokeh<3.10` and `!=` (research §7).

### E2. The gate has a floor only (dash_setup.ado `_dash_setup_gate`, 747-793)

`args pkg got want haspkg`; the fallback `_dash_pyver_ok "`got'" "`want'"` first, then `packaging` through `sfi.Macro.getLocal` (never interpolated). Verdicts `ok`, `below`, `unverified`, `unknown`; the caller (:372-449) prints `OK (version …)`, `(below minimum …)` with the managed-Python branch (:410-418: no pip line, `_dash_setup_guide managed` once), or `(not verified against …)`. Research M2: 3.7.3 below; 3.8.0, 3.8.2, 3.9.2, 3.10.0, 4.0.0, 99.0 ok.

### E3. No run-time version check (dash_render.py, the app)

`grep -n __version__` in dash_render.py, dash.ado, dash_setup.ado and dash_setup_lib.py finds nothing (critic re-measured). Research M4 and M6 are quoted in the Overview. `main` (36823): the mode check (36875-36878) and `_validate_output_path` (36880) come first, then `run = …` (36881). The generated launcher (section "5. __main__ block", from 36386): `"_port = %d" % port` (36405), `_dash_install_access_log_redaction()`, then `"if __name__ != '__main__':"` / `"    make_document(curdoc())"` (36412-36413), then `def _dash_server_app` (36416) whose body calls `_dash_harden_origin_check()` (36477) and `Server(…, auth_provider=_dash_token_auth(_DASH_SERVE_TOKEN), …)` (36482-36490); the `__main__` launcher (36501) catches `RuntimeError` from `_dash_server_app` with `_p.error(str(_e))` (36561-36562).

### E4. Text-sink safety is pinned to two exact patches (test/test_label_sinks.py)

```python
154 VERIFIED_BOKEH = {"3.8.0", "3.9.0"}
1245        assert bokeh.__version__ in VERIFIED_BOKEH, (
```

`TestBokehVersion` (1173) documents a manual Chromium check (steps 1-4: re-read the BokehJS text sinks, build a saved page and a `dash serve` app with `y` labelled `<img src=x onerror="document.title='PWNED'">Y label`, hover, check no IMG and an unchanged title), run on 3.8.0 on 24sep2026 (WP-25). 3.8.1, 3.8.2, 3.9.1 and 3.9.2 are on PyPI and fail the exact set; conftest compares major.minor (`_mm`, test/conftest.py:213).

### E5. The internals, measured (this pass, scratch `s41/probe1.py`-`probe3.py`, `/opt/anaconda3/bin/python3` and `/opt/homebrew/bin/python3`)

```
bokeh 3.8.0 py 3.13.9 | bokeh 3.9.0 py 3.14.5   (identical lines unless shown)
blocks ['body','contents','css_resources','head','inner_body','inner_head','js_resources','postamble','preamble','resources','root','title']
check_allowlist sig (host: 'str', allowlist: 'Sequence[str]') -> 'bool'
allow probe  3.8.0: True   3.9.0: False      # check_allowlist("localhost.dash-origin-check.invalid:1", ["localhost:1"])
harden       3.8.0: True, after False   3.9.0: False, after False
AP props ['get_user','get_user_async','get_login_url','login_url','endpoints']    # properties on AuthProvider
generate_jwt_token(session_id, secret_key=None, signed=False, extra_payload=None, expiration=300)
header keys ['__bk__zlib_', 'session_expiry', 'session_id']
roundtrip _dash_ws_payload("bokeh, " + generate_jwt_token(sid, extra_payload={"arguments": {"token": [b"abc"]}}))["arguments"] -> {'token': [b'abc']}
file_html(Div(text=""), Resources(mode="server", root_url="/"), "dash", template=_dash_served_template()) with bokeh.__version__ = "3.10.0": 0.003 s, csp 1, "<script" 5
default file_html page holds the literal "<head>": True
```

How each fails today when Bokeh changes it (research §2): a FILE without `preamble` renders `<html><head></head><body></body></html>` with no CSP and raises nothing (Jinja drops a child block its parent lacks), so `bokeh serve`'s only policy is gone (fails open); a missing `match_host` is a bare AttributeError; a `check_allowlist` that stops calling `match_host` leaves the lenient matcher (fails open, critic C2); a renamed AuthProvider hook is silently ignored, so Gate A admits every request (fails open, critic C3); a changed JWT layout makes `_dash_ws_payload` (4030) return None, so Gate A refuses every websocket (closed, unusable). The saved page's policy is spliced by `html_str.replace("<head>", …, 1)` (`_assemble_layout`, 32592-32596): a Bokeh writing `<head lang=…>` gets no policy and S04's seal (hashes only) does not see it (fails open).

```python
3784    from bokeh.core.templates import FILE
3785    return FILE.environment.from_string(
3786        "{% extends base %}\n"
3787        "{% block preamble %}{{ super() }}    "          # S04 adds js_resources and inner_body overrides
3893    if not _bokeh_util.match_host("localhost.dash-origin-check.invalid:1",
3894                                  "localhost:1"):
3895        return False
3896    _bokeh_util.match_host = _dash_strict_match_host
4089    from bokeh.server.auth_provider import AuthProvider
4102    class _DashTokenAuth(AuthProvider):
4104        def get_user_async(self):
```

`_dash_session_token_ok` (4114, Gate B) reads `doc.session_context.request.arguments` and already fails closed when any part is missing.

### E6. Served copy lists (R2 row S41)

Constants tuple: `"_DASH_LINK_SAID", "_DASH_BS_ORIGIN_HINT",` / `"_DASH_LINK_UNWRITTEN",` (32967-32968). Functions tuple: `"_dash_strict_match_host",` / `"_dash_harden_origin_check",` (33298-33299). S25 copies `_dash_dep_fail` into the header by source, not by list; `_dash_dep_versions` is never called by the app.

### E7. Tests that pin today's behaviour (flipped in place, never deleted; re-measured by 41-08 to 41-12)

- `test/test_label_sinks.py::TestBokehVersion::test_bokeh_is_a_version_this_was_verified_on` (:1245, exact patches).
- `test/test_version_floor.py::TestTheFloorIsTheTestedBaseline::test_every_declaration_agrees_with_dash_setup` (:72 `Requires: … bokeh>=%s, numpy…`; :80 the dash.sthlp Dependencies line).
- `test/test_floor_matrix.py::TestTheRequirementsFiles::test_each_file_pins_its_baseline_exactly` (S05: "bokeh is in `VERIFIED_BOKEH`", an exact patch).
- `test/test_setup_honesty.cscript` HON-20 (:518), HON-22 (:567), `HON_SB_EXPECT` (:746), HON-29 (:820): the pip vectors and lines `bokeh>=3.8`.
- `test/test_program_coverage.cscript` PC-19 (:764-765, :787), PC-21 (:795, :828), :983, :1024, :1039, :1056, and the venv vector :1087.
- `test/test_setup_python_gate.cscript` :176-178 (`pip install 'bokeh>=3.8'`).
- `test/test_help_examples.cscript` :550-552 and `test/test_help_examples.py:518` (the help's pip lines).
- Not flipped: test_setup_pep668.py :305-317, :352-367, :655-712 and test_version_floor.py :143-152 set `spec` themselves; `scripts/extract_pip_refusals.py`/`test/fixtures/pip_refusals.json` are spec-agnostic (critic C11); test_setup_sandbox.py:276 is the sandbox's own self-test pip call (41-10 re-measures it).

### E8. Blast radius

| Symbol | Risk | Action |
|---|---|---|
| `main` | HIGH at the base (index 14.0) | warn; three lines after `_validate_output_path` |
| `ServerAppBuilder._generate_app_source` | HIGH (5) | warn; one block in section 5 and two calls in the launcher text |
| `ServerAppBuilder._glyph_layer_lines` | HIGH (4) | warn; names appended at S41's two anchors |
| `_dash_served_template`, `_dash_harden_origin_check`, `_dash_token_auth` | UNKNOWN (generated-text callers; grep in Risk) | confirmed by grep; guards added, success paths unchanged |
| `_dash_dep_versions` (S25), `_dash_seal_saved_page` (S04) | measured at `batch-14-base` | one slot filled; one condition added |
| `_dash_ws_payload` | LOW (2) | not edited; called by the new probe |
| `pip_install_argv` | HIGH (3) | not edited |
| `stata_venv`, `VERIFY_CODE`, dash_setup.ado programs | UNKNOWN | grep callers above |

## User stories

- **US-41.1** As an installer, I want `dash_setup` to install a bokeh dash was verified on, and to tell me plainly when the one I have is newer, without changing it, so a fresh setup gets a tested stack and my other work keeps its Bokeh.
- **US-41.2** As a dashboard author, I want `dash` to note once when it runs under a bokeh newer than it was verified on, and to refuse an older one naming `dash_setup`, in a saved build, `dash build, server`, `dash serve`, `python app.py` and `bokeh serve`, so I know when a page's look and its handling of my data's text are unverified.
- **US-41.3** As a publisher of a served dashboard, I want the server to refuse to start with a named error when a Bokeh release changes the hooks dash's Content-Security-Policy, origin check and key check rely on, so an upgrade can never silently serve my data without them.
- **US-41.4** As a maintainer, I want the window declared in one place and every declaration and the text-sink verification tied to it, so widening it is one reviewed change.

## Business requirements

- **BR-41.1** `dash_setup` installs bokeh only inside the window (`bokeh>=3.8,<3.10`): in place when bokeh is missing, into a venv it creates, and into a reused venv whose bokeh is missing or below the window. An installed bokeh at or above the ceiling is never changed (A107).
- **BR-41.2** `dash_setup` reports a bokeh at or above the ceiling as `outside the verified range` (a warning, rc 0, counted in the summary). On an externally managed Python it prints the private-environment guidance once and no pip line; otherwise it prints the line that installs a verified bokeh, naming the linked Python, and runs nothing (A105, critic C6). Every pip line `dash_setup` prints for bokeh carries the ceiling.
- **BR-41.3** At run time in both modes, a bokeh below 3.8 is refused (r(198) in Stata, exit status 1 under `python app.py`, every session refused under `bokeh serve`), naming the version, 3.8 and `dash_setup`. A bokeh above the window gets one `(note:  dash: …)` line per command in Stata (`dash serve` included: the child's copy is not repeated), and one per process under `python app.py` and `bokeh serve`; the dashboard is drawn. A bokeh inside the window, or a patch release of a verified minor, prints nothing (A104).
- **BR-41.4** The text-sink injection checks run, in a browser, for every bokeh minor in the window, and each minor has its verification date recorded; `VERIFIED_BOKEH` equals the window.
- **BR-41.5** If the installed Bokeh lacks, or has changed, any internal on `_DASH_BOKEH_INTERNALS` that guards security (template blocks, the saved `<head>`, the origin matcher, the AuthProvider hook, the session-token layout), the server refuses to start, a served session is refused, or the saved page is not written, with one message naming the internal, the Bokeh version and `dash_setup` (A109).
- **BR-41.6** One window is declared: dash_render.py's constants, dash_setup.ado, dash.pkg, both help files, the requirements files, `scripts/floor_matrix.sh`'s fresh leg, the CHANGELOG Requirements line and `VERIFIED_BOKEH` agree, and a test enforces it. Only bokeh carries a ceiling (A108); there is no constraints file and no hash pinning (A106).

## Technical requirements

### Commit 1: the window

- **TR-41.1 The 3.10 verification (before any code; M10, E12).** 41-01 builds `$S/venv-s41-bk310` with S05's `sh scripts/floor_matrix.sh make /opt/homebrew/bin/python3 $S/venv-s41-bk310 dev` (dev pins, bokeh 3.9), then `$S/venv-s41-bk310/gatevenv/bin/python -m pip install --require-virtualenv --only-binary=:all: "bokeh==3.10.*"` with `PIP_CONFIG_FILE=/dev/null`, `PIP_DISABLE_PIP_VERSION_CHECK=1`, `PIP_CACHE_DIR=$S/venv-s41-bk310/pip-cache`. Verified means all of:
  1. one full run through the queue on the unmodified base: `PATH="$S/venv-s41-bk310/gatevenv/bin:$PATH" DASH_BASELINE=dev "$S/full_suite_queue.sh" "$WT" "$S/41-bk310-full.log"`: the drift warning names bokeh only (3.9 → 3.10); no `skipped`; the only failure allowed is `test/test_label_sinks.py::TestBokehVersion::test_bokeh_is_a_version_this_was_verified_on` (the exact-patch pin 41-08 replaces), E6 for the known flaky tests. Non-strict, because `floor_matrix.sh run` is strict and stops on a bokeh drift; the skip and drift checks replace strictness;
  2. the internals probe `$S/41-bk310-internals.py` (E5's probes) under the venv: the three blocks present, `match_host` and `check_allowlist` present, the origin probe False after `_dash_harden_origin_check()`, the five AuthProvider properties, the JWT round trip, and the served template's probe page with one CSP meta and S04's nonce on every script element;
  3. the text sinks: `TestBokehVersion`'s step 1 against the venv's `bokeh/server/static/js/bokeh.min.js` (each function its docstring names still makes a text node; the tooltip field is still the only HTML-parsed part), recorded in `$S/41-bk310-sinks.txt`; and steps 2-3 in headless Chrome through S04's `_CspProbe`, as `$S/41-bk310-sinks.py`: a saved page and a `python app.py` app built by the venv's Python with `y` labelled with the payload; the axis title, legend and hovered tooltip show the literal text, no IMG element (shadow roots included), `document.title` unchanged.
  All green → `3.11` into `$S/41-ceiling.txt`; anything red → `3.10`, with the reason in `$S/41-bk310-verdict.txt`. `shasum ~/.stata19/console/stata19.rc` is unchanged; nothing is installed outside the venv.
- **TR-41.2 The window (dash_render.py).** Directly after S25's `_dash_dep_versions`, before the "Optional scientific dependencies" banner, a `#:` comment (WP-30 P1.30, M9, A104: patch releases inherit their minor's verification; dash_setup.ado's `min_bokeh`/`max_bokeh` hold the same, pinned by `TestTheWindowIsDeclaredOnce`) and
  ```python
  _DASH_BOKEH_FLOOR = (3, 8)
  _DASH_BOKEH_CEIL = (3, 10)            # exclusive
  _DASH_BOKEH_VERIFIED = ((3, 8), (3, 9))
  ```
  - `_dash_bokeh_window(version) -> str`: `s = str(version or "")[:40]`; `m = re.match(r"(\d+)\.(\d+)", s)`; no match → `"unknown"`; `mm = (int, int)`; `mm < _DASH_BOKEH_FLOOR` → `"below"`; `mm in _DASH_BOKEH_VERIFIED` → `"verified"`; else `"above"` (3.10.0rc1 and dev builds of an unverified minor are above). `import re` local.
  - `_dash_bokeh_check(version=None) -> tuple[str, str]` (refusal, note): `version` None → `getattr(sys.modules.get("bokeh"), "__version__", None)`, importing bokeh inside `try` if absent. The shown version is `"".join(c for c in str(v)[:40] if c.isprintable())`; `rng = "bokeh>=%d.%d,<%d.%d"`; `ver = ", ".join("%d.%d" % p for p in _DASH_BOKEH_VERIFIED)`.
    - below: refusal `"dash: bokeh %s at %s is older than %d.%d, the oldest bokeh dash runs with; run dash_setup, which installs %s"` (exe = `str(sys.executable or "python")[:300]`), note `""`.
    - above: refusal `""`, note `"dash: bokeh %s is newer than the bokeh releases dash was verified on (%s); the dashboard is drawn, but its look and whether text from your data stays inert are unverified; dash_setup installs %s"`.
    - unknown: note `"dash: the installed bokeh's version (%s) could not be read, so dash cannot tell whether it was verified on it (%s); run dash_setup"`.
    - verified: `("", "")`. Reads only `sys`, `re`, the three constants and `_dash_bokeh_window`; no exe in the note, so `main()` and the app produce the same text.
  - `_dash_dep_versions` (S25): its refusal element becomes `_dash_bokeh_check()[0]`; nothing else in it changes. The bokeh note is not added there: it is `main()`'s (TR-41.3), so it prints on every command, not once per load.
- **TR-41.3 `main` (HIGH, warn).** Directly after `_validate_output_path(output_path, mode, launch=launch)` (36880), under a comment (WP-30 P1.30, M9; the refusal normally fires earlier in Stata through `_dash_dep_versions`; this one covers a direct call):
  ```python
  _bk_refuse, _bk_note = _dash_bokeh_check()
  if _bk_refuse:
      raise RuntimeError(_bk_refuse)
  if _bk_note:
      warnings.warn(_bk_note, UserWarning, stacklevel=2)
  ```
  S06's scope prints it as `(note:  dash: bokeh …)` once per command; `dash serve`'s scope records it in `_dash_said`, so S23's relay skips the child's identical line.
- **TR-41.4 The app at start (`_generate_app_source`, section 5; HIGH, warn).** Directly after the `"_dash_install_access_log_redaction()", "",` pair that precedes `"if __name__ != '__main__':"` (36412), insert:
  ```python
  "# WP-30 P1.30 (M9): the bokeh this app runs under, checked at start.",
  "# Below dash's floor it stops (python app.py: exit status 1, one line;",
  "# bokeh serve: every session refused); above the verified window it",
  "# notes once per process (the note hook's holder) and serves on.",
  "_dash_bk_refuse, _dash_bk_note = _dash_bokeh_check()",
  "if _dash_bk_refuse:",
  "    raise (SystemExit if __name__ == '__main__' else RuntimeError)(_dash_bk_refuse)",
  "if _dash_bk_note and not globals().get('_DASH_TRIAL', False):",
  "    warnings.warn(_dash_bk_note, UserWarning)",
  "",
  ```
  `warnings` is imported by S25's header; S23's hook (installed earlier in the module for `__main__` and `bokeh_app_*`) prints the note once per process. A `SystemExit` with a string writes it to stderr with status 1, which `_dash_launch_app` relays as r(198). Nothing else in the generator changes in commit 1.
- **TR-41.5 Served copy list (R2 row S41, X.1 append only).** Constants: `"_DASH_BOKEH_FLOOR", "_DASH_BOKEH_CEIL", "_DASH_BOKEH_VERIFIED",` on a new line after `"_DASH_LINK_UNWRITTEN",` (32968), under a one-line comment "WP-30 P1.30: the verified bokeh window." Functions: `"_dash_bokeh_window", "_dash_bokeh_check",` on a new line after `"_dash_harden_origin_check",` (33299).
- **TR-41.6 dash_setup.ado** (every edited program keeps `version 19`):
  - `local max_bokeh "3.10"` on the line after `local min_bokeh "3.8"` (:48), and the comment above (:38-47) gains: the ceiling is exclusive, the first minor not verified (M9); dash_render.py's `_DASH_BOKEH_CEIL` holds the same.
  - In-place install (:296): after `local _spec …`, `if "`pkg'" == "bokeh" local _spec "`_spec',<`max_bokeh'"`. It runs only when `import bokeh` failed, so nothing installed is replaced.
  - The version loop (:365-372): `local maxver ""`, `if "`pkg'" == "bokeh" local maxver "`max_bokeh'"`; the gate call gains `"`maxver'"` as a fifth argument.
  - `_dash_setup_gate pkg got want haspkg [ceil]`: `args pkg got want haspkg ceil`. After the existing verdict is set and before `return local verdict`: when `"`ceil'" != ""` and the verdict is `ok` or `unverified`, `_dash_pyver_ok "`got'" "`ceil'"`; `r(ok) == 1` → verdict `above` (the numeric fallback reads `3.10.0rc1` at or above `3.10`, which is what "above" needs). The four-argument callers are unchanged; the header comment lists `above`.
  - A new branch `else if "`verdict'" == "above"` after `below`'s: `display as text "  `pkg' ............. {res}`pkgver'{txt} (outside the verified range: `minver' or later, before `maxver')"`; `n_warn + 1`; `warn_items` gains `` `pkg' `pkgver' (outside the verified range)``; detection as the `below` branch does (`_dash_setup_detect` once); managed → `_dash_setup_guide managed` once (critic C6); else `display as text "      To install a verified one:"` then `_dash_pip_command "`pkg'" "`minver'" manual "`maxver'"` and `return local hint_cmd`. No install runs.
  - `_dash_pip_command pkg minver [how] [maxver]`: after `local spec …` (:612), `if "`maxver'" != "" local spec "`spec',<`maxver'"`. The `upgrade` (:424) and `manual` (:349) calls pass `"`maxver'"` / `"`max_bokeh'"` for bokeh.
  - `_dash_setup_venv pymin minb minn minp maxb` (1010-1016 header and `args`); the call at :156 passes `"`max_bokeh'"`.
- **TR-41.7 dash_setup_lib.py.**
  - `bokeh_requirement(installed, floor, ceil) -> str` (new, after `pip_install_argv`): `floor` and `ceil` must fullmatch `[0-9]+(\.[0-9]+)*`, else `ValueError`. `m = re.match(r"(\d+)\.(\d+)", str(installed or "")[:40])`; when `m` and `(int, int) >= version_tuple(ceil)[:2]` → `"bokeh>=" + floor` (never a downgrade); else `"bokeh>=%s,<%s" % (floor, ceil)`. Docstring: A107, critic C5.
  - `stata_venv`: `mins` gains `"bokeh_ceil": sfi.Macro.getLocal("maxb")`. Compute `render_py` before the install. For `state == "venv"` (reused) run `pre = verify_in(vpy, render_py, mins, d["version"])` first and take `have = (pre.get("packages") or {}).get("bokeh", "")`; for a venv just made `have = ""`. The install list uses `bokeh_requirement(have, mins["bokeh"], mins["bokeh_ceil"])`. After a passing verify, when `"bokeh" in (v.get("above") or [])`: print `"  bokeh %s in it is outside the verified range (%s or later, before %s); it was left as it is, and dash notes it when it draws."`.
  - `VERIFY_CODE`: after the package loop, `_out['above'] = []`; `_c = _mins.get('bokeh_ceil', '')`; when `_c` and `_out['packages'].get('bokeh')` and `_t(_out['packages']['bokeh'])[:2] >= _t(_c)[:2]`, append `'bokeh'`. `ok` and `why` are unchanged by it (A105).
  - `stata_shell_line` and `pip_install_argv` are not edited.
- **TR-41.8 Requirements files (IR-16; S05's rule kept).** Each of `test/requirements-stata.txt` and `test/requirements-dev.txt` gains one comment line directly under its header: `# bokeh window (WP-30 P1.30): bokeh>=3.8,<3.10; dash_setup installs it and the pin below lies inside it.` No `name==version` line changes; no option line is added.
- **TR-41.9 `VERIFIED_BOKEH` (test/test_label_sinks.py).** `VERIFIED_BOKEH = {"%d.%d" % p for p in dr._DASH_BOKEH_VERIFIED}` (import `dash_render as dr` if absent), its comment stating A104. New `VERIFIED_ON = {"3.8": "24sep2026, WP-25 (Chromium, saved page and dash serve)", "3.9": "<date of the 3.9 record in the docstring, or of 41-02's browser run under 3.9>", …}`; with ceiling 3.11 it gains `"3.10": "<ddmonyyyy>, WP-30 P1.30 (headless Chrome, saved page and python app.py; $S/41-bk310-sinks.txt)"`. `TestBokehVersion::test_bokeh_is_a_version_this_was_verified_on` (flipped) asserts `_mm(bokeh.__version__) in VERIFIED_BOKEH`; its docstring's step 4 reads "add the minor to `_DASH_BOKEH_VERIFIED` and `VERIFIED_ON`".
- **TR-41.10 Help and package (R3: Dependencies paragraphs only).**
  - dash.pkg:17 `d Requires: Python <FLOOR>+, bokeh>=3.8,<3.10, numpy>=2.3, pandas>=2.3.` (S05's floor kept).
  - dash.sthlp Dependencies (3780-3818): `bokeh>=3.8,<3.10, numpy>=2.3, pandas>=2.3.`, then one sentence: "{cmd:dash} was verified on bokeh 3.8 and 3.9 (any patch release of either); under a newer bokeh it draws and prints a note, and under one older than 3.8 it stops and names {helpb dash_setup}. Only bokeh has a ceiling."
  - dash_setup.sthlp: :98 "at their minimums" → "at their minimums, bokeh within the verified range,"; :137 `{synopt:{opt bokeh}}3.8 or later, before 3.10{p_end}`; a "verified range" paragraph after :150-160 (S05's text kept): the range, A104, that a bokeh at or above 3.10 is reported as a warning and never changed, the managed-Python rule; :166 and :241 and :247 lines carry `"bokeh>=3.8,<3.10"`; :185-187 gains "one at or above 3.10 is reported as outside the verified range, a warning, and left as it is".
  - Every new or changed line is at most 79 characters; no tool or vendor name.
- **TR-41.11 Registries.** `test/function_test_map.py` `FUNCTIONS`, under S41's anchor: `'_dash_bokeh_check': 'test/test_bokeh_window.py::TestTheRuntimeCheck::test_below_the_floor_is_refused_naming_dash_setup'`, `'_dash_bokeh_window': 'test/test_bokeh_window.py::TestTheWindowVerdict::test_each_version_gets_its_verdict'`. `SETUP_FUNCTIONS`, under S41's anchor: `"bokeh_requirement": _P + "TestTheBokehWindow::test_the_requirement_never_downgrades"`. `program_coverage_map.py`: no new program; `_dash_setup_gate`, `_dash_pip_command`, `_dash_setup_venv` are edited in place (R2), so the S41 anchors in `COVERAGE` stay empty for S58 to remove.

### Commit 2: internals fail closed

- **TR-41.12 `_dash_served_template` (the per-session block check).** Before `return FILE.environment.from_string(…)`: `missing = [b for b in ("preamble", "js_resources", "inner_body") if b not in getattr(FILE, "blocks", {})]`; if any, `raise RuntimeError("dash: this Bokeh's page template (bokeh %s) has no %s block, where dash puts the page's Content-Security-Policy and script nonce; the served page would have no policy, so it is not served. Run dash_setup for a verified bokeh." % (v, ", ".join(missing)))`. The docstring names the guard. Cost: one dict lookup per session.
- **TR-41.13 `_dash_check_served_template()`** (new, directly after `_dash_served_template`; launch-time and per `bokeh serve` session, 3 ms measured): `nonce = _dash_new_nonce()`; `page = file_html(Div(text=""), Resources(mode="server", root_url="/"), "dash", template=_dash_served_template(nonce))` (local imports from `bokeh.embed`, `bokeh.models`, `bokeh.resources`); `head = page[:i]` where `i = page.lower().find("</head>")` (no `</head>` → error). Error unless: exactly one `re.findall(r'<meta\s+http-equiv="Content-Security-Policy"', head, re.I)`; `"'nonce-%s'" % nonce` in that head; at least one script element; and every script element's opening tag holds `nonce="<nonce>"`, scanning as `_dash_nonce_scripts` does (match `<script(?=[\s>/])` case-insensitively, take the tag to its `>`, then skip to the next `</script` before searching again). The `RuntimeError` names the count found, the Bokeh version and `dash_setup`. Never renders on an empty context (critic C1).
- **TR-41.14 `_dash_seal_saved_page` (S04's seal; the saved `<head>`).** Before its hash check: `h = page[:page.lower().find("</head>")]` (none → whole page); when the number of `<meta\s+http-equiv="Content-Security-Policy"` matches in `h` (case-insensitive) is not 1, `raise DashScriptPolicyError("dash: refusing to write a page whose head holds %d Content-Security-Policy elements (bokeh %s); dash writes exactly one, so this Bokeh's page is not one dash was verified on; nothing was written." % (n, v))`. Counting only the head keeps user text (in the body's JSON) out of the count. Both saved paths (`_assemble_layout`, `_render_bootstrap_html`) already call the seal.
- **TR-41.15 `_dash_harden_origin_check` (named errors; critic C2).**
  1. `import bokeh.server.util as _bokeh_util`; if `match_host` or `check_allowlist` is not callable on it: `RuntimeError("dash: this Bokeh (bokeh %s) has no bokeh.server.util.%s, which dash's websocket origin check relies on; the server was not started. Run dash_setup for a verified bokeh.")`.
  2. The existing probe and replacement, unchanged.
  3. Then `if _bokeh_util.check_allowlist("localhost.dash-origin-check.invalid:1", ["localhost:1"]):` → `RuntimeError("dash: this Bokeh (bokeh %s) admits a websocket origin that only begins with an allowed host, and dash could not make the check exact; the server was not started. Run dash_setup for a verified bokeh.")`.
  It still returns True only when it replaced the matcher; the launcher's print is unchanged.
- **TR-41.16 `_dash_check_auth_internals()`** (new, directly above `_dash_token_auth`): inside `try`, `from bokeh.server.auth_provider import AuthProvider` and `from bokeh.util.token import generate_jwt_token, generate_session_id, get_token_payload`; an exception → `RuntimeError("dash: this Bokeh (bokeh %s) lacks %s, which the served app's key check uses; the server was not started. Run dash_setup for a verified bokeh.")` naming the import that failed (`type(e).__name__` and its text bounded to 200 characters). Then `get_user_async` and `get_login_url` must be `property` objects on `AuthProvider` (getattr on the class), else the same error naming the hook. Then the round trip: `tok = generate_jwt_token(generate_session_id(), extra_payload={"arguments": {_DASH_TOKEN_ARG: [b"dash-probe"]}})`; `got = _dash_one_value(((_dash_ws_payload("bokeh, " + tok) or {}).get("arguments") or {}).get(_DASH_TOKEN_ARG))`; `got` must be `b"dash-probe"` or `"dash-probe"`, else the error naming "the session token's layout". Measured round trip in E5.
- **TR-41.17 `_dash_token_auth`.** First statement: `_dash_check_auth_internals()`. After building the class: `prov = _DashTokenAuth()`; unless `prov.get_user_async is _admit and prov.get_login_url is _refuse`, `RuntimeError` naming the AuthProvider hook. Return `prov`. Success paths unchanged.
- **TR-41.18 `_DASH_BOKEH_INTERNALS`** (directly after `_DASH_BOKEH_VERIFIED`; a tuple of `(internal, guard, test)` string triples, literal-evaluable), with a `#:` comment: every Bokeh internal dash depends on, the guard that fails closed, and the test that pins it; S54 appends (Save as SVG); S46 and S57 verify theirs across the window. Entries:
  1. `bokeh.core.templates.FILE blocks preamble, js_resources, inner_body` / `_dash_served_template, _dash_check_served_template` / `test/test_bokeh_internals.py::TestTheTemplateFailsClosed::test_a_template_without_the_blocks_is_refused`;
  2. `the <head> of file_html's page` / `_dash_seal_saved_page` / `…::TestTheSavedHeadFailsClosed::test_a_page_without_its_policy_is_not_written`;
  3. `bokeh.server.util.match_host and check_allowlist (imported by the websocket handler at call time)` / `_dash_harden_origin_check` (both launchers: `python app.py` and the bokeh-serve branch, Q-41.1) / `…::TestTheOriginCheckFailsClosed::test_a_missing_matcher_is_a_named_error`;
  4. `bokeh.server.auth_provider.AuthProvider.get_user_async, get_login_url (properties)` / `_dash_check_auth_internals, _dash_token_auth` / `…::TestTheKeyCheckFailsClosed::test_a_renamed_hook_is_a_named_error`;
  5. `bokeh.util.token get_token_payload, generate_jwt_token; the __bk__zlib_ header; the "bokeh, <jwt>" subprotocol` / `_dash_check_auth_internals` / `…::TestTheKeyCheckFailsClosed::test_a_changed_token_layout_is_a_named_error`;
  6. `doc.session_context.request.arguments` / `_dash_session_token_ok (fails closed by construction)` / the existing Gate B test the executor finds with `grep -n "def test.*" test/test_serve_token.py` naming a session without the key;
  7. `bokeh.__version__` / `_dash_bokeh_check` / `test/test_bokeh_window.py::TestTheRuntimeCheck::test_below_the_floor_is_refused_naming_dash_setup`;
  8. `BokehJS Range1d start, end, reset_start, reset_end writes and change.emit() (S21's _DASH_AXIS_FINISH_JS)` / `browser test` / `test/test_default_axes_chrome.py` (S21);
  9. `BokehJS CustomJSTransform func and v_func with args (S35's _DASH_DATE_UNITS_JS)` / `browser test` / `test/test_csp_browser.py::TestTheDateTransformUnderTheCsp::test_saved_page` (S35);
  10. `bokeh.models.CustomJSTicker (imported by every render; the floor's reason)` / `_dash_dep_fail` (S25) / `test/test_dependency_guards.py` (S25).
  If S21 or S35 named their browser tests otherwise at `batch-14-base`, use their names.
- **TR-41.19 The launcher (commit 2).** In `_dash_server_app`'s text, directly before `"    _dash_srv = Server(",` (36482): `"    _dash_check_served_template()",` under a one-line comment. The bokeh-serve branch becomes `"if __name__ != '__main__':"`, `"    _dash_check_served_template()"`, `"    _dash_harden_origin_check()"`, `"    make_document(curdoc())"`. The third line is Q-41.1, resolved: `bokeh serve` runs the app module in the server's process for each session before that session's websocket connects, and Bokeh's handler imports `check_allowlist` at call time (E5, `bokeh/server/views/ws.py:107`). So the strict matcher and TR-41.15's post-hardening probe govern every session's origin check under `bokeh serve` too, including the first one. The call is idempotent: a second call finds the strict matcher, returns False, and passes the probe. It prints nothing; the help says it. A `RuntimeError` from `_dash_server_app` already reaches `_p.error` (exit 2, one line); under `bokeh serve` it refuses that session. Copy list: `"_DASH_BOKEH_INTERNALS",` after S41's commit-1 constants line; `"_dash_check_served_template", "_dash_check_auth_internals",` after S41's commit-1 functions line.
- **TR-41.20 Registries and help (commit 2).** `FUNCTIONS` under S41's anchor: `'_dash_check_auth_internals': 'test/test_bokeh_internals.py::TestTheKeyCheckFailsClosed::test_a_changed_token_layout_is_a_named_error'`, `'_dash_check_served_template': 'test/test_bokeh_internals.py::TestTheTemplateFailsClosed::test_the_probe_page_is_counted'`. dash.sthlp Server Mode (R3, S41's row): the paragraph at 1688-1694 keeps its origin sentences and replaces "{cmd:bokeh serve app.py} uses Bokeh's own check, so run it under Bokeh 3.9 or later." by "{cmd:bokeh serve app.py} makes Bokeh's check exact in the same way for every session, and {cmd:dash} notes any bokeh newer than it was verified on." (Q-41.1); one new paragraph after it: "If a bokeh release changes what this protection relies on -- the page template's blocks, the origin matcher, the key check's hook or its token layout -- the app refuses to start ({cmd:python app.py}) or refuses each session ({cmd:bokeh serve}) with a message naming it, and a saved page is not written; {helpb dash_setup} installs a verified bokeh."
- **TR-41.21 Security (rule 1, G9).**
  - Commit 1 closes: an unverified Bokeh, whose label, legend and tooltip text sinks have not been checked for injection, installed by `dash_setup` and run with no word; a bokeh below the floor run with unknown behaviour.
  - Commit 2 closes: a template without `preamble` serving with no CSP; a saved page whose `<head>` changed written without its policy; a `check_allowlist` that stops calling `match_host` re-admitting look-alike origins; a renamed AuthProvider hook disabling Gate A (each previously fails open).
  - The version string (package metadata) is bounded to 40 printable characters and reaches the user only through S06's escaping (`_dash_emit_note`, Mata `_dash_note`/`_dash_say`); in dash_setup.ado `got` reaches Python only through `_dash_pyver_ok` and `sfi.Macro.getLocal`, never interpolated (test_cscript_hygiene's rule); `maxver` is dash's own literal; every pip spec passes `_SPEC_RE`; nothing is `eval`ed and no `shell=True`. No guard reads user data; every error is one line.

## Boundaries

- **Batch 14 partners:** S39's `_dash_refline_*`, dash.ado graph-option parse, `_dash_line_expand`, Mata `_dash_axreq_check`, the `reflines` limit row and Resource-limits help; S40's `_make_figure_body`, `_FILTER_JS`, `_build_filter_widgets`, the mappers, `_dash_join_glyph`, Plot types and Unsupported help. S41 edits none; in `_glyph_layer_lines` it appends only at its own anchors (R2).
- **Earlier sections, read only except where named:** S04's nonce helpers and policy constants (only `_dash_seal_saved_page` gains one condition); S05's conftest `_BASELINES`, `scripts/floor_matrix.sh` (its `fresh` spec changes only if the ceiling is 3.11), `test_floor_matrix.py` (one flip); S06's channel; S23's hook, relay and `_DASH_TRIAL`; S25's `_dash_dep_fail`, header guards and `_dash_require_deps` (only `_dash_dep_versions`' refusal element changes).
- **Not this section's:** numpy/pandas ceilings (A108); constraints files and hash pinning (A106, OQ7); xdist, node, Chrome and scipy declarations (GAPS2-K5-d, P3.9, IR-16); the nox matrix (P1.33/P1.34); `sys.executable` as the served child (P2.40); bokeh 3.8 vs 3.9 performance (P2.41); nothing of Q-41.1 (resolved: the bokeh-serve branch hardens too, TR-41.19).
- **Never:** `pip_install_argv`, `_SPEC_RE`, `_dash_launch_app`, `_dash_ws_payload`, `_dash_strict_match_host`, the `make_document` body, `DashRenderer.render`, any scheme file; downloads outside `$S/venv-*` (M10); a `permanently` python link.

## Stata truth

None in twoway's sense: P1.30 is a dependency policy, not drawing (research §3). The Stata-side checks are setup-gate and run-time cases:

- **`test/test_setup_version_gate.cscript`** (R1: one contiguous run after SVG-05's `display` and before `display ""`/`ALL CHECKS PASSED`, headed `// BK: the verified bokeh window (WP-30 P1.30)`; `qui do "../dash_setup.ado"` as the script does):
  - BK-01 `_dash_setup_gate bokeh 3.10.0 3.8 1 3.10` → `above`; BK-02 the same with haspkg 0 → `above`; BK-03 `3.10.0rc1` → `above`; BK-04 `3.9.2` → `ok`, `3.7.3` → `below`; BK-05 the four-argument `_dash_setup_gate bokeh 99.0 3.8 1` → `ok` (old callers unchanged); BK-06 hostile `got` (`1.0") == __import__("os").system("touch BK06") or Version("1.0`) with ceil `3.10`: no file `BK06`, rc 0.
- **`test/test_setup_honesty.cscript`** HON-50..HON-56 (one run after the last HON case block; sandbox through `setup_sandbox.py`, `"fake": [["bokeh", "<v>"]]`):
  - HON-50 bokeh 3.10.0, pip available: rc 0; log holds `outside the verified range: 3.8 or later, before 3.10`, `with 1 warning(s)` and `Warned:` naming bokeh; the printed line holds `'bokeh>=3.8,<3.10'` and the linked Python; no pip install vector is recorded.
  - HON-51 the same on a managed Python: the venv guidance once, no `pip install` line, rc 0.
  - HON-52 bokeh 3.9.2: `OK (version 3.9.2)`, no warning.
  - HON-53 bokeh blocked and unblocked on install: the recorded vector ends `bokeh>=3.8,<3.10`.
  - HON-54 `_dash_pip_command bokeh 3.8 upgrade 3.10` → `r(cmd)` holds `bokeh>=3.8,<3.10`; HON-55 without the fourth argument → `bokeh>=3.8` (unchanged form).
  - HON-56 `venv()` into a recorded reused venv whose verify reports bokeh 3.10.0: the install vector holds `bokeh>=3.8` with no ceiling and the log the "left as it is" line.
- **The S41 block of `test/test_wp30_truth.cscript`** (fills S01's stub `* ==== S41 P1.30: Verified bokeh window; internals fail closed ====`; helper `_s41_notes` above the header counts `(note:  dash: bokeh` lines in a named log). Plain `python:` lines only, no captured import probe, so `test_cscript_hygiene.py:322` stays 13 (R1):
  - BK-20 `python: import bokeh, bokeh.embed, bokeh.resources, bokeh.plotting, bokeh.models, bokeh.server.server`; keep `bokeh.__version__` in `_s41_v`; set `"3.10.0"`; `dash scatter mpg weight, saving("`c(tmpdir)'/s41a.html") replace` → rc 0, the file exists, exactly one note line naming `3.10.0` and `dash_setup`.
  - BK-21 the same for `dash build, server saving("`c(tmpdir)'/s41a.py") replace nobrowser`.
  - BK-22 `"3.7.3"`: `capture noisily dash scatter …, saving("`c(tmpdir)'/s41b.html") replace` → rc 198, the log names `bokeh 3.7.3`, `3.8` and `dash_setup`, no `s41b.html`.
  - BK-23 restore `_s41_v`: rc 0 and no note line.
- Runs: `WP30_ONLY=S41 "$SLOT" "$S" "$S/run_<script>.do"` through the driver; no fixture.

## TDD test stubs

### Commit 1 regression tests (red at the batch-14 base unless marked guard; 41-02, 41-03)

New `test/test_bokeh_window.py` (module docstring: the defect, E1-E4, M9, A104-A107). Helpers: `_patched(monkeypatch, v)` imports `bokeh.embed`, `bokeh.resources`, `bokeh.plotting`, `bokeh.models`, `bokeh.server.server` and then sets `bokeh.__version__`; `_spec`/`_data` from `test_mode_parity`; `_boot(tmp_path, app, v)` writes a boot script that does the same imports, patches, sets `sys.argv` and `runpy.run_path(app, run_name="__main__")`.
- Test: 2.4.3, 3.7.3 below; 3.8.0, 3.8.2, 3.9.0, 3.9.2, 3.9.0rc1 verified; 3.10.0, 3.10.0rc1, 3.10.0.dev2, 4.0.0 above; `""`, `"x"`, `"3"`, `None` unknown; a 10,000-character string judged within 0.1 s — `TestTheWindowVerdict::test_each_version_gets_its_verdict[<v>]`
- Test: `_DASH_BOKEH_FLOOR == VERIFIED[0]`, the verified minors are contiguous, `CEIL` is one minor past the last — `TestTheWindowVerdict::test_the_constants_are_one_window`
- Test: dash_setup.ado `min_bokeh`/`max_bokeh`, dash.pkg's Requires, dash.sthlp's Dependencies line, dash_setup.sthlp's table row and its three pip lines, `scripts/floor_matrix.sh`'s fresh spec, `test_label_sinks.VERIFIED_BOKEH`, and every `_BASELINES` bokeh (inside the verified set) agree with the constants — `TestTheWindowIsDeclaredOnce::test_every_declaration_names_the_window`
- Test: each requirements file has exactly one `# bokeh window` line naming the spec, and its `bokeh==` pin's minor is verified — `::test_the_requirements_files_name_the_window`
- Test: `VERIFIED_ON`'s keys equal the window's minors — `::test_every_minor_was_checked_in_a_browser`
- Test: patched 3.7.3: `_dash_bokeh_check()[0]` names `3.7.3`, `3.8`, `dash_setup`; `_dash_dep_versions()[0]` equals it; `dr.main(…)` raises RuntimeError with it and writes nothing — `TestTheRuntimeCheck::test_below_the_floor_is_refused_naming_dash_setup`
- Test (both modes): patched 3.10.0: `dr.main` writes the output and raises exactly one UserWarning starting `dash: bokeh 3.10.0`, naming `3.8, 3.9` and `dash_setup`; under the real version none — `::test_above_the_window_is_one_note_and_the_page_is_written[standalone|server]`
- Test: version `"3.10.0\x1b[31m{res}" + "9"*60` → the note holds no control character and at most 40 characters of version — `::test_the_version_text_is_bounded_and_printable`
- Test: the generated app, executed, defines `_dash_bokeh_window`, `_dash_bokeh_check` and the three constants, and its section-5 block precedes `if __name__ != '__main__':` — `TestTheServedAppChecksAtStart::test_the_app_carries_the_window`
- Test (`serve`): `_boot` with 3.7.3 → exit status 1, stderr holds the refusal, no `Bokeh Server running` — `::test_python_app_py_below_the_floor_stops`
- Test (`serve`): `_boot` with 3.10.0 through `test_server_serves._Launched` → `/health` answers, stderr holds exactly one `(note:  dash: bokeh 3.10.0` line — `::test_python_app_py_above_the_window_notes_once_and_serves`
- Test: the app module run twice in one process as `bokeh_app_a`/`bokeh_app_b` under patched 3.10.0 → one note line; under 3.7.3 → RuntimeError with the refusal and no root on `curdoc()` — `::test_bokeh_serve_notes_once_and_refuses_below_the_floor`
- Test: the text `main()` warns equals the app's `_dash_bokeh_check()[1]`, and `_dash_relay_kind("(note:  " + note + ")")` returns `("note", note, False)`, so `said=` skips it — `::test_dash_serve_prints_the_note_once`

`test/test_setup_pep668.py`, new class `TestTheBokehWindow`:
- Test: `bokeh_requirement` for `""`, `None`, `"3.7.3"`, `"3.9.2"`, `"garbage"` → `bokeh>=3.8,<3.10`; `"3.10.0"`, `"3.10.0rc1"`, `"4.1"` → `bokeh>=3.8`; each fullmatches `_SPEC_RE`; `floor="3.8; rm"` → ValueError — `::test_the_requirement_never_downgrades`
- Test: a recorded `stata_venv` run on a new venv installs `bokeh>=3.8,<3.10`; on a reused venv whose probe reports 3.10.0, `bokeh>=3.8` and the "left as it is" line; reused with 3.9.0, the ceiling — `::test_the_venv_route_downgrades_nothing`
- Test: `VERIFY_CODE` with `bokeh_ceil` `3.10` reports `above == ["bokeh"]` for 3.10.0 and `[]` for 3.9.2, `ok` unchanged — `::test_verify_reports_above_without_failing`

`test/test_label_sinks_browser.py` (new; module skip without Chrome as `test_by_scales_chrome.py` does, red under `DASH_STRICT=1`; guard at the base under 3.8 and 3.9): through S04's `_CspProbe`, the saved page and a `python app.py` app with `y` labelled with E4's payload: literal text in the axis title, legend and hovered tooltip, no IMG (shadow roots too), `document.title` unchanged — `TestTheTextSinksInChrome::test_the_label_stays_text[saved|served]`

Cscript: BK-01..BK-06, HON-50..HON-56, BK-20..BK-23 (Stata truth).

### Commit 2 regression tests, new `test/test_bokeh_internals.py` (red on the commit-1 tree unless marked guard; 41-14)

- Test: `FILE` monkeypatched to a template lacking `preamble` (and, separately, `inner_body`) → `_dash_served_template()` raises RuntimeError naming the block and `Content-Security-Policy` (today: silent, no CSP) — `TestTheTemplateFailsClosed::test_a_template_without_the_blocks_is_refused`
- Test: `_dash_check_served_template()` passes under the real Bokeh; with `_dash_nonce_scripts` patched to sign nothing → RuntimeError; with two metas → RuntimeError; a script body holding `"<script>"` does not trip it — `::test_the_probe_page_is_counted`
- Test (`serve`): an app whose `FILE` lacks `preamble` (patched in a boot script) exits 2 under `python app.py` with the message, and `bokeh serve`'s module run raises it — `::test_the_server_does_not_start`
- Test: `file_html` patched to return a page with `<HEAD>` (and one with two metas) → `DashRenderer` raises `DashScriptPolicyError` and no file is written, both saved paths — `TestTheSavedHeadFailsClosed::test_a_page_without_its_policy_is_not_written`
- Guard: a label holding `<meta http-equiv="Content-Security-Policy" content="x">` is written normally — `::test_user_text_is_not_counted`
- Test: `bokeh.server.util.match_host` deleted → RuntimeError naming it (today AttributeError) — `TestTheOriginCheckFailsClosed::test_a_missing_matcher_is_a_named_error`
- Test: `match_host` monkeypatched to a lenient prefix matcher (3.8's behaviour), then the generated app module run as `bokeh_app_o` (the bokeh-serve branch) → `check_allowlist("localhost.dash-origin-check.invalid:1", ["localhost:1"])` is False afterwards (today True: `bokeh serve` keeps the lenient matcher); a second run as `bokeh_app_p` raises nothing — `::test_bokeh_serve_hardens_the_origin_check` (Q-41.1)
- Test: `check_allowlist` replaced by a prefix matcher (critic t3) → RuntimeError (today False and the lenient check stays) — `::test_a_matcher_the_handler_ignores_is_refused`
- Guard: under the real Bokeh the probe ends rejected and the return value is unchanged (3.8: True, 3.9: False) — `::test_the_real_bokeh_passes`
- Test: `AuthProvider.get_user_async` replaced by a plain method → `_dash_token_auth(key)` raises RuntimeError naming the hook — `TestTheKeyCheckFailsClosed::test_a_renamed_hook_is_a_named_error`
- Test: `bokeh.util.token.get_token_payload` patched to raise ImportError, and separately `generate_jwt_token` patched to omit `__bk__zlib_` → named RuntimeError at `_dash_token_auth` (today: an unusable server) — `::test_a_changed_token_layout_is_a_named_error`
- Test (`serve`): with the hook renamed in a boot script, `python app.py` exits 2 with the message and never prints `Bokeh Server running` — `::test_the_launcher_stops_with_the_message`
- Test: `_DASH_BOKEH_INTERNALS` is a tuple of string triples; each guard names functions defined in dash_render.py; each test's file exists and its class and function are defined (AST) — `TestTheInternalsList::test_every_entry_names_a_guard_and_a_test`
- Test: the generated app defines `_DASH_BOKEH_INTERNALS`, `_dash_check_served_template`, `_dash_check_auth_internals`, and calls the template check before `Server(` and in the bokeh-serve branch — `TestTheInternalsList::test_the_app_runs_the_guards`
- Test: dash.sthlp's Server Mode holds "refuses to start" and "page template's blocks" — `TestTheHelp::test_server_mode_says_what_fails_closed`
- Test: CHANGELOG.md's `### Requirements` holds `bokeh>=3.8,<3.10` and `(WP-30, P1.30)`, and `### Security` holds `refuses to start` and `(WP-30, P1.30)` (red until 41-20 replaces the markers) — `TestTheChangelog::test_requirements_and_security_name_the_window`

### Pinned tests to flip (R9; re-measured, never trusted)

Commit 1 (41-08 to 41-12): E7's list, each with a `Flipped:` line: `TestBokehVersion` to major.minor; `test_every_declaration_agrees_with_dash_setup`'s Requires and Dependencies assertions to `bokeh>=%s,<%s` (with `max_bokeh` read like `min_bokeh`); S05's `test_each_file_pins_its_baseline_exactly` to `_mm(pin) in VERIFIED_BOKEH`; HON-20, HON-22, HON-29, `HON_SB_EXPECT`, PC-19, PC-21 and the PC/PEP vectors (:983, :1024, :1039, :1056, :1087) to `bokeh>=3.8,<3.10`; `test_setup_python_gate.cscript:178` to `'bokeh>=3.8,<3.10'`; `test_help_examples.cscript:550-552` and `test_help_examples.py:518` to the new help lines. If the ceiling is 3.11: `test_floor_matrix.py`'s `fresh prints bokeh>=3.8,<3.10` and `scripts/floor_matrix.sh`'s spec. Commit 2: none expected.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| bokeh 3.10 | 41-01: full run through the queue in `$S/venv-s41-bk310`, internals probe, bundle reading, Chrome sinks | E4 payload | yes (saved, `python app.py`) |
| Window verdict and declarations | `TestTheWindowVerdict`, `TestTheWindowIsDeclaredOnce` | repository files | n/a |
| Run-time check | `TestTheRuntimeCheck`, `TestTheServedAppChecksAtStart`; BK-20..BK-23 | sysuse auto, `_DF` | yes (saved; `dash build, server`; `python app.py`; `bokeh serve`; `dash serve` dedupe) |
| dash_setup | BK-01..BK-06, HON-50..HON-56; `TestTheBokehWindow` | sandbox fakes | n/a |
| Text sinks | `test_label_sinks.py` (flipped), `test_label_sinks_browser.py` (Chrome) | payload | yes |
| Internals fail closed | `test_bokeh_internals.py` | monkeypatched Bokeh | yes (saved seal; served launcher and bokeh serve) |
| Registries, tracking | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_cscript_hygiene.py`, `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads`, `test_tracking_documents.py`, `test_floor_matrix.py` | — | n/a |

**Acceptance criteria.**
- **AC-41.1** (BR-41.1, BR-41.2) HON-50..HON-56 and BK-01..BK-06 PASS; `TestTheBokehWindow` passes; every pip vector or line `dash_setup` builds for bokeh carries the ceiling unless bokeh is already at or above it.
- **AC-41.2** (BR-41.3) `TestTheRuntimeCheck` and `TestTheServedAppChecksAtStart` pass (the `serve` nodes not skipped); BK-20..BK-23 PASS.
- **AC-41.3** (BR-41.4) `test_label_sinks.py` and `test_label_sinks_browser.py` pass under both baselines with no skip; `VERIFIED_ON` covers the window; `$S/41-bk310-verdict.txt` records the 3.10 decision with its evidence.
- **AC-41.4** (BR-41.5) `test_bokeh_internals.py` passes; every failure message names the internal, the version and `dash_setup`.
- **AC-41.5** (BR-41.6) `TestTheWindowIsDeclaredOnce` passes; `grep -rn "bokeh>=3.8\"\|bokeh>=3.8'" dash.pkg dash.sthlp dash_setup.sthlp dash_setup.ado` finds no line without the ceiling.
- **AC-41.6** Every flipped node passes with a `Flipped:` line; none deleted; each commit's full run through the queue reports 0 failed; G7 prints 0 before and after each commit; `stata19.rc` is unchanged.

## Tasks

**Commit boundary.** Tasks 41-01 to 41-13 form commit 1, made by 41-13 on `wp30-s41` with the subject `Install and check bokeh inside one verified window, part 1 of 2: the window (WP-30 P1.30)`; it leaves the BUGS.md entry, its `WP30_OPEN` key and both markers in place (A156). Tasks 41-14 to 41-20 form commit 2, made by 41-20 with the subject `Refuse to serve when the Bokeh internals dash relies on change, part 2 of 2: internals fail closed (WP-30 P1.30)`; it closes all three. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s41`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`; every command uses `git -C "$WT"` or `$WT` paths. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S41 "$SLOT" "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`). Each task appends the files it changed to `$S/41-files-<k>.txt` (k = 1 or 2).

<task type="auto" id="41-01">
  <name>Verify bokeh 3.10 in a scratch venv</name>
  <files>none</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-14-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s41`; stop otherwise. Record `shasum ~/.stata19/console/stata19.rc` in `$S/41-rc-before.txt`. Build `$S/venv-s41-bk310` and install `bokeh==3.10.*` exactly as TR-41.1 gives (wheels only, scratch cache; nothing outside the venv, M10/E12). Launch the leg in the background, `PATH="$S/venv-s41-bk310/gatevenv/bin:$PATH" DASH_BASELINE=dev "$S/full_suite_queue.sh" "$WT" "$S/41-bk310-full.log"`, and wait for its `exit=` line (never relaunch it). Meanwhile write and run under the venv's Python `$S/41-bk310-internals.py` (E5's probes, with `_dash_served_template()` from the base tree) and `$S/41-bk310-sinks.py` (TestBokehVersion steps 2-3 in headless Chrome through `$WT/test/test_csp_browser.py`'s `_CspProbe`), and record step 1 (the bundle reading) in `$S/41-bk310-sinks.txt`. Judge by TR-41.1 and write `3.11` or `3.10` to `$S/41-ceiling.txt` and the evidence (the leg's summary line and drift warning, each probe line, the sink results) to `$S/41-bk310-verdict.txt`.
  ]]></action>
  <verify><![CDATA[`cat "$S/41-ceiling.txt"` prints `3.10` or `3.11`; `"$S/venv-s41-bk310/gatevenv/bin/python" -c "import bokeh; print(bokeh.__version__[:4])"` prints `3.10`; `grep -c "exit=" "$S/41-bk310-full.log"` prints 1; `shasum ~/.stata19/console/stata19.rc` equals `$S/41-rc-before.txt`; `git -C "$WT" status --porcelain` prints nothing.]]></verify>
  <done>Bokeh 3.10 had been run through the full suite, the internals probes and the browser text-sink checks in a scratch venv, and the ceiling was fixed by that evidence.</done>
</task>

<task type="auto" id="41-02">
  <name>Write the window regression tests</name>
  <files>test/test_bokeh_window.py, test/test_setup_pep668.py, test/test_label_sinks_browser.py</files>
  <action><![CDATA[
    Create `test/test_bokeh_window.py` with every commit-1 stub of "TDD test stubs", naming `dr._dash_bokeh_window`, `dr._dash_bokeh_check`, `dr._DASH_BOKEH_FLOOR`, `_CEIL`, `_VERIFIED` and `lib.bokeh_requirement` so they fail with AttributeError now; the expected ceiling comes from `$S/41-ceiling.txt` (written into the test as a literal). Add class `TestTheBokehWindow` to `test/test_setup_pep668.py` after its last class, reusing its recorded-run fixtures. Create `test/test_label_sinks_browser.py` (guard) on S04's `_CspProbe` and `test_server_serves._Launched`. Run `python3 -m pytest test/test_bokeh_window.py test/test_setup_pep668.py test/test_label_sinks_browser.py -q -n 6 -p no:cacheprovider -rA > "$S/41-new-1.log" 2>&1`. Write `$S/41-P1.30-1-failure.txt`: the base sha, one line per failing node with its first error line, then "Guards (pass at the base)" with the browser nodes. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "^FAILED" "$S/41-new-1.log"` is at least 25; `grep -c "^PASSED test/test_label_sinks_browser.py" "$S/41-new-1.log"` prints 2 and `grep -c "SKIPPED.*test_label_sinks_browser" "$S/41-new-1.log"` prints 0; `git -C "$WT" diff --name-only -- dash_render.py dash_setup.ado dash_setup_lib.py` prints nothing.]]></verify>
  <done>Every commit-1 pytest regression test was shown failing on the unmodified tree, and the browser text-sink guard passed under the base Bokeh, with the failure text saved.</done>
</task>

<task type="auto" id="41-03">
  <name>Write the setup and truth cases</name>
  <files>test/test_setup_version_gate.cscript, test/test_setup_honesty.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Before first use, `grep -rn "BK-[0-9]\|HON-5[0-9]" "$WT/test"/*.cscript "$WT/test"/*.py "$WT/test"/*.do` must print nothing. Add BK-01..BK-06 to `test_setup_version_gate.cscript`, HON-50..HON-56 to `test_setup_honesty.cscript`, and the `_s41_notes` helper plus BK-20..BK-23 to the S41 block of `test_wp30_truth.cscript`, each exactly where and as "Stata truth" says, with the ceiling from `$S/41-ceiling.txt`, in each script's own PASS/FAIL form. Use no `capture python:` import line. Run the three scripts through the driver on the unmodified shipped files. Append to `$S/41-P1.30-1-failure.txt` each `BK-nn`/`HON-nn` FAIL line with the line it quotes; BK-05 and BK-23 are guards. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "BK-0[1-4] FAIL|BK-06 FAIL" "$S/run_test_setup_version_gate.log"` is at least 3; `grep -cE "HON-5[0-6] FAIL" "$S/run_test_setup_honesty.log"` is at least 4; `grep -cE "BK-2[0-2] FAIL" "$S/run_test_wp30_truth.log"` is at least 2; `grep -c "SVG-05 PASS" "$S/run_test_setup_version_gate.log"` prints 1.]]></verify>
  <done>The setup-gate, dash_setup and run-time cases were in their scripts and shown failing on the unmodified tree, with the guards passing.</done>
</task>

<task type="auto" id="41-04">
  <name>Add the window to the renderer</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    State in the task log that `main` is HIGH (index 14.0) before editing it. Apply TR-41.2 (the constants with the ceiling of `$S/41-ceiling.txt`, `_dash_bokeh_window`, `_dash_bokeh_check`, each with a docstring citing M9, A104 and the threat, directly after S25's `_dash_dep_versions`), change `_dash_dep_versions`' refusal element only, and apply TR-41.3 to `main` (after `_validate_output_path`). Add TR-41.11's two `FUNCTIONS` entries under S41's anchor, alphabetically. Edit nothing else.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bokeh_window.py -q -n0 -p no:cacheprovider -k "Verdict or RuntimeCheck"` passes; `python3 -m pytest test/test_dependency_guards.py test/test_function_test_map.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The renderer held one verified window, refused a bokeh below it and noted one above it at the top of every render.</done>
</task>

<task type="auto" id="41-05">
  <name>Check the window at app start</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Confirm `$S/batch-14-impact.txt` records the HIGH warnings for `_generate_app_source` and `_glyph_layer_lines` before editing. Apply TR-41.4 (the section-5 block, before `"if __name__ != '__main__':"`) and TR-41.5 (the two copy-list lines at S41's anchors, after S39's and S40's names only if they share an anchor, which they do not). Change no other line of either function.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bokeh_window.py -q -n 6 -p no:cacheprovider` passes except `TestTheWindowIsDeclaredOnce`; `python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads test/test_server.py test/test_serve_launcher.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The served app checked its bokeh at start under python app.py and bokeh serve, refusing below the floor and noting once per process above the window.</done>
</task>

<task type="auto" id="41-06">
  <name>Bound dash_setup's installs and gate</name>
  <files>dash_setup.ado</files>
  <action><![CDATA[
    `dash_setup`, `_dash_setup_gate`, `_dash_pip_command` and `_dash_setup_venv` are UNKNOWN to the index; their callers were confirmed by grep (Risk). Apply TR-41.6: `max_bokeh` beside `min_bokeh` with its comment, the in-place spec, `maxver` in the version loop, the gate's optional fifth argument and `above` verdict, the `above` branch (managed guidance or the manual line, never an install), `_dash_pip_command`'s optional fourth argument, and `_dash_setup_venv`'s fifth. Keep `got` out of every Python line except through `getLocal`. Edit no other program.
  ]]></action>
  <verify><![CDATA[`test_setup_version_gate.cscript` through the driver prints `BK-01 PASS` to `BK-06 PASS` and `ALL CHECKS PASSED`; `test_setup_injection.cscript` through the driver prints its all-passed line; `python3 -m pytest test/test_cscript_hygiene.py test/test_version_floor.py -q -n 6 -p no:cacheprovider` reports 0 failed except the declaration assertion 41-10 flips.]]></verify>
  <done>dash_setup installed bokeh only inside the window and reported a newer one as outside the verified range without changing it.</done>
</task>

<task type="auto" id="41-07">
  <name>Keep venv() from downgrading bokeh</name>
  <files>dash_setup_lib.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-41.7: `bokeh_requirement` after `pip_install_argv`, `stata_venv`'s `bokeh_ceil`, the reused-venv probe through `verify_in`, the requirement from `bokeh_requirement`, the "left as it is" line, and `VERIFY_CODE`'s `above` list. Do not edit `pip_install_argv`, `_SPEC_RE` or `stata_shell_line`. Add the `SETUP_FUNCTIONS` entry of TR-41.11 under S41's anchor.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_setup_pep668.py test/test_function_test_map.py -q -n 6 -p no:cacheprovider` reports 0 failed; `test_setup_honesty.cscript` through the driver prints `HON-50 PASS` to `HON-56 PASS` (its older cases flipped by 41-09 may still fail).]]></verify>
  <done>A venv dash created got bokeh inside the window, and a reused venv's newer bokeh was left as it was and reported.</done>
</task>

<task type="auto" id="41-08">
  <name>Tie the text sinks to the window</name>
  <files>test/test_label_sinks.py, test/requirements-stata.txt, test/requirements-dev.txt</files>
  <action><![CDATA[
    Apply TR-41.9: `VERIFIED_BOKEH` from `dr._DASH_BOKEH_VERIFIED`, `VERIFIED_ON` (3.10's row only if `$S/41-ceiling.txt` reads 3.11, dated from `$S/41-bk310-verdict.txt`), the flipped assertion and the docstring's step 4; add `TestBokehVersion::test_every_minor_in_the_window_was_verified` (keys equal the window's minors). Apply TR-41.8 to both requirements files. Write the `Flipped:` line to `$S/41-flips-1.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_label_sinks.py test/test_bokeh_window.py test/test_floor_matrix.py -q -n 6 -p no:cacheprovider` reports 0 failed except `test_each_file_pins_its_baseline_exactly` (41-10) and the help declarations (41-11); `/opt/anaconda3/bin/python3 -m pytest test/test_label_sinks.py -q -n0 -p no:cacheprovider -k BokehVersion` passes under bokeh 3.8.]]></verify>
  <done>The text-sink verification was held to every minor of the window, and both requirements files named the window.</done>
</task>

<task type="auto" id="41-09">
  <name>Flip the setup cscript pins</name>
  <files>test/test_program_coverage.cscript, test/test_setup_honesty.cscript, test/test_setup_python_gate.cscript</files>
  <action><![CDATA[
    Run the three scripts through the driver and list every FAIL; each must be one of E7's nodes (PC-19, PC-21, :983, :1024, :1039, :1056, :1087; HON-20, HON-22, HON-29, `HON_SB_EXPECT`; the python-gate line :176-178), else stop and report. Flip each in place to the ceilinged spec (`bokeh>=3.8,<3.10` in vectors, `'bokeh>=3.8,<3.10'` in printed lines), with a `// Flipped (WP-30 P1.30): …` comment line, and append each `Flipped:` line to `$S/41-flips-1.txt`. Delete no case.
  ]]></action>
  <verify><![CDATA[Each of the three scripts through the driver prints its own all-passed line and no `FAIL`; `grep -c "Flipped (WP-30 P1.30)" "$WT/test/test_program_coverage.cscript"` is at least 2.]]></verify>
  <done>Every setup case that pinned an unbounded bokeh spec asserted the window, with the reason recorded.</done>
</task>

<task type="auto" id="41-10">
  <name>Flip the declaration pins</name>
  <files>test/test_version_floor.py, test/test_floor_matrix.py, scripts/floor_matrix.sh</files>
  <action><![CDATA[
    Flip `test_every_declaration_agrees_with_dash_setup` (read `max_bokeh` beside `min_bokeh`; the Requires and Dependencies assertions as `bokeh>=%s,<%s`; its CHANGELOG assertion `bokeh >= %s` stays true and is left as it is: the ceiling's CHANGELOG line is pinned by `test_bokeh_internals.py::TestTheChangelog`) and S05's `test_each_file_pins_its_baseline_exactly` (`_mm(pin) in VERIFIED_BOKEH`). Only if the ceiling is 3.11: `scripts/floor_matrix.sh`'s fresh spec and `test_floor_matrix.py`'s dry-run expectation to `<3.11`. Re-measure `test/test_setup_sandbox.py:276`: it is the sandbox's own pip call, left as it is unless it fails. Append the `Flipped:` lines to `$S/41-flips-1.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_version_floor.py test/test_floor_matrix.py test/test_setup_sandbox.py -q -n 6 -p no:cacheprovider` reports 0 failed except the dash.pkg and help assertions 41-11 satisfies.]]></verify>
  <done>The declaration and pins-file tests asserted the window instead of an unbounded floor.</done>
</task>

<task type="auto" id="41-11">
  <name>Declare the window in help</name>
  <files>dash.pkg, dash.sthlp, dash_setup.sthlp</files>
  <action><![CDATA[
    Apply TR-41.10 with the ceiling of `$S/41-ceiling.txt`: dash.pkg's Requires line; the Dependencies paragraph of dash.sthlp; dash_setup.sthlp :98, :137, the verified-range paragraph after S05's minimums paragraph, :166, :185-187, :241, :247. Find each place by its text. Edit no other paragraph (R3); every new or changed line at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bokeh_window.py test/test_version_floor.py test/test_help_conformance.py -q -n 6 -p no:cacheprovider` reports 0 failed; `awk 'length > 79' "$WT/dash_setup.sthlp" | grep -c "bokeh"` prints 0.]]></verify>
  <done>The package file and both help files declared the one window and what dash does outside it.</done>
</task>

<task type="auto" id="41-12">
  <name>Flip the help example pins</name>
  <files>test/test_help_examples.cscript, test/test_help_examples.py</files>
  <action><![CDATA[
    Flip `test_help_examples.cscript` :550-552 (`_hx_pin` lines) and `test_help_examples.py:518` to the help's new pip lines, in place, with a comment naming WP-30 P1.30. Append the `Flipped:` lines to `$S/41-flips-1.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_examples.py -q -n 6 -p no:cacheprovider` reports 0 failed; `test_help_examples.cscript` through the driver prints its all-passed line.]]></verify>
  <done>The help-example pins read the ceilinged pip lines.</done>
</task>

<task type="auto" id="41-13">
  <name>Run the suite and make commit 1</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_bokeh_window.py test_setup_pep668.py test_label_sinks.py test_label_sinks_browser.py test_version_floor.py test_floor_matrix.py test_function_test_map.py test_cscript_hygiene.py test_tracking_documents.py` with `-n 6`, and the four changed setup scripts plus the S41 truth block through the driver. Run `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run `"$S/full_suite_queue.sh" "$WT" "$S/41-full-1.log"` in the background, read when `exit=` appears (E6 for the known flaky tests). Stage exactly the files of `$S/41-files-1.txt`; check `git -C "$WT" diff --cached --name-only` equals it (G6). Write `$S/41-message-1.txt` in the form of "Notes: commit messages", naming commit 1's threat (TR-41.21); check G7, confirm the branch, commit, check G7 on the committed message.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/41-full-1.log"` shows 0 failed and `exit=0`; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.30)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.30 -->' "$WT/CHANGELOG.md"` prints 2 (left for commit 2).]]></verify>
  <done>Commit 1 bounded bokeh to one verified window in dash_setup and checked it at run time in both modes, green, with the entry, key and markers left for commit 2.</done>
</task>

<task type="auto" id="41-14">
  <name>Write the internals regression tests</name>
  <files>test/test_bokeh_internals.py</files>
  <action><![CDATA[
    On the tree commit 1 left, create `test/test_bokeh_internals.py` with every commit-2 stub, naming `dr._dash_check_served_template`, `dr._dash_check_auth_internals` and `dr._DASH_BOKEH_INTERNALS`. Patch Bokeh only through `monkeypatch` (or a boot script for the `serve` nodes) after the imports of "TDD test stubs". Run it with `-n 6 -rA` into `$S/41-new-2.log`. Write `$S/41-P1.30-2-failure.txt`: commit 1's sha, one line per failing node with its first error line (for the template node, that no error was raised and the page held no policy), then the guards that pass. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "^FAILED" "$S/41-new-2.log"` is at least 12; `grep -cE "^PASSED .*(test_user_text_is_not_counted|test_the_real_bokeh_passes)" "$S/41-new-2.log"` prints 2; `git -C "$WT" diff --name-only -- dash_render.py dash.sthlp` prints nothing.]]></verify>
  <done>Every commit-2 regression test was shown failing on the tree commit 1 left, with the guards passing and the failure text saved.</done>
</task>

<task type="auto" id="41-15">
  <name>Make the page templates fail closed</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    `_dash_served_template` is UNKNOWN to the index (generated-text caller at `make_document`); `_dash_seal_saved_page` was measured at the base. Apply TR-41.12 (the block check), TR-41.13 (`_dash_check_served_template`, scanning script elements as `_dash_nonce_scripts` does) and TR-41.14 (the head count in the seal). Leave the success paths byte for byte as they were.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bokeh_internals.py -q -n 6 -p no:cacheprovider -k "Template or SavedHead"` passes except `test_the_server_does_not_start` (41-17); `python3 -m pytest test/test_csp.py test/test_varlist_expansion.py test/test_mode_parity.py test/test_served_bs_layout.py -q -n 6 -p no:cacheprovider` reports 0 failed (the single-y digest unchanged).]]></verify>
  <done>A Bokeh whose template or page head no longer carried dash's policy got a named refusal instead of a page without one, in both modes.</done>
</task>

<task type="auto" id="41-16">
  <name>Make the origin and key checks fail closed</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    `_dash_harden_origin_check` and `_dash_token_auth` are UNKNOWN to the index (launcher text callers); `_dash_ws_payload` is LOW and not edited. Apply TR-41.15 (named errors and the post-hardening probe of `check_allowlist`), TR-41.16 (`_dash_check_auth_internals` above `_dash_token_auth`) and TR-41.17 (the check first in `_dash_token_auth`, and the override assertion).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bokeh_internals.py -q -n 6 -p no:cacheprovider -k "Origin or KeyCheck"` passes except `test_the_launcher_stops_with_the_message` (41-17); `python3 -m pytest test/test_adversarial_matrix.py test/test_serve_token.py test/test_server_serves.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>A Bokeh without the origin matcher, with a handler that ignores it, or with a changed key-check hook or token layout got a named error instead of an open or unusable server.</done>
</task>

<task type="auto" id="41-17">
  <name>List the internals and wire the launcher</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    `_generate_app_source` and `_glyph_layer_lines` are HIGH (warn). Apply TR-41.18 (`_DASH_BOKEH_INTERNALS` after `_DASH_BOKEH_VERIFIED`, with the node ids checked against this tree: `grep -n "class TestTheDateTransformUnderTheCsp" test/test_csp_browser.py`, `ls test/test_default_axes_chrome.py`, the Gate B test in `test/test_serve_token.py`) and TR-41.19 (the launcher calls, the bokeh-serve branch's template check and origin hardening, and the copy-list names). Add TR-41.20's two `FUNCTIONS` entries under S41's anchor.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bokeh_internals.py -q -n 6 -p no:cacheprovider` passes except `TestTheHelp` and `TestTheChangelog`; `python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads test/test_function_test_map.py test/test_csp_browser.py test/test_serve_launcher.py -q -n 6 -p no:cacheprovider` reports 0 failed, no skip.]]></verify>
  <done>The internals list named every Bokeh internal with its guard and test, and the app ran the template check before it served under both launchers.</done>
</task>

<task type="auto" id="41-18">
  <name>Document what fails closed in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-41.20's help to Server Mode: the reworded `bokeh serve` sentence of the origin paragraph (found by "uses Bokeh's own check") and the new paragraph after it. Edit no other paragraph (R3; S04's and S23's paragraphs stay); lines at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bokeh_internals.py::TestTheHelp test/test_help_conformance.py test/test_csp.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The help said what the served app does when a Bokeh release changes the internals its protection relies on.</done>
</task>

<task type="auto" id="41-19">
  <name>Re-run the guards under bokeh 3.10</name>
  <files>none</files>
  <action><![CDATA[
    Only if `$S/41-ceiling.txt` reads 3.11; otherwise write "skipped: 3.10 not verified" to `$S/41-bk310-guards.log` and stop. Run, with the venv's interpreter and node on PATH, `"$S/venv-s41-bk310/gatevenv/bin/python" -m pytest test/test_bokeh_window.py test/test_bokeh_internals.py test/test_label_sinks.py test/test_label_sinks_browser.py test/test_csp_browser.py -q -n 6 -p no:cacheprovider -rs > "$S/41-bk310-guards.log" 2>&1` from `$WT`. A failure here reverses 41-01's verdict: stop and report to the orchestrator, who decides between fixing the guard and returning the ceiling to 3.10 (41-04, 41-08, 41-10, 41-11 re-applied).
  ]]></action>
  <verify><![CDATA[`tail -1 "$S/41-bk310-guards.log"` shows 0 failed and no skipped, or the file reads `skipped: 3.10 not verified`; `shasum ~/.stata19/console/stata19.rc` equals `$S/41-rc-before.txt`.]]></verify>
  <done>The window's run-time check, the internals guards and the text-sink checks were shown green under bokeh 3.10 whenever the ceiling admitted it.</done>
</task>

<task type="auto" id="41-20">
  <name>Close the entry and make commit 2</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.30"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution", today's date as `ddmonyyyy`. Delete the `"P1.30"` key line of `WP30_OPEN`. Replace the `<!-- WP-30 P1.30 -->` markers in place, one under `### Requirements` and one under `### Security`, with "Notes: CHANGELOG lines" (ceiling and verified list from `$S/41-ceiling.txt`). Run `test_tracking_documents.py test_version_floor.py test_bokeh_window.py test_bokeh_internals.py test_cscript_hygiene.py` with `-n 6` and the S41 truth block through the driver; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/41-full-2.log"` in the background, read when `exit=` appears. Stage exactly `$S/41-files-2.txt` plus these three; check the staged list (G6); write `$S/41-message-2.txt` naming commit 2's threats (TR-41.21); G7, branch, commit, G7; report both shas, both messages and `$S/41-bk310-verdict.txt` to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/41-full-2.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.30 -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.30": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -2 --format=%s` shows both subjects ending `(WP-30 P1.30)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.30 was closed naming its tests, its two markers carried the window and the fail-closed guards, and two green commits on wp30-s41 were ready for the merger.</done>
</task>

## Section completion criteria

- bokeh 3.10 was run in a scratch venv (full suite, internals probe, browser text sinks), and the ceiling (`<3.10`, or `<3.11` if all green) follows that evidence (M9, M10, E12; `stata19.rc` unchanged).
- `dash_setup` installs inside the window in place and into a venv it creates, never downgrades a bokeh at or above the ceiling, reports it `outside the verified range` (rc 0, a warning), and follows the managed-Python rule (BK-01..BK-06, HON-50..HON-56).
- Every `dash` command, `python app.py` and `bokeh serve` refuse a bokeh below 3.8 and note one above the window once (per command or per process), `dash serve` included without a repeat (BK-20..BK-23, `TestTheRuntimeCheck`, `TestTheServedAppChecksAtStart`).
- `VERIFIED_BOKEH` is the window, each minor has a browser check on record, and the browser test runs in every baseline.
- Template blocks, the saved head, the origin matcher, the AuthProvider hook and the token layout fail closed with named errors; `_DASH_BOKEH_INTERNALS` lists them (and the BokehJS calls of S21 and S35) for S54 to extend.
- `_dash_bokeh_window`, `_dash_bokeh_check`, `_dash_check_served_template`, `_dash_check_auth_internals` and `bokeh_requirement` exist and are mapped; the served copy lists carry the constants and helpers at S41's anchors.
- Every pinned node is flipped with its reason; none is deleted; two green commits `(WP-30 P1.30)` exist on `wp30-s41`, the second closing the entry, its key and both markers.

## Notes

- **Q-41.1, resolved by the review (no maintainer question).** `bokeh serve app.py` kept Bokeh's own origin matcher (dash.sthlp:1693: "run it under Bokeh 3.9 or later"). Inside the window that left bokeh 3.8's lenient matcher governing `bokeh serve`, which fails open on the very internal that register P1.30.9/A109 says must fail closed ("the origin guard asserts that check_allowlist rejects the probe"). Project rule 1 asks for every exploitable surface to be hardened at once. The fix is one generated line in the bokeh-serve branch, which S41 already edits for the template check (TR-41.19), plus one help sentence (TR-41.20) and one test (`TestTheOriginCheckFailsClosed::test_bokeh_serve_hardens_the_origin_check`), so S41 does it. User-visible change: under bokeh 3.8, `bokeh serve` now refuses a websocket from a look-alike origin (`localhost.example.com` for `localhost`), as `python app.py` already does (CHANGELOG Security line). No P2 residual is filed.
- **Why the 3.10 leg runs first and non-strict.** Verifying first means commit 1 writes the final window once, and the leg exercises the unmodified base; commit 2's guards are then re-run under 3.10 by 41-19. `scripts/floor_matrix.sh run` is strict and stops on any bokeh drift from its baseline, so the leg uses the queue's pytest mode with the venv first on `PATH`, and checks "no skipped" and "drift names bokeh only" itself.
- **S25's note slot is not used for bokeh.** S25 prints `_dash_dep_versions()[1]` once per renderer load; M9's note belongs to every run, so it is raised in `main()` (S06's scope) and in the app (S23's hook). The refusal uses S25's slot, read on every load, so Stata refuses before any render.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the setup scripts and the truth block then SKIP or fail. Check the file after each slot run; a SKIP is not a pass.
- **Merge rules for the shared files.**
  - R1: BK-01..BK-06 at the end of `test_setup_version_gate.cscript`; HON-50..HON-56 as one run in `test_setup_honesty.cscript` (S03, S05, S25 wrote theirs in earlier batches); S41's truth block and helper in their own places; `test_cscript_hygiene.py:322` unchanged (no captured import probe).
  - R2: constants after `"_DASH_LINK_UNWRITTEN",`, functions after `"_dash_harden_origin_check",`; map entries under S41's anchors in `FUNCTIONS` and `SETUP_FUNCTIONS`; the `COVERAGE` anchors stay empty.
  - R3: dash.sthlp Dependencies and Server Mode; dash_setup.sthlp's dependency paragraphs.
  - R4/R5: the two `P1.30` markers (Requirements, Security), the entry and its key, by commit 2 only.
  - R6: every edited dash_setup.ado program keeps `version 19`; the guard order (A154) is untouched.
  - R9: E7's flips. R10: no combined pin moves.
  - R12: S41 is batch 14's only editor of `_generate_app_source`; it edits neither `_make_figure_body` nor `_build_filter_widgets`.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name, for commit 1, `main`, `_dash_dep_versions`, `_dash_bokeh_window`, `_dash_bokeh_check`, the three constants, `ServerAppBuilder._generate_app_source`, `ServerAppBuilder._glyph_layer_lines`, `bokeh_requirement`, `stata_venv`, `VERIFY_CODE`; for commit 2, `_dash_served_template`, `_dash_check_served_template`, `_dash_seal_saved_page`, `_dash_harden_origin_check`, `_dash_check_auth_internals`, `_dash_token_auth`, `_DASH_BOKEH_INTERNALS`, `_generate_app_source`, `_glyph_layer_lines`; plus test symbols of the staged files.
- **Commit messages.** Subjects as in "Commit boundary". Body, in order: the failure file (`$S/41-P1.30-1-failure.txt` / `-2-`); the measured defect (Overview's block; for commit 1 also `$S/41-bk310-verdict.txt`'s summary); the threat closed (TR-41.21, G9); what changed and where (TR-41.1-TR-41.11 / TR-41.12-TR-41.20, both modes); then one line each: `Regression: test/test_bokeh_window.py::<Class>::<test> -- failed at <base sha> with <text>` per node (cscripts as `test/test_setup_version_gate.cscript BK-01`, `test/test_setup_honesty.cscript HON-50`, `test/test_wp30_truth.cscript BK-20`); the `Flipped:` lines, e.g. `Flipped: test/test_label_sinks.py::TestBokehVersion::test_bokeh_is_a_version_this_was_verified_on -- exact patch versions were wrong because a patch release inherits its minor's verification (A104)`; commit 1 `BUGS.md: "<title>" (open; closed by part 2)`, commit 2 `BUGS.md: "<WP30_OPEN["P1.30"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place; ceiling and verified list from `$S/41-ceiling.txt`):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.30). One bokeh window, bokeh>=3.8,<3.10 (dash_render.py _DASH_BOKEH_FLOOR, _DASH_BOKEH_CEIL, _DASH_BOKEH_VERIFIED; dash_setup.ado min_bokeh, max_bokeh; dash.pkg; both help files; the requirements files), verified by major.minor; bokeh 3.10 was <verified in a scratch environment and admitted | run in a scratch environment and not admitted: <reason>>. dash_setup installs inside it in place and into a venv it creates, never downgrades a bokeh at or above the ceiling (dash_setup_lib.bokeh_requirement; a reused venv is probed first), and reports one as outside the verified range, a warning with rc 0 (_dash_setup_gate's above verdict; managed Pythons get the venv guidance, never a pip line). Every dash command reads bokeh.__version__ (_dash_bokeh_check): below 3.8 it is refused r(198) naming dash_setup (S25's _dash_dep_versions slot), above the window main() notes it once per command; the served app checks at start, exiting under python app.py and refusing each bokeh serve session below the floor and noting once per process above it, and dash serve prints the note once. The text-sink checks run in a browser for every minor of the window (test_label_sinks.py VERIFIED_BOKEH, VERIFIED_ON; test_label_sinks_browser.py). The Bokeh internals dash's security relies on fail closed with named errors: the template blocks (_dash_served_template, _dash_check_served_template), the saved page's head (_dash_seal_saved_page), match_host and check_allowlist (_dash_harden_origin_check), the AuthProvider hook and the session-token layout (_dash_check_auth_internals, _dash_token_auth); _DASH_BOKEH_INTERNALS lists each with its guard and test. Pinned by test/test_bokeh_window.py::TestTheRuntimeCheck::test_below_the_floor_is_refused_naming_dash_setup, test/test_bokeh_window.py::TestTheServedAppChecksAtStart::test_python_app_py_above_the_window_notes_once_and_serves, test/test_bokeh_window.py::TestTheWindowIsDeclaredOnce::test_every_declaration_names_the_window, test/test_setup_pep668.py::TestTheBokehWindow::test_the_requirement_never_downgrades, test/test_bokeh_internals.py::TestTheTemplateFailsClosed::test_a_template_without_the_blocks_is_refused, test/test_bokeh_internals.py::TestTheOriginCheckFailsClosed::test_a_matcher_the_handler_ignores_is_refused, test/test_bokeh_internals.py::TestTheKeyCheckFailsClosed::test_a_renamed_hook_is_a_named_error, test/test_label_sinks_browser.py::TestTheTextSinksInChrome::test_the_label_stays_text, test/test_setup_version_gate.cscript BK-01, test/test_setup_honesty.cscript HON-50, test/test_wp30_truth.cscript BK-20. Residual, deferred (WP-30): hash-pinned installs (OQ7) and the dev-dependency declarations of GAPS2-K5-d stay with P3.9.
  ```
- **CHANGELOG lines** (each replaces its marker in place; the `###` lines only say which list):

  ```
  ### Requirements
  - bokeh has a ceiling: `dash_setup` installs `bokeh>=3.8,<3.10` (it installed `bokeh>=3.8`, which resolved to the unverified 3.10.0), the versions dash was verified on (any patch release of 3.8 or 3.9). A bokeh at or above 3.10 that you already have is left as it is and reported as "outside the verified range", a warning; `dash` then draws and prints one note. A bokeh below 3.8 is refused when `dash` runs (it used to render with no word). Only bokeh has a ceiling. (WP-30, P1.30)

  ### Security
  - The served app refuses to start, and a saved page is not written, when a bokeh release changes what dash's protections rely on: the page template's blocks that carry the Content-Security-Policy and script nonce (a template without them served a page with no policy), the saved page's head, the websocket origin matcher (a handler that stopped using it re-admitted look-alike origins; `bokeh serve app.py` now makes Bokeh's origin check exact as `python app.py` does, where under bokeh 3.8 it admitted any origin that began with an allowed host), and the key check's AuthProvider hook and token layout (a renamed hook let every request in). Each stops with one message naming the internal and `dash_setup`. The label, legend and tooltip injection checks run in a browser for every bokeh version in the window. (WP-30, P1.30)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md H4** (:1529): H4b-e closed by `<sha1>`, `<sha2>` (S05 closed H4g); the Tracked line names both sections' commits. **I7** (:1660) is tracked through H4. **K5** (:1861): K5-a, K5-b, K5-c closed by `<sha1>`, `<sha2>`; K5-d stays with P3.9 (IR-16). **K2** (:1811): its residual "no … bokeh below the floor is run by any test" is closed for bokeh by the run-time refusal tests.
  - **DROPIN-REMAINING.md:164** (P1.30): "Closed by <sha1>, <sha2> (WP-30 S41)."
  - **ROADMAP:** P3.9 notes the requirements files carry the bokeh window comment; the next bokeh minor needs a re-verification leg (TR-41.1's recipe) before the ceiling rises.
  - **AGENTS.md invariant:** "the bokeh window is declared once (`_DASH_BOKEH_*`; `min_bokeh`/`max_bokeh`), pinned by `TestTheWindowIsDeclaredOnce`; every Bokeh internal dash's security relies on is on `_DASH_BOKEH_INTERNALS` with a guard that fails closed."
  - **Unverified:** Linux and Windows (M4); Firefox and Safari for the text sinks (the platform package).
