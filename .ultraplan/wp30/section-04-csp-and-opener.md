# Section 04: CSP without 'unsafe-inline'; safe Windows opener (P1.29, M11)

> Part of: WP-30 · Items: P1.29 (entry `P1.29`) · Risk: yellow · Batch: 2 · Depends on: 02 · Blocks: 12, 41, 46, 54 · Tasks: 16, 1 commit · Case prefixes: CSP; SB-21..30, PV-28..34

## Review amendments

- Major: the extractor's root lines (`: env DASH_REPO`, exit 198 when unset) were not S02's TR-02.9 stanza that A130/R7 require; they are now the stanza verbatim (c(pwd) fallback, six-character refusal, r(601)), and the Run line uses the worktree's slot.
- Major: the S04 truth block printed its own PASS lines and wrote to an unnamed `<work>`; CSP-01..04 now report through `_w30_expect`/`_w30_done`, write only under `` `w30_work' `` and erase their pages (TR-01.10.4); 04-13 also requires `ALL CHECKS PASSED`.
- Major: SB-29/SB-30 sat after an `assert sb_fail == ""` placed after SB-28, so at the base they never ran although 04-01 records them failing; the assert now follows SB-30. 04-11's verify expected 18 PASS and no FAIL while SB-28's help paragraph only lands in 04-14; it now expects 17 PASS with SB-28 alone failing, and 04-14 requires all SB-13..30 to pass.
- Minor: `$S` was this review session's scratch path; now `<scratch>/s04` like every other section.
- Spot-checked at HEAD: `_DASH_CSP_STANDALONE` :3682-3685, `_DASH_SECURITY_HEADERS` :3714-3716, `_dash_csp_meta` :3722, `_dash_served_template` :3756/:3786-3790, `_CSP_META` :4459-4462, `_render_bootstrap_html` :30857 (:30973-30978, :31107), `_assemble_layout` :32408 (:32585, :32592-32594), `_glyph_layer_lines` :32834, `_generate_app_source` :33915, `_dash_open_page` dash.ado:5781, `_needed` :236-250, dash.sthlp:924-926 and :1728-1730. All hold.
- Batch 2: S04 and S06 both add one name to `_dash_require_mata`'s `_needed` list (S04 :242, S06 :247) and one header-index entry; R6 allows this in-place data edit on distinct lines, so it is not a shared-function conflict. No other program, renderer function or help paragraph is shared with S05 or S06.
- Checked: M11 (opener declines `% ! ^ & | < > ;` on Windows, writes and prints the path, rc 0; validator unchanged until S12), M5 not engaged (nothing newly refused), A99/A102/A103 obeyed. No open question touches S04.
- Rejected: none.

- (cross-file pass) 04-16 verify: added the key-deletion check `grep -c '^    "P1.29": "' $WT/test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:163 (P1.29) reads: "Both CSPs keep `unsafe-inline`; they need hashes or a nonce, plus a browser test. `%` and `!` in saving paths reach Windows `start` via cmd.exe; whether they expand there is UNCLEAR (unmeasured on Windows). The help does not state saving()'s character rule." Its sources are GAPS2-I12-a/b/c and GAPS2-I14-c/d (GAPS2.md:1675-1709). GAPS2-I12's gap line: "dash.sthlp presents the CSP as a protection. Yet `_DASH_CSP_STANDALONE` and `_DASH_CSP_SERVED` both allow `script-src 'unsafe-inline' 'unsafe-eval'` … BUGS.md:1337 records that the WP-20 slider-title XSS handler ran because of `'unsafe-inline'`. Escaping is the only barrier."

Measured at `c96facd` (research p1-29.md §2, re-checked for this file):
- **Saved page.** An `<img src=x onerror=…>` and an inline `<script>` injected into a saved page both **run** in headless Chrome under today's policy (`inj_img_ran=True inj_script_ran=True`). With script-src set to the SHA-256 of the page's own scripts plus `'unsafe-eval'`, both are blocked and the dropdown's CustomJS still changes the views.
- **Served page.** The same injection runs under `python app.py` and `bokeh serve`. With a per-page nonce in the `<meta>` policy, both are blocked and a Select move still round-trips to the server.
- **Help.** dash.sthlp:1728-1730 says "A saved dashboard may run only the scripts and styles written into it", which is not what `'unsafe-inline'` enforces.
- **Windows opener.** `_dash_open_page, path("C:\Users\me\pct%PATH%x.html") os(Windows) dryrun` returns `r(cmd) = start "" "C:\Users\me\pct%PATH%x.html"`, rc 0. cmd.exe expands `%NAME%` inside double quotes, so `start` could open a file other than the one written. The same holds for `!` (delayed expansion), `^`, and, once S12 lets them into `saving()`, `& | < > ;`.
- **Help, saving().** dash.sthlp:924-926 says only "must end in .html; no .. traversal allowed". Nothing lists the refused characters, and nothing says what Windows does.

**After this section.**
- The saved page's script-src lists the SHA-256 hash of every inline script Bokeh writes, plus `'unsafe-eval'`, and no `'unsafe-inline'`. dash refuses to write a saved page holding an executable inline script it did not hash (A98).
- The served page's `<meta>` policy names a fresh nonce for each page (one `make_document` call per session, one page per session). Every script element of the page carries it. script-src is nonce-only if the browser test is clean (A102; measured clean on 03oct2026, below). The `python app.py` header policy is unchanged (A99).
- The empty page and the link/redirect page carry `default-src 'none'` (A103).
- `'unsafe-eval'` and `style-src 'unsafe-inline'` stay, because BokehJS needs them (measured).
- A headless-Chrome test of both modes shows an injected inline script and handler blocked, before and after a filter move, while the page still renders, filters, hovers and exports.
- On Windows, `_dash_open_page` builds no command and runs nothing for a path holding `% ! ^ & | < > ;`. The page is still written, its path is printed, `r(opened)=0` and `r(why)="metachar"` are returned, and the rc is 0 (M11, P1.29.1, P1.29.7).
- The help states what the policy does and does not protect, the `saving()` character rule as it stands at this commit, and the Windows written-not-opened rule.

**Why one section.** Both halves harden what the user's browser is handed: the page's policy and the command that opens it. The manifest keeps them together so the opener lands before S12 widens `saving()` (M11). The shared truth fixture `saving_chars_truth.json` is created here, and S12 reads it.

**Test order and commit rule (rule 7, A156).** One entry and one commit.
- **04-01** writes every regression test and runs it against the unmodified tree (the batch-2 base). It saves `$S/04-P1.29-failure.txt` and never commits.
- **04-02 to 04-14** make the fix, flip the pins, add the fixture and the guards, and update the help.
- **04-15** verifies.
- **04-16** closes the entry, replaces the marker, runs the full suite through the queue and makes the one commit, `(WP-30 P1.29)`.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every saved and served page's policy changes; two CRITICAL renderer functions and one HIGH generator are edited

**Why.** A policy that drops `'unsafe-inline'` and misses one of the page's own scripts gives a blank dashboard. Every saved page goes through `_assemble_layout` (CRITICAL, 12 impacted) and `_render_bootstrap_html` (CRITICAL, 6). Every served page goes through the generated `make_document` (`_generate_app_source`, HIGH, 5).

**Risk factors.**
1. A script Bokeh writes is missed by the hash scan (an attribute form, case, a module script), and the page goes blank.
2. Line endings: a page written with CRLF on Windows hashes differently unless the hash is taken over the LF text.
3. Hashing the final page would bless a script an escaping fault let into dash's own HTML. That would make the seal vacuous.
4. The served template's nonce filter rewrites text inside a script's body (an INLINE bundle can hold the string `<script`: `bokeh-tables.min.js` holds it twice, measured), which would corrupt that bundle.
5. A name missing from the served copy lists is a NameError on the served page only.
6. The browser harnesses (`responsive_probe.with_probe`, `test_stale_cue_browser._page`) inject inline probe scripts, which the new policies block. About ten Chrome tests would turn red for a harness reason.
7. Nonce-only may refuse a script BokehJS inserts at run time without the nonce (D6 of the research: MathJax, GL).
8. The Windows decline changes three pinned SB cases whose hostile Windows path holds `;` and `&`.

**Mitigation.**
1. `_dash_script_hashes` is unit-tested on attribute forms, case, `type` values, `src=`, JSON blocks and unclosed elements. The browser test asserts zero violations on six saved page families (auto, bs, rich, formats, >10k rows WebGL, KPI brush), in both modes.
2. Hashes are taken over the LF form (`\r\n` and `\r` to `\n`). The research measured a CRLF-written page working.
3. Hashes are taken over Bokeh's fragments only (`file_html` output in `_assemble_layout`; `_extracted_head` and the `components()` script in `_render_bootstrap_html`). `_dash_seal_saved_page` then refuses any executable inline script of the final page outside that set (A98). `TestAHostileFragmentIsNotAdmitted` proves the seal fires.
4. `_dash_nonce_scripts` adds the nonce to each script element's opening tag and skips to that element's `</script`, so it never edits a script's body (prototype below). It is unit-tested with a body holding `"<script>"`.
5. A149's `test_every_listed_name_exists`, `TestTheServedApp::test_the_helpers_are_the_renderers_own_text` (extended) and `TestTheServedAppDefinesEveryNameItReads` (G4).
6. Task 04-07 gives the harnesses a test-only `admit_script` that adds the probe's own hash, or the page's nonce, to the page copy under test. Production is not weakened.
7. Measured nonce-only clean on the rich served app under bokeh 3.9.0 and 3.8.0 (below). 04-08 re-measures across the whole browser matrix and falls back to `'self'` with the reason recorded if any case shows a violation (A102).
8. The flips are named in "Evidence" and carry `Flipped:` lines. A new Windows hostile path without metacharacters (SB-24) keeps the quoting coverage.

## Dependencies

- **Depends on: 02.** The extractor `scripts/extract_saving_chars_truth.do` copies S02's path-free form (`DASH_REPO`, A130). It runs through `scripts/stata_slot.sh` as S02 left it. Through the batch base it also needs S01's entry `P1.29`, its `WP30_OPEN` key, the CHANGELOG marker `<!-- WP-30 P1.29 -->` at the end of `### Security`, the `# WP-30 S04 (P1.29): …` anchors in both maps, and the S04 stub block of `test/test_wp30_truth.cscript`. S03's `version 19` sweep has landed, so dash.ado's programs read `version 19`.
- **Blocks: 12, 41, 46, 54.**
  - S12 widens `saving()` to `; & | < >` and `..` (M11) only after this opener declines them on Windows. It rewrites this section's `saving()` paragraph to the final rule, flips SB-28's `..` needle with it, and reads `saving_chars_truth.json`.
  - S41's template guard must count this section's FILE blocks (`preamble`, `js_resources`, `inner_body`).
  - S46's busy and idle pages run under these policies.
  - S54's Save-as-SVG action runs under them and extends `test_csp_browser.py`.
- **Parallel batch: 2, merge order S04, S05, S06** (index "Batch 2"). S04 lands first.
- **Can run with:** S05 (Python floor) and S06 (one note channel). Neither edits the page assembly, the served template, the generated `doc.template` line, `_dash_open_page` or the CSP tests. S06 does edit dash.ado's `_needed` list and dash_parse.mata's header index, on other lines (Notes, R6).

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines; dash.ado 8,487; dash_parse.mata 6,093; dash.sthlp 3,822). Batch 1 (S01-S03) does not edit dash_render.py, and S03's sweep replaces `version 16.0` lines one for one, so these numbers hold at the batch-2 base. Symbols are authoritative if lines drift.

### The policies today (dash_render.py:3660-3792)

`_DASH_CSP_STANDALONE`, dash_render.py:3682-3692:
```python
3682 _DASH_CSP_STANDALONE = (
3683     "default-src 'none'; "
3684     "script-src 'unsafe-inline' 'unsafe-eval'; "
3685     "style-src 'unsafe-inline'; "
3686     "img-src data: blob:; "
3687     "font-src data:; "
3688     "connect-src 'none'; "
```
`_DASH_CSP_SERVED`, :3699-3709 (`script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; …`). It is also the header's source, `_DASH_SECURITY_HEADERS`, :3714-3719:
```python
3714 _DASH_SECURITY_HEADERS = (
3715     ("Content-Security-Policy", _DASH_CSP_SERVED + "; frame-ancestors 'none'"),
3716     ("X-Content-Type-Options", "nosniff"),
```
`_dash_csp_meta` (:3722-3753; LOW, 8 impacted) refuses anything outside `[A-Za-z0-9 '*+\-./:;=_]`. That whitelist already admits `'sha256-<base64>='` and `'nonce-<token_urlsafe>'`, and it refuses a Jinja `{{ }}` (research §2). So GAPS2's "extend the whitelist" step is not needed, and its body stays unchanged (manifest). The nonce is therefore baked into the template text per page, never passed as a template variable.

`_dash_served_template`, :3756-3792 (UNKNOWN in GitNexus; callers by grep: the generated `make_document` :34724, test_csp.py ×3, test_mode_parity.py:2111, test_served_bs_layout.py:872, test_responsive_layout.py:214):
```python
3786     from bokeh.core.templates import FILE
3787     return FILE.environment.from_string(
3788         "{% extends base %}\n"
3789         "{% block preamble %}{{ super() }}    "
3790         + _dash_csp_meta(_DASH_CSP_SERVED)
3791         + "\n    " + _DASH_VIEWPORT_META
3792         + "\n{% endblock %}",
```
Its docstring (:3766-3769) says "No literal tag names here: this text is copied into the generated app, whose source is checked for a raw script tag". The check is test_server.py:599-607, which refuses `"<script>"` (with the `>`) on every non-base64 line of the app. 04-04 rewrites that sentence (critic 4).

