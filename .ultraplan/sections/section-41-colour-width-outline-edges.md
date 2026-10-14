# Section 41: Colour, width and outline edges

> Part of: WP-31 · GAPS3 rows: E4, E5, E7, E8, E13 · Risk: green · Batch: 14 · Depends on: 01 · Blocks: -- · Tasks: 4, 5 commits · Case-id prefix: U41

## Overview

**What is wrong today.** GAPS3 E4 (GAPS3.md:183): "Stylelist edges: glued `=` forms (`red=blue`, `red=`) and `(red)` reach the renderer as one unknown element (twoway r(198) for `(red)`); an unknown `msymbol()` element draws the p# symbol (twoway: circle, unverified)." E5 (:184): "Colours: a comma colour inside a structured sub-option (`title(, color("1,2,3"))`, region, `xline(, lcolor())`, `ylabel(, labcolor())`) noted and drawn black where twoway refuses r(198); `navy*52` clamp and `color foreground bg` cycle UNCLEAR; `mcolor("red",blue)` unverified." E7 (:186): "pstyle(p#) CI band under a scheme intensity above full is clamped to full (`_intensity` default clamp=True); histogram passes clamp=False." E8 (:187): "rarea and rbar outlines: twoway strokes them (rarea `#1A476F` 17.28 under s2color); dash draws none unless colour options are given." E13 (:192, NEW): "Shipped scheme keys the renderer never references (`color plabel`, `color pline`, `color plineplot`, `linewidth p#solid`, `linewidth parea`); `_SIZE_MAP` kept and serialised into the served app though nothing reads it; `_GSIZE_NUMERIC_PT_PER_UNIT` duplicates `PT_PER_RS`; scheme `%NN` opacity on histogram unverified though the help promises every layer." The task's `*#` question from the index: whether `lwidth(*2)` multiplies before or after the 0.3 pt SVG floor (`line_px`, dash_render.py:7174-7187).

At `6370ca4`: `_dash_stylelist_elems` (dash_parse.mata:5303-5361) splits only the trailing `...`/`..` repeats ("`red=blue` and `(red)` stay one element each, as twoway reads them", :5298-5299 -- the comment asserts what E4 says is unverified); dash.ado's `colour` kind (:3234-3262) refuses a comma-written colour in a plot option only; `p_other_band_styles` reads `self._intensity(_ik, self.fill_alpha)` with the default `clamp=True` (:10746-10750) where the histogram passes `clamp=False` (:10732); `map_rarea` draws one `fig.varea` (:18494-18513) with no stroke (VArea has no line properties) and `map_rbar` sets `line_width` from `plot_line_width(color_idx, "bar")` but its colour only when `color()`/`blcolor()` is given (:18588-18600); `_SIZE_MAP` (:6992-7007) is dead and emitted into the served header (:48082-48084); `_GSIZE_NUMERIC_PT_PER_UNIT = 2.88` (:8899) is used once (:9755) beside `PT_PER_RS = 2.88` (:7015).

**After this section**, both modes: stylelist elements `red=blue`, `red=` and `(red)` are read or refused exactly as twoway does (measured U41-02..04); a comma-written colour inside `title()`, `subtitle()`, `note()`, `caption()`, `xline()`, `yline()`, `xlabel()`, `ylabel()`, `plotregion()`, `graphregion()` and `legend()` is refused with twoway's rc and words where twoway refuses it, else read as RGB; `*#` on a width follows the measured floor order; pstyle(p#) CI bands keep an intensity above full; rarea and rbar carry the outline the scheme's `linestyle p#area`/`p#bar` chain gives (`color p#arealine` -> `color p#`, `linewidth p#area` -> `linewidth p medium`, `linepattern p#area` -> solid) in both modes; `_SIZE_MAP` and `_GSIZE_NUMERIC_PT_PER_UNIT` are gone; a histogram under a scheme whose `color histogram` carries `%NN` draws at that opacity, pinned by a test.

**Why these rows share a section.** Five small edges of the colour/width/outline readers (`stata_colour`, `line_px`, `_intensity`, the two range mappers, the stylelist tokeniser) that no other batch-14 section touches (S42 owns the graph-text parser, S43 the loader and format writers).

**Test order and commit rule.** Five cycles, one commit per row in the order E13 (hygiene first, so the dead constants are gone before anything is measured against the served header), E7, E8, E4, E5. 41-01 writes the extractor, the five per-row regression test files (DECISIONS A14: one file per row -- test/test_dead_constants.py (E13), test/test_band_intensity.py (E7), test/test_range_outlines.py (E8), test/test_stylelist_edges.py (E4), test/test_subopt_colours.py (E5)) and ONLY the E13 truth block, and never commits; 41-02 commits E13 and E7; 41-03 commits E8; 41-04 commits E4 and E5 and hands back. Each row's failing tests are run against the tree the previous commit leaves; each row's closing step appends its own truth block (A14) and stages only its own test file, so no commit stages a later row's red cases. Every GAPS3 Tracked line a closing step writes reads `commit pending` (DECISIONS A11; the merger's step k.3b fills the sha; no amend).

### Section decisions (binding on the executor)

