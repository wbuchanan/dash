# Section 43: Default colour and opacity at every colour site (P1.13 part b)

> Part of: WP-30 · Items: P1.13 part b (entry `P1.13b`; GAPS2-D7-b; GAPS2-D7 recorded closed) · Risk: yellow · Batch: 15 (merge order S42, S43, S44) · Depends on: 16, 30, 31, 32, 38, 39 · Blocks: 56 · Tasks: 12, 1 commit · Case prefix: BI

## Review amendments

- Fixed (major, Q-43.1): checked against section-38-region-styling.md. S38's region reader is `_dash_region_spec` (copy-listed, reached from `_dash_apply_regions` in both modes), and its `_read(arg, role)` step holds the role's `base_hex` for S43 (TR-38.2, "The S43 hook"). TR-43.9 read the base from `fig.border_fill_color`/`fig.background_fill_color`, which S38 sets to composited outputs (a second blend), and stopped on a condition that cannot arise. It now passes `base=base_hex` in that step and writes the alpha to the role's setting; Risk 4, D-43c, E6, 43-09, the landing list, the Resolution and Notes follow, and the (a)/(b) maintainer question and its residual are gone.
- Fixed (major): `$S` was shared with S42 and S44, which run in parallel with the same log names; it is now `<scratch>/s43`, with the batch files read from `<scratch>`.
- Fixed (minor): `_dash_graph_color` has no region caller after S38 (its five calls were the replaced blocks), so it is edited only if 43-09's grep finds a colour-site caller. D-43a no longer has `stata_colour` call a GlyphMapper method (S30's multiplier step applies the rule). The truth block states TR-01.10's form.
- Checked: `_textbox_color` :4839 and its five callers, `_resolve_kpi_color` :17054, `_dash_refline_draw` :26327, the direct `translate_mcolor` sites of E1; S30's `stata_colour`/`parse_color_alpha(**ctx)` and S32's `_style_value(options, role, attr, default)` contracts. No function is shared with S42 or S44; S43 is batch 15's only applier editor (R12). The marker sits in "Results that change" only, as Appendix A lists P1.13b.
- Rejected: refusing nothing new (M5) is right: twoway accepts a bare `*#`/`%#` at every site.
- The review pass applied both lenses.

**Binding readings applied in this file** (M1, M5, M6; register P1.13.1, P1.13.4, P1.13.5, P1.13.6, X.1; index A138, A149, R2, R3, R12):
- **M1 / D5 a.** A bare `*#` and a bare `%#` take the site's own colour before intensity, composed with the object's intensity blend (S16) and a named style's base colour (S32), as twoway draws them; every look change is a CHANGELOG "Results that change" line.
- **P1.13.5 (folded here by A138's split).** Every direct `translate_mcolor` site keeps a `%#` opacity and draws an unknown colour black with the note (S30's D-30c left these sites to S43). The `""`→black map is already gone (S30, D-30g).
- **P1.13.4.** Bare `*#` on filled layers composes with S16's opaque blend, which landed in batch 6.
- **M5.** Nothing is newly refused: twoway accepts a bare `*#`/`%#` at every site. **M6.** A bare form is silent where twoway is silent; only an unknown colour is noted.
- **R12.** S43 is batch 15's one editor of `_apply_marker_opts`, `_apply_line_opts`, `_apply_mlabel_opts` and `_apply_fill_opts`. It edits neither `_make_figure_body` nor `_generate_app_source` (S42 is the template editor), nor `ServerAppBuilder._shared_stat_lines` (manifest note).
- **R2 row S43.** No copy-list entry is added: every function edited is already listed (`_textbox_color` :33360, `_resolve_kpi_color` :33393, `_dash_refline_draw` :33383; S38's `_dash_region_spec` at S38's place; `_dash_graph_color` in `_shared_stat_lines` :33542, if edited at all); the classes travel by source. S43 therefore adds no new module-level function.

**Section decisions (this file).**
- **D-43a. One rule, one place.** `OptionTranslator.stata_colour` gains keyword-only `base=None`. When the value has no colour of its own (a bare `*#`, `%#` or both) and `base` fullmatches `#[0-9a-fA-F]{6}`, the colour is `base`, then S30's own multiplier step (the rule S16's `GlyphMapper._blend_intensity` applies, with the reader's `naturally_white`), with the value's opacity; status `"ok"`. `stata_colour` calls no GlyphMapper method. Without a usable `base` the answer is S30's (`hex` None, the site keeps its colour). `translate_mcolor`, `translate_lcolor` and `parse_color_alpha` already pass every keyword to `stata_colour` (S30 TR-30.6), so `base=` reaches it with no signature change.
- **D-43b. Each site passes the colour it would draw without the option**, read where the site already holds it, never re-derived: an applier's `_style_value` default (S32), the fill mapper's `_fill_base` (S16), the axis object's or figure's current property (S31, S38), the scheme attribute of the xyline (S39), the textbox's scheme colour, the KPI's default.
- **D-43c. Opacity at text, axis and region sites.** A `%#` sets the site's alpha property (`text_alpha`, `major_label_text_alpha`, `axis_line_alpha`, `line_alpha`, `fill_alpha`; at the graph and plot regions the role's `fill_alpha`/`line_alpha` in S38's settings, which S38 composites into an opaque `border_fill_color`/`background_fill_color` and an outline alpha); none is set when the value carries no `%`, so a scheme's own opacity (sttrans) is kept, as twoway keeps it.
- **D-43d. `_textbox_color` keeps its signature.** It gains keyword-only `base=None, colours=None, with_alpha=False`; with `with_alpha=True` it returns `(hex or default, alpha)`. Its five callers pass the base and ask for the alpha. No new name is added (R2).
- **D-43e. The KPI.** `color()`'s base is the card's default text colour (its `default` argument); `bgcolor()` has no colour of its own to adjust (its default is `""`), so a bare form there keeps the default, silently. The KPI's case-insensitive lookup and CSS leniency (S30, P1.13.2) are unchanged.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:103 (P1.13) and S01's entry `P1.13b`: "A bare *# or %# colour, such as mcolor(*.5), is refused or loses the site's default colour, where twoway adjusts that default." At `c96facd` `*.5` is refused at every site (research `.ultraplan/wp30/research/p1-13.md` §2: `translate_mcolor('*.5')` raises; `dash scatter mpg weight, mcolor(*.5)` draws `#1a85ff` with a note under stcolor). After S30 (batch 10) the grammar reads it but returns no colour, so every site keeps its default unadjusted, silently (S30 D-30a; BR-30.13's interim). The direct `translate_mcolor` sites also drop a `%#` (critic: `translate_mcolor('red%50')` is `#ff0000`) and still draw an unknown colour in the scheme's colour with a note (S30 D-30c).

twoway (StataNow 19.5, research §3 and critic; s2color unless named):

```
mcolor(*.5)  #8da3b7 (p1 navy*.5)    stcolor #8dc2ff   sttrans #8da3b7 at opacity 0.2   s1rcolor #808000
mcolor(*2) #0d2438   mcolor(*0) #ffffff   mcolor(*255) #010304
(scatter mpg weight) (scatter price weight, yaxis(2) mcolor(*.5))       p2 #c89a9d (maroon*.5)
mfcolor(*.5) fill #8da3b7    mlcolor(*.5) outline #8da3b7, fill #1a476f    lcolor(*.5) stroke #8da3b7
bar default #486c8c   bar fcolor(*.7) #7f98ae (navy*.7, then inten80)   bar color(*.5) #a4b5c5
bar fintensity(50) fcolor(*.5) #c6d1db    area/rarea fcolor(*.5) #a4b5c5    lfitci acolor(*.5) #e0e0e0
mlabcolor(*.5) #8da3b7    mlabcolor(red%50) opacity 0.50 (sttrans: mlabcolor(red%70) 0.70)
title("T", color(*.5)) #8f96a9 (heading dknavy*.5)   s1rcolor title color(*.5) #808080
title("T", color(red%50)) opacity 0.50       graphregion(color(*.5)) #f5f9f9 (bg*.5)
xline(3000, lcolor(navy*.5)) #8da3b7   xline(3000, lcolor(%50)) #c10534 (xyline) at 0.50   lcolor(red%50) 0.50
*.5%50 and %50*.5: #8da3b7 at 0.5      text(30 3000 "Hi", color(*.5)) #808080
```

**After this section,** in the saved page and the served app, before and after every filter move, a bare `*#`, a bare `%#` and both together take the site's own colour at: markers (fill and outline, through `mcolor`, `mfcolor`, `mlcolor`, a folded `color`), lines (`lcolor`, `clcolor`, a folded `color`), fills (`fcolor`, `color`, and dash's `bfcolor`/`blcolor` on bar and rbar), CI bands, marker labels, titles, subtitles, notes, captions, axis titles and the colour key's title, `labcolor()` and the axis line, the graph and plot regions, the KPI, `xline()`/`yline()` and `colormissing()`. Every direct site keeps a `%#` and draws an unknown colour black with the note. `text()` (S56) inherits the rule through `_textbox_color`.

