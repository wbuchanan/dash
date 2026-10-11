# Section 38: plotregion()/graphregion() styling (P1.20 part a)

> Part of: WP-30 · Items: P1.20 part a (entry `P1.20a`; GAPS2-B18-b, GAPS2-B18-c, GAPS2-B18-d, GAPS2-B18-e, GAPS2-B18-f, AUDIT-66 styling half) · Risk: yellow · Batch: 13 (merge order S37, S38) · Depends on: 10, 13, 30, 32 · Blocks: 43, 47 · Tasks: 11, 1 commit · Case prefix: RS

## Review amendments

- Fixed (major): the 38-03 verify expected S37's MV run on S38's worktree. Both worktrees are cut from `batch-13-base`, so the run is not there. The RS run now goes directly before `// Summary` and the verify checks `AX-08 PASS`. The merger keeps RS after MV (R1).
- Fixed (major): the `LIVE_VALUES["bgcolor"]` flip described the row as a bare 3-tuple. At HEAD it is `({}, {}, "scatter", ("bgcolor", "red", "blue"))`, and `_live_pair` unpacks exactly three, so a fourth element would raise. The flip now extends the graph tuple, and `_live_pair` unpacks `key, a, b, *extra`.
- Fixed (major, Q-43.1): the colour reads in TR-38.2 are now one step that holds each role's current colour. S43 can then pass `base=` there without touching `_make_figure_body` or the template (R12). The exact S43 fix is filed.
- Fixed (minor): E1 swapped the two parsers. :721 is `_dash_parse_graph_opts` and :965 is `_dash_parse_plot_opts`.
- Fixed (minor): TR-38.4 now says `bgcolor(none)` is the colour `none` (black), as BR-38.6 and twoway have it.
- Resolved: Q-38.1. `intensity()`/`shadestyle()` are named under M5 and filed as a P2 row by S58, so no maintainer question remains.
- Checked at HEAD: `_extract_region_*` :5048/:5058/:5065, `_dash_unquoted` :5028, the saved block :30333-30379, `_seen`/`_gkey` :30227-30228, the template lines :35219-35256 with `_DASH_SCHEME` (a SchemeParser, :33478), the copy list :33386-33392, `apply_to_figure` :7376, `_dash_rep_cat` :4676, `_dash_rep_subkey` :5637, `_dash_rep_subs` :5662, the test pins test_help_claims_7.py :205-207/:1134, test_option_validation.py :1091, test_unsupported_report_is_true.py :514/:573, function_test_map.py :688-690. The RS prefix and the new files are free.
- Checked the batch boundary against S37: no shared function, and no shared help paragraph or CHANGELOG marker. Only S38 edits `svg_truth.py`.
- Rejected: "M6 forbids the region note". `lalign()`, `i*`, `margin()` and the rest are valid twoway options dash does not draw, so M5 requires the note (register P1.20.3, P1.20.5).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:131 (P1.20) reads: "`margin()`, `style(none)`, graphregion `lcolor`/`lwidth`, the `i*` options and the abbreviations `fc()`/`lc()` have no effect and nothing is reported." The margin half is S47's (P1.20b). Research `.ultraplan/wp30/research/p1-20.md` §3.3 measured every styling case at `c96facd`, in both modes, through `test_help_claims_7._render_uncached`:

```
plotregion(margin(zero)); graphregion(margin(l+10) lcolor(red) lwidth(thick));
plotregion(style(none)); graphregion(style(none)); graphregion(ifcolor(red));
plotregion(ifcolor(red)); plotregion(c(red)); graphregion(fc(red)); plotregion(lstyle(none));
plotregion(lc(red)); plotregion(lw(thick)); plotregion(lpattern(dash)); graphregion(lcolor(red));
plotregion(bogus(1))
-> saved | <case> | {... identical to base ...} | notes: []
-> served | <case> | {... identical to base ...} | notes: []
```

It also found, beyond the item text: `color()` sets only the fill (twoway sets fill and outline); `none` paints black (`translate_mcolor('none') -> #000000`); `%NN` opacity is dropped (`red%50 -> #ff0000`, alpha 1.0); `lpattern()` and `lstyle(none)` are ignored; repeated copies are not merged by meaning (`_dash_rep_merge("plotregion","color(red)","c(blue)")` gives `color(red) c(blue)`, drawn red where twoway draws blue); and `bgcolor(red)` colours the graph region, where twoway paints it on the canvas under an opaque graph region, so it does not show (critic, `k2.svg`).

**After this section**, in the saved page and the served app, before and after every filter move:
- every sub-option of twoway's region parser (`_fr_area_parse_and_log.ado:33-43`) is read under every spelling twoway accepts (`c()`, `col()`, `fc()`, `fcol()`, `lc()`, `lw()`, `lp()`, `ls()`, `sty()`, `mar()`, …), lower case only;
- `color()` sets fill and outline, `fcolor()` the fill, `lcolor()` the outline, in twoway's edit order; `none` paints nothing and shows what lies beneath; `%NN` gives twoway's opacity; `style()` and `lstyle()` take any area or line style name through S32/S36's `style_bundle`; `lpattern()` and widths on S13's ladder are drawn; the graph region's outline is drawn with Bokeh's `border_line_*`;
- `bgcolor()` paints the canvas under the graph region, as twoway does (IR-2): it shows only where the graph region is `none`, and a lone `bgcolor(red)` no longer shows;
- repeated copies merge in Mata by canonical name in twoway's sequential order, and every `margin()` copy is kept in order for S47;
- what twoway refuses is refused with its code and words (M5): an unknown, capitalised, too-short or repeated sub-option, and a comma inside a region, r(198), graphregion before plotregion and both before `legend()` and the axis options;
- what twoway accepts and dash does not draw (`lalign()`, `ilalign()`, the `i*` inner box, `margin()`, `shadestyle()`, `intensity()`, `marginonly`) is named in one note per region; S47 later draws the plot region's margin and inner box.

