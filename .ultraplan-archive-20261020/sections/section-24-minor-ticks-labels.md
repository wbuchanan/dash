# Section 24: Minor ticks and minor labels

> Part of: WP-31 · GAPS3 rows: D1 · Risk: yellow · Batch: 8 · Depends on: 01 · Blocks: 33 · Tasks: 4, 1 commit · Case-id prefix: U24

## Overview

**What is wrong today.** GAPS3 D1 (GAPS3.md:151): "`xmtick ymtick xmlabel ymlabel tmtick tmlabel` (and the `*2` forms) pending, never read by the renderer. Bokeh has no labelled minor ticks." Evidence `dash.ado:1025-1037; grep 0 in renderer`. GAPS3 §5 (GAPS3.md:293-295) lists the same six among the "entries written to the spec and never read by the renderer". At `6370ca4` the six options are declared (`XMTick YMTick XMLabel YMLabel TMLabel TMTick`, dash.ado:946-947, 961), bounded as `axislist` (`_dash_option_rules`, :3050-3051), written to `graph_options` (the seven key lists, e.g. :7343) and then named in the pending blocks (:1032-1033 xmlabel/xmtick, :1036-1037 tmlabel/tmtick, :1040-1041 ymlabel/ymtick, and the plot parser's twins at :1356-1387), so `dash scatter mpg weight, xmtick(##5)` prints `dash: ignoring unsupported option(s): xmtick()` and draws twoway's default axis. The help's Unsupported section says so (dash.sthlp:4997-5004) and TWOWAY_COVERAGE_AUDIT.md:137 records "Minor ticks/labels absent". There is no `xmtick2()`/`ymtick2()`/`xmlabel2()`/`ymlabel2()` form: `_dash_axfam` (dash_parse.mata:6880-6886) routes `mlabel` and `mtick` to `""`, "the name an axis(2) copy is written as ("" when dash does not route that family)", so `xmtick(5, axis(2))` has nowhere to go.

**After this section** both modes draw minor ticks and minor labels as twoway does. `xmtick()`/`ymtick()` take a numlist, `a(b)c`, `minmax`, `#N` and the minor-only rule `##N` (N-1 ticks between each pair of evenly spaced major ticks; nothing when the majors are uneven, as twoway's `suggest_between_ticks` draws nothing, research/stata-ground-truth.md §8). The marks are the axis's Bokeh minor ticks, `gsize minortick` long (half_tiny, 0.6944 units, 2.67 px at the 4-inch reference) in `color minortick` at `linewidth minortick`, outside the frame like the major ticks. `xmlabel()`/`ymlabel()` draw the same marks and, at each position, a label in `gsize minortick_label` (vsmall, 2.0833 units) and `color tick_label`, written with the axis's format (or the quoted text the option gives), as a `LabelSet` along the frame edge (DISCOVERY Q37, decision M21). `tmtick()`/`tmlabel()` reach the x axis as `xmtick`/`xmlabel` (dash.ado's `_dash_taxis_fold`, WP-30 P1.6) and so are drawn with no further work. `axis(2)` copies are routed to the new `xmtick2()`/`ymtick2()`/`xmlabel2()`/`ymlabel2()` keys and drawn on the second axis. The scheme's `numticks_g horizontal_minor 0`/`vertical_minor 0` are added to every shipped scheme, so no minor tick is drawn unless asked. The minor positions survive a filter move in both modes: explicit positions are constants, and `##N` positions are rewritten with the finished majors by `_dash_refinish_axes` (saved, Python) and `_DASH_AXIS_FINISH_JS` (saved page, after a move), the two finishers R11 gives S24 in batch 8.

**Why this row is alone.** D1 is the only row that edits the tick machinery (`_dash_apply_tick_option`, `_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS`), and S33 (axis sub-options and look, batch 11) builds on the finished minor set. S24 edits no legend, title or sizing code.

**Test order and commit rule (BRIEF).** One cycle, one commit `(WP-31 D1)`: 24-01 writes `test/test_minor_ticks.py` and the extract script, runs the tests against the unmodified tree and saves `<scratch>/24-01-failure.txt` (never commits); 24-02 declares the axis-2 keys and removes the pending lines (dash.ado, dash_parse.mata); 24-03 draws the ticks and labels in the renderer and regenerates the schemes; 24-04 appends the U24 cases, flips the pins, updates help/audit/BUGS/GAPS3/CHANGELOG and makes the one commit on `wp31-s24`.

### Section decisions (this file; binding on the executor)

- **D-24.a One minor slot, shared.** Bokeh gives an axis one set of minor ticks. `xtick()` already uses it (`_dash_apply_tick_option`, dash_render.py:31465-31540: a `CustomJSTicker` whose `minor_code` returns the xtick positions), so `xmtick()` positions join the SAME `CustomJSTicker` as a second argument `mextra` (and `between` for `##N`), never a second ticker. The minor tick length is `gsize minortick` only when the axis has no `xtick()` positions; when both are given the one slot is drawn at the major tick's length (xtick's rule, :31540) and the help says so with the measured example `xtick(10 20) xmtick(15)` (M17: documented where Bokeh cannot express it).
- **D-24.b Labels are a LabelSet on axis 1 and Labels on axis 2.** For the figure's own axes the labels are one `LabelSet` per axis (`x_units="data", y=0, y_units="screen"` for x; `y_units="data", x=0, x_units="screen"` for y: screen units are frame-relative, so they stay aligned on resize with no JavaScript, research/bokeh-web.md §5 (a)). For an `axis(2)` copy the frame's far edge is not a number, so each position is one `Label` with `y=Node(target="frame", symbol="top")` (x axis 2) or `x=Node(target="frame", symbol="right")` (y axis 2), constructs verified under Bokeh 3.9.0 and 3.8 property sets (`Node`, `ImplicitTarget` "frame"). Every label model carries `name="dash_minor_labels"` and tags `[which, str(axis_no)]` so the finishers and the tests find it.
- **D-24.c `axis(2)` is routed like `label2`/`tick2`.** `_dash_axfam`'s `mlabel` and `mtick` rows (dash_parse.mata:6882, :6884) get the names `"mlabel2"` and `"mtick2"`; dash.ado declares `XMLABEL2(string asis) YMLABEL2(string asis) XMTICK2(string asis) YMTICK2(string asis)` beside `YLABEL2`/`XLABEL2` (:943-944) in both parsers, adds the four `sreturn`s, the four names to all seven key lists (after `ylabel2 xlabel2`), four `axislist` rules (:3050) and the four names to `_dash_rep_cat`'s "L" list (dash_parse.mata:6176). test_unsupported_report_is_true.py's declared-graph count moves by +4: recount with the file's `_declared_graph()` at the batch-8 base and write `# <measured old> -> <measured old + 4>: D1 axis(2) minor forms` (R10; DECISIONS A33: S17 in batch 6 moves this count first, so the old value is read at the base, never planned).
- **D-24.d `##N` with uneven majors draws nothing**, as twoway (`tickset_g.class:983-1005`); `##N` on `xlabel()`/`xtick()` is already refused by dash.ado's `axislist` rule as twoway refuses it ("##N ignored, only allowed for minor ticks"), measured in U24-5 before any renderer change.
- **D-24.e Minor label text.** A position with quoted text draws that text; otherwise the axis's own writer: the same helper `_dash_apply_axis_spec` (:30428) uses for an explicit tick with no `labels` entry (its `fmt_fallback`/`fmt_cache` path), so a `%td` axis writes dates and a `format()` on `xlabel()` is followed. After a saved move the page's `_DASH_AXIS_FINISH_JS` rewrites `##N` texts with `axis.formatter.doFormat([v], {loc: 0})[0]` inside `try`, falling back to `String(v)`; explicit positions are never rewritten.
- **D-24.f Grid.** `grid` on `xmtick()`/`xmlabel()` turns on the minor grid in `color/linewidth/linepattern minor_grid` (already parsed: SchemeParser `minor_grid_dash`, :10598); `nogrid` and the default leave it off (`yesno draw_minor_*grid no`).

