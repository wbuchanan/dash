# Codebase research: axes, text, legend, colour (B1, B2, B3, B5, B6, B7, G16, X2, D1)

> Researcher: codebase agent A, 2026-09-25, at HEAD `91d97be` on `s3-bugs`. All anchors checked on the current tree.
> Side effect noted by the agent: one probe imported dash_render without `-B`, which may have refreshed a `.pyc` in `__pycache__/`.

## Summary

**Current anchors.** GAPS2's line numbers mostly still hold, drifting by a few lines at most:
- **B1:** `_dash_parse_axis_label_opt` is at dash_render.py:16041-16074. Its only caller is `_dash_parse_axis_spec` (16605-16735). That parser feeds xlabel/ylabel, xtick/ytick and xlabel2/ylabel2.
- **B2:** `_dash_apply_scale_ranges` (19017-19065) sets an exact `Range1d`. `_dash_finish_secondary_axes` (17158-17163) narrows the second axes the same way.
- **B3/B6/B7:** `_TEXTBOX_SUBOPTS` is at 2438-2445, `_dash_axis_labels` at 16036-16037, `_dash_add_secondary_axes` at 17027-17028.
- **B5:** in `_dash_apply_legend`, `order()` is at 15847-15852 and `label()` at 15929-15939.
- **X2:** `_apply_colorvar` spans 6338-6655.
- **D1:** `_parse_lines` takes the value from 3988-3996.
- **G16:** `_dash_build_hover` at 19839.

**Surprises (where the code or data differ from what GAPS2 implies):**
1. dash.ado already expands numlists (`_dash_validate_value`, kind `numlist`, dash.ado:2122-2148). The graph-option check loops at 2463 and 4705 can write a normalised value back, so B1's ado step can reuse it.
2. Value labels already reach Python in both modes. Only `_dash_build_hover` and `_dash_apply_axis_options` lack a value-label parameter.
3. `axis_truth.json` already holds twoway's measured y extents for `range(0)`, `range(60)`, `range(20 30)` and `range(0 50)`. No test reads them.
4. The only committed `.Graph` extent reading gives `y_scale` [12, 41], the data range, not the drawn extent. Reading `.Graph` for B2 may therefore not give what the plan expects.
5. The saved renderer limits its automatic axis ranges to the primary source's renderers (22314-22330); the served app has no such step. The parity profile cannot see this.
6. GAPS2 X2's "continuous map 6424-6446" is stale: the continuous path is now 6599-6629.
7. Stata's rule grammar allows a rule followed by a labelled numlist. dash drops `#5` from `xlabel(#5 50 "fifty")`, which GAPS2 does not list.
8. The tick formatter keys labels as `"2000.0"`, but JavaScript's `String(tick)` gives `"2000"`. Labels on whole-number ticks only appear because of `major_label_overrides`.
9. dash.ado merges repeated titles into one before Python sees them. So `ytitle("a") ytitle("b", axis(2))` arrives as a single title, which affects B3's `axis(2)` routing.
10. Existing tests that pin the old behaviour and will flip:
    - `test_suboption_warnings.py` expects `xlabel(, valuelabel)` to be named in the note.
    - `test_help_claims_7.cscript` HC7-02 expects `colorlevels()` to be named.
    - `test_graph_options.py::test_single_quoted_label` accepts `'One'` as a label, which Stata does not.
11. Stata's scheme reader takes the third token as the value; `scripts/extract_scheme_truth.py:146-262,297` already does this.
12. The 129 third-party schemes are machine-local in `~/Library/Application Support/Stata/ado/plus/s/`. 127 use quoted RGB.
13. The shipped `sttrans.scheme` was rewritten as `#1a476f%20`, which is why sttrans works today.

**Reusable helpers:** `_textbox_string_end`/`_textbox_lines`, `_textbox_split_point`, `_dash_report_suboptions` (the "named in the note" mechanism), `_dash_warn_once`, `_dash_by_tokens`/`_dash_subopt_name`, `_dash_date_axis_spec`/`_dash_axis_positions`, `_dash_secondary_values`, `_dash_place_count_ticks`, `_dash_count_axes`, `GlyphMapper._mlabel_value_labels`/`_mlabel_value_text`, the explicit tick-label path (16783-16798), the invisible legend-swatch pattern (`_DASH_SWATCH_PREFIX`), and `_dash_imm_next`/`_dash_rep_toks` in Mata.

Any new Python helper must be added to the served app's copy lists (24326-24428 and 24466-24687) and to `test/function_test_map.py`.

---

## 0. Cross-cutting mechanisms

### 0.1 How the served app gets its code
`ServerAppBuilder` does not transcribe code. It copies module functions and constants into the app source with `inspect.getsource` (dash_render.py:24298-24700):
- **Constants list:** 24326-24428. Compiled regexes are written as `re.compile(pattern, flags)` (24438-24444). `_TEXTBOX_SUBOPT_RE` is in the list; `_TEXTBOX_SUBOPTS` (the tuple) is not.
- **Function list:** 24466-24687. It already includes `_parse_textbox_opt`, `_textbox_split_point`, `_textbox_lines`, `_textbox_string_end`, `_textbox_size`, `_textbox_color`, `_dash_textbox`, `_dash_style_axis_titles`, `_dash_axis_labels`, `_dash_parse_axis_label_opt`, `_dash_parse_axis_spec`, `_dash_apply_axis_spec`, `_dash_apply_axis_options`, `_dash_add_secondary_axes`, `_dash_finish_secondary_axes`, `_dash_keep_primary_ranges`, `_dash_finish_count_ticks`, `_dash_count_axes`, `_dash_place_count_ticks`, `_dash_common_count_ticks`, `_parse_scale_range`, `_dash_scale_spec`, `_dash_apply_scale_ranges`, `_dash_legend_key`, `_dash_legend_entries`, `_dash_legend_parts`, `_dash_legend_arg`, `_dash_apply_legend`, `_dash_build_hover`, `_dash_hover_row`, `_dash_hover_layer_vars`, `_dash_report_suboptions`, `_dash_subopt_name`, `_dash_legend_unsupported`, `_dash_date_axis_spec`, `_dash_axis_positions`, `_dash_note_not_dates`.
- **Classes:** `OptionTranslator`, `SchemeParser` and `GlyphMapper` are copied whole (24698-24700). The scheme travels as `_SCHEME_PROPS` (24708), a dict parsed at build time, so D1's parser change reaches the served app through the props with no template edit.
- **Rule:** every new module-level helper or table must be added to these lists. `test_adversarial_matrix.py::TestAxisLabelBounds::test_both_modes_share_the_bound` (about line 1597) shows the pattern for asserting that the served copy exists.

### 0.2 Figure-building order in the two renderers

