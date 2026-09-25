# Section 14: Axis labels and value labels (B1, G16)

> Part of: WP-28 · Gaps: B1, G16 · Risk: red · Batch: 2 · Depends on: 02, 07 · Blocks: 12, 18 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **02, 07** · Blocks **12, 18** · Risk **red** · Commits: two commits: B1 and G16 → CHANGELOG `Results that change`

- D9: risk is red (tokenizer plus ado numlist expansion plus a hover column across both twins).
- D10: use S07's Unicode-aware name check by its final name; never `_DASH_VARNAME_RE` (S07 removes it). Replace the "no overlap with S12/S17" boundary claim with the D4 ordering (S12 follows this section).
- D10: add the E3 `%tm` axis-label probe (`twoway line … , xlabel(, format(%tm))` on a %tm variable; record the tick label texts) to the probe table with a stable id that S12 cites.
- D8: remove checkpoint 14-12 and renumber.
- State that a numeric run holding a backtick or `$` never reaches `numlist` (treated as text and named). Stubs: `valuelabel` under by() panels; `numlist`'s 1,600-element cap versus the 2,000 bound.
- D7: split 14-01, 14-03, 14-05.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

Two gaps share one code path: the reader of `xlabel()`, `ylabel()`, `xtick()`, `ytick()`,
`xlabel2()` and `ylabel2()`. **B1** (S1, silently wrong output): GAPS2 measured that
`xlabel(1 "2019" 2 "2020" 3 "2021")` "gives ticks [1,2,3,2019,2020,2021] with no labels and no
warning", that "a second label line is lost, and a compound-quoted label becomes a lone
backtick", that "`10 20 to 40` loses 30, and `1 2 : 5` uses `:` as a label", and that "`1/5` and
`1[1]3` draw no ticks (they are named)". Research added one more: `xlabel(#5 50 "fifty")` drops
the `#5`, although Stata's grammar is `[rule] [numlist ["label" …]] [, suboptions]`
(axis_label_options.sthlp:50-58). The cause is one function, `_dash_parse_axis_label_opt`
(dash_render.py:16041-16074), which flattens quoted and bare tokens alike with a regex that
treats single quotes as delimiters and knows none of Stata's numlist forms.

**G16** (S3, documented difference 6): "twoway's `xlabel(1/5, valuelabel)` puts value labels at
the ticks, and a user expects `hover(foreign)` to show Domestic/Foreign, as `list` and `browse`
do. dash draws numbers on axes and in tooltips and names `xlabel(, valuelabel)` only in the
note". The value labels already reach Python in both modes; only `_dash_apply_axis_options` and
`_dash_build_hover` never receive them, and the label-set lookup is written five times.

After this section: every numlist form Stata accepts (`a/b`, `a(b)c`, `a[b]c`, `a b to c`,
`a b:c`, negative and fractional steps, comma-separated lists, mixed forms) is expanded by
Stata's own `numlist` in dash.ado and, for hand-written specs and as the served twin, by a
bounded port of the same rules in the renderer; a string is always label text, consecutive
strings are lines of one label, compound quotes are read as Stata reads them, single quotes are
characters, a rule may precede a labelled list, and `_MAX_AXIS_TICKS` still bounds every form.
`valuelabel` (minimum `val`) puts the axis variable's value labels at the ticks, and `hover()`
shows the label text through a derived `__dash_hover_{var}` column that survives filter moves in
both modes. Nothing new is printed once an option is drawn (DISCOVERY Q22).

**Test order (CLAUDE.md rule 7): task 14-01 writes every failing test for both gaps**, runs
them against the unmodified tree at `91d97be`, and the failures are recorded in the two gap
commits' messages. Tasks 14-02 to 14-06 close B1; 14-07 to 14-11 close G16.

## Risk: [yellow] — one parser rewrite that every axis option in both modes passes through, plus a dash.ado normalisation step that runs on every graph

**Why.** `_dash_parse_axis_spec` feeds xlabel/ylabel (`_dash_apply_axis_options`), xtick/ytick
(`_dash_apply_tick_option`), xlabel2/ylabel2 (`_dash_finish_secondary_axes`) and date axes
(`_dash_date_axis_spec`); a regression there changes every dashboard with an axis option.
The ado step touches `_dash_option_rules`, whose graph list is validated per segment and per
graph.

**Risk factors.** (1) The a(b)c bound (`TestAxisLabelBounds`) must survive the tokenizer
rewrite in both modes. (2) Stata's `numlist` refuses more than 1,600 elements (nlist.sthlp:85-87)
while dash's bound is 2,000: a list of 1,601-2,000 values is expanded by the renderer, not by
Stata. (3) Two undocumented readings (whitespace inside `a(b)c`, a second consecutive string)
are settled only by the probes of task 14-02. (4) The hover text column is a new internal
column: it must carry the `__dash` prefix Section 07 reserves and must be on every source the
tooltip attaches to, or a tooltip row reads `???`.

**Mitigation.** The bound tests are run first (14-03 verify); the extract script records
twoway's reading of every ambiguous form before the parser is written, and the cscript compares
dash's page with twoway's SVG for the same commands; the hover column is added by one module
function called wherever a source is built or redrawn, and a both-modes test asserts it is on
every renderer source that carries the variable.

## Dependencies

- **Depends on:** Section 02 (`scripts/svg_truth.py`: `svg_texts(path)`,
  `svg_axis_extent(path, axis, tick_values)`; `test/cert_svg.do`: `cert_svg_export, name() file()`,
  `cert_svg_texts, file()`, `cert_svg_has_text, file() text()`). The extract script and the
  cscript read twoway's tick label text through them. Section 07's fixed internal-column prefix:
  the hover text column is `__dash_hover_{var}`.
- **Blocks:** Section 18 (its hull step reads the tick positions this section's parser
  produces, and its `norescale` sub-option rides the same honoured tuple); Section 19.
- **Parallel batch:** 2. **Can run with:** 11, 12, 13, 15, 16, 17 — none of them edits
  `_dash_parse_axis_spec`, `_dash_apply_axis_options`, `_dash_build_hover` or dash.ado's
  `_dash_option_rules`.

## Evidence

### B1: the parser today

`_dash_parse_axis_label_opt` (dash_render.py:16041-16074) is the whole reader of the numlist
part; its only caller is `_dash_parse_axis_spec` (16605-16735):

```python
16052    tokens = re.findall(r'"([^"]*)"'  # double-quoted label
16053                        r"|'([^']*)'"  # single-quoted label
16054                        r"|([^\s,\"']+)",  # bare token (number or keyword)
16055                        str(raw or ""))
16056    flat = [dq or sq or bare for dq, sq, bare in tokens]
...
16064                try:
16065                    float(next_tok)
16066                except ValueError:
16067                    labels[str(val)] = next_tok
```

So `2019` after `1` is a number, not a label; `'` opens a string; `` `"c "q" d"' `` is read as
the bare token `` ` `` plus the string `c ` and more; `to` and `:` are bare words that become
labels or are dropped; `1/5` and `1[1]3` are not numbers and are named.

`_dash_parse_axis_spec` decides the rule before this call. `#N` is a `fullmatch` on the whole
head (16672-16680), so `#5 50 "fifty"` never matches and `#5` is lost; the `a(b)c` form is a
regex (16686-16714) with the `_MAX_AXIS_TICKS` pre-count and the note that `TestAxisLabelBounds`
pins; the head/tail split is a regex that is not quote-aware:

```python
16648    _m_tail = re.search(r",\s*(?=[A-Za-z_])", text)
...
16664    m_sub = re.search(r",\s*(?=[A-Za-z_])", head)
```

so `xlabel(1 "a, b" 2 "c")` cuts inside the string. The honoured tuple is
`("format", "labsize", "angle", "grid", "nogrid")` (16635); everything else, `valuelabel`
included, goes to `unsupported` and is named by `_dash_report_suboptions` (18813-18830).

The explicit-label applier (16783-16798) keys `major_label_overrides` by float and carries the
labels as JSON in the formatter's `args` (the security shape `TestAxisLabelInjection` pins):

```python
16783        axis_obj.ticker = FixedTicker(ticks=spec["ticks"])
16784        if spec["labels"]:
16791            _labels = {str(k): str(v) for k, v in spec["labels"].items()}
16792            axis_obj.formatter = CustomJSTickFormatter(
16793                args={"labels": json.dumps(_labels)},
16794                code="const m = JSON.parse(labels); "
16795                     "return m[String(tick)] || String(tick);")
16796            axis_obj.major_label_overrides = {
16797                float(k): v for k, v in spec["labels"].items()}
```

Report W §1b: BokehJS matches override keys as JS numbers, so `1` and `1.0` both match tick 1
and a string key never does; `\n` in an override renders as two lines; `$$` is LaTeX. The
formatter map is keyed `"2000.0"` where JS's `String(2000)` is `"2000"`, so on whole-number
ticks the overrides do the work (report A, surprise 8). This section does not change the
formatter's keys: `test_served_dates.py::test_xlabel_text_labels_are_keyed_by_their_dates`
pins them as `str(float)` and the overrides are the path that draws.

### dash.ado already expands numlists

`_dash_validate_value`, kind `numlist` (dash.ado:2122-2148), runs Stata's own `numlist` and
returns the expansion through `c_local _dash_vnorm` (2323):