- **D-41a. E4 is measured before it is coded.** U41-02..U41-04 run `scatter mpg weight turn, mcolor(red=blue)`, `mcolor(red=)`, `mcolor((red))`, `msymbol(bogus circle)` under twoway and record rc, the note or error text and (from the SVG) each series' fill. The task branches: a form twoway refuses is refused in dash.ado's `_dash_stylelist_check` with the measured words (new Mata predicate `_dash_stylelist_paren(raw)` for `(`-led elements; `=` handled in `_dash_stylelist_elems` only if twoway splits it); a form twoway draws is read the way the SVG shows. An unknown msymbol element draws what the SVG shows (circle if twoway draws `O`; the p# symbol otherwise), through `default_symbol_traits` or `symbol_traits("O")`.
- **D-41b. Comma colours in structured sub-options follow U41-05.** The probe runs the eleven host options each with `color("1,2,3")` (or `lcolor`, `labcolor` as the host takes); where twoway's rc is 198 the message text is recorded and dash refuses from a new rule check `_dash_subopt_colour_check` (dash.ado, called from `_dash_validate_opts` after the graph rules at :3974-3990) that reads each host's sub-option words through Mata `_dash_subopt_colour_comma(text, hosts)` (over `_dash_rep_toks`, quoted text never read as a command line) and prints the measured words through `_dash_say`; where rc is 0 the renderer reads the comma RGB as `stata_colour` already reads scheme commas (`context="scheme"` branch at :7412-7421 is extended to `context="option"` for those sub-options). `mcolor("red",blue)` is measured and pinned as it draws (the GAPS "unverified").
- **D-41c. `navy*52` and the `color foreground bg` cycle stay UNCLEAR, pinned nowhere** (GAPS3 says UNCLEAR; stata_colour's docstring already records twoway `#010304`); U41-06 records them in the fixture for the record, and the help's colour paragraph names the difference with the measured example (M17). No code change for them.
- **D-41d. The width floor order is measured.** U41-07: `lwidth(vvthin)` alone and with `lwidth(*2)`, `lwidth(*10)`, `lwidth(*0.5)` on `lwidth(medium)`; `stroke-width` read from the SVG. If twoway multiplies the unfloored width (vvthin*10 = 0.288 pt -> floored 0.3), `translate_lwidth` (:7602-7630) is already right (it multiplies `default_pt` then floors); if twoway multiplies the floored width (0.3*10 = 3 pt), `translate_lwidth` applies `max(default_pt, _LWIDTH_FLOOR_PT)` before `resolve_size`'s `*#` branch. Branch recorded in the docstring.
- **D-41e. E7 is one keyword.** :10746 reads `self._intensity(_ik, self.fill_alpha, clamp=False)`; the band's alpha path then blends at that intensity as the histogram does (`_blend_intensity` divides above 1).
- **D-41f. rarea's outline is two Line renderers on the layer's own source** (`y1var` and `y2var` against `xvar`), tagged `dash_rarea_outline`, styled from `self.scheme.p_other_band_styles[color_idx % 15]` (DECISIONS A34; the list `style_bundle("area", name)` copies from, dash_render.py:10744-10760 and :11021ff), whose outline keys are `line` (a colour string), `line_alpha`, `line_width` and `line_dash` from the `p#other`/`p#otherline` chain -- under s2color the chain ends at `color p#` and `linewidth p medium`, the same values Stata's `linestyle-p#area.style` chain (`color p#arealine -> p#`, `width p#area -> p`) gives, so the measured result is the same; the executor confirms the keys at the batch-14 base with `python3 -c "import dash_render as d; print(sorted(d.SchemeParser.fallback().p_other_band_styles[0]))"` before pasting TR-41.B. The outlines are returned after the VArea so hover and legend read the fill first. twoway's closing edges at the two x ends are not drawn (VArea has no stroke; a `patch` would break the saved copy loop) and the help documents that with the measured SVG (M17). rbar: `line_color` and `line_width` from the same `p_other_band_styles` entry for the bar's outline (measured: the probe records the rbar outline colour; if `ol.rbar` shows the fill colour, the fill is used instead of `line`).
- **D-41g. E13's three deletions and one test.** `_SIZE_MAP` and the emitted lines go; `_GSIZE_NUMERIC_PT_PER_UNIT`'s one use becomes `OptionTranslator.PT_PER_RS`; the five never-read scheme keys are left in the shipped files (they are Stata's own keys; reading them is S44's resolver) and listed in the help's scheme paragraph as "declared, read by no drawing"; `test_histogram_scheme_opacity` pins `%NN` on `color histogram`.

## Risk: [green] -- small readers, each behind a measured branch; one served-header deletion

**Why.** The edits are local; the largest is two new Line renderers on rarea (hover and legend tests may count renderers).

**Risk factors.** 1. Tests counting rarea renderers (`len(r) == 1`) or asserting rbar `line_color is None`. 2. The served header deletion (`_generate_app_source` :48082-48084) makes S41 batch 14's one `_generate_app_source` editor (R12: S42 and S43 must not edit it; S43's writer and loader changes are module functions copied by name). 3. A refusal added to dash.ado must not read quoted text as a command (rule 1). 4. The `=` split, if twoway splits, changes `_dash_stylelist_pick`'s `=` handling (:5398-5404 already treats a bare `=` as "repeat the previous"), so only the tokeniser changes.

**Mitigation.** 1. 41-01 lists the red nodes from a simulated fix. 2. Index owner table; S41 names the three deleted lines only. 3. `_dash_subopt_colour_comma` is built over `_dash_rep_toks`/`_dash_rep_optname` like `_dash_logit_typed` (dash_parse.mata:6496ff; REVIEW-3d F16); U41-10 pins quoted and nested text. 4. Branch on U41-02.

## Dependencies

- **Depends on: 01.** Blocks none.
- **Parallel batch: 14**, merge order S41, S42, S43. **Can run with S42 and S43**: S42 edits the graph-text functions (:33876-34490) and S43 the loader (:2395-2500), `_carry_cols` (:12387), the format writers (:26925-28020) and dash.ado's data writer; none touches `OptionTranslator`, `SchemeParser`, `map_rarea`, `map_rbar`, the stylelist Mata or `_dash_validate_opts`.

## Evidence

### E4 -- the tokeniser

dash_parse.mata:5293-5299 (comment) and :5303-5361 (`_dash_stylelist_elems`): tokens from `_dash_rep_toks(raw, 0)`; only a trailing `...`/`..` is cut; one enclosing quote pair is removed. `_dash_stylelist_pick` (:5389-5407): a bare `=` repeats the element before it, `.` is the default. `_dash_stylelist_bad` (:5413-5422) refuses a misplaced repeat with "invalid syntax" r(198) (measured 03oct2026). `_dash_stylelist_check` (dash.ado, called at :5585) is the refusal site. The unknown-msymbol element path: `_apply_marker_opts` :13347-13353 notes and leaves the glyph's marker, which the scheme cycle set (`default_symbol_traits(i)` :10916), i.e. the p# symbol.

### E5 -- the colour grammar

`stata_colour` (:7441-7513): `context="scheme"` splits on commas (:7412-7421 in `_colour_base`); `context="option"` passes a comma colour to `_colour_base` which returns `"unknown"` -> black with the caller's note. dash.ado :3234-3262 (`colour` kind): refuses `mcolor("255,0,128")` with `invalid '<word>'` r(198), plot options only. Structured options (title/subtitle/note/caption/xline/yline/xlabel/ylabel/plotregion/graphregion/legend) are read in the renderer (`_dash_textbox`, `_dash_region_spec` :6494-6610, `_dash_apply_scale_look` :30820-30861, the refline look); their colours reach `parse_color_alpha`/`stata_colour` with `context="option"`.

### E7 -- the band intensity

```python
10746            "intensity": (self._intensity(_ik, self.fill_alpha) if _ik
10747                          else self.fill_alpha),
```
against the histogram at :10732 `self._intensity("intensity histogram", 1.0, clamp=False)`. `_intensity` (:9767-9784): "With *clamp* the value is held to [0, 1]; without it a value above full is kept (`inten200` is 2.0, as twoway draws the p#bar and p#area chains, WP-30 P1.2b)".

### E8 -- the outlines

`map_rarea` :18494-18513: `fig.varea(..., fill_color=..., fill_alpha=...)`, `_style_restyle(r, options, ("area",))`, `_apply_fill_opts`; returns `[r]`. `map_rbar` :18580-18600: `_rbar_lw = self.scheme.plot_line_width(color_idx, "bar")` sets `line_width`; the outline colour is set only inside the `color`/`blcolor` branches. Stata: `style/areastyle-p#area.style` -> `linestyle scheme p#area`, `style/linestyle-p#area.style` -> `width scheme p#area`, `color scheme p#arealine`, `pattern scheme p#area`; s2color declares no `linewidth p#area`/`color p#arealine`, so the chain ends at `linewidth p medium` and `color p#` (research/stata-ground-truth.md §11: "`areastyle p#area/p#bar` and `linestyle p#area/p#bar` (via style files: width p#area -> p, colour p#arealine -> p#)"). GAPS3's measured rarea stroke: `#1A476F` (navy = `color p1`) at SVG stroke-width 17.28 (twoway's SVG unit: 17.28 = 0.3 rs x 2.88 pt x 20? recorded as given; U41-08 re-measures it beside `line` at `lwidth(medium)` to express it in the same unit).

