# Section 06: Scheme quoted values (D1)

> Part of: WP-28 · Gaps: D1 · Risk: green · Batch: 1 · Depends on: none · Blocks: 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **1** · Depends on **none** · Blocks **19** · Risk **green** · Commits: one commit (D1) → CHANGELOG `Results that change`

- D10: warnings carry the scheme file's basename bounded to 80 characters; the CMYK/hsv/`colour*#` forms are a recorded residual (PRD §7, S19 deferred list).

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

dash.sthlp:2813 tells a user who wants another package's scheme to copy the file into the
working directory. Stata's own colorstyle help writes colours as `"255 0 0"`, and Stata's own
sttrans scheme writes `color p1 "26 71 111 %20"`. GAPS2 D1 measured what dash does with such
a file: "`SchemeParser._parse_lines` (dash_render.py:3988-3993) takes `tokens[-1]` as the
value, so `color background "255 0 0"` is stored under a malformed key and the directive is
lost without a warning. In a probe, a copied `scheme-d3colors.scheme` drew every series
#606060 with 0 warnings; 127 of the 129 local third-party schemes use quoted RGB." The same
reader stores every shipped scheme's `label "s2 color"` line under the key `label "s2`, keeps
`sequence` lines Stata skips, and never strips a compound quote (`special fpfmt_es
\`"%6.2f"'` in s2color).

After this section `_parse_lines` reads a line the way Stata's `scheme.class` reads it
(:189-226): tabs become blanks, `*`, `//`, `*!`, `sequence` and `label` lines are skipped,
the line is tokenised so that a quoted string is one token (an unclosed quote reads to the end
of the line, as `_textbox_string_end` does for textboxes), the key is the first two tokens,
the value is the third with its quotes stripped, and later tokens are ignored; a two-token
line is a class default. `"R G B"`, `"R G B %NN"` and `"R G B%NN"` then reach
`translate_mcolor` and `parse_color_alpha`, which already accept the unquoted forms. A line
that cannot be read that way is named once, with its file and line number, under the same
bound `_include` uses for its notes, and nothing is stored under a malformed key. The served
app receives the parsed dict as `_SCHEME_PROPS` (:24708) and rebuilds the parser from it
(:24714-24720), so it inherits the fix with no template change.

D1 is alone in this section because it changes one method of `SchemeParser` and nothing else
in the renderer; `hsv`, CMYK and `colour*#` values are D7's shared work and stay out of scope.
The section is green: the reference tokeniser already exists in
`scripts/extract_scheme_truth.py`, the shipped schemes are unaffected by the switch, and a
before/after snapshot test proves it.

**Test order (CLAUDE.md rule 7): task 06-01 commits the d3colors fixture and writes every
failing test; task 06-02 makes them green; 06-03 certifies through dash.ado; 06-04 records
the closure; 06-05 is the optional SVG comparison.**

## Risk: [green] — a tokeniser change in one method, checked against every shipped scheme before and after

- **Why.** The rule is Stata's own and already implemented once in this repository; the
  change cannot alter any shipped translation's drawn output, and a snapshot test says so.
- **Risk factors.** (1) A shipped translation might carry a line the new reader warns on
  (a stray one-token line), which would put a warning into every render and turn
  `test_custom_scheme.cscript` CS-11/CS-12 red. (2) A test that counts warnings on a
  hand-written scheme with junk lines could gain a warning. (3) The PLUS sweep must never be
  a skip under `DASH_STRICT`.
- **Mitigation.** The snapshot test asserts zero warnings per shipped file; the warning tests
  are re-run and any changed count is flipped with its reason; the sweep is defined only when
  `DASH_LOCAL_SCHEMES=1` is set, so it is neither collected nor skipped otherwise.

## Dependencies

- **Depends on:** none.
- **Blocks:** 19.
- **Parallel batch:** 1.
- **Can run with:** every other batch-1 section. S06 edits `SchemeParser._parse_lines` and
  adds one static method beside it; no other section edits `SchemeParser`. S02 (the SVG
  helper) is batch 1 too, which is why the SVG comparison here is optional (task 06-05).

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
printable characters.

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
  \`color p1 26 71 111 %20'`), which is why sttrans works today.