| Step | Saved `DashRenderer._make_figure_body` (21931-22366) | Served template (source strings) |
|---|---|---|
| axis titles | `_dash_axis_labels` 21951 | 26143 |
| scale spec | `_dash_scale_spec` x/y 21970-21973 | 26170-26171 |
| date/log axis type | `fig_kwargs[...] = "datetime"/"log"` 22015-22022 | 26192-26195 |
| figure made | `bokeh_figure` 22024; `_dash_mark_date_axes` 22027 | 26196-26197 |
| scheme | `self.scheme.apply_to_figure` 22037 | `_DASH_SCHEME.apply_to_figure` 26204 |
| title/axis-title styling | `_dash_figure_title`, `_dash_style_axis_titles` 22040-22041 | 26210-26211 (after the second axes) |
| second axes | `_dash_add_secondary_axes` 22096 (after the styling) | 26207 (before the styling) |
| `range()`/`reverse` | `_dash_apply_scale_ranges` 22102 | 26256 |
| note/caption/subtitle | `_dash_text_annotations` 22110 | 26259 |
| xlabel/xtick | `_dash_apply_axis_options` 22115 | 26266 |
| layer loop | 22132-22303 | 26277-26393 |
| finish second axes | 22307 | 26399 |
| legend | `self._rebuild_legend` 22311, which calls `_dash_apply_legend` (21799) | `_dash_apply_legend` 26435 |
| limit ranges to primary-source renderers | **22314-22330, saved only** | **absent** |
| `_dash_keep_primary_ranges` | 22333 | 26403 |
| `_dash_finish_count_ticks` | 22335 | 26405 |
| hover | `_dash_build_hover` 22348 | 26451 |
| by() common ticks | `_dash_common_count_ticks` 23318 | 26590 |

Loaders: `_dash_lone_second_axes(spec)` (1639-1702) runs in both, at 21031 (saved) and 24252 (served), before drawing. It turns `ytitle2`/`ylabel2`/`yscale2` into `ytitle`/`ylabel`/`yscale` when every layer is on axis 2.

### 0.3 How options that aren't drawn get named in the note
- **Python sub-options:** `_dash_report_suboptions(option, tokens, seen, key)` (18813-18830):
  ```python
  if seen is not None:
      mark = (key, option, tuple(toks))
      if mark in seen:
          return
      seen.add(mark)
  warnings.warn("dash: %s() sub-option(s) not implemented and ignored: %s"
                % (option, " ".join(toks)), UserWarning, stacklevel=2)
  ```
  The `seen` set is `self._reported_subopts` in the saved renderer (24090) and `_reported_subopts = set()` in the served template (25967). The key is the graph name. Tokens come from `_dash_by_tokens(...)` and names from `_dash_subopt_name(tok)` (18833).
- **One-off notes:** `_dash_warn_once(key, message)` (12377) uses the global `_DASH_NOTED`. `_dash_style_note(option, value, what, using)` (12385) reports an unknown style value.
- **ado level:** undeclared options go through `*` into `_unknown`. Declared-but-pending options go into `_dash_pending` (graph parser: dash.ado:768-797; plot parser has its own list). `_dash_report_ignored` (dash.ado:4372-4419) prints "dash: ignoring unsupported option(s): …". `test/test_unsupported_report_is_true.py` reads the pending blocks and fails if a listed option actually changes the output.
- **DISCOVERY Q22:** once an option is honoured it must print nothing. Only options still not drawn are named.

### 0.4 Test infrastructure to place new tests beside
- **Rendering both modes:**
  - `test_natscale_axes.py` `_figures(mode, tmp_path, df, plots, go, formats)` (312-339), `_MODES` parametrisation, `_axis`/`_ticks` helpers.
  - `test_textbox_multiline.py` `_both_modes(tmp_path, graph_options)` (520-552) with `_drawn(fig)` (502-517), which returns title, labels, xtitle and ytitle from `xaxis[0]`/`yaxis[0]`.
  - `test_dual_axis.py` `_lone_figure(mode, plots, graph_opts)` (311-335).
  - `test_suboption_warnings.py` `_both(bo, go, plots)` (33-37), built on `test_mode_parity._standalone`/`_served`.
  - `test_mode_parity.py` `_spec` (162-189), `_write` (199-207, uses `make_data_json(_DF, _VALUE_LABELS, _LABEL_NAMES)`), `_standalone` (220), `_served` (226-249), `_axes(fig)` profile (580-609, records ranges only when start/end are numbers, plus ticks and labels), `CORPUS` of `_case(...)` entries (940 onward).
  - `ALLOWED` (105-139) has three entries: "aggregate layers recompute live", "linked graphs share one source", "layout(bs) is standalone markup". None bears on these gaps.
- **Data builders:** `conftest.make_data_json(df, value_labels, value_label_names)` (test/conftest.py:425-463) writes `valueLabels`/`valueLabelNames`. `make_spec`, `make_dr` live there too.
- **Function coverage guard:** `test/function_test_map.py`, enforced by `test_function_test_map.py`, must name a test for every new function. Stata programs map in `test/program_coverage_map.py`.
- **Stata truth fixtures:** `scripts/extract_axis_truth.do` registers probes with `zp id group dataset body opts` (106-118), exports SVG and `.gph` (400-428), and writes `test/fixtures/axis_truth.json`. Each probe has `all_text_elements`, `x_axis`/`y_axis` with `mapping.axis_low`/`axis_high`, `gridline_px`, `anchorless_texts`, `plotregion_px`. `test_axis_options.py` loads it through the `truth()` fixture (40-47).
- **cscript helpers:** `test/cert_helpers.do` has `cert_file_has`, `cert_log_has`, `cert_file_count` (Mata-based file search). No SVG helper exists yet; DISCOVERY Q14 plans one as a new shared piece.

---

## B1. Axis-label rules: quoted numeric text, multi-line labels, numlist forms

### Code the fix must touch
- **`_dash_parse_axis_label_opt`** (dash_render.py:16041-16074). It flattens every token, and treats single quotes as delimiters, which Stata does not:
  ```python
  tokens = re.findall(r'"([^"]*)"'  # double-quoted label
                      r"|'([^']*)'"  # single-quoted label
                      r"|([^\s,\"']+)",  # bare token (number or keyword)
                      str(raw or ""))
  flat = [dq or sq or bare for dq, sq, bare in tokens]
  ...
          float(next_tok)
      except ValueError:
          labels[str(val)] = next_tok
  ```
- **`_dash_parse_axis_spec`** (16605-16735):
  - honoured sub-options: 16635 `("format","labsize","angle","grid","nogrid")`; everything else goes to `unsupported`
  - rules: `none`/`minmax` fullmatch (16666-16671); `#N` fullmatch only (16672-16680)
  - `a(b)c` regex expansion with the `_MAX_AXIS_TICKS` pre-count (16686-16714)
  - then `_dash_parse_axis_label_opt(rest)` (16716) and naming of stray bare words (16720-16730)
- **`_MAX_AXIS_TICKS = 2000`** (16081). It is copied into the served app.
- **Callers of `_dash_parse_axis_spec`:**
  - `_dash_apply_axis_options` 16983 (xlabel/ylabel), called at 22115 and 26266
  - `_dash_apply_tick_option` 16879 (xtick/ytick)
  - `_dash_finish_secondary_axes` 17168 (xlabel2/ylabel2), called at 22307 and 26399
  - `_dash_date_axis_spec` (16931-16953) turns ticks and label keys into epoch ms on date axes
