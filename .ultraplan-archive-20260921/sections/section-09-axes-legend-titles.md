# Section 09: Axes, legend, titles and reference lines

## Overview
This is the largest cluster of silent failures in the package. Options that Stata's `syntax`
accepts — because they are declared `string asis` — arrive intact at Python and then have
their contents thrown away by parsers that recognise two or three keywords.

Measured: `xlabel(#10)`, `xlabel(minmax)`, `xlabel(1990(5)2020)` and
`ylabel(, format(%9.0fc))` are all **accepted** and all produce **zero ticks**.
`xlabel(none)` does the opposite of what it says.

And two defects are visibly corrupt rather than merely absent:
`title("My Title", size(large) color(red))` renders the literal text
`My Title , size(large) color(red)`, and `note("n=74", span)` renders `"n=74", span` — quotes
and all, because `note` is `string asis` while `title` is `string`.

## User story
> As a Stata user, my axis labels, legend, titles and reference lines look the way I asked,
> and nothing I typed appears as literal text inside my chart.

## Business requirements
- BR-09.1 Every `xlabel()`/`ylabel()` form Stata accepts produces the ticks Stata produces.
- BR-09.2 Sub-option text never leaks into rendered output.
- BR-09.3 `note()` and `caption()` are legible simultaneously.
- BR-09.4 Reference lines honour their style sub-options.

## Technical requirements — the register

| Line | Defect | Required |
|---|---|---|
| `:5548-5592` | `_parse_axis_label_opt` keeps only tokens `float()` accepts; `#N`, `minmax`, `none`, `1990(5)2020`, `format()`, `labsize()`, `grid` are all dropped | full `axis_label` grammar |
| `:203-213` | `_parse_scale_opt` knows only `log` and `reverse`; `range()`, `noextend`, `alt` dropped — while working range code sits at `:5799-5817` keyed on `xrange`/`yrange`, which `dash.ado` never emits | honour `range()`; delete or wire the dead keys |
| `:6006-6014` | legend `loc_map` has 6 keywords; `position(1..12)`, `order()`, `size()`, `region()` dropped | Stata's clock positions and ordering |
| `:6008` | `legend(off)` needs exact string equality, so `legend(pos(6) off)` leaves the legend visible | parse, don't string-compare |
| every glyph | `legend_label=yvar` always passed, so single-series plots get a legend `twoway` would not draw | match `twoway`'s rule |
| `:5866-5867` | `note()` and `caption()` both 11px `#555555` at screen `(0,0)` `"below"` — **they overlap** | distinct placement; sizes from the scheme |
| `:5878-5879` | subtitle 13px `#444444`, collides with the title | scheme-driven, non-colliding |
| `dash.ado` parse | title/note sub-options leak into the rendered string | strip and apply |
| `:5834-5853` | `xline`/`yline` float-cast tokens and discard `lcolor()`/`lpattern()`/`lwidth()` that `dash.ado` passes through intact; style forced grey dashed | honour the sub-options |
| `:4318-4353` | `if` with `!missing()`, `inlist()` or `< .` fails the AST whitelist, warns, renders **unfiltered** | support Stata's common functions |
| `:1441-1449` | marker border uses `options["lcolor"]` — the connecting-line colour — while `mlcolor()` is parsed and never read | `mlcolor()`, plus `mlwidth()` from S04 |
| `:1488-1521` | `_apply_fill_opts` reads only `fcolor`/`fintensity`; `falpha` never read | honour `falpha()` |
| `:386-387` | `"none": "#ffffff"` — `fcolor(none)` paints an **opaque white blob** | transparent / `fill_alpha=0` |
| `:1893-1899` | `mlabgap` uses `int(float(v))`, so `mlabgap(small)` throws and is silently dropped | route through `translate_msize()` |
| `:1591` | `colormissing` defaults to literal `"grey"` and is never passed through `translate_mcolor`, so `colormissing(eltblue)` emits invalid CSS | translate it |
| marker symbols | hollow markers (`Oh`, `Sh`, `Dh`) render **filled**; `msymbol(i)`/`none` silently draws visible markers | correct symbol mapping |

