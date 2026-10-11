# Section 37: mlabvposition() and mlabtextstyle() (P1.24)

> Part of: WP-30 · Items: P1.24 (entry `P1.24`; REM-§2-S09-mlabvpos, REM-S09-73-mlabpos, REM-05-04-S09-r, GAPS2-A4-p, GAPS2-B27-c, AUDIT-33, REM-05-04-B6) · Risk: yellow · Batch: 13 (merge order S37, S38) · Depends on: 08, 11, 33 · Blocks: none · Tasks: 20, 2 commits (label positions, then label text styles) · Case prefix: MV

## Review amendments

- Fixed (major): Q-37.1 left 37-14 waiting on an approval that no step records. The review resolved it under M1 and register P1.24.3, so the regeneration stands (Notes). 37-14 now runs unless an orchestrator amendment strikes it. The Risk, TR-37.18, AC-37.4 and completion criteria are aligned. The index.md A152, R3 and batch-13 fixes are filed in `review-notes/g06.md`.
- Fixed (minor): 37-12's second truth block is now spelt in section-01's stub form, with its own gate and its own start and end lines as the first and last statements, which `TestTheWp30TruthScript` checks.
- Fixed (minor): E3/TR-37.5 Mata anchors corrected to the HEAD lines (keys :2237-2242, `"mlabel"` :2240).
- Cross-file (filed): index.md R10 lists S37 as a mover of the declared-plot pin (:607). S37 declares no option, so that pin does not move (Notes R10).
- Checked at HEAD: dash.ado :957, :1075-1079, :1219-1220, :3155, :4121 (`_dash_fold_bw` call, before `_dash_fold_mlab` at :1549), :6136-6142; dash_render.py `_DASH_OPT_VAR_KEYS` :25504, `_dash_option_columns` :25531, the copy list :33355-33356, `_MLABEL_CLOCK` :7907, `_apply_mlabel_opts` :9302, call sites :13509/:13953, dispatch :28501; the test pins :240/:121-122 (test_unsupported_report_is_true.py), :598/:604 (test_help_conformance.py), :1014 (test_help_claims_8.py); the cscript anchors :2902/:2904; `CORPUS` closing :1798. The MV prefix and the new files are free.
- Checked the batch boundary against S38: no shared function. S38 edits `_make_figure_body`, the template, S10's Mata region family, `_dash_plot` and the region readers; S37 edits none of them. In the shared test files, S37 extends `_annotations` and S38 the figure profile. Both append cscript runs in merge order.
- Rejected: "add a renderer type gate" (research critic item 9). The measured rscatter quirk is drawn per row by twoway (E9), so dash.ado's count rule is the gate.
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:145 (P1.24) reads: "`mlabvposition(varname)` is not drawn. It and `mlabtextstyle` are declared and pending but never serialised, and no test checks that declared options reach the spec." GAPS2.md:657-666 (B27) gives the plan for the first half: "a per-row clock column mapped to per-row `text_align`/`text_baseline` and offsets in the `LabelSet`"; GAPS2.md:182/:192 (A4) and TWOWAY_COVERAGE_AUDIT.md:113 ("No per-observation `mlabvposition()`, named `mlabtextstyle()`") still list both.

Measured at `c96facd` (research `.ultraplan/wp30/research/p1-24.md` §2; re-measured for this file, `p6.do`, StataNow 19.5):

```
_dash_process_segment "scatter y x, mlabel(lab) mlabvposition(pos) mlabtextstyle(heading)"
SEGJSON {"type":"scatter","yvar":"y","xvar":"x","options":{"mlabel":"lab"},"if_expr":"","in_expr":""}
dash scatter y x, mlabel(lab) mlabvposition(p9)            -> rc 0, "dash: ignoring unsupported option(s): mlabvposition()"
dash rscatter y y2 x, mlabvposition(p9)                    -> rc 0, same note    (twoway: r(103) "rscatter requires 3 variables: y y2 x p9")
dash lfit y x, mlabel(lab) mlabvposition(p9)               -> rc 0, same note    (twoway: r(103) "too many variables specified: y x lab p9")
dash scatter y x, mlabel(lab) mlabvposition(p9) mlabvposition(p9) -> rc 0        (twoway: r(198) "option mlabvposition() not allowed")
dash scatter y x, mlabel(lab) mlabvposition(p9 y)          -> rc 0               (twoway: r(103) "option mlabvposition():  too many names specified")
dash scatter y x, mlabel(lab) mlabvposition(p9*1)          -> rc 0               (twoway: r(198) "* invalid name")
dash scatter y x, mlabel(lab) mlabvposition(nosuch)        -> rc 0               (twoway: r(111) "variable nosuch not found")
dash scatter y x, mlabel(lab) mlabtextstyle(heading) mlabtextstyle(body) -> rc 0, "ignoring unsupported option(s): mlabtextstyle()"
```

