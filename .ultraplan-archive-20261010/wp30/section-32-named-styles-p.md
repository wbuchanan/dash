# Section 32: Named styles p1-p15 (P1.14 part a)

> Part of: WP-30 · Items: P1.14 part a (entry `P1.14a`) · Risk: yellow · Batch: 11 · Depends on: 08, 11, 13, 24 · Blocks: 36, 38, 39, 43 · Tasks: 20, 1 commit · Case prefix: NP

## Review amendments

- Fixed (major): the commit body's `BUGS.md:` line named the section, not the entry. It now quotes section-01's Appendix B title verbatim.
- Fixed (major): 32-08 was a mid-batch maintainer checkpoint, which A151 forbids. It is now an `auto` task that confirms the batch-11.0 approval (E4) and stops if that approval is missing.
- Fixed (major, A139): "No function is shared with S33" was false. S33 adds `color_idx=` to the `_apply_mlabel_opts` call line in seven mappers this section edits. Dependencies now name them and point to S33's maintainer question.
- Fixed (minor): E2 said `_pstyle_idx` reaches only scatteri, pci, pcarrowi and function. `_make_figure_body` passes it to every mapper (:30556-30609), so TR-32.12's override also moves the label colour that S33 reads by index.
- Fixed (minor): Q1 is resolved. Register P1.14.9 rules on `bmlinestyle()`, and S36's file takes it. The Boundaries, the "For later sections" note and the residual list now match.
- Fixed (minor): truth block put in TR-01.10's form: `_w30_expect`/`_w30_done`, and `ALL CHECKS PASSED` checked in 32-14's verify. `TestP::test_first_copy_wins` is gone because it has no pytest body; NP-20 pins that rule.
- Rejected: refusing `pst()`, `ps()` and `as()` under M5. These are option-name abbreviations, part of the option surface that M5 leaves to P2.21 (D-32d). The fixture records twoway's r(198).
- Rejected: a JS twin for the saved page. No page script writes a glyph style, and TestAfterAFilterMove pins that.
- Checked: S32 shares no function with S31. Its dash.ado programs (`_dash_parse_plot_opts`, `_dash_plot_opts_to_json`, `_dash_fold_*`) and Mata functions (`_dash_stylelist_keys`, `_dash_rep_cat`, `_dash_rep_merge`) are untouched by S31 (`_dash_plot`, `_dash_axreq_add`) and S33. Its dash.sthlp Unsupported paragraphs are apart from S31's :3757-3760 sentence. In R10, S32 alone moves :240 and :607 in batch 11.
- The review pass applied both lenses.
- (ratification 06oct2026) Item 27 (A37, P1.12.6) is "Fix in WP-30": S08 (batch 3) syncs the nonselection and muted copies after the appliers; P2.49 is not filed. TR-32.7's `_style_restyle` note now relies on S08's sync, which S32 keeps and runs its restyle before; P2.49 is removed from the Boundaries residuals, the BUGS Resolution and the closeout's residuals to file.
- (ratification 06oct2026) Added one 32-01 regression test, `TestBrushedAndMutedCopies::test_the_copies_carry_the_named_style[mode]`: S32 sets `marker` and `line_dash` and restyles at ten mapper sites outside the appliers, which S08's brushed-copy tests do not exercise. 32-10 runs and verifies it, and the BUGS Resolution names it. Tasks stay 20.

**Binding readings applied in this file** (decisions.md M1, M5, M6; decision-register P1.14.1-P1.14.9, X.1, X.2, X.4, X.5; index A138, A141-A150, IR-14, R1-R13):
- **P1.14.1 (A44), part A.** This section resolves `p1`-`p15` for every style option. Other names (`ci`, `refline`, `p3line`, unknown names) are S36's (part B, IR-14). Until S36 lands they are noted once per render and the layer keeps its own style (D-32b).
- **P1.14.2 (A45).** twoway's factor order. The manifest's gloss "(explicit options win; D2)" is read as the register's ruling: an explicit option wins over every named style that comes *before* it in twoway's factor list, and loses to one that comes *after* it. So `mcolor(red) pstyle(p3)` is red, but `color(red) mstyle(p4)` is p4. Evidence E3 has the measurements.
- **P1.14.4 (A46).** `clstyle()` and `blstyle()` are included.
- **P1.14.5 and P1.14.9 (A47, A51).** `dstyle()` and `dlstyle()` are S36's, per its manifest scope. `bmlinestyle()` (P1.14.9, same pattern) is taken by S36 too (Notes, Q1, resolved).
- **P1.14.6 (A48) [C].** `p()` is its own option, applied last over every style option, and the first copy wins. Its value is one name. A new first-copy category `"F"` goes in `_dash_rep_cat`. dash.sthlp:2282 is corrected. Measured here (E3) and implemented in dash.ado: when `p()` is given, the series' JSON drops every style option twoway discards (D-32a).
- **P1.14.7 and P1.14.8 (A49, A50) [C].** On area and rarea the outline half of a named style is not drawn, and `lstyle()`, `alstyle()` and `blstyle()` are named there (P2.12). On pcarrow, pcbarrow and pcarrowi the arrowhead is not styled, and `mstyle()` and `mlstyle()` are named there (P2.8).
- **M1.** Bundle widths and sizes come from `SchemeParser`, which after S08/S13 reads Stata units, so no unit is converted here.
- **M5.** Nothing is newly refused. twoway never refuses a style name, only notes it. `pst()`, `ps()` and `as()`, which twoway refuses as unknown options, stay named as dash names every unknown option today. That is the option surface of P2.21, which WP-30 does not sweep (D-32d).
- **M6.** A style option a plot type does not use is silent, as in twoway: `lstyle()` on scatter and `astyle()` on line.
- **X.1/A149.** No copy-list change (R2 row S32). Every new name is a `SchemeParser` or `GlyphMapper` method and travels with its class. `_dash_plot_style_indices` is already listed (dash_render.py:33129).

**Section decisions (this file)**
- **D-32a — p() is resolved at the spec.** twoway discards every explicit style option under `p()`, the label style included, for any name, even an unknown one (E3, probes p5/p6). `_dash_plot_opts_to_json` therefore writes `"p"` and omits each key of one list, `_dash_p_drops`, when `s(p)` is non-empty. Both modes, every path and the label options then follow with no renderer label code. That code is `_apply_mlabel_opts`, which belongs to S33 in this batch (R12). In the renderer, `p` is the last factor and is read before `pstyle` everywhere.
- **D-32b — the interim note.** A name outside `p1`-`p15` (case-sensitive, exactly `p` then 1-15 with no leading zero) gets one note per render per option and value, and only where the option's role is drawn on that layer (M6). The note is `dash: <opt>(<name>): only the named styles p1-p15 are drawn; this layer keeps its own style.`, echoed through `_dash_display` and reaching Stata as `(note: …)` through S06's channel. On the four ci types `pstyle()`/`p()` keep `_ci_pstyle`'s own note and `ci`/`ci2` handling. S36 replaces the interim behaviour.
- **D-32c — which line a style reaches is the plot type's** (measured, E3 probes p7/p8). twoway draws two kinds of line:
  - **The connecting line, `style.line`:** line, connected, tsline, lfit, qfit, fpfit, lowess, lpoly, kdensity, mspline, mband, function and the ci fit lines. Here `pstyle`/`lstyle`/`clstyle`/`p` and `lcolor`/`cl*` reach it, and `alstyle` does not.
  - **The area's outline, `style.area.linestyle`:** spike, rspike, rcap, rline, rconnected's lines, the drop of dropline, the spines of rcapsym, pcspike, pccapsym, the shafts of pcarrow and pcbarrow, and the outlines of bar, rbar and histogram. Here `pstyle`/`p`/`lstyle`/`astyle`/`alstyle`/`bstyle`/`blstyle` and `lcolor`/`al*`/`bl*` reach it, and `clstyle` does not.

  The role names are `"line"` and `"aline"`. `_dash_fold_cl`'s type list (dash.ado:1657) is exactly the line role's, so `clstyle()` is cleared off every other type as the cl triple is.
- **D-32d — `pst()`, `ps()`, `as()`** stay named in the ignoring note (P2.21). The fixture records twoway's r(198) for each, and the closeout files the gap.
- **D-32e — restyle once per glyph and role.** A glyph takes its role's bundle exactly once, before any explicit option is read for it. The ten mappers that read `color()` (or `mcolor()`) before their applier do it right after building the glyph. Every other glyph does it in the first statement of its applier. A private renderer attribute `_dash_named_roles` makes the second call a no-op, so explicit options read after the bundle always win in factor order (research critic 2).

## Overview

**What is wrong today.** DROPIN-REMAINING.md:104 (P1.14): "`pstyle()` works only on the four CI fits. `lstyle`, `mstyle`, `mlstyle`, `astyle`, `alstyle`, `bstyle` and `dstyle` are not read." GAPS2 B11 (GAPS2.md:468-473, also D6): "twoway takes `pstyle(p#)`/`lstyle()`/`mstyle()`/`mlstyle()` from the scheme … In dash all of these are on the plot pending list … and named, except `pstyle` on the four ci types." Measured at `c96facd` (research p1-14 §1):
- `dash scatter mpg weight, pstyle(p3)` prints `dash: ignoring unsupported option(s): pstyle()` and draws `#1a476f`; twoway draws p3 (`#55752f` under s2color).
- `lstyle()`, `mstyle()` and `mlstyle()` reach the spec and are never read.
- `astyle()`, `alstyle()`, `bstyle()`, `blstyle()`, `clstyle()` and `p()` are not even declared, so they fall into `*` and are named as typed (`ast()`, `al()`).
- `p()` is twoway's own whole-plot style: `scatter, mcolor(red) p(p3)` draws p3 in twoway. dash names it and writes nothing.

Both modes ignore the options identically, because the served app copies `GlyphMapper` by source.

**After this section**, in the saved page and the served app, and before and after a filter move:
- the ten options (`pstyle`, `p`, `lstyle`, `clstyle`, `mstyle`, `mlstyle`, `astyle`, `alstyle`, `bstyle`, `blstyle`) draw `p1`-`p15` on every plot type, in twoway's factor order, on the line twoway styles for that type (D-32c);
- `pstyle(p#)` and `p(p#)` move the layer's own plot index to `#` for everything the index colours (labels, scatteri, pci, pcarrowi, function), without renumbering the other layers;
- the nine stylelist options split across an expanded varlist through S11's splitter, and `p()` does not split;
- with no named style present, every figure is byte-identical to the base.

**Why one section.** P1.14 is split by register P1.14.1: part A (this section) is the mechanism and `p1`-`p15`; part B (S36) is the name table. All of part A shares one plan, `GlyphMapper._style_plan`, and one resolver, `SchemeParser.style_bundle`, read where every glyph is built.

**Test order and commit rule.** Task 32-01 writes every regression test against the unmodified worktree and saves the failure text (G1, rule 7). Tasks 32-02/32-03 add the fixture and the fixture-driven tests. 32-04 to 32-18 make the fix, flip the pinned tests and fill the truth block. 32-19 runs the changed files, the cscripts, the identity check and one full suite. 32-20 closes BUGS.md, `WP30_OPEN["P1.14a"]` and the CHANGELOG marker, then makes the one commit. No test-only commit exists, and no commit is red.

## Risk: [yellow] — two CRITICAL appliers, five HIGH symbols and fourteen mappers are edited; the empty plan must leave every existing figure byte-identical

**Why yellow.** Every glyph passes through the appliers, so a fault in the plan changes every dashboard. The plan is empty, and returns at once, unless a named-style key holds a value. The identity checks (TR-32.16) prove that on the parity corpus and on the single-y page digest.

**Risk factors.**
1. `_apply_marker_opts` (CRITICAL, 12 impacted) and `_apply_line_opts` (CRITICAL, 40 impacted).
2. `_apply_fill_opts`, `_ci_band_style`, `_ci_line_restyle`, `_ci_pstyle` and `_render_ci_band` are HIGH.
3. Ten mappers are reached through `_dash_glyph_dispatch` and so are UNKNOWN to the index (E5).
4. The role split (D-32c) means a wrong `role=` at one call site styles the wrong line on one type only.
5. S11's splitter and S16's `_fill_base`/`_f` locals are the base this section edits on.

**Mitigation.**
- The empty plan returns `options` itself and never touches a glyph.
- The fixture-driven grid covers 37 types x 11 options x 2 schemes against twoway's SVG and graph object, so a wrong role fails a named node.
- The parity corpus is compared with the plan bypassed, and against the base digests.
- `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` must stay green without re-baselining.

## Dependencies

- **Depends on (manifest): 08, 11, 13, 24.**
  - S08: Stata size units in `OptionTranslator`/`SchemeParser`, so marker sizes in bundles are Stata's.
  - S11: `_dash_stylelist_keys()`, the asis declarations, `_dash_stylelist_pick` and `_dash_plot_opts_to_json`'s `series` argument (S11 TR-11.1-TR-11.9).
  - S13: the line-width ladder behind `plot_line_width`.
  - S24: the scheme's opacity, the histogram style, and the hollow and sm* symbols on every layer. The marker bundle reads what map_scatter reads after S24.
- **Landed earlier and relied on:**
  - S01: the entry `P1.14a` in BUGS.md, `WP30_OPEN["P1.14a"]`, the marker `<!-- WP-30 P1.14a -->` in "Results that change", the stub block `* ==== S32 P1.14a: … ====`, and the map anchors `# WP-30 S32 (P1.14a): Named styles p1-p15 (P1.14 part a)`.
  - S02: the extractor form (`DASH_REPO`).
  - S06: notes as `(note: …)` through `_dash_emit_note`, counted with S06's needle helpers.
  - S07: 26 scheme files and `SchemeParser._BUILTIN_NAMES`.
  - S16: `_blend_intensity(hex, f, naturally_white)`, `_fill_base`/`_f` in the five fill mappers, `_apply_fill_opts(renderer, options, base=None, intensity=1.0)`.
  - S30: colour reads through `stata_colour`/`parse_color_alpha`.