**Why one section.** All of it is one reader (`_dash_apply_regions`), one Mata family (the region rows of S10's tables and merge) and one help paragraph. The margin and inner box need S21's ranges and finishers (S47, batch 16).

**Test order and commit rule (rule 7).** One cycle on `wp30-s38`. 38-01 to 38-03 write the fixture and every regression test and run them against the unmodified batch-13 base, saving `$S/38-P1.20a-failure.txt` (no commit); 38-04 to 38-09 fix, flip and document; 38-10 runs the suite and 38-11 closes the entry and makes the one commit. No test-only commit exists, and no commit is red.

## Risk: [yellow] — the figure body and the served template in one batch, Mata's merge for every repeated option, and a deliberate look change (bgcolor)

**Why.**
- `DashRenderer._make_figure_body` is CRITICAL (research §6: 4 impacted, both modes' figure path); S38 is batch 13's only editor (R12; batch 13 subsection).
- `ServerAppBuilder._generate_app_source` is HIGH (5 impacted); S38 is batch 13's only template editor.
- `ServerAppBuilder._glyph_layer_lines` (the copy lists) is HIGH (4 impacted).
- `_dash_report_suboptions` (CRITICAL, 25) and `OptionTranslator.translate_mcolor` (CRITICAL, 26) are called, never edited.
- `_dash_rep_subs`/`_dash_rep_merge` are UNKNOWN to the index (Mata): grep shows `_dash_rep_subs` ← `_dash_rep_merge` ← `_dash_rep_merge_locals` and `_dash_rep_reduce` (dash.ado:6144), every repeated option. Treated as HIGH.
- `_extract_region_color`, `_extract_region_lcolor`, `_extract_region_lwidth`: LOW (3 each), deleted.

**Risk factors.**
1. The empty-option path must not move: a figure with no region option must keep every property `SchemeParser.apply_to_figure` set, or every page's digest (R10 `_SINGLE_Y_BASELINE_SHA256`) moves.
2. BokehJS paints the border with an even-odd clip that excludes the frame (research §3.4), so `background_fill_color=None` shows the page, not the graph colour; a translucent frame fill composites over the page too.
3. The Mata merge feeds the renderer one string; a merge that keeps the wrong half of a `color()` draws the wrong colour silently.
4. S10's resolver accepts a repeated word option in an unstarred stage; twoway refuses `plotregion(marginonly marginonly)` (measured below).
5. Region text reaches the served app through the spec JSON (rule 1).

**Mitigation.**
1. `_dash_apply_regions` returns before touching the figure when none of `plotregion`, `graphregion`, `bgcolor`, `plotbgcolor` is set; `TestTheEmptyPathIsInert` and the unchanged digest pin it.
2. Fills are composited in Python to an opaque `#rrggbb` (`_dash_region_blend`): a plot-region `none` or `%NN` is drawn over the graph region's resolved colour, the graph region over the canvas. Outline alphas stay Bokeh alphas (lines are painted over the fills).
3. The merge implements the parser's sequential edits (E3); `test_region_options.py::TestTheMerge` checks nine measured pairs, and RS-12 runs them through Mata.
4. A region-only post-pass refuses a repeated word.
5. No CSS path is added; only `#rrggbb`, `None`, floats and dash lists reach Bokeh; notes echo through `_dash_display`; `TestHostileRegionText` (G9).

## Dependencies

- **Depends on: 10, 13, 30, 32.**
  - S10 (batch 4): `_dash_subopt_canon(name, table)` (TR-10.2), the Mata twins `_dash_so_rows(fam)`, `_dash_so_canon`, `_dash_so_resolve`, `_dash_so_family(key)` (which returns `""` for "regions (S38's)", TR-10.6), `_dash_rep_subkey(tok, cat, full)`, `_dash_rep_subs(…, key)`, and the refusal machinery `_dash_subreq_clear/_add/_check/_accept` with the ado program `_dash_subopt_check kind` (TR-10.6 "Refusals").
  - S13 (batch 5): `OptionTranslator.translate_lwidth(value, default_px=None, ref_in=4.0)` (TR-13.4) and D-13d, which leaves the region width's default and reference to S38.
  - S30 (batch 10): `OptionTranslator.stata_colour`, `parse_color_alpha(value, option="", **ctx)` returning `(hex, alpha)` (unknown → black with a note; `"keep"` → `(None, None)`), `scheme_colour_context(scheme)` (TR-30.5-TR-30.7).
  - S32 (batch 11) and S36 (batch 12): `SchemeParser.style_bundle(cls, name)` (TR-32.6, TR-36.9): `"area"` → `fill, fill_alpha, intensity, line, line_alpha, line_width, line_dash`; `"line"` → `line, line_alpha, line_width, line_dash`; a `None` colour is "not drawn"; an unknown name returns the class default with S36's note.
  - S01: entry `P1.20a`, its `WP30_OPEN` key, markers `<!-- WP-30 P1.20a -->` at the end of the `**WP-30 (drop-in P1, 03oct2026)**` group of `### Results that change` and at the end of `### Changed behaviour (may need your do-files changed)`, S38's stub in `test/test_wp30_truth.cscript`, and the map anchors `# WP-30 S38 (P1.20a): plotregion()/graphregion() styling (P1.20 part a)`.
  - Read, not depended on: S06 (notes as `(note:  dash: …)`), S08 (`OptionTranslator.size_ref_of(fig)`), S21 (no region edit), S34 (the per-graph scheme the template passes).
- **Blocks: 43, 47.** S43 composes a bare `*#`/`%#` at the region sites with the site's base colour (manifest S43). S47 draws `plotregion(margin())` from S38's merged copies and the plot region's inner box, and keeps the graphregion margin and `i*` named.
- **Parallel batch: 13**, merge order S37, S38.
- **Can run with:** S37. S37 edits `_apply_mlabel_opts`, `_dash_option_columns`, `_dash_parse_plot_opts`, `_dash_plot_opts_to_json`, Mata `_dash_extract_vars` and the scheme extractor; S38 edits none of them, and S37 edits neither `_make_figure_body`, `_generate_app_source`, the region readers nor S10's Mata family functions.

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines, dash.ado 8,487, dash_parse.mata 6,093, dash.sthlp 3,822). S10, S13, S21, S23, S30, S32, S35 and S36 land before batch 13 and move many of them; the executor re-finds each by symbol at `batch-13-base`.

### E1. Declarations and the Mata category

dash.ado:721 (`_dash_parse_graph_opts`) and :965 (`_dash_parse_plot_opts`) declare `PLOTRegion(string asis) GRAPHRegion(string asis)`; the value reaches the spec as typed. `_dash_rep_cat` puts both in category "I" (dash_parse.mata:4676):

```mata
4676    if (anyof(("legend", "graphregion", "plotregion"), k)) return("I")
```

`_dash_rep_subs` (5662) keeps the last word of each key, where the key is the typed name (`_dash_rep_subkey`, 5637), so `c()` and `color()` are two settings.

### E2. The readers and both call sites (dash_render.py)

```python
5048 def _extract_region_color(val: str) -> str:
5054     m = re.search(r'\bf?color\s*\(([^)]+)\)', val, re.IGNORECASE)
5058 def _extract_region_lcolor(val: str) -> str:
5065 def _extract_region_lwidth(val: str) -> float | None:
```

Saved, `_make_figure_body` (def 30203) at 30333-30379: `bgcolor` → `border_fill_color`, `plotbgcolor` → `background_fill_color`, then `plotregion` fill, `outline_line_color`, `outline_line_width`, then `graphregion` fill only. Served, `_generate_app_source` (def 33915) emits the same lines at 35219-35256 (`"        _raw_bgc = go.get('bgcolor', '')"` … `"                if _c: fig.border_fill_color = _c"`), directly before `_dash_apply_scale_ranges(fig, _xsc, _ysc, …)`. The copy list carries the readers (33388-33392):

```python
33388                          "_extract_region_lwidth",
33391                          "_dash_unquoted", "_extract_region_color",
33392                          "_extract_region_lcolor",
```

`SchemeParser.apply_to_figure` (7376) runs first and sets `background_fill_color = plotregion_color`, `border_fill_color = background_color`, `outline_line_color = plotregion_line_color`, `outline_line_width = plotregion_line_width` (7381-7389).

### E3. twoway's parser (StataNow 19.5, read as text)

`/Applications/StataNow/ado/base/_/_fr_area_parse_and_log.ado` is the region parser; `twowaygraph_g.class:183` calls it for `GRAPHRegion` and :456 for `PLOTRegion` (so graph-region problems are found first). The loop at :17-22 applies each copy in turn. One copy:

```stata
33  syntax [ , STYle(string)        ISTYle(string)      ///
34         LStyle(string)   ILStyle(string)             ///
35         LColor(string)   ILColor(string)             ///
36         LWidth(string)   ILWidth(string)             ///
37         LPattern(string) ILPattern(string)           ///
38         LAlign(string)   ILAlign(string)             ///
39         SHADEStyle(string) ISHADEStyle(string)       ///
40         FColor(string)   IFColor(string)             ///
41         Color(string)    IColor(string)              ///
42         INTENsity(string) IINTENsity(string)         ///
43         Margin(string)   MARGINONLY ]
...
52  foreach opt in color width pattern align {           // l* options first
61  if `"`color'"' != `""' {                             // then color(): line AND fill
62      local oline_eds `"`oline_eds' color(`color')"'
63      local ofill_eds `"`ofill_eds' color(`color')"'
70  if `"`fcolor'"' != `""' {                            // then fcolor(): fill
71      local ofill_eds `"`ofill_eds' color(`fcolor')"'
```

So within a copy `color()` beats `lcolor()` for the outline and `fcolor()` beats `color()` for the fill, whatever the typed order; `style()` and `lstyle()` are starting points; and each copy edits the result of the one before (`.style.editstyle … editcopy`, :104-113). The minimum spellings are the capitals; `shadestyle()`, `intensity()` and `marginonly` are undocumented but accepted.

### E4. twoway's truth (research §3.1-§3.2 and critic; re-measured this pass, `p1.do`-`p3.do`, StataNow 19.5, s2color, SVG units 3960×2880)

Acceptance and refusals:

```
every sub-option and abbreviation of E3 (sty c col fc fcol ls lc lw lp la isty ic ifc ils ilc ilw ilp ila m mar)  rc 0
plotregion(bogus(1))                       option bogus() not allowed       r(198)
plotregion(st(none))                       option st() not allowed          r(198)
plotregion(is(none))                       option is() not allowed          r(198)
plotregion(COLOR(red))                     option COLOR() not allowed       r(198)
plotregion(none)                           option none not allowed          r(198)
plotregion(c(red) c(red))                  option c() not allowed           r(198)
plotregion(fc(red) fcolor(blue))           option fcolor() not allowed      r(198)
plotregion(margin(l+10) margin(r+10))      option margin() not allowed      r(198)
plotregion(color(red) marginonly marginonly) option marginonly not allowed  r(198)
plotregion(margino)                        option margino not allowed       r(198)
plotregion(color(red), lcolor(blue))       invalid 'lcolor'                 r(198)
plotregion(, color(red))                   invalid 'color'                  r(198)
plotregion(color(red),)                    rc 0
graphregion(color(red)) graphregion(c(blue) c(green))   option c() not allowed  r(198)
graphregion(bogus(1)) plotregion(foo(2))   option bogus() not allowed  (either typed order)
legend(bogus) plotregion(foo(1)); xline(abc) plotregion(foo(1))   option foo() not allowed
plotregion(lalign(bogus)) / lpattern(bogus) / margin(bogus) / lcolor(notacolour) / lwidth(abc)
                                           rc 0, "(note:  named style <x> not found in class alignstroke|linepattern|margin|color|linewidth, …)"
```

Drawing (rect fill / stroke / width / opacity; graph rects at x 0, plot rects at x 390.80):

| Option | twoway draws |
|---|---|
| base | canvas `#EAF2F3`; graph fill `#EAF2F3`, outline `#EAF2F3` 5.76; plot fill `#FFFFFF`, outline `#FFFFFF` 5.76 |
| `plotregion(color(red))`, `c(red)` | plot fill and outline `#FF0000` |
| `plotregion(fcolor(blue) color(red))` and `color(red) fcolor(blue)` | fill blue, outline red |
| `plotregion(color(red) lcolor(blue))` either order | fill red, outline red |
| `plotregion(style(none))` | no plot rects; graph colour shows |
| `graphregion(style(none))` | no graph rects; canvas shows |
| `plotregion(style(none) fcolor(red))` | fill red, no outline |
| `plotregion(lstyle(none))` | outline stroke-opacity 0 |
| `plotregion(lstyle(none) lcolor(red))` / `ls(none) lcolor(red)` | red outline |
| `plotregion(lstyle(none) lwidth(thick))` | no outline |
| `plotregion(lc(red) lw(thick) lp(dash))` | dashed red, width 23.04 |
| `plotregion(fcolor(red%50))` | fill `#FF0000`, fill-opacity 0.50, over the graph fill |
| `plotregion(lcolor(red%50) lwidth(thick))` | stroke-opacity 0.50 |
| `plotregion(fcolor(none))`, `color(none)` | no fill (graph colour shows); `color(none)` also no outline |
| `plotregion(lcolor(none))` | outline stroke-opacity 0 |
| `graphregion(color(red))` | graph fill and outline red; `fc(red)` fill only |
| `graphregion(lcolor(red) lwidth(thick))` | graph outline `#FF0000` 23.04 |
| `graphregion(lwidth(thick))` | graph outline `#EAF2F3` (the background) 23.04 |
| `graphregion(color(none))` | no graph rects; canvas shows |
| `bgcolor(red)` | canvas `#FF0000`, hidden under the opaque graph fill |
| `bgcolor(red) graphregion(color(none)) plotregion(fcolor(none))` | canvas red shows through both; plot outline still `#FFFFFF` |
| `graphregion(fcolor(red%50)) bgcolor(blue)` | canvas blue; graph fill red at 0.50 over it |
| `bgcolor(none)` | canvas `#000000` (the colour `none`), hidden |
| `plotregion(style(foreground))` | fill and outline `#000000` |
| `plotregion(lstyle(foreground))` | outline `#000000` |

