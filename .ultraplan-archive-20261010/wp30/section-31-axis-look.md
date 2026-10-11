# Section 31: Axis look sub-options (P1.18 part a, M5/M6)

> Part of: WP-30 · Items: P1.18 part a (entry `P1.18a`) · Risk: yellow · Batch: 11 (merge order S31, S32, S33; S31 first) · Depends on: 08, 10, 13, 15, 30 · Blocks: 43, 52, 53 · Tasks: 13, 1 commit · Case prefix: AXL (AXL-01..AXL-08 in `test/test_suboption_reporting.cscript`; AXL-20..AXL-24 in `test/test_wp30_truth.cscript`)

## Review amendments

- Fixed (major): S30's colour context. TR-31.11 stamped `background_color`/`foreground_color`; it now stamps `OptionTranslator.scheme_colour_context(self)`, as S30's TR for S31, S38 and S39 asks (P1.13.5). The S30 contract line in Dependencies is corrected: `**ctx`, with no `base` keyword.
- Fixed (major): reading the look a second time printed a second, mislabelled `range()` note. `_parse_scale_range` keys its note on the option, so a second `_dash_scale_spec(raw)` call would print `scale(range()) ignores abc`. New `_dash_scale_look` reads the look with no notes and no range parse. TR-31.8/31.9, the copy list (now six functions), the map, tests `test_scale_look` and `test_a_bad_range_is_noted_once`, and the Trap are updated to match.
- Fixed (major): TR-31.14 parsed axis-2 values as `ylabel2(`/`yscale2(`, which `_dash_ax_parse` does not know (`_dash_axfam`, dash_parse.mata:5351). They are now parsed under the axis-1 spelling.
- Fixed (major): `_dash_tick_look` read props through Bokeh's splattable list (`_dash_primary_axes` returns one). It now loops over the members.
- Fixed (major, rule 7): the zlabel() report named `angle(0.785398)` (radians, :26159). With TR-31.1 it would also have dropped the new honoured keys silently. TR-31.7a and 31-05 now name them as typed, and a red-first test is added.
- Fixed (minor): truth block put in TR-01.10's form. Python helpers sit in a `python:` block above the header (`_br_saved` is a Python function, not a Stata program). Any Stata helper declares `version 19`. Pages go only under `` `w30_work' `` and are erased. Cases report through `_w30_expect`/`_w30_done`, and the verify also checks `ALL CHECKS PASSED`.
- Fixed (minor): guard tests added for D-3/BR-31.8 (quoted look words stay text), `xscale2(alt)`, and the by() second-axis subset. A splat-list unit case is added.
- Fixed (minor): 31-13 stops if main moved (E9). The R10 digest is expected unchanged. GAPS2 B23's closure names the sub-options that stay named (new residual R-S31-7). R-S31-5 is tied to S30's D-30f filing.
- Rejected: "angle(Vertical) refused" (manifest scope). IR-5 and register P1.18.3 rule it noted and drawn at 0, as twoway does.
- Rejected: refusing `labcolor("255,0,0")` under M5. S30's D-30f leaves a comma inside a structured option's colour to the closeout. S31 follows that ruling (R-S31-5).
- Rejected: refusing under `nodraw` breaks M5. dash always draws the page, so twoway's draw-time check always applies. This is documented in CHANGELOG.
- Checked: S31's edits (axis parse/apply, `SchemeParser.apply_to_axis`/`apply_to_figure`, `_dash_apply_z_options`, `_dash_plot`, `_dash_axreq_add`, and two new Mata functions) share no function with S32 or S33. The shared test files (`test_mode_parity.py`, `test_help_claims_8.py`/`.cscript`) take distinct cases or profiles. In dash.sthlp, S31's Unsupported sentence (:3757-3760) is not one of S32's paragraphs (:3611-3612, :3647-3655).
- (cross-file pass) 31-13 verify: added the key-deletion check `grep -c '^    "P1.18a": "' $WT/test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:129 (P1.18): "`nolabels`, `noticks`, `xscale(off)`, `noline`, axis line colour, width and pattern, `alt` and `titlegap` are not honoured. `angle(rvertical)`, `angle(stacked)` and other anglestyle names are dropped silently. `labcolor`, `tlength`, `tposition` and `add` are not honoured." GAPS2 B21 (GAPS2.md:579-591) measured "`labs(large)`, `nolabels`, `noticks`, `labcolor(red)`, `glcolor(red)` and `tlength(0)` are ignored"; B23 (:607-621) "`yscale(r(0 100))`, `off`, `noline`, `alt`, `lcolor(red)`, `titlegap(5)` and `rev` are named and ignored"; D9 (:948-958) "`angle(forty_five)`, `angle(rvertical)` and `angle(ninety)` leave labels horizontal with no note, and `angle(Vertical)`, which Stata refuses, is accepted". Re-measured at `c96facd` (Evidence E1, E10): every look sub-option is named and not drawn, in both modes; `angle(rvertical)` and `angle(stacked)` give no angle and no note; `angle(Vertical)` draws 90 degrees and `angle(400)` draws 6.98 radians, both silent; `dash scatter mpg weight, ylabel(, angle(400))` and `yscale(OFF)` return rc 0.

**After this section**, in both modes and before and after any filter move:
- `xlabel()`/`ylabel()` and their second-axis forms draw `nolabels`/`labels` and `noticks`/`ticks` (the positive word wins within one copy), `labcolor()` with `%#` opacity, `tlength()` in Stata's size units and `tposition()` (`outside`, `inside`, `crossing`, each down to one letter).
- `angle()` reads every anglestyle name and twoway's axis abbreviations (`h`, `v`, `rh`, `rv`), case-sensitively. A wrong-case or unknown name gets one note and is drawn at 0, explicitly, so it also overrides a scheme's vertical labels (S15).
- `xtick()`/`ytick()` take their own `noticks`, `tlength()` and `tposition()`; the label options' tick look never reaches the tick-only positions.
- `xscale()`/`yscale()` and `xscale2()`/`yscale2()` draw `off` (line, ticks, labels and title go; the grid stays), `noline`, the axis line's `lcolor()`, `lwidth()` and `lpattern()` (an `lcolor()` re-enables a `noline` line, as twoway does), `alt` and `titlegap()`.
- Under `by()`, `off`, `nolabels`, `noticks` and `titlegap()` are drawn as if absent and are not named, as twoway draws them (M6); `noline`, `alt`, the line style, `labcolor()`, `tlength()`, `tposition()` and `angle()` are drawn on every panel.
- In Stata, `angle()` outside -360..360 on every label and tick family and an `xscale()`/`yscale()` `lwidth()` outside 0..10000 are refused r(198) in twoway's words and order; an `xscale()`/`yscale()` word twoway refuses (`OFF`, `Alt`, `bogus`, a word twice in one copy) is refused r(198) `option OFF not allowed` (M5).

