# Section 37: The region remainder

> Part of: WP-31 · GAPS3 rows: D11 · Risk: yellow · Batch: 12 · Depends on: 01 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U37

## Overview

**What is wrong today.** GAPS3 D11 (GAPS3.md:161): "Region: `graphregion(margin())` not exact; graphregion `i*` options, `intensity() iintensity() shadestyle() ishadestyle() marginonly` named; margin forms `L+10`, three- and five-value, `allsides-ms` not parsed; s1color's unfilled plot region filled white." Evidence dash_render.py:6504-6710 (`_dash_region_spec`, `_dash_apply_regions`). Register rows P2.53 (graphregion margin and i* options), P2.76 (intensity and shading), P2.80 (margin forms; "`margin(allsides-ms)`, r(7) in twoway, drawn as its style file says"), P2.92 (s1color's unfilled plot region).

Measured at `6370ca4` (read from the code; re-measured by 37-01):
- `_dash_region_spec`'s docstring (:6518-6524) lists what it names: "`lalign()`, `ilalign()`, `ishadestyle()`, `iintensity()`, `shadestyle()`, `intensity()`, `marginonly`; for `graphregion` also `margin()` and the inner-box options". `_dash_apply_regions` (:6641) draws `graphregion()` as `border_fill_color` and `plotregion()` as `background_fill_color`/`outline_line_*` (:6698-6705) and reports the named list once per region (:6706-6707).
- `_dash_margin_sides` (:29108) already reads the four forms its docstring names: a style name, numbers ("measured: `1 2 3` keeps the top, a fifth number is the left again"), `{l|r|b|t}{+|-|=}#` terms, and "anything else -- `L+10`, `l5` ... gives zeros and *noted*" -- so the 3-, 5-value and `L+10` claims of D11 are closed for `plotregion(margin())` already; what is open is (a) `graphregion(margin())` is never drawn, (b) `allsides-ms` is drawn from its style file where twoway fails r(7), and (c) the margin's conversion for the graph region (relative to the graph's min(W, H), not the plot region's).
- `SchemeParser` reads `color plotregion` (:10192, default `#ffffff`) and never `shadestyle plotregion`; Stata's `scheme-s1color.scheme` sets `shadestyle plotregion none` (research/stata-ground-truth.md §11 lists the stub as absent from dash's scheme copies), so dash fills s1color's plot region white where twoway leaves it unfilled (the graph background shows through).
- `intensity()` on a region is a fill intensity; dash has the intensity machinery for `fintensity()` (the `_INTENSITY` ladder and the fill mixer the fill appliers call) and does not apply it to regions.