Across copies (each copy edits the last):

| Copies | twoway |
|---|---|
| `plotregion(color(red)) plotregion(lcolor(blue))` | fill red, outline blue |
| `plotregion(lcolor(blue)) plotregion(color(red))` | outline red |
| `plotregion(color(red)) plotregion(c(blue))` | fill and outline blue |
| `plotregion(fcolor(red)) plotregion(style(none))` | no plot rects |
| `plotregion(lcolor(red)) plotregion(lstyle(none))` | outline opacity 0 |
| `plotregion(fcolor(blue)) plotregion(color(red))` | fill and outline red |
| `plotregion(color(red)) plotregion(fcolor(blue))` | fill blue, outline red |
| `plotregion(style(none)) plotregion(fcolor(red))` | fill red, no outline |
| `margin(zero)` then `margin(l+10)` | left 10 %, other sides zero (S47) |

by(): `by(foreign) plotregion(fcolor(red)) graphregion(fcolor(blue))` fills each panel's plot region red and draws no blue (research §3.2); dash paints every panel's border blue in both modes (§3.3). That is IR-9's residual, not this section's.

### E5. Bokeh (research §3.4, critic)

`Plot.border_line_color/width/dash/alpha` exist in bokeh 3.8.0 and 3.9.0 (`'border_line_color' in Plot.properties()`), drawn round the whole canvas. A `BoxAnnotation` on `Node(target="canvas")` is clipped to the frame, so the graph region's inner box cannot be drawn (P1.20.3).

### E6. Tests that pin today's behaviour (flipped in place, never deleted; re-measured in 38-07)

- `test/test_option_validation.py::TestTheRemainingSilentSites::test_a_good_graph_level_colour_is_silent_and_honoured` (:1084-1094): its comment "graphregion(color()) is applied after bgcolor(), so it wins" (:1091) — the assertion stays true for a new reason (IR-2); the flip rewrites the comment and adds the lone-`bgcolor` assertion.
- `test/test_help_claims_7.py::TestRegionColours::test_the_option_sets_the_property[bgcolor(navy)|bgcolor(255 0 0)|bgcolor(#1a476f)]` (`_REGION` rows :205-207): a lone `bgcolor()` set `border_fill_color`; now it leaves it.
- `test/test_help_claims_7.py::TestTheNewHelpers::test_the_region_readers_unquote` (:1134-1141): calls the deleted readers; ported to `_dash_region_spec`.
- `test/test_unsupported_report_is_true.py` `LIVE_VALUES["bgcolor"]` (:514, `({}, {}, "scatter", ("bgcolor", "red", "blue"))`): two lone `bgcolor()` pages are now byte-identical. Its graph tuple gains a fourth element, `{"graphregion": "color(none)"}`, which `_live_pair` (:573, today `key, a, b = g`) merges into both graph-option dicts.
- `test/function_test_map.py:688-690` (`_extract_region_*`) are removed with their functions.
- Guards that must stay green: `test_option_validation.py::TestABadStyleValueNeverAborts` (:1005-1023; the `plotregion(lwidth(abc))` note text is kept), `test_scheme_visual_truth.py::test_graph_region_is_what_stata_drew` (:250) and `::test_apply_to_figure_borders_the_plot_region_as_stata_does` (:402), `test_help_claims_7.py::TestAdversarialLegendAxesRegions` (:1195), `test_twoway_option_parity.cscript` r28/e28 (:1471-1472, different keys merge as before).

### E7. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, index at `c96facd`, research §6 and critic)

| Symbol | Risk | Action |
|---|---|---|
| `DashRenderer._make_figure_body` | CRITICAL (4) | warn; 47 lines replaced by one call |
| `ServerAppBuilder._generate_app_source` | HIGH (5) | warn; 38 template lines replaced by one |
| `ServerAppBuilder._glyph_layer_lines` | HIGH (4) | warn; three names out, four in, at the same place |
| `_extract_region_color/_lcolor/_lwidth` | LOW (3 each) | deleted |
| `_dash_graph_color` | LOW (3) | no longer called for regions; kept (KPI and others) |
| `_dash_report_suboptions`, `translate_mcolor` | CRITICAL | called, not edited |
| `OptionTranslator.parse_color_alpha` | LOW (5) | called |
| Mata `_dash_rep_subs`, `_dash_so_rows`, `_dash_so_family`, `_dash_subreq_add`, `_dash_subreq_check` | UNKNOWN | grep: S10's callers only; treated as HIGH |

## User stories

- **US-38.1** As a twoway user, I want `plotregion(c(red) lc(navy) lw(thick) lp(dash))` and `graphregion(fc(gs14) lcolor(red))` drawn as twoway draws them, in the saved page and the served app, before and after I move a filter, so my do-file's regions look as in Stata.
- **US-38.2** As a twoway user, I want `none`, `%50`, `style(none)`, `lstyle(none)` and named styles such as `style(foreground)` to draw what twoway draws, so a transparent or bare region looks the same.
- **US-38.3** As a twoway user, I want `bgcolor()` to behave as twoway's (under the graph region), so `bgcolor(red) graphregion(color(none))` shows red and a lone `bgcolor(red)` does not.
- **US-38.4** As a twoway user, I want repeated copies (`plotregion(color(red)) plotregion(lcolor(blue))`) to combine as twoway combines them.
- **US-38.5** As a twoway user, I want dash to refuse the region sub-options twoway refuses, with twoway's words, and to name the ones it accepts but cannot draw.
- **US-38.6** As a dashboard publisher, I want region text never to reach the page as code or CSS.

## Business requirements

