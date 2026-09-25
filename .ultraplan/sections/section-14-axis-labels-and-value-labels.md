# Section 14: Axis labels and value labels (B1, G16)

> Part of: WP-28 · Gaps: B1, G16 · Risk: red · Batch: 2 · Depends on: 02, 07 · Blocks: 12, 18 · Tasks: 15, 2 commits (B1, G16)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **02, 07** · Blocks **12, 18** · Risk **red** · Commits: two commits: B1 (14-01..14-09) and G16 (14-10..14-15) → CHANGELOG `Results that change`

- D9: risk is red (tokenizer plus ado numlist expansion plus a hover column across both twins).
- D10: use S07's Unicode-aware name check by its final name, `_dash_is_stata_name` (S07 removed the ASCII regex it replaces). The "no overlap with S12/S17" boundary claim is replaced by the D4 ordering: S17 and S16 merge before this section inside batch 2 (this section's `_on_filter_change` hook and `_vlookup` hunk are applied to their text); S12 runs in batch 3 on this section's signatures.
- D10: the E3 `%tm` axis-label probes `e3_tm_axis` / `e3_tm_axis_lab` (sp500's `m = mofd(date)`, `format m %tm`, `twoway line close m` bare and with `xlabel(492(3)501, format(%tm))`; ticks 492 495 498 501; texts `2001m1 2001m4 2001m7 2001m10`) are recorded by 14-03 in group `b1_label`; S12 cites them by id.
- D8: the checkpoint (old 14-12) is removed; ids are renumbered.
- A numeric run holding a backtick, `$` or `'` never reaches `numlist` (left as written; the renderer names it). Stubs: `valuelabel` under by() panels; `numlist`'s 1,600-element cap versus the 2,000 bound; the fixture's `_meta` keys.
- D7: 14-01 is one task per test file (14-01 B1, 14-10 G16, each in its gap's commit); the old 14-03 is three tasks (14-04, 14-05, 14-06); the AL cases are a block of `test/test_gaps2_truth.cscript` (D11), never a new script, never a hygiene-pin edit.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

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
both modes. The section also records, for section 12 (E3), twoway's tick text on a `%tm` axis.
Nothing new is printed once an option is drawn (DISCOVERY Q22).

**Test order (CLAUDE.md rule 7) and commit rule (D1): each gap's first task writes that gap's
regression tests** and runs them against the tree before the gap's fix, saving the failure text
to `<scratch>/14-01-failure.txt` (B1) and `<scratch>/14-10-failure.txt` (G16) -- neither
commits (a red tree is never committed, rule 4). 14-02 to 14-08 close B1 and 14-09 makes the B1
commit, subject ending `(GAPS2 B1)`; 14-11 to 14-14 close G16 and 14-15 makes the G16 commit,
`(GAPS2 G16)`. Each commit's body opens with its gap's saved failure text (Q24; S01 TR-01.9);
the failing tests land in that commit, never alone.

## Risk: [red] — one parser rewrite that every axis option in both modes passes through, a dash.ado normalisation step that runs on every graph, and a derived hover column on every source in both twins

**Why.** `_dash_parse_axis_spec` feeds xlabel/ylabel (`_dash_apply_axis_options`), xtick/ytick
(`_dash_apply_tick_option`), xlabel2/ylabel2 (`_dash_finish_secondary_axes`) and date axes
(`_dash_date_axis_spec`); a regression there changes every dashboard with an axis option.
The ado step touches `_dash_option_rules`, whose graph list is validated per segment and per
graph. Section 18 (red) builds on the tick positions this section leaves, and section 12 on
its hover and axis signatures.

**Risk factors.** (1) The a(b)c bound (`TestAxisLabelBounds`) must survive the tokenizer
rewrite in both modes. (2) Stata's `numlist` refuses more than 1,600 elements (nlist.sthlp:85-87)
while dash's bound is 2,000: a list of 1,601-2,000 values is expanded by the renderer, not by
Stata. (3) Two undocumented readings (whitespace inside `a(b)c`, a second consecutive string)
are settled only by the probes of 14-02/14-03. (4) The hover text column is a new internal
column: it must carry the `__dash` prefix Section 07 reserves and must be on every source the
tooltip attaches to, or a tooltip row reads `???`. (5) This section's diff is merged after
S17's and S16's in batch 2: the redraw hook lands inside S17's rewritten `_on_filter_change`
and the `_vlookup` hunk beside S16's rewritten `_apply_colorvar`.

**Mitigation.** The bound tests are run first (14-05 verify); the extract script records
twoway's reading of every ambiguous form before the parser is written, and the truth block
compares dash's page with twoway's SVG for the same commands; the hover column is added by one
module function called wherever a source is built or redrawn, and a both-modes test asserts it
is on every renderer source that carries the variable; the two cross-section hunks are each a
few lines named by symbol, so the merger applies a rejected hunk by hand (rule R2).

## Dependencies

- **Depends on:** Section 02 (`scripts/svg_truth.py`: `svg_texts(path)`,
  `svg_axis_extent(path, axis, tick_values)`; `test/cert_svg.do`: `cert_svg_export, name() file()`,
  `cert_svg_texts, file()`, `cert_svg_has_text, file() text()`; `test/test_gaps2_truth.cscript`,
  the one truth script, registered by S02 as runner block 67). The extract script and the truth
  block read twoway's tick label text through them. Section 07: the `__dash` internal-column
  prefix (the hover text column is `__dash_hover_{var}`) and the Unicode-aware name check
  `_dash_is_stata_name`, which replaced the ASCII regex at 19207 in batch 1.
- **Blocks:** Section 12 (batch 3: it rewrites `_dash_hover_row`/`_dash_build_hover` on this
  section's stage-one signatures, adds `fmt_cache` to `_dash_apply_axis_spec` and reads the
  `e3_tm_axis_lab` probe); Section 18 (its hull step reads the tick positions this section's
  parser produces, and its `norescale` sub-option rides the same honoured tuple); Section 19.
- **Parallel batch:** 2. **Can run with:** 04, 05, 13, 16, 17. Merge order inside batch 2 is
  S04, S05, S13, S17, S16, S14 (index.md): this section merges LAST. S17's `_on_filter_change`
  rewrite is on the merged tree before this section's diff, so TR-14.14's redraw hook is a
  three-line insertion into S17's text; S16's rewrite of `_apply_colorvar` 6459-6498 is on the
  tree too, so TR-14.6's `_vlookup` hunk (the six-line lookup at 6399-6405) is applied beside
  it. S12 (batch 3) then edits `_dash_hover_row`, `_dash_build_hover`, `_dash_apply_axis_spec`,
  `_dash_csv_meta`, `_dash_facet_label` and `_build_filter_widgets` on the signatures this
  section leaves (TR-14.5, TR-14.10).

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
  (`_textbox_lines` measured it for titles) — **PROBE** (14-02 registers it; 14-03 records it).
- Whitespace inside `a(b)c` and which rc a bad step (`1(0)5`) raises are undocumented —
  **PROBE**.
- `valuelabel` (minimum `val`): "values should be mapped through the first y variable's value
  label (y*() options) or the x variable's value label (x*() options)"; `xlabel(1 2 3,
  valuelabel)` "would have the same effect as `xlabel(1 "Low" 2 "Med" 3 "Hi")`" (:269-291).
  twoway uses no value label unless told (`test_help_claims_2.cscript` HC2-41 pins it).
- Repeated options: "the rightmost of each is honored"; `add` merges (:1029-1035). The Mata
  merge (`_dash_rep_merge`, dash_parse.mata:4826-4855) joins bodies before the graph-level
  validation at 4705 sees them, so the expansion runs on the merged text.
- A `%tm` axis: twoway labels the ticks in the variable's format (`2001m1`); dash today reads
  `Jan 2000`-style text from a `DatetimeTickFormatter` (GAPS2 E3, section 12's gap). The
  drawn truth is a probe of this section's script because the SVG helper is here.

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
f"__mlabel__{mlabel_var}"` at 91d97be, `__dash_mlabel_{var}` after Section 07 (batch 1),
written once per source when absent, rendered through `_mlabel_value_text`. The hover column is
`__dash_hover_{var}` from the start.

`_dash_build_hover(fig, xvar, y1var, y2var, hover_extra, var_labels, date_vars,
numeric_formats, univar, layers)` (19839-19990) has no value-label parameter; rows come from
`_dash_hover_row(col, label, date_kind, numeric_fmt)` (19795-19808), which returns
`(label, "@{col}{fmt}")`; `_fields_for` (19917-19951) keeps a name only if some renderer's
source carries it and it passes the name check -- `_dash_is_stata_name` after Section 07
(batch 1; it replaced the ASCII regex at 19207), which `__dash_hover_foreign`, an identifier
of 20 characters, passes. Callers: 22348-22359 saved, template 26451-26463 served.

Derived columns survive moves in both modes: the saved page snapshots each source after the
figures are built (`_snapshot_of[id(_gsrc)]`, 23697; handed to the callback at 23785-23787) and
`_FILTER_JS` rebuilds each source from its own snapshot's columns; served,
`_dash_refresh_unlinked` (18166) reads "a column the layer derived … from the snapshot at the
row's own position". A served **redraw** of a computed layer (`agg['redraw'](agg_fdf)`,
template ~26919; inside `_on_filter_change`, which S17 rewrites in this batch before this
section merges) rebuilds its source from the frame, which has no derived column: the hover
column must be re-added there (TR-14.14).

### Fixtures on disk

