# Section 44-03: Scales: off fill, transform words refused, contradictions, log edges, empty minmax

> Part of: WP-44 (Axes, audit package 9) · Items: AX-7, AX-9, AX-10, AX-11, MS-14, DG-13 · Risk: red · Batch: 44.3 · Depends on: 44-02 · Blocks: none (WE) · Tasks: 13, 6 commits · Case-id prefix: Q4403

**Executed 07nov2026 on s3-bugs** (commits 55726b5 AX-7, 852a502 AX-9, 67405fd AX-10, fc8eb54 AX-11, 5b0d7e7 MS-14, f391788 DG-13; fixture test/fixtures/axis_scale_truth.json). Where the work departs from the text below:
- D-44-03.a: an alpha of 0 drops the space (BokehJS measures text only while Text.doit, color set and alpha not 0), so an off fill axis's labels and title take the clear colour `#00000000`, set by `_dash_clear_off_fill` at the start of `_dash_finish_count_ticks`, after every other label colour.
- AX-9: one case, Q4403-2, holds every transform-word probe; Q4403-3 and Q4403-4 are not used. The measured across-copy rule is the last transform word of the merged value (a later `log` clears `logit`). The refusal runs after the draw-time checks, so `-syntax-`'s own refusals come first.
- AX-10: twoway's `-syntax-` binds a no form given twice as one and a second `log` as `log1m` (measured `ax10_*`), which `_dash_scale_exclusive` copies. It runs in `_dash_axreq_add`, not `_dash_rep_reduce`.
- AX-11: under `ylabel(#5)` twoway also writes a 0 label off its scale; a log axis cannot place it, so it is part of the documented picture (Differences item 20).
- MS-14 passed at the 44.3 base and failed at 090d928: closed as a pin, no code.
- DG-13: the empty minmax labels are set when the page is built (a graph empty then stays empty); a graph moved to no row draws no minmax label in either mode, filed as its own open BUGS.md entry (S3). The span refusal is checked when the page is built, so Q4403-12's rows build a page.

## Overview

**What is wrong today.**

- **AX-7.** "yscale(off fill) is drawn as off; twoway keeps the axis's space" (audit :449). `fillspace` is in `_DASH_SCALE_LOOK_SUBOPTS` (dash_render.py:45863-45869) and never read: `_dash_scale_look` (:56719-56745) has no `fill` key, and `_dash_apply_scale_look` sets `axis_obj.visible = False` for `off` (:42837-42838). twoway C10 (`off fill`) puts the x label 2,000 at x=936.39, C11 (`off`) at 557.38 (appendix :1232-1237; `_gs_parse_and_log_axoptions.ado:125-130` sets `fill_if_undrawn`).
- **AX-9 (sil:SD-5).** "xscale/yscale atanh, logit, log1m and style() are named and drawn linear" (audit :455). Re-measured 07nov2026 (StataNow 19 console, probes run through scripts/stata_slot.sh): twoway's parser takes the three words (`_gs_parse_and_log_axoptions.ado:18-23`; axis_scale_options.sthlp documents only `log`), but every graph that leaves `atanh`, `logit` or `log1m` (abbreviation `log1`) on an axis fails with `unrecognized command` r(199): `xscale(atanh)`, `yscale(logit)`, `yscale(alt atanh)`, `tscale(atanh)` on tsline, `zscale(atanh)` on contour, `zscale(logit)` with colorvar(), and across copies (`yscale(log) yscale(logit)`). `yscale(log1m) yscale(nolog1m)` and the `no` forms alone (`noatanh`, `nologit`) draw the plain graph (rc 0). The audit's C12-C14 pictures do not reproduce. dash takes every form with `(note:  dash: yscale() sub-option(s) not implemented and ignored: atanh)` and rc 0, the `no` forms too. `yscale(style(vertical_nogrid))` is rc 0 in twoway and removes the grid (C17); dash notes it as ignored. **Maintainer ruling 07nov2026 (D75):** Stata's scales are linear or log (the `log` sub-option); dash does not allow atanh, logit or log1m on xscale(), yscale(), tscale() or zscale().
- **AX-10.** "Contradictory transforms in one copy (log nolog, atanh log) are accepted; twoway refuses r(198)" (audit :458). twoway runs `opts_exclusive "\`transform'"` over `nolog log noatanh atanh nologit logit nolog1m log1m` within one copy (`_gs_parse_and_log_axoptions.ado:35-39`): F1 "only one of options nolog or log is allowed", F8 "only one of options log or atanh is allowed". Across copies `yscale(log) yscale(nolog)` is rc 0 and linear (C16), and dash matches.
- **AX-11.** "A log axis over data with non-positive values is ticked over positive values only (twoway's whole drawing is degenerate there)" (audit :461). `_dash_layer_extent` (:46078) counts "positive ones on log" (:46092, :46120); twoway C20/G6 ticks 10 20 (natscale over all finite values, ticks at or below 0 dropped), dash 5 10 15; twoway piles the 60 non-positive points on the bottom edge and squashes the rest (appendix :1256-1261).
- **MS-14.** "xscale(range()) on a log axis adds a tick at the range end" (audit :473). `_dash_finish_count_ticks` joins range() values to the tick range unless the axis is a default date axis (:47750-47767); 34-03 (AX-1) restricts that join to `#N` and by() axes on numeric and log axes, which may already close this item at the WP-44 base.
- **DG-13 (DG-11).** "ylabel(minmax) on an empty scale draws Bokeh's default ticks; data spanning about ±8e307 give an OverflowError traceback (twoway gives r(199))" (audit :497). The minmax branch sets a `FixedTicker` only `if len(vals)` (:42330-42341), so the empty 0-1 placeholder keeps Bokeh's ticker; twoway labels `-1.e+300` and `1.e+300` (S07). `_dash_natscale_ticks` computes `d = m * 10.0 ** z` (:40318-40322) with `z_hi = ceil(log10(1.6e308)) + 1 = 310`, and `10.0 ** 310` raises before any finiteness check; twoway itself fails r(199) (X06).

**After this section**, in both modes and after every filter move: `off fill` keeps the axis's space; atanh, logit and log1m on any scale option are refused as twoway's graph fails on them (`unrecognized command`, r(199)), the `no` forms alone are taken silently, and `style()` reads Stata's axis style files; contradictory transforms in one copy are refused in twoway's words; a log axis over non-positive data is ticked as twoway ticks it; range() on a log axis adds no end tick; minmax on an empty scale writes twoway's two labels; data whose span overflows are refused with twoway's rc and line, never a traceback.

**Why one section.** All six sit in the xscale()/yscale() reader (`_dash_scale_spec`, `_dash_scale_look`), the hull and log tick code and the axis finisher (`_DASH_AXIS_FINISH_JS`); the index makes 44-03 batch 44.3's single editor of those (R11, JS = yes).

**Test order and commit rule.** Six commits in the manifest's order `(WP-44 AX-7)`, `(WP-44 AX-9)`, `(WP-44 AX-10)`, `(WP-44 AX-11)`, `(WP-44 MS-14)`, `(WP-44 DG-13)`. 44-03-01 writes the extract script (all items), runs it, and writes only AX-7's regression tests and block; saved failure; no commit. Each item: failing tests saved, then fix + flips + tracking in one commit.

### Section decisions (binding on the executor)

