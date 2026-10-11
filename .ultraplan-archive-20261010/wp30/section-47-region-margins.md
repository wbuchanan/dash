# Section 47: Plot-region margin and inner box (P1.20 part b)

> Part of: WP-30 · Items: P1.20 (entry `P1.20b`; GAPS2-B18-a, AUDIT-66 margin half) · Risk: yellow · Batch: 16 (merge order S45, S46, S47; S47 regenerates and lands last) · Depends on: 08, 21, 38 · Blocks: 50, 57 · Tasks: 11, 1 commit · Case prefix: RM

## Review amendments

- Fixed (major): S38's reader was cited generically ("S38's tokeniser", "region reader", "not-drawn table"). It is now named as section-38 fixes it: `_dash_by_tokens` with `_dash_region_table()`; `_dash_region_spec`, called once by `_dash_inner_box` for the inner fill and line, so S43's bare forms and `%NN` come from the same reader; and the BR-38.9 name set inside `_dash_region_spec`, made option-dependent for plotregion. S47 calls `_dash_apply_regions` and does not edit it.
- Fixed (major): `$S` was shared with S45 and S46 (parallel); it is now `<scratch>/s47`, with the batch files read from `<scratch>`.
- Fixed (minor): the unknown-margin note is keyed once per graph and text, so `_dash_share_by_scales`' recomputation and re-finishes never repeat it. The truth block states TR-01.10's form and its exact header.
- Checked: `_dash_padded_range` (:23489), `_dash_range_hull` (:23535) and `_dash_apply_scale_ranges`' record-only tail (:26098-26100); the 20 root `dash-*.scheme` files (26 after S07) and `scripts/extract_scheme_truth.py`; S38's Mata merge keeps every `margin()` copy in order (TR-38.6), which COPY/COPYR rely on. S47 is batch 16's only finisher editor and regenerator. It edits neither `_make_figure_body` nor the template, and no function shared with S45 or S46. Its RM run follows S45's RC run in `test_twoway_option_parity.cscript` (R1 merge order).
- Rejected: editing `_dash_apply_scale_ranges` (the manifest names it). Since S21 it records `range()` and reverse only, and the margin reaches every range through `_dash_hull_ranges` (D-47f).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:131 (P1.20) reads: "`margin()` … and the `i*` options … have no effect and nothing is reported." S38 (batch 13) drew and named the styling sub-options; the margins and the plot region's inner box are left here. S21 (batch 7) gave every default axis twoway's plot-region margin from the scheme's `margin twoway` and left `plotregion(margin())` "ignored and silent, as today" (section-21 Boundaries; guard `TestPlotregionMarginIsStillIgnored`). Measured (research `.ultraplan/wp30/research/p1-20.md` §3.2-3.3, s2color, SVG 3960 × 2880 units, min(W,H) = 2880):

```
twoway:  base plot margin 2.2% = 63.36 units a side ; margin(zero): data and ticks reach the frame
         margin(l+10): left inset 63.36 + 288 = 351.36 ; margin(large): 230.4 (8%)
         margin(zero) then margin(l+10) (two copies): left 10%, other sides zero
         plotregion(ifcolor(red)): an inner rect #FF0000 at the frame inset by the plot margin; icolor() also outlines it
         graphregion(margin(l+10)): the plot region moves right by 287.97 (10% of 2880)
dash:    every case above draws the base figure, in both modes, with no note
```