## Risk: [yellow] -- every axis with xtick() shares its ticker with the new positions, and two finishers change

**Why.** `_dash_apply_tick_option`'s `CustomJSTicker` is rebuilt with more arguments; `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS` (R11, batch 8) gain a step; 26 scheme files are regenerated.

**Risk factors.** 1. An xtick()-only axis must draw exactly as today (same `extra` argument, same length). 2. `##N` after a move depends on the finished majors in two languages. 3. The scheme regeneration rewrites 26 files; a stub transcribed wrongly reaches every test that reads the scheme. 4. A LabelSet source is a new data sink: label text must stay a canvas text (never HTML). 5. The axis-2 `Label` models use `Node`, which Bokeh 3.8 has but earlier releases did not.

**Mitigation.** 1. `TestXtickIsUnchanged` pins the ticker's `args` keys and the minor lengths for xtick()-only axes before the change (guard). 2. `TestBetweenRuleFollowsTheMajors` runs the saved finisher under node (test_saved_filter_layers `_render`/`_move`) and the served `_on_filter_change`. 3. 24-03 runs the generator twice and `git diff --stat` must show only appended blocks and the fixture; test_scheme_chrome.py `TestEveryShippedSchemeDrawsItsChrome` reads every file. 4. test_label_sinks.py gains the `dash_minor_labels` sink as a `Carrier` (text goes to `LabelSet.text` from a column, a canvas sink). 5. test_bokeh_floor.py (or the version pin test S59 owns) is not edited; `Node` is on 3.8's property set (RESEARCH §2).

## Dependencies

