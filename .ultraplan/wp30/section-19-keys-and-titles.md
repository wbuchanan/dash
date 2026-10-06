# Section 19: Legend keys and default axis titles (P1.16)

> Part of: WP-30 · Items: P1.16 (entry `P1.16`; GAPS2-A13-a..f, GAPS2-C10-a..d, the WP-29 S03/S10 notes) · Risk: yellow · Batch: 7 (merge order S19, S20, S21) · Depends on: 02 · Blocks: 28, 42, 45, 49, 53 · Tasks: 13, 2 commits (keys, then titles) · Case prefix: KT

## Review amendments

- Fixed (major): 19-13's verify grepped `"P1.16"` in `test_tracking_documents.py` for 0, which never holds: `WP30_LISTS` and `WP30_SECTION` keep the key for good (TR-01.2). It now imports the module and checks `WP30_OPEN` lacks the key and `WP30_LISTS` keeps it.
- Fixed (major): `_s19_case` read `${S19_SAME}` and `S19_TK`, but a plain re-prefix of the copied `_s03_app`/`_s03_twoway_keys` writes `S19_SAME_AFTER` and `S19_TW`. The two renames are now stated, and the copy is the whole of :688-880 (imports, `_s03_set`, `_s03_lines` included), which the helpers need.
- Fixed (major, batch boundary): "No function is shared" was false. S19 and S20 both edit dash.ado's `_dash_process_segment` (S19 :3679-3683 and :4309-4312; S20 the `_dash_validate_opts` call at :4121-4126). Recorded as a bounded A139 exception (disjoint hunks about 190 lines apart, S19 lands first, `git apply -3`); index.md fix filed in review-notes/g04.md.
- Fixed (minor): commit 1's body carried a `BUGS.md:` line; TR-01.10 item 7 gives a two-commit section's first commit none. Commit 2's line now quotes Appendix B's title verbatim.
- Checked: anchors E1-E5 (dash_render.py :26695-26706, :26925-26957, :13714-13717, :21438-21444, :21665-21706, :23086-23093; dash.ado :3675-3700, :4296-4312), the copy-list anchors (:32895, :33175, :33228), the 14+1 pinned nodes and the map line :559 all match `c96facd`. `_resolve_level`, `_DEFAULT_LEVEL` and `_dash_histogram_ymode` reach the served app through `_shared_stat_lines` and its constant scan, so TR-19.7's "already copied" holds.
- Checked: M5 (the one message change keeps r(111) in twoway's words), M6 (no note) and register P1.16.1-.5 are obeyed; truth-script block, KT-12 placement (:2854/:2856), map anchor, marker and WP30_OPEN key match section-01.
- Rejected: "19-01 writes four files" (the fixture is the extractor's generated output, listed in 19-06 where it is committed).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:113-120 (P1.16) reads: "lowess, lpoly, mband, mspline and function are all keyed 'Fitted values' … The pc family and scatteri/pci are keyed by the type name. The y title comes from the first layer even when the layers' labels differ. Range types get no y title." GAPS2.md:291-306 (A13, also reported as C10 at :723, :776) adds that twoway draws "no y title when the layers' y labels differ, and 'y1 label/y2 label' for a range plot". The WP-29 notes on the item add that unlabelled multi-layer graphs and second axes take their first layer's name where twoway draws none (a25, k9), and that `yaxis(2)` is titled only from its first layer (S10). The histogram and kdensity keys were closed by WP-29 P0.3 (8d3593e) and stay closed.

Measured at `c96facd` (research `.ultraplan/wp30/research/p1-16.md` §3, 136 probes in four ways; saved page and served app agree on every probe, so this is one text defect shared by both modes, not a mode split):

```
F01 (scatter mpg weight) (lowess mpg weight)
   twoway keys=['Mileage (mpg)', 'lowess mpg weight']  y=[]  x=['Weight (lbs.)']
   dash   keys=['Mileage (mpg)', 'Fitted values']       y=['Mileage (mpg)']  x=['Weight (lbs.)']
F04 (lpoly mpg weight), legend(on)
   twoway keys=['lpoly smooth: Mileage (mpg)']  y=['lpoly smooth: Mileage (mpg)']  x=['lpoly smoothing grid']
   dash   keys=['Fitted values']                y=['Mileage (mpg)']                x=['Weight (lbs.)']
R04 (rcap mpg turn weight), legend(on)
   twoway keys=['Mileage (mpg)/Turn circle (ft.)']  y=['Mileage (mpg)/Turn circle (ft.)']
   dash   keys=['Mileage (mpg)']                    y=[None]
P01 (pcspike mpg weight turn length), legend(on)   twoway key and y 'Mileage (mpg)/Turn circle (ft.)', x 'Weight (lbs.)/Length (in.)'; dash key 'pcspike', no titles
I01 (scatteri 20 3000 25 3500), legend(on)          twoway key 'y', y 'y', x 'x'; dash no legend, no titles
M01 (scatter mpg weight) (scatter price weight)     twoway y=[]; dash y 'Mileage (mpg)'
M07 (scatter mpg weight) (lfit price weight, yaxis(2))   twoway y2 'Fitted values'; dash y2 'Price'
```

At HEAD 52 of 272 mode-probes match twoway's keys and titles. A prototype of this section's design matched 264; the 4 probes left (8 mode-probes) are the measured residuals P2.50 (F31), P2.51 (G25), P2.52 (H01, by drawn side only) and P1.15c (G20).

**After this section**, in the saved page and the served app, before and after any filter move, every layer is keyed in twoway's text (`lowess mpg weight`, `lpoly smooth: Mileage (mpg)`, `Median bands`, `Median spline`, `Predicted mpg`, a function's own name such as `z`, `_y` or `ü`, `L(y1)/L(y2)` for range and pc layers, `y` for scatteri, `y/yb` for pci and pcarrowi), a scatteri-only graph with `legend(on)` draws its key, and each axis — `yaxis(2)` and `xaxis(2)` included, on every by() panel — is titled by default by twoway's measured rule: the label of the first series drawn on that axis when the last series drawn on it has the same label, and no title otherwise. There is no opt-out (register P1.16.3/A58). Text is built raw and compared raw; S09's pass (already landed) and S29's (batch 10) finish it once at the sink.

**Why one section, two commits.** Keys and titles are read from one per-layer table of twoway's series labels (`_dash_layer_series`), so they share a helper and a fixture, but they change different callers: commit 1 the legend (`_dash_legend_key(s)`, `map_scatteri`, the dash.ado function name), commit 2 the axes (`_dash_axis_labels`, HIGH, and `_dash_add_secondary_axes`). Commit 2 depends on commit 1's helper (research §9; A156).

**Test order and commit rule (rule 7, A156).** Two cycles on `wp30-s19`. Commit 1 (keys): 19-01 and 19-02 write and run every key regression test against the unmodified batch-7 base and save `$S/19-P1.16-1-failure.txt` (no commit); 19-03 to 19-07 fix and flip; 19-08 runs the full suite and makes commit 1, leaving the BUGS.md entry, its `WP30_OPEN` key and its CHANGELOG marker in place. Commit 2 (titles): 19-09 writes the title regression tests against the tree commit 1 leaves and saves `$S/19-P1.16-2-failure.txt`; 19-10 to 19-12 fix, flip and document; 19-13 closes the entry, deletes the key, replaces the marker and makes commit 2. No test-only commit exists, and no commit is red.

## Risk: [yellow] — the default text of most multi-layer dashboards changes, through one HIGH helper and a counter-intuitive rule

**Why.** `_dash_axis_labels` is HIGH (`gitnexus impact _dash_axis_labels -d upstream -r dash`: 4 impacted, `_dash_add_secondary_axes` and `_make_figure_body` direct, `_make_figure` and `_build_sources_and_figures` beyond, 3 processes) and is also called from the served template's emitted source (dash_render.py:35139), which the graph does not see. `_glyph_layer_lines` (the served copy lists) is HIGH (4 impacted: `_generate_app_source`, `build`, `main`). Every fit key and most multi-layer titles change text.

**Risk factors.**
1. The first-equals-last rule is not "all layers agree" (GAPS2 A13's plan); a reimplementation from intuition misdraws K01, K03-K05, K07-K11 and F31.
2. A name missing from a served copy list fails only on the served page (RK-9).
3. Pinned tests assert today's text in four files; the research ran 34 files on the prototype but not the full suite (critic 4).
4. The fixture's dash specs are recorded by dash.ado; a spec recorded before the dash.ado change lacks the function name.
5. Later sections build on these helpers (S28, S42, S45, S49, S53); a helper that is not total or reads `type` loosely breaks them.

**Mitigation.**
1. The rule is pinned by a 150-probe twoway fixture whose titles come from twoway's own axis objects, cross-checked against the drawn SVG, and by unit tests over the K01-K11 sequences.
2. G4 (`TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads`) after each copy-list edit, plus `TestTheServedCopy` in the new module.
3. 19-07 and 19-11 run the key- and title-reading files named in the research and re-measure (R9); the full suite runs before each commit.
4. 19-06 regenerates the fixture after the dash.ado edit and verifies every twoway record unchanged.
5. Both helpers are total (unit-tested on malformed input) and key by the spec's `type`; S45 keeps `type` (register P1.16.5/A60).

## Dependencies

- **Depends on: 02.** The new extractor copies S02's path-free root stanza (TR-02.9, A130), and the cscript driver uses S02's `scripts/stata_slot.sh`. S01 provides the open entry `P1.16`, its `WP30_OPEN` key, one marker `<!-- WP-30 P1.16 -->` in the `**WP-30 (drop-in P1, 03oct2026)**` group of `### Results that change`, the S19 stub block of `test/test_wp30_truth.cscript` and the map anchor `# WP-30 S19 (P1.16): Legend keys and default axis titles (P1.16)`. S09 (batch 3) adds `_dash_finish_graph_text`, which finishes this section's text at the sink in both modes.
- **Blocks: 28, 42, 45, 49, 53.** S28 (by() text) and S53 (titles once under by()) call `_dash_axis_default_titles`; S42 (operators) extends `_dash_layer_series` for `L.x` labels; S45 (recast) keys by the original `type`; S49 (horizontal) swaps each layer's series and titles through these helpers (IR-13).
- **Parallel batch: 7**, merge order S19, S20, S21 (S21 red, last).
- **Can run with:** S20 (Stata-only value checks: `_dash_option_rules`, `_dash_validate_opts`, `_dash_fold_mlab`, new `_dash_value_list`/`_dash_mlabel_list`) and S21 (ticker, margin, finishers, `_make_figure_body`, `_generate_app_source`, scheme files). One function is shared, a recorded exception to A139: dash.ado's `_dash_process_segment`, where S19 edits the function branch (:3679-3683) and the function's JSON fields (:4309-4312) and S20 edits only the `_dash_validate_opts` call (:4121-4126). The hunks are disjoint and about 190 lines apart, S19 lands first, and S20's patch applies with `git apply --index -3`; neither edits the other's lines. No other function is shared: S21 edits no key or title helper, and S19 edits none of S21's.

## Evidence

All anchors were re-read at `c96facd` (dash_render.py 37,689 lines, dash.ado 8,487). Batches 1-6 land before this section; the executor re-finds each anchor by symbol at `batch-7-base` and treats the numbers below as approximate.

### E1. Keys: the fit table and the key function (dash_render.py:26695-26706, :26925-26957)

```python
26698  #: has keys ["Mileage (mpg)", "Fitted values"].
26699  _DASH_FIT_TYPES = frozenset({
26700      "lfit", "qfit", "fpfit", "lpoly", "lowess", "mband", "mspline",
26701      "function",
26702  })
26706  _DASH_CI_TYPES = frozenset({"lfitci", "qfitci", "lpolyci", "fpfitci"})
...
26941      var_labels = var_labels or {}
26942      ptype = str(plot.get("type", "")).lower()
26943      if ptype in _DASH_FIT_TYPES or ptype in _DASH_CI_TYPES:
26944          return "Fitted values"
...
26953      yvar = (plot.get("yvar", "") or plot.get("var", "")
26954              or plot.get("yvar1", ""))
26957      return _dash_var_label(var_labels, yvar) if yvar else ptype
```

Range specs carry `yvar1`/`yvar2`/`xvar` and pc specs `y1var`/`x1var`/`y2var`/`x2var` (dash.ado:4296-4308), so a range layer is keyed by its first boundary and a pc layer (no `yvar1`) by its type. Measured at `c96facd` (this pass, `python3 -c` on `dash_render`, auto labels):

```
lowess 'Fitted values'   lpoly 'Fitted values'   mband 'Fitted values'   function 'Fitted values'
rcap {'yvar1':'mpg','yvar2':'turn'} 'Mileage (mpg)'   pcspike 'pcspike'   pci 'pci'   scatteri 'scatteri'
```

The CI line is hard-coded in `_dash_legend_keys` (:26984-26998):

```python
26984          if ptype in _DASH_CI_TYPES:
26988                  lvl = _resolve_level(plot.get("options", {}) or {},
26989                                       _DEFAULT_LEVEL if default_level is None
26990                                       else default_level, ptype)
26995                  if band:
26996                      out.append((n, f"{lvl:g}% CI", band))
26997                  if line:
26998                      out.append((n + 1, "Fitted values", line))
```

`DashRenderer._FIT_TYPES = _DASH_FIT_TYPES` and `_CI_TYPES` (:30075-30076) have no reader outside the module and `test_server_layer_defects.py:1003`.

### E2. scatteri passes no legend label (dash_render.py:13714-13717, :21441-21444)

```python
13714          r = fig.scatter(x="x", y="y", source=si_source,
13715                          marker=marker, size=size,
13716                          fill_color=color, line_color=color,
13717                          line_width=self.scheme.plot_line_width(color_idx, "mark"))
...
21441      if not fig.legend:
21442          # The mapper made none (scatteri, lowess): twoway draws none.  pci
21443          # makes one now, as pcspike does (map_pci_literal).
21444          return
```

So `(scatteri 20 3000 25 3500), legend(on)` draws no legend, where twoway draws the key `y` (I01, G12, G24). The comment is wrong for both types: `map_lowess` passes `legend_label=yvar` (:11362), and twoway keys scatteri.

### E3. Titles: the first layer decides (dash_render.py:21665-21706)

```python
21678      go, vl = graph_opts or {}, var_labels or {}
21679      p0 = plots[0] if plots else {}
21680      ptype = str(p0.get("type", "") or "").lower()
21681      if ptype in _DASH_UNIVARIATE_TYPES:
...
21691          xvar, yvar = p0.get("xvar", ""), p0.get("yvar", "")
21693          x_default = _dash_var_label(vl, xvar)
21694          y_default = _dash_var_label(vl, yvar)
```

Range, pc, immediate and function specs carry no `yvar`, so they get no title. Measured at `c96facd`: `_dash_axis_labels([scatter mpg, scatter price], {}, vl)` → `('Weight (lbs.)', 'Mileage (mpg)')`; rcap → `('Weight (lbs.)', '')`; pcspike → `('', '')`; function and scatteri → `('', '')`.

Callers: saved `_make_figure_body` (:30236-30237) and the served template (:35139-35140, emitted text):

```python
30236          x_label, y_label = _dash_axis_labels(plots, graph_opts,
30237                                               self.variable_labels, _seen, _gkey)
35139              "        x_label, y_label = _dash_axis_labels(plots, go, var_labels,",
35140              "                                             _reported_subopts, gname)",
```

### E4. The second axis inherits the first-layer rule (dash_render.py:23086-23093)

```python
23086          if str(graph_opts.get("by", "") or "").strip():
23087              dflt = ""
23088          else:
23089              own = [p for p in plots
23090                     if str(p.get("options", {}).get(axis_key, "1")).strip()
23091                     == "2"]
23092              dflt = _dash_axis_labels(own, {}, var_labels)[
23093                  0 if n == "x" else 1]
```

Called from saved `_make_figure_body` (:30385) and the served template (:35206). `_dash_lone_second_axes` (:3115) has already moved a graph whose every layer is on `yaxis(2)`/`xaxis(2)` onto axis 1 in both loaders, so a per-axis selection never untitles such a graph (critic A1, A2).

### E5. The function's y name is stripped and lost (dash.ado:3675-3684, :4309-4312)

```stata
3679             mata: st_local("_fn_raw", strtrim(st_global("s(vals)")))
3683             mata: st_local("vals", regexr(strtrim(st_global("s(vals)")), "^[a-zA-Z][a-zA-Z0-9_]*[ ]*=[ ]*", ""))
3684             local expr : copy local vals
...
4309     else if "`ptype'" == "function" {
4310         _dash_json_str `"`macval(expr)'"' _jex
4311         local vfields `""expr":"`_jex'""'
4312     }
```

The ASCII pattern misses names twoway takes. Measured at `c96facd` through the slot (`dash function ü = x, name(kt2)`): `$dash_json_kt2` = `{"plots":[{"type":"function","expr":"ü = x","options":{},…}]…}`; `dash function _y =` prints `error in expression: ` r(111) where `twoway function _y =` prints `nothing found where expression expected` r(111). The points are computed from `_fn_raw` by twoway's own generator (`_dash_fn_points`, dash.ado:5973), so drawing is already right; only the name and the empty-expression message are not. `_dash_process_segment` (dash.ado:3454) has one caller, `_dash_plot` (:5210), which every plot command runs.

### E6. twoway's truth (StataNow 19.5, stcolor; research §4, critic, and this pass)

Per series (a CI fit draws two, band then line):

| Type | y label (= key) | x label |
|---|---|---|
| scatter, line, connected, area, bar, spike, dropline, dot, tsline | `L(y)` | `L(x)` |
| range types (rarea … rscatter, tsrline) | `L(y1)/L(y2)`; one text when equal (R12, G04) | `L(x)` |
| pc types | `L(y1)/L(y2)` (one when equal, G15) | `L(x1)/L(x2)` (one when equal, G16) |
| scatteri | `y` | `x` |
| pci, pcarrowi | `y/yb` | `x/xb` |
| lfit, qfit, lfitci/qfitci line | `Fitted values` | `L(x)` |
| fpfit, fpfitci line | `Predicted <y NAME>` (F15, G01) | `L(x)` |
| lowess | `lowess <y name> <x name>` (F01; full names when abbreviated, C03) | `L(x)` |
| lpoly, lpolyci line | `lpoly smooth: <L(y)>` (F03, F26) | `lpoly smoothing grid` |
| mband / mspline | `Median bands` / `Median spline` | `L(x)` |
| function | the name before `=` when it is a Stata name, else `y` (F27) | `x` |
| histogram / kdensity | `Density`/`Percent`/`Frequency`/`Fraction` / `kdensity <name>` (P0.3, unchanged) | `L(var)` / `x` |
| any CI band | `<level>% CI` | as its line |

`L(v)` is `_dash_var_label`: the label when it is not `""`, else the name. Corroborated by StataNow's source: `twoway_lowess_parse.class:85`, `lpoly.ado:418,422`, `twoway__lfit_serset.ado:46`.

The function name is twoway's `confirm name` on the first token (`twoway__function_gen.ado:37-66`). Measured this pass (`r(yis)` of `twoway__function_gen`; slot run `s19-probe/names.do`):

```
NAMES|_y = x|yis=_y      NAMES|ü = x|yis=ü        NAMES|日本 = x|yis=日本     NAMES|a٣ = x|yis=a٣
NAMES|<32-char name> = x|yis=<that name>          NAMES|<33-char name> = x|yis=y|exp=<the whole text>
NAMES|x^2|yis=y          NAMES|= x|yis=y          NAMES|1y = x|yis=y|exp=1y = x
CONFIRM|a½|rc=0   CONFIRM|aⅣ|rc=0   CONFIRM|<33 chars>|rc=7
MATA ustrregexm "^([\p{L}_][\p{L}\p{N}_]{0,31})[ ]*=": _y→_y ü→ü 日本→日本 a٣→a٣ 1y→none 33-char→none x^2→none
```

The title rule (research §4.2; twoway's axis objects in `k.do`, the drawn SVG in `m4.do`, confirmed by the critic's C01, C02, C11): each axis is titled with its first series' label when its LAST series' label equals it, whatever lies between; otherwise it has no title. It holds per axis (K11 `price, trunk, price` on axis 2 → `Price`), under by() (K10 → `Mileage (mpg)`; G05 → none), by text not by variable (G03, G21), and a CI layer counts as two series:

```
K01 (scatter mpg weight) (scatter mpg length) (scatter mpg weight)   XT=Weight (lbs.) YT=Mileage (mpg)
K02 (scatter mpg weight) (scatter mpg length) (scatter mpg length)   XT=              YT=Mileage (mpg)
K04 (scatter mpg weight) (scatter price weight) (scatter price weight) (scatter mpg weight)   YT=Mileage (mpg)
    (scatter mpg weight) (scatter price weight) (scatter mpg weight) (scatter price weight)   YT=
K05 (lfit mpg weight) (lfitci mpg weight)   YT=Fitted values   [FV, 95% CI, FV]
K06 (lfitci mpg weight) (lfit mpg weight)   YT=                [95% CI, FV, FV]
K07 (rcap mpg turn weight) (scatter mpg weight) (rcap mpg turn weight)   YT=Mileage (mpg)/Turn circle (ft.)
K08 scatter mpg turn mpg weight             YT=Mileage (mpg)
```

`plotregion.class:396-448` (`dimtitle, clean`) reads like "all agree"; the drawing does not follow it, so the rule is pinned by measurement only.

### E7. Residuals measured beside this item (register P1.16.2/A57: filed, not folded)

The prototype's 8 unmatched mode-probes (`compare.py -v`): F31 keys (twoway merges two `95% CI` bands into one key: P2.50), G25 keys (`(histogram mpg) (histogram mpg)`: twoway draws no legend: P2.51), G20 keys (`(rcap mpg turn weight), by(foreign)`: no legend for one layer under by(): P1.15c, S53), H01 sides (axis 2 drawn left when used first: P2.52). From `m5.do`: L01, L02, L04, L05 merge keys (P2.50); L03, L09 draw no legend (P2.51).

### E8. Tests that pin today's behaviour (flipped in place, never deleted; re-measured by 19-07 and 19-11)

Commit 1 (keys), 14 nodes:
- `test/test_server_layer_defects.py::TestTheLegendKeyRule::test_a_computed_layer_is_keyed_fitted_values[fpfit|function|lowess|lpoly|mband|mspline]` (:1003-1006; `[lfit]` and `[qfit]` keep "Fitted values")
- `::TestTheLegendKeyRule::test_a_ci_layer_is_keyed_fitted_values_on_its_own[fpfitci|lpolyci]` (:1008-1011)
- `::TestTheLegendKeyRule::test_a_range_layer_uses_its_first_boundary` (:1039-1040, `{"type": "rbar", "yvar1": "lo"} == "lo"`)
- `::TestTheLegendKeyRule::test_a_layer_with_no_variable_is_keyed_by_its_type` (:1042-1043, `pci` → `"pci"`)
- `::TestTheLegendSaysTheSameThing::test_a_band_and_its_line_are_keyed_separately[lpolyci|fpfitci]` (:754-760, `["95% CI", "Fitted values"]`)
- `test/test_immediate_dashboards.py::TestPciIsDrawnAsPcspike::test_it_has_a_legend_key_as_twoway_gives_it[saved|served]` (:515-526, `["scatteri", "pci"]`)

Commit 2 (titles), 1 node:
- `test/test_unlabelled_variables.py::TestAfterAFilterMove::test_served_names_survive_a_move` (:445-454, asserts y title `["y"]` for unlabelled `(scatter y x) (scatter y2 x)`, where twoway draws none)

`test/function_test_map.py:559` maps `_dash_legend_key` to the first `ci` node above; it is re-pointed in place (TR-19.8). Unchanged on the prototype (research §6, critic): test_legend_order, test_server_legend, test_textbox_no_text, test_axis2_suboptions, test_dual_axis, test_mode_parity, test_saved_stale_cue, test_graph_options, test_axis_options, test_date_units, test_label_sinks, test_ci_band_style, test_function_expr, test_varlist_expansion (the single-y digest included) and 11 more; `test_parser.cscript` P1A-71's `"expr":"x^2"` needle still holds with `,"yname":"y"` after it.

### E9. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, index at `c96facd`)

| Symbol | Edit | Risk |
|---|---|---|
| `_dash_axis_labels` | commit 2: default from the new helper | **HIGH** (warn before editing) |
| `ServerAppBuilder._glyph_layer_lines` | both commits: tuple entries | **HIGH** (warn) |
| `_dash_add_secondary_axes` | commit 2: default | LOW |
| `_dash_legend_key`, `_dash_legend_keys` | commit 1 | LOW |
| `GlyphMapper.map_scatteri` | commit 1: one keyword | LOW |
| `_dash_apply_legend` | commit 1: comment only | UNKNOWN; grep: callers `_rebuild_legend` (:30083) and the served template (:35460) |
| `_dash_process_segment` (dash.ado) | commit 1: function branch | UNKNOWN (ado not indexed); grep: one caller `_dash_plot` (:5210) |
| `_dash_var_label`, `_make_figure_body`, `_generate_app_source` | read only, not edited | CRITICAL / CRITICAL / HIGH |

## User stories

- **US-19.1** As a twoway user, I want `(scatter mpg weight) (lowess mpg weight)` keyed `lowess mpg weight`, and lpoly, mband, mspline, fpfit and their CI lines keyed in twoway's text, so that my legend reads as it does in Stata.
- **US-19.2** As a twoway user, I want range and pc layers keyed `Mileage (mpg)/Turn circle (ft.)`, scatteri `y` and pci `y/yb`, and a scatteri-only graph with `legend(on)` to show its key.
- **US-19.3** As a twoway user, I want `function z = x/100`, `function _y = x` and `function ü = x` keyed `z`, `_y` and `ü`, and `function _y =` refused in twoway's words.
- **US-19.4** As a twoway user, I want no axis title where my layers plot different things, and twoway's title where they agree by its rule, including range, pc, immediate and function layers.
- **US-19.5** As a twoway user, I want `yaxis(2)` and `xaxis(2)` titled by their own layers under the same rule.
- **US-19.6** As a dashboard publisher, I want the saved page and the served app to show the same keys and titles before and after a filter move.

## Business requirements

- **BR-19.1** Each layer's legend key is twoway's text for its type (E6's table), in both modes, before and after any filter move; a CI fit has two keys, `<level>% CI` then its line's text.
- **BR-19.2** A function layer is keyed by the name before its `=` when that is a Stata name (1-32 Unicode characters, a letter or `_` first, then letters, digits or `_`), else `y`; `function <name> =` with no expression is refused r(111) `nothing found where expression expected`, as twoway.
- **BR-19.3** A scatteri-only graph keys its layer `y`; whether the legend shows follows the rule every type follows (two or more keys, or `legend(on)`).
- **BR-19.4** Each axis's default title is the label of the first series drawn on it when the last series drawn on it has the same label, and nothing otherwise; a CI fit counts as two series.
- **BR-19.5** The rule holds on axis 2 by its own layers, on every by() panel, and for range, pc, immediate and function layers; under by() axis 2 still has no default title (WP-29 r7).
- **BR-19.6** An explicit `xtitle()`/`ytitle()`/`ytitle2()`, a typed `""`, sub-options alone, `suffix`/`prefix` and `legend(label())`/`order()` behave as today; sub-options alone on an axis with no default draw no title (H20, H21).
- **BR-19.7** Saved page and served app draw the same keys and titles; no filter move changes them except the saved stale cue's suffix on a stale layer's key.
- **BR-19.8** No note is added or removed (M6); the residuals P2.50, P2.51, P2.52 and P1.15c stay open and are named.

## Technical requirements

**Commit 1 — keys.**

- **TR-19.1 `_DASH_FIT_KEYS`** (dash_render.py, new, directly after `_DASH_CI_TYPES` :26706):
  ```python
  #: The fixed line text twoway gives a fit (twoway__lfit_serset.ado and the
  #: mband/mspline parsers; test/fixtures/series_label_truth.json).  fpfit,
  #: lowess, lpoly and function texts are built from the layer's variables
  #: by _dash_layer_series.
  _DASH_FIT_KEYS = {"lfit": "Fitted values", "qfit": "Fitted values",
                    "lfitci": "Fitted values", "qfitci": "Fitted values",
                    "mband": "Median bands", "mspline": "Median spline"}
  ```
  `_DASH_FIT_TYPES` stays defined, unchanged in value (it is the R2 anchor, the copy lists are append-only under X.1/A133, and `DashRenderer._FIT_TYPES` aliases it); its comment (:26695-26697) is rewritten to "The computed fit types: layers whose y series is computed, not a variable. Their keys and titles come from `_dash_layer_series`."
- **TR-19.2 `_dash_layer_series(plot, var_labels=None, default_level=None)`** (new, directly above `def _dash_legend_key`). Returns `[(y_label, x_label), …]`, one pair per series twoway draws for the layer (two for a CI type, band first). Total: a non-dict *plot* gives `[("", "")]`; a non-dict `options` is `{}`; a non-dict *var_labels* is `{}`; labels go through `_dash_var_label`. The rule, in this order (`ptype` = `type` stripped and lower-cased; `L` = `_dash_var_label(vl, ·)`; `pair(a, b)` = `L(a)` when `L(b)` is `""` or equal to it, `L(b)` when `L(a)` is `""`, else `L(a) + "/" + L(b)`):
  - univariate: kdensity `("kdensity <var>", "x")` (`"kdensity"` with no var); histogram `(_DASH_HIST_YTITLES[_dash_histogram_ymode(options)], L(var))`; `var` is `plot["var"]` or `plot["yvar"]`.
  - `_DASH_RANGE_TYPES`: `(pair(yvar1, yvar2), L(xvar))`.
  - `_DASH_PC_TYPES`: `(pair(y1var, y2var), pair(x1var, x2var))`.
  - `scatteri`: `("y", "x")`; `pci`, `pcarrowi`: `("y/yb", "x/xb")`.
  - `function`: `(name, "x")`, `name` = `plot["yname"]` when it is a `str` of 1-32 characters whose first is `_` or `isalpha()` and whose others are `_` or `isalnum()`, else `"y"` (old, hand-written and hostile specs fall back).
  - the computed line: `lowess` → `" ".join(["lowess"] + [n for n in (yvar, xvar) if n])` (names, never labels); `fpfit`/`fpfitci` → `"Predicted " + yvar` (`"Predicted"` with no yvar); `lpoly`/`lpolyci` → `"lpoly smooth: " + L(yvar)` (`"lpoly smooth:"` with no yvar); else `_DASH_FIT_KEYS[ptype]`. Its x label is `"lpoly smoothing grid"` for lpoly/lpolyci, else `L(xvar)`. A `_DASH_CI_TYPES` layer returns `[(f"{lvl:g}% CI", x), (line, x)]` with `lvl = _resolve_level(options, _DEFAULT_LEVEL if default_level is None else default_level, ptype)` (the expression `_dash_legend_keys` uses today); the others `[(line, x)]`.
  - everything else: `[(L(yvar), L(xvar))]`.
  The text is raw: never escaped, never SMCL-translated (S29 translates once at the sink). A docstring cites E6 and the fixture.
- **TR-19.3 `_dash_legend_key`** (:26925): body becomes `series = _dash_layer_series(plot, var_labels)`, `text = series[-1][0] if series else ""`, and `return text or ptype` with `ptype = str(plot.get("type", "")).lower() if isinstance(plot, dict) else ""` (a plain layer with no variable keeps its type, the hand-written-spec fallback). The histogram/kdensity branches move into TR-19.2 unchanged in result. Docstring: twoway's per-type text, the CI line for a CI type.
- **TR-19.4 `_dash_legend_keys`** (:26960): in the CI branch, `ser = _dash_layer_series(plot, var_labels, default_level)`; the band key is `ser[0][0]` and the line key `ser[-1][0]` (replacing `f"{lvl:g}% CI"` and `"Fitted values"`); the band/line renderer split, numbering and swatch skip are unchanged. Docstring line "its line `n + 1` ("Fitted values")" becomes "its line `n + 1` (the fit's own text)".
- **TR-19.5 scatteri key** (`GlyphMapper.map_scatteri`, :13714-13717): add `legend_label="y"` to the `fig.scatter(...)` call. `_dash_apply_legend` then rebuilds it as every other key (both modes share the mapper and the helper). Rewrite only the comment at :21442-21443 to: "The mapper made none (a layer that drew nothing): there is nothing to key." No code line of `_dash_apply_legend` changes. The generated template's comment at :35443-35446 ("lowess, scatteri and pci pass no label") is NOT edited: `_generate_app_source` is S21's this batch (R12); the closeout records it.
- **TR-19.6 dash.ado, `_dash_process_segment` function branch** (:3675-3712). After :3679 add
  ```stata
              // The y name twoway keys and titles the layer by: the first
              // token when it is a Stata name followed by `=' (twoway__function_gen's
              // confirm name), any Unicode letter or `_' first, at most 32
              // characters; "" otherwise, read in Mata by value.
              mata: st_local("_fn_yname", (ustrregexm(strtrim(st_global("s(vals)")), "^([\p{L}_][\p{L}\p{N}_]{0,31})[ ]*=") ? ustrregexs(1) : ""))
  ```
  and change :3683 to `mata: st_local("vals", ustrregexra(strtrim(st_global("s(vals)")), "^[\p{L}_][\p{L}\p{N}_]{0,31}[ ]*=[ ]*", ""))`, so the name and the expression are split by one pattern (`_y = x` keeps `x`; `function _y =` reaches twoway's r(111) words through the existing empty-expression check at :3691-3700). At :4309-4312 write `_dash_json_str "`_fn_yname'" _jyn` and `local vfields `""expr":"`_jex'","yname":"`_jyn'""'`. `_fn_yname` holds only name characters, so it cannot hold a quote, backtick or `$`; it is JSON-escaped all the same. No new program or Mata function (no map or `_needed` entry).
- **TR-19.7 Served copy lists, commit 1** (`ServerAppBuilder._glyph_layer_lines`): constants tuple, a new line `"_DASH_FIT_KEYS",` after `"_DASH_FIT_TYPES", "_DASH_CI_TYPES",` (:32895, R2's S19 anchor); functions tuple, `"_dash_layer_series",` on a new line after `"_dash_legend_key", "_dash_legend_entries",` (:33175; an S19 addition to R2's row, an anchor no other batch-7 section uses). `_dash_var_label`, `_resolve_level`, `_dash_histogram_ymode`, `_DASH_HIST_YTITLES` and the type sets are already copied.
- **TR-19.8 Maps.** Under `# WP-30 S19 (P1.16): Legend keys and default axis titles (P1.16)` in `test/function_test_map.py`: `'_dash_layer_series': 'test/test_series_labels.py::TestTheSeriesRule::test_each_type_gives_twoways_series'`. In place at :559: `'_dash_legend_key': 'test/test_series_labels.py::TestTheLegendKeys::test_the_key_is_the_last_series_y_label'`. `test/program_coverage_map.py` is unchanged (no new program).

**Commit 2 — titles.**

- **TR-19.9 `_dash_axis_default_titles(plots, var_labels=None, yaxis=1, xaxis=1, default_level=None)`** (new, directly above `def _dash_axis_labels` :21665). Returns `(x_title, y_title)`:
  ```python
  ys, xs = [], []
  for plot in plots or ():
      if not isinstance(plot, dict):
          continue
      opts = plot.get("options") if isinstance(plot.get("options"), dict) else {}
      series = _dash_layer_series(plot, var_labels, default_level)
      if str(yaxis) in (str(opts.get("yaxis", "1") or "1").split() or ["1"]):
          ys.extend(s[0] for s in series)
      if str(xaxis) in (str(opts.get("xaxis", "1") or "1").split() or ["1"]):
          xs.extend(s[1] for s in series)
  x = xs[0] if xs and xs[0] == xs[-1] else ""
  y = ys[0] if ys and ys[0] == ys[-1] else ""
  return x, y
  ```
  The axis option is read as a list of numbers, so a future `yaxis(1 2)` layer (P2.14, refused today) counts on both axes (critic 3). Comparison is of raw text.
- **TR-19.10 `_dash_axis_labels`** (:21665, HIGH): replace :21679-21694 (the `p0` reads and the univariate branch) with `x_default, y_default = _dash_axis_default_titles(plots, vl)`. `_label` and the return are unchanged. Docstring: twoway's first-equals-last rule per axis (E6), not the first layer.
- **TR-19.11 `_dash_add_secondary_axes`** (:23088-23093): the non-by() default becomes `dflt = _dash_axis_default_titles(plots, var_labels, yaxis=2 if n == "y" else 1, xaxis=2 if n == "x" else 1)[0 if n == "x" else 1]`; the `own` list goes; the by() exception (:23086-23087) stays. Docstring paragraph "through `_dash_axis_labels` over the layers on that axis, so its first layer's label" becomes "by `_dash_axis_default_titles` over that axis's own series (twoway's first-equals-last rule)".
- **TR-19.12 Served copy list, commit 2:** `"_dash_axis_default_titles",` on a new line after `"_dash_axis_labels",` (:33228, R2's S19 anchor). Map: `'_dash_axis_default_titles': 'test/test_series_labels.py::TestTheAxisTitleRule::test_first_equals_last'` under the S19 anchor.
- **TR-19.13 Help** (dash.sthlp; R3/A155). A new `{pstd}` paragraph in Statistical Layer Options, after the opening paragraph's "options -- see below." (:2254) and before `{synoptset 20}{...}` (:2256), lines of at most 79 characters:
  ```
  {pstd}
  {it:Legend keys and default axis titles.}  Each layer is keyed as
  {cmd:twoway} keys it: a data layer by its y variable's label, or its
  name when it has none; a range or {cmd:pc} layer by both variables,
  {it:label1}{cmd:/}{it:label2}, one label when the two are the same;
  {cmd:scatteri} {cmd:y}; {cmd:pci} and {cmd:pcarrowi} {cmd:y/yb};
  {cmd:lfit} and {cmd:qfit} {cmd:Fitted values}; {cmd:fpfit}
  {cmd:Predicted} {it:yvar}; {cmd:lowess} {cmd:lowess} {it:yvar xvar};
  {cmd:lpoly} {cmd:lpoly smooth:} {it:ylabel}; {cmd:mband}
  {cmd:Median bands}; {cmd:mspline} {cmd:Median spline}; {cmd:function}
  by the name before its {cmd:=}, or {cmd:y}; {cmd:histogram}
  {cmd:Density} (or its scale); {cmd:kdensity} {cmd:kdensity} {it:varname}.
  A {cmd:ci} fit has two keys, its band {it:#}{cmd:% CI} and then its line.
  Each axis is titled by default with the label of the first series
  drawn on it when the last series drawn on it has the same label, and
  is untitled otherwise, as {cmd:twoway} titles it; a {cmd:ci} fit is
  two series, band then line.  The rule holds for each axis on its own,
  {cmd:yaxis(2)} and {cmd:xaxis(2)} included, and on every {cmd:by()}
  panel.  Keys {cmd:twoway} merges into one and the legend it leaves off
  a graph of histograms alone are still drawn by {cmd:dash}.
  ```
  Three stale sentences elsewhere are corrected in place (each names the rule this section changes; no batch-7 partner owns them: S20 edits :740-742 and :3233, S21 :2811 and :2852): :635-637 "keeps the default (the variable's label, {cmd:Density}, {cmd:kdensity} {it:var})" → "keeps the default title (see {it:Legend keys and default axis titles} under Statistical Layer Options)"; :809-811 extended with "Every other layer is keyed as {cmd:twoway} keys it (see Statistical Layer Options)."; :3010-3013 "by the label (or name) of its first layer's variable, {cmd:Density} or {cmd:kdensity} {it:varname} for those layers" → "by the rule of the first axis, over its own layers' series".
- **TR-19.14 Security (rule 1).** Keys and titles are LegendItem label values (DOM text nodes) and Bokeh axis labels (canvas text), never HTML, as today (`test_label_sinks.py`); S09's pass makes TeX pairs inert after them. The only new input is `yname`: captured in Stata by a pattern of name characters only (≤32), JSON-escaped by `_dash_json_str`, re-validated in Python (TR-19.2), never passed to `eval`, a shell or a format string. Every built text is bounded: two Stata labels of ≤80 characters and a fixed prefix, or two names of ≤32. No `shell=True` anywhere; the extractor's `shell git rev-parse` is in the do-file (D12).
- **TR-19.15 Both modes and JS twins.** Both renderers build keys through `_dash_apply_legend` → `_dash_legend_keys` → `_dash_legend_key` and titles through `_dash_axis_labels`/`_dash_add_secondary_axes` (saved :30083, :30236, :30385; served :35460, :35139, :35206), so one change reaches both. No filter callback rebuilds a key or a title (WP-29 S03's scan of every module-level JS string); the saved stale cue appends `_DASH_STALE_SUFFIX` to whatever the key text is and restores it (:32289). No JS twin is needed and `_FILTER_JS` is not edited.

## Boundaries

- **Partners in batch 7.** S20 owns `_dash_option_rules`, `_dash_validate_value`, `_dash_fold_mlab`, `_dash_fold_bw` and help :740-742, :3233. S21 owns `_make_figure_body`, `_generate_app_source`, `_dash_padded_range`, `_dash_common_count_ticks`, `_dash_share_by_scales`, `_dash_limit_ranges_to_primary`, `_dash_keep_primary_ranges`, the filter builders, `_FILTER_JS`, the finishers, the scheme files and help :2811, :2852. S19 edits none of them.
- **Later sections.** S28 (by() panel labels, the "Graphs by" note), S29 (SMCL translation at the sink: keys and titles stay raw here), S42 (time-series operator labels through `_dash_layer_series`), S45 (recast keeps the original series label: S45 keeps `type` and writes `recast`, register P1.16.5), S49 (horizontal swaps each layer's series; the first-layer swap of P1.9.3 goes through `_dash_axis_default_titles`), S53 (titles once and one legend under by(); G20). P1.4 (S24) styles keys; P1.2 (S15) styles titles.
- **Residuals, not drawn here** (register P1.16.2/A57): P2.50 key merging, P2.51 histogram-only legends, P2.52 first-used-axis placement.
- **Not edited:** `_dash_var_label`, `_dash_axis_vars` (formats and first-layer variables: S18, S49), `_dash_lone_second_axes`, `_dash_fn_points` (its ASCII echo regex at :5977 stays: P1.22/S26's area), `GlyphMapper.map_function` (its `legend_label=text[:40]` is rebuilt by `_dash_apply_legend`), `_dash_textbox_or_default`, `_FILTER_JS`, the stale cue, any scheme or tracking document, `test/program_coverage_map.py`.
- **Decisions applied:** M1 (twoway's look, CHANGELOG Results), M5 (the one message change uses twoway's words and rc), M6 (no note added), register P1.16.1-P1.16.5 (A56-A60), X.1 (append-only copy lists), A148 (map anchor), A156 (two commits).

## Stata truth

### The fixture `test/fixtures/series_label_truth.json` and its extractor

**`scripts/extract_series_label_truth.do`** (new; in `scripts/extract_unlabelled_truth.do`'s shape as S02 converted it). It opens with the header comment (what, why, output, run line `DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_series_label_truth.do`), `clear all`, `set graphics off`, `set more off`, `set linesize 255`, then S02's root stanza (TR-02.9) with `<file>` = `extract_series_label_truth.do`, then `adopath ++ "`repo'/"` and `global dash_nobrowser 1`, `global ZK_REPO "`repo'"`, `global ZK_OUT "`repo'/test/fixtures/series_label_truth.json"`, a work directory `` `c(tmpdir)'dash_series_label_probe `` and `set scheme stcolor`. The stamp: `c(stata_version)`, `c(born_date)`, `c(current_date) c(current_time)` and `git -C "<repo>" rev-parse HEAD` written by `shell` into a tempfile and read back by `file read` (as extract_unlabelled_truth.do:66-80).

**Data.** `_zk_auto` = `sysuse auto, clear`, then `gen m2 = mpg`, `gen p2 = price`, `gen p3 = price` + `label variable p3 "Price"`, `gen t2 = turn` + `label variable t2 "Turn circle (ft.)"`, `gen p4 = price` + `label variable p4 "Mileage (mpg)"`; `_zk_sp` = `sysuse sp500, clear` + `tsset date`. Each is exported once, before the probes, through dash's own writer: `python: dash_render._dash_write_stata_data(<work>/data_<ds>.json, <the variables below>)` (with `sys.path` holding `$ZK_REPO`), auto: `mpg weight turn length price trunk foreign m2 p2 p3 t2 p4`; sp500: `date close open high low`; and each variable's `: format` is written to `<work>/formats_<ds>.txt`.

**Per probe** (`zk id ds body opts`, registered in a table, then run in a loop; `opts` may be empty):
1. reload the data set; `twoway <body>, <opts> name(Graph, replace)`; `graph export <work>/<id>_tw.svg, name(Graph) replace`; record the axis objects' titles `y1 = .Graph.yaxis1.title.text[1]`, `y2 = .Graph.yaxis2.title.text[1]`, `x1`, `x2` (each `capture`d, `""` when the axis does not exist) and the rc;
2. `twoway <body>, <opts> legend(off) name(Graph, replace)` exported to `<work>/<id>_off.svg`;
3. `capture dash clear`; `capture noisily dash <body>, <opts> name(zk<n>)`; the rc, and `$dash_json_zk<n>` and `$dash_fpts_zk<n>` written to `<work>/<id>_dash.txt` and `<work>/<id>_fpts.txt` through Mata `fopen`/`fput`/`fclose` (never a macro expansion).
All text reaches files by value; nothing is echoed with `display`.

**The trailing `python:` block** (reads files only; never calls Stata; a backtick written `\x60`) builds the JSON with `json.dump(…, ensure_ascii=False, indent=1, sort_keys=True)`:
- `_meta`: `stata_version`, `born_date`, `dash_commit`, `extracted`, `scheme` (`stcolor`), `probes` (the count), `method` (one sentence: keys are bare minus legend(off) by multiset; titles are twoway's axis objects; `svg_titles` the drawn texts).
- `data`: `{"auto": <data_auto.json>, "sp500": <data_sp500.json>}`; `formats`: `{"auto": {var: fmt}, "sp500": {…}}`.
- `probes[<id>]`: `ds`, `body`, `opts`, `twoway` = `{"rc", "keys", "titles": {"y1","y2","x1","x2"}, "svg_titles": {"left","right","bottom","top"}}`, `dash` = `{"rc", "graph": <parsed $dash_json>, "points": <parsed $dash_fpts or null>}`.
- `keys`: `scripts/svg_truth.py` `svg_texts` of the two SVGs; bare minus off as a multiset, in (y, x) order; numbers dropped; for a by() probe also the by variable's value labels (`Domestic`, `Foreign`) and every text starting `Graphs by` (research reader).
- `svg_titles`: from the off SVG's non-numeric texts: `rotate == -90` with x below half the width → left, else right; unrotated, not a date (`^\d\d[a-z]{3}\d{4}$`), y below half the height → top, else bottom.

**The probes** (150; 136 from the research's `m1.do`-`m4.do`, 9 from `m5.do`, 5 for this section's names), verbatim:

```stata
zk F01 auto "(scatter mpg weight) (lowess mpg weight)" ""
zk F02 auto "(lowess mpg weight)" "legend(on)"
zk F03 auto "(scatter mpg weight) (lpoly mpg weight)" ""
zk F04 auto "(lpoly mpg weight)" "legend(on)"
zk F05 auto "(scatter mpg weight) (mband mpg weight)" ""
zk F06 auto "(mband mpg weight)" "legend(on)"
zk F07 auto "(scatter mpg weight) (mspline mpg weight)" ""
zk F08 auto "(mspline mpg weight)" "legend(on)"
zk F09 auto "(scatter mpg weight) (function y=20+0.001*x, range(2000 5000))" ""
zk F10 auto "(function y=x^2, range(0 2))" "legend(on)"
zk F11 auto "(scatter mpg weight) (lfit mpg weight)" ""
zk F12 auto "(lfit mpg weight)" "legend(on)"
zk F13 auto "(scatter mpg weight) (qfit mpg weight)" ""
zk F14 auto "(qfit mpg weight)" "legend(on)"
zk F15 auto "(scatter mpg weight) (fpfit mpg weight)" ""
zk F16 auto "(fpfit mpg weight)" "legend(on)"
zk F17 auto "(scatter mpg weight) (lfitci mpg weight)" ""
zk F18 auto "(lfitci mpg weight)" ""
zk F19 auto "(qfitci mpg weight)" ""
zk F20 auto "(fpfitci mpg weight)" ""
zk F21 auto "(scatter mpg weight) (lpolyci mpg weight)" ""
zk F22 auto "(lpolyci mpg weight)" ""
zk F23 auto "(lfit mpg weight) (qfit mpg weight)" ""
zk F24 auto "(lowess mpg weight) (lpoly mpg weight)" ""
zk F25 auto "(scatter m2 weight) (lowess m2 weight)" ""
zk F26 auto "(scatter m2 weight) (lpoly m2 weight)" ""
zk F27 auto "(scatter mpg weight) (function sin(x), range(2000 5000))" ""
zk F28 auto "(scatter mpg weight) (function z=x/100, range(2000 5000))" ""
zk F29 auto "(scatter mpg weight) (lowess mpg weight) (lowess mpg weight, bwidth(0.3))" ""
zk F30 auto "(mband mpg weight) (mspline mpg weight)" ""
zk F31 auto "(scatter mpg weight) (lpolyci mpg weight) (lfitci mpg weight)" ""
zk F32 auto "(scatter mpg weight) (lpoly mpg weight, kernel(biweight) degree(2))" ""
zk U01 auto "(histogram mpg)" "legend(on)"
zk U02 auto "(kdensity mpg)" "legend(on)"
zk U03 auto "(histogram mpg) (kdensity mpg)" ""
zk R01 auto "(rarea mpg turn weight)" "legend(on)"
zk R02 auto "(rbar mpg turn weight)" "legend(on)"
zk R03 auto "(rspike mpg turn weight)" "legend(on)"
zk R04 auto "(rcap mpg turn weight)" "legend(on)"
zk R05 auto "(rcapsym mpg turn weight)" "legend(on)"
zk R06 auto "(rscatter mpg turn weight)" "legend(on)"
zk R07 auto "(rline mpg turn weight)" "legend(on)"
zk R08 auto "(rconnected mpg turn weight)" "legend(on)"
zk R09 auto "(rarea mpg turn weight) (scatter mpg weight)" ""
zk R10 auto "(rcap mpg turn weight) (scatter price weight)" ""
zk R11 auto "(rcap m2 p2 weight)" "legend(on)"
zk R12 auto "(rcap mpg mpg weight)" "legend(on)"
zk R13 auto "(rcap mpg turn weight) (rcap turn mpg weight)" ""
zk P01 auto "(pcspike mpg weight turn length)" "legend(on)"
zk P02 auto "(pccapsym mpg weight turn length)" "legend(on)"
zk P03 auto "(pcarrow mpg weight turn length)" "legend(on)"
zk P04 auto "(pcbarrow mpg weight turn length)" "legend(on)"
zk P05 auto "(pcscatter mpg weight turn length)" "legend(on)"
zk P06 auto "(scatter mpg weight) (pcspike mpg weight turn length)" ""
zk P07 auto "(pcspike m2 weight p2 length)" "legend(on)"
zk I01 auto "(scatteri 20 3000 25 3500)" "legend(on)"
zk I02 auto "(pci 20 3000 25 3500)" "legend(on)"
zk I03 auto "(pcarrowi 20 3000 25 3500)" "legend(on)"
zk I04 auto "(scatter mpg weight) (scatteri 20 3000 25 3500)" ""
zk I05 auto "(scatter mpg weight) (pci 20 3000 25 3500)" ""
zk I06 auto "(scatter mpg weight) (pcarrowi 20 3000 25 3500)" ""
zk D01 auto "(line mpg weight, sort)" "legend(on)"
zk D02 auto "(bar mpg weight)" "legend(on)"
zk D03 auto "(spike mpg weight)" "legend(on)"
zk D04 auto "(dropline mpg weight)" "legend(on)"
zk D05 auto "(dot mpg weight)" "legend(on)"
zk D06 auto "(area mpg weight, sort)" "legend(on)"
zk D07 auto "(connected mpg weight, sort)" "legend(on)"
zk M01 auto "(scatter mpg weight) (scatter price weight)" ""
zk M02 auto "(scatter mpg weight) (line mpg weight, sort)" ""
zk M03 auto "(scatter mpg turn weight)" ""
zk M04 auto "(scatter mpg weight) (scatter mpg length)" ""
zk M05 auto "(scatter mpg weight) (scatter price weight, yaxis(2))" ""
zk M06 auto "(scatter mpg weight) (scatter price weight, yaxis(2)) (scatter trunk weight, yaxis(2))" ""
zk M07 auto "(scatter mpg weight) (lfit price weight, yaxis(2))" ""
zk M08 auto "(scatter m2 weight) (scatter p2 weight)" ""
zk M09 auto "(scatter m2 weight) (scatter p2 weight, yaxis(2))" ""
zk M10 auto "(lfit mpg weight) (scatter mpg weight)" ""
zk M11 auto "(scatter mpg weight) (scatter mpg weight)" ""
zk M12 auto "(scatter mpg weight) (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(2))" ""
zk M13 auto "(histogram mpg) (scatter mpg weight)" ""
zk M14 auto "(scatter mpg weight) (function y=20+0*x, range(2000 5000))" ""
zk M15 auto "(scatter mpg weight) (scatter mpg weight, xaxis(2))" ""
zk M16 auto "(scatter mpg weight) (scatter mpg length, xaxis(2))" ""
zk T01 sp "(tsline close)" "legend(on)"
zk T02 sp "(tsrline high low)" "legend(on)"
zk T03 sp "(tsrline high low) (tsline close)" ""
zk K01 auto "(scatter mpg weight) (scatter mpg length) (scatter mpg weight)" ""
zk K02 auto "(scatter mpg weight) (scatter mpg length) (scatter mpg length)" ""
zk K03 auto "(scatter mpg weight) (scatter price weight) (scatter trunk weight) (scatter mpg weight)" ""
zk K04 auto "(scatter mpg weight) (scatter price weight) (scatter price weight) (scatter mpg weight)" ""
zk K05 auto "(lfit mpg weight) (lfitci mpg weight)" ""
zk K06 auto "(lfitci mpg weight) (lfit mpg weight)" ""
zk K07 auto "(rcap mpg turn weight) (scatter mpg weight) (rcap mpg turn weight)" ""
zk K08 auto "(scatter mpg turn mpg weight)" ""
zk K09 auto "(scatter mpg weight) (lpoly mpg weight) (lfit mpg weight)" ""
zk K10 auto "(scatter mpg weight) (scatter price weight) (scatter mpg weight)" "by(foreign)"
zk K11 auto "(scatter mpg weight) (scatter price weight, yaxis(2)) (scatter trunk weight, yaxis(2)) (scatter price weight, yaxis(2))" ""
zk G01 auto "(scatter m2 weight) (fpfit m2 weight)" ""
zk G02 auto "(fpfitci m2 weight)" ""
zk G03 auto "(scatter price weight) (scatter p3 weight)" ""
zk G04 auto "(rcap turn t2 weight)" "legend(on)"
zk G05 auto "(scatter mpg weight) (scatter price weight)" "by(foreign)"
zk G06 auto "(scatter mpg weight) (lfit mpg weight)" "by(foreign)"
zk G07 auto "(lfitci mpg weight, level(90)) (scatter mpg weight)" ""
zk G08 auto "(lpolyci mpg weight, level(90))" ""
zk G09 auto "(function y=x, range(0 1)) (function y=2*x, range(0 1))" ""
zk G10 auto "(line mpg turn weight, sort)" ""
zk G11 auto "(kdensity mpg) (kdensity mpg, bwidth(5))" ""
zk G12 auto "(scatteri 20 3000) (scatteri 25 3500)" ""
zk G13 auto "(pci 1 1 2 2) (pci 3 3 4 4)" ""
zk G14 auto "(rarea mpg turn weight) (rarea mpg turn weight)" ""
zk G15 auto "(pcspike mpg weight mpg weight)" "legend(on)"
zk G16 auto "(pcspike mpg weight turn weight)" "legend(on)"
zk G17 auto "(kdensity mpg) (scatter mpg weight)" ""
zk G18 auto "(lowess mpg weight) (lowess mpg weight)" ""
zk G19 auto "(scatter mpg weight) (lowess mpg weight)" "by(foreign)"
zk G20 auto "(rcap mpg turn weight)" "by(foreign)"
zk G21 auto "(scatter mpg weight) (scatter p4 weight)" ""
zk G22 auto "(scatter mpg weight) (lfit mpg weight, yaxis(2)) (qfit mpg weight, yaxis(2))" ""
zk G23 auto "(scatter mpg weight) (rcap mpg turn weight, yaxis(2))" ""
zk G24 auto `"(scatteri 20 3000 "pt")"' "legend(on)"
zk G25 auto "(histogram mpg) (histogram mpg)" ""
zk G26 auto "(scatter mpg weight) (mband mpg weight, bands(5))" "ytitle(, size(large))"
zk G27 auto "(scatter mpg weight) (scatter mpg weight)" "by(foreign)"
zk H01 auto "(scatter price weight, yaxis(2)) (scatter mpg weight)" ""
zk H02 auto "(scatter mpg weight, xaxis(2)) (scatter mpg length)" ""
zk H05 auto "(scatter mpg weight) (lfitci mpg weight, yaxis(2))" ""
zk H07 sp "(tsline close open)" ""
zk H11 auto "(function  yy = x, range(0 1))" "legend(on)"
zk H14 auto "(lfit mpg weight) (lfit price weight)" ""
zk H15 auto "(mband mpg weight) (mband price weight)" ""
zk H16 auto "(lowess mpg weight) (lowess price weight)" ""
zk H17 auto "(kdensity mpg) (kdensity price)" ""
zk H20 auto "(scatter mpg weight) (scatter price weight)" "ytitle(, size(large))"
zk H21 auto "(scatter mpg weight) (lpoly price weight)" "xtitle(, size(large))"
zk L01 auto "(lfitci mpg weight) (lfitci price weight)" ""
zk L02 auto "(lfitci mpg weight) (qfitci mpg weight)" ""
zk L03 auto "(histogram mpg) (histogram price)" ""
zk L04 auto "(histogram mpg) (histogram mpg)" "legend(on)"
zk L05 auto "(scatter mpg weight, pstyle(p1)) (scatter mpg weight, pstyle(p1))" ""
zk L06 auto "(histogram mpg) (scatter mpg weight)" ""
zk L07 auto "(scatter mpg weight) (histogram mpg)" ""
zk L08 auto "(rcap mpg turn weight) (scatter mpg weight)" "by(foreign)"
zk L09 auto "(histogram mpg, freq) (histogram mpg, percent)" ""
zk N01 auto "(function _y = x, range(0 1))" "legend(on)"
zk N02 auto "(function ü = x, range(0 1))" "legend(on)"
zk N03 auto "(scatter mpg weight) (function 日本 = x/100, range(2000 5000))" ""
zk N04 auto "(scatter mpg weight) (lowess mp wei)" ""
zk N05 auto "(scatter mpg weight) (fpfit mp wei)" ""
```

Expected (research table, critic, this pass): every twoway rc 0; N01 key `_y`, N02 `ü`, N03 `Mileage (mpg)` and `日本`, N04 `lowess mpg weight`, N05 `Predicted mpg`. The fixture is generated, never patched (R7), added with `git add -f` (`.git/info/exclude:58`), and named by `test/test_series_labels.py` (`test_fixtures_are_committed.py`). Run: `DASH_REPO="$WT" /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S/s19" "$WT/scripts/extract_series_label_truth.do"` (log `$S/s19/extract_series_label_truth.log`).

### The S19 block of `test/test_wp30_truth.cscript` (R1)

Helpers go directly above S01's header line `* ==== S19 P1.16: Legend keys and default axis titles ====`: a `python:` block holding a copy of everything `test/test_wp29_truth.cscript` defines at :688-880 (at `c96facd`: the import lines `_s03_col`, `_s03_json`, `_s03_re`, `_s03_html`, `_s03_w`, `_s03_main`, `_s03_M`, the constants, `_s03_val`, `_s03_models`, `_S03Saved`, `_S03Served`, `_s03_set`, `_s03_page`, `_s03_doc_summary`, `_s03_app`, `_s03_lines` and `_s03_twoway_keys`), renamed `_s19_`/`_S19_`/`S19_` (the constants `_S19_AXES` and `_S19_WIDGETS`; globals `S19_PAGE`, `S19_APP`, `S19_MOVE`, `S19_BARE`, `S19_OFF`; out `S19_K`, `S19_T` saved, `S19_SK`, `S19_ST` served, `S19_FIRED`; two outputs are renamed, not just re-prefixed: `S03_SAME_AFTER` becomes `S19_SAME` and `S03_TW` becomes `S19_TK`, the names `_s19_case` reads), `_s19_twoway_keys` also dropping texts that parse as numbers and joining the keys SORTED, and `_s03_summary` replaced by:

```python
_S19_SIDES = (("left", "y1"), ("right", "y2"), ("below", "x1"), ("above", "x2"))


def _s19_summary(models, by_id):
    sides = dict((k, set()) for _a, k in _S19_SIDES)
    keys = set()
    for m in models:
        if m.kind in ("Figure", "Plot"):
            for attr, k in _S19_SIDES:
                for ref in (m.get(attr) or []):
                    a = by_id(ref)
                    if a is not None and a.kind in _S19_AXES:
                        lab = a.get("axis_label")
                        if lab not in (None, ""):
                            sides[k].add(str(lab))
        elif (m.kind == "Legend" and m.get("name") != "_dash_clegend"
              and m.get("visible") is not False):
            one = []
            for it in (m.get("items") or []):
                item = by_id(it)
                if item is not None:
                    lab = item.get("label")
                    one.append("" if lab is None else str(lab))
            keys.add("|".join(sorted(one)))
    return dict(K=";".join(sorted(keys)),
                T="|".join("%s=%s" % (k, ";".join(sorted(sides[k])))
                           for _a, k in _S19_SIDES))
```

and one Stata program:

```stata
capture program drop _s19_case
program define _s19_case
    version 19
    // id; what = keys | titles | keys-move | titles-move; body; options
    // ("" for none); want = twoway's measured value, keys sorted and joined
    // by "|", titles "y1=..|y2=..|x1=..|x2=..".
    args id what body opts want
    local d "${S19_WORK}"
    quietly twoway `body', `opts' name(Graph, replace)
    local t1 `"`.Graph.yaxis1.title.text[1]'"'
    local t3 `"`.Graph.xaxis1.title.text[1]'"'
    local t2 ""
    local t4 ""
    capture local t2 `"`.Graph.yaxis2.title.text[1]'"'
    capture local t4 `"`.Graph.xaxis2.title.text[1]'"'
    global S19_TWT `"y1=`t1'|y2=`t2'|x1=`t3'|x2=`t4'"'
    global S19_TK ""
    if strpos("`what'", "keys") {
        cert_svg_export, name(Graph) file("`d'/`id'_bare.svg")
        cert_svg_texts, file("`d'/`id'_bare.svg")
        global S19_BARE "`r(list)'"
        quietly twoway `body', `opts' legend(off) name(s19o, replace)
        cert_svg_export, name(s19o) file("`d'/`id'_off.svg")
        cert_svg_texts, file("`d'/`id'_off.svg")
        global S19_OFF "`r(list)'"
        python: __import__("__main__")._s19_twoway_keys()
    }
    local f ""
    if strpos("`what'", "move") local f "filter(weight, type(range))"
    capture dash clear
    capture noisily dash `body', `opts' name(s19g)
    _w30_expect `id' "(_rc == 0)" "dash rc `_rc'"
    capture noisily dash build, saving("`d'/s19g.html") replace nobrowser `f'
    _w30_expect `id' "(_rc == 0)" "dash build rc `_rc'"
    capture noisily dash build, server saving("`d'/s19g_app.py") replace nobrowser `f'
    _w30_expect `id' "(_rc == 0)" "dash build, server rc `_rc'"
    global S19_PAGE "`d'/s19g.html"
    global S19_APP "`d'/s19g_app.py"
    global S19_MOVE = cond("`f'" == "", "", "weight")
    python: __import__("__main__")._s19_page()
    python: __import__("__main__")._s19_app()
    if strpos("`what'", "keys") {
        local a : copy global S19_TK
        local b : copy global S19_K
        local c : copy global S19_SK
    }
    else {
        local a : copy global S19_TWT
        local b : copy global S19_T
        local c : copy global S19_ST
    }
    local ok = (`"`a'"' == `"`want'"') & (`"`b'"' == `"`want'"') & (`"`c'"' == `"`want'"')
    display as text `"  `id' twoway [`a'] saved [`b'] served [`c']"'
    _w30_expect `id' "(`ok' == 1)" `"twoway `a', saved `b', served `c', want `want'"'
    if "`f'" != "" {
        _w30_expect `id' "(${S19_FIRED} > 0 & ${S19_SAME} == 1)" "served move fired ${S19_FIRED}, same ${S19_SAME}"
    }
    foreach x in `id'_bare.svg `id'_off.svg s19g.html s19g_app.py {
        capture erase "`d'/`x'"
    }
    capture erase "${S19_BARE}"
    capture erase "${S19_OFF}"
    capture graph drop Graph s19o
end
```

The block, between S01's start and end lines (commit 1 writes KT-01..KT-05; commit 2 inserts KT-06..KT-11 before the end line):

```stata
    global S19_WORK "`w30_work'"
    sysuse auto, clear

    // KT-01: the fits are keyed in twoway's text (F01, F03, F30, F15).
    _s19_case KT-01 keys "(scatter mpg weight) (lowess mpg weight)" "" "Mileage (mpg)|lowess mpg weight"
    _s19_case KT-01 keys "(scatter mpg weight) (lpoly mpg weight)" "" "Mileage (mpg)|lpoly smooth: Mileage (mpg)"
    _s19_case KT-01 keys "(mband mpg weight) (mspline mpg weight)" "" "Median bands|Median spline"
    _s19_case KT-01 keys "(scatter mpg weight) (fpfit mpg weight)" "" "Mileage (mpg)|Predicted mpg"
    _w30_done KT-01 "lowess, lpoly, mband, mspline and fpfit keyed in twoway's text in both modes"

    // KT-02: a function is keyed by its own name (N01, N02, F28), and the
    // spec dash.ado registers carries it.
    _s19_case KT-02 keys "(function _y = x, range(0 1))" "legend(on)" "_y"
    _s19_case KT-02 keys "(function ü = x, range(0 1))" "legend(on)" "ü"
    _s19_case KT-02 keys "(scatter mpg weight) (function z=x/100, range(2000 5000))" "" "Mileage (mpg)|z"
    mata: st_local("s19_yn", strofreal(strpos(st_global("dash_json_s19g"), char(34) + "expr" + char(34) + ":" + char(34) + "x/100" + char(34) + "," + char(34) + "yname" + char(34) + ":" + char(34) + "z" + char(34)) > 0))
    _w30_expect KT-02 "(`s19_yn' == 1)" "the registered spec does not carry expr x/100 and yname z"
    _w30_done KT-02 "a function layer is keyed by the name before its =, in both modes"

    // KT-03: range and pc layers join both variables (R04, P01).
    _s19_case KT-03 keys "(rcap mpg turn weight)" "legend(on)" "Mileage (mpg)/Turn circle (ft.)"
    _s19_case KT-03 keys "(pcspike mpg weight turn length)" "legend(on)" "Mileage (mpg)/Turn circle (ft.)"
    _w30_done KT-03 "rcap and pcspike keyed L(y1)/L(y2) in both modes"

    // KT-04: scatteri and pci (I01, I05).
    _s19_case KT-04 keys "(scatteri 20 3000 25 3500)" "legend(on)" "y"
    _s19_case KT-04 keys "(scatter mpg weight) (pci 20 3000 25 3500)" "" "Mileage (mpg)|y/yb"
    _w30_done KT-04 "scatteri keyed y and pci y/yb in both modes"

    // KT-05: the served keys survive a filter move.
    _s19_case KT-05 keys-move "(scatter mpg weight) (lowess mpg weight)" "" "Mileage (mpg)|lowess mpg weight"
    _w30_done KT-05 "the served app keeps twoway's keys after a filter move"

    // KT-06..KT-11 (commit 2): default titles by the first-equals-last rule.
    _s19_case KT-06 titles "(scatter mpg weight) (scatter mpg length) (scatter mpg weight)" "" "y1=Mileage (mpg)|y2=|x1=Weight (lbs.)|x2="
    _s19_case KT-06 titles "(scatter mpg weight) (scatter mpg length) (scatter mpg length)" "" "y1=Mileage (mpg)|y2=|x1=|x2="
    _w30_done KT-06 "an axis is titled when its first and last series agree (K01, K02)"
    _s19_case KT-07 titles "(scatter mpg weight) (scatter price weight)" "" "y1=|y2=|x1=Weight (lbs.)|x2="
    _s19_case KT-07 titles "(lpoly mpg weight)" "legend(on)" "y1=lpoly smooth: Mileage (mpg)|y2=|x1=lpoly smoothing grid|x2="
    _w30_done KT-07 "differing layers leave the axis untitled; a fit titles it in its own text (M01, F04)"
    _s19_case KT-08 titles "(rcap mpg turn weight)" "" "y1=Mileage (mpg)/Turn circle (ft.)|y2=|x1=Weight (lbs.)|x2="
    _s19_case KT-08 titles "(pcspike mpg weight turn length)" "" "y1=Mileage (mpg)/Turn circle (ft.)|y2=|x1=Weight (lbs.)/Length (in.)|x2="
    _s19_case KT-08 titles "(function y=x^2, range(0 2))" "" "y1=y|y2=|x1=x|x2="
    _w30_done KT-08 "range, pc and function layers are titled as twoway titles them (R04, P01, F10)"
    _s19_case KT-09 titles "(scatter mpg weight) (lfit price weight, yaxis(2))" "" "y1=Mileage (mpg)|y2=Fitted values|x1=Weight (lbs.)|x2="
    _s19_case KT-09 titles "(scatter mpg weight) (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(2))" "" "y1=Mileage (mpg)|y2=|x1=Weight (lbs.)|x2="
    _s19_case KT-09 titles "(scatter mpg weight) (rcap mpg turn weight, yaxis(2))" "" "y1=Mileage (mpg)|y2=Mileage (mpg)/Turn circle (ft.)|x1=Weight (lbs.)|x2="
    _w30_done KT-09 "axis 2 is titled by its own series (M07, M12, G23)"
    _s19_case KT-10 titles "(scatter mpg weight) (scatter price weight)" "by(foreign)" "y1=|y2=|x1=Weight (lbs.)|x2="
    _s19_case KT-10 titles "(rcap mpg turn weight)" "by(foreign)" "y1=Mileage (mpg)/Turn circle (ft.)|y2=|x1=Weight (lbs.)|x2="
    _w30_done KT-10 "every by() panel follows the rule (G05, G20)"
    _s19_case KT-11 titles-move "(scatter mpg weight) (scatter price weight)" "" "y1=|y2=|x1=Weight (lbs.)|x2="
    _w30_done KT-11 "the served app keeps the default titles after a filter move"

    capture dash clear
    macro drop S19_*
```

A `want` string is twoway's measured value (E6, research table); `_s19_case` also checks twoway against it, so a want twoway's own drawing contradicts is a plan error: stop and report, never edit the want to match dash. Expected at the batch-7 base: KT-01..KT-04 FAIL (dash `Fitted values`, `Mileage (mpg)`, `pcspike`, no legend, `scatteri`), KT-05 FAIL on its keys; after commit 1, KT-01..KT-05 PASS and every case KT-06..KT-11 FAILS until commit 2 (only KT-06's first line, K01, already matches).

### The area case KT-12 in `test/test_parser.cscript` (R1; message checks join their area script)

Appended after the LB-43 block's `macro drop lb_pfail` and before `capture erase "`c(tmpdir)'dash_p1a_run.log"` (P1A-71 at :1152-1180 is the function-refusal block it extends):

```stata
// ================================================================
// KT-12 (WP-30 P1.16) -- a function's y name is any Stata name, as in
// twoway (twoway__function_gen's confirm name): `function _y =' and
// `function ü =' are refused "nothing found where expression expected",
// r(111), as twoway refuses them, and nothing is registered; the spec
// carries the name beside the expression.  dash said "error in
// expression: ", r(111) (measured at c96facd).
// ================================================================
sysuse auto, clear
dash clear
foreach form in "function _y =, name(kt12)" "function ü = , range(0 1)" {
    _p1a_logrun `"dash `form'"'
    local rckt = r(rc)
    cert_file_has "`r(log)'", needle("nothing found where expression expected")
    if `rckt' != 111 | !r(found) {
        display as error `"KT-12 FAIL: dash `form' gave rc `rckt'"'
        exit 9
    }
}
assert "${dash_graph_registry}" == ""
_dash_process_segment "function _y = x^2, range(0 2)" _ptk12 _jsk12
assert strpos(`"`_jsk12'"', `""expr":"x^2","yname":"_y""') > 0
display "KT-12 PASS: function _y = and function ü = are refused r(111) in twoway's words; the spec carries yname"
```

**Running.** Driver only (index "The cscript driver"): `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_test_wp30_truth.do"`, then `WP30_ONLY=S19 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_wp30_truth.do"` (log `$S/run_test_wp30_truth.log`); likewise `test_parser.cscript` (no gate; log `$S/run_test_parser.log`). A SKIP (rc 222, `python_exec` dropped from `~/.stata19/console/stata19.rc`) is not a pass.

## TDD test stubs

All in the new `test/test_series_labels.py` unless named otherwise. Module docstring: the defect (Overview), E6's table and rule, the fixture. Imports: `dash_render as dr`; from `test_unlabelled_variables`: `_spec`, `_build`, `_saved`, `_served`, `_select`, `_filter`, `_text`; from `test_served_linked_views`: `_fire`; from `test_mode_parity`: `_spec as _mp_spec`, `_sc`; from `test_saved_filter_layers`: `_MOVES`, `_render`; from `test_saved_stale_cue`: `_act`, `_back`, `_items_of`, `_layer_rends`; from `test_server_layer_defects`: `plot_for`; `js_runner.requires_node`. `_FIX = json.load(test/fixtures/series_label_truth.json)`; `_AUTO_LABELS` = the fixture's auto `variableLabels`. A helper `_build_probe(mode, tmp_path, pid)` writes `_FIX["data"][ds]` to a file and the spec `_spec([(g, plots, go)])` from `_FIX["probes"][pid]["dash"]["graph"]` with `build_options["formats"] = _FIX["formats"][ds]` and `spec["function_points"] = {g: points}` when points is not null; `_summary(mode, obj)` returns `{"keys": sorted distinct visible series-legend item lists, "y1"/"y2"/"x1"/"x2": sorted distinct non-empty axis labels on left/right/below/above over every figure}`. `_NOT_YET_KEYS = {"F31": "P2.50", "L01": "P2.50", "L02": "P2.50", "L04": "P2.50", "L05": "P2.50", "G25": "P2.51", "L03": "P2.51", "L09": "P2.51", "G20": "P1.15c"}`.

**Commit 1 regression tests** (fail at the batch-7 base; 19-01, 19-02):
- Test: the fixture exists with `_meta` keys `stata_version`, `born_date`, `dash_commit`, `extracted`, `scheme == "stcolor"`, at least 150 probes, every twoway and dash rc 0 — `TestTheFixture::test_it_is_stamped`
- Test (guard on the fixture): for every probe without `by(`, `axis(2)`, `ts`, a quoted string or an `xtitle(`/`ytitle(`, `titles.y1 == "".join(svg_titles.left)` and `titles.x1 == "".join(svg_titles.bottom)` — `TestTheFixture::test_the_axis_objects_agree_with_the_drawing`
- Test: `_dash_layer_series` over a table of one spec per E6 row (auto labels; lowess, lpoly, mband, mspline, fpfit, function, lfit, qfit, every range type, every pc type, scatteri, pci, pcarrowi, histogram, kdensity, scatter, tsline) equals twoway's pair — `TestTheSeriesRule::test_each_type_gives_twoways_series[<type>]`
- Test: unlabelled `m2`: lowess `lowess m2 weight`, lpoly `lpoly smooth: m2`, fpfit `Predicted m2` (labels ignored for the names: labelled `mpg` gives `Predicted mpg`) — `TestTheSeriesRule::test_names_and_labels_as_twoway_uses_them`
- Test: `rcap turn t2` (same label) → `Turn circle (ft.)`; `pcspike mpg weight mpg weight` → `("Mileage (mpg)", "Weight (lbs.)")`; a missing `yvar2` → `L(yvar1)` — `TestTheSeriesRule::test_equal_or_missing_boundaries_give_one_label`
- Test: `lfitci` with `level(90)` → `[("90% CI", "Weight (lbs.)"), ("Fitted values", "Weight (lbs.)")]`; `default_level=99` and no level → `"99% CI"`; lpolyci's x is `lpoly smoothing grid` for both — `TestTheSeriesRule::test_a_ci_layer_is_two_series_band_first`
- Test: function `yname`: `z`, `_y`, `ü`, `日本`, `a½`, a 32-character name → itself; 33 characters, `1y`, `y z`, `a$b`, `<b>`, `""`, `None`, `5`, missing → `y`; x always `x` — `TestTheSeriesRule::test_a_function_is_named_as_twoway_names_it[<case>]`
- Test: totality: `None`, `[]`, `{"type": 3}`, `options` a list, `var_labels` a list, `yvar` an int → no exception, a list of pairs of strings — `TestTheSeriesRule::test_it_is_total`
- Test: for every spec of the table, `_dash_legend_key(p, vl) == _dash_layer_series(p, vl)[-1][0]`; `{"type": "scatter"}` → `"scatter"` — `TestTheLegendKeys::test_the_key_is_the_last_series_y_label`
- Test: `_dash_legend_keys` on a figure with an lpolyci layer (`plot_for("lpolyci")`, unlabelled data) → `[(1, "95% CI"), (2, "lpoly smooth: mpg")]` by number and text — `TestTheLegendKeys::test_a_ci_layer_keys_its_band_and_its_line`
- Test (both modes): `scatteri` alone with `legend(on)` → keys `["y"]` visible; two scatteri → `["y", "y"]`; beside a scatter → `["mpg", "y"]`; alone without `legend(on)` → its one key in a hidden legend, as every one-key graph — `TestScatteriKeys::test_alone_with_legend_on[saved|served]`, `::test_two[saved|served]`, `::test_beside_a_scatter[saved|served]`, `::test_alone_is_hidden_without_legend_on[saved|served]`
- Test (both modes, fixture): for every probe not in `_NOT_YET_KEYS`, the dash keys equal twoway's (sorted) — `TestKeysMatchTwoway::test_keys[<pid>-saved|<pid>-served]` (300 ids; the ones that already match are guards, listed apart in the failure file)
- Test: served, in `test_served_names_survive_a_move`'s harness: `_spec([("g1", [plot_for("scatter", yvar="y", xvar="x"), plot_for("lowess", yvar="y", xvar="x"), plot_for("rcap", yvar1="y1", yvar2="y2", xvar="x")], {})], filters=[_filter("x", "range")])`, `_build("served", …)`: keys `y`, `lowess y x`, `y1/y2`, and `_summary` equal before and after `_fire(doc, "x", (4.0, 24.0))` — `TestKeysAfterAFilterMove::test_served_keys_survive_a_move`
- Test (node): saved `_render(_mp_spec([plot_for("scatter"), plot_for("lowess")], {"filter": _MOVES[1][1]}))` (the range move): after `_act`, the lowess key is `"lowess mpg weight" + dr._DASH_STALE_SUFFIX["fit"]`; after `_back`, `"lowess mpg weight"` — `TestKeysAfterAFilterMove::test_saved_stale_cue_marks_the_new_key`
- Test: the generated app, executed, defines `_dash_layer_series` and `_DASH_FIT_KEYS == dr._DASH_FIT_KEYS` — `TestTheServedCopy::test_the_app_carries_the_key_names`
- Test (cscript): KT-01..KT-05 in `test/test_wp30_truth.cscript`; KT-12 in `test/test_parser.cscript`.

Guards for commit 1 (pass at the base, listed apart): `TestKeysMatchTwoway` ids that already match (scatter-only, lfit/qfit, histogram, kdensity, D probes); `TestTheLegendKeyRule::test_the_level_reaches_the_band_key`; `test_parser.cscript` P1A-71; `TestKeysMatchTwoway::test_the_residuals_still_differ[<pid>]` (each `_NOT_YET_KEYS` probe's keys still differ from twoway's, and its value names its owner; a listed probe that matches after the fix is removed from the list and named in the commit body).

**Commit 2 regression tests** (fail on the commit-1 tree; 19-09):
- Test: `_dash_axis_default_titles` on the K01-K11 sequences, K05/K06's CI series, M01, M04, U03, an empty list and a list of non-dicts gives E6's (x, y) — `TestTheAxisTitleRule::test_first_equals_last[<case>]`
- Test: per-axis selection: M05, M07, M12, K11, M15, M16, H05 for `yaxis=2`/`xaxis=2`; a layer with `{"yaxis": "1 2"}` counts on both — `TestTheAxisTitleRule::test_each_axis_has_its_own_series`
- Test: totality as for the series rule — `TestTheAxisTitleRule::test_it_is_total`
- Test: `_dash_axis_labels` keeps `xtitle("A")`, `ytitle("")`, `ytitle(, suffix)` and `ytitle(, size(large))` with an empty default untitled (H20) — `TestTheAxisLabels::test_explicit_titles_are_unchanged`
- Test (both modes, fixture): for every probe, dash's `y1`, `y2`, `x1`, `x2` (distinct non-empty labels per side over every panel) equal twoway's axis-object titles (`""` as none) — `TestTitlesMatchTwoway::test_titles[<pid>-saved|<pid>-served]`. H01 and H02 are expected to match by axis number (their difference is the side, P2.52); if either differs in text after the fix, it goes into `_NOT_YET_TITLES = {pid: "P2.52"}` with a guard like the keys' one, and the measured values go into the commit body
- Test (both modes): `(scatter mpg) (lfit price, yaxis(2))` y2 `Fitted values`; `(scatter mpg) (scatter mpg, yaxis(2)) (scatter price, yaxis(2))` y2 none; by() draws no axis-2 title (r7, guard) — `TestTheSecondAxis::test_a_fit_titles_axis_2[saved|served]`, `::test_disagreeing_layers_leave_axis_2_untitled[saved|served]`, `::test_by_draws_no_axis_2_title[saved|served]`
- Test: served, same harness, `(scatter y x) (scatter y2 x)` and `(rcap y1 y2 x)` graphs with the x range filter: titles x `x`, y none, and y `y1/y2` for the rcap graph, equal before and after `_fire(doc, "x", (4.0, 24.0))` — `TestTitlesAfterAFilterMove::test_served_titles_survive_a_move`
- Test: the generated app defines `_dash_axis_default_titles` — `TestTheServedCopy::test_the_app_carries_the_title_helper`
- Test: dash.sthlp holds "Legend keys and default axis titles", "when the last series drawn on it has the same label", "{cmd:lowess} {it:yvar xvar}" and "by the rule of the first axis" (whitespace-normalised) — `TestTheHelp::test_the_help_states_the_key_and_title_rules`
- Test (cscript): KT-06..KT-11.

Pinned tests flipped: E8's 14 nodes in 19-07 and 1 node in 19-11.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Series table, key helper | pytest `TestTheSeriesRule`, `TestTheLegendKeys` | literal specs, auto labels | n/a (one function both modes copy) |
| Title helper | pytest `TestTheAxisTitleRule`, `TestTheAxisLabels` | literal specs | n/a |
| 150 twoway probes | pytest `TestKeysMatchTwoway`, `TestTitlesMatchTwoway` | `series_label_truth.json` | yes |
| scatteri legend, axis 2 | pytest `TestScatteriKeys`, `TestTheSecondAxis` | literal specs | yes |
| After a filter move | pytest `TestKeysAfterAFilterMove` (served `_fire`; saved node stale cue), `TestTitlesAfterAFilterMove`; cscript KT-05, KT-11 | literal; sysuse auto | yes |
| Served wiring | `TestTheServedCopy`; G4 guards | generated app | served |
| Live twoway against dash | cscript KT-01..KT-11 | sysuse auto | yes |
| dash.ado name and message | cscript KT-02 (spec), KT-12 (refusal) | sysuse auto | n/a |
| Parity | `test_mode_parity.py` two CORPUS cases | `_DF` | yes |
| Help | `TestTheHelp` | dash.sthlp | n/a |
| Registries and tracking | `test_function_test_map.py`, `test_cscript_hygiene.py`, `test_tracking_documents.py`, `test_fixtures_are_committed.py` | — | n/a |

**Acceptance criteria.**
- **AC-19.1** (BR-19.1, BR-19.3) `TestKeysMatchTwoway` passes for every probe outside `_NOT_YET_KEYS` in both modes; `TestScatteriKeys` passes; KT-01, KT-03, KT-04 PASS.
- **AC-19.2** (BR-19.2) `test_a_function_is_named_as_twoway_names_it` passes; KT-02 and KT-12 PASS; P1A-71 still PASS.
- **AC-19.3** (BR-19.4, BR-19.5) `TestTheAxisTitleRule`, `TestTitlesMatchTwoway` (all 150 probes, both modes) and `TestTheSecondAxis` pass; KT-06..KT-10 PASS.
- **AC-19.4** (BR-19.6) `TestTheAxisLabels` and the unchanged `test_textbox_no_text.py`, `test_legend_order.py`, `test_axis2_suboptions.py` pass.
- **AC-19.5** (BR-19.7) both `AfterAFilterMove` classes pass (the node test is not skipped); KT-05, KT-11 PASS; `test_mode_parity.py` passes with the two new CORPUS cases.
- **AC-19.6** (BR-19.8) `_MUST_WARN` and `ALLOWED` are untouched; `test_the_residuals_still_differ` passes and names P2.50, P2.51, P1.15c.
- **AC-19.7** The 15 flipped nodes pass with their new expectations; the full suite through the queue reports 0 failed before each commit; G7 prints 0 twice per commit.

## Tasks

**Commit boundary.** Tasks 19-01 to 19-08 form commit 1, made by 19-08 on `wp30-s19` with the subject `Key every layer in twoway's text, part 1 of 2: legend keys (WP-30 P1.16)`; it leaves the BUGS.md entry, its `WP30_OPEN` key and its marker in place (A156). Tasks 19-09 to 19-13 form commit 2, made by 19-13 with the subject `Title each axis by twoway's first-equals-last rule, part 2 of 2: default titles (WP-30 P1.16)`; it closes all three. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s19`; every command uses `git -C "$WT"` or `$WT` paths, never the main checkout.

<task type="auto" id="19-01">
  <name>Write the key tests and record them</name>
  <files>scripts/extract_series_label_truth.do, test/test_series_labels.py, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-7-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s19`; stop otherwise. Create `scripts/extract_series_label_truth.do` exactly as "Stata truth" describes (S02's stanza, the data export through `_dash_write_stata_data`, the 150 `zk` lines verbatim, the trailing reader) and run it with `DASH_REPO="$WT"` through the slot; it writes `test/fixtures/series_label_truth.json`. Create `test/test_series_labels.py` with every commit-1 stub of "TDD test stubs" (the helpers `_build_probe`, `_summary`, `_NOT_YET_KEYS`); name new functions as `dr._dash_layer_series` and `dr._DASH_FIT_KEYS` so they fail with AttributeError now. In `test/test_wp30_truth.cscript` put the python helpers and `_s19_case` directly above S01's `* ==== S19 P1.16: …` header and KT-01..KT-05 between S01's S19 start and end lines. Run `python3 -m pytest test/test_series_labels.py -q -n 6 -p no:cacheprovider -rf > "$S/19-new-1.log" 2>&1` and the S19 block through the driver. Write `$S/19-P1.16-1-failure.txt`: the base sha, one line per failing node from `19-new-1.log`, the KT lines of the driver log, then a "Guards (pass at the base)" list. Edit neither dash_render.py nor dash.ado; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/series_label_truth.json')); m=d['_meta']; print(m['probes'], m['scheme'], all(k in m for k in ('stata_version','born_date','dash_commit','extracted')))"` prints `150 stcolor True`; `grep -c FAILED "$S/19-new-1.log"` is at least 60; `grep -cE "KT-0[1-5] FAIL" "$S/run_test_wp30_truth.log"` is at least 4; `git -C "$WT" diff --name-only -- dash_render.py dash.ado` prints nothing.]]></verify>
  <done>The 150-probe twoway fixture existed and every key regression test was shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="19-02">
  <name>Record the function-name refusal case</name>
  <files>test/test_parser.cscript</files>
  <action><![CDATA[
    In `test/test_parser.cscript`, after the LB-43 block's `macro drop lb_pfail` and before `capture erase "`c(tmpdir)'dash_p1a_run.log"` (:2854 and :2856 at `c96facd`), insert the KT-12 block of "Stata truth" verbatim. Run the script through the driver (`run_test_parser.do`, log `$S/run_test_parser.log`) on the unmodified dash.ado; it must stop at KT-12 (every earlier case PASS). Append the KT-12 failure line and the measured message (`error in expression:`) to `$S/19-P1.16-1-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "P1A-71 PASS" "$S/run_test_parser.log"` prints 1; `grep -c "KT-12 FAIL" "$S/run_test_parser.log"` prints 1; `grep -c "KT-12" "$S/19-P1.16-1-failure.txt"` is at least 1.]]></verify>
  <done>The function-name refusal case was in its area script and shown failing on the unmodified dash.ado.</done>
</task>

<task type="auto" id="19-03">
  <name>Add the series rule and fit keys</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-19.1 (add `_DASH_FIT_KEYS` after `_DASH_CI_TYPES`, :26706; rewrite only the comment above `_DASH_FIT_TYPES`, :26695-26697), TR-19.2 (`_dash_layer_series` directly above `def _dash_legend_key`, with its docstring), TR-19.3 (`_dash_legend_key`'s body and docstring) and TR-19.4 (the CI branch and docstring of `_dash_legend_keys`). Impact is LOW for both edited functions (E9). Touch nothing else.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_series_labels.py -q -n0 -p no:cacheprovider -k "TestTheSeriesRule or TestTheLegendKeys"` passes; `python3 -m pytest "test/test_server_layer_defects.py::TestTheLegendKeyRule::test_the_level_reaches_the_band_key" test/test_legend_order.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Every layer's series labels came from one twoway table and the key functions read their text from it.</done>
</task>

<task type="auto" id="19-04">
  <name>Key scatteri and carry the names</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-19.5: `legend_label="y"` in `map_scatteri`'s `fig.scatter(...)` (:13714-13717) and the comment-only rewrite at :21442-21443 in `_dash_apply_legend` (UNKNOWN impact, confirmed by grep in E9; no code line changes). Apply TR-19.7 in `ServerAppBuilder._glyph_layer_lines` (HIGH: warn in the task log before editing): `"_DASH_FIT_KEYS",` on a new line after `"_DASH_FIT_TYPES", "_DASH_CI_TYPES",` and `"_dash_layer_series",` on a new line after `"_dash_legend_key", "_dash_legend_entries",`. Do not edit `_generate_app_source` (R12).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_series_labels.py -q -n 6 -p no:cacheprovider -k "TestScatteriKeys or TestTheServedCopy or TestKeysAfterAFilterMove"` passes; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>A scatteri layer had a key in both modes, and the served app carried the new names.</done>
</task>

<task type="auto" id="19-05">
  <name>Capture the function name in dash.ado</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-19.6 in `_dash_process_segment`'s function branch: the `_fn_yname` capture after :3679, the one-pattern strip at :3683 (`ustrregexra`), and the `"yname"` field at :4309-4312. `_dash_process_segment` is UNKNOWN to the index; its one caller `_dash_plot` (:5210) was confirmed by grep (E9). Edit no other line.
  ]]></action>
  <verify><![CDATA[`test_parser.cscript` through the driver prints `KT-12 PASS` and `All syntax-based parser tests PASSED.`; the S19 truth block through the driver (`WP30_ONLY=S19`) prints `KT-02 PASS`.]]></verify>
  <done>dash.ado wrote the function's Stata name into the spec and refused an empty function expression in twoway's words.</done>
</task>

<task type="auto" id="19-06">
  <name>Regenerate the fixture after the name</name>
  <files>test/fixtures/series_label_truth.json</files>
  <action><![CDATA[
    Copy the fixture to `$S/19-fixture-old.json`, re-run the extractor exactly as in 19-01, and compare with a scratch script `$S/19-cmp.py`: for every probe the `twoway` record and `ds`/`body`/`opts`/`rc` must be identical; `dash.graph` may differ only for the function probes F09, F10, F27, F28, G09, H11, M14, N01, N02, N03, and only by the added `yname` and the stripped `expr`; `_meta` may differ only in `dash_commit` and `extracted`. Save the comparison output to `$S/19-fixture-cmp.txt`. Never patch the file by hand (R7).
  ]]></action>
  <verify><![CDATA[`tail -1 "$S/19-fixture-cmp.txt"` reads `twoway unchanged: 150; dash changed: F09 F10 F27 F28 G09 H11 M14 N01 N02 N03`; `python3 -m pytest test/test_series_labels.py -q -n 6 -p no:cacheprovider -k "TestKeysMatchTwoway or TestTheFixture"` passes.]]></verify>
  <done>The committed fixture held dash's specs with function names and twoway's records unchanged probe by probe.</done>
</task>

<task type="auto" id="19-07">
  <name>Flip the pinned key tests</name>
  <files>test/test_server_layer_defects.py, test/test_immediate_dashboards.py, test/function_test_map.py</files>
  <action><![CDATA[
    Flip E8's 14 commit-1 nodes in place, each with a docstring sentence "Flipped (WP-30 P1.16): <old> was wrong because twoway keys it <new> (series_label_truth.json <probe>)": rename `test_a_computed_layer_is_keyed_fitted_values` to `test_a_computed_layer_is_keyed_as_twoway_keys_it`, keeping its parametrisation over `sorted(dr._DASH_FIT_TYPES)` and asserting a literal table (fpfit `Predicted mpg`, function `y`, lfit and qfit `Fitted values`, lowess `lowess mpg`, lpoly `lpoly smooth: mpg`, mband `Median bands`, mspline `Median spline`, for specs `{"type": t, "yvar": "mpg"}`); rename `test_a_ci_layer_is_keyed_fitted_values_on_its_own` to `test_a_ci_layer_is_keyed_by_its_line_on_its_own` (fpfitci `Predicted mpg`, lpolyci `lpoly smooth: mpg`, lfitci and qfitci `Fitted values`); rename `test_a_range_layer_uses_its_first_boundary` to `test_a_range_layer_joins_its_boundaries` (`{"type":"rbar","yvar1":"lo","yvar2":"hi"}` gives `lo/hi`, and `yvar1` alone `lo`); rename `test_a_layer_with_no_variable_is_keyed_by_its_type` to `test_an_immediate_layer_is_keyed_as_twoway_keys_it` (`pci` `y/yb`, `scatteri` `y`, `{"type":"scatter"}` `scatter`); `test_a_band_and_its_line_are_keyed_separately` asserts `["95% CI", <line>]` with lpolyci `lpoly smooth: mpg` and fpfitci `Predicted mpg`; `test_it_has_a_legend_key_as_twoway_gives_it` asserts `["y", "y/yb"]`. In `test/function_test_map.py` add TR-19.8's entry under the S19 anchor and re-point :559 in place. Run `test_server_layer_defects.py test_immediate_dashboards.py test_glyphs.py test_legend_order.py test_server_legend.py test_saved_stale_cue.py test_label_sinks.py test_mode_parity.py test_ci_band_style.py test_function_expr.py test_pccapsym_pcarrowi.py test_ci_plot_index.py test_colorvar_legend.py test_js_runner.py test_stale_cue_browser.py test_function_test_map.py` with `-n 6`; a failure that pins old key text is flipped here the same way, anything else stops the task. Write one `Flipped:` line per flipped node (R9 form) to `$S/19-flips-1.txt`; delete no test.
  ]]></action>
  <verify><![CDATA[The 16-file run reports 0 failed; `wc -l < "$S/19-flips-1.txt"` is at least 14; `grep -c "test_a_ci_layer_is_keyed_fitted_values_on_its_own" "$WT/test/function_test_map.py"` prints 0.]]></verify>
  <done>Every test that pinned dash's old keys asserted twoway's keys, with the reason recorded, and the map named existing tests.</done>
</task>

<task type="auto" id="19-08">
  <name>Check parity and commit the keys</name>
  <files>test/test_mode_parity.py</files>
  <action><![CDATA[
    Append to `CORPUS` (before its closing `]`, :1798 at `c96facd`, after any earlier section's case): `_case("Fit, range, pc and scatteri keys (WP-30 P1.16)", [_sc(), plot_for("lowess"), plot_for("lpolyci"), plot_for("rcap"), plot_for("pcspike"), plot_for("scatteri")])`; edit neither `ALLOWED` nor `_MUST_WARN` (R8). Run `test_mode_parity.py -k "keys (WP-30"`, `test_series_labels.py`, the S19 truth block and `test_parser.cscript` through the driver. Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`), one full run `"$S/full_suite_queue.sh" "$WT" "$S/19-full-1.log"` in the background, waiting for its `exit=` line and reading the log, never relaunching it (E6 for the known flaky tests). Stage exactly: dash_render.py dash.ado scripts/extract_series_label_truth.do test/test_series_labels.py test/test_wp30_truth.cscript test/test_parser.cscript test/test_server_layer_defects.py test/test_immediate_dashboards.py test/function_test_map.py test/test_mode_parity.py, and `git add -f test/fixtures/series_label_truth.json`; check `git -C "$WT" diff --cached --name-only` lists those 11 only (G6). Write `$S/19-message-1.txt` in the form of "Notes: commit messages", check G7, confirm the branch, commit, and check G7 on the committed message.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/19-full-1.log"` shows 0 failed and `exit=0`; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.16)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.16 -->' "$WT/CHANGELOG.md"` prints 1 (left for commit 2).]]></verify>
  <done>Commit 1 keyed every layer in twoway's text in both modes, green, with the entry, key and marker left for commit 2.</done>
</task>

<task type="auto" id="19-09">
  <name>Write the title tests and record them</name>
  <files>test/test_series_labels.py, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    On the tree commit 1 left, add the commit-2 stubs of "TDD test stubs" to `test/test_series_labels.py` (`TestTheAxisTitleRule`, `TestTheAxisLabels`, `TestTitlesMatchTwoway`, `TestTheSecondAxis`, `TestTitlesAfterAFilterMove`, `TestTheServedCopy::test_the_app_carries_the_title_helper`, `TestTheHelp`), naming `dr._dash_axis_default_titles`. Insert KT-06..KT-11 of "Stata truth" before the S19 block's end line. Run the new classes with `-n 6 -rf` into `$S/19-new-2.log` and the S19 block through the driver. Write `$S/19-P1.16-2-failure.txt`: the commit-1 sha, one line per failing node, the KT-06..KT-11 lines, then the guards that pass (`test_by_draws_no_axis_2_title`, the titles probes that already match, KT-01..KT-05). Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/19-new-2.log"` is at least 40; `grep -cE "KT-(0[6-9]|1[01]) FAIL" "$S/run_test_wp30_truth.log"` is at least 4; `git -C "$WT" diff --name-only -- dash_render.py dash.sthlp` prints nothing.]]></verify>
  <done>Every title regression test was shown failing on the tree commit 1 left, with the failure text saved.</done>
</task>

<task type="auto" id="19-10">
  <name>Choose default titles by twoway's rule</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_dash_axis_labels` and `_glyph_layer_lines` are HIGH (E9). Apply TR-19.9 (`_dash_axis_default_titles` directly above `def _dash_axis_labels`), TR-19.10 (replace `_dash_axis_labels`' `p0` reads and univariate branch, :21679-21694, by the helper; update its docstring), TR-19.11 (the non-by() default of `_dash_add_secondary_axes`, :23088-23093; its docstring) and TR-19.12 (`"_dash_axis_default_titles",` on a new line after `"_dash_axis_labels",` in the functions tuple). Edit neither `_make_figure_body` nor the template (R12).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_series_labels.py -q -n 6 -p no:cacheprovider` passes except `TestTheHelp`; the S19 truth block through the driver prints KT-01..KT-11 PASS; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Every axis, axis 2 included, was titled by twoway's first-equals-last rule in both modes and after a filter move.</done>
</task>

<task type="auto" id="19-11">
  <name>Flip the title pin and register</name>
  <files>test/test_unlabelled_variables.py, test/function_test_map.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    In `test/test_unlabelled_variables.py::TestAfterAFilterMove::test_served_names_survive_a_move` change `before[0]["y"] == ["y"]` to `before[0]["y"] == [None]` (Bokeh's value for an empty axis label) and add "Flipped (WP-30 P1.16): a y title 'y' was wrong because twoway draws none when the layers' labels differ (series_label_truth.json M08)". Add TR-19.12's map entry under the S19 anchor. Append a second CORPUS case `_case("First-equals-last titles and axis 2 (WP-30 P1.16)", [_sc(), plot_for("scatter", yvar="price"), plot_for("rcap", {"yaxis": "2"})])` (`plot_for`'s second argument is the options dict; a keyword sets a spec field). Run `test_unlabelled_variables.py test_axis2_suboptions.py test_dual_axis.py test_textbox_no_text.py test_axis_options.py test_graph_options.py test_scheme_rendered_output.py test_varlist_expansion.py test_date_units.py test_axis_extents.py test_server_facets.py test_label_sinks.py test_mode_parity.py test_function_test_map.py` with `-n 6`; a failure pinning old title text is flipped the same way, anything else stops. Write the `Flipped:` lines to `$S/19-flips-2.txt`; delete no test.
  ]]></action>
  <verify><![CDATA[The 14-file run reports 0 failed; `test -s "$S/19-flips-2.txt"`; `python3 -m pytest test/test_varlist_expansion.py -q -n0 -p no:cacheprovider -k single_y_output` passes (the single-y digest is not moved; if it fails, stop and report under R10).]]></verify>
  <done>The one test that pinned a first-layer title asserted twoway's rule, and the helper and parity case were registered.</done>
</task>

<task type="auto" id="19-12">
  <name>State the key and title rules</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-19.13: insert the new paragraph after "options -- see below." (:2254) and before `{synoptset 20}{...}` (:2256), and correct the three sentences at :635-637, :809-811 and :3010-3013 in place, finding each by its text since earlier batches may have moved it. Edit no other paragraph (R3/A155). Every new or changed line is at most 79 characters.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_series_labels.py::TestTheHelp" test/test_help_conformance.py -q -n 6 -p no:cacheprovider` passes; `awk 'length > 79' dash.sthlp | grep -c "first series"` prints 0.]]></verify>
  <done>The help listed twoway's key text per type and stated the first-equals-last title rule per axis and under by().</done>
</task>

<task type="auto" id="19-13">
  <name>Close the entry and commit titles</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.16"]`. Close that BUGS.md entry in place (`- [x]`) and replace its Resolution line with "Notes: BUGS.md Resolution", today's date as `ddmonyyyy`, keeping the two-space indent every BUGS.md Resolution line has (`  - Resolution: Fixed …`, TR-01.10 item 1). Delete the `"P1.16"` key line of `WP30_OPEN`. Replace `<!-- WP-30 P1.16 -->` in place with the two lines of "Notes: CHANGELOG lines". Run `test_tracking_documents.py test_cscript_hygiene.py test_fixtures_are_committed.py`; the S19 block and `test_parser.cscript` through the driver; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/19-full-2.log"` in the background, read when `exit=` appears. Stage exactly dash_render.py dash.sthlp BUGS.md CHANGELOG.md test/test_series_labels.py test/test_wp30_truth.cscript test/test_unlabelled_variables.py test/function_test_map.py test/test_mode_parity.py test/test_tracking_documents.py and check the staged list is those 10 (G6). Write `$S/19-message-2.txt`, check G7, confirm the branch, commit, check G7 again, and report both shas and messages to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/19-full-2.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.16 -->' "$WT/CHANGELOG.md"` prints 0; `cd "$WT/test" && python3 -c "import test_tracking_documents as t; print('P1.16' in t.WP30_OPEN, 'P1.16' in t.WP30_LISTS)"` prints `False True` (`WP30_LISTS` and `WP30_SECTION` keep the key for good, TR-01.2, so a plain grep of the file is never 0); `git -C "$WT" log -2 --format=%s` shows both subjects ending `(WP-30 P1.16)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.16 was closed naming existing tests, its marker carried the measured old and new texts, and two green commits on wp30-s19 were ready for the merger.</done>
</task>

## Section completion criteria

- Every layer is keyed in twoway's text and every axis titled by twoway's first-equals-last rule, per axis and per panel, in the saved page and the served app, before and after a filter move (pytest fixture classes over 150 probes, KT-01..KT-11).
- `_dash_layer_series`, `_dash_axis_default_titles` and `_DASH_FIT_KEYS` exist, are mapped and travel to the served app; `_DASH_FIT_TYPES` is kept; dash.ado writes `"yname"`; `function _y =` is refused in twoway's words (KT-12).
- `test/fixtures/series_label_truth.json` is generated by `scripts/extract_series_label_truth.do`, stamped, committed with `-f` and read by a test.
- The 15 pinned nodes are flipped in place with their reason; no test is deleted; the residual probes are asserted to still differ and name P2.50, P2.51 and P1.15c.
- Two green commits `(WP-30 P1.16)` exist on `wp30-s19`; the second closes the entry, deletes its key, replaces its marker and updates the help. No file outside the two staged lists changes.

## Notes

- **Order inside commit 1.** The fixture's dash specs are recorded by dash.ado, so 19-06 regenerates it after 19-05; a fixture regenerated before the dash.ado edit keys F28 `y`, not `z`.
- **Raw text.** Compare and store raw labels. S09's `_dash_finish_graph_text` (landed in batch 3) breaks TeX pairs at the sink after the keys and titles are set, and S29 adds SMCL there; neither may be called from these helpers.
- **Key by `type`.** S45 keeps `type` and writes `recast` (A60); never key by a drawn glyph.
- **The served template comment** at dash_render.py:35443-35446 ("lowess, scatteri and pci pass no label") becomes stale after commit 1; it is in `_generate_app_source`, S21's this batch (R12), so it is left for the closeout.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the extractor's python block and the truth script then fail or SKIP. Check the file after each slot run.
- **Merge rules for the shared files.** R1: the S19 block and its helpers above its header; KT-12 at the end of `test_parser.cscript` (S19 is its only batch-7 editor; S20's cases go to `test_varlist_expansion.cscript`). R2: `"_DASH_FIT_KEYS"` at S19's constants anchor; `"_dash_layer_series"` after `"_dash_legend_key", "_dash_legend_entries",` (an addition to R2's S19 row, at an anchor no batch-7 section uses); `"_dash_axis_default_titles"` at S19's function anchor; two map keys under S19's anchor and one in-place value at :559. R3/A155: Statistical Layer Options (S19's row) plus three in-place sentences no batch-7 partner owns (an addition to R3's row; S20's :740-742 and S21's :2811 are separate paragraphs). R4: the one `P1.16` marker, replaced by commit 2 only. R5: the `P1.16` entry and key only. R7: one new fixture and extractor, never hand-patched. R8: two CORPUS cases appended; `ALLOWED`/`_MUST_WARN` untouched. R9: E8's flips. R10: no pin moved. R12: neither `_make_figure_body` nor `_generate_app_source` is edited.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name only `_dash_layer_series`, `_dash_legend_key`, `_dash_legend_keys`, `_dash_apply_legend` (comment), `GlyphMapper.map_scatteri`, `_glyph_layer_lines` and two constants for commit 1, and `_dash_axis_default_titles`, `_dash_axis_labels`, `_dash_add_secondary_axes` and `_glyph_layer_lines` for commit 2, plus test symbols of the staged files.
- **Commit messages.** Subjects as in "Commit boundary". Body, in order: the failure file (`$S/19-P1.16-1-failure.txt` / `-2-`); the measured defect (Overview's rows); what changed and where (TR-19.1-TR-19.8 / TR-19.9-TR-19.13, both modes); then one line each: `Regression: test/test_series_labels.py::<Class>::<test> -- failed at <base sha> with <text>` for each regression node (cscripts as `test/test_wp30_truth.cscript KT-01` and `test/test_parser.cscript KT-12`); the `Flipped:` lines of `$S/19-flips-<k>.txt`, e.g. `Flipped: test/test_server_layer_defects.py::TestTheLegendKeyRule::test_a_computed_layer_is_keyed_fitted_values[lowess] -- "Fitted values" was wrong because twoway keys lowess "lowess <y> <x>"`; commit 1 also `Fixture: test/fixtures/series_label_truth.json (scripts/extract_series_label_truth.do)` and no `BUGS.md:` line (TR-01.10 item 7: a two-commit section's first commit has none); commit 2 `BUGS.md: "Legend keys and default axis titles do not follow twoway: fits are keyed Fitted values, pc and immediate types by their type name, the y title follows the first layer, and range types get none" (closed)` (section-01 Appendix B's title, verbatim; 19-13 checks it equals `WP30_OPEN["P1.16"]` before deleting the key). No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.16). Legend keys and default axis titles follow twoway's measured text and rule in the saved page and the served app, before and after a filter move: _dash_layer_series gives each layer twoway's series labels (lowess mpg weight, lpoly smooth: Mileage (mpg), Median bands, Median spline, Predicted mpg, a function's own Stata name or y, L(y1)/L(y2) for range and pc layers, y for scatteri, y/yb for pci and pcarrowi, a ci fit's band then line), _dash_legend_key and _dash_legend_keys key from it, map_scatteri gives scatteri a key, and dash.ado writes the function's name (any Unicode Stata name of at most 32 characters) as yname; _dash_axis_default_titles titles each axis with its first series' label when its last series has the same label, else none, used by _dash_axis_labels and, per axis, by _dash_add_secondary_axes. Pinned by test/test_series_labels.py::TestKeysMatchTwoway::test_keys, test/test_series_labels.py::TestTitlesMatchTwoway::test_titles, test/test_series_labels.py::TestTheAxisTitleRule::test_first_equals_last, test/test_series_labels.py::TestKeysAfterAFilterMove::test_served_keys_survive_a_move, test/test_wp30_truth.cscript KT-01, test/test_parser.cscript KT-12; fixture test/fixtures/series_label_truth.json. Residual, deferred (WP-30): keys twoway merges (P2.50), the legend twoway leaves off histogram-only graphs (P2.51), the first-used axis drawn left or bottom (P2.52), one legend under by() (P1.15c).
  ```
- **CHANGELOG lines** (replacing `<!-- WP-30 P1.16 -->` in place, Results that change; old values from Overview and E1-E5):

  ```
  - Legend keys are twoway's text, in both modes: `dash (scatter mpg weight) (lowess mpg weight)` keyed the fit `Fitted values` and now `lowess mpg weight`; lpoly `lpoly smooth: Mileage (mpg)`, mband `Median bands`, mspline `Median spline` and fpfit `Predicted mpg` (and the lines of lpolyci and fpfitci) were `Fitted values`; `function z=x/100` was `Fitted values` and is now `z` (`y` with no name; any Stata name, `_y` and `ü` included); `(rcap mpg turn weight)` was `Mileage (mpg)` and `(pcspike mpg weight turn length)` `pcspike`, now both `Mileage (mpg)/Turn circle (ft.)`; pci was `pci` and is `y/yb`; scatteri was `scatteri` and is `y`, and `(scatteri 20 3000 25 3500), legend(on)` now draws its key; `dash function _y =` said `error in expression:` and now says twoway's `nothing found where expression expected`, r(111) as before. (WP-30, P1.16)
  - Default axis titles follow twoway's rule on each axis: the first series' label when the last series' label is the same, else none: `dash (scatter mpg weight) (scatter price weight)` was titled `Mileage (mpg)` and now has no y title; `(scatter mpg weight) (lowess mpg weight)` loses its y title; `(lpoly mpg weight)` is titled `lpoly smooth: Mileage (mpg)` and `lpoly smoothing grid` (was `Mileage (mpg)` and `Weight (lbs.)`); `(rcap mpg turn weight)` and `(pcspike mpg weight turn length)` had no title and are titled `Mileage (mpg)/Turn circle (ft.)` (pcspike's x `Weight (lbs.)/Length (in.)`); `function y=x^2` is titled `y` and `x`; on `yaxis(2)`, `(scatter mpg weight) (lfit price weight, yaxis(2))` was titled `Price` and is `Fitted values`, and `(scatter mpg weight) (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(2))` was `Mileage (mpg)` and is untitled. (WP-30, P1.16)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md A13** (:291-306): `- **Tracked:** Closed in WP-30, BUGS.md "<P1.16 title>", commits <sha1>, <sha2>`, with `(WP-30, GAPS2-A13)` appended to the Resolution; C10 (:723, :776) has no heading of its own and is tracked through A13. The Gap line's anchors (dash_render.py:19500-19505, :16003-16038) are stale: `_DASH_FIT_TYPES` was at 26699 and `_dash_axis_labels` at 21665 at `c96facd`.
  - **DROPIN-REMAINING.md:113-120 (P1.16):** "Closed by <sha1>, <sha2> (WP-30 S19). Keys twoway merges, histogram-only legends and the first-used axis's side are P2.50-P2.52; one legend under by() is P1.15c."
  - **BUGS.md:2742, :2748, :2754** (closed WP-29 entries): their residuals "per-type fit keys", "no title when an axis's layers differ", "y1/y2 range titles" and "the second axis's default title" are closed by this entry.
  - **ROADMAP:** P2.50, P2.51, P2.52 rows (register), each with E7's measured probes.
  - **The served template comment** at dash_render.py:35443-35446 is stale (scatteri now passes a label); the next `_generate_app_source` editor or S58 corrects it.
  - **AGENTS.md invariant:** "legend keys come only from `_dash_layer_series`; default axis titles only from `_dash_axis_default_titles` (twoway's first-equals-last rule per axis); both are raw text."
  - **Unverified:** whether the label strings ("Median spline", "lpoly smooth:", "Predicted") are the same in Stata 14-18.5 was not measured (research UNCLEAR); under M2 dash requires Stata 19, so it is moot.
