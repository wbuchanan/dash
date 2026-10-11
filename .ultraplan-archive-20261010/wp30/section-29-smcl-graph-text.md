# Section 29: SMCL in graph text (P1.11 part b)

> Part of: WP-30 · Items: P1.11 part b (entry `P1.11b`; GAPS2-D3's SMCL half, DROPIN's GAPS2-D3-a, D3-b, D3-c and D3-d, with GAPS2-J2 and GAPS2-B13) · Risk: yellow · Batch: 10 (merge order S28, S29, S30) · Depends on: 06, 09, 15 · Blocks: 56 · Tasks: 12, 1 commit · Case prefix: GT

## Review amendments

- Measured (08oct2026, coordinator-confirmed; scratch note `s29/29-c0-truth.txt`, fixture `_meta.c0_rule` and the c0 cases of `test/fixtures/graph_text_truth.json`): twoway does not empty a text holding `{c 0}`. `{c 0}` (also `{c 00}`, `{char 0}`; `{c 0x0}` is drawn as typed) cuts off the rest of its own styled run on its own line: what follows it is dropped until the next tag opens, closes or is set; text after the run's closing brace and the text's other lines are drawn (`a{c 0}b{bf:c}d` → `a` + bold `c` + `d`; `{bf:a{c 0}b}c` → bold `a` + `c`; `a{c 0}{&alpha}b` → `a`; `{foo:a{c 0}b}c` → `{foo:a`; `title("a" "b{c 0}c")` → `a`, `b`; `s29qzq{c 0}x` → `s29qzq`). This replaces the "empty the whole text" reading wherever this file states it: TR-29.2-TR-29.5 (`_dash_gt_head` returns `("cut",)`; the run reader drops text while cut and clears the cut at an open, a non-literal close or a set tag; `_dash_graph_text_parts` has no empty-the-text rule), GT-01 (the label is exactly `s29qzq`), GT-07 (the subtitle is exactly `s29qzq`), the help sentence ("a text is cut off at {c 0}") and `test_c0_empties_the_whole_text`, renamed `test_c0_cuts_off_its_own_run`. Also measured: `{c a:}`-style character names end in a colon and are read as names (`_dash_graph_text_runs` looks one brace ahead); codes 9, 10 and 13 are laid out by twoway's SVG writer (spaces, line breaks), so the fixture comparison skips them; Stata 19 decodes `\uXXXX` in a string literal, so the truth block spells each needle's backslash `char(92)`.
- Fixed (blocker): GT-02 to GT-05 searched the saved page for raw UTF-8 (`α Ré`, `μ mpg²`, `αFor`, `βb`, `βimm`, `γarr`), but bokeh's page JSON writes every non-ASCII character as a lower-case `\uXXXX` escape (measured on bokeh 3.9.0 with `file_html`: `"text":"\u03b1 R\u00e9 …"`), so the cases could never pass. The needles are now the escaped forms; the block's comment says why. ASCII needles (`{&amp;alpha}`, `"text":"abcd"`, `__dash_mlabstyle_s29ml`) were right.
- Fixed (major): 29-11's verify required `LC_ALL=C grep -c '[^ -~]' dash.sthlp` to print 0, but dash.sthlp:2039 already holds an em dash at `c96facd`; the check now covers only the new paragraphs.
- Checked at `c96facd`: `_apply_mlabel_opts` :9302 and its column choice :9385-9396, `_DASH_MLABEL_PREFIX` :3586, `_mlabel_value_labels` :9600, `_dash_filter_title` :24047 (:24058-24060), `_dash_filter_widget` :24115 with `_label` :24175-24177, `{ul:Tooltips.}` dash.sthlp:3036, copy-list anchors `"_DASH_ASCII_BLANKS",` :33001 and `"_dash_inert_tex",` :33278: all as quoted.
- Checked: batch 10. S29 edits S09's pass functions, `_apply_mlabel_opts`, `_dash_filter_title`, `_dash_filter_widget` and new functions; S28 calls the pass (second call over its chrome cells, keys `<name>__by__head|foot`, which S29's `split("__by__")` maps to the graph) and edits none of them; S30 edits colour functions only. One CORPUS case appended after S28's (R8). Tracking forms match section-01 (title, `Results that change`, stub header, subject). GT-06's note dedup holds across S28's second pass call (`_dash_warn_once` keys per render).
- Rejected: "refuse unknown SMCL under M5" — twoway accepts every text and draws unknown tags as typed (A32); M5 covers only what twoway refuses.
- The review pass applied both lenses.
- Ratified (ratification 06oct2026): index row 8 / register A34 (P1.11.4) answered "Mirror twoway". A text holding `{c 0}` is drawn empty, as twoway draws it; the C0/C1 control codes `{c #}` names are kept as those characters, not dropped. Rewritten to match: Overview, US-29.6, BR-29.1, BR-29.8, TR-29.2-TR-29.5, TR-29.17, the help paragraph (TR-29.16), Boundaries' Decisions, the Stata truth probes and GT-01/GT-07, the scanner and fixture stubs, AC-29.7, tasks 29-01/29-03/29-04/29-11, the CHANGELOG line, the BUGS.md Resolution, the commit threats and the closeout audit line.
- Added (ratification 06oct2026; rule 1): E11 and TR-29.19 enumerate every sink translated text reaches, with how each writes a control code at `c96facd` (measured on bokeh 3.9.0: the saved page, both embed paths, holds no raw C0/C1/U+2028/U+2029 character and `</script>` as `&lt;/script&gt;`). No sink fails to escape at `c96facd`, so no escaping fix is planned; the new `TestControlCodesAreEscapedAtEverySink` (seven tests, nine ids) and one Chrome test pin each sink type, and Risk factor 7 names the hazard.
- Added (ratification 06oct2026): `html.unescape` drops `&#1;`/`&#x1b;` and maps `&#128;`-`&#159;` through cp1252 (measured), so the run reader decodes numeric references itself (TR-29.14) and gains `test_control_codes_are_kept` (five reader tests, was four).
- Added (ratification 06oct2026): research measured `{c 0}` only at the start of a tick label (`{c 0}|`), so "empties the whole text" and "truncates at the NUL" were not told apart. GT-01 and the extractor now measure `s29qzq{c 0}x`, `a{c 0}b`, `{bf:a}{c 0}` and a two-line title; task 29-03 stops and reports if twoway draws any of their text.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:101 (P1.11) reads: "`{bf:}`, `{it:}`, `{sup:}`, `{&beta}` and `{c #}` are drawn literally." GAPS2.md:868 (D3, Gap) reads: "dash translates no SMCL: `title("{bf:Bold} {&alpha} R{sup:2}")` reaches `Title.text` unchanged." GAPS2-J2 (:1735) adds the font tags `{stSerif:}` and `{fontface}`. twoway reads all of it as graph text (Stata's `graph_text.sthlp`). Measured at `c96facd`:

- **Saved page, Python** (`test_mode_parity._spec` with `title("{&alpha} R{sup:2} α")`, `subtitle("{bf:Whole bold}")`): `Title.text` is `'{&alpha} R{sup:2} α'`, the subtitle `Label.text` is `'{bf:Whole bold}'` with `text_font_style` `'normal'`; the page holds `{&amp;alpha}` and `{bf:Whole bold}` once each.
- **Saved page, Stata** (`scripts/stata_slot.sh`, scratch `s29p2.do`/`s29p3.do`): `dash scatter mpg weight, title(<char(123)>bf:a<char(125)>b)` writes `{bf:a}b`; `title("a{c 1}b{c 0}c{c 129}d")` writes `"text":"a{c 1}b{c 0}c{c 129}d"`; `mlabel(s29ml)` with `s29ml = cond(foreign, "{&beta}b", "{bf:Bx}")` writes the raw column (`{&amp;beta}b` 22 times, `{bf:Bx}` 52 times) and no derived column.
- **Every sink, both modes** (research `both_modes.py`, payload `{bf:B} {&alpha} R{sup:2}`): the same raw text on `Title.text`, `Label.text`, `LinearAxis.axis_label`, `major_label_overrides`, the tick-label map, `LegendItem.label`, `Legend.title`, `ColorBar.title`, tooltip row names, filter titles and dropdown options, in the saved page and the served app alike; scatteri and pcarrowi labels likewise (research critic addition 1).

twoway draws `T1 ` + bold `Bold` + ` α R` + raised `2` …, a variable label `{&mu} mpg{sup:2}` as `μ mpg²`, a value label `{it:Dom}` as an italic panel title, and an mlabel string `{&beta}b` as `βb` (research §2, truth1-4).

**After this section** one scanner, `_dash_graph_text`, reads Stata's graph-text grammar as twoway 19.5 does (measured, Stata truth): `{bf:}`, `{it:}`, `{sup:}`/`{superscript:}`, `{sub:}`/`{subscript:}`, `{stSans:}`, `{stSerif:}`, `{stMono:}`, `{stSymbol:}`, `{fontface "name":}`, each tag's colon-less form that runs to the end of the line, the 148 `{&name}` symbols and the `{c #}`, `{c 0x#}`, `{char #}` and `{c name}` characters. It is iterative and linear in the text's length (100,000 `{` in 0.030 s in the scratch prototype). Its output is Unicode, with the text's whole style and font set only where the markup covers the whole text (register P1.11.1/A31); what one Bokeh text cannot draw (a style on part of a text, a raised run with no Unicode form) is drawn in the text's own style, on the line, with one note per graph and kind of text through S06's channel. Every result passes `_dash_inert_tex` last. It is applied once per sink:
- by extending S09's canvas-text pass `_dash_finish_graph_text`, which already runs last in each mode, to titles, subtitles, notes, captions, axis titles, tick labels and the tick-label map, legend keys and titles, by() panel titles and the colour key;
- to the marker-label column in `GlyphMapper._apply_mlabel_opts`, decided over the whole dataset so every by() panel and every filter move keeps the same columns (both modes);
- to the dash-only DOM text the register names (P1.11.3/A33): filter titles, dropdown options taken from value labels and tooltip row names, with style tags removed. KPI and dashboard titles, `tabs()`, string data, value-label tooltip columns and the CSV stay raw.

Other SMCL (`{hline}`, `{cmd:}`, `{ccl}`, links) is drawn as typed (P1.11.2/A32, P2.47). As twoway does (P1.11.4/A34, ratification item 8, answered 06oct2026 "Mirror twoway"), a text holding `{c 0}` is drawn empty and the C0/C1 control codes `{c #}` names are kept as those characters; every sink they reach carries them escaped (`\uXXXX` in JSON and JS strings, HTML-escaped where HTML is written), which TR-29.19 enumerates and pins. A new "Text in graphs" help paragraph says all of it.

**Why one section.** P1.11's TeX half (S09, batch 3) built the pass, its sink table and both call sites; the manifest gives S29 the translator and forbids it `_build_sources_and_figures` and `_generate_app_source`. The marker-label column and the DOM sinks are the same rule reaching the two kinds of text the pass cannot see (data columns and widgets built after it). The translator is not idempotent (`{c -(}bf:x{c )-}` → `{bf:x}` → bold `x`), so every sink takes raw text exactly once; S19, S28 and S56 build raw text for it.

**Test order and commit rule (rule 7, D1).** Task 29-01 writes every regression test of this entry (pytest and the S29 truth block), runs them against the unmodified tree and saves `$S/29-P1.11b-failure.txt`; it never commits. Tasks 29-02 and 29-03 build the truth (reader, extractor, fixture); 29-04 to 29-07 make the fix; 29-08 and 29-09 flip the pinned tests; 29-10 and 29-11 register the names and write the help. Task 29-12 closes the entry, replaces the marker, runs the full suite through the queue and makes the section's one commit, `(WP-30 P1.11b)`. No test-only commit exists and no commit is red.

## Risk: [yellow] — a hostile-input parser on every graph text in two renderers, edits to three CRITICAL symbols and to S09's pass, and a translator that must never run twice on one text

**Why.** Every user string on a graph passes through new parsing code; a wrong decision changes text silently, a second translation changes it again, and a slow scanner is a denial of service on a served app.

**Risk factors.**
1. `GlyphMapper._apply_mlabel_opts` is CRITICAL (16 impacted, 10 direct, 10 processes; the 11 call sites are `map_*`, partly `UNKNOWN` through dispatch); `_dash_filter_title` and `_dash_filter_widget` are CRITICAL (5 impacted, 3 direct, 10 processes each); `ServerAppBuilder._glyph_layer_lines` is HIGH (4). `_mlabel_column_kind` (CRITICAL, 17) is read, not edited.
2. Non-idempotence: a sink translated twice (a shared saved source drawn by two layers, a model reached from two figures, a later section that translates and then hands text to the pass) turns escaped braces into live markup.
3. The served move replaces a layer's data wholesale (`_live.data = … dict(_new.data)`, dash_render.py:36030-36031). If the marker-label decision depended on the rows in view, a move to rows without markup would drop the column the live `LabelSet` names and blank every label.
4. A quadratic scanner: a naive "find the matching brace" per `{`, a regex per character, or run text grown by `+=` is quadratic on `{{{…` (prototype: 0.29-0.38 s for 100,000 `{` with `+=`, 0.030 s with piece lists).
5. Bokeh's text-style defaults differ per model (Title bold, axis label, ColorBar and Legend titles italic, measured on 3.9.0), and S15 resets some; a pass that wrote `normal` would undo S15.
6. Five pinned tests assert raw SMCL (E9) and one area cscript case (JSE-64).
7. Mirrored control codes (A34 as ratified 06oct2026) put U+0001-U+001F, U+007F and C1 code points into translated text; a sink that wrote that text into HTML or a JS literal without escaping would let a control code, a quote or `</script>` break out of a string or a script element.

**Mitigation.**
1. Each CRITICAL edit is one call or one changed line (TR-29.9, TR-29.10); impact is run at the batch base and reported (E10). The mapper change adds columns only where the markup exists; `test_no_markup_no_new_column` and the single-y digest pin the rest.
2. The pass keeps S09's per-model mark and `seen` set; the mapper translates a derived column only where it creates it (inside `if text_col not in source.data`); `test_a_translated_model_is_never_translated_again` and `test_a_column_already_derived_is_not_translated_again` pin both. The help and AGENTS note (closeout) state the raw-once rule.
3. The marker-label decision reads `self.dataset` (the whole frame in both modes, dash_render.py:29248 and :34806), cached per variable; `test_the_decision_reads_the_whole_dataset` and `test_a_served_move_keeps_the_translated_column` pin it.
4. Two linear passes over the positions of `{`, `}` and `:` only, no recursion, piece lists joined once; `TestLinearTime` bounds nine hostile shapes at 1 s each and 1,000,000 `{` at 5 s.
5. A style or font property is written only when the markup asks (style `bold`/`italic`, a font name); `normal` is never written. `test_style_is_set_only_where_markup_asks` pins it.
6. Each flip keeps the test's purpose (the label is text, never markup) and changes only the expected string; task 29-08 re-measures the red list after the fix and flips nothing it did not see red.
7. Translated text reaches only sinks that already escape (E11, measured); TR-29.19 forbids any other route, and `TestControlCodesAreEscapedAtEverySink` plus `TestInChrome::test_control_codes_and_script_text_stay_text` pin each sink type with a payload of control codes, raw U+0085/U+009B/U+2028/U+2029, quotes and `</script>`.

## Dependencies

- **Depends on: 06** (one note channel, batch 2): notes are `warnings.warn("dash: …")` through `_dash_warn_once` inside `main()`, printed by `_dash_note_scope` as `(note:  dash: …)` with braces SMCL-escaped (S06 TR-06.1-06.3); tests count `(note:` text. **09** (TeX half, batch 3): `_DASH_GRAPH_TEXT_SINKS`, `_DASH_GRAPH_TEXT_DONE`, `_dash_graph_text_models`, `_dash_graph_text_props`, `_dash_finish_text_value`, `_dash_finish_graph_text`, its two call sites and its copy-list line (S09 TR-09.1-09.7). **15** (scheme chrome, batch 5): the default text styles (centred unbolded title, upright axis titles) that S29 overrides only when the markup asks, and subtitle/note/caption as `Title` models (`_dash_textbox_place`). Also used, landed earlier: S01's entry `P1.11b`, its `WP30_OPEN` key, the marker `<!-- WP-30 P1.11b -->` (Results that change), the S29 stub block and the map anchor `# WP-30 S29 (P1.11b): SMCL in graph text (P1.11 part b)`; S02's path-free extractor form; S08's `_apply_mlabel_opts` (sizes, gap); S19's raw keys and titles; S23's served-note relay (the pass's notes raised in `make_document` reach Stata through it).
- **Blocks: 56** (`text()`/`ttext()`): its Labels are built raw before the pass and translated by it.
- **Parallel batch: 10** with S28 (by() panel labels and overall text) and S30 (colour grammar). **Merge order S28, S29, S30**: S29 lands after S28, so its pass covers S28's new sinks on the merged tree.
- **Can run with S28 and S30.** S28 edits `_build_sources_and_figures`, `_dash_facet_label`, `DashRenderer._facet_label` and the template's by() titles; S30 edits `translate_mcolor`, `parse_color_alpha`, `OptionTranslator.stata_colour`, SchemeParser's colour methods and the scheme extractor. S29 edits none of them (index Batch 10).