The saved meta is a module constant, `_CSP_META`, dash_render.py:4459-4462:
```python
4459 _CSP_META = (
4460     _dash_csp_meta(_DASH_CSP_STANDALONE)
4461     + "\n" + _DASH_VIEWPORT_META
4462 )
```
It is spliced at the two assembly sites:
- `_render_bootstrap_html` (def :30857; CRITICAL, 6 impacted), :31099-31119:
  ```python
  31104             # A <meta> policy governs only what the page parses after it, …
  31107             f"  {_CSP_META}\n"
  31108             f"{_extracted_head}\n"
  …
  31114             "<body>\n"
  31115             f"{script_tag}\n"
  31116             '<div class="db-container">\n'
  31117             f"{page_body_html}"
  ```
  `_extracted_head` comes from `self._head_of_file_html(file_html(_dummy_col, INLINE, …))` (:30985-30986), and `script_tag` from `components(all_models)` (:30989). `page_body_html` (header, filter bar, tabs, grid) is dash's own HTML (escaped by `_dash_header_fragments`, :25460).
- `_assemble_layout` (def :32408; CRITICAL, 12 impacted), :32585-32596:
  ```python
  32585         html_str = file_html(layout_root, INLINE, title=title_text or "dash")
  32591         _scheme_css = self.scheme.css_style_element()
  32592         html_str = html_str.replace(
  32593             "<head>",
  32594             f"<head>\n    {_CSP_META}\n{_scheme_css}",
  ```
- The empty page has no policy and no viewport, :30973-30978:
  ```python
  30973         if not all_models:
  30974             return (
  30975                 "<!DOCTYPE html><html><body>"
  30976                 "<p style='font-family:sans-serif'>No dashboard content.</p>"
  30977                 "</body></html>"
  ```
  Under `default-src 'none'` its `style=` attribute would be blocked, so 04-03 drops the attribute.
- The redirect/link page, `_dash_redirect_page` (:4216-4226; LOW; callers `_dash_open_tokenized`, `_dash_write_link`, `_dash_announce_key`, `_dash_bokeh_serve_key`, `_dash_launch_app`), has no policy. It is on the served functions copy list (:33422).

The generated app sets the template once per document, dash_render.py:34712-34724:
```python
34712             "def make_document(doc):",
…
34724             "    doc.template = _dash_served_template()",
```

Copy-list anchors (index R2 row S04; `ServerAppBuilder._glyph_layer_lines`):
- constants tuple, :32955-32956:
  ```python
  32955                       "_DASH_CSP_SERVED", "_DASH_SECURITY_HEADERS",
  32956                       "_DASH_VIEWPORT_META",
  ```
- functions tuple, :33289-33290:
  ```python
  33289                          "_dash_csp_meta", "_dash_served_template",
  33290                          "_dash_server_transforms",
  ```

### Measurements (03oct2026, at `c96facd`)

**Script census of saved pages** (scratch `hash_proto.py`; `test_csp._standalone_page`; bokeh 3.9.0):
```
auto 1739670 scripts 5 types ['', 'application/json'] exec-inline 4 unique hashes 4
bs   1745726 scripts 4 types [''] exec-inline 4 unique hashes 4
hash scan ms per 1.7MB page: 7.1
```
dash's own pages carry no inline event handler and no `javascript:` URL (research §2). Every executable inline script is Bokeh's: the bundles, `set_log_level` and the embed script.

**Saved page in Chrome** (research §2, `csp_chrome.py`, bokeh 3.8.0 and 3.9.0):
```
saved_auto.html head  inj_img_ran=True  inj_script_ran=True  customjs_changed_views=True
saved_auto.html hash  inj_img_ran=False inj_script_ran=False customjs_changed_views=True
saved_auto.html hash-noeval ... customjs_changed_views=False + script-src eval (function anonymous(source,orig_source,a
rich_auto.html hash   (tabs, csv, dropdown+range, filterposition(left), by(), colorvar, KPI, hover, $$\beta$$ title)  only the two injected violations
```
Without `style-src 'unsafe-inline'`, Chrome reported 884 `style-src-elem` and 9 `style-src-attr` violations (BokehJS shadow-root styles).

**Served page, nonce-only vs nonce plus `'self'`** (scratch `s04/nonce/nonce_only.py`, which reuses the research's `served_chrome_lib.variant` on its rich app; `python app.py` through `test_server_serves._Launched`; the header policy present):
```
python3 3.14 / bokeh 3.9.0
nonce     | script-src 'self' 'nonce-…' 'unsafe-eval'   docs=1 inj_img=False inj_script=False
   violations=['script-src-elem inline window.__inj_script=1;', 'script-src-attr inline window.__inj_img=1']
   scripts: inline+n,src+n,src+n,src+n,src+n,src+n,inline+n,inline+n,inline+n,inline-n,inline+n
   select->1 server update changed CDS: True; violations after move: (the same two)
nonceonly | script-src 'nonce-…' 'unsafe-eval'          (identical result)
/opt/anaconda3 python 3.13.9 / bokeh 3.8.0: identical for both variants
```
The one `inline-n` script is the probe's injected one. So nonce-only is clean on the rich app. GL above 10,000 rows, formatters, hover and the KPI brush are measured by 04-08 (A102).

**The nonce template prototype** (scratch `s04/tpl_proto.py`, both Bokeh versions): blocks `js_resources` and `inner_body` are overridden with a nonce helper passed as a template global.
```
3.9.0 len(N) 24
script tags 5 nonce'd 4          (the 5th is the text "<script>" inside a script body, left alone)
rest is Bokeh's page: True       (strip the two metas and every nonce attribute: FILE.render(ctx) exactly)
3.8.0 (identical)
HEAD template build ms/each: 0.550    (one compile per session)
```

**The opener and twoway** (StataNow 19.5, `c(os)=Unix c(machine_type)=Mac (Apple Silicon)`; scratch `s04/s04_probe.do`, `s04/s04_open.do`, run through `scripts/stata_slot.sh`):
```
TW [pct%PATH%x] rc=0 literal=1     DASH [pct%PATH%x] rc=0 literal=1
TW [bang!x!y]   rc=0 literal=1     DASH [bang!x!y]   rc=0 literal=1
TW [pct%%x]     rc=0 literal=1     DASH [pct%%x]     rc=0 literal=1
TW [caret^x]    rc=0 literal=1     DASH [caret^x]    rc=0 literal=1
TW [R&D] [a;b] [a|b] [a<b] [a>b]   rc=0 literal=1    DASH rc=198 literal=0   (S12's half)
TW [..] rc=0 resolved=1            DASH [..] rc=198                          (S12's half)
OPEN rc=0  r(cmd)=[start "" "C:\Users\me\pct%PATH%x.html"] opened=0
OPEN rc=0  r(cmd)=[start "" "C:\Users\me\caret^x.html"] opened=0
OPEN rc=0  r(cmd)=[start "" "C:\a b\x (86).html"] opened=0
OPEN rc=0  r(cmd)=[start "" "C:\Users\me\bang!x!y.html"] opened=0
OPENMAC rc=0  r(cmd)=[open '/tmp/pct%PATH%x!y.html']
```
twoway writes these names literally and runs no shell for `saving()`, so dash keeps accepting `%`, `!`, `^` and `%%`. Only dash's own opener is exposed. Whether cmd.exe expands them is unmeasurable here (M4) and is taken from cmd.exe's documented behaviour (research §2).

### The opener (dash.ado:5750-5835; Stata, UNKNOWN in GitNexus; callers by grep: `_dash_render_immediate` :6826, `_dash_build` :8254)

The Windows branch, dash.ado:5812-5819:
```stata
5812     if "`os'" == "Windows" {
5813         mata: st_local("_op_dq", strofreal(strpos(st_local("path"), char(34)) > 0))
5814         if `_op_dq' {
5815             display as error "dash: a Windows path cannot hold a double quote; the page was not opened."
5816             exit 198
5817         }
5818         mata: st_local("cmd", "start " + char(34) + char(34) + " " + char(34) + st_local("path") + char(34))
5819     }
```
The run, dash.ado:5825-5834:
```stata
5825     local opened 0
5826     if "`dryrun'" == "" & "${dash_nobrowser}" == "" {
5827         mata: st_local("_op_rc", strofreal(_stata("shell " + st_local("cmd"), 0, 1)))
5828         local opened 1
5829     }
5830     return local os "`os'"
5831     return local cmd : copy local cmd
5832     return scalar opened = `opened'
```
The one-line form calls the opener instead of printing "dashboard saved to" (dash.ado:6822-6831). So the decline branch must print the path itself. `dash build` prints "dash: dashboard saved to …" first (:8244).

`_dash_path_badchar` (dash_parse.mata:619-630) is the byte-scan model the new Mata function copies:
```mata
619 real scalar _dash_path_badchar(string scalar path) {
620     real scalar      i, c, n
621     real rowvector   bad
623     bad = (34, 96, 36, 59, 38, 124, 60, 62, 9, 10, 13)
```
`_dash_validate_path` (dash.ado:453-544) refuses `" \` $ ; & | < >`, TAB/LF/CR, a `..` segment and a leading `-`, and requires the extension. Python's `_validate_output_path` (dash_render.py:36678) refuses `..`, a leading `-` and every control character. That is the character rule at this commit; S12 changes it.

`_dash_require_mata`'s `_needed` list (dash.ado:237-250) must name every Mata function dash.ado calls (test_program_coverage_map.py:343-365). The new function goes after `_dash_path_badchar` on :242.

### The help today

- dash.sthlp:924-926: `{synopt:{cmdab:sav:ing}{cmd:(}{it:filepath}{cmd:)}}required; path to the output HTML file (must end in {cmd:.html}; no {cmd:..} traversal allowed){p_end}`. The server row is at :946-948.
- dash.sthlp:1727-1737 (Server Mode):
  ```
  1728 The page carries a Content-Security-Policy in both modes.  A saved dashboard
  1729 may run only the scripts and styles written into it and may load nothing
  1730 from anywhere; a served one may also load from, and connect to, the server
  ```
  `test_csp.py::TestTheHelpSaysWhatIsSent` pins four phrases of this paragraph, and the rewrite keeps them.
- dash_render.py:39-46 (module docstring) repeats the claim and is corrected in 04-02.

### Existing tests that pin today's behaviour (flipped, never deleted)

Flipped in 04-06 (each with a `Flipped:` line; the executor re-measures this list on the fixed tree, R9):
- `test/test_csp.py::TestThePolicyConstants::test_the_standalone_policy_is_exactly_the_verified_one`: `STANDALONE_TEXT`/`STANDALONE` lose `'unsafe-inline'` from script-src.
- `test/test_csp.py::TestThePolicyConstants::test_the_standalone_meta_is_built_from_the_constant` and `::test_the_viewport_tag_is_kept`: they read `_CSP_META`, which becomes `_dash_saved_head(hashes)`.
- `test/test_csp.py::TestThePolicyConstants::test_no_policy_admits_another_origin` and `test/test_csp.py::TestTheStandalonePages::test_no_directive_admits_another_origin`: `_assert_no_other_origin` refuses any source outside `_KEYWORDS`/`_SCHEMES`. It now also admits only the exact patterns `'sha256-[A-Za-z0-9+/]{43}='` and `'nonce-[A-Za-z0-9_-]{22,64}'`.
- `test/test_csp.py::TestTheStandalonePages::test_the_page_carries_exactly_the_policy`: script-src becomes `{'unsafe-eval'}` plus exactly the page's script hashes.
- `test/test_csp.py::TestTheServedTemplate::test_it_is_bokehs_page_plus_the_two_metas`: rewritten, not re-pinned (critic 1). It keeps its name (the map names it). It strips the two metas and every ` nonce="N"`, and what is left equals `FILE.render(ctx)`.
- `test/test_csp.py::TestTheServedTemplate::test_the_policy_is_in_the_head_ahead_of_everything` and `::test_it_names_its_base_itself`: `SERVED` becomes the meta's policy with the nonce.
- `test/test_csp.py::TestTheServedApp::test_make_document_sets_the_template` and `::test_a_refused_session_is_served_under_the_policy_too`: the same.
- `test/test_csp.py::TestThePythonLauncherServes::test_the_page_carries_the_meta` and `test/test_csp.py::TestBokehServeServes::test_the_page_carries_the_meta`: the same.
- `test/test_served_bs_layout.py::TestTheServedPageDeclaresTheSavedPagesViewport::test_one_viewport_after_the_policy` (:877) and `test/test_help_claims_4.py::TestTheLauncherServes::test_the_page_has_a_mobile_viewport` (:1787) read `dr._CSP_META`. They read `dr._dash_saved_head([])` instead.
- `test/test_serve_browser.cscript` SB-15, SB-19 and SB-20, sixth call: the hostile Windows path `_sb_W` holds `;` and `&`, so it is now declined (`r(cmd)==""`, nothing reaches the stub, `r(why)=="metachar"`). The quoting coverage moves to SB-24's new hostile path without metacharacters.

