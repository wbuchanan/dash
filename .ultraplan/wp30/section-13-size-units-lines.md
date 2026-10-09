# Section 13: Stata line-width ladder (P1.12 part b, M1)

> Part of: WP-30 · Items: P1.12 part b (entry `P1.12b`) · Risk: yellow · Batch: 5 · Depends on: 08 · Blocks: 31, 32, 38, 39 · Tasks: 17, 1 commit · Case prefix: LN

## Review amendments

- Fixed (blocker, A139): S13 and S15 both edited `SchemeParser._init_properties` in batch 5. S13 no longer edits it (D-13g): S15 replaces the two pixel-literal defaults. TR-13.5, 13-06, the case-sensitive scheme test (now `linewidth minor_grid`), E9's `TestHostileSchemeValues` row, 13-12 and 13-14's flip count follow.
- Fixed (blocker): the LN area cases passed `198 ""`, but `_ov_probe` (test_option_validation.cscript:386-437) counts ` <opt>()` in the log, so every refusal would FAIL. Refused cases now pass the option (`198 lwidth`, OV-09's form). 13-04 also makes the OV-09/12/150 header-comment edit the Stata truth section promised.
- Fixed (major): probe id `line_lwidth_star_neg1` contradicted the id rule (`*` → `star`, `-` → `neg`). Both the example and 13-02's verify now read `line_lwidth_starneg1`.
- Fixed (minor): the truth block now follows TR-01.10 item 4: `python:` helpers above the header, `version 19` helpers, files under `` `w30_work' `` and erased, cases through `_w30_expect`/`_w30_done`.
- Fixed (minor): D-13b is now a marked Maintainer question with a recommendation (ratify). The renderer has no return-code channel (`DashLimitError`/`DashSpecError` reach Stata as Python errors).
- Cross-file: index R3 omits S13's two Differences-from-twoway sentences (:690-693, :744-752). Recorded in g03.md.
- Rejected: "D-13a contradicts register P1.12.2 (class's medium)". The ruling's stated reason is twoway's picture, and E4 measured that twoway draws the plot's default for a bad line-width name (economist `abc` 19.01, not 4.75). M1 (match Stata) governs.
- Rejected: "D-13c refuses `scatter …, lwidth(*-1)`, which twoway accepts (M5)". Today's every-type rule (dash.sthlp:744-752, HC2-18l/o) already refuses negative widths on every type. Narrowing that per type is P2.21's sweep, which M5 excludes.
- Checked: the anchors E1/E2/E5 (`_LWIDTH_MAP` 5324, `translate_lwidth` 5590, `_LWIDTH_PX_PER_UNIT` 5934, `_lwidth` 6635, `_ci_band_style` 8354-8367, `_apply_line_opts` 8602-8606, `mlwidth` 8753, dash.ado 2027-2044 and 2264-2274) match HEAD. The BUGS title, both markers, the stub header and the map anchor match section-01.
- (cross-file pass) 13-17 verify: added the key-deletion check `grep -c '^    "P1.12b": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.
- (ratification 06oct2026) Item 27 (A37, P1.12.6) is "Fix in WP-30": S08 (batch 3) syncs the nonselection and muted copies after the appliers; P2.49 is not filed. The P1.12.6 reading, the Boundaries row and 13-07 now say S13's widths reach the copies through S08's sync, which S13 keeps where S08 put it; no S13 test added (`line_width` is a property S08's sync copies, and S08's brushed-copy tests cover it).
- (ratification 06oct2026) 13-14's run includes S08's brushed-copy tests' file, so a width change that breaks the sync is caught in batch 5.

**Binding readings applied in this file** (index "Index reconciliations", register P1.12, decisions M1, M5, M6):
- **IR-1 / P1.12.1 (M1 strict).** Option B: one Stata unit for every class, 1 rs = 2.88 pt = 3.84 px at the 4-inch reference. The default line goes from 1.5 px to 1.152 px (s2color `linewidth p medium`, .30 rs). S08 builds the unit; this section puts lines on it.
- **P1.12.3.** Stata's linear ladder (`style/linewidth-*.style`), `vvvthin` and `none` added, on S08's unit, with a hairline floor of 0.3 pt.
- **P1.12.4 [C].** `#pt`, `#in`, `#cm` convert to Stata units at the graph's reference length, through S08's `ref_in` (the scheme's smaller `graphsize` side; the `xsize()`/`ysize()` half is S08's open question Q1, and S13 follows whatever S08 lands).
- **P1.12.2, read for lines (D-13a).** The register's "the class's medium, with twoway's note" was measured on markers and text. For a line width twoway draws the plot's own default, not the class's medium: economist `lwidth(abc)` draws 19.01 SVG units, its `linewidth p 1.2`, where medium is 4.75 (Evidence E4). S13 applies the ruling's reason ("twoway's picture"): an unknown or wrong-case line-width name is noted and the site's scheme default is kept, which is today's fallback.
- **P1.12.6 / A37 / A146 (ratification item 27, 06oct2026: fixed in WP-30).** S08 (batch 3) fixes the brushed-glyph bug: after the option appliers run, it copies the styled properties to the renderer's `nonselection_glyph` and `muted_glyph`, keeping dash's nonselection alpha, in both modes. P2.49 is not filed. S13 adds no styled property: it changes the values `_apply_line_opts`, `_apply_marker_opts` (`mlwidth()`) and `_ci_band_style` write to `line_width`, a property S08's sync already copies, and the band's width is a creation keyword, which Bokeh copies. So S13's widths reach the brushed and muted copies through S08's sync. S13 keeps S08's sync where S08 put it, byte for byte, writes each width inside the appliers before the sync runs, and adds no test: S08's brushed-copy tests cover `line_width`, and 13-14's run keeps them green. No S13 test reads `nonselection_glyph` or `muted_glyph`.
- **P1.12.7 / A38.** `lwidth(none)` is closed here; S58 removes it from P2.12.
- **M5.** A width twoway refuses is refused with r(198) and twoway's words, `gm_linewidth must be between 0.000 and  1.0e+04` (two blanks before `1.0e+04`, as twoway prints it), followed by dash's line naming the option (the register's P1.8.2 form: twoway's words, then a dash hint).
- **M6.** No new note where twoway is silent: `lwidth(*0)`, `lwidth(0pt)`, `lwidth(none)` and `lwidth(-0)` draw nothing, silently.
- **A150.** Every note goes through `_dash_style_note` or `warnings.warn` with a `dash`/`dash scheme` prefix, which S06 routes into twoway's `(note: …)` form.
- **R12.** S13 is batch 5's only editor of `_apply_line_opts` and `_apply_marker_opts`. It edits none of `_generate_app_source`, `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets`, `_apply_mlabel_opts` or `_apply_fill_opts`.
- **A139 (no function edited by two sections of a batch).** `SchemeParser._init_properties` is S15's in batch 5 (TR-15.3). S13 does not edit it (D-13g).

**Section decisions (this file).**
- **D-13a** (above). Unknown or wrong-case names keep the site's scheme default, with the existing note.
- **D-13b, for ratification.** dash.ado cannot judge a positive `*#` or an absolute unit whose Stata-unit value passes 10,000 only once the scheme's default or the graph's reference length is known. Examples are `lwidth(*40000)` under s2color and `lwidth(20000pt)` under economist, both r(198) in twoway. dash.ado lets them through, and the renderer notes them and keeps the scheme's default (Notes, open question). Every other form twoway refuses is refused by dash.ado.
- **D-13c.** dash keeps refusing an out-of-range width on every plot type (dash.sthlp:744-752, pinned by HC2-18l and HC2-18o). The new unit and multiplier forms join that rule, so `scatter …, lwidth(*-1)` is refused although twoway, which draws no line there, accepts it. The per-type narrowing is P2.21's.
- **D-13d.** `plotregion(lwidth(*#))` multiplies `thin`, and its absolute units use the 4-inch reference, until S38 passes the scheme's `linewidth plotregion` and the figure's reference at the two call sites S13 may not edit (R12: `_make_figure_body` 30366, `_generate_app_source` 35249). `thin` is the `linewidth plotregion` of every shipped scheme (Evidence E1), so only a user scheme with another plot-region width differs until batch 13.
- **D-13e.** `*#` multiplies the width already set at the site, after the hairline floor. This differs from twoway only where a scheme's default is below 0.3 pt (economist's `linewidth pbar vvthin`, 0.4 px drawn): there `*2` gives 0.8 px where twoway gives 0.4. This is accepted and documented in Notes.
- **D-13g (review, A139).** `_init_properties`' two pixel-literal defaults (`self._lwidth("linewidth p", 1.5)`, `self._lwidth("linewidth major_grid", 0.8)`, dash_render.py:6934/6938) are replaced by S15, batch 5's one `_init_properties` editor, in its TR-15.3 edit (S15 lands after S13). They are reached only when a scheme file lacks the key or holds a value `_lwidth` refuses (every shipped scheme and `_FALLBACK_PROPS` declare both keys), so until S15 lands such a scheme keeps 1.5 px and 0.8 px for those two keys. S13's tests therefore never assert those two fallbacks: its case-sensitivity scheme test uses `linewidth minor_grid`, whose default is already the `thin` rung, and it flips only the `minor_grid`/`axisline` rows of `TestHostileSchemeValues`; S15 flips the `p` and `major_grid` ones.
- **D-13f.** The colour key has no line width to change. `_dash_apply_z_options` sets none, the ColorBar keeps Bokeh's 1 px (Evidence E2), and its chrome is S33's. `zlabel(, tlwidth())` and every axis's `tlwidth()`/`glwidth()` stay named as not drawn (no WP-30 owner; Notes for the closeout).

## Overview

**What is wrong today.** DROPIN-REMAINING.md:102 (P1.12): "Numbers are read as pixels and keywords use a private pixel ladder … `#pt`, `*#` and `vhuge` are refused … and `vvvthin` is missing." GAPS2 D2 (GAPS2.md:849-866) measured the line part: "`lwidth(.3)` draws 0.3 px against a 1.5 px default … The `_LWIDTH_MAP` keyword ratios are not Stata's." The entry S01 opened (BUGS.md, "Line widths use a private ladder without vvvthin or none and read numbers as pixels, and negative widths twoway refuses are accepted") adds the refusals.