## Evidence

All anchors are at `c96facd` (`dash_render.py` 37,689 lines). S09's names do not exist at `c96facd`; their text is S09's TR-09.1-TR-09.7. Earlier batches (S08 in `_apply_mlabel_opts`, S09, S15, S17, S18, S21, S23) move lines before batch 10, so symbols and quoted text are authoritative; re-find each anchor by text.

### E1. The pass S29 extends (S09, batch 3)

S09 adds, directly after `_dash_inert_tex` (dash_render.py:24012-24043) and before `def _dash_filter_title` (:24047): the sink table `_DASH_GRAPH_TEXT_SINKS` (rows `(class, prop, how)` for Title, Label, Axis `axis_label` and `major_label_overrides`, ColorBar `title` and `major_label_overrides`, Legend `title`, LegendItem `label`, the `CustomJSTickFormatter` label map), the mark `_DASH_GRAPH_TEXT_DONE = "_dash_graph_text"` (a Python attribute, never serialised), the walk `_dash_graph_text_models(fig)` (title, the five side lists, each model's formatter, each Legend's items; never `references()`), `_dash_graph_text_props(model)`, `_dash_finish_text_value(value, how) -> (new, changed)` and `_dash_finish_graph_text(figures)`, called once at the end of `DashRenderer._build_sources_and_figures` and once in the generated `make_document` after `_dash_share_by_scales`. Figure keys are `<name>` or `<name>__by__<i>` in both modes (:31541, :31600, :35623), which S09 reserves for S29 to find a panel's graph. S09's copy-list line sits after `"_dash_inert_tex",` (:33278).

### E2. Marker labels: where the column is chosen, and why the decision must not depend on the rows in view

`GlyphMapper._apply_mlabel_opts` (dash_render.py:9302) draws a string column as it is and derives a text column for anything else (:9384-9396):

```python
9385         text_col = values_col
9386         _is_text, _miss = self._mlabel_column_kind(source.data[values_col])
9387         if not _is_text:
9388             _kind = getattr(self, "date_vars", {}).get(mlabel_var)
9394             _vlabels = ({} if _kind else self._mlabel_value_labels(mlabel_var))
9395             text_col = f"{_DASH_MLABEL_PREFIX}{mlabel_var}"
9396             if text_col not in source.data:
```

The comment above it (:9378-9384) states the rule this section must keep: "the derived one ALWAYS exists, named by the variable alone: a served filter redraws a mapper-built source through the mapper, and a column that existed only while a missing value was in view would leave the live LabelSet naming a column its redrawn source no longer has." The served move copies the redrawn data wholesale (:36030-36031):

```python
                    _live.data = _dash_keep_jitter(
                        dict(_new.data), _orig_src_data.get(id(_live), {}))
```

The saved page's filter script subsets every column of the original data, derived ones included (`_FILTER_JS`, :18760-18767: `const _dc = Object.keys(_od); … for (const col of _dc) { _nd[col].push(_od[col][i]); }`). The mapper holds the whole frame in both modes: saved `self.mapper.dataset = self.df` (:29248), served `_DASH_MAPPER.dataset = df` (:34806, generated: "the whole frame, not a filter's rows"); the served mapper is one module-level `GlyphMapper` (:33479), copied by source with its class (:33436). `_mlabel_column_kind` (:9607) returns `(True, zeros)` for a column of strings (:9625-9629) and is also read by `_mlabformat_column` (:9562); it is not edited.

Immediate labels reach the same applier as a reserved string column, one source per clock group (`_immediate_labels`, :14409-14418):

```python
14409        col = f"{_DASH_RESERVED_PREFIX}_{ptype}{_DASH_LABEL_SUFFIX}"
14411            lab_src = ColumnDataSource({
14414                col: [labels[i] for i in rows],
14416            opts = dict(options, mlabel=col, mlabposition=pos)
14418            self._apply_mlabel_opts(fig, lab_src, opts, xcol, ycol)
```

That column is not in the dataset, so its decision reads its own source (static: immediates draw from their own values, generated lines :35059-35062).

### E3. The dash-only DOM sinks

- Filter titles, every widget, both modes, go through `_dash_filter_title` (:24047-24064; callers FilterBuilder :19485, :19558, :19623 and the template :35752):

  ```python
  24058    raw = str(label or "").strip() or str(fallback)
  24059    if ftype != "dropdown":
  24060        raw = _dash_inert_tex(raw)
  24061    if ftype == "slider" and not raw.endswith(("≥", ">=")):
  24062        raw += " ≥"
  ```

- Dropdown option labels: `_dash_filter_widget`'s nested `_label` (def :24175) returns `vlabels[rv]` (:24177) or `vlabels[k]` (:24185) for a value-labelled value and `rv` (:24189) for a string value; options are then grouped by that text (DISCOVERY Q26, :24194-24204).
- Tooltip row names: `_dash_build_hover` adds `HoverTool(tooltips=_flds, …)` with `(label, field)` pairs (:27300, :27424); the label is a DOM text node (test_label_sinks.py docstring). No code rewrites tooltips after the figure is built.
- Raw by the register (P1.11.3): KPI cards and the dashboard title (`Div`, HTML), `TabPanel.title`, string values (data), `_hover_label_vars` value-label columns, the CSV.

### E4. Notes and their reach

`_dash_warn_once(key, message)` (:15363-15368) raises a `UserWarning` once per render (`_DASH_NOTED`, reset by `_dash_reset_notes` in both modes); the served app gets both through `_shared_stat_lines` (:33541). After S06 they print as `(note:  dash: …)` with braces escaped; after S23 the served app's `make_document` notes reach Stata at build. Existing graph notes read `dash: graph '<name>': …` (:3109, :20100).

### E5. Bokeh's text-style properties (3.9.0, measured; 3.8.0 is Stata's interpreter)

| Model | Style, font property | Default style |
|---|---|---|
| Title | `text_font_style`, `text_font` | bold |
| Label | `text_font_style`, `text_font` | normal |
| Axis title / tick labels | `axis_label_text_font_style`, `axis_label_text_font` / `major_label_text_font_style`, `major_label_text_font` | italic / normal |
| ColorBar title / labels | `title_text_font_style`, `title_text_font` / `major_label_text_font_style`, `major_label_text_font` | italic / normal |
| Legend title / keys | `title_text_font_style`, `title_text_font` / `label_text_font_style`, `label_text_font` | italic / normal |
| LabelSet | `text_font_style` (a dataspec: `field("col")` accepted, measured), `text_font` | normal |

One text model carries one style, one font and one baseline: this is why inline runs are approximated (register A31; no MathJax route, S09).

### E6. twoway truth (StataNow 19.5, `graph export … .svg`, runs read from `<tspan>` style and `dy`)

From research §2 (truth1-4.do, measured) and this section's probe `s29p1.do` (`scripts/stata_slot.sh`, tick labels of one `scatteri`, read with research `svgruns.py`):

```
{it:{bf:x}} -> bold x          {bf:a}{bf:b} -> bold 'ab'       {bf:abc -> literal '{bf:abc'
a {bf}b -> 'a ' + bold 'b'     {it}a{bf}b -> italic a, bold b  {bf:{it:both}} -> italic (innermost wins)
{bf:a{it:b}c} -> bold a, italic b, bold c                      {sub:{sup:x}} -> raised x
{sup:{&alpha}} -> raised α     {superscript:2}{subscript:x} -> raised 2, lowered x
{bf:}, {bf} -> nothing         {BF:x} -> literal               { bf:x}, {bf :x} -> bold x
{c 128}{c 150}{c 169}{c 0x41} -> '€–©A' (cp1252)   {c 999}, {c 256}, {c 0XE9} -> literal   {c  233} -> é
{c -(}bf:x{c )-} -> literal '{bf:x}' (never re-read)   {&alpha;}, {& alpha}, {&alpha:x} -> literal
{c 1}|, {c 31}|, {c 129}| -> raw control + '|'    {c 0}| -> the whole label empty
{fontface "Courier New":fx} -> Courier New        {fontface "Courier"}all -> Courier
multi-line title("{bf:a}" "b") -> line 1 bold, line 2 normal (separate <text>)
{cmd:x} {hi:x} {hline 3} {ccl pi} {dup 3:ab} {center:c} links -> rendered by twoway (A32: dash draws them as typed)
s29p1: {foo:{bf:x}} -> '{foo:' + bold 'x' + '}'     {bf:a{foo}b} -> bold 'a{foo}b'     {bf:a{zz:q}b} -> bold 'a{zz:q}b'
       {it:a{bf}b}c -> italic a, bold b, 'c' normal  {it:a{bf:b}c}d -> italic a, bold b, italic c, 'd'
       {bf:a{sup:2}} -> bold a, bold raised 2         { &alpha}, {&alpha } -> α
       {c 233 }, { c 233}, {char 0xe9} -> é           {c 34}{c 36}{c 96}{c 123}{c 125} -> '"$`{}'
       a{c 127}b -> raw DEL                           {stSymbol:{&alpha}b} -> Symbol '∈±β'
       {stSerif:a}{stSerif:b} -> Times 'ab'           {it:{bf:a} -> '{it:' + bold 'a'
       {bf:a}}b -> bold 'a' + '}b'                    title("{bf}a" "b") -> bold 'a', 'b' (no carry)
       subtitle("{it:x}" "{it:y}") -> both lines italic