**Why one section.** One rule, the site's own base colour, applied once at every place a colour option is read; the reader is S30's and the blend S16's. P1.13 was split (A138): S30 owns the grammar.

**Test order and commit rule (rule 7).** One entry, one cycle, one commit `(WP-30 P1.13b)`. 43-01 and 43-02 write the fixture and every regression test, run them on the unmodified batch-15 base and save `$S/43-P1.13b-failure.txt` (no commit); 43-03 to 43-11 fix, flip and document; 43-12 closes the entry, replaces the marker and commits after one full run.

## Risk: [yellow] — five CRITICAL symbols, every colour site, one shared rule

**Why.**
- CRITICAL (manifest notes; research §6): `GlyphMapper._apply_marker_opts` (12 impacted), `_apply_line_opts` (40), `_apply_mlabel_opts` (16), `_textbox_color`, `_resolve_kpi_color`. `OptionTranslator.translate_mcolor` is CRITICAL too (26) but is not edited; `stata_colour` is (S30's).
- HIGH: `_apply_fill_opts`, `_ci_band_style`, `_blend_intensity` (called, not edited).
- UNKNOWN (dispatch through `_dash_glyph_dispatch`'s table, confirmed by grep): `map_bar`, `map_rbar`, `map_area`, `map_rarea`, `map_dropline`, `map_rcapsym`, `map_scatteri`, `map_pcarrow`, `map_pcbarrow`.
- LOW: `_dash_graph_color` (+5 emitted calls in the template), `_dash_refline_draw` (3), `_histogram_quads`, `_apply_colorvar`; `_dash_apply_axis_spec` and `_dash_apply_scale_look` (S31's; HIGH per S31).

**Risk factors.**
1. A site that reads its base back from a glyph after a blend would blend twice (S16 Notes).
2. A base taken from a scheme attribute instead of the named-style plan would ignore `pstyle(p3)` (S32).
3. sttrans and other schemes carry their own opacity; setting an alpha when the value has no `%` would drop it.
4. Region colours were set in `_make_figure_body` and in the template, which S43 may not edit (R12).
5. A `base` reaching `stata_colour` from a user-controlled path must stay hex.

**Mitigation.**
1. Fill sites pass `_fill_base` (S16's variable), never `r.glyph.fill_color`; a test runs `fcolor(*.7)` on bar and compares with twoway's `#7f98ae`.
2. Applier bases come from `self._style_value(options, role, attr, default)` (S32); `pstyle(p3) mcolor(*.5)` is a fixture probe.
3. D-43c; sttrans probes in the fixture.
4. Resolved (Q-43.1, section-38 TR-38.2): S38 replaced both blocks with one copy-listed reader, `_dash_apply_regions` → `_dash_region_spec`, whose one colour step `_read(arg, role)` holds the role's `base_hex`. S43 adds `base=base_hex` there and edits neither `_make_figure_body` nor the template. 43-09 confirms the step at `batch-15-base` and stops only if it is not there.
5. `base` is used only when it fullmatches `#[0-9a-fA-F]{6}`; every output is `#[0-9a-f]{6}` (S30's guard test is extended).

## Dependencies

- **Depends on: 16, 30, 31, 32, 38, 39.**
  - S16 (batch 6): `GlyphMapper._blend_intensity(hexval, f, naturally_white)` with the f > 1 clamp; `_apply_fill_opts(self, renderer, options, base=None, intensity=1.0)` (TR-16.6); the five fill mappers' `_fill_base`/`_f` (TR-16.7).
  - S30 (batch 10): `OptionTranslator.stata_colour(value, *, context, background, foreground, naturally_white) -> (status, hex, alpha)` (D-30a); the delegating readers; the bound translator `self.tr` that reads the graph's scheme (D-30b); `OptionTranslator.scheme_colour_context(scheme)`; black-on-unknown at applier sites; `_textbox_color`, `_dash_graph_color`, `_dash_refline_draw`, `_resolve_kpi_color` through the grammar (TR-30.8). Its notes hand S43 the direct sites, the bases and the help's interim sentences (section-30 :516-521, :1062-1066).
  - S31 (batch 11): `_dash_apply_axis_spec(…, option="axis", by_graph=False, colours=None)` with the `labcolor` line (TR-31.6, "S43 later passes this site's base colour"); `_dash_apply_scale_look(fig, axis_obj, look, option, …, colours=None)` with the axis `lcolor` line (TR-31.8); `fig._dash_scheme_colours` and `axis_obj._dash_scheme_look` (TR-31.11).
  - S32 (batch 11): `GlyphMapper._style_value(self, options, role, attr, default)` (TR-32.7), the base under `pstyle()`/`mstyle()`/`lstyle()`; the ten mappers' colour reads split per role (TR-32.9).
  - S38 (batch 13): the region reader that replaced `_extract_region_color`/`_extract_region_lcolor`/`_extract_region_lwidth` (R2 row S38) and reads region `%NN` through S30's reader; IR-2's `bgcolor()` semantics.
  - S39 (batch 14): `_dash_refline_draw`'s numlist positions and `lstyle()` through `style_bundle`.
  - S33 (batch 11, read): the marker-label default colour and opacity (`color p#label` → `plabel` → `p#`; D-33h hands `mlabcolor(red%70)` to S43).
  - S01 provides the open entry `P1.13b`, its `WP30_OPEN` key, the marker `<!-- WP-30 P1.13b -->` in the WP-30 group of `### Results that change`, the S43 stub block and the map anchors `# WP-30 S43 (P1.13b): Default colour and opacity at every colour site (P1.13 part b)`.
- **Blocks: 56.** S56 colours `text()` through `_textbox_color` and inherits the bare rule.
- **Parallel batch: 15**, merge order S42, S43, S44.
- **Can run with:** S42 edits dash.ado, Mata, `_load_data`, `_dash_take_qual_columns`, `_dash_csv_meta`, `_dash_load_columns` and `_generate_app_source`; S44 edits `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_count_axes`, the `_dash_ts_*` model and `_DASH_AXIS_FINISH_JS`. None of those is S43's, and neither partner edits an applier, a mapper or a colour reader.

## Evidence

Anchors are at `c96facd`, re-verified for this file; S16-S41 move them. The executor re-finds each by symbol at `batch-15-base`; the excerpts below are `c96facd`'s and S30-S39 have rewritten several bodies (their TRs are quoted where they bind).

### E1. Direct `translate_mcolor` sites (dash_render.py)

`_apply_mlabel_opts` (:9302) at :9451:

```python
9449         if "mlabcolor" in options:
9450             try:
9451                 kwargs["text_color"] = self.tr.translate_mcolor(options["mlabcolor"])
9452             except ValueError:
9453                 _dash_style_note("mlabcolor", options["mlabcolor"], "colour")
```

`_apply_colorvar` (:8887) at :8962-8971: `missing_color = "#808080"`, then `self.tr.translate_mcolor(_raw_missing)` with "dash: colormissing(…) is not a recognised colour; using grey." The other direct sites (critic list, research p1-13 "Gaps"): `map_bar` (:10122) and `map_rbar` (:13005) `color`/`bfcolor`/`blcolor`, `map_area` (:10029) and `map_rarea` (:12933) `color`, `_histogram_quads` (:12423), `map_dropline` (:13398), `map_rcapsym` (:13512), `map_scatteri` (:13627), `map_pcarrow` (:14025), `map_pcbarrow` (:14106). `translate_mcolor` strips a `%` suffix, so each drops the opacity.

### E2. Module readers (dash_render.py)

- `_textbox_color(opts, default)` (:4839): "*default* (None from every caller, which then keeps the scheme's colour)". Callers, each holding the figure: `_dash_add_secondary_axes` (:23103), `_dash_figure_title` (:25924), `_dash_style_axis_titles` (:25948), `_dash_text_annotations` (:26012), `_dash_apply_z_options` (:26138). S30 routes it through `parse_color_alpha(str(raw), "color")` and leaves "the opacity and a bare `*#`/`%#`" to S43 (TR-30.8).
- `_dash_graph_color(option, raw)` (:15407); called in `_make_figure_body` (:30340-30376) and as emitted strings in the template (:35226-35255) for `bgcolor`, `plotbgcolor`, `plotregion(color)`, `plotregion(lcolor)`, `graphregion(color)`. S38 replaced the region half of both blocks with its reader.
- `_resolve_kpi_color(val, default, option="")` (:17054); callers `_dash_kpi_card_html` (:17029 `color`, default `text_color`; :17032 `bgcolor`, default `""`) and the saved KPI rebuild (:31811, :31813).
- `_dash_refline_draw(fig, opt, dim, values, style, scheme, Span, range_name="default")` (:26327): the base is `scheme.xyline_color` (:26338). S30 reads `lcolor` through `parse_color_alpha(…, **OptionTranslator.scheme_colour_context(scheme))`; S39 adds `lstyle()`.

### E3. Scheme bases (SchemeParser._init_properties, :6805-6835)

`background_color` (`color background`), `plotregion_color` (`color plotregion`), `title_color` (`color heading`), `subheading_color`, `body_color`, `small_body_color`, `axis_title_color`, `tick_label_color`, `axis_line_color` (`color axisline`), `xyline_color` (:6989), `plotregion_line_color` (:7001). The textbox sites set these on the figure before `_textbox_color` runs (E2's comments: "the scheme's heading, set before this runs, stays").

### E4. twoway's truth

Overview's block (research §3 "bare *#", "Filled layers compose sequentially", "Opacity with intensity"; critic correction 1 for `naturally_white 0`; critic "Gaps" for mlabcolor, title, xline, text). Not yet measured, measured by this section's extractor: `labcolor(*.5)`, `yscale(lcolor(*.5))`, `plotregion(color(*.5))`, `plotregion(lcolor(%50))`, `pstyle(p3) mcolor(*.5)`, `lpattern`-free `clcolor(*.5)` on connected, `rcap`/`dropline`/`pcarrow` `lcolor(*.5)`, `histogram, fcolor(*.5)`, `subtitle`/`note`/`caption`/`ytitle` `color(*.5)`, under s2color, stcolor, sttrans and s1rcolor.

### E5. Tests that pin the interim (written by S30 and S33; flipped, never deleted)

- `test/test_option_validation.py::TestTheRemainingSilentSites::test_area_color` and `::test_bar_color_beside_blcolor` (S30 table, section-30 :340: "stay green (direct mapper sites, S43)"): an unknown colour at a direct site keeps the scheme's fill with the note → black.
- `test/test_colour_grammar.py::TestStataTruth::test_each_probe`: skips the fixture probes whose `owner` is `S43` (`mlabel(make) mlabcolor(bogus)`, `bar …, color(bogus)`; section-30 :557, :736) → the skip is removed for them.
- S33's marker-label opacity tests: `mlabcolor(red%70)` under sttrans drawn at the scheme's 0.20 (section-33 D-33h, :954) → 0.70.
- Any test of S30's that asserts a bare `*#` keeps the default (BR-30.13's interim; `*.5%50` "the bare multiplier is S43's", section-30 :230).
43-01 re-measures them on the base; the list in `$S/43-flips.txt` is what is flipped.

### E6. Blast radius (`gitnexus impact <symbol> -d upstream -r dash` at `c96facd`; re-run at 15.0)

| Symbol | Risk | Action |
|---|---|---|
| `GlyphMapper._apply_marker_opts` | CRITICAL (12) | warn; `base=` at its colour reads |
| `GlyphMapper._apply_line_opts` | CRITICAL (40) | warn; `base=` at its colour reads |
| `GlyphMapper._apply_mlabel_opts` | CRITICAL (16) | warn; one block |
| `_textbox_color` | CRITICAL | warn; keyword-only additions |
| `_resolve_kpi_color` | CRITICAL | warn; `base=default` passed inside |
| `GlyphMapper._apply_fill_opts`, `_ci_band_style` | HIGH | warn; `base=` |
| `OptionTranslator.stata_colour` | (S30's; impact at 15.0) | `base` keyword |
| `_dash_refline_draw`, `_apply_colorvar`, `_histogram_quads` | LOW | in place |
| `_dash_region_spec` (S38's; copy-listed) | impact at 15.0 | `base=base_hex` in its `_read` step |
| `_dash_graph_color` | LOW (no region caller after S38) | edited only if a colour-site caller remains (TR-43.9) |
| the ten mappers | UNKNOWN | dispatch table, grep |
| `ServerAppBuilder._shared_stat_lines` | HIGH | not edited |

## User stories

- **US-43.1** As a twoway user, I want `mcolor(*.5)`, `lcolor(*1.5)`, `fcolor(*.7)` and `mlabcolor(*.5)` to lighten or darken the colour the layer would otherwise draw, so a scheme's palette adjusted by intensity looks as in Stata.
- **US-43.2** As a twoway user, I want `title("T", color(*.5))`, `graphregion(color(*.5))`, `xline(3000, lcolor(%50))` and `ylabel(, labcolor(*.5))` to adjust the scheme's own colour for that element.
- **US-43.3** As a twoway user, I want a `%#` opacity honoured at every colour option, and an unknown colour drawn black with a note, wherever I write it.
- **US-43.4** As a dashboard publisher, I want the saved page and the served app to draw the same adjusted colours, before and after a filter move, and a KPI card's `color(*.5)` to lighten its default text colour.

## Business requirements

- **BR-43.1** A bare `*#` at a colour site draws the colour the site would draw without the option, adjusted by twoway's intensity rule for the graph's scheme (`naturally_white` included); a bare `%#` draws that colour at that opacity; `*#%#` and `%#*#` do both.
- **BR-43.2** The base of a site is: for markers, lines, fills and CI bands, the colour the layer's plot index or named style gives that role (`pstyle()`, `mstyle()`, `lstyle()` and the rest included); for a second-axis layer, its own plot index; for marker labels, the marker-label default; for titles, subtitles, notes, captions, axis titles and the colour key's title, the scheme's colour for that text; for `labcolor()` and the axis line, the axis's scheme colour; for the graph and plot regions, their scheme colours; for `xline()`/`yline()`, the scheme's reference-line colour; for `colormissing()`, dash's missing-value grey; for the KPI's `color()`, its default text colour.
- **BR-43.3** On filled layers (bar, rbar, area, rarea, histogram, CI bands), the adjusted colour is then blended with the object's intensity (scheme or `fintensity()`), in that order.
- **BR-43.4** At every colour option, a `%#` sets that element's opacity; without `%#`, the scheme's own opacity is kept.
- **BR-43.5** At every colour option, an unknown or wrong-case colour draws black (bars `#333333`), noted once, as twoway draws it; a malformed number keeps the default silently (S30's rule).
- **BR-43.6** The saved page and the served app draw the same colours and opacities, before and after any filter move.
- **BR-43.7** The KPI's `bgcolor()` with a bare form keeps its default, silently; every KPI colour accepted before is unchanged.

## Technical requirements

- **TR-43.1 `OptionTranslator.stata_colour`** (S30's; static, travels with the class): keyword-only `base=None` (D-43a). Placement: after the base-colour parse and before S30's multiplier step, `if hx is None and isinstance(base, str) and _HEX6_RE.fullmatch(base): hx = base.lower()`; the multiplier and opacity then apply as to any colour. Docstring: the base rule, twoway's measured examples (`*.5` → `#8da3b7` from navy; `*.5%50`), and that `base` is never parsed as text. Every return stays `#[0-9a-f]{6}` or None.
- **TR-43.2 Marker applier** (`_apply_marker_opts`, CRITICAL, warn). Each colour read (`mcolor`, `mfcolor`, `mlcolor`, the folded `color`) passes `base=` the role's default before the option: fill → `self._style_value(options, "marker", "fill", <today's fill default>)`, line → `self._style_value(options, "marker", "line", <today's line default>)`, using the names S32 gave the roles at `batch-15-base`. `mcolor()` resolves once per role (its base differs per role). Alpha: set only when the reader returns one.
- **TR-43.3 Line applier** (`_apply_line_opts`, CRITICAL, warn): `lcolor`, `clcolor` and the folded `color` pass `base=self._style_value(options, "line", "color", <today's default>)`.
- **TR-43.4 Fills.** `_apply_fill_opts` (HIGH, warn): its `fcolor()` read passes `base=base` (S16's parameter, the pre-intensity fill), so `fcolor(*.7)` is `base*.7` and the blend follows. The five fill mappers' `color()`/`bfcolor()` reads that set `_fill_base` pass `base=_fill_base` (as S16 and S32 left it) through `self.tr.parse_color_alpha(value, option, base=…)`, keep a returned alpha in a local passed on to the glyph's `fill_alpha`, and draw an unknown colour black with the note; `blcolor()` and the outline `lcolor` pass the outline's default. `_ci_band_style` (HIGH, warn): `acolor`/`fcolor`/`color` pass the band's default fill, then the band's intensity applies as S16 left it.
- **TR-43.5 The other direct mapper sites** (`map_dropline`, `map_rcapsym`, `map_scatteri`, `map_pcarrow`, `map_pcbarrow`, `_histogram_quads`): each `translate_mcolor`/`translate_lcolor` call becomes `self.tr.parse_color_alpha(value, option, base=<the colour the mapper set before it, as S32 split it>)`; a non-None alpha is written to the matching `*_alpha`; `(None, None)` keeps today's colour. No other line of these mappers changes.
- **TR-43.6 Marker labels** (`_apply_mlabel_opts`, CRITICAL, warn): `mlabcolor` through `self.tr.parse_color_alpha(options["mlabcolor"], "mlabcolor", base=kwargs["text_color"])` (S33's default, set before this block); `kwargs["text_alpha"] = alpha` when not None (S33 D-33h's `mlabcolor(red%70)` → 0.70); an unknown colour black with the note (the reader's).
- **TR-43.7 `colormissing()`** (`_apply_colorvar`): `self.tr.parse_color_alpha(_raw_missing, "colormissing", base="#808080")`; black on unknown with the reader's note (the "using grey" wording goes); `%#` is applied to `nan_color` only as the hex (Bokeh's mapper has no nan alpha) and named once with `_dash_style_note("colormissing", value, "opacity", "opaque")`.
- **TR-43.8 Text** (D-43d). `_textbox_color(opts, default, *, base=None, colours=None, with_alpha=False)`: `parse_color_alpha(str(raw), "color", base=base, **(colours or {}))`; returns `hx or default` (and the alpha when `with_alpha`). The five callers pass `base=<the property they are about to set, as the scheme set it>` and `colours=getattr(fig, "_dash_scheme_colours", None)`, ask `with_alpha=True` and set the matching alpha when not None: `_dash_add_secondary_axes` (`ax.axis_label_text_color`/`_alpha`), `_dash_figure_title` (`fig.title.text_color`/`text_alpha`), `_dash_style_axis_titles` (`axis_label_text_color`/`_alpha`), `_dash_text_annotations` (subtitle, note, caption Labels: `text_color`/`text_alpha`, base `color_default`), `_dash_apply_z_options` (`key_obj.title_text_color`/`_alpha`).
- **TR-43.9 Axes and regions.**
  - `_dash_apply_axis_spec` (S31's `labcolor` line): `base=axis_obj.major_label_text_color` read before the line writes it.
  - `_dash_apply_scale_look` (S31's `lcolor` line): `base=axis_obj.axis_line_color or (getattr(axis_obj, "_dash_scheme_look", {}) or {}).get("line_color")`.
  - The graph and plot regions (Q-43.1, resolved by section-38 TR-38.2): S38's `_dash_region_spec` reads every region colour through one inner step, `_read(arg, role)`, which holds `current` and `base_hex` (the role's setting at that point of the edit order, or the base dict's value when it is `None`). S43 adds `base=base_hex` to that step's one `parse_color_alpha` call, keeping S38's `**OptionTranslator.scheme_colour_context(scheme)`, and a returned alpha goes to the role's `fill_alpha`/`line_alpha` in `settings` (S38 composites the fill opaque; the outline keeps its alpha). `color()` calls the step once per role, so `graphregion(color(*.5))` adjusts the fill from the fill's base and the outline from the outline's. The figure's composited properties (`fig.border_fill_color`, `fig.background_fill_color`) are outputs and are never read as a base. `_make_figure_body`, the template and `_dash_apply_regions` are not edited.
  - `_dash_graph_color` has no region caller after S38 (its five calls at :30340-30376 and :35226-35255 were the region blocks S38 replaced). 43-09 greps `_dash_graph_color(` at `batch-15-base`: a colour-site caller still there gets `base=` the property it is about to set, through new keyword-only `base=None, colours=None` passed to `parse_color_alpha`; with none, the function is not edited (its removal is S58's dead-code note).
- **TR-43.10 KPI and reference lines.**
  - `_resolve_kpi_color` (CRITICAL, warn): step (1)'s grammar read passes `base=default` when `default` fullmatches hex6 (D-43e); everything else of S30's TR-30.8 unchanged, the output still through `_sanitize_css_color`.
  - `_dash_refline_draw`: the `lcolor` read passes `base=kw["line_color"]` (the scheme's or S39's `lstyle()` colour) and writes `kw["line_alpha"]` when the reader returns an alpha.
- **TR-43.11 Both modes.** Every edited function is shared by source with the served app (the classes travel; the module readers are on the copy lists, E2), the served redraw after a move rebuilds layers through the same mapper, and the saved `_FILTER_JS` writes no colour except the KPI's build-resolved, sanitised values. No template or JS change.
- **TR-43.12 Registries.** No new function; `test/function_test_map.py` is unchanged unless a TR changes a mapped test's meaning (none expected). The S43 anchors stay empty (S58 removes them, A148).
- **TR-43.13 Help** (dash.sthlp "Marker and Transparency Options", R3, S43's row): the colour paragraph states the bare rule (BR-43.1-BR-43.3) with `mcolor(*.5)`, `fcolor(*.7)` on a bar and `title("T", color(*.5))` as examples, the `%#` rule at every site, and drops S30's interim sentences (a bare `*#` keeps the default; the direct sites keep the scheme's colour for an unknown name; titles and regions read s2color's background). Lines at most 79 characters; no tool or vendor.
- **TR-43.14 Security (rule 1).** `base` is used only when it fullmatches hex6 and is never parsed; output stays hex; KPI values still pass `_sanitize_css_color`; notes echo through `_dash_style_note`/`_dash_display`; no user text becomes a property name. A guard test feeds `base="red; x:1"`, `base="#fff"`, a 10,000-character value and `*1e400` and asserts hex output or None.

## Boundaries

- **Batch 15 partners.** S42: dash.ado, dash_parse.mata, `_load_data`, `_dash_take_qual_columns`, `_dash_csv_meta`, `_DASH_CSV_JS`, `_dash_load_columns`, `_generate_app_source`, help "Syntax"/"Plot types". S44: `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_count_axes`, the `_dash_ts_*` model, `_DASH_AXIS_FINISH_JS`, `_dash_axis_plan`, help "Axis and Display Options". S43 edits none of them.
- **Earlier sections, read only:** S16's `_blend_intensity` and the blend order; S30's grammar beyond `base` (the comma refusal, the scheme-file rules, `bg`/`fg`); S31's look functions beyond the two colour lines; S32's style plan; S33's label defaults; S38's reader beyond its colour reads; S39's refline positions and `lstyle()`.
- **Not this section's:** scheme-file colours (S30: a bare `*#` in a scheme draws white, measured); `text()` drawing (S56); comma-written sub-option colours (S30's residual); `ServerAppBuilder._shared_stat_lines`, `_make_figure_body`, `_generate_app_source`, `_FILTER_JS`.

## Stata truth

### `scripts/extract_bare_intensity_truth.do` → `test/fixtures/bare_intensity_truth.json`

S02's stanza (TR-02.9), `adopath ++ "`repo'/"`, `global dash_nobrowser 1`; `_meta` in S19's form (`stata_version`, `born_date`, `dash_commit`, `extracted`), the python block never calling Stata, no `shell=True`. SVGs through `scripts/svg_truth.py` only; each probe `capture noisily` in a named log.

- **Data:** `sysuse auto`; `gen t = _n`.
- **Probes**, each under s2color, stcolor, sttrans and s1rcolor, for each value of `*.5`, `*2`, `%50` and `*.5%50`: `scatter mpg weight, mcolor(V)`, `mfcolor(V)`, `mlcolor(V)`; `scatter mpg weight, pstyle(p3) mcolor(V)`; `(scatter mpg weight) (scatter price weight, yaxis(2) mcolor(V))`; `line mpg weight, sort lcolor(V)`; `connected mpg weight, sort lcolor(V)`; `bar mpg rep78 if rep78<., color(V)`, `fcolor(V)`, `fcolor(V) fintensity(50)`, `lcolor(V)`; `area mpg weight, sort fcolor(V)`; `rarea mpg turn weight, sort fcolor(V)`; `histogram mpg, fcolor(V)`; `lfitci mpg weight, acolor(V)`; `dropline mpg weight, lcolor(V)`; `rcap mpg turn weight, lcolor(V)`; `pcarrow mpg weight turn length, lcolor(V)`; `scatteri 20 3000, mcolor(V)`; `scatter mpg weight, mlabel(make) mlabcolor(V)`; `title("T", color(V))`, `subtitle("S", color(V))`, `note("N", color(V))`, `caption("C", color(V))`, `ytitle("Y", color(V))`; `ylabel(, labcolor(V))`; `yscale(lcolor(V))`; `graphregion(color(V))`; `plotregion(color(V))`, `plotregion(lcolor(V))`; `xline(3000, lcolor(V))`.
- Unknown-at-direct-site probes (s2color): `bar mpg rep78 if rep78<., color(bogus)`, `area … color(bogus)`, `dropline … lcolor(bogus)`, `mlabcolor(bogus)`, `xline(3000, lcolor(bogus))`.
- **Records:** per scheme and probe `rc`, `notes`, and the element's `fill`, `stroke`, `fill-opacity`, `stroke-opacity`, `opacity` (lower-cased), plus the same element's values in the probe without the option (`base`).
- Run: `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_bare_intensity_truth.do"` (about 1,400 exports); `git add -f test/fixtures/bare_intensity_truth.json`.

### The S43 block of `test/test_wp30_truth.cscript` (R1)

Helpers `_s43_*` above S01's `* ==== S43 P1.13b: Default colour and opacity at every colour site ====` header: a `python:` reader of a saved page's document JSON returning a named glyph's or annotation's colour and alpha (any Stata helper declares `version 19`). Cases report through `_w30_expect`/`_w30_done`, write only under `` `w30_work' `` and erase their pages and SVGs before the `S43 end` line (TR-01.10 item 4); run alone (`WP30_ONLY=S43`) the block prints its PASS lines and `ALL CHECKS PASSED`.
- **BI-01:** `scatter mpg weight, mcolor(*.5)` under s2color, stcolor, sttrans, s1rcolor: dash's saved fill (and alpha) equals live twoway's SVG fill.
- **BI-02:** `bar mpg rep78 if rep78<., fcolor(*.7)`: `#7f98ae` in both.
- **BI-03:** `title("T", color(*.5))` and `graphregion(color(*.5))`: equal to twoway.
- **BI-04:** `xline(3000, lcolor(%50))`: colour and 0.50 in both.
- **BI-05:** `mlabel(make) mlabcolor(red%50)`: opacity 0.50 in both.
- **BI-06:** `bar …, color(bogus)`: `#333333`, and dash's note printed.

No area cscript gains a case: nothing is refused (M5).

## TDD test stubs

New `test/test_bare_intensity.py` (red at the batch-15 base unless marked guard; 43-01). `_FIX = json.load(test/fixtures/bare_intensity_truth.json)`; `_both(spec)` → saved and served documents through `test_mode_parity._render_pair`; `_colour(doc, role)` reads a glyph's, annotation's, axis's or figure's colour and alpha.

- Test: the fixture is stamped and holds the four schemes and every probe — `TestTheFixture::test_it_is_stamped`
- Test: `stata_colour("*.5", base="#1a476f")` is `("ok", "#8da3b7", None)`; `"%50"` → `("ok", "#1a476f", 0.5)`; `"*.5%50"` and `"%50*.5"` → `#8da3b7` at 0.5; `naturally_white=False` `"*.5"` on `#ffff00` → `#808000`; `base=None` → S30's answer — `TestTheRule::test_the_base_rule`
- Test: `base="red; x:1"`, `"#fff"`, `123`, a 10,000-character value, `*1e400`: hex or None, never raises — `TestTheRule::test_the_base_is_never_text`
- Test (both modes, fixture): every probe of every scheme: fill/stroke and opacity equal the fixture's — `TestEverySite::test_probe[<scheme>-<probe>-<value>-saved|served]`
- Test (both modes): `mlcolor(*.5)` changes the outline only; `mfcolor(*.5)` the fill only — `TestMarkerRoles::test_roles_are_separate`
- Test (both modes): `pstyle(p3) mcolor(*.5)` is p3's colour adjusted — `TestNamedStyleBase::test_pstyle_base`
- Test (both modes): bar `fcolor(*.7)` `#7f98ae`; `fcolor(*.5) fintensity(50)` `#c6d1db`; `color(*.5)` `#a4b5c5` — `TestFillsBlendAfter::test_order`
- Test (both modes): sttrans `mcolor(*.5)` keeps 0.2; `mcolor(*.5%50)` is 0.5 — `TestSchemeOpacityKept::test_sttrans`
- Test (both modes): unknown colour at each direct site → black (`#333333` on bars) with one note — `TestUnknownAtDirectSites::test_site[<site>]`
- Test: `_textbox_color({"color": "*.5"}, None, base="#1e2d53", with_alpha=True)` → `("#8f96a9", None)`; without the keywords, the base's answer — `TestTheTextReader::test_keywords`
- Test (both modes): title, subtitle, note, caption, ytitle, ytitle2 and the colour key's title with `color(*.5)` and `color(red%50)` — `TestTextSites::test_site[<site>-<value>]`
- Test (both modes): `labcolor(*.5)`, `yscale(lcolor(%50))` — `TestAxisSites::test_site[<value>]`
- Test (both modes): `graphregion(color(*.5))`, `plotregion(color(*.5))`, `plotregion(lcolor(%50))` — `TestRegionSites::test_site[<value>]`
- Test (both modes): `xline(3000, lcolor(*.5))`, `lcolor(%50)`, `lcolor(bogus)` — `TestReflineSite::test_site[<value>]`
- Test: KPI `color(*.5)` lightens the default text colour; `bgcolor(*.5)` keeps the default silently; every value of S30's KPI corpus unchanged — `TestTheKpi::test_bare_forms`
- Test (both modes): `colorvar(price) colormissing(*.5)` adjusts `#808080` — `TestColormissing::test_bare_form`
- Test: saved (node) and served moves keep every colour and alpha of a page holding a bare form on each of scatter, bar, line, title and xline — `TestAfterAFilterMove::test_colours_survive[saved|served]`
- Test: dash.sthlp "Marker and Transparency Options" states the bare rule and holds none of S30's interim sentences — `TestTheHelp::test_the_rule_is_documented`
- Guard: a page with no bare form and no `%#` is byte for byte the base's (the single-y digest unchanged) — `TestNoBareNoChange::test_unchanged`
- Test (cscript): BI-01..BI-06.
- Shared: `test/test_mode_parity.py` CORPUS gains `_case("Bare intensity at every site (WP-30 P1.13b)", [_sc(mcolor="*.5", mlabel="make", mlabcolor="red%50"), plot_for("bar", {"fcolor": "*.7"}), plot_for("line", {"lcolor": "%50"})], go={"title": "T, color(*.5)", "xline": "3000, lcolor(%50)"})`.

### Pinned tests to flip (R9)

E5's list, re-measured by 43-01 into `$S/43-flips.txt`; each flipped in place with `Flipped: <node> -- <the interim answer> was wrong because twoway <draws X>` (black for an unknown name at a direct site; the site's adjusted colour for a bare form; 0.70 for `mlabcolor(red%70)`).

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| The rule | pytest `TestTheRule` | literal | n/a |
| Every site against twoway | pytest `TestEverySite` and the site classes; cscript BI-01..BI-06 | `bare_intensity_truth.json` | yes |
| Fills after intensity | `TestFillsBlendAfter` | fixture | yes |
| Unknown at direct sites | `TestUnknownAtDirectSites`; BI-06 | fixture | yes |
| After moves | `TestAfterAFilterMove` (node saved, served) | auto | yes |
| KPI, colormissing | `TestTheKpi`, `TestColormissing` | literal | yes |
| Parity | `test_mode_parity.py` one CORPUS case | `_DF` | yes |
| Help | `TestTheHelp`, `test_help_conformance.py` | dash.sthlp | n/a |
| Security | `TestTheRule::test_the_base_is_never_text`; `test_security_surface.py` | literal | n/a |

**Acceptance criteria.**
- **AC-43.1** (BR-43.1, BR-43.2) `TestEverySite` passes for every probe and scheme in both modes; BI-01, BI-03..BI-05 PASS.
- **AC-43.2** (BR-43.3) `TestFillsBlendAfter` and BI-02 pass.
- **AC-43.3** (BR-43.4) `TestSchemeOpacityKept` passes; every `%#` probe's opacity equals the fixture's.
- **AC-43.4** (BR-43.5) `TestUnknownAtDirectSites` and BI-06 pass.
- **AC-43.5** (BR-43.6) `TestAfterAFilterMove` passes, the node test not skipped; `test_mode_parity.py` passes with an untouched `ALLOWED`.
- **AC-43.6** (BR-43.7) `TestTheKpi` passes.
- **AC-43.7** Every flip carries its `Flipped:` line, none is deleted; the full suite through the queue reports 0 failed; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 43-01 to 43-12 form the one commit, made by 43-12 on `wp30-s43` with the subject `Give a bare colour intensity or opacity the site's own colour at every colour site (WP-30 P1.13b)`. `$S` is `<scratch>/s43` (43-01 runs `mkdir -p "$S"`; never another section's directory, since S42, S43 and S44 run in parallel); `$SLOT` and the driver are as in section 42; `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s43`; the driver runs with `WP30_ONLY=S43`. Each task appends the files it changed to `$S/43-files.txt`.

<task type="auto" id="43-01">
  <name>Write the fixture and pytest regressions</name>
  <files>scripts/extract_bare_intensity_truth.do, test/test_bare_intensity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "<scratch>/batch-15-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s43`; stop otherwise. `mkdir -p "$S"`. Create `scripts/extract_bare_intensity_truth.do` exactly as "Stata truth" describes and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_bare_intensity_truth.do"`; it writes `test/fixtures/bare_intensity_truth.json`. Create `test/test_bare_intensity.py` with every stub of "TDD test stubs" (keyword `base=` on `stata_colour`, `with_alpha=` on `_textbox_color`, so they fail with TypeError now). Run it with `-n 6 -rf` into `$S/43-new.log`. Re-measure E5's interim pins on the base (`python3 -m pytest test/test_colour_grammar.py test/test_option_validation.py -q -n 6 -p no:cacheprovider -rA` and S33's `test/test_label_key_chrome.py`) and write the nodes that pin an interim answer to `$S/43-flips.txt`. Write `$S/43-P1.13b-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)". Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/bare_intensity_truth.json')); print(sorted(d['schemes']), all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')))"` prints `['s1rcolor', 's2color', 'stcolor', 'sttrans'] True`; `grep -c FAILED "$S/43-new.log"` is at least 60; `git -C "$WT" diff --name-only -- dash_render.py dash.sthlp` prints nothing.]]></verify>
  <done>The twoway bare-intensity fixture existed and every pytest regression test was shown failing on the unmodified tree, with the failure text and the interim pins recorded.</done>
</task>

<task type="auto" id="43-02">
  <name>Write the truth block and parity case</name>
  <files>test/test_wp30_truth.cscript, test/test_mode_parity.py</files>
  <action><![CDATA[
    Put the `_s43_*` helpers directly above S01's `* ==== S43 P1.13b: …` header and BI-01..BI-06 between S01's S43 start and end lines, each comparing live twoway's SVG colour and opacity with dash's saved page and printing `BI-nn PASS: …` through `_w30_expect`. Append the CORPUS case of "TDD test stubs" to `test/test_mode_parity.py` before `CORPUS`'s closing bracket (after any earlier section's cases). Run the block through the driver and the new parity case; append the `BI-nn FAIL` lines and the parity result (a guard if the modes already agree) to `$S/43-P1.13b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "BI-0[1-6] FAIL" "$S/run_test_wp30_truth.log"` is at least 5; `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "WP-30 P1.13b"` runs one case.]]></verify>
  <done>The live twoway comparisons and the parity case were in place, the comparisons shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="43-03">
  <name>Add the base to the colour reader</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Run `gitnexus impact stata_colour -d upstream -r dash` in the main checkout (never in $WT) unless `<scratch>/batch-15-impact.txt` already holds it, and report a HIGH or CRITICAL result before editing. Apply TR-43.1 in `OptionTranslator.stata_colour`: the keyword-only `base=None`, used only when it fullmatches hex6, before S30's multiplier step; the docstring with E4's examples. Change nothing else of S30's reader.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bare_intensity.py -q -n0 -p no:cacheprovider -k TestTheRule` passes; `python3 -m pytest test/test_colour_grammar.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Stata's colour reader took a site's base colour for a bare intensity or opacity and stayed hex-only.</done>
</task>

<task type="auto" id="43-04">
  <name>Pass bases in marker and line appliers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the progress output that `_apply_marker_opts` and `_apply_line_opts` are CRITICAL. Apply TR-43.2 and TR-43.3: every colour read passes `base=` from `self._style_value(options, <role>, <attr>, <today's default>)`, with S32's role names as they are at the base (`grep -n "_style_value(" dash_render.py`), `mcolor()` resolved per role, alpha set only when returned. Touch no size, symbol or width line.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bare_intensity.py -q -n 6 -p no:cacheprovider -k "Marker or NamedStyle or scatter or line or connected"` passes; `python3 -m pytest test/test_named_styles.py test/test_intensity_blend.py test/test_glyphs.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Markers and lines drew a bare intensity or opacity on their own default or named-style colour in both modes.</done>
</task>

<task type="auto" id="43-05">
  <name>Pass bases at fills and bands</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn that `_apply_fill_opts` and `_ci_band_style` are HIGH. Apply TR-43.4: `_apply_fill_opts`' `fcolor()` read with `base=base`; the `color()`/`bfcolor()`/`blcolor()`/outline reads of `map_bar`, `map_rbar`, `map_area`, `map_rarea` and `_histogram_quads` through `self.tr.parse_color_alpha(value, option, base=_fill_base or the outline default)`, alpha carried to the glyph, unknown black with the note; `_ci_band_style`'s band colour reads with the band's default. Never read a colour back from a glyph (S16's rule).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bare_intensity.py -q -n 6 -p no:cacheprovider -k "Fills or bar or area or rarea or histogram or lfitci"` passes; `python3 -m pytest test/test_intensity_blend.py test/test_named_styles.py -q -n 6 -p no:cacheprovider` reports 0 failed except E5's flips.]]></verify>
  <done>Filled layers and CI bands composed a bare intensity with their base and then their intensity, kept a percent opacity and drew an unknown colour black.</done>
</task>

<task type="auto" id="43-06">
  <name>Route the remaining direct mapper sites</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-43.5 to `map_dropline`, `map_rcapsym`, `map_scatteri`, `map_pcarrow` and `map_pcbarrow`: each `translate_mcolor`/`translate_lcolor` colour read becomes `self.tr.parse_color_alpha(value, option, base=<the colour set before it>)`, a returned alpha written to the matching `*_alpha`. The mappers are UNKNOWN to the index: record `grep -n "translate_mcolor\|translate_lcolor" dash_render.py` before and after in `$S/43-sites.txt`; afterwards no applier or mapper calls `translate_mcolor` for a user colour.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bare_intensity.py -q -n 6 -p no:cacheprovider -k "dropline or rcap or pcarrow or scatteri or UnknownAtDirectSites"` passes; `grep -c "self.tr.translate_mcolor" "$WT/dash_render.py"` equals the count of non-user reads listed in `$S/43-sites.txt`.]]></verify>
  <done>Every direct mapper colour site kept a percent opacity, took its base for a bare form and drew an unknown colour black.</done>
</task>

<task type="auto" id="43-07">
  <name>Route marker labels and colormissing</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn that `_apply_mlabel_opts` is CRITICAL. Apply TR-43.6 (`mlabcolor` through `parse_color_alpha` with `base=kwargs["text_color"]`, `text_alpha` from a `%#`) and TR-43.7 (`colormissing` with `base="#808080"`, black on unknown with the reader's note, a `%#` named once). Edit no other line of either function.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bare_intensity.py -q -n 6 -p no:cacheprovider -k "mlab or Colormissing"` passes; `python3 -m pytest test/test_marker_label_parity.py test/test_colorvar_forms.py test/test_axis_options.py -q -n 6 -p no:cacheprovider` reports 0 failed except E5's flips.]]></verify>
  <done>Marker labels and the missing-value colour took the bare rule, a percent opacity and black on an unknown colour.</done>
</task>

<task type="auto" id="43-08">
  <name>Give text sites their base</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn that `_textbox_color` is CRITICAL. Apply TR-43.8: the keyword-only `base`, `colours`, `with_alpha` (default calls unchanged); in `_dash_add_secondary_axes`, `_dash_figure_title`, `_dash_style_axis_titles`, `_dash_text_annotations` and `_dash_apply_z_options` pass the property's current scheme colour as `base`, `getattr(fig, "_dash_scheme_colours", None)` as `colours`, ask for the alpha and set the matching `*_alpha` when returned.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bare_intensity.py -q -n 6 -p no:cacheprovider -k "TextReader or TextSites"` passes; `python3 -m pytest test/test_label_sinks.py test/test_textbox_grammar.py test/test_textbox_no_text.py test/test_label_key_chrome.py -q -n 6 -p no:cacheprovider` reports 0 failed except E5's flips.]]></verify>
  <done>Titles, subtitles, notes, captions, axis titles and the colour key's title took the bare rule and a percent opacity in both modes.</done>
</task>

<task type="auto" id="43-09">
  <name>Give axes, regions, KPI, reflines bases</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-43.9 and TR-43.10: S31's `labcolor` and axis `lcolor` lines with their bases; `base=base_hex` in the `_read` step of S38's `_dash_region_spec` with the alpha to the role's setting; `_dash_graph_color` only if `grep -n "_dash_graph_color(" dash_render.py` finds a colour-site caller (record the grep in `$S/43-sites.txt`); `_resolve_kpi_color` (CRITICAL: warn) with `base=default` when hex; `_dash_refline_draw`'s `lcolor` with `base=kw["line_color"]` and `line_alpha`. First check that `_dash_region_spec` holds the `_read(arg, role)` step with `base_hex` (`grep -n "base_hex" dash_render.py`); if it does not, stop and report without editing `_make_figure_body` or the template (R12).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_bare_intensity.py -q -n 6 -p no:cacheprovider` passes except `TestTheHelp`; `python3 -m pytest test/test_security_surface.py test/test_kpi.py test/test_kpi_security.py test/test_server_kpi_card.py test/test_graph_options.py test/test_axis_suboptions.py -q -n 6 -p no:cacheprovider` reports 0 failed except E5's flips, and so do the files S38 and S39 created for regions and reference lines (`git -C "$WT" log --name-only --format= $(cat "<scratch>/batch-13-base.txt")..HEAD -- test/ | sort -u`, those naming `region` or `refline`/`xline`).]]></verify>
  <done>Axis labels and lines, the graph and plot regions, the KPI and reference lines took their bases for a bare form and kept a percent opacity.</done>
</task>

<task type="auto" id="43-10">
  <name>Flip the interim pins</name>
  <files>test/test_option_validation.py, test/test_colour_grammar.py, test/test_label_key_chrome.py</files>
  <action><![CDATA[
    Flip each node of `$S/43-flips.txt` in place, never deleting one: the two `TestTheRemainingSilentSites` cases to black (bars `#333333`); `TestStataTruth::test_each_probe`'s skip of `owner == "S43"` removed so those probes are checked; S33's `mlabcolor(red%70)` opacity to 0.70 in `test/test_label_key_chrome.py` (S33's file; confirm with `grep -ln "red%70" test/*.py`, and if S33 put it elsewhere, flip it there and name that file in the commit body). Append one `Flipped:` line per node to `$S/43-flips-done.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_option_validation.py test/test_colour_grammar.py $(grep -ln "red%70" "$WT"/test/*.py) -q -n 6 -p no:cacheprovider` reports 0 failed; `wc -l < "$S/43-flips-done.txt"` equals `wc -l < "$S/43-flips.txt"`.]]></verify>
  <done>Every test that pinned an interim colour asserted twoway's colour, with the reason recorded.</done>
</task>

<task type="auto" id="43-11">
  <name>Document the bare rule in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-43.13 in "Marker and Transparency Options" (find the colour paragraph and S30's interim sentences by text): the bare rule with its three examples, the `%#` rule at every site, unknown black at every site; delete only S30's interim sentences. Edit no other paragraph (R3); lines at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_bare_intensity.py::TestTheHelp" test/test_help_conformance.py test/test_colour_grammar.py -q -n 6 -p no:cacheprovider` reports 0 failed; `awk 'length > 79' "$WT/dash.sthlp" | grep -c '\*\.5'` prints 0.]]></verify>
  <done>The help stated the bare rule at every colour site and no longer described the interim.</done>
</task>

<task type="auto" id="43-12">
  <name>Close the entry and make the commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.13b"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution", today's date. Delete the `"P1.13b"` key line of `WP30_OPEN`. Replace `<!-- WP-30 P1.13b -->` in place with "Notes: CHANGELOG line", the old values from the failure file. Run `test_tracking_documents.py`, `test_bare_intensity.py`, `test_mode_parity.py`, `test_colour_grammar.py`, `test_fixtures_are_committed.py` and `test_cscript_hygiene.py` with `-n 6` and the S43 block through the driver; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"<scratch>/full_suite_queue.sh" "$WT" "$S/43-full.log"` in the background, read when `exit=` appears. Stage exactly `$S/43-files.txt`, these three and `test/fixtures/bare_intensity_truth.json` (`git add -f`); G6; G7 before and after; commit.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/43-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.13b -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.13b": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.13b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.13b was closed naming existing tests, its marker carried the measured old and new colours, and one green commit on wp30-s43 was ready for the merger.</done>
</task>

## Section completion criteria

- A bare `*#`, `%#` and both take the site's base at every site of BR-43.2, blended after on filled layers, in both modes, before and after saved and served moves (fixture probes under four schemes; BI-01..BI-05).
- Every direct site keeps `%#` and draws an unknown colour black (BI-06, `TestUnknownAtDirectSites`).
- No new module function; no copy-list change; `_shared_stat_lines`, `_make_figure_body` and the template untouched.
- The fixture is generated, stamped, committed with `-f` and read by tests; E5's pins are flipped with reasons.
- One green commit `(WP-30 P1.13b)` on `wp30-s43` closes the entry, deletes its key and replaces its marker.

## Notes

- **Q-43.1, resolved.** S38's section file (TR-38.2, "The S43 hook") gives region colours one copy-listed reader, `_dash_region_spec`, reached from `_dash_apply_regions` in both modes, whose `_read(arg, role)` step holds the role's `base_hex`. S43 passes that as `base=` and writes the alpha to the role's setting (TR-43.9); no `_make_figure_body` or template line is edited, and no residual is filed.
- **The base is read before the write.** At every text, axis and region site the property already holds the scheme's colour when the option is read; read it into a local first, then write.
- **sttrans.** A bare `*.5` keeps the scheme's 0.2 opacity (measured); only a `%#` sets an alpha (D-43c).
- **naturally_white 0** (s1rcolor): `*.5` multiplies (`#808000` on p1's yellow); the blend's context comes from `self.tr` (D-30b) or `fig._dash_scheme_colours`; never pass `naturally_white=True` by hand.
- **python_exec hazard.** As section 42's Notes.
- **Merge rules for the shared files.**
  - R1: S43's truth block and helpers only; no area script.
  - R2: no copy-list change (E2); S43's map anchors stay empty.
  - R3: "Marker and Transparency Options" (S43's row).
  - R4/R5: the `P1.13b` marker, entry and key.
  - R8: one CORPUS case appended; `ALLOWED`/`_MUST_WARN` untouched.
  - R9: E5's flips. R10: the single-y digest is unchanged (no bare form on that page); 43-12 checks `test_varlist_expansion.py`.
  - R12: S43 is batch 15's editor of the four appliers; not of `_make_figure_body` or `_generate_app_source`.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `OptionTranslator.stata_colour`, the four appliers, `_ci_band_style`, the ten mappers, `_apply_colorvar`, `_textbox_color` and its five callers, `_dash_region_spec` (and `_dash_graph_color` only if 43-09 edited it), `_dash_apply_axis_spec`, `_dash_apply_scale_look`, `_resolve_kpi_color` and `_dash_refline_draw`, plus test symbols.
- **Commit message.** Subject as in "Commit boundary". Body: the failure file; the measured defect (Overview's twoway block and the interim); what changed and where (TR-43.1-TR-43.13, both modes); one `Regression: test/test_bare_intensity.py::<Class>::<test> -- failed at <base sha> with <text>` per node and `test/test_wp30_truth.cscript BI-01` style for the block; the `Flipped:` lines of `$S/43-flips-done.txt`; `Fixture: test/fixtures/bare_intensity_truth.json (scripts/extract_bare_intensity_truth.do)`; `BUGS.md: "A bare *# or %# colour, such as mcolor(*.5), is refused or loses the site's default colour, where twoway adjusts that default" (closed)`.
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.13b). A bare *# and %# take the site's own colour before intensity, as twoway draws them: OptionTranslator.stata_colour takes a base= colour, and every colour site passes its own -- markers and lines from the named-style plan (_apply_marker_opts, _apply_line_opts through _style_value), fills from the pre-intensity fill then blended with the object's intensity (_apply_fill_opts, map_bar, map_rbar, map_area, map_rarea, _histogram_quads, _ci_band_style), marker labels from the label default (_apply_mlabel_opts), text from the scheme's text colours (_textbox_color and its five callers), labcolor and the axis line (_dash_apply_axis_spec, _dash_apply_scale_look), the graph and plot regions from each role's base (_dash_region_spec), the KPI's default (_resolve_kpi_color), xline/yline from the xyline colour (_dash_refline_draw) and colormissing from grey; every direct site keeps a %# opacity and draws an unknown colour black with the note, in the saved page and the served app, before and after filter moves. Pinned by test/test_bare_intensity.py::TestEverySite::test_probe, ::TestFillsBlendAfter::test_order, ::TestUnknownAtDirectSites::test_site, ::TestAfterAFilterMove::test_colours_survive, test/test_wp30_truth.cscript BI-01..BI-06; fixture test/fixtures/bare_intensity_truth.json.
  ```
- **CHANGELOG line** (replaces `<!-- WP-30 P1.13b -->` in place):

  ```
  - A bare colour intensity or opacity adjusts the colour the element would otherwise draw, as in twoway: `dash scatter mpg weight, mcolor(*.5)` kept s2color's #1a476f and now draws #8da3b7 (navy at half intensity); `bar ..., fcolor(*.7)` draws #7f98ae, `title("T", color(*.5))` #8f96a9, `graphregion(color(*.5))` #f5f9f9 and `xline(3000, lcolor(%50))` the reference-line colour at half opacity; a %# is now kept at every colour option (marker labels, bars, areas, droplines, pc arrows, titles, reference lines), and an unknown colour there draws black with the note where the scheme's colour was kept. (WP-30, P1.13b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md D7** (:918-927): D7-b closed by this commit; with S30's D7-a, c, d and e, D7 is Closed: `- **Tracked:** Closed in WP-30, BUGS.md "<P1.13a title>" and "<P1.13b title>", commits <S30 sha>, <S43 sha>.` Plan step 4 stays "not taken" (S30 D-30h).
  - **DROPIN-REMAINING.md:103** (P1.13): "Closed by <S30 sha>, <S43 sha> (WP-30 S30, S43)."
  - **AGENTS.md invariant:** "every colour option is read through `OptionTranslator.stata_colour` with the site's own base; no applier or mapper calls `translate_mcolor` for a user colour."
  - **Unverified:** the KPI and `colormissing()` have no twoway counterpart; their bases are dash's rule.
