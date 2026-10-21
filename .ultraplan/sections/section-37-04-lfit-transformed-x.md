# Section 37-04: lfit/lfitci on xlog/xtransform()

> Part of: WP-37 (Statistical and computed layers) · Items: stat:PT-12 · Risk: yellow · Batch: 37.1 · Depends on: none · Blocks: none · Tasks: 4, 1 commit · Case-id prefix: Q3704

## Overview

**What is wrong today.** The audit (package 12, stat:PT-12, audit :652-654; appendix :1125-1130): "xlog/xtransform() on lfit/lfitci are noted and the straight line drawn; twoway fits the transformed x." twoway's `twoway_lfit_parse.class` (:75-88) passes `xtrans()` to `twoway__lfit_serset`, which regresses y on the transformed x (`VarTrans`) and draws the fitted values over the untransformed x: `lfit mpg weight, xtransform(X^2) n(7)` draws 27.499, 25.558, 23.123, ... (curved); `lfitci mpg weight, xlog` draws the log-x fit and band. dash draws the plain straight line with "ignoring unsupported option(s): xlog". Re-measured 20oct2026: `twoway lfit mpg weight, xtransform(X^2) n(5)`, `lfit ..., xlog n(5)` and `lfitci ..., xlog n(5)` are all rc 0.

**Measured for the other fits and under by() (20oct2026, console StataNow 19.5, one `scripts/stata_slot.sh` run; DECISIONS A-12 asks for it).** `twoway qfit`, `qfitci` and `fpfitci` with `xlog` or `xtransform(X^2)` are rc 0 and their sersets equal those of the same command without the option (qfit's serset mean 19.9523376560211 either way; fpfitci 21.3448237031698): twoway accepts both and draws the fit without them -- `twoway_qfit_parse.class` inherits lfit's parser and its serset call passes no `xtrans()`, and its own check reads `.trans`, which nothing sets. `twoway fpfit` refuses them: `option xlog not allowed`, r(198), and `option xtransform() not allowed`, r(198). `twoway lfit mpg weight, xlog by(foreign)` and `lfitci mpg weight, xtransform(X^2) by(foreign)` are rc 0: twoway fits each panel's own rows. xtransform() text reaching twoway by value: `X+$y` (the dollar sign in a local) r(198) "invalid syntax"; `X;` r(198) "weight; invalid name"; `X+"a"` r(109) "type mismatch".

**What will be true after.** On lfit and lfitci, `xlog` and `xtransform(exp)` are drawn as twoway draws them: dash runs twoway's own generator, `twoway__lfit_serset` with `xtrans()`, at registration through the existing `_dash_fit_points` route (the route estopts()/predopts()/estcmd() take since WP-31 C4), so the points are Stata's; with either option and no `n()`, 100 points are drawn, as twoway's parse sets them; under `by()` the fit is made once per panel over that panel's rows, as twoway makes it (DECISIONS A-12, REVIEW R3-6), and the renderers draw each panel's own points. The same per-panel route takes every fit Stata computes at registration under `by()`: a fit with estopts(), predopts() or estcmd(), which today is fitted once over the whole sample and drawn in every panel, is fitted in each panel from its own rows, as twoway fits it (A-12's rule; Q3704-7). On qfit, qfitci and fpfitci the two options are taken silently and the fit is drawn without them, as twoway draws it; on fpfit they are refused with twoway's words (P11, P4-7). The renderers draw Stata's points and the saved page marks the layer stale after a filter move, as it marks every Stata-computed fit (WP-32); the served app does the same. The two options leave the Unsupported list.

**Test order and commit rule.** Task 37-04-01 writes the failing tests and the S04 block and saves the failure text, no commit; 37-04-02 routes the options on the Stata side (flat and per panel) and drops the notes; 37-04-03 makes both renderers pick each panel's points; 37-04-04 flips pins, edits the help and Unsupported list, closes the item and commits once with the subject ending `(WP-37 stat:PT-12)`.

### Section decisions

