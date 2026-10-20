# Section 42: SMCL inline runs and the other SMCL directives

> Part of: WP-31 · GAPS3 rows: E9 · Risk: yellow · Batch: 14 · Depends on: 01 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U42

## Overview

**What is wrong today.** GAPS3 E9 (GAPS3.md:188): "Inline SMCL style runs (`{bf:}` on part of a text) and raised text with no Unicode form drawn in the text's own style; `{hline} {space} {dup} {cmd:} {hi:} {ccl} {center:}` and links drawn as typed." Its evidence is dash_render.py:34473-34481 (`_dash_graph_text_note`) and :33876-34123 (the graph-text tables and `_dash_graph_text_runs`); its task "Split a text into runs and draw as several Label objects, or document the limit." Register P2.70 ("Exact inline style runs and raised text (TeX route) ... Effort L") and P2.47 ("SMCL beyond graph_text's documented tags drawn as typed ... Effort M").

At `6370ca4` `_dash_graph_text_runs(line)` (:34105-34236) reads `{bf:}`, `{it:}`, `{sup:}`, `{sub:}`, the three font tags, `{&name}` and `{c ...}` exactly as measured on twoway 19.5 (fixture `graph_text_truth.json`), and its docstring records "Other SMCL (`{hline}`, `{cmd:}`) is drawn as typed (A32)". `_dash_graph_text_parts` (:34237-34282) folds the runs into ONE Bokeh text: a style or font shared by every non-blank run is applied to the model; several styles set the flag `"inline"`; a raised run whose every character has a Unicode superscript/subscript form is rewritten (`_DASH_GT_SUP`/`_DASH_GT_SUB`, :33972-33996), else flag `"level"`. `_dash_graph_text_style` (:34399-34470) writes the one style onto the model (Title, Label, axis title, ColorBar/Legend title; tick overrides and legend items only when every label shares it). `_dash_graph_text_note` (:34473-34490) says once per render and sink what could not be drawn. The CSS families for `{stSans}`, `{stSerif}` and `{stMono}` are fixed (the families are the values of `_DASH_GT_TAGS`' three font rows, :34002-34004, and `_dash_gt_head` emits them as a run's `font`; `_DASH_GT_FONTS` :33990 is referenced only by its definition and the copy list; a `graph set` font is S43's G2 -- see TR-42.1's tag-name hand-off, DECISIONS A27).