- **BR-38.1** Every sub-option of E3, at every spelling from its minimum to its full name and in lower case, has the full name's effect, in `plotregion()` and `graphregion()`, in both modes.
- **BR-38.2** `color()` sets fill and outline; `fcolor()` the fill; `lcolor()`, `lwidth()`, `lpattern()` the outline. Within one copy the outline is `color()` over `lcolor()` over `lstyle()`, and the fill is `fcolor()` over `color()` over `style()`, whatever the typed order. `lstyle(none)` removes the outline until a colour revives it (`lwidth()` alone does not). Widths are on Stata's line ladder (S13), with `*#` multiplying the scheme's region width.
- **BR-38.3** `none` (as typed, lower case) draws nothing and shows what lies beneath: the plot region shows the graph region's colour, the graph region the canvas. `%NN` draws at that opacity over what lies beneath. An unknown colour is drawn black with a note (S30).
- **BR-38.4** `style()` takes an area style name and `lstyle()` a line style name, as `style_bundle` resolves them; an unknown name draws the class default with S36's note.
- **BR-38.5** The graph region's outline is drawn when any outline setting is given; its default colour is the graph region's fill and its default width the ladder's `thin`.
- **BR-38.6** `bgcolor()` is the canvas under the graph region. It shows only where the graph region (or, through it, the plot region) is `none` or translucent; `bgcolor(none)` is the colour `none`, black. With no `bgcolor()` the canvas is the scheme's `color background`. `plotbgcolor()` (dash's own) stays the plot region's fill, applied before `plotregion()`.
- **BR-38.7** Repeated copies combine as twoway applies them, each copy editing the last (E4's table); every `margin()` copy is kept, in order.
- **BR-38.8** dash refuses r(198), in twoway's words: an unknown or capitalised sub-option, a spelling shorter than the minimum, a sub-option or `marginonly` given twice in one copy, a word after a comma inside the region (`invalid '<word>'`); `graphregion()` is checked before `plotregion()`, and both before `legend()` and the axis options.
- **BR-38.9** `lalign()`, `ilalign()`, every `i*` option, `margin()`, `shadestyle()`, `ishadestyle()`, `intensity()`, `iintensity()` and `marginonly` are accepted and named, once per region per graph, in one note; nothing else is printed where twoway prints nothing (M6).
- **BR-38.10** A graph with no region option draws exactly as before. Region settings hold before and after every filter move in both modes. Only computed colours and numbers reach the page.

## Technical requirements

- **TR-38.1 The region table** (dash_render.py, new `_dash_region_table()`, directly after `_dash_unquoted`). It returns a tuple of rows in S10's six-column shape `(full, minimum, 1, kind, False, "")` (one stage, `star=False`) in E3's declaration order: style/sty, istyle/isty, lstyle/ls, ilstyle/ils, lcolor/lc, ilcolor/ilc, lwidth/lw, ilwidth/ilw, lpattern/lp, ilpattern/ilp, lalign/la, ilalign/ila, shadestyle/shades, ishadestyle/ishades, fcolor/fc, ifcolor/ifc, color/c, icolor/ic, intensity/inten, iintensity/iinten, margin/m (kind `"a"`), marginonly/marginonly (kind `"w"`). A function, not a constant, so it travels on the functions tuple at the place R2 gives S38. Comment: `_fr_area_parse_and_log.ado:33-43`. Names are canonicalised by S10's `_dash_subopt_canon(name, _dash_region_table())`.
- **TR-38.2 `_dash_region_spec(raw, option, base, scheme, ref_in)`** (new, after the table). Reads one (merged) copy and returns `(settings, named)`.
  - Tokens from `_dash_by_tokens(str(raw))` (quote-aware, linear). Text after a top-level comma is ignored here (dash.ado refuses it).
  - `settings` starts as a copy of `base` (`fill`, `fill_alpha`, `line`, `line_alpha`, `line_width`, `line_dash`).
  - Order, independent of typing (E3): `style` → `scheme.style_bundle("area", arg)` replaces all six; `lstyle` → `style_bundle("line", arg)` replaces the four line keys; `lcolor`, `lwidth`, `lpattern`; then `color` → line colour and alpha; then fill: `color`, then `fcolor`.
  - Colours: every colour sub-option is read by one inner step, `_read(arg, role)`, where `role` is `"fill"` or `"line"`. The step holds `current` (the role's value in `settings` at that point of the edit order) and `base_hex` (`current`, or the `base` dict's value for that role when `current` is `None`). `arg.strip() == "none"` → `None`; otherwise `OptionTranslator.parse_color_alpha(arg, f"{option}({full})", **OptionTranslator.scheme_colour_context(scheme))`. `(None, _)` keeps `current` and its alpha: a malformed value, or a bare `*#`/`%#`, which is S30's interim until S43. Otherwise the step takes the hex and alpha (alpha `None` → 1.0). `color()` calls the step once per role. **The S43 hook (Q-43.1):** S43 (P1.13b, batch 15) adds `base=base_hex` to this one `parse_color_alpha` call and writes a bare `%#` to the role's alpha. It edits `_dash_region_spec` only, never `_make_figure_body` or the template. S38 passes no `base=`.
  - Widths: `OptionTranslator.translate_lwidth(arg, default_px=settings["line_width"], ref_in=ref_in)`; `ValueError`/`TypeError` → `_dash_style_note(f"{option}(lwidth)", arg, "line width", "the default")` (today's text) and keep.
  - Patterns: `OptionTranslator.translate_lpattern(arg)`; failure → `_dash_style_note(f"{option}(lpattern)", arg, "line pattern", "the default")`.
  - With `scheme` `None`, `SchemeParser.fallback()` answers `style_bundle`.
  - `named`: every token whose canonical name is in BR-38.9's set, or that has no canonical name (a hand-written spec; dash.ado refuses it), as typed through `_dash_display`, at most 10 then `"(+<n> more)"`.
  - When a key appears twice (a hand-written spec), the last wins, silently.
- **TR-38.3 `_dash_region_blend(top, alpha, under)`** (new): `top` and `under` are `#rrggbb`; returns `#rrggbb` of `top` at `alpha` over `under` (per channel `round(a*t + (1-a)*u)`); `alpha` `None` or ≥ 1 returns `top`. Inputs not matching `#[0-9a-f]{6}` raise `ValueError` (programming error: every caller passes `stata_colour` output).
- **TR-38.4 `_dash_apply_regions(fig, graph_opts, scheme, seen=None, key="")`** (new):
  1. Return at once when `graph_opts` holds none of `plotregion`, `graphregion`, `bgcolor`, `plotbgcolor` (non-blank).
  2. Canvas `C`: `bgcolor` given → `parse_color_alpha(raw, "bgcolor", **ctx)`. A hex is composited over `#ffffff` at its alpha. `bgcolor(none)` is the colour `none`, `#000000` in S30's table, not "nothing" (BR-38.6; probe `bgcolor(none) graphregion(color(none))`). `(None, _)` → the scheme's. With no `bgcolor`, `scheme.background_color` (the fallback scheme when `None`).
  3. Graph base: fill `scheme.background_color`, line `scheme.background_color`, `line_width` = `translate_lwidth("thin", ref_in=ref_in)`, dash `[]`, alphas 1.0. `_dash_region_spec(graphregion, "graphregion", …)`.
  4. `fig.border_fill_color` = `C` when the fill is `None`, else `_dash_region_blend(fill, fill_alpha, C)`; `border_fill_alpha = 1.0`.
  5. When the graph spec holds any outline-setting token (`style lstyle lcolor lwidth lpattern color`): `border_line_color` (None when not drawn), `border_line_alpha`, `border_line_width`, `border_line_dash`.
  6. Plot base: fill `scheme.plotregion_color`, line `scheme.plotregion_line_color`, width `scheme.plotregion_line_width`, dash `[]`; `plotbgcolor` (if given) is applied first as a `fcolor()` of the plot copy (`"fcolor(" + raw + ")"` is never built: its parsed `(hex, alpha)` is set on the base directly).
  7. `fig.background_fill_color` = the graph region's resolved colour (step 4) when the fill is `None`, else the blend over it; `background_fill_alpha = 1.0`; `outline_line_color/alpha/width/dash` from the spec.
  8. `_dash_report_suboptions("graphregion", named_g, seen, key)`, then `("plotregion", named_p, …)`.
  - `ref_in` is `OptionTranslator.size_ref_of(fig)` (S08); if S08 named it otherwise, use its name.
- **TR-38.5 Both modes.**
  - Saved: in `_make_figure_body`, replace the block from the comment `# Figure background colors` through the graphregion block's last line (30333-30379 at `c96facd`) with `_dash_apply_regions(fig, graph_opts, self.scheme, _seen, _gkey)` under a three-line comment (IR-2, one reader for both modes).
  - Served: in `_generate_app_source`, replace the emitted lines from `"        # bgcolor / plotbgcolor — figure background colors",` through `"                if _c: fig.border_fill_color = _c",` (35219-35256) with `"        _dash_apply_regions(fig, go, <scheme>, _reported_subopts, gname)",`, where `<scheme>` is the expression the template passes to `_dash_text_annotations` on its next lines (`_DASH_SCHEME` at `c96facd`).
  - Copy list (R2 row S38): in `_glyph_layer_lines`' functions tuple remove `"_extract_region_lwidth",` (33388), `"_extract_region_color",` and `"_extract_region_lcolor",` (33391-33392) and put `"_dash_region_table", "_dash_region_spec", "_dash_region_blend", "_dash_apply_regions",` in their place, with the comment reworded; `"_dash_unquoted"` stays.
  - Delete `_extract_region_color`, `_extract_region_lcolor`, `_extract_region_lwidth` (`grep -n "_extract_region_" dash_render.py` must print nothing).
  - No JavaScript twin: a filter move rebuilds sources only (saved `_FILTER_JS`, served `_dash_redraw_for`), never figure properties.
- **TR-38.6 Mata: the region family** (dash_parse.mata, in S10's functions, found by name).
  - `_dash_so_rows("region")` returns TR-38.1's rows in S10's six-column shape (`full min "1" kind "0" ""`).
  - `_dash_so_family(key)` returns `"region"` for `plotregion` and `graphregion` (after `_dash_rep_bare`).
  - New `string scalar _dash_rep_region(string rowvector w1, string rowvector n1, string rowvector w2, string rowvector n2)` (after `_dash_rep_subs`): copy 1's words and full names, then copy 2's; returns the merged words as `full(arg)`, copy 1's survivors then copy 2's, by these rules for each name in copy 2 (and the same for the `i` twins: istyle, ilstyle, ilcolor, ilwidth, ilpattern, ilalign, ishadestyle, ifcolor, icolor, iintensity):
    - `style` drops copy 1's style, lstyle, lcolor, lwidth, lpattern, lalign, shadestyle, color, fcolor, intensity;
    - `lstyle` drops lstyle, lcolor, lwidth, lpattern, lalign, and rewrites copy 1's `color(x)` to `fcolor(x)` unless copy 1 has `fcolor`, then drops it;
    - `shadestyle` drops shadestyle, fcolor, intensity and rewrites `color(x)` to `lcolor(x)` unless copy 1 has `lcolor`, then drops it;
    - `color` drops color, fcolor, lcolor;
    - `fcolor` drops fcolor and rewrites `color(x)` to `lcolor(x)` (or drops it, as above);
    - `lcolor` drops lcolor and rewrites `color(x)` to `fcolor(x)` (or drops it);
    - `lwidth`, `lpattern`, `lalign`, `intensity`, `marginonly` drop their own name;
    - `margin` drops nothing: every copy's `margin()` is kept, in order.
    No `regexm`; byte loops through S10's helpers.
  - `_dash_rep_subs`: when `_dash_so_family(key) == "region"`, resolve each side alone with `_dash_so_resolve(…, "region", …)` and return `_dash_rep_region(…)`; S10's steps 3-6 are not run for it. A word with no full name (dash.ado refuses it first) keeps its typed form and the last of its typed name wins.
  - Header index (dash_parse.mata:1-303) gains `_dash_rep_region`, in place.
- **TR-38.7 Mata: refusals.**
  - `_dash_subreq_add` also records each raw token whose lower-case name is a prefix of `graphregion` at least `graphr` long or of `plotregion` at least `plotr` long (the minimums `dash.sthlp:2731` states), with its whole value.
  - `_dash_subreq_check("region")` resolves every recorded `graphregion` copy, in (seg, place) order, then every `plotregion` copy, each copy alone with `_dash_so_resolve(…, "region", …)`, and returns the first problem as 198 with S10's message (`option <shown> not allowed`). Before resolving a copy: a top-level comma followed by a word gives `invalid '<that word cut at "(">'`; a comma followed by blanks only is ignored. After resolving it: a `w` row named twice gives `option <second as typed> not allowed`. The record is cleared on every refusal and at the end.
  - dash.ado `_dash_plot`: `_dash_subopt_check region` directly before S10's `_dash_subopt_check legend`. `_dash_subopt_check` needs no change for a kind that never returns −1; if S10 wrote it with a kind list, `region` is added there.
  - `_needed` (dash.ado:255 at `c96facd`) gains `_dash_rep_region`.
  - Every message goes through `_dash_say("err", …)`; region text is never put on a command line.
- **TR-38.8 Registries.** Under S38's anchor in `test/function_test_map.py`: `'_dash_apply_regions'`, `'_dash_region_blend'`, `'_dash_region_spec'`, `'_dash_region_table'`, each to its `test/test_region_options.py` node (TDD stubs); delete the three `_extract_region_*` keys (:688-690). Under S38's `COVERAGE["dash_parse.mata"]` anchor in `test/program_coverage_map.py`: `"_dash_rep_region"` → `test/test_twoway_option_parity.cscript` (RS-12). X.5: its `_needed` entry is TR-38.7's.
- **TR-38.9 Help** (dash.sthlp, Region Styling Options, 2685-2734; R3 row S38). Rewrite the synopt table and the paragraphs, found by their text: every sub-option of E3 with its minimum spelling underlined (`{cmdab:c:olor(}`…), what each draws, `none`, `%#`, `style()`/`lstyle()` names, the graph outline, the canvas meaning of `bgcolor()` (replacing ":2717-2721" "dash colors the graph region itself" with twoway's rule and the example `bgcolor(red) graphregion(color(none))`), `plotbgcolor()` as the plot fill, the refusals, and the named list ("drawn by a later release" is not said; "named in a note" is). Lines ≤ 79 characters; no tool or vendor name. The `plotr()`/`graphr()` abbreviation sentence stays.
- **TR-38.10 Security (rule 1).** Region text is parsed by `_dash_by_tokens` and `_dash_subopt_canon` (linear, no regex over the whole text); values reach Bokeh only as `#rrggbb` strings that `stata_colour` produced, `None`, floats from `translate_lwidth` and dash lists from `translate_lpattern`; no style attribute, CSS string or HTML is built from it; every echo goes through `_dash_display` (Python) or `_dash_say` (Mata). G9's threat: injected CSS or script through a region colour; closed by construction and pinned by `TestHostileRegionText`.

## Boundaries

- **S47 (P1.20b):** `margin()` of either region, the plot region's inner box (`i*`) and their notes; S38 only keeps every `margin()` copy in the merge and names them. `_dash_plot_margin`, `_dash_padded_range`, `_dash_apply_scale_ranges` are not touched.
- **S43 (P1.13b):** a bare `*#`/`%#` at the region sites; S38 keeps the site's colour for them.
- **S53/IR-9:** `by(, graphregion() plotregion())` and the outer `graphregion()` on a by() graph stay as they are (drawn per panel / named by by()); residual for S58.
- **S15/S24/S33 (scheme chrome):** `SchemeParser.apply_to_figure` is not edited; the scheme's default region pattern (`linepattern plotregion`, read by no one) stays unread.
- **S10's tables for other families**, `_dash_subopt_canon`, `_dash_so_resolve` and `_dash_subopt_check`'s numeric loop are called, not edited.
- **Not touched:** `_apply_mlabel_opts` and S37's other functions; `_FILTER_JS`; `_build_filter_widgets`; `_dash_graph_color`'s body; `translate_mcolor`; `_dash_report_suboptions`; the KPI's `bgcolor()` (a different option, dash.sthlp:1453).
- **Never:** a CSS path for regions; a hand edit of a generated file; `scripts/regen_option_surface.py` (IR-7).

## Stata truth

### `scripts/extract_region_truth.do` → `test/fixtures/region_truth.json`

S02's stanza (TR-02.9, `<file>` its own name), then `adopath ++ "`repo'/"` and `global dash_nobrowser 1`. `_meta` and the python reader copy S19's `scripts/extract_series_label_truth.do` (`stata_version`, `born_date`, `dash_commit` from `git rev-parse HEAD` captured with `shell` into a local and read through `Macro.getLocal`, `extracted`; never `shell=True`; a backtick written `\x60`). Data `sysuse auto`; commands `twoway scatter mpg weight, <opt>`; each probe under `capture noisily` inside a named log so its error line and notes are recorded.

- **S (spellings), nodraw, s2color:** for each row of E3 and each prefix length 1..len(full), `plotregion(<prefix>(red))` (`<prefix>` alone for `marginonly`), and the capitalised full name: rc. About 210 probes.
- **R (refusals), nodraw:** the 17 refusal and order lines of E4 (R01-R17, as listed there, in that order): rc and first error line.
- **D (drawing), exported to `c(tmpdir)` as SVG, under s2color, stcolor and s1color:** D01-D40: the 23 drawing rows of E4, plus `plotregion(lstyle(p3))`, `plotregion(style(bogus))`, `plotregion(lpattern(bogus))`, `plotregion(lcolor(notacolour))`, `plotregion(lalign(inside) lwidth(vthick))`, `plotregion(ifcolor(red))`, `graphregion(ifcolor(red))`, `plotregion(intensity(50) fcolor(red))`, `bgcolor(none) graphregion(color(none))`, `graphregion(lpattern(dash) lcolor(red))`, `plotregion(lw(*2))` and `graphregion(fcolor(red%50))`.
- **M (merges), SVG, s2color:** M01-M09, E4's across-copies table less the margin row.
- **B (by), SVG, s2color:** B01 `by(foreign) plotregion(fcolor(red)) graphregion(fcolor(blue))`, recorded for the closeout only.
- **Records:** per probe `cmd`, `rc`, `err`, `notes`; for SVG probes `canvas`, `graph_fill`, `graph_line`, `plot_fill`, `plot_line`, each `null` when absent, else `{fill|stroke, opacity, width, dasharray}`. Roles from a new `svg_rects(path)` in `scripts/svg_truth.py` (after `svg_fills`; each `<rect>` in document order with `x, y, w, h, fill, fill_opacity, stroke, stroke_width, stroke_opacity, dasharray`): `canvas` is the first rect; graph rects have `x < 20`; plot rects the rest; a rect with fill `none` is the outline.
- Run: `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_region_truth.do"` (log `$S/extract_region_truth.log`, about 400 probes, 135 exports). `git add -f test/fixtures/region_truth.json`.

### Area cases, `test/test_twoway_option_parity.cscript` (R1; one contiguous run before the `// Summary` divider; after S37's MV run once both land)

Each case runs live twoway (`capture twoway … nodraw`, rc and first error line from a log) and dash (`_ztp_run`) in the script's `nfail`/`faillist` form, printing `RS-nn PASS: …`.
- **RS-01:** E4's 13 refusal lines (R01-R13): dash rc and first line equal twoway's.
- **RS-02:** the order lines (graph before plot in both typed orders; region before `legend(bogus)` and `xline(abc)`).
- **RS-03:** every spelling of every row (min to full) rc 0 in both; one letter shorter refused in both (`st()`, `is()`, `l()`, `in()`, `shad()`).
- **RS-04:** `plotregion(color(red),)` rc 0 both; `plotregion(lalign(bogus))`, `margin(bogus)`, `lcolor(notacolour)` rc 0 both.
- **RS-10:** `_dash_rep_merge("plotregion", "color(red)", "c(blue)")` is `color(blue)`; `("plotregion","color(red)","lcolor(blue)")` is `fcolor(red) lcolor(blue)`; `("plotregion","lcolor(blue)","color(red)")` is `color(red)`; `("plotregion","fcolor(red)","style(none)")` is `style(none)`; `("plotregion","margin(zero)","margin(l+10)")` is `margin(zero) margin(l+10)`; `("graphregion","color(red)","margin(zero)")` is `color(red) margin(zero)` (r28's).
- **RS-11:** the spec of `plotregion(c(red)) plotregion(lc(blue))` holds `fcolor(red) lcolor(blue)` (`_ztp_hasval`).
- **RS-12:** M01-M09 merged by `_dash_rep_merge` give the strings TR-38.6 implies (one assertion each).

### The S38 block of `test/test_wp30_truth.cscript` (R1)

Fills S01's S38 stub. A helper `_s38_page` (python, directly above S38's header) loads a saved page's document JSON and returns the first figure's `background_fill_color`, `border_fill_color`, `outline_line_color/alpha/width/dash`, `border_line_color/alpha/width`.
- **RS-20:** `dash scatter mpg weight, plotregion(c(red) lc(navy) lw(thick) lp(dash)) saving(…)`: fill red, outline navy, dashed, width over the default equal to twoway's 23.04/5.76 within 2 %.
- **RS-21:** `bgcolor(red) graphregion(color(none)) plotregion(fcolor(none))`: border and background `#ff0000`, as twoway's canvas.
- **RS-22:** `plotregion(style(none))`: background equals border, outline `None`.
- **RS-23:** `plotregion(lalign(inside) ifcolor(red))`: rc 0 and one note naming both.

## TDD test stubs

### Regression tests, new `test/test_region_options.py` and `test/test_region_truth.py` (red at the batch-13 base unless marked guard; 38-01, 38-02)

`test_region_truth.py`: `_FIX = json.load(test/fixtures/region_truth.json)`; `_both(go, scheme)` renders `[plot_for("scatter")]` saved (`test_mode_parity._standalone`) and served (`_served`) and returns both first figures.
- Test: the fixture has the four `_meta` keys, `stata_version` starting `19.`, every probe id — `TestTheFixture::test_it_is_stamped`
- Test: `_dash_region_table()`'s spellings equal the S probes: every recorded rc-0 prefix canonicalises to its row, every refused one to `None` — `TestTheTable::test_it_is_twoways_parser` [AttributeError]
- Test (both modes, three schemes): for D01-D40 and M01-M09, dash's plot fill, graph fill (after compositing), outline colour, presence, opacity and dash pattern equal the fixture's; widths as ratios to D01's within 2 % — `TestAgainstTwoway::test_probe[<scheme>-<id>-saved|served]` (an M probe is rendered from the merged string TR-38.6 gives for it, written in the test's `_MERGED` table, which RS-12 holds equal to `_dash_rep_merge`'s output)
- Guard: B01 is recorded with `twoway_draws_outer_graphregion == False` — `TestTheFixture::test_the_by_residual_is_recorded`

`test_region_options.py` (unit and both-mode tests; harness from `test_mode_parity`: `_standalone`, `_served`, `_served_after_move`, `_MOVES`; from `test_saved_filter_layers`: `_render`, `_move`):
- Test: `_dash_region_spec("c(red) lc(navy) lw(thick) lp(dash)", "plotregion", base, s2, 4.0)` sets fill and line red/navy, the thick width, a dash list; no named token — `TestTheSpec::test_abbreviations_read_as_full_names`
- Test: E3's order: `fcolor(blue) color(red)` and `color(red) fcolor(blue)` both fill blue, line red; `lcolor(blue) color(red)` line red; `lstyle(none) lcolor(red)` red; `lstyle(none) lwidth(thick)` line `None` — `TestTheSpec::test_the_edit_order`
- Test: `fcolor(none)`, `color(none)`, `lcolor(none)`, `style(none)` give `None`s; `NONE` is black with S30's note — `TestTheSpec::test_none_paints_nothing`
- Test: `fcolor(red%50)` → `#ff0000`, alpha 0.5; `lcolor(red%50)` → line alpha 0.5 — `TestTheSpec::test_opacity`
- Test: `style(foreground)` and `lstyle(foreground)` give `style_bundle`'s values; `style(bogus)` the class default with one note — `TestTheSpec::test_style_names`
- Test: `lalign(inside) ilcolor(red) margin(zero) shadestyle(x) intensity(50) marginonly` → all six named as typed; 25 named tokens → ten then `(+15 more)` — `TestTheSpec::test_what_is_named`
- Test: `_dash_region_blend("#ff0000", 0.5, "#0000ff") == "#800080"`; `None` and 1.0 return top; `"red"` raises — `TestTheBlend::test_over_under`
- Test (both modes): `plotregion(c(red))` fill and outline red — `TestBothModes::test_color_sets_fill_and_outline[saved|served]`
- Test (both modes): `bgcolor(red)` alone leaves `border_fill_color` at the scheme's; `bgcolor(red) graphregion(color(none))` → `#ff0000`; `… plotregion(fcolor(none))` → background `#ff0000` too; `graphregion(fcolor(red%50)) bgcolor(blue)` → `#800080` — `TestBothModes::test_bgcolor_is_the_canvas[saved|served]`
- Test (both modes): `plotregion(fcolor(none))` background equals border; `graphregion(color(none))` border is the scheme's background — `TestBothModes::test_none_shows_what_lies_beneath[saved|served]`
- Test (both modes): `graphregion(lcolor(red) lwidth(thick))` sets `border_line_color` `#ff0000` and the thick width; `graphregion(lwidth(thick))` sets the background colour; no graph-outline option leaves `border_line_color` at Bokeh's default — `TestBothModes::test_the_graph_outline[saved|served]`
- Test (both modes): `plotregion(lpattern(dash))` sets `outline_line_dash` to `translate_lpattern("dash")` — `TestBothModes::test_the_outline_pattern[saved|served]`
- Test (both modes): the notes of `plotregion(lalign(inside) ifcolor(red)) graphregion(margin(zero))` are one `plotregion()` and one `graphregion()` note; a by() graph prints each once — `TestBothModes::test_one_note_per_region[saved|served]`
- Test: saved (node) and served moves keep every region property — `TestAfterAFilterMove::test_regions_survive[saved|served]`
- Guard: a graph with none of the four options has every figure property `apply_to_figure` set, in both modes — `TestTheEmptyPathIsInert::test_untouched[saved|served]`
- Test: the merge cases of E4 through `_dash_rep_merge` (a Stata run through the driver of a tiny do-file, skipped with a reason when Stata is absent, as `test_varlist_expansion` does) — `TestTheMerge::test_measured_pairs[M01..M09]`
- Test: hostile region text — `color("red;}</style><script>x</script>")`, `ifcolor(red;background:url(x))`, `margin(1;x:y)`, a 100 KB value, 10,000 nested parentheses, a NUL, `lcolor(‮)` — renders in both modes under 1 s, every region property is `#rrggbb`, `None`, a number or a list of numbers, the page text holds no payload outside JSON-escaped spec strings, and every note is at most 80 printable characters per token — `TestHostileRegionText::test_inert[<case>-saved|served]`
- Test: the generated app defines the four helpers and not `_extract_region_color` — `TestTheServedCopy::test_the_app_carries_the_reader`
- Test: dash.sthlp's Region Styling Options names `{cmdab:c:olor(}`, `bgcolor(red) graphregion(color(none))` and no "colors the graph region itself" — `TestTheHelp::test_the_help_is_twoways`
- Test (cscript): RS-01..RS-04, RS-10..RS-12; RS-20..RS-23.
- Shared: `test/test_mode_parity.py` CORPUS gains `_case("Region styling (WP-30 P1.20a)", [_sc()], None, {"plotregion": "c(red) lc(navy) lp(dash)", "graphregion": "fc(gs14) lcolor(red)", "bgcolor": "blue"})` and `_case("Regions none over the canvas (WP-30 P1.20a)", [_sc()], None, {"bgcolor": "red", "graphregion": "color(none)", "plotregion": "fcolor(none)"})`; `_annotations` is not edited (figure properties are compared by `_render_pair`'s figure profile; if they are not, extend the profile with the eight region properties and say so in the commit body).

### Pinned tests to flip (R9; re-measured, never trusted)

E6's four flips: the `test_option_validation.py:1091` comment and an added lone-`bgcolor` assertion; `_REGION`'s three `bgcolor` rows to expect the base figure's `border_fill_color` (`dr.SchemeParser("s2color").background_color` under the harness's default scheme), with `TestRegionCanvas` in the new file carrying the canvas cases; `test_the_region_readers_unquote` → `_dash_region_spec('lwidth(2) color("0 0 255")', …)` fill `#0000ff` and `lcolor("1 2 3")` line `#010203`; `LIVE_VALUES["bgcolor"]` (:514, today `({}, {}, "scatter", ("bgcolor", "red", "blue"))`) → `({}, {}, "scatter", ("bgcolor", "red", "blue", {"graphregion": "color(none)"}))`. `_live_pair` (:573) unpacks the graph tuple as `key, a, b, *extra = g` and returns `{**(extra[0] if extra else {}), key: a}` and the same with `b`, so every 3-tuple row is unchanged.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Spellings, refusals, order | cscript RS-01..RS-04 vs live twoway; pytest `TestTheTable` | `region_truth.json` S, R | n/a |
| Merge | cscript RS-10..RS-12; pytest `TestTheMerge` | M probes | n/a |
| Drawing vs twoway | pytest `TestAgainstTwoway` (3 schemes); cscript RS-20..RS-23 | D, M probes | yes |
| Reader units | pytest `TestTheSpec`, `TestTheBlend` | literal | n/a |
| Canvas, none, outline, pattern, notes | pytest `TestBothModes` | literal | yes |
| After moves | pytest `TestAfterAFilterMove` (node saved; served) | `_DF` | yes |
| Inert empty path | `TestTheEmptyPathIsInert`; `_SINGLE_Y_BASELINE_SHA256` unchanged | corpus | yes |
| Security | `TestHostileRegionText` | literal | yes |
| Parity | `test_mode_parity.py` two CORPUS cases | `_DF` | yes |
| Served wiring | `TestTheServedCopy`; G4 guards | generated app | served |
| Help, registries, tracking | `TestTheHelp`, `test_help_claims_7.py`, `test_function_test_map.py`, `test_program_coverage_map.py`, `test_tracking_documents.py`, `test_fixtures_are_committed.py` | — | n/a |

**Acceptance criteria.**
- **AC-38.1** (BR-38.1, BR-38.8) RS-01..RS-04 PASS against live twoway; `TestTheTable` passes.
- **AC-38.2** (BR-38.2-BR-38.6) `TestAgainstTwoway` passes for every D and M probe under s2color, stcolor and s1color in both modes; `TestTheSpec`, `TestTheBlend`, `TestBothModes` pass; RS-20..RS-22 PASS.
- **AC-38.3** (BR-38.7) RS-10..RS-12 and `TestTheMerge` pass; `margin()` copies survive in order.
- **AC-38.4** (BR-38.9) `test_what_is_named` and `test_one_note_per_region` pass; RS-23 PASS.
- **AC-38.5** (BR-38.10) `TestTheEmptyPathIsInert`, `TestAfterAFilterMove` (node not skipped) and `TestHostileRegionText` pass; the single-y digest pin is unchanged; `test_mode_parity.py` passes with untouched `ALLOWED`/`_MUST_WARN`.
- **AC-38.6** Every flipped node passes with its `Flipped:` line; none is deleted; one full run through the queue reports 0 failed; G7 prints 0 before and after the commit.

## Tasks

**Commit boundary.** Tasks 38-01 to 38-11 form one commit, made by 38-11 on `wp30-s38` with the subject `Draw plotregion() and graphregion() styling as twoway does (WP-30 P1.20a)`; it closes the entry, deletes its key and replaces both markers. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s38`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`; every command uses `git -C "$WT"` or `$WT` paths. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S38 "$SLOT" "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`).

<task type="auto" id="38-01">
  <name>Write the region fixture and truth tests</name>
  <files>scripts/extract_region_truth.do, scripts/svg_truth.py, test/test_region_truth.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-13-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s38`; stop otherwise. Add `svg_rects(path)` to `scripts/svg_truth.py` directly after `svg_fills` (its docstring names the ten keys of "Stata truth"); edit no other function there. Create `scripts/extract_region_truth.do` exactly as "Stata truth" describes (S02's stanza, the S, R, D, M and B probes, named logs, the python reader through `svg_rects`, S19's `_meta` form) and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_region_truth.do"`; it writes `test/fixtures/region_truth.json`. Create `test/test_region_truth.py` with its stubs, naming `dr._dash_region_table` and `dr._dash_apply_regions` so they fail with AttributeError now. Run `python3 -m pytest test/test_region_truth.py -q -n 6 -p no:cacheprovider -rf > "$S/38-new.log" 2>&1`. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/region_truth.json')); p=d['probes']; print(all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')), p['R01']['err'], p['s2color|D02']['plot_line']['stroke'])"` prints `True option bogus() not allowed #ff0000`; `grep -c FAILED "$S/38-new.log"` is at least 5; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata dash_render.py` prints nothing.]]></verify>
  <done>The twoway region fixture existed and the truth tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="38-02">
  <name>Write the unit, mode and security tests</name>
  <files>test/test_region_options.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Create `test/test_region_options.py` with every stub of "TDD test stubs" for that file (module docstring: the defect, E3, E4, IR-2), naming `dr._dash_region_spec`, `dr._dash_region_blend`, `dr._dash_apply_regions`. Append the two CORPUS cases to `test/test_mode_parity.py` before `CORPUS`'s closing bracket, after any earlier section's cases. Run `python3 -m pytest test/test_region_options.py -q -n 6 -p no:cacheprovider -rf >> "$S/38-new.log" 2>&1` and `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider -k "P1.20a" -rf >> "$S/38-new.log" 2>&1`. Write `$S/38-P1.20a-failure.txt`: the base sha, one line per failing node of both files, then "Guards (pass at the base)" listing `TestTheEmptyPathIsInert` and any other passing node. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/38-new.log"` is at least 30; `grep -c "TestTheEmptyPathIsInert" "$S/38-P1.20a-failure.txt"` is at least 1; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata dash_render.py` prints nothing.]]></verify>
  <done>Every pytest regression test of the section was shown failing on the unmodified tree, with the failure text and the guards saved.</done>
</task>

<task type="auto" id="38-03">
  <name>Write the refusal and truth script cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    In `test/test_twoway_option_parity.cscript` add, directly before the `// Summary` divider (after AX-08's block on this worktree; S37's MV run is not on it, and the merger places RS after MV at landing, R1), one contiguous run headed `// RS: plotregion()/graphregion() sub-options, read as twoway reads them (WP-30 P1.20a)` with RS-01..RS-04 and RS-10..RS-12 of "Stata truth" in the script's `nfail`/`faillist` form. In `test/test_wp30_truth.cscript` put `_s38_page` directly above S01's `* ==== S38 P1.20a: …` header and RS-20..RS-23 between S38's start and end lines. Run both through the driver on the unmodified shipped files and append every `RS-nn FAIL` line, with the twoway line it quotes, to `$S/38-P1.20a-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "RS-(0[1-3]|1[0-2]) FAIL" "$S/run_test_twoway_option_parity.log"` is at least 5; `grep -cE "RS-2[0-3] FAIL" "$S/run_test_wp30_truth.log"` is at least 3; `grep -c "AX-08 PASS" "$S/run_test_twoway_option_parity.log"` prints 1 (the worktree is cut from `batch-13-base`, which has no MV run: S37's run lands first and the merger keeps RS after it, R1).]]></verify>
  <done>The live twoway comparisons for refusals, merges and drawing were in place and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="38-04">
  <name>Refuse and merge regions in Mata</name>
  <files>dash_parse.mata, dash.ado</files>
  <action><![CDATA[
    The Mata functions are UNKNOWN to the index; grep confirms their callers are S10's (`grep -n "_dash_so_family\|_dash_rep_subs\|_dash_subreq_" dash_parse.mata dash.ado`). Apply TR-38.6 (`_dash_so_rows("region")`, `_dash_so_family`, the new `_dash_rep_region` after `_dash_rep_subs`, the region branch in `_dash_rep_subs`, the header-index entry) and TR-38.7 (`_dash_subreq_add`'s region record, `_dash_subreq_check("region")` with the comma and repeated-word rules, `_dash_subopt_check region` before `_dash_subopt_check legend` in `_dash_plot`, `_dash_rep_region` in `_needed`). Every message through `_dash_say`; no `regexm`. Edit no other function.
  ]]></action>
  <verify><![CDATA[`test_twoway_option_parity.cscript` through the driver prints `RS-01 PASS` to `RS-04 PASS` and `RS-10 PASS` to `RS-12 PASS`, and `r28`'s case still passes; `python3 -m pytest test/test_region_options.py -q -n0 -p no:cacheprovider -k TestTheMerge` passes; `python3 -m pytest test/test_program_coverage_map.py test/test_file_headers.py -q -n 6 -p no:cacheprovider` reports 0 failed except the map entry 38-08 adds.]]></verify>
  <done>dash refused the region sub-options twoway refuses, in its words and order, and merged repeated copies as twoway applies them, keeping every margin copy.</done>
</task>

<task type="auto" id="38-05">
  <name>Write the shared region reader</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add `_dash_region_table`, `_dash_region_spec`, `_dash_region_blend` and `_dash_apply_regions` directly after `_dash_unquoted`, exactly as TR-38.1-TR-38.4 and TR-38.10 state, each with a docstring citing E3/E4 (and IR-2 for the canvas). Read S08's `size_ref_of` and S13's `translate_lwidth` signature on this tree (`grep -n "def size_ref_of\|def translate_lwidth" dash_render.py`) and use the landed names. Do not wire the call sites yet.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_region_options.py -q -n 6 -p no:cacheprovider -k "TestTheSpec or TestTheBlend"` passes; `python3 -m pytest test/test_region_truth.py -q -n 6 -p no:cacheprovider -k TestTheTable` passes.]]></verify>
  <done>One reader resolved a region's fill, outline and canvas from twoway's grammar, in twoway's edit order, with only computed colours and numbers in its output.</done>
</task>

<task type="auto" id="38-06">
  <name>Wire both modes and the copy list</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_make_figure_body` is CRITICAL (4 impacted), `_generate_app_source` HIGH (5) and `_glyph_layer_lines` HIGH (4), and that S38 is batch 13's only editor of the first two (R12). Apply TR-38.5: the saved block replaced by the one call, the template lines replaced by the one emitted line (find both by their text), the copy-list swap at the three removed names, and delete the three `_extract_region_*` functions. Run every test file naming `border_fill_color`, `background_fill_color` or `outline_line_` (`grep -l` over `test/*.py`) with `-n 6`.
  ]]></action>
  <verify><![CDATA[`grep -c "_extract_region_" "$WT/dash_render.py"` prints 0; `python3 -m pytest test/test_region_options.py test/test_region_truth.py -q -n 6 -p no:cacheprovider` passes except `TestTheHelp`; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_mode_parity.py test/test_scheme_visual_truth.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The saved page and the served app drew regions through the one reader, before and after moves, and the old readers were gone from both.</done>
</task>

<task type="auto" id="38-07">
  <name>Flip the pinned region tests</name>
  <files>test/test_option_validation.py, test/test_help_claims_7.py, test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[
    Re-measure E6's pins on this tree, then flip them in place as "Pinned tests to flip" says, each with a comment `Flipped (WP-30 P1.20a): <old> was wrong because twoway paints bgcolor() under the graph region (region_truth.json D26-D29)` or, for the reader test, `… because the region reader is _dash_region_spec`. Write one `Flipped:` line per node to `$S/38-flips.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_option_validation.py test/test_help_claims_7.py test/test_unsupported_report_is_true.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "^Flipped:" "$S/38-flips.txt"` is at least 4.]]></verify>
  <done>Every test that pinned bgcolor() as the graph region's colour or called the old readers asserted twoway's behaviour, with the reason recorded.</done>
</task>

<task type="auto" id="38-08">
  <name>Register the new functions</name>
  <files>test/function_test_map.py, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-38.8: four `FUNCTIONS` keys under `# WP-30 S38 (P1.20a): …` in alphabetical order, the three `_extract_region_*` keys removed, and `"_dash_rep_region"` under S38's `COVERAGE["dash_parse.mata"]` anchor.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The new reader functions and the Mata merge function were mapped to the tests that run them, and the deleted readers were unmapped.</done>
</task>

<task type="auto" id="38-09">
  <name>Rewrite Region Styling Options in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-38.9 to the Region Styling Options section, found by `{marker region_options}`; edit no other section (R3). Every new or changed line is at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_region_options.py::TestTheHelp" test/test_help_conformance.py test/test_help_claims_7.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "colors the graph region itself" "$WT/dash.sthlp"` prints 0.]]></verify>
  <done>The help described every region sub-option, the canvas meaning of bgcolor() and what is refused and named.</done>
</task>

<task type="auto" id="38-10">
  <name>Run the section and full suites</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_region_options.py test_region_truth.py test_mode_parity.py test_saved_filter_layers.py test_option_validation.py test_help_claims_7.py test_scheme_visual_truth.py test_cscript_hygiene.py test_fixtures_are_committed.py` with `-n 6`, and `test_twoway_option_parity.cscript` plus the S38 truth block through the driver. Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run `"$S/full_suite_queue.sh" "$WT" "$S/38-full.log"` in the background, waiting for its `exit=` line and reading the log, never relaunching it (E6 for the known flaky tests).
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/38-full.log"` shows 0 failed and `exit=0`; `grep -c "RS-2[0-3] PASS" "$S/run_test_wp30_truth.log"` prints 4.]]></verify>
  <done>The section's tests, its script cases and one full suite run were green on the worktree.</done>
</task>

<task type="auto" id="38-11">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.20a"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution" and today's date as `ddmonyyyy`. Delete the `"P1.20a"` key line of `WP30_OPEN`. Replace both `<!-- WP-30 P1.20a -->` markers in place with "Notes: CHANGELOG lines". Run `test_tracking_documents.py` with `-n0`. Stage exactly dash.ado dash_parse.mata dash_render.py dash.sthlp scripts/extract_region_truth.do scripts/svg_truth.py test/test_region_truth.py test/test_region_options.py test/test_mode_parity.py test/test_twoway_option_parity.cscript test/test_wp30_truth.cscript test/test_option_validation.py test/test_help_claims_7.py test/test_unsupported_report_is_true.py test/function_test_map.py test/program_coverage_map.py BUGS.md CHANGELOG.md test/test_tracking_documents.py, and `git add -f test/fixtures/region_truth.json`; check `git -C "$WT" diff --cached --name-only` lists those 20 only (G6). Write `$S/38-message.txt` in the form of "Notes: commit message", check G7, confirm the branch, commit, check G7 again, and report the sha and message to the merger.
  ]]></action>
  <verify><![CDATA[`grep -c '<!-- WP-30 P1.20a -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.20a": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.20a)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.20a was closed naming existing tests, its markers carried the measured old and new behaviour, and one green commit on wp30-s38 was ready for the merger.</done>
</task>

## Section completion criteria

- Every region sub-option and spelling of twoway's parser is read in both modes; `color()`, `none`, `%NN`, style names, patterns, widths and the graph outline draw as the fixture's twoway SVGs under three schemes, before and after filter moves.
- `bgcolor()` is the canvas under the graph region (IR-2), flipped tests and help say so.
- Repeated copies merge as twoway applies them, margins kept in order for S47.
- dash refuses what twoway refuses (RS-01..RS-04) and names the rest in one note per region.
- `_extract_region_*` are gone; `_dash_region_table`, `_dash_region_spec`, `_dash_region_blend`, `_dash_apply_regions` and Mata `_dash_rep_region` exist, are mapped, and the first four travel to the served app.
- No CSS path; `TestHostileRegionText` green.
- One green commit `(WP-30 P1.20a)` on `wp30-s38` closes the entry, deletes its key and replaces both markers.

## Notes

- **Q-38.1, resolved by the review (no maintainer question).** twoway's parser accepts the undocumented `shadestyle()`, `ishadestyle()`, `intensity()`, `iintensity()` and `marginonly` (E3). M5 says a valid twoway option dash cannot draw is named, never refused. The register gives the same disposition to the neighbouring cases (P1.20.3 for `i*`, P1.20.5 for `lalign()`, and A23/A25 for unmeasured grammar filed as P2). No twoway truth for `intensity()`'s argument grammar inside a region was measured, so S38 names all five (BR-38.9) and does not draw them. S58 files the P2 row "region `intensity()`/`shadestyle()` named, not drawn". The fix is recorded in `review-notes/g06.md` for section 58.
- **Q-43.1 (S43's assumption), aligned here.** S38's colour reads sit in one step of `_dash_region_spec` that holds each role's current colour (TR-38.2), so S43 passes `base=` there. S43 needs no edit of `_make_figure_body` or the template. The exact S43 fix is filed in `review-notes/g06.md`.
- **Ordering inside `_dash_plot`.** The region check sits before S10's legend check because twoway parses regions first (E4: region refusals beat `legend(bogus)` and `xline(abc)`); twoway's order between regions and other graph options (titles, `by()`) was not measured beyond these.
- **Width reference.** `translate_lwidth`'s `*#` multiplies the scheme's region width (D-13d is closed here). The fixture compares widths as ratios to the base outline, so the 4-inch reference cancels.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the extractor and RS-20..RS-23 then fail or SKIP. Check the file after each slot run; a SKIP is not a pass.
- **Merge rules for the shared files.**
  - R1: RS-01..RS-12 as one run after S37's MV run in `test_twoway_option_parity.cscript`; the S38 block and its helper in their own places in `test_wp30_truth.cscript`.
  - R2: the four functions at the place of the three removed names (S38's row); map entries under S38's anchors.
  - R3: Region Styling Options only.
  - R4/R5: the two `P1.20a` markers, the entry and its key.
  - R6: Mata in S10's region slots and one new function; `_needed` gains one name; no option key added.
  - R7: one new fixture and extractor; `scripts/svg_truth.py` gains one function (no other section of batch 13 edits it).
  - R8: two CORPUS cases; `ALLOWED`/`_MUST_WARN` untouched.
  - R9: E6's flips. R10: the single-y digest must not move (a region-free page).
  - R12: batch 13's `_make_figure_body` and `_generate_app_source` editor.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `_make_figure_body`, `_generate_app_source`, `_glyph_layer_lines`, the four new functions, the three deleted readers, and test symbols of the staged files.
- **Commit message.** Subject as in "Commit boundary". Body, in order: `$S/38-P1.20a-failure.txt`; the measured defect (Overview's block and E4's bgcolor rows); what changed and where (TR-38.1-TR-38.9, both modes, Mata); the threat closed (G9: region text never reaches the page as CSS or code); then one line each: `Regression: test/test_region_truth.py::TestAgainstTwoway::test_probe -- failed at <base sha> with <text>` (and each other regression node; cscripts as `test/test_twoway_option_parity.cscript RS-01`, `test/test_wp30_truth.cscript RS-20`); the `Flipped:` lines of `$S/38-flips.txt`, e.g. `Flipped: test/test_help_claims_7.py::TestRegionColours::test_the_option_sets_the_property[bgcolor(navy)] -- bgcolor() colouring the graph region was wrong because twoway paints it under the graph region`; `Fixture: test/fixtures/region_truth.json (scripts/extract_region_truth.do)`; `BUGS.md: "<WP30_OPEN["P1.20a"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.20a). plotregion() and graphregion() are read by one reader in both modes (dash_render.py _dash_region_table, _dash_region_spec, _dash_region_blend, _dash_apply_regions, replacing _extract_region_color/_lcolor/_lwidth in _make_figure_body and the served template): every sub-option and spelling of twoway's region parser; color() sets fill and outline, fcolor() the fill, lcolor()/lwidth()/lpattern() the outline in twoway's edit order; none shows what lies beneath; %NN is drawn; style() and lstyle() names resolve through style_bundle; the graph outline is drawn; bgcolor() is the canvas under the graph region, as twoway paints it. Repeated copies merge in Mata as twoway applies them (_dash_rep_region), keeping every margin() copy; unknown, capitalised, short or repeated sub-options and a comma inside a region are refused r(198) in twoway's words (_dash_subreq_check region); lalign(), the i* options, margin(), shadestyle(), intensity() and marginonly are named in one note. Pinned by test/test_region_truth.py::TestAgainstTwoway::test_probe, test/test_region_options.py::TestBothModes::test_bgcolor_is_the_canvas, test/test_region_options.py::TestTheSpec::test_the_edit_order, test/test_region_options.py::TestHostileRegionText::test_inert, test/test_region_options.py::TestAfterAFilterMove::test_regions_survive, test/test_twoway_option_parity.cscript RS-01, test/test_wp30_truth.cscript RS-20; fixture test/fixtures/region_truth.json. Residual, deferred (WP-30): margin() and the plot region's inner box are section 47's; the outer graphregion() on a by() graph and by(, graphregion() plotregion()) stay as they were (closeout P2 row); intensity() and shadestyle() are named, not drawn.
  ```
- **CHANGELOG lines** (each replaces its marker in place; the `###` lines only say which list):

  ```
  ### Results that change
  - plotregion() and graphregion() are drawn as twoway draws them, in both modes: `plotregion(c(red))` drew nothing (abbreviations were not read) and `plotregion(color(red))` filled only, and now both fill and outline in red; `fc()`, `lc()`, `lw()`, `lp()`, `ls()`, `sty()` and the other spellings work; `none` drew black and now draws nothing; `fcolor(red%50)` drew opaque red and now draws it at half opacity; `style(none)`, `lstyle(none)`, `lpattern()` and the graph region's outline were ignored and are drawn; repeated copies combine as twoway combines them (`plotregion(color(red)) plotregion(c(blue))` was red and is blue). `bgcolor()` is now twoway's canvas under the graph region: `bgcolor(red)` alone coloured the graph region red and now changes nothing visible, and `bgcolor(red) graphregion(color(none))` shows red. (WP-30, P1.20a)

  ### Changed behaviour (may need your do-files changed)
  - plotregion() and graphregion() refuse what twoway refuses, r(198) in twoway's words (all rc 0 before, most with no note): an unknown sub-option (`option bogus() not allowed`), a capitalised one (`option COLOR() not allowed`), one shorter than twoway's minimum (`option st() not allowed`), a sub-option given twice in one copy (`option c() not allowed`) and a word after a comma inside the region (`invalid 'lcolor'`). (WP-30, P1.20a)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md B18** (:547-555): `- **Tracked:** Partly closed in WP-30, BUGS.md "<P1.20a title>", commit <sha>: the styling sub-ids b-f; B18-a (margins) is section 47's.` Its "Closable: partly -- Bokeh has no border line around the whole canvas" is stale (E5).
  - **TWOWAY_COVERAGE_AUDIT.md:141** (AUDIT-66): the styling half and the bgcolor half closed by `<sha>`; margins open until S47.
  - **GAPS.md E3** and **ROADMAP.md:1527** ("Not covered, and said so: plotregion(), graphregion()") updated; **DROPIN-REMAINING.md:131**: "Styling closed by <sha> (WP-30 S38); margins S47."
  - **test/fixtures/rejected_options.json:2669-2693** (`abd_graphregion` "DROPPED ... _extract_region_color") and **test/fixtures/twoway_corpus.do:294-296, :559** describe the deleted reader; refresh them.
  - **New P2 rows:** (a) region `intensity()`/`shadestyle()` named, not drawn (Q-38.1, resolved); (b) by()'s outer regions (IR-9, measured in B01).
  - **AGENTS.md invariant:** "region colours and widths are resolved only by `_dash_region_spec`/`_dash_apply_regions`, which emit `#rrggbb`, `None` and numbers; `bgcolor()` is the canvas under the graph region."
  - **Unverified:** the region grammar on Stata 14-18.5 (not run, M2).