- **Blocks: 36, 38, 39, 43.**
  - S36 extends `style_bundle` and its name table, declares `dstyle()`/`dlstyle()`, and adds them to `_dash_p_drops`.
  - S38 (region `style()`) and S39 (`xline(, lstyle())`) call `style_bundle` without editing it.
  - S43 composes a bare `*#`/`%#` with the base `_style_value` returns.
- **Parallel batch 11:** S31 (axis look) and S33 (marker-label and colour-key chrome). Merge order S31, S32, S33 (S33 regenerates and lands last).
- **Can run with:** S31 and S33, with one exception. S31 edits the axis readers and shares no function. S33 edits `_apply_mlabel_opts`, `_apply_colorvar` and `SchemeParser._parse_lines`/`_include`, and it also adds one keyword (`color_idx=color_idx`) to the `_apply_mlabel_opts` call line inside seven mappers this section edits: `map_bar`, `map_dropline`, `map_rcapsym`, `map_scatteri`, `map_pcarrow`, `map_pcbarrow` and `map_pccapsym` (plus `map_scatter` if TR-32.6 moves a read out of it). That breaks A139's one-editor rule, and it is put to the maintainer as S33's Q1 (section-33, Notes, "Maintainer question"; the recommendation is to accept a one-keyword exception, since S33 lands after S32). S32 does not edit any `_apply_mlabel_opts` call line, so S33's keyword is the only hunk on those lines.

## Evidence

All anchors were re-verified at `c96facd`, the batch-11 base's ancestor. Sections 08-30 move the line numbers. Every task finds code by the quoted text, never by number alone.

### E1 — dash.ado and dash_parse.mata

**Declarations** (`_dash_parse_plot_opts`, syntax at :924-990). `pstyle`, `mstyle`, `lstyle` and `mlstyle` are `(string)`; `astyle`, `alstyle`, `bstyle`, `blstyle`, `clstyle` and `p` are absent (S11 makes its 28 keys `(string asis)` and leaves these four `(string)`, S11 TR-11.4):
```
940        BWIDth(string)            DEGree(string)            PSTYle(string) ///
951        COLor(string)             MLWidth(string)           MSTyle(string) ///
952        LStyle(string)            MLStyle(string)           MLPattern(string) ///
```
**The pending list** names all four on every type (:1074, :1082-1085):
```
1074    if `: length local lstyle' local _dash_pending `"`_dash_pending' lstyle"'
1082    if `: length local mlstyle' local _dash_pending `"`_dash_pending' mlstyle"'
1083    if `: length local mstyle' local _dash_pending `"`_dash_pending' mstyle"'
1085    if `: length local pstyle' local _dash_pending `"`_dash_pending' pstyle"'
```
**The sreturn block** (:1181, :1202-1204) and **the JSON writer's key list** (`_dash_plot_opts_to_json`, :3144-3156) carry `pstyle mstyle lstyle mlstyle` and nothing else of the family:
```
3150                   bwidth degree pstyle cmissing recast connect bin width start ///
3152                   lineopts fitopts color mlwidth mstyle lstyle mlstyle mlpattern ///
```
**`_dash_fold_typed`** (:1786-1798) takes `pstyle` off the list on the ci types only:
```
1793    local ci_types "lfitci qfitci lpolyci fpfitci"
1794    if `: list ptype in ci_types' {
1795        local ci_drawn "pstyle acolor alcolor alwidth alpattern"
```
**`_dash_fold_cl`** (:1654-1662) keeps the cl triple only on `line connected lfit qfit fpfit lpoly lowess mspline mband kdensity function tsline lfitci qfitci lpolyci fpfitci` (:1657). These are exactly the types whose connecting line twoway styles (D-32c).

**Repeats** (`dash_parse.mata`). `_dash_rep_cat` (:4664-4685) returns `"R"` (the last copy) for every plot key. `_dash_rep_merge` (:5715-5745) starts `if (cat == "R" | strtrim(v1) == "") return(v2)`. No category keeps the first copy. dash_parse.mata:5170 says "p() is pstyle()", which is true of the abbreviation only.

### E2 — dash_render.py

- **`GlyphMapper._ci_pstyle`** (:8262-8290) reads `options.get("pstyle")` only: `p1`..`p15` via `_CI_PSTYLE_P` (:8259), `ci`/`ci2` via `_CI_PSTYLE_NAMED` (:8257). Any other name is noted and drawn as p1.
- **`_ci_line_restyle`'s p branch** (:8476-8481) is already linestyle p#, the line bundle:
  ```
  8476        elif ps == "p":
  8477            g.line_color = self.scheme.default_color(pi, "connected")
  8478            _a = self.scheme.default_alpha(pi, "connected")
  8479            if _a is not None:
  8480                g.line_alpha = _a
  8481            g.line_width = self.scheme.plot_line_width(pi, "")
  8482            g.line_dash = list(self.scheme.default_connect_pattern(pi))
  ```