### E13 -- the dead constants

```python
6992    _SIZE_MAP: dict[str, int] = {
...
7009    # No size path reads _SIZE_MAP any more (WP-30 P1.12a): every marker,
7010    # text and gap size goes through resolve_size below.  It stays defined
7011    # because the served app's header still emits it as a global no app
7012    # code reads (research N3); removing it needs _generate_app_source.
48082            "# Stata msize() keyword -> pixels, the same map OptionTranslator",
48083            "# uses, so one keyword means one size in both modes.",
48084            "_SIZE_MAP = %r" % (dict(OptionTranslator._SIZE_MAP),),
8899    _GSIZE_NUMERIC_PT_PER_UNIT: float = 2.88
9755        pt = round(val * self._GSIZE_NUMERIC_PT_PER_UNIT, 3)
7015    PT_PER_RS: float = 2.88
```
Histogram opacity: `self.histogram_color, self.histogram_alpha = self._color_alpha("color histogram", "#cac27e")` (:10727-10728) -- the alpha is read; whether `_histogram_quads` (:17905-17912 region) applies `histogram_alpha` to `fill_alpha` is what the test pins.

### Tests that pin today's behaviour

- test/test_colour_grammar.py::TestStataTruth (if any node asserts a sub-option comma colour draws black) and ::TestBothModes.
- test/test_scheme_consumption.py nodes asserting rarea returns one renderer or rbar `line_color` None (grep `map_rarea`, `rbar` in test/test_glyphs.py, test/test_range_plots*.py, test/test_hover*.py renderer counts).
- test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName (no change: `_SIZE_MAP` is not in the copy list; the header emits it directly).
- test/test_size_units.py: the only test naming `_SIZE_MAP` at 6370ca4 (`grep -rn "_SIZE_MAP" test/`; REVIEW-3d F18) -- its node flips to "absent".
- test/test_varlist_expansion.cscript SL-02 pins `_dash_stylelist_elems` on `red=blue` as one element (program_coverage_map.py:705): flipped if twoway splits.

## User stories

- US-41.1 As a Stata user, I want `mcolor((red))` and the other stylelist edge forms to do what twoway does, so a typo is refused where twoway refuses it.
- US-41.2 As a Stata user, I want `title("x", color("1,2,3"))` to be refused (or drawn) exactly as twoway does, never drawn black with a note.
- US-41.3 As a Stata user, I want rarea and rbar outlined as twoway outlines them under my scheme, and a CI band's declared intensity above full kept.
- US-41.4 As a maintainer, I want no dead constant serialised into the served app and the histogram opacity promise pinned.

## Business requirements

- BR-41.1 Each measured stylelist edge form behaves as twoway's rc/drawing says (E4).
- BR-41.2 A comma colour inside each of the eleven structured options is refused with twoway's words or read as RGB, per the measurement; a refusal is a CHANGELOG Changed-behaviour line (M5).
- BR-41.3 CI bands under `pstyle(p#)` keep an intensity above full (E7).
- BR-41.4 rarea and rbar carry the scheme's area outline in both modes, before and after a move; user `lcolor()`/`alcolor()`/`color()` still win (E8).
- BR-41.5 The served source holds no `_SIZE_MAP`; one constant for 2.88 pt per unit; a histogram draws the scheme's `%NN` opacity (E13).
- BR-41.6 `lwidth(*#)` follows the measured floor order.

## Technical requirements

