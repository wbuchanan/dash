# Section 03: Default and empty titles

> Part of: WP-29 · P0: P0.3, P0.4 · Risk: yellow · Batch: 1 · Depends on: 01 · Blocks: 10 · Tasks: 19, 2 commits (P0.3, then P0.4) · Case prefixes: UL, ET

## Review amendments (binding; they override any conflicting text below)

> Units u03-unlabelled (P0.3) and u04-empty-title (P0.4), both reviewed "sound with amendments". Architect decisions A3, A4, A5, A7, A10 and merge rules R1, R2, R5, R7, R8 of `index.md` apply. Every amendment below is applied in the text of this section.

**u03 (P0.3)**
- **A1 — the red-first list is re-measured, never trusted.** The design named 3 tests that the jsonio-faithful helper turns red. The reviewer measured 11 more in 15 other files (`11 failed, 2320 passed`; the same nodes pass at HEAD). Task 03-05 runs all 94 `test/test_*.py` files that use `make_data_json` under the flipped helper on the unfixed tree, and records the complete list. `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` is never re-baselined (R7).
- **A2 — univariate keys are pulled in.** `_dash_legend_key` is rewritten here, so it keys `histogram` by its y-scale word (`Density`, `Percent`, `Frequency`, `Fraction`) and `kdensity` as `kdensity <name>`, as twoway does (HK.svg, KD2.svg, KDLAB.svg, HPLAB.svg). Without this, `(histogram x)(kdensity x)` would regress from `['histogram','kdensity']` to the duplicate `['x','x']`. `test_server_layer_defects.py::TestTheLegendKeyRule::test_a_univariate_layer_uses_its_var_key` is flipped (`'mpg'` → `'Density'`). This partly closes GAPS2-A13/C10 (P1.16); the hand-off is in Notes for the closeout.
- **A3 — the tooltip fallback stops naming unrelated variables.** In `_dash_build_hover`, a generic computed column (`x`, `y`, `y1`, `y2`) is named after a same-named dataset variable only when that variable is one the layer plots (`xvar`, `y1var`, `y2var`). Otherwise it takes the layer's label. Both modes are tested.
- **A4 — the by() test does not pin repeated titles.** It asserts that the set of non-empty titles over all panels is `{'x','y'}`, not that every panel carries both (P1.15 removes the repeats).
- **A5 — `_dash_var_label` is total.** `None` and `""` give the default. Any other non-string name gives `str(name)`, never a `TypeError`.
- **A6 — the no-rewrite test is strict.** It walks every `CustomJS.code` in a built saved page and every module-level JavaScript string of `dash_render`.
- **A7 — cscript details.** These are rewritten for `test/test_wp29_truth.cscript` (architect A3), which has no `_tbg_*`/`_lo_*` helpers. The S03 blocks define their own `_s03_*` python helpers, outside the `if` gate.
- **A8 — the axis-2 default title is fixed here, not deferred.** It lands as part B of the P0.4 cycle and defaults through `_dash_axis_labels`, therefore through `_dash_var_label`. No new P1 item is needed.
- **A9 — one rule for the by() note.** The future P1.15 "Graphs by" note must use `_dash_var_label`: `Graphs by Group` with `g` labelled, `Graphs by g` without (BYL.svg, I.svg). This is recorded for S15.

**u04 (P0.4)**
- **A1 — one widened separator regex.** `_TEXTBOX_SUBOPT_RE` becomes `re.compile(r",\s*(?=[A-Za-z_,]|\Z)")`. There is no `_TEXTBOX_EMPTY_TAIL_RE` and no new constant in the copy list (R2 row S03).
- **A2 — empty sub-option slots are silent.** `_dash_textbox` skips comma-only tokens before naming unhonoured sub-options. This also removes the echo-amplification path (a 200,057-character note for `','*200000`).
- **A3 — no axis-2 default under by().** twoway draws no axis-2 title in a by() graph (r7, s1-s3). The default is `""` whenever `graph_options['by']` is non-blank. The divergence where an explicit title is drawn on every panel goes to P1.15 through S15.
- **A4 — the rule as stated in the help.** "The first comma outside strings and parentheses that is followed, after blanks, by a name, another comma, or the end opens the sub-options; empty slots are ignored." `ytitle(A,,)` is `ytitle(A)`.
- **A5 — pins for `""` with suffix.** `ytitle("", suffix)` keeps the default (r5). `ytitle(, axis(2) suffix)` gives the axis-2 default (r13).
- **A6 — a univariate layer on axis 2.** `(scatter mpg weight) (histogram weight, yaxis(2))` titles axis 2 `Density` (r8).
- **A7 — the fixture decides A1-A3.** It records `ytitle(A,,)`, `ytitle(A, ,)`, `ytitle(,,)`, `ytitle(A, size(large),)`, `ytitle(A,) ytitle(, size(large))`, `ytitle(,) ytitle(, size(large))`, `ytitle("", suffix)` and the by() dual-axis control.
- **A8 — parity under `ylabel(, labsize(large))`.** The second axis is equal in both modes under this option.

**Section-level decisions (this file)**
- **D-03a.** Part B (the axis-2 default title and its scheme style) lands inside the P0.4 commit, so the section keeps the manifest's 2 fix commits.
  - It is required by BR-29.3: `ytitle(, axis(2) size(large))` must keep twoway's default `Price` at large.
  - It is also required by u03 A8.
- **D-03b.** The regenerated `text_truth.json` gains an additive per-probe key `text_records` (`[text, size, fill, rotate]` in document order). This replaces the design's `{text: fill}` map.
  - Both maps keyed by text lose duplicates. Measured: in b1 `Price` is drawn twice, the rotated axis title at 157.44 and the legend key at 112.56, and `text_sizes` keeps only one of them.
- **D-03c.** R2 row S03 gains two anchors the index did not list: `_dash_filter_base_title` after `"_dash_filter_title"` (28716) and `_dash_textbox_or_default` after `"_dash_textbox"` (28799).
- **D-03d.** `test/test_mode_parity.py` is added to the P0.4 cycle's files: gate G3 requires the section's CORPUS cases. After the helper flip every existing CORPUS case is unlabelled data, so P0.3 needs none.
- **D-03e.** Open questions are settled as follows:
  - The interim multi-layer y title is accepted (P1.16).
  - Labels are not capped at 80 characters.
  - Filter widgets keep the saved rule that a label of blanks falls back to the name.
  - `ytitle(, size(bogus))` is unchanged.
  - The r(198) refusals are left to DROPIN §4.

## Overview

**What is wrong today.**

DROPIN-REMAINING.md P0.3 reads: "Unlabelled variables get blank axis titles, legend keys named after the plot type, and blank tooltip labels. `twoway` uses the variable name. The test data helper gives every variable a label, which hides this."

Measured at HEAD in both modes, on data written exactly as Stata's exporter writes it (`{name: ""}`):
- `scatter y x` draws no axis titles, the key `scatter`, and tooltip rows `('', '')`.
- `(scatter y1 x)(scatter y2 x)` is keyed `['scatter','scatter']`.
- The served app's filter widgets are untitled.
- A malformed `variableLabels` aborts the build.

P0.4 reads: "`xtitle(, size())` or `ytitle(, color())` with no text deletes the default title."
- `ytitle(, size(large))` gives `axis_label=None` at 15px in both modes. twoway draws `Mileage (mpg)` at 157.44 against a default of 112.56.
- `ytitle(,)` draws a literal comma.
- `ztitle(, size(large))` empties the colour-key title.
- A second axis is never titled by default. twoway titles it with its layer's label.

**After this section**, every title, key, tooltip row and widget that names a variable uses twoway's measured rule, identical in both modes and unchanged by any filter move: the label when it is not `""`, otherwise the name. A label of blanks is drawn as given. A title option that carries only sub-options keeps twoway's default text and is styled by them. A typed `""` still removes the title. A comma followed by nothing, by blanks or by another comma opens an empty sub-option list. A second axis is titled by default as twoway titles it, except under by(), in the scheme's axis style.

**Why one section.** Both items rewrite `_dash_axis_labels`: P0.3 its default lines (18724, 18729), P0.4 its `_label` (18733-18746). Part B calls `_dash_axis_labels` for the axis-2 default, so it needs P0.3's rule. Two parallel worktrees would conflict on the same function (architect A1).

**Test order and commit rule (rule 7, D1).** The section runs two cycles, P0.3 then P0.4.

The P0.3 cycle:
- **03-02 to 03-04** write P0.3's fixture and failing tests.
- **03-05** runs them, with the flipped helper, against the unmodified tree and saves `$S/03-P0.3-failure.txt`. It never commits.
- **03-06 to 03-10** fix and certify.
- **03-11** closes the entry and makes the P0.3 commit, `(WP-29 P0.3)`.

The P0.4 cycle repeats this on the tree that commit leaves:
- **03-12 and 03-13** regenerate the fixture and write the failing tests, saving `$S/03-P0.4-failure.txt`.
- **03-14 to 03-18** fix and certify.
- **03-19** makes the P0.4 commit, `(WP-29 P0.4)`.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — a test-helper change touches 94 test files, and the title text of every graph changes in both renderers

**Why.** The jsonio-faithful helper changes what 94 test files feed the renderer. The fix changes the visible text of every unlabelled graph, every `histogram`/`kdensity` key and every dual-axis dashboard. These are four code paths (saved renderer, served template, mapper, filter builders) that must stay identical.

**Risk factors.**
1. Red tests hidden in helper users nobody ran (u03 A1).
2. Interim visible differences from twoway that P1.16 owns:
   - a multi-layer y title (`scatter y1 y2 x` draws `y1`; twoway draws none);
   - a range key `y1` where twoway writes `y1/y2`;
   - `lfit y2 y1` alone with y title `y2` where twoway writes `Fitted values`.
3. The served copy lists: a helper missing from them fails only when served.
4. The separator regex is shared by every textbox option (title, subtitle, note, caption, legend title, axis titles, ztitle), so a wrong split changes text everywhere.
5. Part B changes the right axis of every yaxis(2) dashboard (title, size, colour, tick style).
6. The two renderers add the second axis at different points (saved after `_dash_style_axis_titles`, served before it; WP-28 note at dash_render.py:20093-20098).
7. Regenerating `text_truth.json` could silently change the 82 existing probes.

**Mitigation.**
1. 03-05 measures the full red list and 03-09 shows the same 94 files green.
2. The interim differences are listed in the CHANGELOG and handed to S15 for P1.16. Labelled data already behave this way today.
3. Both served-name guards run after every edit (G4).
4. A unit test runs over the whole separator family, including the pins `'"a", 2 more'` and `'"a", "b"'` → -1. A linear-time test runs on 200k-comma inputs.
5. CHANGELOG lines say exactly what changes. The by() exception is measured.
6. Part B styles the axis from the scheme at creation (`SchemeParser.apply_to_axis`), never by copying the primary axis. A test asserts that `xtitle(, size(large))` does not restyle the right axis in either mode.
7. 03-12 compares every pre-existing probe's pre-existing keys before and after; the only change allowed is the new `text_records` key.

**Prototype (measured 30sep2026 in a scratch copy of HEAD with the full design of this section and the flipped helper).**
- 15 related files gave `1 failed, 2262 passed`. The one failure is the planned flip `TestTheLegendKeyRule::test_a_univariate_layer_uses_its_var_key` (`assert 'Density' == 'mpg'`).
- `test_mode_parity.py` plus `test_function_test_map.py` gave `2 failed, 3230 passed`. Both failures are `test_function_test_map.py` naming the new, still unmapped functions.
- The reviewer's 11 extra red nodes gave `11 passed`.
- Both served-name guards gave `2 passed`.

## Dependencies

- **Depends on: 01.** S01 provides:
  - the open BUGS.md entries for P0.3 and P0.4;
  - their keys in `WP29_OPEN` (test/test_tracking_documents.py);
  - the CHANGELOG markers `<!-- WP-29 P0.3 -->` and `<!-- WP-29 P0.4 -->` in the `**WP-29 (drop-in P0, 30sep2026)**` group at the end of `### Results that change`;
  - `test/test_wp29_truth.cscript`, with its `WP29_ONLY` gate and its marker line `* ==== append new blocks above this line ====`.
- **Blocks: 10.** S10 routes `ytitle(, axis(2))`-style options through `_dash_route_axis_titles` and `_dash_add_secondary_axes`, which this section changes (Part B adds `var_labels`/`scheme` parameters and the default). S10 must call the new signature.
- **Parallel batch: 1.** Merge order `S01, S09, S03, S02, S04, S06, S07, S05, S08`. S03 merges third so that the batch's full run shows any label dependence at once (architect A7).
- **Can run with:** S02, S04, S05, S06, S07, S08, S09. No other batch-1 section edits `_dash_axis_labels`, `_dash_legend_key`, `_dash_build_hover`'s fallback, the textbox parser or `_dash_add_secondary_axes`.
  - S06 (hover export) tests unlabelled `hover()` variables. Its new tests pass labels explicitly (A7), and they read names correctly once S03 lands.

## Evidence

All anchors are at HEAD `7421d3d` (dash_render.py 32,205 lines). Symbols are authoritative if lines drift.

### P0.3 — where the empty label comes from and who reads it

The exporter writes Stata's label as Stata holds it, `""` for an unlabelled variable (dash_render.py:1420-1423, `_dash_write_stata_data`; this does not change; test_string_value_export.py:326 pins it):

```python
1420    var_labels, label_names, value_labels = {}, {}, {}
1421    for v in names:
1422        try:
1423            var_labels[v] = str(data.getVarLabel(v))
```

Measured by the u03 research from real Stata (`dash_render._dash_write_stata_data` called inside Stata on generated data): `{'y': '', 'x': '', 'y1': '', 'y2': '', 'g': '', 'z': '', 'w': '   ', 'v': 'Labelled v'}`. `dash.ado` and `dash_parse.mata` never read variable labels (`grep 'var label|st_varlabel'` finds only a comment at dash.ado:4294).

Both loaders keep the dict as read:
- saved, `DashRenderer._load_data`, dash_render.py:25160:
  ```python
  self.variable_labels = stata_json.get("variableLabels", {})
  ```
- served, emitted `_load_spec_and_data`, dash_render.py:29874:
  ```python
  "    var_labels = data_json.get('variableLabels', {})",
  ```

Every consumer uses `.get(v, v)`. That fallback is dead, because the key exists with value `""`:
- `_dash_axis_labels`, dash_render.py:18724 `x_default = vl.get(var, var)` and 18729 `x_default, y_default = vl.get(xvar, xvar), vl.get(yvar, yvar)`.
- `_dash_legend_key`, dash_render.py:23599-23601 (`_DASH_FIT_TYPES`/`_DASH_CI_TYPES` return `"Fitted values"` above it):
  ```python
  23599    yvar = (plot.get("yvar", "") or plot.get("var", "")
  23600            or plot.get("yvar1", ""))
  23601    return (var_labels.get(yvar, yvar) or ptype) if yvar else ptype
  ```
- `_dash_build_hover`:
  - `_fields_for` at 23904: `_c, var_labels.get(_c, _c), ...`.
  - The fallback at 23989-24046:
    ```python
    23989        def _named(col, fallback):
    23992            return var_labels[col] if col in var_labels else fallback
    23994        _x_label = var_labels.get(xvar, xvar or "x")
    23995        _y_label = var_labels.get(y1var, y1var or "y")
    24005            _bin_label = var_labels.get(_bin_var, _bin_var or "value")
    24027                     _cell(var_labels.get(y1var, y1var or "y1"), "y1", data),
    ```
    `_point_or_line` (24012-24021) and `_band` (24039-24047) call `_named` on the drawn columns.
- `GlyphMapper._apply_colorvar`, 6981: `self.variable_labels.get(varname, "") or varname`. This is already correct; it moves to the shared helper so that there is one rule.
- Saved filter widgets, `DashRenderer._build_filter_widgets`, 27577-27579: `(fc.get("label") or "").strip() or self.variable_labels.get(fvar, "").strip() or fvar`. This is correct, and it is the documented chain.
- Served filter widgets, emitted at 30953-30954: `_dash_filter_title(fspec.get('label', ''), var_labels.get(fvar, fvar), ftype)`. `""` wins, so the widget is untitled.

The test helper hides all of this. test/conftest.py:425-461, `make_data_json`, line 451:

```python
451        "variableLabels": {v: v for v in varnames},
```

`grep -l make_data_json test/test_*.py | wc -l` gives 94 test files. The 96 matches of `grep -l make_data_json test/*.py` also include `conftest.py` and `filter_truth_check.py`.

**Measured at HEAD, both modes** (scratch probe `both.py`; data `{name: ""}` for x, y, y1, y2, z, g and `w` labelled `"   "`; `DashRenderer.render()` against `ServerAppBuilder.build` plus `make_document`):