| `:7518-7519` vs `:6551`, `:6555` | dashboard title/subtitle are **HTML-escaped twice** in the Bootstrap path — `title("Price & Weight")` renders `Price &amp; Weight`; the non-Bootstrap path at `:7462-7476` escapes once and is correct | escape once |
| `:5638`, `:5610-5611` | graph titles and axis titles are `html.escape`d but drawn as **canvas text** — Bokeh's `Title` and axis labels are glyphs, not HTML, so `title("R&D spend")` displays as `R&amp;D spend`. Variable labels used as fallback axis titles (`_axis_label:5543-5545`) are **not** escaped and are correct | do not escape canvas text |
| `:6063`, `:4940` | the renderer reads a `hover()` option that **does not exist in `dash.ado` at all** | implement it or delete the dead reads |
| `:5729`, `:5764` | the secondary-axis range is computed from the **unfiltered** `self.df`, so a filtered dashboard's right-hand axis is wrong | compute from the active view |
| `:2014`, `:2030` | `map_line` sorts by x and drops non-x/y columns, then `_apply_mlabel_opts` is called with the **unsorted original** source — marker labels land on the wrong points | pass the sorted source |

Also here: the new options from S05 — `text()`, `xtick()`, `ytick()`, `xmtick()`, `ymtick()`,
`xmlabel()`, `ymlabel()`, and the `t1title`/`b1title`/`l1title`/`r1title` family.

## Risk: [yellow] — many independent changes, each small. The `if`-qualifier work touches a security-sensitive validator and needs care.

## Dependencies
- Depends on: S08
- Blocks: S10
- Parallel batch: 3

## TDD test stubs
- Test: `xlabel(#10)` produces about 10 ticks; `minmax` produces 2; `none` produces 0;
  `1990(5)2020` produces 7 at the right positions.
- Test: `ylabel(, format(%9.0fc))` renders thousands separators on the ticks.
- Test: `xlabel(, labsize(large))` changes tick label size; `angle()` still works.
- Test: `yscale(range(0 50))` sets the range; `noextend` and `alt` behave or are reported.
- Test: `legend(pos(6) off)` hides the legend; `legend(order(2 1))` reorders;
  `legend(position(3))` places right.
- Test: a single-series scatter draws no legend, matching `twoway`.
- Test: `title("T", size(large) color(red))` renders `T` — the sub-option text appears
  nowhere in the output — at the requested size and colour.
- Test: `note("n=74", span)` renders `n=74` with no quotes and no `span`.
- Test: `note()` and `caption()` together do not overlap.
- Test: `xline(3000, lcolor(red) lpattern(solid))` draws a red solid line.
- Test: `if !missing(rep78)`, `if inlist(rep78,1,2)` and `if rep78 < .` all filter correctly.
- Test: `mlcolor(red)` colours the marker border and does not change the connecting line.
- Test: `fcolor(none)` is transparent, not white.
- Test: `msymbol(Oh)` is hollow; `msymbol(none)` draws nothing.
- Test: `mlabgap(small)` is honoured; `colormissing(eltblue)` emits valid CSS.
- Test: `title("Price & Weight")` under `layout(bs)` renders `Price & Weight`, not `&amp;`.
- Test: a graph `title("R&D spend")` renders `R&D spend` on the canvas.
- Test: an apostrophe in a dashboard title survives both layout paths.
- Test: a filtered dual-axis graph's secondary range reflects the filtered rows.
- Test: `mlabel()` on a `line` plot labels the correct points.

## Tasks

<task type="auto" id="09-01">
  <name>Write the axis-label and scale conformance tests</name>
  <files>test/test_axis_options.py, test/test_axis_options.cscript</files>
  <action>
    Derive expected tick positions from Stata where Stata defines them — `#10` and `minmax`
    have specific behaviours — and record the commands used.

    Assert on the emitted ticker configuration, not on the presence of an axis. A test that
    only checks a figure was built will pass today for every one of these.

    Include `xlabel(none)`, which currently produces zero ticks *by accident* and must produce
    zero ticks *by intent* — the test should distinguish them by also asserting the ticker
    type.

    Run and confirm the failure shape: ticks absent or wrong, never an exception.
  </action>
  <verify>Every axis-label form fails with a tick mismatch, not an error.</verify>
  <done>A failing, position-asserting test exists for each axis-label and scale form.</done>
</task>