`test/fixtures/axis_truth.json` (`scripts/extract_axis_truth.do`) holds label probes `a_list`,
`a_pairs` (`xlabel(2000 "low" 4000 "high")`: `x_axis.tick_labels == ["low", "high"]`,
`tick_px == [954.11, 3954.99]`, `mapping: None` because no label parses as a number),
`a_incr`, `a_incr_inside`, `a_hash*`. No probe holds a multi-line, compound, `to`, `:`, `/`,
`[ ]`, rule-plus-list, `valuelabel` or `%tm`-axis case. The probe registration is `zp id group
dataset body opts` (106-119); the script sets its own directories (`global ZA_REPO` at :85,
`ZA_OUT`/`ZA_WORK`/`ZA_REC` at :86-91); the trailing `python:` block (452-1450) parses each SVG
with its private `axis_facts` (627-810) and writes the fixture; every regex there spells a
backtick `\x60`. The fixture's `_meta` already holds `scheme_in_force` (read by
`test_axis_options.py:637`), `stata_version`, `stata_born_date`, `run_date` and the method
sentences; every existing key stays.

### Tests that pin today's behaviour (flip, never delete)

- `test/test_graph_options.py::TestParseAxisLabelOpt::test_single_quoted_label` (436-441)
  pins `'One'` as a label. Flip: ticks `[1.0, 2.0]`, labels `{}`.
- `test/test_suboption_warnings.py` SUBOPTIONS entry `("xlabel valuelabel", {"xlabel": ",
  valuelabel"}, None, "xlabel", ["valuelabel"], [])` (58-59) pins the note. Flip: move the
  case to `TestTheHonouredOnesStayQuiet`.
- `test/test_mode_parity.py` `_MUST_WARN` entry `"xlabel with an unimplemented sub-option"`
  (1459-1461, case at 1168-1169 `{"xlabel": "#5, valuelabel", "ytitle": "Miles,
  orientation(vertical)"}`). Flip: the case becomes `{"xlabel": "#5, labcolor(red)", …}` and
  the expected message names `labcolor(red)`; the key is kept (`test_mode_parity.py:1608-1611`
  requires every key to name a corpus case) and this section is the one whose gap silences
  the entry (rule R6 as index.md states it after the review); `valuelabel` may no longer
  appear in `_MUST_WARN`.
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
- **US-14.8** As the maintainer, I want twoway's tick text on a `%tm` axis recorded once, so
  that section 12 can hold dash's date-axis formatter to it.

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
  axis's default ticks and says so once, in both modes; it is never refused in Stata. A list of
  1,601 to 2,000 values, which Stata's `numlist` refuses, is drawn by the renderer.
- **BR-14.7** `xlabel2()`, `ylabel2()`, `xtick()`, `ytick()` and a date axis read the same
  grammar.
- **BR-14.8** `valuelabel` (minimum `val`) labels each tick that is a labelled whole-number
  code with its label, through the first y variable's set for y options and the x variable's
  for x options, on every panel of a by() graph; an unlabelled tick keeps its number; explicit
  `"text"` wins for its value (as measured); without `valuelabel` nothing changes.
- **BR-14.9** A `hover()` variable with value labels shows the label text in the tooltip, in
  both modes, before and after any filter move; a variable without labels shows its number as
  before.
- **BR-14.10** Once drawn, none of these prints a note (DISCOVERY Q22); a bare word that is
  neither a value, a form, a rule nor a label is still named.
- **BR-14.11** Hostile label text (markup, a JS template, a line separator, a run holding a
  backtick, `$` or `'`) is carried as data and never reaches code, `numlist`'s command line or
  unescaped HTML.

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
  `valuelabel` by prefix in the G16 task 14-12 (not before, so the B1 commit leaves the note
  and its pins as they are): any name of three or more letters that `"valuelabel"` starts with
  sets `out["valuelabel"] = True`. (Section 18 adds `norescale` to the same tuple.)
- **TR-14.5** `_dash_apply_axis_spec(axis_obj, grid_obj, spec, values=None, fmt_fallback="",
  grid_color=None, value_labels=None)` after this section; the merged form after batch 3 is
  `_dash_apply_axis_spec(axis_obj, grid_obj, spec, values=None, fmt_fallback="",
  grid_color=None, value_labels=None, fmt_cache=None)`: section 12 appends `fmt_cache=None`
  and edits only the `format()` branch, section 18 adds the `norescale`/hull hooks (both batch
  3, disjoint hunks; S18 merges before S12). This section: in mode `"count"` with
  `spec["ticks"]`, set `ax._dash_extra_ticks = list(spec["ticks"])` on each axis and the
  overrides for `spec["labels"]`; `_dash_place_count_ticks` (17276-17331) unions
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
  'value_labels.get(labelset' dash_render.py` is 1 afterwards. Section 16 rewrites the
  neighbouring lines 6459-6498 of `_apply_colorvar` and section 17 its string path (6527) in
  this batch, both merged before this section: the hunk here is the six-line lookup only.
- **TR-14.7** `_dash_apply_axis_options(fig, graph_opts, xvar, yvar, frame, numeric_formats,
  seen=None, key="", grid_color=None, value_labels=None, value_label_names=None)`: per axis,
  `_dash_value_labels_for(var, …)` with `var` = `xvar` for x options and `yvar` (the first y
  variable the caller passes) for y options, passed to `_dash_apply_axis_spec`. Call sites:
  22115 (saved: `self.value_labels`, `self.value_label_names`) and template 26266 (served:
  `val_labels`, `val_label_names`); under by() every panel's call passes the same dicts, so
  each panel's axis carries the overrides (F-21). Section 12 later appends `fmt_cache=None`
  after these two keywords.
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
- **TR-14.10** Hover signatures, stage one (this section): `text_col=None` is appended to
  today's `_dash_hover_row(col, label, date_kind="", numeric_fmt="")` — with `text_col` the
  field is `@{text_col}` with no format, tested first and never formatted; `layers=None,
  value_labels=None, value_label_names=None` are appended to `_dash_build_hover(fig, xvar,
  y1var, y2var, hover_extra, var_labels, date_vars, numeric_formats, univar, layers)` (`layers`
  becomes a keyword). Before `_fields_for`, for each name in `hover_extra` whose
  `_dash_value_labels_for` is non-empty and which is not a date variable, `_dash_add_hover_text`
  is called on every renderer source in `_rends` that carries it, and `text_cols[name] =
  column` is recorded; `_fields_for` keeps its presence check and its `_dash_is_stata_name`
  check on the variable name and adds the text column's name to the columns a renderer must
  carry to get the full tooltip. Call sites 22348-22359 and template 26451-26463 pass the two
  dicts by keyword. Stage two (section 12, batch 3): `date_kind`/`numeric_fmt` become `fmt="",
  kind="", storage="", cache=None` (keeping `text_col=None` last) and `formats=None,
  storage_types=None, fmt_cache=None` are appended to `_dash_build_hover`. Final forms:
  `_dash_hover_row(col, label, fmt="", kind="", storage="", cache=None, text_col=None)` and
  `_dash_build_hover(fig, xvar, y1var, y2var, hover_extra, var_labels, date_vars,
  numeric_formats, univar, layers=None, value_labels=None, value_label_names=None,
  formats=None, storage_types=None, fmt_cache=None)`.
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
  tokens (commas inside a run become blanks). A run holding a backtick, `$` or `'` is left as
  written without calling `numlist` (the renderer names or bounds it; nothing is ever
  expanded, F-17); every other run (it holds no double quote by construction) is passed as
  `` numlist `"`macval(run)'"' `` and replaced by `r(numlist)` when `_rc == 0`; the pieces and
  the tail are reassembled with single blanks and the tail's comma. Runs that `numlist` refuses
  are left as written (the renderer names or bounds them). It runs on the merged text, after
  `_dash_rep_merge`.
- **TR-14.13** Refusals follow the measured rc: where probe `a1_bad_step` (`xlabel(1(0)5)`)
  and `a1_bad_word` show twoway refusing, `_dash_axis_expand` refuses with the same rc and
  wording (r(198)/r(121) as measured, echoed through `_dash_say`); where twoway draws, dash
  leaves the run as written. `numlist`'s own element cap (r(123), 1,600 elements) is always
  "left as written": the renderer's bound (`_MAX_AXIS_TICKS`, 2,000) decides, so `xlabel(1/1800)`
  registers untouched and draws 1,800 ticks while `xlabel(0/2100)` keeps the default ticks with
  one note.
- **TR-14.14** Served redraw: in the template's `_on_filter_change` (as section 17 rewrote it
  in this batch) step 3, after `_live.data = _dash_keep_jitter(...)`, for each `(var, vlabels)`
  in a build-time dict `_hover_label_vars` (the `hover()` variables with labels, computed once
  beside 26451) call `_dash_add_hover_text(_live, var, vlabels)` — a three-line insertion into
  S17's text.
- **TR-14.15** Copy lists: the function tuple (24466-24687) gains, immediately after
  `"_dash_apply_axis_spec"` (24580), `_dash_expand_numlist`, `_dash_axis_tokens`,
  `_dash_axis_head_split`, `_dash_value_labels_for`, `_dash_hover_text_column`,
  `_dash_add_hover_text`; no new constant. `test/function_test_map.py` gains an entry per new
  function in alphabetical place (no nested `def` inside them, so no `<locals>` entries);
  `test/program_coverage_map.py` gains `_dash_axis_expand` and `_dash_axis_pieces` citing
  `test_gaps2_truth.cscript:AL-01` and `:AL-02`.
- **TR-14.16** Security: label and value-label text travels as data — overrides and the
  formatter's `args` (canvas), the hover column (a tooltip field value BokehJS escapes; never
  `{safe}`); no user text reaches `code`, an f-string of JS, or `exec`. The ado side builds no
  command line from the text except `` numlist `"`macval(run)'"' `` on a run that holds no
  double quote, backtick, `$` or `'`.
