# Section 12: Drop-in command form and saving() grammar (P1.27, M5/M11)

> Part of: WP-30 · Items: P1.27 (entry `P1.27`) · Risk: yellow · Batch: 4 · Depends on: 03, 04 (and 01's entry, key, markers and stub block) · Blocks: 22 · Tasks: 14, 1 commit · Case prefixes: CF; SB-31..40; PV-35..44

## Review amendments

- Fixed (major, batch boundary): `_dash_plot` is edited by S12 (TR-12.5: :5540, :5560-5568) and by batch partner S10 (its sub-option checks around :5323-5325), and `_dash_require_mata`'s `_needed` by S10, S11 and S12. A139 forbids two sections of a batch editing one function. S10 was cut to a single 3-line hunk, recording through its own Mata. The remaining overlap needs an A139 exception, now a marked Maintainer question in Notes (recommendation: grant, since the hunks are more than 200 lines apart). Re-batching is not possible: every batch from 5 to 8 already holds three sections, and S22 (batch 8) depends on S12.
- Fixed (major): the "Open question" on `$dash__display` for SB-07..SB-11 goes beyond register P1.27.6's "only for the HC2 controls". It is now a marked Maintainer question with a recommendation.
- Fixed (minor, rule 1): the extractor's work folder and the PV/CF scratch folders were fixed names under the shared `c(tmpdir)` (`dash_cf_probe/`, `pv35d`, `pv41d/sub`). Each is now a fresh folder named from a `tempfile` and created with `mkdir`, failing the case if it exists, as S01's scaffold does.
- Fixed (minor): the S12 truth block wrote to its own `c(tmpdir)` folder; it now writes only under the scaffold's `` `w30_work' `` (TR-01.10 item 4).
- Fixed (minor): 12-14's file-count check counted `git show`'s blank line. It now counts non-empty lines.
- Checked: anchors at HEAD (the dispatcher's subcommand regex :115-118, `_dash_browser_wanted` :5696-5703, `_dash_dashboard_browser` :5739-5747, `_dash_build`'s `SAVing(string)` :8099 and `_dash_launch_app`'s `--show` :37318-37321) match. M11's allowed and refused sets match decisions.md, and the `--launch` `..` check stays. M5: twoway's saving words (E11) and r(199) prefixes (P1.27.7). A154 order. Security threats (a)-(g) are each pinned.
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:154-161 (P1.27) lists five drop-in gaps. Sources: CRIT-04, CRIT-02, CRIT-03, CRIT-09 (ids that exist only in DROPIN; the critic pass left no file), GAPS2-I14-a and GAPS2-I14-b (GAPS2.md:1692-1708, the "too strict" half of I14). Every one was re-measured at `c96facd` (research `.ultraplan/wp30/research/p1-27.md` §1 and its Critic additions, and this section's probes in Evidence E11-E12):

- **CRIT-04.** `set graphics off` and batch mode still open a browser. Neither decider reads `c(mode)` or `c(graphics)`: in batch, `_dash_browser_wanted` and `_dash_dashboard_browser` both return `r(open)=1`, and again after `set graphics off`.
- **CRIT-02.** `dash twoway scatter mpg weight`, `dash tw …`, `dash two …` and `dash graph twoway …` are refused, r(198) "dash: unrecognised plot type 'twoway'". twoway takes all of them (rc 0).
- **CRIT-03.** `saving(n1, asis)` writes a file literally named `n1, asis.html`; `saving(n4, bogus)` writes `n4, bogus.html`; `saving(, replace)` writes `, replace.html`; `saving("n, replace")` writes `n.html` with replace applied (twoway writes `n, replace.gph`); `saving(my file.html)` writes `my file.html` (twoway refuses it, r(198)).
- **CRIT-09.** `dash build, saving(b1.html, replace)` is refused, r(198) "saving() path must end in .html (got: b1.html, replace)"; `saving(b2)` is refused where the one-line form writes `b2.html`.
- **GAPS2-I14-a/-b.** `saving(../up.html)` and `saving("R&D.html")` (and `; | < >`) are refused, r(198); twoway writes all of them (rc 0, file exists).

**After this section.** Under M5 (refuse like twoway), M11 (allow; keep sink checks) and the register's rulings P1.27.1-P1.27.8:

- In batch (`c(mode)=="batch"`) and after `set graphics off`, no window opens on any route: the one-line form and `dash build` write the page and print its path, a one-line preview also says it is temporary and that `saving()` keeps a page (P1.27.5), and `dash serve` starts with `--no-browser`. Interactive Stata, the console included, opens the window as before (P1.27.1, P1.27.4; ratification item 15).
- A leading `twoway`, `tw`, `two`, or `graph`/`gr` followed by any of `tw`, `two`, `twow`, `twowa`, `twoway`, is read off once; the dashboard is the unprefixed command's, as a saved page and as a served app. `twow`, `twowa`, `gra`, `grap` (and capitalised spellings of the prefix words) are refused r(199) "command twow is unrecognized"; a second prefix word is refused r(198) "twoway is not a twoway plot type" (P1.27.7).
- One `saving()` grammar serves the one-line form and `dash build` (HTML and server): the text as typed, split at its first comma outside quotes and parentheses; `replace` and `asis` as full lower-case words, once each; anything else refused in twoway's words, r(198) (P1.27.3); an unquoted name holding a blank refused, r(198) (P1.27.7); an empty name is `Graph`; `.gph` is replaced and `.html` (`.py` with `server`) appended on both routes; `asis` is accepted and has no effect.
- `saving()` accepts a `..` segment and `; & | < >`; it still refuses a double quote, backquote, `$`, every control character (1-31, 127, as Python's `_validate_output_path` does) and a file name starting with `-` (M11, P1.27.2). The private `--launch` app path of `dash serve` keeps refusing `..`. The `To launch:` line of `dash build, server` is single-quoted on Mac and Unix, and on Windows names `%`/`!` (P1.29.4, moved here because this section owns `_dash_build`'s saving block).

**Why one section.** The manifest makes P1.27 one entry with one commit: the browser rule, the prefix, the grammar and the character rule all sit on the path from `dash`'s dispatcher to the file written, and the grammar must exist before S22 (batch 8) puts its image-extension rule inside `_dash_saving_parse`.

**Test order and commit rule (rule 7, D1, A156).**

- **12-01 to 12-04** write every regression test (pytest, cscripts, the truth block, the fixture) and run them against the unmodified tree. 12-01 creates `<scratch>/12-P1.27-failure.txt`; 12-02 to 12-04 append to it. None commits.
- **12-05 to 12-12** add the Mata grammar, the prefix strip, the display rule, the saving blocks, the Python path rule, flip the pinned tests, register the units and update the help.
- **12-13** certifies through the slot; **12-14** closes the entry, runs the full suite once through the queue and makes the one commit, `(WP-30 P1.27)`.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every command now passes a prefix step, batch behaviour changes for every user, and a security check is relaxed

**Why.** The prefix strip runs on every `dash` command; the browser rule changes what every `stata -b` user sees; `saving()` widens under M11 (a security trade-off the maintainer chose); the grammar refuses forms that used to write a file.

**Risk factors.**

1. A strip that matches too much routes a subcommand (`dash twoway build`) or a plot type to the wrong place, or rewrites `0` with macro expansion.
2. The certification suite always runs in batch: every case asserting `r(open)==1`, and the HC2 stub-opener controls, turn red or vacuous (critic correction 3).
3. `syntax … SAVing(string)` drops every pair of quotes (E9), so a grammar fed the parsed value cannot tell `saving("n, replace")` from `saving(n, replace)` or a quoted spaced name from an unquoted one.
4. The parsers that declare `SAVing(string)` (`_dash_parse_plot_opts` :961, `_dash_parse_graph_opts` :716) belong to S11's area this batch (A139: no two sections of a batch edit one function).
5. Relaxing `..` and `; & | < >` reaches the shell opener, the printed launch line, JSON and Python.
6. Tests that wrote `..` paths only because they were refused would now write outside the tree (P2-80 from `test/` reaches `<repo>/../../../tmp`; P20-16 reaches the repo root).
7. `_dash_dashboard_browser` reads `r(nodraw)` after an rclass call; a second rclass call before the read clobbers it (critic 9).
8. A user-reachable seam re-enables windows in batch.

**Mitigation.**

1. The strip is a Mata function reading `0` by value and writing it with `st_local`, matching only whole words from a closed list; a stripped command goes straight to `_dash_plot` (CF-01..04 pin every spelling against twoway's measured rc).
2. The decision is a pure-argument program (`_dash_display_on`, the `_dash_python_ok` pattern), so SB/ND cases pass `display(on)` and reach every state in batch (P1.27.6); the end-to-end stub controls set the undocumented `$dash__display on`, fenced by a new hygiene rule.
3. The saving text is re-read as typed from the option list that gave it (`_dash_seg_saving`, the `_dash_seg_by` pattern at dash_parse.mata:4139) and `_dash_build` declares `SAVing(string asis)`; neither parser is edited.
4. As 3: S12 edits no line of either parser.
5. Every sink is named and pinned (TR-12.15, G9): the opener single-quotes on Mac/Unix (measured literal, E11) and declines cmd metacharacters on Windows (S04, landed in batch 2); the launch line is single-quoted (SB-37, SB-38); JSON escapes (`_dash_json_str`); Python writes with `open()` and no shell; macro characters stay refused; `--launch` keeps its `..` check.
6. Each such test is rewritten to write into a scratch subfolder and its parent, never into the tree, and the flip is named (E13).
7. `r(nodraw)` is copied into a local before `_dash_display_on` runs; SB-35 pins the order.
8. The seam honours only `on`/`off`, is read only in the two deciders, appears in no help or shipped text, and a hygiene rule allows it only after a stub is first on PATH or the ado-path and requires its drop (`TestTheDisplaySeamIsFenced`).

## Dependencies

- **Depends on: 01.** The open BUGS.md entry `P1.27` and its `WP30_OPEN` key; the markers `<!-- WP-30 P1.27 -->` at the end of `### Changed behaviour (may need your do-files changed)` and under `### Fixed in WP-30` (index "P1 coverage": "Changed behaviour; Fixed in WP-30"); S12's stub block in `test/test_wp30_truth.cscript`; the S12 anchors in `test/program_coverage_map.py` (end of `COVERAGE["dash.ado"]` and of `COVERAGE["dash_parse.mata"]`, A148).
- **Depends on: 03.** `_dash_require_stata` and `version 19` open `dash`; every new program declares `version 19`; the prefix strip goes after `_dash_require_mata` (A154).
- **Depends on: 04.** `_dash_open_page` declines, on Windows, a path holding `% ! ^ & | < > ;` (written, not opened, path printed, `r(opened)=0`), so no commit opens such a path through cmd.exe once S12 accepts it (M11). S04 also creates `scripts/extract_saving_chars_truth.do` → `test/fixtures/saving_chars_truth.json` (S12 reads it, never runs it), allocates SB-21..30 and PV-28..34, and writes the help's first `saving()` character-rule text, which S12 rewrites to its final form.
- **Blocks: 22.** S22 (batch 8) makes `dash` rclass after S12's strip, and puts the image-extension rule inside `_dash_saving_parse`.
- **Parallel batch: 4, merge order S10, S11, S12** (S12 lands last). S10 edits the renderer's sub-option readers and Mata `_dash_rep_subkey`; S11 edits `_dash_parse_plot_opts`, `_dash_plot_opts_to_json`, `_dash_process_segment`, the folds, `_dash_opts_repeats` and `_dash_rep_reduce`. S12 edits none of them (Boundaries).

## Evidence

Anchors are at `c96facd` (dash.ado 8,487 lines, dash_parse.mata 6,093, dash_render.py 37,689, dash.sthlp 3,822). S01, S03 and S04 land before this section and shift dash.ado's line numbers by a few lines; the symbols are authoritative. GitNexus indexes no Stata or Mata symbol (`gitnexus impact _dash_validate_path -d upstream -r dash` → "Target '_dash_validate_path' not found", UNKNOWN); every caller below was confirmed by `grep -n`.

### E1 The dispatcher routes on the first word (dash.ado:84-146)

```stata
115      mata: st_local("_subcmd", ustrregexm(st_local("0"),                   ///
116          "^[a-zA-Z][a-zA-Z0-9_]*") ? ustrregexs(0) : "")
117      mata: st_local("_args", substr(st_local("0"),                         ///
118          strlen(st_local("_subcmd")) + 1, .))
120      if "`_subcmd'" == "kpi" {
...
144      global dash__uv = string(_caller())
145      _dash_plot `macval(0)'
```

`_dash_require_mata` is at :92. `twoway` reaches `_dash_plot`, which refuses it as a plot type. The plot route hands `0` on through `macval()`, so the strip must rewrite `0` itself, by value (critic correction 4).

### E2 The two deciders read neither c(mode) nor c(graphics)

```stata
5696  program define _dash_browser_wanted, rclass
5698      syntax , SPEC(string asis) [SAVing(string)]
5699      local open = 1
5700      if `"`saving'"' != "" local open = 0
5701      if "${dash_nobrowser}" != "" local open = 0
5702      if strpos(`"`spec'"', `""nodraw":"nodraw""') > 0 local open = 0
5703      return scalar open = `open'

5739  program define _dash_dashboard_browser, rclass
5741      syntax [, NOBRowser]
5742      _dash_registry_nodraw
5743      local open = ("`nobrowser'" == "" & "${dash_nobrowser}" == "" ///
5744                    & r(nodraw) == 0)
5746      if `open' return local flag ""
5747      else      return local flag "--no-browser"
```

Callers: `_dash_browser_wanted` at :6797 and :6820 (`_dash_render_immediate`); `_dash_dashboard_browser` at :8250 (`_dash_build`) and :8417 (`_dash_serve`, whose `r(flag)` becomes `--no-browser` on the launcher's argv, :8455-8457). `grep -n "c(graphics)\|c(mode)" dash.ado dash_parse.mata dash_render.py` finds nothing. Measured (research `dash_meas.do`): `one-line wanted, batch, graphics on: open=1`, `build/serve, batch: open=1`, and both `open=1` after `set graphics off`. The comment at :6812-6813 already claims "a do-file run in batch still does not want a browser window"; nothing implements it.

The served launcher needs no change: `_dash_launch_app` adds `--show` only when `no_browser` is false (dash_render.py:37318-37321), and `no_browser` is `--no-browser` from `_dash_serve`.

```python
37318    _cmd = [sys.executable, "-P", "-c", _DASH_BOOT, app_path, "--port",
37319            str(port)]
37320    if not no_browser:
37321        _cmd.append("--show")
```

Pinned by `test/test_help_claims_2.py::TestTheLauncherBehindDashServe::test_no_browser_and_a_timeout` (guard; `gitnexus impact _dash_launch_app -d upstream -r dash` → LOW, 7 impacted). The index's batch-4 line names `_dash_launch_app`'s `--show` path; it is read, pinned and left unchanged (Notes).

### E3 The one-line form's saving block (dash.ado:6455-6515) and its messages

```stata
6467          tempname P
6468          local replace ""
6469          mata: st_strscalar(st_local("P"), strtrim(st_local("saving_path")))
6470          if regexm(scalar(`P'), "^(.+)[ \t]*,[ \t]*replace[ \t]*$") {
6471              scalar `P' = strtrim(regexs(1))
6472              local replace = "replace"
6473          }
6479          if regexm(lower(scalar(`P')), "\.gph$") {
6483          if !regexm(lower(scalar(`P')), "\.html$") scalar `P' = scalar(`P') + ".html"
6485          _dash_validate_path `"`macval(saving_path)'"'
```

Only a trailing `, replace` is read; every other sub-option becomes part of the file name. The page is announced at :6830, `mata: _dash_say("txt", "dash: dashboard saved to ", st_local("saving_path"), "")`; a preview (no `saving()`) is named by `_dash_tmp_preview` (:6798-6800) and pruned later (dash_render.py:2414-2423: beyond the 4 newest of a session, and a dead session's).

### E4 `_dash_plot`'s replace fold (dash.ado:5559-5568)

```stata
5560      if `: length local g_replace' {
5561          if `: length local g_saving' & !`: length local g_name' {
5562              mata: st_local("g_saving", st_local("g_saving") + ///
5563                  (ustrregexm(st_local("g_saving"), ",[ \t]*replace[ \t]*$") ? "" : ", replace"))
5564          }
```

`saving(k1, asis) replace` becomes `k1, asis, replace`. `g_saving` comes from the parsers' `SAVing(string)` (`_dash_parse_graph_opts` :716, `_dash_parse_plot_opts` :961, sreturned at :1243) and is merged after the segment loop (:5300-5315); `saving` is in `_g_unique` (:5175), so a second copy anywhere is refused "option saving() not allowed", r(198) (matches twoway).

### E5 `dash build`'s saving block (dash.ado:8099, 8126-8156) and the launch line

```stata
8099        SAVing(string)          ///
8126      local _svl : length local saving
8131      if "`server'" != "" {
8142          _dash_validate_path `"`macval(saving)'"' "py"
8146          _dash_validate_path `"`macval(saving)'"' "html"
8236          mata: _dash_say("txt", "  To launch: python " + char(34), st_local("saving"), char(34))
```

The whole text, `b1.html, replace` included, is validated as a path. The banner at :8229-8240 is S23's and S46's later (batches 8, 16); S12 changes :8236 only.

### E6 The path checks (dash.ado:453-552, dash_parse.mata:597-631)

```stata
502      if regexm(`"`fpath'"', "(^|[/\\])\.\.($|[/\\])") {
503          display as error "dash: saving() path may not contain a '..' path segment (path traversal not allowed)."
536      if regexm("`fpath'", `"[;&|<>]"') {
537          display as error "dash: saving() path contains disallowed characters (shell metacharacters not permitted)."
```

```mata
619  real scalar _dash_path_badchar(string scalar path) {
623      bad = (34, 96, 36, 59, 38, 124, 60, 62, 9, 10, 13)
```

Kept: `~/` expansion (:489-496), the leading `-` refusal (:507-518), the suffix check (:519-522), the quote and control loop (:540-547, now defence in depth behind the scan). Callers of `_dash_validate_path`: :6485, :8142, :8146; of `_dash_path_badchar`: :474 and the `_needed` list (:242). Python mirrors it (dash_render.py:36710-36731):

```python
36712    parts = re.split(r"[/\\]", path)
36713    if any(p == ".." for p in parts):
36714        raise ValueError(
36715            "dash_render: --output may not contain a '..' path segment "
36727    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in path):
```

`gitnexus impact _validate_output_path -d upstream -r dash`: LOW, 1 direct caller (`main`, :36880), 6 impacted, 1 process. Python already refuses every control character; Mata refuses only 9, 10, 13 (the alignment M11 asks for).

### E7 The shell sinks

- `_dash_open_page` (dash.ado:5781-5835) is the only shell call (pinned by `test/test_packaging.py::TestNoUnsuppressableBrowserWindow::test_every_launcher_call_sits_inside_a_guard`). Mac/Unix: `open '<path>'` with `'` written `'\''`, run through `_stata(…, 0, 1)` (no macro expansion). Windows: S04's decline rule. Measured (research): `PATH=stub:$PATH /bin/bash -c "open 'R&D;touch PWNED|x<y>z.html'"` → the stub got one argument `R&D;touch PWNED|x<y>z.html`, and no `PWNED` file.
- The printed launch line (E5 :8236) is double-quoted; inside double quotes bash and zsh still run history expansion on `!` (p1-29.md critic 2: `bash: !x!y.py": event not found`), and cmd.exe expands `%NAME%`.

### E8 What twoway's `saving()` grammar is (graph.ado:304, gr_save.ado:5)

`graph.ado:304` calls `gr_save "name" <saving text>`; `gr_save.ado:5` is `syntax anything [, REPLACE ASIS]`: full words only, no abbreviation, case-sensitive.

### E9 `syntax … (string)` drops every pair of quotes (probe `p4.do`, this section, StataNow 19.5)

```
_p4s, saving("a,b.html", replace) sava("a,b.html", replace)
PROBE str=[a,b.html , replace] asis=["a,b.html", replace]
PROBE str=[n, replace]         asis=["n, replace"]
PROBE str=[my file.html]       asis=[my file.html]
PROBE str=[]                   asis=[   ]          (saving(   ))
```

So the grammar needs the text as typed. `_dash_seg_by` (dash_parse.mata:4139-4155) already reads a segment's option words as typed with `_first_comma_pos`, `_dash_rep_toks`, `_dash_rep_optname` and `_dash_rep_value` ("exactly as typed", :4543-4553); `_dash_seg_saving` copies it.

### E10 Where dash's own tests and help rely on today's form

- dash.sthlp:50-51 `saving(filepath [, replace])`; :75 build `saving(filepath)`; :93 `saving(filepath.py)`; :117-129 the plot_specs paragraph; :452-470 Differences 2 and "saving() keeps a file that is already there"; :838 "requires .py extension on saving()"; :924-926 "must end in .html; no .. traversal allowed"; :946-949 "saving() path must end in .py"; :950-956 the nobrowser row ("useful in batch"); :959-977 `{marker nobrowser_global}`.
- `test/test_help_claims_2.py::TestTheHelpSaysWhatWasMeasured::test_dash_nobrowser_is_defined` pins five phrases of :959-977 (kept verbatim).

### E11 twoway truth (StataNow 19.5, console, batch; research `tw_truth.do`, `tw_truth2.do`, `m3.do`, and this section's `p2.do`, `p5.do`)

```
TRUTH mode=[batch] graphics=[on] console=[console] os=[Unix] version=[19.5]
prefix twoway|tw|two|graph twoway|gr tw|graph tw|gr twoway|gr two|gr twow|gr twowa  rc=0
twoway(scatter …) rc=0 ; twoway (..) (..) rc=0 ; gr tw … || … rc=0 ; twoway alone rc=0
twow|twowa  rc=199 "command twow is unrecognized" ; gra two|grap tw rc=199 "command gra is unrecognized"
TWOWAY|Twoway rc=199 ("command TWOWAY not defined by TWOWAY.ado": macOS's case-insensitive file system)
two two -> "two is not a twoway plot type" r(198); tw twoway -> "twoway is …"; twoway tw -> "tw is …";
twoway graph -> "graph is …"; gr tw tw -> "tw is …"                                   (all r(198))
gr|graph scatter, gr TW, graph t -> r(4023) "<word>graph_g.new …: class member function not found"
set graphics off; twoway scatter … rc=0, graph describe rc=0 (built, not displayed)
saving(n1, asis) rc=0 ; (n1, asis replace) | (n1, replace asis) rc=0 ; (n4,replace) rc=0
saving(n1, bogus) "option bogus not allowed" ; (n1, as) "option as not allowed" ; (n1, rep) "option rep not allowed"
(n1, REPLACE) "option REPLACE not allowed" ; (n1, replace replace) "option replace not allowed"
(n1, replace asis asis) "option asis not allowed" ; (n1, asis(x)) "option asis() incorrectly specified"
(n1, replace(1)) "option replace() incorrectly specified" ; (n1, bogus(1)) "option bogus() not allowed"
(n1, , replace) "invalid 'replace' " ; (n1, replace , asis) "invalid 'asis' " ; (n1,) (n1,,) (n1, replace,) rc=0
(my file.html) "invalid syntax,  file.html not allowed" ; (a b c) "invalid syntax,  b c not allowed"
("a b" c) "invalid syntax,  c not allowed"                                                (all r(198))
("n, replace") -> "file n, replace.gph saved" ; ("a,b", replace) -> a,b.gph ; ("my file") -> my file.gph
(, replace) | ("", replace) | (   ) -> "file Graph.gph saved" ; saving() -> rc 0, no file ; ("n5.html") -> n5.html
(n1, asis) nodraw -> r(601) "no current graph" (asis needs a drawn graph; dash's asis has no effect)
../up.gph, ../sub/../up2.gph, R&D, a;b, a|b, a<b, a>b, 50%, a!b, "a b", -e, a(b), a{b}, a#b, a~b, a=b, a,b, a'b  rc=0, file exists
```

### E12 dash at HEAD (research `dash_meas.do`, `m3.do`, `m4.do`, critic `c1.do`; this section's `p3.do`)

```
MEAS prefix [twoway|tw|two|graph twoway|gr tw|graph tw|gr twoway|gr two] rc=198 "unrecognised plot type 'twoway'"
saving(n1, asis) -> "dash: dashboard saved to n1, asis.html" rc=0 ; (n4, bogus) -> "n4, bogus.html"
saving(k1, asis) replace -> "k1, asis.html" ; saving(, replace) -> ", replace.html" ; saving(my file.html) rc=0
saving("n, replace") -> n.html (p3.do: PROBE files: "n.html") ; saving(   ) -> a preview, no file (p3.do)
dash build, saving(b1.html, replace) rc=198 "must end in .html (got: b1.html, replace)" ; saving(b2) rc=198
one-line saving(../up.html) rc=198 ; build saving(../upb.html) rc=198 ; saving("R&D.html") [a;b] [a|b] [a<b] [a>b] rc=198
dash scatter mpg weight || lfit mpg weight, name(bb) rc=0 ; dash (scatter mpg weight) (lfit mpg weight), name(pp) rc=0
```

### E13 Tests that pin today's behaviour (flip in the fix commit with a `Flipped:` line, never delete; re-measure at the batch base, R9)

| Node | Today's expectation | Why it changes |
|---|---|---|
| test/test_path_validation.cscript PV-04 | `; & \| < >` refused by `_dash_validate_path` | M11 allows them |
| test/test_path_validation.cscript PV-05 | `/tmp/../etc/passwd.html` refused | M11 allows `..` |
| test/test_path_validation.cscript PV-11 | `/tmp/a;rm -rf x.py` and `/tmp/../etc/passwd.py` refused (the quote line stays) | M11 |
| test/test_path_validation.cscript PV-12 | `dash build, saving("/tmp/a;b.py") server` r(198) | M11; rewritten under `c(tmpdir)` |
| test/test_path_validation.cscript PV-14 | four `..` segment paths refused | M11 |
| test/test_path_validation.cscript PV-20 (second half) | `saving("<tmpdir>../pv20.py") server` r(198) | M11; rewritten from a scratch subfolder |
| test/test_adversarial.cscript P2-80 | `saving("../../../tmp/evil.html")` r(198) | M11; rewritten to write `../` from a scratch subfolder, never outside it |
| test/test_adversarial.cscript P2-85c | `evil\|cmd.html` refused | M11 |
| test/test_adversarial.cscript P20-08 | `.htm` refused by build ("(got: ….htm)"); `To launch: python "<path>"` | build appends `.html`; the line is single-quoted |
| test/test_adversarial.cscript P20-16 | `sav("../p2016a.html")` and the `///` form r(198) (they would now write into the repo root) | M11; rewritten from a scratch subfolder; `SAVING()` stays refused |
| test/test_serve_browser.cscript SB-01, SB-04 | `_dash_dashboard_browser` r(open)==1 in batch | batch opens nothing; pass `display(on)` |
| test/test_serve_browser.cscript SB-02, SB-03, SB-05 | r(open)==0 for their reason | would pass vacuously in batch; pass `display(on)` |
| test/test_serve_browser.cscript SB-07..SB-11 | `dash serve` flags by reason; SB-09 `--no-browser` absent | batch always flags; the block sets the seam |
| test/test_nodraw_honoured.cscript ND-04 | `_dash_browser_wanted` open 1/0 by reason in batch | pass `display(on)` |
| test/test_help_claims_2.cscript HC2-30, HC2-30b, HC2-34a, HC2-34e, HC2-34f (and HC2-31..36's zeros) | the stub opener runs in batch | the block sets the seam |
| test/test_adversarial_matrix.py::TestRendererOutputPath::test_a_hostile_output_path_is_refused | `"../x.html"`, `"a/../x.html"`, `"a\\..\\x.html"` refused | moved to `test_ordinary_paths_pass` |
| test/test_adversarial_matrix.py::TestRendererOutputPath::test_ordinary_paths_pass | — | gains the three |
| test/test_adversarial_matrix.py::TestRendererOutputPath::test_a_megabyte_path_is_judged_in_linear_time | `long_bad` ends `../x.html` | `long_bad` ends `x\x01.html` |
| test/test_adversarial_matrix.py::TestRendererOutputPath::test_main_refuses_before_it_writes | `sub/../escaped.html` refused | target `sub/-escaped.html` |

Not changed (guards): `test/test_help_claims_4.py::TestTheOutputPathRule::test_the_other_checks_hold_on_the_launch_route` (`..` refused with `launch=True`), PV-02, PV-03, PV-03b, PV-06..10, PV-13, PV-15..19, PV-21..27, P2-85, P2-85b, P20-07, P20-29, test_json_escaping.cscript JSE-68 (its needle `saving() path contains disallowed characters` is kept), test_server_build.cscript SB-06 (needle `To launch: python` stays in dash.ado), `test/test_packaging.py::TestNoUnsuppressableBrowserWindow::test_the_build_command_accepts_nobrowser` (the call `` _dash_dashboard_browser, `nobrowser' `` is kept as written), `test/test_abbreviations.py::test_the_tr_23_6_scans_see_what_they_look_for` (:607 stays 15: S12 adds no program with `syntax`; S11 moves only :619-620).

### E14 Blast radius

| Symbol | File | Risk | Callers (grep) |
|---|---|---|---|
| `dash` | dash.ado:84 | UNKNOWN (not indexed); every command, treat as HIGH | every command |
| `_dash_browser_wanted` | dash.ado:5696 | UNKNOWN | :6797, :6820; ND-04; test_packaging, test_unsupported_report_is_true (source reads) |
| `_dash_dashboard_browser` | dash.ado:5739 | UNKNOWN | :8250, :8417; SB-01..05; test_packaging |
| `_dash_render_immediate` (saving block, preview line) | dash.ado:6432 | UNKNOWN | `_dash_plot` :5682; about 19 test files |
| `_dash_build` (syntax, saving block, :8236) | dash.ado:8072 | UNKNOWN | `dash` |
| `_dash_plot` (saving read, check, fold) | dash.ado:5001 | UNKNOWN | `dash` |
| `_dash_validate_path` | dash.ado:453 | UNKNOWN | :6485, :8142, :8146; PV-*, test_adversarial, test_json_escaping |
| `_dash_path_badchar` | dash_parse.mata:619 | UNKNOWN | :474; `_needed`; PV-03*, P2-85b |
| `_validate_output_path` | dash_render.py:36678 | LOW (1 direct, 6 impacted) | `main` |
| `_dash_launch_app` | dash_render.py:37206 | LOW (7); read only | `__main__` |
| New: `_dash_display_on` (ado); `_dash_strip_prefix`, `_dash_seg_saving`, `_dash_saving_split`, `_dash_saving_parse`, `_dash_launch_quote`, `_dash_launch_warn` (Mata) | | new | — |

## User stories

- **US-12.1** As a twoway user, I want my do-file run with `stata -b` or after `set graphics off` to open no browser tab, and to be told where each page went, so that a batch job behaves as twoway's does.
- **US-12.2** As a twoway user, I want `dash twoway (scatter mpg weight) (lfit mpg weight)` (or `tw`, `two`, `graph twoway`) to draw what the same command without the prefix draws, saved or served, so that I can prefix a copied command with `dash` and nothing else.
- **US-12.3** As a twoway user, I want `saving(f, replace)` and `saving(f, asis)` read as twoway reads them on the one-line form and on `dash build`, and a mistyped sub-option refused in twoway's words, so that no file is written under a name I did not mean.
- **US-12.4** As a twoway user, I want `saving("../out/d.html")` and `saving("R&D.html")` to write where twoway would, so that my project's folder layout works unchanged.
- **US-12.5** As a dashboard publisher, I want the `To launch:` line `dash build, server` prints to run the file it names when I paste it into my shell, whatever characters the path holds.
- **US-12.6** As the maintainer, I want every browser state reachable from a certification script that runs in batch, without a seam a user would meet, so that the rule is tested and the suite never opens a window.

## Business requirements

- **BR-12.1** In batch mode or after `set graphics off`, `dash build`, the one-line form and `dash serve` open no window; the first two print the page's path, and a one-line preview also says it is temporary and that `saving()` keeps a page. In interactive Stata, the console included, windows open exactly as before.
- **BR-12.2** A command preceded by `twoway`, `tw`, `two`, or `graph`/`gr` followed by `tw`, `two`, `twow`, `twowa` or `twoway`, produces the same registered graph, saved page and served app as the command without it.
- **BR-12.3** `twow`, `twowa`, `gra`, `grap` and capitalised prefix words at the start are refused with r(199) "command <word> is unrecognized"; a second prefix word is refused with r(198) "<word> is not a twoway plot type"; a prefix never turns the rest into a `dash` subcommand.
- **BR-12.4** On the one-line form and `dash build` (HTML and server), `saving()` takes `replace` and `asis` as twoway does, keeps a comma inside quotes in the name, writes `Graph` for an empty name, and refuses every form twoway refuses in Table E11 with twoway's rc (198) and words; `asis` changes nothing.
- **BR-12.5** `dash build` appends `.html` (`.py` with `server`) and replaces `.gph` as the one-line form does, and `saving(f, replace)` overwrites.
- **BR-12.6** `saving()` writes a path holding a `..` segment or `; & | < >`; it refuses a double quote, backquote, `$`, any control character and a leading `-`, r(198); `dash serve`'s private app path still refuses `..`.
- **BR-12.7** The `To launch:` line, pasted into bash, zsh or sh, runs the file named, and on Windows the line says when `%` or `!` would be expanded by cmd.exe.
- **BR-12.8** Nothing drawn changes: the saved page and the served app of every command that worked before are unchanged, before and after any filter move; `dash serve` keeps naming and ignoring `saving()`.

## Technical requirements

**TR-12.1 The prefix strip (Mata `_dash_strip_prefix`, dash_parse.mata; `dash`, dash.ado:84).**

- `void _dash_strip_prefix()` reads the caller's local `0` with `st_local("0")` and sets the caller's locals `_pf_kind` (`""`, `"strip"`, `"unrec"` or `"twice"`) and `_pf_word`; on `"strip"` it writes the rest of the command back with `st_local("0", rest)`. No regex runs on the whole command beyond the existing anchor; linear in its length.
- w1 = the leading word `^[a-zA-Z][a-zA-Z0-9_]*` (the anchor E1 uses). If w1 is `twoway`, `tw` or `two`: rest = the text after w1. If w1 is `graph` or `gr`: w2 = the next word after blanks; if w2 is `tw`, `two`, `twow`, `twowa` or `twoway`, rest = the text after w2; otherwise kind `""` (today's route; `graph scatter` keeps r(198) "unrecognised plot type 'graph'", Boundaries). If w1 is `twow`, `twowa`, `gra` or `grap`, or w1 is not all lower case and `lower(w1)` is one of the nine words `twoway tw two twow twowa graph gr gra grap`: kind `"unrec"`, word w1.
- After a strip, if the rest's first word (after blanks, followed by a non-word character or the end) is one of the nine words: kind `"twice"`, word that word (measured for `two`, `tw`, `twoway`, `graph`; the fixture adds `twow` and `gra`).
- In `dash`, directly after `_dash_require_mata` (A154: S03's guard, `version 19`, the Mata guard, [S25's guard later], this strip, [S22's dispatch later]), insert a commented paragraph:

```stata
    mata: _dash_strip_prefix()
    if "`_pf_kind'" == "unrec" {
        mata: _dash_say("err", "command ", st_local("_pf_word"), " is unrecognized")
        exit 199
    }
    if "`_pf_kind'" == "twice" {
        mata: _dash_say("err", "", st_local("_pf_word"), " is not a twoway plot type")
        exit 198
    }
    if "`_pf_kind'" == "strip" {
        global dash__uv = string(_caller())
        _dash_plot `macval(0)'
        exit
    }
```

  A stripped command never reaches the `kpi`/`build`/`clear`/`serve` tests (`dash twoway build` is refused by `_dash_plot` as a plot type, r(198), as twoway refuses `twoway build`). `dash twoway` alone keeps "empty plot specification", r(198) (P2.56, P1.27.8).

**TR-12.2 The display rule (`_dash_display_on`, dash.ado, directly above `_dash_browser_wanted`'s header at :5687).**

- `program define _dash_display_on, rclass`, `version 19`, `args given mode graphics seam`, no `syntax`. A pure function of its arguments; every comparison is made by value in Mata (`st_local`), never inside quotes. `given` is `""`, `on` or `off` (anything else: `display as error "dash: display() is on or off."`, `exit 198`); a non-empty `given` decides; else a `seam` of exactly `on` or `off` decides; else `r(on) = !(mode == "batch" | graphics == "off")`. Header comment: twoway builds its graph and displays nothing in batch and after `set graphics off` (E11), so dash opens no window there (WP-30 P1.27, A88); interactive Stata, the console included, opens one (A89).
- `_dash_browser_wanted`: syntax becomes `syntax , SPEC(string asis) [SAVing(string) DISPlay(string)]`. After the existing three lines, read the seam by value, `mata: st_local("_bw_seam", st_global("dash__display"))`, call `` _dash_display_on `"`display'"' "`c(mode)'" "`c(graphics)'" `"`macval(_bw_seam)'"' `` and `if r(on) == 0 local open = 0`.
- `_dash_dashboard_browser`: syntax `[, NOBRowser DISPlay(string)]`. Copy `r(nodraw)` to `local _db_nd = r(nodraw)` right after `_dash_registry_nodraw`, then the seam read and `_dash_display_on` as above, then `` local open = ("`nobrowser'" == "" & "${dash_nobrowser}" == "" & `_db_nd' == 0 & r(on) == 1) ``. `r(flag)` keeps its two values. Both deciders keep reading `${dash_nobrowser}` and nodraw as written (test_packaging pins).
- Production callers pass no `display()`; the lines :6797, :6820, :8250 (`` _dash_dashboard_browser, `nobrowser' ``) and :8417 are unchanged.
- `$dash__display` is undocumented, read only in these two deciders, honoured only as `on`/`off` (P1.27.6). It is named in no help file, CHANGELOG line or BUGS text.

**TR-12.3 The preview line (`_dash_render_immediate`, else branch at :6828-6831).** After the `dash: dashboard saved to` line, when `` "`_dash_preview'" == "1" ``: `display as text "dash: this page is a temporary preview that later previews may remove; use saving() to keep it."` (P1.27.5). It prints for every preview not opened ($dash_nobrowser, nodraw, batch, graphics off), never for a `saving()` page. It contains neither `dashboard saved to` nor `(note:` (test_bug_regressions BR-02 counts the first; S06's needles match the second).

**TR-12.4 One grammar (Mata, dash_parse.mata, one block directly after `_dash_path_badchar`'s closing brace, :631).**

- `string rowvector _dash_saving_split(string scalar s)` (internal, pure) returns `(file, replace, asis, comma, err)`, the middle three `"0"`/`"1"`, `err` `""` or twoway's message. Linear in `strlen(s)`.
  1. p = `_first_comma_pos(s)`; file part f = `strtrim(substr(s, 1, p - 1))` (all of s when p == 0); comma = `p > 0`; option part o = the text after p.
  2. File: f == "" → `Graph` (twoway's default name; E11 `(, replace)`, `(   )`, `("", replace)`). t = `tokens(f)` (blank-separated, simple and compound quotes bound). One token: remove one enclosing pair of simple (`"…"`) or compound (`` `"…"' ``) quotes when the token starts and ends with that pair; an inner empty `""` → `Graph`; a token with an unbalanced quote is returned whole (the validator refuses its `"` in its own words: PV-21, PV-27, P20-29). Two or more tokens: err = `"invalid syntax,  " + invtokens(t[2..n], " ") + " not allowed"` (two blanks after the comma, as measured).
  3. Options, scanned left to right over o, outside quotes and parentheses, into words and single-comma tokens; the first problem is the error: a comma followed by a word w → `"invalid '" + w + "'"`; a comma followed only by blanks and commas → ignored; `replace` or `asis` (exact, lower case) the first time → set; the same word again → `"option <w> not allowed"`; `replace(…)` or `asis(…)` → `"option <name>() incorrectly specified"`; any other `name(…)` → `"option <name>() not allowed"`; any other word (abbreviations, other case, quoted words) → `"option <w> not allowed"`.
  4. The fixture (`twoway_command_form_truth.json`, E11's list plus `n1, bogus, replace`, `n1, , bogus` and `n1, "replace"`) decides any order not stated here: every record must be reproduced (CF-05).
- `void _dash_saving_parse(string scalar s, string scalar ext)` (called from dash.ado): calls `_dash_saving_split`; on `err` it calls `_dash_say("err", "", err, "")` and `exit(198)`; else it maps the name: a case-insensitive `.gph` suffix is removed and `_sv_gph` set to `"1"`; `"." + ext` is appended unless the name ends in it case-insensitively. It sets the caller's locals by value: `_sv_file`, `_sv_replace` (`"replace"`/`""`), `_sv_asis` (`"asis"`/`""`), `_sv_gph` (`"1"`/`""`), `_sv_comma` (`"1"`/`""`). This is the place S22 adds its image-extension rule.

**TR-12.5 The text as typed (`_dash_seg_saving`, same Mata block; `_dash_plot`).**

- `string scalar _dash_seg_saving(string scalar seg)`: a copy of `_dash_seg_by` (dash_parse.mata:4139-4155) that keeps the value of the last option word whose `_dash_rep_optname` is exactly `sav`, `savi`, `savin` or `saving` (lower case; `SAVING()` stays the parsers' refusal, P20-16), returned by `_dash_rep_value` as typed; `""` when there is none or the value is `""` (twoway treats `saving()` as absent, E11). `saving(   )` returns `"   "`.
- `_dash_plot`, a new paragraph directly above the "Report unsupported options" block (:5540): when the after-comma list `"," + _gopts_axraw` (the copy taken at :5083 before axis routing) gives a value, it wins; else the first of `_seg_1` … `_seg_<n_segs>` that gives one (at most one exists: `_g_unique` refuses a second, E4). A non-empty value replaces `g_saving` by `: copy local`. Then, whenever `g_saving` is non-empty, `mata: _dash_saving_parse(st_local("g_saving"), "html")`, so a malformed `saving()` is refused before anything is registered or written, on the named route too (twoway refuses it with `name()`).
- The fold (:5560-5568) becomes: when `replace` was given with a `saving()` and no `name()`, and `_sv_replace` is empty, append `" replace"` when `_sv_comma` is `"1"`, else `", replace"`, by value in Mata. The note for `replace` without a `saving()`, or with `name()`, is unchanged (PV-25).

**TR-12.6 The one-line route (`_dash_render_immediate`, :6455-6495).** Replace :6467-6484 (the tempname `P`, the replace regex, the `.gph` and `.html` steps) with `mata: _dash_saving_parse(st_local("saving_path"), "html")`, `local replace : copy local _sv_replace`, `local saving_path : copy local _sv_file`; keep `` _dash_validate_path `"`macval(saving_path)'"' ``, the `~/` read-back, the `.gph` line (now `` if "`_sv_gph'" == "1" ``, in whatever form S06 gave it), `_dash_saving_dir` and `_dash_saving_clobber`. Comments name WP-30 P1.27 and the measured defects (E12).

**TR-12.7 `dash build` (`_dash_build`, :8072).** Declare `SAVing(string asis)` (:8099). After the "saving() is required" check, `` local _sv_ext = cond("`server'" != "", "py", "html") ``, `mata: _dash_saving_parse(st_local("saving"), st_local("_sv_ext"))`, `` if "`_sv_replace'" != "" local replace "replace" ``, `local saving : copy local _sv_file`, then one `` _dash_validate_path `"`macval(saving)'"' "`_sv_ext'" `` for both branches (the server branch's comments kept), the read-back, and, when `_sv_gph` is `"1"`, the line `dash build: saving() writes <HTML|a server app>, not a Stata .gph; using <path>` through `_dash_say` (the one-line form's form). `asis` is accepted and has no effect. `_dash_prepare_spec` (:7292) keeps `SAVing(string)`: it never reads the value.

**TR-12.8 The launch line (Mata `_dash_launch_quote`, `_dash_launch_warn`; `_dash_build` :8236).**

- `string scalar _dash_launch_quote(string scalar path, string scalar os)`: `os == "Windows"` → `char(34) + path + char(34)`; otherwise `char(39) + subinstr(path, char(39), char(39) + char(92) + char(39) + char(39), .) + char(39)` (the quoting `_dash_open_page` uses).
- `string scalar _dash_launch_warn(string scalar path, string scalar os)`: on Windows, when the path holds `%` or `!`, `"  Windows:   cmd.exe expands % and ! in this path when the line is pasted; run the app from a folder whose path has neither"`; otherwise `""`.
- :8236 becomes `` local _lh_os = cond("`c(os)'" == "Windows", "Windows", "Unix") ``, `mata: _dash_say("txt", "  To launch: python ", _dash_launch_quote(st_local("saving"), st_local("_lh_os")), "")`, then `mata: st_local("_lh_w", _dash_launch_warn(st_local("saving"), st_local("_lh_os")))` and `` if `: length local _lh_w' mata: _dash_say("txt", "", st_local("_lh_w"), "") ``. The literal `To launch: python` stays in dash.ado (test_server_build.cscript SB-06). The `Access:`/`Options:`/`Limits:` lines are untouched (S23, S46).

**TR-12.9 The character rule (`_dash_validate_path`, dash.ado:453; `_dash_path_badchar`, dash_parse.mata:619).**

- `_dash_path_badchar`: `bad = (34, 96, 36, 1..31, 127)` (build `(34, 96, 36, (1..31), 127)`); the byte scan is unchanged. Rewrite its comment block (:597-618) and the header entry (:42-45): the double quote, backquote and dollar sign (Stata would read them as macro text, or they end the quoted argument), and every control character, as `_validate_output_path` refuses them.
- `_dash_validate_path`: delete the `..` segment block (:498-505, comment and code) and the `[;&|<>]` block (:523-539, comment and code), each replaced by a two-line comment saying why (M11: `saving()` is the user's own command, an absolute path was always accepted, the opener single-quotes, cmd metacharacters are S04's opener's, the private app path keeps its `..` check in dash_render.py). The scan's message becomes `dash: saving() path contains disallowed characters: a double quote, a backquote, $ or a control character.` (keeps the needle `saving() path contains disallowed characters`). The `-` rule, `~/` expansion, suffix check and the quote/control loop (comment: defence in depth behind the scan) stay.

**TR-12.10 Python (`_validate_output_path`, dash_render.py:36678-36748).** The `..` segment check (:36712-36717) runs only when `launch` is true, with the message `dash_render: --output for --launch may not contain a '..' path segment: %r`. The docstring says: a written page or app may sit anywhere the user's `saving()` names, as twoway's may (WP-30 P1.27, M11); only `dash serve`'s private app path (`--launch`) refuses `..`; the leading `-` and control-character checks hold on every route and match `_dash_path_badchar`. No copy-list entry (it is CLI-only; index R2 row S12: no copy-list change). Not shipped into the served app.

**TR-12.11 Registries.**

- `_dash_require_mata`'s `_needed` (dash.ado:237-255): one new continuation line, `_dash_strip_prefix _dash_seg_saving _dash_saving_parse _dash_launch_quote _dash_launch_warn`, after the last line (:255, which gains ` ///`). `_dash_saving_split` is internal and not listed (test_program_coverage_map.py holds `_needed` to dash.ado's calls).
- dash_parse.mata header (:1-303): five Public API entries, after the `_dash_path_badchar(path)` entry, in the existing form (`*!   name(args)` then indented lines); `_dash_saving_parse`'s entry names `_dash_saving_split()` as its internal helper.
- `test/program_coverage_map.py`, under the S12 anchors: `COVERAGE["dash.ado"]`: `"_dash_display_on": ("test_serve_browser.cscript:SB-31", "test_serve_browser.cscript:SB-32")`; `COVERAGE["dash_parse.mata"]`: `"_dash_launch_quote": ("test_serve_browser.cscript:SB-37",)`, `"_dash_launch_warn": ("test_serve_browser.cscript:SB-37",)`, `"_dash_saving_parse": ("test_path_validation.cscript:PV-36", "test_path_validation.cscript:PV-37")`, `"_dash_saving_split": ("test_path_validation.cscript:PV-35",)`, `"_dash_seg_saving": ("test_path_validation.cscript:PV-37",)`, `"_dash_strip_prefix": ("test_wp30_truth.cscript:CF-01", "test_wp30_truth.cscript:CF-02")`, alphabetical.
- `test/function_test_map.py`: no new Python function; `'_validate_output_path'` keeps its entry (`test_a_hostile_output_path_is_refused` still exists).
- Served copy lists: none (R2 row S12). JS twins: none (no JS changes).

**TR-12.12 Help (`dash.sthlp`; R3 rows Syntax, Differences, Subcommands, Dashboard Options).**

- :50-51 → `{cmdab:sav:ing}{cmd:(}{it:filepath} [{cmd:,} {cmd:replace} {cmd:asis}]{cmd:)}`; :75 the same for `dash build`; :93 `{cmdab:sav:ing}{cmd:(}{it:filepath.py} [{cmd:,} {cmd:replace}]{cmd:)}`.
- After :129, a new `{pstd}` paragraph: "As in {cmd:twoway}, the {it:plot_specs} may be preceded by {cmd:twoway}, {cmd:tw} or {cmd:two}, or by {cmd:graph twoway} ({cmd:gr} for {cmd:graph}, and {cmd:tw} to {cmd:twoway} after it), so a command copied from a do-file runs as it is: {cmd:dash twoway (scatter mpg weight) (lfit mpg weight)} draws what {cmd:dash (scatter mpg weight) (lfit mpg weight)} draws, saved or served. One is read: a second, as in {cmd:dash twoway twoway scatter mpg weight}, is refused as {cmd:twoway} refuses it, "twoway is not a twoway plot type", {cmd:r(198)}; {cmd:twow}, {cmd:twowa}, {cmd:gra} and {cmd:grap} are refused with {cmd:r(199)}, "command twow is unrecognized", as Stata refuses them. {cmd:dash twoway} with nothing after it is refused; {cmd:twoway} draws an empty graph."
- :452-458 (Difference 2) ends "… and writes nothing; a {cmd:saving()} {cmd:twoway} would refuse is refused there too."; :460-470 gains: "{cmd:saving()}'s sub-options are {cmd:twoway}'s, {cmd:replace} and {cmd:asis}, in full, in lower case and once each, on the one-line form and {cmd:dash build} alike; {cmd:asis} is accepted and changes nothing, since a saved page is always fixed. Any other word is refused as {cmd:twoway} refuses it, "option bogus not allowed", {cmd:r(198)}, and so is a name holding a blank that is not in quotes: write {cmd:saving("my file.html")}. A comma inside the quotes belongs to the name, and {cmd:saving(, replace)} writes {cmd:Graph.html}."
- :838 "(requires {cmd:.py} extension on {cmd:saving()})" → "({cmd:.py} is appended to a {cmd:saving()} name that does not end in it)".
- :924-926 → "required; the file to write: {cmd:.html} is appended to a name that does not end in it and a {cmd:.gph} suffix is replaced, as on the one-line form; {cmd:saving(}{it:filepath}{cmd:, replace)} overwrites and {cmd:asis} is accepted; see {help dash##saving_chars:Characters in saving()}"; :946-949 "saving() path must end in {cmd:.py}" → "{cmd:.py} is appended to a {cmd:saving()} name that does not end in it".
- :950-956: "useful in batch, where one window per {cmd:dash build} is rarely wanted" → "in batch and after {cmd:set graphics off} no window opens anyway".
- :959-977: keep the five pinned phrases; replace the last sentence ("The global is meant for do-files run in batch …") with "The global is meant for interactive sessions and test suites that should open no window." and add: "{ul:Batch and set graphics off.} As {cmd:twoway} displays no graph in batch ({cmd:c(mode)} is {cmd:batch}) or after {cmd:set graphics off}, {cmd:dash} opens no window there, whatever is set: {cmd:dash build} and the one-line form write the page and print where it is, a one-line preview says it is temporary, and {cmd:dash serve} starts its server without a browser. Interactive Stata, the console included, opens the window as before."
- S04's character-rule text (Dashboard Options, found by reading :916-990 after S04) becomes, under `{marker saving_chars}` (added if S04 gave none): "{ul:Characters in saving().} A {cmd:saving()} path may hold what a file name on your system may hold, as {cmd:twoway}'s {cmd:saving()} may: a {cmd:..} segment, and {cmd:;} {cmd:&} {cmd:|} {cmd:<} {cmd:>} among the rest. Five things are refused, {cmd:r(198)}: a double quote, a backquote and a dollar sign, which Stata reads as macro text; a control character, such as a tab or a line break; and a file name starting with {cmd:-}, which a command would read as an option. On a Mac and on Unix the page is opened with its path in single quotes, where nothing in it is special, and the {cmd:To launch:} line of {cmd:dash build, server} quotes it the same way." followed by S04's Windows sentences kept verbatim, plus: "On Windows the {cmd:To launch:} line keeps double quotes and says so when the path holds {cmd:%} or {cmd:!}, which cmd.exe expands in a pasted line."

**TR-12.13 Tests and fixture** (TDD test stubs; Stata truth). New pytest file `test/test_command_form.py`; new extractor and fixture; cases appended to five cscripts; the S12 truth block.

**TR-12.14 Tracking.** BUGS.md entry `P1.27` closed in place; its `WP30_OPEN` line deleted; both markers replaced in place (12-14).

**TR-12.15 Security (rule 1, G9).** Threats named in the commit body: (a) command injection through a `saving()` path reaching the shell opener (single quotes on Mac/Unix, SB-38 and CF-22 with a `;touch PWNED;` path; Windows declined by S04); (b) the same through the pasted `To launch:` line (single-quoted; SB-37, SB-38); (c) macro expansion of a path (quote, backquote, `$` still refused, read by value in Mata; PV-42, JSE-68); (d) log or terminal control through a path (every control character refused; `_dash_say` replaces controls with `?` in echoes); (e) option smuggling through a leading `-` (refused; PV-42; Python too); (f) writing outside the user's choice: none new (absolute paths were accepted, PV-07); `dash serve`'s private folder keeps its `..` check (`test_the_other_checks_hold_on_the_launch_route`); (g) a user-reachable seam: honours `on`/`off` only, undocumented, cannot reach any sink a user's interactive session does not already reach. No `shell=True`, no `eval`; the strip and the grammar read text by value; every echo is one user word, once (no amplification), through `_dash_say`; every scan is linear (PV-43).

## Boundaries

- **Batch partners.** S10 owns `_dash_subopt_canon`, the renderer's sub-option readers and Mata `_dash_rep_subkey`; S11 owns `_dash_parse_plot_opts` (including its `SAVing(string)` line :961), `_dash_parse_graph_opts`' style lines, `_dash_plot_opts_to_json`, `_dash_process_segment`, the folds `_dash_fold_typed`/`_dash_fold_bw`/`_dash_fold_mlab`, `_dash_opts_repeats`, `_dash_rep_reduce`, and `test_abbreviations.py:619-620`. S12 calls `_dash_rep_toks`, `_dash_rep_optname`, `_dash_rep_value`, `_first_comma_pos` and never edits them.
- **Earlier sections.** S03's guard lines and `version` lines (only S12's new programs say `version 19`); S04's `_dash_open_page` (read, never edited), S04's fixture and extractor (read, never run), S04's Windows sentences in the help (kept verbatim).
- **Later sections.** S22: `r(filename)`, the rclass dispatch after the strip, image extensions inside `_dash_saving_parse`, the help's Exporting and Stored results. S23 and S46: the `dash build, server` banner lines other than `To launch:`, and `_dash_launch_app` (S12 leaves it unchanged). S25: its guard before the strip. S58: every tracking document (GAPS2 Tracked lines, ROADMAP, DROPIN, REMAINING, AGENTS.md).
- **Not changed, documented.** `dash graph <non-twoway word>` keeps r(198) "unrecognised plot type 'graph'" (twoway's r(4023) is an internal class error); a capitalised second word after a stripped prefix keeps dash's r(198) message (twoway's rc is 198 too); `saving(f, asis)` with `nodraw` writes the page (twoway's r(601) "no current graph" needs a drawn graph, which a saved page does not); `saving(f, asis)` again over an existing file keeps dash's "already exists … Use replace option to overwrite." r(198) where twoway gives r(602) (documented at dash.sthlp:460-470); `dash serve, saving()` is still named in a note and ignored.
- **Out of scope.** P2.56 (`dash twoway` alone; filed by the register); Windows and GUI `c(mode)` (M4, the platform package); the rest of the option surface (P2.21).

## Stata truth

**New extractor** `scripts/extract_twoway_command_form_truth.do` → `test/fixtures/twoway_command_form_truth.json`, copied from S02's converted form of `scripts/extract_emptied_layer_truth.do` (the `DASH_REPO`-or-`c(pwd)` preamble, A128/A130), opening with `adopath ++ "${CF_REPO}"` and `global dash_nobrowser 1`; it never calls a dash command. Run once (12-03):

```sh
DASH_REPO="$WT" /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_twoway_command_form_truth.do"
```

Method:

- `sysuse auto, clear`; the work folder is a fresh directory named from `tempfile cfbase` (`` mkdir "`cfbase'_cf" ``, exit 693 if it cannot be made; never a fixed name in the shared `c(tmpdir)`, rule 1), emptied before every case; `quietly shell git -C "${CF_REPO}" rev-parse HEAD > "<work>/git_head.txt"`; globals `CF_VERSION` (`c(stata_version)`), `CF_BORN` (`c(born_date)`), `CF_WHEN`, `CF_MODE` (`c(mode)`), `CF_GRAPHICS` (`c(graphics)`), `CF_OS` (`c(os)`).
- The case texts are set by value from Mata (`st_global("CF_P<i>", …)`, `st_global("CF_S<i>", …)`; compound quotes and apostrophes built with `char(96)`, `char(34)`, `char(39)`), never typed inside Stata quotes.
- Each case runs inside its own log, `log using "<work>/c<i>.log", text replace name(cft)`, between `display "CFT-BEGIN"` and `display "CFT-END"`, as `capture noisily <command>`, with `_rc` stored in `CF_RC<i>`; then `local fl : dir "<work>" files "*"` into `CF_F<i>`.
- **prefix** records (`twoway`-free commands drawn with `name(cfp, replace)`): `scatter mpg weight` (control), the heads `twoway`, `tw`, `two`, `graph twoway`, `gr tw`, `graph tw`, `gr twoway`, `gr two`, `gr twow`, `gr twowa`, `twow`, `twowa`, `gra two`, `grap tw`, `TWOWAY`, `Twoway`, `Graph twoway`, `GR tw`, `two two`, `tw twoway`, `twoway tw`, `twoway twoway`, `graph twoway twoway`, `twoway graph`, `twoway twow`, `twoway gra`, `gr tw tw`, `gr TW`, `graph`, `g tw` each followed by ` scatter mpg weight`; plus `twoway(scatter mpg weight)`, `twoway (scatter mpg weight) (lfit mpg weight)`, `gr tw scatter mpg weight || lfit mpg weight` and `twoway` alone.
- **saving** records (`twoway scatter mpg weight, name(cfs, replace) saving(<text>)`): every text of E11 (`n1, asis`; `n1, asis replace`; `n1, replace asis`; `n1, bogus`; `n1, as`; `n1, rep`; `n1, REPLACE`; `n1, Replace`; `n1, replace replace`; `n1, replace asis asis`; `n1, asis(x)`; `n1, replace(1)`; `n1, bogus(1)`; `n1,`; `n1,,`; `n1, replace,`; `n1, , replace`; `n1, replace , asis`; `n4,replace`; `"n5.html", replace`; `, replace`; `   `; `"", replace`; `my file.html`; `a b c`; `"a b" c`; `"my file", replace`; `"n, replace"`; `"a,b", replace`; `` `"a b"', replace ``), plus `n1, bogus, replace`, `n1, , bogus`, `n1, "replace"`, and an empty `saving()`.
- **display**: `set graphics off`, `twoway scatter mpg weight, name(goff, replace)` rc, `graph describe goff` rc, `set graphics on`.
- A trailing `python:` block reads every global through `sfi.Macro.getGlobal`, reads each case log, keeps the lines between the `CFT-BEGIN` output line and the echo of `display "CFT-END"` that do not start with `. ` or `> `, strips trailing blanks, and writes `msg` (those lines joined by `\n`) and `last` (the last of them). It writes a backtick as `\x60`, never calls Stata, never uses `shell=True`, and erases the work folder.

Fixture keys:

```json
{"_meta": {"stata_version": "19.5", "born_date": "…", "dash_commit": "<sha>", "extracted": "…",
           "mode": "batch", "graphics": "on", "os": "Unix"},
 "prefix":  [{"cmd": "twoway scatter mpg weight", "rc": 0, "msg": "", "last": ""}, …],
 "saving":  [{"text": "n1, bogus", "rc": 198, "msg": "option bogus not allowed", "last": "option bogus not allowed", "files": []}, …],
 "display": {"graphics_off_rc": 0, "graphics_off_describe_rc": 0}}
```

`git add -f test/fixtures/twoway_command_form_truth.json` (`.git/info/exclude:58`). `test/test_command_form.py` names it (`test_fixtures_are_committed.py` is not edited). Path characters come from S04's `test/fixtures/saving_chars_truth.json` (twoway's rc and file for `; & | < >` and a `..` segment), read, never regenerated here (R7).

**Truth block** (S12's stub block in `test/test_wp30_truth.cscript`, `WP30_ONLY=S12`; helpers `_s12_truth` (a `python:` reader setting Stata locals through `sfi.Macro.setLocal`) and `_s12_said` directly above the header): CF-01..CF-08 (TDD stubs).

**Probes run while writing this section** (scratch `<scratch>/s12-probe/`, through the slot; quoted in E9, E11, E12): `p2.do`, `p5.do` (twoway saving and prefix forms), `p3.do` (dash at HEAD), `p4.do` (`syntax` string vs asis).

## TDD test stubs

Regression tests fail at the batch-4 base unless marked guard. Both modes: the saved page and the served app read one spec (`_dash_serve_spec`'s master JSON), and S12 changes no drawing, no JS and no served module code, so "after a filter move" holds by spec identity (CF-07) and needs no move test.

### `test/test_path_validation.cscript` PV-35..PV-44 (appended after S04's PV-34, before the `ALL CHECKS PASSED` display)

- **PV-35** `_dash_saving_split` accepted forms, called in Mata, compared joined by `|`: `n1, asis` → `n1|0|1|1|`; `n1, asis replace` and `n1, replace asis` → replace and asis 1; `n1,`, `n1,,`, `n1, replace,` → no error; `"a,b.html", replace` → `a,b.html`; `"n, replace"` → `n, replace`, replace 0; `` `"a b.html"', replace `` → `a b.html`; `, replace`, `   `, `"", replace` → `Graph`. Fails first: r(3499) `_dash_saving_split() not found`.
- **PV-36** refusals in twoway's words, r(198), by `_dash_saving_parse` under a log: `n1, bogus`, `n1, as`, `n1, rep`, `n1, REPLACE`, `n1, replace replace`, `n1, asis(x)` ("option asis() incorrectly specified"), `n1, bogus(1)` ("option bogus() not allowed"), `n1, , replace` ("invalid 'replace'"), `my file.html` ("invalid syntax,  file.html not allowed"), `"a b" c`. Fails first: r(3499).
- **PV-37** one-line route, in a scratch folder: `saving(n1, asis)` writes `n1.html` and no `n1, asis.html`; `saving(n2, replace asis)`; `saving(k1, asis) replace` overwrites `k1.html`; `saving(n3, bogus)` r(198), message, no file; `saving("n, replace")` writes `n, replace.html`; `saving(my file.html)` r(198); `saving(, replace)` and `saving(   )` write `Graph.html`; `saving(n4, bogus) name(cfn)` r(198), nothing registered. Fails first: the literal `n1, asis.html`.
- **PV-38** `dash build`: `saving(b1.html, replace)` overwrites; `saving(b2)` writes `b2.html`; `saving(b3.py, replace) server` overwrites; `saving(b4) server` writes `b4.py`; `saving(bx.gph)` writes `bx.html` with the `.gph` line; `saving(b5.html, bogus)` r(198) "option bogus not allowed"; `saving(b6.html, asis)` rc 0; `saving("b,7.html", replace)` writes `b,7.html`. Fails first: r(198) "must end in .html (got: b1.html, replace)".
- **PV-39** `_dash_path_badchar` returns 0 for `/tmp/a;b&c|d<e>f.html` and `../x.html`, and the byte for 34, 96, 36, 9, 27, 127; `_dash_validate_path "/tmp/a;b.html"` and `"../out.html"` rc 0. Fails first: 59.
- **PV-40** one-line `saving("R&D.html")`, `saving("a;b.html")`, `saving("a|b.html")`, `saving("a<b.html")`, `saving("a>b.html")` write their files in a scratch folder. Fails first: r(198).
- **PV-41** from `<scratch folder>/sub/`: one-line `saving(../up.html)`, `dash build, saving(../upb.html)` and `saving(../ups.py) server` write into the parent. Fails first: r(198).
- **PV-42** still refused, r(198), with the validator's words: a double quote, a backquote, `$`, a tab, ESC (27), DEL (127) and a leading `-` (`saving(-e.html)`); nothing written. Fails first for ESC and DEL (accepted at base).
- **PV-43** `_dash_saving_split` on a 200,000-character text (50,000 commas inside quotes, then `, replace`) returns `replace` 1 within 2 s (`timer`). Fails first: r(3499).
- **PV-44** `dash serve, saving(x, bogus)`'s route: `_dash_serve_spec` with `saving(x, bogus)` still names `saving()` in its note and returns rc 0 (guard: unchanged).

### `test/test_serve_browser.cscript` SB-31..SB-38 (appended after S04's SB-30; SB-36 at the end of the SB-06..11 stub block)

- **SB-31** `_dash_display_on` table: (`""`, interactive, on, `""`) → 1; (`""`, batch, on, `""`) → 0; (`""`, interactive, off, `""`) → 0; (`""`, batch, off, `""`) → 0; (on, batch, off, `""`) → 1; (off, interactive, on, `""`) → 0; (`""`, batch, on, on) → 1; (`""`, interactive, on, off) → 0; (`""`, batch, on, yes) → 0; (bogus, …) → r(198). Fails first: r(199) unrecognized command.
- **SB-32** seam unset, real batch: `_dash_dashboard_browser` → r(open)==0, r(flag)=="--no-browser". Fails first: 1, "".
- **SB-33** seam unset, real batch: `` _dash_browser_wanted, spec(`"{"plots":[],"graph_options":{}}"') `` → 0. Fails first: 1.
- **SB-34** `set graphics off`: `` _dash_display_on "" "interactive" "`c(graphics)'" "" `` → 0; after `set graphics on` → 1; `c(graphics)` is `on` at the end. Fails first: r(199).
- **SB-35** `display()` on both deciders: `display(on)` → 1, `display(off)` → 0, `display(bogus)` → r(198); a registered nodraw with `display(on)` → 0 and `--no-browser` (r(nodraw) read before the display call). Fails first: option display() not allowed, r(198).
- **SB-36** inside the stub block, seam dropped: `dash serve` hands `--no-browser` to the stub renderer with nothing said. Fails first: not found.
- **SB-37** `_dash_launch_quote`: Unix `/tmp/a b;c&d|e<f>g!h'i.py` → `'/tmp/a b;c&d|e<f>g!h'\''i.py'`; MacOSX the same; Windows `"…"`; `_dash_launch_warn`: Windows with `%` or `!` → the Windows line, Windows without → `""`, Unix with `!` → `""`. Fails first: r(3499).
- **SB-38** (G9) the Unix launch line is pasted into `/bin/sh`: a script file holding `printf '%s\n' <quoted>` run with `shell /bin/sh <file> > <out>`, path `<scratch>/a;touch PWNED;b'c&d|e<f>g!h.py`: `<out>` holds the path whole on one line, and no `PWNED` exists in the working or scratch folder. Fails first: r(3499).

### `test/test_wp30_truth.cscript` S12 block, CF-01..CF-08 (`WP30_ONLY=S12`)

- **CF-01** every fixture `prefix` record with rc 0 (except `twoway` alone): `dash <head> scatter mpg weight, name(cf<i>)` (and the paren, `twoway(`, `||` forms) registers `${dash_json_cf<i>}` equal to the unprefixed command's with the name replaced; `_dash_strip_prefix` on `local 0` sets `_pf_kind` `strip`. Fails first: r(198).
- **CF-02** every record with rc 199: dash's rc is 199; for the lower-case heads the last line equals the fixture's (`command twow is unrecognized`); for `TWOWAY`/`Twoway` dash says `command TWOWAY is unrecognized` (Stata's words on a case-sensitive file system). Fails first: r(198).
- **CF-03** every doubled-prefix record: dash's rc 198 and last line equal the fixture's (`two is not a twoway plot type`). Fails first: the words.
- **CF-04** (guard) `dash twoway build, saving(x.html)`, `dash tw kpi mean(mpg), name(k)` and `dash two clear` are r(198) and change no registry global; `dash graph scatter mpg weight` keeps r(198) "unrecognised plot type 'graph'".
- **CF-05** every fixture `saving` record (except `n1, asis` twice): the one-line form in an empty scratch folder gives rc 0 iff twoway did; a refusal's last line equals the fixture's `last` (trailing blanks stripped); the files written are the fixture's with `.gph` → `.html`. Fails first: `n1, bogus` rc 0.
- **CF-06** every S04 `saving_chars_truth.json` record for `;`, `&`, `|`, `<`, `>` and a `..` segment that twoway wrote: dash writes the `.html` equivalent where twoway wrote the `.gph`. Fails first: r(198).
- **CF-07** (both modes) `dash tw scatter mpg weight, name(s1)` then `_dash_serve_spec, specpath() datapath()` writes the same master JSON as the unprefixed command (the test_serve_options.cscript pattern); the saved one-line page of `dash twoway scatter mpg weight, saving(x.html)` is written and announced. Fails first: r(198).
- **CF-08** (guard) the fixture's `_meta` holds `stata_version`, `born_date`, `dash_commit`, `extracted`, and `mode` is `batch`.

### `test/test_help_claims_2.cscript` browser block, CF-21..CF-22 (after HC2-36, inside the capture block, where the stub opener is first on PATH)

- **CF-21** seam dropped (real batch): `` _hc2_b_build "`bo'" "" `` and `_hc2_b_plot ""` leave the stub log empty; the logs hold `dash: dashboard saved to` and, for the preview, `temporary preview`. Fails first: the stub saw an open.
- **CF-22** (G9) seam on: `` _hc2_b_build "`stubdir'/a;touch PWNED;b.html" "" `` → rc 0; the stub log's first line is `` open `stubdir'/a;touch PWNED;b.html `` (or `xdg-open …`); no `PWNED` in the working folder or `` `stubdir' ``. Fails first: r(198).
- In place (Flipped): `global dash__display on` right after `macro drop dash_nobrowser` (:819); `macro drop dash__display` beside `global dash_nobrowser 1` after `local rc_b = _rc` (:908-909); the header's `Tests:` list names CF-21, CF-22.

### `test/test_command_form.py` (new)

- `TestTheCommandFormFixture::test_the_meta_stamp_is_whole` (guard after 12-03)
- `TestTheCommandFormFixture::test_twoway_takes_the_prefixes_and_refuses_the_rest` (guard: rc 0 for the ten heads, 199 for `twow`/`twowa`/`gra two`/`grap tw`, 198 for the doubled ones)
- `TestTheCommandFormFixture::test_twoway_reads_saving_sub_options_as_full_words` (guard)
- `TestOneSavingGrammar::test_every_route_calls_the_one_parser` — `_dash_render_immediate`, `_dash_build` and `_dash_plot` each contain `_dash_saving_parse(`; fails first.
- `TestOneSavingGrammar::test_no_route_reads_replace_with_a_regex` — no `replace[ \t]*$` regex in dash.ado; fails first.
- `TestOneSavingGrammar::test_saving_is_read_as_typed` — `_dash_build` declares `SAVing(string asis)`; `_dash_plot` calls `_dash_seg_saving(`; fails first.
- `TestTheLaunchLine::test_the_server_banner_quotes_the_path_for_the_shell` — `_dash_build` calls `_dash_launch_quote(` and `_dash_launch_warn(`, and no `"  To launch: python " + char(34)` remains; fails first.
- `TestTheDisplayRule::test_the_seam_is_read_only_by_the_deciders_and_never_documented` — `dash__display` occurs in dash.ado only inside `_dash_browser_wanted` and `_dash_dashboard_browser`, and in no `.sthlp`, `.pkg`, CHANGELOG.md or README; fails first (absent).
- `TestTheDisplayRule::test_the_prefix_strip_follows_the_guards` — in `dash`'s body, `_dash_require_mata` precedes `_dash_strip_prefix()`, which precedes the first `` "`_subcmd'" == `` test (A154); fails first.
- `TestTheHelpStatesTheCommandForm::test_the_syntax_names_the_prefixes`, `::test_saving_takes_replace_and_asis_on_every_route`, `::test_the_browser_rule_names_batch_and_graphics_off`, `::test_the_character_rule_is_the_final_one` (no `{cmd:..} traversal allowed`, no `must end in {cmd:.py}`; names the five refused kinds and `{marker saving_chars}`) — fail first.

### Other pytest

- `test/test_packaging.py::TestNoUnsuppressableBrowserWindow::test_each_decision_reads_the_switches` (extended in place): each decider's body also contains `_dash_display_on`, `c(mode)` and `c(graphics)`; `_dash_display_on`'s body contains `"batch"` and `"off"`. Fails first.
- `test/test_adversarial_matrix.py::TestRendererOutputPath::test_a_parent_segment_is_written_where_twoway_writes` — `dr.main(sp, dp, str(sub / ".." / "escaped.html"))` writes `tmp_path/escaped.html`. Fails first: ValueError.
- `test/test_adversarial_matrix.py::TestRendererOutputPath::test_the_launch_route_keeps_refusing_a_parent_segment` — `"a/../app.py"` raises with `launch=True` and passes with `launch=False`. Fails first (the second half).
- `test/test_cscript_hygiene.py::TestTheDisplaySeamIsFenced::test_the_detector_reads_the_seam` and `::test_no_script_sets_the_seam_without_a_stub_and_a_drop` (guards: the detector `_display_seam_problems(src)` flags a `global dash__display <non-empty>` line not preceded by a `python: … os.environ["PATH"] =` line or an `adopath ++` line naming a `stub` folder, a script that never runs `macro drop dash__display` after setting it, and a build after it while `$dash_nobrowser` is unset outside a program body defined earlier; the scan passes on every `test/*.cscript`).

### Mutation table

| Mutation | Fails |
|---|---|
| `_dash_display_on` ignores `mode` | SB-31, SB-32, SB-33, CF-21 |
| decider calls `_dash_display_on` before copying `r(nodraw)` | SB-35 |
| strip also strips `graph scatter` | CF-04 |
| strip routes the rest to the subcommand dispatch | CF-04 |
| `_dash_saving_split` accepts `rep` | PV-36, CF-05 |
| file part taken from the parsed (quote-stripped) value | PV-37 (`"n, replace"`), CF-05 |
| `_dash_build` keeps `SAVing(string)` | `test_saving_is_read_as_typed`, PV-38 (`saving("b,7.html", replace)`) |
| `..` check left in Mata or Python standalone | PV-39, PV-41, `test_a_parent_segment_is_written_where_twoway_writes` |
| `..` check removed from `--launch` | `test_the_launch_route_keeps_refusing_a_parent_segment`, `test_the_other_checks_hold_on_the_launch_route` |
| launch line double-quoted on Unix | SB-37, SB-38, P20-08 |
| control characters 1-31 not all refused | PV-39, PV-42 |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Prefix strip vs twoway | cscript `test_wp30_truth.cscript` CF-01..CF-04, `WP30_ONLY=S12` | `twoway_command_form_truth.json` | CF-07: one spec for the saved page and the served app |
| saving() grammar vs twoway | CF-05; PV-35..PV-38, PV-43, PV-44 | same | HTML (one-line, build) and server `.py` |
| Path characters | CF-06; PV-39..PV-42; `TestRendererOutputPath` | `saving_chars_truth.json` (S04) | HTML and `.py`; `--launch` kept |
| Browser rule | SB-31..SB-36; CF-21; ND-04, SB-01..05 (flipped) | none | one-line, build, serve |
| Shell sinks (G9) | SB-37, SB-38, CF-22, existing SB-13..20 | none | build HTML and server line |
| Structure, help, seam | `test/test_command_form.py`, `test_packaging.py`, `test_cscript_hygiene.py` | the new fixture | n/a |
| Registries | `test_program_coverage_map.py`, `test_function_test_map.py`, `test_no_orphans.py`, `test_file_headers.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_tracking_documents.py` | none | n/a |
| Help claims kept | `test_help_claims_2.py`, `test_help_conformance.py`, `test_help_claims_8.py` | none | n/a |
| Drawing unchanged | `test/test_mode_parity.py -q -n0` (G3 run as a guard; no CORPUS change) | none | yes, with filter moves |

**Acceptance criteria.**

- **AC-12.1** `python3 -m pytest test/test_command_form.py test/test_packaging.py test/test_adversarial_matrix.py test/test_cscript_hygiene.py test/test_help_claims_4.py -q -n0` reports 0 failed.
- **AC-12.2** Through the driver, `test_path_validation.cscript` prints PV-35..PV-44 PASS and `ALL CHECKS PASSED`; `test_serve_browser.cscript` prints SB-31..SB-38 PASS and `All serve-browser tests PASSED.`; `test_nodraw_honoured.cscript` prints ND-04 PASS.
- **AC-12.3** `WP30_ONLY=S12` on `test_wp30_truth.cscript` prints CF-01..CF-08 PASS, no FAIL, no SKIP.
- **AC-12.4** `test_help_claims_2.cscript` prints CF-21, CF-22 and every HC2 case PASS; `test_adversarial.cscript`, `test_json_escaping.cscript`, `test_server_build.cscript`, `test_program_coverage.cscript`, `test_mata_library_guard.cscript` and `test_ado_loads.cscript` report no FAIL.
- **AC-12.5** `grep -c 'dash__display' dash.sthlp CHANGELOG.md dash.pkg` prints 0 for each; `grep -n 'path segment' dash.ado` prints nothing.
- **AC-12.6** No file outside the scratch folders is created by the suite: `git -C "$WT" status --porcelain --ignored | grep -v '^!! .gitnexus'` after 12-13 lists only the section's own edits.
- **AC-12.7** The full suite, run once through the queue in the worktree, has 0 failed (E6 for the known flaky tests).

## Tasks

**Commit boundary.** Tasks 12-01 to 12-14 form the one commit of entry P1.27, subject `Read twoway's command form, one saving() grammar and twoway's path characters; no window in batch (WP-30 P1.27)`, made by 12-14 on `wp30-s12` in `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s12` (`$WT`) after one full run through the queue. The body:

1. opens with `<scratch>/12-P1.27-failure.txt`;
2. gives the measured defects (E11, E12);
3. says what changed and where, and names the threats of TR-12.15 (G9);
4. carries one line each: `Regression: test/<file>.py::<Class>::<test> -- failed at <batch-4 base sha> with <text>` for each failing pytest node, `Regression: test/<script>.cscript <CASE-ID> -- failed at <sha> with <text>` for PV-35..43, SB-31..38, CF-01..03, CF-05..07, CF-21..22; `Flipped:` lines from `$S/12-flips.txt` (E13's rows, reasons as given there); `Fixture: test/fixtures/twoway_command_form_truth.json (scripts/extract_twoway_command_form_truth.do)`; `BUGS.md: "<title>" (closed)`.

Every command runs from `$WT`; `S=<scratch>/s12` (`mkdir -p "$S"`). A cscript runs only through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`), prefixed `WP30_ONLY=S12` for the truth script. No message, BUGS line, CHANGELOG line or help line names a tool or vendor (G7).

<task type="auto" id="12-01">
  <name>Write the failing grammar and character tests</name>
  <files>test/test_path_validation.cscript, test/test_command_form.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `<scratch>/batch-4-base.txt` and `git -C "$WT" branch --show-current` prints `wp30-s12`. Copy the S12 rows of `<scratch>/batch-4-impact.txt` into `$S/12-impact.txt`; report any HIGH or CRITICAL result for this section's symbols before editing.
    Append PV-35..PV-44 to `test/test_path_validation.cscript` as one contiguous run after S04's last case (PV-34) and before `display "test_path_validation.cscript: ALL CHECKS PASSED"`, exactly as "TDD test stubs" states, each ending `display "PV-3n PASS: …"`. File cases write only under `c(tmpdir)` in fresh folders the case creates from a `tempfile` name (never a fixed name such as `pv35d`; a folder that already exists fails the case, rule 1) and erases (the PV-41 folder with its `sub/`); PV-41 runs `cd` into `sub/` and back with `capture noisily` around it so the working folder is restored on every path; Mata calls read and compare by value. Update the header's case list.
    Create `test/test_command_form.py` with the classes `TestOneSavingGrammar`, `TestTheLaunchLine`, `TestTheDisplayRule` and `TestTheHelpStatesTheCommandForm` of "TDD test stubs" (not the fixture class, which 12-03 adds), reading dash.ado and dash.sthlp as text with a `_program_body(name)` helper in test_packaging.py's form.
    Run `python3 -m pytest test/test_command_form.py -q -n0 -p no:cacheprovider -rf > "$S/12-01-pytest.log" 2>&1` and the driver for `test_path_validation.cscript`. Create `<scratch>/12-P1.27-failure.txt` with the base sha, each failing pytest node with its assertion line, and the first failing cscript line. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/12-01-pytest.log"` equals the number of tests in test/test_command_form.py; `grep -c "PV-35 PASS" "$S/run_test_path_validation.log"` prints 0 and `grep -c "_dash_saving_split() not found" "$S/run_test_path_validation.log"` is at least 1; `test -s <scratch>/12-P1.27-failure.txt`.]]></verify>
  <done>The grammar, character and structure regression tests existed and were shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="12-02">
  <name>Write the failing browser and launch tests</name>
  <files>test/test_serve_browser.cscript, test/test_packaging.py, test/test_adversarial_matrix.py</files>
  <action><![CDATA[
    Append SB-31..SB-35, SB-37 and SB-38 to `test/test_serve_browser.cscript` as one run after S04's SB-30, before `display "All serve-browser tests PASSED."`; put SB-36 at the end of the SB-06..11 capture block (after SB-11's display, before its closing brace, :178-180), with `capture macro drop dash__display` before it. In the same block, as test infrastructure written now, set `global dash__display on` right after SB-06's display and add `capture macro drop dash__display` to the restore after `local rc_sb = _rc` (:181). SB-34 restores `set graphics on` on every path. SB-38 writes its sh script and output under a folder it creates in `c(tmpdir)` and erases. Update the header's `Tests:` line.
    Extend `TestNoUnsuppressableBrowserWindow::test_each_decision_reads_the_switches` in `test/test_packaging.py` (:569-579) with the assertions of "Other pytest", keeping the existing ones.
    Add `test_a_parent_segment_is_written_where_twoway_writes` and `test_the_launch_route_keeps_refusing_a_parent_segment` to `TestRendererOutputPath` in `test/test_adversarial_matrix.py` (after :2930). Do not flip anything yet.
    Run `python3 -m pytest test/test_packaging.py test/test_adversarial_matrix.py -q -n0 -p no:cacheprovider -rf -k "decision_reads or parent_segment" > "$S/12-02-pytest.log" 2>&1` and the driver for `test_serve_browser.cscript`; append the failures to `<scratch>/12-P1.27-failure.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/12-02-pytest.log"` prints 3; `grep -cE "SB-3[1-8] PASS" "$S/run_test_serve_browser.log"` prints 0 and the log shows the first SB-31 failure (`_dash_display_on` unrecognized, r(199)); SB-01..SB-30 still PASS.]]></verify>
  <done>The display-rule, launch-line and parent-segment regression tests existed and were shown failing on the unmodified tree, with the seam already fencing the stub serve block.</done>
</task>

<task type="auto" id="12-03">
  <name>Extract the command-form truth fixture</name>
  <files>scripts/extract_twoway_command_form_truth.do, test/fixtures/twoway_command_form_truth.json, test/test_command_form.py</files>
  <action><![CDATA[
    Create `scripts/extract_twoway_command_form_truth.do` as "Stata truth" specifies: S02's DASH_REPO preamble copied from `scripts/extract_emptied_layer_truth.do` as S02 left it, `adopath ++ "${CF_REPO}"` and `global dash_nobrowser 1`, the prefix, saving and display cases set by value from Mata, one log per case between CFT-BEGIN and CFT-END, and the python block writing the fixture with the `_meta` stamp (no `shell=True`, a backtick as `\x60`).
    Run it once: `DASH_REPO="$WT" /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_twoway_command_form_truth.do"`. Read the fixture and check it against E11 record by record (rc and `last`); a disagreement is reported, never patched.
    Add `TestTheCommandFormFixture` (three guard tests of "TDD test stubs") to `test/test_command_form.py`, reading `test/fixtures/twoway_command_form_truth.json`. Run it (`-n0`): the three pass. `git add -f` is left to 12-14.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/twoway_command_form_truth.json'));print(sorted(d['_meta']), len(d['prefix']), len(d['saving']))"` lists the four _meta keys plus mode, graphics, os, and at least 31 prefix and 34 saving records; `python3 -m pytest test/test_command_form.py -q -n0 -k Fixture` reports 3 passed.]]></verify>
  <done>twoway's measured answers for every prefix spelling, every saving() form and set graphics off were committed-ready as a stamped fixture that a guard test reads.</done>
</task>

<task type="auto" id="12-04">
  <name>Write the failing truth and end-to-end cases</name>
  <files>test/test_wp30_truth.cscript, test/test_help_claims_2.cscript, test/test_cscript_hygiene.py</files>
  <action><![CDATA[
    In S12's stub block of `test/test_wp30_truth.cscript` (`grep -n '==== S12 P1.27' test/test_wp30_truth.cscript`), write CF-01..CF-08 between its start and end display lines, with `_s12_truth` and `_s12_said` directly above its header, as "TDD test stubs" and "Stata truth" give them. Scratch writes go only under the scaffold's `` `w30_work' `` (CF-05's empty folders are fresh subfolders of it), erased before S12's end line (TR-01.10 item 4); the block runs `dash clear` at its end.
    In `test/test_help_claims_2.cscript`'s browser block, add `global dash__display on` right after `macro drop dash_nobrowser` (:819), add CF-21 and CF-22 after HC2-36 inside the capture block (CF-21 drops the seam and sets it again), and add `capture macro drop dash__display` beside `global dash_nobrowser 1` after `local rc_b = _rc` (:908-909). Update the header list.
    Add `_display_seam_problems(src)` and class `TestTheDisplaySeamIsFenced` to `test/test_cscript_hygiene.py`, after `TestNoScriptBuildsWithTheBrowserAllowed`, as "Other pytest" states; do not touch S01's pins (:294, :313, :322).
    Run `python3 -m pytest test/test_cscript_hygiene.py -q -n0`, the driver for `test_wp30_truth.cscript` with `WP30_ONLY=S12`, and for `test_help_claims_2.cscript`; append the CF failures to `<scratch>/12-P1.27-failure.txt`, and record that the HC2 cases still pass.
  ]]></action>
  <verify><![CDATA[test_cscript_hygiene.py reports 0 failed; `grep -c "CF-01 PASS" "$S/run_test_wp30_truth.log"` prints 0 and the log ends at CF-01's failing assert (the block stops at its first failure); `grep -c "CF-21 PASS" "$S/run_test_help_claims_2.log"` prints 0 and `grep -c "HC2-30 PASS"` on the same log prints 1.]]></verify>
  <done>Every regression test of the section existed and had been shown failing on the unmodified tree, and the failure text was complete.</done>
</task>

<task type="auto" id="12-05">
  <name>Add the grammar and prefix Mata functions</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    In dash_parse.mata, after `_dash_path_badchar`'s closing brace (:631) and before `_dash_check_utf8`, add one block with `_dash_strip_prefix`, `_dash_saving_split`, `_dash_saving_parse`, `_dash_seg_saving`, `_dash_launch_quote` and `_dash_launch_warn`, exactly as TR-12.1, TR-12.4, TR-12.5 and TR-12.8 state, each with a header comment naming WP-30 P1.27, the measured twoway rule it follows and its linear-time bound.
    Change `_dash_path_badchar`'s byte list and comment (:597-623) as TR-12.9 states. In the header (:1-303), rewrite the `_dash_path_badchar(path)` entry (:42-45) and add the five Public API entries after it (TR-12.11).
  ]]></action>
  <verify><![CDATA[Through the driver, `test_path_validation.cscript` prints PV-35, PV-36, PV-39 and PV-43 PASS (PV-37 may still fail until 12-08); `test_serve_browser.cscript` prints SB-37 and SB-38 PASS; `python3 -m pytest test/test_file_headers.py -q -n0` reports 0 failed.]]></verify>
  <done>The prefix reader, the one saving() grammar, the as-typed reader, the launch quoting and twoway's character rule existed in Mata as linear, by-value functions.</done>
</task>

<task type="auto" id="12-06">
  <name>Strip the twoway prefix in dash</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In `dash` (:84), directly after `_dash_require_mata` (:92) and its comment, insert a comment paragraph (WP-30 P1.27: twoway, tw, two or graph twoway may precede the plots, as in twoway; twow, twowa, gra and grap are refused r(199) as Stata refuses them; a second prefix r(198); read by value, and the rest goes to the plot route only, so `dash twoway build` is not a build) and the statements of TR-12.1. Change nothing else in `dash`.
    In `_dash_require_mata`, end :255 with ` ///` and add the line `        _dash_strip_prefix _dash_seg_saving _dash_saving_parse _dash_launch_quote _dash_launch_warn` (TR-12.11).
  ]]></action>
  <verify><![CDATA[`WP30_ONLY=S12` on test_wp30_truth.cscript prints CF-01, CF-02, CF-03 and CF-04 PASS; `python3 -m pytest test/test_command_form.py -q -n0 -k prefix_strip_follows` passes; `python3 -m pytest test/test_program_coverage_map.py -q -n0 -k needed` passes.]]></verify>
  <done>dash read twoway's own command words off the front of a plot command, once, and refused the spellings Stata refuses with Stata's codes and words.</done>
</task>

<task type="auto" id="12-07">
  <name>Open no window in batch</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Add `_dash_display_on` directly above `_dash_browser_wanted`'s header comment (:5687), and change `_dash_browser_wanted` (:5696-5704) and `_dash_dashboard_browser` (:5739-5748) and their header comments as TR-12.2 states: the `DISPlay(string)` option, the seam read by value through `st_global("dash__display")`, `r(nodraw)` copied before `_dash_display_on` runs.
    In `_dash_render_immediate`'s else branch (:6828-6831), add the temporary-preview line of TR-12.3 after the `dashboard saved to` line, only when `_dash_preview` is 1. Correct the comment at :6812-6813 to say the decision now reads batch mode and set graphics off.
  ]]></action>
  <verify><![CDATA[Through the driver, `test_serve_browser.cscript` prints SB-31..SB-36 PASS (SB-01 and SB-04 now fail until 12-11 flips them); `python3 -m pytest test/test_packaging.py -q -n0 -k "decision_reads or launcher_call or accepts_nobrowser"` reports 0 failed.]]></verify>
  <done>No route opened a window in batch or after set graphics off, interactive sessions kept theirs, and every state stayed reachable from a batch test through display() and the fenced seam.</done>
</task>

<task type="auto" id="12-08">
  <name>Route both saving blocks through one grammar</name>
  <files>dash.ado</files>
  <action><![CDATA[
    `_dash_plot`: add the as-typed paragraph above the report block (:5540) and rewrite the fold (:5560-5568) as TR-12.5 states.
    `_dash_render_immediate`: replace :6467-6484 as TR-12.6 states, keeping the validator, the read-back, the .gph line, `_dash_saving_dir` and `_dash_saving_clobber`.
    `_dash_build`: `SAVing(string asis)` (:8099), the parse, replace, one validator call for both branches and the .gph line (:8126-8147), and the launch line (:8236), as TR-12.7 and TR-12.8 state.
    `_dash_validate_path`: delete the `..` block (:498-505) and the `[;&|<>]` block (:523-539) with their replacement comments, and change the scan's message, as TR-12.9 states. Update the program's header comment (:450-452) and the scan comment (:464-473).
  ]]></action>
  <verify><![CDATA[Through the driver, `test_path_validation.cscript` prints PV-35..PV-44 PASS (PV-04, PV-05, PV-11, PV-12, PV-14, PV-20 now fail until 12-10); `WP30_ONLY=S12` prints CF-05, CF-06, CF-07 PASS; `python3 -m pytest test/test_command_form.py -q -n0 -k "Grammar or LaunchLine"` reports 0 failed.]]></verify>
  <done>The one-line form and dash build read saving() with one twoway grammar from the text as typed, wrote twoway's path characters, refused only the sink-tied ones, and printed a launch line a shell runs as written.</done>
</task>

<task type="auto" id="12-09">
  <name>Keep parent segments only off the launch route</name>
  <files>dash_render.py, test/test_adversarial_matrix.py</files>
  <action><![CDATA[
    In `_validate_output_path` (dash_render.py:36678), guard the `..` check (:36712-36717) with `launch` and change its message and the docstring, as TR-12.10 states. Nothing else in the function changes; it is not on a served copy list.
    In `test/test_adversarial_matrix.py::TestRendererOutputPath` flip, in place: move `"../x.html"`, `"a/../x.html"`, `"a\\..\\x.html"` from `test_a_hostile_output_path_is_refused` to `test_ordinary_paths_pass`; make `long_bad` `"a/" * 500000 + "x\x01.html"`; make `test_main_refuses_before_it_writes` target `sub / "-escaped.html"` and assert neither it nor `tmp_path / "-escaped.html"` exists. Each with a comment `WP-30 P1.27 (M11): …` giving the reason. Write the four `Flipped:` lines to `$S/12-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_adversarial_matrix.py -q -n0 -k TestRendererOutputPath test/test_help_claims_4.py -k "OutputPathRule"` reports 0 failed; `gitnexus` is not run in the worktree.]]></verify>
  <done>The renderer wrote a page or app wherever the user's saving() named, and dash serve's private app path still refused a parent segment.</done>
</task>

<task type="auto" id="12-10">
  <name>Flip the pinned path cases</name>
  <files>test/test_path_validation.cscript, test/test_adversarial.cscript, test/test_nodraw_honoured.cscript</files>
  <action><![CDATA[
    In `test/test_path_validation.cscript`, flip in place, each with a `// WP-30 P1.27 (M11): …` comment giving E13's reason: PV-04 (the five characters now give rc 0), PV-05 (rc 0), PV-11 (the `;` and `..` lines give rc 0; the quote line stays r(198)), PV-12 (build writes `<c(tmpdir)>a;b.py`, confirmed and erased), PV-14 (rc 0 for all four), PV-20's second half (from a scratch subfolder `<c(tmpdir)>pv20d/`, `saving("../pv20b.py") server` writes `<c(tmpdir)>pv20b.py`, erased).
    In `test/test_adversarial.cscript`, flip P2-80 (from a scratch subfolder, `saving("../p280.html")` writes into its parent, confirmed and erased; nothing written outside `c(tmpdir)`), P2-85c (rc 0), P20-08 (the `.htm` build gives rc 0 with needle `saved to <p2008e>.html`, erased; the launch needle `To launch: python '<p2008y>'`), P20-16 (the `sav(` and `///` forms from a scratch subfolder write into its parent; `SAVING()` still r(198), no file). Update both summary lists (:3662-3664 and the header).
    In `test/test_nodraw_honoured.cscript` ND-04 (:114-134), add `display(on)` to each `_dash_browser_wanted` call.
    Append one `Flipped:` line per node to `$S/12-flips.txt`.
  ]]></action>
  <verify><![CDATA[Through the driver, `test_path_validation.cscript` prints `ALL CHECKS PASSED`; `test_adversarial.cscript` and `test_nodraw_honoured.cscript` report no FAIL; `find <the main checkout and $WT> -maxdepth 4 -name 'p2016*' -o -name 'evil.html' -o -name 'p280.html'` prints nothing.]]></verify>
  <done>Every pinned case that asserted the old refusals asserted twoway's acceptance instead, wrote only under c(tmpdir), and kept its original meaning where the meaning was not the refusal.</done>
</task>

<task type="auto" id="12-11">
  <name>Flip the decider cases and register units</name>
  <files>test/test_serve_browser.cscript, test/program_coverage_map.py</files>
  <action><![CDATA[
    In `test/test_serve_browser.cscript`, add `display(on)` to the `_dash_dashboard_browser` calls of SB-01..SB-05 (:66-90), with a comment that the suite runs in batch, where no window opens now, and `display(on)` keeps each case testing its own reason. Append their `Flipped:` lines, and one for the SB-07..SB-11 block (the seam set in 12-02), to `$S/12-flips.txt`; add one for HC2-30, HC2-30b, HC2-34a, HC2-34e, HC2-34f (the seam set in 12-04).
    In `test/program_coverage_map.py`, add the seven entries of TR-12.11 under the two S12 anchors, alphabetical.
  ]]></action>
  <verify><![CDATA[Through the driver, `test_serve_browser.cscript` prints SB-01..SB-38 PASS and `All serve-browser tests PASSED.`; `python3 -m pytest test/test_program_coverage_map.py test/test_no_orphans.py test/test_file_headers.py test/test_function_test_map.py test/test_statistical_helpers.py -q -n0 -k "coverage or orphan or header or function_test_map or EveryName"` reports 0 failed.]]></verify>
  <done>Every decider case tested its own reason under an explicit display, and every new Stata and Mata unit named the cases that exercise it.</done>
</task>

<task type="auto" id="12-12">
  <name>Update the help for the command form</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Make the dash.sthlp edits of TR-12.12, in order: the three syntax lines (:50-51, :75, :93), the new prefix paragraph after :129, Difference 2 and the saving() paragraph (:452-470), the Subcommands line (:838), the Dashboard Options rows (:924-926, :946-949, :950-956), the nobrowser_global paragraph (:959-977, keeping the five phrases test_help_claims_2.py pins), and S04's character-rule text rewritten to its final form under `{marker saving_chars}` with S04's Windows sentences kept verbatim. Edit no other paragraph (R3).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_command_form.py test/test_help_claims_2.py test/test_help_conformance.py test/test_help_claims_8.py -q -n0 -p no:cacheprovider` reports 0 failed; `grep -c 'traversal allowed' dash.sthlp` prints 0.]]></verify>
  <done>The help stated the prefixes, saving()'s replace and asis on every route, the batch and set graphics off rule, and the final character rule, in the words the tests pin.</done>
</task>

<task type="auto" id="12-13">
  <name>Certify the command form through the slot</name>
  <files>none</files>
  <action><![CDATA[
    Run through the driver, at most three at once (the slot enforces it), each with its own log: `test_wp30_truth` (`WP30_ONLY=S12`), `test_path_validation`, `test_serve_browser`, `test_nodraw_honoured`, `test_help_claims_2`, `test_adversarial`, `test_json_escaping`, `test_server_build`, `test_serve_options`, `test_program_coverage`, `test_mata_library_guard`, `test_ado_loads`, `test_parser`, `test_e2e_single`.
    Run `python3 -m pytest test/test_mode_parity.py -q -n0` (G3 as a guard: no CORPUS change). Do not run `run_all_cscripts.do` or `make cert`.
    A `SKIP: Python not available` line means `python_exec` was dropped from `~/.stata19/console/stata19.rc` by concurrent sessions: report it and re-run that script alone (a skip is not a pass). Write the PASS counts to `$S/12-cert.txt` and check AC-12.6.
  ]]></action>
  <verify><![CDATA[Every listed log has no line matching ` FAIL\b|^r\([0-9]+\);$|SKIP` (`grep -cE " FAIL\b|^r\([0-9]+\);$|SKIP" "$S"/run_test_*.log` prints 0 for each); test_mode_parity.py reports 0 failed; AC-12.6 holds.]]></verify>
  <done>Stata itself certified the prefix, the grammar, the character rule, the browser rule and the launch line in both modes, and the scripts nearest them stayed green.</done>
</task>

<task type="auto" id="12-14">
  <name>Close P1.27 and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP30_OPEN["P1.27"]`. Close that BUGS.md entry in place (`- [x]`) with: `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.27). dash reads twoway's command form: a leading twoway, tw, two or graph twoway (gr, and tw to twoway after it) is read off once by _dash_strip_prefix and the rest drawn as the plain command, saved and served; twow, twowa, gra, grap and capitalised prefix words are refused r(199) "command twow is unrecognized" and a second prefix r(198) "twoway is not a twoway plot type". One saving() grammar (_dash_saving_parse over _dash_saving_split) serves the one-line form and dash build, HTML and server, read from the text as typed (_dash_seg_saving; dash build declares SAVing(string asis)): replace and asis as twoway reads them, any other sub-option and an unquoted name with a blank refused r(198) in twoway's words, an empty name Graph, .gph replaced and .html or .py appended on both routes. saving() accepts a .. segment and ; & | < > as twoway does and refuses a double quote, backquote, $, every control character (as dash_render.py's _validate_output_path) and a leading -; dash serve's private --launch path still refuses .. (M11). The shell opener single-quotes on Mac and Unix and declines cmd metacharacters on Windows (WP-30 P1.29); the To launch line of dash build, server is single-quoted on Mac and Unix and names % and ! on Windows. In batch and after set graphics off no window opens on any route (_dash_display_on, read by _dash_browser_wanted and _dash_dashboard_browser); the path is printed and a preview says it is temporary; interactive Stata still opens one. Pinned by test/test_command_form.py::TestOneSavingGrammar::test_every_route_calls_the_one_parser, test/test_packaging.py::TestNoUnsuppressableBrowserWindow::test_each_decision_reads_the_switches, test/test_adversarial_matrix.py::TestRendererOutputPath::test_a_parent_segment_is_written_where_twoway_writes, test/test_path_validation.cscript PV-37, test/test_path_validation.cscript PV-40, test/test_serve_browser.cscript SB-32, test/test_serve_browser.cscript SB-38, test/test_wp30_truth.cscript CF-01, test/test_wp30_truth.cscript CF-05; fixture test/fixtures/twoway_command_form_truth.json. Residual, deferred (WP-30): dash twoway alone is refused where twoway draws an empty graph (P2.56); c(mode) under Windows batch and the GUI is unmeasured (the platform package).`
    Delete the `"P1.27"` key line from `WP30_OPEN`.
    In CHANGELOG.md replace the marker at the end of `### Changed behaviour (may need your do-files changed)` in place with the three lines under that heading in Notes ("CHANGELOG lines"), and the marker under `### Fixed in WP-30` with the three lines given there, verbatim, each ending `(WP-30, P1.27)`.
    Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Run `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run, `<scratch>/full_suite_queue.sh "$WT" <scratch>/12-full-1.log`, waited for on its `exit=` line.
    `git add -f test/fixtures/twoway_command_form_truth.json`, then stage only: dash.ado, dash_parse.mata, dash_render.py, dash.sthlp, BUGS.md, CHANGELOG.md, scripts/extract_twoway_command_form_truth.do, test/test_command_form.py, test/test_path_validation.cscript, test/test_serve_browser.cscript, test/test_nodraw_honoured.cscript, test/test_help_claims_2.cscript, test/test_adversarial.cscript, test/test_wp30_truth.cscript, test/test_packaging.py, test/test_adversarial_matrix.py, test/test_cscript_hygiene.py, test/program_coverage_map.py, test/test_tracking_documents.py. Check `git diff --cached --name-only` against that list plus the fixture (G6): no project instructions file, .gitignore, AGENTS.md, `.ultraplan/` or scratch file.
    Write the message to `$S/12-message.txt` in the boundary's form; run G7 on it; confirm `git branch --show-current` prints `wp30-s12`; `git commit -F "$S/12-message.txt"`; run G7 on `git log -1 --format=%B`. Report the sha to the merger.
  ]]></action>
  <verify><![CDATA[The full run's log shows 0 failed; `grep -c '<!-- WP-30 P1.27 -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.27": "' test/test_tracking_documents.py` prints 0; `git log -1 --format=%s | grep -c '(WP-30 P1.27)$'` prints 1; G7's check on `git log -1 --format=%B` prints 0; `git show --name-only --format= HEAD | grep -c .` prints 20.]]></verify>
  <done>P1.27 was closed in BUGS.md naming existing tests, its two CHANGELOG markers carried the changed and fixed behaviour, and one green commit on wp30-s12 was ready for the merger.</done>
</task>

## Section completion criteria

- In batch (and after `set graphics off`, reached through `_dash_display_on`'s arguments), the one-line form, `dash build` and `dash serve` open nothing; the path is printed and a preview says it is temporary; with the seam or `display(on)` every earlier rule (nobrowser, `$dash_nobrowser`, nodraw, `saving()`) still decides.
- Every prefix spelling twoway accepts gives the unprefixed graph, saved and served; every one it refuses is refused with its rc and words (CF-01..CF-04).
- Every `saving()` form of the fixture behaves on the one-line form as twoway's (CF-05); `dash build` HTML and server share the grammar (PV-38); `..` and `; & | < >` are written (CF-06, PV-40, PV-41); the five sink-tied kinds are refused (PV-42); `--launch` keeps `..` refused.
- The launch line is single-quoted on Mac/Unix and survives a hostile path in sh (SB-37, SB-38); the opener gets a hostile path as one argument (CF-22).
- The help states the prefixes, `asis`, the batch rule and the final character rule; `$dash__display` is in no user-facing text.
- One green commit `(WP-30 P1.27)` on `wp30-s12`, with its failure text, `Regression:`, `Flipped:`, `Fixture:` and `BUGS.md:` lines and no tool or vendor name; the entry closed in place, its key deleted, both markers replaced.

## Notes

**Traps.**

- **`syntax … (string)` strips quotes** (E9). Never feed `_dash_saving_parse` a value that went through `SAVing(string)`; `_dash_plot` re-reads the text with `_dash_seg_saving`, `_dash_build` declares `asis`.
- **The fold must run after the as-typed read**, or `saving("a,b.html") replace` folds onto the stripped text.
- **`r()` is clobbered** by `_dash_display_on` (rclass): copy `r(nodraw)` first in `_dash_dashboard_browser`, and read `r(on)` before any other rclass call in both deciders.
- **The suite runs in batch.** A new decider test without `display(on)` or the seam asserts the batch rule, not its own reason. `cert_file_has` clobbers `r()`: copy `r(open)`/`r(flag)` into locals before any log search.
- **Never write outside `c(tmpdir)`.** The flipped `..` cases run from a scratch subfolder (`cd` into it under `capture noisily`, `cd` back on every path); `test/` is the cscripts' working folder and its parent is the repository.
- **`c(tmpdir)` must hold no blank** for the unquoted `` saving(`x') `` forms many scripts use: true for the slot's `STATATMP` and the worktree; a path with a blank must be quoted now, as in twoway.
- **The seam is not a user feature.** Do not document it, do not read it outside the two deciders, do not set it in a script without a stub first on PATH or the ado-path, and always drop it.
- **`_dash_launch_app` is not edited.** The index's batch-4 line names its `--show` path; measured (E2), the served decision reaches it only through `_dash_dashboard_browser`'s `r(flag)`, which this section changes, and `test_no_browser_and_a_timeout` pins the launcher's side. S23 and S46 therefore meet the function as it is at `c96facd`.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; scripts then exit 222 and a SKIP is not a pass (index E5).
- **A cscript stops at its first failing assert**, so a red-first log shows only the first failure of each script.

**Merge rules touched.**

- **R1:** PV-35..44 and SB-31..38 are contiguous runs after S04's PV-34 and SB-30, except SB-36, which must sit in the stub-renderer block, and CF-21/22, which must sit in HC2's stub-opener block (the only places their stubs exist). The CF-01..08 block is S12's stub block in `test_wp30_truth.cscript`, helpers above its header. No runner block, no hygiene pin moves.
- **R2:** no copy-list change; `program_coverage_map.py` entries under the S12 anchors only; `function_test_map.py` unchanged.
- **R3:** only the Syntax, Differences (:452-470), Subcommands (:838) and Dashboard Options (:916-980) paragraphs named in TR-12.12. S11 edits Differences' Stylelists paragraph (:786-788) in the same batch: a different paragraph.
- **R4:** the two P1.27 markers only.
- **R5:** BUGS.md's P1.27 entry in place and the `"P1.27"` key line.
- **R6:** every new program opens `version 19`; A154's order in `dash` (S12's strip after `_dash_require_mata`); `_needed` gains one line — S10 and S11 may add names to the same list in batch 4, so on a conflict the merger keeps every section's names; the Mata block sits after `_dash_path_badchar`, away from S10's `_dash_rep_subkey` and S11's splitter; header entries after `_dash_path_badchar`'s.
- **R7:** the new fixture carries the `_meta` stamp and is added with `git add -f`; S04's `saving_chars_truth.json` is read, never regenerated.
- **R9:** E13's flips, one `Flipped:` line each.
- **R10:** no combined pin moves (`test_abbreviations.py:607` stays 15).
- **R12:** no one-editor renderer symbol is edited.

**Commit body line forms** (index deltas): `Regression: … -- failed at <batch-4 base sha> with <text>`, `Flipped: <node> -- <old expectation> was wrong because <why>`, `Fixture: test/fixtures/twoway_command_form_truth.json (scripts/extract_twoway_command_form_truth.do)`, `BUGS.md: "<title>" (closed)`. The body names the threats of TR-12.15 (G9).

**CHANGELOG lines** (12-14 writes each line below verbatim, as a list item, in place of the markers).

Under `### Changed behaviour (may need your do-files changed)`:

- In batch (c(mode) batch) and after `set graphics off`, dash opens no browser window, as twoway displays no graph there: `dash build` and the one-line form write the page and print where it is, a one-line preview adds that it is temporary and that saving() keeps a page, and `dash serve` starts without a browser. A do-file run with `stata -b` used to open one tab per dashboard. Interactive Stata, the console included, still opens the window. (WP-30, P1.27)
- saving() is read as twoway reads it, on the one-line form and on `dash build`: a sub-option other than replace and asis, written in full, in lower case and once each, is refused with twoway's "option bogus not allowed", r(198), and an unquoted name holding a blank with "invalid syntax,  file.html not allowed", r(198). `saving(n, bogus)` used to write a file named "n, bogus.html" and `saving(my file.html)` wrote "my file.html"; put such a name in quotes. (WP-30, P1.27)
- `twow`, `twowa`, `gra` and `grap` (and a capitalised TWOWAY or Graph) in front of the plots are refused with r(199), "command twow is unrecognized", as Stata refuses them; they gave r(198), "unrecognised plot type". A second prefix, `dash twoway twoway scatter mpg weight`, says "twoway is not a twoway plot type", r(198). (WP-30, P1.27)

Under `### Fixed in WP-30`:

- `twoway`, `tw`, `two` and `graph twoway` may precede the plots, as in twoway: `dash twoway (scatter mpg weight) (lfit mpg weight)` was refused, r(198), "unrecognised plot type 'twoway'". (WP-30, P1.27)
- One saving() grammar serves the one-line form and `dash build` (HTML and server): `saving(f, asis)` wrote a file named "f, asis.html", `saving("n, replace")` wrote n.html with replace applied, and `dash build, saving(f, replace)` and `dash build, saving(f)` were refused, r(198). Now replace and asis are read as twoway reads them, a comma inside quotes stays in the name, `saving(, replace)` writes Graph.html, and `dash build` appends .html (.py with server) and replaces .gph as the one-line form does. (WP-30, P1.27)
- saving() accepts a `..` segment and ; & | < > in a path, as twoway does (`saving("../out/d.html")` and `saving("R&D.html")` were refused, r(198)); a double quote, backquote, $, any control character and a leading - are still refused, and dash serve's private app path still refuses `..`. The "To launch:" line of `dash build, server` puts the path in single quotes on a Mac and Unix, so a pasted line runs the file it names. (WP-30, P1.27)

**Notes for the closeout (S58; A145).**

- **GAPS2 I14 parts a and b** are closed: the `..` and `; & | < >` refusals are removed on every written path (Mata and Python), with only sink-tied checks left (I14 plan step 1). Parts c and d are S04's. Tracked line: `- **Tracked:** Closed in WP-30, BUGS.md "<title>", commit <sha>`, and `(WP-30, GAPS2-I14-a)`, `(WP-30, GAPS2-I14-b)` appended to the Resolution.
- **CRIT-02, CRIT-03, CRIT-04, CRIT-09** exist only as ids in DROPIN-REMAINING.md:161; the DROPIN P1.27 row is marked closed with the sha.
- **ROADMAP:** P2.56 (`dash twoway` alone refused; twoway draws an empty graph) is the register's row. Record as documented differences, not new items: `dash graph <non-twoway word>` keeps r(198) where twoway gives an internal r(4023); `saving(f, asis) nodraw` writes the page where twoway gives r(601); `saving()` over an existing file without replace keeps dash's r(198) where twoway gives r(602). The platform package gains: `c(mode)`/`c(graphics)` under Windows `/e`/`/b` batch and GUI Stata, and the Windows `To launch:` line, unmeasured (M4).
- **AGENTS.md invariant** (E7: only if it has no uncommitted edits): "A dash command's prefix, saving() grammar and browser rule are twoway's: test/test_wp30_truth.cscript CF-01..08 compare them with test/fixtures/twoway_command_form_truth.json; `$dash__display` is a test seam, read only by the two browser deciders, never documented."

**Maintainer question (A139 exception for batch 4).** `_dash_plot` is edited by S10 (one hunk: `_dash_subopt_check legend` before the axis-check line at :5324, and `zlabel`/`title` after its exit line) and by S12 (the as-typed saving paragraph above :5540 and the fold at :5560-5568). `_dash_require_mata`'s `_needed` list (:237-255) is edited by S10 and S12 (both after :255) and by S11 (after :250). A139 says no two sections of one batch edit the same function. No re-batching fits: batches 5 to 8 hold three sections each, S12 must precede S22 (batch 8), and S10 must precede S18 (batch 6). **Recommendation: grant the exception for these two programs in batch 4.** The `_dash_plot` hunks are more than 200 lines apart, and the `_needed` additions are separate continuation lines. The merge order S10, S11, S12 is kept, the merger applies each later patch with `git apply -3`, and it keeps every section's names in `_needed` (R6). If refused, S10's three `_dash_subopt_check` calls must move into `_dash_axreq_check` (Mata), with the numlist checks done in Mata; that is a redesign of TR-10.6 to be planned before batch 4's base is recorded.

**Maintainer question (P1.27.6 reading).** Ruling P1.27.6 (A91) limits `$dash__display` to "the HC2 controls". `test_serve_browser.cscript` SB-07..SB-11 are end-to-end controls of the same kind (`dash serve` through a stub renderer, which can open nothing): without the seam, in batch, SB-07/08/10 pass vacuously and SB-09 fails. This section reads A91's "end-to-end controls" to include that block and fences both under the same hygiene rule. If the maintainer strikes that reading, SB-09 is flipped to assert `--no-browser` and SB-07/08/10 are left asserting only the batch rule, which loses `dash serve`'s per-reason coverage. **Recommendation: ratify the wider reading.** SB-07..SB-11 are end-to-end stub controls of exactly the HC2 kind: `dash serve` runs a stub renderer that can open nothing. `TestTheDisplaySeamIsFenced` holds both blocks to the same fence (stub first, seam dropped after), so the seam reaches no sink a user's session does not already reach.

**Line numbers** are `c96facd`'s. S01, S03 and S04 land first and shift dash.ado, test files and dash.sthlp by a few lines; find each anchor by its text.