<task type="auto" id="09-02">
  <name>Implement the axis_label and axis_scale grammars</name>
  <files>dash_render.py</files>
  <action>
    Rewrite `_parse_axis_label_opt` (`:5548-5592`) to handle Stata's `axis_label` grammar:
    a numlist (including the `a(b)c` increment form), `#N`, `minmax`, `none`, explicit
    `value "label"` pairs, and the sub-options `format()`, `labsize()`, `angle()`, `grid`
    and `nogrid`. Keep the existing quoted-label handling, which works, and the existing
    `angle()` support (`:216-243`).

    Numeric tick labels must honour `format()` and, when none is given, the variable's Stata
    display format from S08.

    Extend `_parse_scale_opt` (`:203-213`) to honour `range()`. Working range code already
    exists at `:5799-5817` but is keyed on `xrange`/`yrange`, which `dash.ado` never emits —
    either wire `range()` to it or delete the dead keys. Do not leave both.

    Add `xtick()`, `ytick()`, `xmtick()`, `ymtick()`, `xmlabel()`, `ymlabel()` from S05.
  </action>
  <verify>All 09-01 tests pass; `angle()` and explicit label pairs still work.</verify>
  <done>Axis labelling accepts what `twoway` accepts and produces what `twoway` produces.</done>
</task>

<task type="auto" id="09-03">
  <name>Stop sub-option text leaking into titles, notes and captions</name>
  <files>dash.ado, dash_render.py</files>
  <action>
    The leak is a parsing defect on the Stata side, made inconsistent by the `string` vs
    `string asis` declarations: `title(...)` loses its quotes and keeps the sub-option text,
    `note(...)` keeps both.

    Parse the text and the sub-options apart, in Stata, using the same approach for both so
    they cannot diverge again. Serialize the text and the sub-options as separate keys.

    In Python, apply `size()`, `color()`, `position()` and `span` to the title, subtitle, note
    and caption. Take the defaults from the scheme rather than the current literals — 11px
    `#555555` at `:5866-5867` and 13px `#444444` at `:5878-5879`. The scheme keys exist and
    are parsed; S11 wires the general mechanism, so here take the values and leave a comment
    pointing at S11.

    Fix the overlap: `note()` and `caption()` are both a `Label` at screen `(0,0)` added
    `"below"`. Place them distinctly — Stata puts the note bottom-left and the caption below
    it. Fix the subtitle's collision with the title the same way.

    Add the `t1title`/`t2title`/`b1title`/`b2title`/`l1title`/`l2title`/`r1title`/`r2title`
    and `title2()`/`subtitle2()` options from S05, or report them if genuinely out of scope —
    decide explicitly and write the decision in the help.
  </action>
  <verify>No sub-option text appears in any rendered string; note and caption are both legible; sizes and colours are applied.</verify>
  <done>Titles render the text the user wrote, styled the way they asked.</done>
</task>

<task type="auto" id="09-04">
  <name>Legend: positions, ordering, and not drawing one when twoway would not</name>
  <files>dash_render.py</files>
  <action>
    Replace the 6-keyword `loc_map` (`:6006-6014`) with Stata's clock-position scheme, keeping
    the existing keywords as aliases. Honour `order()`, `size()`, `cols()`, `rows()`,
    `region()` and `ring()`.

    Fix `legend(off)` (`:6008`), which requires exact string equality — `legend(pos(6) off)`
    currently leaves the legend visible. Parse the option and look for the `off` token.

    Then the subtler one: every glyph passes `legend_label=yvar`, so a single-series plot gets
    a legend `twoway` would not draw. Match `twoway`'s rule — establish it by probing Stata
    rather than from memory, and record the probe. This changes existing output for
    single-series graphs; record it in the CHANGELOG.
  </action>
  <verify>Clock positions, ordering and `off` all work; a single-series plot matches `twoway`'s legend behaviour.</verify>
  <done>The legend does what the option says, and appears when `twoway` would show one.</done>
</task>

<task type="auto" id="09-05">
  <name>Reference lines, marker styling and fills</name>
  <files>dash_render.py</files>
  <action>
    `xline()`/`yline()` (`:5834-5853`): `dash.ado` passes the sub-options through intact and
    `_parse_refline` float-casts the tokens and discards them, forcing grey dashed. Parse
    `lcolor()`, `lpattern()`, `lwidth()` and apply them, defaulting from the scheme.

    Marker styling: wire `mlcolor()` to the marker border (`:1441-1449` currently uses
    `options["lcolor"]`, the connecting-line colour, which is wrong in both directions) and
    wire `mlwidth()` from S04. Fix hollow symbols (`Oh`, `Sh`, `Dh`), which render filled, and
    `msymbol(i)`/`none`, which silently draws visible markers.

    Fills: wire `falpha()`/`fa()` in `_apply_fill_opts` (`:1488-1521`) — it is used nine times
    in `examples/comprehensive_demo.do` and does nothing today. Fix `"none": "#ffffff"`
    (`:386-387`), which paints an opaque white blob where `fcolor(none)` should be
    transparent.

    Small ones in the same family: route `mlabgap` through `translate_msize()` (`:1893-1899`)
    so `mlabgap(small)` works instead of throwing and being dropped; pass `colormissing`
    through `translate_mcolor` (`:1591`) so `colormissing(eltblue)` emits valid CSS.
  </action>
  <verify>Reference lines take their style; `mlcolor`/`mlwidth` affect only the marker border; `fcolor(none)` is transparent; `falpha()` works.</verify>
  <done>Style options reach the property they name.</done>
