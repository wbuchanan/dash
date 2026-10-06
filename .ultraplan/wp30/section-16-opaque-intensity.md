# Section 16: Intensity as an opaque blend (P1.2 part b, M1)

> Part of: WP-30 · Items: P1.2 part b (entry `P1.2b`) · Risk: yellow · Batch: 6 · Depends on: 15 · Blocks: 24, 30, 43 · Tasks: 16, 1 commit · Case prefix: OB

## Review amendments

- Fixed (major): 16-08 ran "S15's test_default_look.py", which no section creates (S15's file is test_scheme_chrome.py), so its pytest command would error. It now runs test_scheme_chrome.py.
- Fixed (minor): Q1 (the histogram intensity until S24) is settled by M1 and register P1.4.2, not left to the maintainer. D-16a, Notes and the BUGS Resolution (its conditional clause removed) follow.
- Cross-file: R3 names none of the three in-place help corrections of S16 (Stata scheme support :3369-3372, Statistical Layer Options :2583-2584, Differences :660-664). No batch-6 partner edits them. Recorded in g03.md.
- Rejected: "M5: `fintensity(1e400)` is refused by dash.ado but drawn by twoway". That refusal predates WP-30 and is P2.14's, which M5's scope (only new code in the areas WP-30 touches) leaves alone. S16 does not touch dash.ado's rules.
- Rejected: "nonselection recolouring breaks A37 (P2.49 stays open)". S16 recolours only the fill colour that its own blend writes, so that it adds no new mismatch. Superseded by the ratification of 06oct2026 (below): P2.49 is not filed, and S08 syncs the copies.
- Checked: the anchors (`_INTENSITY` 5970, `_intensity` 6577-6583, `bar_alpha`/`area_alpha` 6951-6954, `_blend_intensity` 8292-8305, `_scheme_alpha` 9727-9742, `_apply_fill_opts` 8844-8860) match HEAD. S16 shares no function with S17 (`_histogram_quads` against `map_histogram`) or S18. It is batch 6's one `_apply_fill_opts` editor (R12). The truth block, BUGS title, single Results marker and map anchor match section-01. The `WP29_ONLY` gate exists in test_wp29_truth.cscript.
- (cross-file pass) 16-16 verify: added the key-deletion check `grep -c '^    "P1.2b": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.
- (ratification 06oct2026) Item 27 (A37, P1.12.6) is "Fix in WP-30": S08 (batch 3) syncs the nonselection and muted copies after the appliers; P2.49 is not filed. The P1.12.6 reading, E1's Brushing paragraph, E6's guard list, BR-16.5, TR-16.6, AC-16.4, 16-07 and 16-08 now rely on S08's sync; TR-16.6's nonselection fill write is kept (it agrees with the sync), with every post-creation fill write inside `_apply_fill_opts`, before the sync.
- (ratification 06oct2026) `TestBrushedFillsKeepTheBlend::test_the_nonselection_copy_has_the_drawn_colour` now pins twoway's literal colours in the nonselection and muted copies, so it stays red at the batch-6 base (S08's sync copies the unblended colour); no test added, counts unchanged. 16-01 checks that S08's sync follows `_apply_fill_opts`.
- (ratification 06oct2026) Removed: the P2.49 residual (Boundaries, BUGS Resolution, For later sections) and the closeout's ROADMAP P2.49 edit; 16-08 treats a failure of S08's brushed-copy tests as a regression of S08's fix.

**Binding readings applied in this file** (decisions.md M1, M5, M6; decision-register P1.2, P1.12.6, P1.13.6; index A145, A150, R2, R3, R12):
- **M1, P1.2.2, P1.2.3.** Markers are drawn opaque unless the colour carries `%NN`, the scheme declares an opacity (`sttrans`) or the user gives dash's own `malpha()`; `map_rconnected`'s two `map_scatter` calls are included. Every dashboard's look changes, with no opt-out, and the change is announced under CHANGELOG "Results that change".
- **P1.2.5 [C].** `fintensity()` is never refused. One shared function, `GlyphMapper._blend_intensity`, carries the measured rule above 100 and its clamp (navy at 6000 and above is `#010304`); S30 (P1.13a) builds `colour*#` on the same function (P1.13.6).
- **P1.2.8 [C], M6.** A user scheme's `intensity bar` and `intensity area` (graph bar's keys) are no longer read, silently: twoway ignores both (measured, Evidence E3). The parser's `bar_alpha` and `area_alpha` are retired the way `gsize text` was (`test_scheme_consumption.py::TestNoParsedKeyIsDiscarded::test_gsize_text_is_retired_because_stata_draws_nothing_with_it`).
- **P1.12.6 [C], A37 (ratification item 27, 06oct2026: fixed in WP-30).** S08 (batch 3) fixes the brushed-glyph bug: after the option appliers run, it copies the styled properties to each renderer's `nonselection_glyph` and `muted_glyph`, keeping dash's nonselection alpha, in both modes. P2.49 is not filed. S16 adds no styled property: its blend changes the value of `fill_color`, which the five mappers write at creation (Bokeh copies creation keywords into both copies) and `_apply_fill_opts`, an applier S08's sync follows, writes afterwards. So S16's blended fills reach the brushed and muted copies through S08's sync. TR-16.6's own write of the nonselection copy's `fill_color` is kept: it writes the glyph's colour and leaves the alpha alone, exactly what S08's sync writes, so it agrees with the sync whichever runs last and costs one assignment. S16 keeps S08's sync where S08 put it, byte for byte, and makes every post-creation fill write inside `_apply_fill_opts`, before the sync runs; no fill colour is written to a glyph outside the creation keywords and that applier. 16-01 checks at the base that the sync follows `_apply_fill_opts`. `TestBrushedFillsKeepTheBlend` is S16's only test that reads a nonselection or muted glyph; it pins twoway's literal colours in both copies, and S08's brushed-copy tests cover every other property.
- **M5.** Nothing is newly refused: twoway accepts every `fintensity()` value (rc 0; an unknown name gets a note). dash.ado's existing refusal of `fintensity(1e400)` (rc 198) is a dash refusal of a value twoway draws, which stays with P2.14; S16 does not touch dash.ado's rules.
- **A150.** Notes go through `_dash_style_note`, which S06's channel prints in twoway's `(note: …)` form; tests count notes with S06's needle helpers.
- **A145.** ROADMAP.md:2051 is corrected by S58, from the text in "Notes for the closeout"; S16 edits no tracking document.
- **R12.** S16 is batch 6's only editor of `_apply_fill_opts`. It edits none of `_make_figure_body`, `_generate_app_source` (S18 owns both in batch 6), `_build_sources_and_figures`, `_build_filter_widgets`, `_apply_marker_opts`, `_apply_line_opts` or `_apply_mlabel_opts`.
- **R2 row S16.** No copy-list entry: `_blend_intensity`, `_scheme_alpha` and the new `_fintensity_value` are `GlyphMapper` methods and `_intensity` a `SchemeParser` method, which travel with their classes (class loop, dash_render.py:33436).