- **TR-14.17** Certification: AL-01..AL-19 are a block `* ==== S14 B1 G16: axis labels ====`
  of `test/test_gaps2_truth.cscript` (D11; the script S02 created and registered as runner
  block 67 with the hygiene pins set once), appended above its closing line `* ==== append new
  blocks above this line ====` in section order (rule R1 governs the block order) and guarded by
  `local only : env GAPS2_ONLY` so it runs alone under `GAPS2_ONLY=S14`: 14-08 adds AL-01..AL-16
  (B1), 14-14 adds AL-17..AL-19 (G16) inside the same block. SR-02's flip stays in
  `test/test_suboption_reporting.cscript`. No new `.cscript`, no edit to
  `test/run_all_cscripts.do` or `test/test_cscript_hygiene.py`.
- **TR-14.18** Fixture provenance (D12): at 14-03's regeneration the python block writes into
  `_meta`, beside every existing key, `stata_version` (`c(stata_version)`), `born_date`
  (`c(born_date)`), `dash_commit` and `extracted` (`c(current_date)`); the do-file stores the
  first, second and fourth in locals, captures `git rev-parse HEAD` with `shell cd "${ZA_REPO}"
  && git rev-parse HEAD > "`gitrev'"` into a `tempfile` and reads it into `local dash_commit`;
  the block reads the four through `sfi.Macro.getLocal` (never `shell=True`, never a Stata
  call). `TestAgainstTwoway::test_meta_carries_the_stata_build` asserts the four keys exist
  and compares nothing. Section 18 regenerates the fixture again in batch 3 (rule R5).

## Boundaries

- No change to the formatter map's keys (`str(float)`), to `_dash_date_axis_spec`, to
  `_dash_apply_tick_option`'s CustomJSTicker mechanism, to `_dash_count_ticker`/`_dash_count_of`,
  or to the `#N` placement rule (`_dash_axis_count_ticks`).
- Widening the axis to label/tick values, `norescale`, and every `range()` change are
  **Section 18**; this section only leaves the positions where 18 reads them (the FixedTicker
  ticks, `ax._dash_extra_ticks`, the CustomJSTicker `extra`).
- Textbox sub-option abbreviations, `axis(#)` routing, `xtitle("")` are **Section 13**.
- The `__dash` refusal, the `__dash_mlabel_*` renaming and `_dash_is_stata_name` are
  **Section 07** (batch 1, on the tree); this section only uses the prefix and the check.
- Formatting the `%tm` axis text in dash (`CustomJSTickFormatter`, `_dash_date_axis_formatter`)
  is **Section 12**; this section only records twoway's text for it.
- `_dash_json_value`'s coercion of numeric-looking strings in snapshots is **Section 17** (X1),
  merged before this section in batch 2; this section's worktree starts from the batch-1 tree,
  so its hover tests use non-numeric labels (Poor…Excellent, Domestic/Foreign) and never a
  label spelled like a number.
- `xmtick`, `ymtick`, `xmlabel`, `ymlabel` stay in `_dash_pending` (B10, out of scope): their
  text is normalised, not drawn.
- x and y variables in the tooltip keep their numbers: only `hover()` variables get the label
  column (twoway has no tooltip; `list`/`browse` show labels for the variables the user asks
  for). The colour key, facet titles, CSV and dropdowns already show labels and are untouched.
- `ylabel(, format())` on a value-labelled tick: the override wins, as Bokeh draws it; not
  probed.
- No new Bokeh model, no JS change, no change to `_FILTER_JS` (the snapshot carries the
  column); no new `.cscript`, no runner or hygiene-pin edit (D11).

## Stata truth