- **Verified today:**
  - `1 "2019" 2 "2020" 3 "2021"` gives ticks [1, 2, 3, 2019, 2020, 2021], no labels, no note
  - `10 20 to 40` gives ticks [10, 20, 40] with the label `{"20.0": "to"}`
  - `1/5` gives the default ticks, with `1/5` named
  - `1 "a" "b" 2 `"c "q" d"'` gives labels `{1: "a", 2: "`"}`
  - also: `#5 50 "fifty"` gives explicit [50] only. Stata allows `[rule] [numlist ["label" …]]` (axis_label_options.sthlp:47-55), so the `#5` is lost. GAPS2 does not list this.

### Does dash.ado already expand numlists? Yes
- **`_dash_validate_value`, kind `numlist`** (dash.ado:2122-2148):
  ```stata
  if !strpos(scalar(`V'), char(34)) {
      capture numlist `"`macval(value)'"'
      local _nlrc = _rc
  }
  ...
          local norm `"`r(numlist)'"'
  ```
  Used by `colorcuts=numlist,1` and `range=numlist,2,2` (plot rules, dash.ado:1869). dash.sthlp:592-593 documents `colorcuts(1(1)5)` reaching the renderer as `1 2 3 4 5`.
- **Graph-level rules** are in `_dash_option_rules` (dash.ado:1853-1929): `local graph xsize=… ysize=… aspectratio=… hover=varlist by=byvarlist scheme=scheme` (1910-1912). They are applied in two places, each writing the normalised value back:
  - per segment in `_dash_validate_opts` (2463-2479): `sreturn local g_`o' "`_dash_vnorm'"`
  - per graph in `_dash_plot` (4705-4713): `local g_`_vopt' : copy local _dash_vnorm`
- **Mata token readers to reuse:**
  - `_dash_imm_next` (dash_parse.mata:1207): gettoken-style reading with quotes, used by scatteri
  - `_dash_imm_number` (1400) and `_dash_json_number` (1384)
  - `_dash_rep_toks(s, commas)` (dash_parse.mata:4064): splits on blanks outside quotes and parentheses
- **Bound before calling `numlist`:** Python must still enforce its bound on hand-written specs; `TestAxisLabelBounds` requires `0(0.000001)1000000` to keep the default ticks with a note, in both modes. Also, dash.sthlp says twoway draws such rules without error, so the ado step must not refuse them.

### How xlabel reaches the spec
- Declared `XLabel(string asis)`, `YLabel`, `XLABEL2`, `YLABEL2`, `XTICk`, `YTICk`, `XMTick`, `YMTick`, `XMLabel`, `YMLabel` in `_dash_parse_graph_opts` (dash.ado:699-724) and in `_dash_parse_plot_opts` (899-958, returned as `g_*` at 1205-1262).
- Aliases `xla2`/`yla2` fold into `xlabel2`/`ylabel2` (742-747, 999).
- Repeated copies merge in Mata category "L" (`_dash_rep_cat`, dash_parse.mata:4251; `_dash_rep_merge` 4826-4855; `add` joins bodies).
- JSON is written in `_dash_plot` (dash.ado:4942-4955): `"`gk'":"<json-escaped raw text>"`. The spec keys are `graph_options.xlabel`, `ylabel`, `xlabel2`, `ylabel2`, `xtick`, `ytick`, `xmtick`, `ymtick`, `xmlabel`, `ymlabel`. Values are the raw text with the user's quotes kept.
- The graph-key `foreach` list appears seven times (dash.ado:3951, 4481, 4512, 4602, 4656, 4687, 4942). Any new graph key must go in all of them.

### Reusable
- `_textbox_string_end(text, i)` (2448-2481): plain and compound strings, nesting, unclosed-to-end.
- `_textbox_lines(text)` (2528-2574).
- `_dash_date_axis_spec` for date axes.
- `_fmt_num` (16956).
- The explicit-label applier (16783-16798):
  ```python
  axis_obj.ticker = FixedTicker(ticks=spec["ticks"])
  if spec["labels"]:
      _labels = {str(k): str(v) for k, v in spec["labels"].items()}
      axis_obj.formatter = CustomJSTickFormatter(
          args={"labels": json.dumps(_labels)},
          code="const m = JSON.parse(labels); "
               "return m[String(tick)] || String(tick);")
      axis_obj.major_label_overrides = {
          float(k): v for k, v in spec["labels"].items()}
  ```
  The keys are `str(float)` (`"2000.0"`) while JavaScript's `String(2000)` is `"2000"`, so on whole-number ticks the overrides do the work, not the formatter map.

### Existing tests
- `test/test_axis_options.py::TestAxisLabelGrammar` (115-235): explicit numlist, value/label pairs, increment forms, minmax, none, `#N`, format, labsize, angle, grid, ylabel, xtick, date axis.
- `test/test_graph_options.py::TestParseAxisLabelOpt` (384-447). `test_single_quoted_label` (436-441) pins `'One'` as a label, which is not Stata; B1 will flip it.
- `test/test_adversarial_matrix.py::TestAxisLabelBounds` (1542-1611) and `TestAxisLabelInjection` (1614 onward).
- `test/test_bug_regressions.py` (51-78, 186 `TestYlabelCountWithAGridIsHonoured`).
- `test/test_mode_parity.py` CORPUS cases 1168-1194.
- `test/test_suboption_warnings.py` SUBOPTIONS and `TestTheHonouredOnesStayQuiet`.
- Fixture `axis_truth.json` probes `a_list`, `a_pairs` (`xlabel(2000 "low" 4000 "high")`), `a_incr`, `a_incr_inside`, `a_hash*` (extract_axis_truth.do:122-165).

---

## B2. Tick and label values don't widen the axis; `range()` narrows or inverts it

### Code the fix must touch
- **`_dash_apply_scale_ranges`** (19017-19065). It replaces the range with an exact `Range1d` before any layer is drawn:
  ```python
  new_lo = lo if lo is not None else cur_lo
  new_hi = hi if hi is not None else cur_hi
  if new_lo is not None and new_hi is not None:
      setattr(fig, attr, Range1d(float(new_lo), float(new_hi)))
  for spec, attr in ((xspec, "x_range"), (yspec, "y_range")):
      if spec.get("reverse"):
          getattr(fig, attr).flipped = True
  ```
  Date bounds are converted with `_dash_axis_positions` and `_dash_note_not_dates` (19032-19046). Called at 22102 and 26256.
- **`_parse_scale_range`** (2409-2435) matches only `\brange\s*\(`. Stata's abbreviation is `r:ange` (axis_scale_options.sthlp:51), so `r(0 100)` is named by `_dash_scale_spec` and dropped. Only the first two tokens are read; there is no missing-value handling.
- **`_dash_scale_spec`** (19001-19014), honoured set `_DASH_SCALE_SUBOPTS = {"log","reverse","range"}` (18998). `rev` is not recognised either.
- **Second axes:** `_dash_finish_secondary_axes` (17095-17178) fits to the drawn values with a 5% pad (log-space on log axes), then narrows exactly:
  ```python
  if want_lo is not None:
      rng.start = float(want_lo)
  if want_hi is not None:
      rng.end = float(want_hi)
  if "reverse" in names:
      rng.start, rng.end = rng.end, rng.start
  ```
  Honoured set `_DASH_SCALE2_SUBOPTS` (17037).
