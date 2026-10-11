# Section 17: Date and format text in keys and tooltips (P1.23 part b)

> Part of: WP-30 · Items: P1.23 part b (entry `P1.23b`) · Risk: yellow · Batch: 6 · Depends on: 01 · Blocks: — · Tasks: 14, 1 commit · Case prefix: DK

## Review amendments

- Fixed (blocker, A139): S17 edited dash.ado's `_dash_validate_value` and `_dash_option_rules`, which S18 also edits in batch 6. The `zlabel()` format refusal (TR-17.9, DK-21..DK-25, the `KINDS` edit, the Changed behaviour line and the `WP30_LISTS` widening) moves to S18 (TR-18.13 (e), AF-14..AF-18). S17 keeps the renderer half and edits no Stata file. Tasks 17-02 and 17-10 are removed and the rest renumbered (16 → 14 tasks). The staging list (21 → 18 files), the BUGS Resolution, the CHANGELOG lines, the help text, AC-17.5, BR-17.3 and the merge notes follow.
- Fixed (minor): 17-14's verify counted files with `git show --name-only --format=`, which prints a leading blank line. It now uses `git diff-tree --no-commit-id --name-only -r HEAD`. The `(WP-30, P1.23b)` count is now 3.
- Fixed (minor): TR-17.10's echo bullet now names the renderer's note path; the Stata echo is S18's.
- Rejected: "D-17a bins in Stata units, not 'ms before binning' as the manifest says". The two are equal for `%td`/`%tc` and only the Stata-unit form is exact for `%tm`…`%ty`, so the manifest's intent is met.
- Rejected: "`%8.0gc` contradicts register P1.5.6's `%7.0gc or %8.0gc`". The ruling asked to measure first. E2 rules out both `%7.0gc` and `%9.0gc`.
- Checked: the anchors (`_apply_colorvar` 8980-8989, `_dash_apply_z_options` 26154-26174, `_dash_build_hover` 27341-27373, dash.ado 2083-2089) match HEAD. S17 shares no function with S16 (S16 edits `_histogram_quads`, S17 `map_histogram`) or S18. The truth block follows TR-01.10 (helpers above the header, `` `w30_work' ``, `_w30_done`). The BUGS title and the single Results marker match section-01.
- (cross-file pass) 17-14 verify: added the key-deletion check `grep -c '^    "P1.23b": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- (cross-file pass) 17-14 verify: added the subject check `git -C $WT log -1 --format=%s` ends `(WP-30 P1.23b)`.
- The review pass applied both lenses.

**Binding readings applied in this file** (index "Index reconciliations", register P1.23 and P1.5):
- **P1.23.2 (M1).** A date colour key is written as twoway writes it: Stata numbers in a comma general format (`15,000`), dates only under `zlabel(, format(%t*))`, which is honoured. This is research decision 2 (a).
- **P1.5.6 [C], A15.** The colour key's fixed format is folded in here and was measured before writing. It is `%8.0gc` (Evidence E2). Neither `%7.0gc` nor `%9.0gc` fits all nine probes. `zlabel(, format())` is honoured for any format the page can write.
- **P1.5.8 (M5, M6), applied to `zlabel()`.** A format twoway refuses (`bogus`, `%9.2x`, `%tdbogus`) is refused with twoway's rc and words, r(198) `invalid format, bogus`. That refusal is dash.ado's, and in batch 6 S18 is `_dash_validate_value`'s one editor (A139), so S18 adds it with its own axis-format refusal (TR-18.13 (e), cases AF-14..AF-18, its Changed behaviour line). S17 does the renderer half: a format twoway accepts that dash cannot write exactly (`%12s`, `%21x`, `%16H`) draws `%9.0g` and is named once.
- **M5.** S17 refuses nothing new, so its `WP30_LISTS` row stays `("Results that change",)`.
- **A150 / X.2.** S06 (batch 2) has landed. The one note this section can print (an unwritable `zlabel()` format) goes through `_dash_report_suboptions`, which S06 routed into twoway's `(note: …)` form. Tests count it the way `test_colorvar_forms.py::TestZOptions` counts zlabel notes at the batch base.
- **R12.** S17 edits none of the one-editor symbols: `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, `_build_filter_widgets` and the four appliers. S18 is batch 6's template and figure-body editor.
- **Section decisions** (this file, each with its reason in Evidence or Technical requirements):
  - **D-17a.** Cuts are computed and rows binned in the variable's Stata units (`_dash_date_units`), not in milliseconds after converting the cuts. The manifest's "converted to ms before binning" is met in its equivalent form. It is identical for `%td`/`%tc`, whose conversion is linear. It is exact for `%tm`…`%ty`, where a `linspace` over milliseconds is not the milliseconds of a `linspace` over months.
  - **D-17b.** `_dash_colorvar_cuts` is not edited. `_dash_colorvar_bins` changes only in its docstring, because both are handed Stata units by their caller.
  - **D-17c.** `zscale(range())` on a date key is read in Stata units. This is folded in under the register's fold rule: same root cause, same function (`_dash_apply_z_options`).
  - **D-17d.** The fixture is `test/fixtures/key_text_truth.json` with its own extractor. `date_axis_truth.json` is S35's, and R7 forbids running another section's extractor. `test/test_date_axis_residuals.py` (PLAN §10) is created here, and S35 appends its classes.
  - **D-17e.** The colour bar's default ticks are all of natscale's `#5` ticks over the plotted values, as twoway lists them. This includes ticks past the data, such as 15,400 over 14,977-15,340. Bokeh draws the ones inside the bar.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:134-144 (P1.23) lists these among the date-axis residuals: "A date `colorvar` key shows ms. Fallback tooltips ignore formats. The histogram tooltip always says "Count"." Research `.ultraplan/wp30/research/p1-23.md` §1 rows 6-8 measured them in both modes. They were re-measured for this file at `c96facd` (Evidence E1):
- `colorvar(date)` draws a colour bar on Bokeh's own ticker, writing numbers around `9.8e+11`.
- `colorlevels(3)` labels its bins `9.78394e+11–9.87898e+11`.
- `colorcuts(15100 15200)` reads its cuts as milliseconds. Both fall below the minimum, so the key is `['≤9.78394e+11', '>9.78394e+11']`.
- `zlabel(, format(%td))` is noted as "not implemented and ignored".
- A date histogram's tooltip reads `@{left}{0}` in epoch milliseconds, and a kdensity's rows are named `x` and `y`.
- Every histogram's height row says `Count`, whatever its measure.

The research's side finding goes further: a numeric colour key of any variable is written in that variable's display format, where twoway writes `%8.0gc` (`price` at `%9.0g` keys `≤5000`; twoway writes `5,000`).

**After this section**, in both modes, before and after a filter move:
- **The colour key.** Its values are read and written in the colour variable's Stata units: the bar's ticks, its binned bounds, a discrete key's levels, `colorcuts()`, `colorlevels()`, `colorvarminmax`, `zlabel()` ticks and `zscale(range())`.
  - The text is twoway's: `%8.0gc` whatever the variable's display format, or `zlabel()`'s `format()`.
  - The bar is ticked where twoway ticks its key (natscale `#5` over the plotted values).
  - So `colorvar(date)` reads `15,000 … 15,400`, `colorcuts(15100 15200)` cuts at those days, and `zlabel(, format(%td))` writes `25jan2001 … 01mar2002`, exactly twoway's texts.
- **Refused formats.** A `zlabel()` format twoway refuses is refused r(198) in twoway's words by S18's dash.ado rule (same batch, TR-17.9); until S18 lands it is drawn in `%9.0g` and named.
- **Computed layers' tooltips.** A histogram's bins and a fit's or density's x and y are written in the display format of the variable they hold: dates as dates, `%12.0fc` with commas.
  - A kdensity's rows are named by its variable and `Density`.
  - A histogram's height row is named as its y axis is titled: `Density`, `Frequency`, `Fraction` or `Percent`.

**Why one section.** All three sub-claims are one defect: dash writes a value that twoway would show in Stata units and display formats in a unit or text of its own. They share one source, the REM-08-05 bullets "Format dates and numbers everywhere they are displayed" (REMAINING.md:2195-2208 colorvar, :2231-2241 fallback hover; ids matched by content in S01's entry). They also share one set of helpers, `_dash_fmt_text`, `_dash_fmt_hover`, `_dash_date_units` and `_dash_units_to_axis`, through two build-time functions that both modes run. Part a (positions on every axis) is S35's, in batch 12, and does not depend on this part (research §8).

**Test order and commit rule (rule 7, D1, A156).** One entry, one commit, `(WP-30 P1.23b)`.
- **17-01 to 17-04** write every regression test and save the failure text to `<scratch>/17-P1.23b-failure.txt`. They never commit. The tests are the pytest classes, the fixture with its fixture-driven tests, and the truth block DK-01..DK-09.
- **17-05 to 17-12** fix, flip, add the parity cases and update the help.
- **17-13** certifies.
- **17-14** closes the entry and commits after one full run through the queue.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every colour key's text and every computed layer's tooltip change in both modes, through two HIGH helpers

**Why.** The text of every numeric colour key changes: a `%9.0g`, `%9.2f` or `%12.0fc` variable now keys in `%8.0gc`. The colour bar moves from Bokeh's ticker to twoway's ticks. Every histogram, fit and density tooltip gains a formatter. `_dash_apply_z_options`, and `_dash_colorvar_bins` for its docstring only, are HIGH in GitNexus. `_dash_build_hover` and `map_histogram` reach every figure in both modes through calls the index cannot see: the emitted app's `_dash_build_hover(` at dash_render.py:35476, and `_dash_glyph_dispatch` at :28534.

**Risk factors.**
1. Tests that pin today's key text and tooltips. The prototype found 12 (Evidence E6), and the executor re-measures.
2. A served-only `NameError` if a new helper is missing from the copy list (RK-9).
3. Float-keyed `major_label_overrides` on a ColorBar must match the FixedTicker's ticks exactly in BokehJS, or a label falls back to Bokeh's own text.
4. Ticks or cuts of a date beyond Stata's calendar give NaN positions.
5. Shared files with batch partners: `dash_render.py` hunks, `dash.sthlp`, `test_mode_parity.py` and the tracking files. S17 edits no Stata file (A139: `_dash_validate_value` is S18's in batch 6).
6. The fallback HoverTool's formatter models add page weight, about 33 KB per distinct `(fmt, kind)`, which is P2.45.

**Mitigation.**
1. The red list was measured on a prototype over 46 test files. 17-09/17-10 flip each node in place with its reason, and the full run before the commit finds any other.
2. G4 runs both served-name guards. Every new name goes at S17's one R2 anchor. Every mode-parameterised test builds the served app through the real template.
3. A headless-Chrome test reads the deserialized `major_label_overrides` map from the saved page and looks each tick up in it. It is the same float-key form the explicit-`zlabel()` labels already use (dash_render.py:26176).
4. `_dash_key_ticks` drops a tick with no finite position. Its unit test passes a tick outside 0100-9999.
5. Every change is gated on a colour key or a computed-only figure. A guard test asserts that a figure with neither builds the same models (ids aside) before and after. The merge notes for R1, R3, R4, R5 and R6 are below.
6. The fallback formatters share the document's `fmt_cache`, so a histogram whose variable a hover tool already writes adds none.

## Dependencies

- **Depends on: 01.** S01 provides:
  - the open BUGS.md entry `P1.23b`, "A date colour key shows epoch milliseconds, fallback tooltips ignore display formats, and the histogram tooltip always says Count";
  - its `WP30_OPEN` key;
  - its `WP30_LISTS` row `("Results that change",)`;
  - the marker `<!-- WP-30 P1.23b -->` in the `**WP-30 (drop-in P1, 03oct2026)**` group of `### Results that change`;
  - the stub block `* ==== S17 P1.23b: Date and format text in keys and tooltips ====` in `test/test_wp30_truth.cscript`;
  - the map anchor `# WP-30 S17 (P1.23b): Date and format text in keys and tooltips (P1.23 part b)` in `test/function_test_map.py` `FUNCTIONS`.
- **Landed earlier and relied on:**
  - **S06** (batch 2): notes in the `(note: …)` form.
  - **S10** (batch 4): sub-option abbreviations. `_dash_parse_axis_spec` reads `for()` as `format()` from then on, and S17 reads `spec["format"]` and so inherits it.
  - **S04** (batch 2): the hashed CSP. S17 adds no JavaScript. Its formatters are the existing `CustomJSHover` writer.
- **Blocks:** none in the manifest. Later sections that touch the same code keep this section's behaviour:
  - S33 (batch 11) styles the ColorBar's chrome and keeps its ticker and overrides.
  - S35 (batch 12) appends to `test/test_date_axis_residuals.py` and moves layers onto mixed axes, where `_dash_fallback_format`'s axis-kind rule already applies.
  - S49 and S55 (horizontal) choose the histogram's bin axis.
- **Parallel batch: 6,** merge order S16, S17, S18.
- **Can run with:** S16 and S18, which edit no function S17 edits.
  - S16 owns `_scheme_alpha`, `_apply_fill_opts`, `_blend_intensity`, `_ci_band_style` and the fill line of `_histogram_quads`, which S17 does not edit.
  - S18 owns `_make_figure_body`, `_generate_app_source`, the new `_dash_axis_tick_formats`, axis `format()` handling and the axis-format refusals, `zlabel()`'s included (dash.ado `_dash_option_rules` and `_dash_validate_value`). S17 reads `_dash_parse_axis_spec` and does not edit it.

## Evidence

All anchors are at `c96facd` (dash_render.py 37,689 lines; dash.ado; dash.sthlp). Symbols are authoritative where lines drift by the batch-6 base.

### E1. The defect, measured both modes at `c96facd`

Probe `<scratch>/wp30/s17-probe/probe.py` builds one spec in both modes through `test/test_date_range.py`'s `_saved`/`_served`. Its data are `_spread_frame()` (12 rows, `date = 14977 + 30*i` `%td`) and a `price` column (`3291 + 1000*i`). The output, verbatim (the saved and served lines are identical):

```
k_date       [('bar', "'auto'", {})]
k_date_lev3  [('legend', ['9.78394e+11–9.87898e+11', '9.87898e+11–9.97402e+11', '9.97402e+11–1.00691e+12'])]
k_date_cuts  [('legend', ['≤9.78394e+11', '>9.78394e+11'])]
k_date_td    [('bar', "'auto'", {})]  ['dash: zlabel() sub-option(s) not implemented and ignored: format(%td)']
k_price_g    [('legend', ['≤5000', '5000–9000', '>9000'])]            (price %9.0g, colorcuts(5000 9000))
k_price_cont [('bar', "'auto'", {})]
h_hist_date  [([('date', '@{left}{0} to @{right}{0}'), ('Count', '@{top}')], {})]
h_hist_freq  [([('lo', '@{left}{0.000} to @{right}{0.000}'), ('Count', '@{top}')], {})]   (lo %9.1f, frequency)
h_lfit_date  [([('date', '@{x}{0}'), ('lo', '@{y}{0.00}')], {})]
h_kdens_date [([('x', '@{x}{0}'), ('y', '@{y}{0.000000}')], {})]
```

Research c8.py measured that the key does not change after a served filter move (before and after `(978393600000.0, 1006905600000.0)`). The saved page's filter script writes no key and no tooltip text.

Stata-built specs agree (research e2e.do/e2e.py: sysuse sp500, `dash build, server` and `dash build, saving()`, rc 0, no note).

### E2. twoway's truth (StataNow 19.5, measured 03oct2026)

Probes `p1.do`-`p4.do` were run as `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/wp30/s17-probe pN.do`. Each starts with `adopath ++ "<repo>/"` and `global dash_nobrowser 1`. Key texts were read from `graph export *.svg` (the `<text>` elements right of the plot region; the last one is the key's title).

**The key format is `%8.0gc`.** From `display` in p1.log:

```
DISP 15000      7gc=[  15000] 8gc=[  15,000] 9gc=[   15,000]
DISP 12345.75   7gc=[  12346] 8gc=[  12,346] 9gc=[ 12,345.8]
DISP 123456.25  7gc=[ 1.2e+05] 8gc=[  123456] 9gc=[  123,456]
DISP 1000000    7gc=[ 1.0e+06] 8gc=[ 1.0e+06] 9gc=[  1000000]
DISP 1296000000000 7gc=[ 1.3e+12] 8gc=[ 1.3e+12] 9gc=[ 1.30e+12]
```

These are compared with the key texts below:
- twoway keys `15,000`, so the format is not `%7.0gc`;
- twoway keys `123456` for six (123456.01..123456.5), so it is not `%9.0gc`;
- `12,346` for mid (12345.608..12346.0), `1.0e+06` for big and `1.3e+12` for `%tc` all agree with `%8.0gc`.

dash's own writer already agrees: `dash_render._dash_fmt_text(v, "%8.0gc")` gives `15,000`, `12,346`, `123456`, `1.0e+06`, `1.3e+12`, `.001235`, `-5,000` for the same values. S18's narrow-width fix covers widths 1-7, so width 8 is unaffected.

**The colour key's texts** (`sysuse sp500`: date `%td`, N 248, 14977..15340; `sysuse auto`):

| Probe | Command (`twoway scatter close open, colorvar(date) …` unless stated) | Key texts |
|---|---|---|
| default | — | `15,000 15,100 15,200 15,300 15,400` |
| colorlevels(3) | `colorlevels(3)` | `15,098 15,219` |
| colorcuts | `colorcuts(15100 15200)` | `15,100 15,200` |
| %td | `zlabel(, format(%td))` | `25jan2001 05may2001 13aug2001 21nov2001 01mar2002` |
| #3 | `zlabel(#3)` | `15,000 15,200 15,400` |
| list | `zlabel(15000 15200)` | `15,000 15,200` |
| labels | `zlabel(15000 "start" 15300 "end")` | `start end` |
| minmax | `zlabel(minmax)` | `14,977 15,340` |
| %9.1fc | `zlabel(, format(%9.1fc))` | `15,000.0 15,100.0 15,200.0 15,300.0 15,400.0` |
| levels + %td | `colorlevels(3) zlabel(, format(%td))` | `03may2001 01sep2001` |
| zscale | `zscale(range(14600 15700))` | `15,000 15,100 15,200 15,300 15,400` (unchanged) |
| %tm on %td | `zlabel(, format(%tm))` | `3210m1 3218m5 3226m9 3235m1 3243m5` |
| m `%tm` | `colorvar(m)` (`gen m = mofd(date)`) | `490 495 500 505` |
| tc `%tc` | `colorvar(tc)` (`gen double tc = cofd(date)`) | `1.3e+12` ×5 |
| dn double | `colorvar(dn)` (`gen double dn = date`) | `15,000 … 15,400` |
| price `%8.0gc` / `%9.0g` | `scatter mpg weight, colorvar(price)` | `0 5,000 10,000 15,000` (both formats) |
| price levels | `… colorvar(price) colorlevels(3)` | `7,496 11,701` |
| price %9.2f | `… zlabel(, format(%9.2f))` | `0.00 5000.00 10000.00 15000.00` |
| price quoted | `… zlabel(, format("%9.2f"))` | `0.00 5000.00 …` (rc 0) |
| price discrete | `… in 1/5, colorvar(price) colordiscrete` (price `%9.0g`) | `4,000 5,000 6,000 7,000 8,000` (ticks, commas) |
| big / tiny | `colorvar(big)` 1080000..5000000 / `tiny` .00121..00170 | `1.0e+06 … 5.0e+06` / `.0012 … .0017` |

**`zlabel()` formats twoway refuses and accepts** (p2.log, p3.log, p4.log):

```
zlabel(, format(bogus))     invalid format, bogus      r(198)   (also on a colordiscrete key)
zlabel(, format(%9.2x))     invalid format, %9.2x      r(198)
zlabel(, format(%tdbogus))  invalid format, %tdbogus   r(198)
zlabel(, format(%12s))      rc 0, keys 0 5000 10000 15000
zlabel(, format(%21x))      rc 0, keys +0.0000000000000X-3ff …
zlabel(, format(%-9.0g))    rc 0
zlabel(, format())          rc 0
zlabel(, f(%9.2f)) / fo() / FORMAT()   option f() not allowed r(198)   (S10's abbreviation rule; minimum for)
confirm format: bogus 7, %9.2x 7, %tdbogus 7, %12s 0, %21x 0, %16H 0, %9.2fc 0, %td 0, %-12.3e 0
dash today: dash scatter mpg weight, colorvar(price) zlabel(, format(bogus)) name(dk1)  ->  rc 0, "graph 'dk1' registered."
```

**Histogram y titles** (research truth1/truth2, p4.log): `histogram date`, `frequency`, `fraction` and `percent` are titled `Density`, `Frequency`, `Fraction` and `Percent`. `display %td 14977` is `02jan2001`, the first bin's start.

twoway has no tooltips, so sub-claims 7-8 are judged against Stata's display formats and twoway's own y title (research §2).

### E3. The colour key code

`GlyphMapper._apply_colorvar` (dash_render.py:8887-9300). Its only caller is `map_scatter` (:9849-9850). `map_connected`, `map_dot` and `map_rconnected` reach it through `map_scatter`. The number text, at :8980-8989:

```python
8980        # A number in the key is the variable's display text (WP-28 S12,
8981        # GAPS2 E3/G6): 4,099 under %8.0gc.  A date's column holds epoch
8982        # milliseconds, which its format cannot write, so it keeps :g.
8983        _cv_fmt = (getattr(self, "formats", {}) or {}).get(varname, "")
8984        _cv_st = (getattr(self, "storage_types", {}) or {}).get(varname)
8985        _num_text = (
8986            (lambda v: _dash_fmt_text(v, _cv_fmt, _cv_st))
8987            if _dash_fmt_kind(_cv_fmt) in ("f", "g", "e")
8988            and not (getattr(self, "date_vars", {}) or {}).get(varname)
8989            else (lambda v: f"{v:g}"))
```

The values, in milliseconds for a date (:9044-9064), are binned as they are (:9095-9108):

```python
9095                    eff_cuts = _dash_colorvar_cuts(dom_vals, cuts, nlevels,
9096                                                   minmax)
9104                    _closed = cuts is None and not minmax
9105                    labels, binned, has_missing = _dash_colorvar_bins(
9106                        dom_vals, eff_cuts, force_discrete, _vlookup,
9107                        closed_ends=_closed, number_text=_num_text,
9108                        bin_values=col_vals)
```

`colordiscrete` levels use `dom_vals`/`col_vals` too (:9114-9128). The continuous bar keeps Bokeh's ticker unless `colorvarminmax` is given (:9250-9263):

```python
9255                if minmax:
9256                    _mm_ticks = sorted(
9257                        {lo, hi} | set(_dash_axis_count_ticks(lo, hi, 5, "")
9258                                       or ()))
9259                    _cbar.ticker = FixedTicker(ticks=_mm_ticks)
9260                mapper = _dash_apply_z_options(fig, _cbar, mapper,
9261                                               self.z_options,
9262                                               *self.z_context)
```

`_dash_colorvar_cuts` (:7724-7765) and `_dash_colorvar_bins` (:7768-7872) do arithmetic only. They take whatever units they are handed. The bins' docstring states today's text rule (:7806-7809: "*number_text* writes an interval boundary (WP-28 S12 …: the variable's display format, ``4,000`` under %8.0gc)").

`_dash_apply_z_options` (:26106-26217) names `format()` and draws `#N` as Bokeh's choice (:26150-26177):

```python
26154            _bad = list(spec.get("unsupported", []))
26155            for _sub, _sv in (("format", spec.get("format")),
26156                              ("labsize", spec.get("labsize"))):
26157                if _sv:
26158                    _bad.append(f"{_sub}({_sv})")
26166            elif spec["mode"] == "minmax":
26167                lo = getattr(out_mapper, "low", None)
26171            elif spec["mode"] == "count":
26172                key_obj.ticker = _dash_count_ticker(spec["count"])
26173            elif spec["mode"] == "explicit" and spec["ticks"]:
26174                key_obj.ticker = FixedTicker(ticks=spec["ticks"])
```

`zscale(range())` widens the mapper with its values taken as they are (:26184-26215). A discrete key names any `zlabel()` whole (:26146-26147).

`_dash_parse_axis_spec` keeps a quoted format's quotes. Measured: `', format("%9.2f")'` gives `'"%9.2f"'`, `'#3, format(%td)'` gives mode count 3 with format `%td`, and `'15000 "start" 15300 "end"'` gives labels `{'15000.0': 'start', '15300.0': 'end'}`.

The helpers it reuses, all already on the served copy lists: `_dash_date_units` and `_dash_units_to_axis` (33168), `_dash_fmt_text` (33213), `_dash_fmt_refusal`/`_dash_fmt_kind` (33203-33204), `_dash_axis_count_ticks` (33262), `_dash_parse_axis_spec` (33230), `_dash_report_suboptions` (33362) and `_STATA_DATE_KINDS` (constants, 33017). `_dash_axis_count_ticks(lo, hi, n, None)` is natscale over linear values and reproduces every twoway key tick set in E2:

```
>>> _dash_axis_count_ticks(14977, 15340, 5, None)  -> [15000.0, 15100.0, 15200.0, 15300.0, 15400.0]
>>> _dash_axis_count_ticks(14977, 15340, 3, None)  -> [15000.0, 15200.0, 15400.0]
>>> _dash_axis_count_ticks(492, 504, 5, None)      -> [490.0, 495.0, 500.0, 505.0]
>>> _dash_axis_count_ticks(3291, 15906, 5, None)   -> [0.0, 5000.0, 10000.0, 15000.0]
>>> _dash_axis_count_ticks(cofd(14977), cofd(15340), 5, None) -> 1.29e12 … 1.33e12, all '1.3e+12' in %8.0gc
```

It must be called with `kind=None`: a date kind there would take `_tsnatscale` over dates, which is an axis rule, while twoway's key is a plain number line.

### E4. The fallback tooltip code

`_dash_build_hover` (dash_render.py:27118-27427) has two callers, both passing the same arguments. They are the saved `DashRenderer._make_figure_body` (:30692-30709) and the emitted app (:35476-35493). The fallback runs only when no renderer carries the comprehensive tooltip's columns (:27329). Its cells use a precision only (:27341-27343):

```python
27341        def _cell(label, col, data):
27342            _p = _tooltip_precision(data.get(col, []))
27343            return (label, f"@{{{col}}}{{{_p}}}")
```

The histogram's bins (:27360-27373):

```python
27367            _bin_var = y1var or univar
27368            _bin_label = _dash_var_label(var_labels, _bin_var, "value")
27369            _p = _tooltip_precision(data.get("left", []))
27372            return ([(_bin_label, f"@{{left}}{{{_p}}} to @{{right}}{{{_p}}}"),
27373                     ("Count", "@{top}")], "vline")
```

`_point_or_line` (:27375-27384) names a computed `x`/`y` by `_named` and reads no format. The hit loop builds the tool with no formatters (:27414-27426):

```python
27423                _rd, (_fb_fields, _fb_mode) = _hit
27424                fig.add_tools(HoverTool(tooltips=_fb_fields,
27425                                        renderers=[_rd], mode=_fb_mode))
```

The comprehensive rows already write formats through `_dash_hover_row` (:27060-27087) → `_dash_fmt_hover` (:21158-21171). That builds a `CustomJSHover` whose args carry `fmt`, `kind` and `storage`, and whose code `_DASH_FMT_MODEL_JS` (:21124-21128) is:

```javascript
var _dash_v = kind ? dash_stata_value_of(%s, kind) : %s;
if (_dash_v === null || _dash_v === undefined) { return "."; }
return dash_fmt_text(_dash_v, fmt, storage);
```

So `kind="td"` writes an epoch-millisecond column as a date. `kind=""` with fmt `%td` writes a Stata value as a date, which is the mixed-axis case S35 creates. The axis a figure draws a date on is read by `_dash_axis_date_kind(fig, axis)` (:841), which both modes mark.

`map_histogram` (:12451-12578) draws through `_histogram_quads` at :12478, :12490 and :12525. It knows its measure: `edges, ymode = self._histogram_grid(arr, options, w)` (:12494), with `_dash_histogram_ymode` (:21656-21662). The words are `_DASH_HIST_YTITLES` (:21652), already on the constants list (:32917), and `_dash_histogram_ymode` is in `_shared_stat_lines` (:33550). `map_histogram` is dispatched as `"histogram": mapper.map_histogram` (:28534) in both modes.

### E5. The Stata side

`zlabel()` is declared in `_dash_parse_graph_opts` (dash.ado:740) and `_dash_parse_plot_opts` (:985). It is passed through untouched: the graph rule table (dash.ado:2083-2089) has no `zlabel` entry.

```stata
2083    local graph ///
2084        xsize=style,1,100  ysize=style,1,100  aspectratio=num,0  hover=varlist  by=byvarlist ///
2085        scheme=scheme ///
2086        xlabel=axislist  ylabel=axislist  xlabel2=axislist  ylabel2=axislist ///
2087        xtick=axislist  ytick=axislist  xtick2=axislist  ytick2=axislist ///
2088        xmtick=axislist  ymtick=axislist ///
2089        xmlabel=axislist  ymlabel=axislist
```

`_dash_validate_value` (:2125-2516) runs every table rule per segment (:2700-2720) and per graph (`_dash_plot`, :5349 and :5371). Its `format` kind (:2479-2505) is the KPI's `fmt()` and refuses `%12s` and `%21x`, which twoway's `zlabel()` accepts, so it cannot serve here. `_dash_axis_pieces` (dash_parse.mata:4419-4432) already splits an axis-label value at Stata's sub-option comma (tag `T`). `_dash_say(style, before, value, after)` (dash_parse.mata:676) echoes user text with no macro expansion. `test/test_option_validation.py:61-64` lists the kinds the table may use (`KINDS`) and checks each has a branch.

### E6. Blast radius (E4; recorded at the batch-6 base)

`gitnexus impact <symbol> -d upstream -r dash`, run at `c96facd`:

| Symbol | Risk | Direct callers / note |
|---|---|---|
| `GlyphMapper._apply_colorvar` | LOW (the manifest says HIGH; measured LOW: 1 direct, `map_scatter`; processes `map_connected`, `map_rconnected`) | every colorvar layer, both modes, through the class copy |
| `_dash_apply_z_options` | **HIGH** (1 direct, `_apply_colorvar`; 3 processes) | warn at 6.0 |
| `_dash_colorvar_bins` | **HIGH** (docstring only) | warn at 6.0 |
| `_dash_colorvar_cuts` | HIGH | read, not edited |
| `_dash_build_hover` | LOW (1 direct, `_make_figure_body`; processes `_build_sources_and_figures`, `_make_figure_body`) | the emitted app's call (:35476) is unseen: real reach is every figure, both modes |
| `GlyphMapper.map_histogram` | UNKNOWN | confirmed by grep: `_dash_glyph_dispatch` (:28534), both modes; every histogram |
| `_dash_option_rules`, `_dash_validate_value` (dash.ado) | UNKNOWN (not indexed) | grep: called at dash.ado:2580/2692/2713/5349/5371; every option value of every command |

### E7. Prototype red list (simulated fix on a scratch copy of `c96facd`)

A scratch tree (`git archive HEAD`) got this section's design of `_apply_colorvar`, `_dash_apply_z_options`, `map_histogram`'s tag and `_dash_build_hover`'s fallback. The dash.ado rule was left out. Its key and tooltip output was the "after" of E1:
- `k_date`: ticks at ms(15000…15300), text `15,000…15,300`;
- `k_date_lev3`: `['14,977–15,087', '15,087–15,197', '15,197–15,307']`;
- `k_date_cuts`: `['≤15,100', '15,100–15,200', '>15,200']`;
- `k_date_td`: `25jan2001 …`, with no note;
- `k_price_g`: `['≤5,000', '5,000–9,000', '>9,000']`;
- `h_hist_date`: `('date', '@{left}{custom} to @{right}{custom}'), ('Density', '@{top}')`;
- `h_kdens_date`: `('date', '@{x}{custom}'), ('Density', …)`.

The saved and served output matched.

46 test files were run on it in five runs. These were the files that mention colorvar, tooltips, HoverTool, histogram, zlabel, kdensity or lfit, test_mode_parity, test_server and test_label_sinks among them. The runs were:
- `10 failed, 7100 passed` (12 files, before the tooltip half was added);
- `498 passed` (7 files);
- `6 failed, 1413 passed` (9 files);
- `2 failed, 2269 passed` (5 files, re-run with the whole design);
- `7148 passed` (22 files).

The 12 failing nodes are the flips of E8. The executor re-measures them in 17-09/17-10 and in the full run.

### E8. Tests that pin today's behaviour (flip in place, never delete; R9)

| Node | Pins | Flip |
|---|---|---|
| `test/test_date_range.py::TestADateColorvarUnderALayersIf::test_colorlevels_cut_the_layers_dates[saved]` and `[served]` (:1076-1092) | bounds in epoch ms with `:g` | bounds are the Stata days `_SPREAD[6] + k*(_SPREAD[11]-_SPREAD[6])/3`, written `%8.0gc` |
| `test/test_server_layer_defects.py::TestTheHoverBuilder::test_a_histogram_gets_the_bin_tooltip` (:1268-1278) | `tooltips[1][0] == "Count"` | `== "Density"` (an untagged quad) |
| `test/test_colorvar_forms.py::TestZOptions::test_zlabel_ticks_the_colour_bar` (:252-270) | `zlabel(#3)` is `BasicTicker(desired_num_ticks=3)` | `FixedTicker` `[5000.0, 10000.0, 15000.0]` over `tp._DF`'s price (3799..11385), overrides `5,000 10,000 15,000` |
| `test/test_colorvar_forms.py::TestZOptions::test_an_unknown_z_sub_option_is_named` (:313-325) | `format(%9.2f)` named | not named; the bar writes `%9.2f` |
| `test/test_colorvar_truth.py::TestTheKeyIsDrawnFromTheLayersRows::test_colorlevels_cuts_of_a_layers_own_if[saved]`, `[served]` (:287-306) | `abs(b[1] - 6828.667) < 0.01` from a `:g` label | `b[1:3] == [6828.7, 9909.3]`, twoway's own `key_texts` (`6,828.7`, `9,909.3`) |
| `test/test_function_audit.py::TestColorCutsPutEachPointInItsLabelledBin::test_each_value_lands_in_the_bin_its_label_describes`, `::test_a_cut_below_the_minimum_is_dropped_here_too`, `::test_the_cuts_may_come_in_any_order` (:317-342) | `≤2000`, `2000–3000` | `≤2,000`, `2,000–3,000` |
| `test/test_unlabelled_variables.py::TestBothModesNameAnUnlabelledVariable::test_a_computed_layer_never_names_an_unrelated_variable[saved]`, `[served]` (:382-388) | kdensity z hovers `["x", "y"]` | `["z", "Density"]`; the lfit half is unchanged |

The manifest's "test_date_range colour-scale rows" were re-measured. Two other date colour-scale tests pin the mapper's millisecond range, which S17 keeps, so they stay green as guards and are not flipped: `TestADateColorvarUnderALayersIf::test_the_key_spans_the_layers_dates` and `::test_a_date_colour_scale_runs_between_its_first_and_last_date` (:888).
`test/test_display_format_sites.py::TestColorvarLabels::test_number_labels_use_the_variables_format` stays green and is not edited, because its price is `%8.0gc`. The `%9.0g` case that tells the two rules apart is S17's new `test_a_g_formatted_variable_keys_with_commas`.

## User stories

- **US-17.1** As a twoway user, I want `scatter close open, colorvar(date)` to key `15,000 … 15,400` as twoway does, and `zlabel(, format(%td))` to key dates, so that my key reads the same as Stata's.
- **US-17.2** As a twoway user, I want `colorcuts(15100 15200)`, `colorlevels(3)`, `zlabel(#3)`, `zlabel(minmax)` and `zscale(range())` on a date colour variable to be read in the variable's own units, so that the bins and ticks fall where twoway puts them.
- **US-17.3** As a twoway user, I want every numeric colour key written as twoway writes it (`5,000`, whatever the variable's display format), and `zlabel(, format(%9.2f))` honoured, so that a pasted command keys the same way (the refusal of `zlabel(, format(bogus))` is S18's US-18.5).
- **US-17.4** As a dashboard publisher, I want a histogram, fit or density tooltip to show dates as dates and numbers in their display format, so that readers see values, not epoch milliseconds.
- **US-17.5** As a dashboard publisher, I want a histogram's tooltip to name its height the way its y axis does (Density, Frequency, Fraction or Percent), so that the number is not mislabelled as a count.
- **US-17.6** As a dashboard publisher, I want all of this identical in the saved page and the served app, before and after a filter move, so that the two outputs agree.
- **US-17.7** As the maintainer, I want twoway's key texts recorded in a fixture and compared live in the truth script, so that the key stays certified against Stata.

## Business requirements

- **BR-17.1** A colour key built from a date variable shows Stata numbers in twoway's `%8.0gc`, the same texts twoway draws for the same command (E2). This covers the bar, binned bounds and discrete levels.
- **BR-17.2** `colorcuts()`, `colorlevels()`/`colornlevels()`, `colorvarminmax`, `zlabel(#N)`, `zlabel(minmax)`, an explicit `zlabel()` list and `zscale(range())` are read in the colour variable's Stata units. Each observation falls in the bin twoway puts it in.
- **BR-17.3** Every numeric colour key is written in `%8.0gc`, unless `zlabel(, format())` names a format, in which case that format is used. A format twoway accepts that dash cannot write draws `%9.0g` and is named once. (A format twoway refuses is refused r(198) `invalid format, <fmt>` by S18's dash.ado rule, BR-18.5.)
- **BR-17.4** The colour bar is ticked at twoway's key ticks (natscale `#5` over the plotted values) with twoway's texts.
- **BR-17.5** The tooltips of histograms, fits and smooths, and kdensity write each value in the display format of the variable it holds. Dates are written as dates. A kdensity's rows are named by its variable and `Density`.
- **BR-17.6** A histogram's height row is named `Density`, `Frequency`, `Fraction` or `Percent`, the word twoway titles its y axis with.
- **BR-17.7** BR-17.1-17.6 hold identically in the saved page and the served app, before and after a filter move.
- **BR-17.8** Nothing changes for a figure with no colour key whose tooltips are not computed-only.

## Technical requirements

- **TR-17.1 New module helpers** (dash_render.py, directly after `_dash_colorvar_bins`, before the `# GlyphMapper` banner at :7875). Each has a docstring that cites WP-30 P1.23b and the E2 measurement.
  - **`_dash_key_format(zopts) -> (fmt, unwritable)`**
    - Reads `format` from `_dash_parse_axis_spec(zopts["zlabel"])` when `zlabel` is non-blank, and strips one pair of enclosing double quotes.
    - No format: returns `("%8.0gc", None)`.
    - A format of at most 60 characters with `_dash_fmt_refusal(fmt) is None`: returns `(fmt, None)`.
    - Otherwise: returns `("%9.0g", fmt[:60])`.
  - **`_dash_key_ticks(units, kind, fmt, labels=None) -> (positions, overrides)`**
    - Takes finite Stata-unit ticks.
    - The position is `_dash_units_to_axis([u], kind)[0]` for a kind in `_STATA_DATE_KINDS`, else `u`. A tick whose position is not finite is dropped.
    - The override text is `labels[str(float(u))]` when the user labelled that value; `_dash_parse_axis_spec` writes label keys in that form, `'15000.0'`. Otherwise it is `_dash_fmt_text(u, fmt)`.
    - Positions are sorted and de-duplicated, and overrides are keyed by `float(position)`.
  - **`_dash_hist_measure(renderer) -> str`**
    - Reads a tag `"dash_hist_<mode>"` from `renderer.tags`.
    - `<mode>` must be a key of `_DASH_HIST_YTITLES`.
    - Returns `_DASH_HIST_YTITLES[mode]`, and `"Density"` (twoway's default) when the renderer has no such tag.
  - **`_dash_fallback_format(var, axis_kind, formats, date_vars, cache) -> CustomJSHover | None`**
    - Returns None unless `var` passes `_dash_is_stata_name`.
    - A date variable (`date_vars[var]` in `_STATA_DATE_KINDS`) gets `_dash_fmt_hover(_dash_date_fmt(formats.get(var, ""), kind), kind if axis_kind == kind else "", "", cache)`. Milliseconds on its own date axis, the Stata value on a numeric one.
    - A variable whose `_dash_fmt_kind(formats.get(var))` is `f`, `g` or `e` gets `_dash_fmt_hover(fmt, "", "", cache)`.
    - Anything else gets None.
    - Storage is `""`, because the column is computed in double.
- **TR-17.2 `GlyphMapper._apply_colorvar`**: four edits, nothing else in the method.
  1. **The number text (:8980-8989).** Replace with:
     - `_cv_kind` = the variable's date kind when it is in `_STATA_DATE_KINDS`, else `""`;
     - `_key_fmt, _key_bad = _dash_key_format(self.z_options)`;
     - `_num_text = lambda v: _dash_fmt_text(v, _key_fmt)`;
     - a comment saying the key is twoway's `%8.0gc` or `zlabel()`'s `format()`, in Stata units.

     `_vlookup` and the `:g` fallback on colliding labels (:9117-9121) stay.
  2. **The key's Stata units.** After `dom_all_missing` (:9064), set `col_units`/`dom_units` to `_dash_date_units(col_vals, _cv_kind)`/`_dash_date_units(dom_vals, _cv_kind)` when `is_numeric and _cv_kind`, else to `col_vals`/`dom_vals`.
  3. **Bins in those units.**
     - `_dash_colorvar_cuts` and `_dash_colorvar_bins` get `dom_units` and `bin_values=col_units` (:9095-9108).
     - The colordiscrete branch reads `dom_units`/`col_units` in `non_nan`, `binned` and `has_missing` (:9114-9128).
     - The colour column and mapper factors are unchanged in kind: label strings.
  4. **Default bar ticks (:9250-9263).** When `dom_units` has a finite value:
     - `_lo_s`/`_hi_s` are its minimum and maximum;
     - the ticks are `_dash_axis_count_ticks(_lo_s, _hi_s, 5, None) or [_lo_s]`, with `{_lo_s, _hi_s}` added under `colorvarminmax`;
     - `_dash_key_ticks(ticks, _cv_kind, _key_fmt)` gives `_cbar.ticker = FixedTicker(ticks=positions)` and `_cbar.major_label_overrides = overrides`;
     - `_dash_apply_z_options(…, kind=_cv_kind, units=(_lo_s, _hi_s))` is called. This keyword extension lands with TR-17.3, in task 17-07.

     With no finite value, the bar keeps Bokeh's ticker and `units=None`. The mapper's `low`/`high` stay in the column's units (milliseconds for a date), so the glyph's colours are unchanged.
- **TR-17.3 `_dash_apply_z_options(fig, key_obj, mapper_obj, zopts, seen, key, kind="", units=None)`.** The two new parameters are keyword-only in practice. The discrete call (:9222) passes neither.
  - **The bar.**
    - `_kfmt, _kbad = _dash_key_format(zopts)`.
    - The named list keeps `unsupported`, `labsize`, `angle` and `grid` as today. It drops the unconditional `format(...)` and adds `format(<_kbad>)` only when `_kbad`.
    - Modes:
      - `none`: `FixedTicker([])` with empty overrides.
      - `minmax`: Stata ticks `[lo, hi]` from `units`.
      - `count`: `_dash_axis_count_ticks(lo, hi, n, None) or []`, unioned with `spec["ticks"]` (US-14.4's `#5 50 "fifty"` form).
      - `explicit`: `spec["ticks"]`.
    - Each tick list goes through `_dash_key_ticks(ticks, kind, _kfmt, spec["labels"])` to the ticker and overrides.
    - With `units=None` the explicit form keeps today's `FixedTicker(ticks=spec["ticks"])` with its labels, and `minmax`/`count` leave the ticker.
  - **A discrete key.** A `zlabel()` whose only content is a writable `format()` (mode `default`, no ticks, no labels, no unsupported, labsize, angle or grid) is honoured silently, because `_apply_colorvar` already wrote the labels in it. Any other `zlabel()` is named whole, as today.
  - **`zscale(range(a b))` with `kind`.** Each bound becomes `_dash_units_to_axis([v], kind)[0]`, and a non-finite one counts as absent. `log` and `reverse` are unchanged.
  - The `_dash_count_ticker` import becomes unused here and is removed from this function only.
- **TR-17.4 `_dash_colorvar_bins` docstring** (:7806-7809). The `number_text` sentence now reads: the caller's writer, "twoway's %8.0gc or zlabel()'s format(), of a value in the variable's Stata units (WP-30 P1.23b)". There is no code change. `_dash_colorvar_cuts` is not edited (D-17b).
- **TR-17.5 `GlyphMapper.map_histogram`.**
  - After `if options is None: options = {}`, set `_hm = "dash_hist_" + _dash_histogram_ymode(options)`.
  - Each of the three renderers `_histogram_quads` returns (:12478, :12490, :12525) gets `r.tags = list(r.tags or []) + [_hm]` before it is returned.
  - The `_mark_silent` path tags first, then marks.
  - `_histogram_quads` itself is not edited, because S16 owns its fill line.
- **TR-17.6 `_dash_build_hover`'s fallback** (:27329-27426). The comprehensive path (:27175-27301) is not touched.
  - **New nested `_layer_of(rd)`** returns the plot spec of the `layers` entry whose renderers hold `rd` (an identity test), or `{}`.
  - **`_cell(label, col, data, var="", axis="x")`.** When `_dash_fallback_format(var, _dash_axis_date_kind(fig, axis), formats, date_vars, fmt_cache)` returns a model `h`, it records `_fb_fmts[f"@{{{col}}}"] = h` and returns `(label, f"@{{{col}}}{{custom}}")`. Otherwise it returns today's precision cell.
  - `_fb_fmts` is a dict created before the shape loop and cleared before each `_shape(_rd, _data)` call. The tool is `HoverTool(tooltips=…, formatters=dict(_fb_fmts), renderers=[_rd], mode=…)`.
  - **Variables per shape:**
    - `_bins`: `_bin_var = _layer_of(rd).get("var") or y1var or univar`. The row is `(_bin_label, f"{L} to {R}")`, where L and R are the field strings of `_cell(_bin_label, "left", data, _bin_var, "x")` and of the same for `"right"`. The second row is `(_dash_hist_measure(rd), "@{top}")`.
    - `_point_or_line` on a layer whose type is `kdensity`, or on no layer when `univar` is set and `xvar` is empty: x var `layer.get("var") or univar`, labelled `_dash_var_label(var_labels, it, "x")`. The y row is `_cell("Density", fy, data)` with no var.
    - `_point_or_line` otherwise:
      - x var = `fx` when `fx` is a key of `formats` or `date_vars`, else `layer.get("xvar") or xvar`;
      - y var = `fy` likewise, else `layer.get("yvar") or y1var`;
      - axes `"x"`, `"y"`;
      - labels unchanged (`_named`).
    - `_range`: x `xvar`, y1 `y1var`, y2 `y2var`.
    - `_segment`: each end's column when it is a key of `formats` or `date_vars`, axes y, x, y, x.
    - `_band`: `fx` → `layer.get("xvar") or xvar`; `f1`/`f2` → `layer.get("yvar") or y1var`.
- **TR-17.7 Served copy list** (R2, S17's anchor). In `_glyph_layer_lines`' functions tuple, after `"_dash_colorvar_domain", "_dash_colorvar_field",` (dash_render.py:33368), add one line, `"_dash_key_format", "_dash_key_ticks", "_dash_hist_measure", "_dash_fallback_format",`, under a comment `# WP-30 P1.23b: the colour key's units and text, the computed tooltips' formats`.
  - `_apply_colorvar` and `map_histogram` travel with `GlyphMapper`.
  - `_dash_apply_z_options` and `_dash_build_hover` are already listed (33369, 33171).
  - No constant is added.
- **TR-17.8 Maps** (A148, X.5). Under the anchor `# WP-30 S17 (P1.23b): Date and format text in keys and tooltips (P1.23 part b)` in `test/function_test_map.py` `FUNCTIONS`, add, alphabetical by key:

  | Key | Test |
  |---|---|
  | `'_dash_build_hover.<locals>._layer_of'` | `test/test_date_axis_residuals.py::TestFallbackTooltipsUseDisplayFormats::test_a_kdensity_names_its_variable_and_density` |
  | `'_dash_fallback_format'` | `test/test_date_axis_residuals.py::TestTheKeyHelpers::test_the_fallback_format_rule` |
  | `'_dash_hist_measure'` | `test/test_date_axis_residuals.py::TestTheKeyHelpers::test_the_measure_word_reads_the_tag` |
  | `'_dash_key_format'` | `test/test_date_axis_residuals.py::TestTheKeyHelpers::test_the_key_format_rule` |
  | `'_dash_key_ticks'` | `test/test_date_axis_residuals.py::TestTheKeyHelpers::test_key_ticks_positions_and_text` |

  No Stata program or Mata function is added, so `test/program_coverage_map.py` is unchanged.
- **TR-17.9 dash.ado: none (review, A139).** The `zlabel()` format refusal (`zlabel=keyformat` in `_dash_option_rules`, its `_dash_validate_value` branch and `KINDS`) is S18's TR-18.13 (e), because S18 is batch 6's one `_dash_validate_value` editor. Until S18 lands, a refused `zlabel()` format reaches the renderer, where `_dash_key_format` draws `%9.0g` and names it (TR-17.1), so no S17 commit is red.
- **TR-17.10 Security (rule 1).**
  - **Key text.**
    - A generated number text, or the user's own `zlabel()` label, which is already a raw canvas sink (`major_label_overrides`, as at :26176).
    - Legend labels are BokehJS text nodes, so no HTML is built.
  - **Tooltips.**
    - Labels: a variable's label (existing path), `_DASH_HIST_YTITLES` words or `"Density"`.
    - Fields: fixed column names (`left`, `right`, `top`, `x`, `y`) or columns `_drawn_field` already checked with `_dash_is_stata_name`.
    - Formatter args: data (`fmt`, `kind`, `storage`) parsed by the existing writer, never pasted into code. The tag holds only `_DASH_HIST_YTITLES` keys.
  - **Bounded lengths.** The renderer reads at most 60 characters of a format, and an unwritable one is named through `_dash_report_suboptions` (S06's note channel, `_dash_display`-bounded echo). The Stata-side refusal and its echo are S18's (TR-18.13 (e)).
  - **No new code paths of concern.** No new JavaScript, CustomJS or `new Function` consumer. No `shell=True`. No `eval` of user text. The extractor's git sha comes from a file `shell` wrote (D12).
- **TR-17.11 Both modes and the move.** Every behaviour is decided at build time by functions both modes run: the class copy and the copy list.
  - The saved filter script writes no key and no tooltip text.
  - The served refresh keeps the colour column's labels (filtered by row index from the build snapshot, dash_render.py:35791-35798) and the tooltip models.
  - A redraw copies data onto the live renderer, which keeps its tag.
  - Tests check each before and after a move (TDD stubs).
- **TR-17.12 Help** (R3: "Mapping a Variable to Colour", plus the one Tooltips sentence the scope names).
  - **dash.sthlp:3156-3162** is rewritten to the text of task 17-12: the key's units, `%8.0gc`, the bar's ticks, `format()` on both keys and the `%9.0g` fallback (the refusal sentence is S18's, in its own Axis and Display paragraph).
  - **dash.sthlp:3057-3058.** "x and y or a histogram's bin and count" becomes "x and y, a {cmd:kdensity}'s x and {cmd:Density}, or a histogram's bin and its height, named as its y axis is titled ({cmd:Density}, {cmd:Frequency}, {cmd:Fraction} or {cmd:Percent})".
  - **dash.sthlp:3059-3062.** The display-format sentence gains "-- a computed layer's bins and points too --".
  - **dash.sthlp:2753.** The `zlab:el()` synopt reads `{synopt:{cmdab:zlab:el(}{it:#}[{it:#} ...][{cmd:, format(}{it:%fmt}{cmd:)}]{cmd:)}}colour-key ticks and number format; see {cmd:colorvar()}{p_end}`.

## Boundaries

- **Not touched (batch partners):**
  - **S16:** `_scheme_alpha`, `_apply_fill_opts`, `_blend_intensity`, `_ci_band_style`, `_histogram_quads`' fill line, and any colour or alpha line of `_apply_colorvar` (:9162-9187, :9265-9271). S16 may recolour nonselection glyphs. S17 edits only the four places of TR-17.2.
  - **S18:** `_make_figure_body`, `_generate_app_source`, `_dash_axis_tick_formats`, `_dash_apply_tick_option`, `_dash_parse_axis_spec`, the `axislist` kind and `_dash_axis_expand`, axis `format()` refusals, and the help's axis-format paragraphs and log example. S18's x/y-label format refusal is its own. S17 refuses only `zlabel()`'s.
- **Not touched (later sections):**
  - **S35** (P1.23a): date positions of layers and axes, `_dash_figure_date_kind`, `_on_axis`, second axes, base, literal layers and the mixed-axis transform. It owns `date_axis_truth.json` and appends classes to `test_date_axis_residuals.py`.
  - **S33:** the ColorBar's chrome (fonts, standoff, scheme keys) keeps S17's ticker and overrides.
  - **S30/S43:** colour grammar in `colormissing()` and `colpalette()`.
  - **S49/S55:** a horizontal histogram's bin axis in the tooltip.
  - **S10:** `zlabel()` sub-option abbreviations and capitals (`f()`, `fo()`, `FORMAT()`).
  - **P2.21:** a repeated `format()` inside one `zlabel()`.
- **Not changed (documented differences that stay):**
  - dash maps an unbinned key continuously. twoway bins it at its ticks (dash.sthlp:3124-3126). The bar draws the ticks that fall inside the plotted range. twoway's ramp spans its whole tick list, for example 0 for price.
  - A discrete key lists its levels. twoway's draws a ramp with natscale ticks (E2, price discrete).
  - The mapper's `low`/`high` stay in the column's units (milliseconds for a date). The guard tests pin them.
- **M6.** Nothing new is printed where twoway is silent. A writable `zlabel()` format, quoted or not, and an empty `format()` are silent.

## Stata truth

**New extractor** `scripts/extract_key_text_truth.do`, writing **`test/fixtures/key_text_truth.json`**. It copies S02's path-free root form (A130, `DASH_REPO`), copied from an extractor S02 converted. Its header comment names the purpose, the output, the run line and the METHOD (the `scripts/svg_truth.py` reader as `extract_colorvar_qualifier_truth.do` uses it).
- After the root block, its first statements are `adopath ++ "<repo>/"` and `global dash_nobrowser 1`, then the `c(python_exec)` gate (exit 601 when empty).
- It writes only under `` `c(tmpdir)'dash_key_text_probe ``.
- `shell git -C "<repo>" rev-parse HEAD > "<work>/sha.txt"` gives the sha. The python block reads it from that file, never calls back into Stata and never uses `shell=True`.

**Probes** (each with `name(g, replace)`, rc captured, `graph export "<work>/<name>.svg", replace` when rc is 0; the twoway command line is stored):
- **`sysuse sp500`:**
  - `k_date` `twoway scatter close open, colorvar(date)`;
  - `k_date_lev3` (… `colorlevels(3)`);
  - `k_date_cuts` (… `colorcuts(15100 15200)`);
  - `k_date_td` (… `zlabel(, format(%td))`);
  - `k_date_n3` (… `zlabel(#3)`);
  - `k_date_minmax` (… `zlabel(minmax)`);
  - `k_date_lbl` (… `zlabel(15000 "start" 15300 "end")`);
  - `k_date_f91` (… `zlabel(, format(%9.1fc))`);
  - `k_date_lev_td` (… `colorlevels(3) zlabel(, format(%td))`);
  - `k_date_zrange` (… `zscale(range(14600 15700))`);
  - `k_date_tm` (… `zlabel(, format(%tm))`);
  - `k_tm` (`gen m = mofd(date)`, `format m %tm`, `colorvar(m)`);
  - `k_tc` (`gen double tc = cofd(date)`, `format tc %tc`, `colorvar(tc)`);
  - `k_dn` (`gen double dn = date`, `colorvar(dn)`);
  - `h_density`, `h_frequency`, `h_fraction`, `h_percent` (`twoway histogram date[, frequency|fraction|percent]`).
- **`sysuse auto`:**
  - `k_price_gc` (`twoway scatter mpg weight, colorvar(price)`);
  - then `format price %9.0g` and `k_price_g`, `k_price_cuts` (… `colorcuts(5000 9000)`), `k_price_lev3` (… `colorlevels(3)`), `k_price_f92` (… `zlabel(, format(%9.2f))`), `k_price_quoted` (… `zlabel(, format("%9.2f"))`);
  - `f_bogus`, `f_92x`, `f_tdbogus` (`zlabel(, format(bogus|%9.2x|%tdbogus))`, recording rc and the first `display as error` line, read from a `log using` text log);
  - `f_12s`, `f_21x` (rc 0 and key texts).
- **`clear`, `set obs 50`, `gen x = _n`, `gen y = _n`:** `k_big` (`gen double big = 1000000 + _n*80000`), `k_tiny` (`.0012 + _n*.00001`), `k_mid` (`12345.6 + _n*.008`), `k_six` (`123456 + _n*.01`), each `twoway scatter y x, colorvar(<v>)`.
- **`display` records:** for v in 15000, 15098.333, 1296000000000, 1000000, 1234567, .00123456, -5000, 12345.75, 123456.25, write `local t : display %7.0gc v` (and `%8.0gc`, `%9.0gc`) verbatim to a records file.

**Fixture keys.**
- `_meta`: `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit`, `extracted` (`c(current_date)`), `script` (D12).
- `display`: `{"<v>": {"%7.0gc": t, "%8.0gc": t, "%9.0gc": t}}`.
- `probes`: `{name: {cmd, rc, err, var, kind, key_texts, ytitle, data}}`.
  - `key_texts` are the `<text>` elements right of `svg_plotregion(svg)["right"]`, in document order, less the last one (the key's title).
  - `ytitle` is the one text of a histogram probe that is in `Density|Frequency|Fraction|Percent`.
  - `data` is the colour variable's values (sp500's 248 dates, months or `%tc`; auto's 74 prices; the 50 generated values), so a test can rebuild the same key.
- A backtick is written `\x60`. The file is staged with `git add -f test/fixtures/key_text_truth.json` (`.git/info/exclude:58`). It is named by `test/test_date_axis_residuals.py`, and `TestTheKeyTextTruth::test_the_fixture_is_stamped` asserts the four `_meta` keys.
- **Run:** `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s17 $WT/scripts/extract_key_text_truth.do` (log `<scratch>/s17/extract_key_text_truth.log`).

**The truth block** (R1). The DK cases go between S01's `display as text "S17 start …"` and `"S17 end …"` lines of `test/test_wp30_truth.cscript`.
- Its python helpers sit directly above `* ==== S17 P1.23b: Date and format text in keys and tooltips ====` and declare nothing in another block.
- Every argument crosses through `sfi.Macro.getGlobal` and every answer goes back through `Macro.setGlobal`. No macro text is pasted into Python source.
- Files go under `` `w30_work' `` and are erased before the end line.
- Run it through the driver:

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > <scratch>/s17/run_test_wp30_truth.do
WP30_ONLY=S17 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s17 <scratch>/s17/run_test_wp30_truth.do
```

| Helper | Reads | Sets |
|---|---|---|
| `_s17_svg()` | `S17_SVG` | `S17_TW`, the twoway key texts joined by `\|` (the fixture's `key_texts` rule). `S17_YT`, the histogram y title word or empty. |
| `_s17_page()` | `S17_PAGE` (a saved page) | Reads the page's Bokeh documents with the WP-29 `_s03_models` method that S07's `_s07_page` reuses. `S17_D`: a ColorBar's `major_label_overrides` values in its FixedTicker's tick order. Else the colorvar Legend's (`_COLORVAR_LEGEND_NAME`) inner bounds: each label split on `–`, with `≤`/`>` stripped, the distinct inner bound texts in order. Else, for a discrete key, its labels. `S17_H`: the fallback HoverTool's second row label. `S17_HF`: the first formatter's `fmt` and `kind` joined by `,`. |
| `_s17_app()` | `S17_APP` (a served `app.py`), `S17_MOVE` | Runs `make_document(Document())` and sets `S17_S`/`S17_SH` (the same summaries). Fires the `Select` whose `_dash_var` is `S17_MOVE` to its second option, as `test_mode_parity._fire` does, and sets `S17_FIRED` to 1 when a callback ran. `S17_SAME_AFTER` is 1 when both summaries are unchanged. |

| Id | twoway | dash | PASS when |
|---|---|---|---|
| DK-01 | `sysuse sp500`; `twoway scatter close open, colorvar(date)` → SVG; `_s17_svg` | `dash scatter close open, colorvar(date) saving(dk01.html, replace) nobrowser`; `_s17_page` | `S17_TW == S17_D == "15,000\|15,100\|15,200\|15,300\|15,400"` |
| DK-02 | … `colorlevels(3)` | same with `colorlevels(3)` | `S17_TW == S17_D == "15,098\|15,219"` |
| DK-03 | … `colorcuts(15100 15200)` | same | `"15,100\|15,200"` both |
| DK-04 | … `zlabel(, format(%td))`; `zlabel(#3)`; `zlabel(minmax)` | same three | each pair equal (`25jan2001…01mar2002`; `15,000\|15,200\|15,400`; `14,977\|15,340`) |
| DK-05 | `gen m = mofd(date)`, `format m %tm`; `colorvar(m)` | same | `"490\|495\|500\|505"` both |
| DK-06 | `sysuse auto`, `format price %9.0g`; `twoway scatter mpg weight, colorvar(price)`; and `colorcuts(5000 9000)` | same two | `"0\|5,000\|10,000\|15,000"` both; `"5,000\|9,000"` both |
| DK-07 | — | `gen byte up = close > open`; DK-01's and DK-02's commands registered with `name(dk07a)`/`name(dk07b)`, then `dash build, server saving(dk07.py, replace) nobrowser filter(up, type(dropdown))`; `_s17_app` with `S17_MOVE up` | `S17_S` equals DK-01's and DK-02's `S17_D`; `S17_FIRED == 1`; `S17_SAME_AFTER == 1` |
| DK-08 | `twoway histogram date[, frequency\|fraction\|percent]` → `S17_YT` | `dash histogram date[, …] saving(…)`; `_s17_page` (and the served app for `frequency`) | `S17_H == S17_YT` for all four (Density, Frequency, Fraction, Percent) |
| DK-09 | `local s = string(14977, "%td")` (twoway's first bin start; E2) | DK-08's default page | `S17_HF == "%td,td"`; dash's Python twin `_dash_fmt_text(_dash_stata_value_of(left0, "td"), "%td")` equals `` `s' `` (`02jan2001`) |

Each case ends `_w30_done DK-0k "<what>"`. No case prints SKIP. The header list of blocks gains `S17  P1.23b colour-key text and computed tooltips against twoway (DK-01..DK-09)`.

**The refusal cases** are S18's (AF-14..AF-18 in `test/test_option_validation.cscript`, TR-18.13 (e)); S17 adds none.

## TDD test stubs

New file `test/test_date_axis_residuals.py`. Its module docstring quotes E1 and E2 (commands and dates) and says S35 appends its classes below S17's.
- **Imports and constants:**
  - `_saved`, `_served`, `_spec`, `_filter` from `test_date_range`;
  - `js_texts` from `test_display_format_sites`;
  - `_fire` from `test_mode_parity`;
  - `JsSession` from `js_runner`;
  - `colour_bins as cb`;
  - `MODES = ("saved", "served")`;
  - `_ms(d) = (d - 3653) * 86400000.0`.
- **Data:**
  - `_KEY = DataFrame(date=[14977 + 33*i for i in range(11)] + [15340], lo=range(12), hi=range(12))`. It has sp500's minimum and maximum, so twoway's sp500 texts apply.
  - `_TM`: 13 rows with `m` = the Stata months 492..504, format `%tm`. The loader converts them, as it converts `date`.
  - `_TC`: `tc = date * 86400000` (Stata's `%tc` milliseconds) for `_KEY`'s dates, format `%tc`.
  - `_PRICE`: `price = [3291, 4099, 4749, 5079, 5788, 6295, 7827, 8814, 9735, 11385, 13466, 15906]`, format `%9.0g`, with `lo`/`hi` 0..11.
- **Helpers:** `_bar(root)` (the one ColorBar: ticks, overrides); `_keys(root)` (the colorvar Legend's labels); `_tool(root)` (the one HoverTool's tooltips and formatters).

### Regression tests (red at the batch-6 base unless marked guard), both modes where a page exists

- Test: `…::TestADateColourKeyIsInStataUnits::test_the_bar_ticks_a_date_at_twoways_numbers[saved|served]` — `colorvar(date)` on `_KEY`; ticks `== [_ms(t) for t in (15000, 15100, 15200, 15300, 15400)]`; overrides texts `15,000 … 15,400`. Base: ticker `'auto'`.
- Test: `…::test_colorlevels_bins_and_labels_in_stata_units[…]` — `colorlevels(3)`; factors `['14,977–15,098', '15,098–15,219', '15,219–15,340']`; rows 0-3, 4-7, 8-11 in bins 0, 1, 2 (15076 ≤ 15098 < 15109; 15208 ≤ 15219 < 15241). Base: `9.78394e+11–…`.
- Test: `…::test_colorcuts_are_read_in_stata_units[…]` — `colorcuts(15100 15200)`; factors `['≤15,100', '15,100–15,200', '>15,200']`; bins of rows `[0,0,0,0,1,1,1,2,2,2,2,2]`. Base: `['≤9.78394e+11', '>9.78394e+11']`.
- Test: `…::test_colordiscrete_levels_are_stata_numbers[…]` — 5 rows (14977, 14978, 14979, 14980, 14983), `colordiscrete`; labels `14,977 14,978 14,979 14,980 14,983`.
- Test: `…::test_colorvarminmax_ticks_the_first_and_last_date[…]` — ticks include `_ms(14977)` and `_ms(15340)` with texts `14,977`, `15,340`.
- Test: `…::test_a_period_key_is_in_its_own_units[…]` — `_TM` `colorvar(m)`: ticks text `490 495 500 505`; `colorlevels(3)`: factors `['492–496', '496–500', '500–504']`.
- Test: `…::test_a_tc_key_is_in_statas_milliseconds[…]` — `_TC`: five ticks, every text `1.3e+12` (twoway `k_tc`).
- Test: `…::test_the_key_is_unchanged_after_a_filter_move[…]` — `_filter("range", "lo")`. Saved: `JsSession(r.filter_callbacks)` moves the slider (as `test_display_format_sites.py::TestParity` does). Served: `_fire(RangeSlider, (2, 9))`. Bar ticks and overrides, Legend factors, and the colour column's labels of the drawn rows are equal before and after.
- Test: `…::TestZlabelOnAColourKey::test_format_td_writes_dates[…]` — `zlabel(, format(%td))`: overrides `25jan2001 05may2001 13aug2001 21nov2001 01mar2002`; no `zlabel` note. Base: `'auto'` plus the note.
- Test: `…::test_count_ticks_are_twoways[…]` — `zlabel(#3)`: ticks `_ms` of 15000, 15200, 15400, texts `15,000 15,200 15,400`.
- Test: `…::test_minmax_ticks_the_first_and_last[…]` — texts `14,977 15,340`.
- Test: `…::test_explicit_ticks_and_labels_are_stata_values[…]` — `zlabel(15000 "start" 15300 "end")`: overrides `{_ms(15000): 'start', _ms(15300): 'end'}`.
- Test: `…::test_a_numeric_format_writes_the_stored_value[…]` — `zlabel(, format(%9.1fc))`: `15,000.0 … 15,400.0`.
- Test: `…::test_format_reaches_the_binned_labels[…]` — `colorlevels(3) zlabel(, format(%td))`: `['02jan2001–03may2001', '03may2001–01sep2001', '01sep2001–31dec2001']`; no note.
- Test: `…::test_format_reaches_a_discrete_key_silently[…]` — `colordiscrete zlabel(, format(%9.2f))` on `_PRICE[:5]`: labels `3291.00 4099.00 4749.00 5079.00 5788.00`; no `zlabel` note.
- Test: `…::test_zscale_range_is_read_in_stata_units[…]` — `zscale(range(14600 15700))`: mapper `low == _ms(14600)`, `high == _ms(15700)`; ticks unchanged. Base: low unchanged (14600 taken as ms).
- Test: `…::test_an_unwritable_format_draws_g_and_is_named[…]` — `zlabel(, format(%21x))`: texts `15000 15100 15200 15300 15400`; exactly one note holding `format(%21x)`.
- Test: `…::TestANumberKeyIsInTwowaysCommaFormat::test_a_g_formatted_variable_keys_with_commas[…]` — `_PRICE` `%9.0g`, `colorcuts(5000 9000)`: `['≤5,000', '5,000–9,000', '>9,000']`. Base: `≤5000`.
- Test: `…::test_the_bar_ticks_a_number_at_twoways_numbers[…]` — `_PRICE` continuous: ticks `[0, 5000, 10000, 15000]`, texts `0 5,000 10,000 15,000`.
- Test: `…::test_a_discrete_number_key_uses_commas[…]` — `_PRICE[:5]` (`%9.0g`) `colordiscrete`: labels `3,291 4,099 4,749 5,079 5,788`. Base: `3291 4099 …`.
- Test: `…::TestFallbackTooltipsUseDisplayFormats::test_a_date_histograms_bins_are_dates[…]` — `histogram date` on `_KEY`: tooltips `[('date', '@{left}{custom} to @{right}{custom}'), ('Density', '@{top}')]`; formatter args `{'fmt': '%td', 'kind': 'td', 'storage': ''}`; `js_texts(f, [_ms(14977)], "value") == ['02jan2001']`.
- Test: `…::test_a_formatted_histograms_bins_have_commas[…]` — a `%12.0fc` variable `big`: args `fmt '%12.0fc'`, kind `''`; `js_texts(f, [1250000.0], "value") == ['1,250,000']`.
- Test: `…::test_a_fit_on_a_date_axis_writes_dates[…]` — `lfit lo date`: x row `('date', '@{x}{custom}')` with kind `td`; `lo` with no format keeps `@{y}{0.00}`.
- Test: `…::test_a_kdensity_names_its_variable_and_density[…]` — `kdensity date`: `[('date', '@{x}{custom}'), ('Density', '@{y}{…}')]`. Base: `('x', …), ('y', …)`.
- Test: `…::test_the_tooltips_survive_a_filter_move[…]` — histogram date with `_filter("range", "lo")`. Saved: JsSession move, then the quad source's new `left[0]` through `js_texts` gives `_dash_fmt_text(_dash_stata_value_of(left0, "td"), "%td")`. Served: `_fire` the RangeSlider, the same check on the live source. Tooltips and formatter args are equal before and after.
- Test: `…::test_a_variable_with_no_format_keeps_todays_precision` — guard (green at base): no `formats`, `univar="price"` gives `@{left}{0.0}` (as `test_function_audit.py:717-727`).
- Test: `…::TestHistogramTooltipNamesItsMeasure::test_the_height_row_is_the_y_titles_word[density|frequency|fraction|percent-saved|served]` — row 2's label is `Density`/`Frequency`/`Fraction`/`Percent`. Base: `Count`.
- Test: `…::test_an_untagged_quad_is_density` — a hand-built `fig.quad` with no tag gives `Density`.
- Test: `…::test_an_emptied_histogram_is_tagged_too` — `histogram date if lo > 99` (no row) still carries `dash_hist_density`.
- Test: `…::TestTheKeyHelpers::test_the_key_format_rule` — `{}` gives `('%8.0gc', None)`; `', format(%td)'` gives `('%td', None)`; `', format("%9.2f")'` gives `('%9.2f', None)`; `', format(%21x)'` gives `('%9.0g', '%21x')`; `', format(%12s)'` gives `('%9.0g', '%12s')`; a 200-character format is cut at 60.
- Test: `…::test_key_ticks_positions_and_text` — `td`: positions are `_ms`, texts `%8.0gc`; `""`: positions are the values; a label keyed `'15000.0'` wins; a tick at 3000000 days (past 9999) is dropped.
- Test: `…::test_the_measure_word_reads_the_tag` — each of the four tags; an unknown tag `dash_hist_bogus` gives `Density`.
- Test: `…::test_the_fallback_format_rule` — date on its axis gives kind `td`; date on a numeric axis (`axis_kind=None`) gives kind `""`, fmt `%td`; `%12.0fc` gives kind `""`; a `%9s` string format or an unknown variable gives None; a name with `}` gives None.
- Test: `…::TestTheKeyTextTruth::test_the_fixture_is_stamped` — `_meta` holds `stata_version`, `born_date`, `dash_commit`, `extracted`.
- Test: `…::test_the_key_format_is_eight_wide_comma_general` — for every `display` record, `_dash_fmt_text(v, "%8.0gc")` equals the `%8.0gc` text stripped. `%7.0gc` of 15000 has no comma and `%9.0gc` of 123456.25 has one, so neither is the key's format (E2).
- Test: `…::test_every_probe_keys_as_twoway[<probe>-saved|served]` — over every `k_*` probe whose kind is a bar, bins or labels: dash's key texts, built from the probe's `data` and options, equal `key_texts`. For bins the inner bounds are compared, and for the date-plus-%tm probe the overrides.
- Test: `…::test_the_histogram_measures_are_twoways_titles` — `h_*` `ytitle` equals `_DASH_HIST_YTITLES[m]`.
- Test: `…::test_twoway_refuses_what_dash_refuses` — `f_bogus`, `f_92x`, `f_tdbogus`: rc 198 and `err` is `invalid format, <f>`; `f_12s`, `f_21x`: rc 0.
- Test: `…::TestANonKeyFigureIsUnchanged::test_a_plain_scatter_builds_the_same_models` — guard (green before and after). `scatter lo hi` and `scatter lo hi, yaxis(2)` on `_KEY`, no colorvar, saved and served: the JSON of the document with ids removed is equal to a frozen copy taken in 17-01 at the base. Never re-baselined.
- Test: `test/test_key_text_chrome.py::TestTheKeyTextReachesThePage::test_the_page_maps_each_tick_to_its_text` (new file; module-level skip when `responsive_probe.find_chrome()` is None, as `test_by_scales_chrome.py` does; a skip is not a pass). It builds the saved `colorvar(date)` page on `_KEY` and opens it with `range_probe.RangeProbe`. `_eval` finds the ColorBar model in `Bokeh.documents[0].all_models` (by `m.constructor.__name__ == "ColorBar"`) and returns `cb.ticker.ticks.map(t => cb.major_label_overrides.get(t))`, which must equal `['15,000', …, '15,400']`. There must be no `js_errors()`. At the base the ticker is `auto`, so the read fails.

### Refusal cases (cscript)

None in S17: the `zlabel()` refusal cases are S18's AF-14..AF-18 (TR-17.9).

### Flips (in place; R9; red at base after the flip)

The twelve nodes of E8, each with a trailing comment `# WP-30 P1.23b: <reason>` and one `Flipped:` line in `<scratch>/s17/17-flips.txt`:
- `test_date_range.py::TestADateColorvarUnderALayersIf::test_colorlevels_cut_the_layers_dates[saved|served]` — "bounds in epoch milliseconds were wrong because twoway cuts and writes a date key in its Stata days (15,098 15,219)".
- `test_server_layer_defects.py::TestTheHoverBuilder::test_a_histogram_gets_the_bin_tooltip` — "'Count' was wrong because a histogram's height is the measure its y axis is titled with; an untagged bar is Density, twoway's default".
- `test_colorvar_forms.py::TestZOptions::test_zlabel_ticks_the_colour_bar` — "zlabel(#3) as Bokeh's BasicTicker was wrong because twoway places #N key ticks by its natscale rule (15,000 15,200 15,400 for sp500's dates)". Only the `#3` part changes. The list and `none` parts stay.
- `test_colorvar_forms.py::TestZOptions::test_an_unknown_z_sub_option_is_named` — "naming format(%9.2f) was wrong because twoway writes the key in it (0.00 5000.00 …)". The `orientation()` and `alt` parts stay.
- `test_colorvar_truth.py::TestTheKeyIsDrawnFromTheLayersRows::test_colorlevels_cuts_of_a_layers_own_if[saved|served]` — "a bound read from a :g label was wrong because the key is twoway's %8.0gc, 6,828.7 and 9,909.3, which the fixture's key_texts hold".
- `test_function_audit.py::TestColorCutsPutEachPointInItsLabelledBin` (3 nodes) — "2000 was wrong because twoway writes key numbers in %8.0gc whatever the variable's format (2,000)".
- `test_unlabelled_variables.py::TestBothModesNameAnUnlabelledVariable::test_a_computed_layer_never_names_an_unrelated_variable[saved|served]` — "kdensity z's rows x and y were wrong because they are z's values and its density; the rule that no unrelated variable is named still holds".

### Mutation checks (each must turn the named test red; 17-13)

| Mutation | Test |
|---|---|
| `_num_text` back to the variable's own format | `TestANumberKeyIsInTwowaysCommaFormat::test_a_g_formatted_variable_keys_with_commas` |
| bins on `dom_vals` (ms) instead of `dom_units` | `TestADateColourKeyIsInStataUnits::test_colorcuts_are_read_in_stata_units` |
| `_dash_key_ticks` returns the units as positions | `TestADateColourKeyIsInStataUnits::test_the_bar_ticks_a_date_at_twoways_numbers` |
| `_dash_axis_count_ticks(…, kind)` instead of `None` in TR-17.3 | `TestZlabelOnAColourKey::test_count_ticks_are_twoways` |
| `_dash_hist_measure` returns `"Count"` | `TestHistogramTooltipNamesItsMeasure::test_the_height_row_is_the_y_titles_word` |
| no tag in `map_histogram` | `test_the_height_row_is_the_y_titles_word[frequency-served]` |
| `_dash_fallback_format` ignores `axis_kind` | `TestTheKeyHelpers::test_the_fallback_format_rule` |
| `_dash_key_format` dropped from the copy list | every `[served]` key test (NameError) and `TestTheServedAppCarriesEveryName` |

## Test plan

| What | How | Fixture | Both modes / move? |
|---|---|---|---|
| Date key: bar, bins, cuts, discrete, minmax, periods, `%tc` | pytest `TestADateColourKeyIsInStataUnits` | `key_text_truth.json` (`k_date*`, `k_tm`, `k_tc`) | both; after a saved and a served move |
| `zlabel()` and `zscale()` on a key | pytest `TestZlabelOnAColourKey` | `k_date_td`, `_n3`, `_minmax`, `_lbl`, `_f91`, `_lev_td`, `_zrange` | both |
| Numeric key text and bar ticks | pytest `TestANumberKeyIsInTwowaysCommaFormat` | `k_price_*`, `k_big`, `k_tiny`, `k_mid`, `k_six`, `display` | both |
| Computed tooltips' formats | pytest `TestFallbackTooltipsUseDisplayFormats`; node via `js_texts` | — (Stata `display %td 14977`) | both; after a move |
| Histogram measure | pytest `TestHistogramTooltipNamesItsMeasure` | `h_*` | both |
| Helpers | pytest `TestTheKeyHelpers` | — | n/a |
| Every probe as twoway | pytest `TestTheKeyTextTruth` | the whole fixture | both |
| The page draws the override texts | Chrome `test_key_text_chrome.py` | — | saved (served shares the model) |
| Live twoway vs dash | cscript `test_wp30_truth.cscript` DK-01..DK-09, `WP30_ONLY=S17` | live Stata | saved and served, after a move |
| Parity | pytest `test_mode_parity.py` (3 CORPUS and 1 MOVE_CORPUS cases) | — | both, before and after a move |
| Guards | `TestANonKeyFigureIsUnchanged`; the two ms-range tests of E8 | frozen copy | both |
| Registries | `test_function_test_map.py`, `test_program_coverage_map.py`, `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads`, `test_cscript_hygiene.py`, `test_tracking_documents.py` | — | — |

**Acceptance criteria.**
- **AC-17.1** `dash scatter close open, colorvar(date)` on sp500 keys `15,000|15,100|15,200|15,300|15,400` in both modes, equal to twoway (DK-01, `TestTheKeyTextTruth`).
- **AC-17.2** `colorlevels(3)` and `colorcuts(15100 15200)` on a date give twoway's bounds, with every row in twoway's bin (DK-02, DK-03, `TestADateColourKeyIsInStataUnits`).
- **AC-17.3** `zlabel(, format(%td))`, `zlabel(#3)`, `zlabel(minmax)`, a labelled list, `format(%9.1fc)` and `zscale(range())` match twoway, and none prints a note (DK-04, `TestZlabelOnAColourKey`).
- **AC-17.4** Every numeric key is written `%8.0gc` (`price` at `%9.0g`: `5,000`), and the bar is ticked `0|5,000|10,000|15,000` (DK-06).
- **AC-17.5** `zlabel(, format(%12s))` and `format(%21x)` draw `%9.0g` and are named once (`test_an_unwritable_format_draws_g_and_is_named`). The refusal of `format(bogus|%9.2x|%tdbogus)` is S18's (AC-18.5).
- **AC-17.6** A date histogram, fit or kdensity tooltip writes `02jan2001`. A `%12.0fc` histogram writes `1,250,000`. A kdensity's rows are its variable and `Density`.
- **AC-17.7** The histogram's height row is `Density`, `Frequency`, `Fraction` or `Percent` (DK-08).
- **AC-17.8** All of the above are identical in the saved page and the served app, before and after a filter move (DK-07, the `…after_a_filter_move` tests, G3).
- **AC-17.9** The 12 flips carry their reasons. The guards and every registry are green, the full suite is green once, and BUGS.md, `WP30_OPEN` and the CHANGELOG are closed in place (G5).

## Tasks

**Commit boundary.** Tasks 17-01 to 17-14 form the one P1.23b commit. Its subject is `Write colour keys and computed tooltips in Stata's units and formats (WP-30 P1.23b)`. Task 17-14 makes it on `wp30-s17` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s17`, after one full run through the queue.
- The body opens with `<scratch>/17-P1.23b-failure.txt`, then gives the measured defect (E1) and what changed where (TR-17.1-17.9).
- It then carries one line each of:
  - `Regression: test/test_date_axis_residuals.py::<Class>::<test> -- failed at <batch-6 base sha> with <text>` (and the `test_key_text_chrome.py` node);
  - `Flipped: <node> -- <old expectation> was wrong because <why>` (twelve, from `<scratch>/s17/17-flips.txt`);
  - `Fixture: test/fixtures/key_text_truth.json (scripts/extract_key_text_truth.do)`;
  - `BUGS.md: "A date colour key shows epoch milliseconds, fallback tooltips ignore display formats, and the histogram tooltip always says Count" (closed)`.

Every command runs from `$WT`. `<scratch>` is the WP-30 scratch directory the orchestrator hands over, and `$S7=<scratch>/s17`. No body, BUGS, CHANGELOG or help line names a tool or vendor (G7).

<task type="auto" id="17-01">
  <name>Write the failing key and tooltip tests</name>
  <files>test/test_date_axis_residuals.py, test/test_key_text_chrome.py</files>
  <action><![CDATA[
    First check the cut and the inputs:
    - `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-6-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s17`;
    - run `mkdir -p $S7`;
    - `<scratch>/batch-6-impact.txt` holds the E6 rows. If a row is missing, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout (plus the grep for UNKNOWN) and append it.

    Create `test/test_date_axis_residuals.py` with the module docstring, imports, constants, data and helpers of "TDD test stubs", and every class and test listed there except `TestTheKeyTextTruth` (17-03).

    For `TestANonKeyFigureIsUnchanged`, compute at the base the sha256 of each of its two documents' JSON with every `id` removed (saved and served). Write the digests into the test as constants, with a comment saying they were taken at the batch-6 base and are never re-baselined.

    Create `test/test_key_text_chrome.py` with its one class.

    Run `python3 -m pytest test/test_date_axis_residuals.py test/test_key_text_chrome.py -q -n0 -p no:cacheprovider -rf > $S7/17-01.log 2>&1`. Write `<scratch>/17-P1.23b-failure.txt` with:
    - the base sha;
    - each failing node with its one-line reason;
    - a separate list of the two guards that passed: `test_a_variable_with_no_format_keeps_todays_precision` and `TestANonKeyFigureIsUnchanged::test_a_plain_scatter_builds_the_same_models`.

    The `TestTheKeyHelpers` tests fail with `AttributeError`, because the helpers do not exist yet. Do not commit, and do not weaken a test to make it pass.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' $S7/17-01.log` is at least 40; `grep -c "auto\|Count\|9.78394e+11\|_dash_key_format" $S7/17-01.log` is at least 4; `tail -1 $S7/17-01.log` reports exactly 2 passed; `test -s <scratch>/17-P1.23b-failure.txt`; `git -C $WT status --porcelain` shows only the two new files.]]></verify>
  <done>Every pytest regression test of the section existed and was shown failing on the unmodified tree, the guards passed, and the failure text was saved.</done>
</task>

<task type="auto" id="17-02">
  <name>Extract twoway's key text truth</name>
  <files>scripts/extract_key_text_truth.do, test/fixtures/key_text_truth.json</files>
  <action><![CDATA[
    Create `scripts/extract_key_text_truth.do` as "Stata truth" describes:
    - the S02 root form (copy the root block of an S02-converted extractor verbatim, renaming its globals to `KT_*`);
    - `adopath ++` then `global dash_nobrowser 1`;
    - the python gate;
    - every probe in the order listed;
    - the `display` records;
    - the python block, which uses `scripts/svg_truth.py`'s `svg_texts` and `svg_plotregion` the way `scripts/extract_colorvar_qualifier_truth.do`'s block does (from :178), and writes the fixture with sorted keys and `_meta`.

    Run `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh $S7 $WT/scripts/extract_key_text_truth.do`. Check the probes against E2 by eye: every texts list must equal the E2 table. Stage nothing yet. The fixture is added with `git add -f` in 17-14.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/key_text_truth.json'));p=d['probes'];print(sorted(d['_meta'])[:4], p['k_date']['key_texts'], p['k_date_lev3']['key_texts'], p['k_price_g']['key_texts'], p['f_bogus']['rc'], p['f_bogus']['err'], p['h_percent']['ytitle'], d['display']['15000']['%8.0gc'].strip())"` prints `['born_date', 'dash_commit', 'extracted', 'script']`, `['15,000', '15,100', '15,200', '15,300', '15,400']`, `['15,098', '15,219']`, `['0', '5,000', '10,000', '15,000']`, `198`, `invalid format, bogus`, `Percent`, `15,000`; the log ends with no `r(` error.]]></verify>
  <done>twoway's colour-key texts, refusals, histogram titles and display records were extracted from Stata 19.5 into a stamped fixture.</done>
</task>

<task type="auto" id="17-03">
  <name>Add the fixture-driven truth tests</name>
  <files>test/test_date_axis_residuals.py</files>
  <action><![CDATA[
    Add `TestTheKeyTextTruth` with the five tests of "TDD test stubs". Load `test/fixtures/key_text_truth.json` by name, and fail rather than skip when the file is absent.

    `test_every_probe_keys_as_twoway` is parametrized over the `k_*` probes whose texts dash's key form can show:
    - every bar probe;
    - the bins probes (`k_date_lev3`, `k_date_cuts`, `k_date_lev_td`, `k_price_cuts`, `k_price_lev3`) compared on inner bounds;
    - `k_date_lbl` on overrides.

    The discrete probe is omitted because twoway draws a ramp there (Boundaries). Each case is crossed with `MODES`. It rebuilds the probe's frame from `data` with the probe's options and format, and compares dash's texts with `key_texts`.

    Run the class on the unmodified renderer and append its failing nodes to `<scratch>/17-P1.23b-failure.txt` under `Fixture-driven`. `test_the_fixture_is_stamped`, `test_the_key_format_is_eight_wide_comma_general`, `test_the_histogram_measures_are_twoways_titles` and `test_twoway_refuses_what_dash_refuses` pass at base: list them as guards.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k TestTheKeyTextTruth -rf 2>&1 | tail -1` reports at least 30 failed and exactly 4 passed.]]></verify>
  <done>Every twoway probe was compared with dash's key in both modes, failing on the unmodified tree except the four fixture guards.</done>
</task>

<task type="auto" id="17-04">
  <name>Fill the S17 truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Add `_s17_svg`, `_s17_page` and `_s17_app` (python, as the "Stata truth" helper table says) directly above `* ==== S17 P1.23b: Date and format text in keys and tooltips ====`. Write cases DK-01..DK-09 of the truth table between S17's own start and end display lines. Every file goes under `` `w30_work' `` and is erased before the end line. Drop graphs with `graph drop`. Add the header list line `S17  P1.23b colour-key text and computed tooltips against twoway (DK-01..DK-09)`.

    Do not touch another block, the marker line or the summary. Write the driver:

    printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > $S7/run_test_wp30_truth.do

    Run `WP30_ONLY=S17 scripts/stata_slot.sh $S7 $S7/run_test_wp30_truth.do`. Append the DK FAIL lines to the failure file under `Truth block`.
  ]]></action>
  <verify><![CDATA[`grep -c 'DK-0[1-9] FAIL' $S7/run_test_wp30_truth.log` is at least 7 (DK-01..DK-06 and DK-08 fail at base); `grep -c 'S17 start\|S17 end' $S7/run_test_wp30_truth.log` prints 2; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider -k Wp30` passes.]]></verify>
  <done>The live twoway comparison of the colour key and the computed tooltips existed in S17's own block and failed on the unmodified tree.</done>
</task>

<task type="auto" id="17-05">
  <name>Add the key and hover helpers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `_dash_key_format`, `_dash_key_ticks`, `_dash_hist_measure` and `_dash_fallback_format` (TR-17.1) after `_dash_colorvar_bins` (before the `# GlyphMapper` banner, :7875). Each has a docstring citing WP-30 P1.23b and the measurement.

    Add the copy-list line of TR-17.7 after `"_dash_colorvar_domain", "_dash_colorvar_field",` (:33368).

    Add the five `FUNCTIONS` entries of TR-17.8 under S17's anchor, alphabetical. The `_layer_of` entry's test exists from 17-01.

    Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k TestTheKeyHelpers` and the two served-name guards.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_axis_residuals.py -k "test_the_key_format_rule or test_key_ticks_positions_and_text or test_the_measure_word_reads_the_tag or test_the_fallback_format_rule" "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" -q -n0 -p no:cacheprovider` passes; `test_function_test_map.py` fails only on `_layer_of` (not yet defined).]]></verify>
  <done>The four module helpers existed with unit tests green, reached the served app through S17's anchor, and were mapped.</done>
</task>

<task type="auto" id="17-06">
  <name>Write colorvar keys in Stata units</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-17.2's four edits in `GlyphMapper._apply_colorvar`, each with a comment citing WP-30 P1.23b:
    1. the number-text block (:8980-8989);
    2. `col_units`/`dom_units` after `dom_all_missing` (:9064);
    3. the bins and colordiscrete levels in those units (:9095-9128);
    4. the default bar ticks (:9250-9259). The `_dash_apply_z_options` call (:9260-9262) keeps its arguments until 17-07 extends the signature and the call together.

    Do not edit the colour, alpha, palette or Legend lines (S16, S24, S30). Edit `_dash_colorvar_bins`'s docstring per TR-17.4.

    Before editing, warn in `$S7/17-notes.txt` that `_dash_colorvar_bins` is HIGH (E6, docstring only). Run `python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "TestADateColourKeyIsInStataUnits or TestANumberKeyIsInTwowaysCommaFormat"`.
  ]]></action>
  <verify><![CDATA[That run passes, both modes, including `test_the_key_is_unchanged_after_a_filter_move`; `python3 -m pytest test/test_colorvar_forms.py test/test_colorvar_legend.py -q -n0 -p no:cacheprovider` fails only in the E8 nodes of test_colorvar_forms.py.]]></verify>
  <done>A colour key's bins, levels, cuts and bar ticks were computed and written in the variable's Stata units in twoway's %8.0gc, in both modes.</done>
</task>

<task type="auto" id="17-07">
  <name>Read zlabel and zscale in key units</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-17.3 to `_dash_apply_z_options` (:26106-26217), after recording in `$S7/17-notes.txt` that it is HIGH (E6):
    - the signature;
    - the named list;
    - the four `zlabel()` modes through `_dash_key_ticks` with `_dash_axis_count_ticks(lo, hi, n, None)`;
    - the discrete key's format-only silence;
    - `zscale(range())` in Stata units;
    - removing the now-unused `_dash_count_ticker` use here.

    In the same task, extend `_apply_colorvar`'s continuous call (:9260-9262) with `kind=_cv_kind, units=_units`, where `_units` is `(_lo_s, _hi_s)` from 17-06 or None. The discrete call (:9222) is unchanged. The docstring gains a paragraph on units and text.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_axis_residuals.py -q -n0 -p no:cacheprovider -k "TestZlabelOnAColourKey or TestADateColourKeyIsInStataUnits or TestANumberKeyIsInTwowaysCommaFormat or TestTheKeyTextTruth"` passes; `python3 -m pytest test/test_colorvar_forms.py -q -n0 -p no:cacheprovider -k test_a_z_option_on_a_discrete_key_is_named_once` passes.]]></verify>
  <done>zlabel() ticks, labels and format(), and zscale(range()), were read in the colour variable's units on both keys, with only unwritable formats named.</done>
</task>

<task type="auto" id="17-08">
  <name>Format the computed layers' tooltips</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-17.5 to `GlyphMapper.map_histogram` (the tag on all three returned renderers; `_histogram_quads` untouched).

    Apply TR-17.6 to `_dash_build_hover`'s fallback (:27329-27426):
    - `_layer_of`;
    - `_cell`'s two new parameters and `_fb_fmts`;
    - the per-shape variables;
    - `_dash_hist_measure`;
    - the tool built with `formatters=dict(_fb_fmts)`.

    The comprehensive path above :27329 is not edited. Check the `_layer_of` map entry now resolves.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_axis_residuals.py test/test_function_test_map.py -q -n0 -p no:cacheprovider -k "TestFallbackTooltipsUseDisplayFormats or TestHistogramTooltipNamesItsMeasure or function_test_map"` passes; `python3 -m pytest test/test_function_audit.py -q -n0 -p no:cacheprovider -k "Tooltip or Band or Range"` passes.]]></verify>
  <done>Histogram, fit and density tooltips wrote their variables' display formats, kdensity named its variable and Density, and the histogram named its measure, in both modes.</done>
</task>

<task type="auto" id="17-09">
  <name>Flip the colour key pins</name>
  <files>test/test_colorvar_forms.py, test/test_colorvar_truth.py, test/test_date_range.py</files>
  <action><![CDATA[
    Flip, in place and keeping every node's name:
    - `TestZOptions::test_zlabel_ticks_the_colour_bar`'s `#3` part (to `FixedTicker` `[5000.0, 10000.0, 15000.0]` and overrides `5,000 10,000 15,000`);
    - `TestZOptions::test_an_unknown_z_sub_option_is_named`'s third part (format(%9.2f) is not named, and the bar's overrides read `%9.2f`);
    - `TestTheKeyIsDrawnFromTheLayersRows::test_colorlevels_cuts_of_a_layers_own_if` (`b[1:3] == [6828.7, 9909.3]` and the outer bounds unchanged);
    - `TestADateColorvarUnderALayersIf::test_colorlevels_cut_the_layers_dates` (bounds `_SPREAD[6] + k*(_SPREAD[11]-_SPREAD[6])/3` within 0.5 day, written `%8.0gc`; update its comment "The key writes a date's milliseconds with :g").

    Each flip gets the trailing comment `# WP-30 P1.23b: <reason>` and one `Flipped:` line in `$S7/17-flips.txt` with the E8 reason. Add the one docstring sentence to the class docstring of `TestADateColorvarUnderALayersIf` ("in epoch milliseconds" becomes "its mapper in epoch milliseconds, its text in Stata days").
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_colorvar_forms.py test/test_colorvar_truth.py test/test_date_range.py -q -n 4 -p no:cacheprovider` passes; `grep -c '^Flipped:' $S7/17-flips.txt` is at least 6.]]></verify>
  <done>The six colour-key pins asserted twoway's units and text, kept their names, and recorded why.</done>
</task>

<task type="auto" id="17-10">
  <name>Flip the tooltip and bin-label pins</name>
  <files>test/test_server_layer_defects.py, test/test_function_audit.py, test/test_unlabelled_variables.py</files>
  <action><![CDATA[
    Flip, in place, with the E8 reasons:
    - `TestTheHoverBuilder::test_a_histogram_gets_the_bin_tooltip` (`"Density"`);
    - the three `TestColorCutsPutEachPointInItsLabelledBin` nodes (`≤2,000`, `2,000–3,000`, `>3,000`);
    - the kdensity half of `TestBothModesNameAnUnlabelledVariable::test_a_computed_layer_never_names_an_unrelated_variable` (`[["z", "Density"]]`).

    Each flip gets the `# WP-30 P1.23b:` comment and a `Flipped:` line in `$S7/17-flips.txt`. In `test/test_display_format_sites.py`, add no change: `TestColorvarLabels` stays green, and its rule is now stated in the help.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_server_layer_defects.py test/test_function_audit.py test/test_unlabelled_variables.py test/test_display_format_sites.py -q -n 4 -p no:cacheprovider` passes; `grep -c '^Flipped:' $S7/17-flips.txt` is at least 12.]]></verify>
  <done>The tooltip and bin-label pins asserted twoway's words and format, with every flip recorded.</done>
</task>

<task type="auto" id="17-11">
  <name>Append the parity corpus cases</name>
  <files>test/test_mode_parity.py</files>
  <action><![CDATA[
    At the end of `CORPUS`, under the comment `# WP-30 P1.23b: colour-key text and computed tooltips`, append:
    - `_case("colorvar() colorcuts() keyed %8.0gc", [_sc(colorvar="price", colorcuts="5000 9000")])`;
    - `_case("colorvar() zlabel(, format(%9.2f))", [_sc(colorvar="price")], go={"zlabel": ", format(%9.2f)"})`;
    - `_case("histogram, frequency tooltip", [plot_for("histogram", {"frequency": "frequency"})])`.

    At the end of `MOVE_CORPUS` append `_move_case("colorvar() colorlevels(), dropdown", _MOVES[0], [_sc(colorvar="price", colorlevels="3")])`. Do not edit `ALLOWED` or `_MUST_WARN` (R8).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py -q -n 4 -p no:cacheprovider -k "colorcuts or zlabel or frequency or colorlevels"` passes with at least 4 selected.]]></verify>
  <done>The parity corpus drew the new key text and tooltip identically in both modes, before and after a move.</done>
</task>

<task type="auto" id="17-12">
  <name>Update the help for keys and tooltips</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Rewrite dash.sthlp:3156-3162 (Mapping a Variable to Colour) to this text, keeping SMCL:

    "{pstd}
    The colour key's own axis options, {cmd:ztitle()}, {cmd:zlabel()} and {cmd:zscale()}, are taken as graph options and drawn on the key: the title on either key; ticks, {cmd:#}{it:N}, {cmd:none} and {cmd:minmax}, and {cmd:range()} (widening only), {cmd:log} and {cmd:reverse}, on the colour bar. The key's numbers are {it:varname}'s values in its own units, written as {cmd:twoway} writes its colour key: in {cmd:%8.0gc} whatever {it:varname}'s display format ({cmd:5,000} for a {cmd:%9.0g} {cmd:price}), or in {cmd:zlabel(, format())}'s format -- on the colour bar, in a binned key's bounds and in a discrete key's levels. The colour bar is ticked where {cmd:twoway} ticks its key, by the rule of {cmd:#5} over the plotted values, and {cmd:#}{it:N}, {cmd:minmax}, a list of values, {cmd:colorcuts()}, {cmd:colorlevels()} and {cmd:range()} are read in the same units. So a date variable keys {cmd:15,000} ... {cmd:15,400} and {cmd:colorcuts(15100 15200)} cuts at those days, as in {cmd:twoway}; {cmd:zlabel(, format(%td))} writes the dates. A format {cmd:twoway} accepts that {cmd:dash} cannot write ({cmd:%12s}, {cmd:%21x}) is drawn as {cmd:%9.0g} and named in the note. On a discrete key {cmd:zlabel()}'s ticks and {cmd:zscale()} are named in the note. {cmd:ztitle()} given only sub-options styles the key's default title, the colour variable's label; {cmd:suffix} and {cmd:prefix} add lines to it."

    Make the Tooltips edits of TR-17.12 (:3057-3062) and the `zlab:el()` synopt (:2753). Edit no other paragraph (R3).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_help_claims_7.py test/test_help_claims_8.py -q -n 4 -p no:cacheprovider` passes; `grep -c '%8.0gc' dash.sthlp` is one more than at base; `grep -c "histogram's bin and count" dash.sthlp` prints 0.]]></verify>
  <done>The help stated the colour key's units, text, ticks and format() rule, and the computed tooltips' formats and measure words.</done>
</task>

<task type="auto" id="17-13">
  <name>Certify the section before commit</name>
  <files>none</files>
  <action><![CDATA[
    1. Run every changed pytest file and the registries, writing to `$S7/17-13.log`: `python3 -m pytest test/test_date_axis_residuals.py test/test_key_text_chrome.py test/test_colorvar_forms.py test/test_colorvar_truth.py test/test_colorvar_legend.py test/test_date_range.py test/test_server_layer_defects.py test/test_function_audit.py test/test_unlabelled_variables.py test/test_display_format_sites.py test/test_mode_parity.py test/test_function_test_map.py test/test_program_coverage_map.py test/test_cscript_hygiene.py test/test_tracking_documents.py test/test_fixtures_are_committed.py test/test_label_sinks.py "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n 6 -p no:cacheprovider`.
    2. Run the truth-script driver with `WP30_ONLY=S17`.
    3. Apply each mutation of "Mutation checks" by hand in turn. Run its named test, see it fail, and restore the file. `git -C $WT diff --stat` must be the same before and after.
    4. Run `git -C $WT merge --no-edit main`, expecting `Already up to date.` (E9).
    5. Launch `<scratch>/full_suite_queue.sh $WT $S7/17-full-1.log` in the background and wait for its `exit=` line with an until-loop (E1, E6).
  ]]></action>
  <verify><![CDATA[`tail -1 $S7/17-13.log` reports 0 failed; `grep -c 'DK-0[1-9] PASS' $S7/run_test_wp30_truth.log` prints 9 and the block ends `ALL CHECKS PASSED`; each mutation turned its test red (recorded in `$S7/17-mutations.txt`); `grep '^exit=' $S7/17-full-1.log` prints `exit=0` with 0 failed.]]></verify>
  <done>The section's tests, both cscripts, the registries, the mutation checks and one full suite passed on the worktree.</done>
</task>

<task type="auto" id="17-14">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    1. **BUGS.md.** Close the entry titled `WP30_OPEN["P1.23b"]` in place: `- [x]`, and the Resolution of Notes "BUGS.md Resolution", naming every test by node id.
    2. **`WP30_OPEN`.** Delete the `"P1.23b"` key line.
    3. **`WP30_LISTS`.** Unchanged (`("Results that change",)`): S17 refuses nothing (TR-17.9).
    4. **CHANGELOG.md.** Replace the `<!-- WP-30 P1.23b -->` marker in the Results group in place with Notes' three Results lines. Each line ends `(WP-30, P1.23b)`.
    5. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.
    6. `git add -f test/fixtures/key_text_truth.json`. Stage exactly: dash_render.py, dash.sthlp, BUGS.md, CHANGELOG.md, scripts/extract_key_text_truth.do, test/fixtures/key_text_truth.json, test/test_date_axis_residuals.py, test/test_key_text_chrome.py, test/test_colorvar_forms.py, test/test_colorvar_truth.py, test/test_date_range.py, test/test_server_layer_defects.py, test/test_function_audit.py, test/test_unlabelled_variables.py, test/test_mode_parity.py, test/test_wp30_truth.cscript, test/function_test_map.py, test/test_tracking_documents.py.
    7. Check `git diff --cached --name-only` lists those 18 and no `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.ultraplan/` or `*.html` (G6).
    8. Write the message per the commit boundary to `$S7/17-msg.txt`. Run G7, confirm `git branch --show-current` prints `wp30-s17`, commit with `git commit -F $S7/17-msg.txt`, then run G7 on `git log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`grep -Eic 'claude|anthropic' $S7/17-msg.txt` and `git -C $WT log -1 --format=%B | grep -Eic 'claude|anthropic'` both print 0; `git -C $WT log -1 --format=%s` ends `(WP-30 P1.23b)`; `git -C $WT diff-tree --no-commit-id --name-only -r HEAD | wc -l` prints 18; `grep -c '<!-- WP-30 P1.23b -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.23b": "' test/test_tracking_documents.py` prints 0; `grep -c '(WP-30, P1.23b)' CHANGELOG.md` prints 3; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The P1.23b entry was closed with its tests named, its key deleted, its lists and CHANGELOG lines written in place, and the one commit made on wp30-s17.</done>
</task>

## Section completion criteria

- One commit on `wp30-s17`, subject ending `(WP-30 P1.23b)`, holding exactly the 18 files of 17-14. Its body has the failure text, the `Regression:`, 12 `Flipped:`, `Fixture:` and `BUGS.md:` lines, and passes G7.
- Every regression test of "TDD test stubs" failed at the batch-6 base (`<scratch>/17-P1.23b-failure.txt`) and passes now. The guards passed before and after.
- `test/fixtures/key_text_truth.json` carries the D12 `_meta` stamp, is tracked with `git add -f`, and is named by `test_date_axis_residuals.py`.
- DK-01..DK-09 print PASS under `WP30_ONLY=S17`. No new SKIP.
- G3 (parity), G4 (both served-name guards) and G5 (tracking) are green. One full suite through the queue is green.
- BUGS.md's P1.23b entry is `- [x]` with its Resolution. Its `WP30_OPEN` key is gone, its `WP30_LISTS` row is unchanged, and no `<!-- WP-30 P1.23b -->` marker remains.
- dash.sthlp states the key's units and format, the `format()` rule, and the computed tooltips' formats and measure words.

## Notes

**Traps for the executor.**
1. **`kind=None` for key ticks.** `_dash_axis_count_ticks(lo, hi, n, kind)` with a date kind takes the date-axis `_tsnatscale` rule. The colour key is twoway's plain number line (E2: `%tm` keys `490 495 500 505`), so pass `None` and convert positions with `_dash_key_ticks`.
2. **The mapper stays in milliseconds.** Only text, ticks, cuts and bins move to Stata units. The colour column's `transform` still maps the source's millisecond column. Do not "fix" `low`/`high`, because the E8 guards pin them.
3. **Overrides are keyed by the exact float position.** The ticker's tick list and the override keys must be the same Python floats, both from `_dash_key_ticks`. Do not round one of them.
4. **Copy lists.** A missing name fails only on the served page. Run `TestTheServedAppCarriesEveryName` after 17-05 and again in 17-13 (R2, RK-9).
5. **`_fb_fmts` must be cleared per shape attempt.** Otherwise a shape that did not hit leaves formatters for columns the final tool does not show.
6. **No Stata edit.** The `zlabel()` refusal is S18's (TR-17.9); do not touch dash.ado or `test_option_validation.*`.
7. **The python_exec hazard** (project memory). Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. Run the extractor and the drivers through `stata_slot.sh` only, and check the file after 17-02 and 17-13.
8. **Fixture exclude rule.** `.git/info/exclude:58` ignores `*.json`. Stage the fixture with `git add -f`.

**Merge rules for the shared files (batch 6: S16, S17, S18).**
- **R1.** `test_wp30_truth.cscript`: S17 writes only inside its own block and directly above its header. S17 adds no area-script case (its `zlabel()` refusal cases are S18's AF-14..AF-18).
- **R2.** One copy-list line at S17's anchor (33368). Five `FUNCTIONS` keys under S17's map anchor.
- **R3.** dash.sthlp: "Mapping a Variable to Colour" (S17's per the R3 table), plus the one Tooltips sentence (3057-3062) and the `zlab:el()` synopt (2753) under "Axis and Display Options". S18 edits that title's axis-format paragraphs and the log example, which are distinct paragraphs. S16 edits "Marker and Transparency Options".
- **R4.** CHANGELOG: S17 replaces only its one Results marker.
- **R5.** BUGS.md and `test_tracking_documents.py`: only P1.23b's entry and key line.
- **R6.** dash.ado: not edited by S17 (A139; S18 is batch 6's `_dash_option_rules`/`_dash_validate_value` editor and adds `zlabel=keyformat`).
- **R7.** New fixture and extractor, S17's own, never run by another section.
- **R8.** CORPUS and MOVE_CORPUS appends only.
- **R9.** The 12 flips of E8.
- **R10.** No combined pin moves. The single-y page digest (`test_varlist_expansion.py` `_SINGLE_Y_BASELINE_SHA256`) has no colorvar or computed layer and does not change. 17-13 confirms it.
- **R12.** None of the one-editor symbols is edited.

**Commit-body line forms** (BRIEF, with WP-30 deltas):
- `Regression: test/test_date_axis_residuals.py::TestADateColourKeyIsInStataUnits::test_the_bar_ticks_a_date_at_twoways_numbers[saved] -- failed at <sha> with <text>` (one per regression node);
- `Flipped: <node> -- <old> was wrong because <why>`;
- `Fixture: test/fixtures/key_text_truth.json (scripts/extract_key_text_truth.do)`;
- `BUGS.md: "A date colour key shows epoch milliseconds, fallback tooltips ignore display formats, and the histogram tooltip always says Count" (closed)`.

**BUGS.md Resolution** (17-14, in place; `<date>` is the commit's ddmonyyyy):
`- Resolution: Fixed <date> (WP-30, P1.23b). A colour key is read and written in its variable's Stata units in GlyphMapper._apply_colorvar and _dash_apply_z_options (new _dash_key_format, _dash_key_ticks): a date key's bar ticks, colorcuts()/colorlevels() bounds, colordiscrete levels, zlabel() ticks and zscale(range()) are Stata values written in twoway's %8.0gc or zlabel()'s format(), the bar is ticked at twoway's key ticks, and a zlabel() format twoway accepts that the page cannot write is drawn in %9.0g with one note; the tooltips of histograms, fits and densities write their variables' display formats (new _dash_fallback_format in _dash_build_hover) and a histogram's height row names its measure (map_histogram's tag, new _dash_hist_measure); identical in the saved page and the served app, before and after a filter move. Pinned by test/test_date_axis_residuals.py::TestADateColourKeyIsInStataUnits::test_the_bar_ticks_a_date_at_twoways_numbers, test/test_date_axis_residuals.py::TestZlabelOnAColourKey::test_format_td_writes_dates, test/test_date_axis_residuals.py::TestANumberKeyIsInTwowaysCommaFormat::test_a_g_formatted_variable_keys_with_commas, test/test_date_axis_residuals.py::TestFallbackTooltipsUseDisplayFormats::test_a_date_histograms_bins_are_dates, test/test_date_axis_residuals.py::TestHistogramTooltipNamesItsMeasure::test_the_height_row_is_the_y_titles_word, test/test_date_axis_residuals.py::TestTheKeyTextTruth::test_every_probe_keys_as_twoway, test/test_key_text_chrome.py::TestTheKeyTextReachesThePage::test_the_page_maps_each_tick_to_its_text, test/test_wp30_truth.cscript DK-01; fixture test/fixtures/key_text_truth.json.`

**CHANGELOG lines** (17-14). The old values are from the saved failure text.
- Results that change, in place of the marker:
  - `- dash scatter close open, colorvar(date): a date colour key's ticks, its colorcuts()/colorlevels() bounds, its colordiscrete levels and its zlabel() ticks are read and written in the variable's Stata units, as twoway writes them -- 15,000 ... 15,400, where dash wrote epoch milliseconds (9.78394e+11) -- and colorcuts(15100 15200) now cuts at those days instead of collapsing to the minimum; zlabel(, format(%td)) writes dates. (WP-30, P1.23b)`
  - `- Every numeric colour key is written in twoway's %8.0gc whatever the variable's display format (price at %9.0g keys ≤5,000, not ≤5000), and the colour bar is ticked at twoway's key ticks (0, 5,000, 10,000, 15,000) where Bokeh chose its own; zlabel(#N) places ticks by twoway's rule and zlabel(, format()) is honoured on every key. (WP-30, P1.23b)`
  - `- Tooltips of histogram, the fits and smooths and kdensity write values in the variable's display format (a date histogram's bins read 02jan2001, not 978393600000); a kdensity's rows are its variable and Density, not x and y; and a histogram's height row is named Density, Frequency, Fraction or Percent, as its y axis is titled, not Count. (WP-30, P1.23b)`

**Notes for the closeout** (A145). This text is for S58, which alone edits the tracking documents.
- **REMAINING.md.** The 08-05 bullets REMAINING.md:2195-2208 (colorvar) and :2231-2241 (fallback hover), ids REM-08-05-M1, REM-08-05-C7c, REM-08-05-C10 and REM-08-05-M2 (matched by content in S01's entry), are closed by P1.23b, commit `<sha>`. They are marked `[WP-30 P1.23b, commit <sha>: closed]` as WP-29 marked its bullets.
- **DROPIN-REMAINING.md P1.23.** The text part ("A date colorvar key shows ms. Fallback tooltips ignore formats. The histogram tooltip always says Count.") is closed by P1.23b, commit `<sha>`. The positions part is S35's.
- **Register P1.5.6.** The colour key's fixed format was measured to be `%8.0gc` (`%7.0gc` writes 15000 without a comma; `%9.0gc` writes 123,456 where the key writes 123456). It is closed in P1.23b, so no P2 is filed.
- **P2.45 (ROADMAP).** The fallback tooltips can add one 33 KB formatter model per distinct `(fmt, kind)` not already on the page. This is the same cost P2.45 already tracks.
- **Residuals.** These are candidate P2 rows for S58.3 to file or fold:
  - (a) A `zlabel()` given twice where only an earlier copy carries a refused `format()`. twoway validates every copy (E2: `zlabel(, format(bogus)) zlabel(, format(%9.2f))` is r(198)). dash validates the merged value. This folds into P2.21's sweep.
  - (b) A repeated `format()` inside one `zlabel()` (twoway: `option format() not allowed`, r(198)). Also P2.21.
  - (c) A horizontal histogram's tooltip names its bins on x. That belongs to S49/S55 when they land; otherwise it is a P2 row.
- **TWOWAY_COVERAGE_AUDIT.md.** The colour key's text (`zlabel(, format())`) moves from "named, not drawn" to "drawn as twoway".

**Open questions.** None. The coordination point with S18 is settled by the review (A139): S18 adds the `zlabel()` refusal to its own dash.ado edit (TR-18.13 (e), AF-14..AF-18) and its Changed behaviour line; S17 edits no Stata file.