Extend `scripts/extract_axis_truth.do`. The probe registration gains two optional arguments:
`zp id group dataset body opts ticks hull` — `ticks` the positions the option asks for, ascending
(for the SVG fit when labels are text); `hull` is Section 18's. The record line gains both. Two
dataset names are handled in the loop: `auto_vl` as `sysuse auto, clear` followed by `label
define alrep 1 "Poor" 2 "Fair" 3 "Average" 4 "Good" 5 "Excellent"` and `label values rep78
alrep`; `sp500_tm` as `sysuse sp500, clear`, `generate m = mofd(date)`, `format m %tm` (sp500
covers 2001, so `m` runs 492..503). The trailing `python:` block imports `svg_texts` and
`svg_axis_extent` from `scripts/svg_truth.py` (`sys.path.insert(0, os.path.join(REPO,
"scripts"))`) for the new groups only — the private `parse_svg`/`axis_facts` reader stays for
the existing groups (section 18 rewires the whole script onto `svg_truth` when it regenerates
in batch 3) — and, for every probe in groups `b1_label` and `g16_valuelabel`, records `texts`
(`[t["text"] for t in svg_texts(svg)]`: the normalised text of every `<text>` element, U+00A0
to a space, in document order) and, when `ticks` is given, `x_axis.mapping` from
`svg_axis_extent(svg, "x", ticks)` (Section 02's `low`/`high`/`space`/`reversed`, stored under
the fixture's `axis_low`/`axis_high` names) instead of the label-parsing fit — `tick_values`
needs one entry per tick pixel in axis order or the reader raises `ValueError`; catch it and
`None`, record the reason under `unverified`, and keep the tick pixel positions. The block
never calls Stata, writes any backtick as `\x60`, and stamps `_meta` as TR-14.18 says while
keeping every existing key.

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
| `e3_tm_axis` | none (`sp500_tm`, body `twoway line close m`) | — | the default tick texts of a `%tm` axis (the control for the next row) |
| `e3_tm_axis_lab` | `xlabel(492(3)501, format(%tm))` (`sp500_tm`, body `twoway line close m`) | 492 495 498 501 | the texts `2001m1 2001m4 2001m7 2001m10` |

Group `g16_valuelabel`, dataset `auto_vl`:

| id | command | records |
|---|---|---|
| `g16_vl_slash` | `twoway scatter mpg rep78, xlabel(1/5, valuelabel)` | Poor … Excellent |
| `g16_vl_abbrev` | `…, xlabel(1/5, val)` | the same |
| `g16_vl_unlabelled` | `…, xlabel(0/6, valuelabel)` | "0" and "6" as numbers |
| `g16_vl_mixed` | `…, xlabel(1 "one" 2/5, valuelabel)` | which text is drawn at 1 |
| `g16_vl_default` | `…, xlabel(, valuelabel)` | what the default ticks show |
| `g16_vl_y` | `twoway scatter rep78 mpg, ylabel(1/5, valuelabel)` | the y labels |
| `g16_vl_by` | `twoway scatter mpg rep78, by(foreign) xlabel(1/5, valuelabel)` | every panel's texts (F-21) |
| `g16_vl_off` | `twoway scatter mpg rep78, xlabel(1/5)` | numbers (control) |

The script sets its own directories (`global ZA_REPO` at :85), so it is run directly through the
slot wrapper (D6, index.md step 0; it implements CLAUDE.md rule 10's console invocation under
one of three slots and sets `STATATMP=/tmp/dash-s14/tmp/` with the trailing slash), never the
GUI, once, by 14-03:

```
scripts/stata_slot.sh /tmp/dash-s14 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_axis_truth.do
```

Read `/tmp/dash-s14/extract_axis_truth.log` for `probe <id> rc=` lines. Section 18 runs the
same script in batch 3, after this section has merged, and regenerates the fixture last (rule
R5): its run re-records this section's groups unchanged (checked probe by probe) and rewires
the script onto `svg_truth` for every group, removing the private reader; no coordination
inside batch 2 is needed. The fixture is `*.json` and hidden by
`.git/info/exclude`: `git add -f test/fixtures/axis_truth.json`. `test_fixtures_are_committed.py`
requires a test to name it — `test_axis_options.py` already does, and the new tests read it too.
The regeneration is verified probe by probe: every one of the 233 pre-existing probes' records
outside `_meta` are unchanged (a python one-liner compares the old and new JSON per id), never
by a diff's line count.

A cscript (`test_gaps2_truth.cscript`, `test_suboption_reporting.cscript`) resolves
`cert_helpers.do`, `cert_svg.do` and `adodir ".."` from `test/`, as `test/run_all_cscripts.do`
does with its `cd`, so it is run through a two-line driver written into the scratch directory:

```
mkdir -p /tmp/dash-s14
printf 'cd "%s/test"\ndo "%s/test/%s"\n' /Users/billy/Desktop/Programs/StataPrograms/d/dash /Users/billy/Desktop/Programs/StataPrograms/d/dash test_gaps2_truth.cscript > /tmp/dash-s14/run_test_gaps2_truth.do
GAPS2_ONLY=S14 scripts/stata_slot.sh /tmp/dash-s14 /tmp/dash-s14/run_test_gaps2_truth.do
```

(the same two lines with `test_suboption_reporting.cscript` and no `GAPS2_ONLY` for the other
script). The logs are `/tmp/dash-s14/run_<script>.log`; `GAPS2_ONLY=S14` makes the truth
script run only this section's block. Both scripts exit 222 themselves when `c(python_exec)` is
empty; a SKIP is not a pass.

## TDD test stubs

All B1 stubs in **`test/test_axis_label_grammar.py`** (new, 14-01), all G16 stubs in
**`test/test_value_labels_drawn.py`** (new, 14-10). Both-mode helper `_figures(mode, tmp_path, df,
plots, go, formats=None, value_labels=None, label_names=None)` modelled on
`test_natscale_axes._figures` (312-339) with `make_data_json(df, value_labels, label_names)`,
written once in `test_axis_label_grammar.py` and imported by the G16 file. Each gap's stubs
fail on the tree before that gap's fix and their failure text is saved by the gap's first task
(Q24).

B1 (14-01):

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
- Test: `TestTheBound::test_between_numlists_cap_and_the_bound_the_renderer_expands` —
  `xlabel(1/1800)` (above Stata's 1,600-element cap, below the 2,000 bound): 1,800 ticks, no
  note, both modes; `xlabel(0/2100)`: the default ticks with one note.
- Test: `TestTheExpander::test_forms`, `::test_a_zero_step_is_bad`, `::test_to_needs_two_values`,
  `::test_the_count_is_taken_before_any_value_is_made`, `::test_non_finite_endpoints_do_not_raise`
  — unit tests of `_dash_expand_numlist`. Pre-fix: `AttributeError`.
- Test: `TestTheTokenizer::test_compound_quotes_nest`, `::test_an_unclosed_string_runs_to_the_end`,
  `::test_a_comma_inside_a_string_is_text`, `::test_the_head_split_is_quote_aware` — unit tests
  of `_dash_axis_tokens` and `_dash_axis_head_split`.
- Test: `TestAgainstTwoway::test_every_b1_probe_draws_the_texts_twoway_drew` — for each
  `b1_label` probe with rc 0 in `axis_truth.json` other than the two `e3_` probes, dash's
  override values (in tick order) equal the probe's non-numeric tick texts, and its FixedTicker
  equals the probe's `ticks`; the test fails, not skips, when the fixture lacks the group
  ("task 14-03 must land first").
- Test: `TestAgainstTwoway::test_the_tm_axis_probe_is_recorded` — `e3_tm_axis_lab` exists in
  group `b1_label` with `ticks` `[492, 495, 498, 501]` and its `texts` minus `e3_tm_axis.texts`
  are `2001m1`, `2001m4`, `2001m7`, `2001m10` (the section 12 contract); fails, never skips,
  when absent.
- Test: `TestAgainstTwoway::test_meta_carries_the_stata_build` — `axis_truth.json`'s `_meta`
  holds `stata_version`, `born_date`, `dash_commit`, `extracted` and still `scheme_in_force`
  (nothing compared, D12).
- Test: `TestHostileLabels::test_label_text_stays_data_in_both_modes` — `1 "</script><script>
  alert(1)</script>" 2 "x y"`: the code is the fixed parser, the labels are in `args` and
  overrides whole, the page has no `<script>alert(1)`.
- Flip: `test_graph_options.py::TestParseAxisLabelOpt::test_single_quoted_label`.

G16 (14-10):

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
- Test: `TestValueLabelsOnAxes::test_by_panels_each_carry_the_overrides` — `by(foreign)` with
  `xlabel(1/5, valuelabel)`: every panel's x axis has the five overrides in both modes (F-21;
  per `g16_vl_by`).
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
- Test: `TestHoverShowsValueLabels::test_the_row_helper_takes_text_col_last` —
  `_dash_hover_row("foreign", "Foreign", text_col="__dash_hover_foreign")` gives
  `("Foreign", "@{__dash_hover_foreign}")` and `_dash_build_hover` accepts `layers=`,
  `value_labels=`, `value_label_names=` by keyword (the stage-one signatures section 12
  extends).
- Test: `TestAgainstTwoway::test_every_g16_probe_draws_the_texts_twoway_drew`.
- Flips: `test_suboption_warnings.py` "xlabel valuelabel" entry; `test_mode_parity.py`
  `_MUST_WARN` "xlabel with an unimplemented sub-option" and its case; SR-02 in
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
| pass a run holding `$x` to `numlist` | AL-02 (`xlabel(2000 $x 4000)` registers with the run untouched) |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| each numlist form, labelled pairs, lines, compound quotes, single quotes, rule+list | pytest `test_axis_label_grammar.py` | `axis_truth.json` (`b1_label`) | yes |
| the bound in every form; the 1,600/2,000 gap | pytest `TestTheBound`, `test_adversarial_matrix.py::TestAxisLabelBounds` | — | yes |
| expander and tokenizer units | pytest | — | n/a |
| ado expansion (`numlist` reached, tail kept, merged text, hostile run untouched) | truth block AL-01..AL-04 (spec JSON read with `cert_file_has`) | — | n/a |
| twoway's ticks and texts vs dash's page | truth block AL-05..AL-16 (`cert_svg_export` + `cert_svg_texts`; page needles) | — | saved page |
| twoway's `%tm` tick text recorded for section 12 | pytest `TestAgainstTwoway::test_the_tm_axis_probe_is_recorded` | `axis_truth.json` (`e3_tm_axis_lab`) | n/a |
| fixture `_meta` stamp | pytest `TestAgainstTwoway::test_meta_carries_the_stata_build` | `axis_truth.json` | n/a |
| `valuelabel`, `val`, unlabelled code, y, second axis, by() panels | pytest `test_value_labels_drawn.py` | `axis_truth.json` (`g16_valuelabel`) | yes |
| `hover()` label column, snapshot, served redraw, hostile label | pytest | — | yes |
| twoway's valuelabel texts vs dash's | truth block AL-17..AL-19 | — | saved page |
| the note is gone | pytest `test_suboption_warnings.py`, cscript SR-02 (flipped) | — | yes |
| copy lists, function map | `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_function_test_map.py`, `test_program_coverage_map.py` | — | served |

Acceptance criteria:

- **AC-14.1** `xlabel(1 "2019" 2 "2020" 3 "2021")` draws ticks 1, 2, 3 labelled 2019, 2020,
  2021 in both modes, with no note; the truth block finds the same three texts in twoway's SVG
  and dash's page.
- **AC-14.2** Every form in `TestNumlistForms` draws Stata's values in both modes; `1(2)10`
  draws 1, 3, 5, 7, 9; the ado spec for `xlabel(1/5)` carries `1 2 3 4 5`.
- **AC-14.3** A second string is a second line and a compound string keeps its inner quotes,
  as the `a1_twolines`/`a1_compound` probes record.
- **AC-14.4** `#5 50 "fifty"` draws the five count ticks and 50 labelled "fifty".
- **AC-14.5** `0(0.000001)1000000` and its `/`, `to`, `[ ]` twins keep the default ticks with
  one note, under 2 s, in both modes; dash.ado does not refuse them; `1/1800` draws 1,800 ticks.
- **AC-14.6** `xlabel(1/5, valuelabel)` draws Poor…Excellent in both modes, on every by()
  panel, and prints nothing; `val` works; an unlabelled code keeps its number; y maps through
  the first y variable.
- **AC-14.7** `hover(foreign)` shows Domestic/Foreign in both modes, on every source the
  tooltip attaches to, before and after a filter move.
- **AC-14.8** `grep -c 'value_labels.get(labelset' dash_render.py` is 1; every new function is
  in the copy list after `"_dash_apply_axis_spec"` and in `function_test_map.py`; the full pytest
  suite passes before each commit; the S14 block, SR-02 and the other scripts this section
  touches pass with no skip.
- **AC-14.9** `axis_truth.json` carries `e3_tm_axis_lab` with the four `2001m…` texts and the
  `_meta` stamp, with every pre-existing probe unchanged.
- **AC-14.10** BUGS.md carries closed B1 and G16 entries in the D3 form naming their tests;
  dash.sthlp 672-680 and 2318-2331 are updated; the `<!-- WP-28 B1 -->` and `<!-- WP-28 G16 -->`
  markers in the `**WP-28 (GAPS2 audit, 25sep2026)**` group of `### Results that change` are
  replaced by lines ending `(WP-28, B1)` and `(WP-28, G16)`.

## Tasks

Commit boundary: **two commits** -- **B1** = 14-01..14-09 (subject ending `(GAPS2 B1)`; the
fixture of 14-03, with its `e3_` and `g16_` probes, lands here with a `Fixture:` line) and
**G16** = 14-10..14-15 (`(GAPS2 G16)`). Each closing task runs the full pytest suite once in
the worktree before its commit (CLAUDE.md rules 4 and 11), commits on the worktree branch
`wp28-s14`, and the merger lands the two commits on `s3-bugs` in order with the same messages
(index.md step 1). Each body opens with its gap's saved failure text (Q24) and carries S01
TR-01.9's `Regression:` / `Flipped:` / `Fixture:` / `BUGS.md:` lines. Every Stata run goes
through `scripts/stata_slot.sh` (D6): the extract script directly, a cscript through the driver
of "Stata truth". No AI references anywhere.

<task type="auto" id="14-01">
  <name>Write the failing B1 tests</name>
  <files>test/test_axis_label_grammar.py</files>
  <action><![CDATA[
    Create `test/test_axis_label_grammar.py`. Its module docstring states the B1 defects in CHANGELOG terms: `xlabel(1 "2019" 2 "2020" 3 "2021")` drew six unlabelled ticks; `10 20 to 40` drew 10, 20, 40 with `to` as a label; `1/5` and `1[1]3` drew the default ticks; `#5 50 "fifty"` lost the `#5`. Copy the header block of `test/test_natscale_axes.py` (imports, `_HERE`, the `sys.path` inserts, `_MODES`, `_SEQ`) and its `_figures` helper, adding `value_labels`/`label_names` arguments passed to `make_data_json` (the G16 file imports these); add a rep78-like frame builder `_rep_frame()` with codes 0-6 and the label set Poor…Excellent under set name `alrep` keyed by `{"rep78": "alrep"}`; and a `truth()` module fixture that `pytest.fail`s (never skips) when `test/fixtures/axis_truth.json` lacks the `b1_label` group or the `e3_tm_axis_lab` probe ("task 14-03 must land first"). Write every B1 stub of "TDD test stubs" with exactly those names, including the mutation-sensitive assertions. Do not touch `dash_render.py` or `dash.ado`. Run the file against the unmodified tree. Do not commit: save the failure summary to `<scratch>/14-01-failure.txt`; it opens the B1 commit's body and its values are the CHANGELOG's old ticks (Q24, S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_axis_label_grammar.py -q 2>&1 | tail -5` shows 0 passed, no collection error; `python3 -m pytest test/test_axis_label_grammar.py -q -k value_text_pairs 2>&1 | grep -c "2019.0"` is non-zero (the headline fails on the wrong tick list, not on an exception); `<scratch>/14-01-failure.txt` exists.]]></verify>
  <done>The B1 test file existed, collected cleanly, and every test in it failed at 91d97be for the reason its stub names, with nothing committed.</done>
</task>

<task type="auto" id="14-02">
  <name>Register the B1 and G16 probes</name>
  <files>scripts/extract_axis_truth.do</files>
  <action><![CDATA[
    In `scripts/extract_axis_truth.do`: extend `zp` (106-119) with optional `ticks` (arg 6) and `hull` (arg 7) globals and write both into the PROBE record line (after `shown`); add the `auto_vl` dataset branch in the export loop (`if "`ds'" == "auto_vl" { sysuse auto, clear ... label define alrep ... label values rep78 alrep }`, and reset the `curds` logic accordingly); register every probe of the "Stata truth" tables in groups `b1_label` (the `a1_` rows; the two `e3_` rows are 14-03's) and `g16_valuelabel`, compound-quoted where the option holds quotes (`zp "a1_compound" ... `"xlabel(2000 `"c "q" d"' 4000 "high")"'` — check the nesting by echoing each `shown` line in the log later). In the `python:` block: `sys.path.insert(0, os.path.join(REPO, "scripts"))`, `from svg_truth import svg_texts, svg_axis_extent` (the private reader stays for the existing groups); parse the two new record fields; for probes in the two new groups write `texts` (from `svg_texts`, U+00A0 normalised) and, when `ticks` is non-empty, replace `x_axis["mapping"]` (or `y_axis`) with `svg_axis_extent(svg, axis, ticks)`; keep `rc` and the log's error line for the `a1_bad_*`, `a1_single_quote`, `a1_str_first`, `a1_spaces_incr` probes in a new `findings.label_refusals` map; add the `_meta` stamp of TR-14.18 (the locals and the `tempfile`/`shell` capture in the do-file, `Macro.getLocal` in the block) beside every existing `_meta` key. No backtick literal in the block (`\x60`); the block calls no Stata. Do not run the script here: 14-03 registers the `%tm` probes and makes the section's one run.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && grep -c '^zp "a1_' scripts/extract_axis_truth.do` prints 23 and `grep -c '^zp "g16_' scripts/extract_axis_truth.do` prints 8; `grep -c 'auto_vl\|label_refusals\|dash_commit\|from svg_truth import' scripts/extract_axis_truth.do` is at least 4; `python3 -c "t=open('scripts/extract_axis_truth.do').read(); b=t[t.index('python:'):]; assert '\x60' not in b; compile(b[b.index('\n')+1:b.rindex('\nend')], 'block', 'exec')"` prints nothing (the block compiles and holds no backtick).]]></verify>
  <done>Every B1 and G16 probe, the `auto_vl` dataset branch, the `svg_truth` reader for the new groups and the `_meta` stamp were registered in the extract script, ready for the section's one run.</done>
</task>

<task type="auto" id="14-03">
  <name>Record twoway's %tm axis-tick text for E3</name>
  <files>scripts/extract_axis_truth.do, test/fixtures/axis_truth.json</files>
  <action><![CDATA[
    In the export loop add a dataset branch `sp500_tm`: `sysuse sp500, clear`, `generate m = mofd(date)`, `format m %tm`. Register `zp "e3_tm_axis" "b1_label" "sp500_tm" "twoway line close m" "" ""` and `zp "e3_tm_axis_lab" "b1_label" "sp500_tm" "twoway line close m" "xlabel(492(3)501, format(%tm))" "492 495 498 501"` after the `a1_` rows (sp500 covers 2001, so the expected texts are `2001m1 2001m4 2001m7 2001m10`). The python block records `texts` for both as for every `b1_label` probe. Run the script once through the wrapper: `scripts/stata_slot.sh /tmp/dash-s14 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_axis_truth.do` (the section's one regeneration, carrying 14-02's probes; section 18 regenerates again in batch 3, rule R5); read `/tmp/dash-s14/extract_axis_truth.log` for every `probe <id> rc=` line and the echoed `shown` lines of the compound-quoted probes; then `git add -f test/fixtures/axis_truth.json`. Verify the regeneration probe by probe: for each of the 233 pre-existing probe ids, the record in the new file equals the record in `git show HEAD:test/fixtures/axis_truth.json` (a python loop over `probes`, `findings` and `unverified`, `_meta` excluded); a difference is a reader regression to fix, never a fixture to patch.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -c "import json; d=json.load(open('test/fixtures/axis_truth.json')); p=d['probes']; print(p['a1_pairs3']['texts'], p['g16_vl_slash']['texts'], p['e3_tm_axis_lab']['texts'], d['findings']['label_refusals'], sorted(k for k in d['_meta'] if k in ('born_date','dash_commit','extracted','stata_version','scheme_in_force')))"` prints the three year texts, Poor…Excellent, a list holding `2001m1`, `2001m4`, `2001m7` and `2001m10`, the rc map, and the five keys; `python3 -c "import json,subprocess; old=json.loads(subprocess.run(['git','show','HEAD:test/fixtures/axis_truth.json'],capture_output=True,text=True).stdout); new=json.load(open('test/fixtures/axis_truth.json')); bad=[k for k in old['probes'] if old['probes'][k]!=new['probes'][k]]; print(len(old['probes']), bad)"` prints `233 []`; `git ls-files test/fixtures/axis_truth.json` prints the path; `python3 -m pytest test/test_axis_options.py test/test_axis_label_grammar.py -q -k "test_axis_options or Twoway" 2>&1 | tail -2` shows `test_axis_options.py` still green and `TestAgainstTwoway::test_the_tm_axis_probe_is_recorded` and `::test_meta_carries_the_stata_build` passing.]]></verify>
  <done>twoway's %tm tick text, every B1 and G16 reading and the `_meta` stamp became one committed regeneration of `axis_truth.json` that left every pre-existing probe unchanged and that section 12's date-axis test can read.</done>
</task>

<task type="auto" id="14-04">
  <name>Add the numlist expander and tokenizer</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Beside `_MAX_AXIS_TICKS` add `_dash_expand_numlist`, `_dash_axis_tokens` and `_dash_axis_head_split` exactly as TR-14.1/14.2 specify (count before value, `too_many`, `bad`, quote-aware split). Read `a1_spaces_incr`, `a1_single_quote`, `a1_str_first` and `label_refusals` first and cite the probe id in a comment where a rule follows one. Add the three to the served function list immediately after `"_dash_apply_axis_spec"` (24580) and map them in `test/function_test_map.py` to `TestTheExpander::test_forms` and `TestTheTokenizer::test_the_head_split_is_quote_aware`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_label_grammar.py -q -k "Expander or Tokenizer"` passes; `python3 -c "import dash_render as d;print(d._dash_expand_numlist(['1','2','3/5','8(2)12']))"` prints `([1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 10.0, 12.0], False, [])`.]]></verify>
  <done>Stata's numlist forms and the quote-aware tokenizer existed as bounded, mapped, copied functions.</done>
</task>

<task type="auto" id="14-05">
  <name>Rebuild the axis label parsers on them</name>
  <files>dash_render.py, test/test_graph_options.py</files>
  <action><![CDATA[
    Rebuild `_dash_parse_axis_label_opt` on the two helpers (same `(ticks, labels)` contract; a `str` labels the last value; further strings join with `"\n"`; a string before any value goes to `unsupported`). In `_dash_parse_axis_spec` replace the `_m_tail`/`m_sub` regexes and the sub-option-stripping regex with `_dash_axis_head_split`, read a leading rule token, replace the a(b)c block with the expander keeping the `_too_many` warning text, and append `bad` and stray words to `unsupported`; leave `valuelabel` in `unsupported` for now (14-12 honours it, so the B1 commit keeps the note and its pins green). Flip `test_graph_options.py::TestParseAxisLabelOpt::test_single_quoted_label` to ticks `[1.0, 2.0]`, labels `{}`, with a docstring saying Stata's single quote is a character; record the flip as a `Flipped:` line in `<scratch>/14-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_label_grammar.py -q -k "Labelled or Numlist or Bound or Hostile"` passes except `test_a_rule_then_a_labelled_list` (14-06); `python3 -m pytest test/test_axis_options.py test/test_graph_options.py test/test_adversarial_matrix.py -k "Grammar or AxisLabel" -q` passes; `python3 -m pytest test/test_suboption_warnings.py test/test_mode_parity.py -q -k "valuelabel or unimplemented" 2>&1 | tail -2` is still green (the note is untouched until 14-12).]]></verify>
  <done>Every numlist form, quoted string, line and compound quote was read as twoway reads it, bounded as before, with the `valuelabel` note left in place for the G16 commit.</done>
</task>

<task type="auto" id="14-06">
  <name>Carry count-mode lists into the tickers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `_dash_apply_axis_spec` add `value_labels=None`, stash `ax._dash_extra_ticks` and the overrides in mode `"count"`, and add the value-label override merge of TR-14.5 (explicit text wins, or the reverse if `g16_vl_mixed` says so — cite it; the merge is inert until 14-12 passes labels and the parser sets `spec["valuelabel"]`). In `_dash_place_count_ticks` union `_dash_extra_ticks` into the FixedTicker and into `t_lo`/`t_hi`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_label_grammar.py test/test_served_dates.py test/test_help_claims_8.py test/test_natscale.py -q 2>&1 | tail -3` is green including `test_a_rule_then_a_labelled_list`.]]></verify>
  <done>A rule before a labelled list drew both, and count ticks kept the listed values.</done>
</task>

<task type="auto" id="14-07">
  <name>Expand axis numlists in dash.ado</name>
  <files>dash.ado, dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    Implement TR-14.11 to TR-14.13. In `dash_parse.mata`, beside `_dash_rep_toks` (4064), add `_dash_axis_pieces(string scalar s)` returning a string colvector of pieces tagged by a leading character (`R` rule, `S` string, `B` bare run, `T` tail) using the same quote-and-parenthesis walk `_dash_rep_toks` uses; a `B` run holding a backtick, `$` or `'` is tagged `H` (hostile: left as written, never passed to `numlist`). In `dash.ado`, add `_dash_axis_expand` (reads its text by value through `_dash_text_args` as `_dash_validate_value` does at 1957; loops the pieces; for each `B` piece replaces commas by blanks and runs `` capture numlist `"`macval(run)'"' ``, substituting `r(numlist)` on rc 0 and leaving the run as written otherwise, `numlist`'s 1,600-element cap included; on the rc the `label_refusals` finding shows twoway refusing, refuses with the same rc and wording through `_dash_say`; reassembles with the tail's comma). Add kind `axislist` to `_dash_validate_value` (norm from `_dash_axis_expand`, no bounds) and the ten `=axislist` rules to `_dash_option_rules`'s graph list (1910-1912). No library rebuild exists or is needed: dash_parse.mata is `run` from dash.ado. Add both programs to `test/program_coverage_map.py` with references `test_gaps2_truth.cscript:AL-01` and `test_gaps2_truth.cscript:AL-02`.
  ]]></action>
  <verify><![CDATA[Write `/tmp/dash-s14/probe.do` holding `adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash"`, `global dash_nobrowser 1`, `sysuse auto`, `dash scatter mpg weight, xlabel(1/5 "five" 10 20 to 40, grid) name(t1)` and `dash build, saving(t1.html)`, run `scripts/stata_slot.sh /tmp/dash-s14 /tmp/dash-s14/probe.do`, and check `/tmp/dash-s14/probe.log` ends with rc 0 and its spec JSON line carries `"xlabel":"1 2 3 4 5 \"five\" 10 20 30 40, grid"`; `python3 -m pytest test/test_unsupported_report_is_true.py test/test_option_surface.py test/test_program_coverage_map.py -q 2>&1 | tail -2` is green.]]></verify>
  <done>dash.ado wrote Stata's own expansion of every axis numlist into the spec, strings, hostile runs and sub-options untouched, and refused only what twoway refuses.</done>
</task>

<task type="auto" id="14-08">
  <name>Certify the label grammar against twoway</name>
  <files>test/test_gaps2_truth.cscript</files>
  <action><![CDATA[
    Append to `test/test_gaps2_truth.cscript` (S02 created it in batch 1 and registered it as runner block 67; it opens with the Python gate that exits 222, loads `cert_helpers.do` and `cert_svg.do`, sets `global dash_nobrowser 1`, and ends with the line `* ==== append new blocks above this line ====`), above that last line and after every earlier section's block (rule R1: blocks in section order), the block
```
* ==== S14 B1 G16: axis labels ====
local only : env GAPS2_ONLY
if inlist("`only'", "", "S14") {
    display as text "S14 start `c(current_time)'"
    ... AL-01..AL-16 (AL-17..AL-19 are added by 14-14) ...
    display as text "S14 end `c(current_time)'"
}
* ==== end S14 ====
```
    with, inside the `if`, a `*` case index, `sysuse auto, clear`, and the cases, each displaying `AL-nn PASS` or `AL-nn FAIL: <why>` through the script's PASS/FAIL helper and never `exit`ing on a failure: AL-01 `_dash_axis_expand` on `1/5 "five" 10 20 to 40, grid` returns the expanded text; AL-02 `_dash_axis_pieces` splits a compound-quoted label with a comma inside, and `xlabel(2000 $x 4000)` registers with the run untouched (the `H` piece); AL-03 the registry JSON for `xlabel(1(2)10)` carries `1 3 5 7 9` (`cert_file_has ... needle(...)`); AL-04 `xlabel(0(0.000001)1000000)` and `xlabel(1/1800)` register with rc 0 and their runs as written, and the pages build (the 2,000 note is pytest's `TestTheBound`). AL-05..AL-16: for each B1 form in the "Stata truth" table with rc 0, `twoway scatter mpg weight|rep78, xlabel(...)` then `cert_svg_export, file()`, `cert_svg_texts, file()` (`r(n)` texts) and one `cert_svg_has_text, file() text("<label>")` per expected label (`r(found)`), then `dash ..., name(alN)` + `dash build, saving()`, and assert with `cert_file_has` that the page carries each label text and the FixedTicker list (measure the exact JSON spelling of `"ticks":[...]` and the overrides `entries` on AL-05 once and pin it as a `*` note at the top of the block). Edit neither `test/run_all_cscripts.do` nor `test/test_cscript_hygiene.py` (D11: S02 alone set the pins). Run the block with the driver of "Stata truth" under `GAPS2_ONLY=S14` and read `/tmp/dash-s14/run_test_gaps2_truth.log`.
  ]]></action>
  <verify><![CDATA[`grep -c "AL-[01][0-9] PASS" /tmp/dash-s14/run_test_gaps2_truth.log` prints 16, `grep -c " FAIL" /tmp/dash-s14/run_test_gaps2_truth.log` prints 0 and `grep -c '^r([0-9]*);' /tmp/dash-s14/run_test_gaps2_truth.log` prints 0; `python3 -m pytest test/test_cscript_hygiene.py test/test_program_coverage_map.py -q 2>&1 | tail -2` is green.]]></verify>
  <done>The one truth script's S14 block proved, live, that twoway and dash draw the same ticks and texts for every B1 form and that dash.ado's expansion reaches the spec.</done>
</task>

<task type="auto" id="14-09">
  <name>Close B1 in BUGS.md, help and CHANGELOG</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append at the end of BUGS.md (S01 TR-01.8; never mid-file) the closed entry `- [x] Title: Axis-label rules misread quoted numeric text, multi-line labels and numlist forms` with File Names and Line Numbers (`dash_render.py` `_dash_parse_axis_label_opt`, `_dash_parse_axis_spec`, `_dash_apply_axis_spec`; `dash.ado` `_dash_axis_expand`, `_dash_option_rules`; `dash_parse.mata` `_dash_axis_pieces`), Description (GAPS2 B1's measured symptoms and the measured readings of the two undocumented forms), Suggested fix, and `- Resolution: Fixed <ddmonyyyy> (WP-28, B1). Axis label options are tokenised quote-aware (_dash_axis_tokens, _dash_axis_head_split), every numlist form is expanded by Stata's numlist in dash.ado (_dash_axis_expand) and by _dash_expand_numlist in the renderer, strings are label lines, a rule may precede a labelled list, and _MAX_AXIS_TICKS still bounds every form, in both renderers. Pinned by test/test_axis_label_grammar.py::TestLabelledTicks::test_value_text_pairs_draw_three_labelled_ticks, ::TestNumlistForms::test_each_form_draws_statas_values, test/test_gaps2_truth.cscript AL-05; fixture test/fixtures/axis_truth.json.` -- the title holds no `"`. In dash.sthlp 2318-2327 extend the vocabulary table: `a/b`, `a[b]c`, `a b to c`, `a b:c`, value `"text"` pairs, a second string as a second line, compound quotes, a rule before a list, and that dash.ado expands the list with Stata's `numlist` (the 2,000-tick bound stays as documented); grep `test/test_help_claims_*.cscript` and `test/test_help_examples.py` for the changed lines and update any pin. In `CHANGELOG.md` replace the marker `<!-- WP-28 B1 -->` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of the release's `### Results that change` list (S01 placed it there, D2) with ONE line ending `(WP-28, B1)` naming the command, the old ticks and the new (from `<scratch>/14-01-failure.txt`, Q24): `xlabel(1 "2019" 2 "2020" 3 "2021")` was six ticks unlabelled, now three labelled; `10 20 to 40` was 10 20 40, now 10 20 30 40; `1/5` and `1[1]3` were the default ticks; `#5 50 "fifty"` was 50 alone, now both. Write nothing under any other heading. Run the full pytest suite once in the worktree (`python3 -m pytest test/ -q`, the first of this section's two launches), then the S14 block through the driver; grep the three files and the message for `claude|anthropic`; commit 14-01..14-09 on the worktree branch `wp28-s14` as ONE commit, subject ending `(GAPS2 B1)`, body opening with `<scratch>/14-01-failure.txt` and carrying the `Regression:` / `Flipped:` (from `<scratch>/14-flips.txt`) / `Fixture: test/fixtures/axis_truth.json (scripts/extract_axis_truth.do)` / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` with this message (index.md step 1).
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_1.py -q 2>&1 | tail -2` is green; `grep -c '<!-- WP-28 B1 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, B1)' CHANGELOG.md BUGS.md` prints 2; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0 and `git log -1 --format=%s | grep -c '(GAPS2 B1)'` prints 1.]]></verify>
  <done>B1 was closed in BUGS.md naming its tests, documented in dash.sthlp, its CHANGELOG marker replaced by the line with the recorded old ticks, and committed as one green commit on `wp28-s14` carrying the regenerated fixture.</done>