Extended without a flip (new parameters or names): `test_csp.py::TestThePolicyConstants::test_no_meta_policy_carries_frame_ancestors` (+ `_DASH_CSP_SERVED_META`, `_DASH_CSP_NO_SCRIPTS`), `TestTheMetaWriter::test_every_policy_dash_writes_is_accepted` (+ a hashed and a nonce'd policy), `TestTheServedApp::test_the_source_defines_the_policy_constants` (+ the two new constants), `TestTheServedApp::test_the_helpers_are_the_renderers_own_text` (+ `_dash_new_nonce`, `_dash_csp_served`, `_dash_nonce_scripts`), and `test_responsive_layout.py::TestTheProbe::test_with_probe_goes_before_body_end`.

Red for a harness reason only, until 04-07: `test_responsive_layout.py::TestPagesFitInChrome::test_saved_page_fits`, `::TestServedDocumentsFitInChrome::test_served_document_fits`, `::TestTheServedBsGridReflowsAsTheSavedOne::test_cards_and_canvases_agree` and `test_stale_cue_browser.py::TestInChrome::test_bokehjs_marks_and_clears`. Their probe `<script>` is unhashed and un-nonced.

Guards that must stay green unchanged:
- `test_csp.py::TestThePolicyConstants::test_the_served_policy_is_exactly_the_verified_one` and `::test_the_headers_are_exactly_four` (A99: `_DASH_CSP_SERVED` byte-identical);
- `TestThePythonLauncherServes::test_the_page_carries_the_headers`;
- `TestBokehServeServes::test_it_sends_no_security_header`;
- `test_mode_parity.py::TestThePagesHeads::test_both_pages_declare_one_viewport` (no-argument template call: default nonce);
- `test_serve_token.py::TestTheTokenHelpers::test_the_redirect_page_escapes_and_sends_no_referrer`;
- `test_packaging.py`'s one-shell-site test (:510-540);
- `test_abbreviations.py:599-610`;
- `test_server.py`'s Layer-1 raw `<script>` check (:599-607);
- `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline`. Its digest covers only the document JSON (`normalise_bokeh_html`, :150-170), which this section does not change, so R10's digest is expected not to move. If it moves, stop and diagnose.
- `test_by_scales_chrome.py` (DevTools; must still pass under the hash policy);
- SB-13, SB-14, SB-16 to SB-18;
- HC2-30.

Docstrings that state the old policy (text only, 04-09): test_csp.py's module docstring (:28-31), test_html_output.py:1917, test_label_sinks.py:1189, test_responsive_layout.py:204 (quotes the old `doc.template` line), and test_server.py:9879-9881 (says SB-15 covers a Windows path holding `;` and `&`).

## User stories

- **US-04.1** As a dashboard publisher, I want a saved dashboard to run only the scripts dash wrote into it, so that a script or event handler that slipped into the page some other way never runs in my readers' browsers.
- **US-04.2** As a dashboard publisher, I want each served page to run only scripts carrying that page's own one-time nonce, under `python app.py` and `bokeh serve` alike, so that an injected script is refused on the served app too.
- **US-04.3** As a dashboard reader, I want the hardened page to render, filter, hover, brush and export exactly as before, so that the protection costs me nothing.
- **US-04.4** As a Windows user, I want a page whose path holds `%`, `!`, `^`, `&`, `|`, `<`, `>` or `;` to be written and its path printed rather than handed to cmd.exe, so that dash never opens a different file than the one it wrote.
- **US-04.5** As a twoway user, I want `saving()` to accept `%`, `!` and `^` in a path as twoway does, and the help to state which characters dash refuses and what it does on Windows, so that I can name my files as I name my graphs.

## Business requirements

- **BR-04.1** The saved page's script policy names every inline script dash writes and no `'unsafe-inline'`. A page holding an inline script dash did not name is not written, and dash stops with a named error. (BR-30.29)
- **BR-04.2** Each served page carries a policy naming a nonce that differs on every page. Every script of the page carries it. The policy is nonce-only unless a measured case needs `'self'`, in which case the reason is recorded. The `python app.py` header keeps its policy, and the page's own policy refuses injected scripts. (BR-30.29, A99, A102)
- **BR-04.3** `'unsafe-eval'` and inline styles stay, and the help says why. The empty page and the link/redirect page carry `default-src 'none'`. (BR-30.29, A103)
- **BR-04.4** In Chrome, in both modes, an injected inline script and an injected inline handler are blocked before and after a filter move. The page renders with no policy violation of its own, filters, hovers, brushes and exports (CSV and the toolbar's PNG). (BR-30.29, I12-c)
- **BR-04.5** On Windows, a page whose path holds `% ! ^ & | < > ;` is written and its path printed. Nothing is passed to the shell, the opener reports `r(opened)=0` and `r(why)="metachar"`, and the command ends rc 0. Previews follow the same rule. Mac and Unix open such paths as before. (BR-30.29, M11, P1.29.1, P1.29.7)
- **BR-04.6** `saving()` accepts `%`, `!`, `^` and `%%` and writes the file under the name as typed, as twoway does (fixture). (P1.27's half is S12's.)
- **BR-04.7** The help states the `saving()` character rule at this commit, the Windows written-not-opened rule, and what the CSP does and does not protect, including the CSP level 1 blank page [R17]. (I12-a, I12-b, I14-d)

## Technical requirements

**Saved page (dash_render.py, near the CSP block :3660-3792 unless stated):**
- **TR-04.1** `_DASH_CSP_STANDALONE` becomes the saved base policy: `"default-src 'none'; script-src 'unsafe-eval'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"`. Rewrite its comment (:3670-3681) to say that hashes are inserted per page, why `'unsafe-eval'` and `style-src 'unsafe-inline'` stay (measured: `new Function` for CustomJS and the tick formatter; 884 style violations), and that CSP level 1 browsers show a blank page (A101).
- **TR-04.2** `_dash_script_hashes(html: str) -> list[str]`: the sorted, de-duplicated base64 SHA-256 digests (no `sha256-` prefix) of every executable inline script element in `html`.
  - **Scan.** Find an opening tag with `re.compile(r"<script(?=[\s>/])([^>]*)>", re.I)`. Its body is the text up to the next `re.compile(r"</script", re.I)`, or to the end of `html` if there is none.
  - **Executable** means no `type` attribute, or an empty one, or a type that is a JavaScript MIME type or `module` (case-insensitive, trimmed; `text/javascript`, `application/javascript`, `text/ecmascript`, `application/ecmascript`, `module`). A script with a `src` attribute is skipped, and so is any other type (e.g. `application/json`).
  - **Digest** is taken over the body with `\r\n` and then `\r` replaced by `\n`, encoded UTF-8.
  - Raises `TypeError` for a non-string. Bounded: one pass, no backtracking regex over the body.
- **TR-04.3** `_dash_csp_standalone(hashes) -> str`: `_DASH_CSP_STANDALONE` with `'sha256-<h>'` for each distinct `h`, sorted, inserted directly after the single `"script-src "` (the base must hold exactly one; assert). Each `h` must fullmatch `[A-Za-z0-9+/]{43}=`, or `ValueError`.
- **TR-04.4** `_dash_saved_head(hashes) -> str` = `_dash_csp_meta(_dash_csp_standalone(hashes)) + "\n" + _DASH_VIEWPORT_META`. It replaces the module constant `_CSP_META`, which is deleted along with its comment (:4456-4462). Update the block comment at :3663-3669 and the module docstring at :39-46.
- **TR-04.5** `class DashScriptPolicyError(RuntimeError)` (beside `DashSpecError`, :1161) and `_dash_seal_saved_page(page: str, hashes) -> str`.
  - The seal raises `DashScriptPolicyError` when `set(_dash_script_hashes(page)) - set(hashes)` is not empty, and otherwise returns `page`.
  - Message: `"dash: refusing to write a page holding %d inline script(s) dash did not write (sha256 %s); nothing was written."` The hash list is bounded to 200 characters. It holds no user text.
- **TR-04.6** `_assemble_layout`:
  - `hashes = _dash_script_hashes(html_str)` right after `file_html(...)` (:32585), before any splice.
  - The splice (:32592-32596) writes `_dash_saved_head(hashes)` where `_CSP_META` was.
  - It returns `_dash_seal_saved_page(html_str, hashes)`.
- **TR-04.7** `_render_bootstrap_html`:
  - `hashes = _dash_script_hashes(_extracted_head) + _dash_script_hashes(script_tag)` after `components()` (:30989).
  - :31107 writes `_dash_saved_head(hashes)`.
  - It returns `_dash_seal_saved_page(html_str, hashes)`.
  - Never hash `page_body_html`, `header_html` or the final page.
- **TR-04.8** Empty page (:30973-30978): `"<!DOCTYPE html><html><head>" + _dash_csp_meta(_DASH_CSP_NO_SCRIPTS) + "</head><body><p>No dashboard content.</p></body></html>"`, with no `style=` attribute. New constant `_DASH_CSP_NO_SCRIPTS = "default-src 'none'"`, placed after `_DASH_SECURITY_HEADERS` (one constant per policy, :3663).

**Served page:**
- **TR-04.9** `_DASH_CSP_SERVED` (:3699) stays byte-identical as the header's source (A99). Its comment says so. New `_DASH_CSP_SERVED_META`, the meta's base: `"default-src 'none'; script-src 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'"` (nonce-only, A102). If 04-08 finds a violation, script-src becomes `'self' 'unsafe-eval'`, and the comment records the case and the violation.
- **TR-04.10** `_dash_new_nonce() -> str`: `secrets.token_urlsafe(18)` (24 characters, 144 bits), with `import secrets` inside the function.
- **TR-04.11** `_dash_csp_served(nonce) -> str`: `TypeError` unless `nonce` is a str. `ValueError` unless it fullmatches `[A-Za-z0-9_-]{22,64}`. It returns `_DASH_CSP_SERVED_META` with `'nonce-<nonce>'` inserted directly after its single `"script-src "`.
- **TR-04.12** `_dash_nonce_scripts(markup, nonce) -> markupsafe.Markup`: it validates `nonce` as TR-04.11 does. For each opening `<script` tag (`(?=[\s>/])`, case-insensitive), it inserts ` nonce="<nonce>"` right after `<script`, then copies the element's body unchanged through the next `</script` (or the end). Text outside script elements is unchanged. `from markupsafe import Markup` goes inside the function. No literal `<script>` may appear in its source or docstring (test_server.py:599-607).
- **TR-04.13** `_dash_served_template(nonce=None)`:
  - `nonce=None` means `_dash_new_nonce()`, so the no-argument callers (test_mode_parity.py:2111, test_served_bs_layout.py:872, test_responsive_layout.py:214) keep working.
  - The template text: the existing `preamble` override, now with `_dash_csp_meta(_dash_csp_served(nonce))`, plus `"{% block js_resources %}{{ dash_nonce_scripts(super()) }}{% endblock %}\n{% block inner_body %}{{ dash_nonce_scripts(super()) }}{% endblock %}"`.
  - `globals={"base": FILE, "dash_nonce_scripts": functools.partial(_dash_nonce_scripts, nonce=nonce)}`, with `import functools` inside. No lambda: a lambda would need its own `function_test_map.py` key.
  - The docstring's "No literal tag names here" sentence becomes "No complete script tag (`<` + `script>`) here: the generated app's source is checked for one (test_server.py:599-607)". The docstring states the per-page nonce and the FILE blocks it relies on (`preamble`, `js_resources`, `inner_body`; S41 guards them).
- **TR-04.14** Generated `make_document` (:34718-34724): the comment gains "One nonce per document, so one per page: Bokeh renders one page per session (WP-30 P1.29)", and the line becomes `"    doc.template = _dash_served_template(_dash_new_nonce())",`. It is still set before the key and limiter checks, so refused sessions are nonce'd too.
- **TR-04.15** `_dash_redirect_page` (:4216): `_dash_csp_meta(_DASH_CSP_NO_SCRIPTS)` goes directly after `<meta charset="utf-8">`. The escaping and the other metas are unchanged.
- **TR-04.16** Copy lists (R2, append only):
  - constants tuple: `"_DASH_CSP_SERVED_META", "_DASH_CSP_NO_SCRIPTS",` on a new line after `"_DASH_CSP_SERVED", "_DASH_SECURITY_HEADERS",` (:32955);
  - functions tuple: `"_dash_csp_served", "_dash_new_nonce", "_dash_nonce_scripts",` on a new line after `"_dash_csp_meta", "_dash_served_template",` (:33289).
  - Not copied: `_dash_script_hashes`, `_dash_csp_standalone`, `_dash_saved_head`, `_dash_seal_saved_page`, `DashScriptPolicyError` (saved only).
- **TR-04.17** `test/function_test_map.py`, under the `# WP-30 S04 (P1.29): …` anchor, alphabetical:
  - `_dash_csp_served` → `test/test_csp.py::TestTheNonce::test_the_served_policy_names_the_nonce_and_no_unsafe_inline`
  - `_dash_csp_standalone` → `test/test_csp.py::TestTheStandalonePolicy::test_hashes_are_inserted_sorted_and_once`
  - `_dash_new_nonce` → `test/test_csp.py::TestTheNonce::test_a_nonce_is_fresh_and_urlsafe`
  - `_dash_nonce_scripts` → `test/test_csp.py::TestTheServedTemplate::test_only_script_elements_get_the_nonce`
  - `_dash_saved_head` → `test/test_csp.py::TestThePolicyConstants::test_the_standalone_meta_is_built_from_the_constant`
  - `_dash_script_hashes` → `test/test_csp.py::TestTheScriptHashes::test_only_executable_inline_scripts_are_hashed`
  - `_dash_seal_saved_page` → `test/test_csp.py::TestAHostileFragmentIsNotAdmitted::test_the_seal_refuses_an_unhashed_script`

  The existing `_dash_served_template` entry (:640) keeps its node, because the test keeps its name.
- **TR-04.18** No JavaScript changes, so there is no JS twin. CustomJS, the tick and hover formatters and the KPI brush are untouched and run under the kept `'unsafe-eval'`.

**Windows opener (Stata):**
- **TR-04.19** dash_parse.mata: `real scalar _dash_cmd_metachar(string scalar path)` directly after `_dash_path_badchar` (:619-630), in its form. `bad = (37, 33, 94, 38, 124, 60, 62, 59)` (`% ! ^ & | < > ;`); it returns the byte of the first match, or 0, scanning bytes. Its comment cites cmd.exe's `%NAME%` expansion inside quotes, `!` under delayed expansion, `^ & | < > ;` as cmd's escape and separators, M11 and P1.29. The header index gets an entry after `_dash_path_badchar`'s (:42-45): `*!   _dash_cmd_metachar(path)` / `*!       The byte value of the first character Windows' command shell reads in a quoted path -- % ! ^ & | < > ; -- or 0.` dash.ado's `_needed` (:242) gains `_dash_cmd_metachar` after `_dash_path_badchar`.
- **TR-04.20** `_dash_open_page`, Windows branch, after the double-quote refusal (:5813-5817, which keeps its place and r(198)), before the command is built:
  ```stata
  mata: st_local("_op_meta", strofreal(_dash_cmd_metachar(st_local("path"))))
  if `_op_meta' {
      mata: _dash_say("txt", "dash: not opened, because Windows' command shell would read the " + char(`_op_meta') + " in ", st_local("path"), "; open the page yourself.")
      return local os "`os'"
      return local cmd ""
      return local why "metachar"
      return scalar opened = 0
      exit
  }
  ```
  The comment above it states the rule, that it applies with or without dryrun and under `$dash_nobrowser`, rc 0, and M11. The header comment (:5750-5779) gains one sentence on `r(why)`. Mac and Unix are unchanged. The validator is unchanged (twoway accepts `%`, `!`, `^`). The path goes through `_dash_say` (SMCL-escaped, never parsed). `%` in the text is an argument of `printf`, never its format. S06 does not migrate this line (S06 notes).
- **TR-04.21** `test/program_coverage_map.py`:
  - under `COVERAGE["dash_parse.mata"]`'s S04 anchor: `"_dash_cmd_metachar": ("test_serve_browser.cscript:SB-21",)`;
  - in place, `_dash_open_page`'s tuple (:229-231) gains `"test_serve_browser.cscript:SB-22"`.

**Fixture, help, tracking:**
- **TR-04.22** `scripts/extract_saving_chars_truth.do` writes `test/fixtures/saving_chars_truth.json` ("Stata truth"). `test/test_saving_chars.py` (new) reads it. The `test_wp30_truth.cscript` S04 block reads it, and S12's block will.
- **TR-04.23** dash.sthlp:
  - the `saving()` synopt (:924-926) and the `server` synopt (:946-948) point to a new `{marker saving_chars}` paragraph, placed after `{synoptline}` (:953) and before `{marker nobrowser_global}`;
  - the Server Mode CSP paragraph (:1727-1737) is rewritten (texts in task 04-14).
- **TR-04.24** BUGS.md entry `P1.29` closed in place. `WP30_OPEN`'s `"P1.29"` line is deleted. The `<!-- WP-30 P1.29 -->` marker in `### Security` is replaced in place (task 04-16 texts).

## Boundaries

- **Not touched here:**
  - `_dash_csp_meta`'s body;
  - `_DASH_CSP_SERVED`'s value;
  - `_DASH_SECURITY_HEADERS`;
  - `_dash_server_transforms` (A99);
  - `_head_of_file_html` (CRITICAL; read only);
  - `_dash_header_fragments` and `_dash_header_models`;
  - any CustomJS or JS constant;
  - `_dash_validate_path`;
  - `_dash_path_badchar`;
  - `_validate_output_path`;
  - the Mac/Unix opener lines;
  - `_dash_open_tokenized` (the served route opens through Python's `webbrowser`/osascript, never cmd.exe);
  - dash_render.py's `__main__` block.
- **Batch partners (batch 2).**
  - **S05 owns:** `dash_setup.ado`'s floor and verdict, `_dash_pymin`, the `_dash_require_python` message, `dash.pkg` Requires, the Dependencies paragraphs of dash.sthlp/dash_setup.sthlp, CHANGELOG `### Requirements`, `test/conftest.py` `_BASELINES`, `scripts/floor_matrix.sh`, its Makefile target, `test/requirements-dev.txt`, `test/requirements-stata.txt`, and the setup cscripts.
  - **S06 owns:** `_dash_smcl_escape`, `_dash_emit_note` and `_dash_note_scope` (`__main__`); the Mata `_dash_note`; the 11 txt note sites in `_dash_process_segment`, `_dash_render_immediate`, `_dash_build`, `_dash_report_ignored` and the `_dash_tmp_*` programs; dash.sthlp:594-604; `test_note_channel.py`; the NC-01..06 cases; and the 29 `UserWarning` needles.
  - S04 edits none of these. Both S04 and S06 add one name to dash.ado's `_needed` list and one entry to dash_parse.mata's header index, on different lines (R6).
- **Later sections:**
  - S12 (batch 4): the `saving()` widening (`..`, `; & | < >`); `_dash_path_badchar`/`_dash_validate_path`; the final form of this section's `saving()` paragraph and SB-28's `..` needle; the `To launch:` single-quoting with its Windows warning (P1.29.4/A100, moved to S12 by the manifest); PV-04/05/14 and P2-80; SB-31..40 and PV-35..44.
  - S41: the FILE-block guard (`preamble`, `js_resources`, `inner_body`) and the internals list.
  - S46: the busy and idle pages.
  - S54: Save as SVG under these policies, extending `test_csp_browser.py`.
  - S35 and S53: their CustomJS under `'unsafe-eval'`, each with its own browser check.
  - S09: drops MathJax from saved pages. S04's TeX browser case asserts no violation, not MathJax's presence.
  - S22: `dash`'s own `r(filename)`. `r(opened)`/`r(why)` belong to `_dash_open_page` only.
  - S58: ROADMAP, GAPS2/GAPS/DROPIN tracking lines (Notes for the closeout).
- **Excluded:**
  - measuring cmd.exe on Windows (M4);
  - opening through `os.startfile`/ShellExecute (option B, deferred to the platform package, P1.34.6);
  - Firefox or Safari in the suite (Firefox was checked once by hand, research §2);
  - a CSP level 1 fallback (A101);
  - a header carrying the nonce (A99).

## Stata truth

**New extractor** `scripts/extract_saving_chars_truth.do`, in S02's path-free form (A130): its root lines are S02's TR-02.9 stanza verbatim, with the message prefix `extract_saving_chars_truth.do` (S02's `TestTheExtractorRoot::test_every_root_stanza_is_whole` reads every `scripts/*.do` holding `local repo : environment DASH_REPO`). If S02's landed stanza differs from the lines below, copy S02's exactly.

```stata
* extract_saving_chars_truth.do -- twoway's saving() on paths holding the
* characters WP-30 rules on (P1.29, S04; P1.27, S12): its return code and
* whether the file was written under the name as typed, on this machine.
* Writes test/fixtures/saving_chars_truth.json, read by
* test/test_saving_chars.py and test/test_wp30_truth.cscript (S04, S12).
* Run (never the GUI):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_saving_chars_truth.do
* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_saving_chars_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zr_rc' | _rc {
    local _zr_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_saving_chars_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
version 19
set more off
sysuse auto, clear
local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local os "`c(os)'"
local machine "`c(machine_type)'"
tempfile gh base
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"
local d "`base'_sct"
capture mkdir "`d'"
capture mkdir "`d'/sub"
local keys  pct_path bang pct_pct caret amp semi pipe lt gt
local names `" "pct%PATH%x" "bang!x!y" "pct%%x" "caret^x" "R&D" "a;b" "a|b" "a<b" "a>b" "'
local i 0
foreach n of local names {
    local ++i
    local k : word `i' of `keys'
    capture erase `"`d'/tw_`n'.gph"'
    capture twoway scatter mpg weight, saving(`"`d'/tw_`n'.gph"', replace) nodraw
    local rc_`k' = _rc
    capture confirm file `"`d'/tw_`n'.gph"'
    local w_`k' = (_rc == 0)
    local f_`k' `"tw_`n'.gph"'
    capture erase `"`d'/tw_`n'.gph"'
}
capture twoway scatter mpg weight, saving("`d'/sub/../tw_dotdot.gph", replace) nodraw
local rc_dotdot = _rc
capture confirm file "`d'/tw_dotdot.gph"
local w_dotdot = (_rc == 0)
local f_dotdot "sub/../tw_dotdot.gph"
capture erase "`d'/tw_dotdot.gph"
capture rmdir "`d'/sub"
capture rmdir "`d'"
python:
import json, os
from sfi import Macro
keys = "pct_path bang pct_pct caret amp semi pipe lt gt dotdot".split()
probes = {}
for k in keys:
    f = Macro.getLocal("f_" + k)
    probes[k] = {"file": f,
                 "command": 'twoway scatter mpg weight, saving("<dir>/' + f + '", replace) nodraw',
                 "rc": int(float(Macro.getLocal("rc_" + k))),
                 "written": Macro.getLocal("w_" + k) == "1"}
out = {"probes": probes,
       "_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit").strip(),
                 "extracted": Macro.getLocal("extracted"),
                 "os": Macro.getLocal("os"),
                 "machine_type": Macro.getLocal("machine"),
                 "scope": "macOS only; Windows is unmeasured (WP-30 M4)",
                 "source": "scripts/extract_saving_chars_truth.do"}}
path = os.path.join(Macro.getLocal("repo"), "test", "fixtures", "saving_chars_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
```
The python block never calls Stata, never uses `shell=True`, and holds no backtick. A later regeneration is verified probe by probe outside `_meta` (R7).

**Run:** `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh $S $WT/scripts/extract_saving_chars_truth.do`. Read `$S/extract_saving_chars_truth.log`, then `git -C $WT add -f test/fixtures/saving_chars_truth.json`.

**Expected fixture** (measured 03oct2026, see Evidence): all ten probes `rc 0, written true` (`pct_path`, `bang`, `pct_pct`, `caret`, `amp`, `semi`, `pipe`, `lt`, `gt`, `dotdot`). `_meta` holds `stata_version` 19.5, `born_date`, `dash_commit`, `extracted`, `os` "Unix" and `machine_type` "Mac (Apple Silicon)".

**Truth block** in `test/test_wp30_truth.cscript`, between S04's own start and end lines (R1). Its helper is a `python:` block directly above `* ==== S04 P1.29: … ====`, defining `_csp_truth(key)` on `__main__`. `_csp_truth` reads `fixtures/saving_chars_truth.json` relative to the working directory (the driver `cd`s into `test/`) and sets globals `CSP_RC` and `CSP_W` for that key. The gated cases use single-line `python: __import__("__main__")._csp_truth("<key>")` calls only (the WP-29 truth-script form):
- **CSP-01..04** (guards): for `pct_path`, `bang`, `pct_pct` and `caret`, run `capture noisily dash scatter mpg weight, saving("`w30_work'/d_<stem>.html", replace)`, with `<stem>` the fixture file minus `tw_` and `.gph`. dash's rc equals `CSP_RC`, and `confirm file` on the literal name agrees with `CSP_W`, each checked by `_w30_expect CSP-0n "<cond>" "<msg>"` and closed by `_w30_done CSP-0n "saving() with <char> is written as typed, as twoway writes it"` (TR-01.10.4), which prints `CSP-0n PASS: …`. Each case erases its page before S04's end line, so the block leaves nothing in `` `w30_work' ``.

The driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > $S/run_test_wp30_truth.do`, then `WP30_ONLY=S04 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh $S $S/run_test_wp30_truth.do`.

twoway has no CSP counterpart. The CSP is certified in pytest and Chrome.

## TDD test stubs

Regression tests, written by 04-01 and failing at the batch-2 base:

`test/test_csp.py` (new classes; the failure at base is in brackets):
- Test: only executable inline scripts are hashed, and the digest is base64 SHA-256 over the LF text. — `test/test_csp.py::TestTheScriptHashes::test_only_executable_inline_scripts_are_hashed` [AttributeError: no `_dash_script_hashes`]
- Test: CRLF and LF bodies give one hash; `<SCRIPT>` upper case and `type="module"` are executable; `src=` and `application/json` are skipped; an unclosed script runs to the end. — `::TestTheScriptHashes::test_forms_and_line_endings` [AttributeError]
- Test: `_dash_csp_standalone` inserts sorted, distinct hashes after `script-src ` and refuses a malformed hash. — `test/test_csp.py::TestTheStandalonePolicy::test_hashes_are_inserted_sorted_and_once` [AttributeError]
- Test: on each saved page family (auto, bs, csv+tabs+range, filterposition(left), TeX title, by(), the stale-cue page), script-src has no `'unsafe-inline'`. — `test/test_csp.py::TestTheSavedPageAdmitsOnlyItsOwnScripts::test_script_src_has_no_unsafe_inline` [`'unsafe-inline'` in script-src]
- Test: the policy's hash set equals the set of the page's executable inline scripts. — `::TestTheSavedPageAdmitsOnlyItsOwnScripts::test_the_hashes_are_exactly_the_pages_scripts` [no hash in the policy]
- Test: `'unsafe-eval'` is kept and style-src is `{'unsafe-inline'}`. — `::TestTheSavedPageAdmitsOnlyItsOwnScripts::test_eval_and_inline_styles_are_kept` (guard; passes at base)
- Test: a script slipped into the bs header (monkeypatched `dr._dash_header_fragments`) or into the auto page's scheme CSS (monkeypatched `SchemeParser.css_style_element`) makes `render()` raise `DashScriptPolicyError`, and `dr.main()` writes no file. — `test/test_csp.py::TestAHostileFragmentIsNotAdmitted::test_render_refuses_and_writes_nothing` [the page was written with the script]
- Test: `_dash_seal_saved_page` returns a page whose scripts are all hashed and raises otherwise. — `::TestAHostileFragmentIsNotAdmitted::test_the_seal_refuses_an_unhashed_script` [AttributeError]
- Test: the empty bs page carries `default-src 'none'` first in `<head>` and no `style=` attribute. — `test/test_csp.py::TestTheEmptyAndRedirectPages::test_the_empty_page_runs_nothing` [no CSP meta]
- Test: `_dash_redirect_page` carries `default-src 'none'` and still escapes and sends no referrer. — `::TestTheEmptyAndRedirectPages::test_the_redirect_page_runs_nothing` [no CSP meta]
- Test: a nonce is 24 URL-safe characters and two differ. — `test/test_csp.py::TestTheNonce::test_a_nonce_is_fresh_and_urlsafe` [AttributeError]
- Test: `_dash_csp_served(n)` names `'nonce-n'` and `'unsafe-eval'`, holds no `'unsafe-inline'` in script-src, and refuses `"abc"`, `"a"*65`, `'x"y'`, `"{{x}}"` (ValueError) and `None` (TypeError). — `::TestTheNonce::test_the_served_policy_names_the_nonce_and_no_unsafe_inline` [AttributeError]
- Test: the template rendered with a real served context and with an INLINE context gives every script element the nonce, leaves a `"<script>"` inside a script body untouched, and gives an escaped hostile title or JSON text no nonce. — `test/test_csp.py::TestTheServedTemplate::test_only_script_elements_get_the_nonce` [no nonce attribute]
- Test: `_dash_served_template("bad")` raises ValueError. — `::TestTheServedTemplate::test_a_bad_nonce_is_refused` [TypeError: takes 0 arguments]
- Test: two `make_document` calls give two different nonces, each page's scripts carry its own, and the meta names it. — `test/test_csp.py::TestTheServedApp::test_each_document_gets_its_own_nonce` [no nonce]
- Test: under `python app.py`, every script of a fetched page carries the meta's nonce, two GETs differ, and the header is unchanged. — `test/test_csp.py::TestThePythonLauncherServes::test_every_script_carries_the_pages_nonce` [no nonce] (`serve`)
- Test: the same under `bokeh serve`. — `test/test_csp.py::TestBokehServeServes::test_every_script_carries_the_pages_nonce` [no nonce] (`serve`)
- Test: the Server Mode paragraph names `SHA-256`, `nonce`, `{cmd:'unsafe-eval'}`, `inline styles`, `CSP level 1` and `{cmd:default-src 'none'}`, and no longer says "may run only the scripts and styles written into it". — `test/test_csp.py::TestTheHelpSaysWhatIsSent::test_it_says_what_the_policy_protects` [old sentence present]

`test/test_csp_browser.py` (new; module skip without Chrome, as test_by_scales_chrome.py does; a skip is red under `DASH_STRICT=1`):
- Driver `_CspProbe(range_probe.RangeProbe)`, in this file, so range_probe.py is not edited.
  - It takes `url` (file or http).
  - Before `Page.navigate` it registers, with `Page.addScriptToEvaluateOnNewDocument`, `document.addEventListener('securitypolicyviolation', e => (window.__v = window.__v || []).push(e.violatedDirective + ' ' + e.blockedURI))`.
  - Methods: `violations()`; `inject()`, which uses `Runtime.evaluate` to append `<img src="data:," onerror="window.__inj_img=1">` and a created `<script>` with text `window.__inj_script=1`, then waits 500 ms; `ran()`, which reads `[!!window.__inj_img, !!window.__inj_script]`; and `in_task(js)`, which wraps an action in `setTimeout(…, 0)` so it runs as a page task.
- Test: on saved pages `auto`, `bs` and `rich`, the injected handler and script do not run, and the only violations are `script-src-attr inline` and `script-src-elem inline`. — `test/test_csp_browser.py::TestSavedPageInChrome::test_an_injected_script_and_handler_do_not_run` [both ran]
- Test: the same under `python app.py` and `bokeh serve` (rich app). — `test/test_csp_browser.py::TestServedPageInChrome::test_an_injected_script_and_handler_do_not_run` [both ran] (`serve`)
- Test: an injected same-origin `<script src="/static/js/bokeh.min.js">` without the nonce is refused (A102 nonce-only). — `::TestServedPageInChrome::test_a_same_origin_script_without_the_nonce_is_refused` [it loaded]

Guard and control tests in the same file (they pass at base; they exist to show the hardened pages still work):
- `::TestSavedPageInChrome::test_it_renders_with_no_violation_of_its_own` over `auto`, `bs`, `rich`, `formats` (`ylabel(, format(%9.2fc))` and a formatted hover), `big` (12,000 rows, WebGL, `_WEBGL_THRESHOLD` dash_render.py:3556) and `brush` (`link()` with a selection-driven KPI).
- `::TestSavedPageInChrome::test_a_filter_move_still_works_and_a_later_injection_is_blocked`: the dropdown in a page task changes a CDSView; zero new violations; inject again and it is blocked.
- `::TestSavedPageInChrome::test_exports_still_work`: the CSV button's view `click()` and the SaveTool's view action each deliver a file to a `Browser.setDownloadBehavior` directory within 10 s; zero violations.
- `::TestSavedPageInChrome::test_hover_and_brush_run`: `Input.dispatchMouseEvent` over a glyph shows a tooltip; selection indices set in a page task change the KPI Div text; zero violations.
- `::TestServedPageInChrome::test_it_renders_filters_and_round_trips`: launcher and bokeh serve, rich and big; a Select move changes the CDS lengths; zero violations; injecting after the move is blocked.
- `::TestTheMethodSeesWhatItClaims::test_under_the_old_policy_the_injection_runs`: a test copy of the auto page with the meta replaced by `c96facd`'s policy; both injected pieces run.
- `::TestTheMethodSeesWhatItClaims::test_without_unsafe_eval_a_move_is_blocked_and_seen`: a test copy without `'unsafe-eval'`; the move records an `eval` violation and changes nothing.
- `::TestTheRedirectPageInChrome::test_it_still_forwards`: the redirect page, written to a file with a `_Launched` app's URL, navigates there with no violation.

`test/test_serve_browser.cscript` (new SB-21..30 and the flips):
- **SB-21**: `_dash_cmd_metachar` returns the byte for each of `% ! ^ & | < > ;` and 0 for `C:\Users\o'brien\my dash (v1, v2)=#~\page.html`, `""` and `C:\Users\Zoë\p.html`. [r(3499) `_dash_cmd_metachar()` not found]
- **SB-22**: `_dash_open_page, path("C:\Users\me\a<c>b.html") os(Windows) dryrun` for each of the eight characters returns rc 0, `r(cmd)==""`, `r(opened)==0`, `r(why)=="metachar"`, `r(os)=="Windows"`. [`r(cmd)` was `start "" "C:\Users\me\a%b.html"`]
- **SB-23** (stubs on): without dryrun, `os(Windows)` and a `%PATH%` path give rc 0 and no `opened.log`, and the captured log holds `dash: not opened` and the path as typed. [`CALL start` recorded]
- **SB-24** (guard): `C:\Users\o'brien\my dash (v1, v2)\page.html` on Windows is still `start "" "<path>"` dry, and wet the stub gets `ARG[]` `ARG[<path>]`.
- **SB-25** (guard): on MacOSX and Unix, a path holding all eight characters is single-quoted dry, and wet the stub gets it whole. `r(why)==""`.
- **SB-26** (guard): with `$dash_nobrowser` set, the Windows metacharacter path still returns `r(cmd)==""` and `r(why)=="metachar"`.
- **SB-27** (guard): a Windows path holding `"` and `%` is still r(198), because the double-quote refusal comes first (SB-16's order).
- **SB-28**: dash.sthlp's `{marker saving_chars}` paragraph names every byte `_dash_cmd_metachar` flags (`{cmd:<c>}`) and every printable byte `_dash_path_badchar` refuses (`double quote`, `backquote`, else `{cmd:<c>}`), plus `{cmd:..}`, `control character` and `{cmd:-}`. [no marker]
- **SB-29** (after the restore, `$dash_nobrowser` 1): `dash scatter mpg weight, saving("<tmp>/dash_sb29.html", replace)` writes a page with `script-src 'sha256-` and no `script-src 'unsafe-inline'` (`cert_file_has`). [needle found]
- **SB-30**: `dash build, saving("<tmp>/dash_sb30.py") server replace` writes an app holding `doc.template = _dash_served_template(_dash_new_nonce())`. [not found]

Each of SB-21..30 runs in its own `capture noisily { }` (SB-21..28 inside the opener block, SB-29..30 after the restore) and adds its id to a local `sb_fail` on failure. After SB-30, `assert "`sb_fail'" == ""` with the list displayed, so at base every failing case, SB-29 and SB-30 included, shows its own text (an assert after SB-28 would stop the script before SB-29 and SB-30 ever ran).

Guards written after the fix:
- `test/test_path_validation.cscript` PV-28..34 (Test plan);
- `test/test_saving_chars.py`;
- the truth block's CSP-01..04;
- `test/test_responsive_layout.py::TestTheProbe::test_with_probe_admits_itself_under_both_policies`.

Pinned tests to flip: the "Existing tests" list in Evidence.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Hash scan, policy builders, seal, nonce, template helper | pytest `test_csp.py` (unit) | — | saved and served helpers |
| Saved pages carry exactly their scripts' hashes; seal fires | pytest `test_csp.py` | — | saved (7 families) |
| Served template, app, launcher, bokeh serve nonce | pytest `test_csp.py` (`serve` marks) | — | served (2 servers) |
| Empty and redirect pages | pytest `test_csp.py` + Chrome | — | both (empty: saved; redirect: served route) |
| Injection blocked; renders, filters (before and after a move), hover, brush, exports, WebGL; controls | Chrome over DevTools, `test_csp_browser.py` | — | both |
| Harnesses admit their probe | pytest `test_responsive_layout.py`, `test_stale_cue_browser.py` | — | both |
| `_dash_cmd_metachar`; opener dry/wet; Mac/Unix unchanged; order; help paragraph; Stata-route page and app | cscript `test_serve_browser.cscript` SB-21..30 | — | saved page and served app (SB-29/30) |
| `%`, `!`, `%%`, `^` written as typed on every route | cscript `test_path_validation.cscript` PV-28..34 | — | HTML, build and server |
| dash agrees with twoway on the four characters | truth block CSP-01..04 | `saving_chars_truth.json` | saved route |
| Fixture stamp and contents; Python validator accepts the four | pytest `test_saving_chars.py` | `saving_chars_truth.json` | — |
| Registries and served names | `test_function_test_map.py`, `test_program_coverage_map.py`, `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads`, `test_file_headers.py`, `test_cscript_hygiene.py` | — | served |
| Parity unchanged | `test_mode_parity.py` | — | both |
| Help | `test_csp.py::TestTheHelpSaysWhatIsSent`, SB-28, `test_help_conformance.py`, `test_help_claims_2.py`, `test_help_claims_4.py` | — | — |

PV cases (guards; each `display "PV-nn PASS: …"`), appended after PV-27 and before the script's cleanup:
- **PV-28** `dash scatter mpg weight, saving("<pvd>/pct%PATH%x.html")`: rc 0, and the literal file exists.
- **PV-29** `bang!x!y`.
- **PV-30** `pct%%x`.
- **PV-31** `caret^x`.
- **PV-32** `dash build, saving("<pvd>/b%HOME%!x.html") replace` after `dash scatter mpg weight, name(pv32)`: rc 0, literal.
- **PV-33** the same with `server` and `.py`: rc 0, literal.
- **PV-34** `_dash_validate_path "<pvd>/v%PATH%!^%%x.html"`: rc 0.

**Acceptance criteria.**
- **AC-04.1** `python3 -m pytest test/test_csp.py test/test_saving_chars.py test/test_served_bs_layout.py test/test_help_claims_4.py test/test_serve_token.py -q -n0 -p no:cacheprovider` reports 0 failed, with no skip.
- **AC-04.2** `python3 -m pytest test/test_csp_browser.py test/test_responsive_layout.py test/test_stale_cue_browser.py test/test_by_scales_chrome.py -q -p no:cacheprovider` reports 0 failed and no skip, on this Mac with Chrome. `test_csp_browser.py` alone finishes in under 3 minutes at `-n0`.
- **AC-04.3** Through the driver: `test_serve_browser.cscript` prints `SB-21 PASS` … `SB-30 PASS`; `test_path_validation.cscript` prints `PV-28 PASS` … `PV-34 PASS`; `test_wp30_truth.cscript` under `WP30_ONLY=S04` prints `CSP-01 PASS` … `CSP-04 PASS`. No FAIL, no new SKIP, no `r(` error line.
- **AC-04.4** `python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py test/test_file_headers.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_cscript_hygiene.py test/test_mode_parity.py test/test_server.py test/test_packaging.py test/test_varlist_expansion.py -q -p no:cacheprovider` reports 0 failed.
- **AC-04.5** Every non-comment line of dash_render.py matching `'unsafe-inline' 'unsafe-eval'` is `_DASH_CSP_SERVED`'s script-src line (`grep -n "'unsafe-inline' 'unsafe-eval'" dash_render.py | grep -v ':\s*#'`), `grep -c "_CSP_META\b" dash_render.py test/*.py` prints 0s, and `git diff <base> -- dash_render.py | grep -c "_DASH_CSP_SERVED = "` prints 0 (byte-identical).
- **AC-04.6** BUGS.md's `P1.29` entry is closed in place, naming existing tests. `WP30_OPEN` has no `"P1.29"`. `grep -c '<!-- WP-30 P1.29 -->' CHANGELOG.md` prints 0. `test_tracking_documents.py` passes.
- **AC-04.7** One commit on `wp30-s04` ending `(WP-30 P1.29)`, after one green full run through the queue, with no `claude|anthropic` in its message, and with a body naming both threats (G9).

## Tasks

**Commit boundary.** Tasks 04-01 to 04-16 form the one P1.29 commit, subject `Run only dash's own scripts on every page and never open a Windows path through cmd.exe metacharacters (WP-30 P1.29)`, made by 04-16 on `wp30-s04`.

- **Paths.** The worktree is `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s04`. `$S=<scratch>/s04`, `<scratch>` being the orchestrator's WP-30 scratch directory (`mkdir -p $S`). `$MAIN=/Users/billy/Desktop/Programs/StataPrograms/d/dash`. Every command runs with absolute paths into `$WT`.
- **Body.** It opens with `$S/04-P1.29-failure.txt`, then the measured defect, then what changed where. Then one line each:
  - `Regression: test/<file>::<Class>::<test> -- failed at <batch-2 base sha> with <text>` (cscript cases as `test/test_serve_browser.cscript SB-nn`);
  - `Flipped: <node> -- <old expectation> was wrong because <why>` (from `$S/04-flips.txt`);
  - `Fixture: test/fixtures/saving_chars_truth.json (scripts/extract_saving_chars_truth.do)`;
  - `BUGS.md: "<title>" (closed)`;
  - and the G9 line `Threats closed: an injected inline script or event handler running in a saved or served dashboard; a Windows page path that cmd.exe would rewrite before start opens it.`
- **Rules.** No AI or vendor reference anywhere. Never stage `CLAUDE.md`, `.gitignore`, `AGENTS.md` or `.ultraplan/`.

<task type="auto" id="04-01">
  <name>Write the failing regression tests</name>
  <files>test/test_csp.py, test/test_csp_browser.py, test/test_serve_browser.cscript</files>
  <action><![CDATA[
    Check the worktree:
    - `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-2-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s04`;
    - `<scratch>/batch-2-impact.txt` lists `_assemble_layout` and `_render_bootstrap_html` (CRITICAL) and `_generate_app_source` (HIGH) with the maintainer's approval. Say the warning in your progress output; if the approval is missing, stop.

    Then write every regression test of "TDD test stubs", with exactly those class and test names:
    - **test_csp.py.** Add the new classes. Import `DashScriptPolicyError` lazily through `dr` so collection works at base. The served page families reuse `_standalone_page`, extended with keyword arguments for tabs, csv, filterposition, a range filter, a by() graph option, colorvar and a TeX xtitle (copy the option strings from an existing test that uses each; `grep -n "tabs\|filter_position\|colorvar\|by" test/test_mode_parity.py`).
    - **test_csp_browser.py.** Create it with `_CspProbe`, the page builders and every regression, guard and control test of the stubs. Served apps come from `test_server_serves._build_app`, `_Launched` and `_Served`.
    - **test_serve_browser.cscript.**
      - Add SB-21..28 at the end of the `capture noisily {` opener block, after SB-20's `else` branch. Each case sits in its own `capture noisily { }` and records failures in `sb_fail`. Wet cases go under `if `sb_stubs'`.
      - Add the new Mata values to the drop line.
      - Add SB-29..30 after the restore (`global dash_nobrowser 1`) and before the final display.
      - Update the header's "Tests:" line to SB-30.

    Run on the unmodified tree:
    - `python3 -m pytest $WT/test/test_csp.py $WT/test/test_csp_browser.py -q -n0 -p no:cacheprovider -rf > $S/04-01-pytest.log 2>&1`;
    - the driver for `test_serve_browser.cscript` (BRIEF "Running one cscript", `<repo>`=`$WT`) into `$S/run_test_serve_browser.log`.

    Write `$S/04-P1.29-failure.txt`: the base sha, each regression node with its failure line (the bracketed texts of the stubs), and the guard and control tests that passed. Do not commit, and do not touch any non-test file.
  ]]></action>
  <verify><![CDATA[`grep -c "FAILED" $S/04-01-pytest.log` is at least 17; `grep -c "test_an_injected_script_and_handler_do_not_run" $S/04-01-pytest.log` is at least 2; `grep -cE "SB-2[1-9]|SB-30" $S/04-P1.29-failure.txt` is at least 6 (SB-21, 22, 23, 28, 29, 30); `grep -c "TestTheMethodSeesWhatItClaims.*PASSED\|passed" $S/04-01-pytest.log` is at least 1; `test -s $S/04-P1.29-failure.txt`.]]></verify>
  <done>Every P1.29 regression test existed and was shown failing on the batch-2 base with its own text, the controls showed the browser method sees injections and eval blocks, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="04-02">
  <name>Add the saved page's policy builders</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-04.1 to TR-04.5 and TR-04.8's constant in dash_render.py:
    - `_DASH_CSP_STANDALONE`'s new value and comment (:3670-3692);
    - `_DASH_CSP_NO_SCRIPTS` after `_DASH_SECURITY_HEADERS` (:3719);
    - `_dash_script_hashes`, `_dash_csp_standalone` and `_dash_saved_head` after `_dash_csp_meta` (:3753);
    - `DashScriptPolicyError` after `DashSpecError` (:1161);
    - `_dash_seal_saved_page` after `_dash_saved_head`.

    Delete `_CSP_META` and its comment (:4456-4462). Leave its two call sites for 04-03 (the module fails to import until then, so run no tests in between). Rewrite the block comment at :3663-3669 and the module docstring at :39-46: a saved page runs only the scripts dash wrote, named by hash; a served page only scripts carrying its nonce; `'unsafe-eval'` and inline styles stay.

    Each new function's docstring states its threat (an injected inline script), the measurement it rests on (Evidence), and its bounds. Add the four function keys of TR-04.17 under the S04 anchor of `test/function_test_map.py`, alphabetically.
  ]]></action>
  <verify><![CDATA[`grep -n "_CSP_META" $WT/dash_render.py` lists only :31107 and :32594 (fixed by 04-03); `grep -c "def _dash_script_hashes\|def _dash_csp_standalone\|def _dash_saved_head\|def _dash_seal_saved_page\|class DashScriptPolicyError" $WT/dash_render.py` prints 5.]]></verify>
  <done>The saved base policy without 'unsafe-inline', the hash scan, the per-page meta builder, the empty-page policy constant and the fail-closed seal existed in the renderer and in the function map.</done>
</task>

<task type="auto" id="04-03">
  <name>Hash and seal both saved pages</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in your progress output that `_assemble_layout` and `_render_bootstrap_html` are CRITICAL (12 and 6 impacted) before editing.

    In `_assemble_layout` (:32585-32596), apply TR-04.6:
    ```python
    html_str = file_html(...)
    hashes = _dash_script_hashes(html_str)
    ...replace("<head>", f"<head>\n    {_dash_saved_head(hashes)}\n{_scheme_css}", 1)
    return _dash_seal_saved_page(html_str, hashes)
    ```

    In `_render_bootstrap_html`, apply TR-04.7:
    - `hashes = _dash_script_hashes(_extracted_head) + _dash_script_hashes(script_tag)` right after `components()` (:30989);
    - `_dash_saved_head(hashes)` at :31107;
    - `return _dash_seal_saved_page(html_str, hashes)` at :31122.

    Apply TR-04.8 to the empty page (:30973-30978). Update the comment at :31103-31106 to say the policy now names each of Bokeh's scripts by hash, taken before dash's own HTML is spliced in. Change nothing else in either function.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_csp.py -q -n0 -p no:cacheprovider -k "ScriptHashes or StandalonePolicy or SavedPageAdmits or Hostile or EmptyAndRedirect and empty"` reports 0 failed; `python3 -m pytest $WT/test/test_mode_parity.py $WT/test/test_varlist_expansion.py -q -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Both saved pages listed exactly their Bokeh scripts' hashes with no 'unsafe-inline', refused to be written with any other inline script, and the empty page carried default-src 'none'.</done>
</task>

<task type="auto" id="04-04">
  <name>Give the served template a nonce</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-04.9 to TR-04.13 and TR-04.15:
    - `_DASH_CSP_SERVED_META` after `_DASH_CSP_SERVED` (:3709), whose comment now says it is the `python app.py` header's source and stays byte-identical (A99);
    - `_dash_new_nonce`, `_dash_csp_served` and `_dash_nonce_scripts` after `_dash_csp_meta`;
    - `_dash_served_template(nonce=None)` with the two block overrides through `functools.partial`, and its docstring rewritten (critic 4);
    - `_dash_redirect_page` with `_dash_csp_meta(_DASH_CSP_NO_SCRIPTS)` after the charset meta.

    No complete `<` + `script>` may appear in any of these functions' source or docstrings. Add the three function keys of TR-04.17 for the nonce helpers under the S04 anchor of `test/function_test_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_csp.py -q -n0 -p no:cacheprovider -k "TheNonce or only_script_elements or bad_nonce or redirect_page_runs_nothing"` reports 0 failed; `python3 -c "import sys;sys.path.insert(0,'$WT');import dash_render as d,inspect;src=''.join(inspect.getsource(getattr(d,n)) for n in ('_dash_served_template','_dash_nonce_scripts','_dash_csp_served','_dash_new_nonce','_dash_redirect_page'));assert '<script>' not in src;print('ok')"` prints ok.]]></verify>
  <done>The served template gave every script element of a page one fresh nonce named by a nonce-only meta policy, without editing any script body, and the redirect page carried default-src 'none'.</done>
</task>

<task type="auto" id="04-05">
  <name>Set the nonce in the generated app</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in your progress output that `ServerAppBuilder._generate_app_source` is HIGH (5 impacted) before editing.

    Apply TR-04.14 to the emitted `make_document` lines (:34718-34724): the comment line, then `"    doc.template = _dash_served_template(_dash_new_nonce())",`.

    Apply TR-04.16 to the two copy-list tuples of `_glyph_layer_lines`:
    - `"_DASH_CSP_SERVED_META", "_DASH_CSP_NO_SCRIPTS",` on a new line after :32955, extending the comment above it by "and the meta's own base and the no-script pages' policy (WP-30 P1.29)";
    - `"_dash_csp_served", "_dash_new_nonce", "_dash_nonce_scripts",` on a new line after :33289, extending its comment the same way.

    Re-order nothing.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_csp.py -q -n0 -p no:cacheprovider -k "TheServedApp or LauncherServes or BokehServeServes"` reports no failure other than the pinned `test_make_document_sets_the_template`, `test_a_refused_session_is_served_under_the_policy_too` and `test_the_page_carries_the_meta` (flipped by 04-06); `python3 -m pytest "$WT/test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "$WT/test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" $WT/test/test_server.py -q -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every served session built its page from a template carrying its own nonce, under python app.py and bokeh serve, with every new name on the served copy lists.</done>
</task>

<task type="auto" id="04-06">
  <name>Flip the pinned policy tests</name>
  <files>test/test_csp.py, test/test_served_bs_layout.py, test/test_help_claims_4.py</files>
  <action><![CDATA[
    In test_csp.py:
    - set `STANDALONE_TEXT`/`STANDALONE` to the new base;
    - add `SERVED_META_TEXT`/`SERVED_META` (the meta base);
    - add `_HASH_RE` and `_NONCE_RE` and admit those exact forms in `_assert_no_other_origin`;
    - add `_assert_saved_policy(page)` (STANDALONE with script-src equal to `{'unsafe-eval'}` plus the page's hash sources) and `_assert_served_policy(page)` (SERVED_META with script-src equal to `{'unsafe-eval', "'nonce-N'"}`, where N is the page's one nonce, every script carries it, and no `'unsafe-inline'`).

    Flip in place, with these helpers, each test of Evidence's flip list. Rewrite `test_it_is_bokehs_page_plus_the_two_metas` as described there (keep its name and give it a new docstring). Extend the four parametrized/extended tests listed in Evidence. Rewrite the module docstring's last paragraph: the browser run is now `test_csp_browser.py`.

    In test_served_bs_layout.py:877 and test_help_claims_4.py:1787, replace `dr._CSP_META` with `dr._dash_saved_head([])`.

    Append one `Flipped:` line per flipped node to `$S/04-flips.txt`. A test whose old expectation still holds is not flipped.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_csp.py $WT/test/test_served_bs_layout.py $WT/test/test_help_claims_4.py -q -p no:cacheprovider` reports 0 failed except `TestTheHelpSaysWhatIsSent::test_it_says_what_the_policy_protects` (04-14); `grep -c "^Flipped:" $S/04-flips.txt` is at least 12.]]></verify>
  <done>Every test that pinned 'unsafe-inline', the old served policy or the removed _CSP_META constant asserted the hashed and nonced policies instead, each flip recorded with its reason.</done>
</task>

<task type="auto" id="04-07">
  <name>Let the browser harnesses admit their probes</name>
  <files>test/responsive_probe.py, test/test_responsive_layout.py, test/test_stale_cue_browser.py</files>
  <action><![CDATA[
    In `test/responsive_probe.py`, add `admit_script(page_html, script_html)`. It places a complete script element before `</body>` (or appends it) and admits it under the page's own policy:
    - If the page's CSP meta names `'nonce-X'`, add ` nonce="X"` to the element's opening tag.
    - Else, if its script-src has no `'unsafe-inline'`, insert `'sha256-<the element body's LF digest>'` after `script-src ` in that meta's content.
    - With no meta, change nothing.

    It is test-only. Production text is never touched; only the page copy under test is. `with_probe(page_html)` becomes `admit_script(page_html, PROBE_JS)`.

    Then:
    - In test_stale_cue_browser.py, `_page` (:113-125) uses `responsive_probe.admit_script(page, _PROBE)`.
    - In test_responsive_layout.py, add `TestTheProbe::test_with_probe_admits_itself_under_both_policies`: a hashed page gains the probe's hash, and a nonce'd page's probe carries the nonce.
    - Extend `test_with_probe_goes_before_body_end` unchanged in its two assertions.
    - Update the docstring at :204 to quote the new `doc.template = _dash_served_template(_dash_new_nonce())` line.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_responsive_layout.py $WT/test/test_stale_cue_browser.py $WT/test/test_by_scales_chrome.py -q -p no:cacheprovider` reports 0 failed and 0 skipped.]]></verify>
  <done>The Chrome harnesses measured hashed and nonced pages again, admitting only their own probe on the page copy under test.</done>
</task>

<task type="auto" id="04-08">
  <name>Measure nonce-only across the browser matrix</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Run `python3 -m pytest $WT/test/test_csp_browser.py -q -n0 -p no:cacheprovider -rA > $S/04-08-browser.log 2>&1`, then repeat it with `/opt/anaconda3/bin/python3` (bokeh 3.8.0, Stata's Python) into `$S/04-08-browser-38.log`.

    **If every test passes in both,** nonce-only stands (A102). Write `$S/04-a102.txt` saying so, with both logs' last lines and the list of cases (rich, formats, big/WebGL, brush, hover, MathJax title, launcher, bokeh serve), and do not edit dash_render.py.

    **If any served case records a violation for a dash-or-Bokeh script without the nonce,** apply A102's fallback:
    - `_DASH_CSP_SERVED_META`'s script-src becomes `'self' 'unsafe-eval'`, with a comment naming the case and the violation;
    - flip `test_a_same_origin_script_without_the_nonce_is_refused` to assert that the script loads, with a `Flipped:` line;
    - record it all in `$S/04-a102.txt`;
    - the help sentence of 04-14 then adds "or come from the server it came from".

    A saved-page violation is a defect of 04-02/04-03: fix the code, not the test.
  ]]></action>
  <verify><![CDATA[`tail -1 $S/04-08-browser.log` and `tail -1 $S/04-08-browser-38.log` each report 0 failed and 0 skipped; `test -s $S/04-a102.txt`.]]></verify>
  <done>The served script policy was settled by measurement on both supported Bokeh versions, nonce-only unless a recorded case required 'self'.</done>
</task>

<task type="auto" id="04-09">
  <name>Correct docstrings describing the old policy</name>
  <files>test/test_html_output.py, test/test_label_sinks.py, test/test_server.py</files>
  <action><![CDATA[
    - test_html_output.py:1914-1919: the page's policy names its own scripts by hash; a CDN script is not allowed.
    - test_label_sinks.py:1188-1191: before WP-30 the page's CSP included `script-src 'unsafe-inline'`; it now names each of its scripts by hash, so an inline handler would also be blocked by the policy, but what protects the label is still BokehJS's text rendering.
    - test_server.py's BUG-40 comment (:9879-9881): SB-15's Windows path is now declined for its `;` and `&` (SB-22), and SB-24 keeps start's quoting of a hostile path without them.

    Text only: no assertion changes.
  ]]></action>
  <verify><![CDATA[`git -C $WT diff --stat -- test/test_html_output.py test/test_label_sinks.py test/test_server.py` shows only these three files; `python3 -m pytest $WT/test/test_html_output.py $WT/test/test_label_sinks.py -q -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>No test docstring still described the page policy as allowing inline scripts or the Windows hostile path as opened.</done>
</task>

<task type="auto" id="04-10">
  <name>Add the cmd metacharacter scanner</name>
  <files>dash_parse.mata, dash.ado</files>
  <action><![CDATA[
    Apply TR-04.19:
    - `_dash_cmd_metachar` directly after `_dash_path_badchar` in dash_parse.mata (:619-630), with its comment block in the file's form;
    - its header index entry after `_dash_path_badchar`'s (:42-45);
    - `_dash_cmd_metachar` added after `_dash_path_badchar` on dash.ado's `_needed` line (:242).

    Touch no other line of `_dash_require_mata`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_program_coverage_map.py $WT/test/test_file_headers.py -q -n0 -p no:cacheprovider` reports no failure other than `_dash_cmd_metachar` having no coverage entry yet (added by 04-11).]]></verify>
  <done>The Mata library had a byte scanner naming the first character cmd.exe would read in a quoted path, listed in the header index and in the library check.</done>
</task>

<task type="auto" id="04-11">
  <name>Decline metacharacter paths in the Windows opener</name>
  <files>dash.ado, test/test_serve_browser.cscript, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-04.20 in `_dash_open_page` (dash.ado:5812-5819) and its header comment (:5750-5779).

    Flip SB-15/19/20's sixth call in test_serve_browser.cscript:
    - `_sb_want[6]` becomes `""`;
    - `_sb_log[6]` becomes `"(none)"`;
    - SB-19's `assert r(opened) == 1` becomes `assert r(opened) == (`i' != 6)`;
    - SB-15's display text becomes "… is one quoted argument on a Mac and Unix; on Windows its ; and & make the opener decline it (SB-22)";
    - add a comment on the Mata setup lines: "Flipped (WP-30 P1.29): W holds ; and &, which cmd.exe reads".

    Append the three `Flipped:` lines to `$S/04-flips.txt`. Apply TR-04.21 to `test/program_coverage_map.py`.

    Run the driver for `test_serve_browser.cscript` (`$WT`) into `$S/run_test_serve_browser.log`.
  ]]></action>
  <verify><![CDATA[`grep -cE "SB-(1[3-9]|2[0-7]|29|30) PASS" $S/run_test_serve_browser.log` prints 17 and `sb_fail` lists SB-28 alone (its help paragraph is 04-14's, so the script still ends at that assert); `python3 -m pytest $WT/test/test_program_coverage_map.py $WT/test/test_packaging.py $WT/test/test_abbreviations.py -q -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>On Windows the opener built no command for a path cmd.exe would rewrite, printed the path and returned r(opened) 0 and r(why) metachar with rc 0, while Mac and Unix opened such paths quoted as before.</done>
</task>

<task type="auto" id="04-12">
  <name>Extract twoway's saving characters truth</name>
  <files>scripts/extract_saving_chars_truth.do, test/fixtures/saving_chars_truth.json, test/test_saving_chars.py</files>
  <action><![CDATA[
    Create `scripts/extract_saving_chars_truth.do` exactly as "Stata truth" gives it, with S02's landed header lines if they differ. Run it as "Stata truth" says, and read the log. Every probe must be `rc 0, written true`, as Evidence measured; a difference is investigated, never patched (R7). Then `git -C $WT add -f test/fixtures/saving_chars_truth.json`.

    Create `test/test_saving_chars.py` with two classes:
    - `TestTheTruthFixture`:
      - `test_meta_carries_the_stamp`: `stata_version`, `born_date`, `dash_commit`, `extracted`;
      - `test_every_probe_is_recorded`: the ten keys;
      - `test_twoway_writes_every_name_as_typed`: rc 0 and written for all ten.
    - `TestTheRendererAcceptsWhatTwowayWrites::test_the_four_s04_characters_pass_the_python_route`: `dr._validate_output_path` returns `/tmp/x/<stem>.html` (standalone) and `<stem>.py` (server) unchanged for `pct_path`, `bang`, `pct_pct` and `caret`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_saving_chars.py $WT/test/test_fixtures_are_committed.py -q -n0 -p no:cacheprovider` reports 0 failed; `git -C $WT ls-files test/fixtures/saving_chars_truth.json` prints the path; `grep -c "arch -arm64\|/Users/billy" $WT/scripts/extract_saving_chars_truth.do` prints 0.]]></verify>
  <done>twoway's return code and written name for every character WP-30 rules on were recorded in a stamped, committed fixture that the suite reads.</done>
</task>

<task type="auto" id="04-13">
  <name>Pin the character rule as guards</name>
  <files>test/test_path_validation.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Append PV-28..34 of "Test plan" to test_path_validation.cscript, after PV-27's last line and before its cleanup. Each case erases its file afterwards; PV-32/33 run `dash clear` after themselves.

    Write the S04 truth block (CSP-01..04 and its python helper above its header) as "Stata truth" gives it, between S04's own start and end lines. Never write inside another section's block.

    Run both through the driver:
    - `test_path_validation.cscript` into `$S/run_test_path_validation.log`;
    - `test_wp30_truth.cscript` with `WP30_ONLY=S04` into `$S/run_test_wp30_truth.log`.
  ]]></action>
  <verify><![CDATA[`grep -cE "PV-(2[89]|3[0-4]) PASS" $S/run_test_path_validation.log` prints 7; `grep -cE "CSP-0[1-4] PASS" $S/run_test_wp30_truth.log` prints 4; `grep -c "ALL CHECKS PASSED" $S/run_test_wp30_truth.log` prints 1; `grep -c " FAIL\|SKIP\|^r([0-9]*);" $S/run_test_wp30_truth.log` prints 0; `python3 -m pytest $WT/test/test_cscript_hygiene.py -q -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>dash's acceptance of %, !, %% and ^ in saving() on every route was pinned and certified against twoway's recorded truth.</done>
</task>

<task type="auto" id="04-14">
  <name>State the protection and character rule</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    **saving() synopt (:924-926).** It becomes: `required; path to the output HTML file, which must end in {cmd:.html}; see {help dash##saving_chars:Characters in saving()}`. Point the `server` synopt's sentence (:946-948) to the same link.

    **New paragraph,** after the table's `{synoptline}` (:953):

    `{marker saving_chars}{pstd}{ul:Characters in saving().}  A {cmd:saving()} path may not hold a double quote, a backquote, {cmd:$}, {cmd:;}, {cmd:&}, {cmd:|}, {cmd:<}, {cmd:>} or a control character such as a tab or a line break, may not have a {cmd:..} segment, and its file name may not begin with {cmd:-}: such a path is refused, r(198), and nothing is written.  Other characters, {cmd:%}, {cmd:!} and {cmd:^} among them, are written as typed, as {cmd:twoway}'s {cmd:saving()} writes them.  On Windows, dash does not open a page whose path holds {cmd:%}, {cmd:!}, {cmd:^}, {cmd:&}, {cmd:|}, {cmd:<}, {cmd:>} or {cmd:;}, because Windows' command shell, through which the page would be opened, reads them as instructions: the page is written, dash prints its path, and you open it yourself.  This includes the one-line form's preview page when the name of your user folder holds such a character.`

    **Server Mode (:1727-1737).** Replace the paragraph with the text of Notes "Help text for the CSP paragraph". Keep the four phrases `test_csp.py::TestTheHelpSaysWhatIsSent` pins.

    Then run `python3 -m pytest $WT/test/test_help_conformance.py $WT/test/test_help_claims_2.py $WT/test/test_help_claims_4.py $WT/test/test_csp.py -q -p no:cacheprovider`, and the driver for test_serve_browser.cscript (SB-28).
  ]]></action>
  <verify><![CDATA[The pytest command reports 0 failed; `grep -c "SB-28 PASS" $S/run_test_serve_browser.log` prints 1 and `grep -c "FAIL\|^r([0-9]*);" $S/run_test_serve_browser.log` prints 0 (SB-13..SB-30 all pass); `grep -c "may run only the scripts and styles written into it" $WT/dash.sthlp` prints 0; `grep -c "{marker saving_chars}" $WT/dash.sthlp` prints 1.]]></verify>
  <done>The help said which saving() characters dash refuses, what Windows does with the rest, and what the page policy does and does not protect.</done>
</task>

<task type="auto" id="04-15">
  <name>Verify the section before closing</name>
  <files>none</files>
  <action><![CDATA[
    Run, from `$WT`, each into its own log under `$S`:
    - the AC-04.1, AC-04.2 and AC-04.4 pytest commands (`-n0` for single files);
    - `python3 -m pytest $WT/test/test_tracking_documents.py -q -n0 -p no:cacheprovider` (the entry is still open: green);
    - the drivers for `test_serve_browser.cscript`, `test_path_validation.cscript`, `test_wp30_truth.cscript` (`WP30_ONLY=S04`) and `test_help_claims_2.cscript` (HC2-30 still opens a Mac page).

    Check AC-04.5 by grep. A failure is fixed in the code it names, never by weakening a test. Record each log's last line in `$S/04-15-summary.txt`.
  ]]></action>
  <verify><![CDATA[`$S/04-15-summary.txt` shows 0 failed and 0 skipped for every pytest log, and no FAIL or `r(` line for any cscript log.]]></verify>
  <done>Every test file, certification script and registry the section touches was green on the worktree before the closing task.</done>
</task>

<task type="auto" id="04-16">
  <name>Close P1.29 and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the entry's title as `WP30_OPEN["P1.29"]`. In BUGS.md change that entry's `- [ ]` to `- [x]` and replace only its Resolution line with Notes "BUGS.md Resolution". Name the test nodes exactly, and give `<ddmonyyyy>` as the commit day. Delete the `"P1.29"` key line from `WP30_OPEN`. Replace `<!-- WP-30 P1.29 -->` in CHANGELOG.md's `### Security` in place with Notes "CHANGELOG lines" (two bullets, each ending `(WP-30, P1.29)`).

    Confirm dash.sthlp holds 04-14's text. Then:
    1. Run `python3 -m pytest $WT/test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.
    2. Run `git -C $WT merge --no-edit main`, expecting `Already up to date.` (E9; otherwise stop and report).
    3. Run `<scratch>/full_suite_queue.sh $WT <scratch>/04-full-1.log` in the background and wait for its `exit=` line (E1; never relaunch it to check on it; E6 for the known flaky tests).
    4. Check that `git -C $WT diff --name-only` plus untracked files name only: dash_render.py, dash.ado, dash_parse.mata, dash.sthlp, BUGS.md, CHANGELOG.md, scripts/extract_saving_chars_truth.do, test/fixtures/saving_chars_truth.json, test/test_csp.py, test/test_csp_browser.py, test/test_saving_chars.py, test/test_serve_browser.cscript, test/test_path_validation.cscript, test/test_wp30_truth.cscript, test/function_test_map.py, test/program_coverage_map.py, test/responsive_probe.py, test/test_responsive_layout.py, test/test_stale_cue_browser.py, test/test_served_bs_layout.py, test/test_help_claims_4.py, test/test_html_output.py, test/test_label_sinks.py, test/test_server.py and test/test_tracking_documents.py (G6).
    5. Stage exactly those, with `git add -f` for the fixture. Write the message (subject of the commit boundary, body as specified) to `$S/04-message.txt`; G7 must give 0 on it before the commit.
    6. Confirm `git -C $WT branch --show-current` prints `wp30-s04`, commit with `-F $S/04-message.txt`, and run G7 on `git log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`grep -c "exit=0" <scratch>/04-full-1.log` prints 1 and the log shows 0 failed; `git -C $WT log -1 --format=%s | grep -c '(WP-30 P1.29)'` prints 1; `git -C $WT log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.29 -->' $WT/CHANGELOG.md` prints 0; `grep -c '^    "P1.29": "' $WT/test/test_tracking_documents.py` prints 0; `grep -c '(WP-30, P1.29)' $WT/CHANGELOG.md` prints 2; `git -C $WT show --name-only --format= HEAD | grep -cE 'CLAUDE.md|\.gitignore|AGENTS.md|\.ultraplan'` prints 0.]]></verify>
  <done>P1.29 was closed in BUGS.md naming existing tests, its CHANGELOG marker was replaced in the Security list, and one green commit on wp30-s04 carried the whole section.</done>
</task>

## Section completion criteria

- AC-04.1 to AC-04.7 hold on `wp30-s04`.
- The only `'unsafe-inline'` left in any script-src dash writes is the `python app.py` header's (`_DASH_CSP_SERVED`, byte-identical; A99).
- Every saved page lists exactly its Bokeh scripts' hashes and is sealed. Every served page has one fresh nonce on every script. The empty and redirect pages carry `default-src 'none'`.
- In Chrome, both modes block an injected script and handler before and after a move, with zero violations of their own, and still filter, hover, brush and export (bokeh 3.8.0 and 3.9.0).
- On Windows, `_dash_open_page` runs nothing for a path holding `% ! ^ & | < > ;` and returns `r(opened)=0`, `r(why)="metachar"`, rc 0. Mac and Unix are unchanged.
- `saving_chars_truth.json` is committed and stamped, and read by `test_saving_chars.py` and the S04 truth block.
- The help states the protection, its limits and the character rule.
- The commit body opens with the failure text and carries the Regression, Flipped, Fixture, BUGS.md and Threats lines.

## Notes

**Traps.**
1. **Hash the fragments, never the final page.** Hashing after the splice would admit any script an escaping fault let into the header, filter bar or grid. The seal is then vacuous, and `TestAHostileFragmentIsNotAdmitted` goes green for the wrong reason. The hashes come from `file_html`'s output (auto) and from `_extracted_head` plus `script_tag` (bs), and the seal checks the finished page against them.
2. **The template text is copied into the generated app.** No complete `<` + `script>` may appear in `_dash_served_template`, `_dash_nonce_scripts`, `_dash_csp_served`, `_dash_new_nonce` or `_dash_redirect_page`, docstrings included (test_server.py:599-607). Use `(?=[\s>/])` in the regex. Use `functools.partial`, not a lambda.
3. **The nonce is baked into the template text** through `_dash_csp_meta`, whose whitelist refuses braces. Never pass it as `doc.template_variables` with a `{{ }}` in the meta.
4. **`_DASH_CSP_SERVED` stays byte-identical:** it is the header's source. Its comment changes, not its value.
5. **Removing `_CSP_META`:** 04-02 leaves dash_render.py unimportable until 04-03. Do both before running anything.
6. **Copy lists** skip a misspelt name silently (A149). Run `test_every_listed_name_exists` after 04-05.
7. **Chrome actions run in a page task** (`setTimeout(…, 0)` from `Runtime.evaluate`) or through `Input.dispatchMouseEvent`. The control test without `'unsafe-eval'` proves the method sees eval blocks. The violation listener is registered with `Page.addScriptToEvaluateOnNewDocument`, which the policy does not govern.
8. **Downloads in headless Chrome:** `Browser.setDownloadBehavior` with `behavior: "allow"` and a temporary `downloadPath`. If the page session refuses the Browser domain, use the browser endpoint from `/json/version`. If neither works at the installed Chrome, record the measured reason and assert the CSV CustomJS ran with no violation instead (never a silent pass).
9. **The single-y digest** (`test_varlist_expansion.py`) covers the document JSON only and is expected not to move (R10). Never re-baseline it here.
10. **The cscript gate:** SB-21..28 sit inside the opener's `capture noisily` block, so wet cases need `sb_stubs`. SB-29..30 need `$dash_nobrowser` back at 1, so they sit after the restore. On Windows itself the wet cases skip as SB-18..20 do.
11. **`%` in Stata text** is literal in macros and in `_dash_say`, where it is printf's argument, not its format. `!` is literal in Stata. Neither needs escaping in the do-files.
12. **S06 lands after S04** and wraps `main()`. A `DashScriptPolicyError` then reaches Stata as S06's channel reports an error. Neither section depends on the other's form of it.

**Merge rules touched.**
- **R1:** test_serve_browser.cscript, test_path_validation.cscript, and the truth script's S04 block with its helper above the header.
- **R2:** the copy lists at :32955 and :33289; both maps under S04's anchors, plus `_dash_open_page`'s tuple in place.
- **R3:** dash.sthlp Dashboard Options (S04 creates the `saving()` paragraph; S12 rewrites it) and Server Mode (the CSP paragraph).
- **R4:** CHANGELOG `### Security` marker.
- **R5:** BUGS.md `P1.29` and the `WP30_OPEN` key.
- **R6:** dash.ado `_needed` and the dash_parse.mata header index. S06 edits other lines of both; the merger keeps both entries.
- **R7:** the fixture through its extractor, `git add -f`.
- **R9:** the flips.
- **R10:** the digest is not expected to move.

**Help text for the CSP paragraph** (04-14; replaces dash.sthlp:1727-1737):

> {pstd}
> The page carries a Content-Security-Policy in both modes, and the policy decides which scripts the browser runs.  A saved dashboard runs only the scripts dash wrote into it, each named in its policy by its SHA-256 hash, and loads nothing from anywhere; dash refuses to write a saved page holding an inline script it did not name.  A served page runs only the scripts that carry that page's nonce, a random value the server makes for each page it sends, and may also load from, and connect to, the server it came from, and nothing else.  So a script or an event handler that reached a page some other way -- through a fault in escaping, say -- does not run.  Two allowances remain, because BokehJS needs them: {cmd:'unsafe-eval'}, since Bokeh compiles each filter callback, tick formatter and tooltip formatter with {cmd:new Function}, and inline styles, since BokehJS writes its styles as it draws.  The policy is no substitute for escaping, which dash does for every string you give it, and a browser that supports only the first version of the standard (CSP level 1) shows a blank page.  The page that forwards your browser to a served dashboard, and the page written when a dashboard has nothing to show, carry {cmd:default-src 'none'}: they run no script at all.  {cmd:python app.py} also sends a policy as a header on every response, {cmd:/health} included, adding {cmd:frame-ancestors 'none'} so that no other site can frame the dashboard, and sends {cmd:X-Content-Type-Options: nosniff}, {cmd:X-Frame-Options: DENY} and {cmd:Referrer-Policy: no-referrer} with it.  That header cannot know each page's nonce, so it keeps {cmd:'unsafe-inline'}; a browser applies both policies, and the page's own refuses an injected script.  {cmd:bokeh serve app.py} sends none of these headers, so its page carries the policy but can be framed.

If 04-08 keeps `'self'`, the third sentence reads "…only the scripts that carry that page's nonce or come from the server it came from…".

**BUGS.md Resolution** (04-16):

`- Resolution: Fixed <ddmonyyyy> (WP-30, P1.29). The saved page's script-src lists the SHA-256 hash of each inline script Bokeh writes, taken before dash splices its own HTML in (_dash_script_hashes over file_html's output in _assemble_layout, over the head and the components() script in _render_bootstrap_html; _dash_csp_standalone, _dash_saved_head), and no longer 'unsafe-inline'; _dash_seal_saved_page refuses, with DashScriptPolicyError and nothing written, a page holding an inline script it did not hash. The served page's meta policy names a nonce made for each page (_dash_new_nonce, _dash_csp_served, _dash_nonce_scripts, through _dash_served_template(nonce), set by the generated make_document), nonce-only as measured in Chrome on bokeh 3.8 and 3.9; the python app.py header policy is unchanged and the page's own refuses injected scripts. The empty page and the link and redirect page carry default-src 'none'. 'unsafe-eval' and inline styles stay, because BokehJS needs them. On Windows _dash_open_page builds no command for a path holding % ! ^ & | < > or ; (_dash_cmd_metachar), prints the path and returns r(opened) 0 and r(why) metachar with rc 0; Mac and Unix are unchanged. The help states the protection, its limits and the saving() character rule. Pinned by test/test_csp_browser.py::TestSavedPageInChrome::test_an_injected_script_and_handler_do_not_run, test/test_csp_browser.py::TestServedPageInChrome::test_an_injected_script_and_handler_do_not_run, test/test_csp.py::TestTheSavedPageAdmitsOnlyItsOwnScripts::test_the_hashes_are_exactly_the_pages_scripts, test/test_csp.py::TestAHostileFragmentIsNotAdmitted::test_render_refuses_and_writes_nothing, test/test_csp.py::TestTheServedApp::test_each_document_gets_its_own_nonce, test/test_serve_browser.cscript SB-22, test/test_serve_browser.cscript SB-23; fixture test/fixtures/saving_chars_truth.json. Residual, deferred (WP-30): whether cmd.exe expands % and ! is unmeasured, and opening such a page without cmd.exe belongs to the platform package; Firefox was checked once by hand and Safari not at all.`

If 04-08 kept `'self'`, replace "nonce-only as measured" with "with 'self', because <the recorded case>".

**CHANGELOG lines** (04-16; replace `<!-- WP-30 P1.29 -->` in `### Security`):

```
- A dashboard page no longer lets an injected script run. A saved page's
  Content Security Policy used to allow `'unsafe-inline'` scripts, so an
  inline script or event handler that reached the page ran; it now names
  each script dash writes by its SHA-256 hash, and dash refuses to write a
  page holding any other. A served page names a nonce made for each page it
  sends, under `python app.py` and `bokeh serve` alike. `'unsafe-eval'` and
  inline styles stay, because BokehJS needs them; a browser that supports
  only CSP level 1 shows a blank page. The page that forwards a browser to a
  served dashboard, and the page written for a dashboard with nothing to
  show, carry `default-src 'none'`. (WP-30, P1.29)
- On Windows, a dashboard whose path holds `%`, `!`, `^`, `&`, `|`, `<`, `>`
  or `;` is written but no longer opened: the command shell that opened it
  reads `%NAME%` even inside quotes, so it could open another file than the
  one written. dash prints the path instead. (WP-30, P1.29)
```

**Notes for the closeout** (S58; A145: this section edits no tracking document):
- **GAPS2.md I12** (:1675): `- **Tracked:** Closed in WP-30, BUGS.md "<title of P1.29>", commit <sha>`. Append `(WP-30, GAPS2-I12)` to the entry's Resolution. Closes I12-a, I12-b and I12-c.
- **GAPS2.md I14** (:1692): partly closed here (I14-c, I14-d) and partly by S12 (I14-a, I14-b). Mark it Closed only once S12 has landed, naming both commits: `Closed in WP-30, BUGS.md "<P1.29 title>" (commit <S04 sha>) and "<P1.27 title>" (commit <S12 sha>)`. Append `(WP-30, GAPS2-I14)` to the S12 entry's Resolution and note the S04 half there.
- **GAPS.md I3** (:1867, "CLOSED by WP-20" with `'unsafe-inline'` retained): add "script-src `'unsafe-inline'` removed in WP-30 (P1.29): hashes on the saved page, a per-page nonce on the served page, a Chrome test of both modes."
- **GAPS.md E7** (:1219): add "The Windows `%`/`!` opener case closed in WP-30 (P1.29); the over-refusal of `..` and `; & | < >` in WP-30 (P1.27)."
- **DROPIN-REMAINING.md P1.29** (:163): closed, commit `<sha>`.
- **ROADMAP.md WP-30:** the P1.29 row. The deferred platform package (P1.34.6) gains: measure cmd.exe's expansion of `%` and `!` on Windows; open such a page without cmd.exe (option B, ShellExecute through `os.startfile`); and a Firefox and Safari run of `test_csp_browser.py`.
- **PLAN.md G11 documented divergences:** the CSP level 1 blank page [R17].

The research id collision (X.3) is settled here. S04 uses SB-21..30 and PV-28..34 (all allocated ids used) and the CSP prefix (CSP-01..04). S12 starts at SB-31 and PV-35.
