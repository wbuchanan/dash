# Section 52: The add sub-option (P1.18 part b)

> Part of: WP-30 · Items: P1.18 part b (entry `P1.18b`; REM-09-02-LABEL-ADD, GAPS2-B21-f, the WP-29 S05/S10 axis(2) `add` note) · Risk: yellow · Batch: 18 (merge order S51, S52, S53) · Depends on: 21, 31, 44 · Blocks: 57 · Tasks: 12, 1 commit · Case prefix: AD

## Review amendments

- Fixed (major, batch boundary): AD-22 ran `dash tsline y, tlabel(2001m1, add)`, which needs S51's fold, absent from S52's worktree (cut from the batch-18 base); 52-11's "no AD FAIL" could not be met. AD-22 now draws `xlabel(492, add)` against twoway's `tlabel(2001m1, add)`, and S51's TA-02 pins the fold to `"xlabel":"492, add"` (S51 amended), so the pair is the cross case.
- Fixed (minor): Dependencies name the adjacent `_dash_rep_subs` (S51) and `_dash_rep_merge` (S52) hunks for the merger (R6).
- Checked at HEAD: `_dash_rep_merge` 5715 with the `drop = ("add")` rule at :5736-5738 and the empty-first-copy return at :5723, `_dash_axis_pieces` 4430, `_dash_rep_merge_locals` 5749, `_dash_rep_reduce`'s merge call 5831, `_dash_axis_expand` 2537 and its caller 2331, the `#N` union at dash_render.py:23435-23438, the pinned `test_add_is_named_on_ylabel2` at test_axis2_suboptions.py:369-374, dash.sthlp:2962-2963, r23 at test_twoway_option_parity.cscript:1461.
- Checked: TR-52.10's merge rule reproduces E6's five merge rows and a01; M5 (`zlabel()`'s `add` named, a valid option dash does not draw), M6 (`ytick(…, add)` silent); the JS union writes numbers from the plan only (rule 1); A9's budget is timed.
- Checked (batch 18): S52 is the batch's only finisher editor (R11) and edits none of `_generate_app_source`, `_build_sources_and_figures`, `_make_figure_body`; S53 reads `_dash_finish_secondary_axes` and the axis appliers without editing them; S51 edits none of S52's functions.
- Cross-file (notes file): index 18.0's expected list omits S52's `_dash_parse_axis_spec` (CRITICAL), `_dash_apply_axis_spec` and `_dash_apply_z_options` (HIGH).
- Rejected: `<files>none</files>` in 52-11 (BRIEF allows the word none).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:129 (P1.18) ends "`labcolor`, `tlength`, `tposition` and `add` are not honoured; `add` replaces the default ticks. WP-29 note: `add` on an axis(2)-routed label is named, not drawn." Measured at `c96facd` (research `.ultraplan/wp30/research/p1-18.md` §2 j, k, D-1, D-2; both modes alike):

```
ylabel(25, add)                    -> FixedTicker [25.0]; "ylabel() sub-option(s) not implemented and ignored: add"   (twoway: 10 20 30 40 25)
ylabel(25, axis(2) add)            -> spec ylabel2 "25, add"; y2 ticks [25.0]; "ylabel2() ... add"                     (twoway: 0 5000 10000 15000 + the value)
ylabel(25, add) ylabel(35, add)    -> spec "ylabel":"25 35" (add dropped by the Mata merge)                              (twoway: 10 20 30 40 25 35)
ylabel(15(10)35, add)              -> spec "15 25 35, add", identical to ylabel(15 25 35, add)                           (twoway: 15 25 35 against 10 20 30 40 15 25 35)
ylabel(0(10)100, norescale)        -> spec "0 10 ... 100, norescale"; the renderer keeps norescale                        (twoway draws a lone rule as if norescale were absent)
```

**After this section**, in the saved page and the served app, before and after every filter move:
- `add` after a list of values (`ylabel(25, add)`, `ylabel(25 "x", add)`, `ylabel(15 "a" 25(10)45, add)`) draws the axis's default ticks, S21's natscale ticker on numeric axes and S44's date ticker on `%td`-`%ty` axes, plus the listed values, and every re-tick after a move keeps the union;
- after a leading rule (`a(b)c`, `#N`, `minmax`, `none`) `add` is spent, as twoway spends it;
- `ylabel(…, axis(2) add)` (spec `ylabel2`) is drawn on the second axis the same way, and is no longer named;
- repeated copies merge as twoway merges them (`ylabel(25, add) ylabel(35, add)` keeps `add`; a later copy with no values keeps the earlier copy's `add`);
- dash.ado keeps the rule-versus-list distinction for the renderer, which also makes `ylabel(0(10)100, norescale)` through Stata draw as twoway draws it;
- `nolabels`, `noticks` (S31) and by() (M6, S31's silence) apply to the added positions as to the default ones; `xtick()`/`ytick()` accept `add` in silence (twoway draws the same picture with or without it).

**Why one section.** The renderer union, the Mata merge (D-1) and the ado rule preservation (D-2) are the three halves of one sub-option and one BUGS.md entry, `P1.18b`. It lands after S21 (default ticker, finishers), S31 (tail-only parsing, `show_labels`/`show_ticks`) and S44 (date ticker), and is batch 18's only axis-finisher editor (R11).

**Test order and commit rule (rule 7).** One cycle on `wp30-s52`: 52-01 writes the fixture and every regression test and runs them against the unmodified batch-18 base, saving `$S/52-P1.18b-failure.txt` (no commit); 52-02 to 52-11 fix, flip, document and certify; 52-12 closes the entry and makes the one commit. No test-only commit exists, and no commit is red.

## Risk: [yellow] — one CRITICAL parser, the shared finisher JS, and two Stata paths every axis option runs

**Why.**
- `_dash_parse_axis_spec` is CRITICAL (`gitnexus impact _dash_parse_axis_spec -d upstream -r dash`: 8 impacted; callers `_dash_apply_axis_options`, `_dash_apply_tick_option`, `_dash_apply_z_options`, `_dash_finish_secondary_axes`; research p1-18 §6).
- `_dash_apply_axis_spec` (HIGH), `_dash_apply_z_options` (HIGH); `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_place_count_ticks` LOW by graph but called from the served template text (research §6, critic): treat as HIGH.
- S21's `_dash_axis_plan`, `_DASH_AXIS_FINISH_JS` and `_dash_refinish_axes` are new since `c96facd`; the merger's 18.0 impact run records them.
- `_dash_rep_merge` (dash_parse.mata:5715), `_dash_axis_pieces` (dash_parse.mata:4430) and `_dash_axis_expand` (dash.ado:2537) are UNKNOWN (Stata/Mata, not indexed): every repeated graph option goes through the first (`_dash_rep_merge_locals` :5752, `_dash_rep_reduce` :5831, the two gk loops dash.ado:5272-5287 and :5304-5312), and every axis-label option through the other two (`_dash_validate_value`'s axislist branch, dash.ado:2326-2332, calls `_dash_axis_expand`, which calls `_dash_axis_pieces`).

**Risk factors.**
1. The saved re-finish (`_DASH_AXIS_FINISH_JS`) and the served re-finish (`_dash_refinish_axes`) must union the same extras, or the two modes part after the first move.
2. The date ticker (S44) writes ticks in its own code path; an `add` that unions on numeric axes only would be lost on date axes after a move.
3. Changing `_dash_rep_merge`'s `drop` rule touches every L-category option (xlabel ... zlabel), including test_twoway_option_parity.cscript r23 (`xlabel(2000 3000) xlabel(4000, add)` → `xlabel(2000 3000 4000)`).
4. `_dash_axis_expand` runs before every axis-label value is written; a wrong rule test would drop `add` or `norescale` from lists that need them.

**Mitigation.**
1. One plan field (`extra`) feeds both modes; TestTheRefinishKeepsIt runs the node saved re-finish and the served `_dash_refinish_axes` on the same spec and compares with the build.
2. TestOnADateAxis asserts, in both modes and after a move, ticks-with-add equal ticks-without-add plus the value on a `%tm` axis.
3. The merge rule is twoway's measured table (Evidence E6), each row a cscript case (AD-01..AD-06), r23 kept as a guard.
4. The rule test is added in place to the Mata splitter `_dash_axis_pieces` (its only callers are `_dash_axis_expand` and test_gaps2_truth.cscript AL-02), with no regex, unit-tested in the cscript (AD-07..AD-09) on every head form of E6; no new Mata function, so `_needed` and the header index, which S51 extends in this batch, are not touched by S52.

## Dependencies

- **Depends on: 21, 31, 44.**
  - S21 (batch 7): `_dash_default_ticker(n)` (a `FixedTicker` tagged `_DASH_COUNT_TAG + n` and `_DASH_DEFAULT_TAG`), its install in `_dash_apply_axis_options` and `_dash_finish_secondary_axes` (TR-21.6), `fig._dash_numticks`, the finisher chain (`_dash_count_axes`, `_dash_place_count_ticks`, `_dash_finish_count_ticks(refinish=…)`, `_dash_common_count_ticks`), `_dash_axis_plan` (plan field `extra`), `_DASH_AXIS_FINISH_JS`, `_dash_refinish_axes` and the A9 budgets.
  - S31 (batch 11): tail-only sub-option reading on S10's resolved names, `_DASH_AXLABEL_HONOURED`, `show_labels`/`show_ticks`, `_dash_tick_look`, the by() silence (TR-31.10). S31's Notes: "`add` must respect `show_labels`/`show_ticks` from this spec".
  - S44 (batch 15): the `%td`-`%ty` default ticker, its Python helpers at S21's anchor and its JS port inside `_DASH_AXIS_FINISH_JS` (manifest S44 notes: "S52's add then unions with this ticker too").
  - S01: entry `P1.18b`, its `WP30_OPEN` key, the marker `<!-- WP-30 P1.18b -->` in the `**WP-30 (drop-in P1, 03oct2026)**` group of `### Results that change`, the S52 stub of `test/test_wp30_truth.cscript`, and the anchors `# WP-30 S52 (P1.18b): The add sub-option (P1.18 part b)`.
  - Read, not depended on by the manifest: S10 (sub-option table, `add`'s spellings), S35 (`_dash_date_axis_spec` converts listed values on date axes; Notes: any reader of glyph coordinates calls `_dash_spec_units`), S47 (its names at S21's copy-list anchor, after which S52's goes).
- **Blocks: 57** (the served worker audits the final move path).
- **Parallel batch: 18**, merge order S51, S52, S53.
- **Can run with:** S51 (Stata/Mata only: `_dash_parse_graph_opts`, `_dash_parse_plot_opts`, `_dash_process_segment`, `_dash_plot`, `_dash_prepare_spec`, Mata `_dash_rep_cat`, `_dash_rep_subs`, `_dash_ax_parse`, `_dash_route_axis2`, `_dash_axreq_*`, new `_dash_taxis_*`/`_dash_tdate_*` functions; never `_dash_rep_merge`, `_dash_axis_pieces` or `_dash_axis_expand`) and S53 (by() axes and keys: `_build_sources_and_figures`, the template's by() block, `_dash_layout_cell`, `_dash_reflow`, `_dash_parse_by`, new `_dash_by_*` helpers, the extractor and scheme files). S52 edits none of their functions, and they edit none of S52's. S51's folded `tlabel(…, add)` reaches S52's code as `xlabel "<n>, add"`. S52's worktree is cut from the batch-18 base, which lacks S51's fold, so the cross case is a pair: S51's TA-02 pins `tsline y, tlabel(2001m1, add)` folded to `"xlabel":"492, add"`, and S52's AD-22 and `TestOnADateAxis` draw `xlabel(492, add)` against twoway's `tlabel(2001m1, add)` ticks; G8 runs both scripts on the merged tree. S51 edits `_dash_rep_subs` directly above `_dash_rep_merge` (dash_parse.mata:5662-5711 and :5713-5745): the hunks may touch in context, and the merger keeps both (R6).

## Evidence

Anchors are at `c96facd` (dash.ado 8,487 lines, dash_parse.mata 6,093, dash_render.py 37,689, dash.sthlp 3,822). S08-S50 move many of them; the executor re-finds each by symbol at `batch-18-base` and treats numbers as approximate.

### E1. The parser names `add` (dash_render.py:22636-22652, before S10/S31)

```python
22636        for _tok in _dash_by_tokens(tail.lstrip(",").strip()):
22637            _nm = _dash_subopt_name(_tok)
...
22651            if _nm not in ("format", "labsize", "angle", "grid", "nogrid"):
22652                out["unsupported"].append(_tok)
```

S10 replaced the literal tuple by `_DASH_AXLABEL_HONOURED` and S31 extended it (TR-31.1); `add` is in neither, so it is reported through `_dash_report_suboptions` and the explicit list replaces the ticker (:22795-22796, `axis_obj.ticker = FixedTicker(ticks=spec["ticks"])`).

### E2. The union already exists for `#N` lists (dash_render.py:22783-22794, :23435-23440)

```python
22783    elif mode == "count":
...
22788        axis_obj.ticker = _dash_count_ticker(spec["count"])
22789        if spec["ticks"]:
...
22794            axis_obj._dash_extra_ticks = list(spec["ticks"])
...
23435    _extra = getattr(ax, "_dash_extra_ticks", None)
23436    if _extra:
23437        if t_base:
23438            t_base = sorted(set(t_base) | set(_extra))
```

S21 keeps this union in `_dash_place_count_ticks` (TR-21.8 writes ticks only) and carries the list into the saved plan as `extra` ("the `#N` list's union ticks", TR-21.10). `add` is the same union over the default ticker.

### E3. The Mata merge drops `add` (dash_parse.mata:5715-5743)

```mata
5731    add  = (cat == "L" & anyof(w2, "add"))
5732    drop = ("suffix", "prefix")
5733    if (cat == "L") drop = ("add")
...
5736    else if (add & has2)  body = strtrim(b1) + " " + strtrim(b2)
5737    else                  body = (has2 ? strtrim(b2) : strtrim(b1))
5738    sub = _dash_rep_subs(s1, s2, cat, drop)
```

`add` is always spent, whatever the first copy carried (critic: `drop = ("add")`, :5737 in the research's count).

### E4. dash.ado expands every run before the renderer sees it (dash.ado:2537-2560)

`_dash_axis_expand` splits the value with Mata `_dash_axis_pieces` (dash_parse.mata:4430; tags S strings, B bare runs, H runs holding a backtick, `$` or `'`, T the tail) and replaces each B run by `numlist`'s expansion. `15(10)35, add` and `15 25 35, add` leave it as the same text; the renderer's lone-rule rule for `norescale` (dash_render.py:22675-22678, `_DASH_AXIS_INCR_RE.match(...)`) never sees a rule from Stata. Its caller is `_dash_validate_value`'s axislist branch (dash.ado:2326-2332).

### E5. The second axis (dash_render.py:23172-23230; test pin)

`_dash_finish_secondary_axes` parses `ylabel2`/`xlabel2` with `_dash_parse_axis_spec` and applies them with `_dash_apply_axis_spec`; its report names `add`. S21 installs the default ticker on y2/x2 when the spec is empty or mode "default" (TR-21.6). Pinned: `test/test_axis2_suboptions.py::TestTheSecondAxisOptionsReachTheSecondAxis::test_add_is_named_on_ylabel2` (:369-374). dash.sthlp:2962-2963: "{cmd:add} on a label routed to the second axis ({cmd:ylabel(5000, axis(2) add)}) is named, not applied."

### E6. twoway's truth (StataNow 19.5; `sysuse auto`, `scatter mpg weight`; `.Graph.yaxis1.major.dlg_tickpos`)

From research p1-18 §3 and critic (k01-k04, y04), quoted:

| Probe | twoway ticks |
|---|---|
| `ylabel(25, add)` / `(5, add)` / `(50, add)` | `10 20 30 40 25` / `… 5` / `… 50` (axis widened to 50) |
| `ylabel(15 25 to 35, add)`, `ylabel(15/17, add)` | default plus the list |
| `ylabel(15 "a" 25(10)45, add)` | `10 20 30 40 15 25 35 45` |
| `ylabel(25 "x", add)` | default, 25 labelled "x" |
| `ylabel(15(10)35, add)` / `ylabel(15(10)35 50, add)` | `15 25 35` / `15 25 35 50` (a leading rule ignores the default) |
| `ylabel(#2, add)` / `ylabel(#2 25, add)` / `ylabel(minmax, add)` / `ylabel(none, add)` / `ylabel(, add)` | `0 20 40` / `0 20 40 25` / `12 41` / none / default |
| `ylabel(25) ylabel(35, add)` | `25 35` |
| `ylabel(25, add) ylabel(35, add)` | `10 20 30 40 25 35` |
| `ylabel(25, add) ylabel(35)` | `35` |
| `ylabel(25, nolabels) ylabel(35, add)` | `25 35`, labels hidden |
| `by(foreign)`, `ylabel(25, add)` (y04) | default plus 25 on each panel |
| `tsline y, tlabel(2001m1, add)` (p1-06 c16) | the default date ticks plus 2001m1 |

Measured for this file (`$S/s51-53/probe.do` through `scripts/stata_slot.sh`, records `$S/s51-53/records.txt`, 04oct2026; open claims the research left):

```
a01 ylabel(25, add) ylabel(, nolabels)      yaxis1 major 10 20 30 40 25, lab=0
a02 ylabel(25, add) ylabel(, labsize(small)) yaxis1 major 10 20 30 40 25
a03 ytick(25)                               yaxis1 major 10 20 30 40; majornl 25
a04 ytick(25, add)                          yaxis1 major 10 20 30 40; majornl 25     (identical to a03)
a05 ylabel(#3 25, add)                      yaxis1 major 10 20 30 40 25
a06 ylabel(25, add norescale)               yaxis1 major 10 20 30 40 25
a07 ylabel(50, add norescale)               yaxis1 major 10 20 30 40 50
a08 xlabel(5000, add) xlabel(1500, add)     xaxis1 major 2000 3000 4000 5000 1500
b00 (scatter mpg weight) (scatter price weight, yaxis(2))                   yaxis2 major 0 5000 10000 15000
b01 … , ylabel(6000, axis(2) add)                                          yaxis2 major 0 5000 10000 15000 6000
```

a01 is a merge rule the research left open: a later copy with no values keeps the earlier copy's `add`. a03/a04: `add` changes nothing on a tick-only option. b01 settles the WP-29 note: twoway draws an axis(2) `add`.

### E7. Tests that pin today's behaviour (flipped in place, never deleted; re-measured by 52-01)

- `test/test_axis2_suboptions.py::TestTheSecondAxisOptionsReachTheSecondAxis::test_add_is_named_on_ylabel2` (both modes): becomes `test_add_is_drawn_on_ylabel2`, asserting no note and y2 ticks equal the default ticks plus the values.
- Guards that stay green: `test/test_twoway_option_parity.cscript` r23/e23 (:1461); S31's `test_axis_suboptions.py` classes; S21's `test_default_axes.py`; S44's date-ticker tests.
- `grep -rn "add" test/test_suboption_warnings.py test/test_mode_parity.py test/test_help_claims_7.py` at the base: any row that expects `add` named moves to a still-named token (`labgap`), with a `Flipped:` line.

### E8. Blast radius (from research §6; re-run at 18.0)

| Symbol | Risk | Action |
|---|---|---|
| `_dash_parse_axis_spec` | CRITICAL | warn; one honoured name and two lines |
| `_dash_apply_axis_spec` | HIGH | warn; the explicit branch's add path |
| `_dash_apply_z_options` | HIGH | warn; `add` named as typed |
| `_dash_apply_axis_options`, `_dash_finish_secondary_axes` | LOW (graph; template text) | the default-ticker condition |
| `_dash_place_count_ticks`, `_dash_axis_plan`, `_DASH_AXIS_FINISH_JS` | LOW / new | read, edited only if a test shows the union missing |
| `_dash_rep_merge`, `_dash_axis_pieces`, `_dash_axis_expand` | UNKNOWN | grep callers (Risk); the expander's comment only |

## User stories

- **US-52.1** As a twoway user, I want `ylabel(25, add)` to keep my axis's default ticks and add 25, so a do-file that marks one extra value draws as in Stata, in both modes and after any filter move.
- **US-52.2** As a twoway user with time series, I want `tlabel(2001m1, add)` and `xlabel(492, add)` on a monthly axis to add one date to the default date ticks.
- **US-52.3** As a twoway user with two y axes, I want `ylabel(6000, axis(2) add)` drawn on the second axis instead of a note.
- **US-52.4** As a twoway user, I want repeated `ylabel()` copies and `a(b)c` rules read with `add` exactly as twoway reads them.

## Business requirements

- **BR-52.1** `add` after a head that begins with a value draws the axis's default ticks plus every listed value (labels as given), on x and y axes, first and second axes, numeric and date axes, in every by() panel.
- **BR-52.2** `add` after a head that begins with a rule (`a(b)c`, `#N`, `##N`, `minmax`, `none`) has no effect; `ylabel(, add)` draws the default.
- **BR-52.3** The added values survive every re-tick: the saved page and the served app show the same ticks before and after any filter move, and the axis range reaches an added value as twoway's does (`norescale` as twoway applies it).
- **BR-52.4** Repeated copies: a copy with values and `add` appends to the copy before it and keeps that copy's `add`; a copy with values and no `add` replaces; a copy with no values keeps the values and `add` before it (E6 rows).
- **BR-52.5** `ylabel(0(10)100, norescale)` typed in Stata draws as twoway draws it (a lone rule widens the axis); `ylabel(0 10 20, norescale)` keeps `norescale`.
- **BR-52.6** `nolabels` hides the added values' labels and `noticks` their ticks; under by() the forms twoway ignores stay silent (S31).
- **BR-52.7** `add` is never named on `xlabel`/`ylabel`/`xlabel2`/`ylabel2`/`xtick`/`ytick` and their axis(2) routes; on `zlabel()` (the colour key) it is named, as a valid option dash does not draw.

## Technical requirements

- **TR-52.1 `_dash_parse_axis_spec`** (in place, CRITICAL; warn). `_DASH_AXLABEL_HONOURED` (S10's constant, S31's form) gains `"add"`; `out` gains `"add": False`. When S10's resolved tail names hold `add` (S10's table decides its spellings), `out["add"] = True`, read from the tail only (D-3; quoted label text never sets it). After the head is read: `add` stays True only when the head's first token is a value, that is when the head is non-blank, does not match `_DASH_AXIS_RULE_RE` (`#N`/`##N`), is not `minmax`/`none`, and its first blank-delimited token does not match `_DASH_AXIS_INCR_RE` after blanks are removed (an `a(b)c` rule; `15/17` and `15 25 to 35` are values, E6). Otherwise `out["add"] = False` (spent, silent). The docstring's Returns gains `add` and cites E6. A hand-written `"15(10)35, add"` therefore draws 15 25 35, as through Stata after TR-52.8.
- **TR-52.2 New `_dash_axis_add(axis_obj, spec, numticks=None)`** (module level, directly after `_dash_apply_axis_spec`; no nested defs). Returns True when it applied `add`:
  - `spec.get("add")` and `spec["ticks"]` non-empty, else False.
  - The ticker: kept when it is a `FixedTicker` whose `tags` hold `_DASH_DEFAULT_TAG` (S21's and S44's default tickers, installed by TR-52.3/52.4); otherwise `axis_obj.ticker = _dash_count_ticker(int(numticks or 5))` (a categorical axis, `isinstance(axis_obj.ticker, ContinuousTicker)` false, returns False untouched).
  - `axis_obj._dash_extra_ticks = sorted(set(float(t) for t in spec["ticks"]))`, the same attribute E2's `#N` path sets, so `_dash_place_count_ticks`, `_dash_axis_plan` and the re-finishers union it.
  - `spec["labels"]` → `axis_obj.major_label_overrides` (merged with any already set); no `CustomJSTickFormatter` (the default ticks keep their formatter).
  - `spec.get("norescale")` → `axis_obj._dash_tick_norescale = True` is NOT set; instead `axis_obj._dash_extra_norescale = True`, read by TR-52.5.
- **TR-52.3 `_dash_apply_axis_options`** (in place): S21's install condition for the default ticker ("`raw` is empty or its spec's mode is default", TR-21.6) becomes "… or `spec.get("add")`"; the same holds on date kinds where S44 installs its default ticker. `_dash_apply_axis_spec`'s explicit branch is entered only when `not spec.get("add")`; with `add`, `_dash_axis_add(axis_obj, spec, fig._dash_numticks[letter])` runs in its place (one `if` before the branch chain, inside `_dash_apply_axis_spec`, through a new keyword `numticks=None` that `_dash_apply_axis_options` passes). Label look (S31), format and angle lines run as for any spec.
- **TR-52.4 `_dash_finish_secondary_axes`** (in place): the y2/x2 default-ticker condition gains `or spec.get("add")`, and the `{n}label2` call passes `numticks=fig._dash_numticks[letter]`. Its report no longer names `add` (honoured, TR-52.1).
- **TR-52.5 The finishers (R11; S52 is batch 18's only editor).** Each change below is made only if 52-01's tests show the union missing at the base; each is then pinned:
  - `_dash_place_count_ticks`: the `_extra` union (:23435-23440) runs for `default` entries as for `#N` entries, on build and on `refinish`, and for S44's date entries (whatever function writes their ticks); held ticks already hold the extras.
  - Hull: an extra joins the hull (twoway widened the axis to 50, E6) unless `_dash_extra_norescale`, which follows the fixture's `ylabel(50, add norescale)` range.
  - `_dash_axis_plan`: `extra` is written for every planned axis whose ticker carries `_dash_extra_ticks` (count, default and date entries).
  - `_DASH_AXIS_FINISH_JS`: `dash_axis_compute` unions `plan.extra` into the computed ticks for count, default and date entries alike (sorted, de-duplicated with the same `%.15g` key the Python side uses), before ranges are padded; `_dash_refinish_axes` needs no change when `_dash_place_count_ticks` does it.
  - A9's budgets hold (ratification item 3): TestTheRefinishKeepsIt times the served re-finish with and without `add`.
- **TR-52.6 `_dash_apply_z_options`** (in place, HIGH; warn): `add` joins the typed names it reports for the colour key (S31's list), so `zlabel(1000, add)` is named once, and the parsed spec's `add` is set False before any applier sees it, so the key's ticks are the listed values as today.
- **TR-52.7 Tick-only options.** `_dash_apply_tick_option` is not edited: `add` is honoured by the parser, and a tick-only position is already drawn beside the default ticks (E6 a03/a04), so `ytick(25, add)` draws as `ytick(25)`, silent.
- **TR-52.8 dash.ado `_dash_axis_expand`** (in place; `version 19` since S03): no code change is needed, because the T piece `_dash_axis_pieces` returns is already the cleaned tail (TR-52.9); its header comment gains the two rules (E6, E4) and names `_ap_rule`. The tail is rebuilt in Mata from its words, never by macro substitution of user text.
- **TR-52.9 Mata `_dash_axis_pieces`** (dash_parse.mata:4430, in place; no regex, linear): after the head/tail split it already makes, it rates the head and sets the caller's new local `_ap_rule`: the head's first token (a quoted string counts as a value) is `#`-led, `minmax` or `none` (lower case), or holds `(` with numbers (`strtoreal`) before `(` and after `)` → a rule; the head being exactly one such `a(b)c` token → 2 (lone rule); a rule followed by more → 1; a value first, or an empty head → 0. When `_ap_rule` is 1 or 2 the T piece's text has every `add` word removed, and when 2 every `norescale` word too (tail words split with `_dash_rep_toks(tail, 1)`, re-joined after the comma by one blank; an emptied tail is `""`). Its comment block and header-index text are updated in place; no new function, so `_needed` is unchanged.
- **TR-52.10 Mata `_dash_rep_merge`** (in place; UNKNOWN). For cat `"L"`: `a1 = anyof(strlower(_dash_rep_toks(s1, 1)), "add")`, `a2` likewise for `s2`; body as today (`add & has2` appends, else the second's body or, with none, the first's); `keep = has2 ? (a2 & a1) : a1`; `sub = _dash_rep_subs(s1, s2, cat, ("add"))`, then `if (keep) sub = sub + (sub != "" ? " " : "") + "add"`. Every other category unchanged. The comment block above it cites E6's five merge rows and a01.
- **TR-52.11 Served copy list** (R2 row S52): `"_dash_axis_add",` directly after S47's names at S21's functions anchor (after `"_dash_refinish_axes",` and the names S27, S44, S47 placed after it). `_dash_parse_axis_spec`, `_dash_apply_axis_spec`, `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_apply_z_options`, `_dash_place_count_ticks`, `_dash_axis_plan`, `_DASH_AXIS_FINISH_JS` and `_DASH_AXLABEL_HONOURED` change in place. `_generate_app_source` is not edited.
- **TR-52.12 JS twin.** `_DASH_AXIS_FINISH_JS`'s union (TR-52.5) is the twin of `_dash_place_count_ticks`' union; TestTheRefinishKeepsIt runs both on one spec (node, `js_runner.requires_node`).
- **TR-52.13 Registries.** `test/function_test_map.py` under S52's anchor: `'_dash_axis_add': 'test/test_axis_add.py::TestTheUnitFunctions::test_axis_add'`. `test/program_coverage_map.py`: the existing `"_dash_axis_pieces"` entry gains `"test_suboption_reporting.cscript:AD-09"` in place (no new key).
- **TR-52.14 Help** (R3: Axis and Display Options, S52's paragraphs; S51's new paragraph is left as merged): the label sub-options paragraph (about :2834-2838 as S31 left it) gains one sentence: `add` adds the listed values to the axis's default ticks (dates included), after a rule it has no effect, and repeated copies merge as twoway's; the second-axis sentence (:2962-2963) becomes "{cmd:add} on a label routed to the second axis ({cmd:ylabel(5000, axis(2) add)}) adds to that axis's default ticks."; the repeats example at :554 stays true. Lines at most 79 characters.
- **TR-52.15 Security (rule 1).** Added values reach Bokeh only as floats from the existing numlist reader (`_dash_parse_axis_label_opt`, bounded by `_MAX_AXIS_TICKS`); labels only through `major_label_overrides` (canvas text, already a registered sink); no new JS string carries user text (the plan is JSON numbers). Mata reads values with `st_local` and never builds a command line from them; the rule test in `_dash_axis_pieces` is linear and regex-free.

## Boundaries

- **Batch partners:** S51's Stata/Mata functions and its help paragraph; S53's by() functions, `_dash_reflow`, `_dash_layout_cell`, `_build_sources_and_figures`, `_generate_app_source`, the extractor and the 26 scheme files. S52 edits none.
- **Earlier sections, read only:** S21's ticker and margins (only the union lines of TR-52.5 may change), S31's look keys, S35's date conversion, S44's date ticks, S10's tables (one name added to `_DASH_AXLABEL_HONOURED`).
- **Not this section's:** `xmlabel()`/`xmtick()` (minor ticks, P2.2); `add` on `zlabel()` drawn (named); label `alternate`, `custom`, `labgap` (P2.20).
- **Never:** `_FILTER_JS` (S21's call site stays), `_make_figure_body`, `_generate_app_source`, a hand patch of a generated file.

## Stata truth

New extractor `scripts/extract_axis_add_truth.do` in S02's path-free form (TR-02.9 stanza; `adopath ++ "`repo'/"`, `global dash_nobrowser 1`, `set graphics off`, `version 19`), `_meta` as S31's extractor writes it (`stata_version`, `born_date`, `dash_commit` from `git rev-parse HEAD` via `shell` into a tempfile, `extracted`; the python block never calls Stata, no `shell=True`, a backtick as `\x60`). The recorder is research p1-18's `_rec` (`.Graph.<axis>.major.dlg_tickpos`, `show_labels`) plus `.plotregion1.yscale.curmin/curmax` and `xscale` likewise.

- Auto probes (`scatter mpg weight, …`): every E6 row, a01-a08, `ylabel(0(10)100, norescale)` and `ylabel(0 10 20, norescale)` (ranges), `ylabel(, noticks) ylabel(25, add)`.
- Second axis: b00, b01 and `ylabel(6000, axis(2) add) ylabel(9000, axis(2) add)`.
- by(): `ylabel(25, add) by(foreign)` per panel (`.Graph.graphs[k]`… as S21's recorder reads panels).
- Dates: 60 months (`t = tm(2000m1)+_n-1`, `%tm`, `tsset t`, `y = 100+_n`): `tsline y`, `tsline y, xlabel(492, add)`, `tsline y, tlabel(2001m1, add)` (twoway's side of AD-22 and of the cross case with S51's TA-02).
- Records: per probe `cmd`, `rc`, per axis `ticks`, `labels_shown`, `range`. Written to `test/fixtures/axis_add_truth.json`; `git add -f`.
- Run: `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_axis_add_truth.do"` (log `$S/extract_axis_add_truth.log`).

Area cases, `test/test_suboption_reporting.cscript` (R1; one contiguous run after S31's AXL block, before the summary), each reading the spec from `$dash_json_<name>` after `dash scatter …, name(<n>)`:
- **AD-01** `ylabel(25, add) ylabel(35, add)` → `"ylabel":"25 35, add"`. **AD-02** `ylabel(25) ylabel(35, add)` → `"25 35"`. **AD-03** `ylabel(25, add) ylabel(35)` → `"35"`. **AD-04** `ylabel(25, add) ylabel(, nolabels)` → `"25, nolabels add"`. **AD-05** `ylabel(25, nolabels) ylabel(35, add)` → `"25 35, nolabels"`. **AD-06** the after-comma merge: `(scatter mpg weight, ylabel(25, add)), ylabel(35, add)` → `"25 35, add"`.
- **AD-07** `ylabel(15(10)35, add)` → `"15 25 35"`; `ylabel(15 25 35, add)` → `"15 25 35, add"`; `ylabel(#2 25, add)` keeps no `add`. **AD-08** `ylabel(0(10)100, norescale)` → no `norescale`; `ylabel(0 10 20, norescale)` keeps it; `ylabel(15/17, add)` keeps `add`. **AD-09** `mata: _dash_axis_pieces()` on `", add"`, `"25, add"`, `"\"a\" 25, add"`, `"15(10)35, add"`, `"15(10)35 50, add"`, `"#3 25, add"`, `"minmax, add"`, `"none, add"`, `"15/17, add"` sets `_ap_rule` 0 0 0 2 1 1 1 1 0, the T piece keeping `add` exactly for the 0s; AL-02's case still passes.

S52 block of `test/test_wp30_truth.cscript` (fills S01's stub; helpers `_s52_*` above its header): **AD-20** live `twoway scatter mpg weight, ylabel(25, add)` ticks (recorder) against dash's saved page ticks (python reader of the page's `FixedTicker`, S21's reader helper if it exists); **AD-21** b01 on the second axis; **AD-22** dash's `tsline y, xlabel(492, add)` (492 is 2001m1; no S51 fold needed) against live twoway's `tsline y, tlabel(2001m1, add)` (c16), both recorded in the same run.

## TDD test stubs

New `test/test_axis_add.py`. Imports: `dash_render as dr`; `test_mode_parity` `_render_pair`, `_spec`; `test_saved_filter_layers` `_render`, `_move`; `test_served_filter_move` `_move as _served_move`; `js_runner.requires_node`; S21's tick readers from `test_default_axes.py` (`_ticks_of`). `_FIX = json.load(test/fixtures/axis_add_truth.json)`; `_MODES = ("saved", "served")`.

Regression tests (red at the batch-18 base):
- Test: the fixture has the four `_meta` keys, `stata_version` starting `19.`, every E6 probe — `TestTheFixture::test_it_is_stamped` (guard after 52-01)
- Test: `_dash_parse_axis_spec("25, add")["add"] is True` and nothing is unsupported; `'25 "add" 35'` has `add` False; `"15(10)35, add"`, `"#2 25, add"`, `"minmax, add"` have `add` False; `"15/17, add"` True — `TestTheParser::test_add_is_read_from_the_tail`
- Test: per auto probe of E6, both modes, the y ticks drawn equal the fixture's — `TestAddUnionsWithTheDefault::test_probe[mode-<id>]`
- Test: the same after a saved `_move` and a served `_served_move` that keeps every row and one that keeps half — `TestAfterAFilterMove::test_probe[mode-<id>]`
- Test: `%tm` 60-month frame, `xlabel: "492, add"`: ticks equal the same spec's ticks without the key plus 492 (in the axis's units), before and after a move — `TestOnADateAxis::test_one_date_is_added[mode]`
- Test: `ylabel2: "6000, add"` on the two-axis frame: y2 ticks equal b01's, no note — `TestTheSecondAxis::test_add_is_drawn[mode]`
- Test: `by: "foreign"`, `ylabel: "25, add"`: every panel's ticks equal the fixture's — `TestUnderBy::test_each_panel[mode]`
- Test: `ylabel: "25, add nolabels"`: label font `0px` on the axis, ticks still unioned; `noticks` gives zero tick lengths — `TestTheLookApplies::test_nolabels_and_noticks[mode]`
- Test: the saved plan's `extra` holds 25 and the node run of `_DASH_AXIS_FINISH_JS` on the moved plan writes the union; the served `_dash_refinish_axes` writes the same; served re-finish time within A9 — `TestTheRefinishKeepsIt::test_both_modes_agree`
- Test: `zlabel: "1000, add"` names `add` once in each mode — `TestTheColourKeyNamesIt::test_named_once`
- Test: `ytick: "25, add"` draws as `ytick: "25"` and is silent — `TestTheTickOptionIgnoresIt::test_silent[mode]` (guard: green at the base for drawing, red for the note)
- Test: `_dash_axis_add` unit cases (default-tagged ticker kept; plain ticker replaced by a count ticker; categorical untouched; labels merged; returns False without values) — `TestTheUnitFunctions::test_axis_add`
- Test: dash.sthlp's label paragraph names `add` as drawn and the second-axis sentence no longer says "named, not applied" — `TestTheHelp::test_it_documents_add`

`test/test_mode_parity.py`: append two `CORPUS` and one `MOVE_CORPUS` case tagged `"WP-30 P1.18b"` (`ylabel(25, add)`; `ylabel2(6000, add)` dual axis; the `%tm` `xlabel(492, add)`).

### Pinned tests to flip (R9; re-measured, never trusted)

`test_axis2_suboptions.py::TestTheSecondAxisOptionsReachTheSecondAxis::test_add_is_named_on_ylabel2` → `test_add_is_drawn_on_ylabel2` (no note; y2 ticks default plus 5000 and 10000), `Flipped:` line "named and not drawn was wrong because twoway draws an axis(2) add (b01)". Any further node 52-01's run shows naming `add` is flipped the same way and listed in `$S/52-flips.txt`.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Parser | pytest `TestTheParser` | literal | n/a |
| Union with default ticks | `TestAddUnionsWithTheDefault`, `TestUnderBy`, `TestTheLookApplies` | `axis_add_truth.json` | yes |
| After moves, both re-finishers | `TestAfterAFilterMove`, `TestTheRefinishKeepsIt` (node) | auto frame | yes |
| Dates | `TestOnADateAxis`; truth AD-22 | 60-month frame | yes |
| Second axis | `TestTheSecondAxis`; AD-21 | dual-axis frame | yes |
| Mata merge, ado rule | cscript AD-01..AD-09 | sysuse auto | n/a |
| Live twoway | truth AD-20..AD-22 | sysuse auto, tsline | saved |
| Parity | `test_mode_parity.py` | corpus | yes |
| Registries, tracking | map, coverage, served-name guards, `test_tracking_documents.py` | — | n/a |

**Acceptance criteria.**
- **AC-52.1** (BR-52.1, BR-52.2) Every E6 auto probe draws the fixture's ticks in both modes; AD-20 PASS.
- **AC-52.2** (BR-52.3) `TestAfterAFilterMove`, `TestTheRefinishKeepsIt` and `TestOnADateAxis` pass, node not skipped; A9's budget holds.
- **AC-52.3** (BR-52.4, BR-52.5) AD-01..AD-09 PASS; r23 still PASS.
- **AC-52.4** (BR-52.6, BR-52.7) `TestTheLookApplies`, `TestUnderBy`, `TestTheColourKeyNamesIt`, `TestTheTickOptionIgnoresIt` pass; `add` appears in no axis note of the suite.
- **AC-52.5** The flipped node passes; the full suite through the queue reports 0 failed; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 52-01 to 52-12 form one commit, made by 52-12 on `wp30-s52` with the subject `Add the add sub-option's values to the default ticks in both modes and after moves (WP-30 P1.18b)`. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s52`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S52 "$SLOT" "$S" "$S/run_<script>.do"`.

<task type="auto" id="52-01">
  <name>Write the fixture and failing tests</name>
  <files>scripts/extract_axis_add_truth.do, test/test_axis_add.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-18-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s52`; stop otherwise. Create `scripts/extract_axis_add_truth.do` as "Stata truth" describes and run it through `$SLOT` with `DASH_REPO="$WT"`; it writes `test/fixtures/axis_add_truth.json`. Compare it with E6 row by row; any difference stops the section. Create `test/test_axis_add.py` with every stub of "TDD test stubs" (new names `dr._dash_axis_add` fail with AttributeError now) and append the three `test_mode_parity.py` cases before `CORPUS`'s and `MOVE_CORPUS`'s closing brackets. Run `python3 -m pytest test/test_axis_add.py -q -n 6 -p no:cacheprovider -rf > "$S/52-new.log" 2>&1` and the parity file with `-k "WP-30 P1.18b"`, then grep the suite for tests that expect `add` named (E7) into `$S/52-flips.txt`. Write `$S/52-P1.18b-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)". Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/axis_add_truth.json')); print(all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')), d['probes']['b01']['yaxis2']['ticks'])"` prints `True [0.0, 5000.0, 10000.0, 15000.0, 6000.0]` (or the same as ints); `grep -c FAILED "$S/52-new.log"` is at least 12; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata dash_render.py` prints nothing.]]></verify>
  <done>The add fixture existed and every pytest regression test was shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="52-02">
  <name>Write the Stata merge and rule cases</name>
  <files>test/test_suboption_reporting.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    In `test/test_suboption_reporting.cscript`, directly after S31's AXL block and before the summary, add one contiguous run headed `// AD: add merged and kept as twoway reads it (WP-30 P1.18b)` with AD-01..AD-09 of "Stata truth", each printing `AD-nn PASS: …` in the script's `nfail`/`faillist` form; values are read from `$dash_json_<name>` through Mata, never by macro expansion. Fill S01's S52 stub of `test/test_wp30_truth.cscript` with AD-20..AD-22 (helpers `_s52_*` directly above the S52 header). Run both through the driver on the unmodified shipped files and append each `AD-nn FAIL` line to `$S/52-P1.18b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "AD-0[1-9] FAIL" "$S/run_test_suboption_reporting.log"` is at least 5 (AD-02, AD-03 and AD-05 may pass as guards); `grep -cE "AD-2[0-2] FAIL" "$S/run_test_wp30_truth.log"` is at least 2; `grep -c "AXL-01 PASS" "$S/run_test_suboption_reporting.log"` prints 1.]]></verify>
  <done>The merge, rule and live twoway cases were in their scripts and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="52-03">
  <name>Keep add through the Mata merge</name>
  <files>dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-52.10 to `_dash_rep_merge` (cat "L" only; `keep = has2 ? (a2 & a1) : a1`; `add` re-appended to the merged sub-options) with a comment citing E6's merge rows and a01. Apply TR-52.9 to `_dash_axis_pieces` in place, updating its comment block and header-index text; no regex, no new function. Extend the `_dash_axis_pieces` COVERAGE entry (TR-52.13). Run AD-01..AD-09 and test_gaps2_truth.cscript's AL block through the driver.
  ]]></action>
  <verify><![CDATA[`grep -cE "AD-0[1-9] PASS" "$S/run_test_suboption_reporting.log"` prints 9; `grep -c "AL-02 PASS" "$S/run_test_gaps2_truth.log"` prints 1; after a driver run of `test_twoway_option_parity.cscript`, `grep -cE "r23.*FAIL|FAIL.*r23" "$S/run_test_twoway_option_parity.log"` prints 0.]]></verify>
  <done>Repeated axis-label copies kept add as twoway keeps it, and the splitter spent add after a leading rule and norescale after a lone rule.</done>
</task>

<task type="auto" id="52-04">
  <name>Document the rule in the expander</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In `_dash_axis_expand` (TR-52.8) rewrite only the header comment above `program define _dash_axis_expand` to name the two rules `_dash_axis_pieces` now applies (a rule-led head spends `add`; a lone `a(b)c` rule drops `norescale`), cite E4 and E6, and name `_ap_rule`; no statement changes. Run the AXL and AD blocks of `test_suboption_reporting.cscript` through the driver.
  ]]></action>
  <verify><![CDATA[`grep -cE "AD-0[1-9] PASS" "$S/run_test_suboption_reporting.log"` prints 9; `grep -cE "AXL-[0-9]+ FAIL" "$S/run_test_suboption_reporting.log"` prints 0.]]></verify>
  <done>dash.ado's expander said which rules keep add and norescale for the renderer, and every AD and AXL case passed.</done>
</task>

<task type="auto" id="52-05">
  <name>Read add in the axis parser</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_parse_axis_spec` is CRITICAL. Add `"add"` to `_DASH_AXLABEL_HONOURED` in place and the TR-52.1 key and head rule to `_dash_parse_axis_spec`, extending its docstring. Run `TestTheParser`, then `test_axis_suboptions.py`, `test_graph_options.py` and `test_axis2_suboptions.py` (all must stay green except the E7 flip).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_axis_add.py::TestTheParser" test/test_axis_suboptions.py test/test_graph_options.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The parser read add from the tail only and spent it after a leading rule.</done>
</task>

<task type="auto" id="52-06">
  <name>Union added values with default ticks</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `_dash_axis_add` (TR-52.2) after `_dash_apply_axis_spec` with a docstring citing E2 and E6. Give `_dash_apply_axis_spec` the keyword `numticks=None` and the add path of TR-52.3; change the default-ticker conditions in `_dash_apply_axis_options` (TR-52.3) and `_dash_finish_secondary_axes` (TR-52.4), passing `numticks`. Add `"_dash_axis_add",` at S52's copy-list anchor (TR-52.11) and its map key under S52's anchor. Run `TestAddUnionsWithTheDefault`, `TestTheSecondAxis`, `TestUnderBy`, `TestTheLookApplies` and `TestTheUnitFunctions`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_axis_add.py" -q -n 6 -p no:cacheprovider -k "Union or SecondAxis or UnderBy or LookApplies or UnitFunctions"` reports 0 failed; `python3 -m pytest test/test_statistical_helpers.py -q -n0 -k TestTheServedAppCarriesEveryName` passes.]]></verify>
  <done>add drew the default ticks plus the listed values on first and second axes in both modes at build.</done>
</task>

<task type="auto" id="52-07">
  <name>Keep the union through re-finishes</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Run `TestAfterAFilterMove`, `TestOnADateAxis` and `TestTheRefinishKeepsIt`. For each failure, apply the matching TR-52.5 bullet only: the `_extra` union in `_dash_place_count_ticks` for default and date entries, the hull rule with `_dash_extra_norescale`, `extra` in `_dash_axis_plan`, and the union in `_DASH_AXIS_FINISH_JS`'s `dash_axis_compute` (one sorted, de-duplicated union before padding, keyed as the Python side keys). Record in `$S/52-finisher.txt` which bullets were needed and the served re-finish time with and without add.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_add.py -q -n 6 -p no:cacheprovider` reports 0 failed with no node test skipped; `python3 -m pytest test/test_default_axes.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Both modes kept the added values through every re-tick after a move, on numeric and date axes, within the A9 budget.</done>
</task>

<task type="auto" id="52-08">
  <name>Name add on the colour key</name>
  <files>dash_render.py, test/test_axis2_suboptions.py</files>
  <action><![CDATA[
    Warn that `_dash_apply_z_options` is HIGH. Add `add` to the typed names it reports (TR-52.6). Flip `test_add_is_named_on_ylabel2` in place to `test_add_is_drawn_on_ylabel2` (E7) with a comment naming b01, and record the `Flipped:` line in `$S/52-flips.txt`. Run `TestTheColourKeyNamesIt`, `TestTheTickOptionIgnoresIt`, `test_axis2_suboptions.py` and `test_colorvar_forms.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis2_suboptions.py test/test_colorvar_forms.py "test/test_axis_add.py::TestTheColourKeyNamesIt" "test/test_axis_add.py::TestTheTickOptionIgnoresIt" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>zlabel's add was named once, ytick's add drew silently, and the axis(2) pin asserted the drawn ticks.</done>
</task>

<task type="auto" id="52-09">
  <name>Check parity and any remaining pin</name>
  <files>test/test_mode_parity.py</files>
  <action><![CDATA[
    Run `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider` (G3) with S52's cases; `ALLOWED` and `_MUST_WARN` are not edited (R8). If `$S/52-flips.txt` lists a node other than 52-08's (none was found when this file was written), flip it in place in its own file in this task (move its token to `labgap`), never deleting it, record its `Flipped:` line and name the file in `$S/52-files.txt`; more than one further file stops the section for a re-plan.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py test/test_suboption_warnings.py -q -n 6 -p no:cacheprovider` reports 0 failed; `git -C "$WT" diff -- test/test_mode_parity.py | grep -c "^-.*ALLOWED"` prints 0.]]></verify>
  <done>Both modes agreed on the new cases and every pin that expected add named had been flipped with its reason.</done>
</task>

<task type="auto" id="52-10">
  <name>Document add in the help</name>
  <files>dash.sthlp, test/test_axis_add.py</files>
  <action><![CDATA[
    Re-grep "Axis and Display Options" at the base (S10, S15, S18, S21, S31, S35, S44, S50 and S51 edited it; R3) and make the two TR-52.14 edits only, keeping S51's paragraph untouched. Run `TestTheHelp`, `test_help_conformance.py` and `test_help_claims_7.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_axis_add.py::TestTheHelp" test/test_help_conformance.py test/test_help_claims_7.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "is named, not applied" "$WT/dash.sthlp"` prints 0.]]></verify>
  <done>The help said add adds to the default ticks on both axes and how copies merge.</done>
</task>

<task type="auto" id="52-11">
  <name>Run the section's scripts and suites</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_axis_add.py`, `test_axis2_suboptions.py`, `test_default_axes.py`, `test_axis_suboptions.py`, `test_mode_parity.py`, `test_function_test_map.py`, `test_program_coverage_map.py`, `test_fixtures_are_committed.py` and the served-name guards (G4) with `-n 6`; `test_suboption_reporting.cscript`, `test_twoway_option_parity.cscript` and the S52 truth block through the driver. Every case prints PASS; a SKIP is not a pass (check `~/.stata19/console/stata19.rc` still holds `python_exec`).
  ]]></action>
  <verify><![CDATA[Each pytest run reports 0 failed; `grep -c "AD-.. FAIL" "$S/run_test_suboption_reporting.log" "$S/run_test_wp30_truth.log"` prints 0 for both; `grep -c SKIP "$S/run_test_wp30_truth.log"` prints 0.]]></verify>
  <done>Every changed test file and the section's script cases passed in the worktree.</done>
</task>

<task type="auto" id="52-12">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.18b"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution". Delete only the `"P1.18b"` key line. Replace `<!-- WP-30 P1.18b -->` in place with "Notes: CHANGELOG line". Run `test_tracking_documents.py -n0`; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/52-full.log"` in the background, waited for on its `exit=` line and read, never relaunched (E6 for known flaky tests). Stage exactly the files 52-01 to 52-12 changed, `git add -f test/fixtures/axis_add_truth.json`; check `git -C "$WT" diff --cached --name-only` (G6). Write `$S/52-message.txt` ("Notes: commit message"), check G7, confirm the branch, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/52-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.18b -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.18b": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.18b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.18b was closed naming existing tests, its marker carried the old and new ticks, and one green commit on wp30-s52 was ready for the merger.</done>
</task>

## Section completion criteria

- `add` after values unions with the default ticks (S21's and S44's) on every axis, in both modes, before and after saved and served moves, in by() panels; after a rule it is spent (fixture probes, AD-20..AD-22).
- `ylabel(…, axis(2) add)` is drawn and not named; `zlabel()`'s `add` is named; `ytick(…, add)` is silent.
- The Mata merge and `_dash_axis_expand` reproduce E6's merge and rule rows (AD-01..AD-09); r23 still passes.
- `_dash_axis_add` exists, is mapped and travels to the served app; `_dash_axis_pieces` rates the head and its coverage entry names AD-09.
- The fixture is generated, stamped, committed with `-f` and read by tests.
- One green commit `(WP-30 P1.18b)` on `wp30-s52` closes the entry, deletes its key and replaces its marker.

## Notes

- **The finisher edits are conditional.** S21 already unions `_dash_extra_ticks` for `#N` lists and plans `extra`; S44's date path is not yet written. 52-07 edits only what its tests prove missing, and records which bullets were needed, so the merger's `detect-changes` matches.
- **Units.** On a date axis the listed values are Stata dates; S35's `_dash_date_axis_spec` converts `spec["ticks"]` before `_dash_axis_add` stores them, so the extras are in the axis's own units, as the `#N` list's are.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the extractor and the truth block then fail or SKIP. Check after each slot run.
- **Merge rules for the shared files.**
  - R1: AD-01..AD-09 as one run after S31's AXL block in `test_suboption_reporting.cscript` (no batch-18 partner edits it); S52's own truth block.
  - R2: one name at S21's anchor after S47's; one map key; one coverage key.
  - R3: Axis and Display Options, two sentences; S51's paragraph in the same title lands first and is kept.
  - R4/R5: the one `P1.18b` marker, entry and key.
  - R6: no new Mata function and no `_needed` change (S51 extends both in this batch); `_dash_rep_merge` and `_dash_axis_pieces` change in place, header-index text in place.
  - R7: new extractor and fixture, never run by another section.
  - R8: three corpus cases. R9: E7's flip. R11: S52 is batch 18's only finisher editor; A9 kept. R12: no one-editor symbol edited.
- **Commit message.** Subject as in "Commit boundary". Body: `$S/52-P1.18b-failure.txt`; the measured defect (Overview's block); what changed and where (TR-52.1-TR-52.14, both modes, the finisher bullets 52-07 needed); then `Regression: test/test_axis_add.py::<Class>::<test> -- failed at <base sha> with <text>` per node (cscripts as `test/test_suboption_reporting.cscript AD-01`, `test/test_wp30_truth.cscript AD-20`); the `Flipped:` lines of `$S/52-flips.txt`; `Fixture: test/fixtures/axis_add_truth.json (scripts/extract_axis_add_truth.do)`; `BUGS.md: "<WP30_OPEN["P1.18b"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.18b). add after a list of values adds them to the axis's default ticks (S21's natscale ticker, S44's date ticker) instead of replacing them, on x and y, first and second axes and in every by() panel, in the saved page and the served app and through every re-finish after a filter move (_dash_parse_axis_spec reads it from the tail, _dash_axis_add, _dash_apply_axis_options, _dash_finish_secondary_axes, the finisher union); after a leading a(b)c, #N, minmax or none rule it is spent, as twoway spends it; dash.ado keeps the rule-versus-list distinction (_dash_axis_expand through Mata _dash_axis_pieces), which also drops norescale from a lone rule as twoway does; repeated copies keep add as twoway merges them (_dash_rep_merge); an axis(2) add is drawn; zlabel()'s add is named. Pinned by test/test_axis_add.py::TestAddUnionsWithTheDefault::test_probe, test/test_axis_add.py::TestAfterAFilterMove::test_probe, test/test_axis_add.py::TestOnADateAxis::test_one_date_is_added, test/test_axis_add.py::TestTheSecondAxis::test_add_is_drawn, test/test_suboption_reporting.cscript AD-01, test/test_wp30_truth.cscript AD-20; fixture test/fixtures/axis_add_truth.json.
  ```
- **CHANGELOG line** (replaces the marker in place, in the WP-30 group of Results that change):

  ```
  - `add` adds to the default ticks: `dash scatter mpg weight, ylabel(25, add)` drew one tick at 25 and named `add` in a note, and now draws 10 20 30 40 and 25, as twoway does, on date axes (`tlabel(2001m1, add)`) and second axes (`ylabel(6000, axis(2) add)`, named before) too, before and after filter moves; after a rule (`ylabel(15(10)35, add)`) `add` has no effect, repeated `ylabel(…, add)` copies keep it, and `ylabel(0(10)100, norescale)` now widens the axis as twoway's lone rule does. (WP-30, P1.18b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md B21:** with S10 and S31 landed, B21-f (`add`) is closed by `<sha>`; B21 stays partly open only for P2.20's items (labgap, label and tick styles, grid styles, gmin/gmax, custom, alternate).
  - **REMAINING.md:** REM-09-02-LABEL-ADD closed; the :2459 label bullet loses `add`.
  - **DROPIN-REMAINING.md:129 (P1.18):** "Closed by <S31 sha> (P1.18a) and <sha> (WP-30 S52)"; the WP-29 axis(2) `add` note is closed by the same commit.
  - **AGENTS.md invariant:** "added axis values live only in `_dash_extra_ticks`, unioned by `_dash_place_count_ticks` and `_DASH_AXIS_FINISH_JS` from the plan's `extra`."
  - **Unverified:** twoway's treatment of `add` after a rule in a later copy (`ylabel(25, add) ylabel(15(10)35, add)`) is not measured; dash reads the merged head's first token.