```
sc    saved  {'x': [None], 'y': [None], 'hover': [['', '']], 'legend': [['scatter']]}       (served identical)
two   saved  {'x': [None], 'y': [None], 'hover': [['', ''], ['', '']], 'legend': [['scatter', 'scatter']]}
fit   saved  {'legend': [['scatter', 'Fitted values']], 'hover': [['', '']]}
hist  saved  {'x': [None], 'y': ['Density'], 'hover': [['', 'Count']], 'legend': [['histogram']]}
rcap  saved  {'hover': [['', '', '']], 'legend': [['rcap']]}
blank saved  {'y': ['   '], 'hover': [['', '   ']], 'legend': [['   ']]}
```

Filter widgets at HEAD (`filters` x range, g dropdown, w range):

```
saved  [('RangeSlider', 'w'), ('RangeSlider', 'x'), ('Select', 'g')]
served [('RangeSlider', ''), ('RangeSlider', '   '), ('Select', '')]
```

Malformed `variableLabels` at HEAD:

| `variableLabels` | saved | served |
|---|---|---|
| `['a']` | `RuntimeError dash_render: failed to build figure 'sc': 'list' object has no attribute 'get'` | `AttributeError` |
| `{'y': 5}` and `{'y': {'a': 1}}` | `RuntimeError ... failed to validate FigureOptions(...).y_axis_label` | `ValueError` |
| `{'y': None}` | `RuntimeError ... HoverTool(...).tooltips` | `ValueError` |

The tooltip fallback names unrelated variables (u03 A3). At HEAD, on data that also holds unlabelled `x` and `y`:
- `kdensity z` gives hover `[('', '@{x}{0.000}'), ('', '@{y}{0.00000}')]`;
- `lfit y2 y1` gives `[('', '@{x}{0.00}'), ('', '@{y}{0.00}')]`.

The computed source's generic `x`/`y` columns are looked up as the dataset's unrelated `x`/`y`.

After a filter move nothing changes:
- **Served.** The u03 research fired the `RangeSlider(x)` callback (1 fired); titles, keys and tooltip labels were unchanged.
- **Saved.** No page script writes a title. A scan of every module-level JavaScript string of `dash_render` for `.axis_label =`, `.tooltips =`, `.title =`, `.label =` found none. The only `.text =` is the KPI card in `_FILTER_JS`.

### P0.3 — twoway truth (Stata 19, s2color, 12 generated observations, `graph export` to SVG; `YT` = a rotate(-90) text)

```
A  scatter y x                      YT 'y'  'x'
B  scatter y1 y2 x                  'x'  keys 'y1' 'y2'  (no y title)
C  (scatter y1 x)(line y2 x)        'x'  keys 'y1' 'y2'
D  ... y1 labelled "First"          keys 'First' 'y2'
E  w labelled "   "; scatter w x    YT '\xa0\xa0\xa0'   (blank, NOT the name)
G  histogram x                      YT 'Density'  'x'
H  twoway kdensity x                YT 'kdensity x'  'x'
I  scatter y x, by(g)               YT 'y'  'x'  'Graphs by g'
J  scatter y x, colorvar(z)         key title YT 'z'
K  (scatter y x)(lfit y x)          keys 'y' 'Fitted values'  (no y title)
L  rcap y1 y2 x                     YT 'y1/y2'
M  line y t (%td)                   't'
P  x labelled "Horizontal"          'y'  'Horizontal'
W  scatter y x, legend(on)          key 'y'
HK (histogram x)(kdensity x)        keys 'Density' 'kdensity x'
KD2 (kdensity x)(kdensity y)        keys 'kdensity x' 'kdensity y'
KDLAB same, x/y labelled            keys 'kdensity x' 'kdensity y'   (the NAME, not the label)
HPLAB (histogram x, percent)(kdensity x), labelled   keys 'Percent' 'kdensity x'
BYL g labelled "Group"; by(g)       'Graphs by Group'
AX2 (scatter y x)(scatter y1 x, yaxis(2))   YT 'y' left, YT 'y1' on axis 2
```

The rule: twoway writes a variable's label when the label is non-empty, and its name when the label is exactly `""`. A label of blanks is not empty and is drawn as given. Stata's label state: `: var label y` of an unlabelled variable is `""`; `label variable y1 "   "` keeps length 3; `label variable y1 ""` gives `""` again.

### P0.4 — the defect

`_dash_axis_labels._label`, dash_render.py:18733-18746:

```python
18733    def _label(opt, default):
18734        raw = go.get(opt, "")
18735        text, opts = _dash_textbox(raw, opt, seen, key)
18739        given = bool(str(raw or "").strip())
18742        if "suffix" in opts:
18743            return default + ("\n" + text if text else "")
18744        if "prefix" in opts:
18745            return (text + "\n" if text else "") + default
18746        return text if given else default
```

`given` is computed over the whole raw value, sub-options included. So `', size(large)'` counts as "given with empty text" and removes the title.

The separator regex at 2751 does not split at a trailing comma: `_TEXTBOX_SUBOPT_RE = re.compile(r",\s*(?=[A-Za-z_])")`. Measured at HEAD:

```
'A,'           split -1  ('A,', {})
'A,,'          split -1  ('A,,', {})
','            split -1  (',', {})
'"A",'         split -1  ('A\n,', {})
', size(large)' split 0  ('', {'size': 'large'})
'"a", 2 more'  split -1     '"a", "b"' split -1      'A, size(large),' split 1
```

Other sites:
- **Colour key.** `_dash_apply_z_options`, 22818-22823:
  ```python
  if ztitle_raw:
      text, topts = _dash_textbox(ztitle_raw, "ztitle", seen, key)
      key_obj.title = text
  ```
  `', size(large)'` empties it.
- **Second axis.** `_dash_add_secondary_axes`, 20076-20128, has no default. At 20117-20120:
  ```python
  text, opts = _dash_textbox(graph_opts.get(f"{n}title2", ""), f"{n}title2", seen, key)
  ax = (LogAxis if is_log else LinearAxis)(**{kw: name}, axis_label=text)
  ```
  It is added after `SchemeParser.apply_to_figure` in both modes (saved 26037 then 26096; served 30411 then 30414), so the axis keeps Bokeh's 13px #444444.
- **Unhonoured sub-options.** `_dash_textbox`, 22571-22600, names them. Its loop at 22585-22597 would name a bare `,` token once the regex splits at commas (u04 A2).

Spec storage is already right (u04 research, real Stata): `ytitle(, size(large))` is stored as `', size(large)'`, `ytitle(,)` as `','`, `ytitle("A") ytitle(, size(large))` as `'"A", size(large)'`, and the dual `ytitle(, axis(2) size(large))` as `ytitle2 ', size(large)'` (`_dash_route_axis2`, dash_parse.mata:4893). `dash.ado` and Mata need no change.

**Measured at HEAD, both modes** (scratch probes; data unlabelled):

```
ysize  ytitle ', size(large)'      y [None] at '15px'          (twoway: default text at large)
dual   (scatter)(line, yaxis(2))   right axis ('', '13px', '#444444', ticks '11px')   (twoway: 'Price', scheme style)
```

### P0.4 — twoway truth (StataNow 19.5, born 12 Aug 2026, scheme stcolor; default title 112.56, `large` 157.44; text, size, fill, rotate from `scripts/svg_truth.svg_texts`)

```
a0  scatter mpg weight                          'Mileage (mpg)' 112.56 rot-90; 'Weight (lbs.)' 112.56
a1  ytitle(, size(large))                       'Mileage (mpg)' 157.44 rot-90
a2  xtitle(, color(red))                        'Weight (lbs.)' 112.56 #ff0000
a6  ytitle(,)                                   'Mileage (mpg)' 112.56   (default kept)
a11 ytitle("") ytitle(, size(large))            no y title
a13 ytitle("A") ytitle(, size(large))           'A' 157.44     a14 reversed order: 'A' 157.44
a15 ytitle(, orientation(horizontal))           'Mileage (mpg)' drawn horizontal
b0  (scatter mpg weight)(line price weight, yaxis(2))   'Price' 112.56 rot-90 (axis 2)
b1  ... ytitle(, axis(2) size(large))           'Price' 157.44 rot-90; legend 'Price' 112.56
b4  scatter mpg weight, yaxis(2) ytitle(, axis(2) size(large))   'Mileage (mpg)' 157.44
b6  ... ytitle(, axis(2))                       'Price' 112.56 rot-90
c1  histogram mpg, ytitle(, size(large))        'Density' 157.44    c3 percent: 'Percent' 157.44
d1  kdensity mpg, ytitle(, size(large))         'kdensity mpg' 157.44
e1  title(, size(large))                        no title drawn (no default to keep)
e7  by(foreign) ytitle(, size(large))           'Mileage (mpg)' 157.44
f1  colorvar(price) ztitle(, size(large))       key 'Price' 157.44   f2 color(red): 'Price' #ff0000   f3 ztitle(""): none
g1  z = mpg unlabelled; ytitle(, size(large))   'z' 157.44
a25 (scatter mpg weight)(scatter price weight), ytitle(, size(large))   no y title (P1.16)
r3  ytitle(A,) ytitle(, size(large))            'A' 157.44     r4 ytitle(,) ytitle(, size(large)): default 157.44
r5  ytitle("", suffix)                          'Mileage (mpg)' (default kept)
r6  ytitle(A,,)  'A'    r10 ytitle(A, ,)  'A'    r18 ytitle(A, size(large),)  'A' 157.44
r7  (scatter)(line price weight, yaxis(2)), by(foreign)   axis-2 ticks drawn, NO rotated 'Price'
r8  (scatter mpg weight)(histogram weight, yaxis(2))      axis 2 'Density' rot-90
r12 ytitle("", axis(2))  no axis-2 title    r13 ytitle(, axis(2) suffix)  'Price' rot-90
refused r(198): ytitle(, bogus(1)); ytitle(, colour(red)); title(a, 1); yaxis(2) ytitle(, size(large))
```

Stata's own code agrees:
- `/Applications/StataNow/ado/base/_/_gs_parse_and_log_axtitle.ado:14` is `_parse comma mtext 0 : 0`. Lines 25-27 replace the text only `if "mtext" != ""`, and lines 30-31 apply the sub-options separately.
- `_fr_title_parse_and_log.ado:16-20` has the same rule for `title()`.
- `axis_title_options.sthlp:218-228`: only `title("")` suppresses a title.

### Prototype of the fix (scratch copy of HEAD, this section's design, flipped helper)

The widened regex:

```
'A,' 1 ('A', {})     'A,,' 1 ('A', {})     'A, ,' 1 ('A', {})     ',,' 0 ('', {})     ',' 0 ('', {})
'"A",' 3 ('A', {})   '"a", 2 more' -1      'a, 1' -1             '"a", "b"' -1        'A, size(large),' 1
'a'+', '*200000 split+parse 0.205 s        ','*200000 0.021 s
```

Both modes after the fix, identical:

```
sc    {'x': ['x'], 'y': ['y'], 'hover': [['x', 'y']], 'legend': [['y']]}
two   {'x': ['x'], 'y': ['y1'], 'hover': [['x', 'y1'], ['x', 'y2']], 'legend': [['y1', 'y2']]}
fit   {'legend': [['y', 'Fitted values']]}
hist  {'x': ['x'], 'y': ['Density'], 'hover': [['x', 'Count']], 'legend': [['Density']]}
hk    legend ['Density', 'kdensity x']          kd: hover ('x','y'); lf (lfit y2 y1): hover ('y1','y2')
blank {'y': ['   '], 'legend': [['   ']]}
ysize {'y': ['y'], 'ysz': ['15px']}
dual  right ('y2', '10pt', '#000000', ticks '10pt')    dual_size right ('y2', '15px', ...)
dual_by right ('', '10pt', ...) on both panels       x2 top ('w', ...)      hist2 right ('Density', ...)
widgets  saved and served [('RangeSlider', 'w'), ('RangeSlider', 'x'), ('Select', 'g')]
malformed ['a'] / {'y': 5} / {'y': {'a': 1}} / {'y': None}: both modes draw y title 'y'
```

### Blast radius (R8; GitNexus has no index for this repository)

`mcp__gitnexus__list_repos` on 30sep2026 listed only TYME and PhotoShootPlannerPro. 03-01 runs `npx gitnexus analyze` first. Callers found by grep:

| Symbol | Callers (dash_render.py) |
|---|---|
| `_dash_axis_labels` | 25947 (saved), 30347 (served); Part B adds `_dash_add_secondary_axes` |
| `_dash_legend_key` | 23646 (`_dash_legend_keys`) |
| `_dash_legend_keys` | 18516, 23661 |
| `_dash_build_hover` | 26349 (saved), 30679 (served) |
| `_dash_filter_title` | 16630, 16703, 16706, 16765, 16768, 30953 |
| `_textbox_split_point` | 1777, 2952, 22582 |
| `_parse_textbox_opt` | 1774, 22580, 22638, 25974, 30353 |
| `_dash_textbox` | 18735, 20117, 22611, 22690, 22820 |
| `_dash_apply_z_options` | 7199, 7236 |
| `_dash_add_secondary_axes` | 26096 (saved), 30414 (served template) |
| `SchemeParser.apply_to_figure` | 26037, 30411 |
| `make_data_json` | 94 test files |

Expected HIGH (index R8): `_dash_axis_labels`, `make_data_json`.

### Tests that pin today's behaviour (flip, never delete)

- `test/test_server_layer_defects.py::TestTheLegendKeyRule::test_a_univariate_layer_uses_its_var_key` (:1021-1022) asserts that `histogram` is keyed `'mpg'`. Flip it to `'Density'` and add `kdensity` → `'kdensity mpg'` (A2). It is the only failure the prototype showed.
- These keep their text and are red-first under the flipped helper, then green: `test_server_legend.py::TestAServedFigureHasALegend::test_the_labels_name_the_series` (got `['scatter','Fitted values']`), `::TestTheLegendOptionsNowReachIt::test_lastlabel_is_applied_not_named` (got `['scatter','L']`), and `test_filter_widget_parity.py::TestTheLabelReachesTheServedWidget::test_without_a_label_it_still_falls_back_to_the_name`.
- These 11 nodes are red under the flipped helper at HEAD (u03 review: `11 failed, 2320 passed`) and green with the fix (`11 passed`, measured):
  - `test_adversarial_matrix.py::TestALayoutThatCannotBeReadIsReported::test_a_zero_in_a_grid_is_one_in_both_modes` ×2;
  - `::TestARepeatedLayoutNameIsPlacedOnce::test_the_saved_page_embeds_a_repeated_item_once`;
  - `::TestTextPlotOptionBounds::test_a_long_legend_label_is_escaped_once`;
  - `::TestTextPlotOptionBounds::test_a_legend_order_of_a_hundred_thousand_keys_is_bounded`;
  - `test_display_format_sites.py::TestTooltips::test_fields_carry_custom_and_a_formatter_with_the_format` ×2;
  - `test_date_range.py::TestTheSavedPageHoldsThePlaceholder::test_a_hover_variable_carries_every_date` ×3;
  - `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline`.
- **Kept as pins (green at HEAD and after):**
  - `test_textbox_grammar.py::TestEmptyTitles` (`'"", size(large)'` removes; `ytitle2('""')` removes);
  - `::TestPrefixSuffix`;
  - `test_textbox_multiline.py::TestTextboxSplitPoint::test_a_comma_before_any_word_splits` (`'"a", 2 more'` and `'"a", "b"'` → -1);
  - `test_colorvar_forms.py::TestZOptions::test_ztitle_titles_the_colour_bar`;
  - `test_server_layer_defects.py::TestTheLegendKeyRule::test_a_range_layer_uses_its_first_boundary` (`'lo'`) and `::test_a_layer_with_no_variable_is_keyed_by_its_type` (`'pci'`). These two are P1.16 territory.
  - `::TestTheHoverBuilder::test_a_density_curve_gets_the_generic_tooltip` (`['x','y']`).
- Per-file helpers that write `{v: v}` (test_dual_axis.py:36, test_filters.py, test_graph_options.py, test_glyphs.py, test_dates.py) model labelled data and stay.
- `dash.sthlp:2585-2586` says of `ytitle2()` "an absent option draws no title either". No test quotes it (grep); 03-18 rewrites it.

## User stories

- **US-03.1** As a twoway user with unlabelled data, I want `dash scatter y x` to title its axes `y` and `x`, key its layers `y1` and `y2`, and name its tooltip rows `x` and `y`, as twoway names them, so that a dashboard of raw data is readable without labelling every variable first.
- **US-03.2** As a twoway user, I want a variable labelled with blanks drawn blank, and a mixed graph to use label or name per variable, exactly as twoway does.
- **US-03.3** As a twoway user, I want `(histogram x)(kdensity x)` keyed `Density` and `kdensity x`, not twice by the variable, so that the two layers can be told apart as in Stata.
- **US-03.4** As a dashboard reader of a served app, I want every filter widget titled by its variable's label or name, as the saved page titles it.
- **US-03.5** As a dashboard publisher, I want a data file with a malformed `variableLabels` to draw names instead of aborting the build.
- **US-03.6** As a twoway user, I want `ytitle(, size(large))`, `xtitle(, color(red))` and `ztitle(, size(large))` to restyle the default title rather than delete it, in both modes and after any filter move.
- **US-03.7** As a twoway user, I want `ytitle(A,)`, `ytitle(,)` and `ytitle(A,,)` read as twoway reads them: `A`, the default, and `A`.
- **US-03.8** As a twoway user with a second axis, I want it titled by default with its layer's label in the scheme's style, and not titled under `by()`, as twoway draws it.
- **US-03.9** As the maintainer, I want the test data helper to write labels as Stata's exporter writes them, so that no defect hides behind fabricated labels again.