</task>

<task type="auto" id="09-06">
  <name>Support Stata functions in if qualifiers, then commit</name>
  <files>dash_render.py, .ultraplan/CHANGELOG.md</files>
  <action>
    `_validate_if_expr` (`:4318-4353`) rejects any `Call` node, so `if !missing(rep78)`,
    `if inlist(rep78,1,2)` and `if rep78 < .` all fail validation, warn, and render
    **unfiltered**. These are the three most common qualifier forms in real Stata code.

    This validator replaced a regex blacklist with an AST whitelist in commit `700e770` to
    close an RCE. **Do not loosen the whitelist.** Add a translation layer *before* validation
    that rewrites a fixed set of Stata functions into whitelisted expressions:
    `missing(x)` → an isna comparison, `inlist(x,a,b,...)` → an explicit disjunction or an
    isin call added to the whitelist by name, `inrange(x,a,b)` → a bounded comparison, and
    Stata's `x < .` missing idiom → the corresponding notna test. Everything else stays
    rejected.

    Write adversarial tests for this specifically, per project rule 18: attempt injection
    through each newly-accepted function's arguments and confirm the whitelist still holds.

    Run all suites against the S01 baseline. Record the legend and title changes in the
    CHANGELOG. Commit as single-issue commits, one per defect cluster.
  </action>
  <verify>The three qualifier forms filter correctly; adversarial tests confirm the whitelist is not weakened; suites green.</verify>
  <done>Common Stata qualifiers work without reopening the RCE the whitelist closed.</done>
</task>

<task type="auto" id="09-07">
  <name>Fix HTML escaping, hover, the secondary-axis range and mlabel on lines</name>
  <files>dash_render.py</files>
  <action>
    Four defects that share this section's territory and would otherwise be orphaned.

    **Double escaping.** `render()` escapes the dashboard title and subtitle at `:7518-7519`,
    then `_render_bootstrap_html` escapes them again at `:6551` and `:6555`. Under
    `layout(bs)`, `title("Price & Weight")` renders `Price &amp; Weight` and an apostrophe
    renders `&#x27;`. The non-Bootstrap path (`:7462-7476`) escapes once and is correct.
    Escape once, in one place, and test both layouts.

    **Escaping canvas text.** `fig_kwargs["title"] = html.escape(...)` (`:5638`) and
    `x_label = html.escape(raw_xtitle)` (`:5610-5611`) escape strings that Bokeh draws as
    **canvas glyphs**, not HTML — so `title("R&D spend")` displays as `R&amp;D spend`.
    Remove the escaping on canvas text. Note that `_axis_label` (`:5543-5545`) does **not**
    escape variable labels used as fallback axis titles, and is already correct — which is the
    evidence that escaping here is the bug, not the protection. Confirm no XSS surface is
    opened: these values reach a canvas, not the DOM. Add an adversarial test asserting so,
    and keep escaping on everything that genuinely reaches HTML.

    **The phantom `hover()` option.** `:6063` and `:4940` read a `hover()` key that does not
    exist in `dash.ado`. Either implement it — the renderer clearly expects to control
    tooltip content — or delete the dead reads. Decide explicitly; leaving a dead read is how
    `xrange`/`yrange` (`:5799-5817`) misled the axis work in 09-02.

    **Secondary-axis range.** `_compute_secondary_range` is called with `self.df`
    (`:5729`, `:5764`), the unfiltered frame, so a filtered dual-axis graph's right-hand axis
    does not move. Compute it from the active view, and make the filter callback update it.

    **`mlabel()` on line plots.** `map_line` (`:2014`) sorts by x and drops non-x/y columns,
    then `_apply_mlabel_opts` is called at `:2030` with the **unsorted original** source, so
    labels attach to the wrong points. Pass the sorted source.
  </action>
  <verify>Ampersands and apostrophes render literally in both layout paths and on the canvas; the filtered secondary axis moves; line-plot marker labels land correctly; the `hover()` decision is implemented and documented.</verify>
  <done>No user-supplied text is mangled on its way to the screen, and no dead option read remains in the axis code.</done>
</task>