- **`_ci_band_style`** (:8307-8405) starts from `p_other_band_styles[pi]` (areastyle p#, built at :7120-7140 from `p#other`/`p#otherline`) or the ci style, then merges `color < lcolor < acolor < fcolor < alcolor`, `lwidth < alwidth`, `lpattern < alpattern`.
- **The three appliers.**
  - `_apply_line_opts` (:8540-8620) folds `color()` onto `lcolor()` unless `blcolor()` is given (:8569-8570), then applies cl*, lcolor, lwidth, lpattern and lalpha.
  - `_apply_marker_opts` (:8622-8805) folds `color()` onto `mcolor()` (:8650) and applies marker, mcolor, msymbol, msize, mfcolor, mlcolor, mlwidth, hollow, malpha and msangle.
  - `_apply_fill_opts` (:8807-8860) applies fill.

  None of them reads a style key.
- **The ten mappers that read an explicit colour before their applier** (research critic 2, re-verified):
  - `map_area` 10097 and `map_rarea` 12994 read `color()` onto the fill;
  - `map_bar` 10261 and `map_rbar` 13073 read `color()` onto fill and outline, then `bfcolor()` and `blcolor()` (10275, 10280; 13093, 13100);
  - `_histogram_quads` reads `color()` at 12438;
  - `map_dropline` 13484 and `map_rcapsym` 13585 read `mcolor()`/`color()` into the segment and marker colours passed at construction;
  - `map_scatteri` 13687 reads `mcolor()`/`color()`, plus `msize()`/`msymbol()` at 13702-13710;
  - `map_pcarrow` 14070 and `map_pcbarrow` 14151 read `lcolor()`/`color()` into the shaft and head colour.

  For example, map_dropline (13476-13487):
  ```
  13478        seg_color = self.scheme.default_color(color_idx, "spike")
  13479        dot_color = self.scheme.default_color(color_idx, "dropline")
  13480        try:
  13481            if "mcolor" in options:
  13482                seg_color = dot_color = self.tr.translate_mcolor(
  13483                    options["mcolor"])
  13484            elif "color" in options:
  ```
  An applier that restyled from a bundle first would overwrite these reads: twoway draws `area, pstyle(p3) color(red)` red in either order (research c1).
- **Applier call sites** (`_apply_line_opts`, by role, D-32c):
  - **line:** 8253 (`_render_ci_band`), 9983 (`map_line`, which `map_connected`, `map_rconnected` (13354, 13357) and `map_tsline` call), 10837, 10918, 10995, 11363, 11777, 12323, 12890, 14729, 14851, 14948.
  - **aline:** 10286 (bar), 10362 (spike), 12448 (histogram), 13107 (rbar), 13149 (rspike), 13233 (rcap), 13307-13308 (rline), 13504 (dropline), 13613 (rcapsym), 13787 (pcspike), 14080 (pcarrow), 14161 (pcbarrow), 14259 (pccapsym).
  - **None (P2.12):** 10117 (map_area's optional border).

  `map_rconnected` draws its two lines through `map_line`, so `map_line` needs the role passed through.
- **The style index.** `_dash_plot_style_indices` (:26709-26736) numbers layers. A ci layer counts as two, and `pstyle` is never read. Saved: `_make_figure_body` takes `_pstyle_idx = _dash_plot_style_indices(plots)` (:30423) and passes `color_idx=_pstyle_idx[pi]` to every mapper it calls: scatteri, pci, pcarrowi and function directly (:30556-30569), and every other type through `_dash_add_glyph`/`_dash_add_pc_glyph` (:30576-30609; re-read at review). So TR-32.12's override moves every default the index colours on a `pstyle(p#)`/`p(p#)` layer, the marker-label colour that S33 reads by index included. Served: the emitted code at :35058 (`_sidx = _dash_plot_style_indices(g.get('plots', []))[pi]`) and :35129 does the same. Editing the function reaches every path in both modes, and `_make_figure_body` is not edited (R12).
- **The served copy.** The copy loop skips a missing name (:33426-33430) and copies `OptionTranslator`, `SchemeParser` and `GlyphMapper` whole (:33436). `_dash_plot_style_indices` is listed at :33129. `_dash_warn_once` and `_dash_display` are already copied (`_ci_pstyle` uses both).
- **The stale cue.** `r.muted_glyph = _dash_stale_glyph(r.glyph)` (:32328) clones the glyph after it is mapped, so a named style must be on the glyph before the filter widgets are built. D-32e does that.

### E3 — twoway truth (StataNow 19.5 MP, batch, through `scripts/stata_slot.sh`)

**Research measurements** (research p1-14 §2; graph object `.Graph.plotregion1.plotK.style.*`, stcolor unless stated; p3 = `0 191 127`, p4 = `255 212 0`):
```
s1mono line lstyle(p3)       lc 0 0 0 w .3 vshortdash      lstyle(p3line) 128 128 128 solid
s1mono scatter mstyle(p3)    mf 128 128 128, symbol square
scatter color(red) mstyle(p4)        mf=255 212 0 | lc=255 0 0 | af=255 0 0
scatter mlcolor(red) mstyle(p4)      mf=255 212 0 | ml=255 0 0
scatter mstyle(p4) mlstyle(p3)       mf=255 212 0 | ml=0 191 127   (either order)
connected lstyle(p3) clstyle(p4)     lc=255 212 0 | al=0 191 127   (either order)
line lwidth(thick) lstyle(p3)        lc=0 191 127 | lw=.8
area color(red) astyle(p4)           af=255 212 0 | al=255 212 0
area color(red) pstyle(p4)           af=255 0 0   | al=255 0 0
area fintensity(30) astyle(p4)       af=255 212 0 | ai=30
bar blcolor(red) bstyle(p4)          af=255 212 0 | al=255 0 0
lfitci pstyle(p3) astyle(p4)         band af=255 212 0 ai=80
s2color scatter pstyle(p3) = p3 #55752f; (scatter, pstyle(p3)) (scatter): plot 2 stays p2
```

**p() (research critic c4/c5, and this section's probes p3, p5 and p6, 03oct2026, stcolor):**
```
. twoway scatter mpg weight, <o> nodraw    (o as listed; read: mf, symbol, size, label colour/position)
mcolor(red) msize(huge) p(p3)        mf=0 191 127 | circle | 1.04166            (msize huge alone 4.8611)
mlabel(make) mlabcolor(red) p(p3)    labc=0 191 127      (mlabcolor(red) pstyle(p3): labc=255 0 0)
mlabel(make) mlabposition(9) p(p3)   labpos=3            (without p(): 9)
mlabformat(%9.1f) / mlabgap(5) / mfcolor(red) / mlwidth(thick)   each lost under p(p3)
cmissing(n) p(p3): connect_missings=no (kept);  connect(l) sort p(p3): connect=direct (kept)
mcolor(red) p(bogus)   (note:  named style bogus not found in class seriesstyle, default attributes used)  mf=26 133 255
msymbol(T) p(p3 p4)    (note:  named style p3 p4 not found in class seriesstyle, default attributes used)  circle
mcolor(red) p(p3) p(bogus)   mf=0 191 127 (the first copy)     p(bogus) p(p3): the note, p1
scatter mpg weight, p(p3) mcolor(red%50)   mf=0 191 127, opacity 100
scatter mpg weight, pst(p3)                rc=198
```

**Per-y lists (probe p3):**
```
scatter mpg turn weight, pstyle(p3 p4)   plot1 p3, plot2 p4 (mf 255 212 0)
line mpg turn weight, lstyle(p3 p4)      plot1 lc p3, plot2 lc p4
area mpg turn weight, astyle(p3 p4)      plot1 af p3, plot2 af p4
```

**Which line a style reaches (probes p7 and p8, SVG strokes other than chrome; `#1A85FF` p1, `#00BF7F` p3):**
```
spike/rspike/rcap/pcspike: lcolor(red) red; lstyle, alstyle, astyle(p3) #00BF7F; clcolor(red), clstyle(p3), mstyle(p3) unchanged
dropline: lstyle/alstyle/astyle(p3) the drop #00BF7F; mstyle(p3) the marker fill and outline #00BF7F, the drop unchanged
line, lfit, kdensity, function, mspline, mband, lowess, lpoly: clstyle(p3) #00BF7F; alstyle(p3) unchanged
connected: clstyle(p3) the connecting line; alstyle(p3) unchanged
rline, rconnected (its 2 lines), bar, rbar, histogram: alstyle(p3) #00BF7F; clstyle(p3) unchanged
pcarrow, pcbarrow, pccapsym, rcapsym: alstyle(p3) the 74 shafts/spines only; heads and caps' markers unchanged
```
The commands: `quietly twoway <t> <vars> [in 1/5], <o> name(g, replace)` then `graph export c<i>.svg`, with strokes counted by `grep -o 'stroke:#[0-9A-F]*'`. The do-files `p1.do`-`p8.do` under `<scratch>/s32-probe/` are scratch only; the extractor (Stata truth) re-measures every row.

### E4 — the tests that pin today's behaviour (flip, never delete; R9)

Re-measured by 32-01 on the batch-11 base. A pin found there that is not on this list is investigated before it is flipped.

| Pin | Today's expectation | After |
|---|---|---|
| `test/test_unsupported_report_is_true.py::TestTheListIsCoveredAndHonest::test_the_blocks_were_actually_found` (:240) | 48 plot pending | 44 |
| `test/test_unsupported_report_is_true.py::TestEveryDeclaredOptionIsClassified::test_the_syntax_blocks_were_actually_found` (:607) | 169 declared plot | 175 (astyle alstyle bstyle blstyle clstyle p) |
| `test/test_unsupported_report_is_true.py` `PLOT_VALUES` rows `lstyle` (:118), `mlstyle` (:126), `mstyle` (:128), `pstyle` (:133), driving `test_a_plot_option_reported_unsupported_really_is[...]` | inert | the rows move to `LIVE_VALUES`, with the six new options (`test_a_plot_option_not_reported_unsupported_really_works[...]`) |
| `test/test_help_conformance.py::TestTheParsersFoundSomething::test_the_ignored_list_was_found` (:598) and `::test_the_unsupported_section_was_found` (:603) | 48, 48 | 44, 44 |
| `test/test_help_examples.py::TestTheShapeOfTheExamples::test_which_commands_the_help_shows_output_for` (:124) | `pstyle(p3) t1title("hi")` | `mlpattern(dash) t1title("hi")` |
| `test/test_ci_band_style.py` `_NOT_COMPARED` (:70) | `"astyle"` not compared | compared: `TestTheBandAgainstStata::test_each_measured_case[*-astyle]` |
| S11's `test/test_stylelists.py::TestTheParserKeepsQuotes::test_the_later_lists_are_not_yet_asis` (`_NOT_YET`) and `::TestOneList::test_the_mata_key_list_is_the_declared_set` (`_STYLE_KEYS`), as S11/S20 landed them | the four names not asis; the list without them | `pstyle mstyle lstyle mlstyle` leave `_NOT_YET`; `_STYLE_KEYS` gains the nine |
| `test/test_varlist_expansion.cscript` SL-01 | the key list's word count at base (28 + S20's 4) | +9 |
| `test/test_help_claims_8.cscript` HC8-01 (:379-383), HC8-07 (:512-515) | `pstyle()` named | `mlpattern()` named |
| `test/test_help_claims_8.cscript` HC8-02 `p_opts`/`p_names` (:392-393) and its "48 plot-level" text | pstyle lstyle mstyle mlstyle named | removed; 44 |
| `test/test_ci_band_options.cscript` CB-03 (:208-225) | `psty(p3)` named on scatter | not named; the four fitarea options still named |
| `test/test_ci_band_options.cscript` CB-04 (:255-285) | `al(red)` named as typed | `al(red)` is `alstyle(red)`: no ignoring note, no `alcolor`, the interim style note |
| `test/test_statistical_options.cscript` LB-19 (:1047-1054) | "p(800) is pstyle()" | "p(800) is p()": still never `pwidth`, and `"p":"800"` is in the spec |

These need no flip:
- `test/test_help_claims_8.py::TestAnUnsupportedOptionIsInertWhenServed::test_plot_level` reads the pending list, so it shrinks with it.
- `test/test_ci_band_style.py::TestAdversarial::*` keep `_ci_pstyle`'s note.
- `test/test_ci_plot_index.py` passes no options.

`test/fixtures/rejected_options.json` (rows lstyle, mstyle, mlstyle, astyle, bstyle, pstyle: "implement-S09-style") and `test/fixtures/abbrev_truth.json` (`mls` dash→mlabsize, the pre-fix record) are not edited. The first belongs to the closeout (A145); the second is P3.7's.

### E5 — blast radius (`gitnexus impact <symbol> -d upstream -r dash`, 03oct2026, `c96facd`)

| Symbol | Risk |
|---|---|
| `GlyphMapper._apply_marker_opts` | **CRITICAL** (12 impacted) |
| `GlyphMapper._apply_line_opts` | **CRITICAL** (40 impacted) |
| `_apply_fill_opts`, `_ci_band_style`, `_ci_line_restyle`, `_ci_pstyle`, `_render_ci_band` | HIGH (6, 6, 6, 8, 5) |
| `_dash_plot_style_indices`, `_histogram_quads`, `map_scatteri`, `map_pcarrow` | LOW |
| `map_area`, `map_bar`, `map_rarea`, `map_rbar`, `map_dropline`, `map_rcapsym`, `map_pcbarrow` | UNKNOWN (dispatch dict); `grep -n` confirms each is reached only through `_dash_glyph_dispatch`/`_dash_pc_dispatch` and tests |
| `map_line`, `map_spike`, `map_rspike`, `map_rcap`, `map_rline`, `map_pcspike`, `map_pccapsym` (one keyword each) | UNKNOWN or LOW; run at 11.0 |
| `SchemeParser` (new `style_bundle`) | LOW |
| `_dash_parse_plot_opts`, `_dash_fold_typed`, `_dash_fold_cl`, `_dash_plot_opts_to_json` (dash.ado); `_dash_rep_cat`, `_dash_rep_merge`, `_dash_stylelist_keys` (Mata) | UNKNOWN (not indexed): confirmed by `grep -n` |

## User stories

- **US-32.1** As a twoway user, I want `pstyle(p3)` on any plot type to draw that layer in plot style 3, as in twoway, in the saved page and the served app.
- **US-32.2** As a twoway user, I want `lstyle()`, `clstyle()`, `mstyle()`, `mlstyle()`, `astyle()`, `alstyle()`, `bstyle()` and `blstyle()` with `p1`-`p15` to style the lines, markers, fills and outlines twoway styles with them.
- **US-32.3** As a twoway user, I want a named style and my own options to combine as twoway combines them (`mcolor(red) pstyle(p3)` red, `color(red) mstyle(p4)` p4), so a do-file draws the same in dash.
- **US-32.4** As a twoway user, I want `p(p3)` to restyle the whole plot as twoway does, discarding my other style options, so that copy-pasted commands agree.
- **US-32.5** As a dashboard author, I want `scatter y1 y2 x, pstyle(p3 p4)` to style each y with its own element.
- **US-32.6** As a dashboard user, I want the named style kept after I move a filter, in the legend key, and on the stale cue of a computed layer.
- **US-32.7** As a twoway user, I want to be told in one note when a style name is not drawn yet, and where a named style's outline or arrowhead is not drawn, with nothing printed where twoway prints nothing.

## Business requirements

- **BR-32.1** On every plot type, `pstyle()`, `p()`, `lstyle()`, `clstyle()`, `mstyle()`, `mlstyle()`, `astyle()`, `alstyle()`, `bstyle()` and `blstyle()` with `p1`-`p15` draw the colours, widths, patterns, symbols, sizes and intensities twoway draws, in both modes, before and after a filter move.
- **BR-32.2** A named style and an explicit option combine in twoway's factor order: an option wins over a style that comes before it in that order and loses to one after it.
- **BR-32.3** `p()` restyles the whole plot after every other style option, including the marker-label style. The first copy wins, the value is one name, and the label text, `connect()` and `cmissing()` are kept.
- **BR-32.4** `pstyle(p#)` and `p(p#)` draw the layer in plot `#` for everything the plot number colours, on every path (scatteri, pci, pcarrowi and function included). The other layers keep their numbers.
- **BR-32.5** The nine stylelist options split across an expanded varlist as twoway splits them; a single-y type uses the first element; `p()` never splits.
- **BR-32.6** A style reaches the line twoway styles with it on each type: the connecting line on the line types, the outline on the spike, range, pc and bar types.
- **BR-32.7** Not drawn yet, and said so:
  - a name other than `p1`-`p15` gets one note and the layer's own style;
  - `lstyle()`, `alstyle()` and `blstyle()` on area and rarea are named in the ignoring note;
  - `mstyle()` and `mlstyle()` on pcarrow, pcbarrow and pcarrowi are named in the ignoring note;
  - nothing is printed where twoway uses nothing.
- **BR-32.8** A `colorvar()` layer keeps its mapped colours. The legend key and the stale cue show the named style.
- **BR-32.9** A dashboard with no named style draws exactly what it drew before.
- **BR-32.10** twoway's abbreviations are accepted: `psty`, `p`, `ls`, `cls`, `mst`, `mls`, `ast`, `al`, `bst`, `bl`.
- **BR-32.11** No style name can run code, name a file, reach a scheme key or print more than 80 printable characters.
- **BR-32.12** The help documents the options, the factor order, `p()`, the lists and what is not drawn yet.

## Technical requirements

- **TR-32.1 Declarations** (dash.ado `_dash_parse_plot_opts`).
  - `PSTYle`, `MSTyle`, `LStyle` and `MLStyle` become `(string asis)`.
  - Add one line after the `LStyle(…) MLStyle(…) MLPattern(…)` line: `ASTyle(string asis) ALstyle(string asis) BSTyle(string asis) BLstyle(string asis) CLStyle(string asis) P(string) ///`. The capitalised minimums are twoway's (research s1.do).
  - Delete the four pending lines (:1074, :1082, :1083, :1085). Add no new pending line.
  - In the sreturn block, after `sreturn local mlstyle`, add `sreturn local` lines for `astyle alstyle bstyle blstyle clstyle p` (`: copy local`).
  - The option-surface comment (:685-694) names the five places; all are kept in step by hand. `scripts/regen_option_surface.py` is never run (IR-7).
- **TR-32.2 Lists and p() at the spec** (`_dash_plot_opts_to_json`).
  - The foreach key list gains `clstyle astyle alstyle bstyle blstyle p` after `mstyle lstyle mlstyle`.
  - Before the loop, define `local _dash_p_drops` as twoway's style-option keys dash declares: `pstyle color mcolor msymbol marker msize msangle mfcolor mlcolor mlwidth mlpattern mstyle mlstyle malpha lcolor lwidth lpattern lalpha lstyle clcolor clwidth clpattern clstyle acolor alcolor alwidth alpattern astyle alstyle bstyle blstyle bfcolor blcolor fcolor fintensity falpha mlabcolor mlabsize mlabposition mlabgap mlabangle mlabformat mlabwidth`. Each line of the list carries a comment naming E3's measurement.
  - When `s(p)` is non-empty, read by value with `st_global`, skip every key in the list (`: list key in _dash_p_drops`).
  - Kept under `p()`: `mlabel`, `connect`, `cmissing`, `sort` and every non-style key (E3).
  - A spec without `p` is byte-identical.
- **TR-32.3 Stylelists** (S11's machinery; dash_parse.mata).
  - Append `pstyle lstyle clstyle mstyle mlstyle astyle alstyle bstyle blstyle` to `_dash_stylelist_keys()`'s literal, and rewrite its "who adds later" comment for S32's part.
  - Nothing else in S11's code changes. The normaliser, check and writer read the list.
  - `p` is not added.
- **TR-32.4 First copy wins** (dash_parse.mata).
  - `_dash_rep_cat`: `if (k == "p") return("F")` before `return("R")`, and the comment above it gains `"F" p() (the first copy)`.
  - `_dash_rep_merge`: after `cat = …`, `if (cat == "F") return(strtrim(v1) != "" ? v1 : v2)`.
  - `_dash_rep_reduce` is unchanged. Its non-`"R"` branch writes `p(<merged>)` at the last copy's place.
  - The comment at :5170 becomes "(minimum pw: p() is twoway's own p() option)".
- **TR-32.5 Type folds** (dash.ado).
  - `_dash_fold_typed`: `ci_drawn` loses `pstyle`. Add two blocks of the `jit_undrawn` form, reading by value through `st_global`:
    - on `area rarea`, each of `lstyle alstyle blstyle` given is appended to `named` (P2.12);
    - on `pcarrow pcbarrow pcarrowi`, each of `mstyle mlstyle` given is appended to `named` (P2.8).

    Each block sits under a two-line comment citing E3 and the register row.
  - `_dash_fold_cl` gains `sreturn local clstyle ""` beside the triple (D-32c).
- **TR-32.6 `SchemeParser.style_bundle(self, cls, name) -> "dict | None"`** (new, after `plot_line_width`).
  - `cls` is `"marker"`, `"line"` or `"area"`.
  - `name` must `re.fullmatch(r"p(?:[1-9]|1[0-5])", name)` on the stripped text. Otherwise the method returns None.
  - The integer `i` (0-14) is the only thing taken from the name. No scheme key is ever formatted from user text.
  - **line**: `{"line": self.default_color(i, "connected"), "line_alpha": self.default_alpha(i, "connected"), "line_width": self.plot_line_width(i, ""), "line_dash": list(self.default_connect_pattern(i))}`. This is linestyle p#, `_ci_line_restyle`'s p branch.
  - **area**: `dict(self.p_other_band_styles[i])`, with `line_dash` copied to a list. This is areastyle p#: `fill`, `fill_alpha`, `intensity`, `line`, `line_alpha`, `line_width`, `line_dash`.
  - **marker**: `{"fill", "fill_alpha", "line", "line_alpha", "line_width", "symbol", "size"}`. These are read through exactly the SchemeParser calls `map_scatter` makes for its defaults at `color_idx=i` after S24: `default_color(i, "scatter")`, `default_alpha`, `default_symbol`, `default_marker_size`, `plot_line_width(i, "mark")`, and S24's hollow and sm* reads. If S24 left one of them inline in `map_scatter`, move it into one SchemeParser helper that both call. `fill_alpha` is 0.0 for a hollow symbol.
  - Bundles are new dicts and are never shared with the parser's lists.
- **TR-32.7 The plan** (GlyphMapper; new methods directly after `_ci_line_restyle`).
  - **`_STYLE_FACTORS`** is a class tuple in twoway's factor order (research §2.5), one entry per key.
    - A style entry maps role to bundle class:
      - `pstyle`: marker→marker, mline→marker, line→line, area→area, aline→area;
      - `lstyle`: line→line, aline→line;
      - `clstyle`: line→line;
      - `mstyle`: marker→marker, mline→marker;
      - `mlstyle`: mline→line;
      - `astyle`: area→area, aline→area;
      - `alstyle`: aline→line;
      - `bstyle`: area→area, aline→area;
      - `blstyle`: aline→line;
      - `p` (last): as `pstyle`.
    - An explicit entry is a tuple of roles. The order is:
      - `color` (all five);
      - `lcolor lwidth lpattern` (line, aline);
      - `clcolor clwidth clpattern` (line);
      - `msymbol marker mfcolor msize msangle` (marker);
      - `mcolor` (marker, mline);
      - `mlcolor mlwidth` (mline);
      - `acolor` (area, aline);
      - `alcolor alwidth alpattern` (aline);
      - `bfcolor` (area);
      - `blcolor` (aline);
      - `fcolor fintensity` (area).
    - Each sits at its twoway place: after `pstyle` comes `color`; after `lstyle` the l* options; after `clstyle` the cl* options; after `mstyle` the m* options; after `mlstyle` the ml* options; after `astyle`, `acolor`; after `alstyle`, the al* options; after `bstyle`, `bfcolor`; after `blstyle`, `blcolor`; then `fcolor` and `fintensity`; `p` is last.
    - dash's own `malpha`, `lalpha` and `falpha` are not in the table and are never shadowed.
  - **`_style_plan(self, options) -> "dict | None"`** returns None unless a style key of the table holds a non-blank value.
    - For each present style key it asks `self.scheme.style_bundle(cls, value)` for every class it uses. A None answer marks the key unresolved, and the key is ignored.
    - It returns `{"win": {role: (key, position, bundle)}, "unresolved": [(key, value, roles)]}`. A role's winner is the last resolved style key that covers it.
    - It is a pure function of `options` and the scheme.
  - **`_style_options(self, options, roles) -> dict`** returns `options` itself when the plan is None.
    - Otherwise it returns a copy without each explicit key whose covered roles (its roles intersected with `roles`) are all shadowed: the role has a winner at a later position.
    - If `mcolor` or `color` is shadowed for `mline` but not `marker`, it becomes `mfcolor` with the same value, unless `mfcolor` is present.
    - A key with no role in `roles` (dropline's `mcolor` on its segment) is dropped only when it is shadowed in every role it covers.
  - **`_style_value(self, options, role, attr, default)`** returns the role's winning bundle's `attr`, or `default`.
  - **`_style_restyle(self, renderer, options, roles) -> None`**.
    - For each role in `roles` not already in `renderer._dash_named_roles`, it records the role and, when the role has a winner, sets the glyph attributes the glyph has:
      - **marker**: `fill_color`, `fill_alpha`, `marker`, `size`;
      - **mline**: `line_color`, `line_alpha`, `line_width`;
      - **line/aline**: `line_color`, `line_alpha`, `line_width`, `line_dash`;
      - **area**: `fill_color = self._blend_intensity(fill, intensity, self.scheme.naturally_white)` and `fill_alpha`.
    - A `None` colour sets that alpha to 0.0 (the style draws nothing there). A `None` alpha is 1.0.
    - It then calls `_style_unresolved` for each unresolved key whose roles meet `roles`.
    - It never writes `nonselection_glyph` or `muted_glyph` itself. Every glyph it restyles, in an applier's first statement or right after a mapper builds it (D-32e), then reaches an applier, after which S08's sync (batch 3; A37, ratification 06oct2026: fixed in WP-30, P2.49 not filed) copies the styled properties to both copies, keeping dash's nonselection alpha. S32 keeps that sync where S08 put it, byte for byte, and its restyle runs before it. `_style_restyle` sets `marker` and `line_dash` as well as sizes, widths, colours and alphas; `TestBrushedAndMutedCopies` pins that the copies carry each of them, and if S08's sync does not copy one, 32-10 stops and reports (S08 owns the sync).
  - **`_style_unresolved(self, key, value) -> None`** calls `_dash_warn_once(("named-style", key, str(value)), self._STYLE_UNREAD_NOTE.format(opt=key, name=_dash_display(value)))`. The class constant `_STYLE_UNREAD_NOTE` is D-32b's text.
- **TR-32.8 The appliers.**
  - `_apply_marker_opts(renderer, options)` starts with `self._style_restyle(renderer, options, ("marker", "mline"))` and `options = self._style_options(options, ("marker", "mline"))`. The rest is unchanged.
  - `_apply_line_opts(self, renderer, options, role="line")` gains the keyword. When `role` is not None, it starts with `self._style_restyle(renderer, options, (role,))` and `options = self._style_options(options, (role,))`. `role=None` leaves today's behaviour.
  - `_apply_fill_opts(renderer, options, base=None, intensity=1.0)` starts with `self._style_restyle(renderer, options, ("area",))` and `options = self._style_options(options, ("area",))`.
- **TR-32.9 The ten mappers** (D-32e). Each gets these edits, and every explicit read below takes `self._style_options(options, <its role>)`:
  - **The five fill mappers** (`map_area`, `map_rarea`, `map_bar`, `map_rbar`, `_histogram_quads`):
    - S16's `_fill_base` default becomes `self._style_value(options, "area", "fill", <today's default>)`, and `_f` becomes `self._style_value(options, "area", "intensity", <today's>)`;
    - right after the glyph is built: `self._style_restyle(r, options, ("area", "aline"))`. Use `("area",)` on map_area and map_rarea;
    - the `color()` read is split per role: the fill from the `("area",)` options and the outline from the `("aline",)` options; `bfcolor()`/`blcolor()` likewise;
    - the outline applier call passes `role="aline"`, and map_area's border passes `role=None`.
  - **`map_dropline` and `map_rcapsym`:** build the segment and the marker with the scheme defaults, call `_style_restyle(seg, options, ("aline",))` and `_style_restyle(dot, options, ("marker", "mline"))`, then set the explicit `mcolor()`/`color()` read from the `("marker", "mline")` options onto the glyphs. This keeps today's rule that the segment takes `mcolor()`. Their segment applier passes `role="aline"`.
  - **`map_scatteri`:** `_style_restyle(r, options, ("marker", "mline"))` right after `fig.scatter`. The applier re-applies the unshadowed `msize()`/`msymbol()`/`mcolor()`.
  - **`map_pcarrow` and `map_pcbarrow`:** `_style_restyle(seg, options, ("aline",))` right after the shaft is built. The head keeps its colour (P2.8), and the shaft's applier passes `role="aline"`.
- **TR-32.10 The aline call sites** (E2 list). Pass `role="aline"` at bar, spike, histogram, rbar, rspike, rcap, rline (both), dropline, rcapsym, pcspike, pcarrow, pcbarrow and pccapsym. `map_line(…, role="line")` gains the keyword and passes it to its `_apply_line_opts`. `map_rconnected` calls `map_line` with `role="aline"` for both lines.
- **TR-32.11 The ci types.**
  - `_ci_pstyle` reads `options.get("p")` first, then `pstyle`, and names the option it read in its note.
  - `_render_ci_band` passes `_nopstyle = {k: v for k, v in options.items() if k not in ("pstyle", "p")}` to `_ci_band_glyphs`' style, `_ci_line_restyle`'s restyle and `_apply_line_opts`. pstyle and p never shadow an option, because pstyle is first and p's options were dropped at the spec. `_ci_pstyle` still reads the full options.
  - `_ci_band_style(options)`:
    - after today's base from `_ci_pstyle`, take the plan of `_nopstyle`. An `area` winner replaces `fill`, `fill_alpha` and `intensity`. An `aline` winner replaces `line`, `line_alpha`, `line_width` and `line_dash`, from the area bundle (astyle/bstyle) or the line bundle (lstyle/alstyle/blstyle);
    - then every explicit read uses `oa = self._style_options(o, ("area",))` for fill keys and `ol = self._style_options(o, ("aline",))` for outline keys. `_col` takes the dict it reads from, and `color()`/`acolor()` are applied to the fill from `oa` and to the outline from `ol`.
  - `_ci_line_restyle` ends with `self._style_restyle(line_r, _nopstyle, ("line",))` for an lstyle/clstyle winner.
- **TR-32.12 The style index.** In `_dash_plot_style_indices`, after a layer's index is computed (and so after `n` advances), override that layer's value only. The name is read from the layer's `options`: `p`, then `pstyle`. When it `re.fullmatch(r"p(?:[1-9]|1[0-5])", …)`, the value is `#-1`. The pattern is an inline literal, because the function is copied by name. `n` is unchanged. The docstring cites E3's numbering row.
- **TR-32.13 Both modes.**
  - No copy-list change and no `_generate_app_source`/`_make_figure_body` edit (R2 row S32, R12).
  - The served app draws through the copied classes and the listed `_dash_plot_style_indices`.
  - **No JS twin.** No saved-page script writes a glyph style (the filter callbacks move data only). `TestAfterAFilterMove::test_no_page_script_writes_a_style` pins that over every CustomJS of a built page and every module-level `*_JS` string: no `line_color`, `fill_color`, `line_dash`, `line_width`, `.marker` or `.size` assignment.
- **TR-32.14 Registries.**
  - Under the S32 anchor of `test/function_test_map.py`, in alphabetical order: `GlyphMapper._style_options`, `GlyphMapper._style_plan`, `GlyphMapper._style_restyle`, `GlyphMapper._style_unresolved`, `GlyphMapper._style_value` and `SchemeParser.style_bundle`, each pointing at its `test/test_named_styles.py` node (TDD stubs).
  - `program_coverage_map.py` is unchanged: no new program. The edited Mata functions keep their entries (TP-14 and SL-01) and gain no new key.
- **TR-32.15 Notes** go through S06's channel (X.2). The interim note and `_ci_pstyle`'s are `dash: `-prefixed `warnings.warn` raised inside `main()`. The ignoring note gains the type-specific names through `_dash_fold_typed`'s `named`.
- **TR-32.16 Identity.**
  - (a) Committed: `TestTheEmptyPlanIsInert::test_the_corpus_draws_the_same_with_the_plan_bypassed` renders every `test_mode_parity.CORPUS` case saved and served, once normally and once with `_style_plan` monkeypatched to return None, and compares `normalise_bokeh_html`/document JSON. It also asserts that no corpus case holds a style key except S32's own.
  - (b) Section-only: 32-03 writes SHA-256 digests of every pre-S32 CORPUS case's normalised saved page and served document at the base to `$S/32-base-digests.json`, and 32-19 compares them on the fixed tree. They must be equal.
  - (c) `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` stays green unedited.
- **TR-32.17 Parity** (R8). `test/test_mode_parity.py` `CORPUS` gains, after its last case:
  - `_case("named styles p1-p15", …)`: scatter `pstyle(p3)`, line `lstyle(p4)`, bar `bstyle(p5) blcolor(red)`, spike `alstyle(p6)`, area `astyle(p7)`;
  - `_case("p() and the plot index", …)`: scatter `p(p3)`, scatteri `pstyle(p4)`, function `pstyle(p5)`, pci `pstyle(p6)`;
  - `_case("named styles on a ci fit", …)`: lfitci `pstyle(p3) astyle(p4) alstyle(p5)`.

  `ALLOWED` and `_MUST_WARN` are untouched.
- **TR-32.18 Security (rule 1).**
  - A name is matched with `re.fullmatch` against a fixed pattern and reduced to an integer, and never used to build a path, a scheme key, a Bokeh field or a format string.
  - Notes echo it through `_dash_display` (printable, at most 80 characters).
  - The spec writes it through `_dash_json_str`.
  - dash.ado reads every value by value (`st_global`) and puts it on a command line only through `macval()`.
  - No `eval`, `exec` or `shell=True`.
  - The extractor's only `shell` call is S02's `git -C "<root>" rev-parse HEAD` into a tempfile.
  - `TestAdversarial` covers SMCL `{bf:x}`, quotes, a backtick and `$`, `../x`, `p3;rm -rf /`, a 100,000-character name (rendered in under 2 s), Unicode `p３`, `p03`, `P3` and a blank.

## Boundaries

- **Not this section's:**
  - non-p names, twoway's default attributes and its note (S36, which edits only `style_bundle`, its table, the extractor and generated files, and may retire `_style_unresolved`);
  - `dstyle()`, `dlstyle()` and `bmlinestyle()` (S36; Q1);
  - region `style()` (S38) and `xline(, lstyle())` (S39);
  - a bare `*#`/`%#` against a named style's base (S43);
  - `recast()`'s type (S45).
- **Batch partners.**
  - S31 owns `_dash_parse_axis_spec`, `_parse_axis_angle`, `_dash_scale_spec` and the axis paragraphs of the help.
  - S33 owns `_apply_mlabel_opts`, `_apply_colorvar`, SchemeParser's read-recording (`_parse_lines`, `_include`), the extractor and scheme regeneration, and the Marker Label / colour-key / scheme-support paragraphs.
  - S32 edits none of these. Labels follow `p()` through D-32a and `pstyle()` through the index.
- **Residuals named, not drawn:**
  - area/rarea outlines (P2.12);
  - pc arrowheads styled by `mstyle()` (P2.8);
  - `pst()`/`ps()`/`as()` refusals (P2.21).
- **Not edited:**
  - `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures` and `_build_filter_widgets` (R12);
  - the copy-list tuples;
  - `scripts/regen_option_surface.py`;
  - `test/fixtures/rejected_options.json` and `abbrev_truth.json` (A145, P3.7);
  - every tracking document (A145).

## Stata truth

**Extractor** `scripts/extract_named_style_truth.do` (new, committed), in S02's form, copied from S11's `extract_stylelist_truth.do`:
- `local repo : env DASH_REPO`, else `c(pwd)` when it holds `dash.ado` and `test/run_all_cscripts.do`, else `exit 601`.
- Then `adopath ++ "`repo'/"`, `global dash_nobrowser 1`, `clear all`, `set more off`, `version 19`, `local entry_scheme "`c(scheme)'"`.
- `_meta`: `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit` (`shell git -C "`repo'" rev-parse HEAD > <tempfile>`, read with `file read`), and `extracted` (`c(current_date)`).
- Program `_np_read k`: the reader of research `pst_prog.do`. For plot `k` it reads `mf mfop ml mlw ms msz lc lop lw lp af afop ai al alw alp labc labpos` from `.Graph.plotregion1.plot`k'.style`, each via `` `.Graph….rgb' ``/`.val`/`.stylename`, into one `|`-separated record line.
- Program `_np_case id scheme cmd`:
  - `capture noisily twoway <cmd> name(g, replace)` under a text log;
  - record `_rc` and the `(note: …)` lines;
  - read plots 1-3 when rc is 0;
  - `graph export <id>.svg` for the R and S grids only;
  - append `id|scheme|rc|cmd|records|svg|log` to a tempfile.
- Data: `sysuse auto` (and `sysuse sp500, clear` with `tsset date` for TS rows).

**Grids** (case ids; every command ends `, <opts>` as written):
- **B (bundles).** For each scheme of `SchemeParser._BUILTIN_NAMES`, listed literally in the do-file, and `k` in 1..15: `B-<scheme>-p<k>` `scatter mpg weight in 1/5, pstyle(p<k>)`. The seriesstyle's marker, line and area are all read, so one row is all three bundles. 390 rows.
- **R (roles by type), schemes stcolor and s1mono.** For each type of `scatter line connected area rarea bar rbar histogram spike rspike rcap rcapsym rline rconnected rscatter dropline dot lfit qfit lowess lpoly fpfit kdensity mspline mband function lfitci lpolyci pcspike pccapsym pcscatter pcarrow pcbarrow scatteri pci pcarrowi tsline`, with the type's usual variables (E3's do-files):
  - `R-<scheme>-<type>-none`;
  - `R-<scheme>-<type>-<opt>` with `<opt>(p3)` for each of the ten options;
  - with SVG.

  814 rows.
- **F (factor order, stcolor):**
  - F01-F25, research t5's rows verbatim;
  - F26 `scatter mpg weight, mcolor(red) pstyle(p3)`;
  - F27 `line mpg weight, lcolor(red) pstyle(p3)`;
  - F28 `area mpg weight, fcolor(red) pstyle(p3)`;
  - F29 `bar mpg weight, color(red) blstyle(p4)`;
  - F30 `spike mpg weight, lcolor(red) alstyle(p4)`;
  - F31 `spike mpg weight, alstyle(p4) lcolor(red)`;
  - F32 `dropline mpg weight, mcolor(red) mstyle(p4)`;
  - F33 `dropline mpg weight, mstyle(p4) mcolor(red)`;
  - F34 `dropline mpg weight, lstyle(p3) mcolor(red)`.
- **P (p(), stcolor):**
  - P01 `scatter, mcolor(red) msize(huge) p(p3)`;
  - P02 `scatter, mlabel(make) mlabcolor(red) p(p3)`;
  - P03 `mlabel(make) mlabposition(9) p(p3)`;
  - P04 `mlabel(make) mlabformat(%9.1f) p(p3)`;
  - P05 `mlabel(make) mlabgap(5) p(p3)`;
  - P06 `mfcolor(red) p(p3)`;
  - P07 `mlwidth(thick) p(p3)`;
  - P08 `cmissing(n) p(p3)`;
  - P09 `connect(l) sort p(p3)`;
  - P10 `line, lstyle(p4) p(p3)`;
  - P11 `area, fcolor(red) p(p3)`;
  - P12 `p(p3) pstyle(p4)`;
  - P13 `pstyle(p4) p(p3)`;
  - P14 `p(p3) p(p4)`;
  - P15 `mcolor(red) p(p3) p(bogus)`;
  - P16 `mcolor(red) p(bogus)`;
  - P17 `msymbol(T) p(p3 p4)`;
  - P18 `p(p3) mcolor(red%50)`;
  - P19 s1mono `line, p(p3)`;
  - P20 `lfitci, p(p3)`.
- **N (numbering and lists, stcolor):**
  - N01 `(scatter mpg weight, pstyle(p3)) (scatter mpg turn)`;
  - N02 `scatter mpg turn weight, pstyle(p3 p4)`;
  - N03 `line mpg turn weight, lstyle(p3 p4)`;
  - N04 `area mpg turn weight, astyle(p3 p4)`;
  - N05 `scatter mpg weight, pstyle(p3 p4)`;
  - N06 `scatter mpg turn weight, p(p3 p4)`;
  - N07 `(scatteri 20 3000, pstyle(p3)) (function y=20, range(2000 4000) pstyle(p4))`;
  - N08 `(pci 20 2000 30 4000, pstyle(p5)) (pcarrowi 15 2000 25 4000, pstyle(p6))`.
- **A (abbreviations, stcolor):**
  - A01-A10: `psty(p3)`, `p(p3)`, `ls(p3)`, `cls(p3)`, `mst(p3)`, `mls(p3)`, `ast(p3)`, `al(p3)`, `bst(p3)`, `bl(p3)`, each on the type that uses it;
  - A11 `scatter, pst(p3)`, A12 `ps(p3)`, A13 `area, as(p3)`, each recorded with rc and message.
- **U (other names, for S36 and for the interim note's tests):** `scatter/line/area` x `pstyle/lstyle/mstyle/astyle` x `bogus P3 p16 p03 ci ci2 foreground refline p3line p3bar none`, recorded with notes. 132 rows.

The python block (`python:` … `end`; `sfi.Macro.getLocal`; never `shell=True`; a backtick as `\x60`; `sys.path` gets `<repo>/scripts` for `svg_truth`) writes `{"cases": {id: {"scheme","cmd","rc","notes","plots":{k:{…}},"svg":{"strokes":[[hex,n]],"fills":[[hex,n]]}}}, "schemes": [...], "_meta": {...}}` with `indent=2, sort_keys=True` to `<repo>/test/fixtures/named_style_truth.json`. It prints `named_style_truth: wrote <N> cases` and restores `entry_scheme`.

**Run.**
```
mkdir -p "$S/truth"
DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S/truth" "$WT/scripts/extract_named_style_truth.do"
git -C $WT add -f test/fixtures/named_style_truth.json
```
`test/test_named_styles.py` names the fixture, so `test_fixtures_are_committed.py` passes unedited. The fixture is never patched by hand (R7).

**Truth block** (`test/test_wp30_truth.cscript`, between S01's `S32 start` and `S32 end` lines, gate `WP30_ONLY=S32`).
- The helpers `_s32_page`, `_s32_app` and `_s32_svg` (python, top level, directly above `* ==== S32 P1.14a:`) copy S11's `_s11_*` pattern. They read the saved page's document, the served app's `make_document`, and twoway's SVG through `svg_truth`.
- Program `_s32_case id scheme cmd` runs `twoway <cmd>, nodraw name(g, replace)` and `graph export`, then `dash <cmd>, saving(<work>/s32.html, replace)`, then `dash <cmd>, name(g1)` with `dash build, server saving(<work>/s32.py) replace nobrowser`.
- It compares the layer's stroke and fill colours, the marker symbol and the line dash in the saved page, the served document, and the served document after `_fire`-ing a `filter(price, type(range))` move.
- Cases:
  - NP-01 s2color `scatter mpg weight, pstyle(p3)`;
  - NP-02 s1mono `line mpg weight, sort lstyle(p3)`;
  - NP-03 s1mono `scatter mpg weight, mstyle(p3)`;
  - NP-04 stcolor `area mpg weight, sort astyle(p3)`;
  - NP-05 stcolor `bar mpg weight, bstyle(p3) blcolor(red)`;
  - NP-06 stcolor `scatter mpg weight, mcolor(red) p(p3)`;
  - NP-07 stcolor `spike mpg weight, alstyle(p3)`;
  - NP-08 stcolor `scatter mpg turn weight, pstyle(p3 p4)`;
  - NP-09 stcolor `(scatteri 20 3000, pstyle(p3)) (function y=20, range(2000 4000) pstyle(p4))`.
- Each case reports through `_w30_expect`/`_w30_done` (`NP-nn PASS: …`; TR-01.10 item 4). Files are written only under `` `w30_work' `` and erased before the end line. Run alone (`WP30_ONLY=S32`), the script prints `ALL CHECKS PASSED`.

## TDD test stubs

### Regression tests written by 32-01 (`test/test_named_styles.py`, new; each FAILS at the batch-11 base; the values are E3's literal twoway hexes)

Modes go through `test_scheme_resolution._draw`/`MODES`, specs through `test_mode_parity._spec` and `test_server_layer_defects.plot_for`, the served move through `test_served_linked_views._served_doc`/`_fire`, and notes through S06's needle helpers.
- `TestPstyle::test_scatter_pstyle_p3_is_p3[mode]`: s2color marker fill `#55752f`.
- `TestPstyle::test_line_pstyle_takes_the_connect_chain[mode]`: s1mono `line, pstyle(p3)` is black and vshortdash (not plot 3's grey solid).
- `TestPstyle::test_bar_pstyle_is_areastyle_p3[mode]`: stcolor `bar, pstyle(p3)` fill `#00bf7f` blended at 80, outline width `.3` in px.
- `TestLstyle::test_s1mono_line_lstyle_p3[mode]`: black, vshortdash.
- `TestLstyle::test_spike_lstyle_reaches_the_outline[mode]`: stcolor `#00bf7f`.
- `TestMstyle::test_s1mono_mstyle_p3_is_a_grey_square[mode]`: `#808080`, square.
- `TestMlstyle::test_outline_only[mode]`: `mlstyle(p3)` outline `#00bf7f`, fill p1.
- `TestAstyleBstyle::test_area_astyle_p3[mode]`, `::test_bar_bstyle_p3[mode]`, `::test_bar_blstyle_p3_outline_only[mode]`.
- `TestClstyle::test_connected_clstyle_is_the_connecting_line[mode]`, `::test_spike_clstyle_is_silent_and_unchanged[mode]` (guard: unchanged at the base too).
- `TestFactorOrder::test_color_then_mstyle_is_p4[mode]`, `::test_mcolor_then_pstyle_is_red[mode]`, `::test_mlcolor_then_mstyle_keeps_the_red_outline[mode]`, `::test_color_then_astyle_on_area_is_p4[mode]`, `::test_area_color_then_pstyle_is_red[mode]` (critic 2), `::test_lwidth_then_lstyle_keeps_the_width[mode]`, `::test_fintensity_then_astyle_keeps_30[mode]`, `::test_dropline_color_then_pstyle_is_red[mode]`, `::test_scatteri_mcolor_then_pstyle_is_red[mode]`, `::test_pcarrow_lcolor_then_pstyle_is_red[mode]`.
- `TestP::test_p_overrides_mcolor[mode]`: `mcolor(red) p(p3)` is p3. `::test_p_on_lfitci_draws_p3[mode]`. (The first-copy rule is a Stata spec check, cscript NP-20, and has no pytest node.)
- `TestNumbering::test_the_next_layer_keeps_p2[mode]`, `::test_scatteri_and_function_take_the_index[mode]`, `::test_pci_and_pcarrowi_take_the_index[mode]`.
- `TestLists::test_two_y_split[mode]`: the spec objects `[{"pstyle":"p3"},{"pstyle":"p4"}]` draw p3 then p4. The splitting itself is the cscript NP-46.
- `TestOtherNames::test_noted_once_and_drawn_as_the_layer[mode]`: `lstyle(refline)` on line is noted once with the D-32b text, and the line keeps p1. `::test_unused_option_is_silent[mode]`: `scatter, lstyle(bogus)` prints nothing.
- `TestAfterAFilterMove::test_served_style_survives_a_move`: the style is the same after `_fire` and the data changed. `::test_no_page_script_writes_a_style` (guard; passes at base).
- `TestLegendAndStale::test_the_legend_key_is_the_named_style[mode]`, `::test_a_computed_layer_keeps_its_style_on_the_stale_cue` (saved, `lfit, lstyle(p3)`: `muted_glyph.line_color == #00bf7f`).
- `TestColorvar::test_colorvar_keeps_its_mapping[mode]` (guard).
- `TestBrushedAndMutedCopies::test_the_copies_carry_the_named_style[mode]` (A37; S08's sync): in both `nonselection_glyph` and `muted_glyph`, s2color `scatter, pstyle(p3)` has fill `#55752f` and the glyph's `marker` and `size`; s1mono `line, lstyle(p3)` has the glyph's `line_color`, `line_width` and `line_dash` (vshortdash, not solid); stcolor `bar, pstyle(p3)` (a mapper-site restyle, D-32e) has the glyph's `fill_color`, which is not p1's; each nonselection alpha is not the glyph's.
- `TestAdversarial::test_hostile_names_are_noted_shortened_and_inert[name]` (TR-32.18 list), `::test_a_huge_name_is_bounded_in_time`.
- `TestTheHelp::test_the_named_styles_paragraph_states_the_order` and `::test_2282_no_longer_says_p_is_pstyle`.

### Added by 32-03 (fixture-driven; fail at base unless marked)

- `TestTheFixture::test_meta_is_stamped`, `::test_every_shipped_scheme_is_recorded` (equals `SchemeParser._BUILTIN_NAMES`), `::test_twoways_notes_are_recorded` (U rows): guards.
- `TestStyleBundle::test_against_stata[scheme-pk]`: 390 nodes. `style_bundle` for each class equals the B row through `translate_lwidth`, `translate_msize`, `translate_lpattern`, `translate_msymbol` and the rgb-to-hex conversion.
- `TestStyleBundle::test_the_marker_bundle_is_the_scatter_default[scheme-pk]`: the bundle equals `map_scatter`'s glyph at `color_idx=k-1`.
- `TestStyleBundle::test_names_are_exact`: `P3`, `p16`, `p03`, `p3 ` with a blank inside, `""` → None.
- `TestRoles::test_against_stata[scheme-type-opt]`: R grid, saved mode. The drawn strokes and fills of each type's glyphs equal the SVG colours, excluding chrome.
- `TestFactorOrder::test_each_measured_row[Fnn]` and `TestP::test_each_measured_row[Pnn]`: saved and served.
- `TestFactorOrder::test_shadowed_options_are_dropped`: unit tests of `_style_options`.
- `TestRestyle::test_only_named_roles_change`, `::test_style_value_falls_back`: units.
- `TestTheEmptyPlanIsInert::test_the_corpus_draws_the_same_with_the_plan_bypassed` (TR-32.16a; at base it passes vacuously, since the method is missing and is skipped by `hasattr`, which is recorded as a guard).
- `test/test_unsupported_report_is_true.py` `LIVE_VALUES` gains:
  - `pstyle ({"pstyle":"p2"},{"pstyle":"p6"},"scatter",{})`;
  - `p ({"p":"p2"},{"p":"p6"},"scatter",{})`;
  - `lstyle (… "p3","p7" …,"line")`;
  - `clstyle (…,"line")`;
  - `mstyle (… "p1","p5" …,"scatter")`;
  - `mlstyle (…,"scatter")`;
  - `astyle (…,"area")`;
  - `alstyle`, `bstyle` and `blstyle` (`"p3","p7"`, `"bar"`).

  `test_a_plot_option_not_reported_unsupported_really_works[<each>]` fails at base for the four declared names.

### cscripts (32-14 to 32-17)

- `test_wp30_truth.cscript` NP-01..NP-09 (Stata truth).
- `test_twoway_option_parity.cscript`:
  - NP-20 `p(p3) p(p4)` writes `"p":"p3"`, and `p(p3) mcolor(red) lcolor(red) mlabcolor(red)` writes no `mcolor`/`lcolor`/`mlabcolor` but keeps `mlabel`;
  - NP-21 `pstyle(p4) p(p3)` writes `p` only;
  - NP-22 area/rarea `lstyle(p3) alstyle(p3) blstyle(p3)` named, `astyle(p3)` not;
  - NP-23 pcarrow `mstyle(p3) mlstyle(p3)` named;
  - NP-24 `spike, clstyle(p3)` writes no `clstyle`;
  - NP-25 `scatter, astyle(p3)` is silent, rc 0.
- `test_abbreviations.cscript` NP-30..NP-33: the ten minimums land on their keys (`dash_json_<g>`) and are not named; `pst()`, `ps()` and `as()` are named as typed, rc 0 (D-32d); `ml(p3)` is r(111) as twoway.
- `test_parser.cscript` NP-40..NP-42: every new key reaches the spec, a hostile name is stored as text (`$HOME`, a backtick), and p()'s drop list is honoured on a 3-y varlist.
- `test_varlist_expansion.cscript` NP-46..NP-48: `scatter mpg turn weight, pstyle(p3 p4)` writes `pstyle` per series, `p(p3 p4)` writes `"p":"p3 p4"` on both, and `pstyle(p3 .. )` on three y gives p3 x3. SL-01 is flipped (+9).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Bundles = twoway's seriesstyle p1-p15, 26 schemes | pytest `TestStyleBundle` | named_style_truth.json B | n/a (unit) |
| Every type x option on the right line | pytest `TestRoles` (saved), NP-01..09 (both, plus a move) | R | yes |
| Factor order, p() | pytest `TestFactorOrder`, `TestP` | F, P | yes |
| Numbering on every path | pytest `TestNumbering`, NP-09 | N | yes |
| Lists | cscript NP-46..48, pytest `TestLists`, NP-08 | N | yes |
| Spec, folds, repeats, abbreviations | cscripts NP-20..25, NP-30..33, NP-40..42 | A | n/a |
| After a filter move | pytest `TestAfterAFilterMove`, NP-01..09 | — | yes |
| Identity | pytest `TestTheEmptyPlanIsInert`; `$S` digests; single-y digest | — | yes |
| Parity | `test_mode_parity.py` CORPUS (G3) | — | yes |
| Notes and silence | pytest `TestOtherNames`, `TestAdversarial` | U | yes |
| Help | pytest `TestTheHelp`, test_help_conformance, test_help_examples, HC8 | — | n/a |
| Registries | test_function_test_map, test_program_coverage_map, test_statistical_helpers::TestTheServedAppCarriesEveryName, test_resource_limits::TestTheServedAppDefinesEveryNameItReads, test_cscript_hygiene, test_tracking_documents | — | — |

**Acceptance criteria.**
- **AC-32.1** Every `TestStyleBundle`, `TestRoles`, `TestFactorOrder` and `TestP` node passes, saved and served. No fixture row is excluded without a `_meta.excluded` reason naming S36, P2.8 or P2.12.
- **AC-32.2** NP-01..NP-09 print PASS, and each compares the saved page, the served document and the served document after a move.
- **AC-32.3** `$S/32-base-digests.json` equals the fixed tree's digests for every pre-S32 CORPUS case, and the single-y digest test passes unedited.
- **AC-32.4** The plot pending count is 44 and the declared count 175. The help's Unsupported section and `_dash_pending` agree (test_help_conformance).
- **AC-32.5** `al(p3)` lands on `alstyle`, `p(p3) p(p4)` on `p3`, and `pst(p3)` is named (rc 0).
- **AC-32.6** No new UserWarning outside S06's channel. The interim note appears once and is at most 80 printable characters of name.
- **AC-32.7** One full suite through the queue is green (E6 for flaky tests), and the BUGS.md entry, `WP30_OPEN` key and CHANGELOG marker are closed in the commit.

## Tasks

**Commit boundary.** Tasks 32-01 to 32-20 form the one commit of entry `P1.14a`, subject `Draw the named styles p1-p15 on every plot type in twoway's order (WP-30 P1.14a)`.
- It is made by 32-20 on `wp30-s32` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s32` (`$WT`), after one full run through the queue.
- `$S` is `<scratch>/s32`, where `<scratch>` is the orchestrator's WP-30 scratch directory (index "Deltas"). Every command runs from `$WT` unless it names the main checkout.

The body:
1. opens with `<scratch>/32-P1.14a-failure.txt`;
2. then the measured defect (Overview) and what changed, where, in both modes;
3. then one line each:
   - `Regression: test/test_named_styles.py::<Class>::<test> -- failed at <batch-11 base sha> with <text>` (each 32-01 class's first node);
   - `Flipped: <node> -- <old expectation> was wrong because <why>`, one per E4 row;
   - `Fixture: test/fixtures/named_style_truth.json (scripts/extract_named_style_truth.do)`;
   - `BUGS.md: "pstyle() works only on the four CI fits, and lstyle, mstyle, mlstyle, astyle, alstyle, bstyle and their siblings are not read" (closed)` (the Appendix B title of section-01, verbatim).

No subject, body, BUGS line, CHANGELOG line or help line names a tool or vendor (G7): `grep -Eic 'claude|anthropic'` prints 0 on the message file before the commit and on `git log -1 --format=%B` after it. Never stage `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.ultraplan/` or any `*.html` (E7, G6).

<task type="auto" id="32-01">
  <name>Write the failing named-style regression tests</name>
  <files>test/test_named_styles.py</files>
  <action><![CDATA[
    Run `mkdir -p "$S"`. Check that `git -C $WT rev-parse HEAD` equals `<scratch>/batch-11-base.txt` and that `git -C $WT branch --show-current` prints `wp30-s32`; otherwise stop. Read `<scratch>/batch-11-impact.txt` and confirm it records the CRITICAL warnings for GlyphMapper._apply_marker_opts and GlyphMapper._apply_line_opts, the HIGH ones for _apply_fill_opts, _ci_band_style, _ci_line_restyle, _ci_pstyle and _render_ci_band, and their approval. For any symbol of E5 missing there, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout (never in $WT), append the result, and report every HIGH or CRITICAL result before editing. Check what the dependencies landed, and stop and report if any is missing:
    - `grep -n "_dash_stylelist_keys" $WT/dash_parse.mata` (S11);
    - `grep -n "def _fintensity_value\|_fill_base" $WT/dash_render.py` (S16);
    - `grep -n "def _dash_emit_note" $WT/dash_render.py` (S06);
    - `grep -n "naturally_white" $WT/dash_render.py` (S15).
    Create test/test_named_styles.py with every class and test of "TDD test stubs / Regression tests written by 32-01" and those exact names. Use the helpers named there, and write every expectation as E3's literal twoway hex, width, symbol or pattern converted through OptionTranslator.translate_lwidth, translate_msize and translate_lpattern only. Never compute an expectation through SchemeParser or GlyphMapper. Run `python3 -m pytest test/test_named_styles.py -q -n0 -p no:cacheprovider -rf > "$S/32-01.log" 2>&1`. Write `<scratch>/32-P1.14a-failure.txt` with the base sha, each FAILED line with its first assertion text, and, under "Guard tests (pass before and after)", the guards. Do not touch dash.ado, dash_parse.mata or dash_render.py, and do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/32-01.log"` prints at least 40; `grep -E '^FAILED.*(no_page_script_writes_a_style|keeps_its_mapping|spike_clstyle_is_silent)' "$S/32-01.log"` prints nothing; `test -s <scratch>/32-P1.14a-failure.txt`.]]></verify>
  <done>Every 32-01 regression test existed with twoway's literal values and failed on the unfixed tree, the guards passed, and the failure text was saved.</done>
</task>

<task type="auto" id="32-02">
  <name>Extract the named-style truth from Stata</name>
  <files>scripts/extract_named_style_truth.do, test/fixtures/named_style_truth.json</files>
  <action><![CDATA[
    Create scripts/extract_named_style_truth.do as "Stata truth" specifies, copying the header, `_meta` capture, record file and python block of S11's scripts/extract_stylelist_truth.do (S02's `DASH_REPO` form, with no maintainer path and no `arch` literal). Its comment header names WP-30 P1.14a, the fixture and the run line. Write the grids B, R, F, P, N, A and U in that order, taking the R grid's variables from E3's probe do-files and listing the 26 scheme names literally from `python3 -c "import dash_render as d;print(' '.join(sorted(d.SchemeParser._BUILTIN_NAMES)))"`. Run it with the "Run" commands, then read `$S/truth/extract_named_style_truth.log`. Check the fixture against E3: B-s2color-p3 mf `85 117 47`; R-s1mono-line-lstyle lc `0 0 0` vshortdash; F (`color(red) mstyle(p4)`) mf `255 212 0`; P01 msz `1.04166`; P14 the first copy; N02 plot 2 p4; A11 rc 198; R-stcolor-spike-clstyle unchanged. A difference is investigated and reported, never patched by hand (R7). Run `git -C $WT add -f test/fixtures/named_style_truth.json`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/named_style_truth.json'));m=d['_meta'];assert all(k in m for k in ('stata_version','born_date','dash_commit','extracted'));c=d['cases'];assert len(c)>=1350;print(len(c))"` prints the case count; `grep -c 'named_style_truth: wrote' "$S/truth/extract_named_style_truth.log"` prints 1; `grep -c "arch -arm64\|/Users/billy" scripts/extract_named_style_truth.do` prints 0; `git -C $WT ls-files test/fixtures/named_style_truth.json` prints the path.]]></verify>
  <done>twoway's resolved styles for every bundle, type-by-option role, precedence, p(), numbering, abbreviation and other-name case were recorded in a stamped fixture staged with git add -f.</done>
</task>

<task type="auto" id="32-03">
  <name>Add fixture-driven tests and base digests</name>
  <files>test/test_named_styles.py, test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[
    Add every test of "Added by 32-03" to test/test_named_styles.py, reading test/fixtures/named_style_truth.json once at module level. In test/test_unsupported_report_is_true.py, add the ten `LIVE_VALUES` rows of the same subsection in alphabetical place, each with a one-line comment `# WP-30 P1.14a: drawn, p1-p15`. Do not remove the PLOT_VALUES rows yet (32-12 does). Write a scratch script, `$S/digests.py`, never committed, that renders every case of `test_mode_parity.CORPUS` saved (through `normalise_bokeh_html`) and served (its document JSON with ids normalised as test_mode_parity does), and writes `{case: [sha_saved, sha_served]}` to `$S/32-base-digests.json` (with `--compare <file>` it renders only the cases named in that file and prints `identical: <N> cases`, or each differing case and exits 1). Run it on the unmodified tree. Run `python3 -m pytest test/test_named_styles.py test/test_unsupported_report_is_true.py -q -n 6 -p no:cacheprovider -rf > "$S/32-03.log" 2>&1` and append the new FAILED lines to `<scratch>/32-P1.14a-failure.txt`, with the fixture guards under the guard heading. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/32-03.log"` exceeds the count in `$S/32-01.log`; `python3 -m pytest test/test_named_styles.py -q -n0 -k TestTheFixture` passes; `python3 -c "import json;print(len(json.load(open('$S/32-base-digests.json'))))"` equals the CORPUS length at base.]]></verify>
  <done>The fixture-driven tests and the LIVE_VALUES rows failed on the unfixed tree, and the base digests of the parity corpus were saved.</done>
</task>

<task type="auto" id="32-04">
  <name>Declare and serialise the style options</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In dash.ado apply TR-32.1, TR-32.2 and TR-32.5, finding each place by the text E1 quotes:
    - `_dash_parse_plot_opts`'s syntax: the four `(string asis)` changes and the new declaration line after `LStyle(…) MLStyle(…) MLPattern(…)`;
    - delete the four pending lines;
    - the six `sreturn local` lines after `sreturn local mlstyle`;
    - in `_dash_plot_opts_to_json`, the six keys after `mstyle lstyle mlstyle`, the `_dash_p_drops` local with its per-line comments, and the `s(p)` test read by value (`mata: st_local("_p_on", strofreal(strtrim(st_global("s(p)")) != ""))`), skipping a dropped key inside the loop;
    - `_dash_fold_typed`: `pstyle` out of `ci_drawn`, and the area/rarea and pcarrow/pcbarrow/pcarrowi blocks;
    - `_dash_fold_cl`: `sreturn local clstyle ""`.
    Each edited program keeps `version 19`. Then grep the parser and the folds for a local named `p` (`grep -n "local p \|\`p'" `) and stop if one exists besides the new option.
  ]]></action>
  <verify><![CDATA[`grep -nE "_dash_pending' (pstyle|lstyle|mstyle|mlstyle)\"" dash.ado` prints nothing; `grep -n 'ASTyle(string asis)' dash.ado` prints one line; `python3 -m pytest test/test_abbreviations.py test/test_help_conformance.py -q -n0 -p no:cacheprovider -k "declar or shadow or prefix or fold"` reports 0 failed.]]></verify>
  <done>dash.ado declared the ten options with twoway's minimums, wrote them per series, dropped twoway's discarded keys under p(), and named the outline and arrowhead styles where they are not drawn.</done>
</task>

<task type="auto" id="32-05">
  <name>Extend the stylelist keys and repeats</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    In dash_parse.mata, apply TR-32.3 and TR-32.4. Append the nine names to `_dash_stylelist_keys()`'s literal and update its comment. Add the `"F"` category to `_dash_rep_cat` with its comment line, add the `"F"` branch to `_dash_rep_merge` directly after `cat = _dash_rep_cat(key)`, and reword the :5170 comment. The header index (`*!` block) changes only in `_dash_rep_reduce`'s description: "(the last copy, the first for p(), or the copies merged)". Run the driver for test/test_twoway_option_parity.cscript and test/test_varlist_expansion.cscript (`printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" <script> > "$S/run_<script>.do"` and the slot wrapper).
  ]]></action>
  <verify><![CDATA[Both logs end without `FAIL` except SL-01 (flipped by 32-17) and the NP cases not yet written; `grep -n 'return("F")' dash_parse.mata` prints one line; `python3 -m pytest test/test_file_headers.py test/test_program_coverage_map.py -q -n0` reports 0 failed.]]></verify>
  <done>The stylelist key list held the nine named-style options, and a repeated p() kept its first copy in Mata.</done>
</task>

<task type="auto" id="32-06">
  <name>Add the style bundle resolver</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `SchemeParser.style_bundle(self, cls, name)` directly after `plot_line_width`, exactly as TR-32.6 defines it, with a docstring citing research p1-14 §3, E3's B grid and the security rule. If S24 left a hollow or sm* marker read inline in `map_scatter`, move it into one SchemeParser method that both call, changing nothing map_scatter draws. Add the `'SchemeParser.style_bundle'` key under the S32 anchor of test/function_test_map.py. Run `python3 -m pytest test/test_named_styles.py -q -n 6 -p no:cacheprovider -k TestStyleBundle`.
  ]]></action>
  <verify><![CDATA[`TestStyleBundle` reports 0 failed (all 390 plus the marker-default nodes); `python3 -m pytest test/test_function_test_map.py -q -n0` passes.]]></verify>
  <done>SchemeParser resolved p1-p15 to twoway's marker, line and area bundles for all 26 shipped schemes from the integer index alone.</done>
</task>

<task type="auto" id="32-07">
  <name>Write the factor-order plan methods</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add to GlyphMapper, directly after `_ci_line_restyle`: `_STYLE_FACTORS`, `_STYLE_UNREAD_NOTE`, `_style_plan`, `_style_options`, `_style_value`, `_style_restyle` and `_style_unresolved`, exactly as TR-32.7 defines them. There are no nested defs and no module-level names. Each docstring cites the register row and E3's measurement. Add their five keys under the S32 anchor of test/function_test_map.py, in alphabetical order. Run `python3 -m pytest test/test_named_styles.py -q -n0 -p no:cacheprovider -k "shadowed or only_named_roles or falls_back"`.
  ]]></action>
  <verify><![CDATA[The selected unit tests pass; `python3 -m pytest test/test_function_test_map.py test/test_statistical_helpers.py -q -n0 -k "every or Served"` reports 0 failed.]]></verify>
  <done>GlyphMapper computed each role's winning bundle and the explicit options it shadows in twoway's factor order, with an empty plan that returns the options unchanged.</done>