**Section decisions (this file).**
- **D-16a — the histogram's intensity until S24.** The manifest and BR-30.2 group histograms with the p#bar chain. Measured (Evidence E3): twoway draws `histogram mpg, fcolor(navy)` as `#1A476F` under s2color and s1rcolor and `#31597D` (inten90) under stcolor: a histogram reads `intensity histogram` (`style/shadestyle-histogram.style`), `full` in the s2color family and `inten90` in the st family, never `intensity p#bar`. Under M1 S16 draws the histogram fill as an opaque blend at intensity 1 (full) and stops reading `intensity bar` for it; S24 (P1.4a) adds `color histogram`/`intensity histogram` and passes its intensity through the same blend. Under s2color nothing changes in colour; under s1rcolor the histogram becomes opaque (twoway's picture); under the st schemes it stays at full until S24. This is settled, not a maintainer question: M1 (match Stata) and register P1.4.2 (twoway's histogram style on every histogram layer, owned by P1.4a, S24) both rule out the p#bar chain for histograms (Notes, "Q1, resolved").
- **D-16b — range fills.** `map_rbar` reads the p#bar chain and `map_rarea` the p#area chain, as twoway does (rbar and rarea default `#486C8C`, `rarea color(red)` `#FF3333`, Evidence E3). The one blend serves all five `_apply_fill_opts` callers. `map_rarea`'s `fill_alpha=0.5` stays: it is S24's (REM-11-04-B13-RAREA, register P1.4.3).
- **D-16c — outlines stay as drawn.** A bar's outline (`line_color`) and an area's optional border keep the unblended resolved colour; twoway strokes `rbar, color(red)` `#FF0000` while filling it `#FF3333`.
- **D-16d — intensity names and missing values** (measured, Evidence E3). Exactly Stata's 14 intensity styles are names, case-sensitive: `inten0` … `inten100` by tens, `inten200`, `full` (100) and `max` (999999). `fintensity(.)` draws the layer's own intensity, silently (an empty value is treated the same: unmeasured, a renderer-only guard). Any other text (`abc`, `inten150`, `inten55`, `INTEN50`, `Full`, `.a`, `()`) draws full intensity with one note, as twoway's "named style … not found in class intensity, default attributes used" does. A number is read by S08's `OptionTranslator.stata_number`; a negative number is 0.
- **D-16e — the pstyle(p#) band is left alone.** `SchemeParser.p_other_band_styles` keeps its clamped intensity: measured, `lfitci, pstyle(p1)` under a scheme with `intensity p1bar inten200` draws its band `#486C8C`, not navy/2, so the band does not follow `intensity p#bar` above full the way the documented chain says. Recorded for S32 (named styles) in Notes; S16 lifts the clamp only on the bar and area chains S15 added.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:67-76 (P1.2) ends: "Markers are drawn at alpha 0.8, and `fintensity()` is applied as alpha." GAPS2 D11 (GAPS2.md:972-980): "Stata draws markers opaque … Stata's intensity lightens a colour toward white instead of making it transparent. dash turns `intensity p inten80` into alpha." Re-measured at `c96facd` in both modes (Evidence E2): every scatter, connected, dot and rconnected marker is `fill_alpha 0.8 line_alpha 0.8`; a bar is the full `#1a476f` at 1.0 where twoway draws `#486C8C`; `fintensity(50)` is `#1a476f` at alpha 0.5 where twoway draws the opaque `#8DA3B7`; `fintensity(150)` is clamped to opaque navy where twoway draws `#112F4A`; `fintensity(-5)` is invisible (alpha 0) where twoway draws white; a user's `fcolor(yellow)` is `#ffff00` where twoway draws `#FFFF33`; the CI band blends towards white under s1rcolor (`#a8a8a8`) where twoway multiplies towards black (`#282828`); and a user scheme's `intensity area inten40`, which twoway ignores, makes every area see-through.

**After this section**, in both modes, before and after any filter move:
- markers are opaque unless `%NN`, `sttrans` or `malpha()` asks for an opacity;
- bar, rbar, area and rarea fills are the resolved colour (the scheme's p# colour, or `color()`/`fcolor()`/`bfcolor()`) blended at the layer's intensity (`intensity p#bar` or `intensity p#area`, through Stata's chains, above 100 too), opaque unless an opacity is declared or asked for; histogram fills are opaque at full intensity until S24;
- `fintensity()` replaces the layer's intensity and is drawn by twoway's rule: towards white below 100 and divided above it under `naturally_white 1`, multiplied under `naturally_white 0` (s1rcolor), with Stata's clamp to the smallest non-zero channel, rounded half up; it is never refused;
- the CI band's `fintensity()` follows the same rule;
- a brushed-away fill keeps the drawn colour, dimmed;
- a user scheme's `intensity bar`/`intensity area` are ignored, as twoway ignores them.

**Why one section.** These are one root cause, intensity read as alpha, at one set of symbols: `_scheme_alpha` (markers and the four `_scheme_alpha` fill sites), `_apply_fill_opts` (all five fill mappers), `_blend_intensity` and `_ci_band_style` (the band). P1.2a's chrome is S15 (batch 5), which supplies `naturally_white` and the p#bar/p#area chains; S24 (sttrans opacity on every layer, the histogram style), S30 (`colour*#`) and S43 (bare `*#`/`%#` at every site) build on the one blend.

**Test order and commit rule (rule 7, D1).** One entry, one commit, `(WP-30 P1.2b)`.
- **16-01** writes the regression tests with twoway's literal values, runs them against the unmodified tree and saves `<scratch>/16-P1.2b-failure.txt`. It never commits.
- **16-02** extracts the fixture; **16-03** adds the fixture-driven and guard tests and appends their failure lines.
- **16-04 to 16-15** fix, re-measure the red list, flip the pinned tests, add the parity cases, fill the truth block and update the help.
- **16-16** closes the entry, replaces the marker and makes the commit after one full run through the queue.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every dashboard's markers and fills change colour or opacity, five HIGH symbols are edited, and 46 pinned rows assert intensity-as-alpha or unblended fills

**Why.** M1 accepts the visible change (PLAN K2, RK-4): every marker loses its 0.8 alpha and every bar and area changes colour. One code path serves both modes (the served app copies `GlyphMapper` and `SchemeParser` by source and rebuilds the scheme from its property dict, dash_render.py:33435-33479), so the risk is breadth, not divergence.

**Risk factors.**
1. HIGH symbols (index batch 6.0; Evidence E5): `GlyphMapper._scheme_alpha` (8 impacted, 4 direct, 4 processes), `GlyphMapper._apply_fill_opts` (6, 5 direct), `GlyphMapper._blend_intensity` (6, through `_ci_band_glyphs`), `GlyphMapper._ci_band_style` (6) and `_ci_band_glyphs` (6, 4 direct). `map_bar`, `map_area`, `map_rarea`, `map_rbar` and `map_rconnected` are `UNKNOWN` (dispatched by name through `_dash_glyph_dispatch`, def 28501, entries 28519-28548; confirmed by grep).
2. Pinned tests assert today's alphas (Evidence E6); the prototype measured them. Each is flipped with its reason (R9), never deleted.
3. The single-y page digest (`test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline`) moves with the marker alpha (R10; S16 is a listed mover).
4. The histogram's interim intensity (D-16a) and rarea's interim alpha (D-16b) are knowingly not twoway's until S24 lands in batch 8; no release is cut before S58 (IR-12's precedent).
5. S15's attributes are consumed by name (`naturally_white`, `p_bar_intensity`, `p_area_intensity`); a different spelling at the batch base would break the plan's code.
6. `_scheme_alpha`'s signature loses its third argument, and S24 extends `_scheme_alpha`'s callers in batch 8.

**Mitigation.**
1. Impact is read at the batch base (index 6.0) and re-checked by 16-01 before any edit; `UNKNOWN` callers were confirmed by grep (Evidence E5).
2. 16-08 re-measures the red list on the fixed tree against Evidence E6; 16-09 to 16-14 flip exactly that list, each with a `Flipped:` line.
3. The merger re-derives the digest after S16's landing (R10); the commit message says why it moved.
4. D-16a and D-16b are stated in the CHANGELOG line and handed to S24 in "For later sections"; S24's flips are named there.
5. 16-01 greps the batch base for S15's three attributes and stops and reports if any is missing or renamed (it never adds them itself: S15 owns them, manifest S15 notes).
6. The new signature is written in "For later sections"; every caller at the batch base is in S16 (`grep -n '_scheme_alpha(' dash_render.py` shows 4 call sites and the definition at `c96facd`).

**Prototype (measured 03oct2026 on a `git archive` copy of `c96facd` in scratch, with S16's design applied using `scheme.fill_alpha` as a stand-in for S15's chains and `naturally_white` read with `getattr(…, 1)`).** The 52 test files that mention an alpha, an intensity, a fill colour or the page digest were run; the failures are Evidence E6.

## Dependencies

- **Depends on: 15.** S15 (batch 5) adds to `SchemeParser` (manifest S15 notes: "Owns naturally_white and the p#bar/p#area chains that S16 and S30 consume"): `naturally_white` (0 or 1, from `system naturally_white`, s2color's 1 in `_FALLBACK_PROPS`), and the 15-element lists of the bar and area intensity chains (`intensity p#bar → pbar → p# → p`, `intensity p#area → parea → p# → p`), here called `p_bar_intensity` and `p_area_intensity`; the 26 regenerated scheme files carry `system naturally_white 0` for s1rcolor. Through earlier batches: S01 (the entry, `WP30_OPEN["P1.2b"]`, the marker `<!-- WP-30 P1.2b -->`, the stub block `S16`, the map anchor), S06 (the note channel), S08 (`OptionTranslator.stata_number`).
- **Blocks: 24, 30, 43.** S24 routes sttrans opacity to every layer through `_scheme_alpha`/`default_alpha` and adds the histogram style; S30 builds `colour*#` on `_blend_intensity`; S43 composes a bare `*#`/`%#` with the fill blend through `_apply_fill_opts`'s `base`.
- **Parallel batch: 6.** Merge order S16, S17, S18 (S16 first).
- **Can run with:** S17 (date and format text in keys and tooltips: `_apply_colorvar`, `_dash_apply_z_options`, `_dash_build_hover`, `map_histogram`'s hover tag; it does not edit `_histogram_quads`, `map_scatter`'s alpha line or any fill line) and S18 (axis formats: `_make_figure_body`, `_generate_app_source`, `_dash_axis_tick_formats`). No function is shared. S17 edits `map_histogram`'s tag and S16 `_histogram_quads`, two different methods; the hunks are apart.

## Evidence

All anchors are `c96facd`'s (dash_render.py 37,689 lines). Batches 3-5 (S07, S08, S13, S14, S15) land before S16 and move lines; the symbols named are authoritative.

### E1 — the code (dash_render.py)

**`SchemeParser`: intensity read as alpha.** `_INTENSITY` (5969-5974) lacks `inten200` and `max`:

```python
5970    _INTENSITY: dict[str, float] = {
5971        "inten0":   0.0,  "inten10":  0.10, "inten20":  0.20,
5972        "inten30":  0.30, "inten40":  0.40, "inten50":  0.50,
5973        "inten60":  0.60, "inten70":  0.70, "inten80":  0.80,
5974        "inten90":  0.90, "inten100": 1.0,  "full":     1.0,
```

`_intensity` (6577-6583) clamps to 1:

```python
6577    def _intensity(self, key: str, default: float = 0.8) -> float:
6578        raw = self._props.get(key, "").strip().lower()
6579        if raw in self._INTENSITY:
6580            return self._INTENSITY[raw]
6581        try:
6582            return max(0.0, min(1.0, float(raw) / 100.0))
6583        except (ValueError, TypeError):
```

The three intensities (6951-6954); `bar_alpha` and `area_alpha` read graph bar's keys:

```python
6951        # Fill intensities
6952        self.fill_alpha: float = self._intensity("intensity p", 0.8)
6953        self.bar_alpha: float = self._intensity("intensity bar", 0.8)
6954        self.area_alpha: float = self._intensity("intensity area", 0.8)
```

`_FALLBACK_PROPS` carries `"intensity area": "full"`, `"intensity bar": "full"`, `"intensity p": "inten80"` (5769-5771). `p_other_band_styles` (7120-7130) already walks the p#bar chain for the pstyle(p#) band (`_first_present((f"intensity p{_i}bar", "intensity pbar", f"intensity p{_i}", "intensity p"))`, 7124-7125); D-16e leaves it.

**`GlyphMapper._scheme_alpha`** (9727-9742) turns the intensity into an alpha unless an opacity is declared:

```python
9727    def _scheme_alpha(self, color_idx: int, plot_type: str,
9728                      intensity_alpha: float) -> float:
...
9741        declared = self.scheme.default_alpha(color_idx, plot_type)
9742        return intensity_alpha if declared is None else declared
```

Its four call sites: `map_scatter` 9836-9837 (`alpha=self._scheme_alpha(color_idx, "scatter", self.scheme.fill_alpha)`, the marker's 0.8), `map_area` 10091-10092 (`self.scheme.area_alpha`), `map_bar` 10239-10240 (`self.scheme.bar_alpha`), `_histogram_quads` 12435-12436 (`self.scheme.bar_alpha`). `map_connected` (10024), `map_dot` (13392) and `map_rconnected` (13356 and 13361) draw their markers through `map_scatter`:

```python
13354            self.map_line(fig, source, y1var, xvar, options, view=view,
13355                          color_idx=color_idx, line_kind="", order=order),
13356            self.map_scatter(fig, source, y1var, xvar, options, view=view, color_idx=color_idx),
...
13361            self.map_scatter(fig, source, y2var, xvar, options, view=view,
13362                             color_idx=color_idx, colorvar_key=False),
```

**`GlyphMapper._blend_intensity`** (8292-8305) blends towards white only and clamps f to [0, 1]:

```python
8292    @staticmethod
8293    def _blend_intensity(hexval: str, f: float) -> str:
...
8302        f = max(0.0, min(1.0, float(f)))
8303        return "#%02x%02x%02x" % tuple(
8304            max(0, min(255, int(math.floor(255.0 - (255.0 - c) * f + 0.5))))
8305            for c in rgb)
```

**`GlyphMapper._apply_fill_opts`** (8807-8860) writes `fintensity()` into `fill_alpha`:

```python
8844        if "fintensity" in options:
8845            try:
8846                val = str(options["fintensity"]).strip()
8847                # Stata fintensity: 0-100 (percentage) or keywords inten0-inten100
8848                if val.startswith("inten"):
8849                    pct = float(val[5:]) / 100.0
...
8857            else:
8858                pct = max(0.0, min(1.0, pct))
8859                if hasattr(glyph, "fill_alpha"):
8860                    glyph.fill_alpha = pct
```

Its five callers, each after the mapper set `fill_color` itself: `map_area` 10103, `map_bar` 10283, `_histogram_quads` 12446, `map_rarea` 13001, `map_rbar` 13105. `map_bar` (10231-10283) creates the glyph in the p# colour at `bar_alpha`, then `color()` and `bfcolor()` overwrite `r.glyph.fill_color` with the unblended colour:

```python
10231        _bar_default_color = self.scheme.default_color(color_idx, "bar")
10232        _vbar_kwargs: dict = dict(
...
10235            fill_color=_bar_default_color,
10236            line_color=_bar_default_color,
...
10239            fill_alpha=self._scheme_alpha(color_idx, "bar",
10240                                          self.scheme.bar_alpha),
```

`map_area` (10086-10103) does the same at `area_alpha` and reads `r.glyph.fill_color` back as the default border colour (10110); `map_rarea` (12981-13001) draws at `fill_alpha=0.5`; `map_rbar` (13056-13105) at the default 1.0; `_histogram_quads` (12423-12449) at `bar_alpha`.

**The CI band.** `_ci_band_style` (8376-8386) parses `fintensity()` again, clamped to [0, 1]; `_ci_band_glyphs` (8414-8419) blends towards white whatever the scheme:

```python
8376        if "fintensity" in options:
8377            try:
8378                v = str(options["fintensity"]).strip()
8379                pct = float(v[5:] if v.startswith("inten") else v) / 100.0
...
8386                st["intensity"] = max(0.0, min(1.0, pct))
...
8418            fill_color=self._blend_intensity(fill, st.get("intensity", 1.0)),
```

**Brushing.** Bokeh copies `nonselection_glyph` from the creation keywords; `_dash_dim_nonselection` (29025-29047, CRITICAL, not edited) sets only its alphas. A colour written on `renderer.glyph` afterwards never reaches the copy (research critic: `dash_bar50.html` VBar nonselection `#1a476f` at 0.1). From batch 3, S08's sync copies every applier's styled properties to the nonselection and muted copies (A37, ratification 06oct2026), so at the batch-6 base both copies carry the glyph's unblended colour.

**No page script writes a fill.** Every module-level JavaScript string (`_FILTER_JS` 18562, `_DASH_FILTER_MASK_JS` 18454, the tick and CSV scripts) was scanned for `fill_color`/`fill_alpha` writes: none. The saved page's filter move re-filters views; it never restyles a glyph. The served move rebuilds glyphs through the same `GlyphMapper` (research p1-02 §1, `probe_move.py`).

### E2 — measured at `c96facd`, both modes

From research p1-02 §1 and its critic additions (saved `tp._standalone`, served `ServerAppBuilder` + `make_document`; the modes agree on every value), and after a served `foreign, type(dropdown)` move to "Foreign" (`probe_move.py`):

```
scatter / connected / dot      Scatter fill_alpha 0.8 line_alpha 0.8   (s2color, stcolor, s1rcolor, economist)
rconnected                     [('Scatter', 0.8)] twice                 scatteri, rscatter, dropline 1.0
bar                            VBar #1a476f alpha 1.0                   twoway #486C8C
bar fintensity(50)             VBar #1a476f alpha 0.5                   twoway #8DA3B7 opaque
area                           VArea #1a476f alpha 1.0                  twoway #486C8C
lfitci fintensity(150)         band #c0c0c0                             twoway #808080
s1rcolor lfitci fintensity(50) band #a8a8a8                             twoway #282828
served after the move          scatter 0.8; bar #1a476f 1.0; bar fintensity(50) #1a476f 0.5; area #1a476f 1.0
saved page HTML                "fill_alpha":{"type":"value","value":0.8} on the Scatter
```

### E3 — twoway truth (StataNow 19.5 MP; `graph export` to SVG; fills read as `fill:#RRGGBB[;fill-opacity:a]`)

Research p1-02 §2 (do-files `inten.do`, `inten2.do`, `inten3.do`, `fc.do`, `fneg.do`) and critic `spot.do`-`spot5.do`:

```
s2color bar default            #486C8C  = p1 #1A476F at inten80 towards white
s2color bar p2                 #A65D62;  stcolor #489DFF; economist #658397; s1mono and sj #808080
sttrans bar                    #486C8C fill-opacity:0.20
s1rcolor bar                   #CCCC00  = yellow * 0.8 (towards black)
area / rarea s2color           #486C8C opaque
bar fcolor(yellow), color(yellow), area fcolor(yellow)   #FFFF33
bar fintensity(50)             #8DA3B7;  fintensity(150) #112F4A;  fintensity(1000) #03070B;  fintensity(0) and (-5) #FFFFFF
navy fintensity(5000)          #010102;  6000, 7500, 9000, 9999, 10000, 20000, 100000  #010304;  white fintensity(9999) #030303
s1rcolor navy fintensity(50)   #0D2438;  fintensity(150) #276BA7;  yellow fintensity(10000) #FFFF00
lfitci default / fintensity(150)   #C0C0C0 / #808080;  s1rcolor lfitci fintensity(50) #282828
markers: scatter, connected, dot, mcolor(navy)  #1A476F opaque;  mcolor(navy%50) fill-opacity:0.50
user scheme: #include s2color + intensity bar inten40 + intensity area inten40     bar and area #486C8C (ignored)
             #include s2color + intensity p1bar inten40 + intensity p1area inten40   bar and area #A3B5C5
```

Measured for this file, 03oct2026, through `scripts/stata_slot.sh` (scratch `…/wp30/s16-probe/p16.do`-`p16e.do`, `sysuse auto`, `lcolor(none)` where an outline would cover the fill; `rarea`/`rbar` with `gen lo = mpg - 3`, `gen hi = mpg + 3`, `sort weight`):

```
twoway rbar lo hi rep78 if rep78<., scheme(s2color)                       #486C8C (69 bars)
twoway rbar lo hi rep78 if rep78<., scheme(s1rcolor)                      #CCCC00
twoway rarea lo hi weight, scheme(s2color)                                #486C8C
twoway bar …, fcolor(navy%50) scheme(s2color)                             #486C8C fill-opacity:0.50
twoway bar …, fcolor(navy) scheme(sttrans)                                #486C8C fill-opacity:0.20
twoway bar …, fcolor(navy) scheme(stcolor)                                #486C8C
twoway (bar mpg rep78) (bar price rep78, yaxis(2)), scheme(s2color)       #486C8C and #A65D62
twoway bar …, fcolor(navy) fintensity(0) scheme(s1rcolor)                 #010304   (fintensity(1) the same)
twoway bar …, fcolor(red) fintensity(0) scheme(s1rcolor)                  #010000
twoway bar …, fcolor("200 100 3") fintensity(1) scheme(s1rcolor)          #432101
twoway area mpg weight, fcolor(navy) fintensity(50) scheme(s1rcolor)      #0D2438
twoway lfitci mpg weight, fintensity(-5) scheme(s2color)                  band #FFFFFF
twoway bar …, fcolor(navy) fintensity(.)                                  #486C8C, no note (the layer's intensity)
twoway bar …, fcolor(navy) fintensity(inten200)                           #0D2438
twoway bar …, fcolor(navy) fintensity(max)                                #010304
twoway bar …, fcolor(navy) fintensity(full) / (INTEN50) / (Full) / (inten55) / (inten150) / (abc) / (.a)
                                                                          #1A476F; all but full print
  (note:  named style abc not found in class intensity, default attributes used)
twoway bar …, fintensity(abc) / (inten150) / (50x) / (1e400) / (.)       rc 0 every one
twoway histogram mpg, fcolor(navy) scheme(s2color)                        #1A476F   (intensity histogram full)
twoway histogram mpg, fcolor(navy) scheme(stcolor)                        #31597D   (inten90)
twoway histogram mpg, fcolor(navy) scheme(s1rcolor)                       #1A476F
twoway histogram mpg, fintensity(50) scheme(s2color)                      #E5E1BF   (khaki #CAC27E at 50: S24's colour)
twoway connected mpg weight / rconnected lo hi weight / dot mpg rep78     #1A476F markers, no fill-opacity
twoway scatter mpg weight, mcolor(navy%50) scheme(s1rcolor)               #1A476F fill-opacity:0.50
twoway scatter mpg weight, scheme(sttrans)                                #1A476F fill-opacity:0.20
twoway scatter mpg weight, malpha(50)                                     option malpha() not allowed, r(198)
user scheme s16up: #include s2color, intensity p1bar inten200, intensity p1area 150
  bar #0D2438 (navy/2), area #112F4A (navy/1.5), lfitci pstyle(p1) band #486C8C (D-16e)
dash bar mpg rep78, fintensity(1e400)     dash: fintensity() must be a name or a number (got: 1e400), r(198)   (P2.14)
dash bar mpg rep78, fintensity(abc)       rc 0 (the renderer notes it)
```

Stata's intensity styles (`/Applications/StataNow/ado/base/style/intensity-*.style`, `set val`): `inten0`-`inten100` by tens, `inten200` 200, `full` 100, `max` 999999. `scheme-s2color.scheme:1267-1306`: `intensity histogram full`, `intensity bar full` (graph bar), `intensity p inten80`, and the p#bar/p#area lines commented out (resolved through the chain); `scheme-stcolor.scheme`, `scheme-stmono1.scheme`, `scheme-stmono2.scheme`: `intensity histogram inten90`; `scheme-s1rcolor.scheme`: `system naturally_white 0`. `style/shadestyle-p#bar.style` and `shadestyle-p#area.style` read `intensity p#bar`/`p#area`; `shadestyle-histogram.style` reads `intensity histogram`.

### E4 — the rule (validated against every hex of E3)

For a channel c of the resolved colour and intensity f (f < 0 read as 0), rounding half up (`floor(x + 0.5)`):
- `naturally_white 1`: f ≤ 1 gives `255 - (255 - c) f`; f > 1 gives `c / f`;
- `naturally_white 0`: `c f`, clamped to 255;
- then, if any channel that was non-zero came out 0, every channel is `c / m` instead, with m the smallest non-zero channel of the resolved colour.

A scratch script applied the rule to the 30 measured pairs above: 29 agree. The one exception is the known P1.13 UNCLEAR, navy at exactly 52 (`fintensity(5200)`; twoway `#010304`, the rule `#010102`), recorded in research p1-13 §3 and excluded from every test with that reason.

### E5 — blast radius (`gitnexus impact <symbol> -d upstream -r dash`, 03oct2026 at `c96facd`)

| Symbol | Risk | Impacted / direct / processes |
|---|---|---|
| `GlyphMapper._scheme_alpha` | **HIGH** | 8 / 4 / 4 |
| `GlyphMapper._apply_fill_opts` | **HIGH** | 6 / 5 / 3 |
| `GlyphMapper._blend_intensity` | **HIGH** | 6 / 1 / 3 |
| `GlyphMapper._ci_band_style` | **HIGH** | 6 / 1 / 3 |
| `GlyphMapper._ci_band_glyphs` | **HIGH** | 6 / 4 / 4 |
| `SchemeParser._intensity` | LOW | 2 / 1 / 2 |
| `SchemeParser._init_properties` | LOW | 1 / 1 / 1 |
| `GlyphMapper._histogram_quads` | LOW | 1 / 1 / 1 |
| `GlyphMapper.map_scatter` | LOW | 3 / 3 / 2 |
| `map_bar`, `map_area`, `map_rarea`, `map_rbar`, `map_rconnected` | `UNKNOWN` | no caller resolved; `grep -n 'mapper.map_bar\|mapper.map_area\|mapper.map_rarea\|mapper.map_rbar\|mapper.map_rconnected' dash_render.py` finds them in the `_dash_glyph_dispatch` table (def 28501; `"scatter"` 28519, `"area"` 28522, `"bar"` 28523, `"rarea"` 28543, `"rbar"` 28544, `"rconnected"` 28548), the one path both modes use |
| `_dash_dim_nonselection` | CRITICAL | 8 / 1 / 8 — **not edited** |

### E6 — tests that pin today's behaviour (flip, never delete)

**Prototype result.** The 52 files gave `103 failed, 12217 passed` (11:37 at `-n 6`); with D-16a applied (the histogram at full intensity) the 16 red files gave `96 failed, 3192 passed`. Every failure is one of the pins below: a fill expected in the unblended colour, an intensity expected as an alpha, a marker expected at 0.8, or a retired attribute. F44-F46 were not run by the prototype (it kept the attributes and ran no cscript) and are red by construction. 16-08 re-measures the list on the real fix; a node outside it is investigated before it is flipped (R9).

| Id | Node (flip in place) | Pinned today | Why it was wrong, and the new expectation |
|---|---|---|---|
| F1 | `test/test_glyphs.py::TestFillOptions::test_map_area_fcolor` | `fcolor(red)` → `#ff0000` | twoway fills a user colour at the area's intensity: `#ff3333` (E3: `area fcolor(yellow)` `#FFFF33`) |
| F2 | `…::TestFillOptions::test_map_area_fintensity` | `fintensity(50)` → `fill_alpha` 0.5 | an intensity is a colour: `#8da3b7`, `fill_alpha` 1.0 |
| F3 | `…::TestFillOptions::test_map_area_fintensity_inten_keyword` | `inten75` → alpha 0.75 | `inten75` is no Stata style (E3: `inten55` is noted): `#1a476f`, one note naming `fintensity(inten75)` |
| F4 | `…::TestFillOptions::test_map_bar_fcolor` | `fcolor(magenta)` → `#ff00ff` | `#ff33ff` (magenta at inten80) |
| F5 | `…::TestFillOptions::test_map_bar_fintensity` | `fintensity(80)` → alpha 0.8 | `#486c8c`, `fill_alpha` 1.0 |
| F6 | `…::TestFillOptions::test_map_histogram_fintensity` | `fintensity(40)` → alpha 0.4 | `#a3b5c5`, `fill_alpha` 1.0 |
| F7 | `…::TestFillOptions::test_map_rarea_fcolor` | `#ff00ff` | `#ff33ff` |
| F8 | `…::TestFillOptions::test_map_rarea_fintensity` | alpha 0.3 | `#bac8d4`; rarea's `fill_alpha` stays 0.5 (S24) |
| F9 | `…::TestFillOptions::test_map_rbar_fcolor` | `#ff0000` | `#ff3333` (E3: `rbar, color(red)` fills `#FF3333`) |
| F10 | `…::TestFillOptions::test_map_rbar_fintensity` | alpha 0.6 | `#7691a9`, alpha 1.0 |
| F11 | `…::TestFillOptions::test_fintensity_clamped_min` | `-10` → alpha 0.0 (invisible) | twoway draws white: `#ffffff`, alpha 1.0 |
| F12 | `…::TestFillOptions::test_fintensity_clamped_max` (passes; rewritten) | `150` → alpha 1.0, "clamped" | twoway darkens: `#112f4a`, alpha 1.0 |
| F13 | `test/test_glyphs.py::TestBarOptions::test_bfcolor_sets_fill` | the bfcolor hex | the hex at the bar's intensity |
| F14 | `…::TestBarOptions::test_blcolor_bfcolor_independent` | the bfcolor hex | the fill blended, the outline (`blcolor()`) unchanged (D-16c) |
| F15-F17 | `test/test_glyphs.py::TestHardeningGuards::test_bar_empty_source_keeps_the_scheme_style`, `…::test_rbar_empty_source_keeps_the_scheme_style`, `…::test_rarea_empty_source_keeps_the_scheme_style` | fill == `default_color(…)` | fill == `_blend_intensity(default_color(…), p_bar_intensity / p_area_intensity of the index, naturally_white)`; the populated-equals-empty assertion is kept |
| F18 | `test/test_glyphs.py::TestMapRarea::test_rarea_fcolor_applied` | the user hex | blended at inten80 |
| F19 | `test/test_glyphs.py::TestMapRbar::test_rbar_fcolor_applied` | the user hex | blended at inten80 |
| F20 | `test/test_server.py::TestServerAreaOptions::test_area_fcolor_applied` | `"#ff0000" in fill_colors` | `"#ff3333"` |
| F21 | `…::TestServerAreaOptions::test_area_fintensity_sets_alpha` | `fill_alpha ≈ 0.5` | renamed `test_area_fintensity_blends_the_colour`: `#8da3b7` among the fills, every `fill_alpha` 1.0 |
| F22 | `test/test_server.py::TestServerRareaOptions::test_rarea_fcolor_applied_functional` | `#ff0000` | `#ff3333` |
| F23 | `test/test_server.py::TestServerRbarOptions::test_rbar_bfcolor_applied` | `#ff0000` | `#ff3333` |
| F24, F25 | `test/test_html_output.py::TestColorRenderingAllPlotTypes::test_rarea_fcolor_in_html`, `…::test_rbar_fcolor_in_html` | the user hex in the page | the blended hex in the page |
| F26 | `test/test_html_output.py::TestNewOptionHtml::test_bfcolor_bar_fill_in_html` | the bfcolor hex | blended |
| F27 | `test/test_html_output.py::TestOutputBackendAndVisualMarkers::test_rarea_varea_glyph_has_fill_attributes` | `#1a476f` at 0.5 | `#486c8c` at 0.5 (the 0.5 is S24's) |
| F28, F29 | `test/test_html_output.py::TestPlotOptionsInHtml::test_fcolor_in_bar_html`, `…::test_fcolor_maroon_appears_in_area_html` | the user hex | blended (maroon `#90353b` → `#a65d62`) |
| F30 | `test/test_html_verification.py::TestAlphaTransparency::test_alpha_out_of_range_ignored` (ALP-16) | the default marker's alpha < 1.0 (0.8) | markers are opaque; the base is drawn under sttrans (0.2) so a clamp to 1.0 is still caught |
| F31 | `test/test_html_verification.py::TestColorHexInJson::test_fcolor_in_bar_json` | the user hex in the JSON | blended |
| F32 | `test/test_help_claims_7.py::TestColorColoursTheWholeLayer::test_the_fill_is_the_colour[bar/rbar/area/rarea × saved/served]` (8) | the fill equals `color()`'s hex | the fill is `color()`'s hex at the layer's intensity (twoway `rbar, color(red)` `#FF3333`); histogram rows unchanged (D-16a) |
| F33 | `…::TestColorColoursTheWholeLayer::test_a_specific_colour_option_wins[saved/served]` | `fcolor()`'s hex | `fcolor()`'s hex blended |
| F34 | `test/test_help_claims_8.py::TestTheSchemeOpacityStopsWhereTheHelpSays::test_the_colour_but_not_the_opacity[rarea-saved/served]` | rarea colour sets `{#cc6677}` / `{#90353b}` | `{#d68592}` / `{#a65d62}` (p2 at inten80); the equal-alphas assertion is S24's and is kept |
| F35 | `test/test_color_alias.py::TestColorReachesTheCommonPlotTypes::test_bar_still_honours_color` | `color()`'s hex | blended |
| F36 | `test/test_option_validation.py::TestTheRemainingSilentSites::test_area_color` | `color()`'s hex | blended; the no-note assertion kept |
| F37 | `test/test_ci_plot_index.py::TestBothModes::test_each_layer_takes_statas_plot_index[rarea_rcap_scatter-saved/served]` | rarea fill = the p# hex | the p# hex at the p#area intensity (the plot index rule itself is unchanged) |
| F38 | `test/test_emptied_layer_style.py::TestTheKeyIsTwoways::test_the_empty_layer_draws_in_twoways_key_colour[s2color/s1mono × bar/rbar/rarea]` (6) | a VBar/VArea fill equals the key's stroke (`#90353b`, `#a0a0a0`) | the fixture's `key_styles` is the key's stroke, the unblended colour; the fill is that colour blended at the layer's intensity (`#a65d62`, `#b3b3b3`) |
| F39 | `test/test_scheme_consumption.py::TestNoParsedKeyIsDiscarded::test_the_key_is_read_somewhere[bar_alpha/area_alpha]` | parsed and read | the two rows move to the new `…::test_graph_bars_intensity_keys_are_retired[bar_alpha/area_alpha]`: `not hasattr(SchemeParser("s2color"), attr)` and `_scheme_attr_reads(attr) == []`, as `gsize text` was retired |
| F40 | `…::TestNoParsedKeyIsDiscarded::test_a_schemes_area_intensity_and_minor_grid_reach_both_modes` | `intensity area inten40` → alpha 0.4 | twoway ignores it (E3): the area is `#486c8c` at 1.0 in both modes; the minor-grid half is kept |
| F41 | `test/test_scheme_resolution.py::TestEveryOtherSchemeIsUnchanged::test_the_alphas_are_what_they_were` (38 nodes at `c96facd`, 50 after S07) | `PINNED_ALPHAS["Scatter"] = (0.8, 0.8)`; `PINNED_EXCEPTIONS` s1rcolor VBar/Quad 0.8 | `(1.0, 1.0)`; `PINNED_EXCEPTIONS = {}`, its comment saying why |
| F42 | `…::TestSttransIsDrawnTranslucent::test_a_user_fcolor_with_its_own_alpha_wins_on_a_bar[standalone/served]` | `fcolor(red%60)` fill `#ff0000` | `#ff3333`, alpha 0.6 kept (E3: `fcolor(navy%50)` `#486C8C` at 0.50) |
| F43 | `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` | `_SINGLE_Y_BASELINE_SHA256` | re-derived (R10): the marker alpha 0.8 → 1.0 |
| F44 | `test/test_scheme.py::TestIntensitiesAndFonts::test_bar_alpha_is_float_between_0_and_1` | `0 ≤ bar_alpha ≤ 1` | renamed `test_the_bar_intensity_chain_is_unclamped`: `p_bar_intensity` has 15 entries, each ≥ 0, s2color's 0.8, and no `bar_alpha` |
| F45 | `test/test_scheme_fidelity.py` `ALPHA_SCALARS` rows `bar_alpha`, `area_alpha` (read through `evaluate_scheme`, 471-482) | the parser attribute | the file's transcription is still checked, through the declared directive: for a prop in a new `RETIRED_INTENSITY = {"bar_alpha", "area_alpha"}`, `actual = sp._intensity(<first chain key with a declared value>)` (MISSING when none); the 133-unit count is unchanged |
| F46 | `test/test_wp29_truth.cscript` EW-02 (`_ew_colour`/`_ew_check`, 4513-4540) | a VBar/VArea fill in twoway's key stroke colours | for a VBar/VArea, `want` is the stroke colours blended by `GlyphMapper._blend_intensity` at the probe scheme's p2 bar or area intensity; lines unchanged |

Guards that must stay green (not flips): `test/test_ci_band_style.py` (the measured bands, default intensity full; `TestAdversarial::test_fintensity_out_of_range_is_bounded` still yields `#rrggbb`), `test/test_glyphs.py::TestFitCIFillOptions` (`#e0e0e0`, `#ececec`), `test/test_scheme_coercion.py::TestIntensity` (`clamp=True` default), `test/test_scheme.py::TestIntensitiesAndFonts::test_s2color_fill_alpha_is_0_8`, the histogram rows of F32, `test/test_bug_regressions.cscript` BR-01 (`falpha()` still sets the alpha), `test/test_help_claims_2.cscript` HC2-04G (`fintensity(-5)` rc 0), and S08's brushed-copy tests (the nonselection and muted copies carry the applied styles, with dash's nonselection alpha; A37). Where one of them pins a marker alpha of 0.8 or an unblended fill that S16 changes on the glyph itself, the value is flipped to the glyph's new value with the copies still equal to it; any other failure is a regression of S08's fix.

### E7 — the help, dash.ado and the CHANGELOG

- dash.sthlp:3261-3263 (Marker and Transparency Options, S16's under R3): `malpha()`, `lalpha()`, `falpha()` rows; 3267-3274 says `%NN` and `malpha()` are the same thing. Nothing says markers are opaque or what an intensity does.
- dash.sthlp:3369-3372 (Series, Stata scheme support): "… which wins over the alpha {cmd:dash} otherwise derives from the intensities" — false after S16.
- dash.sthlp:2583-2584 (the CI band's sub-option table): "the fill's intensity, drawn as {cmd:twoway} draws it, the colour blended towards white" — false under s1rcolor and above 100.
- dash.sthlp:660-664 (Option values): an unknown style name, "a fill intensity" among them, "is reported once per render and the scheme's default drawn" — for `fintensity()` twoway draws full intensity.
- dash.ado:1999-2001 (`_dash_option_rules`' comment): "(mlabposition and fintensity have none: twoway accepts 13, 2.5, 150 and -5 with a note or silently, and the renderer notes and defaults)" — after S16 the renderer draws 150 and -5 as twoway does; the rule `fintensity=style` (2031) is unchanged.
- test/test_option_validation.cscript:49: `OV-21  fintensity(150) rc 0 (unbounded: the renderer notes it)` — the comment becomes false; the case (567-569) is unchanged.
- CHANGELOG.md: S01's marker `<!-- WP-30 P1.2b -->` in the `**WP-30 (drop-in P1, 03oct2026)**` group of `### Results that change` (`WP30_LISTS["P1.2b"]` is that list only).

## User stories

- **US-16.1** As a twoway user, I want `scatter`, `connected`, `dot` and `rconnected` markers drawn opaque, as Stata draws them, so that my dashboard's colours are the scheme's, and `mcolor(navy%50)` or `malpha(50)` still make them see-through.
- **US-16.2** As a dashboard publisher, I want bars, range bars, areas and range areas filled with the scheme's colour at its intensity, opaque, as in my Stata report, including when I give `color()` or `fcolor()`.
- **US-16.3** As a twoway user, I want `fintensity(50)`, `fintensity(150)`, `fintensity(inten200)`, `fintensity(0)` and `fintensity(-5)` drawn as twoway draws them, darker above 100 and towards black under s1rcolor, and never refused.
- **US-16.4** As a twoway user, I want `lfitci, fintensity(150)` and the other CI bands to darken and lighten as twoway's do.
- **US-16.5** As a dashboard reader, I want a brushed-away bar dimmed in its own colour, not in another.
- **US-16.6** As a scheme author, I want `intensity p1bar` and `intensity p1area` read (above 100 too) and `intensity bar`/`intensity area` ignored, as twoway reads and ignores them.

## Business requirements

- **BR-16.1** Markers of scatter, connected, dot and rconnected have opacity 1 unless the colour carries `%NN`, the scheme declares an opacity or `malpha()` is given; then that opacity, as today.
- **BR-16.2** A bar, rbar, area or rarea fill is the resolved colour (scheme p#, else `color()`, else `fcolor()`/`bfcolor()`) blended at the layer's intensity by the rule of Evidence E4, at opacity 1 unless an opacity is declared or asked for (rarea's own 0.5 excepted until S24). The layer's intensity is `intensity p#bar` (bar, rbar) or `intensity p#area` (area, rarea) through Stata's chains, unbounded above.
- **BR-16.3** A histogram fill is opaque at full intensity, the resolved colour unblended, until S24 brings the histogram's own intensity (D-16a).
- **BR-16.4** `fintensity()` replaces the layer's intensity on every fill type and on the CI band, read as D-16d says, drawn by the rule of E4; no value is refused; an unknown name draws full intensity with one note; `.` draws the layer's intensity silently; a negative number is 0.
- **BR-16.5** Every drawn fill colour is `#rrggbb`, and the brushed-away (nonselection) and muted copies of a fill have the drawn colour.
- **BR-16.6** A user scheme's `intensity bar` and `intensity area` change nothing and print nothing.
- **BR-16.7** BR-16.1 to BR-16.6 hold on the saved page and in the served app, before and after a filter move, and the two modes draw the same (BR-30.38).
- **BR-16.8** Outline colours, line widths, `falpha()`, `fcolor(none)`, the KPI, colour keys and every non-fill colour are unchanged.

## Technical requirements

All in `dash_render.py` unless named.

- **TR-16.1 One blend.** `GlyphMapper._blend_intensity(hexval, f, naturally_white=True) -> str` (staticmethod, 8292): parse `#rrggbb` (any other input returned unchanged, as today); `f = float(f)`, non-finite read as 1.0, negative read as 0.0; apply E4's rule with `naturally_white` read as a boolean; write lower-case `#rrggbb`. Docstring: the rule, the clamp, the measured examples (`#8da3b7`, `#112f4a`, `#010304`, `#0d2438`) and the UNCLEAR navy-at-52 case with its reason. No logging, no exception for any input.
- **TR-16.2 One `fintensity()` reader.** `@staticmethod GlyphMapper._fintensity_value(raw) -> float | None`, directly after `_blend_intensity`, reading names from the one table `SchemeParser._INTENSITY` (TR-16.3 makes it Stata's 14 styles): `v = str(raw).strip()`; `""` or `"."` → None; `v in SchemeParser._INTENSITY` → its value, unclamped (exact case, so `Full` and `INTEN50` are not names); `n = OptionTranslator.stata_number(v)` not None → `max(0.0, n / 100.0)`; otherwise `_dash_style_note("fintensity", raw, "fill intensity", using="full intensity")` and 1.0. Never raises; the echoed value is bounded by `_dash_display` (80 printable characters); `stata_number` refuses more than 64 characters, so no long text is parsed.
- **TR-16.3 The scheme's chains, unclamped.** `SchemeParser._INTENSITY` (5970) gains `"inten200": 2.0` and `"max": 9999.99`. `_intensity(self, key, default=0.8, clamp=True)`: with `clamp=False` a name keeps its value and a number is `max(0.0, float(raw) / 100.0)` when finite (else the default). S15's readers of `p_bar_intensity` and `p_area_intensity` pass `clamp=False`. `p_other_band_styles` (7128) is not changed (D-16e). Every existing caller keeps `clamp=True`, so `test_scheme_coercion.py::TestIntensity` is unchanged.
- **TR-16.4 Graph bar's keys retired.** Delete `self.bar_alpha` and `self.area_alpha` (6953-6954) and replace the comment above with one saying that `intensity bar` and `intensity area` are graph bar's keys, which twoway's bar and area ignore (measured), so they are no longer read (register P1.2.8). `self.fill_alpha` stays (it is `intensity p`, read by `p_other_band_styles`). `_FALLBACK_PROPS` and the scheme files are not edited (S24 regenerates the files in batch 8).
- **TR-16.5 Opacity from the scheme only.** `GlyphMapper._scheme_alpha(self, color_idx, plot_type) -> float` (9727): the declared opacity (`self.scheme.default_alpha`) or 1.0. Its docstring says an intensity is a colour, never an alpha (M1, GAPS2 D11). The four callers drop their third argument: `map_scatter` (`alpha=self._scheme_alpha(color_idx, "scatter")`, which makes scatter, connected, dot and rconnected opaque), `map_area`, `map_bar`, `_histogram_quads`. `_apply_marker_opts` is not edited: `mcolor(x%NN)` and `malpha()` still set the alpha after creation.
- **TR-16.6 The fill applier.** `GlyphMapper._apply_fill_opts(self, renderer, options, base=None, intensity=1.0) -> None` (8807), in this order: (1) `fcolor(none)` → `fill_alpha = 0.0` (unchanged); otherwise `fcolor()` through `self.tr.parse_color_alpha` sets `base` to its colour and, if it carries `%NN`, `fill_alpha` (unchanged rule); (2) `falpha()`/`fa()` unchanged; (3) `fintensity()` → `f = self._fintensity_value(...)`, used when not None, else `intensity`; (4) when `base` is a string matching `#[0-9a-fA-F]{6}`: `c = self._blend_intensity(base, f, self.scheme.naturally_white)`, `renderer.glyph.fill_color = c`, and, when `renderer.nonselection_glyph` has a `fill_color` property, `renderer.nonselection_glyph.fill_color = c` (its alpha untouched). This write must agree with S08's sync (A37): both give the copy the glyph's colour and leave its alpha alone. S08's sync is kept where S08 put it, byte for byte, and step (4) runs before it, so the sync carries `c` to the muted copy. `fill_alpha` is never derived from an intensity. Docstring states the order and that `base` is the unblended colour the caller resolved (never read back from the glyph).
- **TR-16.7 The five fill mappers.** Each resolves `_fill_base` (the scheme's `default_color(color_idx, <cycle>)`, replaced by `color()` and then `bfcolor()` where the mapper reads them, through `translate_mcolor` with today's note on a bad name) and `_f`, creates the glyph with `fill_color=self._blend_intensity(_fill_base, _f, self.scheme.naturally_white)`, keeps every other creation keyword, writes `color()`/`bfcolor()` into `_fill_base` instead of `r.glyph.fill_color` (outline writes unchanged, D-16c), and ends with `self._apply_fill_opts(r, options, base=_fill_base, intensity=_f)`:
  - `map_bar`: `_f = self.scheme.p_bar_intensity[color_idx % 15]`; `fill_alpha=self._scheme_alpha(color_idx, "bar")`;
  - `map_rbar`: the same `_f`; creation alpha unchanged (S24's);
  - `map_area`: `_f = self.scheme.p_area_intensity[color_idx % 15]`; `fill_alpha=self._scheme_alpha(color_idx, "area")`; the default border colour (10110) is `_fill_base`, not the glyph's blended colour;
  - `map_rarea`: the area `_f`; `fill_alpha=0.5` unchanged (D-16b); `color()` sets `_fill_base` only when `fcolor()` is absent (unchanged rule);
  - `_histogram_quads`: `_f = 1.0` (D-16a); `fill_alpha=self._scheme_alpha(color_idx, "histogram")`; `color()` sets `_fill_base`.
- **TR-16.8 The CI band.** `_ci_band_style`: the `fintensity()` block (8376-8386) becomes `f = self._fintensity_value(options["fintensity"])`; `st["intensity"] = f` when not None (no upper bound). `_ci_band_glyphs` (8418): `fill_color=self._blend_intensity(fill, st.get("intensity", 1.0), self.scheme.naturally_white)`. The band is coloured at creation, so its nonselection copy already carries the blend.
- **TR-16.9 Both modes.** No new module-level name, so no copy-list entry (R2 row S16). The served app rebuilds `SchemeParser` from `_SCHEME_PROPS` with `_init_properties()` (33455-33458), so S15's attributes and the retired ones follow by source. `TestTheServedAppCarriesEveryName` and `TestTheServedAppDefinesEveryNameItReads` stay green (G4). No `_make_figure_body`/`_generate_app_source` line changes (R12).
- **TR-16.10 No JS twin.** No page script reads or writes a fill colour or alpha (E1), so the saved page needs no JavaScript change; `TestAfterAFilterMove::test_no_page_script_writes_a_fill` pins that for every CustomJS of a built page and every module-level `*_JS` string.
- **TR-16.11 Registries.** `test/function_test_map.py`, under `# WP-30 S16 (P1.2b): Intensity as an opaque blend (P1.2 part b, M1)` (A148): `'GlyphMapper._fintensity_value': 'test/test_intensity_blend.py::TestTheFintensityParser::test_numbers_names_and_missing'`. Repointed in place: `GlyphMapper._blend_intensity` (189) → `…::TestTheBlend::test_above_full_divides_and_clamps`; `GlyphMapper._scheme_alpha` (198) → `…::TestMarkersAreOpaque::test_default_markers`. `program_coverage_map.py` unchanged (no Stata program).
- **TR-16.12 Parity.** `test/test_mode_parity.py` `CORPUS` gains, after its last case: `_case("bar, fintensity(150)", [plot_for("bar", {"fintensity": "150"})])`, `_case("area, s1rcolor, fintensity(50)", [plot_for("area", {"fcolor": "navy", "fintensity": "50"})], {"scheme": "s1rcolor"})`, `_case("rconnected, sttrans", [plot_for("rconnected")], {"scheme": "sttrans"})`, `_case("rbar and rarea, color(red)", [plot_for("rbar", {"color": "red"}), plot_for("rarea", {"color": "red"})])`, `_case("histogram, fcolor(navy) fintensity(50)", [plot_for("histogram", {"fcolor": "navy", "fintensity": "50"})])`, `_case("lfitci, fintensity(150)", [plot_for("lfitci", {"fintensity": "150"})])`. `ALLOWED` and `_MUST_WARN` untouched (R8).
- **TR-16.13 Security (rule 1).** Every fill colour written to a glyph is `#rrggbb` produced by `_blend_intensity` from a parsed colour, or a colour `parse_color_alpha` already validated; no option text reaches a page except through `_dash_style_note`, which echoes it through `_dash_display` (printable, at most 80 characters); `_fintensity_value` parses at most 64 characters through `stata_number`'s anchored grammar, never `eval` or `float()` on raw text (so `1_000`, `nan` and `inf` are names, noted); the extractor writes its user schemes only under a `tempfile`-named directory in `c(tmpdir)`, uses no `shell=True`, and its single `shell` call runs `git -C "<root>" rev-parse HEAD` with the root it validated; the truth block writes only under `` `w30_work' ``.

## Boundaries

- **Batch partners.** S17 owns `_apply_colorvar`, `_dash_apply_z_options`, `_dash_colorvar_*`, `_dash_build_hover` and `map_histogram`'s tooltip tag; S18 owns `_make_figure_body`, `_generate_app_source`, `_dash_axis_tick_formats` and `format_truth.json`. S16 edits none of them.
- **Earlier sections.** S15's extractor, scheme files, `scheme_truth.json`, `_FALLBACK_PROPS` keys and the chain attributes are read, not edited (except TR-16.3's `clamp=False` on the two chain readers). S08's `stata_number` and `_apply_marker_opts`, S13's `_apply_line_opts` and `_ci_band_style` line-width code, and S14's bar widths are not touched.
- **Later sections.** S24: sttrans opacity on the other ~30 mappers, `rarea`'s 0.5, the histogram's colour, intensity, outline and width (`TestTheSchemeOpacityStopsWhereTheHelpSays`, `test_80_to_140_directives`, `TestMarkColourIsForMarkers` are S24's flips except the rows S16 must move, named in E6), the scheme regeneration. S30: `colour*#`, CMYK, HSV and `naturally_white` in `stata_colour`, building on `_blend_intensity`. S32: pstyle(p#) bands (D-16e). S43: a bare `*#`/`%#` at every colour site, composed with this blend through `_apply_fill_opts`'s `base`.
- **Residuals not taken.** P2.14 (`fintensity(1e400)` refused by dash.ado, drawn white by twoway); the navy-at-52 rounding (P1.13's UNCLEAR).
- **Not edited:** dash.ado's rules, dash_parse.mata, `_dash_dim_nonselection`, the copy lists, any scheme file, `scheme_truth.json`, the runner, the hygiene pins, any tracking document beyond BUGS.md and CHANGELOG.md.

## Stata truth

**New extractor** `scripts/extract_intensity_truth.do` → **new fixture** `test/fixtures/intensity_truth.json` (`git add -f`; `.git/info/exclude:58` ignores `*.json`). It copies S02's path-free extractor form (A130, R7): the root is `DASH_REPO`, else `c(pwd)` when it holds `dash.ado` and `test/run_all_cscripts.do`, else `exit 601` with "set DASH_REPO to the dash repository"; it opens with `adopath ++ "<root>/"` and `global dash_nobrowser 1` (index E5), then `version 19`, `set graphics off`, `set more off`. It writes its two user schemes (`scheme-s16up.scheme`, `scheme-s16dn.scheme`, the texts of E3) into a `tempfile`-named directory under `c(tmpdir)` and `adopath ++` it, never into the repository. Run from the worktree: `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh $S $WT/scripts/extract_intensity_truth.do` (log `$S/extract_intensity_truth.log`). No other section runs it (R7).

**Method.** `sysuse auto, clear`, `gen lo = mpg - 3`, `gen hi = mpg + 3`, `sort weight`. Each probe is one call `_ob_probe id scheme kind command`, which runs `capture noisily <command>` inside `log using …, text` (the note lines are kept), records `_rc`, then `graph export "<probe dir>/<id>.svg", replace`. After the loop one `python:` block (no Stata call inside, no `shell=True`, a backtick written `\x60`) reads every SVG through `scripts/svg_truth.py`'s `svg_document` and `svg_fills` (marker kind: `svg_marker_fills`) and records the dominant fill of the probe's kind with its opacity.

**Probes** (`lcolor(none)` on every bar, rbar, area, rarea and histogram probe):

| Kind | Command (`twoway …`) | Schemes / values | Recorded |
|---|---|---|---|
| marker | `scatter mpg weight`; `connected mpg weight`; `dot mpg rep78 if rep78<.`; `rconnected lo hi weight` | s2color, stcolor, s1rcolor, economist, sttrans | marker fill, fill-opacity (absent = 1) |
| marker_pct | `scatter mpg weight, mcolor(navy%50)` | s2color, s1rcolor | the same |
| bar | `bar mpg rep78 if rep78<.` | s2color, stcolor, economist, s1mono, sj, s1rcolor, sttrans | bar fill and opacity |
| bar_p2 | `(bar mpg rep78 if rep78<.) (bar price rep78 if rep78<., yaxis(2))` | s2color | both fills |
| bar_user | `bar …, fcolor(yellow)`; `bar …, color(yellow)`; `bar …, fcolor(navy%50)` | s2color; `fcolor(navy)` under sttrans and stcolor | fill and opacity |
| fi | `bar …, fcolor(navy) fintensity(V)` | V in 50 150 1000 0 -5 5000 6000 9999 inten200 max full inten50 . abc inten150 INTEN50 Full .a | fill; notes |
| fi_s1r | `bar …, fcolor(navy) fintensity(V) scheme(s1rcolor)` | V in 50 150 0 1; `fcolor(red) fintensity(0)`; `fcolor("200 100 3") fintensity(1)`; `fcolor(yellow) fintensity(10000)` | fill |
| area | `area mpg weight`; `area mpg weight, fcolor(yellow)`; `area mpg weight, fcolor(navy) fintensity(50)` | s2color; the third also s1rcolor | fill |
| range | `rbar lo hi rep78 if rep78<.`; `rarea lo hi weight`; `rbar …, color(red)` (outline drawn: no `lcolor(none)`); `rarea …, color(red)` | s2color; rbar also s1rcolor | fill, and the rbar outline stroke |
| hist | `histogram mpg, fcolor(navy)`; `histogram mpg, fcolor(navy) fintensity(50)`; `histogram mpg` (`"owner": "S24"`) | s2color, stcolor, s1rcolor | fill |
| band | `lfitci mpg weight`; `lfitci mpg weight, fintensity(V)` | V in 150 -5 under s2color; 50 under s1rcolor | the band's fill |
| userscheme | `bar …`; `area mpg weight` | s16up, s16dn | fill |

**Probe ids** are `<kind>_<scheme>_<value>` (s2color left out; `.` written `dot`, `.a` `dota`, `-5` `m5`; case kept, so `fi_INTEN50`; a command without a value numbered `_1`, `_2` in table order).

**Fixture keys.** `{"_meta": {"stata_version", "born_date", "dash_commit", "extracted", "rule": "E4", "excluded": {"navy_fi_5200": "P1.13 UNCLEAR, research p1-13 section 3"}}, "probes": {id: {"kind", "scheme", "command", "rc", "notes": [lines starting "(note:"], "fill", "opacity", "fills": [every distinct fill, for bar_p2], "stroke", "owner"}}}`. `dash_commit` comes from `shell git -C "<root>" rev-parse HEAD > <tempfile>`, read back with `file read` and reaching python through `Macro.getLocal` (D12). Expected values are those of E3; a difference is investigated and reported, never patched (R7). A probe with `"owner": "S24"` is recorded for reference and is never asserted by S16.

**Truth block** (`test/test_wp30_truth.cscript`, S16's stub between `* ==== S16 P1.2b: Intensity as an opaque blend ====` and `* ==== end S16 ====`, gate `local only : env WP30_ONLY` then `` if inlist("`only'", "", "S16") { ``). Helpers go directly above S16's header, outside every gate: `_s16_page` and `_s16_app`, copies of WP-29 S03's readers (`_s03_val`, `_s03_models`, `_S03Saved`, `_S03Served`, test_wp29_truth.cscript:698-760) renamed `_s16_*`, returning `S16_FILLS` (for every glyph renderer in document order, `Type:fill_color:fill_alpha:line_alpha`, joined by `;`) for the saved page `S16_PAGE` and for the served app (built with `ServerAppBuilder`, `make_document`), the served one also after a `Select` move on `foreign` to `Foreign` (`S16_SAME_AFTER` = 1 when every entry is unchanged); and `_s16_svg`, which wraps `cert_svg_fills` into `S16_TW` (`#RRGGBB|opacity` of the dominant fill). Each case runs twoway and dash on the same command and checks through `_w30_expect`/`_w30_done`:

| Case | Check |
|---|---|
| OB-10 | `scatter mpg weight`, `connected mpg weight` and `rconnected lo hi weight` under s2color: twoway's markers carry no fill-opacity; every Scatter in `S16_FILLS` has `fill_alpha` and `line_alpha` 1 in both modes |
| OB-11 | `bar mpg rep78` under s2color and s1rcolor: twoway's fill equals the VBar's `fill_color` (case-folded) in both modes, `fill_alpha` 1 |
| OB-12 | `bar …, fcolor(navy) fintensity(V)`, V in 50, 150 and 0 under s2color, 50 under s1rcolor: twoway's fill equals dash's in both modes |
| OB-13 | `area mpg weight` and `rarea lo hi weight` (fill only) and `rbar …, color(red)` (fill `#FF3333`, outline `#FF0000`): equal in both modes |
| OB-14 | `lfitci mpg weight, fintensity(150)`: twoway's band `#808080` equals the VArea's fill in both modes |
| OB-15 | `bar …` under sttrans: `#486C8C` at 0.20 in twoway; dash's VBar the same colour at `fill_alpha` 0.2 in both modes |
| OB-16 | `bar …, fintensity(abc)`: twoway's log holds `named style abc not found in class intensity`; dash's log holds one note naming `fintensity(abc)`; both draw `#1A476F` |
| OB-17 | the served app after the move: `S16_SAME_AFTER` = 1 for the commands of OB-10, OB-11 and OB-12 |

**Area scripts.** No case is added: nothing is newly refused and no Stata-side message changes. `test/test_option_validation.cscript:49`'s header comment for OV-21 is corrected in place to "rc 0 (drawn darker, as twoway draws it)".

## TDD test stubs

All in the new `test/test_intensity_blend.py` unless named. `[mode]` is parametrised over `("standalone", "served")` through `test_scheme_resolution._draw(spec, mode)` and `tp._spec` (`test_mode_parity`); a user scheme is written into `tmp_path` and `monkeypatch.chdir(tmp_path)` as `test_scheme_consumption.py:541-570` does; the served move uses `test_served_linked_views._served_doc` and `_fire`. Colours are compared lower-case.

### Regression tests written by 16-01 (each FAILS at the batch-6 base; expectations are twoway's values of E3)

- Test: `_blend_intensity` above 1 divides and clamps: (`#1a476f`, 1.5) `#112f4a`, 10 `#03070b`, 50 `#010102`, 60 `#010304`, 9999.99 `#010304`; (`#ffffff`, 99.99) `#030303` — `test/test_intensity_blend.py::TestTheBlend::test_above_full_divides_and_clamps`
- Test: under `naturally_white` 0 it multiplies and clamps: navy .5 `#0d2438`, 1.5 `#276ba7`, 0 `#010304`, .01 `#010304`; red 0 `#010000`; `#c86403` .01 `#432101`; yellow 100 `#ffff00`, .8 `#cccc00` — `…::TestTheBlend::test_naturally_white_0_multiplies`
- Test: `_fintensity_value`: `50` .5, `150` 1.5, `-5` 0.0, `1d3` 10.0, `inten200` 2.0, `max` 9999.99, `full` 1.0, `inten50` .5, `.` and `""` None, with no note — `…::TestTheFintensityParser::test_numbers_names_and_missing`
- Test: `abc`, `inten150`, `inten55`, `INTEN50`, `Full`, `.a`, `()` and a 200-character string give 1.0 and exactly one note each naming `fintensity(` — `…::TestTheFintensityParser::test_an_unknown_name_is_full_with_one_note`
- Test: a scheme `{"intensity p1bar": "inten200", "intensity p1area": "150"}` (rebuilt as `test_scheme_resolution._props_scheme` does) carries `p_bar_intensity[0] == 2.0` and `p_area_intensity[0] == 1.5` — `…::TestTheSchemeChains::test_intensity_above_full_reaches_the_chains`
- Test [mode]: scatter, connected, dot and rconnected under s2color, stcolor, s1rcolor and economist draw every Scatter at `fill_alpha` 1.0 and `line_alpha` 1.0 — `…::TestMarkersAreOpaque::test_default_markers`
- Test [mode]: default fills: bar s2color `#486c8c`, bar layer 2 `#a65d62`, stcolor bar `#489dff`, s1rcolor bar `#cccc00`, area `#486c8c`, rbar `#486c8c`, rarea `#486c8c` (fill colour only), each `fill_alpha` 1.0 but rarea — `…::TestFillsAreAnOpaqueBlend::test_default_fills`
- Test [mode]: user colours take the intensity: bar `fcolor(yellow)` and `color(yellow)` `#ffff33`, area `fcolor(yellow)` `#ffff33`, rarea `color(red)` `#ff3333`, rbar `color(red)` fill `#ff3333` and `line_color` `#ff0000`, bar `bfcolor(yellow)` `#ffff33` (dash's alias of fcolor()) — `…::TestFillsAreAnOpaqueBlend::test_user_colours_take_the_intensity`
- Test [mode]: bar `fcolor(navy%50)` `#486c8c` at 0.5; sttrans bar and sttrans `fcolor(navy)` `#486c8c` at 0.2 — `…::TestFillsAreAnOpaqueBlend::test_an_opacity_is_kept_beside_the_blend`
- Test [mode]: bar `fcolor(navy) fintensity(V)` under s2color: 50 `#8da3b7`, 150 `#112f4a`, 1000 `#03070b`, 0 and -5 `#ffffff`, 5000 `#010102`, 6000 and 9999 `#010304`, `inten200` `#0d2438`, `max` `#010304`, `full` `#1a476f`, `inten50` `#8da3b7`, `.` `#486c8c`; every `fill_alpha` 1.0; no note — `…::TestFintensityIsABlend::test_the_measured_values`
- Test [mode]: `abc`, `inten150`, `INTEN50`, `Full`, `.a` draw `#1a476f` with one note naming `fintensity(<value>)` — `…::TestFintensityIsABlend::test_an_unknown_intensity_is_full_with_the_note`
- Test [mode]: s1rcolor bar `fcolor(navy)`: 50 `#0d2438`, 150 `#276ba7`, 0 and 1 `#010304`; `fcolor(red) fintensity(0)` `#010000`; area `fcolor(navy) fintensity(50)` `#0d2438` — `…::TestFintensityIsABlend::test_naturally_white_0`
- Test [mode]: area, rarea, rbar and histogram with `fcolor(navy) fintensity(50)` fill `#8da3b7` — `…::TestFintensityIsABlend::test_every_fill_type`
- Test [mode]: lfitci `fintensity(150)` band `#808080`; s1rcolor `fintensity(50)` `#282828` — `…::TestCiBandIntensity::test_the_measured_bands`
- Test [mode]: the nonselection and muted copies' `fill_color` is the drawn colour, twoway's literal hex: bar `fintensity(50)` `#8da3b7`, bar `fcolor(yellow)` `#ffff33`, area `fcolor(yellow)` `#ffff33`, histogram `fcolor(red)` `#ff0000`, rbar `color(red)` `#ff3333`; the nonselection `fill_alpha` is not the glyph's (red at the base, where S08's sync copies the unblended colour) — `…::TestBrushedFillsKeepTheBlend::test_the_nonselection_copy_has_the_drawn_colour`
- Test: served, three one-layer graphs (`scatter mpg weight`; `bar mpg rep78`; `area mpg weight, fcolor(navy) fintensity(50)`, each its scheme's p1) with a `foreign` dropdown filter, `_fire(doc, "foreign", "Foreign")`: every glyph's `fill_color`/`fill_alpha`/`line_alpha` before and after the move equals E3's values (`#1a476f` 1/1, `#486c8c` 1, `#8da3b7` 1) — `…::TestAfterAFilterMove::test_the_served_app_redraws_the_same_colours`
- Test [mode]: user scheme s16dn (E3) draws bar and area `#a3b5c5`; a scheme with only `#include s2color`, `intensity bar inten40`, `intensity area inten40` draws `#486c8c` at 1.0, with no note — `…::TestGraphBarKeysAreNotRead::test_intensity_bar_and_area_are_ignored`
- Test: `SchemeParser("s2color")` has no `bar_alpha` and no `area_alpha` — `…::TestGraphBarKeysAreNotRead::test_the_parser_no_longer_carries_them`
- Test [mode]: histogram `fcolor(navy)` under s1rcolor `#1a476f` at `fill_alpha` 1.0 (twoway's full intensity; was 0.8) — `…::TestTheHistogramUntilS24::test_s1rcolor_is_opaque`
- Test: the served module's `GlyphMapper` has `_fintensity_value` and its `SchemeParser._INTENSITY` holds `inten200` and `max` — `…::TestBothModesShareTheCode::test_the_served_mapper_has_the_reader`

**Guard tests (pass before and after; listed apart in the failure file):**
- `…::TestTheBlend::test_below_full_is_unchanged` (navy .8 `#486c8c`, .5 `#8da3b7`, 0 `#ffffff`, red .5 `#ff8080`, `-1` `#ffffff`, `"notahex"` returned as given).
- `…::TestMarkersAreOpaque::test_a_declared_or_asked_opacity_still_wins` [mode] (sttrans 0.2; `mcolor(navy%50)` 0.5; `malpha(40)` 0.4).
- `…::TestCiBandIntensity::test_the_default_band_and_negative_intensity` [mode] (default `#c0c0c0`; `fintensity(-5)` `#ffffff`).
- `…::TestTheHistogramUntilS24::test_s2color_keeps_the_full_colour` [mode] (histogram default and `fcolor(navy)` `#1a476f` at 1.0 under s2color, twoway's full intensity).
- `…::TestAfterAFilterMove::test_no_page_script_writes_a_fill` (no `fill_color`/`fill_alpha` assignment in any CustomJS `code` of a built saved page or in any module-level string of `dash_render` ending `_JS`).

### Added by 16-03 (fixture-driven)

- Test [probe, mode]: every probe of `intensity_truth.json` whose `owner` is not `S24` (and not `navy_fi_5200`) is drawn by dash with twoway's fill and opacity — `test/test_intensity_blend.py::TestStataFills::test_each_probe`
- Test: the fixture's `_meta` holds `stata_version`, `born_date`, `dash_commit` and `extracted`, and every probe has `rc` 0 — `…::TestTheFixture::test_the_meta_stamp` (guard)
- Test: the fixture's notes for `fi_abc`, `fi_inten150`, `fi_INTEN50`, `fi_Full`, `fi_dota` hold "not found in class intensity" and `fi_dot` and `fi_full` none — `…::TestTheFixture::test_twoways_notes_are_recorded` (guard)

### Other files

- `test/test_scheme_visual_truth.py::test_marker_opacity_is_what_stata_drew[name-i]` (new, beside `test_marker_colour_is_what_stata_drew`): `GlyphMapper(scheme=_parser(name)).map_scatter` at `color_idx=i` draws `fill_alpha` and `line_alpha` 1.0 for p1-p3 of the four recorded schemes (GAPS2 D11 plan step 3; the PNG fixture holds the unblended hexes). Fails at the base.
- `test/test_mode_parity.py`: the six CORPUS cases of TR-16.12 (G3).
- The flips of E6, in their own files.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| The blend and the reader (units) | pytest `TestTheBlend`, `TestTheFintensityParser`, `TestTheSchemeChains` | — | n/a (pure functions; the served module's copy checked by `TestBothModesShareTheCode`) |
| Markers, fills, fintensity, bands, brushing | pytest classes of `test_intensity_blend.py` | E3 literals | yes, `[mode]` |
| Every measured probe | pytest `TestStataFills` | `intensity_truth.json` | yes |
| After a filter move | served `_fire`; saved static script scan | — | yes |
| Parity, every plot type and the new cases | `python3 -m pytest test/test_mode_parity.py -q -n0` (G3) | — | yes |
| Live twoway against both modes | `test_wp30_truth.cscript` S16 block, OB-10..OB-17, `WP30_ONLY=S16` | live SVG | yes, and after a served move |
| Visual-truth PNG record | `test_scheme_visual_truth.py::test_marker_opacity_is_what_stata_drew` | `test/fixtures/scheme_visual/` | saved mapper |
| Served names | `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads` (G4) | — | served |
| Registries | `test_function_test_map.py`, `test_program_coverage_map.py` | — | — |
| Tracking | `test_tracking_documents.py` (G5) | — | — |
| Whole suite | one full run through the queue (index E1) | — | — |

**Acceptance criteria.**
- **AC-16.1** Every Scatter drawn by scatter, connected, dot and rconnected has `fill_alpha` and `line_alpha` 1.0 under the shipped schemes except sttrans (0.2), in both modes and after a served move; `%NN` and `malpha()` still set their opacity.
- **AC-16.2** Every non-S24 probe of `intensity_truth.json` matches dash's fill and opacity exactly in both modes; OB-10..OB-17 print PASS.
- **AC-16.3** `fintensity()` is never refused by the renderer; an unknown name prints one note and draws full intensity; `.` and every number print nothing.
- **AC-16.4** A brushed-away fill's nonselection and muted copies have the drawn colour.
- **AC-16.5** `SchemeParser` has no `bar_alpha`/`area_alpha`; a user scheme's `intensity bar`/`area` change nothing.
- **AC-16.6** The E6 flips each carry a `Flipped:` line; no test is deleted; the single-y digest is re-derived with its reason.
- **AC-16.7** `test_mode_parity.py` is green with the six new cases; G4 and the registries are green; one full run is green.

## Tasks

**Commit boundary.** Tasks 16-01 to 16-16 form the one commit of entry `P1.2b`, subject `Draw markers opaque and every intensity as an opaque blend (WP-30 P1.2b)`, made by 16-16 on `wp30-s16` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s16` (`$WT`), after one full run through the queue. `$S` is `<scratch>/s16` (`<scratch>`: the orchestrator's WP-30 scratch directory, index "Deltas"). Every command runs from `$WT` unless it names the main checkout. The body:
1. opens with `<scratch>/16-P1.2b-failure.txt`;
2. then the measured defect (Evidence E2) and what changed, where, in both modes;
3. then one line each: `Regression: test/test_intensity_blend.py::<Class>::<test> -- failed at <batch-6 base sha> with <text>`; `Flipped: <node> -- <old expectation> was wrong because <why>` (every E6 row and any extra flip in `$S/16-flips.txt`); `Fixture: test/fixtures/intensity_truth.json (scripts/extract_intensity_truth.do)`; `BUGS.md: "<WP30_OPEN["P1.2b"]>" (closed)`; one line saying why the single-y digest moved (R10: the marker alpha 0.8 became 1.0).

No subject, body, BUGS line, CHANGELOG line or help line names a tool or vendor (G7): `grep -Eic 'claude|anthropic'` prints 0 on the message file before and on `git log -1 --format=%B` after. Never stage `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.ultraplan/` or any `*.html` (E7, G6).

<task type="auto" id="16-01">
  <name>Write the failing intensity regression tests</name>
  <files>test/test_intensity_blend.py</files>
  <action><![CDATA[
    Run `mkdir -p "$S"`; check that `git -C $WT rev-parse HEAD` equals `<scratch>/batch-6-base.txt` and `git -C $WT branch --show-current` prints `wp30-s16`, else stop. Read `<scratch>/batch-6-impact.txt` and confirm it records the HIGH warnings for _scheme_alpha, _apply_fill_opts, _blend_intensity, _ci_band_style and _ci_band_glyphs with their approval (index 6.0); if one is missing, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout (never in $WT), append it, and report every HIGH or CRITICAL result before editing. Check S08's sync (A37): `python3 -c` a bar with `fcolor(yellow)` through `test_scheme_resolution._draw` in both modes and confirm its `nonselection_glyph.fill_color` and `muted_glyph.fill_color` equal the glyph's `#ffff00`; if not, S08's sync does not follow `_apply_fill_opts`: stop and report (S08 owns the sync). Check S15's attributes: `grep -nE 'self\.(naturally_white|p_bar_intensity|p_area_intensity)\b' $WT/dash_render.py` must show all three assigned in `SchemeParser._init_properties`, and `grep -n 'system naturally_white' $WT/dash-s1rcolor.scheme` must print a line with 0; if any is missing or renamed, stop and report (S15 owns them). Create test/test_intensity_blend.py with every test of "TDD test stubs / Regression tests written by 16-01" and the five guard tests, with exactly those class and test names, modes through `test_scheme_resolution._draw` and `MODES`, specs through `test_mode_parity._spec`, user schemes written into `tmp_path` under `monkeypatch.chdir`, the served move through `test_served_linked_views._served_doc` and `_fire`, notes counted with S06's needle helpers, and every expectation written as the literal twoway hex of Evidence E3 (never computed through dash_render). Run `python3 -m pytest test/test_intensity_blend.py -q -n0 -p no:cacheprovider -rf > "$S/16-01.log" 2>&1` and write `<scratch>/16-P1.2b-failure.txt`: the base sha, each FAILED line with its first assertion text, then under "Guard tests (pass before and after)" the five guards. Do not touch dash_render.py; do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/16-01.log"` prints at least 20 (every regression stub fails in at least one node); `grep -E '^FAILED.*(test_below_full_is_unchanged|still_wins|negative_intensity|keeps_the_full_colour|writes_a_fill)' "$S/16-01.log"` prints nothing; `test -s <scratch>/16-P1.2b-failure.txt`.]]></verify>
  <done>Every 16-01 regression test existed with twoway's literal values and was shown failing on the unfixed tree, the guards passed, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="16-02">
  <name>Extract the intensity truth from Stata</name>
  <files>scripts/extract_intensity_truth.do, test/fixtures/intensity_truth.json</files>
  <action><![CDATA[
    Create scripts/extract_intensity_truth.do exactly as "Stata truth" specifies: S02's root rule (DASH_REPO, else c(pwd) holding dash.ado and test/run_all_cscripts.do, else exit 601), `adopath ++ "<root>/"` and `global dash_nobrowser 1` first, then `version 19`, the two user schemes written with `file write` into a tempfile-named directory under c(tmpdir) that is then `adopath ++`-ed, the `_ob_probe` program, every probe of the table, the D12 stamp through `shell git -C` into a tempfile read back with `file read`, and one trailing python block that reads the SVGs through scripts/svg_truth.py (`svg_document`, `svg_fills`, `svg_marker_fills`), never calls Stata, never uses shell=True, writes a backtick as \x60 and prints `intensity_truth: wrote <N> probes`. Run `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_intensity_truth.do"` and read `$S/extract_intensity_truth.log`. Check the fixture against Evidence E3 (bar s2color #486C8C; s1rcolor #CCCC00; fi 150 #112F4A; fi 6000 #010304; fi_s1r 50 #0D2438; fi_s1r 0 #010304; band 150 #808080; sttrans bar opacity 0.20; s16dn bar #A3B5C5; fi_abc's notes hold "not found in class intensity"); a difference is investigated and reported, never patched by hand (R7). Run `git add -f test/fixtures/intensity_truth.json`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/intensity_truth.json'));m=d['_meta'];assert all(k in m for k in ('stata_version','born_date','dash_commit','extracted'));p=d['probes'];assert len(p)>=80 and all(v['rc']==0 for v in p.values());print(len(p))"` prints the probe count; `git ls-files test/fixtures/intensity_truth.json` prints the path; `grep -c 'intensity_truth: wrote' "$S/extract_intensity_truth.log"` prints 1 and the log holds no uncaptured `r(` error.]]></verify>
  <done>twoway's fill colour and opacity for every marker, bar, area, range, histogram, band, intensity and user-scheme probe were recorded in a stamped fixture staged with git add -f.</done>
</task>

<task type="auto" id="16-03">
  <name>Add the fixture-driven and record tests</name>
  <files>test/test_intensity_blend.py, test/test_scheme_visual_truth.py</files>
  <action><![CDATA[
    Add `TestStataFills::test_each_probe` (parametrised over the fixture's probe ids, minus every probe whose `owner` is "S24" and minus `_meta.excluded`, and over MODES; it rebuilds each probe's command as a dash spec through a table in the test file mapping probe kind to plot type and options, and compares the drawn glyph's `fill_color` (lower case) and opacity with the probe's `fill`/`opacity`, the rbar probe's `line_color` with its `stroke`), `TestTheFixture::test_the_meta_stamp` and `TestTheFixture::test_twoways_notes_are_recorded` to test/test_intensity_blend.py, reading test/fixtures/intensity_truth.json once at module level from `Path(__file__).parent / "fixtures"`. Add `test_marker_opacity_is_what_stata_drew(name, i)` to test/test_scheme_visual_truth.py directly after `test_marker_colour_is_what_stata_drew` (188-196), parametrised the same way, drawing `GlyphMapper(scheme=_parser(name)).map_scatter` on a three-row source at `color_idx=i` and asserting `fill_alpha` and `line_alpha` 1.0, with a docstring citing GAPS2 D11 plan step 3. Run both files on the unmodified renderer with `-q -n0 -p no:cacheprovider -rf > "$S/16-03.log" 2>&1`, and append to `<scratch>/16-P1.2b-failure.txt` the new FAILED lines and the two fixture guards under the guard heading. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/16-03.log"` prints more than in `$S/16-01.log`; `python3 -m pytest test/test_intensity_blend.py -q -n0 -p no:cacheprovider -k "TestTheFixture"` passes; `grep -c 'test_marker_opacity_is_what_stata_drew' "$S/16-03.log"` is at least 1.]]></verify>
  <done>The fixture-driven tests and the visual-truth opacity test failed on the unfixed renderer, the fixture guards passed, and both lists were added to the saved failure text.</done>
</task>

<task type="auto" id="16-04">
  <name>Write the one blend and reader</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Rewrite `GlyphMapper._blend_intensity` (8292-8305) as TR-16.1 defines it, keeping it a staticmethod, with the docstring TR-16.1 asks for. In `SchemeParser`, add `"inten200": 2.0` and `"max": 9999.99` to `_INTENSITY` (5970-5974) with a comment naming /Applications/StataNow/ado/base/style/intensity-*.style's `set val` values, and give `_intensity` (6577) the `clamp=True` keyword of TR-16.3 (a name's value is `min(1.0, v)` and a number is clamped to [0, 1] when clamp is true, exactly as today; unclamped otherwise, negative read as 0). Add `@staticmethod _fintensity_value(raw)` to `GlyphMapper` directly after `_blend_intensity`, as TR-16.2 defines it, reading names from `SchemeParser._INTENSITY` (exact case) and numbers through `OptionTranslator.stata_number`. Under the `# WP-30 S16 (P1.2b): Intensity as an opaque blend (P1.2 part b, M1)` anchor of test/function_test_map.py add the `GlyphMapper._fintensity_value` key, and repoint `GlyphMapper._blend_intensity` (189) in place, as TR-16.11 gives them.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_intensity_blend.py -q -n0 -p no:cacheprovider -k "TestTheBlend or TestTheFintensityParser"` passes; `python3 -m pytest test/test_scheme_coercion.py test/test_ci_band_style.py test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>One blend carried twoway's rule above and below full intensity under both naturally_white values with Stata's clamp, and one reader read fintensity() as twoway does, both mapped to their tests.</done>
</task>

<task type="auto" id="16-05">
  <name>Read the bar and area chains unclamped</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `SchemeParser._init_properties`, make S15's two readers of `p_bar_intensity` and `p_area_intensity` call `_intensity(..., clamp=False)` (change nothing else of S15's lines; leave `p_other_band_styles` at 7124-7129 as it is, D-16e). Leave `_FALLBACK_PROPS`, every scheme file and the extractor untouched. Rewrite `SchemeParser.default_alpha`'s docstring sentence that says the declared opacity "wins over fill_alpha, bar_alpha and area_alpha" (7228-7232) to say an intensity is a colour and a declared opacity is the only scheme opacity.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_intensity_blend.py -q -n0 -p no:cacheprovider -k "TestTheSchemeChains"` passes; `python3 -m pytest test/test_scheme_coercion.py test/test_scheme.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The scheme's bar and area intensity chains carried values above full, as twoway reads them, and every other intensity reader was unchanged.</done>
</task>

<task type="auto" id="16-06">
  <name>Draw markers opaque and retire bar keys</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Change `GlyphMapper._scheme_alpha` (9727-9742) to `_scheme_alpha(self, color_idx, plot_type) -> float`, returning `self.scheme.default_alpha(color_idx, plot_type)` when it is not None and 1.0 otherwise, with the docstring of TR-16.5. Update its four callers: `map_scatter` (9836-9837) to `alpha=self._scheme_alpha(color_idx, "scatter")` with the comment above it saying markers are opaque as twoway draws them unless an opacity is declared or asked for; `map_area` (10091), `map_bar` (10239) and `_histogram_quads` (12435) to the two-argument form (their fill colour is 16-07's). Do not edit `_apply_marker_opts`, `map_connected`, `map_dot` or `map_rconnected`, which draw through map_scatter. Now that nothing reads them, delete `self.bar_alpha` and `self.area_alpha` (6953-6954) and rewrite the comment above `self.fill_alpha` (6951) as TR-16.4 says, keeping `self.fill_alpha`. Repoint the `GlyphMapper._scheme_alpha` key (198) of test/function_test_map.py in place to `test/test_intensity_blend.py::TestMarkersAreOpaque::test_default_markers`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_intensity_blend.py -q -n0 -p no:cacheprovider -k "TestMarkersAreOpaque"` passes in both modes; `grep -c '_scheme_alpha(' dash_render.py` prints 5 (the definition and four calls); `grep -nE '(scheme|self)\.(bar_alpha|area_alpha)' dash_render.py` prints nothing; `python3 -m pytest test/test_function_test_map.py -q -n0 -p no:cacheprovider` and `python3 -m pytest test/test_intensity_blend.py -q -n0 -p no:cacheprovider -k test_the_parser_no_longer_carries_them` pass.]]></verify>
  <done>Scatter, connected, dot and rconnected markers were drawn opaque in both modes unless a colour's %NN, the scheme's declared opacity or malpha() set one, and graph bar's intensity keys were no longer parsed.</done>
</task>

<task type="auto" id="16-07">
  <name>Blend the five fill mappers opaquely</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Rewrite `GlyphMapper._apply_fill_opts` (8807-8860) as TR-16.6 defines it (signature `(self, renderer, options, base=None, intensity=1.0)`, the order fcolor, falpha/fa, fintensity, blend; the nonselection fill colour, written before S08's sync, which is kept where S08 put it; never an alpha from an intensity). Then change `map_bar` (10231-10283), `map_rbar` (13056-13105), `map_area` (10086-10110), `map_rarea` (12981-13001) and `_histogram_quads` (12423-12449) as TR-16.7 says: resolve `_fill_base` and `_f`, create the glyph at the blended colour, write `color()`/`bfcolor()` into `_fill_base` (keeping each bad-name note and each outline write), make map_area's default border colour `_fill_base`, keep rarea's `fill_alpha=0.5` and rbar's creation alphas, and end each with `self._apply_fill_opts(r, options, base=_fill_base, intensity=_f)`. A line S14 changed in these mappers (bar widths, the spacing tag) is kept as S14 left it.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_intensity_blend.py -q -n0 -p no:cacheprovider -k "TestFillsAreAnOpaqueBlend or TestFintensityIsABlend or TestBrushedFillsKeepTheBlend or TestGraphBarKeysAreNotRead or TestTheHistogramUntilS24 or TestAfterAFilterMove or TestBothModesShareTheCode"` passes; `grep -c 'self._apply_fill_opts(r, options, base=' dash_render.py` prints 5.]]></verify>
  <done>Bar, rbar, area and rarea fills were the resolved colour blended at the layer's intensity, histogram fills opaque at full intensity, fintensity() a blend, and the brushed-away copy in the drawn colour, in both modes.</done>
</task>

<task type="auto" id="16-08">
  <name>Blend the band and re-measure pins</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `GlyphMapper._ci_band_style` replace the fintensity block (8376-8386) with the `_fintensity_value` call of TR-16.8, and in `_ci_band_glyphs` (8418) pass `self.scheme.naturally_white` to `_blend_intensity`. Run test/test_intensity_blend.py and test/test_scheme_visual_truth.py (all green expected), then the 52 candidate files of the prototype (`cd $WT/test && grep -l -i 'fill_alpha\|fintensity\|fill_color\|line_alpha\|\.alpha\b\|1a476f\|_SHA256\|intensity\|bar_alpha\|area_alpha' test_*.py`) plus test_size_units.py and S15's test_scheme_chrome.py (S15 created no test_default_look.py), at `-q -n 6 -p no:cacheprovider`, into `$S/16-08.log`. Write `$S/16-red.txt`: every failing node classified as one of F1-F46 (Evidence E6) or as new. A new node is investigated: if it pins intensity-as-alpha, a marker at 0.8 or an unblended fill, add it to `$S/16-flips.txt` with its old expectation and reason; anything else is a defect of the fix, which is corrected before going on. A failure in S08's brushed-copy tests is a regression of S08's fix (A37): it is corrected in S16's code, never flipped, except a pin of a marker alpha of 0.8 or an unblended fill that S16 changes on the glyph itself, which is flipped to the glyph's new value with the copies still equal to it (E6's guard paragraph).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_intensity_blend.py test/test_scheme_visual_truth.py test/test_ci_band_style.py -q -n0 -p no:cacheprovider` passes; every FAILED node of `$S/16-08.log` appears in `$S/16-red.txt` with a class (F-id or a `$S/16-flips.txt` line).]]></verify>
  <done>The CI band's fintensity() followed twoway's rule under both naturally_white values, and the full list of pinned tests the fix turns red was measured and classified.</done>
</task>

<task type="auto" id="16-09">
  <name>Flip the glyph and server pins</name>
  <files>test/test_glyphs.py, test/test_server.py, test/test_html_output.py</files>
  <action><![CDATA[
    Flip F1-F29 in place as Evidence E6 says, editing only the named tests: change each expected value to the E6 expectation (the literal hex, never computed through dash_render, except F15-F17, whose expectations are built from the scheme's default colour through `GlyphMapper._blend_intensity` as E6 states), rewrite each docstring to say what twoway draws and cite Evidence E3, and rename only F21 (`test_area_fintensity_sets_alpha` → `test_area_fintensity_blends_the_colour`). Record one `Flipped: <node> -- <old expectation> was wrong because <why>` line per node in `$S/16-flips.txt` (F21 names both node ids). Delete nothing.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_glyphs.py test/test_server.py test/test_html_output.py -q -n 6 -p no:cacheprovider` passes; `grep -c '^Flipped: test/test_\(glyphs\|server\|html_output\)' "$S/16-flips.txt"` prints at least 29; `git -C $WT diff --stat -- test/test_glyphs.py test/test_server.py test/test_html_output.py` shows no test function removed (`git -C $WT diff -- test/test_glyphs.py test/test_server.py test/test_html_output.py | grep -c '^-    def test_'` equals the number of renamed tests, 1).]]></verify>
  <done>The glyph, server and HTML pins that asserted unblended fills or intensity as alpha asserted twoway's blended, opaque colours instead.</done>
</task>

<task type="auto" id="16-10">
  <name>Flip the colour and help-claim pins</name>
  <files>test/test_html_verification.py, test/test_help_claims_7.py, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Flip F30-F34 in place as Evidence E6 says. F30 (ALP-16): draw `base` and `r` under `GlyphMapper(scheme=SchemeParser("sttrans"))` so the base alpha is 0.2 and a clamp to 1.0 is still caught; rewrite its comment (markers are opaque by default since WP-30 P1.2b). F32/F33: the expected fill is the colour at the layer's p#bar or p#area intensity for bar, rbar, area and rarea (literal hexes per colour used by the test), histogram rows unchanged. F34: only the two colour sets of the rarea rows change (`{"#d68592"}` under sttrans, `{"#a65d62"}` under s2color); the alpha comparison and every other row stay for S24. Append one `Flipped:` line per node to `$S/16-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_html_verification.py test/test_help_claims_7.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` passes; `grep -c '^Flipped: test/test_\(html_verification\|help_claims_7\|help_claims_8\)' "$S/16-flips.txt"` prints at least 5.]]></verify>
  <done>The alpha, colour-alias and help-claim pins asserted opaque markers and blended fills, with the rarea rows left to S24 for their opacity.</done>
</task>

<task type="auto" id="16-11">
  <name>Flip the alias, validation and index pins</name>
  <files>test/test_color_alias.py, test/test_option_validation.py, test/test_ci_plot_index.py</files>
  <action><![CDATA[
    Flip F35-F37 in place as Evidence E6 says: F35 and F36 expect `color()`'s hex at the layer's intensity (literal hexes) and keep their no-note assertions; F37 expects the rarea fill to be the plot index's p# colour at the p#area intensity, built through `GlyphMapper._blend_intensity` from the colour the test already derives, so the plot-index rule it pins is unchanged. Also confirm `test_option_validation.py`'s STYLE_CASES row `("area", {"fintensity": "abc"}, "fintensity")` still finds exactly one note naming fintensity() in both modes (unchanged). Append the `Flipped:` lines to `$S/16-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_color_alias.py test/test_option_validation.py test/test_ci_plot_index.py -q -n 6 -p no:cacheprovider` passes; `grep -c '^Flipped: test/test_\(color_alias\|option_validation\|ci_plot_index\)' "$S/16-flips.txt"` prints at least 3.]]></verify>
  <done>The colour-alias, silent-site and plot-index pins expected blended fills while keeping what each test was written to guard.</done>
</task>

<task type="auto" id="16-12">
  <name>Flip the scheme parser pins</name>
  <files>test/test_scheme_consumption.py, test/test_scheme.py, test/test_scheme_fidelity.py</files>
  <action><![CDATA[
    F39: remove `"bar_alpha", "area_alpha"` from `test_the_key_is_read_somewhere`'s parameter list (595) and add, directly after `test_gsize_text_is_retired_because_stata_draws_nothing_with_it`, `test_graph_bars_intensity_keys_are_retired_because_twoway_ignores_them` parametrised over the two names, asserting `not hasattr(SchemeParser("s2color"), attr)` and `_scheme_attr_reads(attr) == []`, its docstring quoting Evidence E3's user-scheme measurement. F40: the area of `test_a_schemes_area_intensity_and_minor_grid_reach_both_modes` is `#486c8c` at `fill_alpha` 1.0 in both modes (`intensity area inten40` ignored), the minor-grid assertions kept, the docstring rewritten. F44: rename and rewrite `test_bar_alpha_is_float_between_0_and_1` as E6 says. F45: add `RETIRED_INTENSITY` next to `ALPHA_SCALARS` (225-232) with the comment of E6 and read `actual` for those two props through the declared directive in `evaluate_scheme`'s intensity loop (471-482), leaving the unit count (288) unchanged. Append the `Flipped:` lines to `$S/16-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_consumption.py test/test_scheme.py test/test_scheme_fidelity.py test/test_scheme_fallback_provenance.py -q -n 6 -p no:cacheprovider` passes; `grep -c 'bar_alpha' test/test_scheme_consumption.py` is at least 1 (the retired-key test) and `grep -c '^Flipped: test/test_scheme\(_consumption\|_fidelity\)\?\.py' "$S/16-flips.txt"` prints at least 4.]]></verify>
  <done>The scheme tests recorded graph bar's intensity keys as retired, still checked their transcription in the shipped files, and pinned the unclamped bar chain.</done>
</task>

<task type="auto" id="16-13">
  <name>Flip resolution, key and digest pins</name>
  <files>test/test_scheme_resolution.py, test/test_emptied_layer_style.py, test/test_varlist_expansion.py</files>
  <action><![CDATA[
    F41: set `PINNED_ALPHAS["Scatter"] = (1.0, 1.0)` and `PINNED_EXCEPTIONS = {}` (551-561), rewriting the comment above them to say markers are opaque and s1rcolor's bar intensity is now a colour (WP-30 P1.2b). F42: the fill is `#ff3333` at 0.6 in both modes. F38: in `TestTheKeyIsTwoways::test_the_empty_layer_draws_in_twoways_key_colour`, for a VBar or VArea compare the fill with `{GlyphMapper._blend_intensity(c, f, sp.naturally_white) for c in colours}`, f the scheme's `p_bar_intensity` (bar, rbar) or `p_area_intensity` (rarea) at the probed layer's index, with a comment that the fixture records the key's stroke. F43: re-derive `_SINGLE_Y_BASELINE_SHA256` (343) by running the test, taking the digest it reports, and writing it with the trailing comment `# <old> -> <new>: P1.2b markers drawn opaque (alpha 0.8 -> 1.0)` (R10). Append the `Flipped:` lines to `$S/16-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_resolution.py test/test_emptied_layer_style.py test/test_varlist_expansion.py -q -n 6 -p no:cacheprovider` passes; `grep -c 'P1.2b markers drawn opaque' test/test_varlist_expansion.py` prints 1.]]></verify>
  <done>The opacity pins of every other scheme, the emptied-layer key comparison and the single-y digest matched the opaque drawing, each with its reason.</done>
</task>

<task type="auto" id="16-14">
  <name>Add parity cases and the truth block</name>
  <files>test/test_mode_parity.py, test/test_wp30_truth.cscript, test/test_wp29_truth.cscript</files>
  <action><![CDATA[
    Append TR-16.12's six `_case` entries at the end of `CORPUS` in test/test_mode_parity.py. Fill S16's stub in test/test_wp30_truth.cscript between its own start and end lines with OB-10..OB-17 as "Stata truth / Truth block" specifies, the helpers `_s16_page`, `_s16_app` and `_s16_svg` (declaring `version 19`) directly above S16's header, files written only under `` `w30_work' `` and erased before the end line. Flip F46 in test/test_wp29_truth.cscript's `_ew_colour`/`_ew_check` (4513-4540) as E6 says, editing only EW-02's comparison. Run `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider` (G3); then each cscript through the two-line driver from the worktree: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_test_wp30_truth.do"` and `WP30_ONLY=S16 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_wp30_truth.do"`; the same for test_wp29_truth.cscript with `WP29_ONLY=S12`, and for test_option_validation.cscript, test_bug_regressions.cscript and test_help_claims_2.cscript unset. Read each log; if `python_exec` was dropped (exit 222, a SKIP), restore it and re-run, since a skip is not a pass. Append F46's `Flipped:` line to `$S/16-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider` passes; `grep -c "OB-1[0-7] PASS" "$S/run_test_wp30_truth.log"` prints 8 with no `FAIL`; `grep -c "EW-0[23] PASS" "$S/run_test_wp29_truth.log"` prints 2; `test_option_validation: ALL CHECKS PASSED`, `test_bug_regressions` and `test_help_claims_2` end in their ALL CHECKS PASSED lines.]]></verify>
  <done>Both modes drew the same in the parity corpus's new cases, twoway's live drawing agreed with the saved page and the served app before and after a move, and WP-29's emptied-layer cases compared blended fills.</done>
</task>

<task type="auto" id="16-15">
  <name>Rewrite the help on intensity</name>
  <files>dash.sthlp, dash.ado, test/test_option_validation.cscript</files>
  <action><![CDATA[
    In dash.sthlp, Marker and Transparency Options (S16's under R3): add one paragraph after the `%NN`/`malpha()` paragraph (3268-3274) saying, in this order: markers are drawn opaque as twoway draws them unless a colour's %NN, a scheme's declared opacity (sttrans) or malpha() asks for one; a bar, rbar, area or rarea fill is its colour at the layer's intensity (the scheme's intensity p#bar or p#area, inten80 in the shipped schemes), opaque, so s2color's bar is #486C8C and fcolor(yellow) fills #FFFF33; fintensity() replaces that intensity as twoway draws it (blended towards white below 100, darker above it, fintensity(150) dividing each channel by 1.5; towards black under s1rcolor, whose scheme is not naturally white; 0 and negative values draw white, almost black under s1rcolor; fintensity(.) the layer's own; inten0 to inten100, inten200, full and max are the names, and any other name draws full intensity with a note; no value is refused); a histogram is filled at full intensity; a brushed-away fill is dimmed in its own colour. Correct in place the three sentences of Evidence E7 that S16 makes false: 3369-3372 (the opacity a scheme declares sets the opacity of the opaque colours its intensities give), 2583-2584 (the CI band's intensity: towards white below 100, darker above, towards black under s1rcolor) and 660-664 (for a fill intensity, full intensity is drawn). Correct dash.ado's comment at 1999-2001 and test/test_option_validation.cscript's OV-21 header comment (49) as E7 says; change no rule, case or code. Write no number a test of this section does not pin.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_8.py test/test_help_conformance.py test/test_option_validation.py -q -n 6 -p no:cacheprovider` passes; `grep -c 'derives from the intensities' dash.sthlp` prints 0; `grep -c '486C8C' dash.sthlp` is at least 1; `git -C $WT diff -U0 -- dash.ado | grep -c '^[-+][^-+/]'` prints 0 (comment lines only).]]></verify>
  <done>The help, dash.ado's rule comment and the validation script's header described opaque markers and intensity as an opaque blend as dash now draws them.</done>
</task>

<task type="auto" id="16-16">
  <name>Close P1.2b and commit the section</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP30_OPEN["P1.2b"]`; close that BUGS.md entry in place (`- [ ]` → `- [x]`, its open `  - Resolution:` line replaced by the Resolution of Notes, "Text for the closing task", indentation kept), and delete the `"P1.2b"` key line from `WP30_OPEN`. In CHANGELOG.md replace the `<!-- WP-30 P1.2b -->` marker in `### Results that change` with the five lines of Notes, each ending `(WP-30, P1.2b)` (R4). Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`; then `git -C $WT merge --no-edit main` (expect `Already up to date.`, else stop and report, E9); then one full run through the queue, `<scratch>/full_suite_queue.sh $WT <scratch>/16-full-1.log`, launched in the background and waited for on its `exit=` line, never relaunched (E1, E6 for the known flaky tests). Stage exactly dash_render.py, dash.sthlp, dash.ado, BUGS.md, CHANGELOG.md, scripts/extract_intensity_truth.do, test/test_intensity_blend.py, test/test_scheme_visual_truth.py, test/function_test_map.py, the flipped files of 16-09 to 16-14, test/test_option_validation.cscript, test/test_tracking_documents.py and any file named in `$S/16-flips.txt`, plus `git add -f test/fixtures/intensity_truth.json`; check `git diff --cached --name-status` (G6), write the message to `$S/16-msg.txt` per the commit boundary, run G7 on it, confirm `git -C $WT branch --show-current` prints `wp30-s16`, commit with `git commit -F "$S/16-msg.txt"`, run G7 on `git log -1 --format=%B`, and report the sha and the message path to the merger.
  ]]></action>
  <verify><![CDATA[`grep -E '^exit=0' <scratch>/16-full-1.log` matches and its summary shows 0 failed; `git log -1 --format=%s` ends `(WP-30 P1.2b)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.2b -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.2b": "' test/test_tracking_documents.py` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.2b was closed naming tests that exist, its CHANGELOG marker carried the measured old and new values, and the section's one green commit on wp30-s16 was ready for the merger.</done>
</task>

## Section completion criteria

- In both modes, before and after a served filter move: scatter, connected, dot and rconnected markers opaque unless `%NN`, sttrans or `malpha()`; bar, rbar, area and rarea fills the resolved colour blended at the p#bar/p#area chain intensity (unclamped), opaque unless an opacity is declared or asked for (rarea's 0.5 left to S24); histogram fills opaque at full intensity (D-16a); `fintensity()` and the CI band by E4's rule, never refused; brushed-away fills in the drawn colour.
- `intensity_truth.json` is new, stamped and staged with `git add -f`; every non-S24 probe matches; OB-10..OB-17 print PASS.
- `SchemeParser.bar_alpha`/`area_alpha` are gone; `_scheme_alpha(color_idx, plot_type)` returns only a declared opacity or 1.0.
- Every E6 row (and every extra flip recorded in `$S/16-flips.txt`) is flipped with a `Flipped:` line; no test was deleted; the single-y digest is re-derived with its reason.
- One green commit `(WP-30 P1.2b)` exists on `wp30-s16` with the failure text and the `Regression:`, `Flipped:`, `Fixture:` and `BUGS.md:` lines; the BUGS.md entry is closed in place, `WP30_OPEN` lost only `"P1.2b"`, the marker is replaced.
- Not edited: `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, `_build_filter_widgets`, `_apply_marker_opts`, `_apply_line_opts`, `_apply_mlabel_opts`, `_dash_dim_nonselection`, the copy lists, any scheme file, `scheme_truth.json`, `_FALLBACK_PROPS`, dash.ado's rules, dash_parse.mata, any runner block or hygiene pin, any tracking document beyond BUGS.md and CHANGELOG.md.

## Notes

### Q1, resolved by the review (D-16a)

**Q1 — the histogram's intensity between S16 (batch 6) and S24 (batch 8), D-16a.** Resolved as (a): M1 binds dash to twoway's picture, and register P1.4.2 gives the histogram's own style to P1.4a (S24), so (b) would move every s2color histogram away from twoway for no ruling's sake. The analysis is kept for the record. The manifest's scope and BR-30.2 say histogram fills "blend the p#bar/p#area intensity". Measured, twoway's histogram reads `intensity histogram` (`style/shadestyle-histogram.style`): `histogram mpg, fcolor(navy)` is `#1A476F` under s2color and s1rcolor and `#31597D` (inten90) under stcolor, so the p#bar chain would draw `#486C8C` there, moving every s2color histogram away from twoway for two batches (and changing every histogram colour twice before the release). Options:
- **(a)** Draw histograms at full intensity until S24 adds `intensity histogram` (this file's plan): s2color-family histograms keep today's colour, s1rcolor's become opaque (twoway's), the st family stays at full until S24.
- **(b)** Follow the manifest's text literally: histograms at the p#bar chain (`#486C8C` under s2color) until S24 replaces it.

**Ruling: (a).** For the record, under (b), `_histogram_quads` passes `_f = self.scheme.p_bar_intensity[color_idx % 15]`, `TestTheHistogramUntilS24` expects `#486c8c`, and F32's histogram rows, `test_glyphs.py::TestFillOptions::test_map_histogram_fcolor`, `test_html_output.py::TestColorRenderingAllPlotTypes::test_histogram_fcolor_in_html`, `TestOutputBackendAndVisualMarkers::test_histogram_model_has_fill_and_top`, `test_server.py::TestServerHistogramOptions::test_histogram_fcolor_applied` and `test_glyphs.py::TestHardeningGuards::test_histogram_empty_source_keeps_the_scheme_style` join E6 (the prototype measured them red under (b)).

### Text for the closing task (16-16)

**BUGS.md, P1.2b** (closed in place, `- [x]`):

`- Resolution: Fixed <ddmonyyyy> (WP-30, P1.2b). Markers are drawn opaque, as twoway draws them, unless a colour's %NN, the scheme's declared opacity or malpha() sets one: GlyphMapper._scheme_alpha returns only a declared opacity, so scatter, connected, dot and rconnected (both of its map_scatter calls) lost their alpha 0.8. Every intensity is an opaque blend through one function, GlyphMapper._blend_intensity, by twoway's measured rule (towards white below 100, divided above it, multiplied under naturally_white 0, with Stata's clamp to the smallest non-zero channel): GlyphMapper._apply_fill_opts and map_bar, map_rbar, map_area, map_rarea and _histogram_quads blend the resolved colour (the scheme's, color(), fcolor() or bfcolor()) at intensity p#bar or p#area, read unclamped through SchemeParser._intensity, histograms at full intensity until WP-30 section 24; fintensity() is read by GlyphMapper._fintensity_value (Stata's fourteen intensity names, case-sensitive, and any number, never refused; an unknown name draws full intensity with the note) and drawn as that blend on every fill and on the confidence band (_ci_band_style, _ci_band_glyphs); the brushed-away and muted copies of a fill keep the drawn colour; a user scheme's intensity bar and intensity area are no longer read (SchemeParser.bar_alpha and area_alpha retired), as twoway ignores them. The saved page and the served app draw the same, before and after a filter move. Pinned by test/test_intensity_blend.py::TestMarkersAreOpaque::test_default_markers, test/test_intensity_blend.py::TestFillsAreAnOpaqueBlend::test_default_fills, test/test_intensity_blend.py::TestFintensityIsABlend::test_the_measured_values, test/test_intensity_blend.py::TestFintensityIsABlend::test_naturally_white_0, test/test_intensity_blend.py::TestCiBandIntensity::test_the_measured_bands, test/test_intensity_blend.py::TestBrushedFillsKeepTheBlend::test_the_nonselection_copy_has_the_drawn_colour, test/test_intensity_blend.py::TestAfterAFilterMove::test_the_served_app_redraws_the_same_colours, test/test_intensity_blend.py::TestStataFills::test_each_probe, test/test_wp30_truth.cscript OB-10; fixture test/fixtures/intensity_truth.json. Residual, deferred (WP-30): rarea's own opacity 0.5 and the histogram's scheme colour and intensity are section 24's; fintensity(1e400), which dash.ado refuses and twoway draws white, is P2.14.`

**CHANGELOG.md**, `<!-- WP-30 P1.2b -->` in `### Results that change` replaced by:

```
- Markers are drawn opaque, as twoway draws them: `dash scatter mpg weight`, `connected`, `dot` and `rconnected` drew every marker at alpha 0.8 under every scheme but sttrans, and now draw them at 1.0; `mcolor(navy%50)`, `malpha()` and sttrans' %20 still set an opacity. (WP-30, P1.2b)
- Fills are the colour blended at the layer's intensity, opaque, as twoway draws them: `dash bar mpg rep78` filled its bars `#1a476f` and now fills them `#486c8c` under s2color (`#cccc00`, was `#ffff00` at alpha 0.8, under s1rcolor); `area`, `rbar` and `rarea` likewise (`#486c8c`, was `#1a476f`); a colour you give takes the intensity too: `fcolor(yellow)` and `color(yellow)` fill `#ffff33` (were `#ffff00`), `rbar, color(red)` fills `#ff3333` and keeps its `#ff0000` outline. Histograms stay at full intensity until their own scheme style is read. (WP-30, P1.2b)
- `fintensity()` is drawn as twoway draws it, an opaque colour, never an opacity: `fintensity(50)` on navy is `#8da3b7` (was navy at alpha 0.5), `fintensity(150)` `#112f4a` and `fintensity(1000)` `#03070b` (were clamped to navy), `fintensity(0)` and `fintensity(-5)` white (were invisible), under s1rcolor `fintensity(50)` `#0d2438`; `inten200` and `max` are read; an unknown name such as `inten75` draws full intensity with the note (was alpha 0.75). On confidence bands `lfitci, fintensity(150)` is `#808080` (was `#c0c0c0`) and, under s1rcolor, `fintensity(50)` `#282828` (was `#a8a8a8`). (WP-30, P1.2b)
- A user scheme's `intensity p#bar` and `intensity p#area` are read, above 100 too (`intensity p1bar inten200` fills navy bars `#0d2438`), and its `intensity bar` and `intensity area`, which twoway ignores, are no longer read: `intensity area inten40` drew areas at alpha 0.4 and now changes nothing. (WP-30, P1.2b)
- A brushed-away bar or area is dimmed in the colour it is drawn in (it was dimmed in the colour before intensity and `fcolor()`). (WP-30, P1.2b)
```

### Traps for the executor

- **Never read the colour back from the glyph.** `_apply_fill_opts` takes `base`; a glyph created at the blended colour would be blended twice if its `fill_color` were the base (the research's warning).
- **`color()` writes two things on bars.** The outline keeps the resolved colour (D-16c); only the fill is blended. `blcolor()` and `lcolor()` are not touched.
- **`map_area`'s border.** Its default colour was `r.glyph.fill_color` (10110); after S16 that is blended, so it must be `_fill_base`.
- **rarea's 0.5 and rbar's `line_alpha=0`** stay; S24 owns both.
- **`fill_alpha` stays an intensity name.** `SchemeParser.fill_alpha` is `intensity p` and still feeds `p_other_band_styles` (7128); do not rename or delete it (`test_scheme.py::TestIntensitiesAndFonts` and the fidelity harness read it).
- **Case.** Intensity names are exact (`Full`, `INTEN50` are unknown); scheme files are lower case and `_intensity` keeps lower-casing them.
- **`.` is not `.a`.** `fintensity(.)` is the layer's intensity, silently; `.a` is an unknown name with the note (E3).
- **The clamp** applies under both `naturally_white` values and only when a channel that was non-zero rounds to 0; `f = 0` under `naturally_white 0` gives navy `#010304`, not black.
- **Navy at exactly 52** (`fintensity(5200)`) is P1.13's UNCLEAR; no test uses it.
- **Notes.** `_dash_style_note` is not edited; count its note through S06's needle helpers. The value is echoed by `_dash_display` (80 printable characters).
- **Served code** is the same source: no copy-list entry, no generated line. If the served test fails with a NameError, a module-level helper was added by mistake; keep every new name a method.
- **Line numbers** move after batches 3-5 (S08 touches `_apply_marker_opts`, S13 `_ci_band_style`'s widths, S14 `map_bar`/`map_rbar`'s widths and deletes `_tag_spacing`, S15 `_init_properties` and `_FALLBACK_PROPS`); find each site by symbol.
- **python_exec hazard.** Several concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; a cscript then exits 222. A skip is not a pass: restore and re-run.
- **The red list is re-measured** (16-08); a node outside E6 is investigated before it is flipped (R9).

### Shared files and merge rules

- **R1:** S16's truth block between its own start and end lines, helpers directly above its header; WP-29's EW-02 edited in place only; no area-script case added; test_option_validation.cscript's header comment only.
- **R2:** no copy-list entry (row S16); `test/function_test_map.py` keys under S16's anchor, and the two repointed keys in place (A148).
- **R3:** dash.sthlp Marker and Transparency Options (S16's), plus the three in-place corrections of E7 (3369-3372 in Stata scheme support, 2583-2584 in Statistical Layer Options, 660-664 in Differences from twoway); no batch-6 partner edits those paragraphs (S17: Mapping a Variable to Colour; S18: Axis and Display and the log example at 2865).
- **R4:** the one `P1.2b` marker, replaced in place by five lines.
- **R5:** BUGS.md `P1.2b` in place; only the `"P1.2b"` line of `WP30_OPEN` deleted.
- **R7:** `intensity_truth.json` new, stamped, `git add -f`; no scheme file or `scheme_truth.json` touched.
- **R8:** six CORPUS cases appended; `ALLOWED`/`_MUST_WARN` untouched.
- **R9:** F1-F46 and any `$S/16-flips.txt` line flipped with `Flipped:` lines.
- **R10:** `_SINGLE_Y_BASELINE_SHA256` re-derived here and by the merger after S16 lands.
- **R12:** S16 is batch 6's only editor of `_apply_fill_opts`; it edits no other applier and neither the template nor the figure body.

### For later sections

- **S24** extends `_scheme_alpha(color_idx, plot_type)` (two arguments now; declared opacity or 1.0) to its ~30 construction sites; sets rarea's alpha by area's rule (replacing `fill_alpha=0.5`, F8, F27 and F34's alpha half); passes the histogram's `intensity histogram` as `_histogram_quads`' `_f` and `color histogram` as its `_fill_base` (flipping `TestTheHistogramUntilS24` with the reason); regenerates the scheme files (where `intensity bar`/`intensity area` may then be dropped from the extractor's output, since nothing reads them).
- **S30** builds `OptionTranslator.stata_colour`'s `colour*#` on `GlyphMapper._blend_intensity(hex, f, naturally_white)`; the object's intensity then blends the rounded result again in `_apply_fill_opts` (twoway composes them: `fcolor(*.7)` `#7f98ae`, research p1-13 §3).
- **S43** passes a bare `*#`/`%#`'s site colour as `_apply_fill_opts`' `base` before intensity.
- **S32** owns the pstyle(p#) band: D-16e's measurement (band `#486C8C` under `intensity p1bar inten200`) says `p_other_band_styles` does not follow `intensity p#bar` above full; S32 measures and decides.
- **Every later fill applier** (S24, S30, S43) writes its colour inside `_apply_fill_opts` or at creation, so S08's sync carries it to the nonselection and muted copies (A37); `TestBrushedFillsKeepTheBlend` and S08's brushed-copy tests stay green.

### Notes for the closeout (A145; S58 writes them)

- **GAPS2 D11** (D11-a markers, D11-b intensity): `- **Tracked:** Closed in WP-30, BUGS.md "<P1.2b title>", commit <sha>`, and `(WP-30, GAPS2-D11)` appended to the Resolution.
- **DROPIN-REMAINING.md P1.2:** part b closed by S16's commit (part a by S15's).
- **ROADMAP.md:2051** is wrong and is replaced by: "- s1rcolor's bar intensity (`intensity p#bar` through the p chain, inten80) is drawn as twoway draws it, an opaque blend towards black (`#cccc00`), since WP-30 P1.2b; the former alpha 0.8 read graph bar's `intensity bar`, which twoway's bar ignores, and compounded where bars overlap. `p_mark_colors` equals `p_colors` in all 14 shipped schemes, so TR-16.5 exists for user schemes only."
- **TWOWAY_COVERAGE_AUDIT.md** lines 112 (marker styling), 115 (fill/bar styling) and 116 (confidence bands): tag "intensity drawn as an opaque blend and markers opaque since WP-30 P1.2b".
- **ROADMAP P2.14:** gains `fintensity(1e400)` (dash.ado r(198) "must be a name or a number"; twoway draws it white, rc 0, measured 03oct2026).
- **New P2 candidate for S58 to file** unless S32 closes it: pstyle(p#) confidence bands under a scheme whose `intensity p#bar` is above full (D-16e).

### Line numbers

Every anchor is `c96facd`'s. Batches 3-5 land first and edit several of these functions (Traps); the symbols named here are authoritative.