```

So: a tag is `{`, optional blanks, a case-sensitive name, optional blanks, then `:` (it wraps text up to its matching `}`) or `}` (it holds to the end of the line, scoped to the tag that encloses it); an unknown name is literal text, with `{foo}` one literal unit and `{foo:` a literal frame whose content is still read and whose `}` is printed; an unclosed tag is literal; bold and italic exclude each other, the innermost wins in each of style, level and font. Sizes: sup/sub at 0.583 of the font, raised 0.524 em / lowered 0.143 em. Tables measured (research scratch, to be regenerated by this section's extractor): 148 `{&name}` symbols, `{c #}` for 32..255 (128..159 follow cp1252; 129, 141, 143, 144, 157 stay C1 controls), 78 `{c name}` forms of smcl.sthlp, 88 `{stSymbol:}` characters (`a`→α, `c`→χ, `j`→ϕ, `'`→∍, `@`→≅ …). twoway reads `{&alpha}` inside `{stSymbol:}` as its UTF-8 bytes in the Symbol encoding (`∈±`); dash draws the symbol (Boundaries, documented difference). Control codes: `{c 1}`, `{c 31}` and `{c 129}` are written raw (research p1-11.md:89, :97), and `{c 0}|` leaves the whole label with no text (research p1-11.md:89, a tick label). That is the only `{c 0}` measurement: with `{c 0}` first, "empties the label" and "ends the label at the NUL" give the same result, so GT-01 and the extractor add `{c 0}` after text and in a two-line title (Stata truth); the ratified rule (index row 8) is "a label holding `{c 0}` is emptied".

### E7. A scratch prototype of the scanner (03oct2026; `s29/proto.py`, not repo code)

The two-pass design of TR-29.4, with tables from the research scratch, reproduced all 31 measured cases above (`cases 31 mismatches 0`). Timings, piece lists joined once:

```
100k {  0.030s    1M {  0.367s    100k }  0.028s    1M }  0.293s
50k {&  0.028s    500k {&  0.233s  25k {bf: (unclosed)  0.026s   250k {bf:  0.310s
10k-deep closed nesting 0.013s   20k {fontface "  0.183s*   {c 9×5000}  0.000s   1 MB plain  0.003s
(* with run text grown by +=; the same variant took 0.277-0.385 s on the 100k shapes)
```

### E8. Today's hostile and control-character behaviour (Stata, `s29p3.do`)

```
dash scatter mpg weight, title("<5000×{>x")        rc 0, 2.861 s, page 1,306,192 bytes, braces drawn
dash scatter mpg weight, title("a{c 1}b{c 0}c{c 129}d")   rc 0, "text":"a{c 1}b{c 0}c{c 129}d"
```

In a `log using` text log, a command inside an `if {}` block is echoed with its macros unexpanded (`title("`s29t'")`, `s29p2_inner.log`), so a needle built with `char()` never appears in the echo.

### E9. Tests that pin today's behaviour (flipped in tasks 29-08 and 29-09, never deleted)

Each asserts the raw SMCL that twoway does not draw:
- `test/test_immediate_values.py::TestScatteriDrawsItsRecords::test_the_label_is_text_not_markup` — `list(ls.source.data[_text_field(ls)]) == [payload]` with `payload = '<img src=x onerror=alert(1)>{bf:X}"],"expr":"1'`.
- `test/test_immediate_values.py::TestBothModesDrawTheSame::test_a_scatteri_label_reaches_the_served_page_as_text` — `got == [(-4, 0, [payload])]` with `"</script><script>alert(1)</script>{bf:X}"`.
- `test/test_pccapsym_pcarrowi.py::TestMapPcarrowi::test_the_label_is_text_not_markup` — the same assertion for pcarrowi.
- `test/test_textbox_multiline.py::TestTextboxAdversarial::test_macro_smcl_markup_and_python_in_a_string_arrive_as_written` — title and note `== payload`, which holds `{bf:\"z\"}`.
- `test/test_json_escaping.cscript` JSE-64 — `_jr_page_check()` compares the Title and Label texts with `jr_t64`, which opens `{bf:"z"}`.

Checked and not affected (no recognised directive, or no rendered text): `test_label_sinks.py` (payloads `{safe}`, `@x{safe} $index`, `$$\href{javascript:alert(1)}{x}$$`, `\[\style{…}{x}\]` hold only unknown tags, drawn as typed); `test_adversarial_matrix.py:2835-2840` (a Select value); `test_twoway_option_parity.cscript` TP-14e (the spec JSON in `dash_json_zq14h`); `test_adversarial.cscript` P19-24..26 and `test_help_claims_7.cscript` HC7-09 (refusal echoes); `test_parser.cscript` p1a77/p1a78 (a function expression); `test_echo_text.cscript` (Mata echo). Task 29-08 re-measures this list on the fixed tree.

### E10. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, index at `c96facd`)

| Symbol | Edit | Risk | Direct callers / processes |
|---|---|---|---|
| `GlyphMapper._apply_mlabel_opts` | decision call, derived columns, two kwargs | CRITICAL (16) | 10: `map_*`, `_immediate_labels`, `_make_figure_body` (`UNKNOWN` through dispatch) |
| `GlyphMapper._mlabel_column_kind` | not edited (read) | CRITICAL (17) | `_apply_mlabel_opts`, `_mlabformat_column` |
| `_dash_filter_title` | one line | CRITICAL (5, 10 processes) | FilterBuilder `build_dropdown`/`build_slider`/`build_range`, template |
| `_dash_filter_widget` | the nested `_label`'s two value-label returns | CRITICAL (5, 10 processes) | `build_dropdown`, `build_slider`, `build_range` |
| `ServerAppBuilder._glyph_layer_lines` | two tuple appends | HIGH (4) | `_generate_app_source` |
| S09's `_DASH_GRAPH_TEXT_SINKS`, `_dash_graph_text_models`, `_dash_finish_text_value`, `_dash_finish_graph_text` | extended in place | measured at batch-10 base (expected HIGH/CRITICAL through the two builders) | `_build_sources_and_figures`, generated `make_document` |
| `svg_document` (scripts/svg_truth.py) | not edited; a sibling module added | HIGH (8) | — |
| new: `_dash_gt_char`, `_dash_gt_head`, `_dash_graph_text_runs`, `_dash_graph_text_parts`, `_dash_graph_text`, `_dash_graph_text_plain`, `_dash_finish_text_runs`, `_dash_graph_text_style`, `_dash_graph_text_note`, `GlyphMapper._mlabel_markup`, `GlyphMapper._mlabel_markup_rows`, the `_DASH_GT_*` tables, `_DASH_MLABSTYLE_PREFIX` | added | no callers yet | — |

No Stata or Mata program is edited (dash.ado passes the text through intact, research critic c1.do).

### E11. How a control code travels to each sink at `c96facd` (measured 06oct2026, bokeh 3.9.0)

A spec with `title("a\x01b\x1bc\x81d\x9de\x85\x9b\u2028\u2029</script><script>alert(1)</script>\"'\u03b1")` (the codes typed raw, since translation does not exist yet) through `test_mode_parity._standalone_page`: the page holds 0 characters in `[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u2028\u2029]`, 4 `<script` (as a plain title), 0 `<script>alert`, and the Title as `"text":"a\u0001b\u001bc\u0081d\u009de\u0085\u009b\u2028\u2029&lt;/script&gt;&lt;script&gt;alert(1)&lt;/script&gt;\"'\u03b1"`. The same payload in a bare-Bokeh `components()` script and `file_html` page (Title, axis label, legend label, tooltip row, `Select` title and option) gave 0 raw controls and only escaped `</script>`. Per sink:

| Sink | Path at `c96facd` | Escaping |
|---|---|---|
| Saved page, default layout: every canvas text, marker-label columns, `Select`/slider titles and options, tooltip rows | `DashRenderer._assemble_layout` → `file_html` (dash_render.py:32585) → bokeh/embed/elements.py:121-122 | `serialize_json`'s `PayloadEncoder` (bokeh/core/json_encoder.py:163, :170-172) keeps `JSONEncoder`'s `ensure_ascii=True`: C0, C1, U+2028/2029 and all non-ASCII become `\uXXXX`; then `html.escape(…, quote=False)` (`<`, `>`, `&`) inside `<script type="application/json">` |
| Saved page, `layout()` pages: the same models | `_render_bootstrap_html` → `components()` (dash_render.py:30989, written at :31115) → elements.py:177-181 | the same JSON, HTML-escaped, `'` → `&#x27;`, `\` doubled, in a single-quoted JS literal |
| Tick-label map | `CustomJSTickFormatter(args={"labels": json.dumps(_labels)})` (dash_render.py:22813) | `json.dumps` default `ensure_ascii=True`, read by `JSON.parse`; then one of the two rows above |
| Served app, the wire | Bokeh's protocol `serialize_json(self.payload)` (bokeh/protocol/message.py:380) | as the first row, without the HTML step (a websocket frame) |
| Served app, the generated source | the spec as base64 of `json.dumps(spec)` (dash_render.py:32817, :33911); `repr(filter_specs)` (:34814); constants `"%s = %r"` after a `literal_eval` round-trip (:33640-33643) | `repr` writes every non-printable character as `\x..`/`\u....`; graph text is translated inside `make_document`, so translated text never enters the source |
| HTML dash writes | `_dash_header_fragments` (:25467-25470), `_dash_kpi_card_html` (:17033-17036) | `html.escape`; raw text only (P1.11.3), so no translated text and no `{c #}` code reaches them |
| Notes, Stata output | `_dash_warn_once`; `_dash_display` (:26386) | non-printables become `?`; S29's notes hold no user text (TR-29.8) |

Not sinks of translated text: the CSV (raw, P1.11.3) and `_dash_write_stata_data`'s handoff file (dash_render.py:1766, `ensure_ascii=False`, so C1 and U+2028 are written raw there, which is valid JSON; written before the render, never HTML or JS). No sink above writes a control code, a quote or `</script>` unescaped, so S29 adds no escaping code; TR-29.19 keeps translated text on these paths.

## User stories

- **US-29.1** As a twoway user, I want `title("{&alpha} = R{sup:2}")`, `subtitle("{bf:Fuel economy}")` and `xtitle("{stSerif:Weight}")` drawn as twoway draws them, so the text on my dashboard is the text on my Stata graph.
- **US-29.2** As a twoway user whose variable and value labels hold graph-text markup (`{&mu} mpg{sup:2}`, `{it:Domestic}`), I want every place those labels appear on a graph — axis titles, legend keys, tick labels, by() panel titles, the colour key and marker labels — to show them as twoway does, in both modes and after any filter move.
- **US-29.3** As a twoway user, I want `scatter mpg weight, mlabel(name)` and `scatteri 2 2 "{&beta}"` labels with markup drawn translated, and a whole-bold label drawn bold.
- **US-29.4** As a dashboard publisher, I want a filter's title, a dropdown's value-label options and a tooltip's row names to read `μ mpg` rather than `{&mu} mpg`, while KPI cards, tab titles, string values and the CSV keep my text as stored.
- **US-29.5** As a twoway user, I want to be told once, without my text echoed, when dash cannot draw part of my markup (a bold word inside a title, a raised letter), and to read in the help exactly what is drawn and what is not.
- **US-29.6** As a dashboard publisher, I want hostile text (100,000 braces, deep nesting, control codes) handled in well under a second, with control codes drawn as twoway draws them but carried only as escaped text, and no TeX pair reaching the page.

## Business requirements

- **BR-29.1** Every graph-text directive twoway 19.5 draws (E6) is drawn with twoway's characters, in both modes: each of the 148 symbols, every `{c #}` from 1 to 255 (control codes included, as the characters twoway writes), every `{c name}`, the `{stSymbol:}` letters, and the measured edge cases' text; a text holding `{c 0}` is drawn empty, as twoway draws it.
- **BR-29.2** A text's whole style (bold or italic) and font are those twoway draws when the markup covers every visible character of it; otherwise the sink keeps its own style and font (S15's defaults stand).
- **BR-29.3** A raised or lowered run is drawn as Unicode superscript or subscript characters when every character has one; otherwise it is drawn on the line.
- **BR-29.4** Unknown tags, unclosed tags, stray braces and other SMCL are drawn as typed; escaped braces (`{c -(}`, `{c )-}`) are never read again; no text is translated twice.
- **BR-29.5** Where dash draws a text differently from twoway because of markup (a part styled, a run not raised), it prints one note per graph and kind of text, naming the graph and the kind and never the user's text; it prints nothing otherwise (M6) and refuses nothing (M5: twoway accepts all text).
- **BR-29.6** Marker labels from a string variable, value labels or an immediate layer are drawn translated, with per-label bold or italic, in both modes, on every by() panel and after any filter move.
- **BR-29.7** Filter titles, dropdown options from value labels and tooltip row names show the translated characters with style tags removed; KPI and dashboard titles, `tabs()`, string values (tooltips, dropdowns, data) and the CSV are unchanged.
- **BR-29.8** The C0/C1 control codes `{c #}` produces are kept (mirrored, A34 as ratified 06oct2026), and every sink they reach carries them, with quotes and `</script>`, escaped: `\uXXXX` in every JSON or JS string, HTML-escaped wherever HTML is written, valid JSON everywhere, so none can end a string, a script element or an attribute (TR-29.19); no TeX pair assembled by translation reaches a canvas sink; the saved page ships no MathJax for any of it.
- **BR-29.9** A page whose text holds no recognised directive is unchanged by this section (no new column, no style property, identical text).

## Technical requirements

- **TR-29.1 Tables.** Directly after S09's `_dash_finish_graph_text` (the last definition of S09's block) and before `def _dash_filter_title`, add module constants, every non-ASCII character written as a `\uXXXX` escape so look-alikes (Greek Α against Latin A) are reviewable:
  - `_DASH_GT_SYMBOLS`: name → character for every key of the fixture's `symbols` (148), transcribed by a scratch script from `test/fixtures/graph_text_truth.json`, never typed by hand.
  - `_DASH_GT_CNAMES`: name → character for every fixture `cnames` entry whose name is not a decimal or `0x` number (those are read by `_dash_gt_char`).
  - `_DASH_GT_STSYMBOL`: character → character for every fixture `stsymbol` entry whose output differs from its input.
  - `_DASH_GT_SUP`: `0-9` → `⁰ ¹ ² ³ ⁴-⁹`, `+` → `⁺`, `-` and `−` → `⁻`, `=` → `⁼`, `(` → `⁽`, `)` → `⁾`, `n` → `ⁿ`, `i` → `ⁱ`. `_DASH_GT_SUB`: `0-9` → `₀-₉`, `+` → `₊`, `-` and `−` → `₋`, `=` → `₌`, `(` → `₍`, `)` → `₎`.
  - `_DASH_GT_FONTS = {"stSans": "Helvetica, Arial, sans-serif", "stSerif": "Times, Times New Roman, serif", "stMono": "Courier, Courier New, monospace"}`.
  - `_DASH_GT_TAGS`: `bf` → `("style", "bold")`, `it` → `("style", "italic")`, `sup` and `superscript` → `("level", 1)`, `sub` and `subscript` → `("level", -1)`, `stSans`/`stSerif`/`stMono` → `("font", <the _DASH_GT_FONTS value>)`, `stSymbol` → `("font", "symbol")`.
  - `_DASH_GT_STYLE_PROPS`, rows `(class, prop, style_prop, font_prop, kind)`: `("Title", "text", "text_font_style", "text_font", "title, subtitle, note or caption")`, `("Label", "text", …same…)`, `("Axis", "axis_label", "axis_label_text_font_style", "axis_label_text_font", "axis title")`, `("Axis", "major_label_overrides", "major_label_text_font_style", "major_label_text_font", "tick label")`, `("ColorBar", "title", "title_text_font_style", "title_text_font", "colour key title")`, `("ColorBar", "major_label_overrides", "major_label_text_font_style", "major_label_text_font", "tick label")`, `("Legend", "title", "title_text_font_style", "title_text_font", "legend key or title")`, `("Legend", "items", "label_text_font_style", "label_text_font", "legend key or title")`, `("LegendItem", "label", None, None, "legend key or title")`, `("CustomJSTickFormatter", "args", None, None, "tick label")`.
  - Beside `_DASH_MLABEL_PREFIX` (:3586): `_DASH_MLABSTYLE_PREFIX = "__dash_mlabstyle_"` (it can never equal a `__dash_mlabel_` name: the two differ at their 12th character).
  - No module-level `re.compile`: compiled patterns cannot travel through the constants tuple; compile inside the functions (Python caches them).

- **TR-29.2 `_dash_gt_char(code)`** → the character `{c code}` draws, or `None` for 0: `chr(code)` for 1-127 and 160-255 (1-31 and 127 are the C0 controls and DEL, kept as twoway writes them raw); `bytes([code]).decode("cp1252")` for 128-159, and `chr(code)` (the C1 code point) where cp1252 has no character (129, 141, 143, 144, 157); `None` for 0, which empties the text (TR-29.3, TR-29.5). Register P1.11.4/A34 as ratified 06oct2026 ("Mirror twoway"); the fixture's `chars` is the truth for 1-255, and `test_char_codes` compares every code with it, so a C1 code twoway writes otherwise is caught there. The caller treats a code above 255 as an unknown directive.

- **TR-29.3 `_dash_gt_head(head, term)`** → the meaning of the directive whose text between `{` and its terminator is `head` and whose terminator is `term` (`":"` or `"}"`). `h = head.strip(" \t")`; then, in order:
  1. `h in _DASH_GT_TAGS` → `("open" if term == ":" else "set", dim, value)`.
  2. `re.fullmatch(r'fontface[ \t]+(?:"([^"]*)"|([^\s"]+))', h)` → the name, kept to `[A-Za-z0-9 _-]` (`re.sub`), cut to 64 characters, stripped, `None` if empty → `("open"|"set", "font", name)`.
  3. `term == "}"` and `re.fullmatch(r"&([A-Za-z0-9]+)", h)` with the name in `_DASH_GT_SYMBOLS` → `("emit", symbol)`.
  4. `term == "}"` and `re.fullmatch(r"(?:c|char)[ \t]+(\S+)", h)`: an argument matching `[0-9]{1,6}` or `0x[0-9a-fA-F]{1,6}` (lower-case `x`; `0XE9` is literal) is a code: `("empty",)` for 0 (`{c 0}`, `{c 00}`, `{c 0x0}`, `{char 0}`), `("emit", _dash_gt_char(code))` for 1-255, `("unit",)` above; an argument in `_DASH_GT_CNAMES` → `("emit", char)`; anything else `("unit",)`. The digit caps keep Python's int parsing linear (a 5,000-digit argument is literal).
  5. Otherwise `("unit",)` for `term == "}"` and `("frame",)` for `term == ":"`.

- **TR-29.4 `_dash_graph_text_runs(line)`** → a list of runs `(text, style, level, font)` for one line (no `"\n"` in it), `style` in `{"normal", "bold", "italic"}`, `level` in `{-1, 0, 1}`, `font` `None`, a family string or `"symbol"`. Plain loops only (no recursion, no nested `def`, no lambda). `sp` = the positions of `{`, `}` and `:` from one `re.finditer(r"[{}:]", s)`. A `{` at `sp[k]` has terminator `sp[k+1]` when that is `:` or `}`; otherwise it is a literal `{`.
  - **Pass 1, pairing.** Walk `sp` with index `k`. A `{` with a terminator: `act = _dash_gt_head(s[p+1:q], s[q])`, remember `acts[p] = (act, q)`; if `s[q] == ":"` push `p`; advance `k` by 2. A literal `{`: `k += 1`. A `}` not consumed as a terminator: if the stack is non-empty, pop it and add the popped position to `closed`; `k += 1`. A `:` not consumed: `k += 1`.
  - **Pass 2, emission.** `state = ("normal", 0, None)`, `frames = []`. Text between specials is emitted with the current state; while `state`'s font is `"symbol"`, literal text (only) is mapped with `str.translate` over a table built from `_DASH_GT_STSYMBOL`. A `{` in `acts` with `":"`: if `p in closed` and the action is `open`, push `(state, False)` and set the dimension; if `p in closed` and the action is `frame`, emit `s[p:q+1]` literally and push `(state, True)`; if `p not in closed`, emit `s[p:q+1]` literally and push nothing. A `{` with `"}"`: `set` changes the dimension in the current state; `emit` emits the character(s) unmapped; `unit` emits `s[p:q+1]`; `empty` ends the walk and the function returns `None` (the line holds `{c 0}`). A literal `{` emits `"{"`. An unconsumed `}`: if `frames`, pop `(saved, literal)`, emit `"}"` when `literal`, then `state = saved`; else emit `"}"`. An unconsumed `:` emits `":"`.
  - Runs keep a list of pieces per state and join each once at the end (E7). Adjacent equal states share a run; empty pieces are not stored.
  - Returns `None` instead of runs when pass 2 reaches an `empty` action (a `{c 0}` read as a directive; an escaped `{c -(}c 0{c )-}` is never one).
  - Docstring: the grammar of E6, `{c 0}` and the control codes as twoway draws them (A34 as ratified 06oct2026), the one documented difference (a symbol inside `{stSymbol:}` drawn as itself), the measured linear times, and that the function is not idempotent.

- **TR-29.5 `_dash_graph_text_parts(text)`, `_dash_graph_text(text)`, `_dash_graph_text_plain(text)`.**
  - `_dash_graph_text_parts(text)` → `(plain, style, font, flags)`: `str(text).split("\n")`, each line through `_dash_graph_text_runs`; when any line's runs are `None` the whole text is drawn empty and the result is `("", None, None, ())` (twoway empties a label holding `{c 0}`; the scope is the text one sink receives, all its lines, and the extractor's two-line case confirms it). For a run with `level != 0`: if every character is in the level's table or is whitespace, map it; else keep it and add `"level"` to `flags`. Over the runs whose text holds a non-blank character (all lines together): the set of styles; one style → `None` for `"normal"`, else that style; several → `None` and `"inline"`. The set of fonts (a `"symbol"` run counts as `None`): one → that font; several → `None` and `"inline"`. Lines joined with `"\n"`. `flags` is a sorted tuple.
  - `_dash_graph_text(text)` → `(_dash_inert_tex(plain), style, font, flags)`: the canvas result; `_dash_inert_tex` runs last on the joined text, so `{c S|}{c S|}x{c S|}{c S|}` or `{c 92}(y{c 92})` cannot form a live pair.
  - `_dash_graph_text_plain(text)` → `plain` alone (DOM sinks; `_dash_filter_title` applies the TeX breaker itself for slider titles).
  - Text holding no `{` is returned unchanged by `_dash_graph_text_plain` (BR-29.9; `test_text_without_markup_is_unchanged`); a raw control character already in the text (no `{c #}`) is kept as it is, like any other character.
  - `{c 0}` is the only way to empty a text: a DOM sink then shows an empty title or option (an emptied value label shares its empty text with any other, grouped by DISCOVERY Q26's rule), and a marker label is drawn as an empty string.

- **TR-29.6 S09's pass, extended in place.**
  - `_DASH_GRAPH_TEXT_SINKS` gains the row `("HoverTool", "tooltips", "tooltips")`; `_dash_graph_text_models(fig)` appends, after S09's models, every `HoverTool` in `fig.tools` (local import).
  - New `_dash_finish_text_runs(value, how)` → `(new, changed, results)`, S09's four kinds with `_dash_graph_text(v)[0]` in place of `_dash_inert_tex(v)` and each `_dash_graph_text` tuple appended to `results`; kind `"tooltips"`: a list of `(label, field)` pairs gets `(_dash_graph_text_plain(label), field)` for each string label, fields untouched, `results` empty; a string template is returned unchanged. S09's `_dash_finish_text_value(value, how)` becomes `return _dash_finish_text_runs(value, how)[:2]`, so S09's tests keep their meaning.
  - `_dash_finish_graph_text(figures)`: as S09's, plus: `graph = str(key).split("__by__", 1)[0]`; for a `Legend`, before its own props, `results` of every item's fixed label (`_dash_finish_text_runs(it.label, "value")[2]`, items still raw because the walk reaches them after the Legend) go to `_dash_graph_text_style(model, "items", results, fig)`; for each `(prop, how)`, `new, diff, res = _dash_finish_text_runs(…)`, `setattr` when `diff`, then `_dash_graph_text_style(model, prop, res, fig)`; when it applies a tick style on an Axis, `id(model.formatter)` joins a `styled_fmt` set, and a later `CustomJSTickFormatter` in that set drops its `"inline"` flag. Flags gather in `pending[(graph, kind)]`; after both loops, for each entry with flags, `_dash_graph_text_note(f"graph '{_dash_display(graph)}'", kind, flags)` in insertion order. The return value counts models whose text changed or whose style was set.
  - S09's mark, `seen` set, call sites and order are unchanged: no edit to `_build_sources_and_figures` or `_generate_app_source`.

- **TR-29.7 `_dash_graph_text_style(model, prop, results, fig)`** → `(kind, flags, applied)`. The row is the first of `_DASH_GT_STYLE_PROPS` whose prop equals `prop` and whose class (`getattr(bokeh.models, cls)`) the model is an instance of; no row → `(None, set(), False)`. `flags` = the union of the results' flags; `styled` = results with a style or font.

  | Row | Applied when | Otherwise |
  |---|---|---|
  | Title, Label, Axis `axis_label`, ColorBar `title`, Legend `title` | `results[0]` has a style or font: set each that is not `None` | nothing |
  | Axis / ColorBar `major_label_overrides` | every result has the same `(style, font)` with one not `None`, the ticker is a `FixedTicker` with at least one tick, every tick (as `float`) is a key of the overrides, and the axis is not counted (`id(model)` not in `{id(e["ax"]) for e in getattr(fig, "_dash_count_entries", None) or ()}`) | `"inline"` when `styled` |
  | Legend `items` | every fixed-label result has the same `(style, font)` with one not `None` | `"inline"` when `styled` |
  | LegendItem `label` | never (the Legend decides) | no `"inline"` |
  | CustomJSTickFormatter `args` | never (its axis decides) | `"inline"` when `styled` (dropped by TR-29.6 when the axis applied) |

  A `normal` style is never written (Risk 5).

- **TR-29.8 `_dash_graph_text_note(where, kind, flags)`** → raises at most one note per `("graph_text", where, kind)` and render through `_dash_warn_once(key, message, stacklevel=3)`. Message: `f"dash: {where}: " + "; ".join(parts) + " (help dash, Text in graphs)."`, `parts` in this order: with `"inline"`, `f"{{bf:}}, {{it:}} or a font tag on part of a {kind} is drawn in that text's own style and font"`; with `"level"`, `f"{{sup:}} or {{sub:}} around a character with no raised or lowered form in a {kind} is drawn on the line"`. `where` is `graph '<name>'` (pass) or `mlabel(<var>)` or `<type> labels` (mapper; TR-29.9); names pass `_dash_display`. No user text.

- **TR-29.9 Marker labels (`GlyphMapper`; edit `_apply_mlabel_opts` once, warn CRITICAL first).**
  - `_mlabel_markup(self, var, texts, cache_key=None)` → `None` when `_dash_graph_text_plain(t) == t` for every distinct string `t` of `texts`; else `(need_style, font)`: `need_style` when any `_dash_graph_text(t)[1]` is not `None`; `font` the one non-`None` font when every result's font is that one, else `None` (and `"inline"` if fonts differ); with any flags it calls `_dash_graph_text_note(where, "marker label", flags)` (`where` = `mlabel(<var>)`, or `<type> labels` when `var` is `_DASH_RESERVED_PREFIX + "_" + <type> + _DASH_LABEL_SUFFIX`). A non-`None` `cache_key` memoises the answer in `self._dash_gt_markup` (a dict created with `getattr(self, "_dash_gt_markup", None)`).
  - `_mlabel_markup_rows(self, texts)` → `(out, styles)`: each distinct string translated once by `_dash_graph_text` (a per-call dict, then a mapper-level dict `self._dash_gt_rows` cleared when it passes 65,536 entries); `out` holds the translation (a non-string is kept), `styles` `"normal"` or the whole style.
  - In `_apply_mlabel_opts`, after `_is_text, _miss = …` (:9386): the universe of texts is, for a string column, the whole dataset's column (`self.dataset[mlabel_var]` when `getattr(self, "dataset", None)` holds it, `cache_key=(mlabel_var, id(self.dataset))`), else the source's own column (immediates; no cache); for a value-labelled non-date column, `list(_vlabels.values())` (`cache_key=(mlabel_var, "vl")`); otherwise none (numbers and dates hold no markup). With a non-`None` answer: a string column's text column becomes `f"{_DASH_MLABEL_PREFIX}{mlabel_var}"`; `style_col = f"{_DASH_MLABSTYLE_PREFIX}{mlabel_var}"` when `need_style`. The translated text (and style) columns are written only where `text_col not in source.data` — for a string column in a new guarded block, for value labels inside the existing block, on `rendered` before it is stored — never over an existing column (the saved page shares one source among layers, Risk 2). The `LabelSet` kwargs gain `text_font_style=field(style_col)` (`from bokeh.core.properties import field`) and `text_font=font` when set. `mlabformat()` already returns the default column for strings (`_mlabformat_column`, :9562-9565) and for value labels (its `if self._mlabel_value_labels(var): return default_col`).

- **TR-29.10 The dash-only DOM sinks (register P1.11.3).**
  - `_dash_filter_title`: `raw = _dash_graph_text_plain(str(label or "").strip() or str(fallback))`, then S09's slider-family `_dash_inert_tex` and the `≥` as today. The docstring adds the rule and the reason.
  - `_dash_filter_widget`'s `_label`: the two value-label returns become `_dash_graph_text_plain(vlabels[rv])` and `_dash_graph_text_plain(vlabels[k])`; a string value (`return rv`) stays raw. Values that now share one display text become one entry (DISCOVERY Q26's existing rule).
  - Tooltip row names: through the pass (TR-29.6), so `_dash_build_hover` is not edited.
  - Not edited: KPI builders, `_build_kpi_html`, the dashboard header, `TabPanel` titles, `_hover_label_vars`/`_dash_add_hover_text`, the CSV writers.

