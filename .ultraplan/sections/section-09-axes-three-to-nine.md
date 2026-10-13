# Section 09: Axes three to nine

> Part of: WP-31 · GAPS3 rows: C10c (the axes 3-9 part of C10) · Risk: red · Batch: 3 · Depends on: 01, 06 · Blocks: 35 · Tasks: 4, 1 commit · Case-id prefix: U09

## Overview

**What is wrong today.** GAPS3 C10 (4.C): "Values twoway accepts are refused: ... `yaxis(1 2)`, axes 3-9." Evidence dash.ado:2995 `yaxis=int,1,2  xaxis=int,1,2` in `_dash_option_rules`, and :3147-3149 in `_dash_validate_value`: `if inlist("`opt'", "yaxis", "xaxis") { local extra ". dash draws two axes." }`, so `dash scatter mpg weight, yaxis(3)` is `dash: yaxis() must be an integer between 1 and 2 (got: 3). dash draws two axes.` r(198). twoway (`B/a/axis_choice_options.sthlp:161-165`): "You may have up to nine y axes and nine x axes ... When there are three or more y axes (or x axes), the axes are stacked up on the left (on the bottom)." Everything in dash that knows a second axis knows exactly one: `_dash_route_axis2` (dash_parse.mata:7015-7061) rewrites `axis(2)` into `ylabel2()`-style keys and `continue`s for any other number (:7050-7051 `else if (n == 2 & fam[r, 6] != "") dn = d + fam[r, 6]; else continue`); `_dash_add_secondary_axes` (dash_render.py:31720-31823) builds `extra_y_ranges["y2"]`/`extra_x_ranges["x2"]` only; `_dash_finish_secondary_axes` (:32581ff) loops over the two names; `_dash_assign_axis_ranges` (def :33568, :33578-33594), `_dash_layer_axis_names` (:1271), `_dash_axis_vars` (:1307), `_dash_axis_tick_formats` (:1431-1432), `_dash_axis_date_kind` (:1471), `_dash_count_axes` (`letter + "2"`), the orphan note `_DASH_AXIS2_KEYS` (:3708, :3986) and `_dash_lone_second_axes` (def :4000, the test at :4028-4036) all test `== "2"` at `6370ca4`. `yaxis(1 2)` (a layer on both axes) is S06's (C10b), which lands in batch 2 before S09 is cut (A32): on S09's base the token is `yaxis=axes,1,2`, every one of those sites reads `"2" in _dash_axis_tokens(...)`, and `_dash_add_glyph` draws one copy per token with `_dash_assign_axis_ranges` returning early for a multi-token option; S09 generalises that tree, not `6370ca4`'s.

**After this section.** `yaxis(#)`/`xaxis(#)` take 1-9 with twoway's own bound message for 0 and 10 (measured). A layer on axis n≥2 draws on `extra_y_ranges["y<n>"]`/`extra_x_ranges["x<n>"]`, each with its own `LinearAxis`/`LogAxis`/`DatetimeAxis`, placed on the side twoway places it (fixture; help: 1 left, 2 right, three or more stacked on the left; x alike below). `axis(n)` on `ytitle() ylabel() ytick() yline() yscale()` (and x, and the t family) reaches axis n through the same routing that serves axis 2, in both modes. The "dash draws two axes" sentence is gone. The second-axis move behaviour (D9) is S35's and is built on this generalisation.

**Test order and commit rule.** One row, one commit `(WP-31 C10c)`: 09-01 writes the extractor, fixture and every regression test red, no commit; 09-02 the Stata side; 09-03 the renderer; 09-04 certifies, documents, closes and commits.

### Section decisions (binding on the executor)

- **D-09.a Axis n≥3 options travel in one JSON key, `axisn`, not in seventy new options.** `_dash_route_axis2` rewrites `axis(2)` into dash's `ylabel2()`-family keys because those keys are declared options with their own `sreturn`s and seven key lists (dash.ado:5776, 6714, 6748, 6849, 6924, 6956, 7339). Declaring `ylabel3()..yline9()` for both letters and five families would add 70 declarations, 70 `sreturn`s, 70 names in each of the seven lists and 70 `_dash_rep_cat` names. Instead the route REMOVES an `axis(n)` token with 3 ≤ n ≤ 9 from the returned option text and records it in an external Mata matrix `_dash_axisn` (letter, n, family, value with the axis word removed exactly as the axis-2 rewrite forms it, segment), the pattern of `_dash_axreq_add` (dash_parse.mata:7063-7166). `_dash_plot` clears it at start (`_dash_axisn_clear()`, beside `_dash_axreq_clear`) and the graph JSON writer (:7335-7415) adds `"axisn":<object>` from `_dash_axisn_json()` when the matrix is non-empty: `{"y3":{"label":"...","title":"...","tick":"...","line":"...","scale":"..."},"x4":{...}}`, copies of one (letter, n, family) merged with `_dash_rep_merge(<letter><family>2, v1, v2)` (the axis-2 key's category: L, T, L, X, S). The renderer reads `graph_opts["axisn"]` (a dict; anything else is ignored) through one accessor `_dash_axisn_value(graph_opts, name, family)` that returns `graph_opts[f"{letter}{family}2"]` for n == 2 and `graph_opts["axisn"][name][family]` for n ≥ 3, so every reader of a second-axis option becomes a reader of "axis n". **Listed for ratification** (a departure from "every option is declared"; the alternative is the 70-fold expansion).
- **D-09.b Sides come from the fixture, with the help's rule as the hypothesis.** `SchemeParser.axis_side(which, number)` (dash_render.py:10800-10810) grows a third argument `count` (the number of distinct axes used on that letter): `count <= 2` keeps today's rule (1 first side, 2 the other, `alt_yaxes`/`alt_xaxes` swapping); `count >= 3` places EVERY axis of that letter on the first side (left/below), axis 1 innermost, then 2, 3, ... outward (Bokeh stacks `fig.left` in list order, innermost first). If `axes_truth` (the fixture, measured from SVG label positions) contradicts the hypothesis -- for example axis 2 stays on the right when a third exists -- the fixture's side per (count, number) is written into a module constant `_DASH_AXIS_SIDES = {(3, 1): "left", (3, 2): ..., ...}` that `axis_side` consults first; the test pins the constant to the fixture.
- **D-09.c Lone rewrite generalised to one number.** `_dash_lone_second_axes` (:4000-4060; REVIEW-1 R1-12): when every layer of a graph is on the same axis k ≥ 2 of a letter, that letter's axis becomes axis 1 and that graph's `axisn[<letter>k]` (or the `*2` keys for k = 2) become the first-axis keys, as today for k = 2. Layers spread over axes 2 and 3 with none on 1 are NOT rewritten here; which of them is drawn left is S35's "first-used axis" rule.
- **D-09.d The var-count, hover, legend and format readers compare axis numbers as integers, over S06's tokens (REVIEW-1 R1-03).** Every axis read goes through S06's `_dash_axis_tokens(opts, key)`; S09 adds `_dash_axis_nos(opts, letter) -> list[int]` = the distinct, sorted numbers of `_dash_axis_tokens(opts, letter + "axis")` each read by `_dash_axis_number` and clamped to 1..9 (`[1]` for anything else), and `_dash_axis_no(opts, letter) = max(_dash_axis_nos(opts, letter))` for single-copy readers (a copy drawn by `_dash_add_glyph`'s pair loop carries one token). Every `"2" in tokens` test listed in the Overview becomes an integer comparison, and every `"y2"`/`letter + "2"` name becomes `f"{letter}{n}"`. A `yaxis(1 2)` layer still yields two copies (`default`, `y2`): S06's feature must not regress. The services that need a letter's axis names iterate `range(2, 10)`.

## Risk: [red] -- fourteen second-axis readers in the renderer, a Mata route, the rules table, both modes, and S35 builds on it

**Why.** The number 2 is hard-coded in fourteen places across module and template; a miss draws a layer on the primary range silently (the WP-28 defect `_dash_assign_axis_ranges` fixed). The Mata route edits `_dash_route_axis2`, which every axis option passes through. The rules table is S05/S06's hot function in batch 2 -- S09 is in batch 3, after them, and edits one rule token.

**Risk factors.** (1) A reader missed; (2) the side rule unmeasured; (3) `_dash_axreq_check`'s "yaxis3 does not exist" refusal (dash_parse.mata:7168-7210) must keep refusing options for an axis no layer uses while accepting 3-9 when used; (4) `_g_ys`/`_g_xs` (the layers' axis numbers handed to `_dash_axreq_check`) must carry every number a layer names; (5) batch partners S08 (abbreviation table, `_dash_split_segs`) and S10 (`_FILTER_JS`) -- disjoint.