Re-measured at `c96facd`, the saved page and the served app are identical line for line (Evidence E3):
- `lwidth(thin)` is 0.8 px, `thick` 2.5, `vvthick` 5.0 and `vvvthick` 6.6 against `medium` 1.5. Stata's ratios to medium are 0.667, 2.667, 8.667 and 14.0; dash's are 0.533, 1.667, 3.333 and 4.4.
- `lwidth(.3)` is 0.3 px (Stata's medium), and `lwidth(2)` is 2 px (6.67 mediums in Stata).
- `vvvthin`, `none`, `1pt`, `*2` are each noted as "not a recognised line width" and drawn at the scheme's width. This happens for `lwidth()`, `mlwidth()`, `alwidth()`, `plotregion(lwidth())` and `xline(…, lwidth())`; only `alwidth(none)` was special-cased to 0.
- `lwidth(THICK)` draws thick, where twoway notes it and draws the default.
- A scheme's `linewidth p .8` draws 4.0 px while `linewidth p thick` (also .8) draws 2.5 px.
- `xline(20, lwidth(-1))` draws 0.1 px in silence.
- `lwidth(*-1)` and `lwidth(-1pt)` reach the renderer with rc 0 and a note. twoway refuses them, r(198).

**After this section.** In both modes, before and after any filter move:
- every line width is drawn in Stata's units on S08's one unit, 1 rs = 3.84 px: medium .30 = 1.152 px, thin .20 = 0.768, thick .80 = 3.072, vvvthick 4.2 = 16.128. `vvvthin` and every non-zero width below 0.3 pt are drawn at 0.3 pt (0.4 px); `none`, `0` and `*0` draw nothing;
- a number is Stata units, as are `#rs`; `#pt`, `#in` and `#cm` are absolute, at the graph's reference length; `*#` multiplies the width the site would otherwise draw;
- names are matched case-sensitively. An unknown name is noted and the scheme's width kept (D-13a);
- this holds for `lwidth()`, `mlwidth()`, `clwidth()`, `alwidth()`, `plotregion(lwidth())` (D-13d), `xline()`/`yline()`'s `lwidth()`, and every `linewidth` key a scheme file declares;
- dash.ado refuses a negative number, multiplier or unit form and an `rs` value above 10,000, with r(198) and twoway's words (M5), on the four plot options, in every route (`dash` immediate, `dash graph`, `dash build`, `dash serve`).

The default s2color line, marker outline, grid and reference line go from 1.5 to 1.152 px. Axis lines, the plot-region border and bar outlines go from 0.8 to 0.768 px, and economist's lines from 6.0 to 4.608 px. This is the M1 change the CHANGELOG announces.

**Why one section.** This is the line kind of S08's resolver (A138: P1.12a is S08, P1.12b is S13). It was split off because `_apply_line_opts` is the most-impacted CRITICAL symbol of the appliers (40 impacted). Every later width consumer, S31 (axis line width), S32 (named styles), S38 (region styling) and S39 (`xline` `lstyle()`), needs one ladder first. S15, in this batch, reads the scheme's tick widths through `SchemeParser._lwidth`, so S13's ladder applies to them on merge (index batch 5).

**Test order and commit rule (rule 7, D1, A156).** There is one entry, one cycle and one commit, `(WP-30 P1.12b)`.
- **13-01** writes the regression tests whose expectations are the twoway values quoted in Evidence, runs them against the unmodified tree (the batch-5 base, with S08 landed) and saves `<scratch>/13-P1.12b-failure.txt`. It never commits.
- **13-02** extracts the fixture. **13-03** adds the fixture-driven tests and the guards, runs them on the unmodified renderer and appends their red lines to the same file. Guard tests pass and are listed apart.
- **13-04** writes the LN refusal cases and runs them red on the unmodified dash.ado.
- **13-05 to 13-10** make the fix (the ladder, the scheme, the appliers, the graph sites, dash.ado), register `line_px` and add the parity cases.
- **13-11 to 13-14** flip the pinned tests and re-run the measured list.
- **13-15** certifies against twoway in Stata.
- **13-16** writes the help and re-derives the page digest.
- **13-17** closes the entry, replaces both markers and makes the one commit after one full run through the queue.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every dashboard's lines get thinner, a CRITICAL applier and a dash.ado validator change, and 51 test functions (544 nodes) pin the private ladder

**Why.** M1 accepts a visible change to every dashboard (RK-4): every default line, grid, axis and outline moves (Overview). The applier `_apply_line_opts` feeds every line-drawing plot type. `_dash_validate_value` judges every plot option of every route.

**Risk factors.**
1. Blast radius (gitnexus at `c96facd`, re-run at the batch-5 base). `GlyphMapper._apply_line_opts` is CRITICAL: 40 impacted, 26 direct, 26 processes. `GlyphMapper._apply_marker_opts` is CRITICAL (12 / 7 / 8). `OptionTranslator.translate_lwidth` is HIGH (10 / 3 / 3), and `GlyphMapper._ci_band_style` is HIGH (6 / 1 / 3). LOW: `SchemeParser._lwidth` (6 / 3 / 2), `_bounded_lwidth` (2), `_plot_lwidth_of` (4), `_extract_region_lwidth` (3), `_dash_refline_draw` (3). `OptionTranslator.resolve_size` is S08's new method and is measured at the batch-5 base. dash.ado's `_dash_option_rules` and `_dash_validate_value` are not indexed (UNKNOWN). Their callers by grep: `_dash_validate_value` at dash.ado:2692, 2713, 5349, 5371, 7069, 7451 and 7456; `_dash_option_rules` at 2580.
2. Pinned tests. The prototype's measured red list is in Evidence E9. Each test there is flipped with its reason (R9), never deleted.
3. The single-y page digest (`test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline`, :393) moves. S15 moves it in the same batch, so the merger re-derives it (R10).
4. Cross-mode drift. The served app copies the three classes whole (class loop at 33436-33438) and `_extract_region_lwidth` (33388) and `_dash_refline_draw` (33383) by name. If a site were only fixed in one mode, the gap would show only in parity.
5. dash.ado's style kind also serves `msize`, `mlabsize`, `mlabgap`, `msangle`, `xsize` and `ysize`. A unit branch that leaked into them would refuse forms S08 makes legal.

**Mitigation.**
1. Impact is run at the batch base (index 5.0) and checked in 13-01. `TestEmptyOptionsChangeNothing` runs every line type in both modes. `test_mode_parity.py` gains S13's CORPUS and MOVE_CORPUS cases (G3).
2. 13-03 records the red list on the unfixed tree. 13-09 and 13-11 to 13-14 flip exactly that list, and 13-14 re-runs it.
3. The commit message says why the digest moved, and the merger re-derives it.
4. Every behaviour test runs in both modes (`_figure(mode, …)` from `test_scheme_linewidth.py`), and for the served app also after a `_fire` filter move. No new module-level name exists (R2 row S13).
5. The unit branch runs only when the rule carries the new fourth parameter `u` (`style,0,10000,u`), which only the four line options carry. A pytest checks that no other rule carries it, LN-14 checks that `msize(-1pt)` still passes, and S08's SU-01..SU-08 stay green.

**Prototype** (measured 03oct2026 on a scratch copy of `c96facd` exported with `git archive HEAD`, with a standalone version of TR-13.1 to TR-13.7 and no S08; `python3 probe_modes13.py` before and after; the test-file list of Evidence E9 run as files, not the full suite). Both modes agreed line for line after the change (E3). The red list is E9.

## Dependencies

- **Depends on: 08.** S08 provides:
  - `OptionTranslator.resolve_size(value, kind, default_pt, ref_in=4.0)`, `_SIZE_KINDS`, `stata_number`, `size_multiplier`, `PT_PER_RS = 2.88`, `PX_PER_PT = 4/3` and `size_ref_of(fig)`;
  - `SchemeParser.size_ref_in`, and the `fig._dash_size_ref_in` stamp written by `apply_to_figure` (S08 TR-08.1 to TR-08.7).

  S13 appends `"line"` to `_SIZE_KINDS`, as S08's TR-08.1 anticipates. S01 provides the entry `P1.12b`, its `WP30_OPEN` key, the markers `<!-- WP-30 P1.12b -->` in `### Results that change` (the WP-30 group) and in `### Changed behaviour (may need your do-files changed)`, the stub `* ==== S13 P1.12b: Stata line-width ladder ====` and the map anchor `# WP-30 S13 (P1.12b): Stata line-width ladder (P1.12 part b, M1)`. S06 provides the note channel. S02 provides the extractor root stanza (TR-02.9). S11 (batch 4) splits a plot option's stylelist, so `lwidth(1 pt)` reaches S13 as `1`, as twoway reads it (Evidence E4).
- **Blocks: 31, 32, 38, 39.**
  - S31: axis line width through `translate_lwidth`.
  - S32: a named style's width.
  - S38: region widths. It passes the scheme default and reference to `_extract_region_lwidth`, or replaces it (D-13d).
  - S39: `lstyle()` on reference lines, through `_dash_refline_draw`.
- **Parallel batch: 5**, merge order S13, S14, S15.
- **Can run with:**
  - S14 edits `map_bar`/`map_rbar` widths (bar widths, not line widths), `map_rcap`'s cap length, `map_rcapsym`, `_tag_spacing` (deleted), `_FILTER_JS`'s spacing writer, `_build_filter_widgets` and `_dash_copy_redraw_geometry`.
  - S15 edits the extractor, the 26 scheme files, `scheme_truth.json`, `SchemeParser.apply_to_figure`/`apply_to_axis`, `_init_properties`' new chrome attributes, `_FALLBACK_PROPS`, `_dash_add_secondary_axes`, `_dash_finish_secondary_axes` and the new `_dash_textbox_place`.
  - S13 touches none of them, and does not edit `_init_properties` (D-13g): S15 replaces its two pixel-literal width defaults. Both sections flip different nodes of `test_scheme_review_fixes.py::TestHostileSchemeValues`; the parametrize rows of `test_every_negative_linewidth_is_refused` are adjacent lines, so the merger keeps S13's `minor_grid`/`axisline` rows and S15's `p` row by hand (test-only context conflict).

## Evidence

All anchors are at `c96facd` (dash_render.py 37,689 lines; dash.ado 8,487). S01-S12 land before batch 5, so the lines drift by a few dozen. The symbols and the quoted text are authoritative.

### E1 — the private ladder and the scheme's own unit (dash_render.py)

`OptionTranslator._LWIDTH_MAP`, 5321-5341, is a pixel ladder whose ratios are not Stata's. It has no `vvvthin` and no `none`:
```python
5324    _LWIDTH_MAP: dict[str, float] = {
5325        "vvthin":   0.2,
5327        "thin":     0.8,
5329        "medium":   1.5,
5331        "thick":    2.5,
5333        "vvthick":  5.0,
5341        "vvvthick": 6.6,
```
`OptionTranslator.translate_lwidth`, 5578-5604, lower-cases the value, reads the map, and passes a bare number through as pixels:
```python
5590        v = value.strip().lower()
5591        if v in OptionTranslator._LWIDTH_MAP:
5592            return OptionTranslator._LWIDTH_MAP[v]
5595        try:
5596            f = float(v)
5599        if math.isfinite(f):
5600            return max(0.1, f)
```
The scheme side (WP-16) puts a bare number on a third scale, `SchemeParser._LWIDTH_PX_PER_UNIT`, at 5930-5934:
```python
5930    # A bare number in a `linewidth' directive is a Stata linewidth unit
5931    # (style/linewidth-medium.style: .30).  dash anchors the `medium'
5932    # keyword at 1.5px through _LWIDTH_MAP, so one unit is 5.0px.
5934    _LWIDTH_PX_PER_UNIT: float = 5.0
```
`SchemeParser._lwidth`, 6625-6660, lower-cases, sends a keyword to `translate_lwidth`, scales a number by 5.0, and returns the default for an unknown keyword silently:
```python
6635        raw = self._props.get(key, "").strip().lower()
6638        try:
6639            val = float(raw)
6640        except ValueError:
6641            try:
6642                return OptionTranslator.translate_lwidth(raw)
6643            except ValueError:
6644                return default
6659        return val * self._LWIDTH_PX_PER_UNIT
```
Its consumers in `_init_properties` take pixel defaults (6934, 6938) or rungs (6941, 6949, 6993, 7004): `self._lwidth("linewidth p", 1.5)`, `self._lwidth("linewidth major_grid", 0.8)`, `OptionTranslator.translate_lwidth("thin")` and so on. `_bounded_lwidth` (6731-6743) and `_plot_lwidth_of` (7317-7336) bound a scheme width to `[0, _LWIDTH_MAX_PX]` (100 px, 6721). Every plot type's default width goes through `plot_line_width` (7338-7374) and `_plot_lwidth_of`, so `_lwidth` is the one scheme reader. `_FALLBACK_PROPS` (5728) holds keywords only (5764-5823).

The shipped schemes' `linewidth` values (`grep -h '^linewidth' dash-*.scheme | awk '{print $3}' | sort | uniq -c`): `medium` 119, `thin` 79, and one each of `1.2` (economist `p`), `thick` (economist `pother`) and `vvthin` (economist `pbar`). `linewidth plotregion thin` is in 19 of the 20 files; economist has none and gets `_FALLBACK_PROPS`' `thin`.

Stata's ladder (`/Applications/StataNow/ado/base/style/linewidth-*.style`, `set val`):
```
none 0   vvvthin .000001   vvthin .01   vthin .15   thin .2   medthin .25   medium .30
medthick .45   thick .8   vthick 1.4   vvthick 2.6   vvvthick 4.2
```

### E2 — every explicit line-width site (dash_render.py)

- `GlyphMapper._apply_line_opts`, 8540-8616. `clwidth()` takes `lwidth()`'s place (8575-8581). The width is set at 8602-8606, with no default passed, so `*#` cannot work:
  ```python
  8602        if "lwidth" in options:
  8603            try:
  8604                glyph.line_width = self.tr.translate_lwidth(options["lwidth"])
  8605            except ValueError:
  8606                _dash_style_note(_lw_name, options["lwidth"], "line width")
  ```
- `GlyphMapper._apply_marker_opts`, 8622-. `lwidth()` is only validated on a marker (8731-8735, twoway notes an unknown name even where it draws no line). `mlwidth()` is the marker outline (8753-8759):
  ```python
  8753        if "mlwidth" in options:
  8754            try:
  8755                glyph.line_width = self.tr.translate_lwidth(options["mlwidth"])
  8756            except ValueError:
  8757                _dash_style_note("mlwidth", options["mlwidth"], "line width")
  ```
- `GlyphMapper._ci_band_style`, 8307-8401. This is the band outline (`lwidth()` < `alwidth()`). `none` is special-cased, and a pixel cap of 1000 drops a valid Stata width silently:
  ```python
  8354        for key in ("lwidth", "alwidth"):
  8358            if str(val).strip().lower() == "none":
  8359                st["line_width"] = 0.0
  8362                w = self.tr.translate_lwidth(str(val))
  8366            if math.isfinite(w) and 0.0 <= w <= 1000.0:
  8367                st["line_width"] = w
  ```
- `_extract_region_lwidth`, 5065-5085. This is the plot-region border, with no default and no reference:
  ```python
  5065 def _extract_region_lwidth(val: str) -> float | None:
  5070     m = re.search(r'\blwidth\s*\(([^)]+)\)', val, re.IGNORECASE)
  5080         return OptionTranslator.translate_lwidth(raw)
  5082         _dash_style_note("plotregion(lwidth)", raw, "line width",
  ```
  It has two call sites, both in R12-locked functions: saved `_make_figure_body` (def 30203) at 30366-30368, `_pr_lw = _extract_region_lwidth(raw_plotregion)` then `fig.outline_line_width = _pr_lw`; and served `_generate_app_source` (def 33915) at 35249-35250, the same two lines emitted.
- `_dash_refline_draw`, 26327-26368. This is `xline()`/`yline()`. The default is the scheme's `xyline_width`, or a literal 1.0 without a scheme. The sub-options run through one loop, with no default for `*#`:
  ```python
  26334    if scheme is not None:
  26335        kw = {"line_color": scheme.xyline_color,
  26337              "line_width": scheme.xyline_width}
  26339        kw = {"line_color": "#000000", "line_dash": "dashed",
  26340              "line_width": 1.0}
  26349            ("lwidth", "line width", OptionTranslator.translate_lwidth,
  26351        if style.get(sub):
  26353                kw[attr] = fn(style[sub])
  ```
- The colour key (D-13f). `_dash_apply_z_options`, 26106-26217, sets no line width. The ColorBar is built at 9243 with Bokeh's defaults (`bar_line_width`, `major_tick_line_width` and `border_line_width` all 1). `_dash_parse_axis_spec(', tlw(thick) glwidth(thick)')['unsupported']` gives `['tlw(thick)', 'glwidth(thick)']` (measured), so a tick or grid width sub-option is named on every axis, the colour key's included.
- The served app. `ServerAppBuilder._glyph_layer_lines` copies `OptionTranslator`, `SchemeParser` and `GlyphMapper` whole (33436-33438). Its functions tuple lists `"_dash_refline_draw"` (33383) and `"_extract_region_lwidth"` (33388). No saved-page script writes a width: `grep -n "line_width" dash_render.py` after 15000 finds only Python (22955, 26337, 26340, 26350, 30368) and the emitted region line (35250). A filter move changes source data only, and the stale cue rebuilds `muted_glyph` from the glyph (32328).

### E3 — measured at `c96facd`, both modes (scratch `probe_modes13.py`; saved `DashRenderer._build_figures`, served `ServerAppBuilder.build` + `make_document`; s2color unless named; served identical line for line)

```
line default 1.5 | economist default 6.0 | lwidth(medium) 1.5 | thin 0.8 | thick 2.5 | vvvthick 6.6
lwidth(vvvthin) 1.5 + "dash: lwidth(vvvthin) is not a recognised line width; using the scheme's default."
lwidth(none) 1.5 + note | lwidth(1pt) 1.5 + note | lwidth(*2) 1.5 + note | economist lwidth(*2) 6.0 + note
lwidth(.3) 0.3 | lwidth(2) 2.0 | lwidth(THICK) 2.5 (no note)
clwidth(thick) on connected: line 2.5, markers 1.5 | scatter outline 1.5 | mlwidth(*2) 1.5 + note | mlwidth(thick) 2.5
bar outline 0.8 | bar lwidth(*2) 0.8 + note | economist bar outline 0.2
lfitci band outline 1.5 | alwidth(*2) 1.5 + note | alwidth(thick) 2.5 | alwidth(none) 0.0
plotregion border 0.8 | lwidth(thick) 2.5 | lwidth(*2) 0.8 + note | lwidth(1pt) 0.8 + note
xline 1.5 | lwidth(*2) 1.5 + note | lwidth(thick) 2.5 | lwidth(-1) 0.1 (silent) | lwidth(none) 1.5 + note
```

After the prototype (TR-13.1-TR-13.7, standalone, so `ref_in` is 4.0 and the region `*2` multiplies medium; the design's D-13d multiplies thin, giving 1.536):
```
line default 1.152 | economist 4.608 | medium 1.152 | thin 0.768 | thick 3.072 | vvvthick 16.128
vvvthin 0.4 | none 0.0 | .3 1.152 | 2 7.68 | 1pt 1.3333 | *2 2.304 | THICK 1.152 + note | economist *2 9.216
clwidth(thick) 3.072 (markers 1.152) | mlwidth(*2) 2.304 | mlwidth(thick) 3.072
bar 0.768 | bar *2 1.536 | economist bar 0.4
lfitci 1.152 | alwidth(*2) 2.304 | thick 3.072 | none 0.0
plotregion 0.768 | thick 3.072 | 1pt 1.3333
xline 1.152 | *2 2.304 | thick 3.072 | -1 1.152 + note | none 0.0
MODES-AGREE (saved and served diff empty)
```

### E4 — twoway truth (StataNow 19.5, console, through `scripts/stata_slot.sh`; scratch `…/wp30/s13/probe/p1.do`-`p3.do`, 03oct2026)

The SVG unit is 720 per inch, so 10 units = 1 pt. One rs is 28.8 units under s2color (5.5 × 4 in), 15.84 under economist (2.2 × 2.2) and 32.4 under stcolor (7.5 × 4.5). The class setting is `.Graph.plotregion1.plot1.style.line.width.setting`.

Return codes and settings (`capture noisily twoway line mpg weight, lwidth(X)`, s2color):
```
THICK, Thick, 1PT, -1PT, *abc, "* 2" -> rc 0, "(note:  named style THICK not found in class linewidth, default attributes used)", setting .3
thick .8 | "1 pt" 1 | .5cm .5 | +1 1 | 10000rs 10000 | *0 0 | -0 0 | *-0 0 | 0pt 0 | 20000pt 20000 | *33333 9999.9
*2 .6 | none 0 | vvvthin 1e-06 | .3rs .3 | 1e-7 1e-07 | "2 *" 2 | 1d3 1000 | 1e4 10000 | +1pt 1 | 1e400 . | *1e400 .
1e5rs, 10001, *-1, -1pt, -0.5in, *40000, 1d5, 10000.001, *-0.0001, -0.0001rs, "-1 pt"
   -> r(198) "gm_linewidth must be between 0.000 and  1.0e+04"
economist: *2 2.4 | 20000pt r(198) | 14000pt 14000 | 1pt 1 | medium .3
stcolor:   *2 .6  | 20000pt 20000  | 14000pt 14000 | 1pt 1 | medium .3
scatter mlwidth(*-1), mlwidth(-1pt): r(198) | scatter mlwidth(*2) .6 (default .3)
scatter lwidth(*-1), lwidth(-1pt): rc 0 (no line drawn, not evaluated)
line clwidth(*-1): r(198) | lfitci alwidth(*-1), alwidth(-1pt): r(198) | line alwidth(*-1): rc 0 | bar lwidth(*-1): r(198)
xline(3000, lwidth(*-1)), xline(3000, lwidth(-1)), plotregion(lwidth(*-1)), plotregion(lwidth(-1)): r(198)
user scheme "#include s2color / linewidth p THICK": the note, drawn .3 | "linewidth p .8": .8 (23.04 units)
```

Drawn stroke widths in SVG units (`graph export`, every `stroke-width` counted):
```
s2color line default 8.64 (.3 rs) | 1pt 10.00 | "1 pt" 28.80 (1 rs: a stylelist, S11) | .5cm 141.73 (14.17 pt)
vvvthin 3.00 | vvthin 3.00 | 1e-7 3.00   (a non-zero width is floored at 0.3 pt)
none 0.00 | THICK 8.64 (default) | thick 23.04
economist default 19.01 (1.2 rs) | abc 19.01 (the scheme's, not medium's 4.75) | *2 38.02 | 1pt 10.00 | medium 4.75
stcolor default 9.72 | 1pt 10.00 | abc 9.72
xline default 8.64 | xline lwidth(*2) 17.28 (2 x xyline) | 1pt 10.00 | none: not drawn
xline(3000, lwidth(1 pt)) 10.00 and plotregion(lwidth(1 pt)) 10.00   (a graph sub-option reads "1 pt" as 1 pt)
plotregion(lwidth(*2)) 11.52 (2 x linewidth plotregion thin) | lwidth(thick) 23.04
scatter outline 8.64 | mlwidth(*2) 17.28 | mlwidth(vvvthin) 3.00
bar outline 5.76 (pbar thin) | bar lwidth(*2) 11.52 | economist bar 3.00 (pbar vvthin, floored)
lfitci alwidth(*2): the band outline 34.56 against 17.28 by default (twice)
```

So twoway's rules are as follows:
- Widths are linear in Stata units. The bound is 0 to 10,000 on the value in Stata units, so the same `#pt` passes under stcolor and is refused under economist.
- `*#` multiplies the site's own default: the plot's p# width, the scheme's `xyline`, `plotregion` or `pbar` width, or the marker outline.
- A non-zero stroke is floored at 0.3 pt, and the scheme's widths are floored too.
- Names are case-sensitive. An unknown name is noted and the plot's default drawn.
- A negative multiplier, a negative unit or an `rs` value above 10,000 is r(198) with `gm_linewidth must be between 0.000 and  1.0e+04`, where twoway evaluates the width.
- A graph sub-option reads a blank before a unit as that unit. A plot option is a stylelist, so `1 pt` is two elements (S11).

### E5 — dash.ado (not indexed; read and grep at `c96facd`)

`_dash_option_rules`, 2025-2045. The four line options share one rule form, and `alwidth()` carries twoway's type list:
```stata
2029        msize=style  mlabsize=style  mlabgap=style ///
2030        lwidth=style,0,10000  mlwidth=style,0,10000 ///
2043        clwidth=style,0,10000 ///
2044        alwidth=style,0,10000@lfitci|qfitci|lpolyci|fpfitci|area|bar|spike|...
```
`_dash_validate_value`, 2125. Its style branch (2261-2274) bounds only a bare number and refuses a digits-only overflow. `-1pt`, `*-1` and `1e5rs` pass as names:
```stata
2268        if "`p1'" != "" & "`p2'" != "" {
2269            if `isnum' {
2270                if `R' < `p1' | `R' > `p2' local bad "a name or a number between `p1' and `p2'"
2271            }
2272            else if `numlike' local bad "a name or a number between `p1' and `p2'"
```
Its message (2511-2514) is dash's own: `mata: _dash_say("err", "`prefix': `opt'() must be `bad' (got: ", st_local("value"), ")`extra'")`, then `exit 198`. Measured (research p1-12, Measurement B): `dash line …, lwidth(*-1)` and `lwidth(-1pt)` give a note and rc 0. `dash line …, lwidth(-1)` gives r(198) `must be a name or a number between 0 and 10000`. The rule grammar's fourth parameter is already used by `level=num,0,100,x`. `_dash_say(style, before, value, after)` is dash_parse.mata:676.

The help documents the bounds at dash.sthlp:690-697 ("{cmd:lwidth()} and {cmd:mlwidth()} 0 to 10000") and the every-type rule at 744-752 ("{cmd:scatter mpg weight, lwidth(-1)}, which {cmd:twoway} draws, is refused"). The line options paragraph is at 3275-3281, and the scheme Units paragraph at 3424-3434 ("A {cmd:linewidth} number is Stata's own unit, {cmd:medium} being 0.30, so {cmd:economist}'s {cmd:linewidth p 1.2} draws four times as wide as {cmd:s2color}'s lines", which stays true).

### E6 — measured gitnexus impact (`gitnexus impact <symbol> -d upstream -r dash`, 03oct2026 at `c96facd`)

| symbol | risk | impacted / direct / processes |
|---|---|---|
| `GlyphMapper._apply_line_opts` | CRITICAL | 40 / 26 / 26 |
| `GlyphMapper._apply_marker_opts` | CRITICAL | 12 / 7 / 8 |
| `OptionTranslator.translate_lwidth` | HIGH | 10 / 3 / 3 |
| `GlyphMapper._ci_band_style` | HIGH | 6 / 1 / 3 |
| `SchemeParser._lwidth` | LOW | 6 / 3 / 2 |
| `SchemeParser._plot_lwidth_of` | LOW | 4 / 2 / 2 |
| `SchemeParser._bounded_lwidth` | LOW | 2 / 1 / 2 |
| `_extract_region_lwidth` | LOW | 3 / 1 / 2 (the served caller is a string: confirmed by grep at 35249) |
| `_dash_refline_draw` | LOW | 3 / 1 / 1 |
| `OptionTranslator.resolve_size` | not at `c96facd` (S08) | measured at the batch-5 base |
| dash.ado `_dash_option_rules`, `_dash_validate_value` | UNKNOWN (not indexed) | grep: callers in E5 |

HIGH/CRITICAL warning: `_apply_line_opts` and `_apply_marker_opts` feed every plot type, so 13-14 re-runs every file of E9, both-mode suites included, and 13-17's full run is the backstop. A seventh `_dash_validate_value` caller at 7456 (the scheme rule) never reaches the style branch.

### E7 — S08's contract S13 builds on (section-08 TR-08.1 to TR-08.7)

`resolve_size(value, kind, default_pt, ref_in=4.0)` returns signed points. In order it tries `size_multiplier` (`*` then a Stata number), then `stata_number` (× 2.88), then a number with optional blanks and `pt`/`in`/`cm`/`rs`, then the kind's relative ladder, then its points ladder. Anything else raises ValueError, as does a value longer than 64 characters or a magnitude above `_SIZE_MAX_RS` (1,000) × 2.88. `ref_in` is used when finite and positive, else 4.0. GlyphMapper sites read `getattr(self.scheme, "size_ref_in", 4.0)`, and module sites read `OptionTranslator.size_ref_of(fig)`. S13 needs a per-kind maximum (10,000 for lines) and a line ladder. Both are S13's edits to `resolve_size` (TR-13.2). If S08 landed a different signature or names, S13 uses the landed ones and records the difference in its commit body. If `resolve_size` is missing, stop and report.

### E8 — fixtures on disk

- `test/fixtures/linewidth_chain_truth.json` and `marker_linewidth_truth.json` record Stata units per plot and scheme. `test_scheme_linewidth.py::_px` (:91-97) turns them into pixels through `translate_lwidth` and `_LWIDTH_PX_PER_UNIT`. After S13 that is `line_px(units × 2.88)` (one rule), so those tests stay fixture-driven.
- `test/fixtures/scheme_truth.json` `_meta.units.linewidth.dash_rule` (written by `scripts/extract_scheme_truth.py:2138-2144`) says "px = value * 5.0 … keywords still go through `OptionTranslator._LWIDTH_MAP`". No test reads it. It is generated, so S13 does not touch it. S15 regenerates in this batch and owns the sentence (Notes).
- New: `test/fixtures/line_width_truth.json` (Stata truth, below).

### E9 — tests that pin today's behaviour (flip in place, never delete)

**How measured.** The prototype tree was run against the file list `grep -lE "translate_lwidth|_LWIDTH|line_width|lwidth|mlwidth|clwidth|alwidth|outline_line|xyline|plot_line_width|_lwidth|grid_line_width|axis_line_width|vvvthick|SINGLE_Y_BASELINE" test/test_*.py`, plus every `test_help_claims_*.py`, `test_scheme*.py`, `test_glyphs.py` and `test_dual_axis.py`: 54 files run as a list, `-n 6`. The list, each under `test/`, is: test_adversarial_matrix.py test_axis_options.py test_ci_band_style.py test_ci_plot_index.py test_dropline_marker_options.py test_dual_axis.py test_emptied_layer_style.py test_example_simulation.py test_glyphs.py test_help_claims_1.py … test_help_claims_8.py (all eight) test_help_conformance.py test_html_output.py test_html_verification.py test_immediate_dashboards.py test_immediate_values.py test_marker_label_parity.py test_mode_parity.py test_option_validation.py test_options.py test_pccapsym_pcarrowi.py test_phase4_plots.py test_polyline_ordering.py test_qualifier_logic.py test_saved_filter_layers.py test_saved_stale_cue.py test_scheme.py test_scheme_coercion.py test_scheme_consumption.py test_scheme_fallback_provenance.py test_scheme_fidelity.py test_scheme_grid_measured.py test_scheme_grids.py test_scheme_integration.py test_scheme_linewidth.py test_scheme_quoted_values.py test_scheme_rendered_output.py test_scheme_resolution.py test_scheme_review_fixes.py test_scheme_visual_truth.py test_security_surface.py test_server.py test_suboption_warnings.py test_textbox_grammar.py test_textbox_no_text.py test_twoway_option_parity.py test_unsupported_report_is_true.py test_varlist_expansion.py. 13-14 adds `test_line_width_units.py` and S08's `test_size_units.py` to it. The result was `544 failed, 13034 passed in 706.59s`. The same 52 test functions (814 nodes) on the unmodified copy gave `814 passed in 23.44s`, so every failure is S13's. Each red test pins a pixel value of the private ladder. The new values are Stata units × 3.84 px: thin .768, medium 1.152, vthin .576, thick 3.072, vthick 5.376, vvvthick 16.128, and a number n gives n × 3.84.

| Test (file::Class::test) | Pin today | Flip to |
|---|---|---|
| `test/test_ci_band_style.py::TestTheBandAgainstStata::test_each_measured_case` (398 params), `::TestBothModes::test_the_band_is_drawn_as_stata_draws_it` (50), `::TestAdversarial::test_a_pstyle_dash_does_not_know_is_p1` (16) | module table `_UNIT_PX = {0.3: 1.5, 0.8: 2.5, 0.15: 0.5, 1.2: 6.0, 0.0: 0.0}` (:89) | `{0.3: 1.152, 0.8: 3.072, 0.15: 0.576, 1.2: 4.608, 0.0: 0.0}` (one edit) |
| `test/test_ci_band_style.py::TestTheSchemeKeys::test_a_user_schemes_ci_keys_are_read` (:254, assert :265), `::test_a_user_schemes_other_keys_are_read` (:268, assert :277) | 2.5, 3.5 | 3.072, 5.376 |
| `test/test_scheme_linewidth.py::TestTheChainAgainstStata::test_each_measured_plot` (8 economist params), `::TestMarkerOutlinesAgainstStata::test_each_measured_marker` (10), `::TestMarkerOutlinesAgainstStata::test_after_a_ci_fit` | helper `_px` (:91-97), `unit * SchemeParser._LWIDTH_PX_PER_UNIT` (deleted) | `dr.OptionTranslator.line_px(unit * dr.OptionTranslator.PT_PER_RS)` for every unit, one rule |
| `test/test_scheme_linewidth.py::TestVvvthick::test_on_the_ladder` (:632), `::test_a_scheme_reads_it` (:643); `::TestBothModesDrawVvvthick::test_lwidth_and_mlwidth` (:659, both modes) | 6.6; `tr(" VVVTHICK ") == 6.6` | 16.128; `pytest.raises(ValueError)` for `" VVVTHICK "` (names are case-sensitive, E4). The class docstring is rewritten from the 0.588 power law to the linear ladder |
| `test/test_scheme_rendered_output.py::TestTheGlyphSizes::test_the_line_width_is_the_schemes_on_statas_scale` (economist rows, both modes) | `PX_PER_LINEWIDTH_UNIT = 5.0` (:85), read by `_line_width_px` (:154-162) | `3.84  # 2.88 pt x 4/3 per Stata unit (WP-30 P1.12b)`, and the docstring of `_line_width_px` |
| `…::TestAC162TheEconomistLineIsThickerThanS2colors::test_6_0_over_1_5` (:627, both modes) | `(6.0, 1.5)` | `(4.608, 1.152)`. The name is kept and the class docstring says the old numbers were dash's private scale |
| `…::TestTheUnitFunctions::test_a_numeric_linewidth_is_5px_per_stata_unit` (:849-853, 3 params), `::test_medium_keyword_still_anchors_at_1_5` (:855-857) | `("1.2", 6.0), ("0.30", 1.5), ("3.5", 17.5)`; 1.5 | `("1.2", 4.608), ("0.30", 1.152), ("3.5", 13.44)`; 1.152 |
| `test/test_scheme_review_fixes.py::TestAxisLineWidth::test_a_numeric_axisline_is_a_stata_linewidth_unit` (:494, both modes) | `linewidth axisline 0.6` → 3.0 (:504) | 2.304 |
| `…::TestHostileSchemeValues::test_every_negative_linewidth_is_refused` (params `linewidth minor_grid` :554 and `linewidth axisline` :555 only) | default 0.8 (minor grid, axis line: the `thin` rung) | 0.768. The `linewidth p` row (:553, 1.5), `test_three_hostile_values_give_three_warnings_and_the_defaults` (:544, grid 0.8) and `test_the_hostile_scheme_still_renders` (:583, grid 0.8) read `_init_properties`' pixel literals, which S13 does not edit (D-13g): they stay green here and are S15's flips |
| `test/test_scheme_coercion.py::TestLineWidth::test_a_numeric_value_is_a_stata_linewidth_unit` (:227-236) | 3.5 → 17.5; 0.30 → 1.5 | 13.44; 1.152. The docstring says one unit is 3.84 px |
| `test/test_options.py::TestTranslateLwidth::test_numeric_string_passthrough` (:190-192) | `"2.5"` → 2.5 | 9.6. The name is kept and the docstring says a number is Stata units |
| `test/test_server.py::TestServerLineWidthAllTypes` (class :1500): `test_lfit_applies_lwidth` (:1610), `test_qfit…` (:1621), `test_connected…` (:1632), `test_lowess…` (:1643), `test_kdensity…` (:1654), `test_mspline…` (:1664), `test_tsline…` (:1675), `test_rspike…` (:1686), `test_rline…` (:1697), `test_function…` (:1708), `test_tsrline…` (:1719), `test_rconnected…` (:1730), `test_rcapsym…` (:1741), `test_pcspike…` (:1752), `test_pcarrow_applies_lwidth` (:1764), `test_pcbarrow_applies_lwidth` (:1776), `test_pcarrow_lwidth_applies_to_arrow_annotations` (:1788), `test_pcbarrow_lwidth_applies_to_arrow_annotations` (:1801) | `lwidth(thick)=2.5`: the `target_lw=2.5` defaults of `_has_renderer_with_lw` (:1592) and `_has_arrow_with_lw` (:1602), and each literal 2.5 | a class constant `_THICK_PX = 3.072  # Stata's thick, .8 units x 3.84 px (WP-30 P1.12b)`, used in both defaults, every assertion and every docstring |
| `test/test_glyphs.py::TestMapSpike::test_spike_lwidth_applied` (:363-367) | `lwidth("3")` → 3.0 | 11.52 |
| `test/test_glyphs.py::TestMapPcarrow::test_pcarrow_lwidth_applied` (:1631), `::test_pcarrow_lwidth_applies_to_arrow_annotations` (:1647), `::TestMapPcbarrow::test_pcbarrow_lwidth_applied` (:1679), `::test_pcbarrow_lwidth_applies_to_arrow_annotations` (:1695) | 2.5 | 3.072 |
| `test/test_html_output.py::TestLineWidthPatternHtml::test_lwidth_thick_in_line_html` (:2099), `::test_lwidth_applied_to_spike` (:2126), `::test_lwidth_applied_to_bar` (:2137), `::test_lwidth_applied_to_histogram` (:2148) | `[2.5]*20` and the scheme's `[1.5]*20` (:2109, :2112); vthick `[3.5]*20` (:2135); `[2.5]*20`, `[2.5]*4` | `[3.072]*20`, `[1.152]*20`; `[5.376]*20`; `[3.072]*20`, `[3.072]*4` |
| `test/test_phase4_plots.py::TestMapPcspike::test_pcspike_lwidth_option_applied` (:125-128) | 2.5 | 3.072 |
| `test/test_polyline_ordering.py::test_a_degraded_layer_still_applies_lwidth` (:283, 7 params, assert :314, docstring :291-295) | 2.5 | 3.072 |
| `test/test_help_claims_7.py::TestRegionColours::test_the_option_sets_the_property` (row `_REGION` :197, both modes) | `("plotregion", "lwidth(2)", "outline_line_width", 2.0)` | `… 7.68)` |
| `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` (:393; `_SINGLE_Y_BASELINE_SHA256` :343) | the page digest | re-derived in 13-16, written with `# <old> -> <new>: P1.12b every default line, outline, grid and axis width moves to Stata's units` (R10) |

Pinned by the design but not by the standalone prototype (13-03 and 13-09 measure them red):
- `test/test_option_validation.py::TestTheTableIsWellFormed::test_the_contract_tokens_are_all_there` (:213). `CONTRACT_PLOT_RULES` (:69-84) `lwidth=style,0,10000  mlwidth=style,0,10000` becomes `lwidth=style,0,10000,u  mlwidth=style,0,10000,u`. The count of 41 is unchanged.
- `test/test_option_validation.py::TestTheTableIsWellFormed::test_the_parameters_fit_the_kind` (:249, the four line-option params). The `style`/`istyle` branch allows `len(ps) == 3` only for `style` with `ps[2] == "u"`, beside 0 and 2.
- The scheme-keyword note (TR-13.5) may add one warning to a hostile-scheme test that writes an unknown width keyword. 13-12 re-runs `test_scheme_coercion.py`, `test_scheme_review_fixes.py` and `test_scheme_consumption.py` and flips any such count in place, naming it in `13-flips.txt`, and 13-14 re-runs E9's whole list.

Not red, kept as written: `test/test_twoway_option_parity.py::…::test_clwidth_has_lwidths_bounds` (:300-307, a substring of the new rule), and `test/test_help_claims_7.py:1088` and `test/test_help_claims_2.py:275` (their sentences are kept word for word in 13-16). The cscripts read rc and option names only: `test_option_validation.cscript` OV-09/OV-12/OV-150, `test_help_claims_2.cscript` HC2-04I/J and HC2-18l/o, `test_ci_band_options.cscript` CB-01, `test_twoway_option_parity.cscript` TP-01 and `test_help_claims_8.cscript` HC8-14. 13-15 runs each. E9 expects no change there, so a FAIL is reported to the orchestrator: an area-script flip needs a task of its own (three files per task).

## User stories

- **US-13.1** As a twoway user, I want `lwidth(thick)`, `lwidth(.5)`, `lwidth(1pt)` and `lwidth(*2)` to draw as wide, relative to my other lines and text, as they draw in Stata, so a do-file's line hierarchy survives on the dashboard.
- **US-13.2** As a twoway user, I want `lwidth(vvvthin)` and `lwidth(none)` to work, and `lwidth(THICK)` to be named as twoway names it, so every width my graphs use is honoured or reported, never silently changed.
- **US-13.3** As a dashboard publisher, I want the default lines, grids, axes and outlines of every shipped scheme drawn at the scheme's own widths in Stata's proportions, in the saved page and the served app alike, so readers see the same picture as in a Stata report.
- **US-13.4** As a twoway user, I want `lwidth(*-1)` or `lwidth(-1pt)` refused with twoway's message and return code, so a mistake in my do-file fails in dash where it fails in twoway.
- **US-13.5** As a dashboard publisher, I want `mlwidth()`, `clwidth()`, `alwidth()`, `plotregion(lwidth())` and `xline(…, lwidth())` to read widths by the same rule as `lwidth()`, unchanged by a filter move.

## Business requirements

Each holds in both modes and after any filter move (BR-30.38), under every shipped scheme.

- **BR-13.1** A line width is in Stata's units on the one unit of IR-1: 1 unit = 2.88 pt = 3.84 px. Every keyword of Stata's linewidth ladder draws its Stata value: `none` 0, `vvvthin` .000001 … `vvvthick` 4.2. `lwidth(.3)` draws the s2color default line, and `lwidth(thick)/lwidth(medium)` is 8/3.
- **BR-13.2** `#rs` is relative. `#pt`, `#in` and `#cm` are absolute at the graph's reference length (S08). `*#` multiplies the width the site would otherwise draw: the plot's scheme width, the marker outline, the band outline, the scheme's `xyline` width, or the plot-region width (D-13d). A graph sub-option's blank before the unit is read as the unit.
- **BR-13.3** A non-zero width below 0.3 pt is drawn at 0.3 pt (0.4 px). A zero width (`none`, `0`, `*0`, `0pt`) draws nothing, silently.
- **BR-13.4** The default line is 1.152 px under s2color (economist 4.608), and every scheme `linewidth` key reads by the same rule as an option. An explicit keyword or number equal to the scheme's draws exactly the scheme's width.
- **BR-13.5** A name is case-sensitive. An unknown or wrong-case name, in an option or in a user's scheme file, is noted once and the site's default is drawn, as twoway draws it.
- **BR-13.6** `lwidth()`, `mlwidth()`, `clwidth()` and `alwidth()` holding a negative number, a negative multiplier, a negative unit form, a number above 10,000 or an `rs` value above 10,000 are refused with r(198) and twoway's words, `gm_linewidth must be between 0.000 and  1.0e+04`, followed by one line that names the option and the value. This holds on every route and on every plot type the rule applies to today (D-13c). `alwidth()` keeps its type list.
- **BR-13.7** A positive `*#` or absolute unit whose value passes 10,000 units only at render time is noted and drawn at the site's default (D-13b; twoway refuses it).
- **BR-13.8** No width reaches the page as text. Every width is a finite float in the page's JSON, and no user text reaches HTML, CSS or JS from a width option.

## Technical requirements

All in `dash_render.py` unless named. The line numbers are `c96facd`'s, so find the quoted text.

- **TR-13.1 The ladder on `OptionTranslator`** (class 5098). Replace the `_LWIDTH_MAP` banner and dict (5321-5341) with:
  - the banner comment `# Stata linewidth keyword -> Stata units (style/linewidth-<name>.style, set val)`;
  - `_LWIDTH_RS: dict = {"none": 0.0, "vvvthin": 0.000001, "vvthin": 0.01, "vthin": 0.15, "thin": 0.2, "medthin": 0.25, "medium": 0.3, "medthick": 0.45, "thick": 0.8, "vthick": 1.4, "vvthick": 2.6, "vvvthick": 4.2}`, with a comment quoting E1 and the measurement date;
  - `_LWIDTH_MAX_RS: float = 10000.0` (twoway's `gm_linewidth` bound);
  - `_LWIDTH_FLOOR_PT: float = 0.3` (the SVG writer's floor, E4).

  `_LWIDTH_MAP` is deleted. Its only readers are `translate_lwidth` (5591-5592) and docstrings at 6628-6629 and 5933, and no test reads it (grep). Append `"line"` to S08's `_SIZE_KINDS`.
- **TR-13.2 The line kind of `resolve_size`** (S08's method). In step (4), the relative ladder for `kind == "line"` is `_LWIDTH_RS`. Step (5) has no points ladder for lines. The magnitude check uses `_LWIDTH_MAX_RS` for `"line"` and `_SIZE_MAX_RS` for the other kinds. Nothing else in the method changes, so markers, text and gaps are untouched: S08's tests are the guard.
- **TR-13.3 `@staticmethod line_px(pt) -> float`** (new, on `OptionTranslator`). It returns `0.0` for `pt == 0` and `max(pt, _LWIDTH_FLOOR_PT) * PX_PER_PT` for a finite `pt > 0`. It raises ValueError for a negative or non-finite `pt`. It is the one pixel rule for every line width, option and scheme alike.
- **TR-13.4 `translate_lwidth(value, default_px=None, ref_in=4.0) -> float`** (5578) becomes a thin wrapper:
  1. `default_pt = default_px * 0.75` when `default_px` is a finite float ≥ 0, else `_LWIDTH_RS["medium"] * PT_PER_RS`.
  2. `pt = resolve_size(value, "line", default_pt, ref_in)` (ValueError passes up).
  3. If `pt < 0`, raise ValueError. dash.ado refuses the plot options before, and a graph sub-option is noted until S38/S39 refuse it (M5).
  4. Return `line_px(pt)`.

  `value` is not lower-cased (BR-13.5). The docstring cites E4, IR-1 and P1.12.3. Its existing callers with one argument keep working.
- **TR-13.5 The scheme on the same rule** (`SchemeParser`, class 5646).
  - Delete `_LWIDTH_PX_PER_UNIT` (5930-5934) and its comment, and point the `_lwidth` docstring at `line_px`.
  - In `_lwidth` (6625), drop `.lower()` (6635). A float `val` that is finite and ≥ 0 returns `OptionTranslator.line_px(val * OptionTranslator.PT_PER_RS)`. The negative branch stays.
  - A keyword is still read through `OptionTranslator.translate_lwidth(raw)`. On ValueError, warn once in the negative branch's form, `dash scheme: line width '<_dash_display(raw)>' (from '<key>') is not a recognised line width; using <default:g>px.`, and return `default` (BR-13.5; twoway notes it, E4).
  - The signature default `1.5` becomes `None`, read as `OptionTranslator.translate_lwidth("medium")`.
  - `_init_properties` is not edited (D-13g; S15 turns its two pixel literals into rungs). The other callers already pass rungs.
  - `_LWIDTH_MAX_PX` (100 px) stays dash's own scheme bound.
- **TR-13.6 The appliers** (S13 is batch 5's one editor, R12).
  - `_apply_line_opts` (8602-8606): `glyph.line_width = self.tr.translate_lwidth(options["lwidth"], glyph.line_width, getattr(self.scheme, "size_ref_in", 4.0))`, and catch `(ValueError, TypeError)`, keeping the note (`_lw_name`, "line width"). A glyph whose `line_width` is a field spec, not a number, is passed `default_px=None`.
  - `_apply_marker_opts`. The `mlwidth()` site (8753-8759) gets the same change against the marker glyph's `line_width`. The `lwidth()` validation site (8731-8735) stays a check only, now case-sensitive through the wrapper.
  - `_ci_band_style` (8354-8367): delete the `none` special case and the `0.0 <= w <= 1000.0` cap. Set `st["line_width"] = self.tr.translate_lwidth(str(val), st.get("line_width"), getattr(self.scheme, "size_ref_in", 4.0))`, and on ValueError note and `continue` as today. `line_none` (8400) already treats 0 as no outline.
  - No mapper is edited. Every mapper reaches these appliers, and `map_area`'s border line (10107-10116) and the arrowheads (`arrow_lw = seg.glyph.line_width`, 14083, 14164) follow them.
- **TR-13.7 Graph-level sites.**
  - `_extract_region_lwidth(val, default_px=None, ref_in=4.0)` (5065). It calls `translate_lwidth(raw, default_px if default_px is not None else OptionTranslator.translate_lwidth("thin"), ref_in)` (D-13d), with the note unchanged.
  - `_dash_refline_draw` (26327). The no-scheme default `1.0` becomes `OptionTranslator.translate_lwidth("medium")`. The `lwidth` sub-option calls `OptionTranslator.translate_lwidth(style["lwidth"], kw["line_width"], OptionTranslator.size_ref_of(fig))`, and `lcolor`/`lpattern` keep their calls. Split the loop's lwidth row into its own `try` with the same note and `using` ("the default").
  - Neither call site of `_extract_region_lwidth` is edited (R12).
- **TR-13.8 dash.ado.**
  - **`_dash_option_rules`** (2030, 2043, 2044): the four rules become `lwidth=style,0,10000,u`, `mlwidth=style,0,10000,u`, `clwidth=style,0,10000,u` and `alwidth=style,0,10000,u@<the same type list>`. The comment above the table gains one sentence: "`,u` reads the value in Stata's line-width units (WP-30 P1.12b)".
  - **`_dash_validate_value`, style branch** (2261-2274). When `"`p3'" == "u"`, the value is read through the scalar `T` with the existing number pattern (call it NUM: `[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eEdD][-+]?[0-9]+)?`):
    - **(a)** `regexm(scalar(`T'), "^\*(NUM)$")` is a multiplier. Missing `real()` (overflow) passes as a name (twoway accepts `*1e400`, E4). Below 0 is out of range.
    - **(b)** `regexm(scalar(`T'), "^(NUM) *(pt|in|cm|rs)$")` is a unit form. Missing `real()` passes as a name. Below 0 is out of range, and `rs` above `p2` is out of range. `pt`, `in` and `cm` have no upper bound here (D-13b).
    - **(c)** A bare number keeps today's test, now out of range when `R < p1 | R > p2`. The digits-only overflow keeps today's words (P2.14).
    - **(d)** Anything else passes as a name.
  - **The refusal.** When (a), (b) or (c) is out of range, print twoway's line, then dash's, and exit 198:
    ```stata
    mata: _dash_say("err", "gm_linewidth must be between 0.000 and  1.0e+04", "", "")
    mata: _dash_say("err", "`prefix': `opt'() must be a line width from 0 to 10000 Stata units (got: ", st_local("value"), ")")
    exit 198
    ```
    This is placed inside the branch, before the shared `bad` message (2511).
  - **Other kinds.** A style rule without `u` (`msize`, `mlabsize`, `mlabgap`, `msangle`, `xsize`, `ysize`) is untouched, byte for byte. Every program keeps S03's `version 19`. No program is added, so `program_coverage_map.py` is unchanged and its `_dash_validate_value` entry (OV-100) stays.
- **TR-13.9 Both modes.** The three classes travel whole. `_extract_region_lwidth` (33388) and `_dash_refline_draw` (33383) change in place. R2 row S13: no constant or function is added to either tuple, and `_shared_stat_lines` is unchanged. `line_px` is an `OptionTranslator` method. `TestTheServedAppCarriesEveryName` (with S01's `test_every_listed_name_exists`) and `TestTheServedAppDefinesEveryNameItReads` stay green (G4). There is no JavaScript twin: no saved-page script reads or writes a width (E2). A served filter move rebuilds data only, which `TestAfterAFilterMove` pins.
- **TR-13.10 Registries.** Under S13's anchor in `test/function_test_map.py` `FUNCTIONS`, add `'OptionTranslator.line_px': 'test/test_line_width_units.py::TestTheUnitFunctions::test_line_px_floors_and_converts'`. Existing keys are kept, and their nodes still exist after the flips (`OptionTranslator.translate_lwidth` → `test_options.py::TestTranslateLwidth::test_all_lwidth_keywords_positive`; `SchemeParser._lwidth` → `test_scheme_coercion.py::TestLineWidth::test_a_named_width_is_translated`; `_extract_region_lwidth`, `_dash_refline_draw` unchanged). `program_coverage_map.py` is unchanged.
- **TR-13.11 Security (rule 1).** A width reaches Bokeh only as a float from `line_px`, and never as text. `resolve_size`'s regular expressions are anchored with no nested quantifier, so a 1 MB value is judged in under 0.1 s. A value over 64 characters is a name, echoed through `_dash_display` (80 printable characters). dash.ado reads the value only through the scalar `T` and echoes it through `_dash_say`, never inside quotes or a macro expansion. The `,u` patterns are fixed strings. The extractor's python block reads `git rev-parse HEAD` from a file the do-file wrote with `shell`, never calls Stata, and never uses `shell=True`. No `eval` or `exec` reads a width.

## Boundaries

- **Batch partners (do not edit their functions).** S14 owns `map_bar`/`map_rbar` bar widths, rcap cap length, `map_rcapsym`'s end markers, `_tag_spacing`, `_FILTER_JS`'s spacing writer, `_build_filter_widgets` and `_dash_copy_redraw_geometry`. S15 owns `scripts/extract_scheme_truth.py` (including the `linewidth` `dash_rule` sentence, E8), the 26 scheme files, `scheme_truth.json`, `SchemeParser.apply_to_figure`/`apply_to_axis`, the chrome attributes it adds to `_init_properties` and `_FALLBACK_PROPS`, `_dash_add_secondary_axes`, `_dash_finish_secondary_axes`, `_dash_textbox_place`, and the help's Stata scheme support paragraphs (R3), including the Units paragraph (3424-3434), whose line-width sentence stays true and is not edited here.
- **Earlier sections.** S08 owns `resolve_size`'s marker, text and gap kinds, `stata_number`, `size_multiplier`, `css_pt`, `size_ref_of`, `_SIZE_MAX_RS` and every size site. S13 only adds the line kind (TR-13.2). S11 owns the stylelist splitter.
- **Later sections.**
  - S31: axis line width, tick length, `tlength()`; `tlwidth()` and `glwidth()` are named and unowned (D-13f).
  - S32/S36: named styles' widths.
  - S33: ColorBar chrome.
  - S38: region readers, region refusals (`plotregion(lwidth(-1))` is r(198) in twoway, E4), and the region default and reference (D-13d).
  - S39: `xline` refusals, including `lwidth(-1)` and `lwidth(*-1)`, and `lstyle()`.
  - S50: `xline` `style()`.
  - S43: bare `*#` colours.
  - S48: `iscale()`.
  - P2.13: `scale()`.
  - S08 (batch 3, landed): the sync of the nonselection and muted copies (A37, ratification 06oct2026). S13 keeps it where S08 put it, and its width writes stay inside `_apply_line_opts` and `_apply_marker_opts`, before the sync runs.
  - P2.21: per-type narrowing of the width refusals (D-13c).
- **Not edited:**
  - the R12-locked functions (`_generate_app_source`, `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets`) and `_apply_mlabel_opts`, `_apply_fill_opts`;
  - `_dash_style_note`, `_dash_warn_once`, `_dash_reset_notes`, `_dash_display` (CRITICAL helpers);
  - `_apply_colorvar`, `_dash_apply_z_options`, `_dash_parse_axis_spec`;
  - the mappers;
  - the copy lists;
  - dash_parse.mata;
  - `_FALLBACK_PROPS`;
  - any scheme file or generated fixture;
  - tracking documents other than BUGS.md and CHANGELOG.md (A145).
- **Exclusions.** Stata 16-18.5 are not measured (M2). The GUI's screen floor is unmeasured: the 0.3 pt floor is the SVG writer's (register P1.12.3). Linux, Windows and Intel Mac are not measured (M4).

## Stata truth

**Extractor (new):** `scripts/extract_line_width_truth.do`, in S02's path-free form. Its header comment names the run line, then comes TR-02.9's root stanza with `<file>` = `extract_line_width_truth.do`, then `adopath ++ "`repo'/"`, `global dash_nobrowser 1`, `clear all`, `set more off` and `version 19`. The `_meta` locals follow `extract_join_order_truth.do`'s form (`c(stata_version)`, `c(born_date)`, `git -C "`repo'" rev-parse HEAD` written by `shell` to a tempfile and read back with `file read`, `c(current_date)`). Data: `sysuse auto, clear` then `keep in 1/5`. Each probe runs `capture noisily twoway <cmd>`, records `_rc`, the class setting where rc is 0 (`.Graph.plotregion1.plot1.style.line.width.setting`, or `.style.marker.linestyle.width.setting` for `mlwidth`), and, where the probe asks, a `graph export` SVG read in the python block by `scripts/svg_truth.py` (`svg_document`, every `stroke-width`, divided by 720/72 = 10 units per pt). The refusal words are taken from the log with `log using … , text` around each refused probe. The python block writes `test/fixtures/line_width_truth.json` with `json.dump(…, indent=1, sort_keys=True)`. It reads every local through `Macro.getLocal`, never calls Stata, and writes a backtick as `\x60`.

**Probe ids.** An id is the value, or `<type>_<option>_<value>`, with `*` written `star`, `-` written `neg`, `.` written `p` and a blank written `_` (e.g. `line_lwidth_starneg1`, `line_lwidth_neg1pt`, `forms.p3`, `forms.star2`). Case is kept (`forms.THICK`).

**Probe keys** (all s2color unless the key names a scheme):
- `ladder.<kw>` for each of the 12 keywords: `{rc, setting}`.
- `forms.<id>`: `{value, rc, setting, stroke_pt}` for `.3`, `2`, `1pt`, `.5cm`, `1in`, `10000rs`, `1e-7`, `*2`, `*0`, `0pt`, `none`, `vvvthin`, `vvthin`, `THICK`, `Thick`, `1PT`, `20000pt`, `*33333`, `1d3`, `+1pt`.
- `refusals.<id>`: `{option, type, value, rc, words}` for `line lwidth(*-1)`, `line lwidth(-1pt)`, `line lwidth(-0.5in)`, `line lwidth(1e5rs)`, `line lwidth(-1)`, `line lwidth(10001)`, `line lwidth(*-0.0001)`, `line lwidth(-0.0001rs)`, `scatter mlwidth(*-1)`, `scatter mlwidth(-1pt)`, `line clwidth(*-1)`, `lfitci alwidth(*-1)`, `lfitci alwidth(-1pt)`, `bar lwidth(*-1)`, and the accepted controls `scatter lwidth(*-1)` (rc 0), `line alwidth(*-1)` (rc 0), `line lwidth(*40000)` (198, D-13b), `economist line lwidth(20000pt)` (198, D-13b).
- `schemes.<scheme>.<id>`: `{setting, stroke_pt}` for `default`, `abc`, `*2`, `1pt`, `medium` under `economist` and `stcolor`.
- `sites.<id>`: `{stroke_pt}` for `xline_default`, `xline_x2` (`xline(3000, lwidth(*2))`), `xline_1pt`, `xline_1_pt` (`lwidth(1 pt)`), `plotregion_x2` (with `lcolor(red)`), `plotregion_thick`, `scatter_outline`, `mlwidth_x2`, `bar_outline`, `bar_x2`, `economist_bar_outline`, `lfitci_outline`, `lfitci_alwidth_x2`.
- `user_scheme.THICK`: `{rc, setting, note}`, from a scheme file the do-file writes into its scratch working directory.
- `floor_pt: 0.3` (derived: the smallest non-zero stroke over `forms`, asserted equal to 0.3 by the python block).

**`_meta`:** `stata_version`, `born_date`, `dash_commit`, `extracted`, plus `units` ("SVG 720 units per inch; 10 units = 1 pt; 1 rs = min(graph width, height)/100") and `source` (the extractor's path). The fixture is added with `git add -f test/fixtures/line_width_truth.json` and read by `test/test_line_width_units.py` (so `test_fixtures_are_committed.py` passes unedited, R7).

**Run (never the GUI, E5):**
```sh
mkdir -p <scratch>/s13/truth
DASH_REPO=$WT $WT/scripts/stata_slot.sh <scratch>/s13/truth $WT/scripts/extract_line_width_truth.do
# log: <scratch>/s13/truth/extract_line_width_truth.log ; fixture: $WT/test/fixtures/line_width_truth.json
```

**Truth block** (`test/test_wp30_truth.cscript`, between S01's `S13 start` and `S13 end` display lines of the stub `* ==== S13 P1.12b: Stata line-width ladder ====`, gated by `WP30_ONLY=S13`; TR-01.10 item 4). Python helpers `_s13_page(path)`, `_s13_app(spec, data)` and `_s13_svg(path)` sit in a `python:` block directly above the S13 header (no brace inside the gated block; any Stata helper program there declares `version 19`). They read the saved page's document JSON, build the served app with `make_document`, and read an SVG's stroke widths, returning `|`-joined widths in px, or in pt for the SVG, through an `S13_*` global; every argument crosses through `sfi.Macro`. Every page, spec and SVG is written under `` `w30_work' `` and erased before the end line, and every case reports through S01's `_w30_expect`/`_w30_done` (`LN-nn PASS: …`). Cases, each as twoway's SVG against dash's saved page and served document, as a ratio to the default line of the same graph, within 1%:
- **LN-20** `lwidth(thick)` / default = 0.8/0.3 (twoway 23.04/8.64; dash 3.072/1.152).
- **LN-21** economist `lwidth(1pt)` / default = 10.00/19.01 (dash 2.424/4.608, the reference 2.2 in through S08).
- **LN-22** `lwidth(*2)`, `mlwidth(*2)`, `xline(3000, lwidth(*2))` and `bar lwidth(*2)` are each 2 × their own default.
- **LN-23** `lwidth(vvvthin)` = 0.3 pt (0.4 px), and `lwidth(none)` = 0 with no visible stroke.
- **LN-24** `lwidth(THICK)` gives twoway's note and dash's note (S06 form), and both draw the default.
- **LN-25** economist's default bar outline is floored (twoway 3.00 units, dash 0.4 px).
- **LN-26** after a served filter move (the app's `filter()` widget fired through `_s13_app`'s document), every width of LN-20 to LN-25 is unchanged.
- **LN-27** the refusal corpus of `refusals.*`: dash's rc equals twoway's for every probe, except the two D-13b controls (twoway 198, dash 0 with the note) and `scatter lwidth(*-1)` (twoway 0, dash 198, D-13c), which are asserted as such.

**Area cases** (`test/test_option_validation.cscript`, one contiguous run after OV-168 and before the CV corpus loop, R1). `_ov_case id cmdtext expected opt [needle]` (:440-463): a refused case passes the option it must name as `opt` (OV-09's form, `198 lwidth`; `_ov_probe` counts ` <opt>()` in the log, so an empty `opt` would FAIL every refusal), and no needle, because `_ov_has` derives the registered name from an `OV-` id; an accepted case passes `0 ""`. The words are checked with `_ov_said`:
- **LN-01** `dash line mpg weight, lwidth(*-1) name(ln01)`: 198, and the log says `gm_linewidth must be between 0.000 and` and `lwidth() must be a line width from 0 to 10000 Stata units (got: *-1)`.
- **LN-02** `lwidth(-1pt)`: 198. **LN-03** `lwidth(-0.5in)`: 198. **LN-04** `lwidth(1e5rs)`: 198. **LN-05** `scatter mpg weight, mlwidth(*-1)`: 198, naming `mlwidth()`. **LN-06** `line … clwidth(-1pt)`: 198, naming `clwidth()`. **LN-07** `lfitci … alwidth(*-1)`: 198. **LN-08** `line … alwidth(*-1)`: rc 0 (not on the type list, as twoway).
- **LN-09** `lwidth(10000rs)`, `lwidth(*0)`, `lwidth(0pt)`, `lwidth(-0)`: each rc 0. **LN-10** `lwidth(20000pt)` and `lwidth(*40000)`: rc 0 (D-13b). **LN-11** `lwidth(vvvthin)`, `lwidth(none)`, `lwidth(THICK)`, `lwidth(1PT)`, `lwidth(-1PT)`, `lwidth(*1e400)`: rc 0 (names; twoway notes and draws).
- **LN-12** `lwidth(-1)`: 198, and the log now carries twoway's line before dash's (`_ov_said` with `gm_linewidth`).
- **LN-13** `scatter … lwidth(*-1)`: 198 (D-13c). **LN-14** `msize(-1pt)`, `msize(*-1)`, `mlabgap(-2pt)`: rc 0 (the `u` branch does not leak into S08's kinds).

**Area cases flipped in place (R1):** `test_option_validation.cscript` OV-09, OV-12 and OV-150 keep their rc and option needle. Their header lines (:37, :40, :239) gain "and twoway's gm_linewidth line", a comment edit made in 13-04. `test_help_claims_2.cscript` HC2-18l and HC2-18o keep rc 198 and the option needle. `test_ci_band_options.cscript` CB-01, `test_twoway_option_parity.cscript` TP-01 and `test_help_claims_8.cscript` HC8-14 compare rc and option naming only. No edit is expected in any of them. 13-15 runs each, and a FAIL is reported to the orchestrator, not flipped inside 13-15.

## TDD test stubs

### Regression tests, `test/test_line_width_units.py` (new; red at the batch-5 base unless marked guard)

Module helpers: `_figure(mode, plots, go=None, scheme="s2color")` and `_widths(fig, kinds)` (copied from `test_scheme_linewidth.py:286-336`'s form), and `_fire(doc)` (the P0.18 move harness, `test_mode_parity.py`'s `_MOVES[0]` dropdown move). `_T = json.load(test/fixtures/line_width_truth.json)` is loaded lazily in the fixture-driven classes only, so 13-01's classes run before 13-02 writes it. `_PX = 2.88 * 4 / 3`.

- Test: `…::TestTheUnitFunctions::test_line_px_floors_and_converts`. `line_px(0) == 0.0`, `line_px(0.0288) == 0.4`, `line_px(0.864) == 1.152`, and `line_px(-1)` and `line_px(nan)` raise ValueError. Red: AttributeError.
- Test: `…::TestTheLadderIsStatas::test_each_keyword_is_its_stata_units[<kw>]` (12). `translate_lwidth(kw) == line_px(rs × 2.88)`, rs from E1: thin 0.768, thick 3.072, vvvthick 16.128, vvvthin 0.4, none 0.0. Red: 0.8 ≠ 0.768, and ValueError for vvvthin and none.
- Test: `…::TestNumbersAreStataUnits::test_a_number_is_relative_units`. `".3"` → 1.152, `"2"` → 7.68, `"1e-7"` → 0.4. Red: 0.3.
- Test: `…::TestNumbersAreStataUnits::test_a_scheme_number_and_its_keyword_agree`. A SchemeParser built from `#include s2color` / `linewidth p .8` has `default_line_width` equal to that of `linewidth p thick` (3.072). Red: 4.0 vs 2.5.
- Test: `…::TestAbsoluteUnits::test_points_inches_centimetres_and_rs`. `1pt` → 4/3, `1in` → 96, `.5cm` → 18.898, `1rs` → 3.84, `10000rs` → 38400.0. Red: ValueError.
- Test: `…::TestAbsoluteUnits::test_the_reference_length_scales_them[saved|served]`. Under economist, `lwidth(1pt)` / default == 10.00 / 19.01 within 1%. Red: ValueError, then 1.5/6.0.
- Test: `…::TestTheMultiplier::test_star_multiplies_the_site_default[saved|served]`. These are the E3 "after" values: `*2` 2.304, economist `*2` 9.216, `mlwidth(*2)` 2.304, `bar lwidth(*2)` 1.536, `alwidth(*2)` 2.304, `xline(20, lwidth(*2))` 2.304, `plotregion(lwidth(*2))` 1.536 (2 × thin, D-13d), `*0` 0.0. Red: the scheme width with a note.
- Test: `…::TestVvvthinAndNone::test_vvvthin_is_the_hairline[saved|served]` (0.4) and `…::test_none_draws_nothing[saved|served]`. Line, `mlwidth`, `clwidth`, `alwidth`, `xline` and `plotregion` are 0.0, with no note (`_assert_no_note`, S06's needle helper). Red: 1.5 with a note.
- Test: `…::TestTheHairlineFloor::test_a_width_below_0_3pt_is_drawn_at_it[saved|served]`. `vvthin`, `1e-7`, and economist's default bar outline are 0.4. Red: 0.2 and 0.1.
- Test: `…::TestNamesAreCaseSensitive::test_a_capitalised_name_is_noted_and_the_default_drawn[saved|served]`. `THICK`, `Thick` and `MEDIUM` draw the default (1.152) with one note each. Red: 2.5, no note.
- Test: `…::TestNamesAreCaseSensitive::test_a_capitalised_scheme_keyword_is_noted`. A user scheme `#include s2color` / `linewidth minor_grid THICK` gives `minor_grid_line_width == translate_lwidth("thin")` (the key's rung default; D-13g keeps the `linewidth p` literal out of S13's tests) and one `dash scheme:` note naming `linewidth minor_grid`. Red: 2.5, no note.
- Test: `…::TestTheDefaultLine::test_each_shipped_scheme_draws_statas_default[<scheme>]`. For every name in `SchemeParser._BUILTIN_NAMES`, `default_line_width == line_px(units × 2.88)`, with units from `scheme_truth.json`'s `linewidth p` value, read through `_T["ladder"]` for a keyword. Red: 1.5 for s2color.
- Test: `…::TestEveryLineSiteBothModes::test_thick_at_every_site[saved|served]`. Line `lwidth(thick)`, connected `clwidth(thick)`, scatter `mlwidth(thick)`, lfitci `alwidth(thick)`, bar `lwidth(thick)`, `plotregion(lwidth(thick))` and `xline(20, lwidth(thick))` are all 3.072. Red: 2.5.
- Test: `…::TestEveryLineSiteBothModes::test_1pt_at_every_site[saved|served]`. Each is 1.3333 under s2color, except the region, which is also 1.3333 at the 4-inch reference (D-13d). Red: the default with a note.
- Test: `…::TestTheRendererBound::test_10000_units_is_drawn_and_more_is_noted[saved|served]`. `10000rs` is 38400.0. `*40000` gives the default and one note naming `lwidth(*40000)`. Red: ValueError for `10000rs`.
- Test: `…::TestTheRegionAndReflineDefaults::test_region_star_multiplies_the_default_it_is_given`. `_extract_region_lwidth("lwidth(*2)", default_px=3.0)` is 6.0, and with no default it is 1.536. Red: TypeError.
- Test: `…::TestTheRegionAndReflineDefaults::test_refline_without_a_scheme_is_medium`. `_dash_refline_draw` with `scheme=None` gives 1.152. Red: 1.0.
- Test: `…::TestTheBandOutline::test_a_wide_alwidth_is_not_dropped[saved|served]`. `alwidth(300)` is 1152.0 (the old 1000 px cap dropped it). Red: 1.5.

Guard tests (green at the base and after; listed apart in the failure file):
- Guard: `…::TestEmptyOptionsChangeNothing::test_every_line_type_draws_the_schemes_width[saved|served]`. Over `test_scheme_linewidth._SITES`' 27 types under `_SCHEME`, every line glyph width equals `plot_line_width(i, kind)`, and no note is raised.
- Guard: `…::TestAnUnknownNameKeepsTheSchemeDefault::test_economist_abc_is_the_schemes_width[saved|served]`. `lwidth(abc)` under economist equals the economist default, with one note.
- Guard: `…::TestAfterAFilterMove::test_served_widths_survive_a_move`. Fire `_MOVES[0]` on a served `line, lwidth(thick)` with `filter(rep)`, and the widths are unchanged.
- Guard: `…::TestAfterAFilterMove::test_no_saved_script_writes_a_width`. Every `CustomJS.code` of a saved page with `filter()`, plus `_FILTER_JS`, contains no `line_width`.
- Guard: `…::TestHostileWidths::test_never_raises_out_and_is_linear[<value>]`. The values are `"x"*1_000_000`, `"<script>"`, `"*1e308"`, `"nan"`, `"inf"`, `"1e400pt"`, `"*" + "9"*500` and `"-0"`. Each returns a finite float ≥ 0 or raises ValueError, in under 0.1 s.
- Guard: `…::TestNothingSerialisesAWidthAsText::test_widths_are_numbers_in_the_page`. In the saved page's JSON for `lwidth(*2) xline(20, lwidth(1pt))`, every `line_width` is an int or float.

dash.ado contract (pytest; red at the base):
- Test: `…::TestTheLineWidthRulesAreUnitAware::test_the_four_line_options_carry_u`. `_parse_rules(_BLOCK)` from `test_option_validation.py` gives `lwidth`, `mlwidth`, `clwidth` and `alwidth` with params `("0","10000","u")`, and no other rule has `"u"`. Red: no `u`.
- Test: `…::TestTheLineWidthRulesAreUnitAware::test_the_validator_quotes_twoways_words`. `_program_body("_dash_validate_value")` contains `gm_linewidth must be between 0.000 and  1.0e+04` exactly once, inside the `p3 == "u"` branch. Red: absent.

### Flips (in place; R9 `Flipped:` lines; red at the base after the edit where they assert new values)

These are exactly E9's table plus its two `test_option_validation.py` rows, re-measured by 13-03, 13-12 and 13-14, never trusted. Each node keeps its name. Each edited docstring or comment states the old scale ("dash's private ladder, medium 1.5 px") and the new rule ("Stata units, 1 unit = 3.84 px, WP-30 P1.12b"). Each test function gets one line in `<scratch>/s13/13-flips.txt`, a parametrised one once, with its parameter count: `Flipped: <node> -- <old value> was wrong because dash now draws line widths in Stata's units on Stata's ladder (WP-30 P1.12b, measured in twoway 03oct2026)`. A test that pins case-insensitivity (`TestVvvthick::test_on_the_ladder`'s `" VVVTHICK "`) is flipped to assert the ValueError, citing E4's `THICK` note.

### Guards appended to existing files (green at the base and after)

- `test/test_mode_parity.py` `CORPUS` (appended under `# WP-30 P1.12b: Stata line widths`):
  - `_case("line widths in Stata units", [plot_for("line", {"lwidth": "*2"}), plot_for("scatter", {"mlwidth": "thick"})], go={"xline": "20, lwidth(1pt)", "plotregion": "lwidth(thick)"})`;
  - `_case("vvvthin and none", [plot_for("line", {"lwidth": "vvvthin"}), plot_for("lfitci", {"alwidth": "none"})])`.

  `MOVE_CORPUS` gets `_move_case("line, lwidth(*2), dropdown", _MOVES[0], [plot_for("line", {"lwidth": "*2"})])`. `ALLOWED` and `_MUST_WARN` are not edited (R8).

### Mutation table (each must turn a named test red)

| Mutation | Red test |
|---|---|
| `_LWIDTH_RS["thin"] = 0.25` | `TestTheLadderIsStatas::test_each_keyword_is_its_stata_units[thin]` |
| drop the floor in `line_px` | `TestVvvthinAndNone::test_vvvthin_is_the_hairline` |
| `translate_lwidth` lower-cases again | `TestNamesAreCaseSensitive::test_a_capitalised_name_is_noted_and_the_default_drawn` |
| `_apply_line_opts` passes no default | `TestTheMultiplier::test_star_multiplies_the_site_default` |
| `_lwidth` keeps × 5.0 | `TestNumbersAreStataUnits::test_a_scheme_number_and_its_keyword_agree` |
| `resolve_size` line max back to 1,000 | `TestTheRendererBound::test_10000_units_is_drawn_and_more_is_noted` |
| dash.ado `u` branch skips the unit form | LN-02 |
| the `u` branch applied to every style kind | LN-14 and `test_the_four_line_options_carry_u` |
| `_ci_band_style` keeps the 1000 px cap | `TestTheBandOutline::test_a_wide_alwidth_is_not_dropped` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Ladder, numbers, units, `*#`, floor, case | pytest `test_line_width_units.py` | `line_width_truth.json` | yes, `[saved|served]` |
| Every line site | pytest `TestEveryLineSiteBothModes` | E3/E4 values | yes |
| Scheme widths on the same rule | pytest `TestTheDefaultLine`, `test_scheme_linewidth.py` (flipped) | `scheme_truth.json`, `linewidth_chain_truth.json`, `marker_linewidth_truth.json` | yes |
| After a filter move | pytest `TestAfterAFilterMove`, `test_mode_parity.py` MOVE_CORPUS | — | served move; saved script scan |
| Parity | pytest `test_mode_parity.py` CORPUS | — | yes |
| Refusals: rc and words | cscript `test_option_validation.cscript` LN-01..LN-14 | — | n/a (dash.ado) |
| twoway against dash | cscript `test_wp30_truth.cscript` S13 block, LN-20..LN-27 | live twoway SVG | yes, plus a served move |
| Contract of the rules | pytest `TestTheLineWidthRulesAreUnitAware`, `test_option_validation.py` (flipped) | dash.ado text | n/a |
| Registries | pytest `test_function_test_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` | — | served names |
| Help | pytest `test_help_conformance.py`, `test_help_claims_*.py` naming the edited lines | dash.sthlp | n/a |
| End to end | the S13 truth block builds a saved page with `dash build` and a served document per case; `test_html_verification.py` runs unchanged | — | yes |

**Acceptance criteria.**
- **AC-13.1** `translate_lwidth` gives E1's 12 rungs × 3.84 px with the 0.3 pt floor. `lwidth(.3)` equals the s2color default (1.152 px) in both modes.
- **AC-13.2** `lwidth(1pt)` is 1.3333 px under s2color, and its ratio to economist's default is twoway's 10.00/19.01 within 1%. `*2` is twice the site's default at all seven sites of `test_star_multiplies_the_site_default`.
- **AC-13.3** `vvvthin` is 0.4 px. `none`, `*0` and `0pt` are 0.0 with no note.
- **AC-13.4** `THICK` and a scheme's `linewidth p THICK` are noted once and draw the default. Economist `lwidth(abc)` draws economist's default.
- **AC-13.5** LN-01..LN-14 pass. The four line options refuse twoway's refused forms with r(198), twoway's words and the option named. `msize(-1pt)` is still rc 0.
- **AC-13.6** `WP30_ONLY=S13` prints LN-20..LN-27 PASS with no FAIL or SKIP.
- **AC-13.7** Saved and served agree for every CORPUS and MOVE_CORPUS case. The served widths are unchanged after a move, and no saved script writes a width.
- **AC-13.8** Every test of E9 has been flipped with a `Flipped:` line. `test_function_test_map.py`, both served-name guards and `test_cscript_hygiene.py` pass. One full run is green (E6 for the known flaky tests).

## Tasks

**Commit boundary.** Tasks 13-01 to 13-17 form the one P1.12b commit, made by 13-17 on `wp30-s13` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s13`, after one full run through the queue. Its subject is `Draw line widths in Stata's units on Stata's ladder and refuse the widths twoway refuses (WP-30 P1.12b)`.
- The body opens with `<scratch>/13-P1.12b-failure.txt`, then gives the measured defect (E3, E4), then what changed and where (TR-13.1 to TR-13.8, both modes), and why the single-y digest moved.
- It then carries one line each of:
  - `Regression: test/test_line_width_units.py::<Class>::<test> -- failed at <batch-5 base sha> with <text>`;
  - `Flipped: <node> -- <old expectation> was wrong because dash now draws line widths in Stata's units on Stata's ladder (WP-30 P1.12b, measured in twoway 03oct2026)` (one per line of `<scratch>/s13/13-flips.txt`);
  - `Fixture: test/fixtures/line_width_truth.json (scripts/extract_line_width_truth.do)`;
  - `BUGS.md: "Line widths use a private ladder without vvvthin or none and read numbers as pixels, and negative widths twoway refuses are accepted" (closed)`.

Every command runs from `$WT`. `<scratch>` is the WP-30 scratch directory the orchestrator hands over. No body, BUGS or CHANGELOG line names a tool or vendor (G7).

<task type="auto" id="13-01">
  <name>Write the failing line-width regression tests</name>
  <files>test/test_line_width_units.py</files>
  <action><![CDATA[
    First check the cut: `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-5-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s13`. Run `mkdir -p <scratch>/s13`. Check that `<scratch>/batch-5-impact.txt` holds E6's rows, with `OptionTranslator.resolve_size` measured at this base. If a row is missing, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout and append it, report any new HIGH/CRITICAL before editing, and confirm the dash.ado rows by `grep -n "_dash_validate_value\|_dash_option_rules" dash.ado`. Confirm S08's contract (E7): `python3 -c "import dash_render as d; T=d.OptionTranslator; print(T._SIZE_KINDS, T.PT_PER_RS, T.PX_PER_PT, callable(T.resolve_size), callable(T.size_ref_of))"` prints `('marker', 'text', 'gap') 2.88 1.3333333333333333 True True`. If it does not, stop and report.

    Create `test/test_line_width_units.py` with the module helpers and every regression class of "TDD test stubs / Regression tests" that needs no fixture: TestTheUnitFunctions, TestTheLadderIsStatas (the E1 values), TestNumbersAreStataUnits, TestAbsoluteUnits, TestTheMultiplier, TestVvvthinAndNone, TestTheHairlineFloor, TestNamesAreCaseSensitive, TestEveryLineSiteBothModes, TestTheRendererBound, TestTheRegionAndReflineDefaults and TestTheBandOutline. Expected values are the literals of E3 ("after") and E4, never computed by the code under test. The module docstring quotes the defect (E3's first block), the probe commands of E4 and their date.

    Run `python3 -m pytest test/test_line_width_units.py -q -n0 -p no:cacheprovider -rf > <scratch>/s13/13-01.log 2>&1`. Write `<scratch>/13-P1.12b-failure.txt`: the base sha, then each failing node with its one-line reason. Do not commit, and do not weaken a test to pass.
  ]]></action>
  <verify><![CDATA[`grep -c "^FAILED" <scratch>/s13/13-01.log` is at least 40; `grep -c "0.8 == \|2.5 == \|ValueError\|AttributeError" <scratch>/s13/13-01.log` is at least 4; `test -s <scratch>/13-P1.12b-failure.txt`; `git -C $WT status --porcelain` lists only `?? test/test_line_width_units.py`.]]></verify>
  <done>Every constant-expectation regression test of the section existed and was shown failing on the unmodified tree, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="13-02">
  <name>Extract twoway's line-width truth</name>
  <files>scripts/extract_line_width_truth.do, test/fixtures/line_width_truth.json</files>
  <action><![CDATA[
    Create `scripts/extract_line_width_truth.do` exactly as "Stata truth / Extractor" specifies. It opens with a header comment naming the run line, then TR-02.9's root stanza, `adopath ++ "`repo'/"`, `global dash_nobrowser 1`, `clear all`, `set more off`, `version 19` and the `_meta` locals. It writes every probe key listed there, and its python block writes `test/fixtures/line_width_truth.json` under `repo` with `json.dump(…, indent=1, sort_keys=True)`. The python block reads locals through `Macro.getLocal`, imports `scripts/svg_truth.py` from the repo by path, never calls Stata, never uses `shell=True`, and writes a backtick as `\x60`.

    Run it: `mkdir -p <scratch>/s13/truth && DASH_REPO=$WT $WT/scripts/stata_slot.sh <scratch>/s13/truth $WT/scripts/extract_line_width_truth.do`. Then check every value against E4. A value that differs is a finding: stop and report, and do not edit the fixture by hand (R7). Run `git -C $WT add -f test/fixtures/line_width_truth.json` now, so later diffs show it.
  ]]></action>
  <verify><![CDATA[`grep -cE "^r\([0-9]+\);$" <scratch>/s13/truth/extract_line_width_truth.log` prints 0 (every probe is captured, so an uncaught error is a defect of the extractor); `python3 -c "import json;d=json.load(open('test/fixtures/line_width_truth.json'));print(all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')), d['ladder']['thick']['setting'], d['forms']['vvvthin']['stroke_pt'], d['refusals']['line_lwidth_starneg1']['rc'], round(d['schemes']['economist']['abc']['stroke_pt'],3), d['floor_pt'])"` prints `True 0.8 0.3 198 1.901 0.3`.]]></verify>
  <done>Stata's measured ladder, forms, refusals, scheme cases and sites were written to a committed-to-be fixture with its provenance stamp, matching Evidence E4 value for value.</done>
</task>

<task type="auto" id="13-03">
  <name>Add fixture tests, guards and contract tests</name>
  <files>test/test_line_width_units.py</files>
  <action><![CDATA[
    Append to `test/test_line_width_units.py`:
    - the fixture-driven `TestTheLadderIsStatas::test_ratios_to_medium_are_statas`, which compares `_T["ladder"]` settings' ratios with dash's px ratios, except `none` and the floored rungs;
    - `TestTheDefaultLine::test_each_shipped_scheme_draws_statas_default`;
    - `TestNamesAreCaseSensitive::test_a_capitalised_scheme_keyword_is_noted`;
    - `TestTheLineWidthRulesAreUnitAware`, which imports `_parse_rules`, `_BLOCK` and `_program_body` from `test_option_validation` and `test_abbreviations` as `test_option_validation.py` does;
    - every Guard class of "TDD test stubs".

    `_T` loads `test/fixtures/line_width_truth.json`, which also names the fixture for `test_fixtures_are_committed.py`. Run the file as in 13-01 into `<scratch>/s13/13-03.log`. Append to `<scratch>/13-P1.12b-failure.txt` the newly failing nodes under the heading `Fixture-driven and contract tests, red at base`, and the passing guard nodes under `Guard tests, green at base`.
  ]]></action>
  <verify><![CDATA[In `<scratch>/s13/13-03.log`, every `Test…Guard`-listed class (TestEmptyOptionsChangeNothing, TestAnUnknownNameKeepsTheSchemeDefault, TestAfterAFilterMove, TestHostileWidths, TestNothingSerialisesAWidthAsText) shows no FAILED line; `grep -c "FAILED.*TestTheLineWidthRulesAreUnitAware" <scratch>/s13/13-03.log` prints 2; `grep -c "Guard tests, green at base" <scratch>/13-P1.12b-failure.txt` prints 1.]]></verify>
  <done>The fixture-driven and dash.ado contract tests were shown red on the unmodified tree, the guards green, and both lists were saved.</done>
</task>

<task type="auto" id="13-04">
  <name>Write the LN refusal cases red-first</name>
  <files>test/test_option_validation.cscript</files>
  <action><![CDATA[
    `grep -cE '(^|[^A-Za-z0-9_])LN-[0-9]' test/*.cscript test/*.py test/*.do` must print 0 for every file before you start (A143).

    In `test/test_option_validation.cscript`, after `_ov_case OV-168 …` (:862) and before the `CV-nn` banner, add one contiguous block (R1) of LN-01 to LN-14, exactly as "Stata truth / Area cases". Its header comment names WP-30 P1.12b, twoway's words and E4's date. Each refused case is written as OV-09 is (:554): `_ov_case`, the id, the command in compound quotes ending `name(lnNN)`, then `198 <opt>` with the option it refuses (`lwidth`, `mlwidth`, `clwidth` or `alwidth`). It is followed by `_ov_said LN-nn "gm_linewidth must be between 0.000 and"` and `_ov_said LN-nn "<opt>() must be a line width"`. Each accepted case is written the same way, with `0 ""`. Also extend the header lines of OV-09, OV-12 and OV-150 (:37, :40, :239) with "and twoway's gm_linewidth line" (comment only). A case with several values (LN-09, LN-10, LN-11, LN-14) is one `_ov_case` per value under the same id, with names `lnNNa`, `lnNNb` and so on. Add the 14 ids to the header's case list (:9-:240 block) in its form.

    Run it on the unmodified dash.ado through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_option_validation.cscript > <scratch>/s13/run_test_option_validation.do`, then `$WT/scripts/stata_slot.sh <scratch>/s13 <scratch>/s13/run_test_option_validation.do`. Append the failing LN ids, and the OV cases that still pass, to `<scratch>/13-P1.12b-failure.txt` under `Area cscript, red at base`.
  ]]></action>
  <verify><![CDATA[`grep -E "LN-(01|02|03|04|05|06|07|12|13) FAIL" <scratch>/s13/run_test_option_validation.log | wc -l` is at least 9 (rc 0 where 198 is wanted, or the gm_linewidth words missing); `grep -E "LN-(08|09|10|11|14) PASS" <scratch>/s13/run_test_option_validation.log | wc -l` is at least 5; no `OV-` case changed state.]]></verify>
  <done>Every new refusal case was shown failing against the unmodified dash.ado and every acceptance case passing, with the ids saved.</done>
</task>

<task type="auto" id="13-05">
  <name>Put the ladder on OptionTranslator</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-13.1 to TR-13.4.

    Replace the `_LWIDTH_MAP` banner and dict (find `    _LWIDTH_MAP: dict[str, float] = {`) with `_LWIDTH_RS`, `_LWIDTH_MAX_RS` and `_LWIDTH_FLOOR_PT`, each commented as TR-13.1 says. Append `"line"` to `_SIZE_KINDS`.

    In `resolve_size`, add the line ladder and the per-kind maximum (TR-13.2) and nothing else.

    Add `@staticmethod line_px(pt)` (TR-13.3) directly after `resolve_size`. Rewrite `translate_lwidth` (TR-13.4) with its new docstring.

    Then fix the stale comments that name the old map: `grep -n "_LWIDTH_MAP" dash_render.py` must print nothing.

    Run `python3 -m pytest test/test_size_units.py -q -p no:cacheprovider` (S08's file: it must stay green, so the marker, text and gap kinds are unchanged) and `python3 -m pytest test/test_line_width_units.py -q -n0 -p no:cacheprovider -k "UnitFunctions or LadderIsStatas or a_number_is_relative or points_inches or Hostile"`.
  ]]></action>
  <verify><![CDATA[Both runs report 0 failed; `python3 -c "import dash_render as d;T=d.OptionTranslator;print([round(T.translate_lwidth(k),4) for k in ('none','vvvthin','thin','medium','thick','vvvthick','1pt','.3')])"` prints `[0.0, 0.4, 0.768, 1.152, 3.072, 16.128, 1.3333, 1.152]`.]]></verify>
  <done>OptionTranslator carried Stata's linewidth ladder, the line kind of the shared resolver and the one pixel rule with the 0.3 pt floor, and translate_lwidth became its wrapper.</done>
</task>

<task type="auto" id="13-06">
  <name>Read scheme widths by the same rule</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-13.5 in `SchemeParser`:
    - delete `_LWIDTH_PX_PER_UNIT` and its comment;
    - in `_lwidth`, drop `.lower()`, return `OptionTranslator.line_px(val * OptionTranslator.PT_PER_RS)` for a finite non-negative number, add the once-per-key `dash scheme:` note for an unknown keyword, and make the signature default `None`, read as medium;
    - rewrite `_lwidth`'s docstring to E4's rule.

    Leave `_init_properties` (S15's in batch 5, D-13g), `_bounded_lwidth`, `_plot_lwidth_of`, `plot_line_width`, `_LWIDTH_MAX_PX` and `_FALLBACK_PROPS` as they are.

    Run `python3 -m pytest test/test_line_width_units.py -q -n0 -p no:cacheprovider -k "DefaultLine or scheme_number or scheme_keyword or Hairline"`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c "_LWIDTH_PX_PER_UNIT" dash_render.py` prints 0; `python3 -c "import dash_render as d;print(round(d.SchemeParser.fallback().default_line_width,3))"` prints `1.152`.]]></verify>
  <done>Every scheme linewidth key, keyword or number, was drawn by the same Stata-unit rule as an option, case-sensitively and with twoway's note for an unknown keyword.</done>
</task>

<task type="auto" id="13-07">
  <name>Route the appliers through the ladder</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-13.6:
    - `_apply_line_opts`'s width at `glyph.line_width = self.tr.translate_lwidth(options["lwidth"])`;
    - `_apply_marker_opts`' `mlwidth()` site;
    - `_ci_band_style`'s `lwidth`/`alwidth` loop, deleting the `none` special case and the 1000 px cap.

    Each passes the site's current width as `default_px`, `default_px=None` when that width is not a plain number (`isinstance(…, (int, float))`), and `getattr(self.scheme, "size_ref_in", 4.0)` as `ref_in`. Each catches `(ValueError, TypeError)` and keeps its note. Keep S08's sync of the nonselection and muted copies where S08 put it, byte for byte, and write each width inside the applier, before the sync runs, so the brushed and muted copies carry the new width (A37). Do not edit any mapper, `_apply_mlabel_opts` or `_apply_fill_opts` (R12).

    Run `python3 -m pytest test/test_line_width_units.py -q -n0 -p no:cacheprovider -k "BandOutline or EmptyOptions or CaseSensitive or Hairline or AnUnknownName"`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `python3 -c "import dash_render as d"` raises nothing.]]></verify>
  <done>lwidth(), clwidth(), mlwidth() and the band outline read Stata units, multiply the site's own default and draw none as nothing, in both modes.</done>
</task>

<task type="auto" id="13-08">
  <name>Route the region and reference-line widths</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-13.7.
    - `_extract_region_lwidth(val, default_px=None, ref_in=4.0)` uses `thin` when `default_px` is None (D-13d), with the docstring naming S38 as the section that passes the scheme's width.
    - `_dash_refline_draw` has the no-scheme default `OptionTranslator.translate_lwidth("medium")`, and its `lwidth` sub-option is read with `kw["line_width"]` and `OptionTranslator.size_ref_of(fig)`, in its own `try` with the existing note.

    Do not edit the two `_extract_region_lwidth` call sites (`_make_figure_body`, `_generate_app_source`; R12), or the copy lists.

    Run `python3 -m pytest test/test_line_width_units.py -q -n0 -p no:cacheprovider -k "not UnitAware"` and `python3 -m pytest test/test_axis_options.py -q -p no:cacheprovider -k "Reference or refline"`.
  ]]></action>
  <verify><![CDATA[Both runs report 0 failed (the dash.ado contract class waits for 13-09); `python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>plotregion(lwidth()) and xline()/yline()'s lwidth() were read on the same ladder in both modes, with the region's default and reference left for S38 to pass.</done>
</task>

<task type="auto" id="13-09">
  <name>Make dash.ado's width bounds unit-aware</name>
  <files>dash.ado, test/test_option_validation.py</files>
  <action><![CDATA[
    Make TR-13.8 in `_dash_option_rules`: the four `,u` rules and the comment sentence. In `_dash_validate_value`'s style branch, add the `p3 == "u"` reading (a) to (d), with twoway's line then dash's line and `exit 198`. Write it with `regexm` on the scalar `T` and `real()` through the scalar `R`, as the existing branch does, with no macro expansion of the value. Keep the comment block style of the surrounding code, citing E4's measurements and M5.

    In `test/test_option_validation.py`, flip `CONTRACT_PLOT_RULES` (:71) and `test_the_parameters_fit_the_kind` (:249) as E9 says, each with a comment `# WP-30 P1.12b: the line-width rules read Stata units (,u)`, and append both `Flipped:` lines to `<scratch>/s13/13-flips.txt`.

    Run `python3 -m pytest test/test_option_validation.py test/test_line_width_units.py test/test_twoway_option_parity.py -q -p no:cacheprovider -k "Table or UnitAware or clwidth"`, then the OV cscript through the driver of 13-04.
  ]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; in `<scratch>/s13/run_test_option_validation.log`, `grep -c " FAIL" ` prints 0 and `grep -cE "LN-(0[1-9]|1[0-4]) PASS"` prints at least 14 and the script ends `test_option_validation: ALL CHECKS PASSED`.]]></verify>
  <done>dash.ado refused every line-width form twoway refuses with r(198), twoway's words and the option named, and left every other style rule as it was.</done>
</task>

<task type="auto" id="13-10">
  <name>Register line_px and add parity cases</name>
  <files>test/function_test_map.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Under the anchor `# WP-30 S13 (P1.12b): Stata line-width ladder (P1.12 part b, M1)` of `FUNCTIONS`, add `'OptionTranslator.line_px': 'test/test_line_width_units.py::TestTheUnitFunctions::test_line_px_floors_and_converts',` (TR-13.10). Leave every other key as it is.

    Append the two `CORPUS` cases and the one `MOVE_CORPUS` case of "Guards appended", under the comment `# WP-30 P1.12b: Stata line widths`, at the end of each list (R8). `ALLOWED` and `_MUST_WARN` are not edited.

    Run `python3 -m pytest test/test_function_test_map.py test/test_mode_parity.py -q -p no:cacheprovider -k "line widths or vvvthin or lwidth or every"`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `python3 -m pytest test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The one new function named its unit test, and saved and served parity covered line widths before and after a move.</done>
</task>

<task type="auto" id="13-11">
  <name>Flip the scheme-side width pins</name>
  <files>test/test_ci_band_style.py, test/test_scheme_linewidth.py, test/test_scheme_rendered_output.py</files>
  <action><![CDATA[
    Make E9's rows for these three files, in place, keeping every node's name and parametrisation: `_UNIT_PX` and the two `TestTheSchemeKeys` literals; `_px`, `TestVvvthick` (literals, the upper-case case and the docstring) and `TestBothModesDrawVvvthick`; and `PX_PER_LINEWIDTH_UNIT`, `_line_width_px`'s docstring, `TestAC162…`, `test_a_numeric_linewidth_is_5px_per_stata_unit` and `test_medium_keyword_still_anchors_at_1_5`. Each edited docstring states the old and new rule (Flips paragraph). Append one `Flipped:` line per test function to `<scratch>/s13/13-flips.txt`, a parametrised one once, with its parameter count.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ci_band_style.py test/test_scheme_linewidth.py test/test_scheme_rendered_output.py -q -p no:cacheprovider` reports 0 failed; `grep -c "_LWIDTH_PX_PER_UNIT\|== 6.6\|approx(6.0)" test/test_scheme_linewidth.py test/test_scheme_rendered_output.py` prints 0 for each file.]]></verify>
  <done>The ci-band, scheme-chain and rendered-scheme tests asserted Stata's units on Stata's ladder, with their flips recorded.</done>
</task>

<task type="auto" id="13-12">
  <name>Flip the scheme-parser and translator pins</name>
  <files>test/test_scheme_review_fixes.py, test/test_scheme_coercion.py, test/test_options.py</files>
  <action><![CDATA[
    Make E9's rows for these three files, in place: `TestAxisLineWidth::test_a_numeric_axisline_is_a_stata_linewidth_unit` (3.0 → 2.304), the `linewidth minor_grid` and `linewidth axisline` rows of `TestHostileSchemeValues::test_every_negative_linewidth_is_refused` (0.8 → 0.768; leave its `linewidth p` row and the two grid assertions, which are S15's, D-13g), `TestLineWidth::test_a_numeric_value_is_a_stata_linewidth_unit` (17.5 → 13.44, 1.5 → 1.152, and its docstring) and `TestTranslateLwidth::test_numeric_string_passthrough` (2.5 → 9.6, and a docstring). Also re-run `test_scheme_review_fixes.py` and `test_scheme_coercion.py` for a warning count that TR-13.5's note changed, and flip it with its reason. Append the `Flipped:` lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_review_fixes.py test/test_scheme_coercion.py test/test_options.py -q -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The scheme parser's and the translator's tests asserted the one Stata-unit rule, with their flips recorded.</done>
</task>

<task type="auto" id="13-13">
  <name>Flip the served, glyph and page pins</name>
  <files>test/test_server.py, test/test_glyphs.py, test/test_html_output.py</files>
  <action><![CDATA[
    Make E9's rows for these three files, in place. In `test/test_server.py`, add `_THICK_PX = 3.072` to `TestServerLineWidthAllTypes` with its comment, and use it in both helper defaults (:1592, :1602), the 18 tests' assertions and their docstrings. In `test/test_glyphs.py`, change the spike's 3.0 to 11.52 and the four pc arrow tests' 2.5 to 3.072. In `test/test_html_output.py`, change the four `TestLineWidthPatternHtml` tests' lists, and the comment at :2107. Append the `Flipped:` lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_server.py test/test_glyphs.py test/test_html_output.py -q -p no:cacheprovider -k "Lwidth or lwidth or LineWidth"` reports 0 failed.]]></verify>
  <done>The served-app, glyph and saved-page tests asserted Stata's thick and vthick widths, with their flips recorded.</done>
</task>

<task type="auto" id="13-14">
  <name>Flip the last pins and measure the list</name>
  <files>test/test_phase4_plots.py, test/test_polyline_ordering.py, test/test_help_claims_7.py</files>
  <action><![CDATA[
    Make E9's rows for these three files, in place: the pcspike 2.5, the degraded-layer 2.5 (assert :314 and docstring :291-295), and `_REGION`'s `lwidth(2)` row (:197, 2.0 → 7.68). Append the `Flipped:` lines.

    Then re-run E9's whole list of 54 files (plus `test_line_width_units.py`, `test_size_units.py` and, if S08 placed them elsewhere, the file of S08's brushed-copy tests), `-n 6`, into `<scratch>/s13/13-14.log`, with every file path written out in the command (Notes, the guard hook), never through a variable. It must report 0 failed except `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` (13-16). A red node not in E9 is a pin the prototype could not see: flip it in this task only if it is in one of the three files above. Otherwise stop and report the node to the orchestrator, because a fourth file needs a task of its own (D7).
  ]]></action>
  <verify><![CDATA[`grep -E "^FAILED" <scratch>/s13/13-14.log` lists only the single-y digest node; `grep -c "^Flipped:" <scratch>/s13/13-flips.txt` is at least 51 (E9's functions, less the two hostile-default functions D-13g leaves to S15, plus 13-09's two).]]></verify>
  <done>Every pin E9 lists was flipped with its reason, and a re-run of the measured list showed nothing else red but the page digest.</done>
</task>

<task type="auto" id="13-15">
  <name>Certify against twoway in Stata</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Inside S01's stub `* ==== S13 P1.12b: Stata line-width ladder ====` (between its start and end display lines), write LN-20 to LN-27 as "Stata truth / Truth block" specifies, with `_s13_*` python helpers directly above the header (no brace inside the gated block). Every case prints `LN-nn PASS` or `LN-nn FAIL` and the measured pair, and uses the scheme it names only through `scheme()`, so the session scheme is never changed.

    Run it through the driver with `WP30_ONLY=S13`: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > <scratch>/s13/run_test_wp30_truth.do`, then `WP30_ONLY=S13 $WT/scripts/stata_slot.sh <scratch>/s13 <scratch>/s13/run_test_wp30_truth.do`. Then run, each through the driver, `test_option_validation.cscript`, `test_help_claims_2.cscript`, `test_ci_band_options.cscript`, `test_twoway_option_parity.cscript` and `test_help_claims_8.cscript`. If one of them reports a FAIL, stop and report it with the case id: E9 expects none, and a flip there is an area-script edit for the orchestrator to allot.

    Afterwards, check that `~/.stata19/console/stata19.rc` still holds `python_exec` (project memory): an exit 222 is a SKIP, not a pass.
  ]]></action>
  <verify><![CDATA[`grep -cE "LN-2[0-7] PASS" <scratch>/s13/run_test_wp30_truth.log` prints 8 and `grep -c " FAIL\|SKIP" <scratch>/s13/run_test_wp30_truth.log` prints 0; each of the five area logs ends with its `ALL CHECKS PASSED` (or the script's own pass line) and has no ` FAIL`.]]></verify>
  <done>Stata certified that dash's saved page and served app draw twoway's line-width ratios at every site, before and after a move, and that every area script still passed.</done>
</task>

<task type="auto" id="13-16">
  <name>Document the ladder and re-derive the digest</name>
  <files>dash.sthlp, test/test_varlist_expansion.py</files>
  <action><![CDATA[
    In dash.sthlp, edit only these paragraphs (R3; see Notes):
    1. **Line options paragraph** (Marker and Transparency Options, :3275-3281). Keep its sentences word for word (`test_help_claims_7.py:1088` reads "An unknown {cmd:lcolor()} or {cmd:lwidth()} name is still reported"). After it, add one `{pstd}` paragraph headed `{ul:Line widths.}` stating:
       - BR-13.1 to BR-13.5 and BR-13.7 in plain words: the ladder with its 12 names in order; 1 unit = 2.88 point at the four-inch reference; `#pt`, `#in`, `#cm` and `#rs`; `*#`;
       - the 0.3-point floor; `none`; case;
       - the sites;
       - that `*#` and an absolute size whose value passes 10000 units only once drawn is noted and drawn at the default, where twoway refuses it.
    2. **The bounds sentence** (:690-693). `{cmd:lwidth()} and {cmd:mlwidth()} 0 to 10000` becomes `{cmd:lwidth()}, {cmd:mlwidth()} and {cmd:clwidth()} 0 to 10000 Stata units`, as a number, `#rs`, a non-negative `#pt`, `#in`, `#cm` or `*#`, refused with twoway's message {cmd:gm_linewidth must be between 0.000 and 1.0e+04}, followed by dash's line naming the option. `alwidth()` gets the same, with its existing type clause.
    3. **The every-type sentence** (:744-752). In `{cmd:dash} checks them on every plot type` (:750-751), insert `, their unit and multiplier forms included,` after `checks them`. Keep `{cmd:scatter mpg weight, lwidth(-1)}, which {cmd:twoway} draws, is refused` word for word (`test_help_claims_2.py:275`).

    Do not touch the Units paragraph (:3424-3434, S15's title; its sentence stays true) or :2701 (S38).

    Then run `python3 -m pytest test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline -q -n0 -p no:cacheprovider`. Read the new digest from its message, and write it into `_SINGLE_Y_BASELINE_SHA256` (:343) with the R10 comment of E9. Run `python3 -m pytest test/test_help_conformance.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_7.py test/test_help_claims_8.py test/test_varlist_expansion.py -q -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c "gm_linewidth must be between" dash.sthlp` prints at least 1; `grep -c "vvvthin" dash.sthlp` prints at least 1; `grep -Eic "claude|anthropic" dash.sthlp` prints 0.]]></verify>
  <done>The help described line widths in Stata's units, the floor, the case rule, the refusals in twoway's words and the one documented residual, and the single-y page digest named why it moved.</done>
</task>

<task type="auto" id="13-17">
  <name>Close P1.12b and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    1. Find the title as `WP30_OPEN["P1.12b"]`. In BUGS.md, close that entry in place (`- [x]`) and replace its Resolution with:

    `  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.12b). Line widths are read in Stata's units on Stata's own linewidth ladder (none, vvvthin to vvvthick), one unit 3.84 px at the four-inch reference: OptionTranslator._LWIDTH_MAP was replaced by _LWIDTH_RS, resolve_size gained the line kind, OptionTranslator.line_px applies the 0.3 pt floor, translate_lwidth reads numbers, #pt, #in, #cm, #rs and *# case-sensitively, and SchemeParser._lwidth reads scheme numbers and keywords by the same rule; lwidth(), clwidth(), mlwidth(), alwidth(), plotregion(lwidth()) and xline()/yline()'s lwidth() multiply their own default, in the saved page and the served app, before and after a filter move. dash.ado refuses a negative number, multiplier or unit form and an rs value above 10000 with r(198) and twoway's gm_linewidth message. Pinned by test/test_line_width_units.py::TestTheLadderIsStatas::test_each_keyword_is_its_stata_units, test/test_line_width_units.py::TestTheMultiplier::test_star_multiplies_the_site_default, test/test_line_width_units.py::TestVvvthinAndNone::test_none_draws_nothing, test/test_line_width_units.py::TestTheDefaultLine::test_each_shipped_scheme_draws_statas_default, test/test_option_validation.cscript LN-01, test/test_wp30_truth.cscript LN-20; fixture test/fixtures/line_width_truth.json. Residual, deferred (WP-30): a positive *# or absolute width whose value passes 10000 units only at draw time (lwidth(*40000), economist lwidth(20000pt)) is noted and drawn at the default where twoway refuses it; plotregion(lwidth(*#)) multiplies thin and reads absolute units at the four-inch reference until section 38 passes the scheme's width; dash refuses a negative width on every plot type, also where twoway does not evaluate it (P2.21).`

    2. Delete the `"P1.12b"` key line from `WP30_OPEN`.

    3. In CHANGELOG.md, replace `<!-- WP-30 P1.12b -->` under `### Results that change` in place with:

    `- Line widths are drawn in Stata's units on Stata's own ladder, one unit 2.88 point (3.84 pixels) as for every other size. Under s2color the default line, marker outline, grid and reference line go from 1.5 to 1.15 pixels, axis lines, the plot-region border and bar outlines from 0.8 to 0.77, and economist's lines from 6.0 to 4.61. lwidth(thin) was 0.8 and is 0.77, lwidth(thick) 2.5 and now 3.07, lwidth(vvthick) 5.0 and now 9.98, lwidth(vvvthick) 6.6 and now 16.13. A number is Stata units, so lwidth(.3) was 0.3 pixels and is 1.15, and lwidth(2) was 2 and is 7.68. lwidth(vvvthin), lwidth(none), lwidth(1pt), lwidth(*2) and the in, cm and rs units are drawn where they were noted and ignored, a width under 0.3 point is drawn at 0.3 point, and a name is matched in its case, so lwidth(THICK) is noted and drawn at the scheme's width, as twoway draws it. This holds for lwidth(), mlwidth(), clwidth(), alwidth(), plotregion(lwidth()), xline() and yline(), and for a scheme's linewidth keys, in the saved dashboard and the served app. (WP-30, P1.12b)`

    Replace the marker under `### Changed behaviour (may need your do-files changed)` in place with:

    `- A line width twoway refuses is refused with twoway's message, gm_linewidth must be between 0.000 and  1.0e+04, r(198), and a second line naming the option. lwidth(*-1), lwidth(-1pt), mlwidth(-0.5in), clwidth(*-1), alwidth(-1pt) and lwidth(1e5rs) were drawn at the scheme's width with a note. lwidth(-1) and lwidth(10001), refused before in dash's own words, now print twoway's message first. As before, dash refuses a negative width on every plot type, where twoway refuses it only where it draws the line or outline. lwidth(*40000) and economist's lwidth(20000pt), which twoway refuses once it knows the default width and the graph's size, are noted and drawn at the default. (WP-30, P1.12b)`

    4. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`, then `git -C $WT merge --no-edit main` (expect `Already up to date.`), then one full run: `<scratch>/full_suite_queue.sh $WT <scratch>/13-full-1.log`, launched in the background and waited for on its `exit=` line (E1, E6).

    5. Stage only these files:
    - `dash_render.py dash.ado dash.sthlp BUGS.md CHANGELOG.md scripts/extract_line_width_truth.do`;
    - `test/test_line_width_units.py test/test_option_validation.py test/test_option_validation.cscript test/test_wp30_truth.cscript test/function_test_map.py test/test_mode_parity.py test/test_tracking_documents.py test/test_varlist_expansion.py`;
    - the twelve flipped files of 13-11 to 13-14;
    - `git add -f test/fixtures/line_width_truth.json`.

    Check `git diff --cached --name-only` against that list (G6; never CLAUDE.md, .gitignore, AGENTS.md or `.ultraplan/`). Write the message to `<scratch>/s13/msg.txt` in the Commit boundary's form, run G7 (`grep -Eic 'claude|anthropic'` prints 0) before and after `git commit -F <scratch>/s13/msg.txt`, and report the sha and message to the orchestrator.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/13-full-1.log` prints `exit=0` and the pytest summary line above it names no `failed` or `error`; `git log -1 --format=%s` ends `(WP-30 P1.12b)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.12b -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.12b": "' test/test_tracking_documents.py` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.12b was closed in BUGS.md naming tests that exist, its key was removed from WP30_OPEN, both CHANGELOG markers became the measured lines, and one green commit on wp30-s13 was ready for the merger.</done>
</task>

## Section completion criteria

- Every line width of every site in E2 is drawn in Stata's units on Stata's ladder, in the saved page and the served app, before and after a filter move. `vvvthin` and sub-0.3 pt widths are at 0.3 pt, `none` draws nothing, and names are case-sensitive.
- Every scheme `linewidth` key reads by the same rule. The s2color default line is 1.152 px and economist's 4.608 px.
- dash.ado refuses the forms of BR-13.6 with r(198), twoway's words and the option named, and S08's kinds are unaffected (LN-14).
- `test_wp30_truth.cscript` prints LN-20..LN-27 PASS under `WP30_ONLY=S13`, and `test_option_validation.cscript` prints LN-01..LN-14 PASS with every OV case.
- `test/fixtures/line_width_truth.json` exists with its `_meta` stamp and is committed with `git add -f`.
- One green commit `(WP-30 P1.12b)` on `wp30-s13`, with its failure text, `Regression:`, `Flipped:`, `Fixture:` and `BUGS.md:` lines, and no AI reference.
- The BUGS.md entry is closed in place, the `WP30_OPEN["P1.12b"]` line is deleted, and both markers are replaced. No other entry, key, marker, copy list, runner, hygiene pin, scheme file or generated fixture is touched.

## Notes

- **S08 first.** S13 extends S08's `resolve_size`. If 13-01's contract check fails, S08 has not landed or landed other names: stop and report, never re-create S08's methods here. Use S08's `stata_number`, `size_multiplier` and `size_ref_of` as landed. A difference from E7 goes in the commit body, one line.
- **The line maximum is per kind.** S08 bounds every kind at 1,000 units. Lines are bounded at 10,000 (twoway's `gm_linewidth`), so `resolve_size` must branch on `kind` for the maximum (TR-13.2), and `TestTheRendererBound` pins it. Do not raise `_SIZE_MAX_RS` itself, which would change S08's kinds.
- **Floats.** `line_px` returns values like 0.7679999999999999. Tests compare with `pytest.approx`, and E9's flips write the rounded value inside `approx`, never `==`. Bokeh accepts any finite non-negative float, and a width of 0 is not drawn: BokehJS's line visuals return `doit` false for `line_width == 0` (measured in bokeh 3.9.0's `bokeh.min.js`, `return!(null==e||0==t||0==i)`).
- **The guard hook counts pytest launches.** A `pytest` command whose text names no `test/test_<x>.py` and no `::` counts as a full launch, even when its files come from a variable. The third such launch in a session is refused (`.claude/hooks/guard-full-suite.sh`). Write the files out in every pytest command of 13-14, never `$FILES`. The one full run is 13-17's, through the queue.
- **dash.ado regex.** The programs run under S03's `version 19`, so `regexm` is the classic engine:
  - escape the star as `\*`;
  - the number pattern has two inner groups, so in `^(NUM) *(pt|in|cm|rs)$` the unit is `regexs(4)`; count the parentheses again after writing it;
  - `real("1d3")` is 1000 and `real("1e400")` is missing;
  - twoway's message holds two blanks before `1.0e+04`. Print it as measured, and keep the tests' needle to `gm_linewidth must be between 0.000 and`.
- **Not to be confused.** `msize`, `mlabsize` and `mlabgap` (S08) have no `u`. A `-1pt` there passes as S08 designed (twoway draws nothing, silently). LN-14 pins that the branch does not leak.
- **python_exec hazard** (project memory). Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The truth script then exits 222, and a SKIP is not a pass. Check the file after 13-02, 13-04 and 13-15.
- **Python inside the gated block holds no brace.** Stata scans a skipped block's braces, so `_s13_*` helpers sit above the S13 header (index delta "Truth script").
- **Shared files (R1-R13).**
  - **R1.** Only the S13 block of `test_wp30_truth.cscript`, with helpers above its header. One contiguous LN run after OV-168 in `test_option_validation.cscript`. No runner block or hygiene pin.
  - **R2.** No copy-list change: `line_px` and `_LWIDTH_RS` travel with `OptionTranslator`, and `_extract_region_lwidth` and `_dash_refline_draw` change in place. One map key goes under S13's anchor.
  - **R3.** The help paragraphs S13 edits are the line-options paragraph of Marker and Transparency Options (S13's row, batch 5) and two sentences of Differences from twoway (:690-693 bounds, :744-752 every-type rule). The latter title is not in R3's table for S13, but S13's scope (dash.ado's bounds) names them. No batch-5 partner edits 444-814, so the merger needs no rule. The orchestrator may add S13 to that row.
  - **R4.** Two markers, Results that change and Changed behaviour, replaced in place.
  - **R5.** The one entry and its key line.
  - **R6.** dash.ado's `_dash_option_rules` (four tokens) and `_dash_validate_value`'s style branch only. S03's `version 19` stays. No option key is added.
  - **R7.** A new extractor in S02's form. The fixture is generated, never patched, and added with `git add -f`. `scheme_truth.json` and the scheme files are not touched.
  - **R8.** `CORPUS`/`MOVE_CORPUS` appended only.
  - **R9.** Flips in place.
  - **R10.** The single-y digest. S15 moves it too, and the merger re-derives it after S15 lands.
  - **R12.** S13 is batch 5's only editor of `_apply_line_opts` and `_apply_marker_opts`. It edits no other one-editor symbol, and not `_init_properties` (S15's, D-13g).
  - **R13.** `gitnexus` runs in the main checkout only.
- **For S15 (same batch, lands after S13).** S15 replaces `_init_properties`' two pixel literals with `translate_lwidth("medium")` and `translate_lwidth("thin")` and flips the `linewidth p` row and the two grid assertions of `TestHostileSchemeValues` (D-13g; TR-15.3). S15 reads `linewidth tick` and any other new width key through `SchemeParser._lwidth` or `translate_lwidth`, so its tick widths land on Stata's ladder with no further edit (index batch 5). Its regeneration should also rewrite the stale `linewidth` `dash_rule` sentence of `scripts/extract_scheme_truth.py:2138-2144` to "a linewidth keyword or number is Stata units, px = max(units x 2.88, 0.3) x 4/3 (WP-30 P1.12b)". S13 leaves that generated text alone (R7). S15's chrome may compare widths: compare against `translate_lwidth("<keyword>")`, never against a pixel literal.
- **For S31, S32, S38, S39 (the blocked sections).**
  - The API is `OptionTranslator.translate_lwidth(value, default_px=None, ref_in=4.0) -> float px`, which raises ValueError for an unknown name, a negative value or one past 10,000 units. Notes go through `_dash_style_note(option, value, "line width")`.
  - **S38** passes `default_px=fig.outline_line_width` (the scheme's, set by `apply_to_figure`) and `ref_in=OptionTranslator.size_ref_of(fig)` at both `_extract_region_lwidth` call sites, or replaces the reader with its own. It also adds the region refusals twoway makes (E4: `plotregion(lwidth(-1))`, `lwidth(*-1)` r(198)).
  - **S39** adds the `xline` width refusals (E4) and keeps `_dash_refline_draw`'s `lwidth` branch.
  - **S31** reads the axis line width the same way, against `apply_to_axis`'s width.
  - **S32**'s named styles carry Stata units, never pixels.
- **Commit body line forms** are BRIEF's, with WP-30 ids. `failed at` is `batch-5-base.txt`'s sha.
- **Maintainer question (D-13b; an M5 exception, so it needs the maintainer).**
  - dash.ado cannot refuse a positive `*#` or an absolute unit whose value passes 10,000 Stata units only once the scheme's default width or the graph's size is known. Examples are `lwidth(*40000)` under s2color and `lwidth(20000pt)` under economist, both r(198) in twoway.
  - This plan notes them and draws the site's default.
  - The alternative is a refusal from the renderer. Today a renderer exception reaches Stata only as a Python error (dash_render.py's `DashLimitError`/`DashSpecError` carry no return code to dash.ado), so a twoway-equal r(198) would need a new channel.
  - **Recommendation: ratify D-13b** (note and draw the default). The forms are absurd widths (over 10,000 Stata units, 38,400 px at the 4-inch reference), the note names them, and the channel is a cross-cutting change outside P1.12b. If struck, S13 stops before 13-05 for a re-plan.
- **Notes for the closeout (S58).**
  - **GAPS2 D2** (GAPS2.md:849-866). Sub-claims a, b and e for line widths, and c whole, are closed by P1.12b; a, b, d and e for markers and text, and B9, by P1.12a. When both entries are closed, the Tracked line becomes `- **Tracked:** Closed in WP-30, BUGS.md "Marker, text and gap sizes are read as pixels on a private ladder, and #pt, *# and vhuge are refused, where twoway reads Stata's relative size units", commit <P1.12a sha>; BUGS.md "Line widths use a private ladder without vvvthin or none and read numbers as pixels, and negative widths twoway refuses are accepted", commit <P1.12b sha>`. `(WP-30, GAPS2-D2)` is appended to both Resolutions, and GAPS2-D2 is recorded closed.
  - **ROADMAP.md:2048-2050** ("The linewidth keyword ladder `_LWIDTH_MAP` keeps ratios that are not Stata's … recorded as a follow-up") is closed by P1.12b, commit `<sha>`.
  - **DROPIN-REMAINING.md:102** (P1.12) is closed by P1.12a and P1.12b. **DROPIN P2.12** (:204) loses `lwidth(none)` (register P1.12.7/A38).
  - **New residual rows for ROADMAP:**
    - D-13b, the draw-time 10,000-unit bound;
    - D-13e, `*#` on a sub-0.3 pt default;
    - `tlwidth()` and `glwidth()` on every axis and the colour key, named and not drawn, with no WP-30 owner (D-13f);
    - D-13c, per-type narrowing of the width refusals, which belongs to P2.21.
  - **TWOWAY_COVERAGE_AUDIT.md** rows that list `lwidth`/`mlwidth`/`clwidth`/`alwidth` as implemented (research: rows 112-114, 136, 140) gain "in Stata's units (WP-30 P1.12b)".
  - **AGENTS.md invariant** (E7): "Line widths have one rule: OptionTranslator.translate_lwidth → resolve_size(kind "line") → line_px (Stata units × 3.84 px, 0.3 pt floor); scheme widths go through SchemeParser._lwidth, never a pixel literal."
- **Line numbers** are `c96facd`'s. S01-S12 land before batch 5 and shift dash_render.py and dash.ado by a few dozen lines. The symbols and the quoted excerpts are the text to find.