- **TR-29.11 Served copy lists (R2 row S29).** In `_glyph_layer_lines`' constants tuple, after `"_DASH_ASCII_BLANKS",` (:33001), a comment `# Graph-text markup (WP-30 P1.11b).` and `"_DASH_GT_SYMBOLS", "_DASH_GT_CNAMES", "_DASH_GT_STSYMBOL",` / `"_DASH_GT_SUP", "_DASH_GT_SUB", "_DASH_GT_FONTS", "_DASH_GT_TAGS",` / `"_DASH_GT_STYLE_PROPS", "_DASH_MLABSTYLE_PREFIX",`. In the functions tuple, after S09's `"_dash_graph_text_props", "_dash_finish_text_value",` line, a comment `# The graph-text scanner and its pass helpers (WP-30 P1.11b).` and `"_dash_gt_char", "_dash_gt_head", "_dash_graph_text_runs",` / `"_dash_graph_text_parts", "_dash_graph_text", "_dash_graph_text_plain",` / `"_dash_finish_text_runs", "_dash_graph_text_style", "_dash_graph_text_note",`. GlyphMapper's two methods travel with the class (:33436). Every value is `ast.literal_eval`-safe.

- **TR-29.12 Both modes, no JavaScript twin.** Canvas text: the pass runs last in each mode (S09); no served callback writes canvas text and the saved stale cue writes the pass's text plus a constant suffix (`_FILTER_JS` :19341-19344), so text and style hold after a move. Marker labels: derived columns are data; the saved filter script subsets them with every column (E2) and the served redraw re-derives them from the same whole-dataset decision. DOM sinks are built once. `_FILTER_JS` and every other JS constant are unchanged.

- **TR-29.13 Registries.** Under `# WP-30 S29 (P1.11b): SMCL in graph text (P1.11 part b)` in `test/function_test_map.py`, alphabetically: `'GlyphMapper._mlabel_markup': 'test/test_graph_text.py::TestMarkerLabels::test_the_decision_reads_the_whole_dataset'`, `'GlyphMapper._mlabel_markup_rows': 'test/test_graph_text.py::TestMarkerLabels::test_each_distinct_label_is_translated_once'`, `'_dash_finish_text_runs': 'test/test_graph_text.py::TestThePass::test_finish_text_runs_returns_each_result'`, `'_dash_graph_text': 'test/test_graph_text.py::TestTheScanner::test_the_result_passes_inert_tex_last'`, `'_dash_graph_text_note': 'test/test_graph_text.py::TestTheNote::test_one_note_per_graph_and_kind_naming_no_user_text'`, `'_dash_graph_text_parts': 'test/test_graph_text.py::TestTheScanner::test_whole_style_and_font_only_when_markup_asks'`, `'_dash_graph_text_plain': 'test/test_graph_text.py::TestDomSinks::test_plain_text_strips_style_and_keeps_tex'`, `'_dash_graph_text_runs': 'test/test_graph_text.py::TestTheScanner::test_measured_edge_cases'`, `'_dash_graph_text_style': 'test/test_graph_text.py::TestThePass::test_style_is_set_only_where_markup_asks'`, `'_dash_gt_char': 'test/test_graph_text.py::TestGraphTextTruth::test_char_codes'`, `'_dash_gt_head': 'test/test_graph_text.py::TestTheScanner::test_heads_name_known_directives_only'`. No Stata program or Mata function: `test/program_coverage_map.py` is unchanged.

- **TR-29.14 Truth tooling.** `scripts/svg_text_runs.py` (new, stdlib only: `re`, `html`): `svg_text_runs(path)` → one dict per `<text>` in document order, `{"x", "y", "runs"}`, each run `{"text", "weight", "style", "family", "size", "level"}` from the `<tspan>` (or the element's own) `style` and the running sum of `dy` (`"sup"` below the baseline, `"sub"` above, `""` on it; 0.5 px tolerance); text decoded in one `re.sub` over `&(#[0-9]{1,7}|#x[0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{0,31});`: a numeric reference → `chr(N)` for every N up to 0x10FFFF (`html.unescape` alone drops `&#1;` and `&#x1b;` and maps `&#128;`-`&#159;` through cp1252, measured 06oct2026), a named one → `html.unescape` of that reference alone, so nothing is decoded twice; raw control characters are kept as written, and U+00A0 → space; raises `FileNotFoundError` on a missing file; never imports Stata. `scripts/svg_truth.py` is not edited. `scripts/extract_graph_text_truth.do` and `test/fixtures/graph_text_truth.json`: "Stata truth".

- **TR-29.15 Flips (R9).** Each pinned test of E9 keeps its purpose and its assertion shape and expects twoway's text: the scatteri/pcarrowi payloads `…{bf:X}…` → the same string with `{bf:X}` replaced by `X`, read from the column the `LabelSet` names (`_text_field(ls)`), and the raw column still holding the payload; `test_macro_smcl_markup_and_python_in_a_string_arrive_as_written` → `payload.replace('{bf:"z"}', '"z"')` for the title, the note and `_page_titles`; JSE-64 → `JR_WANT`/`JR_L1` set to `jr_t64` with its opening `{bf:"z"}` replaced by `"z"` (`subinstr(…, 1)` in Mata). Each docstring or comment gains: "Flipped (WP-30 P1.11b): {bf:…} is graph-text markup, which twoway draws as the bold text; the label stays text, never HTML or script."

- **TR-29.16 Help (R3/A155).** In dash.sthlp's Axis and Display Options, directly above the `{pstd}` line (:3035 at `c96facd`) that opens the paragraph beginning `{ul:Tooltips.}` (:3036; find by text), insert (prose lines at most 79 characters):

  ```
  {marker graph_text}{...}
  {pstd}
  {ul:Text in graphs.}  Text {cmd:dash} draws on a graph -- a title,
  subtitle, note or caption, an axis title, a tick label, a legend key or
  title, a {cmd:by()} panel title, the colour key and a marker label,
  typed in an option or taken from a variable label, a value label or a
  string variable -- reads Stata's graph-text markup as {cmd:twoway} does
  (see {help graph_text}): {cmd:{c -(}bf:}{it:text}{cmd:{c )-}},
  {cmd:{c -(}it:}{it:text}{cmd:{c )-}}, {cmd:{c -(}sup:}{it:text}{cmd:{c )-}},
  {cmd:{c -(}sub:}{it:text}{cmd:{c )-}}, the font tags
  {cmd:{c -(}stSans:}, {cmd:{c -(}stSerif:}, {cmd:{c -(}stMono:},
  {cmd:{c -(}stSymbol:} and {cmd:{c -(}fontface "}{it:name}{cmd:":}, each
  also as {cmd:{c -(}bf{c )-}}, which holds to the end of the line, the
  symbols {cmd:{c -(}&}{it:name}{cmd:{c )-}} ({cmd:{c -(}&alpha{c )-}} is
  the Greek letter alpha) and the characters {cmd:{c -(}c }{it:#}{cmd:{c )-}},
  {cmd:{c -(}c 0x}{it:#}{cmd:{c )-}} and {cmd:{c -(}c }{it:name}{cmd:{c )-}}.
  The characters are drawn in Unicode.  A text drawn on a graph has one
  style, one font and one baseline, so markup that covers the whole text
  makes it bold, italic or in that font, and a raised or lowered run uses
  Unicode's superscript or subscript characters when each of its
  characters has one (digits, {cmd:+ - = ( )} and, raised, {cmd:n} and
  {cmd:i}).  Markup on part of a text, or a raised run without such
  characters, is drawn in the text's own style and on the line, and
  {cmd:dash} says so in one note for each graph and kind of text.  Tick
  labels and legend keys take a style only when every one of them has it.
  {cmd:{c -(}stSans:}, {cmd:{c -(}stSerif:} and {cmd:{c -(}stMono:} draw
  in the reader's sans-serif, serif and monospace fonts (Helvetica, Times
  and Courier where installed; a {cmd:graph set} font is not read), and
  {cmd:{c -(}fontface{c )-}} needs that font on the reader's computer.
  As in {cmd:twoway}, a text holding {cmd:{c -(}c 0{c )-}} is drawn empty,
  and the control codes ({cmd:{c -(}c 1{c )-}} to {cmd:{c -(}c 31{c )-}},
  {cmd:{c -(}c 127{c )-}}, 129, 141, 143, 144 and 157) are kept as those
  characters; the page carries them as escaped text, never as markup or
  script.  One small difference is kept: a symbol inside
  {cmd:{c -(}stSymbol:} is drawn as itself.  Other SMCL
  ({cmd:{c -(}hline{c )-}}, {cmd:{c -(}space{c )-}},
  {cmd:{c -(}dup{c )-}}, {cmd:{c -(}cmd:{c )-}}, {cmd:{c -(}hi:{c )-}},
  {cmd:{c -(}ccl{c )-}}, {cmd:{c -(}center:{c )-}} and links) and an
  unknown tag are drawn as typed, as are {cmd:$$} and {cmd:\(} pairs.

  {pstd}
  Around the graphs, a filter's title, a dropdown's options taken from
  value labels and a tooltip's row names show the characters, without the
  style and font tags.  KPI titles, the dashboard's title and subtitle,
  {cmd:tabs()} titles, string values in tooltips and dropdowns, and the
  {cmd:csv} download keep the text as it is stored.

  {pstd}
  {it:Example:}

  {phang2}{cmd:. sysuse auto, clear}{p_end}
  {phang2}{cmd:. dash scatter mpg weight, title("{c -(}&alpha{c )-} = R{c -(}sup:2{c )-}") subtitle("{c -(}bf:Fuel economy{c )-}")}{p_end}

  ```

  The example prints no note (both texts are whole). No other help paragraph is edited.

- **TR-29.17 Security (rule 1).** The scanner reads only `{`, `}` and `:` positions and short heads; its time and memory are linear (TestLinearTime), it never recurses, never calls `eval`/`exec`/a shell or touches a file, and its output holds only characters of the input, table characters, the code points `{c #}` names (control codes included, A34 as ratified 06oct2026), or nothing (`{c 0}`); `_dash_inert_tex` runs last on canvas text, so translation cannot assemble a TeX pair, and every sink carries a control code escaped (TR-29.19). A font name reaching Bokeh's CSS `font` is from a fixed table or `[A-Za-z0-9 _-]{0,64}`, so `;`, quotes, parentheses and `url(` cannot reach a style. Canvas and DOM text stays raw text in its Bokeh property (no escaping by dash: TextSinks' rule); Bokeh's serialisation escapes it (E11) and HTML sinks are untouched. Notes name only graph names, variable names and fixed words, through `_dash_display` and S06's escape. The style column name is built from a variable name dash.ado validated and the reserved prefix. The commit body names the threats: denial of service by hostile markup, a mirrored control code, quote or `</script>` breaking out of a JSON or JS string or a script element, a translated TeX pair reaching the page, CSS through `{fontface}`.

- **TR-29.18 Budget.** Each `TestLinearTime` shape under 1 s and 1,000,000 `{` under 5 s; a served move over 10,000 rows with 1,000 distinct marked labels translates each distinct label at most once per process (`test_each_distinct_label_is_translated_once`).