- **Explicit ticks** only set `FixedTicker` (16783-16784); `minmax` sets `FixedTicker([min, max])` (16769-16775). xtick positions travel as `CustomJSTicker(args={"extra": [...]})` (16893-16917).
- **How log and date axes are made:** chosen once, before the figure, through `fig_kwargs["x_axis_type"] = "datetime"` or `"log"` (22015-22022; served 26192-26195). A date axis's positions are epoch ms, and the unit is found with `_dash_axis_date_kind(fig, "x")` (set by `_dash_mark_date_axes`). The second axis is `LogAxis` when `xscale2`/`yscale2` has `log` (17025-17029).
- **`norescale`** is not parsed anywhere (dash.ado, dash_parse.mata, dash_render.py, dash.sthlp). `_dash_parse_axis_spec(", norescale")` puts it in `unsupported`, so it is named.

### The place to add the hull step, and helpers to reuse
- **`_dash_finish_count_ticks(fig)`** (17334-17352) runs after the layers, in both modes. `_dash_count_axes(fig)` (17210-17273) collects per-axis entries (axis, ticker, range, kind of None/"log"/date, and lo/hi from `_dash_secondary_values`).
- **`_dash_place_count_ticks`** (17276-17331) already widens a range to reach its outermost ticks, with Bokeh's 5% pad model:
  ```python
  if isinstance(rng, DataRange1d):
      if getattr(rng, "flipped", False):
          return
      if common:
          rng.start, rng.end = float(min(t_lo, d_lo)), float(max(t_hi, d_hi))
          return
      if t_lo < d_lo:
          rng.start = t_lo
  ```
- **`_dash_secondary_values(fig, range_attr, name)`** (17040-17092) returns the finite drawn values on a range, through each renderer's view, skipping the colour-key swatches.
- **`_dash_keep_primary_ranges`** (17181-17207).
- **By-panel common scale:** `_dash_common_count_ticks` (17355-17377).
- **Divergence to handle:** the saved renderer limits `DataRange1d.renderers` to primary-source renderers (22314-22330: "Computed-glyph renderers … use separate ColumnDataSources"). The served template has no such block (no `range.renderers =` outside 17207 and 22328-22330). `test_mode_parity._axes` records range start/end only when they are numbers, so it cannot see this.

### Truth already on disk
`test/fixtures/axis_truth.json` → `probes[id].y_axis.mapping.axis_low`/`axis_high` (SVG-fitted drawn extent), from extract_axis_truth.do:167-176. No test reads these yet:

| Probe | Option | axis_low | axis_high |
|---|---|---|---|
| `b_default` | none | 9.12 | 41.88 |
| `b_range_0` | `yscale(range(0))` | −1.16 | 42.16 |
| `b_range_60` | `yscale(range(60))` | 8.58 | 61.42 |
| `b_range_narrow` | `yscale(range(20 30))` | 9.12 | 41.88 (identical to the default: never narrowed) |
| `b_range_0_50` | `yscale(range(0 50))` | −1.42 | 51.42 |

`natscale_axes_truth.json._meta` documents the `.Graph` reading (`.Graph.graphs[k].yaxis1.plotregion.yscale.min/max`). Its by() record gives `y_scale` [12, 41], the data extremes, for `ylabel(#5)` whose ticks are 10(10)40. So the `.Graph` scale property may be the data range, not the drawn extent, which matters for B2's step 4. No script in `scripts/` produced that fixture.

