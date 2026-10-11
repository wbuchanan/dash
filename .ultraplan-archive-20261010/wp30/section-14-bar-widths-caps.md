# Section 14: Bar widths and range caps (P1.17 part a)

> Part of: WP-30 · Items: P1.17 part a (entry P1.17a) · Risk: yellow · Batch: 5 · Depends on: 08 · Blocks: 27, 49 · Tasks: 13, 1 commit · Case prefix: BG

## Review amendments

- Fixed (major): the truth-block header was written `bar widths and range caps`; S01's stub header is the manifest name less its parenthesis, `Bar widths and range caps` (TR-01.6), and `TestTheWp30TruthScript` reads it. The section now names S01's header and never retypes it.
- Fixed (major, M5/R4): the new rcap/rcapsym refusal needs a Changed behaviour line, but S01's Appendix A gives P1.17a only Results that change. 14-13 now widens `WP30_LISTS` only if the consistency pass has not, and replaces a Changed behaviour marker if S01 placed one. The Results marker is named by its list. The S01/index fix is recorded in g03.md.
- Fixed (minor): 14-11 (`<files>none</files>`) could flip tests in unlisted files. A red node outside 14-03..14-06's files now stops and is reported (one to three files per task).
- Fixed (minor): EW-02's location (`test_wp29_truth.cscript`). The R1 note no longer suggests that S13 appends to test_twoway_option_parity.cscript.
- Cross-file: index batch 5 omits S14's `_generate_app_source` (HIGH), `_glyph_layer_lines` (HIGH) and `build_dropdown` (CRITICAL) from 5.0's expected list. R2's S14 row says `_dash_copy_redraw_geometry` "in place", where register A61 removes it ("−"). Both are recorded in g03.md.
- Rejected: "refuse `rcap …, bw(.5)` (twoway r(198)) under M5". `bw()` is dash's own spelling (`_dash_fold_bw`), and twoway refuses it on every type, bar included. Refusing it is the option-surface sweep M5 leaves to P2.21. BG-09 keeps today's note.
- Rejected: "D-14b breaks A139 (one `_generate_app_source` editor per batch)". Neither S13 nor S15 edits the template (both Boundaries say so), so S14 is batch 5's one editor. The edit only deletes the four emitted lines A61 removes.
- Checked: the anchors (`map_bar` 10200-10260, `_tag_spacing` 10292, `map_rbar` 13052, `map_rcap` 13198, `_FILTER_JS` 18740, copy list 33332, template 36039-36042, dash.ado 4113-4121 and `_needed` :251, program_coverage_map's dash_parse.mata form) match HEAD. No function is shared with S13 or S15: the appliers are called, not edited, and the copy-list anchors differ.
- (cross-file pass) 14-13 step 2: S01 Appendix A now gives P1.17a "Results that change; Changed behaviour" (g03 fix applied in S01), so the row and the Changed behaviour marker are expected in place; the fallback widening is kept for safety.
- (cross-file pass) 14-13 verify: added the key-deletion check `grep -c '^    "P1.17a": "' test/test_tracking_documents.py` prints 0 (S01 TR-01.10.1).
- - (ratification 06oct2026, binding) After removing the bar spacing writer, add to task 14-01's failing tests one case in `test/test_brushed_copies.py` (S08's file): after a filter move, a bar's `nonselection_glyph` and `muted_glyph` widths equal the glyph's width in both modes (S08's known gap, A61).
The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:121-127 (P1.17) reads: "bar and rbar default to 0.8× the smallest x gap, not 1 x-unit. rbar ignores `barwidth()` with no note. [...] rcap cap width ignores `msize()`, and rcapsym draws caps `twoway` does not." Its WP-29 note adds: "barwidth() on a date axis (S05); P0.18 (commit 2d52fbe) fixed the served redraw widths only: twoway's one-x-unit bar width stays here". GAPS2 A3 (GAPS2.md:145-172) gives the gap and its plan; its tracking points at BUGS.md:504, where the divergence was recorded in WP-27 and not acted on ("twoway_bar.sthlp documents twoway bar's default barwidth as a constant 1 in xvar units, NOT derived from x spacing").

Measured at `c96facd` (research `.ultraplan/wp30/research/p1-17.md` §2, re-measured for this file under Evidence):
- `bar y x` draws width 0.8 × the smallest x gap: 0.8 at spacing 1, 0.08 at .1, 4.0 at 5, 0.4 for x = {1, 1.5, 4, 10, 11}. twoway draws 1.0 in every case (`.plot1.bar_size` = 1).
- `rbar lo hi x, barwidth(.3)` draws 0.8 (or 56 on the parity frame's weights), with no note. twoway draws 0.3.
- On a weekly `%td` axis a bar is 5.6 days wide (twoway: 1 day), and `barwidth(3)` draws 3 **milliseconds** (twoway: 3 days). A monthly `%tm` bar is 23.2 days wide (twoway: one month).
- `rcap ..., msize(large)` draws the same caps as `msize(small)`: half-width 0.2 × the smallest x gap in data units. twoway's cap is the msize in Stata's relative units (cap length / min(W,H) × 100 = 1.52778 for the default, 2.4306 for large) and does not move with the x spacing.
- `rcapsym` draws a spine, two cap Segments and two markers of fixed `size=7`. twoway draws the spine and two markers at the scheme's symbol size, and no cap line.
- After a filter move the widths change in both modes (WP-29 P0.18: the saved page recomputes 0.8 × the kept rows' gap, the served app copies the redraw's width: 56 → 168).

**After this section** both modes draw bar and rbar one x unit wide, or `barwidth()` units, in the x variable's own units on a date axis (a day for `%td`, a millisecond for `%tc`/`%tC`, one period for `%tw`-`%ty`), as twoway draws them. rbar reads `barwidth()` (and dash's `bw()` and `width()` spellings that already reach it) silently. rcap's caps are `marker="dash"` Scatter glyphs as long as a marker of the layer's `msize()`, the scheme's `symbolsize p#` by default, in screen units, through S08's resolver. rcapsym draws no caps, and its end markers start at the scheme's symbol size. `barwidth()` on rcap and rcapsym is refused r(198) with twoway's words, `option barwidth() not allowed`, naming the spelling as typed (P1.17.4, M5). Every width and cap is a constant or a per-row data column, so it holds through a filter move in the saved page and the served app with no recompute, and the WP-29 P0.18 spacing machinery is deleted: `GlyphMapper._tag_spacing`, the `_FILTER_JS` spacing writer, the `derived_spacing_*` callback arguments that `_build_filter_widgets` fills, and `_dash_copy_redraw_geometry` with its served copy-list entry and its emitted call (P1.17.3, A61). Cap renderers carry the tag `dash_cap`, which S49's transpose rotates (P1.17.5, A62).

**Why one section, and what is left for S27.** These four sub-claims (GAPS2-A3-a, A3-b, A3-d, A3-e) are geometry that needs no axis knowledge and is invariant under filter moves, and they share the four mappers and the spacing machinery. The default base (A3-c, A3-f) needs the finished axis scale and S21's finishers, so it is S27's, two batches later (A138, IR-12). S14 must not touch `base`.

**Test order and commit rule (rule 7, D1).** One cycle, one commit `(WP-30 P1.17a)`:
- **14-01** writes the truth extractor and runs it (twoway only, so the fixture is the same before and after the fix), writes `test/test_bar_range_geometry.py`, runs it against the unmodified tree and saves `<scratch>/14-P1.17a-failure.txt`. It never commits.
- **14-02** writes the BG truth block and the refusal cases red and appends their FAIL lines.
- **14-03 to 14-06** flip the pinned tests in place (red at base after the flip) and append the parity cases.
- **14-07 to 14-10** fix the mappers, remove the machinery and add the refusal.
- **14-11** certifies, **14-12** updates the help, **14-13** closes the entry and makes the one commit.

No test-only commit exists, and no commit is red.

### Section decisions (this file; binding on the executor)

- **D-14a. rcapsym's `barwidth()` is refused with rcap's.** The register rules on rcap (P1.17.4). Measured 03oct2026 (probe `p1.do`, Evidence): twoway refuses `barwidth()` with r(198) `option barwidth() not allowed` on rcap **and rcapsym**, and also on rspike, rscatter, rarea, rline, rconnected, scatter and line; it accepts it on spike, dropline and area. rcap and rcapsym are this section's mappers, so both fall inside M5's "areas WP-30 touches". The other seven types are outside S14's area and are handed to the closeout as part of P2.21's surface (Notes).
- **D-14b. `_dash_copy_redraw_geometry` is deleted, not kept inert** (register P1.17.3, ruling A61: "Remove it (deletions, with the CRITICAL/HIGH warnings)"; research p1-17 §4 step 4; critic correction 4). Once no width depends on the kept rows the function has nothing to copy, and S55's planned use ("uses height") is cancelled with P1.9's step 5 (IR-13). This makes S14 batch 5's one `ServerAppBuilder._generate_app_source` editor: the edit deletes the four emitted lines at dash_render.py:36039-36042 and nothing else. Neither S13 nor S15 edits the template (their scopes and research name no template line), so A139's "at most one per batch" holds. The index's R2 row S14 ("`_dash_copy_redraw_geometry`, 33332, in place") is read as superseded: the copy-list entry at 33332 is **removed** ("−"). This deviation is reported with the 5.0 HIGH list. **Fallback** if the maintainer rules "keep" at 5.0: the function, its entry and its call stay; its body becomes a documented no-op (`return None`, docstring naming P1.17a), and `TestTheRedrawGeometry`'s four nodes are flipped to assert that nothing is copied; 14-09's verify then expects one `_dash_copy_redraw_geometry` definition, one copy-list entry and one emitted call.
- **D-14c. Per-row edges on a period axis.** On `%tw`, `%tm`, `%tq`, `%th` and `%ty` a bar spans `_dash_units_to_axis(u - w/2)` to `_dash_units_to_axis(u + w/2)`, because periods differ in length in milliseconds (a month is 28-31 days), so no constant millisecond width is right. The VBar is drawn from two reserved data columns, `__dash_bar_xc` (centre) and `__dash_bar_w` (width), held as `GlyphMapper` class attributes `_BAR_XC` and `_BAR_W`, so no served copy-list entry is needed (R2: class members travel with their class). The field form is used on every path of a period-kind x, the empty layer included, so the glyph's field specs are the same whatever rows a move keeps.
- **D-14d. The unit follows the variable, not the figure's axis.** The kind is `self.date_vars.get(xvar)` (both modes attach it through `_dash_attach_labels`, dash_render.py:25741). A date variable's column is held in epoch milliseconds wherever it is drawn (`_dash_load_columns`, :701), so its width must be in milliseconds even on a mixed axis. Mixed date and numeric axes stay S35's.
- **D-14e. The cap size is S08's marker size.** map_rcap calls S08's `OptionTranslator.resolve_size` exactly as S08's `_apply_marker_opts` calls it for `msize()` (same kind, same default), and defaults to `self.scheme.default_marker_size(color_idx)`. S14 does not edit `_apply_marker_opts`: S13 is batch 5's editor of the appliers (R12).
- **D-14f. One rule on every path.** The empty bar and rbar layers take width 1 (or `barwidth()`), replacing WP-29 P0.18's "one fallback width (0.8, 0.64)". The string-x branch of map_bar (`_bar_numeric = False`, :10194-10197) is unreachable since GAPS2 G2 (dash.ado refuses a string x r(109)); the `x_vals` computation that fed it and the width is deleted, and the width rule is the same 1.

## Risk: [yellow] — every bar, rbar, rcap and rcapsym dashboard changes look, and the removal edits the saved filter script, two CRITICAL and two HIGH symbols

**Why.** The width and cap rules change every bar and range dashboard in both modes. The removal deletes code from `_FILTER_JS` (shared by every saved page with a filter), from the three filter builders, from `_build_filter_widgets` and from the served template. The mappers are dispatched by name (`_dash_glyph_dispatch`, dash_render.py:28546-28549), so GitNexus resolves none of their callers.

**Risk factors.**
1. Pinned tests of today's widths, cap Segments and spacing tags across many files (Evidence "Measured red list").
2. A period-date bar drawn from a data column must keep that column through a saved move (row copy) and a served redraw (data copy), or BokehJS draws nothing.
3. The served app copies data only; a glyph spec that depended on the row count (a field on one path, a value on another) would break after a move that empties a layer.
4. Hover and colour readers: cap Scatters join the layer's HoverTool renderers (measured on the simulated fix: the tooltip fields are unchanged), and a Scatter left at Bokeh's default `fill_color` #1f77b4 showed up in two colour tests (Evidence "Measured red list").
5. Bokeh's `dash` marker has length equal to `size` in screen pixels (BokehJS `_one_line`: `moveTo(-r, 0); lineTo(r, 0)`, `r = size / 2`); a later Bokeh could change that.
6. A refusal in dash.ado must read the option word as typed without reading text inside quotes or nested parentheses.
7. Batch partners: S13 edits `_apply_line_opts` and `_apply_marker_opts`, which the cap Scatters pass through; S15 regenerates the scheme files whose `symbolsize` the caps read.

**Mitigation.**
1. 14-01 to 14-06 write and flip every pin before the fix; the red list below was measured on a simulated fix and is re-measured in 14-11 (R9).
2. `TestTheWidthHoldsAcrossAMove` runs the page's own `_FILTER_JS` under node and the served `_on_filter_change`, for `%tm` bars too.
3. D-14c: the field form on every path; `test_an_empty_period_layer_keeps_the_field_form` pins it.
4. `TestTheTooltipsAreUnchanged` (guard) pins the tooltip fields in both modes; the caps take `fill_color=_rcap_color` (no visual effect: BokehJS's `dash` marker strokes a line only).
5. `test_the_dash_marker_is_as_long_as_its_size` reads BokehJS's `_one_line` source from the installed package, so a Bokeh change fails a named test.
6. `_dash_barwidth_typed` reads top-level tokens through `_dash_rep_toks`/`_dash_rep_optname`, as `_dash_logit_typed` does; BG-09 pins quoted and nested text.
7. S14 calls the appliers and edits neither; the cap tests compare with `map_scatter`'s own marker size, not with constants, so S13's and S15's merges cannot strand them.

## Dependencies

- **Depends on: 08.** S08's `OptionTranslator.resolve_size(value, kind, default)` sizes the caps in Stata units (IR-1: option B, one Stata unit for every class), and `SchemeParser.default_marker_size` returns S08's px for `symbolsize p#`. S14 copies S08's `msize()` call from `_apply_marker_opts` at the batch-5 base.
- **Blocks: 27, 49.** S27 (batch 9) draws twoway's default base in `map_bar`, `map_spike`, `map_dropline` and `map_area` on the tree this section leaves; it must not reintroduce a row-dependent width. S49 (batch 17) transposes the four mappers and rotates every renderer tagged `dash_cap` (P1.17.5).
- **Precedes S21** (batch 7; manifest note): S21's hull and its saved JS port read a bar's extent from its glyph, a constant or the `__dash_bar_w` column (test_axis_extents.py `TestBars` already reads both forms).
- **Parallel batch: 5**, merge order S13, S14, S15. **Can run with S13 and S15**: neither edits map_bar, map_rbar, map_rcap, map_rcapsym, `_FILTER_JS`, the filter builders, `_build_filter_widgets`, `_generate_app_source`, `_dash_process_segment` or `dash_parse.mata`'s parser helpers. S13's `_apply_line_opts` and `_apply_marker_opts` are called by the caps unchanged.

## Evidence

All anchors are at `c96facd` (dash_render.py 37,689 lines, dash.ado 8,487). Symbols are authoritative; S08-S12 (batches 3-4) land first and may shift numbers.

### The widths

`GlyphMapper.map_bar` (def :10122) derives the width from the kept rows' spacing and tags the source, dash_render.py:10198-10221 and :10256-10260:

```python
10200        _bar_fallback = 0.8
10201        if len(x_vals) >= 2:
10202            gaps = [x_vals[i+1] - x_vals[i] for i in range(len(x_vals)-1)]
10203            bar_width = 0.8 * min(gaps)
10214        for key in ("barwidth", "width"):
10215            if key in options:
10216                _bw = _stat_option_float(options, key, None, "bar",
10217                                         lo=_MIN_BAR_WIDTH)
10218                if _bw is not None:
10219                    bar_width = _bw
10256        if _bar_numeric:
10259            self._tag_spacing(clean_source, xvar, 0.8, _bar_fallback,
10260                              distinct=True, glyphs=[r.glyph])
```

A `barwidth()` value reaches `width=` raw, so on a date axis (epoch milliseconds) `barwidth(3)` is 3 ms. `map_rbar` (def :13005) never reads `barwidth`/`width`, :13050-13068:

```python
13052        _rb_fallback = 0.8 * 0.8
13053        bar_width = (0.8 * min(x_vals[i+1] - x_vals[i]
13054                               for i in range(len(x_vals)-1))
13055                     if len(x_vals) >= 2 else _rb_fallback)
13067        self._tag_spacing(source, xvar, 0.8, _rb_fallback, distinct=True,
13068                          glyphs=[r.glyph])
```

dash.ado already hands `barwidth()` to rbar's spec (`BARWidth(string)`, dash.ado:934; `bw()` folds to it on bar, rbar, histogram, dot and spike, :1604-1617), so no dash.ado change is needed for rbar.

### The caps

`map_rcap` (def :13153), :13194-13235: half-width 0.2 × the smallest gap, in data units, two cap Segments, `msize()` never read:

```python
13198        if len(x_sorted) >= 2:
13199            cap_hw = 0.2 * np.min(np.diff(x_sorted))
13208            _x0_col: x_arr - cap_hw, _x1_col: x_arr + cap_hw,
13211        self._tag_spacing(cap_source, xvar, 0.2, 0.2, distinct=False,
13212                          cols=((_x0_col, -1), (_x1_col, 1)))
13230        bot_cap = fig.segment(**_bot_kwargs)
13235        return [spine, bot_cap, top_cap]
```

`map_rcapsym` (def :13512), :13561-13625: the same caps plus two markers of fixed size:

```python
13565            cap_hw = 0.2 * float(np.min(np.diff(x_sorted)))
13599                                    fill_color=mark_color, line_color=mark_color, size=7,
13602                                    fill_color=mark_color, line_color=mark_color, size=7,
13608        bot_cap = fig.segment(**_rcs_bcap_kw)
13625        return [spine, bot_cap, top_cap, bot_dot, top_dot]
```

The scheme's marker size is `SchemeParser.default_marker_size(index)` (:7291-7298, `symbolsize p#` cycling through fifteen). `OptionTranslator.translate_msize` (:5542) is what S08 replaces with `resolve_size`.

### The spacing machinery (WP-29 P0.18, commit 2d52fbe)

- `GlyphMapper._tag_spacing`, :10292-10309, a staticmethod writing `source._dash_spacing` and `source._dash_spacing_glyphs`.
- `_FILTER_JS` (constant at :18562), :18737-18753 and :18769-18778:
  ```js
  18740 const _dspacing = (typeof derived_spacing_json !== "undefined")
  18741     ? JSON.parse(derived_spacing_json) : [];
  18744 function dash_spacing(xs, sp) {
  18769         const _sp = _dspacing[_di];
  18770         if (_sp && _sp.x in _nd) {
  18774                 _nd[_col] = _xs.map((v) => (v === null || v === undefined ||
  18777             for (const _g of (_dspacing_glyphs[_di] || [])) { _g.width = _w; }
  ```
  The script writes columns and a glyph property named by JSON the page carries; the removal takes that path away.
- `FilterBuilder.build_dropdown` (:19430), `build_slider` (:19531), `build_range` (:19593): the default args `"derived_spacing_json": "[]"` and `"derived_spacing_glyphs": []` at :19522-19523, :19584-19585, :19647-19648.
- `DashRenderer._build_filter_widgets` (def :31899), :32213-32219 builds `_der_spacing_json_all` and `_der_spacing_glyphs_all`; :32264-32265 passes them to every callback.
- `_dash_copy_redraw_geometry`, :24941-24957; its served name at :33332 (`_glyph_layer_lines` functions tuple); its emitted call in `_generate_app_source`, :36039-36042:
  ```python
  36039            "                    # A bar's or rbar's width is the kept rows' spacing",
  36040            "                    # (GlyphMapper._tag_spacing); the redraw's glyph",
  36041            "                    # holds it, the live one the build's (WP-29 P0.18).",
  36042            "                    _dash_copy_redraw_geometry(_live, _new)",
  ```

### The refusal site (dash.ado)

`_dash_process_segment` (program at dash.ado:3454) refuses lowess's `logit` on other types naming the word as typed, then folds `bw()`, :4113-4121:

```stata
4113         if "`ptype'" != "lowess" {
4114             mata: st_local("_lt_typed", _dash_logit_typed(st_local("opts_raw")))
4115             if `: length local _lt_typed' {
4116                 mata: _dash_say("err", "option ", st_local("_lt_typed"), " not allowed")
4118                 exit 198
4120         }
4121         _dash_fold_bw "`ptype'"
```

`_dash_logit_typed` (dash_parse.mata:4986-5001, header index :128-129) reads top-level tokens with `_dash_rep_toks(opts, 0)` (:4376); `_dash_rep_optname(tok)` (:4531-4541) returns the name an option word was typed with, `""` for a non-option. Every Mata function dash.ado calls is named in `_dash_require_mata`'s `_needed` list (dash.ado:237-254; `_dash_logit_typed` at :251).

### Date units

`_dash_date_units(column, kind)` (:535) and its inverse `_dash_units_to_axis(values, kind)` (:569) convert between epoch milliseconds and Stata units ("a period kind placed at its period's start, a fraction of a period linearly between that start and the next (`%tm` 492.5 is 2001-01-16 12:00)"). Both are already in the served functions tuple (:33168-33169), as are `_STATA_MS_MIN`, `_STATA_MS_MAX` and `_STATA_EPOCH_UNIX_MS` in the constants tuple. Reserved columns: every column dash makes is `__dash<what>` (dash_render.py:3578-3584), and dash.ado refuses a user variable with that prefix (dash.ado:4777-4781).

### Measured at `c96facd` (this file's probes, 03oct2026)

dash's mappers on date x (`scratch/s14/datecheck.py`: `GlyphMapper` with `date_vars={"d": kind}`, `%td` weekly 14975+7k, `%tm` 720-722, `%tq` 160-161):

```
td bar {} width ms 483840000.0 days 5.6
td bar {'barwidth': '3'} width ms 3.0 days 3.472222222222222e-08
td rbar {} width ms 483840000.0 days 5.6
tm bar {} width ms 2004480000.0 days 23.2
tm rbar {'barwidth': '.5'} width ms 2004480000.0 days 23.2
tq bar {} width ms 6289920000.0 days 72.8
```

The same script on a simulated fix (a scratch tree carrying TR-14.1 to TR-14.6):

```
td bar {} width ms 86400000.0 days 1.0
td bar {'barwidth': '3'} width ms 259200000.0 days 3.0
td rbar {} width ms 86400000.0 days 1.0
tm bar {} x field __dash_bar_xc per-row widths days [31. 30. 30.]
tm rbar {'barwidth': '.5'} x field __dash_bar_xc per-row widths days [15.5 15.  15. ]
tq bar {} x field __dash_bar_xc per-row widths days [91.5 91. ]
```

Tooltips and glyphs on the parity frame (`scratch/s14/hovercheck.py`, saved renderer), at `c96facd` then on the simulated fix:

```
rcap    HOVER [weight, mpg, price] over ['Segment', 'Segment', 'Segment']
        -> same fields over ['Segment', 'Scatter', 'Scatter']; caps ('Scatter', size 8.0, 'dash', ['dash_cap'])
rcapsym HOVER [weight, mpg, price] over ['Segment','Segment','Segment','Scatter','Scatter']; dots size 7
        -> same fields over ['Segment', 'Scatter', 'Scatter']; dots size 8.0 (the scheme's, before S08)
rbar barwidth(.3)  VBar width 56.0 -> 0.3      bar  VBar width 56.0 -> 1
```

(The 8.0 px default and `msize(large)` = 15 px are `translate_msize`'s; after S08 both are in Stata units: 5.87 px for medium, IR-1.)

dash end to end (critic `c3.do`, re-confirmed by `p1.do`): `dash rcap lo hi x1, barwidth(.5)`, `dash rcapsym lo hi x1, barwidth(.5)`, `dash rspike lo hi x1, barwidth(.5)` and `dash rcap lo hi x1, barw(.5)` all return rc 0 with no note; `dash rcap lo hi x1, msize(large)` and `dash rbar lo hi x1, barwidth(.3)` return rc 0 with no note.

### Blast radius (E4; recorded in `<scratch>/batch-5-impact.txt` at 5.0)

`gitnexus impact <symbol> -d upstream -r dash`, 03oct2026 at `c96facd`:

| Symbol | Risk | Note |
|---|---|---|
| `DashRenderer._build_filter_widgets` | **CRITICAL** (12 impacted, 1 direct) | Deletion of :32213-32219 and :32264-32265 only. Warn before editing. |
| `FilterBuilder.build_dropdown` | **CRITICAL** (6) | Deletion of two default args only. Warn before editing. |
| `ServerAppBuilder._generate_app_source` | **HIGH** (5) | Deletion of the four emitted lines :36039-36042 only (D-14b). Warn before editing. |
| `ServerAppBuilder._glyph_layer_lines` | **HIGH** (4) | Deletion of `"_dash_copy_redraw_geometry",` (:33332) only. Warn before editing. |
| `FilterBuilder.build_slider`, `build_range` | UNKNOWN (0 resolved) | grep: one def each, called by `_dash_filter_widget`; deletion of two default args each |
| `GlyphMapper.map_bar`, `map_rbar`, `map_rcap`, `map_rcapsym` | UNKNOWN (0 resolved) | Dispatched by name at :28546-28549 through `_dash_add_glyph`; grep finds 3-7 references each. Treat as every bar and range layer, both modes. |
| `GlyphMapper._tag_spacing` | LOW (4 direct) | Deleted with its four callers |
| `_dash_copy_redraw_geometry` | UNKNOWN | grep: def :24941, name :33332, call :36042, tests in 2 files; deleted |
| `_FILTER_JS` | UNKNOWN (constant) | grep: 25 references in dash_render.py, 27 test files; only the spacing lines are deleted |
| `translate_msize` (called before S08; S08's `resolve_size` after) | CRITICAL (13) | Called, not edited |
| `_stat_option_float` | CRITICAL (36) | Called, not edited |
| `SchemeParser.default_marker_size` | UNKNOWN | Called, not edited (6 call sites by grep) |
| `_make_figure_body`, `_apply_marker_opts`, `_apply_line_opts` | CRITICAL | **Not edited** (R12: S13 edits the appliers in batch 5) |
| `_dash_process_segment` (dash.ado), `_dash_require_mata` | UNKNOWN (Stata; not indexed) | grep: one def each; S14 inserts 8 lines after :4120 and one name at :251 |

### Measured red list (simulated fix, 57 test files)

Method (index R9: a research list is re-measured, not trusted). The tree at `c96facd` was copied to scratch with `git archive HEAD`, and TR-14.1 to TR-14.6 were applied to its dash_render.py by a patch script (the dash.ado refusal and the help were not simulated). The 50 test files that name bar, rbar, rcap, rcapsym, `VBar` or `barwidth`, plus test_function_test_map.py, test_served_dates.py, test_date_units.py, test_filter_exclusion_sets.py, test_statistical_helpers.py, test_internal_column_names.py and test_varlist_expansion.py, were run with `-n 6`:
- unmodified copy: 0 failures in the first 91% (the run was stopped at its time limit);
- simulated fix: `33 failed, 13206 passed in 849.69s`. Two of the 33 (`test_help_claims_8.py::TestTheSchemeOpacityStopsWhereTheHelpSays::test_the_colour_but_not_the_opacity[rcap-saved|served]`) failed only because a cap Scatter kept Bokeh's default `fill_color` #1f77b4; with `fill_color=_rcap_color` (TR-14.4) they pass (`176 passed` over that class, test_ci_plot_index.py `TestBothModes` and test_scheme_review_fixes.py). That leaves **31 nodes**, flipped by 14-03 to 14-05 or fixed by 14-09's map edits:

| Node | Today's assertion | After (flip) |
|---|---|---|
| test_glyphs.py::TestMapRcapsym::test_rcapsym_returns_five_renderers | 5 renderers | 3 (spine, two markers) |
| test_glyphs.py::TestMapRcapsym::test_rcapsym_caps_are_segments | renderers 1, 2 are Segment | renderers 1, 2 are Scatter markers; no Segment but the spine |
| test_glyphs.py::TestMapRcapsym::test_rcapsym_dots_are_scatter | renderers 3, 4 Scatter | renderers 1, 2 Scatter |
| test_glyphs.py::TestMapRcapsymOptions::test_rcapsym_lcolor_applied_to_all_segments | spine and two caps maroon | the spine maroon and no cap Segment drawn |
| test_glyphs.py::TestMapRcapsymOptions::test_rcapsym_msize_applied_to_scatter_markers | `renderers[3].glyph.size` | `renderers[1]` and `[2]` |
| test_glyphs.py::TestMapRcapsymOptions::test_rcapsym_mcolor_applied_to_scatter_markers | `renderers[3]` fill | `renderers[1]` and `[2]` |
| test_glyphs.py::TestMapRcap::test_rcap_all_segments | three Segments | spine Segment, two Scatter caps with `marker == "dash"` |
| test_pipeline_integration.py::TestPipelineRcapsym::test_rcapsym_renders | `len(fig.renderers) >= 5` | `== 3` |
| test_ci_plot_index.py::TestBothModes::test_each_layer_takes_statas_plot_index[rarea_rcap_scatter-saved], [...-served] | `_DRAWS["rcap"]` Segment only | `_DRAWS["rcap"] = [("Segment", "rcap"), ("Scatter", "rcap")]`; the comment "rcapsym draws its caps and spike as three Segments" becomes "rcapsym draws its spike as one Segment" |
| test_date_range.py::TestAComputedLayerIsDrawnOnTheDateAxis::test_a_bar_over_dates_is_as_wide_as_their_spacing | `[0.8 * 30 * 86400000.0]` | `[86400000.0]` |
| test_emptied_layer_style.py::TestTheBarWidthFallback::test_one_rule_for_none_one_and_the_tag | bar 0.8, rbar 0.64, a `_dash_spacing` tag | 1.0 and 1.0, no tag |
| test_saved_filter_layers.py::TestTheSpacingTag::test_the_rule_is_recorded | the tag's dict | `GlyphMapper` has no `_tag_spacing`; no source is tagged |
| test_saved_filter_layers.py::TestTheSpacingTag::test_a_moved_bar_is_as_wide_as_its_kept_rows_are_spaced[bar-width], [rbar-width] | 56 then 168 | 1.0 then 1.0 |
| test_saved_filter_layers.py::TestTheCopiesAgainstHostileInput::test_the_spacing_travels_as_data_not_code | `derived_spacing_json` is a JSON string | `cb.code == _FILTER_JS` and no `derived_spacing_*` arg |
| test_served_filter_move.py::TestTheRedrawGeometry::test_a_bar_takes_the_redraws_width | live width 168 | served live width equals the redraw's, 1.0, and the app holds no `_dash_copy_redraw_geometry` |
| test_served_filter_move.py::TestTheRedrawGeometry::test_an_untagged_source_is_left_alone | untagged source unchanged | no source carries `_dash_spacing_glyphs`, in either mode |
| test_served_filter_move.py::TestTheRedrawGeometry::test_a_non_finite_or_non_positive_width_is_ignored[nan], [inf], [0], [-1], [text], [None] | width 56 kept | that spec `barwidth` draws width 1 with one note and nothing raises, both modes |
| test_served_filter_move.py::TestTheRedrawGeometry::test_extra_glyphs_are_zipped_to_the_shorter | `[168.0, 10.0]` | a graph with a bar and an rbar keeps both widths (1.0) after a served move |
| test_served_filter_move.py::TestTheServedBarAfterAMove::test_the_served_width_is_the_kept_rows_spacing[bar], [rbar] | `("value", 168.0)` | `("value", 1.0)` |
| test_view_alignment.py::TestADerivedWidthComesFromTheRowsDrawn::test_the_width_matches_the_prefiltered_width[map_rcap-varnames2], [map_rcapsym-varnames3] | "exposed no width" (no `x0_cap`) | `_bar_width` reads the cap Scatter's or the marker's `size`; equal through a qualifier and directly |
| test_function_test_map.py::test_no_entry_is_stale, ::test_every_function_has_an_entry | — | fixed by TR-14.10's entries, not flipped |

Not red on the simulated fix, though the research listed them: test_range_plots.py:125 (`test_rcap_has_caps`, 3 renderers), test_glyphs.py:1261-1263 and :1323-1335 (line options reach the Scatter caps' `line_color`), test_html_output.py, test_axis_extents.py:463 (it already reads a width field), test_scheme_review_fixes.py:376 (R5 colours), test_view_alignment.py:105-109 (`TestTheAlignedLayersStayAligned`), test_varlist_expansion.py's single-y digest. They stay as they are. Not run by pytest: `test/test_e2e_filters.cscript` EW-01 (asserts `served_after != served_before`; flipped by 14-06) and `test/filter_truth_check.py:358` `vbar_width` (a helper; unchanged, it reads a value width). S27's flips (`TestBarOptions::test_base_default_is_zero`, test_html_output.py:2020) are not S14's.

## User stories

- **US-14.1** As a twoway user, I want `dash bar y x` and `dash rbar lo hi x` to draw bars one unit of x wide, so a yearly or categorical bar chart looks as it does in Stata (bars touching) and fractional x overlaps as Stata's does.
- **US-14.2** As a twoway user, I want `dash rbar lo hi x, barwidth(.3)` to draw bars 0.3 wide, so the option I pasted from a do-file does something.
- **US-14.3** As a dashboard publisher with dates on x, I want `barwidth()` read in days on a `%td` axis and in periods on a `%tm` axis, so `barwidth(7)` on weekly `%td` data draws touching bars, as in Stata.
- **US-14.4** As a twoway user, I want `rcap ..., msize(large)` to lengthen the caps, and the default caps to match Stata's at any x spacing, so a confidence-interval plot looks like my report's.
- **US-14.5** As a twoway user, I want `rcapsym` drawn without cap lines, its markers at the scheme's symbol size, as twoway draws it.
- **US-14.6** As a dashboard reader, I want bar widths and caps to stay the same when I move a filter, on the saved page and in the served app, so the picture does not jump.
- **US-14.7** As a twoway user, I want `rcap ..., barwidth(.5)` refused as twoway refuses it, with the same message and code, so a do-file that fails in Stata does not silently succeed in dash.

## Business requirements

- **BR-14.1** A bar or range bar with no `barwidth()` is one x unit wide in both modes, before and after any filter move, whatever the spacing of x (twoway: `.plot1.bar_size` 1 at spacing .1, 1, 5 and uneven).
- **BR-14.2** `barwidth(#)` on bar and rbar is drawn # x units wide, with no note; `bw(#)` and `width(#)`, which dash already reads as `barwidth()` on these types, draw the same.
- **BR-14.3** On a date x the unit is the variable's: a day (`%td`), a millisecond (`%tc`, `%tC`), a week, month, quarter, half-year or year (`%tw`, `%tm`, `%tq`, `%th`, `%ty`), each bar spanning its own period's fraction on a period axis.
- **BR-14.4** An rcap cap is as long, in screen pixels, as a marker of the layer's `msize()` is wide (S08's units), the scheme's `symbolsize p#` by default; it does not change with the x spacing, the zoom or a filter move.
- **BR-14.5** rcapsym draws its spine and one marker at each end, no cap line; the markers' default size is the scheme's symbol size.
- **BR-14.6** `barwidth()` on rcap or rcapsym is refused with r(198) and the message `option <typed>() not allowed`, `<typed>` being the spelling given (`barw` to `barwidth`), in comma mode, in a plot group and after `||`. Nothing else is newly refused.
- **BR-14.7** The tooltips of bar, rbar, rcap and rcapsym layers are unchanged.
- **BR-14.8** The saved page and the served app draw identical widths and caps, before and after a filter move (G3).

## Technical requirements

- **TR-14.1 `GlyphMapper._bar_extent(self, xvar, xs, width)`** (new method, placed where `_tag_spacing` is deleted, after `map_bar`). Returns `(x_field, width_spec, cols)`. With `kind = (self.date_vars or {}).get(xvar)`:
  - `kind` not a Stata date kind: `(xvar, width, {})`.
  - `"td"`: `(xvar, width * 86_400_000.0, {})`; `"tc"`, `"tC"`: `(xvar, width, {})`. A product past `2 * (_STATA_MS_MAX - _STATA_MS_MIN)` is clamped to it, so the width is always finite.
  - `"tw" "tm" "tq" "th" "ty"`: `u = _dash_date_units(xs, kind)`; the unit bounds of Stata's dates `ulo, uhi = _dash_date_units(np.array([_STATA_MS_MIN, _STATA_MS_MAX]) + _STATA_EPOCH_UNIX_MS, kind)` (epoch-ms floats, which `_dash_date_units` reads as it reads a date column); `L = _dash_units_to_axis(clip(u - width/2, ulo, uhi), kind)`, `R = _dash_units_to_axis(clip(u + width/2, ulo, uhi), kind)`; returns `(self._BAR_XC, self._BAR_W, {self._BAR_XC: (L + R) / 2, self._BAR_W: R - L})` as float64 arrays (empty arrays for an empty `xs`; NaN where `u` is NaN, which draws no bar).
  - Class attributes `_BAR_XC = "__dash_bar_xc"` and `_BAR_W = "__dash_bar_w"` on `GlyphMapper` (D-14c). Never raises.
- **TR-14.2 `map_bar`.** Delete :10186-10205 (the `try`/`except` that builds `x_vals` and `_bar_numeric`, `_bar_fallback`, the gap width) and the `_tag_spacing` block :10256-10260. `bar_width = 1.0`; the `barwidth`/`width` loop (:10214-10221) stays, without its `_bar_numeric = False` line. Then `x_field, width_spec, cols = self._bar_extent(xvar, df[xvar], bar_width)`; when `cols`, `df = df.assign(**cols)` before `clean_source = ColumnDataSource(df)` (move that line below the call). `_vbar_kwargs` takes `x=x_field, width=width_spec`. The empty path (`_is_empty`) goes through the same call (its column is empty). Update the docstring ("one x unit, or barwidth(), in the variable's units on a date axis (twoway_bar.sthlp:123-133)").
- **TR-14.3 `map_rbar`.** Delete the spacing: :13043 (`x_vals`) and :13050-13055 (`_rb_fallback`, the gap width), and :13067-13068; keep `_rb_x` only as far as `_rb_sel` needs it (:13039-13040) and the subset copy (:13047-13049); rewrite the comments at :13033-13038 and :13044-13046, which describe the spacing. Read `barwidth`, then `width`, through `_stat_option_float(options, key, None, "rbar", lo=_MIN_BAR_WIDTH)` (first present key wins, a bad value noted and 1 used, as map_bar). `x_field, width_spec, cols = self._bar_extent(xvar, source.data[xvar], bar_width)`; `source.data.update(cols)` when `cols`; `_rbar_kwargs` takes `x=x_field, width=width_spec`. The empty path builds `{xvar: [], y1var: [], y2var: []}` and goes through the same call.
- **TR-14.4 `map_rcap`.** Delete `x_sorted`/`cap_hw`, `_x0_col`/`_x1_col` and their columns, and :13211-13212. `cap_px = self.scheme.default_marker_size(color_idx)`; when `"msize" in options`, `cap_px` is S08's resolver called as S08's `_apply_marker_opts` calls it for `msize()` with that default (a bad value takes S08's path: the class's medium and twoway's note, P1.12.2). The two caps are `fig.scatter(x=xvar, y=y1var|y2var, source=cap_source, marker="dash", angle=0.0, size=cap_px, line_cap="round", fill_color=_rcap_color, line_color=_rcap_color, line_width=self.scheme.plot_line_width(color_idx, ""))`, each with `r.tags = ["dash_cap"]` (P1.17.5). `_apply_line_opts` still runs on all three renderers. Returns `[spine, bot_cap, top_cap]`. No view (unchanged: the rows are taken first).
- **TR-14.5 `map_rcapsym`.** Delete `cap_hw`, the `x0_cap`/`x1_cap` columns, `_rcs_bcap_kw`/`_rcs_tcap_kw` and their two `fig.segment` calls and :13575-13576. The dots' `size=7` (:13599, :13602) becomes `size=self.scheme.default_marker_size(color_idx)`. `_apply_line_opts` runs on the spine; `_apply_marker_opts` on both dots (unchanged). Returns `[spine, bot_dot, top_dot]`; docstring: "twoway draws no cap lines (measured: 0 cap lines, 5 spines, 10 markers)".
- **TR-14.6 Remove the spacing machinery** (D-14b): `_tag_spacing` (:10292-10309); in `_FILTER_JS` the comment and `_dspacing`, `_dspacing_glyphs` and `dash_spacing` (:18737-18753) and the `_sp` block (:18769-18778), keeping the rest of the derived-copy loop byte-for-byte; the six default args at :19522-19523, :19584-19585, :19647-19648; `_build_filter_widgets` :32213-32219 and :32264-32265; `_dash_copy_redraw_geometry` (:24941-24957); `"_dash_copy_redraw_geometry",` at :33332; the four emitted lines :36039-36042. Afterwards `grep -c "_tag_spacing\|dash_spacing\|derived_spacing\|_dspacing\|_dash_copy_redraw_geometry\|_dash_spacing" dash_render.py` prints 0.
- **TR-14.7 Mata `_dash_barwidth_typed(opts)`** in dash_parse.mata directly after `_dash_logit_typed` (:5001): over `toks = _dash_rep_toks(opts, 0)`, the first `nm = _dash_rep_optname(toks[i])` with `strpos(toks[i], "(")` and `anyof(("barw", "barwi", "barwid", "barwidt", "barwidth"), nm)` is returned; else `""`. Header index entry after `_dash_logit_typed`'s (:128-129): `_dash_barwidth_typed(opts)` / "The first word spelling barwidth() as typed (refused on rcap and rcapsym)." Added to `_needed` after `_dash_logit_typed` (dash.ado:251).
- **TR-14.8 The refusal** in `_dash_process_segment`, inserted after :4120 and before `_dash_fold_bw` (:4121):
  ```stata
  // barwidth() on rcap and rcapsym: refused naming the spelling as typed,
  // as twoway refuses it -- "option barw() not allowed", r(198) (measured
  // 03oct2026; WP-30 P1.17a).  bw() is left to _dash_fold_bw.
  if inlist("`ptype'", "rcap", "rcapsym") {
      mata: st_local("_bwt_typed", _dash_barwidth_typed(st_local("opts_raw")))
      if `: length local _bwt_typed' {
          mata: _dash_say("err", "option ", st_local("_bwt_typed"), "() not allowed")
          exit 198
      }
  }
  ```
  The echoed word is one of five fixed spellings, so no user text reaches the message.
- **TR-14.9 Served copy lists (R2).** No name is added. `"_dash_copy_redraw_geometry",` is removed from the functions tuple (D-14b). `_bar_extent`, `_BAR_XC` and `_BAR_W` travel with `GlyphMapper` (class loop, :33436). `_dash_date_units`, `_dash_units_to_axis`, `_dash_float_values` and the `_STATA_*` constants are already copied. `test_every_listed_name_exists` (S01) and `TestTheServedAppDefinesEveryNameItReads` stay green.
- **TR-14.10 Maps (A148).** test/function_test_map.py: delete `'GlyphMapper._tag_spacing'` (:201) and `'_dash_copy_redraw_geometry'` (:636); add under `# WP-30 S14 (P1.17a): Bar widths and range caps` `'GlyphMapper._bar_extent': 'test/test_bar_range_geometry.py::TestTheBarExtent::test_each_kind'`. test/program_coverage_map.py, under S14's `COVERAGE["dash_parse.mata"]` anchor: `"_dash_barwidth_typed": ("test_twoway_option_parity.cscript:BG-07",)`.
- **TR-14.11 JS twins.** None added: no width is computed in the page's script any more. The derived-copy loop of `_FILTER_JS` copies `__dash_bar_xc`/`__dash_bar_w` with every other column of a kept row.
- **TR-14.12 Security (rule 1).** The removal deletes the only `_FILTER_JS` path that wrote data columns and a glyph property named by page JSON (`_sp.cols`, `_g.width`). The new columns are dash's own, under the reserved prefix. The refusal echoes a fixed spelling through `_dash_say`. No `shell=True`, no `eval`, no new text sink.

## Boundaries

- **S27 (batch 9) owns the default base** (A3-c, A3-f): `base_val`, the `bottom` of map_bar, `y0` of spike and dropline, `<y>_base` of area, `_dash_finish_auto_bases`, the hull. S14 leaves every `base` line as it is, and dash.sthlp:2358-2368 (`base()`) unchanged.
- **S13 (same batch)** owns `_apply_line_opts`, `_apply_marker_opts`' `mlwidth`, `_LWIDTH_MAP` and line widths. The caps' `line_width` stays `plot_line_width(color_idx, "")` and `_apply_line_opts` runs after it.
- **S15 (same batch)** owns the scheme extractor, the 26 scheme files and `scheme_truth.json`. S14 reads `symbolsize` through `default_marker_size` and regenerates nothing.
- **S08** owns `resolve_size`, `translate_msize` and `_apply_marker_opts`' `msize`; S14 calls them.
- **S24 (batch 8)** owns the default alpha of range and spike construction sites and the p# symbol cycle on rcapsym. **S11/S20** own `_dash_fold_bw` and per-series `barwidth()` lists (rbar `barwidth()` lists stay refused as twoway refuses them, BR-30.1). **S45** owns `recast(bar)`, which calls map_bar's rule. **S49/S55** own `horizontal`: S14 only tags caps `dash_cap`.
- **S21 (batch 7)** owns the hull, natscale and `_DASH_AXIS_FINISH_JS`.
- Not touched: `_make_figure_body`, `_build_sources_and_figures`, `_dash_fold_bw`, `_dash_option_rules` (dash's own `barwidth > 0` bound stays; twoway accepts `barwidth(0)` and `barwidth(-1)`, research §3; P2.21), `bw()` on non-bar types (named in the note, unchanged), `barwidth()` on rspike, rscatter, rarea, rline, rconnected, scatter and line (outside this area, D-14a), `spike barwidth()` (accepted by both), the tracking documents (A145).

## Stata truth

**New extractor** `scripts/extract_bar_geometry_truth.do`, in S02's path-free form (A128/A130: the tree from `DASH_REPO`, else `c(pwd)` when it holds dash.ado), opening with `adopath ++ "<repo>/"` and `global dash_nobrowser 1`; run only as:

```sh
DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s14/x $WT/scripts/extract_bar_geometry_truth.do
```

It writes `test/fixtures/bar_geometry_truth.json` (`git add -f`), with `_meta` = `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit` (`git rev-parse HEAD` written by `shell` to a file in the work directory, read by the python block; never `shell=True`), `extracted` (`c(current_date) c(current_time)`). It is twoway-only (it never runs dash), so it is the same before and after the fix. A trailing `python:` block reads every SVG with `scripts/svg_truth.py` (`svg_document`, `svg_lines`, `svg_axis_reading`) and writes the JSON; every SVG is erased. All graphs `set scheme s2color` unless named; data are typed with `input`:

```
x1 xp1 x5 xu  y  lo hi  d(%td, 14975 + 7k)  dd(%td, 14975 + k)  m(%tm, 720 + k)   k = 0..4
1  .1  5  1   3  1  4
2  .2  10 1.5 4  2  5
3  .3  15 4   2  1  3
4  .4  20 10  5  3  6
5  .5  25 11  1  0  2
```

| Key | twoway command | Recorded |
|---|---|---|
| `widths.bar_s1`, `bar_s01`, `bar_s5`, `bar_su` | `twoway bar y x1` / `xp1` / `x5` / `xu` | `.Graph.plotregion1.plot1.bar_size`; SVG rect widths ÷ px per x unit (`svg_axis_reading` on the labelled x ticks) |
| `widths.rbar_s1`, `rbar_s5`, `rbar_bw03` | `twoway rbar lo hi x1` / `x5` / `x1, barwidth(.3)` | the same |
| `widths.bar_td_weekly`, `bar_td_weekly_bw3`, `bar_td_daily` | `twoway bar y d` / `d, barwidth(3)` / `dd` | `bar_size`; SVG width in days |
| `widths.bar_tm`, `bar_tm_bw05`, `rbar_tm` | `twoway bar y m` / `m, barwidth(.5)`, `rbar lo hi m` | `bar_size`; SVG width in months |
| `caps.rcap_<m>` for m in `default tiny small medium large vlarge n2 x2` | `twoway rcap lo hi x1[, msize(m)]` (`n2` = `msize(2)`, `x2` = `msize(*2)`) | cap length (horizontal `<line>`s of the plot's stroke), canvas W and H, `ratio = 100 * cap / min(W, H)`, `.plot1.style.marker.size.val` |
| `caps.rcap_s5`, `rcap_wide`, `rcap_stcolor` | `rcap lo hi x5`; `rcap lo hi x1, xsize(11) ysize(4)`; `rcap lo hi x1, scheme(stcolor)` | the same |
| `rcapsym.default`, `rcapsym.stcolor` | `twoway rcapsym lo hi x1[, scheme(stcolor)]` | horizontal cap lines (0), spines, markers, `marker.size.val` |
| `refusals.<type>` for rcap rcapsym rspike rscatter rarea rline rconnected scatter line spike dropline area; `refusals.rcap_barw`, `rcap_barwi`, `rcap_bw` | `capture noisily twoway <type> <vars>, barwidth(.5)`; `rcap ..., barw(.5)` / `barwi(.5)` / `bw(.5)` | rc and the message line |

**Measured values** (research t1.do-t5.do and this file's `p1.do`/`p2.do`, StataNow 19.5, run through the slot 03oct2026):

```
bar_size: bar x1/xp1/x5/xu 1 (SVG 0.9999-1.0001 x units); rbar 1; rbar barwidth(.3) .3
%td: bar_size 1 (daily and weekly; SVG 0.9999 days); barwidth(3) 3 (2.9999 days)
%tm: bar 1.0 month; barwidth(.5) .5; rbar 1.0
rcap cap (SVG units, canvas 3960x2880, min 2880):
  default 44.06 | medium 44.06 | tiny 10.02 | small 29.95 | large 70.04 | vlarge 89.97 | msize(2) 57.55
  spacing 5: 44.06 | xsize(11) ysize(4) (7920x2880): 44.06 | stcolor (5400x3240): 33.75
marker.size.val: rcap and rcapsym s2color 1.52778, stcolor 1.04166; rcapsym large 2.4306; rcap msize(*2) 3.05556
rcapsym: 0 cap lines, 5 spines, 20 circles (10 markers as fill + outline)
refusals: "option barwidth() not allowed" r(198) on rcap rcapsym rspike rscatter rarea rline rconnected scatter line;
          rc 0 on spike dropline area; rcap barw(.5) "option barw() not allowed"; rcap bw(.5) "option bw() not allowed"
```

The rule: a cap is as long as a marker of the same `msize` is wide (44.06 = 2 × 22.03, the stroke-centre radius of an `msize(medium)` circle in the same graph; critic c1), `ratio` = the msize in Stata's relative units of min(W,H)/100 (44.06/28.8 = 1.530; 70.04/28.8 = 2.432).

**Truth block** (R1): in `test/test_wp30_truth.cscript`, between S01's `S14 start`/`S14 end` lines, under S01's stub header `* ==== S14 P1.17a: Bar widths and range caps ====` (the manifest's name less its parenthesis, as TR-01.6 writes it; never retyped); its python helpers (`_bg_widths(sp, dp)`, `_bg_caps(sp, dp)`, `_bg_move(sp, dp, app)`; `_bg_` prefix) sit directly above that header at top level, holding no brace inside the gate. Each case registers with `dash ..., name(zbgK)`, writes its spec with `_dash_serve_spec, specpath() datapath()` and compares the saved renderer and the generated app (as `test/test_wp29_truth.cscript` EW-02 does) with twoway's own value from the same run:
- **BG-01** bar at x spacing .1, 1, 5 and uneven: dash's VBar width, saved and served, equals `.plot1.bar_size` (1).
- **BG-02** rbar default, `barwidth(.3)` and `bw(.3)`: width equals `bar_size` (1, .3, .3), both modes; the logged output of each `dash` call holds no `(note:`.
- **BG-03** `%td` weekly default and `barwidth(3)`, `%tm` default and `barwidth(.5)`: dash's width in the variable's units (ms ÷ 86,400,000; for `%tm` `_dash_date_units(R) - _dash_date_units(L)` per row) equals `bar_size`, both modes.
- **BG-04** rcap default, `msize(small)`, `msize(large)`, `msize(*2)`: twoway's `ratio` is `marker.size.val` within 1%; dash's cap Scatter (marker `dash`) has the size dash gives a `scatter ..., msize(same)` marker, both modes; the same at x spacing 5.
- **BG-05** rcapsym: twoway's SVG has 0 horizontal cap lines; dash draws Segment, Scatter, Scatter in both modes, the Scatters at dash's default scatter size.
- **BG-06** served move: `dash bar mpg weight, filter(foreign)` on the parity frame: the served VBar is 1 wide before and after the Foreign move (generated app, the Select's callback fired as UL-08 fires it).

**Refusal cases** (R1; C7 area script for plot-option refusals, where TP-15 refuses `logit`): `test/test_twoway_option_parity.cscript`, appended as one contiguous run after its last case block and before `// Summary`, with header lines `*! BG-07..BG-09` added to the script's case list:
- **BG-07** `dash rcap lo hi x1, barwidth(.5)` and `dash rcapsym lo hi x1, barwidth(.5)`, in comma mode, as `dash (rcap lo hi x1, barwidth(.5))` and as `dash scatter hi x1 || rcap lo hi x1, barwidth(.5)`: rc 198 and the error line equals twoway's own (`capture noisily twoway ...` in the same run, both logged).
- **BG-08** `barw(.5)`, `barwi(.5)`, `barwidth(.5)` on rcap: dash's line names the spelling typed, equal to twoway's.
- **BG-09** guards: `dash bar`, `rbar`, `spike ..., barwidth(.5)` rc 0; `dash rcap lo hi x1, legend(label(1 "barwidth(2)"))` rc 0 (quoted and nested text is not read); `dash rcap lo hi x1, bw(.5)` keeps today's note (unchanged).

`EW-01` in `test/test_e2e_filters.cscript` is flipped in place (Tests that pin today's behaviour).

## TDD test stubs

### Regression tests, `test/test_bar_range_geometry.py` (new; red at `c96facd` unless marked guard)

Helpers: `_figs(mode, spec, df, formats=None)` (saved: `DashRenderer(...).render()` figures; served: `ServerAppBuilder.build` then `make_document`, as test_date_range.py `_saved`/`_served`); `plot_for` from test_server_layer_defects; moves through test_saved_filter_layers `_render`/`_move`/`_MOVES` (the page's own `_FILTER_JS` under node) and test_mode_parity `_served_after_move`; the fixture read once at module level. Every class that draws is parametrized `mode in ("saved", "served")`.

- Test: the fixture exists, carries the four `_meta` keys and every key of the Stata truth table — `TestTheFixture::test_meta_is_stamped`, `::test_every_case_was_measured` (guard after 14-01).
- Test: bar and rbar at x spacing .1, 1, 5 and uneven are as wide as twoway's `bar_size` — `TestBarIsOneXUnit::test_the_width_is_twoways[mode-type-case]` (red: 0.8 × gap).
- Test: rbar `barwidth` and `width` keys draw 0.3 — `TestRbarReadsBarwidth::test_the_option_is_drawn[mode-key]` (red); no note is raised — `::test_no_note` (guard).
- Test: `_bar_extent` for no kind, td, tc, tC and each period kind — `TestTheBarExtent::test_each_kind` (red: AttributeError); an empty column keeps the field form — `::test_an_empty_column`; `barwidth(1e305)` on `%td` and `barwidth(1e9)` on `%tm` stay finite — `::test_a_width_past_statas_dates_stays_finite` (red).
- Test: a `%td` bar is one day by default and three with `barwidth(3)`; `%tc` one millisecond — `TestBarwidthOnADateAxis::test_td_default_is_a_day`, `::test_td_barwidth_is_days`, `::test_tc_is_a_millisecond` (red).
- Test: a period bar spans `_dash_units_to_axis(u ± w/2)` for tw, tm, tq, th, ty, and the fixture's `%tm` `bar_size` — `::test_a_period_bar_spans_its_period[mode-kind]`, `::test_rbar_on_a_period_axis` (red).
- Test: an empty `%tm` layer is drawn from `__dash_bar_xc`/`__dash_bar_w` — `::test_an_empty_period_layer_keeps_the_field_form` (red).
- Test: a saved move and a served move leave bar and rbar widths at 1 and a `%tm` bar's columns equal to the kept rows' — `TestTheWidthHoldsAcrossAMove::test_saved[type]`, `::test_served[type]`, `::test_a_period_bar_after_a_saved_move` (red: 56 → 168).
- Test: rcap's caps are Scatter, `marker == "dash"`, `angle == 0`, `line_cap == "round"`, tagged `dash_cap` — `TestRcapCapsAreScreenUnits::test_caps_are_dash_markers[mode]` (red).
- Test: a cap is as long as a `map_scatter` marker of the same `msize()` (tiny, small, medium, large, vlarge, 2, `*2`) — `::test_the_cap_is_a_marker_of_its_msize[mode-m]` (red).
- Test: the default cap is `scheme.default_marker_size(i)` under s2color and stcolor — `::test_the_default_is_the_schemes_symbol_size[mode-scheme]` (red).
- Test: the cap size is the same at x spacing 1 and 5, and after a move in both modes — `::test_the_cap_does_not_follow_the_x_spacing`, `::test_the_caps_are_unchanged_by_a_move` (red).
- Test: twoway's cap ratio is its marker size (fixture only) — `::test_twoways_cap_is_its_msize` (guard).
- Test: the caps (the renderers tagged `dash_cap`) take `color p#`, not `p#mark`, under a user scheme where they differ — `::test_the_caps_take_the_p_line_colour[mode]` (red: no renderer is tagged).
- Test: BokehJS's `dash` marker is drawn `size` long (reads `_one_line` from the installed `bokeh/server/static/js/bokeh.js`) — `::test_the_dash_marker_is_as_long_as_its_size` (guard).
- Test: rcapsym draws Segment, Scatter, Scatter with markers at the scheme's size — `TestRcapsymDrawsNoCaps::test_spine_and_two_markers[mode]`, `::test_the_markers_take_the_schemes_size[mode]` (red).
- Test: no source carries `_dash_spacing`; `_FILTER_JS` holds no `dash_spacing`/`derived_spacing`; no callback has a `derived_spacing_*` arg; the generated app and module hold no `_dash_copy_redraw_geometry`; `GlyphMapper` has no `_tag_spacing` — `TestTheSpacingMachineryIsGone::test_no_mapper_tags_a_source[mode]`, `::test_the_page_script_holds_no_spacing_writer`, `::test_no_callback_carries_spacing_args`, `::test_the_served_app_holds_no_geometry_copier` (red).
- Test: tooltips of bar, rbar, rcap, rcapsym keep their fields in both modes — `TestTheTooltipsAreUnchanged::test_the_fields[mode-type]` (guard).

### Cases in cscripts

- `test_wp30_truth.cscript` BG-01..BG-06 (red at base except the twoway half of BG-04).
- `test_twoway_option_parity.cscript` BG-07, BG-08 (red), BG-09 (guard).

### Flips (in place, each with a `Flipped:` line; red at base after the flip)

Listed under Evidence "Measured red list". Each keeps its node name; its docstring gains the reason "twoway draws a bar one x unit wide, and caps as long as a marker of its msize (P1.17a)".

### Parity corpus (R8; appended, guards at base)

`test/test_mode_parity.py`, under `# WP-30 P1.17a: bar widths and range caps`: `CORPUS` cases "rbar barwidth(.3)", "rcap msize(large)", "rcapsym", "bar on a %tm x"; `MOVE_CORPUS` cases "rcap msize(large), dropdown" and "bar on a %tm x, range" (the frame gains a `%tm` column only in the cases' own spec; `_DF` is not edited). The comment at :2490 becomes "bar and rbar widths hold through a move (WP-30 P1.17a)". `ALLOWED` and `_MUST_WARN` are not edited.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Widths at four spacings, bar and rbar | pytest `TestBarIsOneXUnit`; cscript BG-01 | `bar_geometry_truth.json` `widths` | yes |
| rbar `barwidth()`, `bw()`, `width()`, no note | pytest `TestRbarReadsBarwidth`; BG-02 | `widths.rbar_bw03` | yes |
| Date units (td, tc, tw-ty), empty period layer | pytest `TestBarwidthOnADateAxis`, `TestTheBarExtent`; BG-03 | `widths.bar_td_*`, `bar_tm*` | yes |
| Widths after a move | pytest `TestTheWidthHoldsAcrossAMove` (node and served `_on_filter_change`); BG-06; EW-01 flipped; `MOVE_CORPUS` | — | yes |
| Caps from `msize()`, default, screen units | pytest `TestRcapCapsAreScreenUnits`; BG-04 | `caps.*` | yes |
| rcapsym without caps | pytest `TestRcapsymDrawsNoCaps`; BG-05 | `rcapsym.*` | yes |
| The machinery is gone | pytest `TestTheSpacingMachineryIsGone`; registry tests (R2) | — | yes |
| Refusal | cscript BG-07..BG-09 | `refusals.*` (documentation; the cscript compares live) | n/a (Stata) |
| Tooltips | pytest `TestTheTooltipsAreUnchanged` | — | yes |
| Parity | `python3 -m pytest test/test_mode_parity.py -q -n0` (G3) | — | yes |

**Acceptance criteria**
- **AC-14.1** For every `widths` record, dash's width in x units equals twoway's `bar_size` to 1e-9, saved and served, before and after a move.
- **AC-14.2** `barwidth(.3)` on rbar draws 0.3 in both modes with no note.
- **AC-14.3** On `%td` the default width is 86,400,000 ms and `barwidth(3)` is 259,200,000; on `%tm`, `%tq`, `%tw`, `%th`, `%ty` each bar's edges equal `_dash_units_to_axis(u ± w/2)` to 1 ms; no width is ever non-finite.
- **AC-14.4** Every rcap cap is a `dash` Scatter, tagged `dash_cap`, of the size dash gives a marker of the same `msize()`, equal at x spacing 1 and 5 and after a move; twoway's fixture ratio equals its `marker.size.val` within 1% for all eleven records.
- **AC-14.5** rcapsym returns three renderers (Segment, Scatter, Scatter) at the scheme's marker size.
- **AC-14.6** `barwidth()` in any spelling on rcap or rcapsym is refused r(198) with the line twoway prints, in three forms; bar, rbar and spike are not refused.
- **AC-14.7** `grep -c "_tag_spacing\|dash_spacing\|derived_spacing\|_dash_copy_redraw_geometry" dash_render.py` prints 0, and the registry tests are green.
- **AC-14.8** `test_wp30_truth.cscript` under `WP30_ONLY=S14` prints BG-01..BG-06 PASS; `test_twoway_option_parity.cscript` prints BG-07..BG-09 PASS and ALL CHECKS PASSED; `test_e2e_filters.cscript` prints EW-01 PASS; no SKIP.
- **AC-14.9** One full run through the queue is green before the commit.

## Tasks

**Commit boundary.** Tasks 14-01 to 14-13 form the one P1.17a commit, subject `Draw bars one x unit wide and range caps from msize(), as twoway does (WP-30 P1.17a)`, made by 14-13 on `wp30-s14` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s14`, after one full run through the queue.
- The body opens with `<scratch>/14-P1.17a-failure.txt`, then the measured defect, then what changed where (both modes; the machinery removed; D-14b's template deletion named).
- One line each of:
  - `Regression: test/test_bar_range_geometry.py::<Class>::<test> -- failed at <batch-5 base sha> with <text>`, and `Regression: test/test_wp30_truth.cscript BG-0k`, `test/test_twoway_option_parity.cscript BG-0k`;
  - `Flipped: <node> -- <old expectation> was wrong because twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a)` (one per flip, from `<scratch>/s14/14-flips.txt`);
  - `Fixture: test/fixtures/bar_geometry_truth.json (scripts/extract_bar_geometry_truth.do)`;
  - `BUGS.md: "<title>" (closed)`.

Every command runs from `$WT`. No body, BUGS or CHANGELOG line names a tool or vendor (G7).

<task type="auto" id="14-01">
  <name>Measure twoway and write failing tests</name>
  <files>scripts/extract_bar_geometry_truth.do, test/fixtures/bar_geometry_truth.json, test/test_bar_range_geometry.py</files>
  <action><![CDATA[
    Check the cut: `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-5-base.txt` and `git -C $WT branch --show-current` prints `wp30-s14`; `mkdir -p <scratch>/s14/x`. Confirm `<scratch>/batch-5-impact.txt` holds the Evidence "Blast radius" rows with the maintainer's approval of the CRITICAL/HIGH rows and of D-14b; if D-14b was struck, follow its fallback in 14-09 and 14-04. Create scripts/extract_bar_geometry_truth.do by the "Stata truth" table (copy the path-free head of an extractor S02 converted, e.g. scripts/extract_emptied_layer_truth.do), run it through the slot, and `git add -f test/fixtures/bar_geometry_truth.json`. Check that its values match "Measured values" (bar_size 1, caps 44.06/70.04 within 0.1, rcapsym 0 cap lines); a mismatch stops the task. Create test/test_bar_range_geometry.py with exactly the classes and tests of "TDD test stubs / Regression tests" (module docstring: the defect, the probe commands, the twoway table). Run `python3 -m pytest test/test_bar_range_geometry.py -q -n0 -p no:cacheprovider -rf > <scratch>/s14/14-01.log 2>&1` and write `<scratch>/14-P1.17a-failure.txt`: the base sha, each failing node with its one-line reason, then the guards that passed. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/bar_geometry_truth.json'));print(sorted(d['_meta']))"` prints `['born_date', 'dash_commit', 'extracted', 'stata_version']`; `grep -c FAILED <scratch>/s14/14-01.log` is at least 30; `grep -c "TestTheFixture\|TestTheTooltipsAreUnchanged\|test_twoways_cap_is_its_msize" <scratch>/s14/14-01.log` shows no FAILED line for them; `test -s <scratch>/14-P1.17a-failure.txt`.]]></verify>
  <done>twoway's widths, caps and refusals were recorded in a stamped fixture, and every regression test was shown failing on the unmodified tree with its failure text saved.</done>
</task>

<task type="auto" id="14-02">
  <name>Write the BG truth and refusal cases</name>
  <files>test/test_wp30_truth.cscript, test/test_twoway_option_parity.cscript</files>
  <action><![CDATA[
    In test_wp30_truth.cscript, add the `_bg_` python helpers directly above `* ==== S14 P1.17a:` (top level, no brace inside the gate) and write BG-01 to BG-06 of "Stata truth / Truth block" between S01's `S14 start` and `S14 end` lines, each ending with S01's done helper (`_w30_done BG-0k "<what>"`), its expectations through `_w30_expect`. Every file goes under the scaffold's work directory and is erased at the end; `dash clear` and `set scheme` are restored. In test_twoway_option_parity.cscript, append BG-07 to BG-09 as one run after the last case block and before `// Summary`, in the script's `nfail`/`faillist` form, each comparing dash's logged error line with twoway's from the same run; add `*! BG-07..BG-09` lines to its header list. Run both through the driver (index "The cscript driver"; `WP30_ONLY=S14` for the truth script) on the unmodified tree and append the FAIL lines to `<scratch>/14-P1.17a-failure.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c "BG-0[1-6] FAIL" <scratch>/s14/run_test_wp30_truth.log` prints 6 (BG-04's twoway half holds; its dash half fails); `grep -c "BG-0[78] FAIL" <scratch>/s14/run_test_twoway_option_parity.log` prints 2 and `grep -c "BG-09 PASS" <scratch>/s14/run_test_twoway_option_parity.log` prints 1; `grep -c "SKIP" <scratch>/s14/run_test_wp30_truth.log` prints 0.]]></verify>
  <done>Stata's own drawing and refusals were compared with dash's in cases that failed on the unmodified tree, and the guard case passed.</done>
</task>

<task type="auto" id="14-03">
  <name>Flip the glyph and pipeline pins</name>
  <files>test/test_glyphs.py, test/test_pipeline_integration.py, test/test_ci_plot_index.py</files>
  <action><![CDATA[
    Flip, in place and keeping every node name, the ten nodes of these three files in Evidence "Measured red list" (seven in test_glyphs.py, one in test_pipeline_integration.py, two parametrized ids of one test in test_ci_plot_index.py, whose `_DRAWS["rcap"]` and dedup comment change), each to the "After" column. Add to each flipped docstring "Flipped (WP-30 P1.17a): twoway draws rcap caps as long as a marker of its msize, and rcapsym none." Do not touch `TestBarOptions::test_base_default_is_zero` (S27's) or any node not in the table. Append one `Flipped: <node> -- <old> was wrong because <why>` line per node to `<scratch>/s14/14-flips.txt`. Run the three files on the unmodified renderer and append their red nodes under `Pinned, red at base after the flip` to `<scratch>/14-P1.17a-failure.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_glyphs.py test/test_pipeline_integration.py test/test_ci_plot_index.py -q -p no:cacheprovider` reports exactly 10 failed, all in the table; `grep -c "^Flipped: test/test_glyphs.py" <scratch>/s14/14-flips.txt` prints 7.]]></verify>
  <done>The glyph, pipeline and plot-index pins asserted Scatter caps and a capless rcapsym, with each flip recorded.</done>
</task>

<task type="auto" id="14-04">
  <name>Flip the move and fallback pins</name>
  <files>test/test_saved_filter_layers.py, test/test_served_filter_move.py, test/test_emptied_layer_style.py</files>
  <action><![CDATA[
    test_saved_filter_layers.py: `TestTheSpacingTag::test_the_rule_is_recorded` → asserts `not hasattr(dr.GlyphMapper, "_tag_spacing")` and that a bar and an rbar source carry no `_dash_spacing`; `test_a_moved_bar_is_as_wide_as_its_kept_rows_are_spaced` → width 1.0 before and after the move; `TestTheCopiesAgainstHostileInput::test_the_spacing_travels_as_data_not_code` → `cb.code == dr._FILTER_JS` and no `derived_spacing_json`/`derived_spacing_glyphs` key in `cb.args`. test_served_filter_move.py: delete only the helper `_spaced`; flip `TestTheRedrawGeometry`'s four nodes to assert through `tp._served_after_move` and the generated source that the redraw's widths equal the live ones (1.0), that no source carries `_dash_spacing_glyphs`, that a hand-written spec `barwidth` of nan, inf, 0, -1, text or None draws width 1 with one note and raises nothing in either mode, and that a graph with a bar and an rbar keeps both widths after the move; `TestTheServedBarAfterAMove::test_the_served_width_is_the_kept_rows_spacing` → `("value", 1.0)`. test_emptied_layer_style.py `TestTheBarWidthFallback::test_one_rule_for_none_one_and_the_tag` → bar and rbar width 1.0 with 0 and 1 rows and no `_dash_spacing`. Record each flip; run the three files on the unmodified renderer and append the red nodes.
  ]]></action>
  <verify><![CDATA[`grep -c "_dash_spacing_glyphs\[0\].width == 168\|== pytest.approx(168.0)\|approx(0.64)" test/test_saved_filter_layers.py test/test_served_filter_move.py test/test_emptied_layer_style.py` prints 0 for each file; the three files fail on the unmodified renderer exactly in the flipped nodes.]]></verify>
  <done>The WP-29 P0.18 pins asserted invariant widths and the absence of the spacing machinery, keeping their node names and robustness intent.</done>
</task>

<task type="auto" id="14-05">
  <name>Flip the date and alignment pins</name>
  <files>test/test_date_range.py, test/test_view_alignment.py</files>
  <action><![CDATA[
    test_date_range.py `test_a_bar_over_dates_is_as_wide_as_their_spacing` → `widths == [86400000.0]` (one day; twoway's `bar_size` 1, fixture `widths.bar_td_daily`), its docstring updated. test_view_alignment.py: `_bar_width` also returns a cap Scatter's `size` (marker `dash`) and an rcapsym marker's `size`; `TestADerivedWidthComesFromTheRowsDrawn`'s docstring says no width or cap is derived from the rows any more, so a qualifier never changes one; its four parametrized cases stay. Record each flip as in 14-03 and run the two files on the unmodified renderer.
  ]]></action>
  <verify><![CDATA[`grep -c "0.8 \* 30 \* 86400000" test/test_date_range.py` prints 0; the two files fail on the unmodified renderer in exactly the three nodes of the table (the date node and two `test_the_width_matches_the_prefiltered_width` ids, whose rcap and rcapsym widths are still the gap's).]]></verify>
  <done>The date and alignment pins expected twoway's day-wide bar and screen-unit caps.</done>
</task>

<task type="auto" id="14-06">
  <name>Flip EW-01 and append parity cases</name>
  <files>test/test_e2e_filters.cscript, test/test_mode_parity.py</files>
  <action><![CDATA[
    EW-01 (test_e2e_filters.cscript:590-633): header comment and PASS line say the served bar is 1 wide before and after the move, as the saved page draws it after the move and from the Foreign rows alone; `ftc.put("ew_01", int(saved_after == served_after == saved_qual == served_before == 1.0))`. In test_mode_parity.py append the `CORPUS` and `MOVE_CORPUS` cases of "TDD test stubs / Parity corpus" and rewrite the comment at :2490; nothing else. Record the flip; run `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "P1.17a or rcap or rcapsym or rbar or tm"` on the unmodified renderer (the new cases are guards: both modes draw alike) and EW-01 through the driver (red).
  ]]></action>
  <verify><![CDATA[The parity run reports 0 failed; `grep -c "EW-01 FAIL\|assertion is false" <scratch>/s14/run_test_e2e_filters.log` is at least 1; `grep -c "WP-30 P1.17a" test/test_mode_parity.py` prints at least 2.]]></verify>
  <done>The end-to-end width case expected an invariant width, and the parity corpus held the new geometry in both modes.</done>
</task>

<task type="auto" id="14-07">
  <name>Draw bars one x unit wide</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn (CRITICAL/HIGH rows are not edited here). Add `GlyphMapper._BAR_XC`, `_BAR_W` and `_bar_extent` per TR-14.1, then make TR-14.2 (map_bar) and TR-14.3 (map_rbar). Do not touch `base_val`, `bottom`, the colour or line code, `_apply_fill_opts`, `_apply_line_opts`, `_apply_mlabel_opts` or the empty-layer styling. Run `python3 -m pytest test/test_bar_range_geometry.py -q -n0 -p no:cacheprovider -k "BarIsOneXUnit or RbarReads or BarExtent or DateAxis"` and the 14-03..14-05 files.
  ]]></action>
  <verify><![CDATA[Those classes pass; `grep -n "0.8 \* min\|_bar_fallback\|_rb_fallback" dash_render.py` prints nothing; `python3 -m pytest test/test_internal_column_names.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>bar and rbar were drawn one x unit wide or barwidth() wide, in the variable's units on a date axis, on every path in both modes.</done>
</task>

<task type="auto" id="14-08">
  <name>Draw caps from msize, rcapsym without</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-14.4 (map_rcap) and TR-14.5 (map_rcapsym). Read S08's `_apply_marker_opts` at the batch-5 base and copy its `msize()` resolver call verbatim for `cap_px` (D-14e); do not edit `_apply_marker_opts` or `_apply_line_opts` (S13's, R12). Tag both cap renderers `["dash_cap"]`. Run `python3 -m pytest test/test_bar_range_geometry.py -q -n0 -p no:cacheprovider -k "Rcap or Tooltips"` and test_glyphs.py, test_pipeline_integration.py, test_ci_plot_index.py, test_range_plots.py, test_scheme_review_fixes.py and test_help_claims_8.py (the last three are guards that stay green).
  ]]></action>
  <verify><![CDATA[Those runs report 0 failed; `sed -n "/def map_rcapsym/,/def map_scatteri/p" dash_render.py | grep -c "size=7\|fig.segment"` prints 1 (the spine's `fig.segment`); `sed -n "/def map_rcap(/,/def map_rline/p" dash_render.py | grep -c 'marker="dash"'` prints 2.]]></verify>
  <done>rcap's caps became dash markers sized as markers of their msize() in screen units, and rcapsym drew no caps, its markers at the scheme's size.</done>
</task>

<task type="auto" id="14-09">
  <name>Remove the spacing machinery</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Warn before editing `_build_filter_widgets` and `build_dropdown` (CRITICAL), `_glyph_layer_lines` and `_generate_app_source` (HIGH). Make TR-14.6: delete exactly the lines it names and nothing else in those symbols; the derived-copy loop of `_FILTER_JS` keeps every other line byte-for-byte. Make TR-14.10's function_test_map.py edits under S14's anchor. Run test_saved_filter_layers.py, test_served_filter_move.py, test_emptied_layer_style.py, `test/test_bar_range_geometry.py -k "Machinery or Holds"`, test_function_test_map.py, test_program_coverage_map.py, `"test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName"` and `"test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads"`.
  ]]></action>
  <verify><![CDATA[`grep -c "_tag_spacing\|dash_spacing\|derived_spacing\|_dspacing\|_dash_copy_redraw_geometry\|_dash_spacing" dash_render.py` prints 0; every run above reports 0 failed.]]></verify>
  <done>The spacing machinery was gone from the mappers, the page script, the filter builders and the served app, and widths held through moves in both modes.</done>
</task>

<task type="auto" id="14-10">
  <name>Refuse barwidth on rcap and rcapsym</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    Add `_dash_barwidth_typed` and its header-index entry (TR-14.7), add it to `_needed` after `_dash_logit_typed` (dash.ado:251), and insert TR-14.8's block in `_dash_process_segment` after the logit refusal and before `_dash_fold_bw`. Add TR-14.10's program_coverage_map.py entry under S14's anchor. Run test_twoway_option_parity.cscript through the driver, then `python3 -m pytest test/test_program_coverage_map.py test/test_option_validation.py -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[`grep -c "BG-0[789] PASS" <scratch>/s14/run_test_twoway_option_parity.log` prints 3 and the log ends with `ALL CHECKS PASSED`; the pytest run reports 0 failed.]]></verify>
  <done>barwidth() in any spelling on rcap and rcapsym was refused with twoway's code and words, in every command form, and nothing else was newly refused.</done>
</task>

<task type="auto" id="14-11">
  <name>Certify in both modes against Stata</name>
  <files>none</files>
  <action><![CDATA[
    Run every test file changed in 14-01..14-10 plus the 57 files of Evidence "Measured red list": `python3 -m pytest <those files> -q -p no:cacheprovider`. A failure outside the flipped list is a pin the red list missed: if its file is one 14-03 to 14-06 already edit, flip it there in place with a `Flipped:` line (R9) and re-run; otherwise stop and report the node to the orchestrator, which allots a task for that file (never delete or skip it). Then G3 `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider`, `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` (expected unchanged: a scatter page with no filter), and through the driver `test_wp30_truth.cscript` (`WP30_ONLY=S14`), `test_twoway_option_parity.cscript` and `test_e2e_filters.cscript`. Afterwards check `~/.stata19/console/stata19.rc` still holds `python_exec`.
  ]]></action>
  <verify><![CDATA[All pytest runs report 0 failed; `grep -c "BG-0[1-6] PASS" <scratch>/s14/run_test_wp30_truth.log` prints 6; `grep -c "EW-01 PASS" <scratch>/s14/run_test_e2e_filters.log` prints 1; `grep -c " FAIL\|SKIP" ` on the three logs prints 0.]]></verify>
  <done>Stata certified the widths, caps and refusals, and both modes drew them alike before and after moves.</done>
</task>

<task type="auto" id="14-12">
  <name>Describe widths and caps in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Plot types (S14's paragraph, R3): after the `{ul:pccapsym.}` paragraph (:346-349) add `{ul:Bars and range caps.}`: bar and rbar draw each bar one unit of x wide whatever the spacing of x, as twoway does, and barwidth(#) sets another width in the same units; on a date axis the unit is the variable's own (a day for %td, a millisecond for %tc and %tC, a week, month, quarter, half-year or year for %tw to %ty), so monthly data held as %td dates draws bars a day wide, as in twoway, and barwidth(30) widens them; widths do not change when a filter moves; rcap draws its caps as long as a marker of its msize() is wide, the scheme's symbol size by default, in screen units; rcapsym draws no caps, only its spike and a marker at each end at the scheme's symbol size unless msize() says otherwise; barwidth() on rcap or rcapsym is refused, r(198), as twoway refuses it. Linking and Brushing :1161-1163: end the rbar sentence at "drawn from its own rows." Server Mode :1519-1520: delete "and a bar's or cap's width taken from the spacing of the rows kept"; :1541: "bins, grid and fitted line included." Touch nothing else (the `base()` entry :2358-2368 is S27's). Run `python3 -m pytest test/test_help_conformance.py $(grep -l "rbar\|rcapsym\|bar widths" test/test_help_claims_*.py) -q -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c "rows' spacing\|spacing of the rows kept\|bar widths included" dash.sthlp` prints 0; `grep -c "Bars and range caps" dash.sthlp` prints 1.]]></verify>
  <done>The help described twoway's bar widths, date units, caps and the refusal, and no longer described widths taken from the rows' spacing.</done>
</task>

<task type="auto" id="14-13">
  <name>Close P1.17a and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    1. The title is `WP30_OPEN["P1.17a"]`. Close that BUGS.md entry in place (`- [x]`) and replace its Resolution with: `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.17a). GlyphMapper.map_bar and map_rbar draw each bar one x unit wide, or barwidth() units (rbar now reads barwidth() and width()), in the variable's own units on a date axis through GlyphMapper._bar_extent (a day for %td, a millisecond for %tc, the period's own span for %tw-%ty from the __dash_bar_xc and __dash_bar_w columns); map_rcap draws its caps as dash markers as long as a marker of its msize() (the scheme's symbolsize p# by default) in screen units, tagged dash_cap; map_rcapsym draws no caps and starts its markers at the scheme's symbol size; dash.ado refuses barwidth() on rcap and rcapsym with twoway's r(198) "option barwidth() not allowed", naming the spelling typed (_dash_barwidth_typed). WP-29 P0.18's spacing machinery is removed (GlyphMapper._tag_spacing, the page script's spacing writer and its derived_spacing arguments, _dash_copy_redraw_geometry and its served call), and widths and caps hold through filter moves in both renderers. Pinned by test/test_bar_range_geometry.py::TestBarIsOneXUnit::test_the_width_is_twoways, test/test_bar_range_geometry.py::TestRcapCapsAreScreenUnits::test_the_cap_is_a_marker_of_its_msize, test/test_bar_range_geometry.py::TestTheWidthHoldsAcrossAMove::test_served, test/test_wp30_truth.cscript BG-01, test/test_twoway_option_parity.cscript BG-07; fixture test/fixtures/bar_geometry_truth.json. Residual, deferred (WP-30): twoway's default base and axis extent are P1.17b (section 27); barwidth() on rspike, rscatter, rarea, rline, rconnected, scatter and line, which twoway refuses, stays accepted (P2.21).`
    2. Delete the `"P1.17a"` key line from `WP30_OPEN`. S01's Appendix A now assigns P1.17a both lists (cross-file pass), so `WP30_LISTS["P1.17a"]` should already read `("Results that change", "Changed behaviour")`; only if it still reads `("Results that change",)`, set it to `("Results that change", "Changed behaviour")` in the same commit (R4); if the orchestrator's consistency pass already added the Changed behaviour list and marker, leave the row.
    3. CHANGELOG.md: replace the `<!-- WP-30 P1.17a -->` under `### Results that change` in place with: `- Bars and range caps are drawn at twoway's size. dash bar mpg weight drew each bar 0.8 times the smallest gap between the x values (56 on weights 1800-4080), now one x unit wide (1), as twoway draws it; on a date axis one unit is the variable's own, a day for %td, a millisecond for %tc, a week, month, quarter, half-year or year for %tw-%ty (a weekly %td bar was 5.6 days wide, now 1 day: barwidth(7) draws touching weekly bars), and barwidth() is read in those units (barwidth(3) on a %td axis drew 3 milliseconds, now 3 days). rbar reads barwidth() (barwidth(.3) was ignored). rcap's caps are as long as a marker of its msize(), the scheme's symbol size by default, and no longer change with the x spacing (they were 0.4 times the smallest gap and ignored msize()); rcapsym draws no caps (it drew two) and its markers start at the scheme's symbol size (they were 7 pixels). Widths and caps no longer change when a filter moves, in either mode. (WP-30, P1.17a)`. Then, under `### Changed behaviour (may need your do-files changed)`, replace `<!-- WP-30 P1.17a -->` in place if S01 placed one there, else add the line at the end of that list, in entry order among the WP-30 markers and lines (after the last one of an entry before P1.17a, before the first one of an entry after it): `- barwidth() on rcap and rcapsym is refused, r(198), with twoway's message option barwidth() not allowed, naming the spelling given (barw() to barwidth()); dash accepted it and drew nothing different. (WP-30, P1.17a)`
    4. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`; `git -C $WT merge --no-edit main` (expect `Already up to date.`); one full run `<scratch>/full_suite_queue.sh $WT <scratch>/14-full-1.log`, launched in the background and waited for on its `exit=` line (E1, E6).
    5. Stage only: `dash_render.py dash.ado dash_parse.mata dash.sthlp BUGS.md CHANGELOG.md scripts/extract_bar_geometry_truth.do`, the test files 14-01..14-11 changed (including `test/function_test_map.py test/program_coverage_map.py test/test_tracking_documents.py` and the three cscripts), and `git add -f test/fixtures/bar_geometry_truth.json`. Check `git diff --cached --name-only` (G6: never CLAUDE.md, .gitignore, AGENTS.md, .ultraplan/ or *.html). Write the message to `<scratch>/s14/msg.txt` in the boundary's form; G7 before and after `git commit -F <scratch>/s14/msg.txt`; report the sha and message.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/14-full-1.log` prints `exit=0` and the summary line above it names no `failed` or `error`; `git log -1 --format=%s` ends `(WP-30 P1.17a)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.17a -->' CHANGELOG.md` prints 0; `grep -c "(WP-30, P1.17a)" CHANGELOG.md` prints 2; `grep -c '^    "P1.17a": "' test/test_tracking_documents.py` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.17a was closed in BUGS.md naming tests that exist, its key was removed, its CHANGELOG marker became the measured Results line beside a Changed behaviour line, and one green commit on wp30-s14 was ready for the merger.</done>
</task>

## Section completion criteria

- bar and rbar are one x unit wide (or `barwidth()`) in both modes, before and after moves, in the variable's units on every date kind; rbar reads `barwidth()` silently.
- rcap caps are `dash` Scatters tagged `dash_cap`, sized as markers of their `msize()` (scheme default), independent of the x spacing; rcapsym has no caps and scheme-sized markers.
- `barwidth()` on rcap and rcapsym is refused r(198) in twoway's words, spelling as typed; nothing else newly refused.
- No `_tag_spacing`, spacing JS, `derived_spacing_*` arg or `_dash_copy_redraw_geometry` remains; the registry tests and G3 parity are green.
- `bar_geometry_truth.json` is stamped and named by `test_bar_range_geometry.py`; BG-01..BG-09 and EW-01 PASS through the driver; every flip is recorded with its reason.
- One green commit `(WP-30 P1.17a)` on `wp30-s14`; the BUGS.md entry closed in place, its `WP30_OPEN` key deleted, `WP30_LISTS` updated, the marker replaced and the Changed behaviour line added.

## Notes

- **The derived-copy loop is shared.** Every saved line, area, bar, range and label copy is written by the same `_FILTER_JS` loop; deleting the `_sp` block must leave `_dsrcs[_di].data = _nd;` and the selection clear exactly as they are. test_saved_filter_layers.py's row-type moves (`_ROW_TYPES`) are the guard.
- **Period columns and node.** `__dash_bar_xc`/`__dash_bar_w` are float arrays; `_snapshot_of` serialises them through `DashRenderer._to_serialisable` like any column, so NaN rows travel as the page's NaN form. `test_a_period_bar_after_a_saved_move` runs the real script under node.
- **S08's numbers.** Do not pin pixel constants for caps: compare with `map_scatter`'s marker size for the same `msize()`. After S08 a medium marker is 5.87 px (IR-1), so a default cap is about 5.9 px long against today's 0.4 × gap in data units.
- **rcapsym marker symbol** stays Bokeh's circle; the p# symbol cycle reaching rcapsym is S24's (batch 8).
- **python_exec hazard** (project memory): concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the truth script then exits 222 and a SKIP is not a pass. Check after 14-02 and 14-11.
- **Shared files (R1-R13).**
  - **R1:** the S14 block only, helpers above its header; BG-07..BG-09 appended as one run in test_twoway_option_parity.cscript (no batch-5 partner appends there: S13's LN cases go to test_option_validation.cscript); EW-01 flipped in place.
  - **R2:** one removal from the functions tuple (`"_dash_copy_redraw_geometry",`, 33332), no addition; the S15 anchor (`"_dash_textbox_or_default",`, 33372) is not adjacent. Map entries under S14's anchors.
  - **R3:** Plot types (S14's title), plus the three spacing sentences in Linking and Brushing and Server Mode, which no batch-5 section edits.
  - **R4:** the one Results marker replaced; one Changed behaviour line added and `WP30_LISTS["P1.17a"]` widened in the same commit.
  - **R5:** the one entry and its key line.
  - **R6:** `_dash_process_segment` gains one block; `_dash_barwidth_typed` goes after `_dash_logit_typed` in the parser section, with its header-index entry and `_needed` name.
  - **R7:** the new extractor, run only by S14; S27 writes its own extractor for the base cases.
  - **R8:** `CORPUS`/`MOVE_CORPUS` appended; one comment rewritten.
  - **R9:** flips in place, recorded.
  - **R10:** no combined pin moves; the single-y digest is unchanged (no bar, no filter).
  - **R12:** S14 is batch 5's `_build_filter_widgets` editor and, by D-14b, its `_generate_app_source` editor (deletion only); it edits no applier and not `_make_figure_body`.
- **Commit body line forms** are BRIEF's, with WP-30 ids; `failed at` is `batch-5-base.txt`'s sha.
- **For S27 (batch 9).** Widths and caps are constants or columns; S27's auto-base column joins the source beside `__dash_bar_*` and must not change `x` or `width`. test_glyphs.py `TestBarOptions::test_base_default_is_zero` and the base lines of the date and HTML tests are S27's flips.
- **For S49 (batch 17).** Rotate every renderer whose `tags` holds `dash_cap` (angle π/2 under `horizontal`); bar widths become HBar heights by the same `_bar_extent` (use its `x_field`/`width_spec` on the swapped axis).
- **For S55 (batch 19).** `_dash_copy_redraw_geometry` no longer exists (D-14b): widths and heights are invariant, so nothing about geometry needs copying after a served move, and P1.9's step 5 stays cancelled (IR-13).
- **Notes for the closeout (S58).**
  - **DROPIN P1.17:** bullets 1, 2 and 4 (widths, rbar `barwidth()`, rcap/rcapsym caps) and the WP-29 S05/S12 bar-width notes are closed by P1.17a, commit `<sha>`; bullets 3 and 5 (base) remain for P1.17b.
  - **GAPS2-A3:** sub-claims a, b, d and e closed by P1.17a; the Tracked line waits for S27 to close c and f; append `(WP-30, GAPS2-A3)` to a Resolution only when both parts have landed.
  - **AUDIT-44** (TWOWAY_COVERAGE_AUDIT.md rows :72 rbar "bar geometry only partially reproduced", :74 rcap "cap geometry is an approximation", :75 rcapsym "cap/marker geometry differs"): tag as corrected by WP-30 P1.17a; the "default base differs" rows (:63-66, :115) are P1.17b's. The audit's rows are unnumbered, so the mapping of AUDIT-44 to these rows is by content.
  - **BUGS.md:504** (WP-27's recorded divergence): its "note recorded ... not acted on" is acted on by P1.17a; S58 may cross-reference it, never edit its Resolution.
  - **P2.21 residual:** twoway refuses `barwidth()` on rspike, rscatter, rarea, rline, rconnected, scatter and line (r(198), measured 03oct2026); dash accepts it there. twoway accepts `barwidth(0)` and `barwidth(-1)` (rc 0), which dash refuses with its own bound.
  - **ROADMAP:** the WP-30 entry lists P1.17a and its commit; the P0.18 rows at ROADMAP:4554, :4660 and :4703 gain "spacing machinery removed by WP-30 P1.17a".
  - **AGENTS.md invariant** (E7): "no glyph geometry depends on the rows a filter keeps: bar widths are one x unit or barwidth() (date units on date axes, per-row `__dash_bar_*` columns on period axes) and rcap caps are screen-unit markers tagged dash_cap".
- **Line numbers** are `c96facd`'s; S01-S12 land first. Symbols and the quoted excerpts are authoritative.