- Local third-party schemes: `~/Library/Application Support/Stata/ado/plus/s/scheme-*.scheme`,
  129 files, 127 with quoted RGB. `scheme-d3colors.scheme` is 3701 lines, has **no
  `#include`**, `label "d3colors"` at :26, `color p gs6` at :300 and `color p1 "31 119 180"`
  … `color p15 "127 127 127"` at :301-315. It is self-contained, so a verbatim copy parses
  identically anywhere. `.git/info/exclude` hides `*.json`/`*.csv`/`*.schema`, not
  `*.scheme`, so the copy is staged with a plain `git add`.

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
  parse with zero warnings (TR-06.7).
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
- **US-06.2** As the Stata user pasting twoway syntax, I want `scheme(d3colors)` with the
  file in my working directory to draw d3colors' fifteen series colours in the saved page
  and the served app alike, so that the picture is the one Stata draws.
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
  number, at most ten per parse plus one summary line, and nothing is stored for it.
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
- **TR-06.4** The warning: `warnings.warn(f"dash scheme: line {lineno} of
  '{os.path.basename(path)}' is not a `styletype element style' directive and was skipped:
  {self._safe_name(line)}", UserWarning, stacklevel=3)`, counted in
  `_notes["\0badlines"]`; the first `self._MAX_INCLUDE_NOTES` (10) are printed, the eleventh
  prints once "dash scheme: more lines in '<file>' could not be read; no more are noted", and
  none after. `lineno` comes from `enumerate(lines, 1)`.
- **TR-06.5** Security (rule 1): the echoed text passes `_safe_name` (printable, ≤ 80
  characters); no scheme value reaches HTML or JS except through `translate_mcolor` and the
  existing readers; the tokeniser never evaluates text.
- **TR-06.6** New test module `test/test_scheme_quoted_values.py` (stubs below), and the
  fixture `test/fixtures/schemes/scheme-d3colors.scheme`, a verbatim copy of the local file
  (3701 lines; `color p1 "31 119 180"` at :301), named literally by the test module so
  `test_fixtures_are_committed.py` accepts it. The before/after snapshot test carries the
  old six-line reader verbatim as a local function `_old_parse(path)` and compares it with
  the new reader over `schemes/*.scheme`.
- **TR-06.7** `test/function_test_map.py` gains
  `'SchemeParser._scheme_tokens': 'test/test_scheme_quoted_values.py::TestTheTokeniserIsStatas::test_a_quoted_value_is_one_token'`.
- **TR-06.8** The PLUS sweep (`TestLocalThirdPartySchemesParse`) is defined inside `if
  os.environ.get("DASH_LOCAL_SCHEMES") == "1":` at module level, so without the variable no
  test exists to skip; with it, an absent directory is `pytest.fail`, not a skip. Documented in
  the module docstring as a local check outside the strict suite:
  `DASH_LOCAL_SCHEMES=1 python3 -m pytest test/test_scheme_quoted_values.py -k Local`.
- **TR-06.9** New `test/test_custom_scheme_quoted.cscript` (CQ-01..CQ-03) built from
  `test/test_custom_scheme.cscript`'s scaffolding (`_cs_write_theme` :104-127 generalised to
  take the replacement line, `_cs_run`, `_cs_log`, `_cs_page`, `_cs_expect`, `_cs_done`),
  registered in `test/run_all_cscripts.do` as block 67 in the :1087-1109 pattern.
- **TR-06.10** BUGS.md closed entry for D1; CHANGELOG under `### Results that change` /
  `**Colours, schemes and appearance**` (:113); dash.sthlp's scheme paragraph (:2804-2814)
  gains the grammar sentence; ROADMAP.md:2039-2041's WP-16 note is left as history (S19
  updates GAPS2's Tracked line).

## Boundaries

- `hsv h s v`, CMYK `"c m y k"` and `colour*#` intensity values are **D7's** and out of
  scope: a scheme declaring them still gets `_color`'s "not a colour dash recognises" warning
  and the default; do not extend `translate_mcolor` here.
