# Section 34: yvarlabel/xvarlabel, marker-label and marker-line options, mlabel defaults

> Part of: WP-31 · GAPS3 rows: D8, C17, E3, C14, C15 · Risk: green · Batch: 11 · Depends on: 01 · Blocks: -- · Tasks: 4, 5 commits · Case-id prefix: U34

## Overview

**What is wrong today.**

- **D8** (4.D, S2 NEW): "`yvarlabel()`/`xvarlabel()` (real twoway options, advanced_options.sthlp) undeclared: generic note, not drawn, not in the help." Evidence dash.ado:933-975 and :1167-1239 (neither syntax block declares them); test/fixtures/rejected_options.json:2300-2314 (`xvarlabel("Weight")` twoway rc 0, dash rc 0 with the note). `B/a/advanced_options.sthlp:135-137, 178-230`: `yvarlabel(quoted_strings)` one string per y variable and `xvarlabel(quoted_string)` "treat the specified strings as if they were the variable labels", used for the axis titles and the legend keys; `xvarlabel("")` removes the title. research/stata-ground-truth.md §1.2: `ZVARLabel YVARLabel XVARLabel` are factored in `FactorPlot` (:755-803) for every yxview type.
- **C17** (4.C, S3 NEW): "`mlabprefix()`/`mlabsuffix()` (StataNow) and `lalign()` at plot level are undeclared: generic note, absent from the help's Unsupported list. `headlabel` is accepted-and-named on pcspike/pcscatter/pci/pcarrowi where only pcarrow/pccapsym take it (twoway unverified)." Research §1.2 lists `MLABPREfix MLABSUFFix` and `LAlign` among the seriesstyle options every yxview type factors; §1.3 settles headlabel: accepted on **all** yxyx types and all y3x types (`yxyxview_parse:52,67`; `y3xview_parse:57,72`), so dash's accept-and-name is right and S02 (C1) declares it; S34 records the finding and changes nothing about headlabel.
- **E3** (4.E, S2): "`msangle(anglestyle name)` noted and drawn at 0 degrees although `_DASH_ANGLESTYLES` exists; `mlalign()`, `mwidth`, `mlabstyle()` undeclared (generic note)." Evidence dash_render.py:13465-13475 (`float(str(options["msangle"]))`, a name is a `ValueError` → `_dash_style_note` and no rotation) beside `_dash_anglestyle_degrees` (:6386-6420) which `mlabangle` already uses (:14303). `mlalign` is declared pending by S08 (batch 3, D-08.d); `mwidth` is S03's (C2, batch 1: "Read msize() with mwidth on rbar") -- 34-01 checks both and S34 declares only what is still undeclared.
- **C14** (S3): "`rscatter y y2 x, mlabel(y)` draws; twoway r(102)." Evidence dash.ado:3712-3760 (`_dash_mlabel_list`) and :2132-2165 (the range types' variable count in `_dash_mlabv_parse`'s caller counts `mlabvposition` but not `mlabel` toward `limit 3`). The exact twoway sentence is measured in 34-01 (research §1.1: `y2xview_parse:35-45` "exactly 3 vars else `type' requires 3 variables" r(103)/r(102)).
- **C15** (S3): "Bar marker labels default to 3 o'clock; twoway's bar default is 12." Evidence dash_render.py:14360 `pos = str(options.get("mlabposition", "3") or "3")`; research §13: `labelstyle-p#bar.style` → `clockdir pbar 12` for bar and rbar (`_type_suffix` returns "bar" for bar/rbar only), every other type 3.

**After this section.** `yvarlabel()`/`xvarlabel()` are declared, written to the spec and read wherever a series label is read (`_dash_layer_series`, dash_render.py:39826: axis default titles and legend keys both come from it). `mlabprefix()`/`mlabsuffix()` are declared and drawn (text column = prefix + text + suffix); `lalign()`, `mlalign()`, `mlabstyle()` are declared, `center` honoured silently, `inside`/`outside` named once ("drawn centred": Bokeh strokes are centred on the path), `mlabstyle(p#)` read as the label's pstyle (colour and size from `labelstyle p#` through the scheme, the position from the type's default clock). `msangle(forty_five)` and every anglestyle name rotate the markers. `rscatter y y2 x, mlabel(y)` returns twoway's rc and sentence. bar and rbar labels default to 12 o'clock.

**Test order and commit rule.** Five rows, five commits in the order D8, C17, E3, C15, C14: 34-01 writes tests and fixture, no commit; 34-02 lands D8 and C17; 34-03 lands E3 and C15; 34-04 lands C14 and finishes the help.

### Section decisions (binding on the executor)