## Business requirements

- **BR-03.1** Wherever a title, legend key, tooltip row, colour-key title or axis-2 title names a variable, it shows the variable's label when that label is not `""`, and the name otherwise. A label of blanks is shown as given.
- **BR-03.2** A filter widget is titled by `label()`, else the variable's label, else the name. A blank text counts as absent. The rule is the same in both modes.
- **BR-03.3** A `histogram` layer is keyed by its y-scale word (`Density`, `Percent`, `Frequency`, `Fraction`). A `kdensity` layer is keyed `kdensity <name>`, using the name even when the variable is labelled.
- **BR-03.4** A computed layer's tooltip never names an unrelated dataset variable.
- **BR-03.5** Titles, keys, tooltip rows and widget titles are identical in the saved page and the served app, at first paint and after every filter move.
- **BR-03.6** A data file whose `variableLabels` is not a mapping, or holds non-text labels, builds and draws names.
- **BR-03.7** A title option whose text part is blank keeps the default title (the label or name, `Density`/`Percent`/`Frequency`/`Fraction`, `kdensity <name>`, the colour variable's label, the axis-2 default) and applies its `size()` and `color()`. `title()`, `subtitle()`, `note()` and `caption()` have no default and draw nothing.
- **BR-03.8** A typed `""` removes the title, with or without sub-options and in any merge order. `""` with `suffix` or `prefix` keeps the default.
- **BR-03.9** The first comma outside strings and parentheses that is followed, after blanks, by a name, another comma or the end opens the sub-options. Empty slots are ignored silently. A comma followed by a digit or a quote stays text.
- **BR-03.10** A second axis is titled by default as twoway titles it: its first layer's label or name, or the univariate title. It is drawn in the scheme's axis style, and `ytitle2()`/`ytitle(, axis(2))` sub-options style it. Under `by()` it has no default title.
- **BR-03.11** Every changed text is listed in CHANGELOG "Results that change" with the command, the old value and the new.

## Technical requirements

### P0.3

- **TR-03.1 `_dash_var_label(var_labels, name, default="")`** is a new module function, placed directly above `_dash_attach_labels` (dash_render.py:22449).
  - Return `default` when `name is None or name == ""`.
  - Return `str(name)` when `name` is not a `str` (A5).
  - Otherwise let `lab = (var_labels if isinstance(var_labels, dict) else {}).get(name)`, and return `lab` when `isinstance(lab, str) and lab != ""`, else `name`.
  - Never `.strip()`.
  - The docstring cites twoway's rule and E.svg.
- **TR-03.2 `_dash_clean_var_labels(raw)`** is new, placed beside TR-03.1. It returns `{}` when `raw` is not a `dict`. Otherwise it returns `{k: (v if isinstance(v, str) and v != "" else k) for k, v in raw.items() if isinstance(k, str) and k}`.
  - Called by the saved loader at 25160: `self.variable_labels = _dash_clean_var_labels(stata_json.get("variableLabels", {}))`.
  - Called by the emitted served loader at 29874: `"    var_labels = _dash_clean_var_labels(data_json.get('variableLabels', {}))",`.
  - Membership is kept: every variable keeps its key, so `_named()` still tells dataset variables from computed columns.
  - The qualifier-column pop at 25200 (`self.variable_labels.pop(_qc, None)`) and the served twin at 29920 work unchanged on the cleaned dict.
- **TR-03.3 `_dash_filter_base_title(label, var_labels, name)`** is new, placed beside TR-03.1. Do NOT name it `_dash_filter_label`: that is the `filter()` option parser at 23145. It returns `str(label or "").strip() or str((var_labels if isinstance(var_labels, dict) else {}).get(name, "") or "").strip() or str(name)`.
  - Saved 27577-27579 becomes `flabel = _dash_filter_base_title(fc.get("label"), self.variable_labels, fvar)`.
  - Served 30953-30954 becomes `_dash_filter_title(_dash_filter_base_title(fspec.get('label', ''), var_labels, fvar), fvar, ftype)`.
  - `_dash_filter_title` itself is unchanged: it still adds `" ≥"` to a slider and passes slider titles through `_dash_inert_tex`.
  - The dropdown builder's fallback `FilterBuilder._safe(varname)` (16630) becomes unreachable and is left as it is (u03 review: `_safe` html-escapes, and a Select title is a text node).
- **TR-03.4 Consumers** read through `_dash_var_label`:
  - `_dash_axis_labels`: 18724 becomes `x_default = _dash_var_label(vl, var)`; 18729 becomes `x_default = _dash_var_label(vl, xvar)` and `y_default = _dash_var_label(vl, yvar)`.
  - `GlyphMapper._apply_colorvar` 6981 becomes `var_display = _dash_var_label(self.variable_labels, varname)`.
  - `_dash_build_hover`:
    - 23904: pass `_dash_var_label(var_labels, _c)` as the row label.
    - 23994-23995: `_x_label = _dash_var_label(var_labels, xvar, "x")` and `_y_label = _dash_var_label(var_labels, y1var, "y")`.
    - 24005: `_bin_label = _dash_var_label(var_labels, _bin_var, "value")`.
    - 24027-24028: `_dash_var_label(var_labels, y1var, "y1")` and `(..., y2var, "y2")`.
    - `_named` (23989-23992) becomes (A3):
      ```python
      if col in var_labels and (col not in ("x", "y", "y1", "y2")
                                or col in (xvar, y1var, y2var)):
          return _dash_var_label(var_labels, col)
      return fallback
      ```
- **TR-03.5 `_dash_legend_key`** (23579-23601):
  - After the fit/ci branch, `histogram` returns `_DASH_HIST_YTITLES[_dash_histogram_ymode(plot.get("options"))]`.
  - `kdensity` returns `"kdensity %s" % v` where `v = plot.get("var", "") or plot.get("yvar", "")`, and the type name when `v` is empty.
  - Every other type returns `_dash_var_label(var_labels, yvar) if yvar else ptype`.
  - The docstring cites HK.svg, KD2.svg and KDLAB.svg.
  - `_DASH_HIST_YTITLES` and `_dash_histogram_ymode` are already in the served app (`_dash_axis_labels` uses them).
- **TR-03.6 Both renderers.** The saved JavaScript is unchanged: no script writes titles.
  - **Served copy list** (functions tuple, R2): `"_dash_var_label", "_dash_clean_var_labels",` after `"_dash_legend_key", "_dash_legend_entries",` (28619), and `"_dash_filter_base_title",` after `"_dash_filter_title",` (28716).
  - `GlyphMapper` travels with its class (28840).
  - `test/function_test_map.py` gains `_dash_var_label`, `_dash_clean_var_labels` and `_dash_filter_base_title`, in alphabetical place.
- **TR-03.7 `make_data_json(df, value_labels=None, value_label_names=None, variable_labels=None)`** (test/conftest.py:425). It writes `"variableLabels": {v: (variable_labels or {}).get(v, "") for v in varnames}`. The docstring says this is what `_dash_write_stata_data` writes for an unlabelled variable.
- **TR-03.8 Security (rule 1).** No new sink:
  - Axis titles and legend keys are canvas text.
  - Tooltip row labels are BokehJS text nodes.
  - Select titles are text nodes.
  - Slider titles still pass `_dash_inert_tex`.
  - A name replaces a label in sinks that already carry arbitrary label text.
  - Tooltip FIELDS still pass `_dash_is_stata_name` (23887-23895).
  - The cleaner and the total helper remove four abort paths (non-dict mapping, int, dict and null labels) and add no exception path.

### P0.4

- **TR-03.9 Separator.** dash_render.py:2751 becomes `_TEXTBOX_SUBOPT_RE = re.compile(r",\s*(?=[A-Za-z_,]|\Z)")`. The comment above it gains A4's sentence and the measurements r6, r10, r18.
  - `_textbox_split_point` (2790-2831) and `_parse_textbox_opt` (2921-2993) are unchanged in code. `m.end()` stays valid because the regex matches at every split.
  - The constant is already in the served constants tuple (28362).
- **TR-03.10 `_textbox_has_text(raw) -> bool`** is new, directly after `_parse_textbox_opt`:
  ```python
  s = str(raw or "")
  cut = _textbox_split_point(s)
  return bool((s[:cut] if cut >= 0 else s).strip())
  ```
  Typed `""` gives True; `', size(large)'`, `','` and `',,'` give False. It goes in the served functions tuple after `"_textbox_split_point",` (28535).
- **TR-03.11 `_dash_textbox`** (22571-22600). The bad-token loop starts with `if not t.strip(", "): continue` (A2).
- **TR-03.12 `_dash_textbox_or_default(raw, option, default, seen=None, key="") -> (text, opts)`** is new, directly after `_dash_textbox`:
  - It calls `text, opts = _dash_textbox(raw, option, seen, key)`.
  - With `suffix`: `"\n".join(p for p in (default, text) if p)`.
  - With `prefix`: `"\n".join(p for p in (text, default) if p)`.
  - Otherwise: `text if _textbox_has_text(raw) else default`.
  - It goes in the served functions tuple after `"_dash_textbox",` (28799).
- **TR-03.13 `_dash_axis_labels._label`** keeps its name and nesting (the function_test_map key `_dash_axis_labels.<locals>._label` stays valid). Its body becomes `return _dash_textbox_or_default(go.get(opt, ""), opt, default, seen, key)[0]`. `_dash_style_axis_titles` (22627) is unchanged and still applies `size()`/`color()` to the primary axes.
- **TR-03.14 `_dash_apply_z_options`** (22818-22829): `text, topts = _dash_textbox_or_default(ztitle_raw, "ztitle", key_obj.title or "", seen, key); key_obj.title = text`. The size and colour lines are unchanged. It works for the ColorBar and for the discrete Legend.
- **TR-03.15 Part B.**
  - **`SchemeParser.apply_to_axis(self, axis)`** is a new method holding the six assignments of `apply_to_figure`'s axis loop (5474-5481). The loop becomes `for axis in ...: self.apply_to_axis(axis)`. It travels with the class.
  - **`_dash_add_secondary_axes(fig, plots, graph_opts, frame, seen=None, key="", var_labels=None, scheme=None)`**, for each wanted axis:
    1. `dflt = ""` if `str(graph_opts.get("by", "") or "").strip()`.
    2. Otherwise `dflt = _dash_axis_labels([p for p in plots if str(p.get("options", {}).get(axis_key, "1")).strip() == "2"], {}, var_labels)[0 if n == "x" else 1]`.
    3. `text, opts = _dash_textbox_or_default(graph_opts.get(f"{n}title2", ""), f"{n}title2", dflt, seen, key)`.
    4. After the axis is built, `if scheme is not None: scheme.apply_to_axis(ax)`.
    5. Then the existing `size()`/`color()` lines.
    6. Never copy from the primary axis (renderer order).
  - **Saved caller** 26096-26098 passes `self.variable_labels, self.scheme`. This is the per-graph scheme the saved renderer swaps in at 25906-25916.
  - **Served template** 30414-30415 becomes `"        _dash_add_secondary_axes(fig, plots, go, g_df,"`, `"                                 _reported_subopts, gname,"`, `"                                 var_labels, _DASH_SCHEME)"`.
  - `test/function_test_map.py` gains `SchemeParser.apply_to_axis`, `_textbox_has_text` and `_dash_textbox_or_default`.
- **TR-03.16 Security (rule 1).**
  - The regex is linear (lookahead of one character). 200k-comma inputs run in under 2 s; measured 0.02-0.21 s.
  - Empty slots no longer produce an echo as long as the input.
  - There is no new sink: axis labels and the ColorBar title are canvas text, and the Legend title is a DOM text node, raw as today. The default text is the label already embedded in the page.

## Boundaries

- **Do not change:**
  - `_dash_write_stata_data` (jsonio layout, pinned by test_string_value_export.py:326, :385);
  - `dash.ado`, `dash_parse.mata` (`_dash_rep_merge` 5032-5060 and `_dash_route_axis2` 4893 are already twoway's);
  - `_dash_route_axis_titles` (1747-1802) and `_dash_lone_second_axes` (1805-1871) — S10 owns axis(#) routing;
  - `_dash_figure_title`, `_dash_text_annotations`, `_dash_style_axis_titles`;
  - any saved-page JavaScript.
- **P1.16 is not done here**, beyond the univariate keys of TR-03.5. The following stay as they are:
  - no y title when layers differ;
  - `y1/y2` for range and pc types;
  - per-type fit keys and titles (`lowess y x`, lpoly, mband);
  - the scatteri/pci/pc keys (`'pci'`, `'lo'` pins stay).
- **P1.15 is not done here.** Out of scope: repeated by() axes, the "Graphs by" note, and explicit axis-2 titles under by().
- **The refusals twoway makes with r(198) stay out of scope** (DROPIN §4 refuse-vs-note): `ytitle(, bogus(1))`, `colour()`, `title(a, 1)`, prefix with suffix, and a lone-axis `ytitle(, size(large))`.
- **`ytitle(, size(bogus))`** (twoway 123.69 by an unmeasured rule) keeps its current note.
- **Size units are P1.12.** dash's `large` stays 15px; tests assert dash's `_textbox_size` value, never Stata's ratio.
- **Tracking documents stay with S15 (architect A5).** Do not edit `ROADMAP.md`, `GAPS2.md`, `REMAINING.md`, `TWOWAY_COVERAGE_AUDIT.md`, `DROPIN-REMAINING.md` or `AGENTS.md`. Their text is in Notes for the closeout.
- **No other script is edited.** No new `.cscript` file; no edit to `test/run_all_cscripts.do`, `test/test_cscript_hygiene.py` or `test/test_gaps2_truth.cscript` (R1).

## Stata truth

Every run goes through `scripts/stata_slot.sh` with `dash_nobrowser=1` in the environment (CLAUDE.md rule 10). It is never the GUI and never a bare `stata-mp`. Let `S=<scratch>/s03` (created by 03-01) and `WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s03`.

**New fixture `test/fixtures/unlabelled_truth.json`, written by the new `scripts/extract_unlabelled_truth.do` (03-02).**

The script's frame and the steps of each probe:
- **Frame.** It copies `scripts/extract_text_truth.do`'s frame:
  - header;
  - `global ZU_REPO` (pointed at `$WT` while running, restored to the main checkout path before committing, as extract_text_truth.do:61-65 says);
  - the D12 provenance stamp copied from extract_text_truth.do:79-96 (`shell git -C ... rev-parse HEAD` into a tempfile, read back, asserted 40 hex);
  - the `cert_svg.do` load (:97-102);
  - `set scheme s2color` (the scheme the evidence was measured under; recorded as `scheme_in_force`).
- **Data.** Each probe regenerates the data with a program `_zu_data`: `clear; set obs 12; gen double y = _n + 0.5; gen double y1 = _n; gen double y2 = _n + 3; gen double x = _n*2; gen double z = mod(_n,4); gen g = mod(_n,2); gen double w = _n*1.5; gen t = mdy(1,1,2000)+_n; format t %td`. The values are deterministic, so pytest mirrors them exactly.
- **Registration.** `zu id setup command option control`. `setup` is one Stata command run after `_zu_data` through `` `macval(setup)' `` (empty, or `label variable y1 "First"`). The one probe that needs two labels uses the script's own program `_zu_label_xy` (`label variable x "Horizontal"` then `label variable y "Vertical"`), so no setup string has to be split. `option` follows extract_text_truth.do's `_zt_has_top_comma` rule. `control` names the legend(off) twin or is empty.
- **Per probe:**
  - Run `command[, option] name(zqu, replace)` and `graph export` to `$ZU_WORK/<id>.svg`.
  - Write a line `P|id|rc|rcx|svg|control|shown|setup`.
  - For each of the 8 variables, write a line `L|id|var|<: variable label var>`.
- **The trailing python block** (no backtick; never calls Stata) records, per probe:
  - `command`, `setup`, `rc`, `labels` (`{var: label}`);
  - `texts` (`[[text, size, fill, rotate, x, y], ...]` of every `<text>` whose `svg_truth.label_value(text) is None`, in document order);
  - `rotated` (`[[text, x], ...]` of the rotate -90 entries, sorted by x);
  - `flat` (the non-rotated texts of `texts`, in order);
  - for a probe with a control, `keys_in_drawn_order`: the probe's entries minus the control's by multiset, sorted by `(y, x)`, as extract_text_truth.do:371-379 does.
- **`_meta`**: `stata_version`, `born_date`, `dash_commit`, `extracted`, `scheme_in_force`, `method`.

Probes. These have a `<id>__off` twin (same setup and command, option `legend(off)`, no control), and name it as their control: ul_multi_y, ul_two_layers, ul_mixed, ul_blank_key, ul_fit, ul_hist_kd, ul_histpct_kd, ul_histfreq_kd, ul_histfrac_kd, ul_kd2, ul_kd_labelled, ul_legend_on and ul_range_key. For a probe whose own option is not empty, the twin's option replaces it.

| id | setup | command | twoway (measured) |
|---|---|---|---|
| ul_scatter | — | `twoway scatter y x` | rotated `y`, flat `x` |
| ul_multi_y | — | `twoway scatter y1 y2 x` | keys y1 y2; no rotated (P1.16, recorded only) |
| ul_two_layers | — | `twoway (scatter y1 x) (scatter y2 x)` | keys y1 y2 |
| ul_mixed | `label variable y1 "First"` | same as ul_two_layers | keys First y2 |
| ul_blank_title | `label variable w "   "` | `twoway scatter w x` | rotated `   ` (NBSP normalised) |
| ul_blank_key | `label variable w "   "` | `twoway (scatter w x) (scatter y2 x)` | keys `   ` y2 |
| ul_fit | — | `twoway (scatter y x) (lfit y x)` | keys y, Fitted values |
| ul_hist | — | `twoway histogram x` | rotated Density, flat x |
| ul_kdensity | — | `twoway kdensity x` | rotated kdensity x |
| ul_hist_kd | — | `twoway (histogram x) (kdensity x)` | keys Density, kdensity x |
| ul_histpct_kd | — | `twoway (histogram x, percent) (kdensity x)` | keys Percent, kdensity x |
| ul_histfreq_kd | — | `twoway (histogram x, frequency) (kdensity x)` | to be measured |
| ul_histfrac_kd | — | `twoway (histogram x, fraction) (kdensity x)` | to be measured |
| ul_kd2 | — | `twoway (kdensity x) (kdensity y)` | keys kdensity x, kdensity y |
| ul_kd_labelled | `_zu_label_xy` | same as ul_kd2 | keys kdensity x, kdensity y |
| ul_by | — | `twoway scatter y x` + option `by(g)` | y, x, `Graphs by g` |
| ul_by_labelled | `label variable g "Group"` | same as ul_by | `Graphs by Group` (for P1.15) |
| ul_colorvar | — | `twoway scatter y x` + `colorvar(z)` | rotated y and z |
| ul_legend_on | — | `twoway scatter y x` + `legend(on)` | key y |
| ul_xlabelled | `label variable x "Horizontal"` | `twoway scatter y x` | rotated y, flat Horizontal |
| ul_date | — | `twoway line y t` | flat t |
| ul_axis2 | — | `twoway (scatter y x) (scatter y1 x, yaxis(2))` | rotated y, y1 |
| ul_ytitle_size | — | `twoway scatter y x` + `ytitle(, size(large))` | rotated y, larger than ul_scatter's (g1) |
| ul_rcap | — | `twoway rcap y1 y2 x` | rotated y1/y2 (P1.16, recorded only) |
| ul_range_key | — | `twoway (rarea y1 y2 x) (scatter y x)` | keys y1/y2, y (P1.16, recorded only) |

The run: `mkdir -p "$S" && dash_nobrowser=1 scripts/stata_slot.sh "$S" "$WT/scripts/extract_unlabelled_truth.do"`. The log is `$S/extract_unlabelled_truth.log`. Then `git add -f test/fixtures/unlabelled_truth.json` (`*.json` is excluded locally). `test_unlabelled_variables.py` names the file, which satisfies `test_fixtures_are_committed.py` with no edit there.

**Regenerated fixture `test/fixtures/text_truth.json`, through the extended `scripts/extract_text_truth.do` (03-12; R5: S03 is the only WP-29 regenerator).**

New `zp` lines go at the end of the title group (after `t_style_refused`, :190). Format: `zp "<id>" "title" "auto" "<command>" "<option>" "<control>"`.
- Plain scatter, command `twoway scatter mpg weight`, control `t_default`:
  - t_ytitle_nt_size `ytitle(, size(large))`
  - t_xtitle_nt_color `xtitle(, color(red))`
  - t_ytitle_nt_c `ytitle(, c(red))`
  - t_ytitle_nt_comma `ytitle(,)`
  - t_ytitle_nt_dcomma `ytitle(,,)`
  - t_ytitle_trailing `ytitle(A,)`
  - t_ytitle_qtrailing `ytitle("A",)`
  - t_ytitle_dcomma `ytitle(A,,)`
  - t_ytitle_spcomma `ytitle(A, ,)`
  - t_ytitle_size_trailing `ytitle(A, size(large),)`
  - t_title_nt_comma `title(,)`
  - t_title_trailing `title(A,)`
  - t_note_qtrailing `note("N",)`
  - t_ytitle_nt_orient `ytitle(, orientation(horizontal))`
  - t_ytitle_axis1_nt_size `ytitle(, axis(1) size(large))`
  - t_ytitle_empty_suffix `ytitle("", suffix)`
  - t_ytitle_merge_empty_size `ytitle("") ytitle(, size(large))`
  - t_ytitle_merge_size_text `ytitle(, size(large)) ytitle("A")`
  - t_ytitle_merge_trailing_size `ytitle(A,) ytitle(, size(large))`
  - t_ytitle_merge_comma_size `ytitle(,) ytitle(, size(large))`
  - t_by_ytitle_nt_size `by(foreign) ytitle(, size(large))`
- Second axis, command `twoway (scatter mpg weight) (line price weight, yaxis(2))`, control `t_y2_default`:
  - t_ytitle_axis2_nt_size `ytitle(, axis(2) size(large))`
  - t_ytitle_axis2_nt `ytitle(, axis(2))`
  - t_ytitle_axis2_suffix `ytitle(, axis(2) suffix)`
  - t_y2_by `by(foreign)`
  - t_y2_by_title `by(foreign) ytitle(P, axis(2))`
- New controls (option `""`, control `""`):
  - t_x2_default `twoway (scatter mpg weight) (scatter mpg length, xaxis(2))`
  - t_y2_hist `twoway (scatter mpg weight) (histogram weight, yaxis(2))`
  - t_y2_two_layers `twoway (scatter mpg weight) (line price weight, yaxis(2)) (line turn weight, yaxis(2))` (recorded for P1.16, not asserted)
- t_xtitle_axis2_nt_size: command as t_x2_default, `xtitle(, axis(2) size(large))`, control `t_x2_default`.
- t_ytitle_lone_nt_size: command `twoway scatter mpg weight, yaxis(2)`, `ytitle(, axis(2) size(large))`, control `""` (it relies on `_zt_has_top_comma`, like `t_ytitle_axis2_lone`).
- Histogram, control `t_hist_default`, command `twoway histogram mpg`: t_hist_ytitle_nt_size `ytitle(, size(large))`; t_hist_pct_ytitle_nt_size `percent ytitle(, size(large))`.
- Kdensity, control `t_kdens_default`, command `twoway kdensity mpg`: t_kdens_ytitle_nt_size `ytitle(, size(large))`; t_kdens_xtitle_nt_size `xtitle(, size(large))`.
- Colour key, command `twoway scatter mpg weight`:
  - t_z_default, option `colorvar(price)`, control `""`;
  - control `t_z_default`: t_ztitle_nt_size `colorvar(price) ztitle(, size(large))`, t_ztitle_nt_color `colorvar(price) ztitle(, color(red))`, t_ztitle_suffix `colorvar(price) ztitle("extra", suffix)`, t_ztitle_empty `colorvar(price) ztitle("")`.

A control probe with a top-level comma in its command would get a second comma (the loop at :258-261 appends `, name(...)` when the option is empty). That is why by() and colorvar() go in the option field.

Header comment updates:
- the probe count (42 → 42 + the new title probes);
- "Only ONE of the 42 probes" becomes "Only TWO ... (`t_ytitle_axis2_lone`, `t_ytitle_lone_nt_size`)".

In the python block, per probe, add the additive key `"text_records": [[e["text"], e["size"], e["fill"], e["rotate"]] for e in entries]` (D-03b). Existing keys are unchanged.

The run:
1. Point `ZA_REPO` at `$WT`.
2. Run `dash_nobrowser=1 scripts/stata_slot.sh "$S" "$WT/scripts/extract_text_truth.do"` (log `$S/extract_text_truth.log`).
3. Restore `ZA_REPO`.
4. Verify that for every probe present before, every key present before is equal; that `_meta` keeps its keys; and that only `text_records` is new on old probes.
5. `git add -f test/fixtures/text_truth.json`.

**Certification blocks in `test/test_wp29_truth.cscript` (03-10, 03-17).** Two blocks, above the marker, after S01's and S02's blocks (R1, section order), both gated on S03:

```
* ==== S03 P0.3: unlabelled variables ====
python:   <the _s03_* helpers; braces allowed here, outside the gate>
end
local only : env WP29_ONLY
if inlist("`only'", "", "S03") {
    display as text "S03 P0.3 start `c(current_time)'"
    ... UL-01 .. UL-08 (python blocks inside the gate hold NO brace: use dict(), never {}) ...
    display as text "S03 P0.3 end `c(current_time)'"
}
* ==== end S03 P0.3 ====
* ==== S03 P0.4: title sub-options without text ====
local only : env WP29_ONLY
if inlist("`only'", "", "S03") {
    ... ET-01 .. ET-10 ...
}
* ==== end S03 P0.4 ====
```

Run them through the driver (index "The cscript driver"):

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp29_truth.cscript > "$S/run_test_wp29_truth.do"
dash_nobrowser=1 WP29_ONLY=S03 scripts/stata_slot.sh "$S" "$S/run_test_wp29_truth.do"   # log: $S/run_test_wp29_truth.log
```

Read the log; never relaunch to check. A `SKIP: Python not available` exit 222 is not a pass: check `c(python_exec)` (the python_exec hazard).

## TDD test stubs

Base sha: `$(cat <scratch>/batch-1-base.txt)` for P0.3. For P0.4 it is the `wp29-s03` HEAD after the P0.3 commit. "Fails at base" means the stated text in `$S/03-P0.<n>-failure.txt`. Tests marked **guard** pass at base on purpose and are listed separately in the failure file (G1).

### P0.3 — `test/test_unlabelled_variables.py` (new)

Module setup:
- `_NAMES = ["x","y","y1","y2","z","g","t","w"]` and 12 rows mirroring `_zu_data`: `y = n + 0.5`, `y1 = n`, `y2 = n + 3`, `x = 2n`, `z = n % 4`, `g = n % 2`, `t = 14610 + n`, `w = 1.5n`, for n = 1..12.
- `_write_data(tmp_path, labels)` writes the file with `dr._dash_write_stata_data(path, " ".join(_NAMES), sfi=FakeSfi(columns, {v: "double" for v in _NAMES}, var_labels=labels))`. `FakeSfi` is imported from `test_string_value_export`. This is byte for byte what Stata writes.
- The spec carries `build_options["formats"] = {"t": "%td"}`.
- `_saved(spec, data)` is `DashRenderer(sp, dp)` + `render()`. `_served(spec, data)` is `ServerAppBuilder(sp, dp).build(ap)`, exec, then `make_document(Document())`.
- `_profile(figs)` gives, per figure: x titles, y titles, right titles, legend item labels (excluding `dr._COLORVAR_LEGEND_NAME`) and HoverTool row labels.
- `unlabelled_truth.json` is loaded with `pytest.fail` naming 03-02 if it is absent (never skip).
- `MODES = ("saved", "served")`.

Tests:
- Test: `TestTheVarLabelRule::test_an_empty_label_is_the_name`. `_dash_var_label({'y': ''}, 'y') == 'y'`. Fails at base: `AttributeError: ... no attribute '_dash_var_label'`.
- Test: `TestTheVarLabelRule::test_a_label_wins`. `{'y': 'Mileage'}` gives `'Mileage'`.
- Test: `TestTheVarLabelRule::test_a_label_of_blanks_is_kept`. `{'y': '   '}` gives `'   '`, equal to the fixture's `ul_blank_title` rotated text.
- Test: `TestTheVarLabelRule::test_no_name_takes_the_default`. `({}, '', 'x')` gives `'x'`; `({}, None, 'y')` gives `'y'`.
- Test: `TestTheVarLabelRule::test_a_non_text_label_is_the_name`. Labels `5`, `None` and `{'a': 1}` each give the name.
- Test: `TestTheVarLabelRule::test_a_non_text_name_never_raises` (A5). `(dict(), ['a'])` gives `"['a']"`; `(dict(), {'a': 1})` gives `"{'a': 1}"`; `(['bad'], 'y')` gives `'y'`.
- Test: `TestCleanVarLabels::test_empty_and_non_text_labels_become_the_name`. `{'y': '', 'x': 'Lab', 'w': None}` gives `{'y': 'y', 'x': 'Lab', 'w': 'w'}`.
- Test: `TestCleanVarLabels::test_a_non_mapping_is_empty`. `['a']`, `None` and `'str'` each give `{}`.
- Test: `TestCleanVarLabels::test_a_non_text_or_empty_key_is_dropped`. `{3: 'z', '': 'q'}` gives `{}`.
- Test: `TestFilterBaseTitle::test_label_then_variable_label_then_name`:
  - `('', {'x': ''}, 'x')` → `'x'`;
  - `('  ', {'x': '  '}, 'x')` → `'x'`;
  - `('L', {'x': 'Lab'}, 'x')` → `'L'`;
  - `('', {'x': 'Lab'}, 'x')` → `'Lab'`;
  - `('', ['x'], 'x')` → `'x'`.
- Test, parametrised over `MODES`, in `TestBothModesNameAnUnlabelledVariable`. Each test's fixture probe is checked first, then dash.
  - `test_axis_titles_are_the_names[mode]`: `scatter y x` gives x `'x'`, y `'y'` (ul_scatter). Fails at base: `[None]`.
  - `test_legend_keys_are_the_names[mode]`: `(scatter y1 x)(scatter y2 x)` gives `['y1','y2']`, equal to `ul_two_layers.keys_in_drawn_order`. Fails at base: `['scatter','scatter']`.
  - `test_a_fit_beside_data_keys_the_data_by_name[mode]`: gives `['y','Fitted values']` (ul_fit). Fails at base: `['scatter','Fitted values']`.
  - `test_a_mixed_graph_uses_label_or_name[mode]`: with `y1` labelled `First`, gives `['First','y2']` (ul_mixed). Fails at base: `['First','scatter']`.
  - `test_a_label_of_blanks_is_drawn_blank[mode]`: `scatter w x` gives y title `'   '` (ul_blank_title), and `(scatter w x)(scatter y2 x)` gives keys `['   ','y2']` (ul_blank_key). Partly a guard: the title passes at base, the key list fails with `'scatter'`.
  - `test_legend_on_keys_a_single_layer_by_name[mode]`: `scatter y x` with `legend: "on"` gives `['y']` (ul_legend_on). Fails at base: `['scatter']`.
  - `test_histogram_titles_and_bin_row_name_the_variable[mode]`: `histogram x` gives x title `'x'`, y `'Density'` (ul_hist), and bin row label `'x'`. Fails at base: x `None`, bin row `''`.
  - `test_univariate_keys_follow_twoway[mode]` (A2): `(histogram x)(kdensity x)` gives `['Density','kdensity x']` (ul_hist_kd); the percent, frequency and fraction variants follow their probes; `(kdensity x)(kdensity y)` gives `['kdensity x','kdensity y']` (ul_kd2), even with x and y labelled (ul_kd_labelled). Fails at base: `['histogram','kdensity']`.
  - `test_tooltip_rows_name_the_variables[mode]`: `scatter y x` with the graph option `hover: "z"` (a space-separated string in `graph_options`, as `test_display_format_sites.py::_graph` (:89) builds it) gives labels `['x','y','z']`. Fails at base: `['','','']`.
  - `test_a_computed_layer_never_names_an_unrelated_variable[mode]` (A3): `lfit y2 y1` gives `['y1','y2']`; `kdensity z` gives `['x','y']` from `_x_label`/`_y_label` defaults, not the dataset's x/y. Fails at base: `['','']`.
  - `test_a_range_tooltip_names_both_ends[mode]`: `rcap y1 y2 x` gives `['x','y1','y2']`. Fails at base: `['','','']`.
  - `test_by_panels_title_axes_by_name[mode]` (A4): `scatter y x, by(g)` gives a set of non-empty axis titles over all panels `== {'x','y'}`. Fails at base: empty set.
  - `test_a_date_axis_is_titled_by_name[mode]`: `line y t` gives x title `'t'` (ul_date). Fails at base: `None`.
  - `test_a_colour_key_is_titled_by_name[mode]`: `scatter y x, colorvar(z)` gives a ColorBar title `'z'` (ul_colorvar). Guard.
  - `test_filter_widgets_are_titled_by_name[mode]`: filters `x` range, `g` dropdown and `w` (labelled `"   "`) range. Each filter dict carries both `"var"` (served key) and `"varname"` (saved key). Titles sorted `['g','w','x']`. Fails at base, served: `['', '', '   ']`. Guard saved.
  - `test_the_modes_agree`: the profile of a five-graph dashboard (sc, two, fit, hist, rcap) and its widget titles are equal across modes.
- Test: `TestAfterAFilterMove::test_served_names_survive_a_move`. Fire `x` to `(4.0, 24.0)` with `test_served_linked_views._fire`. Then the profile is unchanged and equals the names. Fails at base on the names.
- Test: `TestAfterAFilterMove::test_the_saved_scripts_never_rewrite_titles` (A6). For every `<script type="application/json">` of a saved page with a filter, collect each `CustomJS` object's `code`. For every module-level `str` of `dash_render` longer than 200 characters that contains `function` or `=>`, assert no match of `\.(axis_label|tooltips|title|label)\s*=`. Guard (it pins why a move cannot regress the saved page).
- Test: `TestMalformedLabels::test_the_build_draws_names[mode]`, parametrised over `variableLabels` `['a']`, `{'y': 5}`, `{'y': {'a': 1}}`, `{'y': None}`. The build succeeds and the y title is `'y'`. Fails at base with the errors in Evidence.
- Test: `TestTheServedCopy::test_the_app_defines_the_helpers`. The generated app's source has `def _dash_var_label(`, `def _dash_clean_var_labels(` and `def _dash_filter_base_title(`, and the loader line calls `_dash_clean_var_labels(`. Fails at base.
- Test: `TestTheFixture::test_meta_keys_and_probes`. `_meta` has `stata_version`, `born_date`, `dash_commit` (40 hex), `extracted`, `scheme_in_force`; every probe id of the "Stata truth" table is present with `rc == 0`. Guard once 03-02 ran.

### P0.3 — other files

- Test: `test/test_conftest_helpers.py::TestTheHelperIsJsonioFaithful::test_an_unlabelled_variable_has_an_empty_label`. For a 2-column frame, `make_data_json(df)["StataJSON"]["variableLabels"]` equals the `variableLabels` that `_dash_write_stata_data` writes through `FakeSfi` with no labels (`{v: ''}`). Fails at base: `{v: v}`.
- Test: `test/test_conftest_helpers.py::TestTheHelperIsJsonioFaithful::test_labels_can_be_given`. `make_data_json(df, variable_labels={'mpg': 'Mileage'})` gives `{'mpg': 'Mileage', 'weight': ''}`. Fails at base: `TypeError` (unexpected keyword).
- Test: `test/test_server_layer_defects.py::TestTheLegendKeyRule::test_an_empty_label_falls_back_to_the_name`. `_dash_legend_key({'type':'scatter','yvar':'mpg'}, {'mpg': ''}) == 'mpg'`. Fails at base: `'scatter'`.
- Flipped: `test/test_server_layer_defects.py::TestTheLegendKeyRule::test_a_univariate_layer_uses_its_var_key` becomes `test_a_univariate_layer_uses_twoways_key`. `{'type':'histogram','var':'mpg'}` → `'Density'`; with `options {'percent': 'percent'}` → `'Percent'`; `{'type':'kdensity','var':'mpg'}` with labels `{'mpg':'Mileage (mpg)'}` → `'kdensity mpg'`. The old `'mpg'` was wrong because twoway keys a histogram by its scale (HK.svg) and kdensity by `kdensity <name>` (KDLAB.svg). The flip is recorded with the `Flipped:` form.
- The helper-flip red list (03-05). Every node that the flip alone turns red at base must be green after 03-07. It includes at least the 3 + 11 nodes listed in Evidence.

### P0.4 — `test/test_textbox_no_text.py` (new)

The file imports `_lone_figure` and `_axes` from `test_dual_axis`, and `_both` and `_colorbar` from `test_colorvar_forms`. It loads `text_truth.json` (`pytest.fail` if absent). `MODES = ("saved", "served")`. `_ONE = [{'type':'scatter','yvar':'y1','xvar':'x','options':{}}]`. `LARGE = f"{dr._textbox_size({'size': 'large'}, None):g}px"`, which is `'15px'`.

- Test: `TestTextboxHasText::test_cases` (parametrised).
  - False: `''`, `','`, `',,'`, `', size(large)'`, `' , size(large)'`, `',size(large)'`, `', suffix'`.
  - True: `'""'`, `'"", size(large)'`, `'" "'`, `'A'`, `'A,'`, `'"A",'`, `'A,,'`.
  - Fails at base: `AttributeError`.
- Test: `TestTrailingComma::test_split_point`. `_textbox_split_point` of `','`, `'A,'`, `'A, '`, `'"A",'` is `0, 1, 1, 3`. Fails at base: `-1`.
- Test: `TestTrailingComma::test_split_point_double`. `'A,,'` → 1, `'A, ,'` → 1, `',,'` → 0; `'"a", "b"'` and `'"a", 2 more'` stay -1. Fails at base: `-1` for the first three.
- Test: `TestTrailingComma::test_parse`. `_parse_textbox_opt` of `'A,'` is `('A', {})`, of `'"A",'` is `('A', {})`, of `','` is `('', {})`. Fails at base: `('A,', {})`, `('A\n,', {})`, `(',', {})`.
- Test: `TestTrailingComma::test_title_family_both_modes[mode]`. `title 'A,'` gives Title text `'A'`; `title ','` gives no title text; `note '"N",'` gives a Label `'N'`. Fails at base: `'A,'`.
- Test: `TestTrailingComma::test_double_comma[mode]`. `ytitle 'A,,'` and `'A, ,'` title `'A'` and emit no warning (`warnings.catch_warnings(record=True)` holds no `ytitle()` note); `',,'` keeps `'y1'`; `'A, size(large),'` gives `'A'` at `LARGE` with no warning. Fails at base: `'A,,'`.
- Test: `TestTrailingComma::test_facet_title_keeps_its_panel[mode]`. `by: 'g'` with `title 'A,'` gives every panel title starting with `'A — '`. Fails at base: `'A, — '`.
- Test: `TestTrailingComma::test_a_routed_double_comma_is_silent`. `_dash_route_axis_titles` of a spec with `ytitle 'A,, axis(2)'` gives `ytitle2 'A, ,'`. Then `_dash_textbox('A, ,', 'ytitle2')` returns `'A'` with no warning. Guard on routing; fails at base on the text.
- Test: `TestTrailingComma::test_comma_digit_is_still_text`. `'"a", 2 more'` and `'a, 1'` give -1 (pin).
- Test: `TestSubOptionsKeepTheDefault::test_size_keeps_the_y_title[mode]`. `ytitle ', size(large)'` gives `yaxis[0].axis_label == 'y1'` and font size `LARGE`. Fails at base: `None`.
- Test: `TestSubOptionsKeepTheDefault::test_colour_keeps_the_x_title[mode]`. `xtitle ', color(red)'` gives `'x'` and `'#ff0000'`. Fails at base: `None`.
- Test: `TestSubOptionsKeepTheDefault::test_every_spelling[mode]`. `', c(red)'`, `',size(large)'`, `' , size(large)'`, `', si(large)'`, `', axis(1) size(large)'`, `','` and `',,'` each give `'y1'`. Fails at base: `None` or `','`.
- Test: `TestSubOptionsKeepTheDefault::test_unhonoured_suboption_keeps_title_and_is_named[mode]`. `', orientation(horizontal)'` and `', lcolor(red) box'` give `'y1'`, and exactly one warning naming the sub-option. Fails at base: `None`.
- Test: `TestSubOptionsKeepTheDefault::test_histogram_kdensity[mode]`. A histogram with `ytitle ', size(large)'` gives `'Density'`; with `percent` it gives `'Percent'`; kdensity's ytitle gives `'kdensity y1'` and its xtitle `'x'`. Fails at base: `None`.
- Test: `TestSubOptionsKeepTheDefault::test_lone_second_axis[mode]`. Every layer `yaxis(2)` with `ytitle2 ', size(large)'` gives a single left axis `'y1'` at `LARGE`. Fails at base: `None`.
- Test: `TestSubOptionsKeepTheDefault::test_by_panels[mode]`. `by 'g'` with `ytitle ', size(large)'` gives every panel's y axis `'y1'` at `LARGE`. Fails at base: `None`.
- Test: `TestSubOptionsKeepTheDefault::test_merged_values[mode]`:
  - `'"A", size(large)'` gives `'A'` at `LARGE`;
  - `', size(large) color(red)'` gives `'y1'`, red, `LARGE`;
  - `'"", size(large)'` removes the title (pin).
- Test: `TestSubOptionsKeepTheDefault::test_empty_text_with_suffix[mode]` (A5). `ytitle '"", suffix'` gives `'y1'` (r5). Guard (passes at base by the old code's luck).
- Test: `TestSubOptionsKeepTheDefault::test_suffix_prefix_alone_and_empty_default`. `_dash_textbox_or_default(', suffix', 'ytitle', 'y1')[0] == 'y1'` and `('"e", suffix', 'ytitle', '')[0] == 'e'`. Fails at base: `AttributeError`.
- Test: `TestSubOptionsKeepTheDefault::test_an_unlabelled_variable_is_styled[mode]`. Data from `make_data_json` with no labels (S03's helper) and `ytitle ', size(large)'` give `'y1'` at `LARGE` (twoway g1: `'z'` at 157.44). Fails at base: `None`.
- Test: `test/test_colorvar_forms.py::TestZOptions::test_ztitle_suboptions_keep_the_key_title`, through `_both`:
  - ColorBar `ztitle ', size(large)'` gives the colour variable's default title at `LARGE`;
  - discrete Legend `', color(red)'` gives the default in red;
  - `','` gives the default;
  - `'"extra", suffix'` gives `'<default>\nextra'`;
  - `'""'` gives `''` (pin).
  - Both modes. Fails at base: `''`.
- Test: `test/test_textbox_multiline.py::TestTextboxSplitPoint::test_a_comma_before_another_comma_or_the_end_splits`. `'A,'` → 1, `'A,,'` → 1, `'A, ,'` → 1, `'"A",'` → 3, `','` → 0. Fails at base: `-1`.
- Test: `TestSecondAxisDefaultTitle::test_default_title[mode]` (part B):
  - dual (`y1` on axis 1, `y2` on yaxis(2)) gives right axis `'y2'`;
  - `ytitle2 ', size(large)'` gives `'y2'` at `LARGE`;
  - `ytitle2 ''` gives `'y2'`;
  - an `xaxis(2)` layer gives a top axis titled by its xvar;
  - `ytitle2 '""'` gives `''` or `None` (pin).
  - Fails at base: `''`.
- Test: `TestSecondAxisDefaultTitle::test_no_default_under_by[mode]` (A3). `by 'g'` with a yaxis(2) layer gives every panel's right axis `''` or `None`. Guard.
- Test: `TestSecondAxisDefaultTitle::test_histogram_on_axis_two[mode]` (A6). A histogram layer on yaxis(2) gives right axis `'Density'` (r8). Fails at base: `''`.
- Test: `TestSecondAxisDefaultTitle::test_suffix_alone[mode]` (A5). `ytitle2 ', suffix'` gives `'y2'` (r13). Fails at base: `''`.
- Test: `TestSecondAxisDefaultTitle::test_scheme_style[mode]`. The right axis's `axis_label_text_font_size`, `axis_label_text_color`, `major_label_text_font_size`, `major_label_text_color`, `axis_line_color` and `axis_line_width` equal the default `SchemeParser`'s. With `xtitle ', size(large)'` the right axis keeps the scheme size in both modes. Fails at base: `'13px'`, `'#444444'`.
- Test: `TestSecondAxisDefaultTitle::test_parity_under_ylabel_labsize` (A8). The right axis's label and tick properties are equal saved and served under `ylabel ', labsize(large)'`. Guard after the fix.
- Test: `TestSchemeApplyToAxis::test_unit`. `SchemeParser.apply_to_axis(LinearAxis())` sets the six properties to the scheme's values, and `apply_to_figure` gives the same primary-axis values as before (compare with the six attributes read at base from a figure built by `apply_to_figure`). Fails at base: `AttributeError`.
- Test: `TestEndToEnd::test_saved_page_document`. `DashRenderer(...).render()` of `ytitle ', size(large)'` holds, in the embedded document JSON, a `LinearAxis` with `axis_label` `'y1'` and `axis_label_text_font_size` `LARGE`. Fails at base: no `axis_label`.
- Test: `TestEndToEnd::test_served_app_after_a_filter_move`. Served app with a `y1` range filter: the y axis is `'y1'` at `LARGE` before and after `test_served_linked_views._fire`. Fails at base.
- Test: `TestLinearTime::test_hostile_commas`. `_textbox_split_point`, `_textbox_has_text` and `_dash_textbox_or_default` on `'a' + ', ' * 200000` and `',' * 200000` each finish in under 2 s. Guard.
- Test: `TestLinearTime::test_hostile_double_commas` (A2). `_dash_textbox(',' * 200000, 'ytitle')` finishes in under 2 s and emits no warning. Fails at base: no split, so the title text is 200,000 commas (asserted: text `''`).
- Test: `TestTheServedCopy::test_names`. The generated app's source defines `_textbox_has_text` and `_dash_textbox_or_default`, and its secondary-axes call passes `var_labels, _DASH_SCHEME`. Fails at base.
- Test: `TestTheFixtureIsPinned::test_dash_draws_what_twoway_draws[pid]`, parametrised over a table `_PINNED = {pid: (plots, graph_options, axis, expected_text, style)}`.
  - The table covers t_ytitle_nt_size, t_xtitle_nt_color, t_ytitle_nt_c, t_ytitle_nt_comma, t_ytitle_trailing, t_ytitle_qtrailing, t_ytitle_dcomma, t_ytitle_spcomma, t_ytitle_size_trailing, t_ytitle_empty_suffix, t_ytitle_merge_* (four), t_ytitle_axis2_nt_size, t_ytitle_axis2_suffix, t_xtitle_axis2_nt_size, t_ytitle_lone_nt_size, t_y2_hist, t_y2_by, t_hist_*, t_kdens_*, t_ztitle_nt_size, t_ztitle_suffix, t_ztitle_empty.
  - The data carry auto's names and labels through `make_data_json(df, variable_labels={'mpg': 'Mileage (mpg)', 'weight': 'Weight (lbs.)', 'price': 'Price', 'length': 'Length (in.)'})`.
  - **(1) The fixture.** `text_records` holds an entry with `expected_text` and the axis's rotation. For a size probe, its size is greater than the control's same text and rotation. For a colour probe, its fill is `#ff0000`. For a removal probe, no entry has that text and rotation.
  - **(2) dash, both modes.** The axis label equals `expected_text` (or is `''`/`None` for a removal), at `LARGE` or `#ff0000` where styled.
  - Fails at base on every non-pin probe.

### Mutation table

| Break this | Test that must die |
|---|---|
| `_dash_var_label` strips the label | `TestTheVarLabelRule::test_a_label_of_blanks_is_kept` |
| drop `_dash_clean_var_labels` from the served loader | `TestBothModesNameAnUnlabelledVariable::test_filter_widgets_are_titled_by_name[served]`, `TestMalformedLabels[served]` |
| `_named` without the generic-column guard | `test_a_computed_layer_never_names_an_unrelated_variable` |
| `_dash_legend_key` keeps `var` for kdensity | `test_univariate_keys_follow_twoway` |
| remove `"_dash_var_label"` from the copy list | `TestTheServedAppCarriesEveryName`, `TestTheServedCopy` |
| regex without `,` in the lookahead | `test_split_point_double`, `test_double_comma` |
| `_dash_textbox` still names `,` tokens | `test_double_comma` (warning), `test_hostile_double_commas` |
| `_label` uses `bool(raw.strip())` | `test_size_keeps_the_y_title` |
| axis-2 default under by() | `test_no_default_under_by` |
| axis 2 styled by copying the primary axis | `test_scheme_style` (saved differs) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| twoway's label-or-name rule, cleaner, widget base title | pytest unit | unlabelled_truth.json (blank label) | n/a |
| titles, keys, tooltips, colour key, widgets on Stata-written data | pytest (`_dash_write_stata_data` + FakeSfi) | unlabelled_truth.json | yes |
| univariate keys | pytest | unlabelled_truth.json | yes |
| computed tooltips name the layer's variables | pytest | none | yes |
| after a filter move | pytest (served `_fire`); saved: JS scan | none | yes |
| malformed `variableLabels` | pytest | none | yes |
| jsonio-faithful helper | pytest | none | n/a |
| helper flip neutral across 94 files | `grep -l make_data_json test/test_*.py \| xargs python3 -m pytest -q -p no:cacheprovider` | none | yes |
| separator, `_textbox_has_text`, `_dash_textbox_or_default` | pytest unit, linear-time | none | n/a |
| sub-options keep the default; merges; suffix/prefix | pytest | text_truth.json | yes |
| colour-key title | pytest (`_both`) | text_truth.json | yes |
| axis-2 default, by() exception, scheme style, parity | pytest | text_truth.json | yes |
| every new fixture probe drawn by dash as twoway draws it | pytest `TestTheFixtureIsPinned` | text_truth.json | yes |
| parity corpus | `test_mode_parity.py` (new CORPUS cases) | none | yes |
| Stata end to end: UL-01..UL-08 | `test_wp29_truth.cscript` S03 P0.3 block | none (Stata computes) | yes (UL-08 served) |
| Stata end to end: ET-01..ET-10 | `test_wp29_truth.cscript` S03 P0.4 block | none | yes (ET-10 served) |
| served names | `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads` | none | served |

**Cases of the P0.3 block** (data from `_zu_data`'s commands; twoway side via `cert_svg_export`/`cert_svg_has_text`/`cert_svg_texts`; dash side via `dash ..., name(...)`, `dash build, saving(<html>) replace nobrowser` and `_s03_page()`):
- **UL-01** `scatter y x`: twoway has texts `y` and `x`; dash axes `default=x|default=y`.
- **UL-02** `(scatter y1 x) (scatter y2 x)`: twoway keys (bare minus `legend(off)`) `y1|y2` equal dash keys.
- **UL-03** `(scatter y x) (lfit y x)`: keys `y|Fitted values`.
- **UL-04** `label variable w "   "`: twoway's y title of `scatter w x` normalises to three blanks, and the dash axes hold `default=   `. Keys of `(scatter w x) (scatter y2 x)` are `   |y2`.
- **UL-05** `histogram x`: twoway `Density`, `x`; dash `default=Density|default=x`.
- **UL-06** `(histogram x) (kdensity x)` and `(kdensity x) (kdensity y)`: keys equal twoway's.
- **UL-07** Tooltip labels on the saved page: `scatter y x` gives `x|y`; `lfit y2 y1` gives `y1|y2` (dash's convention).
- **UL-08** Served (`dash build, saving(<app>) server replace filter(x, type(range)) filter(g, type(dropdown))`):
  1. Exec with the `curdoc` attach replaced, as test_gaps2_truth.cscript:1534-1541 does.
  2. Run `make_document`.
  3. The summary equals the saved page's, built with the same filters.
  4. Widget titles are `g|x`.
  5. After the x RangeSlider's callbacks fire (1 fired), the summary is unchanged.

**Cases of the P0.4 block** (`sysuse auto`):
- **ET-01** `ytitle(, size(large))`: twoway `Mileage (mpg)` at a size above the a0 default; the dash saved y axis `Mileage (mpg)` at `15px`.
- **ET-02** `xtitle(, color(red))`: twoway fill `#ff0000`; dash `#ff0000`.
- **ET-03** `ytitle(,)` keeps the default; `ytitle(A,)` gives `A`; `title(A,)` gives `A`.
- **ET-04** `histogram mpg, ytitle(, size(large))` gives `Density`; `kdensity mpg, ytitle(, size(large))` gives `kdensity mpg`.
- **ET-05** `(scatter mpg weight) (line price weight, yaxis(2)), ytitle(, axis(2) size(large))`: twoway rotated `Price` larger; the dash right axis `Price` at `15px`. Without the option, `Price` in the scheme size.
- **ET-06** `colorvar(price) ztitle(, size(large))`: the key title `Price`.
- **ET-07** `ytitle("") ytitle(, size(large))` gives no title; `ytitle(, size(large)) ytitle("A")` gives `A` at 15px.
- **ET-08** `ytitle(A,,)` and `ytitle(A, size(large),)` give `A`.
- **ET-09** `(scatter mpg weight) (line price weight, yaxis(2)), by(foreign)`: twoway has no rotated `Price`; every dash panel's right axis is blank.
- **ET-10** The served app of ET-01, ET-05 and ET-06 (`dash build, ... server replace filter(mpg, type(range))`) gives the same titles, sizes and key title as the saved page, before and after a move.

Acceptance criteria:
- **AC-03.1** `python3 -m pytest test/test_unlabelled_variables.py test/test_conftest_helpers.py test/test_server_layer_defects.py test/test_server_legend.py test/test_filter_widget_parity.py -q -n0 -p no:cacheprovider` passes with no skip.
- **AC-03.2** `grep -l make_data_json test/test_*.py | xargs python3 -m pytest -q -p no:cacheprovider` reports 0 failed on the fixed tree. `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` passes with its committed baseline unchanged (`git diff --stat test/test_varlist_expansion.py` is empty).
- **AC-03.3** `python3 -m pytest test/test_textbox_no_text.py test/test_colorvar_forms.py test/test_textbox_multiline.py test/test_textbox_grammar.py test/test_dual_axis.py test/test_mode_parity.py -q -n0 -p no:cacheprovider` passes.
- **AC-03.4** The S03 blocks of `test/test_wp29_truth.cscript` print `UL-01 PASS` … `UL-08 PASS` and `ET-01 PASS` … `ET-10 PASS` under `WP29_ONLY=S03`, with no FAIL and no `r(` line.
- **AC-03.5** Both served-name guards and `test_function_test_map.py` pass.
- **AC-03.6** BUGS.md's P0.3 and P0.4 entries are closed in place, naming existing tests. `WP29_OPEN` has no `P0.3`/`P0.4` key. `grep -c '<!-- WP-29 P0.3 -->\|<!-- WP-29 P0.4 -->' CHANGELOG.md` prints 0. `test_tracking_documents.py` passes.
- **AC-03.7** The full suite is green once per commit. Two commits exist on `wp29-s03`, ending `(WP-29 P0.3)` and `(WP-29 P0.4)`, with no `claude|anthropic` in either message.

## Tasks

**Commit boundary.** Tasks 03-01 to 03-11 form the P0.3 commit, subject `Name unlabelled variables by their names in titles, keys, tooltips and widgets (WP-29 P0.3)`, made by 03-11. Tasks 03-12 to 03-19 form the P0.4 commit, subject `Keep the default title when a title option gives only sub-options (WP-29 P0.4)`, made by 03-19.

Both are made on `wp29-s03` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s03` (`$WT`), after one full suite run each. Each body:
1. opens with its saved failure text;
2. then gives the measured defect and what changed where;
3. then carries one line each: `Regression: test/<file>.py::<Class>::<test> -- failed at <sha> with <text>`, `Flipped: <node> -- <old expectation> was wrong because <why>`, `Fixture: test/fixtures/<name>.json (scripts/<extract script>)`, `BUGS.md: "<title>" (closed)`.

No AI reference anywhere; grep the message for `claude|anthropic` before and after committing. Never stage `CLAUDE.md` or `.gitignore`. Every command runs from `$WT`.

<task type="auto" id="03-01">
  <name>Record the blast radius before editing</name>
  <files>none</files>
  <action><![CDATA[
    Set `S=<scratch>/s03` (the scratch directory the orchestrator handed over) and run `mkdir -p "$S"`. From `$WT` run `npx gitnexus analyze`, then `mcp__gitnexus__list_repos` to read the name the worktree was indexed under. Run `gitnexus_impact({target, direction: "upstream", repo})` for: `_dash_axis_labels`, `_dash_legend_key`, `_dash_build_hover`, `_dash_filter_title`, `DashRenderer._load_data`, `DashRenderer._build_filter_widgets`, `GlyphMapper._apply_colorvar`, `_textbox_split_point`, `_parse_textbox_opt`, `_dash_textbox`, `_dash_apply_z_options`, `_dash_add_secondary_axes`, `SchemeParser.apply_to_figure`, `ServerAppBuilder.build`, and `make_data_json` (test/conftest.py). Write each result's direct callers, affected processes and risk level to `$S/03-impact.txt`, beside the grep table of Evidence "Blast radius". HIGH is expected for `_dash_axis_labels` and `make_data_json` (index R8). State that warning in the agent's progress output and continue. If any other symbol returns HIGH or CRITICAL, stop and report it to the orchestrator before editing (CLAUDE.md "Never Do").
  ]]></action>
  <verify><![CDATA[`test -s "$S/03-impact.txt" && grep -c "risk" "$S/03-impact.txt"` prints at least 15.]]></verify>
  <done>The blast radius of every symbol this section edits was recorded, and any unexpected HIGH or CRITICAL result was reported before an edit.</done>
</task>

<task type="auto" id="03-02">
  <name>Extract the unlabelled-variable truth from Stata</name>
  <files>scripts/extract_unlabelled_truth.do, test/fixtures/unlabelled_truth.json</files>
  <action><![CDATA[
    Create `scripts/extract_unlabelled_truth.do` exactly as "Stata truth" specifies (frame copied from scripts/extract_text_truth.do:1-144, `ZU_` prefixes, `set scheme s2color`, `_zu_data`, the `zu` registration, the probes of the table with their `__off` twins, the export loop, the `L|` label lines, and the python block with `texts`, `rotated`, `flat`, `keys_in_drawn_order` and `_meta`). In the python block, write any backtick as `\x60`; never call Stata from it and never use `shell=True`. Point `ZU_REPO` at `$WT` for the run. Run `dash_nobrowser=1 scripts/stata_slot.sh "$S" "$WT/scripts/extract_unlabelled_truth.do"` and read `$S/extract_unlabelled_truth.log`. Check that the recorded values equal Evidence's twoway table (ul_scatter rotated `y`; ul_two_layers keys `y1, y2`; ul_blank_title rotated three blanks; ul_hist_kd keys `Density, kdensity x`; ul_kd_labelled keys `kdensity x, kdensity y`). A difference is investigated, never patched by hand (R5). Restore `ZU_REPO` to `/Users/billy/Desktop/Programs/StataPrograms/d/dash`, then run `git add -f test/fixtures/unlabelled_truth.json`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/unlabelled_truth.json'));m=d['_meta'];assert all(k in m for k in ('stata_version','born_date','dash_commit','extracted','scheme_in_force'));p=d['probes'];assert p['ul_two_layers']['keys_in_drawn_order']==['y1','y2'];assert p['ul_hist_kd']['keys_in_drawn_order']==['Density','kdensity x'];assert [t for t,_ in p['ul_scatter']['rotated']]==['y'];print(len(p))"` prints the probe count with no error; `git ls-files test/fixtures/unlabelled_truth.json` prints the path.]]></verify>
  <done>Stata's own drawing of every unlabelled-variable case was recorded in a committed-ready fixture carrying the D12 stamp.</done>
</task>

<task type="auto" id="03-03">
  <name>Make the test data helper jsonio-faithful</name>
  <files>test/conftest.py, test/test_conftest_helpers.py</files>
  <action><![CDATA[
    In `test/conftest.py::make_data_json` (425-461), add the keyword parameter `variable_labels: "dict | None" = None` and change line 451 to `"variableLabels": {v: (variable_labels or {}).get(v, "") for v in varnames},`. Add a docstring sentence saying this is what `dash_render._dash_write_stata_data` writes for an unlabelled variable, and that a label equal to the name hid P0.3. Create `test/test_conftest_helpers.py` with the two `TestTheHelperIsJsonioFaithful` tests of "TDD test stubs". Import `FakeSfi` from `test_string_value_export` and `make_data_json` from `conftest`. Write the FakeSfi file with `dr._dash_write_stata_data(path, "mpg weight", sfi=FakeSfi({"mpg": [1.0, 2.0], "weight": [3.0, 4.0]}, {"mpg": "double", "weight": "double"}))` and compare its `variableLabels`. Do not touch dash_render.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_conftest_helpers.py -q -n0 -p no:cacheprovider` passes, and `git stash` shows the test failing on the base helper. To check that, run `git stash push test/conftest.py` and the pytest command (2 failed, with `{'mpg': 'mpg', ...}` and an unexpected keyword), then `git stash pop`.]]></verify>
  <done>The shared test helper wrote an empty label for an unlabelled variable, as Stata's exporter does, and a test pinned it against the real writer.</done>
</task>

<task type="auto" id="03-04">
  <name>Write the failing P0.3 regression tests</name>
  <files>test/test_unlabelled_variables.py, test/test_server_layer_defects.py</files>
  <action><![CDATA[
    Create `test/test_unlabelled_variables.py` with every test of "TDD test stubs / P0.3 — test/test_unlabelled_variables.py", with exactly those class and test names and the module setup described there. The data are written by `_dash_write_stata_data` through `FakeSfi`. The spec carries `formats {"t": "%td"}`. Filter dicts carry `var` and `varname`. Served documents come from `ServerAppBuilder(sp, dp).build(ap)` plus exec plus `make_document(Document())`, as `test/test_dual_axis.py::_lone_figure` does. The move uses `from test_served_linked_views import _fire`. Expected values come from `unlabelled_truth.json` where the stub names a probe. In `test/test_server_layer_defects.py::TestTheLegendKeyRule` (1002), add `test_an_empty_label_falls_back_to_the_name`. Replace `test_a_univariate_layer_uses_its_var_key` (1021-1022) by `test_a_univariate_layer_uses_twoways_key` with the three assertions of the stub, and record its `Flipped:` line in `$S/03-P0.3-flips.txt`. Do not touch dash_render.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unlabelled_variables.py test/test_server_layer_defects.py -q -n0 -p no:cacheprovider --co 2>&1 | tail -2` collects with no error, and `$S/03-P0.3-flips.txt` holds one `Flipped:` line.]]></verify>
  <done>Every P0.3 regression test existed with its fixture-driven expectations, and the one pin asserting a variable-named histogram key was flipped with its reason recorded.</done>
</task>

<task type="auto" id="03-05">
  <name>Run red first and record the list</name>
  <files>none</files>
  <action><![CDATA[
    With 03-03's helper and 03-04's tests on the unmodified renderer, run `python3 -m pytest test/test_unlabelled_variables.py test/test_conftest_helpers.py test/test_server_layer_defects.py -q -n0 -p no:cacheprovider -rf > "$S/03-P0.3-new.log" 2>&1`. Then run `grep -l make_data_json test/test_*.py > "$S/03-helper-users.txt"` and `xargs python3 -m pytest -q -p no:cacheprovider -rf < "$S/03-helper-users.txt" > "$S/03-P0.3-helper-red.log" 2>&1`. This covers 94 files and is not the full suite (the conftest lock and the guard hook treat a file list as targeted). Write `$S/03-P0.3-failure.txt` from the two logs: the base sha (`cat <scratch>/batch-1-base.txt`), each new test's failure line (expected texts in "TDD test stubs"), the guard tests that pass, and the complete list of helper-user nodes the flip alone turned red. That list must include the 14 nodes of Evidence; any extra node is added to the list with its failure text. Do not commit, and do not change any test to make it pass.
  ]]></action>
  <verify><![CDATA[`grep -c "FAILED" "$S/03-P0.3-new.log"` is at least 20; `grep -c "test_single_y_output_matches_prefix_baseline\|test_the_labels_name_the_series\|test_without_a_label_it_still_falls_back_to_the_name" "$S/03-P0.3-helper-red.log"` is at least 3; `test -s "$S/03-P0.3-failure.txt"`.]]></verify>
  <done>Every P0.3 regression test and the complete set of tests the faithful helper exposed were shown failing on the unfixed renderer, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="03-06">
  <name>Add the label helpers and clean loaders</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Directly above `def _dash_attach_labels(` (dash_render.py:22449), add `_dash_var_label`, `_dash_clean_var_labels` and `_dash_filter_base_title` as TR-03.1, TR-03.2 and TR-03.3 define them. Each has a docstring citing twoway's measured rule (E.svg: a label of blanks is drawn as given), the security note of TR-03.8, and the name clash with `_dash_filter_label` (23145). Change the saved loader (25160) and the emitted served loader line (29874) to call `_dash_clean_var_labels`. In the served functions tuple, insert `"_dash_var_label", "_dash_clean_var_labels",` after the line holding `"_dash_legend_key", "_dash_legend_entries",` (28619), and `"_dash_filter_base_title",` after `"_dash_filter_title",` (28716). Add the three names to `test/function_test_map.py` in alphabetical place: `_dash_var_label` maps to `test/test_unlabelled_variables.py::TestTheVarLabelRule::test_an_empty_label_is_the_name`, `_dash_clean_var_labels` to `::TestCleanVarLabels::test_empty_and_non_text_labels_become_the_name`, and `_dash_filter_base_title` to `::TestFilterBaseTitle::test_label_then_variable_label_then_name`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unlabelled_variables.py -q -n0 -p no:cacheprovider -k "VarLabelRule or CleanVarLabels or FilterBaseTitle or Malformed or TheServedCopy"` passes; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Both loaders cleaned variableLabels to text keyed by name, the three helpers existed in the module and in the served app, and malformed label maps drew names.</done>
</task>

<task type="auto" id="03-07">
  <name>Route every consumer through the label rule</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-03.4 and TR-03.5 in place:
    - `_dash_axis_labels` 18724 and 18729;
    - `GlyphMapper._apply_colorvar` 6981;
    - `_dash_build_hover` 23904, `_named` 23989-23992 (with the generic-column guard of A3), 23994-23995, 24005 and 24027-24028;
    - `_dash_legend_key` 23579-23601 (histogram by `_DASH_HIST_YTITLES[_dash_histogram_ymode(plot.get("options"))]`, kdensity `"kdensity %s" % v`, then `_dash_var_label`);
    - saved filter titles 27577-27579 through `_dash_filter_base_title`;
    - the emitted served filter title 30953-30954 as TR-03.3 writes it.
    Update each touched docstring to name the rule and its measurement. Leave the dropdown builder's `FilterBuilder._safe` fallback (16630) as it is. Change no JavaScript.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unlabelled_variables.py test/test_conftest_helpers.py test/test_server_layer_defects.py test/test_server_legend.py test/test_filter_widget_parity.py -q -n0 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every title, key, tooltip row, colour-key title and widget title of both renderers read through one label-or-name rule, histogram and kdensity layers were keyed as twoway keys them, and computed tooltips named their own layer's variables.</done>
</task>

<task type="auto" id="03-08">
  <name>Prove the helper flip neutral everywhere</name>
  <files>none</files>
  <action><![CDATA[
    Run `xargs python3 -m pytest -q -p no:cacheprovider -rf < "$S/03-helper-users.txt" > "$S/03-P0.3-helper-green.log" 2>&1`. Every node of 03-05's red list must now pass, and nothing else may fail. Run `git diff --stat test/test_varlist_expansion.py`: it must print nothing, because the SHA-256 page baseline is never re-baselined (R7). A failure that is not on the red list is first diagnosed. If it pins the old blank, type-named or variable-named text (for example a `histogram` key asserted as a label), flip it with a `Flipped:` line appended to `$S/03-P0.3-flips.txt`; never delete it. Any other failure is a defect of 03-06/03-07: fix the code, not the test. Then run `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider` (G3; after the flip, its corpus is unlabelled data).
  ]]></action>
  <verify><![CDATA[`tail -1 "$S/03-P0.3-helper-green.log"` reports 0 failed; `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider 2>&1 | tail -1` reports 0 failed; `git diff --stat test/test_varlist_expansion.py` prints nothing.]]></verify>
  <done>All 94 helper-using test files and the parity corpus passed on the faithful helper with the fix, and the page baseline returned to its committed value untouched.</done>
</task>

<task type="auto" id="03-09">
  <name>Certify P0.3 against Stata in both modes</name>
  <files>test/test_wp29_truth.cscript</files>
  <action><![CDATA[
    Read the S01 scaffold's opening lines for its expect/done tally pair and work directory. In test_gaps2_truth.cscript these are `_gt_expect`, `_gt_done` and local `gt_work` (lines 46-73); use whatever names S01 gave them. Above `* ==== append new blocks above this line ====`, after the S01 and S02 blocks (R1), append the block `* ==== S03 P0.3: unlabelled variables ====` of "Stata truth". It starts with a `python:` block, outside the gate, defining and attaching to `__main__`:
    - `_s03_models(path)`: every object of every `<script type="application/json">` of a page; copy test_gaps2_truth.cscript:403-419, reading all scripts;
    - `_s03_page()`: sets globals `S03_AX` (sorted `range=label` of LinearAxis/LogAxis/DatetimeAxis), `S03_AXS` (`range=label@size@colour`), `S03_KEYS` (legend item labels in order, excluding the legend named `_dash_clegend`), `S03_TIPS` (each HoverTool's row labels joined by `,`, tools joined by `;`), `S03_W` (sorted Select/RangeSlider/Slider titles) and `S03_CBAR` (ColorBar or colour-legend title `title@size@colour`) from page `S03_PAGE`;
    - `_s03_app()`: sets the same globals prefixed `S03_S` from app `S03_APP`. It execs with the attach line replaced, as test_gaps2_truth.cscript:1534-1541 does, then fires the RangeSlider whose `_dash_var` is `S03_MOVE` and sets `S03_FIRED` and `S03_SAME_AFTER` (1 when the summary is unchanged);
    - `_s03_twoway_keys()`: S03_BARE minus S03_OFF, sorted by `(y, x)`, as `_lo_twoway` does at :1283-1292;
    - `_s03_text()`: `size|fill|rotate` of every `<text>` equal to `S03_TXT` in `S03_SVG`.
    Then, gated `if inlist("`only'", "", "S03")`, write UL-01..UL-08 of "Test plan", each closing with `_gt_done UL-0n "<what>"` and never `exit`ing on a failure. Python lines inside the gate hold no brace. Run the driver of "Stata truth" with `WP29_ONLY=S03` and read `$S/run_test_wp29_truth.log`.
  ]]></action>
  <verify><![CDATA[`grep -c "UL-0[1-8] PASS" "$S/run_test_wp29_truth.log"` prints 8; `grep -c " FAIL" "$S/run_test_wp29_truth.log"` prints 0; `grep -c '^r([0-9]*);' "$S/run_test_wp29_truth.log"` prints 0; `grep -c "SKIP" "$S/run_test_wp29_truth.log"` prints 0.]]></verify>
  <done>Stata itself certified that dash names unlabelled variables as twoway draws them, on the saved page and in the served app before and after a move.</done>
</task>

<task type="auto" id="03-10">
  <name>Document the label rule in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    In dash.sthlp item 6 (704-717), rewrite the first sentence so that variable labels "title the axes, key the legend, name the tooltip rows and the colour key, and title filter widgets". Add: "A variable with no label is named by its name there, as {cmd:twoway} names it; a label of blanks is drawn as given, except on a filter widget, which then shows the name. A {cmd:histogram} layer is keyed {cmd:Density}, {cmd:Percent}, {cmd:Frequency} or {cmd:Fraction}, and a {cmd:kdensity} layer {cmd:kdensity} {it:varname}, as in {cmd:twoway}." In the Tooltips paragraph (2606-2632), after its first sentence, add: "Each row is named by the variable's label, or by its name when it has none." Then run `python3 -m pytest test/test_help_conformance.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_3.py test/test_help_claims_4.py test/test_help_claims_5.py test/test_help_claims_6.py test/test_help_claims_7.py test/test_help_claims_8.py -q -p no:cacheprovider`, and update any quote of the changed sentences.
  ]]></action>
  <verify><![CDATA[That pytest command reports 0 failed; `grep -c "named by its name there" dash.sthlp` prints 1.]]></verify>
  <done>The help stated twoway's label-or-name rule for every place dash names a variable, and the twoway keys of histogram and kdensity.</done>
</task>

<task type="auto" id="03-11">
  <name>Close P0.3 and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the entry title as the value of `"P0.3"` in `WP29_OPEN` (test/test_tracking_documents.py). In BUGS.md change that entry's `- [ ]` to `- [x]` in place and rewrite only its Resolution:

    `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.3). Both loaders clean variableLabels through _dash_clean_var_labels, and every consumer reads through _dash_var_label (the label when it is not empty, else the name; a label of blanks drawn as given): _dash_axis_labels, _dash_legend_key (histogram keyed by its scale word, kdensity as kdensity <name>), _dash_build_hover (a computed column named after the layer's own variable), GlyphMapper._apply_colorvar, and the filter widgets of both renderers through _dash_filter_base_title. test/conftest.py make_data_json writes an empty label for an unlabelled variable, as Stata's exporter does. Pinned by test/test_unlabelled_variables.py::TestBothModesNameAnUnlabelledVariable::test_axis_titles_are_the_names, test/test_unlabelled_variables.py::TestBothModesNameAnUnlabelledVariable::test_legend_keys_are_the_names, test/test_unlabelled_variables.py::TestBothModesNameAnUnlabelledVariable::test_tooltip_rows_name_the_variables, test/test_unlabelled_variables.py::TestBothModesNameAnUnlabelledVariable::test_filter_widgets_are_titled_by_name, test/test_conftest_helpers.py::TestTheHelperIsJsonioFaithful::test_an_unlabelled_variable_has_an_empty_label, test/test_wp29_truth.cscript UL-01; fixture test/fixtures/unlabelled_truth.json. Residual, deferred (WP-29): no y title when layers differ, y1/y2 range titles and per-type fit keys stay P1.16; the Graphs by note stays P1.15.`

    Every reference is a full node id. Delete the `"P0.3"` key line from `WP29_OPEN`. In CHANGELOG.md replace `<!-- WP-29 P0.3 -->` in place with one line ending `(WP-29, P0.3)` that names the commands and the old and new values:
    - `dash scatter y x` on unlabelled data drew no axis titles, key `scatter` and tooltip rows `''`; now `x`, `y`, `y`.
    - `(scatter y1 x)(scatter y2 x)` was keyed `scatter scatter`; now `y1 y2`.
    - `(histogram mpg)(kdensity mpg)` was keyed by the variable twice; now `Density` and `kdensity mpg`.
    - Served filter widgets were untitled; now titled by the variable.
    - A malformed variableLabels aborted the build; now draws names.
    - Until P1.16, a multi-layer unlabelled graph draws its first layer's name as y title where twoway draws none.
    Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`, then the full suite once (`python3 -m pytest test/ -q`; prefix `FULL_SUITE_RERUN=1` only if the hook refuses), and read its log. Run `gitnexus_detect_changes()`; only this cycle's symbols and files may appear. Stage only `dash_render.py dash.sthlp BUGS.md CHANGELOG.md test/conftest.py test/test_conftest_helpers.py test/test_unlabelled_variables.py test/test_server_layer_defects.py test/function_test_map.py test/test_tracking_documents.py test/test_wp29_truth.cscript scripts/extract_unlabelled_truth.do`, plus `git add -f test/fixtures/unlabelled_truth.json`, plus any file 03-08 flipped. Commit with the subject of the commit boundary. The body is `$S/03-P0.3-failure.txt`, the defect, the change, then the `Regression:` (one per new failing test, `failed at <base sha> with <text>`), `Flipped:` (from `$S/03-P0.3-flips.txt`), `Fixture: test/fixtures/unlabelled_truth.json (scripts/extract_unlabelled_truth.do)` and `BUGS.md: "<title>" (closed)` lines. Grep the message for `claude|anthropic` before and after committing, and save the message to `$S/03-P0.3-message.txt` for the merger.
  ]]></action>
  <verify><![CDATA[The full suite's last line reports 0 failed; `git log -1 --format=%s | grep -c '(WP-29 P0.3)'` prints 1; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0; `grep -c '<!-- WP-29 P0.3 -->' CHANGELOG.md` prints 0; `grep -c '(WP-29, P0.3)' CHANGELOG.md BUGS.md` prints 2 lines of counts ≥ 1; `git show --stat HEAD | grep -c "CLAUDE.md\|.gitignore"` prints 0.]]></verify>
  <done>P0.3 was closed in BUGS.md naming existing tests, its CHANGELOG marker was replaced with the measured old and new values, and one green commit on wp29-s03 carried the cycle.</done>
</task>

<task type="auto" id="03-12">
  <name>Regenerate the textbox truth with new probes</name>
  <files>scripts/extract_text_truth.do, test/fixtures/text_truth.json</files>
  <action><![CDATA[
    Copy the committed fixture first: `cp test/fixtures/text_truth.json "$S/text_truth.before.json"`. In `scripts/extract_text_truth.do`:
    - add every `zp` line listed in "Stata truth / Regenerated fixture" at the end of the title group, after `t_style_refused` (:190);
    - update the header's probe count and the "Only ONE" sentence;
    - in the python block, add `"text_records": [[e["text"], e["size"], e["fill"], e["rotate"]] for e in entries]` to each `probes_out[pid]` (D-03b), changing no other key.
    Point `ZA_REPO` at `$WT`, run `dash_nobrowser=1 scripts/stata_slot.sh "$S" "$WT/scripts/extract_text_truth.do"`, read `$S/extract_text_truth.log`, and restore `ZA_REPO`. Verify with python that for every probe in the before-file, every key it had is equal in the new file, that `_meta` keeps its keys, and that the new probes match the measurements of Evidence: t_ytitle_nt_size has `['Mileage (mpg)', 157.44, '#000000', -90.0]`; t_ytitle_dcomma has rotated `A`; t_y2_by has no rotated `Price`; t_y2_hist has rotated `Density`. A mismatch is investigated, never patched (R5). Then `git add -f test/fixtures/text_truth.json`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;a=json.load(open('$S/text_truth.before.json'))['probes'];b=json.load(open('test/fixtures/text_truth.json'))['probes'];bad=[(p,k) for p in a for k in a[p] if b[p].get(k)!=a[p][k]];assert not bad,bad;assert ['Mileage (mpg)',157.44,'#000000',-90.0] in b['t_ytitle_nt_size']['text_records'];assert not [r for r in b['t_y2_by']['text_records'] if r[0]=='Price' and r[3]==-90.0];print(len(b))"` prints the new probe count; `python3 -m pytest test/test_textbox_grammar.py test/test_legend_order.py test/test_axis_options.py test/test_ci_plot_index.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The textbox fixture held twoway's drawing of every sub-option-only, trailing-comma, merge, axis-2 and colour-key case, with every earlier probe unchanged.</done>
</task>

<task type="auto" id="03-13">
  <name>Write the failing P0.4 regression tests</name>
  <files>test/test_textbox_no_text.py, test/test_colorvar_forms.py, test/test_textbox_multiline.py</files>
  <action><![CDATA[
    Create `test/test_textbox_no_text.py` with every test of "TDD test stubs / P0.4", with exactly those names, the module setup and the `_PINNED` table. Add `TestZOptions::test_ztitle_suboptions_keep_the_key_title` to `test/test_colorvar_forms.py` (class at :228). Add `TestTextboxSplitPoint::test_a_comma_before_another_comma_or_the_end_splits` to `test/test_textbox_multiline.py` (class at :436). Do not touch dash_render.py. Record `git rev-parse HEAD` (the P0.3 commit) as this cycle's base. Run `python3 -m pytest test/test_textbox_no_text.py "test/test_colorvar_forms.py::TestZOptions" "test/test_textbox_multiline.py::TestTextboxSplitPoint" -q -n0 -p no:cacheprovider -rf > "$S/03-P0.4-new.log" 2>&1`, and write `$S/03-P0.4-failure.txt`: the base sha, each failure line (expected texts in the stubs, for example `assert None == 'y1'` and `'' == 'y2'`), and the guard tests that pass. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "FAILED" "$S/03-P0.4-new.log"` is at least 25 and `grep -c "error" "$S/03-P0.4-new.log"` shows no collection error; `test -s "$S/03-P0.4-failure.txt"`.]]></verify>
  <done>Every P0.4 regression test existed and failed for its recorded reason on the tree the P0.3 commit left, with nothing committed.</done>
</task>

<task type="auto" id="03-14">
  <name>Keep the default under sub-option-only titles</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-03.9 to TR-03.14:
    - the separator regex at 2751, with its comment extended by A4's rule and r6/r10/r18;
    - `_textbox_has_text` after `_parse_textbox_opt`;
    - the comma-only skip in `_dash_textbox`'s bad loop;
    - `_dash_textbox_or_default` after `_dash_textbox`;
    - `_dash_axis_labels._label` delegating (keep the nested function and its name);
    - the ztitle block of `_dash_apply_z_options`.
    In the served functions tuple, insert `"_textbox_has_text",` after `"_textbox_split_point",` (28535) and `"_dash_textbox_or_default",` after `"_dash_textbox",` (28799); no constant changes. Add `_textbox_has_text` (test `test/test_textbox_no_text.py::TestTextboxHasText::test_cases`) and `_dash_textbox_or_default` (`::TestSubOptionsKeepTheDefault::test_suffix_prefix_alone_and_empty_default`) to `test/function_test_map.py` in alphabetical place, and point `_dash_axis_labels.<locals>._label` at `test/test_textbox_no_text.py::TestSubOptionsKeepTheDefault::test_size_keeps_the_y_title`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_no_text.py "test/test_colorvar_forms.py::TestZOptions" test/test_textbox_multiline.py test/test_textbox_grammar.py -q -n0 -p no:cacheprovider -k "not SecondAxisDefaultTitle and not SchemeApplyToAxis"` reports 0 failed; both served-name guards and `test/test_function_test_map.py` pass.]]></verify>
  <done>A title option carrying only sub-options kept twoway's default text and was styled by them, a trailing or doubled comma opened an empty sub-option list silently, and the colour key's title followed the same rule, in both renderers.</done>
</task>

<task type="auto" id="03-15">
  <name>Title the second axis as twoway does</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-03.15:
    - Extract `SchemeParser.apply_to_axis` from the axis loop of `apply_to_figure` (5474-5481) and make the loop call it.
    - Extend `_dash_add_secondary_axes` (20076) with `var_labels=None, scheme=None`, the by() check, the default from `_dash_axis_labels` over the axis's own layers, `_dash_textbox_or_default`, and `scheme.apply_to_axis(ax)` before the `size()`/`color()` lines.
    - Update its docstring (default, by() exception r7, scheme style, why never copied from the primary axis).
    - Pass `self.variable_labels, self.scheme` at the saved call (26096-26098), and change the served template lines (30414-30415) to pass `var_labels, _DASH_SCHEME`.
    Add `SchemeParser.apply_to_axis` to `test/function_test_map.py` (test `test/test_textbox_no_text.py::TestSchemeApplyToAxis::test_unit`). Tell the S10 agent, through the orchestrator, that the signature changed (S10 depends on 03).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_no_text.py test/test_dual_axis.py test/test_scheme.py -q -n0 -p no:cacheprovider` reports 0 failed; both served-name guards and `test/test_function_test_map.py` pass.]]></verify>
  <done>A second axis was titled by default with its layers' label or univariate title in the scheme's axis style, untitled under by(), and styled identically in both renderers.</done>