On the saved page of `mlabvposition(pos)` the one `LabelSet` has `x_offset 4`, `text_baseline "middle"` and `text_font_size "10px"`, the `pos` column is not in the page, and all 18 labels sit at 3 o'clock. twoway draws each row at its own clock, and `mlabtextstyle(heading)` at the scheme's heading size and colour (157.44 #000000 against the default 89.94 #1A85FF under stcolor).

**After this section**, in the saved page and the served app, before and after every filter move:
- `mlabvposition(varname)` places each observation's label at its own clock position on the nine types twoway labels with it (scatter, connected, bar, dot, dropline, pcscatter, pccapsym, pcarrow, pcbarrow), by twoway's measured value rules (a whole number 0-12; missing or string → `mlabposition()`, else 3; anything else → 12 with one note), `mlabgap()` along each row's own direction, one variable for every y;
- twoway's refusals of it are dash's, in twoway's words and codes (M5): the 21 range and fit types (r(103)), a second copy (r(198)), two names (r(103)), a non-name (r(198)), a missing variable (r(111));
- `mlabtextstyle(textstyle)` draws the labels in any of Stata's 37 shipped text box styles, read from the scheme on S33's marker-label defaults, as a per-y style list (S11), with `mlabsize()`/`mlabcolor()` winning in either order and an unknown name noted and drawn in `body`, as twoway draws it;
- a guard test fails whenever an option declared in either parser reaches neither the spec nor a named allowlist.

**Why one section, two commits.** Both options are P1.24 and share `_apply_mlabel_opts`, the pending block, the help's one Unsupported entry ("Marker-label placement and text style") and its pins. They are independent in code: commit 1 (positions) touches dash.ado's fold, Mata's extractor and the per-row LabelSet fields; commit 2 (text styles) touches S11's key list, SchemeParser's text box table and the scheme files. Commit 2 needs commit 1's guard test and both need S33's defaults (A156).

**Test order and commit rule (rule 7, A156).** Two cycles on `wp30-s37`.
- **Commit 1 (label positions):** 37-01 and 37-02 write the fixture and every commit-1 regression test and run them against the unmodified batch-13 base, saving `$S/37-P1.24-1-failure.txt` (no commit); 37-03 to 37-09 fix, flip and document; 37-10 runs the full suite and makes commit 1, leaving the BUGS.md entry, its `WP30_OPEN` key and both CHANGELOG markers in place.
- **Commit 2 (label text styles):** 37-11 and 37-12 write the commit-2 fixture and tests against the tree commit 1 leaves and save `$S/37-P1.24-2-failure.txt`; 37-13 to 37-19 fix, regenerate, flip and document; 37-20 closes the entry, deletes the key, replaces both markers and makes commit 2.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — two CRITICAL renderer symbols, a parser fold that must speak twoway's words, and a scheme regeneration in a batch that has none

**Why.**
- `GlyphMapper._apply_mlabel_opts` is CRITICAL: `gitnexus impact _apply_mlabel_opts -d upstream -r dash` gives 16 impacted, 10 direct, 10 processes.
- `_dash_option_columns` is CRITICAL: 15 impacted, 4 direct, 13 processes. Every saved column list, the embed plan and the served `extra_cols` read it.
- `ServerAppBuilder._glyph_layer_lines` (the served copy lists) is HIGH: 4 impacted.
- `map_dropline` and `map_pcscatter` are UNKNOWN: they are reached through `_dash_glyph_dispatch`'s dict (dash_render.py:28501), confirmed by grep.
- Every Stata and Mata symbol is UNKNOWN (not indexed): `_dash_parse_plot_opts` (callers dash.ado:4088, :4092, :4101, :4104, :6235), `_dash_plot_opts_to_json` (:4330), `_dash_process_segment` (:5210), `_dash_extract_vars` (dash.ado:6532, :7619).
- Commit 2 regenerates the 26 shipped scheme files, which A152 reserves to listed regenerators; S37 is not listed there. Q-37.1 is resolved in Notes: the regeneration stands (M1, register P1.24.3), and index.md A152 gains S37 as a cross-file fix.

**Risk factors.**
1. Layers of one graph share one source (measured, critic 2: two scatter layers' LabelSets both on `p1006`), so per-row columns named by the variable alone would hand the second layer's fallback and gap to the first.
2. Stacked sources hold derived `x`, `y`, `y0` columns that `_carry_cols` never overwrites (dash_render.py:8124-8126), so a position variable named `x`, `y` or `y0` would be read as coordinates on dropline and pcscatter.
3. A date-formatted position variable reaches the saved renderer as datetimes (comment at dash_render.py:9384-9386); twoway reads the stored number.
4. twoway's refusal is a variable-count rule, not a type list: `rscatter y y2 x, mlabel(y) mlabvposition(p9)` is accepted and drawn at 9 o'clock, `lfit y x, mlabvposition(x)` is accepted (measured, E9). A type list would refuse both.
5. `_dash_option_columns` feeds both modes' data plans; a wrong name there drops or adds a column everywhere.
6. Commit 2 adds about 30 directives to every shipped scheme file, which moves the directive-count pin and the help sentence that states it.
7. The served copy loop skips a misspelt name silently (RK-9).

**Mitigation.**
1. Per-row columns are keyed by variable, fallback clock and distance (`__dash_mlabvpos_<var>_p<k>_d<n>_x|_y|_a|_b`); a test draws two layers on one source with different `mlabposition()`/`mlabgap()`.
2. dropline and pcscatter carry the values under the reserved column `GlyphMapper._MLABVPOS_VALUES` and pass `vpos_col`, as `label_col` is passed; tests use variables named `x`, `y` and `y0`.
3. The values are read through `_dash_date_units` for a date variable; fixture case DT.
4. `_dash_fold_mlabv` implements twoway's own count (`twoway_y2xview_parse.class:36-44`, `twoway_lfit_parse.class:35-41`, `twoway_mspline_parse.class:25-26`), and the renderer has no type gate; MV-11 pins the quirks against live twoway.
5. `_dash_option_columns` adds the name only when it is one Stata name (`_dash_mlabvpos_name`); its existing callers' tests (`test_pipeline_integration.py` and every file naming it) run in 37-04.
6. The regeneration is one extractor run, never hand-patched (R7); 37-18 re-derives the pin and 37-19 the help sentence; Q-37.1 (resolved) keeps a strike form for the orchestrator only.
7. G4 guards in 37-04, where the name and its first caller land together; `TestTheServedCopy` runs the generated app in 37-05.

## Dependencies

- **Depends on: 08, 11, 33.**
  - S08 (batch 3): `_apply_mlabel_opts(…, label_col=None, radius_px=None)`, the label distance `radius_px + gap_px` along the clock's unit vector (clock 0 → no offset), `_mlabel_gap_px(raw, default_pt, ref_in)` and `resolve_size(…, "text", …)` (TR-08.9). The per-row offsets multiply the same distance.
  - S11 (batch 4): `string asis` style options, `_dash_stylelist_keys()` (its comment names "S37 `mlabtextstyle`"), `_dash_stylelist_pick`, the per-series `_dash_plot_opts_to_json … series` and the repeats probe (TR-11.1-TR-11.9).
  - S33 (batch 11): the marker-label default size and colour from `p#label`/`plabel` (research p1-04 §4B-1: `SchemeParser.p_label_sizes[15]`, `p_label_colors[15]`, chain `color p#label → color plabel → p#`, `gsize p#label → gsize plabel`), the extractor's `plabel` keys and the regenerated files `mlabtextstyle()` starts from.
  - S01 provides the open entry `P1.24`, its `WP30_OPEN` key, the markers `<!-- WP-30 P1.24 -->` under `### Fixed in WP-30` and at the end of `### Changed behaviour (may need your do-files changed)`, the S37 stub block of `test/test_wp30_truth.cscript` and the map anchors `# WP-30 S37 (P1.24): mlabvposition() and mlabtextstyle() (P1.24)`.
  - Landed before and read here, not depended on by the manifest: S02 (extractor stanza TR-02.9, `scripts/stata_slot.sh`), S06 (notes leave as `(note: …)` through `_dash_warn_once`'s `dash:` text), S20 (mlabel() lists in `s(mlabel)`), S24 (the directive-count pin's current bounds), S32 (the pending list after the p# names left it), S34 (schemes along the ado-path).
- **Blocks:** none (manifest). Hand-offs, not dependencies: S40, S45, S49, S51 and S56 move the same pending pins later (R10); S45 judges the type refusal on the recast type (register P1.24.1); S49 keeps the offsets physical (manifest scope).
- **Parallel batch: 13**, merge order S37, S38.
- **Can run with:** S38 (region styling). S38 edits `_make_figure_body`, the template's region block, `_dash_subopt_canon`'s region table, Mata `_dash_rep_subkey`/`_dash_rep_merge` and the `_extract_region_*` readers; S37 edits none of them, and S38 edits neither `_apply_mlabel_opts`, `_dash_parse_plot_opts`, the mappers nor any scheme file.

## Evidence

Anchors are at `c96facd` (dash.ado 8,487 lines, dash_parse.mata 6,093, dash_render.py 37,689, dash.sthlp 3,822). S08, S11, S20, S32 and S33 land before batch 13 and move many of them; the executor re-finds each by symbol at `batch-13-base` and treats the numbers as approximate.

### E1. Declared and pending, never serialised (dash.ado)

`_dash_parse_plot_opts` (897) declares both with twoway's minimum abbreviations (:957):

```stata
957        MLABTextstyle(string)     MLABVposition(string)     XOVERHANGs ///
```

and puts both on the pending list (:1075-1079):

```stata
1075    // WP-22: mlabtextstyle() names a text style in a .scheme file, and
1076    // mlabvposition() a variable of clock positions, one per observation;
1077    // dash draws a layer's labels at one position in the scheme's style.
1078    if `: length local mlabtextstyle' local _dash_pending `"`_dash_pending' mlabtextstyle"'
1079    if `: length local mlabvposition' local _dash_pending `"`_dash_pending' mlabvposition"'
```

Neither has an `sreturn local` (block from :1135; the neighbours are `sreturn local mlabangle`/`mlabformat` at :1219-1220), and neither is in `_dash_plot_opts_to_json`'s key list (3131; the list at :3144-3158 holds the line `clcolor clpattern clwidth mlabangle mlabformat ///` at :3155). A scan of the plot parser at `c96facd` (this pass, Python over dash.ado's text):

```
169 declared; no s(): ['bins','mlabtextstyle','mlabvposition','xoverhangs','yoverhangs','mlg','cv','colv','pbgc','xla2','xsc2','xti2','yla2','ysc2','yti2']
plain s() not in JSON keys: ['sort1','bw']
```

All but the two P1.24 options and `xoverhangs`/`yoverhangs` (P2.13, "Sizing") are aliases folded into a serialised key. `sort1` is read by `_dash_sort_opt` and never written (test_twoway_option_parity.py:270-274), and `bw` is folded by `_dash_fold_bw`. Nothing tests this: test_option_surface.cscript O2-01..O2-10 checks return codes and the note only.

### E2. A second copy is not caught (dash_parse.mata, dash.ado)

`_dash_rep_unique` already lists `mlabvposition` among the options twoway takes once (dash_parse.mata:4695-4704). `_dash_opts_repeats` finds an option's key through the `s()` it sets (dash.ado:6136-6142):

```stata
6136    forvalues i = 1/`_rp_n' {
6137        local _rp_key`i' ""
6138        sreturn clear
6139        capture `parser' , `macval(_rp_tok`i')'
6140        if _rc continue
6141        local _rp_sm : s(macros)
6142        mata: st_local("_rp_key`i'", _dash_rep_keyof(st_local("_rp_sm")))
```

With no `s()`, the key is empty and `mlabvposition(p9) mlabvposition(pos)` is accepted. Once the option sets `s(mlabvposition)`, `_dash_refuse_repeat` (6157) refuses it as twoway does: `option mlabvposition() not allowed`, r(198).

### E3. The variable never reaches the data (dash_parse.mata)

`_dash_extract_vars` (2229) collects the option-named variables from the plot JSON (:2237-2242):

```mata
2237    keys    = (char(34)+"yvar"+char(34)+":",   char(34)+"xvar"+char(34)+":",  char(34)+"var"+char(34)+":",
2238               char(34)+"yvar1"+char(34)+":", char(34)+"yvar2"+char(34)+":",
2239               char(34)+"y1var"+char(34)+":", char(34)+"x1var"+char(34)+":", char(34)+"y2var"+char(34)+":", char(34)+"x2var"+char(34)+":",
2240               char(34)+"mlabel"+char(34)+":",
2241               char(34)+"colorvar"+char(34)+":",
2242               char(34)+"wexp"+char(34)+":")
```

Its callers are dash.ado:6532 (`_dash_prepare_spec`, the immediate route) and :7619 (the build route).

### E4. The renderer's column tables (dash_render.py)

```python
25504 _DASH_OPT_VAR_KEYS = ("colorvar", "mlabel", "wexp")
...
25531 def _dash_option_columns(options, columns=None):
25536     for key in _DASH_OPT_VAR_KEYS:
25537         if key == "mlabel":
25538             v = _dash_mlabel_names(options)[0]
25539         else:
25540             v = str((options or {}).get(key, "") or "").strip()
```

Every column consumer goes through `_dash_option_columns`: the saved column lists (:1446, :1517, `DashRenderer._collect_plot_vars` :29087), the embed plan (:28168) and the served `extra_cols` (emitted at :34844, :34980, :34998). `_DASH_OPT_VAR_KEYS` is already on the served constants list (:32918); `_dash_option_columns` and `_dash_mlabel_names` are on the functions list (:33355-33356):

```python
33355                          # The columns a layer's options name.
33356                          "_dash_mlabel_names", "_dash_option_columns",
```

### E5. One position per layer (dash_render.py, `_apply_mlabel_opts`, 9302-9500)

```python
9424         kwargs: dict[str, Any] = dict(
9425             x=xvar,
9426             y=yvar,
9427             text=text_col,
9428             source=source,
9429             text_font_size="10px",
9430             x_offset=4,
9431             y_offset=4,
9432         )
...
9466         pos = str(options.get("mlabposition", "3") or "3").strip()
9467         if pos in GlyphMapper._MLABEL_CLOCK_NAMES:
9468             p = int(pos)
...
9474         (bx, by), (ux, uy), (align, baseline) = GlyphMapper._MLABEL_CLOCK[p]
```

`mlabvposition` is never read. `_MLABEL_CLOCK` (7907-7921) holds, per clock 0-12, a base pair, the unit vector and Bokeh's `(text_align, text_baseline)`, measured right on 23sep2026 (e.g. `9: ((-4, 0), (-1.0, 0.0), ("right", "middle"))`, `0: ((0, 0), (0.0, 0.0), ("center", "middle"))`). S08 replaces the base pair by `radius_px + gap_px` along the unit vector (TR-08.9); the table's unit vectors and anchors stay. The text column it derives is keyed by the variable alone (:9395 `text_col = f"{_DASH_MLABEL_PREFIX}{mlabel_var}"`, computed only when absent, :9396-9416); `_mlabformat_column` keys by variable AND format (:9592) because "the saved page shares one source among its layers".

### E6. Where labels are drawn, and which sources carry a column

The 11 call sites of `_apply_mlabel_opts`: map_scatter :9861 (also scatter's view subset through `_subset_source` :9866, and connected, dot and rconnected, which call map_scatter), map_bar :10289, map_dropline :13509, map_rcapsym :13623-13624, map_pcscatter :13953, map_pcarrow :14103, map_pcbarrow :14175, map_pccapsym :14282, `_immediate_labels` :14418, map_rscatter :14632.

- **Carry every column, no shadowing:** map_scatter (the graph source or its subset), map_bar (its frame copies every column of the data's length, :10170-10184), pcarrow and pcbarrow (`ColumnDataSource(self._carry_cols(source, dict(ColumnDataSource(clean).data), clean.index.to_numpy()))`, :14062-14064 and the pcbarrow twin), pccapsym (`seg_src` from the frame's own variable-named columns plus `_carry_cols`), rcapsym (the caller's source). The research's "`_pc_clean_with_label` must copy it" (§4a.3) is not needed: pcarrow and pcbarrow carry every source column through `_carry_cols` after the frame.
- **Derived names that shadow** (`_carry_cols` "never overwrites" a key, :8124-8126):
  - map_dropline (:13457-13460): `_dl_cols = {"x": x_plot, "y": y_plot, "y0": zeros, xvar: x_arr, yvar: y_arr}`;
  - map_pcscatter (:13911): `_pc_cols = {"x": x_all.tolist(), "y": y_all.tolist()}` over the stacked endpoints; its labels already ride a reserved column, `_DASH_MLABEL_VALUES` (:3587, used at :13896-13900);
  - map_rscatter (:14590-14611): stacked `x`, `y`.
- **The immediate path drops the option** (:14416-14417), as twoway ignores it on scatteri and pcarrowi (measured, E9):

  ```python
  14416             opts = dict(options, mlabel=col, mlabposition=pos)
  14417             opts.pop("mlabvposition", None)
  ```

### E7. The text box table holds 14 names (dash_render.py)

`SchemeParser._NOTE_TEXTBOXES` (6751-6766) maps a note() text box name to `(size key, colour key, drawbox, fill key)` for 14 names (small_body, body, smbody, key_label, legend_key, heading, legend_title, subheading, clegend, axis_title, label, small_label, reverse_big, filled); `_init_note_textbox` (6769, LOW: 2 impacted) is its only reader (UNKNOWN for the constant, confirmed by grep). StataNow ships 37 `ado/base/style/textboxstyle-*.style` files. Each reads `set size scheme <key>` and `set color scheme <key>` (transcribed this pass from 19.5's files; `name size/colour`, `=` the same key as the size):

```
axis_title axis_title/axis_title    body body/body                    bordered filled_text/filled_text
clegend subheading/subheading       editor text_option/text_option    filled filled_text/filled_text
fpbody fpbody/fpbody                fpcollabel fpcoltitle/fpcoltitle  fpcoltitle fpcoltitle/fpcoltitle
fpcustom fpbody/fpbody              fplabel fpbody/fpbody             fpnulllefttext fpnulllefttext/fpnulllefttext
fpnullrighttext fpnullrighttext/=   fpspacer fpspacer/fpspacer        fptick_label fpbody/tick_label
heading heading/heading             key_label key_label/key_label     label label/label
legend_key key_label/key_label      legend_title heading/heading      matrix_label matrix_label/matrix_label
matrix_marklbl matrix_marklbl/=     minortick_label minortick_label/tick_label
p# p#label/p#label                  p#barlabel p#barlabel/p#barlabel  p#boxlabel p#boxlabel/p#boxlabel
reverse_big reverse_big/reverse_big_text  small_body small_body/small_body  small_label small_label/label
smbody small_body/body              sts_risktable sts_risk_label/=    sts_risktitle sts_risk_title/=
subheading subheading/subheading    subheading_gs subheading/subheading
text_option text_option/text_option tick_biglabel tick_biglabel/=     tick_label tick_label/tick_label
```

The shipped `dash-*.scheme` files carry only some of those keys (count of the 20 files at `c96facd` holding `gsize K` / `color K`): body, heading, subheading, small_body, key_label, axis_title, tick_label 20/20 each; reverse_big 1/1, reverse_big_text -/1; label, small_label, filled_text, text_option, the fp* keys, matrix_label, matrix_marklbl, minortick_label, sts_risk_label, sts_risk_title, tick_biglabel, pbarlabel, pboxlabel 0/0. StataCorp schemes override several of the missing keys (grep of `ado/base/s/scheme-*.scheme`): e.g. `gsize matrix_label` in economist, `color matrix_label` in s1rcolor, s1color, s2mono; `gsize label` in economist, s1manual; `color label` in s1color, s1rcolor, s2mono; `gsize minortick_label` in economist, s1manual. So the keys must be transcribed per scheme (TR-37.18), not defaulted.

### E8. twoway's own rules (StataNow 19.5 class files, read as text)

- `twoway_yxview_parse.class:187` declares `MLABVposition(name)`; :308-317 unabbreviate it with `unab` (except on the "allow anything" immediate types) and append it to the varlist: ``.varlist = "`:list varlist | mlabvposition'"``. The label variables were appended the same way at :259 (``.varlist = "`:list varlist | labclean'"``).
- The count rules (the message prints the whole `.varlist`):
  - range types, `twoway_y2xview_parse.class:36-44`: ``local vlist : list vlist - mlablist``; more than 3 → ``{p 0 8}`.viewtype' requires 3 variables: `.varlist'``, r(103) (fewer → r(102));
  - lfit, qfit, lfitci, qfitci, fpfitci (`twoway_lfit_parse.class:35-41`) and fpfit: the label variables subtracted, more than 2 → `too many variables specified: <varlist>`, r(103);
  - mspline and mband (`twoway_mspline_parse.class:25-26`): no subtraction, more than 2 → the same words;
  - lowess, lpoly, lpolyci (`syntax varlist(numeric min=2 max=2)` on the list less the label variables) and kdensity (one variable) → `too many variables specified`, r(103).
- `mlabtextstyle()` is folded `rightmost` into `label(textstyle(X))`, and `mlabsize()`/`mlabcolor()` into `label(textstyle(size(X)))`/`color(X)` (`twoway_yxview_parse.class:656-664`), so the explicit size and colour win in either order.

### E9. twoway's truth (measured; Stata truth has the commands)

Positions (research §3 and critic, re-measured this pass in `p1.do`-`p4.do`; 18 points on a diagonal, `pos` 0..12 then `.`, 3.5, 13, -1, `.a`):

| Case | `twoway scatter y x, mlabel(lab) …` | Measured |
|---|---|---|
| A | `mlabvposition(pos)` | rows 0..12 exactly as `mlabposition(k)`; `.`, `.a` at 3; 3.5, 13, -1 at 12 with `(note:  named style 3.5 not found in class clockdir, default attributes used)` per value; rc 0 |
| C | `+ mlabposition(9)` | `.`, `.a` at 9: a missing value takes `mlabposition()` |
| G | `+ mlabgap(5)` | each row's offset widens along its own direction; 0 unchanged |
| K3 | byte copy of `pos` | 3.5 stored as 3, drawn at 3 |
| E2 | string variable, `+ mlabposition(6)` | rc 0, all at 6 (at 3 without `mlabposition()`); no note |
| My2 | `scatter y y2 x, mlabel(lab lab) mlabvposition(p9)` | both series at 9 |
| By | `by(g)` | each panel's rows at their own clocks |
| D | no `mlabel()` | rc 0, no labels |

Types (t4, t8, t9, `p1.do`): drawn per row on scatter, connected, bar, dot, dropline, pcscatter, pccapsym, pcarrow, pcbarrow. Accepted with no labels on line, spike, area, pcspike, tsline (`nosuch` r(111)). Never read on histogram, function, scatteri, pci, pcarrowi (`nosuch` rc 0; `scatteri 1 1 "a" 2 2 "b", mlabvposition(p9)` draws at 3). Refused r(103) on the other 21, string or numeric variable alike, a missing variable r(111) first:

```
rarea requires 3 variables: y y2 x p9            rarea requires 3 variables: y y2 x lab p9      (with mlabel(lab))
(rbar rcap rcapsym rconnected rline rscatter rspike likewise; tsrline: "rline requires 3 variables: y y2 x p9", x the tsset variable)
too many variables specified: y x p9             (lfit qfit fpfit lfitci qfitci fpfitci mspline mband; "y x lab p9" with mlabel)
too many variables specified                     (lowess lpoly lpolyci kdensity, with or without mlabel)
rscatter requires 3 variables: yvalue y2 x labtext p9   (typed rscatter yval y2 x, mlabel(labt) mlabvposition(p): names unabbreviated)
option mlabvposition() not allowed               r(198)   (a second copy; also the graph-level form, already pinned at test_twoway_option_parity.cscript:2105)
option mlabvposition():  too many names specified r(103)  (mlabvposition(p9 y))
* invalid name                                   r(198)   (mlabvposition(p9*1))
variable nosuch not found                        r(111)
mlabvposition()  rc 0;   mlabvposition(p) (abbreviated variable) rc 0;   mlabv mlabvp mlabvpos mlabvposi rc 0
```

The count quirks (`p3.do`, `p4.do`): `rscatter y y2 x, mlabvposition(y)` rc 0; `lfit y x, mlabvposition(x)` rc 0; `rscatter y y2 x, mlabel(y) mlabvposition(p9)` rc 0 and drawn with all eight labels `text-anchor="end"` (9 o'clock); `rscatter y y2 x, mlabel(lab) mlabvposition(lab)` rc 0; `rscatter y y2 x, mlabel(. lab) mlabvposition(p9)` r(103) `rscatter requires 3 variables: y y2 x lab p9`; `rscatter y y2 x, mlabel(y)` alone r(102) `rscatter requires 3 variables: y y2 x` (mlabel's quirk, not this section's; Notes for the closeout).

Recast, for S45 (`p1.do`): `lfit y x, recast(scatter) mlabvposition(p9)` r(103) `too many variables specified: y x p9`; `rscatter y y2 x, recast(scatter) mlabvposition(p9)` r(103) `scatter requires 3 variables: y y2 x p9`; `scatter y x, recast(rscatter) mlabvposition(p9)` rc 0 with twoway's yxtype notes.

Text styles (research t5, t7; `p5.do`, `p7.do`), label font size in the exported SVG and its fill:

| style | stcolor | s2color | economist | s1rcolor |
|---|---|---|---|---|
| none (default `p#`) | 89.94 #1A85FF | 79.94 #1A476F | 44.01 #3E647D | 79.94 #FFFF00 |
| heading | 157.44 #000000 | 139.96 #1E2D53 | | |
| subheading | 123.69 #000000 | 110.01 #000000 | | |
| body, label, tick_label, axis_title, key_label | 112.56 #000000 | 99.99 #000000 | body 47.52, label 60.49 #000000 | 99.99 #FFFFFF |
| matrix_label | 135.00 #000000 | | 65.99 #000000 | 120.04 #FFFFFF |
| text_option (and editor) | 112.56 #000000 | | 55.00 #000000 | 99.99 #FFFFFF |
| fpbody / tick_biglabel / sts_risktable | 110.03 / 123.69 / 112.56 #000000 | | | |
| p3, p3barlabel | 89.94 #00BF7F (p3's) | | p3barlabel 44.01 #82C0E9 | p3barlabel 79.94 #0080FF |
| nosuch, Heading, p0, p16 | 112.56 #000000 + note | 99.99 #000000 + note | 47.52 #000000 (= body) | 99.99 #FFFFFF (= body) |
| heading + mlabsize(vsmall), either order | 67.50 | 60.02 #1E2D53 | | |
| heading + mlabcolor(red), either order | 157.44 #FF0000 | 139.96 #FF0000 | | |
| heading + mlabsize(*2) | 315.06 (2× heading) | | | |
| mlabsize(*2) alone | 179.89 #1A85FF (2× default) | | | |

The note is `(note:  named style nosuch not found in class textstyle, default attributes used)`; the case matters (`Heading` is noted). Twice: the rightmost copy wins (`heading` then `body` draws body, 112.56). A list: `scatter y y2 x, mlabel(lab lab) mlabtextstyle(heading body)` gives y heading and y2 body; a lone `mlabtextstyle(heading)` styles only y (y2 keeps p2's 89.94 #D41159); `mlabtextstyle(. heading)` gives y p1's default and y2 heading (S11's padding rule). Accepted on line, lfit and rscatter (rc 0); quoted `mlabtextstyle("heading")` rc 0; `mltextstyle()` (textstyle.sthlp's spelling) is r(198) and stays dash's unknown option.

### E10. Tests that pin today's behaviour (flipped in place, never deleted; re-measured by 37-07, 37-08, 37-16 and 37-17)

- `test/test_unsupported_report_is_true.py::test_a_plot_option_reported_unsupported_really_is[mlabvposition]` and `[mlabtextstyle]`: parametrised by the pending list (PLOT_VALUES :121-122). The entries move to `LIVE_VALUES`, so `test_a_plot_option_not_reported_unsupported_really_works[mlabvposition]`/`[mlabtextstyle]` take their place.
- `test/test_unsupported_report_is_true.py::TestTheListIsCoveredAndHonest::test_the_blocks_were_actually_found` (:240, 48 at `c96facd`; S32 moved it first).
- `test/test_help_conformance.py::TestTheParsersFoundSomething::test_the_ignored_list_was_found` (:598, 48) and `::test_the_unsupported_section_was_found` (:604, 48).
- `test/test_help_claims_8.py::TestAnUnsupportedOptionIsInertWhenServed::test_plot_level[mlabvposition]` and `[mlabtextstyle]` leave their parametrisation with the pending list (`_CONTEXT` :1272-1273 is left as data); their positive counterparts are this section's served tests.
- `test/test_help_claims_8.py::TestTheUnsupportedSectionSaysWhatTwowayDoes::test_every_listed_option_is_still_listed` and `test/test_help_conformance.py::TestTheUnsupportedSectionIsTrue::*`: kept green by the help edit in the same commit.
- `test/test_help_claims_8.cscript` HC8-02 (:387-428): `mlabvposition(pos)`/`mlabtextstyle(heading)` in `p_opts`, both in `p_names` (must be named); the comments and done text count 48.
- `test/test_twoway_option_parity.cscript` TP-06 rows `mlabv(pos)` and `mlabt(heading)` (:481-487, must be named) and TP-13a's controls (:1289-1297, `c2t`/`c2v` must be 1); the header comment :48.
- `test/test_stylelists.py` (S11) `_NOT_YET` holds `mlabtextstyle` and `_STYLE_KEYS` lacks it; `test/test_varlist_expansion.cscript` SL-01 counts `_dash_stylelist_keys()` (as S20 and S32 left them).
- `test/test_help_claims_8.py::TestTheShippedFiles::test_80_to_140_directives` (:1014; as S24/S33 left it) moves with the regeneration.
- Not flips: test_option_surface O2-01 replays twoway_corpus.do:356-357 on scatter (rc 0 stays); `test/fixtures/rejected_options.json:1446-1478, :4198-4215` record `dash_rc 198` that no test asserts (S58's, A145); test_twoway_option_parity.py `_F3_PLOT` (minimum abbreviations unchanged).

### E11. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, index at `c96facd`)

| Symbol | Risk | Impacted / direct / processes | Action |
|---|---|---|---|
| `GlyphMapper._apply_mlabel_opts` | CRITICAL | 16 / 10 / 10 | warn; one keyword and two blocks added, both gated on their option |
| `_dash_option_columns` | CRITICAL | 15 / 4 / 13 | warn; one branch added |
| `ServerAppBuilder._glyph_layer_lines` | HIGH | 4 / 1 / 4 | warn; one name appended at S37's anchor |
| `GlyphMapper._pc_clean_with_label` | HIGH | 4 / 2 / 3 | not edited (E6) |
| `SchemeParser._init_note_textbox` | LOW | 2 / 1 / 2 | not edited |
| `map_dropline`, `map_pcscatter` | UNKNOWN | — | dispatch dict, confirmed by grep (28501) |
| `_DASH_OPT_VAR_KEYS`, `_NOTE_TEXTBOXES`, `_FALLBACK_PROPS` | UNKNOWN (constants) | — | grep: :25536, :29076, :32918; :6769; :5834, :6438 |
| dash.ado and Mata programs | UNKNOWN | — | grep callers in Risk |

## User stories

- **US-37.1** As a twoway user, I want `scatter y x, mlabel(lab) mlabvposition(pos)` to put each label at its own clock position, so a do-file that moves crowded labels apart draws as in Stata, in the saved page and the served app, and stays so after I move a filter.
- **US-37.2** As a twoway user, I want a missing position to fall back to `mlabposition()`, an impossible one to be drawn at 12 with a note, and `mlabgap()` to push each label outward along its own direction, so my data's edge cases draw as twoway draws them.
- **US-37.3** As a twoway user, I want dash to refuse `mlabvposition()` exactly where twoway refuses it, with twoway's words, so a pasted command that fails in Stata fails the same way in dash.
- **US-37.4** As a twoway user, I want `mlabtextstyle(heading)` (or `p3`, `small_body`, `tick_label`, …) to draw labels in the scheme's text style, one style per y when I give a list, so styled labels look as in Stata.
- **US-37.5** As a maintainer, I want a test that fails whenever an option declared in dash.ado reaches neither the spec nor a named allowlist, so an accepted option cannot again be silently dropped.

## Business requirements

- **BR-37.1** With `mlabel()` and `mlabvposition(varname)` on scatter, connected, bar, dot, dropline, pcscatter, pccapsym, pcarrow or pcbarrow, each observation's label is placed at the clock position its row holds, as `mlabposition()` places a label at that position, in every by() panel and under the layer's own if/in.
- **BR-37.2** A position that is a whole number from 0 to 12 is that clock. A missing value (`.` and `.a`-`.z`) and every row of a string variable take `mlabposition()`, else 3, silently. Any other number is drawn at 12 and the distinct values are named once per variable per render (at most ten, then a count). A date-formatted variable is read as its stored number. `mlabgap()` widens each label's offset along its own direction; position 0 is never offset.
- **BR-37.3** One `mlabvposition()` variable applies to every y of the layer; it is never split as a style list.
- **BR-37.4** dash refuses, in twoway's words and with its codes: `mlabvposition()` that adds a variable beyond what the type takes (twoway's count rule) on rarea, rbar, rcap, rcapsym, rconnected, rline, rscatter, rspike, tsrline (r(103), `<type> requires 3 variables: …`, tsrline as `rline`), lfit, qfit, fpfit, lfitci, qfitci, fpfitci, mspline, mband (r(103), `too many variables specified: …`), lowess, lpoly, lpolyci, kdensity (r(103), `too many variables specified`); a second copy (r(198)); two names (r(103)); a non-name (r(198)); a variable that does not exist (r(111)), each in twoway's order. The quirks twoway accepts (a position or label variable that is already a plotted variable) are accepted.
- **BR-37.5** On line, spike, area, pcspike and tsline the option is checked and accepted and draws nothing; on histogram, function, scatteri, pci and pcarrowi it is not read at all. Neither option is named in the "ignoring unsupported option(s)" note any more; nothing is printed where twoway prints nothing (M6).
- **BR-37.6** The positions hold in both modes before and after any saved or served filter move: every kept row keeps its own clock, and a page drawn from the kept rows looks the same.
- **BR-37.7** `mlabtextstyle(textstyle)` takes any of Stata's 37 shipped text box style names (`p#`, `p#barlabel`, `p#boxlabel` for # 1-15), case as written, and draws the labels at that style's size and colour in the graph's scheme. `mlabsize()` and `mlabcolor()` win in either order; a relative `mlabsize(*#)` scales the style's size. It is a style list, one element per y. The rightmost copy wins. An unknown name (including a user's own textboxstyle file, P2.55) is noted as twoway notes it and drawn in `body`.
- **BR-37.8** Label offsets are in screen units, independent of the data and the axes, so a transposed (horizontal) layer keeps each label's physical clock position.
- **BR-37.9** Every option declared in `_dash_parse_plot_opts` and `_dash_parse_graph_opts` reaches the spec (an `s()` the writers read) or is an alias or on a named allowlist with its reason; a test enforces it.

## Technical requirements

### Commit 1: label positions

- **TR-37.1 dash.ado serialisation.**
  - `_dash_parse_plot_opts`: add `sreturn local mlabvposition : copy local mlabvposition` directly after `sreturn local mlabformat : copy local mlabformat` (:1220). Delete the pending line :1079 and reword the comment :1075-1077 to speak of `mlabtextstyle()` alone. The declaration stays `MLABVposition(string)`; it is not a style list (BR-37.3) and is not added to `_dash_stylelist_keys()`.
  - `_dash_plot_opts_to_json`: add `mlabvposition` to the key list directly after `mlabformat` (the line `clcolor clpattern clwidth mlabangle mlabformat ///`, :3155 before S11). Under S11 the key is read whole for every series (it is not in `_dash_stylelist_keys()`).
- **TR-37.2 `_dash_mlabv_parse`** (new program, directly above `_dash_fold_mlabv`; not sclass; never touches `s()`):

  ```stata
  program define _dash_mlabv_parse
      version 19
      syntax [, MLABVposition(name)]
      unab mlabvposition : `mlabvposition'
      c_local _mv_name `mlabvposition'
  end
  ```

  It is twoway's own declaration and unabbreviation (E8), so the messages and codes are Stata's: `option mlabvposition():  too many names specified` r(103), `<tok> invalid name` r(198), `variable <x> not found` r(111), and an ambiguous abbreviation as `unab` words it.
- **TR-37.3 `_dash_fold_mlabv`** (new sclass program, directly after `_dash_fold_mlab`'s `end`, with a header comment of the `_dash_fold_mlab` kind citing E8/E9):
  1. `args ptype pvars`. Read `s(mlabvposition)` by value (`mata: st_local("v", st_global("s(mlabvposition)"))`); empty → `exit`.
  2. `ptype` in `histogram function scatteri pci pcarrowi` → `sreturn local mlabvposition ""` and `exit` (never read, BR-37.5).
  3. `capture noisily _dash_mlabv_parse , mlabvposition(`macval(v)')`; on `_rc` → `exit _rc`. Then `sreturn local mlabvposition `"`_mv_name'"'` (the unabbreviated name).
  4. Only for the 21 types of BR-37.4 (three lists: `mv_range` = the eight range types and tsrline; `mv_fit` = lfit qfit fpfit lfitci qfitci fpfitci mspline mband; `mv_smooth` = lowess lpoly lpolyci kdensity): read `s(mlabel)` by value without its `.` tokens, in one Mata line (`mata: st_local("ml", invtokens(select(tokens(st_global("s(mlabel)")), tokens(st_global("s(mlabel)")) :!= ".")))`), and `capture unab labs : `macval(ml)'`; on failure `exit` (a missing label variable or an S20 shorthand is refused later by the checks that own it, as twoway refuses the label first).
  5. `local all : list pvars | labs`, then `local all : list all | _mv_name`. The counted list is `all` on mspline and mband, else `: list all - labs`. The limit is 3 on `mv_range`, 1 on kdensity, else 2. At or under the limit → `exit` (the quirks of E9 are accepted).
  6. Over it: `mv_range` → `mata: _dash_say("err", <shown> + " requires 3 variables: ", st_local("all"), "")` with `<shown>` `rline` for tsrline, else the type; `mv_fit` → `_dash_say("err", "too many variables specified: ", st_local("all"), "")`; `mv_smooth` → `display as error "too many variables specified"`. Then `exit 103`.
  - The value reaches a command line only inside `macval()` in step 3, where `syntax`'s name type refuses anything but one name; `labs` and `_mv_name` are names `unab` returned. Every echo goes through `_dash_say`.
  - If a test shows `unab` clearing `s()` (it does not in 19.5's built-in), replace both `unab` calls by Mata `_st_varindex(name, 1)` lookups with the same messages; MV-08 pins that the other keys survive.
- **TR-37.4 The call site.** In `_dash_process_segment`, directly before `_dash_fold_bw "`ptype'"` (:4121), under a two-line comment:

  ```stata
  _dash_fold_mlabv "`ptype'" "`yvar1' `yvar2' `yvar' `xvar'"
  ```

  On range types `yvar` is empty and `xvar` is the tsset variable for tsrline (:3646); on the fits and smooths `yvar1`/`yvar2` are empty; kdensity's `xvar` is empty. It runs before `_dash_fold_mlab`, so `mspline y x, mlabel(lab) mlabvposition(p9)` gets twoway's full message, and before `_dash_validate_opts`.
- **TR-37.5 Mata.** `_dash_extract_vars` (dash_parse.mata:2229): add `char(34)+"mlabvposition"+char(34)+":",` after the `"mlabel"` key (:2240) and name the option in its comment block (:2221-2226). No new Mata function, no `_needed` or header-index change.
- **TR-37.6 Renderer: the name.**
  - New module function `_dash_mlabvpos_name(options)`, directly after `_dash_mlabel_names` (25515-25528): the stripped `mlabvposition` value when `_dash_is_stata_name` accepts it, else `""`. Docstring: why one name (dash.ado refuses two; a hand-written spec may carry anything).
  - `_DASH_OPT_VAR_KEYS = ("colorvar", "mlabel", "mlabvposition", "wexp")`, its comment extended by one sentence.
  - `_dash_option_columns`: `elif key == "mlabvposition": v = _dash_mlabvpos_name(options)`. Its docstring names the option.
- **TR-37.7 Renderer: the per-row columns.**
  - `GlyphMapper._MLABVPOS_VALUES = "__dash_mlabvpos_values"` (a class attribute beside `_MLABEL_CLOCK`; it travels with the class).
  - New `GlyphMapper._mlabel_vpos_columns(self, source, options, fallback, distance, vpos_col=None) -> "tuple[str, str, str, str] | None"`, directly after `_mlabel_gap_px`:
    1. `raw` = the stripped option; empty → None. `name = _dash_mlabvpos_name(options)`; empty → `_dash_warn_once(("mlabvposition", raw, "name"), "dash: mlabvposition(<raw shown>) must name one variable; the labels are drawn at mlabposition().")` and None.
    2. `col = vpos_col or name`; absent from `source.data` → a once-only note "dash: mlabvposition(<name>): the variable is not in the data; the labels are drawn at mlabposition()." and None.
    3. `_is_text, _miss = self._mlabel_column_kind(source.data[col])`; text → None, silently (E9 E2).
    4. Values: `_dash_date_units(column, kind)` when `getattr(self, "date_vars", {}).get(name)` is a kind, else `_dash_float_values(column, coerce=True)`.
    5. Clocks, vectorised: `k = full(n, fallback)`; `whole = isfinite(v) & (v == floor(v)) & (v >= 0) & (v <= 12)`; `k[whole] = v[whole]`; `bad = isfinite(v) & ~whole`; `k[bad] = 12`. When `bad.any()`: one `_dash_warn_once(("mlabvposition", name, "range"), …)` naming the first ten distinct bad values in order of appearance (each `_dash_fmt_text(x, "%9.0g")`), then "and N more", in the form of the immediate path's note (:14404-14408): "dash: mlabvposition(pos): 3.5, 13, -1 are not a whole number from 0 to 12; those labels are drawn at 12 (above), where twoway draws them."
    6. From `_MLABEL_CLOCK`: `ux[k]`, `uy[k]`, `align[k]`, `baseline[k]` (13-row lookup arrays built once); `xo = where(k == 0, 0.0, distance * ux[k])`, `yo` likewise.
    7. Names: `base = f"__dash_mlabvpos_{name}_p{fallback}_d{dk}"` with `dk` = `round(distance * 1e6)` written as digits, `m` before a negative value; columns `base + "_x"`, `"_y"`, `"_a"`, `"_b"`, written only when `base + "_x"` is absent (deterministic, so a served redraw writes the same names). Offsets as float64 arrays, align and baseline as object arrays (P2.41).
    8. Return the four names.
- **TR-37.8 `_apply_mlabel_opts`** (CRITICAL, warn): add the keyword `vpos_col: "str | None" = None` after S08's `radius_px`, documented beside `label_col`. After the scalar position block sets `text_align`/`text_baseline` and the offsets (S08's form), call `self._mlabel_vpos_columns(source, options, p, <S08's distance radius_px + gap_px>, vpos_col)`; when it returns names, set `kwargs["x_offset"]`, `["y_offset"]`, `["text_align"]`, `["text_baseline"]` to `field(<name>)` (`from bokeh.core.properties import field`). No type gate: dash.ado's count rule is the gate (E9's rscatter quirk is drawn per row by twoway), and the immediate path keeps popping the key (E6). The docstring's option list names `mlabvposition`.
- **TR-37.9 The mappers.**
  - `map_dropline`: when `_dash_mlabvpos_name(options)` names a column of `source.data`, add `_dl_cols[self._MLABVPOS_VALUES] = np.asarray(source.data[<name>])[mask]` before `_carry_cols` (a datetime column stays an array), and pass `vpos_col=self._MLABVPOS_VALUES` at :13509.
  - `map_pcscatter`: beside `clean[_DASH_MLABEL_VALUES]` (:13896-13900), add `clean[self._MLABVPOS_VALUES]` from the variable's column (array for a date column), stack it as the labels are stacked (:13926-13932), and pass `vpos_col=self._MLABVPOS_VALUES` at :13953.
  - Not edited, and pinned by tests: map_scatter, map_bar, map_pcarrow, map_pcbarrow, map_pccapsym, map_rcapsym, map_rscatter, `_pc_clean_with_label`, `_immediate_labels`. If at `batch-13-base` `TestEveryLabellingType::test_type[bar-…]` shows map_bar's frame no longer carries the column (S14 or S27 rebuilt it), carry it as dropline does and say so in the commit body.
- **TR-37.10 Served copy list** (R2 row S37): `"_dash_mlabvpos_name",` on a new line directly after `"_dash_mlabel_names", "_dash_option_columns",` (dash_render.py:33356) in `_glyph_layer_lines`' functions tuple. No constant is added (`_DASH_OPT_VAR_KEYS` is listed at :32918 and edited in place; `_MLABVPOS_VALUES` and the methods travel with GlyphMapper). `_generate_app_source` is not edited.
- **TR-37.11 JS twins: none.** The per-row columns are data columns of the label's source. The saved `_FILTER_JS` filters every column of every graph and derived source by row from snapshots taken after the figures are built (`_snapshot_of`, :32068-32080 and :32207-32211; `_collect_derived_sources` :29662), and the served redraw rebuilds them through the mapper (deterministic names) or copies them by row (`_dash_refresh_linked` :24732, `_dash_refresh_unlinked` :24849). No module-level JavaScript string changes.
- **TR-37.12 Registries.**
  - `test/function_test_map.py`, under S37's anchor, alphabetically: `'GlyphMapper._mlabel_vpos_columns': 'test/test_mlabvposition.py::TestThePerRowColumns::test_every_clock_and_the_fallbacks'`, `'_dash_mlabvpos_name': 'test/test_mlabvposition.py::TestTheName::test_one_stata_name_or_nothing'`.
  - `test/program_coverage_map.py` `COVERAGE["dash.ado"]`, under S37's anchor: `"_dash_fold_mlabv": ("test_twoway_option_parity.cscript:MV-01", "test_twoway_option_parity.cscript:MV-02")`, `"_dash_mlabv_parse": ("test_twoway_option_parity.cscript:MV-06", "test_twoway_option_parity.cscript:MV-07")`.
- **TR-37.13 Help (commit 1)**, `dash.sthlp` "Marker Label Options" (R3, S37's) and the Unsupported entry (pending mover):
  - A `{synopt:{cmdab:mlabv:position(}{it:varname}{cmd:)}}` entry after `mlabp:osition(`: the clock position of each observation's label read row by row; the value rules of BR-37.2; one variable for every y; `mlabgap()` along each row's direction.
  - In "Where labels are drawn", one paragraph: the nine types; accepted and drawing nothing on line, spike, area, pcspike, tsline; not read on histogram, function, scatteri, pci, pcarrowi; refused as twoway refuses it on the range and fit types (r(103), its words), a second copy (r(198)), two names (r(103)), a non-name (r(198)).
  - The Unsupported entry "Marker-label placement and text style" (:3704-3709) keeps only its `{opt mlabtextstyle(textstyle)}` sentence; its heading becomes "Marker-label text style".
  - Every new or changed line is at most 79 characters.

### Commit 2: label text styles

- **TR-37.14 dash.ado and Mata.**
  - `MLABTextstyle(string)` becomes `MLABTextstyle(string asis)` (S11's TR-11.4 form; the minimum abbreviation stays).
  - `_dash_stylelist_keys()` (dash_parse.mata, S11's TR-11.1): append `mlabtextstyle` to the returned list and drop it from the "who adds later" comment. No other Mata change.
  - `sreturn local mlabtextstyle : copy local mlabtextstyle` after the `mlabvposition` line of TR-37.1; `mlabtextstyle` in `_dash_plot_opts_to_json`'s key list after `mlabvposition`; delete the pending line :1078 and its comment.
  - Nothing refuses it (twoway accepts it everywhere, E9); no `_dash_option_rules` entry; the repeats reduction keeps the rightmost copy (S11's probe handles an empty copy).
- **TR-37.15 SchemeParser's text box styles** (class 5646; methods and class attributes travel to the served app):
  - `_TEXTBOX_STYLES: "dict[str, tuple[str, str]]"`, directly above `_NOTE_TEXTBOXES` (:6744): the 34 fixed names of E7 to `(size key, colour key)`, transcribed from the fixture's `_meta.table` (never edited by hand; a test asserts equality). The three `p#` families are handled by the method, not the dict.
  - `textbox_style(self, name) -> "tuple[str, str] | None"`: `name` must be a `str` of at most 32 characters. An exact key of `_TEXTBOX_STYLES` → `(self._gsize(f"gsize {size_key}", <body size>), self._color(f"color {color_key}", <body colour>))`. A match of `^p([1-9]|1[0-5])(barlabel|boxlabel)?$` → for `p<n>`, S33's `p_label_sizes[n-1]`/`p_label_colors[n-1]`; for `p<n>barlabel`/`p<n>boxlabel`, `gsize p<n>barlabel` → `gsize pbarlabel` → `p_label_sizes[n-1]` and `color p<n>barlabel` → `color pbarlabel` → `p_label_colors[n-1]` (the fixture decides; if it disagrees, the chain is corrected to it, never the fixture). Anything else → None. The name is a key into the table, never a path or a file name.
  - `_FALLBACK_PROPS` (:5728) gains the textbox keys TR-37.18 transcribes, with s2color's values, so `SchemeParser.fallback()` resolves every name as dash-s2color does.
  - `_NOTE_TEXTBOXES` and `_init_note_textbox` are not edited; a guard asserts their 14 names' size and colour keys equal `_TEXTBOX_STYLES`'.
- **TR-37.16 `_apply_mlabel_opts` (commit 2).** After S33's defaults set `text_font_size`/`text_color` and before the `mlabcolor`/`mlabsize` blocks: when `mlabtextstyle` is non-blank, `self.scheme.textbox_style(value)` (a `p<n>` name carries its own index, as twoway reads `p3` on any layer, E9); None → `_dash_style_note("mlabtextstyle", value, "text style", "the body text style")` and `textbox_style("body")`; then set both kwargs. `mlabsize(*#)` then scales the style's size through S08's `resolve_size(…, css_to_pt(kwargs["text_font_size"]) …)` (E9: 315.06 = 2 × heading).
- **TR-37.17 Units (register P1.24.2).** Sizes come from `SchemeParser._gsize` in points, the unit S33's defaults use, so every ratio to the default is twoway's; nothing new is converted.
- **TR-37.18 The scheme keys (Q-37.1, resolved: regenerate).**
  - `scripts/extract_scheme_truth.py`: for every key `_TEXTBOX_STYLES` reads that the generated files lack (E7: label, small_label, filled_text, text_option, reverse_big, reverse_big_text, matrix_label, matrix_marklbl, minortick_label, tick_biglabel, sts_risk_label, sts_risk_title, fpbody, fpcoltitle, fpnulllefttext, fpnullrighttext, fpspacer, pbarlabel, pboxlabel; any `p#barlabel`/`p#boxlabel` a StataCorp chain sets), add a resolver property beside `"key_label_size"`/`"key_label_color"` (:1146-1153, :1252-1259), `color_of(...)` for colours and `scalar(..., "gsize", [...], lambda t: resolve_sized(r, "gsize", t))` for sizes, and one emitted group after the "Text sizes, one per textbox style" group (:1586-1593), headed "Text sizes and colours of the remaining text box styles, read by mlabtextstyle() (WP-30 P1.24)". A key a scheme's chain does not set is not written.
  - Run it once (`python3 scripts/extract_scheme_truth.py` with the arguments its header gives) to rewrite all 26 `dash-*.scheme` files and `test/fixtures/scheme_truth.json`; verify every pre-existing property of every scheme unchanged (R7).
  - Strike form, used only if the orchestrator refuses the A152 amendment before `batch-13-base` is recorded: no extractor change; a key absent from the scheme resolves to s2color's value (carried in `_FALLBACK_PROPS`); `test_mlabtextstyle.py` holds `_NOT_YET = {(<scheme>, <probe>): "per-scheme textbox keys"}` for the probes that then differ, `TestTheLabels` skips them by that table, and a guard `TestTheLabels::test_the_residuals_still_differ` asserts each still differs from the fixture (A146's form: recorded, never a failing test); S58 files the residual.
- **TR-37.19 Registries and help (commit 2).**
  - `test/function_test_map.py` under S37's anchor: `'SchemeParser.textbox_style': 'test/test_mlabtextstyle.py::TestTheTable::test_every_name_resolves'`.
  - `dash.sthlp` Marker Label Options: a `{synopt:{cmdab:mlabt:extstyle(}{it:textstyle}{cmd:)}}` entry: one of Stata's text box styles (`heading`, `subheading`, `body`, `small_body`, `label`, `tick_label`, `p1`-`p15`, …) read from the scheme; a style list, one element per y (link to Style lists); `mlabsize()`/`mlabcolor()` override it whatever their order; an unknown name, or a user's own textboxstyle file, is reported and drawn in `body`, as twoway draws it.
  - The Unsupported entry is removed whole.
  - "What the shipped files are" (:3537): the directive count is rewritten to the range 37-18 measures, in place, nothing else in that paragraph.
- **TR-37.20 Security (rule 1).**
  - The position variable reaches the renderer only as a name `_dash_is_stata_name` accepted; the per-row column names are built from it and numbers; align and baseline values come from `_MLABEL_CLOCK`; no user text becomes a Bokeh property name or field except through that check.
  - The notes echo through `_dash_display` (80 printable characters) and list at most ten numbers; the per-row work is O(rows) numpy.
  - dash.ado echoes through `_dash_say`; the value reaches one command line inside `macval()` and `syntax`'s name type.
  - The text style name is matched against a fixed table and one regex; it is never a path, never read from disk, never part of a scheme key except as a validated table entry or `p<n>` built from an integer.
  - The extractor reads Stata's style files as data, with a name regex `^textboxstyle-([A-Za-z0-9_#]+)\.style$` and a 64 KiB size bound per file; nothing is executed; no `shell=True`.
- **TR-37.21 Fixtures (R7).** `test/fixtures/mlabvpos_truth.json` (`scripts/extract_mlabvpos_truth.do`, commit 1) and `test/fixtures/mlabtextstyle_truth.json` (`scripts/extract_mlabtextstyle_truth.do`, commit 2), each with the D12 `_meta` stamp, added with `git add -f`, read by the tests that name them.

## Boundaries

- **Batch 13 partner S38 (P1.20a):** region styling, `_make_figure_body`, the template's region block, `_dash_subopt_canon`'s region table, Mata `_dash_rep_subkey`/`_dash_rep_merge`, the `_extract_region_*` readers and their copy-list entries, the Region Styling help. S37 touches none; S38 regenerates no scheme file and edits neither the extractor nor `_apply_mlabel_opts`.
- **Earlier sections, read only:** S08's `resolve_size`, `_mlabel_gap_px`, `_mlabel_radius_px` and the 11 call sites' `radius_px`; S11's splitter, normaliser, check and repeats probe (S37 adds one key); S20's `_dash_fold_mlab`, `_dash_fold_bw` and mlabel() list checks; S33's `p_label_*` defaults and their scheme keys; S06's channel.
- **Later sections:**
  - **S45 (P1.8b):** places `_dash_recast_opt` before `_dash_fold_mlabv` and makes the refusal judge the recast type (register P1.24.1), with E9's measured recast cases: a derived type keeps its own rule (`lfit, recast(scatter)` r(103)); a range type recast to a yx type is refused with the new type's name (`scatter requires 3 variables: y y2 x p9`); an out-of-group target falls back silently.
  - **S49 (P1.9a):** its transposition helper swaps a LabelSet's `x`/`y` fields only, never `x_offset`, `y_offset`, `text_align`, `text_baseline` or the `__dash_mlabvpos_*` columns; it measures twoway's horizontal labels and extends `TestOffsetsArePhysical` with horizontal bar and dropline.
  - **S40, S45, S49, S51, S56** move the pending-list pins after S37 (R10) and keep `TestDeclaredOptionsReachTheSpec` green for every option they declare or honour.
- **Not this section's:** `headlabel`, pc* first-point labels when the second point is missing, extended missing values, value-labelled dates (the rest of GAPS2-B27); `mlabstyle()` and the rest of P2.12; user textboxstyle files (P2.55); mlabel()'s r(102) quirk (Notes for the closeout); shadowing of `x`/`y` on rscatter's stacked source (P2.28); `xoverhangs`/`yoverhangs` (P2.13); `_dash_fold_mlab`'s own wording on mspline/mband (unchanged).
- **Never:** `scripts/regen_option_surface.py` (IR-7; it deletes hand-added declarations); a hand patch of a generated file; `_generate_app_source`, `_make_figure_body`, `_FILTER_JS`.

## Stata truth

Two new extractors in S02's form (TR-02.9 stanza, `<file>` their own name), then `adopath ++ "`repo'/"` and `global dash_nobrowser 1`. Their `_meta` block and python reader copy S19's `scripts/extract_series_label_truth.do` (`stata_version` = `c(stata_version)`, `born_date` = `c(born_date)`, `dash_commit` from `git rev-parse HEAD` captured with `shell` into a local and read through `Macro.getLocal`, `extracted` = today; the python block never calls Stata, never uses `shell=True`, writes a backtick as `\x60`). SVGs are read only through `scripts/svg_truth.py` (`svg_texts`). Each probe runs as `capture noisily` inside a named log (`log using "<tmp>/mv_<id>.log", text replace name(mvp)` … `log close mvp`) so its notes are recorded; exports go to `c(tmpdir)`.

### `scripts/extract_mlabvpos_truth.do` → `test/fixtures/mlabvpos_truth.json` (commit 1)

```stata
clear
set scheme stcolor
set obs 18
gen double x = _n
gen double y = _n
gen str3 lab = "R" + string(_n)
gen double pos = _n - 1 in 1/13
replace pos = 3.5 in 15
replace pos = 13 in 16
replace pos = -1 in 17
replace pos = .a in 18
gen byte bpos = pos
gen str4 spos = string(pos)
gen double dpos = pos
format dpos %td
gen double p9 = 9
gen byte g = mod(_n, 2)
gen double y2 = y + 20
gen double x2 = x + 0.5
gen double y3 = y + 0.5
```

- **References** (`REF_<t>_<k>`, k = 0..12): `twoway <t> <vars>, mlabel(lab) mlabposition(k)` for t in scatter, connected, bar, dot, dropline (vars `y x`) and pcscatter, pccapsym, pcarrow, pcbarrow (vars `y x y3 x2`); `REFG_scatter_<k>` with `mlabgap(5)`; `REFB_scatter_<k>` with `by(g)`. 143 exports.
- **Probes** (`scatter y x, mlabel(lab) …` unless named): A `mlabvposition(pos)`; C `mlabvposition(pos) mlabposition(9)`; G `mlabvposition(pos) mlabgap(5)` (classified against REFG); K3 `mlabvposition(bpos)`; E2 `mlabvposition(spos) mlabposition(6)`; DT `mlabvposition(dpos)`; BY `mlabvposition(pos) by(g)` (against REFB); MY2 `scatter y y2 x, mlabel(lab lab) mlabvposition(p9)`; T_<t> `<t> <vars>, mlabel(lab) mlabvposition(pos)` for the eight other types; RSQ `rscatter y y2 x, mlabel(y) mlabvposition(p9)`; SI `scatteri 1 1 "a" 2 2 "b", mlabvposition(p9)` against `scatteri 1 1 "a" 2 2 "b"`.
- **Records:** per probe `cmd`, `rc`, `notes` (the `(note:` lines of its log), and per label row `R<n>`: `anchor`, `dx`, `dy` (against the same type's `mlabposition(0)` reference, the label centred on its point) and `clock` = the k whose reference matches within 0.05 units and the same anchor, else null. MY2 records both series' anchors and `equal_to_ref` against `scatter y y2 x, mlabel(lab lab) mlabposition(9)`; RSQ records its anchors; SI records `equal_to_ref`. `_meta` also holds `scheme: "stcolor"`, `probes` (count), `data` (the 18 rows as written, `.a` as null).
- **Expected** (research §3, critic): A rows R1..R13 clocks 0..12, R14 3, R15..R17 12, R18 3, notes naming 3.5, 13, -1; C R14 and R18 9; K3 R16 (3.5 stored as 3) 3; E2 every row 6; DT as A; MY2 `equal_to_ref` true; T_* as A; RSQ every anchor `end`; SI `equal_to_ref` true.
- Run: `DASH_REPO="$WT" /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_mlabvpos_truth.do"` (log `$S/extract_mlabvpos_truth.log`; about 160 exports). `git add -f test/fixtures/mlabvpos_truth.json`.

### `scripts/extract_mlabtextstyle_truth.do` → `test/fixtures/mlabtextstyle_truth.json` (commit 2)

- **Table:** the python block lists `c(sysdir_base)/style/textboxstyle-*.style` (TR-37.20 guards) and records each name's `set size scheme <k>` and `set color scheme <k>` keys as `_meta.table` (37 names, `p#` names kept with `#`).
- **Data:** 3 rows, `x`, `y = 2x`, `y2 = y + 1`, `lab = "Q" + string(_n)`, `lab2 = "S" + string(_n)`.
- **Probes** under each of stcolor, s2color, economist and s1rcolor (`scatter y x, mlabel(lab) …`): `DEF` (none); one per fixed name of the table; `p1`, `p3`, `p3barlabel`, `p3boxlabel`; `nosuch`, `Heading`, `p0`, `p16`; `HV` `mlabtextstyle(heading) mlabsize(vsmall)` and `VH` the reverse; `HR`/`RH` with `mlabcolor(red)`; `H2` `mlabtextstyle(heading) mlabsize(*2)`; `TW` `mlabtextstyle(heading) mlabtextstyle(body)`; `QT` `mlabtextstyle("heading")`; `L2` `scatter y y2 x, mlabel(lab lab2) mlabtextstyle(heading body)`, `L1` `… mlabtextstyle(heading)`, `LD` `… mlabtextstyle(. heading)`. About 52 probes per scheme.
- **Records:** per scheme and probe `rc`, `notes`, and per series (Q, S) the label `size` and lower-cased `fill`.
- Run as above (`extract_mlabtextstyle_truth.log`, about 210 exports). `git add -f test/fixtures/mlabtextstyle_truth.json`.

### Area cases, `test/test_twoway_option_parity.cscript` (R1; one contiguous run after AX-08's block, whose last line is `set linesize `saved_ls'` at :2902, and before the `// Summary` divider at :2904, at `c96facd`)

Each case runs live twoway (`capture twoway … nodraw`, its rc and first error line from a log) and dash (`_ztp_run`), in the script's `nfail`/`faillist` pattern, printing `MV-nn PASS: …`. Data: `sysuse auto` plus `gen double p9 = 9`, `gen double q9 = 9`, `gen str4 sp9 = "9"`, `gen double pos = mod(_n, 13)`, `tsset` on a generated time variable for tsrline.
- **MV-01** (commit 1): for each of the 21 refused types, `mlabvposition(p9)`: dash rc = twoway rc = 103 and dash's error line equals twoway's.
- **MV-02:** the same with `mlabel(make)` on rscatter, lfit, mspline and lowess, typed with abbreviated variables (`rscatter mp tu wei, mlabel(ma) mlabvposition(q)`; no other auto variable starts `ma` or `q`): the line names the full names, `make` and `q9` among them.
- **MV-03:** a string variable `sp9` on rscatter and lfit: 103 both.
- **MV-04:** `mlabvposition(nosuch)` on rscatter and lfit: 111 both, `variable nosuch not found`.
- **MV-05:** `scatter …, mlabel(make) mlabvposition(p9) mlabvposition(pos)` and `mlabv(p9) mlabvposition(pos)`: 198 both, `option mlabvposition() not allowed`.
- **MV-06:** `mlabvposition(p9 pos)`: 103 both, `option mlabvposition():  too many names specified`.
- **MV-07:** `mlabvposition(p9*1)`: 198 both, the same error line.
- **MV-08:** `mlabvposition()` rc 0; `mlabv(po)`, `mlabvp(pos)`, `mlabvposi(pos)` rc 0 with `_ztp_hasval zqtp mlabvposition pos`, and `_ztp_hasval zqtp mlabel make` and `mcolor red` kept (s() survives the fold).
- **MV-09:** `mlabvposition(nosuch)` on histogram, function, scatteri, pci, pcarrowi: rc 0 both, and the spec holds no `mlabvposition` key.
- **MV-10:** line, spike, area, pcspike, tsline with `mlabvposition(p9)`: rc 0, the key in the spec, no note; with `nosuch`: 111 both.
- **MV-11:** the quirks: `rscatter … , mlabvposition(<its first y>)`, `lfit … , mlabvposition(<its x>)`, `rscatter …, mlabel(<its first y>) mlabvposition(p9)`, `rscatter …, mlabel(make) mlabvposition(make)`: rc 0 both; `rscatter …, mlabel(. make) mlabvposition(p9)`: 103 both, same line.
- **MV-12** (commit 2): `mlabtextstyle(heading)` on line, lfit, rscatter: rc 0 both, no note; `mlabtextstyle(heading) mlabtextstyle(body)` keeps `body`; `mlabt(heading)` keeps `heading`; `mlabtextstyle()` rc 0.
- **MV-13** (commit 2): `scatter mpg turn weight, mlabel(make make) mlabtextstyle(heading body)`: rc 0, the two plots' options hold `heading` and `body`; `mlabtextstyle(.. heading)`: dash rc = twoway rc.

### The S37 blocks of `test/test_wp30_truth.cscript` (R1)

Commit 1 fills S01's S37 stub; commit 2 adds a second block `* ==== S37 P1.24: mlabtextstyle() ====` directly below the first block's end line. Helpers `_s37_*` sit above the S37 header: a python `_s37_page()` that loads a saved page's embedded document JSON, finds its LabelSets and returns, per label row, `text_align` (field values resolved) and `text_font_size`/`text_color`.
- **MV-20:** `_dash_process_segment "scatter y x, mlabel(lab) mlabv(po)"` writes `"mlabvposition":"pos"`; live `twoway scatter y x, mlabel(lab) mlabv(po)` rc 0.
- **MV-21:** case A drawn live by twoway (SVG anchors) and by `dash … saving()`: per row, dash's align maps to twoway's anchor (`left`/`start`, `center`/`middle`, `right`/`end`) for all 18 rows.
- **MV-22:** case C likewise (`.`/`.a` right-aligned).
- **MV-23:** MY2: both series all `right`.
- **MV-24:** BY: per panel, as twoway.
- **MV-25** (commit 2): `mlabtextstyle(heading)` under stcolor: dash's size over its default equals twoway's ratio within 1 %, colours equal.
- **MV-26:** L2 per series.
- **MV-27:** `nosuch`: twoway's note and dash's `mlabtextstyle(nosuch)` note both printed; dash draws body.

## TDD test stubs

### Commit 1 regression tests, new `test/test_mlabvposition.py` (red at the batch-13 base unless marked guard; 37-01)

Module docstring: the defect (Overview), E8/E9, the fixture. Imports: `dash_render as dr`; from `test_mode_parity`: `_render_pair`, `_annotations`, `_spec as _mp_spec`; from `test_saved_filter_layers`: `_render`, `_move`, `_profile`, `_saved_of_rows`, `_MOVES`; from `test_served_filter_move`: `_move as _served_move`; from `test_server_layer_defects`: `plot_for`; `js_runner.requires_node`. `_FIX = json.load(test/fixtures/mlabvpos_truth.json)`; `_DATA` = its rows as a frame; `_both(plots, go=None)` → `{"saved": figs, "served": figs}`; `_row_clocks(labelset)` → per drawn row, the k of `dr.GlyphMapper._MLABEL_CLOCK` whose `(align, baseline)` equal the row's and whose unit vector is parallel to its `(x_offset, y_offset)` (k = 0 when both are 0).

- Test: the fixture has the four `_meta` keys, `stata_version` starting `19.`, `scheme == "stcolor"`, every probe id of Stata truth, A's notes naming 3.5, 13 and -1 — `TestTheFixture::test_it_is_stamped`
- Test: dash.ado's `_dash_parse_plot_opts` has `sreturn local mlabvposition`, no pending line for it, and `_dash_plot_opts_to_json`'s key list holds it — `TestTheSpecCarriesIt::test_the_parser_writes_it`
- Test: dash_parse.mata's `_dash_extract_vars` keys hold `"mlabvposition"` — `TestTheSpecCarriesIt::test_the_mata_extractor_lists_it`
- Test: `"mlabvposition" in dr._DASH_OPT_VAR_KEYS`; `_dash_option_columns({"mlabel": "lab", "mlabvposition": "pos"}) == ["lab", "pos"]`; `"pos x"`, `"a$b"`, 33 characters → no column; restricted by `columns` — `TestTheSpecCarriesIt::test_the_renderer_carries_its_column`
- Test: every option declared in `_dash_parse_plot_opts`' syntax block has `sreturn local <name>` or `sreturn local g_<name>`, or is in `test_unsupported_report_is_true.ALIASES`, or in `_ALLOW = {"xoverhangs": "P2.13", "yoverhangs": "P2.13", "mlabtextstyle": "P1.24 part 2"}`; at the base it names `mlabvposition` — `TestDeclaredOptionsReachTheSpec::test_every_declared_plot_option_has_an_s_return`
- Guard: every plain `sreturn local <name>` of the plot parser is in `_dash_plot_opts_to_json`'s key list or in `{"sort1": "read by _dash_sort_opt, never written", "bw": "folded by _dash_fold_bw"}` — `::test_every_plain_s_return_is_written`
- Guard: the same rule over `_dash_parse_graph_opts` (aliases pbgc, xla2, xsc2, xti2, yla2, ysc2, yti2) — `::test_every_declared_graph_option_has_an_s_return`
- Guard: each `_ALLOW` name is still declared and still lacks an `s()` (the list shrinks when one is fixed) — `::test_the_allowlist_is_live`
- Test: `_dash_mlabvpos_name`: `"pos"`, `" pos "`, `"ü"` → itself; `""`, `None`, `"pos x"`, `"1p"`, `"<b>"`, `"a$b"`, 33 characters, `{"mlabvposition": 5}` → `""` — `TestTheName::test_one_stata_name_or_nothing`
- Test: `_mlabel_vpos_columns` on a source with `pos = [0..12, nan, 3.5, 13, -1, nan]`, fallback 3 and 9, distance 10: per row the align, baseline and offset equal `_MLABEL_CLOCK[k]` × 10 with k the clock of BR-37.2; one note naming `3.5, 13, -1` — `TestThePerRowColumns::test_every_clock_and_the_fallbacks`
- Test: distance 10 vs 15 (gap 5): every k ≠ 0 row moves 5 px along its own unit vector; k = 0 rows stay (0, 0) — `::test_the_gap_runs_along_each_rows_direction`
- Test: a string column → None and no note — `::test_a_string_column_is_the_fallback_silently`
- Test: a `%td` column holding datetimes of days 0..12 → clocks 0..12 — `::test_a_date_column_is_read_in_stata_units`
- Test: 25 distinct bad values → one note, ten values then `and 15 more`, at most 80 printable characters of name — `::test_out_of_range_values_get_one_capped_note`
- Test: two layers on one source with `mlabposition(9)`/`mlabgap(5)` and without get distinct column sets; `mlabel(pos_vpx)` beside `mlabvposition(pos)` shares no column name — `::test_names_are_keyed_by_fallback_and_distance`
- Test (both modes, fixture): A, C, G, K3, E2, DT, BY (each panel), MY2 (both series): dash's per-row clocks equal the fixture's — `TestTheSavedAndServedPages::test_case[<probe>-saved|<probe>-served]`
- Test (both modes, fixture): connected, bar, dot, dropline, pcscatter, pccapsym, pcarrow, pcbarrow — `TestEveryLabellingType::test_type[<type>-saved|<type>-served]`
- Test (both modes): dropline with the position variable named `x`, `y`, `y0`; pcscatter with `x`, `y`: the clocks are the variable's — `TestEveryLabellingType::test_a_variable_named_like_a_derived_column[<case>]`
- Test (both modes): scatter with `if_expr`, `in_expr` and a linked `by()`: each drawn row keeps its clock — `TestEveryLabellingType::test_a_view_keeps_the_rows_clocks[<case>]`
- Test (both modes): RSQ is drawn with every label `right`, as the fixture's anchors — `TestEveryLabellingType::test_the_range_quirk_is_drawn_per_row`
- Guard (both modes): SI draws as without the option — `TestTheImmediateTypes::test_scatteri_ignores_it`
- Guard: no `mlabel()` → no LabelSet and no `__dash_mlabvpos_` column — `TestNoLabelNoColumns::test_without_mlabel_nothing_is_added`
- Test (node): the saved page of `plot_for("scatter", {"mlabel": "rep", "mlabvposition": "rep"})` and of `plot_for("dropline", {...})` after each `_MOVES` move equals `_saved_of_rows` of the kept rows, per-row fields included, and each kept row's clock is the one its `rep` value gives (red at the base, where every row is at 3) — `TestAfterAFilterMove::test_saved_move_keeps_each_rows_clock[<type>-<move>]`
- Test: served, a linked scatter, an unlinked scatter and a pcarrow layer with `mlabvposition`: after `_served_move`, each kept row's clock equals the fixture-style expectation from its own value — `TestAfterAFilterMove::test_served_moves[linked|unlinked|pcarrow]`
- Test: the same `pos` column with data scaled by 1000 and the axes swapped (`scatter x y`) gives identical offset columns — `TestOffsetsArePhysical::test_offsets_do_not_depend_on_the_data`
- Test: the generated app, executed, defines `_dash_mlabvpos_name` and `GlyphMapper._MLABVPOS_VALUES` — `TestTheServedCopy::test_the_app_defines_the_names`
- Test: dash.sthlp's Marker Label Options holds `{cmdab:mlabv:position(}` and the Unsupported section no longer names `mlabvposition` — `TestTheHelp::test_the_help_documents_it`
- Guard: the CSV metadata of a page with `mlabvposition` lists no `__dash_mlabvpos_` column — `TestTheCsv::test_no_derived_column_is_exported`
- Test (cscript): MV-01..MV-11 in `test/test_twoway_option_parity.cscript`; MV-20..MV-24 in `test/test_wp30_truth.cscript`.
- Shared harness (not a new test): `test/test_mode_parity.py::_annotations` records, for a LabelSet, `x_offset`, `y_offset`, `text_align` and `text_baseline` resolved per row when they are fields (the column's values from `r.source`, numbers through `_num`), so every parity and saved-move comparison sees per-row positions; two CORPUS cases: `_case("Per-row label clocks (WP-30 P1.24)", [_sc(mlabel="rep", mlabvposition="rep"), plot_for("dropline", {"mlabel": "rep", "mlabvposition": "foreign"})])` and `_case("Per-row clocks on pc types (WP-30 P1.24)", [plot_for("pcscatter", {"mlabel": "rep", "mlabvposition": "rep"}), plot_for("pcarrow", {"mlabel": "rep", "mlabvposition": "rep"})])`; `test/test_saved_filter_layers.py` `_CORPUS` gains `_case("a scatter labelled at per-row clocks, dropdown", _MOVES[0], [plot_for("scatter", {"mlabel": "rep", "mlabvposition": "rep"})])` and the same for pcscatter with `_MOVES[1]`.

### Commit 2 regression tests, new `test/test_mlabtextstyle.py` (red on the commit-1 tree unless marked guard; 37-11, 37-12)

`_FIX = json.load(test/fixtures/mlabtextstyle_truth.json)`; `_ratio(fig)` = the label's font size over the same scheme's default label size, both through `OptionTranslator.css_to_pt`.

- Test: the fixture is stamped, holds the four schemes and `_meta.table` has 37 names — `TestTheFixture::test_it_is_stamped`, `::test_the_table_has_the_37_shipped_names`
- Test: `dr.SchemeParser._TEXTBOX_STYLES` equals the fixture's table less the three `p#` families — `TestTheTable::test_it_is_the_fixtures_table`
- Test: for each scheme and each fixed name, `textbox_style(name)` resolves, and its size over the default `p1` label size equals the fixture's ratio within 1 %, its colour the fixture's fill — `TestTheTable::test_every_name_resolves[<scheme>-<name>]`
- Guard: `_NOTE_TEXTBOXES`' 14 names have `_TEXTBOX_STYLES`' size and colour keys — `TestTheTable::test_the_note_table_agrees`
- Test: `Heading`, `p0`, `p16`, `p3x`, `../heading`, 10,000 characters, `None` → None, within 0.1 s — `TestTheTable::test_case_and_range_are_twoways`
- Test: `SchemeParser.fallback().textbox_style(n)` equals dash-s2color's for every name — `TestTheTable::test_the_fallback_resolves_as_s2color`
- Test (both modes, fixture): every probe of every scheme: ratio within 1 % and colour equal, per series — `TestTheLabels::test_style[<scheme>-<probe>-saved|served]`
- Test (both modes): HV = VH and HR = RH, as the fixture — `TestTheLabels::test_size_and_colour_win_in_either_order`
- Test (both modes): H2 is twice heading — `TestTheLabels::test_a_relative_size_scales_the_style`
- Test (both modes): `nosuch`, `Heading`, `p16`: one note `mlabtextstyle(<name>) is not a recognised text style; using the body text style.` and body's size and colour — `TestTheLabels::test_an_unknown_name_is_noted_and_drawn_body[<name>]`
- Test (both modes): L2, L1, LD per series as the fixture — `TestTheLabels::test_per_y_list[L2|L1|LD]`
- Test: dash.ado declares `MLABTextstyle(string asis)`, `_dash_stylelist_keys()` lists it, `sreturn local mlabtextstyle` exists, the JSON key list holds it, no pending line; `TestDeclaredOptionsReachTheSpec._ALLOW` no longer holds it — `TestTheSpecCarriesIt::test_the_parser_writes_one_element_per_series`
- Test: saved (node) and served moves keep each label's size and colour — `TestAfterAFilterMove::test_style_survives[saved|served]`
- Test: every shipped `dash-*.scheme` carries `gsize`/`color` for each table key its StataCorp chain sets (the fixture's `scheme_truth.json` properties) — `TestTheSchemeFiles::test_every_scheme_carries_the_textbox_keys`
- Test: dash.sthlp holds `{cmdab:mlabt:extstyle(}` and no Unsupported entry for it — `TestTheHelp::test_the_help_documents_it`
- Test (cscript): MV-12, MV-13; MV-25..MV-27.
- Shared: `test/test_mode_parity.py` CORPUS `_case("Label text styles, per y (WP-30 P1.24)", [_sc(mlabel="rep", mlabtextstyle="heading"), plot_for("dropline", {"mlabel": "rep", "mlabtextstyle": "p3"})], bo={"scheme": "stcolor"})`.

### Pinned tests to flip (R9; re-measured, never trusted)

Commit 1 (37-07, 37-08): `test_unsupported_report_is_true.py` PLOT_VALUES `mlabvposition` → `LIVE_VALUES` (`({**_ML, "mlabvposition": "rep78"}, {**_ML, "mlabvposition": "foreign"}, "scatter", {})`) and the pending count −1; `test_help_conformance.py` `test_the_ignored_list_was_found`/`test_the_unsupported_section_was_found` −1; HC8-02 (`mlabvposition` from `p_names` to a new `p_honoured` list asserted not named, counts in comments); TP-06's `mlabv(pos)` row → a TP-06h table (honoured: rc = twoway's, not named, `_ztp_hasval zqtp mlabvposition pos`) run by a loop directly after TP-06's; TP-13a's `c2v` expects 0 and `_ztp_hasval zqtp mlabvposition pos`.
Commit 2 (37-16 to 37-18): the same moves for `mlabtextstyle` (LIVE_VALUES `({**_ML, "mlabtextstyle": "heading"}, {**_ML, "mlabtextstyle": "body"}, "scatter", {})`; TP-06h row `mlabt(heading)`; `c2t`); `test_stylelists.py` `_STYLE_KEYS` gains and `_NOT_YET` loses `mlabtextstyle`; SL-01's word count +1; `test_80_to_140_directives`' bounds re-derived.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Spec, Mata, column table | pytest `TestTheSpecCarriesIt` (text); cscript MV-08, MV-20 | dash.ado, dash_parse.mata | n/a |
| Declared options guard | pytest `TestDeclaredOptionsReachTheSpec` | dash.ado | n/a |
| Refusals and words | cscript MV-01..MV-11 against live twoway | sysuse auto | n/a |
| Per-row clocks | pytest `TestThePerRowColumns`, `TestTheSavedAndServedPages`, `TestEveryLabellingType`; cscript MV-21..MV-24 | `mlabvpos_truth.json` | yes |
| After filter moves | pytest `TestAfterAFilterMove` (node saved; served linked, unlinked, pcarrow); `test_saved_filter_layers.py` corpus | `_DF` | yes |
| Physical offsets | pytest `TestOffsetsArePhysical` | literal | n/a |
| Text styles | pytest `TestTheTable`, `TestTheLabels`, `TestTheSchemeFiles`; cscript MV-12, MV-13, MV-25..MV-27 | `mlabtextstyle_truth.json`, `scheme_truth.json` | yes |
| Parity | `test_mode_parity.py` three CORPUS cases, `_annotations` per row | `_DF` | yes |
| Served wiring | `TestTheServedCopy`; G4 guards | generated app | served |
| Help | `TestTheHelp` ×2, `test_help_conformance.py`, `test_help_claims_8.py` | dash.sthlp | n/a |
| Registries, tracking | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_cscript_hygiene.py`, `test_tracking_documents.py`, `test_fixtures_are_committed.py` | — | n/a |

**Acceptance criteria.**
- **AC-37.1** (BR-37.1, BR-37.2, BR-37.3) `TestTheSavedAndServedPages` and `TestEveryLabellingType` pass for every fixture probe in both modes; `TestThePerRowColumns` passes; MV-21..MV-24 PASS.
- **AC-37.2** (BR-37.4, BR-37.5) MV-01..MV-11 PASS against live twoway (rc and first error line); `test_scatteri_ignores_it` passes; neither option appears in any "ignoring unsupported option(s)" note of the suite's runs.
- **AC-37.3** (BR-37.6) `TestAfterAFilterMove` (both commits) and the saved-move corpus pass, the node tests not skipped; `test_mode_parity.py` passes with the new cases and an untouched `ALLOWED`/`_MUST_WARN`.
- **AC-37.4** (BR-37.7) `TestTheTable`, `TestTheLabels` and `TestTheSchemeFiles` pass for all four schemes (or, only under TR-37.18's strike form, with its `_NOT_YET` table and passing guard); MV-12, MV-13, MV-25..MV-27 PASS.
- **AC-37.5** (BR-37.8) `TestOffsetsArePhysical` passes.
- **AC-37.6** (BR-37.9) `TestDeclaredOptionsReachTheSpec` passes with `_ALLOW` holding only `xoverhangs` and `yoverhangs` after commit 2.
- **AC-37.7** Every flipped node passes with its new expectation and a `Flipped:` line; no test is deleted; the full suite through the queue reports 0 failed before each commit; G7 prints 0 twice per commit.

## Tasks

**Commit boundary.** Tasks 37-01 to 37-10 form commit 1, made by 37-10 on `wp30-s37` with the subject `Place each marker label at its row's clock position, part 1 of 2: mlabvposition() (WP-30 P1.24)`; it leaves the BUGS.md entry, its `WP30_OPEN` key and both markers in place (A156). Tasks 37-11 to 37-20 form commit 2, made by 37-20 with the subject `Draw marker labels in the scheme's text box styles, part 2 of 2: mlabtextstyle() (WP-30 P1.24)`; it closes all three. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s37`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`; every command uses `git -C "$WT"` or `$WT` paths. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S37 "$SLOT" "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`).

<task type="auto" id="37-01">
  <name>Write the position fixture and tests</name>
  <files>scripts/extract_mlabvpos_truth.do, test/test_mlabvposition.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-13-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s37`; stop otherwise. Create `scripts/extract_mlabvpos_truth.do` exactly as "Stata truth" describes (S02's stanza, the data, the 143 references, the probes, the per-probe named logs, the python reader through `scripts/svg_truth.py`, S19's `_meta` form) and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_mlabvpos_truth.do"`; it writes `test/fixtures/mlabvpos_truth.json`. Create `test/test_mlabvposition.py` with every commit-1 stub of "TDD test stubs"; name new symbols as `dr._dash_mlabvpos_name`, `dr.GlyphMapper._mlabel_vpos_columns` and `dr.GlyphMapper._MLABVPOS_VALUES`, so they fail with AttributeError now. In `test/test_mode_parity.py` extend `_annotations`' LabelSet branch (per-row fields, `text_align`, `text_baseline`) and append the two commit-1 CORPUS cases before `CORPUS`'s closing bracket (:1798 at c96facd, after any earlier section's cases). Run `python3 -m pytest test/test_mlabvposition.py -q -n 6 -p no:cacheprovider -rf > "$S/37-new-1.log" 2>&1` and `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider -k "WP-30 P1.24" -rf >> "$S/37-new-1.log" 2>&1`. Write `$S/37-P1.24-1-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)" with the guard nodes. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/mlabvpos_truth.json')); m=d['_meta']; a=d['probes']['A']['clock']; print(m['scheme'], all(k in m for k in ('stata_version','born_date','dash_commit','extracted')), [a['R%d'%i] for i in (1,13,14,15,18)])"` prints `stcolor True [0, 12, 3, 12, 3]`; `grep -c FAILED "$S/37-new-1.log"` is at least 25; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata dash_render.py` prints nothing.]]></verify>
  <done>The twoway position fixture existed and every commit-1 pytest regression test was shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="37-02">
  <name>Write the refusal, truth and move cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_wp30_truth.cscript, test/test_saved_filter_layers.py</files>
  <action><![CDATA[
    In `test/test_twoway_option_parity.cscript`, after AX-08's block (its last line `set linesize `saved_ls'`, :2902 at c96facd) and before the `// Summary` divider (:2904), add one contiguous run headed `// MV: mlabvposition(), read as twoway reads it (WP-30 P1.24)` with its data lines and MV-01..MV-11 of "Stata truth", each comparing live twoway's rc and first error line with dash's in the script's `nfail`/`faillist` form. In `test/test_wp30_truth.cscript` put the `_s37_*` helpers directly above S01's `* ==== S37 P1.24: …` header and MV-20..MV-24 between S01's S37 start and end lines. Append the two `_CORPUS` cases of "TDD test stubs" to `test/test_saved_filter_layers.py` after its last labelled case (guards at the base). Run both scripts through the driver and `test_saved_filter_layers.py -k "per-row"` on the unmodified shipped files. Append to `$S/37-P1.24-1-failure.txt` every `MV-nn FAIL` line with the twoway line it quotes, and list the saved-move cases under the guards. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "MV-(0[1-8]|10) FAIL" "$S/run_test_twoway_option_parity.log"` is at least 7 (MV-09 and MV-11 may pass as guards); `grep -cE "MV-2[0-4] FAIL" "$S/run_test_wp30_truth.log"` is at least 4; `grep -c "AX-08 PASS" "$S/run_test_twoway_option_parity.log"` prints 1.]]></verify>
  <done>The refusal cases, the live twoway comparisons and the saved-move cases were in place, the first two shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="37-03">
  <name>Serialise and fold mlabvposition in Stata</name>
  <files>dash.ado, dash_parse.mata</files>
  <action><![CDATA[
    `_dash_parse_plot_opts`, `_dash_plot_opts_to_json`, `_dash_process_segment` and `_dash_extract_vars` are UNKNOWN to the index; their callers were confirmed by grep (Risk). Apply TR-37.1 (the `sreturn` after `mlabformat`'s, the JSON key after `mlabformat`, the pending line :1079 deleted and the comment :1075-1077 reworded), TR-37.2 (`_dash_mlabv_parse`), TR-37.3 (`_dash_fold_mlabv` after `_dash_fold_mlab`'s `end`, each new program with a header comment and `version 19`), TR-37.4 (the call directly before `_dash_fold_bw "`ptype'"`) and TR-37.5 (the Mata key and comment). Edit no other program, and neither `_dash_fold_mlab` nor `_dash_fold_bw`.
  ]]></action>
  <verify><![CDATA[`test_twoway_option_parity.cscript` through the driver prints `MV-01 PASS` to `MV-11 PASS`, and its only FAIL lines are TP-06's and TP-13a's naming `mlabvposition()` (flipped by 37-08); `python3 -m pytest test/test_mlabvposition.py -q -n0 -p no:cacheprovider -k "TestTheSpecCarriesIt and not renderer"` passes.]]></verify>
  <done>dash.ado wrote mlabvposition into the spec and refused it where and as twoway refuses it, and Mata carried its variable into the data.</done>
</task>

<task type="auto" id="37-04">
  <name>Carry the column and serve the name</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_option_columns` is CRITICAL (15 impacted, 13 processes) and `_glyph_layer_lines` HIGH (4 impacted). Apply TR-37.6 (`_dash_mlabvpos_name` directly after `_dash_mlabel_names`; `"mlabvposition"` after `"mlabel"` in `_DASH_OPT_VAR_KEYS`, its comment extended; the `elif` branch of `_dash_option_columns` and its docstring) and, in the same edit, TR-37.10 (`"_dash_mlabvpos_name",` on a new line directly after `"_dash_mlabel_names", "_dash_option_columns",`, :33356 at c96facd): the served app calls `_dash_option_columns` for every layer, so the name must travel with the branch. Do not edit `_generate_app_source`. Run every test file that names `_dash_option_columns` (`grep -l _dash_option_columns test/*.py`) and `test_embedded_rows.py` with `-n 6`; a failure stops the task.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mlabvposition.py -q -n0 -p no:cacheprovider -k "TestTheName or renderer_carries"` passes; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider` passes; the files of the action report 0 failed.]]></verify>
  <done>The column tables of both modes named the position variable, refused anything that is not one Stata name, and the served app defined the helper.</done>
</task>

<task type="auto" id="37-05">
  <name>Compute per-row clocks and offsets</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_apply_mlabel_opts` is CRITICAL (16 impacted, 10 direct) and that S37 is batch 13's only editor of it (R12). Apply TR-37.7 (`GlyphMapper._MLABVPOS_VALUES` beside `_MLABEL_CLOCK`; `_mlabel_vpos_columns` directly after `_mlabel_gap_px`, with a docstring citing E9's rules and the shared-source reason for the names) and TR-37.8 (the `vpos_col` keyword after S08's `radius_px`, the call after the scalar position block using S08's distance, `field()` specs, the docstring). Add no type gate and do not edit `_immediate_labels`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mlabvposition.py -q -n 6 -p no:cacheprovider -k "TestThePerRowColumns or TestTheSavedAndServedPages or TestNoLabelNoColumns or TestTheImmediateTypes or TestOffsetsArePhysical or TestTheServedCopy"` passes; `python3 -m pytest test/test_marker_label_parity.py test/test_glyphs.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Each labelled row drew at its own clock in both modes, keyed so that layers sharing a source kept their own fallbacks and gaps.</done>
</task>

<task type="auto" id="37-06">
  <name>Keep stacked sources from shadowing positions</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    `map_dropline` and `map_pcscatter` are UNKNOWN to the index (dispatch dict, `_dash_glyph_dispatch` :28501, confirmed by grep). Apply TR-37.9: carry the variable's values under `self._MLABVPOS_VALUES` in `_dl_cols` before `_carry_cols` and in `clean`/`_pc_cols` beside `_DASH_MLABEL_VALUES` (stacked as the labels are, datetime columns kept as arrays), and pass `vpos_col=self._MLABVPOS_VALUES` at both `_apply_mlabel_opts` calls. Edit no other mapper; if `test_type[bar-saved]` fails at this point, carry the column in map_bar's frame the same way and record why in `$S/37-notes.txt` for the commit body.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mlabvposition.py -q -n 6 -p no:cacheprovider -k "TestEveryLabellingType or TestAfterAFilterMove"` passes, the `x`, `y` and `y0` variants included and the node tests not skipped; `python3 -m pytest test/test_saved_filter_layers.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every labelling type read the position variable itself, even when named like a column the mapper derives, and every row kept its clock after saved and served moves.</done>
</task>

<task type="auto" id="37-07">
  <name>Flip the pinned pending-list counts</name>
  <files>test/test_unsupported_report_is_true.py, test/test_help_conformance.py, test/test_help_claims_8.cscript</files>
  <action><![CDATA[
    Re-measure E10's commit-1 pins on this tree, then flip them in place, each with a comment "Flipped (WP-30 P1.24): <old> was wrong because twoway draws mlabvposition() per row (mlabvpos_truth.json A)": move `"mlabvposition"` from `PLOT_VALUES` to `LIVE_VALUES` (alphabetical place, the values of "Pinned tests to flip"); set the plot pending count (`test_the_blocks_were_actually_found`) and `test_help_conformance.py`'s two counts (:598, :604) to the measured values, each with `# <old> -> <new>: P1.24 mlabvposition() honoured` (R10); in HC8-02 move `mlabvposition` from `p_names` to a new `p_honoured` list checked not named, and correct the counts in its comments and done text. Write one `Flipped:` line per node to `$S/37-flips-1.txt`, and one "Left the parametrisation" line each for `test_a_plot_option_reported_unsupported_really_is[mlabvposition]` and `TestAnUnsupportedOptionIsInertWhenServed::test_plot_level[mlabvposition]`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unsupported_report_is_true.py test/test_help_conformance.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` reports 0 failed except `test_every_listed_option_is_still_listed` and `TestTheUnsupportedSectionIsTrue` (fixed by 37-09); `test_help_claims_8.cscript` through the driver prints `HC8-02 PASS`.]]></verify>
  <done>Every count and case that pinned mlabvposition() as ignored asserted it honoured, with the reason recorded.</done>
</task>

<task type="auto" id="37-08">
  <name>Flip the parity rows and register</name>
  <files>test/test_twoway_option_parity.cscript, test/function_test_map.py, test/program_coverage_map.py</files>
  <action><![CDATA[
    In `test/test_twoway_option_parity.cscript` turn TP-06's `mlabv(pos)` row into the first row of a TP-06h honoured table (rc equal to twoway's, not named in the note, `_ztp_hasval zqtp mlabvposition pos`) run by a new loop directly after TP-06's loop; flip TP-13a's `c2v` to expect 0 and add `_ztp_hasval zqtp mlabvposition pos`; update the header comment :48. Append the `Flipped:` lines to `$S/37-flips-1.txt`. Add TR-37.12's two `FUNCTIONS` entries under the `# WP-30 S37 (P1.24): …` anchor of `test/function_test_map.py` and its two `COVERAGE["dash.ado"]` entries under S37's anchor of `test/program_coverage_map.py`, alphabetically. Delete no test.
  ]]></action>
  <verify><![CDATA[`test_twoway_option_parity.cscript` through the driver prints `TP-06h PASS`, no `TP-13a FAIL`, and `test_twoway_option_parity: ALL CHECKS PASSED`; `python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The parity rows asserted mlabvposition() honoured, and the new function, method and programs were mapped to the tests that run them.</done>
</task>

<task type="auto" id="37-09">
  <name>Document per-row positions in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-37.13: the `mlabv:position(` synopt entry after `mlabp:osition(`'s, the paragraph in "Where labels are drawn", and the Unsupported entry reduced to `mlabtextstyle()` under the heading "Marker-label text style". Find each place by its text (earlier batches may have moved the lines). Edit no other paragraph (R3); every new or changed line is at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_mlabvposition.py::TestTheHelp" test/test_help_conformance.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` reports 0 failed; `awk 'length > 79' "$WT/dash.sthlp" | grep -c "mlabvposition"` prints 0.]]></verify>
  <done>The help documented mlabvposition() with twoway's rules and the Unsupported section named only mlabtextstyle().</done>
</task>

<task type="auto" id="37-10">
  <name>Run the suite and make commit 1</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_mlabvposition.py`, `test_mode_parity.py`, `test_saved_filter_layers.py`, `test_cscript_hygiene.py`, `test_fixtures_are_committed.py` and `test_tracking_documents.py` with `-n 6`, and `test_twoway_option_parity.cscript`, `test_help_claims_8.cscript` and the S37 truth block through the driver. Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run `"$S/full_suite_queue.sh" "$WT" "$S/37-full-1.log"` in the background, waiting for its `exit=` line and reading the log, never relaunching it (E6 for the known flaky tests). Stage exactly dash.ado dash_parse.mata dash_render.py dash.sthlp scripts/extract_mlabvpos_truth.do test/test_mlabvposition.py test/test_mode_parity.py test/test_wp30_truth.cscript test/test_twoway_option_parity.cscript test/test_saved_filter_layers.py test/test_unsupported_report_is_true.py test/test_help_conformance.py test/test_help_claims_8.cscript test/function_test_map.py test/program_coverage_map.py, and `git add -f test/fixtures/mlabvpos_truth.json`; check `git -C "$WT" diff --cached --name-only` lists those 16 only (G6). Write `$S/37-message-1.txt` in the form of "Notes: commit messages", check G7, confirm the branch, commit, and check G7 on the committed message.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/37-full-1.log"` shows 0 failed and `exit=0`; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.24)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.24 -->' "$WT/CHANGELOG.md"` prints 2 (left for commit 2).]]></verify>
  <done>Commit 1 drew mlabvposition() per row in both modes and refused it as twoway does, green, with the entry, key and markers left for commit 2.</done>
</task>

<task type="auto" id="37-11">
  <name>Write the text-style fixture and tests</name>
  <files>scripts/extract_mlabtextstyle_truth.do, test/test_mlabtextstyle.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    On the tree commit 1 left, create `scripts/extract_mlabtextstyle_truth.do` as "Stata truth" describes (the style-file table with TR-37.20's guards, four schemes, the probes, per-series size and fill, notes) and run it with `DASH_REPO="$WT"` through the slot; it writes `test/fixtures/mlabtextstyle_truth.json`. Create `test/test_mlabtextstyle.py` with every commit-2 stub, naming `dr.SchemeParser._TEXTBOX_STYLES` and `textbox_style`. Append the commit-2 CORPUS case to `test/test_mode_parity.py`. Run the new tests with `-n 6 -rf` into `$S/37-new-2.log`. Write `$S/37-P1.24-2-failure.txt`: the commit-1 sha, one line per failing node, then the guards that pass. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/mlabtextstyle_truth.json')); print(len(d['_meta']['table']), sorted(d['schemes']))"` prints `37 ['economist', 's1rcolor', 's2color', 'stcolor']`; `grep -c FAILED "$S/37-new-2.log"` is at least 40; `git -C "$WT" diff --name-only -- dash.ado dash_render.py dash-stcolor.scheme` prints nothing.]]></verify>
  <done>The twoway text-style fixture with Stata's 37-name table existed and every commit-2 pytest regression test was shown failing on the tree commit 1 left.</done>
</task>

<task type="auto" id="37-12">
  <name>Write the text-style script cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Add MV-12 and MV-13 of "Stata truth" to the end of S37's run in `test_twoway_option_parity.cscript` (before `// Summary`), and the second S37 block `* ==== S37 P1.24: mlabtextstyle() ====` directly below the first S37 block's end line in `test_wp30_truth.cscript`, in section-01's stub form exactly (`local only : env WP30_ONLY`, `` if inlist("`only'", "", "S37") { ``, its own `S37 start`/`S37 end` display lines as the first and last statements, MV-25..MV-27 between them, `* ==== end S37 ====`). Run both scripts through the driver on the tree commit 1 left. Append the MV FAIL lines and the twoway lines they quote to `$S/37-P1.24-2-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "MV-1[23] FAIL" "$S/run_test_twoway_option_parity.log"` is at least 1; `grep -cE "MV-2[5-7] FAIL" "$S/run_test_wp30_truth.log"` is at least 2; `grep -cE "MV-2[0-4] PASS" "$S/run_test_wp30_truth.log"` prints 5.]]></verify>
  <done>The text-style cases were in their scripts and shown failing on the tree commit 1 left, with commit 1's cases still passing.</done>
</task>

<task type="auto" id="37-13">
  <name>Make mlabtextstyle a serialised style list</name>
  <files>dash.ado, dash_parse.mata</files>
  <action><![CDATA[
    Apply TR-37.14: `MLABTextstyle(string asis)`; `mlabtextstyle` appended to `_dash_stylelist_keys()`'s list and removed from its "who adds later" comment; the `sreturn` after `mlabvposition`'s; the JSON key after `mlabvposition`; the pending line :1078 and its comment deleted. `_dash_stylelist_keys` is UNKNOWN to the index; its callers are S11's (`grep -n _dash_stylelist_keys dash.ado`). Edit nothing else.
  ]]></action>
  <verify><![CDATA[`test_twoway_option_parity.cscript` through the driver prints `MV-12 PASS` and `MV-13 PASS`; `python3 -m pytest test/test_mlabtextstyle.py -q -n0 -p no:cacheprovider -k TestTheSpecCarriesIt` passes except its `_ALLOW` clause (37-17).]]></verify>
  <done>dash.ado wrote one mlabtextstyle() element per series and kept twoway's rightmost copy.</done>
</task>

<task type="auto" id="37-14">
  <name>Transcribe the textbox keys and regenerate</name>
  <files>scripts/extract_scheme_truth.py</files>
  <action><![CDATA[
    Q-37.1 is resolved (Notes): run this task unless an orchestrator amendment committed on `wp30-p1` before `batch-13-base` strikes S37 from A152, in which case skip it and apply TR-37.18's strike form in 37-15. Apply TR-37.18: the resolver properties and the one emitted group for the text box keys the generated files lack. Copy `test/fixtures/scheme_truth.json` and the 26 `dash-*.scheme` files to `$S/37-schemes-old/`, run the extractor as its header says (it rewrites the 26 files and the fixture), and compare with a scratch script `$S/37-cmp.py`: every pre-existing property and directive of every scheme must be unchanged; only the new keys may be added. Save the comparison to `$S/37-schemes-cmp.txt`. Never patch a generated file by hand (R7).
  ]]></action>
  <verify><![CDATA[`tail -1 "$S/37-schemes-cmp.txt"` reads `unchanged: 26 schemes; added keys only`; `grep -c "^gsize matrix_label" "$WT/dash-economist.scheme"` prints 1; `python3 -m pytest test/test_scheme_fidelity.py test/test_scheme_fallback_provenance.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every shipped scheme carried the text box keys its StataCorp chain sets, regenerated by the extractor and verified probe by probe.</done>
</task>

<task type="auto" id="37-15">
  <name>Resolve text styles from the scheme</name>
  <files>dash_render.py, test/test_mlabtextstyle.py</files>
  <action><![CDATA[
    Warn in the task log that `_apply_mlabel_opts` is CRITICAL. Apply TR-37.15 (`_TEXTBOX_STYLES` from the fixture's table, `textbox_style`, the `_FALLBACK_PROPS` keys with s2color's values) and TR-37.16 (the style block after S33's defaults and before `mlabcolor`/`mlabsize`). Read S33's per-index default names on this tree (`grep -n "p_label_sizes\|p_label_colors" dash_render.py`); if S33 named them otherwise, use its names. If 37-14 was skipped, add to `test/test_mlabtextstyle.py` TR-37.18's `_NOT_YET` table (measured on this tree) and its guard; otherwise leave that file alone.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mlabtextstyle.py -q -n 6 -p no:cacheprovider` passes except `TestTheHelp` and the `_ALLOW` clause; `python3 -m pytest test/test_scheme_consumption.py test/test_scheme_fallback_provenance.py test/test_marker_label_parity.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed; the S37 blocks through the driver print `MV-25 PASS` to `MV-27 PASS`.]]></verify>
  <done>Marker labels took any of Stata's 37 text box styles from the scheme in both modes, explicit size and colour winning and unknown names noted and drawn in body.</done>
</task>

<task type="auto" id="37-16">
  <name>Flip the text-style pending counts</name>
  <files>test/test_unsupported_report_is_true.py, test/test_help_conformance.py, test/test_help_claims_8.cscript</files>
  <action><![CDATA[
    Re-measure and flip, as 37-07 did, for `mlabtextstyle`: `PLOT_VALUES` → `LIVE_VALUES` (the values of "Pinned tests to flip"), the pending counts in both pytest files (R10 comment form), HC8-02's `p_names` → `p_honoured` and its counts. Append the `Flipped:` and "Left the parametrisation" lines to `$S/37-flips-2.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unsupported_report_is_true.py test/test_help_conformance.py -q -n 6 -p no:cacheprovider` reports 0 failed except the Unsupported-section checks fixed by 37-19; `test_help_claims_8.cscript` through the driver prints `HC8-02 PASS`.]]></verify>
  <done>Every count and case that pinned mlabtextstyle() as ignored asserted it drawn, with the reason recorded.</done>
</task>

<task type="auto" id="37-17">
  <name>Flip parity rows and the guard allowlist</name>
  <files>test/test_twoway_option_parity.cscript, test/test_mlabvposition.py, test/test_stylelists.py</files>
  <action><![CDATA[
    Turn TP-06's `mlabt(heading)` row into TP-06h's second row and flip TP-13a's `c2t` (expect 0, `_ztp_hasval zqtp mlabtextstyle heading`). Remove `"mlabtextstyle"` from `_ALLOW` in `test/test_mlabvposition.py` with a comment that part 2 serialised it. In `test/test_stylelists.py` add `mlabtextstyle` to `_STYLE_KEYS` (or the extension list S20/S32 left) and remove it from `_NOT_YET`. Append the `Flipped:` lines to `$S/37-flips-2.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`test_twoway_option_parity.cscript` through the driver prints `test_twoway_option_parity: ALL CHECKS PASSED`; `python3 -m pytest test/test_mlabvposition.py test/test_stylelists.py -q -n 6 -p no:cacheprovider` reports 0 failed except `test_mlabvposition.py::TestTheHelp` if the Unsupported entry is still present (37-19).]]></verify>
  <done>The parity rows, the style-list pins and the declared-option guard held mlabtextstyle() as a serialised style list.</done>
</task>

<task type="auto" id="37-18">
  <name>Move the key-count and directive pins</name>
  <files>test/test_varlist_expansion.cscript, test/test_help_claims_8.py, test/function_test_map.py</files>
  <action><![CDATA[
    In `test/test_varlist_expansion.cscript` raise SL-01's key count by one, in S20's and S32's form. If 37-14 ran, re-derive `TestTheShippedFiles::test_80_to_140_directives`' bounds from the regenerated files (the minimum and maximum directive counts over the 26) and write them with `# <old> -> <new>: P1.24 textbox keys` (R10); otherwise leave the pin. Add TR-37.19's `FUNCTIONS` entry under S37's anchor of `test/function_test_map.py`. Append the `Flipped:` lines to `$S/37-flips-2.txt`.
  ]]></action>
  <verify><![CDATA[`test_varlist_expansion.cscript` through the driver prints `SL-01 PASS`; `python3 -m pytest test/test_help_claims_8.py test/test_function_test_map.py -q -n 6 -p no:cacheprovider` reports 0 failed except the help-sentence check 37-19 fixes.]]></verify>
  <done>The key-count, directive-count and map pins held the new key list and the regenerated files.</done>
</task>

<task type="auto" id="37-19">
  <name>Document text styles in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-37.19's help: the `mlabt:extstyle(` synopt entry after `mlabv:position(`'s; the Unsupported entry removed whole; and, only if 37-14 ran, the directive count of "What the shipped files are" rewritten in place to 37-18's range. Find each place by its text. Every new or changed line is at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_mlabtextstyle.py::TestTheHelp" "test/test_mlabvposition.py::TestTheHelp" test/test_help_conformance.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "Marker-label text style" "$WT/dash.sthlp"` prints 0.]]></verify>
  <done>The help documented mlabtextstyle() and no longer listed either option as unsupported.</done>
</task>

<task type="auto" id="37-20">
  <name>Close the entry and make commit 2</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.24"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution", today's date as `ddmonyyyy`. Delete the `"P1.24"` key line of `WP30_OPEN`. Replace both `<!-- WP-30 P1.24 -->` markers in place with "Notes: CHANGELOG lines" (the Fixed line under `### Fixed in WP-30`, the refusals under `### Changed behaviour`). Run `test_tracking_documents.py test_cscript_hygiene.py test_fixtures_are_committed.py test_mlabtextstyle.py test_mlabvposition.py test_mode_parity.py` with `-n 6`, both S37 blocks and both area scripts through the driver; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/37-full-2.log"` in the background, read when `exit=` appears. Stage exactly the files 37-11 to 37-19 changed (written to `$S/37-files-2.txt` as each task ends) plus these three, with `git add -f test/fixtures/mlabtextstyle_truth.json` and, if 37-14 ran, `git add -f test/fixtures/scheme_truth.json`; check `git -C "$WT" diff --cached --name-only` equals that list (G6). Write `$S/37-message-2.txt`, check G7, confirm the branch, commit, check G7 again, and report both shas and messages to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/37-full-2.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.24 -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.24": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -2 --format=%s` shows both subjects ending `(WP-30 P1.24)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.24 was closed naming existing tests, its markers carried the measured old and new behaviour, and two green commits on wp30-s37 were ready for the merger.</done>
</task>

## Section completion criteria

- `mlabvposition(varname)` places every labelled row at its own clock on the nine labelling types, by twoway's value rules, in the saved page and the served app, before and after saved and served filter moves, in by() panels and under if/in (fixture probes, MV-21..MV-24).
- dash refuses it where and as twoway does (MV-01..MV-11), accepts it where twoway does, never names it in the note, and the immediate types ignore it.
- `mlabtextstyle()` draws any of the 37 shipped text box styles from the scheme, per y, with size and colour overrides in either order and unknown names noted and drawn in body, in both modes (four schemes in the fixture).
- `TestDeclaredOptionsReachTheSpec` guards both parsers with only `xoverhangs`/`yoverhangs` allowed.
- `_dash_mlabvpos_name`, `GlyphMapper._mlabel_vpos_columns`, `SchemeParser.textbox_style`, `_dash_fold_mlabv` and `_dash_mlabv_parse` exist, are mapped and (for the module function) travel to the served app.
- Both fixtures are generated by their extractors, stamped, committed with `-f` and read by tests; the 26 scheme files are regenerated by 37-14's extractor run, never hand-patched (TR-37.18's strike form only if the orchestrator struck it).
- Every pinned node is flipped with its reason; none is deleted.
- Two green commits `(WP-30 P1.24)` exist on `wp30-s37`; the second closes the entry, deletes its key and replaces both markers.

## Notes

- **Q-37.1, resolved by the review (no maintainer question).** Commit 2 regenerates the 26 scheme files and `scheme_truth.json` with the text box keys (TR-37.18) and rewrites the directive count of "What the shipped files are". M1 ("Match Stata") and register P1.24.3 (a committed table of all 37 shipped textboxstyle names) require each scheme's own sizes and colours: without the keys, `mlabtextstyle(label)` and 23 other names draw s2color's values under economist, s1rcolor, s1color, s2mono and s1manual, where twoway draws the scheme's own (E7, E9). A152's purpose (two regenerations in one batch conflict) is kept: batch 13 has no other regenerator and S38 touches no extractor, scheme file or `scheme_truth.json`, the same exception A152 grants S07. Cross-file fixes (recorded in `review-notes/g06.md` for the orchestrator): index.md A152 gains "S37 (batch 13, the S07-style exception: its partner S38 touches no generated file)"; the batch-13 subsection and diagram line note "S37 regenerates (commit 2)"; R3's "Stata scheme support" row gains "S37 (13: the directive-count sentence of What the shipped files are)"; R10's declared-plot row (:607) drops S37 (no option is declared). TR-37.18's strike form applies only if the orchestrator refuses that amendment before `batch-13-base` is recorded.
- **No type gate in the renderer** (differs from the research critic's item 9, on measurement): twoway draws per-row clocks on rscatter in the cases its count rule accepts (E9, `p4.do`: all eight labels `text-anchor="end"`), so dash.ado's count rule is the only gate.
- **`_pc_clean_with_label` is not edited** (differs from research §4a.3): pcarrow and pcbarrow carry every source column through `_carry_cols` after the frame (E6). A test pins it.
- **S08's names.** The distance S08 multiplies the unit vector by, and the `radius_px` keyword, are read at `batch-13-base`; if S08 named them differently, use its names, never re-derive the radius.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; both extractors and the truth blocks then fail or SKIP. Check the file after each slot run; a SKIP is not a pass.
- **Merge rules for the shared files.**
  - R1: MV-01..MV-13 in `test_twoway_option_parity.cscript` as one run at its end; S37's two truth blocks and their helpers in their own places.
  - R2: `"_dash_mlabvpos_name"` at S37's anchor; map entries under S37's anchors; `_DASH_OPT_VAR_KEYS` in place.
  - R3: Marker Label Options (S37's row), the Unsupported entry (pending mover) and the one directive-count sentence (Q-37.1's R3 amendment).
  - R4/R5: the two `P1.24` markers, the entry and its key, by commit 2 only.
  - R6: `version 19` in both new programs; one key added to S11's Mata function.
  - R7: two new fixtures and extractors; the scheme regeneration only by 37-14's extractor run (on a conflict the merger re-runs it).
  - R8: three CORPUS cases appended; `_annotations`' LabelSet branch extended (if S38 touches the same branch, the merger keeps both); `ALLOWED`/`_MUST_WARN` untouched.
  - R9: E10's flips. R10: the pending counts (twice), the two help-conformance counts, HC8-02's comment counts, SL-01, the directive pin; the declared count (:607) is unchanged (no declaration added).
  - R12: S37 is batch 13's only editor of `_apply_mlabel_opts`; it edits neither `_make_figure_body` nor `_generate_app_source`.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name, for commit 1, `_dash_mlabvpos_name`, `_dash_option_columns`, `GlyphMapper._apply_mlabel_opts`, `GlyphMapper._mlabel_vpos_columns`, `GlyphMapper.map_dropline`, `GlyphMapper.map_pcscatter`, `_glyph_layer_lines` and the constant; for commit 2, `SchemeParser.textbox_style`, `GlyphMapper._apply_mlabel_opts` and the extractor's symbols; plus test symbols of the staged files.
- **Commit messages.** Subjects as in "Commit boundary". Body, in order: the failure file (`$S/37-P1.24-1-failure.txt` / `-2-`); the measured defect (Overview's block); what changed and where (TR-37.1-TR-37.13 / TR-37.14-TR-37.19, both modes); then one line each: `Regression: test/test_mlabvposition.py::<Class>::<test> -- failed at <base sha> with <text>` per regression node (cscripts as `test/test_twoway_option_parity.cscript MV-01`, `test/test_wp30_truth.cscript MV-21`); the `Flipped:` lines of `$S/37-flips-<k>.txt`, e.g. `Flipped: test/test_help_claims_8.cscript HC8-02 -- mlabvposition() named in the note was wrong because dash draws it per row as twoway does`; `Fixture: test/fixtures/mlabvpos_truth.json (scripts/extract_mlabvpos_truth.do)` (commit 2: `mlabtextstyle_truth.json`, and `scheme_truth.json (scripts/extract_scheme_truth.py)`); commit 1 `BUGS.md: "<title>" (open; closed by part 2)`, commit 2 `BUGS.md: "<WP30_OPEN["P1.24"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.24). mlabvposition(varname) is serialised (dash.ado _dash_parse_plot_opts, _dash_plot_opts_to_json), checked as twoway checks it (_dash_fold_mlabv with _dash_mlabv_parse: its name rule, its variable count on the range and fit types r(103) in twoway's words, a second copy r(198), a missing variable r(111); not read on histogram, function, scatteri, pci and pcarrowi), carried into the data (Mata _dash_extract_vars) and the column tables (_DASH_OPT_VAR_KEYS, _dash_option_columns), and drawn per row through LabelSet fields (GlyphMapper._mlabel_vpos_columns: a whole number 0-12 is that clock, missing or string takes mlabposition(), anything else 12 with one note, mlabgap() along each row's direction) on scatter, connected, bar, dot, dropline, pcscatter, pccapsym, pcarrow and pcbarrow, in the saved page and the served app, before and after filter moves; mlabtextstyle() is a style list resolved from Stata's 37 text box styles on the scheme (SchemeParser.textbox_style; the 26 shipped schemes carry the keys), mlabsize() and mlabcolor() winning in either order and an unknown name noted and drawn in body; a guard test holds every declared option to the spec. Pinned by test/test_mlabvposition.py::TestTheSavedAndServedPages::test_case, test/test_mlabvposition.py::TestEveryLabellingType::test_type, test/test_mlabvposition.py::TestAfterAFilterMove::test_served_moves, test/test_mlabvposition.py::TestDeclaredOptionsReachTheSpec::test_every_declared_plot_option_has_an_s_return, test/test_mlabtextstyle.py::TestTheLabels::test_style, test/test_twoway_option_parity.cscript MV-01, test/test_wp30_truth.cscript MV-21; fixture test/fixtures/mlabvpos_truth.json, test/fixtures/mlabtextstyle_truth.json. Residual, deferred (WP-30): user-written textboxstyle files are noted as unknown (P2.55); a position variable named x or y on rscatter's stacked source is read as the coordinates (P2.28); twoway's r(102) for a range layer whose mlabel() names one of its own variables is not reproduced (filed by S58).
  ```
- **CHANGELOG lines** (each replaces its marker in place; the two `###` lines below only say which list, and are not written):

  ```
  ### Fixed in WP-30
  - `mlabvposition(varname)` and `mlabtextstyle()` are drawn, in both modes and after filter moves: `dash scatter y x, mlabel(lab) mlabvposition(pos)` drew every label at 3 o'clock and named the option in the note, and now draws each row at the clock its value gives (a whole number 0-12; missing values and string variables at `mlabposition()`, else 3; any other number at 12 with a note), with `mlabgap()` along each row's direction; `mlabtextstyle(heading)` was named in the note and drawn in the marker-label default, and now draws the scheme's heading (under stcolor 1.75 times the default label size, black where the default is p1's blue), any of Stata's 37 text box styles, one per y as a style list. (WP-30, P1.24)

  ### Changed behaviour (may need your do-files changed)
  - `mlabvposition()` is refused where twoway refuses it, in twoway's words (all rc 0 with a note before): on rarea, rbar, rcap, rcapsym, rconnected, rline, rscatter, rspike and tsrline (`rscatter requires 3 variables: y y2 x p9`, r(103)), on lfit, qfit, fpfit, lfitci, qfitci, fpfitci, mspline and mband (`too many variables specified: y x p9`, r(103)) and on lowess, lpoly, lpolyci and kdensity (`too many variables specified`, r(103)); a second copy (`option mlabvposition() not allowed`, r(198)); two names (`option mlabvposition():  too many names specified`, r(103)); an expression (`* invalid name`, r(198)); a variable that does not exist (`variable nosuch not found`, r(111)). (WP-30, P1.24)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md A4** (:175-196): the `mlabvposition()` part (A4-p, :182, :192) is closed by `<sha1>`; A4 stays partly open for the parts other entries carry.
  - **GAPS2.md B27** (:657-666): `- **Tracked:** Partly closed in WP-30, BUGS.md "<P1.24 title>", commits <sha1>, <sha2>: mlabvposition and mlabtextstyle drawn; headlabel, pc* first-point labels when the second point is missing, extended missing values and value-labelled dates stay open.` The Gap line's anchor (dash.ado:1049-1050) is stale (:1078-1079 at `c96facd`).
  - **REMAINING.md** :139, :454 (REM-§2-S09-mlabvpos, REM-S09-73-mlabpos), :810-836/:870-881 (REM-05-04-S09-r, REM-05-04-B6, the O2-08 test, which `TestDeclaredOptionsReachTheSpec` now is); **TWOWAY_COVERAGE_AUDIT.md:113** (AUDIT-33); **GAPS.md F3/E1** (WP-22's partial fix finished); **DROPIN-REMAINING.md:145** (P1.24): "Closed by <sha1>, <sha2> (WP-30 S37)."
  - **P2.12** (DROPIN:205) loses `mlabtextstyle`; `mlabstyle`, `mlalign` and `mwidth` stay.
  - **New P2 row (measured, `p4.do`):** twoway refuses a range layer whose `mlabel()` names one of its own plotted variables (`rscatter y y2 x, mlabel(y)`: r(102) `rscatter requires 3 variables: y y2 x`); dash draws it.
  - **test/fixtures/rejected_options.json** :1446-1478 and :4198-4215 record `dash_rc 198` for these options; refresh them.
  - **AGENTS.md invariant:** "per-row label positions live only in `__dash_mlabvpos_*` columns built by `GlyphMapper._mlabel_vpos_columns` from one Stata name; text box styles resolve only through `SchemeParser.textbox_style`'s table."
  - **Unverified:** the twoway behaviour of `mlabvposition()` under `horizontal` (S49 measures it) and on Stata 14-18.5 (not run, M2).