**Mitigation.** (1) `test_no_reader_tests_for_two` reads dash_render.py and asserts no `"2" in _dash_axis_tokens` (S06's form) or `== "2"` beside an axis key outside `_dash_axis_nos`; the parity corpus gains a 3-axis case in both modes; (2) the extractor measures sides for 2, 3 and 4 y axes and 3 x axes from twoway's SVG; (3) U09-5 pins both answers; (4) `grep -n "_g_ys" dash.ado` in 09-02 and a cscript case with `yaxis(3)` + `ylabel(, axis(3))`; (5) boundaries.

## Dependencies

- **Depends on: 01, 06** (DECISIONS A32: S06's `axes` kind `yaxis=axes,1,2`, `_dash_axis_tokens`, the pair loop in `_dash_add_glyph` and the `_dash_assign_axis_ranges` early return are the tree S09 is cut on; the anchors below were read at `6370ca4` and are re-read on the batch-2 landed tree, where the `== "2"` sites are S06's token reads). **Blocks: 35** (S35 recomputes `y<n>`/`x<n>` ranges after a move and places the first-used axis; it reads the `_dash_axisn_value` accessor and `axis_side(which, n, count)`).
- **Parallel batch: 3** with S10 (JS) and S08 (abbreviations). S09 owns `_dash_add_secondary_axes` (index owner table) and edits `_dash_route_axis2`, `_dash_option_rules` (one token: no S05/S06 in batch 3), `_dash_validate_value` :3147-3149, the renderer readers listed, `SchemeParser.axis_side`. It does not touch `_FILTER_JS`, `_expand_plottype_str`, `_dash_split_segs`, `_make_figure_body`, `_generate_app_source` (the template's `_dash_add_secondary_axes(...)` call at :49446 and `_dash_finish_secondary_axes` at :49640 keep their signatures).

## Evidence

Anchors at 6370ca4, re-read on the batch-2 landed tree before editing (S06 moved every `== "2"` site to a token read and the rule token to `yaxis=axes,1,2`; the line numbers drift).

### The bound and its sentence (dash.ado:2995, :3147-3149)

```stata
2995        yaxis=int,1,2  xaxis=int,1,2 ///
3147    if inlist("`opt'", "yaxis", "xaxis") {
3148        local extra ". dash draws two axes."
3149    }
```

The error form (:3615-3618): `dash: yaxis() must be an integer between 1 and 2 (got: 3). dash draws two axes.` r(198). twoway's own bound is compiled (`twowaygraph_g.class` ParseOpts strips `yaxis()`; its message for `yaxis(10)` is measured in 09-01, expected the `integer 1 to 9` form of `syntax`'s `numlist`).

### The route (dash_parse.mata:7015-7061) and the family table (:6878-6886)

```mata
6878    return(("title",  "title",   "title",  "2", "6", "title2" \
6879            "label",  "labels",  "label",  "2", "2", "label2" \
6880            "mlabel", "mlabels", "mlabel", "3", "3", ""       \
6881            "tick",   "ticks",   "tick",   "4", "4", "tick2"  \
6882            "mtick",  "mticks",  "mtick",  "3", "5", ""       \
6883            "line",   "lines",   "line",   "3", "7", "line2"  \
6884            "scale",  "scale",   "scale",  "3", "1", "scale2"))
7050        else if (n == 2 & fam[r, 6] != "") dn = d + fam[r, 6]
7051        else continue
7052        toks[i] = dn + "(" + (scale ? rest :
7053                  body + (rest == "" ? "" : ", " + rest)) + ")"
```

`_dash_ax_parse` (:6920) hands back `n`, the axis number the first axis word names, for any integer; `_dash_axreq_add`/`_dash_axreq_check` (:7063-7210) record every axis option and refuse one whose axis no layer uses: `"ylabels(...) not allowed, yaxis3 does not exist"` (:7196-7199). The layers' axis sets reach it as `_g_ys`/`_g_xs` (dash.ado:6975). mlabel/mtick rows have no axis-2 key (col 6 `""`): `ymlabel(, axis(2))` is named for the note today (comment :7010-7011; D1/S24 draws minor ticks).

### The renderer's readers of "2"

| Where | Line | Test |
|---|---|---|
| `_dash_layer_axis_names` | :1271 | `axis_no = 2 if ... == "2" else 1` |
| `_dash_axis_vars` | :1307 | `on = (2 if ... == "2" else 1)` |
| `_dash_axis_tick_formats` | :1431-1432 | `xa = "2" if ...`; keys `"x2"`,`"y2"` |
| `_dash_axis_date_kind` | :1471-1473 | `if axis in ("x2", "y2")` |
| `_DASH_AXIS2_KEYS`, the orphan note | :3708, :3986-3995 | `== "2"`, the five `*2` keys |
| `_dash_lone_second_axes` (def :4000) | :4028-4036 | `all(... == "2")` (`"2" in tokens` after S06) |
| `GlyphMapper._unit_kind` caller | :15905 | `two = ... == "2"` → `axis + "2"` |
| `_dash_add_secondary_axes` | :31764-31766 | the two tuples; `_compute_secondary_range(..., 2)`; `scheme.axis_side(n, 2)` at :31803 |
| `_dash_finish_secondary_axes` | :32636-32640 | the two tuples |
| `_dash_count_axes` | (def +60) | `letter if name == "default" else letter + "2"` |
| `_dash_assign_axis_ranges` (def :33568) | :33578-33594 | `use_y2`, `"y2"` (S06: `"2" in _dash_axis_tokens(options, "yaxis")`, with an early return for a multi-token option) |
| `_dash_axis_default_titles` | :28538 | already takes any `yaxis=`/`xaxis=` number (`str(yaxis) in ...split()`) -- no change |
| saved call site | :43792-43799 | `date_axes` dict keyed `"y2"`,`"x2"` from `_ya2`,`_xa2` |
| served template | :49446, :49640 | the calls (signatures kept) |
| `SchemeParser.axis_side` | :10800-10810 | `other if number == 2 else first` |

`_compute_secondary_range(df, plots, axis_key, var_key, axis_number=2, padding_pct=0.05)` (:11840) already takes any number.

### Tests that pin today's two-axis world (flip or extend, never delete)

- test/test_dual_axis.py `TestSecondaryAxisSecurity::test_non_numeric_yaxis_treated_as_primary` (:283): keep; add `yaxis(3)` cases beside it.
- test/test_axis2_suboptions.py `TestTheRouteUnit::test_axis_number_unit` (:526): parametrised numbers; if a case asserts that 3 is "not routed", flip to the `axisn` record.
- test/test_option_validation.cscript cases asserting `yaxis(3)` r(198) and "dash draws two axes" (`grep -n "two axes\|yaxis(3)\|xaxis(3)" test/*.cscript test/*.py` in 09-01): flip to rc 0.
- test/fixtures/rejected_options.json rows for `yaxis(3)` if any (`grep -n '"yaxis(3' test/fixtures/rejected_options.json`): the reader test's expectation flips.

## User stories

- **US-09.1** As a twoway user, I want `(scatter a x, yaxis(1)) (scatter b x, yaxis(2)) (scatter c x, yaxis(3))` drawn with three y axes placed as twoway places them, in both modes.
- **US-09.2** As a twoway user, I want `ylabel(0(10)50, axis(3))`, `ytitle("C", axis(3))`, `yscale(log axis(3))`, `yline(20, axis(3))` and `ytick(, axis(3))` to reach the third axis.
- **US-09.3** As a twoway user, I want `yaxis(10)` refused with twoway's words, and no sentence about dash drawing two axes.

## Business requirements

- **BR-09.1** `yaxis(#)`/`xaxis(#)` accept 1-9 on every type that takes them; 0, 10 and a non-integer are refused with twoway's measured rc and line.
- **BR-09.2** A layer on axis n draws against a range spanning its own drawn values (the rule `_dash_finish_secondary_axes` applies to axis 2 today), with its own axis, titled by twoway's default-title rule over the layers on axis n.
- **BR-09.3** Axis placement equals the fixture's for every measured (count, number): y 1-2 as today; three or more y axes on the left in number order; x alike below.
- **BR-09.4** `axis(n)` sub-options on the five routed families reach axis n; `ymlabel()/ymtick()` with `axis(n)` are named as they are for axis 2 today; an axis option naming an axis no layer uses is refused as today (`yaxis3 does not exist`).
- **BR-09.5** The saved page and the served app draw identical axes (G3 parity); a lone axis k is drawn as the first axis.
- **BR-09.6** Nothing about one- and two-axis graphs changes (test_dual_axis.py, test_axis2_suboptions.py stay green).

## Technical requirements

- **TR-09.1 Rules.** dash.ado:2995 `yaxis=axes,1,9  xaxis=axes,1,9` (S06's `axes` kind, bound raised; REVIEW-1 R1-03); delete :3147-3149 (the `extra` for yaxis/xaxis; the `if ... else if "degree"` chain starts at `degree`). The message for 0/10 is dash's `must be an integer between 1 and 9` form unless the fixture's `bounds.yaxis10.text` differs, in which case `_dash_validate_value`'s yaxis/xaxis branch prints the fixture's text verbatim (copied as a literal with the fixture key in a comment).
- **TR-09.2 Mata route and registry (D-09.a).** dash_parse.mata: after `_dash_route_axis2`'s `else continue` (:7051) insert `else if (n >= 3 & n <= 9 & fam[r, 6] != "") { _dash_axisn_add(d, n, fam[r, 1], (scale ? rest : body + (rest == "" ? "" : ", " + rest)), seg); toks[i] = ""; any = 1; continue }` -- `_dash_route_axis2` gains a `seg` argument (its one caller dash.ado:5493 passes the segment number; the after-comma call passes `n_segs + 1` as `_dash_axreq_add` does) and the join loop skips empty tokens. New functions, placed directly after `_dash_axreq_check`: `_dash_axisn_clear()`, `_dash_axisn_add(d, n, family, value, seg)` (external `string matrix _dash_axisn`, 5 columns), `_dash_axisn_json()` (rows ordered by letter, n, family order of `_dash_axfam`, seg; copies merged with `_dash_rep_merge(d + family + "2", v1, v2)`; values escaped with `_json_escape`; returns `""` when empty). Header-index entries after `_dash_axreq_check`'s (:450); `_needed` (dash.ado:471 line) gains the three names in alphabetical place; program_coverage_map entries under `# WP-31 S09 (C10c): axes three to nine`. dash.ado `_dash_plot`: `mata: _dash_axisn_clear()` beside the existing `_dash_axreq_clear()` call (grep); the graph JSON writer (:7335-7415) adds, after the `graph_options` object's last key, `mata: st_local("_axn", _dash_axisn_json())` and `if `: length local _axn' local gopts_json `"`macval(gopts_json)',"axisn":`macval(_axn)'"'` (read the writer's actual local names first). `_g_ys`/`_g_xs`: confirm (grep :6975 region) they accumulate every `yaxis()` value as typed; no change expected.
- **TR-09.3 Renderer accessors (D-09.d).** New module helpers after `_dash_axis_number` (:3717): `_dash_axis_nos(opts, letter) -> list[int]` (S06's `_dash_axis_tokens(opts, letter + "axis")`, each token through `_dash_axis_number`, clamped to 1 when not 1..9, distinct, sorted; `[1]` when empty), `_dash_axis_no(opts, letter) -> int` (`max(_dash_axis_nos(...))`, for single-copy readers) and `_dash_axisn_value(graph_opts, letter, n, family) -> str` (D-09.a; `""` when absent; `graph_opts["axisn"]` must be a dict of dicts of str, else ignored). All three on the functions copy tuple after `"_dash_reference_lines",` (:47223; R2; S06's `_dash_axis_tokens` sits there already) and in test/function_test_map.py under `# WP-31 S09 (C10c)`. Replace every reader in the Evidence table: `_dash_layer_axis_names` returns `_dash_axis_no(opts, phys)`; `_dash_axis_vars(plots, axis_no)` tests `axis_no in _dash_axis_nos(opts, letter)`; `_dash_axis_tick_formats` keys `f"{letter}{n}"` for every n used; `_dash_axis_date_kind(fig, axis)` accepts `"y3"`..`"x9"` (the `kinds` lookup generalised: `fig._dash_axis_kinds` dict keyed by name -- read how `_x2_date`/`_y2_date` reach it at :43797 and store per name); `_DASH_AXIS2_KEYS` and the orphan note (:3986-3995) iterate n in 2..9 (n ≥ 3 through `_dash_axisn_value`); `_dash_lone_second_axes` per D-09.c; `GlyphMapper._unit_kind` caller :15905 `axis + str(n) if n > 1 else axis`; `_dash_count_axes` `letter if name == "default" else name`; `_dash_assign_axis_ranges` sets `r.y_range_name = f"y{n}"` with `n = _dash_axis_no(options, "y")` when `n >= 2 and f"y{n}" in fig.extra_y_ranges` (x alike), keeping S06's early return for a multi-token option (the pair loop assigned per copy).
- **TR-09.4 `_dash_add_secondary_axes`.** The two-tuple loop becomes `for letter, var_key, rng_attr, kw, dflt_side in (("y", "yvar", "extra_y_ranges", "y_range_name", "right"), ("x", ...))`: `used = sorted({n for p in plots for n in _dash_axis_nos(p.get("options", {}), letter)} - {1})` (every number a `yaxis(1 2)`-style layer names counts; R1-03); for `n in used`: name `f"{letter}{n}"`, `_compute_secondary_range(frame, plots, letter + "axis", var_key, n)`, title through `_dash_textbox_or_default(_dash_axisn_value(graph_opts, letter, n, "title"), f"{letter}title{n}", dflt, seen, key)` with `dflt = _dash_axis_default_titles(plots, var_labels, yaxis=n if letter == "y" else 1, xaxis=n if letter == "x" else 1)[...]`, log from `_dash_axisn_value(..., "scale")`, side `scheme.axis_side(letter, n, len(used) + 1)` (D-09.b; without a scheme the same rule in a module helper `_dash_axis_side_default(letter, n, count)`), `date_axes` keyed by name. Returns `has` as a dict `{name: True}` -- its two callers (:43792, :49446) unpack `_has_y2, _has_x2`: keep the return shape `(has_y2, has_x2)` AND attach `fig._dash_extra_axes = used_names` so callers needing the full list read the attribute (no signature change at the template call site). Docstring updated.
- **TR-09.5 `_dash_finish_secondary_axes`.** The two-tuple loop iterates `for name in list(fig.extra_y_ranges) + list(fig.extra_x_ranges)` whose names match `^[xy][2-9]$`, with `letter = name[0]`, `n = int(name[1])`, `sides` both sides of that letter, and every `graph_opts.get(f"{n}scale2")`/`label2`/`tick2`/`line2` read through `_dash_axisn_value(graph_opts, letter, n, family)`. `_DASH_SCALE2_SUBOPTS` unchanged. `_dash_scale_values2`/`_dash_scale_reverse2` dicts are already keyed by name.
- **TR-09.6 `SchemeParser.axis_side(which, number=1, count=2)`** per D-09.b, with `_DASH_AXIS_SIDES` consulted first when 09-01 filled it (a module constant appended as the last string of the constants copy tuple `for _name in ("_TEXTBOX_SUBOPTS", ...)` at :46584-46784, R2; REVIEW-1 R1-13: there is no `_DASH_STALE_STATUS_HTML` anchor in that tuple).
- **TR-09.7 The reference lines** (`_dash_reference_lines`, :38879 `rname = "y2" if opt == "yline" else "x2"`): a `yline` copy routed from `axisn[y<n>].line` is drawn on range `y<n>` -- iterate n in 2..9 reading `_dash_axisn_value(graph_opts, letter, n, "line")` (n = 2 is today's `yline2`).
- **TR-09.8 Security.** `axisn` values are user text already escaped by `_json_escape` into the spec and read as data; the renderer never evals them; names reaching Bokeh (`y3`..`x9`) are fixed literals. No new sink.

### Code to insert (verbatim where marked)

**TR-09.2 the route branch (dash_parse.mata, replaces :7050-7051):**

```mata
        else if (n == 2 & fam[r, 6] != "") dn = d + fam[r, 6]
        else if (n >= 3 & n <= 9 & fam[r, 6] != "") {
            // Axes three to nine (WP-31 C10c, D-09.a): the option leaves the
            // text and is recorded for the graph's "axisn" object.
            _dash_axisn_add(d, n, fam[r, 1],
                            (scale ? rest : body + (rest == "" ? "" : ", " + rest)), seg)
            toks[i] = ""
            any = 1
            continue
        }
        else continue
```

and the join loop (:7059) becomes `for (i = 1; i <= cols(toks); i++) { if (toks[i] == "") continue; out = out + (out == "" ? "" : " ") + toks[i] }`. The signature: `string scalar _dash_route_axis2(string scalar opts, real scalar seg)`; dash.ado:5493 passes the segment number its caller holds; the after-comma call passes `` `n_segs' + 1 ``.

**TR-09.2 the registry (dash_parse.mata, after `_dash_axreq_check`; verbatim):**

```mata
// ==== axes three to nine (WP-31 C10c) ======================================
// _dash_axisn_clear(), _dash_axisn_add(d, n, family, value, seg) and
// _dash_axisn_json(): the axis options written for axes 3-9 travel in the
// graph's "axisn" object, {"y3":{"label":"...","title":"..."},...}, one
// entry per (letter, axis, family); copies merge as the axis-2 key's
// category merges them (_dash_rep_merge).  Values are the user's text,
// escaped by _json_escape; nothing here is run.
void _dash_axisn_clear()
{
    external string matrix _dash_axisn
    _dash_axisn = J(0, 5, "")
}

void _dash_axisn_add(string scalar d, real scalar n, string scalar family,
                     string scalar value, real scalar seg)
{
    external string matrix _dash_axisn
    if (rows(_dash_axisn) == 0 | cols(_dash_axisn) != 5) _dash_axisn = J(0, 5, "")
    _dash_axisn = _dash_axisn \ (d, strofreal(n), family, value, strofreal(seg))
}

string scalar _dash_axisn_json()
{
    external string matrix _dash_axisn
    string scalar    out, name, fams, v
    string rowvector names, families
    real scalar      i, j, k

    if (rows(_dash_axisn) == 0 | cols(_dash_axisn) != 5) return("")
    families = ("title", "label", "tick", "line", "scale")
    names = J(1, 0, "")
    for (i = 1; i <= rows(_dash_axisn); i++) {
        name = _dash_axisn[i, 1] + _dash_axisn[i, 2]
        if (!anyof(names, name)) names = names, name
    }
    names = sort(names', 1)'
    out = "{"
    for (i = 1; i <= cols(names); i++) {
        fams = ""
        for (j = 1; j <= cols(families); j++) {
            v = ""
            for (k = 1; k <= rows(_dash_axisn); k++) {
                if (_dash_axisn[k, 1] + _dash_axisn[k, 2] != names[i] |
                    _dash_axisn[k, 3] != families[j]) continue
                v = (v == "" ? _dash_axisn[k, 4] :
                     _dash_rep_merge(_dash_axisn[k, 1] + families[j] + "2", v, _dash_axisn[k, 4]))
            }
            if (v == "") continue
            fams = fams + (fams == "" ? "" : ",") + char(34) + families[j] + char(34) +
                   ":" + char(34) + _json_escape(v) + char(34)
        }
        out = out + (i > 1 ? "," : "") + char(34) + names[i] + char(34) + ":{" + fams + "}"
    }
    return(out + "}")
}
```

(Copies of one key are appended in segment order, so the k-loop merges them in the order twoway reads them.)

**TR-09.3 the accessors (dash_render.py, after `_dash_axis_number`; verbatim; `_dash_axis_tokens` is S06's):**

```python
def _dash_axis_nos(opts, letter):
    """The axis numbers a layer's ``yaxis()``/``xaxis()`` names, each 1-9,
    distinct and sorted (WP-31 C10c over S06's token read); ``[1]`` for
    anything else.  *opts* that is not a dict counts as empty."""
    if not isinstance(opts, dict):
        return [1]
    out = set()
    for tok in _dash_axis_tokens(opts, letter + "axis"):
        n = _dash_axis_number(str(tok))
        out.add(n if isinstance(n, int) and 1 <= n <= 9 else 1)
    return sorted(out) or [1]


def _dash_axis_no(opts, letter):
    """The one axis number a single-copy reader wants: the largest of
    ``_dash_axis_nos`` (a copy drawn by ``_dash_add_glyph``'s pair loop
    carries one token, so this is that token)."""
    return max(_dash_axis_nos(opts, letter))


def _dash_axisn_value(graph_opts, letter, n, family):
    """The text of ``<letter><family>(..., axis(n))`` for axis *n* of
    *letter*: the ``ylabel2``-style key for n == 2, the graph's ``axisn``
    object for 3-9 (D-09.a); ``""`` when absent or malformed."""
    go = graph_opts if isinstance(graph_opts, dict) else {}
    if n == 2:
        v = go.get(f"{letter}{family}2", "")
        return v if isinstance(v, str) else ""
    axisn = go.get("axisn")
    if not isinstance(axisn, dict):
        return ""
    entry = axisn.get(f"{letter}{n}")
    if not isinstance(entry, dict):
        return ""
    v = entry.get(family, "")
    return v if isinstance(v, str) else ""
```

(`_dash_axis_number` returns an int or None per its docstring :3717ff; read it to confirm the return type.)

**TR-09.6 `SchemeParser.axis_side` (dash_render.py:10800-10810, replaces the body):**

```python
    def axis_side(self, which: str, number: int = 1, count: int = 2) -> str:
        """The panel axis *number* of *which* sits in among *count* axes of
        that letter: with one or two, y1 on the left (right under `yesno
        alt_yaxes yes', economist) and y2 opposite, x1 below (above under
        alt_xaxes) and x2 opposite (WP-30 P1.2a); with three or more every
        axis is stacked on the first side, as twoway stacks them
        (axis_choice_options.sthlp:161-165; WP-31 C10c, measured in
        test/fixtures/axes_n_truth.json sides.*)."""
        measured = _DASH_AXIS_SIDES.get((which, count, number))
        if measured is not None:
            return measured
        if which == "y":
            alt = self.alt_yaxes
            first, other = ("right", "left") if alt else ("left", "right")
        else:
            alt = self.alt_xaxes
            first, other = ("above", "below") if alt else ("below", "above")
        if count >= 3:
            return first
        return other if number == 2 else first
```

with `_DASH_AXIS_SIDES: dict = {}` as a module constant (filled from `<scratch>/s09/sides.txt` only when the fixture contradicts the rule; keys `(letter, count, number)`).

## Boundaries

- Not S09's: the y2/x2 range after a filter move, `_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS`, `_dash_axis_plan` (S35, R11); the first-used-axis side rule and `horizontal` with `yaxis(2)` titles (S35); `yaxis(1 2)` (S06); `ymlabel()/ymtick()` on any axis (S24); axis look sub-options (S33); `_FILTER_JS` (S10); `_make_figure_body`, `_generate_app_source` (template call sites unchanged); the help's Secondary axes section beyond the paragraph named in Notes.

## Stata truth

**New extractor** `scripts/extract_axes_n_truth.do` → `test/fixtures/axes_n_truth.json` (path-free form; `_meta` five keys; `git add -f`). Data `sysuse auto`; `set scheme s2color`. SVG export per graph (`graph export <work>/<key>.svg`) read by the python block with scripts/svg_truth.py (`svg_document`, `svg_axis_reading`): an axis's side is where its tick-label texts sit relative to the plot region's x extent (left/right) or y extent (below/above).

| Key | twoway command | Recorded |
|---|---|---|
| `bounds.yaxis0`, `yaxis10`, `yaxis_frac`, `xaxis10` | `scatter mpg weight, yaxis(0)` / `yaxis(10)` / `yaxis(2.5)` / `xaxis(10)` | rc and the message line |
| `sides.y2` | `(scatter mpg weight, yaxis(1)) (scatter price weight, yaxis(2))` | side of each y axis (by its label range: mpg 12-41, price 3291-15906) |
| `sides.y3`, `sides.y4` | the above plus `(scatter length weight, yaxis(3))` [+ `(scatter turn weight, yaxis(4))`] | side of each y axis and its order from the plot edge outward (label x positions sorted) |
| `sides.x3` | `(scatter mpg weight, xaxis(1)) (scatter mpg price, xaxis(2)) (scatter mpg length, xaxis(3))` | side and order of each x axis |
| `sides.y23_no1` | `(scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(3))` | sides (for S35's first-used rule; recorded here, read there) |
| `routed.label3`, `title3`, `scale3`, `line3`, `tick3` | the three-axis graph plus `ylabel(150(20)230, axis(3))` / `ytitle("Len", axis(3))` / `yscale(log axis(3))` / `yline(200, axis(3))` / `ytick(160 220, axis(3))` | rc; `.Graph.yaxis3.title.text`; the tick label texts of the third axis from the SVG; the line's y position |
| `refusals.axis3_unused` | `scatter mpg weight, ylabel(1 2, axis(3))` | rc and line (expected `ylabel(...) not allowed, yaxis3 does not exist` -- or twoway's actual words) |

**Truth block** (R1) `* ==== S09 C10c: Axes three to nine ====` appended by 09-01 above the marker line of test/test_wp31_truth.cscript (one row, one block, A14; S01 writes no stub, D-01.e), helpers `_u09_*` above the header:
- **U09-1** the three-axis graph registered with dash: both modes have `extra_y_ranges` keys `y2`, `y3`, three y axes, each layer's `y_range_name` as its option says; sides equal the fixture's `sides.y3`.
- **U09-2** the four-axis y graph and the three-axis x graph: sides equal `sides.y4`, `sides.x3`.
- **U09-3** each `routed.*` option: the third axis's title / ticks / type / line equal the fixture's, both modes.
- **U09-4** `yaxis(0)`, `yaxis(10)`, `yaxis(2.5)`, `xaxis(10)`: dash's rc and line equal the fixture's; the log holds no `two axes`.
- **U09-5** `ylabel(1 2, axis(3))` with no layer on axis 3: rc and line equal `refusals.axis3_unused`; with a layer on axis 3: rc 0.
- **U09-6** a lone `yaxis(3)` graph draws one left axis (D-09.c), both modes.

**Block skeleton** (WP-30 form):

```stata
// S09 helpers (WP-31 C10c).  _u09_axes: for a registered graph, saved and
// served, the list (side, range_name, axis_label) of every y or x axis in
// the order Bokeh stacks them, and each layer's range name; answers
// through globals u09_s, u09_v.
python:
(helpers, top level)
end
* ==== S09 C10c: Axes three to nine ====
local only : env WP31_ONLY
if inlist("`only'", "", "S09") & `: list posof "S09" in w31_run' {
display as text "S09 start " c(current_date) " " c(current_time)
sysuse auto, clear
dash clear
// U09-1
capture noisily dash (scatter mpg weight, yaxis(1)) (scatter price weight, yaxis(2)) ///
    (scatter length weight, yaxis(3)), name(u091)
_w31_expect U09-1 (_rc == 0) "three y axes rc `=_rc'"
tempfile sp dp
_dash_serve_spec, specpath("`sp'") datapath("`dp'")
python: _u09_axes("`sp'", "`dp'", "y")
_w31_expect U09-1 ("${u09_s}" == "${u09_v}") "saved and served axes differ: ${u09_s} vs ${u09_v}"
python: _u09_fixture_sides("y3")      // the fixture's sides into u09_f
_w31_expect U09-1 ("${u09_s}" == "${u09_f}") "sides ${u09_s}, twoway ${u09_f}"
_w31_done U09-1 "three y axes drawn on twoway's sides in both modes"
// U09-2 .. U09-6 likewise
dash clear
display as text "S09 end " c(current_date) " " c(current_time)
}
* ==== end S09 ====
```

**Area script** test/test_option_validation.cscript: **U09-7** `yaxis(3)` rc 0 on scatter, line, bar, rarea, histogram (one loop); **U09-8** `yaxis(1 2)` keeps S06's answer, two copies on `default` and `y2` (guard; R1-03).

## TDD test stubs

### Regression tests, `test/test_axes_three_to_nine.py` (new; red at 6370ca4 unless guard)

Helpers: `_figs(mode, spec)` as test_dual_axis.py `_lone_figure` builds saved and served figures; the fixture read once.

- Test: fixture stamped and complete -- `TestTheFixture::test_meta`, `::test_keys` (guard after 09-01).
- Test: `_dash_axis_nos` returns `[1]`, `[2]`, `[1, 2]`, `[3]` for `"1"`, `"2"`, `"1 2"`, `"3"` and `[1]` for junk; `_dash_axis_no` is its max; `_dash_axisn_value` reads n == 2 from the `*2` keys and n ≥ 3 from `axisn`, ignoring a non-dict -- `TestTheAccessors::test_axis_nos[value]`, `::test_axis_no_is_the_max`, `::test_axisn_value` (red: AttributeError).
- Test: a `yaxis "1 2"` layer on the three-axis spec still gives two copies with `y_range_name` `default` and `y2` (S06's feature, guard; R1-03) -- `TestThreeAxes::test_both_axes_layer_keeps_two_copies[mode]`.
- Test: a three-y-axis spec gives `extra_y_ranges` `{y2, y3}`, three LinearAxis on the fixture's sides in order, and layers' `y_range_name`s `default, y2, y3`, both modes -- `TestThreeAxes::test_ranges_axes_and_sides[mode]` (red), `::test_four_y_axes[mode]`, `::test_three_x_axes[mode]` (red).
- Test: `axisn` title/label/scale/line/tick reach axis 3 -- `TestRoutedOptions::test_each_family[mode-family]` (red).
- Test: each y<n> range spans its layer's drawn values with twoway's rule, as y2 does today -- `TestEachRangeSpansItsLayer::test_hull[mode-n]` (red).
- Test: a lone `yaxis(3)` is drawn as the first axis -- `TestLone::test_lone_three[mode]` (red).
- Test: no reader compares an axis option to the literal "2" outside the accessor -- `TestNoReaderTestsForTwo::test_grep` (red).
- Test: `axis_side(which, n, count)` for the fixture's (count, n) pairs -- `TestSides::test_each_measured_pair` (red).
- Test: the served app carries `_dash_axis_nos`, `_dash_axis_no`, `_dash_axisn_value`, `_DASH_AXIS_SIDES` -- `TestCopyLists::test_names` (red).
- Test: one- and two-axis graphs are unchanged (digest of test_dual_axis.py's `_LONE` and `DUAL_Y` figures: axes, sides, range names) -- `TestNothingElseMoved::test_two_axis_profile[mode]` (guard).

### Cases in cscripts

- `test_wp31_truth.cscript` U09-1..U09-6 (red; U09-5's second half guard).
- `test_option_validation.cscript` U09-7 (red), U09-8 (guard); flips found by 09-01's grep.

### Parity corpus (R8)

test/test_mode_parity.py under `# WP-31 S09`: `CORPUS` "three y axes" (`[_sc(), plot_for("scatter", {"yaxis": "2"}, yvar="price"), plot_for("line", {"yaxis": "3"}, yvar="length")]`), "three y axes with axisn label and title" (`go={"axisn": {"y3": {"label": "150(20)230", "title": "Len"}}}`), "three x axes"; `MOVE_CORPUS` "three y axes, dropdown" (S35 extends the move profile).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Bounds 1-9, twoway's words | cscript U09-4, U09-7 | `bounds.*` | n/a |
| Three/four y, three x axes drawn and placed | pytest `TestThreeAxes`, `TestSides`; cscript U09-1, U09-2 | `sides.*` | yes |
| axis(n) routing | pytest `TestRoutedOptions`; cscript U09-3 | `routed.*` | yes |
| Unused axis refused | cscript U09-5 | `refusals.*` | n/a |
| Lone axis k | pytest `TestLone`; cscript U09-6 | -- | yes |
| Registries, copy lists | pytest `TestCopyLists`, test_function_test_map.py, test_program_coverage_map.py, `TestTheServedAppCarriesEveryName` | -- | -- |
| Parity | `python3 -m pytest test/test_mode_parity.py -q -n0 -k "S09 or axes"` | -- | yes |

**Acceptance criteria**
- **AC-09.1** `yaxis(3)`..`yaxis(9)` rc 0 on every type taking `yaxis()`; 0/10/2.5 return the fixture's rc and line; the string `two axes` is absent from dash.ado.
- **AC-09.2** Sides for every fixture `(count, n)` pair match in both modes.
- **AC-09.3** Every routed family reaches axis 3 in both modes; `axis(3)` with no layer on 3 is refused as the fixture says.
- **AC-09.4** `grep -nE '"2" in _dash_axis_tokens|axis", "1"\)\)\.strip\(\) == "2"' dash_render.py` prints nothing (S06's token tests and `6370ca4`'s equality tests are both gone, replaced by `_dash_axis_nos`).
- **AC-09.5** test_dual_axis.py and test_axis2_suboptions.py green; parity green; U09-1..U09-8 PASS; no SKIP.

## Tasks

**Commit boundary.** One commit on `wp31-s09` (`$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s09`), subject `Draw up to nine y and x axes, placed and routed as twoway does (WP-31 C10c)`, made by 09-04; body in BRIEF's forms with `Fixture: test/fixtures/axes_n_truth.json (scripts/extract_axes_n_truth.do)`, `BUGS.md: "<C10c title>" (closed)`, `GAPS3: C10c Tracked` (the C10 row is split a/b/c per index A4; C10c's Tracked line is its own).

<task type="auto" id="09-01">
  <name>Measure twoway and write failing tests</name>
  <files>scripts/extract_axes_n_truth.do, test/fixtures/axes_n_truth.json, test/test_axes_three_to_nine.py</files>
  <action><![CDATA[
    Check the cut (`<scratch>/batch-3-base.txt`, branch `wp31-s09`) and that S06 landed: `grep -c "yaxis=axes,1,2" dash.ado` prints 1 and `grep -c '"_dash_axis_tokens",' dash_render.py` prints 1 (a 0 stops the task: S09 depends on 06, A32); `mkdir -p <scratch>/s09/x`. Create scripts/extract_axes_n_truth.do per "Stata truth" (path-free head copied from scripts/extract_default_base_truth.do:1-60; SVG reading through scripts/svg_truth.py as scripts/extract_bar_geometry_truth.do does), run it through the slot, `git add -f test/fixtures/axes_n_truth.json`. Compare `sides.*` with D-09.b's hypothesis and write `<scratch>/s09/sides.txt`: `hypothesis holds` or the (count, number) → side table to put in `_DASH_AXIS_SIDES`. Create test/test_axes_three_to_nine.py with the classes of "TDD test stubs". Append U09-1..U09-6 to test/test_wp31_truth.cscript above the marker (helpers `_u09_*`), U09-7/U09-8 to test/test_option_validation.cscript before `// Summary`. Run `grep -n "two axes\|yaxis(3)\|xaxis(3)\|yaxis(9)" test/*.cscript test/*.py test/fixtures/rejected_options.json` and flip each pin of the 1-2 bound in place (`Flipped (WP-31 C10c)`), recording in `<scratch>/s09/09-flips.txt`. Run the pytest file (`-rf > <scratch>/s09/09-01.log`) and the two cscripts through the driver (`WP31_ONLY=S09`) on the unmodified tree; write `<scratch>/09-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/axes_n_truth.json'));print(sorted(d['_meta']), sorted(d))"` prints the five `_meta` keys and `_meta bounds refusals routed sides`; `grep -c FAILED <scratch>/s09/09-01.log` is at least 12 and no FAILED line names TestTheFixture or TestNothingElseMoved; `grep -c "U09-[1-6] FAIL" <scratch>/s09/run_truth.log` is at least 5; `grep -c "U09-7 FAIL" <scratch>/s09/run_option_validation.log` prints 1 and `U09-8 PASS` 1; `grep -c SKIP` on both logs prints 0; `test -s <scratch>/s09/sides.txt`.]]></verify>
  <done>twoway's axis bounds, sides for two to four y axes and three x axes, and its axis(3) routing were recorded in a stamped fixture, and every regression test and case was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="09-02">
  <name>Accept axes one to nine in Stata</name>
  <files>dash.ado, dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    Make TR-09.1 (the rule token at :2995, delete :3147-3149, the fixture's bound text if it differs) and TR-09.2 (`_dash_route_axis2`'s `seg` argument and the n 3-9 branch with empty-token skipping in the join loop; `_dash_axisn_clear/_add/_json` after `_dash_axreq_check` with header-index entries; `_needed` names; `_dash_plot`'s clear call; the graph JSON writer's `"axisn"` key; confirm `_g_ys`/`_g_xs` carry every number). program_coverage_map entries under `# WP-31 S09 (C10c): axes three to nine` (`"test_wp31_truth.cscript:U09-3"`). Run test_option_validation.cscript and the truth script (`WP31_ONLY=S09`: U09-4, U09-5 green; U09-1..3, U09-6 still red on the renderer), test_axis2_suboptions.cscript if one exists (`ls test/test_axis2*.cscript`), and `python3 -m pytest test/test_program_coverage_map.py test/test_axis2_suboptions.py::TestTheRouteUnit -q -n0 -p no:cacheprovider`. Then `python3 - <<EOF` is NOT used: instead write a two-line probe do-file registering the three-axis graph with `ylabel(150(20)230, axis(3))` and `_dash_serve_spec, specpath(<scratch>/s09/spec.json) datapath(<scratch>/s09/data.json)`, run it through the slot, and check the spec holds `"axisn":{"y3":{"label":"150(20)230"}}`.
  ]]></action>
  <verify><![CDATA[`grep -c "yaxis=axes,1,9  xaxis=axes,1,9" dash.ado` prints 1; `grep -c "two axes" dash.ado` prints 0; `grep -c "U09-[45] PASS" <scratch>/s09/run_truth.log` prints 2; test_option_validation.cscript's log ends `ALL CHECKS PASSED` with `U09-7 PASS`; `python3 -c "import json;print(json.load(open('<scratch>/s09/spec.json'))['graphs'][0]['graph_options']['axisn'])"` prints `{'y3': {'label': '150(20)230'}}`; the pytest run reports 0 failed.]]></verify>
  <done>dash.ado accepted yaxis() and xaxis() one to nine with twoway's words for the bounds, and axis(3)-(9) options travelled to the spec in the axisn object.</done>
</task>

<task type="auto" id="09-03">
  <name>Draw and route axes three to nine</name>
  <files>dash_render.py, test/function_test_map.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Make TR-09.3 (the three accessors `_dash_axis_nos`, `_dash_axis_no`, `_dash_axisn_value` after `_dash_axis_number`, every reader in the Evidence table rewritten over S06's token reads, the three copy-list entries after `"_dash_reference_lines",` and the constant appended last in the constants tuple at :46584-46784), TR-09.4 (`_dash_add_secondary_axes`: the per-letter `used` loop, `fig._dash_extra_axes`, the kept `(has_y2, has_x2)` return), TR-09.5 (`_dash_finish_secondary_axes` over every `^[xy][2-9]$` range), TR-09.6 (`axis_side(which, number, count)` and `_DASH_AXIS_SIDES` from `<scratch>/s09/sides.txt`), TR-09.7 (reference lines on range y<n>). Do not edit `_dash_refinish_axes`, `_dash_axis_plan`, `_DASH_AXIS_FINISH_JS`, `_make_figure_body` or the template strings (the two template call sites keep their signatures). function_test_map.py entries under `# WP-31 S09 (C10c)`. Append the parity cases. Run `python3 -m pytest test/test_axes_three_to_nine.py test/test_dual_axis.py test/test_axis2_suboptions.py test/test_function_test_map.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "not Move"` and the truth script (`WP31_ONLY=S09`).
  ]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; `grep -cE '"2" in _dash_axis_tokens|axis", "1"\)\)\.strip\(\) == "2"' dash_render.py` prints 0; `grep -c '"_dash_axis_nos",' dash_render.py` prints 1 and `grep -c '"_dash_axisn_value",' dash_render.py` prints 1; `grep -c "U09-[1-6] PASS" <scratch>/s09/run_truth.log` prints 6 and `grep -c " FAIL\|SKIP"` prints 0.]]></verify>
  <done>Both renderers drew a layer on any of axes two to nine against its own range and axis, on twoway's measured side, with axis(n) options routed to it.</done>
</task>

<task type="auto" id="09-04">
  <name>Certify, document and commit C10c</name>
  <files>dash.sthlp, BUGS.md, CHANGELOG.md</files>
  <action><![CDATA[
    Run every test file touched in 09-01..09-03 plus `python3 -m pytest test/test_help_conformance.py test/test_unsupported_report_is_true.py test/test_tracking_documents.py test/test_reference_lines*.py test/test_served_*axis*.py -q -p no:cacheprovider` (globs resolved by ls; skip absent names), then the three cscripts through the driver. A failure outside the flip list: flip in place if its file is one 09-01 edited, else stop and report the node. dash.sthlp (R3; S09's paragraph): the Secondary axes section (`grep -n "Secondary axes" dash.sthlp`) says yaxis()/xaxis() take 1 to 9, where axes three and up are placed (the fixture's words: on the left, or as measured), and that axis(#) routes every label, tick, title, line and scale option; delete any "two axes" sentence (`grep -n "two axes\|second axis only" dash.sthlp`). Close C10c: BUGS.md entry Resolution in BRIEF's closed form naming test/test_axes_three_to_nine.py::TestThreeAxes::test_ranges_axes_and_sides, test/test_wp31_truth.cscript U09-1 and the fixture; GAPS3 `- **C10c Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (DECISIONS A11: the merger's step k.3b writes the landed sha; no `git commit --amend`); CHANGELOG `<!-- WP-31 C10c -->` under `### Results that change` replaced by `- yaxis(3) to yaxis(9) and xaxis(3) to xaxis(9) are drawn, placed as twoway places them (<the fixture's sides.y3 words: on the left in number order, or as measured>); yaxis(0) and yaxis(10) are refused with twoway's line <bounds.yaxis10.text> (dash said "dash draws two axes"). (WP-31, C10c)` (REVIEW-1 R1-26: the measured words, never "as twoway places them" alone). Stage dash.ado dash_parse.mata dash_render.py dash.sthlp BUGS.md CHANGELOG.md GAPS3.md scripts/extract_axes_n_truth.do test/test_axes_three_to_nine.py test/test_wp31_truth.cscript test/test_option_validation.cscript test/function_test_map.py test/program_coverage_map.py test/test_mode_parity.py and the flipped files; `git add -f test/fixtures/axes_n_truth.json`; check `git diff --cached --name-only` names no CLAUDE.md/.ultraplan/*.html; write `<scratch>/s09/msg.txt` in the boundary's form, grep it for `claude|anthropic` (0), commit with it, re-grep. No amend: the Tracked line stays `commit pending` until the merger's step k.3b.
  ]]></action>
  <verify><![CDATA[Every pytest run reports 0 failed; the three cscript logs end with their all-passed lines and hold no FAIL or SKIP; `git log -1 --format=%s` ends `(WP-31 C10c)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 C10c -->' CHANGELOG.md` prints 0; `grep -c "C10c Tracked:\*\* Closed in WP-31, BUGS.md \".*\", commit pending\.$" GAPS3.md` prints 1; `grep -c "two axes" dash.sthlp dash.ado` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Axes one to nine were certified in both modes against twoway's measured sides and routing, documented, and C10c was closed in one green commit on wp31-s09.</done>
</task>

## Section completion criteria

- `yaxis()`/`xaxis()` 1-9 accepted; bounds in twoway's words; no "two axes" text anywhere.
- Layers on axes 2-9 drawn on their own ranges and axes on the fixture's sides in both modes; `axis(n)` options routed through `axisn`.
- One- and two-axis behaviour unchanged (test_dual_axis.py, test_axis2_suboptions.py green).
- `axes_n_truth.json` stamped and named; U09-1..U09-8 PASS; flips recorded; one green commit; C10c closed, its Tracked line `commit pending`; S06's `yaxis(1 2)` still draws two copies.

## Notes

- **Renderer order (WP-28 Notes):** the saved renderer adds the extra axes AFTER `_dash_style_axis_titles`, the served template BEFORE it; style each axis where it is built, as `_dash_add_secondary_axes` does for axis 2 (docstring :31737-31745).
- **Bokeh stacking:** `fig.add_layout(ax, "left")` appends to `fig.left`; the first element is innermost. For "stacked on the left" append in number order 1, 2, 3 ... (axis 1 is already there).
- **`_dash_count_axes` and the plan:** by naming every extra range `y<n>`, the count-ticks finisher and `_dash_axis_plan` see the new axes as they see `y2` today; whether that makes them follow a move is S35's question (GAPS3 D9 says y2 does not follow today), not S09's.
- **Decisions for ratification:** D-09.a (one `axisn` JSON key instead of 70 declared options); D-09.b's fallback constant if the fixture contradicts the help.
- **Shared files.** R1: the S09 block; U09-7/8 in test_option_validation.cscript. R2: three functions after `_dash_reference_lines`, one constant appended last in the constants tuple (R1-13). R3: the Secondary axes paragraph. R4: one marker. R5: one entry (C10c). R6: `_needed` gains three names; `version 19` in no new program (Mata only). R7: one fixture. R8: four corpus entries. R9: flips. R11: S09 does not edit the axis finishers. R12: S09 edits `_dash_option_rules` (one token) -- batch 3 has no other rules editor; it does not edit `_make_figure_body` or `_generate_app_source`.
- **For S35:** read `fig._dash_extra_axes`, `_dash_axisn_value`, `axis_side(which, n, count)`; the fixture's `sides.y23_no1` is recorded for S35's first-used rule.
- **For S24 (minor ticks):** `ymlabel(, axis(n))`/`ymtick(, axis(n))` are still named for the note (family rows with no axis key); S24 may extend `_dash_axisn_add` to the `mlabel`/`mtick` families.