</task>

<task type="auto" id="03-16">
  <name>Add parity cases and flip exposed pins</name>
  <files>test/test_mode_parity.py</files>
  <action><![CDATA[
    Append to `CORPUS` (test/test_mode_parity.py:1126, before its closing bracket):
    - `_case("ytitle(, size(large)) keeps the default", [_sc()], None, {"ytitle": ", size(large)"})`;
    - `_case("xtitle(, color(red)) and ytitle(A,,)", [_sc()], None, {"xtitle": ", color(red)", "ytitle": "A,,"})`;
    - `_case("a second axis titled by default and by ytitle2(, size(large))", [_sc(), plot_for("line", {"yaxis": "2"}, yvar="price")], None, {"ytitle2": ", size(large)"})`, using a numeric `_DF` column other than the scatter's y for `yvar`.
    Edit neither `ALLOWED` nor `_MUST_WARN` (R6). Run `python3 -m pytest test/test_mode_parity.py test/test_dual_axis.py test/test_textbox_grammar.py test/test_legend_order.py test/test_axis_options.py test/test_label_sinks.py test/test_server_legend.py test/test_help_claims_1.py -q -n0 -p no:cacheprovider`. A failure that pins today's untitled second axis or a sub-option-only title deleting its default is flipped with a `Flipped:` line in `$S/03-P0.4-flips.txt`, never deleted. Any other failure is fixed in the code.
  ]]></action>
  <verify><![CDATA[That pytest command reports 0 failed and no new skip; `grep -c "keeps the default\|titled by default" test/test_mode_parity.py` prints at least 2.]]></verify>
  <done>The parity corpus held the section's title cases and both modes drew them identically, with any exposed pin flipped and recorded.</done>