- **Depends on: 01** (tracking: BUGS entry, GAPS3 Tracked line, CHANGELOG marker `<!-- WP-31 D1 -->`, the truth script's `// 70.` registration).
- **Blocks: 33** (axis sub-options and look, batch 11): S33's `tlength()`/`tposition()` on minor ticks reads the `mextra` argument and `minortick_length_px` this section adds.
- **Parallel batch: 8**, merge order S25, S23, S24. **Can run with S23 and S25**: S23 adds `_dash_contour_*` helpers, S25 edits `_FILTER_JS`; neither touches `_dash_apply_axis_options`, `_dash_apply_tick_option`, `_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS`, `SchemeParser`'s tick attributes or the scheme files.

## Evidence

All anchors at `6370ca4` (dash_render.py 52,280 lines; dash.ado 11,039; dash_parse.mata 9,789).

### The pending lines (dash.ado)

```
1032    if `: length local xmlabel' local _dash_pending `"`_dash_pending' xmlabel"'
1033    if `: length local xmtick' local _dash_pending `"`_dash_pending' xmtick"'
1034    // WP-30 P1.6: tmlabel() and tmtick() are stored on xmlabel/xmtick by
1035    // _dash_taxis_fold and drawn when minor ticks are (P2.2).
1036    if `: length local tmlabel' local _dash_pending `"`_dash_pending' tmlabel"'
1037    if `: length local tmtick' local _dash_pending `"`_dash_pending' tmtick"'
1040    if `: length local ymlabel' local _dash_pending `"`_dash_pending' ymlabel"'
1041    if `: length local ymtick' local _dash_pending `"`_dash_pending' ymtick"'
```
(The graph block is :1010-1042; the plot parser's block at :1320-1387 repeats the six lines, its comment at :1379.) The rules already exist: `xmtick=axislist  ymtick=axislist` / `xmlabel=axislist  ymlabel=axislist` (:3050-3051). The seven key lists hold `xmtick ymtick xmlabel ymlabel ... tmlabel tmtick` (:5776, 6714, 6748, 6849, 6924, 6956, 7339-7345).

### The tick-only path the minor set must join (dash_render.py)

`_dash_apply_tick_option` (:31465) builds the one ticker an axis may carry:

```python
31507        if mode == "explicit" and spec["ticks"]:
31508            args["extra"] = [float(t) for t in spec["ticks"]]
31509            minor = _DASH_TICK_EXTRA_JS
31524        ax.ticker = CustomJSTicker(args=dict(args, base=ax.ticker),
31525                                   major_code=_DASH_TICK_MAJOR_JS,
31526                                   minor_code=minor)
31531            ax._dash_hull_tick_extra = list(args["extra"])
31540        ax.minor_tick_line_color = ax.major_tick_line_color
```
It is called once per axis from `_dash_apply_axis_options` (:31700-31704) after the label spec; the scale look follows (:31708-31716). `_dash_refinish_axes` rewrites the base ticker as `FixedTicker(ticks=vals, minor_ticks=[], ...)` (:32982) and `t.args = dict(t.args, base=fixed)` (:32988) once the layers are drawn; `_DASH_AXIS_FINISH_JS` (:30933) does the same on the saved page after a move. The scheme applies `axis.minor_tick_line_color = self.minortick_color` (:11574) and nothing else for minor ticks; `SchemeParser` reads `color minortick` (:10602) but not `gsize minortick`, `gsize tickgap` or `linewidth minortick` (the dash-s2color.scheme stubs at :343, :482, :515 exist for colour, pattern and width; `gsize minortick_label vsmall` at :555; no `gsize minortick`, no `gsize tickgap`, no `numticks_g *_minor`).

### Stata's rule (research/stata-ground-truth.md §8)

`##N` -> N-1 values between major ticks, allowed with `mlabel()`/`mtick()` only (`axis_label_options.sthlp:62-68, 903-910`); requires evenly spaced majors, else no minor ticks (`:662-669`; `tickset_g.class:983-1005`: delta = major delta / N, extended by whole deltas from the major min/max). Scheme: `numticks_g horizontal_minor 0`, `vertical_minor 0` (`scheme-s2color.scheme:293-294`); `gsize minortick half_tiny` vs `tick tiny` (`:153-154`); `gsize minortick_label vsmall` (`:160`); `gsize tickgap half_tiny` (`:156`); `color minortick black` (`:350`), `linewidth minortick thin` (`:1207`); `textboxstyle-minortick_label.style`: size minortick_label, color tick_label.

### Fixtures on disk

None for minor ticks. `test/fixtures/scheme_truth.json` is regenerated by `scripts/extract_scheme_truth.py` (R7; the generator also rewrites the 26 `dash-*.scheme` files, :13-24 of its docstring).

### Tests that pin today's behaviour (flip, never delete)

- `test/test_unsupported_report_is_true.py` PLOT/GRAPH value tables: `"xmtick": ("5(1)40", "10(2)40", "scatter")` (:154) and the `xmlabel`, `ymtick`, `ymlabel`, `tmtick`, `tmlabel` entries beside it; the pending counts at :240-262 (`test_the_blocks_were_actually_found`) and the declared counts at :725-726 (`196`, `85`).
- `test/test_help_conformance.py::TestTheUnsupportedSectionIsTrue` (:938-960): follows the pending blocks and the help both ways.
- `test/test_help_claims_8.py::TestAnUnsupportedOptionIsInertWhenServed` (:1410): derives its list from the pending blocks (follows automatically).
- `test/test_scheme_chrome.py::TestTheChromeKeysAreRead` (:383): the stub set every scheme must carry (gains the four stubs).

## User stories

- US-24.1 As a Stata analyst, I want `xmtick(##5)` to draw four small ticks between my major ticks so that my dashboard axis reads like my twoway graph.
- US-24.2 As a Stata analyst, I want `ymlabel(2.5 7.5)` to draw small labelled ticks at those values so that intermediate values are readable without crowding the major labels.
- US-24.3 As a Stata analyst, I want `tmtick()`/`tmlabel()` on a time axis and `xmtick(, axis(2))` on a second axis to be drawn, not named as unsupported.
- US-24.4 As a dashboard reader, I want the minor ticks to stay in place after I move a filter, in the saved page and the served app alike.

## Business requirements

- BR-24.1 `xmtick()`, `ymtick()`, `xmlabel()`, `ymlabel()`, `tmtick()`, `tmlabel()` and their `axis(2)` copies are drawn in both modes; nothing is printed for them (Q36).
- BR-24.2 `##N` draws N-1 marks between each adjacent pair of evenly spaced major ticks and nothing when they are uneven.
- BR-24.3 Minor marks are shorter than major marks (the scheme's `gsize minortick`), minor labels smaller than major labels (`gsize minortick_label`), both in the scheme's colours.
- BR-24.4 No minor tick is drawn unless an option asks for one.
- BR-24.5 `xtick()` alone draws exactly as before.
- BR-24.6 A filter move leaves explicit minor positions where they are and moves `##N` positions with the majors.

## Technical requirements

- TR-24.1 **dash.ado.** Delete the six pending lines in both blocks (:1032-1033, :1036-1037, :1040-1041 and the plot parser's six). Declare `XMLABEL2 YMLABEL2 XMTICK2 YMTICK2 (string asis)` after `XLABEL2(string asis)` (:944) in `_dash_parse_graph_opts` and in `_dash_parse_plot_opts`' graph part; add `sreturn local xmlabel2 : copy local xmlabel2` (and the three others) after `sreturn local xlabel2` (:1071) and the `g_` forms after `sreturn local g_xlabel2`; add `xmlabel2 ymlabel2 xmtick2 ymtick2` after `xlabel2` in all seven key lists (:5776, 6714, 6748, 6849, 6924, 6956, 7339); add `xmtick2=axislist  ymtick2=axislist  xmlabel2=axislist  ymlabel2=axislist` after :3051.
- TR-24.2 **dash_parse.mata.** `_dash_axfam` (:6880-6886): rows `"mlabel", "mlabels", "mlabel", "3", "3", "mlabel2"` and `"mtick", "mticks", "mtick", "3", "5", "mtick2"`. `_dash_rep_cat` (:6176-6177): add `"xmtick2", "ymtick2", "xmlabel2", "ymlabel2"` after `"xmlabel", "ymlabel",`. Update the header index comment at :421 to name the four new axis-2 spellings.
- TR-24.3 **SchemeParser** (dash_render.py :10598-10606): add `self.minortick_length_px = self._tick_length_px("gsize minortick", "half_tiny")`, `self.tickgap_px = self._tick_length_px("gsize tickgap", "half_tiny")`, `self.minortick_line_width = self._bounded_lwidth("linewidth minortick", self.tick_line_width)`, `self.minortick_label_font_size = self._gsize("gsize minortick_label", "vsmall")` (the `_TEXTBOX_STYLES` row at :10071 already maps `minortick_label` -> size `minortick_label`, colour `tick_label`), and `self.numticks_minor = {"x": self._bounded_int("numticks_g horizontal_minor", 0, 0, 50, "minor tick count"), "y": ... "vertical_minor" ...}`. Generalise `_tick_length_px(self, key="gsize tick", default="tiny")` (:9980) keeping its one-argument behaviour. In `apply_to_axis` (:11574) add `axis.minor_tick_line_width = self.minortick_line_width` and record `"minor_length": self.minortick_length_px` and `"tickgap": self.tickgap_px` in `axis._dash_scheme_look` (:11580-11584).
- TR-24.4 **Parsing.** Module constant `_DASH_MINOR_RULE_RE = re.compile(r"^\s*##(\d{1,9})(?=\s|$)")` after `_DASH_AXIS_RULE_RE`; `_dash_parse_axis_spec` (:30297) gains `out["between"] = None` and, when `_DASH_MINOR_RULE_RE` matches the head and the caller passed `minor=True`, records `between = max(2, min(N, 50))` and strips the token before the existing rule match. Without `minor=True` the token stays unparsed (dash.ado refuses it first, D-24.d).
- TR-24.5 **The drawer.** New module function `_dash_apply_minor_ticks(fig, axes, grids, which, axis_no, mtick_raw, mlabel_raw, values, seen, key, *, date_kind=None, by_graph=False, ref_in=4.0, fmt_fallback="", fmt_cache=None, value_labels=None)` placed directly after `_dash_apply_tick_option` (:31540). Steps: (1) parse both raws with `_dash_parse_axis_spec(raw, minor=True)`, name the unsupported tokens and the label-only sub-options on mtick (the `_dash_apply_tick_option` list, :31493-31497) through `_dash_report_suboptions(option, ...)`; `_dash_date_axis_spec` when `date_kind`. (2) `positions`: the union of both specs' explicit ticks, `minmax` extremes of `values`, and `#N` through `_dash_count_ticker(N)` as `args["mevery"]`. (3) For every `ContinuousTicker` axis in `axes`: if `ax.ticker` is already the xtick `CustomJSTicker` (its `args` has `"extra"` or `"every"`), add `mextra`/`between`/`mevery` to its `args` and set `minor_code=_DASH_MTICK_JS`; else build `CustomJSTicker(args=dict(base=ax.ticker, mextra=..., between=..., mevery=...), major_code=_DASH_TICK_MAJOR_JS, minor_code=_DASH_MTICK_JS)`. (4) Length: when `"extra"`/`"every"` is absent (no xtick), `ax.minor_tick_out = int(round(ax._dash_scheme_look["minor_length"]))` (inside/crossing follow `tick_position` as :11566-11572), else leave xtick's lengths (D-24.a); `ax.minor_tick_line_color = ax.major_tick_line_color`. (5) Hull: extend `ax._dash_hull_tick_extra` with the explicit positions unless `norescale`. (6) Grid: `grid` -> `g.minor_grid_line_color = scheme minor_grid colour` for `g in grids` (read from `fig._dash_scheme_colours`'s scheme or pass the colour as `grid_color`). (7) Labels (mlabel only): texts = quoted labels, else the axis writer (D-24.e); axis 1 -> `LabelSet(source=ColumnDataSource({"pos": positions, "text": texts}), x="pos", y=0, x_units="data", y_units="screen", y_offset=-(minor_length + tickgap), text_align="center", text_baseline="top", text_font_size=minortick_label_font_size, text_color=scheme tick_label colour, level="overlay", name="dash_minor_labels", tags=[which, "1"])` (y axis: `y="pos", x=0, y_units="data", x_units="screen", x_offset=-(minor_length + tickgap), text_align="right", text_baseline="middle"`); axis 2 -> one `Label(x=p, x_units="data", y=Node(target="frame", symbol="top"), y_offset=minor_length + tickgap, anchor="bottom_center", ...)` per position (y axis 2: `x=Node(target="frame", symbol="right")`, `anchor="center_left"`), same name and tags `[which, "2"]`; `fig.add_layout(model)` (centre layer). Positions are capped at `_MAX_AXIS_TICKS`. Imports (`CustomJSTicker`, `LabelSet`, `Label`, `Node`, `ColumnDataSource`) inside the function (the `_dash_reference_lines` pattern).
- TR-24.6 **JS ticker code.** Module constant `_DASH_MTICK_JS` after `_DASH_TICK_EXTRA_JS`: returns the sorted union of `extra` (if present), `mextra`, `mevery.get_ticks_notrust(...)`'s majors (if present) and, when `between` is a number, for the base's majors `m` sorted ascending: if `m.length >= 2` and every gap equals the first within `1e-9 * |gap|`, emit `m[i] + k*gap/between` for `k = 1..between-1` for each adjacent pair; else nothing. Written in the form of `_DASH_TICK_EXTRA_JS` (read it and `_DASH_TICK_MAJOR_JS` first; same `base` call).
- TR-24.7 **Call sites.** `_dash_apply_axis_options` (:31700-31704): after the `traw` block add `mt, ml = graph_opts.get(ax_key[0] + "mtick", ""), graph_opts.get(ax_key[0] + "mlabel", "")` and `if mt or ml: _dash_apply_minor_ticks(fig, axis_obj, grid_obj, ax_key[0], 1, mt, ml, col, seen, key, date_kind=kind, by_graph=by_graph, ref_in=ref_in, fmt_fallback=fb, fmt_cache=fmt_cache, value_labels=vlabels)`. `_dash_finish_secondary_axes` (:32581): the same for the `xmtick2`/`xmlabel2`/`ymtick2`/`ymlabel2` keys with `axis_no=2` on the axis whose `x_range_name`/`y_range_name` is the secondary range. Both renderers call these two functions already (saved :43824-43830 region, served template line 104 of the `_dash_figure_for` excerpt), so no template edit is needed.
- TR-24.8 **Finishers (R11).** `_dash_refinish_axes` (:32271): after :32988 (`t.args = dict(t.args, base=fixed)`), when `"between" in t.args` recompute the between positions in Python from `vals` (the same rule as TR-24.6) and rewrite the matching `dash_minor_labels` model's source (`fig.select(name="dash_minor_labels")` filtered by tags) with the positions and texts (D-24.e writer). `_DASH_AXIS_FINISH_JS` (:30933): after the block that writes the base ticks, for an axis whose ticker `args.between` is a number, find the figure's `dash_minor_labels` renderer with matching tags, recompute positions and set `source.data = {pos: [...], text: [...]}` with `doFormat` in `try`. One JS edit, this section's only one.
- TR-24.9 **Scheme stubs (R7).** In `scripts/extract_scheme_truth.py`: truth entries after `"tick_length"` (:1615): `"minortick_length": chrome_one("minortick_length", "gsize", "minortick", ...)`, `"tickgap": chrome_one("tickgap", "gsize", "tickgap", ...)`, `"minortick_line_width": chrome_one(..., "linewidth", "minortick", ...)`; after `scalar("numticks_g", "vertical_major", ...)` (:2220): `scalar("numticks_g", "horizontal_minor", "numticks_horizontal_minor")`, `scalar("numticks_g", "vertical_minor", "numticks_vertical_minor")`; directives after `("gsize", "tick", nm("tick_length"), ("tick_length", None))` (:2377): `("gsize", "minortick", nm("minortick_length"), ("minortick_length", None))`, `("gsize", "tickgap", nm("tickgap"), ("tickgap", None))`, `("linewidth", "minortick", nm("minortick_line_width"), ("minortick_line_width", None))`. Run `/opt/homebrew/bin/python3.14 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json` (:96-97): every `dash-*.scheme` gains the lines `gsize minortick half_tiny`, `gsize tickgap half_tiny`, `numticks_g horizontal_minor 0`, `numticks_g vertical_minor 0` (and `linewidth minortick thin` where absent) in a dated appended block; `git add -f test/fixtures/scheme_truth.json`.
- TR-24.10 **Copy lists (R2).** Constants tuple: `"_DASH_MINOR_RULE_RE", "_DASH_MTICK_JS",` after `"_DASH_AXLABEL_HONOURED",` (:46641). Functions tuple: `"_dash_apply_minor_ticks",` after S23's last entry `"_dash_contour_surface",` (S23 lands before S24 in batch 8 and appends its seven helpers after `"_dash_reference_lines",` :47223), falling back to after `"_dash_apply_tick_option",` (:47027) only if S23 has not landed on the base; the two batch-8 hunks then never share context (index R2, A7). `test/function_test_map.py`: `"_dash_apply_minor_ticks": "test/test_minor_ticks.py::TestMinorTicksAreDrawn::test_explicit_positions"`.
- TR-24.11 **Help (R3).** Remove the "Minor ticks and minor labels" paragraph (dash.sthlp:4997-5004); add under `{marker axis_options}` (:3511ff, after the `xtick()` paragraph) a paragraph "Minor ticks and labels" giving the grammar, `##N`, the sizes, the shared-slot rule (D-24.a) with its example, and `axis(2)`. TWOWAY_COVERAGE_AUDIT.md:137 gains `[WP-31 D1, commit pending: corrected -- minor ticks and labels drawn]` (the merger's step k.3b fills the sha, A11); :169 loses `xmlabel`, `xmtick`, `ymlabel`, `ymtick`.
- TR-24.12 **Program maps.** No new Stata program or Mata function (R6 untouched beyond the data edits in TR-24.2).

## Boundaries

- Does not edit `_dash_apply_axis_spec`'s major-tick behaviour, `_dash_scale_look`, `_dash_add_secondary_axes` (S35), `_FILTER_JS` (S25 is batch 8's editor), `_make_figure_body`, the served template, any legend or title function, or `_dash_option_rules` beyond the four `axislist` tokens (S04/S05/S06 own the rules table in batches 1-2; batch 8 has no other rules editor).
- Does not add minor ticks by default (`numticks_g *_minor 0`).
- Does not read CMYK/HSV scheme values (M7).

## Stata truth

Script `scripts/extract_minor_tick_truth.do` -> `test/fixtures/minor_tick_truth.json` (R7: `_meta` with `stata_version`, `born_date`, `dash_commit` via `shell git rev-parse HEAD` into a file read by `file read`, `extracted`, `source`; the python block reads locals through `Macro.getLocal`; `git add -f`). Head copied from scripts/extract_default_base_truth.do (:21-48). Cases, each `quietly twoway ... , name(u24k, replace)` then `classutil describe .u24k.xaxis1.minor` once (its member names go in `_meta.members`) and the values read from `.u24k.xaxis1.minor.ticks` / `.n` (the tickset's tick positions; if the member is named otherwise the describe output says so and the script reads that):

| key | command | values |
|---|---|---|
| m_between5 | `scatter mpg weight, xlabel(0(1000)5000) xmtick(##5)` | minor positions (expect 250-step values between 0 and 5000, 20 of them) |
| m_between_uneven | `scatter mpg weight, xlabel(1000 2000 4000) xmtick(##5)` | minor count (expect 0) |
| m_explicit | `scatter mpg weight, xmtick(1500 2500)` | positions 1500 2500 |
| m_labels | `scatter mpg weight, xmlabel(1500 "a" 2500)` | positions and label texts |
| m_sizes | `scatter mpg weight, xmtick(1500) xtick(2500)`; SVG export | the two tick lengths in SVG units (minor shorter: half_tiny vs tiny) |
| m_refusal | `capture scatter mpg weight, xlabel(##5)` | `_rc` and the log line (expect r(198) or twoway's "##N ignored" note; recorded, not guessed) |
| m_axis2 | `scatter mpg weight \|\| scatter price weight, yaxis(2) ymtick(5000 10000, axis(2))` | positions on `.yaxis2.minor` |

Run: `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s24 $WT/scripts/extract_minor_tick_truth.do` (`global dash_nobrowser 1` in the script). `test_minor_ticks.py::TestTheFixture` names the fixture (test_fixtures_are_committed.py).

## TDD test stubs

### Regression tests, `test/test_minor_ticks.py` (new; red at `6370ca4` unless marked guard)

Helpers: `_figs(mode, graph_opts, plots=None)` renders one scatter of the auto frame in both modes (test_axis_options.py's `_saved`/`_served` helpers); `_minor_ticker(fig, which)` returns the axis's `CustomJSTicker` args; `_minor_labels(fig, which, axis_no)` the `dash_minor_labels` models with those tags. Every drawing class is parametrized `mode in ("saved", "served")`.

- Test: the fixture exists with the four `_meta` keys and every key of the truth table -- `TestTheFixture::test_meta_is_stamped`, `::test_every_case_was_measured` (guard after 24-01).
- Test: `xmtick(1500 2500)` puts `[1500.0, 2500.0]` in the x ticker's `mextra` and no `extra` -- `TestMinorTicksAreDrawn::test_explicit_positions[mode]` (red: no CustomJSTicker).
- Test: `xmtick(a(b)c)`, `minmax`, `#3` -- `::test_rule_forms[mode-form]` (red).
- Test: `xmtick(##5)` with `xlabel(0(1000)5000)` sets `between == 5`, and the Python finisher writes 20 positions equal to the fixture's `m_between5` -- `TestBetweenRule::test_between_matches_twoway[mode]` (red).
- Test: uneven majors give no between positions -- `::test_uneven_majors_draw_nothing[mode]` (red).
- Test: minor tick length is `round(scheme.minortick_length_px)` (3 px under s2color) when no xtick(), and xtick's length when both -- `TestMinorLength::test_half_tiny_alone[mode]`, `::test_shared_slot_takes_the_major_length[mode]` (red: AttributeError `minortick_length_px`).
- Test: `xmlabel(1500 "a" 2500)` draws one `LabelSet` named `dash_minor_labels` with texts `["a", "2500"]`, `y_units == "screen"`, `text_font_size == scheme.minortick_label_font_size` -- `TestMinorLabels::test_texts_and_units[mode]` (red); on a `%td` axis the text is the date writer's -- `::test_date_axis_text[mode]` (red); y axis uses `x_units == "screen"`, `text_align == "right"` -- `::test_y_axis_geometry[mode]` (red).
- Test: `ymtick(5000 10000, axis(2))` reaches `graph_options["ymtick2"]` (parser fixture from 24-01's probe JSON written by `_dash_serve_spec`) and draws `Label` models with a `Node` y -- `TestAxisTwo::test_routed_to_the_second_axis`, `::test_labels_use_frame_nodes[mode]` (red).
- Test: `tmtick()`/`tmlabel()` on a `%td` x axis draw as `xmtick`/`xmlabel` -- `TestTimeAxis::test_folded_onto_x[mode]` (red).
- Test: no option -> no minor ticks (`minor_tick_out == 0` or no CustomJSTicker) and `scheme.numticks_minor == {"x": 0, "y": 0}` under every shipped scheme -- `TestNoMinorByDefault::test_none_drawn[mode]`, `::test_every_scheme_says_zero` (red: attribute missing).
- Test: `xtick(10 20)` alone: ticker args keys `{"base", "extra"}`, same minor length as at base -- `TestXtickIsUnchanged::test_args_and_length[mode]` (guard).
- Test: after a saved move (node) and a served move, explicit positions are unchanged and `##5` positions follow the new majors -- `TestAfterAMove::test_explicit_hold[mode]`, `::test_between_follows_the_majors[mode]` (red).
- Test: `grid` on `xmtick()` sets the minor grid colour; default leaves it None -- `TestMinorGrid::test_grid_word[mode]` (red).
- Test: no note is printed for any of the six options or the four axis-2 forms -- `TestSilentWhenHonoured::test_no_note[option]` (red: the note names them).
- Test: a hostile label text (`<img src=x onerror=...>`) is the LabelSet's column value verbatim and appears nowhere in the saved HTML outside the Bokeh JSON -- `TestLabelTextIsACanvasSink::test_raw_in_column_only` (guard; joins test_label_sinks.py's inventory as a `Carrier`).

### Cases in cscripts

- `test/test_wp31_truth.cscript` block `* ==== S24 D1: Minor ticks and labels ====`: U24-1 (between positions equal twoway's, read from `.u24k.xaxis1.minor` live and from dash's spec through a `python:` render), U24-2 (uneven majors: 0 minors both sides), U24-3 (explicit positions), U24-4 (label texts), U24-6 (axis(2) positions). Red at base except the twoway halves.
- `test/test_option_validation.cscript` U24-5: `dash scatter mpg weight, xlabel(##5)` has twoway's `_rc` and words (`capture noisily twoway` beside `capture dash` in the same run; D-24.d). Guard if already equal at base, else red.

### Flips (in place, each with a `Flipped:` line)

- test_unsupported_report_is_true.py: move `xmtick`, `xmlabel`, `ymtick`, `ymlabel`, `tmtick`, `tmlabel` entries from the pending tables to `LIVE_VALUES` with two values that render differently (`"xmtick": ("1500 2500", "2000", "scatter")`); counts at :240-262 and :725-726 move with `# <measured old> -> <new>: D1 <why>` comments: declared graph +4 (the axis(2) minor forms), pending graph -6 and pending plot -6 (the six options drawn); each old value is recounted at the batch-8 base with the file's `_declared_plot()`/`_declared_graph()`/`_plot_pending()`/`_graph_pending()` helpers, never copied from another section's plan (DECISIONS A33).
- test_scheme_chrome.py::TestTheChromeKeysAreRead: the required stub set gains `gsize minortick`, `gsize tickgap`, `numticks_g horizontal_minor`, `numticks_g vertical_minor`.

### Parity corpus (R8; appended, guards at base)

test_mode_parity.py under `# WP-31 D1 (section 24): minor ticks and labels`: `CORPUS` cases `"xmtick(##5) xmlabel(1500 2500) ymtick(20 30)"` and `"ymtick(5000, axis(2)) on a yaxis(2) layer"`; `MOVE_CORPUS` case `_move_case("xmtick(##5) after a dropdown move (WP-31 D1)", _MOVES[0], [plot_for("scatter")], go={"xlabel": "0(1000)5000", "xmtick": "##5", "xmlabel": "1500 2500"})`. `ALLOWED` untouched.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Explicit/rule positions in the ticker | pytest test_minor_ticks.py | -- | yes |
| `##N` equals twoway's positions | pytest + cscript U24-1/U24-2 | minor_tick_truth.json | yes |
| Minor length and colour | pytest | scheme_truth.json | yes |
| Minor labels: text, size, units, axis 2 Nodes | pytest + U24-4/U24-6 | minor_tick_truth.json | yes |
| Hold across a move | pytest (node + served) | -- | yes |
| `##N` refused on xlabel() | cscript U24-5 | live twoway | n/a |
| Schemes carry the stubs | pytest test_scheme_chrome.py | scheme_truth.json | n/a |
| Help/Unsupported/audit agree | pytest test_help_conformance.py | -- | n/a |

Acceptance: AC-24.1 every red stub green in both modes; AC-24.2 U24-1..U24-6 PASS through the driver, no SKIP; AC-24.3 xtick()-only axes unchanged (guard green); AC-24.4 `git diff --stat` after the generator shows 26 scheme files and the fixture only; AC-24.5 test_help_conformance.py, test_unsupported_report_is_true.py, test_label_sinks.py, test_csp.py green.

## Tasks

**Commit boundary.** Tasks 24-01 to 24-04 form the one D1 commit, subject `Draw minor ticks and minor labels as twoway does (WP-31 D1)`, made by 24-04 on `wp31-s24` in `$WT=<worktrees>/wp31-s24`. Body: `<scratch>/24-01-failure.txt`, the measured defect, what changed where (both modes; the two finishers; the 26 schemes), then `Regression: test/test_minor_ticks.py::<Class>::<test> -- failed at 6370ca4 with <text>` lines, `Regression: test/test_wp31_truth.cscript U24-1..U24-4, U24-6`, `Regression: test/test_option_validation.cscript U24-5`, one `Flipped:` line per flip, `Fixture: test/fixtures/minor_tick_truth.json (scripts/extract_minor_tick_truth.do)`, `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`, `BUGS.md: "<D1 title>" (closed)`, `GAPS3: D1 Tracked`. No tooling names.

<task type="auto" id="24-01">
  <name>Measure twoway and write failing tests</name>
  <files>scripts/extract_minor_tick_truth.do, test/fixtures/minor_tick_truth.json, test/test_minor_ticks.py</files>
  <action><![CDATA[
    Check `git -C $WT rev-parse HEAD` equals the batch-8 base sha and `git -C $WT branch --show-current` prints `wp31-s24`; `mkdir -p <scratch>/s24`. Create scripts/extract_minor_tick_truth.do from the head of scripts/extract_default_base_truth.do (:21-48) with the seven cases of "Stata truth" (a `classutil describe` of `.u24k.xaxis1.minor` recorded in `_meta.members`; SVG export of m_sizes through cert_svg.do's reader); run `DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s24 $WT/scripts/extract_minor_tick_truth.do`; `git add -f test/fixtures/minor_tick_truth.json`. Create test/test_minor_ticks.py with exactly the classes and tests of "TDD test stubs / Regression tests" (module docstring: the defect, the probe commands, the fixture keys); the parity and flip edits wait for 24-04. Run `python3 -m pytest test/test_minor_ticks.py -q -n0 -p no:cacheprovider -rf > <scratch>/s24/24-01.log 2>&1` and write `<scratch>/24-01-failure.txt`: the base sha, each failing node with its one-line reason, then the guards that passed. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/minor_tick_truth.json'));print(sorted(d['_meta'])[:4], len(d['m_between5']['positions']))"` prints `['born_date', 'dash_commit', 'extracted', 'members'] 20` (or the measured count, recorded); `grep -c FAILED <scratch>/s24/24-01.log` is at least 20; no FAILED line names TestTheFixture, TestXtickIsUnchanged or TestLabelTextIsACanvasSink; `test -s <scratch>/24-01-failure.txt`.]]></verify>
  <done>twoway's minor-tick positions, label texts, lengths and refusal were recorded in a stamped fixture, and every regression test was shown failing on the unmodified tree with its failure text saved.</done>
</task>

<task type="auto" id="24-02">
  <name>Declare axis-2 minor keys and unpend</name>
  <files>dash.ado, dash_parse.mata</files>
  <action><![CDATA[
    In dash.ado apply TR-24.1: delete the six `_dash_pending` lines for xmlabel, xmtick, tmlabel, tmtick, ymlabel, ymtick in the graph block (:1032-1041) and the plot parser's block (:1356-1387), with the two "WP-30 P1.6" comment lines above tmlabel; add `XMLABEL2(string asis) YMLABEL2(string asis) XMTICK2(string asis) YMTICK2(string asis)` after `XLABEL2(string asis)` in both parsers' syntax; add the four `sreturn local` lines (and `g_` forms) after the `xlabel2` ones; insert `xmlabel2 ymlabel2 xmtick2 ymtick2` after `xlabel2` in all seven key lists; append `xmtick2=axislist  ymtick2=axislist  xmlabel2=axislist  ymlabel2=axislist` as a new continuation line after :3051. In dash_parse.mata apply TR-24.2 (`_dash_axfam` rows mlabel2/mtick2; `_dash_rep_cat` "L" list; header comment :421). Run `python3 -m pytest test/test_abbreviations.py -q -k "seven_graph_key_lists or prefix" -p no:cacheprovider` and `python3 -m pytest test/test_unsupported_report_is_true.py -q -p no:cacheprovider -rf > <scratch>/s24/24-02.log 2>&1` (expected red on the count pins only, fixed in 24-04).
  ]]></action>
  <verify><![CDATA[`grep -c "_dash_pending' [xyt]m\(tick\|label\)\"" dash.ado` prints 0; `grep -c "xmtick2" dash.ado` prints at least 10 (syntax x2, sreturn x2, seven lists, one rule); `grep -n '"mtick2"\|"mlabel2"' dash_parse.mata` prints two lines; the abbreviations test run prints `passed` for the seven-lists node.]]></verify>
  <done>The six minor-tick options left both pending blocks and their axis(2) copies gained declared keys routed by the axis-family table.</done>
</task>

<task type="auto" id="24-03">
  <name>Draw minor ticks, labels and finishers</name>
  <files>dash_render.py, scripts/extract_scheme_truth.py, test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    Apply TR-24.3 to TR-24.8 and TR-24.10 in dash_render.py in this order: SchemeParser attributes and `apply_to_axis` (:10598-10606, :11574-11584, `_tick_length_px` :9980); `_DASH_MINOR_RULE_RE` and the `minor=` keyword of `_dash_parse_axis_spec` (:30297); `_DASH_MTICK_JS` after `_DASH_TICK_EXTRA_JS`; `_dash_apply_minor_ticks` after `_dash_apply_tick_option` (:31540) with the step list of TR-24.5 and imports inside the function; the two call sites (TR-24.7); the Python step in `_dash_refinish_axes` after :32988 and the JS step in `_DASH_AXIS_FINISH_JS` (TR-24.8); the two copy-list entries (TR-24.10: the function entry after S23's `"_dash_contour_surface",`, else after `"_dash_apply_tick_option",`) and the function_test_map.py entry. Apply TR-24.9 to scripts/extract_scheme_truth.py and run `/opt/homebrew/bin/python3.14 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json` twice; `git add -f test/fixtures/scheme_truth.json`. Run `python3 -m pytest test/test_minor_ticks.py test/test_scheme_chrome.py test/test_axis_options.py test/test_statistical_helpers.py -q -p no:cacheprovider -k "not Chrome" > <scratch>/s24/24-03.log 2>&1`.
  ]]></action>
  <verify><![CDATA[`grep -c "gsize minortick\b" dash-*.scheme | grep -vc ":1$"` prints 0 (every file has exactly one); `grep -c "numticks_g horizontal_minor" dash-s2color.scheme` prints 1; the second generator run prints no "corrected" or "appended" line; `tail -1 <scratch>/s24/24-03.log` shows 0 failed except the test_unsupported pins (not in this run); `python3 -c "import dash_render as d; print(callable(d._dash_apply_minor_ticks))"` prints True.]]></verify>
  <done>Both renderers drew minor ticks in the scheme's length and colour, minor labels as frame-edge LabelSets and Labels, and the between rule survived the Python and JavaScript finishers; every shipped scheme carried the four minor stubs.</done>
</task>

<task type="auto" id="24-04">
  <name>Certify, flip, document and commit D1</name>
  <files>test/test_wp31_truth.cscript, test/test_option_validation.cscript, dash.sthlp</files>
  <action><![CDATA[
    Append the S24 block (`* ==== S24 D1: Minor ticks and labels ====` ... `* ==== end S24 ====`, R1 form, U24-1..U24-4, U24-6) above the marker line of test/test_wp31_truth.cscript and U24-5 to test/test_option_validation.cscript (its `nfail`/`faillist` form; `*! U24-5` header line). Write the driver `printf 'global dash_nobrowser 1\ncd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp31_truth.cscript > <scratch>/s24/run_truth.do` and run `WP31_ONLY=S24 scripts/stata_slot.sh <scratch>/s24 <scratch>/s24/run_truth.do`; the same for test_option_validation.cscript. Flip the pins (TDD "Flips") in test_unsupported_report_is_true.py and test_scheme_chrome.py; append the parity cases (R8); add the `dash_minor_labels` Carrier to test_label_sinks.py. Apply TR-24.11 to dash.sthlp and TWOWAY_COVERAGE_AUDIT.md. Close the D1 BUGS.md entry (BRIEF form), rewrite the GAPS3 `D1 Tracked` line to `- **D1 Tracked:** Closed in WP-31, BUGS.md "<D1 title>", commit pending.` (write `commit pending`; the merger's step k.3b fills the sha, DECISIONS A11), replace `<!-- WP-31 D1 -->` with a Results line `dash scatter mpg weight, xmtick(##5): no minor ticks -> four between each pair of major ticks (WP-31 D1)`. Run `python3 -m pytest test/test_minor_ticks.py test/test_unsupported_report_is_true.py test/test_help_conformance.py test/test_label_sinks.py test/test_mode_parity.py -k "D1 or minor or Unsupported or sink" -q -p no:cacheprovider`, then `git add -A` and commit with the body of "Commit boundary"; `git log -1 --format=%B | grep -ci "claude\|anthropic"` must print 0.
  ]]></action>
  <verify><![CDATA[`grep -c "U24-[1-6] PASS" <scratch>/s24/*.log` sums to 6 and `grep -c SKIP <scratch>/s24/run_truth.log` prints 0; `grep -c "Minor ticks and minor labels" dash.sthlp` prints 0 and `grep -c "Minor ticks and labels" dash.sthlp` prints 1; `grep -c "^- \*\*D1 Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1; `git log -1 --format=%s` ends `(WP-31 D1)`.]]></verify>
  <done>D1 was certified against twoway, its pins flipped with reasons, its help, audit, BUGS and GAPS3 lines rewritten, and one green commit landed on wp31-s24.</done>
</task>

## Section completion criteria

- The six options and their four axis(2) keys are drawn in both modes and printed about by nothing; `##N` matches twoway's positions and draws nothing on uneven majors.
- Minor ticks are `gsize minortick` long (xtick's length when the slot is shared, documented), minor labels `gsize minortick_label` in `color tick_label`.
- Every shipped scheme carries the four stubs; `scheme_truth.json` is regenerated, never hand-edited.
- Explicit minor positions hold and `##N` positions follow the majors after saved and served moves.
- U24-1..U24-6 PASS; every flip recorded; help, Unsupported list, audit, BUGS.md, GAPS3 §9 and CHANGELOG updated in the one `(WP-31 D1)` commit.

## Notes

- **Renderer order.** Saved: `apply_to_figure` (sets the scheme's minor colour) -> `_dash_apply_axis_options` (xtick, then this section's minor step) -> `_dash_refinish_axes` after the layers. Served: the template calls the same module functions (`_dash_figure_for`, line 104 of the excerpt at :49380-49560); no template edit.
- **Copy lists (R2):** constants after `"_DASH_AXLABEL_HONOURED",` (:46641); functions after S23's `"_dash_contour_surface",` (fallback `"_dash_apply_tick_option",` :47027 if S23 has not landed), so S23's and S24's batch-8 hunks do not collide (A7). `SchemeParser` methods travel with the class.
- **R11:** S24 is batch 8's only editor of `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS`; S33 (batch 11) and S35 (batch 12) come after.
- **R12:** S24 edits none of `_FILTER_JS`, `_generate_app_source`, `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets`, the four `_apply_*` appliers or `_dash_layout_cell`; `_dash_option_rules` gains four `axislist` tokens only (no other batch-8 section edits it).
- **R6:** no new program; `_dash_rep_cat` and `_dash_axfam` are data edits; the seven key lists change together.
- **R7:** two fixtures (`minor_tick_truth.json` new; `scheme_truth.json` regenerated), both `git add -f`.
- **R8:** CORPUS/MOVE_CORPUS appended under the section comment; `ALLOWED` untouched.
- **R9/R10:** flips in place; count pins move with `# <measured old> -> <new>: D1 ...` comments, the old value measured at the base (A33).
- **R3:** S24 owns the axis_options paragraph it adds and the Unsupported paragraph it removes; S56 owns the rest.
- **python_exec hazard:** check `grep python_exec ~/.stata19/console/stata19.rc` after each slot run; exit 222 is a SKIP, not a pass.
- **For S33:** read `axis._dash_scheme_look["minor_length"]` and the ticker's `mextra`/`between` args; never rebuild the CustomJSTicker.
- **Commit-body line forms** are BRIEF's with `failed at 6370ca4`.