- Do not change `#include` resolution, `_resolve_path`, `_include`'s fallback to s2color, the
  three include bounds, or `_FALLBACK_PROPS` (:3463).
- Do not change `_color`, `_color_alpha`, `_init_properties` or the p# chain.
- Do not read schemes from PLUS (dash.sthlp:2808-2814; X5 out of scope); the sweep reads the
  files directly through `_parse_file(path, set())` for the test only.
- Do not change the served template; `_SCHEME_PROPS` carries the fix.
- Keep `line.startswith("*")` and `line.startswith("//")` as the comment rule. Stata compares
  the first *token* (`*foo` is not a comment there); dash's superset has been its behaviour
  since the parser was written and no shipped or measured scheme depends on the difference.
  Record this in the tokeniser's docstring; do not narrow it.
- Do not print anything for a scheme that reads cleanly (DISCOVERY Q22).
- The SVG comparison (task 06-05) runs only if S02's `test/cert_svg.do` exists; otherwise
  it is deferred to S19 and nothing is written for it.

## Stata truth

None new from an extract script. The reading rule is Stata's own `scheme.class:189-226`, its
documented forms are in `colorstyle.sthlp:221-240` and `scheme_files.sthlp:121-130`, and
`test/fixtures/scheme_truth.json` (from `scripts/extract_scheme_truth.py`, third-token
reading) already pins sttrans's `"26 71 111 %20"` as `#1a476f` at opacity 0.2. The optional
SVG comparison (06-05) would export `sysuse auto; twoway scatter mpg weight, scheme(d3colors)`
to SVG through S02's helper and read the marker fill `#1f77b4`; it needs the copied scheme
on Stata's ado-path (`adopath + <dir>` holding `scheme-d3colors.scheme`) and the invocation
`cd <dir> && STATATMP=<dir>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do <file>.do`. No
fixture is added, so no `git add -f` is needed; the `.scheme` fixture of TR-06.6 is not
excluded by `.git/info/exclude`.

## TDD test stubs

The first three are the regression tests that fail at 91d97be. All live in
`test/test_scheme_quoted_values.py` unless a file is named.

- **Test: `TestQuotedValuesAreRead::test_d3colors_p1_to_p15_are_the_files_rgb_values`**:
  `sp = dr.SchemeParser.__new__(dr.SchemeParser)`; `props = sp._parse_file(_D3, set())`
  (`_D3 = test/fixtures/schemes/scheme-d3colors.scheme`); assert `props["color p1"] == "31
  119 180"` … `props["color p15"] == "127 127 127"` (the fifteen strings from :301-315,
  listed in the test), `props["color p"] == "gs6"`, and no key contains `"`. Then the parser
  rebuilt from `props` (`_props_scheme`, the `test_scheme_resolution.py:574-581` pattern)
  has `p_colors == ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a",
  "#d62728", "#ff9896", "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", "#e377c2", "#f7b6d2",
  "#7f7f7f"]` and `p_alphas == [None]*15`. Pre-fix failure: `KeyError: 'color p1'` (the key
  is `color p1 "31 119`).
- **Test: `TestQuotedValuesAreRead::test_both_modes_draw_d3colors_p1`** (both modes):
  `monkeypatch.chdir(tmp_path)`; copy the fixture to `tmp_path/"d3colors.scheme"` (the
  working-directory form dash.sthlp documents); saved: a scatter spec with `build_options
  {"scheme": "d3colors"}` through `dr.DashRenderer(sp, dp)` — assert
  `renderer.scheme.p_colors[0] == "#1f77b4"` and the scatter glyph's `fill_color`; served:
  `test_server_scheme._build_doc(tmp_path, {"scheme": "d3colors"})` and
  `_first_glyph_colour(doc) == "#1f77b4"`; also import the built app module and assert
  `_SCHEME_PROPS["color p1"] == "31 119 180"`. Pre-fix: the gs6 grey in both.