- **TR-29.19 Control codes at every sink (rule 1; A34 as ratified 06oct2026).** Translated text may hold U+0001-U+001F, U+007F and the C1 code points twoway writes for 129, 141, 143, 144 and 157; raw U+0085, U+009B, U+2028 and U+2029 can already arrive in any Stata string. Translated text reaches only the sinks of E11, each of which escapes at `c96facd`, so no escaping code is added and none is edited:
  - Every canvas, marker-label and DOM sink is a Bokeh model property or a `ColumnDataSource` column; it reaches the saved page through Bokeh's `serialize_json` (`ensure_ascii`, then HTML-escaped, in a `<script type="application/json">` from `file_html` or a single-quoted JS literal from `components()`) and the served app through the same encoder on the wire. BokehJS draws it on the canvas or sets it as a DOM text node, never as HTML.
  - The tick-label map stays `json.dumps` with `ensure_ascii` left at its default (`True`), read by `JSON.parse`.
  - The served app's generated source never holds translated text: the translator runs inside `make_document`; S29's constants travel by `repr` (TR-29.11) and hold no control character (`_DASH_GT_*` values are printable symbols and letters).
  - HTML that dash writes (`_dash_header_fragments`, `_dash_kpi_card_html`, the KPI cards' `dash_html_escape`) takes raw text only (P1.11.3), never `_dash_graph_text` output.
  - Notes hold no user text (TR-29.8).
  A later section that sends graph text to another sink writes it through a Bokeh property, a `ColumnDataSource` column or `json.dumps(..., ensure_ascii=True)`, never by concatenating it into HTML, a JS literal or generated Python; it adds its sink to `TestControlCodesAreEscapedAtEverySink`. The payload of that class, `_CTRL_PAYLOAD`, is `"a{c 1}b{c 27}c{c 127}d{c 129}e{c 157}f"` + `"\x85\x9b\u2028\u2029"` (raw) + `"</script><script>alert(1)</script>\"'"` + a literal backslash-`u0022` and `<img src=x onerror=alert(2)>`; its expected text is the payload with the five codes replaced by the fixture's `chars` values for 1, 27, 127, 129 and 157; `_CTRL_RE` is `[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u2028\u2029]`.

## Boundaries

- **Batch partners.** S28 owns `_build_sources_and_figures`, `_dash_facet_label`, `DashRenderer._facet_label`, the template's by() titles, the "Graphs by" note, its `test_label_sinks.py` sink registrations and help :2070/:2096; its new canvas sinks must be in a figure the pass walks (S09's contract), which S29's pass then translates. S30 owns `OptionTranslator.stata_colour`, `translate_mcolor`, `parse_color_alpha`, `SchemeParser._color`/`_color_alpha`/`foreground_color`, the scheme extractor, the 26 scheme files, `scheme_truth.json` and the Marker and Transparency help. S29 edits none of them.
- **S09's call sites** in `_build_sources_and_figures` and `_generate_app_source` are not edited (manifest). Neither are `_dash_inert_tex`, `_stale_cue_args`, `_build_filter_widgets`, `_FILTER_JS`, `_dash_apply_axis_spec`, `_dash_text_annotations`, `_dash_axis_labels`, `_dash_apply_legend`, `_dash_apply_z_options`, `_dash_build_hover`, `_mlabel_column_kind`, `_mlabformat_column`, `_immediate_labels`, `scripts/svg_truth.py`, dash.ado, dash_parse.mata, dash_setup.*.
- **Later sections.** S33 (batch 11) sets marker-label and colour-key chrome; S37 (batch 13) `mlabtextstyle()` and `mlabvposition()` in `_apply_mlabel_opts`; S43 (batch 15) colour sites; S56 (batch 19) `text()` Labels, built raw before the pass. They keep S29's kwargs and the raw-once rule.
- **Residuals.** Exact inline style runs and raised text Unicode cannot express (a TeX route) stay the manifest's item-11 residual; SMCL beyond graph_text's tags is P2.47 (A32); the served bundle's MathJax is P2.48 (A36); reading `graph set` fonts for `{stSans}`/`{stSerif}`/`{stMono}` belongs to P2.22.
- **Decisions.** A31-A34 bind this section. A34 is ratification item 8, answered 06oct2026, CHANGED to "Mirror twoway" (a label holding `{c 0}` is emptied; C0/C1 codes kept, escaped at every sink, rule 1). The re-plan that the pending note asked for is done (ratification 06oct2026): TR-29.2-TR-29.5, TR-29.14, TR-29.16, TR-29.17, TR-29.19, GT-01, GT-07 and the stubs state the mirrored rule; nothing waits on batch 10's base (A151).

## Stata truth

**Fixture `test/fixtures/graph_text_truth.json`**, written by the new `scripts/extract_graph_text_truth.do` in S02's path-free form (copy the `DASH_REPO` block of `scripts/extract_text_truth.do` as S02 left it; no home-directory path or `arch` literal anywhere, `TestNoMaintainerPaths` scans `scripts/extract_*.do`). Shape of `extract_text_truth.do`: header (why, output, how to run with `<repo>` placeholders), `clear all`, `set graphics off`, the `_meta` provenance block (`git -C <repo> rev-parse HEAD` through `shell` into a temp file, read into a local, refused unless 40 characters), the probes, one trailing `python:` block that imports `svg_text_runs` from `<repo>/scripts` (via `Macro.getGlobal`), never calls Stata back and spells any backtick `\x60`.

Probes (each tick label is `"<i>_" + <directive>`, so the reader keys every label by its index and never splits on a character the output may hold; the research scratch split on `=` and mangled `{c Y=}`):
- `symbols`: the 148 names read at run time from Stata's own `graph_text.sthlp` (`findfile graph_text.sthlp`, regex `{c -(}&([A-Za-z0-9]+){c )-}`, unique; assert 148), three `twoway scatteri` graphs of at most 50 labels `{&<name>}`.
- `chars`: `{c <n>}` for n = 1..255, five graphs, raw controls recorded as twoway writes them (the reader keeps every code, TR-29.14); `{c 0}` as cases (below).
- `cnames`: every `{c <name>}` form of `smcl.sthlp`'s table (78 at research), as research truth3 did, written in compound quotes.
- `stsymbol`: `{stSymbol:<ch>}` for ASCII 33..126 except `"`, `$`, backtick, `{`, `}` and `\` (88).
- `cases`: every input of E6 (truth2's 25 and truth3's 51 edge cases, `s29p1.do`'s 20), the multi-line titles, and four `{c 0}` cases added for the ratified rule (`{c 0}|` is already among E6's; `a{c 0}b|`, `{bf:a}{c 0}`, `{c 1}a{c 0}` as tick labels, and the two-line `title("a" "b{c 0}c")`), each with `category` `graph_text` (now including `{c 0}` and the control codes), `other_smcl` (A32) or `difference` (only `{stSymbol:{&alpha}b}`).
- Each graph: `graph export <work>/gt_<k>.svg, replace`; the python block records, per label, `runs` from `svg_text_runs` (text, weight, style, family, level); a label the SVG does not hold (twoway emptied it, as for `{c 0}`) is recorded with `runs: []`, never skipped.

Keys: `_meta` (`stata_version`, `born_date`, `dash_commit`, `extracted`), `symbols` (name → text), `chars` (code → text, raw controls kept as twoway wrote them), `cnames` (name → text), `stsymbol` (char → text), `cases` (list of `{id, input, category, runs}`). Run: `DASH_REPO="$WT" /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S29" "$WT/scripts/extract_graph_text_truth.do"`; then `git -C "$WT" add -f test/fixtures/graph_text_truth.json` (`.git/info/exclude:58`). The fixture is read by `test/test_graph_text.py` (its name appears there; `test_fixtures_are_committed.py` is not edited). Never patched by hand.

**The S29 block** of `test/test_wp30_truth.cscript` replaces S01's stub body between `* ==== S29 P1.11b: … ====` and `* ==== end S29 ====`, keeping S01's header and gate lines. Read S01's helper and work-directory names first (`grep -n 'program define _w30\|w30_work' test/test_wp30_truth.cscript`); the text below uses `_w30_expect`, `_w30_done` and `w30_work` as S09 does.

```stata
* ==== S29 P1.11b: SMCL graph text drawn as twoway draws it ====
local only : env WP30_ONLY
if inlist("`only'", "", "S29") {
    display as text "S29 start " c(current_date) " " c(current_time)
    local W "`w30_work'"

    // GT-01 (guard, the truth): a symbol, a character, a whole-bold text,
    // value labels as panel titles, string and immediate marker labels.
    sysuse auto, clear
    quietly twoway scatter mpg weight, title("{&alpha} R{c 233}") ///
        subtitle("{bf:Whole bold}") name(s29a, replace)
    cert_svg_export, name(s29a) file("`W'/s29a.svg")
    local s29_svg "`r(file)'"
    foreach t in "α Ré" "Whole bold" {
        cert_svg_has_text, file("`s29_svg'") text(`"`t'"')
        local s29_f = r(found)
        _w30_expect GT-01 "(`s29_f' == 1)" `"twoway did not draw `t'"'
    }
    label define s29o 0 "{it:Dom}" 1 "{&alpha}For", replace
    label values foreign s29o
    generate str12 s29ml = cond(foreign, "{&beta}b", "{bf:Bx}")
    quietly twoway scatter mpg weight, by(foreign) mlabel(s29ml) name(s29b, replace)
    cert_svg_export, name(s29b) file("`W'/s29b.svg")
    local s29_svg "`r(file)'"
    foreach t in "Dom" "αFor" "βb" "Bx" {
        cert_svg_has_text, file("`s29_svg'") text(`"`t'"')
        local s29_f = r(found)
        _w30_expect GT-01 "(`s29_f' >= 1)" `"twoway did not draw `t'"'
    }
    quietly twoway scatteri 2 2 "{&beta}imm" 4 3 "{bf:Bimm}", name(s29c, replace)
    cert_svg_export, name(s29c) file("`W'/s29c.svg")
    cert_svg_has_text, file("`r(file)'") text("βimm")
    local s29_f = r(found)
    _w30_expect GT-01 "(`s29_f' == 1)" "twoway did not draw the scatteri label"
    // twoway empties a label holding {c 0} (A34, ratified 06oct2026); the
    // anchor label proves the graph was drawn and read.
    quietly twoway scatteri 2 2 "s29qzq{c 0}x" 4 3 "s29anchor", name(s29z, replace)
    cert_svg_export, name(s29z) file("`W'/s29z.svg")
    local s29_svg "`r(file)'"
    cert_svg_has_text, file("`s29_svg'") text("s29qzq")
    local s29_f = r(found)
    cert_svg_has_text, file("`s29_svg'") text("s29anchor")
    local s29_a = r(found)
    _w30_expect GT-01 "(`s29_f' == 0 & `s29_a' == 1)" ///
        "twoway c-0 label drawn `s29_f', anchor `s29_a'"
    _w30_done GT-01 "twoway draws graph-text markup"

    // GT-02: the same titles in dash.  The page JSON writes every non-ASCII
    // character as a lower-case \uXXXX escape (bokeh 3.9 measured: "α Ré" is
    // written \u03b1 R\u00e9), so every needle holding one is written so.
    quietly dash scatter mpg weight, title("{&alpha} R{c 233}") ///
        subtitle("{bf:Whole bold}") saving("`W'/s29a.html", replace)
    cert_file_has "`W'/s29a.html", needle("\u03b1 R\u00e9")
    local s29_t = r(found)
    cert_file_has "`W'/s29a.html", needle("{&amp;alpha}")
    local s29_r1 = r(found)
    cert_file_has "`W'/s29a.html", needle("{bf:Whole bold}")
    local s29_r2 = r(found)
    _w30_expect GT-02 "(`s29_t' == 1 & `s29_r1' == 0 & `s29_r2' == 0)" ///
        "titles: translated `s29_t', raw symbol `s29_r1', raw bold `s29_r2'"
    _w30_done GT-02 "titles carry the translated text"

    // GT-03: labels -- a variable label as the y title, value labels as panels.
    label variable mpg "{&mu} mpg{sup:2}"
    quietly dash scatter mpg weight, by(foreign) saving("`W'/s29b.html", replace)
    cert_file_has "`W'/s29b.html", needle("\u03bc mpg\u00b2")
    local s29_y = r(found)
    cert_file_has "`W'/s29b.html", needle("\u03b1For")
    local s29_p = r(found)
    _w30_expect GT-03 "(`s29_y' == 1 & `s29_p' == 1)" ///
        "labels: y title `s29_y', panel title `s29_p'"
    _w30_done GT-03 "variable and value labels are translated"

    // GT-04: string marker labels: a translated column and a style column.
    quietly dash scatter mpg weight, mlabel(s29ml) saving("`W'/s29m.html", replace)
    cert_file_has "`W'/s29m.html", needle("\u03b2b")
    local s29_m = r(found)
    cert_file_has "`W'/s29m.html", needle("__dash_mlabstyle_s29ml")
    local s29_s = r(found)
    _w30_expect GT-04 "(`s29_m' == 1 & `s29_s' == 1)" ///
        "mlabel: translated `s29_m', style column `s29_s'"
    _w30_done GT-04 "string marker labels are translated, whole bold kept"

    // GT-05: immediate labels.
    quietly dash scatteri 2 2 "{&beta}imm" 4 3 "{bf:Bimm}", saving("`W'/s29i.html", replace)
    cert_file_has "`W'/s29i.html", needle("\u03b2imm")
    local s29_i = r(found)
    quietly dash pcarrowi 1 1 2 2 "{&gamma}arr", saving("`W'/s29j.html", replace)
    cert_file_has "`W'/s29j.html", needle("\u03b3arr")
    local s29_j = r(found)
    _w30_expect GT-05 "(`s29_i' == 1 & `s29_j' == 1)" ///
        "immediates: scatteri `s29_i', pcarrowi `s29_j'"
    _w30_done GT-05 "immediate labels are translated"

    // GT-06: one note per graph and kind, never echoing the text.  The
    // text is built with char() so the command echo cannot hold it.
    local s29t = char(123) + "bf:a" + char(125) + "b"
    capture log close s29l
    quietly log using "`W'/s29n.log", text replace name(s29l)
    quietly dash scatter mpg weight, title("`s29t'") by(foreign) ///
        saving("`W'/s29n.html", replace)
    quietly log close s29l
    cert_log_has "`W'/s29n.log", needle("own style")
    local s29_n = r(count)
    cert_log_has "`W'/s29n.log", needle("{bf:a}b")
    local s29_e = r(count)
    _w30_expect GT-06 "(`s29_n' == 1 & `s29_e' == 0)" ///
        "note lines `s29_n', user text echoed `s29_e'"
    _w30_done GT-06 "one note, no user text"

    // GT-07: as twoway draws them (A34, ratified 06oct2026 "Mirror twoway"):
    // control codes are kept, and the page JSON carries them as lower-case
    // \u escapes, never raw; a text holding {c 0} is drawn empty.
    sysuse auto, clear
    quietly dash scatter mpg weight, title("a{c 1}b{c 27}c{c 129}d") ///
        subtitle("s29qzq{c 0}x") saving("`W'/s29k.html", replace)
    cert_file_has "`W'/s29k.html", needle(`""text":"a\u0001b\u001bc\u0081d""')
    local s29_k = r(found)
    cert_file_has "`W'/s29k.html", needle("s29qzq")
    local s29_z = r(found)
    _w30_expect GT-07 "(`s29_k' == 1 & `s29_z' == 0)" ///
        "escaped control title `s29_k', c-0 subtitle text `s29_z'"
    _w30_done GT-07 "control codes kept and escaped, a c-0 text is empty"

    // GT-08 (guard): a title of 5,000 open braces builds.
    local s29h = 5000*"{"
    capture quietly dash scatter mpg weight, title("`s29h'x") ///
        saving("`W'/s29h.html", replace)
    local s29_rc = _rc
    _w30_expect GT-08 "(`s29_rc' == 0)" "hostile title rc `s29_rc'"
    _w30_done GT-08 "hostile markup builds"

    display as text "S29 end " c(current_date) " " c(current_time)
}
* ==== end S29 ====
```

Expected at the batch-10 base (E1, E8, E11 and research): GT-01 PASS (its `{c 0}` check measures twoway only), GT-02 to GT-07 FAIL (GT-07: the raw `a{c 1}b…` title and the raw `s29qzq{c 0}x` subtitle are on the page), GT-08 PASS (measured rc 0 at `c96facd`). If GT-01's `{c 0}` check fails, twoway does not empty the label: stop and report to the coordinator (the ratified reading, index row 8, rests on it). GT-07's `\u0081` is `{c 129}` written raw as research measured it (p1-11.md:89, :97); if the fixture's `chars["129"]` is another character, the needle takes that character's lower-case `\uXXXX` escape. **Running it**, from the worktree only: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S29/run_test_wp30_truth.do"`, then `WP30_ONLY=S29 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S29" "$S29/run_test_wp30_truth.do"`; log `$S29/run_test_wp30_truth.log`. A `SKIP` (rc 222, `python_exec` lost from `~/.stata19/console/stata19.rc`) is not a pass.