**Decisions applied.** Register P1.18.1 (M6: silent under by()), P1.18.2 (sizes through S08/S13's `resolve_size`), P1.18.3 and IR-5 (`angle(Vertical)` is noted and drawn at 0, never refused; only twoway's refusals are refused), P1.18.4 (M5: bounds and capitalised scale words refused r(198) in twoway's words; `NOLABELS` in the label family is S10's), P1.18.5 (tick-only positions take their own look from the scheme's geometry).

**Why one section.** One parser (`_dash_parse_axis_spec`, `_dash_scale_spec`) and one applier pair (`_dash_apply_axis_spec`, the new `_dash_apply_scale_look`) serve every axis of both modes; one BUGS.md entry, `P1.18a`. The `add` sub-option is S52 (P1.18b).

**Test order and commit rule (rule 7, D1, index "per-entry cycle").** One cycle, one commit:
- **31-01** writes every regression test, runs it on the unmodified worktree and saves `<scratch>/31-P1.18a-failure.txt`; it never commits.
- **31-02** writes the extractor and the fixture, and the fixture-reading guards.
- **31-03 to 31-12** fix, flip, copy-list, Stata side, help.
- **31-13** closes the entry, replaces the two markers, runs the full suite through the queue and makes the one commit, subject ending `(WP-30 P1.18a)`.

No test-only commit exists and no commit is red.

## Risk: [yellow] — additive look sub-options inside three CRITICAL parsers that every axis of every graph passes through

**Why.** `_dash_parse_axis_spec`, `_parse_axis_angle` and `_dash_scale_spec` are CRITICAL; every xlabel, ylabel, xtick, ylabel2 and scale of both modes passes through them, and the served app runs them from copied source. New Stata refusals stop do-files that ran before (PLAN K3).

**Risk factors.**
1. GitNexus, `gitnexus impact <s> -d upstream -r dash` in the main checkout, 03oct2026 at `c96facd`:
   - CRITICAL: `_dash_parse_axis_spec` (8 impacted), `_parse_axis_angle` (7; `-f dash_render.py` disambiguates two candidates), `_dash_scale_spec` (6).
   - HIGH: `_dash_apply_axis_spec` (4), `_dash_apply_tick_option` (4), `_dash_scale_name` (6), `_dash_apply_z_options` (5, `-f dash_render.py`), `ServerAppBuilder._glyph_layer_lines` (copy lists).
   - LOW by the graph, but called from the template string too (grep): `_dash_apply_axis_options` (3), `_dash_finish_secondary_axes` (3), `SchemeParser.apply_to_figure`/`apply_to_axis` (3).
   - UNKNOWN (Stata/Mata, confirmed by grep): `_dash_plot` (dash.ado:5001, one caller :145), Mata `_dash_axreq_add` (callers dash.ado:5213, :5323), `_dash_ax_parse` (:5500, :5574).
2. S10 (batch 4), S13 (5), S15 (5), S18 (6), S21 (7) and S30 (10) have rewritten parts of these functions by this section's base; every anchor below is at `c96facd` and is re-grepped at `batch-11-base`.
3. The M5 refusal of `xscale()`/`yscale()` words twoway refuses also refuses `xscale(bogus)`, which HC1-15 (as S10 left it) and HC2-21l pin as named.
4. Tick geometry is a Bokeh `Int`: a float aborts the render (ValueError).

**Mitigation.**
1. The parser change is confined to the resolved tail names S10 provides (no regex over the whole text); the spec gains keys and loses none. `_parse_axis_angle` keeps its contract (radians or None) and its 7 pins (`test_graph_options.py:1198-1230`) stay green.
2. 31-01 checks each dependency's contract on the base before writing a test, and stops if one is missing.
3. Every refusal has a twoway twin measured live in the same AXL case, and a CHANGELOG "Changed behaviour" line. The pins are flipped in place (Evidence E11).
4. One geometry helper rounds and clamps (`_dash_tick_geometry`), with a unit test.

## Dependencies

- **Depends on: 08, 10, 13, 15, 30** (and S01, S03, S06 from batches 0-2). They provide, by batch 11:
  - S01: the BUGS.md entry `P1.18a` (title "The axis look sub-options nolabels, noticks, off, noline, line colour, width and pattern, alt, titlegap, labcolor, tlength and tposition are not honoured, and anglestyle names are dropped silently"), its `WP30_OPEN` key, the markers `<!-- WP-30 P1.18a -->` in "Results that change" and "Changed behaviour", the stub block `* ==== S31 P1.18a: Axis look sub-options ====`, and the map anchors `# WP-30 S31 (P1.18a): Axis look sub-options (P1.18 part a, M5/M6)` (A148).
  - S03: `version 19` in every program. S06: the note channel; `_dash_style_note` keeps its signature.
  - S08: `OptionTranslator.resolve_size(value, kind, default_pt, ref_in)`, `size_medium_pt`, `PX_PER_PT`, `size_ref_of(fig)`, and `_dash_apply_axis_spec(..., ref_in=4.0)` passed by both callers (S08 TR-08.7).
  - S10: `_DASH_AXLABEL_SUBOPT_TABLE`, `_DASH_AXSCALE_SUBOPT_TABLE`, `_DASH_AXLABEL_HONOURED`, `_dash_subopt_canon`, `_dash_subopt_resolve`; `_dash_parse_axis_spec` reading resolved tail names with `out["typed"]`; Mata `_dash_so_rows`, `_dash_so_resolve`, `_dash_so_isnum`, column 10 of `_dash_axreq`; the repeat merge keyed by full name (last copy wins; `on|off` and `noX`→`X` one key).
  - S13: `OptionTranslator.translate_lwidth(value, default_px=None, ref_in=4.0)` (case-sensitive, ValueError on an unknown name) and the `,u` line-width rule in `_dash_validate_value` (twoway's `gm_linewidth` line, then dash's).
  - S15: `SchemeParser.apply_to_axis(axis, which=None, number=1)` setting tick length (`tick_length_px`), side (`tick_position`), colour and width and the vertical_tick angle; `axis_flags`, `axis_side`; the scheme's `alt_*axes` move in `apply_to_figure`; `_dash_finish_secondary_axes` searching both sides.
  - S30: `OptionTranslator.parse_color_alpha(value, option="", **ctx)`, whose context goes straight to `stata_colour` (`background`, `foreground`, `naturally_white`), and `OptionTranslator.scheme_colour_context(scheme)` (`{}` for None), which S30's TR "S31, S38, S39" names as the one way these sections pass a scheme's colours (register P1.13.5). An unknown colour: twoway's note, black. S31 passes no `base`; S43 adds that later.
- **Blocks: 43, 52, 53.** S43 gives `labcolor()` and the axis `lcolor()` sites bare `*#`/`%#` (TR-31.6, TR-31.8 name them); S52's `add` respects `nolabels`/`noticks`; S53's by() axes keep TR-31.10's silence.
- **Parallel batch: 11** (merge order S31, S32, S33). S32 edits the four appliers, the ten colour-reading mappers and the plot syntax; S33 edits `_apply_mlabel_opts`, `_apply_colorvar` and `SchemeParser._parse_lines`/`_include`, regenerates the schemes and lands last.
- **Can run with them because** S31 edits none of their functions: it edits `SchemeParser.apply_to_figure`/`apply_to_axis` (one line each), never the read-recording or a scheme file, and no applier or mapper.

## Evidence

All anchors at `c96facd` (dash_render.py 37,689 lines; dash.ado 8,487; dash_parse.mata 6,093; dash.sthlp 3,822). Symbols govern when lines drift.

**E1. The label parser** (`_dash_parse_axis_spec`, dash_render.py:22602). At HEAD the tail loop honours a fixed set and reads the rest from the whole text (S10 replaces both; the honoured set is S10's `_DASH_AXLABEL_HONOURED` afterwards):

```python
22633    head, tail = _dash_axis_head_split(text)
22646            if _nm not in ("format", "labsize", "angle", "grid", "nogrid"):
22647                out["unsupported"].append(_tok)
22649    out["angle"] = _parse_axis_angle(text)
22656    if re.search(r"\bnogrid\b", text, re.I):
22657        out["grid"] = False
22658    elif re.search(r"\bgrid\b", text, re.I):
```

Measured at HEAD (`python3 -c` on `dash_render`, warnings ignored):

```
', nolabels noticks labcolor(red) tlength(3) tposition(inside)' -> angle None, unsupported ['nolabels', 'noticks', 'labcolor(red)', 'tlength(3)', 'tposition(inside)']
', angle(rvertical)' -> angle None, unsupported []
', angle(stacked)'   -> angle None, unsupported []
', angle(Vertical)'  -> angle 1.5707963267948966
', angle(400)'       -> angle 6.981317007977318
'10 "angle(45)" 20'  -> angle 0.7853981633974483        (D-3; S10's N4 fixes it)
'10 "nogrid" 20, grid' -> grid False                    (D-3)
```

**E2. The angle reader** lowercases and knows two names (dash_render.py:5014-5024); the anglestyle table beside it is read only by `mlabangle()` (:4953-4957, `_dash_anglestyle_degrees` :4960):

```python
5014    m = re.search(r'\bangle\s*\(\s*([^)]+)\s*\)', raw, re.IGNORECASE)
5017    val = m.group(1).strip().lower()
5018    if val == "horizontal":
5020    if val == "vertical":
5021        return _math.pi / 2
5023        return _math.radians(float(val))
4953 _DASH_ANGLESTYLES = {
4954     "default": 0.0, "zero": 0.0, "horizontal": 0.0, "forty_five": 45.0,
4955     "ninety": 90.0, "vertical": 90.0, "rhorizontal": 180.0,
4956     "rvertical": 270.0, "two_seventy": 270.0, "stdarrow": 28.64,
```

**E3. The applier** sets only labsize, angle and grid (dash_render.py:22837-22854); there is no `option`, `by()` or colour argument:

```python
22837    if spec["labsize"]:
22846    if spec["angle"] is not None:
22847        axis_obj.major_label_orientation = spec["angle"]
22848    if spec["grid"] is not None:
```

**E4. Tick-only positions copy the major tick after the label look** (`_dash_apply_tick_option`, :22882; copy :22950-22957; called by `_dash_apply_axis_options` at :23030 after `_dash_apply_axis_spec` at :23025):

```python
22950        # A tick-only position is a major tick without its label: the same
22952        ax.minor_tick_in = ax.major_tick_in
22953        ax.minor_tick_out = ax.major_tick_out
22954        ax.minor_tick_line_color = ax.major_tick_line_color
```

So a label `noticks` or `tlength()` would leak onto the `ytick()` positions. twoway keeps them apart (research critic k07, k08, y08, y09): `ylabel(, noticks) ytick(25)` draws the 25 tick at default length; `ytick(25, tlength(5))` lengthens only it; `ytick(25, noticks)` hides only it.

**E5. The scale reader** (`_DASH_SCALE_SUBOPTS` :26022, `_dash_scale_spec` :26025-26048) honours log, reverse and range; zscale shares it (`_dash_apply_z_options`, :26184), and the second axes have their own set (`_DASH_SCALE2_SUBOPTS` :23114, read at :23221-23225):

```python
26022 _DASH_SCALE_SUBOPTS = frozenset({"log", "reverse", "range"})
26038    toks = _dash_by_tokens(str(raw or "").strip())
26039    names = [_dash_scale_name(t) for t in toks]
26041        _dash_report_suboptions(
26042            option, [t for t, n in zip(toks, names)
26043                     if n not in _DASH_SCALE_SUBOPTS], seen, key)
```

Measured: `_dash_scale_spec("off")`, `("noline lcolor(red) lwidth(thick) lpattern(dash)")`, `("alt titlegap(5)")` and `("OFF")` all return `{'log': False, 'reverse': False, 'values': [], 'lo': None, 'hi': None}`. `_dash_scale_name` (:4619-4629) lowercases through `_dash_subopt_name` (:25817), so a hand-written `OFF` would read as `off`.

**E6. Call order in both modes** (neither call site is edited, R12). Saved `_make_figure_body`: `_dash_scale_spec` :30255, `scheme.apply_to_figure` :30326, `_dash_add_secondary_axes` :30385, `_dash_apply_scale_ranges` :30392, `_dash_apply_axis_options` :30405, `_dash_finish_secondary_axes` :30660. Served template: :35166, :35203, :35206, :35257, :35268, :35417. In both, `_dash_apply_axis_options` runs after the scheme and after axis 2 is added, and `_dash_finish_secondary_axes` runs last; both receive `graph_opts` (so `by()` is known: `_dash_add_secondary_axes` already reads `graph_opts.get("by")`, :23086). The saved page's scripts write no axis property (the only axis-adjacent write is the stale cue's titles, :19346), so the look survives a saved move; S21's finisher writes tickers only.

**E7. Copy lists** (`_glyph_layer_lines`, def :32834). Listed today: `_DASH_ANGLESTYLES` (32929), `_DASH_SCALE_SUBOPTS` (32934), `_DASH_SCALE2_SUBOPTS` (32938), `_parse_axis_angle` and `_dash_anglestyle_degrees` (33223-33225), `_dash_parse_axis_spec`/`_dash_apply_axis_spec` (33230), `_dash_primary_axes`/`_dash_apply_tick_option` (33242), `_dash_apply_axis_options` (33243), `_dash_finish_secondary_axes` (33246), `_dash_scale_name` (33255), `_dash_apply_z_options` (33369), `_dash_scale_spec` (33375). Constants are emitted by value (`"%s = %r"`, :33056), so a frozenset built from another is order-free.

**E8. Stata side.**
- `_dash_validate_value`'s `axislist` branch only expands numlists (dash.ado:2326-2332); no axis rule bounds `angle()`, and `xscale`/`yscale` are not in the graph rule table (`_dash_option_rules` :2083-2089).
- `_dash_plot` records raw axis options and refuses twoway's parse errors at :5323-5324 (`_dash_axreq_add`, `_dash_axreq_check`), then validates the merged graph rules at :5364-5373, then checks `legend()` at :5378. The merged values are the locals `g_<key>` (key list :5066-5071, `ymlabel`, `ymtick`, `yscale2` included).
- Mata `_dash_axfam()` (dash_parse.mata:5351) lists the scale family first; `_dash_ax_parse` (:5391) returns a scale's words "every word of a scale" and a label's "after the first comma"; `_dash_axreq_add` (:5560) fills one row per axis option. S10 adds column 10 for the label, mlabel, tick and mtick families only. `_needed` (dash.ado:255) lists the Mata functions the guard requires.

**E9. twoway's truth** (StataNow 19.5, `sysuse auto`, `twoway scatter mpg weight`; research p1-18 §3 and critic additions, re-measured for this section 03oct2026 through `scripts/stata_slot.sh`, scratch probes `probe1.do`-`probe17.do`, quoted here with their results):
- Drawn: `nolabels`/`nolab`/`nolabel` (lab 0; `nola` r(198)); `noticks`/`notick`; `labels nolabels` and `ticks noticks` in one copy show both; across copies the last wins (`ylabel(, labels) ylabel(, nolabels)` lab 0). `labcolor(red)` #ff0000, `labc(red%50)` opacity .5, `labcolor(bogus)` and `labcolor(Red)` note and black. `tlength(3)` 3 rs; `tlength(*2)` 2.7776 (twice the scheme's 1.3888); `tlength(bogus)` note and 3.8194 (medium); `tlength(0)` no tick; `tlength(-1)` rc 0, the tick drawn 32.4 SVG units (1 rs) **into** the plot region under `outside` and under `inside` (probe5 t01, t02).
- `tposition()`: `o`, `out`, `i`, `ins`, `c`, `cross`, `insid` all read (probe6); `bogus`, `Inside`, `O`, `Out` note twice and cross the axis.
- `angle()`: the anglestyle names by full name only (`forty`, `ninet`, `two`, `std`, `zer`, `defa` note and draw 0), plus `h…horizontal` (≥1), `v…vertical` (≥1), `rh…rhorizontal` (≥2), `rv…rvertical` (≥2) on x and y; `r`, `V`, `H`, `Rv`, `Vertical`, `stacked`, `45deg` note and draw 0 (under s2color too, q11). Numbers -360..360 (`1e2`, `+30`, `-45.5`).
- `yscale(off)`: no line, ticks, labels or title (`ytitle("Hi")` too), grid kept. `off on` and `on off` in one copy: off; `yscale(off) yscale(on)`: drawn. `noline`/`noli`; `noline line` either order: no line; `noli lc(red)` and `lc(red) noline`: red line; `noline lwidth(thick)`, `noline lpattern(dash)`: no line (probe8). `lcolor(red) lwidth(thick) lpattern(dash)`: 255 0 0, .8, dash. `lwidth(bogus)`: note, scheme width kept; `lpattern(bogus)`, `lpattern(Dash)`: note, solid; `lcolor(bogus)`: note, black. `lwidth(*2)`: twice the scheme width.
- Under economist (y axis on the right with no line or ticks; probe17): `yscale(line)` draws a black line, `yscale(lcolor(red))` a red one, `ylabel(, ticks)` ticks of length zero.
- `alt`: y to the right, x above; under economist (y right by scheme) `yscale(alt)` moves it left; `yscale(alt alt)` r(198) "option alt not allowed"; `yscale(alt) yscale(alt)` toggles twice (left; residual R-S31-1). With `yaxis(2)`: `yscale(alt)` puts y1 right, inside y2; `yscale(alt axis(2))` puts y2 left, outside y1; both swap them.
- `titlegap(5)`: 5 rs; `titlegap(-2)` and `titleg(0)` accepted; `titlegap(*2)` twice the scheme's (stcolor 1.3888, s2color .3472); `titlegap(bogus)`: note, 3.8194.
- Refusals, only when the graph is drawn (with `nodraw` both are rc 0, probe1 P4/P6): `angle(400)`, `ang(-361)`, `angle(360.5)`, `angle(1e3)`, `angle(+400)` on ylabel, xlabel, ytick, ymlabel, ymtick and `ylabel(, axis(2) …)`: "textangle must be between -360.000 and 360.000", r(198); `yscale(lwidth(-1))`, `lw(-1)`, `lwidth(20000)`, `yscale(axis(2) lwidth(-1))`: "gm_linewidth must be between 0.000 and  1.0e+04" (two blanks), r(198). Both also under `by()`. Merged before checking: `(scatter mpg weight, ylabel(, angle(400))), ylabel(, angle(0))` rc 0, the reverse r(198) (probe3 Q1, Q2).
- Order of the bounds (probe3, probe14, probe15): axis by axis in the order y1, x1, y2, x2; on one axis the scale's `lwidth()` before any label or tick `angle()`. A parse error (`yscale(OFF)`) comes before any bound.
- Scale words: `yscale(OFF)`, `yscale(Alt)`, `yscale(ALT)`, `xscale(bogus)` r(198) "option OFF not allowed" (with the typed word); `yscale(lwidth(-1) lwidth(1))` "option lwidth() not allowed". Minimums re-measured (probe13): `alt`, `titleg`, `outerg`, `noli`, `li`, `noex`, `ex`, `nofex`, `fex`, `lst`, `lc`, `lw`, `lp`, `nofill`, `fill`, `norev`, `rev`, `sty` read; `al`, `title`, `outer`, `nol`, `l`, `noe`, `e`, `nofe`, `fe`, `ls`, `l(red)`, `nofil`, `fil`, `re`, `st` r(198) — S10's `_DASH_AXSCALE_SUBOPT_TABLE` minimums.
- Under `by(foreign)` (research b01-b08, y01-y08; probe9): drawn as if absent, no note: `yscale(off)` (labels, ticks and title still drawn), `xscale(off)`, `ylabel(, nolabels)`, `ylabel(, noticks)`, `ytick(25, noticks)`, `yscale(titlegap(10))`. Drawn: `noline`, `alt`, `lcolor(red)`, `labcolor(red)`, `tlength(5)`, `tposition(inside)`, `angle(vertical)`, `lwidth(thick) lpattern(dash)`, `xscale(alt)`, `ytick(25, tlength(5))`. A bad `titlegap(bogus)` or `labcolor(bogus)` is still noted.

**E10. dash at HEAD in Stata** (probe16): `dash scatter mpg weight, ylabel(, angle(400)) yscale(OFF)` rc 0 with "yscale() sub-option(s) not implemented and ignored: OFF"; `ylabel(, NOLABELS)` rc 0 (S10 refuses it); `ylabel(, labcolor("255,0,0"))` rc 0, named (twoway: "invalid '0'", r(198); residual R-S31-5).

**E11. Tests that pin today's behaviour** (flipped in place, never deleted; each gets a `Flipped:` line):
- `test/test_suboption_warnings.py::TestAnUnimplementedSuboptionIsNamed::test_once_in_both_modes[ylabel labcolor]`, `[ylabel labgap tlength]`, `[yscale reverse noline titlegap]`, `[xscale log range and off]` (SUBOPTIONS :58-66).
- `test/test_help_claims_7.py::TestSecondaryAxisLabelGrammar::test_a_suboption_it_does_not_honour_is_named` (:333-336, `ylabel2 labcolor(red)`).
- `test/test_help_claims_7.py::TestTheSecondAxisIsItsOwn::test_an_unhonoured_yscale2_suboption_is_named` (:1045-1049, `yscale2 noline`).
- `test/test_help_claims_8.py::TestTheUnsupportedProseIsTrue::test_xscale_alt_is_named_and_reverse_honoured` (:1399-1415).
- `test/test_mode_parity.py::TestTheTwoModesAgree::test_same_warnings[xscale(range()) and yscale with an unimplemented sub-option]` and `[xlabel with an unimplemented sub-option]` (CORPUS :1473-1477, `_MUST_WARN` :1905-1913).
- `test/test_suboption_reporting.cscript` SR-03 (:190-198) and SR-04 (:200-208), header :21-23.
- `test/test_help_claims_8.cscript` HC8-05 (:483-494, `xscale(alt)` named).
- `test/test_help_claims_1.cscript` HC1-15 (:818-849 as S10 leaves it: `xscale(bogus)` named) and `test/test_help_claims_2.cscript` HC2-21l (:636, rc 0).

Guards that must stay green: `test/test_graph_options.py::TestParseAxisAngle` (7) and `::TestAxisLabelAngle`; `test/test_colorvar_forms.py` `test_an_unknown_z_sub_option_is_named` (`zscale(alt)` named, :319-320); `test/test_axis_extents.py::TestTheReader::test_scale_names` (`"re"` stays `"re"`); `test/test_help_claims_2.py::TestAnUnknownSubOptionWordIsNamedAndDrawnWithout` (renderer-level, still named); `test/test_mode_parity.py::TestTheYLabelAngleEntry`.

## User stories

- **US-31.1** As a twoway user, I want `ylabel(, nolabels noticks labcolor(red%50) tlength(3) tposition(inside))` drawn as twoway draws it, so my axes look the same in the dashboard.
- **US-31.2** As a twoway user, I want `angle(rvertical)`, `angle(forty_five)` and twoway's `angle(v)`/`angle(rh)` honoured, and a mistyped `angle(Vertical)` noted and drawn level as twoway draws it.
- **US-31.3** As a twoway user, I want `xscale(off)`, `yscale(noline)`, the axis line's colour, width and pattern, `alt` and `titlegap()` drawn, on second axes too.
- **US-31.4** As a twoway user drawing `by()`, I want the forms twoway ignores there to be ignored silently and the rest drawn on every panel.
- **US-31.5** As a twoway user, I want `ytick(25, tlength(5))` to lengthen only those ticks, and `ylabel(, noticks)` to leave my `ytick()` positions alone.
- **US-31.6** As a twoway user, I want `angle(400)`, `yscale(lwidth(-1))` and `yscale(OFF)` refused with twoway's message, so a do-file that twoway stops stops in dash too.

## Business requirements

- **BR-31.1** Each label look sub-option of E9 draws what twoway draws (labels hidden, ticks hidden, label colour and opacity, tick length in Stata units, tick side) on x, y, x2 and y2, in both modes, before and after a filter move, with no note.
- **BR-31.2** Every anglestyle name and twoway's four axis abbreviations draw their angle; any other name, in any case, gets one note and is drawn at 0 even where the scheme draws vertical labels.
- **BR-31.3** Tick-only positions keep the scheme's tick look unless their own option gives `noticks`, `tlength()` or `tposition()`.
- **BR-31.4** Each scale look sub-option of E9 draws what twoway draws on axis 1 and axis 2, including `lcolor()` beside `noline`, `off` over `on` in one copy, and `alt` moving the axis to the other side (inside an existing second axis; a second axis outside the first).
- **BR-31.5** Under `by()`, `off`, `nolabels`, `noticks` (label and tick-only) and `titlegap()` are drawn as if absent and not named; the other look sub-options are drawn on every panel; a bad value is still noted once.
- **BR-31.6** An unknown value (`tposition(bogus)`, `tlength(bogus)`, `titlegap(bogus)`, `labcolor(bogus)`, `lcolor(bogus)`, `lwidth(bogus)`, `lpattern(Dash)`) is noted once and drawn as twoway draws it (crossing, medium, medium, black, black, scheme width, solid).
- **BR-31.7** In Stata, `angle()` outside -360..360 and a scale `lwidth()` outside 0..10000 are refused r(198) with twoway's line first, on the merged option, in twoway's order (E9), also under `by()` and `nodraw`; an `xscale()`/`yscale()` word twoway refuses is refused r(198) with twoway's message.
- **BR-31.8** Quoted label text is never read as a look sub-option.
- **BR-31.9** zlabel(), zscale() and xtick()'s label words keep naming the look sub-options they do not draw.

## Technical requirements

**TR-31.1 Label tail keys** (`_dash_parse_axis_spec`, in place, on S10's resolved names).
- `_DASH_AXLABEL_HONOURED` (S10's constant, in place) gains `"labels"`, `"nolabels"`, `"ticks"`, `"noticks"`, `"labcolor"`, `"tlength"`, `"tposition"`.
- `out` gains `"show_labels": None, "show_ticks": None, "labcolor": None, "tlength": None, "tposition": None, "angle_bad": None`.
- `show_labels` is True when the resolved names hold `labels`, else False when they hold `nolabels`, else None; `show_ticks` likewise with `ticks`/`noticks` (the positive word wins within one copy; S10's Mata merge keeps the last copy's word).
- `labcolor`, `tlength`, `tposition`: the argument (text between the first `(` and the final `)`, stripped) of the last token with that name; `out["typed"]` records each as typed (S10's rule).
- `angle`: `out["angle"] = _parse_axis_angle("angle(" + arg + ")")`; when that is None, `out["angle"] = 0.0` and `out["angle_bad"] = arg`.

**TR-31.2 `_parse_axis_angle(raw)`** (in place; body only). The regex at :5014 stays; `val` is stripped, never lowercased. `deg = _dash_anglestyle_degrees(val)`; if None, `deg` is 0, 90, 180 or 270 when `val` is non-empty and a prefix of `horizontal` (minimum 1), `vertical` (1), `rhorizontal` (2) or `rvertical` (2). Return `math.radians(deg)` or None. The docstring cites E9's measurement. `mlabangle()` is not changed (it calls `_dash_anglestyle_degrees` directly).

**TR-31.3 New `_dash_tick_geometry(position, length_px)`** (module level, after `_dash_primary_axes`) → `(tick_in, tick_out)` ints. `L = float(length_px)`, non-finite → 0; `n = int(round(min(abs(L), 100.0)))`. `L < 0` → `(n, 0)` (E9 t01/t02). `"outside"` → `(0, n)`; `"inside"` → `(n, 0)`; anything else (`"crossing"`) → `(h, h)` with `h = int(round(min(abs(L), 100.0) / 2.0))`.

**TR-31.4 New `_dash_tick_position(raw)`** → `"outside"`, `"inside"`, `"crossing"` when the stripped `raw` is non-empty, equals its lower case and is a prefix of exactly that word; else None. At most 32 characters are read.

**TR-31.5 New `_dash_tick_look(axis_obj, spec, minor=False, by_graph=False, option="", ref_in=4.0)`** applies `show_ticks`, `tlength`, `tposition` to `major_tick_*` (or `minor_tick_*`). `axis_obj` is one axis or Bokeh's splattable list (`_dash_primary_axes` returns the list type it is given, dash_render.py:22857-22868); the function loops over its members (`list(axis_obj)` when it is a list, else `[axis_obj]`) and reads and writes each member's own props, never through the splat (a splat of two axes reads back a list, not a number or a dict). Each note is printed once, before the loop.
- The base is `axis_obj._dash_scheme_look` (TR-31.11): `tick_length` (px float; 0 on an axis whose axisstyle draws no ticks, whose tickstyle has `length zero`), `tick_position`, `tick_color`. Without it: length `max(major_tick_in, major_tick_out)`, position `outside` if `major_tick_in == 0`, `inside` if `major_tick_out == 0`, else `crossing`; colour `major_tick_line_color`.
- `by_graph` and `show_ticks is False` → `show = None` (M6).
- Major, with `show`, `tlength` and `tposition` all None → return unchanged.
- `tlength` → `L = OptionTranslator.resolve_size(v, "gap", base_len * 0.75, ref_in) * OptionTranslator.PX_PER_PT`; ValueError → `_dash_style_note(f"{option}(tlength)", v, "size", "medium")` and `L = size_medium_pt("gap") * PX_PER_PT`.
- `tposition` → `_dash_tick_position(v)`; None → `_dash_style_note(f"{option}(tposition)", v, "tick position", "crossing")` and `"crossing"`.
- `show is False` → in = out = 0; otherwise `_dash_tick_geometry(pos, L)`. When `show is True` and the `*_tick_line_color` is None, it becomes the base's `tick_color` or `"#000000"`. A no-tick axis therefore stays without visible ticks unless `ticks` and a `tlength()` are both given (E9: economist's `ylabel(, ticks)` draws ticks of length zero; `tlength()` alone leaves the colour None).

**TR-31.6 `_dash_apply_axis_spec`** (in place) gains keywords `option="axis"`, `by_graph=False`, `colours=None` (S08's `ref_in` stays). After S08's labsize block and before the angle line:
- `show_labels is False and not by_graph` → `major_label_text_font_size = "0px"`, `major_label_standoff = 0`.
- `labcolor` → `hex_, alpha = OptionTranslator.parse_color_alpha(v, f"{option}(labcolor)", **(colours or {}))`; `major_label_text_color = hex_ or "#000000"`; `major_label_text_alpha = alpha` when not None. (S43 later passes this site's base colour.)
- `_dash_tick_look(axis_obj, spec, False, by_graph, option, ref_in)`.
- `angle_bad` not None → `_dash_style_note(f"{option}(angle)", spec["angle_bad"], "angle", "0 degrees")`; the existing orientation line then writes `0.0`.

**TR-31.7 `_dash_apply_tick_option`** (in place) gains `by_graph=False, ref_in=4.0`. The six copy lines (:22952-22957) keep the colour, width, alpha and dash copies; `minor_tick_in`/`minor_tick_out` come from `_dash_tick_look(ax, spec, True, by_graph, option, ref_in)`. Its named extras (S10's `spec["typed"]` for `format`, `labsize`, `angle`) also name `labcolor`, `labels`, `nolabels` as typed.

**TR-31.7a `_dash_apply_z_options`, the zlabel() report** (in place, :26149-26163; BR-31.9). The new honoured names leave `spec["unsupported"]`, so the colour bar would drop them silently; the report therefore names, as typed (`spec["typed"]`), every honoured key the ColorBar does not draw: `format`, `labsize`, `angle`, `grid`/`nogrid` (as today) and `labels`, `nolabels`, `ticks`, `noticks`, `labcolor`, `tlength`, `tposition`. This also closes a defect the research critic measured at `c96facd` (rule 7, test first in 31-01): `zlabel(4000 8000, angle(45))` is named `angle(0.785398)`, the radians `_parse_axis_angle` returns (`f"angle({spec['angle']:g})"`, :26159-26160), and after TR-31.1 `angle(stacked)` would be named `angle(0)`; both are named as typed. If S10 already reports from `spec["typed"]` here, only the new keys are added.

**TR-31.8 Scale look.**
- New constant `_DASH_SCALE_LOOK_SUBOPTS = frozenset({"off", "on", "noline", "line", "lcolor", "lwidth", "lpattern", "alternate", "titlegap"})`, directly above `_DASH_SCALE2_SUBOPTS` (:23114), which becomes `frozenset({"log", "reverse", "range"}) | _DASH_SCALE_LOOK_SUBOPTS`. `_DASH_SCALE_SUBOPTS` (:26022) is unchanged (zscale's set).
- `_dash_scale_name(tok)` (in place): `typed = str(tok).split("(", 1)[0].strip()`; `canon = _dash_subopt_canon(typed, _DASH_AXSCALE_SUBOPT_TABLE)`; None → return `typed` (so `OFF` stays `OFF` and is named); `canon == "range"` without `(` → `typed`; else `canon`. `rev`→`reverse`, `r(1)`→`range`, `noli`→`noline`, `lc(red)`→`lcolor`, `alt`→`alternate`, `re`→`re`.
- New `_dash_scale_look(raw)` (module level, directly after `_dash_scale_spec`) → the look dict: `off` (`"off"` in names), `line_off` (`"noline"` in names and `"lcolor"` not), `line_on` (`"line"` in names), `lcolor`, `lwidth`, `lpattern`, `titlegap` (last argument or None), `alternate` (bool). Tokens from `_dash_by_tokens`, names from `_dash_scale_name`. It never notes and never calls `_parse_scale_range`, so reading the look a second time cannot print a second `range()` note (`_parse_scale_range(raw, option or "scale")` keys its `_dash_warn_once` on the option, so a second `_dash_scale_spec(raw)` call would print `scale(range()) ignores abc` beside `yscale(range()) ignores abc`; measured by reading dash_render.py:4566-4616 at `c96facd`).
- `_dash_scale_spec(raw, option="", seen=None, key="")` (in place): it names tokens outside `_DASH_SCALE_SUBOPTS | _DASH_SCALE_LOOK_SUBOPTS` when `option` is `"xscale"` or `"yscale"`, and outside `_DASH_SCALE_SUBOPTS` otherwise (zscale keeps naming the look). It returns its five keys plus `"look": _dash_scale_look(raw)`.
- New `_dash_apply_scale_look(fig, axis_obj, look, option, number=1, by_graph=False, ref_in=4.0, colours=None)`:
  - `off` and not `by_graph` → `axis_obj.visible = False`.
  - `lcolor` → `parse_color_alpha(v, f"{option}(lcolor)", **(colours or {}))`; `axis_line_color = hex_ or "#000000"`, `axis_line_alpha` when given.
  - `lwidth` → `axis_line_width = OptionTranslator.translate_lwidth(v, axis_obj.axis_line_width, ref_in)`; ValueError → `_dash_style_note(f"{option}(lwidth)", v, "line width", "the scheme's width")`.
  - `lpattern` → `v != v.lower()` or ValueError from `translate_lpattern(v)` → `_dash_style_note(f"{option}(lpattern)", v, "line pattern", "solid")`, `axis_line_dash = []`; else `axis_line_dash = translate_lpattern(v)`.
  - `line_off` → `axis_line_color = None`; else `line_on` and `axis_line_color is None` → the base's `line_color` (TR-31.11) or `"#000000"`.
  - `titlegap` → `px = resolve_size(v, "gap", axis_obj.axis_label_standoff * 0.75, ref_in) * PX_PER_PT`; ValueError → note `"medium"` and `size_medium_pt("gap") * PX_PER_PT`. Applied only when not `by_graph`: `axis_label_standoff = int(round(max(-100.0, min(100.0, px))))`. The value is read (and noted) under by() too.
  - `alternate` → `_dash_axis_alternate(fig, axis_obj, number)`.
- New `_dash_axis_alternate(fig, axis_obj, number)`: find `axis_obj` (by identity) in `fig.left`/`fig.right` or `fig.below`/`fig.above`; remove it there; on the other side, number 1 inserts it at index 0 (innermost, inside a second axis), number 2 appends it (outermost). Not found → no-op. Each list is reassigned whole.

**TR-31.9 Where the scale look is applied.**
- `_dash_apply_axis_options` (in place): `by_graph = bool(str(graph_opts.get("by", "") or "").strip())`; `colours = getattr(fig, "_dash_scheme_colours", None)`; `ref_in` as S08 passes it. `_dash_apply_axis_spec(..., option=ax_key, by_graph=by_graph, colours=colours)` and `_dash_apply_tick_option(..., by_graph=by_graph, ref_in=ref_in)`. After the label/tick loop, for `("x", "xscale", fig.xaxis, "x_range_name")` and `("y", "yscale", fig.yaxis, "y_range_name")` with a non-blank raw value: `look = _dash_scale_look(raw)` (no note: the sub-option note was printed at :30255/:35166), then `_dash_apply_scale_look(fig, ax, look, opt, 1, by_graph, ref_in, colours)` for each axis of `_dash_primary_axes(axes, rattr)` (a list copy, since `alt` edits the side lists).
- `_dash_finish_secondary_axes` (in place): `by_graph`, `colours`, `ref_in = OptionTranslator.size_ref_of(fig)`. The `{n}label2` call passes `option=f"{n}label2", by_graph, colours`; the `{n}tick2` call passes `by_graph, ref_in`. After the label and tick blocks, when `ax` is not None and `scale_raw` is non-blank: `_dash_apply_scale_look(fig, ax, _dash_scale_look(scale_raw), f"{n}scale2", 2, by_graph, ref_in, colours)`. Its own report (:23223-23225) keeps `_DASH_SCALE2_SUBOPTS`, now with the look.

**TR-31.10 by() (M6).** `by_graph` suppresses exactly `off`, `nolabels`, label and tick-only `noticks`, and the `titlegap` standoff; none of them is named (all are honoured names). Every other look sub-option is applied per panel.

**TR-31.11 The scheme's look snapshot** (`SchemeParser`, in place).
- `apply_to_axis(axis, which=None, number=1)`: as its last statements, `axis._dash_scheme_look = {"tick_length": <S15's tick_length_px, or 0.0 when axis_flags(which, number) says the axisstyle draws no ticks>, "tick_position": <S15's tick_position>, "tick_color": self.tick_color, "line_color": self.axis_line_color}` (the colours as the scheme gives them, before any no-tick or no-line zeroing; `which` None counts as drawing ticks). Underscore attribute: never serialised.
- `apply_to_figure(fig)`: directly after S08's `fig._dash_size_ref_in` stamp, `fig._dash_scheme_colours = OptionTranslator.scheme_colour_context(self)` (S30's context: `bg_lookup`, `fg_lookup`, `naturally_white`; never `background_color`/`foreground_color` read here, so there is one colour context, P1.13.5). If S30 already stamps that context on the figure, that stamp is read instead and no second one is added.

**TR-31.12 Served copy lists** (append only; R2, A149). The index's R2 row lists S31 as in-place only; this section adds names at two anchors no other section uses (Notes, "R2"):
- Constants tuple: after `"_DASH_SCALE2_SUBOPTS",` (32938) add `"_DASH_SCALE_LOOK_SUBOPTS",`.
- Functions tuple: after `"_dash_apply_axis_options",` (33243) add `"_dash_tick_geometry", "_dash_tick_position", "_dash_tick_look", "_dash_scale_look", "_dash_apply_scale_look", "_dash_axis_alternate",`.
- In place: `_parse_axis_angle`, `_dash_parse_axis_spec`, `_dash_apply_axis_spec`, `_dash_apply_tick_option`, `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_scale_name`, `_dash_scale_spec`, `_DASH_SCALE2_SUBOPTS`, `_DASH_AXLABEL_HONOURED`. `SchemeParser` methods travel with the class. No JavaScript twin: no saved-page script reads or writes a label, tick, line or side property (E6), and the served move path recomputes data only.

**TR-31.13 Stata: scale words** (dash_parse.mata, in place). In `_dash_axreq_add`, column 10 is also filled for the scale family: the message `_dash_so_resolve(words, J(1, cols(words), 1), "axscale", names, msg, at)` returns, or `""`. `_dash_axreq_check` already refuses column 10 after column 9. The header index entry of `_dash_axreq_add` names the scale family.

**TR-31.14 Stata: draw-time bounds** (dash_parse.mata after S10's functions; dash.ado `_dash_plot`).
- New Mata `real scalar _dash_angle_out(string scalar s)`: 1 when `strtrim(s)` passes `_dash_so_isnum(…, 0)` and `strtoreal` of it is below -360 or above 360, else 0.
- New Mata `void _dash_axbound_list()`: reads the calling program's locals `g_<opt>` and sets its locals `_axb_n` and, per finding j, `_axb_k<j>` (`l` or `a`), `_axb_o<j>` (the option name) and `_axb_v<j>` (the argument as typed). Order (E9): for (side, axis) in (y,1), (x,1), (y,2), (x,2): the scale (`<s>scale` or `<s>scale2`) first, then `<s>label`, `<s>tick`, `<s>mlabel`, `<s>mtick` (axis 2: `<s>label2`, `<s>tick2`). Each value is parsed as `"<s><family>(" + value + ")"` with `_dash_ax_parse` (its words) and resolved with `_dash_so_resolve` (`"axscale"` or `"axlabel"`). The family word is always twoway's axis-1 spelling (`yscale(`, `ylabel(`, `ytick(`, `ymlabel(`, `ymtick(`), also for an axis-2 local (`g_yscale2`, `g_ylabel2`, `g_ytick2`): `_dash_ax_parse` recognises only twoway's option words (`_dash_axfam()`, dash_parse.mata:5351-5360, has no `label2` row as a family name), and the merged axis-2 value no longer carries its `axis(2)`. A scale's last `lwidth` token is always listed (`l`); a label or tick family's last `angle` token is listed (`a`) only when `_dash_angle_out` is 1. No regex; linear in the words.
- dash.ado `_dash_plot`, directly after the graph-rule loop (:5373) and before the `legend()` check (:5378), a block:
  ```stata
  mata: _dash_axbound_list()
  forvalues _j = 1/`_axb_n' {
      local _axv : copy local _axb_v`_j'
      if "`_axb_k`_j''" == "l" {
          _dash_validate_value "dash `_axb_o`_j''()" "lwidth" "style,0,10000,u" `"`macval(_axv)'"' ""
      }
      else {
          mata: _dash_say("err", "textangle must be between -360.000 and 360.000", "", "")
          mata: _dash_say("err", "dash: `_axb_o`_j''(): angle() must be an anglestyle or a number from -360 to 360 (got: ", st_local("_axv"), ")")
          exit 198
      }
  }
  ```
  S13's `,u` rule prints twoway's `gm_linewidth` line, then dash's, and exits 198.
- `_needed` (dash.ado:255) gains `_dash_axbound_list _dash_angle_out`; the dash_parse.mata header index gains one entry each.

**TR-31.15 Registries.**
- `test/function_test_map.py`, under the S31 anchor, alphabetical: `_dash_apply_scale_look` → `test/test_axis_suboptions.py::TestTheUnitFunctions::test_apply_scale_look`, `_dash_axis_alternate` → `…::test_axis_alternate`, `_dash_scale_look` → `…::test_scale_look`, `_dash_tick_geometry` → `…::test_tick_geometry`, `_dash_tick_look` → `…::test_tick_look`, `_dash_tick_position` → `…::test_tick_position`.
- `test/program_coverage_map.py` `COVERAGE["dash_parse.mata"]`, under the S31 anchor: `"_dash_angle_out": ("test_suboption_reporting.cscript:AXL-01",)`, `"_dash_axbound_list": ("test_suboption_reporting.cscript:AXL-05",)`.

**TR-31.16 Security (rule 1).** A colour reaches Bokeh only as `#rrggbb` from S30's reader; a pattern only as a list of ints; sizes as bounded ints or floats; no property name is built from user text. Notes echo through `_dash_style_note` (`_dash_display`: 80 printable characters, S06's SMCL escape). Tokens come from `_dash_by_tokens` (quote-aware, linear); `_dash_tick_position` reads at most 32 characters; `resolve_size` bounds at 64. In Stata, values are read with `st_local` in Mata and echoed only through `_dash_say`; `_dash_validate_value` reads by value (`_dash_text_args`). No `eval`, `exec`, `_stata()` on user text or `shell=True`.

## Boundaries

- **Batch partners (do not edit their functions):** S32 owns `_apply_marker_opts`, `_apply_line_opts`, `_apply_mlabel_opts`, `_apply_fill_opts`, the ten mappers it names, `SchemeParser.style_bundle` and `_dash_plot_style_indices`; S33 owns `_apply_colorvar`, `SchemeParser._parse_lines`/`_include`, the extractor and the 26 scheme files (it regenerates last).
- **Not edited here:** `_make_figure_body`, `_generate_app_source` (R12), `_dash_add_secondary_axes`, `_dash_apply_scale_ranges`, `_dash_report_suboptions`, `_dash_style_note`, `_dash_anglestyle_degrees`, `_DASH_ANGLESTYLES`, S10's tables other than `_DASH_AXLABEL_HONOURED`, `_dash_subopt_canon`/`_resolve`, Mata `_dash_so_*`, `_dash_rep_*`, S13's `_dash_validate_value` branch, S15's tick values and sides, `_dash_axis_expand`.
- **Later sections:** `add` (S52, with D-1 and D-2 of research p1-18); bare `*#`/`%#` at `labcolor()` and the axis line (S43); by() outer axes and edge labels (S53); `tlabel`/`tscale` (S51, which folds them onto these keys); `labgap`, `labstyle`, `tstyle`, `tl*` tick-line styles, grid styles, `gmin`/`gmax`, `custom` and the label `alternate` (P2.20); `fill`, `outergap()`, `lstyle()`, `extend`/`noextend` stay named.
- **Colour key:** `zlabel()` look words and `zscale()` look words stay named (BR-31.9).
- **Tracking documents:** S58 only (A145). **Plan files:** never edited (G6).

## Stata truth

**Extractor.** Create `scripts/extract_axis_subopt_truth.do`, copying `scripts/extract_axis2_truth.do`'s frame as S02 converted it (`DASH_REPO`, A130): `adopath ++ "${DASH_REPO}/"`, `global dash_nobrowser 1`, `set graphics off`, `version 19`, `sysuse auto`; the `_meta` locals (`c(stata_version)`, `c(born_date)`, `c(current_date)`, and `git rev-parse HEAD` written to a tempfile by `shell` and read back). Per probe:
- `log using "<work>/<id>.log", text replace name(_axl)`; `capture noisily twoway <cmd>` (drawn, never `nodraw`, unless the id says so); the rc; `log close _axl`;
- on rc 0: one record line of `.Graph.<ax>` members for `yaxis1`, `xaxis1` and, when present, `yaxis2` (the member list of research p1-18 truth.do: `draw_view.istrue`, `style.majorstyle.tickstyle.{show_labels.istrue, show_ticks.istrue, length.val, position.stylename, textstyle.color.rgb}`, `style.majorstyle.tickangle.val`, `style.linestyle.{color.rgb, width.val, pattern.stylename}`, `position.stylename`, `style.title_gap.val`), then `graph export "<work>/<id>.svg", replace`.

The python block reads each log's first line after the echoed command that starts `option`, `textangle`, `gm_linewidth`, `invalid` or `(note:` (as `messages`), each record, and each SVG through `scripts/svg_truth.py:svg_document` (`texts` `[text, round(x), round(y), fill, rotate]`, short `hlines`/`vlines` as `[x1, x2, y, stroke, width, dasharray]`, the long axis lines, `plotregion`). It writes `test/fixtures/axis_subopt_truth.json` as `{"_meta": {"stata_version", "born_date", "dash_commit", "extracted", "scheme_in_force"}, "probes": {id: {"cmd", "scheme", "rc", "messages", "members", "svg"}}}`; it never calls Stata, never uses `shell=True`, and writes a backtick as `\x60`.

**Probes** (fixture keys; `twoway scatter mpg weight, <opts>` under stcolor unless noted; `Y2` = `(scatter mpg weight) (scatter price weight, yaxis(2) xaxis(2))`; `BY` adds `by(foreign)`):
- **Base:** `base_st`, `base_s2` (scheme s2color), `base_econ` (economist).
- **Labels:** `lab_nolabels lab_nolab lab_noticks lab_notick lab_lab_nolab lab_ticks_noticks lab_noticks_ticks lab_copies_lab_nolab lab_copies_nolab_lab lab_labcolor lab_labc_alpha lab_labcolor_bogus lab_labcolor_Red lab_tl3 lab_tl0 lab_tl_neg lab_tl_neg_inside lab_tl_star2 lab_tl_bogus lab_tl_10pt lab_tp_outside lab_tp_inside lab_tp_crossing lab_tp_o lab_tp_i lab_tp_c lab_tp_bogus lab_tp_Inside lab_quoted` (`ylabel(10 "nolabels" 20 "angle(45)" 30)`).
- **Angles** (`ylabel(, angle(<v>))`): `ang_<name>` for the ten anglestyles; `ang_h ang_v ang_ve ang_rh ang_rho ang_rv ang_rve ang_r ang_forty ang_Vertical ang_V ang_Rv ang_stacked ang_45deg ang_m90 ang_m45_5 ang_1e2 ang_plus30 ang_360 ang_m360`; `ang_stacked_s2` (s2color); `xang_rv` (`xlabel(, angle(rv))`); `y2ang_rv` (Y2, `ylabel(, axis(2) angle(rvertical))`).
- **Scale:** `sc_off sc_off_title` (`ytitle("Hi") yscale(off)`) `sc_off_on sc_on_off sc_off_copies_on sc_noline sc_noli sc_noline_line sc_line_noline sc_noli_lc sc_lc_noline sc_noline_lw sc_noline_lp sc_style sc_style_abbr sc_lc_bogus sc_lp_bogus sc_lp_Dash sc_lw_bogus sc_lw_star2 sc_alt sc_xalt sc_alt_copies sc_tgap5 sc_tgap0 sc_tgap_neg sc_tgap_star2 sc_tgap_bogus econ_alt econ_lc econ_line` (the last three under economist: `yscale(alt)`, `yscale(lcolor(red))`, `yscale(line)`).
- **Second axis (Y2):** `y2_alt1 y2_alt2 y2_altboth y2_off2 y2_nolab2 y2_lc2 y2_tgap2`.
- **by() (BY):** `by_off by_xoff by_nolab by_noticks by_tgap by_tgap_bogus by_noline by_alt by_xalt by_lc by_labc by_tl by_tp by_ang by_style by_ytick_noticks by_ytick_tl by_y2_nolab by_y2_off` (the last two on Y2 with BY).
- **Tick-only:** `tk_base` (`ylabel(10(10)40) ytick(25)`), `tk_lab_noticks`, `tk_lab_tl`, `tk_own_tl`, `tk_own_noticks`, `tk_own_tp`.
- **Refusals and order:** `rf_ang400 rf_angm361 rf_ang360_5 rf_ang1e3 rf_angplus400 rf_xang400 rf_ytick_ang rf_ymlabel_ang rf_ymtick_ang rf_y2_ang rf_by_ang rf_nodraw_ang` (with `nodraw`, rc 0) `rf_lw_neg rf_lw_abbr rf_lw_big rf_y2_lw rf_by_lw rf_OFF rf_Alt rf_ALT rf_bogus rf_alt_alt rf_lw_dup rf_ord_xlab_yscale rf_ord_ylab_xscale rf_ord_ylab_yscale rf_ord_cap_angle rf_ord_y1lab_y2scale rf_ord_y2lab_x1scale rf_ord_y2lab_x2scale rf_ord_x2lab_y2scale rf_merge_seg_after rf_merge_after_seg rf_merge_lw rf_comma_labc` (`ylabel(, labcolor("255,0,0"))`).

**Run.** `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s31 $WT/scripts/extract_axis_subopt_truth.do`, then `git -C $WT add -f test/fixtures/axis_subopt_truth.json` (`.git/info/exclude:58`). Never patched by hand (R7); a value differing from E9 stops the section for investigation.

**Truth block** (`test/test_wp30_truth.cscript`, S01's stub `* ==== S31 P1.18a: Axis look sub-options ====`, gated `WP30_ONLY=S31`). Helpers directly above that header: one `python:` block (with its own imports of `html`, `json`, `re`, `warnings`, `bokeh.document.Document` and `bokeh.models.Plot`) defining the Python functions `_axl_saved` (a copy of the Python function `_br_saved`, test_bug_regressions.cscript:159-180, with its `_br_plots`/`_br_by_title` helpers renamed `_axl_`) and `_axl_profile`; any Stata helper program there declares `version 19` (TR-01.10 item 4). The cases sit between S01's `S31 start` and `S31 end` lines, which stay the block's first and last statements. Each case builds the page with `dash … saving("`w30_work'/axlNN.html")` (only under `` `w30_work' ``, erased before the end line), reads the figure's axes from the page, compares with the same command's twoway members in the same session, and reports through `_w30_expect`/`_w30_done` (`AXL-2n PASS: …`):
- **AXL-20** angles: for each of `rvertical forty_five ninety two_seventy stdarrow v rh rv Vertical stacked`, the y axis's `major_label_orientation` equals `radians(tickangle.val)`.
- **AXL-21** label look: `nolabels` (font `0px`), `noticks` (0/0), `labcolor(red%50)` (#ff0000, .5), `tlength(3)` (0/12), `tposition(inside)` (scheme length inside).
- **AXL-22** scale look: `off` (visible false), `noline` (no line colour), `noli lc(red)` (#ff0000), `lwidth(thick)` (3.072), `alt` (axis in `right`), `titlegap(5)` (standoff 19).
- **AXL-23** by(): `yscale(off) ylabel(, nolabels noticks) yscale(titlegap(10))` draws every panel's y axis as `by(foreign)` alone does, and the log names none of them; `yscale(noline alt)` is applied.
- **AXL-24** second axis: `yscale(alt axis(2))` puts y2 in `left` after y1; `yscale(off axis(2))` hides y2.

## TDD test stubs

The first block is red at `batch-11-base` (31-01). New file `test/test_axis_suboptions.py`: its `_spec(plots, go, scheme="s2color")` and `_figures(mode, tmp_path, plots, go, scheme="s2color")` copy `test_axis_label_grammar._spec`/`_figures` with `build_options["scheme"]`; `_MODES = ("saved", "served")`; data `test_axis_label_grammar._rep_frame()`; notes counted through S06's helpers or `warnings.catch_warnings`; saved moves through `test_saved_filter_layers._render`/`_move`; served moves through `test_mode_parity._served_after_move`. Pixel values are written as literals from E9 at one unit = 3.84 px (s2color tick 1.3888 rs = 5.33 px → 5).

**Regression (red at the base), every one `[mode]` in both modes:**
- Test: each anglestyle name on y sets the orientation `radians(deg)` (rvertical 4.712389, forty_five 0.785398, stdarrow 0.499862, …) — `test/test_axis_suboptions.py::TestAngleStyles::test_each_anglestyle_name`
- Test: `v`, `ve`, `h`, `rh`, `rho`, `rv`, `rve` read as 90, 90, 0, 180, 180, 270, 270 degrees; `r` does not — `::TestAngleStyles::test_twoways_axis_abbreviations`
- Test: `Vertical`, `V`, `Rv`, `stacked`, `forty`, `45deg` give orientation 0.0 and one note naming the typed value — `::TestAngleStyles::test_a_wrong_case_or_unknown_name_is_noted_and_level`
- Test: under s2color (S15's vertical y labels) `ylabel(, angle(stacked))` is 0.0, not pi/2 — `::TestAngleStyles::test_an_unknown_name_overrides_the_scheme_angle`
- Test: `xlabel(, angle(rv))`, `ylabel2(, angle(rvertical))`, `xlabel2(, angle(v))` — `::TestAngleStyles::test_x_and_second_axes`
- Test: `nolabels` → `major_label_text_font_size == "0px"` and standoff 0; `labels nolabels` keeps the scheme size — `::TestLabelVisibility::test_nolabels_and_the_positive_word`
- Test: `noticks` → 0/0; `ticks noticks` keeps (0, 5) — `::TestLabelVisibility::test_noticks_and_the_positive_word`
- Test: `labcolor(red%50)` → `#ff0000`, alpha 0.5; `labcolor(bogus)` → `#000000` and one note — `::TestLabelColourAndTicks::test_labcolor`
- Test: `tlength(3)` → (0, 12); `tlength(*2)` → (0, 11); `tlength(bogus)` → (0, 15) with a note; `tlength(-1)` → (4, 0); `tlength(0)` → (0, 0) — `::TestLabelColourAndTicks::test_tlength_in_stata_units`
- Test: `tposition(o|outside)` (0, 5), `(i|inside)` (5, 0), `(c|crossing)` (3, 3); `tposition(bogus)` and `(Inside)` (3, 3) with one note each — `::TestLabelColourAndTicks::test_tposition`
- Test: `ylabel(, noticks) ytick(25)`: major (0, 0), minor (0, 5); `ylabel(, tlength(5)) ytick(25)`: major (0, 19), minor (0, 5) — `::TestTickOnlyStyleIsSeparate::test_the_label_look_does_not_reach_the_tick_positions`
- Test: `ytick(25, tlength(5))` minor (0, 19), major (0, 5); `ytick(25, noticks)` minor (0, 0); `ytick(25, tposition(inside))` minor (5, 0) — `::TestTickOnlyStyleIsSeparate::test_a_tick_option_has_its_own_look`
- Test: `yscale(off)` → y axis `visible` False, its grid's colour unchanged; `yscale(off on)` and `(on off)` hidden — `::TestScaleLook::test_off`
- Test: `noline`, `noline line`, `line noline` → no line colour; `noli lc(red)` and `lc(red) noline` → `#ff0000`; `noline lwidth(thick)` → none — `::TestScaleLook::test_noline_and_lcolor`
- Test: `lcolor(red) lwidth(thick) lpattern(dash)` → `#ff0000`, 3.072, `[8, 4]`; `lc(red) lw(1) lp(shortdash)` → `#ff0000`, 3.84, `[4, 4]` — `::TestScaleLook::test_line_style`
- Test: `lcolor(bogus)` black, `lwidth(bogus)` scheme width, `lpattern(Dash)` and `(bogus)` `[]`, one note each — `::TestScaleLook::test_unknown_line_values_are_noted`
- Test: `titlegap(5)` 19, `titlegap(-2)` -8, `titlegap(*2)` 10, `titlegap(bogus)` 15 with a note — `::TestScaleLook::test_titlegap`
- Test: `yscale(alt)` puts y1 at `fig.right[0]`; `xscale(alt)` at `fig.above[0]`; under economist `yscale(alt)` puts it in `fig.left` — `::TestScaleLook::test_alt_moves_the_axis`
- Test: under economist (no y line or ticks), `yscale(line)` draws a line (colour not None), `yscale(lcolor(red))` a `#ff0000` line, and `ylabel(, ticks)` ticks of length (0, 0) — `::TestScaleLook::test_an_axis_the_scheme_draws_bare`
- Test: with a yaxis(2) layer: `yscale(alt)` → `right == [y1, y2]`; `yscale2(alt)` → `left == [y1, y2]`; both → y1 right, y2 left; with an xaxis(2) layer, `xscale2(alt)` → `below == [x1, x2]` — `::TestSecondAxis::test_alt_with_a_second_axis`
- Test: `yscale2(off)` hides y2; `ylabel2(, nolabels)` `0px`; `yscale2(noline lcolor(red))` red; no note for any — `::TestSecondAxis::test_second_axis_look`
- Test: under `by(foreign)`: `yscale(off) xscale(off) ylabel(, nolabels noticks) yscale(titlegap(10)) ytick(25, noticks)` gives every panel's axes the props `by(foreign) ytick(25)` gives and no note naming them; `yscale(noline alt lcolor(red)) ylabel(, labcolor(red) tlength(5) angle(vertical))` is applied on every panel; with a yaxis(2) layer, `ylabel2(, nolabels)` and `yscale2(off)` are drawn as absent with no note (probes `by_y2_nolab`, `by_y2_off`) — `::TestUnderBy::test_twoways_subset`
- Test: `by(foreign) yscale(titlegap(bogus))` notes once — `::TestUnderBy::test_a_bad_value_is_still_noted`
- Guard (green at the base): `xtick(2500, labcolor(red) nolabels)` names both as typed; `zlabel(1(1)5, labcolor(red) tlength(2) nolabels)` on a ColorBar names all three; `zscale(alt off noline titlegap(2))` names all four — `::TestOtherParsersStillName::test_named`
- Test (red at the base): `colorvar(price) zlabel(4000 8000, angle(45))` names `angle(45)`, not `angle(0.785398)`; `zlabel(4000 8000, angle(stacked))` names `angle(stacked)` — `::TestOtherParsersStillName::test_zlabel_names_each_as_typed`
- Guard (BR-31.8, D-3; green at the base after S10): `ylabel(10 "nolabels" 20 "labcolor(red)" 30 "angle(stacked)")` keeps the scheme's label size, colour and angle, draws the three texts, and prints no angle note — `::TestOtherParsersStillName::test_quoted_label_text_is_text`
- Guard: `yscale(range(abc) noline)` prints exactly one `range()` note, naming `yscale(range())`, and none naming `scale(range())`, in both modes — `::TestScaleLook::test_a_bad_range_is_noted_once`
- Test: a scatter with a dropdown and `ylabel(, noticks labcolor(red) angle(rvertical)) yscale(noline alt)` draws (0, 0), `#ff0000`, 4.712389, no line and the axis in `fig.right`, and the same after one move, saved (page JS) and served — `::TestAfterAFilterMove::test_the_look_holds`
- Test: `_dash_scale_spec("noli lc(red) alt off on titleg(5)")["look"]` is `{"off": True, "line_off": False, "line_on": False, "lcolor": "red", "lwidth": None, "lpattern": None, "titlegap": "5", "alternate": True}`; `_dash_scale_name("OFF") == "OFF"`, `("alt") == "alternate"` — `::TestTheUnitFunctions::test_scale_spec_look`
- Test: `_dash_tick_geometry` (outside/inside/crossing at 5.33, -3.84, 1e9, nan); `_dash_tick_position` (`o`, `cross`, `Inside`, `""`, 33 characters); `_dash_tick_look` on a bare `LinearAxis` and on a splattable list of two axes (each member set, no list read back); `_dash_scale_look` (the dict of `test_scale_spec_look`, and no warning for `range(abc)`); `_dash_apply_scale_look` on a figure; `_dash_axis_alternate` with and without a second axis — `::TestTheUnitFunctions::test_tick_geometry`, `::test_tick_position`, `::test_tick_look`, `::test_scale_look`, `::test_apply_scale_look`, `::test_axis_alternate`
- Guard: a 10,000-character `labcolor()`, `lpattern()` and `tposition()`, `tlength("9" * 10**6)`, `angle(` + `"1" * 10**6` + `)` are judged within 0.5 s, notes at most 80 printable characters, and no `<script` or the value reaches a style string of the page — `::TestAdversarial::test_hostile_values`

**Regression (Stata, red at the base), `test/test_suboption_reporting.cscript`** (one contiguous run after SR-09, before the summary; each case runs twoway's twin in the same case and compares rc and first line):
- AXL-01 `dash scatter mpg weight, ylabel(, angle(400))`: 198, the log holds `textangle must be between -360.000 and 360.000` and `dash: ylabel(): angle()`.
- AXL-02 `xlabel(, ang(-361))`, `ylabel(, angle(1e3))`, `ytick(25, angle(400))`, `ymlabel(25, angle(400))`, `ymtick(25, angle(400))`, Y2 `ylabel(, axis(2) angle(400))`, `xlabel(, angle(400)) by(foreign)`, `ylabel(, angle(400)) nodraw`: 198 each.
- AXL-03 `yscale(lwidth(-1))`, `yscale(lw(20000))`, Y2 `yscale(axis(2) lwidth(-1))`, `yscale(lwidth(-1)) by(foreign)`: 198, `gm_linewidth must be between 0.000 and`.
- AXL-04 `yscale(OFF)`, `yscale(Alt)`, `xscale(bogus)`, `yscale(alt alt)`, `yscale(lwidth(1) lwidth(2))`: 198 and `option OFF not allowed`, `option Alt not allowed`, `option bogus not allowed`, `option alt not allowed`, `option lwidth() not allowed`.
- AXL-05 order: `xlabel(, angle(400)) yscale(lwidth(-1))` → gm_linewidth; `ylabel(, angle(400)) xscale(lwidth(-1))` → textangle; `ylabel(, angle(400)) yscale(OFF)` → `option OFF not allowed`; Y2 `ylabel(, axis(2) angle(400)) xscale(lwidth(-1))` → gm_linewidth; Y2 `ylabel(, axis(2) angle(400)) xscale(axis(2) lwidth(-1))` → textangle.
- AXL-06 merge: `dash (scatter mpg weight, ylabel(, angle(400))), ylabel(, angle(0))` and `(scatter mpg weight, yscale(lw(-1))), yscale(lw(1))`: 0; `(scatter mpg weight, ylabel(, angle(0))), ylabel(, angle(400))`: 198.
- AXL-07 (guards and one red) rc 0: `angle(360)`, `angle(-360)`, `angle(400deg)` (note), `yscale(lwidth(10000))`, `ylabel(, tlength(-1))`, `yscale(titlegap(-2))`; `ylabel(, angle(Vertical))` rc 0 with one note naming `Vertical` (red: no note at the base).
- AXL-08 `yscale(off noline alt lcolor(red) lwidth(thick) lpattern(dash) titlegap(5))` and `ylabel(, nolabels noticks labcolor(red) tlength(3) tposition(inside) angle(rvertical))`: rc 0 and no "not implemented" line.

**Flipped in place** (E11; 31-09 and 31-10): the four SUBOPTIONS rows become `("ylabel labcolor", {"ylabel": ", labcolor(red) labgap(2)"}, None, "ylabel", ["labgap(2)"], ["labcolor"])`, `("ylabel labgap tlength", …, ["labgap(2)"], ["tlength"])`, `("yscale reverse noline titlegap", {"yscale": "reverse noline titlegap(2) outergap(1)"}, None, "yscale", ["outergap(1)"], ["reverse", "noline", "titlegap"])`, `("xscale log range and off", {"xscale": "log range(1000 5000) off extend"}, None, "xscale", ["extend"], ["log", "range", "off"])`; `TestTheHonouredOnesStayQuiet` gains `{"ylabel": ", nolabels noticks labcolor(red) tlength(3) tposition(inside) angle(rvertical)", "yscale": "off noline lcolor(red) lwidth(thick) lpattern(dash) alt titlegap(5)"}`. HC7's two tests use `labgap(2)` and `outergap(1)`. HC8's pytest and HC8-05 assert `xscale(alt)` puts the x axis in `fig.above` with no note (`test_xscale_alt_is_drawn_and_reverse_honoured`; the `Flipped:` line names the old node). The two parity CORPUS rows use `"reverse outergap(1)"` and `"#5, labgap(2)"`, with their `_MUST_WARN` text. SR-03 uses `labgap(2)`; SR-04 names `outergap(1)` and not `reverse noline titlegap`. HC1-15 and HC2-21l expect `xscale(bogus)` r(198) `option bogus not allowed`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Angles, label look, tick-only look, scale look, second axis, by(), other parsers, unit functions, adversarial | pytest `test/test_axis_suboptions.py` | literals from E9; `axis_subopt_truth.json` via `TestTheTruthFixture` | yes, and after a move |
| Fixture stamp and agreement | pytest `TestTheTruthFixture` (31-02) | `axis_subopt_truth.json` | — |
| Refusals, order, merge, notes in Stata | cscript `test_suboption_reporting.cscript` AXL-01..08 | live twoway twin | saved (Stata route) |
| Drawn against twoway | cscript truth block AXL-20..24 | live twoway members | saved page; served by pytest |
| Parity | pytest `test_mode_parity.py` (CORPUS and MOVE_CORPUS cases, `_axes` profile extended) | — | yes |
| Pinned flips | the files of E11 | — | yes |
| Registries | `test_function_test_map.py`, `test_program_coverage_map.py`, `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads`, `test_tracking_documents.py` | — | — |

Parity additions (R8, appended): `test_mode_parity.py` `_axes(fig).one` records `tick_in`, `tick_out`, `minor_tick_in`, `minor_tick_out`, `label_alpha`, `label_color`, `label_standoff`, `axis_label_standoff`, `line_dash` and the side (`"left"`, `"right"`, `"below"`, `"above"`, found by identity in the figure's lists); CORPUS gains `"axis look: label sub-options"`, `"axis look: scale sub-options"`, `"axis look: anglestyle names"`, `"axis look: second axis alt and off"` and `"axis look: under by()"`; MOVE_CORPUS gains `"axis look after a move, dropdown"`.

**Acceptance criteria.**
- **AC-31.1** Every regression stub fails at `batch-11-base` and passes after 31-12; the failure text is saved.
- **AC-31.2** Every E9 drawn form gives in dash the measured look on x, y, x2 and y2, identically in both modes and after a move (BR-31.1-31.4).
- **AC-31.3** Under `by()` the four ignored forms are drawn as absent with no note; the rest are drawn (BR-31.5).
- **AC-31.4** AXL-01..06 give twoway's rc and first line; AXL-07/08 rc 0 (BR-31.7).
- **AC-31.5** The flipped pins pass with their new expectations, and every guard of E11 stays green.
- **AC-31.6** The full suite through the queue reports 0 failed; the truth block prints PASS for AXL-20..24 and no SKIP.

## Tasks

**Commit boundary.** One commit unit, entry `P1.18a`: tasks 31-01 to 31-13. 31-01 never commits; 31-13 makes the one commit, subject `Draw the axis look sub-options and twoway's anglestyle names (WP-30 P1.18a)`. `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s31`, `$S` is `<scratch>/s31`.

<task type="auto" id="31-01">
  <name>Write the failing regression tests</name>
  <files>test/test_axis_suboptions.py, test/test_suboption_reporting.cscript</files>
  <action><![CDATA[Check the cut: `git -C $WT rev-parse HEAD` equals `<scratch>/batch-11-base.txt` and `git -C $WT branch --show-current` prints `wp30-s31`; `mkdir -p $S`. Read `<scratch>/batch-11-impact.txt` and state the CRITICAL warnings for `_dash_parse_axis_spec`, `_parse_axis_angle`, `_dash_scale_spec` and the HIGH ones of Risk factor 1. Confirm the contracts in one `python3 -c` from $WT: `OptionTranslator.resolve_size`, `size_medium_pt`, `size_ref_of`, `PX_PER_PT`; `translate_lwidth` has `default_px` and `ref_in`; `parse_color_alpha` has `background` and `foreground`; `_dash_subopt_canon`, `_DASH_AXSCALE_SUBOPT_TABLE`, `_DASH_AXLABEL_HONOURED` exist; `_dash_parse_axis_spec(", angle(45)")["typed"]` exists; `SchemeParser.apply_to_axis` takes `which, number`; `grep -n "_dash_so_resolve\|_dash_so_isnum" $WT/dash_parse.mata` finds both; if any is missing, stop and report. Create `test/test_axis_suboptions.py` with every pytest stub of "TDD test stubs" (exact class and test names, the helpers named there, literal expected values), and append AXL-01..AXL-08 to `test/test_suboption_reporting.cscript` as one contiguous block after SR-09 with header lines in its `*!` list. Run them on the unmodified tree and write `<scratch>/31-P1.18a-failure.txt`: the base sha, each FAILED pytest node with its first assertion line, each AXL FAIL line, and the guard nodes that pass. Do not edit dash_render.py, dash.ado or dash_parse.mata and do not commit.]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_axis_suboptions.py -q -n0 -p no:cacheprovider -rf` reports at least one failure in every regression class (the guards `TestOtherParsersStillName` and `TestAdversarial` pass and are listed as guards in the failure text); `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_suboption_reporting.cscript > $S/run_test_suboption_reporting.do && /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh $S $S/run_test_suboption_reporting.do`; `grep -cE "AXL-0[1-7] FAIL" $S/run_test_suboption_reporting.log` prints at least 7; `test -s <scratch>/31-P1.18a-failure.txt`; `git -C $WT status --porcelain` shows only the two test files.]]></verify>
  <done>Every regression test existed, failed on the unmodified tree, and its failure text was saved.</done>
</task>

<task type="auto" id="31-02">
  <name>Extract the axis sub-option truth fixture</name>
  <files>scripts/extract_axis_subopt_truth.do, test/fixtures/axis_subopt_truth.json, test/test_axis_suboptions.py</files>
  <action><![CDATA[Create `scripts/extract_axis_subopt_truth.do` exactly as "Stata truth / Extractor" says, with every probe id listed there, a `*!` header naming WP-30 P1.18a and the run line, and the python block's rules (no Stata call, no `shell=True`, `\x60`). Run it through the slot (`DASH_REPO=$WT .../scripts/stata_slot.sh $S $WT/scripts/extract_axis_subopt_truth.do`) and `git -C $WT add -f test/fixtures/axis_subopt_truth.json`. Compare the fixture with E9 probe by probe (angles, tick lengths, positions, colours, line style, side, title gap, the by() subset, every refusal's rc and first line, the order probes); any difference stops the section. Add class `TestTheTruthFixture` to `test/test_axis_suboptions.py`: `test_meta_is_stamped` (the four `_meta` keys), `test_the_literals_are_twoways` (each literal angle, length and side the regression tests use equals the fixture's member, converted at 3.84 px per unit), `test_the_by_subset` (the by() ignored set equals the probes whose members equal `base`).]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('$WT/test/fixtures/axis_subopt_truth.json'));print(sorted(d['_meta']), len(d['probes']))"` prints the four keys and at least 150; `python3 -m pytest $WT/test/test_axis_suboptions.py -q -n0 -p no:cacheprovider -k TestTheTruthFixture` passes; `git -C $WT diff --cached --name-only` lists the fixture.]]></verify>
  <done>The truth fixture was extracted from StataNow 19.5 with its stamp and read by tests that pin the literals to it.</done>
</task>

<task type="auto" id="31-03">
  <name>Read anglestyles as twoway reads them</name>
  <files>dash_render.py</files>
  <action><![CDATA[Warn in the progress output that `_parse_axis_angle` and `_dash_parse_axis_spec` are CRITICAL. Rewrite `_parse_axis_angle`'s body (about :5014-5024) per TR-31.2, keeping its signature, regex and None contract, with a docstring citing E9's abbreviation measurements. In `_dash_parse_axis_spec`, on S10's resolved angle token, set `out["angle"] = 0.0` and `out["angle_bad"] = arg` when `_parse_axis_angle` returns None (TR-31.1), and add `angle_bad` to `out`'s defaults. In `_dash_apply_axis_spec` add the keyword `option="axis"` and the `angle_bad` note of TR-31.6 directly above the orientation line. Do not touch `_dash_anglestyle_degrees` or `_DASH_ANGLESTYLES`.]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_axis_suboptions.py -q -n0 -p no:cacheprovider -k "TestAngleStyles and not second"` passes; `python3 -m pytest $WT/test/test_graph_options.py -q -n0 -p no:cacheprovider -k "ParseAxisAngle or AxisLabelAngle"` passes.]]></verify>
  <done>Axis labels took every anglestyle name and twoway's abbreviations, and a wrong-case or unknown name was noted and drawn at 0.</done>
</task>

<task type="auto" id="31-04">
  <name>Draw the label and tick look</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[Warn that `_dash_apply_axis_spec` is HIGH. Extend `_DASH_AXLABEL_HONOURED` in place and add the TR-31.1 keys to `_dash_parse_axis_spec`. Add `_dash_tick_geometry`, `_dash_tick_position` and `_dash_tick_look` after `_dash_primary_axes` (about :22858) exactly as TR-31.3-31.5, each with a docstring citing E9. In `_dash_apply_axis_spec` add `by_graph=False` and `colours=None` and the nolabels, labcolor and tick-look lines of TR-31.6 after S08's labsize block. In `SchemeParser.apply_to_axis` add the `_dash_scheme_look` snapshot as its last statements and in `apply_to_figure` the `_dash_scheme_colours` stamp after S08's stamp (TR-31.11; first grep `apply_to_figure` for an S30 stamp of background and foreground and reuse it if present). In `_dash_apply_axis_options` compute `by_graph` and `colours` and pass `option=ax_key`, `by_graph`, `colours` to `_dash_apply_axis_spec` (TR-31.9). Add the three `_dash_tick_*` keys of TR-31.15 under the S31 anchor of `test/function_test_map.py`, alphabetically.]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_axis_suboptions.py -q -n0 -p no:cacheprovider -k "TestLabelVisibility or TestLabelColourAndTicks or tick_geometry or tick_position or tick_look"` passes; `python3 -m pytest $WT/test/test_function_test_map.py $WT/test/test_scheme_fallback_provenance.py $WT/test/test_textbox_no_text.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>nolabels, noticks, labcolor, tlength and tposition were drawn on the labelled axes from the scheme's tick geometry, silent under by() where twoway is.</done>
</task>

<task type="auto" id="31-05">
  <name>Give tick-only positions their own look</name>
  <files>dash_render.py</files>
  <action><![CDATA[Warn that `_dash_apply_tick_option` and `_dash_apply_z_options` are HIGH. In `_dash_apply_tick_option` add `by_graph=False, ref_in=4.0`, replace the two `minor_tick_in`/`minor_tick_out` copy lines (about :22952-22953) with `_dash_tick_look(ax, spec, True, by_graph, option, ref_in)` placed after the four colour/width/alpha/dash copies, rewrite the comment above them (the scheme's geometry, the option's own look; E4), and add `labcolor`, `labels`, `nolabels` to its named typed extras (TR-31.7). In `_dash_apply_axis_options` pass `by_graph` and `ref_in` to it. In `_dash_apply_z_options` report the zlabel() keys the ColorBar does not draw from `spec["typed"]` and add `labels`, `nolabels`, `ticks`, `noticks`, `labcolor`, `tlength`, `tposition` to them (TR-31.7a, BR-31.9), so `angle(45)` is named as typed.]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_axis_suboptions.py -q -n0 -p no:cacheprovider -k "TestTickOnlyStyleIsSeparate or TestOtherParsersStillName"` passes (including `test_zlabel_names_each_as_typed`); `python3 -m pytest $WT/test/test_colorvar_forms.py $WT/test/test_help_claims_8.py -q -n0 -p no:cacheprovider -k "z_sub_option or xtick"` passes.]]></verify>
  <done>xtick()/ytick() positions kept the scheme's tick look unless their own option changed it, and the colour key kept naming the look words.</done>
</task>

<task type="auto" id="31-06">
  <name>Draw the scale look on both axes</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[Warn that `_dash_scale_spec` is CRITICAL and `_dash_scale_name` HIGH. Add `_DASH_SCALE_LOOK_SUBOPTS` above `_DASH_SCALE2_SUBOPTS` and widen the latter in place; rewrite `_dash_scale_name` on S10's table, add `_dash_scale_look` directly after `_dash_scale_spec`, and give `_dash_scale_spec` its option-gated honoured set and its `look` key (TR-31.8). Add `_dash_apply_scale_look` and `_dash_axis_alternate` after `_dash_tick_look` (TR-31.8). In `_dash_apply_axis_options` apply the primary scale look after the label/tick loop, and in `_dash_finish_secondary_axes` the second axis's look and the label2/tick2 keywords (TR-31.9). Add the three keys of TR-31.15 (`_dash_apply_scale_look`, `_dash_axis_alternate`, `_dash_scale_look`) under the S31 anchor of `test/function_test_map.py`.]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_axis_suboptions.py -q -n0 -p no:cacheprovider -k "TestScaleLook or TestSecondAxis or TestUnderBy or TestAfterAFilterMove or scale_spec_look or scale_look or apply_scale_look or axis_alternate"` passes; `python3 -m pytest $WT/test/test_axis_extents.py $WT/test/test_axis2_suboptions.py $WT/test/test_colorvar_forms.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>off, noline, the axis line's colour, width and pattern, alt and titlegap were drawn on axes 1 and 2 in both modes, with twoway's by() subset ignored silently.</done>
</task>

<task type="auto" id="31-07">
  <name>List the new names and extend parity</name>
  <files>dash_render.py, test/test_mode_parity.py</files>
  <action><![CDATA[Warn that `ServerAppBuilder._glyph_layer_lines` is HIGH. Add `"_DASH_SCALE_LOOK_SUBOPTS",` after `"_DASH_SCALE2_SUBOPTS",` (about :32938) and the six functions of TR-31.12 after `"_dash_apply_axis_options",` (about :33243), with a one-line comment `# WP-30 P1.18a: the axis look`, appending only (TR-31.12). In `test/test_mode_parity.py` extend `_axes(fig).one` with the keys of the Test plan's parity row, append the five CORPUS cases and the MOVE_CORPUS case (R8), and flip the two CORPUS rows and their `_MUST_WARN` entries of E11 to `"reverse outergap(1)"` and `"#5, labgap(2)"`, appending each `Flipped:` line to `$S/31-flips.txt`.]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_mode_parity.py $WT/test/test_statistical_helpers.py $WT/test/test_resource_limits.py -q -n0 -p no:cacheprovider -k "TwoModes or Move or ServedApp or CopiedHelpers or YLabelAngle"` passes.]]></verify>
  <done>The served app carried every new helper and the parity corpus showed both modes drawing the axis look alike before and after a move.</done>
</task>

<task type="auto" id="31-08">
  <name>Refuse twoway's axis refusals in Stata</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[In dash_parse.mata extend `_dash_axreq_add`'s column 10 to the scale family (TR-31.13) and add `_dash_angle_out` and `_dash_axbound_list` after S10's Mata functions (TR-31.14), each preceded by a comment citing E9's measured order and messages, with no `regexm`; add their header-index entries and update `_dash_axreq_add`'s. In dash.ado insert TR-31.14's block in `_dash_plot` directly after the graph-rule validation loop (grep `foreach _vrule of local _dash_rules_graph` and take the second loop's end) and before the `g_legend` check, and add both names to `_needed`. Add the two COVERAGE entries of TR-31.15 under the S31 dash_parse.mata anchor of `test/program_coverage_map.py`.]]></action>
  <verify><![CDATA[Run `test_suboption_reporting.cscript` through the driver: `grep -E "AXL-0[1-8] (PASS|FAIL)" $S/run_test_suboption_reporting.log` shows 8 PASS; `python3 -m pytest $WT/test/test_program_coverage_map.py $WT/test/test_file_headers.py $WT/test/test_no_orphans.py -q -n0 -p no:cacheprovider` passes (the `_needed` and header-index pins).]]></verify>
  <done>dash refused out-of-range angles and line widths and the scale words twoway refuses, with twoway's words, order and return code.</done>
</task>

<task type="auto" id="31-09">
  <name>Flip the pinned pytest expectations</name>
  <files>test/test_suboption_warnings.py, test/test_help_claims_7.py, test/test_help_claims_8.py</files>
  <action><![CDATA[Flip in place, as "TDD test stubs / Flipped in place" gives them: the four SUBOPTIONS rows and the new `TestTheHonouredOnesStayQuiet` case; `TestSecondaryAxisLabelGrammar::test_a_suboption_it_does_not_honour_is_named` to `labgap(2)`; `TestTheSecondAxisIsItsOwn::test_an_unhonoured_yscale2_suboption_is_named` to `outergap(1)`; and `TestTheUnsupportedProseIsTrue::test_xscale_alt_is_named_and_reverse_honoured` renamed `test_xscale_alt_is_drawn_and_reverse_honoured`, asserting no `xscale()` sub-option note and the x axis in `fig.above` in both modes. Append one `Flipped: <node> -- <old expectation> was wrong because twoway draws <x> (E9)` line per node to `$S/31-flips.txt`.]]></action>
  <verify><![CDATA[`python3 -m pytest $WT/test/test_suboption_warnings.py $WT/test/test_help_claims_7.py $WT/test/test_help_claims_8.py -q -n0 -p no:cacheprovider` passes; `wc -l < $S/31-flips.txt` is at least 9.]]></verify>
  <done>The pytest pins that asserted the old naming asserted twoway's drawing instead.</done>
</task>

<task type="auto" id="31-10">
  <name>Flip the pinned certification cases</name>
  <files>test/test_suboption_reporting.cscript, test/test_help_claims_8.cscript, test/test_help_claims_1.cscript</files>
  <action><![CDATA[Flip in place (R1, only the named cases and their `*!` header lines): SR-03 to `ylabel(, labgap(2))` named; SR-04 to `yscale(reverse noline titlegap(2) outergap(1))` naming `outergap(1)` and not `reverse noline titlegap`; HC8-05's `xscale(alt)` half to rc 0 with no `xscale() sub-option` line; HC1-15's `xscale(bogus)` half (a separate command, as S10 left it) to rc 198 with `option bogus not allowed` in the log. Append their `Flipped:` lines to `$S/31-flips.txt`.]]></action>
  <verify><![CDATA[Run the three scripts through the driver; each log ends with its `ALL CHECKS PASSED` line, and `grep -E "(SR-0[34]|HC8-05|HC1-15) PASS"` finds four lines across the logs.]]></verify>
  <done>The certification pins asserted twoway's drawing and refusals for the axis look.</done>
</task>

<task type="auto" id="31-11">
  <name>Fill the truth block and HC2-21l</name>
  <files>test/test_help_claims_2.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[Flip HC2-21l (about :636) to `_hc2_dash "HC2-21l" 198 ...` with its header line, appending its `Flipped:` line to `$S/31-flips.txt`. In `test/test_wp30_truth.cscript` fill S01's S31 stub between its start and end lines with AXL-20..AXL-24 exactly as "Stata truth / Truth block", the helpers `_axl_saved` and `_axl_profile` directly above `* ==== S31 P1.18a: Axis look sub-options ====`; each case reports through `_w30_expect`/`_w30_done` and writes only under `` `w30_work' ``, erasing its pages before the `S31 end` line (TR-01.10 item 4).]]></action>
  <verify><![CDATA[`WP30_ONLY=S31` run of `test_wp30_truth.cscript` through the driver: `grep -c "AXL-2[0-4] PASS" $S/run_test_wp30_truth.log` prints 5, `grep -c "ALL CHECKS PASSED" $S/run_test_wp30_truth.log` prints 1, and the log has no `SKIP`; the HC2 script run ends `ALL CHECKS PASSED`; `python3 -m pytest $WT/test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider -k Wp30` passes.]]></verify>
  <done>The drawn axis look was compared with twoway's members in Stata and the last pin was flipped.</done>
</task>

<task type="auto" id="31-12">
  <name>Document the axis look in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Re-grep each paragraph at the base (S10, S15, S18, S21 edited this title earlier; R3) and edit only these: (1) the label sub-options paragraph (about :2834-2838): add `nolabels`/`labels`, `noticks`/`ticks` (the positive word wins in one option), `labcolor()`, `tlength()`, `tposition()`, `angle()`'s anglestyle names and twoway's `h`, `v`, `rh`, `rv`, the note-and-0 rule for another name, the -360..360 refusal, and xtick()/ytick()'s own look; (2) a new paragraph after the `range()` paragraph (about :2850) for the scale look of TR-31.8, the `xscale(bogus)` refusal, the `lwidth()` bound and the by() subset (M6); (3) the ylabel2()/yscale2() paragraph (about :3017-3025): the same look on axis 2, `alt` outside the first axis; (4) the Differences sentence (about :784-788, as S10 left it): `xscale(bogus)` is refused as twoway refuses it; (5) the xalternate sentence (about :3757-3760): `alt` is drawn. Use the twoway messages exactly as E9 quotes them and name no tool or vendor.]]></action>
  <verify><![CDATA[`grep -c "rvertical" $WT/dash.sthlp` is at least 2; `grep -c "names as a sub-option it does not implement" $WT/dash.sthlp` prints 0; `python3 -m pytest $WT/test/test_help_claims_1.py $WT/test/test_help_claims_2.py $WT/test/test_help_claims_7.py $WT/test/test_help_claims_8.py $WT/test/test_help_conformance.py -q -n0 -p no:cacheprovider` passes; `grep -Eic "claude|anthropic" $WT/dash.sthlp` prints 0.]]></verify>
  <done>The help described the drawn axis look, the refusals and the by() exceptions as twoway has them.</done>
</task>

<task type="auto" id="31-13">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[Close the `P1.18a` entry in place (`- [x]`, the Resolution of "Notes / BUGS.md Resolution", naming tests that exist); delete its `WP30_OPEN` key line; replace `<!-- WP-30 P1.18a -->` in "Results that change" and in "Changed behaviour" with the lines of "Notes / CHANGELOG", each ending `(WP-30, P1.18a)`. Run every changed test file and the three cscripts through the driver, then `git -C $WT merge --no-edit main` (expect `Already up to date.`; otherwise stop and report without committing, E9), then one full run in the background `<scratch>/full_suite_queue.sh $WT <scratch>/31-full-1.log` and wait for its `exit=` line (E1, E6). Check G6 (`git -C $WT diff --cached --name-status` holds only this section's files), write the message to `$S/msg.txt` (failure text, defect, changes, `Regression:`, `Flipped:` lines from `$S/31-flips.txt`, `Fixture: test/fixtures/axis_subopt_truth.json (scripts/extract_axis_subopt_truth.do)`, `BUGS.md: "<title>" (closed)`), run G7 before and after, confirm the branch prints `wp30-s31`, and commit once.]]></action>
  <verify><![CDATA[`grep "exit=" <scratch>/31-full-1.log` prints `exit=0` and the log reports 0 failed; `python3 -m pytest $WT/test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes; `grep -c "WP-30 P1.18a -->" $WT/CHANGELOG.md` prints 0; `grep -c '^    "P1.18a": "' $WT/test/test_tracking_documents.py` prints 0; `git -C $WT log -1 --format=%s` ends with `(WP-30 P1.18a)`; `git -C $WT log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.18a was closed, its markers replaced, the full suite was green, and the section's one commit was made on wp30-s31.</done>
</task>

## Section completion criteria

- One commit on `wp30-s31`, subject ending `(WP-30 P1.18a)`, made after a green full run (`exit=0`), its body opening with `<scratch>/31-P1.18a-failure.txt`.
- AC-31.1 to AC-31.6 hold; `test_axis_suboptions.py`, the three area cscripts and the S31 truth block pass with no SKIP.
- BUGS.md `P1.18a` closed in place; its `WP30_OPEN` key gone; no `<!-- WP-30 P1.18a -->` left; `test_tracking_documents.py` green.
- The fixture is committed with `_meta` and read by tests; the copy-list guards, both maps and `_needed` are green.
- No file outside this section's `<files>` lists is in the commit (G6).

## Notes

**Traps.**
- **Int geometry.** `major_tick_in/out`, `minor_tick_*`, `major_label_standoff` and `axis_label_standoff` are Bokeh `Int`: always pass `_dash_tick_geometry`'s ints or `int(round(…))`.
- **Order inside the appliers.** nolabels after S08's labsize (it must win); the tick look after S15's scheme (apply_to_axis runs first in both modes); the scale look after the label loop in `_dash_apply_axis_options`, since `alt` reassigns the side lists (iterate over a copy).
- **The snapshot.** Read `_dash_scheme_look`, never the current major props, for the tick-only copy: the label look has already run (E4).
- **No call-site edits.** `_make_figure_body` and `_generate_app_source` are not edited (R12): the scale look is reached through `_dash_apply_axis_options` and `_dash_finish_secondary_axes`, which both modes already call with `graph_opts`. If a test shows a mode where these do not run, stop and report.
- **The look is read by `_dash_scale_look`, never by a second `_dash_scale_spec` call.** `_dash_scale_spec` names and parses `range()` once, at figure creation; a second call would re-run `_parse_scale_range` under the option `scale` and print a second, mislabelled range note (`test_a_bad_range_is_noted_once`).
- **zscale** shares `_dash_scale_spec`: its honoured set stays `_DASH_SCALE_SUBOPTS`, so `zscale(alt)` stays named (`test_colorvar_forms.py:319-320`).
- **Merged values.** twoway checks bounds on the merged option (E9 Q1/Q2), so the bound loop runs on `g_<opt>` after S10's merge, never per segment; a capitalised word is a parse error and `_dash_axreq_check` (earlier in `_dash_plot`) refuses it first, as twoway does.
- **`nodraw`.** twoway checks the bounds only when it draws; dash always builds the page, so it refuses under `nodraw` too (CHANGELOG says so).
- **Renderer-only specs.** A hand-written spec never reaches Stata: there `angle(400)` is an unknown angle (note, 0), `OFF` is named.

**R10.** No count pin moves. `_SINGLE_Y_BASELINE_SHA256` is expected unchanged (the snapshot and colour context are underscore attributes, never serialised, and every new write is gated on a given option); if it moves, the commit message says why and the merger re-derives it.

**Merge rules touched.** R1 (AXL block contiguous after SR-09 in `test_suboption_reporting.cscript`; own truth block), R2 (anchors of TR-31.12; maps under the S31 anchors), R3 (dash.sthlp: Axis and Display Options, two sentences of Differences and Unsupported; S32 edits the Unsupported pending list in the same batch, landing after S31), R4 (two markers), R5 (own entry and key), R6 (two Mata functions, `_needed`, header index; `_dash_plot` after the rule loop), R7 (new extractor in S02's form, `git add -f`), R8 (CORPUS appended; two `_MUST_WARN` rows this fix silences), R9 (E11 flips), R12 (no call-site edit).

**R2.** The index's R2 row lists S31 as in-place only; this section adds one constant and six functions (TR-31.12) at `"_DASH_SCALE2_SUBOPTS",` and `"_dash_apply_axis_options",`, anchors no other section uses (checked against the R2 table). The merger records the addition in `<scratch>/batch-11-merge.log`; `test_every_listed_name_exists` guards it.

**Commit body line forms.**
- `Regression: test/test_axis_suboptions.py::TestAngleStyles::test_each_anglestyle_name -- failed at <batch-11-base sha> with <text>` (one per class's first red node), and `Regression: test/test_suboption_reporting.cscript AXL-01 -- failed at <sha> with rc 0`.
- `Flipped: <node> -- <old expectation> was wrong because <why>` (from `$S/31-flips.txt`).
- `Fixture: test/fixtures/axis_subopt_truth.json (scripts/extract_axis_subopt_truth.do)`.
- `BUGS.md: "The axis look sub-options nolabels, noticks, off, noline, line colour, width and pattern, alt, titlegap, labcolor, tlength and tposition are not honoured, and anglestyle names are dropped silently" (closed)`.

**BUGS.md Resolution** (one line, in place):
`  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.18a). xlabel(), ylabel(), xtick(), ytick() and their second-axis forms draw nolabels, noticks, labcolor(), tlength() and tposition() (_dash_parse_axis_spec, _dash_apply_axis_spec, _dash_tick_look, _dash_apply_tick_option, from the scheme's tick geometry recorded by SchemeParser.apply_to_axis), and angle() reads every anglestyle name and twoway's h, v, rh and rv, a wrong-case or unknown name noted and drawn at 0 (_parse_axis_angle); xscale(), yscale(), xscale2() and yscale2() draw off, noline, lcolor(), lwidth(), lpattern(), alt and titlegap() (_dash_scale_spec, _dash_apply_scale_look, _dash_axis_alternate), in the saved page and the served app alike, before and after a filter move; under by() off, nolabels, noticks and titlegap() are drawn as if absent with no note, as twoway draws them. dash.ado refuses angle() outside -360 to 360 and a scale lwidth() outside 0 to 10000 on the merged option in twoway's words and order (_dash_axbound_list), and the xscale() and yscale() words twoway refuses (_dash_axreq_add). Pinned by test/test_axis_suboptions.py::TestAngleStyles::test_each_anglestyle_name, test/test_axis_suboptions.py::TestLabelColourAndTicks::test_tlength_in_stata_units, test/test_axis_suboptions.py::TestTickOnlyStyleIsSeparate::test_a_tick_option_has_its_own_look, test/test_axis_suboptions.py::TestScaleLook::test_alt_moves_the_axis, test/test_axis_suboptions.py::TestUnderBy::test_twoways_subset, test/test_suboption_reporting.cscript AXL-01, test/test_wp30_truth.cscript AXL-20; fixture test/fixtures/axis_subopt_truth.json. Residual, deferred (WP-30): two copies of yscale(alt) toggle the axis back in twoway and draw one alt in dash; the default gap between tick labels and the axis title is not read from the scheme; zlabel() and zscale() look words are named on the colour key; xtick()'s labcolor(), labels and nolabels are named; a comma inside a quoted axis colour is drawn black with a note where twoway refuses it; xscale() and yscale() fill, outergap(), extend and the axis lstyle() stay named.`

**CHANGELOG** (in place of the two markers):
- Results that change: `- xlabel(), ylabel(), xtick(), ytick() and their second-axis forms draw nolabels, noticks (labels and ticks win within one option), labcolor() with %# opacity, tlength() in Stata's size units and tposition(); xscale(), yscale() and their second-axis forms draw off, noline, the axis line's lcolor(), lwidth() and lpattern(), alt and titlegap(). Each was named in a "not implemented" note and not drawn. dash scatter mpg weight, ylabel(, angle(rvertical)) drew the labels at the scheme's own angle and now draws them at 270 degrees; every anglestyle name and twoway's h, v, rh and rv are read. ylabel(, angle(Vertical)) drew 90 degrees and is now noted and drawn at 0, also over a scheme's vertical labels. Under by(), xscale(off), yscale(off), nolabels, noticks and titlegap() are drawn as if absent, with no note, as twoway draws them. (WP-30, P1.18a)`
- Changed behaviour: `- angle() outside -360 to 360 in xlabel(), ylabel(), xtick(), ytick(), xmlabel(), ymlabel(), xmtick(), ymtick() and their axis(2) forms is refused, r(198), with twoway's message textangle must be between -360.000 and 360.000; it was drawn. dash refuses it under nodraw too, where twoway checks it only when the graph is drawn. (WP-30, P1.18a)`, `- An xscale() or yscale() lwidth() below 0 or above 10000 is refused, r(198), with twoway's message gm_linewidth must be between 0.000 and 1.0e+04. (WP-30, P1.18a)`, `- An xscale() or yscale() sub-option twoway refuses, such as yscale(OFF), yscale(Alt), xscale(bogus) or a word given twice in one option, is refused, r(198), with twoway's message (option OFF not allowed); it was named in a note and drawn. (WP-30, P1.18a)`

**Notes for the closeout (S58; A145).**
- GAPS2 Tracked lines: **B23** Closed in WP-30, BUGS.md "<P1.18a title>", commit <sha> (B23 carries P1.18a only), with the line's own words "fill, outergap(), extend/noextend/fextend and the axis lstyle()/style() stay named; residual R-S31-7" (GAPS2 B23 itself says "Closable: partly" for fill and extend). **D9** Closed in WP-30 likewise (D9-a; D9-b, `angle(Vertical)` accepted, is closed by the same commit). **B21**: "Partly closed in WP-30 (S10 P1.19 and S31 P1.18a): abbreviations, nolabels, noticks, labcolor, tlength and tposition are drawn; open: add (S52), labgap, label and tick styles, grid styles, gmin/gmax, custom and alternate (P2.20)."
- REMAINING.md: REM-09-02-NOLABELS-NOTICKS, -SCALE-OFF, -SCALE-LINE, -SCALE-TITLEGAP, -LABEL-ANGLE, -LABEL-LABCOLOR, -LABEL-TICKGEOM closed by S31; the :2447 scale bullet closed; the :2459 label bullet keeps `alternate`, `custom` (P2.20) and `add` (S52).
- TWOWAY_COVERAGE_AUDIT.md:137 (AUDIT-28): tag "[WP-30 P1.18a, commit <sha>: corrected -- xscale(alt)/yscale(alt) and the axis look sub-options are drawn]".
- DROPIN-REMAINING.md P1.18: part a closed by S31, part b by S52; P2.20's "`angle(Vertical)` is accepted" bullet struck.
- New P2 residuals: R-S31-1 two copies of `yscale(alt)` toggle twice in twoway (back to the default side), dash's merge keeps one; R-S31-2 the scheme's `gsize axis_title_gap` (s2color .3472, stcolor 1.3888 rs) is not read, so the default title gap and `titlegap(*#)` start from Bokeh's 5 px; R-S31-3 `zlabel()`/`zscale()` look words are named on the colour key; R-S31-4 `xtick()`'s `labcolor()`, `labels`, `nolabels` are named; R-S31-5 `ylabel(, labcolor("255,0,0"))`: twoway "invalid '0'" r(198), dash draws black with a note (the same filing as S30's D-30f for a comma inside a structured option's colour, so the closeout files one P2 residual for both); R-S31-6 whether `mlabangle()` takes twoway's `h`, `v`, `rh`, `rv` is unmeasured; R-S31-7 `xscale()`/`yscale()` `fill`, `outergap()`, `extend`/`noextend`/`fextend`/`nofextend` and the axis `lstyle()`/`style()` stay named (no Bokeh counterpart for fill and extend; the axis line style is P2.20's).
- For S52: `add` must respect `show_labels`/`show_ticks` from this spec, and S52's own fixture is its own extractor's (R7: this extractor is never run by another section).