- **Test: `TestQuotedValuesAreRead::test_a_quoted_rgb_with_opacity_reaches_the_alpha_reader`**:
  a temp scheme with `color p1 "26 71 111 %20"`, `color p2 "0 255 0%50"`, `color background
  "  0 255   0"`; through `_props_scheme`: `p_colors[:2] == ["#1a476f", "#00ff00"]`,
  `p_alphas[:2] == [0.2, 0.5]`, `background_color == "#00ff00"`, and zero warnings. Pre-fix:
  KeyError.
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
  a bad line of 500 non-printable characters is echoed as at most 80 printable ones.
- **Test: `TestShippedSchemesParseAsBefore::test_every_shipped_scheme_gives_the_old_props_minus_label_and_sequence`**
  (parametrised over the 20 files of `schemes/`): `new = sp._parse_file(path, set())` with
  warnings recorded; `old = _old_parse(path)` (the verbatim :3990-3998 loop over the file,
  ignoring `#include` lines in both readers by parsing with a `_visited` that pre-contains
  every resolved include — simplest: compare only the keys the file itself writes, by
  reading the file with the include lines removed into a temp copy for both readers); assert
  `{k: v for k, v in old.items() if not (k == "sequence" or k.startswith("label"))}` equals
  `new` after stripping quotes from old values, and that zero warnings were recorded. Passes
  before and after (it is the safety net, not a regression test).
- **Test: `TestLocalThirdPartySchemesParse::test_no_local_scheme_yields_a_malformed_key`**
  (defined only under `DASH_LOCAL_SCHEMES=1`): for every `scheme-*.scheme` in the PLUS `s/`
  directory, `_parse_file(path, set())` under `warnings.catch_warnings()`; assert no key
  contains `"` or `` ` ``, and that at least 100 files were read; `pytest.fail` if the
  directory is absent.
- **Cscript: `test/test_custom_scheme_quoted.cscript`** CQ-01 `myquoted.scheme`
  (s1rcolor with `color background "255 0 0"`): `dash scatter mpg weight, scheme(myquoted)
  saving(q.html, replace)` rc 0, no `UserWarning` in the log, `q.html` carries `#ff0000`;
  CQ-02 the same with `color background "255 0 0 %50"`: `#ff0000` present, no warning; CQ-03
  s1rcolor plus an appended `color p1 "31 119 180"` line: `#1f77b4` present. Pre-fix: CQ-01
  and CQ-02 pages carry s1rcolor's own background and not `#ff0000`.

**Pinned tests to flip:** none expected. Candidates to re-run and flip with a reason if a
warning count changes: `test/test_scheme_consumption.py::TestAnIncludeIsSplicedWhereItStands`,
`test/test_scheme_coercion.py::TestParseFile`, `test/test_scheme.py`,
`test/test_scheme_review_fixes.py`, `test/test_custom_scheme.cscript` CS-10..CS-12.

**Mutation table — proof the tests are not vacuous.** Apply, confirm the named test fails,
revert:

| break this | test that must die |
|---|---|
| in `_scheme_tokens`, split on whitespace only | `test_a_quoted_value_is_one_token`, `test_d3colors_p1_to_p15_are_the_files_rgb_values` |
| keep the quotes on the token | `test_a_quoted_rgb_with_opacity_reaches_the_alpha_reader` (`parse_color_alpha` returns `(None, None)`) |
| take `tokens[-1]` again | `test_a_two_token_line_is_a_class_default_and_a_fourth_token_is_ignored` (`blue`) |
| stop skipping `label`/`sequence` | `test_comment_sequence_and_label_lines_store_nothing`, `test_every_shipped_scheme_gives_the_old_props_minus_label_and_sequence` |
| store a bad line under its first token | `test_each_bad_line_is_named_with_its_number_then_the_bound_holds` (`props != {}`) |
| drop the `_MAX_INCLUDE_NOTES` bound | the same test (twelve warnings, not eleven) |
| echo the raw line in the warning | the same test (the 500-character echo) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| d3colors p1-p15 read as the file's RGB | pytest | fixtures/schemes/scheme-d3colors.scheme | saved (`_parse_file`, `p_colors`) and served (`_SCHEME_PROPS`, `_first_glyph_colour`) |
| `"R G B %NN"` and `"R G B%NN"` carry opacity | pytest | temp scheme | parser (shared by both) |
| Tokeniser contract (tabs, compound, unclosed, fourth token) | pytest | none | n/a |
| Comment/sequence/label skipped; two-token default | pytest | temp scheme | parser |
| Unreadable lines: named, numbered, bounded, not stored, echo bounded | pytest | temp scheme | parser |
| 20 shipped schemes parse as before, no warning | pytest (snapshot) | schemes/*.scheme | parser |
| 129 local schemes, no malformed key | pytest, `DASH_LOCAL_SCHEMES=1` only | machine-local PLUS | parser |
| Page built by dash from a quoted scheme carries `#ff0000` / `#1f77b4` | cscript | s1rcolor copy | saved page |
| Served names / function map | pytest `TestTheServedAppCarriesEveryName`, `test_function_test_map.py` | none | served |
| Scatter SVG under d3colors equals dash's p1 | cscript through `test/cert_svg.do` | none | optional (06-05) |
| Full suite, both interpreters | `python3 -m pytest test/ -q`; `make test` | all | both |

Acceptance criteria:

- **AC-06.1** The d3colors fixture parses to `color p1` … `color p15` equal to the file's
  RGB strings, and `p_colors` to the fifteen hex values, in both modes; before the fix the key
  is absent.
- **AC-06.2** `"26 71 111 %20"` gives `#1a476f` at 0.2 and `"0 255 0%50"` gives `#00ff00` at
  0.5 through the parser.
- **AC-06.3** Every shipped scheme's props equal the old reader's minus `label`/`sequence`
  keys, with zero warnings.
- **AC-06.4** A file of twelve unreadable lines yields eleven bounded warnings naming file and
  line, and an empty props dict.
- **AC-06.5** `test_custom_scheme_quoted.cscript` CQ-01..03 pass; `test_custom_scheme.cscript`
  CS-01..15 still pass.
- **AC-06.6** Full pytest green under both interpreters with nothing skipped for this
  section; `DASH_LOCAL_SCHEMES=1` run reads ≥ 100 local files with no malformed key.
- **AC-06.7** BUGS.md holds the closed D1 entry naming its tests; CHANGELOG and dash.sthlp
  updated.

## Tasks

<task type="auto" id="06-01">
  <name>Commit the d3colors fixture and the failing tests</name>
  <files>test/fixtures/schemes/scheme-d3colors.scheme (new), test/test_scheme_quoted_values.py (new)</files>
  <action>
    Copy `~/Library/Application Support/Stata/ado/plus/s/scheme-d3colors.scheme` verbatim to
    `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/fixtures/schemes/scheme-d3colors.scheme`
    (`mkdir -p` the directory; `wc -l` must print 3701 and `sed -n 301p` must print `color p1
    "31 119 180"`); stage it with `git add` (the `.scheme` extension is not in
    `.git/info/exclude`). Create `test/test_scheme_quoted_values.py` with tests only: a module
    docstring stating the defect (a copied `scheme-d3colors.scheme` drew every series in
    `color p`'s gs6 grey with no warning because `color p1 "31 119 180"` was stored under the
    key `color p1 "31 119`), the fixture's provenance (the d3colors package's file, its `*!`
    line, copied unchanged so its line numbers hold), and the `DASH_LOCAL_SCHEMES=1`
    instruction of TR-06.8; the header block of `test/test_scheme_resolution.py` with
    `_props_scheme` copied (:574-581), `from test_server_scheme import _build_doc,
    _first_glyph_colour`, and `_D3` as the fixture path named literally
    (`test_fixtures_are_committed.py` needs the literal). Write every stub in "TDD test
    stubs" with exactly those names, including `_old_parse` for the snapshot class and the
    env-gated `TestLocalThirdPartySchemesParse`. Run the file against the unmodified tree and
    paste the failure summary into the commit message: `KeyError: 'color p1'` for the
    headline, the gs6 colour for the both-modes test, `AttributeError` for the tokeniser,
    while the snapshot class passes (it is the safety net).
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && git ls-files test/fixtures/schemes/scheme-d3colors.scheme` prints the path; `python3 -m pytest test/test_scheme_quoted_values.py -q 2>&1 | tail -20` shows the `TestShippedSchemesParseAsBefore` cases passing and every other test failing, with `grep -c "KeyError: 'color p1'"` on the output non-zero; `python3 -m pytest test/test_fixtures_are_committed.py -q 2>&1 | tail -3` passes; `DASH_LOCAL_SCHEMES=1 python3 -m pytest test/test_scheme_quoted_values.py -q -k Local 2>&1 | tail -3` collects one test (it fails pre-fix on malformed keys).]]></verify>
  <done>The d3colors scheme is a committed, test-named fixture, and a new test module collects cleanly with every regression test failing for the recorded reason and the shipped-scheme snapshot passing.</done>
</task>

<task type="auto" id="06-02">
  <name>Read scheme lines as Stata's scheme.class does</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_render.py` add
    `@staticmethod def _scheme_tokens(line)` immediately before `_parse_lines` (:3941) per
    TR-06.1, with a docstring citing scheme.class:189-226 (`tokenize`, `args style id
    stylename`), `scripts/extract_scheme_truth.py:207-262` as the earlier reading, the
    measured `symbolsize p small *medium` → `small`, and the comment-rule note of
    Boundaries. Rewrite the tail of `_parse_lines` (:3990-3998) and its comment-skip line
    (:3955) per TR-06.2 and TR-06.4: tabs to blanks, `//` skipped, `enumerate(lines, 1)` for
    line numbers, `sequence`/`label` skipped, the bounded warning through `_notes` and
    `_safe_name`, two-token class defaults, third-token values, later tokens ignored, and the
    nameless `#include` warned the same way. Update `_parse_lines`'s docstring and the class
    docstring paragraph on the file grammar (about :3383-3400) to say the value is the third
    token with quotes removed. Add the function-map entry of TR-06.7 to
    `test/function_test_map.py` beside `SchemeParser._safe_name` (:242). Line numbers are
    pre-edit; locate by symbol.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_scheme_quoted_values.py test/test_scheme_coercion.py test/test_scheme_consumption.py test/test_scheme.py test/test_scheme_fidelity.py test/test_scheme_resolution.py test/test_scheme_review_fixes.py test/test_server_scheme.py test/test_function_test_map.py test/test_statistical_helpers.py -q 2>&1 | tail -5` reports no failures; `python3 -c "import dash_render as d;print(d.SchemeParser._scheme_tokens('color p1 \"31 119 180\" extra'))"` prints `['color', 'p1', '31 119 180', 'extra']`; `grep -n 'tokens\[-1\]' dash_render.py | grep -v textbox` prints nothing in `SchemeParser`; `DASH_LOCAL_SCHEMES=1 python3 -m pytest test/test_scheme_quoted_values.py -q -k Local 2>&1 | tail -3` passes.]]></verify>
  <done>SchemeParser reads a directive's value as Stata's third token with quotes stripped, skips what Stata skips, names each unreadable line once under the include-note bound, and every test of 06-01 and every existing scheme test passes.</done>
</task>

<task type="auto" id="06-03">
  <name>Certify a quoted scheme through dash.ado</name>
  <files>test/test_custom_scheme_quoted.cscript (new), test/run_all_cscripts.do</files>
  <action><![CDATA[
    Create `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_custom_scheme_quoted.cscript`
    from `test/test_custom_scheme.cscript`: the same header block (:70-88, title `"dash
    custom schemes, quoted values"`), the same working-directory setup (:98-103, :167-176),
    `_cs_write_theme` generalised to take the replacement line as a third argument so the
    three files can be written (`myquoted.scheme` with `color background      "255 0 0"`,
    `myquoted50.scheme` with `color background      "255 0 0 %50"`, `myp1.scheme` as s1rcolor
    plus an appended line `color p1 "31 119 180"`), and the helper programs `_cs_run`,
    `_cs_count`, `_cs_expect`, `_cs_done`, `_cs_log`, `_cs_page` copied unchanged (:178-281).
    Cases per the stub: CQ-01 `dash scatter mpg weight, scheme(myquoted) saving(q1.html,
    replace)` rc 0, `_cs_log ... "UserWarning" 0`, `_cs_page ... "#ff0000" 1`; CQ-02 with
    `myquoted50`, the same three assertions; CQ-03 with `myp1`, `#1f77b4` present. Restore
    `c(scheme)` and `cd` back at the end as the original does; `exit 1` if the tally is
    non-zero. Register it in `test/run_all_cscripts.do` as block 67 by copying :1087-1109
    with the new name. Run it alone from a scratch directory (`cd ".../dash/test"` then `do
    "test_custom_scheme_quoted.cscript"` in a driver do-file, `STATATMP=<scratch>/tmp/`,
    `arch -arm64 /usr/local/bin/stata-mp -b do run_one.do`) and read `run_one.log`; then run
    `test_custom_scheme.cscript` the same way to confirm CS-01..CS-15 still pass.
  ]]></action>
  <verify><![CDATA[`grep -c "PASS" <scratch>/run_one.log` prints 3 and `grep -c "FAIL" <scratch>/run_one.log` prints 0 for the new script; the second run's log shows fifteen `CS-.. PASS` lines and no `FAIL`; `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -3` passes.]]></verify>
  <done>A registered certification script proves through dash.ado that a working-directory scheme written with Stata's quoted RGB, with and without %opacity, draws its declared background and p1 colour with no warning, and the existing custom-scheme script is unaffected.</done>
</task>

<task type="auto" id="06-04">
  <name>Close D1 in BUGS.md, CHANGELOG and the help</name>
  <files>BUGS.md, CHANGELOG.md, dash.sthlp</files>
  <action>
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/BUGS.md` append a closed entry
    `- [x] Title: A scheme's quoted values (RGB colours, %opacity) were dropped without a
    warning` with File Names and Line Numbers (`dash_render.py SchemeParser._parse_lines
    (tokens[-1] as the value)`), Description (GAPS2 D1's measured symptom: `color background
    "255 0 0"` stored under a malformed key, a copied scheme-d3colors.scheme drawing every
    series grey with 0 warnings, 127 of 129 local third-party schemes using quoted RGB;
    `label "s2 color"` stored under `label "s2` in every shipped scheme), Suggested fix
    (tokenise as scheme.class does: third token, quotes stripped, `sequence`/`label`
    skipped, one bounded warning per unreadable line), and Resolution "Fixed. Certified by
    test/test_scheme_quoted_values.py::TestQuotedValuesAreRead (d3colors p1-p15 in both
    modes, %opacity), ::TestTheTokeniserIsStatas, ::TestUnreadableLinesWarnOnceEach,
    ::TestShippedSchemesParseAsBefore (the twenty shipped schemes unchanged) and
    test/test_custom_scheme_quoted.cscript CQ-01..CQ-03. hsv, CMYK and colour*# values are
    D7's." In `CHANGELOG.md` under `### Results that change` / `**Colours, schemes and
    appearance**` (:113) add: a scheme file copied into the working directory that wrote its
    colours as Stata's schemes do, `color p1 "31 119 180"` or `color p1 "26 71 111 %20"`,
    lost every such directive without a warning and drew the scheme's `color p` default or
    s2color's colour in its place; the value is now read as Stata reads it, so such a scheme
    draws its declared colours and opacities, and a line dash cannot read is named once with
    its line number (WP-28 D1). In `dash.sthlp` extend the scheme paragraph (:2804-2814)
    after "Copy the file into the working directory instead." with: the file is read as
    Stata reads it, each line `styletype element style` with the style the third word, quoted
    when it holds blanks, as in `color background "255 0 0"` or `color p1 "26 71 111 %20"`;
    a line that cannot be read that way is named once, with its line number, and skipped.
    grep the three edits and the commit message for `claude` and `anthropic` before and after
    committing.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_1.py -q 2>&1 | tail -3` passes; `grep -n "quoted values (RGB colours, %opacity)" BUGS.md` finds the entry; `grep -n '26 71 111 %20' CHANGELOG.md dash.sthlp` finds both; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0; `python3 -m pytest test/ -q 2>&1 | tail -5` reports no failures.]]></verify>
  <done>D1 is recorded closed in BUGS.md naming its tests, the colour change is listed under "Results that change", the help states the scheme grammar dash reads, and the full suite is green.</done>
</task>

<task type="auto" id="06-05">
  <name>Compare d3colors against Stata's SVG if S02 has landed</name>
  <files>test/test_custom_scheme_quoted.cscript</files>
  <action><![CDATA[
    If `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/cert_svg.do` does not exist
    (S02 is batch 1 and may not have merged), do nothing to the tree and record "D1 SVG
    comparison deferred to S19: test/cert_svg.do absent" in this task's commit message or,
    if there is nothing to commit, in the section's completion note. If it exists, add case
    CQ-04 to `test/test_custom_scheme_quoted.cscript`: write `scheme-d3colors.scheme` (a copy
    of the fixture) into a temporary directory, `adopath + "<dir>"`, `graph export` of
    `twoway scatter mpg weight, scheme(d3colors)` to SVG through S02's helper, read the first
    marker's fill (normalising U+00A0 to a blank first, research report D §11) and assert it
    equals `#1f77b4` and equals the p1 fill dash draws in `q3.html`'s scatter (decode the
    glyph's `fill_color` from the page's Bokeh JSON, or `cert_file_has` for `#1f77b4`).
    Restore the ado-path afterwards. Run the script alone as in 06-03.
  ]]></action>
  <verify><![CDATA[Either `ls test/cert_svg.do` fails and the deferral is recorded, or `grep -c "CQ-04 PASS" <scratch>/run_one.log` prints 1 and `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -3` passes.]]></verify>
  <done>Stata's own SVG of a scatter under the copied d3colors scheme agrees with dash's p1, or the comparison is recorded as deferred to S19 with the reason.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" exists and passes; the three regression tests are recorded
  as failing at 91d97be in 06-01's commit message.
- `SchemeParser._scheme_tokens` exists and is named in `test/function_test_map.py`;
  `_parse_lines` no longer contains `tokens[-1]`.
- `git ls-files test/fixtures/schemes/scheme-d3colors.scheme` lists the fixture and
  `test_fixtures_are_committed.py` is green.
- `test/test_custom_scheme_quoted.cscript` is registered and passes under `arch -arm64
  /usr/local/bin/stata-mp -b`; `test/test_custom_scheme.cscript` still passes; the cert suite
  reports no SKIP.
- `python3 -m pytest test/ -q` and `make test` are green with no skip from this section;
  `DASH_LOCAL_SCHEMES=1 python3 -m pytest test/test_scheme_quoted_values.py -k Local`
  passes on this machine.
- BUGS.md, CHANGELOG.md and dash.sthlp carry the D1 closure; no AI reference anywhere.
- No file outside the five tasks' file lists is modified.

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
- **The sweep is not a skip.** Under `DASH_STRICT=1` (`make test`, `make check`) any skip is
  red; the PLUS sweep is therefore defined only when `DASH_LOCAL_SCHEMES=1` is set, so the
  strict suite never sees it. Run it by hand on this machine before committing 06-02.
- **A third-party scheme's `#include`.** Some local schemes `#include` another PLUS scheme;
  `_include` resolves through `_resolve_path` (CWD and dash's `schemes/` only), so such an
  include falls back to s2color with a "(note: scheme X not found …)" warning. The sweep
  records warnings and asserts only on keys.
- **Stata's Python.** The cscripts' `python:` blocks, if any, run under `c(python_exec)`;
  keep to three concurrent Stata sessions in the batch, and on a run of SKIPs check
  `c(python_exec)` before trusting them.
- **Renderer order.** The scheme is parsed once at build time in both modes and the served
  app rebuilds it from `_SCHEME_PROPS`; there is no order difference to mind.
- **Line numbers drift.** `_scheme_tokens` adds about 40 lines before `_parse_lines`; every
  anchor in 06-02 is also a symbol, and the symbol is authoritative.