This pass (`s47probe/m1.do`, StataNow 19.5, `scatter mpg weight, plotregion(<o>)`, first marker's SVG centre): `margin(bogus)` prints `(note:  named style bogus not found in class margin, default attributes used)` and draws exactly as `margin(zero)`; `margin(l+5 l+5)` draws as `margin(l+10)`; `margin(l +10)` as `margin(l+10)`; `margin(medsmall)` and `margin(2.2 2.2 2.2 2.2)` as the default; `margin(sides)` as `margin(3.5 3.5 0 0)`; `margin(l-5)` puts the first marker left of `margin(l=0)`'s (1568.78 against 1620.26), so a side can go below zero; `margin(10-pt)` is accepted; `margin(L+10)` prints `(note:  named style L not found in class gsize, …)`; `margin(1 2 3)` and `margin(1 2 3 4 5)` are accepted and draw something else.

**After this section**, in the saved page and the served app, at build, after every filter move and on reset:
- `plotregion(margin())` sets the plot-region margin by twoway's marginstyle grammar (the 28 style names, `# # # #` as left right bottom top, `l|r|b|t [+|-|=] #` in % of min(W,H), `#-pt` styles), applied in order over the scheme's `margin twoway` and over earlier copies, per side, through S21's `_dash_plot_margin`, `_dash_padded_range` and finishers; zero is exact, other values within A6's tolerance (about 0.8% of the width); an unknown name prints twoway's note and draws zero, as twoway does;
- `plotregion(istyle() icolor() ifcolor() ilstyle() ilcolor() ilwidth() ilpattern())` draws the inner box as one BoxAnnotation in data units at the finished axis hull, styled by S38's region reader, moved by the re-finish after a move;
- `graphregion(margin())` and the graphregion `i*` options are named in S38's one note, not drawn (P1.20.2, P1.20.3);
- the 26 shipped scheme files carry Stata's margin ladder (`gsize <x>margin`), so a user scheme that changes it is read.

**Why one section.** One margin model (register P1.20.8: "P1.3-A owns `_dash_plot_margin` … P1.20b extends its grammar: l/r/b/t with + - =, copies that add, the inner box and the graphregion margin. No second parser.") and S21's finisher chain carry both the margin and the inner box; S47 is batch 16's one finisher editor (A153, R11) and its one scheme regenerator (A152).

**Test order and commit rule (rule 7).** One cycle on `wp30-s47`: 47-01 to 47-03 write the fixture and every regression test and run them against the unmodified batch-16 base, saving `$S/47-P1.20b-failure.txt` (no commit); 47-04 to 47-10 fix, regenerate, flip and document; 47-11 closes the entry and makes the one commit. No test-only commit exists, and no commit is red.

**Section decisions (this file).**
- **D-47a Per-side fractions.** `_dash_plot_margin` returns `{"x": (left, right), "y": (bottom, top)}`, each a frame fraction in visual order (start side, end side), so a reversed axis keeps "left" on the left (twoway's margins are sides of the plot region, not data ends). `_dash_padded_range(…, margin=)` and its inverse accept a pair or, for S21's callers and hand-built ranges, a float meaning both sides.
- **D-47b Bounds.** Each side is clamped to [−0.45, 0.45] and the two sides of an axis to a sum of at most 0.9 (both scaled down together), so a hostile or careless value can never collapse or invert a range. Negative sides are kept (measured `l-5`).
- **D-47c Forms dash reads.** The help's grammar only (a name, four numbers, `l|r|b|t` terms with an optional blank and sign, `=` when no sign). Everything else (`L+10`, three or five numbers, `1;x:y`) gets twoway's note naming the text and draws zero, as `bogus` does; twoway's own drawing of `L+10`, `1 2 3` and `1 2 3 4 5` is not reproduced (residual).
- **D-47d by() panels.** A user margin is multiplied by S21's f(G) as the default is (D-21b), on the hypothesis H-47.1 that twoway scales the plot region's margin as one quantity; the fixture's `BY_L10` and `BY_ZERO` probes decide in 47-01, and if they contradict H-47.1 the model takes the fixture's rule and the commit body says so.
- **D-47e No box without an i\* option.** The BoxAnnotation exists only when an inner sub-option is given (every shipped scheme's `areastyle inner_plotregion` is `none`), so pages without one are unchanged except for the plan's margin pairs (Notes: digest).
- **D-47f `_dash_apply_scale_ranges` is read, not edited.** Since S21 it records `range()` values and reverse only (dash_render.py:26051-26100); the margin reaches every range through S21's `_dash_hull_ranges`. The manifest's mention is satisfied by reading `fig._dash_scale_reverse` there.

## Risk: [yellow] — two CRITICAL symbols on every axis range, a JS twin that must agree to 1e-9, and a regeneration that lands last

**Why.**
- `_dash_padded_range` is CRITICAL (10 impacted, 3 direct; research §6); every axis range of both modes passes through it after S21.
- `_make_figure_body` is CRITICAL; S47 is batch 16's reserved editor of it (R12) but this design does not need to edit it (TR-47.10); if 47-08 finds it must, it warns before editing.
- S21's finishers (`_dash_plot_margin`, `_dash_hull_ranges`, `_dash_range_hull`, `_dash_finish_count_ticks`, `_dash_share_by_scales`, `_dash_finish_secondary_axes`, `_dash_axis_plan`, `_DASH_AXIS_FINISH_JS`) did not exist at `c96facd`; 16.0 runs `gitnexus impact` on each at the batch base and reports HIGH/CRITICAL (S21 flagged `_dash_share_by_scales` and `_dash_common_count_ticks` CRITICAL).
- `SchemeParser._init_properties` (LOW, 3 real callers) and the extractor's `expected_directives` (LOW).
- S38's region reader and not-drawn table (names fixed by S38 at batch 13) are edited in one place: the plotregion `margin` and plotregion `i*` entries leave the not-drawn list.

**Risk factors.**
1. Changing the margin from a number to a pair touches every consumer S21 wrote, in Python and in the JS twin.
2. The inner box must follow the hull after a move in both modes, on shared by() ranges, on y2/x2 and on date and log axes.
3. Regenerating 26 scheme files collides with any other generator in the batch.
4. The plan JSON gains pairs, which moves the single-y page digest (R10) though S47 is not in R10's expected list.
5. Hostile margin text (huge, negative, very long, punctuation) reaches a parser in both modes.

**Mitigation.**
1. Float stays accepted (D-47a); S21's tests are re-measured and flipped with reasons (R9); `test_natscale_js.py`'s padding parity extends to pairs (2,000 seeded cases).
2. One helper `_dash_inner_box(fig)` is called at the end of `_dash_hull_ranges` (build and re-finish, both modes), and the plan carries the box model so `dash_axis_finish` writes it; tests after saved (node) and served moves, under by(), on a reversed, a log and a `%td` axis.
3. A152/R7: S47 is the batch's only regenerator and lands last; a conflict is resolved by re-running the extractor on the merged tree, never by hand.
4. 47-09 re-derives the digest on the worktree with a comment naming P1.20b; the merger re-derives it on the merged tree (R10).
5. D-47b's bounds, a 2,000-character cap on the margin text read (longer is noted, zero drawn), linear-time parsing, and `TestHostileMargins` (timing and no CSS path: nothing here reaches CSS; margins are numbers in ranges).

## Dependencies

- **Depends on: 08, 21, 38.**
  - S08 (batch 3): the relative unit, 1 rs = min(W,H)/100, and `pt` sizes through `resolve_size` (TR-08.9); `#-pt` margins convert through it.
  - S21 (batch 7): `_dash_plot_margin(scheme, graph_opts, panels=1)` (TR-21.4), `fig._dash_margin`/`_dash_margin_args` stamps in both modes (TR-21.5), `_dash_padded_range(lo, hi, kind, reverse, margin)` and `_dash_range_hull` (TR-21.8), `_dash_hull_ranges`, `_dash_finish_count_ticks(fig, refinish)`, `_dash_common_count_ticks`, `_dash_share_by_scales` (f(G), D-21b), `_dash_refinish_axes` (served), `_dash_axis_plan` and `_DASH_AXIS_FINISH_JS` (`dash_axis_pad`, the inverse, `dash_axis_finish`), `SchemeParser.plot_margin_rs` from `margin twoway` through `_DASH_MARGIN_RS` (D-21a), and the guard `test/test_default_axes.py::TestPlotregionMarginIsStillIgnored`.
  - S38 (batch 13), by the names its section file fixes (section-38 TR-38.1-TR-38.4): `_dash_region_table()` (the region rows, canonicalised by `_dash_subopt_canon(name, _dash_region_table())`), the quote-aware tokeniser `_dash_by_tokens` it reads with, `_dash_region_spec(raw, option, base, scheme, ref_in)` → `(settings, named)` whose `named` holds the tokens of BR-38.9's set (the "not-drawn table" below), `_dash_region_blend` and `_dash_apply_regions(fig, graph_opts, scheme, seen, key)`. Also: the region table in S10's `_dash_subopt_canon` (canonical names, abbreviations `m`, `mar`, `ic`, `ifc`, …), Mata `_dash_rep_subkey`/`_dash_rep_merge` merging region copies by canonical name and keeping every `margin()` copy in order ("so margins accumulate for S47"), the region reader that replaced `_extract_region_*` (R2 row S38) with its resolution of colour, `none`, `%NN`, `style(none)`/`lstyle(none)`, widths and patterns, its one not-drawn note, and the refusal of a sub-option repeated within one copy (P1.20.1).
  - S01 provides the open entry `P1.20b`, its `WP30_OPEN` key, the marker `<!-- WP-30 P1.20b -->` in the WP-30 group of `### Results that change`, the S47 stub and the map anchor `# WP-30 S47 (P1.20b): Plot-region margin and inner box (P1.20 part b)`.
  - Landed before and extending the same finishers: S27 (`_dash_finish_auto_bases`), S35 (date transforms), S44 (`_dash_ts_pair`, `_DASH_TSNATSCALE_JS`).
- **Blocks: 50, 57.** S50 (batch 17) reads this margin model for `noextend` (P1.21: under `margin(zero)` noextend equals extend); S57 audits the served move path that calls `_dash_refinish_axes`.
- **Parallel batch: 16**, merge order S45, S46, S47; S47 lands last (A152).
- **Can run with:** S45 (dash.ado plot parser, mapper tails, `_dash_layer_series`) and S46 (`_generate_app_source`, launcher, serve options). S47 edits neither the template nor a mapper; neither partner edits a finisher, `_dash_plot_margin`, SchemeParser or a scheme file.

## Evidence

Anchors at `c96facd` unless named as S21's or S38's (which do not exist there); the executor re-finds each by symbol at `batch-16-base`.

### E1. The range helpers before S21 (dash_render.py)

`_dash_padded_range(lo, hi, kind=None, reverse=False)` (23489) pads 5%; `_dash_range_hull(rng, kind=None)` (23535) inverts it; `_dash_apply_scale_ranges` (26051) only records values and reverse:

```python
26098    fig._dash_scale_values = vals
26099    fig._dash_scale_reverse = rev
26100    fig._dash_rescaled = frozenset(rescale or ())
```

S21 makes the pad f/(1−2f) × span with `margin=f` from `fig._dash_margin[letter]`, records `_dash_margin_f`, and writes ranges in place in `_dash_hull_ranges` (TR-21.8); its JS twin pads the same way (TR-21.11).

### E2. The region code before S38 (dash_render.py `_make_figure_body`)

```python
30354        raw_plotregion = graph_opts.get("plotregion", "")
30355        if raw_plotregion:
30356            _pr_bg = _extract_region_color(raw_plotregion)
...
30371        raw_graphregion = graph_opts.get("graphregion", "")
```

No reader of `margin` or `i*` exists; the served template repeats the block (:35231-35256). S38 replaces both with one shared reader.

### E3. Stata's margin model (StataNow 19.5, read as text)

`plotregionstyle-twoway.style`: `set margin scheme twoway`, `set inner_boxstyle scheme twoway_iplotregion`. scheme-s2color.scheme:195-203 holds the only margin ladder of the shipped schemes (every other scheme inherits it):

```
gsize sidemargin relative3     gsize medmargin relative3p5     gsize medsmmargin relative2p2
gsize medlgmargin relative5    gsize largemargin relative8     gsize vlargemargin relative12
gsize smallmargin relative1p2  gsize vsmallmargin relative0p6  gsize tinymargin relative0p3
```

The 28 `margin-*.style` files set `gleft gright gtop gbottom` to a ladder name, `zero` or a `#-pt` size, e.g. `left`: sidemargin 0 0 0; `sides`: medmargin medmargin 0 0; `top_bottom`: 0 0 medmargin medmargin; `allsides-ms`: medmargin medmargin smallmargin smallmargin; `10-pt`: 10-pt on all four. `areastyle inner_plotregion none` in every shipped scheme. marginstyle.sthlp: `# # # #` is left, right, bottom, top; `{l|r|b|t}[<space>][+|-|=]#`; "# is interpreted as a percentage of the minimum of the width and height of the graph."

### E4. Stata truth already measured (research §3.2, and this pass, Overview)

Quoted in the Overview; the fixture of 47-01 records every case with S21's `margin_rel` method (edge-to-curmin distance over min(W,H)) and the inner rects.

### E5. Tests that pin today's or S21's behaviour (re-measured by 47-09, flipped in place)

- `test/test_default_axes.py::TestPlotregionMarginIsStillIgnored::test_margin_zero_changes_nothing_yet[saved|served]` (S21's guard: "`plotregion(margin(zero))` gives the same ranges as no option (S47's)").
- `test/test_default_axes.py::TestTheHelpers::test_the_plot_margin[...]` and `::test_the_by_factor[...]` (scalar `(fx, fy)` and `["y"] / 0.022`), `::test_padded_range_takes_a_margin`, `::test_range_hull_inverts_any_margin`.
- `test/test_natscale_js.py::TestJsPaddingEqualsPython::test_padded_ranges` (scalar f).
- S38's tests that assert plotregion `margin()`/`i*` named as not drawn (in `test/test_region_options.py`, S38's file; re-found by `grep -n "margin\|ifcolor\|icolor" test/test_region_options.py`).
- `test/test_varlist_expansion.py` `_SINGLE_Y_BASELINE_SHA256` (R10).
- `test/test_scheme_fidelity.py` and the scheme digest pins: regenerated files (R7), compared probe by probe outside `_meta`.

### E6. Blast radius (16.0 at `batch-16-base`)

| Symbol | Risk at `c96facd` / expected | Edited |
|---|---|---|
| `_dash_padded_range` | CRITICAL (10) | yes (pair margins) |
| `_make_figure_body` | CRITICAL | no (TR-47.10) |
| `_dash_range_hull` | TEST_ONLY (S21) | yes (pair inverse) |
| `_dash_plot_margin`, `_dash_hull_ranges`, `_dash_share_by_scales`, `_dash_finish_secondary_axes`, `_dash_axis_plan`, `_DASH_AXIS_FINISH_JS` | S21's; run impact at 16.0 | yes |
| `_dash_apply_scale_ranges` | LOW (3) | no (D-47f) |
| `SchemeParser._init_properties` | LOW | yes (ladder keys) |
| `_dash_region_spec` (S38's; its BR-38.9 named set) | run impact at 16.0 | the named set made option-dependent (TR-47.9); called by `_dash_inner_box` |

## User stories

- **US-47.1** As a twoway user, I want `plotregion(margin(zero))`, `margin(l+10)` and the named margins drawn as twoway draws them, so that my data sit where my do-file puts them.
- **US-47.2** As a twoway user, I want `plotregion(ifcolor(red) ilcolor(black))` to shade the inner plot region, as twoway does, before and after a filter move.
- **US-47.3** As a twoway user, I want `graphregion(margin())` and the graphregion inner options named when dash does not draw them, so that nothing is dropped in silence.
- **US-47.4** As a scheme author, I want my scheme's margin sizes read.

## Business requirements

- **BR-47.1** A `plotregion(margin())` value sets each side's margin as twoway does, applied in order over the scheme's and earlier copies'; zero puts the data hull on the frame exactly; other values are within 0.008 of twoway's frame fraction per side (A6); both modes agree within 1e-9 relative.
- **BR-47.2** The margin holds after every filter move, on reset, under by() (with twoway's panel scaling), on y2/x2, reversed, log and date axes.
- **BR-47.3** An unknown margin text prints twoway's note naming it and draws zero; no margin text can collapse or invert an axis.
- **BR-47.4** The plotregion inner sub-options draw one inner box at the axis hull, styled as S38 styles a region (colour, `none`, `%NN`, `style(none)`, widths, patterns), moving with the hull after a move; without them no box is drawn.
- **BR-47.5** `graphregion(margin())` and the graphregion `i*` options are named in the region note, once per graph, not drawn; plotregion `margin()` and `i*` are no longer named.
- **BR-47.6** The shipped schemes carry the margin ladder, and a scheme that changes it changes the margins.

## Technical requirements

- **TR-47.1 Scheme keys** (scripts/extract_scheme_truth.py; 26 files; `scheme_truth.json`). The extractor resolves the nine ladder keys of E3 through the include chain with provenance, records `margin_ladder` (name → relative value) per scheme, and writes the nine `gsize <name>margin relative<v>` directives through `expected_directives` in its scalar form. A regenerated file is never patched by hand (R7).
- **TR-47.2 SchemeParser** (travels with its class). `_FALLBACK_PROPS` gains the nine ladder keys at s2color's values. `_init_properties` sets `self.margin_ladder` (name → rs, each through `_gsize`'s relative reader, an unreadable value keeping s2color's, silently). The class constant `_MARGINSTYLES` maps the 28 style names to `(left, right, bottom, top)` entries, each a ladder name, `0` or a point size (`("pt", 10.0)`), transcribed from Stata's files (E3) and pinned against the fixture's `_meta.marginstyles`. `SchemeParser.margin_sides(name)` returns the four rs values (pt sizes passed through as `("pt", v)`), or None for an unknown name. `plot_margin_sides` = `margin_sides(<margin twoway>)` (S21's `plot_margin_rs` stays, the left side of it, for S21's callers).
- **TR-47.3 `_dash_margin_sides(text, start, scheme)`** (new module function, pure): `start` is the current `[l, r, b, t]` in rs; returns `(new_sides, noted)`. Grammar (D-47c): the text stripped and capped at 2,000 characters; a style name → its four sides; exactly four numbers → l r b t; one or more `l|r|b|t` terms, each `[<blank>][+|-|=]#` (no sign is `=`), applied in order, repeats accumulating (measured `l+5 l+5`); a number is a finite float (`1e400`, `nan` and `inf` are not numbers). Anything else → `start` replaced by zeros and `noted` = the text (as typed, at most 80 characters), for `(note:  named style <text> not found in class margin, default attributes used)`. Points convert to rs as `pt / (min(W,H) in points) × 100` with W, H in inches as `_dash_plot_margin` reads them.
- **TR-47.4 `_dash_plot_margin(scheme, graph_opts, panels=1)`** (S21's; extended): starts from `scheme.plot_margin_sides`; reads the plotregion margin values with S38's tokeniser (`_dash_by_tokens` over `graph_opts["plotregion"]`, each name canonicalised by `_dash_subopt_canon(name, _dash_region_table())`, every `margin` entry in order as S38's Mata merge `_dash_rep_region` keeps them); applies `_dash_margin_sides` to each; prints each `noted` text once per graph through S06's channel (`_dash_emit_note`, keyed by graph and text through S06's once-per-build key, so the by() recomputation of TR-47.6 and a re-finish never print it again), in both modes from the same function; multiplies by f(panels) (D-47d); converts to frame fractions (left/right × min(W,H)/W, bottom/top × min(W,H)/H); applies D-47b; returns `{"x": (left, right), "y": (bottom, top)}`. Pure apart from the note; reads no figure.
- **TR-47.5 Padding and its inverse.** `_dash_padded_range(lo, hi, kind=None, reverse=False, margin=None)`: `margin` a float f means `(f, f)`; with `(s, e)`, F = span/(1 − s − e), and the start side gets s·F, the end side e·F (start = lo − s·F, end = hi + e·F; reversed: start = hi + s·F, end = lo − e·F; log in log10 space); `_dash_margin_f` stores the pair. `_dash_range_hull(rng, kind=None, margin=None)` inverts it exactly for any pair (D-47a). None keeps S21's legacy 5%.
- **TR-47.6 Finisher consumers** (S21's code, R11). `_dash_hull_ranges`, `_dash_finish_secondary_axes` and `_dash_share_by_scales` pass `fig._dash_margin[letter]` (now a pair) unchanged; `_dash_share_by_scales` recomputes it with `panels=len(figs)` as before. `_dash_axis_plan` writes `margin` as a two-number list and, per panel, `box` (the model index of the panel's inner box, −1 for none) with the box in `models`.
- **TR-47.7 The JS twin.** `_DASH_AXIS_FINISH_JS`'s `dash_axis_pad` and its inverse take `[s, e]` (a number still meaning both), line for line with TR-47.5; `dash_axis_finish` writes each panel's box `left`/`right` from the x hull and `bottom`/`top` from the y hull (min and max of the hull, in the axis's units: milliseconds on a date axis, data units on log) after it writes the ranges, and leaves a side whose axis held its range unchanged. No DOM, no `eval`, no BokehJS view internals (TR-21.11's rule).
- **TR-47.8 `_dash_inner_box(fig)`** (new module function): reads the plotregion inner sub-options (`istyle icolor ifcolor ilstyle ilcolor ilwidth ilpattern`) from `fig._dash_margin_args[1]` with `_dash_by_tokens` and `_dash_region_table()`'s canonical names, maps each to its outer name (`icolor` → `color`, …) and resolves fill and line by one call of `_dash_region_spec(<the mapped tokens>, "plotregion", <the inner base: fill and line None>, scheme, ref_in)`, so twoway's edit order, `none`, `%NN` and S43's bare forms come from S38's one reader (its `named` result is discarded here: the outer copy's names were reported by `_dash_apply_regions`); when none is given it returns None and adds nothing. Otherwise it creates once (tag `dash_inner_box`, `level="underlay"`, `fig.add_layout`) or updates a `BoxAnnotation` with `fill_color/fill_alpha/line_color/line_alpha/line_width/line_dash` from the resolution (a `none` fill or line → alpha 0) and edges from the figure's current x and y hulls (`_dash_range_hull` of the primary ranges with their margins; a DataRange1d axis leaves its edges None, the frame edge). It is called at the end of `_dash_hull_ranges` for that figure, so build, the served re-finish and `_dash_common_count_ticks`' shared by() ranges all update it. `ilalign()` stays named (S38, P1.20.5).
- **TR-47.9 Notes.** S38's not-drawn table is the BR-38.9 name set that `_dash_region_spec` tests for `named`; it becomes option-dependent: for `option == "plotregion"` it loses `margin` and the seven inner names drawn here (`istyle icolor ifcolor ilstyle ilcolor ilwidth ilpattern`; `ilalign`, `ishadestyle`, `iintensity`, `lalign`, `shadestyle`, `intensity`, `marginonly` stay named); `graphregion` `margin` and its inner names (`istyle icolor ifcolor ilstyle ilcolor ilwidth ilpattern ilalign`) stay in it or are added if S38 left them silent, named as typed (register P1.19.5) once per graph (P1.20.2, P1.20.3).
- **TR-47.10 Not edited.** `_make_figure_body` and the template (the stamps of TR-21.5 already carry `graph_opts` to every figure in both modes), `_dash_apply_scale_ranges` (D-47f), `_FILTER_JS` (A153), `_build_filter_widgets`, every mapper.
- **TR-47.11 Copy lists (R2 row S47).** Functions, after S44's `"_dash_ts_pair",` (S21's anchor chain): `"_dash_margin_sides", "_dash_inner_box",`. `SchemeParser` travels with its class; `_DASH_AXIS_FINISH_JS` is already copied.
- **TR-47.12 Maps.** Under S47's anchor of `test/function_test_map.py`: `_dash_inner_box` → `test/test_region_margins.py::TestTheInnerBox::test_probe`, `_dash_margin_sides` → `test/test_region_margins.py::TestTheMarginGrammar::test_form`, `SchemeParser.margin_sides` → `test/test_region_margins.py::TestTheSchemeLadder::test_styles`. No Stata program is added.
- **TR-47.13 Help** (R3: Region Styling Options). The margin rows (`margin(marginstyle)` with the grammar, copies that add, zero exact, the bound of D-47b, the unknown-name rule, by()), the inner box rows (the seven names, drawn at the axis hull), and one sentence that `graphregion(margin())` and the graphregion inner options are named, not drawn; lines at most 79 characters.
- **TR-47.14 Security (rule 1).** Margin text is parsed by a bounded, linear-time tokeniser into floats; only clamped numbers reach ranges, the plan JSON (`allow_nan=False`) and BoxAnnotation fields; colours reach Bokeh only through S38's reader; nothing reaches CSS or HTML; the note echoes at most 80 characters through S06's escaping.

## Boundaries

- **Batch partners:** S45 (dash.ado plot parser, mapper tails, S19's label helper) and S46 (`_generate_app_source`, `_dash_launch_app`, `__main__`, serve options, help Server Mode/Limits/Subcommands). S47 edits none of them.
- **Earlier sections, read only:** S38's region reader body and merge (S47 edits only its not-drawn table entries and calls the reader), S10's canon table (S38's region rows used as they are), S08's size resolver, S27/S35/S44's finisher hooks (kept in order).
- **Later:** S50 (`noextend` reads the margin pair); S52 (`add` after S47's names at S21's anchor); S53 (by() axes); S57.
- **Not this section's:** an exact outer graph margin (P2.53, graphregion `margin()` drawn); the graphregion inner box (Bokeh boxes clip to the frame, P1.20.3); by()'s own `plotregion()`/`graphregion()` (IR-9, S53/S58); `lalign()`/`ilalign()` (P1.20.5); twoway's drawing of `L+10`, three or five numbers (residual).
- **Never:** a hand patch of a scheme file or `scheme_truth.json`; `scripts/regen_option_surface.py` (IR-7).

## Stata truth

### `scripts/extract_margin_truth.do` → `test/fixtures/margin_truth.json`

S02's stanza with `<file>` its own name, then `adopath ++ "`repo'/"` and `global dash_nobrowser 1`; `_meta` in S21's form (`stata_version`, `born_date`, `dash_commit`, `extracted`, `units` "margin_rel = plot-region edge to curmin (or curmax) distance / min(canvas W, H)"), plus `marginstyles` (the 28 `margin-*.style` files' four sides, read as text from `c(sysdir_base)/style/`) and `ladders` (each of s2color, stcolor, economist's nine ladder values). The recorder is S21's `_ns_rec` form (`.Graph.plotregion1.{x,y}scale.{curmin,curmax}`, per by() panel `.Graph.graphs[k]`); the python block reads SVGs through `scripts/svg_truth.py` (`svg_document`, `svg_axis_extent`, `svg_plotregion`), never calls Stata, never uses `shell=True`, writes a backtick as `\x60`.

- **Probes** (`twoway scatter mpg weight, <opts>` on `sysuse auto`; under s2color unless named; each in a named log for its notes): `DEF`; `ZERO` `plotregion(margin(zero))`; `BOGUS` `margin(bogus)`; `L10` `margin(l+10)`; `LM5` `margin(l-5)`; `LEQ0` `margin(l=0)`; `LEQ10` `margin(l=10)`; `L5` `margin(l5)`; `L5L5` `margin(l+5 l+5)`; `LSP` `margin(l +10)`; `Q4` `margin(1 2 3 4)`; `NAMES.<n>` each of the 28 names; `COPY` `plotregion(margin(zero)) plotregion(margin(l+10))`; `COPYR` the reverse order; `MIX` `plotregion(margin(zero) color(red)) plotregion(mar(t+5))`; `XS` `xsize(10) ysize(3) plotregion(margin(l+10))`; `REV` `xscale(reverse) plotregion(margin(l+10))`; `LOG` `yscale(log) plotregion(margin(b+10))`; `TD` a `%td` x (`gen d = mdy(1,1,2000)+_n*30`, `format d %td`, `scatter mpg d, plotregion(margin(r+10))`); `Y2` `(scatter mpg weight) (scatter price weight, yaxis(2)), plotregion(margin(t+10))`; `BY_L10` `by(foreign) plotregion(margin(l+10))`; `BY_ZERO` `by(foreign) plotregion(margin(zero))`; `ECON_DEF`, `ECON_L10` under economist; `ST_L10` under stcolor; `CAPL` `margin(L+10)`; `Q3` `margin(1 2 3)`; `Q5` `margin(1 2 3 4 5)`; `I1` `plotregion(ifcolor(red))`; `I2` `icolor(red)`; `I3` `ilcolor(red) ilwidth(thick)`; `I4` `ifcolor(red%50) ilpattern(dash)`; `I5` `istyle(none) ifcolor(red)`; `I6` `ifcolor(red) margin(zero)`; `I7` `ifc(red) ilc(blue)`; `G1` `graphregion(margin(l+10))`; `G2` `graphregion(ifcolor(red))`.
- **Records:** per probe `rc`, `notes`, per axis and panel `curmin`, `curmax`, `margin_rel` for both sides (`lo`, `hi` in visual order), and for `I*` the inner rect (`x`, `y`, `w`, `h` in data units through the axis reading, `fill`, `fill_opacity`, `stroke`, `stroke_width`, `dash`). `BY_*` record `gmetric`.
- **Expected** (E4): `ZERO` and `BOGUS` both sides 0 (BOGUS with the note); `L10` left 0.122, others 0.022; `L5L5` = `L10`; `COPY` left 0.10, others 0; `COPYR` all 0; `Q4` 0.01 0.02 0.03 0.04; `I1` rect = the frame inset by 0.022.
- Run: `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_margin_truth.do"` (log `$S/extract_margin_truth.log`, about 80 exports). `git add -f test/fixtures/margin_truth.json`.

### Area cases, `test/test_twoway_option_parity.cscript` (R1; one contiguous run at the end of its last case block, after S45's RC run)

Header `// RM: plot-region margins and inner box (WP-30 P1.20b)`; live twoway and dash, rc and notes from named logs, `RM-nn PASS: …`.
- **RM-01** `plotregion(margin(bogus))`: rc 0 both; dash's note equals twoway's line.
- **RM-02** `plotregion(margin(zero))`, `margin(l+10)`, `mar(t-5)`, `m(1 2 3 4)`, `margin(10-pt)`: rc 0 both, no dash note.
- **RM-03** `plotregion(margin(zero) margin(l+10))` (one copy): r(198) both, twoway's `option margin() not allowed` (S38's refusal, checked here).
- **RM-04** `graphregion(margin(l+10))`, `graphregion(ifcolor(red) ilc(blue))`: rc 0 both; dash's region note names `margin()`, `ifcolor()`, `ilc()` as typed; no note names a plotregion margin or inner option.
- **RM-05** `plotregion(ifcolor(red) ilalign(inside))`: rc 0 both; dash names `ilalign()` only.

### The S47 block of `test/test_wp30_truth.cscript` (R1)

Helpers `_s47_*` directly above S01's `* ==== S47 P1.20b: Plot-region margin and inner box ====` header (a `python:` reader returning, per saved or served figure, the inner hulls with `_dash_range_hull` and the margin pair, and the BoxAnnotation fields; any Stata helper declares `version 19`). Cases report through `_w30_expect`/`_w30_done`, write only under `` `w30_work' `` and erase their pages and SVGs before the `S47 end` line (TR-01.10 item 4); run alone (`WP30_ONLY=S47`) the block prints its PASS lines and `ALL CHECKS PASSED`. Inside the stub:
- **RM-20** `ZERO`, `L10`, `COPY`, `Q4`, `ECON_L10`: dash's per-side `margin_rel` (from `_dash_plot_margin` × W/min(W,H)) equals the fixture's within 0.0005, and the page's frame fraction within 0.008 (A6), saved and served.
- **RM-21** `REV`, `LOG`, `TD`, `Y2`: the same.
- **RM-22** `BY_L10`, `BY_ZERO`: per panel, as the fixture (H-47.1 decided).
- **RM-23** `I1`-`I7`: the box's edges equal the axis hulls, its fill, alpha, line and dash equal the fixture's rect (colours lower-cased), saved and served.
- **RM-24** after a served move and a saved node move (`if price <= 7075.5`), `L10` and `I1`: margins and box follow the kept rows as twoway's `if` graph draws them.

## TDD test stubs

### Regression tests, new `test/test_region_margins.py` (red at the batch-16 base unless marked guard; 47-02)

Helpers reuse S21's `test_default_axes.py` `_figs(mode, …)`, `_inner`, `_saved_move`, `_served_move`; the fixture is loaded lazily inside fixture classes.
- Test: `…::TestTheMarginGrammar::test_form[<case>]` — `_dash_margin_sides` on every form of D-47c (names, four numbers, terms with and without blanks and signs, repeats, `#-pt`, unknown, `L+10`, three and five numbers, `1;x:y`, a 3,000-character text) against literal expectations. Red: AttributeError.
- Test: `…::TestThePlotMargin::test_probe[<fixture probe>]` — `_dash_plot_margin` × W/min(W,H) equals the fixture's `margin_rel` per side within 0.0005 (BY probes after 47-01 settles H-47.1). Red: scalar return.
- Test: `…::TestTheHelpers::test_padded_range_takes_a_pair` and `::test_range_hull_inverts_any_pair` — f/(1−s−e) arithmetic, exact inverse (1e-12) for 200 seeded pairs including negatives, both kinds, reversed. Red: TypeError.
- Test: `…::TestTheHelpers::test_bounds` — sides clamped to [−0.45, 0.45], sum ≤ 0.9. Red.
- Test: `…::TestTheRangesTakeTheMargin::test_probe[ZERO|L10|COPY|Q4|REV|LOG|TD|Y2-saved|served]` — the inner hull with the pair margin equals the data hull ∪ ticks (S21's rule), and `rng._dash_margin_f` equals `_dash_plot_margin(...)[letter]`. Red: margins ignored.
- Test: `…::TestAfterAFilterMove::test_margin_holds[L10|ZERO-saved|served]` and `::test_reset_returns_to_it[saved|served]`. Red.
- Test: `…::TestByPanels::test_probe[BY_L10|BY_ZERO-saved|served]`. Red.
- Test: `…::TestTheInnerBox::test_probe[I1..I7-saved|served]` — one BoxAnnotation tagged `dash_inner_box`, edges at the hulls, styling as the fixture. Red: no box.
- Test: `…::TestTheInnerBox::test_follows_a_move[saved|served]` and `::test_shared_by_ranges[saved|served]`. Red.
- Test: `…::TestNoBoxWithoutInnerOptions::test_no_annotation[saved|served]` — guard (no box at the base or after).
- Test: `…::TestTheNotes::test_graphregion_named[saved|served]`, `::test_plotregion_not_named[saved|served]`, `::test_unknown_margin_noted_once[saved|served]` (S06's counting helper). Red for the plotregion and unknown cases.
- Test: `…::TestTheSchemeLadder::test_styles` (`_MARGINSTYLES` equals `_meta.marginstyles`), `::test_every_shipped_scheme_carries_it[<26>]`, `::test_a_scheme_override_changes_the_margin` (a user scheme with `gsize medsmmargin relative5`). Red.
- Test: `…::TestHostileMargins::test_bounded_and_fast[<texts>]` (`"l+1e308"`, `"l-1e308"`, `"x"*100000`, `"l+" * 5000 + "1"`, `"nan nan nan nan"`): finite ranges, under 0.1 s each, a note for the unparseable. Red: AttributeError.
- Test: `test/test_natscale_js.py::TestJsPaddingEqualsPython::test_padded_ranges_with_sides` and `::TestJsFinishEqualsPython::test_the_box_follows` (2,000 seeded pairs; 200 moves with I1). Red.
- `test/test_mode_parity.py` CORPUS, under `# WP-30 P1.20b: plot-region margin and inner box`: `margin l+10`, `margin zero`, `inner box ifcolor`; MOVE_CORPUS `margin and box after a range move` (red).

### Pinned tests to flip (R9; re-measured, never trusted)

E5's list, each flipped in place with a `Flipped:` line and never deleted:
- `test/test_default_axes.py::TestPlotregionMarginIsStillIgnored::test_margin_zero_changes_nothing_yet[saved|served]`: its body now asserts that `plotregion(margin(zero))` puts the data hull on the frame (`rng._dash_margin_f == (0.0, 0.0)`), docstring "twoway draws margin(zero) with no margin (P1.20b)"; the node name is kept.
- `test_default_axes.py::TestTheHelpers::test_the_plot_margin[...]` expects pairs (stcolor `{"x": (0.0132, 0.0132), "y": (0.022, 0.022)}`), and `::test_the_by_factor[...]` reads `["y"][0] / 0.022`.
- `::test_padded_range_takes_a_margin`, `::test_range_hull_inverts_any_margin` and `test_natscale_js.py`'s scalar cases keep passing (a float is still accepted) and are not flipped unless red.
- S38's not-drawn assertions for the plotregion `margin` and inner names (in `test/test_region_options.py`) assert drawn and not named.
- `test/test_varlist_expansion.py` `_SINGLE_Y_BASELINE_SHA256` re-derived (R10).

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Grammar, bounds, ladder | pytest `TestTheMarginGrammar`, `TestTheHelpers`, `TestTheSchemeLadder`, `TestHostileMargins` | literals; `margin_truth.json` | n/a |
| Margins against twoway | pytest `TestThePlotMargin`, `TestTheRangesTakeTheMargin`, `TestByPanels`; truth RM-20..RM-22 | `margin_truth.json` | yes |
| Inner box | pytest `TestTheInnerBox`, `TestNoBoxWithoutInnerOptions`; truth RM-23 | fixture | yes |
| After moves, reset | pytest `TestAfterAFilterMove`, `TestTheInnerBox::test_follows_a_move`; truth RM-24; `test_mode_parity.py` MOVE_CORPUS | auto | saved (node), served |
| JS twin | `test_natscale_js.py` pair and box cases | seeded | JS against Python |
| Notes and refusals | pytest `TestTheNotes`; cscript RM-01..RM-05 | live twoway | yes |
| Regeneration | `test_scheme_fidelity.py` (unedited), the probe-by-probe diff of 47-04 | `scheme_truth.json` | n/a |
| Budgets | S21's `TestTheRefinishBudget` and the 100-panel chrome test (A9) still pass | — | both |

**Acceptance criteria.**
- **AC-47.1** (BR-47.1, BR-47.2) RM-20..RM-22 and RM-24 PASS; `TestThePlotMargin`, `TestTheRangesTakeTheMargin`, `TestAfterAFilterMove` and `TestByPanels` pass in both modes.
- **AC-47.2** (BR-47.3) `TestTheMarginGrammar`, `TestHostileMargins` and RM-01 pass.
- **AC-47.3** (BR-47.4) `TestTheInnerBox`, RM-23 and `TestNoBoxWithoutInnerOptions` pass; the node tests are not skipped.
- **AC-47.4** (BR-47.5) `TestTheNotes`, RM-04 and RM-05 pass.
- **AC-47.5** (BR-47.6) `TestTheSchemeLadder` passes; the 26 files and `scheme_truth.json` come from one extractor run, every pre-existing probe's records unchanged outside `_meta`.
- **AC-47.6** S21's budgets (A9) pass; `test_mode_parity.py` passes with `ALLOWED`/`_MUST_WARN` untouched; every flip carries a `Flipped:` line; the full suite reports 0 failed; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 47-01 to 47-11 form one commit, made by 47-11 on `wp30-s47` with the subject `Draw the plot-region margin and inner box as twoway does (WP-30 P1.20b)`. `<scratch>` and `$SLOT` as in section 45; `$S` is `<scratch>/s47` (47-01 runs `mkdir -p "$S"`; S45, S46 and S47 run in parallel, so no log or slot directory is shared); `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s47`; cscripts through the driver with `WP30_ONLY=S47`.

<task type="auto" id="47-01">
  <name>Write and run the margin extractor</name>
  <files>scripts/extract_margin_truth.do</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "<scratch>/batch-16-base.txt"` and the branch is `wp30-s47`; stop otherwise. `mkdir -p "$S"`. Check the prefix is free: `grep -lE '(^|[^A-Za-z0-9_])RM-[0-9]' "$WT"/test/*.cscript "$WT"/test/*.py "$WT"/test/*.do` prints nothing. Create `scripts/extract_margin_truth.do` as "Stata truth" describes and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_margin_truth.do"`; it writes `test/fixtures/margin_truth.json`. Read `BY_L10` and `BY_ZERO` against S21's f(2) = 0.85 and write in `$S/47-notes.txt` whether H-47.1 holds (the BY panel's left `margin_rel` equals (0.022 + 0.10) × 0.85 within 0.0005); record also `LEQ0`'s left `margin_rel` (D-47c's `=` reading) and whether it is 0 within 0.0005. Check `~/.stata19/console/stata19.rc` still holds `python_exec`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/margin_truth.json')); m=d['_meta']; p=d['probes']; print(all(k in m for k in ('stata_version','born_date','dash_commit','extracted')), len(m['marginstyles']), round(p['L10']['x']['margin_rel']['lo'],3), round(p['ZERO']['y']['margin_rel']['hi'],3))"` prints `True 28 0.122 0.0`.]]></verify>
  <done>The twoway margin and inner-box fixture existed, with H-47.1 and the l=0 reading decided and recorded.</done>
</task>

<task type="auto" id="47-02">
  <name>Write the margin regression tests</name>
  <files>test/test_region_margins.py, test/test_natscale_js.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Create `test/test_region_margins.py` with every stub of "TDD test stubs" (new names as `dr._dash_margin_sides`, `dr._dash_inner_box`, `dr.SchemeParser.margin_sides`, so they fail with AttributeError now; `TestByPanels` written to the rule 47-01 recorded). Add the two JS cases to `test/test_natscale_js.py` under S21's classes, and the CORPUS and MOVE_CORPUS cases to `test/test_mode_parity.py` after any earlier section's cases. Run `python3 -m pytest test/test_region_margins.py test/test_natscale_js.py -q -n 6 -p no:cacheprovider -rf > "$S/47-new.log" 2>&1` and the parity file with `-k "P1.20b"` appended. Write `$S/47-P1.20b-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)". Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/47-new.log"` is at least 40; `grep -c "TestNoBoxWithoutInnerOptions" "$S/47-P1.20b-failure.txt"` prints 1 (under the guards); `git -C "$WT" diff --name-only -- dash_render.py dash.sthlp` prints nothing.]]></verify>
  <done>Every pytest and JS regression test for margins and the inner box was shown failing on the unmodified tree, with the guards listed apart.</done>
</task>

<task type="auto" id="47-03">
  <name>Write the area and truth cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    In `test/test_twoway_option_parity.cscript`, as one contiguous run at the end of its last case block (after S45's RC run), add the header `// RM: plot-region margins and inner box (WP-30 P1.20b)` and RM-01..RM-05. In `test/test_wp30_truth.cscript` put the `_s47_*` helpers directly above S01's `* ==== S47 P1.20b: …` header and RM-20..RM-24 between its start and end lines. Run both through the driver on the unmodified shipped files and append every `RM-nn FAIL` line to `$S/47-P1.20b-failure.txt` (RM-02, RM-03 and RM-05 may pass as guards). Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "RM-(01|04) FAIL" "$S/run_test_twoway_option_parity.log"` prints 2; `grep -cE "RM-2[0-4] FAIL" "$S/run_test_wp30_truth.log"` prints 5.]]></verify>
  <done>The live twoway comparisons for notes, margins and the inner box were in place and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="47-04">
  <name>Regenerate schemes with the ladder</name>
  <files>scripts/extract_scheme_truth.py, test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    Apply TR-47.1 in `scripts/extract_scheme_truth.py` (the nine ladder keys resolved with provenance, `margin_ladder` recorded, the directives through `expected_directives`). Save the pre-run fixture to `$S/47-scheme-before.json`, run `python3 scripts/extract_scheme_truth.py` in `$WT` (it rewrites the 26 `dash-*.scheme` files, generated, and `test/fixtures/scheme_truth.json`), then compare every pre-existing probe's records outside `_meta` with the saved copy: only the nine keys and their provenance may differ (R7). Never patch a generated file.
  ]]></action>
  <verify><![CDATA[`grep -c '^gsize medsmmargin' "$WT"/dash-*.scheme | grep -c ':1$'` prints 26; a second extractor run leaves `git -C "$WT" status --porcelain -- 'dash-*.scheme' test/fixtures/scheme_truth.json` unchanged; the probe-by-probe comparison prints no difference outside the nine keys; `python3 -m pytest test/test_scheme_fidelity.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The 26 shipped schemes and the scheme fixture carried Stata's margin ladder from one extractor run, nothing else changed.</done>
</task>

<task type="auto" id="47-05">
  <name>Read the ladder and the grammar</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-47.2 (`_FALLBACK_PROPS`, `margin_ladder`, `SchemeParser._MARGINSTYLES`, `margin_sides`, `plot_margin_sides`) and TR-47.3 (`_dash_margin_sides` beside S21's `_dash_plot_margin`, with a docstring citing E3 and D-47c), and add `"_dash_margin_sides",` to the functions tuple after S44's `"_dash_ts_pair",` (TR-47.11).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_region_margins.py -q -n 6 -p no:cacheprovider -k "TestTheMarginGrammar or TestTheSchemeLadder or TestHostileMargins"` passes; `python3 -m pytest test/test_scheme_fidelity.py test/test_default_axes.py -q -n 6 -p no:cacheprovider -k "Scheme"` reports 0 failed.]]></verify>
  <done>dash read each scheme's margin ladder and parsed every margin form twoway documents, bounded and in linear time.</done>
</task>

<task type="auto" id="47-06">
  <name>Pad each side by its margin</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_padded_range` is CRITICAL (10 impacted) and list the 16.0 risks of `_dash_plot_margin`, `_dash_hull_ranges` and `_dash_share_by_scales`; S47 is batch 16's only finisher editor (R11). Apply TR-47.4 (`_dash_plot_margin` per side, S38's tokeniser, the notes, f(panels) per 47-01's rule, D-47b), TR-47.5 (`_dash_padded_range` and `_dash_range_hull` with pairs, floats still accepted) and TR-47.6 (the consumers pass pairs; `_dash_axis_plan` writes `margin` as a list). Edit no other function.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_region_margins.py -q -n 6 -p no:cacheprovider -k "TestThePlotMargin or TestTheHelpers or TestTheRangesTakeTheMargin and served or TestByPanels and served or TestTheNotes"` passes; `python3 -m pytest test/test_default_axes.py test/test_by_scales.py test/test_axis_extents.py -q -n 6 -p no:cacheprovider` reports 0 failed except E5's S21 pins (flipped by 47-09).]]></verify>
  <done>Every axis range of both modes took the plot-region margin per side, from the scheme and from each plotregion copy in order, within twoway's tolerance.</done>
</task>

<task type="auto" id="47-07">
  <name>Port the sides to the JS twin</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-47.7 to `_DASH_AXIS_FINISH_JS`: `dash_axis_pad` and its inverse take a pair (a number meaning both), line for line with TR-47.5; `dash_axis_finish` writes each panel's box edges after its ranges. Keep TR-21.11's rules (no DOM, no eval, no view internals, writes only when values change). Do not edit `_FILTER_JS` (A153).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_natscale_js.py -q -n 6 -p no:cacheprovider` passes, the pair case included; `python3 -m pytest test/test_region_margins.py -q -n 6 -p no:cacheprovider -k "saved and (TestTheRangesTakeTheMargin or TestAfterAFilterMove or TestByPanels)"` passes, the node tests not skipped.]]></verify>
  <done>The saved page's re-finish padded each side as Python does and kept the margin after every move.</done>
</task>

<task type="auto" id="47-08">
  <name>Draw the inner box and fix notes</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-47.8 (`_dash_inner_box` beside `_dash_margin_sides`, called at the end of `_dash_hull_ranges`; the plan's `box` index from TR-47.6) and TR-47.9 (S38's not-drawn table: plotregion `margin` and the seven plotregion inner names out; graphregion `margin` and its inner names in, as typed). Add `"_dash_inner_box",` after `"_dash_margin_sides",` in the functions tuple (TR-47.11). If `_make_figure_body` must change, stop and report under R12 first (CRITICAL).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_region_margins.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed except E5's pins; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_region_options.py -q -n 6 -p no:cacheprovider` reports 0 failed except S38's not-drawn pins of E5.]]></verify>
  <done>The plotregion inner options drew one box at the axis hull in both modes, following it after moves, and only the graphregion margin and inner options were named.</done>
</task>

<task type="auto" id="47-09">
  <name>Flip the pins and the digest</name>
  <files>test/test_default_axes.py, test/test_region_options.py, test/test_varlist_expansion.py</files>
  <action><![CDATA[
    Re-measure E5 on this tree and flip in place, each with a comment "Flipped (WP-30 P1.20b): <old> was wrong because twoway draws plotregion(margin()) and the inner box (margin_truth.json)": S21's `TestPlotregionMarginIsStillIgnored::test_margin_zero_changes_nothing_yet` body (zero margin puts the hull on the frame), `test_the_plot_margin` and `test_the_by_factor` to pairs; S38's not-drawn assertions for plotregion margin and inner names; `_SINGLE_Y_BASELINE_SHA256` re-derived with `# <old> -> <new>: P1.20b the axis plan carries margin pairs` (R10). Write one `Flipped:` line per node to `$S/47-flips.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_default_axes.py test/test_region_options.py test/test_varlist_expansion.py test/test_by_scales.py -q -n 6 -p no:cacheprovider` reports 0 failed; through the driver `test_twoway_option_parity.cscript` prints RM-01..RM-05 PASS and `test_wp30_truth.cscript` RM-20..RM-24 PASS.]]></verify>
  <done>Every pin that asserted margins ignored or plotregion inner options named asserted what twoway draws, with the reason recorded.</done>
</task>

<task type="auto" id="47-10">
  <name>Document margins and map helpers</name>
  <files>dash.sthlp, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-47.13 in Region Styling Options (find the places by their text; edit no other paragraph, R3; lines at most 79 characters; no tool or vendor name) and TR-47.12 (the three entries under S47's anchor, alphabetically). Run S21's budget tests (`TestTheRefinishBudget`, the 100-panel chrome test when Chrome is present) and record their times in `$S/47-notes.txt` (A9).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py test/test_help_conformance.py test/test_region_margins.py -q -n 6 -p no:cacheprovider` reports 0 failed; `awk 'length > 79' "$WT/dash.sthlp" | grep -ci margin` prints 0; `python3 -m pytest test/test_default_axes.py -q -n0 -p no:cacheprovider -k "TestTheRefinishBudget"` passes.]]></verify>
  <done>The help documented plot-region margins, the inner box and the named graphregion forms, the helpers were mapped, and the re-finish stayed within its budgets.</done>
</task>

<task type="auto" id="47-11">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.20b"]`. Close that BUGS.md entry in place (`- [x]`, the Resolution of Notes). Delete the `"P1.20b"` key line of `WP30_OPEN`. Replace the `<!-- WP-30 P1.20b -->` marker in place with Notes' line. Run `test_tracking_documents.py`, `test_fixtures_are_committed.py`, `test_cscript_hygiene.py`, `test_region_margins.py`, `test_natscale_js.py` and `test_mode_parity.py` with `-n 6`, and both cscripts through the driver. `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"<scratch>/full_suite_queue.sh" "$WT" "$S/47-full.log"` in the background, read when `exit=` appears. Stage exactly the files 47-01 to 47-11 changed and the 26 regenerated scheme files, with `git add -f test/fixtures/margin_truth.json test/fixtures/scheme_truth.json`; check `git -C "$WT" diff --cached --name-only` (G6). Write `$S/47-message.txt` in Notes' form, check G7, confirm the branch, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/47-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.20b -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.20b": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.20b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.20b was closed naming existing tests, its marker carried the measured old and new behaviour, and one green commit on wp30-s47 was ready to land last in batch 16.</done>
</task>

## Section completion criteria

- `plotregion(margin())` sets each side's margin as twoway does, over the scheme and earlier copies, in both modes, after moves, on reset, under by(), on y2/x2, reversed, log and date axes (RM-20..RM-22, RM-24; `TestThePlotMargin`, `TestTheRangesTakeTheMargin`, `TestAfterAFilterMove`, `TestByPanels`).
- The plotregion inner box is one BoxAnnotation at the hull, styled as twoway styles it, following moves (RM-23; `TestTheInnerBox`); none without inner options.
- Unknown margins are noted and zero; hostile ones bounded; graphregion margin and inner options named (RM-01, RM-04; `TestTheNotes`, `TestHostileMargins`).
- The 26 schemes and `scheme_truth.json` carry the ladder from one extractor run; `margin_truth.json` is generated, stamped and committed with `-f`.
- S21's budgets hold; every pin is flipped with its reason; one green commit `(WP-30 P1.20b)` on `wp30-s47` closes the entry, deletes its key and replaces the marker, and lands last in batch 16.

## Notes

- **H-47.1 and `l=0`.** This pass measured `margin(l=0)` with the first marker only (Overview); the side's own `margin_rel` is recorded by 47-01. If `LEQ0`'s left side is not 0 within 0.0005, dash still implements `=` as the help states, and the measured value is written into the Resolution's residual, never patched into the model by guess. by() scaling (D-47d) follows 47-01's recorded rule.
- **R2 table (S47 row "Constants —").** The marginstyle table is `SchemeParser._MARGINSTYLES`, a class constant that travels with its class, so no constants entry is needed; the two functions go after S44's `"_dash_ts_pair",`.
- **R10 digest (not in R10's expected list).** The axis plan's `margin` becomes a list on every page with a plan, so `_SINGLE_Y_BASELINE_SHA256` moves; 47-09 re-derives it and the merger re-derives it on the merged tree (R10's rule for any section whose commit changes the single-y page).
- **python_exec hazard.** Check `~/.stata19/console/stata19.rc` after each slot run; a SKIP is not a pass.
- **Merge rules.** R1: RM-01..RM-05 as one run after S45's RC run in `test_twoway_option_parity.cscript`; RM-20..RM-24 in S47's stub, helpers above its header. R2: TR-47.11. R3: Region Styling Options (S38's paragraph kept, S47's rows added). R4/R5: the `P1.20b` marker, entry and key. R7: one new fixture and extractor; the regeneration by 47-04's run only, and on a conflict the merger re-runs `scripts/extract_scheme_truth.py` on the merged tree. R8: CORPUS/MOVE_CORPUS appended. R9: E5's flips. R10: the digest. R11: S47 is batch 16's only finisher editor. R12: S47 does not edit `_make_figure_body` or `_generate_app_source`.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `_dash_padded_range`, `_dash_range_hull`, `_dash_plot_margin`, `_dash_hull_ranges`, `_dash_share_by_scales`, `_dash_finish_secondary_axes`, `_dash_axis_plan`, `_dash_margin_sides`, `_dash_inner_box`, `SchemeParser._init_properties`, `SchemeParser.margin_sides`, `_dash_region_spec` (its named set), the extractor's symbols and test symbols.
- **Commit message.** Subject as in "Commit boundary". Body: `$S/47-P1.20b-failure.txt`; the measured defect (Overview's block); what changed (TR-47.1-TR-47.13, both modes); 47-01's H-47.1 and `l=0` findings; then `Regression: test/test_region_margins.py::<Class>::<test> -- failed at <base sha> with <text>` per node, `test/test_twoway_option_parity.cscript RM-01`, `test/test_wp30_truth.cscript RM-20`; the `Flipped:` lines of `$S/47-flips.txt`; `Fixture: test/fixtures/margin_truth.json (scripts/extract_margin_truth.do)`; `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`; `BUGS.md: "<WP30_OPEN["P1.20b"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.20b). plotregion(margin()) sets the plot-region margin per side by twoway's marginstyle grammar (dash_render.py _dash_margin_sides: the 28 style names, four numbers, l/r/b/t terms with + - =, points), applied in order over the scheme's margin twoway and over earlier copies, through _dash_plot_margin and _dash_padded_range with per-side fractions (zero exact, others within 0.8% of the width), in the saved page and the served app, after every filter move and under by(); an unknown margin is noted in twoway's words and drawn as zero; the plotregion inner options draw one inner box at the axis hull (_dash_inner_box), moved by the re-finish in both modes; graphregion(margin()) and the graphregion inner options are named, not drawn; the 26 shipped schemes carry Stata's margin ladder. Pinned by test/test_region_margins.py::TestThePlotMargin::test_probe, test/test_region_margins.py::TestAfterAFilterMove::test_margin_holds, test/test_region_margins.py::TestTheInnerBox::test_probe, test/test_twoway_option_parity.cscript RM-01, test/test_wp30_truth.cscript RM-20; fixture test/fixtures/margin_truth.json. Residual, deferred (WP-30): graphregion(margin()) is not drawn (P2.53); the graphregion inner box is not drawn (Bokeh boxes clip to the frame); twoway's drawing of margin(L+10) and of three or five numbers is not reproduced (drawn as zero with the note).
  ```
- **CHANGELOG line** (replaces the marker in place, in the WP-30 group of `### Results that change`):

  ```
  - `plotregion(margin())` and the plot region's inner box are drawn: `dash scatter mpg weight, plotregion(margin(zero))` kept a 2.2% margin and `plotregion(margin(l+10))` changed nothing, with no note; now `margin(zero)` puts the data on the frame and `margin(l+10)` adds 10% of the graph's smaller side on the left (0.122 of it in all), copies add as in twoway, an unknown margin is noted and drawn as zero, `plotregion(ifcolor(red))` shades the inner plot region, and `graphregion(margin())` and the graphregion inner options are named as not drawn. (WP-30, P1.20b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md B18** (B18-a): closed by `<sha>`; B18 closes when S38's entry is also closed. **AUDIT-66** (TWOWAY_COVERAGE_AUDIT.md:141): the margin half closed by `<sha>`.
  - **P2.53** (graphregion margin) and the graphregion inner box stay filed; **new P2 row:** twoway's drawing of `margin(L+10)`, `margin(1 2 3)` and `margin(1 2 3 4 5)`.
  - **AGENTS.md invariant:** "a plot-region margin is a per-side frame-fraction pair from `_dash_plot_margin` only; ranges are padded only by `_dash_padded_range` and its JS twin; the inner box is written only by `_dash_inner_box` and `dash_axis_finish`."
  - **Unverified:** Stata 14-18.5 (not run, M2); D-47d if 47-01 found the by() rule differs (then stated in the commit body).