- **D-44-03.a off fill keeps the space, invisibly.** `_dash_scale_look` returns `"fill": True` when the last of `fillspace`/`nofillspace` in the copy is `fillspace`; `_dash_apply_scale_look`, for `off` with `fill` (and not by_graph), leaves `axis_obj.visible` True and sets `axis_line_color = None`, `major_tick_line_color = None`, `minor_tick_line_color = None`, `major_label_text_alpha = 0.0`, `axis_label_text_alpha = 0.0` (the labels keep their layout extent, so the border is what twoway keeps). `fill` without `off` stays the plain axis (dash.sthlp:4617-4618, which is true without off). Labels written by later code (filters, the finisher) never reset these alphas: the finisher writes tickers and overrides only (re-read `dash_axis_finish` to confirm; a node test pins it).
- **D-44-03.b atanh, logit and log1m are refused, never drawn (D75).** No scale transform is drawn: no CustomJSTransform, no glyph walk, no new columns. New Mata `real scalar _dash_scale_untransformable(string colvector copies)`: walks the copies of one scale key in the order typed, each copy's words canonicalised through `_dash_so_canon(<word>, "axscale")`; `atanh`, `logit` and `log1m` each set their own flag and their `no` form clears it (expected; the fixture's across-copy probes `ax9.log_then_logit`, `ax9.logit_then_log` and `ax9.log1m_then_no` are the truth, and a later `log` clears a flag only if `ax9.logit_then_log` is rc 0); returns 1 when any flag is set after the last copy. It runs in `_dash_rep_reduce`'s first loop beside D-44-03.d's exclusivity check, over the same keys (`xscale yscale xscale2 yscale2 tscale tscale2 zscale`, the axis-3..9 scale keys and `axis(#)` copies), after every copy's exclusivity check, so `yscale(atanh log)` is still r(198) first as in twoway; it sets the caller's local `_rp_trans`, and dash.ado's caller at :10993 refuses with `_dash_say("err", "unrecognized command")` and `exit 199` (twoway's line and rc, from the fixture's `ax9.*` rows) after the `_rp_excl` refusal. A graph with one copy reaches the same loop (D-44-03.d's confirmation). The refusal happens before Python, so saved and served agree by construction. The `no` forms draw the plain graph in twoway and are taken silently: `_DASH_SCALE_SUBOPTS` gains `noatanh`, `nologit` and `nolog1m`, so no "ignored" note names them (`nolog` stays 49-02's, Boundaries). `_DASH_AXSCALE_SUBOPT_TABLE` and the Mata `axscale` rows keep the six words: they are twoway's parser table and the canon for abbreviations (`log1`).
- **D-44-03.c style() on a scale reads axisstyle files.** `_STYLE_FILE_CLASSES` gains `"axisstyle"` (after 44-02's three; the class-tuple pin moves again, Evidence); `SchemeParser.axis_style_tokens("axisstyle", name)` (44-02's resolver) maps `draw_major_grid no` -> `nogrid` on the axis's label option, `linestyle scheme <k>` -> `lstyle(<k>)`, `extend_low/high` -> `noextend`/`extend`, `majorstyle scheme <n>` -> `style(<n>)` on the label option (44-02 reads ticksetstyles); tokens are spliced before the explicit sub-options. An unknown name: twoway's named-style note (fixture words).
- **D-44-03.d One copy, twoway's exclusivity.** New Mata `string scalar _dash_scale_exclusive(string scalar copy)`: the full names (through `_dash_so_canon(<word>, "axscale")`) present in the copy among `nolog log noatanh atanh nologit logit nolog1m log1m`, in THAT declared order, deduplicated; with two or more, returns `"only one of options " + <a> + " or " + <b> + " is allowed"` (three or more: `"<a>, <b>, or <c>"`, opts_exclusive.ado's form), else "". Called in `_dash_rep_reduce`'s first loop (dash_parse.mata:11929-11944) on `_dash_rep_value(toks[i])` for every token whose key is `xscale yscale xscale2 yscale2 tscale tscale2 zscale` or an axis-3..9 scale key, before any merge, setting the caller's local `_rp_excl`; dash.ado's caller at :10993 refuses with `_dash_say("err", <line>)` and `exit 198` when it is set. A graph option list with no repeated option also reaches `_dash_rep_reduce` (confirm by the test `yscale(log nolog)` alone; if it does not, call the check where `_dash_parse_graph_opts` hands `xscale()` to `_dash_subopt_check`, dash.ado:8772, on the single copy). D-44-03.b's `_dash_scale_untransformable` runs in the same loop, after this check.
- **D-44-03.e Log ticks as twoway ticks them; the picture of the positive points.** On a log axis the count tick input is every finite value (non-positive included) for the tick range only, natscale over it, then ticks at or below 0 dropped (twoway's rule, C20/G6); the hull keeps the positive values. twoway's degenerate picture (the non-positive points piled on the bottom edge and the rest squashed, appendix :1256-1261) is not copied: ruling A-5 documents it, as RH-8 is (Q25), and A-15 applies A-5 to WP-44's residuals as WP-43 applies it. The log rule paragraph says so in one sentence with the measured example (C20: `gen z = mpg - 25`, `scatter z weight, yscale(log)`), one Differences line links to it, a help-claim test pins it, and AX-11 closes in the Documented forms with no open or residual entry (A-5, A-15: a residual a ruling documents closes `Documented`, with a Documented Tracked line, as RH-8 does in 46-02): Tracked line (PD-3) `Documented in WP-44, BUGS.md "<title>", commit pending.`; Resolution (PD-4, documented) `Documented <ddmonyyyy> (WP-44, AX-11). dash.sthlp Differences from twoway and the xscale()/yscale() log rule paragraph: log axes ticked over every finite value as twoway ticks them; twoway's degenerate picture is not copied (A-5). Pinned by test/test_axis_scales_p9.py::TestLogTicks::test_the_help_sentence, ::test_nonpositive, Q4403-7. Closes GAPS4 AX-11 (WP-44, AX-11).` Because the state is `documented`, AX-11's `AX-11 (documented)` rows of `scripts/corpus/ledger.tsv` stay live under D-33-05.e and are kept (A-10, A-15); only a plain `AX-11` row, if one exists, is deleted (D-33-05.i).
- **D-44-03.f MS-14 is measured at the base first.** If `TestLogRange::test_no_end_tick` passes at the WP-44 base (34-03 landed), the commit closes MS-14 with that test as the pin and its failure recorded at `090d928` (detached scratch worktree), no code; else the fix is: in `_dash_finish_count_ticks` (and `dash_axis_finish`), `extra` is emptied for a log axis whose ticks are not `#N`, exactly as for a default date axis.
- **D-44-03.g Empty minmax writes twoway's labels.** In the minmax branch (:42330-42341) and the tick branch (:44483-44487), when there are no values: `FixedTicker(ticks=[lo, hi], tags=[_DASH_COUNT_TAG + "1", _DASH_MINMAX_TAG])` at the empty scale's ends (`_DASH_EMPTY_SCALE[kind]`, :40244) with `major_label_overrides = {lo: <fixture text lo>, hi: <fixture text hi>}` (expected `-1.e+300` and `1.e+300`, which are what twoway's `%9.0g` writes for its ±1e300 empty scale); `dash_axis_finish` keeps this after a move to an empty selection and restores natscale minmax when rows return.
- **D-44-03.h Overflow is refused before Python, in twoway's words.** (1) `_dash_natscale_ticks` (and `dash_natscale` in JS, `Math.pow` returns Infinity and needs no guard) skips a candidate whose `10.0 ** z` overflows (`try: p = 10.0 ** z except OverflowError: continue`) and returns `[lo, hi]` when none is finite -- no traceback can come from it. (2) The refusal: 37-01's `_dash_zero_obs_check` (PD-15; it walks every plot of the spec with its variables, `qual_col` and options) gains a span step: per (dimension, axis number, after `horizontal` swaps) the minimum and maximum of the plotted variables over the rows the plot draws (`summarize` with the plot's and graph's qual columns); when `max - min` is missing in Stata arithmetic (beyond `c(maxdouble)`) for any axis, it prints the fixture's `dg11.pm8e307` line and exits with its rc (expected r(199) and twoway's words). Whether two one-signed plots that together overflow are refused is the fixture's `dg11.two_plots` answer; follow it.

## Risk: [red] -- the log tick input, the axis finisher's JS and the copy reducer every command passes through

**Why.** The finisher runs on every move of every saved page; the log tick input change touches every log axis; `_dash_rep_reduce` and dash.ado's refusal path run for every command.

**Risk factors.**
1. The transform refusal on `_dash_rep_reduce` refuses a form twoway draws (`yscale(noatanh)`, `yscale(log1m) yscale(nolog1m)`, an abbreviation of another word).
2. The log input change moves ticks on every log axis with non-positive data; other log axes must not move.
3. `_dash_rep_reduce` is on every command's path; a wrong key test refuses a valid copy.
4. The span refusal adds `summarize` calls per plot at export (time).
5. 34-03/34-09 rewrote parts of `_dash_finish_count_ticks` and `dash_axis_finish`; anchors moved.

**Mitigation.**
1. Q4403-2..4 run every `ax9.*` probe, the rc 0 ones (no forms, `log1m` then `nolog1m`) included, against the fixture's rc.
2. `TestLogTicks::test_positive_data_unchanged` runs every axis_truth.json log probe.
3. `TestExclusive::test_valid_copies` runs C16 and every axis_look_truth scale probe through the cscript case Q4403-6.
4. The span step runs only on `summarize`-able numeric variables already counted by 37-01's walk; 44-03-12 records the cert block's time.
5. Re-read both finishers at the 44.3 base; the node tests are written against that base.

## Dependencies

- **Depends on: 44-02** (batch 44.2): `SchemeParser.axis_style_tokens` and the three style classes; 44-02's `_DASH_AXIS_FINISH_JS` edits (nogextend, margin) are the base this section edits.
- **Blocks:** none; WP-44's WE follows.
- **Parallel batch 44.3:** alone (R11: the only editor of `_DASH_AXIS_FINISH_JS` and `_dash_finish_count_ticks`).
- Reads 37-01's `_dash_zero_obs_check` (WP-37, landed) and 34-03's range rule (WP-34, landed).

## Evidence

Anchors at `090d928`; re-read at the 44.3 base.

```python
56685 _DASH_SCALE_SUBOPTS = frozenset({"log", "reverse", "range"})
...
56732     out = {"off": "off" in names,
56733            "line_off": "noline" in names and "lcolor" not in names,
...
56737            "outergap": None, "lstyle": None, "noextend": None}
```

```python
42837     if look.get("off") and not by_graph:
42838         axis_obj.visible = False
```

```python
40316     z_lo = math.floor(math.log10(rng / (n + 2))) - 1
40317     z_hi = math.ceil(math.log10(rng)) + 1
40318     for z in range(z_lo, z_hi + 1):
40319         for m in (1, 2, 5):
40320             d = m * 10.0 ** z
```

```python
42330     elif mode == "minmax":
42331         if values is not None:
...
42334             if len(vals):
...
42339                 axis_obj.ticker = FixedTicker(
42340                     ticks=[float(vals.min()), float(vals.max())],
```

`_dash_finish_count_ticks` :47748-47767 (`if e["kind"] == "log": extra = [v for v in extra if v > 0]`; the default-date exemption). `_dash_layer_extent` :46078 (positive values on log, :46120). `_DASH_EMPTY_SCALE = {"linear": (0.0, 1.0), "log": (1.0, 10.0)}` :40244. `_dash_rep_reduce` dash_parse.mata:11914 (first loop :11929-11944), caller dash.ado:10993. Stata: `_gs_parse_and_log_axoptions.ado:18-39` (syntax, `opts_exclusive "\`transform'"`), `:125-130` (fillspace), `transform.class:109-123`, `/Applications/StataNow/ado/base/o/opts_exclusive.ado` (message forms), `style/axisstyle-vertical_nogrid.style` (`set draw_major_grid no`). Fixtures on disk: axis_truth.json `b2_log_range`, axis_look_truth.json scale probes.

### Tests that pin today's behaviour (flip, never delete)

- Tests asserting atanh/logit/log1m on a scale are taken with the "ignored" note flip to the r(199) refusal, and those asserting style() is named flip to drawn: `grep -rn "atanh\|logit\|log1m" test/*.py test/*.cscript | grep -v lowess`.
- Tests asserting `off fill` equals `off`: `grep -rn "fill" test/test_axis_look_options.py test/test_axis_options.py`.
- test/test_axis_extents.py `b2_log_range` (hull only): extend with the drawn ticks (MS-14).
- Pins of the help sentences :4617-4618 ("fill draw the plain axis"), :4662-4665 (log rule) -- HR-16 `:4617 fill` is corrected here.
- test/test_help_claims_9.py::TestTheUnreadStyleFiles::test_the_reader_still_skips_both_classes (:222-228): the class tuple as 44-02 left it (eight classes) gains `"axisstyle"` -- flipped again with the R10 comment `# old -> new: axisstyle (WP-44 AX-9)`.

## User stories

- **US-44-03.1** As a Stata user, I want `yscale(off fill)` to keep the space so that a combined layout lines up as in Stata.
- **US-44-03.2** As a Stata user, I want `yscale(logit)`, `xscale(atanh)` and `zscale(log1m)` refused as Stata refuses them, so that a do-file that fails in Stata fails in dash instead of drawing a linear axis with a note.
- **US-44-03.3** As a Stata user who typed `yscale(log nolog)`, I want twoway's refusal so that the do-file behaves the same.
- **US-44-03.4** As a Stata user, I want a log axis's ticks, a log axis with range(), and minmax on an empty sample to look as twoway's.
- **US-44-03.5** As a Stata user, I want an overflowing data range refused in twoway's words, never a Python traceback.

## Business requirements

- **BR-44-03.1** `off fill` keeps the axis's border space; nothing of the axis is visible.
- **BR-44-03.2** atanh, logit and log1m (any abbreviation, any scale option, across copies) are refused before Python with twoway's line and rc (`unrecognized command`, r(199)); the `no` forms alone draw the plain graph with no note; style() reads the axis style file.
- **BR-44-03.3** Two transform words in one copy are refused r(198) with twoway's line; copies across options merge as today.
- **BR-44-03.4** Log ticks equal twoway's on non-positive data; range() on a log axis adds no end tick; empty minmax writes twoway's two labels.
- **BR-44-03.5** An overflowing span is refused before Python with twoway's rc and line; no traceback on any input.
- **BR-44-03.6** Saved page and served app agree.

## Technical requirements

- **TR-44-03.1** `_dash_scale_look` gains `"fill"`; `_dash_apply_scale_look` per D-44-03.a.
- **TR-44-03.2** Mata `_dash_scale_untransformable` (D-44-03.b) beside `_dash_scale_exclusive`, called in `_dash_rep_reduce`'s first loop; header index line; `_needed` entry; the `_rp_trans` read and the r(199) refusal at dash.ado:10993's caller, after the `_rp_excl` refusal. `_DASH_SCALE_SUBOPTS` += `{"noatanh", "nologit", "nolog1m", "style"}`; `_dash_scale_spec` returns `"style_tokens"` (D-44-03.c). No Python or JS transform code.
- **TR-44-03.3** Mata `_dash_scale_exclusive` (D-44-03.d) after `_dash_rep_reduce`, before `_dash_scale_untransformable`; header index line; `_needed` entry; program_coverage_map.py row naming `test_option_validation.cscript:Q4403-6`; the `_rp_excl` read at dash.ado:10993's caller.
- **TR-44-03.4** Log input (D-44-03.e): `_dash_layer_extent(..., role="ticks")` returns finite values including non-positive on `"log"` when called for the tick input (new `role` value), positive only for the hull; `_dash_finish_count_ticks` and `dash_axis_finish` call the tick role, then drop ticks `<= 0`.
- **TR-44-03.5** MS-14 per D-44-03.f.
- **TR-44-03.6** Empty minmax per D-44-03.g; the texts are read from `test/fixtures/axis_scale_truth.json` at TEST time only; the code writes the two literal strings the fixture holds (`"-1.e+300"`, `"1.e+300"` if confirmed), with a comment citing the fixture key.
- **TR-44-03.7** Overflow per D-44-03.h: `_dash_natscale_ticks` guard; the span step inside `_dash_zero_obs_check` (dash.ado; re-read 37-01's program) with the fixture's rc and line; program_coverage_map.py note for the extended program.
- **TR-44-03.8** No new Python function for AX-9. test/program_coverage_map.py rows: `_dash_scale_untransformable` -> `test_option_validation.cscript:Q4403-2`, `_dash_scale_exclusive` -> `:Q4403-6`.
- **TR-44-03.9** Parity (R8) `CORPUS` under `# WP-44 44-03`: `"yscale off fill"`, `"yscale noatanh"`, `"yscale style vertical_nogrid"`, `"yscale log non-positive"`, `"xscale log range"`, `"ylabel minmax empty"`; `MOVE_CORPUS`: `"ylabel minmax empty, dropdown to none"`.
- **TR-44-03.10** Help (R3): :4612-4618 (fill: keeps the space with off -- HR-16 `:4617 fill`), a sentence under xscale()/yscale() that `log` is the only scale transform and that atanh, logit and log1m are refused as Stata refuses them (r(199)), a style() paragraph with the measured example, the AX-10 refusal sentence, the log rule paragraph (:4662-4665) rewritten to twoway's rule plus the one-sentence difference on the degenerate picture (D-44-03.e) with its Differences line, the minmax sentence for an empty sample, the overflow refusal sentence. TWOWAY_COVERAGE_AUDIT.md: each item's closing commit appends `[WP-44 <id>: corrected -- <what is drawn>]` to the row of its option (grep `xscale`, `yscale`, `minmax` in the file; when no row names the option, the commit body says so).

## Boundaries

- Do not edit `_dash_axis_title_look` (44-01), `_DASH_AXLABEL_HONOURED` or the custom overlay (44-02) except to read 44-02's resolver, the date-axis rules (44-04), `_dash_lone_second_axes` (44-05).
- `nolog`, `noreverse`, `ring()` silence is 49-02's (AX-21); this section adds `nolog` only as a transform word for the exclusivity check and the merge (it already reads as "not log").
- No new browser, no `graph set`.

## Stata truth

New `scripts/extract_axis_scale_truth.do` -> `test/fixtures/axis_scale_truth.json` (frame of `scripts/extract_axis_look_truth.do`; per key: rc, log lines, SVG texts/positions, plot region, and `.Graph.plotregion1.yscale`/`xscale` members and `dlg_tickpos` through `cert_graph_scale`'s reading, as test/cert_svg.do:295 reads them). Keys:
- `ax7.*`: `off_fill` and `off` (C10/C11: `scatter mpg weight, yscale(off fill)` / `yscale(off)`), `x_off_fill`.
- `ax9.*` (rc and the log's error line for each): `atanh_y` (`scatter mpg weight, yscale(atanh)`), `logit_y`, `log1m_y`, `log1_y` (`yscale(log1)`), `atanh_x` (`xscale(atanh)`), `alt_atanh` (`yscale(alt atanh)`), `t_atanh` (sp500, `tsset date`, `tsline close, tscale(atanh)`), `z_contour` (sandstone, `twoway contour depth northing easting, zscale(atanh)`), `z_colorvar` (`scatter mpg weight, colorvar(price) zscale(logit)`), `axis2` (`(scatter mpg weight) (scatter price weight, yaxis(2)), yscale(axis(2) logit)`), `log_then_logit` (`yscale(log) yscale(logit)`), `logit_then_log` (`yscale(logit) yscale(log)`), `log1m_then_no` (`yscale(log1m) yscale(nolog1m)`), `no_forms` (`yscale(noatanh nologit nolog1m)`; its SVG equals the plain graph's), `style_nogrid` (`yscale(style(vertical_nogrid))`), `style_noline` (`horizontal_noline` on x), `style_bogus`. Measured 07nov2026 before this revision: the refused forms are `unrecognized command` r(199), `log1m_then_no` and `no_forms` rc 0, `style_nogrid` rc 0.
- `ax10.*`: `log_nolog` (F1), `atanh_log` (F8), `three` (`yscale(log logit atanh)`), `across` (C16 `yscale(log) yscale(nolog)`), `log_log` (`yscale(log log)`).
- `ax11.*`: C20 (`gen z = mpg - 25`, `scatter z weight, yscale(log)`), `with_n` (`ylabel(#5)` beside it).
- `ms14.*`: B04 (`scatter mpg weight, xscale(range(1000)) xscale(log)`), `b2` (`yscale(log range(1000 20000))`), `with_n` (`yscale(log range(1000 20000)) ylabel(#5)`).
- `dg13.*`: S07 (`scatter mpg weight if price < 0, xlabel(#5) ylabel(minmax)`), `log_empty` (with `yscale(log)`).
- `dg11.*`: `pm8e307` (`clear`, `set obs 2`, `gen y = cond(_n == 1, 8e307, -8e307)`, `gen x = _n`, `scatter y x`), `pm4_5e307`, `pm4_4e307`, `one_signed` (0 and 8e307), `two_plots` (`(scatter y1 x) (scatter y2 x)` with y1 = 8e307, y2 = -8e307 one row each).

Run twice through `scripts/stata_slot.sh` with DASH_REPO; `git add -f`. Truth blocks `* ==== S03 AX-7: off fill keeps the space ====`, `S03 AX-9` (scale styles only), `S03 AX-11`, `S03 MS-14`, `S03 DG-13`, gate `WP44_ONLY`/`"S03"`, helper `_q4403_reg`. **Block order (BRIEF):** batch 44.1 landed the S04 (44-04) and S05 (44-05) blocks and batch 44.2 the S02 blocks (44-02, inserted above S04), so insert each S03 block directly above the first `* ==== S04` header (44-04's `* ==== S04 AX-18: numbers and log on date axes ====` block), after 44-02's S02 blocks, in item order -- not above the append marker; the hygiene reader requires section order S01, S02, S03, S04, S05. AX-10 has no S03 block: all its cases are refusals or acceptances measured against the fixture's twoway answers, so its truth is the area-script case Q4403-6 (BRIEF, Certification scripts: refusal cases go in the existing cscript for their area). The refusal cases (Q4403-2..4 transform words, Q4403-6 exclusivity, Q4403-12 overflow) go in test/test_option_validation.cscript under their own ids.

## TDD test stubs

New file `test/test_axis_scales_p9.py`:
- Test: off fill keeps the border -- ::TestOffFill::test_space_kept[saved|served] (fails at base: visible False); ::test_off_alone_unchanged.
- Test: transform words -- Q4403-2 (atanh), Q4403-3 (logit), Q4403-4 (log1m) in test/test_option_validation.cscript: every refused `ax9.*` probe of that word refused with the fixture's line and rc, and the rc 0 probes (`no_forms`, `log1m_then_no`) drawn with no note (fails at base: rc 0 with the ignored note); ::TestTransformWords::test_no_forms_silent[saved|served] (`yscale(noatanh)`: no ignored note, the y axis's ticks equal the plain page's; fails at base: note); ::TestTransformWords::test_the_help_sentence (the xscale()/yscale() sentence, the `_between(_help(), ...)` pattern; fails at base).
- Test: the log-picture sentence -- ::TestLogTicks::test_the_help_sentence (the log rule paragraph's sentence and its Differences line, the `_between(_help(), ...)` pattern; fails at base).
- Test: scale style() -- ::TestScaleStyle::test_vertical_nogrid[saved|served]; ::test_unknown_notes.
- Test: exclusivity -- Q4403-6 cscript (refused copies and C16 accepted); ::TestExclusive::test_message_forms (Mata through the cscript; pytest checks the help sentence).
- Test: log ticks -- ::TestLogTicks::test_nonpositive[saved|served] (fails at base: 5 10 15); ::test_positive_data_unchanged; ::test_js_twin (node).
- Test: log range -- ::TestLogRange::test_no_end_tick[saved|served] (D-44-03.f).
- Test: empty minmax -- ::TestEmptyMinmax::test_labels[saved|served] (fails at base); ::test_move_to_empty (node).
- Test: overflow -- ::TestOverflow::test_natscale_guard (pure Python: `_dash_natscale_ticks(-8e307, 8e307, 5)` returns a list, no exception; fails at base with OverflowError); Q4403-12 cscript (r(199) line).
- cscript blocks: Q4403-1 (off fill), Q4403-2..4 (transform words refused; test_option_validation.cscript), Q4403-5 (style), Q4403-7 (log ticks), Q4403-8..9 (log range), Q4403-10..11 (empty minmax).
- Flips: listed under Evidence.
- Parity: TR-44-03.9.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| off fill | pytest TestOffFill; Q4403-1 | axis_scale_truth.json ax7.* | yes |
| transform words and style() | Q4403-2..4 (test_option_validation.cscript); pytest TestTransformWords, TestScaleStyle; Q4403-5 | ax9.* | refusal: Stata side; no forms and style(): yes |
| exclusivity | Q4403-6 (test_option_validation.cscript) | ax10.* | Stata side |
| log ticks, log range | pytest TestLogTicks, TestLogRange; node; Q4403-7..9 | ax11.*, ms14.*, axis_truth.json b2_log_range | yes |
| empty minmax | pytest TestEmptyMinmax; node; Q4403-10..11 | dg13.* | yes |
| overflow | pytest TestOverflow; Q4403-12 | dg11.* | Stata side + renderer guard |
| parity and moves | test_mode_parity.py CORPUS/MOVE_CORPUS | -- | yes |

Acceptance criteria:
- **AC-44-03.1** off fill's plot region equals the fixture's within the geometry tolerance used by test_axis_look_options.py; nothing of the axis is visible.
- **AC-44-03.2** Every refused `ax9.*` probe prints the fixture's line with its rc (expected `unrecognized command`, r(199)) and writes no page; `yscale(atanh log)` is r(198) with twoway's exclusivity line first; `no_forms` and `log1m_then_no` draw as the plain graph with no note; `style_nogrid` removes the grid as C17.
- **AC-44-03.3** ax10 refusals print twoway's line with r(198); C16 draws linear.
- **AC-44-03.4** C20 ticks 10 20; the degenerate twoway picture is stated in the log rule paragraph and its Differences line, pinned; AX-11's Tracked line is `Documented in WP-44, BUGS.md "<title>", commit pending.` and its BUGS Resolution PD-4's documented form (D-44-03.e), with no open or residual entry (A-5, A-15) and its `AX-11 (documented)` ledger rows kept and live (A-10, A-15, D-33-05.e); B04 and b2_log_range draw no range-end tick; S07 writes the fixture's two labels.
- **AC-44-03.5** `pm8e307` is refused with the fixture's rc and line; no input reaches `10.0 ** z` overflow.

## Tasks

**Commit boundary.** AX-7: 44-03-01 (no commit) + 44-03-02 (commit `Keep an off axis's space under fill (WP-44 AX-7)`). AX-9: 44-03-03 (no commit) + 44-03-04 (commit `Refuse atanh, logit and log1m scales and read scale styles (WP-44 AX-9)`). AX-10: 44-03-05 (commit `Refuse contradictory scale transforms in one copy (WP-44 AX-10)`; failing case written and saved first in the task). AX-11: 44-03-06 (no commit) + 44-03-07 (commit `Tick log axes over every value as twoway does (WP-44 AX-11)`). MS-14: 44-03-08 (commit `Pin log range() ticks over the data (WP-44 MS-14)`; test, base check and fix-or-pin in one task). DG-13: 44-03-09 (no commit) + 44-03-10 (commit `Label an empty minmax axis and refuse overflowing spans (WP-44 DG-13)`). 44-03-11 browser check, 44-03-12 cert timing, 44-03-13 section check (no commits). Branch `wp44-s03`; `$WT` and the closing steps every closing task takes before its commit are in Notes ("Before every commit").

```xml
<task type="auto" id="44-03-01">
  <name>Measure scales; write AX-7 failing tests</name>
  <files>scripts/extract_axis_scale_truth.do, test/test_axis_scales_p9.py, test/test_wp44_truth.cscript</files>
  <action><![CDATA[Create scripts/extract_axis_scale_truth.do with every key of "Stata truth", run it twice through scripts/stata_slot.sh with DASH_REPO set, git add -f test/fixtures/axis_scale_truth.json (staged). Create test/test_axis_scales_p9.py with TestOffFill only and insert "* ==== S03 AX-7: off fill keeps the space ====" (Q4403-1) directly above the first `* ==== S04` header of test/test_wp44_truth.cscript, after the S02 blocks (Stata truth, Block order), not above the append marker. Run both on the unmodified tree; save to <scratch>/44-03-01-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_scales_p9.py::TestOffFill -q -n0 -> test_space_kept fails (visible False), test_off_alone_unchanged passes; Q4403-1 FAIL; failure file exists]]></verify>
  <done>The scale fixture exists and AX-7's tests fail on the unmodified tree.</done>
</task>

<task type="auto" id="44-03-02">
  <name>Keep an off axis's space</name>
  <files>dash_render.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[Implement D-44-03.a (TR-44-03.1); confirm by a node test in test/test_axis_scales_p9.py::TestOffFill (test_move_keeps_alphas) that dash_axis_finish never resets the alphas. Rewrite dash.sthlp:4617-4618 (HR-16 fill). Parity "yscale off fill". Close AX-7 (BUGS closed form naming TestOffFill and Q4403-1; GAPS4 Closed, commit pending; delete AX-7's GAPS4_OPEN line in test/test_tracking_documents.py; CHANGELOG Fixed; TWOWAY_COVERAGE_AUDIT.md's scale row gains "[WP-44 AX-7: corrected -- off fill keeps the axis's space]"); take the three closing steps for `AX-7` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `AX-7` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py AX-7`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); run TestOffFill, test_axis_look_options.py, test_axis_options.py, the block; commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_scales_p9.py::TestOffFill test/test_axis_look_options.py -q -n0 -> pass; "Q4403-1 PASS"; python3 test/known_differences.py AX-7 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 AX-7)"]]></verify>
  <done>off fill keeps the axis's space in both modes and AX-7 is committed.</done>
</task>

<task type="auto" id="44-03-03">
  <name>Write AX-9 failing tests</name>
  <files>test/test_axis_scales_p9.py, test/test_option_validation.cscript, test/test_wp44_truth.cscript</files>
  <action><![CDATA[Add cases Q4403-2 (atanh), Q4403-3 (logit) and Q4403-4 (log1m) to test/test_option_validation.cscript: each refused `ax9.*` probe of the word refused with the fixture's line and rc, `no_forms` and `log1m_then_no` drawn (rc 0) with no "ignored" note in the log. Write TestTransformWords (test_no_forms_silent, test_the_help_sentence) and TestScaleStyle in test/test_axis_scales_p9.py, and insert "* ==== S03 AX-9: scale styles ====" (Q4403-5) in test/test_wp44_truth.cscript directly above the first `* ==== S04` header, after S03 AX-7 (Block order). Run all of them on the tree as 44-03-02 left it; save to <scratch>/44-03-03-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_scales_p9.py::TestTransformWords test/test_axis_scales_p9.py::TestScaleStyle -q -n0 -> fail (the ignored note; style not drawn); Q4403-2..4 FAIL (rc 0); Q4403-5 FAIL]]></verify>
  <done>AX-9's regression tests fail before the fix and are saved.</done>
</task>

<task type="auto" id="44-03-04">
  <name>Refuse transform words; read scale styles</name>
  <files>dash_parse.mata, dash.ado, dash_render.py, dash.sthlp, test/test_mode_parity.py, test/program_coverage_map.py</files>
  <action><![CDATA[Implement D-44-03.b (TR-44-03.2: `_dash_scale_untransformable` in `_dash_rep_reduce`'s first loop, the `_rp_trans` refusal `unrecognized command` r(199) in dash.ado, the three `no` forms in `_DASH_SCALE_SUBOPTS`) and D-44-03.c (the axisstyle class and tokens; copy lists for any new served name). Flip the pins the Evidence grep finds and the class-tuple pin of test_help_claims_9.py (eight -> nine classes, `# old -> new: axisstyle (WP-44 AX-9)`). Help: the xscale()/yscale() sentence (only `log` transforms a scale; atanh, logit and log1m are refused as Stata refuses them) and the style() paragraph with the measured example. CHANGELOG under "### Changed behaviour (may need your do-files changed)": "xscale(), yscale(), tscale() and zscale() with atanh, logit or log1m are refused with r(199), as twoway's graph fails on them; dash took them with a note before (scatter mpg weight, yscale(logit)) (WP-44, AX-9)", and under "### Fixed in WP-44" the style() line. Parity entries "yscale noatanh" and "yscale style vertical_nogrid"; test/program_coverage_map.py row for `_dash_scale_untransformable`. Close AX-9 (BUGS closed form naming sil:SD-5, D75, the 07nov2026 re-measure (twoway r(199); the audit's C12-C14 pictures do not reproduce), BUGS.md:3563's D7 closure, and the pins Q4403-2..5 and TestTransformWords, TestScaleStyle; GAPS4 Closed, commit pending; delete AX-9's GAPS4_OPEN line in test/test_tracking_documents.py; TWOWAY_COVERAGE_AUDIT.md's scale row gains "[WP-44 AX-9: corrected -- atanh, logit and log1m refused as twoway's graph refuses them; style() drawn]"); take the three closing steps for `AX-9` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `AX-9` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py AX-9`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); run the AX-9 tests, test_help_claims_9.py, test_program_coverage_map.py, test_cscript_hygiene.py, test_mode_parity.py -k "44-03" (batch tier, targeted), test_option_validation.cscript and the S03 block; commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_scales_p9.py::TestTransformWords test/test_axis_scales_p9.py::TestScaleStyle test/test_help_claims_9.py test/test_program_coverage_map.py -q -n0 -> pass; "Q4403-2 PASS" .. "Q4403-5 PASS" and test_option_validation.cscript's ALL CHECKS PASSED; python3 test/known_differences.py AX-9 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 AX-9)"]]></verify>
  <done>atanh, logit and log1m are refused on every scale option as twoway's graph refuses them, scale style() is drawn in both modes, and AX-9 is committed.</done>
</task>

<task type="auto" id="44-03-05">
  <name>Refuse contradictory transforms per copy</name>
  <files>dash_parse.mata, dash.ado, test/test_option_validation.cscript</files>
  <action><![CDATA[AX-10 adds no S03 block (Stata truth: its truth is the area-script case). First add case Q4403-6 to test/test_option_validation.cscript (ax10.log_nolog, atanh_log, three refused with the fixture's line and r(198); across and log_log accepted), run it through a two-line driver on the tree as 44-03-04 left it and save the failure to <scratch>/44-03-05-failure.txt. Then implement D-44-03.d (TR-44-03.3; its test/program_coverage_map.py row) and TR-44-03.10's AX-10 refusal sentence in dash.sthlp; add the CHANGELOG line under "### Changed behaviour (may need your do-files changed)" (a form dash accepted is now refused). Close AX-10 (BUGS, GAPS4, GAPS4_OPEN in test/test_tracking_documents.py; TWOWAY_COVERAGE_AUDIT.md's scale row gains "[WP-44 AX-10: corrected -- two transforms in one copy refused as twoway refuses them]"); take the three closing steps for `AX-10` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `AX-10` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py AX-10`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); run the cscript, test_tracking_documents.py, test_cscript_hygiene.py, test_program_coverage_map.py, test_twoway_option_parity.cscript through stata_slot.sh; commit.]]></action>
  <verify><![CDATA[before: Q4403-6 FAIL (rc 0); after: "Q4403-6 PASS" and test_option_validation.cscript's ALL CHECKS PASSED; python3 -m pytest test/test_program_coverage_map.py test/test_cscript_hygiene.py -q -n0 -> pass; python3 test/known_differences.py AX-10 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 AX-10)"]]></verify>
  <done>Two transform words in one scale copy are refused in twoway's words and AX-10 is committed.</done>
</task>

<task type="auto" id="44-03-06">
  <name>Write AX-11 failing tests</name>
  <files>test/test_axis_scales_p9.py, test/test_wp44_truth.cscript</files>
  <action><![CDATA[Write TestLogTicks (test_nonpositive, test_positive_data_unchanged over every axis_truth.json log probe, test_js_twin, test_the_help_sentence) and insert "* ==== S03 AX-11: log ticks over every value ====" (Q4403-7) directly above the first `* ==== S04` header, after S03 AX-9 (Block order). Run; save to <scratch>/44-03-06-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_scales_p9.py::TestLogTicks -q -n0 -> test_nonpositive fails ([5, 10, 15] != [10, 20]); test_positive_data_unchanged passes]]></verify>
  <done>AX-11's regression tests fail before the fix and are saved.</done>
</task>

<task type="auto" id="44-03-07">
  <name>Tick log axes over every value</name>
  <files>dash_render.py, dash.sthlp</files>
  <action><![CDATA[Implement D-44-03.e (TR-44-03.4) in _dash_layer_extent's new role, _dash_finish_count_ticks and dash_axis_finish. Rewrite the log rule paragraph (dash.sthlp:4662-4665) and add the one-sentence difference on twoway's degenerate picture (the C20 example) with its Differences line, pinned by TestLogTicks::test_the_help_sentence (A-5). Parity "yscale log non-positive" in test/test_mode_parity.py. Close AX-11 in the Documented forms of D-44-03.e (A-5, A-15): BUGS Resolution "Documented <ddmonyyyy> (WP-44, AX-11). dash.sthlp Differences from twoway and the xscale()/yscale() log rule paragraph: log axes ticked over every finite value as twoway ticks them; twoway's degenerate picture is not copied (A-5). Pinned by test/test_axis_scales_p9.py::TestLogTicks::test_the_help_sentence, ::test_nonpositive, Q4403-7. Closes GAPS4 AX-11 (WP-44, AX-11)." and `- [x]`; GAPS4 Tracked line "Documented in WP-44, BUGS.md "<title>", commit pending."; no open or residual entry; delete AX-11's GAPS4_OPEN line in test/test_tracking_documents.py; CHANGELOG Fixed; TWOWAY_COVERAGE_AUDIT.md's scale row gains "[WP-44 AX-11: corrected -- log ticks over every value; the degenerate picture documented]". Take the three closing steps for `AX-11` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `AX-11` rows of scripts/corpus/ledger.tsv (its `AX-11 (documented)` rows stay), run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py AX-11`, delete each `<file>:<line>` row it prints (a row of the difference AX-11 documents rewritten to `"AX-11 (documented)"`) or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)) -- with this ledger rule: keep every `AX-11 (documented)` row of scripts/corpus/ledger.tsv (live under D-33-05.e while AX-11 is documented, A-10, A-15) and delete only a plain `AX-11` row if one exists (rewritten to `AX-11 (documented)` instead when it records the degenerate picture D-44-03.e documents), then regenerate test/fixtures/corpus_ledger.json; commit body `BUGS.md: "<title>" (documented)`. Run TestLogTicks, test_axis_extents.py, test_natscale.py, test_tracking_documents.py, test_corpus_ledger.py, the block; commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_scales_p9.py::TestLogTicks test/test_natscale.py test/test_axis_extents.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass (TestTheLedger::test_every_ledger_row_is_live included); grep -c "AX-11 Tracked:\*\* Documented in WP-44" GAPS4.md -> 1; grep -c "^AX-11 (documented)" scripts/corpus/ledger.tsv -> the count it had before this commit; "Q4403-7 PASS"; python3 test/known_differences.py AX-11 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 AX-11)"]]></verify>
  <done>Log axes over non-positive data are ticked as twoway ticks them and AX-11 is committed.</done>
</task>

<task type="auto" id="44-03-08">
  <name>Pin or fix the log range tick</name>
  <files>test/test_axis_scales_p9.py, dash_render.py, test/test_axis_extents.py</files>
  <action><![CDATA[Write TestLogRange::test_no_end_tick over ms14.b04, ms14.b2, ms14.with_n (with_n keeps the widened ticks if the fixture says so) and insert "* ==== S03 MS-14: log range() ticks over the data ====" (Q4403-8, Q4403-9) in test/test_wp44_truth.cscript directly above the first `* ==== S04` header, after S03 AX-11 (Block order). Run at the 44.3 base. If it fails: save the failure, implement D-44-03.f's fix in _dash_finish_count_ticks and dash_axis_finish, and pass. If it passes: run it against 090d928 in a detached scratch worktree (git worktree add <scratch>/base090 090d928; copy the new test file in; python3 -m pytest that file -q -n0), save that failure, remove the worktree, and change no code. Extend test_axis_extents.py's b2_log_range test with the drawn ticks. Close MS-14 (BUGS names 34-03 when the base already passed; GAPS4 Closed; GAPS4_OPEN in test/test_tracking_documents.py; TWOWAY_COVERAGE_AUDIT.md's scale row gains "[WP-44 MS-14: corrected -- range() on a log axis adds no end tick]"; when the code fix was taken, the CHANGELOG line "- range() on a log axis no longer adds a tick at the range's end (scatter mpg weight, xscale(range(1000)) xscale(log)) (WP-44, MS-14)" under "### Fixed in WP-44", and no CHANGELOG line when it closed as a pin, since nothing drawn changed in WP-44). Take the three closing steps for `MS-14` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `MS-14` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py MS-14`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_scales_p9.py::TestLogRange test/test_axis_extents.py -q -n0 -> pass; "Q4403-8 PASS", "Q4403-9 PASS"; <scratch>/44-03-08-failure.txt holds a failure (at the 44.3 base or at 090d928); python3 test/known_differences.py MS-14 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 MS-14)"]]></verify>
  <done>range() on a log axis adds no end tick, pinned, and MS-14 is committed.</done>
</task>

<task type="auto" id="44-03-09">
  <name>Write DG-13 failing tests</name>
  <files>test/test_axis_scales_p9.py, test/test_option_validation.cscript, test/test_wp44_truth.cscript</files>
  <action><![CDATA[Write TestEmptyMinmax (test_labels, test_move_to_empty) and TestOverflow::test_natscale_guard; insert "* ==== S03 DG-13: empty minmax and overflowing spans ====" (Q4403-10, Q4403-11) directly above the first `* ==== S04` header, after S03 MS-14 (Block order), and add Q4403-12 (dg11.pm8e307 refused with the fixture's rc and line; one_signed drawn) to test/test_option_validation.cscript. Run; save to <scratch>/44-03-09-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_scales_p9.py::TestEmptyMinmax test/test_axis_scales_p9.py::TestOverflow -q -n0 -> fail (Bokeh ticks; OverflowError); Q4403-10..12 FAIL]]></verify>
  <done>DG-13's regression tests fail before the fix and are saved.</done>
</task>

<task type="auto" id="44-03-10">
  <name>Label empty minmax; refuse overflow</name>
  <files>dash_render.py, dash.ado, dash.sthlp</files>
  <action><![CDATA[Implement D-44-03.g (both minmax branches and dash_axis_finish) and D-44-03.h (the natscale guard; the span step in _dash_zero_obs_check with the fixture's rc and line). Help: the minmax sentence for an empty sample and the overflow refusal; CHANGELOG under "### Fixed in WP-44" (the refusal replaces an r(7102) traceback, rc now twoway's). Parity "ylabel minmax empty" and its MOVE entry in test/test_mode_parity.py. Close DG-13 (BUGS names DG-11; GAPS4 Closed; GAPS4_OPEN in test/test_tracking_documents.py; TWOWAY_COVERAGE_AUDIT.md's axis-label row gains "[WP-44 DG-13: corrected -- minmax on an empty scale labelled as twoway; overflowing spans refused]"); take the three closing steps for `DG-13` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `DG-13` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py DG-13`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); run TestEmptyMinmax, test_tracking_documents.py, TestOverflow, test_natscale.py, the zero-observation tests 37-01 added (grep -l _dash_zero_obs_check test/), the block and test_option_validation.cscript; commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_scales_p9.py test/test_natscale.py -q -n0 -> pass; "Q4403-10 PASS", "Q4403-11 PASS", "Q4403-12 PASS"; python3 test/known_differences.py DG-13 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 DG-13)"]]></verify>
  <done>Empty minmax axes write twoway's labels, overflowing spans are refused in twoway's words, and DG-13 is committed.</done>
</task>

<task type="auto" id="44-03-11">
  <name>Check the scale changes in Chrome</name>
  <files>none</files>
  <action><![CDATA[Run DASH_TEST_TIER=release python3 -m pytest test/test_default_axes_chrome.py -q -n0 and one new release-tier test TestOffFill::test_painted (a saved `yscale(off fill)` page loaded through test/range_probe.py's RangeProbe: the frame's left edge equals the plain page's and no y tick or label paints). Chrome only.]]></action>
  <verify><![CDATA[both pass; js_errors() == []]]></verify>
  <done>The off fill axis paints as the fixture says in Chrome, with no page error.</done>
</task>

<task type="auto" id="44-03-12">
  <name>Time the S03 truth blocks</name>
  <files>none</files>
  <action><![CDATA[Run test_wp44_truth.cscript with WP44_ONLY=S03 once through stata_slot.sh and record the S03 start/end lines' seconds in <scratch>/44-03-timing.txt for the w44_secs table W0 created (the orchestrator updates the table at the batch's merge).]]></action>
  <verify><![CDATA[the log shows "S03 start" and "S03 end" lines and no FAIL; the timing file exists]]></verify>
  <done>The S03 blocks pass together and their cost is recorded.</done>
</task>

<task type="auto" id="44-03-13">
  <name>Check the section end to end</name>
  <files>none</files>
  <action><![CDATA[Run the section's tests, test_option_validation.cscript, test_mode_parity.py -k "44-03", test_help_conformance.py, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test_function_test_map.py, test_program_coverage_map.py, test_tracking_documents.py, test_corpus_ledger.py; grep the six commit messages for claude|anthropic. Write <scratch>/44-03-handback.txt listing the functions edited beyond the manifest's Owns cell (Notes).]]></action>
  <verify><![CDATA[all pass; grep count 0; the hand-back file exists]]></verify>
  <done>The six commits are green together and the hand-back lists what the merger needs.</done>
</task>
```

## Section completion criteria

- Six commits `(WP-44 AX-7)` .. `(WP-44 DG-13)` with failure texts (MS-14's possibly at `090d928`), flips, tracking edits and the three closing steps (Notes: plain rows of scripts/corpus/ledger.tsv removed, corpus_ledger.json regenerated; `python3 test/known_differences.py <id>` printing no row, AX-11's known-table rows of its documented difference in the `(documented)` form, every table's `test_every_known_difference_is_open` green; S09's Q3309-1 PASS, the guard fixture regenerated and committed with the item whenever Q3309-1 reported a change); five Tracked lines in the Closed form and AX-11's in the Documented form (D-44-03.e; A-5, A-15), its `AX-11 (documented)` ledger rows kept; `axis_scale_truth.json` committed and named.
- Q4403-1..12 pass; parity and move entries agree; Chrome check green.

## Notes

- **Traps.** (1) `_dash_rep_reduce` must check each copy as typed, never the merged value (C16); the transform flags of D-44-03.b are the one thing it carries across copies, in the order typed. (2) The span step's `max - min` is computed in Stata double; do not compute it in Mata with `.` checks that treat overflow differently -- test with the fixture's values. (3) `log1` is `log1m`'s abbreviation and `log` is not an abbreviation of `logit`: canonicalise through `_dash_so_canon` before testing a word.
- **Help paragraphs this section owns (R3):** dash.sthlp:4612-4618 (scale look; HR-16 `:4617 fill`), the transform-words sentence and the style() paragraph, :4662-4665 (log rule), the minmax sentence, the overflow sentence, one Differences line (the degenerate log picture).
- **Merge rules touched:** R1, R2, R3, R5, R6 (two Mata functions, one extended ado program), R8, R9, R10 (the class-tuple pin), R11/R12 (sole editor of `_DASH_AXIS_FINISH_JS` and `_dash_finish_count_ticks` in batch 44.3).
- **Owns beyond the manifest's cell (for the orchestrator):** `_dash_rep_reduce` (dash_parse.mata, the exclusivity and transform-word calls), the new Mata `_dash_scale_exclusive` and `_dash_scale_untransformable`, `_dash_zero_obs_check` (dash.ado, 37-01's program, the span step), `_dash_layer_extent` (the `role` value), `_STYLE_FILE_CLASSES` (`axisstyle`). 44-03 is alone in batch 44.3.
- **Before every commit (BRIEF; CLAUDE.md rules 4 and 6; R13).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp44-s03` (BRIEF "Pull form"): every path and command below runs in it. Every closing task (44-03-02, 44-03-04, 44-03-05, 44-03-07, 44-03-08, 44-03-10) takes **the three closing steps** after its tracking edits and before its commit, in this order, whether the item closes `Closed` or `Documented` (BRIEF "The corpus ledger and the known-differences tables" (1)-(3); D-33-05.i, D-33-10.a, D-33-10.h, D-33-09.c; A-10): **(1) the ledger step** -- delete every row of `scripts/corpus/ledger.tsv` whose `gaps4_id` is the item's plain lead id (`AX-7`, `AX-9`, `AX-10`, `AX-11`, `MS-14`, `DG-13`), keep every `<id> (documented)` and `<id> (residual)` row -- AX-11 (twoway's degenerate picture of non-positive data on a log axis, D-44-03.e; A-5, A-15) closes `Documented` (A-5), so a plain row of it that records the difference it documents is rewritten to `<id> (documented)` with its `when` narrowed to that difference, never deleted (D-33-05.e), run `python3 scripts/corpus/ledger.py` (no `--run`: the fixture's `_meta` is kept), `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py test/test_tracking_documents.py -q -n0` in the task's verify; **(2) the known-differences step** -- run `python3 test/known_differences.py <lead id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints (a `*_KNOWN` row whose value is exactly the lead id; `(documented)` and `(residual)` rows are not printed and stay), except that a difference the item's ruling keeps moves into that table's deliberate dict -- the companion dict 33-10 names for it: `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN` (`SCALE_FRAME_DELIBERATE` in test/scale_frame_known.py, `BY_POSITION_DELIBERATE` in test/test_by_text.py, `BY_TYPES_DELIBERATE` in test/test_by_types.py, `STAT_COMBOS_DELIBERATE` in test/test_statistical_truth.py, `COLORVAR_DELIBERATE` in test/test_colorvar_truth.py) -- written `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n); for AX-11 (twoway's degenerate picture of non-positive data on a log axis, D-44-03.e; A-5, A-15), which closes `Documented`, a printed row that records the difference the item documents is rewritten to the value `"<id> (documented)"` (live after the Documented closure, D-33-10.a, A-10), never deleted (none is expected for AX-7, AX-9, AX-10, MS-14 or DG-13: each closes `Closed` and no ruling keeps a difference of it; a row the executor would keep without a ruling id is reported to the orchestrator, not moved); then run the hygiene command it prints (`python3 -m pytest <the files defining test_every_known_difference_is_open> -q -n0 -k every_known_difference_is_open`) in the task's verify; **(3) the guard step** -- run block S09 of test/test_wp33_truth.cscript alone (`WP33_ONLY=S09`, BRIEF's two-line driver with `<repo>` = `$WT`); if 33-09's guard check Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate `test/fixtures/corpus_guard_truth.json` with its extract script (`DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do`), `git add -f` it, rerun S09 to its `Q3309-1 PASS` and commit it with the item (body line `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)`). Then, before the commit: (4) `cd $WT && git pull --ff-only . main` (BRIEF "Pull form"; CLAUDE.md rule 4; a no-op when the batch base already contains main -- if it refuses because main moved, stop and report to the orchestrator, never make a merge commit). (5) Run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is re-run) and report HIGH/CRITICAL or UNKNOWN risk in the hand-back. (6) Grep the message for claude|anthropic before and after committing.
- **Commit-body lines:** `Regression: test/test_axis_scales_p9.py::TestOffFill::test_space_kept -- failed at <base sha> with <text>`; `Flipped: <node> -- <old> was wrong because twoway draws <x>`; `Fixture: test/fixtures/axis_scale_truth.json (scripts/extract_axis_scale_truth.do)`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` (every commit; plus `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` when Q3309-1 reported a change); `BUGS.md: "<title>" (closed)` (AX-11: `(documented)`); `GAPS4: AX-7 Tracked`.
