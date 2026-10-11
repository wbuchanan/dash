# Section 10: axis(#) routing and by() shared scales

> Part of: WP-29 · P0: P0.5 then P0.2 · Risk: red · Batch: 2 · Depends on: 03, 05 · Blocks: 15 (closeout) · Tasks: 23, 2 commits (P0.5, then P0.2) · Case prefixes: AX, BSC

## Review amendments (binding; they override any conflicting text below)

Both designs this section carries were reviewed "sound with amendments". Every amendment is folded into the text below. This list is the index:

- **u05 (P0.5) A1** The axis number follows twoway's integer bounds. N is used only when it is finite, whole and within -2147483648..2147483647; anything else is axis 1. N is printed in an integer format, never by bare `strofreal`, which prints `1.00e+09`. → TR-10.2.
- **u05 A2** N comes from the FIRST lower-case axis word. For each option the order is: the double-comma test, then "does N exist", then the case and duplicate tests. → TR-10.3.
- **u05 A3** Refusals come in twoway's order: side, then family, then typed position, with every segment before the after-comma options. → TR-10.3, TR-10.4.
- **u05 A4** A second top-level comma, or any comma in a scale, is refused with `invalid '<word>'`, r(198). A trailing empty comma is accepted. → TR-10.3; SD-7.
- **u05 A5** twoway's plural spellings (`ylabels()`, `yticks()`, `ylines()`, `ymlabels()`, `ymticks()` and the x forms) are part of the family table. → TR-10.1; SD-6.
- **u05 A6** `test_option_validation.py::_DASH_ONLY` gains `ytick2` and `xtick2`. → task 10-09.
- **u05 A7** The declared counts in `test_unsupported_report_is_true.py` become 169 and 72, and LIVE_VALUES gains the four new options. → task 10-09.
- **u05 A8** `_dash_lone_second_axes` joins line copies; it no longer overwrites them. → TR-10.7.
- **u05 A9** The y2 tick extent leaves the primary range alone and honours norescale. → TR-10.8; tests.
- **u05 A10** `add` on a routed label is named on `ylabel2()`. → Boundaries; test.
- **u05 A11** The `_dash_axreq` external is cleared after the check, as well as at the start of the command. → TR-10.4.
- **u02 (P0.2) served note at build time** The range-not-applied note is decided by a pure helper and raised at build time (`ServerAppBuilder._plan_graph_notes`), never from a session. → TR-10.16. This section applies the same rule to P0.5's unused-second-axis note: index R6, PLAN K6.
- **u02 style() exact names** Only the exact names `style(rescale)` and `style(combine)` rescale. `style(resc)` does not. `compact style(rescale)` does. `style(rescale) nor` does not. → TR-10.13.
- **u02 Chrome in real time** The browser tests drive Chrome over the DevTools protocol in real time and never force a range update. They need a new `test/range_probe.py` and a served-page helper. → TR-10.21.
- **u02 100 panels** A Chrome test moves a slider on a 100-panel graph and checks how fast the ranges settle. → test stub; Risk.
- **u02 sharing stays inside one graph** Tested with two by() graphs, by() graphs in tabs(), and a link() group. → tests.
- **u02 rescale plus range() ticks** m07: `yrescale ylabel(#5) yscale(range(0))` ticks each panel over its own data, with no 0. → test.
- **u02 cross-unit dependency on P0.12a** S13 merges after this section in batch 2. Its token must leave `make_document(Document())` callable from the test helpers this section uses. → Dependencies, Notes.
- **u02 audit text** Hand `TWOWAY_COVERAGE_AUDIT.md:142` ("common scales" already in dash's column) to S15. → Notes for the closeout.

The section decisions SD-1 to SD-13 below settle every open question either design left. Every amendment above is applied in the text that follows.

## Overview

**P0.5.** twoway's `axis(#)` sub-option routes an option to the axis it names. dash applies it to the first axis. DROPIN-REMAINING.md P0.5 reads: "`yscale(log axis(2))` logs the primary axis, and the note names only `axis(2)`." Measured at HEAD in both modes (see Evidence):

- `ylabel(20 30, axis(2))` puts a FixedTicker [20, 30] on the LEFT axis.
- `yline(5000, axis(2))` draws `Span(5000, y_range_name='default')`.
- `ytitle("T", ax(2))` titles the left axis and names `ax(2)`.

dash.ado's repeat merge loses data too:

- `ylabel(10 20) ylabel(5000 10000, axis(2))` stores only `ylabel "5000 10000, axis(2)"`, so the first axis's labels are lost.
- An `axis(2)` that names an axis no layer uses is drawn on axis 1 with rc 0, where twoway refuses it with r(198).

After P0.5:

- `axis(2)` on `xtitle/ytitle`, `xlabel/ylabel`, `xtick/ytick`, `xline/yline` and `xscale/yscale` (twoway's spellings and abbreviations, plurals included) draws on the second axis in the saved page and the served app, before and after any filter move.
- `axis(1)` and an unqualified option stay on the first axis.
- Every form twoway refuses is refused with twoway's message and r(198), in twoway's order: an axis no layer uses, `AXIS()`, a repeated `axis()`, and a second comma.

**P0.2.** DROPIN-REMAINING.md P0.2 reads: "A plain `by(foreign)` autoranges each panel separately; axes are shared only when ticks or a range are given explicitly. `by(, yrescale)` is named in the note and ignored." twoway draws every panel of a by() graph on ONE scale per axis: x, y and the second axes, with the Total panel included. `yrescale`, `xrescale` and `rescale` (and their abbreviations and `style(rescale|combine)`) give each panel its own scale on that axis.

After P0.2, both modes share one Bokeh range object per non-rescaled axis across a graph's panels. The shared scale is the union of what every panel draws, and it stays the union after every filter move, because BokehJS unions the bounds of every plot that shares a DataRange1d (measured in Chrome in real time). A rescaled axis gets each panel's own autorange, `#N` ticks and hull. As in twoway, `range()` on a rescaled axis is not applied, and one note says so at build time in both modes.

**Why one section.** P0.2 must stop applying the `range()` values that P0.5 routes onto y2/x2 when that axis is rescaled. Both items edit `_dash_apply_scale_ranges`, `_dash_finish_secondary_axes` and the served template's figure builder. The architect's A2 broke the cycle: P0.5 lands first, then P0.2, in one worktree.

**Test order and commit rule (CLAUDE.md rule 7, index step 1).** The section runs two cycles on worktree branch `wp29-s10`:

1. **P0.5 cycle.** Tasks 10-01 to 10-03 extract the fixture, write every P0.5 regression test, run it against the batch-2 base and save the failure text to `<scratch>/10-P0.5-failure.txt`. Tasks 10-04 to 10-12 fix the code, flip the pins and certify. Task 10-13 closes the entry and makes the P0.5 commit, whose subject ends `(WP-29 P0.5)`.
2. **P0.2 cycle.** Tasks 10-14 to 10-16 repeat this on the tree the P0.5 commit leaves, saving `<scratch>/10-P0.2-failure.txt`. Tasks 10-17 to 10-22 fix, flip and certify. Task 10-23 makes the P0.2 commit, whose subject ends `(WP-29 P0.2)`.

No test-only commit exists and no commit is red.

## Risk: [red] — a parser change in Mata and Python that turns accepted commands into r(198), and a shared-range change that alters every by() graph's interaction

**Why.**
- P0.5 changes what dash.ado accepts. Several forms become r(198) to match twoway: commands that rc 0 today (`ylabel(…, axis(2))` with no axis-2 layer, `AXIS(2)`, a second comma, axis-1 options on a lone `yaxis(2)` graph).
- It also adds four keys that must travel through the two syntax blocks, two sreturn blocks, the seven graph-key lists in `dash.ado` and both renderers.
- P0.2 replaces every by() panel's own range with a shared object. That changes pan and zoom, and with them the parity profiles of every by() corpus entry.
- P0.2 relies on BokehJS behaviour (DataRange1d unioning `_plot_bounds` across plots) that no Python test can observe.

**Risk factors.**
1. Missing one of the seven graph-key lists drops `ytick2`/`yline2` at that stage, silently.
2. The order of refusals: twoway sorts by side, then family, then position. dash scans the after-comma options first (dash.ado:4641 runs before the segment loop at 4746).
3. Mata `_dash_rep_toks(sub, 1)` drops commas (`_dash_rep_toks("angle(0), axis(2)", 1)` gives `angle(0)` and `axis(2)`), so a double-comma form would be routed silently.
4. The order trap: creating the shared DataRange1d after `_dash_place_count_ticks(common=True)` loses the `#N` start and end.
5. A served note printed only in a session never reaches the Stata log (HC5-08). The parity guard cannot see this (`test_mode_parity._served` merges build and session warnings, test_mode_parity.py:233-252).
6. A shared DataRange1d with 100 panels makes each plot's `update_dataranges` loop over the union renderer list. One move is about 100 plots × (100 × layers) bound checks, plus 100 repaints.
7. BokehJS 3.9.0 `DataRange1d.update` returns early once `have_updated_interactively` is set (bokeh.js `update(bounds, dimension, plot, ratio) { if (this.have_updated_interactively) return; …`). After a user pans one panel, the shared range stops following filter moves on EVERY panel. Today the same happens per panel.
8. GitNexus has no index of this repository (`list_repos` lists only TYME and PhotoShootPlannerPro), so the impact analysis CLAUDE.md requires needs `gitnexus analyze` first.
9. S13 (P0.12a token) merges after this section and may gate `make_document`.

**Mitigation.**
1. `test_abbreviations.py::TestTheAxisRouteKnowsDashsSpellings::test_the_seven_graph_key_lists_agree` asserts that the lists are identical and hold the new keys.
2. `_dash_axreq_add` takes the segment number. The after-comma rows are numbered `n_segs + 1` and added after the loop. AX-04 replays twoway's measured orders.
3. The route and the scan detect the second comma with `_dash_rep_split` applied twice. AX-05 pins it.
4. `TestTheHelpers::test_share_by_scales_units` pins the order trap.
5. The two notes are decided by pure helpers at build time. BSC-10 reads the note in the Stata log after `dash build, server`, and `TestTheNoteReachesTheUser::test_served_build_raises_the_range_note` pins it in pytest.
6. `test_by_scales_chrome.py::test_hundred_panels_settle` bounds the settle time at 3 s. The measured number goes into the P0.2 commit body.
7. The help says panning or zooming one panel moves the others and stops the autorange for them all, as Bokeh does for any one panel today.
8. Tasks 10-01 and 10-14 run `gitnexus analyze` and `gitnexus_impact`.
9. The new served tests go through `test_mode_parity._served`, `test_dual_axis._lone_figure` and one new helper, `test_by_scales._served_doc`, which is the one place S13 must touch.

## Dependencies

- **Depends on: S03 (batch 1).**
  - u04 rewrites `_TEXTBOX_SUBOPT_RE`/`_textbox_split_point` and the empty-title rule.
  - u03 adds `var_labels=` to `conftest.make_data_json` (A7). This section's new tests pass `var_labels` explicitly wherever they assert title text.
  - S03 may also touch `_dash_route_axis2`/`_dash_route_axis_titles` (u04: `ytitle2` with no text). This section edits the S03 version of both and keeps its empty-text behaviour.
  - The "unlabelled variable + `ytitle(, size(large))`" case belongs to whichever section lands second (index "Why the dependencies"), which is this one: `TestTheTitleRouteKeepsTheDefault`.
- **Depends on: S05 (batch 1).** Dates are in Stata units, so the `%td` by() probe (c23) and the date-primary `yline(#, axis(2))` test compare in the variable's unit.
- **Blocks:** S15 (closeout) only.
- **Parallel batch:** 2. It can run with S11, S12 and S13. Merge order: S10, S11, S12, S13.
  - S11 also edits `dash.ado` option validation and `dash_parse.mata`. This section's `_dash_route_axis2` region is larger, so it merges first.
  - S13 (served token) merges last. It must keep `make_document(doc)` callable by `test_mode_parity._served`, `test_dual_axis._lone_figure` and `test_by_scales._served_doc`, or update those three helpers in its own commit.
- **Why P0.5 before P0.2 (A2).** u02 drops `range()` on a rescaled y2/x2. Those values only reach `yscale2`/`xscale2` once P0.5 routes `yscale(range(0) axis(2))` there.

## Evidence

Line numbers are HEAD `7421d3d`'s. Batch 1 shifts them, so locate everything by symbol.

### Blast radius (R8; grep-based, because GitNexus has no `dash` index)

`mcp gitnexus list_repos` at plan time returned only `TYME` and `PhotoShootPlannerPro`. Tasks 10-01 and 10-14 run `gitnexus analyze` and then `gitnexus_impact({target, direction: "upstream"})` for each symbol below. They record the output in `<scratch>/10-impact.txt` and report any HIGH or CRITICAL result to the orchestrator before editing. By grep at `7421d3d`:

| Symbol | Callers | Expected risk |
|---|---|---|
| `_dash_route_axis2` (Mata) | dash.ado:3922 (segment), 4641 (after comma) | MEDIUM |
| `_dash_rep_cat` (Mata) | dash_parse.mata:5033, 5150 | LOW |
| `_dash_route_axis_titles` | dash_render.py:25024 (saved loader), 28287 (builder) | LOW |
| `_dash_lone_second_axes` | dash_render.py:25025, 28288 | LOW |
| `_textbox_canon` / `_TEXTBOX_SUBOPTS` | 4 calls; every textbox | MEDIUM |
| `_dash_finish_secondary_axes` | 26317 (saved), served template 30620 | MEDIUM |
| `_dash_reference_lines` | 26107, served 30469 | LOW |
| `_dash_refline_draw` | 22941 only | LOW |
| `_dash_parse_by` | 7 sites: 1225, 21841 (`[1]` index), 25690, 27111, 28155, 29236, served string 30754 | MEDIUM |
| `_dash_apply_scale_ranges` | 26103, served 30464 | LOW |
| `_dash_hull_ranges` | 3 calls in `_dash_finish_count_ticks` / `_dash_common_count_ticks` | LOW |
| `_dash_common_count_ticks` | saved 27284, served 30843 | LOW |
| `DashRenderer._make_figure` / `_make_figure_body` | 27270, 27296 | HIGH expected (R8 lists `_make_figure_body`) |
| served `_dash_figure_for` | 4 calls in the template | MEDIUM |
| `ServerAppBuilder.build` / `_plan_by_groups` | 29175 | LOW |

### P0.5: twoway's rule (graph_g.class:1300-1422, `ParseAndLogAxes`)

```stata
local optnames  SCale	Labels	MLabels	TICks	MTicks	Title	LInes
foreach d in X T Y Z {
    ...
    local comma = cond(`optdex'==1, ",", "")
    syntax [ , `d'`opt'(string asis) * ]
    while `"``optnm''"' != `""' {
        if `optdex' == 6 { _parse comma unused opts : `optnm'
                           ._axisnum n : `opts' }
        else             { ._axisnum n : `comma'``optnm'' }
        if ! `:list n in `dl's' {
            di as error "`optnm'(``optnm'') not allowed, " "`dl'axis`n' does not exist"
            exit 198
        }
        ... _gs_parse_and_log_tickset / _axtitle / _axoptions / _lines ...
program _axisnum
    syntax [anything] [, AXis(integer 1) * ]
```

From this source:
- The minimum spellings are `xsc` (SCale), `xl` (Labels), `xml` (MLabels), `xtic` (TICks), `xmt` (MTicks), `xt` (Title) and `xli` (LInes).
- The full names are plural: `xlabels`, `xticks`, `xmlabels`, `xmticks`, `xlines`.
- The order is X before Y, then the family order SCale, Labels, MLabels, TICks, MTicks, Title, LInes.
- The axis word's minimum is `ax`.
- A scale is prefixed with a comma, so any top-level comma in it is a "second" comma.
- The refusal message names the family in its plural form, whatever the user typed (`ylabel(1, axis(4))` prints `ylabels(1, axis(4)) not allowed, yaxis4 does not exist`).

### P0.5: twoway, measured (StataNow 19.5; `sysuse auto`; B = `(scatter mpg weight) (line price weight, yaxis(2) sort)`)

Graph members were read as `.Graph.yaxis<k>.<major|majornl|minor|minornl>.dlg_tickpos[i]`, `.Graph.plotregion<j>.yscale.{curmin,curmax,transform.stylename,reverse.istrue}`, `.Graph.plotregion<j>.yaxis_dexes` and `.Graph.plotregion<j>._xylines[l].z`.

**Routing (rc 0):**

| Command | Result |
|---|---|
| `B, ylabel(5000 10000 15000, axis(2))` | yaxis2 major [5000 10000 15000]; yaxis1 stays [10 20 30 40] |
| `B, yscale(log axis(2))` | PR2 `ytr=log`, PR1 linear |
| `B, yline(5000, axis(2))` | the line is in `plotregion2._xylines` (z=5000) |
| `B, ytick(5000 7500, axis(2))` | yaxis2 majornl [5000 7500] |
| `ymlabel(…, axis(2))` / `ymtick(…, axis(2))` | yaxis2 minor / minornl |
| X = `(scatter mpg weight) (scatter mpg length, xaxis(2))` | `xlabel(150 200, axis(2))` gives xaxis2 [150 200]; `xscale log axis(2)` gives PR2 xtr=log; `xline(200, axis(2))` is in PR2; `xtick` gives xaxis2 majornl |

**Repeats:**

| Command | Result |
|---|---|
| `ylabel(10 20) ylabel(5000 10000, axis(2))` | y1 [10 20], y2 [5000 10000] |
| `ylabel(5000 10000, axis(2)) ylabel(6000, axis(2))` | y2 [6000] |
| `yline(5000 10000, axis(2)) yline(20)` | PR1 line 20; PR2 lines 5000 and 10000 |
| `yscale(log axis(2)) yscale(reverse)` | PR1 reversed, PR2 log |

**Extents:**

| Command | PR2 extent |
|---|---|
| `ylabel(20000, axis(2))` | [3291, 20000] |
| `ytick(20000, axis(2))` | [0, 20000] |
| `yline(30000, axis(2))` | [0, 15906]: lines never widen |
| `ylabel(5000 10000, axis(2) norescale) ytick(20000, axis(2) norescale)` | [3291, 15906], lists drawn |

**Spellings (rc 0):**
- `ax(2)` and `axi(2)` route for ylabel, ytic, yli, ysc, yml, ymt and ytitle.
- `axis( 2 )`, `axis(02)`, `axis(2.0)`, `axis(+2)`, `axis(2e0)` and `axis(1.0x+1)` give axis 2.
- `axis(a)`, `axis()`, `axis(2.5)`, `axis(1.5)`, `axis(2 1)`, `axis(#2)`, `axis(.)`, `axis(1e300)`, `axis(2147483648)`, `axis(-2147483649)` and `axis(-9999999999)` give axis 1, silently. An earlier `axis(2)` does not carry over.

**Plurals (rc 0 in twoway):**
- `ylabels(5000 10000, axis(2))` gives yaxis2 major [5000 10000].
- `yticks(5000, axis(2))` gives yaxis2 majornl [5000].
- `ylines(5000, axis(2))` gives PR2 L(z=5000).
- `ymticks(5000, axis(2))` gives yaxis2 minornl [5000].

dash prints `dash: ignoring unsupported option(s): ylabels()` and drops the whole option at rc 0.

**Refusals (r198), messages verbatim:**
```
ylabels(20 30, axis(2)) not allowed, yaxis2 does not exist        <- twoway scatter mpg weight, ylabel(20 30, axis(2))
ylabels(5000 10000) not allowed, yaxis1 does not exist            <- line price weight, yaxis(2) sort ylabel(5000 10000)
xscale(log axis(3)) not allowed, xaxis3 does not exist            <- B, ylabel(1, axis(3)) xscale(log axis(3))        [X before Y]
ylabels(1, axis(4)) not allowed, yaxis4 does not exist            <- B, yline(1, axis(3)) ylabel(1, axis(4))          [Labels before LInes]
ylabels(5000, axis(3) axis(1)) not allowed, yaxis3 does not exist <- B, ylabel(5000, axis(3) axis(1))                 [first axis word]
option axis() not allowed                                         <- B, ylabel(5000, axis(1) axis(3))
option AXIS() not allowed                                         <- B, ylabel(5000, AXIS(3)) ; ytitle(T, AXIS(2)) ; yscale(log AXIS(2)) ; yline(5000, AXIS(2))
option Axis() not allowed                                         <- B, ylabel(5000, Axis(2))
ylabels(5000, AXIS(2)) not allowed, yaxis1 does not exist         <- line price weight, yaxis(2) sort ylabel(5000, AXIS(2))
ylabels(5000, AXIS(2) axis(3)) not allowed, yaxis3 does not exist <- B, ylabel(5000, AXIS(2) axis(3))
yscale(axis(3)) not allowed, yaxis3 does not exist                <- B, ylabel(5000, axis(2)) yscale(axis(3))         [SCale first]
yscale(log axis(4)) not allowed, yaxis4 does not exist            <- (scatter mpg weight, ylabel(1, axis(3))) (line ..., yaxis(2) sort), yscale(log axis(4))
option AXIS() not allowed                                         <- B, ytitle(T, axis(3)) ylabel(1, AXIS(2))          [Labels before Title]
ylabels(1, axis(3)) not allowed, yaxis3 does not exist            <- (scatter mpg weight, ylabel(1, axis(3))) (line ..., yaxis(2) sort), ylabel(1, axis(4))   [segment before after-comma]
ylabels(1, axis(5)) not allowed, yaxis5 does not exist            <- scatter mpg weight || line price weight, yaxis(2) sort ylabel(1, axis(5)) || , ylabel(1, axis(4))
ylabels(5000, axis(2147483647)) not allowed, yaxis2147483647 does not exist
ylabels(5000, axis(-2147483648)) not allowed, yaxis-2147483648 does not exist
ylabels(5000, axis(1e9)) not allowed, yaxis1000000000 does not exist
ylabels(5000, axis(-0)) not allowed, yaxis0 does not exist
ylabels(5000, axis(1e1)) not allowed, yaxis10 does not exist
invalid 'axis'   <- yscale(log, axis(2)) ; ytitle(TT, size(small), axis(2)) ; yline(5000, lcolor(red), axis(2)) ; ylabel(5000, angle(0), axis(2)) ; ytick(20 30, grid, axis(1))
invalid 'color'  <- ytitle(TT, size(small), color(red))
invalid 'range'  <- yscale(log, range(1 50))
invalid 'log'    <- yscale(, log)
invalid 'lwidth' <- yline(20, lcolor(red), lwidth(thick))
too many options, r(1003), 0.06 s <- 10,000 copies of ylabel(1, axis(2))
```

Two forms are accepted, rc 0: `ytitle(TT, size(small),)`, and `ytick(5000, axis(2),)` (yaxis2 majornl [5000]).

When the offending value holds a double quote, twoway's own message breaks: `twoway scatter mpg weight, ytitle("T", axis(2))` prints `ytitle(unknown function T", axis()` with r(133).

`syntax [, YTICk(string asis) ytick2(string asis)]` binds `ytick2(5)` to ytick2 and `ytick(5)`/`ytic(5)` to ytick. A lower-case declaration binds only its full name.

### P0.5: dash today (both modes agree, both wrong)

Through `test/test_dual_axis.py::_lone_figure("saved"|"served", …)`:

| Spec on a dual-y graph | Drawn |
|---|---|
| `{"ylabel": "20 30, axis(2)"}` | left FixedTicker [20, 30]; right (y2) BasicTicker; warns `dash: ylabel() sub-option(s) not implemented and ignored: axis(2)` |
| `{"yscale": "log axis(2)"}` | left LogAxis, right LinearAxis; the same warning for yscale() |
| `{"yline": "5000, axis(2)"}` | `Span(location=5000, dimension='width', y_range_name='default')`; warning |
| `{"ytick": "5000 7500, axis(2)"}` | left CustomJSTicker `extra=[5000, 7500]`; right untouched; warning |
| x family with `axis(2)` | all on the bottom axis, with warnings |
| `{"ytitle": '"T", ax(2)'}` | LEFT axis titled `T`; warns `ytitle() sub-option(s) not implemented and ignored: ax(2)` (`_TEXTBOX_SUBOPTS` has `("axis", "axis")`, dash_render.py:2727; the Mata route tests the literal `axis(`, dash_parse.mata:4914-4916) |
| `{"ytitle": '"T", AXIS(2)'}` | ROUTED to y2 (dash_parse.mata:4911 lowercases), where twoway gives r(198) |
| single-axis graph + `{"ylabel": "20 30, axis(2)"}` | [20, 30] on the only axis with a note (twoway: r198) |

After a served filter move (foreign dropdown) with `ylabel "5000 10000, axis(2)"`, `yline "6000, axis(2)"` and `yscale "log axis(2)"`, the models are identical before and after: `[LogAxis default ticks [5000,10000], LinearAxis y2 [], Span(6000,'default')]`. `_on_filter_change` rewrites sources only. No saved-page JS touches axes or extra ranges.

dash.ado spec (`$dash_json_<name>`; every command rc 0):

| Command | Stored |
|---|---|
| `ylabel(10 20) ylabel(5000 10000, axis(2))` | `ylabel "5000 10000, axis(2)"` (axis-1 labels lost) |
| reverse order | `ylabel "10 20, axis(2)"` |
| `yscale(log axis(2)) yscale(reverse)` | `yscale "log axis(2) reverse"` |
| `yline(5000, axis(2)) yline(20)` | `yline "5000, axis(2), 20"` |
| `ylab(5000, ax(2))` | `ylabel "5000, ax(2)"` |

Only ytitle/xtitle are routed today (dash.ado:3922, 4641; dash_parse.mata:4893-4945). Mata `_dash_route_axis2("xt(V, axis(2))")` leaves it unrouted (its minimum is 3, twoway's is 2).

### P0.5: current code

`_dash_route_axis2`, dash_parse.mata:4893-4945 (title family only, minimum 3):
```mata
nm  = strlower(_dash_rep_optname(tok))
if (strlen(nm) >= 3 & strlen(nm) <= 6 & strpos(tok, "(") &
    (substr("ytitle", 1, strlen(nm)) == nm |
     substr("xtitle", 1, strlen(nm)) == nm)) {
    if (_dash_rep_split(_dash_rep_value(tok), body, sub)) {
        sub_w = _dash_rep_toks(sub, 1)
        ...
            if (arg == "1" | arg == "2") {
```

dash.ado also:
- declares `YTITLE2 … XSCALE2` and the folded synonyms `YLA2 …` (dash.ado:702-722, 940-960; folds at 744-750);
- has seven identical graph-key `foreach` lists (4090, 4624, 4656, 4746, 4800, 4831, 5086);
- has the rule table `xlabel2=axislist ylabel2=axislist` at 1949-1951.

`_dash_rep_cat` (dash_parse.mata:4378-4395) classes `xlabel2/ylabel2` as "L" and `xline/yline` as "X".

`_dash_lone_second_axes` (dash_render.py:1805-1863) moves `go[first+'2']` over `go[first]`:
```python
for first in _DASH_LONE_AXIS_OPTIONS[side]:
    second = go.pop(first + "2", None)
    if isinstance(second, str) and second.strip():
        go[first] = second
```

`_DASH_LONE_AXIS_OPTIONS` is `{"y": ("ytitle", "ylabel", "yscale"), "x": (...)}` (1743).

`_dash_refline_draw` (23003-23045) converts dates on the primary axis kind and builds `Span(location=v, dimension=dim, **kw)` with no range name.

`_dash_finish_secondary_axes` (20193-20301) reads `{n}scale2`, `{n}label2` and `_parse_scale_range(scale_raw, f"{n}scale2")` (its `want`), and returns early with `if spec is None: continue` when there is no label2.

### P0.2: twoway's rule

bygraph_g.class:268-269 declares `NORescale Rescale NOXRescale NOYRescale XRescale YRescale` and `STYLE(passthru)`. Lines :292-296 read: "if `style' == "" & `compact' != "" { local style style(compact) }". Lines :363-385:
```stata
if "`rescale'" != "" { local xrescale xrescale ; local yrescale yrescale }
else if "`norescale'" != "" { local noxrescale noxrescale ; local noyrescale noyrescale }
if "`xrescale'`noxrescale'" != "" { .`log'.Arrpush ._set_xor indiv_xrescale "`xrescale'" "`noxrescale'" ... }
```

`set_rescaled` (:1161-1200) resets the scales of a rescaled axis. On a shared axis it sets min/max to `axis_allrange` (:1393-1413), the min and max over every panel. Every shipped scheme sets `by_indiv_[xy]rescale no` (scheme-s2color.scheme:2208-2209). by_option.sthlp:250-273 documents the abbreviations.

### P0.2: twoway, measured

`sysuse auto`, members `.Graph.graphs[k].plotregion1.{y,x}scale.{min,max,curmin,curmax}`, `.{y,x}axis1.major.{min,max,delta}`, `.{y,x}axis1.draw_view.istrue`, `.yaxis2.plotregion.yscale.{min,max}` and `.subtitle.text[1]`.

**Shared by default:**

| id | command | per panel |
|---|---|---|
| c01 | `scatter mpg weight, by(foreign)` | both y [12,41] cur [10,41], x [1760,4840], ticks 10(10)40 / 2000(1000)5000; panel 2 yview 0 |
| c13 / c14 / c27 | `by(foreign, total)` / `by(rep78, missing)` / `by(foreign rep78)` | every panel, Total included, shares |
| c15 | `(scatter)(lfit), by(foreign)` | both y [10.7276, 41]: the fit is in the common scale |
| c16 / k07 | `(scatter mpg weight)(scatter price weight, yaxis(2)), by(foreign)` [`yscale(range(0) axis(2))`] | y2 [3291,15906] ticks 0(5000)15000 on both [k07: y2 [0,15906]] |
| c18, c22, c26, c25, d52, c23 | log, histogram, kdensity, bar, rarea, `%td` x | shared |
| d47 / d50 | `if price>6000` / `in 1/60` | the qualified rows only (d47 y [12,26] on both) |
| c33 | `by(foreign) yscale(range(0))` | both [0,41] |

**Rescale:**

| id | command | per panel |
|---|---|---|
| c02 | `by(foreign, yrescale)` | y [12,34] cur [10,40] / [14,41] cur [10,41]; x shared; yview 1 on both |
| c03 | `by(foreign, xrescale)` | x [1800,4840] / [1760,3420] (panel-2 ticks 1500(500)3500); y shared |
| c04, c05 `r`, c31 `resc`, k09 `re`, e08 `rescal` | rescale | both axes per panel |
| c06 `yr`, c32 `yresc`, e09 `yrescal`; c07 `xr` | | that axis per panel |
| c36 | `r(1)` | rows(1): shared |
| c08 / c29 | `norescale` / `noyrescale` | shared |
| c09 `rescale noyrescale`, c10 `yrescale noyrescale`, d53 `yrescale norescale`, d54 `norescale yrescale`, k11 `res noyr` | | y per panel (yes wins) |
| c11 `style(rescale)`, e02 `style(combine)` | | both per panel |
| e01 | `style(rescale) noyrescale` | x per panel, y shared |
| m06 | `style(rescale) nor` | both shared |
| m03 | `style(resc)` | both shared (exact style name) |
| m04 | `compact style(rescale)` | both per panel |
| c12 | `style(compact) yrescale` | y per panel |
| m01, m02 | two `style()` | r(198) |
| k03, e06, e07 | `YRESCALE`, `Yrescale` | r(198) |
| k16 | `rescale(1)` | r(198) |
| c38 | `total yrescale` | the Total panel gets its own [12,41] |
| k06 / c28 | `yrescale ylabel(#5)` | 10(5)35 / 15(5)40 |
| c30 | `rescale ylabel(#5) xlabel(#4)` | x 2000(1000)5000 / 1500(500)3500 |
| d19 / k02 | `yrescale yscale(range(0))` | [12,34] cur [10,40] / [14,41] cur [10,41]: range dropped |
| d44, d46, d49, d55, e10, e12, f01 | range() on a rescaled axis (y2 too; e12 y2 [3291,15906] / [3748,12990]; f01 single panel) | dropped |
| d40 / d41 | `yrescale xscale(range(0))` / `xrescale yscale(range(0))` | x [0,4840] / y [0,41]: kept on the non-rescaled axis |
| m07 | `yrescale ylabel(#5) yscale(range(0))` | 10(5)35 cur [10,35] / 15(5)40 cur [14,41]: no 0 |
| c20 / d48 | `yrescale ylabel(0(10)50)` / `ytick(0 60)` | cur [0,50] / [0,60] per panel: labels and ticks widen |
| e03 / e04 | reverse / log | kept per panel |
| c17 / f03 | `yrescale` with yaxis(2) / `xrescale` with xaxis(2) | y2 [3291,15906] ticks 0(5000)15000 / [3748,12990] ticks 4000(2000)14000; x2 per panel |

### P0.2: dash today

The by() parse, dash_render.py:17001-17141. `_DASH_BY_SUPPORTED` holds cols, missing and total only, so every rescale token is appended to `unsupported`:
```python
name = tok.split("(", 1)[0].strip().lower()
...
else:
    unsupported.append(tok)
```

The saved panel loop (27239-27286) calls `self._make_figure(g_panel, src, facet_view=panel_view_r)`, then `_dash_common_count_ticks([...])`. The served template does the same (30754-30845, `_dash_figure_for(_g_pan, _fname, _gdf, _fac_label=_label)`, then `_dash_common_count_ticks([...])`). `_dash_common_count_ticks` (20758-20809) re-ticks `#N` and builds a common HULL only where some panel has explicit values. It calls `_dash_hull_ranges(f, es, common=…)` per figure, which makes one Range1d per figure. `_dash_limit_ranges_to_primary` (20812) sets each panel's own DataRange1d `renderers`.

Measured with the `_auto_like` frame (Domestic mpg 12-34, weight 1800-4840; Foreign mpg 14-41, weight 1760-3420):

| Case | Both modes |
|---|---|
| `by(foreign)` | every panel has a DISTINCT DataRange1d on x and y (ids differ), each with `renderers` length 1 |
| `by(foreign, yrescale)` | the same models, plus `dash: by() sub-option(s) not implemented and ignored: yrescale` (`r` and `norescale` named the same) |
| `yrescale ylabel(#5)` | both panels ticked 10,20,30,40, y start 10 / end 42.45 (twoway: 10(5)35 and 15(5)40) |
| `yrescale xrescale xlabel(#3)` | x 2000..5000 on both (twoway panel 2: 2000(1000)4000) |
| `yrescale yscale(range(0))` | one common Range1d, -2.05..43.05, on both (twoway: no 0) |
| y2 under by() | per-panel Range1d 2660.25-16536.75 and 3285.9-13452.1 (twoway: one [3291,15906]) |

In the browser (BokehJS 3.9.0, headless Chrome):

- The saved page `by(foreign)` draws Domestic x [1648,4992] y [10.9,35.1] and Foreign x [1677,3503] y [12.65,42.35]. The served document (make_document, then file_html) is identical.
- Driven in real time over the DevTools protocol with no forced update, after a price RangeSlider moves to 3291-7075.5: Domestic y [11.711,18.079], Foreign y [13.574,22.953].
- Prototype with ONE DataRange1d per axis whose renderers are the union of the panels' renderers: initial y [10.55,42.45], x [1606,4994] on both panels (the union [12,41] / [1760,4840] padded 5% a side). Within 1 s of the same move, real time, unforced: y [11.474,23.053], x [1718,2642] on both. For histogram panels (`renderers` [] on both), one DataRange1d gives y -0.002..0.048, then -0.008..0.159 after the move, on both.

> **Truth dispute resolved (u02 review).** The design's "11.47/23.05 with no JS" figure was a FORCED reading. Its probe called `pv._range_manager.update_dataranges()`, and its unforced reading under `--virtual-time-budget --dump-dom` stayed at 10.55-42.45 with `invalidate_dataranges` true. The reviewer's real-time CDP driver confirmed the claim unforced, as quoted above. This is why the Chrome tests use a real-time driver (TR-10.21). `test/responsive_probe.py:171-175` (virtual time, `--dump-dom`) cannot observe a repaint after a move, and no `_served_page` helper exists anywhere in `test/`.

BokehJS 3.9.0 (`bokeh/server/static/js/bokeh.js`), `DataRange1d.computed_renderers()`: `compute_renderers(renderers.length == 0 ? "auto" : renderers, [...all_renderers])` over `this.linked_plots`. `update()` stores `_plot_bounds.set(plot, total_bounds)` and takes `_compute_min_max(this._plot_bounds.entries(), dimension)`, the union over every plot that shares the range. Python `DataRange1d().renderers` defaults to `[]`, which means "auto".

### Tests that pin today's behaviour (flip, never delete)

- `test/test_suboption_warnings.py::TestAnUnimplementedSuboptionIsNamed::test_once_in_both_modes[yline axis]` (SUBOPTIONS entry at :75-76: `{"yline": "20 25, lpattern(dash) axis(2)"}` names `axis(2)`). Flip the entry to `axis(3)`, which is still named. Add a routed case with a `yaxis(2)` layer to `TestTheHonouredOnesStayQuiet`.
- `test/test_server_facets.py::TestAnUnimplementedBySuboptionIsNamed::test_each_unimplemented_sub_option_is_named[foreign, norescale noixlabel]` (:512) becomes `["noixlabel"]`. `test_by_scales.py::TestTheRescaleSubOptions::test_rescale_tokens_are_not_named` asserts that norescale is absent.
- `test/test_unsupported_report_is_true.py::TestEveryDeclaredOptionIsClassified::test_the_syntax_blocks_were_actually_found` (:592-593, `== 165` / `== 68`) becomes 169 / 72. `::test_every_declared_option_is_classified` gains LIVE_VALUES for `ytick2`, `xtick2`, `yline2` and `xline2` (A7).
- `test/test_option_validation.py::_DASH_ONLY` (:1279-1284) gains `ytick2` and `xtick2` (A6). Without them `test_every_twoway_option_in_the_table_was_probed` (:1313-1320) fails on the new rule-table entries.
- `test/test_textbox_grammar.py`: the `TestTheFixtureIsPinned` docstring and the "Boundaries: recorded, not pinned" note for `t_axis3`/`t_axis2_no_layer` change in comment only (now pinned as refusals by AX-03).
- `test/test_natscale_axes.py` module docstring :13-15 ("dash does not implement yrescale … its panels take the common scale") is text only and is rewritten.
- Parity profiles: the `_axes.rng` `renderers` count of every by() CORPUS entry moves from 1 to the panel union, in BOTH modes together. Nothing is flipped, but expect the numbers to move.
- dash.sthlp :2501-2503 ("`by(, yrescale)` is not implemented"), :2549-2553 ("still named, not read"; "refuses all twelve"), :1780-1783 (the implemented by() list) and :2556-2562 (the lone axis accepts axis-1 options). No test pins this wording (grep of `test/` for each phrase finds none). The help-conformance checks see the new declarations (`test_help_conformance.py::TestEveryDashOnlyOptionIsDocumented`).
- `test/test_function_test_map.py` fails until the new functions are mapped. `test/test_program_coverage_map.py` fails until the new Mata functions are mapped.

## Section decisions (the designs' open questions, settled here)

| Id | Question | Decision | Why / alternative |
|---|---|---|---|
| SD-1 | axis-1 options on a graph whose every layer is on `yaxis(2)` (c33, c35, c36: twoway r198 `yaxis1 does not exist`) | REFUSE, r(198), twoway's message. It falls out of the general check, because the layer axis set is {2} | twoway parity. The alternative keeps the documented leniency (dash.sthlp:2556-2562). Changed behaviour: a CHANGELOG line. No cscript passes axis-1 options on a lone yaxis(2) graph (grep: OV-31 has none; JSE-46k uses `xtitle2`). Hand-made specs keep `_dash_lone_second_axes`. |
| SD-2 | Quoted value with no axis: twoway r(133) with a broken message | dash r(198) with an intact message. Tests assert twoway rc != 0 and dash rc == 198 | twoway's 133 is its own message bug |
| SD-3 | dash's own `ytitle2()`/`ylabel2()`/… typed with no axis-2 layer | Accepted. The renderer names them once, at build time in both modes (`_dash_unused_second_axis_notes`) | JSE-46k (`xtitle2` with no `xaxis(2)`) keeps passing |
| SD-4 | Upper- or mixed-case `AXIS(2)` | Refused, `option AXIS() not allowed` (the word as typed), in A2's order | twoway parity. Today the title route accepts it |
| SD-5 | `ymlabel()`/`ymtick()` with `axis(2)` | Validated by the axis check, not routed and not drawn. The pending note stays | Drawing minor labels is P1. Handed to S15 |
| SD-6 | Plural spellings (A5) | IMPLEMENTED in the route: the exact plural word is renamed to dash's singular before `syntax`, with or without an axis word | twoway accepts them; dash drops them unnamed today; it costs one table column |
| SD-7 | Double comma (A4) | Refused, `invalid '<word>'`, r(198), for every title, label, tick, mlabel, mtick and line option, and for any comma in a scale | Binding amendment. Changed behaviour: a CHANGELOG line |
| SD-8 | `range()` on a rescaled axis | Not applied, as in twoway. One note per graph and letter at BUILD time in both modes | The alternative draws a different picture from twoway |
| SD-9 | `style(rescale)`/`style(combine)` | Their scale part is honoured. A note says `only its separate scales are drawn`. Any other `style()` is named as today | m03/m04/m06 measured |
| SD-10 | Case of rescale tokens | `_dash_parse_by`'s `.lower()` is kept, so `YRESCALE` is honoured where twoway gives r(198) | Consistent with cols/total today. Refusing it belongs to a by() validation item, handed to S15 |
| SD-11 | One object or equal values on explicit-hull and `#N` axes | ONE Range1d object per axis per graph, so panels pan and zoom together | Consistent interaction. Documented |
| SD-12 | Case ids and truth blocks | AX-01..AX-08 in `test_twoway_option_parity.cscript`. AX-11..AX-18 and BSC-01..BSC-07 are two S10 blocks of `test/test_wp29_truth.cscript` (A3, `WP29_ONLY=S10`). BSC-08..BSC-10 go in `test_by_suboptions.cscript` | index manifest prefixes AX, BSC (checked unused: `grep -o "\bAX-[0-9]*\|\bBSC-[0-9]*" test/*.cscript test/*.py` finds none; `DAX-` in test_dual_axis.py is a different id, so grep with `\b`) |
| SD-13 | twoway's common scale includes fit lines (c15), and twoway draws only outer axes on shared panels | Out of scope: the primary-renderer limit (`_dash_limit_ranges_to_primary`) keeps fits out of every autorange (pre-existing), and dash draws every panel's axes (B16) | Handed to S15 for the P1.3 and B16 owners |

## User stories

- **US-10.1** As a twoway user, I want `ylabel(…, axis(2))`, `yscale(log axis(2))`, `yline(#, axis(2))` and `ytick(…, axis(2))` (and the x forms, in any of twoway's spellings) to style the second axis, so that my do-file draws the same picture in dash, saved and served, before and after a filter move.
- **US-10.2** As a twoway user, I want `ylabel(10 20) ylabel(5000 10000, axis(2))` to keep both lists, so that repeating an option per axis works as in twoway.
- **US-10.3** As a twoway user, I want an `axis(#)` that names an axis no layer uses, a repeated `axis()`, `AXIS()` and a second comma refused with twoway's message and r(198), so that a typo is not drawn silently on the wrong axis.
- **US-10.4** As a twoway user, I want `by()` panels to share one scale per axis (y, x and the second axes, the Total panel too), so that the panels compare at a glance as in Stata.
- **US-10.5** As a twoway user, I want `by(, yrescale)`, `xrescale`, `rescale`, their abbreviations and `style(rescale)` to give each panel its own scale on that axis, with `#N` ticks per panel and `range()` handled as twoway handles it.
- **US-10.6** As a dashboard reader, I want the shared scale to keep spanning what every panel shows after I move a filter, so that the panels stay comparable.
- **US-10.7** As a dashboard publisher using `dash build, server`, I want every note about a dropped `range()` or an unused second-axis option printed in my Stata log when I build, not only in a server session I never see.

## Business requirements

- **BR-10.1** Every routed option is drawn on the axis it names, in both modes, before and after any filter move. axis(1) and unqualified options stay on axis 1. Nothing is dropped unnamed.
- **BR-10.2** Repeated copies are merged per axis as twoway merges them (the last list wins per axis, line copies are kept, scale words merge).
- **BR-10.3** Every refusal matches twoway's rc and message text, in twoway's order. The axis number follows twoway's integer bounds.
- **BR-10.4** By default a by() graph's panels share one scale per axis (x, y, y2, x2), equal to the union of every panel's drawn data, and it stays the union after every filter move.
- **BR-10.5** A rescaled axis is scaled, ticked (`#N`) and hulled per panel. Its `range()` values (axis(2)'s too) are not applied, with one note at build time in both modes. Labels and ticks still widen each panel. reverse and log are kept.
- **BR-10.6** Sharing never crosses graphs: a range object is shared only among one by() graph's own panels.
- **BR-10.7** Changed results and changed acceptance are listed in CHANGELOG.md with the command, the old value and the new.

## Technical requirements

### P0.5 (axis(#) routing)

- **TR-10.1 Family table (Mata and Python share it by content).** For side d in {x, y}, in this order:

  | family | twoway full name | dash name | minimum | message name | rewrite on N=2 | axis words read from |
  |---|---|---|---|---|---|---|
  | title | dtitle | dtitle | 2 | dtitle | dtitle2 | after the first top-level comma |
  | label | dlabels | dlabel | 2 | dlabels | dlabel2 | after the first comma |
  | mlabel | dmlabels | dmlabel | 3 | dmlabels | not routed | after the first comma |
  | tick | dticks | dtick | 4 | dticks | dtick2 | after the first comma |
  | mtick | dmticks | dmtick | 3 | dmticks | not routed | after the first comma |
  | line | dlines | dline | 3 | dlines | dline2 | after the first comma |
  | scale | dscale | dscale | 3 | dscale | dscale2 | every word of the value |

  A token belongs to a family when:
  - its option name is typed in lower case;
  - it starts with d;
  - its length is at least the minimum and at most the full name's;
  - it equals the full name's prefix of that length.

  The minimums make the match unique: `yt` is title, `ytic` is tick, `yl` is label, `yli` is line. `yti2`/`yla2` never match (a digit). An upper-case option name is never touched; `_dash_refuse_foreign` refuses it later, as today.

  An **axis word** is a token whose name, as typed, is a lower-case string of at least 2 characters that is a prefix of `axis`, followed by `(`.

  A **badly cased axis word** is a token whose lower-cased name is such a prefix but which is not typed in lower case (`AXIS(`, `Axis(`, `AX(`).

- **TR-10.2 Axis number.** `real scalar _dash_axis_num(string scalar arg)` in dash_parse.mata, with Python twin `_dash_axis_number(arg)`:
  - `v = strtoreal(strtrim(arg))`.
  - Return v when `v < .`, `v == floor(v)` and `-2147483648 <= v <= 2147483647`; otherwise return 1.
  - The Python twin accepts only `^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$` after strip, so `inf`, `nan` and `1_0` give 1. Mata routes hex forms such as `1.0x+1` before any spec exists; the twin serves hand-made specs only.
  - A message prints N as `strtrim(strofreal(N, "%11.0f"))` (`1000000000`, `-2147483648`), never bare `strofreal`.

- **TR-10.3 The Mata route.** `_dash_route_axis2(opts)` keeps its signature and its no-op early return. For each top-level token of a family, with value `v`:
  1. **Double comma.**
     - Non-scale family: `_dash_rep_split(v, body, sub)` and then `_dash_rep_split(sub, b2, s2)`. When the second returns 1 and `strtrim(s2) != ""`, the token is left byte for byte (refused by the check).
     - Scale family: `_dash_rep_split(v, b, s)` returns 1 with `strtrim(s) != ""` → left as typed.
     - A comma followed only by blanks is accepted: the route then reads `b2` (non-scale) or `b` (scale) as the sub-option text.
  2. **Axis words.** Scan the sub-option words (`_dash_rep_toks(sub, 0)` after the trailing-comma trim, or every word of a scale's value). The FIRST axis word gives N = `_dash_axis_num(its argument)`. With none, N = 1. A second axis word or any badly cased axis word → the token is left as typed.
  3. **Rewrite.**
     - N=1: drop the axis word (when present) and rename a plural to dash's name. Example: `ylabels(5000)` becomes `ylabel(5000)` and `yticks(1, axis(1))` becomes `ytick(1)`. A singular name with no axis word is not touched.
     - N=2 on title, label, tick, line: `d<family>2(<body>[, <rest>])`, where rest is the remaining words joined by one blank.
     - N=2 on scale: `dscale2(<rest words>)`.
     - Any other N, and mlabel/mtick with N=2: the token is left as typed.
  4. Every other byte (quotes, `$`, backticks, `"axis(2)"` inside a string) is returned unchanged. No regex.

- **TR-10.4 The axis check (refusals).** In dash_parse.mata, next to `_dash_route_axis2`:
  - **`void _dash_axreq_clear()`** sets the external `string matrix _dash_axreq` to `J(0, 9, "")`.
  - **`void _dash_axreq_add(string scalar opts, real scalar seg)`** scans the RAW (unrouted) option text with the TR-10.1 table:
    - A counting pass first, then a preallocated block, so the work is O(n).
    - One row per family token: side (1 = x, 2 = y), family index 1..7 in twoway's order (scale 1, labels 2, mlabels 3, ticks 4, mticks 5, title 6, lines 7), `seg`, the token's position, N, the message name, the value as typed, the double-comma word ("" if none), and the first bad axis word as typed ("" if none).
    - The bad axis word is the first, in typed order, among badly cased axis words and second lower-case axis words, cut at its `(`.
    - The double-comma word is the first blank-delimited word after the second comma, cut at its first `(`.
    - dash's own `ytitle2()`… are not family tokens and are not recorded (SD-3).
  - **`real scalar _dash_axreq_check(string scalar ys, string scalar xs)`**:
    - Orders the rows by (side, family, seg, position) with `order()`.
    - Reports the first row that fails, testing in this order:
      1. the double-comma word → `invalid '` + word + `'`;
      2. N not in that side's set → `<msg>(<value>) not allowed, <d>axis<N> does not exist`;
      3. the bad axis word → `option <word>() not allowed`.
    - Prints through `_dash_say("err", before, value, after)`, so user text is SMCL-escaped.
    - Calls `_dash_axreq_clear()` and returns 198 on a refusal. Otherwise it clears and returns 0.
  - **`ys`/`xs`** are the blank-separated distinct layer axes (an empty yaxis means 1).
  - **Where dash.ado calls them (`_dash_plot`):**
    - `_dash_axreq_clear()` at its start, beside `global dash__g_by ""`.
    - For each segment, `_dash_axreq_add(<the segment's raw opts before routing>, k)` AFTER its `_dash_parse_plot_opts` succeeds, so r(1003) stores nothing.
    - For the after-comma options, `_dash_axreq_add(<raw gopts>, n_segs + 1)`, called after the segment loop (A3).
    - Then `_dash_axreq_check(ys, xs)` right after the after-comma merge (after dash.ado:4836, before `_dash_option_rules` at 4848), with `exit 198` when it returns 198.
  - The `_needed` list (dash.ado:232-246) appends `_dash_axis_num _dash_axreq_clear _dash_axreq_add _dash_axreq_check` at its END.

- **TR-10.5 Declarations and keys (dash.ado).**
  - Declare lower-case `ytick2(string asis) xtick2(string asis) yline2(string asis) xline2(string asis)` in `_dash_parse_graph_opts` (702-722) and `_dash_parse_plot_opts` (940-960).
  - Add `sreturn local ytick2 : copy local ytick2` (and the three others) after `sreturn local xscale2` (833), and `sreturn local g_ytick2 : copy local ytick2` (and the others) after `sreturn local g_xscale2` (1245).
  - Add `ytick2 xtick2 yline2 xline2` to all seven `foreach gk/gkey in` lists (4090, 4624, 4656, 4746, 4800, 4831, 5086), after `xscale2`.
  - Rule table (1949-1951): `ytick2=axislist xtick2=axislist`.
  - `_dash_rep_cat`: `ytick2`/`xtick2` in the "L" list; `yline2`/`xline2` join the "X" test.
  - The per-segment layer axis: after `_dash_parse_plot_opts` in `_dash_process_segment`, `c_local _seg_yaxis_out` and `_seg_xaxis_out` hold the normalised `yaxis`/`xaxis` value (`= cond(real(s(yaxis)) < ., real(s(yaxis)), 1)`, beside `c_local _seg_named_out` at 4082). `_dash_plot` resets them beside 4740 and accumulates `_g_ys`/`_g_xs` with `: list uniq` after 4768.

- **TR-10.6 Python route twin.** These run in both loaders, between `_dash_route_axis_titles` and `_dash_lone_second_axes` (DashRenderer.__init__ 25024-25025; ServerAppBuilder.__init__ 28287-28288).
  - **`_TEXTBOX_SUBOPTS`** `("axis", "axis")` becomes `("axis", "ax")`.
  - **`_dash_route_axis_titles`** finds the first axis word typed in lower case through `_dash_subopt_name`, plus a case test on the raw token, and applies `_dash_axis_number`. N=1 drops the word, N=2 routes, any other N leaves the token.
  - **New `_dash_route_axis_options(spec)`:**
    - pure: it returns a new dict and returns a spec of the wrong shape unchanged;
    - linear;
    - handles `ylabel/xlabel` and `ytick/xtick` (`_dash_axis_head_split`, then `_dash_by_tokens` of the tail);
    - handles `yscale/xscale` (`_dash_by_tokens` of the whole value);
    - handles `yline/xline`: copies are cut with `_dash_by_tokens_commas` and grouped as `_dash_refline_instances` groups them (a numeric segment after a comma starts a copy). Each copy is routed alone, and axis-2 copies are joined with `", "` onto `yline2`.
  - **When N=2 meets an existing `*2` key:**
    - for label, tick or scale, the explicit `*2` key wins and `_dash_warn_once(("route", graph name, key), "dash: <key>(..., axis(2)) and <key>2() both given; <key>2() is drawn")` (the ytitle precedent);
    - for lines, the copies are joined.
  - Module constant `_DASH_AXIS2_KEYS = {"y": ("ytitle2", "ylabel2", "yscale2", "ytick2", "yline2"), "x": (...)}`.

- **TR-10.7 Lone axis.**
  - `_DASH_LONE_AXIS_OPTIONS` becomes `{"y": ("ytitle", "ylabel", "yscale", "ytick", "yline"), "x": (…)}`.
  - In `_dash_lone_second_axes`, for `yline`/`xline` the moved `*2` value is JOINED to an existing first-axis value with `", "` (A8). The other keys keep "the `*2` wins".

- **TR-10.8 Drawing (shared helpers; both modes).**
  - **`_dash_refline_draw(fig, opt, dim, values, style, scheme, Span, range_name="default")`:**
    - converts dates only when `range_name == "default"`;
    - passes `y_range_name=range_name` (`dim == "width"`) or `x_range_name=range_name` to the Span.
  - **`_dash_reference_lines`** also reads `yline2`/`xline2`. It parses them with `_dash_refline_instances`, names bad tokens under option `yline`, and draws with `range_name="y2"`/`"x2"` only when `"y2" in fig.extra_y_ranges` (`"x2" in fig.extra_x_ranges`). A Span never widens a range (c44).
  - **`_dash_finish_secondary_axes`:**
    - reads `{n}tick2` before the range is set: `tspec = _dash_parse_axis_spec(tick_raw)`; when `tspec["mode"] == "explicit"` and not `tspec.get("norescale")`, its ticks join `vals` (c46, A9);
    - replaces `if spec is None: continue` with a branch, so that `{n}tick2` is applied whether or not `{n}label2` is: `_dash_apply_tick_option([ax], grids, tick_raw, f"{n}tick2", col_vals or None, seen, key, grid_color, date_kind=None)`, where `grids` holds a `Grid(dimension=dim, axis=ax, grid_line_color=None, **{kw: name})` added when `tspec.get("grid")`;
    - places `#N` through `_dash_finish_count_ticks`, which runs after it in both modes.
  - **The primary y range is never touched** by y2 tick positions (A9).

- **TR-10.9 Build-time notes.**
  - **New pure `_dash_unused_second_axis_notes(graph)`** returns `[(key, text)]`:
    - one entry per non-blank `{d}title2/{d}label2/{d}scale2/{d}tick2/{d}line2` key on a graph where no plot has `options[{d}axis] == "2"`;
    - the text is `dash: graph '<_dash_display(name)>': <key>() (<first>(..., axis(2))) is not drawn: no layer is on <d>axis(2).`;
    - the key is `("axis2-unused", name, key)`.
  - **Saved:** `DashRenderer._build_figures` calls it once per graph at the top of the "3. Build figures" loop and raises each note through `_dash_warn_once`.
  - **Served:** the new `ServerAppBuilder._plan_graph_notes()` is called beside `self._plan_by_groups()` in `build()` (29175). It raises the same notes and never loads the frame. The app session never calls it, so it does not repeat the note.

- **TR-10.10 Copy lists and maps.**
  - The served app calls no new helper for P0.5. `_dash_route_axis_options`, `_dash_axis_number` and `_dash_unused_second_axis_notes` run at build time and are NOT copied.
  - `_TEXTBOX_SUBOPTS`, `_dash_refline_draw`, `_dash_reference_lines` and `_dash_finish_secondary_axes` change in place and are already copied (constants 28362; functions 28682-28684, 28803-28805).
  - If an executor finds the app calling a new name, it goes after `"_dash_apply_scale_ranges"` (28803, R2) and `test_textbox_grammar.py::TestTheServedCopy` gains it.
  - `test/function_test_map.py` gains `_dash_axis_number`, `_dash_route_axis_options`, `_dash_unused_second_axis_notes` and `ServerAppBuilder._plan_graph_notes`.
  - `test/program_coverage_map.py` gains `_dash_axis_num` → `test_twoway_option_parity.cscript:AX-02`, `_dash_axreq_clear`/`_dash_axreq_add`/`_dash_axreq_check` → `test_twoway_option_parity.cscript:AX-03`, `:AX-04`, and puts `test_twoway_option_parity.cscript:AX-01` first for `_dash_route_axis2`, keeping TBG-03/TBG-02.

- **TR-10.11 Saved-page JS.** None. Axes and Spans are static models (measured). The CustomJSTicker reuses the constant `_DASH_TICK_*_JS`.

- **TR-10.12 Security.**
  - No regex, `eval` or `exec` on user text.
  - Mata reads values by value (`st_local`) and keeps them in an external matrix, never in a macro. The matrix is cleared at the start and after the check (A11).
  - Every echo goes through `_dash_say` (Stata) or `_dash_display` (Python).
  - Positions reach Bokeh only as floats through the existing parsers (bounded by `_MAX_AXIS_TICKS`).
  - The scans are linear, with preallocation. AX-08 times 10,000 copies under 10 s.

### P0.2 (by() shared scales)

- **TR-10.13 Rescale parse.**
  - `_DASH_BY_SUPPORTED` (17001) gains six keys with every spelling from the minimum to the full name:
    - `"rescale": ("r", "re", …, "rescale")`
    - `"norescale": ("nor", …)`
    - `"xrescale": ("xr", …)`
    - `"yrescale": ("yr", …)`
    - `"noxrescale": ("noxr", …)`
    - `"noyrescale": ("noyr", …)`

    It is already copied (constants 28375).
  - `_dash_parse_by` consumes a bare token of any of them (no `(`), so it is not named. `r(1)` keeps being named (rows).
  - A `style(<arg>)` token whose stripped arg is exactly `rescale` or `combine` is removed from `unsupported`. When `warn` is set, it is noted once: `dash: by() sub-option style(<arg>): only its separate scales are drawn; the rest of the style is not implemented.`
  - The 5-tuple is unchanged; 7 call sites read it.
  - **New `_dash_by_rescale(by_raw) -> frozenset`** (a subset of {"x", "y"}). It never raises (it takes `str()` of anything) and is linear:
    - It tokenises the text after the first comma with `_dash_by_tokens`, so `title("yrescale")` is never read.
    - The style base is yes when the LAST `style()` token's arg is exactly `rescale` or `combine`.
    - `rescale` adds yes on x and y. Otherwise `norescale` adds no on both.
    - `[no]xrescale`/`[no]yrescale` add yes or no for that axis.
    - An axis is rescaled if any yes, else not if any no, else the style base.
    - `compact` never matters (m04).

- **TR-10.14 Per-panel build.**
  - `DashRenderer._make_figure(graph_spec, source, facet_view=None, rescale=frozenset())` passes `rescale` to `_make_figure_body`, which passes it to `_dash_apply_scale_ranges(fig, _xsc, _ysc, …, rescale=rescale)`.
  - The served template's `def _dash_figure_for(g, gname, g_df, _fac_label=None, _rescale=frozenset()):` passes `rescale=_rescale` at its `_dash_apply_scale_ranges` call (30464).
  - `_dash_apply_scale_ranges(…, rescale=frozenset())` empties `vals[letter]` for each rescaled letter (twoway drops range(); m07 shows the emptied values must not feed `_dash_finish_count_ticks`' `extra`). It keeps `rev` and `flipped` (e03), and sets `fig._dash_rescaled = frozenset(rescale)`.
  - `_dash_finish_secondary_axes` skips `want` for `y2` when `"y" in getattr(fig, "_dash_rescaled", ())` (`x2` when `"x"`). Before padding, it records `fig._dash_secondary_hulls[name] = (lo, hi, kind, reverse)` with the pre-padding min and max of `vals`.

- **TR-10.15 Call sites.**
  - Saved by() loop (27239-27286): `_brs = _dash_by_rescale(g.get("graph_options", {}).get("by", ""))` once per graph, then `self._make_figure(g_panel, src, facet_view=panel_view_r, rescale=_brs)`. `_dash_common_count_ticks([...])` becomes `_dash_share_by_scales([...], _brs)`.
  - Served template (30754-30845): `_brs = _dash_by_rescale((go.get('by') or '').strip())` after the `_dash_parse_by` line. Every `_dash_figure_for(...)` in the by() branch passes `_rescale=_brs`: the panel loop, the empty-frame fallback and the every-panel-dropped fallback. `_dash_common_count_ticks([...])` becomes `_dash_share_by_scales([...], _brs)`.
  - The saved renderer's one-empty-panel paths must pass the same set; the parity case "by(foreign, yrescale) yscale(range(0)) with every foreign missing" pins it.

- **TR-10.16 Build-time range note.**
  - **Pure `_dash_by_range_notes(graph)`** returns `[(key, text)]`:
    - `[]` unless `_dash_parse_by(by, warn=False)[0]` is non-empty;
    - otherwise one entry per letter in `_dash_by_rescale(by)` whose `{d}scale` or `{d}scale2` value matches `_DASH_SCALE_RANGE_RE` (2635);
    - the text is `dash: graph '<_dash_display(name)>': by(, <d>rescale) draws each panel on its own <d> scale; <d>scale(range()) is not applied, as in twoway.`;
    - the key is `("by-range", name, d)`.
  - Saved: called with `_dash_unused_second_axis_notes` at the top of the "3. Build figures" loop. Served: called in `ServerAppBuilder._plan_graph_notes()`.
  - The app never calls it. `_dash_parse_by`'s note at build time (HC5-08) is unchanged.

- **TR-10.17 `_dash_share_by_scales(figs, rescale)`**, new, placed after `_dash_common_count_ticks`. Called in both modes once a graph's panels are built.
  - Return when `len(figs) < 2`. Otherwise, for each letter in ("x", "y") not in `rescale`:
    - **(a) Primary axis.** When every panel's `{letter}_range` is a `DataRange1d`:
      - Build `shared = DataRange1d(**{k: v for k, v in figs[0].<letter>_range.properties_with_values(include_defaults=False).items() if k not in ("renderers", "start", "end", "id", "name")})`.
      - Set `shared.flipped = any(f.<letter>_range.flipped for f in figs)`.
      - Set `shared.renderers` to the union of the panels' lists in panel order, de-duplicated by `id()` with a set. When every list is `[]`/`"auto"`, keep `[]`. When only some are, expand those panels to `[r for r in f.renderers if getattr(r, "<y|x>_range_name", "default") == "default" and not _dash_is_swatch(r)]`.
      - Assign it to every panel.
      - Repoint `e["rng"]` of that letter's `name == "default"` entries in `f._dash_count_entries` and `f._dash_hull_axes`.
    - **(b) Second axis `{letter}2`.** When every panel has `extra_{letter}_ranges[name]`:
      - Take the union of `f._dash_secondary_hulls[name]` (lo, hi). kind and reverse come from the first panel.
      - Build one `_dash_padded_range(lo, hi, kind, reverse)`.
      - Set it into every panel's `extra_{letter}_ranges` with `f.extra_y_ranges = {**f.extra_y_ranges, name: new}`.
      - Repoint the matching entries' `rng`.
  - Then call `_dash_common_count_ticks(figs, letters=<the non-rescaled letters>)`.
  - **ORDER IS LOAD-BEARING:** share first, then the common ticks.

- **TR-10.18 `_dash_common_count_ticks(figs, letters=("x", "y"))` and `_dash_hull_ranges(fig, entries, common=None, made=None)`.**
  - In `_dash_common_count_ticks`, count groups and hull panels keep only entries whose `e["letter"] in letters`. y2 entries carry letter `"y"`, so under yrescale y2 `#N` stays per panel (c17).
  - One `made = {}` dict is passed to every `_dash_hull_ranges` call. With `made` and `common`, `_dash_hull_ranges` creates the padded Range1d once per `hkey` and reuses it for every later panel. One object per axis gives SD-11.
  - Defaults keep today's behaviour for non-by graphs and direct test calls.

- **TR-10.19 Filter moves.** No code. Both modes update sources only. The shared DataRange1d recomputes the union in BokehJS. Explicit-hull and `#N` Range1d axes keep holding, as documented.

- **TR-10.20 Copy lists and maps.**
  - Functions tuple: `"_dash_by_rescale"` after `"_dash_by_tokens", "_dash_parse_by",` (28638, R2), and `"_dash_share_by_scales"` after `"_dash_common_count_ticks"` (28708).
  - `_dash_by_range_notes` is build-time only and NOT copied. This deviates from the R2 table, which lists it: the app must not repeat the note (R6).
  - `test/function_test_map.py` gains `_dash_by_rescale`, `_dash_by_range_notes` and `_dash_share_by_scales`. `_dash_common_count_ticks` stays mapped (:424).
  - Both served guards stay green: `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` and `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`.

- **TR-10.21 Real-time browser harness.** New `test/range_probe.py`:
  - **Launch:**
    - reuses `responsive_probe.find_chrome()`;
    - starts Chrome `--headless=new --no-first-run --user-data-dir=<tmp> --remote-debugging-port=<free port from socket.bind(("127.0.0.1", 0))> --window-size=1200,900 about:blank`;
    - reads `http://127.0.0.1:<port>/json` and connects with `tornado.websocket.websocket_connect`.
  - **API:**
    - `RangeProbe(path)` is a context manager that kills Chrome and removes the profile on exit.
    - `ranges()` returns, per Figure, `[title, y.start, y.end, x.start, x.end, y_range.id, x_range.id]` from `Bokeh.documents[*].all_models`.
    - `move_range_slider(fraction)` sets each RangeSlider's `value` to `[start, start + fraction*(end-start)]`.
    - `wait_settled(timeout)` polls `ranges()` every 100 ms until two readings agree.
    - `js_errors()` collects `Runtime.exceptionThrown`.
  - It never calls `update_dataranges` or `request_paint`. A test greps its source for both.
  - The served page is `bokeh.embed.file_html(doc.roots…, INLINE)` of a `make_document` document, before and after `test_mode_parity._fire`.
  - It skips without Chrome (the responsive_probe convention).

- **TR-10.22 Security.**
  - The rescale parse reads fixed names through the existing linear, quote-aware tokenizer. It never raises on hostile or non-string input.
  - There is no new JavaScript and no string interpolation into JS.
  - The notes echo the graph name only through `_dash_display`.
  - The renderer union is bounded by `$dash_max_by_groups` × layers and de-duplicated with an id set.
  - Nothing is written to disk, and no file mode changes.

## Boundaries

- Axes 3-9 and `yaxis(1 2)` stay GAPS2 B15 residual work: `yaxis(3)` is still refused (dash.ado:1897).
- `ymlabel`/`ymtick` are validated, not drawn (SD-5).
- The `t*` time-axis options (P1), the T and Z sides of `ParseAndLogAxes`, and B22/B23 sub-option validation (`a(2)` → twoway "option a() not allowed", `bogus()` inside a label) are not this section's.
- Date-valued second axes are out of scope (y2/x2 stay Linear/Log).
- `ylabel(…, axis(2) add)` is routed. `add` is named on `ylabel2()` (twoway adds to the default ticks: yaxis2 major [0 15000 5000 10000]). This is recorded as a residual (A10).
- The second axis's default title is out of scope: twoway titles `yaxis(2)` by its layers' variables, while dash draws none (`_dash_add_secondary_axes` uses `{n}title2` or ""). Measured in dash only. Handed to S15.
- The outer-axes-only display of shared panels (B16 i*axes) and fits in the common scale (c15) are out of scope (SD-13).
- Refusing `YRESCALE` (r198 in twoway) and two `style()` is a by() validation item (SD-10).
- Do not edit `_dash_axis_labels` (S03), `_make_figure_body`'s filter/qualifier code (S07, S12, S14), the lpoly helpers (S11) or the served launcher (S08, S13).
- No new `.cscript`, and no edit to `test/run_all_cscripts.do` or `test/test_cscript_hygiene.py` (A3, R1).
- Only S15 edits ROADMAP.md, GAPS2.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, DROPIN-REMAINING.md and AGENTS.md (A5); see "Notes for the closeout".

## Stata truth

Two new fixtures. Each is extracted by a script under `scripts/` that reads its repository root from a global, so it runs through a two-line driver. `<repo>` is the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s10`. `<scratch>` is the section's scratch directory (the one holding `batch-2-base.txt`). Stata runs from `<scratch>/s10`:

```sh
mkdir -p <scratch>/s10
printf 'global W29_REPO "%s"\ndo "%s/scripts/extract_axis2_truth.do"\n' "<repo>" "<repo>" > <scratch>/s10/run_extract_axis2_truth.do
dash_nobrowser=1 <repo>/scripts/stata_slot.sh <scratch>/s10 <scratch>/s10/run_extract_axis2_truth.do     # log <scratch>/s10/run_extract_axis2_truth.log
```

The same two lines with `extract_by_scales_truth` run the second script. Each script:
- opens with `if "${W29_REPO}" == "" exit 198` and `adopath ++ "${W29_REPO}/"`;
- sets `graphics off`;
- captures `shell cd "${W29_REPO}" && git rev-parse HEAD > "<tempfile>"` and reads it back into a local (the extract_axis_truth.do:107-114 pattern);
- writes the JSON from a `python:` block that reads Stata only through `sfi.Macro.getLocal`/`sfi.Data` and never calls Stata. A backtick is written as `\x60`.

`_meta` (D12) holds `stata_version`, `born_date`, `dash_commit`, `extracted` and `method`. Both fixtures are `git add -f`'d and named in `test/test_fixtures_are_committed.py`. No existing fixture is regenerated; `natscale_axes_truth.json`'s `by` records are reused as they are.

- **`scripts/extract_axis2_truth.do` → `test/fixtures/axis2_truth.json`.**
  - **Probes:** every command quoted in "P0.5: twoway, measured" (ids c2-c54, x1-x12, x101-x114, x201-x210, r-, gb, plus the integer-bound and double-comma rows). Each probe holds in `local o` with compound quotes (`` `"…"' ``). Never put a bare quoted word in a `foreach` list: that produced a spurious r(133) in the research.
  - **Per probe:** `id`, `command`, `rc`, `error` (the first error line, read from a per-probe log through `file read`), and:
    - per axis object yaxis1/yaxis2/xaxis1/xaxis2: the `dlg_tickpos` lists of major, majornl, minor and minornl (`.Graph.<ax>.<set>.dlg_tickpos[i]`, `arrnels` first);
    - per plotregion j: `yaxis_dexes`, `xaxis_dexes`, `{y,x}scale.{curmin,curmax}`, `transform.stylename`, `reverse.istrue`, and `_xylines[l].z` with orientation (`gdi_y0 == gdi_y1`);
    - for gb: per panel, `.Graph.graphs[k].yaxis2.major.dlg_tickpos`.
  - **`_meta.caveats`:** "twoway prints a broken message and r(133) for a refused value holding a double quote".
- **`scripts/extract_by_scales_truth.do` → `test/fixtures/by_scales_truth.json`.**
  - **Probes:** ids c01-c38, d19-d55, e01-e12, f01-f05, k01-k21 and m01-m08 as quoted in "P0.2: twoway, measured", plus one row per spelling of the rescale-rule list in the TDD stubs.
  - **Per probe:** `command`, `rc`, `n` (`.Graph.n`) and per panel:
    - `title` (`.Graph.graphs[k].subtitle.text[1]`);
    - y and x `plotregion1.{y,x}scale.{min,max,curmin,curmax,reverse.istrue,transform.stylename}`;
    - `{y,x}axis1.major.{min,max,delta}`;
    - `{y,x}axis1.draw_view.istrue`;
    - `yaxis2.plotregion.yscale.{min,max}`, `yaxis2.major.{min,max,delta}`, `xaxis2.plotregion.xscale.{min,max}`.
  - **`data`:** `sysuse auto`'s `mpg weight price turn rep78 foreign` (74 rows; a missing value is JSON null) with foreign's value labels, plus the `%td` set of c23 (`set obs 20; gen t = td(01jan2000)+cond(_n>10,400+_n*30,_n); format t %td; gen g = _n>10; gen y = _n+cond(_n>10,100,0)`).
  - **`rescale_rule`:** derived in the python block. It maps each rescale-list spelling to the sorted letters whose panel `scale.min/max` differ between panels.
- **Live truth blocks** in `test/test_wp29_truth.cscript` (they measure twoway in the same run; no fixture):
  - `* ==== S10 P0.5: axis(#) routing ====` (AX-11..AX-18);
  - `* ==== S10 P0.2: by() shared scales ====` (BSC-01..BSC-07).

  Both are gated `local only : env WP29_ONLY` / `if inlist("`only'", "", "S10") {`. They are appended above `* ==== append new blocks above this line ====`, after every batch-1 block (R1). Their helper programs and `python:` reader sit directly above each block's `local only` line, outside the gate, because a `program define` or `python:` block cannot sit inside the `if`.

  Run:
  ```sh
  printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_wp29_truth.cscript" > <scratch>/s10/run_test_wp29_truth.do
  dash_nobrowser=1 WP29_ONLY=S10 <repo>/scripts/stata_slot.sh <scratch>/s10 <scratch>/s10/run_test_wp29_truth.do
  ```
  Read the log; never relaunch to check. A SKIP is not a pass: the script exits 222 when `c(python_exec)` is empty.

## TDD test stubs

New tests pass `var_labels` explicitly wherever they assert title text (A7). A saved figure comes from `DashRenderer(sp, dp)._build_figures()`. A served one comes from `ServerAppBuilder(sp, dp).build(ap)`, then import, then `make_document(Document())` (the `test_dual_axis._lone_figure` pattern). Both are parametrised `mode in ("saved", "served")`.

### P0.5: `test/test_axis2_suboptions.py` (new, task 10-02)

The data is a 74-row frame built from `test/fixtures/axis2_truth.json`'s probe data, or from `test/fixtures/data/auto.csv` with `price`/`length` synthesised as in `test_dual_axis._make_spec_and_data`. Each test names its pre-fix failure.

- Test: `TestTheSecondAxisOptionsReachTheSecondAxis::test_ylabel_axis2[mode]` — dual-y plus `ylabel "20 30, axis(2)"`: the right (y2) axis ticker is `FixedTicker([20, 30])`, the left ticker is not [20, 30], and no warning contains `axis(2)`. Pre-fix: left [20, 30] plus a warning.
- Test: `…::test_yscale_log_axis2[mode]` — right `LogAxis` (`y_range_name == "y2"`), left `LinearAxis`. Pre-fix: left LogAxis.
- Test: `…::test_yline_axis2[mode]` — the Span at 5000 has `y_range_name == "y2"`. Pre-fix: `"default"`.
- Test: `…::test_ytick_axis2[mode]` — the right axis ticker is a `CustomJSTicker` with `args["extra"] == [5000.0, 7500.0]`; the left ticker type is unchanged.
- Test: `…::test_x_family[mode]` — dual-x plus `xlabel "150 200, axis(2)"`, `xscale "log axis(2)"`, `xline "200, axis(2)"` and `xtick "160, axis(2)"` all land on the `above`/x2 axis or range.
- Test: `…::test_axis1_and_unqualified_stay_first[mode]` — `ylabel "20 30, axis(1)"`: left [20, 30], no warning. Pre-fix: `axis(1)` named.
- Test: `…::test_axis_spellings[mode]` — `ax(2)`, `axi(2)`, `axis( 2 )`, `axis(02)`, `axis(2.0)`, `axis(+2)` and `axis(2e0)` go right. `axis(2.5)`, `axis(a)`, `axis()`, `axis(1e300)` and `axis(2147483648)` go left, silently.
- Test: `…::test_ytitle_ax2_titles_the_second_axis[mode]` — `ytitle '"T", ax(2)'`: the right `axis_label == "T"`. Pre-fix: left, with a note.
- Test: `…::test_extents[mode]`:
  - `ytick "20000, axis(2)"` widens the y2 hull to ≥ 20000 (`_dash_range_hull(fig.extra_y_ranges["y2"])`);
  - `ylabel "20000, axis(2)"` widens;
  - `yline "30000, axis(2)"` does not;
  - `ytick "20000, axis(2) norescale"` and `ylabel "20000, axis(2) norescale"` do not;
  - the PRIMARY `y_range` is the same model type, with the same `renderers` and hull, as with no option (A9).
- Test: `…::test_merged_line_copies_split[mode]` — hand-made `yline "5000, axis(2), 20"` gives `Span(5000, "y2")` and `Span(20, "default")`.
- Test: `…::test_lone_second_axis[mode]` — lone yaxis(2) plus `ylabel "1000(2000)5000, axis(2)"`, `yscale "log axis(2)"`, `ytick "4000, axis(2)"` and `yline "3000, axis(2)"`: one left `LogAxis` with those ticks and a Span on `"default"`. A hand-made lone spec with `yline "20"` and `yline2 "3000"` keeps both Spans (A8).
- Test: `…::test_by_panels[mode]` — `by(foreign)` plus `ylabel "5000 10000, axis(2)"`: every panel's y2 axis is `FixedTicker([5000, 10000])`.
- Test: `…::test_date_primary_axis_line_on_y2[mode]` — a `%td` x with y on the left and a second layer `yaxis(2)`, plus `yline "5000, axis(2)"`: the Span sits at 5000 on `"y2"`, not date-converted.
- Test: `…::test_add_is_named_on_ylabel2[mode]` — `ylabel "5000 10000, axis(2) add"`: exactly one warning names `add` and starts `dash: ylabel2()`, and none starts `dash: ylabel()` (A10).
- Test: `TestTheTitleRouteKeepsTheDefault::test_unlabelled_title_restyled_through_the_route[mode]` — unlabelled `mpg` (`var_labels={}`) with `ytitle ", size(large) axis(1)"` and with `ytitle ", size(large)"`: the left `axis_label == "mpg"`, at the large size (S03's rule, kept through the route).
- Test: `TestAfterAFilterMove::test_served_move_keeps_routing` — a served document with a foreign dropdown, before and after `test_mode_parity._fire`: the Span stays on y2, the right ticks stay, the left ticker is untouched, and the saved figure equals it.
- Test: `TestTheRouteUnit::test_route_axis_options_unit`:
  - the caller's spec is unmodified;
  - `axis(1)` is dropped and `axis(2)` moved;
  - `axis(3)` is kept;
  - an explicit `ylabel2` wins with one note;
  - a quoted `"axis(2)"` inside label text and an upper-case `AXIS(2)` are untouched;
  - malformed specs pass through;
  - 2,000 graphs take under 2 s.
- Test: `TestTheRouteUnit::test_axis_number_unit` — the TR-10.2 table, including `"1e300"→1`, `"2147483647"→2147483647`, `"-0"→0`, `"inf"→1`, `"1_0"→1`.
- Test: `TestUnusedSecondAxisOptionsAreNamed::test_orphan_note[mode]` — one axis plus `ylabel2 "5"`: exactly one note `… ylabel2() … is not drawn: no layer is on yaxis(2).` One axis plus a hand-made `ylabel "20 30, axis(2)"`: no [20, 30] on the left and one note.
- Test: `TestUnusedSecondAxisOptionsAreNamed::test_served_note_is_raised_at_build_time` — the note is in `ServerAppBuilder.build()`'s own warnings and appears exactly once over build plus session.
- Test: `TestTheFixtureIsPinned::test_dash_draws_on_twoways_axis[mode]` — for every rc-0 probe of `axis2_truth.json` that dash can draw (label, scale, tick, line), the ticks, lines and transform are on the same axis index in dash. `test_meta_stamp` checks the four `_meta` keys.

### P0.5: Stata (task 10-03, `test/test_twoway_option_parity.cscript`)

Appended after S02's JO cases, before `// Summary`. Header "Groups" lines are added for AX-01..AX-08. Each case runs twoway and dash in the same run, adds to `nfail`/`faillist` on failure and prints `AX-0n PASS: …`.

- **AX-01** (direct) `_dash_route_axis2` maps:
  - `ylabel(5000 10000, axis(2)) ylabel(10 20)` → `ylabel2(5000 10000) ylabel(10 20)`
  - `yscale(log ax(2))` → `yscale2(log)`
  - `yline(5000, axis(2) lcolor(red))` → `yline2(5000, lcolor(red))`
  - `ytitle(T, ax(2))` → `ytitle2(T)`
  - `xt(V, axis(2))` → `xtitle2(V)`
  - `ylabels(5000)` → `ylabel(5000)`
  - `ytick(5000, axis(2),)` → `ytick2(5000)`

  The following come back byte for byte: `ymlabel(1, axis(2))`, `ylabel(5000, AXIS(2))`, `ylabel(5000, axis(2) axis(1))`, `ylabel(5000, angle(0), axis(2))`, `ylabel(1, axis(3))`, and hostile text (`$x`, a backtick, `"axis(2)"` in a label string).
- **AX-02** (direct) `_dash_axis_num` returns:
  - 2 for `2`, `02`, `2.0`, ` 2 `, `+2`, `2e0`, `1.0x+1`;
  - 1 for `a`, ``, `2.5`, `2 1`, `#2`, `.`, `1e300`, `2147483648`, `-2147483649`;
  - 2147483647, -2147483648, 1000000000, 0 and 10 for `2147483647`, `-2147483648`, `1e9`, `-0`, `1e1`.
- **AX-03** (refusal parity) For each refused command in Evidence (no layer: ylabel, yscale, yline, ytick, ymlabel, ymtick and unquoted ytitle; axis(3), (0), (-1), (10); duplicates; `AXIS`/`Axis`; xlabel axis(2) with only a y2 layer; lone `yaxis(2)` plus `ylabel(5000 10000)`, plus `ytitle(T)`; the integer-bound refusals):
  - twoway rc 198 and dash rc 198;
  - dash's log holds twoway's first error line (`cert_log_has`).

  For the quoted `ytitle("T", axis(2))`, twoway rc != 0, dash rc 198, and dash's log holds `ytitle("T", axis(2)) not allowed, yaxis2 does not exist` (SD-2).
- **AX-04** (order) The A3/A2 ordering commands from Evidence. dash's single error line equals twoway's.
- **AX-05** (double comma) The `invalid '<word>'` refusals in both. `ytitle(TT, size(small),)` and `ytick(5000, axis(2),)` are rc 0 in both, and the second stores `ytick2 "5000"`.
- **AX-06** (accepted parity, rc 0 in both) `ax(2)`, `axi(2)`, `axis(02)`, `axis(2.0)`, `axis(a)`, `axis(1e300)`, `axis(1.0x+1)`, the plot-group form `(scatter mpg weight, ylabel(5000, axis(2))) (line price weight, yaxis(2) sort)`, the by() form, and the plurals `ylabels(…, axis(2))`, `yticks`, `ylines`, `ymticks`.
- **AX-07** (spec after the merge; fails today) The stored spec equals:

  | command | stored spec |
  |---|---|
  | `ylabel(10 20) ylabel(5000 10000, axis(2))` | `ylabel "10 20"`, `ylabel2 "5000 10000"` |
  | the reverse order | the same |
  | `yscale(log axis(2)) yscale(reverse)` | `yscale "reverse"`, `yscale2 "log"` |
  | `yline(5000, axis(2)) yline(20)` | `yline "20"`, `yline2 "5000"` |
  | `ylabels(5000)` | `ylabel "5000"` |
- **AX-08** (exhaustion) 10,000 copies of `ylabel(1, axis(2))`: twoway r(1003), dash r(1003), dash under 10 s, and afterwards `mata: rows(_dash_axreq)` is 0.

### P0.5: truth block AX-11..AX-18 (task 10-11, `test/test_wp29_truth.cscript`)

Each case compares the live twoway `.Graph` members with dash's saved page and with the served app.

- **Saved page:** a python reader of the page's `application/json` models (the `_tbg_models` pattern, test_gaps2_truth.cscript:403-420).
- **Served app:** `dash build, saving("<app>") server replace`, then a `python:` block that imports the app with importlib, runs `make_document(Document())` and walks the models.

| Case | Command | Pass condition |
|---|---|---|
| AX-11 | ylabel axis(2) | y2 ticks = `.Graph.yaxis2.major.dlg_tickpos` |
| AX-12 | yscale(log axis(2)) | the right axis is a LogAxis; `.Graph.plotregion2.yscale.transform.stylename` is `log` |
| AX-13 | yline axis(2) | the Span is on y2; the line is in `plotregion2._xylines` |
| AX-14 | ytick axis(2) | the CustomJSTicker extra equals `yaxis2.majornl` |
| AX-15 | the x family | on the x2 axis |
| AX-16 | extents | `ytick(20000, axis(2))` puts 20000 inside y2; `yline(30000, axis(2))` does not |
| AX-17 | lone axis | one left axis with [5000 10000] |
| AX-18 | by() | each panel's y2 ticks = `.Graph.graphs[k].yaxis2.major` |

### P0.2: `test/test_by_scales.py` (new, task 10-15)

The data is the `by_scales_truth.json` `data` block. It fails with `pytest.fail` naming the fixture when the fixture is absent; never skip. The test file defines:
- `_emulated_hull(figs, letter)`: the min and max over every listed renderer of the shared range (or every default-range, non-swatch renderer when `[]`) of its glyph field's finite values, through its CDSView booleans;
- `_served_doc(spec)`: the build, import and `make_document` path, the one helper S13 may adjust.

- Test: `TestTheRescaleSubOptions::test_the_rescaled_axes_match_twoway[spelling]` — `_dash_by_rescale("foreign, " + s)` equals the fixture `rescale_rule[s]` for:

  | spellings | rescaled |
  |---|---|
  | `''`, `norescale`, `nor`, `noyrescale`, `r(1)`, `style(compact)`, `style(resc)` (m03), `style(rescale) nor` (m06) | {} |
  | `rescale`, `r`, `re`, `resc`, `rescal`, `rescale noyrescale`, `res noyr` (k11), `style(rescale)`, `style(combine)`, `compact style(rescale)` (m04) | {x,y} |
  | `yrescale`, `yr`, `yresc`, `yrescal`, `yrescale noyrescale`, `yrescale norescale`, `norescale yrescale`, `nor yr`, `style(compact) yrescale`, `compact yrescale`, `rows(1) yrescale`, `total yrescale` | {y} |
  | `xrescale`, `xr`, `xresc` | {x} |
  | `style(rescale) noyrescale` | {x} |

  Pre-fix: AttributeError (the function does not exist).
- Test: `…::test_rescale_tokens_are_not_named[by_raw]` — no `by() sub-option(s) not implemented` warning for `yrescale`, `xr`, `r`, `norescale`, `noyrescale`. `rows(2) yrescale` names only `rows(2)`. `r(1)` and `rescale(1)` are still named. Pre-fix: named.
- Test: `…::test_style_rescale_is_named_with_its_own_note` — `style(rescale)` gives exactly the TR-10.13 note and is absent from the generic line. `style(compact)` is in the generic line.
- Test: `…::test_hostile_by_text_never_raises` — 100,000 tokens, unbalanced quotes and parentheses, `title("yrescale")` (not read), `yrescale(`, `None`, `42`, `b"x"`. Each returns a frozenset, and the 100k case takes under 1 s.
- Test: `TestPanelsShareOneScale::test_default_shares_x_and_y[mode]` — c01: every panel's `x_range` is one object and so is every `y_range`. Its `renderers` is the union (length = the sum of the panels'). `_emulated_hull` equals the fixture's c01 panel yscale [12,41] and xscale [1760,4840]. Pre-fix: distinct objects, hulls 12-34 / 14-41.
- Test: `…::test_total_missing_and_multi_var_panels_share[mode]` — c13, c14, c27.
- Test: `…::test_auto_ranged_layers_share[mode]` — histogram (c22) and kdensity (c26): one object, `renderers == []`.
- Test: `…::test_date_and_log_axes_share[mode]` — c23 (`%td` x, in units per S05) and c18 (`yscale(log)`): the emulated hulls equal the fixture.
- Test: `…::test_a_linked_by_graph_shares[mode]` — `by(foreign)` inside `link()`: the shared range's renderers include each panel's CDSView renderer.
- Test: `…::test_reverse_is_kept_on_the_shared_range[mode]` — `xscale(reverse)`: the shared x range is `flipped`.
- Test: `…::test_qualified_rows_only[mode]` — d47 `if price>6000`: the emulated y hull is [12,26].
- Test: `TestRescaleGivesEachPanelItsOwn::test_yrescale_xrescale_rescale[mode]` — c02, c03, c04, c05, e01: the rescaled letter has distinct objects whose emulated hulls equal the fixture per panel; the other letter is shared.
- Test: `…::test_count_ticks_are_per_panel[mode]` — `natscale_axes_truth.json` `by` record `by(foreign, yrescale) ylabel(#5)`: panel ticks 10(5)35 and 15(5)40; c30 x 2000(1000)5000 and 1500(500)3500. Pre-fix: 10(10)40 on both.
- Test: `…::test_range_is_not_applied_on_a_rescaled_axis[mode]` — d19, d44, f01 (one panel) and e10: no panel's hull reaches 0 (`_dash_range_hull` or `_emulated_hull`), and the one note is identical in both modes. d40/d41: range() still applies on the non-rescaled axis ([0,4840] / [0,41]). Pre-fix: one Range1d -2.05..43.05.
- Test: `…::test_count_ticks_ignore_range_on_a_rescaled_axis[mode]` — m07: ticks 10(5)35 and 15(5)40, and no tick or hull at 0.
- Test: `…::test_labels_and_ticks_still_widen_each_panel[mode]` — c20 `ylabel(0(10)50)` gives a hull of 0..50 per panel (distinct objects); d48 `ytick(0 60)` gives 0..60.
- Test: `…::test_reverse_and_log_survive[mode]` — e03: each panel's y range is reversed (`_dash_range_reversed`); e04: each panel's left axis is a `LogAxis`.
- Test: `TestTheSecondAxisIsShared::test_y2_and_x2[mode]`:
  - c16, k07 and f02: one Range1d whose `_dash_range_hull` equals [3291,15906], [0,15906] with `yscale(range(0) axis(2))`;
  - c17, e12 and f03: per panel under y/xrescale ([3291,15906] / [3748,12990]), with range(0) not applied.

  Pre-fix: per-panel y2.
- Test: `TestAfterAFilterMove::test_the_shared_range_spans_the_union_after_a_move[saved|served]`:
  - served: `_fire` a price RangeSlider to 3291-7075.5; every panel still shares one y object, and its `_emulated_hull` equals the union of the moved panels' rows (pandas over `price <= 7075.5`), matching `test_mode_parity._saved_with_qualifier`;
  - saved: the filter callback's args reference no range model, and every panel keeps the one object.
- Test: `TestSharingStaysInOneGraph::test_two_by_graphs[mode]`, `::test_by_graphs_in_tabs[mode]`, `::test_by_graph_in_a_link_group_with_a_plain_graph[mode]` — no range object is shared across graphs, and each union holds only that graph's panel renderers.
- Test: `TestTheNoteReachesTheUser::test_one_note_per_letter_in_both_modes` — `rescale yscale(range(0)) xscale(range(0))` gives exactly two notes (y, x) in both modes, with the same text. Without by(), or with no range(), there is none.
- Test: `TestTheNoteReachesTheUser::test_served_build_raises_the_range_note` — in `ServerAppBuilder.build()`'s own warnings, and exactly once over build plus session.
- Test: `TestTheHelpers::test_share_by_scales_units`:
  - a single panel is a no-op;
  - mixed `[]`/list renderers expand;
  - an empty panel;
  - renderer de-duplication;
  - an idempotent second call;
  - `#N` start and end survive (share-before-ticks order);
  - `_dash_common_count_ticks(figs, letters=("x",))` leaves y alone;
  - with `made`, `_dash_hull_ranges` gives one object.
- Test: `TestTheFixtureIsPinned::test_meta_stamp` and `::test_every_probe_has_panels`.

### P0.2: `test/test_by_scales_chrome.py` (new, task 10-16; real time, `test/range_probe.py`)

- Test: `TestTheBrowserDrawsOneScale::test_saved_page_initial_and_after_a_move` — the c01 data with a price RangeSlider. Initially both panels' BokehJS y start and end are equal (expected ≈ 10.55 / 42.45). After `move_range_slider(0.3)` and `wait_settled(3)` they are still equal (≈ 11.47 / 23.05). Pre-fix: 10.9-35.1 vs 12.65-42.35.
- Test: `…::test_served_document_initial_and_after_a_move` — `file_html` of the served document before and after `_fire`: equal across panels each time.
- Test: `…::test_yrescale_panels_differ` — y differs between panels and x is equal, before and after the move. Both panels' y change after the move (the per-panel control).
- Test: `…::test_auto_ranged_histogram_panels_share_after_a_move` — histogram panels: one y range, equal before and after.
- Test: `…::test_hundred_panels_settle` — 100 by-groups (`g = _n % 100`, 5 rows each) and one move: equal ranges across all panels within 3 s, and `js_errors() == []`. Record the measured seconds.
- Test: `…::test_the_probe_never_forces_an_update` — `range_probe.py`'s source contains neither `update_dataranges` nor `request_paint`.

### P0.2: Stata (task 10-21)

- **Truth block BSC-01..BSC-07** (`test/test_wp29_truth.cscript`): the live twoway `.Graph.graphs[k].plotregion1.{y,x}scale.min/max` against dash's saved page (`dash scatter …, by(…) saving()` read by the model reader) and the served app (import, then `make_document`). The pytest emulated-hull rule is ported into the python reader.

  | Case | What | Pass condition |
  |---|---|---|
  | BSC-01 | `by(foreign)` | one shared y and one shared x object, hull = live min/max |
  | BSC-02 | `yrescale` | per panel |
  | BSC-03 | `rescale` and `r` | per panel on both axes |
  | BSC-04 | `total` | the Total panel shares |
  | BSC-05 | yaxis(2) | y2 hull = live `.yaxis2.plotregion.yscale` |
  | BSC-06 | `yrescale ylabel(#5)` | ticks = live `.yaxis1.major` per panel |
  | BSC-07 | `yrescale yscale(range(0))` | no 0 in any panel; live curmin 10 |
- **`test/test_by_suboptions.cscript`** (after BYS-06; the header lists "BSC-08 through BSC-10"):

  | Case | What | Pass condition |
  |---|---|---|
  | BSC-08 | `yrescale xrescale rescale r norescale noyrescale` | none in the not-implemented line (`_bys_render`); `style(rescale)` gives its own note |
  | BSC-09 | `dash scatter mpg weight, by(foreign, yrescale) yscale(range(0)) saving()` | the TR-10.16 note exactly once in the log |
  | BSC-10 | the same graph, `dash build, saving("<app>") replace server` | the note exactly once in the log (the HC5-08 pattern) |

**Mutation table:**

| break this | test that must die |
|---|---|
| route `axis(2)` after `_dash_opts_repeats` | AX-07 |
| report rows in insertion order | AX-04 |
| `_dash_rep_toks(sub, 1)` for the double-comma test | AX-05, AX-01 |
| `strofreal(N)` in the message | AX-03 (1e9 row) |
| drop the `range_name` on `Span` | `test_yline_axis2` |
| widen y2 by ytick under norescale | `test_extents` |
| note the unused second axis in the session only | `test_served_note_is_raised_at_build_time`, `test_mode_parity` `_MUST_WARN` |
| share AFTER `_dash_common_count_ticks` | `test_share_by_scales_units` (`#N` start/end) |
| keep `range()` values on a rescaled axis | `test_range_is_not_applied_on_a_rescaled_axis`, BSC-07 |
| omit `_rescale=_brs` in one served `_dash_figure_for` call | `test_mode_parity` "by(foreign, yrescale) yscale(range(0))" |
| share across graphs (one global cache) | `TestSharingStaysInOneGraph` |
| forget `"_dash_share_by_scales"` in the copy list | `TestTheServedAppDefinesEveryNameItReads` |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| axis(2) options draw on the second axis | pytest `test_axis2_suboptions.py` | axis2_truth.json | yes |
| routing holds after a filter move | pytest (served `_fire`) | none | yes |
| spec after the merge, refusals and their order, double comma, accepted spellings, exhaustion | cscript AX-01..AX-08 (twoway asked in the same run) | none | n/a (Stata) |
| twoway's axis vs dash's, live | truth block AX-11..AX-18 | none | yes |
| parity of the routed cases, before and after a move | `test_mode_parity.py` CORPUS and MOVE_CORPUS | none | yes |
| registries | `test_function_test_map.py`, `test_program_coverage_map.py`, both served guards | none | n/a |
| by() shared scale, rescale, y2/x2, notes, sharing per graph | pytest `test_by_scales.py` | by_scales_truth.json, natscale_axes_truth.json | yes |
| browser union after a move; 100 panels | pytest + Chrome over CDP (`test_by_scales_chrome.py`) | none | yes |
| twoway's panel scales vs dash's, live | truth block BSC-01..BSC-07 | none | yes |
| sub-options not named; range note in the Stata log on a saved and a served build | cscript BSC-08..BSC-10 | none | yes |

Acceptance criteria:

- **AC-10.1** `python3 -m pytest test/test_axis2_suboptions.py test/test_by_scales.py test/test_by_scales_chrome.py test/test_mode_parity.py test/test_suboption_warnings.py test/test_server_facets.py test/test_natscale_axes.py test/test_unsupported_report_is_true.py test/test_option_validation.py test/test_abbreviations.py test/test_textbox_grammar.py -q -n0` passes, with the Chrome tests run (not skipped) on the maintainer's machine.
- **AC-10.2** The `S10` blocks of `test/test_wp29_truth.cscript` print `AX-11 PASS` … `AX-18 PASS` and `BSC-01 PASS` … `BSC-07 PASS` under `WP29_ONLY=S10`. `test_twoway_option_parity.cscript` prints `AX-01 PASS` … `AX-08 PASS`. `test_by_suboptions.cscript` prints `BSC-08 PASS` … `BSC-10 PASS`. None prints `FAIL` or `SKIP`.
- **AC-10.3** Both served guards, `test_function_test_map.py`, `test_program_coverage_map.py` and `test_fixtures_are_committed.py` pass.
- **AC-10.4** BUGS.md carries the P0.5 and P0.2 entries closed (`- Resolution: Fixed <ddmonyyyy> (WP-29, P0.5).` / `(WP-29, P0.2).`), naming existing tests. Their `WP29_OPEN` keys are gone. `grep -c '<!-- WP-29 P0.5 -->\|<!-- WP-29 P0.2 -->' CHANGELOG.md` prints 0. `test_tracking_documents.py` passes.
- **AC-10.5** `git log --format=%s wp29-p0..wp29-s10` shows exactly two commits, ending `(WP-29 P0.5)` and `(WP-29 P0.2)` in that order. Neither message matches `claude|anthropic`.

## Tasks

**Commit boundary.**
- Tasks 10-01 to 10-13 form the P0.5 commit. Its subject is `Draw axis(#) options on the axis they name (WP-29 P0.5)`, and 10-13 makes it.
- Tasks 10-14 to 10-23 form the P0.2 commit. Its subject is `Share one scale per axis across by() panels (WP-29 P0.2)`, and 10-23 makes it.

Both commits go on worktree branch `wp29-s10` (`/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s10`), after one full suite run each. Each body opens with its saved failure text, then the measured defect, then what changed and where, then the line forms in Notes.

The merger lands them on `wp29-p0` in order with `patch -p1` (index step 1). Every Stata run is `scripts/stata_slot.sh <scratch>/s10 <file>.do` with `dash_nobrowser=1`. No AI references anywhere. Never stage `CLAUDE.md`, `.gitignore` or scratch files.

<task type="auto" id="10-01">
  <name>Extract the axis(2) truth fixture</name>
  <files>scripts/extract_axis2_truth.do, test/fixtures/axis2_truth.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[
First run `gitnexus analyze` in the worktree, then `gitnexus_impact({target, direction: "upstream"})` for `_dash_route_axis2`, `_dash_rep_cat`, `_dash_route_axis_titles`, `_dash_lone_second_axes`, `_textbox_canon`, `_dash_finish_secondary_axes`, `_dash_reference_lines`, `_dash_refline_draw` and `ServerAppBuilder.build`. Write each result to `<scratch>/10-impact.txt`. Report any HIGH or CRITICAL result to the orchestrator before editing those symbols. If the index cannot be built, record the grep table from this section's Evidence instead and say so.

Create `scripts/extract_axis2_truth.do` as "Stata truth" specifies:
- the `W29_REPO` guard and `adopath ++`;
- the `_ticks`/`_m` member readers (read `.Graph.<ax>.<set>.dlg_tickpos.arrnels` first, then each element; per plotregion `yaxis_dexes`, `xaxis_dexes`, `yscale`/`xscale` `curmin`/`curmax`/`transform.stylename`/`reverse.istrue`, `_xylines[l].z` with `gdi_y0 == gdi_y1` for orientation);
- every probe of "P0.5: twoway, measured" run under `capture noisily` with its own `log using` so the first error line is captured, each held in `local o` with compound quotes;
- a `python:` block that writes `test/fixtures/axis2_truth.json` with the `_meta` keys `stata_version`, `born_date`, `dash_commit`, `extracted`, `method` ("`.Graph` members via graph_g.class ParseAndLogAxes") and `caveats`.

Run it through the two-line driver of "Stata truth". `git add -f` the fixture, and add `axis2_truth.json` to the committed-fixture list in `test/test_fixtures_are_committed.py`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^r([0-9]*);' <scratch>/s10/run_extract_axis2_truth.log` prints 0. `python3 -c "import json;d=json.load(open('test/fixtures/axis2_truth.json'));m=d['_meta'];assert all(k in m for k in ('stata_version','born_date','dash_commit','extracted'));p={x['id']:x for x in d['probes']};print([float(v) for v in p['c2']['axes']['yaxis2']['major']], p['c33']['rc'])"` prints `[5000.0, 10000.0, 15000.0] 198` (the probe list is `probes`, each with `id`, `command`, `rc`, `error`, `axes` keyed `yaxis1 yaxis2 xaxis1 xaxis2` holding `major majornl minor minornl` lists, and `plotregions`). `python3 -m pytest test/test_fixtures_are_committed.py -q -n0` passes. `<scratch>/10-impact.txt` exists.]]></verify>
  <done>twoway's axis(#) routing, extents, spellings and refusals were recorded from Stata in a committed-to-be fixture with its D12 stamp, and the blast radius of the P0.5 symbols was recorded.</done>
</task>

<task type="auto" id="10-02">
  <name>Write the failing axis(2) renderer tests</name>
  <files>test/test_axis2_suboptions.py</files>
  <action><![CDATA[
Create `test/test_axis2_suboptions.py` with every test listed under "P0.5: test/test_axis2_suboptions.py", using exactly those class and test names. Build figures as `test/test_dual_axis.py::_lone_figure` does (import its `_make_spec_and_data`, or write a local twin that passes `var_labels` explicitly, A7). For served moves use `test_mode_parity._served` and `test_mode_parity._fire`. Use `dr._dash_range_hull` for hulls. Load `test/fixtures/axis2_truth.json`, failing with `pytest.fail` naming task 10-01 if it is absent. The unit tests reference `dr._dash_route_axis_options` and `dr._dash_axis_number`, which do not exist yet, so they must fail with AttributeError and not with a collection error: reference them inside the tests, not at import. Do not touch `dash_render.py`.

Run `python3 -m pytest test/test_axis2_suboptions.py -q -n0 -p no:cacheprovider 2>&1 | tail -40` against the unmodified batch-2 base. Save the output to `<scratch>/10-P0.5-failure.txt`, headed with the sha in `<scratch>/batch-2-base.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[The run collects without error. `test_ylabel_axis2[saved]` fails asserting the right ticker, `test_yline_axis2[served]` fails on `y_range_name == 'default'`, and `test_route_axis_options_unit` fails with AttributeError. `TestTheTitleRouteKeepsTheDefault` passes (a guard; list it as such in the failure file). `<scratch>/10-P0.5-failure.txt` exists.]]></verify>
  <done>Every P0.5 renderer regression test existed and failed for its recorded reason at the batch-2 base, with the guard tests named separately and nothing committed.</done>
</task>

<task type="auto" id="10-03">
  <name>Write the failing AX Stata cases</name>
  <files>test/test_twoway_option_parity.cscript</files>
  <action><![CDATA[
Append AX-01..AX-08 to `test/test_twoway_option_parity.cscript` as specified under "P0.5: Stata". Place them after the last case block (S02's JO cases, merged in batch 1) and before the `// Summary` banner. Add one header "Groups:" line per case after the TP-16 line.

- Use the script's `_ztp_run` (log capture, `r(rc)`), `cert_log_has` and `_ztp_hasval`.
- Run twoway's command under its own named log, so its first error line can be read and used as dash's needle.
- Every failure appends to `nfail`/`faillist` and prints `AX-0n FAIL: <why>`, and the script continues.
- AX-01, AX-02 and AX-08's `_dash_axreq` check call Mata functions that do not exist yet. Wrap them in `capture` and record the rc as a failure, so the script runs to the end.

Run the script through the driver (`printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_twoway_option_parity.cscript" > <scratch>/s10/run_parity.do`, then `dash_nobrowser=1 <repo>/scripts/stata_slot.sh <scratch>/s10 <scratch>/s10/run_parity.do`). Append every AX FAIL line from `<scratch>/s10/run_parity.log` to `<scratch>/10-P0.5-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "AX-0[1-8] FAIL" <scratch>/s10/run_parity.log` is at least 6. AX-01, AX-02, AX-03, AX-05 and AX-07 fail; AX-06 may pass for the forms dash already accepts. `grep -c "TP-1[0-6] PASS\|JO-[0-9]* PASS" <scratch>/s10/run_parity.log` equals the count before the edit (no earlier case broke). The failure file holds the AX lines.]]></verify>
  <done>The Stata-side P0.5 regression cases existed, measured twoway in the same run, and failed against the batch-2 base for their recorded reasons.</done>
</task>

<task type="auto" id="10-04">
  <name>Route every axis family in Mata</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
In `dash_parse.mata`, next to `_dash_route_axis2` (about :4884 at 7421d3d; S03 may have edited it, so edit S03's version):
- Add `real scalar _dash_axis_num(string scalar arg)` per TR-10.2.
- Rewrite `_dash_route_axis2(opts)` per TR-10.1 and TR-10.3: the seven-family table for x and y with twoway's full names and minimums; option names matched only when typed in lower case; the double-comma test with `_dash_rep_split` applied twice; the first lower-case axis word gives N; plurals renamed; N=2 rewrites for title, label, tick, line and scale; everything else returned byte for byte.
- Keep the signature and the `if (!any) return(opts)` early return, and add no regex.
- Update the header index (dash_parse.mata:245-247) for the new behaviour and add one line for `_dash_axis_num`.

Keep S03's empty-text title behaviour as it is.
  ]]></action>
  <verify><![CDATA[The parity script re-run through the driver prints `AX-01 PASS` and `AX-02 PASS`. `python3 -m pytest test/test_program_coverage_map.py -q -n0` fails ONLY for the unmapped `_dash_axis_num` (mapped in 10-05).]]></verify>
  <done>dash's Mata route rewrote every axis family's axis(2) form to dash's second-axis key, dropped axis(1), renamed plurals and left every refused form as typed.</done>
</task>

<task type="auto" id="10-05">
  <name>Add the axis-request scan and check</name>
  <files>dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
Add `_dash_axreq_clear()`, `_dash_axreq_add(string scalar opts, real scalar seg)` and `real scalar _dash_axreq_check(string scalar ys, string scalar xs)` per TR-10.4. The external is `string matrix _dash_axreq` with 9 columns. `_dash_axreq_add` preallocates after a counting pass and never grows a row at a time. `_dash_axreq_check` sorts with `order()` on (side, family, seg, position), reports the first failing row in the A2 order through `_dash_say("err", ...)` with N printed as `strtrim(strofreal(N, "%11.0f"))`, and clears the matrix on both paths.

Add the three functions to the header index. In `test/program_coverage_map.py`:
- map `_dash_axis_num` to `("test_twoway_option_parity.cscript:AX-02",)`;
- map the three axreq functions to `("test_twoway_option_parity.cscript:AX-03", "test_twoway_option_parity.cscript:AX-04")`;
- put `"test_twoway_option_parity.cscript:AX-01"` first in `_dash_route_axis2`'s tuple.

Keep keys in alphabetical place (R2).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_program_coverage_map.py -q -n0` passes. A scratch do-file run through `stata_slot.sh` that does `mata: _dash_axreq_clear(); _dash_axreq_add("ylabel(1, axis(3)) xscale(log axis(3))", 1); _dash_axreq_check("1 2", "1")` prints `xscale(log axis(3)) not allowed, xaxis3 does not exist` and returns 198.]]></verify>
  <done>Mata could record every axis option's request and refuse the first failing one with twoway's message, in twoway's order, keeping no typed text afterwards.</done>
</task>

<task type="auto" id="10-06">
  <name>Wire the route and check into dash.ado</name>
  <files>dash.ado</files>
  <action><![CDATA[
In `dash.ado`, per TR-10.4 and TR-10.5:
1. Declare `ytick2(string asis) xtick2(string asis) yline2(string asis) xline2(string asis)` in `_dash_parse_graph_opts` (702-722) and `_dash_parse_plot_opts` (940-960), and add the four `sreturn local` lines after `sreturn local xscale2` (833) and the four `sreturn local g_*` lines after `sreturn local g_xscale2` (1245).
2. Add `ytick2 xtick2 yline2 xline2` after `xscale2` in all seven graph-key lists (4090, 4624, 4656, 4746, 4800, 4831, 5086).
3. Add `ytick2=axislist xtick2=axislist` to the graph rule table (1949-1951), and append the four Mata names at the END of `_needed` (232-246).
4. In `_dash_process_segment`, keep the raw option text in `_opts_pre` before the route at 3922. After `_dash_parse_plot_opts` succeeds, `c_local _seg_axreq_raw : copy local _opts_pre`, and set `c_local _seg_yaxis_out`/`_seg_xaxis_out` from the normalised yaxis/xaxis beside 4082.
5. In `_dash_plot`:
   - call `mata: _dash_axreq_clear()` beside `global dash__g_by ""`;
   - keep the raw `gopts_raw` before its route at 4641;
   - in the segment loop, reset the three new `_seg_*` locals beside 4740, then after `_dash_process_segment` call `mata: _dash_axreq_add(st_local("_seg_axreq_raw"), k)` and accumulate `_g_ys`/`_g_xs` with `: list uniq`;
   - after the after-comma merge (after 4836) call `mata: _dash_axreq_add(<raw gopts>, n_segs + 1)`, then `mata: st_local("_axrc", strofreal(_dash_axreq_check(st_local("_g_ys"), st_local("_g_xs"))))` and `if `_axrc' exit 198`.

Use `macval()` wherever the raw text is copied.
  ]]></action>
  <verify><![CDATA[The parity script run through the driver prints `AX-01` to `AX-08 PASS` except any case that needs the renderer (none of AX-01..08 does), and no earlier TP or JO case fails. `python3 -m pytest test/test_unsupported_report_is_true.py test/test_option_validation.py test/test_abbreviations.py -q -n0` shows only the failures 10-09 will flip (the declared counts 165/68, the unclassified four options, `_DASH_ONLY`), listed in `<scratch>/10-pending-flips.txt`.]]></verify>
  <done>dash.ado routed axis(2) on every family before the repeat merge, kept both axes' copies, and refused twoway's refused forms with twoway's message, rc and order.</done>
</task>

<task type="auto" id="10-07">
  <name>Write the Python route twin</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
In `dash_render.py`, per TR-10.2, TR-10.6 and TR-10.7:
- Change `_TEXTBOX_SUBOPTS`' `("axis", "axis")` to `("axis", "ax")`.
- Add `_dash_axis_number(arg)` and the constant `_DASH_AXIS2_KEYS` beside `_DASH_LONE_AXIS_OPTIONS` (1743).
- Rewrite `_dash_route_axis_titles` (1747-1802) to use the first lower-case axis word and `_dash_axis_number`.
- Add `_dash_route_axis_options(spec)` after it.
- Extend `_DASH_LONE_AXIS_OPTIONS` with `ytick`/`yline` (and the x forms), and make `_dash_lone_second_axes` join line copies (A8).
- In `DashRenderer.__init__` (25022-25025) and `ServerAppBuilder.__init__` (28285-28288), call `_dash_route_axis_options` between the titles route and the lone-axis rewrite.

Map `_dash_axis_number` and `_dash_route_axis_options` in `test/function_test_map.py` to `test/test_axis2_suboptions.py::TestTheRouteUnit::…` in alphabetical place. Copy nothing into the served app (TR-10.10).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis2_suboptions.py -q -n0 -k "TheRouteUnit or axis_spellings or ytitle_ax2 or axis1_and_unqualified or merged_line or lone_second_axis or ylabel_axis2 or yscale_log"` passes. `python3 -m pytest test/test_textbox_grammar.py test/test_function_test_map.py -q -n0` passes.]]></verify>
  <done>A hand-made spec's axis(2) options were routed by the renderer exactly as dash.ado routes them, the ax spelling and twoway's axis-number rule held, and a lone axis kept both its line copies.</done>
</task>

<task type="auto" id="10-08">
  <name>Draw second-axis ticks, lines and notes</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
In `dash_render.py`, per TR-10.8 and TR-10.9:
- Give `_dash_refline_draw` the `range_name="default"` parameter.
- Make `_dash_reference_lines` draw `yline2`/`xline2` on `y2`/`x2` when the range exists.
- In `_dash_finish_secondary_axes`, read `{n}tick2` before the range is set (widening unless norescale) and apply it through `_dash_apply_tick_option` whether or not `{n}label2` is given.
- Add `_dash_unused_second_axis_notes(graph)`. Call it once per graph at the top of `DashRenderer._build_figures`' "3. Build figures" loop, raising through `_dash_warn_once`. Add `ServerAppBuilder._plan_graph_notes()`, called beside `self._plan_by_groups()` in `build()` (29175), which raises the same notes from `self.spec` without loading the frame.
- The served template must NOT call the note helper.

Map both new names in `test/function_test_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis2_suboptions.py -q -n0` passes completely. `python3 -m pytest test/test_resource_limits.py -q -n0 -k DefinesEveryName` and `python3 -m pytest test/test_statistical_helpers.py -q -n0 -k CarriesEveryName` pass.]]></verify>
  <done>yline2/xline2 Spans and ytick2/xtick2 ticks were drawn on the second axis in both modes with twoway's extents, and an unused second-axis option was named once at build time in both modes.</done>
</task>

<task type="auto" id="10-09">
  <name>Flip the pinned option tables</name>
  <files>test/test_suboption_warnings.py, test/test_unsupported_report_is_true.py, test/test_option_validation.py</files>
  <action><![CDATA[
Flip each of the following, each with a comment naming WP-29 P0.5:
- `test_suboption_warnings.py` SUBOPTIONS entry `"yline axis"` (:75-76): `axis(2)` becomes `axis(3)` and the named list `["axis(3)"]`. Add `({"yline": "20 25, axis(2)"}, [plot_for("scatter"), dict(plot_for("scatter"), options={"yaxis": "2"})])` to `TestTheHonouredOnesStayQuiet`'s parameters.
- `test_unsupported_report_is_true.py:592-593`: `165` becomes `169` and `68` becomes `72`, with the comment updated. Add LIVE_VALUES entries for `ytick2`, `xtick2`, `yline2` and `xline2`, following the `ylabel2` entry at :541-542 (a `yaxis(2)`/`xaxis(2)` layer and two values that draw differently, e.g. `("ytick2", "5000", "9000")` and `("yline2", "5000", "9000")`).
- `test_option_validation.py::_DASH_ONLY`: add `"xtick2", "ytick2"` with a comment that twoway refuses those names outright.

Record one `Flipped: <node> -- <old expectation> was wrong because <why>` line per change in `<scratch>/10-flips-P0.5.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_suboption_warnings.py test/test_unsupported_report_is_true.py test/test_option_validation.py -q -n0` passes with no new skips.]]></verify>
  <done>The three option tables that pinned the misrouted axis(2) or the old declaration counts pinned the routed behaviour, with each flip recorded.</done>
</task>

<task type="auto" id="10-10">
  <name>Extend parity, served copy and spelling tests</name>
  <files>test/test_mode_parity.py, test/test_textbox_grammar.py, test/test_abbreviations.py</files>
  <action><![CDATA[
In `test/test_mode_parity.py`:
- In `_axes.one`, record `"range_names": (a.x_range_name, a.y_range_name)` (a Bokeh axis carries both) and, for a CustomJSTicker, `sorted((a.ticker.args or {}).get("extra", []))`. In `_annotations`, record a Span's `y_range_name`/`x_range_name`.
- Append the CORPUS cases "ylabel/yscale/yline/ytick axis(2) routed", "xlabel/xscale/xline/xtick axis(2) routed", "axis(2) under by()" and "ylabel2 with no second-axis layer". Add a `_MUST_WARN` entry for the last, with the TR-10.9 text prefix.
- Append the MOVE_CORPUS case "yaxis(2) with axis(2) options, dropdown". `ALLOWED` is never edited (R6).

In `test/test_textbox_grammar.py`, update the `TestTheFixtureIsPinned` docstring and the "Boundaries: recorded, not pinned" note to say AX-03 pins the refusals.

In `test/test_abbreviations.py`, add `TestTheAxisRouteKnowsDashsSpellings` with:
- `test_mata_family_minimums_match_twoway`: parse the family table in `dash_parse.mata` and assert the minimums 2/2/3/4/3/3/3 and the plural full names;
- `test_the_seven_graph_key_lists_agree`: every `foreach gk in`/`foreach gkey in` list of `dash.ado` is identical and holds `ytick2 xtick2 yline2 xline2`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py test/test_textbox_grammar.py test/test_abbreviations.py -q -n0` passes. A deliberate local revert of one list entry in dash.ado makes `test_the_seven_graph_key_lists_agree` fail; restore it.]]></verify>
  <done>Parity profiles saw axis routing and both modes agreed on the new cases before and after a move, and the spelling and key-list guards pinned the dash.ado wiring.</done>
</task>

<task type="auto" id="10-11">
  <name>Certify routing against live twoway</name>
  <files>test/test_wp29_truth.cscript, test/program_coverage_map.py</files>
  <action><![CDATA[
Read `test/test_wp29_truth.cscript` (S01's scaffold, with batch-1 blocks). Append, above `* ==== append new blocks above this line ====` and after every earlier block, the block `* ==== S10 P0.5: axis(#) routing ====` … `* ==== end S10 P0.5 ====`. Gate it with `local only : env WP29_ONLY` and `if inlist("`only'", "", "S10") {`, and print `S10 start`/`S10 end` with `c(current_time)`.

Above the `local only` line, outside the gate, define the block's helpers:
- a `python:` reader of a saved page's models (the `_tbg_models` pattern) and of a served app (import with importlib, `make_document(Document())`, walk `doc.roots` references);
- the case helper the scaffold provides, or, if it has none, `_w29s10_expect`/`_w29s10_done` with the bodies of test_gaps2_truth.cscript:51-70.

Inside the gate, write AX-11..AX-18 as "P0.5: truth block" specifies. Each runs the twoway command, reads `.Graph` members, runs the same dash command with `saving()` and `dash build, saving("<app>") server replace`, and compares. Add `test_wp29_truth.cscript:AX-11` as a second reference for `_dash_route_axis2` in `test/program_coverage_map.py`.

Run it with the driver under `WP29_ONLY=S10`.
  ]]></action>
  <verify><![CDATA[`grep -c "AX-1[1-8] PASS" <scratch>/s10/run_test_wp29_truth.log` prints 8. `grep -c "FAIL\|SKIP" <scratch>/s10/run_test_wp29_truth.log` prints 0. `python3 -m pytest test/test_cscript_hygiene.py test/test_program_coverage_map.py -q -n0` passes.]]></verify>
  <done>Stata itself certified, in the S10 block of the WP-29 truth script, that dash's saved page and served app draw every axis(2) option on the axis twoway draws it on.</done>
</task>

<task type="auto" id="10-12">
  <name>Document axis(#) routing in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
Rewrite `dash.sthlp`:
- :2540-2553 (Secondary axes):
  - `axis(2)` on `ytitle()`, `ylabel()`, `ytick()`, `yline()` and `yscale()` (and the x forms, twoway's spellings and plurals, the minimum `ax`, lower case) draws on the second axis, and `axis(1)` on the first;
  - a number that is not a whole number within twoway's range means axis 1;
  - an axis no layer uses, a repeated `axis()`, an `AXIS()` in capitals and a second comma are refused, r(198), with twoway's message;
  - `ymlabel()`/`ymtick()` are not drawn on either axis;
  - delete "still named, not read" and change "refuses all twelve" to "refuses all sixteen".
- :2556-2562 (lone axis): the axis(2) forms style the one axis, and axis-1 options are refused as twoway refuses them (SD-1).
- Add synopt rows `ytick2(rule)`, `xtick2(rule)`, `yline2(linelist)` and `xline2(linelist)` to the table at 2564-2577 (dash's own spellings, no abbreviation).
- :549-556: `axis(1)`/`axis(2)` and its `ax` spelling.
- The Reference lines entry (2886-2890) and "Ticks without labels" (2523-2530): `axis(2)` puts the line or tick on the second axis's scale; lines never widen an axis, ticks do.
- Under Boundaries, say that `add` on a routed label is named.

Grep `test/test_help_claims_*.py`, `test/test_help_claims_*.cscript` and `test/test_help_conformance.py` for each changed sentence and update any pin.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_abbreviations.py -q -n0` passes (`TestEveryDashOnlyOptionIsDocumented` finds the four synopt rows). `grep -c "still named, not read" dash.sthlp` prints 0.]]></verify>
  <done>The help stated twoway's axis(#) rule, the refusals, the lone-axis rule and dash's four new second-axis options.</done>
</task>

<task type="auto" id="10-13">
  <name>Close P0.5 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
In BUGS.md, close IN PLACE the entry S01 opened for P0.5. Its exact title is the value of key `"P0.5"` in `WP29_OPEN`:
- `- [ ]` becomes `- [x]`.
- File Names and Line Numbers: dash_parse.mata `_dash_route_axis2`, `_dash_axis_num`, `_dash_axreq_*`; dash.ado `_dash_plot`, `_dash_process_segment` and both syntax blocks; dash_render.py `_TEXTBOX_SUBOPTS`, `_dash_route_axis_titles`, `_dash_route_axis_options`, `_dash_lone_second_axes`, `_dash_reference_lines`, `_dash_refline_draw`, `_dash_finish_secondary_axes`, `_dash_unused_second_axis_notes`, `ServerAppBuilder._plan_graph_notes`.
- The Resolution: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.5). axis(#) on the title, label, tick, line and scale families is routed before the repeat merge in Mata and by the renderer twin, drawn on the second axis in both renderers, and refused as twoway refuses it, in twoway's order. Pinned by test/test_axis2_suboptions.py::TestTheSecondAxisOptionsReachTheSecondAxis::test_ylabel_axis2, test/test_axis2_suboptions.py::TestAfterAFilterMove::test_served_move_keeps_routing, test/test_twoway_option_parity.cscript AX-03, test/test_wp29_truth.cscript AX-11; fixture test/fixtures/axis2_truth.json. Residual, deferred (WP-29): axes 3-9 and yaxis(1 2) (B15), ymlabel/ymtick drawing, add on a routed label, the second axis's default title.`

Delete the `"P0.5"` key line from `WP29_OPEN` in `test/test_tracking_documents.py`.

In CHANGELOG.md, replace the two `<!-- WP-29 P0.5 -->` markers in place:
- In Results that change, ONE line ending `(WP-29, P0.5)` that names `ylabel(20 30, axis(2))`, `yscale(log axis(2))`, `yline(5000, axis(2))` and `xtick(…, axis(2))` (old: drawn on the first axis with a note; new: the second axis, saved and served), `ylabel(10 20) ylabel(5000 10000, axis(2))` (old: the first axis's labels lost) and `ylabels()`/`yticks()`/`ylines()` (old: dropped).
- In Changed behaviour, ONE line ending `(WP-29, P0.5)` naming the new refusals (an axis no layer uses, a repeated axis(), AXIS(), a second comma, axis-1 options on a lone yaxis(2) graph) and the new options `ytick2()`, `xtick2()`, `yline2()`, `xline2()`.

Run `python3 -m pytest test/ -q` once (the full suite, rule 4; read its log, never relaunch), then the parity script and the S10 truth block through the drivers. Run `gitnexus_detect_changes()` and check `git diff --cached --name-only` against the files of tasks 10-01 to 10-13. Grep the message for `claude|anthropic`. Commit on `wp29-s10` with the subject `Draw axis(#) options on the axis they name (WP-29 P0.5)`. The body opens with `<scratch>/10-P0.5-failure.txt` and then carries:
- `Regression: test/test_axis2_suboptions.py::<Class>::<test> -- failed at <batch-2 base sha> with <text>` lines;
- the `Flipped:` lines from `<scratch>/10-flips-P0.5.txt`;
- `Fixture: test/fixtures/axis2_truth.json (scripts/extract_axis2_truth.do)`;
- `BUGS.md: "<title>" (closed)`.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips. `python3 -m pytest test/test_tracking_documents.py -q -n0` passes. `grep -c '<!-- WP-29 P0.5 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-29, P0.5)' CHANGELOG.md BUGS.md` totals 3. `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0. `git log -1 --format=%s | grep -c '(WP-29 P0.5)$'` prints 1.]]></verify>
  <done>P0.5 was closed in BUGS.md naming existing tests, its markers were replaced, its tracking key was deleted, and one green commit on wp29-s10 carried the whole cycle.</done>
</task>

<task type="auto" id="10-14">
  <name>Extract the by() scales truth fixture</name>
  <files>scripts/extract_by_scales_truth.do, test/fixtures/by_scales_truth.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[
Run `gitnexus_impact` (upstream) for `_dash_parse_by`, `_dash_apply_scale_ranges`, `_dash_hull_ranges`, `_dash_common_count_ticks`, `DashRenderer._make_figure`, `DashRenderer._make_figure_body`, `DashRenderer._build_figures` and `ServerAppBuilder._plan_by_groups`, re-running `gitnexus analyze` first if the index is stale. Append the results to `<scratch>/10-impact.txt`. `_make_figure_body` is expected HIGH (index R8): report it to the orchestrator before task 10-18 edits it.

Create `scripts/extract_by_scales_truth.do` as "Stata truth" specifies:
- the `W29_REPO` guard;
- a `_rec` program reading the per-panel members listed there, with `capture` around each member that may be absent (`yaxis2`, `xaxis2`);
- the probes, each under `capture noisily` with `graph drop _all` after;
- the `data` block from `sysuse auto` and the `%td` set;
- a `python:` block that writes `test/fixtures/by_scales_truth.json` with `_meta`, `data`, `probes` and the derived `rescale_rule`.

Run it through the two-line driver, `git add -f` the fixture and add it to `test/test_fixtures_are_committed.py`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^r([0-9]*);' <scratch>/s10/run_extract_by_scales_truth.log` prints 0. `python3 -c "import json;d=json.load(open('test/fixtures/by_scales_truth.json'));p={x['id']:x for x in d['probes']};print('%g %g %g'%(float(p['c01']['panels'][0]['y']['min']),float(p['c01']['panels'][1]['y']['max']),float(p['c02']['panels'][0]['y']['max'])),d['rescale_rule']['style(rescale) noyrescale'],d['rescale_rule']['style(resc)'])"` prints `12 41 34 ['x'] []` (the probe list is `probes`, each with `id`, `command`, `rc`, `n` and `panels`, each panel with `title`, `y`, `x`, `y2`, `x2` dicts keyed `min max curmin curmax reverse transform major_min major_max major_delta view`). `python3 -m pytest test/test_fixtures_are_committed.py -q -n0` passes.]]></verify>
  <done>twoway's per-panel scales for every by() and rescale form were recorded from Stata, with the data they were measured on and a D12 stamp.</done>
</task>

<task type="auto" id="10-15">
  <name>Write the failing by() scale tests</name>
  <files>test/test_by_scales.py</files>
  <action><![CDATA[
Create `test/test_by_scales.py` with every test listed under "P0.2: test/test_by_scales.py", using exactly those names. Use the fixture's `data` block through `conftest.make_spec`/`make_data_json` (pass `var_labels` explicitly), the helpers `_emulated_hull` and `_served_doc`, and `test_mode_parity._fire`/`_saved_with_qualifier` for the move cases. Reference `dr._dash_by_rescale` and `dr._dash_share_by_scales` inside tests, never at import.

Run `python3 -m pytest test/test_by_scales.py -q -n0 -p no:cacheprovider 2>&1 | tail -60` on the tree the P0.5 commit left. Save it to `<scratch>/10-P0.2-failure.txt`, headed with `git rev-parse HEAD`. Do not commit.
  ]]></action>
  <verify><![CDATA[Collection succeeds. `test_default_shares_x_and_y[saved]` fails on distinct range objects; `test_count_ticks_are_per_panel[served]` fails with 10,20,30,40; `test_the_rescaled_axes_match_twoway` fails with AttributeError. The failure file exists and names every failing node.]]></verify>
  <done>Every P0.2 pytest regression test existed and failed for its recorded reason on the tree the P0.5 commit left, with nothing committed.</done>
</task>

<task type="auto" id="10-16">
  <name>Build the real-time Chrome range probe</name>
  <files>test/range_probe.py, test/test_by_scales_chrome.py</files>
  <action><![CDATA[
Create `test/range_probe.py` per TR-10.21: the free-port DevTools launch, the tornado websocket client with `max_message_size=1 << 28`, `RangeProbe` with `ranges()`, `move_range_slider(fraction)`, `wait_settled(timeout)`, `js_errors()`, and cleanup on exit. It never calls `update_dataranges` or `request_paint`.

Create `test/test_by_scales_chrome.py` with the six tests of "P0.2: test/test_by_scales_chrome.py":
- skip at module level when `responsive_probe.find_chrome()` is None, using the existing skip text convention;
- build saved pages with `DashRenderer(sp, dp).render(out)`;
- build served pages as `file_html` of a `make_document` document, before and after `test_mode_parity._fire`.

Run them on the tree the P0.5 commit left and append their output to `<scratch>/10-P0.2-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[On a machine with Chrome, `python3 -m pytest test/test_by_scales_chrome.py -q -n0` shows `test_saved_page_initial_and_after_a_move`, `test_served_document_initial_and_after_a_move` and `test_hundred_panels_settle` FAILING on unequal panel ranges. `test_yrescale_panels_differ` and `test_the_probe_never_forces_an_update` pass (guards). `grep -c "update_dataranges\|request_paint" test/range_probe.py` prints 0.]]></verify>
  <done>A real-time browser probe existed that observed the per-panel ranges after a filter move without forcing them, and the browser tests failed for the recorded reason before the fix.</done>
</task>

<task type="auto" id="10-17">
  <name>Parse the rescale sub-options</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Per TR-10.13 and TR-10.16:
- Extend `_DASH_BY_SUPPORTED` with the six rescale keys.
- Make `_dash_parse_by` consume their bare tokens and give `style(rescale|combine)` its own note.
- Add `_dash_by_rescale(by_raw)` after `_dash_parse_by`, and `_dash_by_range_notes(graph)` after it.
- Call `_dash_by_range_notes` beside `_dash_unused_second_axis_notes` in `DashRenderer._build_figures` and in `ServerAppBuilder._plan_graph_notes()`, raising each through `_dash_warn_once`.
- Add `"_dash_by_rescale"` to the served functions tuple after `"_dash_by_tokens", "_dash_parse_by",` (28638). Do not copy `_dash_by_range_notes` (TR-10.20).

Map `_dash_by_rescale` and `_dash_by_range_notes` in `test/function_test_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_scales.py -q -n0 -k "TheRescaleSubOptions or TheNoteReachesTheUser"` passes. `python3 -m pytest test/test_server_facets.py -q -n0 -k Unimplemented` fails only on the `norescale noixlabel` entry (flipped in 10-20).]]></verify>
  <done>Both modes read twoway's rescale rule from by(), stopped naming its sub-options, and named a dropped range() once at build time.</done>
</task>

<task type="auto" id="10-18">
  <name>Rescale each panel in both renderers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
Per TR-10.14 and TR-10.15:
- Add `rescale=frozenset()` to `DashRenderer._make_figure` and `_make_figure_body` and to `_dash_apply_scale_ranges`.
- Empty the rescaled letters' `_dash_scale_values` and set `fig._dash_rescaled`.
- Make `_dash_finish_secondary_axes` skip `want` on a rescaled y2/x2 and record `fig._dash_secondary_hulls`.
- Saved by() loop: compute `_brs` once per graph and pass `rescale=_brs` to every panel's `_make_figure`.
- Served template: add `_rescale=frozenset()` to `_dash_figure_for` and pass `rescale=_rescale` at its `_dash_apply_scale_ranges` line. In the by() branch, compute `_brs` and pass `_rescale=_brs` to all three `_dash_figure_for` calls (the panels, the empty-frame fallback, the every-panel-dropped fallback).
- Non-by graphs must be unchanged.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_scales.py -q -n0 -k "range_is_not_applied or count_ticks_ignore_range or reverse_and_log or labels_and_ticks_still_widen"` passes. `python3 -m pytest test/test_axis_extents.py test/test_dual_axis.py test/test_natscale_axes.py -q -n0` passes.]]></verify>
  <done>A rescaled axis dropped its range() values and kept reverse, log and its labels' widening, per panel, in both renderers.</done>
</task>

<task type="auto" id="10-19">
  <name>Share one scale across the panels</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Per TR-10.17 and TR-10.18:
- Add `made=None` to `_dash_hull_ranges` (the same Range1d object per `hkey` when given) and `letters=("x", "y")` to `_dash_common_count_ticks` (one `made` dict across its calls).
- Add `_dash_share_by_scales(figs, rescale)` after `_dash_common_count_ticks`: (a) one DataRange1d per non-rescaled letter, (b) one second-axis Range1d from the panels' `_dash_secondary_hulls`, then `_dash_common_count_ticks(figs, letters=…)`. Share BEFORE ticking.
- Replace the saved call (27284) and the served call (30843) with `_dash_share_by_scales([...], _brs)`.
- Add `"_dash_share_by_scales"` to the served functions tuple after `"_dash_common_count_ticks"` (28708).

Map `_dash_share_by_scales` in `test/function_test_map.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_by_scales.py -q -n0` passes completely. `python3 -m pytest test/test_by_scales_chrome.py -q -n0` passes on a machine with Chrome; record `test_hundred_panels_settle`'s measured seconds in `<scratch>/10-P0.2-perf.txt`. `python3 -m pytest test/test_resource_limits.py test/test_statistical_helpers.py -q -n0 -k "DefinesEveryName or CarriesEveryName"` passes.]]></verify>
  <done>Every by() graph's panels shared one range object per non-rescaled axis, spanning the union of their data before and after any filter move in both modes, and each graph's sharing stayed inside it.</done>
</task>

<task type="auto" id="10-20">
  <name>Flip the by() pins and extend parity</name>
  <files>test/test_server_facets.py, test/test_natscale_axes.py, test/test_mode_parity.py</files>
  <action><![CDATA[
- `test_server_facets.py:512`: `("foreign, norescale noixlabel", ["norescale", "noixlabel"])` becomes `["noixlabel"]`, with a comment that norescale is twoway's default and is honoured (WP-29 P0.2).
- Rewrite `test_natscale_axes.py`'s docstring :13-15 to say dash honours yrescale and its panels then tick per panel, as `test_by_scales.py::TestRescaleGivesEachPanelItsOwn::test_count_ticks_are_per_panel` pins.
- In `test/test_mode_parity.py`, append the CORPUS cases:
  - "by(foreign, yrescale)";
  - "by(foreign) with yaxis(2)";
  - "by(foreign, rescale) ylabel(#5)";
  - "by(foreign, yrescale) yscale(range(0))", with a `_MUST_WARN` entry for the TR-10.16 text prefix;
  - "by(foreign, yrescale) yscale(range(0)) with every foreign missing".
- Append the MOVE_CORPUS case "by(foreign) shared scale, price slider".
- Add `TestByPanelsShareInBothModes::test_the_sharing_partition_agrees`: for each by() CORPUS case, the partition of panels by `id(fig.y_range)`/`id(fig.x_range)` is the same in both modes.
- Re-run the existing by() entries. Their `renderers` counts move together in both modes; do not edit `ALLOWED` (R6).

Record each flip in `<scratch>/10-flips-P0.2.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_server_facets.py test/test_natscale_axes.py test/test_mode_parity.py -q -n0` passes with no new skips.]]></verify>
  <done>The tests that pinned norescale as ignored or by() panels as independent pinned twoway's shared and rescaled scales, and both modes agreed on the sharing of every by() case.</done>
</task>

<task type="auto" id="10-21">
  <name>Certify by() scales in Stata</name>
  <files>test/test_wp29_truth.cscript, test/test_by_suboptions.cscript, test/program_coverage_map.py</files>
  <action><![CDATA[
Append the block `* ==== S10 P0.2: by() shared scales ====` … `* ==== end S10 P0.2 ====` directly after the S10 P0.5 block in `test/test_wp29_truth.cscript`. It has the same gate, and its helpers and its `python:` reader sit outside the gate. BSC-01..BSC-07 follow "P0.2: Stata".

In `test/test_by_suboptions.cscript`, after BYS-06 and before `capture program drop _bys_render`:
- add BSC-08 (through `_bys_render`/`_bys_take`);
- add BSC-09 and BSC-10, using a new `_bsc_logrun` program (the `_bys_render` log pattern for an arbitrary command) and `cert_log_has` with `r(count) == 1` for the TR-10.16 note on `dash scatter …, saving()` and on `dash build, saving("<app>") replace server`.

Update its header's "Tests:" line. In `test/program_coverage_map.py`, add `test_by_suboptions.cscript:BSC-10` where `_dash_plot` or the build program is mapped, if the map tracks the served build. Run both scripts through the driver (`WP29_ONLY=S10` for the truth script).
  ]]></action>
  <verify><![CDATA[`grep -c "BSC-0[1-7] PASS" <scratch>/s10/run_test_wp29_truth.log` prints 7 and `grep -c "AX-1[1-8] PASS" <scratch>/s10/run_test_wp29_truth.log` still prints 8. `grep -c "BSC-0[89] PASS\|BSC-10 PASS" <scratch>/s10/run_by_suboptions.log` prints 3, and `grep -c "BYS-0[1-6] PASS" <scratch>/s10/run_by_suboptions.log` prints 6. Neither log has `FAIL`, `SKIP` or an `r(` error line.]]></verify>
  <done>Stata certified that dash's by() panels share or rescale exactly as twoway's, and that the dropped-range note reached the Stata log on a saved and a served build.</done>
</task>

<task type="auto" id="10-22">
  <name>Document by() scales in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
Update `dash.sthlp`:
- In "Faceting with by()" (1735-1800), add a paragraph: as in twoway, the panels share one scale per axis (y, x and a second axis) over every panel's data, the Total panel's too, and keep sharing it after a filter move; panning or zooming one panel moves the others and, as in any Bokeh plot, stops that axis following later filter moves.
- Add synopt rows `by(varlist, yrescale|xrescale|rescale)`, naming the abbreviations `yr`, `xr`, `r`, the `no` forms, and that yes wins when both are given, as in twoway. Add a row for `style(rescale)`/`style(combine)`: only their separate scales are drawn.
- Say that on a rescaled axis `yscale(range())`/`xscale(range())`, `axis(2)`'s included, are not applied, as in twoway, with a note; labels and ticks still widen each panel; reverse and log are kept.
- Say that twoway draws only the outer axes on shared panels, while dash draws every panel's.
- At :1780-1783, add the rescale forms to the implemented list.
- At :2501-2503, replace "{cmd:by(, yrescale)} is not implemented" with "with {cmd:by(, yrescale)} each panel is ticked over its own data, as {cmd:twoway} ticks it".

Grep the help-claims tests for the changed sentences and update any pin.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py -q -n0` passes. `grep -c "yrescale)} is not implemented" dash.sthlp` prints 0.]]></verify>
  <done>The help described twoway's shared by() scales, the rescale forms dash honours, the dropped range() and the linked pan and zoom.</done>
</task>

<task type="auto" id="10-23">
  <name>Close P0.2 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
Close IN PLACE the BUGS.md entry keyed `"P0.2"` in `WP29_OPEN`:
- File Names: dash_render.py `_DASH_BY_SUPPORTED`, `_dash_parse_by`, `_dash_by_rescale`, `_dash_by_range_notes`, `_dash_apply_scale_ranges`, `_dash_finish_secondary_axes`, `_dash_hull_ranges`, `_dash_common_count_ticks`, `_dash_share_by_scales`, `DashRenderer._make_figure`, `_build_figures`, the served `_dash_figure_for` and by() loop, `ServerAppBuilder._plan_graph_notes`.
- The Resolution: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.2). A by() graph's panels share one range object per axis (y, x, y2, x2) in both renderers, spanning the union of every panel's data after any filter move; yrescale, xrescale, rescale, their abbreviations and style(rescale|combine) give each panel its own scale, #N ticks and hull, and range() on a rescaled axis is not applied, with one note at build time. Pinned by test/test_by_scales.py::TestPanelsShareOneScale::test_default_shares_x_and_y, test/test_by_scales.py::TestRescaleGivesEachPanelItsOwn::test_count_ticks_are_per_panel, test/test_by_scales_chrome.py::TestTheBrowserDrawsOneScale::test_saved_page_initial_and_after_a_move, test/test_wp29_truth.cscript BSC-01, test/test_by_suboptions.cscript BSC-10; fixture test/fixtures/by_scales_truth.json. Residual, deferred (WP-29): twoway's common scale includes fit lines, outer-axes-only display (B16), YRESCALE and two style() are accepted where twoway refuses them.`

Delete the `"P0.2"` key line from `WP29_OPEN`. In CHANGELOG.md, replace the `<!-- WP-29 P0.2 -->` marker in Results that change with ONE line ending `(WP-29, P0.2)`. It states that:
- `dash scatter mpg weight, by(foreign)` drew Domestic on 12-34 and Foreign on 14-41 and now draws both on 12-41, as twoway does, with second axes shared too;
- `by(foreign, yrescale) ylabel(#5)` drew 10(10)40 on both panels and now draws 10(5)35 and 15(5)40;
- `by(, yrescale) yscale(range(0))` drew both panels from 0 and now leaves range() unapplied, with a note;
- by() panels now pan and zoom together.

Run the full suite once (`python3 -m pytest test/ -q`), then the two cscripts of 10-21 and the parity script through the drivers. Run `gitnexus_detect_changes()` and `git diff --cached --name-only` (only tasks 10-14..10-23's files). Grep the message for `claude|anthropic`. Commit on `wp29-s10` with the subject `Share one scale per axis across by() panels (WP-29 P0.2)`. The body opens with `<scratch>/10-P0.2-failure.txt`, then gives the `<scratch>/10-P0.2-perf.txt` number and carries:
- `Regression:` lines (`-- failed at <P0.5 commit sha> with <text>`);
- the `Flipped:` lines from `<scratch>/10-flips-P0.2.txt`;
- `Fixture: test/fixtures/by_scales_truth.json (scripts/extract_by_scales_truth.do)`;
- `BUGS.md: "<title>" (closed)`.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips. `python3 -m pytest test/test_tracking_documents.py -q -n0` passes. `grep -c '<!-- WP-29 P0.2 -->' CHANGELOG.md` prints 0. `git log -2 --format=%s` lists the P0.2 subject above the P0.5 subject. `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>P0.2 was closed in BUGS.md naming existing tests, its marker and tracking key were gone, and a second green commit on wp29-s10 carried the cycle on top of P0.5's.</done>
</task>

## Section completion criteria

- In both modes, before and after a filter move:
  - every axis(2) form of the title, label, tick, line and scale families (twoway's spellings and plurals) draws on the second axis, and axis(1)/unqualified options draw on the first;
  - `ylabel(10 20) ylabel(5000 10000, axis(2))` keeps both lists.
- dash refuses, with twoway's message, r(198) and order: an axis no layer uses, a repeated axis(), AXIS(), a second comma, and axis-1 options on a lone second-axis graph. AX-01..AX-08 and AX-11..AX-18 pass.
- Every by() graph's panels share one range object per non-rescaled axis (y, x, y2, x2), equal to the union of their data, in both modes and in Chrome after a move. Rescaled axes are per panel, with twoway's `#N` ticks, `range()` dropped and one build-time note. BSC-01..BSC-10 pass, and the 100-panel move settles within 3 s.
- Two commits on `wp29-s10`, P0.5 then P0.2, each holding its failing tests, fix, flips, fixture and closed BUGS.md entry. No test-only commit. The full suite was green before each.
- No `.cscript` was created, and neither the runner nor the hygiene pins were edited. Both fixtures carry `_meta` and are committed. Every flip is recorded as a `Flipped:` line.

## Notes

- **Line numbers** are `7421d3d`'s and batch 1 shifts them (S03, S05, S07 and S08 edit `dash_render.py` and `dash.ado`). Locate everything by symbol. S03 may have rewritten `_dash_route_axis2` and `_dash_route_axis_titles`; edit its versions.
- **Renderer order.** The served template adds second axes before styling titles, while the saved renderer does it after (WP-28 Notes). Every change here lives in the shared helpers, so the order does not matter. The parity profiles now record range names, so drift shows.
- **The two notes are build-time only (R6, K6).** `_dash_unused_second_axis_notes` and `_dash_by_range_notes` are called by `DashRenderer._build_figures` and by `ServerAppBuilder._plan_graph_notes()`, never by the served template. `ServerAppBuilder.build` already calls `_dash_reset_notes()` (29098), so a saved render earlier in the same Stata session cannot swallow the build's note.
- **Share before ticking.** `_dash_share_by_scales` must assign the shared range and repoint `e["rng"]` before `_dash_common_count_ticks` runs. Otherwise the `#N` start/end land on discarded objects.
- **`have_updated_interactively`.** After a user pans or zooms, BokehJS stops autoranging that range. With sharing, this applies to every panel at once. That is Bokeh's behaviour, documented in the help, and not a defect of this section.
- **Copy lists (R2).**
  - Functions tuple: `"_dash_by_rescale"` after `"_dash_by_tokens", "_dash_parse_by",` (28638), and `"_dash_share_by_scales"` after `"_dash_common_count_ticks"` (28708).
  - No constants entry (`_DASH_BY_SUPPORTED` is already copied at 28375).
  - The build-time helpers (`_dash_route_axis_options`, `_dash_axis_number`, `_dash_unused_second_axis_notes`, `_dash_by_range_notes`) are not copied. This deviates from the R2 table's "`_dash_by_range_notes` after `_dash_by_tokens`" and "axis(#) helpers after `_dash_apply_scale_ranges`", because the app must not repeat build-time notes (R6). If a reviewer prefers parity with `_dash_route_axis_titles` (copied though unused), copying is harmless, but the template must never call them.
- **Shared files (R1-R8).**
  - R1: AX cases go at the end of `test_twoway_option_parity.cscript` after S02's JO run. The S10 blocks go above the truth script's marker in section order, and BSC-08..10 go at the end of `test_by_suboptions.cscript`.
  - R2: map keys in alphabetical place.
  - R3: only the help paragraphs named in 10-12/10-22, only the P0.5/P0.2 markers, only these two BUGS.md entries, and only the two `WP29_OPEN` key lines.
  - R4: axis-word routing is this section's (no other batch-2 section edits `_dash_route_axis2`).
  - R5: two new fixtures, none regenerated.
  - R6: CORPUS/MOVE_CORPUS/`_MUST_WARN` appends only, and never `ALLOWED`.
  - R7: flips are recorded, never deleted.
  - R8: impact before each edit, and `gitnexus_detect_changes()` before each commit.
- **S13 merges after this section.** If the served token gates `make_document`, S13 updates `test_mode_parity._served`, `test_dual_axis._lone_figure` and `test_by_scales._served_doc`, the three helpers this section's served tests use, plus the two `python:` readers of the S10 truth blocks.
- **Commit-body line forms (index Deltas):**
  - `Regression: test/<file>.py::<Class>::<test> -- failed at <sha> with <text>`
  - `Flipped: <node> -- <old expectation> was wrong because <why>`
  - `Fixture: test/fixtures/<name>.json (scripts/<extract script>)`
  - `BUGS.md: "<title>" (closed)`
- **Stata.** Use only `scripts/stata_slot.sh <scratch>/s10 <file>.do` with `dash_nobrowser=1` and a do-file that opens with `adopath ++` (the extract scripts through their `W29_REPO` driver, the cscripts through the `cd test` driver). Never the GUI, never a bare `stata-mp`, never `make cert`. When many sessions run at once, `python_exec` can vanish from `~/.stata19/console/stata19.rc`, so check `c(python_exec)` before trusting a SKIP.
- **pytest.** While iterating, run only the changed files (`-n0 -p no:cacheprovider` for single nodes). Run the full suite once per commit and read its log.

### Notes for the closeout (S15 only, A5)

- **GAPS2.md:**
  - B4: closed by P0.2 (B4-a, B4-b).
  - B15-a: closed by P0.5. B15 itself stays partly closed: axes 3-9 and `yaxis(1 2)` remain.
  - B16: its rescale part is closed by P0.2. rows/holes/titles/i*axes remain.
  - B22-c: `axis(2)` on lines is closed. The other B22 sub-items remain.
- **REMAINING.md:2451-2466** (`axis(#)` misrouted): closed by P0.5.
- **TWOWAY_COVERAGE_AUDIT.md:142:** the dash column already claimed "common scales" at HEAD, which was false before P0.2. Fix both columns, and drop yrescale from "ignored". The AUDIT-27 row is closed by P0.5.
- **DROPIN-REMAINING.md:** annotate P0.2 and P0.5 with their commits.
- **ROADMAP WP-29:** record the 100-panel settle time from the P0.2 commit body.
- **New residuals to record:**
  - dash draws no default title on `yaxis(2)` (twoway titles it by its layers' variables);
  - `ylabel(…, axis(2) add)` is named, not drawn;
  - `ymlabel/ymtick` with `axis(2)` are validated, not drawn: tell the P1 owner to route them through this section's family table;
  - `YRESCALE` and two `style()` are accepted where twoway refuses them (by() validation item);
  - twoway's common scale includes fit lines (c15) (P1.3 owner);
  - outer-axes-only display on shared panels (B16 owner).
- **AGENTS.md invariant:** "by() sharing is decided by `_dash_share_by_scales` after every panel is built and before `_dash_common_count_ticks`; served notes are decided at build time (`ServerAppBuilder._plan_graph_notes`)."