- **D-37-04.a Stata computes, dash draws.** No transform is evaluated in Python or JavaScript: `xtransform()` is a Stata expression, and no user text reaches `eval`/`exec` (M13). The points come from `twoway__lfit_serset` exactly as twoway draws them.
- **D-37-04.b After a move.** The layer takes the "fit" stale cue (`_frozen_layer_tag`'s forced kind for a layer drawn from Stata's points, dash_render.py:62710-62727) in the saved page, and the served app's `_dash_points_stale_follow` (WP-32); a by() panel's layer is judged against its own panel's `nobs`. No JS is written (no refit is possible without evaluating the user's expression); the manifest's JS column says yes, and none is needed (reported, REVIEW R3-37).
- **D-37-04.c Scope, as twoway (DECISIONS A-12, P11, P4-7).** lfit and lfitci draw the fit on the transformed x, flat and per by() panel. qfit, qfitci and fpfitci take `xlog` and `xtransform()` with no note and draw the fit without them, which is the picture twoway draws (measured). fpfit refuses them with twoway's rc and words (measured; Q3704-4 pins dash beside twoway).
- **D-37-04.d xlog wins.** As twoway's parse does (`.xtrans = "ln(X)"` after `.xtrans = xtransform`), `xlog` with `xtransform()` uses `ln(X)`.
- **D-37-04.e Per panel, keyed by the panel's values (DECISIONS A-12).** Under by(), for every fit `_dash_fit_points` computes -- lfit/lfitci with xlog or xtransform(), and any fit type of `_ft_types` with estopts(), predopts() or estcmd() -- `_dash_process_segment` runs the generator once per by() group of the plot's sample -- the group's rows, the by() variables present unless `missing` -- and once over the whole sample for the Total panel under `total`, and writes `{"panels": [{"key": [<the group's by() values>], "points": <points>}, ...], "total": <points>}`. Both renderers give each panel the entry whose key equals its own by() values (`_dash_fit_panel_spec`). The key is the values, not the panel's place: the renderers leave out panels twoway leaves out (`_dash_by_panel_dropped`) after grouping, so a place counted in Stata could name another panel; C12's function points (keyed by place) are unchanged.
- **D-37-04.f No check of dash's own on the expression (REVIEW R3-23).** The `xtransform()` text is read only by value (`st_global("s(xtransform)")`) and handed on only through `macval()`; dash never puts it in a `mata:` line, a `display`, an `=` expression or the spec. twoway's generator therefore receives exactly the text twoway's parse would hand it and answers it as twoway does (measured above); Q3704-6 pins each of those answers beside twoway's. If a text class answers differently in dash (a backtick text is the one not measured above), the task adds `xtransform` to `_dash_fit_opts_check`'s `_dash_fit_opt_bad` loop (dash.ado:10508-10514) with twoway's measured rc and first line for that class, and the hand-back says so.

## Risk: [yellow] -- a new Stata-side generator call on two fit types, and a per-panel route

**Why.** `_dash_fit_points` runs twoway's estimation at registration; a mistake in the gate sends every lfit through it or breaks the estopts route; a key mismatch draws a panel's layer empty.

**Risk factors.** 1. The `_ft_on` gate (dash.ado:7219-7220) fires only when estopts()/predopts()/estcmd() are given. 2. `xtransform()` holds an expression: it must reach the generator by value, never re-expanded. 3. lfitci's band (`std`) must come with the points. 4. `_dash_process_segment` is a hot block in this batch (37-01 edits its per-type check block :6826-6930). 5. A panel's key in Stata and in the renderer must agree for numbers, strings and missing values (`by(, missing)`). 6. `_generate_app_source_body` is R12-hot.

**Mitigation.** 1. The gate gains one disjunct for lfit/lfitci with either option; the estopts cases keep their tests (test_fit_options*.py, U-C4 cases) green. 2. The value is read with `st_global("s(xtransform)")` into a local and passed as `xtrans(`macval(...)')`, as estopts() is passed. 3. `_dash_fit_points` already sets `std` for lfitci (`_fp_ci`). 4. This section edits only :7210-7245 of `_dash_process_segment` and `_dash_fit_points` (:10583-10650); 37-01 edits :6826-6930 and the call at :8593. 5. Numbers are written by `_dash_json_number17` (17 significant digits, read back exactly as Python floats), strings through `_dash_json_escape`, missing values as their code text (".", ".a" ... ".z"); TestThePanels pins numeric, string and `by(rep78, missing)` keys in both modes. 6. This section is batch 37.1's only editor of `_generate_app_source_body` (37-01 and 37-05 do not touch it); reported, as the manifest's Owns omits it.

## Dependencies

- **Depends on:** none. It builds on 35-08 (WP-35): the extended-missing code column is named through 35-08's per-spec accessor (`_dash_code_prefix(spec)`), not the module constant `_DASH_CODE_PREFIX`.
- **Blocks:** none.
- **Parallel batch:** 37.1 with 37-01 and 37-05; merge order 37-01, 37-04, 37-05.
- **Can run with:** both (disjoint lines of `_dash_process_segment`; no `map_contour`; 37-05 is help only and does not edit the Unsupported "Type-specific options" paragraph or the `{ul:Fit options.}` paragraph, dash.sthlp:3546-3579, that this section edits; 37-05's lpolyci paragraph is :4011-4040).

## Evidence

### dash today (re-read)

- Declared and noted: dash_parse.mata:8142 `("xlog", "xlog", "0", "lfit qfit lfitci qfitci fpfitci", "0")`, :8145 `("xtransform", "xt", "1", "lfit qfit lfitci qfitci fpfitci", "0")` (the takes table: the types each option is valid on; fpfit is not among them); repeat-scan rows :7675. The note "ignoring unsupported option(s): xlog" comes from the unsupported list (read where xlog lands with `grep -n '"xlog"\|xtransform' dash.ado dash_parse.mata`).
- The estopts route: `_dash_process_segment` :7214-7240 (`local _ft_types "lfit qfit lfitci qfitci fpfit fpfitci"`; `_ft_on` = `$dash__ftsc` set and estopts/predopts/estcmd given; then `_dash_fit_points `yvar' `xvar' `macval(_psq)' `_ft_w', sc() ptype() estopts() predopts() estcmd() n() range() level() std() atobs`). `_psq` (:6404-6410) is the plot's sample with the graph's qualifier; `_ss_by` (:6862) the by() text. `_dash_by_parts <scalar>` (:5536-5571) c_locals `_by_vars`, `_by_miss` and `_by_total`.
- `_dash_fit_points` (:10583): `syntax varlist(min=2 max=2 numeric ts) [if] [in] [fw aw pw iw], SC(name) PType(name) [ESTopts(string asis) PREDopts(string asis) ESTCmd(string asis) N(string) RAnge(string) ATObs LEVel(string) STD(string)]`; `local pts 100`, `if "`ptype'" == "lfit" local pts 3`; the lfit/qfit generator call (`local gen twoway__lfit_serset` ... `capture noisily `gen', sersetname(__dash_fit_ss) x(`x') y(`y') ...`, :10627-10632); the points into `sc` by `_dash_fit_points_json(nobs)`.
- `_dash_fit_opts_check` (:10488-10556): the `_dash_fit_opt_bad` loop over estopts, predopts, estcmd (:10508-10514).
- The renderer: `_dash_attach_function_points` puts a fit layer's points in its options (dash_render.py:5119-5180, `_DASH_FIT_POINT_TYPES` :5115); `_dash_fit_points_of` (:26876) reads a flat `{"x","y"[,"lo","hi"],"nobs"}` and returns False for anything else (a `panels` object reaching it unpicked draws the layer empty with a note); `_fit_points_draw` (:20064-20140) draws them and marks a layer stale when it has fewer rows than `nobs`; `_frozen_layer_tag` forces kind "fit" (:62710-62727). by() panels: saved `_build_sources_and_figures` makes the facet entries (unlinked :64962-64980, linked :64905-64921; `self._facet_total_keys` initialised with a `hasattr` guard at :64770-64771) and the figure loop calls `_dash_fn_panel_spec(g_panel, panel_idx_r)` (:65041); served, the literals `_g_pan = _dash_fn_panel_spec(g, _fi)` and `_g_pan = _dash_fn_panel_spec(_g_tot, _fi)` (:70830-70834), the panel's frame `_gdf`, the graph options `go`; served functions tuple entry `"_dash_fn_panel_spec",` (:67800). `_dash_by_groups` (:5418) groups both modes, a coded missing group keyed by its code text.
- Help: dash.sthlp:6548-6556 (Unsupported, "Type-specific options": "{opt xlog} and {opt xtransform(exp)} on {cmd:lfit} and the other fits, which fit against a transformed {it:x}; ... draws each plot as it draws it without them, and names them").

### twoway

`/Applications/StataNow/ado/base/t/twoway_lfit_parse.class:50-88`: `XTransform(string) XLOG`, `if xtransform != "" | xlog != "" { if n == 3 local n 100 }`, `.xtrans = xtransform`, `if xlog != "" .xtrans = "ln(X)"`, passed at :145; `twoway__lfit_serset.ado:1-30`: `XTRANS(string)` → `VarTrans x regx xtrans`, `regress y regx`; lfitci's class :97 the same. `twoway_qfit_parse.class` inherits `twoway_lfit_parse`, checks `.trans` (never set) and passes no `xtrans()` to `twoway__qfit_serset`. `twoway_fpfit_parse.class` inherits `twoway_yxview_parse` and declares neither option.

### Pins today

- Any test asserting the xlog/xtransform note on any fit (`grep -rn 'xtransform\|xlog' test/*.py test/*.cscript`): flip for lfit, lfitci, qfit, qfitci and fpfitci; an fpfit refusal pin stays if it already gives twoway's words.
- test/test_help_conformance.py's Unsupported pins (`_unsupported_section`, the count pin at :807): the "Type-specific options" paragraph loses the xlog/xtransform clause.

## User stories

- US-37-04.1 As a Stata user with an existing twoway command, I want `lfit mpg weight, xlog` and `lfitci mpg weight, xtransform(X^2)` to draw twoway's curve, alone or under by(), so that a fit on a transformed x looks as it does in Stata.
- US-37-04.2 As a Stata user, I want `qfit ..., xlog` drawn as twoway draws it without a note, and `fpfit ..., xlog` refused as twoway refuses it, so that the syntax is twoway's.
- US-37-04.3 As a Stata user with an existing twoway command, I want `lfit mpg weight, estopts(nocons) by(foreign)` to draw each panel's own fit, as twoway does, so that a panel never shows a line fitted to another panel's rows.

## Business requirements

- BR-37-04.1 On lfit and lfitci, `xlog` and `xtransform(exp)` draw twoway's points (and band), with no note, in both modes; under by() each panel draws the fit of its own rows, and the Total panel the fit of all of them.
- BR-37-04.2 With either option and no `n()`, 100 points are drawn; with `n()`, that many.
- BR-37-04.3 After a filter move the layer shows the stale cue, as every Stata-computed fit does.
- BR-37-04.4 On qfit, qfitci and fpfitci the options draw what the command draws without them, with no note; on fpfit they are refused with twoway's return code and words.
- BR-37-04.5 An xtransform() expression twoway refuses is refused with twoway's return code and words.
- BR-37-04.6 The help's Unsupported list no longer names the two options.
- BR-37-04.7 A fit with estopts(), predopts() or estcmd() under by() draws, in each panel, the fit of that panel's own rows, and in the Total panel the fit of all of them, in both modes.

## Technical requirements

- **TR-37-04.1 `_dash_fit_points`** (dash.ado:10583): add `XTRans(string asis)` to the option list; after `if "`n'" != "" local pts `n'` add `if `"`macval(xtrans)'"' != "" & "`n'" == "" local pts 100` with the comment `// twoway_lfit_parse.class: xlog or xtransform() with the default n() draws 100 points (WP-37 stat:PT-12).`; in the `twoway__lfit_serset` call add `xtrans(`macval(xtrans)')` -- only when `"`gen'" == "twoway__lfit_serset"` (`twoway__qfit_serset` is never given it).
- **TR-37-04.2 The gate** (`_dash_process_segment` :7219-7240): after `mata: st_local("_ft_on", ...)` add
  ```stata
  // xlog and xtransform() on lfit and lfitci: twoway's generator fits the
  // transformed x (twoway_lfit_parse.class; WP-37 stat:PT-12).  xlog wins.
  local _ft_x ""
  if inlist("`ptype'", "lfit", "lfitci") {
      mata: st_local("_ft_x", st_global("s(xtransform)"))
      mata: st_local("_ft_xl", st_global("s(xlog)"))
      if "`_ft_xl'" != "" local _ft_x "ln(X)"
      mata: st_local("_ft_on", strofreal(`_ft_on' | (st_global("dash__ftsc") != "" & st_local("_ft_x") != "")))
  }
  ```
  and pass `xtrans(`macval(_ft_x)')` on the `_dash_fit_points` line when `_ft_x` is non-empty. Read the exact s() names the parser sets for the two options (`grep -n 'xtransform\|XTRansform\|XLOG' dash.ado`) and use them. When `_ss_by` is non-empty and `_ft_on` is 1 -- for any type of `_ft_types`, with xlog/xtransform() (lfit and lfitci) or with estopts(), predopts() or estcmd() -- the per-panel route of TR-37-04.3 runs instead of the flat call: twoway fits each panel's own rows in every case (DECISIONS A-12; Q3704-5, Q3704-7). Without by() the flat call is unchanged.
- **TR-37-04.3 Per panel** (`_dash_process_segment`, inside the gate, version 19 code):
  ```stata
  // Under by(), twoway fits each panel's own rows (DECISIONS A-12): one
  // fit per by() group of the plot's sample, keyed by the group's values,
  // and the Total panel's over the whole sample (WP-37 stat:PT-12).
  tempname _ft_bt _ft_one _ft_all
  mata: st_strscalar(st_local("_ft_bt"), st_local("_ss_by"))
  _dash_by_parts `_ft_bt'
  tempvar _ft_tu _ft_g
  quietly generate byte `_ft_tu' = 0
  quietly replace `_ft_tu' = 1 `macval(_psq)'
  if !`_by_miss' {
      foreach _v of local _by_vars {
          quietly replace `_ft_tu' = 0 if missing(`_v')
      }
  }
  quietly egen long `_ft_g' = group(`_by_vars') if `_ft_tu', missing
  quietly summarize `_ft_g', meanonly
  local _ft_ng = cond(r(N), r(max), 0)
  mata: st_strscalar(st_local("_ft_all"), "")
  forvalues _gi = 1/`_ft_ng' {
      mata: st_strscalar(st_local("_ft_one"), "")
      capture _dash_fit_points `yvar' `xvar' if `_ft_g' == `_gi' `_ft_w', sc(`_ft_one') ptype(`ptype') estopts(`macval(_ft_e)') predopts(`macval(_ft_p)') estcmd(`macval(_ft_c)') `_ft_o' `_ft_a' xtrans(`macval(_ft_x)')
      if _rc == 0 {
          mata: _dash_fit_panel_add(st_local("_ft_all"), _dash_fit_panel_key(st_local("_by_vars"), st_local("_ft_g"), `_gi'), st_strscalar(st_local("_ft_one")))
      }
  }
  local _ft_tot ""
  if `_by_total' {
      mata: st_strscalar(st_local("_ft_one"), "")
      capture _dash_fit_points `yvar' `xvar' if `_ft_tu' `_ft_w', sc(`_ft_one') ptype(`ptype') estopts(`macval(_ft_e)') predopts(`macval(_ft_p)') estcmd(`macval(_ft_c)') `_ft_o' `_ft_a' xtrans(`macval(_ft_x)')
      if _rc == 0 local _ft_tot 1
  }
  mata: st_strscalar(st_local("_ft_sc"), "{" + char(34) + "panels" + char(34) + ":[" + st_strscalar(st_local("_ft_all")) + "]" + (st_local("_ft_tot") == "1" ? "," + char(34) + "total" + char(34) + ":" + st_strscalar(st_local("_ft_one")) : "") + "}")
  ```
  (`_ft_sc` is the scalar `$dash__ftsc` names, as the flat call fills it. The two calls pass the flat call's options exactly as it passes them, dash.ado:7238-7240 at 090d928 -- `estopts(`macval(_ft_e)') predopts(`macval(_ft_p)') estcmd(`macval(_ft_c)') `_ft_o' `_ft_a'` -- plus `xtrans()`; an empty `_ft_e`, `_ft_p`, `_ft_c` or `_ft_x` passes an empty option, which `_dash_fit_points` reads as not given, as the flat call relies on today.) A panel whose generator fails (one observation: twoway leaves the panel out, and so does the renderer, `_dash_by_panel_dropped`) has no entry. New Mata functions (dash_parse.mata, beside `_dash_fit_points_json`; one `*!` header-index entry each, both directly after the `*!   _dash_fit_points_json(nobs)` entry, dash_parse.mata:185-189 at 090d928, and before `*!   _dash_fit_opt_bad(s)` (:190; re-read); both on one new `_needed` continuation line `        _dash_fit_panel_key _dash_fit_panel_add ///` inserted directly after the `_needed` line that holds `_dash_fit_points_json` (dash.ado:487 at 090d928; re-read), touching no existing line -- 37-01, in the same batch and earlier in its merge order, inserts its line directly before the list's last line (:506), so the two insertions never meet in one cherry-pick hunk, REVIEW R2-22). test/program_coverage_map.py (R6), under `"dash_parse.mata"` directly after the `"_dash_fit_points_json"` entry: `"_dash_fit_panel_key": ("test_wp37_truth.cscript:Q3704-5",),` and `"_dash_fit_panel_add": ("test_wp37_truth.cscript:Q3704-5",),`: `string scalar _dash_fit_panel_key(string scalar vars, string scalar gvar, real scalar gi)` -- `[` + for each variable of `vars`, at the first observation where `gvar == gi`: a string variable `"` + `_dash_json_escape(value)` + `"`; a numeric one `_dash_json_number17(value)` when not missing, else `"` + `strofreal(value)` + `"` (".", ".a" ... ".z") -- joined by `,` + `]`; `void _dash_fit_panel_add(string scalar sc, string scalar key, string scalar pts)` -- appends `{"key":<key>,"points":<pts>}` to the string scalar named `sc`, a comma before every entry but the first. The flat route (no by()) is unchanged.
- **TR-37-04.4 The notes.** Remove xlog and xtransform from the noted options of lfit, lfitci, qfit, qfitci and fpfitci: where the unsupported list is built for a type (find the site that prints "ignoring unsupported option(s)" for a fit and the table rows that feed it), none of the five lists them. Leave the takes-table rows (dash_parse.mata:8142, :8145): fpfit stays off them. Q3704-4 compares fpfit's refusal with twoway's; where dash's rc or first line differs, the takes-table refusal of an option not valid on a type is made to print twoway's line `option xlog not allowed` / `option xtransform() not allowed`, r(198).
- **TR-37-04.5 Both modes: each panel's points** (dash_render.py, two new module functions after `_dash_fn_panel_spec`, standard library and numpy only):
  ```python
  def _dash_by_key_of(df, by_raw, code_prefix=None):
      """The by() values of panel frame *df* as a list, in by() order (WP-37
      stat:PT-12), for _dash_fit_panel_spec: a string as text, a number as
      a float, a missing number as its code text -- the code column
      <code_prefix><name> when it holds one, else "." -- or None when *df*
      has no row."""

  def _dash_fit_panel_spec(g, key, total=False):
      """The graph *g* as one by() panel draws its fit layers (WP-37
      stat:PT-12): a copy whose fit plots carrying {"panels": [...]} points
      carry the entry whose key equals *key* -- strings equal as text,
      numbers as floats, codes as text -- or, with *total*, the "total"
      points; a panel with no entry draws the layer empty
      ({"x": [], "y": [], "nobs": 0}, with "lo"/"hi" for lfitci).  *g*
      itself when no plot carries such points."""
  ```
  `_dash_by_key_of` reads the variables with `_dash_parse_by(by_raw)[0].split()` and the code prefix from 35-08's per-spec accessor at the batch base (`_dash_code_prefix(spec)`; the module constant `_DASH_CODE_PREFIX` at 090d928). Saved: in `_build_sources_and_figures` initialise `self._facet_keys = {}` with the same `hasattr` guard as `_facet_total_keys` (:64770-64771); in both facet loops (unlinked :64974-64979, linked :64913-64918) add `self._facet_keys[fkey] = _dash_by_key_of(group_df, by_raw, _dash_code_prefix(self.master_spec))` (the by() text local of each loop: `by_raw` / `by_raw_lnk2`); in the figure loop, after `g_panel = _dash_fn_panel_spec(g_panel, panel_idx_r)` (:65041) add `g_panel = _dash_fit_panel_spec(g_panel, self._facet_keys.get(fkey), fkey in self._facet_total_keys)`. Served (R2, R12): after the literal `"            _g_pan = _dash_fn_panel_spec(g, _fi)",` add `"            _g_pan = _dash_fit_panel_spec(_g_pan, _dash_by_key_of(_gdf, go.get('by', ''), <the served app's code prefix>), False)",` and after `"                _g_pan = _dash_fn_panel_spec(_g_tot, _fi)",` add `"                _g_pan = _dash_fit_panel_spec(_g_pan, None, True)",` (re-read how the served app names the code prefix after 35-08 and use it); add `"_dash_by_key_of", "_dash_fit_panel_spec",` to the served functions tuple directly after `"_dash_fn_panel_spec",` (:67800; insert, do not reorder). test/function_test_map.py: `"_dash_by_key_of": "test/test_lfit_xtrans.py::TestThePanels::test_the_key_of_a_panel"`, `"_dash_fit_panel_spec": "test/test_lfit_xtrans.py::TestThePanels::test_each_panel_takes_its_own_points"`. `TestTheServedAppCarriesEveryName` must stay green.
- **TR-37-04.6 Help (R3).** dash.sthlp:6548-6556: delete the clause "{opt xlog} and {opt xtransform(exp)} on {cmd:lfit} and the other fits, which fit against a transformed {it:x};" (the paragraph keeps its other options, as the sections before this one left them). The `{phang}{ul:Fit options.}` paragraph of Statistical Layer Options (`{marker smoother_options}`): it starts at dash.sthlp:3546 and ends at :3579 with "{cmd:option estopts() incorrectly specified}, r(198)." at 090d928 (re-read); it is not 37-05's lpolyci paragraph (:4011-4040), which 37-05 edits in this batch. After its last sentence it gains: "{opt xlog} and {opt xtransform(exp)} on {cmd:lfit} and {cmd:lfitci} fit {it:y} on the transformed {it:x} with {cmd:twoway}'s own generator, at 100 points unless {cmd:n()} says otherwise, as {cmd:twoway} draws them; after a filter move the saved page and the served app keep the curve as built and mark it.  On {cmd:qfit}, {cmd:qfitci} and {cmd:fpfitci}, {cmd:twoway} accepts both and draws the fit without them, and so does {cmd:dash}; {cmd:fpfit} refuses them, as {cmd:twoway} does.  Under {cmd:by()} a fit Stata computes -- one with {opt xlog}, {opt xtransform()}, {opt estopts()}, {opt predopts()} or {opt estcmd()} -- is made once in each panel from that panel's rows, and the Total panel's from all of them, as {cmd:twoway} makes it."

## Boundaries

- No change to the estimation of qfit, qfitci, fpfit, fpfitci (D-37-04.c: only their note goes, and fpfit's refusal words if they differ); no JS edit; no new estimator in Python.
- Edit `_dash_process_segment` only at :7210-7245 (R12: 37-01 owns the per-type check block); do not change the flat route of estopts()/predopts()/estcmd() without by() -- under by() they take the per-panel route (TR-37-04.2).
- `_dash_fn_panel_spec` and C12's function points are not changed.

## Stata truth

Live, no fixture (twoway's generator is dash's source of points; the cases show the stored points equal twoway's serset). Block above the marker of test/test_wp37_truth.cscript, after S01 when it is there (R1 order; in this batch the merger keeps S01 before S04):
```
* ==== S04 stat:PT-12: lfit and lfitci on a transformed x ====
```
- Q3704-1: `twoway lfit mpg weight, xtransform(X^2) n(7) nodraw` and its serset (`.Graph.plotregion1.plot1.serset` read through `serset use, clear` under `preserve`, as test_wp31_truth.cscript's U-C4 cases read a fit's serset; re-read one there) beside `dash lfit mpg weight, xtransform(X^2) n(7) name(q4a)` whose stored points (`function_points` table entry 1 in the spec written by `_dash_serve_spec, specpath() datapath()`) hold the same 7 y values to 1e-9.
- Q3704-2: `lfit mpg weight, xlog` (no n()): 100 points, equal to twoway's serset.
- Q3704-3: `lfitci mpg weight, xlog n(5)`: y, lower and upper equal twoway's serset.
- Q3704-4: the log of `dash lfit mpg weight, xlog` holds no `ignoring unsupported option(s)` and no `xlog`; for each of `qfit`, `qfitci` and `fpfitci` with `xlog` and with `xtransform(X^2)`: `capture noisily twoway <cmd>, nodraw` rc 0 beside `capture noisily dash <cmd>, saving(<tmp>.html, replace)` rc 0 with no note (no `nobrowser` on the one-line form: it is an option of `dash build` and `dash serve` only, and the one-line form refuses it, r(198); saving() keeps the browser shut), and the page's layer data equals that of the same dash command without the option (a `python:` helper over the two pages); for `fpfit` with each option: dash's rc and first message line equal twoway's (`option xlog not allowed` / `option xtransform() not allowed`, r(198)).
- Q3704-5: by() (DECISIONS A-12, REVIEW R3-6): `lfit mpg weight, xlog by(foreign)` and `lfitci mpg weight, xtransform(X^2) n(5) by(foreign, total)`: after `serset drop _all`, `twoway <cmd> nodraw` and each panel's serset read in order (`serset set <s>`, as test_wp31_truth.cscript S46 U46-04 reads them), beside `dash <cmd> name(q4p)` and `_dash_serve_spec`: each panel's stored points (the `panels` entry whose key is the panel's `foreign` value, and `total`) equal that panel's serset to 1e-9.
- Q3704-6: xtransform() text by value (D-37-04.f): for `X+` followed by `char(36)` and `y`, `X;`, `X+"a"`, and `X+` followed by `char(96)`, `y` and `char(39)`, each built in a local so the do-file expands nothing: `capture noisily twoway lfit mpg weight, xtransform(<text>) nodraw` and `capture noisily dash lfit mpg weight, xtransform(<text>) name(q4x, replace)` give the same rc and first message line.
- Q3704-7: estopts() under by() (DECISIONS A-12): `lfit mpg weight, estopts(nocons) by(foreign)`: after `serset drop _all`, `twoway lfit mpg weight, estopts(nocons) by(foreign) nodraw` and each panel's serset read in order, as Q3704-5 reads them, beside `dash lfit mpg weight, estopts(nocons) by(foreign) name(q4e)` and `_dash_serve_spec`: each panel's stored points (the `panels` entry whose key is the panel's `foreign` value) equal that panel's serset to 1e-9, and the two panels' points differ from each other (one whole-sample fit drawn twice fails this).

## TDD test stubs

Failing first (task 01):
- Test: test/test_lfit_xtrans.py::TestTheRoute::test_the_gate_covers_xlog_and_xtransform (dash.ado `_dash_process_segment` text: the `_ft_x` block and the `xtrans()` pass), ::test_fit_points_takes_xtrans (`_dash_fit_points`' syntax has `XTRans(` and the 100-point default line), ::test_under_by_the_fit_is_per_panel (the gate's by() branch calls `_dash_fit_panel_key` and writes `panels`), ::test_estopts_under_by_is_per_panel (the by() branch is taken on `_ft_on` alone, so an estopts()/predopts()/estcmd() fit under by() reaches it; red: the flat call runs), ::test_no_fit_notes_the_options (no fit type's noted list holds xlog or xtransform).
- Test: test/test_lfit_xtrans.py::TestTheDrawing::test_points_are_drawn[std|srv] (a spec whose lfit layer carries `xtransform` and `points` from a hand-written table drawn as given in both modes -- guard: `_fit_points_draw` exists), ::test_no_note_for_lfit[std|srv] (the warnings of rendering an lfit with `xlog` and points hold no "xlog").
- Test: test/test_lfit_xtrans.py::TestThePanels::test_each_panel_takes_its_own_points[std|srv] (a by(foreign) spec whose lfit layer carries `{"panels": [{"key": [0], "points": A}, {"key": [1], "points": B}]}`: panel 0's line is A, panel 1's B; red: the layer is drawn empty with the "cannot be read" note), ::test_the_total_panel[std|srv] (`by(foreign, total)` with a `total` entry), ::test_a_string_and_a_missing_key[std|srv] (a string by() variable, and `by(rep78, missing)` with a key `["."]`), ::test_the_key_of_a_panel (`_dash_by_key_of` on frames with a number, a string, a NaN with and without a code column), ::test_a_panel_with_no_entry_is_empty.
- Test: test/test_lfit_xtrans.py::TestTheHelp::test_unsupported_drops_the_options, ::test_the_lfit_paragraph.
- cscript: Q3704-1..7.
- Pins: nodes asserting the xlog/xtransform note on any fit, and any node asserting that an estopts()/predopts()/estcmd() fit under by() draws one whole-sample fit in every panel (task 01 lists both; at 090d928 `grep -rn 'estopts\|predopts\|estcmd' test/*.py test/*.cscript | grep 'by('` finds none).
- Parity: `CORPUS` entries `_case("stat:PT-12: lfit xlog with Stata's points", [plot_for("lfit", {"xlog": "xlog", "points": {...}})])` and `_case("stat:PT-12: lfit xlog per by() panel", [plot_for("lfit", {"xlog": "xlog", "points": {"panels": [...]}})], go={"by": "foreign"})` using the `points` table shape `_dash_fit_points_of` reads (R8).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| routed through twoway's generator | cscript Q3704-1..3 (twoway serset beside dash) | -- | saved and served draw the same points |
| per by() panel and the Total panel, estopts() under by() | cscript Q3704-5, Q3704-7; pytest TestThePanels | -- | yes |
| no note on the five fits; fpfit refused as twoway | cscript Q3704-4, pytest TestTheDrawing | -- | yes |
| xtransform() text answered as twoway | cscript Q3704-6 | -- | n/a |
| wiring | pytest TestTheRoute | -- | n/a |
| help | pytest TestTheHelp | -- | n/a |
| parity | two CORPUS entries | -- | yes |
| no plain stat:PT-12 ledger or known-differences row; guard verdicts unchanged or regenerated | pytest test_corpus_ledger.py; `python3 test/known_differences.py stat:PT-12` and its hygiene command; S09 block of test_wp33_truth.cscript (`WP33_ONLY=S09`) | corpus_ledger.json, corpus_guard_truth.json | n/a |

- AC-37-04.1 Q3704-1..3, Q3704-5 and Q3704-7 match twoway's sersets to 1e-9; Q3704-4 and Q3704-6 hold.
- AC-37-04.2 Each by() panel draws its own fit in both modes, the Total panel the whole sample's.

## Tasks

**Commit boundary.** One commit by 37-04-04, subject `Fit lfit and lfitci on a transformed x with twoway's own generator, per by() panel (WP-37 stat:PT-12)`, staging dash.ado, dash_parse.mata, dash_render.py, dash.sthlp, test/test_lfit_xtrans.py, test/test_mode_parity.py, test/function_test_map.py, test/program_coverage_map.py (the two Mata functions' entries), the flipped pins, the S04 block, TWOWAY_COVERAGE_AUDIT.md, BUGS.md, GAPS4.md, CHANGELOG.md, test/test_tracking_documents.py, plus scripts/corpus/ledger.tsv and test/fixtures/corpus_ledger.json (and test/fixtures/corpus_guard_truth.json) when 37-04-04's ledger step changes them and each test file whose `*_KNOWN` or `*_DELIBERATE` table its known-differences step edits (BRIEF "The corpus ledger and the known-differences tables"). `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp37-s04` (BRIEF "Pull form": every command names the worktree by this absolute path; `scripts/stata_slot.sh` runs `cd <scratch>` before Stata starts, so a relative path is not found).

<task type="auto" id="37-04-01">
  <name>Write the failing transformed-x tests</name>
  <files>test/test_lfit_xtrans.py, test/test_wp37_truth.cscript</files>
  <action><![CDATA[
    In $WT, re-read dash.ado:6400-6412, :6860-6864, :7205-7245, :10488-10650 and dash_render.py:5115-5180, :26876-26930, :64760-64980, :65030-65045, :67795-67805 and :70815-70840; find the s() names of xlog and xtransform, the site of the "ignoring unsupported option(s)" note for fits, and 35-08's code-prefix accessor (`grep -n 'def _dash_code_prefix' dash_render.py`); run `grep -rn 'xtransform\|xlog' test/*.py test/*.cscript > <scratch>/37-04-pins.txt` and append `grep -rn 'estopts\|predopts\|estcmd' test/*.py test/*.cscript | grep 'by('` to it. Run `node .gitnexus/run.cjs impact "<name>" --direction upstream --repo .` for `_dash_process_segment`, `_dash_fit_points`, `_dash_fit_opts_check`, `_dash_fn_panel_spec`, `_build_sources_and_figures` and `_generate_app_source_body`, writing callers and risk to `<scratch>/37-04/anchors.txt` (HIGH, CRITICAL or UNKNOWN named in the hand-back; an UNKNOWN confirmed with `grep -n` before editing; REVIEW R3-17). Create test/test_lfit_xtrans.py with the classes of the stubs (new helpers reached with `getattr` inside each test, so a tree without them fails on an assertion). Append the S04 block (Q3704-1..7) to test/test_wp37_truth.cscript above the marker. Run `python3 -m pytest test/test_lfit_xtrans.py -q -n0 -p no:cacheprovider -rf > <scratch>/37-04-01.log` and S04 through the driver (`WP37_ONLY=S04`); save failing nodes and FAIL lines to `<scratch>/37-04-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/37-04-01.log` is at least 11 (TestTheRoute 5, TestThePanels in both modes, TestTheHelp 2); `grep -c "Q3704-[1-57] FAIL" <scratch>/run_test_wp37_truth.log` is at least 5 (dash draws the straight line, notes xlog, and fits under by() once, with xlog and with estopts()); the Q3704-6 lines are recorded in the failure file whatever they say; `test -s <scratch>/37-04-01-failure.txt`.]]></verify>
  <done>The transformed-x, per-panel and refusal tests and certification cases existed and were shown failing against the unmodified tree, beside twoway's measured sersets and answers.</done>
</task>

<task type="auto" id="37-04-02">
  <name>Route xlog and xtransform through Stata</name>
  <files>dash.ado, dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-37-04.1 (`_dash_fit_points`: `XTRans()`, the 100-point default, `xtrans()` on the lfit generator only), TR-37-04.2 (the `_ft_x` block and the `xtrans()` argument), TR-37-04.3 (the per-panel route under by() for every `_ft_on` fit, `_dash_fit_panel_key` and `_dash_fit_panel_add` in dash_parse.mata with their header-index entries after `_dash_fit_points_json`'s, their own `_needed` line after the line holding `_dash_fit_points_json`, and their two program_coverage_map.py entries) and TR-37-04.4 (no fit type notes the two options; fpfit's refusal in twoway's words if Q3704-4 showed it differs). If Q3704-6 showed a text class answered differently from twoway, apply D-37-04.f's fallback in `_dash_fit_opts_check` with twoway's measured rc and line. Run `python3 -m pytest test/test_lfit_xtrans.py::TestTheRoute test/test_fit_options*.py test/test_statistical_helpers.py test/test_program_coverage_map.py test/test_file_headers.py -q -n0 -p no:cacheprovider` and S04's Q3704-1..4 and -6 through the driver.
  ]]></action>
  <verify><![CDATA[TestTheRoute passes; the fit-options tests pass; `grep -c "Q3704-[12346] PASS" <scratch>/run_test_wp37_truth.log` prints 5; test_program_coverage_map.py passes; `diff <(git show HEAD:dash.ado | sed -n '/^    local _needed /,/[^\/]$/p') <(sed -n '/^    local _needed /,/[^\/]$/p' dash.ado) | grep -c '^<'` prints 0 (no base line of the `_needed` list is removed or changed; the check reads the list alone, since this task edits the `_dash_fit_points` call at dash.ado:7238-7240) and the same command with `grep -c '^>'` prints 1 (the section's one new continuation line).]]></verify>
  <done>lfit and lfitci with xlog or xtransform() stored twoway's own fitted points and band, per by() panel under by(), the other fits took the options as twoway does, and fpfit refused them in twoway's words.</done>
</task>

<task type="auto" id="37-04-03">
  <name>Draw each panel's own points</name>
  <files>dash_render.py, test/function_test_map.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Add `_dash_by_key_of` and `_dash_fit_panel_spec` after `_dash_fn_panel_spec` (TR-37-04.5); initialise and fill `self._facet_keys` in `_build_sources_and_figures`'s two facet loops and call `_dash_fit_panel_spec` in the saved figure loop; add the two served literals and the two served functions-tuple names after `"_dash_fn_panel_spec",`; add the function_test_map.py entries and the two CORPUS entries after the last lfit entry. Run `python3 -m pytest test/test_lfit_xtrans.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py test/test_by_*.py -k "fn_panel or fit or lfit" -q -n0 -p no:cacheprovider`, `python3 -m pytest test/test_mode_parity.py -k "stat:PT-12" -q -n0 -p no:cacheprovider`, and S04's Q3704-5 and Q3704-7 through the driver.
  ]]></action>
  <verify><![CDATA[test_lfit_xtrans.py passes but TestTheHelp (37-04-04); TestTheServedAppCarriesEveryName and test_function_test_map.py pass; the parity run's last line reads `<n> passed in ...` with no `failed` or `error`; `grep -c "Q3704-[1-7] PASS" <scratch>/run_test_wp37_truth.log` prints 7.]]></verify>
  <done>Both renderers drew each by() panel's own transformed-x fit, the Total panel's over every row, and a panel with no entry empty.</done>
</task>

<task type="auto" id="37-04-04">
  <name>Flip notes, fix the help, commit</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Flip the note pins listed in `<scratch>/37-04-pins.txt` in place with `Flipped (WP-37 stat:PT-12)` comments; apply TR-37-04.6; run `python3 -m pytest test/test_lfit_xtrans.py test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider` and through the driver test_statistical_options.cscript, test_option_surface.cscript and S04. Close the BUGS.md entry 33-01 opened for stat:PT-12 (`grep -n 'WP-37 section 37-04 has not landed' BUGS.md`) in PD-4's closed form (both modes; Pinned by test/test_lfit_xtrans.py::TestThePanels, Q3704-1..7); Tracked line `commit pending`; delete stat:PT-12 from `GAPS4_OPEN`; CHANGELOG `### Fixed in WP-37`: `- lfit and lfitci with xlog or xtransform() drew a straight line and named the option; they draw twoway's fit on the transformed x, once in each by() panel, and qfit, qfitci and fpfitci take the two options without a note, as twoway does (WP-37, stat:PT-12)` and its own line `- lfit mpg weight, estopts(nocons) by(foreign) (and every fit with estopts(), predopts() or estcmd() under by()) drew the whole sample's fit in each panel; each panel draws the fit of its own rows, as twoway does (WP-37, stat:PT-12)`; append to TWOWAY_COVERAGE_AUDIT.md's lfit and lfitci rows (:87, :90, re-read) `[WP-37 stat:PT-12: corrected -- xlog and xtransform() fit the transformed x, per by() panel]`. The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h): (1) run `awk -F'\t' '$1 == "stat:PT-12" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the item's plain rows; a `stat:PT-12 (documented)` or `stat:PT-12 (residual)` row stays, A-10), rerun `python3 scripts/corpus/ledger.py` (33-05; no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py stat:PT-12` (33-10) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion dict 33-10 names for it (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`, `ABBREV_DELIBERATE` in test/test_abbreviations.py for `ABBREV_KNOWN`, and beside 33-11..33-13's tables `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n); no ruling of this section keeps one, so none is expected: qfit, qfitci and fpfitci draw as twoway draws them (D-37-04.c) -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes, and stage each table file the step edited, by the path the printed row names; (3) run the corpus guard block (`WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do`, the driver of BRIEF "Running one cscript" written for test/test_wp33_truth.cscript with `<repo>` = `$WT`) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes), and put each Q3309-1 message and the fixture's `Fixture:` line in the commit body (a worse verdict this item's change does not explain is a regression: fix the code first, CLAUDE.md rule 2). Before committing, in `$WT`: `git pull --ff-only . main` (CLAUDE.md rule 4; `Already up to date.` at the batch base -- if it refuses, stop and report to the orchestrator, never a merge commit on a section branch) and `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; HIGH or CRITICAL risk named in the hand-back; REVIEW R3-17). Grep the message for `claude|anthropic`, commit, grep again.
  ]]></action>
  <verify><![CDATA[The pytest run's last line reads `<n> passed in ...` with no `failed` or `error`; each driver log ends with its pass line; `git log -1 --format=%s | grep -c "(WP-37 stat:PT-12)"` prints 1; `git show HEAD -- CHANGELOG.md | grep -c '^+.*(WP-37, stat:PT-12)'` prints 2; `grep -c "stat:PT-12 Tracked:\*\* Closed in WP-37.*commit pending" GAPS4.md` prints 1; `awk -F'\t' '$1 == "stat:PT-12"' scripts/corpus/ledger.tsv | wc -l` prints 0 and test/test_corpus_ledger.py passes; `python3 test/known_differences.py stat:PT-12` prints no `<file>:<line>` row and the hygiene command it prints passes; the S09 guard block ends with its pass line.]]></verify>
  <done>stat:PT-12 was closed: lfit and lfitci on a transformed x drew twoway's curve alone and per by() panel, the other fits took the options as twoway does, the help and Unsupported list said so, no ledger or known-differences row named stat:PT-12 alone, and the commit landed on wp37-s04.</done>
</task>

## Section completion criteria

- `_dash_fit_points` takes `xtrans()`; the gate sends lfit/lfitci with xlog or xtransform() through it; under by() every fit it computes (estopts()/predopts()/estcmd() included) takes the per-panel route; `_dash_fit_panel_key`, `_dash_fit_panel_add`, `_dash_by_key_of` and `_dash_fit_panel_spec` exist, mapped, served where they must be; no fit notes the two options; fpfit refuses them as twoway does.
- Q3704-1..7 pass; BUGS/GAPS4/CHANGELOG (two lines)/GAPS4_OPEN and the coverage-audit rows updated in the one commit.
- No plain `stat:PT-12` row is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table (`python3 test/known_differences.py stat:PT-12` prints none); corpus_ledger.json is regenerated by `scripts/corpus/ledger.py`; test/test_corpus_ledger.py, the hygiene command and the S09 guard block pass; corpus_guard_truth.json is regenerated by its extract script if Q3309-1 reported any change for a guard example.

## Notes

- **Traps.** (1) The generator leaves s() empty: the gate reads the s() values before the call (as :7213-7216 says), and the per-panel loop reads nothing from s() after its first generator call. (2) `xtransform(X^2)` holds `^`: never put it inside double quotes in a `mata:` line; read it with `st_global`. (3) lfit's default 3 points becomes 100 only when a transform is given. (4) `egen ..., missing` keeps missing by() values as groups; without by()'s own `missing` those rows are taken out of `_ft_tu` first, as by() leaves them out. (5) A served Total panel is the panel whose index is `_t_idx`; the literal for it passes `True`, the other `False`.
- **GitNexus and rule 4.** `impact` on every function this section edits before its first edit (37-04-01); `git pull --ff-only . main` (in `$WT`, BRIEF "Pull form") and `detect-changes --scope all` before the commit (37-04-04); HIGH, CRITICAL or UNKNOWN risk goes in the hand-back (REVIEW R3-17).
- **Help paragraphs owned (R3):** dash.sthlp:6548-6556 (Unsupported "Type-specific options" clause) and the sentences appended to the `{phang}{ul:Fit options.}` paragraph of Statistical Layer Options (dash.sthlp:3546-3579 at 090d928; re-read) -- not 37-05's lpolyci paragraph, :4011-4040, in the same batch.
- **Merge rules touched:** R1 (S04 after S01), R2 (two names after `"_dash_fn_panel_spec",`, two served literals), R6 (two Mata functions on one new `_needed` line after the `_dash_fit_points_json` line, in the header index after its entry and in program_coverage_map.py), R8 (two CORPUS entries), R9, R12 (`_dash_process_segment`: only :7210-7245; `_generate_app_source_body`: batch 37.1's only editor).
- **Reported to the orchestrator (REVIEW R3-37).** The manifest says JS = yes and Owns "JS fit twins": no JS is written; the section edits `_generate_app_source_body` (R12-hot) and `_build_sources_and_figures`, which Owns does not name. Under by(), estopts(), predopts() and estcmd() take the per-panel route as well (TR-37-04.2, Q3704-7, its own CHANGELOG line): twoway fits each panel's rows whatever the option (A-12's rule), so R3-6's whole-sample flat route under by() is closed here rather than left open.
- **Commit-body line forms:** `Regression: test/test_lfit_xtrans.py::TestTheRoute::test_the_gate_covers_xlog_and_xtransform -- failed at <base> with <text>`; `Regression: test/test_lfit_xtrans.py::TestThePanels::test_each_panel_takes_its_own_points[std] -- failed at <base> with <text>`; `Flipped: <node> -- the xlog note was wrong because twoway fits the transformed x on lfit and lfitci and draws the plain fit on qfit, qfitci and fpfitci`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` and `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` only when 37-04-04's ledger step changed them; `BUGS.md: "<title>" (closed)`; `GAPS4: stat:PT-12 Tracked`; `TWOWAY_COVERAGE_AUDIT.md: lfit and lfitci rows corrected`.