- TR-41.1 (E13) Delete dash_render.py:6992-7013 (`_SIZE_MAP` and its comment) and :48082-48085 (the three emitted lines and the blank); replace :9755 with `pt = round(val * OptionTranslator.PT_PER_RS, 3)` and delete :8895-8899 (the comment and constant), moving the comment's substance ("a bare gsize number is a relative size, 2.88 pt per unit at the 4-inch reference") to `PT_PER_RS`'s comment at :7013-7015.
- TR-41.2 (E13) `test/test_scheme_consumption.py::TestHistogramSchemeOpacity::test_percent_on_color_histogram[mode]`: a scheme file in tmp with `#include s2color` and `color histogram "202 194 126%40"` draws the Quad with `fill_alpha == 0.4` in both modes. `_histogram_quads` already applies `fill_alpha=scheme.histogram_alpha` (:17895-17896), so this test is a GUARD (REVIEW-3d F17), expected green at base; only if it is red does `_histogram_quads` gain `fill_alpha=self.scheme.histogram_alpha` where it sets `fill_color`. E13's Results line therefore names only the deletions (TR-41.C).
- TR-41.3 (E7) :10746: `self._intensity(_ik, self.fill_alpha, clamp=False)`.
- TR-41.4 (E8) `map_rarea`: after `_apply_fill_opts`, read `_b = self.scheme.p_other_band_styles[color_idx % 15]` (DECISIONS A34; a flat dict with the outline keys `line` (colour string), `line_alpha`, `line_width`, `line_dash`); two renderers `fig.line(x=xvar, y=y1var, source=source, line_color=_b["line"], line_alpha=_b.get("line_alpha", 1.0), line_width=_b["line_width"], line_dash=list(_b.get("line_dash") or []), tags=["dash_rarea_outline"])` and the same for `y2var`, with `view=view` when given; apply `self._apply_line_opts(outline, options, role="aline")` to each so `alcolor()`/`alwidth()`/`alpattern()`/`color()` win; return `[r, top, bottom]`. `map_rbar`: before `fig.vbar`, set `_rbar_kwargs["line_color"] = _b["line"]` (the same entry; or the fill when `ol.rbar` says so) when no `color`/`blcolor` option names one; keep `_rbar_lw`.
- TR-41.5 (E4) dash_parse.mata: per D-41a either (i) `_dash_stylelist_elems` cuts a bare element at each `=` into `stem`, `=`, `rest` (so `red=blue` is `red`, `=`, `blue` and `red=` is `red`, `=`), or (ii) nothing. New `real scalar _dash_stylelist_paren(string scalar raw)`: 1 when a bare element starts with `(`. dash.ado `_dash_stylelist_check`: when `_dash_stylelist_paren` is 1, `_dash_say("err", <measured text>)`, `exit 198`. Header index, `_needed` (alphabetical after `_dash_stylelist_norm`), program_coverage_map.py entry `"test_option_validation.cscript:U41-02"`.
- TR-41.6 (E5) dash_parse.mata `string scalar _dash_subopt_colour_comma(string scalar text, string scalar hosts)`: for each top-level token of `text` (`_dash_rep_toks(text, 0)`) whose `_dash_rep_optname` is in `hosts` (space-separated), read its parenthesised value's own tokens; for each whose name is one of `color lcolor labcolor fcolor mcolor mlcolor bcolor lpattern`-- no: the colour names only, `color lcolor labcolor fcolor bcolor ilcolor`, whose value (one enclosing quote pair stripped) holds a comma and no other `"`, return `<host>(<name>)`; else `""`. dash.ado: in `_dash_validate_opts` after the graph rules loop (:3974-3990, which reads each option as `st_global("s(g_" + o + ")")`; `opts_raw` exists only in the segment parser, :4921 and :5486, and is NOT available here -- REVIEW-3d F15, DECISIONS A34), loop over the refused hosts: `foreach _h in <hosts whose fixture rc is 198> { mata: st_local("_sc", _dash_subopt_colour_comma(st_global("s(g_" + "`_h'" + ")"), "`_h'")) ; if `"`_sc'"' != "" { ... exit 198 } }` -- the Mata function takes `(value, host)`: the one host's option VALUE (not the whole option text) and the host name, and returns `<host>(<name>)` or `""`; if non-empty print the measured text (with the host name substituted as twoway's message does) and `exit 198`. Only the hosts whose fixture rc is 198 are listed. For hosts with rc 0, `_colour_base` (:7412) takes the comma branch when `context in ("scheme", "subopt")` and the three renderer readers (`_dash_region_spec` :6494, `_dash_apply_scale_look` :30852, the textbox colour reader) pass `context="subopt"`.
- TR-41.7 (E5, width) `translate_lwidth` per D-41d; docstring cites `test/fixtures/colour_width_edges_truth.json` key `lw.*`.
- TR-41.8 Both renderers: every change is a class member or a dash.ado/Mata edit; the one module function touched, `_dash_region_spec`, is already in the functions tuple (:46822-47270); no new copy-list entry. function_test_map.py: no new Python function (if `_dash_region_spec` gains a helper, add it). program_coverage_map.py: the two Mata functions.
- TR-41.9 Help (R3): dash.sthlp :1049-1056 (the "Colours (but for a comma)" paragraph: state the sub-option rule as measured), the rarea/rbar paragraphs (grep `rarea` in the plot-type section; add "outlined in the scheme's area line style; the end edges twoway closes are not drawn"), the scheme paragraph naming the five unread keys, the CI band paragraph (`pstyle(p#)` intensity above full kept). CHANGELOG: Changed behaviour line(s) for each form newly refused; Results lines for E7/E8.


### Reference TR-41.A: the eleven structured hosts and the colour sub-option each takes (U41-05's probe list)

| host | sub-option probed | where the renderer reads it today |
|---|---|---|
| title(), subtitle(), note(), caption() | `color("1,2,3")` | `_dash_textbox` colour reader (S30) |
| xline(), yline() | `lcolor("1,2,3")` | `_dash_refline_draw` look (:38870 region) |
| xlabel(), ylabel() | `labcolor("1,2,3")` | `_dash_apply_scale_look` (:30820-30861) |
| plotregion(), graphregion() | `color("1,2,3")` and `lcolor("1,2,3")` | `_dash_region_spec` (:6494-6610) |
| legend() | `color("1,2,3")` | legend textbox reader |

Mata sketch for TR-41.6 (goes after `_dash_logit_typed`'s closing brace, dash_parse.mata:6496ff -- REVIEW-3d F16; header index line `//   _dash_subopt_colour_comma(value, host) -- "<host>(<name>)" of the first comma-written colour inside one structured option's value, "" if none`):

```
string scalar _dash_subopt_colour_comma(string scalar value, string scalar host)
{
    string rowvector inner
    string scalar    val, sub
    real scalar      j, p

    // value is one host option's recorded value, s(g_<host>) (A34);
    // the copies are already merged ", " by the Stata side.
    inner = _dash_rep_toks(value, 0)
    for (j = 1; j <= cols(inner); j++) {
        sub = _dash_rep_optname(inner[j])
        if (!anyof(("color", "lcolor", "labcolor", "fcolor", "bcolor", "ilcolor"), sub)) continue
        p   = strpos(inner[j], "(")
        if (!p) continue
        val = strtrim(substr(inner[j], p + 1, strlen(inner[j]) - p - 1))
        if (strlen(val) >= 2 & substr(val, 1, 1) == char(34) & substr(val, -1, 1) == char(34)) val = substr(val, 2, strlen(val) - 2)
        if (strpos(val, ",") & !strpos(val, char(34))) return(host + "(" + sub + ")")
    }
    return("")
}
```
Quoted text never becomes a command: the value is compared, not evaluated; the message is printed with `_dash_say("err", <measured words with the host>)`.

### Reference TR-41.B: map_rarea's outline (TR-41.4), to be pasted after `self._apply_fill_opts(r, options, base=_fill_base, intensity=_f)` (:18510)

```python
        # twoway strokes the rarea polygon in linestyle p#area (colour
        # p#arealine -> p#, width p#area -> p medium, pattern solid; WP-31
        # E8, test/fixtures/colour_width_edges_truth.json ol.rarea).  The
        # scheme's p#other/p#otherline chain ends at the same values and is
        # what style_bundle("area", ...) copies (A34).  VArea has no stroke,
        # so the two bounds are Lines on the same source; the closing edges
        # at the x ends are documented, not drawn.
        _b = self.scheme.p_other_band_styles[color_idx % 15]
        _outlines = []
        for _yb in (y1var, y2var):
            _kw = dict(x=xvar, y=_yb, source=source, line_color=_b["line"],
                       line_alpha=_b.get("line_alpha", 1.0),
                       line_width=_b["line_width"],
                       line_dash=list(_b.get("line_dash") or []),
                       tags=["dash_rarea_outline"])
            if view is not None:
                _kw["view"] = view
            _o = fig.line(**_kw)
            self._apply_line_opts(_o, options, role="aline")
            _outlines.append(_o)
        return [r] + _outlines
```
`p_other_band_styles` is the list `style_bundle("area", name)` returns `dict(self.p_other_band_styles[i])` from (:11021ff); its keys at 6370ca4 are `line`, `line_alpha`, `line_width`, `line_dash` beside the fill keys (A34). If the batch-14 base has renamed them, read the list's builder at :10744-10760 and take the four outline keys as named there.

### Verbatim entries TR-41.C

- CHANGELOG Changed-behaviour line form (one per refused form): `- <host>(..., color("1,2,3")) was drawn black with a note; it is refused, as twoway refuses it: "<measured words>" r(198) (WP-31, E5)`; `- mcolor((red)) reached the renderer as an unknown colour; it is refused, as twoway refuses it: "<measured words>" r(198) (WP-31, E4)`.
- CHANGELOG Results lines: `- lfitci ..., pstyle(p1) under a scheme declaring intensity p1bar inten200 drew the band at full; it is drawn at twice full, blended as twoway blends it (WP-31, E7)`; `- rarea and rbar drew no outline; they are outlined in the scheme's area line style (WP-31, E8)`. E13's line goes under `### Fixed in WP-31` and names only the deletions (REVIEW-3d F17): `- The served app's header no longer carries the unread _SIZE_MAP; one constant (PT_PER_RS) gives points per unit; the histogram's scheme opacity is pinned by a test (WP-31, E13)`.
- test/program_coverage_map.py `"dash_parse.mata"` block: `"_dash_stylelist_paren": ("test_option_validation.cscript:U41-11",),` and `"_dash_subopt_colour_comma": ("test_option_validation.cscript:U41-12", "test_wp31_truth.cscript:U41-10"),` (ids as written in 41-04).
- dash.sthlp :1051 sentence becomes: `Colours (but for a comma, inside a plot option or inside title(), subtitle(), note(), caption(), xline(), yline(), xlabel(), ylabel(), plotregion(), graphregion() and legend(), where twoway refuses it and so does dash), msymbol(), lpattern() and ...` -- edited to the fixture's actual host list.
- Help scheme paragraph addition: `The shipped schemes declare color plabel, color pline, color plineplot, linewidth p#solid and linewidth parea, which Stata's own files declare too; no drawing reads them.`

## Boundaries

- No change to `_blend_intensity`, `_LWIDTH_RS`, `resolve_size` beyond D-41d's one ordering; no scheme CMYK/HSV (M7); no `*.style` reading (S44); no graph-text (S42); no loader (S43).
- `_generate_app_source`: the three-line deletion only.
- `navy*52` and `color foreground bg` stay UNCLEAR (D-41c).

## Stata truth

Script `scripts/extract_colour_width_edges_truth.do` -> `test/fixtures/colour_width_edges_truth.json` (R7 form; run through the slot; `git add -f`; named by test_colour_width_edges.py).

| Key | Command (sysuse auto, s2color) | Recorded |
|---|---|---|
| `sl.eq_glued` | `scatter mpg weight turn, mcolor(red=blue)` | rc, log text, series fills from SVG |
| `sl.eq_trail` | `..., mcolor(red=)` | same |
| `sl.paren` | `..., mcolor((red))` | rc, error text |
| `sl.msym_unknown` | `..., msymbol(bogus circle)` | rc, note text, first series' marker shape |
| `sl.quoted_comma` | `scatter mpg weight, mcolor("red",blue)` | rc, text, fill |
| `sc.<host>.<subopt>` for the 11 hosts (13 records: plotregion and graphregion probe both `color` and `lcolor`; REVIEW-3d F19) | `scatter mpg weight, <host>(..., color("1,2,3"))` (xline: `xline(3000, lcolor("1,2,3"))`; ylabel: `ylabel(, labcolor("1,2,3"))`; plotregion/graphregion: `(color("1,2,3"))` and `(lcolor("1,2,3"))`; legend: `legend(color("1,2,3"))`) | rc, error/note text, the element's colour in the SVG when rc 0 |
| `lw.vvthin`, `lw.vvthin_x10`, `lw.medium_x2`, `lw.medium_x0_5` | `line mpg weight, lwidth(vvthin)`, `lwidth(vvthin*10)`? no: `lwidth(*10)` under a scheme whose `linewidth p` is vvthin (scheme file in work dir); `lwidth(*2)`, `lwidth(*.5)` | `stroke-width` |
| `ol.rarea`, `ol.rbar` | `rarea mpg trunk weight, sort` and `rbar mpg trunk weight` + export | the polygon/rect `stroke`, `stroke-width`, `stroke-dasharray`; beside `ol.line_medium`: `line mpg weight, lwidth(medium)`'s stroke-width |
| `ci.inten200` | scheme file `#include s2color` + `intensity p1bar inten200`; `lfitci mpg weight, pstyle(p1)` | the band's fill colour |
| `hist.pct` | scheme `color histogram "202 194 126%40"`; `histogram mpg` (twoway histogram) | the bars' `fill-opacity` |
| `unclear.navy52`, `unclear.fgbg` | `scatter ..., mcolor(navy*52)`; `mcolor(bg fg)` | fills (record only) |

Truth blocks (R1; DECISIONS A14: one block per row, each appended by the row's closing step; 41-01 appends only the E13 block; helpers `_u41_*` above the first block; each block ends `* ==== end S41 <row> ====`): `* ==== S41 E13: Dead constants and histogram opacity ====` (U41-01 fixture stamped; U41-09 histogram `%40` opacity both modes); `* ==== S41 E7: CI band intensity ====` (U41-08 CI band under `intensity p1bar inten200` keeps the blend, both modes); `* ==== S41 E8: rarea and rbar outlines ====` (U41-06 rarea and rbar outline colour/width in both modes equal the fixture -- python helper reading the `dash_rarea_outline` renderers and the VBar's `line_color`/`line_width`); `* ==== S41 E4: Stylelist edges ====` (U41-02..04 the three stylelist forms: dash's rc and text equal twoway's in the same session, `capture noisily twoway` beside `capture noisily dash`, `cert_log_has`); `* ==== S41 E5: Comma colours and the width floor ====` (U41-05 each of the 13 `sc.*` records: dash's rc equals twoway's; U41-07 `lwidth(*10)` width per fixture; U41-10 `_dash_subopt_colour_comma` reads nothing inside quotes: `title("a,b", color(red))` passes, and a nested `title(, size(x) color("1,2,3"))` is caught). Refusal cases (U41-02..05 where twoway refuses) are also appended to test_option_validation.cscript as U41-11.. in its `_ov_assert` form, by the row's closing step.

## TDD test stubs

### Regression tests, one new file per row (DECISIONS A14; red at 6370ca4 unless guard)

| Row | File | Classes |
|---|---|---|
| E13 | `test/test_dead_constants.py` | `TestTheFixture`, `TestDeadConstants` (plus `TestHistogramSchemeOpacity` appended to test/test_scheme_consumption.py, a guard) |
| E7 | `test/test_band_intensity.py` | `TestBandIntensity` |
| E8 | `test/test_range_outlines.py` | `TestRareaOutline`, `TestRbarOutline` |
| E4 | `test/test_stylelist_edges.py` | `TestStylelistEdges` |
| E5 | `test/test_subopt_colours.py` | `TestSubOptionCommaColours`, `TestWidthMultiplierFloor`, `TestUnclearStaysDocumented` |

Each row's commit stages that row's file only (no commit stages a later row's red cases). The fixture is named by test_dead_constants.py::TestTheFixture (test_fixtures_are_committed.py) and staged in the E13 commit.

- Test: fixture stamped, every key -- `TestTheFixture::test_meta`, `::test_keys` (guard).
- Test: `_dash_stylelist_elems`'s behaviour per fixture through dash.ado's spec (the Mata is reached by the cscript; here the spec's `mcolor` JSON for `red=blue`) -- `TestStylelistEdges::test_glued_equals_matches_twoway`, `::test_paren_is_refused_or_drawn` (red by branch).
- Test: an unknown msymbol element draws the fixture's shape -- `::test_unknown_symbol_element[mode]` (red if twoway draws circle).
- Test: each host with a comma colour: the renderer refuses nothing (dash.ado does) and, where twoway draws, draws the RGB -- `TestSubOptionCommaColours::test_each_host[mode-host]` (red: black + note).
- Test: `translate_lwidth("*10", default_px=vvthin_px)` equals the fixture's stroke-width x PX_PER_PT -- `TestWidthMultiplierFloor::test_order` (red or guard by branch).
- Test: `p_other_band_styles[0]["intensity"] == 2.0` under `intensity p1bar inten200` -- `TestBandIntensity::test_above_full_kept` (red: 1.0); the drawn band fill equals the fixture -- `::test_fill_matches_twoway[mode]` (red).
- Test: `map_rarea` returns three renderers, two Lines tagged `dash_rarea_outline` with the scheme's p# colour and medium width; `alcolor(red)` recolours them; a saved and a served move keep them -- `TestRareaOutline::test_two_outlines[mode]`, `::test_alcolor_wins[mode]`, `::test_after_a_move[mode]` (red: one renderer).
- Test: `map_rbar` VBar `line_color` is the scheme's bar outline colour -- `TestRbarOutline::test_default_outline[mode]` (red: None).
- Test: `OptionTranslator` has no `_SIZE_MAP`; the generated app source holds no `_SIZE_MAP`; `SchemeParser` has no `_GSIZE_NUMERIC_PT_PER_UNIT`; a gsize `50` resolves to 144 pt -- `TestDeadConstants::test_size_map_gone`, `::test_app_header_has_no_size_map`, `::test_one_pt_per_unit_constant` (red).
- Test: histogram `%40` opacity -- `test_scheme_consumption.py::TestHistogramSchemeOpacity::test_percent_on_color_histogram[mode]` (guard: `_histogram_quads` already applies `histogram_alpha`, REVIEW-3d F17).
- Test: `navy*52` and `bg fg` draw today's values (record, guard) -- `TestUnclearStaysDocumented::test_values`.

### Cases in cscripts

test_wp31_truth.cscript U41-01..U41-10 in the five row blocks (red except U41-01, U41-09 (guard) and U41-10's twoway half); test_option_validation.cscript U41-11.. (red) for each refused form.

### Flips

Nodes in `<scratch>/s41/41-flips.txt` (rarea renderer counts, rbar outline None, SL-02 if `=` splits); reason "twoway outlines rarea/rbar from the scheme's area line style (E8)" / "twoway reads the stylelist form as measured (E4)".

### Parity corpus (R8)

`CORPUS`: "rarea default outline", "rbar default outline", "lfitci pstyle(p1) inten200 scheme"; `MOVE_CORPUS`: "rarea, dropdown to Foreign".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Stylelist edges | cscript U41-02..04 + pytest | colour_width_edges_truth.json | yes |
| Sub-option comma colours | cscript U41-05 (+ U41-11..) + pytest | same | yes |
| Width floor order | pytest + U41-07 | same | n/a |
| Band intensity | pytest + U41-08 | same | yes |
| Outlines | pytest + U41-06 + parity | same | yes |
| Dead constants, histogram opacity | pytest + U41-09 | same | yes |

AC-41.1..AC-41.6 one per BR.

## Tasks

**Commit boundary.** 41-01 (tests, no commit); 41-02 commits E13 `Remove the dead size map and duplicate unit constant, pin histogram scheme opacity (WP-31 E13)` then E7 `Keep a CI band's scheme intensity above full under pstyle(p#) (WP-31 E7)`; 41-03 commits E8 `Outline rarea and rbar from the scheme's area line style (WP-31 E8)`; 41-04 commits E4 `Read or refuse stylelist edge forms as twoway does (WP-31 E4)` then E5 `Refuse or read comma colours inside structured options as twoway does (WP-31 E5)` and hands back. Each body: the row's failure text from `<scratch>/41-01-failure.txt`, measured defect, change, `Regression:`/`Flipped:`/`Fixture:`/`BUGS.md:`/`GAPS3:` lines. Every Tracked line a closing step writes is `- **<row> Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (DECISIONS A11; the merger's step k.3b fills the sha; no amend). `$WT=<worktrees>/wp31-s41`.

<task type="auto" id="41-01">
  <name>Measure the five edges and write failing tests</name>
  <files>scripts/extract_colour_width_edges_truth.do, test/fixtures/colour_width_edges_truth.json, test/test_dead_constants.py</files>
  <action><![CDATA[
    Check the worktree (branch wp31-s41 at the batch-14 base). Create the extractor from the "Stata truth" table (head as scripts/extract_date_axes_truth.do; SVGs parsed with xml.etree; `_meta` five keys), run through the slot, `git add -f` the fixture. Create the five per-row test files of "TDD test stubs" (test/test_dead_constants.py, test/test_band_intensity.py, test/test_range_outlines.py, test/test_stylelist_edges.py, test/test_subopt_colours.py) with exactly their classes, every expectation from the fixture; add `TestHistogramSchemeOpacity` to test/test_scheme_consumption.py (a guard). Run the six files `-q -n0 -p no:cacheprovider -rf > <scratch>/s41/41-01.log`, write `<scratch>/41-01-failure.txt` grouped by row (E13, E7, E8, E4, E5). Append the `_u41_*` helpers and ONLY the E13 block (`* ==== S41 E13: Dead constants and histogram opacity ====`, U41-01, U41-09) to test/test_wp31_truth.cscript above the marker (A14: the E7, E8, E4 and E5 blocks are appended by 41-02, 41-03 and 41-04) and run it (`WP31_ONLY=S41`), append FAIL lines. On a scratch copy carrying TR-41.1..TR-41.7 run test_glyphs.py, test_scheme_consumption.py, test_colour_grammar.py, test_hover*.py, test_range*.py, test_size_units.py and write `<scratch>/s41/41-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/colour_width_edges_truth.json'));print(sorted(d['_meta']), sum(k.startswith('sc.') for k in d))"` prints the five keys and at least 11 (13 expected: two sub-options on each region host); `grep -c FAILED <scratch>/s41/41-01.log` is at least 10 (TestHistogramSchemeOpacity is a guard and not counted); `grep -c "U41-0[19]" <scratch>/s41/run_test_wp31_truth.log` is at least 2 and `grep -c "U41-0[2-8]" <scratch>/s41/run_test_wp31_truth.log` prints 0 (only the E13 block exists yet); `test -s <scratch>/41-01-failure.txt`.]]></verify>
  <done>twoway's rc, words and drawing for every edge were recorded and every regression test and truth case was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="41-02">
  <name>Delete dead constants, unclamp the band, commit E13 and E7</name>
  <files>dash_render.py, test/test_scheme_consumption.py, BUGS.md</files>
  <action><![CDATA[
    Apply TR-41.1 and TR-41.2's fix only if its guard is red; run test_dead_constants.py, test_scheme_consumption.py::TestHistogramSchemeOpacity, test_size_units.py (the `_SIZE_MAP` pin, flipped to "absent" -- REVIEW-3d F18), test_server_app*.py, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test_sizes*.py (gsize paths), and U41-01/U41-09; update the help's scheme paragraph (TR-41.9) with the five unread keys; close BUGS.md E13, rewrite GAPS3 `E13 Tracked` to `- **E13 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (A11), replace the E13 marker with TR-41.C's deletions-only line; stage test/test_dead_constants.py, the E13 block and `git add -f test/fixtures/colour_width_edges_truth.json`; commit `(WP-31 E13)`. Then append the E7 block (`* ==== S41 E7: CI band intensity ====`, U41-08) above the marker and re-run test_band_intensity.py and U41-08 red on the E13 tree (append to the failure file); apply TR-41.3; run TestBandIntensity, test_fit_bands*.py, U41-08; help CI-band sentence; close E7, Tracked line (`commit pending`), marker; stage test/test_band_intensity.py and the E7 block; commit `(WP-31 E7)`. Grep both messages for tooling names (0).
  ]]></action>
  <verify><![CDATA[`grep -c "_SIZE_MAP\|_GSIZE_NUMERIC_PT_PER_UNIT" dash_render.py` prints 0; `python3 -m pytest test/test_dead_constants.py test/test_band_intensity.py test/test_size_units.py test/test_scheme_consumption.py -k "HistogramSchemeOpacity or Dead or Band or size" -q -p no:cacheprovider` ends 0 failed; `grep -c "U41-0[189] PASS" <scratch>/s41/run_test_wp31_truth.log` prints 3; `git log --format=%s -2` ends `(WP-31 E7)` then `(WP-31 E13)`; `grep -c "E13 Tracked:\*\* Closed in WP-31.*commit pending\|E7 Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` prints 2.]]></verify>
  <done>The served header no longer carries the dead size map, one constant gives points per unit, histogram scheme opacity is pinned, and CI bands keep an intensity above full; two commits landed.</done>
</task>

<task type="auto" id="41-03">
  <name>Outline rarea and rbar from the scheme, commit E8</name>
  <files>dash_render.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[
    Append the E8 block (`* ==== S41 E8: rarea and rbar outlines ====`, U41-06) above the marker and re-run test_range_outlines.py and U41-06 red on the E7 tree (append to the failure file). Apply TR-41.4 in map_rarea and map_rbar from `p_other_band_styles[color_idx % 15]` (A34; the colour key for rbar's outline from `ol.rbar` in the fixture: if it equals `color p#` use the entry's `line`; if it is the fill colour, use the fill). Flip the E8 nodes of 41-flips.txt in place (renderer counts, `line_color is None`). Append the parity entries. Edit the rarea/rbar help paragraphs (closing edges documented with `ol.rarea`'s measured stroke). Run test_range_outlines.py, the flipped files, test_mode_parity.py -k "rarea or rbar", test_saved_filter_layers.py -k "rarea or rbar", test_hover*.py, and U41-06. Close BUGS.md E8, Tracked line (`commit pending`, A11), marker (a Results line: "rarea/rbar: no outline -> the scheme's area line"); stage test/test_range_outlines.py and the E8 block; commit `(WP-31 E8)`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_range_outlines.py test/test_mode_parity.py -k "rarea or rbar or Outline" -q -p no:cacheprovider` ends 0 failed; `grep -c "U41-06 PASS" <scratch>/s41/run_test_wp31_truth.log` is 1; `git log -1 --format=%s` ends `(WP-31 E8)`; `grep -c "E8 Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` prints 1.]]></verify>
  <done>rarea carries two scheme-styled outline Lines and rbar a scheme-coloured outline in both modes, surviving moves, with the end edges documented; the E8 commit landed.</done>
</task>

<task type="auto" id="41-04">
  <name>Read or refuse stylelist and sub-option colour edges, commit E4 and E5</name>
  <files>dash_parse.mata, dash.ado, test/test_option_validation.cscript</files>
  <action><![CDATA[
    Append the E4 block (`* ==== S41 E4: Stylelist edges ====`, U41-02..04) above the marker and re-run test_stylelist_edges.py and U41-02..04 red on the E8 tree (append to the failure file). Apply TR-41.5 by the fixture's `sl.*` branches (D-41a), add the Mata function(s) to the header index, `_needed` (dash.ado:448-479, alphabetical) and test/program_coverage_map.py; append the E4 refusal cases to test_option_validation.cscript as U41-11.. (`_ov_assert` form, `capture twoway` beside `capture dash`); flip SL-02 in test_varlist_expansion.cscript if `=` splits. Run test_stylelist_edges.py, test_abbreviations.py, test_program_coverage_map.py, the S41 block (U41-02..04) and test_option_validation.cscript through the driver. CHANGELOG Changed-behaviour line(s) for refused forms; close BUGS.md E4, Tracked (`commit pending`, A11), marker; stage test/test_stylelist_edges.py and the E4 block; commit `(WP-31 E4)`. Then append the E5 block (`* ==== S41 E5: Comma colours and the width floor ====`, U41-05, U41-07, U41-10) and re-run test_subopt_colours.py and those cases red on the E4 tree; apply TR-41.6 (the `(value, host)` Mata function over `s(g_<host>)`, A34) and TR-41.7 by `sc.*` and `lw.*` (D-41b, D-41d), same registrations, the E5 refusal cases appended to test_option_validation.cscript, U41-05/07/10 and the pytest classes; help :1049-1056; CHANGELOG lines; close E5, Tracked (`commit pending`), marker; stage test/test_subopt_colours.py and the E5 block; commit `(WP-31 E5)`. Then run the five S41 test files whole, test_colour_grammar.py, test_option_validation.py, test_csp.py and both cscripts once more; write `<scratch>/s41/handback.txt` (five shas, branches taken with measured values, residuals: D-41c's UNCLEAR pair, rarea end edges).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_dead_constants.py test/test_band_intensity.py test/test_range_outlines.py test/test_stylelist_edges.py test/test_subopt_colours.py test/test_colour_grammar.py test/test_option_validation.py test/test_csp.py test/test_program_coverage_map.py -q -p no:cacheprovider` ends 0 failed; `grep -c "U41-\(0[1-9]\|10\) PASS" <scratch>/s41/run_test_wp31_truth.log` prints 10 and `grep -c FAIL` prints 0; `grep -c "ALL CHECKS PASSED" <scratch>/s41/run_test_option_validation.log` prints 1; `git log --format=%s <base>..HEAD | grep -c "(WP-31 E"` prints 5; `grep -c "E\(4\|5\|7\|8\|13\) Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` prints 5; `test -s <scratch>/s41/handback.txt`.]]></verify>
  <done>Stylelist edge forms and comma colours inside structured options behave as twoway's measured rc and words, the width multiplier follows the measured floor order, and S41's five commits were verified green.</done>
</task>

## Section completion criteria

- No `_SIZE_MAP`/`_GSIZE_NUMERIC_PT_PER_UNIT`; histogram opacity pinned; band intensity unclamped; rarea/rbar outlined in both modes and documented; E4/E5 forms match the fixture; width floor order matched.
- Five green commits, each staging its own row's test file and truth block (A14); BUGS.md E4, E5, E7, E8, E13 closed; five Tracked lines reading `commit pending` (A11); markers; CHANGELOG Changed-behaviour lines for every newly refused form; fixture stamped and named.

## Notes

- **Rule 1:** `_dash_subopt_colour_comma` and `_dash_stylelist_paren` read tokens, never run them; the refusal text comes from the fixture through `_dash_say`, the host name through `_dash_display`.
- **The hover tool:** the outline Lines join the layer's renderers list; `_hover_tool` reads the first renderer's fields -- keep the VArea first in the returned list.
- **Copy lists:** none; `_dash_region_spec` is already copied (:46822-47270).
- **R12:** S41 is batch 14's `_generate_app_source` editor (three deleted lines). S42/S43 do not touch it.
- **Shared files:** R1 five row blocks (A14) + area-script cases; R3 the named paragraphs; R4 five markers; R5 five entries, five Tracked lines (`commit pending`); R6 Mata header index and `_needed`; R7 one extractor; R8 appended; R9 flips; R10 none.
- **python_exec hazard** as in S40.
- **For S44:** `p_other_band_styles[i]`'s outline keys `line`, `line_alpha`, `line_width`, `line_dash` are what rarea's and rbar's outlines read (A34); S44's resolver must keep that list's shape.
- **Decisions for maintainer ratification.** D-41b (up to eleven comma-colour forms inside structured options become refusals where twoway refuses them; M5 Changed-behaviour lines), D-41c (`navy*52` and the `color foreground bg` cycle left UNCLEAR by decision, documented), D-41f (rarea's outline as two Lines on the layer's source from the scheme's `p_other_band_styles` entry; the closing end edges documented under M17).

## Addendum (14oct2026, DECISIONS D14): batch 1-4 gaps added to this section

### C4b: fitplot() and ciplot() lines and bands are drawn in the layer's own colour with twoway's colours for those views unmeasured

**Gap.** S11 draws fitplot() (the fit drawn as another type) and ciplot() (the band drawn as another range type) in the layer's p-style colour; twoway's colours for those views were not measured (found by S11).

**Requirement.** Measure, from twoway's SVG, the stroke and fill colours of `lfitci ..., fitplot(scatter)`, `..., ciplot(rline)`, `..., ciplot(rcap)` and `..., ciplot(rarea)` under s2color and stcolor; match them in `_render_ci_band`/`_dash_draw_range_as` in both modes, or document a measured difference.

**Tests.** pytest on the renderer colours (both modes) and a `* ==== S41 C4b: ... ====` truth block reading twoway's SVG with cert_svg.do. Fits S41 because S41 reads colours and outlines from the scheme's band styles in batch 14.

**Process (binding, as for every row).** Task 1 of this row writes the failing tests and saves `<scratch>/41-C4b-failure.txt`; then the fix; then ONE commit with subject ending `(WP-31 C4b)`. The closing task flips the BUGS.md entry "fitplot() and ciplot() lines and bands are drawn in the layer's own colour with twoway's colours for those views unmeasured" to `- [x]` with a Resolution in the BRIEF's closed form ending `Closes GAPS3 C4 (WP-31, C4b).`, deletes the `"C4b":` line from `WP31_OPEN` in test/test_tracking_documents.py, rewrites GAPS3.md's `- **C4b Tracked:**` line to `Closed in WP-31, BUGS.md "fitplot() and ciplot() lines and bands are drawn in the layer's own colour with twoway's colours for those views unmeasured", commit pending.`, and replaces `<!-- WP-31 C4b -->` in place under `### Results that change` with a line ending `(WP-31, C4b)`. Measure twoway first (an extract script or a live probe in the cscript); where the measurement contradicts this addendum, the measurement wins and the deviation is recorded. Refusal/message cases go to the area cscript under the `U41` prefix; drawing comparisons go to a `* ==== S41 C4b: ... ====` block in test/test_wp31_truth.cscript. dash replaces twoway (DECISIONS D13): never use `dash twoway` in a probe.