## TDD test stubs

The regression tests, in the new `test/test_graph_text.py` unless named (fail at the batch-10 base, task 29-01; the module imports helpers from `test_label_sinks` (`hostile_inputs`, `_build`, `CLASSIFIED`, `carriers`, `tag`), `test_mode_parity` (`_spec`, `_case` data helpers, `_standalone_page`, `_served`, `_fire`, `_widgets_of`, `_DF`), `test_saved_filter_layers` (`_render`, `_move`), `test_server_layer_defects.plot_for`, `js_runner.requires_node`, `test_stale_cue_browser._run_chrome`, `conftest.make_data_json`; new names are reached as `dr.<name>` so they fail with AttributeError):

- Test: the fixture exists and carries `_meta` with its four keys; the fixture-driven ids collect from it lazily and, while it is missing, collect one id `fixture-missing` that fails naming the extractor — `TestGraphTextTruth::test_the_fixture_carries_its_stamp`
- Test: each of the 148 `{&name}` gives the fixture's character — `TestGraphTextTruth::test_symbols[<name>]`
- Test: each `{c n}`, n = 1..255, gives exactly the fixture's text, control codes (1-31, 127, 129, 141, 143, 144, 157) included as the characters twoway writes (A34 as ratified 06oct2026) — `TestGraphTextTruth::test_char_codes[<n>]`
- Test: each `{c name}` — `TestGraphTextTruth::test_char_names[<name>]`; each `{stSymbol:ch}` — `TestGraphTextTruth::test_stsymbol[<ch>]`
- Test: each `graph_text` case (the `{c 0}` and control-code cases included; a case with `runs: []` expects `""`): dash's text equals twoway's runs joined, each raised or lowered run mapped through `_DASH_GT_SUP`/`_SUB` when every character has a form, and dash's style equals the runs' one weight/style (else `None` with `"inline"`) — `TestGraphTextTruth::test_measured_cases[<id>]`
- Test: each `difference` and `other_smcl` case gives the documented dash text (`{stSymbol:{&alpha}b}` → `αβ`, the one `difference`; `{hline 3}` → as typed) — `TestGraphTextTruth::test_documented_differences[<id>]`
- Test: the 31 cases of E7, as an explicit table (input → runs' `(text, style)`), with any control row written as twoway draws it (e.g. `{c 1}|` → `"\x01|"`, `{c 31}|` → `"\x1f|"`, `a{c 127}b` → `"a\x7fb"`, `{c 129}|` → the fixture's `chars["129"]` + `"|"`, `{c 0}|` → `None` runs) — `TestTheScanner::test_measured_edge_cases`
- Test: `_dash_gt_head` for each row of TR-29.3, including `BF`, `& alpha`, `c 0XE9`, `c 256`, a 5,000-digit code, a fontface with `;}"<x>`, `c 0`/`c 0x0`/`char 0` → `("empty",)` and `c 1` → `("emit", "\x01")` — `TestTheScanner::test_heads_name_known_directives_only`
- Test: `{c 0}|`, `a{c 0}b`, `{bf:a}{c 0}`, `{char 0}x`, `{c 0x0}x` and the two-line `"a\nb{c 0}c"` give `("", None, None, ())` from `_dash_graph_text_parts` and `""` from `_dash_graph_text_plain`; `{c -(}c 0{c )-}` gives the literal `{c 0}`; `{c 0}` after 100,000 `{` returns in under 1 s — `TestTheScanner::test_c0_empties_the_whole_text`
- Test: `{bf:a}{bf:b}` → bold; `{bf:a}b` → `None` + `inline`; `{stSerif:a}{stSerif:b}` → the serif family; `{stSerif:a}b` → `inline`; `{bf:}` → `("", None, None, ())`; two lines `{it:x}`/`{it:y}` → italic; `{bf}a` / `b` → `inline` — `TestTheScanner::test_whole_style_and_font_only_when_markup_asks`
- Test: `R{sup:2}` → `R²`; `x{sub:1}` → `x₁`; `{sup:-(n)}` → `⁻⁽ⁿ⁾`; `x{sub:i}` → `xi` + `level`; `{sup:{&alpha}}` → `α` + `level` — `TestTheScanner::test_sup_and_sub_in_unicode_or_flagged`
- Test: `{bf}a\nb` carries no style to line 2; a tag opened on line 1 and closed on line 2 is literal on both — `TestTheScanner::test_lines_are_read_one_by_one`
- Test: `{fontface "Cour;ier<x>(u)":t}` gives the font `Courierxu`; a 100-character name is cut to 64; `{fontface "":t}` gives font `None`; `{fontface "a}b":t}` is literal (the head ends at the first `}`) — `TestTheScanner::test_fontface_names_are_sanitised`
- Test: `{c S|}{c S|}x{c S|}{c S|}` and `{c 92}(y{c 92})`: `_dash_graph_text` holds no `_TEX_DELIM_RE` match and `contains_tex_string` is false; `_dash_graph_text_plain` gives `$$x$$` — `TestTheScanner::test_the_result_passes_inert_tex_last`
- Test: `{c -(}bf:x{c )-}` → `{bf:x}` with style `None` — `TestTheScanner::test_escaped_braces_are_never_read_again`
- Test: every `test_label_sinks.PAYLOADS` value, `"Price $"`, `"{safe} @x $index"`, `"a}b:c{"` and `"{foo} {zz:q}"` are unchanged by `_dash_graph_text_plain` — `TestTheScanner::test_text_without_markup_is_unchanged`
- Test: 100,000 `{`; 100,000 `}`; 25,000 `{bf:`; 10,000-deep closed nesting; 50,000 `{&`; 30,000 `{c `; 20,000 `{fontface "`; `{sup:` + 100,000 digits + `}`; 100,000 mixed `{bf:a}{&alpha}{c 233}}{:` each under 1 s in `_dash_graph_text` — `TestLinearTime::test_hostile_text_takes_well_under_a_second[<shape>]`; 1,000,000 `{` under 5 s — `TestLinearTime::test_a_million_braces_stay_linear`
- Test: `_dash_finish_text_runs` for the five kinds returns translated values and one result per text; `_dash_finish_text_value` returns its first two — `TestThePass::test_finish_text_runs_returns_each_result`
- Test: hand-built figure: a Title `{bf:T}`, a Label `{it:L}`, an axis label `{stMono:x}`, a ColorBar title `{bf:c}`, a Legend title `{it:g}`: each style/font property set; a plain title leaves `text_font_style` at its value — `TestThePass::test_style_is_set_only_where_markup_asks`
- Test: `FixedTicker([1, 2])` with overrides `{1: "{bf:a}", 2: "{bf:b}"}` → bold; overrides on one of two ticks → not set + `inline`; a counted axis → not set — `TestThePass::test_tick_labels_take_a_style_only_when_every_tick_shares_it`
- Test: Legend items `{it:a}`, `{it:b}` → `label_text_font_style` italic; `{it:a}`, `b` → not set + `inline` — `TestThePass::test_legend_keys_take_a_style_only_when_every_key_shares_it`
- Test: a Title `{c -(}bf:x{c )-}` through `_dash_finish_graph_text` twice (and a `figures` mapping listing the same figure under two keys) stays `{bf:x}`, style unset — `TestThePass::test_a_translated_model_is_never_translated_again`
- Test: a HoverTool `[("{&mu} mpg", "@{mpg}")]` → `[("μ mpg", "@{mpg}")]`, marked; a string template unchanged — `TestThePass::test_tooltip_row_names_are_plain_text`
- Test: fields, `GlyphRenderer.name`, `CategoricalColorMapper.factors`, a `LabelSet(text="col")`, a source column and the display-format formatter holding `{bf:x}` are unchanged — `TestThePass::test_hover_fields_and_other_models_are_left_alone`
- Test: a two-panel by() spec with `title("{bf:QZQ}x")` and `xlabel(3000 "{bf:QZQ}" 4000)`: exactly two warnings starting `dash: graph 'g1': ` (kinds title… and tick label), neither holding `QZQ` — `TestTheNote::test_one_note_per_graph_and_kind_naming_no_user_text`; `title("{bf:Whole}")` raises none — `TestTheNote::test_no_note_for_whole_text_markup`; the warning lists of both modes are equal and hold the title note — `TestTheNote::test_both_modes_raise_the_same_notes`
- Test: both modes, `hostile_inputs("{&alpha}{c 233}R{sup:2}{c -(}{c )-}{c S|}")` built with `_build(…, inputs=…)`: every CANVAS carrier and `CustomJSTickFormatter.args` holds `tag + "αéR²{}$"` and never the raw payload — `TestEverySinkBothModes::test_every_canvas_sink_draws_the_translation[standalone|served]`
- Test: same build: LegendItem, Legend.title, Select.title, slider titles, value-label `Select.options` labels and tooltip labels hold the translation; `Div.text` (escaped once), `TabPanel.title`, `make`'s option labels, `ColumnDataSource` raw columns, `CustomJS.args` and `CategoricalColorMapper.factors` hold the raw payload; the derived `__dash_mlabel_make` column holds the translation — `TestEverySinkBothModes::test_dom_sinks_show_characters_and_html_and_data_stay_raw[standalone|served]`
- Test: both modes, title `{bf:T}`, subtitle `{it:S}`, xtitle `{stSerif:X}`, ztitle `{bf:Z}` with `colorvar(price)`, `legend(label(1 "{it:k}"))` on one key: each sink's style/font property — `TestEverySinkBothModes::test_whole_text_style_reaches_each_sink[standalone|served]`
- Test: both modes, payload `{c S|}{c S|}x{c S|}{c S|}` in every input: no model satisfies `bokeh.embed.bundle._model_requires_mathjax`; the saved page holds no `bokeh-mathjax` — `TestEverySinkBothModes::test_no_model_needs_mathjax[standalone|served]`
- Test (guard; rule 1; TR-29.19, E11): one spec puts `_CTRL_PAYLOAD` in the title, xtitle, an `xlabel()` tick label, a legend key, a string `mlabel()` variable, a dropdown's value label and a hover variable's label; built as a default page and as a `layout()` page: the whole page holds no `_CTRL_RE` character, its `<script` count equals the same spec's with the payload replaced by `x`, it holds no `<script>alert` and no `<img src=x`, and `alert(1)` occurs only after `&lt;script&gt;` — `TestControlCodesAreEscapedAtEverySink::test_the_saved_page_holds_no_raw_control_and_no_injected_script[default|layout]`
- Test: the same pages' document JSON, taken from the `application/json` script (default; `html.unescape`) or the `components()` literal (layout; undo `&#x27;`, the doubled `\\`, then `html.unescape`), parses with `json.loads`, and the Title text, axis label, LegendItem label, tick override, derived `__dash_mlabel_` column, `Select` title and option label and tooltip row name equal the expected text (codes mirrored, the rest as typed) — `TestControlCodesAreEscapedAtEverySink::test_the_saved_document_json_decodes_to_the_mirrored_text[default|layout]`
- Test: the axis's `CustomJSTickFormatter.args["labels"]` is ASCII-only (`str.isascii()`), holds no `</script>` and `json.loads` gives the expected tick text — `TestControlCodesAreEscapedAtEverySink::test_the_tick_label_map_is_valid_json_with_escaped_codes`
- Test: served, `bokeh.core.json_encoder.serialize_json(doc.to_json())` of the built document (what the protocol sends, bokeh/protocol/message.py:380) is ASCII-only, parses with `json.loads` and gives the expected texts at the same sinks — `TestControlCodesAreEscapedAtEverySink::test_the_served_wire_json_is_escaped`
- Test: the generated served source parses with `ast.parse`, holds no `_CTRL_RE` character and no part of the payload as plain text (`</script><script>alert` absent), each `_DASH_GT_*` assignment `literal_eval`s to the module's value, and its base64 spec decodes to the raw payload — `TestControlCodesAreEscapedAtEverySink::test_the_served_app_source_holds_no_raw_control`
- Test (guard): `_dash_header_fragments(P, P)` and `_dash_kpi_card_html` with `P = _CTRL_PAYLOAD` hold `&lt;/script&gt;`, `&quot;` and `&#x27;`, no `</script>`, and the literal `{c 1}` (raw text, P1.11.3: no translated code reaches dash's own HTML) — `TestControlCodesAreEscapedAtEverySink::test_dash_written_html_escapes_quotes_and_script`
- Test (guard): the warnings of both builds above hold no `_CTRL_RE` character and no part of the payload — `TestControlCodesAreEscapedAtEverySink::test_notes_hold_no_control_character`
- Test: both modes, a string variable `ml` with `{&beta}b` and `{bf:Bx}`: the LabelSet names `__dash_mlabel_ml`, the column holds `βb`/`Bx`, `text_font_style` is `field("__dash_mlabstyle_ml")` holding `normal`/`bold` — `TestMarkerLabels::test_a_string_variable_is_drawn_translated[standalone|served]`; value labels `{it:Dom}`/`{&alpha}For` on `foreign` — `::test_value_labels_are_drawn_translated[…]`; scatteri and pcarrowi labels — `::test_immediate_labels_are_drawn_translated[…]`
- Test: a `{bf:Bx}` row gives a style column; an all-normal column gives none — `TestMarkerLabels::test_a_whole_bold_label_gets_a_style_column`
- Test: by(foreign) where only foreign==1 rows hold markup: both panels' LabelSets name the derived column (both modes) — `TestMarkerLabels::test_the_decision_reads_the_whole_dataset`
- Test: 10,000 rows, 1,000 distinct marked labels: a counting wrapper on `dr._dash_graph_text` sees 1,000 calls, then 0 on a second draw — `TestMarkerLabels::test_each_distinct_label_is_translated_once`
- Test: two layers on one saved source with `mlabel(ml)` holding `{c -(}bf:x{c )-}`: the column is `{bf:x}` and no style column — `TestMarkerLabels::test_a_column_already_derived_is_not_translated_again`
- Test (guard): a string column with no directive: the LabelSet names the raw column; no `__dash_mlabel_`/`__dash_mlabstyle_` column — `TestMarkerLabels::test_no_markup_no_new_column`
- Test (node; `requires_node`): saved, `_move` the dropdown to Foreign: the moved source holds `__dash_mlabel_ml` and `__dash_mlabstyle_ml` for the kept rows only, translated — `TestAfterAFilterMove::test_saved_marker_labels_after_the_move`
- Test: served, `_fire` the Select to the group with no marked rows and back: the live source keeps both derived columns throughout — `TestAfterAFilterMove::test_a_served_move_keeps_the_translated_column`
- Test: both modes, after a move: Title text and `text_font_style`, the legend key (plus the stale suffix, saved) unchanged — `TestAfterAFilterMove::test_canvas_style_survives_a_move[standalone|served]`
- Test: `_dash_filter_title("{&mu} mpg", "v", t)` is `μ mpg` for a dropdown and a range and `μ mpg ≥` for a slider; `_dash_filter_title("{bf:$$x$$}", "v", "range")` holds no TeX pair and `_dash_filter_title("{bf:$$x$$}", "v", "dropdown")` is `$$x$$` — `TestDomSinks::test_filter_titles_show_the_characters`
- Test: `_dash_filter_widget("dropdown", "foreign", [0.0, 1.0], "t", {"0": "{it:Dom}", "1": "{&alpha}For"})` lists the option labels `All`, `Dom` and `αFor`; a string column `["{bf:a}", "b"]` keeps `{bf:a}` — `TestDomSinks::test_dropdown_options_from_value_labels_show_the_characters`
- Test (guard): KPI title/subtitle, dashboard title, `tabs()` titles and the CSV header hold the raw markup — `TestDomSinks::test_string_values_kpis_tabs_and_titles_stay_raw`
- Test: `_dash_graph_text_plain("{bf:a}\\(b\\)")` is `a\(b\)` (no joiner) — `TestDomSinks::test_plain_text_strips_style_and_keeps_tex`
- Test: the generated source defines the nine functions with `inspect.getsource` text and assigns each `_DASH_GT_*` constant and `_DASH_MLABSTYLE_PREFIX` — `TestTheServedApp::test_the_translator_travels_by_source`
- Test (Chrome; skip without it, red under `DASH_STRICT=1`): the saved page of a spec with `title("{&alpha}")`, a value-labelled dropdown `{&alpha}For` and an all-italic legend shows `α` in the dropdown's option text and an italic computed style on the legend label — `TestInChrome::test_the_page_shows_the_translated_text`
- Test (Chrome; as above): the saved page of the `_CTRL_PAYLOAD` spec, with `alert(1)`/`alert(2)` replaced by `window.__dash_pwned=1`, loads with `window.__dash_pwned` undefined, `document.scripts.length` equal to the source's `<script` count, and the dropdown's option text holding U+0001 and `</script>` as text — `TestInChrome::test_control_codes_and_script_text_stay_text`
- Test: dash.sthlp's `{ul:Text in graphs.}` paragraph names `{help graph_text}`, "one note", "drawn as typed", "is drawn empty", "escaped text" and "keep the text as it is stored", holds no "left out", and lies between the axis-title paragraphs and `{ul:Tooltips.}` — `TestTheHelp::test_the_help_documents_text_in_graphs`
- Cscript: `test/test_wp30_truth.cscript` GT-02..GT-07.

Truth tooling tests (written with the reader in task 29-02, green when written): `test/test_svg_text_runs.py::TestTheRunReader::test_plain_text_is_one_run`, `::test_tspans_carry_weight_style_family_and_level` (a hand-written SVG string in `tmp_path` in Stata's dialect, E6's `{superscript:2}{subscript:x}` dy values -47.11/59.96), `::test_nbsp_and_entities_are_read_as_text`, `::test_control_codes_are_kept` (raw U+0001 and U+0081 in a `<tspan>`, `&#1;`, `&#x1b;`, `&#129;` and `&#150;` read as U+0001, U+001B, U+0081 and U+0096; `&amp;#1;` read as the text `&#1;`), `::test_a_missing_file_raises`.

Guard tests (pass at the base; listed apart in the failure file): GT-01, GT-08, `TestControlCodesAreEscapedAtEverySink::test_the_saved_page_holds_no_raw_control_and_no_injected_script[default|layout]`, `::test_dash_written_html_escapes_quotes_and_script` and `::test_notes_hold_no_control_character` (every sink already escapes at the base, E11; the class's four other tests fail first because the codes are not yet produced), `TestEverySinkBothModes::test_no_model_needs_mathjax[standalone|served]` (nothing forms a pair until translation does), `TestMarkerLabels::test_no_markup_no_new_column`, `TestDomSinks::test_string_values_kpis_tabs_and_titles_stay_raw`, `TestThePass::test_hover_fields_and_other_models_are_left_alone`, the parity case of task 29-10 (both modes agree before and after), `test_label_sinks.py` and `test_canvas_tex.py` unchanged.

Pinned tests flipped in tasks 29-08/29-09 (E9): `test/test_immediate_values.py::TestScatteriDrawsItsRecords::test_the_label_is_text_not_markup`, `test/test_immediate_values.py::TestBothModesDrawTheSame::test_a_scatteri_label_reaches_the_served_page_as_text`, `test/test_pccapsym_pcarrowi.py::TestMapPcarrowi::test_the_label_is_text_not_markup`, `test/test_textbox_multiline.py::TestTextboxAdversarial::test_macro_smcl_markup_and_python_in_a_string_arrive_as_written`, `test/test_json_escaping.cscript` JSE-64.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Scanner, tables, differences | pytest `TestGraphTextTruth`, `TestTheScanner` | `graph_text_truth.json` | n/a (pure; the served copy is the same source) |
| Linear time | pytest `TestLinearTime` | generated strings | n/a |
| The pass: text, style, notes, raw-once | pytest `TestThePass`, `TestTheNote` | hand-built models; `_DF` specs | yes (`TestTheNote` compares) |
| Every sink | pytest `TestEverySinkBothModes` | `hostile_inputs(<SMCL payload>)` | yes |
| Marker labels | pytest `TestMarkerLabels` | `make_data_json` with a string and value labels | yes |
| After a filter move | pytest `TestAfterAFilterMove` (node; served `_fire`) | `_DF` + string column | yes |
| DOM sinks and raw sinks | pytest `TestDomSinks` | unit calls; hostile build | yes |
| Served wiring | pytest `TestTheServedApp`, `TestTheServedAppDefinesEveryNameItReads`, `TestTheServedAppCarriesEveryName` | generated source | served |
| Parity | pytest `test_mode_parity.py` CORPUS case + `_MUST_WARN` | `_DF` | yes |
| Control codes at every sink (rule 1) | pytest `TestControlCodesAreEscapedAtEverySink`, Chrome `test_control_codes_and_script_text_stay_text`, GT-07 | `_CTRL_PAYLOAD`, `_DF` + string column and value labels | yes (saved: default and `layout()`; served: wire and source) |
| Browser | Chrome `TestInChrome` | `_DF` | saved |
| twoway truth | cscript GT-01..GT-08; extractor | sysuse auto | n/a |
| Reader | pytest `test_svg_text_runs.py` | inline SVG | n/a |
| Flips | the five pinned tests | as each | as each |
| Help, registries, tracking | `TestTheHelp`, `test_help_conformance.py`, `test_help_examples.py`, `test_function_test_map.py`, `test_tracking_documents.py`, `test_cscript_hygiene.py`, `test_runner_portability.py` | — | n/a |

**Acceptance criteria.**
- **AC-29.1** (BR-29.1) `TestGraphTextTruth` passes for every fixture id (148 symbols, 255 codes, every name, 88 stSymbol characters, every case).
- **AC-29.2** (BR-29.2, 29.3) `TestTheScanner` and `TestThePass` pass; GT-02 and GT-03 PASS.
- **AC-29.3** (BR-29.4) `test_measured_edge_cases`, `test_escaped_braces_are_never_read_again`, `test_a_translated_model_is_never_translated_again` and `test_a_column_already_derived_is_not_translated_again` pass.
- **AC-29.4** (BR-29.5) `TestTheNote` passes; GT-06 PASS (one note line, no echo); the parity `_MUST_WARN` entry is met in both modes; nothing is refused.
- **AC-29.5** (BR-29.6) `TestMarkerLabels` and `TestAfterAFilterMove` pass (the node test not skipped on this machine); GT-04, GT-05 PASS.
- **AC-29.6** (BR-29.7) `TestDomSinks` and `test_dom_sinks_show_characters_and_html_and_data_stay_raw` pass in both modes.
- **AC-29.7** (BR-29.1, BR-29.8) GT-07 PASS (control codes on the page as `\u` escapes, a `{c 0}` text empty) and GT-01's `{c 0}` check PASS; `test_c0_empties_the_whole_text`, every `TestControlCodesAreEscapedAtEverySink` id and `TestInChrome::test_control_codes_and_script_text_stay_text` pass (Chrome not skipped on this machine); `test_the_result_passes_inert_tex_last` and `test_no_model_needs_mathjax` pass; `TestLinearTime` passes.
- **AC-29.8** (BR-29.9) `test_text_without_markup_is_unchanged`, `test_no_markup_no_new_column` and `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` pass with the batch-10 base's digest; `test_label_sinks.py` and `test_canvas_tex.py` pass unchanged.
- **AC-29.9** The five flips pass with their new expectation; no test is deleted and the collected count grows.
- **AC-29.10** GT-01..GT-08 print PASS under `WP30_ONLY=S29` with no SKIP; the full suite through the queue reports 0 failed; G7 prints 0.

## Tasks

**Commit boundary.** All twelve tasks form the one commit of entry `P1.11b`, made by task 29-12 on `wp30-s29` with the subject `Draw Stata's graph-text markup as twoway draws it (WP-30 P1.11b)`. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$S29` is `$S/s29` (`mkdir -p` it), `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s29`; every command runs with `git -C "$WT"` or `$WT` paths, never in the main checkout.

<task type="auto" id="29-01">
  <name>Write the failing tests and record them</name>
  <files>test/test_graph_text.py, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-10-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s29`; read `$S/batch-10-impact.txt` and `$S/wp30-ratified.txt` row 8, which must read "Mirror twoway" (answered 06oct2026: a label holding `{c 0}` is emptied; C0/C1 codes kept and escaped); stop and report if it reads otherwise. Save `python3 -m pytest test/test_immediate_values.py test/test_pccapsym_pcarrowi.py test/test_textbox_multiline.py test/test_label_sinks.py --collect-only -q -p no:cacheprovider | tail -1 > "$S29/29-collect-base.txt"`. Create `test/test_graph_text.py` with every `test_graph_text.py` stub of "TDD test stubs" (module docstring: the Overview's defect, E6's grammar, the A31-A34 rulings), loading `test/fixtures/graph_text_truth.json` lazily as the first stub says. Replace the body of S01's S29 stub in `test/test_wp30_truth.cscript` with the block of "Stata truth", using S01's helper names. Run `python3 -m pytest test/test_graph_text.py -q -n0 -p no:cacheprovider -rf > "$S29/29-new.log" 2>&1` and the S29 block through the driver ("Stata truth", Running it). Write `$S/29-P1.11b-failure.txt`: the base sha, one line per failing regression test from `29-new.log`, the GT lines of the log, and the guard tests that passed. Do not commit; do not edit `dash_render.py`.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S29/29-new.log"` is at least 40; `grep -c "GT-0[2-7] FAIL" "$S29/run_test_wp30_truth.log"` prints 6 and `grep -cE "GT-0[18] PASS" "$S29/run_test_wp30_truth.log"` prints 2; `test -s "$S/29-P1.11b-failure.txt"`; `git -C "$WT" diff --name-only -- dash_render.py` prints nothing.]]></verify>
  <done>Every regression test of P1.11b was shown failing on the unmodified tree, the two guard cases passed, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="29-02">
  <name>Add the SVG run reader and its tests</name>
  <files>scripts/svg_text_runs.py, test/test_svg_text_runs.py</files>
  <action><![CDATA[
    Create `scripts/svg_text_runs.py` as TR-29.14 says: a module docstring in `scripts/svg_truth.py`'s shape (why it exists: svg_truth's `svg_document` keeps a `<text>` element's markup in its text and is HIGH-impact, so the run reader is a sibling; what Stata's writer emits for tspans, measured in E6; the stdlib-only and no-callback rules), and `svg_text_runs(path)`. Do not edit `scripts/svg_truth.py`. Create `test/test_svg_text_runs.py` with the five reader tests of "TDD test stubs", each SVG written inline to `tmp_path` (no fixture file, no home-directory path).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_svg_text_runs.py test/test_runner_portability.py -q -n0 -p no:cacheprovider` passes; `git -C "$WT" diff --name-only -- scripts/svg_truth.py` prints nothing.]]></verify>
  <done>A sibling reader returned each Stata SVG text's style and level runs with every control code kept, pinned by its own tests, with svg_truth.py untouched.</done>
</task>

<task type="auto" id="29-03">
  <name>Extract twoway's graph-text truth</name>
  <files>scripts/extract_graph_text_truth.do, test/fixtures/graph_text_truth.json</files>
  <action><![CDATA[
    Create `scripts/extract_graph_text_truth.do` as "Stata truth" specifies: S02's `DASH_REPO` block copied from `scripts/extract_text_truth.do`, the `_meta` provenance, the five probe families with `"<i>_"`-prefixed tick labels, the symbol names read from `graph_text.sthlp` (assert 148), and one trailing `python:` block using `svg_text_runs` that writes `test/fixtures/graph_text_truth.json` with `json.dump(…, indent=2, sort_keys=True, ensure_ascii=True)`. Run it with `DASH_REPO="$WT" /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S29" "$WT/scripts/extract_graph_text_truth.do"`, read its log for `r(` errors; check that every case whose input holds `{c 0}` has `runs: []` (twoway drew no text) and stop and report to the coordinator if any has text (the ratified reading, index row 8, is that twoway empties the label); then `git -C "$WT" add -f test/fixtures/graph_text_truth.json`. Check `~/.stata19/console/stata19.rc` still holds `python pyexec_64`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/graph_text_truth.json')); print(sorted(d['_meta']), len(d['symbols']), len(d['chars']), len(d['stsymbol']), d['symbols']['alpha'], d['chars']['128'])"` prints `['born_date', 'dash_commit', 'extracted', 'stata_version'] 148 255 88 α €`; `python3 -m pytest "test/test_graph_text.py::TestGraphTextTruth::test_the_fixture_carries_its_stamp" test/test_runner_portability.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>twoway 19.5's drawing of every symbol, character code, character name, stSymbol letter and edge case was recorded in a stamped fixture by a path-free extractor.</done>
</task>

<task type="auto" id="29-04">
  <name>Add the graph-text scanner and its tables</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    After S09's `_dash_finish_graph_text` and before `def _dash_filter_title`, add the constants of TR-29.1 (transcribe the three tables from the fixture with a scratch script writing `\uXXXX` escapes; add `_DASH_MLABSTYLE_PREFIX` beside `_DASH_MLABEL_PREFIX`), then `_dash_gt_char` (TR-29.2), `_dash_gt_head` (TR-29.3), `_dash_graph_text_runs` (TR-29.4: two passes, piece lists, no recursion, no nested def or lambda, no module-level `re.compile`), `_dash_graph_text_parts`, `_dash_graph_text` and `_dash_graph_text_plain` (TR-29.5), each with a docstring stating the twoway truth it follows (E6), the A32 rule, A34 as ratified 06oct2026 (`{c 0}` empties the text; control codes kept) and the measured times (E7). Call them from nowhere yet.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_graph_text.py -q -n 6 -p no:cacheprovider -k "TestGraphTextTruth or TestTheScanner or TestLinearTime"` passes with every fixture id collected (`test_c0_empties_the_whole_text` among them); `python3 -m pytest test/test_canvas_tex.py test/test_label_sinks.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>The scanner drew every measured twoway case, `{c 0}` and the control codes included, kept the one documented difference, and handled each hostile shape in well under a second, with nothing yet calling it.</done>
</task>

<task type="auto" id="29-05">
  <name>Extend the canvas-text pass and copy lists</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    State in the progress output that S09's pass functions were measured at the batch base and report any HIGH or CRITICAL first. Apply TR-29.6 to S09's `_DASH_GRAPH_TEXT_SINKS`, `_dash_graph_text_models`, `_dash_finish_text_value` and `_dash_finish_graph_text` in place, and add `_dash_finish_text_runs`, `_dash_graph_text_style` (TR-29.7, its rule table in the docstring) and `_dash_graph_text_note` (TR-29.8, the exact message). Apply TR-29.11 to `_glyph_layer_lines`' two tuples at their anchors. Edit neither `_build_sources_and_figures` nor `_generate_app_source`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_graph_text.py -q -n 6 -p no:cacheprovider -k "TestThePass or TestTheNote or TestEverySinkBothModes or TestTheServedApp or test_canvas_style_survives_a_move"` passes; `python3 -m pytest test/test_canvas_tex.py test/test_label_sinks.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>Every canvas sink drew the translation with its whole style in both modes, notes came once per graph and kind, and the translator travelled to the served app.</done>
</task>

<task type="auto" id="29-06">
  <name>Translate marker labels in the mapper</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the progress output that `GlyphMapper._apply_mlabel_opts` is CRITICAL (16 impacted, 10 direct) and that `_mlabel_column_kind` is read, not edited. Add `GlyphMapper._mlabel_markup` and `GlyphMapper._mlabel_markup_rows` directly after `_mlabel_value_labels`, and make the one edit of TR-29.9 in `_apply_mlabel_opts` after `_is_text, _miss = self._mlabel_column_kind(...)`: the universe and decision, the derived text and style columns written only where the column is new, and the two `LabelSet` kwargs. Touch no `map_*` method and not `_immediate_labels`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_graph_text.py -q -n 6 -p no:cacheprovider -k "TestMarkerLabels or TestAfterAFilterMove"` passes with the node test not skipped; `python3 -m pytest test/test_marker_label_parity.py test/test_glyphs.py test/test_internal_column_names.py test/test_varlist_expansion.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>Marker labels from string variables, value labels and immediate layers were drawn translated with per-label style in both modes, on every panel and after every move.</done>
</task>

<task type="auto" id="29-07">
  <name>Translate the dash-only page text</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn that `_dash_filter_title` and `_dash_filter_widget` are CRITICAL (5 impacted, 10 processes). Apply TR-29.10: in `_dash_filter_title` translate the resolved title with `_dash_graph_text_plain` before the slider-family `_dash_inert_tex` and the inequality, and extend its docstring; in `_dash_filter_widget`'s nested `_label` wrap the two value-label returns in `_dash_graph_text_plain`, leaving `return rv` raw. Edit nothing else.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_graph_text.py -q -n 6 -p no:cacheprovider -k "TestDomSinks or TestEverySinkBothModes"` passes; `python3 -m pytest test/test_filters.py test/test_filter_widget_data.py test/test_label_sinks.py -q -n 6 -p no:cacheprovider` passes; `python3 -m pytest test/test_graph_text.py -q -n 6 -p no:cacheprovider -k "not TestTheHelp"` passes, `TestControlCodesAreEscapedAtEverySink` (nine ids) and the two Chrome tests among them, none skipped.]]></verify>
  <done>Filter titles, value-label dropdown options and tooltip row names showed the translated characters while KPI, tab, dashboard and data text stayed as stored.</done>
</task>

<task type="auto" id="29-08">
  <name>Flip the pinned pytest expectations</name>
  <files>test/test_immediate_values.py, test/test_pccapsym_pcarrowi.py, test/test_textbox_multiline.py</files>
  <action><![CDATA[
    First re-measure the red list on the fixed tree, by named files only (never `test/` as a whole): `python3 -m pytest test/test_immediate_values.py test/test_pccapsym_pcarrowi.py test/test_textbox_multiline.py test/test_label_sinks.py test/test_canvas_tex.py test/test_mode_parity.py test/test_saved_stale_cue.py test/test_saved_filter_layers.py test/test_server_facets.py test/test_marker_label_parity.py test/test_filters.py test/test_filter_widget_data.py test/test_title_escaping.py test/test_security_surface.py test/test_adversarial_matrix.py test/test_glyphs.py test/test_immediate_dashboards.py test/test_server_layer_defects.py test/test_help_claims_7.py -q -n 6 -p no:cacheprovider > "$S29/29-red.log" 2>&1`, and list every failure. Flip in place exactly the E9 pytest tests that failed because they expected the raw `{bf:…}` (TR-29.15), adding the "Flipped (WP-30 P1.11b)" sentence; any other failure is a defect of this section, fixed in dash_render.py, never flipped. Delete no test. Write one `Flipped:` line per flip (index R9 form) to `$S29/29-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_immediate_values.py test/test_pccapsym_pcarrowi.py test/test_textbox_multiline.py test/test_label_sinks.py -q -n 6 -p no:cacheprovider` reports 0 failed and its collected count equals the count in `$S29/29-collect-base.txt`; `grep -c '^Flipped:' "$S29/29-flips.txt"` prints 4.]]></verify>
  <done>The four pytest tests that pinned raw markup expected twoway's text, kept their security purpose, and every other test in their files passed unchanged.</done>
</task>

<task type="auto" id="29-09">
  <name>Flip JSE-64 and note the sink rule</name>
  <files>test/test_json_escaping.cscript, test/test_label_sinks.py</files>
  <action><![CDATA[
    In `test/test_json_escaping.cscript`, edit only case JSE-64 (R1): set `JR_WANT` and `JR_L1` to `jr_t64` with its opening `{bf:"z"}` replaced by `"z"` (Mata `subinstr(st_local("jr_t64"), "{bf:" + char(34) + "z" + char(34) + "}", char(34) + "z" + char(34), 1)`), reword its comment and PASS line from "drawn exactly as typed" to "drawn as twoway draws them", with the flip sentence of TR-29.15. Run that script through the driver and confirm `JSE-64 PASS`. In `test/test_label_sinks.py` add one paragraph to the module docstring, after S09's TeX paragraph: canvas and DOM text sinks carry graph-text markup translated (WP-30 P1.11b, `_dash_graph_text`), HTML and data sinks keep it raw, and the payloads here hold no recognised directive. Append the JSE-64 `Flipped:` line to `$S29/29-flips.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c "JSE-64 PASS" "$S29/run_test_json_escaping.log"` prints 1 and the log ends without `r(`; `python3 -m pytest test/test_label_sinks.py test/test_cscript_hygiene.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>JSE-64 expected twoway's drawing of its title and note, and the label-sink inventory stated where graph-text markup is translated and where it stays raw.</done>
</task>

<task type="auto" id="29-10">
  <name>Register the names and the parity case</name>
  <files>test/function_test_map.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Under the S29 anchor of `test/function_test_map.py`, add the eleven entries of TR-29.13 in alphabetical order. At the end of `CORPUS` in `test/test_mode_parity.py` (after any case S28 appended; before its closing `]`), add `_case("SMCL graph text (WP-30 P1.11b)", [_sc(), plot_for("lfit")], go={"title": '"{bf:a}b {&alpha}"', "subtitle": '"{it:Whole italic}"', "xtitle": '"{&mu} R{sup:2}"', "xlabel": '3000 "{bf:a}" 4000 "{bf:b}"', "legend": 'label(1 "{&beta} key")'})`, and to `_MUST_WARN` the new entry `"SMCL graph text (WP-30 P1.11b)": "dash: graph 'g1': {bf:}, {it:} or a font tag on part of a title"`. Edit no existing `_MUST_WARN` entry and not `ALLOWED` (R8).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider -k "SMCL or must_warn"` passes.]]></verify>
  <done>The eleven new functions were mapped to their tests and both modes were shown to draw and note the same graph-text markup.</done>
</task>

<task type="auto" id="29-11">
  <name>Write the Text in graphs help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    In dash.sthlp's Axis and Display Options, directly above the `{pstd}` line that opens the paragraph beginning `{ul:Tooltips.}` (find by text), insert the text of TR-29.16 exactly; it ends with a blank line. Edit no other paragraph (A155, R3).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_graph_text.py::TestTheHelp" test/test_help_conformance.py test/test_help_examples.py -q -n 6 -p no:cacheprovider` passes; `awk '/ul:Text in graphs/,/keep the text as it is stored/' dash.sthlp | awk 'length > 79' | grep -c .` prints 0; `awk '/ul:Text in graphs/,/keep the text as it is stored/' dash.sthlp | LC_ALL=C grep -c '[^ -~]'` prints 0 (the new paragraphs are ASCII; dash.sthlp:2039 already holds one em dash at `c96facd`, so the whole file is not checked).]]></verify>
  <done>The help said which graph-text markup dash draws, how it approximates what one text model cannot draw, that a `{c 0}` text is empty and control codes are kept and carried escaped as in twoway, the one kept difference, and which page text stays as stored.</done>
</task>

<task type="auto" id="29-12">
  <name>Close the entry and make the commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.11b"]`. In BUGS.md close that entry in place (`- [x]`) and replace its Resolution with Notes' "BUGS.md Resolution", today's date in `ddmonyyyy`. Delete the `"P1.11b"` key line of `WP30_OPEN`. Replace the one `<!-- WP-30 P1.11b -->` in CHANGELOG.md in place with Notes' line. Run `python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py test/test_function_test_map.py -q -n0 -p no:cacheprovider`; the S29 truth block once more through the driver; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); then one full run, `"$S/full_suite_queue.sh" "$WT" "$S29/29-full-1.log"` in the background, waiting for its `exit=` line and reading the log (never relaunching; E6 for the four known flaky tests). Stage exactly the 18 files of Notes' "Staged set" (`git add -f` for the fixture) and check `git -C "$WT" diff --cached --name-only` lists those and nothing else (G6). Write the message to `$S29/29-message.txt` as Notes says, check `grep -Eic 'claude|anthropic'` prints 0, confirm the branch prints `wp30-s29`, commit with `git -C "$WT" commit -F "$S29/29-message.txt"`, check the committed message the same way, and report the sha to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S29/29-full-1.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.11b -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.11b": "' "$WT/test/test_tracking_documents.py"` prints 0; `grep -c "GT-0[1-8] PASS" "$S29/run_test_wp30_truth.log"` prints 8; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.11b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.11b was closed naming existing tests and its fixture, its CHANGELOG marker carried the before and after text, and one green commit on wp30-s29 was ready for the merger.</done>
</task>

## Section completion criteria

- Every graph-text directive twoway draws is drawn with twoway's characters at every canvas sink, in marker labels and (characters only) in the named DOM sinks, in both modes, before and after a filter move; whole-text style and font are set only where the markup asks; what one text cannot draw is noted once per graph and kind (pytest, GT-01..GT-08, Chrome).
- The scanner meets the linear-time bounds and never translates a text twice; a page with no recognised directive is unchanged (the single-y digest at the base's value).
- A text holding `{c 0}` is drawn empty and control codes are kept, as twoway draws them; every sink type of E11 carries them escaped, with no raw C0/C1/U+2028/U+2029 character and no injected script on the saved page (default and `layout()`), on the served wire or in the served source (`TestControlCodesAreEscapedAtEverySink`, Chrome, GT-07).
- The eleven new functions, the `_DASH_GT_*` tables and `_DASH_MLABSTYLE_PREFIX` exist, are mapped and travel to the served app; S09's call sites are unedited.
- The fixture is extracted, stamped and committed with `git add -f`; the reader is a sibling of `svg_truth.py`, which is unedited.
- The five pinned expectations are flipped in place with their reason; no test is deleted.
- One green commit `(WP-30 P1.11b)` exists on `wp30-s29`; its body opens with the failure text and carries the `Regression:`, `Flipped:`, `Fixture:` and `BUGS.md:` lines; entry P1.11b is closed, its key deleted, its marker replaced, the help paragraph added.

## Notes

- **Raw once.** `_dash_graph_text` is not idempotent. A sink gets raw text and is translated by the pass or by its own maker, then marked; a derived marker-label column is translated only where it is created. Never call the translator on text that came out of it (a stale-cue label, a KPI copy of a title, a panel join of translated labels).
- **The decision reads the dataset.** A marker-label column's existence must not depend on the rows in view (E2). Read `self.dataset`, not the source, for a variable; only an immediate layer's reserved column reads its own source.
- **Panel titles in tests.** Find a panel's label among all `Title` texts of the panel figure (`fig.title` and the Titles of its side lists), never `fig.title.text` alone: S28 (same batch, merged first) moves the label to a separate panel title.
- **Style defaults differ per model (E5).** Never write `normal`; S15's choices stand unless the markup asks.
- **Help is ASCII SMCL.** In dash.sthlp a literal brace is `{c -(}`/`{c )-}`; `{&alpha}` is not used there (the help says "the Greek letter alpha"). The help-examples harness decodes `{c -(}` to run the example.
- **No module-level compiled regex, no nested functions** in the new code: the first cannot travel by the constants tuple, the second each need a map entry.
- **python_exec hazard.** Concurrent Stata sessions can drop `python pyexec_64` from `~/.stata19/console/stata19.rc`; the extractor and truth block then fail or skip (rc 222). Check the file after each Stata run.
- **Merge rules for the shared files.** R1: the S29 block of `test_wp30_truth.cscript` only, and in `test_json_escaping.cscript` only case JSE-64. R2: the constants after `"_DASH_ASCII_BLANKS",`, the functions after S09's line; eleven map entries under S29's anchor (adjacent to S28's and S30's anchors: context-only conflicts, keep every entry). R3/A155: one new paragraph pair above `{ul:Tooltips.}`; S28 edits Faceting (:2070, :2096) and S30 Marker and Transparency. R4: the one `P1.11b` marker. R5: the `P1.11b` entry and key only (S28 and S30 delete adjacent keys). R7: the new fixture with `_meta`, `git add -f`, never patched. R8: one CORPUS case appended after S28's and one new `_MUST_WARN` entry (no existing entry edited). R9: the five flips of E9. R10: no pin moves; if the merged single-y digest test fails after S28/S29/S30 land, the merger re-derives it. R12: S29 is batch 10's only editor of `_apply_mlabel_opts`.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` after `git apply` lists only S09's four pass symbols, `_glyph_layer_lines`, `GlyphMapper._apply_mlabel_opts`, `_dash_filter_title`, `_dash_filter_widget`, the new names and test symbols of the staged files.
- **Staged set (18).** `dash_render.py dash.sthlp BUGS.md CHANGELOG.md scripts/svg_text_runs.py scripts/extract_graph_text_truth.do test/fixtures/graph_text_truth.json test/test_graph_text.py test/test_svg_text_runs.py test/test_wp30_truth.cscript test/test_immediate_values.py test/test_pccapsym_pcarrowi.py test/test_textbox_multiline.py test/test_json_escaping.cscript test/test_label_sinks.py test/function_test_map.py test/test_mode_parity.py test/test_tracking_documents.py`.
- **Commit message** (`$S29/29-message.txt`). Subject: `Draw Stata's graph-text markup as twoway draws it (WP-30 P1.11b)`. Body, in order: the contents of `$S/29-P1.11b-failure.txt`, with every scratch or worktree path cut to its file name (the scratch path would fail G7); the measured defect (Overview, E8); what changed and where (TR-29.4-TR-29.10, both modes); the threats closed (TR-29.17); then one line each:
  - `Regression: test/test_graph_text.py::<Class>::<test> -- failed at <batch-10 base sha> with <text>` for every regression test of "TDD test stubs" (parametrised ones once per test, naming the id count), and `Regression: test/test_wp30_truth.cscript GT-02` … `GT-07`;
  - the five `Flipped:` lines of `$S29/29-flips.txt`, e.g. `Flipped: test/test_immediate_values.py::TestScatteriDrawsItsRecords::test_the_label_is_text_not_markup -- the raw {bf:X} in the drawn column was wrong because twoway draws {bf:X} as a bold X; the label is still text, never markup`;
  - `Fixture: test/fixtures/graph_text_truth.json (scripts/extract_graph_text_truth.do)`;
  - `BUGS.md: "<WP30_OPEN["P1.11b"] title>" (closed)`.
  No tool or vendor name anywhere (G7).
- **BUGS.md Resolution** (one line, in place; markup in backticks, test ids bare):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.11b). Graph text reached Bokeh with its SMCL as typed: `title("{&alpha} R{sup:2}")` drew the braces, as did variable and value labels, legend keys, tick labels, by() panel titles, the colour key and marker labels, in both modes. A linear-time scanner of Stata's graph-text grammar, _dash_graph_text, with tables transcribed from twoway 19.5's SVG (test/fixtures/graph_text_truth.json), turns `{bf:}`, `{it:}`, `{sup:}`/`{sub:}`, the font tags, `{&name}` symbols and `{c ...}` characters into Unicode, sets the whole text's style and font only where the markup covers all of it, and passes the result through _dash_inert_tex last. The canvas-text pass _dash_finish_graph_text applies it once to every canvas sink in the saved page and the served app and notes once per graph and kind of text what one style cannot draw; GlyphMapper._apply_mlabel_opts derives translated marker-label and per-label style columns, decided over the whole dataset so every by() panel and filter move keeps them; _dash_filter_title, value-label dropdown options and tooltip row names show the characters with style tags removed. As twoway draws them, a text holding `{c 0}` is drawn empty and control codes are kept; every sink carries them escaped (`\uXXXX` in the page and wire JSON, never raw). Pinned by test/test_graph_text.py::TestGraphTextTruth::test_symbols, test/test_graph_text.py::TestEverySinkBothModes::test_every_canvas_sink_draws_the_translation, test/test_graph_text.py::TestMarkerLabels::test_the_decision_reads_the_whole_dataset, test/test_graph_text.py::TestAfterAFilterMove::test_a_served_move_keeps_the_translated_column, test/test_graph_text.py::TestLinearTime::test_hostile_text_takes_well_under_a_second, test/test_graph_text.py::TestControlCodesAreEscapedAtEverySink::test_the_saved_document_json_decodes_to_the_mirrored_text, test/test_wp30_truth.cscript GT-02, test/test_wp30_truth.cscript GT-07; fixture test/fixtures/graph_text_truth.json. Residual, deferred (WP-30): a style or raised run on part of a text, and raised text with no Unicode form, are drawn in the text's own style on the line (no TeX route); SMCL beyond graph_text's tags is drawn as typed (P2.47).
  ```
- **CHANGELOG line** (replaces `<!-- WP-30 P1.11b -->` in the `**WP-30 (drop-in P1, 03oct2026)**` group of Results that change; code in backticks):

  ```
  - Stata's graph-text markup is drawn as twoway draws it. `dash scatter mpg weight, title("{&alpha} R{sup:2}") subtitle("{bf:Bold}")` drew `{&alpha} R{sup:2}` and `{bf:Bold}` as typed; the title is now `α R²` and the subtitle bold `Bold`. The same holds for axis titles, tick labels, legend keys and titles, by() panel titles, the colour key and marker labels (string variables, value labels, scatteri and pcarrowi), in the saved page and the served app, before and after a filter move; filter titles, dropdown options from value labels and tooltip row names show the characters without style tags. Markup on part of a text is drawn in the text's own style with one note; as in twoway, a text holding `{c 0}` is drawn empty and control codes are kept, carried in the page as escaped text. (WP-30, P1.11b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md D3** (:866): with S09's commit, `- **Tracked:** Closed in WP-30, BUGS.md "<P1.11a title>" and "<P1.11b title>", commits <S09 sha>, <S29 sha>`, and `(WP-30, GAPS2-D3)` appended to both Resolutions. B13 (:490) and J2 (:1735) have no heading of their own and close with D3 (S01's note).
  - **DROPIN-REMAINING.md:101 (P1.11):** "Closed by <S09 sha> (P1.11a, TeX) and <S29 sha> (P1.11b, SMCL)."
  - **ROADMAP:** the manifest's item-11 residual (exact inline style runs and raised text through a TeX route) as a P2/P3 row; P2.47 (other SMCL, A32) and P2.48 (served MathJax, A36) as the register files them; P2.22 gains "`{stSans}`, `{stSerif}` and `{stMono}` map to fixed CSS families (WP-30 P1.11b); reading `graph set` fonts should feed them".
  - **TWOWAY_COVERAGE_AUDIT.md:** graph text (`graph_text.sthlp`'s tags, symbols, `{c}`) drawn, `{c 0}` and control codes as twoway draws them (ratified 06oct2026), with one documented difference (a symbol inside `{stSymbol:}`).
  - **AGENTS.md invariant:** "Graph text is translated once: every canvas sink takes raw text and `_dash_finish_graph_text` (or its maker, then the mark) translates it; `_dash_graph_text` is not idempotent. Marker-label columns are decided over `GlyphMapper.dataset`, never the rows in view."