</task>

<task type="auto" id="03-17">
  <name>Certify P0.4 against Stata in both modes</name>
  <files>test/test_wp29_truth.cscript</files>
  <action><![CDATA[
    Below `* ==== end S03 P0.3 ====` and above the marker, append the block `* ==== S03 P0.4: title sub-options without text ====`, gated on S03 like the P0.3 block. It reuses the `_s03_*` helpers. Each case:
    1. `sysuse auto, clear`;
    2. runs the twoway command, `cert_svg_export` and `_s03_text()` for the title's text, size and fill;
    3. then `capture dash clear`, the dash command with the same options and `name(et<n>)`, `dash build, saving("<work>/et<n>.html") replace nobrowser` and `_s03_page()`;
    4. compares with the tally's expect helper.
    Write ET-01..ET-10 as "Test plan" lists them. ET-10 builds one served app of the three graphs with `filter(mpg, type(range))` and uses `_s03_app()` with `S03_MOVE mpg`. The python lines inside the gate hold no brace. Update the script's header comment list of blocks with the line `S03  P0.3 unlabelled variables (UL-01..UL-08); P0.4 title sub-options without text (ET-01..ET-10)`. Run the driver with `WP29_ONLY=S03`.
  ]]></action>
  <verify><![CDATA[`grep -c "UL-0[1-8] PASS" "$S/run_test_wp29_truth.log"` prints 8, `grep -c "ET-[01][0-9] PASS" "$S/run_test_wp29_truth.log"` prints 10, and `grep -c " FAIL\|^r([0-9]*);\|SKIP" "$S/run_test_wp29_truth.log"` prints 0.]]></verify>
  <done>Stata itself certified that sub-option-only titles, trailing and doubled commas, merges, the colour-key title and the second axis are drawn as twoway draws them, saved and served.</done>
