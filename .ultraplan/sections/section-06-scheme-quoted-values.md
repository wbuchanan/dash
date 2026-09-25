# Section 06: Scheme quoted values (D1)

> Part of: WP-28 · Gaps: D1 · Risk: green · Batch: 1 · Depends on: none · Blocks: 19 · Tasks: 4, 1 commit (D1)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **1** · Depends on **none** · Blocks **19** · Risk **green** · Commits: one commit (D1) → CHANGELOG `Results that change`

- D13/Q30: third-party scheme files are out of scope. The PLUS sweep (the env-gated test), the copied third-party scheme fixture, its p1-p15 and both-modes tests and every "127 of 129"/"129 local files" claim are gone, and the old optional SVG-comparison task after the closing task is deleted (feasibility #18; no colorvar case is added for it either, the file being third-party). D1 is pinned with a scheme file the test writes itself: a copy of the shipped `schemes/s1rcolor.scheme` with `color background "255 0 0"`, `color p1 "26 71 111 %20"`, `color p2 "0 255 0%50"`, an unclosed quote, a `label "…"` line and a tab-separated line. GAPS2's measured symptom on a copied third-party file may be quoted as history; no task or test names that file.
- D11 (`sections/BRIEF.md` "Certification scripts"; `sections/index.md` rule R1): the CQ-01..CQ-03 cases join `test/test_custom_scheme.cscript`; no new script, no runner or pin edit.
- D10/F-10: the warning's file name goes through `_safe_name(os.path.basename(path))` (printable, at most 80 characters), as the echoed line already does.
- D3 (consistency #2): the D1 entry is appended at the END of BUGS.md with `- Resolution: Fixed <ddmonyyyy> (WP-28, D1). …`; the CMYK/hsv/`colour*#` forms are its `Residual, deferred (WP-28): …` clause (PRD §7, S19's deferred list).
- D2 (`sections/index.md` rule R3; section-01 TR-01.7; consistency #1): 06-04 replaces the marker `<!-- WP-28 D1 -->` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of `### Results that change` with one line ending `(WP-28, D1)`, quoting the failing test's recorded output as the old value (Q24).
- D1/F-01 (with the worktree-branch commit rule of `sections/index.md` step 1): 06-01 to 06-03 do not commit; the section's one commit is made by 06-04 on the worktree branch `wp28-s06`, subject ending `(GAPS2 D1)`; the merger lands it onto `s3-bugs`.
- feasibility #3: no `(new)` annotation in `<files>`; four tasks after the deletion, renumbered 06-01..06-04.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

dash.sthlp:2813 tells a user who wants another package's scheme to copy the file into the
working directory. Stata's own colorstyle help writes colours as `"255 0 0"`, and Stata's own
sttrans scheme writes `color p1 "26 71 111 %20"`. GAPS2 D1 measured what dash does with such
a file: "`SchemeParser._parse_lines` (dash_render.py:3988-3993) takes `tokens[-1]` as the
value, so `color background "255 0 0"` is stored under a malformed key and the directive is
lost without a warning. In a probe, a copied third-party scheme drew every series #606060
with 0 warnings." (That probe used a third-party file; third-party scheme files are out of
scope by decision, DISCOVERY Q30 and review D13, so the symptom is history here and the rule
is pinned with a scheme file the test writes.) The same reader stores every shipped scheme's
`label "s2 color"` line under the key `label "s2`, keeps `sequence` lines Stata skips, and
never strips a compound quote (`special fpfmt_es \`"%6.2f"'` in s2color).

After this section `_parse_lines` reads a line the way Stata's `scheme.class` reads it
(:189-226): tabs become blanks, `*`, `//`, `*!`, `sequence` and `label` lines are skipped,
the line is tokenised so that a quoted string is one token (an unclosed quote reads to the end
of the line, as `_textbox_string_end` does for textboxes), the key is the first two tokens,
the value is the third with its quotes stripped, and later tokens are ignored; a two-token
line is a class default. `"R G B"`, `"R G B %NN"` and `"R G B%NN"` then reach
`translate_mcolor` and `parse_color_alpha`, which already accept the unquoted forms. A line
that cannot be read that way is named once, with its file (its bounded basename) and line
number, under the same bound `_include` uses for its notes, and nothing is stored under a
malformed key. The served app receives the parsed dict as `_SCHEME_PROPS` (:24708) and
rebuilds the parser from it (:24714-24720), so it inherits the fix with no template change.

D1 is alone in this section because it changes one method of `SchemeParser` and nothing else
in the renderer; `hsv`, CMYK and `colour*#` values are D7's shared work and stay out of scope,
and third-party scheme files are out of scope by decision (Q30/D13). The section is green: the
reference tokeniser already exists in `scripts/extract_scheme_truth.py`, the shipped schemes
are unaffected by the switch, and a before/after snapshot test proves it.

**Test order (CLAUDE.md rule 7) and commit rule (D1): task 06-01 writes every failing test**
(the regression tests read a scheme file the test module writes itself), runs them against
the unmodified tree and saves the failure text to `<scratch>/06-01-failure.txt` -- it does not
commit (a red tree is never committed, rule 4); 06-02 makes them green; 06-03 certifies through
dash.ado in the existing custom-scheme script; 06-04 closes the entry, runs the full pytest
suite once in the worktree and makes the section's ONE commit on the worktree branch
`wp28-s06`, subject ending `(GAPS2 D1)`, whose body opens with the saved failure text (S01
TR-01.9); the merger lands that commit onto `s3-bugs` (`sections/index.md` step 1).

## Risk: [green] — a tokeniser change in one method, checked against every shipped scheme before and after

- **Why.** The rule is Stata's own and already implemented once in this repository; the
  change cannot alter any shipped translation's drawn output, and a snapshot test says so.
- **Risk factors.** (1) A shipped translation might carry a line the new reader warns on
  (a stray one-token line), which would put a warning into every render and turn
  `test_custom_scheme.cscript` CS-11/CS-12 red. (2) A test that counts warnings on a
  hand-written scheme with junk lines could gain a warning.
- **Mitigation.** The snapshot test asserts zero warnings per shipped file; the warning tests
  are re-run and any changed count is flipped with its reason; the test-written scheme file
  holds every odd line form the reader must accept (unclosed quote, `label`, tabs) so a
  spurious warning is caught in this section's own tests.

## Dependencies

- **Depends on:** none.
- **Blocks:** 19.
- **Parallel batch:** 1. Batch-1 merge order S01, S03, S02, S06, S07, S08, S09, S10
  (`sections/index.md` step 1).
- **Can run with:** every other batch-1 section. S06 edits `SchemeParser._parse_lines` and
  adds one static method beside it; no other section edits `SchemeParser`. It extends
  `test/test_custom_scheme.cscript`, which no other section edits.

## Evidence

### The reader (`dash_render.py`, checked at 91d97be)

`SchemeParser._parse_lines` :3941-3998, called by `_parse_file` :3897-3939 (from `__init__`
:3713-3716 and `_include` :4000-4049). The tail of the loop:

```python
 3955            if not line or line.startswith("*"):
 3956                continue
 ...
 3990            tokens = line.split()
 3991            if len(tokens) < 2:
 3992                continue  # malformed line — skip
 3993
 3994            category = tokens[0]
 3995            value = tokens[-1]
 3996            subcats = tokens[1:-1]
 3997            key = (category + " " + " ".join(subcats)).strip() if subcats else category
 3998            props[key] = value
```

`color p1 "31 119 180"` splits into `color`, `p1`, `"31`, `119`, `180"`, so the key is
`color p1 "31 119` and the value `180"`; `color p1` is never set and the p# chain
(`_first_present((f"color p{i}", "color p"))`, :4465-4468) falls through to `color p`. The
`#include` handling (:3960-3988), `_include` (:4000-4049), `_resolve_path` (:3785) and the
bounds `_MAX_SCHEME_INCLUDE_DEPTH` (:3374, 32), `_MAX_SCHEME_INCLUDES` (:3380, 256) and
`_MAX_INCLUDE_NOTES` (:3895, 10) are untouched. `_include`'s note bound (:4022-4041) counts
in `_notes["\0count"]` and warns the first ten times, then once more; that is the bound a
per-line warning reuses. `_safe_name` (:4052-4057) keeps a warning's echo of file text to 80
printable characters; the file's basename goes through it too (F-10).

The colour readers already accept the unquoted forms (research report A, D1 table):

| Input (after quote-stripping) | `translate_mcolor` (:3182) | `parse_color_alpha` (:3116) |
|---|---|---|
| `26 71 111` | `#1a476f` | `('#1a476f', None)` |
| `26 71 111 %20` | `#1a476f` | `('#1a476f', 0.2)` |
| `0 255 0%50` | `#00ff00` | `('#00ff00', 0.5)` (`rfind("%")`, :3145) |
| `"26 71 111"` (quotes kept) | ValueError | `(None, None)` |
| `khaki*0.3`, `hsv 120 1 1`, `0 100 100 0` | refused | refused — D7 |

`_color` (:4077-4100) warns "dash scheme: colour ... is not a colour dash recognises" for a
present but unreadable key, and `_color_alpha` (:4102-4128) carries the `%NN` opacity; both
are unchanged and receive the stripped value.

### The served copy

`OptionTranslator`, `SchemeParser` and `GlyphMapper` are copied whole (:24698-24700). The
scheme travels as `_SCHEME_PROPS = %r` of `self.scheme._props` (:24708), and
`_dash_build_scheme` (:24714-24720) does `SchemeParser.__new__`, `_s._props =
dict(_SCHEME_PROPS)`, `_s._init_properties()`. A parsed dict fixed at build time is a fixed
served scheme; no template edit.

### Stata's grammar

`$BASE/s/scheme.class:189-226` (research report A §D1, D §9): `local line : subinstr local
line "\`=char(009)'" " ", all`; `tokenize \`"\`line'"'`; `args style id stylename`; `#include`
is dispatched on the first token; lines whose first token is `*`, `//`, `*!`, `sequence` or
`label` are skipped; `if "\`stylename'" == "" { local stylename \`id'; local id _default }`.
`tokenize` makes a double-quoted or compound-quoted string one token and removes the quotes.
`scheme_files.sthlp:121-130`: "the RGB values and any style using more than one token or word
must be enclosed in quotes"; `:343-350`: extra spaces inside an RGB string are ignored;
`colorstyle.sthlp:221-240`: `"0 255 0%50"`.

Reference implementation already in the repository: `scripts/extract_scheme_truth.py`
`SchemeResolver._load` (:207-262) with `_TOKEN = re.compile(r'"[^"]*"|\S+')` (:297), whose
docstring records `symbolsize p small *medium` read as `small` (measured, sttrans marker
radius 19.29). It handles neither compound quotes nor an unclosed quote.

### The files on disk

- `/Applications/StataNow/ado/base/s/scheme-s2color.scheme`: `sequence 1210` (:25), `label
  "s2 color"` (:26), `special fpfmt_es \`"%6.2f"'` … `special fpfmt_order \`"_VAR_"'`
  (:78-85, compound quotes), `color p1 navy` (:430). `scheme-sttrans.scheme:43-49`: `color p
  "26 71 111 %20"`, `color p1 "26 71 111 %20"`, … No base scheme has an unclosed quote
  (`grep -n '^[a-z]* [a-z_0-9]* "[^"]*$' scheme-*.scheme` finds none at 91d97be; research
  report A's `scheme-meta.scheme` example is not on this install). No base scheme has a `//`
  line.
- dash's shipped translations, `schemes/*.scheme` (20 files): sttrans was transcribed to
  `color p1 #1a476f%20` (:47; provenance :267 `transcribed from scheme-sttrans.scheme:44
  \`color p1 26 71 111 %20'`), which is why sttrans works today. `schemes/s1rcolor.scheme` is
  the shipped file the test module copies and edits (it holds a `color background` line, as
  `test_custom_scheme.cscript`'s `_cs_write_theme` relies on at :104-127).
- Third-party scheme files under Stata's PLUS directory are out of scope by decision
  (DISCOVERY Q30, review D13): none is read, copied, swept or named by this section.
- The test-written scheme lives under pytest's `tmp_path` (and the cscript's under
  `c(tmpdir)`): no fixture is added to `test/fixtures`, so `test_fixtures_are_committed.py`
  needs no new name and no `git add -f`.

### Existing tests that pin today's behaviour

Listed so the executor flips or revises, never deletes:

- `test/test_scheme_coercion.py::TestParseFile::test_directives_are_read` (:355-367,
  three-token lines) and `::test_comments_and_blank_lines_are_ignored` (:369-372): unchanged
  by the new reader; they stay as regression cover.
- `test/test_scheme_consumption.py::TestAnIncludeIsSplicedWhereItStands` (:1562-…): the
  function map's entry for `_parse_lines` (`test_a_repeated_include_overwrites_again`);
  its warning-count tests (`test_a_hostile_name_is_printed_bounded_and_printable`, the
  `_MAX_SCHEME_INCLUDES` bound) write only `#include` and `color` lines, so no count should
  change; if one does, flip it with the reason in the commit message.
- `test/test_custom_scheme.cscript` CS-10 (exactly one UserWarning for `set scheme
  zzdashtest`) and CS-11/CS-12 (no warning for the shipped names): the shipped files must
  parse with zero warnings (TR-06.7). The script's scaffolding (`_cs_write_theme` Mata
  function :104-127, `_cs_run` :184, `_cs_count` :207, `_cs_expect` :224, `_cs_done` :235,
  `_cs_log` :249, `_cs_page` :265, the working directory `cs_dir` under `c(tmpdir)`, the
  restore/cleanup section :553-560 and the summary :562-572) is what CQ-01..CQ-03 reuse.
- `test/test_scheme_fidelity.py` (`raw_props` :329-331, `declared` :334-342) reads
  `_props` by key for every shipped scheme against `scheme_truth.json`: unchanged keys, so
  unchanged results; the snapshot test in TR-06.6 makes that explicit.
- `test/function_test_map.py`: `SchemeParser._parse_lines` :239, `_parse_file` :238,
  `_color` :223, `_color_alpha` :224, `_include` :229, `_safe_name` :242 stay; the new
  tokeniser needs an entry.

## User stories

- **US-06.1** As the scheme author, I want a scheme written the way Stata's own schemes are
  written, with quoted RGB and `%opacity`, to be read by dash, so that the copied file draws
  the colours it declares.
- **US-06.2** As the Stata user pasting twoway syntax, I want `scheme(myquoted)` with a file
  in my working directory that writes `color background "255 0 0"` and `color p1 "26 71 111
  %20"` to draw that background and that p1 colour in the saved page and the served app
  alike, so that the picture is the one Stata draws.
- **US-06.3** As the scheme author, I want a line dash cannot read to be named once, with
  its line number, so that a typo is found rather than silently dropped.
- **US-06.4** As the maintainer, I want every shipped scheme to parse exactly as before, so
  that no existing dashboard changes colour.

## Business requirements

- **BR-06.1** A scheme directive whose value is quoted (`"R G B"`, `"R G B %NN"`,
  `"R G B%NN"`, a quoted format or text) is read with the value the quotes enclose.
- **BR-06.2** A directive's value is its third word; anything after it is ignored, as Stata
  ignores it; a two-word directive sets the class default.
- **BR-06.3** Comment lines (`*`, `*!`, `//`), `sequence` and `label` lines change nothing.
- **BR-06.4** A directive line that cannot be read is named once with its file and line
  number, at most ten per parse plus one summary line, and nothing is stored for it; the
  file name and the echoed line are bounded and printable.
- **BR-06.5** The twenty shipped schemes draw exactly what they drew before, with no warning.
- **BR-06.6** The served app draws the same scheme colours as the saved page.
- **BR-06.7** Nothing is printed for a scheme that reads cleanly (DISCOVERY Q22).

## Technical requirements

- **TR-06.1** Add `@staticmethod SchemeParser._scheme_tokens(line: str) -> list[str]`
  immediately before `_parse_lines`: replace tabs with blanks; scan left to right; a token is
  a compound-quoted string `\`"…"'`, a double-quoted string `"…"` (an unclosed one reads to
  the end of the line), or a run of non-blank characters; each quoted token is returned with
  its quotes removed and its inner whitespace runs collapsed to one blank (`" ".join(s.split())`,
  which is how `"  0 255   0"` reaches `translate_mcolor` as `0 255 0`). Bounded by the line's
  length; no regex backtracking on user text (a single pass with an index).
- **TR-06.2** `_parse_lines` (:3941-3998): `line = raw_line.replace("\t", " ").strip()`;
  skip `""`, `line.startswith("*")` (covers `*!`) and `line.startswith("//")`; the `#include`
  block stays as it is; then `tokens = self._scheme_tokens(line)`; if `tokens[0] in
  ("sequence", "label")`: `continue`; if `len(tokens) < 2`: warn per TR-06.4 and `continue`;
  if `len(tokens) == 2`: `props[tokens[0]] = tokens[1]`; else `props[tokens[0] + " " +
  tokens[1]] = tokens[2]`. The `subcats` join and `tokens[-1]` go. A `#include` line with no
  name (`len(parts) != 2`, :3961-3962) is also an unreadable line and warns the same way.
- **TR-06.3** The value stored is the stripped, collapsed token; `_color`/`_color_alpha`
  are unchanged and now succeed on `26 71 111`, `26 71 111 %20` and `0 255 0%50`.
- **TR-06.4** The warning (F-10): `warnings.warn(f"dash scheme: line {lineno} of
  '{self._safe_name(os.path.basename(path))}' is not a `styletype element style' directive
  and was skipped: {self._safe_name(line)}", UserWarning, stacklevel=3)`, counted in
  `_notes["\0badlines"]`; the first `self._MAX_INCLUDE_NOTES` (10) are printed, the eleventh
  prints once "dash scheme: more lines in '<bounded basename>' could not be read; no more are
  noted", and none after. `lineno` comes from `enumerate(lines, 1)`. The path comes from the
  user's `scheme()` option through `_resolve_path`, so its basename is user text and is
  bounded like the line.
- **TR-06.5** Security (rule 1): the echoed text and the file's basename pass `_safe_name`
  (printable, ≤ 80 characters); no scheme value reaches HTML or JS except through
  `translate_mcolor` and the existing readers; the tokeniser never evaluates text.
- **TR-06.6** New test module `test/test_scheme_quoted_values.py` (stubs below) with a
  helper `_write_scheme(tmp_path, name="myquoted")` that copies `schemes/s1rcolor.scheme` to
  `tmp_path / f"{name}.scheme"` (the working-directory form dash.sthlp:2813 documents)
  and, in that copy, replaces the `color background` line with `color background "255 0 0"`
  and appends the lines `color p1 "26 71 111 %20"`, `color p2 "0 255 0%50"`, `color p3 "0 0
  255` (an unclosed quote: reads to the end of the line), `label "written by the test"`, and
  `color\tp4\t"1 2 3"` (tab-separated); it returns the path. The regression tests read that
  file (D13: no third-party file is copied or read). The before/after snapshot test carries
  the old six-line reader verbatim as a local function `_old_parse(path)` and compares it
  with the new reader over `schemes/*.scheme`.
- **TR-06.7** `test/function_test_map.py` gains, in alphabetical place beside
  `SchemeParser._safe_name` (rule R2),
  `'SchemeParser._scheme_tokens': 'test/test_scheme_quoted_values.py::TestTheTokeniserIsStatas::test_a_quoted_value_is_one_token'`.
- **TR-06.8** No third-party sweep (D13/Q30): no test reads Stata's PLUS directory, and no
  environment variable gates a test in this module.
- **TR-06.9** Certification (D11; no new script): `test/test_custom_scheme.cscript` gains
  CQ-01..CQ-03 after CS-15 and before its restore/cleanup section (:553), built on the
  script's own scaffolding: a second Mata function `_cs_write_quoted(src, dst, bgline,
  extra)` beside `_cs_write_theme` (:104-127; the existing function and its callers are
  untouched) that copies `src` to `dst`, replaces the `color background` line with `bgline`
  when `bgline` is not empty and appends `extra` when it is not empty; the files
  `myquoted.scheme` (`color background      "255 0 0"`), `myquoted50.scheme` (`color
  background      "255 0 0 %50"`) and `myp1.scheme` (s1rcolor plus an appended `color p1
  "31 119 180"`) written into `cs_dir`; the cases through `_cs_run`, `_cs_log`, `_cs_page`,
  `_cs_expect`, `_cs_done` (`CQ-01 PASS: ...`); the header's case list (:35-60) extended with
  CQ-01..CQ-03; the cleanup `foreach` (:556) extended with `q1.html q2.html q3.html
  myquoted.scheme myquoted50.scheme myp1.scheme`. The runner already registers the script;
  the hygiene pins are untouched (rule R1).
- **TR-06.10** BUGS.md: one closed entry for D1 appended at the END of the file (D3) with
  `- Resolution: Fixed <ddmonyyyy> (WP-28, D1). <what changed>. Pinned by
  test/test_scheme_quoted_values.py::TestQuotedValuesAreRead::test_a_scheme_written_with_quoted_values_is_read,
  ::TestQuotedValuesAreRead::test_both_modes_draw_the_quoted_background_and_p1,
  ::TestTheTokeniserIsStatas::test_a_quoted_value_is_one_token,
  ::TestUnreadableLinesWarnOnceEach::test_each_bad_line_is_named_with_its_number_then_the_bound_holds,
  ::TestShippedSchemesParseAsBefore::test_every_shipped_scheme_gives_the_old_props_minus_label_and_sequence,
  test/test_custom_scheme.cscript CQ-01..CQ-03. Residual, deferred (WP-28): hsv, CMYK and
  colour*# scheme values are D7's (GAPS2 D7), not read here.`; CHANGELOG: the marker
  `<!-- WP-28 D1 -->` (in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of
  `### Results that change`, placed by S01) is replaced in place by one line ending
  `(WP-28, D1)` naming the command, the old value (the scheme's own `color background` and
  `color p` defaults drawn, `#1e2d53` and s1rcolor's `color p` for the test-written file, as
  06-01 recorded) and the new (`#ff0000`, `#1a476f` at 0.2); dash.sthlp's scheme paragraph
  (:2804-2814) gains the grammar sentence; ROADMAP.md:2039-2041's WP-16 note is left as
  history (S19 updates GAPS2's Tracked line).

## Boundaries

- `hsv h s v`, CMYK `"c m y k"` and `colour*#` intensity values are **D7's** and out of
  scope: a scheme declaring them still gets `_color`'s "not a colour dash recognises" warning
  and the default; do not extend `translate_mcolor` here. Recorded as the D1 entry's
  residual (PRD §7; S19's deferred list).
- Third-party scheme files are out of scope by decision (DISCOVERY Q30, review D13): no
  sweep of Stata's PLUS directory, no copied third-party fixture, no SVG comparison under a
  third-party scheme, no test or task naming one.
- Do not change `#include` resolution, `_resolve_path`, `_include`'s fallback to s2color, the
  three include bounds, or `_FALLBACK_PROPS` (:3463).
- Do not change `_color`, `_color_alpha`, `_init_properties` or the p# chain.
- Do not read schemes from PLUS (dash.sthlp:2808-2814; X5 out of scope).
- Do not change the served template; `_SCHEME_PROPS` carries the fix.
- Keep `line.startswith("*")` and `line.startswith("//")` as the comment rule. Stata compares
  the first *token* (`*foo` is not a comment there); dash's superset has been its behaviour
  since the parser was written and no shipped or measured scheme depends on the difference.
  Record this in the tokeniser's docstring; do not narrow it.
- Do not print anything for a scheme that reads cleanly (DISCOVERY Q22).
- Do not create a `.cscript` file, and do not edit `test/run_all_cscripts.do` or
  `test/test_cscript_hygiene.py` (D11; rule R1); do not touch the existing CS-01..CS-15 cases.

## Stata truth

None new from an extract script. The reading rule is Stata's own `scheme.class:189-226`, its
documented forms are in `colorstyle.sthlp:221-240` and `scheme_files.sthlp:121-130`, and
`test/fixtures/scheme_truth.json` (from `scripts/extract_scheme_truth.py`, third-token
reading) already pins sttrans's `"26 71 111 %20"` as `#1a476f` at opacity 0.2. No fixture is
added, so no `git add -f` and no `_meta` stamp is needed.

The one Stata run of the section (06-03) is `test/test_custom_scheme.cscript` alone, through
the two-line driver of `sections/BRIEF.md` "Running one cscript" (`<repo>` =
`/Users/billy/Desktop/Programs/StataPrograms/d/dash`):

```
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_custom_scheme.cscript" > /tmp/dash-s06/run_test_custom_scheme.do
scripts/stata_slot.sh /tmp/dash-s06 /tmp/dash-s06/run_test_custom_scheme.do
```

(log `/tmp/dash-s06/run_test_custom_scheme.log`; the wrapper implements CLAUDE.md rule 10,
sets `STATATMP=/tmp/dash-s06/tmp/` and caps concurrent Stata sessions at three; never the
GUI).

## TDD test stubs

The first three are the regression tests that fail at 91d97be. All live in
`test/test_scheme_quoted_values.py` unless a file is named; they read the file
`_write_scheme(tmp_path)` writes (TR-06.6).

- **Test: `TestQuotedValuesAreRead::test_a_scheme_written_with_quoted_values_is_read`**:
  `sp = dr.SchemeParser.__new__(dr.SchemeParser)`; `props = sp._parse_file(_write_scheme(
  tmp_path), set())` under `warnings.catch_warnings(record=True)`; assert `props["color
  background"] == "255 0 0"`, `props["color p1"] == "26 71 111 %20"`, `props["color p2"] ==
  "0 255 0%50"`, `props["color p3"] == "0 0 255"` (the unclosed quote read to the end of the
  line), `props["color p4"] == "1 2 3"` (the tab-separated line), no key starts with `label`,
  no key contains `"`, and zero warnings. Then the parser rebuilt from `props`
  (`_props_scheme`, the `test_scheme_resolution.py:574-581` pattern) has `background_color
  == "#ff0000"`, `p_colors[:2] == ["#1a476f", "#00ff00"]` and `p_alphas[:2] == [0.2, 0.5]`.
  Pre-fix failure: `KeyError: 'color background'` (the key is `color background "255 0`).
- **Test: `TestQuotedValuesAreRead::test_both_modes_draw_the_quoted_background_and_p1`**
  (both modes): `monkeypatch.chdir(tmp_path)`; `_write_scheme(tmp_path)` (the
  working-directory form dash.sthlp documents); saved: a scatter spec with `build_options
  {"scheme": "myquoted"}` through `dr.DashRenderer(sp, dp)` — assert
  `renderer.scheme.background_color == "#ff0000"`, `renderer.scheme.p_colors[0] == "#1a476f"`
  and the scatter glyph's `fill_color` is `#1a476f`; served:
  `test_server_scheme._build_doc(tmp_path, {"scheme": "myquoted"})` and
  `_first_glyph_colour(doc) == "#1a476f"`; also import the built app module and assert
  `_SCHEME_PROPS["color p1"] == "26 71 111 %20"`. Pre-fix: s1rcolor's own background
  (`#1e2d53`) and its `color p` default in both; record the two colours the failing run
  prints (Q24: the CHANGELOG's old value).
- **Test: `TestQuotedValuesAreRead::test_a_quoted_rgb_with_opacity_reaches_the_alpha_reader`**:
  a temp scheme of three lines, `color p1 "26 71 111 %20"`, `color p2 "0 255 0%50"`, `color
  background "  0 255   0"`; through `_props_scheme`: `p_colors[:2] == ["#1a476f",
  "#00ff00"]`, `p_alphas[:2] == [0.2, 0.5]`, `background_color == "#00ff00"`, and zero
  warnings. Pre-fix: KeyError.
- **Test: `TestTheTokeniserIsStatas::test_a_quoted_value_is_one_token`** (rule 3, the new
  function): `_scheme_tokens('color p1 "31 119 180"') == ["color", "p1", "31 119 180"]`.
  Pre-fix: `AttributeError`.
- **Test: `TestTheTokeniserIsStatas::test_tabs_compound_quotes_and_an_unclosed_quote`**:
  `"color\tp1\t\"1 2 3\""` → three tokens; `"special fpfmt_es `\"%6.2f\"'"` →
  `["special", "fpfmt_es", "%6.2f"]`; `'color background "255 0 0'` → `["color",
  "background", "255 0 0"]` (reads to end of line); `'symbolsize p small *medium'` →
  four tokens and `_parse_lines` stores `small`.
- **Test: `TestTheReaderSkipsWhatStataSkips::test_comment_sequence_and_label_lines_store_nothing`**:
  a file of `* c`, `*! v`, `// c`, `sequence 1210`, `label "x y"`, `color p1 navy` → props
  `{"color p1": "navy"}` exactly, no warning. Pre-fix: `sequence` and `label "x` keys.
- **Test: `TestTheReaderSkipsWhatStataSkips::test_a_two_token_line_is_a_class_default_and_a_fourth_token_is_ignored`**:
  `intensity full` → `{"intensity": "full"}`; `color p1 red blue` → `{"color p1": "red"}`.
- **Test: `TestUnreadableLinesWarnOnceEach::test_each_bad_line_is_named_with_its_number_then_the_bound_holds`**:
  a file with twelve one-token lines (`junk1` … `junk12`) and `#include` with no name;
  `warnings.catch_warnings(record=True)`: exactly eleven warnings, the first ten naming
  `line N of 'x.scheme'` in order, the eleventh the "no more are noted" text; `props == {}`;
  a bad line of 500 non-printable characters is echoed as at most 80 printable ones; a file
  whose basename is 200 characters of which 100 are non-printable is named by at most 80
  printable characters (F-10).
- **Test: `TestShippedSchemesParseAsBefore::test_every_shipped_scheme_gives_the_old_props_minus_label_and_sequence`**
  (parametrised over the 20 files of `schemes/`): `new = sp._parse_file(path, set())` with
  warnings recorded; `old = _old_parse(path)` (the verbatim :3990-3998 loop over the file,
  ignoring `#include` lines in both readers by parsing with a `_visited` that pre-contains
  every resolved include — simplest: compare only the keys the file itself writes, by
  reading the file with the include lines removed into a temp copy for both readers); assert
  `{k: v for k, v in old.items() if not (k == "sequence" or k.startswith("label"))}` equals
  `new` after stripping quotes from old values, and that zero warnings were recorded. Passes
  before and after (it is the safety net, not a regression test).
- **Cscript: `test/test_custom_scheme.cscript`** CQ-01 `myquoted.scheme` (s1rcolor with
  `color background "255 0 0"`): `dash scatter mpg weight, scheme(myquoted) saving(q1.html,
  replace)` rc 0, no `UserWarning` in the log, `q1.html` carries `#ff0000`; CQ-02 the same
  with `myquoted50.scheme` (`color background "255 0 0 %50"`) into `q2.html`: `#ff0000`
  present, no warning; CQ-03 `myp1.scheme` (s1rcolor plus an appended `color p1 "31 119
  180"` line) into `q3.html`: `#1f77b4` present. Pre-fix: CQ-01 and CQ-02 pages carry
  s1rcolor's own background and not `#ff0000`.

**Pinned tests to flip:** none expected. Candidates to re-run and flip with a reason if a
warning count changes: `test/test_scheme_consumption.py::TestAnIncludeIsSplicedWhereItStands`,
`test/test_scheme_coercion.py::TestParseFile`, `test/test_scheme.py`,
`test/test_scheme_review_fixes.py`, `test/test_custom_scheme.cscript` CS-10..CS-12.

**Mutation table — proof the tests are not vacuous.** Apply, confirm the named test fails,
revert:

| break this | test that must die |
|---|---|
| in `_scheme_tokens`, split on whitespace only | `test_a_quoted_value_is_one_token`, `test_a_scheme_written_with_quoted_values_is_read` |
| keep the quotes on the token | `test_a_quoted_rgb_with_opacity_reaches_the_alpha_reader` (`parse_color_alpha` returns `(None, None)`) |
| take `tokens[-1]` again | `test_a_two_token_line_is_a_class_default_and_a_fourth_token_is_ignored` (`blue`) |
| stop skipping `label`/`sequence` | `test_comment_sequence_and_label_lines_store_nothing`, `test_every_shipped_scheme_gives_the_old_props_minus_label_and_sequence` |
| read an unclosed quote as one word | `test_a_scheme_written_with_quoted_values_is_read` (`color p3`) |
| store a bad line under its first token | `test_each_bad_line_is_named_with_its_number_then_the_bound_holds` (`props != {}`) |
| drop the `_MAX_INCLUDE_NOTES` bound | the same test (twelve warnings, not eleven) |
| echo the raw line or the raw basename in the warning | the same test (the 500-character echo; the 200-character name) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| A test-written scheme with quoted RGB, %opacity, an unclosed quote, a `label` line and a tab line is read | pytest | temp scheme (copy of `schemes/s1rcolor.scheme`) | saved (`_parse_file`, `p_colors`) and served (`_SCHEME_PROPS`, `_first_glyph_colour`) |
| `"R G B %NN"` and `"R G B%NN"` carry opacity | pytest | temp scheme | parser (shared by both) |
| Tokeniser contract (tabs, compound, unclosed, fourth token) | pytest | none | n/a |
| Comment/sequence/label skipped; two-token default | pytest | temp scheme | parser |
| Unreadable lines: named, numbered, bounded, not stored, echo and name bounded | pytest | temp scheme | parser |
| 20 shipped schemes parse as before, no warning | pytest (snapshot) | schemes/*.scheme | parser |
| Page built by dash from a quoted scheme carries `#ff0000` / `#1f77b4` | cscript CQ-01..03 in `test_custom_scheme.cscript` | s1rcolor copies | saved page |
| Served names / function map | pytest `TestTheServedAppCarriesEveryName`, `test_function_test_map.py` | none | served |
| Full suite once in the worktree | `python3 -m pytest test/ -q` | all | both |

Acceptance criteria:

- **AC-06.1** The test-written scheme parses to `color background`, `color p1`, `color p2`,
  `color p3` and `color p4` equal to its quoted strings, and `background_color`/`p_colors`
  to `#ff0000`/`#1a476f`, in both modes; before the fix the keys are absent.
- **AC-06.2** `"26 71 111 %20"` gives `#1a476f` at 0.2 and `"0 255 0%50"` gives `#00ff00` at
  0.5 through the parser.
- **AC-06.3** Every shipped scheme's props equal the old reader's minus `label`/`sequence`
  keys, with zero warnings.
- **AC-06.4** A file of twelve unreadable lines yields eleven bounded warnings naming file and
  line, and an empty props dict; a hostile basename is bounded to 80 printable characters.
- **AC-06.5** `test_custom_scheme.cscript` passes CS-01..CS-15 and CQ-01..CQ-03 through the
  driver and the wrapper; no new script, runner block or pin.
- **AC-06.6** The full pytest suite is green once in the worktree before the section's one
  commit on `wp28-s06` (subject ending `(GAPS2 D1)`), with nothing skipped for this section.
- **AC-06.7** BUGS.md holds the closed D1 entry at its end, `- Resolution: Fixed <ddmonyyyy>
  (WP-28, D1). ...`, naming its tests and the D7 residual; the `<!-- WP-28 D1 -->` marker is
  replaced in place by a line ending `(WP-28, D1)` and `grep -c '<!-- WP-28 D1 -->'
  CHANGELOG.md` prints 0; dash.sthlp updated.

## Tasks

Commit boundary: **one commit (D1)** holding 06-01 to 06-04, made by 06-04 on the worktree branch `wp28-s06`, subject ending `(GAPS2 D1)`, body per S01 TR-01.9 opening with the saved failure text; the full pytest suite runs green once in the worktree before it (CLAUDE.md rules 4 and 11); the merger lands the commit onto `s3-bugs` with that message (`sections/index.md` step 1). No task before 06-04 commits. The one Stata run (06-03) goes through `scripts/stata_slot.sh` with the two-line driver under "Stata truth" (D6). No full cert-suite run here (S19). No AI references anywhere.

<task type="auto" id="06-01">
  <name>Write the failing quoted-scheme tests</name>
  <files>test/test_scheme_quoted_values.py</files>
  <action><![CDATA[
    Create `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_scheme_quoted_values.py` with tests only: a module docstring stating the defect (a scheme line `color p1 "31 119 180"` was stored under the key `color p1 "31 119`, so the value was lost without a warning and the scheme's `color p` default drew instead; third-party scheme files are out of scope, DISCOVERY Q30, so the tests read a file they write themselves), the header block of `test/test_scheme_resolution.py` with `_props_scheme` copied (:574-581), `from test_server_scheme import _build_doc, _first_glyph_colour`, and the helper `_write_scheme(tmp_path, name="myquoted")` of TR-06.6 (copy `schemes/s1rcolor.scheme`, replace its `color background` line, append the five lines: `color p1 "26 71 111 %20"`, `color p2 "0 255 0%50"`, `color p3 "0 0 255`, `label "written by the test"`, the tab-separated `color\tp4\t"1 2 3"`). Write every stub in "TDD test stubs" with exactly those names, including `_old_parse` for the snapshot class; no environment-gated test, no PLUS directory, no copied third-party file (D13). Run the file against the unmodified tree. Do not commit: save the failure summary to the scratch directory as `06-01-failure.txt` -- `KeyError: 'color background'` for the headline, the two colours the both-modes test prints (s1rcolor's `#1e2d53` background and its `color p` default) for the CHANGELOG's old value (Q24), `AttributeError` for the tokeniser -- while the snapshot class passes (it is the safety net); it becomes the opening paragraph of the D1 commit (S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_scheme_quoted_values.py -q 2>&1 | tail -20` shows the `TestShippedSchemesParseAsBefore` cases passing and every other test failing, with `grep -c "KeyError: 'color background'"` on the output non-zero; `grep -c "DASH_LOCAL_SCHEMES\|plus/s\|d3" test/test_scheme_quoted_values.py` prints 0; `git status --short` lists exactly the new test file; `<scratch>/06-01-failure.txt` exists and holds the two pre-fix colours.]]></verify>
  <done>A new test module that writes its own quoted scheme collected cleanly with every regression test failing for the recorded reason and the shipped-scheme snapshot passing, no third-party file was touched, and nothing was committed.</done>
</task>

<task type="auto" id="06-02">
  <name>Read scheme lines as Stata's scheme.class does</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py` add `@staticmethod def _scheme_tokens(line)` immediately before `_parse_lines` (:3941) per TR-06.1, with a docstring citing scheme.class:189-226 (`tokenize`, `args style id stylename`), `scripts/extract_scheme_truth.py:207-262` as the earlier reading, the measured `symbolsize p small *medium` → `small`, and the comment-rule note of Boundaries. Rewrite the tail of `_parse_lines` (:3990-3998) and its comment-skip line (:3955) per TR-06.2 and TR-06.4: tabs to blanks, `//` skipped, `enumerate(lines, 1)` for line numbers, `sequence`/`label` skipped, the bounded warning through `_notes` and `_safe_name` on both the echoed line and `os.path.basename(path)` (F-10), two-token class defaults, third-token values, later tokens ignored, and the nameless `#include` warned the same way. Update `_parse_lines`'s docstring and the class docstring paragraph on the file grammar (about :3383-3400) to say the value is the third token with quotes removed. Add the function-map entry of TR-06.7 to `test/function_test_map.py` beside `SchemeParser._safe_name` (:242), alphabetical place. Line numbers are pre-edit; locate by symbol.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_scheme_quoted_values.py test/test_scheme_coercion.py test/test_scheme_consumption.py test/test_scheme.py test/test_scheme_fidelity.py test/test_scheme_resolution.py test/test_scheme_review_fixes.py test/test_server_scheme.py test/test_function_test_map.py test/test_statistical_helpers.py -q 2>&1 | tail -5` reports no failures; `python3 -c "import dash_render as d;print(d.SchemeParser._scheme_tokens('color p1 \"31 119 180\" extra'))"` prints `['color', 'p1', '31 119 180', 'extra']`; `grep -n 'tokens\[-1\]' dash_render.py | grep -v textbox` prints nothing in `SchemeParser`; `grep -c "_safe_name(os.path.basename(path))" dash_render.py` prints at least 1.]]></verify>
  <done>SchemeParser read a directive's value as Stata's third token with quotes stripped, skipped what Stata skips, named each unreadable line once with a bounded file name under the include-note bound, and every test of 06-01 and every existing scheme test passed.</done>
</task>

<task type="auto" id="06-03">
  <name>Certify a quoted scheme through dash.ado</name>
  <files>test/test_custom_scheme.cscript</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_custom_scheme.cscript` add, beside `_cs_write_theme` in the Mata block (:104-127), the function `_cs_write_quoted(string scalar src, string scalar dst, string scalar bgline, string scalar extra)` of TR-06.9 (copy, replace the `color background` line with `bgline` when non-empty, append `extra` when non-empty; return the number of lines replaced), leaving `_cs_write_theme` and every existing case untouched. After CS-15 and before the restore/cleanup section (:553) add CQ-01..CQ-03 per the stub: write `myquoted.scheme`, `myquoted50.scheme` and `myp1.scheme` into `cs_dir` with `_cs_write_quoted`, then `dash scatter mpg weight, scheme(myquoted) saving(q1.html, replace)` through `_cs_run`, `_cs_expect CQ-01 "(\`rc' == 0)" ...`, `_cs_log CQ-01 "\`lg'" "UserWarning" 0`, `_cs_page CQ-01 "q1.html" "#ff0000" 1`, `_cs_done CQ-01 "..."`; CQ-02 the same with `myquoted50` into `q2.html`; CQ-03 with `myp1` into `q3.html` and `#1f77b4`. Extend the header's case list (:35-60) with the three cases and the cleanup `foreach` (:556) with `q1.html q2.html q3.html myquoted.scheme myquoted50.scheme myp1.scheme`. No new script, no runner or pin edit (D11, rule R1). Run the script alone through the driver `/tmp/dash-s06/run_test_custom_scheme.do` and the wrapper ("Stata truth") and read `/tmp/dash-s06/run_test_custom_scheme.log`.
  ]]></action>
  <verify><![CDATA[`grep -c "CQ-0[1-3] PASS" /tmp/dash-s06/run_test_custom_scheme.log` prints 3, `grep -c "CS-[0-9]* PASS" /tmp/dash-s06/run_test_custom_scheme.log` prints 15, the log ends with `test_custom_scheme: ALL CHECKS PASSED` and `grep -c '^r([0-9]*);' /tmp/dash-s06/run_test_custom_scheme.log` prints 0; `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -3` passes with its pins untouched; `git diff --stat -- test/run_all_cscripts.do test/test_cscript_hygiene.py` prints nothing.]]></verify>
  <done>The existing custom-scheme certification script proved through dash.ado that a working-directory scheme written with Stata's quoted RGB, with and without %opacity, drew its declared background and p1 colour with no warning, and its fifteen earlier cases still passed.</done>
</task>

<task type="auto" id="06-04">
  <name>Close D1 in the tracking documents</name>
  <files>BUGS.md, CHANGELOG.md, dash.sthlp</files>
  <action><![CDATA[
    Append at the end of `/Users/billy/Desktop/Programs/StataPrograms/d/dash/BUGS.md` (S01 TR-01.8; never mid-file) the closed entry `- [x] Title: A scheme's quoted values (RGB colours, %opacity) were dropped without a warning` with File Names and Line Numbers (`dash_render.py SchemeParser._parse_lines (tokens[-1] as the value)`), Description (GAPS2 D1's measured symptom: `color background "255 0 0"` stored under a malformed key; a copied scheme written with quoted RGB drawing every series in its `color p` default with 0 warnings; `label "s2 color"` stored under `label "s2` in every shipped scheme), Suggested fix (tokenise as scheme.class does: third token, quotes stripped, `sequence`/`label` skipped, one bounded warning per unreadable line), and the Resolution line of TR-06.10 verbatim, `- Resolution: Fixed <ddmonyyyy> (WP-28, D1). SchemeParser._parse_lines tokenises a line as scheme.class does (_scheme_tokens: a quoted or compound-quoted string is one token, quotes stripped, the third token is the value, sequence and label lines are skipped, an unreadable line is named once with its bounded file name and line number), in both renderers through _SCHEME_PROPS. Pinned by <the tests and cases TR-06.10 lists>. Residual, deferred (WP-28): hsv, CMYK and colour*# scheme values are D7's (GAPS2 D7), not read here.` (the title holds no `"`). In `CHANGELOG.md` replace the marker `<!-- WP-28 D1 -->` -- it sits in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of `### Results that change`, placed by S01 -- in place with one line ending `(WP-28, D1)`: a scheme file copied into the working directory that wrote its colours as Stata's schemes do, `color background "255 0 0"` or `color p1 "26 71 111 %20"`, lost every such directive without a warning and drew the scheme's own `color background` and `color p` defaults in its place (the two colours 06-01 recorded for the test-written file); the value is now read as Stata reads it, so such a scheme draws its declared colours and opacities (`#ff0000`; `#1a476f` at 0.2), and a line dash cannot read is named once with its line number. Add nothing anywhere else in CHANGELOG.md. In `dash.sthlp` extend the scheme paragraph (:2804-2814) after "Copy the file into the working directory instead." with: the file is read as Stata reads it, each line `styletype element style` with the style the third word, quoted when it holds blanks, as in `color background "255 0 0"` or `color p1 "26 71 111 %20"`; a line that cannot be read that way is named once, with its line number, and skipped. Run the full pytest suite once in the worktree, `python3 -m pytest test/ -q` (CLAUDE.md rules 4 and 11; the merger's `git merge --no-edit main` and pre-commit run are `sections/index.md` step 1); fix any regression in the code, never by weakening a test. Grep the three edits and the message draft for `claude` and `anthropic` (nothing may match). Commit the whole section as ONE commit on the worktree branch `wp28-s06`; the merger lands it onto `s3-bugs` with this message (`sections/index.md` step 1): subject ending `(GAPS2 D1)`, body opening with `<scratch>/06-01-failure.txt` and carrying the S01 TR-01.9 lines (`Regression:` per regression test with its KeyError/colour text; no `Flipped:` line unless a warning-count test moved, then one per flip; no `Fixture:` line; `BUGS.md: "A scheme's quoted values (RGB colours, %opacity) were dropped without a warning" (closed)`). The merge command into `main` is S19's to report; do not run any merge.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_1.py -q 2>&1 | tail -3` passes; `grep -n "quoted values (RGB colours, %opacity)" BUGS.md` finds the entry and `tail -12 BUGS.md | grep -c "Resolution: Fixed .* (WP-28, D1)"` prints 1; `grep -c '<!-- WP-28 D1 -->' CHANGELOG.md` prints 0 and `awk '/^### Results that change/{f=1;next} /^### /{f=0} f' CHANGELOG.md | grep -c '(WP-28, D1)'` prints 1; `grep -n '26 71 111 %20' CHANGELOG.md dash.sthlp` finds both; `python3 -m pytest test/ -q 2>&1 | tail -5` reports no failures; `git log -1 --format=%s | grep -c '(GAPS2 D1)'` prints 1; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0; `git rev-parse --abbrev-ref HEAD` prints `wp28-s06`; `git status --short` prints nothing.]]></verify>
  <done>D1 was recorded closed at the end of BUGS.md naming its tests and its D7 residual, the D1 marker was replaced in place by the line quoting the old and new colours, the help stated the scheme grammar dash reads, and one green commit on `wp28-s06` carried the whole section for the merger.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" exists and passes; the three regression tests are recorded
  as failing at 91d97be in the D1 commit's message (from `<scratch>/06-01-failure.txt`).
- `SchemeParser._scheme_tokens` exists and is named in `test/function_test_map.py`;
  `_parse_lines` no longer contains `tokens[-1]`; the warning's file name and echoed line
  pass `_safe_name`.
- No fixture was added; no third-party scheme file was read, copied or named; no
  environment-gated test exists in the module.
- `test/test_custom_scheme.cscript` passes CS-01..CS-15 and CQ-01..CQ-03 through the driver
  and the wrapper; no `.cscript` was created and neither the runner nor the hygiene pins
  changed.
- One commit on `wp28-s06`, subject ending `(GAPS2 D1)`, holding the failing tests, the fix,
  the cscript cases and the closed BUGS.md entry; no test-only commit exists (D1); the full
  suite was green once in the worktree before it.
- BUGS.md (D3 form, at the end, with the D7 residual clause), CHANGELOG.md (the D1 marker
  replaced in place, ending `(WP-28, D1)`) and dash.sthlp carry the D1 closure; no AI
  reference anywhere.
- No file outside the four tasks' file lists is modified.

## Notes

- **Compound quotes.** s2color's `special fpfmt_es \`"%6.2f"'` is a real line in a real
  scheme; the tokeniser must treat `\`"` … `"'` as one token and return `%6.2f`. dash's own
  translations may carry the same lines: the snapshot test's quote-stripping comparison
  (`old.strip('"\'\`') == new`) covers them.
- **The snapshot's `#include` handling.** `_parse_file` splices includes, so `old` and `new`
  would both contain s2color's keys; either compare only the keys the file writes itself
  (parse a temp copy with `#include` lines removed, through both readers) or pass a
  `_visited` pre-filled with every resolvable include's realpath. The first is simpler and is
  what the stub prescribes.
- **Warnings are per parse.** The `\0badlines` counter lives in `_notes`, the dict
  `_parse_file` creates per top-level parse and threads through `_include`; a scheme with
  bad lines in an included file counts against the same bound.
- **The test-written scheme.** `_write_scheme` copies a shipped file so the snapshot and the
  regression share one source of truth; the unclosed-quote line `color p3 "0 0 255` is a
  legal line for the reader (it reads to the end of the line) and must produce no warning;
  the `label` line must store nothing; the tab line must reach `color p4`.
- **Shared registries (rules R1-R6).** R1: no cscript is created; CQ-01..CQ-03 join
  `test_custom_scheme.cscript`, whose runner block and pins are untouched. R2: the
  `function_test_map.py` key goes beside `SchemeParser._safe_name`; the merger resolves
  append conflicts textually. R3: the D1 marker only, the help paragraph 2804-2814 only, the
  BUGS.md entry at the end. R4/R5/R6: no graph-key list, no fixture, no parity corpus edit.
- **Commit body** uses S01 TR-01.9's line forms verbatim: `Regression: test/<file>.py::<Class>::<test> -- failed at 91d97be with <text>` (one per regression test), `Flipped: <node> -- <old expectation> was wrong because <why>` (only if a warning-count test moved), `BUGS.md: "<title>" (closed)`; no `Fixture:` line. The commit is made on `wp28-s06` and landed on `s3-bugs` by the merger (`sections/index.md` step 1).
- **Stata's Python.** The cscript's `python:` blocks, if any, run under `c(python_exec)`;
  the wrapper keeps to three concurrent Stata sessions, and on a run of SKIPs check
  `c(python_exec)` before trusting them.
- **Stata invocation.** The one run is `test_custom_scheme.cscript` through the two-line
  driver of "Stata truth" (`sections/BRIEF.md` "Running one cscript"); never the GUI, never a
  bare `stata-mp`, never the full cert suite inside a section (S19).
- **Renderer order.** The scheme is parsed once at build time in both modes and the served
  app rebuilds it from `_SCHEME_PROPS`; there is no order difference to mind.
- **Line numbers drift.** `_scheme_tokens` adds about 40 lines before `_parse_lines`; every
  anchor in 06-02 is also a symbol, and the symbol is authoritative.