</task>

<task type="auto" id="32-08">
  <name>Confirm the approval for the two CRITICAL appliers</name>
  <files>none</files>
  <action><![CDATA[
    Before 32-09 edits `_apply_marker_opts` and `_apply_line_opts` (CRITICAL; E5), confirm that the batch-11.0 approval recorded in `<scratch>/batch-11-impact.txt` covers both symbols (index 11.0 lists them as expected CRITICAL; E4). The approval is obtained at the batch base, before the worktrees are cut, never mid-batch (A151's lesson). If it does not cover both, stop and report; do not wait inside the worktree. In the progress output, state the empty-plan guarantee (`_style_restyle` returns at once and `_style_options` returns the same dict when no style key holds a value) and the identity checks of TR-32.16.
  ]]></action>
  <verify><![CDATA[`grep -n "_apply_marker_opts" <scratch>/batch-11-impact.txt` and `grep -n "_apply_line_opts" <scratch>/batch-11-impact.txt` each print a line, and the file records the batch-11.0 approval.]]></verify>
  <done>The batch-11.0 approval for editing the two CRITICAL appliers was confirmed.</done>
</task>

<task type="auto" id="32-09">
  <name>Restyle and filter in the three appliers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-32.8: the two leading statements in `_apply_marker_opts` and `_apply_fill_opts`, and in `_apply_line_opts` the `role="line"` keyword with the `role is None` guard. Leave every other line of the three bodies as it is. Extend each docstring by one paragraph naming the factor order and D-32e. Run test/test_glyphs.py, test/test_graph_options.py, test/test_ci_band_style.py and test/test_varlist_expansion.py with `-q -n 6 -p no:cacheprovider`. Every failure must be a test that 32-12/32-13 flips; anything else is a defect fixed now.
  ]]></action>
  <verify><![CDATA[The four files report 0 failed apart from E4's listed pins; `python3 -m pytest test/test_varlist_expansion.py -q -n0 -k single_y_output` passes.]]></verify>
  <done>Every glyph that reaches an applier took its role's named style once, before any explicit option, and with no named style the appliers behaved exactly as before.</done>
</task>

<task type="auto" id="32-10">
  <name>Fix the ten pre-applier mappers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-32.9 to map_area, map_rarea, map_bar, map_rbar, _histogram_quads, map_dropline, map_rcapsym, map_scatteri, map_pcarrow and map_pcbarrow, finding each by E2's quoted text. In the five fill mappers, S16's `_fill_base`/`_f` defaults go through `_style_value`, the restyle comes right after the glyph is built, and the colour reads are split per role. map_dropline and map_rcapsym are restructured so the explicit colour is set after the restyle. map_scatteri, map_pcarrow and map_pcbarrow get the restyle line. Keep every line S14, S16, S24 or S30 wrote. Run `python3 -m pytest test/test_named_styles.py -q -n 6 -p no:cacheprovider -k "FactorOrder or Astyle or Numbering or BrushedAndMutedCopies"`. If `TestBrushedAndMutedCopies` fails because S08's sync does not copy a property `_style_restyle` sets (`marker`, `line_dash`), or does not follow a mapper's restyle, stop and report: S08 owns the sync (A37).
  ]]></action>
  <verify><![CDATA[`test_area_color_then_pstyle_is_red`, `test_dropline_color_then_pstyle_is_red`, `test_scatteri_mcolor_then_pstyle_is_red` and `test_pcarrow_lcolor_then_pstyle_is_red` and `TestBrushedAndMutedCopies::test_the_copies_carry_the_named_style` pass in both modes; `python3 -m pytest test/test_intensity_blend.py test/test_glyphs.py -q -n 6` reports 0 failed.]]></verify>
  <done>The ten mappers that read a colour before their applier took the named style first and the user's colour after it, as twoway orders them.</done>
