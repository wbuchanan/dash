# Section 06: One note channel (P1.26 part a)

> Part of: WP-30 · Items: P1.26 part a (entry `P1.26a`) · Risk: yellow · Batch: 2 · Depends on: 01 · Blocks: 22, 23, 26, 29, 33, 34, 41 · Tasks: 13, 1 commit · Case ids: NC-01..06

## Review amendments

- Blocker: the S06 truth block kept its own tally (`s06_fail`, `assert $s06_fail == 0`), so `WP30_ONLY=S06` ended "no case ran", r(9), and a failure would abort every later block; NC-01/NC-02 now report through `_w30_expect`/`_w30_done` (TR-01.10.4), write their logs and page under `` `w30_work' `` (they used `c(tmpdir)`), erase them, and 06-12 requires `ALL CHECKS PASSED`.
- Minor: 06-01 counts distinct NC case ids, since a case can print several FAIL lines.
- Open question resolved from the register (P1.26.2 "twoway's measured visibility", P1.26.4/A84 form): both defaults stand; no maintainer question remains beyond ratifying item 13 as written.
- Spot-checked at HEAD: dash_render.py `_dash_warn_once` :15363, `__main__` try :37627-37628, `_DASH_NOTE_FILE` print :36905, `_note` :1663, scheme note :6420, estimator note :28388; dash.ado :446, :3767, :3777, :4654, :4995, :6488, :7353; dash_parse.mata `_dash_say` :676, :4255, :4264. All hold.
- Batch 2: S06 shares no function with S04 or S05; shared files are edited in distinct hunks (dash_render.py: S04 :1161/:3660-3792/assembly, S06 :64/:1663/:15342/`main`/`__main__`; dash.ado `_needed` :242 vs :247 under R6; `scripts/release_verdict.py` S05 floor functions vs S06 `DIAGNOSTICS`; dash.sthlp distinct paragraphs).
- Checked: M6 (no new note; only the channel changes, silent where twoway is untouched), A150 (lands last, reads partners' needles), security (SMCL escape twin, 4,000 bound, constant Mata format).
- Rejected: none.

- (cross-file pass) 06-13 verify: added the key-deletion check `grep -c '^    "P1.26a": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
The review pass applied both lenses.
- Row 44 checked (ratification 06oct2026): S06 and S58 agree. dash.sthlp's "named in a warning" is not reworded in WP-30 (three tests pin it); S58 files a P3.3 note (R58-14). The Help terminology note now says so instead of "the closeout may reword them".
- Row 4 bookkeeping (ratification 06oct2026): S33 adds no note through this channel (no unread-scheme-key note); the Later sections list drops it. The Blocks edge to S33 stays (batch order; S33's no-note tests run against this channel's output).

## Overview

**What is wrong today.** DROPIN-REMAINING.md P1.26 (line 146) says that notes "print as raw UserWarnings with internal paths" and that "a session `warnings` filter of "ignore" silences them; one of "error" turns a note into r(7102)". GAPS2 X4 (GAPS2.md:1976) adds that the certification log carries the raw Python form (X4-d). Research p1-26 (m7) found one more fault: dash.ado's own notes are hidden by `quietly`, while the renderer's survive it. So dash is inconsistent with itself and with twoway.

Measured at `c96facd` (StataNow 19.5, probes quoted under Evidence):
- `dash scatter mpg weight, mcolor(notacolor)` prints `…/dash/dash_render.py:8679: UserWarning: dash: mcolor(notacolor) is not a recognised colour; using the scheme's default.` and then a Python source line, in red (SMCL class `{err}`).
- After `python: warnings.filterwarnings("ignore")` no note prints, rc 0. After `python: warnings.simplefilter("error", UserWarning)` the render fails: a 60-line traceback, r(7102).
- `quietly dash scatter mpg weight, mcolor(notacolor) play(x)` prints the renderer's red warning but hides dash.ado's `dash: ignoring unsupported option(s): play()`.
- twoway prints `(note:  named style notacolor not found in class color, default attributes used)` in text colour. It shows under `quietly` and under `set output error`, and `capture` hides it.

**After this section.** Every note dash prints in Stata's session takes one path, the way twoway prints its notes. This holds for the saved build, for `dash build, server` and for the build phase of `dash serve`. A note is one line, `(note:  dash: …)`, in text colour (`SFIToolkit.errprintln("{txt}…")` from the renderer, `errprintf("{txt}…")` from Mata). It shows under `quietly` and `set output error`, and `capture` hides it. It is printed once per command, SMCL-escaped, at most 4,000 characters, and never names a file of dash or a source line.

A session's Python warnings filters, `PYTHONWARNINGS` included, neither hide a dash note nor make it an error. They still govern every other warning.

The two notes dash repeats in twoway's own words are `(note:  regress|fracpoly could not fit model)` and `(note: scheme X not found, using s2color)`. They print as twoway prints them, as plain text that `quietly` hides (measured below). The log gates `help_examples.FLAGGED` and `release_verdict.DIAGNOSTICS` learn the new form, and the 29 `UserWarning` needles in four certification scripts now count note text. The served app's own sessions and the launcher's relay are P1.26 part b (S23).

**Why one section, and why first.** X.2/A150 rules that the channel lands before any other note is added or reworded. Otherwise every later section's needles would migrate twice. S06 runs in batch 2 and merges last of S04, S05 and S06, so it sees its partners' work at landing (Notes, trap 9).

`_dash_warn_once`, `_dash_style_note` and `_dash_reset_notes` are CRITICAL, and no line of them changes. `warnings.warn` stays dash's internal mechanism, which about 16,700 tests capture. Only the boundary where a note leaves Python for Stata changes.

**Test order and commit rule (rule 7, A141).** One cycle, one commit `(WP-30 P1.26a)`.
- 06-01 and 06-02 write every regression test, run them against the unmodified tree, and save `<scratch>/06-P1.26a-failure.txt`. They never commit.
- 06-03 to 06-10 make the fix, flip the pinned tests (each with a `Flipped:` line) and update the help.
- 06-11 and 06-12 certify.
- 06-13 closes the BUGS.md entry, deletes its `WP30_OPEN` key, replaces both CHANGELOG markers in place, runs the full suite once through the queue and commits.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every command's visible output changes form, and about 40 test pins move with it

**Why.** Every note a user sees changes in three ways at once: its form (`(note:  dash: …)`), its colour (from red to text colour), and its visibility (it now shows under `quietly`, and `capture` hides it). Tests that read logs move with it:
- 29 `UserWarning` needles in four certification scripts;
- three exact-line pins (HC8-01, -06, -07);
- three `startswith("dash: note:")` readers (PF-09, and PF-11 and PF-12 through `_pf_notes`);
- three source, help and output pins in `test_private_files.py`;
- two writer tests;
- the two log gates.

The `__main__` block calls `main`. `main` is LOW (7 callers) without tests, CRITICAL (243) with them, and treated as HIGH as index batch 2.0 lists it.

**Risk factors.**
1. A needle that keeps "UserWarning" would turn vacuous: a log full of notes would pass an absence check.
2. A pinned test that reads log text in a script nobody runs, since `make cert` is not a section's to run (index, Full-suite runs, rule 3).
3. The gates go blind. 98 of the 121 literal warn messages hold none of `DIAGNOSTICS`' other needles (research critic, item 2).
4. The session's filters could leak if the scope does not restore them, for example on a KeyboardInterrupt.
5. `errprintln` reads SMCL, so an echoed `{stata …}` would become a clickable command.
6. Partners S04 and S05 might add a needle that counts Python warnings (A150).
7. Later sections may reword the colour, symbol or by() notes that the tests use.

**Mitigation.**
1. Each absence check counts two needles: `(note:` and `Warning:`, the second catching any Python warning line. The controls (render_log_clean check 5, CS-10) must count exactly one note.
2. 06-12 runs every certification script whose text holds a note needle, 29 scripts, through the driver.
3. 06-02 writes failing gate tests first, and 06-07 adds the note pattern to both gates.
4. `warnings.catch_warnings` restores both `filters` and `showwarning` on any exit. A test raises inside the scope and checks identity afterwards.
5. `_dash_smcl_escape`, the twin of Mata `_dash_smcl_text` (parity in NC-06), plus a 4,000-character bound.
6. 06-13 reads the partners' worktree diffs, read-only, for new needles before committing. A miss is S06's to fix after landing (index step 2).
7. Every new test is relational. It compares the notes printed under a filter with those printed under default filters, or counts the `(note:  dash: ` form, never a note's wording. The relational form covers mcolor, msymbol and by() notes.

**Prototype (03oct2026, scratch, not in the repository).** The scope, emitter and escape of TR-06.1 to TR-06.3, run around `warnings.warn` under each session filter:

```
ignore  | other: shown/ignored | said: 2 | (note:  dash: mcolor({stata x}) is bad.) || dash: graph 'g' plot 2 (lfit): (note:  regress could not fit model)
error   | other: raised        | said: 2 | (same two lines)
default | other: shown/ignored | said: 2 | (same two lines) || …/proto.py:61: FutureWarning: other thing
filters restored: True True
```

A non-dash `FutureWarning` stayed under the session's filter: ignored, raised, or shown. The Mata twin printed the same form under `quietly` and nothing under `capture` (probe p5, under Stata truth).

## Dependencies

- **Depends on: 01.** S01 opens the BUGS.md entry `P1.26a` and its `WP30_OPEN` key. It places the markers `<!-- WP-30 P1.26a -->` in `### Changed behaviour (may need your do-files changed)` and `### Fixed in WP-30` (index, P1 coverage). It also writes S06's stub block in `test/test_wp30_truth.cscript`, and the map anchors `# WP-30 S06 (P1.26a): One note channel` at the end of `FUNCTIONS` and of `COVERAGE["dash_parse.mata"]` (A148).
- **Ratification.** Ratification item 13 (A82, A84) binds this section. Two readings of the measured truth are written here and must be confirmed with it (see "Open question" at the end of Notes).
- **Blocks: 22, 23, 26, 29, 33, 34, 41.**
  - Each adds or relays a note, so it uses `_dash_emit_note`, Mata `_dash_note` or a `dash…: `-prefixed `warnings.warn` raised inside `main()`, and counts note text as TR-06.11 does.
  - S23 copies `_dash_smcl_escape` and `_dash_emit_note` into the served app (index R2 row S23). It reads `_dash_said`, the set the scope yields, for its `said=` de-duplication.
- **Parallel batch: 2** (S04, S05, S06; merge order S04, S05, S06).
  - S04 owns the page assembly, `_dash_served_template`, `_dash_open_page` and its Windows written-not-opened line, and the `saving()` help paragraph.
  - S05 owns `_dash_pymin`, `_dash_require_python`, `dash_setup`, conftest and the floor script.
  - No function is shared. S06 lands last so it can migrate a partner's needle (A150).

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines; dash.ado 8,487; dash_parse.mata 6,093; dash.sthlp 3,822). S02 and S03 land in batch 1 and S03 adds lines at the top of `dash`, so dash.ado's line numbers drift by batch 2's base. Find each site by the quoted text, and record the shift in the task's progress output.

### E1. The renderer's notes are Python warnings, and the entry point has no guard

All 87 `warnings.warn` calls raise `UserWarning`: 80 name it and 7 take the default (AST count; 94 lines match the text `warnings.warn(`). Their message starts are `dash:` (106 literal starts), `dash scheme:` (14) and `dash kpi:` (through `_dash_style_note(…, prefix="dash kpi")`, dash_render.py:17108). The helpers that de-duplicate per render are CRITICAL and are not edited (dash_render.py:15350-15368):

```python
15350  _DASH_NOTED: set = set()
15353  def _dash_reset_notes():
15363  def _dash_warn_once(key, message, stacklevel=4):
15364      """``warnings.warn(message)`` unless *key* was already raised this render."""
15365      if key in _DASH_NOTED:
15366          return
15367      _DASH_NOTED.add(key)
15368      warnings.warn(message, UserWarning, stacklevel=stacklevel)
```

dash.ado runs the renderer in the user's own Python session. `_dash_do_render` runs it at dash.ado:446 and `_dash_serve` at :8473:

```
446      python: _dash_render_ns = runpy.run_path("`_py_renderpy'", run_name="__main__")
```

The `__main__` block calls `main()` with no warnings guard (dash_render.py:37624-37639):

```python
37624      import sys as _sys
37625      _report = globals().get("_dash_launch_report")
37626      _launching = args.mode == "server" and args.launch
37627      try:
37628          _written = main(args.spec, args.data, args.output, args.mode,
37629                          args.port, launch=_launching,
37630                          private_output=args.private_output)
37631      except KeyboardInterrupt:
37632          if not _launching:
37633              raise
```

### E2. Measured at `c96facd`

**In Stata** (research m1; my p2, 03oct2026, `set linesize 255`):

```
. quietly dash scatter mpg weight, mcolor(notacolor) play(x) saving(p2e.html, replace)
/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py:8679: UserWarning: dash: mcolor(notacolor) is not a recognised colour; using the scheme's default.
  color, alpha = self.tr.parse_color_alpha(
. capture dash scatter mpg weight, mcolor(notacolor) play(x) saving(p2f.html, replace)
. display "rc=" _rc
rc=0
```

The ado's `dash: ignoring unsupported option(s): play()` is missing under `quietly` (m7). The renderer's red warning, its path and its source line survive. Research m1 D2: under `filterwarnings("ignore")` no note, rc 0. D3: under `simplefilter("error", UserWarning)`, `RuntimeError: dash_render: failed to build figure ''`, rc 7102.

**In Python, both build modes** (probe py1/py2, 03oct2026): a spec with `scatter mpg weight, mcolor(notacolor)` and `by(foreign, graphregion(color(red)))`, run as `__main__` with `--mode standalone` and `--mode server`:

```
standalone default -> UserWarning: dash: by() sub-option(s) not implemented and ignored: graphregion(color(red))
                      UserWarning: dash: mcolor(notacolor) is not a recognised colour; using the scheme's default.
server     default -> UserWarning: dash: by() sub-option(s) not implemented and ignored: graphregion(color(red))
standalone/server under simplefilter("ignore") -> stderr lines: 0
standalone/server under simplefilter("error")  -> RAISED UserWarning dash: by() sub-option(s) not implemented and ignored: …
PYTHONWARNINGS=error::UserWarning python3 -c "…run_path('dash_render.py', run_name='__main__')" -> rc=1, 36 stderr lines, last "UserWarning: dash: by() sub-option(s) …"
PYTHONWARNINGS=ignore                                                                       -> rc=0, 0 stderr lines
```

`by(, graphregion())` stays named and not drawn through WP-30 (IR-9). Its note is the stable build-time note in both modes that the new tests use.

**The certification log.** `.ultraplan/handoff/wp29-run_all_cscripts.log` (02oct2026) has 154 lines holding "UserWarning". 87 match `dash_render\.py:[0-9]+:` (GAPS2 X4-d said 21; research critic, item 10).

### E3. The note sites of dash.ado and dash_parse.mata

`_dash_say` prints through `printf` (dash_parse.mata:676-680), and `quietly` hides `printf`:

```
676  void _dash_say(string scalar style, string scalar before,
677                 string scalar value, string scalar after) {
678      if (!anyof(("err", "txt", "res"), style)) style = "txt"
679      printf("{%s}%s\n", style, _dash_smcl_text(before + value + after))
680  }
```

The manifest says "the 11 txt note sites". At `c96facd` there are 11 `_dash_say("txt", …)` calls in dash.ado. Four of them are status lines, not notes (research critic, item 7), and four notes are printed some other way. The binding inventory is this table. Each **note** row moves to Mata `_dash_note`; the other rows stay as they are.

| # | Where (`c96facd`) | Program / function | Text | Disposition |
|---|---|---|---|---|
| 1 | dash.ado:3767 | `_dash_process_segment` | `dash: <ptype> ignored '<left>' at the end: <why>` | note → `_dash_note` |
| 2 | dash.ado:3770 | `_dash_process_segment` | `dash: <ptype> ignored '<left>' at the end, too little for another …, as twoway does.` | note → `_dash_note` |
| 3 | dash.ado:3777 | `_dash_process_segment` | `display as text "dash: pci draws no labels, …"` | note → `_dash_note` |
| 4 | dash.ado:4654 | `_dash_tmp_open` | the R-8 privacy note `_to_note` (`dash: note: …`) | note → `_dash_note` |
| 5 | dash.ado:4690 | `_dash_tmp_preview` | `_tp_note` (`dash: note: …`) | note → `_dash_note` |
| 6 | dash.ado:4716 | `_dash_tmp_close` | `_tc_err` (`dash: <p> is not a dash run folder; nothing was removed.`) | note → `_dash_note` |
| 7 | dash.ado:4995 | `_dash_report_ignored` | `dash: ignoring unsupported option(s): …` | note → `_dash_note` |
| 8 | dash.ado:6488 | `_dash_render_immediate` | `dash: saving() writes HTML, not a Stata .gph; using …` | note → `_dash_note` |
| 9 | dash.ado:7353-7355 | `_dash_prepare_spec` | two `display as text` lines: `dash serve: ignoring option(s) that only apply to dash build: …` and `dash serve streams the dashboard; it writes no file.` | one note → `_dash_note` |
| 10 | dash_parse.mata:4255 | `_dash_fn_spec_tail` | `dash: the function points stored for graph '' are not dash's; …` | note → `_dash_note` |
| 11 | dash_parse.mata:4264 | `_dash_fn_spec_tail` | the same, naming the graph | note → `_dash_note` |
| — | dash.ado:6830, 8243 | `_dash_render_immediate`, `_dash_build` | `dash: dashboard saved to …` | status line; keeps `_dash_say` (twoway's `file x.gph saved` is hidden by `quietly`, p2 B) |
| — | dash.ado:8229, 8236 | `_dash_build` | `dash build: server app written to …`, `  To launch: python "…"` | status lines; keep `_dash_say` |
| — | dash.ado:4206, 4232, 5522, 5533 | `_dash_process_segment`, `_dash_plot` | `display as text "(note:  regress\|fracpoly could not fit model)"` before a refusal | twoway's own words, which `quietly` hides in twoway too (p3 A/B, p2 D); unchanged |

Excerpts:

```
3766              if "`_pci_stop'" == "empty" {
3767                  mata: _dash_say("txt", "dash: `ptype' ignored '", st_local("_pci_left"), "' at the end: " + st_local("_imm_empty"))
3776              if "`ptype'" == "pci" & `_pci_nlab' > 0 {
3777                  display as text "dash: pci draws no labels, as twoway pci draws none; a scatteri layer can label a point."
4652      // The privacy class (R-8): printed, never an error.
4653      if `: length local _to_note' {
4654          mata: _dash_say("txt", "", st_local("_to_note"), "")
4994      // The names are the user's text: shown as written, never as SMCL.
4995      mata: _dash_say("txt", "dash: ignoring unsupported option(s):", st_local("out"), "")
6487          if `_gph' {
6488              mata: _dash_say("txt", "dash: saving() writes HTML, not a Stata .gph; using ", st_local("saving_path"), "")
7352      if `"`_srv_na'"' != "" {
7353          display as text "dash serve: ignoring option(s) that only apply to dash build:" ///
7354              as result `"`_srv_na'"'
7355          display as text "  dash serve streams the dashboard; it writes no file."
```

```
4255          else _dash_say("txt", "dash: the function points stored for graph '",
4256                         "", "' are not dash's; that layer is drawn from its expression.")
4264                  _dash_say("txt", "dash: the function points stored for graph '",
4265                            nm[i], "' are not dash's; that layer is drawn from its expression.")
```

None of these sites sits inside a `quietly {` block or behind a `quietly`/`capture` call (awk over each program and grep of every call site, 03oct2026). The `quietly` that now shows them is the user's.

### E4. The renderer's other notes that do not pass through `warnings`

These two are the same fault in the same code (fold rule), so they join the channel:

- `main()` prints the unprivate-server-app note with `print()`, which `quietly` hides (dash_render.py:36903-36907):
  ```python
  36903          if not _dash_mode_private(written.st) and \
  36904                  not _dash_chosen_path(output_path):
  36905              print(_DASH_NOTE_FILE % (output_path,
  36906                                       stat.S_IMODE(written.st.st_mode)),
  36907                    flush=True)
  ```
- `_dash_write_stata_data._note` prints the UTF-8 note with `displayln`, which `quietly` hides (dash_render.py:1661-1666):
  ```python
  1661      def _note(what):
  1662          # What is named is a Stata name, never the text itself.
  1663          tk.displayln(f"{{txt}}dash: {what} holds text that is not valid "
  ```

The launcher's own lines are S23's and are not touched here. These are the link-file note `print("dash: note: " + p + …)` at dash_render.py:4334, and the token and parent-watch lines at 4256, 4412, 4433 and 36800.

### E5. Notes that carry twoway's own words

```python
6419                  warnings.warn(
6420                      f"dash scheme: (note: scheme {safe} not found, using "
6421                      f"s2color) -- '#include {safe}' in "
28386          where = f"graph {gname!r} plot {index}" if gname else f"plot {index}"
28387          warnings.warn(
28388              f"dash: {where} ({ptype}): (note:  {unfit} could not fit model)",
```

twoway prints both of these as ordinary text, which `quietly` hides (p3 B, p4 B). Help :263-265 says dash "gives the same note", and :3514 says so "in Stata's words". The emitter therefore prints these two as they are, with `displayln("{txt}…")`.

### E6. The SMCL helper the renderer must mirror

```
665  string scalar _dash_smcl_text(string scalar s) {
669      t = subinstr(s, char(0), "")
670      for (b = 1; b <= 31; b++) t = subinstr(t, char(b), "?")
671      t = subinstr(t, char(127), "?")
672      for (b = 128; b <= 159; b++) t = subinstr(t, char(194) + char(b), "?")
673      t = subinstr(t, "{", char(0))
674      t = subinstr(t, "}", "{c )-}")
675      return(subinstr(t, char(0), "{c -(}"))
```

Python's `sys.stderr` text is logged literally (research critic: c2.smcl shows `{c -(}stata …`). `errprintln`, `displayln` and `errprintf` interpret SMCL (m6, and probe p1 L, which printed `{stata display 1:x}` from `{c -(}…{c )-}`). Only the new path needs the escape.

### E7. The log gates go blind once "UserWarning" is gone

```python
# test/help_examples.py:563-578 (FLAGGED; used at :642)
    (re.compile(r"^dash: ignoring unsupported option\(s\):"), "names an option as ignored"),
    (re.compile(r"not implemented and ignored"), "names a sub-option as ignored"),
    (re.compile(r"\w*Warning:"), "prints a warning"),
    (re.compile(r"^(?:WARNING|ERROR|CRITICAL):[A-Za-z_][\w.]*:"), "prints a logged warning or error"),
    (re.compile(r"Traceback \(most recent call last\)"), "prints a Python traceback"),
# scripts/release_verdict.py:41-51 (DIAGNOSTICS; used by diagnostics() at :102)
    "ignor", "not implemented", "not found", "fallback", "not a recognised",
    "warning", "traceback", "error:", "drew nothing",
```

The anchored `^dash: ignoring` stops matching once the line begins `(note:`. `"warning"` stops catching renderer notes. A84 (P1.26.4) rules that both gates match twoway's `(note: …)` form.

### E8. Tests that pin today's behaviour (flip in place, never delete; re-measured by 06-01)

| Node / case | What it pins | Flip |
|---|---|---|
| `test/test_help_claims_8.cscript` HC8-01, HC8-06, HC8-07 | the exact line `dash: ignoring unsupported option(s): …` (`_hc_log … 1 1`) | the exact line `(note:  dash: ignoring unsupported option(s): …)` |
| `test/test_custom_scheme.cscript` CS-01..CS-08, CS-10, CS-11, CS-12, CS-14, CQ-01..CQ-03 (14 `_cs_log … "UserWarning"` lines, CS-12's 2, 5 header lines: 21) | the count of "UserWarning" lines | `_cs_notes`: the count of `(note:` lines, and 0 `Warning:` lines |
| `test/test_render_log_clean.cscript` checks [4/5], [5/5] (4 lines, 2 header lines: 6) | "UserWarning" 0, control 1 | `(note:` 0 / 1, and `Warning:` 0 |
| `test/test_render_locate.cscript` LOC-16 (:372) | "UserWarning" absent | `(note:` and `Warning:` absent |
| `test/test_json_escaping.cscript` JSE-17 comment (:456) | describes the Python form | comment only |
| `test/test_adversarial.cscript` PF-09 (:3597) | `startswith("dash: note:")` | `startswith("(note:  dash: ")` |
| `test/test_wp29_truth.cscript` `_pf_notes` (:3074-3075): PF-11 step 4 (absence), PF-12 (presence) | `startswith("dash: note:")` | `startswith("(note:  dash: ")` |
| `test/test_private_files.py::TestTheAdoUsesThePrivateDir::test_the_note_is_printed_once_per_command` (:2063) | `'_dash_say("txt"' in to` | `'_dash_note(' in to` |
| `test/test_private_files.py::TestTheHelpDocumentsTheTempfiles::test_it_states_the_note_and_the_anti_hijack_guard` (:2122) | the help holds `dash: note:` | the help holds `(note: dash:` |
| `test/test_private_files.py::TestTheNote::test_a_server_app_on_a_disk_without_permissions_is_written_and_noted` (:1312-1333) | the note on stdout, `dash: note: ` | on stderr outside Stata, `(note:  dash: `, once; none on either stream for the launch route |
| `test/test_string_value_export.py::TestTheWriter::test_text_that_is_not_utf8_is_read_through_ustrfix` (:368) and `::test_a_label_that_is_not_utf8_is_read_through_ustrfix` (:388, :397) | `displayln("{txt}dash: …")` | `errprintln("{txt}(note:  dash: …)")`; FakeSfi's `SFIToolkit` gains `errprintln`, appending to the same `shown` list |

These substring readers are unaffected: their text survives inside `(note:  …)` at linesize 255.
- `test_parser.cscript`: pci, scatteri and pcarrowi tails, pci labels, FX-11.
- `test_help_claims_2.cscript` HC2-25c.
- `test_custom_scheme.cscript` CS-15, whose include note now prints as is.
- `test_string_values.cscript`: the UTF-8 notes, through `cert_log_has`.

06-12 runs them all the same. None of the `test_private_files.py` checks of `_dash_run_open`'s returned `note` (:1097-1098, :1262, :1294) changes, because the returned string keeps `dash: note: `. The `startswith("dash: note: ")` readers in `test_serve_token.py` (:721, :1646) read the launcher's link-file note, which S06 does not touch.

### E9. Blast radius (GitNexus, main checkout, index at `c96facd`)

| Symbol | Edit | Result |
|---|---|---|
| `main` (dash_render.py) | the `_DASH_NOTE_FILE` call (one statement) | LOW, 7 impacted, with `--file dash_render.py`; CRITICAL, 243, with `--include-tests`. Treat as HIGH (index batch 2.0): warn before the edit. |
| `__main__` block | the `with` around `main(...)` | not a graph symbol |
| `_dash_write_stata_data` | `_note`'s one call | UNKNOWN (0 callers resolved); grep: dash.ado `_dash_write_data` (:4556) and 7 test files |
| `_dash_smcl_escape`, `_dash_emit_note`, `_dash_note_scope` | new | — |
| `help_examples.judge` / `FLAGGED` | one regex changed, one added | UNKNOWN; grep: `judge` is used by `test_help_examples.cscript` and `test_help_examples.py` |
| `release_verdict.diagnostics` / `DIAGNOSTICS` | one needle added | LOW (3) |
| Stata/Mata: `_dash_process_segment`, `_dash_tmp_open`, `_dash_tmp_preview`, `_dash_tmp_close`, `_dash_report_ignored`, `_dash_render_immediate`, `_dash_prepare_spec`, `_dash_require_mata`, `_dash_fn_spec_tail`; new `_dash_note` | sites as E3 | UNKNOWN (not indexed). grep (03oct2026): `_dash_process_segment` at 5210; `_dash_tmp_open` at 6702, 8170, 8384; `_dash_tmp_preview` at 6799; `_dash_tmp_close` at 6748, 6755, 6808, 8226, 8481, 8485; `_dash_report_ignored` at 5571; `_dash_render_immediate` at 5682; `_dash_prepare_spec` at 8192, 8352; `_dash_fn_spec_tail` at 6782, 8062. Record as unresolved, never as low. |
| Not edited (CRITICAL): `_dash_warn_once` (120), `_dash_style_note` (69), `_dash_reset_notes` (15), `_dash_display` (134) | — | — |

## User stories

- **US-06.1** As a twoway user, I want dash's notes to look and behave like twoway's notes: one `(note: …)` line in text colour, shown under `quietly`, hidden by `capture`. Then my do-files and logs can treat `dash` as they treat `twoway`.
- **US-06.2** As a dashboard publisher, I want a warnings filter set in my session's Python, or by `PYTHONWARNINGS`, to neither hide dash's notes nor make dash fail with r(7102). Then a filter set for another package cannot silence or break my builds.
- **US-06.3** As a dashboard publisher, I want each note once and without dash's internal paths or source lines. Then my log stays readable and does not reveal where dash is installed.
- **US-06.4** As a twoway user, I want a value I typed to appear in a note exactly as I typed it, never drawn as SMCL. Then a brace in an option can never become a clickable command.
- **US-06.5** As a dashboard publisher, I want the help's examples and the release gate to keep catching any note an example does not show. Then a note cannot slip into a published example unnoticed.

## Business requirements

- **BR-06.1** Every note dash prints in Stata's session is one line `(note:  dash: …)` in text colour. This covers the renderer in a saved build, `dash build, server` and `dash serve`'s build phase, and dash.ado and dash_parse.mata. The line shows under `quietly` and `set output error`, and `capture` hides it.
- **BR-06.2** dash's copies of twoway's own estimator note (`(note:  regress|fracpoly could not fit model)`) and scheme-lookup note (`(note: scheme X not found, using s2color)`) print as plain text in twoway's words, which `quietly` hides, as in twoway.
- **BR-06.3** A session warnings filter neither hides a dash note nor changes dash's return code. This holds for "ignore" and "error", for any category, set in Python or through `PYTHONWARNINGS`. Every other warning still follows the session's filters, and after the command the session's filters and `showwarning` are the objects they were before.
- **BR-06.4** A note raised more than once in one command prints once.
- **BR-06.5** No note line shows `UserWarning`, a path to a file of dash, or a Python source line.
- **BR-06.6** User text in a note is shown as typed: SMCL braces are escaped, control characters (C0, DEL, C1) show as `?`, NUL is dropped, and a note holds at most 4,000 characters of text.
- **BR-06.7** The help's example check and the release gate flag any `(note:` line that an example's help text does not show.
- **BR-06.8** The help states how dash prints a note, and every example output line, quoted note and claim about `quietly` in the paragraphs this section owns matches what dash prints.

## Technical requirements

- **TR-06.1 `_dash_smcl_escape(text, braces=True)`** (new; dash_render.py, directly above the comment `#: The notes already raised this render` at :15342). Place `_dash_emit_note` and `_dash_note_scope` beside it in that order.
  - Steps: `s = str(text)`; drop every `"\x00"`; replace each character whose code point is 1-31, 127 or 128-159 with `"?"`. With `braces` true, replace `{` by a NUL placeholder, then `}` by `{c )-}`, then the placeholder by `{c -(}`, as the Mata twin does (E6).
  - It is the Python twin of `_dash_smcl_text`. For UTF-8 text the two give equal strings (NC-06).
  - It reads no module-level name, so S23 can copy it by name.
- **TR-06.2 `_dash_emit_note(text, sfi=None)`** (new). It prints one note and returns the line it printed, with no SMCL. It never raises.
  1. `t = str(text)`. A leading `"dash: note: "` becomes `"dash: "`, because the R-8 notes already say "note".
  2. If `len(t) > 4000`, `t = t[:3997] + "..."`.
  3. **Text class.** If `re.match(r"dash: .*: \(note:  (?:regress|fracpoly) could not fit model\)$|dash scheme: \(note: scheme \S+ not found, using s2color\)", t)`, the line is `t` itself. Otherwise the line is `"(note:  " + t + ")"`, with two blanks, as twoway prints its graph notes (probe p1).
  4. **Sink.** Take `mod = sfi`, or `import sfi` (`None` on ImportError). Then `fn = getattr(getattr(mod, "SFIToolkit", None), "displayln" if text class else "errprintln", None)`.
     - If `fn` exists and `threading.current_thread() is threading.main_thread()`, call `fn("{txt}" + _dash_smcl_escape(line))`.
     - Otherwise, or if that call raises any `Exception`, run `print(_dash_smcl_escape(line, braces=False), file=sys.stderr, flush=True)`, ignoring `OSError` and `ValueError`.
  - It imports `re`, `sys` and `threading` locally, and reads no module-level name other than `_dash_smcl_escape`. This is required because S23 copies it into the generated app (`TestTheServedAppDefinesEveryNameItReads`).
  - The `getattr` chain is the `_dash_stata_poller` pattern (dash_render.py:37115-37132). Tests install `sfi` stubs without `errprintln` (`test_serve_lifecycle.py:763-909`).
- **TR-06.3 `_dash_note_scope(sfi=None)`** (new; `@contextlib.contextmanager`; add `import contextlib` after `import collections`, dash_render.py:64).
  - Inside `with warnings.catch_warnings():`:
    1. save `orig = warnings.showwarning`;
    2. define `_show(message, category, filename, lineno, file=None, line=None)`. When `issubclass(category, UserWarning)` and `re.match(r"dash(?:_render| scheme| kpi| build| serve)?: ", str(message))`, it prints the text once through `_dash_emit_note(str(message), sfi=sfi)`, tracked in a `said` set, and returns. Any other warning goes to `orig(message, category, filename, lineno, file, line)` unchanged;
    3. assign `warnings.showwarning = _show`;
    4. call `warnings.filterwarnings("always", message=<the same pattern>, category=UserWarning)`, which inserts the filter first;
    5. `yield said`.
  - `catch_warnings` restores the session's `filters` list object and `showwarning` on every exit, KeyboardInterrupt included.
  - The `"always"` filter disables Python's per-location registry, so the text de-duplication replaces it.
  - Use nothing newer than Python 3.10: no `catch_warnings(action=…)` (3.11+) and no `warnings._showwarnmsg_impl`. S05 may lower the floor.
- **TR-06.4 The entry point** (dash_render.py:37627-37630). Replace the `try:` body with `with _dash_note_scope() as _dash_said:` around the unchanged `_written = main(…)` call. The `except KeyboardInterrupt:` branch is unchanged.
  - The scope ends before `_dash_launch_app`, which is S23's. `_dash_said` keeps the set for S23's `said=`.
  - `main()` itself is not wrapped, so the tests that call `main()` or `render()` still see warnings (`TestTheRendererEntryPoint::test_main_called_directly_still_warns`).
- **TR-06.5 `main()`'s unprivate-app note** (dash_render.py:36905-36907). `print(_DASH_NOTE_FILE % (…), flush=True)` becomes `_dash_emit_note(_DASH_NOTE_FILE % (…))`. The text and the condition are unchanged.
- **TR-06.6 The data writer's UTF-8 note** (dash_render.py:1663-1666). `tk.displayln(f"{{txt}}dash: {what} …")` becomes `_dash_emit_note(f"dash: {what} …", sfi=sfi)`, with the same words. `sfi` is the function's parameter or the module it imported (:1650-1651).
- **TR-06.7 Mata `_dash_note(before, value, after)`** (new; dash_parse.mata, directly after `_dash_say`, :676-680):
  ```
  void _dash_note(string scalar before, string scalar value,
                  string scalar after) {
      string scalar t
      t = before + value + after
      if (substr(t, 1, 12) == "dash: note: ") t = "dash: " + substr(t, 13, .)
      if (ustrlen(t) > 4000) t = usubstr(t, 1, 3997) + "..."
      errprintf("{txt}(note:  %s)\n", _dash_smcl_text(t))
  }
  ```
  - The format string is a constant, so the user's text is only ever an argument.
  - It has no text class, because the ado's copies of twoway's words stay `display as text` (E3, last row).
  - Add a header entry after `_dash_say`'s (dash_parse.mata:50-53), in that entry's form: `*!   _dash_note(before, value, after)`, then `*!       Print before + value + after as one note, (note:  ...), in text`, `*!       colour on Stata's error channel, as twoway prints its notes.` and `*!`.
  - Add `_dash_note` to `_dash_require_mata`'s `_needed` (dash.ado:247) after `_dash_say`. `test_file_headers.py::TestTheMataLibraryHeader::test_its_public_api_is_the_list_dash_ado_needs` requires both.
  - `_dash_say` itself does not change (68 call sites).
- **TR-06.8 The eleven note sites** (E3 rows 1-11). Each `_dash_say("txt", B, V, A)` becomes `_dash_note(B, V, A)` with the same arguments.
  - Row 3 becomes `mata: _dash_note("dash: pci draws no labels, as twoway pci draws none; a scatteri layer can label a point.", "", "")`.
  - Row 9 becomes one statement, `mata: _dash_note("dash serve: ignoring option(s) that only apply to dash build:", st_local("_srv_na"), ". dash serve streams the dashboard and writes no file.")`, and its two `display` lines go. `_srv_na` is read by value, never expanded in a `display`.
  - Rows 10-11 change `_dash_say("txt", …)` to `_dash_note(…)` inside `_dash_fn_spec_tail`.
  - Every program keeps the `version` line S03 gave it. No other line of these programs changes.
- **TR-06.9 Unchanged.** These stay as they are:
  - the status lines (6830, 8229, 8236, 8243);
  - the ado's verbatim twoway notes (4206, 4232, 5522, 5533) and the "insufficient observations" text lines;
  - `_dash_say`;
  - every `warnings.warn` message;
  - the launcher's prints (E4);
  - the generated app.
- **TR-06.10 The log gates.**
  - `test/help_examples.py` `FLAGGED`: the first pattern becomes `re.compile(r"^(?:\(note:\s+)?dash: ignoring unsupported option\(s\):")`, with the same label. Append `(re.compile(r"\(note:\s"), "prints a note")` as the last entry, so the specific labels still win.
  - `scripts/release_verdict.py` `DIAGNOSTICS`: add `"(note:",` after `"drew nothing",`, with a comment naming WP-30 P1.26a.
  - `judge`, `diagnostics` and `allowed_in` do not change.
- **TR-06.11 The needles.**
  - In `test/test_custom_scheme.cscript`, add a helper `_cs_notes id logfile want` beside `_cs_log` (`version 19`). It runs `_cs_log "`id'" "`logfile'" "(note:" `want'` and `_cs_log "`id'" "`logfile'" "Warning:" 0`. Each `_cs_log … "UserWarning" N` line becomes `_cs_notes … N`. CS-12 counts `(note:` and `Warning:` through `_cs_count`, each 0. The five header lines (36, 39, 48, 57, 68) say "no note" / "one note".
  - `test/test_render_log_clean.cscript` checks 4 and 5 count `(note:` (0, then the control's 1) and `Warning:` (0, 0) with `_rlc_count`. Its header (:28-45) explains why.
  - `test/test_render_locate.cscript` LOC-16 loops over `"was not found" "could be resolved" "(note:" "Warning:"`.
  - The `test/test_json_escaping.cscript` comment (:454-461) says the line was Python's UserWarning before WP-30 and is a `(note: …)` line now.
  - Every later note test counts these needles (A150).
- **TR-06.12 The help** (R3: S06 owns dash.sthlp item 5 of "Differences from twoway", :584-622, and the two lines below):
  - :599 becomes `{p 12 12 2}{cmd:(note: dash: ignoring unsupported option(s): play() text())}{p_end}`.
  - :620-621 becomes "is named in a note, as {cmd:by()}'s are: {cmd:(note: dash: legend() sub-option(s) not implemented and ignored: span stack)}."
  - Insert one new paragraph after :600, before the `{phang2}` at :601: the text of the Stata-truth "Help paragraph" below.
  - :3612 becomes `{p 12 12 2}{cmd:(note: dash: ignoring unsupported option(s): pstyle() t1title())}{p_end}`.
  - :1838-1845 ("When a location is not private"): "prints one note per command, beginning {cmd:dash: note:}," becomes "prints one note per command, {cmd:(note: dash:} …{cmd:)},". "Under {cmd:quietly} the note is not shown, like dash's other notes." becomes "Like {cmd:dash}'s other notes, it is shown under {cmd:quietly} and hidden by {cmd:capture}."
  - SMCL paragraph mode collapses the two blanks, and `help_examples.shown_at` compares through `_norm`, so the help writes one blank.
  - The help lines 1584 and 1622 ("a line beginning {cmd:dash: note:}") describe the launcher's link-file note, which S06 does not change. They stay, and S23 owns them.
- **TR-06.13 Maps (X.5, A148).**
  - `test/function_test_map.py`: under S06's anchor, alphabetically:
    - `'_dash_emit_note': 'test/test_note_channel.py::TestTheNoteLine::test_a_note_is_one_errprintln_in_text_colour'`;
    - `'_dash_note_scope': 'test/test_note_channel.py::TestTheNoteScope::test_an_ignore_filter_hides_no_note'`;
    - `'_dash_note_scope.<locals>._show': 'test/test_note_channel.py::TestTheNoteScope::test_other_warnings_keep_the_sessions_filters'`;
    - `'_dash_smcl_escape': 'test/test_note_channel.py::TestTheSmclEscape::test_braces_become_smcl_codes'`.
  - `test/program_coverage_map.py` `COVERAGE["dash_parse.mata"]`, under S06's anchor: `"_dash_note": ("test_render_log_clean.cscript:NC-06", "test_render_log_clean.cscript:NC-05"),`.
  - No ado program is added.
- **TR-06.14 Both modes; no served copy and no JavaScript.**
  - The saved build and the served build both run `main()` inside the scope. The served build's notes are the planners' (`_plan_graph_notes`, `_plan_by_groups`) and the scheme notes, raised in Stata's process.
  - A saved page's filter move runs JavaScript and raises no Python note. A served session's notes stay in the child until S23.
  - Index R2 row S06: no constant or function is added to either `_glyph_layer_lines` tuple or to `_shared_stat_lines`. S23 adds `_dash_smcl_escape` and `_dash_emit_note` after `"_dash_note_empty_layer",` (dash_render.py:33137) in batch 8.
  - No JS twin exists or is needed. No page changes, so `test_varlist_expansion.py`'s `_SINGLE_Y_BASELINE_SHA256` (R10) and `test_mode_parity.py` stay as they are. G3 is run to show it.
- **TR-06.15 Security (rule 1, G9).**
  - The threat: a note echoes user text (option values, labels, graph names), and `errprintln`, `displayln` and `errprintf` read SMCL. An unescaped `{stata …}`, `{browse …}` or `{view …}` would draw a link that runs a command when clicked. ESC and CSI bytes could drive the terminal of console Stata.
  - The defences:
    - every Stata-bound line passes `_dash_smcl_escape` or `_dash_smcl_text`;
    - control characters become `?`;
    - a note is bounded at 4,000 characters of text;
    - no internal path or source line is printed;
    - the Mata format string is constant;
    - no `shell=True`, `exec` or `eval` is introduced;
    - nothing is written to the page.
  - The commit body names the threat.

## Boundaries

- **Not edited:**
  - `_dash_warn_once`, `_dash_style_note`, `_dash_reset_notes` and `_dash_display` (CRITICAL), and any `warnings.warn` message text;
  - `_dash_say`;
  - `_dash_note_empty_layer`, `_dash_layer_drew_anything` and `_make_figure_body` (S23's M6 argument, then S26);
  - `ServerAppBuilder.build`, `_generate_app_source`, `_plan_graph_notes` and `_plan_by_groups` (S23's trial and app hook; S04's `doc.template` line);
  - `_dash_launch_app`, its relay and the launcher's prints (S23; S12's `--show`);
  - `test_mode_parity.py`'s `_served`, `CORPUS`, `_MUST_WARN` and `ALLOWED` (S23 restores the own-if entries).
- **Batch partners.**
  - S04: `_assemble_layout`, `_render_bootstrap_html`, `_dash_served_template`, `_dash_csp_meta`, `_dash_open_page` (its Windows line is printed as its other lines are and is not a note site), the `saving()` character-rule paragraph, the CSP help, and `saving_chars_truth.json`.
  - S05: `_dash_pymin`, `_dash_require_python`, `dash_setup.ado`, `dash_setup_lib.py`, `test/conftest.py`, the floor script and the requirements files.
  - S06 edits none of these.
- **Later sections.**
  - S22 (the stale-graph note), S26 (the function note), S29 (the inline-markup note), S34 (the ado-path lookup) and S41 (the bokeh-window note) add notes through this channel. S33 adds none: by ratification row 4 (06oct2026) there is no unread-scheme-key note, and S33's tests pin that nothing is printed.
  - S41's run-time check must raise its note inside `main()` or call `_dash_emit_note` directly. A warning raised at import time is outside the scope.
  - The guard order at the top of `dash` (A154) is not touched.
  - The export-block paragraphs of `_dash_render_immediate` (S12, S22, S34, S42) change only in row 8's one line.
- **Exclusions.** There is no separate debug log (research §2, I-sum: scope creep), and the GUI's colours are not measured (the console is the only binary run; the SMCL class is the evidence). Windows' child-pipe encoding is deferred with P1.34 (M4).

## Stata truth

No fixture. The truth is which output channel a line takes, not a value, so the S06 block of `test/test_wp30_truth.cscript` runs twoway live beside dash (NC-01, NC-02), with no `_meta` stamp. The probes below were run 03oct2026 through `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s06-probe <file>.do` (StataNow 19.5 MP, console). Each opened with `adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"`, `global dash_nobrowser 1`, `set graphics off` and `sysuse auto, clear`, and logged text and SMCL.

**p1 (default linesize):**

```
. twoway scatter mpg weight, mcolor(notacolor) nodraw
(note:  named style notacolor not found in class color, default attributes
    used)                                           <- printed twice; {p 0 4 2}-wrapped, no "> "
. quietly twoway scatter mpg weight, mcolor(notacolor) nodraw
(note:  named style notacolor …)                    <- shown, twice
. capture twoway scatter mpg weight, mcolor(notacolor) nodraw
                                                    <- nothing
. quietly mata: errprintf("{txt}(note: probe D %s)\n", "x")       -> (note: probe D x)
. capture mata: errprintf("{txt}(note: probe E %s)\n", "x")       -> nothing
. set output error / mata: errprintf("{txt}(note: probe F %s)\n") -> (note: probe F x)
. quietly python: …SFIToolkit.errprintln("{txt}(note: probe G)")  -> (note: probe G)
. quietly mata: printf("{txt}(note: probe I)\n")                  -> nothing
. mata: errprintf("{txt}%s\n", "(note: " + 30*"abcdefghij " + ")")  -> wrapped with "> " at the linesize
. mata: errprintf("{txt}%s\n", "(note: {c -(}stata display 1:x{c )-})") -> (note: {stata display 1:x})
```

**p3 and p4 (linesize 255): twoway's two classes.**

```
. capture noisily twoway lfit mpg weight in 1, nodraw     -> (note:  regress could not fit model) / insufficient observations
. quietly twoway (scatter mpg weight) (lfit mpg weight if price > 20000), nodraw   -> nothing
. twoway (scatter mpg weight) (lfit mpg weight if price > 20000), nodraw           -> (note:  regress could not fit model)
. set output error / twoway … mcolor(notacolor)  -> both named-style notes shown
               / twoway (scatter)(lfit if price > 20000) -> the regress note NOT shown
. capture noisily twoway fpfit mpg weight if price > 20000, nodraw -> (note:  fracpoly could not fit model) / observation numbers out of range
. twoway scatter mpg weight, scheme(nosuchscheme) nodraw          -> (note: scheme nosuchscheme not found, using s2color)
. quietly twoway scatter mpg weight, scheme(nosuchscheme) nodraw  -> nothing
. quietly twoway scatter mpg weight, msymbol(weird) nodraw        -> (note:  named style weird not found in class symbol, default attributes used)
. quietly twoway (scatter mpg weight) (qfit mpg weight in 1), nodraw -> nothing;  plain -> (note:  regress could not fit model)
SMCL: {txt}(note:  regress could not fit model)   {txt}(note:  named style …
```

**p2: status lines.** `twoway scatter mpg weight, saving(p2a.gph, replace) nodraw` prints `file p2a.gph saved`. Under `quietly` it prints nothing, which is why dash's `dashboard saved to` keeps `_dash_say`.

**p5: the planned Mata helper**, defined in scratch after `run dash_parse.mata` and called from a program:

```
. s06p play() {stata display 999:x}  -> (note:  dash: ignoring unsupported option(s):play() {stata display 999:x})
. quietly s06p play()                -> (note:  dash: ignoring unsupported option(s):play())
. capture s06p play()                -> nothing
. mata: _s06_note("", "dash: note: /tmp/x could not be made private.", "") -> (note:  dash: /tmp/x could not be made private.)
SMCL: {res}{err}{txt}(note:  dash: ignoring unsupported option(s):play() {c -(}stata display 999:x{c )-})
```

**The channel table** (research m5/m6, confirmed by p1-p5):

| Channel | plain | quietly | capture | set output error | SMCL class |
|---|---|---|---|---|---|
| twoway's named-style note | shown | shown | hidden | shown | `{txt}`, error stream |
| twoway's estimator / scheme-lookup note | shown | hidden | hidden | hidden | `{txt}` |
| Python stderr (today's notes) | shown | shown | hidden | shown | `{err}` |
| `errprintln("{txt}…")`, `errprintf("{txt}…")` (the new note class) | shown | shown | hidden | shown | `{err}{txt}` |
| `displayln("{txt}…")`, `printf` (`_dash_say`; the new text class) | shown | hidden | hidden | hidden | `{txt}` |

**Help paragraph** (TR-06.12; exact SMCL to insert after dash.sthlp:600):

```
{phang2}
    {ul:How a note is printed.}  Every note {cmd:dash} prints -- this one,
    and those about a value it draws differently or a layer that drew
    nothing -- is printed as {cmd:twoway} prints its notes: one line,
    {cmd:(note: dash:} ...{cmd:)}, in text colour, shown under
    {cmd:quietly} and {cmd:set output error} and hidden by {cmd:capture}.
    A note is printed once per command however often it arises, never
    names a file or a line of {cmd:dash}'s own code, and is neither hidden
    nor made an error by a Python {cmd:warnings} filter or by
    {cmd:PYTHONWARNINGS}; other packages' Python warnings still follow
    those filters.  The two notes {cmd:dash} gives in {cmd:twoway}'s own
    words, {cmd:(note: regress could not fit model)} (or {cmd:fracpoly}'s)
    and {cmd:(note: scheme} {it:name} {cmd:not found, using s2color)},
    are printed as {cmd:twoway} prints them, as plain text that
    {cmd:quietly} hides.

```

## TDD test stubs

### Regression tests (06-01, 06-02; each fails at the batch-2 base)

`test/test_note_channel.py` (new). It imports `dash_render as dr` as `test/test_private_files.py` does. `_RENDER` is `<repo>/dash_render.py`.

`_Rec` is a stand-in `sfi` whose `SFIToolkit` records `("err", s)` from `errprintln` and `("txt", s)` from `displayln` in `self.calls`. `_spec(tmp_path)` writes `make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {"mcolor": "notacolor"}}])`, with `graph_options["by"] = "foreign, graphregion(color(red))"`, and `make_data_json` of four rows (mpg, weight, foreign).

`_run(tmp_path, mode, flt, monkeypatch, capsys)` monkeypatches `sys.argv` to `--spec --data --output o.html|o.py --mode standalone|server`. Inside `warnings.catch_warnings()` it applies `simplefilter(flt)` unless `flt is None`, snapshots `warnings.filters` (object and copy) and `warnings.showwarning`, and runs `runpy.run_path(_RENDER, run_name="__main__")`. It returns `(output_exists, stderr, restored)`. `_notes(err)` is the list of lines starting `(note:  dash: `.

- Test: `test/test_note_channel.py::TestTheSmclEscape::test_braces_become_smcl_codes` — `"{stata display 1:x}"` gives `"{c -(}stata display 1:x{c )-}"`, and `"a}b{c"` gives `"a{c )-}b{c -(}c"`. Fails at base: `AttributeError: module 'dash_render' has no attribute '_dash_smcl_escape'`.
- Test: `…::TestTheSmclEscape::test_control_characters_become_question_marks` — `"a\x01\x1b[2J\x7f\x85b\x00c"` gives `"a??[2J??bc"`.
- Test: `…::TestTheSmclEscape::test_other_text_is_unchanged` — `"café % $x \x60q' \"r\" é"` is unchanged. With `braces=False`, braces stay and controls are still `?`.
- Test: `…::TestTheNoteLine::test_a_note_is_one_errprintln_in_text_colour` — with `_Rec`, `_dash_emit_note("dash: x is odd.", sfi=rec)` gives `rec.calls == [("err", "{txt}(note:  dash: x is odd.)")]` and returns `"(note:  dash: x is odd.)"`.
- Test: `…::TestTheNoteLine::test_the_line_is_smcl_escaped` — `"dash: msymbol({stata display 1:x}) is …"` arrives as `{c -(}stata display 1:x{c )-}` inside the one `errprintln` call.
- Test: `…::TestTheNoteLine::test_a_note_note_prefix_is_said_once` — `"dash: note: /t/x could not be made private."` gives the line `"(note:  dash: /t/x could not be made private.)"`.
- Test: `…::TestTheNoteLine::test_twoways_own_text_notes_print_as_text` — `"dash: graph 'g1' plot 2 (lfit): (note:  regress could not fit model)"` and `"dash scheme: (note: scheme zz not found, using s2color) -- '#include zz' in 'a.scheme'."` each go to one `("txt", "{txt}" + text)` call, unwrapped. `"dash: mcolor((note:  regress could not fit model)) is not a recognised colour; using the scheme's default."` goes to `errprintln`, wrapped.
- Test: `…::TestTheNoteLine::test_a_long_note_is_cut_at_4000` — 10,000 `x` characters give a line of exactly `len("(note:  ") + 4000 + 1` characters, ending `...)`.
- Test: `…::TestTheNoteLine::test_outside_stata_one_plain_line_on_stderr` — with `monkeypatch.setitem(sys.modules, "sfi", None)`, `_dash_emit_note("dash: {a}")` writes exactly `"(note:  dash: {a})\n"` to stderr and nothing to stdout.
- Test: `…::TestTheNoteLine::test_off_the_main_thread_it_goes_to_stderr` — called in a `threading.Thread` with `_Rec`, `rec.calls == []` and stderr holds the line.
- Test: `…::TestTheNoteLine::test_it_never_raises` — a stand-in whose `errprintln` raises `RuntimeError` falls back to stderr. A stand-in with no `SFIToolkit` falls back to stderr.
- Test: `…::TestTheNoteScope::test_an_ignore_filter_hides_no_note` — under `simplefilter("ignore")`, `warnings.warn("dash: a.")` inside `_dash_note_scope(sfi=rec)` gives one `errprintln`.
- Test: `…::TestTheNoteScope::test_an_error_filter_raises_no_note` — under `simplefilter("error")`, no exception and one `errprintln`. `"dash kpi: k."` and `"dash scheme: s."` are notes too.
- Test: `…::TestTheNoteScope::test_a_note_raised_twice_prints_once` — the same text raised twice gives one call. The yielded set equals `{"dash: a."}`.
- Test: `…::TestTheNoteScope::test_other_warnings_keep_the_sessions_filters` — `FutureWarning("x")` and `UserWarning("not dash")`:
  - under "ignore": no call and nothing recorded;
  - under "error": the `FutureWarning` raises;
  - under `catch_warnings(record=True)` outside the scope: the non-dash warning is recorded by the outer recorder.
- Test: `…::TestTheNoteScope::test_the_filters_and_showwarning_are_restored` — after a normal exit and after an exception raised inside, `warnings.filters is before`, `list(before) == copy` and `warnings.showwarning is show`.
- Test: `…::TestTheRendererEntryPoint::test_an_ignore_filter_hides_no_note` — parametrized `mode` in (standalone, server). It first asserts that the control run (`flt=None`) printed at least one `(note:  dash: ` line, then that the `_notes` under `"ignore"` equal the control's. In server mode one note contains `graphregion(color(red))`. Fails at base on the first assertion: `AssertionError: no (note:  dash: line; stderr: '…UserWarning: dash: by() sub-option(s) …'`, where an equality alone would pass as `[] == []`.
- Test: `…::TestTheRendererEntryPoint::test_an_error_filter_raises_no_note` — parametrized `mode`. Under `"error"` no exception, the output file exists, and the `_notes` equal the control's. Fails at base: `UserWarning: dash: by() sub-option(s) not implemented and ignored: graphregion(color(red))`.
- Test: `…::TestTheRendererEntryPoint::test_no_path_or_source_line_is_printed` — parametrized `mode`, default filters. Stderr holds none of `"UserWarning"`, `"dash_render.py:"` or `"parse_color_alpha("`. Fails at base on `"UserWarning"`.
- Test: `…::TestTheRendererEntryPoint::test_the_sessions_filters_survive` — `restored` is True under each of None, "ignore" and "error".
- Test: `…::TestTheRendererEntryPoint::test_pythonwarnings_in_the_environment` — `subprocess.run([sys.executable, "-c", <runpy of _RENDER with the standalone argv>], env=dict(os.environ, PYTHONWARNINGS="error::UserWarning"), capture_output=True, text=True, timeout=180)` gives returncode 0, at least one `(note:  dash: ` line on stderr and no `Traceback`. Fails at base: `rc=1`, a 36-line traceback.
- Test (guard; passes at base): `…::TestTheRendererEntryPoint::test_main_called_directly_still_warns` — `pytest.warns(UserWarning, match="graphregion")` around `dr.main(sp, dp, out)`.
- Test: `test/test_help_examples.py::TestTheJudge::test_a_note_line_is_flagged` — parametrized over these three lines, each giving one problem from `hx.judge(line + "\n", 0, 0, [])`:
  - `"(note:  dash: graph 'g' plot 2 (lpoly) drew nothing from 74 observations.)"`;
  - `"(note:  dash: mcolor(x) is not a recognised colour; using the scheme's default.)"`;
  - `"dash: graph 'g' plot 2 (lfit): (note:  regress could not fit model)"`.

  Fails at base: `assert 0 == 1`.
- Test: `test/test_help_examples.py::TestTheJudge::test_an_ignored_option_note_keeps_its_reason` — `hx.judge("(note:  dash: ignoring unsupported option(s): [aweight])\n", 0, 0, [])` gives one problem containing `"names an option as ignored"`. Fails at base.
- Test: `test/test_release_verdict.py::TestEachFailureFails::test_an_example_that_prints_a_note` — parametrized over `"dash: graph 'g' plot 2 (lfit): (note:  regress could not fit model)"` and `"(note:  dash: aspectratio(2) is drawn as the plot's shape.)"`. As `test_an_example_that_prints_a_diagnostic` (:136-148) does, `not ok`, and a line holds `"printed: " + printed`. Both fail at base, since neither holds an old needle.

### Certification cases (06-01 writes them; NC prefix checked unused at `c96facd`: `grep -rln 'NC-0[0-9]' test/` prints nothing)

`test/test_wp30_truth.cscript`, S06's block, between its stub's start and end lines. Each check is a `_w30_expect NC-0k "<cond>" "<msg>"` line and each case closes with one `_w30_done NC-0k "<msg>"` (TR-01.10.4), which prints `NC-0k PASS: …` or `NC-0k FAIL: …` and counts the case; the block keeps no tally of its own and never `assert`s or `exit`s, so `WP30_ONLY=S06` ends `ALL CHECKS PASSED` and a failure does not stop the later blocks. Logs go to `` `w30_work'/wp30_s06_<k>.log `` through `log using …, text replace name(s06nc)`, pages to `` `w30_work'/wp30_s06.html ``, and both are erased before S06's end line. Logs are counted with `cert_log_has …, needle(…)`, `r(count)`, copied into a local before the next `_w30_expect` (`cert_log_has` clobbers `r()`).

- **NC-01** (twoway truth, named-style class):
  - `quietly twoway scatter mpg weight, mcolor(notacolor) nodraw` logs at least one `(note:` line;
  - `capture twoway …` logs none;
  - `quietly dash scatter mpg weight, mcolor(notacolor) saving("`w30_work'/wp30_s06.html", replace)` logs at least one `(note:  dash: ` line;
  - `capture dash …` logs no `(note:` line and no `Warning:` line.

  Fails at base: `quietly dash` logs 0 `(note:  dash: ` lines.
- **NC-02** (twoway truth, estimator class):
  - `twoway (scatter mpg weight) (lfit mpg weight if price > 20000), nodraw` logs one `could not fit model` line, and `quietly twoway …` logs none;
  - `dash (scatter mpg weight) (lfit mpg weight if price > 20000), saving(…, replace)` logs one, and `quietly dash …` logs none.

  Fails at base: `quietly dash` logs 1, the red UserWarning.

`test/test_render_log_clean.cscript`: one contiguous run after check [5/5] (R1). A local `nc_fail` counts FAILs, and `assert `nc_fail' == 0` follows NC-06. Each Python statement reads Stata values through `sfi.Macro.getLocal`, never a macro inside a Python string literal (test_cscript_hygiene).

- **NC-03**: `dash scatter mpg weight, mcolor(notacolor) saving(…) replace` is logged twice: once with the session's filters, then after `python: _nc_cm = _nc_w.catch_warnings()`, `python: _nc_cm.__enter__()` and `python: _nc_w.filterwarnings("ignore")`, under `capture noisily`, followed by `python: _nc_cm.__exit__(None, None, None)`. Both runs give rc 0, the default run has at least one `(note:  dash: ` line, and the ignore run has the same count. Fails at base: default 0 and ignore 0, so "at least one" fails.
- **NC-04**: the same with `python: _nc_w.simplefilter("error")`. rc 0, and the count equals the default run's. Fails at base: rc 7102.
- **NC-05**: `dash scatter mpg weight, mcolor(notacolor) play(x) saving(…) replace` logs no logical line holding `UserWarning` or `dash_render.py:`, and at least two `(note:  dash: ` lines (the renderer's and the ado's). Fails at base: 1 `UserWarning`, 1 path, 0 notes.
- **NC-06**:
  - (a) `quietly dash scatter mpg weight, mcolor(notacolor) play(x) saving(…) replace` logs at least two `(note:  dash: ` lines, one of them holding `ignoring unsupported option(s): play()`;
  - (b) `capture dash …` logs no `(note:`, `Warning:` or `ignoring` line;
  - (c) under an SMCL log, `dash scatter mpg weight, msymbol({stata display 999:x}) saving(…) replace` leaves no `{stata display 999` in the SMCL file, while the text log of the same run holds `{stata display 999:x}` on at least two logical lines (the command and the note);
  - (d) after `_dash_xm_load`, `sys.modules["_dash_render_export"]._dash_smcl_escape` equals Mata `_dash_smcl_text` on `{bf:x} a}b{c`, `"x" + char(1) + char(127) + "y"`, `"a" + char(194) + char(133) + "b"` and `"caf" + uchar(233)`. When the function is missing it reports `MISSING`, with no `capture` and no probe.

  Fails at base on (a): the ado note is hidden, giving 0 lines, and on (d): `MISSING`. (c) is a guard: stderr is already logged literally (research critic, item 8).

### Flips (06-04 to 06-10; each with a `Flipped:` line)

These are the nodes and cases of Evidence E8, written as that table says.

### Mutation checks (run by hand in 06-11 against pytest; not committed)

- Removing the `filterwarnings("always", …)` line turns `TestTheNoteScope::test_an_ignore_filter_hides_no_note` red (and NC-03, when that script is run).
- Replacing `errprintln` with `displayln` in TR-06.2 turns `TestTheNoteLine::test_a_note_is_one_errprintln_in_text_colour` red (and NC-01's `quietly dash` check).
- Dropping `_dash_smcl_escape` from the sink turns `TestTheNoteLine::test_the_line_is_smcl_escaped` red (and NC-06 (c)).
- Removing the text class turns `TestTheNoteLine::test_twoways_own_text_notes_print_as_text` red (and NC-02).

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Escape, emitter, scope (units) | pytest `test/test_note_channel.py` (`TestTheSmclEscape`, `TestTheNoteLine`, `TestTheNoteScope`) | stand-in `sfi` | n/a (Stata-process output) |
| The entry point under filters, `PYTHONWARNINGS`, no path | pytest `TestTheRendererEntryPoint` | `make_spec` with `mcolor(notacolor)`, `by(foreign, graphregion(color(red)))` | yes: `--mode standalone` and `--mode server` |
| Visibility against twoway (named-style and estimator classes) | `test_wp30_truth.cscript` S06 block, NC-01, NC-02, driver with `WP30_ONLY=S06` | `sysuse auto`; twoway live | saved build (the served build's notes take the same scope; pytest covers server mode) |
| Filters, form, `quietly`/`capture`, SMCL, twin parity | `test_render_log_clean.cscript` NC-03..06, driver | `sysuse auto` | saved |
| The gates | pytest `test_help_examples.py::TestTheJudge`, `test_release_verdict.py::TestEachFailureFails` | made-up log lines | n/a |
| The 29 needles and the pins | the scripts of E8, and every script holding a note needle (06-12) | as each script | as each script |
| Registries | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_file_headers.py`, `test_no_orphans.py`, `test_cscript_hygiene.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_tracking_documents.py` | — | — |
| No drawing change (G3, R10) | `test_mode_parity.py`, `test_varlist_expansion.py` | — | yes, unchanged |
| The help | `test_help_examples.py`, `test_help_conformance.py`, `test_help_claims_1.py`-`_8.py`, `test_private_files.py`; `test_help_examples.cscript` and `test_help_claims_8.cscript` through the driver | dash.sthlp | — |

**Acceptance criteria.**
- **AC-06.1** (BR-06.1) NC-01: `quietly dash …` shows a `(note:  dash: ` line and `capture dash …` shows none. NC-06 (a)/(b) show the same for dash.ado's note. The help example lines read `(note: dash: …)`, and `test_help_examples.cscript` passes.
- **AC-06.2** (BR-06.2) NC-02: `quietly dash (scatter)(lfit if price > 20000)` shows no `could not fit model` line, and plain `dash` shows one, as twoway does. `test_twoways_own_text_notes_print_as_text` passes.
- **AC-06.3** (BR-06.3) NC-03, NC-04 and `TestTheRendererEntryPoint` (both modes) pass, `test_pythonwarnings_in_the_environment` gives rc 0, and `test_the_sessions_filters_survive` and `test_other_warnings_keep_the_sessions_filters` pass.
- **AC-06.4** (BR-06.4) `test_a_note_raised_twice_prints_once` passes, and CS-15 still logs each `#include` note exactly once.
- **AC-06.5** (BR-06.5) NC-05 and `test_no_path_or_source_line_is_printed` pass.
- **AC-06.6** (BR-06.6) `TestTheSmclEscape`, `test_the_line_is_smcl_escaped`, `test_a_long_note_is_cut_at_4000` and NC-06 (c)/(d) pass.
- **AC-06.7** (BR-06.7) The new judge and verdict tests pass, and every existing one is unchanged and green.
- **AC-06.8** (BR-06.8) `grep -c 'How a note is printed' dash.sthlp` prints 1. `grep -c '{cmd:dash: ignoring unsupported' dash.sthlp` prints 0. The tempfiles section holds `(note: dash:` and no "is not shown, like dash's other notes".
- **AC-06.9** The migrated needles bite. render_log_clean's control [5/5] counts exactly one `(note:` line and CS-10 exactly one. `grep -c UserWarning test/test_custom_scheme.cscript test/test_render_log_clean.cscript test/test_render_locate.cscript` prints 0 0 0.
- **AC-06.10** Tracking (G5): the entry is closed naming existing tests, the `"P1.26a"` key is gone, and `grep -c '<!-- WP-30 P1.26a -->' CHANGELOG.md` prints 0.

## Tasks

**Commit boundary.** Tasks 06-01 to 06-13 form the one commit of entry `P1.26a`. Its subject is `Print dash's notes as twoway prints its notes, through one channel (WP-30 P1.26a)`, and 06-13 makes it on `wp30-s06` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s06`, after one full run through the queue. The body is in this order:
1. `<scratch>/06-P1.26a-failure.txt`;
2. the measured defect (E2);
3. what changed and where, and the threat closed (TR-06.15);
4. one `Regression: test/<file>.py::<Class>::<test> -- failed at <batch-2 base sha> with <text>` line per regression test, and `Regression: test/<script>.cscript NC-0k -- failed at <sha> with <text>` for NC-01..05;
5. `Guard: …` lines for `test_main_called_directly_still_warns` and NC-06 (c);
6. one `Flipped: <node> -- <old expectation> was wrong because <why>` line per E8 row;
7. `BUGS.md: "<title>" (closed)`.

There is no `Fixture:` line. `$S` is the orchestrator's WP-30 scratch directory, `<scratch>` in the index (Deltas, "Base commit"), and S06's own runs use `S6=$S/s06` so that partners' driver logs never collide. Every command runs from `$WT`. Stata runs only through `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S6" <driver>.do`. The message contains no AI reference.

<task type="auto" id="06-01">
  <name>Write the failing channel tests</name>
  <files>test/test_note_channel.py, test/test_render_log_clean.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    First check `git -C "$WT" rev-parse HEAD` equals `cat $S/batch-2-base.txt` and `git -C "$WT" branch --show-current` prints `wp30-s06`; run `mkdir -p "$S6"`; read `$S/batch-2-impact.txt` and `$S/wp30-ratified.txt` row 13 (stop and report if row 13 is struck). Create `test/test_note_channel.py` with every test of "TDD test stubs / Regression tests" in classes TestTheSmclEscape, TestTheNoteLine, TestTheNoteScope and TestTheRendererEntryPoint, with the helpers `_Rec`, `_spec`, `_run`, `_notes` as described (spec data built with `make_spec` and `make_data_json` from test/conftest.py). In `test/test_render_log_clean.cscript` append NC-03..NC-06 as one contiguous run after check [5/5] and before `dash clear`, with a `nc_fail` tally and a final `assert `nc_fail' == 0`; leave checks 1-5 as they are. In `test/test_wp30_truth.cscript` write NC-01 and NC-02 between S06's stub start and end display lines only (R1), reported through `_w30_expect`/`_w30_done` with no tally, `assert` or `exit` of their own, writing only under `` `w30_work' `` and erasing their files before the end line. Do not touch any shipped file.
  ]]></action>
  <verify><![CDATA[
    `python3 -m pytest test/test_note_channel.py -q -n0 -p no:cacheprovider -rf > "$S6/06-01-py.log" 2>&1; tail -3 "$S6/06-01-py.log"` shows failures and no collection error, except `test_main_called_directly_still_warns`, which passes. For each of `test_render_log_clean.cscript` and `test_wp30_truth.cscript`, write the driver `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" <script> > "$S6/run_<name>.do"` and run `WP30_ONLY=S06 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S6" "$S6/run_<name>.do"`. `cat "$S6"/run_*.log | grep -oE "NC-0[1-6] FAIL" | sort -u | wc -l` prints 6: NC-01 to NC-05 each fail, and NC-06 fails on (a) and (d) (a case may print several FAIL lines, one per failed check). Then write `$S/06-P1.26a-failure.txt`: the base sha, each failing pytest node with its last assertion line, and each NC FAIL line, with every scratch path cut to its last component (the scratch path holds a word G7 forbids), so `grep -Eic 'claude|anthropic' "$S/06-P1.26a-failure.txt"` prints 0.
  ]]></verify>
  <done>Every regression test and certification case of the section existed and was shown failing on the unmodified tree, and the failure text was saved without a commit.</done>
</task>

<task type="auto" id="06-02">
  <name>Write the failing log-gate tests</name>
  <files>test/test_help_examples.py, test/test_release_verdict.py</files>
  <action><![CDATA[
    In `test/test_help_examples.py` class TestTheJudge (848) add `test_a_note_line_is_flagged` (parametrized over the three lines of its stub) and `test_an_ignored_option_note_keeps_its_reason`, after `test_a_warning_a_sub_option_note_or_a_traceback_is_flagged` (900). In `test/test_release_verdict.py` class TestEachFailureFails (87) add `test_an_example_that_prints_a_note`, parametrized over the two lines of its stub, in the form of `test_an_example_that_prints_a_diagnostic` (136-148). Change no existing test, `help_examples.py` or `release_verdict.py`.
  ]]></action>
  <verify><![CDATA[
    `python3 -m pytest test/test_help_examples.py test/test_release_verdict.py -q -n0 -p no:cacheprovider -rf -k "note_line_is_flagged or keeps_its_reason or prints_a_note"` reports 6 failed (3 + 1 + 2). The same files without `-k` report no other failure. Append the six failure lines to `$S/06-P1.26a-failure.txt`.
  ]]></verify>
  <done>The gates' blindness to the new note form was shown by six failing tests, recorded with the section's failure text.</done>
</task>

<task type="auto" id="06-03">
  <name>Add the escape, emitter and scope</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `import contextlib` after `import collections` (dash_render.py:64). Directly above the comment `#: The notes already raised this render` (15342) add `_dash_smcl_escape`, `_dash_emit_note` and `_dash_note_scope` exactly as TR-06.1, TR-06.2 and TR-06.3 specify, each with a docstring citing the measured channel table (Stata truth), the security reason (TR-06.15), and for `_dash_emit_note` that it is self-contained because S23 copies it into the served app. Do not edit `_dash_warn_once`, `_dash_style_note`, `_dash_reset_notes` or `_dash_display`. Add the four FUNCTIONS entries of TR-06.13 under the `# WP-30 S06 (P1.26a): One note channel` anchor of `test/function_test_map.py`, alphabetically.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_note_channel.py -q -n0 -p no:cacheprovider -k "SmclEscape or NoteLine or NoteScope"` reports 0 failed; `python3 -m pytest test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes; `python3 -c "import ast;ast.parse(open('dash_render.py').read())"` exits 0.]]></verify>
  <done>The renderer could print a note in twoway's channel, escaped and bounded, and could hold a session's filters off dash's notes while leaving every other warning alone.</done>
</task>

<task type="auto" id="06-04">
  <name>Route the renderer's notes through the scope</name>
  <files>dash_render.py, test/test_private_files.py, test/test_string_value_export.py</files>
  <action><![CDATA[
    State in the progress output that `main` is treated as HIGH (E9) before editing it. Apply TR-06.4: at dash_render.py:37627-37630 wrap the unchanged `main(...)` call in `with _dash_note_scope() as _dash_said:` inside the existing `try:`; leave the KeyboardInterrupt branch and the launch block as they are. Apply TR-06.5 (36905-36907) and TR-06.6 (1663-1666). Flip `test/test_private_files.py::TestTheNote::test_a_server_app_on_a_disk_without_permissions_is_written_and_noted` to read `capsys.readouterr().err`, count lines starting `(note:  dash: ` that hold the path and "every observation" (1), and assert neither stream holds such a line on the launch route. In `test/test_string_value_export.py` give FakeSfi's SFIToolkit (176) an `errprintln` that appends to `fake.shown`, and flip the three `startswith("{txt}dash: …")` assertions (368, 388, 397) to `startswith("{txt}(note:  dash: …")`. Write each flip's `Flipped:` line to `$S6/06-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_note_channel.py test/test_private_files.py test/test_string_value_export.py test/test_serve_launcher.py test/test_serve_lifecycle.py test/test_resource_limits.py test/test_help_claims_2.py test/test_help_claims_4.py test/test_adversarial_matrix.py test/test_serve_token.py -q -p no:cacheprovider` reports 0 failed; `grep -c Flipped "$S6/06-flips.txt"` prints 3.]]></verify>
  <done>Every note the renderer raises or prints in Stata's process went through the channel in both build modes, the session's filters were restored, and the two writer and server-app pins were flipped with reasons.</done>
</task>

<task type="auto" id="06-05">
  <name>Add the Mata note helper</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    In dash_parse.mata add `_dash_note` exactly as TR-06.7 gives it, directly after `_dash_say` (676-680), with a comment block in the style of the `_dash_smcl_text`/`_dash_say` block (640-663) citing twoway's measured channel; add its header entry after `_dash_say`'s (50-53) in the same spacing. In dash.ado's `_dash_require_mata` add `_dash_note` after `_dash_say` on the `_needed` line that holds `_dash_immediate _dash_say` (247 at `c96facd`). Add `"_dash_note": ("test_render_log_clean.cscript:NC-06", "test_render_log_clean.cscript:NC-05"),` under S06's anchor in `COVERAGE["dash_parse.mata"]` of `test/program_coverage_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_file_headers.py test/test_program_coverage_map.py test/test_no_orphans.py -q -n0 -p no:cacheprovider` is run at the end of 06-06 and reports 0 failed then. Run now, only checks that `_dash_note` is listed but not yet called may fail, because 06-06 adds the callers.]]></verify>
  <done>dash's Mata library carried a note printer that shows under quietly and hides under capture, listed in its header and in the library guard.</done>
</task>

<task type="auto" id="06-06">
  <name>Route the eleven ado and Mata notes</name>
  <files>dash.ado, dash_parse.mata, test/test_private_files.py</files>
  <action><![CDATA[
    Apply TR-06.8 to the eleven note rows of Evidence E3, finding each by its quoted text (the line numbers drifted with S03): rows 1, 2, 4, 5, 6, 7, 8 change `_dash_say("txt", ` to `_dash_note(` with the same arguments; row 3's `display as text` and row 9's two `display` lines become the single `mata: _dash_note(...)` statements of TR-06.8; rows 10 and 11 in `_dash_fn_spec_tail` change `_dash_say("txt", ` to `_dash_note(`. Leave every row of TR-06.9 unchanged. Flip `test/test_private_files.py::TestTheAdoUsesThePrivateDir::test_the_note_is_printed_once_per_command` (2063) to `'_dash_note(' in to`, with its `Flipped:` line in `$S6/06-flips.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c '_dash_say("txt"' dash.ado` prints 4 (the status lines) and `grep -c '_dash_say("txt"' dash_parse.mata` prints 0; `grep -c 'mata: _dash_note(' dash.ado` prints 9; `python3 -m pytest test/test_private_files.py test/test_file_headers.py test/test_program_coverage_map.py test/test_no_orphans.py test/test_security_surface.py test/test_option_validation.py -q -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>dash.ado's and dash_parse.mata's eleven notes printed through Stata's note channel, and the status lines and twoway's verbatim notes kept their own channel.</done>
</task>

<task type="auto" id="06-07">
  <name>Teach the log gates the note form</name>
  <files>test/help_examples.py, scripts/release_verdict.py</files>
  <action><![CDATA[
    Apply TR-06.10: in `test/help_examples.py` FLAGGED (563-578) change the first pattern to `r"^(?:\(note:\s+)?dash: ignoring unsupported option\(s\):"` and append `(re.compile(r"\(note:\s"), "prints a note")` as the last entry, with a comment citing WP-30 P1.26a and the measured form; in `scripts/release_verdict.py` DIAGNOSTICS (41-51) add `"(note:",` after `"drew nothing",` with a comment. Change nothing else in either file.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_examples.py test/test_release_verdict.py -q -p no:cacheprovider` reports 0 failed, including the six tests 06-02 wrote.]]></verify>
  <done>The help-example judge and the release gate flagged any note line an example did not show, in the new form as in the old.</done>
</task>

<task type="auto" id="06-08">
  <name>Migrate the UserWarning needles</name>
  <files>test/test_custom_scheme.cscript, test/test_render_log_clean.cscript, test/test_render_locate.cscript</files>
  <action><![CDATA[
    Apply TR-06.11. In `test/test_custom_scheme.cscript` add `_cs_notes` directly after `_cs_log` (ends 302), replace each of the 14 `_cs_log … "UserWarning" N` lines (331, 340, 354, 366, 381, 394, 405, 415, 444, 462, 523, 607, 616, 625) by `_cs_notes … N`, make CS-12 (482-485) count `(note:` and `Warning:` (each 0), and reword header lines 36, 39, 48, 57, 68. In `test/test_render_log_clean.cscript` make checks [4/5] and [5/5] count `(note:` and `Warning:` as TR-06.11 says, update their display lines and the header (28-45), and bump its Version line. In `test/test_render_locate.cscript` change LOC-16's needle list (372). Write one `Flipped:` line per script to `$S6/06-flips.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c UserWarning test/test_custom_scheme.cscript test/test_render_log_clean.cscript test/test_render_locate.cscript` prints 0 for each; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider` passes; the three scripts pass through the driver in 06-12.]]></verify>
  <done>Every log check that counted Python warnings counted note lines and Python warning lines instead, so each absence check still bit and each control counted its one note.</done>
</task>

<task type="auto" id="06-09">
  <name>Flip the note-prefix readers</name>
  <files>test/test_adversarial.cscript, test/test_wp29_truth.cscript, test/test_json_escaping.cscript</files>
  <action><![CDATA[
    In `test/test_adversarial.cscript` PF-09 (3597) change `x.startswith("dash: note:")` to `x.startswith("(note:  dash: ")` and update the comment at 3563. In `test/test_wp29_truth.cscript` change `_pf_notes` (3074-3075) the same way, which covers PF-11 step 4 and PF-12. In `test/test_json_escaping.cscript` reword the JSE-17 comment (454-461) as TR-06.11 says. Write the `Flipped:` lines to `$S6/06-flips.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c 'startswith("dash: note:")' test/test_adversarial.cscript test/test_wp29_truth.cscript` prints 0 for each; the scripts pass through the driver in 06-12 (PF-09, PF-11 and PF-12 print PASS).]]></verify>
  <done>The privacy cases read the R-8 note in its new form, so their presence and absence checks kept their meaning.</done>
</task>

<task type="auto" id="06-10">
  <name>State the note channel in the help</name>
  <files>dash.sthlp, test/test_help_claims_8.cscript, test/test_private_files.py</files>
  <action><![CDATA[
    Apply TR-06.12 to dash.sthlp: the example line 599, the sentence at 620-621, the new paragraph after 600 (exact SMCL under Stata truth "Help paragraph"), the example line 3612, and the two sentences of 1838-1845. Leave 1584 and 1622 as they are. In `test/test_help_claims_8.cscript` flip HC8-01 (383), HC8-06 (506) and HC8-07 (515) to the exact lines `(note:  dash: ignoring unsupported option(s): …)` with two blanks. Flip `test/test_private_files.py::TestTheHelpDocumentsTheTempfiles::test_it_states_the_note_and_the_anti_hijack_guard` (2122) from `"dash: note:"` to `"(note: dash:"`. Add the `Flipped:` lines to `$S6/06-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_examples.py test/test_help_conformance.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_3.py test/test_help_claims_4.py test/test_help_claims_5.py test/test_help_claims_6.py test/test_help_claims_7.py test/test_help_claims_8.py test/test_private_files.py -q -p no:cacheprovider` reports 0 failed; `grep -c 'How a note is printed' dash.sthlp` prints 1; `grep -c '{cmd:dash: ignoring unsupported' dash.sthlp` prints 0.]]></verify>
  <done>The help said how dash prints a note, and its example output lines, quoted note and quietly claim matched what dash printed.</done>
</task>

<task type="auto" id="06-11">
  <name>Run the section's Python tests</name>
  <files>none</files>
  <action><![CDATA[
    Run every pytest file this section changed or that runs the renderer's entry point, then the registries and the no-drawing-change guards: `python3 -m pytest test/test_note_channel.py test/test_help_examples.py test/test_release_verdict.py test/test_private_files.py test/test_string_value_export.py test/test_serve_launcher.py test/test_serve_lifecycle.py test/test_serve_token.py test/test_resource_limits.py test/test_adversarial_matrix.py test/test_help_claims_2.py test/test_help_claims_4.py test/test_function_test_map.py test/test_program_coverage_map.py test/test_file_headers.py test/test_no_orphans.py test/test_cscript_hygiene.py test/test_security_surface.py test/test_option_validation.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_mode_parity.py test/test_varlist_expansion.py -q -p no:cacheprovider > "$S6/06-11.log" 2>&1`. Then apply each mutation of "Mutation checks" by hand in turn, run the named test, see it fail, and restore the file (`git -C "$WT" diff --stat` must show the same files before and after).
  ]]></action>
  <verify><![CDATA[`tail -1 "$S6/06-11.log"` reports 0 failed and no error; each of the four mutations turned its named test red (recorded in `$S6/06-mutations.txt`), and `git -C "$WT" diff --stat` is unchanged by them.]]></verify>
  <done>Every Python test the section touches passed, both build modes kept their pages, the served name guards held, and the tests were shown to catch each fault they exist for.</done>
</task>

<task type="auto" id="06-12">
  <name>Run every script that reads a note</name>
  <files>none</files>
  <action><![CDATA[
    Build the list `{ grep -lE 'UserWarning|ignoring unsupported option|not a recognised|dash: note:|could not fit model|drew nothing|not implemented and ignored|\(note:|only apply to dash build|function points stored|writes HTML, not a Stata|ignored .* at the end|pci draws no labels|holds text that is not valid' test/*.cscript; printf '%s\n' test/test_help_examples.cscript test/test_mata_library_guard.cscript test/test_echo_text.cscript test/test_wp30_truth.cscript; } | sort -u > "$S6/06-scripts.txt"` (about 29 scripts). Write each driver with `while read p; do n=$(basename "$p" .cscript); printf 'cd "%s/test"\ndo "%s/test/%s.cscript"\n' "$WT" "$WT" "$n" > "$S6/run_$n.do"; done < "$S6/06-scripts.txt"`, then run the drivers three at a time: `sed 's#.*/##; s#\.cscript$##' "$S6/06-scripts.txt" | xargs -P 3 -I{} sh -c 'WP30_ONLY=S06 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$0" "$0/run_{}.do"' "$S6"`. Never run `run_all_cscripts.do` or `make cert`. A failing case is fixed in the code or flipped with a reason in the case named, then that script is run again.
  ]]></action>
  <verify><![CDATA[For every script in `$S6/06-scripts.txt`: `grep -cE '^r\([0-9]+\);$' "$S6/run_<name>.log"` prints 0, `grep -c 'FAIL' "$S6/run_<name>.log"` prints 0 (a FAIL inside a case's own description text is checked by eye), and `grep -c '^SKIP' "$S6/run_<name>.log"` prints 0; NC-01..NC-06 each print PASS, and `run_test_wp30_truth.log` holds `test_wp30_truth: ALL CHECKS PASSED`.]]></verify>
  <done>Every certification script that reads a note or a warning passed against the new channel, with no skip, and the section's six cases passed.</done>
</task>

<task type="auto" id="06-13">
  <name>Close P1.26a and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the partners' new needles first: `git -C /Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s04 diff "$(cat $S/batch-2-base.txt)" -- test/ | grep -n '^+.*UserWarning'` and the same for wp30-s05; record the result in `$S6/06-partners.txt` and report any hit to the orchestrator (it is migrated after landing, Notes trap 9). Close the entry whose title is `WP30_OPEN["P1.26a"]` in place (A140): `- [x]`, and the Resolution of Notes "BUGS.md Resolution", every test a full node id; delete the `"P1.26a"` key line from `WP30_OPEN`. Replace the two `<!-- WP-30 P1.26a -->` markers in place with the CHANGELOG lines of Notes, each ending `(WP-30, P1.26a)`. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`; run `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); launch `$S/full_suite_queue.sh "$WT" "$S6/06-full-1.log"` in the background and wait with an until-loop on its `exit=` line (E1; E6 for the four known flaky tests). Stage exactly: dash_render.py dash.ado dash_parse.mata dash.sthlp BUGS.md CHANGELOG.md scripts/release_verdict.py test/help_examples.py test/test_note_channel.py test/test_help_examples.py test/test_release_verdict.py test/test_private_files.py test/test_string_value_export.py test/function_test_map.py test/program_coverage_map.py test/test_tracking_documents.py and the eight cscripts test/test_render_log_clean.cscript, test/test_wp30_truth.cscript, test/test_custom_scheme.cscript, test/test_render_locate.cscript, test/test_json_escaping.cscript, test/test_adversarial.cscript, test/test_wp29_truth.cscript and test/test_help_claims_8.cscript, and no other file. Write the body as the commit boundary says into `$S6/06-msg.txt`, check G7, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -2 "$S6/06-full-1.log"` shows 0 failed and `exit=0`; `git -C "$WT" diff --cached --name-only | wc -l` printed 24 before the commit and none of CLAUDE.md, .gitignore, AGENTS.md, .gitnexus/ or .ultraplan/; `git -C "$WT" log -1 --format=%s | grep -c '(WP-30 P1.26a)'` prints 1; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.26a -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.26a": "' test/test_tracking_documents.py` prints 0; `grep -c '(WP-30, P1.26a)' CHANGELOG.md` prints 2; `git -C "$WT" branch --show-current` prints `wp30-s06`.]]></verify>
  <done>P1.26a was closed in BUGS.md naming existing tests, its key and both markers were gone, and one green commit on wp30-s06 carried the section.</done>
</task>

## Section completion criteria

- One commit on `wp30-s06`, subject ending `(WP-30 P1.26a)`, whose full run through the queue showed 0 failed. Its body opens with the saved failure text and carries the Regression, Guard, Flipped and BUGS.md lines.
- `test/test_note_channel.py` (all classes) and the new judge and verdict tests are green. NC-01..NC-06 print PASS, and every script of `$S6/06-scripts.txt` passes with no skip.
- In both build modes, a session filter of "ignore" or "error" and `PYTHONWARNINGS=error::UserWarning` leave dash's notes printed and rc 0. No note line holds `UserWarning` or a path.
- dash.ado's and dash_parse.mata's eleven notes go through `_dash_note`. The four status lines and twoway's four verbatim notes are unchanged.
- The registries, the served name guards, `test_mode_parity.py` and `test_varlist_expansion.py` are green, with no copy-list change.
- BUGS.md entry `P1.26a` is closed, the `WP30_OPEN["P1.26a"]` key is gone, both markers are replaced, and the help states the channel.
- Nothing staged outside the 24 files. No plan file, `CLAUDE.md`, `.gitignore` or `AGENTS.md`.

## Notes

**Traps for the executor.**
1. **The scope wraps the call, not `main`.** About 16,700 tests capture dash's notes as warnings from `main()` and `render()`, which is why `test_main_called_directly_still_warns` exists. Never move the scope into `main()` or `render()`.
2. **Self-contained helpers.** `_dash_emit_note` and `_dash_smcl_escape` must read no module-level constant. S23 copies them by name, and a missing constant is a served-only NameError (RK-9). Keep the text-class regex and the 4,000 bound as literals inside the function.
3. **The stand-in `sfi` modules.** `test_serve_lifecycle.py` installs `sfi` stubs with `pollstd` only. The emitter must fall back to stderr through `getattr`, never raise.
4. **Restoring filters in the cscripts.** NC-03 and NC-04 change the session's filters. The dash call is always `capture noisily`, so `__exit__` runs. A leaked "ignore" would silence every later script in a certification run, the hazard render_log_clean check [5/5] was written for.
5. **Cscript hygiene.**
   - Python lines read Stata values with `Macro.getLocal`, never a macro inside a Python string literal (`test_cscript_hygiene.py` in-string macro rule).
   - NC-06 (d) reports `MISSING` through `getattr`, never through `capture python:`, so it adds no import probe and moves no hygiene pin (`len(with_probes) == 13`).
   - No `SKIP…Python` line is added.
6. **Raw and rejoined logs.** `cert_file_has` searches raw bytes, and `cert_log_has` and `_rlc_count` rejoin Stata's `> ` continuations. A note grows by nine characters, so an exact or raw check near the linesize can wrap. The exact checks (HC8) set linesize 255. 06-12 is what proves the rest.
7. **Anchors drift.** S02 and S03 landed in batch 1. Find dash.ado sites by their quoted text, never by number.
8. **Merge rules.** R1 covers the truth block, the area run in render_log_clean and in-place flips only. R2: no copy-list change (row S06), and the map entries go under S06's anchors. R3: help ownership is item 5 of Differences (:584-622, :599, :620-621), :3612's example and :1838-1845 (the tempfiles paragraph; S04 edits the CSP paragraph of Server Mode, a different paragraph). R4: two markers. R5: only S06's entry and key. R6: `_needed` and the header index in place; programs keep S03's `version 19`. R9: the flips of E8. R10: no pin moves.
9. **A partner's needle (A150).** S04 and S05 run in parallel worktrees cut from the same base, so S06's commit cannot see a needle they add. 06-13 reads their diffs read-only and reports a hit. If one lands, the merger's G8 shows it red after S06 lands, and the fix is S06's (index step 2): a fresh `wp30-s06` worktree cut from `wp30-p1`, a commit with subject ending `(WP-30 P1.26a)`, landed by the routine.
10. **The failure text goes into the commit body.** Pytest and Stata print absolute paths, and the scratch directory's path holds a word G7 forbids. Cut every path in `06-P1.26a-failure.txt` and in the body to its last component before G7 runs.
11. **Python versions.** S05 may lower the floor to 3.11. The code uses nothing newer than 3.10, and `contextlib`, `catch_warnings()` and `threading.main_thread()` exist throughout. On a free-threaded 3.14 build, where `sys.flags.context_aware_warnings` is on, `catch_warnings` is context-local. The test suite does not run one, and that case is left to the platform package (M4).

**Hand-offs to later sections.**
- **S23.** Copy `_dash_smcl_escape` and `_dash_emit_note` after `"_dash_note_empty_layer",`. Pass `said=_dash_said` from `__main__` to `_dash_launch_app`; the set holds the raw message texts printed at build. Keep the estimator note `(note:  regress could not fit model)` for `lfit` with its own `if` keeping no row, because twoway prints it (p3). NC-02 pins it, and M6 silences only "drew nothing". The launcher's link-file note (dash_render.py:4334) and help 1584 and 1622 are S23's to move into the channel.
- **S22, S26, S29, S33, S34, S41 and every later note.** Raise with `warnings.warn("dash…: …")` inside `main()`, or call `_dash_emit_note` (Python) or `mata: _dash_note(...)` (ado). Count note text with `(note:` and `Warning:`. Never assert a note's full wording where another section may reword it.
- **S34.** render_log_clean's control [5/5] and CS-10 use `scheme-zzdashrlc.scheme` and `scheme-zzdashtest.scheme` in the working directory, so that dash cannot translate them. Once S34 finds `scheme-NAME.scheme` along the ado-path, both controls go silent. S34 replaces them with a scheme dash still cannot read and keeps their count of one note.
- **S30, S24, S36.** They may reword the colour, symbol and style notes. S06's tests are relational for that reason.

**BUGS.md Resolution (06-13, verbatim apart from the date):**

`- Resolution: Fixed <ddmonyyyy> (WP-30, P1.26a). Every note dash prints in Stata's session takes twoway's channel. The renderer's __main__ block runs main() inside _dash_note_scope, which prints each dash warning once through _dash_emit_note as one (note:  dash: ...) line in text colour on Stata's error stream (SFIToolkit.errprintln, SMCL-escaped by _dash_smcl_escape, at most 4,000 characters, with no file path or source line), whatever the session's warnings filters or PYTHONWARNINGS say, and leaves every other warning to those filters; dash's copies of twoway's estimator and scheme-lookup notes print as plain text, which quietly hides, as twoway's do. main()'s unprivate-app note and the data writer's UTF-8 note use the same emitter, and dash.ado's and dash_parse.mata's eleven notes use its Mata twin _dash_note, so all of them show under quietly and are hidden by capture; help_examples.FLAGGED and release_verdict.DIAGNOSTICS read the new form. Saved builds, dash build, server and dash serve's build alike. Pinned by test/test_note_channel.py::TestTheRendererEntryPoint::test_an_ignore_filter_hides_no_note, test/test_note_channel.py::TestTheRendererEntryPoint::test_an_error_filter_raises_no_note, test/test_note_channel.py::TestTheRendererEntryPoint::test_no_path_or_source_line_is_printed, test/test_note_channel.py::TestTheRendererEntryPoint::test_pythonwarnings_in_the_environment, test/test_note_channel.py::TestTheNoteScope::test_a_note_raised_twice_prints_once, test/test_note_channel.py::TestTheNoteLine::test_the_line_is_smcl_escaped, test/test_render_log_clean.cscript NC-03, test/test_render_log_clean.cscript NC-04, test/test_render_log_clean.cscript NC-05, test/test_render_log_clean.cscript NC-06, test/test_wp30_truth.cscript NC-01, test/test_wp30_truth.cscript NC-02. Residual, deferred (WP-30): the served app's session notes, its stderr and the launcher's own lines reach Stata in P1.26b (S23).`

**CHANGELOG lines (06-13, in place of the two markers):**

- `### Changed behaviour (may need your do-files changed)`:
  `- dash prints its notes as twoway prints its notes. Each is one line, (note:  dash: ...), in text colour; it shows under quietly and set output error, and capture hides it. It never names dash's files or Python source lines. Before, the renderer's notes were red Python warnings (".../dash_render.py:8679: UserWarning: dash: mcolor(notacolor) is not a recognised colour; ..." and a source line) that quietly did not hide, and dash.ado's own notes ("dash: ignoring unsupported option(s): play()", "dash: note: ...") were hidden by quietly. dash's copies of twoway's own "(note:  regress could not fit model)" and "(note: scheme X not found, using s2color)" print as plain text that quietly hides, as twoway's do. A do-file that searches a log for "UserWarning", or for a line beginning "dash: ignoring unsupported option(s)" or "dash: note:", now finds "(note:  dash: ...)". (WP-30, P1.26a)`
- `### Fixed in WP-30`:
  `- A Python warnings filter set in the session no longer hides or escalates dash's notes. After python: warnings.filterwarnings("ignore") the note still prints. After python: warnings.simplefilter("error"), or with PYTHONWARNINGS=error, the dashboard is drawn (rc 0), where it failed with r(7102) and a 60-line traceback. Other packages' warnings still follow the session's filters, and a note raised twice in one command prints once. (WP-30, P1.26a)`

**Notes for the closeout (S58; A145).**
- **GAPS2.md X4** (GAPS2.md:1976): `- **Tracked:** Closed in WP-30, BUGS.md "<P1.26a title>", commit <sha>` for X4-a, X4-b, X4-c and X4-d. X4-d's evidence is S58.5's certification log: `grep -cE 'dash_render\.py:[0-9]+: UserWarning' <cert log>` prints 0, against 87 in `.ultraplan/handoff/wp29-run_all_cscripts.log`. Append `(WP-30, X4)` to the Resolution.
- **GAPS2 I summary** (GAPS2.md:1590, "Logging … weaker than the rules ask"). Its measurable part for the Stata process (notes lost under filters, hidden by quietly, raw paths) is closed by this commit. Its served half is F5a and F5b (S23's commit), so the Tracked line names both shas.
- **DROPIN-REMAINING.md P1.26** (line 146): part a closed by S06's commit (the raw UserWarnings with paths; the "ignore" and "error" filters), with the ado-note finding m7. The first two bullets and the WP-29 S12 note are S23's.
- **ROADMAP.md:452** ("UserWarnings … survive quietly, though not capture"): add a WP-30 note that notes now take twoway's channel (P1.26a).
- **Help terminology.** dash.sthlp still says "named in a warning" at 1312-1313, 2123, 2919, 2962, 2967 and 3023. These paragraphs belong to S10, S18, S28, S31, S48, S51 and S52 (R3), so S06 did not reword them. They stay unreworded through WP-30: three test lines pin the phrase, so the closeout leaves it and files a P3.3 note instead (ratification row 44, 06oct2026; section-58 R58-14).
- **test/cert_helpers.do:101-110** still explains log rejoining by the old warning form. It is accurate history, and S58 may reword it.

**Resolved by the review (was an open question; register P1.26.2 and P1.26.4, A82, A84):** both defaults below stand. P1.26.2's ruling is "Like twoway's … twoway's measured visibility", so each copy of a twoway note takes the visibility twoway gives that note (M1: match Stata), and A84's form is `(note: …)`, which `(note:  dash: <text>)` is. Ratification item 13 remains the maintainer's to ratify as written; nothing here needs a separate decision.
1. **The two visibility classes.** Item 13 says notes "show under quietly". Measured 03oct2026, twoway itself has two classes. Its named-style notes show under `quietly`, but `(note:  regress|fracpoly could not fit model)` and `(note: scheme X not found, using s2color)` are plain text that `quietly` and `set output error` hide (p3, p4). Default: dash's copies of those two print as twoway prints them, hidden by `quietly`, and every other dash note shows under `quietly`. Alternative: every dash note shows under `quietly`.
2. **The exact form.** Default: `(note:  dash: <text>)`. It uses twoway's two blanks, keeps dash's own prefix inside the parentheses, and shortens a leading `dash: note: ` to `dash: `. Alternative: drop the `dash:` prefix, `(note:  <text>)`, which would also move every substring needle that includes `dash: `, more than 100 lines across 20 scripts.