**After this section**, both renderers: `graphregion(margin())` is drawn exactly, in every marginstyle form, as `min_border_left/right/top/bottom` added to the figure (relative units of the graph's min(W, H)); `margin(allsides-ms)` and the other style names twoway fails on are refused with twoway's rc and line (measured); `intensity()` on `plotregion()`/`graphregion()` mixes the fill as `fintensity()` mixes a bar's; `shadestyle(none)` draws no fill and the other shadestyle words follow the measurement; the scheme's `shadestyle plotregion none` is honoured (s1color, s1mono, s1rcolor, s1manual, stmono1 draw an unfilled plot region); `iintensity()`, `ishadestyle()`, the graphregion `i*` options and `marginonly` are measured and either drawn where Bokeh has the property or documented as a difference with the measured example (D-37.b, M17). Options drawn print nothing (Q36).

**Test order and commit rule (rule 7, M6).** One row, one commit `(WP-31 D11)`. 37-01 writes the extractor, fixture, `test/test_region_remainder.py` and the U37 cases, runs them red, saves `<scratch>/37-01-failure.txt`; 37-02 draws; 37-03 flips, help, BUGS, GAPS3, CHANGELOG, commit.

### Section decisions (this file; binding on the executor)

- **D-37.a `graphregion(margin())` is `min_border_*`.** The four sides from `_dash_margin_sides(text, start)` with *start* the scheme's `margin graph` sides (s2color: the executor reads the stub `margin graph` from `/Applications/StataNow/ado/base/s/scheme-s2color.scheme`, converted by `SchemeParser.margin_sides`), in relative units; px = side / 100 x min(`width`, `height`) at build (Bokeh 3 has no `width`/`height`), added to each `min_border_*` (never assigned: S32 and S33 also add to them); a figure without `margin()` is left untouched (DECISIONS A18: the function returns before touching any border, so `min_border_* is None` -- Bokeh's inherit-from-`min_border` state -- survives). Bokeh has no outer margin model besides `min_border`; the axis labels sit inside it, as inside twoway's graphregion margin. The conversion uses the figure's `width`/`height` at build; a resize keeps the px (documented).
- **D-37.b Inner-region options follow Bokeh's reach.** The graph region's inner box (`istyle() icolor() ifcolor() ilcolor() ilwidth() ilpattern() ilstyle() ilalign()`) is the area inside the graphregion margin and outside the plot region; Bokeh paints one `border_fill_color` over margin and inner box alike and draws no box there. `ifcolor()`/`icolor()` are drawn as the border fill (the margin takes the same colour, a documented difference measured by `inner.ifcolor`); `ilcolor()/ilwidth()/ilpattern()/ilstyle()/istyle()` are not drawable (`border_line_*` outlines the whole canvas, which is `lcolor()`'s) and stay named with the help's measured example. `iintensity()` applies to the same fill as `intensity()` when `ifcolor()` is drawn; `ishadestyle(none)` clears it. `marginonly` (fill the margin, not the inner box) is not drawable and stays named. The D11 Resolution records these as the residual under M17 (documented difference), not as open work.
- **D-37.c `intensity()` mixes toward white as `fintensity()` does.** The same mixer (`OptionTranslator` intensity helper the fill appliers use; the executor finds it by `grep -n "fintensity" dash_render.py` and reads the function `_apply_fill_opts`/`_apply_area_opts` call) is applied to the region's resolved fill after `color()`/`fcolor()` and before `%NN`; `*#` forms and the named ladder (`inten0`..`inten100`, `full`) through the existing reader. The scheme stubs `intensity background`/`foreground` already read (stata-ground-truth.md §11) are the defaults.
- **D-37.d `shadestyle()` words.** `none` -> fill None; `pattern10`/`pattern#` and other names are measured (`shade.*`); where twoway draws a solid fill for them dash draws the fill and is silent; a name twoway refuses is refused with its line. `SchemeParser.plotregion_shade` reads `shadestyle plotregion` from the scheme files (a word, no colour space; M7 untouched); `none` -> `pbase["fill"] = None` in `_dash_apply_regions` (the existing blend path: :6680-6700 already maps a None plot fill to `gfill`, the graph fill, which is twoway's "unfilled" picture; today's defect is only that `pbase["fill"] = sch.plotregion_color` (#ffffff) is never None), unless `plotregion(color()/fcolor())` names one; no second `background_fill_color = None` branch. The shipped `dash-s1color.scheme` and the other s1* copies gain the stub line THROUGH THE GENERATOR (scripts/extract_scheme_truth.py: truth entry `plotregion_shade` and directive `scalar("shadestyle", "plotregion", "plotregion_shade")`; run twice; `git add -f test/fixtures/scheme_truth.json`; REVIEW-3 R3-08 -- the files are generator output and a hand edit is erased at the next run; S44 owns style *files*, not the shipped scheme copies' stubs).
- **D-37.e `allsides-ms` is refused as twoway refuses it.** The fixture records rc and the first line for `margin(allsides-ms)` and for every `margin-*.style` name whose twoway run fails (the executor lists `/Applications/StataNow/ado/base/style/margin-*.style`); dash.ado's region check (`_dash_subopt_check region`, :6978, through Mata `_dash_subreq_check("region")`) refuses exactly those names with the measured rc and line. Names twoway draws stay drawn through `SchemeParser.margin_sides`.

## Risk: [yellow] -- every figure's border and fill pass through the two region functions

**Why.** `_dash_apply_regions` and `_dash_region_spec` run on every figure in both modes; the scheme reader change affects five shipped schemes' plot regions.

**Risk factors.**
1. s1-family schemes change look: the plot region becomes transparent (twoway's picture).
2. `min_border_*` is written by S32 (batch 11, sizing), S33 (batch 11, outergap) and S37; order of addition does not matter, assignment would.
3. Pinned tests: test_region_options.py, test_region_truth.py, test_region_margins.py, test_scheme_*.py nodes asserting the white plot region under s1color, the named list and `min_border` values.
4. The intensity mixer's exact arithmetic must match twoway's (already pinned for `fintensity()`; regions reuse it).
5. Batch partners: S36 passes by()'s region copies into `_dash_apply_regions` and adds `mult=None` to `_dash_plot_margin`; S37 must keep both signatures.

**Mitigation.**
1. `region_remainder_truth.json` records s1color's SVG (no plot-region rect fill) and `TestShade::test_s1color_unfilled` pins it in both modes.
2. `+=` only; `TestGraphMargin::test_adds_not_assigns` builds with a preset `min_border_left` and checks the sum.
3. Flips in place with the reason (R9).
4. `TestIntensity::test_same_mixer_as_fintensity` compares a region fill with a bar's fill under the same `intensity(inten50)`.
5. `_dash_apply_regions(fig, graph_opts, scheme, seen=None, key="")` keeps its signature; `_dash_plot_margin` is read, not edited, by S37 (the graph margin is a new function `_dash_graph_margin`).

## Dependencies

- **Depends on: 01.** **Blocks:** none.
- **Parallel batch: 12**, merge order 35, 36, 37. **Can run with S35 and S36:** S35 edits the secondary axes and the finishers; S36 the by() appliers, `_FILTER_JS`, `_build_filter_widgets`, the template and `_make_figure_body`. S37 edits `_dash_region_spec`, `_dash_apply_regions`, a new `_dash_graph_margin`, `SchemeParser` (two accessors), dash_parse.mata's `_dash_subreq_check` region kind and the shipped scheme copies' stubs. No shared function.

## Evidence

All anchors at `6370ca4`; re-read before editing.

### The region reader

```python
6504 def _dash_region_spec(raw, option, base, scheme=None, ref_in=4.0):
6518     *named* lists, as typed through ``_dash_display``, the sub-options
6519     twoway accepts and dash does not draw (``lalign()``, ``ilalign()``,
6520     ``ishadestyle()``, ``iintensity()``, ``shadestyle()``,
6521     ``intensity()``, ``marginonly``; for ``graphregion`` also ``margin()``
6522     and the inner-box options, which plotregion draws elsewhere since
6523     WP-30 P1.20b) and any word with no region name: ten, then
```

The `elsewhere` set at :6534-6538 names `margin istyle icolor ifcolor ilstyle ilcolor ilwidth ilpattern ilalign` for plotregion ("drawn elsewhere (_dash_plot_margin, _dash_inner_box)"), and for graphregion the same names fall to *named*.

### The applier

```python
6641 def _dash_apply_regions(fig, graph_opts, scheme, seen=None, key=""):
6670     raw_g = str(go.get("graphregion") or "")
6671     g, named_g = _dash_region_spec(raw_g, "graphregion", {
6672         "fill": sch.background_color, "fill_alpha": 1.0,
6673         "line": sch.background_color, "line_alpha": 1.0,
6698     fig.background_fill_color = (
6702     fig.outline_line_color = p["line"]
6706     _dash_report_suboptions("graphregion", named_g, seen, key)
6707     _dash_report_suboptions("plotregion", named_p, seen, key)
```

### The margin grammar

`_dash_margin_sides(text, start, scheme=None, short_in=4.0)` (:29108-29165): style names through `sch.margin_sides(t)`, numbers cycling over four sides, `[lrbt][+=-]#` terms, zeros and a note for anything else. `_dash_plot_margin` (:29168) applies it to the plot region's margin; `_dash_inner_box` (:29252) draws the plot region's inner box. Nothing applies it to `graphregion`.

### The scheme reader

```python
10192        self.plotregion_color: str = self._color("color plotregion", "#ffffff")
10482        # files carry it: `color plotregion_line' is white in s2color (on
```

`grep -c "shadestyle" dash_render.py` prints only the docstring mentions; no stub is read. Stata's `scheme-s1color.scheme` (read by the executor): `shadestyle plotregion none`; `scheme-s2color.scheme:801` `shadestyle plotregion` (a fill), `areastyle plotregion` :1494, `areastyle twoway_plotregion` :1496 (stata-ground-truth.md §11).

### Stata rules

- `region_options.sthlp` (`/Applications/StataNow/ado/base/r/region_options.sthlp`, read by the executor): `margin()` "the margin between the region and its containing region"; `i*` options style the inner region; `marginonly` "the fill color applies to the margin only"; `intensity()` the fill intensity; `shadestyle()` a shade style.
- `marginstyle.sthlp`: the 28 names; `allsides-ms` is not among the documented names (P2.80 measured r(7)).
- `_fr_area_parse_and_log.ado` (`/Applications/StataNow/ado/base/_/`): the parse order `style lstyle lcolor lwidth lpattern lalign color fcolor intensity shadestyle margin marginonly` then the `i*` set; `_DASH_BY_GRAMMAR`'s stage-3 comment (:26084) cites it.

### Fixtures on disk

`test/fixtures/region_truth.json` (WP-30 P1.20a), `margin_truth.json` (P1.20b). S37 adds `region_remainder_truth.json`.

### Tests that pin today's behaviour (flip in place, never delete)

- test/test_region_options.py -- nodes asserting `intensity()`, `shadestyle()`, `marginonly`, `margin()` on graphregion or an `i*` option is in *named*.
- test/test_region_truth.py::TestAgainstTwoway -- nodes comparing s1color's plot-region fill to white.
- test/test_region_margins.py -- nodes asserting `margin(allsides-ms)` draws from the style file.
- test_scheme_*.py nodes asserting `plotregion_color` is drawn under s1color/s1mono; test_help_claims_* nodes reading dash.sthlp:3471-3475.

The exact red list is measured by 37-01 into `<scratch>/37-flips.txt`.

## User stories

- **US-37.1** As a Stata user, I want `graphregion(margin(large))` and `graphregion(margin(l+5 r+5))` drawn so that my dashboard's outer spacing matches my graph.
- **US-37.2** As a Stata user, I want `plotregion(intensity(inten50))` and `plotregion(shadestyle(none))` drawn as twoway draws them.
- **US-37.3** As a user of s1color, I want the plot region unfilled, as twoway draws it.
- **US-37.4** As a Stata user who typed `margin(allsides-ms)`, I want dash to fail as twoway fails so that my do-file behaves the same under both.
- **US-37.5** As a Stata user, I want to know from the help which inner-region options Bokeh cannot draw and what dash draws instead.

## Business requirements

- **BR-37.1** `graphregion(margin())` in every marginstyle form changes the figure's outer spacing by twoway's amounts (within 1 px at the reference size) in both modes, silently.
- **BR-37.2** `intensity()` and `shadestyle()` on either region are drawn as the fixture says, silently.
- **BR-37.3** Schemes with `shadestyle plotregion none` draw an unfilled plot region in both modes.
- **BR-37.4** Style names twoway fails on are refused with twoway's rc and line.
- **BR-37.5** The inner-region options Bokeh cannot draw are named once and the help shows the measured difference.

## Technical requirements

Sub-option -> property map (`_dash_apply_regions`):

| Sub-option | Region | Bokeh property | Rule |
|---|---|---|---|
| `margin(marginstyle)` | graphregion | `fig.min_border_left/right/top/bottom` (added) | D-37.a through `_dash_graph_margin(fig, scheme, graph_opts)` |
| `intensity(#)` | both | the region's fill (`border_fill_color` / `background_fill_color`) | D-37.c mixer after colour, before alpha |
| `shadestyle(none)` | both | fill None | D-37.d; other words per fixture |
| `ifcolor()`, `icolor()` | graphregion | `border_fill_color` | D-37.b (documented: the margin takes the colour too) |
| `iintensity()` | graphregion | the same fill when `ifcolor()`/`icolor()` is drawn | D-37.b |
| `ishadestyle(none)` | graphregion | clears that fill | D-37.b |
| `istyle() ilstyle() ilcolor() ilwidth() ilpattern() ilalign()`, `marginonly`, `lalign()`, `ilalign()` | both | none | stay in *named*; help example |
| scheme `shadestyle plotregion none` | plotregion default | `pbase["fill"] = None` -> the existing blend to the graph fill | D-37.d |

- **TR-37.1** `_dash_graph_margin(fig, scheme, graph_opts)` new module function after `_dash_plot_margin` (:29250): reads every `graphregion()` copy's `margin()` through `_dash_margin_sides` over the scheme's `margin graph` sides, converts to px by `min(fig.plot_width, fig.plot_height) / 100` (or the figure's `width`/`height` when `plot_*` is None), adds to the four `min_border_*`; called from `_dash_apply_regions` after the graphregion fill is set. Copy list: after `"_dash_plot_margin",` in the functions tuple (grep the entry). `_dash_region_spec`'s graphregion branch stops naming `margin` (remove it from the graphregion *named* path).
- **TR-37.2** `_dash_region_spec` reads `intensity()` and `shadestyle()` into *settings* (`"intensity": <float or None>`, `"shade": "none"|<word>|None`) in twoway's parse order (after `fcolor`), and for graphregion `ifcolor()/icolor()/iintensity()/ishadestyle()` into `"ifill"`, `"iintensity"`, `"ishade"`; the *named* list drops them. `_dash_apply_regions` applies the mixer (D-37.c) and the shade rule (D-37.d) to both fills.
- **TR-37.3** `SchemeParser.plotregion_shade` (string, `_word("shadestyle plotregion", "")`) and `SchemeParser.graph_margin_sides` (the `margin graph` stub through `margin_sides`); `_dash_apply_regions` sets `pbase["fill"] = None` when `sch.plotregion_shade == "none"` and no `plotregion(color()/fcolor())` is given (the existing None-fill blend path at :6680-6700 then draws the graph fill); `plotregion(shadestyle(<fill word>))` restores the colour.
- **TR-37.4** Shipped scheme copies: `dash-s1color.scheme`, `dash-s1mono.scheme`, `dash-s1rcolor.scheme`, `dash-s1manual.scheme`, `dash-stmono1.scheme` (and any other whose Stata file holds the stub) gain `shadestyle plotregion none`; `dash-s2color.scheme` and the rest gain the stub as Stata's file has it -- all through scripts/extract_scheme_truth.py (the directive `scalar("shadestyle", "plotregion", "plotregion_shade")` beside the other shadestyle directives and the truth entry; run `scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json` twice; `git add -f`), never by hand (R3-08: hand edits are erased at the next generator run and never pinned by `scheme_truth.json`). The scheme-file tests (test_scheme_files*.py) that count stubs move their counts with `# old -> new: D11 shadestyle plotregion` (R10).
- **TR-37.5** Mata `_dash_subreq_check("region")` (dash_parse.mata :8206-8300 region) refuses the fixture's failing margin names with the measured rc and line (a data table `_DASH_MARGIN_REFUSED` of name -> (rc, line) written from the fixture into dash_parse.mata as a string matrix constant; the test `TestRefusals::test_table_equals_fixture` pins the two equal). dash.ado unchanged (the call at :6978 exists).
- **TR-37.6** Help (R3): Region Styling Options :3403-3511 -- the sentence at :3471-3475 ("`lalign()`, `ilalign()`, `ishadestyle()`, `iintensity()`, `shadestyle()`, `intensity()` and `marginonly` are accepted and named ... and so are `graphregion()`'s `margin()` and inner-box options, which are not drawn") is rewritten: `intensity()`, `shadestyle()`, `graphregion(margin())`, `ifcolor()`/`icolor()`, `iintensity()`, `ishadestyle()` are drawn; `istyle() ilstyle() ilcolor() ilwidth() ilpattern() ilalign() lalign() marginonly` are named, with the measured example (D-37.b: twoway's inner box line under `graphregion(ilcolor(red))` versus dash's unchanged border); a new sentence under Stata scheme support (:4520-4967) on `shadestyle plotregion none`. TWOWAY_COVERAGE_AUDIT.md :141 gains `graphregion(margin()) intensity() shadestyle()`.
- **TR-37.7** `test/function_test_map.py` entries for `_dash_graph_margin` and new `SchemeParser` accessors; parity `CORPUS` entries `"graphregion margin l+5"`, `"plotregion intensity inten50 shadestyle none"`, `"s1color plot region"` under `# WP-31 D11` (R8).

### Code and verbatim texts (copy, do not paraphrase)

**`_dash_graph_margin(fig, scheme, graph_opts)`** (after `_dash_plot_margin`):

```python
def _dash_graph_margin(fig, scheme, graph_opts):
    """graphregion(margin()) as additions to the figure's min_border_*
    (WP-31 D11, D-37.a): every copy's margin() over the scheme's `margin
    graph' sides, relative units of min(W, H) at build.  Adds, never
    assigns (S32's sizing and S33's outergap() share the borders)."""
    sch = scheme if scheme is not None else SchemeParser.fallback()
    start = list(getattr(sch, "graph_margin_sides", None) or [0.0] * 4)
    raw = str((graph_opts or {}).get("graphregion") or "")
    sides, noted = list(start), None
    for tok in _dash_by_tokens(raw.strip()):
        if _dash_subopt_canon(tok.split("(", 1)[0].strip(),
                              _DASH_REGION_SUBOPT_TABLE) == "margin" and "(" in tok:
            sides, noted = _dash_margin_sides(_dash_subopt_arg(tok), sides,
                                              scheme=sch,
                                              short_in=OptionTranslator.size_ref_of(fig))
    if noted:
        _dash_style_note("graphregion(margin)", noted, "margin", "zero")
    if sides == start:
        return  # no margin() given: every min_border_* stays as it was (A18)
    w = getattr(fig, "width", None) or 0
    h = getattr(fig, "height", None) or 0
    short = float(min(w, h)) if w and h else 0.0
    if short <= 0:
        return
    for name, i in (("min_border_left", 0), ("min_border_right", 1),
                    ("min_border_bottom", 2), ("min_border_top", 3)):
        add = (sides[i] - start[i]) / 100.0 * short
        if add == 0:
            continue  # an untouched side keeps None (inherits fig.min_border)
        cur = getattr(fig, name)
        if cur is None:
            cur = fig.min_border or 0  # Bokeh 3.8: min_border_* is None until set
        setattr(fig, name, int(round(cur + add)))
```

`_DASH_REGION_SUBOPT_TABLE` is the region table `_dash_region_spec` resolves with (the executor reads its name at :6504-6560; if the function resolves by a local table, name that one). Bokeh 3.8 `Plot().min_border_left is None` (it inherits `min_border`, 5): the three guards (`sides == start` return, `add == 0` continue, `fig.min_border` when the side is None) keep a figure without `margin()` -- and every untouched side -- at `None`; the earlier draft (`cur = getattr(fig, name) or 0`, no early return) turned the auto border into an explicit 0 on every figure in both modes (REVIEW-3b F17, DECISIONS A18). `TestGraphMargin::test_no_margin_leaves_borders_none` pins it.

**`SchemeParser` accessors** (after `default_marker_size`):

```python
    @property
    def plotregion_shade(self) -> str:
        """`shadestyle plotregion' as a word (WP-31 D11; none = unfilled)."""
        return str(self._raw.get("shadestyle plotregion", "") or "").strip().lower()

    @property
    def graph_margin_sides(self):
        """`margin graph' as [l, r, b, t] relative units (WP-31 D11)."""
        v = self._raw.get("margin graph", "")
        return self.margin_sides(str(v)) if v else [0.0] * 4
```

(`self._raw` is the parsed stub dict the other `_color`/`_word` readers use; the executor substitutes its name.)

**Mata table** (in dash_parse.mata beside `_dash_subreq_check`'s region kind):

```
// Margin style names twoway fails on (WP-31 D11, D-37.e): name, rc, line;
// equal to test/fixtures/region_remainder_truth.json refusals.* with rc != 0.
string matrix _dash_margin_refused_table()
{
    return(("allsides-ms", "7", "<fixture line>") \
           ("<name>", "<rc>", "<line>"))
}
```

**Help sentence** (Region Styling Options, replacing :3471-3475): `{cmd:intensity()}, {cmd:shadestyle()}, {cmd:graphregion(margin())}, {cmd:ifcolor()}, {cmd:icolor()}, {cmd:iintensity()} and {cmd:ishadestyle()} are drawn as {cmd:twoway} draws them ({cmd:shadestyle(none)} leaves the region unfilled).  {cmd:istyle()}, {cmd:ilstyle()}, {cmd:ilcolor()}, {cmd:ilwidth()}, {cmd:ilpattern()}, {cmd:ilalign()}, {cmd:lalign()} and {cmd:marginonly} are accepted and named in a note, once per region: {it:difference from twoway}, whose graph region has an inner box between its margin and the plot region that Bokeh does not draw -- {cmd:graphregion(ilcolor(red))} outlines that box in {cmd:twoway} and changes nothing in {cmd:dash}, and {cmd:graphregion(ifcolor(red))} fills the box in {cmd:twoway} and the whole border in {cmd:dash}.  A margin style name {cmd:twoway} fails on ({cmd:allsides-ms}) fails here with its return code and words.`

Stata scheme support (one sentence): `A scheme whose {cmd:shadestyle plotregion} is {cmd:none} (s1color, s1mono, s1rcolor, s1manual, stmono1) draws an unfilled plot region, as {cmd:twoway} does; {cmd:plotregion(fcolor())} fills it.`

**BUGS.md Resolution (D11):** `  - Resolution: Fixed <ddmonyyyy> (WP-31, D11). _dash_region_spec reads intensity(), shadestyle(), ifcolor(), icolor(), iintensity() and ishadestyle(); _dash_apply_regions draws them and calls _dash_graph_margin, which adds graphregion(margin()) in every marginstyle form to the figure's borders; SchemeParser.plotregion_shade honours shadestyle plotregion none, so the s1 family draws an unfilled plot region; _dash_subreq_check refuses the margin style names twoway fails on with its return code and words; in both renderers. Pinned by test/test_region_remainder.py::TestGraphMargin::test_form, test/test_region_remainder.py::TestShade::test_s1color_unfilled, test/test_wp31_truth.cscript U37-01, test/test_option_validation.cscript U37-04; fixture test/fixtures/region_remainder_truth.json. Residual, deferred (WP-31): istyle() ilstyle() ilcolor() ilwidth() ilpattern() ilalign() lalign() marginonly have no Bokeh property and are documented with the measured example (M17) (GAPS3 D11 Tracked). Closes GAPS3 D11 (WP-31, D11).`

**CHANGELOG lines (D11):**
- Results: `- Regions are drawn as twoway draws them. dash scatter mpg weight, scheme(s1color) filled the plot region white, now unfilled as twoway's shadestyle plotregion none says; graphregion(margin(large)) had no effect, now twoway's gaps (<the fixture's px at the reference size>); plotregion(intensity(inten50)) and shadestyle(none) were named and ignored, now drawn. (WP-31, D11)`
- Changed behaviour: `- plotregion(margin(allsides-ms)) and the other margin style names twoway fails on are refused with twoway's return code and words; dash drew them from the style file. (WP-31, D11)`

### Both-mode call sites (grep first; anchors drift)

| Change | Saved renderer | Served app | Finder |
|---|---|---|---|
| region spec and fills | `_dash_apply_regions` (module function, copied) called from `_make_figure_body` (:43782) | the same function, called at the emitted :49465-49467 lines | `grep -n "_dash_apply_regions(" dash_render.py` |
| graphregion margin | `_dash_graph_margin` called inside `_dash_apply_regions` | the same (copied with its entry) | `grep -n '"_dash_plot_margin",' dash_render.py` (the entry it follows) |
| scheme stubs | `SchemeParser` (class copied whole) | the same | none needed |
| margin refusals | dash.ado `_dash_subopt_check region` (:6978) -> Mata | n/a (refused before the spec is written) | `grep -n "_dash_subopt_check region" dash.ado` |

### The intensity mixer (D-37.c)

The executor finds it with `grep -n "fintensity" dash_render.py | head`; the function that turns a colour and an intensity into the drawn fill (the one `_apply_fill_opts` or `_apply_area_opts` calls, whose docstring names `inten0`..`inten100`) is called once per region as `fill = <mixer>(fill, settings["intensity"])` after the colour and before the alpha. If the mixer is a `GlyphMapper` method, lift it to a module function with a copy-list entry after `"_dash_graph_margin",` and have the method call it (one definition). `TestIntensity::test_same_mixer_as_fintensity` compares `plotregion(fcolor(navy) intensity(inten50))`'s `background_fill_color` with `bar ..., fcolor(navy) fintensity(inten50)`'s glyph fill.

### Measured red list procedure (37-01)

On a scratch copy of the worktree, change `_dash_region_spec`'s *named* list and the s1 default fill only, run `python3 -m pytest test/test_region_options.py test/test_region_truth.py test/test_region_margins.py test/test_scheme*.py test/test_help_claims_*.py -q -n0 -p no:cacheprovider -rf`, copy the failing node ids with their reasons into `<scratch>/37-flips.txt`, delete the copy.

### Stub-count pins (R10)

`grep -n "shadestyle\|stub_count\|len(stubs)" test/test_scheme_files*.py test/test_scheme_parser*.py` lists the tests that count scheme stubs; each declared count that grows by one gains the comment `# old -> new: D11 shadestyle plotregion`.

## Boundaries

- Not `_dash_plot_margin`'s body or `_dash_inner_box` (the plot region's own margin landed in WP-30 P1.20b; S36 adds `mult=None` to `_dash_plot_margin`).
- Not by()'s regions (S36 passes them in); not `_make_figure_body`, the template, `_FILTER_JS` (R12: S36's).
- No style-*file* reading (`areastyle-*.style`, `shadestyle-*.style`): S44. The scheme *stubs* are read as words.
- No colour spaces beyond RGB/RGBA (M7).

## Stata truth

**New extractor** `scripts/extract_region_remainder_truth.do` (path-free form of scripts/extract_by_grid_truth.do :1-45), run as `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s37/x $WT/scripts/extract_region_remainder_truth.do`, writing `test/fixtures/region_remainder_truth.json` (`git add -f`; `_meta` five keys). twoway only; `sysuse auto`; `set scheme s2color` unless named; each graph exported to SVG and read by `scripts/svg_truth.py`.

| Key | twoway command (`scatter mpg weight, ...`) | Recorded |
|---|---|---|
| `gmargin.<name>` for `zero small medium large vlarge sides tb l+5` and `1 2 3`, `1 2 3 4 5`, `L+10` | `graphregion(margin(<form>))` | plot-region box px and canvas px: the four outer gaps; any log line |
| `gmargin.stub` | `scatter mpg weight` | the `margin graph` stub text from the scheme file; the default four gaps |
| `refusals.<name>` for `allsides-ms` and every `margin-*.style` basename | `capture noisily twoway scatter mpg weight, plotregion(margin(<name>))` | rc, first error line |
| `intensity.<inten0,inten50,inten80,full,star05>` x `<plot,graph>` | `plotregion(intensity(inten50))` ... `graphregion(intensity(*.5))` | the region rect's fill colour |
| `shade.<none,pattern10,solid,bogus>` x `<plot,graph>` | `plotregion(shadestyle(none))` ... | fill present and colour; rc and line for `bogus` |
| `inner.<ifcolor,icolor,ilcolor,ilwidth,istyle_none,marginonly,iintensity,ishade_none>` | `graphregion(ifcolor(red))` ... `graphregion(fcolor(red) marginonly)` | the rects between canvas and plot box: their fills and strokes |
| `s1.<s1color,s1mono,s1rcolor,s1manual,stmono1,s2color>` | `scatter mpg weight, scheme(<s>)` | whether a plot-region rect has a fill; the `shadestyle plotregion` stub text |
| `s1.override` | `scheme(s1color) plotregion(fcolor(yellow))` | the plot-region fill |
| `s1.red_graph` | `scheme(s1color) graphregion(fcolor(red))` | the plot-region rect's fill (twoway: red shows through the unfilled plot region; dash today: white) -- the one row where filled and unfilled are distinguishable, since s1color's `color background white` and `color plotregion white` (scheme-s1color:18, :73) make the plain `s1.*` rows look alike |

**Truth block** (R1): `test/test_wp31_truth.cscript`, header `* ==== S37 D11: The region remainder ====`, helpers `_ur_*`, cases ending `_w31_done U37-0k`:
- **U37-01** `dash scatter mpg weight, graphregion(margin(large))`: each `min_border_*` grew by the fixture's gap minus the default gap, in px at the figure's size, saved and served; no `sub-option(s) not implemented` in the log.
- **U37-02** `plotregion(intensity(inten50)) graphregion(intensity(inten80))`: both fills equal the fixture's colours.
- **U37-03** `plotregion(shadestyle(none))`: `background_fill_color` is None; `scheme(s1color)`: None; `scheme(s1color) plotregion(fcolor(yellow))`: `#ffff00`; `scheme(s2color)`: the scheme colour.
- **U37-04** (test_option_validation.cscript, before `// Summary`) for every `refusals.<name>` with rc != 0: `capture dash scatter mpg weight, plotregion(margin(<name>))` rc and line equal twoway's in the same run; `margin(medium)` rc 0.
- **U37-05** `graphregion(ifcolor(red) ilcolor(blue))`: `border_fill_color` `#ff0000`; the log names `ilcolor(blue)` once and nothing else.

## TDD test stubs

### Regression tests, `test/test_region_remainder.py` (red at `6370ca4` unless marked guard)

Helpers: `_figs(mode, spec)` as test_region_options.py; the fixture once.
- Test: fixture `_meta` and keys -- `TestTheFixture::test_meta`, `::test_keys` (guard).
- Test: each `gmargin.<form>` adds the fixture's gaps to `min_border_*` within 1 px; `L+10` adds zero with the note twoway prints -- `TestGraphMargin::test_form[mode-form]` (red: unchanged borders), `::test_adds_not_assigns` (red).
- Test: `_dash_graph_margin` exists and is in the served copy list -- `::test_served_copy` (red).
- Test: a figure built without `graphregion(margin())` keeps `min_border_left/right/top/bottom is None` in both modes after `_dash_apply_regions`, and `margin(l+5)` alone leaves right/top/bottom None -- `TestGraphMargin::test_no_margin_leaves_borders_none[mode]`, `::test_one_side_leaves_the_others_none[mode]` (guard for the first at 6370ca4 -- the function does not exist yet -- red for the second; both must stay green after 37-02, A18).
- Test: `intensity()` on each region mixes as the fixture; equals a bar's `fintensity()` fill -- `TestIntensity::test_each[mode-region-level]`, `::test_same_mixer_as_fintensity` (red).
- Test: `shadestyle(none)` clears the fill; other words per fixture; `bogus` refused/noted per fixture -- `TestShade::test_none[mode-region]`, `::test_words[mode-word]` (red).
- Test: s1color/s1mono/s1rcolor/s1manual/stmono1 draw the plot region as the graph fill (the None-fill blend: `background_fill_color == border_fill_color`, and under `scheme(s1color) graphregion(fcolor(red))` the plot region is red, the fixture's `s1.red_graph`); s2color draws the colour; `plotregion(fcolor())` overrides -- `::test_s1color_unfilled[mode-scheme]`, `::test_red_graph_shows_through[mode]`, `::test_override[mode]` (red: white).
- Test: `SchemeParser.plotregion_shade` reads the stub from each shipped scheme as the fixture's `s1.*` stub text -- `::test_stub_read[scheme]` (red).
- Test: `ifcolor()/icolor()` fill the border; `iintensity()` mixes it; `ishadestyle(none)` clears; `ilcolor() ilwidth() istyle() marginonly lalign()` stay named once -- `TestInner::test_fill[mode]`, `::test_named[mode]` (red for the fill; guard for the named list once the list shrinks -- the assertion is the exact remaining list).
- Test: refused margin names equal the fixture's table in Mata -- `TestRefusals::test_table_equals_fixture` (red; reads dash_parse.mata).
- Test: nothing is printed for a drawn sub-option -- `TestSilentWhenHonoured::test_no_warning[mode-sub]` (red).

### Cases in cscripts
- `test_wp31_truth.cscript` U37-01, U37-02, U37-03, U37-05 (red); `test_option_validation.cscript` U37-04 (red for the refusals, guard for `medium`).

### Flips (in place, each with a `Flipped:` line)
From `<scratch>/37-flips.txt`; docstrings gain "twoway draws graphregion(margin()), intensity(), shadestyle() and an unfilled s1color plot region (WP-31 D11)".

### Parity corpus (R8; guards at base)
TR-37.7's entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| graphregion margin forms | pytest `TestGraphMargin`; U37-01 | `gmargin.*` | yes |
| intensity, shadestyle | pytest `TestIntensity`, `TestShade`; U37-02, U37-03 | `intensity.* shade.*` | yes |
| s1 schemes unfilled | pytest `TestShade::test_s1color_unfilled`; U37-03 | `s1.*` | yes |
| inner options | pytest `TestInner`; U37-05 | `inner.*` | yes |
| refusals | cscript U37-04; pytest `TestRefusals` | `refusals.*` | n/a |
| parity | `python3 -m pytest test/test_mode_parity.py -q -n0` | -- | yes |

**Acceptance criteria**
- **AC-37.1** Every `gmargin` form moves the borders by twoway's gaps within 1 px at the reference size, in both modes, silently.
- **AC-37.2** `intensity()` and `shadestyle()` fills equal the fixture's; the mixer equals `fintensity()`'s.
- **AC-37.3** The five s1-family schemes draw `background_fill_color None`; s2color unchanged; an explicit `fcolor()` wins.
- **AC-37.4** Every failing margin name in the fixture is refused by dash with twoway's rc and line.
- **AC-37.5** `ifcolor()/icolor()/iintensity()/ishadestyle()` drawn; exactly `istyle ilstyle ilcolor ilwidth ilpattern ilalign lalign marginonly` remain named, and the help shows the measured example.
- **AC-37.6** `WP31_ONLY=S37` prints U37-01, 02, 03, 05 PASS; test_option_validation.cscript prints U37-04 PASS and ALL CHECKS PASSED; no SKIP; one green commit `(WP-31 D11)`.

## Tasks

**Commit boundary.** Tasks 37-01 to 37-03 form the one D11 commit, subject `Draw graphregion margins, region intensity and shading, and honour an unfilled plot region (WP-31 D11)`, made by 37-03 on `wp31-s37` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s37`. Body per BRIEF: `<scratch>/37-01-failure.txt`, the measured defect, the change in both renderers, `Regression:`, `Flipped:` lines, `Fixture: test/fixtures/region_remainder_truth.json (scripts/extract_region_remainder_truth.do)`, `BUGS.md: "<title>" (closed)`, `GAPS3: D11 Tracked`.

<task type="auto" id="37-01">
  <name>Measure twoway and write the failing tests</name>
  <files>scripts/extract_region_remainder_truth.do, test/fixtures/region_remainder_truth.json, test/test_region_remainder.py</files>
  <action><![CDATA[
    Check `git -C $WT rev-parse HEAD` equals `<scratch>/batch-12-base.txt` and the branch is `wp31-s37`; `mkdir -p <scratch>/s37/x`. Create scripts/extract_region_remainder_truth.do by the "Stata truth" table (head from scripts/extract_by_grid_truth.do :1-45; the margin style names from `ls /Applications/StataNow/ado/base/style/margin-*.style`), run it through the slot, `git add -f test/fixtures/region_remainder_truth.json`, and write the branch values (which margin names fail and their lines; the shade words' fills; the inner options' rects; the s1 stubs) to `<scratch>/s37/measured.txt`. Create test/test_region_remainder.py with the classes of "TDD test stubs". Append the U37 block to test/test_wp31_truth.cscript above the marker line and U37-04 to test/test_option_validation.cscript before `// Summary`. Run `python3 -m pytest test/test_region_remainder.py -q -n0 -p no:cacheprovider -rf > <scratch>/s37/37-01.log 2>&1` and both cscripts through the driver (`WP31_ONLY=S37`); write `<scratch>/37-01-failure.txt`; list the pins a simulated fix turns red into `<scratch>/37-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/region_remainder_truth.json'));print(sorted(d['_meta']))"` prints `['born_date', 'dash_commit', 'extracted', 'source', 'stata_version']`; `grep -c FAILED <scratch>/s37/37-01.log` is at least 20 and none names `TestTheFixture`; `grep -c "U37-0[1-5] FAIL" <scratch>/s37/run_test_wp31_truth.log <scratch>/s37/run_test_option_validation.log` totals 5; no SKIP; `test -s <scratch>/37-01-failure.txt`.]]></verify>
  <done>twoway's graphregion margins, region intensities and shades, inner-region rects, s1 stubs and margin refusals were recorded in a stamped fixture, and every regression test was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="37-02">
  <name>Draw the regions and read the shade stub</name>
  <files>dash_render.py, dash_parse.mata, scripts/extract_scheme_truth.py</files>
  <action><![CDATA[
    In dash_render.py: `_dash_region_spec` (:6504) reads `intensity() shadestyle()` and the graphregion `ifcolor() icolor() iintensity() ishadestyle()` into *settings* in twoway's order and drops them and `margin` (graphregion) from *named* (TR-37.2); add `_dash_graph_margin` after `_dash_plot_margin` (:29250; D-37.a) and call it from `_dash_apply_regions` (:6641) after the graphregion fill, adding to `min_border_*`; apply the intensity mixer (D-37.c; the function `fintensity()` uses, found by `grep -n fintensity dash_render.py`) and the shade rule (D-37.d) to both fills; `SchemeParser.plotregion_shade` and `graph_margin_sides` (TR-37.3) and `pbase["fill"] = None` under a `none` shade (the existing blend path; no new branch). `_dash_graph_margin` carries A18's three guards (verbatim code above) and `TestGraphMargin::test_no_margin_leaves_borders_none` stays green. Copy-list entry `"_dash_graph_margin",` after `"_dash_plot_margin",`. Add the `shadestyle plotregion` truth entry and directive to scripts/extract_scheme_truth.py, run it twice with `--out test/fixtures/scheme_truth.json`, `git add -f` the fixture and the regenerated `dash-*.scheme` (TR-37.4; never a hand edit), moving any stub-count pins with `# old -> new: D11` comments. In dash_parse.mata `_dash_subreq_check`'s region kind, add the `_DASH_MARGIN_REFUSED` table from the fixture's `refusals` with rc != 0 and refuse those names with their lines (TR-37.5). Add function_test_map entries. Run `python3 -m pytest test/test_region_remainder.py test/test_region_options.py test/test_region_truth.py test/test_region_margins.py test/test_statistical_helpers.py -q -p no:cacheprovider -k "not Silent"` (the flips come in 37-03).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_region_remainder.py -q -n0 -p no:cacheprovider` reports 0 failed; `grep -c "shadestyle plotregion none" dash-s1color.scheme` prints 1 and `grep -c plotregion_shade scripts/extract_scheme_truth.py` is at least 2 and `git status --porcelain dash-*.scheme test/fixtures/scheme_truth.json` is empty after a second generator run; `grep -c '"_dash_graph_margin",' dash_render.py` prints 1; `python3 -c "import dash_render as d; from bokeh.plotting import figure; f=figure(width=300,height=200); d._dash_graph_margin(f, None, {}); print(f.min_border_left, f.min_border_top)"` prints `None None`; `python3 -c "import dash_render as d; print('margin' in d._dash_region_spec('margin(large)', 'graphregion', {'fill': '#fff', 'fill_alpha': 1, 'line': '#fff', 'line_alpha': 1, 'line_width': 1, 'line_dash': 'solid'})[1])"` prints False.]]></verify>
  <done>graphregion margins, region intensity and shading, the inner fill words and the scheme's unfilled plot region were drawn in both renderers, and the failing margin names were refused in twoway's words.</done>
</task>

<task type="auto" id="37-03">
  <name>Flip pins, update help and commit D11</name>
  <files>dash.sthlp, BUGS.md, CHANGELOG.md</files>
  <action><![CDATA[
    Flip every node of `<scratch>/37-flips.txt` in place with the reason (R9); append TR-37.7's parity entries under `# WP-31 D11: the region remainder`. Help (R3, TR-37.6): rewrite dash.sthlp :3471-3475 and add the measured inner-box example and the `shadestyle plotregion none` sentence under Stata scheme support; TWOWAY_COVERAGE_AUDIT.md :141. Close the D11 BUGS.md entry (Resolution naming `_dash_region_spec`, `_dash_apply_regions`, `_dash_graph_margin`, `SchemeParser.plotregion_shade`, `_dash_subreq_check`, both renderers; `Residual, deferred (WP-31): istyle() ilstyle() ilcolor() ilwidth() ilpattern() ilalign() lalign() marginonly have no Bokeh property and are documented with the measured example (M17) (GAPS3 D11 Tracked)`), rewrite the D11 Tracked line to `- **D11 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (the documented difference is named in the BUGS Resolution; the merger's step k.3b writes the sha, DECISIONS A11), replace the `<!-- WP-31 D11 -->` markers (Results: `scheme(s1color)` drew a white plot region, now unfilled; `graphregion(margin(large))` had no effect, now twoway's gaps; Changed behaviour: `margin(allsides-ms)` and the other failing names are refused with twoway's rc and words). Run `python3 -m pytest test/test_region_remainder.py test/test_region_options.py test/test_region_truth.py test/test_region_margins.py test/test_mode_parity.py test/test_help_conformance.py test/test_tracking_documents.py test/test_statistical_helpers.py -q -p no:cacheprovider` plus the files `<scratch>/37-flips.txt` names, and both cscripts through the driver. Stage dash_render.py dash_parse.mata the dash-*.scheme files dash.sthlp TWOWAY_COVERAGE_AUDIT.md BUGS.md CHANGELOG.md GAPS3.md scripts/extract_region_remainder_truth.do test/test_region_remainder.py test/test_wp31_truth.cscript test/test_option_validation.cscript test/test_mode_parity.py test/function_test_map.py and the flipped files; `git add -f test/fixtures/region_remainder_truth.json`; commit; grep the message for `claude|anthropic` before and after.
  ]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; the driver logs show `U37-01 PASS`, `U37-02 PASS`, `U37-03 PASS`, `U37-05 PASS`, `U37-04 PASS` and `ALL CHECKS PASSED`, no SKIP; `git log -1 --format=%s` ends `(WP-31 D11)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 D11 -->' CHANGELOG.md` prints 0; `grep -c "and so are {cmd:graphregion()}'s {cmd:margin()}" dash.sthlp` prints 0.]]></verify>
  <done>D11 was closed in BUGS.md with its documented residual, its Tracked line rewritten, its markers replaced, the help described the drawn region options and the measured difference, and one green commit on wp31-s37 was ready for the merger.</done>
</task>

## Section completion criteria

- `graphregion(margin())` in every form, `intensity()`, `shadestyle()`, `ifcolor()/icolor()/iintensity()/ishadestyle()` drawn in both modes, silently; the s1 family's plot region unfilled; failing margin names refused with twoway's words.
- Exactly `istyle ilstyle ilcolor ilwidth ilpattern ilalign lalign marginonly` remain named, documented with the measured example.
- `region_remainder_truth.json` stamped and named; U37-01..U37-05 PASS; flips recorded; one green commit `(WP-31 D11)`; BUGS, GAPS3, CHANGELOG, help, audit, maps, corpus updated.

## Notes

- **`min_border_*` is shared.** S32 (sizing), S33 (`outergap()`) and S37 add to it; never assign. Batch 11 lands before batch 12, so S37 reads the S32/S33 values at its base.
- **Signatures S36 relies on.** `_dash_apply_regions(fig, graph_opts, scheme, seen=None, key="")` unchanged; `_dash_plot_margin` not edited here (S36 adds `mult=None`).
- **Scheme stubs are words.** `shadestyle plotregion none` is read as a word; no colour parsing is added (M7). The shipped copies are regenerated from Stata's files only for this one stub line; S44 (batch 15) owns the style tables.
- **Mixer reuse.** The intensity arithmetic is pinned for `fintensity()` already; `TestIntensity::test_same_mixer_as_fintensity` keeps the two identical. Do not write a second mixer.
- **python_exec hazard** (project memory) after each cscript run; a SKIP is not a pass.
- **Shared files.** R1: the U37 block, U37-04 in test_option_validation.cscript; R2: one function after `_dash_plot_margin`; R3: Region Styling Options and one sentence in Stata scheme support; R4: markers; R5: entry and Tracked line; R6: Mata table in `_dash_subreq_check` only; R7: one extractor; R8: corpus; R9: flips; R10: scheme stub-count pins moved with a comment; R12: no hot function.
- **Commit-body line forms** are BRIEF's; `failed at` is `batch-12-base.txt`'s sha.
- **For S56 (help reconciliation).** The inner-box example is S37's paragraph; S56 reads it, never rewrites it.
- **Decisions for maintainer ratification.** D-37.a (`min_border` as the graphregion margin, px fixed at build), D-37.b (inner-box options documented under M17, `ifcolor()` drawn as the border fill), D-37.d (scheme stub `shadestyle plotregion` read; shipped copies gain the line), D-37.e (failing margin names copied as refusals).
