# Section 08: Stata size units for markers, text and gaps (P1.12 part a, M1)

> Part of: WP-30 · Items: P1.12 part a (entry `P1.12a`; register P1.12.6, the brushed copies, fixed under it, ratification row 27) · Risk: yellow · Batch: 3 · Depends on: 01 · Blocks: 13, 14, 15, 18, 21, 30, 31, 32, 33, 37, 47, 48, 56 · Tasks: 19, 1 commit · Case prefix: SU

## Review amendments

- Fixed (major): Q1 is now a marked "Maintainer question" with a recommendation. The review found two faults in option (a) as drafted. First, it stamps only the figure, while the GlyphMapper sites (`msize()`, `mlabsize()`, `mlabgap()`) read `self.scheme.size_ref_in` on the one mapper each renderer shares (`self.mapper = GlyphMapper(scheme=self.scheme, …)`, dash_render.py:29175; served `_DASH_MAPPER`, :33479), so markers would not follow `xsize()`. Second, it would make S08 a second `_generate_app_source` editor in batch 3 beside S09 (A139). The recommendation is (b), with register P1.12.4's "closes P2.13's 4-inch reference" narrowed to the scheme's `graphsize` half.
- Fixed (minor): the truth block names S01's `_w30_expect`/`_w30_done` outright instead of hedging. Its pages and logs go under `` `w30_work' `` and are erased before the end line. `_su_case` opens `version 19`.
- Checked: anchors at HEAD (`_SIZE_MAP` 5309, `translate_msize` 5542, `_textbox_size` 4819, `_apply_marker_opts` 8622, `_apply_mlabel_opts` 9302, `_mlabel_gap_px` 9503, `_MARKER_PX_ANCHOR` 5966, the served `_SIZE_MAP` line 34117, `_dash_style_note`'s `using` argument at 15371, the eleven `_apply_mlabel_opts`/`_immediate_labels` call sites, and the ten `@15px@` needles of F29 at test_wp29_truth.cscript:1109-1243) all match.
- Checked: the manifest's N1 (nonselection and muted glyphs) is out of scope under register P1.12.6 and A146, and is filed as P2.49 with a guard, as written. M5: no new refusal (dash.ado unchanged; SU-01..08). M6: negative and zero sizes stay silent.
- Checked: batch 3 shares no function. S07 edits data and lists; S09 edits `_build_sources_and_figures`, `_generate_app_source` and new functions. S08 alone edits the four size appliers' sites. The `CORPUS`/`function_test_map.py` appends conflict only in context.
- Cross-file (notes file): index R3 lists S08 only under Marker Label Options. Its scope also edits dash.sthlp 690-691 (Differences), 3155-3162 (Mapping a Variable to Colour) and 3424-3434 (Units, under Stata scheme support, which S07 also edits in batch 3, in other paragraphs).
- (cross-file pass) 08-18 verify: added the key-deletion check `grep -c '^    "P1.12a": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.
- (ratification 06oct2026) Row 27 (A37, P1.12.6) answered "Fix in WP-30": the brushed-glyph bug joins S08. The binding reading P1.12.6, the Overview, Risk factor 7, Evidence E10, US-08.7, BR-08.9, TR-08.16 and TR-08.17, the new test file `test/test_brushed_copies.py` (written failing by 08-01), the new task 08-09, AC-08.11, the closing text and the help's Linking and Brushing sentence carry it. The old guard `TestBrushedCopiesKeepCreationValues` is dropped before it was ever written (it recorded the bug). Tasks 08-09 to 08-18 of the earlier draft are now 08-10 to 08-19 (the "08-18 verify" line above is today's 08-19).
- (ratification 06oct2026) BUGS.md handling: closed in S08's commit, under S08's own entry `P1.12a`. No extra entry is appended and P2.49 is not filed (index A146 and IR-15, section-01's S58.1 note and Appendix B as they stand: Appendix B's P1.12a entry is unchanged, and P1.12a's Resolution names the brushed-copy fix and its tests). The commit body carries one `Regression:` line per brushed test. One more Results line goes to the CHANGELOG under P1.12a's marker.
- (ratification 06oct2026) Batch-3 boundary re-checked. S08 newly edits `_dash_add_glyph` and `_dash_add_pc_glyph` (LOW, 3 impacted each; their served callers are generated template lines, which the index does not resolve) and `_dash_dim_nonselection` (CRITICAL, 8 impacted / 1 direct / 8 processes, measured 06oct2026 at `c96facd`). It adds the staticmethod `GlyphMapper._sync_brushed_copies`. S07 edits none of these. S09 edits `_build_sources_and_figures`, which calls `_dash_dim_nonselection` (:31658, :31684), but S09 does not edit the function, and S08 does not edit the call lines. No function is shared. The copy lists are unchanged: the three module functions are already listed (:33131-33132, :33329) and change in place, and the method travels with `GlyphMapper`.
- (ratification 06oct2026) A move-time bar width is out of reach until S14. A bar's or rbar's brushed copies keep the build's width after a filter move: `_dash_copy_redraw_geometry` (served) and `_build_filter_widgets`' width script (saved) write the live glyph only. S14 (batch 5) deletes both (A61). S08 does not edit them (R12), and S14 adds a bar-after-a-move case to `test/test_brushed_copies.py` (For later sections).

**Binding readings applied in this file** (index "Index reconciliations", register P1.12):
- **IR-1 / P1.12.1 (M1 strict).** Option B: one Stata unit for every class at the 4-inch reference, 1 rs = 2.88 pt = 3.84 px. The manifest's "the D1 per-class anchors" reads "D1's one unit". The default marker goes from 8 px to 5.87 px here; the default line's 1.5 → 1.15 px is S13's.
- **P1.12.2.** An unknown size name draws the class's medium, with twoway's note.
- **P1.12.4 [C].** `#pt`, `#in`, `#cm` convert to Stata units at the reference length of the graph, then draw on the one unit. The scheme half (its `graphsize`) is built here. The `xsize()`/`ysize()` half is **Maintainer question Q1** (Notes; recommendation (b)); until it is answered the plan builds the scheme half only.
- **P1.12.5 [C].** The gap is measured from the marker's edge, `gsize label_gap` (half_tiny, 2 pt) by default. The diagonal clocks and the no-marker origins were measured for this file (Evidence E5); the 4 px pins are flipped with the reason.
- **P1.12.6 [C], A37, A146, IR-15, ratification row 27 (06oct2026, CHANGED: "Fix in WP-30").** The nonselection/muted glyph sync (research N1, critic C4) is fixed here, as the manifest's scope lists it ("explicit msize/mcolor/mlwidth reach the nonselection and muted glyphs (N1)"), in both modes and for every applier a layer runs: marker, line, fill, colorvar and mlabel. It is fixed under S08's own entry `P1.12a`. P2.49 is not filed and no extra BUGS.md entry is opened (index A146). Its failing-first tests are `test/test_brushed_copies.py` (08-01), and the fix is 08-09 (TR-08.16, TR-08.17).
- **A150 / X.2.** S06 (batch 2) has landed: every note added here goes through `_dash_style_note`, whose warnings S06's channel prints in twoway's `(note: …)` form; tests count note text through S06's needle helpers.
- **R12.** S08 edits none of `_generate_app_source`, `_make_figure_body`, `_build_sources_and_figures` or `_build_filter_widgets` (S09 is batch 3's template and `_build_sources_and_figures` editor). It is batch 3's only editor of `_apply_marker_opts` and `_apply_mlabel_opts`.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:102 (P1.12): "Numbers are read as pixels and keywords use a private pixel ladder: `msize(medium)` gives 11px against a default of 8. `#pt`, `*#` and `vhuge` are refused, `mlabgap` is read as px, and `vvvthin` is missing." GAPS2 D2 (GAPS2.md:849-866) measured it: `msize(1.52778)` draws 1 px, `title(,size(large))` gives 15px, "smaller than the 14pt default", and units, `*#` and `vhuge` are refused. GAPS2 B9 (GAPS2.md:457) is the same gap for explicit text `size()`. Re-measured at `c96facd` in both modes (Evidence E3): `msize(medium)` 11 px where the default marker is 8; `title("T", size(large))` 15 px where the scheme's heading is 14 pt (18.67 px); `size(5)` 5 px where twoway draws 14.4 pt; `msize(4pt)`, `msize(*2)`, `msize(vhuge)`, `size(12pt)`, `labsize(10pt)` all noted and dropped; `mlabgap(5)` is 5 px added to a fixed 4 px offset.

dash keeps three private scales (research p1-12 section 4): text in CSS points (3.84 px per Stata unit), markers anchored at 8 px for 4.4 pt (5.24 px per unit), lines at 5 px per unit. twoway has one: every size is a relative unit of min(width, height)/100 of the graph, and a keyword is a fixed number of those units from its class's style file.

**After this section**, in both modes and unchanged by any filter move:
- one unit for every class, 1 rs = 2.88 pt = 3.84 px (IR-1);
- `msize()`, `mlabsize()`, `mlabgap()`, textbox `size()` (title, subtitle, note, caption, axis titles, the second axis's title, the colour key's title), `labsize()` (both axes, second axes, the colour bar's `zlabel()`) and `legend(size())` read numbers and keywords in Stata units, `#pt`/`#in`/`#cm`/`#rs`, `*#` (times the size the scheme or dash would otherwise draw there) and every keyword of Stata's `symbolsize` and `gsize` ladders, `vhuge` and `ehuge` included, case-sensitively;
- the default s2color marker is 5.87 px (stcolor 4.0, economist 9.33); an explicit keyword equal to the scheme's draws exactly the scheme's default;
- a marker label sits (marker radius + gap) from its point along its clock direction, the gap 2 pt by default, the radius half the layer's marker size even where no marker is drawn (bar, pcarrow, pcbarrow), as twoway places it;
- an unknown name (including a wrong-case one) draws the class's medium with the note; a negative or zero size draws nothing, silently, as twoway does;
- a brushed-away (nonselection) or muted copy of every layer's glyph draws that glyph's own size, marker, colours, widths and dash. Only its opacity is dimmed: dash's nonselection alpha (0.15 linked, Bokeh's 0.1 otherwise) and Bokeh's muted 0.2, never above the glyph's own, so a hollow marker stays hollow (ratification row 27, Evidence E10).

**Why one section.** These are the marker, text and gap kinds of one resolver; the line kind (S13) and every later consumer (S14, S15, S18, S21, S30, S31, S32, S33, S37, S47, S48, S56) need its grammar first. Lines are split off because `_apply_line_opts` is the batch's heaviest CRITICAL symbol (about 40 impacted) and S13 lands in batch 5 on this resolver. The brushed copies are in by ratification row 27. Their fix is one pass after each layer's appliers have run, so it needs no edit of `_apply_line_opts` and reaches S13's widths when they land.

**Test order and commit rule (rule 7, D1, A156).** One entry, one commit, `(WP-30 P1.12a)`.
- **08-01** writes the regression tests whose expectations are the twoway values quoted in Evidence, plus the brushed-copy tests of `test/test_brushed_copies.py` (Evidence E10). It runs them against the unmodified tree and saves `<scratch>/08-P1.12a-failure.txt`. It never commits.
- **08-02** extracts the fixture; **08-03** adds the fixture-driven tests and the guard tests, runs them on the unmodified renderer and appends their failure lines to the same file (guard tests pass and are listed apart).
- **08-04 to 08-18** fix (08-09 syncs the brushed copies), flip, add the truth block and the area cases, certify and update the help.
- **08-19** closes the entry, its Resolution recording the brushed-copy fix (no other entry is opened). It replaces both markers and makes the commit after one full run through the queue.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every dashboard's markers and labels move, five CRITICAL symbols are edited, and about 30 tests pin the private ladder

**Why.** M1 accepts the visible change (RK-4, PLAN K2): every default marker shrinks from 8 to 5.87 px and every default marker label moves (s2color 3 o'clock: 4 px → 5.6 px from the centre). The edited symbols feed every plot type in both modes.

**Risk factors.**
1. CRITICAL symbols (index batch 3.0): `OptionTranslator.translate_msize` (13 impacted / 3 direct / 8 processes), `_textbox_size` (9 / 5 / 7), `GlyphMapper._mlabel_gap_px` (16 / 1 / 9), `GlyphMapper._apply_marker_opts` (12 / 7 / 8), `GlyphMapper._apply_mlabel_opts` (16 / 10 / 10). HIGH: `_dash_apply_axis_spec` (4 / 2 / 3), `_dash_apply_z_options` (5). The 11 `_apply_mlabel_opts` call sites are `map_*` methods reached through name dispatch (`UNKNOWN` callers; confirmed by grep in Evidence E8).
2. Pinned tests: the prototype (below) shows the tests that pin today's ladder, offsets and pixel strings; each is flipped with its reason (R9), never deleted.
3. The single-y page digest (`test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline`) moves, and S09 moves it in the same batch (R10).
4. The two renderers must agree: the saved renderer and the served app share the three classes by source and the module helpers by the copy list (`_textbox_size` at dash_render.py:33360). A helper that only one mode calls would show only in parity.
5. Text sizes change unit (`"15px"` → `"14pt"`): a later section that compares font strings must compare points (`OptionTranslator.css_to_pt`).
6. The reference length for absolute units (P1.12.4) is reachable in the module text functions only through the figure (TR-08.7), a Python-only attribute that a figure not styled by `SchemeParser.apply_to_figure` lacks (it then reads 4 in).
7. The brushed-copy sync (TR-08.16, TR-08.17) touches every layer of every dashboard in both modes. `_dash_dim_nonselection` is CRITICAL (8 / 1 / 8), and the served callers of `_dash_add_glyph`/`_dash_add_pc_glyph` are generated lines the index does not see. Five test files read a nonselection or muted glyph today (Evidence E10).

**Mitigation.**
1. Impact runs at the batch base (index 3.0) and the section checks it before editing (08-01); the empty-option identity guard (`TestEmptyOptionsChangeNothing`) runs over every scatter-type mapper in both modes.
2. 08-10 re-measures the red list on the fixed tree against Evidence E9; 08-10 to 08-16 flip exactly that list, each with a `Flipped:` line.
3. The merger re-derives the digest after each of S08's and S09's landings (R10); S08's commit message says why it moved.
4. Every behaviour test runs in both modes (`_figure(mode, …)`) and, for the served app, after a `_fire` filter move; `test_mode_parity.py` gains S08's CORPUS cases (G3); no new module-level name is added (R2 row S08), so the copy lists are untouched.
5. `css_pt` writes two fixed decimals (never an exponent, which Bokeh's FontSize validator rejects); `css_to_pt` reads both units.
6. `size_ref_of(fig)` falls back to 4.0, the reference dash already documents (dash.sthlp:3427), and a test asserts the stamp exists on every figure of both modes, by() panels included.
7. One staticmethod does the whole sync, called at the end of the two dispatchers both modes already share. A guard (`test_the_dimming_alphas_are_kept`) pins today's 0.15 / 0.1 / 0.2. 08-10's red-list measurement adds the five files of Evidence E10. `_dash_dim_nonselection`'s CRITICAL warning is logged before 08-09 edits it.

**Prototype** (scratch copy of `c96facd` exported with `git archive HEAD`, a minimal version of TR-08.1 to TR-08.11; 63 test files that mention a size, an offset or a scheme; run as a file list, not the full suite). The measured red list is in "Tests that pin today's behaviour" (Evidence E9).

## Dependencies

- **Depends on: 01.** S01 provides the open entry `P1.12a` in BUGS.md, its key in `WP30_OPEN`, the markers `<!-- WP-30 P1.12a -->` in `### Results that change` (the `**WP-30 (drop-in P1, 03oct2026)**` group) and `### Changed behaviour (may need your do-files changed)`, the stub block `* ==== S08 P1.12a: … ====` in `test/test_wp30_truth.cscript`, and the anchor `# WP-30 S08 (P1.12a): Stata size units for markers, text and gaps` in `test/function_test_map.py` `FUNCTIONS`. S06 (batch 2) provides the note channel (A150); S02 (batch 1) provides the extractor form (`DASH_REPO`, A130).
- **Blocks:** S13 (line kind), S14 (rcap cap length from `msize()`; rcapsym's end-marker size), S15 (tick and title chrome sizes), S18, S21 and S47 (margins in Stata units), S30 (reuses `stata_number`/`size_multiplier`), S31 (`tlength()`/`titlegap()`), S32 (named styles carry sizes), S33 and S37 (marker-label defaults and `mlabtextstyle()`), S48 (`iscale()`), S56 (`text()` size).
- **Parallel batch: 3**, merge order S07, S08, S09.
- **Can run with:** S07 edits the scheme extractor, the 26 scheme files, `scheme_truth.json`, `SchemeParser._BUILTIN_NAMES` and `_dash_shipped_schemes`; S09 edits `_dash_inert_tex`'s new pass, `_build_sources_and_figures` and `_generate_app_source`. S08 touches none of them. S08 iterates `SchemeParser._BUILTIN_NAMES` in its scheme tests, so after S07 lands they cover 26 schemes with no edit. S08 cannot sit with S10 (both edit `_dash_apply_legend` and `_dash_apply_z_options`), which is why S10 is batch 4.

## Evidence

All anchors are at `c96facd` (dash_render.py 37,689 lines; dash.ado 8,487; dash.sthlp 3,822; CHANGELOG.md 824). Symbols are authoritative if lines drift; S07 lands before S08 in batch 3 and does not edit dash_render.py's size code.

### E1 — the private ladders (dash_render.py)

`OptionTranslator._SIZE_MAP`, 5309-5319 (no vtiny, vhuge, ehuge):

```python
5309    _SIZE_MAP: dict[str, int] = {
5310        "tiny":     3,
5311        "vsmall":   5,
5312        "small":    7,
5314        "medium":   11,
5316        "large":    15,
5318        "huge":     24,
5319    }
```

`translate_msize`, 5542-5570, lower-cases, maps the keyword, and reads a number as whole pixels:

```python
5554        v = value.strip().lower()
5555        if v in OptionTranslator._SIZE_MAP:
5556            return OptionTranslator._SIZE_MAP[v]
5561        try:
5562            f = float(v)
5565        if math.isfinite(f):
5566            return max(1, int(f))
5567        raise ValueError(
```

`_SIZE_MAP` has one more reader: the served header emits it as a global no app code reads (research N3), `ServerAppBuilder._generate_app_source`, 34115-34117:

```python
34115            "# Stata msize() keyword -> pixels, the same map OptionTranslator",
34116            "# uses, so one keyword means one size in both modes.",
34117            "_SIZE_MAP = %r" % (dict(OptionTranslator._SIZE_MAP),),
```

S08 keeps `_SIZE_MAP` defined (no size path reads it after S08) because removing it would break this line and `_generate_app_source` is S09's in batch 3 (R12). Notes for the closeout carry N3.

The scheme side is already in Stata units, at a separate anchor. `SchemeParser._GSIZE_PT` 5898-5915 (text, at the 4-inch reference: `medium` 11pt, `large` 14pt, `vhuge` 28pt, and a dash-only `ehuge` 32pt that Stata's gsize class does not have), `_GSIZE_NUMERIC_PT_PER_UNIT = 2.88` (5921), `_SYMBOLSIZE_PT` 5943-5957 (medium 4.4, large 7.0, vhuge 16.0, ehuge 32.0), and the marker anchor, 5959-5967:

```python
5959    # Marker diameter in Bokeh screen pixels.  The RATIOS are Stata's, from
5960    # _SYMBOLSIZE_PT above; the anchor is dash's own -- medium (4.4pt),
5961    # which is what s2color asks for, keeps the 8px dash has always drawn,
5962    # so the default dashboard is unchanged and a scheme that asks for
5966    _MARKER_PX_ANCHOR: float = 8.0
5967    _MARKER_PX_ANCHOR_PT: float = 4.4
```

`SchemeParser._markersize_px`, 7248-7276, scales every scheme symbolsize from that anchor (`px = self._MARKER_PX_ANCHOR * pt / self._MARKER_PX_ANCHOR_PT`, 7274); it is called from `_init_properties` (6806) at 7051 (`marker_size`) and 7059 (`p_marker_sizes`), after the scheme's `graphsize x`/`graphsize y` are read at 7015-7016. The scheme sizes therefore draw 5.24 px per Stata unit for markers and 3.84 px per unit for text (CSS points).

### E2 — every size site (dash_render.py)

| Site | Function (def) | Lines | Today |
|---|---|---|---|
| `msize()` | `GlyphMapper._apply_marker_opts` (8622) | 8699-8704 | `glyph.size = self.tr.translate_msize(…)`; ValueError → `_dash_style_note("msize", v, "size")` |
| `msize()` pre-read | `GlyphMapper.map_scatteri` (13627) | 13701-13706 | silent `translate_msize`, default kept on ValueError |
| `mlabsize()` | `GlyphMapper._apply_mlabel_opts` (9302) | 9455-9460 | `f"{size_px}px"` from `translate_msize` |
| label default | same | 9424-9432 | `text_font_size="10px", x_offset=4, y_offset=4` (the 10px default is S33's) |
| `mlabgap()` | same + `_mlabel_gap_px` (9503) | 9462-9491, 9503-9528 | keyword via `_SIZE_MAP`, number as px; offset = fixed base `_MLABEL_CLOCK` (7907-7921) + gap × unit |
| textbox `size()` | `_textbox_size` (4819) | 4819-4836 | `float(translate_msize(raw))` px; unknown → UserWarning "ignoring it", default kept |
| title | `_dash_figure_title` (25905) | 25921-25923 | `f"{_t_px:g}px"` |
| axis titles | `_dash_style_axis_titles` (25929) | 25947-25953 | same |
| subtitle/note/caption | `_dash_text_annotations` (25969) | 26011-26016 | same, else the scheme's size |
| second axis title | `_dash_add_secondary_axes` (23034) | 23100-23102 | same |
| colour-key title | `_dash_apply_z_options` (26106) | 26129-26137 | same |
| colour-key labels | same | 26145-26157 | `zlabel(, labsize())` is named, not drawn |
| `legend(size())` | `_dash_apply_legend` (21400) | 21619-21629 | `f"{translate_msize(…):g}px"` on every legend |
| `labsize()` | `_dash_apply_axis_spec` (22714) | 22836-22844 | same; UserWarning "ignoring it" |

`_textbox_size`, 4819-4836:

```python
4819 def _textbox_size(opts: dict, default: "float | None") -> "float | None":
4826    raw = opts.get("size", "")
4827    if not raw:
4828        return default
4829    try:
4830        return float(OptionTranslator.translate_msize(raw))
4831    except (ValueError, TypeError):
4832        warnings.warn(
4833            f"dash: size({raw}) is not a recognised text size; ignoring it.",
```

The gap and the fixed base, 9473-9490:

```python
9473        (bx, by), (ux, uy), (align, baseline) = GlyphMapper._MLABEL_CLOCK[p]
9474        gap = 0.0
9475        if "mlabgap" in options:
9476            try:
9477                gap = self._mlabel_gap_px(options["mlabgap"])
9486        if gap:
9487            kwargs["x_offset"] = bx + gap * ux
9488            kwargs["y_offset"] = by + gap * uy
9489        else:
9490            kwargs["x_offset"], kwargs["y_offset"] = bx, by
```

`_MLABEL_CLOCK` (7907-7921) holds per clock the base pair (4 px at 3, 6, 9, 12; (±3, ±3) or (±3, ±2) at the diagonals), the unit vector and Bokeh's anchor; its anchors and unit vectors are right (measured 23sep2026) and are kept. `_apply_mlabel_opts(self, fig, source, options, xvar, yvar, label_col=None)` (9302-9310) never sees the glyph.

The reference length: `SchemeParser._init_properties` reads `graphsize x`/`graphsize y` (7015-7016; every Stata scheme sets both, or twoway fails r(198), per the comment at 7008-7014). Both renderers style each figure first with the scheme, before every S08 site and before the plot loop: saved `self.scheme.apply_to_figure(fig)` (30326, then `_dash_figure_title` 30329, `_dash_add_secondary_axes` 30385, `_dash_text_annotations` 30400, `_dash_apply_axis_options` 30405, the plot loop 30425); served `_DASH_SCHEME.apply_to_figure(fig)` (generated at 35203, then `_dash_add_secondary_axes` 35206, `_dash_figure_title` 35211, `_dash_apply_axis_options` 35268, the layer loop). `apply_to_figure(self, fig)` (7376) takes no graph options, so `xsize()`/`ysize()` cannot reach it without editing its two call lines (Q1). Bokeh documents that `HasProps.__setattr__` "short circuit[s] all property machinery for `_private` attributes" (bokeh/core/has_props.py, measured on 3.9.0: `fig._dash_ref = 4.5` sets, `fig.dash_ref = 1` raises AttributeError), so a `_dash_size_ref_in` attribute is Python-only and never serialised.

### E3 — measured at `c96facd`, both modes (research p1-12 Measurement A; saved `DashRenderer._build_figures`, served `ServerAppBuilder.build` + `make_document`; served identical line for line)

```
msize(None) -> size=8.0          msize(medium) -> 11      msize(large) -> 15
msize(1.52778) -> 1              msize(4pt)/(*2)/(vhuge)/(abc) -> 8.0 + "is not a recognised size; using the scheme's default."
title size(None) -> 14pt  size(medium) -> 11px  size(large) -> 15px  size(5) -> 5px
title size(12pt)/(*2)/(vhuge) -> 14pt + "is not a recognised text size; ignoring it."
ylabel labsize(None) -> 10pt  (5) -> 5px  (medium) -> 11px  (10pt)/(*2) -> 10pt + note
mlabsize(None) -> 10px  (medium) -> 11px  (5) -> 5px  (10pt)/(*2) -> 10px + note
mlabgap(None)/(0) -> x_offset=4  (5) -> 9.0  (medium) -> 15.0  (10pt) -> 4 + note
legend size(None) -> 10pt  (5) -> 5px  (large) -> 15px  (12pt) -> 10pt + note
```

Through Stata (research dash1.do/dash2.do): `dash scatter mpg weight, msize(medium)` writes a saved page whose Scatter has size 11 (the default page: 8.0); `msize(-1)` draws 1 px, rc 0 (twoway: a zero-size marker); `msize(4pt) … title("TTT", size(12pt))` notes both and returns rc 0. A filter move changes no size in either mode: the saved scripts write no `size`, `font_size`, `x_offset` or `y_offset` (a scan of every module-level JavaScript string of `dash_render` for `\.size\s*=`, `font_size\s*=`, `x_offset\s*=` and `y_offset\s*=` found none, 03oct2026; the only generated size literal is the stale cue's own `text_font_size="9pt"`, 32318), and the served move only reassigns source data. `_dash_copy_redraw_geometry` copies widths only.

### E4 — twoway truth (StataNow 19.5, console; s2color 5.5 × 4 in, viewBox 3960 × 2880, 10 SVG units = 1 pt, 1 rs = 28.8 units)

From the research note (section 3, `.Graph.plotregion1.plot1.style.marker.size.setting` and SVG):

```
msize: default/medium 1.52778  large 2.4306  small 1.04166  vtiny .1  tiny .34722
       vhuge 5.555  ehuge 11.111  4pt -> 4 (drawn 1.392rs = 4.0pt)  .1in -> 2.5rs  .2cm -> 1.968rs
       1.52778rs -> 1.52778  *2 -> 3.05556  *.5 -> .76389  0 -> 0  100 -> 100
       stcolor: default 1.04166 (small); *2 -> 2.08332 (twice the SCHEME default); abc -> 1.52778
title size (pt): default 14 (large)  medium 11  large 14  12pt 12  5 14.4  *2 28  vhuge 28  huge 20
       minuscule 1  half_tiny 2  5rs 14.4  .25in 18  tenth 28.8  relative3 8.64  10-pt 10  *0 0
       abc/ehuge/vvvthin/vtiny -> "(note: named style abc not found in class gsize, default attributes used)", 11pt
labsize: default 10pt  5 -> 14.4pt  medium 11pt  10pt 10pt  *2 20pt  vhuge 28pt  abc 11pt
mlabsize: default 8pt  medium 11  large 14  5 -> 14.4  10pt 10  *2 16  vhuge 28
legend(size()): default 10pt  5 -> 14.4pt  large 14pt  12pt 12pt  *2 20pt
mlabgap (label x - marker centre, 3 o'clock): default 41.95 units (radius 22.03 + 19.92 = half_tiny .6944rs, 2pt)
       0 -> 22.03 (the radius)  5 -> radius + 5rs  10pt -> radius + 10pt  medium -> radius + 11pt
       *2 -> radius + 2 x default gap  -2 -> radius - 2rs
       msize(small) mlabgap(0) -> 14.98 = small/2; msize(large) mlabgap(0) -> 35.02 = large/2
```

Reference length (research critic C1, title font size in SVG points): s2color `size(large)` 14.00 and `size(14pt)` 14.00; stcolor (7.5 × 4.5 in) 15.74 and 14.01; economist (2.2 × 2.2 in) 7.70 and 14.00. A relative size scales with min(width, height); an absolute one does not. Shipped schemes whose smaller side is not 4 in: economist 2.2, s1manual/s2manual/s2gmanual/stgcolor 2.392, sj/stsj 2.6, stcolor/stmono1/stmono2/sttrans 4.5.

### E5 — measured for this file (03oct2026, StataNow 19.5 through `scripts/stata_slot.sh`; scratch `…/wp30/s08/p1.do`-`p5.do`)

Notes, signs and case (`capture noisily twoway scatter mpg weight in 1, msize(X)`, then the class setting):

```
MSIZE_RC|-1|0|-1|            (no note)            MSIZE_RC|*-1|0|-1.52778|   (no note)
MSIZE_RC|-1pt|0|-1|          (no note)
(note:  named style HUGE not found in class symbolsize, default attributes   MSIZE_RC|HUGE|0|1.52778|
(note:  named style Large not found in class symbolsize, default attributes  MSIZE_RC|Large|0|1.52778|
MSIZE_RC|1e400|0|.|          (no note)            MSIZE_RC|1d3|0|1000|
TSIZE_RC|-1|0 (no note)      (note:  named style LARGE not found in class gsize, default attributes used)
MLABSIZE_RC|-1|0 / *-1|0 (no note)    MLABSIZE Large / MLABGAP abc / MLABGAP Large: the gsize note
(note:  named style 4PT not found in class gsize ...)  title size(4PT) and size(4Pt) drawn 11pt (110.01 units)
```

So twoway is silent on a negative or zero size (M6), notes a wrong-case name and a wrong-case unit and draws medium (P1.12.2), and reads `1d3` as 1000 (Stata's `d` exponent). Measured medium fallbacks: `mlabgap(abc)` and `mlabgap(medium)` both put the label 132.04 units from the centre (radius 22.03 + 110.01, 11 pt); `mlabsize(abc)` 110.01 (11 pt); `legend(size(abc))` 110.01 on both keys.

A blank before a unit: on the graph options `title(, size(4 pt))`, `subtitle(, size(4 pt))`, `ytitle(, size(4 pt))`, `ylabel(, labsize(4 pt))`, `legend(size(4 pt))` and `zlabel(, labsize(4 pt))` all draw 39.97 units (4 pt) and `size(4 in)` 2879.91 (288 pt); on the plot options `msize(4 pt)` draws the 4-unit marker of `msize(4)` (inner radius 57.54), `mlabsize(4 pt)` 115.21 (4 rs) and `mlabgap(4 pt)` radius + 115.2 (4 rs). The plot options are twoway stylelists, so `4 pt` is two elements and the one y takes `4` (S11's splitter, P1.1a, batch 4).

Label position at each clock (s2color, `mlabel(make)`, `mlabposition(p)`, label anchor minus the circle centre in units; circle r 26.35 outer, 22.03 nominal):

```
clock 12 default dy=-41.95  gap 0 dy=-22.03        clock  2 default (36.38,-21.04)  gap 0 (19.06,-11.01)
clock  3 default dx= 41.95  gap 0 dx= 22.03        clock  4 default (36.38, 76.94)  gap 0 (19.06, 66.91)
clock  9 default dx=-41.95  gap 0 dx=-22.03        clock  6 default dy= 97.85       gap 0 dy= 77.93
```

At clock 2, (19.06, 11.01) is 22.01 × (cos 30°, sin 30°): the anchor point is (radius + gap) along the unit vector the table already holds; the y differences at 4 and 6 add the text's ascent (55.9 = 0.7 × the 79.94 font), which Bokeh's `text_baseline="top"` already supplies.

No-marker origins and `msize()` (`mlabgap(0)` unless stated):

```
bar mpg weight in 1, mlabel(make)                 top 1294.96; label baseline 1272.93 (gap 0, 22.03 above) / 1253.01 (default, +19.92)
pcarrow / pcbarrow mpg weight y2 x2, mlabel(make) tail x 704.76; label x 726.78 (gap 0, +22.02) / 746.71 (default)
pcarrow ..., msize(large) mlabgap(0)              label x 739.78 (+35.02 = large/2); pcbarrow the same
bar ..., msize(large) mlabgap(0)                  label baseline 1259.94 (35.02 above the top)
scatteri 20 3000 "lab"                            dx 41.95 default, 22.03 at gap 0
pcspike ..., mlabel(make); pci with "lab"         no label drawn
msize(-1) mlabgap(0)                              dx -14.35 (= -0.5 rs: the signed radius)
stcolor default (viewBox 5400 x 3240, 32.4 units/rs)  gap 0 dx 16.88 (small/2 = .52083 rs); default dx 39.32 (+22.44 = .6926 rs)
```

So the gap's origin is half the layer's marker size (signed, and `msize()` when given) on every type, drawn marker or not. `gsize label_gap` is `half_tiny` in scheme-s2color.scheme, scheme-s1manual.scheme and scheme-economist.scheme, and every one of Stata's 26 schemes includes s2color; none of dash's 20 shipped `dash-*.scheme` files carries the key (`grep -l label_gap dash-*.scheme` prints nothing), and `SchemeParser` does not read it.

Colour key and absolute units under stcolor:

```
twoway scatter mpg weight, colorvar(price) zlabel(, labsize(large))  key labels 0, 5,000, 10,000, 15,000 at 139.96 (14pt); default key labels 99.99 (10pt); ZLAB_RC|0
twoway scatter ..., colorvar(price) ztitle("ZZ", size(large))       ZZ at 139.96
set scheme stcolor; title("TTT", size(14pt))                          TTT at 140.06 (14pt; the default large title is 157.44)
set scheme stcolor; msize(4pt)                                        setting 4
```

### E6 — Stata's ladders (`/Applications/StataNow/ado/base/style/*.style`, `set val` and `set sztype`)

`symbolsize` (relative): zero 0, vtiny .1, tiny .34722222, vsmall .520833, small 1.04166, medsmall 1.25, medium 1.52778, medlarge 1.94444, large 2.4306, vlarge 3.125, huge 4.8611, vhuge 5.555, ehuge 11.111; (points): 2-pt, 3-pt, 4-pt, 6-pt, 11-pt, 12-pt, 14-pt, 16-pt, 20-pt, 24-pt.

`gsize` (relative): zero 0, minuscule .3472, quarter_tiny .34722, third_tiny .46296, half_tiny .6944, tiny 1.3888, vsmall 2.0833, small 2.777, medsmall 3.4722, medium 3.8194, medlarge 4.1667, large 4.8611, vlarge 5.5556, huge 6.9444, vhuge 9.7222, default 4.166, tenth 10, quarter 25, third 33.333333333333, half 50, full 100, relative0p3 .3, relative0p6 .6, relative1p2 1.2, relative1p5 1.5, relative2p2 2.2, relative3 3, relative3p5 3.5, relative4 4, relative5 5, relative8 8, relative12 12; (points): 1-pt, 2-pt, 3-pt, 4-pt, 6-pt, 8-pt, 10-pt, 11-pt, 12-pt, 14-pt, 16-pt, 20-pt, 24-pt, 32-pt, 180-pt. There is no gsize `ehuge` or `vtiny` (twoway notes both on text, E4).

### E7 — dash.ado, the help and the CHANGELOG

`_dash_option_rules` (2025), 2028-2030:

```stata
2028    local plot ///
2029        msize=style  mlabsize=style  mlabgap=style ///
2030        lwidth=style,0,10000  mlwidth=style,0,10000 ///
```

`_dash_validate_value` (2125), style kind 2261-2274: a name passes untouched; only a number is held to bounds, and `msize`/`mlabsize`/`mlabgap` have none; a numeric-looking overflow (`1e400`) is refused r(198). `4pt`, `*2`, `.1in`, `vhuge`, `HUGE` and `1d3` (real() 1000) all pass today (measured 03oct2026, scratch `p6.do`: `dash scatter mpg weight, <opt> name(su0k)` printed `SUCHK|msize(4pt)|0`, `SUCHK|msize(*2)|0`, `SUCHK|msize(vhuge)|0`, `SUCHK|msize(.1in)|0`, `SUCHK|msize(1d3)|0`, `SUCHK|msize(HUGE)|0`, `SUCHK|mlabsize(*1.5)|0`, `SUCHK|mlabgap(2pt)|0`); S08 changes no dash.ado line and pins that with SU-01..SU-08 (test_option_validation.cscript). Stata/Mata are not in the GitNexus index (`UNKNOWN`): `_dash_validate_value` is called at dash.ado:2692, 2713, 5349, 5371, 7069, 7451 and `_dash_option_rules` at 2580 (grep, research section 5 step 4). That dash.ado refuses `msize(1e400)` where twoway draws (E5: setting `.`, rc 0) is P2.14's, not S08's.

Help: dash.sthlp:690-691 ("A name or a number: {cmd:msize()}, {cmd:mlabsize()}, {cmd:mlabgap()} …"), 2150-2151 (`mlabsize(` "size keyword or number"), 2158-2165 (`mlabgap(` "in pixels, added to {cmd:dash}'s own offset of about 4 pixels … a size keyword … is the pixels {cmd:mlabsize()} reads it as"), 3155-3162 (the colour key: "ticks, {cmd:#}{it:N}, {cmd:none} and {cmd:minmax} … on the colour bar"; labsize unmentioned) and the Units paragraph 3424-3434:

```
3425 {ul:Units.}  Sizes are converted on Stata's own scale.  A {cmd:gsize} or
3426 {cmd:symbolsize} number is a relative size, 100 being the smaller dimension
3427 of the graph, and is drawn as it would be on Stata's four-inch reference
3428 graph: {cmd:medium} text is 3.8194, which is 11 point, so one unit is 2.88
3429 point, and {cmd:economist}'s {cmd:gsize heading 6.0} is 17.28 point.
3430 Marker sizes follow Stata's {cmd:symbolsize} ladder, which is not the text
3431 ladder: a {cmd:large} marker is 7 point against {cmd:medium}'s 4.4.  A
```

CHANGELOG.md:521-523 (research N2), WP-15's line, is wrong at HEAD: dash notes `msize(abc)` and draws (rc 0), as twoway does.

```
521 - Option values are validated as twoway validates them. A bad value such as
522   `msize(abc)` or `yaxis(3)` is r(198) or r(111), naming the option. A style
523   name dash cannot draw is noted and the default is used (WP-15).
```

### E8 — blast radius (`gitnexus impact <symbol> -d upstream -r dash`, 03oct2026 at `c96facd`)

| Symbol | Risk | Impacted / direct / processes | Note |
|---|---|---|---|
| `OptionTranslator.translate_msize` | CRITICAL | 13 / 3 / 8 | warn (index 3.0) |
| `_textbox_size` | CRITICAL | 9 / 5 / 7 | one CLI call returned `UNKNOWN` (several candidates); the exact run gave CRITICAL. Treat as CRITICAL |
| `GlyphMapper._mlabel_gap_px` | CRITICAL | 16 / 1 / 9 | warn |
| `GlyphMapper._apply_marker_opts` | CRITICAL | 12 / 7 / 8 | warn; R12: S08 is batch 3's only editor |
| `GlyphMapper._apply_mlabel_opts` | CRITICAL | 16 / 10 / 10 | warn; 11 call sites, `map_*` through dispatch (`UNKNOWN`) |
| `_dash_apply_axis_spec` | HIGH | 4 / 2 / 3 | warn |
| `_dash_apply_z_options` | HIGH | 5 | one CLI call `UNKNOWN`; research recorded HIGH |
| `SchemeParser._markersize_px`, `SchemeParser._init_properties`, `SchemeParser.apply_to_figure`, `_dash_apply_legend`, `_dash_apply_axis_options`, `_dash_figure_title`, `_dash_style_axis_titles`, `_dash_text_annotations`, `_dash_add_secondary_axes`, `GlyphMapper.map_scatteri` | LOW | 1-3 each | — |
| `GlyphMapper.map_scatter`, `map_bar`, `map_dropline`, `map_rcapsym`, `map_pcscatter`, `map_pcarrow`, `map_pcbarrow`, `map_pccapsym`, `map_rscatter`, `map_pcarrowi`, `_immediate_labels` | `UNKNOWN` | — | called through `_dash_glyph_dispatch`/name dispatch; their one changed line each is the `_apply_mlabel_opts`/`_immediate_labels` call (grep: 9861, 10289, 13509, 13623-13624, 13725, 13953, 14103, 14175, 14282, 14418, 14462, 14632) |
| `_dash_validate_value`, `_dash_option_rules` (dash.ado) | `UNKNOWN` (not indexed) | — | not edited |

### E9 — tests that pin today's behaviour (flip, never delete)

Each is flipped in the fix commit with a `Flipped:` line (R9). The list is the prototype's red list on the 63 size-related files (Risk, "Prototype"); 08-10 re-measures it on the fixed worktree, and any extra node is investigated and added with its failure text, never edited merely to pass.

**Prototype measurement** (Risk): `127 failed, 13051 passed, 4 errors in 725.67s` at `-n 4`. Of these, two `test_function_test_map.py` failures (`test_every_function_has_an_entry`, `test_what_nothing_runs_is_kept_on_purpose`) were the prototype's unmapped and unreached names (TR-08.5, TR-08.9 and TR-08.14 keep both reached and mapped), and two (`test_option_validation.py::TestTheDefaultIsWhatTheSchemeGives::test_a_bad_msize_draws_the_schemes_size`, `::TestABadValueNoLongerAbortsTheRender::test_scatteri_msize`) were a 1e-5 px difference between the prototype's two marker tables that TR-08.6 removes (`_markersize_px` reads the resolver): both must pass unflipped, and are investigated, never flipped, if they do not. The 4 errors are `test/test_textbox_no_text.py`'s collection (its module constant). The rest, plus four nodes the prototype did not exercise (marked †: `_mlabel_gap_px` and the medium note text change in the final design), are the flips:

| # | Node | Today | After (reason) |
|---|---|---|---|
| F1 | `test/test_options.py::TestTranslateMsize::test_numeric_string_passthrough` | `translate_msize("12") == 12` | 46.08 (12 Stata units × 3.84 px) |
| F2 | `test/test_scheme_rendered_output.py` module constant `MARKER_PX_ANCHOR = 8.0` (86), read by `::TestTheGlyphSizes::test_the_marker_size_follows_the_symbolsize_ladder` (20 schemes × 2 modes) | 8.0 | `1.52778 * 2.88 * 4.0 / 3.0` (5.86668: Stata's medium on the one unit, IR-1; `_marker_px` keeps `MARKER_PX_ANCHOR * pt / 4.4`, within its 0.02 px tolerance) |
| F3 | `test/test_scheme_rendered_output.py::TestNamedMarkerSizes::test_the_size` | stcolor 5.45, economist 12.73, s2color 8.0 | 4.0, 9.33, 5.87 |
| F4 | `test/test_scheme_rendered_output.py::TestTheUnitFunctions::test_markersize_px_anchors_medium_at_8px` | medium 8.0, small 5.45, large 12.73, `3.0` 15.71 | renamed `test_markersize_px_anchors_medium_at_4_4pt`: `1.52778 * 2.88 * 4 / 3`, `1.04166 * …`, `2.4306 * …`, `3.0 * 2.88 * 4 / 3` (5.86668, 3.99997, 9.33350, 11.52) |
| F5 | `test/test_scheme_consumption.py::TestPerSeriesStyleCycle::test_an_explicit_option_beats_the_scheme` (the `{"msize": "12"}` row; and its stcolor default 5.45) | 12.0; 5.45 | 46.08; 4.0 |
| F6 | `test/test_help_claims_5.py::TestTheClockPositionPlacesTheLabelAsTwowayDoes::test_the_default_is_three_oclock` | `(4, 0)` | `(5.6, 0)`: radius 2.933 + gap 2.667 px |
| F7 | `…::TestTheClockPositionPlacesTheLabelAsTwowayDoes::test_mlabgap_widens_the_gap_along_the_clock_direction` (7 clocks) | base + gap × unit | (r + gap) × unit, gap in Stata units |
| F8 | `…::TestTheClockPositionPlacesTheLabelAsTwowayDoes::test_mlabgap_is_the_pixels_given` (`0`, `-2`, `2.5`, `small`, `tiny`) | 4, 2, 6.5, 11, 7 px | r + g × 3.84 (`small` 2.777, `tiny` 1.3888 units): 2.93, -4.75, 12.53, 13.60, 8.27; renamed `test_mlabgap_is_in_statas_units` |
| F9 | `…::TestTheClockPositionPlacesTheLabelAsTwowayDoes::test_a_position_twoway_does_not_recognise_is_drawn_at_twelve` (6 rows) and `::test_every_label_of_a_two_ended_type_is_placed_alike` | `(0, 4)`, `(-4, 0)` | `(0, 5.6)`, `(-5.6, 0)` |
| F10 | `test/test_help_claims_5.py::TestTheOtherLabelOptions::test_mlabsize_takes_a_keyword_or_a_number` | `'7px'` | `'8pt'` (`small` text is 2.777 units, 7.998 pt) |
| F11 | `test/test_help_claims_5.py::TestAdversarialLabelPlacement::test_a_gap_in_another_spelling_is_not_a_gap` (7 rows) | noted, `(4, 0)` | noted, drawn at medium: `(2.933 + 14.667, 0)` (P1.12.2) |
| F12 † | `test/test_help_claims_5.py::TestTheClockHelpers::test_the_gap_reader` | `small` 7.0, `HUGE` 24.0, `10` 10.0 | in px at 3.84 per unit: `small` 10.66, `10` 38.4; `HUGE` moves to the refused list (case, E5) |
| F13 † | `test/test_help_claims_5.py::TestTheClockHelpers::test_the_gap_reader_refuses_what_is_not_a_gap` | `*2` refused | `*2` read (2 × 2 pt); `HUGE` and `5px` refused |
| F14 | `test/test_immediate_values.py::TestScatteriDrawsItsRecords` (10 tests: `test_a_missing_coordinate_draws_no_point_and_no_label`, `test_a_label_without_a_clock_or_mlabposition_is_at_three`, `test_an_empty_label_or_a_lone_clock_draws_no_label`, `test_the_label_style_options_apply`, `test_an_immediate_label_replaces_mlabel`, `test_a_record_without_a_clock_field_still_labels`, `test_the_label_is_text_not_markup`, `test_a_label_sits_at_its_point_at_its_clock_position`, `test_a_clock_that_is_not_a_whole_number_is_drawn_at_twelve`, `test_a_label_without_a_clock_takes_mlabposition`), `::TestPcarrowiDrawsAnOddClockWhereTwowayDoes::test_it_is_drawn_at_twelve`, `::TestBothModesDrawTheSame::test_a_scatteri_label_reaches_the_served_page_as_text`, `::TestBothModesDrawTheSame::test_pcarrowi_with_an_odd_clock_position` | 4 px base offsets; `f"{translate_msize('large')}px"` | 5.6 px; `'14pt'` |
| F15 | `test/test_pccapsym_pcarrowi.py::TestMapPcarrowi` (`test_a_label_is_drawn_at_the_tail_at_its_clock_position`, `test_a_label_without_a_clock_or_mlabposition_is_at_three`, `test_a_label_without_a_clock_takes_mlabposition`, `test_the_label_style_options_apply`, `test_a_clock_that_is_not_a_whole_number_is_drawn_at_twelve_once`) | 4 px base; px label size | 5.6 px from the tail (E5: pcarrow's origin is half the marker size); `'14pt'` |
| F16 | `test/test_marker_label_parity.py::test_the_label_options_reach_every_label` (rcapsym, rconnected, rscatter, pcscatter, pcarrow, pcbarrow) | `(-4, 0)` | `(-5.6, 0)` |
| F17 | `test/test_glyphs.py::TestMlabelOption::test_mlabsize_applied` | `"…px"` | `"…pt"` |
| F18 | `test/test_textbox_no_text.py` module constant `LARGE` (42) | `f"{_textbox_size(…):g}px"` | `_textbox_size({'size': 'large'}, None)` (`'14pt'`; `_textbox_size` returns CSS) |
| F19 | `test/test_colorvar_forms.py::TestZOptions::test_ztitle_suboptions_keep_the_key_title` | the same `:g}px` form | the CSS string |
| F20 | `test/test_axis2_suboptions.py::TestTheTitleRouteKeepsTheDefault::test_unlabelled_title_restyled_through_the_route` (4 rows) | `"%gpx" % translate_msize("large")` (15px) | `'14pt'` |
| F21 | `test/test_axis_options.py::TestTitleTextFidelity::test_title_size_and_colour_are_applied`, `::test_abbreviated_size_and_colour_are_applied` | px | pt |
| F22 | `test/test_colorvar_legend.py::TestTheSchemeChromeIsStillApplied::test_an_explicit_legend_size_still_wins` | `legend(size(4))` → `'4px'` | `'11.52pt'` |
| F23 | `test/test_textbox_grammar.py::TestAbbreviationsAreSubOptions::test_every_size_spelling` | `size(large)` must differ from the plain title | uses `huge` (20 pt): `large` now IS the s2color heading (14 pt), BR-08.4 |
| F24 | `test/test_help_claims_2.py::TestAnUnknownStyleInsideAStructuredOption::test_one_note_and_the_schemes_default_in_both_modes`, the six `size(bogus)` rows (title, xtitle, ytitle × s2color, s1rcolor) | the plain figure's size | for the size rows (`sub.startswith("size")`) the drawn size is `'11pt'` in both modes (twoway's medium, P1.12.2); the colour rows are unchanged (S30 owns unknown colours) and `::test_a_known_style_is_still_honoured` (`vlarge`, 16 pt) passes as it is |
| F25 | `test/test_option_validation.py::TestAnUnknownStyleNameIsNamedOnceInBothModes::test_one_note_naming_the_option`, row `("scatter", {"msize": "*2"}, "msize")` (609) | `*2` noted | the row becomes `{"msize": "Large"}` (still unknown: wrong case, E5) |
| F26 | `test/test_option_validation.py::TestTheDefaultIsWhatTheSchemeGives::test_a_bad_clock_position_labels_at_twelve_oclock` | `(0, 4)` | `(0, 5.6)` |
| F27 † | `test/test_option_validation.py::TestTheRemainingSilentSites::test_legend_size` | `"…; using the scheme's default."` | `"…; using medium."` |
| F28 | `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` (`_SINGLE_Y_BASELINE_SHA256`, 393-403) | `fd0db4f6…a1361` | re-derived on the worktree (the default marker is 5.87 px), then by the merger after S08 and after S09 (R10) |
| F29 † | `test/test_wp29_truth.cscript` ET-01, ET-04, ET-05, ET-06, ET-07, ET-08, ET-10 (1109-1243) | `@15px@` | `@14pt@` (each case edited in place, R1) |

Pins that pass unchanged and must stay so (re-run in 08-10's measurement): `test/test_options.py::TestTranslateMsize::test_all_size_keywords_are_positive` and `::test_size_keywords_are_increasing`; `test/test_glyphs.py::TestMapScatter::test_scatter_msize_applied`, `::TestMapRcapsymOptions::test_rcapsym_msize_applied_to_scatter_markers`, `::TestMlabelOption::test_mlabgap_increases_offset`; `test/test_pccapsym_pcarrowi.py::TestMapPccapsym::test_marker_options_style_the_markers_and_not_the_spike`; `test/test_scheme_rendered_output.py::TestTheUnitFunctions::test_the_symbolsize_ladder_is_statas`; `test/test_help_claims_8.py::TestTheUnitsAreStatas` (all); `test/test_help_claims_5.py::TestTheClockHelpers::test_the_table_covers_the_thirteen_positions` and `::TestAdversarialLabelPlacement::test_a_megabyte_value_is_judged_at_once`; `test/test_option_validation.py::TestTheNoteHelper::test_the_translators_still_raise`, `::TestABadStyleValueNeverAborts::test_a_non_finite_size_or_width`, `::TestUserTextIsEchoedThroughDashDisplay::test_the_style_note`; `test/test_mode_parity.py` (all).

### E10 — the brushed copies (ratification row 27; research N1, critic C4; measured 06oct2026 at `c96facd`)

**Mechanism.** Bokeh makes a renderer's copies once, when the renderer is made. `bokeh/plotting/_renderer.py` `create_renderer` (Bokeh 3.9.0) builds `nonselection_glyph` from the creation keywords with `override_defaults={'alpha': 0.1}` and `muted_glyph` with `{'alpha': 0.2}`: "we always set one". dash's appliers then write `renderer.glyph` only. Examples: `_apply_marker_opts` 8622 (`glyph = renderer.glyph`), `_apply_line_opts` 8540, `_apply_fill_opts` 8807, `_apply_colorvar` 8887 and `map_bar`'s `bfcolor`/`blcolor` 10271-10285. No dash line reads or writes `nonselection_glyph` except `_dash_dim_nonselection` (29025-29047), which sets its two alphas to `_NONSELECTION_ALPHA` (0.15, :3566) on linked figures (saved :31658 and :31684 in `_build_sources_and_figures`, served the generated line :35527). No dash line reads or writes `muted_glyph` except the saved stale cue, which rebuilds it from the glyph (`r.muted_glyph = _dash_stale_glyph(r.glyph)`, :32328, after every figure is built). Every figure carries box and lasso select (`_DASH_FIGURE_TOOLS`, :24418), so any figure can show its nonselection copies, linked or not.

**Both modes go through two dispatchers.** Each layer is drawn through `_dash_add_glyph` (28955) or `_dash_add_pc_glyph` (29006). The saved callers are `DashRenderer._add_glyph` (30749) and `_add_pc_glyph` (30780). The served callers are the generated lines at 34967, 34990 and 35002. Every applier of the layer runs inside that call, and both functions are on the served functions tuple (:33131-33132). `yline()`/`xline()` draw a `Span` (measured: no extra `GlyphRenderer`), which has no copies.

**Measured** (scratch `…/wp30/s08n1/probe.py`, `test_scheme_linewidth._figure` in both modes; glyph / nonselection / muted; served identical to saved line for line):

```
scatter msize(large) mcolor(red)          size 15/8.0/8.0  fill_color #ff0000/#1a476f/#1a476f  line_color the same  fill_alpha 0.8/0.1/0.2
scatter msymbol(Oh)                       fill_alpha 0.0/0.1/0.2   (a brushed-away hollow marker is drawn filled)
scatter malpha(5)                         fill_alpha 0.05/0.1/0.2  (a brushed-away point is drawn twice as opaque)
scatter msymbol(T) mlwidth(thick)         line_width 2.5/1.5/1.5
line lwidth(thick) lcolor(red)            line_color #ff0000/#1a476f/#1a476f  line_width 2.5/1.5/1.5
bar fcolor(red)                           fill_color #ff0000/#1a476f/#1a476f
connected mcolor(red) lcolor(blue) msize(large)   Line: line_color #0000ff/#1a476f; Scatter: as the first row
```

**Prototype** (saved mode, `_dash_add_glyph` wrapped by a scratch sync of TR-08.16's rule, `…/s08n1/proto.py`): every row above then draws the glyph's size, colours and widths in both copies. Alphas become min(copy, glyph): 0.1/0.2 for an opaque glyph, 0.0 for `Oh`, 0.05 for `malpha(5)`. `colorvar(y)`'s `fill_color` field (with its `LinearColorMapper`) is shared by all three.

**Blast radius** (`node .gitnexus/run.cjs impact <symbol> --direction upstream --repo .`, 06oct2026): `_dash_dim_nonselection` CRITICAL (8 impacted / 1 direct / 8 processes); `_dash_add_glyph` LOW (3 / 1 / 1); `_dash_add_pc_glyph` LOW (3 / 1 / 1). The served callers are template strings, so the LOW results undercount them; they are confirmed by grep at 34967-35002.

**Tests that read a copy today** (re-measured by 08-10; none is expected to flip, and any that does is investigated first): `test/test_linking.py:152`, `test/test_layout_tabs.py:306-384` (all linked nonselection `fill_alpha == _NONSELECTION_ALPHA`; their glyphs are opaque, so min(0.15, glyph) is still 0.15), `test/test_help_claims_4.py:1809-1817` (`saved == served == {0.15}`), `test/test_help_claims_5.py:894-895`, `test/test_served_bs_layout.py::TestALinkedFigureDimsAlike` (`test_the_helper`'s `SimpleNamespace` renderers have no `glyph`, so TR-08.17 keeps today's assignment for them; `test_the_served_document`'s unlinked `0.1`), `test/test_mode_parity.py:354` (the `dim` profile) and `test/test_saved_stale_cue.py` (the rebuilt muted glyph, built after the sync).

## User stories

- **US-08.1** As a twoway user, I want `msize(medium)`, `msize(1.52778)`, `msize(4pt)`, `msize(*1.5)` and `msize(vhuge)` drawn at Stata's sizes, so a do-file's markers look the same relative to its text as in Stata.
- **US-08.2** As a twoway user, I want `title("T", size(large))`, `size(5)`, `size(12pt)`, `size(*2)`, `ylabel(, labsize(small))`, `mlabsize(medium)`, `legend(size(large))` and `zlabel(, labsize(large))` drawn at Stata's text sizes, so an explicit `large` is the scheme's own `large` and not something smaller.
- **US-08.3** As a twoway user, I want `mlabgap()` measured from the marker's edge in Stata's units, with twoway's default gap, so labels sit where twoway puts them at every clock position and on bars and arrows.
- **US-08.4** As a twoway user, I want a misspelt or wrong-case size name (`msize(Large)`, `size(abc)`) drawn at medium with twoway's note, and a negative size drawn as nothing in silence, as twoway does.
- **US-08.5** As a dashboard publisher, I want the saved page and the served app to draw the same sizes, before and after any filter move, so a reader sees one picture.
- **US-08.6** As a twoway user with a stcolor or economist do-file, I want `size(14pt)` and `msize(4pt)` drawn in the same proportion to the scheme's own sizes as twoway draws them.
- **US-08.7** As a dashboard reader who box- or lasso-selects points, I want the points I did not select to keep their size, symbol, colour and outline and only fade. Today they snap back to the scheme's default marker, so a large red series turns into small navy dots and a hollow series turns solid.

## Business requirements

Each holds in both modes and after any filter move (BR-30.38), under every shipped scheme.

- **BR-08.1** A number in a marker, text or gap size is in Stata's relative units, one unit for every class: 1 unit = 2.88 pt = 3.84 px (IR-1). `msize(1.52778)` draws the default s2color marker; `title(, size(5))` is 14.4 pt.
- **BR-08.2** Every keyword of Stata's `symbolsize` ladder (markers) and `gsize` ladder (text and gaps) draws its Stata value, including `vtiny`, `vhuge`, `ehuge` (markers), `tenth`, `quarter`, `third`, `half`, `full`, `default`, the `relative*` names and the `#-pt` names; names are case-sensitive.
- **BR-08.3** `#pt`, `#in`, `#cm` (and the graph-option forms with a blank before the unit) are absolute sizes converted at the graph's reference length (the scheme's smaller `graphsize` side; `xsize()`/`ysize()` per Q1); `#rs` is relative; `*#` multiplies the size that would otherwise be drawn at that site.
- **BR-08.4** The default marker is 5.87 px under s2color (4.0 under stcolor, 9.33 under economist), and an explicit keyword equal to the scheme's default draws exactly that default, for markers, titles, axis titles, tick labels, legend keys and marker labels.
- **BR-08.5** A marker label's anchor is (r + g) from its point along its clock direction, r half the layer's marker size (`msize()` when given, signed; the scheme's p# size otherwise, on bar, pcarrow and pcbarrow too), g the gap (`mlabgap()`, else 2 pt); clock 0 centres the label and ignores the gap.
- **BR-08.6** An unknown size name, a wrong-case name or unit, or a magnitude above 1,000 units draws the class's medium (marker 1.52778, text and gap 3.8194 units) with one note naming the option and value; a negative or zero marker or text size draws nothing and a negative gap moves the label toward the point, both in silence.
- **BR-08.7** `zlabel(, labsize())` is drawn on a colour bar; on a discrete key it stays named.
- **BR-08.8** dash.ado accepts every form above as it does today (no new refusal) and no value reaches the page as text: every size is written as a number or as a fixed-decimal `Npt` string.
- **BR-08.9** (ratification row 27) The brushed-away (nonselection) and muted copies of every layer's glyph draw the glyph's own properties after all of the layer's appliers have run: size, marker, angle, fill and line colours, line width and dash, hatch, and colour-mapped fields. The exception is opacity: each copy's fill, line and hatch alpha is the smaller of the glyph's and the copy's own dimming alpha (dash's 0.15 on a linked figure, Bokeh's 0.1 otherwise, Bokeh's 0.2 when muted). This holds in both modes, on by() panels and paired-coordinate layers, and after any filter move. The saved stale cue's rebuilt muted glyph is unchanged.

## Technical requirements

All in `dash_render.py` unless named. Line numbers are `c96facd`'s.

- **TR-08.1 Stata's ladders on `OptionTranslator`** (class 5098; insert after `_SIZE_MAP`, 5319, before the `_LWIDTH_MAP` banner at 5321). Class attributes, each with a comment citing its style file: `PT_PER_RS: float = 2.88` (4 in × 72 pt / 100); `PX_PER_PT: float = 4.0 / 3.0` (CSS); `_SYMBOLSIZE_RS` and `_GSIZE_RS` (the relative values of E6, exactly as the style files write them); `_SYMBOLSIZE_ABS_PT` and `_GSIZE_ABS_PT` (the `#-pt` names, in points); `_SIZE_UNIT_PT = {"pt": 1.0, "in": 72.0, "cm": 72.0 / 2.54}`; `_SIZE_KINDS = ("marker", "text", "gap")` (S13 appends `"line"`); `_SIZE_MAX_RS = 1000.0`; `_SIZE_TEXT_MAX = 64`; and the compiled number grammar `_STATA_NUMBER_RE = re.compile(r"[-+]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eEdD][-+]?[0-9]+)?")` (ASCII digits only; `d`/`D` is Stata's exponent, E5 `1d3`). `_SIZE_MAP` stays defined and unread by any size path (the served header still emits it; N3).
- **TR-08.2 One number and multiplier parser** (S30 reuses both): `@staticmethod stata_number(text) -> float | None` (fullmatch of `_STATA_NUMBER_RE` on the stripped text, at most `_SIZE_TEXT_MAX` characters, `d`→`e`, finite, else None) and `@staticmethod size_multiplier(text) -> float | None` (`*` then optional blanks then a `stata_number`; None when the text is not a multiplier). Neither raises, logs or evaluates text.
- **TR-08.3 `@staticmethod resolve_size(value, kind, default_pt, ref_in=4.0) -> float`**: signed points at dash's 4-inch reference. `kind` not in `_SIZE_KINDS` → ValueError. The value is stripped; empty or longer than 64 characters → ValueError. In order: (1) `size_multiplier` → `m × default_pt`; (2) `stata_number` → `n × PT_PER_RS`; (3) a number, optional blanks, then exactly `pt`, `in`, `cm` or `rs` (lower case) → `rs`: `n × PT_PER_RS`, else `n × _SIZE_UNIT_PT[u] × 4.0 / ref_in`; (4) a name in the kind's relative ladder (`_SYMBOLSIZE_RS` for `"marker"`, `_GSIZE_RS` for `"text"`/`"gap"`) → `rs × PT_PER_RS`; (5) a name in the kind's points ladder → `pt × 4.0 / ref_in`; otherwise ValueError. `ref_in` is used only when finite and > 0, else 4.0. A non-finite result, or a magnitude above `_SIZE_MAX_RS × PT_PER_RS` (2,880 pt), raises ValueError. No floor: callers floor (TR-08.6, TR-08.9) because the label radius needs the sign (E5).
- **TR-08.4 Helpers on `OptionTranslator`**: `size_medium_pt(kind)` (marker 1.52778 × 2.88; text and gap 3.8194 × 2.88); `css_pt(pt) -> str` (`max(0, pt)` written `f"{pt:.2f}"` with trailing zeros and point stripped, plus `"pt"`: `"14pt"`, `"14.4pt"`, `"8pt"` for `small`'s 7.99776, never an exponent); `css_to_pt(css) -> float | None` (`"<number>pt"` or `"<number>px"` × 0.75, else None); `size_ref_of(fig) -> float` (`getattr(fig, "_dash_size_ref_in", 4.0)`, used only when a finite float in (0, 100], else 4.0).
- **TR-08.5 `translate_msize(value, default_px=None, ref_in=4.0) -> float`** (5542) stays, as the marker kind's px wrapper: the signed `resolve_size(value, "marker", (default_px if given else the medium px) × 0.75, ref_in) × PX_PER_PT`, raising ValueError as before. Its production callers are `_apply_marker_opts` and `map_scatteri` (TR-08.8) and `_mlabel_radius_px` (TR-08.9), so `test_function_test_map.py::test_what_nothing_runs_is_kept_on_purpose` still finds it reached.
- **TR-08.6 The scheme on one unit** (`SchemeParser`, class 5646). `_MARKER_PX_ANCHOR = 1.52778 * 2.88 * 4.0 / 3.0` (5.86668, Stata's medium on the one unit; `_MARKER_PX_ANCHOR_PT` and `_SYMBOLSIZE_PT` stay, as the help-claim tests read them), and `_markersize_px` (7248) reads keywords and numbers through `resolve_size(kw, "marker", size_medium_pt("marker"), self.size_ref_in) × PX_PER_PT`, floored at 0, lower-casing as today, an empty or unknown value giving the anchor silently, so an explicit `msize(medium)` and the s2color default are the same float (the prototype's two-table version differed by 1e-5 px, E9); its docstring's "8px", "5.45px", "12.73px" become 5.87, 4.0 and 9.33. In `_init_properties` directly after 7016: `self.size_ref_in = min(graphsize_x, graphsize_y)` when both are positive finite numbers, else 4.0; `self.label_gap_pt = OptionTranslator.css_to_pt(self._gsize("gsize label_gap", "2pt")) or 2.0` (every shipped scheme: 2.0, E5). In `apply_to_figure` (7376), first statement: `fig._dash_size_ref_in = self.size_ref_in` (Python-only, E2). The served app rebuilds the scheme from `_props` plus `_init_properties()` (33446-33458), so both modes get both attributes with no copy-list edit.
- **TR-08.7 The reference at each site.** GlyphMapper sites use `getattr(self.scheme, "size_ref_in", 4.0)`. Module sites use `OptionTranslator.size_ref_of(fig)`: `_dash_figure_title`, `_dash_style_axis_titles`, `_dash_text_annotations`, `_dash_apply_legend`, `_dash_apply_z_options`, and `_dash_add_secondary_axes` (or its `scheme.size_ref_in` when `scheme` is given). `_dash_apply_axis_spec` gains a keyword `ref_in=4.0`, passed by its two callers: `_dash_apply_axis_options` (23025, `size_ref_of(fig)`) and `_dash_add_secondary_axes` (23300). Under Q1's "yes" the two stamping call lines also pass `graph_opts` (Notes).
- **TR-08.8 Markers.** `_apply_marker_opts` (8699-8704): `px = self.tr.translate_msize(v, float(glyph.size), ref)` and `glyph.size = max(0.0, px)`; on ValueError, `_dash_style_note("msize", v, "size", "medium")` and `glyph.size = size_medium_pt("marker") * PX_PER_PT`. A glyph whose `size` is not a plain number keeps today's path (a field spec is not multiplied). `map_scatteri`'s silent pre-read (13701-13706) resolves against `self.scheme.default_marker_size(color_idx)` the same way and stays silent (the note comes from `_apply_marker_opts`).
- **TR-08.9 Marker labels.** `_apply_mlabel_opts(…, label_col=None, radius_px=None)`; when None, `radius_px = self.scheme.default_marker_size(0) / 2`. New `GlyphMapper._mlabel_radius_px(self, options, base_px) -> float`: half of `self.tr.translate_msize(options["msize"], base_px, ref)` when `msize` is given (medium on ValueError, silently: `_apply_marker_opts` notes it), else `base_px / 2`; signed. All 11 call sites pass `radius_px=self._mlabel_radius_px(options, self.scheme.default_marker_size(color_idx))`: map_scatter 9861, map_bar 10289, map_dropline 13509, map_rcapsym 13623 and 13624, map_pcscatter 13953, map_pcarrow 14103, map_pcbarrow 14175, map_pccapsym 14282, map_rscatter 14632, and `_immediate_labels` 14418, which gains the keyword `radius_px=None` and gets it from map_scatteri (13725) and map_pcarrowi (14462). `mlabsize` (9455-9460): `css_pt(resolve_size(v, "text", css_to_pt(kwargs["text_font_size"]) or size_medium_pt("text"), ref))`, ValueError → note and `css_pt(size_medium_pt("text"))`. `mlabgap` (9474-9490): `gap_px = GlyphMapper._mlabel_gap_px(v, self.scheme.label_gap_pt, ref)`, default `label_gap_pt × PX_PER_PT`, ValueError → note and medium; then clock 0 → offsets (0, 0); else `x_offset = (radius_px + gap_px) × ux`, `y_offset = (radius_px + gap_px) × uy` (the `_MLABEL_CLOCK` base pair is no longer read; the table and its anchors stay). `_mlabel_gap_px(raw, default_pt=2.0, ref_in=4.0) -> float` (staticmethod, signed px) = `resolve_size(raw, "gap", default_pt, ref_in) × PX_PER_PT`; its 32-character, ASCII-digit and finiteness guards are now `resolve_size`'s (64 characters).
- **TR-08.10 Text.** `_textbox_size(opts, default=None, ref_in=4.0, option="size") -> str | None`: None when `size` is not given; else `css_pt(resolve_size(raw, "text", css_to_pt(default) or size_medium_pt("text"), ref_in))`; ValueError → `_dash_style_note(option, raw, "size", "medium")` and `css_pt(size_medium_pt("text"))`. Its five callers pass the size already on the model as `default` and write the returned string unchanged: `_dash_figure_title` (`fig.title.text_font_size`, option `"title(size)"`), `_dash_style_axis_titles` (the first primary axis's `axis_label_text_font_size`, `"xtitle(size)"`/`"ytitle(size)"`), `_dash_text_annotations` (`size_default`, `"subtitle(size)"`/`"note(size)"`/`"caption(size)"`), `_dash_add_secondary_axes` (`ax.axis_label_text_font_size` after `apply_to_axis`, `"ytitle2(size)"`/`"xtitle2(size)"`), `_dash_apply_z_options` (`key_obj.title_text_font_size`, `"ztitle(size)"`). `legend(size())` (21619-21629): per legend, `lg.label_text_font_size = css_pt(resolve_size(v, "text", css_to_pt(lg.label_text_font_size) or medium, ref))`, ValueError → `_dash_style_note("legend(size)", v, "size", "medium")` and medium on every legend. `labsize()` (22836-22844): the same against `axis_obj.major_label_text_font_size`, note option `"labsize"`, replacing the UserWarning. `zlabel(, labsize())` on a ColorBar: removed from `_bad` (26150-26152) and drawn as `key_obj.major_label_text_font_size`; on a Legend it stays named.
- **TR-08.11 Notes and silence.** Every note is `_dash_style_note(option, value, "size", "medium")` (CRITICAL helper, not edited; deduplicated per render by `_dash_warn_once`; the value echoed through `_dash_display`, 80 printable characters). No note for a negative, zero or `*-1` size (M6; E5).
- **TR-08.12 dash.ado.** No line changes. SU-01..SU-08 pin that `msize(4pt)`, `msize(*2)`, `msize(vhuge)`, `msize(.1in)`, `msize(1d3)`, `msize(HUGE)`, `mlabsize(*1.5)` and `mlabgap(2pt)` register with rc 0 and reach the spec as written.
- **TR-08.13 Both modes.** The three classes travel whole (class loop 33436-33438); `_textbox_size` (33360) and every module site listed in TR-08.7 are already on the functions tuple; R2 row S08: no constant or function added to either tuple, no `_shared_stat_lines` change. `TestTheServedAppCarriesEveryName` (with S01's `test_every_listed_name_exists`) and `TestTheServedAppDefinesEveryNameItReads` stay green (G4). No JavaScript twin: no saved-page script reads or writes a size (E3).
- **TR-08.14 Registries.** Under S08's anchor in `test/function_test_map.py` `FUNCTIONS`, alphabetical: `GlyphMapper._mlabel_radius_px`, `OptionTranslator.css_pt`, `OptionTranslator.css_to_pt`, `OptionTranslator.resolve_size`, `OptionTranslator.size_medium_pt`, `OptionTranslator.size_multiplier`, `OptionTranslator.size_ref_of`, `OptionTranslator.stata_number`, each mapped to its `test/test_size_units.py` node (TDD stubs). Existing keys whose named test is renamed by a flip are repointed in place: `SchemeParser._markersize_px` (to `…::TestTheUnitFunctions::test_markersize_px_anchors_medium_at_4_4pt`). No Stata program is added (`program_coverage_map.py` unchanged).
- **TR-08.16 The brushed copies (ratification row 27; Evidence E10).** New `@staticmethod GlyphMapper._sync_brushed_copies(fig, before=()) -> None`. It is a GlyphMapper method, so it travels with the class (R2: no copy-list entry). For each `GlyphRenderer` in `fig.renderers` whose `id()` is not in `before`, and for each of its `nonselection_glyph` and `muted_glyph` that is an instance of exactly `type(renderer.glyph)` (None, `"auto"` or another class is left alone), it walks every property name in `type(glyph).properties()` minus `bokeh.model.Model.properties()` and minus `{"decorations", "defs"}`:
  - a name ending `_alpha`: when both the glyph's and the copy's values are plain real numbers (not `bool`), the copy's value becomes `min(copy, glyph)`. Otherwise (a field or a transform) the copy keeps its own value;
  - any other name: when the copy's value differs from the glyph's, the copy's is set to the glyph's. A dict or `value()`/`field()` spec and a transform or mapper model are shared, never deep-copied, so a colour mapper updated by a move updates all three.
  It never raises (no user value reaches it), reads no option and writes nothing but the two copies. `_dash_add_glyph` (28955) and `_dash_add_pc_glyph` (29006), in place, record `_before = frozenset(id(r) for r in fig.renderers)` as their first statement. Their bodies are wrapped in `try: … finally: GlyphMapper._sync_brushed_copies(fig, _before)`, so every return path (a skipped layer included) syncs exactly the renderers that call added, and their return values are unchanged. The served app runs the same two functions (copied by name, :33131-33132) and the copied class, so neither the template nor `_make_figure_body` is edited (R12). Docstrings cite Evidence E10 and ratification row 27.
- **TR-08.17 The dimming keeps a copy no brighter than its glyph.** `_dash_dim_nonselection(fig, alpha=_NONSELECTION_ALPHA)` (29025-29047), in place (CRITICAL; warn): for each of `fill_alpha` and `line_alpha` the copy has, the value set is `min(alpha, g)` when the renderer's `glyph` has that property as a plain real number `g`. Otherwise (no `glyph`, as `test_served_bs_layout.py::test_the_helper`'s stand-ins have, or a field) it is `alpha`, as today. Its docstring gains one paragraph. Its call sites and its place in both modes are unchanged.
- **TR-08.18 Registries and help for the copies.** Under S08's anchor in `test/function_test_map.py` `FUNCTIONS`: `GlyphMapper._sync_brushed_copies` → `test/test_brushed_copies.py::TestBrushedCopiesFollowTheGlyph::test_the_sync_helper`. `_dash_dim_nonselection` keeps its key (test_linking.py). dash.sthlp "Linking and Brushing" (1147-1163) gains one sentence after "…highlights them where it draws them as markers": "Observations that are not selected keep their markers' size, symbol, colours and outline and are drawn faint, never more opaque than they are drawn unselected." No other help line moves.
- **TR-08.15 Security (rule 1).** Sizes reach the page only as floats or `css_pt` strings built from floats; no user text reaches CSS, HTML or JS. Every regex is anchored with no nested quantifier (linear time; a 1 MB value is judged in under 0.1 s); a value longer than 64 characters is a name, noted with a bounded echo. No `eval`, `exec`, `shell=True` or Stata call reads a size; the extractor's python block never calls Stata. `_dash_size_ref_in` is a Python attribute that is never serialised (a test reads the saved page's JSON for it). The brushed-copy sync copies only values already on the glyph (never user text) and names no new model, property or callback. It adds no text sink and no script.

## Boundaries

- **Batch partners.** S07 owns `scripts/extract_scheme_truth.py`, the 26 `dash-*.scheme` files, `test/fixtures/scheme_truth.json`, `SchemeParser._BUILTIN_NAMES`, `_dash_shipped_schemes`, `dash.pkg` and dash.sthlp's "twenty" (3300, 3501, 3505, 3573). S09 owns `_dash_finish_graph_text`, `_dash_inert_tex`, `DashRenderer._build_sources_and_figures`, `ServerAppBuilder._generate_app_source` and `test_label_sinks.py`'s TeX rows. S08 edits the bodies of `_dash_add_glyph`, `_dash_add_pc_glyph` and `_dash_dim_nonselection` (ratification row 27); S09 only contains a call of the last, unedited. S08 does not regenerate schemes and does not add `gsize label_gap` to the scheme files (TR-08.6 reads it with the default; a later regenerator may add it).
- **Later sections (do not touch their parts).** S13: the line kind, `_LWIDTH_MAP`, `translate_lwidth`, `_apply_line_opts`, `mlwidth`, `_ci_band_style`, `_extract_region_lwidth`, `_dash_refline_draw`, `SchemeParser._lwidth`, dash.ado's lwidth bounds and the default line's 1.15 px. S14: rcapsym's end-marker `size=7` (13599, 13602) and rcap's cap length. S15: tick and title chrome from the scheme (`apply_to_axis`, the rest of `apply_to_figure`). S24: the 0.707 `sm*` factor after `msize()`. S30: colour `*#` (reusing `stata_number`/`size_multiplier`). S31: `tlength()`, `titlegap()`. S33: the default marker-label size and colour (today 10px) and ColorBar chrome. S37: `mlabvposition()`, `mlabtextstyle()`. S48: `iscale()`. S56: `text()` sizes. S10: sub-option abbreviations (`labs()`, legend `s()`), including in `_dash_apply_legend` and `_dash_apply_z_options`. S11: stylelists (a blank inside a plot option's size is two elements, E5).
- **Residuals.** P2.14 (dash.ado refuses `msize(1e400)`, which twoway draws), P2.8 (arrowhead sizes), P2.16 (weighted marker sizes), P2.5 (legend key sizes), P2.20 (`labgap()`), P2.13's `scale()`. N3 (the dead served `_SIZE_MAP` global) needs `_generate_app_source` (R12). A bar's or rbar's brushed copies keep the build's width after a filter move until S14 deletes the move-time width (A61; `_dash_copy_redraw_geometry` and `_build_filter_widgets`' width script are not S08's, R12).
- **Not edited:** `_generate_app_source`, `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets`, `_apply_line_opts`, `_apply_fill_opts`, `_dash_warn_once`, `_dash_style_note`, `_dash_reset_notes`, `_apply_colorvar`, `SchemeParser._gsize` and its `_GSIZE_PT` table (scheme reading is unchanged; its `third_tiny` 1pt rounding and dash-only `ehuge` stay, Notes), `_dash_parse_axis_spec`, the 11 mappers' other lines, dash.ado, dash_parse.mata, the copy lists, any tracking document other than BUGS.md and CHANGELOG.md (A145).

## Stata truth

**New extractor** `scripts/extract_size_units_truth.do` → **new fixture** `test/fixtures/size_units_truth.json` (`git add -f`; `.git/info/exclude:58` ignores `*.json`). It copies S02's path-free extractor form (A130, R7): the repository root is the environment variable `DASH_REPO`, else `c(pwd)` when it holds `dash.ado` and `test/run_all_cscripts.do`, else `exit 601` with "set DASH_REPO to the dash repository"; it opens with `adopath ++ "<root>/"` and `global dash_nobrowser 1` (index E5), then `version 19`, `set graphics off`, `set more off`. It is run directly through the wrapper from the worktree: `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh $S $WT/scripts/extract_size_units_truth.do` (log `$S/extract_size_units_truth.log`). It is never run by another section (R7).

**Method.** Data: `sysuse auto, clear`, `keep in 1/3` (the full 74 rows for the colorvar probes). Each probe is registered by one program call `_su_probe id scheme site value command`, which runs `capture noisily <command>` inside `log using … , text` (so the note lines are captured), records `_rc`, for the marker site reads `` `.Graph.plotregion1.plot1.style.marker.size.setting' `` into a local before the export, then `graph export "<probe dir>/<id>.svg", replace`. The probe directory is under `c(tmpdir)`, never in the repository. After the loop one `python:` block (no Stata call inside it, no `shell=True`, a backtick written `\x60`) reads every SVG through `scripts/svg_truth.py`'s `svg_document` (texts, circles, canvas) and writes the fixture.

**Probes** (each id is `<scheme>_<site>_<n>`; `""` is the probe without the option):

| Site | Command (`twoway …`) | Values | Recorded |
|---|---|---|---|
| marker | `scatter mpg weight in 1, msize(V)` | `""` medium large small vtiny tiny vhuge ehuge 1.52778 4pt .1in .2cm 1.52778rs `*2` `*.5` 0 -1 `*-1` -1pt abc HUGE Large 4PT 1d3 | `setting`, the inner circle's r (the smaller of the two concentric circles; none for a size ≤ 0), `drawn_rs` = 2r / units_per_rs |
| title | `scatter mpg weight in 1, title("TTT", size(V))` | `""` medium large 12pt 5 `*2` vhuge huge minuscule half_tiny tenth relative3 10-pt 5rs .25in "4 pt" "4 in" abc LARGE 4PT ehuge vtiny -1 `*-1` | the font size of `TTT` in pt (`size/10`), or absent |
| subtitle | `scatter …, subtitle("SSS", size(V))` | `""` large 5 "4 pt" | the same for `SSS` |
| ytitle | `scatter …, ytitle(, size(V))` | `""` large `*2` "4 pt" | the y title's size |
| labsize | `scatter …, ylabel(, labsize(V))` | `""` 5 medium 10pt `*2` vhuge abc "4 pt" | the y tick labels' size |
| mlabsize | `scatter …, mlabel(make) mlabsize(V)` | `""` medium large 5 10pt `*2` vhuge abc Large -1 | `AMC Concord`'s size |
| legend | `(scatter mpg weight in 1) (scatter price weight in 1, yaxis(2)), legend(size(V))` | `""` 5 large 12pt `*2` abc "4 pt" | both keys' sizes |
| zlabel | `scatter mpg weight, colorvar(price) zlabel(, labsize(V))` (74 rows) | `""` large "4 pt" | the colour-key tick labels' size |
| ztitle | `scatter mpg weight, colorvar(price) ztitle("ZZ", size(V))` | `""` large | `ZZ`'s size |
| mlabgap | `scatter mpg weight in 1, mlabel(make) mlabposition(P) mlabgap(V)` | P in 12 2 3 4 6 9 0 × V in `""` 0 5 10pt medium `*2` -2 abc | the label anchor minus the circle centre (`dx_rs`, `dy_rs`) and the label's font size |
| mlabgap_msize | `scatter …, mlabel(make) msize(M) mlabgap(0)` | M in small large -1 | the same |
| origin | `bar mpg weight in 1, mlabel(make) barwidth(100)`; `pcarrow mpg weight y2 x2 in 1, mlabel(make)`; `pcbarrow …`; `scatteri 20 3000 "lab"` (y2 = mpg + 5, x2 = weight + 300) | `mlabgap(0)`, default, and `msize(large) mlabgap(0)` | the label anchor minus the point (the bar's top `<rect>` y, the arrow's first `<line>` x1/y1, the scatteri circle) |
| reference | `scatter mpg weight in 1, title("TTT", size(V)) msize(W)` | (V, W) in (`""`, `""`), (14pt, 4pt) | the title size, the marker setting and its drawn rs |

Schemes: every site under s2color; the marker, title, mlabgap and reference sites also under stcolor and economist. `units_per_rs` is min(viewBox width, height)/100 of each SVG (s2color 28.8, stcolor 32.4, economist 15.84); 10 units are 1 pt in every scheme. Ladders: the do-file reads `c(sysdir_base)style/symbolsize-*.style` and `gsize-*.style` with `file read` and passes each name's `set val`/`set sztype` pair to the python block as one `|`-joined global, so the fixture carries Stata's own tables.

**Fixture keys.** `{"_meta": {"stata_version", "born_date", "dash_commit", "extracted", "schemes": [...], "units": "SVG 10 units = 1 pt; rs = min(viewBox w, h)/100 units"}, "ladders": {"symbolsize": {name: [val, sztype]}, "gsize": {…}}, "probes": {id: {"scheme", "site", "value", "command", "rc", "notes": [the lines starting "(note:"], "setting", "units_per_rs", "drawn_rs", "drawn_pt", "dx_rs", "dy_rs", "font_pt"}}}`. `dash_commit` comes from `shell git -C "<root>" rev-parse HEAD > <tempfile>`, read back with `file read` into a local, and reaches python through `Macro.getLocal` (D12). Expected values are those of Evidence E4-E6; a difference is investigated and reported, never patched (R7).

**Truth block** (`test/test_wp30_truth.cscript`, S08's stub between `* ==== S08 P1.12a: …` and `* ==== end S08 ====`, gate `local only : env WP30_ONLY` then `` if inlist("`only'", "", "S08") { ``). The helpers go directly above S08's header, outside every gate, where a python block may hold braces: `_s08_page` and `_s08_app`, copies of WP-29 S03's `_s03_models`/`_S03Saved`/`_S03Served` readers (test_wp29_truth.cscript:688-760) renamed `_s08_*`, returning `S08_MSZ` (the first Scatter's size), `S08_TTL` (the title's font size), `S08_LBL` (the first LabelSet's `x_offset|y_offset|text_font_size`), `S08_LEG` (each legend's label font size) and `S08_CBL` (the ColorBar's label font size) for the saved page `S08_PAGE` and for the served app (built with `ServerAppBuilder` and `make_document`); the served one also after a `RangeSlider` move on `weight` (`S08_SAME_AFTER` = 1 when every value is unchanged). The block sets `set scheme s2color` (stcolor for SU-12) and restores the session's `c(scheme)` at its end. Each case runs twoway and dash on the same data and command, then S01's `_w30_expect` with the case id, and closes the case with `_w30_done <id> "<what>"`. Every saved page, served `app.py` and log is written under `` `w30_work' `` (named logs: `log using …, text replace name(su1k)`) and erased before S08's end line (TR-01.10 item 4):

| Case | Check |
|---|---|
| SU-10 | `msize(medium)` and `msize(1.52778)`: twoway's setting equals the default's (1.52778); dash's saved and served `S08_MSZ` equal the default page's, 5.8667 ± 0.001 |
| SU-11 | `title("T", size(large))` under s2color: twoway's title font equals the default title's (140 units); dash's `S08_TTL` is `14pt` in both modes, equal to the default page's |
| SU-12 | stcolor, `title("T", size(14pt))` against the default: twoway's ratio 140.06/157.44; dash's ratio (`css_to_pt`) the same ± 0.5 % in both modes |
| SU-13 | `mlabel(make)` by default and with `mlabgap(0)` at clock 3: twoway's `dx/28.8` × 3.84 equals dash's `x_offset` ± 0.05 px in both modes |
| SU-14 | `legend(size(*2))`: twoway's key font over the default's is 2; dash's the same in both modes |
| SU-15 | `colorvar(price) zlabel(, labsize(large))`: twoway 14 pt; dash's `S08_CBL` `14pt` in both modes |
| SU-16 | `msize(HUGE)`: twoway's log holds `named style HUGE not found`, dash's log holds one note naming `msize(HUGE)` and medium, and `S08_MSZ` is 5.8667; `msize(-1)`: neither log holds a note and dash's size is 0 |
| SU-17 | the served app after the move: `S08_SAME_AFTER` = 1 for the probes of SU-10, SU-11, SU-13 and SU-15 |

**Area script** (`test/test_option_validation.cscript`, one contiguous run after OV-168 and before the `CV-nn` corpus block at 864): a helper `_su_case` (a copy of `_ov_case`, 440-464, opening `version 19` instead of its `version 16.0`, whose registered name is `su` plus the id's digits) and SU-01..SU-08, each registering with rc 0, no "must be" line, and the spec carrying the value as written (the needle in the script's form, e.g. `` `""msize":"4pt""' ``, as OV-64 writes `kernel`): SU-01 `msize(4pt)`, SU-02 `msize(*2)`, SU-03 `msize(vhuge)`, SU-04 `msize(.1in)`, SU-05 `msize(1d3)`, SU-06 `msize(HUGE)`, SU-07 `mlabsize(*1.5)`, SU-08 `mlabgap(2pt)` (`dash scatter mpg weight, <opt> name(su0k)`).

## TDD test stubs

All in the new `test/test_size_units.py` unless named. `[mode]` is parametrised over `("saved", "served")` through a `_figure(mode, wd, plots, scheme="s2color", go=None)` helper copied from `test/test_scheme_linewidth.py:299-327` with graph options added; the served move uses `test_served_linked_views._served_doc` and `_fire`. Values in px are Bokeh screen pixels, in pt CSS points; 1 Stata unit = 2.88 pt = 3.84 px.

### Regression tests written by 08-01 (each FAILS at the batch-3 base; the expectations are twoway's values of Evidence E4/E5)

- Test: a bare number is Stata's relative unit, `resolve_size("1.52778", "marker", 4.4)` = 4.40001 pt and `("5", "text", 11)` = 14.4 pt — `test/test_size_units.py::TestResolveSize::test_a_number_is_statas_relative_unit`
- Test: `4pt` is 4 pt at reference 4 and 3.5556 pt at 4.5; `.1in` 7.2 pt; `.2cm` 5.669 pt; `1.52778rs` 4.40001 pt — `::TestResolveSize::test_absolute_units_at_the_reference`
- Test: `"4 pt"` and `"4 in"` are 4 pt and 288 pt (the graph-option reading, E5) — `::TestResolveSize::test_a_blank_before_a_unit`
- Test: `*2` against 14 pt is 28; `*.5` 7; `*-1` -14 (signed) — `::TestResolveSize::test_the_multiplier`
- Test: each of the 13 symbolsize names and each of the 31 relative gsize names (E6) is its Stata value × 2.88; `10-pt` is 10 pt at reference 4 — `::TestResolveSize::test_every_symbolsize_keyword`, `::test_every_gsize_keyword`
- Test: `HUGE`, `Large`, `4PT`, `4Pt` raise ValueError; `ehuge` and `vtiny` raise for `"text"` and read for `"marker"` — `::TestResolveSize::test_names_are_case_sensitive`, `::test_ehuge_and_vtiny_are_not_text_sizes`
- Test: `1d3` is 1000 units — `::TestResolveSize::test_statas_d_exponent`
- Test: `abc`, `""`, `5px`, `inf`, `nan`, `"٥"`, `0x10`, `1_000`, `--5`, `5e`, `5,0`, 65 characters, `1001` and an unknown kind raise ValueError — `::TestResolveSize::test_what_is_not_a_size_raises`
- Test: `stata_number` reads `.5`, `-2`, `1e2`, `1d3`; `size_multiplier` reads `*2` and `* .5`, and gives None for `2`, `**2`, `*abc` — `::TestStataNumberAndMultiplier::test_stata_number_reads_statas_spellings`, `::test_size_multiplier_reads_star_number_only`
- Test: `css_pt(7.99776) == "8pt"`, `css_pt(14.4) == "14.4pt"`, `css_pt(1e-6) == "0pt"`, `css_pt(-3) == "0pt"`, `css_pt(2880) == "2880pt"`, no `e` in any output; `css_to_pt("14pt") == 14`, `css_to_pt("16px") == 12`, `css_to_pt("1em") is None` — `::TestCssHelpers::test_css_pt_writes_two_fixed_decimals`, `::test_css_to_pt_reads_pt_and_px`
- Test [mode]: the default s2color marker is 5.8667 px; stcolor 4.0; economist 9.3335 — `::TestTheDefaultSizes::test_the_default_marker`
- Test [mode]: `msize(medium)` equals the default glyph's size; `msize(1.52778)` 5.8667, `msize(4pt)` 5.3333, `msize(*2)` 11.7334, `msize(vhuge)` 21.331, `msize(.1in)` 9.6 — `::TestExplicitMarkerSizes::test_medium_equals_the_default`, `::test_numbers_units_and_star`
- Test [mode]: under stcolor `msize(*2)` is 8.0 (twice stcolor's small) — `::TestExplicitMarkerSizes::test_star_doubles_the_schemes_default`
- Test [mode]: `msize(-1)`, `msize(*-1)`, `msize(-1pt)` and `msize(0)` draw size 0 with no note — `::TestExplicitMarkerSizes::test_negative_or_zero_draws_nothing_silently`
- Test [mode]: `title("T", size(large))` is `"14pt"` and equals the default title's font; `size(5)` 14.4pt, `12pt`, `*2` 28pt, `vhuge` 28pt, `tenth` 28.8pt, `relative3` 8.64pt, `10-pt` 10pt, `4 pt` 4pt — `::TestExplicitTextSizes::test_title_large_is_the_heading`, `::test_title_numbers_units_and_star`
- Test [mode]: `ytitle(, size(large))` 14pt; `subtitle("S", size(5))` 14.4pt; `ytitle2(, size(5))` on a `yaxis(2)` layer 14.4pt; `note("N", size(*2))` twice the scheme's note size — `::TestExplicitTextSizes::test_axis_titles_subtitle_note_and_axis_two`
- Test [mode]: `ylabel(, labsize(5))` 14.4pt, `labsize(medium)` 11pt, `labsize(10pt)` 10pt, `labsize(*2)` twice the default — `::TestExplicitTextSizes::test_labsize`
- Test [mode]: `mlabsize(medium)` 11pt, `mlabsize(5)` 14.4pt, `mlabsize(10pt)` 10pt — `::TestExplicitTextSizes::test_mlabsize`
- Test [mode]: `legend(size(5))` 14.4pt, `size(large)` 14pt, `size(12pt)` 12pt, `size(*2)` twice the default, on every legend — `::TestExplicitTextSizes::test_legend_size`
- Test [mode]: `colorvar(price) zlabel(, labsize(large))` sets the ColorBar's label font to 14pt with no note; `ztitle("Z", size(large))` 14pt — `::TestExplicitTextSizes::test_the_colour_key`
- Test [mode]: under stcolor `title(, size(14pt))` is 12.444pt while `size(large)` is 14pt; under economist `size(14pt)` is 25.455pt; under s2color 14pt; stcolor `msize(4pt)` 4.7407 px — `::TestAbsoluteUnitsFollowTheSchemesReference::test_title_and_marker`
- Test [mode]: `msize(abc)`, `msize(HUGE)`, `msize(Large)` and `msize(4PT)` draw 5.8667 px with one note naming the value and `medium`; under stcolor `msize(abc)` is 5.8667, not 4.0 — `::TestUnknownNamesDrawMedium::test_markers`
- Test [mode]: `title(T, size(abc))` and `size(LARGE)` 11pt; `mlabsize(abc)` 11pt; `legend(size(abc))` 11pt; `ylabel(, labsize(abc))` 11pt; `mlabgap(abc)` an offset of 2.933 + 14.667 px; one note each — `::TestUnknownNamesDrawMedium::test_text_and_gaps`
- Test: `size_medium_pt("marker")` 4.40001, `("text")` and `("gap")` 10.99987 — `::TestUnknownNamesDrawMedium::test_the_medium_of_each_class`
- Test [mode]: `mlabel(make)` at clock 3 is `(5.6, 0)`; `mlabgap(0)` `(2.933, 0)`; `mlabgap(5)` 22.133; `mlabgap(10pt)` 16.267; `mlabgap(*2)` 8.267; `mlabgap(-2)` -4.747 — `::TestMarkerLabelsFromTheMarkerEdge::test_the_gap_is_from_the_edge`
- Test [mode]: `msize(large) mlabgap(0)` 4.667; `msize(small) mlabgap(0)` 2.0; `msize(-1) mlabgap(0)` -1.92 — `::TestMarkerLabelsFromTheMarkerEdge::test_the_radius_follows_msize`
- Test [mode]: clocks 12, 2, 4, 6 and 9 put the anchor (r + g) along the unit vector (`(0, 5.6)`, `(4.850, 2.8)`, `(4.850, -2.8)`, `(0, -5.6)`, `(-5.6, 0)`); clock 0 is `(0, 0)` whatever the gap — `::TestMarkerLabelsFromTheMarkerEdge::test_every_clock`
- Test [mode]: bar, pcarrow and pcbarrow labels sit half the scheme's marker size plus the gap from their point (5.6 px by default; `msize(large) mlabgap(0)` 4.667); scatteri and pcarrowi immediate labels too — `::TestMarkerLabelsFromTheMarkerEdge::test_no_marker_types`
- Test [mode]: under stcolor the default offset is 2.0 + 2.667 px — `::TestMarkerLabelsFromTheMarkerEdge::test_under_stcolor`
- Test: `_mlabel_radius_px({"msize": "large"}, 5.8667)` 4.6668; `({}, 4.0)` 2.0 — `::TestMarkerLabelsFromTheMarkerEdge::test_the_radius_helper`
- Test (served): after a `RangeSlider` move on `weight`, every size of a dashboard holding `msize(large)`, `mlabel(make) mlabgap(5)`, `title(T, size(*2))`, `ylabel(, labsize(5))` and `legend(size(large))` is unchanged and equals the saved page's — `::TestBothModesAfterAMove::test_sizes_survive_a_move`
- Test [mode]: every figure, by() panels included, carries `_dash_size_ref_in` equal to its scheme's `size_ref_in` (4.0 s2color, 4.5 stcolor, 2.2 economist); `size_ref_of(object())` is 4.0 and a stamp of `"x"`, `nan`, `-1` or `1e9` reads 4.0 — `::TestTheReferenceStamp::test_every_figure_carries_it`, `::test_size_ref_of_reads_the_stamp`
- Guard: the saved page's HTML holds no `_dash_size_ref_in` — `::TestTheReferenceStamp::test_it_is_never_serialised` (passes at the base and after; listed apart in the failure text)
- Test: `resolve_size("9" * 10**6, "text", 11)` raises within 0.1 s; `title("T", size(</style><script>x</script>))` draws `11pt` with one note whose echo is at most 80 printable characters, and the page holds neither `<script>x` nor the value in any style string — `::TestAdversarialSizes::test_a_megabyte_value_is_judged_at_once`, `::test_hostile_text_never_reaches_a_style`

### Brushed copies, written by 08-01 (`test/test_brushed_copies.py`; ratification row 27; each FAILS at the base unless marked guard)

`[mode]` uses the same `_figure(mode, wd, plots, scheme="s2color", go=None)` helper as `test_size_units.py`, imported from it. Linked pairs use `test_help_claims_4.py`'s `_pair_spec(link="g1 g2")`, `_saved`, `_served_app` and `_served_session`. The served move uses `test_served_linked_views._served_doc` and `_fire`. `same(a, b)` compares every non-alpha property of TR-08.16's walk. Expectations are relations to the drawn glyph, never pixel literals, so S13, S16, S24 and S30 move none of them.

- Test: on a hand-built `GlyphRenderer` (`Scatter` glyph size 15, red; copies at Bokeh's defaults), `GlyphMapper._sync_brushed_copies(fig)` makes both copies `same` as the glyph, sets `fill_alpha` to `min(0.1, 0.8)` and `min(0.2, 0.8)`, and leaves a renderer listed in `before`, a `None` copy and a copy of another class untouched; `name` and `tags` are not copied — `::TestBrushedCopiesFollowTheGlyph::test_the_sync_helper`
- Test: `_dash_dim_nonselection` on a figure whose scatter glyph has `fill_alpha` 0.0 and `line_alpha` 0.05 sets the copy's to 0.0 and 0.05, and on a `SimpleNamespace` renderer without `glyph` sets 0.15 as today — `::TestBrushedCopiesFollowTheGlyph::test_the_dim_helper_keeps_a_copy_no_brighter_than_its_glyph`
- Test [mode]: `scatter, msize(large) mcolor(red)`, `connected, mcolor(red) lcolor(blue) msize(large)` (both renderers) and `scatteri … msymbol(D)`: each copy is `same` as its glyph — `::test_marker_options_reach_the_copies`
- Test [mode]: `line, lwidth(thick) lcolor(red) lpattern(dash)`, `scatter, msymbol(T) mlwidth(thick) mlcolor(blue)` and `rcap lo hi x, lcolor(red)`: line colour, width and dash of each copy equal the glyph's — `::test_line_and_outline_options_reach_the_copies`
- Test [mode]: `bar, fcolor(red)`, `area, fcolor(yellow)` and `scatter, colorvar(price)`: each copy's `fill_color` equals the glyph's (the same field spec and mapper object for colorvar) — `::test_fill_and_colorvar_reach_the_copies`
- Test [mode]: `msymbol(Oh)` gives both copies `fill_alpha` 0.0; `malpha(5)` gives both copies alphas of at most 0.05; `msymbol(i)` 0.0 everywhere. The same holds on a linked pair after `_dash_dim_nonselection` — `::test_a_copy_is_never_more_opaque_than_the_glyph`
- Test [mode]: a `pcscatter … , mcolor(red) msize(large)` layer and every panel of `scatter, mcolor(red) by(foreign)` (S28's panels found through `test/by_panel_probe.py` once it exists; before S28, every figure of the result) — `::test_paired_and_by_panel_layers`
- Test [mode]: with a `RangeSlider` filter on `x`, after `_fire` (served) and in the saved document (whose filter scripts write no glyph property, E3), the copies of `msize(large) mcolor(red) lwidth(thick)` layers are still `same` as their glyphs — `::test_the_copies_hold_after_a_move`
- Guard [mode]: a plain scatter's copies keep 0.1 (unlinked), 0.15 (linked) and 0.2 (muted) — `::test_the_dimming_alphas_are_kept` (passes at the base and after)
- Guard (saved): a frozen layer's `muted_glyph` is still `_dash_stale_glyph(glyph)`'s rebuild (`test_saved_stale_cue.py`'s frozen-layer spec) — `::test_the_stale_cue_still_rebuilds_the_muted_glyph` (passes at the base and after)

### Added by 08-03 (fixture-driven; each fails at the base unless marked guard)

- Test: the fixture's `_meta` holds `stata_version`, `born_date`, `dash_commit` and `extracted` — `::TestTheFixture::test_the_meta_stamp` (passes once the fixture exists; listed with the guards)
- Test: `OptionTranslator._SYMBOLSIZE_RS`, `_GSIZE_RS` and the two `_ABS_PT` tables equal the fixture's `ladders` — `::TestTheFixture::test_the_ladders_are_statas`
- Test [probe × mode]: for every marker, title, subtitle, ytitle, labsize, mlabsize, legend, zlabel and ztitle probe with a drawn size, dash's size over dash's default = twoway's `drawn_rs` over twoway's default ± 1 %; a probe twoway draws nothing for draws 0 — `::TestStataRatios::test_sizes`
- Test [probe × mode]: for every mlabgap, mlabgap_msize and origin probe, dash's offset along the clock direction / 3.84 = twoway's (r + g) in rs ± 0.02 — `::TestStataRatios::test_label_offsets`
- Test [scheme in `SchemeParser._BUILTIN_NAMES` × mode]: `msize(<symbolsize p>)` equals the default marker; `title(T, size(<gsize heading>))`, `ylabel(, labsize(<gsize tick_label>))` and `legend(size(<gsize key_label>))` equal the scheme's own font sizes (`css_to_pt` ± 0.01 pt) — `::TestExplicitKeywordEqualsSchemeDefault::test_each_scheme`
- Test: `SchemeParser._SYMBOLSIZE_PT[k]` = `_SYMBOLSIZE_RS[k] × 2.88` ± 0.01 for every key, and `_GSIZE_PT` likewise for every key both hold except `third_tiny` (the scheme table's 1 pt) — `::TestTheTablesAgree::test_the_scheme_tables_match_the_ladders` (fails at the base: the `_RS` tables are new)
- Guard [mode × type]: for scatter, connected, dot, dropline, rcapsym, rconnected, rscatter, pcscatter, pccapsym and scatteri, the glyph built with no options equals the glyph built with `_apply_marker_opts` monkeypatched to a no-op, property by property; `_apply_mlabel_opts` with only `mlabel` adds one LabelSet and changes no glyph — `::TestEmptyOptionsChangeNothing::test_marker_options`, `::test_label_options` (passes at the base and after)
- Guard: no module-level JavaScript string of `dash_render` (the saved page's filter, stale-cue and finisher scripts) matches `\.size\s*=`, `font_size\s*=`, `x_offset\s*=` or `y_offset\s*=`, so a saved filter move cannot change a size (E3) — `::TestBothModesAfterAMove::test_no_saved_script_writes_a_size` (passes at the base and after)
- (ratification 06oct2026: the P2.49 guard `TestBrushedCopiesKeepCreationValues` is not written; the copies are fixed, see "Brushed copies" below.)

### Other files

- `test/test_mode_parity.py` `CORPUS`, appended after its last case (R8), in `_case(name, plots, bo, go)`'s shape: `"S08 msize(*2) mlabgap(1) mlabsize(*2)"` (`[_sc(msize="*2", mlabel="foreign", mlabgap="1", mlabsize="*2")]`); `"S08 msize(4pt) under stcolor"` (`[_sc(msize="4pt")]`, bo `{"scheme": "stcolor"}`); `"S08 title size(*1.5) and labsize(10pt)"` (`[_sc()]`, go `{"title": "T, size(*1.5)", "ylabel": ", labsize(10pt)"}`); `"S08 legend size(5)"` (`[_sc(), plot_for("lfit")]`, go `{"legend": "size(5)"}`); `"S08 mlabposition(2) and bar labels"` (`[_sc(mlabel="foreign", mlabposition="2"), plot_for("bar", {"mlabel": "foreign"})]`); `"S08 msize(HUGE) noted"` (`[_sc(msize="HUGE")]`). `ALLOWED` and `_MUST_WARN` are not edited.
- `test/function_test_map.py`: TR-08.14's keys under S08's anchor.
- The flips F1-F29 of Evidence E9, each with a `Flipped:` line.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Resolver grammar, ladders, helpers (rule 3) | pytest `test_size_units.py` (`TestResolveSize`, `TestStataNumberAndMultiplier`, `TestCssHelpers`) | E6 constants | n/a (pure) |
| Default and explicit marker, text and gap sizes | pytest `[mode]` classes | E4/E5 values | yes |
| Ratios against twoway, every probe | pytest `TestStataRatios` | `size_units_truth.json` | yes |
| Keyword = scheme default, every shipped scheme | pytest `TestExplicitKeywordEqualsSchemeDefault` | `_BUILTIN_NAMES` (26 after S07) | yes |
| After a filter move | pytest `TestBothModesAfterAMove`; truth SU-17 | — | served moved, saved compared |
| Parity | `test_mode_parity.py` with S08's six CORPUS cases (G3) | — | yes |
| Identity guard | pytest `TestEmptyOptionsChangeNothing` | — | yes |
| Brushed copies (ratification row 27) | pytest `test/test_brushed_copies.py` (`TestBrushedCopiesFollowTheGlyph`), after a served move too | — | yes |
| Live twoway against dash | `test_wp30_truth.cscript` SU-10..SU-17, `WP30_ONLY=S08`, through the driver | live Stata | yes |
| dash.ado accepts the forms | `test_option_validation.cscript` SU-01..SU-08, through the driver | — | registration only |
| Served names (G4) | `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` | — | served |
| Registries | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_cscript_hygiene.py`, `test_tracking_documents.py` | — | — |
| Security (rule 1) | `TestAdversarialSizes`, `TestTheReferenceStamp::test_it_is_never_serialised` | — | yes |
| The whole suite | one full run through the queue (index E1) before the commit | — | — |

**Acceptance criteria.**
- **AC-08.1** Every 08-01 and 08-03 regression test (`test/test_brushed_copies.py` included) failed on the unfixed tree (`<scratch>/08-P1.12a-failure.txt`) and passes after the fix; the guard classes pass before and after.
- **AC-08.2** `msize(<symbolsize p>)`, `title(, size(<heading>))`, `ylabel(, labsize(<tick_label>))` and `legend(size(<key_label>))` equal the scheme's defaults under each of the 26 shipped schemes, in both modes.
- **AC-08.3** Every fixture probe's ratio matches twoway's within 1 % (sizes) or 0.02 units (offsets), in both modes.
- **AC-08.4** The default s2color marker is 5.8667 px, stcolor 4.0, economist 9.3335; the default 3 o'clock label is 5.6 px from its point (stcolor 4.667).
- **AC-08.5** Unknown and wrong-case names draw medium with exactly one note each; negative sizes draw nothing with no note (M6).
- **AC-08.6** After a served filter move every size is unchanged and equals the saved page's; `test_mode_parity.py` is green with the six new cases.
- **AC-08.7** `test_wp30_truth.cscript` under `WP30_ONLY=S08` prints SU-10..SU-17 PASS; `test_option_validation.cscript` prints SU-01..SU-08 PASS and still ends `ALL CHECKS PASSED`; `test_wp29_truth.cscript` prints ET-01..ET-10 PASS with `@14pt@`.
- **AC-08.8** F1-F29 are flipped in place with `Flipped:` lines; no test was deleted and the collected test count did not fall.
- **AC-08.9** The full suite is green once through the queue; the served-name guards and the registries are green; `gitnexus detect-changes` at landing names only S08's symbols.
- **AC-08.10** BUGS.md: `P1.12a` closed in the WP-30 form naming tests that exist, the brushed-copy tests among them; no other entry added and no P2.49 entry anywhere; `WP30_OPEN` lost only `P1.12a`; both `<!-- WP-30 P1.12a -->` markers replaced (five Results lines); CHANGELOG.md:521-523 corrected; no AI reference anywhere.
- **AC-08.11** (ratification row 27) Every node of `test/test_brushed_copies.py` but its two guards failed at the base and passes after 08-09, in both modes. The five files of Evidence E10 that read a copy pass unflipped. dash.sthlp's Linking and Brushing sentence is in place.

## Tasks

**Commit boundary.** Tasks 08-01 to 08-19 form the one commit of entry `P1.12a`, subject `Draw marker, text and label-gap sizes in Stata's units (WP-30 P1.12a)`, made by 08-19 on `wp30-s08` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s08` (`$WT`), after one full run through the queue. `$S` is `<scratch>/s08` (`<scratch>`: the orchestrator's WP-30 scratch directory, index "Deltas"); every command runs from `$WT` unless it names the main checkout. The body:
1. opens with `<scratch>/08-P1.12a-failure.txt`;
2. then the measured defect (Evidence E3) and what changed, where, in both modes;
3. then one line each: `Regression: test/test_size_units.py::<Class>::<test> -- failed at <batch-3 base sha> with <text>`; `Flipped: <node> -- <old expectation> was wrong because <why>` (F1-F29); `Fixture: test/fixtures/size_units_truth.json (scripts/extract_size_units_truth.do)`; `BUGS.md: "<WP30_OPEN["P1.12a"]>" (closed)`; one `Regression: test/test_brushed_copies.py::TestBrushedCopiesFollowTheGlyph::<test> -- failed at <batch-3 base sha> with <text>` line per brushed test, under a line saying the brushed-away and muted copies are fixed under P1.12a (ratification row 27; no other BUGS.md entry); and one line saying why the single-y digest moved (R10).

No subject, body, BUGS line, CHANGELOG line or help line names a tool or vendor (G7); `grep -Eic 'claude|anthropic'` prints 0 on the message file before and on `git log -1 --format=%B` after. Never stage `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.ultraplan/` or any `*.html` (E7, G6).

<task type="auto" id="08-01">
  <name>Write the failing size regression tests</name>
  <files>test/test_size_units.py, test/test_brushed_copies.py</files>
  <action><![CDATA[
    Run `mkdir -p "$S"`; check that `git -C $WT rev-parse HEAD` equals `<scratch>/batch-3-base.txt` and `git -C $WT branch --show-current` prints `wp30-s08`, else stop. Read `<scratch>/batch-3-impact.txt` and confirm it records the CRITICAL warnings for translate_msize, _textbox_size, _mlabel_gap_px, _apply_marker_opts and _apply_mlabel_opts and the HIGH ones for _dash_apply_axis_spec and _dash_apply_z_options with their approval (index 3.0); if any is missing, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout (never in $WT), append it, and report every HIGH or CRITICAL result before editing. Create test/test_size_units.py with every test of "TDD test stubs / Regression tests written by 08-01", with exactly those class and test names, the `_figure(mode, wd, plots, scheme="s2color", go=None)` helper (copied from test/test_scheme_linewidth.py:299-327, graph options added), the served move through `test_served_linked_views._served_doc` and `_fire`, and every expectation written as the literal twoway value of Evidence E4/E5 (never computed through dash). Create test/test_brushed_copies.py with every test of "TDD test stubs / Brushed copies" (ratification row 27), with exactly those class and test names and the helpers named there, each expectation a relation to the drawn glyph (Evidence E10). Run `python3 -m pytest test/test_size_units.py -q -n0 -p no:cacheprovider -rf > "$S/08-01.log" 2>&1` and `python3 -m pytest test/test_brushed_copies.py -q -n0 -p no:cacheprovider -rf > "$S/08-01b.log" 2>&1`, then write `<scratch>/08-P1.12a-failure.txt`: the base sha, each FAILED line of both logs with its first assertion text (the brushed lines under a `Brushed copies (ratification row 27):` heading), and the guards that pass (`TestTheReferenceStamp::test_it_is_never_serialised`, `TestBrushedCopiesFollowTheGlyph::test_the_dimming_alphas_are_kept`, `::test_the_stale_cue_still_rebuilds_the_muted_glyph`). Do not touch dash_render.py and do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/08-01.log"` prints at least 55; `grep -E '^[0-9]+ failed, 1 passed' "$S/08-01.log"` matches; `grep -E '^14 failed, 3 passed' "$S/08-01b.log"` matches (the six `[mode]` tests in both modes and the two unit tests fail; the three guard nodes pass); `grep -c 'Brushed copies (ratification row 27):' <scratch>/08-P1.12a-failure.txt` prints 1; `test -s <scratch>/08-P1.12a-failure.txt`.]]></verify>
  <done>Every 08-01 regression test existed with twoway's literal values, the brushed-copy tests existed with relations to the drawn glyph, all were shown failing on the unfixed tree, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="08-02">
  <name>Extract the size truth from Stata</name>
  <files>scripts/extract_size_units_truth.do, test/fixtures/size_units_truth.json</files>
  <action><![CDATA[
    Create scripts/extract_size_units_truth.do exactly as "Stata truth" specifies: S02's root rule (DASH_REPO, else c(pwd) holding dash.ado and test/run_all_cscripts.do, else exit 601), `adopath ++` and `global dash_nobrowser 1` first, the `_su_probe` program, every probe of the table under its schemes, the ladder read through `file read` of c(sysdir_base)style/symbolsize-*.style and gsize-*.style, the D12 stamp through `shell git -C` into a tempfile, and one trailing python block that reads the SVGs through scripts/svg_truth.py's svg_document, never calls Stata, never uses shell=True and spells a backtick \x60. Run `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_size_units_truth.do"` and read `$S/extract_size_units_truth.log`. Check the fixture against Evidence E4-E6 (s2color default marker drawn_rs 1.528 ± 0.01; title large 14 pt; mlabgap default dx_rs 1.457 ± 0.01; pcarrow msize(large) mlabgap(0) dx_rs 1.216 ± 0.01; stcolor title 14pt 14.0 pt against a 15.74 pt default; the HUGE probe's notes hold "named style HUGE not found"); a difference is investigated and reported, never patched by hand (R7). Run `git add -f test/fixtures/size_units_truth.json`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/size_units_truth.json'));m=d['_meta'];assert all(k in m for k in ('stata_version','born_date','dash_commit','extracted'));p=d['probes'];assert len(p)>=150;assert float(d['ladders']['symbolsize']['medium'][0])==1.52778;print(len(p))"` prints the probe count; `git ls-files test/fixtures/size_units_truth.json` prints the path; `tail -5 "$S/extract_size_units_truth.log"` shows the python block's closing line `size_units_truth: wrote <N> probes` (the do-file prints it) and no uncaptured `r(` error.]]></verify>
  <done>Stata's own drawing of every marker, text and gap probe and Stata's size ladders were recorded in a stamped fixture staged with git add -f.</done>
</task>

<task type="auto" id="08-03">
  <name>Add the fixture-driven and guard tests</name>
  <files>test/test_size_units.py</files>
  <action><![CDATA[
    Add every test of "TDD test stubs / Added by 08-03" to test/test_size_units.py, reading test/fixtures/size_units_truth.json once at module level (the path from `Path(__file__).parent / "fixtures"`). `TestStataRatios` is parametrised over the probe ids (ids as pytest ids) and the two modes; `TestExplicitKeywordEqualsSchemeDefault` over `sorted(dr.SchemeParser._BUILTIN_NAMES)` (20 names before S07 lands, 26 after) and the modes; `TestEmptyOptionsChangeNothing` uses `monkeypatch.setattr(dr.GlyphMapper, "_apply_marker_opts", lambda self, r, o: None)` and compares every glyph property through `glyph.properties_with_values()`. Run the file on the unmodified renderer, `python3 -m pytest test/test_size_units.py -q -n0 -p no:cacheprovider -rf > "$S/08-03.log" 2>&1`, and append to `<scratch>/08-P1.12a-failure.txt` the new FAILED lines and, under a "Guard tests (pass before and after)" heading, the passing guards (`TestTheFixture::test_the_meta_stamp`, `TestEmptyOptionsChangeNothing`, `TestBothModesAfterAMove::test_no_saved_script_writes_a_size`, `TestTheReferenceStamp::test_it_is_never_serialised`). Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/08-03.log"` is larger than in `$S/08-01.log`; `grep -c 'Guard tests' <scratch>/08-P1.12a-failure.txt` prints 1; `python3 -m pytest test/test_size_units.py -q -n0 -p no:cacheprovider -k "EmptyOptions or meta_stamp or never_serialised or no_saved_script"` passes.]]></verify>
  <done>The fixture-driven regression tests failed on the unfixed renderer, the guards passed, and both lists were added to the saved failure text.</done>
</task>

<task type="auto" id="08-04">
  <name>Add Stata's ladders and the resolver</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    In `OptionTranslator` (class at 5098), after `_SIZE_MAP` (5309-5319) and before the `_LWIDTH_MAP` banner (5321), add the constants of TR-08.1 with a comment per table naming its style files, and the staticmethods `stata_number`, `size_multiplier`, `resolve_size`, `size_medium_pt`, `css_pt`, `css_to_pt` and `size_ref_of` exactly as TR-08.2 to TR-08.4 define them, each with a docstring citing Evidence E4-E6 (resolve_size's states the grammar order and that it never floors). Add a comment above `_SIZE_MAP` saying no size path reads it and the served header still emits it (research N3, index R12). Change nothing else in this task. Add the seven `OptionTranslator.*` keys of TR-08.14 under the `# WP-30 S08 (P1.12a): …` anchor of test/function_test_map.py, alphabetically, each mapped to its 08-01 test node.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_size_units.py -q -n0 -p no:cacheprovider -k "TestResolveSize or TestStataNumberAndMultiplier or TestCssHelpers or medium_of_each_class or size_ref_of_reads or megabyte"` passes; `python3 -m pytest test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>One resolver read every marker, text and gap size in Stata's units, with Stata's ladders, one number and multiplier grammar and the CSS helpers, all on OptionTranslator and mapped to their tests.</done>
</task>

<task type="auto" id="08-05">
  <name>Put the scheme on the one unit</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `SchemeParser` set `_MARKER_PX_ANCHOR = 1.52778 * 2.88 * 4.0 / 3.0` (5966), rewrite the comment above it (5959-5965) to say the anchor is Stata's medium on dash's one unit (IR-1), and make `_markersize_px` (7248-7276) read through `OptionTranslator.resolve_size(kw, "marker", OptionTranslator.size_medium_pt("marker"), getattr(self, "size_ref_in", 4.0))` times `PX_PER_PT`, floored at 0, keeping its lower-casing, its empty-name and unknown-name fallback to the anchor (silent, as today) and updating its docstring's numbers (5.87, 4.0, 9.33). In `_init_properties`, directly after `self.graphsize_y` (7016), add `size_ref_in` and `label_gap_pt` as TR-08.6 defines them, with a comment citing Evidence E2/E5. Make `self.size_ref_in`'s stamp the first statement of `apply_to_figure` (7376): `fig._dash_size_ref_in = self.size_ref_in`, with a comment that the leading underscore keeps it out of Bokeh's property machinery and the page. Do not touch `_gsize`, `_GSIZE_PT`, `_SYMBOLSIZE_PT` or `apply_to_axis`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_size_units.py -q -n0 -p no:cacheprovider -k "TestTheDefaultSizes or TestTheReferenceStamp or TestTheTablesAgree"` passes; `python3 -c "import sys;sys.path.insert(0,'.');import dash_render as d;print(d.SchemeParser('s2color').default_marker_size(0), d.SchemeParser('stcolor').size_ref_in)"` prints a first number starting `5.86667` and then `4.5`.]]></verify>
  <done>Every scheme drew its markers on the one Stata unit, each figure carried its scheme's reference length in both modes, and no scheme text size changed.</done>
</task>

<task type="auto" id="08-06">
  <name>Route marker sizes through the resolver</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Rewrite `OptionTranslator.translate_msize` (5542-5570) as `translate_msize(value, default_px=None, ref_in=4.0) -> float`: the signed px of `resolve_size(value, "marker", (default_px if given else the medium px) * 0.75, ref_in) * PX_PER_PT`, raising ValueError as before; update its docstring (Stata units, signed, the callers floor). In `GlyphMapper._apply_marker_opts` (8699-8704) apply TR-08.8: a numeric `glyph.size` is the default, `glyph.size = max(0.0, px)`, and an unreadable value notes through `_dash_style_note("msize", v, "size", "medium")` and draws the medium px; a non-numeric `glyph.size` (a field) keeps today's lines. In `map_scatteri` (13701-13706) resolve against `self.scheme.default_marker_size(color_idx)` through `translate_msize`, floored at 0, still silent on ValueError. Warn in the progress output that `_apply_marker_opts` and `translate_msize` are CRITICAL (Evidence E8) before editing.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_size_units.py -q -n0 -p no:cacheprovider -k "TestExplicitMarkerSizes or TestAbsoluteUnitsFollowTheSchemesReference or (TestUnknownNamesDrawMedium and markers) or TestEmptyOptionsChangeNothing"` passes; `python3 -m pytest test/test_option_validation.py -q -n0 -p no:cacheprovider -k "bad_msize or scatteri_msize or translators_still_raise or non_finite"` passes.]]></verify>
  <done>msize() was read in Stata's units on every marker in both modes, an unknown name drew medium with one note, and a negative size drew nothing in silence.</done>
</task>

<task type="auto" id="08-07">
  <name>Place marker labels from the marker edge</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `GlyphMapper._mlabel_radius_px(self, options, base_px)` and rewrite the staticmethod `_mlabel_gap_px(raw, default_pt=2.0, ref_in=4.0)` as TR-08.9 defines them, with docstrings citing Evidence E5's clock, origin and signed-radius measurements. In `_apply_mlabel_opts` (9302) add the keyword `radius_px=None`, read `mlabsize` (9455-9460) and `mlabgap` (9474-9490) through the resolver as TR-08.9 says, and set the offsets to (radius + gap) along the clock's unit vector, (0, 0) at clock 0; keep `_MLABEL_CLOCK` and its anchors unchanged and say in a comment that its base pair is no longer read for the offset. Pass `radius_px=self._mlabel_radius_px(options, self.scheme.default_marker_size(color_idx))` at the 11 call sites (9861, 10289, 13509, 13623, 13624, 13953, 14103, 14175, 14282, 14418 through `_immediate_labels`, 14632) and give `_immediate_labels` (14355) the keyword `radius_px=None`, passed by `map_scatteri` (13725) and `map_pcarrowi` (14462). Add `GlyphMapper._mlabel_radius_px` to test/function_test_map.py under S08's anchor; warn that `_apply_mlabel_opts` and `_mlabel_gap_px` are CRITICAL before editing.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_size_units.py -q -n0 -p no:cacheprovider -k "TestMarkerLabelsFromTheMarkerEdge or (TestUnknownNamesDrawMedium and text_and_gaps) or mlabsize or label_offsets"` passes; `grep -c "radius_px=self._mlabel_radius_px(" dash_render.py` prints 12 (the ten `map_*` call sites and the two `_immediate_labels` callers; the call inside `_immediate_labels`, 14418, passes `radius_px=radius_px`).]]></verify>
  <done>Every marker label was placed its marker's radius plus Stata's gap from its point along its clock direction, on every type and in both modes, with mlabsize() in Stata's text units.</done>
</task>

<task type="auto" id="08-08">
  <name>Route text sizes through the resolver</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Rewrite `_textbox_size` (4819-4836) as TR-08.10 defines it (returns a CSS string or None; unknown name → `_dash_style_note(option, raw, "size", "medium")` and medium) and change its five callers to pass the model's current size as the default, the reference, and the option name, writing the returned string unchanged: `_dash_figure_title` (25921-25923), `_dash_style_axis_titles` (25947-25953), `_dash_text_annotations` (26011-26016), `_dash_add_secondary_axes` (23100-23102) and `_dash_apply_z_options` (26129-26137). Route `legend(size())` (21619-21629) and `labsize()` (22836-22844) through the resolver per legend and per axis as TR-08.10 says, replacing the UserWarning with `_dash_style_note`, give `_dash_apply_axis_spec` (22714) the keyword `ref_in=4.0` and pass it from `_dash_apply_axis_options` (23025, `OptionTranslator.size_ref_of(fig)`) and `_dash_add_secondary_axes` (23300). In `_dash_apply_z_options` draw `zlabel(, labsize())` on a ColorBar (take it out of `_bad`, 26150-26152) and keep naming it on a Legend. Warn that `_textbox_size` is CRITICAL and `_dash_apply_axis_spec` and `_dash_apply_z_options` HIGH before editing; edit no other line of these functions.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_size_units.py -q -n0 -p no:cacheprovider` passes in full; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Every title, subtitle, note, caption, axis title, tick label, legend key, marker label and colour-key size was read in Stata's text units in both modes, and the colour bar drew zlabel(, labsize()).</done>
</task>

<task type="auto" id="08-09">
  <name>Make the brushed copies follow the glyph</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Ratification row 27; Evidence E10. Log in the progress output that `_dash_dim_nonselection` is CRITICAL (8 / 1 / 8) and that `_dash_add_glyph`/`_dash_add_pc_glyph` are LOW with served callers the index does not resolve, before editing; re-run `node .gitnexus/run.cjs impact <symbol> --direction upstream --repo .` in the main checkout (never in $WT) if `<scratch>/batch-3-impact.txt` lacks them, and append the result. Add `GlyphMapper._sync_brushed_copies(fig, before=())` as TR-08.16 defines it (a staticmethod, after `_apply_fill_opts`), with a docstring citing Evidence E10 (Bokeh's creation-time copies, the measured rows) and ratification row 27. In `_dash_add_glyph` (28955) and `_dash_add_pc_glyph` (29006) make `_before = frozenset(id(r) for r in fig.renderers)` the first statement and wrap the rest of each body in `try: … finally: GlyphMapper._sync_brushed_copies(fig, _before)`, changing no other line and no return value. In `_dash_dim_nonselection` (29025-29047) apply TR-08.17 (min of `alpha` and the renderer glyph's own plain-number alpha; today's assignment when there is no glyph or no number) and add the docstring paragraph. Do not edit `_apply_marker_opts`' brushed behaviour separately, `_apply_line_opts`, `_apply_fill_opts`, `_apply_colorvar`, `_dash_stale_glyph`, `_dash_copy_redraw_geometry`, `_build_filter_widgets`, `_make_figure_body`, `_build_sources_and_figures`, `_generate_app_source` or either copy-list tuple (TR-08.13: the three module functions are listed already, the method travels with GlyphMapper). Add `GlyphMapper._sync_brushed_copies` to test/function_test_map.py under S08's anchor (TR-08.18).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_brushed_copies.py -q -n0 -p no:cacheprovider` passes in full; `python3 -m pytest test/test_linking.py test/test_layout_tabs.py test/test_help_claims_4.py test/test_served_bs_layout.py test/test_saved_stale_cue.py -q -n 6 -p no:cacheprovider` reports 0 failed; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes; `git -C $WT diff -U0 -- dash_render.py | grep -cE '^[-+][[:space:]]+"_dash_(pc_dispatch|add_pc_glyph|dim_nonselection)"'` prints 0 (no copy-list line moved).]]></verify>
  <done>Every layer's brushed-away and muted copies drew its glyph's own size, symbol, colours, widths and dash at a dimmed opacity never above the glyph's, in both modes and after a served move, with the stale cue and the linked dimming unchanged.</done>
</task>

<task type="auto" id="08-10">
  <name>Measure and flip the unit pins</name>
  <files>test/test_options.py, test/test_scheme_rendered_output.py, test/function_test_map.py</files>
  <action><![CDATA[
    Re-measure the red list on the fixed tree: write the 63-file selection of the prototype (`grep -lE "msize|mlabsize|mlabgap|labsize|size\(|font_size|x_offset|marker_size|translate_msize|_textbox_size|glyph\.size|\.size\b|_markersize_px|MARKER_PX|nonselection|muted_glyph" test/test_*.py`, plus test/test_*scheme*.py, test/test_mode_parity.py, test/test_varlist_expansion.py, test/test_function_test_map.py, test/test_statistical_helpers.py and the five copy-reading files of Evidence E10) to `$S/08-sel.txt` and run it as a file list (`xargs python3 -m pytest -q -n 4 -p no:cacheprovider -rf < "$S/08-sel.txt" > "$S/08-pins.log" 2>&1`; a file list, never `test/` itself). Compare its FAILED nodes with F1-F29 (Evidence E9) and write `$S/08-flips.txt`; a node not in the table is investigated, and is flipped only if it pins the old ladder, offset or pixel string, with a new F-line; a red node that reads a nonselection or muted glyph is a regression of 08-09 (Evidence E10 expects none), fixed in dash_render.py, never flipped. Flip F1, F2 (the constant at 86 and its comment), F3 and F4 in place (F4 renamed `test_markersize_px_anchors_medium_at_4_4pt`, and `SchemeParser._markersize_px` in test/function_test_map.py repointed to it), each with a comment naming WP-30 P1.12a and the twoway value, and a `Flipped:` line in `$S/08-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_options.py test/test_scheme_rendered_output.py test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes; `grep -c '^Flipped:' "$S/08-flips.txt"` prints at least 4.]]></verify>
  <done>The red list was re-measured on the fixed tree and the unit and scheme pins were flipped in place with their reasons.</done>
</task>

<task type="auto" id="08-11">
  <name>Flip the label placement pins</name>
  <files>test/test_help_claims_5.py, test/test_immediate_values.py, test/test_pccapsym_pcarrowi.py</files>
  <action><![CDATA[
    Flip F6-F15 in place with the after-values of Evidence E9: offsets become (radius + gap) along the unit vector (5.6 px by default under s2color), gaps are in Stata units, unknown gaps draw medium with a note, `_mlabel_gap_px`'s table moves `HUGE` to the refused list and `*2` to the read list, and label sizes become `'14pt'`. Rename `test_mlabgap_is_the_pixels_given` to `test_mlabgap_is_in_statas_units` and keep every other name. Each flipped assertion carries a comment naming WP-30 P1.12a and Evidence E5's measurement, and each node a `Flipped:` line in `$S/08-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_5.py test/test_immediate_values.py test/test_pccapsym_pcarrowi.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Every marker-label placement pin asserted twoway's edge-based offset in Stata units.</done>
</task>

<task type="auto" id="08-12">
  <name>Flip the label and series pins</name>
  <files>test/test_marker_label_parity.py, test/test_glyphs.py, test/test_scheme_consumption.py</files>
  <action><![CDATA[
    Flip F16 (`(-4, 0)` becomes `(-5.6, 0)`), F17 (the mlabsize string in points) and F5 (the `{"msize": "12"}` row draws 46.08 px and stcolor's default 4.0) in place, each with a comment naming WP-30 P1.12a and a `Flipped:` line in `$S/08-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_marker_label_parity.py test/test_glyphs.py test/test_scheme_consumption.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The marker-label, label-size and per-series size pins asserted Stata's units.</done>
</task>

<task type="auto" id="08-13">
  <name>Flip the title size pins</name>
  <files>test/test_textbox_no_text.py, test/test_colorvar_forms.py, test/test_axis2_suboptions.py</files>
  <action><![CDATA[
    Flip F18 (`LARGE = dr._textbox_size({'size': 'large'}, None)`, the CSS string `'14pt'`, so every test of the file compares strings as before), F19 (the `_textbox_size` CSS string) and F20 (`"%gpx" % translate_msize("large")` becomes `'14pt'`) in place, each with a comment naming WP-30 P1.12a and twoway's 14 pt, and a `Flipped:` line in `$S/08-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_no_text.py test/test_colorvar_forms.py test/test_axis2_suboptions.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Every title-size pin asserted twoway's point size in both modes.</done>
</task>

<task type="auto" id="08-14">
  <name>Flip the title and legend pins</name>
  <files>test/test_axis_options.py, test/test_colorvar_legend.py, test/test_textbox_grammar.py</files>
  <action><![CDATA[
    Flip F21 (the title size and colour tests assert the size in points), F22 (`legend(size(4))` is `'11.52pt'`) and F23 (`test_every_size_spelling` uses `huge`, because `large` is now the s2color heading itself, BR-08.4) in place, each with a comment naming WP-30 P1.12a and Evidence E4, and a `Flipped:` line in `$S/08-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_axis_options.py test/test_colorvar_legend.py test/test_textbox_grammar.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The title, legend-size and abbreviation pins asserted Stata's text units.</done>
</task>

<task type="auto" id="08-15">
  <name>Flip the medium, validation and digest pins</name>
  <files>test/test_help_claims_2.py, test/test_option_validation.py, test/test_varlist_expansion.py</files>
  <action><![CDATA[
    Flip F24 (in `test_one_note_and_the_schemes_default_in_both_modes`, whose rows come from `_TEXTBOX_STYLE` at test_help_claims_2.py:455-466, the size rows assert `'11pt'` in both modes instead of the plain figure's size, and the docstring says why; the colour rows and `test_a_known_style_is_still_honoured` stay as they are), F25 (row 609 becomes `("scatter", {"msize": "Large"}, "msize")`), F26 (`(0, 5.6)`) and F27 (`"…; using medium."`) in place. Re-derive F28: run `python3 -m pytest test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline -q -n0 -p no:cacheprovider`, copy the reported actual digest into `_SINGLE_Y_BASELINE_SHA256` with the trailing comment `# fd0db4f6 -> <new8>: P1.12a the default marker is 5.87 px` (R10). Add the F24-F28 `Flipped:` lines to `$S/08-flips.txt`, each flipped assertion carrying a comment naming WP-30 P1.12a.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_2.py test/test_option_validation.py test/test_varlist_expansion.py -q -n0 -p no:cacheprovider` passes; `grep -c '^Flipped:' "$S/08-flips.txt"` prints at least 28 (F1-F28; F29 is 08-16's).]]></verify>
  <done>The unknown-size, validation and single-y digest pins matched twoway's medium fallback and the new default marker.</done>
</task>

<task type="auto" id="08-16">
  <name>Fill the truth block, flip ET, extend parity</name>
  <files>test/test_wp30_truth.cscript, test/test_wp29_truth.cscript, test/test_mode_parity.py</files>
  <action><![CDATA[
    Write S08's truth block between its own start and end lines in test/test_wp30_truth.cscript with cases SU-10..SU-17 exactly as "Stata truth / Truth block" specifies, and the `_s08_page`/`_s08_app` helpers directly above S08's header, outside every gate (R1); no brace inside a python block within the gate. In test/test_wp29_truth.cscript flip F29: replace `@15px@` by `@14pt@` in ET-01, ET-04, ET-05, ET-06, ET-07, ET-08 and ET-10 (1109-1243), editing only those cases, with a `//` comment naming WP-30 P1.12a; add the `Flipped:` line. Append S08's six CORPUS cases ("TDD test stubs / Other files") after the last case of `CORPUS` in test/test_mode_parity.py, without touching `ALLOWED` or `_MUST_WARN` (R8). Do not touch any other section's block, the runner or the hygiene pins.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider` passes (including `TestTheWp30TruthScript`); `grep -c "SU-1[0-7]" test/test_wp30_truth.cscript` prints at least 8; `grep -c "@15px@" test/test_wp29_truth.cscript` prints 0; `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider` passes and `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider --co -k S08 | grep -c S08` prints 6.]]></verify>
  <done>S08's truth block compared twoway's live drawing with both modes for eight cases, WP-29's title-size cases expected Stata's 14 pt, and parity held on six new size cases.</done>
</task>

<task type="auto" id="08-17">
  <name>Add area cases and run the cscripts</name>
  <files>test/test_option_validation.cscript</files>
  <action><![CDATA[
    Add `_su_case` and SU-01..SU-08 to test/test_option_validation.cscript as one contiguous run after OV-168 (857-862) and before the CV-nn corpus block (864), as "Stata truth / Area script" specifies, and list them in the script's header comment. Run each changed script through the two-line driver from the worktree: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_option_validation.cscript > "$S/run_test_option_validation.do"` then `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_option_validation.do"`; the same for test_wp29_truth.cscript (with `WP29_ONLY=S03` set) and for test_wp30_truth.cscript as `WP30_ONLY=S08 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_wp30_truth.do"`. Read each log; if `python_exec` was dropped (exit 222, a SKIP), restore it and re-run, since a skip is not a pass.
  ]]></action>
  <verify><![CDATA[`grep -c "SU-0[1-8] PASS" "$S/run_test_option_validation.log"` prints 8 and the log ends `test_option_validation: ALL CHECKS PASSED`; `grep -c "SU-1[0-7] PASS" "$S/run_test_wp30_truth.log"` prints at least 8 with no FAIL; `grep -c "ET-[0-9]* PASS" "$S/run_test_wp29_truth.log"` prints at least 10 with no FAIL.]]></verify>
  <done>dash.ado was shown to accept every new size form, and twoway's live drawing agreed with both modes in the truth block and in WP-29's flipped title cases.</done>
</task>

<task type="auto" id="08-18">
  <name>Rewrite the help on size units</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Edit only these paragraphs (R3): the Units paragraph (3424-3434), which now says that every size dash reads, option or scheme, is a Stata unit of 2.88 point (3.84 pixels) at the four-inch reference, one unit for every class; that numbers, the symbolsize and gsize keywords (case-sensitive), #rs, *# (times the size drawn there otherwise) and #pt/#in/#cm (converted at the scheme's smaller graphsize side; and at xsize()/ysize() if Q1 is answered yes) are read; that the default marker is 5.87 pixels under s2color; that an unknown or wrong-case name draws medium with a note and a negative size nothing; the mlabsize() synopt (2150-2151: a text size in Stata's units); the mlabgap() synopt (2158-2165: a gsize measured from the marker's edge, half_tiny (2 point) by default, also on bar, pcarrow and pcbarrow from half the layer's marker size; a negative gap toward the point; nothing at mlabposition(0); keep the mlg() sentence); the colour-key paragraph (3155-3162: zlabel(, labsize()) is drawn on the colour bar and named on a discrete key); the list at 690-691 (msize(), mlabsize() and mlabgap() take a name, a number, a number with a unit or a *# multiplier); and, in Linking and Brushing (1147-1163), TR-08.18's one sentence on the unselected observations (ratification row 27). Keep every other sentence, and write no number that a test of this section does not pin.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_8.py test/test_help_conformance.py -q -n0 -p no:cacheprovider` passes; `grep -c "about 4 pixels" dash.sthlp` prints 0; `grep -c "2.88" dash.sthlp` is at least 1; `grep -c "never more opaque than they are drawn unselected" dash.sthlp` prints 1.]]></verify>
  <done>The help described Stata's size units, the edge-based label gap and the drawn colour-bar label size as dash now draws them.</done>
</task>

<task type="auto" id="08-19">
  <name>Close P1.12a and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP30_OPEN["P1.12a"]`; close that entry in place (`- [x]`) with the Resolution of Notes ("BUGS.md text"), and delete the `"P1.12a"` key line from `WP30_OPEN`; no other BUGS.md entry is added (ratification row 27: the brushed copies are fixed under P1.12a, P2.49 is not filed). In CHANGELOG.md replace the `<!-- WP-30 P1.12a -->` marker in `### Results that change` with the five Results lines of Notes, and the one in `### Changed behaviour (may need your do-files changed)` with its line, each ending `(WP-30, P1.12a)`; correct 521-523 in place as Notes gives it (R4). Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`; then `git -C $WT merge --no-edit main` (expect `Already up to date.`, else stop and report, E9); then one full run through the queue, `<scratch>/full_suite_queue.sh $WT <scratch>/08-full-1.log`, launched in the background and waited for on its `exit=` line, never relaunched (E1, E6 for the known flaky tests). Stage exactly dash_render.py, dash.sthlp, BUGS.md, CHANGELOG.md, scripts/extract_size_units_truth.do, test/test_size_units.py, test/test_brushed_copies.py, test/function_test_map.py, the 18 flipped test files of Evidence E9 (test_options, test_scheme_rendered_output, test_scheme_consumption, test_help_claims_5, test_immediate_values, test_pccapsym_pcarrowi, test_marker_label_parity, test_glyphs, test_textbox_no_text, test_colorvar_forms, test_axis2_suboptions, test_axis_options, test_colorvar_legend, test_textbox_grammar, test_help_claims_2, test_option_validation, test_varlist_expansion, test_wp29_truth.cscript), test/test_mode_parity.py, test/test_wp30_truth.cscript, test/test_option_validation.cscript, test/test_tracking_documents.py and any extra flip recorded in `$S/08-flips.txt`, plus `git add -f test/fixtures/size_units_truth.json`; check `git diff --cached --name-status` (G6), write the message to `$S/08-msg.txt` per the commit boundary, run G7 on it, confirm `git -C $WT branch --show-current` prints `wp30-s08`, commit with `git commit -F "$S/08-msg.txt"`, run G7 on `git log -1 --format=%B`, and report the sha and message path to the merger.
  ]]></action>
  <verify><![CDATA[`grep -E '^exit=0' <scratch>/08-full-1.log` matches and the log's summary line shows 0 failed; `git log -1 --format=%s` ends `(WP-30 P1.12a)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.12a -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.12a": "' test/test_tracking_documents.py` prints 0; `grep -c 'P2.49' BUGS.md` prints 0; `git log -1 --format=%B | grep -c '^Regression: test/test_brushed_copies.py'` is at least 8; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.12a was closed naming tests that exist, the brushed-copy fix among them with no other entry opened, both CHANGELOG markers carried the measured old and new values, and the section's one green commit on wp30-s08 was ready for the merger.</done>
</task>

## Section completion criteria

- In both modes and after a served filter move, `msize()`, `mlabsize()`, `mlabgap()`, textbox `size()` (title, subtitle, note, caption, axis titles, the second axis's title, the colour key's title), `labsize()` (axes and the colour bar) and `legend(size())` read Stata's numbers, keywords, units and multipliers on the one unit (1 rs = 2.88 pt = 3.84 px), and every fixture probe matches twoway's ratio.
- The default s2color marker is 5.8667 px (stcolor 4.0, economist 9.3335); an explicit keyword equal to the scheme's default draws exactly it under all 26 shipped schemes.
- Marker labels sit (radius + gap) from their point at every clock, on bar, pcarrow, pcbarrow and the immediate types too; the default gap is 2 pt.
- Unknown and wrong-case names draw medium with one note; negative sizes draw nothing in silence.
- (ratification row 27) Every layer's brushed-away and muted copies draw the glyph's own size, symbol, colours, widths and dash, dimmed but never more opaque than the glyph, in both modes, on by() panels and after a served move; `test/test_brushed_copies.py` is green.
- `size_units_truth.json` is new, stamped and staged with `git add -f`; `test_wp30_truth.cscript` SU-10..SU-17, `test_option_validation.cscript` SU-01..SU-08 and `test_wp29_truth.cscript` ET-01..ET-10 print PASS.
- F1-F29 are flipped with `Flipped:` lines; the single-y digest is re-derived with its reason; no test was deleted.
- One green commit `(WP-30 P1.12a)` exists on `wp30-s08` with the failure text, `Regression:`, `Flipped:`, `Fixture:` and `BUGS.md:` lines; BUGS.md `P1.12a` is closed (its Resolution names the brushed-copy fix), no other entry is added, `WP30_OPEN` lost only `P1.12a`, both markers are replaced and CHANGELOG.md:521-523 is corrected.
- Not edited: `_generate_app_source`, `_make_figure_body`, `_build_sources_and_figures`, `_build_filter_widgets`, `_apply_line_opts`, `_apply_fill_opts`, `_apply_colorvar`, `_dash_stale_glyph`, `_dash_copy_redraw_geometry`, the copy lists, any scheme file, `scheme_truth.json`, dash.ado, dash_parse.mata, any runner block or hygiene pin, any tracking document beyond BUGS.md and CHANGELOG.md.

## Notes

### Maintainer question (Q1)

**Q1 — `xsize()`/`ysize()` in the reference length for `#pt`/`#in`/`#cm` (register P1.12.4).** The ruling says absolute units convert at min(xsize or graphsize x, ysize or graphsize y). The scheme's `graphsize` reaches every S08 site (TR-08.6, TR-08.7), but a graph's `xsize()`/`ysize()` reach none of the sites that lack the graph's options (the GlyphMapper appliers, `_dash_apply_legend`, `_dash_apply_axis_spec`, `_dash_apply_z_options`). The one per-figure step every mode runs before them is `apply_to_figure(fig)`, and passing it the graph's options needs one line in `DashRenderer._make_figure_body` (30326) and one generated line in `_generate_app_source` (35203). R12 gives `_make_figure_body` to other sections and `_generate_app_source` to S09 in batch 3. Options:
- **(a)** Grant S08 those two one-line edits as an R12 exception: `apply_to_figure(fig, graph_opts=None)` stamps `min(xsize or gx, ysize or gy)`. A conflict with S09 would be in context only (different lines of the template).
- **(b)** Leave it: absolute units follow the scheme's `graphsize` only (exact for every graph drawn without `xsize()`/`ysize()`), and the `xsize()`/`ysize()` part is filed by S58 as a P2 residual, so P2.13's "4-inch reference" sub-claim stays partly open.

**Review finding (06oct2026).** Option (a) as drafted is incomplete and breaks a batch rule:
- It stamps only the figure. The GlyphMapper sites (`msize()`, `mlabsize()`, `mlabgap()`; TR-08.7) read `self.scheme.size_ref_in` from the one GlyphMapper each renderer shares across its figures: `self.mapper = GlyphMapper(scheme=self.scheme, …)` (dash_render.py:29175) and the served `_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)` (:33479). Making markers follow `xsize()` would also mean passing a per-figure reference through every marker applier call, which is more R12-locked and CRITICAL code than the two lines (a) names.
- It makes S08 a second `_generate_app_source` editor in batch 3 beside S09, which A139 forbids.

**Recommendation: (b).** The maintainer is asked to ratify a narrowed register P1.12.4: "closes P2.13's 4-inch reference for the scheme's `graphsize`; the `xsize()`/`ysize()` half is filed as a P2 row by S58". The help (08-18) then names only the scheme's `graphsize`. If (a) is granted instead, it must cover the GlyphMapper sites too, and it needs its own A139 exception or a later batch whose section already edits `_make_figure_body` and `_generate_app_source`.

**Default if unanswered when batch 3's base is recorded: (b).** Under (a), 08-05 also edits those two lines, TR-08.7's last sentence applies, and `TestAbsoluteUnitsFollowTheSchemesReference` gains a `xsize(8) ysize(8)` case (economist `size(14pt)` then 7 pt against `large`'s 14 pt, from twoway's 28.01 pt `large` at 8 × 8 in, research critic C1).

### Text for the closing task (08-19)

**BUGS.md, P1.12a** (closed in place, `- [x]`):

`- Resolution: Fixed <ddmonyyyy> (WP-30, P1.12a). Marker, text and label-gap sizes are read in Stata's units, one unit for every class (2.88 point, 3.84 pixels, at the four-inch reference): OptionTranslator.resolve_size reads numbers, Stata's symbolsize and gsize keywords (case-sensitive), #rs, *# and #pt, #in and #cm (converted at the scheme's smaller graphsize side) for msize() (GlyphMapper._apply_marker_opts, map_scatteri), mlabsize() and mlabgap() (_apply_mlabel_opts, the gap now measured from the marker's edge, half_tiny by default, at all eleven call sites), textbox size() (_textbox_size and its five callers), labsize() (_dash_apply_axis_spec, and zlabel() on the colour bar) and legend(size()) (_dash_apply_legend), in the saved renderer and the served app alike; SchemeParser draws its markers on the same unit (the default s2color marker is 5.87 pixels, was 8), stamps each figure with its reference length and reads gsize label_gap. An unknown or wrong-case name draws the class's medium with one note, and a negative size draws nothing, silently, as twoway does. The brushed-away (nonselection) and muted copies Bokeh makes when a renderer is created now follow every applier: GlyphMapper._sync_brushed_copies, run by _dash_add_glyph and _dash_add_pc_glyph after each layer in both modes, gives them the glyph's own size, symbol, colours, widths and dash, and _dash_dim_nonselection never makes a copy more opaque than its glyph (they kept the scheme's default marker; register P1.12.6, research N1). Pinned by test/test_size_units.py::TestResolveSize::test_a_number_is_statas_relative_unit, test/test_size_units.py::TestExplicitMarkerSizes::test_medium_equals_the_default, test/test_size_units.py::TestExplicitTextSizes::test_title_large_is_the_heading, test/test_size_units.py::TestMarkerLabelsFromTheMarkerEdge::test_the_gap_is_from_the_edge, test/test_size_units.py::TestStataRatios::test_sizes, test/test_size_units.py::TestBothModesAfterAMove::test_sizes_survive_a_move, test/test_brushed_copies.py::TestBrushedCopiesFollowTheGlyph::test_marker_options_reach_the_copies, test/test_brushed_copies.py::TestBrushedCopiesFollowTheGlyph::test_a_copy_is_never_more_opaque_than_the_glyph, test/test_brushed_copies.py::TestBrushedCopiesFollowTheGlyph::test_the_copies_hold_after_a_move, test/test_wp30_truth.cscript SU-10, test/test_option_validation.cscript SU-01; fixture test/fixtures/size_units_truth.json. Residual, deferred (WP-30): line widths are P1.12b (section 13); a bar's brushed copies keep the build's width after a filter move until section 14[; xsize() and ysize() do not change the reference length of absolute units (Q1)].`

(The bracketed clause is written only if Q1 is answered (b) or left unanswered.)

**BUGS.md, P2.49:** not filed (ratification row 27, 06oct2026). The brushed copies are fixed and closed under P1.12a above, and no other entry is appended (index A146).

**CHANGELOG.md**, `<!-- WP-30 P1.12a -->` in `### Results that change` replaced by:

```
- `dash scatter mpg weight` draws its markers at Stata's size, on one unit for every class (1 Stata unit = 2.88pt = 3.84px): the default marker is 5.87px under s2color (was 8), 4.0 under stcolor (was 5.45) and 9.33 under economist (was 12.73); `msize(medium)` is 5.87px (was 11) and `msize(large)` 9.33 (was 15); `msize(4pt)`, `msize(*2)` and `msize(vhuge)` draw 5.33, 11.73 and 21.33px where they were noted and drawn at the default. (WP-30, P1.12a)
- Text sizes are Stata's: `title("T", size(large))` is 14pt (was 15px), `size(5)` 14.4pt (was 5px), `ylabel(, labsize(medium))` and `mlabsize(medium)` 11pt (were 11px), `legend(size(large))` 14pt (was 15px). `#pt`, `#in`, `#cm`, `#rs`, `*#` and every gsize keyword (`vhuge`, `tenth`, `relative3`, `10-pt`, ...) are drawn where they were noted, `zlabel(, labsize())` is drawn on the colour bar where it was named, and under stcolor and economist `size(14pt)` keeps twoway's proportion to the scheme's sizes (12.44pt and 25.45pt). (WP-30, P1.12a)
- Marker labels sit where twoway puts them, the marker's radius plus the gap from their point: 5.6px from the point by default under s2color (was 4px), 22.1px with `mlabgap(5)` (was 9px); bar, pcarrow and pcbarrow labels sit half the layer's marker size from their point. (WP-30, P1.12a)
- An unknown or wrong-case size name draws the class's medium with the note, as twoway does: `title("T", size(abc))` is 11pt (was the scheme's 14pt) and `msize(HUGE)` 5.87px (was 24px); a negative size draws nothing, silently (`msize(-1)` drew 1px). (WP-30, P1.12a)
- Points left out of a box or lasso selection keep their own look: with `msize(large) mcolor(red)` the unselected points are drawn large and red, faded (they were drawn at the scheme's default size and colour), a hollow `msymbol(Oh)` stays hollow (it was filled), and `lwidth()`, `lcolor()`, `fcolor()` and `colorvar()` reach them too, in the saved page and the served app. (WP-30, P1.12a)
```

and in `### Changed behaviour (may need your do-files changed)` by:

```
- A number in `msize()`, `mlabsize()`, `mlabgap()`, `size()`, `labsize()` or `legend(size())` is in Stata's relative units (1 = 3.84px), not pixels: `msize(10)` draws 38.4px where it drew 10px, and `mlabgap(5)` leaves 19.2px of gap where it left 5. A do-file written for dash's pixel reading needs its sizes divided by 3.84 or written as keywords. (WP-30, P1.12a)
```

**CHANGELOG.md:521-523** (WP-15's line, corrected in place, R4; research N2):

```
- Option values are validated as twoway validates them. A bad value such as
  `lwidth(-1)` or `yaxis(3)` is r(198) or r(111), naming the option. A style
  name dash cannot draw, such as `msize(abc)`, is noted and drawn, as in twoway (WP-15).
```

### Traps for the executor

- **Two kinds of "default".** `*#` multiplies what would be drawn at that site (the glyph's construction size, the model's current font size, the scheme's label gap); an unknown name draws the class's medium, which is not the scheme's default under stcolor (E4: `msize(abc)` 1.52778, not stcolor's small). Keep both rules separate.
- **Signs.** `resolve_size` never floors. A glyph size and a CSS size floor at 0; the label radius and the gap keep their sign (E5: `msize(-1) mlabgap(0)` puts the label at -0.5 units).
- **Case.** Option names and units are case-sensitive (`HUGE`, `4PT` are unknown). `_markersize_px` keeps lower-casing scheme values as it does today; scheme files are lower case.
- **`glyph.size` may be a field spec** on some mappers; `_apply_marker_opts` multiplies only a plain number.
- **The marker-label default size is 10px until S33** (batch 11). `mlabsize(*2)` doubles dash's 10px (15pt; twoway 16pt from its 8pt). The ratio tests hold; S08 writes no absolute `*#` label-size expectation.
- **A blank inside `msize()`, `mlabsize()` or `mlabgap()`** is a stylelist separator in twoway (E5); S11 (batch 4) splits it. S08 writes no test of `msize(4 pt)`.
- **`_SIZE_MAP` stays.** The served header emits it (34117); deleting it breaks every served build. No size path reads it after S08 (`TestResolveSize::test_names_are_case_sensitive` asserts that `HUGE`, which `_SIZE_MAP`'s lower-cased lookup read as 24 px, now raises).
- **`_textbox_size` returns a CSS string now.** Its five callers write it unchanged; a later section adding a caller passes the model's current size as `default`.
- **`css_pt` writes two decimals**, so an explicit keyword equals the scheme's `_gsize` string (`small` 7.99776 → `"8pt"`); never `:g` (Bokeh's FontSize validator rejects an exponent; `_gsize`'s comment at 6558-6564).
- **The stamp is Python-only.** `fig._dash_size_ref_in` is set in `apply_to_figure`; a figure that never passes through it reads 4.0. Never serialise it, and never read it from page JSON.
- **Served order differs** (E2): the served app adds the second axis before the title, the saved renderer after; both read the reference from the stamp, which `apply_to_figure` sets first in both.
- **Fixture provenance.** The extractor reads `DASH_REPO`; run it with `DASH_REPO=$WT`. Never hand-patch the fixture (R7).
- **python_exec hazard.** Several concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; a cscript then exits 222. A skip is not a pass: restore and re-run.
- **Notes and their needles.** Count notes through S06's helpers (A150); `_dash_style_note` is not edited, so its text is `dash: <opt>(<value>) is not a recognised size; using medium.` before S06's `(note: …)` framing.
- **The red list is re-measured** (08-10); a node outside F1-F29 is investigated before it is flipped (R9).
- **The brushed copies (ratification row 27).** Sync after the appliers, never inside one: `_apply_line_opts` is S13's (R12), and a sync inside `_apply_marker_opts` alone would miss lines, fills and colorvar (critic C4). Alphas take the minimum, never the glyph's value: the copies must stay faint. Do not touch `muted_glyph` after the build: the saved stale cue replaces it later (:32328) and its tests pin that rebuild.

### Shared files and merge rules

- **R1:** S08's truth block between its own start and end lines, helpers directly above its header; SU-01..SU-08 as one run at the end of `test_option_validation.cscript`'s last case block; WP-29's ET cases edited in place only.
- **R2:** no copy-list entry (R2 row S08: `_textbox_size` at 33360 changes in place; `_dash_add_glyph`, `_dash_add_pc_glyph` (33131-33132) and `_dash_dim_nonselection` (33329) change in place; `GlyphMapper._sync_brushed_copies` travels with its class; `resolve_size`, the `*#` parser and the helpers are OptionTranslator methods; `_mlabel_gap_px` and `_mlabel_radius_px` GlyphMapper methods); `test/function_test_map.py` keys under S08's anchor only (A148).
- **R3:** dash.sthlp 690-691 (Differences), 2150-2165 (Marker Label Options, S08's in the R3 table), 3155-3162 (Mapping a Variable to Colour; S17 and S33 are in other batches) and 3424-3434 (Units; S07 edits 3300, 3501, 3505 and 3573 of the same title in this batch); and one sentence in Linking and Brushing (1147-1163; ratification row 27; S14 edits that title's spacing sentences in batch 5).
- **R4:** the two P1.12a markers, replaced in place; CHANGELOG.md:521-523 corrected in place (index R4's named correction).
- **R5:** BUGS.md `P1.12a` in place, nothing appended (ratification row 27: P2.49 is not filed); only the `P1.12a` line of `WP30_OPEN` deleted.
- **R7:** `size_units_truth.json` new, stamped, `git add -f`; no scheme file or `scheme_truth.json` touched.
- **R8:** six CORPUS cases appended; `ALLOWED`/`_MUST_WARN` untouched.
- **R9:** F1-F29 flipped with `Flipped:` lines.
- **R10:** `_SINGLE_Y_BASELINE_SHA256` re-derived here and by the merger after S08 and S09 land.
- **R12:** S08 is batch 3's only editor of `_apply_marker_opts`, `_apply_mlabel_opts`, `_dash_add_glyph`, `_dash_add_pc_glyph` and `_dash_dim_nonselection`, and edits none of the template, figure-body, sources-and-figures or filter-widget functions.

### For later sections

- **S13** adds `"line"` to `_SIZE_KINDS`, a `_LWIDTH_RS` ladder and its own floor (0.3 pt) inside `resolve_size`'s kind table, and calls it from `translate_lwidth` and the line sites; it keeps `resolve_size`'s signature and grammar order.
- **S30** reads colour multipliers through `OptionTranslator.stata_number` (and `size_multiplier` for a bare `*#`), not a second number grammar.
- **S14, S15, S31, S47, S48, S56** pass the size already drawn at their site as `default_pt` and the reference from `size_ref_of(fig)` or `scheme.size_ref_in`.
- **S33** sets the default marker-label size from the scheme's label key; `_apply_mlabel_opts`'s `mlabsize` default is then that size, and `*#` follows it with no S08 change.
- **S24** applies its 0.707 `sm*` factor after `msize()` in `_apply_marker_opts`; the label radius (`_mlabel_radius_px`) does not include it unless S24 measures that twoway's does.
- **Every later applier edit (S13, S14, S16, S17, S24, S30, S32, S33, S35, S43; ratification row 27).** A glyph property written inside a layer's mapper reaches its brushed copies through `GlyphMapper._sync_brushed_copies` with no further code, so no later section writes `nonselection_glyph` or `muted_glyph` itself for a property the sync copies. A property written after the dispatch returns (outside `_dash_add_glyph`/`_dash_add_pc_glyph`) calls `GlyphMapper._sync_brushed_copies(fig, <ids before>)` itself, or the section adds a case to `test/test_brushed_copies.py`. Each of these sections runs that file in its pin measurement. S16's nonselection fill recolouring becomes redundant but stays harmless: the sync writes the same value, and S16's `fill_alpha is not the glyph's` holds, since min(0.1, 1.0) = 0.1. S24's hollow marker now dims to 0 fill, not `_NONSELECTION_ALPHA`. S30's reference to `TestBrushedCopiesKeepCreationValues` becomes `test/test_brushed_copies.py`, which S30 keeps green.
- **S14** deletes `_dash_copy_redraw_geometry` and the saved width script (A61). It adds `test_brushed_copies.py::TestBrushedCopiesFollowTheGlyph::test_a_bar_copy_keeps_its_width_after_a_move[mode]` and removes P1.12a's residual clause from the CHANGELOG/help if one was written.

### Notes for the closeout (A145; S58 writes them)

- **GAPS2 D2:** D2-a, D2-b, D2-d and D2-e are closed for the marker, text and gap kinds by S08's commit; D2-c and the line parts by S13, which records D2 closed. Tracked line after S08: `Partly closed in WP-30 (P1.12a), BUGS.md "<P1.12a title>", commit <sha>; the line widths are P1.12b`.
- **GAPS2 B9:** `Closed in WP-30, BUGS.md "<P1.12a title>", commit <sha>` (explicit text `size()` in Stata's units).
- **DROPIN-REMAINING.md P1.12:** part a closed by S08's commit; part b by S13's.
- **ROADMAP:** the register's P2.49 row is written withdrawn (ratification row 27: fixed by S08 under P1.12a, commit <sha>; no BUGS.md entry). P2.13's "4-inch reference" sub-claim: closed for the scheme's `graphsize` by S08 (P1.12.4); its `xsize()`/`ysize()` part closed too if Q1 is answered (a), else kept open. ROADMAP.md:2048-2050 (the `_LWIDTH_MAP` ratios) is S13's.
- **P3 hygiene rows** (unless a later section removed them): the served header's dead `_SIZE_MAP` global and `OptionTranslator._SIZE_MAP` itself (research N3; needs `_generate_app_source`); `SchemeParser._GSIZE_PT`'s `third_tiny` 1 pt (Stata 1.333 pt) and its dash-only `ehuge` (Stata's gsize class has none), both scheme-side readings S08 leaves unchanged.
- **TWOWAY_COVERAGE_AUDIT.md** rows 112-114, 136 and 140 (`msize`, `lwidth`, `labsize` "implemented"): tag "in Stata's units since WP-30 P1.12a/P1.12b".
- **AGENTS.md invariant:** every size an option gives goes through `OptionTranslator.resolve_size` on one unit (1 rs = 2.88 pt = 3.84 px); text sizes are written by `css_pt`; a figure's reference length is stamped by `SchemeParser.apply_to_figure`; a layer's brushed copies are synced from its glyph by `GlyphMapper._sync_brushed_copies` at the end of `_dash_add_glyph`/`_dash_add_pc_glyph` (ratification row 27).

### Line numbers

Every anchor is `c96facd`'s. S07 lands before S08 in batch 3 and edits `SchemeParser._BUILTIN_NAMES` (5704) and the scheme files, not the size code; if its landing moves lines, the symbols named here are authoritative.

### Notes for the orchestrator (ratification 06oct2026)

- **section-01: no change needed.** Its amendment line 19 and S58.1 (:437) already expect 3 open entries after WP-30 with P2.49 not filed. Appendix B's P1.12a entry is unchanged: it names the marker, text and gap part, and the brushed copies are recorded only in P1.12a's closing Resolution and the commit body. `WP30_OPEN` and the markers are unchanged.
- **index.md** (not edited here):
  - "Batch 3" step 3.0's expected HIGH/CRITICAL list gains `_dash_dim_nonselection` (CRITICAL, 8 / 1 / 8), plus `_dash_add_glyph` and `_dash_add_pc_glyph` (LOW, with served template callers the index does not resolve; confirmed by grep at 34967-35002).
  - R3's S08 row gains "Linking and Brushing (one sentence, 1147-1163)".
  - R2's S08 row may add "`_dash_add_glyph`, `_dash_add_pc_glyph`, `_dash_dim_nonselection` change in place; `GlyphMapper._sync_brushed_copies` travels with its class". There is still no list change.
  - Section table row 08 is unchanged (yellow, M), and the task count is now 19.
  - A146, IR-15 and the open-entry counts (:362-364) already match.
- **Other sections that still describe P2.49 as open** (edit by the orchestrator or their owners; the wording is in "For later sections" above):
  - section-13 :24 and :460;
  - section-16 :11, :20, :201 (`_dash_dim_nonselection` "sets only its alphas" now takes the min against the glyph), :413, :769 and :777;
  - section-24 :615 (a brushed-away hollow marker dims to 0 fill, not `_NONSELECTION_ALPHA`);
  - section-30 :946 (`TestBrushedCopiesKeepCreationValues` is never written; read `test/test_brushed_copies.py`, which must stay green).
- **section-14:** add the bar-after-a-move brushed-copy case named in "For later sections" when it deletes `_dash_copy_redraw_geometry` (A61).
- **manifest.json:** S08's scope already lists N1 ("explicit msize/mcolor/mlwidth reach the nonselection and muted glyphs (N1)"). No change.