</task>

<task type="auto" id="03-18">
  <name>Document the textbox rule in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    In dash.sthlp, after the empty-text sentence at 558-562, add: "An axis title given only sub-options -- {cmd:xtitle(, size(large))}, {cmd:ytitle(, color(red))}, {cmd:ytitle(, axis(2) size(large))}, {cmd:ztitle(, size(large))} -- keeps the default title and applies them, as in {cmd:twoway}; only empty quotes remove a title, and {cmd:ytitle("", suffix)} keeps it. The first comma outside quotes and parentheses that is followed by a sub-option name, another comma or nothing opens the sub-options, and empty slots are ignored: {cmd:ytitle(A,)} and {cmd:ytitle(A,,)} are {cmd:ytitle(A)}, and {cmd:ytitle(,)} keeps the default." At 2582-2586, replace "an absent option draws no title either" with: "without one, the second axis is titled as {cmd:twoway} titles it -- by the label (or name) of its first layer's variable, {cmd:Density} or {cmd:kdensity} {it:varname} for those layers -- in the scheme's axis style, and sub-options alone style that title; under {cmd:by()} it has no default title, as in {cmd:twoway}." At 2695-2699, add: "{cmd:ztitle()} given only sub-options styles the key's default title, the colour variable's label; {cmd:suffix} and {cmd:prefix} add lines to it." Run the help-claims and conformance tests of 03-10 and update any quote.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_claims_3.py test/test_help_claims_4.py test/test_help_claims_5.py test/test_help_claims_6.py test/test_help_claims_7.py test/test_help_claims_8.py -q -p no:cacheprovider` reports 0 failed; `grep -c "an absent option draws no title either" dash.sthlp` prints 0.]]></verify>
  <done>The help stated twoway's textbox sub-option rule, the trailing-comma rule, the second axis's default title with its by() exception, and the colour-key title rule.</done>
</task>

<task type="auto" id="03-19">
  <name>Close P0.4 and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP29_OPEN["P0.4"]`. In BUGS.md close that entry in place (`- [x]`) and rewrite its Resolution:

    `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.4). The sub-option separator _TEXTBOX_SUBOPT_RE also opens at a comma followed by another comma or by nothing, and empty slots are not named; _dash_textbox_or_default keeps the default text whenever the text part is blank (_textbox_has_text), so _dash_axis_labels, _dash_apply_z_options and _dash_add_secondary_axes keep twoway's default under size(), color() and the other sub-options, while a typed "" still removes the title. The second axis is titled by default from its own layers (none under by()) and styled by SchemeParser.apply_to_axis, in both renderers. Pinned by test/test_textbox_no_text.py::TestSubOptionsKeepTheDefault::test_size_keeps_the_y_title, test/test_textbox_no_text.py::TestTrailingComma::test_double_comma, test/test_textbox_no_text.py::TestSecondAxisDefaultTitle::test_default_title, test/test_colorvar_forms.py::TestZOptions::test_ztitle_suboptions_keep_the_key_title, test/test_wp29_truth.cscript ET-01; fixture test/fixtures/text_truth.json. Residual, deferred (WP-29): no title when an axis's layers differ stays P1.16; an explicit axis-2 title under by() drawn on every panel stays P1.15; the r(198) refusals stay with DROPIN section 4.`

    Delete the `"P0.4"` key line from `WP29_OPEN`. In CHANGELOG.md replace `<!-- WP-29 P0.4 -->` in place with one line ending `(WP-29, P0.4)`:
    - `ytitle(, size(large))`, `xtitle(, color(red))`, `ztitle(, size(large))` and any title option given only sub-options drew no title (axis_label None) in both modes; the default title is now drawn and styled, as in twoway.
    - `ytitle(,)` drew a literal comma and `title(A,)` drew `A,`; a comma followed by nothing or by another comma now opens an empty sub-option list.
    - The second axis of a yaxis(2)/xaxis(2) graph had no title and Bokeh's 13px #444444 style; it is now titled by its layers' label, in the scheme's axis style, and untitled under by().
    Run `test_tracking_documents.py`, the full suite once (`python3 -m pytest test/ -q`) and `gitnexus_detect_changes()`. Stage only `dash_render.py dash.sthlp BUGS.md CHANGELOG.md scripts/extract_text_truth.do test/test_textbox_no_text.py test/test_colorvar_forms.py test/test_textbox_multiline.py test/test_mode_parity.py test/function_test_map.py test/test_tracking_documents.py test/test_wp29_truth.cscript`, plus `git add -f test/fixtures/text_truth.json` and any file 03-16 flipped. Commit with the boundary's P0.4 subject. The body is `$S/03-P0.4-failure.txt` first, then `Regression:` lines (`failed at <P0.3 commit sha>`), `Flipped:` lines from `$S/03-P0.4-flips.txt`, `Fixture: test/fixtures/text_truth.json (scripts/extract_text_truth.do)` and `BUGS.md: "<title>" (closed)`. Grep the message for `claude|anthropic` before and after, save it to `$S/03-P0.4-message.txt`, and report both commit shas and messages to the orchestrator for the merger. The merger runs `git -C $WT format-patch -1 --stdout <sha> | patch -p1` in the main checkout, oldest first.
  ]]></action>
  <verify><![CDATA[The full suite's last line reports 0 failed; `git log -2 --format=%s | grep -c '(WP-29 P0.[34])'` prints 2; `git log -2 --format=%B | grep -ci 'claude\|anthropic'` prints 0; `grep -c '<!-- WP-29 P0.[34] -->' CHANGELOG.md` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P0.4 was closed in BUGS.md naming existing tests, its CHANGELOG marker carried the measured old and new values, and the section's second green commit on wp29-s03 was ready for the merger.</done>
</task>

## Section completion criteria

- Unlabelled variables are named by their names, and labelled ones by their labels, in every axis title, legend key, tooltip row, colour-key title and filter widget, in both modes, before and after a filter move. A label of blanks is drawn as given. histogram and kdensity layers are keyed as twoway keys them.
- A malformed `variableLabels` draws names in both modes.
- `make_data_json` writes `""` for an unlabelled variable. All 94 helper-using test files pass, and the SHA-256 page baseline is unchanged.
- A title option with only sub-options keeps twoway's default and is styled. A typed `""` removes the title. Trailing and doubled commas are read as twoway reads them, silently. The second axis is titled by default (none under by()) in the scheme's style, identically in both modes.
- `test/test_wp29_truth.cscript` prints UL-01..UL-08 and ET-01..ET-10 PASS under `WP29_ONLY=S03`.
- `unlabelled_truth.json` is new and `text_truth.json` is regenerated with every earlier probe's keys unchanged. Both carry the D12 stamp and are `git add -f`'d.
- Two green commits exist on `wp29-s03`, `(WP-29 P0.3)` then `(WP-29 P0.4)`, each with its failure text, `Regression:`/`Flipped:`/`Fixture:`/`BUGS.md:` lines and no AI reference. Both BUGS.md entries are closed in place, both `WP29_OPEN` keys are deleted and both CHANGELOG markers are replaced.
- No other script is edited: no new `.cscript`, no runner or hygiene-pin edit, no `test_gaps2_truth.cscript` edit, and no tracking document beyond BUGS.md and CHANGELOG.md.

## Notes

- **Two label paths, one rule.** The loaders clean the dict (so any future `.get(v, v)` is right) and the consumers call `_dash_var_label` (so direct callers and unit tests passing raw dicts are right). Keep both: removing either one fails a test of the mutation table.
- **Blank labels differ by sink, on purpose.** Axes, keys and tooltips draw `"   "` (twoway E.svg, BL.svg). Widgets fall back to the name (the saved page's documented chain; there is no twoway truth for widgets). `_dash_filter_base_title` strips; `_dash_var_label` never does.
- **Renderer order (WP-28 note, dash_render.py:20093-20098).** The saved renderer adds the second axis after `_dash_style_axis_titles`, and the served app adds it before. Style it only from the scheme at creation; never copy from the primary axis. `test_scheme_style` fails in saved mode if this is broken.
- **Per-graph scheme.** The saved renderer swaps a graph's own `scheme()` into `self.scheme` (25906-25916). The served app has one `_DASH_SCHEME`. Part B passes each renderer's own scheme object and so inherits that existing difference unchanged; it is not a new one.
- **Filter spec keys differ by renderer.** Saved `_build_filter_widgets` reads `"varname"`; the served template reads `"var"`. Test filter dicts carry both.
- **Python inside a gated cscript block holds no brace.** Stata still scans a skipped block's braces (test_gaps2_truth.cscript:1485-1486). Put the `_s03_*` helpers outside the `if`, where braces are safe.
- **Fixture provenance.** Both extract scripts hardcode the repository root. Point it at the worktree to run, and restore it before staging (scripts/extract_text_truth.do:61-65 says the same). The python blocks write a backtick as `\x60`.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The truth script then exits 222, and a SKIP is not a pass.
- **The red list of 03-05 is the record (R7).** It belongs in the P0.3 commit body. A node that is red only with the flipped helper is never "fixed" by editing the test.
- **Commit bodies** use the BRIEF line forms with WP-29 ids. P0.3's `failed at` sha is `<scratch>/batch-1-base.txt`'s. P0.4's is the P0.3 commit.
- **Shared registries (R1-R7).**
  - **R1:** two S03 blocks in `test_wp29_truth.cscript` above the marker, in section order.
  - **R2:** copy-list entries at 28535, 28619 and 28716 (D-03c adds 28716 and 28799). `function_test_map.py` gains six names in alphabetical place; there is no new Stata program, so no `program_coverage_map.py` change.
  - **R3:** dash.sthlp regions 558-562, 704-717, 2582-2586, 2606-2632 and 2695-2699; BUGS.md entries P0.3/P0.4 in place; CHANGELOG markers P0.3/P0.4; `WP29_OPEN` keys P0.3/P0.4.
  - **R5:** `text_truth.json` regenerated, never hand-patched.
  - **R6:** CORPUS appended; `ALLOWED`/`_MUST_WARN` untouched.
  - **R7:** flips recorded.
- **For S06 (merges after S03 in batch 1).** Its hover tests on unlabelled `hover()` variables see names after S03. Per architect A7, its new tests pass labels explicitly wherever they assert label text.
- **For S10 (batch 2).** `_dash_add_secondary_axes` takes `var_labels` and `scheme` after `key`; S10's axis(#) changes call it with them. `_TEXTBOX_SUBOPT_RE` now matches at a trailing or doubled comma, so `_dash_route_axis_titles` can produce values such as `'A, ,'`, which `_dash_textbox` reads silently.
- **For S12 (batch 2).** `TestAfterAFilterMove::test_the_saved_scripts_never_rewrite_titles` forbids JavaScript writes of `.axis_label`, `.tooltips`, `.title` and `.label`. If S12's stale cue must write one of these, S12 narrows the test to writes carrying variable-label text and records why.
- **Notes for the closeout (S15; architect A5).**
  - **ROADMAP WP-29:** P0.3 and P0.4 rows, with commit shas.
  - **REMAINING.md:** REM-08-05-C3b, REM-08-05-C3a and REM-08-05-M3 are closed by P0.3. CRIT-01 (DROPIN critic pass) is closed by P0.4.
  - **GAPS2:** A13/C10 are PARTLY closed by P0.3. The Tracked line names the histogram and kdensity keys; the open part is the fit, lowess, lpoly and mband keys, the pc and immediate keys, no y title when layers differ, and `y1/y2` range titles.
  - **DROPIN P1.16:** annotate that histogram/kdensity keys are done and that, until P1.16, unlabelled multi-layer graphs and second axes take their first layer's name as title (twoway draws none when the layers differ: a25, k9).
  - **DROPIN P1.15:** add that dash draws an explicit axis-2 title on every by() panel where twoway draws none (r7, s1-s3), and that the future "Graphs by" note must use `_dash_var_label` (`Graphs by Group` / `Graphs by g`, BYL.svg, I.svg).
  - **No new P1 item:** the axis-2 default title is fixed in P0.4.
  - **AGENTS.md invariant:** "every text naming a variable goes through `_dash_var_label`; both loaders clean labels with `_dash_clean_var_labels`; `make_data_json` writes `""` for unlabelled variables" (pinned by `test_unlabelled_variables.py` and `test_conftest_helpers.py`).
- **Line numbers** are `7421d3d`'s. Batch-1 sections that merge before S03 (S01, S09) do not edit `dash_render.py`; symbols are authoritative.