### Existing tests
- `test_axis_options.py::TestAxisScale` (237-271). It currently pins exact narrowing: `range(0 50)` gives start 0 and end 50, and `range(0)` gives start 0.
- `test_graph_options.py::TestXscaleYscaleReverse` (the function map's entry for `_dash_apply_scale_ranges`).
- `test_dual_axis.py::TestSecondaryAxisSetup`/`TestSecondaryAxisOptions` (100-217).
- `test_natscale_axes.py` both-mode classes (360-450).
- `test_mode_parity` case "xscale(range()) and yscale with an unimplemented sub-option" (1163).

---

## B3. Textbox sub-option abbreviations drawn as text

### Code the fix must touch
- **`_TEXTBOX_SUBOPTS`** and the split regex (2438-2445). Full names only, and `bcolor`, `lstyle`, `lalign`, `prefix`, `suffix`, `axis` are missing:
  ```python
  _TEXTBOX_SUBOPTS = (
      "size", "color", "colour", "position", "pos", "span", "box", "nobox",
      "justification", "just", "alignment", "margin", "linegap", "bexpand",
      "bmargin", "fcolor", "lcolor", "lwidth", "lpattern", "orientation",
      "ring", "placement", "width", "height", "tstyle", "style",
  )
  _TEXTBOX_SUBOPT_RE = re.compile(
      r",\s*(?=(?:" + "|".join(_TEXTBOX_SUBOPTS) + r")\b)", re.I)
  ```
- **`_textbox_split_point`** (2484-2525) splits only at a comma followed by a match of `_TEXTBOX_SUBOPT_RE`.
- **`_parse_textbox_opt`** (2614-2682). Sub-option names are kept exactly as written (lower-cased), so `c(red)` becomes `{"c": "red"}`:
  ```python
  scan = tail[:tail.rfind(")") + 1]
  for m2 in re.finditer(r"\b([A-Za-z_]+)\s*\(([^)]*)\)", scan):
      opts[m2.group(1).lower()] = m2.group(2).strip()
  for flag in ("span", "box", "nobox"):
  ```
  Verified: `_parse_textbox_opt('"T", c(red)')` returns `('T\n,\nc(red)', {})`, and `'"Volume", axis(2)'` returns `('Volume\n,\naxis(2)', {})`.
- **`_textbox_color`** reads `color`/`colour` (2597-2611). **`_textbox_size`** reads `size` (2577-2594). Both need names normalised first.
- **`_dash_textbox`** (18861-18878) names every token not in `_DASH_TEXTBOX_HONOURED = {"size","color","colour"}` (18858), compared as written, so an abbreviation would be named even once honoured.
- **Callers of `_parse_textbox_opt`:** 18870 (`_dash_textbox`), 18916 (`_dash_style_axis_titles`), 21978 (saved figure title), template 26149 (served title).
- **Callers of `_dash_textbox`:** 16034-16035 (`_dash_axis_labels`), 18889 (`_dash_figure_title`), 18968 (`_dash_text_annotations`: note, caption, subtitle).
- **`axis(2)` routing:** nothing reads `axis(#)` today (B15). Two places could do it:
  - Python: a spec rewrite beside `_dash_lone_second_axes` (1639), which runs in both loaders (21031, 24252). It must run before the lone-axis rewrite, which moves `ytitle2` into `ytitle`.
  - dash.ado: the Mata repeat merge treats every copy of `ytitle` as one option (category "T", `_dash_rep_merge` dash_parse.mata:4826-4855). The body of the last copy wins and sub-options merge, so `ytitle("a") ytitle("b", axis(2))` reaches the spec as one `ytitle` of `"b", axis(2)`. Routing `axis(2)` copies before the merge (`_dash_opts_repeats` / `_dash_rep_reduce`) is the only faithful place.

### Stata's table: spelling and minimum abbreviation
From textbox_options.sthlp:41-77, title_options.sthlp:56-66 and axis_title_options.sthlp:54-63:

| Sub-option | Minimum | Sub-option | Minimum |
|---|---|---|---|
| tstyle | tsty | bcolor | bc |
| orientation | orient | fcolor | fc |
| size | si | lstyle | ls |
| color | c | lpattern | lp |
| justification | j | lwidth | lw |
| alignment | al | lcolor | lc |
| margin | m | lalign | la |
| linegap, width, height | full | bmargin | bm |
| box, nobox | full | bexpand | bex |
| placement | place | position (titles) | pos |
| ring, span, prefix, suffix | full | axis(#) (axis titles, 1-9) | full |

Two entries in dash's tuple are not in Stata's help: `colour` and `style`.

### Existing tests
- `test_textbox_multiline.py`: `TestParseTextboxOpt` (97), `TestCommaInsideTheUsersText` (138), `TestMultilineReachesTheDocument` (184), `TestTheTextIsReadAsStataReadsIt` (394), `TestTextboxSplitPoint` (431), `TestTextboxLines` (456), `TestTextboxStringEnd` (475), `TestBothModesDrawTheTextAsTyped` (569, with `_both_modes`), `TestTextboxAdversarial` (614).
- `test_suboption_warnings.py`: SUBOPTIONS ("xtitle orientation", "ytitle size and justification"), `TestTheHonouredOnesStayQuiet` (100-119), `TestAxisTitlesSplitTheirSuboptions` (121-143).
- `test_axis_options.py::TestTitleTextFidelity` (429-521).
- cscript: `test_json_escaping.cscript` JSE-46 (1833-2016).

---

## B5. `legend` `order()` text and `label()`-after-`order()` applied to the wrong keys

### Code the fix must touch: `_dash_apply_legend` (15780-15983)
- **Step 1:** keys are rebuilt in place on the mapper's legend. It returns early if `fig.legend` is empty (15819-15822). Items are built at 15834-15841:
  ```python
  items = [LegendItem(label={"value": lbl}, renderers=rends)
           for lbl, rends in _dash_legend_entries(
               live, var_labels or {}, default_level)]
  ```
- **Step 2, `order()`:** numbers only, applied to positions:
  ```python
  _order = _dash_legend_arg(_calls, ("order",))
  if _order is not None and legend is not None:
      wanted = [int(t) for t in re.findall(r"\d+", _order)]
      current = list(legend.items)
      legend.items = [current[i - 1] for i in wanted
                      if 1 <= i <= len(current)]
  ```
- **Step 5, `label()`:** applied by displayed position after the reorder (15929-15939):
  ```python
  lm = _DASH_LEGEND_LABEL_RE.fullmatch(_arg)
  idx = int(lm.group(1)) - 1
  if 0 <= idx < len(legend.items):
      legend.items[idx].label = {
          "value": "\n".join(_textbox_lines(lm.group(2)))}
  ```
- **`lastlabel`:** not in `_DASH_LEGEND_SUBOPTS` (18839-18841), so `_dash_legend_unsupported` (18850) names it.
- **Parsing:** `_dash_legend_parts(legend_opt)` (15682-15703) gives bare words plus `(name, arg)` calls through `_dash_by_tokens`. `_dash_legend_arg(calls, names, pattern)` (15706-15717) returns the first match. `_DASH_LEGEND_LABEL_RE = re.compile(r"\s*(\d{1,6})(\s.*)", re.S)` (18847).
- **Key list:** `_dash_legend_entries(plot_renderers, var_labels, default_level)` (19754-19792) makes one key per layer and two for a CI type (band `"{lvl:g}% CI"`, then "Fitted values"). It skips a layer whose renderers are empty or all swatches (19772-19774), so position-based numbering can drift from Stata's plot numbering. Stata's own numbering, with a CI fit counting as two plots, is `_dash_plot_style_indices` (19513-19541). `_dash_legend_key` (19729-19751) gives the default text.
- **Callers:** saved `DashRenderer._rebuild_legend` (21794-21805), called at 22311. Served template at 26435-26438, with `_plot_rends` built from `_leg_bounds` (26422-26428).
- **Colour-key legend:** `_COLORVAR_LEGEND_NAME = "_dash_clegend"` (2012) is kept out of the rebuild (15827-15830).

### Label-only (`-`) entries: existing pattern and BokehJS behaviour
- The discrete colorvar key already backs `LegendItem`s with invisible renderers (6574-6579):
  ```python
  _r = fig.scatter(
      x=[float("nan")], y=[float("nan")],
      color=color, size=0,
      visible=False, name=f"{_DASH_SWATCH_PREFIX}{factor}",
  )
  legend_items.append(LegendItem(label=factor, renderers=[_r]))
  ```
  `_DASH_SWATCH_PREFIX = "_clegend_"` (18708). `_dash_is_swatch(r)` (18766-18771) makes range fitting (17053), primary-range pools (17205) and legend entries (19772) skip such renderers.
- **Installed BokehJS 3.9.0** (Python 3.14.5): `is_active` is `t=>!0` under `click_policy` "none", which dash keeps (15795-15796). A `LegendItem` is dropped only when its own `visible` is false (`get_labels_list_from_label_prop(){if(!this.visible)return[];…}`), so an item backed by an invisible renderer is drawn. The marker legend icon ignores the glyph's `size`, so a `-` row needs fill and line alpha 0 (or colour None) to show no swatch.
- **legend_options.sthlp:216-298:** `order()` takes `{#|-} ["text" …]`. `-` followed by `""` inserts nothing; `" "` inserts a blank line. `lastlabel(# "text" …)` overrides both `order()` and `label()`.

### Existing tests
- `test_axis_options.py::TestLegendOptions.test_order_reorders_the_keys` (399) and `test_order_can_drop_a_key` (407).
- `test_graph_options.py::TestLegendLabels` (452, with 556-600 label overrides) and `TestLegendColsRows` (1259).
- `test_server_legend.py`: `TestAServedFigureHasALegend` (87), `TestTheLegendOptionsNowReachIt` (136).
- `test_mode_parity` cases "legend(order(2 1))" (1203) and `legend(label(1 "Cars") cols(2))` (1207).
- `test_textbox_multiline.py::TestALegendLabelIsReadAsStataReadsIt` (800) and `TestALegendLabelAdversarial` (835).
- `test_ci_plot_index.py::…test_the_legend_keeps_its_keys_in_order` (276).
- `test_label_sinks.py` (legend text is a DOM text node).
- `extract_axis_truth.do` already tells legend text in the SVG apart by diffing against a `legend(off)` companion probe (`anchorless_texts`).

---

## B6. `xtitle("")`/`ytitle("")` don't remove the axis title

- **`_dash_axis_labels`** (16003-16038):
  ```python
  x_text, _ = _dash_textbox(go.get("xtitle", ""), "xtitle", seen, key)
  y_text, _ = _dash_textbox(go.get("ytitle", ""), "ytitle", seen, key)
  x_label = x_text or x_default
  y_label = y_text or y_default
  ```
  Verified: `_dash_textbox('""', 'xtitle')` returns `('', {})`. `_textbox_lines('""')` is empty because an empty token ends the lines (2572-2573).
- **Spec:** `XTitle(string asis)` keeps `""` (length 2), so `: length local` > 0 and the JSON carries `"xtitle":"\"\""` (dash.ado:4944-4952). dash.sthlp:455-458 says an empty `title("")` clears.
- **Callers:** 21951 (saved) and template 26143-26144 (served). The result goes to `x_axis_label`/`y_axis_label` in the figure kwargs (21979-21980; 26151-26152).
- **Also affected:** `_dash_lone_second_axes` moves `ytitle2` to `ytitle` only when `second.strip()` is non-empty (1692-1694). A raw `""` is non-empty, so `ytitle2("")` survives the move. `_dash_style_axis_titles` uses `_parse_textbox_opt` and will still style an empty title; that is harmless.
- **Tests to place beside:** `test_textbox_multiline.py::TestBothModesDrawTheTextAsTyped.test_an_axis_title_is_the_same_saved_and_served` (605-612) and `test_axis_options.py::TestTitleTextFidelity`.

---

## B7. `ytitle2()`/`xtitle2()` draw their quote marks and ignore textbox grammar

- **`_dash_add_secondary_axes`** (16997-17030). The only reader of `{n}title2` (verified with grep):
  ```python
  n = name[0]
  toks = _dash_by_tokens(str(graph_opts.get(f"{n}scale2", "") or ""))
  is_log = "log" in [_dash_subopt_name(t) for t in toks]
  ax = (LogAxis if is_log else LinearAxis)(
      **{kw: name}, axis_label=graph_opts.get(f"{n}title2", ""))
  fig.add_layout(ax, side)
  ```
  Callers: 22096 (saved, after `_dash_style_axis_titles`) and template 26207 (served, before it). `_dash_style_axis_titles` (18905-18929) styles only `_dash_primary_axes(axes, rattr)` (16832-16843). Styling the second axis inside `_dash_add_secondary_axes` avoids depending on that order.
- **ado:** `YTITLE2(string asis)`/`XTITLE2(string asis)` (dash.ado:708) with aliases `yti2`/`xti2` (744, 747). The quotes reach the spec.
- **Reuse:** `_dash_textbox(raw, "ytitle2", seen, key)`, then `ax.axis_label_text_font_size`/`axis_label_text_color` from `_textbox_size`/`_textbox_color` (the same code as 18923-18929). `seen`/`key` are not parameters of `_dash_add_secondary_axes` today, so its signature needs extending, including the template call at 26207.
- **Tests:**
  - `test_dual_axis.py::TestSecondaryAxisOptions.test_ytitle2_on_right_axis` (178, DAX-07, unquoted value).
  - `TestALoneSecondAxisIsDrawnAsTwowayDrawsIt` (353-419, both modes with `_lone_figure`; `test_a_hostile_title_is_canvas_text` at 410).
  - `test_json_escaping.cscript` JSE-46 case `jg46k` (line 1974): `dash (scatter mpg weight) (line mpg weight), ytitle2("line 1" "line 2") xtitle2(`"a "b" c"')`, checked stored as typed (1980, 1985).

---

## G16. Value labels never drawn on axes or in tooltips

### Value labels already reach Python
- **Export:** `_dash_write_stata_data` (dash_render.py:1214) through sfi, run by dash.ado `_dash_write_data` (4169-4215). Labels are collected at 1313-1351 and written as:
  ```python
  "valueLabelNames": label_names,   # {var: labelset}
  "valueLabels": value_labels,      # {VAR name: {code: text}}, keyed by the variable
  ```
  Keys come from `_dash_label_key` (1193-1211): the integer as text; `.`, `.a`-`.z` as jsonio's codes.
- **Saved load:** `self.value_labels`/`self.value_label_names` (21150-21153).
- **Served load:** `val_label_names`/`val_labels` (template 25699-25700, `meta` 25749-25751, used at 25866-25876). They are attached to the mapper with `_dash_attach_labels` (18745-18763).
- **The labelset-then-variable lookup is written five times:** `_apply_colorvar` 6399-6405; `GlyphMapper._mlabel_value_labels` 6973-6987 (the cleanest); `_dash_csv_meta` 13909-13912; `_dash_facet_label` 15601-15607; the saved filter builder 23598-23603. A shared module-level helper would be reuse, not new logic.
- **Code → text:** `GlyphMapper._mlabel_value_text(value, vlabels)` (7085-7104, staticmethod) gives the label if the value is a labelled whole number, else the number, else "." for missing.

### Tooltips
- **`_dash_build_hover(fig, xvar, y1var, y2var, hover_extra, var_labels, date_vars, numeric_formats, univar, layers)`** (19839-19990) has no value-label parameter. Rows come from `_dash_hover_row(col, label, date_kind, numeric_fmt)` (19795-19808), which returns `(label, "@{col}{fmt}")`. `_fields_for` (19917-19951) keeps a column only if some renderer's source carries it (`_c not in _present`), and it refuses names that fail `_DASH_VARNAME_RE`. A group gets the full tooltip only if `_seen <= _cols_of(r)`.
- **Callers:** 22348-22359 (saved) and template 26451-26463 (served).
- **The marker-label derived column to mirror** is in `GlyphMapper._apply_mlabel_opts` (6732-6765):
  ```python
  _vlabels = ({} if _kind else self._mlabel_value_labels(mlabel_var))
  text_col = f"__mlabel__{mlabel_var}"
  if text_col not in source.data:
      raw = list(source.data[values_col])
      if _vlabels:
          rendered = [self._mlabel_value_text(v, _vlabels) for v in raw]
  ```
  DISCOVERY Q7 renames `__mlabel__*` to the `__dash` prefix; a hover column should use that prefix too.
- **Derived columns survive filter moves in both modes.** On the saved page, each source's snapshot is taken in `render()` after the figures are built (23785-23787), and `_FILTER_JS` rebuilds each source from its own snapshot's columns (14204-14215). When served, `_dash_refresh_unlinked` (18166) reads a column missing from the frame "from the snapshot at the row's own position".

### Axes (`valuelabel`)
- `_dash_parse_axis_spec` treats `valuelabel` as unsupported (honoured tuple 16635-16636). Verified: `, valuelabel` → `['valuelabel']`, and `, val` → `['val']`. Stata's minimum is `val` (axis_label_options.sthlp:112).
- Stata maps the ticks through the first y variable's value label for y options and the x variable's for x options (axis_label_options.sthlp:269-280).
- `_dash_apply_axis_options(fig, graph_opts, xvar, yvar, frame, numeric_formats, seen, key, grid_color)` (16965-16994) has no value labels; it needs a parameter at 22115 and 26266. Reuse the explicit-label path (16783-16798). For the default ticker, `major_label_overrides` keyed by float code is what matches.

### Docs and tests
- dash.sthlp:672-680 (difference 6 says axes and tooltips show numbers and `xlabel(, valuelabel)` is named).
- `test_suboption_warnings.py` SUBOPTIONS entry `("xlabel valuelabel", {"xlabel": ", valuelabel"}, None, "xlabel", ["valuelabel"], [])`. It pins the note and will flip.
- `test_mode_parity` `_DF` has `foreign` with `_VALUE_LABELS = {"origin": {"0": "Domestic", "1": "Foreign"}}` and `_LABEL_NAMES = {"foreign": "origin"}` (86-98). Cases "hover()" (1133) and "hover() on a bar" (1134) use `hover: "foreign"`.
- `test_server_layer_defects.py::TestTheHoverBuilder` (the function map's entry for `_dash_build_hover`/`_dash_hover_row`).
- `test_marker_label_parity.py::TestTheLabelSetLookup` (the value-label lookup).

---

## X2. `colorvar()`: `colordiscrete` + `colorcuts()`, cuts below the minimum, `colorlevels`, `colorvarminmax`, z options

### Code the fix must touch: `GlyphMapper._apply_colorvar` (6338-6655)
- **Only caller:** `map_scatter` (7229), so colorvar is drawn on scatter, connected, rconnected and dot.
- **Option reads:**
  - `colordiscrete` → `force_discrete = bool(options.get("colordiscrete"))` (6376)
  - `colornlevels` (6422-6428)
  - `colorcuts`, split on blanks and sorted (6430-6437)
  - value labels through `_vlookup` (6396-6420)
- **Interval path taken whatever `colordiscrete` says** (6456-6479):
  ```python
  if is_numeric and (force_discrete or needs_binning):
      color_field = f"_cvar_{varname}_bin"
      if cuts is not None:
          # User-supplied boundaries: bins are (-∞, c0], (c0, c1], …, (cN, +∞)
          n_bins = len(cuts) + 1
  ```
  `_assign_cut` uses `searchsorted(side="left")` (6473-6477). Cuts below the minimum are kept (no filtering).
- **Paths:**
  - equal-width `colornlevels` (6481-6498)
  - `colordiscrete` without cuts: one level per distinct value, with value labels (6500-6511)
  - string path (6517-6533)
  - palette choice (6539-6555)
  - discrete Legend with swatches, titled `var_display`, name `_COLORVAR_LEGEND_NAME` (6566-6597)
  - continuous `LinearColorMapper` plus `ColorBar(title=var_display)` (6599-6629; GAPS2's "6424-6446" is stale)
  - the layer's own plot-legend item is stripped (6644-6655)
- **Plumbing in dash.ado:**
  - Plot syntax at 911-913: `COLORVar(string) COLPALette(string) COLORDIScrete COLORUSEPLEGend COLORNlevels(string) COLORCUTs(string asis) COLORMissing(string)`.
  - sreturn at 1141-1146; rules at 1867-1869 (`colornlevels=int,2,256`, `colorcuts=numlist,1`, `colorvar=var`); JSON key list in `_dash_plot_opts_to_json` (2856-2860).
  - `_dash_fold_typed` (1672 onward, companion list at 1684) names colorvar companions on types that don't draw them.
  - Mata `_dash_rep_unique` (dash_parse.mata:4271-4292) refuses a second `colorvar`/`colordiscrete`/`colorcuts`.
  - `_dash_rep_und_tab` (4318-4400) lists the undeclared-but-take-once colour options: `colorvarminmax` (4362), `colorrule`/`colorstart`/`colorend`, `colorformissing`, `colorkeysrange`, and graph-wide `clegend` (4366).
  - `colorlevels` is in neither Mata table; it arrives through `*` and is named. Declaring `colorlevels`/`colorvarminmax` means editing the syntax, sreturn, rules, JSON list, `_dash_fold_typed` list, and removing `colorvarminmax` from `_dash_rep_und_tab`.
- **z options:** `zlabel`, `ztitle`, `zscale` are declared nowhere (no match in dash.ado, dash_parse.mata, dash.sthlp or test fixtures). Stata's spellings: `zlab:el` (axis_label_options.sthlp:32), `zti:tle` "contour legend axis title" (axis_title_options.sthlp:37), `zsc:ale` (axis_scale_options.sthlp:38). They are graph-level, so they need:
  - both syntax blocks (dash.ado:699, 899) and the `g_*` sreturn blocks (801-856, 1206-1262)
  - the seven graph-key `foreach` lists (3951 … 4942)
  - Mata `_dash_rep_cat` categories (L, T, S)
  - drawing on the Legend or ColorBar made in `_apply_colorvar` (title, ticker, `major_label_overrides`)
- **Stata rules** (colorvar_options.sthlp:95-133): under `colordiscrete`, `colorcuts` values are the levels and other values join missing (gray). Cuts below the minimum are ignored, and if all are below, the minimum is the cut. `colorlevels(#)` makes #−1 equal cuts. `colorvarminmax` adds the min and max to the cuts. `colorcuts` and `colorlevels` may not be combined.

### Tests that will change or can be placed beside
- `test_help_claims_7.cscript` HC7-02 (lines 316-325) runs `dash scatter mpg weight, colorvar(price) colorlevels(4) colorrule(hue) colorformissing(red)` and asserts the note names `colorlevels() colorrule() colorformissing()`. This flips once `colorlevels` is honoured.
- `test_glyphs.py` "P1A-46" block (3348-3600): colordiscrete, colorcuts intervals (3487-3515), colormissing, coloruseplegend.
- `test_function_audit.py` (286-360): `TestColorCutsPutEachPointInItsLabelledBin` and `TestColorLevelsPutEachPointInItsLabelledBin`, the function map's entries for `_assign_cut`/`_assign_nlev`.
- `test_colorvar_legend.py` (`_VL` repair labels, `_render`): `TestTheDiscreteColourKeySurvives`, `TestTheSchemeChromeIsStillApplied`, `TestTheMixedCase`, `TestTheContinuousPathIsUnchanged`, `TestNoColorvarIsUnchanged`.
- `test_mode_parity` colorvar cases (1141-1150).
- `test/fixtures/rejected_options.json` holds historical probes for `colorlevels(4)`/`colorvarminmax`: twoway rc 0, where dash once refused them.

---

## D1. Quoted scheme values (RGB, %opacity) dropped without a warning

### Code the fix must touch: `SchemeParser._parse_lines` (3941-3998)
```python
tokens = line.split()
if len(tokens) < 2:
    continue  # malformed line — skip
category = tokens[0]
value = tokens[-1]
subcats = tokens[1:-1]
key = (category + " " + " ".join(subcats)).strip() if subcats else category
props[key] = value
```
- Only `*` comments and blank lines are skipped (3955). `//`, `*!`, `sequence` and `label` are not treated as Stata treats them: `label "s2 color"` in every shipped scheme is stored under the malformed key `'label "s2'`.
- `#include` handling (3960-3986) and `_include` (4000-4049) are untouched by D1.
- **Callers:** `_parse_file` (3897-3939), called from `__init__` (3715-3716) and `_include`.
- **The served app** receives `_SCHEME_PROPS` (24708) and `_s._props = dict(_SCHEME_PROPS)` (24717). It never parses a file.

### Stata's grammar (scheme.class:189-226)
```stata
local line : subinstr local line "`=char(009)'" " " , all
tokenize `"`line'"'
args style id stylename
if `"`style'"' == `"#include"' { .setscheme , scheme(`id') ...
if `"`style'"' != `"*"' & `"`style'"' != `"//"' & ... `"*!"' & `"sequence"' & `"label"' {
    if "`stylename'" == "" { local stylename `id' ; local id _default }
```
- Tabs become blanks. Keys are two-level (`style id`). The value is the third token, with its quotes removed by `tokenize`; later tokens are ignored. A two-token line is a class default.
- **Reference implementation:** `scripts/extract_scheme_truth.py` `SchemeResolver._load` (207-262) with `_TOKEN = re.compile(r'"[^"]*"|\S+')` (297). Its docstring (146-163) records `symbolsize p small *medium` read as `small` (measured). It does not handle compound quotes or an unclosed quote. Stata's base `scheme-meta.scheme` has `margin legend "1 0 0 0` with no closing quote; `_textbox_string_end` already reads an unclosed string to the end, as gettoken does.
- **Shipped schemes are unaffected** by a switch to third-token reading: the only non-comment lines with more than three tokens are `label "…"` lines. sttrans was transcribed to `color p1 #1a476f%20` (schemes/sttrans.scheme:47, provenance at :267).
- **The colour readers already accept the unquoted forms:**

  | Input | `translate_mcolor` | `parse_color_alpha` |
  |---|---|---|
  | `26 71 111` | `#1a476f` | `('#1a476f', None)` |
  | `26 71 111 %20` | `#1a476f` | `('#1a476f', 0.2)` |
  | `"26 71 111"` (quoted) | ValueError | `(None, None)` |
  | `khaki*0.3` | refused | refused |
  | `hsv 120 1 1` | refused | refused |
  | `0 100 100 0` (CMYK) | refused | refused |

  The last three are D7's shared work. `SchemeParser._color` (4077-4100) and `_color_alpha` (4102-4128) warn "dash scheme: colour … is not a colour dash recognises" for a present but unreadable key. Warnings are bounded with `_notes` and `_MAX_INCLUDE_NOTES` in `_include`; a per-line D1 warning should use the same bound.

### The 129 local third-party schemes
- They are in `/Users/billy/Library/Application Support/Stata/ado/plus/s/scheme-*.scheme`. 127 contain a `color … "digits` line; the two exceptions are `scheme-s1network.scheme` and `scheme-s2network.scheme`. `scheme-d3colors.scheme:301` has `color p1 "31 119 180"`, and `label "d3colors"` is at :26.
- Across these files plus Stata's 26 base schemes, the quoted directives are `color` (29,374 lines), `special` (298; for example `special matrix_xaxis "xlabels(#3, axis(X))"`), `label` (151) and `margin` (1). Quoted formats such as `"%24.0fc"` also appear.
- The files are machine-local and in PLUS, which dash deliberately doesn't read (dash.sthlp:2808-2814; X5 is out of scope). A test over them has to skip when absent, and test_fixtures_are_committed-style rules mean a committed test should pin a copied d3colors, not the PLUS path. A parse test can call `SchemeParser.__new__` plus `_parse_file(path, set())` directly; `#include`s resolve through `_resolve_path` to dash's translations.

### Existing tests and scripts
- `test_scheme_consumption.py::TestAnIncludeIsSplicedWhereItStands` (the function map's entry for `_parse_lines`).
- `test_scheme.py`, `test_scheme_fidelity.py`, `test_scheme_coercion.py`, `test_scheme_resolution.py`, `test_scheme_review_fixes.py`, `test_scheme_visual_truth.py`, `test_server_scheme.py`.
- `test_custom_scheme.cscript` (CS-01…CS-15). It builds `mytheme.scheme` from s1rcolor with `color background #123456`, unquoted; a quoted variant would sit beside it.
- `scripts/extract_scheme_truth.py` (fixture `scheme_truth.json`).

---

## Reusable helper index

| Helper | Anchor | Use |
|---|---|---|
| `_textbox_string_end` | 2448-2481 | B1, B5 tokenising; D1 unclosed quotes |
| `_textbox_lines` | 2528-2574 | multi-line labels (B1, B5, B7) |
| `_textbox_split_point`, `_TEXTBOX_SUBOPT_RE` | 2484-2525, 2444 | B3 table |
| `_parse_textbox_opt` | 2614-2682 | B3 normalisation point |
| `_textbox_size`, `_textbox_color` | 2577-2611 | B3, B7 styling |
| `_dash_textbox` | 18861-18878 | B6, B7 text plus naming |
| `_dash_style_axis_titles` | 18905-18929 | B7 styling template |
| `_dash_report_suboptions`, `_dash_subopt_name`, `_dash_by_tokens` | 18813-18835 | naming in the note |
| `_dash_warn_once`, `_dash_style_note` | 12377, 12385 | one-off notes |
| `_dash_parse_axis_spec`, `_dash_apply_axis_spec` | 16605, 16738 | B1, G16 |
| `_dash_date_axis_spec`, `_dash_axis_positions`, `_dash_note_not_dates` | 16931 | date positions (B1, B2) |
| `_dash_count_axes`, `_dash_place_count_ticks`, `_dash_finish_count_ticks`, `_dash_common_count_ticks` | 17210-17377 | B2 extent step |
| `_dash_secondary_values` | 17040-17092 | drawn values per range (B2) |
| `_MAX_AXIS_TICKS` | 16081 | B1 bound |
| `_dash_add_secondary_axes`, `_dash_finish_secondary_axes` | 16997, 17095 | B2, B7 |
| `_dash_legend_parts`, `_dash_legend_arg`, `_dash_legend_entries`, `_dash_plot_style_indices` | 15682, 15706, 19754, 19513 | B5 |
| `_DASH_SWATCH_PREFIX`, `_dash_is_swatch` | 18708, 18766 | B5 `-` placeholders |
| `_dash_build_hover`, `_dash_hover_row` | 19839, 19795 | G16 |
| `GlyphMapper._mlabel_value_labels`, `_mlabel_value_text`; marker-label derived column | 6973, 7085; 6732-6765 | G16 |
| `_apply_colorvar` | 6338-6655 | X2 |
| `SchemeParser._parse_lines`; `extract_scheme_truth.SchemeResolver` | 3941; scripts 146-297 | D1 |
| dash.ado `_dash_validate_value` (numlist), `_dash_option_rules` | 2122-2148, 1853-1929 | B1 ado expansion |
| Mata `_dash_imm_next`, `_dash_imm_number`, `_dash_rep_toks`, `_dash_rep_merge` | dash_parse.mata 1207, 1400, 4064, 4826 | B1, B3 ado side |