</task>

<task type="auto" id="14-10">
  <name>Write the failing G16 tests</name>
  <files>test/test_value_labels_drawn.py</files>
  <action><![CDATA[
    Create `test/test_value_labels_drawn.py`. Its module docstring states the G16 defects in CHANGELOG terms: `xlabel(1/5, valuelabel)` was named and drew numbers; `hover(foreign)` showed 0/1. Import `_figures`, `_rep_frame`, `_MODES` and `truth` from `test_axis_label_grammar` (14-01) rather than copying them; for the hover tests import `test_mode_parity as tp` and use `tp._spec`, `tp._standalone`, `tp._served`, `tp._DF`, `tp._VALUE_LABELS`, `tp._LABEL_NAMES`; for the served redraw reuse the `_fire` pattern of `test_help_claims_3.py:415-497`. Write every G16 stub of "TDD test stubs" with exactly those names, including `test_by_panels_each_carry_the_overrides` and `test_the_row_helper_takes_text_col_last`; use only non-numeric labels (Poor…Excellent, Domestic/Foreign). Do not touch `dash_render.py`. Run the file against the tree as the B1 commit left it (the G16 code paths are untouched by B1). Do not commit: save the failure summary to `<scratch>/14-10-failure.txt`; it opens the G16 commit's body (Q24, S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_value_labels_drawn.py -q 2>&1 | tail -5` shows 0 passed, no collection error; `python3 -m pytest test/test_value_labels_drawn.py -q -k hover_foreign 2>&1 | grep -c "@{foreign}"` is non-zero (the headline fails on the number row, not on an exception); `<scratch>/14-10-failure.txt` exists.]]></verify>
  <done>The G16 test file existed, collected cleanly, and every test in it failed for the reason its stub names, with nothing committed.</done>
</task>

<task type="auto" id="14-11">
  <name>Replace the five label-set lookups with one</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Implement TR-14.6: add `_dash_value_labels_for(var, value_labels, value_label_names)` at module level immediately before `_dash_attach_labels` (18745); make `GlyphMapper._mlabel_value_labels` a one-line call to it; replace the copies at `_apply_colorvar` (the six-line `_vlookup` lookup, 6399-6405 at 91d97be; sections 16 and 17 rewrote the lines around it in this batch and merge before this section, so the hunk is those six lines only), `_dash_csv_meta` (13909-13912), `_dash_facet_label` (15601-15607) and the saved filter builder (23598-23603) with calls, keeping each site's later type check where it existed. Add the function to the served function list after the three of 14-04 (all after `"_dash_apply_axis_spec"`) and to `test/function_test_map.py` naming `test/test_value_labels_drawn.py::TestTheLookup::test_by_variable_name_as_jsonio_writes_it`.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && grep -c 'value_labels.get(labelset' dash_render.py` prints 1; `python3 -m pytest test/test_value_labels_drawn.py -k TheLookup test/test_marker_label_parity.py test/test_facets.py test/test_csv_download.py -q 2>&1 | tail -3` is green (substitute the facet and CSV test files the function map names for `_dash_facet_label` and `_dash_csv_meta`).]]></verify>
  <done>One module-level lookup served the colour key, marker labels, CSV, facet titles and filters, and the served app carried it.</done>
</task>

<task type="auto" id="14-12">
  <name>Draw valuelabel on axes in both modes</name>
  <files>dash_render.py, test/test_suboption_warnings.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    In `_dash_parse_axis_spec` honour `valuelabel` by prefix (TR-14.4: any name of three or more letters that `"valuelabel"` starts with sets `out["valuelabel"] = True` and leaves `unsupported`). Implement TR-14.7 and TR-14.8: the two new parameters on `_dash_apply_axis_options` and on `_dash_finish_secondary_axes`, the per-axis lookup, and the four call sites (22115, 22307 saved; template 26266, 26399 served — the served ones pass `val_labels`, `val_label_names` and `plots`). Read `g16_vl_mixed`, `g16_vl_default` and `g16_vl_by` from the fixture and make the override merge of 14-06 follow them (comment the probe ids). Flip `test_suboption_warnings.py`: move the "xlabel valuelabel" SUBOPTIONS entry into `TestTheHonouredOnesStayQuiet`'s parametrisation. Flip `test_mode_parity.py`: the case at 1168-1169 becomes `{"xlabel": "#5, labcolor(red)", "ytitle": "Miles, orientation(vertical)"}` and the `_MUST_WARN` text of the key "xlabel with an unimplemented sub-option" names `labcolor(red)` (the key is kept: :1608-1611 requires it to name a corpus case; this section is the one whose gap silences the entry, rule R6 as index.md states it after the review); add a corpus case `_case("xlabel(1/5, valuelabel)", [plot_for("scatter", xvar="rep")], None, {"xlabel": "1/5, valuelabel"})` (the parity `_DF` has `rep` 3-5 but no labels for it — add `"rep_lbl": {"3": "Three", "4": "Four", "5": "Five"}` to `_VALUE_LABELS` and `"rep": "rep_lbl"` to `_LABEL_NAMES`, and check the existing hover/facet cases still agree); touch no other `_MUST_WARN` entry and never `ALLOWED`. Record the flips as `Flipped:` lines in `<scratch>/14-flips.txt`.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_value_labels_drawn.py -k "OnAxes or Twoway" test/test_suboption_warnings.py test/test_mode_parity.py -k "valuelabel or unimplemented or hover or by_panels" -q 2>&1 | tail -3` is green; `python3 -m pytest test/test_suboption_reporting.py -q 2>&1 | tail -2` names no new failure.]]></verify>
  <done>`xlabel(1/5, valuelabel)` drew the label set on the primary and second axes and on every by() panel in both modes and printed nothing; the two pinned tests and the `_MUST_WARN` case were flipped with the key kept.</done>
</task>

<task type="auto" id="14-13">
  <name>Show value labels in tooltips</name>
  <files>dash_render.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Implement TR-14.9, TR-14.10 (stage one) and TR-14.14: `_dash_hover_text_column`, `_dash_add_hover_text` (module level, before `_dash_hover_row` 19795), the `text_col=None` parameter appended to `_dash_hover_row` (tested first, never formatted), the `layers=None, value_labels=None, value_label_names=None` keywords appended to `_dash_build_hover` and its column pass (columns added on every renderer source in `_rends` that carries the variable, before `_fields_for` runs; `_fields_for` keeps its `_dash_is_stata_name` check), the two call sites (22348-22359 with `self.value_labels`/`self.value_label_names`; template 26451-26463 with `val_labels`/`val_label_names`, both by keyword), the template's build-time `_hover_label_vars` dict and the three-line redraw hook in `_on_filter_change` step 3 as section 17 rewrote it (locate `_live.data = _dash_keep_jitter(` by text, never by line). Add the two functions to the served function list after `_dash_value_labels_for` and to `function_test_map.py`. In `test_mode_parity.py` add the class `TestHoverShowsValueLabelsInBothModes` that renders cases "hover()" and "hover() on a bar" through `_standalone`/`_served` and asserts the tooltip row and column values agree (the corpus profile already compares tools and glyphs; this adds the values).
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_value_labels_drawn.py test/test_mode_parity.py -k "Hover or hover" test/test_server_layer_defects.py -k TheHoverBuilder test/test_label_sinks.py -q 2>&1 | tail -3` is green; `python3 -c "import inspect,dash_render as d;print(list(inspect.signature(d._dash_hover_row).parameters)[-1], [p for p in inspect.signature(d._dash_build_hover).parameters][-3:])"` prints `text_col ['layers', 'value_labels', 'value_label_names']`.]]></verify>
  <done>`hover(foreign)` showed Domestic/Foreign on every source the tooltip attaches to, in both modes, the column survived a saved snapshot rebuild and a served redraw, and the stage-one hover signatures were in place for section 12.</done>
</task>

<task type="auto" id="14-14">
  <name>Certify valuelabel and hover against twoway</name>
  <files>test/test_gaps2_truth.cscript, test/test_suboption_reporting.cscript</files>
  <action><![CDATA[
    Inside the S14 block of `test/test_gaps2_truth.cscript` (14-08), after AL-16 and before the `S14 end` line, add AL-17..AL-19: AL-17 defines the `alrep` label set on `sysuse auto`, exports `twoway scatter mpg rep78, xlabel(1/5, valuelabel)` and asserts with `cert_svg_has_text, file() text("Excellent")` and the dash page carrying every label text in its overrides; AL-18 the control `xlabel(1/5)` draws numbers in both; AL-19 `dash scatter mpg rep78, hover(rep78)` builds a page whose HoverTool references `__dash_hover_rep78` and whose source carries "Poor" (`cert_file_has`); update the block's `*` case index. Flip SR-02 in `test/test_suboption_reporting.cscript` (174-182): `_sr_check SR-02 "`lg'" xlabel "" "valuelabel"` — valuelabel is honoured and must not be named — and update the `*!` index line 20; record the flip in `<scratch>/14-flips.txt`. Run both scripts through the driver (`GAPS2_ONLY=S14` for the truth script).
  ]]></action>
  <verify><![CDATA[`grep -c "AL-[01][0-9] PASS" /tmp/dash-s14/run_test_gaps2_truth.log` prints 19 and `grep -c " FAIL" /tmp/dash-s14/run_test_gaps2_truth.log` prints 0; `/tmp/dash-s14/run_test_suboption_reporting.log` shows `SR-02 PASS` and no FAIL, with `grep -c '^r([0-9]*);' /tmp/dash-s14/run_test_suboption_reporting.log` printing 0.]]></verify>
  <done>twoway's valuelabel texts and dash's page agreed live in the S14 block, and the certification suite no longer expected valuelabel to be named.</done>
</task>

<task type="auto" id="14-15">
  <name>Close G16 in BUGS.md, help and CHANGELOG</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append at the end of BUGS.md the closed entry `- [x] Title: Value labels are never drawn on axes or in tooltips` with File Names and Line Numbers (`dash_render.py` `_dash_parse_axis_spec`, `_dash_apply_axis_spec`, `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_build_hover`, `_dash_hover_row`, `_dash_value_labels_for`), Description (GAPS2 G16's measured symptoms), Suggested fix, and `- Resolution: Fixed <ddmonyyyy> (WP-28, G16). valuelabel (minimum val) maps ticks through the first y variable's or the x variable's label set via _dash_value_labels_for and major_label_overrides on primary and second axes and every by() panel, and a labelled hover() variable shows its label through the derived column __dash_hover_<var> that survives saved snapshots and served redraws, in both renderers. Pinned by test/test_value_labels_drawn.py::TestValueLabelsOnAxes::test_valuelabel_draws_the_label_set, ::TestHoverShowsValueLabels::test_hover_foreign_shows_domestic_and_foreign, test/test_gaps2_truth.cscript AL-17; fixture test/fixtures/axis_truth.json.` -- the title holds no `"`. Rewrite dash.sthlp 672-680 (difference 6): value labels are used automatically where listed, an axis is labelled with numbers unless `valuelabel` (minimum `val`) is given — then the first y variable's or the x variable's labels, as in twoway — and a hover tooltip shows the value label of a `hover()` variable; add `valuelabel` to the sub-option list at 2328-2331; grep `test/test_help_claims_*.cscript` and `test/test_help_examples.py` for the changed lines and update any pin. In `CHANGELOG.md` replace the marker `<!-- WP-28 G16 -->` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of the release's `### Results that change` list (S01 placed it there, D2) with ONE line ending `(WP-28, G16)`: `xlabel(1/5, valuelabel)` was named and drew 1..5, now Poor…Excellent; `hover(foreign)` showed 0/1, now Domestic/Foreign (from `<scratch>/14-10-failure.txt`, Q24). Write nothing under any other heading. Run the full pytest suite once in the worktree (`python3 -m pytest test/ -q`, the second launch), then the S14 block and `test_suboption_reporting.cscript` through the driver; grep the three files and the message for `claude|anthropic`; commit 14-10..14-15 on `wp28-s14` as ONE commit, subject ending `(GAPS2 G16)`, body opening with `<scratch>/14-10-failure.txt` and carrying the `Regression:` / `Flipped:` (SR-02, the `_MUST_WARN` case, the SUBOPTIONS row) / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` with this message (index.md step 1); report `git checkout main && git merge s3-bugs` without running it.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_2.py -q 2>&1 | tail -2` is green; `grep -c '<!-- WP-28 B1 -->\|<!-- WP-28 G16 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, G16)' CHANGELOG.md BUGS.md` prints 2; `git log -2 --format=%s | grep -c '(GAPS2 B1)\|(GAPS2 G16)'` prints 2 and `git log -2 --format=%B | grep -ci "claude\|anthropic"` prints 0; `git status --short | grep -v '^??' | grep -v '.ultraplan\|REMAINING\|CLAUDE.md'` prints nothing.]]></verify>
  <done>G16 was closed in BUGS.md naming its tests, difference 6 in dash.sthlp was rewritten, the G16 marker was replaced by the line with the recorded old texts, and the section's second green commit on `wp28-s14` carried it.</done>
</task>

## Section completion criteria

- Every stub in "TDD test stubs" passes in both modes; the flipped tests and SR-02 pass in
  their new form; no test was deleted; each regression stub failed on the tree before its
  gap's fix for its recorded reason.
- `axis_truth.json` holds the `b1_label` (with `e3_tm_axis` and `e3_tm_axis_lab`) and
  `g16_valuelabel` groups produced by Stata in one regeneration, with the `_meta` stamp and
  every pre-existing probe unchanged, and is committed in the B1 commit.
- Two commits on `wp28-s14`, subjects ending `(GAPS2 B1)` and `(GAPS2 G16)`, each after a
  green full suite; no test-only commit exists (D1).
- The S14 block of `test_gaps2_truth.cscript` passes AL-01..AL-19 with 0 FAIL; no new
  `.cscript`, no runner or hygiene-pin edit (D11); `test_suboption_reporting.cscript` passes
  with SR-02 flipped.
- `_dash_expand_numlist`, `_dash_axis_tokens`, `_dash_axis_head_split`,
  `_dash_value_labels_for`, `_dash_hover_text_column`, `_dash_add_hover_text` are in the served
  function list after `"_dash_apply_axis_spec"` and in `function_test_map.py`;
  `_dash_axis_expand` and `_dash_axis_pieces` are in `program_coverage_map.py` citing AL-01 and
  AL-02.
- The full pytest suite is green under both interpreters with no skip before each commit.
- BUGS.md has closed B1 and G16 entries in the D3 form; dash.sthlp 672-680 and 2318-2331 are
  updated; both markers replaced; no AI references.
- Section 18 can read tick positions from `FixedTicker.ticks`, `ax._dash_extra_ticks` and the
  CustomJSTicker `extra`, and `norescale` has a tuple to join; section 12 finds
  `_dash_hover_row(…, text_col=None)`, `_dash_build_hover(…, layers=None, value_labels=None,
  value_label_names=None)`, `_dash_apply_axis_spec(…, value_labels=None)` and the
  `e3_tm_axis_lab` probe.

## Notes

- **Line numbers drift.** 14-04 to 14-06 add about 150 lines near 16041; every later anchor is
  also a symbol — locate by `def` name, never by a bare number after an insertion; sections 04,
  05, 13, 16 and 17 merge before this section in batch 2 and move the widget, colorvar and
  `_on_filter_change` regions.
- **Two undocumented readings are decided by the probes, not by taste.** Write the parser
  after reading `a1_twolines`, `a1_run_label`, `a1_spaces_incr`, `a1_single_quote`,
  `a1_str_first` and `label_refusals`; if `a1_spaces_incr` shows twoway refusing
  `2000 (500) 4000`, flip `test_axis_options.py::TestAxisLabelGrammar::test_increment_form_with_spaces`
  to that reading in 14-05 and record it as a `Flipped:` line.
- **The bound is the renderer's.** Stata's `numlist` refuses more than 1,600 elements with
  r(123); the ado step leaves such a run as written and the renderer bounds it at 2,000. A
  1,601-2,000 list is expanded in Python only (`TestTheBound::test_between_numlists_cap_and_the_bound_the_renderer_expands`);
  document nothing new (dash.sthlp already states the 2,000 bound).
- **Hostile runs never reach `numlist`.** A run holding a backtick, `$` or `'` is tagged `H`
  by `_dash_axis_pieces` and left as written; `xlabel(2000 $x 4000)` registers untouched
  (AL-02) and the renderer names `$x`. Every other run is passed as
  `` numlist `"`macval(run)'"' `` and holds no double quote by construction.
- **Commit bodies** use S01 TR-01.9's line forms verbatim: `Regression:
  test/<file>.py::<Class>::<test> -- failed at 91d97be with <text>`, `Flipped: <node> -- <old
  expectation> was wrong because <why>` (one per flip), `Fixture: test/fixtures/axis_truth.json
  (scripts/extract_axis_truth.do)` (the B1 commit), `BUGS.md: "<title>" (closed)`.
- **Shared registries (rules R1-R6).** R1: the AL cases are one block of
  `test_gaps2_truth.cscript`, appended above its closing line in section order; the runner and
  the hygiene pins are never edited. R2: the six new functions go after `"_dash_apply_axis_spec"`
  in the served function tuple; `function_test_map.py` and `program_coverage_map.py` entries in
  alphabetical place; the merger applies the `_vlookup` hunk beside S16's rewrite and the
  redraw hook inside S17's `_on_filter_change` by hand if `patch -p1` rejects them. R3: BUGS.md
  is appended at the end, each gap replaces only its own marker, and dash.sthlp 672-680,
  2318-2331 are this section's paragraphs. R4: no graph key is added (the ado expansion uses
  `_dash_option_rules`). R5: `axis_truth.json` is regenerated once here and once by section 18
  in batch 3 (which re-runs this section's groups unchanged, probe by probe, and removes the
  private reader for every group), never patched by hand. R6: `CORPUS` gains one case; the one `_MUST_WARN` entry
  this section's gap silences is changed with its key kept; `ALLOWED` is never edited.
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
  backtick; the script is run through `scripts/stata_slot.sh /tmp/dash-s14 <script>` (it sets
  its own directories; the wrapper sets `STATATMP=/tmp/dash-s14/tmp/` and holds one of three
  slots) — many sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`, after
  which every Python cscript SKIPs; a skip is not a pass; restore with `set python_exec
  /opt/anaconda3/bin/python3, permanently`. The `_meta` stamp keeps every existing key
  (`test_axis_options.py:637` reads `scheme_in_force`); the regeneration is checked probe by
  probe, never by a diff's line count.
- **`$dash_nobrowser`.** `cscript` drops every global: the truth script sets `global
  dash_nobrowser 1` right after its `cscript` line (S02), and the probe do-file of 14-07 sets
  it itself.
- **Security.** The value-label text in the hover column is a tooltip *field value*; BokehJS
  escapes it unless the field is written `{safe}` — never write `{safe}`. Label text in
  overrides is canvas text. `_dash_is_stata_name` still gates the variable name; the derived
  column name is built from a name that passed it.
- **X1 interplay.** `_dash_json_value` (13828-13862) turns a numeric-looking string into a
  float in the saved snapshot; section 17 (merged before this section) keeps string values as
  text, but this section's worktree starts from the batch-1 tree, so its hover tests use only
  non-numeric labels and the G16 entry records nothing about it.
