# Section 24: Scheme opacity, histogram style and symbols reach every layer (P1.4 part a)

> Part of: WP-30 · Items: P1.4 part a (entry `P1.4a`) · Risk: yellow · Batch: 8 · Depends on: 07, 16 · Blocks: 30, 32, 33, 45, 49 · Tasks: 19, 1 commit · Case prefix: SK

## Review amendments

- Fixed (major): the truth block's `_s24_dash` said only "builds … from the command's spec"; it now registers the command, writes the saved page and the served app with `dash build` (a `foreign` dropdown for SK-09's move) under `` `w30_work' ``, and reads both documents as S19's helpers do.
- Resolved Q1 (S15's directive-count pin) by index R10 without the maintainer: S15 moves the bound and the help's "80 to 140" in its own commit; S21 moves it only if red (F33); S24 re-measures and renames it. Cross-file fix filed for section-15 and R10.
- Fixed (minor): Boundaries now name S19's `legend_label="y"` on `map_scatteri` and S21's three scheme keys as earlier edits S24 keeps; the commit's BUGS line quotes Appendix B's title verbatim; the SK cases are stated to count no notes (S22's batch-8 note cannot move them).
- Checked: anchors E1-E5 (dash_render.py :5239-5302, :6527, :6797-6806, :6864, :7172, :8199-8252, :8448-8474, :8622/:8768-8791, :9727, :9976-9979, :10823-10837, :12423-12449, :12983-12986, :13993, :33446-33459) and the E9 nodes (test_help_claims_8.py :763/:1014, test_scheme_review_fixes.py :387/:394, test_html_output.py :1856, test_glyphs.py :3337, test_emptied_layer_style.py :107-115) match `c96facd`; S14's caps are `dash` Scatters tagged `dash_cap` as TR-24.4 assumes.
- Checked: M1 (every look change has a Results line), M5 (nothing refused), M6 (nothing printed), IR-4 (sm* factor after `msize()`, from the scheme and `msymbol()`), A152 (S24 regenerates last in batch 8) and R12 (`_apply_marker_opts` is S24's alone in batch 8; S23 edits no mapper or parser) hold; every new parser attribute is built in `_init_properties` from `_props`, so the served app and `fallback()` have it.
- Rejected: "D-24c's per-name factors contradict IR-4's 0.707" (M1 binds the measured table; IR-4's number is the circle's, which D-24c keeps).
- (cross-file pass) 24-19 verify: added the key-deletion check `grep -c '^    "P1.4a": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- (cross-file pass) TR-24.19 shipped-files change 1: the sentence it rewrites is S15's "<lo> to <hi> directives" (S15 15-18 now flips the pin and the sentence first), not "80 to 140".
- The review pass applied both lenses.
- Ratification row 4 (ratification 06oct2026, CHANGED: no unread-directive note): D-24f, "Why one section", Dependencies (S33), Boundaries (S33) and Notes "For later sections" (S33) no longer mention S33's unread-directive note, exempt list or read-recording; S33 retains every parsed directive and notes none (S33's D-33d).
- Ratification row 27 (ratification 06oct2026, "Fix in WP-30"): Boundaries' "P2.49 owns the nonselection and muted copies" now says they follow S08's brushed-copy sync (ratification row 27), which keeps dash's nonselection alpha; the Resolution's residual "the nonselection and muted copies of a marker are P2.49's" is removed and the Resolution says those copies are styled by P1.12a's brushed-copy sync (S08), not by P1.4a. P2.49 is not filed.

## Overview

**Binding readings applied in this file** (decisions.md M1, M5, M6; decision-register P1.4.2, P1.4.3, P1.4.5, P1.4.6, P1.4.7, X.1, X.5; index A138, A145, A148, A152, IR-4, IR-11, R2, R3, R7, R9, R10, R12):
- **M1, P1.4.2, P1.4.3.** Every histogram layer takes twoway's histogram style, and rarea takes area's opacity rule (opaque; 0.2 under `sttrans`). Both are announced under CHANGELOG "Results that change".
- **P1.4.5, P1.4.7 (A11).** The symbol cycle on five more types, the `p#mark` key fix (side h) and the `malpha()`-refills-hollow bug (side i) are folded in. Side h flips `TestMarkColourIsForMarkers`, the `p_mark_colors` chain and dash.sthlp:3363-3365, each with its reason.
- **P1.4.6, IR-4 (A12).** The `sm*` size factor applies to the scheme's p# symbols and to a user's `msymbol(sm*)`, after `msize()`, inside `_apply_marker_opts`. Only the lower-case shorthands (`o d s t x` and their hollow forms) stay with P2.11.
- **M5.** Nothing is newly refused. **M6.** Nothing new is printed: every change is drawn, silently.
- **A152, IR-11.** S24 is batch 8's only scheme regenerator. It lands last in the batch, after S22 and S23.
- **R12.** S24 is batch 8's only editor of `_apply_marker_opts`. It does not edit `_apply_line_opts`, `_apply_mlabel_opts`, `_apply_fill_opts`, `_make_figure_body` or `_generate_app_source`.

**Section decisions (this file).**
- **D-24a — opacity at construction, only when declared.** Each construction site passes `line_alpha`/`fill_alpha` only when the scheme declares an opacity on that colour (`GlyphMapper._scheme_alpha_kw`, the pattern `map_line` already uses at dash_render.py:9972-9979). The 25 schemes that declare none build the same glyph models at these sites as before. `_apply_line_opts` is untouched: a user colour without `%NN` keeps the scheme's opacity, and one with `%NN` wins (measured, E7).
- **D-24b — `_ci_line_restyle` has the last word.** Under `pstyle(ci)`/`pstyle(ci2)` the fit line takes the named style's opacity or none. Under `pstyle(p#)` it takes p#'s. Measured under sttrans: `lfitci, pstyle(ci)` draws its line `#808080` opaque, and `pstyle(p3)` draws it `#DDCC77` at 0.20 (E7, probe p24b).
- **D-24c — the small-symbol factor is measured per name, not one 0.707.** Stata 19.5 draws `smcircle`, `smdiamond`, `smsquare`, `smplus` and their hollow forms at 0.707 (1/√2) of the full symbol, `smtriangle`/`smtriangle_hollow` at 0.75, and `smx`/`smv` exactly as `x`/`v` (factor 1). The probe is p24a (E7), at the default size and at `msize(large)`. The register and IR-4 say "0.707", and M1 ("match Stata") binds the measured table.
- **D-24d — the histogram's keys and their defaults.** The parser reads `color histogram`, `color histogram_line`, `intensity histogram` and `linewidth histogram`. Each one a user scheme does not declare defaults to s2color's value (khaki `#cac27e`, stone `#d7d29e`, `full`, `medium`), as the CI band's keys do (dash_render.py:7078-7112, "The defaults are s2color's" at 7091). `pstyle(p#)` on a histogram (`#A65D62`/`#90353B`, E7) is S32's.
- **D-24e — the fixture key `p_mark_colors` keeps its name.** It becomes the marker FILL chain (`p#markfill → pmarkfill → p# → p`), beside a new `p_markline_colors`. No Stata 19.5 scheme declares any of `p#mark`, `p#markfill` or `p#markline` (every such line is commented out), so the 26 files and every recorded colour are unchanged. Only the provenance and sources text of `p_mark_colors` changes.
- **D-24f — `intensity bar` and `intensity area` leave the shipped files.** S16 stopped reading them (register P1.2.8, S16 TR-16.4). S15's Notes ("For S24") and S16's TR-16.4 hand their removal to S24, the next regenerator. The extractor drops them from the files and `_FALLBACK_PROPS` loses them. Their fixture keys `bar_alpha`/`area_alpha` stay, as Stata's own record. The shipped-but-unread keys therefore stay five (register P1.4.4). S33 keeps no exempt list: by ratification row 4 (06oct2026) no unread directive is noted, and every parsed directive, read or not, stays in the parsed scheme (S33's D-33d).
- **D-24g — sub-claims e and f are S33's.** The manifest's "a-f" uses a lettering older than the research note's. By its scope text, A138 ("P1.4 (g, ColorBar, unread directives): S33") and S01's P1.4b entry, the marker-label size and colour (research e) and the ColorBar chrome (research f) are S33's. S24 closes research a, b, b', c, c', d, h and i.
- **D-24h — caps and heads.** rcap's caps are S14's `dash` Scatter markers (TR-14.4); they take the opacity on fill and line. An arrow head takes its shaft's final `line_alpha`, read after `_apply_line_opts`, as `arrow_lw` is. Measured: pcarrow's 5 shafts and 10 head strokes, and rcap's 5 spines and 10 caps, all carry `stroke-opacity:0.20` under sttrans (E7).

**What is wrong today.** DROPIN-REMAINING.md:78-82 (P1.4) reads: "sttrans opacity is missing on fits, spikes, ranges, immediates and bands. Histograms ignore the scheme's histogram colour, intensity and line width. Hollow and sm* p# symbols are drawn filled and full size. rarea is drawn at alpha 0.5." Its WP-29 note keeps "the empty histogram key colour" here (P0.18's residual). GAPS2-D18 records the probe: lfit, kdensity and function lines, rspike/spike/rcap segments and scatteri/rscatter/dropline markers are drawn at alpha 1.0 and the rarea fill at 0.5, while scatter, line, bar, area and histogram draw at 0.2. GAPS2-D19 says `map_histogram` draws the p1 colour with a white 1px outline, where twoway draws the scheme's histogram style.

Re-measured at `c96facd` in both modes (Evidence E6):
- Under sttrans, 30 layer types draw at 1.0. rarea draws at 0.5.
- Every histogram is the bar p# cycle with a white outline: s2color `#1a476f`, and a second histogram `#90353b`. twoway draws both khaki `#CAC27E`, outlined stone `#D7D29E`.
- s1mono's p7-p10 are drawn filled, and its p11-p15 at full size.
- scatteri, rscatter, pcscatter, dropline and rcapsym draw a circle on every layer.
- A user scheme's `color p1mark` colours the markers, where twoway ignores it.
- `msymbol(Oh) malpha(50)` fills the hollow marker at 0.5.

**After this section**, in both modes, before and after any filter move:
- A colour opacity the scheme declares reaches every layer's lines, segments, markers and fills. The confidence band's fill is the one exception, because twoway draws it in `color ci_area`, which declares none.
- rarea is opaque, or 0.2 under sttrans, as area is.
- Every histogram layer is drawn in the scheme's histogram style: `color histogram` at `intensity histogram`, outlined in `color histogram_line` at `linewidth histogram`. That includes an emptied layer's key. `color()`, `fcolor()`, `lcolor()` and `fintensity()` still win.
- The scheme's hollow symbols are drawn as outlines. Its small symbols, and a user's `msymbol(sm*)`, are drawn at Stata's measured size for them, whatever `msize()` says.
- The p# symbol cycle reaches every marker type.
- Markers take `color p#markfill` for their fill and `color p#markline` for their outline.
- A hollow symbol stays hollow under `malpha()` and `mfcolor()`.

**Why one section.** These are one root cause: a scheme key read at only some of the glyph-construction sites. They share one set of symbols: the ~30 mapper construction sites, the parser's p# lists, `_apply_marker_opts`' end block, `_histogram_quads`, and one extractor change with one regeneration (A152). Labels, the colour key and the unread directives (retained in the parsed scheme, not noted; ratification row 4) are P1.4's other part (S33, batch 11), which extends this section's fixture.

**Test order and commit rule (rule 7, D1).** There is one entry and one commit, `(WP-30 P1.4a)`.
- **24-01** writes the regression tests with twoway's literal values, runs them against the unmodified tree and saves `<scratch>/24-P1.4a-failure.txt`. It never commits.
- **24-02 to 24-05** add the SVG reader, extract the fixture and append the fixture-driven and emptied-key failures.
- **24-06 to 24-18** fix, regenerate, flip the pinned tests, add the parity cases, fill the truth block and update the help.
- **24-19** closes the entry, replaces the marker and makes the commit after one full run through the queue.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — about 30 construction sites in both modes, two CRITICAL symbols, a regeneration of 26 files, and every histogram dashboard changes colour

**Why.** M1 accepts the visible changes (PLAN K2, RK-4): histogram style, rarea opacity and the symbols of nine mono schemes. One code path serves both modes, because the served app copies `GlyphMapper`, `SchemeParser` and `OptionTranslator` by source and rebuilds the scheme from its property dict (dash_render.py:33446-33459). The risk is breadth, not divergence.

**Risk factors.**
1. CRITICAL symbols (index batch 8.0): `GlyphMapper._apply_marker_opts` (12 impacted, 7 direct) and `GlyphMapper._empty_fit_line` (8 impacted, 8 direct).
2. HIGH symbols: `_scheme_alpha` (8, read only), `_render_ci_band` (5, 4 direct), `_ci_line_restyle` (6, 4 direct) and `_add_arrow_heads` (4, 2 direct).
3. Most mappers are `UNKNOWN`: they are dispatched by name through `_dash_glyph_dispatch` (dash_render.py:28519-28560).
4. The parser's new attributes must be computed in `_init_properties` from `_props` alone. Otherwise the served app (`SchemeParser.__new__` plus `_SCHEME_PROPS`) and `fallback()` lack them (research critic 3).
5. Pinned tests assert today's behaviour (E9). The red list must be re-measured on the batch base, because S07-S21 move code first (R9).
6. The regeneration rewrites 26 files and `scheme_truth.json`. A conflict is a re-run, never a hand edit (R7).
7. The `sm*` factor must survive `msize()` (critic 2). `msize()` sets `glyph.size` in `_apply_marker_opts` (8698-8701), so a factor applied only at construction would be lost.

**Mitigation.**
1. 24-01 checks that `<scratch>/batch-8-impact.txt` records the CRITICAL/HIGH warnings with approval. Any other symbol gets `gitnexus impact` in the main checkout before editing.
2. D-24a's "only when declared" rule leaves 25 schemes' construction kwargs unchanged at the opacity sites. `TestOtherSchemesDeclareNothing` pins it.
3. Every new attribute is read through `test_scheme_resolution._props_scheme` in a test (TR-24.8). `test_scheme_fallback_provenance.py` stays green through the `_FALLBACK_PROPS` entries.
4. 24-14 re-measures the red list after the fix and flips exactly that list, each flip recorded in `$S/24-flips.txt`.
5. The factor is applied once, last, inside `_apply_marker_opts`. A test applies `msize(large)` to s1mono's p11.

## Dependencies

- **Depends on: 07, 16.**
  - S07 (batch 3) ships 26 schemes (`SCHEMES`, `_BUILTIN_NAMES`, `EXPECTED_SCHEMES`), so S24's regeneration covers 26 files.
  - S16 (batch 6) rewrote `_scheme_alpha(color_idx, plot_type)` to return a declared opacity or 1.0. S16 also gave the five fill mappers `_fill_base`/`_f` and `_blend_intensity(hex, f, naturally_white)` with `_apply_fill_opts(r, options, base=, intensity=)`. It retired `bar_alpha`/`area_alpha`, gave `_intensity` an unclamped reader (`clamp=False`), and left `map_rarea`'s 0.5 and the histogram's full intensity to S24 (D-16a, D-16b). It also created `test/test_intensity_blend.py` with `TestTheHistogramUntilS24` and `test/fixtures/intensity_truth.json`, whose `"owner": "S24"` histogram probes S24 asserts.
  - Through earlier batches:
    - S01: the entry, `WP30_OPEN["P1.4a"]`, the marker `<!-- WP-30 P1.4a -->`, the stub block `S24` and the map anchor.
    - S02: the path-free extractor form.
    - S06: the note channel, which S24 does not use.
    - S08: `resolve_size`/`translate_msize` in `_apply_marker_opts`, and markers at 5.87 px.
    - S13: the line ladder behind `SchemeParser._lwidth`.
    - S14: rcap's `dash` caps tagged `dash_cap`, rcapsym's caps removed and its markers sized from the scheme.
    - S15: the chrome keys and `naturally_white`.
- **Blocks:**
  - **S30** (batch 10, colour grammar): after side h, `color p1mark bogus` can no longer turn markers black (register P1.13.7).
  - **S32** (batch 11, named styles): `style_bundle` replaces the construction reads S24 adds, keeping hollow, factor, histogram style and opacity.
  - **S33** (batch 11): marker labels, ColorBar, and unread directives (retained in the parsed scheme, not noted; ratification row 4). It extends `scheme_layer_truth.json` and regenerates again.
  - **S45** (batch 16, recast): a recast layer passes its new type to `_scheme_alpha_kw`.
  - **S49** (batch 17, horizontal): every transposed construction site keeps S24's alpha kwargs.
- **Parallel batch: 8.** Merge order S22, S23, S24 (S24 last, A152).
- **Can run with:**
  - S22: the `dash` dispatcher, `_dash_render_immediate`, `_dash_build`, `_dash_saving_parse`, dash.sthlp Syntax/Exporting.
  - S23: `_make_figure_body`, `_generate_app_source`, `_dash_launch_app`, the trial, `test_mode_parity.py`'s `_MUST_WARN`, dash.sthlp Server Mode.
  - No function is shared. Both partners and S24 append to `test_mode_parity.py` `CORPUS` and to their own map anchors, so the hunks are apart (R2, R8).

## Evidence

All anchors are `c96facd`'s (dash_render.py 37,689 lines). Batches 1-7 land before S24 and move lines, so the symbols named are authoritative.

### E1 — opacity: where it is read today, and where it is not

**The pattern to copy** (`map_line`, 9972-9979), which passes a line alpha only when the scheme declares one:

```python
9972        # A line has no intensity-derived alpha (Stata's `intensity p' is
...
9976        _line_alpha = self.scheme.default_alpha(
9977            color_idx, "connected" if connected else "line")
9978        if _line_alpha is not None:
9979            _line_kwargs["line_alpha"] = _line_alpha
```

**`_scheme_alpha`** (9727-9742; S16 drops its third argument and returns the declared opacity or 1.0), read by `map_scatter` 9836, `map_area` 10091, `map_bar` 10239 and `_histogram_quads` 12435. `map_bar`'s outline already reads `default_alpha(color_idx, "bar")` (10246). bar, area, scatter, connected, dot, line, tsline and rconnected are therefore conformant and not edited for opacity.

**The fit line with no rows** (`_empty_fit_line`, 10831-10837), which has no alpha:

```python
10831        r = fig.line(x=xcol, y=ycol,
10832                     source=ColumnDataSource({xcol: [], ycol: []}),
10833                     line_color=self.scheme.default_color(color_idx, "line"),
10834                     line_width=self.scheme.plot_line_width(color_idx,
10835                                                            width_kind),
10836                     legend_label=yvar)
10837        self._apply_line_opts(r, options)
```

**The CI fit line** (`_render_ci_band`, 8242-8252), which takes a colour but no alpha. Then `_ci_line_restyle` (8448-8474) sets a named style's alpha only when declared:

```python
8245        line_r = fig.line(
8246            x=x_col, y=y_col, source=source,
8247            line_color=color,
...
8251        self._ci_line_restyle(line_r, options)
8252        self._apply_line_opts(line_r, options)
```
```python
8464                g.line_color = ls["line"]
8465                if ls.get("line_alpha") is not None:
8466                    g.line_alpha = ls["line_alpha"]
...
8469        elif ps == "p":
8470            g.line_color = self.scheme.default_color(pi, "connected")
8471            _a = self.scheme.default_alpha(pi, "connected")
8472            if _a is not None:
8473                g.line_alpha = _a
```

**The sites with no alpha** (each a `fig.*` call; the plot type is the one its `default_color` call names):

| Mapper | Construction site(s) | Colour cycle asked |
|---|---|---|
| `_empty_fit_line` | 10831 | `"line"` |
| `map_lfit`, `map_qfit` | 10914, 10991 | `"line"` |
| `map_lfitci`, `map_qfitci`, `map_fpfitci` (no rows) | 11046, 11171, 12370 | `"line"` |
| `map_lfitci`, `map_qfitci`, `map_lpolyci`, `map_fpfitci` (rows) | `_render_ci_band` 8245, called at 11097, 11224, 11835, 12417 | `"line"` |
| `map_lowess`, `map_lpoly`, `map_fpfit`, `map_kdensity` | 11359, 11773, 12319, 12886 | `"line"` |
| `map_mspline`, `map_mband`, `map_function` | 14725, 14847, 14909 and 14944 | `"line"` |
| `map_rline` (and `map_tsrline` through it, 14525) | 13305, 13306 | `"line"` |
| `map_spike` | 10361 | `"spike"` |
| `map_rspike` | 13148 | `"rspike"` |
| `map_rcap` | spine 13229; caps 13230-13231 (S14: two `dash` Scatters) | `"rcap"` |
| `map_dropline` | segment 13502 (`"spike"`), dot 13503 (`"dropline"`) | both |
| `map_rcapsym` | spine 13607; dots 13610-13611 (S14: caps removed) | `"rcap"`, `"rscatter"` |
| `map_pcspike` (and `map_pci_literal` through it, 13842) | 13786 | `"pcspike"` |
| `map_pcarrow` (and `map_pcarrowi`, 14455), `map_pcbarrow` | shafts 14079, 14160; heads 14096-14098, 14167-14170 | `"pcarrow"`, `"pcbarrow"` |
| `map_pccapsym` | segment 14254 (`"pccapsym"`), dots 14270 (`"pcscatter"`) | both |
| `map_scatteri`, `map_pcscatter`, `map_rscatter` | 13714, 13951, 14630 | `"scatter"` |
| `map_rbar` | 13066 (fill; `line_alpha=0`, no outline) | `"bar"` |
| `map_rarea` | 12984-12989 | `"area"` |

**rarea's half opacity** (12983-12986):

```python
12983        _varea_kwargs: dict = dict(x=xvar, y1=y1var, y2=y2var, source=source,
12984                                    fill_color=self.scheme.default_color(color_idx, "area"),
12985                                    fill_alpha=0.5,
12986                                    legend_label=y1var)
```

**Arrow heads** (`_add_arrow_heads`, 14017-14022; heads built at 14096-14098), which take the shaft's width but not its alpha:

```python
14083        arrow_lw = seg.glyph.line_width
...
14096        self._add_arrow_heads(fig, pc_source, y1var, x1var, y2var, x2var,
14097                              color, arrow_lw,
14098                              end=OpenHead(size=10, line_color=color))
```

### E2 — the histogram

`_histogram_quads` (12423-12449) fills with the bar p# cycle and a white outline, and has no width. It serves the populated and both empty branches (12478, 12490, 12525):

```python
12429        r = fig.quad(top="top", bottom=0, left="left", right="right",
12430                     source=source,
12431                     fill_color=self.scheme.default_color(color_idx, "histogram"),
12432                     line_color="white",
12433                     # `intensity bar' -- a histogram is a bar plot in
12434                     # Stata's own scheme vocabulary.
12435                     fill_alpha=self._scheme_alpha(
12436                         color_idx, "histogram", self.scheme.bar_alpha),
```

(S16 rewrites 12431-12436 into `_fill_base`, `_f = 1.0` and `_blend_intensity`; D-16a.) `_cycle_for` (7186-7187) puts `"histogram"` in the bar cycle. None of the 20 shipped files has `color histogram` (`grep -l '^color histogram' dash-*.scheme` prints nothing). Stata's style files: `shadestyle-histogram.style` has `set color scheme histogram`, `set intensity scheme histogram`; `linestyle-histogram.style` has `set width scheme histogram`, `set color scheme histogram_line`. The keys each scheme's `#include` chain resolves, through the extractor's `SchemeResolver` (probe `hist_keys.py`, 03oct2026):

```
s2color, s2gcolor, s1color, s1rcolor, economist, s2color8, meta    khaki (#cac27e) / stone (#d7d29e)   full     medium
stcolor, stcolor_alt, stgcolor, stgcolor_alt, the four st*_meta/mv, stcoloralias
                                                                   stc1 (#1a85ff) / stc1*0.7 (#5faaff) inten90  vthin
stmono1, stmono2                                                   gs8 (#808080) / black                 inten90  vthin
stsj, s2mono, s1mono, sj, s2manual, s1manual, s2gmanual            gs8 (#808080) / black                 full     medium
sttrans                                                            "26 71 111 %20" (#1a476f, 20) for both full     medium
```

### E3 — symbols

`SchemeParser._symbol` (6797-6804) keeps only Bokeh's marker name:

```python
6797    def _symbol(self, key: str, default: str = "circle") -> str:
6798        raw = self._props.get(key, "").strip()
6799        if not raw:
6800            return default
6801        try:
6802            return OptionTranslator.translate_msymbol(raw)
```

The cycle (6878-6882) is a list of those names. `_MARKER_MAP` (5249-5302) maps every `sm*` to the full shape. `_HOLLOW_SYMBOLS` (5239-5244) is read only from `msymbol()`/`marker`.

`_apply_marker_opts` sets `msize()` (8698-8701), then the hollow block (8768-8780), then `malpha()` (8782-8791). That order is what refills a hollow marker (side i):

```python
8768        _sym_raw = str(options.get("msymbol", options.get("marker", ""))
8769                       ).strip().lower()
8770        if _sym_raw in OptionTranslator._HOLLOW_SYMBOLS:
8771            if hasattr(glyph, "fill_alpha"):
8772                glyph.fill_alpha = 0.0
...
8782        if "malpha" in options:
...
8786                    if hasattr(glyph, "fill_alpha"):
8787                        glyph.fill_alpha = ma / 100.0
```

Only `map_scatter` (9774) and `map_pccapsym` (14271) read `default_symbol`:
- `map_scatteri` defaults to `marker = "circle"` (13707).
- `map_rscatter` (14623-14630) and `map_pcscatter` (13944-13951) pass no marker.
- `map_dropline`'s dot (13490-13495) passes no marker.
- `map_rcapsym`'s dots (13597-13602) pass no marker at `size=7`.

`_apply_marker_opts` is called once per marker glyph: 9847, 13508, 13615 (two dots), 13722, 13952, 14280, 14631.

### E4 — the marker colour key (side h)

The marker colour cycle follows the `p#mark` chain (6864-6866), and `_cycle_for` sends every marker type to it (7188-7194):

```python
6864        _pm = [self._stub_color_alpha(i, "mark") for i in range(1, 16)]
6865        self.p_mark_colors: list[str] = [c for c, _ in _pm]
6866        self.p_mark_alphas: "list[float | None]" = [a for _, a in _pm]
```

Stata's `markerstyle-p#.style` reads `set fillcolor scheme p#markfill` and `set linestyle scheme p#mark`, and `linestyle-p#mark.style` reads `set color scheme p#markline`. So `color p#mark` is never a marker colour. The extractor's `p_color_series("p_mark_colors", "mark")` (scripts/extract_scheme_truth.py:736) and `expected_directives`' stub tuple `("mark", "p_mark_colors")` (1467) follow the same wrong chain. `_stub_color_alpha(i, stub)` (6527-6541) already walks `p<i><stub> → p<stub> → p<i> → p` for any stub.

### E5 — both modes and filter moves

- The served app rebuilds the scheme from the property dict (33446-33459: `SchemeParser.__new__`, `_s._props = dict(_SCHEME_PROPS)`, `_s._init_properties()`). `fallback()` (5827-5841) does the same from `_FALLBACK_PROPS`.
- The three classes are copied by source (class loop 33436). Methods and class constants need no copy-list entry (R2 row S24).
- A served filter move copies redraw data onto the live sources (emitted 36019-36042). Glyph styles stay as built.
- The saved page's scripts never write a glyph style: the stale cue toggles `r.muted` only (19330). `_dash_stale_glyph` (1130-1145) scales each build-time alpha by `_DASH_STALE_ALPHA` (0.3, 1095), so a build-time 0.2 shows as 0.06 when a computed layer is stale.

### E6 — measured at `c96facd`, both modes

The probe drew each type alone under sttrans through `test_scheme_resolution._draw`, with `(Type, fill_alpha, line_alpha)` per glyph. Both modes agreed on every row (`[same]`):

```
lfit [('Line', None, 1.0)]            lfitci [('VArea', 1.0, None), ('Patch', 0.0, 1.0), ('Line', None, 1.0)]
kdensity/function/mband [('Line', None, 1.0)]     spike, rspike, pcarrow [('Segment', None, 1.0)]
rcap [('Segment', None, 1.0) x3]      rcapsym [Segment x3 at 1.0, ('Scatter', 1.0, 1.0) x2]
dropline [('Segment', None, 1.0), ('Scatter', 1.0, 1.0)]   rline [('Line', None, 1.0) x2]
rscatter, scatteri, pcscatter [('Scatter', 1.0, 1.0)]       pccapsym [Segment 1.0, ('Scatter', 1.0, 1.0)]
rbar [('VBar', 1.0, 0)]   rarea [('VArea', 0.5, None)]   histogram [('Quad', 0.2, 1.0)]
```

Under s1mono, `p_symbols` is `circle diamond square triangle x plus circle diamond square triangle circle diamond square triangle x`. The second layer's markers were:

```
scatteri [('circle', 8.0)]  rscatter [('circle', 8.0)]  pcscatter [('circle', 8.0)]  dropline [('circle', 8.0)]
rcapsym [('circle', 7), ('circle', 7)]               scatter [('diamond', 8.0)]  pccapsym [('diamond', 8.0)]
```

`map_scatter(..., {"msymbol": "Oh", "malpha": "50"})` gives `fill_alpha 0.5, line_alpha 0.5`. Research p1-04 §2 measured the histogram as s2color `Quad(#1a476f, 1.0, white)`, stcolor `#1a85ff`, s1mono `#606060`, and a second histogram `#90353b`. The empty histogram's key was `#90353b`/white where twoway keys `#d7d29e` (`emptied_layer_truth.json`). A user `color p1mark green` drew the markers green.

### E7 — twoway truth (StataNow 19.5 MP, `graph export` to SVG)

From research p1-04 §3 (t1, t2, t4, t6, t8, t10, t11) and its critic additions (c1, c2):
- **sttrans opacity.**
  - Lines: lfit, kdensity, function, lowess, lpoly, mband, mspline, fpfit and line are all `stroke-opacity:0.20`.
  - Segments: spike, rspike, rcap, pcspike, pcarrow and pci are `stroke-opacity:0.20`.
  - Markers: scatteri, rscatter, rcapsym and dropline draw `fill-opacity:0.20` and `stroke-opacity:0.20`.
  - Fills: rarea and area fill `#486C8C` at 0.20; rbar likewise; the histogram `#1A476F` at 0.20 with its outline at 0.20.
  - The CI band is `fill:#C0C0C0` with no opacity, and its line is at 0.20.
- **User colours under sttrans.** `lcolor(red)` is `#FF0000` at 0.20; `lcolor(red%70)` is 0.70; rspike `lcolor(red)` is 0.20; rarea `fcolor(red)` is 0.20.
- **rarea against area.** Every scheme draws the two identically (s2color fills `#486C8C` opaque).
- **Histogram style.**
  - s2color, s1color and s1rcolor: fill `#CAC27E`, outline `#D7D29E`. economist: the same colours.
  - s1mono, s2mono: `#808080` with a black outline. stmono1: `#8D8D8D`.
  - stcolor: `#3191FF` (stc1 at inten90), outline `#5FAAFF`.
  - sttrans: `#1A476F` at 0.20, fill and outline.
  - **Two histogram layers draw the same style.**
  - A user scheme with `color histogram red`, `intensity histogram inten50`, `color histogram_line blue`, `linewidth histogram vthick` draws `#FF8080` outlined `#0000FF` 40.32.
  - Options: `fcolor(red)` gives `#FF0000` with a stone outline; `color(red)` gives both red; `pstyle(p2)` gives `#A65D62`/`#90353B` (S32's).
- **Symbols.**
  - s1mono `scatter y1-y15`: p7 `circle_hollow` and p9 `square_hollow` are stroked only. p11 `smcircle`'s centre-line radius is 15.59 against p1's 22.03.
  - `pstyle(p7) mfcolor(red)` stays hollow.
  - c2: under `msize(large)` p11 is 24.75 against 35.02 (0.707). The factor survives `msize()`.
- **The cycle.** Under s1mono the second layer of scatteri, rscatter, pcscatter, dropline and rcapsym draws diamonds in `#A0A0A0`.
- **Mark colours.** `color p1mark green` leaves twoway's marker `#1A476F`. `color p1markfill green` / `color p1markline blue` give a green fill and a blue outline.

Measured for this file, 03oct2026, through `scripts/stata_slot.sh` (scratch `…/wp30/s24/p24a.do` and `p24b.do`, `sysuse auto`). Each symbol was drawn alone (`scatter mpg weight in 1`, axes off). The ratio is the stroked outline's extent, sm over full:

```
msymbol           default  msize(large)        msymbol            default  msize(large)
smcircle          0.7077   0.7067              smcircle_hollow    0.7077   0.7067   (stroke only)
smdiamond         0.7063   0.7076              smdiamond_hollow   0.7063   0.7076   (stroke only)
smsquare          0.7079   0.7067              smsquare_hollow    0.7079   0.7067   (stroke only)
smtriangle        0.7510   0.7506              smtriangle_hollow  0.7510   0.7506   (stroke only)
smplus            0.7081   0.7066              smx  1.0000 1.0000   smv  1.0000 1.0000 (same geometry as x, v)
user scheme `#include s2color', `color pmarkfill green', `color pmarkline blue'  ->  fill:#008000, stroke:#0000FF, on both layers
user scheme `#include s2color', `color p1mark green', `color pmark red'          ->  fill:#1A476F, stroke:#1A476F
twoway lfitci mpg weight, pstyle(ci) scheme(sttrans)    -> line stroke:#808080 (no opacity); band fill:#C0C0C0
twoway lfitci mpg weight, pstyle(p3) scheme(sttrans)    -> line #DDCC77 stroke-opacity:0.20; band #E4D692 fill-opacity:0.20
twoway pcarrow mpg weight price length in 1/5, scheme(sttrans)   -> 15 strokes #1A476F stroke-opacity:0.20 (5 shafts, 10 head lines)
twoway rcap mpg price weight in 1/5, scheme(sttrans)            -> 15 strokes stroke-opacity:0.20 (5 spines, 10 caps)
twoway histogram mpg, color(red) scheme(sttrans)                -> fill #FF0000 fill-opacity:0.20; outline #FF0000 stroke-opacity:0.20
twoway (scatter ..) (scatter .., msymbol(smcircle_hollow) mfcolor(red)), scheme(s1mono) -> layer 2 stroke #A0A0A0 only, no red fill
```

Stata 19.5 writes diamond, square and triangle markers as `<polygon>` elements, and `x` as two `<line>` elements. `scripts/svg_truth.py:svg_fills` reads no `<polygon>`, as its docstring admits, so this section adds its own reader (TR-24.16).

### E8 — the extractor, the files and the fallback

- `scripts/extract_scheme_truth.py`:
  - `extract` (603) with `p_color_series` (717) and `color_of` (678);
  - `expected_directives` (1371), with the "Fill intensities." group at 1498-1501 holding `intensity bar`/`intensity area`;
  - `_drop_undeclared_stubs` (1915) driven by `_STUB_KEY` (1907-1912, `"color": re.compile(r"p\d+(line|bar|mark|lineplot)")`);
  - `update_scheme_file` (1852), which calls it at 1867.
- Directive counts at `c96facd` (`test_help_claims_8._directives`):
  - colour schemes 80-83;
  - s1mono and stmono1 110; s2mono, s2manual, stmono2 and stsj 111; sj 112;
  - s1manual 119; s2gmanual 139.
- S15 adds about 24 chrome directives per file, and S24 adds four histogram keys and removes two (D-24f). So `test_80_to_140_directives` is re-measured, never trusted.
- `_FALLBACK_PROPS` (5728-5824) has `"intensity area": "full"`, `"intensity bar": "full"`, `"intensity p": "inten80"` (5769-5771) and no histogram, symbol or mark key.

### E9 — tests that pin today's behaviour (flipped by 24-14 to 24-16, never deleted; R9)

| Node | Today | After |
|---|---|---|
| `test/test_help_claims_8.py::TestTheSchemeOpacityStopsWhereTheHelpSays::test_the_colour_but_not_the_opacity` (:763-782, 13 types × 2 modes) | sttrans alphas equal s2color's | renamed `test_the_colour_and_the_opacity`: every sttrans alpha is 0.2, every s2color one 1.0; the band `#c0c0c0` stays 1.0 |
| `test/test_help_claims_8.py::TestTheShippedFiles::test_80_to_140_directives` (:1013-1030) | 80 ≤ n ≤ 140 and help "80 to 140" | renamed `test_the_directive_count_is_what_the_help_says`: the measured bounds, the same numbers in the help |
| `test/test_scheme_review_fixes.py::TestMarkColourIsForMarkers::test_markers_take_p1mark_and_segments_take_p1` (:387-408, 12 types × 2 modes) | markers take `color p1mark` | renamed `test_markers_take_p1markfill_and_segments_take_p1`: `p1mark` ignored; `p1markfill` fills, `p1markline` outlines |
| `test/test_html_output.py::TestOutputBackendAndVisualMarkers::test_rarea_varea_glyph_has_fill_attributes` (:1856-1866) | `fill_alpha` `[0.5]*20` | `[1.0]*20` (area's rule); fill colour as S16 left it |
| `test/test_glyphs.py::TestHardeningGuards::test_histogram_empty_source_keeps_the_scheme_style` (:3337-3342) | colour equals `default_color(0, "histogram")` | equals `_blend_intensity(histogram_color, histogram_intensity, naturally_white)` |
| `test/test_intensity_blend.py::TestTheHistogramUntilS24::test_s2color_keeps_the_full_colour` (S16) | default histogram `#1a476f` | default `#cac27e`; `fcolor(navy)` stays `#1a476f` |
| `test/test_emptied_layer_style.py::_key_cases` (:108-116) | skips `histogram` | includes it: `TestTheKeyIsTwoways::test_the_empty_layer_draws_in_twoways_key_colour[s2color-histogram]` and `[s1mono-histogram]` |
| `test/test_scheme_fidelity.py` `COLOR_LISTS["p_mark_colors"]` (:214) | `p{i}mark → pmark` chain | `p{i}markfill → pmarkfill`; `"p_markline_colors"` row added |
| `test/test_scheme_fidelity.py` `ALPHA_SCALARS` (:225-232), if S16 left `bar_alpha`/`area_alpha` | the two retired directives checked | the two rows removed (D-24f) |

Extended, not flipped:
- `test/test_scheme_consumption.py::TestNoParsedKeyIsDiscarded::test_the_key_is_read_somewhere` (:594): new attributes.
- `test/test_scheme_consumption.py` :1546: the shipped-cycle loop gains `p_markline_colors`.
- `test/test_scheme_resolution.py` `ALPHA_LISTS` (:542): `p_markline_alphas`.

Guards that must stay green:
- `test/test_scheme_fallback_provenance.py::TestTheFallbackMirrorsS2color::test_every_style_attribute_matches`;
- `test/test_scheme_resolution.py::TestSttransIsDrawnTranslucent`, `::TestEveryOtherSchemeIsUnchanged` (Quad `(1.0, 1.0)`);
- `test/test_scheme_fidelity.py::test_regenerating_a_shipped_file_is_a_no_op`, `::test_an_older_translation_loses_its_resolved_stub_lines`;
- `test/test_emptied_layer_style.py::TestTheHistogramQuads::test_the_empty_and_populated_quads_share_a_style`;
- `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline`. Expected unchanged: scatter's construction kwargs do not change under s2color. If it moves, it is re-derived with its reason (R10).

### E10 — blast radius (`gitnexus impact <sym> -d upstream -r dash`, 03oct2026)

| Symbol | Risk | Note |
|---|---|---|
| `GlyphMapper._apply_marker_opts` | **CRITICAL** (12; 7 direct) | warn; one new keyword and one end block |
| `GlyphMapper._empty_fit_line` | **CRITICAL** (8; 8 direct) | warn; one kwarg spread |
| `GlyphMapper._scheme_alpha` | HIGH (8; 4 direct) | read only; the new helper sits beside it |
| `GlyphMapper._render_ci_band` | HIGH (5; 4 direct) | one keyword |
| `GlyphMapper._ci_line_restyle` | HIGH (6; 4 direct) | D-24b |
| `GlyphMapper._add_arrow_heads` | HIGH (4; 2 direct) | one keyword |
| `_histogram_quads`, `map_scatter`, `map_scatteri`, `map_pcarrow`, `map_function`, `map_rline`, `translate_msymbol`, `SchemeParser._symbol`, `_init_properties`, `_cycle_for`, `_stub_color_alpha`; extractor `expected_directives`, `update_scheme_file`, `_drop_undeclared_stubs`, `p_color_series` | LOW (1-3) | `_init_properties` has three real callers (the parser, `fallback()`, the emitted app) |
| `map_rarea`, `map_pcscatter`, `map_rscatter`, `map_pccapsym`, `map_dropline`, `map_rcapsym`, `map_lfit`, `map_spike`, `map_kdensity`, `SchemeParser.default_color`, `default_alpha`; extractor `extract` | UNKNOWN | confirmed by `grep -n`: dispatched through `_dash_glyph_dispatch` (28519-28560) in both modes; `extract`'s callers are `main()` and `test_scheme_fidelity.py`. Recorded as unresolved, every bar, range, pc and fit layer in both modes. |

## User stories

- **US-24.1** As a twoway user drawing under `sttrans`, I want fits, spikes, ranges, paired-coordinate and immediate layers drawn at the scheme's 20% opacity, as Stata draws them, with the confidence band left as Stata leaves it.
- **US-24.2** As a dashboard publisher, I want histograms drawn in my scheme's histogram style, khaki with a stone outline under s2color and the same for every histogram layer, so the dashboard matches my Stata report.
- **US-24.3** As a twoway user, I want rarea drawn as opaque as area, not half transparent.
- **US-24.4** As a twoway user of s1mono, sj or another mono scheme, I want its hollow and small symbols drawn hollow and small, and the symbol cycle on every marker type, so the series stay distinguishable without colour.
- **US-24.5** As a twoway user, I want `msymbol(smcircle)` drawn small, also with `msize(large)`, and `msymbol(Oh) malpha(50)` drawn hollow.
- **US-24.6** As a scheme author, I want `color p1markfill` and `color p1markline` to colour my markers and `color p1mark` to be ignored, as twoway reads them.
- **US-24.7** As a dashboard reader, I want every one of these looks unchanged by a filter move, on the saved page and in the served app.

## Business requirements

- **BR-24.1** Under a scheme that declares a colour opacity, every line, segment, marker and fill drawn in a p# colour, and every arrow head and cap, carries that opacity. The CI band's fill and outline, drawn in `ci_area`'s colours, do not. A user colour with its own `%NN`, or `malpha()`/`lalpha()`/`falpha()`, still wins. A user colour without `%NN` keeps the scheme's opacity.
- **BR-24.2** A CI fit line under `pstyle(ci)`/`pstyle(ci2)` takes the named style's opacity or none. Under `pstyle(p#)` it takes p#'s.
- **BR-24.3** rarea's fill opacity is area's: 1, or the scheme's declared opacity.
- **BR-24.4** Every histogram layer is drawn with:
  - fill `color histogram` blended at `intensity histogram`;
  - opacity `color histogram`'s declared opacity or 1;
  - outline `color histogram_line` at its declared opacity or 1, `none` drawing no outline;
  - outline width `linewidth histogram`.

  The layer's position in the graph does not change it. `color()`, `fcolor()`, `lcolor()`, `lwidth()` and `fintensity()` still win as they do on bars. An emptied histogram's key has the same style.
- **BR-24.5** A p# symbol the scheme names hollow is drawn with no fill, whatever `mfcolor()` or `malpha()` say. A user `msymbol()` replaces it: `msymbol(O)` is filled, and `msymbol(Oh)` is hollow under `malpha()`.
- **BR-24.6** A small symbol, from the scheme's cycle or a user's `msymbol()`, is drawn at Stata's measured factor of the size it would otherwise have, `msize()` included:
  - 0.7071 for `smcircle`, `smdiamond`, `smsquare`, `smplus` and their hollow forms;
  - 0.75 for `smtriangle` and `smtriangle_hollow`;
  - 1 for `smx` and `smv`.

  The lower-case shorthands keep today's size (P2.11).
- **BR-24.7** scatter, connected, dot, rconnected, scatteri, rscatter, pcscatter, pccapsym, dropline and rcapsym markers take the p# symbol cycle when no `msymbol()` is given.
- **BR-24.8** A marker's fill is `color p#markfill → pmarkfill → p# → p`. Its outline is `color p#markline → pmarkline → p# → p`. `color p#mark` and `color pmark` change nothing.
- **BR-24.9** BR-24.1 to BR-24.8 hold on the saved page and in the served app, before and after a filter move, and the two modes draw the same. A stale computed layer on the saved page shows at 0.3 of its drawn opacity.
- **BR-24.10** A scheme that declares no opacity draws every non-histogram, non-rarea layer at the opacity it drew before.
- **BR-24.11** No input is newly refused and no note is newly printed.

## Technical requirements

All in `dash_render.py` unless named. "The base" is `<scratch>/batch-8-base.txt`.

- **TR-24.1 The opacity helper.** `GlyphMapper._scheme_alpha_kw(self, color_idx: int, plot_type: str, *, fill: bool = False, line: bool = True) -> dict`, directly after `_scheme_alpha`.
  - It sets `a = self.scheme.default_alpha(color_idx, plot_type)` and returns `{}` when `a is None`.
  - Otherwise it returns `{"line_alpha": a}` when `line` and `{"fill_alpha": a}` when `fill`.
  - Its docstring states D-24a, the E7 measurement, and that an intensity never reaches it.
- **TR-24.2 Lines and fits.** Each `fig.line` of E1's first block gains `**self._scheme_alpha_kw(color_idx, "line")`:
  - `_empty_fit_line`, the four no-rows CI lines and the line mappers;
  - both `map_rline` lines;
  - both `map_function` lines.

  `_render_ci_band` gains the keyword `alpha_kw: "dict | None" = None`, spread into its `fig.line` as `**(alpha_kw or {})`. Its four callers pass `alpha_kw=self._scheme_alpha_kw(color_idx, "line")`.
- **TR-24.3 `_ci_line_restyle` (D-24b).**
  - For a named style: `want = ls["line_alpha"] if ls.get("line_alpha") is not None else 1.0`, assigned to `g.line_alpha` only when it differs from the current value.
  - For `ps == "p"`: `want = _a if _a is not None else 1.0`, with the same assignment rule.
  - With no `pstyle()` nothing changes. `_apply_line_opts` still runs after it.
- **TR-24.4 Segments, ranges and paired coordinates.** Each construction keyword dict gains `**self._scheme_alpha_kw(color_idx, <type of its colour call>)`:
  - `map_spike` ("spike"); `map_rspike` ("rspike");
  - `map_rcap`'s spine ("rcap") and its two `dash_cap` Scatters (`"rcap", fill=True, line=True`);
  - `map_dropline`'s segment ("spike"); `map_rcapsym`'s spine ("rcap");
  - `map_pcspike` ("pcspike"); `map_pcarrow` ("pcarrow"), `map_pcbarrow` ("pcbarrow"); `map_pccapsym`'s segment ("pccapsym").
  - `map_rbar` gains `**self._scheme_alpha_kw(color_idx, "rbar", fill=True, line=False)`. Its `line_alpha=0` stays: its outline is not this section's.
- **TR-24.5 Arrow heads (D-24h).** `_add_arrow_heads(..., end, start=None, line_alpha=1.0)`:
  - the `Arrow` gets `line_alpha=line_alpha` only when it is not 1.0;
  - `map_pcarrow`/`map_pcbarrow` read `_la = seg.glyph.line_alpha` after `_apply_line_opts`, beside `arrow_lw`, and pass it;
  - `OpenHead(...)`/`NormalHead(...)` get `line_alpha=_la` when it is not 1.0.
- **TR-24.6 rarea.** `fill_alpha=0.5` becomes `fill_alpha=self._scheme_alpha(color_idx, "rarea")` (S16's two-argument form, as `map_area`'s `"area"`). "rarea" is in `_cycle_for`'s bar set, so the opacity comes from the same cycle as area's.
- **TR-24.7 Symbol traits.**
  - `OptionTranslator._SMALL_SYMBOL_FACTOR: dict[str, float]`, after `_INVISIBLE_SYMBOLS`:
    - `smcircle`, `smcircle_hollow`, `smdiamond`, `smdiamond_hollow`, `smsquare`, `smsquare_hollow`, `smplus` → `math.sqrt(0.5)`;
    - `smtriangle`, `smtriangle_hollow` → 0.75;
    - `smx`, `smv` → 1.0;
    - a comment cites E7's table.
  - `@staticmethod symbol_traits(value: str) -> tuple[str, bool, float]`, after `translate_msymbol`:
    - `marker = OptionTranslator.translate_msymbol(value)`, which raises `ValueError` as it does today;
    - `key = value.strip()`; `low = key.lower()`;
    - `hollow = low in _HOLLOW_SYMBOLS`;
    - `factor = _SMALL_SYMBOL_FACTOR.get(key, _SMALL_SYMBOL_FACTOR.get(low, 1.0))`.

    Every factor key is a full name, so the one- and two-letter shorthands keep 1.0 (P2.11). `translate_msymbol` is unchanged.
- **TR-24.8 The parser (from `_props` alone).**
  - `SchemeParser._symbol_traits(self, key, default="circle") -> tuple[str, bool, float]`: a blank key gives `(default, False, 1.0)`; otherwise `OptionTranslator.symbol_traits(raw)`, with `ValueError` giving `(default, False, 1.0)`. `_symbol` becomes `return self._symbol_traits(key, default)[0]`.
  - In `_init_properties` the p# symbol block (6878-6882) builds `_st` once over the same `_first_present` chain, then sets `self.p_symbols`, `self.p_symbol_hollow: list[bool]` and `self.p_symbol_factor: list[float]`.
  - `_pm` (6864) reads `"markfill"`; its comment names `markerstyle-p#.style`'s `fillcolor`. A new `_pml = [self._stub_color_alpha(i, "markline") …]` sets `self.p_markline_colors`/`self.p_markline_alphas`, with a comment naming `linestyle-p#mark.style`.
  - After the CI band block (`self.ci_line_styles`, 7112), D-24d:
    - `self.histogram_color, self.histogram_alpha = self._color_alpha("color histogram", "#cac27e")`;
    - `self.histogram_line_color, self.histogram_line_alpha = self._band_color("color histogram_line", "#d7d29e")`;
    - `self.histogram_intensity = <S16's unclamped intensity reader>("intensity histogram", 1.0)`, as S16 reads `p_bar_intensity` (`clamp=False` in S16's TR-16.3);
    - `self.histogram_line_width = self._bounded_lwidth("linewidth histogram", self.default_line_width)`.
  - Public accessors after `default_symbol` (7279): `default_symbol_traits(self, index) -> tuple[str, bool, float]` (index % 15) and `default_markline(self, index) -> tuple[str, "float | None"]`.
  - `_cycle_for`'s marker comment (7188-7192) is rewritten: markers fill from `p#markfill`; `p#mark` is not read (twoway does not, E7).
  - `_FALLBACK_PROPS` gains `"color histogram": "#cac27e"`, `"color histogram_line": "#d7d29e"`, `"intensity histogram": "full"`, `"linewidth histogram": "medium"` after `"linewidth ci2_area"`, and loses `"intensity area"`/`"intensity bar"` (D-24f).
- **TR-24.9 The marker helpers.**
  - `GlyphMapper._marker_traits(self, color_idx, options) -> tuple[str, bool, float]`:
    - `raw = str(options.get("msymbol", options.get("marker", "")) or "").strip()`;
    - when `raw` is non-blank and `OptionTranslator.symbol_traits(raw)` succeeds, that result;
    - otherwise `self.scheme.default_symbol_traits(color_idx)`. An unknown name keeps the scheme's symbol; `_apply_marker_opts` names it, as today.
  - `GlyphMapper._marker_alpha_kw(self, color_idx) -> dict`: `fill_alpha` from `default_alpha(color_idx, "scatter")` and `line_alpha` from `default_markline(color_idx)[1]`, each only when not None.
- **TR-24.10 `_apply_marker_opts(self, renderer, options, traits=None)` (CRITICAL; warn).**
  - `traits` is `(hollow, factor)` from the mapper. When the options carry a valid `msymbol`/`marker`, its own `symbol_traits` replace `traits`, so the user wins. When both are absent it is `(False, 1.0)`. A user `msymbol(sm*)` is therefore sized at every caller.
  - The hollow and invisible block (8766-8780) moves to the end of the method, after `malpha()` and `msangle()` (side i), and reads the resolved `hollow` (today's `_sym_raw` test is kept for the invisible names).
  - Last of all, when `factor != 1.0` and `glyph.size` is a finite number, `glyph.size = glyph.size * factor`. This runs once, after `msize()` (critic 2).
  - The docstring states the order.
- **TR-24.11 The marker sites.** In each of `map_scatter`, `map_scatteri`, `map_rscatter`, `map_pcscatter`, `map_dropline` (dot), `map_rcapsym` (two dots) and `map_pccapsym` (dots):
  - `marker, _h, _f = self._marker_traits(color_idx, options)` gives the construction `marker=`;
  - `size=` is unfactored, as today (S08's `default_marker_size`, or scatteri's own `msize()` pre-resolution);
  - `fill_color=` is the site's fill (`default_color(color_idx, <its type>)`, or the colour the site resolved from `mcolor()`/`color()`);
  - `line_color=` is `self.scheme.default_markline(color_idx)[0]`, unless the site resolved a user colour, in which case that colour;
  - the call ends with `self._apply_marker_opts(r, options, traits=(_h, _f))`.

  Alphas:
  - `map_scatter` keeps S16's `alpha=self._scheme_alpha(color_idx, "scatter")`. It adds `line_alpha=al` only when `al = default_markline(color_idx)[1]` is not None and differs.
  - The other six sites spread `**self._marker_alpha_kw(color_idx)`.
  - `map_rscatter`/`map_pcscatter` replace `color=` with `fill_color=`/`line_color=`.
  - `map_scatteri`'s local `marker = "circle"` default and its `msymbol` pre-resolution give way to `_marker_traits`.
- **TR-24.12 The histogram.** In `_histogram_quads`:
  - `_fill_base = self.scheme.histogram_color` replaces the p# colour; `color()` still overwrites it.
  - `_f = self.scheme.histogram_intensity` replaces S16's `1.0`, or Q1(b)'s `p_bar_intensity`.
  - `fill_color=self._blend_intensity(_fill_base, _f, self.scheme.naturally_white)`.
  - `fill_alpha=self.scheme.histogram_alpha if self.scheme.histogram_alpha is not None else 1.0`.
  - `line_color=self.scheme.histogram_line_color or _fill_base`, plus `line_alpha=0.0` when the scheme says `none` (`histogram_line_color is None`), else `line_alpha=self.scheme.histogram_line_alpha` when declared.
  - `line_width=self.scheme.histogram_line_width`.
  - `_apply_fill_opts(r, options, base=_fill_base, intensity=_f)` and `_apply_line_opts(r, options)` follow, unchanged.
  - `color_idx` no longer chooses a colour. The docstring says why (E7, two layers).
- **TR-24.13 The extractor** (`scripts/extract_scheme_truth.py`).
  1. `p_mark_colors = p_color_series("p_mark_colors", "markfill")` (736), with a comment citing `markerstyle-p#.style`; `p_markline_colors = p_color_series("p_markline_colors", "markline")` beside it, added to the output dict after `"p_mark_colors"` (1084).
  2. `color_alpha_of(out_key, keys)` beside `color_of` (678): as `color_of`, but through `c.resolve_with_opacity(tok)`, recording `opacities[f"{out_key}_opacity"] = pct`.
  3. The output dict gains, after the CI keys (1200-1222), with a comment citing the three histogram style files:
     - `"histogram_color": color_alpha_of("histogram_color", ["histogram"])`;
     - `"histogram_line_color": color_alpha_of("histogram_line_color", ["histogram_line"])`;
     - `"histogram_intensity": scalar("histogram_intensity", "intensity", ["histogram"], lambda t: resolve_intensity(r, t))`;
     - `"histogram_line_width": scalar("histogram_line_width", "linewidth", ["histogram"], lambda t: resolve_linewidth(r, t), class_default=True)`.
  4. In `expected_directives`:
     - the stub tuple `("mark", "p_mark_colors")` (1467) becomes `("markfill", "p_mark_colors"), ("markline", "p_markline_colors")`;
     - the "Fill intensities." group keeps only `intensity p`;
     - a new group after the CI group writes `color histogram` and `color histogram_line` through `_color_token(e[key], e.get(key + "_opacity"))`, plus `intensity histogram` and `linewidth histogram` (`use_name=True`).
  5. `_STUB_KEY["color"]` becomes `p\d+(line|bar|mark|markfill|markline|lineplot)`.
  6. `_RETIRED_DIRECTIVES = {("intensity", "bar"), ("intensity", "area")}`, with a comment citing register P1.2.8. `_drop_undeclared_stubs` also drops a present directive in that set (one docstring sentence), and it is reported in `removed`.

  The fixture keys `bar_alpha`/`area_alpha` stay.
- **TR-24.14 Regeneration (A152, R7).**
  - Run `python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json`. It updates all 26 `dash-<name>.scheme` and the fixture.
  - Check every pre-existing fixture key per scheme unchanged, outside `_meta.generated_utc`, `_meta.provenance`, the new keys, and `provenance`/`sources` of `p_mark_colors`, whose rule text now names `p#markfill`.
  - Check every pre-existing directive line unchanged, except the two retired lines removed, and their provenance comments.
  - Check that a second run prints `up to date` 26 times.
- **TR-24.15 Both modes; copy lists; JS.**
  - No module-level name is added, so there is no copy-list entry (R2 row S24): the new methods and class constants travel with their classes (33436).
  - Every new parser attribute comes from `_props` in `_init_properties` (E5).
  - No page script writes a glyph style, so there is no JS twin. `TestAfterAFilterMove::test_no_page_script_writes_a_glyph_style` pins that: no CustomJS code and no module-level `*_JS` string assigns `line_alpha`, `fill_alpha`, `size` or `marker`.
  - G4's two served-name guards stay green.
- **TR-24.16 The SVG layer reader.**
  - Create `scripts/svg_layer.py`, a module with no Stata import. It provides:
    - `svg_elements(path) -> list[dict]`: every drawn `<circle>`, `<rect>` (not one covering more than half the canvas), `<polygon>`, `<path>` and `<line>`, in document order, each with `kind`, `fill`, `fill_opacity`, `stroke`, `stroke_opacity`, `stroke_width` and `extent` (the stroked geometry's larger side: a circle's 2r, a rect's larger side, the bounding box of points or `d`), with colours lower-cased and opacity None when absent;
    - `marker_shape(elements) -> str | None`: `circle` (circle), `square` (rect, or a 4-point polygon with axis-aligned sides), `diamond` (a 4-point polygon whose top vertex shares the centre x), `triangle` (3 points), `x` (two diagonal lines), `plus` (two axis lines), `v` (an open 3-point path);
    - `hollow(elements) -> bool`: True when no element of the marker has a colour fill.
  - Unit tests: `test/test_svg_layer.py`, on literal SVG strings copied from E7's elements.
- **TR-24.17 Registries (A148, X.5).** In `test/function_test_map.py`, under `# WP-30 S24 (P1.4a): Scheme opacity, histogram style and symbols reach every layer (P1.4 part a)`, alphabetical:
  - `'GlyphMapper._marker_alpha_kw'`, `'GlyphMapper._marker_traits'`, `'GlyphMapper._scheme_alpha_kw'`;
  - `'OptionTranslator.symbol_traits'`;
  - `'SchemeParser._symbol_traits'`, `'SchemeParser.default_markline'`, `'SchemeParser.default_symbol_traits'`.

  Each points at its test in TDD stubs. `program_coverage_map.py` is unchanged: there is no Stata or Mata program.
- **TR-24.18 Parity (R8).** `test/test_mode_parity.py` `CORPUS` gains, after its last case:
  - `_case("sttrans fits and ranges", [plot_for("lfit"), plot_for("rspike"), plot_for("pcarrow"), plot_for("scatteri")], {"scheme": "sttrans"})`;
  - `_case("rarea, s2color", [plot_for("rarea")])`;
  - `_case("two histograms, stcolor", [plot_for("histogram"), plot_for("histogram")], {"scheme": "stcolor"})`;
  - `_case("s1mono symbol cycle", [plot_for("scatter")] * 11 + [plot_for("dropline"), plot_for("rcapsym")], {"scheme": "s1mono"})`;
  - `_case("msymbol(smcircle) msize(large)", [plot_for("scatter", {"msymbol": "smcircle", "msize": "large"})])`.

  `ALLOWED` and `_MUST_WARN` are untouched.
- **TR-24.19 Help (R3, A155).**
  - dash.sthlp's Series paragraph (3357-3378) and the "What the shipped files are" paragraph (3534-3561) only.
  - The Series paragraph gets four changes:
    1. The `p#mark` clause (3363-3365) becomes the `markfill`/`markline` sentence.
    2. The opacity clause (3367-3372, as S16 left it) says the declared opacity reaches every layer except the confidence band, and that a user colour without `%NN` keeps it.
    3. One sentence on hollow and small symbols, their measured factors, `msize()`, and the cycle on every marker type.
    4. One sentence on the histogram style.
  - The shipped-files paragraph gets three changes:
    1. The directive-count sentence ("<lo> to <hi> directives" as S15 left it, "80 to 140" at `c96facd`) becomes the measured bounds.
    2. Its carried-keys list adds the four histogram keys.
    3. The inferred-directive example ("the area intensity, which Stata resolves through a fallback") becomes the general rule, because `intensity area` is gone.
- **TR-24.20 Security (rule 1).**
  - No new text sink and no echoed user text.
  - Scheme values reach the parser through the existing bounded readers: `_color_alpha`/`_band_color` (a colour or the default, with today's warning), S16's intensity reader (finite or default) and `_bounded_lwidth` (refused aloud past `_LWIDTH_MAX_PX`).
  - A symbol name is a fixed-table lookup, and a factor comes from a fixed table.
  - The extractor and `svg_layer.py` parse files as data, with no `eval`, no `shell=True` and no network.
  - The truth block writes only under `w30_work`.

## Boundaries

- **Batch partners.** S22 owns the `dash` dispatcher's rclass return, `_dash_render_immediate`'s and `_dash_build`'s ends, `_dash_saving_parse`, and dash.sthlp's Syntax and Exporting. S23 owns `_make_figure_body`, `_generate_app_source`, `_dash_launch_app`, the trial, `_MUST_WARN`, and dash.sthlp's Server Mode. S24 edits none of them.
- **Earlier sections.** S24 reads these and does not edit them:
  - S16's `_blend_intensity`, `_apply_fill_opts`, `_fintensity_value`, `_scheme_alpha` and `intensity_truth.json`;
  - S15's chrome keys and `naturally_white`;
  - S14's caps, `_bar_extent`, rcapsym's sizes and the `dash_cap` tag;
  - S13's `_lwidth`/`_apply_line_opts`;
  - S08's `resolve_size`/`msize` branch and `_mlabel_gap_px`;
  - S07's scheme list;
  - S19's `legend_label="y"` on `map_scatteri`'s `fig.scatter(...)` (P1.16, batch 7), which TR-24.11's rewrite of that call keeps;
  - S21's three scheme keys (`numticks_g horizontal_major`/`vertical_major`, `margin twoway`) and its extractor lines, which the regeneration keeps.
- **Later sections.**
  - S33 owns `_apply_mlabel_opts`' defaults (research e), `_apply_colorvar`'s ColorBar chrome (research f), research g's unread directives (closed by disposition: retained in the parsed scheme and not noted, ratification row 4) and its extension of `scheme_layer_truth.json` (D-24g).
  - S32 owns `pstyle(p#)` on histograms and the named-style bundles.
  - S30 owns `stata_colour`.
  - S45 owns recast.
  - S49/S55 own `horizontal`.
  - P2.11 owns the lower-case shorthands, `point`, `V`, `pipe`, `arrow` and the geometry of `x`/`v` (Stata draws `x` at half the circle's extent; E7).
  - The nonselection and muted copies follow S08's brushed-copy sync (ratification row 27; batch 3, before S24), which carries a glyph's styled properties to them and keeps dash's `_NONSELECTION_ALPHA`, so a brushed-away hollow marker dims at that alpha. S24 edits neither `_dash_dim_nonselection` nor that sync.
- **Not taken (no WP-30 owner; Notes for the closeout).** twoway strokes rarea's and rbar's outlines (rarea `#1A476F` 17.28 under s2color, research t6). dash draws none.
- **Not edited:**
  - `_apply_line_opts`, `_apply_fill_opts`, `_apply_mlabel_opts`, `_apply_colorvar`, `_dash_dim_nonselection`, `_dash_stale_glyph`, `_make_figure_body`, `_generate_app_source`, `_glyph_layer_lines`' tuples;
  - dash.ado, dash_parse.mata;
  - the runner, the hygiene pins;
  - `scripts/svg_truth.py`;
  - any tracking document beyond BUGS.md and CHANGELOG.md (A145).

## Stata truth

**New SVG reader** `scripts/svg_layer.py` (TR-24.16).

**New extractor** `scripts/extract_scheme_layer_truth.do` writes the **new fixture** `test/fixtures/scheme_layer_truth.json`. The fixture needs `git add -f`, because `.git/info/exclude:58` ignores `*.json`. S33 extends it later (manifest).
- It copies S02's path-free form (R7): root `DASH_REPO`, else `c(pwd)` when it holds `dash.ado` and `test/run_all_cscripts.do`, else `exit 601` with "set DASH_REPO to the dash repository".
- Its first lines are `adopath ++ "<root>/"` and `global dash_nobrowser 1`, then `version 19`, `set graphics off`, `set more off`.
- It exits 601 with a message when `c(python_exec)` is empty.
- It writes its user schemes into a tempfile-named directory under `c(tmpdir)` and `adopath ++`s it, never into the repository:
  - `scheme-w24g.scheme`: `#include s2color`, `color pmarkfill green`, `color pmarkline blue`;
  - `scheme-w24m.scheme`: `#include s2color`, `color p1mark green`, `color pmark red`;
  - `scheme-w24f.scheme`: `#include s2color`, `color p1markfill green`, `color p1markline blue`;
  - `scheme-w24h.scheme`: `#include s2color`, `color histogram red`, `intensity histogram inten50`, `color histogram_line blue`, `linewidth histogram vthick`.
- Run from the worktree: `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh $S $WT/scripts/extract_scheme_layer_truth.do`. The log is `$S/extract_scheme_layer_truth.log`. No other section runs it (R7).

**Method.**
- Setup: `sysuse auto, clear`, `gen lo = mpg - 3`, `gen hi = mpg + 3`, `forvalues i = 1/15 { gen y`i' = mpg + `i' }`, `sort weight`.
- Each probe is `_sk_probe <id> <group> <scheme> <command>`. It runs `capture noisily twoway <command>, scheme(<scheme>) legend(off)`, records `_rc`, then `graph export "<dir>/<id>.svg", replace` when rc is 0.
- After the loop, one `python:` block:
  - imports `scripts/svg_layer.py` from the root (by path, through `sys.path`);
  - reads every SVG's `svg_elements`, minus the elements the base graph `scatter mpg weight` draws under the same scheme (axes, ticks, labels, region);
  - records each probe's elements plus, for `symbol` probes, `marker_shape`, `hollow` and the stroked `extent`;
  - derives `sm_factor[name]`, the small symbol's extent over its full symbol's, at default size and at `msize(large)`;
  - never calls Stata and never uses `shell=True`; a backtick is written `\x60`;
  - prints `scheme_layer_truth: wrote <N> probes`;
  - erases every SVG.
- The D12 stamp: `shell git -C "<root>" rev-parse HEAD > <tempfile>`, read back with `file read`, reaching python through `Macro.getLocal`.

**Probes.**

| Group | Commands (`twoway …`) | Schemes |
|---|---|---|
| opacity | each of `lfit mpg weight`, `qfit`, `lowess`, `lpoly`, `fpfit`, `mspline`, `mband`, `kdensity mpg`, `function y=x/1000, range(1760 4840)`, `lfitci`, `qfitci`, `lpolyci`, `fpfitci`, `spike mpg weight`, `rspike lo hi weight`, `rcap lo hi weight`, `rcapsym lo hi weight`, `dropline mpg weight`, `rline lo hi weight`, `rscatter lo hi weight`, `rbar lo hi rep78 if rep78<.`, `rarea lo hi weight`, `area mpg weight`, `scatteri 20 3000 30 4000`, `pci 20 3000 30 4000`, `pcspike mpg weight price length`, `pcarrow mpg weight price length in 1/5`, `pcarrowi 20 3000 30 4000`, `pcbarrow mpg weight price length in 1/5`, `pccapsym mpg weight price length in 1/5`, `pcscatter mpg weight price length`, `histogram mpg` | sttrans; `rarea` and `area` also s2color |
| opacity_user | `rspike lo hi weight, lcolor(red)`; `lfit mpg weight, lcolor(red%70)`; `rarea lo hi weight, fcolor(red)`; `histogram mpg, color(red)`; `lfitci mpg weight, pstyle(ci)`; `lfitci mpg weight, pstyle(p3)` | sttrans |
| histogram | `histogram mpg`; `(histogram mpg) (histogram trunk)` | s2color, stcolor, s1mono, s2mono, economist, s1rcolor, sttrans, stmono1 |
| histogram_opt | `histogram mpg, fcolor(red)`; `…, color(red)`; `…, lcolor(blue)`; `histogram mpg, fcolor(navy)` (stcolor); `histogram mpg` (w24h) | s2color unless named |
| symbol | `scatter y1-y15 weight in 1/3`; `scatter y1-y11 weight in 1/3, msize(large ..)` (eleven `large`); `(scatter mpg weight in 1/3) (scatter mpg weight in 4/6, msymbol(smcircle_hollow) mfcolor(red))`; `(scatter …) (scatter …, pstyle(p7) mfcolor(red))` | s1mono |
| sm | `scatter mpg weight in 1, msymbol(<name>)` and `…, msymbol(<name>) msize(large)` for the 11 small names and their full names, axes off (`xscale(off) yscale(off) plotregion(style(none))`) | s2color |
| cycle | `(scatter mpg weight) (<t>)` for `scatteri 20 3000`, `rscatter lo hi weight`, `pcscatter mpg weight price length`, `dropline mpg weight`, `rcapsym lo hi weight` | s1mono |
| mark | `scatter mpg weight in 1/3`; `(scatter mpg weight in 1/3) (scatter price weight in 1/3, yaxis(2))` | w24g, w24m, w24f |

**Fixture keys.**

```
{"_meta": {"stata_version", "born_date", "dash_commit", "extracted", "source": "scripts/extract_scheme_layer_truth.do"},
 "probes": {id: {"group", "scheme", "command", "rc",
                 "elements": [{"kind", "fill", "fill_opacity", "stroke", "stroke_opacity", "stroke_width", "extent"}],
                 "layers": [{"shape", "hollow", "extent", "fill", "stroke"}]   (symbol, cycle, mark probes; one per layer, first marker)}},
 "derived": {"sm_factor": {name: {"default": r, "large": r}}, "s1mono_hollow": [15 bools], "s1mono_extent": [15 floats]}}
```

Expected values are E7's. A difference is investigated and reported, never patched (R7). `TestTheFixture::test_meta_is_stamped` asserts the four `_meta` keys.

**Truth block** (`test/test_wp30_truth.cscript`, S24's stub). Cases go between `* ==== S24 P1.4a: Scheme opacity, histogram style and symbols reach every layer ====` and `* ==== end S24 ====`, behind the gate `local only : env WP30_ONLY` and `` if inlist("`only'", "", "S24") { ``.

The helpers go directly above S24's header, outside every gate, and declare `version 19`:
- `_s24_dash <command> <scheme>` runs `capture dash clear`, registers `dash <command>, scheme(<scheme>) name(s24g)`, then writes `dash build, saving("`w30_work'/s24.html") replace nobrowser filter(foreign, type(dropdown))` and `dash build, server saving("`w30_work'/s24_app.py") replace nobrowser filter(foreign, type(dropdown))`, and reads both in a python block: the page's Bokeh document from its embedded JSON, and the app's `make_document` on a fresh `Document` (the attach line replaced by `pass` before `exec`), as S19's `_s19_page`/`_s19_app` do. It returns, per glyph renderer in document order, `Type|marker|size|fill_color|fill_alpha|line_color|line_alpha` in `S24_SAVED`/`S24_SERVED`. It also returns `S24_SAME_AFTER` (1 when the served list is unchanged after the app's `Select` on `foreign` is set to `Foreign` and its callbacks are fired). Every file goes under `` `w30_work' `` and is erased by the case; the cases count no notes, so S22's stale-graph note (batch 8, merged first) cannot move them.
- `_s24_tw <file>` returns `svg_layer.svg_elements` summarised the same way in `S24_TW`.

Every case runs twoway and dash on one command and checks through `_w30_expect`/`_w30_done`:

| Case | Check |
|---|---|
| SK-01 | sttrans, `lfit`, `rspike`, `pcarrow … in 1/5`, `scatteri 20 3000`: twoway's strokes are 0.20; every dash glyph's `line_alpha` (and the scatteri fill) is 0.2 in both modes |
| SK-02 | `rarea lo hi weight`: s2color opaque in both, sttrans 0.2 in both |
| SK-03 | `histogram mpg` under s2color, stcolor, s1mono: twoway's fill and stroke equal dash's Quad `fill_color`/`line_color` (case-folded) in both modes |
| SK-04 | `(histogram mpg) (histogram trunk)` under s2color: one style in twoway, one in dash |
| SK-05 | s1mono `scatter y1-y15`: twoway's hollow list equals dash's `fill_alpha == 0` list; p11's extent over p1's equals dash's size ratio within 1% |
| SK-06 | `scatter …, msymbol(smcircle) msize(large)` against `msymbol(circle) msize(large)`: twoway's ratio equals dash's within 1% |
| SK-07 | s1mono `(scatter) (dropline)` and `(scatter) (rcapsym)`: twoway's second-layer shape is a diamond; dash's marker is `diamond` |
| SK-08 | w24g: twoway's fill `#008000` and stroke `#0000ff` equal dash's in both modes; w24m: twoway and dash `#1a476f` |
| SK-09 | `S24_SAME_AFTER` = 1 for SK-01's and SK-05's commands |

## TDD test stubs

**Regression tests written by 24-01** (literal twoway values from E7; red at the base). Modes come from `test_scheme_resolution._draw`/`MODES`, specs from `test_mode_parity._spec`, user schemes from `test_scheme_review_fixes._user_scheme`, and moves from `test_served_linked_views._served_doc` with `test_mode_parity._fire`.

`test/test_scheme_layer_alpha.py`:
- Test [type, mode]: under sttrans the second layer's every non-band glyph has `line_alpha` 0.2, and `fill_alpha` 0.2 where it is a marker or the rbar fill. Types: lfit, qfit, lowess, lpoly, fpfit, kdensity, function, mspline, mband, lfitci, qfitci, lpolyci, fpfitci, spike, rspike, rcap, rcapsym, dropline, rline, tsrline, rscatter, rbar, scatteri, pci, pcspike, pcarrow, pcarrowi, pcbarrow, pccapsym, pcscatter. Node: `TestSttransReachesEveryLayer::test_each_type`.
- Test [mode]: every pcarrow and pcbarrow head (`Arrow.end`/`start`) and the Arrow have `line_alpha` 0.2 — `TestSttransReachesEveryLayer::test_the_arrow_heads`.
- Test [mode]: an lfit and an lfitci with no rows (`if price > 99999`) draw their line at 0.2 — `TestSttransReachesEveryLayer::test_the_empty_fit_line`.
- Test [mode]: rarea is `fill_alpha` 1.0 under s2color and 0.2 under sttrans, equal to area's — `TestRareaFollowsArea::test_area_s_rule`.
- Test [mode]: `rspike, lcolor(red)` under sttrans is `#ff0000` at 0.2 — `TestUserColoursUnderSttrans::test_a_colour_without_pct_keeps_the_scheme_opacity`.
- Test [mode]: `lfitci, pstyle(ci)` under sttrans draws its line opaque (guard at the base, kept) — `TestTheCiLineRestyle::test_pstyle_ci_is_opaque`.
- Test [mode]: after a dropdown move (`foreign` to Foreign) the served lfit, rspike and pcarrow glyphs keep 0.2 — `TestAfterAFilterMove::test_the_served_glyphs_keep_their_opacity`.
- Test: the saved page's stale copy of a sttrans lfit (`_dash_stale_glyph`) has `line_alpha` 0.06 — `TestAfterAFilterMove::test_the_saved_stale_copy_scales_it`.
- Test [scheme]: for each of the 25 non-sttrans shipped schemes, `_scheme_alpha_kw(i, t, fill=True)` is `{}` for every i in 0..14 and t in E1's types — `TestOtherSchemesDeclareNothing::test_the_helper_is_empty`.

`test/test_histogram_scheme_style.py`:
- Test [scheme, mode]: the Quad's fill, outline, fill alpha and outline alpha are, case-folded — `TestTheSchemesHistogramStyle::test_each_scheme`:
  - s2color, economist, s1rcolor: `#cac27e`, `#d7d29e`, 1, 1;
  - stcolor: `#3191ff`, `#5faaff`;
  - s1mono, s2mono: `#808080`, `#000000`;
  - stmono1: `#8d8d8d`, `#000000`;
  - sttrans: `#1a476f`, `#1a476f`, 0.2, 0.2.

  `line_width` equals `SchemeParser(name)._bounded_lwidth("linewidth histogram", …)`.
- Test [mode]: two histogram layers under s2color have the same fill and outline — `TestTheSchemesHistogramStyle::test_two_layers_share_it`.
- Test [mode]: under s2color — `TestOptionsStillWin::test_each_option`:
  - `fcolor(red)` gives fill `#ff0000` and outline `#d7d29e`;
  - `color(red)` gives both `#ff0000`;
  - `lcolor(blue)` gives outline `#0000ff`;
  - `fcolor(navy)` under stcolor gives `#31597d`;
  - `color(red)` under sttrans gives `#ff0000` at 0.2 and 0.2.
- Test [mode]: a user scheme w24h draws `#ff8080` outlined `#0000ff` at `linewidth vthick` — `TestOptionsStillWin::test_a_user_scheme_s_histogram_keys`.
- Test [scheme, mode]: an empty histogram's Quad `line_color` is `#d7d29e` (s2color) and `#000000` (s1mono) — `TestTheEmptyHistogramKey::test_the_key_colour`.
- Test [probe, mode]: every `intensity_truth.json` probe with `"owner": "S24"` is drawn with twoway's fill — `TestStatasHistogramProbes::test_the_s24_probes`.
- Test: for all 26 schemes, `_props_scheme(SchemeParser(n)._props)` has the same six `histogram_*` attributes as `SchemeParser(n)`, and `SchemeParser.fallback()`'s equal s2color's — `TestTheParser::test_attributes_from_props_alone`.

`test/test_scheme_symbol_traits.py`:
- Test [name]: `OptionTranslator.symbol_traits` gives — `TestSymbolTraits::test_each_stata_name`:
  - `circle` (`circle`, False, 1.0); `Oh` (`circle`, True, 1.0);
  - `smcircle` (`circle`, False, 0.7071); `smcircle_hollow` (`circle`, True, 0.7071);
  - `smdiamond`, `smsquare`, `smplus` at 0.7071;
  - `smtriangle` 0.75; `smx` and `smv` 1.0;
  - lower-case `o` 1.0;
  - `bogus` raises `ValueError`.
- Test: s1mono's `p_symbol_hollow` is `[F]*6+[T]*4+[F]*5`, and `p_symbol_factor` is `[1]*10+[.7071,.7071,.7071,.75,1]` (±1e-4) — `TestTheSchemeCycle::test_s1mono_traits`.
- Test [scheme]: every colour scheme's 15 traits are `(False, 1.0)` — `TestTheSchemeCycle::test_colour_schemes_are_plain`.
- Test [mode]: s1mono with 11 scatter layers — `TestDrawnTraits`:
  - layer 7's Scatter has `fill_alpha` 0 and `line_alpha` 1 (`::test_p7_is_hollow`);
  - layer 11's `size` is `0.7071 * default_marker_size(10)` (`::test_p11_is_small`);
  - with `msize(large)` on layer 11, it is 0.7071 × the large size dash gives `msize(large)` on layer 1 (`::test_the_factor_survives_msize`).
- Test [mode]: `msymbol(O)` on s1mono's p7 is filled — `TestDrawnTraits::test_a_user_symbol_replaces_the_scheme_s` (guard).
- Test [mode]: s2color `msymbol(smcircle)` and `msymbol(smcircle) msize(large)` are 0.7071 of `msymbol(circle)` with the same `msize()` — `TestDrawnTraits::test_a_user_small_symbol`.
- Test [mode]: `msymbol(Oh) malpha(50)` has `fill_alpha` 0 and `line_alpha` 0.5; s1mono p7 with `mfcolor(red) malpha(50)` has `fill_alpha` 0 — `TestHollowStaysHollow::test_malpha_and_mfcolor`.
- Test [type, mode]: under s1mono `(scatter)(<t>)` draws `diamond` for t in scatteri, rscatter, pcscatter, dropline, rcapsym — `TestTheCycleReachesEveryMarkerType::test_the_second_layer_is_a_diamond`.
- Test [mode]: a user scheme `color p1 #111111` + `color p1mark #22aa22` draws the marker fill `#111111` — `TestMarkerColourKeys::test_p1mark_is_not_read`.
- Test [mode]: `color p1markfill #22aa22` + `color p1markline #0000ff` gives fill `#22aa22` and outline `#0000ff`; the same through `pmarkfill`/`pmarkline` on layer 2 — `TestMarkerColourKeys::test_markfill_and_markline`.

**Fixture-driven tests added by 24-04** (red at the base; their lines are appended to the failure file):
- `test/test_scheme_layer_alpha.py::TestTwowaysOpacity::test_each_probe[probe-mode]`: every `opacity`/`opacity_user` probe's stroke and fill opacities equal dash's glyph alphas. The band (`#c0c0c0`) and the axis elements are excluded.
- `test/test_scheme_layer_alpha.py::TestTheFixture::test_meta_is_stamped`.
- `test/test_histogram_scheme_style.py::TestTwowaysHistogram::test_each_probe[probe-mode]`: fill, opacity, stroke and stroke opacity.
- `test/test_scheme_symbol_traits.py::TestTwowaysSymbols::test_each_probe[probe-mode]`:
  - `layers[*].hollow` equals dash's `fill_alpha == 0`;
  - `shape` maps to Bokeh's marker (`circle`, `diamond`, `square`, `triangle`, `x`, `plus`);
  - the extent ratios against p1 equal dash's size ratios within 1%;
  - `derived.sm_factor` equals `_SMALL_SYMBOL_FACTOR` within 1%.

**Added by 24-05:** `test/test_emptied_layer_style.py::TestTheKeyIsTwoways::test_the_empty_layer_draws_in_twoways_key_colour[s2color-histogram]` and `[s1mono-histogram]`.

**Unit tests (green after their task):**
- `test/test_svg_layer.py::TestSvgElements::test_each_kind`;
- `::TestMarkerShape::test_each_shape`;
- `::TestHollow::test_stroke_only`.

**Guard tests (green before and after):**
- `TestTheCiLineRestyle::test_pstyle_ci_is_opaque`;
- `TestDrawnTraits::test_a_user_symbol_replaces_the_scheme_s`;
- `TestSttransReachesEveryLayer::test_the_band_is_unchanged` (lfitci's VArea `#c0c0c0` at 1.0 under sttrans, both modes);
- `TestAfterAFilterMove::test_no_page_script_writes_a_glyph_style`;
- `TestOtherSchemesDeclareNothing::test_drawn_alphas_are_one[type-scheme]` (s2color, stcolor, s1mono: every glyph of E1's types other than rarea and histogram has line and fill alpha 1.0, except rbar's `line_alpha` 0 and hollow fills).

**Pinned tests to flip:** E9's table.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Opacity on ~30 types, heads, empty fits, user colours, pstyle | pytest `test_scheme_layer_alpha.py` | `scheme_layer_truth.json` (opacity, opacity_user) | yes, and the served move |
| Stale copy on the saved page | pytest | — | saved |
| No page script writes a style | pytest | — | saved (scripts), served (no JS) |
| rarea rule | pytest; cscript SK-02 | opacity probes | yes |
| Histogram style, options, empty key | pytest `test_histogram_scheme_style.py`, `test_emptied_layer_style.py`; cscript SK-03/04 | histogram probes; `intensity_truth.json` S24 probes; `emptied_layer_truth.json` | yes |
| Symbol traits, factor, msize, hollow, cycle | pytest `test_scheme_symbol_traits.py`; cscript SK-05/06/07 | symbol, sm, cycle probes | yes |
| Mark colour keys | pytest; cscript SK-08 | mark probes | yes |
| Extractor, regeneration | pytest `test_scheme_fidelity.py` (regeneration no-op, older translation, property fidelity) | `scheme_truth.json` | — |
| Parser from `_props` | pytest `TestTheParser`, `test_scheme_fallback_provenance.py` | — | served rebuild |
| Parity | `python3 -m pytest test/test_mode_parity.py -q -n0` (G3) | — | yes |
| Registries, served names | `test_function_test_map.py`, `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads` (G4) | — | — |
| Truth | `test_wp30_truth.cscript` with `WP30_ONLY=S24` through the driver | live twoway | yes |
| Whole suite | one full run through the queue (E1) | — | — |

**Acceptance criteria.**
- **AC-24.1** Every regression test of 24-01, 24-04 and 24-05 failed at the base, with the text saved, and passes after the fix. The guards pass at the base and after.
- **AC-24.2** Under sttrans, every glyph of E1's types carries 0.2 in both modes and after a served move, the band excepted. SK-01, SK-02 and SK-09 print PASS.
- **AC-24.3** Every histogram probe matches twoway's fill, outline and opacities in both modes. An emptied histogram's key matches. SK-03 and SK-04 print PASS.
- **AC-24.4** s1mono's traits, the measured `sm*` factors (within 1%, `msize()` included) and the symbol cycle on the five types match twoway. SK-05 to SK-07 print PASS.
- **AC-24.5** `color p#mark` is not read, and `p#markfill`/`p#markline` are. SK-08 prints PASS.
- **AC-24.6** The 26 regenerated files and `scheme_truth.json` keep every pre-existing record and directive (TR-24.14's exceptions only). A second extractor run prints `up to date` 26 times.
- **AC-24.7** E9's flips each carry a `Flipped:` line, and no test is deleted. G3, G4, the registries and one full run are green.

## Tasks

**Commit boundary.** Tasks 24-01 to 24-19 form the one commit of entry `P1.4a`, subject `Carry the scheme's opacity, histogram style and symbols to every layer (WP-30 P1.4a)`.
- It is made by 24-19 on `wp30-s24` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s24` (`$WT`), after one full run through the queue.
- `$S` is `<scratch>/s24` (`<scratch>`: the orchestrator's WP-30 scratch directory, index "Deltas"). Every command runs from `$WT` unless it names the main checkout.
- The body:
  1. opens with `<scratch>/24-P1.4a-failure.txt`;
  2. then the measured defect (E6) and what changed, where, in both modes;
  3. then one line each:
     - `Regression: test/<file>.py::<Class>::<test> -- failed at <batch-8 base sha> with <text>`, one per regression class;
     - `Flipped: <node> -- <old expectation> was wrong because <why>`, every E9 row and every line of `$S/24-flips.txt`;
     - `Fixture: test/fixtures/scheme_layer_truth.json (scripts/extract_scheme_layer_truth.do)`;
     - `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`;
     - `BUGS.md: "The scheme's opacity, histogram colour, intensity and width, and its hollow and sm symbols do not reach fits, spikes, ranges, immediates, histograms or rarea" (closed)` (section-01 Appendix B's title, verbatim; 24-19 checks it equals `WP30_OPEN["P1.4a"]`);
     - a `Rebaselined:` line only if the single-y digest moved (R10).

No subject, body, BUGS line, CHANGELOG line or help line names a tool or vendor (G7). `grep -Eic 'claude|anthropic'` prints 0 on the message file before committing and on `git log -1 --format=%B` after. Never stage `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.ultraplan/` or any `*.html` (E7, G6).

<task type="auto" id="24-01">
  <name>Write the failing scheme reach regression tests</name>
  <files>test/test_scheme_layer_alpha.py, test/test_histogram_scheme_style.py, test/test_scheme_symbol_traits.py</files>
  <action><![CDATA[
    Run `mkdir -p "$S"`. Check that `git -C $WT rev-parse HEAD` equals `<scratch>/batch-8-base.txt` and that `git -C $WT branch --show-current` prints `wp30-s24`; otherwise stop. Read `<scratch>/batch-8-impact.txt` and confirm it records the CRITICAL warnings for `_apply_marker_opts` and `_empty_fit_line` and the HIGH ones for `_scheme_alpha`, `_render_ci_band`, `_ci_line_restyle` and `_add_arrow_heads`, with approval (index 8.0). For any missing symbol, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout (never in $WT), append it and report before editing. Check S16's state with `grep -nE 'def _scheme_alpha\(self, color_idx: int, plot_type: str\)|def _blend_intensity|_fill_base' $WT/dash_render.py`, `test -f $WT/test/fixtures/intensity_truth.json` and `grep -n 'class TestTheHistogramUntilS24' $WT/test/test_intensity_blend.py`; if any is missing or renamed, stop and report (S16 owns them). Create the three files with every test of "TDD test stubs / Regression tests written by 24-01", using exactly those class and test names, the helpers named there, and expectations written as twoway's literal values from Evidence E7 (sizes as ratios to `default_marker_size`, widths compared with `SchemeParser`, never literals). Run `python3 -m pytest test/test_scheme_layer_alpha.py test/test_histogram_scheme_style.py test/test_scheme_symbol_traits.py -q -n0 -p no:cacheprovider -rf > "$S/24-01.log" 2>&1`. Write `<scratch>/24-P1.4a-failure.txt` with the base sha, then each FAILED line with its first assertion text, then the guard tests under "Guard tests (pass before and after)". Do not touch dash_render.py, and do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/24-01.log"` prints at least 60; `grep -E '^FAILED.*(pstyle_ci_is_opaque|replaces_the_scheme_s|band_is_unchanged|writes_a_glyph_style|drawn_alphas_are_one)' "$S/24-01.log"` prints nothing; `test -s <scratch>/24-P1.4a-failure.txt`.]]></verify>
  <done>Every 24-01 regression test existed with twoway's literal values and failed on the unfixed tree, the guards passed, and the failure text was saved.</done>
</task>

<task type="auto" id="24-02">
  <name>Add the SVG layer reader and tests</name>
  <files>scripts/svg_layer.py, test/test_svg_layer.py</files>
  <action><![CDATA[
    Create scripts/svg_layer.py per TR-24.16: `svg_elements(path)`, `marker_shape(elements)` and `hollow(elements)`. Parse with `re` over the file text, no Stata import, no network; lower-case every colour; opacity None when absent; extent of the stroked geometry. Create test/test_svg_layer.py with `TestSvgElements::test_each_kind`, `TestMarkerShape::test_each_shape` (circle, square, diamond, triangle, x, plus, v from E7's literal elements) and `TestHollow::test_stroke_only`, writing the SVGs into `tmp_path`. Run the file.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_svg_layer.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The SVG layer reader existed with unit tests for every function.</done>
</task>

<task type="auto" id="24-03">
  <name>Extract the scheme layer truth from Stata</name>
  <files>scripts/extract_scheme_layer_truth.do, test/fixtures/scheme_layer_truth.json</files>
  <action><![CDATA[
    Create scripts/extract_scheme_layer_truth.do exactly as "Stata truth" specifies: S02's root rule; `adopath ++ "<root>/"` and `global dash_nobrowser 1` first; `version 19`; the four user schemes written with `file write` into a tempfile-named directory under c(tmpdir) that is then `adopath ++`-ed; `_sk_probe`; every probe of the table; the D12 stamp; and one trailing python block that imports scripts/svg_layer.py, never calls Stata, never uses shell=True, writes a backtick as \x60 and erases the SVGs. Run `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_scheme_layer_truth.do"` and read `$S/extract_scheme_layer_truth.log`. Check the fixture against E7: every sttrans opacity probe at 0.2; the band `#c0c0c0` with no opacity; s2color histogram `#cac27e`/`#d7d29e`; stcolor `#3191ff`/`#5faaff`; `derived.sm_factor.smtriangle.default` near 0.751 and `smx` 1.0; `s1mono_hollow` `[F]*6+[T]*4+[F]*5`; w24g `#008000`/`#0000ff`. A difference is investigated and reported, never patched (R7). Run `git add -f test/fixtures/scheme_layer_truth.json`.
  ]]></action>
  <verify><![CDATA[`grep -c '^r(' "$S/extract_scheme_layer_truth.log"` prints 0; `grep -q 'scheme_layer_truth: wrote' "$S/extract_scheme_layer_truth.log"`; `python3 -c "import json;d=json.load(open('test/fixtures/scheme_layer_truth.json'));m=d['_meta'];assert all(m.get(k) for k in ('stata_version','born_date','dash_commit','extracted'));print(len(d['probes']))"` prints the probe count.]]></verify>
  <done>scheme_layer_truth.json was written from live twoway exports, stamped and staged with git add -f.</done>
</task>

<task type="auto" id="24-04">
  <name>Add the fixture-driven truth tests</name>
  <files>test/test_scheme_layer_alpha.py, test/test_histogram_scheme_style.py, test/test_scheme_symbol_traits.py</files>
  <action><![CDATA[
    Append the classes of "Fixture-driven tests added by 24-04" to the three files: `TestTwowaysOpacity`, `TestTheFixture`, `TestTwowaysHistogram` and `TestTwowaysSymbols`. Each is parametrised over the fixture's probes of its groups and both modes, and builds dash's spec for the same command through `test_mode_parity._spec` and `plot_for`. Run them on the still unmodified renderer with `-rf > "$S/24-04.log" 2>&1`, and append their FAILED lines to `<scratch>/24-P1.4a-failure.txt` under "Fixture-driven".
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/24-04.log"` prints at least 20; `test_meta_is_stamped` passes; `git -C $WT diff --stat -- dash_render.py` prints nothing.]]></verify>
  <done>The twoway truth tests existed, failed on the unfixed renderer and were recorded.</done>
</task>

<task type="auto" id="24-05">
  <name>Include the histogram in the emptied-key test</name>
  <files>test/test_emptied_layer_style.py</files>
  <action><![CDATA[
    In `_key_cases` (:108-116) remove `t == "histogram" or` from the skip test, so the s2color and s1mono histogram probes are collected. The comparison already reads `line_color` for any glyph that is not VArea/VBar; add one comment line saying a Quad's key is its outline. Run `python3 -m pytest test/test_emptied_layer_style.py -q -n0 -p no:cacheprovider -rf -k histogram > "$S/24-05.log" 2>&1` and append the two FAILED lines to the failure file under "Emptied key". Record `Flipped: test/test_emptied_layer_style.py::_key_cases -- the histogram was skipped because its key colour was left to P1.4 (WP-29 S12)` in `$S/24-flips.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED.*histogram' "$S/24-05.log"` prints 2.]]></verify>
  <done>The emptied histogram's key was under test and shown failing on the unfixed tree.</done>
</task>

<task type="auto" id="24-06">
  <name>Teach the extractor the new keys</name>
  <files>scripts/extract_scheme_truth.py, test/test_scheme_fidelity.py</files>
  <action><![CDATA[
    Make TR-24.13's six changes in scripts/extract_scheme_truth.py. In test/test_scheme_fidelity.py:
    - change `COLOR_LISTS["p_mark_colors"]` (:214) to `["color p{i}markfill", "color pmarkfill", "color p{i}", "color p"]` and add `"p_markline_colors": ["color p{i}markline", "color pmarkline", "color p{i}", "color p"]`;
    - add `test_the_histogram_keys_are_resolved` (parametrised over the 26 names: `extract()` gives a hex `histogram_color` and `histogram_line_color`, an intensity dict and a line-width dict; sttrans' opacity is 20);
    - add `test_the_retired_intensities_are_dropped` (an older translation carrying `intensity bar full` and `intensity area full` loses both through `update_scheme_file`, and a second run changes nothing);
    - if `ALPHA_SCALARS` still lists `bar_alpha`/`area_alpha`, remove those two rows and record the flip in `$S/24-flips.txt`.
    Do not regenerate yet.
  ]]></action>
  <verify><![CDATA[`python3 -c "import sys;sys.path.insert(0,'scripts');import extract_scheme_truth as x;e=x.extract(x.DEFAULT_STATA_BASE,'stcolor');print(e['histogram_color'],e['histogram_line_color'],e['histogram_intensity']['name'],e['histogram_line_width']['name'])"` prints `#1a85ff #5faaff inten90 vthin`; `python3 -m pytest test/test_scheme_fidelity.py -q -n0 -p no:cacheprovider -k "histogram_keys or retired"` passes.]]></verify>
  <done>The extractor resolved the histogram keys and the markfill and markline chains, and retired graph bar's two intensities.</done>
</task>

<task type="auto" id="24-07">
  <name>Regenerate the 26 shipped scheme files</name>
  <files>dash-*.scheme (the 26), test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    Run TR-24.14's command. Write the two checks to `$S/regen_check.py` and save their output to `$S/regen_check.txt`:
    - the fixture comparison against `git show HEAD:test/fixtures/scheme_truth.json`, with TR-24.14's allowed differences;
    - the directive comparison per file, with only the two retired lines removed.
    Run the extractor a second time, writing `> "$S/regen2.log" 2>&1`, and confirm `up to date` 26 times. Run `git add -f test/fixtures/scheme_truth.json`. Generated files are never hand-edited (R7).
  ]]></action>
  <verify><![CDATA[`grep -l '^color histogram ' dash-*.scheme | wc -l` prints 26; `grep -lE '^intensity (bar|area) ' dash-*.scheme | wc -l` prints 0; `grep -c 'up to date' "$S/regen2.log"` prints 26; `$S/regen_check.txt` ends `unchanged: 26 schemes`.]]></verify>
  <done>The 26 shipped files and scheme_truth.json carried the histogram keys and lost the two retired intensities, with every other record unchanged.</done>
</task>

<task type="auto" id="24-08">
  <name>Give the parser traits, marks and histogram</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Make TR-24.8 in `SchemeParser` and `_FALLBACK_PROPS`. For the histogram intensity, use the unclamped reader S16 added (`grep -n 'def _intensity' dash_render.py`); if its signature is not `(key, default, clamp=...)`, use S16's form exactly as S16's `p_bar_intensity` line does. Add `SchemeParser._symbol_traits`, `SchemeParser.default_markline` and `SchemeParser.default_symbol_traits` to function_test_map.py under S24's anchor (TR-24.17). Run `test_scheme_symbol_traits.py -k "TheSchemeCycle or MarkerColourKeys"`, `test_histogram_scheme_style.py -k TheParser`, `test_scheme_fallback_provenance.py` and `test_scheme_fidelity.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_fallback_provenance.py test/test_scheme_fidelity.py -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_scheme_symbol_traits.py -q -n0 -p no:cacheprovider -k "test_s1mono_traits or colour_schemes_are_plain"` passes; `python3 -m pytest test/test_histogram_scheme_style.py -q -n0 -p no:cacheprovider -k test_attributes_from_props_alone` passes.]]></verify>
  <done>SchemeParser carried symbol traits, markfill and markline colours and the histogram style, all from its property dict, and the fallback still mirrored s2color.</done>
</task>

<task type="auto" id="24-09">
  <name>Add symbol traits and the marker applier</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Warn first: `_apply_marker_opts` is CRITICAL (12 impacted, 7 direct). Make TR-24.7 (`_SMALL_SYMBOL_FACTOR`, `symbol_traits`), TR-24.9 (`_marker_traits`, `_marker_alpha_kw`) and TR-24.10. TR-24.10 adds the `traits=None` keyword and moves the hollow and invisible block after `malpha()`/`msangle()`, so it runs at the end of the method followed by the one size multiplication. No other branch of `_apply_marker_opts` changes. Add the three function_test_map.py entries (TR-24.17). Run `test_scheme_symbol_traits.py -k "SymbolTraits or HollowStaysHollow or a_user_small_symbol"`, `test_graph_options.py` and `test_glyphs.py -k "marker or msymbol or msize or malpha"`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_symbol_traits.py -q -n0 -p no:cacheprovider -k "SymbolTraits or HollowStaysHollow or a_user_small_symbol"` passes; `python3 -m pytest test/test_graph_options.py test/test_glyphs.py -q -n0 -p no:cacheprovider -k "marker or msymbol or msize or malpha"` passes.]]></verify>
  <done>Symbol traits existed, and _apply_marker_opts drew hollow symbols hollow after malpha() and small ones at the measured factor after msize().</done>
</task>

<task type="auto" id="24-10">
  <name>Pass the opacity to lines and fits</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Warn first: `_empty_fit_line` is CRITICAL (8), and `_render_ci_band` and `_ci_line_restyle` are HIGH. Add `_scheme_alpha_kw` (TR-24.1) and its function_test_map.py entry. Make TR-24.2 at every line site of E1's table (`_empty_fit_line`, `map_lfit`, `map_qfit`, the three no-rows CI lines, `map_lowess`, `map_lpoly`, `map_fpfit`, `map_kdensity`, `map_mspline`, `map_mband`, both `map_function` lines, both `map_rline` lines, `_render_ci_band` and its four callers) and TR-24.3 in `_ci_line_restyle`. Run `test_scheme_layer_alpha.py -k "lfit or qfit or lowess or lpoly or fpfit or kdensity or function or mspline or mband or rline or empty_fit or CiLineRestyle"` and `test_ci_band_style.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_layer_alpha.py -q -n0 -p no:cacheprovider -k "lfit or qfit or lowess or lpoly or fpfit or kdensity or function or mspline or mband or rline or empty_fit or CiLineRestyle"` passes; `python3 -m pytest test/test_ci_band_style.py test/test_emptied_layer_style.py -q -n0 -p no:cacheprovider -k "not histogram"` passes.]]></verify>
  <done>Every fit, smooth, function and range line carried the scheme's declared opacity at construction, and _ci_line_restyle had the last word under pstyle().</done>
</task>

<task type="auto" id="24-11">
  <name>Pass the opacity to segments and fills</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn first: `_add_arrow_heads` is HIGH. Make TR-24.4 (spike, rspike, rcap spine and caps, dropline segment, rcapsym spine, pcspike, pcarrow and pcbarrow shafts, pccapsym segment, rbar fill), TR-24.5 (heads) and TR-24.6 (rarea's area rule). Before editing map_rcap, confirm with `grep -n 'dash_cap' dash_render.py` that S14's caps are Scatter glyphs; if they are still Segments, give them `line=True` only and record that in `$S/24-notes.txt`. Run `test_scheme_layer_alpha.py -k "spike or rcap or dropline or pc or rbar or scatteri or arrow or Rarea or UserColours"`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_layer_alpha.py -q -n0 -p no:cacheprovider -k "spike or rcap or dropline or pc or rbar or arrow or Rarea or UserColours"` passes.]]></verify>
  <done>Every segment, cap, arrow head and range fill carried the declared opacity, and rarea followed area's rule.</done>
</task>

<task type="auto" id="24-12">
  <name>Draw the cycle and mark colours on markers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-24.11 at the seven marker sites: `map_scatter`, `map_scatteri`, `map_rscatter`, `map_pcscatter`, `map_dropline`'s dot, `map_rcapsym`'s two dots and `map_pccapsym`'s dots. Each call to `_apply_marker_opts` passes `traits=(_h, _f)`. Keep every size unfactored at construction (the factor is applied once, in `_apply_marker_opts`). If S08's `_apply_mlabel_opts` calls at these sites pass a marker radius computed from `default_marker_size`, pass the glyph's final `r.glyph.size` instead, and note it in `$S/24-notes.txt`; `_apply_mlabel_opts` itself is not edited (R12). Run `test_scheme_symbol_traits.py` and `test_scheme_layer_alpha.py -k "scatteri or rscatter or pcscatter or dropline or rcapsym or pccapsym"`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_symbol_traits.py -q -n0 -p no:cacheprovider -k "not Twoways"` passes; `python3 -m pytest test/test_scheme_layer_alpha.py -q -n0 -p no:cacheprovider -k "scatteri or rscatter or pcscatter or dropline or rcapsym or pccapsym"` passes.]]></verify>
  <done>Every marker type took the scheme's symbol cycle, its traits and its markfill and markline colours.</done>
</task>

<task type="auto" id="24-13">
  <name>Draw histograms in the scheme's histogram style</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-24.12 in `_histogram_quads`, keeping S16's `_apply_fill_opts(r, options, base=_fill_base, intensity=_f)` call and `_apply_line_opts`. Update its docstring. Run `test_histogram_scheme_style.py`, `test_emptied_layer_style.py` and `test_intensity_blend.py -k "not UntilS24"`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_histogram_scheme_style.py test/test_emptied_layer_style.py -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_intensity_blend.py -q -n0 -p no:cacheprovider -k "not UntilS24"` passes.]]></verify>
  <done>Every histogram layer and an emptied histogram's key were drawn in the scheme's histogram style with user options still winning.</done>
</task>

<task type="auto" id="24-14">
  <name>Re-measure and flip the first pins</name>
  <files>test/test_help_claims_8.py, test/test_scheme_review_fixes.py, test/test_varlist_expansion.py</files>
  <action><![CDATA[
    Run the three new test files plus every test file that greps for `histogram`, `rarea`, `sttrans`, `p1mark`, `symbol`, `Quad`, `alpha` or `scheme` (`grep -lE` over test/*.py), with `-n 6 -p no:cacheprovider -rf > "$S/24-red.log" 2>&1`. Write each failure that is a pinned old behaviour to `$S/24-flips.txt` as a `Flipped:` line; any other failure is a defect to fix in the code, not a flip.
    In test_help_claims_8.py:
    - rename `test_the_colour_but_not_the_opacity` to `test_the_colour_and_the_opacity` and invert it per E9, keeping lfitci's band at `#c0c0c0` 1.0;
    - add `test_the_help_says_where_it_stops`: the help has no "not yet its opacity" and names the confidence band as the exception;
    - rename `test_80_to_140_directives` to `test_the_directive_count_is_what_the_help_says`, with bounds equal to the measured minimum and maximum over the 26 files rounded outward to the nearest ten, and a docstring giving the measured counts and why they moved (S15's chrome keys, S24's histogram keys, the two retired intensities).
    In test_scheme_review_fixes.py, flip `TestMarkColourIsForMarkers` per E9: `color p1mark` is now ignored (markers draw `LINE`), plus a second scheme line pair `color p1markfill`/`color p1markline` checked on fill and outline.
    Run test_varlist_expansion.py; if the single-y digest moved, re-derive it (R10) with a trailing comment naming P1.4a and the reason, and write the `Rebaselined:` line to `$S/24-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_8.py test/test_scheme_review_fixes.py test/test_varlist_expansion.py -q -n0 -p no:cacheprovider` passes once 24-18's help edit lands (run again then); `grep -c '^Flipped:' "$S/24-flips.txt"` prints at least 4.]]></verify>
  <done>The red list was re-measured and the help-claims, mark-colour and digest pins were flipped with their reasons recorded.</done>
</task>

<task type="auto" id="24-15">
  <name>Flip the rarea and histogram pins</name>
  <files>test/test_html_output.py, test/test_glyphs.py, test/test_intensity_blend.py</files>
  <action><![CDATA[
    Flip, per E9 and `$S/24-red.log`:
    - `TestOutputBackendAndVisualMarkers::test_rarea_varea_glyph_has_fill_attributes` (`fill_alpha` `[1.0]*20`, comment: area's rule, twoway's rarea is opaque);
    - `TestHardeningGuards::test_histogram_empty_source_keeps_the_scheme_style` (compare with the scheme's histogram fill);
    - `TestTheHistogramUntilS24::test_s2color_keeps_the_full_colour` (the default is `#cac27e`, `fcolor(navy)` stays `#1a476f`; rename the class `TestTheHistogramIntensity` only if the node name is not referenced elsewhere, `grep -rn UntilS24 test/`).
    Flip any other row of `$S/24-red.log` in these three files the same way. Add every `Flipped:` line to `$S/24-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_html_output.py test/test_glyphs.py test/test_intensity_blend.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>The rarea opacity and histogram colour pins expected twoway's values, each with its reason recorded.</done>
</task>

<task type="auto" id="24-16">
  <name>Extend the key lists and parity corpus</name>
  <files>test/test_scheme_consumption.py, test/test_scheme_resolution.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    In test_scheme_consumption.py:
    - add `histogram_color`, `histogram_line_color`, `histogram_intensity`, `histogram_line_width`, `p_symbol_hollow`, `p_symbol_factor` and `p_markline_colors` to `test_the_key_is_read_somewhere`'s list (:594);
    - add `"p_markline_colors"` to the cycle loop at :1546.
    In test_scheme_resolution.py, add `"p_markline_alphas": "p_markline_colors_opacity"` to `ALPHA_LISTS` (:542) and one `p_markline_alphas` assertion to `test_a_cycle_declares_its_own_opacity`.
    Append TR-24.18's five `CORPUS` cases to test_mode_parity.py. Then run the remaining rows of `$S/24-red.log` in any other file and fix or flip them as 24-14 says.
    Run G3 (`python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider`) and G4.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py test/test_scheme_consumption.py test/test_scheme_resolution.py -q -n 6 -p no:cacheprovider` passes; `python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The parser-key lists and the parity corpus covered the new attributes and looks, and both modes drew the same.</done>
</task>

<task type="auto" id="24-17">
  <name>Fill the S24 truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Write the helpers `_s24_dash` and `_s24_tw` directly above S24's header line, outside every gate, each declaring `version 19`. Write cases SK-01 to SK-09 of "Stata truth" between S24's start and end display lines. Files go only under `` `w30_work' `` and are erased before the end line. The python helpers import scripts/svg_layer.py by path, pass every value through `Macro.setLocal`, never inline user text into Python source and never use shell=True. Write the driver `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_truth.do"` and run `WP30_ONLY=S24 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_truth.do"`.
  ]]></action>
  <verify><![CDATA[`grep -c '^SK-0[1-9] PASS' "$S/run_truth.log"` prints 9; `grep -q 'ALL CHECKS PASSED' "$S/run_truth.log"`; `grep -c 'FAIL' "$S/run_truth.log"` prints 0; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider -k Wp30` passes.]]></verify>
  <done>The S24 truth block compared twoway's SVG with dash's saved page and served app on nine cases and every case passed.</done>
</task>

<task type="auto" id="24-18">
  <name>Update the scheme support help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Edit only the Series paragraph (3357-3378) and "What the shipped files are" (3534-3561), as TR-24.19 says, using the text of Notes, "Text for the closing task / dash.sthlp", rewritten around whatever S15 and S16 left in those paragraphs (keep their sentences; R3). The directive bounds are the ones 24-14 measured. Check the SMCL with `grep -n '{cmd:p}{it:#}{cmd:mark}' dash.sthlp`, which must print only the markfill/markline sentence. Run test_help_claims_8.py, test_help_claims_1.py and test_help_claims_7.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_8.py test/test_help_claims_1.py test/test_help_claims_7.py -q -n 6 -p no:cacheprovider` passes; `grep -c 'not yet its opacity' dash.sthlp` prints 0; `grep -c '80 to 140' dash.sthlp` prints 0.]]></verify>
  <done>The help described opacity on every layer, the histogram style, the symbol traits and the marker colour keys, with the measured directive count.</done>
</task>

<task type="auto" id="24-19">
  <name>Close P1.4a and commit the section</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP30_OPEN["P1.4a"]`. Close that BUGS.md entry in place: `- [ ]` becomes `- [x]`, and its open `  - Resolution:` line is replaced by the Resolution in Notes, keeping the indentation. Delete the `"P1.4a"` key line from `WP30_OPEN`. In CHANGELOG.md, replace the `<!-- WP-30 P1.4a -->` marker in `### Results that change` with the lines in Notes, each ending `(WP-30, P1.4a)` (R4). Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.
    Then run `git -C $WT merge --no-edit main` and expect `Already up to date.`; otherwise stop and report (E9). Then make one full run through the queue: `<scratch>/full_suite_queue.sh $WT <scratch>/24-full-1.log`, launched in the background and waited for on its `exit=` line, never relaunched (E1; E6 for the known flaky tests).
    Stage exactly these, plus `git add -f` on test/fixtures/scheme_layer_truth.json and test/fixtures/scheme_truth.json:
    - dash_render.py, dash.sthlp, BUGS.md, CHANGELOG.md;
    - the 26 dash-*.scheme files;
    - scripts/extract_scheme_truth.py, scripts/extract_scheme_layer_truth.do, scripts/svg_layer.py;
    - the five new test files, test/function_test_map.py, test/test_tracking_documents.py, test/test_wp30_truth.cscript;
    - the flipped and extended files of 24-05 and 24-14 to 24-16, and any file named in `$S/24-flips.txt`.
    Check `git diff --cached --name-status` (G6). Write the message to `$S/24-msg.txt` per the commit boundary and run G7 on it. Confirm `git -C $WT branch --show-current` prints `wp30-s24`. Commit with `git commit -F "$S/24-msg.txt"`, run G7 on `git log -1 --format=%B`, and report the sha and the message path to the merger.
  ]]></action>
  <verify><![CDATA[`grep -E '^exit=0' <scratch>/24-full-1.log` matches and its summary shows 0 failed; `git log -1 --format=%s` ends `(WP-30 P1.4a)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.4a -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.4a": "' test/test_tracking_documents.py` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.4a was closed naming tests that exist, its CHANGELOG marker carried the measured old and new values, and the section's one green commit on wp30-s24 was ready for the merger.</done>
</task>

## Section completion criteria

- In both modes, before and after a served filter move, all of the following hold:
  - a declared scheme opacity reaches every line, segment, cap, arrow head, marker and range fill of the ~30 types in E1, the CI band excepted;
  - `_ci_line_restyle` has the last word;
  - rarea follows area's rule;
  - every histogram layer and an emptied histogram's key take the scheme's histogram style, with options winning;
  - hollow and small symbols are drawn by the measured traits, after `msize()`, from the scheme or `msymbol()`;
  - the cycle reaches the five marker types;
  - markers read `p#markfill`/`p#markline`;
  - `msymbol(Oh) malpha()` stays hollow.
- `scheme_layer_truth.json` is new, stamped and staged with `git add -f`. `scheme_truth.json` and the 26 files are regenerated, never hand-edited, and a second run is a no-op. SK-01 to SK-09 print PASS.
- The new functions have their `function_test_map.py` entries. No copy-list entry is added. G3 and G4 are green.
- Every E9 row and every `$S/24-flips.txt` line is flipped with a `Flipped:` line, and no test was deleted.
- One green commit `(WP-30 P1.4a)` exists on `wp30-s24`, carrying the failure text and the `Regression:`, `Flipped:`, `Fixture:` and `BUGS.md:` lines. The BUGS.md entry is closed in place, `WP30_OPEN` lost only `"P1.4a"`, and the marker is replaced.
- Not edited: `_apply_line_opts`, `_apply_fill_opts`, `_apply_mlabel_opts`, `_apply_colorvar`, `_make_figure_body`, `_generate_app_source`, `_dash_dim_nonselection`, the copy lists, dash.ado, dash_parse.mata, `scripts/svg_truth.py`, any runner block or hygiene pin, any tracking document beyond BUGS.md and CHANGELOG.md.

## Notes

### Traps for the executor

- **The served state comes from `_props` alone.** Every new `SchemeParser` attribute must be assigned in `_init_properties`. An attribute set in `__init__`, `_parse_lines` or `_include` exists in the saved renderer and not in the served app or `fallback()`. `TestTheParser::test_attributes_from_props_alone` catches it.
- **Opacity kwargs only when declared** (D-24a). Writing `line_alpha=1.0` explicitly changes the serialised page of 25 schemes. `TestOtherSchemesDeclareNothing` and the single-y digest catch it.
- **The factor is applied once.** Never multiply at construction and again in `_apply_marker_opts`. `map_scatteri` pre-resolves `msize()` at construction, and `_apply_marker_opts` resolves it again before multiplying, so the value is right only because construction sizes stay unfactored.
- **`_ci_line_restyle` runs after construction**, so the construction alpha is overwritten under `pstyle()`. Assign only when the value differs.
- **S16's names.** Read `_scheme_alpha`'s two-argument form, `_blend_intensity(hex, f, naturally_white)`, `_apply_fill_opts(…, base=, intensity=)` and the unclamped intensity reader as they are at the base. If S16's Q1 was answered (b), `_histogram_quads`' `_f` is `p_bar_intensity` at the base and becomes `histogram_intensity`.
- **Shared files** (index merge rules):
  - `test_mode_parity.py` CORPUS appends (R8; S23 appends too, merge order S22, S23, S24);
  - `test/function_test_map.py` under S24's own anchor (R2);
  - `test_wp30_truth.cscript` inside S24's block only (R1);
  - BUGS.md, `WP30_OPEN` and CHANGELOG own lines only (R4, R5);
  - dash.sthlp's two scheme-support paragraphs only (R3);
  - the 26 files and `scheme_truth.json`: regenerated last in the batch, a conflict re-run, never hand-merged (R7, A152);
  - `_apply_marker_opts` (R12).
- **Python and Stata.** Stata runs only through `scripts/stata_slot.sh`. The fixture's python block never calls back into Stata. `~/.stata19/console/stata19.rc` keeps the maintainer's `python_exec` (E12).
- **Commit-body line forms:**
  - `Regression: test/test_scheme_layer_alpha.py::TestSttransReachesEveryLayer::test_each_type -- failed at <sha> with <text>`;
  - `Flipped: <node> -- <old> was wrong because <why>`;
  - `Fixture: test/fixtures/scheme_layer_truth.json (scripts/extract_scheme_layer_truth.do)`;
  - `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`;
  - `BUGS.md: "<title>" (closed)`.

### Q1, about S15's file, not this one (resolved by index R10, review pass)

**Resolved: (a).** R10 makes the section whose commit moves a pin measure and write the new value; S15's ~24 chrome directives move the directive count first, so S15 moves the bound and the help's "80 to 140" in its own commit (filed as a cross-file fix for section-15 and R10's table in review-notes/g04.md). S21 moves it again only if its three keys cross the bound (its F33), and S24's 24-14 re-measures, renames and rewrites it. No maintainer answer is needed. The original question, for the record:

**Q1 — who flips `test_80_to_140_directives` first.** S15 (batch 5) appends about 24 chrome directives to each file. That puts s2gmanual at about 163 directives, past the test's 140, three batches before S24, which index R9 names as the flipper. S15's section file names no flip of it, so S15's full run would be red. Options:
- **(a)** S15 moves the bound and the help's "80 to 140" itself, with a `Flipped:` line, and S24 re-measures them (24-14 already re-measures).
- **(b)** S15 keeps the pin by some other means.

S24's tasks hold under either answer.

### Text for the closing task (24-19)

**BUGS.md, P1.4a** (closed in place, `- [x]`):

`- Resolution: Fixed <ddmonyyyy> (WP-30, P1.4a). A colour opacity the scheme declares (sttrans's %20) is passed when each glyph is built to every fit, smooth, function, spike, range, paired-coordinate and immediate layer, through GlyphMapper._scheme_alpha_kw: the lines of _empty_fit_line, _render_ci_band and the fit mappers, the segments of spike, rspike, rcap (and its caps), dropline, rcapsym, pcspike, pcarrow, pcbarrow and pccapsym, their arrow heads, every marker, and rbar's fill; _ci_line_restyle keeps the last word under pstyle(); the confidence band keeps ci_area's colour with no opacity, as twoway draws it; rarea follows area's rule (opaque, 0.2 under sttrans). A histogram is drawn in the scheme's histogram style -- color histogram at intensity histogram, outlined in color histogram_line at linewidth histogram -- the same for every histogram layer and for an emptied layer's key (SchemeParser.histogram_*, GlyphMapper._histogram_quads); scripts/extract_scheme_truth.py and the 26 shipped files carry the four keys, and graph bar's intensity bar and intensity area, which twoway's bar and area ignore, are no longer written. The scheme's hollow symbols are drawn hollow and its small symbols at Stata's measured size for them (0.707 of the full symbol; 0.75 for smtriangle; smx and smv as x and v), after msize(), and so is a user's msymbol(sm*) (OptionTranslator.symbol_traits, SchemeParser.default_symbol_traits, GlyphMapper._apply_marker_opts); the symbol cycle reaches scatteri, rscatter, pcscatter, dropline and rcapsym; markers read color p#markfill and p#markline, not p#mark; msymbol(Oh) with malpha() stays hollow. A marker's nonselection and muted copies are styled by WP-30 P1.12a's brushed-copy sync, not by this entry. The saved page and the served app draw the same, before and after a filter move. Pinned by test/test_scheme_layer_alpha.py::TestSttransReachesEveryLayer::test_each_type, test/test_scheme_layer_alpha.py::TestRareaFollowsArea::test_area_s_rule, test/test_scheme_layer_alpha.py::TestAfterAFilterMove::test_the_served_glyphs_keep_their_opacity, test/test_histogram_scheme_style.py::TestTheSchemesHistogramStyle::test_each_scheme, test/test_histogram_scheme_style.py::TestTheEmptyHistogramKey::test_the_key_colour, test/test_scheme_symbol_traits.py::TestDrawnTraits::test_the_factor_survives_msize, test/test_scheme_symbol_traits.py::TestTheCycleReachesEveryMarkerType::test_the_second_layer_is_a_diamond, test/test_scheme_symbol_traits.py::TestMarkerColourKeys::test_markfill_and_markline, test/test_scheme_symbol_traits.py::TestHollowStaysHollow::test_malpha_and_mfcolor, test/test_wp30_truth.cscript SK-01; fixture test/fixtures/scheme_layer_truth.json. Residual, deferred (WP-30): the lower-case symbol shorthands, point, V, pipe, arrow and the geometry of x and v are P2.11's; the rarea and rbar outlines twoway strokes are not drawn (filed by the closeout).`

**CHANGELOG.md:** `<!-- WP-30 P1.4a -->` in `### Results that change` is replaced by these lines. The old values come from `<scratch>/24-P1.4a-failure.txt`.

```
- `twoway histogram mpg` and every other histogram layer is drawn in the scheme's histogram style, the same for every layer: s2color fill `#1a476f` with a white 1px outline (a second histogram `#90353b`) -> khaki `#cac27e` outlined stone `#d7d29e` at `linewidth histogram`; stcolor `#1a85ff` -> `#3191ff` outlined `#5faaff`; s1mono `#606060` -> `#808080` outlined black; an emptied histogram's key likewise. `color()`, `fcolor()`, `lcolor()` and `fintensity()` still win (WP-30, P1.4a)
- `twoway rarea` is drawn as opaque as `area`: fill opacity 0.5 -> 1 (0.2 under sttrans) (WP-30, P1.4a)
- Under `scheme(sttrans)`, fits, smooths, function, spikes, range caps and lines, paired-coordinate layers, arrow heads and immediate layers carry the scheme's 20% opacity: alpha 1.0 -> 0.2; the confidence band stays as it was, as twoway draws it (WP-30, P1.4a)
- The mono schemes' hollow symbols (s1mono's p7-p10 and the rest) are drawn hollow, and small symbols (`smcircle` and the rest, from the scheme or `msymbol()`) at Stata's size for them, about 0.71 of the full symbol (0.75 for `smtriangle`), after `msize()`: filled and full size -> hollow and small. scatteri, rscatter, pcscatter, dropline and rcapsym take the scheme's symbol cycle (circle -> the p# symbol) (WP-30, P1.4a)
- A user scheme's `color p#mark` no longer colours markers, as twoway does not read it; `color p#markfill` and `color p#markline` now colour a marker's fill and outline. `msymbol(Oh) malpha(50)` stays hollow (fill 0.5 -> 0) (WP-30, P1.4a)
```

**dash.sthlp** (TR-24.19; SMCL, fitted into the paragraphs as they stand at the base):
- Series, replacing the `p#mark` clause: "the marker fill and outline colours ({cmd:color p}{it:#}{cmd:markfill} and {cmd:color p}{it:#}{cmd:markline}, each falling back to {cmd:p}{it:#} as Stata's chain does; {cmd:color p}{it:#}{cmd:mark} is not read, as {cmd:twoway} does not read it)".
- Series, replacing the opacity clause: "and a colour opacity the scheme declares ({cmd:sttrans}'s {cmd:%20}), which is carried into every layer's lines, markers and fills in both modes, as Stata draws it, except the confidence band, which {cmd:twoway} draws in {cmd:color ci_area} with no opacity; a colour you give without its own {cmd:%}{it:NN} keeps the scheme's opacity, and {cmd:mcolor(}{it:x}{cmd:%}{it:NN}{cmd:)} or {cmd:malpha()} still win."
- Series, new sentence: "A symbol in the cycle, or one you give with {cmd:msymbol()}, is drawn with its own traits: a hollow symbol ({cmd:circle_hollow} and the rest) as an outline, whatever {cmd:mfcolor()} or {cmd:malpha()} say, and a small one ({cmd:smcircle}, {cmd:smdiamond}, {cmd:smsquare}, {cmd:smplus} and their hollow forms) at 0.71 of the full symbol's size, {cmd:smtriangle} at 0.75, after {cmd:msize()}, as Stata 19.5 draws them; {cmd:smx} and {cmd:smv} are drawn as {cmd:x} and {cmd:v}. The cycle reaches every marker: {cmd:scatter}, {cmd:connected}, {cmd:dot}, {cmd:rconnected}, {cmd:scatteri}, {cmd:rscatter}, {cmd:pcscatter}, {cmd:pccapsym} and the markers of {cmd:dropline} and {cmd:rcapsym}."
- Series, new sentence: "A histogram is drawn in the scheme's histogram style, {cmd:color histogram} at {cmd:intensity histogram} outlined in {cmd:color histogram_line} at {cmd:linewidth histogram}, the same for every histogram layer, as {cmd:twoway} draws it; {cmd:color()}, {cmd:fcolor()}, {cmd:lcolor()} and {cmd:fintensity()} still win."
- Shipped files: "{it:N} to {it:M} directives" (24-14's numbers). The carried keys gain "{cmd:color histogram} and {cmd:histogram_line}, {cmd:intensity histogram} and {cmd:linewidth histogram}". The inferred example becomes "or inferred by {cmd:dash} where Stata resolves the key through a fallback and {cmd:dash} writes it out resolved".

### Notes for the closeout (S58; A145)

- **GAPS2.md Tracked lines.**
  - **D18** (sttrans opacity) and **D19** (histogram style): Closed by P1.4a, with this commit's sha.
  - **D5**: sub-claims g (hollow p# symbols) and h (sm* p# symbols) are closed by P1.4a, together with the `msymbol(sm*)` size of IR-4. D5's other sub-claims (arrow, arrowf, pipe, point, V, the lower-case shorthands, the refusals) stay with P2.11, so D5 stays open.
- **TWOWAY_COVERAGE_AUDIT.md:112** (AUDIT-76): drop "scheme opacity does not reach every geometry" from the marker-styling row's limitations.
- **REMAINING.md:1381** (REM-11-04-B13-RAREA): done, rarea's 0.5. Its second half (the served 0.6 fills) was already gone at `c96facd`.
- **DROPIN-REMAINING.md P1.4:** part a is closed by S24. Research sub-claims e, f and g are S33's (D-24g).
- **ROADMAP P2.11's scope:**
  - The sm* sizes are closed by P1.4a, for the scheme and for `msymbol()` (IR-4).
  - Add the measured geometry: Stata draws `x` and `smx`, and `v` and `smv`, at the same size, and `x` at half the circle's extent, where dash's `x` spans the full marker size.
  - The lower-case shorthands remain.
- **A residual with no owner** (Boundaries): twoway strokes rarea's and rbar's outlines, which dash does not draw. Proposed as a new P2 row.
- **scripts/svg_truth.py:** `svg_fills`' docstring says Stata never writes `<polygon>`. Stata 19.5 writes diamond, square and triangle markers as polygons (E7). Proposed as a P3 note. The S24 reader `scripts/svg_layer.py` reads them.

### For later sections

- **S33** extends `scheme_layer_truth.json` through its own extractor block or a second script. It keeps every S24 probe unchanged (R7). The shipped-but-unread keys stay five, because `intensity bar`/`intensity area` are gone (D-24f). By ratification row 4 (06oct2026) S33 keeps no exempt list and no read-recording: every parsed directive, read or not, stays in `_props` (S33's D-33d), so S24's new reads (`color histogram*`, `intensity histogram`, `linewidth histogram`, `color p#markfill`/`markline`) need nothing from S33.
- **S30**: `color p#mark` is unread, so a bad value there is silent in both twoway and dash.
- **S32**: `style_bundle` must keep `_marker_traits`' hollow and factor, the histogram style (`pstyle(p2)` gives `#A65D62`/`#90353B`, E7) and the opacity kwargs.
- **S45**: a recast layer passes its new type to `_scheme_alpha_kw` and `_cycle_for`.
- **S49**: every transposed construction site keeps S24's kwargs.