```stata
2129        local _nlrc 7
2130        if !strpos(scalar(`V'), char(34)) {
2131            capture numlist `"`macval(value)'"'
2132            local _nlrc = _rc
2133        }
...
2145                local norm `"`r(numlist)'"'
```

It refuses a value holding a double quote by construction (a label text would end the quotes
on numlist's command line). The graph rules live in `_dash_option_rules` (1853-1929):

```stata
1910    local graph ///
1911        xsize=style,1,100  ysize=style,1,100  aspectratio=num,0  hover=varlist  by=byvarlist ///
1912        scheme=scheme
```

and are applied twice, each time writing the normalised value back: per segment in
`_dash_validate_opts` (2463-2479, `sreturn local g_`o' `"`macval(_dash_vnorm)'"'`) and per
graph in `_dash_plot` (4705-4713, `local g_`_vopt' : copy local _dash_vnorm`). The JSON is
written from the `g_*` locals at 4942-4955 with the user's quotes kept. `xmtick`, `ymtick`,
`xmlabel` and `ymlabel` are in the `_dash_pending` block (dash.ado:791-797): they are named as
unsupported and `test_unsupported_report_is_true.py` asserts they change nothing; normalising
their text does not change that.

### Stata's rules (report D §1, §2)

- Grammar: `[rule] [numlist ["label" [numlist ["label" …]]]] [, suboptions]`; "Either rule or
  numlist must be specified, and both may be specified" (axis_label_options.sthlp:50-58).
- numlist forms (numlist.sthlp:28-62): `1/3`, `3/1`, `-5/-8`; `1 2 to 4`, `4 3 to 1`; `1 2:4`;
  `1(2)9`, `9(-2)1`, `-1(.5)2.5`; `1[1]3` ≡ `1(1)3`; `1(2)10` "the same five numbers: 1, 3, 5,
  7, 9"; forms mix freely; commas may separate inside an option's parentheses, which collides
  with the sub-option comma (report D §1: split off the sub-options first).
- A text labels the one value before it (`ylabel(10 20 30 "mean" 40 50)`, :1013-1022). Whether
  a second consecutive string is a second line is documented only for titles and legend labels
  (`_textbox_lines` measured it for titles) — **PROBE** (14-02 records it).
- Whitespace inside `a(b)c` and which rc a bad step (`1(0)5`) raises are undocumented —
  **PROBE**.
- `valuelabel` (minimum `val`): "values should be mapped through the first y variable's value
  label (y*() options) or the x variable's value label (x*() options)"; `xlabel(1 2 3,
  valuelabel)` "would have the same effect as `xlabel(1 "Low" 2 "Med" 3 "Hi")`" (:269-291).
  twoway uses no value label unless told (`test_help_claims_2.cscript` HC2-41 pins it).
- Repeated options: "the rightmost of each is honored"; `add` merges (:1029-1035). The Mata
  merge (`_dash_rep_merge`, dash_parse.mata:4826-4855) joins bodies before the graph-level
  validation at 4705 sees them, so the expansion runs on the merged text.

### G16: value labels already reach Python

Export (`_dash_write_stata_data`, dash_render.py:1313-1351) writes `valueLabelNames`
(`{var: labelset}`) and `valueLabels` (keyed by set or, as jsonio does, by variable). Saved
load: `self.value_labels` / `self.value_label_names` (21150-21153); served: `val_label_names` /
`val_labels` (template 25699-25700, `meta` 25749-25751) and `_dash_attach_labels(_DASH_MAPPER,
…)` (25874-25876). The labelset-then-variable lookup is written **five times**:
`_apply_colorvar` 6399-6405, `GlyphMapper._mlabel_value_labels` 6973-6987, `_dash_csv_meta`
13909-13912, `_dash_facet_label` 15601-15607 and the saved filter builder 23598-23603. The
cleanest copy:

```python
6983        labelset = getattr(self, "value_label_names", {}).get(var, "")
6984        vlabels = (getattr(self, "value_labels", {}).get(labelset, {})
6985                   if labelset else {})
6986        if not vlabels:
6987            vlabels = getattr(self, "value_labels", {}).get(var, {})
6988        return vlabels if isinstance(vlabels, dict) else {}
```

`GlyphMapper._mlabel_value_text(value, vlabels)` (7085-7104, staticmethod) turns a code into
its label ("." for missing, the number for an unlabelled value). The marker-label derived
column is the pattern for a hover column (`_apply_mlabel_opts`, 6750-6765): `text_col =
f"__mlabel__{mlabel_var}"`, written once per source when absent, rendered through
`_mlabel_value_text`. Section 07 renames it under `__dash`; the hover column is
`__dash_hover_{var}` from the start.

`_dash_build_hover(fig, xvar, y1var, y2var, hover_extra, var_labels, date_vars,
numeric_formats, univar, layers)` (19839-19990) has no value-label parameter; rows come from
`_dash_hover_row(col, label, date_kind, numeric_fmt)` (19795-19808), which returns
`(label, "@{col}{fmt}")`; `_fields_for` (19917-19951) keeps a name only if some renderer's
source carries it and it passes `_DASH_VARNAME_RE` (19207, `^[A-Za-z_][A-Za-z0-9_]*$`, which
`__dash_hover_foreign` passes). Callers: 22348-22359 saved, template 26451-26463 served.

Derived columns survive moves in both modes: the saved page snapshots each source after the
figures are built (`_snapshot_of[id(_gsrc)]`, 23697; handed to the callback at 23785-23787) and
`_FILTER_JS` rebuilds each source from its own snapshot's columns; served,
`_dash_refresh_unlinked` (18166) reads "a column the layer derived … from the snapshot at the
row's own position". A served **redraw** of a computed layer (`agg['redraw'](agg_fdf)`,
template ~26919) rebuilds its source from the frame, which has no derived column: the hover
column must be re-added there (TR-14.14).

### Fixtures on disk

`test/fixtures/axis_truth.json` (`scripts/extract_axis_truth.do`) holds label probes `a_list`,
`a_pairs` (`xlabel(2000 "low" 4000 "high")`: `x_axis.tick_labels == ["low", "high"]`,
`tick_px == [954.11, 3954.99]`, `mapping: None` because no label parses as a number),
`a_incr`, `a_incr_inside`, `a_hash*`. No probe holds a multi-line, compound, `to`, `:`, `/`,
`[ ]`, rule-plus-list or `valuelabel` case. The probe registration is `zp id group dataset body
opts` (106-119); the trailing `python:` block (452-1450) parses each SVG with `axis_facts`
(627-810) and writes the fixture; every regex there spells a backtick `\x60`.

### Tests that pin today's behaviour (flip, never delete)

- `test/test_graph_options.py::TestParseAxisLabelOpt::test_single_quoted_label` (436-441)
  pins `'One'` as a label. Flip: ticks `[1.0, 2.0]`, labels `{}`.
- `test/test_suboption_warnings.py` SUBOPTIONS entry `("xlabel valuelabel", {"xlabel": ",
  valuelabel"}, None, "xlabel", ["valuelabel"], [])` (58-59) pins the note. Flip: move the
  case to `TestTheHonouredOnesStayQuiet`.
- `test/test_mode_parity.py` MUST_WARN entry `"xlabel with an unimplemented sub-option"`
  (1459-1461, case at 1168-1169 `{"xlabel": "#5, valuelabel", "ytitle": "Miles,
  orientation(vertical)"}`). Flip: the case becomes `{"xlabel": "#5, labcolor(red)", …}` and
  the expected message names `labcolor(red)`; `valuelabel` may no longer appear in MUST_WARN.
- `test/test_suboption_reporting.cscript` SR-02 (174-182) pins "xlabel(, valuelabel) is named".
  Flip: it is not named, and the page carries a value label.
- `test/test_mode_parity.py` CORPUS cases "hover()" (1133) and "hover() on a bar" (1134) gain a
  value-label assertion (a new class, not a corpus change).
- Kept green, unchanged: `test_axis_options.py::TestAxisLabelGrammar`,
  `test_adversarial_matrix.py::TestAxisLabelBounds` and `::TestAxisLabelInjection`,
  `test_served_dates.py::TestANumberOnADateAxisIsAStataDate`,
  `test_help_claims_8.py::test_a_label_written_in_xtick_is_not_drawn`,
  `test_help_claims_2.py::test_an_axis_is_labelled_with_numbers`.

## User stories

- **US-14.1** As the Stata user pasting twoway syntax, I want `xlabel(1 "2019" 2 "2020" 3
  "2021")` to draw three labelled ticks so that my date-coded axis reads as it does in twoway.
- **US-14.2** As the Stata user, I want `xlabel(1/5)`, `xlabel(1[1]3)`, `xlabel(10 20 to 40)`,
  `xlabel(1 2:5)` and `xlabel(1(2)10)` to draw the ticks Stata's numlist gives so that I can
  write the forms I already use.
- **US-14.3** As the Stata user, I want a second string after a value to be a second line, and
  a compound-quoted label to keep its inner quotes, so that a multi-line or quoted tick label
  is drawn as twoway draws it.
- **US-14.4** As the Stata user, I want `xlabel(#5 50 "fifty")` to keep both the rule and the
  labelled value so that Stata's `[rule] [numlist …]` grammar holds.
- **US-14.5** As the Stata user, I want `xlabel(1/5, valuelabel)` to put my value labels at the
  ticks so that a coded axis reads as words, as twoway's does.
- **US-14.6** As the dashboard viewer, I want `hover(foreign)` to show "Domestic"/"Foreign"
  rather than 0/1, before and after a filter move, in the saved page and the served app.
- **US-14.7** As the maintainer, I want the label and numlist rules pinned against twoway's own
  drawing so that a regression fails a test rather than a user.

## Business requirements

- **BR-14.1** A double-quoted or compound-quoted string in an axis label option is label text
  for the value before it; it is never read as a number, a rule or a sub-option.
- **BR-14.2** Consecutive strings after one value are the lines of that value's label, in
  order.
- **BR-14.3** A single quote is a character; `'One'` is a bare word, not a label.
- **BR-14.4** Every numlist form Stata accepts (`a/b`, `a(b)c`, `a[b]c`, `a b to c`, `a b:c`,
  negative and fractional steps, comma-separated values, mixed forms) draws exactly the values
  Stata's `numlist` gives; `1(2)10` draws 1, 3, 5, 7, 9.
- **BR-14.5** A rule (`#N`, `none`, `minmax`) may precede a labelled list, and both are drawn.
- **BR-14.6** A request for more than `_MAX_AXIS_TICKS` (2,000) ticks, in any form, keeps the
  axis's default ticks and says so once, in both modes; it is never refused in Stata.
- **BR-14.7** `xlabel2()`, `ylabel2()`, `xtick()`, `ytick()` and a date axis read the same
  grammar.
- **BR-14.8** `valuelabel` (minimum `val`) labels each tick that is a labelled whole-number
  code with its label, through the first y variable's set for y options and the x variable's
  for x options; an unlabelled tick keeps its number; explicit `"text"` wins for its value
  (as measured); without `valuelabel` nothing changes.
- **BR-14.9** A `hover()` variable with value labels shows the label text in the tooltip, in
  both modes, before and after any filter move; a variable without labels shows its number as
  before.
- **BR-14.10** Once drawn, none of these prints a note (DISCOVERY Q22); a bare word that is
  neither a value, a form, a rule nor a label is still named.
- **BR-14.11** Hostile label text (markup, a JS template, a line separator) is carried as data
  and never reaches code or unescaped HTML.

## Technical requirements

- **TR-14.1** `_dash_expand_numlist(tokens, limit=_MAX_AXIS_TICKS)` (new, module level,
  dash_render.py, beside `_MAX_AXIS_TICKS`): expands one run of bare tokens by [U] 11.1.8:
  `n`; `a/b` (step ±1 toward b, inclusive); `a(b)c` and `a[b]c` (from a by b while ≤ c for
  b > 0, ≥ c for b < 0, `a + i*b` never accumulated, inclusive within the existing `1e-9`
  tolerance); `x y to z` and `x y:z` (also `x y : z` and `y:z` split from one token): step =
  y − x from the two values before the word; every count is computed before any value is made
  and the run stops with `too_many=True` once the total would pass *limit*; a zero step, a
  non-finite endpoint, a `to` with fewer than two values before it, or any other token goes to
  `bad`. Returns `(values, too_many, bad)`.
- **TR-14.2** `_dash_axis_tokens(head)` (new): the head's tokens as `(kind, text)`, kind
  `"str"` for a plain or compound string read with `_textbox_string_end` (2448-2481; an
  unclosed string runs to the end), else `"bare"` for a run of non-blank, non-comma characters;
  a comma outside a string is a separator. `_dash_axis_head_split(text)` (new): `(head, tail)`
  at the first comma outside a string that is followed by optional blanks and a letter or
  underscore — the existing rule made quote-aware; `tail` is `""` when there is none.
- **TR-14.3** `_dash_parse_axis_label_opt(raw)` keeps its `(ticks, labels)` contract (ticks a
  sorted list of floats, labels `{str(float): text}`) and is rebuilt on TR-14.1/14.2: bare
  tokens between strings form one run expanded by `_dash_expand_numlist`; a `str` token labels
  the last value produced so far; further `str` tokens join it with `"\n"`; a string before any
  value is dropped and reported through the parser's `unsupported`. It no longer removes
  commas by regex: `_dash_axis_tokens` treats them as separators.
- **TR-14.4** `_dash_parse_axis_spec(raw)` uses `_dash_axis_head_split` for the head/tail
  split (replacing both regexes at 16648 and 16664 and the sub-option-stripping regex at
  16657-16660); reads a **leading** rule token — `#N`, `##N`, `none`, `minmax`, `.` — with
  `re.match(r"(##?\s*\d+|none|minmax|\.)\s*(.*)$", head, re.I)` and parses the remainder as the
  list, so mode `"count"` may carry non-empty `ticks`/`labels` (the `#N` clamp and the
  9-digit rule at 16676-16679 are unchanged); replaces the a(b)c regex block (16686-16714) with
  the tokenizer + expander, keeping the `_too_many` warning text verbatim (it names
  `_MAX_AXIS_TICKS:,`); appends the expander's `bad` tokens and the stray bare words to
  `unsupported` (replacing the loop at 16720-16730). Its honoured tuple (16635) gains
  `valuelabel` by prefix: any name of three or more letters that `"valuelabel"` starts with sets
  `out["valuelabel"] = True`. (Section 18 adds `norescale` to the same tuple.)
- **TR-14.5** `_dash_apply_axis_spec(axis_obj, grid_obj, spec, values=None, fmt_fallback="",
  grid_color=None, value_labels=None)`: in mode `"count"` with `spec["ticks"]`, set
  `ax._dash_extra_ticks = list(spec["ticks"])` on each axis and the overrides for
  `spec["labels"]`; `_dash_place_count_ticks` (17276-17331) unions
  `getattr(ax, "_dash_extra_ticks", [])` into the `FixedTicker` it writes and into `t_lo`/`t_hi`.
  With `spec["valuelabel"]` and a non-empty `value_labels` (`{code: text}`), the overrides
  become `{float(code): text for code with int(code) == float(code)}` updated by the explicit
  `spec["labels"]` (explicit text wins, or the reverse if probe `g16_vl_mixed` says so), on
  every mode that draws ticks; in mode `"explicit"` the formatter map carries the same union;
  in `"default"`/`"count"` only `major_label_overrides` is set (Bokeh applies an override only
  on a tick it matches, so unlabelled ticks keep the formatter). Underscore attributes on a
  Bokeh model are allowed (`fig._dash_count_entries` at 17349 already relies on it).
- **TR-14.6** `_dash_value_labels_for(var, value_labels, value_label_names)` (new, module
  level): the labelset-then-variable lookup of `_mlabel_value_labels`, returning `{}` for a
  non-dict; `GlyphMapper._mlabel_value_labels` becomes `return _dash_value_labels_for(var,
  getattr(self, "value_labels", {}), getattr(self, "value_label_names", {}))`, and the other
  four copies (6399-6405, 13909-13912, 15601-15607, 23598-23603) call it. `grep -c
  'value_labels.get(labelset' dash_render.py` is 1 afterwards.
- **TR-14.7** `_dash_apply_axis_options(fig, graph_opts, xvar, yvar, frame, numeric_formats,
  seen=None, key="", grid_color=None, value_labels=None, value_label_names=None)`: per axis,
  `_dash_value_labels_for(var, …)` with `var` = `xvar` for x options and `yvar` (the first y
  variable the caller passes) for y options, passed to `_dash_apply_axis_spec`. Call sites:
  22115 (saved: `self.value_labels`, `self.value_label_names`) and template 26266 (served:
  `val_labels`, `val_label_names`).
- **TR-14.8** `_dash_finish_secondary_axes(fig, graph_opts, seen=None, key="",
  grid_color=None, plots=None, value_labels=None, value_label_names=None)`: `ylabel2(,
  valuelabel)`/`xlabel2(, valuelabel)` map through the first layer with `yaxis`/`xaxis` `2`'s
  `yvar` (or `yvar1`) / `xvar`; call sites 22307 and 26399 pass `plots` and the two dicts. With
  `valuelabel` honoured by the parser, leaving the second axes out would drop it in silence.
- **TR-14.9** `_dash_hover_text_column(var)` (new) returns `f"__dash_hover_{var}"`;
  `_dash_add_hover_text(source, var, vlabels)` (new) writes that column to `source.data` when
  absent, from `source.data[var]` through `GlyphMapper._mlabel_value_text`, and returns the
  column name; it never overwrites an existing column of that name and skips a source whose
  `var` column is missing or of another length.
- **TR-14.10** `_dash_build_hover(…, layers=None, value_labels=None, value_label_names=None)`:
  before `_fields_for`, for each name in `hover_extra` whose `_dash_value_labels_for` is
  non-empty and which is not a date variable, call `_dash_add_hover_text` on every renderer
  source in `_rends` that carries it, and record `text_cols[name] = column`.
  `_dash_hover_row(col, label, date_kind="", numeric_fmt="", text_col=None)`: with `text_col`
  the field is `@{text_col}` with no format. `_fields_for` keeps its presence and
  `_DASH_VARNAME_RE` checks on the variable name and adds the text column's name to the
  columns a renderer must carry to get the full tooltip. Call sites 22348-22359 and template
  26451-26463 pass the dicts.
- **TR-14.11** dash.ado: `_dash_option_rules` graph list gains `xlabel=axislist ylabel=axislist
  xlabel2=axislist ylabel2=axislist xtick=axislist ytick=axislist xmtick=axislist
  ymtick=axislist xmlabel=axislist ymlabel=axislist`. `_dash_validate_value` gains kind
  `axislist`: `norm` is the value returned by the new program `_dash_axis_expand`, never a
  refusal unless TR-14.13 says so.
- **TR-14.12** `_dash_axis_expand` (new ado program, `c_local`/rclass in the file's style) with
  Mata `_dash_axis_pieces(s)` (new, dash_parse.mata beside `_dash_rep_toks` 4064): the head is
  cut from the tail at the first comma outside a string followed by blanks and a letter or
  underscore; the head is split into pieces — a leading rule token (`#N`, `##N`, `none`,
  `minmax`, `.`), plain or compound strings kept verbatim with their quotes, and runs of bare
  tokens (commas inside a run become blanks); each run is passed to `capture numlist
  "`run'"` (a run holds no double quote by construction) and replaced by `r(numlist)` when
  `_rc == 0`; the pieces and the tail are reassembled with single blanks and the tail's comma.
  Runs that `numlist` refuses are left as written (the renderer names or bounds them). It runs
  on the merged text, after `_dash_rep_merge`.
- **TR-14.13** Refusals follow the measured rc: where probe `a1_bad_step` (`xlabel(1(0)5)`)
  and `a1_bad_word` show twoway refusing, `_dash_axis_expand` refuses with the same rc and
  wording (r(198)/r(121) as measured, echoed through `_dash_say`); where twoway draws, dash
  leaves the run as written. `numlist`'s own element cap (r(123), 1,600 elements) is always
  "left as written": the renderer's bound decides.
- **TR-14.14** Served redraw: in the template's `_on_filter_change` step 3, after `_live.data =
  _dash_keep_jitter(...)`, for each `(var, vlabels)` in a build-time dict `_hover_label_vars`
  (the `hover()` variables with labels, computed once beside 26451) call
  `_dash_add_hover_text(_live, var, vlabels)`.
- **TR-14.15** Copy lists: functions 24466-24687 gain `_dash_expand_numlist`,
  `_dash_axis_tokens`, `_dash_axis_head_split`, `_dash_value_labels_for`,
  `_dash_hover_text_column`, `_dash_add_hover_text`; no new constant. `test/function_test_map.py`
  gains an entry per new function (no nested `def` inside them, so no `<locals>` entries);
  `test/program_coverage_map.py` gains `_dash_axis_expand` and `_dash_axis_pieces`.
- **TR-14.16** Security: label and value-label text travels as data — overrides and the
  formatter's `args` (canvas), the hover column (a tooltip field value BokehJS escapes; never
  `{safe}`); no user text reaches `code`, an f-string of JS, or `exec`. The ado side builds no
  command line from the text except `numlist "`run'"` where `run` cannot hold a quote.

## Boundaries

- No change to the formatter map's keys (`str(float)`), to `_dash_date_axis_spec`, to
  `_dash_apply_tick_option`'s CustomJSTicker mechanism, to `_dash_count_ticker`/`_dash_count_of`,
  or to the `#N` placement rule (`_dash_axis_count_ticks`).
- Widening the axis to label/tick values, `norescale`, and every `range()` change are
  **Section 18**; this section only leaves the positions where 18 reads them (the FixedTicker
  ticks, `ax._dash_extra_ticks`, the CustomJSTicker `extra`).
- Textbox sub-option abbreviations, `axis(#)` routing, `xtitle("")` are **Section 13**.
- `__mlabel__*` renaming and the `__dash` refusal are **Section 07**; this section only uses
  the prefix. `_dash_json_value`'s coercion of numeric-looking strings in snapshots is
  **Section 17** (X1): a value label spelled like a number can still be coerced after a saved
  move until 17 lands — record, do not fix here.
- `xmtick`, `ymtick`, `xmlabel`, `ymlabel` stay in `_dash_pending` (B10, out of scope): their
  text is normalised, not drawn.
- x and y variables in the tooltip keep their numbers: only `hover()` variables get the label
  column (twoway has no tooltip; `list`/`browse` show labels for the variables the user asks
  for). The colour key, facet titles, CSV and dropdowns already show labels and are untouched.
- `ylabel(, format())` on a value-labelled tick: the override wins, as Bokeh draws it; not
  probed.
- No new Bokeh model, no JS change, no change to `_FILTER_JS` (the snapshot carries the
  column).

## Stata truth

Extend `scripts/extract_axis_truth.do`. The probe registration gains two optional arguments:
`zp id group dataset body opts ticks hull` — `ticks` the positions the option asks for, ascending
(for the SVG fit when labels are text); `hull` is Section 18's. The record line gains both. A
dataset name `auto_vl` is handled in the loop as `sysuse auto, clear` followed by `label define
alrep 1 "Poor" 2 "Fair" 3 "Average" 4 "Good" 5 "Excellent"` and `label values rep78 alrep`.
The trailing `python:` block imports `svg_texts` and `svg_axis_extent` from
`scripts/svg_truth.py` (`sys.path.insert(0, os.path.join(REPO, "scripts"))`) and, for every
probe in groups `b1_label` and `g16_valuelabel`, records `texts` (`[t["text"] for t in
svg_texts(svg)]`: the normalised text of every `<text>` element, U+00A0 to a space, in document
order) and, when `ticks` is given, `x_axis.mapping` from `svg_axis_extent(svg, "x", ticks)`
(Section 02's `low`/`high`/`space`/`reversed`, stored under the fixture's `axis_low`/
`axis_high` names) instead of the label-parsing fit — `tick_values` needs one entry per tick
pixel in axis order or the reader raises `ValueError`; catch it and `None`, record the reason
under `unverified`, and keep the tick pixel positions. The block never calls Stata and writes
any backtick as `\x60`.

Probes (group `b1_label`, dataset `auto` unless noted; body `twoway scatter mpg weight`, or
`twoway scatter mpg rep78` where the positions are 0-10):

| id | option | ticks | records |
|---|---|---|---|
| `a1_pairs3` | `xlabel(1 "2019" 2 "2020" 3 "2021")` (rep78) | 1 2 3 | three texts |
| `a1_twolines` | `xlabel(2000 "low" "end" 4000 "high")` | 2000 4000 | rc; whether "end" is a second line |
| `a1_compound` | ``xlabel(2000 `"c "q" d"' 4000 "high")`` | 2000 4000 | the text `c "q" d` |
| `a1_to` | `xlabel(2000 2500 to 4000)` | 2000 2500 3000 3500 4000 | positions |
| `a1_colon` | `xlabel(2000 2500:4000)` | same | positions |
| `a1_colon_sp` | `xlabel(2000 2500 : 4000)` | same | rc (spaces around `:`) |
| `a1_slash` | `xlabel(1/5)` (rep78) | 1 2 3 4 5 | |
| `a1_slash_down` | `xlabel(5/1)` (rep78) | 1 2 3 4 5 | |
| `a1_bracket` | `xlabel(1[1]3)` (rep78) | 1 2 3 | |
| `a1_step2` | `xlabel(1(2)10)` (rep78) | 1 3 5 7 9 | 10 absent |
| `a1_negstep` | `ylabel(40(-10)10)` | 10 20 30 40 (y) | |
| `a1_frac` | `ylabel(10(2.5)20)` | 10 12.5 15 17.5 20 (y) | |
| `a1_hash_list` | `xlabel(#5 3000 "three")` | — | the count ticks and "three" |
| `a1_hash_incr` | `xlabel(#3 2000(1000)4000)` | — | |
| `a1_run_label` | `xlabel(2000(1000)4000 "top")` | 2000 3000 4000 | which value gets "top" |
| `a1_commas` | `xlabel(2000,3000,4000)` | 2000 3000 4000 | |
| `a1_commas_grid` | `xlabel(2000,3000,4000, grid)` | same | rc and gridlines |
| `a1_spaces_incr` | `xlabel(2000 (500) 4000)` | — | rc |
| `a1_single_quote` | `xlabel(2000 'a' 4000)` | — | rc |
| `a1_str_first` | `xlabel("a" 2000)` | — | rc |
| `a1_bad_step` | `xlabel(1(0)5)` | — | rc and message |
| `a1_bad_word` | `xlabel(2000 abc 4000)` | — | rc and message |
| `a1_mixed` | `xlabel(1 2 3/5 8(2)12)` (rep78) | 1 2 3 4 5 8 10 12 | |

Group `g16_valuelabel`, dataset `auto_vl`:

| id | command | records |
|---|---|---|
| `g16_vl_slash` | `twoway scatter mpg rep78, xlabel(1/5, valuelabel)` | Poor … Excellent |
| `g16_vl_abbrev` | `…, xlabel(1/5, val)` | the same |
| `g16_vl_unlabelled` | `…, xlabel(0/6, valuelabel)` | "0" and "6" as numbers |
| `g16_vl_mixed` | `…, xlabel(1 "one" 2/5, valuelabel)` | which text is drawn at 1 |
| `g16_vl_default` | `…, xlabel(, valuelabel)` | what the default ticks show |
| `g16_vl_y` | `twoway scatter rep78 mpg, ylabel(1/5, valuelabel)` | the y labels |
| `g16_vl_off` | `twoway scatter mpg rep78, xlabel(1/5)` | numbers (control) |

Run from a scratch directory: `mkdir -p /tmp/dash-s14 && cd /tmp/dash-s14 && STATATMP=/tmp/dash-s14/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_axis_truth.do`
(the trailing slash on `STATATMP`; never the GUI; at most three Stata sessions at once — Section
18 runs the same script, so coordinate: one run per section, or one run after both sections'
probes are registered). The fixture is `*.json` and hidden by `.git/info/exclude`: `git add -f
test/fixtures/axis_truth.json`. `test_fixtures_are_committed.py` requires a test to name it —
`test_axis_options.py` already does, and the new tests read it too.

## TDD test stubs

All B1 stubs in **`test/test_axis_label_grammar.py`** (new), all G16 stubs in
**`test/test_value_labels_drawn.py`** (new). Both-mode helper `_figures(mode, tmp_path, df,
plots, go, formats=None, value_labels=None, label_names=None)` modelled on
`test_natscale_axes._figures` (312-339) with `make_data_json(df, value_labels, label_names)`.
The first stubs are the regression tests that fail at `91d97be`.

- Test: `TestLabelledTicks::test_value_text_pairs_draw_three_labelled_ticks` —
  `xlabel(1 "2019" 2 "2020" 3 "2021")`: FixedTicker `[1, 2, 3]`, overrides `{1: "2019", 2:
  "2020", 3: "2021"}`, no warning, both modes. Pre-fix: ticks `[1, 2, 3, 2019, 2020, 2021]`.
- Test: `TestLabelledTicks::test_a_second_string_is_a_second_line` — `{2000: "low\nend",
  4000: "high"}` (or as `a1_twolines` records). Pre-fix: `"end"` lost.
- Test: `TestLabelledTicks::test_a_compound_string_is_one_label` — override `c "q" d`.
  Pre-fix: a lone backtick.
- Test: `TestLabelledTicks::test_single_quotes_are_characters` — `xlabel(2000 'a' 4000)`:
  ticks `[2000, 4000]`, no overrides, `'a'` named once in both modes.
- Test: `TestLabelledTicks::test_a_string_labels_the_last_value_of_its_run` — per
  `a1_run_label`.
- Test: `TestLabelledTicks::test_a_string_before_any_value_is_named_not_drawn`.
- Test: `TestNumlistForms::test_each_form_draws_statas_values[form]` — parametrised over
  `1/5`, `5/1`, `-2/2`, `1[1]3`, `1(2)10`, `9(-2)1`, `-1(.5)2.5`, `10 20 to 40`, `1 2 : 5`,
  `1 2:5`, `1 2 3/5 8(2)12`, `1,2,3`, `1,2,3, grid` with the expected lists; both modes.
  Pre-fix: `1/5` named; `to` becomes a label.
- Test: `TestNumlistForms::test_a_rule_then_a_labelled_list` — `#5 50 "fifty"` on mpg: after
  `_dash_finish_count_ticks` the FixedTicker holds 10, 20, 30, 40 and 50, overrides `{50:
  "fifty"}`. Pre-fix: `[50]` only.
- Test: `TestNumlistForms::test_xlabel2_ytick_and_a_date_axis_share_the_grammar` —
  `ylabel2(1/3)` beside a `yaxis(2)` layer, `xtick(2000 2500 to 4000)` (CustomJSTicker
  `extra`), `xlabel(14977/14980)` on a `%td` axis (four epoch-ms ticks).
- Test: `TestTheBound::test_every_form_is_held_to_the_limit[form]` — `0(0.000001)1000000`,
  `0/2000000`, `0 1 to 5000000`, `0[0.5]5000`: mode default, empty ticks, one note naming
  `2,000`, under 2 s, both modes (`served_app["_dash_parse_axis_spec"]` as
  `test_adversarial_matrix.py:1597` does).
- Test: `TestTheExpander::test_forms`, `::test_a_zero_step_is_bad`, `::test_to_needs_two_values`,
  `::test_the_count_is_taken_before_any_value_is_made`, `::test_non_finite_endpoints_do_not_raise`
  — unit tests of `_dash_expand_numlist`. Pre-fix: `AttributeError`.
- Test: `TestTheTokenizer::test_compound_quotes_nest`, `::test_an_unclosed_string_runs_to_the_end`,
  `::test_a_comma_inside_a_string_is_text`, `::test_the_head_split_is_quote_aware` — unit tests
  of `_dash_axis_tokens` and `_dash_axis_head_split`.
- Test: `TestAgainstTwoway::test_every_b1_probe_draws_the_texts_twoway_drew` — for each
  `b1_label` probe with rc 0 in `axis_truth.json`, dash's override values (in tick order) equal
  the probe's non-numeric tick texts, and its FixedTicker equals the probe's `ticks`; the test
  fails, not skips, when the fixture lacks the group ("task 14-02 must land first").
- Test: `TestHostileLabels::test_label_text_stays_data_in_both_modes` — `1 "</script><script>
  alert(1)</script>" 2 "x y"`: the code is the fixed parser, the labels are in `args` and
  overrides whole, the page has no `<script>alert(1)`.
- Flip: `test_graph_options.py::TestParseAxisLabelOpt::test_single_quoted_label`.

G16:

- Test: `TestValueLabelsOnAxes::test_valuelabel_draws_the_label_set` — frame with `rep78`
  1-5 and labels Poor…Excellent; `xlabel(1/5, valuelabel)`: overrides `{1: "Poor", …, 5:
  "Excellent"}`, no warning, both modes. Pre-fix: overrides empty, `valuelabel` named.
- Test: `TestValueLabelsOnAxes::test_val_is_the_minimum_abbreviation`.
- Test: `TestValueLabelsOnAxes::test_an_unlabelled_code_keeps_its_number` — `xlabel(0/6,
  valuelabel)`: 0 and 6 absent from the overrides.
- Test: `TestValueLabelsOnAxes::test_y_options_map_through_the_first_y_variable` and
  `::test_ylabel2_maps_through_the_second_axis_layer`.
- Test: `TestValueLabelsOnAxes::test_explicit_text_and_a_value_label_on_one_tick` — per
  `g16_vl_mixed`.
- Test: `TestValueLabelsOnAxes::test_without_valuelabel_nothing_changes` — the HC2-41 twin.
- Test: `TestValueLabelsOnAxes::test_the_default_ticker_keeps_its_formatter` — `xlabel(,
  valuelabel)`: BasicTicker kept, overrides set for every labelled code.
- Test: `TestTheLookup::test_by_set_name`, `::test_by_variable_name_as_jsonio_writes_it`,
  `::test_none`, `::test_a_non_dict_is_empty` — `_dash_value_labels_for`. Pre-fix:
  `AttributeError`.
- Test: `TestTheLookup::test_the_five_copies_are_gone` — `grep`-style read of dash_render.py:
  the idiom `value_labels.get(labelset, {}) if labelset` appears once, inside the helper.
- Test: `TestHoverShowsValueLabels::test_hover_foreign_shows_domestic_and_foreign` —
  `hover(foreign)` on `test_mode_parity._DF` with `_VALUE_LABELS`/`_LABEL_NAMES`: the
  HoverTool's row for `foreign` is `("foreign", "@{__dash_hover_foreign}")` and the scatter
  source's column is `["Domestic", "Foreign", …]`, both modes. Pre-fix: `@{foreign}`.
- Test: `TestHoverShowsValueLabels::test_the_column_is_on_every_source_the_tooltip_attaches_to`
  — `(scatter)(bar)` with `hover(foreign)`: both sources carry the column; a fit's source,
  which carries no `foreign`, keeps the generic tooltip.
- Test: `TestHoverShowsValueLabels::test_the_saved_snapshot_carries_the_column` — the
  `all_graph_sources_orig` snapshot for the graph's source has `__dash_hover_foreign`.
- Test: `TestHoverShowsValueLabels::test_a_served_redraw_re_adds_the_column` — `(scatter mpg
  weight)(lfit mpg weight)` served with `hover(foreign)`: fire a filter move
  (`test_help_claims_3.py:415-497`'s `tp._fire` pattern), then every source the hover tool lists
  still carries the column.
- Test: `TestHoverShowsValueLabels::test_a_hostile_value_label_is_data` — label
  `<img src=x onerror=alert(1)>`: the tooltip field is not `{safe}`, the page holds no raw
  `<img src=x onerror`.
- Test: `TestHoverShowsValueLabels::test_the_parity_cases_with_hover_foreign` — cases 1133 and
  1134 rendered through `tp._standalone`/`tp._served`: the same tooltip rows and column values.
- Test: `TestAgainstTwoway::test_every_g16_probe_draws_the_texts_twoway_drew`.
- Flips: `test_suboption_warnings.py` "xlabel valuelabel" entry; `test_mode_parity.py`
  MUST_WARN "xlabel with an unimplemented sub-option" and its case; SR-02 in
  `test_suboption_reporting.cscript`.

**Mutation table** (apply, see the named test fail, revert):

| break this | test that must die |
|---|---|
| in `_dash_parse_axis_label_opt`, attach a string to the *first* value of the run | `test_a_string_labels_the_last_value_of_its_run` |
| in `_dash_expand_numlist`, use `<` instead of `<=` for the `a(b)c` limit | `test_each_form_draws_statas_values[1/5]` (5 missing) |
| skip the pre-count and expand first | `test_every_form_is_held_to_the_limit[0(0.000001)1000000]` (times out) |
| key the value-label overrides by `str(code)` | `test_valuelabel_draws_the_label_set` |
| return `{}` from `_dash_value_labels_for` for the variable-keyed form | `test_by_variable_name_as_jsonio_writes_it` and `test_marker_label_parity.py::TestTheLabelSetLookup::test_keyed_by_variable_as_jsonio_writes_it` |
| drop the redraw hook of TR-14.14 | `test_a_served_redraw_re_adds_the_column` |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| each numlist form, labelled pairs, lines, compound quotes, single quotes, rule+list | pytest `test_axis_label_grammar.py` | `axis_truth.json` (`b1_label`) | yes |
| the bound in every form | pytest `TestTheBound`, `test_adversarial_matrix.py::TestAxisLabelBounds` | — | yes |
| expander and tokenizer units | pytest | — | n/a |
| ado expansion (`numlist` reached, tail kept, merged text) | cscript `test_axis_labels.cscript` AL-01..AL-04 (spec JSON read with `cert_file_has`) | — | n/a |
| twoway's ticks and texts vs dash's page | cscript AL-05..AL-16 (`cert_svg_export` + `cert_svg_texts`; page needles) | — | saved page |
| `valuelabel`, `val`, unlabelled code, y, second axis | pytest `test_value_labels_drawn.py` | `axis_truth.json` (`g16_valuelabel`) | yes |
| `hover()` label column, snapshot, served redraw, hostile label | pytest | — | yes |
| twoway's valuelabel texts vs dash's | cscript AL-17..AL-19 | — | saved page |
| the note is gone | pytest `test_suboption_warnings.py`, cscript SR-02 (flipped) | — | yes |
| copy lists, function map | `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_function_test_map.py`, `test_program_coverage_map.py` | — | served |

Acceptance criteria:

- **AC-14.1** `xlabel(1 "2019" 2 "2020" 3 "2021")` draws ticks 1, 2, 3 labelled 2019, 2020,
  2021 in both modes, with no note; the cscript finds the same three texts in twoway's SVG and
  dash's page.
- **AC-14.2** Every form in `TestNumlistForms` draws Stata's values in both modes; `1(2)10`
  draws 1, 3, 5, 7, 9; the ado spec for `xlabel(1/5)` carries `1 2 3 4 5`.
- **AC-14.3** A second string is a second line and a compound string keeps its inner quotes,
  as the `a1_twolines`/`a1_compound` probes record.
- **AC-14.4** `#5 50 "fifty"` draws the five count ticks and 50 labelled "fifty".
- **AC-14.5** `0(0.000001)1000000` and its `/`, `to`, `[ ]` twins keep the default ticks with
  one note, under 2 s, in both modes; dash.ado does not refuse them.
- **AC-14.6** `xlabel(1/5, valuelabel)` draws Poor…Excellent in both modes and prints nothing;
  `val` works; an unlabelled code keeps its number; y maps through the first y variable.
- **AC-14.7** `hover(foreign)` shows Domestic/Foreign in both modes, on every source the
  tooltip attaches to, before and after a filter move.
- **AC-14.8** `grep -c 'value_labels.get(labelset' dash_render.py` is 1; every new function is
  in the copy list and `function_test_map.py`; the full pytest suite and the cert suite pass
  with no skip.
- **AC-14.9** BUGS.md carries closed B1 and G16 entries naming their tests; dash.sthlp 672-680
  and 2318-2327 and CHANGELOG are updated.

## Tasks

Commit boundaries: 14-01's B1 tests, 14-02, 14-03, 14-04, 14-05 and 14-06 are **one commit
(B1)**; 14-01's G16 tests and 14-07 to 14-11 are **one commit (G16)**. The full pytest suite
runs green once before each commit (CLAUDE.md rules 4 and 11); the failing-test output of 14-01
is pasted into the respective commit message. No AI references anywhere.

<task type="auto" id="14-01">
  <name>Write the failing tests for both gaps</name>
  <files>test/test_axis_label_grammar.py, test/test_value_labels_drawn.py</files>
  <action>
    Create the two files. Module docstrings state the defects in CHANGELOG terms: `xlabel(1 "2019" 2 "2020" 3 "2021")` drew six unlabelled ticks; `10 20 to 40` drew 10, 20, 40 with `to` as a label; `1/5` and `1[1]3` drew the default ticks; `#5 50 "fifty"` lost the `#5`; `xlabel(1/5, valuelabel)` was named and drew numbers; `hover(foreign)` showed 0/1. Copy the header block of `test/test_natscale_axes.py` (imports, `_HERE`, the `sys.path` inserts, `_MODES`, `_SEQ`) and its `_figures` helper, adding `value_labels`/`label_names` arguments passed to `make_data_json`; a rep78-like frame builder `_rep_frame()` with codes 0-6 and the label set Poor…Excellent under set name `alrep` keyed by `{"rep78": "alrep"}`; and a `truth()` module fixture that `pytest.fail`s (never skips) when `test/fixtures/axis_truth.json` lacks the `b1_label` / `g16_valuelabel` group ("task 14-02 must land first"). Write every stub of "TDD test stubs" with exactly those names, including the mutation-sensitive assertions. For the hover tests import `test_mode_parity as tp` and use `tp._spec`, `tp._standalone`, `tp._served`, `tp._DF`, `tp._VALUE_LABELS`, `tp._LABEL_NAMES`; for the served redraw reuse the `_fire` pattern of `test_help_claims_3.py:415-497`. Do not touch `dash_render.py` or `dash.ado`. Run each file alone against the unmodified tree and keep the failure summaries for the two commit messages.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_axis_label_grammar.py test/test_value_labels_drawn.py -q 2>&1 | tail -5` shows 0 passed, no collection error; `python3 -m pytest test/test_axis_label_grammar.py -q -k value_text_pairs 2>&1 | grep -c "2019.0"` is non-zero (the headline fails on the wrong tick list, not on an exception).]]></verify>
  <done>Both test files exist, collect cleanly, and every test in them fails at 91d97be for the reason its stub names.</done>
</task>

<task type="auto" id="14-02">
  <name>Record twoway's readings in the axis fixture</name>
  <files>scripts/extract_axis_truth.do, test/fixtures/axis_truth.json</files>
  <action><![CDATA[
    In `scripts/extract_axis_truth.do`: extend `zp` (106-119) with optional `ticks` (arg 6) and `hull` (arg 7) globals and write both into the PROBE record line (after `shown`); add the `auto_vl` dataset branch in the export loop (`if "`ds'" == "auto_vl" { sysuse auto, clear ... label define alrep ... label values rep78 alrep }`, and reset `curds` logic accordingly); register every probe of the "Stata truth" tables in groups `b1_label` and `g16_valuelabel`, compound-quoted where the option holds quotes (`zp "a1_compound" ... `"xlabel(2000 `"c "q" d"' 4000 "high")"'` — check the nesting by echoing each `shown` line in the log). In the `python:` block: `sys.path.insert(0, os.path.join(REPO, "scripts"))`, `from svg_truth import svg_texts, svg_axis_extent`; parse the two new record fields; for probes in the two new groups write `texts` (from `svg_texts`, U+00A0 normalised) and, when `ticks` is non-empty, replace `x_axis["mapping"]` (or `y_axis`) with `svg_axis_extent(svg, axis, ticks)`; keep `rc` and the log's error line for the `a1_bad_*`, `a1_single_quote`, `a1_str_first`, `a1_spaces_incr` probes in a new `findings.label_refusals` map. No backtick literal in the block (`\x60`); the block calls no Stata. Run Stata from a scratch directory with `STATATMP` as the "Stata truth" section says, read the log for `probe <id> rc=`, then `git add -f test/fixtures/axis_truth.json`.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -c "import json; d=json.load(open('test/fixtures/axis_truth.json')); p=d['probes']; print(p['a1_pairs3']['texts'], p['g16_vl_slash']['texts'], d['findings']['label_refusals'])"` prints the three year texts, Poor…Excellent, and the rc map; `git ls-files test/fixtures/axis_truth.json` prints the path; `python3 -m pytest test/test_axis_options.py -q 2>&1 | tail -2` is still green.]]></verify>
  <done>The fixture records twoway's texts, tick positions and return codes for every B1 and G16 form, produced by Stata and committed.</done>
</task>

<task type="auto" id="14-03">
  <name>Port the numlist rules and the tokenizer</name>
  <files>dash_render.py, test/function_test_map.py, test/test_graph_options.py</files>
  <action>
    Implement TR-14.1 to TR-14.5 in `dash_render.py`: `_dash_expand_numlist`, `_dash_axis_tokens`, `_dash_axis_head_split` beside `_MAX_AXIS_TICKS` (16081); rebuild `_dash_parse_axis_label_opt` on them (same `(ticks, labels)` contract); in `_dash_parse_axis_spec` replace the two `_m_tail`/`m_sub` regexes and the sub-option-stripping regex with the head split, read a leading rule token, replace the a(b)c block with the expander (keep the `_too_many` warning text), append `bad` and stray words to `unsupported`, and honour `valuelabel` by prefix (`out["valuelabel"]`, default False); in `_dash_apply_axis_spec` add `value_labels=None`, the `_dash_extra_ticks` stash for count mode and the value-label overrides; in `_dash_place_count_ticks` union `_dash_extra_ticks` into the FixedTicker and the tick extremes. Read the `a1_twolines`, `a1_run_label`, `a1_spaces_incr`, `a1_single_quote` and `label_refusals` records first and write the rule the way twoway read it (a comment cites the probe id). Add the three new functions to the copy list (24466-24687) and to `test/function_test_map.py` (naming tests from `test_axis_label_grammar.py`). Flip `test_graph_options.py::TestParseAxisLabelOpt::test_single_quoted_label` to assert ticks `[1.0, 2.0]` and `labels == {}` with a docstring saying Stata's single quote is a character.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_axis_label_grammar.py test/test_adversarial_matrix.py -k "Grammar or Labelled or Numlist or Bound or Expander or Tokenizer or Injection or Hostile or Twoway" -q 2>&1 | tail -3` is green; `python3 -m pytest test/test_axis_options.py test/test_graph_options.py test/test_served_dates.py test/test_help_claims_8.py -q 2>&1 | tail -3` is green.]]></verify>
  <done>The renderer reads every numlist form, quoted strings, lines, compound quotes and a rule before a list, bounded as before, in both modes; `valuelabel` is parsed but not yet fed with labels.</done>
</task>

<task type="auto" id="14-04">
  <name>Expand axis numlists with Stata's numlist in dash.ado</name>
  <files>dash.ado, dash_parse.mata, test/program_coverage_map.py</files>
  <action>
    Implement TR-14.11 to TR-14.13. In `dash_parse.mata`, beside `_dash_rep_toks` (4064), add `_dash_axis_pieces(string scalar s)` returning a string colvector of pieces tagged by a leading character (`R` rule, `S` string, `B` bare run, `T` tail) using the same quote-and-parenthesis walk `_dash_rep_toks` uses; add a unit case for it to the cscript of 14-05 (AL-02). In `dash.ado`, add `_dash_axis_expand` (reads its text by value through `_dash_text_args` as `_dash_validate_value` does at 1957; loops the pieces; for each `B` piece replaces commas by blanks and runs `capture numlist "`run'"`, substituting `r(numlist)` on rc 0; on the rc the `label_refusals` finding shows twoway refusing, refuses with the same rc and wording through `_dash_say`; reassembles with the tail's comma). Add kind `axislist` to `_dash_validate_value` (norm from `_dash_axis_expand`, no bounds) and the ten `=axislist` rules to `_dash_option_rules`'s graph list (1910-1912). Add both programs to `test/program_coverage_map.py` with references `test_axis_labels.cscript:AL-01` and `:AL-02`.
  </action>
  <verify><![CDATA[`cd /tmp/dash-s14 && STATATMP=/tmp/dash-s14/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do probe.do` where probe.do runs `sysuse auto` then `dash scatter mpg weight, xlabel(1/5 "five" 10 20 to 40, grid) name(t1)` and `dash build, saving(t1.html)` with `global dash_nobrowser 1`, prints rc 0 and the log's spec JSON line carries `"xlabel":"1 2 3 4 5 \"five\" 10 20 30 40, grid"`; `python3 -m pytest test/test_unsupported_report_is_true.py test/test_option_surface.py -q 2>&1 | tail -2` is green.]]></verify>
  <done>dash.ado writes Stata's own expansion of every axis numlist into the spec, strings and sub-options untouched, and refuses only what twoway refuses.</done>
</task>

<task type="auto" id="14-05">
  <name>Certify the label grammar against twoway</name>
  <files>test/test_axis_labels.cscript, test/run_all_cscripts.do</files>
  <action><![CDATA[
    Create `test/test_axis_labels.cscript` in the style of `test_help_claims_2.cscript` (a `*!` case index; `cscript` line; `global dash_nobrowser 1` immediately after it; `quietly do "cert_helpers.do"` and `quietly do "cert_svg.do"` from `test/` before any `cd`, as Section 02 prescribes — `cert_svg.do` derives its scripts directory from `c(pwd)` and exits 222 itself when `c(python_exec)` is empty, so no other Python probe is written; a `_al_ok id ok what` PASS/FAIL helper like `_hc2_ok` 248-259). Cases: AL-01 `_dash_axis_expand` on `1/5 "five" 10 20 to 40, grid` returns the expanded text; AL-02 `_dash_axis_pieces` splits a compound-quoted label with a comma inside; AL-03 the registry JSON for `xlabel(1(2)10)` carries `1 3 5 7 9` (`cert_file_has ... needle(...)`); AL-04 `xlabel(0(0.000001)1000000)` registers with rc 0 and builds with the `2,000` note in the log. AL-05..AL-16: for each B1 form in the "Stata truth" table with rc 0, `twoway scatter mpg weight|rep78, xlabel(...)` then `cert_svg_export, file()`, `cert_svg_texts, file()` (`r(n)` texts) and one `cert_svg_has_text, file() text("<label>")` per expected label (`r(found)`), then `dash ..., name(alN)` + `dash build, saving()`, and assert with `cert_file_has` that the page carries each label text and the FixedTicker list (measure the exact JSON spelling of `"ticks":[...]` and the overrides `entries` on AL-05 once and pin it as a `*!` note at the top). AL-17..AL-19 are G16's (task 14-10) — leave numbered gaps. Register the script in `test/run_all_cscripts.do` in the block shape at 60-87 (`test_cscript_hygiene.py::TestEveryCscriptIsWiredIntoTheRunner` requires it) and bump the count `test_cscript_hygiene.py:294` reads if Section 02's #66 made it a count. Run it alone from a scratch directory with `STATATMP`.
  ]]></action>
  <verify><![CDATA[`cd /tmp/dash-s14 && STATATMP=/tmp/dash-s14/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_axis_labels.cscript && grep -c " PASS" test_axis_labels.log` prints 16 and `grep -c " FAIL\| SKIP" test_axis_labels.log` prints 0; `python3 -m pytest test/test_cscript_hygiene.py test/test_program_coverage_map.py -q 2>&1 | tail -2` is green.]]></verify>
  <done>A registered certification script proves, live, that twoway and dash draw the same ticks and texts for every B1 form and that dash.ado's expansion reaches the spec.</done>
</task>

<task type="auto" id="14-06">
  <name>Close B1 in BUGS.md, help and CHANGELOG</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action>
    Append a closed BUGS.md entry (`- [x] Title: Axis-label rules misread quoted numeric text, multi-line labels and numlist forms (GAPS2 B1)` with the four fields in order; Resolution names `test/test_axis_label_grammar.py::TestLabelledTicks::test_value_text_pairs_draw_three_labelled_ticks` and `test/test_axis_labels.cscript` AL-05, and states the measured readings of the two undocumented forms). In dash.sthlp 2318-2327 extend the vocabulary table: `a/b`, `a[b]c`, `a b to c`, `a b:c`, value `"text"` pairs, a second string as a second line, compound quotes, a rule before a list, and that dash.ado expands the list with Stata's `numlist` (the 2,000-tick bound stays as documented). In CHANGELOG.md under `### Results that change` add the B1 item with the command, the old ticks and the new ones (`xlabel(1 "2019" 2 "2020" 3 "2021")`: was six ticks unlabelled, now three labelled; `10 20 to 40`: was 10 20 40, now 10 20 30 40; `1/5`, `1[1]3`: were the default ticks; `#5 50 "fifty"`: 50 alone, now both) marked (WP-28). Grep the three files and the commit message for `claude|anthropic` before committing. Pull local main, run the full suite once (`python3 -m pytest test/ -q`), commit the B1 group on `s3-bugs` with 14-01's failure summary in the message.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_1.py -q 2>&1 | tail -2` is green; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>B1 is closed in BUGS.md naming its tests, documented in dash.sthlp and CHANGELOG, and committed as one commit with a green full suite.</done>
</task>

<task type="auto" id="14-07">
  <name>Replace the five label-set lookups with one</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    Implement TR-14.6: add `_dash_value_labels_for(var, value_labels, value_label_names)` at module level immediately before `_dash_attach_labels` (18745); make `GlyphMapper._mlabel_value_labels` a one-line call to it; replace the copies at `_apply_colorvar` (6399-6405), `_dash_csv_meta` (13909-13912), `_dash_facet_label` (15601-15607) and the saved filter builder (23598-23603) with calls, keeping each site's later type check where it existed. Add the function to the copy list and to `test/function_test_map.py` naming `test/test_value_labels_drawn.py::TestTheLookup::test_by_variable_name_as_jsonio_writes_it`.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && grep -c 'value_labels.get(labelset' dash_render.py` prints 1; `python3 -m pytest test/test_value_labels_drawn.py -k TheLookup test/test_marker_label_parity.py test/test_facets.py test/test_csv_download.py -q 2>&1 | tail -3` is green (substitute the facet and CSV test files the function map names for `_dash_facet_label` and `_dash_csv_meta`).]]></verify>
  <done>One module-level lookup serves the colour key, marker labels, CSV, facet titles and filters, and the served app carries it.</done>
</task>

<task type="auto" id="14-08">
  <name>Draw valuelabel on axes in both modes</name>
  <files>dash_render.py, test/test_suboption_warnings.py, test/test_mode_parity.py</files>
  <action>
    Implement TR-14.7 and TR-14.8: the two new parameters on `_dash_apply_axis_options` and on `_dash_finish_secondary_axes`, the per-axis lookup, and the four call sites (22115, 22307 saved; template 26266, 26399 served — the served ones pass `val_labels`, `val_label_names` and `plots`). Read `g16_vl_mixed` and `g16_vl_default` from the fixture and make the override merge follow them (comment the probe ids). Flip `test_suboption_warnings.py`: move the "xlabel valuelabel" SUBOPTIONS entry into `TestTheHonouredOnesStayQuiet`'s parametrisation. Flip `test_mode_parity.py`: the case at 1168-1169 becomes `{"xlabel": "#5, labcolor(red)", "ytitle": "Miles, orientation(vertical)"}` and its MUST_WARN text names `labcolor(red)`; add a corpus case `_case("xlabel(1/5, valuelabel)", [plot_for("scatter", xvar="rep")], None, {"xlabel": "1/5, valuelabel"})` (the parity `_DF` has `rep` 3-5 but no labels for it — add `"rep_lbl": {"3": "Three", "4": "Four", "5": "Five"}` to `_VALUE_LABELS` and `"rep": "rep_lbl"` to `_LABEL_NAMES`, and check the existing hover/facet cases still agree).
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_value_labels_drawn.py -k "OnAxes or Twoway" test/test_suboption_warnings.py test/test_mode_parity.py -k "valuelabel or unimplemented or hover" -q 2>&1 | tail -3` is green; `python3 -m pytest test/test_suboption_reporting.py -q 2>&1 | tail -2` names no new failure.]]></verify>
  <done>`xlabel(1/5, valuelabel)` draws the label set on the primary and second axes in both modes and prints nothing; the two pinned tests are flipped.</done>
</task>

<task type="auto" id="14-09">
  <name>Show value labels in tooltips through a derived column</name>
  <files>dash_render.py, test/test_mode_parity.py</files>
  <action>
    Implement TR-14.9, TR-14.10 and TR-14.14: `_dash_hover_text_column`, `_dash_add_hover_text` (module level, before `_dash_hover_row` 19795), the `text_col` parameter of `_dash_hover_row`, the value-label parameters and column pass of `_dash_build_hover` (columns added on every renderer source in `_rends` that carries the variable, before `_fields_for` runs), the two call sites (22348-22359 with `self.value_labels`/`self.value_label_names`; template 26451-26463 with `val_labels`/`val_label_names`), the template's build-time `_hover_label_vars` dict and the redraw hook in `_on_filter_change` step 3. Add the two functions to the copy list and to `function_test_map.py`. In `test_mode_parity.py` add the class `TestHoverShowsValueLabelsInBothModes` that renders cases "hover()" and "hover() on a bar" through `_standalone`/`_served` and asserts the tooltip row and column values agree (the corpus profile already compares tools and glyphs; this adds the values).
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_value_labels_drawn.py test/test_mode_parity.py -k "Hover or hover" test/test_server_layer_defects.py -k TheHoverBuilder test/test_label_sinks.py -q 2>&1 | tail -3` is green.]]></verify>
  <done>`hover(foreign)` shows Domestic/Foreign on every source the tooltip attaches to, in both modes, and the column survives a saved snapshot rebuild and a served redraw.</done>
</task>

<task type="auto" id="14-10">
  <name>Certify valuelabel and hover against twoway</name>
  <files>test/test_axis_labels.cscript, test/test_suboption_reporting.cscript</files>
  <action>
    Add AL-17..AL-19 to `test/test_axis_labels.cscript`: AL-17 defines the `alrep` label set on `sysuse auto`, exports `twoway scatter mpg rep78, xlabel(1/5, valuelabel)` and asserts with `cert_svg_has_text, file() text("Excellent")` and the dash page carrying every label text in its overrides; AL-18 the control `xlabel(1/5)` draws numbers in both; AL-19 `dash scatter mpg rep78, hover(rep78)` builds a page whose HoverTool references `__dash_hover_rep78` and whose source carries "Poor" (`cert_file_has`). Flip SR-02 in `test/test_suboption_reporting.cscript` (174-182): `_sr_check SR-02 "`lg'" xlabel "" "valuelabel"` — valuelabel is honoured and must not be named — and update the `*!` index line 20.
  </action>
  <verify><![CDATA[`cd /tmp/dash-s14 && STATATMP=/tmp/dash-s14/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do /Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_axis_labels.cscript && grep -c " PASS" test_axis_labels.log` prints 19; the same invocation of `test/test_suboption_reporting.cscript` shows `SR-02 PASS` and no FAIL.]]></verify>
  <done>twoway's valuelabel texts and dash's page agree live, and the certification suite no longer expects valuelabel to be named.</done>
</task>

<task type="auto" id="14-11">
  <name>Close G16 in BUGS.md, help and CHANGELOG</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append a closed BUGS.md entry `- [x] Title: Value labels are never drawn on axes or in tooltips (GAPS2 G16)` naming `test/test_value_labels_drawn.py::TestValueLabelsOnAxes::test_valuelabel_draws_the_label_set` and `::TestHoverShowsValueLabels::test_hover_foreign_shows_domestic_and_foreign`. Rewrite dash.sthlp 672-680 (difference 6): value labels are used automatically where listed, an axis is labelled with numbers unless `valuelabel` (minimum `val`) is given — then the first y variable's or the x variable's labels, as in twoway — and a hover tooltip shows the value label of a `hover()` variable; add `valuelabel` to the sub-option list at 2328-2331. CHANGELOG: under `### Fixed` (or `### New`) one G16 line naming `xlabel(, valuelabel)` and `hover()` (WP-28). Grep for `claude|anthropic`, pull local main, run the full suite once, commit the G16 group with 14-01's failure summary in the message, and report the merge command (`git checkout main && git merge s3-bugs`) without running it.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_2.py -q 2>&1 | tail -2` is green; `git status --short | grep -v '^??' | grep -v '.ultraplan\|REMAINING\|CLAUDE.md'` prints nothing.]]></verify>
  <done>G16 is closed in BUGS.md naming its tests, difference 6 in dash.sthlp is rewritten, CHANGELOG lists it, and the commit is on s3-bugs with a green full suite.</done>
</task>

<task type="checkpoint" id="14-12">
  <name>Verify both suites and the served twin</name>
  <files>none</files>
  <action>
    Run the full pytest suite once under the development Python (`python3 -m pytest test/ -q`) and once under Stata's (`make test`), then the certification suite (`make cert`, from a scratch directory with `STATATMP`), and confirm: no failure, no skip, `test_axis_labels.cscript` 19 PASS, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` green. Open one saved page and one served app for `dash scatter mpg rep78, xlabel(1/5, valuelabel) hover(rep78)` and read the axis and a tooltip. Present the two commit hashes and the merge command.
  </action>
  <verify>Both suite runs report 0 failed and 0 skipped; the maintainer confirms the axis reads Poor…Excellent and the tooltip shows the label.</verify>
  <done>Section 14 is verified end to end in both modes and both interpreters, and its two commits are ready to merge.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" passes in both modes; the four flipped tests and SR-02 pass
  in their new form; no test was deleted.
- `axis_truth.json` holds the `b1_label` and `g16_valuelabel` groups produced by Stata, is
  committed, and `TestAgainstTwoway` reads it.
- `test_axis_labels.cscript` is registered and passes with 19 PASS, 0 SKIP.
- `_dash_expand_numlist`, `_dash_axis_tokens`, `_dash_axis_head_split`,
  `_dash_value_labels_for`, `_dash_hover_text_column`, `_dash_add_hover_text` are in the copy
  list and in `function_test_map.py`; `_dash_axis_expand` and `_dash_axis_pieces` are in
  `program_coverage_map.py`.
- The full pytest suite is green under both interpreters with no skip; the cert suite passes.
- BUGS.md has closed B1 and G16 entries; dash.sthlp 672-680 and 2318-2331 and CHANGELOG are
  updated; two commits on `s3-bugs`, no AI references.
- Section 18 can read tick positions from `FixedTicker.ticks`, `ax._dash_extra_ticks` and the
  CustomJSTicker `extra`, and `norescale` has a tuple to join.

## Notes

- **Line numbers drift.** 14-03 adds about 150 lines near 16041; every later anchor is also a
  symbol — locate by `def` name, never by a bare number after an insertion.
- **Two undocumented readings are decided by the probes, not by taste.** Write the parser
  after reading `a1_twolines`, `a1_run_label`, `a1_spaces_incr`, `a1_single_quote`,
  `a1_str_first` and `label_refusals`; if `a1_spaces_incr` shows twoway refusing
  `2000 (500) 4000`, flip `test_axis_options.py::TestAxisLabelGrammar::test_increment_form_with_spaces`
  to that reading in 14-03 and say so in the commit message.
- **The bound is the renderer's.** Stata's `numlist` refuses more than 1,600 elements with
  r(123); the ado step leaves such a run as written and the renderer bounds it at 2,000. A
  1,601-2,000 list is expanded in Python only; document nothing new (dash.sthlp already states
  the 2,000 bound).
- **Renderer order differs.** The saved renderer styles axis titles before adding second axes,
  the served template after (report A §0.2); nothing here depends on that order, but the
  second-axis `valuelabel` runs in `_dash_finish_secondary_axes`, which both call after the
  layers.
- **Copy lists.** A new module-level name used by a copied function is a `NameError` in the
  served app at draw time, not at build time
  (`test_statistical_helpers.py::TestTheServedAppCarriesEveryName`).
- **Pending options.** `xmtick`, `ymtick`, `xmlabel`, `ymlabel` stay in `_dash_pending`;
  `test_unsupported_report_is_true.py` renders each with two values and expects no change —
  normalising their text keeps that true.
- **Fixture rules.** `git add -f` the JSON; the `python:` block never calls Stata; `\x60` for a
  backtick; `STATATMP=<dir>/tmp/` with the trailing slash from a scratch directory; at most
  three Stata sessions — many sessions can drop `python_exec` from
  `~/.stata19/console/stata19.rc`, after which every Python cscript SKIPs; a skip is not a
  pass; restore with `set python_exec /opt/anaconda3/bin/python3, permanently`.
- **`$dash_nobrowser`.** `cscript` drops every global: set `global dash_nobrowser 1` right
  after the `cscript` line or `test_cscript_hygiene.py` flags every build.
- **Security.** The value-label text in the hover column is a tooltip *field value*; BokehJS
  escapes it unless the field is written `{safe}` — never write `{safe}`. Label text in
  overrides is canvas text. `_DASH_VARNAME_RE` still gates the variable name; the derived
  column name is built from a name that passed it.
- **X1 interplay.** `_dash_json_value` (13828-13862) turns a numeric-looking string into a
  float in the saved snapshot; a value label such as "7" would come back as 7 after a move
  until Section 17 lands. Record it in the G16 BUGS.md entry as a known interaction, not a
  residual of this section.