</task>

<task type="auto" id="32-11">
  <name>Route the outline roles and ci types</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-32.10: the `role="aline"` keyword at the thirteen E2 call sites, `role=None` at map_area's border, the `role` keyword on map_line, and map_rconnected's two calls. Then TR-32.11: `_ci_pstyle` reading `p` first, `_render_ci_band`'s `_nopstyle`, `_ci_band_style`'s plan step and per-role reads (keep `_col` as the nested helper the map names), and `_ci_line_restyle`'s closing restyle. Then TR-32.12 in `_dash_plot_style_indices`. Run `python3 -m pytest test/test_named_styles.py test/test_ci_band_style.py test/test_ci_plot_index.py -q -n 6 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[`TestRoles`, `TestNumbering` and `TestP` report 0 failed; test_ci_band_style.py and test_ci_plot_index.py report 0 failed except the `astyle` rows that 32-13 adds to the comparison.]]></verify>
  <done>Each plot type's lines took the style twoway styles them with, the ci band and fit line merged the named styles in order, and pstyle(p#) and p(p#) set the layer's own plot index on every path in both modes.</done>
</task>

<task type="auto" id="32-12">
  <name>Flip the pending-list and help pins</name>
  <files>test/test_unsupported_report_is_true.py, test/test_help_conformance.py, test/test_help_examples.py</files>
  <action><![CDATA[
    Flip E4's rows, each with a comment `# Flipped (WP-30 P1.14a): <old> -> <new>: <why>`:
    - remove PLOT_VALUES `lstyle`, `mlstyle`, `mstyle` and `pstyle` (their LIVE_VALUES rows exist from 32-03);
    - move the pins 48 to 44 (pending, :240) and 169 to 175 (declared, :607) in test_unsupported_report_is_true.py;
    - move both 48 pins to 44 in test_help_conformance.py (:598, :603);
    - in test_help_examples.py (:124), change the key `'dash scatter mpg weight, pstyle(p3) t1title("hi")'` to `'dash scatter mpg weight, mlpattern(dash) t1title("hi")'`.
    The help itself changes in 32-18. Append each `Flipped:` line to `$S/32-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unsupported_report_is_true.py -q -n 6 -p no:cacheprovider` reports 0 failed; test_help_conformance.py and test_help_examples.py fail only on the help text 32-18 writes.]]></verify>
  <done>The pending-list, declaration and help-example pins expected the ten options as drawn, each flip recorded with its reason.</done>