**What twoway does with the other SMCL** is not measured: `graph_text.sthlp` documents only the tags dash reads; `{hline}`, `{space}`, `{dup}`, `{cmd:}`, `{hi:}`, `{ccl}`, `{center:}` and `{browse ...}` links are SMCL that `display` knows. U42-02 measures each in a graph title and records the SVG text. The task then branches: whatever twoway draws (the literal braces, the directive's expansion, or nothing) dash draws, through the same linear scanner.

**After this section**, in both modes: every SMCL directive of the probe list is drawn exactly as twoway's SVG shows it; a text with several style runs is drawn as twoway draws it where Bokeh has a model for it (D-42a) and otherwise keeps today's one-style rule with the note and a documented, measured example (M17); a raised run with no Unicode form keeps today's rule, documented with a measured example; the help's graph-text paragraph is rewritten from the fixture.

**Why one section.** E9 is the one row; it is the graph-text parser's batch-14 owner (index owner table: "graph-text parser: 42").

**Test order and commit rule.** One cycle, one commit `(WP-31 E9)`: 42-01 measures and writes the red tests (no commit); 42-02 fixes; 42-03 documents, closes and commits.

### Section decisions (binding on the executor)

- **D-42a. Inline style runs are drawn as several Label models only for the sinks that are Labels already, and documented everywhere else.** Bokeh's `Title`, axis `axis_label`, `Legend.title`, legend item labels and tick labels are single-text models with one `text_font_style`; Bokeh has no rich text (RESEARCH §2 forbids the 3.9 `Markdown` widget) and Python cannot measure a run's width to place the next Label (no font metrics server-side). The one sink dash draws as `Label` models today is the `text()`/`ttext()` added text (S30's `_dash_textbox`, batch 10) and `note`/`caption` when drawn as Labels in their textbox -- for those, several runs could be several Labels placed by a JS measure. That is a CustomJS on the figure's canvas with `measureText`, new JS for two sinks, under the nonce path. The maintainer's decision list says "or document the limit" (GAPS3 E9's task) and P2.70 grades it L; S42 is M. **Ruling:** S42 documents the inline limit with a measured example (M17) and improves the one-style fold in two measured cases: (i) when the runs that differ in style are blank-only (already handled) and (ii) when exactly one run is styled and it is the WHOLE non-blank text of a tick label or legend label (already handled per label). No Label splitting. The TeX route (`$$\mathbf{}$$`) is refused: it would route user text through MathJax (`_dash_inert_tex`, test_label_sinks.py::TestTeX and ::TestInertTex pin that no TeX pair assembles), a rule-1 surface. This ruling is listed for ratification in the hand-back.
- **D-42b. The seven other directives and links follow the probe.** For each of `{hline}`, `{hline 5}`, `{space 3}`, `{dup 3:ab}`, `{cmd:x}`, `{hi:x}`, `{ccl N}`, `{center:x}`, `{browse "u":t}`, `{help x}`, `{stata x}`: if twoway's SVG shows the text as typed, dash keeps drawing it as typed (today) and the help lists it as literal; if the SVG shows the directive expanded (e.g. `{dup 3:ab}` as `ababab`, `{hline 5}` as five line characters, `{space 3}` as three blanks, `{cmd:x}` as `x`), `_dash_graph_text_runs` gains that expansion in its pass 2 as a new row of `_DASH_GT_TAGS` (a `("literal", text)` kind) with the measured output; `{ccl N}` and `{center:}` likewise; a count argument is bounded at 200 (a `{dup 100000:x}` is cut, noted once) and the whole text's expansion is bounded at 4,000 characters (`_DASH_GT_TEXT_BUDGET`; once the emitted expansions of one text pass it, the rest of that directive's expansion is dropped and the flag `cut` is set) so no text can grow the page unboundedly (rule 1; a text of many `{hline 200}` cannot grow 18x past the budget); a link is its visible text if twoway shows that.
- **D-42c. Raised text with no Unicode form stays on the line, flagged, documented** with the measured example `{sup:q}` (no superscript q in Unicode) from the fixture.
- **D-42d. The scanner stays linear and non-recursive** (:34126-34131: "Two passes over the positions of `{`, `}` and `:` only, no recursion"); a new expansion runs inside pass 2 over the already-paired directives; `test_graph_text.py::TestLinearTime` (:395) must stay green with the new rows (100,000 `{` in about 0.03 s).

## Risk: [yellow] -- the parser is reached by every text sink in both modes

**Why.** `_dash_graph_text_runs` is called for every title, label, tick override, legend label, tooltip name and filter title (test_graph_text.py::TestEverySinkBothModes :601, ::TestControlCodesAreEscapedAtEverySink :731); a wrong expansion changes every page.

**Risk factors.** 1. A `{dup N:}` or `{hline N}` expansion is a size amplifier. 2. Text reaching HTML sinks (filter titles, tooltips) must stay escaped after expansion. 3. The measured fixture may show twoway drawing some directives as typed and others expanded; a half-implemented table is worse than none. 4. The `inline` note text is pinned (test_graph_text.py::TestTheNote :551) and the help paragraph (::TestTheHelp :1118).

**Mitigation.** 1. D-42b's bound of 200 per directive and the 4,000-character budget per text, `TestBounds::test_dup_is_cut` and `::test_total_budget`. 2. Expansion happens in `_dash_graph_text_runs`, before `_dash_graph_text_plain`/`dash_html_escape`; `TestControlCodesAreEscapedAtEverySink` is run. 3. Every probe key becomes one parametrized test; a directive is expanded only when the fixture says so. 4. Flipped in place with the reason.

## Dependencies

- **Depends on: 01.** Blocks none. S30 (batch 10, textbox placement and added text) has landed; S42 calls `_dash_textbox`'s text path, does not edit it.
- **Parallel batch: 14**, merge order S41, S42, S43. **Can run with S41 and S43**: S41 edits colours/outlines; S43 edits the loader, the writers and, for G2's `graph set` fonts, `_dash_graph_text_style` ONLY (DECISIONS A27): S42 owns `_DASH_GT_TAGS`, `_dash_gt_head` and `_dash_graph_text_runs` (index owner table, batch 14) and makes the one-line change S43 reads -- `_dash_gt_head` emits the TAG NAME (`stSans`, `stSerif`, `stMono`) as a run's `font` instead of the CSS family (TR-42.1); S43's `_dash_graph_text_style` maps that name through `fig._dash_gt_fonts` (default `_DASH_GT_FONTS`). S42 does not edit `_dash_graph_text_style` or `_DASH_GT_FONTS`. S42 is batch 14's only editor of test/test_graph_text.py (S43's `TestGraphSetFonts` lives in its new test/test_graph_set_fonts.py; R3-10) and the only editor of dash.sthlp's graph-text paragraph :4060-4075 (S43's fonts sentence is handed to TR-42.4; REVIEW-3e F1).

## Evidence

### The scanner and the fold

```python
34105 def _dash_graph_text_runs(line):
34106     """The styled runs twoway draws for one line of graph text: a list of
34107     ``(text, style, level, font)`` ...
34123     next tag opens, closes or is set (measured 08oct2026: ``a{c 0}b{bf:c}d``
34124     draws ``a``, bold ``c``, ``d``).  Other SMCL (``{hline}``, ``{cmd:}``)
34125     is drawn as typed (A32).  One documented difference: a symbol inside
34126     ``{stSymbol:}`` is drawn as itself.
34237 def _dash_graph_text_parts(text):
34238     """``(plain, style, font, flags)``: graph text as one Bokeh text draws
34239     it. ... Over the runs that hold a non-blank character, one style gives
34245     *style* (None for normal) and one font gives *font*; several give None
34246     and the flag ``"inline"`` (one text model has one style and font: register
34247     A31).
34473 def _dash_graph_text_note(where, kind, flags):
34477     if "inline" in flags:
34478         parts.append(f"{{bf:}}, {{it:}} or a font tag on part of a {kind} "
34479                      f"is drawn in that text's own style and font")
34481         parts.append(f"{{sup:}} or {{sub:}} around a character with no "
34482                      f"raised or lowered form in a {kind} is drawn on the "
34483                      f"line")
```
The tag table `_DASH_GT_TAGS` (:33997-34031): `"sup": ("level", 1)`, `"bf"`, `"it"`, the fonts. `_dash_gt_head(head, term)` (:34051) classifies a directive head; `_dash_gt_char(code)` (:34032) the `{c ...}` codes. Sinks: `_dash_finish_text_runs(value, how)` (:34302-34398) for `"text"`, `"map"`, `"value"`, `"labels"`, `"tooltips"`; `_dash_graph_text_style` (:34399) applied at :33845 and :33856. All these are module functions already in the served functions tuple (grep `"_dash_graph_text_runs"` in :46822-47270 confirms; a new helper goes after `_dash_graph_text_runs`'s entry).

### Stata's rule

`B/g/graph_text.sthlp` documents `{bf}`, `{it}`, `{sup}`, `{sub}`, `{stSans}`, `{stSerif}`, `{stMono}`, `{fontface}`, `{&symbol}`, `{c code}` only. `B/s/smcl.sthlp` documents `{hline}`, `{space}`, `{dup}`, `{cmd:}`, `{hi:}`, `{ccl}`, `{center:}`, `{browse}`, `{help}`, `{stata}` for the Results window. How the graph text renderer (compiled, `gdi text`) treats them is unmeasured -- U42-02.

### Fixtures and tests on disk

`test/fixtures/graph_text_truth.json` (scripts/extract_graph_text_truth.do): the measured tag grammar; test_graph_text.py classes `TestGraphTextTruth` (:220), `TestTheScanner` (:310), `TestLinearTime` (:395), `TestThePass` (:429), `TestTheNote` (:551), `TestEverySinkBothModes` (:601), `TestControlCodesAreEscapedAtEverySink` (:731), `TestMarkerLabels` (:831), `TestAfterAFilterMove` (:916), `TestDomSinks` (:980), `TestTheServedApp` (:1013), `TestInChrome` (:1089), `TestTheHelp` (:1118). Pins to flip: any node of `TestTheScanner` asserting `{hline}` or `{cmd:x}` is literal (if the probe shows expansion), `TestTheNote` nodes pinning the note's words if they change, `TestTheHelp` (help paragraph text).

## User stories

- US-42.1 As a Stata user, I want `title("Mean {dup 2:--} {hline 3}")` and `{cmd:}`/`{hi:}` in my titles drawn as twoway draws them.
- US-42.2 As a Stata user, I want to know, from the help, exactly what `{bf:}` on part of a title does in dash and why, with twoway's picture beside it.
- US-42.3 As a maintainer, I want no SMCL directive able to grow a page without bound.

## Business requirements

- BR-42.1 Each probed directive draws what twoway's SVG shows, in every sink, both modes.
- BR-42.2 An inline style run and a raised run with no Unicode form are documented with a measured example; the one-render note stays.
- BR-42.3 A count argument above 200 is cut with one note; text reaching HTML stays escaped.
- BR-42.4 Nothing is printed when the text is drawn as twoway draws it.

## Technical requirements

- TR-42.1 New rows in `_DASH_GT_TAGS` (:33997-34031) for each directive the fixture shows expanded: `"hline": ("literal", "─")`, `"space": ("literal", " ")`, `"dup": ("dup", None)`, `"cmd": ("passthrough", None)`, `"hi": ("passthrough", None)`, `"ccl": ("ccl", None)`, `"center": ("passthrough", None)`, `"browse"`/`"help"`/`"stata"`: `("link", None)` -- the kind words are read by a new branch in pass 2 of `_dash_graph_text_runs` (D-42b): `literal` with an optional count argument repeats the literal `min(count, 200)` times; `dup` repeats its `:`-text `min(count, 200)` times (the text itself is re-read for tags? No: measured; if twoway styles inside `{dup}`, the inner text is appended as a run with the enclosing style); `passthrough` emits the `:`-text in the enclosing style; `ccl` emits `""` (a c-class value cannot be read here; measured -- if twoway prints the value, dash.ado must expand `{ccl}` at registration: then `_dash_graph_text_ccl` in dash.ado replaces `{ccl name}` with `c(name)` for the allowed names `current_date current_time username N k filename` only); `link` emits the visible text. Only the rows the fixture needs are added. One further line, independent of the fixture (A27, F2): the three font rows of `_DASH_GT_TAGS` (`"stSans": ("font", "Helvetica, Arial, sans-serif")`, `stSerif`, `stMono`, :34002-34004) keep their CSS values as documentation but `_dash_gt_head` emits the TAG NAME (`stSans`) as the run's `font` (`font = h` in place of the row's value, :34069-34071); `_dash_graph_text_style` (S43's edit) maps the name through `fig._dash_gt_fonts`, default `_DASH_GT_FONTS` -- until S43 lands, S42 adds the one-dict lookup `_DASH_GT_FONTS.get(font, font)` at the existing read in `_dash_graph_text_style` so the page is unchanged (S43 replaces that one expression; recorded in both Dependencies paragraphs). `{stSymbol:}` is unchanged.
- TR-42.2 `_dash_gt_head(head, term)` (:34051): accept a numeric argument after the name (`hline 5`, `space 3`, `dup 3`) -- the head regex becomes `name[ blanks][digits]`, digits at most 6 characters, value parsed with `int()` and bounded.
- TR-42.3 A new flag `"cut"` set when a count was bounded or the text's 4,000-character budget was reached; `_dash_graph_text_note` gains `parts.append(f"a repeat count above 200 or an expansion above 4,000 characters in a {kind} was cut")`.
- TR-42.4 Help (R3): dash.sthlp's graph-text paragraph (:4060-4075 region, "labels and legend keys take a style only when every one of them has it" ... ) gains: the list of directives drawn as twoway draws them (from the fixture), the inline-run limit with the measured example (`title("a {bf:b} c")`: twoway bold b; dash draws the whole title in the title's style and says so once), the raised-text example (`{sup:q}`), the 200 bound and the 4,000-character budget, and -- handed over from S43 (A27, F1; S42 is the only editor of this paragraph in batch 14) -- the fonts sentence in one of its two measured forms: `A {cmd:graph set} font face is read where Stata keeps it and leads the {c -(}stSans{c )-}, {c -(}stSerif{c )-} and {c -(}stMono{c )-} families.` or `A {cmd:graph set} font face is not read: Stata keeps it where no program can read it (measured), so the three families are fixed.` The form is chosen by the `fonts.home` probe, which S42's own extractor runs (the same two probe lines as S43's `fonts.home`/`fonts.svg`, so the two fixtures agree). test_help_claims_*.py that quote this paragraph are updated in the same commit.
- TR-42.5 Both renderers: the functions are in the functions tuple already; a new module helper (none planned; if one is added, after `"_dash_graph_text_runs",`). function_test_map.py: no new function unless a helper is added.
- TR-42.6 `test/test_graph_text.py` gains `TestOtherSmclDirectives` (parametrized over the fixture's `smcl.*` keys, both modes, three sinks: title, xlabel override, legend label), `TestBounds` (`test_dup_is_cut`, `test_hline_is_cut`, `test_note_once[mode]` -- each `pytest.mark.skipif` the fixture's `smcl.dup_big` shows no expansion, since then nothing is bounded, D-42b; and `test_total_budget`, unconditional: a text of 25 `{hline 200}` directives expands to at most 4,000 characters and flags `cut`), `TestInlineLimitIsDocumented` (the help names the example and the note is raised once in both modes; the unconditional red of 42-01), and `TestTagNameFont::test_head_emits_tag_name` (`_dash_gt_head("stSans", ...)` returns `font == "stSans"`; the drawn `text_font` still equals `_DASH_GT_FONTS["stSans"]`).


### Reference TR-42.A: the pass-2 branch (TR-42.1), to be added where pass 2 emits a directive's run in `_dash_graph_text_runs` (the `kind, val = _DASH_GT_TAGS[name]` read; re-read the function at the batch-14 base)

```python
            elif kind == "literal":
                # {hline} / {hline 5} / {space 3}: the literal repeated the
                # directive's count (1 when absent), bounded (WP-31 E9).
                n = min(count or 1, _DASH_GT_REPEAT_MAX)
                if (count or 1) > _DASH_GT_REPEAT_MAX:
                    flags.add("cut")
                emit(val * n, style, level, font)
            elif kind == "dup":
                n = min(count or 1, _DASH_GT_REPEAT_MAX)
                if (count or 1) > _DASH_GT_REPEAT_MAX:
                    flags.add("cut")
                emit(inner_text * n, style, level, font)
            elif kind == "passthrough":   # {cmd:x} {hi:x} {center:x}
                emit(inner_text, style, level, font)
            elif kind == "link":          # {browse "u":t} {help x} {stata c:t}
                emit(link_visible_text(inner_text), style, level, font)
            elif kind == "ccl":
                emit("", style, level, font)
```
with `_DASH_GT_REPEAT_MAX = 200` and `_DASH_GT_TEXT_BUDGET = 4000` module constants beside `_DASH_GT_TAGS` (constants tuple entries after `_DASH_STALE_STATUS_HTML`'s group, R2) and `count` parsed by TR-42.2's head rule; `emit` keeps a running total of the characters the expansions of this text have produced and, when `total + len(expansion) > _DASH_GT_TEXT_BUDGET`, emits only the first `_DASH_GT_TEXT_BUDGET - total` characters and adds `"cut"` to `flags` (F26). `link_visible_text`: for `{browse "u":t}`/`{stata c:t}` the text after the first `:` outside quotes; for `{help x}` the word `x`. Each row exists only if the fixture shows that directive expanded; the `emit` helper and the run tuple are the function's existing ones.

### Reference TR-42.B: the fixture-driven test parametrisation

| key | typed | drawn by twoway (fixture) | dash after S42 |
|---|---|---|---|
| smcl.hline | `a {hline} b` | measured | equal to the fixture |
| smcl.hline5 | `a {hline 5} b` | measured | equal |
| smcl.space3 | `a{space 3}b` | measured | equal |
| smcl.dup3 | `a {dup 3:xy} b` | measured | equal |
| smcl.cmd / smcl.hi / smcl.center | `{cmd:xy}` ... | measured | equal |
| smcl.ccl | `{ccl current_date}` | measured | equal (or dash.ado expansion) |
| smcl.browse / help / stata | links | measured | equal |
| smcl.dup_big | `{dup 1000:x}` | measured length | 200 x's, flag `cut`, one note |
| budget (no fixture key) | 25 x `{hline 200}` | -- | at most 4,000 characters, flag `cut` |
| inline.bf_part | `a {bf:b} c` | tspan 2 bold | whole title in its own style; note once; help example |
| inline.sup_q | `a{sup:q}` | tspan 2 raised | on the line; note once; help example |
| inline.sup_2 | `a{sup:2}` | raised 2 | `a²` (today's Unicode rule, guard) |

### Verbatim TR-42.C: the help paragraph's new sentences (dash.sthlp, after the `{c -(}c 0{c )-}` sentence at :4071-4072)

```
{pstd}
The other SMCL directives {cmd:{c -(}hline{c )-}}, {cmd:{c -(}space{c )-}},
{cmd:{c -(}dup{c )-}}, {cmd:{c -(}cmd:{c )-}}, {cmd:{c -(}hi:{c )-}},
{cmd:{c -(}ccl{c )-}}, {cmd:{c -(}center:{c )-}} and the link directives are
drawn as {cmd:twoway} draws them (<the fixture's outcome per directive, in one
clause each>); a repeat count above 200 is cut to 200, an expansion above
4,000 characters is cut there, and dash says so once.
<the fonts sentence of TR-42.4 in the form the fonts.home probe selects>
A style tag on part of a text -- {cmd:title("a {c -(}bf:b{c )-} c")} -- is
drawn by {cmd:twoway} with only the b bold; a Bokeh text has one style, so
{cmd:dash} draws the whole title in the title's style and says so once.
A raised or lowered character with no Unicode form -- {cmd:{c -(}sup:q{c )-}} --
is drawn on the line by {cmd:dash} where {cmd:twoway} raises it; the digits,
signs and brackets have forms and are raised.
```
`TestInlineLimitIsDocumented::test_help_example` greps the two example texts.

- BUGS.md E9 Resolution form: `Fixed <ddmonyyyy> (WP-31, E9). _dash_graph_text_runs draws {hline}, {space}, {dup}, {cmd:}, {hi:}, {ccl}, {center:} and links as twoway's SVG shows (<list>), bounded at 200 repeats and 4,000 characters per text, in both renderers; inline style runs and raised text with no Unicode form stay one-style/on the line and are documented with twoway's measured picture (M17, D-42a). Pinned by test/test_graph_text.py::TestOtherSmclDirectives::test_each_directive, ::TestBounds, ::TestInlineLimitIsDocumented, test/test_wp31_truth.cscript U42-02; fixture test/fixtures/smcl_text_truth.json. Closes GAPS3 E9 (WP-31, E9).`

## Boundaries

- No Label splitting, no TeX, no MathJax (D-42a); `_dash_inert_tex` untouched.
- `_DASH_GT_FONTS` values, `_dash_graph_text_style`'s font mapping and `graph set` are S43's (G2); S42 only makes `_dash_gt_head` emit the tag name (TR-42.1) and adds the bridging `_DASH_GT_FONTS.get(font, font)` lookup S43 replaces.
- `_dash_textbox`/`_dash_textbox_place` (S30) are called, not edited.
- No `_FILTER_JS` edit (the saved move re-applies the finished text through `_dash_finish_text_runs`'s stored results, unchanged).

## Stata truth

Script `scripts/extract_smcl_text_truth.do` -> `test/fixtures/smcl_text_truth.json`. Per key, `sysuse auto; twoway scatter mpg weight, title(<text>) name(u42, replace); graph export <key>.svg`; the python block reads every `<text>` element's content in the SVG and records the title's text (joined `tspan`s), rc and any log line.

| Key | title text |
|---|---|
| `smcl.hline` | `a {hline} b` |
| `smcl.hline5` | `a {hline 5} b` |
| `smcl.space3` | `a{space 3}b` |
| `smcl.dup3` | `a {dup 3:xy} b` |
| `smcl.cmd` | `a {cmd:xy} b` |
| `smcl.hi` | `a {hi:xy} b` |
| `smcl.ccl` | `a {ccl current_date} b` |
| `smcl.center` | `{center:xy}` |
| `smcl.browse` | `a {browse "https://www.stata.com":xy} b` |
| `smcl.help` | `a {help twoway} b` |
| `smcl.stata` | `a {stata sysuse auto:xy} b` |
| `smcl.dup_big` | `{dup 1000:x}` (rc and the text's length) |
| `inline.bf_part` | `a {bf:b} c` (per-tspan `font-weight`) |
| `inline.sup_q` | `a{sup:q}` (per-tspan `baseline-shift`/`dy` and size) |
| `inline.sup_2` | `a{sup:2}` (control: the Unicode form dash writes) |
| `fonts.home` | `graph set svg fontface Courier`; `graph set window fontface Courier`; capture `graph set`, `graph query`, `macro list`, `char list` to a log (S43's probe, repeated so TR-42.4's fonts sentence can be chosen in this batch) | the log text; whether a readable home exists |
| `fonts.svg` | `scatter ..., title("{stSans:a}")` after `graph set svg fontface Courier`; SVG | the title's `font-family` |

Truth block `* ==== S42 E9: SMCL inline runs ====`: U42-01 fixture stamped; U42-02 for each `smcl.*` key dash's saved and served title text (python helper reading `fig.title.text` after `_dash_finish_text_runs`) equals the fixture's text; U42-03 `{dup 1000:x}` is cut to 200 and one note is logged (`cert_log_has`); U42-04 `a {bf:b} c` logs the inline note once in dash and the help paragraph names the example (`cert_file_has dash.sthlp`).

## TDD test stubs

- Test: fixture stamped, 17 keys -- `test_graph_text.py::TestSmclFixture::test_meta` (guard).
- Test: each `smcl.*` key's text equals the fixture in title, xlabel override and legend label, both modes -- `TestOtherSmclDirectives::test_each_directive[mode-sink-key]` (red for every expanded directive; guard for literal ones).
- Test: `{dup 1000:x}` and `{hline 100000}` are cut to 200 and flagged `cut`, note once -- `TestBounds::test_dup_is_cut`, `::test_hline_is_cut`, `::test_note_once[mode]` (red when the fixture shows `smcl.dup_big` expanded; skipped otherwise, F25); 25 x `{hline 200}` stops at 4,000 characters -- `::test_total_budget` (red).
- Test: `_dash_gt_head` emits the tag name as `font` and the drawn family is unchanged -- `TestTagNameFont::test_head_emits_tag_name` (red).
- Test: the scanner stays linear with the new rows -- `TestLinearTime` (guard, existing).
- Test: control codes stay escaped after expansion at every HTML sink -- `TestControlCodesAreEscapedAtEverySink` (guard, existing) plus `::test_expanded_text_is_escaped` (red if a new row exists).
- Test: the help names `a {bf:b} c` and `a{sup:q}` with twoway's measured picture -- `TestInlineLimitIsDocumented::test_help_example` (red), `::test_note_once[mode]` (guard).
- Flips: any `TestTheScanner` node pinning a now-expanded directive as literal; `TestTheHelp` paragraph pins.
- cscript: U42-01..U42-04 (red: U42-02 for expanded keys, U42-03, U42-04's help half).
- Parity: `CORPUS` "title with {dup 3:ab} {hline 2}".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Directive expansion | pytest TestOtherSmclDirectives + U42-02 | smcl_text_truth.json | yes |
| Bounds | pytest TestBounds + U42-03 | -- | yes |
| Inline/raised documentation | pytest + U42-04 | same | yes |
| Escaping | existing class | -- | yes |

AC-42.1 every probed directive drawn as twoway's SVG; AC-42.2 bounds; AC-42.3 help example and note; AC-42.4 one green commit.

## Tasks

**Commit boundary.** 42-01..42-03 form the one E9 commit, subject `Draw the other SMCL directives as twoway does and document inline style runs (WP-31 E9)`; body opens with `<scratch>/42-01-failure.txt`. `$WT=<worktrees>/wp31-s42`.

<task type="auto" id="42-01">
  <name>Measure twoway's SMCL drawing and write failing tests</name>
  <files>scripts/extract_smcl_text_truth.do, test/fixtures/smcl_text_truth.json, test/test_graph_text.py</files>
  <action><![CDATA[
    Check the worktree (wp31-s42 at the batch-14 base). Create the extractor from the "Stata truth" table (head as scripts/extract_graph_text_truth.do, which already parses SVG tspans; `_meta` five keys), run through the slot, `git add -f` the fixture. Append `TestSmclFixture`, `TestOtherSmclDirectives`, `TestBounds` (its three cut tests skip unless the fixture's `smcl.dup_big` text differs from the typed text; `test_total_budget` always runs), `TestInlineLimitIsDocumented` and `TestTagNameFont` to test/test_graph_text.py (fixture-driven: a key whose fixture text equals the typed text is a guard). Run `python3 -m pytest test/test_graph_text.py -q -n0 -p no:cacheprovider -rf > <scratch>/s42/42-01.log`, write `<scratch>/42-01-failure.txt`. Write U42-01..U42-04 into the S42 block, run with `WP31_ONLY=S42`, append FAIL lines. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/smcl_text_truth.json'));print(sorted(d['_meta']), len([k for k in d if k!='_meta']))"` prints the five keys and 17; `grep -c FAILED <scratch>/s42/42-01.log` is at least 3 (`TestInlineLimitIsDocumented::test_help_example`, `TestBounds::test_total_budget` and `TestTagNameFont::test_head_emits_tag_name` are red whatever the probe shows; the other `TestBounds` nodes are red only when `smcl.dup_big` expands); `test -s <scratch>/42-01-failure.txt`.]]></verify>
  <done>twoway's drawing of eleven SMCL directives, two inline cases and the graph set font home was recorded and the regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="42-02">
  <name>Expand the measured directives and bound the counts</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-42.1 for exactly the keys whose fixture text differs from the typed text (D-42b) plus its fixture-independent tag-name line in `_dash_gt_head` with the bridging lookup in `_dash_graph_text_style`, TR-42.2, TR-42.3 and TR-42.A's `_DASH_GT_TEXT_BUDGET`; keep the two passes (D-42d). If `smcl.ccl` shows the c-class value, add the dash.ado registration-time expansion named in TR-42.1 (then dash.ado joins this task's files in place of nothing else: at most three files). Run test_graph_text.py (TestOtherSmclDirectives, TestBounds, TestLinearTime, TestControlCodesAreEscapedAtEverySink, TestEverySinkBothModes green), test_label_sinks.py, test_csp.py, and U42-02/U42-03 through the driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_graph_text.py test/test_label_sinks.py test/test_csp.py -q -p no:cacheprovider -k "not InlineLimitIsDocumented"` ends 0 failed; `grep -c "U42-0[23] PASS" <scratch>/s42/run_test_wp31_truth.log` prints 2.]]></verify>
  <done>Every probed SMCL directive is drawn as twoway's SVG shows it in both modes, repeat counts are bounded at 200 and texts at 4,000 characters with one note, the font tags travel by name, and the scanner stayed linear and escaped.</done>
</task>

<task type="auto" id="42-03">
  <name>Document the inline limit, close E9 and commit</name>
  <files>dash.sthlp, BUGS.md, GAPS3.md</files>
  <action><![CDATA[
    Apply TR-42.4 to the graph-text paragraph using the fixture's `inline.bf_part` and `inline.sup_q` records (twoway's picture in words: which tspan is bold / raised) and the fonts sentence in the form `fonts.home` selects (S43 does not edit this paragraph); update the test_help_claims_*.py nodes that quote the paragraph and flip `TestTheHelp`/`TestTheNote` pins in place. Run test_graph_text.py whole, test_help_conformance.py, test_help_claims_*.py -k "graph_text or smcl", and the S42 block (U42-04 PASS). Close BUGS.md's E9 entry (Resolution names D-42a as the documented limit, M17, and lists the expanded directives), rewrite `E9 Tracked` as `- **E9 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (the merger's step k.3b writes the sha, DECISIONS A11; the inline limit is a documented difference, not a residual: M17), replace the E9 marker(s) (a Results line: "titles with {dup}/{hline}/{cmd:}: drawn as typed -> as twoway draws them" per the fixture). Commit `(WP-31 E9)`; grep the message for tooling names (0). Write `<scratch>/s42/handback.txt` listing D-42a for ratification and the fixture's per-directive outcome.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_graph_text.py test/test_help_conformance.py -q -p no:cacheprovider` ends 0 failed; `grep -c FAIL <scratch>/s42/run_test_wp31_truth.log` prints 0; `git log -1 --format=%s` ends `(WP-31 E9)`; `grep -c '^- \*\*E9 Tracked:\*\* Closed' GAPS3.md` prints 1.]]></verify>
  <done>The help documents the inline-run and raised-text limits with twoway's measured pictures, the E9 entry and Tracked line are closed, and the one commit landed green.</done>
</task>

## Section completion criteria

- Each of the eleven directives drawn as the fixture says, both modes, three sinks; counts and the per-text budget bounded; `_dash_gt_head` emits the tag name; escaping intact; linear time kept.
- Help paragraph rewritten from the fixture; `TestTheHelp` green; D-42a recorded for ratification.
- One green commit; BUGS.md E9 closed; Tracked line; marker; fixture stamped and named.

## Notes

- **Order of passes:** expansions are applied in pass 2 after directives are paired, so `{dup 3:{bf:x}}` is read with the enclosing-tag rule the fixture shows; never re-scan output (the docstring's "Not idempotent" stays true).
- **HTML sinks** (`_dash_graph_text_plain` for filter titles, tooltips) get the expanded characters and then `dash_html_escape`/`html.escape`; the `TestControlCodesAreEscapedAtEverySink` class is the guard.
- **Copy lists:** `_DASH_GT_REPEAT_MAX` and `_DASH_GT_TEXT_BUDGET` after `_DASH_STALE_STATUS_HTML`'s group (R2); no new function unless a helper is added after `"_dash_graph_text_runs",`.
- **For S43 (same batch):** `_dash_gt_head` emits `stSans`/`stSerif`/`stMono` as `font`; `_dash_graph_text_style` holds the one expression `_DASH_GT_FONTS.get(font, font)` that S43 replaces with the `fig._dash_gt_fonts` lookup (A27). The fonts sentence of the help paragraph is S42's; S43's 43-03 does not touch :4060-4075.
- **R3:** the graph-text paragraph only; S56 reconciles the rest in batch 19.
- **R12:** no hot function.
- **python_exec hazard** as S40.
- **Decision for ratification:** D-42a (document inline runs; no Label splitting, no TeX).

## Addendum (15oct2026, DECISIONS D24): row D13b added to this section

### D13b: Global macros in title(), subtitle(), note() and caption() are drawn literally where twoway expands them

**Gap.** S30 made `text()` expand a global at registration with `_dash_at_globals` (by text substitution only; a global holding a `=exp` is not evaluated, documented). title()/subtitle()/note()/caption() still keep `$name` literal by JSE-65's decision, while twoway expands globals in every graph text option.

**Requirement.** Measure twoway for each text option (and the edge titles, axis titles, legend label text) with a global that holds plain text, SMCL, quotes and a `=exp`; expand the same way as S30's text() (substitution, bounded length, refusal past the bound), never evaluating; keep JSE-65's guarantee that text Stata already expanded is not expanded twice; update JSE-65 with a Flipped line.

**Fits S42** because S42 owns the graph-text parser (`_dash_gt_head`, inline SMCL runs) in batch 14.

**Process (binding).** As every row: measure twoway first (the measurement wins over this text; record a deviation); failing tests first with saved failure text; ONE commit with subject ending `(WP-31 D13b)`; close the BUGS.md entry "Global macros in title(), subtitle(), note() and caption() are drawn literally where twoway expands them" (Resolution ending `Closes GAPS3 D13 (WP-31, D13b).`), delete its `"D13b":` WP31_OPEN line, rewrite GAPS3.md's `- **D13b Tracked:**` line to `Closed in WP-31, BUGS.md "<title>", commit pending.`, replace `<!-- WP-31 D13b -->` under `### Results that change` with a line ending `(WP-31, D13b)`. dash replaces twoway (D13).