- **D-34.a `yvarlabel()` is one quoted string per y variable, in order; `xvarlabel()` one string.** Parsed with `_dash_stylelist_locals` (the per-y element splitter dash already uses, dash_parse.mata:5283-5292 `_dash_stylelist_keys`); `yvarlabel` joins `_dash_stylelist_keys()` so the per-y writer splits it per series as it splits `mlabel`. The renderer's `_dash_layer_series` substitutes `options["yvarlabel"]`'s element for `L(yvar)` and `options["xvarlabel"]` for `L(xvar)` when present (a raw `""` element removes the label, as twoway's `xvarlabel("")` does: the title and key are empty text). Both the axis default title (`_dash_axis_default_titles`, :28538) and the legend keys (`_dash_legend_keys`, :39925) read `_dash_layer_series`, so one edit serves both.
- **D-34.b Prefix and suffix are text, not variables.** `mlabprefix(string asis)`/`mlabsuffix(string asis)` are read by value; the LabelSet text column is built in `_apply_mlabel_opts` as `prefix + text + suffix` per row after value labels and `mlabformat()` are applied; the text reaches the page as a column (canvas text, never HTML), so no escaping is needed beyond what the column already gets.
- **D-34.c Alignment options are honoured as `center` and named otherwise.** `lalign()`, `mlalign()` (and the existing `clalign`-style spellings dash may already name) accept `center|inside|outside` (twoway's `alignmentstyle`); `center` is silent (Q36: honoured); `inside`/`outside` print one note `dash: lalign(inside) is drawn centred: the page cannot align a stroke to a side.` (through `_dash_style_note`'s sentence form); any other word is refused with twoway's measured line (`lalign(bogus)` measured in 34-01).
- **D-34.d `mlabstyle(name)` reads the scheme's labelstyle.** `SchemeParser` gains `label_style(name) -> dict(color=?, size=?, position=?)` reading `labelstyle-<name>.style`'s stubs as the shipped translation holds them (`color p#label`, `gsize label`, `clockdir p 3`/`pbar 12`); unknown name → twoway's measured refusal line. `mlabstyle` joins `_dash_stylelist_keys()`.
- **D-34.e The type's default clock lives in the mapper call.** `map_bar` (dash_render.py:15272) and `map_rbar` (:18512) pass `options` with `mlabposition` defaulted to `"12"` (`opts = dict(options); opts.setdefault("mlabposition", "12")`) at their `_apply_mlabel_opts` calls (:15459, :19210, :19212); every other call keeps the applier's default `"3"`. `_apply_mlabel_opts` itself is not edited for this (R12: S34 is batch 11's `dash.ado syntax + mlabel readers` owner; it edits the applier for prefix/suffix and mlabstyle only).
- **D-34.f C14's rule is the measured one.** 34-01 measures `rscatter y y2 x, mlabel(y)`, `mlabel(y2)`, `mlabel(x)`, `mlabel(other)`, `mlabel(y other)`, and the same on rcapsym and rconnected (the three range types that label). The hypothesis: twoway refuses with r(102) when a label variable is also a plotted variable because its serset variable list collapses the duplicate. Whatever the fixture says is implemented in `_dash_mlabel_list`'s caller for `mv_range` types (dash.ado:2132 list): the measured condition, rc and sentence, copied as literals with the fixture key in a comment.

## Risk: [green] -- declarations, one series-label reader, two defaults; every text is measured

**Why.** The edits are the declared-option recipe (research/codebase-mechanics.md §1d(a), seven steps) and a two-line default in two mappers. Risk factors: (1) `_dash_layer_series` feeds axis titles, legend keys and the first-equals-last rule -- a wrong substitution changes default titles everywhere; (2) the `mlabel` LabelSet text column is also the hover-label column in places (`_dash_add_hover_text`, :39991-40020) -- prefix/suffix are written to a NEW column (`label_col + "_mlab"`) that only the LabelSet reads, so `label_col` (the tooltip's) is untouched; (3) S08 and S03 may already have declared `mlalign`/`mwidth`; (4) `yvarlabel` as a stylelist key must not break `p()` drops. Mitigation: (1) `test_series_labels_without_the_options_are_unchanged` digests `_dash_layer_series` over the parity corpus's specs before and after; (2) `test_the_tooltip_is_unchanged_by_prefix`; (3) 34-01's grep decides; (4) `_dash_p_drops` (dash.ado:4415-4430) is read before adding.

## Dependencies

- **Depends on: 01** (entries D8, C17, E3, C14, C15 open). Reads what S08 (mlalign pending) and S03 (mwidth) left. DECISIONS D2: mlabel's minimum abbreviation becomes twoway's `mlab` and `mla()` is `mlalign()`; S08 declares both (batch 3) and S34 only draws `mlalign` (D-34.c) -- S34 adds no abbreviation rule. **Blocks: --.**
- **Parallel batch: 11** with S32 (figure sizing) and S33 (axis label/scale appliers). S34 edits the plot syntax (dash.ado:1167-1239), `sreturn`s, `_dash_plot_opts_to_json`, `_dash_stylelist_keys`, `_dash_mlabel_list`'s range caller, `_apply_mlabel_opts`, `_apply_marker_opts`' `msangle` branch (:13465-13475), `_dash_layer_series`, `SchemeParser.label_style` (new), `map_bar`/`map_rbar`'s call lines. S33 edits `_dash_apply_axis_spec`/scale appliers, S32 `_dash_layout_cell`, `_dash_figure_aspect` and `_make_figure_body`'s tail; disjoint. The index gives S33 the appliers of axes, S34 the mlabel readers; `_apply_marker_opts` is not in R12's four `_apply_*` list? It is (the four appliers: line, marker, fill, mlabel): S34 is batch 11's editor of `_apply_marker_opts` (msangle) and `_apply_mlabel_opts`; S32 and S33 must not touch them (their Boundaries say so; confirm at 34-01). `_dash_option_rules` is S32's in batch 11 (DECISIONS A15): S34 does not edit it; its `lalign`/`mlalign` enum tokens are handed to S32's rules edit (TR-34.1).

## Evidence

### Declarations (dash.ado:1167-1239, :933-966)

The plot syntax line :1170 `MLabel(string asis) MLABColor(string asis) MLABSize(string asis)`, :1171 `MLABPosition(string asis) MLABGap(string asis) MLABWidth(string)`; the marker options :1168-1169; `MLABANGle MLABFormat MLABTextstyle MLABVposition` :1202-1203; `XVARFormat YVARFormat` :1205 (plot syntax; :1207-1211 is the graph syntax). The graph syntax (:933-966) has no varlabel option (twoway's are plot options; `FactorPlot`). sreturns :1403-1530; JSON key list :4441-4458 (`mlabangle mlabformat mlabvposition mlabtextstyle xvarformat yvarformat` at :4454-4456); `_dash_p_drops` :4415-4430; `_dash_stylelist_keys()` dash_parse.mata:5286-5292 (`mlabel jitter base barwidth` and `mlabtextstyle` are per-y lists).

### The undeclared table (dash_parse.mata:6250-6324)

Rows read at 6370ca4: `headlabel` (pcs), `mwidth` (`histogram rbar`); NO row for `yvarlabel xvarlabel mlabprefix mlabsuffix lalign mlalign mlabstyle` (they fall to the catch-all and are named by the generic note). So S34 deletes the `mwidth` row only if S03 did not (34-01 grep), and adds `mwidth` to `_dash_rep_unique` (:6200) in that case (the table lists options twoway takes once).

### msangle (dash_render.py:13465-13475) and the anglestyles (:6379-6420)

```python
13467        if "msangle" in options:
13468            try:
13469                angle_deg = float(str(options["msangle"]).strip())
13475                _dash_style_note("msangle", options["msangle"], "angle")
13477                if hasattr(glyph, "angle"):
13478                    glyph.angle = math.radians(angle_deg)
```

`_DASH_ANGLESTYLES = {"default": 0, "zero": 0, "horizontal": 0, "forty_five": 45, "ninety": 90, "vertical": 90, "rhorizontal": 180, "rvertical": 270, "two_seventy": 270, "stdarrow": 28.64}`; `_dash_anglestyle_degrees(raw)` returns degrees or None (names, -360..360 numbers, strict spelling). `mlabangle` uses it at :14303. The rules table bounds `msangle=style,-360,360` (dash.ado:2993); `_dash_validate_value`'s `style` kind passes names untouched (:3261-3264), so a bogus name reaches the renderer today and `mlabangle=style,-360,360@...` (:3007) behaves the same -- whether twoway refuses `msangle(bogus)` is the fixture's `msangle.bogus` (TR-34.4).

### The mlabel default (dash_render.py:14358-14364) and the mapper calls

```python
14360        pos = str(options.get("mlabposition", "3") or "3").strip()
```

Calls: `map_bar` :15459 `self._apply_mlabel_opts(fig, clean_source, options, xvar, yvar, ...)`; `map_rbar` :19210 and :19212 (both ends). test_marker_label_parity.py `test_labels_are_drawn_where_twoway_draws_them` (:420) and `test_the_label_options_reach_every_label` (:458) pin positions through options, not defaults; `grep -n '"3"\|mlabposition' test/test_marker_label*.py test/test_glyphs.py` in 34-01 finds any pin of the bar default (flip).

### Series labels (dash_render.py:39826-39905) and their readers

`_dash_layer_series(plot, var_labels, default_level)` returns `[(y_label, x_label), ...]` with `L(name) = _dash_var_label(vl, name)`; read by `_dash_axis_default_titles` (:28538-28575) and `_dash_legend_keys` (:39925). `_dash_var_label(var_labels, name, default="")` :36640.

### C14's count (dash.ado:2132-2165, :3712-3760)

`_dash_mlabv_parse`'s caller: `mv_range "rarea rbar rcap rcapsym rconnected rline rscatter rspike tsrline"`, `limit 3`, `counted = all - labs` (labels are NOT counted on range types today, :2150), the message `<ptype> requires 3 variables: <all>` r(103). `_dash_mlabel_list` (:3712) validates each element as a variable and returns the normalised list; it never compares the label variables with the plotted ones.

### Pinned tests (flip, never delete)

| Node | Today | After |
|---|---|---|
| test/test_unsupported_report_is_true.py :725-726 counts | 197/85 after S08 (196 at 6370ca4) | +`yvarlabel xvarlabel mlabprefix mlabsuffix lalign mlabstyle` (+`mwidth`, +`mlalign` if not yet declared): `# 197 -> 203: D8 C17 E3 declared` |
| test/test_help_claims_*.py / cscripts asserting the generic note names `yvarlabel()` etc. (`grep -rn "yvarlabel\|mlabprefix\|lalign\|mlabstyle\|msangle(forty" test/`) | named in the note | drawn (silent) or the measured refusal |
| test/fixtures/rejected_options.json readers for `xvarlabel`/`yvarlabel` rows (`disposition rc0-at-c96facd`) | dash rc 0 + note | dash rc 0, no note: the reader's expectation moves |
| test/test_glyphs.py marker-angle tests for `msangle` with a name (`grep -n "msangle" test/test_glyphs.py test/test_marker*.py`) | drawn at 0 with a note | rotated |
| any test pinning rscatter `mlabel(y)` drawing (`grep -rn "mlabel(lo)\|mlabel(y)" test/*.cscript`; test_twoway_option_parity.cscript:3578 names `rscatter lo hi weight, mlabel(lo) mlabvposition(p9)`) | drawn | the fixture's rc and line (flip only the cases the fixture refuses) |

## User stories

- **US-34.1** As a twoway user, I want `scatter mpg weight, yvarlabel("Miles") xvarlabel("Pounds")` to title the axes and the legend keys with those strings.
- **US-34.2** As a twoway user, I want `mlabel(make) mlabprefix("[") mlabsuffix("]")` drawn as `[Buick Century]`.
- **US-34.3** As a twoway user, I want `msangle(forty_five)` to rotate the markers, as `msangle(45)` does.
- **US-34.4** As a twoway user, I want `lalign(center)` accepted silently, `lalign(inside)` named once, and `mlabstyle(p2)` to style my labels as p2's.
- **US-34.5** As a twoway user, I want bar labels above the bars by default, as in twoway.
- **US-34.6** As a twoway user, I want `rscatter y y2 x, mlabel(y)` answered as twoway answers it.

## Business requirements

- **BR-34.1** `yvarlabel()`'s k-th string is the k-th y series' label in the legend and in the default axis title (first-equals-last rule over the substituted labels); `xvarlabel()` likewise for x; `("")` removes; both silent; both modes.
- **BR-34.2** `mlabprefix()`/`mlabsuffix()` wrap every label's text on every type that draws labels; tooltips unchanged; both modes.
- **BR-34.3** `lalign()`/`mlalign()`: `center` silent; `inside`/`outside` one note; other words refused as twoway refuses them (measured).
- **BR-34.4** `mlabstyle(p#)` colours and sizes the labels as the scheme's `labelstyle p#` says; an unknown name is refused as twoway refuses it (measured).
- **BR-34.5** `msangle(<anglestyle name>)` rotates by the name's degrees; a bad name is answered as twoway answers it (`msangle.bogus` measured: refused with twoway's line when its rc is non-zero, else drawn unrotated with one note).
- **BR-34.6** bar and rbar labels default to 12 o'clock; `mlabposition()` still overrides; every other type's default is unchanged.
- **BR-34.7** `rscatter|rcapsym|rconnected y y2 x, mlabel(<plotted var>)` returns the fixture's rc and line; `mlabel(<other var>)` draws.
- **BR-34.8** Every newly declared option is in the help (test_help_conformance.py:825 for dash-only spellings; the Unsupported list for anything still named).

## Technical requirements

- **TR-34.1 Declarations.** dash.ado plot syntax: after `YVARFormat(string)` (:1205) add `YVARLabel(string asis)  XVARLabel(string asis)`; after `MLABWidth(string)` (:1171) add `MLABPREfix(string asis) MLABSUFFix(string asis) MLABSTyle(string asis)`; after `LALpha(string)` (:1173) add `LAlign(string)`; `MLAlign(string)` only if `grep -c "MLAlign" dash.ado` is 0 (else S08's stands); `MWidth` only if `grep -c "MWidth" dash.ado` is 0 (else S03's). sreturns after their neighbours (:1403-1530). JSON keys (:4441-4458): `yvarlabel xvarlabel` after `yvarformat`; `mlabprefix mlabsuffix mlabstyle` after `mlabtextstyle`; `lalign mlalign mwidth` after `lalpha`-region keys. `_dash_stylelist_keys()` gains `yvarlabel mlabstyle mlabprefix mlabsuffix` (per-y lists; `xvarlabel` is one value). `_dash_p_drops`: read :4415-4430 and add the three label keys if `mlabel` is dropped there. Pending lines: none (all drawn or settled). `_dash_rep_und_tab`: delete the `mwidth` row if S34 declares `mwidth`; add `"mwidth"` to `_dash_rep_unique`'s list (:6206-6214) in that case. Rules (`_dash_option_rules`, dash.ado:2990-3010): S32 is batch 11's rules editor (DECISIONS A15); the two tokens `lalign=enum,center|inside|outside  mlalign=enum,center|inside|outside` are handed to S32's rules edit as disjoint tokens (S32 adds them in batch 11; S34 reads them and does not edit `_dash_option_rules`). `msangle` keeps `style,-360,360`; its bogus-name answer is TR-34.4's.
- **TR-34.2 `_dash_layer_series` (D-34.a).** After `def L(name)`: `yl = _dash_stylelist_elements(opts.get("yvarlabel"))` is NOT available in Python -- the spec already carries the per-y element for a stylelist key (the writer picks element k for y number k, `_dash_stylelist_pick`), so `opts.get("yvarlabel")` is this series' string or absent. Rule: `ylab = opts["yvarlabel"] if "yvarlabel" in opts else L(yvar)` (a present empty string gives `""`); `xlab = opts["xvarlabel"] if "xvarlabel" in opts else L(xvar)`; applied in the data-layer, range (`pair()` on both boundaries uses `ylab` for each), pc, and fit branches where `L(y)`/`L(x)` of the plotted variables are read; the computed-text branches (`Fitted values`, `kdensity <var>`) are twoway's own words and unchanged.
- **TR-34.3 `_apply_mlabel_opts` (D-34.b, D-34.d).** After the text column is final (after `_mlabformat_column`): `pre = str(options.get("mlabprefix", "") or "")`, `suf = ...`; if either, write a NEW column `label_source.data[label_col + "_mlab"] = [pre + t + suf ...]` and point the LabelSet's `text` field at it; `label_col` is untouched (it also feeds the hover text at map_bar :15459, where the LabelSet source is `clean_source`). `mlabstyle`: `st = self.scheme.label_style(options["mlabstyle"])` when present; its `color`/`size` seed `text_color`/`text_font_size` before `mlabcolor()`/`mlabsize()` are read (explicit options win). `SchemeParser.label_style(name)` (new method, copied with its class, R2 n/a): reads `color <name>label`→`color p#label` fallback and `gsize label`, `clockdir` for `pbar`; unknown → raises `ValueError`, caught by the applier into the measured refusal? No -- refusals are Stata's: dash.ado refuses `mlabstyle(bogus)` with the fixture's line (rule kind `istyle` for `mlabstyle`, :3308: read how `pstyle` is checked and copy).
- **TR-34.4 msangle (E3).** dash_render.py:13467-13482: replace the `float(...)` read with `deg = _dash_anglestyle_degrees(options["msangle"])`; `None` → `_dash_style_note("msangle", ..., "anglestyle")` and no rotation; else `glyph.angle = math.radians(deg)`. The bogus name: if fixture `msangle.bogus` has rc≠0, refuse in dash.ado by an `anglestyle` kind in `_dash_validate_value` (a name in `_DASH_ANGLESTYLES` or a number within the bounds) with the measured line -- the kind is S34's own branch at :3261ff, not a rules-table token; else (rc 0) the renderer's note above is the answer and dash.ado is unchanged.
- **TR-34.5 Alignment (D-34.c).** The three alignment options reach the renderer; `_apply_line_opts` (lalign), `_apply_marker_opts` (mlalign) read them: `center` → nothing; `inside`/`outside` → `_dash_style_note(opt, value, ...)` with the sentence of D-34.c, once per page (`_dash_warn_once` key `("align", opt, value)`). `_apply_line_opts` is S41's hot function in batch 14 and no one's in batch 11 -- S34 adds the five-line read; S41 is told in Notes.
- **TR-34.6 Bar default (D-34.e).** `map_bar` :15459 and `map_rbar` :19210/:19212: `_mlopts = dict(options); _mlopts.setdefault("mlabposition", "12")` before the call, passing `_mlopts`. (The applier's note for an unknown position says "12 (above)" already: unchanged.)
- **TR-34.7 C14 (D-34.f).** In the range-type count (dash.ado:2150-2165) after `local labs` is known: `if `: list ptype in mv_range' & "`labs'" != "" { local dup : list labs & pvars; if "`dup'" != "" { <fixture rc/sentence> } }` -- the condition, rc and sentence literal come from `test/fixtures/varlabel_mlabel_truth.json` `c14.<case>`; the executor writes them as literals with the key in a comment. If the fixture shows twoway DRAWS (rc 0) every case, C14 is closed as "measured false" with its BUGS entry Resolution saying so and no code change.
- **TR-34.8 Registries.** test/test_unsupported_report_is_true.py: `LIVE_VALUES` entries for `yvarlabel xvarlabel mlabprefix mlabsuffix msangle(name) mlabstyle` (two values that render differently), `PLOT_VALUES`/`ALIASES` for `lalign mlalign` if kept as "named for inside/outside" (classify as LIVE with `center`/`inside`: they render the same -- so classify in `ALIASES`-like `ROUTED`? Read the file's categories and put them where an accepted-and-sometimes-noted option goes, with a comment); counts moved with `# old -> new: D8 C17 E3 <why>`. test/function_test_map.py: `SchemeParser.label_style`. test/program_coverage_map.py: no new program. test_help_conformance.py:825: every new spelling is twoway's (in abbrev_truth.json after S08's regeneration? `yvarlabel` etc. must be in the extractor's option list or `_twoway_spelling` fails → add the six names to scripts/extract_abbrev_truth.do's option table is S08's file; instead give each a help definition entry (R3) so the test passes either way).
- **TR-34.9 Security.** Prefix/suffix and varlabels are canvas text through Bokeh columns and axis labels; the legend label is a Bokeh property. No HTML sink; no new JS. `mlabstyle` names reach `SchemeParser` lookups through the existing name check (`_dash_is_stylename`-style; read `pstyle`'s path).

### Code to insert (verbatim where marked)

**TR-34.1 the syntax additions (dash.ado; each line shows the neighbour it follows):**

```stata
        MLABPosition(string asis) MLABGap(string asis)      MLABWidth(string) ///
        MLABPREfix(string asis)   MLABSUFFix(string asis)   MLABSTyle(string asis) ///
        MALpha(string)            MARKER(string)            LColor(string asis) ///
        LWidth(string asis)       LPattern(string asis)     LALpha(string) ///
        LAlign(string) ///
        ...
        XVARFormat(string)        YVARFormat(string) ///
        YVARLabel(string asis)    XVARLabel(string asis) ///
```

(`MLAlign(string)` already follows the mlabel declaration after S08; `MWidth` after S03 -- `<scratch>/s34/prior.txt` decides.)

**TR-34.2 `_dash_layer_series` (dash_render.py:39826ff; after `def L(name)` add, and use `Ly`/`Lx` for the plotted variables' labels in the data, range, pc and fit branches):**

```python
    def Ly(name):
        # yvarlabel("...") stands in for the y variable's label; the spec
        # carries this series' element of the per-y list (WP-31 D8;
        # advanced_options.sthlp:178-230).  A present "" removes the label.
        if "yvarlabel" in opts and isinstance(opts["yvarlabel"], str):
            return opts["yvarlabel"]
        return L(name)

    def Lx(name):
        if "xvarlabel" in opts and isinstance(opts["xvarlabel"], str):
            return opts["xvarlabel"]
        return L(name)
```

`pair(a, b)` reads `Ly` for both boundaries; `L(plot.get("xvar"))` becomes `Lx(plot.get("xvar"))`; the computed-text branches stay.

**TR-34.3 prefix/suffix (`_apply_mlabel_opts`, after the text column is final):**

```python
        # mlabprefix()/mlabsuffix() (WP-31 C17): text around every label,
        # on the LabelSet's own column only (tooltips keep the bare text).
        pre = str(options.get("mlabprefix", "") or "")
        suf = str(options.get("mlabsuffix", "") or "")
        if (pre or suf) and label_col in getattr(label_source, "data", {}):
            mlab_col = label_col + "_mlab"
            label_source.data[mlab_col] = [
                pre + ("" if t is None else str(t)) + suf
                for t in label_source.data[label_col]]
            label_set.text = mlab_col          # the LabelSet reads the new column
```

(`label_source`/`label_col`/`label_set` are the names the applier gives the LabelSet's source, text field and model; read them at :14104-14400 before inserting. `label_col` is never rewritten: at map_bar :15459 the source is `clean_source` and the same column feeds the hover text.)

**TR-34.4 msangle (dash_render.py:13467-13482, replaces the `try` block):**

```python
        if "msangle" in options:
            # An anglestyle name or a number (WP-31 E3): forty_five rotates
            # 45 degrees, as mlabangle() already reads it.
            deg = _dash_anglestyle_degrees(options["msangle"])
            if deg is None:
                _dash_style_note("msangle", options["msangle"], "anglestyle")
            elif hasattr(glyph, "angle"):
                glyph.angle = math.radians(deg)
                if hasattr(glyph, "angle_units"):
                    glyph.angle_units = "rad"
```

**TR-34.6 the bar default (map_bar :15459; map_rbar :19210 and :19212):**

```python
        # Bar labels sit above their bars by default: labelstyle p#bar,
        # clockdir pbar 12 (WP-31 C15; every other type keeps 3).
        _mlopts = dict(options)
        _mlopts.setdefault("mlabposition", "12")
        self._apply_mlabel_opts(fig, clean_source, _mlopts, xvar, yvar, ...)
```

**TR-34.7 C14 (dash.ado, in the range count after `local labs` is known, :2150 region; the literals from `<scratch>/s34/c14.txt`):**

```stata
    // A range plot labelled by one of its own variables (WP-31 C14): twoway
    // answers <rc> "<sentence>" (test/fixtures/varlabel_mlabel_truth.json
    // c14.y, c14.y2, c14.x).
    if `: list ptype in mv_range' & "`labs'" != "" {
        local _c14dup : list labs & pvars
        if "`_c14dup'" != "" {
            display as error "<sentence as measured>"
            exit <rc as measured>
        }
    }
```

## Boundaries

- Not S34's: `headlabel` (S02 declares; research settles its type set -- S34 writes the finding into C17's Resolution); drawing `mwidth` (S03); the `rbar msize()` width (S03); minor-tick label styles (S24); legend geometry (S31); `mlabel()` several variables in one element (S06); `_dash_mlabel_list`'s element checks (S06); axis-title styling (S33); `_apply_fill_opts`; `_FILTER_JS`; the template.

## Stata truth

**New extractor** `scripts/extract_varlabel_mlabel_truth.do` → `test/fixtures/varlabel_mlabel_truth.json` (path-free form; `_meta` five keys; `git add -f`). `sysuse auto`; `gen lo = mpg - 2`, `gen hi = mpg + 2`; `set scheme s2color`.

| Key | twoway command | Recorded |
|---|---|---|
| `varlabel.y`, `x`, `both`, `x_empty`, `y_two` | `scatter mpg weight, yvarlabel("Miles")` / `xvarlabel("Pounds")` / both / `xvarlabel("")` / `scatter mpg price weight, yvarlabel("A" "B")` | rc; `.Graph.yaxis1.title.text`, `.xaxis1.title.text`; legend key texts (`.Graph.legend.keys[k].label.text` or the SVG texts) |
| `prefix.both` | `scatter mpg weight in 1/3, mlabel(make) mlabprefix("[") mlabsuffix("]")` | rc; the SVG label texts |
| `align.center`, `inside`, `outside`, `bogus`; `malign.*` | `line mpg weight, lalign(center|inside|outside|bogus)`; `scatter ..., mlalign(...)` | rc and line |
| `mlabstyle.p2`, `bogus` | `scatter mpg weight in 1/3, mlabel(make) mlabstyle(p2)` / `mlabstyle(bogus)` | rc and line; label colour from SVG |
| `msangle.forty_five`, `bogus`, `n45` | `scatter mpg weight, msymbol(T) msangle(forty_five)` / `msangle(bogus)` / `msangle(45)` | rc and line; the marker rotation (SVG `transform` or equality of the forty_five and 45 SVGs) |
| `bardefault.bar`, `rbar`, `scatter` | `bar mpg weight in 1/3, mlabel(make)`; `rbar lo hi weight in 1/3, mlabel(make)`; `scatter ...` | `.Graph.plotregion1.plot1.style.label.position` (expected 12, 12, 3) |
| `c14.y`, `y2`, `x`, `other`, `y_other`, `rcapsym_y`, `rconnected_y` | `rscatter lo hi weight, mlabel(lo)` / `mlabel(hi)` / `mlabel(weight)` / `mlabel(make)` / `mlabel(lo make)`; `rcapsym lo hi weight, mlabel(lo)`; `rconnected ...` | rc and line |
| `mwidth.rbar`, `mlalign.declared` | `rbar lo hi weight, mwidth`; `scatter mpg weight, mla(center)` | rc (for S03/S08 cross-checks) |

**Truth blocks** (R1; DECISIONS A14: one block per row, appended by the row's closing task -- 34-01 appends only D8's): `* ==== S34 D8: yvarlabel() and xvarlabel() ====` (U34-1), `* ==== S34 C17: mlabprefix(), mlabsuffix(), lalign() ====` (U34-2, U34-3), `* ==== S34 E3: msangle names, mlalign(), mwidth, mlabstyle() ====` (U34-4, U34-5), `* ==== S34 C15: bar label default ====` (U34-6), `* ==== S34 C14: range plots labelled by a plotted variable ====` (U34-7); helpers `_u34_*` above the first block; each block ends `* ==== end S34 <row> ====`:
- **U34-1** `varlabel.*`: dash's axis titles and legend key texts equal twoway's, both modes; no `(note:` in the log.
- **U34-2** `prefix.both`: the LabelSet texts equal twoway's SVG texts, both modes; the HoverTool tooltips are the same as without the options.
- **U34-3** `align.*`, `malign.*`: dash's rc equals twoway's; `center` logs no note; `inside` logs exactly one `drawn centred` line; `bogus` logs twoway's line.
- **U34-4** `mlabstyle.p2`: label colour equals the scheme's `color p2label`; `bogus` → twoway's rc and line.
- **U34-5** `msangle.forty_five`: both modes' marker `angle` is `radians(45)`; `msangle(bogus)` → twoway's rc and line; `n45` equals `forty_five`.
- **U34-6** `bardefault.*`: dash's LabelSet anchors for bar and rbar are the 12 o'clock placement (`text_baseline == "bottom"`, `text_align == "center"` as `_MLABEL_CLOCK[12]` gives) and scatter's the 3 o'clock one.
- **U34-7** `c14.*`: dash's rc and line equal twoway's for every case.

**Block skeleton** (WP-30 form; the D8 block -- the other four repeat it with their row id and cases):

```stata
// S34 helpers (WP-31 D8 C17 E3 C14 C15).  _u34_titles: axis titles and
// legend key texts of a registered graph, saved and served; _u34_labels:
// a LabelSet's texts, align and baseline; _u34_angle: the scatter's
// angle; each through globals u34_s, u34_v.
python:
(helpers, top level)
end
* ==== S34 D8: yvarlabel() and xvarlabel() ====
local only : env WP31_ONLY
if inlist("`only'", "", "S34") & `: list posof "S34" in w31_run' {
display as text "S34 D8 start"
sysuse auto, clear
dash clear
// U34-1
local lg "`c(tmpdir)'dash_u34_1.log"
quietly log using "`lg'", name(_u34log) text replace
capture noisily dash scatter mpg weight, yvarlabel("Miles") xvarlabel("Pounds") name(u341)
local rc = _rc
quietly log close _u34log
_w31_expect U34-1 (`rc' == 0) "yvarlabel/xvarlabel rc `rc'"
cert_file_has "`lg'", needle("(note:")
_w31_expect U34-1 (r(found) == 0) "a note was printed for a drawn option"
tempfile sp dp
_dash_serve_spec, specpath("`sp'") datapath("`dp'")
python: _u34_titles("`sp'", "`dp'")
_w31_expect U34-1 ("${u34_s}" == "${u34_v}") "saved ${u34_s} vs served ${u34_v}"
python: _u34_fixture("varlabel.both")       // twoway's titles/keys into u34_f
_w31_expect U34-1 ("${u34_s}" == "${u34_f}") "dash ${u34_s}, twoway ${u34_f}"
_w31_done U34-1 "yvarlabel() and xvarlabel() title the axes and keys as twoway does"
dash clear
display as text "S34 D8 end"
}
* ==== end S34 D8 ====
// The C17 block (U34-2, U34-3), E3 (U34-4, U34-5), C15 (U34-6) and C14
// (U34-7) blocks follow the same skeleton, each appended by its row's task.
```

**Area script** test/test_option_validation.cscript: **U34-8** `yvarlabel("A") xvarlabel("B")` rc 0 and the registry JSON carries both keys; **U34-9** `lalign(bogus)` rc equals the fixture's; **U34-10** `headlabel` on pcspike, pcscatter, pci, pcarrowi, pcarrow, pccapsym: rc 0 (guard; research §1.3).

## TDD test stubs

### Regression tests, one new file per row (DECISIONS A14; red at 6370ca4 unless guard)

| Row | File | Classes |
|---|---|---|
| D8 | `test/test_varlabel_options.py` | `TestTheFixture`, `TestVarlabels`, `TestTheDeclarations` |
| C17 | `test/test_mlabel_prefix_suffix.py` | `TestPrefixSuffix`, `TestAlignment` |
| E3 | `test/test_msangle_mlabstyle.py` | `TestMsangle`, `TestLabelStyle` |
| C15 | `test/test_mlabel_bar_default.py` | `TestBarDefault` |
| C14 | `test/test_range_mlabel_rule.py` | `TestTheRule::test_dash_ado_carries_the_fixture_literals` (source read of dash.ado for the `c14.*` rc and sentence; red at base; a guard that passes trivially if the fixture shows twoway draws every case) |

Each row's commit stages that row's file only (no commit stages a later row's red cases).

- Test: fixture stamped and complete -- `TestTheFixture::test_meta`, `::test_keys` (guard after 34-01).
- Test: `_dash_layer_series` substitutes `yvarlabel`/`xvarlabel` per series and `""` removes -- `TestVarlabels::test_series[case]` (red: KeyError-free but unchanged labels); axis default titles and legend keys follow, both modes -- `::test_axis_titles[mode]`, `::test_legend_keys[mode]` (red); without the options every corpus spec's series are unchanged -- `::test_unchanged_without_the_options` (guard).
- Test: prefix and suffix wrap the LabelSet text and not the tooltip, both modes, on scatter, bar, rscatter -- `TestPrefixSuffix::test_text[mode-type]` (red), `::test_the_tooltip_is_unchanged_by_prefix[mode]` (guard).
- Test: `msangle` names rotate; `bogus` answers per the fixture branch (noted when twoway's rc is 0; the `anglestyle` kind's refusal line in dash.ado read from source when rc≠0); `45` equals `forty_five` -- `TestMsangle::test_each_name[name]` (red), `::test_bogus_follows_the_fixture` (guard on the rc-0 branch, red on the refusal branch).
- Test: `lalign`/`mlalign` center silent, inside one note -- `TestAlignment::test_center_is_silent`, `::test_inside_is_noted_once` (red).
- Test: `label_style("p2")` returns the scheme's label colour/size; bar/rbar default clock 12, scatter 3 -- `TestLabelStyle::test_p2` (red: AttributeError), `TestBarDefault::test_bar_and_rbar_are_12[mode-type]` (red), `::test_scatter_stays_3[mode]` (guard).
- Test: the declared keys are in the JSON key list, the stylelist keys, the syntax, the sreturns (source read) -- `TestTheDeclarations::test_each_name` (red).
- Test: the rejected_options.json readers' expectation for `xvarlabel` moves from "rc 0 with note" to "rc 0 silent" -- in the existing reader file (flip), referenced here.

### Cases in cscripts

- `test_wp31_truth.cscript` U34-1..U34-7 (red; U34-5's `n45` half and U34-6's scatter half guards).
- `test_option_validation.cscript` U34-8, U34-9 (red), U34-10 (guard).

### Parity corpus (R8)

test/test_mode_parity.py under `# WP-31 S34`: `CORPUS` "yvarlabel and xvarlabel", "mlabel with prefix and suffix", "bar with mlabel (default 12)", "msangle(forty_five)"; `MOVE_CORPUS` "bar with mlabel, dropdown".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| varlabels on titles and keys | pytest test_varlabel_options.py `TestVarlabels`; cscript U34-1, U34-8 | `varlabel.*` | yes |
| prefix/suffix | pytest test_mlabel_prefix_suffix.py `TestPrefixSuffix`; cscript U34-2 | `prefix.*` | yes |
| alignment, mlabstyle, msangle names | pytest `TestAlignment` (test_mlabel_prefix_suffix.py), `TestLabelStyle`, `TestMsangle` (test_msangle_mlabstyle.py); cscript U34-3..5, U34-9 | `align.* mlabstyle.* msangle.*` | yes |
| bar default 12 | pytest test_mlabel_bar_default.py `TestBarDefault`; cscript U34-6 | `bardefault.*` | yes |
| C14 | cscript U34-7; pytest test_range_mlabel_rule.py `TestTheRule` | `c14.*` | n/a |
| Registries, help | test_unsupported_report_is_true.py, test_help_conformance.py, test_function_test_map.py | -- | -- |

**Acceptance criteria**
- **AC-34.1** For every `varlabel.*` record dash's titles and keys equal twoway's in both modes, silently.
- **AC-34.2** Prefix/suffix texts equal twoway's; tooltips unchanged.
- **AC-34.3** Every `align.* malign.* mlabstyle.* msangle.*` rc equals twoway's (`msangle.bogus`: refused when the fixture's rc≠0, else drawn unrotated with one note); `center` silent; `inside` noted once.
- **AC-34.4** bar/rbar default clock 12, scatter 3, both modes.
- **AC-34.5** Every `c14.*` rc and line equals twoway's.
- **AC-34.6** U34-1..U34-10 PASS; test_help_conformance.py and test_unsupported_report_is_true.py green; no SKIP.

## Tasks

**Commit boundary.** Five commits on `wp31-s34` (`$WT=.../dash-wt/wp31-s34`): 34-02 `Read yvarlabel() and xvarlabel() for axis titles and legend keys (WP-31 D8)` then `Declare and draw mlabprefix(), mlabsuffix() and lalign() (WP-31 C17)`; 34-03 `Rotate markers by anglestyle names and declare mlalign(), mwidth and mlabstyle() (WP-31 E3)` then `Default bar and rbar marker labels to 12 o'clock (WP-31 C15)`; 34-04 `Answer a range plot labelled by a plotted variable as twoway does (WP-31 C14)`. Bodies in BRIEF's forms; `Fixture: test/fixtures/varlabel_mlabel_truth.json (scripts/extract_varlabel_mlabel_truth.do)` on the D8 commit. Every GAPS3 Tracked line a closing task writes reads `commit pending` (DECISIONS A11; the merger's step k.3b fills the sha); each row's commit stages that row's test file and truth block only (A14).

<task type="auto" id="34-01">
  <name>Measure twoway and write failing tests</name>
  <files>scripts/extract_varlabel_mlabel_truth.do, test/fixtures/varlabel_mlabel_truth.json, test/test_varlabel_options.py</files>
  <action><![CDATA[
    Check the cut (`<scratch>/batch-11-base.txt`, branch `wp31-s34`); `mkdir -p <scratch>/s34/x`. Record `grep -c "MLAlign\|MWidth" dash.ado` and `grep -n '"mwidth"' dash_parse.mata` in `<scratch>/s34/prior.txt` (what S08/S03 declared). Create scripts/extract_varlabel_mlabel_truth.do per "Stata truth" (path-free head from scripts/extract_default_base_truth.do:1-60; SVG reading through scripts/svg_truth.py), run it through the slot, `git add -f test/fixtures/varlabel_mlabel_truth.json`. Write `<scratch>/s34/c14.txt`: the fixture's `c14.*` rc/line and the rule they imply (D-34.f). Create the five per-row test files of "TDD test stubs" (test/test_varlabel_options.py, test/test_mlabel_prefix_suffix.py, test/test_msangle_mlabstyle.py, test/test_mlabel_bar_default.py, test/test_range_mlabel_rule.py) with exactly their classes. Append the helpers `_u34_*` and ONLY the D8 block (U34-1) to test/test_wp31_truth.cscript above the marker (A14: the C17, E3, C15 and C14 blocks are appended by 34-02, 34-03 and 34-04), U34-8..U34-10 to test/test_option_validation.cscript before `// Summary`. Flip the pins found by `grep -rn "yvarlabel\|xvarlabel\|mlabprefix\|mlabsuffix\|lalign\|mlabstyle\|msangle(forty\|msangle(bogus\|mlabel(lo)" test/` and `grep -n "mlabposition\|\"3\"" test/test_marker_label_parity.py test/test_glyphs.py` (only nodes asserting today's behaviour named in Evidence), recording in `<scratch>/s34/34-flips.txt`. Run the five pytest files (`-rf > <scratch>/s34/34-01.log`) and both cscripts through the driver (`WP31_ONLY=S34`) on the unmodified tree; write `<scratch>/34-01-failure.txt` grouped by row. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/varlabel_mlabel_truth.json'));print(sorted(d['_meta']), sorted(d))"` prints the five `_meta` keys and `_meta align bardefault c14 malign mlabstyle mlalign msangle mwidth prefix varlabel`; `grep -c FAILED <scratch>/s34/34-01.log` is at least 10 and no FAILED line names TestTheFixture, test_unchanged_without_the_options or test_scatter_stays_3; `grep -c "U34-1 FAIL" <scratch>/s34/run_truth.log` prints 1 and `grep -c "U34-[2-7]"` prints 0 (only the D8 block exists yet); `grep -c "U34-[89] FAIL" <scratch>/s34/run_option_validation.log` prints 2 and `U34-10 PASS` 1; `grep -c SKIP` on both logs prints 0; `test -s <scratch>/s34/c14.txt`.]]></verify>
  <done>twoway's varlabel titles and keys, label prefixes, alignment and style refusals, anglestyle rotations, default label clocks and range-label answers were recorded, and every regression test and case was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="34-02">
  <name>Declare varlabels, prefix, suffix, lalign; commit D8 and C17</name>
  <files>dash.ado, dash_parse.mata, dash_render.py</files>
  <action><![CDATA[
    D8: make TR-34.1 for `YVARLabel XVARLabel` (syntax, sreturns, JSON keys, `yvarlabel` in `_dash_stylelist_keys`, `_dash_p_drops` check; no `_dash_option_rules` edit -- S32's, A15) and TR-34.2; test_unsupported_report_is_true.py LIVE_VALUES entries and count comment; a help definition entry for each (dash.sthlp, S34's Marker labels / Axis titles paragraphs: `grep -n "yvarformat" dash.sthlp` and add the varlabel entries beside the varformat ones). Flip the D8 nodes. Run `python3 -m pytest test/test_varlabel_options.py test/test_unsupported_report_is_true.py test/test_help_conformance.py -q -n0 -p no:cacheprovider -k "Varlabel or Declarations or unsupported or conformance"` and both cscripts (U34-1, U34-8). Close D8 (BUGS.md, GAPS3 Tracked `commit pending`, CHANGELOG `<!-- WP-31 D8 -->` → Results line); stage test/test_varlabel_options.py and the D8 block only among the tests; commit. C17: append the C17 truth block (U34-2, U34-3) above the marker; re-run test/test_mlabel_prefix_suffix.py and U34-2, U34-3, U34-9 against the new tree, append to the failure file; make TR-34.1 for `MLABPREfix MLABSUFFix LAlign` (+`MLAlign` only if prior.txt says 0), TR-34.3's prefix/suffix lines (the new `_mlab` column), TR-34.5 for `lalign` (and `mlalign` if declared here); the `lalign`/`mlalign` enum tokens are NOT added here -- S32's rules edit carries them (A15), so `lalign(bogus)` is refused only once batch 11 is merged (U34-9 is run against the merged tree by the merger; record it in the hand-back); LIVE_VALUES/ALIASES entries; help entries; write the headlabel finding into C17's BUGS.md Resolution ("headlabel is accepted on every pc and y3x type, yxyxview_parse:52,67 and y3xview_parse:57,72; dash's accept-and-name stands; S02 declares it"). Flip the C17 nodes. Run the same pytest selection plus test/test_mlabel_prefix_suffix.py and both cscripts. Close C17 (GAPS3 Tracked `commit pending`; CHANGELOG marker → Results line for prefix/suffix and a Changed-behaviour line for `lalign(bogus)` if newly refused); stage test/test_mlabel_prefix_suffix.py and the C17 block; commit.
  ]]></action>
  <verify><![CDATA[`grep -c "YVARLabel(string asis)  XVARLabel(string asis)" dash.ado` prints 1; `grep -c "MLABPREfix(string asis) MLABSUFFix(string asis)" dash.ado` prints 1; the pytest runs report 0 failed; `grep -c "U34-[123] PASS" <scratch>/s34/run_truth.log` prints 3; `grep -c "U34-8 PASS\|U34-10 PASS" <scratch>/s34/run_option_validation.log` prints 2 (U34-9 passes once S32's tokens are merged; its FAIL is named in the hand-back); `git log -2 --format=%s` shows `(WP-31 C17)` then `(WP-31 D8)`; `grep -c '<!-- WP-31 D8 -->\|<!-- WP-31 C17 -->' CHANGELOG.md` prints 0; `grep -c "D8 Tracked:\*\* Closed in WP-31.*commit pending\|C17 Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` prints 2; `git log -2 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>yvarlabel() and xvarlabel() titled axes and legend keys, prefix, suffix and lalign() were declared and drawn or named as twoway's measurements require, and D8 and C17 were closed in their own green commits.</done>
</task>

<task type="auto" id="34-03">
  <name>Rotate by anglestyle names, label styles, bar default; commit E3 and C15</name>
  <files>dash_render.py, dash.ado, test/function_test_map.py</files>
  <action><![CDATA[
    E3: append the E3 truth block (U34-4, U34-5) above the marker; re-run test/test_msangle_mlabstyle.py and U34-4, U34-5 against the tree 34-02 left; append to the failure file. Make TR-34.4 (msangle through `_dash_anglestyle_degrees`; the `msangle.bogus` branch: an `anglestyle` kind in `_dash_validate_value` with the measured line when the fixture's rc≠0, else the note only), TR-34.1/TR-34.3's `MLABSTyle` and `SchemeParser.label_style` (plus `MLAlign`/`MWidth` only where prior.txt says 0; if S03 declared `MWidth`, record "mwidth closed by S03 (C2)" in E3's Resolution; if S08 declared `MLAlign`, delete its pending line and move its PLOT_VALUES entry per TR-34.8), the `istyle`-kind rule for `mlabstyle` with the fixture's refusal text. function_test_map.py entry `SchemeParser.label_style` under `# WP-31 S34 (E3)`. Flip the E3 nodes. Run `python3 -m pytest test/test_msangle_mlabstyle.py test/test_glyphs.py test/test_marker_label_parity.py test/test_unsupported_report_is_true.py test/test_function_test_map.py -q -n0 -p no:cacheprovider` and both cscripts. Close E3 (BUGS.md, Tracked `commit pending`, CHANGELOG marker → Results line "msangle(forty_five) drew markers unrotated with a note; it rotates them 45 degrees" and Changed-behaviour lines for the newly refused `mlabstyle(bogus)`/`msangle(bogus)` if the fixture refuses them); stage test/test_msangle_mlabstyle.py and the E3 block; commit. C15: append the C15 truth block (U34-6); re-run test/test_mlabel_bar_default.py and U34-6; make TR-34.6; flip the C15 nodes; run the same selection plus test/test_mlabel_bar_default.py and the truth script; close C15 (Tracked `commit pending`; CHANGELOG marker → Results line "bar mpg weight, mlabel(make) placed labels at 3 o'clock; 12 now, as twoway"); stage test/test_mlabel_bar_default.py and the C15 block; commit.
  ]]></action>
  <verify><![CDATA[`grep -c "_dash_anglestyle_degrees(options\[\"msangle\"\])" dash_render.py` prints 1; `grep -c 'setdefault("mlabposition", "12")' dash_render.py` prints 3; `grep -c "def label_style" dash_render.py` prints 1; the pytest runs report 0 failed; `grep -c "U34-[1-6] PASS" <scratch>/s34/run_truth.log` prints 6; `git log -2 --format=%s` shows `(WP-31 C15)` then `(WP-31 E3)`; `grep -c '<!-- WP-31 E3 -->\|<!-- WP-31 C15 -->' CHANGELOG.md` prints 0.]]></verify>
  <done>Anglestyle names rotated markers, mlabstyle() styled labels from the scheme, mlalign()/mwidth were settled, bar and rbar labels defaulted to 12 o'clock, and E3 and C15 were closed in their own green commits.</done>
</task>

<task type="auto" id="34-04">
  <name>Answer labelled range plots as twoway; commit C14</name>
  <files>dash.ado, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[
    Append the C14 truth block (U34-7); re-run test/test_range_mlabel_rule.py and U34-7 against the tree 34-03 left; append to the failure file. Make TR-34.7 from `<scratch>/s34/c14.txt` (the measured condition, rc and sentence as literals; if twoway draws every case, make no code change and close C14 as measured false with the fixture as evidence). Append the parity cases of "TDD test stubs / Parity corpus". Flip the C14 nodes (test_twoway_option_parity.cscript:3578's `mlabel(lo)` case only if the fixture refuses it). dash.sthlp (R3): the Marker labels paragraph (:2763ff) gains the prefix/suffix, mlabstyle, bar default and anglestyle sentences and the range-label rule; the Unsupported list loses `mlalign()` if drawn/settled and gains nothing. Run `python3 -m pytest test/test_range_mlabel_rule.py test/test_varlabel_options.py test/test_mlabel_prefix_suffix.py test/test_msangle_mlabstyle.py test/test_mlabel_bar_default.py test/test_mode_parity.py test/test_help_conformance.py test/test_help_claims_5.py test/test_tracking_documents.py -q -n0 -p no:cacheprovider -k "not Move or S34"` and the three cscripts (truth `WP31_ONLY=S34`, test_option_validation.cscript, test_twoway_option_parity.cscript). Close C14 (BUGS.md, Tracked `commit pending`, CHANGELOG marker → Changed-behaviour line naming the refused form and twoway's words, or a Results line "measured: twoway draws it; no change"); stage test/test_range_mlabel_rule.py and the C14 block; commit.
  ]]></action>
  <verify><![CDATA[`grep -c "U34-[1-7] PASS" <scratch>/s34/run_truth.log` prints 7 and `grep -c " FAIL\|SKIP"` prints 0; the two area-script logs end with their all-passed lines; the pytest run reports 0 failed; `git log -1 --format=%s` ends `(WP-31 C14)`; `grep -c '<!-- WP-31 C14 -->' CHANGELOG.md` prints 0; `grep -c "Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` counts the five S34 rows among its lines (no `commit <sha>` form anywhere); `git log -5 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>A range plot labelled by one of its plotted variables was answered as twoway answers it, the help described every option this section drew, and C14 was closed in one green commit on wp31-s34.</done>
</task>

## Section completion criteria

- `yvarlabel()`/`xvarlabel()` title axes and keys silently in both modes; `("")` removes.
- prefix/suffix drawn; `lalign`/`mlalign` center silent, inside/outside noted once, bad words refused as twoway; `mlabstyle(p#)` styled; `msangle(name)` rotated.
- bar/rbar labels default 12; scatter 3.
- C14 answered as measured.
- `varlabel_mlabel_truth.json` stamped and named; U34-1..U34-10 PASS (U34-9 on the merged batch-11 tree); flips recorded; five green commits, each staging its own row's test file and truth block; five entries closed with `commit pending` Tracked lines.

## Notes

- **Stylelist per-y pick:** the spec carries the k-th element of a stylelist key for y number k (`_dash_stylelist_pick`, dash.ado:4470ff). `yvarlabel("A" "B")` on `scatter mpg price weight` yields two plot records with `"yvarlabel":"A"` and `"B"`. Quoted elements keep their quotes until the writer strips them (`string asis`, comment dash.ado:1241-1247): confirm the written value is the bare text.
- **S41 (batch 14) edits `_apply_line_opts`** for colour/width edges; S34's `lalign` read is five lines at the end of that applier -- S41 must keep them.
- **For S32 (batch 11):** add `lalign=enum,center|inside|outside  mlalign=enum,center|inside|outside` to `_dash_option_rules` beside the plot-level `l*`/`ml*` tokens (A15); S34's U34-9 and `TestAlignment::test_bogus_is_refused` read them.
- **Decision for ratification:** D-34.c (inside/outside named, not drawn: Bokeh has no stroke alignment); D-34.d (mlabstyle through the scheme's labelstyle stubs; the shipped translation may lack `labelstyle` entries -- then `label_style` reads `color p#label` and `gsize label` directly, and S44's resolver may replace it).
- **python_exec hazard**; **cscript drops globals**: `_u34_` helpers answer through globals set in the block.
- **Shared files.** R1: the five S34 row blocks (A14); U34-8..10 in test_option_validation.cscript; one flip in test_twoway_option_parity.cscript. R2: none (a `SchemeParser` method travels with its class). R3: Marker labels paragraph, the varformat/varlabel entries, the Unsupported list's `mlalign()` line. R4: five markers. R5: five entries. R6: `_dash_rep_unique` gains `mwidth` only if S34 declares it; `version 19` unchanged programs. R7: one fixture. R8: five corpus entries. R9: flips. R10: the declared counts. R12: S34 is batch 11's editor of `_apply_marker_opts`, `_apply_mlabel_opts`, `_apply_line_opts` (five lines) and `_dash_validate_value`'s `anglestyle` kind (only on the fixture's refusal branch); S32/S33 edit none of these. `_dash_option_rules` is S32's: S34's two enum tokens ride S32's rules edit (A15).