</task>

<task type="auto" id="32-13">
  <name>Flip ci and stylelist pins, extend parity</name>
  <files>test/test_ci_band_style.py, test/test_stylelists.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    In test/test_ci_band_style.py, remove `"astyle"` from `_NOT_COMPARED` (:70) and rewrite its comment so it names only `ciplot`. In S11's test/test_stylelists.py, remove `pstyle mstyle lstyle mlstyle` from `_NOT_YET` and add the nine names to `_STYLE_KEYS`, each with a flip comment. Append TR-32.17's three `_case` entries at the end of `CORPUS` in test/test_mode_parity.py. Append the `Flipped:` lines to `$S/32-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ci_band_style.py test/test_stylelists.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The ci band's astyle case was compared with twoway, S11's lists held the nine named styles, and the parity corpus drew the named styles alike in both modes.</done>
</task>

<task type="auto" id="32-14">
  <name>Fill the S32 truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Between S01's `S32 start` and `S32 end` lines, write NP-01..NP-09 as "Stata truth / Truth block" specifies. Put the python helpers `_s32_page`, `_s32_app` and `_s32_svg` and the program `_s32_case` (opening `version 19`) directly above `* ==== S32 P1.14a:`, never inside another block. Set the scheme per case and restore it at the end, write only under `` `w30_work' ``, and erase those files before the end line. Run `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_test_wp30_truth.do"` then `WP30_ONLY=S32 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_wp30_truth.do"`. If `python_exec` was dropped (exit 222, a SKIP), restore it and run again, since a skip is not a pass.
  ]]></action>
  <verify><![CDATA[`grep -c 'NP-0[1-9] PASS' "$S/run_test_wp30_truth.log"` prints 9, `grep -c 'ALL CHECKS PASSED' "$S/run_test_wp30_truth.log"` prints 1, and the log holds no `FAIL` or `SKIP`; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -k Wp30` passes.]]></verify>
  <done>The truth block compared twoway's drawing with the saved page, the served app and the served app after a filter move for nine named-style cases, all passing.</done>
</task>

<task type="auto" id="32-15">
  <name>Add the area cscript cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_abbreviations.cscript, test/test_parser.cscript</files>
  <action><![CDATA[
    Append NP-20..NP-25 to test/test_twoway_option_parity.cscript, NP-30..NP-33 to test/test_abbreviations.cscript and NP-40..NP-42 to test/test_parser.cscript, as one contiguous run at the end of each script's last case block (R1). Each case is as "TDD test stubs / cscripts" describes. Read every spec with `mata: st_global("dash_json_<g>")` by value, and use the script's own pass/fail tally. Extend each script's `*!` header with its NP lines. First run `grep -n "NP-" test/*.cscript test/*.py test/*.do` and confirm only S32's ids exist. Run each script through the driver.
  ]]></action>
  <verify><![CDATA[Each of the three logs prints PASS for every NP case and ends with the script's ALL PASSED line; `grep -c "NP-2[0-5] PASS" "$S/run_test_twoway_option_parity.log"` prints 6.]]></verify>
  <done>The spec, the folds, the first-copy rule and twoway's abbreviations were pinned in the area certification scripts.</done>
</task>

<task type="auto" id="32-16">
  <name>Flip the pinned cscript cases</name>
  <files>test/test_ci_band_options.cscript, test/test_help_claims_8.cscript, test/test_statistical_options.cscript</files>
  <action><![CDATA[
    Flip, editing only the named case:
    - CB-03: drop `pstyle()` from the named list and add a check that it is not named; keep `psty(p3)` in the command.
    - CB-04's `al(red)` half: `r(note)` is 0, there is no `alcolor`, and the spec holds `"alstyle":"red"`. Rewrite its header line and PASS text.
    - HC8-01: the help example and its expected note become `mlpattern(dash) t1title("hi")` / `mlpattern() t1title()`, in the note form at base.
    - HC8-02: remove the four names from `p_opts`/`p_names` and change "48" to "44".
    - HC8-07: `mlpattern(HC8SECRETVALUE)` replaces `pstyle(...)`.
    - LB-19: reword to "p(800) is p(), never pwidth()" and add the check that the spec holds `"p":"800"`.
    Update each header comment. Run each script through the driver and append the `Flipped:` lines to `$S/32-flips.txt`.
  ]]></action>
  <verify><![CDATA[The three logs show CB-03, CB-04, HC8-01, HC8-02, HC8-07 and LB-19 PASS and no FAIL; HC8-01 passes only after 32-18 (rerun then).]]></verify>
  <done>The certification cases that pinned pstyle() and al() as ignored pinned twoway's reading instead, each with its reason.</done>
</task>

<task type="auto" id="32-17">
  <name>Pin the per-y named-style lists</name>
  <files>test/test_varlist_expansion.cscript</files>
  <action><![CDATA[
    Flip SL-01's word count by +9 from its value at base, with a comment naming the nine keys. Append NP-46..NP-48 after the last SL case as one contiguous run, each reading `dash_json_<g>` per series by value. Run the script through the driver.
  ]]></action>
  <verify><![CDATA[`grep -c "SL-01 PASS\|NP-4[6-8] PASS" "$S/run_test_varlist_expansion.log"` prints 4 and the log holds no FAIL.]]></verify>
  <done>Each y of an expanded varlist got its own named-style element, and p() was written whole to every series.</done>
</task>

<task type="auto" id="32-18">
  <name>Document named styles in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Edit only these paragraphs (R3):
    - :2281-2282: `{cmd:pw()} is its shortest spelling ({cmd:p()} is {cmd:twoway}'s own {cmd:p()} option, the whole plot's style; see {help dash##namedstyles:Named styles})`.
    - :2596-2600: the fitarea options are named on other types, `pstyle()` no longer is; and `astyle()`, `alstyle()`, `bstyle()`, `blstyle()` and `lstyle()` style the band in twoway's order.
    - :3611-3612: the Unsupported example becomes `mlpattern(dash) t1title("hi")` with the note line in the base's form.
    - :3647-3655: delete the Unsupported "Named styles" entry.
    - Add a `{marker namedstyles}` paragraph at the end of Marker and Transparency Options, before `{marker scheme}`. It covers: the ten options and their minimums; `p1`-`p15`; the factor order with three examples; `p()` (applied last, first copy, one name, label text and `connect()` kept); lists per y; which line each type takes; the plot index; and what is not drawn yet (other names, with the note; the outline on area and rarea; arrowheads on the pc arrows).
    Use only `{cmd:}` for option names in the new paragraph, never `{opt}`. Run test/test_help_conformance.py, test/test_help_examples.py, test/test_help_claims_*.py and `TestTheHelp`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_help_examples.py test/test_named_styles.py -q -n 6 -p no:cacheprovider -k "help or Help or conformance or examples"` reports 0 failed; `grep -c '{marker namedstyles}' dash.sthlp` prints 1; HC8-01 rerun passes.]]></verify>
  <done>The help documented the named styles, twoway's order, p() and what is not drawn yet, and no longer listed them as unsupported.</done>
</task>

<task type="auto" id="32-19">
  <name>Run checks, identity and full suite</name>
  <files>none</files>
  <action><![CDATA[
    Run every changed pytest file with `-n 6 -p no:cacheprovider`. Run every changed cscript through the driver (`WP30_ONLY=S32` for the truth script). Run `python3 $S/digests.py --compare $S/32-base-digests.json` on the fixed tree; any difference stops the task and is a defect of this section (TR-32.16b). Then run `git -C $WT merge --no-edit main`, expecting `Already up to date.` (E9), and one full suite through the queue: `<scratch>/full_suite_queue.sh $WT <scratch>/32-full-1.log` in the background, waited on with Monitor until its `exit=` line. A known flaky failure is rerun once alone (E6) and recorded in `<scratch>/batch-11-flaky.txt`.
  ]]></action>
  <verify><![CDATA[`python3 $S/digests.py --compare $S/32-base-digests.json` prints `identical:` with the base case count and exits 0; `tail -1 <scratch>/32-full-1.log` is `exit=0` and the log shows 0 failed.]]></verify>
  <done>Every changed test and certification script passed, the parity corpus drew byte-identically without named styles, and one full suite was green.</done>
</task>

<task type="auto" id="32-20">
  <name>Close the entry and commit</name>
  <files>BUGS.md, test/test_tracking_documents.py, CHANGELOG.md</files>
  <action><![CDATA[
    Close BUGS.md's `P1.14a` entry in place with Notes "Text for the closing task": `- [x]` and the Resolution line. Delete only the `"P1.14a"` line of `WP30_OPEN` in test/test_tracking_documents.py (R5), and replace only `<!-- WP-30 P1.14a -->` in CHANGELOG.md with the Notes line (R4). Run `python3 -m pytest test/test_tracking_documents.py -q -n0`. Check scope with `git -C $WT status --porcelain` and `git -C $WT diff --cached --name-only` (no CLAUDE.md, .gitignore, AGENTS.md, .ultraplan/ or *.html). Write the message to `$S/msg.txt` per the Commit boundary, with every line of `$S/32-flips.txt`. Run G7 on it, `git -C $WT add` the changed files, `git -C $WT add -f test/fixtures/named_style_truth.json`, confirm `git -C $WT branch --show-current` prints `wp30-s32`, then `git -C $WT commit -F $S/msg.txt`, and run G7 on `git log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`grep -c '^    "P1.14a": "' test/test_tracking_documents.py` prints 0; `grep -c 'WP-30 P1.14a -->' CHANGELOG.md` prints 0; `git -C $WT log -1 --format=%s` ends `(WP-30 P1.14a)`; `git -C $WT log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The P1.14a entry, its WP30_OPEN key and its CHANGELOG marker were closed, and the one commit was made on wp30-s32.</done>
</task>

## Section completion criteria

- One commit on `wp30-s32` with subject ending `(WP-30 P1.14a)`, made after a green full run, with no CLAUDE.md, .gitignore, AGENTS.md, plan or HTML file staged.
- AC-32.1 to AC-32.7 hold.
- BUGS.md's entry is closed in place, the `WP30_OPEN["P1.14a"]` line is gone, and the CHANGELOG marker is replaced in place.
- The fixture is committed with `git add -f` and its `_meta` stamp.
- The registry tests (R2 list) are green: function_test_map, program_coverage_map, served-name tests, cscript hygiene and tracking documents.
- No copy-list tuple, `_make_figure_body`, `_generate_app_source`, `_apply_mlabel_opts` or `_apply_colorvar` line changed: `git -C $WT diff <base> -- dash_render.py | grep -c "_apply_mlabel_opts(self\|_apply_colorvar(\|def _make_figure_body"` prints 0.

## Notes

### Q1 (resolved at review)

`bmlinestyle()` (register P1.14.9: "Declare and serialise; noted until P2.9 / P2.8") is S36's. Section 36's binding readings take it beside `dstyle()`/`dlstyle()`. Until S36 lands, it stays named as typed.

### Text for the closing task (32-20)

**BUGS.md, P1.14a** (closed in place, `- [x]`):

`- Resolution: Fixed <ddmonyyyy> (WP-30, P1.14a). The named styles p1 to p15 are drawn on every plot type, as twoway draws them. pstyle(), lstyle(), clstyle(), mstyle(), mlstyle(), astyle(), alstyle(), bstyle(), blstyle() and p() are declared with twoway's abbreviations and written per series. The nine stylelists split across an expanded varlist, and p() is one name whose first copy wins (_dash_rep_cat "F"). Under p() the spec drops every style option twoway discards, the label style included. SchemeParser.style_bundle resolves p# to twoway's marker, line and area bundles from the plot index alone. GlyphMapper._style_plan applies them in twoway's factor order: each glyph takes its role's bundle once, before any explicit option (in the three appliers, and right after the glyph is built in map_area, map_rarea, map_bar, map_rbar, _histogram_quads, map_dropline, map_rcapsym, map_scatteri, map_pcarrow and map_pcbarrow), and an explicit option before the style in that order is not applied. Each type's lines take the style twoway styles them with: the connecting line on the line types, the outline on spike, range, pc and bar types. The ci band and fit line merge the styles (_ci_band_style, _ci_line_restyle). _dash_plot_style_indices moves a pstyle(p#) or p(p#) layer to plot #, reaching scatteri, pci, pcarrowi and function. The saved page and the served app draw the same, before and after a filter move, and the brushed-away and muted copies of a styled glyph carry its style through section 8's sync. Pinned by test/test_named_styles.py::TestPstyle::test_scatter_pstyle_p3_is_p3, test/test_named_styles.py::TestFactorOrder::test_area_color_then_pstyle_is_red, test/test_named_styles.py::TestFactorOrder::test_each_measured_row, test/test_named_styles.py::TestP::test_p_overrides_mcolor, test/test_named_styles.py::TestRoles::test_against_stata, test/test_named_styles.py::TestStyleBundle::test_against_stata, test/test_named_styles.py::TestNumbering::test_scatteri_and_function_take_the_index, test/test_named_styles.py::TestAfterAFilterMove::test_served_style_survives_a_move, test/test_named_styles.py::TestBrushedAndMutedCopies::test_the_copies_carry_the_named_style, test/test_named_styles.py::TestTheEmptyPlanIsInert::test_the_corpus_draws_the_same_with_the_plan_bypassed, test/test_wp30_truth.cscript NP-01, test/test_twoway_option_parity.cscript NP-20, test/test_varlist_expansion.cscript NP-46; fixture test/fixtures/named_style_truth.json. Residual, deferred (WP-30): names other than p1-p15, twoway's default attributes for an unknown name, and dstyle()/dlstyle() are section 36's; the outline half of a named style on area and rarea is P2.12; arrowheads styled by mstyle() are P2.8; pst(), ps() and as(), which twoway refuses, stay named (P2.21).`

**CHANGELOG.md**, `<!-- WP-30 P1.14a -->` in `### Results that change` replaced by:

```
- The named styles `p1`-`p15` are drawn on every plot type, as twoway draws them: `pstyle()`, `lstyle()`, `clstyle()`, `mstyle()`, `mlstyle()`, `astyle()`, `alstyle()`, `bstyle()` and `blstyle()` were ignored with a note (`pstyle()` was drawn only on the four ci fits); `dash scatter mpg weight, pstyle(p3)` drew `#1a476f` and now draws p3's `#55752f` under s2color. A named style and your own options combine in twoway's order: `mcolor(red) pstyle(p3)` is red and `color(red) mstyle(p4)` is p4. `p()`, named in the note before, is twoway's whole-plot style: `mcolor(red) p(p3)` draws p3, discarding the other style options. `al()` and `bl()` are now `alstyle()` and `blstyle()`, as in twoway (they were named as typed). A name other than `p1`-`p15` is noted and the layer keeps its own style. (WP-30, P1.14a)
```

### Traps for the executor

- **Restyle once, then read.** A glyph's role bundle goes on before any explicit option is read for it. Calling `_style_restyle` after an explicit read overwrites the user's colour; the critic-2 tests catch this.
- **The role is the type's, not the glyph class's.** rline and rconnected draw Bokeh `Line`s, but take `aline` (E3). The connected line takes `line`. `clstyle()` is cleared off non-cl types in dash.ado, so the renderer never sees it there.
- **Do not read a colour back from the glyph.** S16's `_apply_fill_opts(base=…)` re-blends from `_fill_base`, so `_fill_base`'s default must come from `_style_value`, never from `r.glyph.fill_color`.
- **Byte identity.** Never add a constructor keyword that was not passed before (Bokeh serialises a set default). Set bundle attributes only when the role has a winner.
- **`_dash_plot_style_indices` is copied by source.** Use an inline `re.fullmatch` literal, no module constant. `n` must advance exactly as before.
- **The ci types read `p`/`pstyle` in `_ci_pstyle` only.** Every other consumer gets `_nopstyle`, or the interim note fires twice.
- **asis values.** `pstyle("p3")` arrives quoted in s(). S11's pick strips one level, and the renderer strips blanks only.
- **python_exec.** A cscript SKIP (exit 222) is a dropped `python_exec`, not a pass: restore it and run again (memory note).

### Shared files and merge rules

- dash_render.py: R2 (no copy-list change) and R12 (S32 is batch 11's editor of `_apply_marker_opts`, `_apply_line_opts` and `_apply_fill_opts`).
- dash.ado and dash_parse.mata: R6 (no option key or Mata function shared with S31/S33).
- Cscripts: R1 (own block; NP runs at the end of each area script; S31 and S33 keep merge order if they append to one of them).
- dash.sthlp: R3 (Statistical Layer Options :2282 and :2596-2600; Unsupported; a new paragraph in Marker and Transparency Options, which no batch-11 partner edits).
- CHANGELOG.md: R4. BUGS.md and test_tracking_documents.py: R5. Fixture: R7. Parity corpus: R8. Flips: R9.
- Pins: R10. Plot pending 48 → 44 and declared 175 are S32's moves in batch 11; the merger re-derives them if a partner moved one too.

### For later sections

- **S36:**
  - extends `SchemeParser.style_bundle` with the curated name table (IR-14) and makes an unknown name return twoway's default attributes with twoway's note;
  - `_style_unresolved` and `_STYLE_UNREAD_NOTE` may then be retired;
  - adds `dstyle dlstyle` to the declarations, the sreturn block, the JSON key list, `_dash_stylelist_keys()` and `_dash_p_drops`;
  - adds `bmlinestyle` too (Q1, taken by S36).
- **S38/S39:** call `self.scheme.style_bundle("area"|"line", name)` without editing it.
- **S43:** composes a bare `*#`/`%#` with `GlyphMapper._style_value(options, role, attr, default)` as the site's base.
- **S45:** under `recast()`, the role table (D-32c) follows the drawn type.

### Notes for the closeout (A145; S58 writes them)

- **GAPS2.md B11** (also D6, which has no heading of its own): Closed only when P1.14a and P1.14b are both closed. Its Tracked line names both commits.
- **REMAINING.md:** the named-style words in the S09 style lists at :133-140, :149, :448-452, :818-821 and :892-893 (REM-§2-S09-lstyle, -mstyle, -areastyle, REM-S09-73-namedstyles, REM-05-04-S09-g) are drawn for p1-p15. `dstyle`, `dlstyle` and `bmlinestyle` stay listed until S36.
- **TWOWAY_COVERAGE_AUDIT.md (AUDIT-29, AUDIT-30):** the rows at :112, :114, :116, :169 and :173 lose "mstyle()/mlstyle() bundles … not implemented", "Named lstyle() bundles absent" and the named-style entries of the ignored list.
- **DROPIN-REMAINING.md P1.14:** part a closed by this commit.
- **test/fixtures/rejected_options.json:** the rows lstyle, mstyle, mlstyle, astyle, bstyle and pstyle (disposition "implement-S09-style") become honoured for p1-p15.
- **Residuals to file:**
  - P2.12 (area/rarea outline of a named style);
  - P2.8 (arrowheads by `mstyle()`);
  - P2.21 (`pst()`, `ps()`, `as()` refused by twoway, named by dash);
  - P3.7 (`abbrev_truth.json` still records `mls` as mlabsize);

### Line numbers

Every number above is at `c96facd`. Sections 01-31 move them, so each task locates code by the quoted text and by function name.
