# Section 15: Scheme chrome: titles, ticks, grid, economist axes (P1.2 part a, M1)

> Part of: WP-30 · Items: P1.2 part a (entry `P1.2a`) · Risk: yellow · Batch: 5 · Depends on: 07, 08 · Blocks: 16, 21, 28, 29, 31, 53, 56 · Tasks: 19, 1 commit · Case prefix: LK

## Review amendments

- Fixed (blocker, A139): S13 and S15 both edited `SchemeParser._init_properties` in batch 5. S15 is now its one editor and takes S13's two pixel-literal width defaults (TR-15.3, 15-06; S13 D-13g). The three `TestHostileSchemeValues` pins they feed are added to E11 and flipped in 15-12 as rung expressions. Those expressions hold at S15's base, where they are not red, and on the merged tree.
- Fixed (major): TR-15.2's regeneration check would fail. The stale `linewidth` `dash_rule` sentence of `_meta.units` (extract_scheme_truth.py:2140-2144) is rewritten to S13's rule (TR-15.1, as S13's Notes ask), and the check exempts that key.
- Fixed (minor): the P1.2.7 "open question" is resolved by the binding register (the minor ticks are S21's). The manifest's wording is recorded in g03.md as a consistency fix.
- Fixed (minor): the Decisions line claimed that `test_default_look.py`/`look_truth.json` were left to S16. S16 creates neither, so the line now names each section's own files. The PLAN.md row is recorded in g03.md.
- Fixed (minor): the S13 merge note now says that `_init_properties`/`_FALLBACK_PROPS` have one batch-5 editor, and how the merger keeps the adjacent parametrize rows.
- Rejected: "15-05 lists 28 files (rule: 1-3 per task)". The 26 scheme files and `scheme_truth.json` are one generated set written by one command (A152, R7), as every regenerator's task is. Its one hand edit is the test_help_claims_8.py flip.
- Checked: the anchors (`apply_to_figure` 7420-7424, `_DASH_TEXTBOX_DEFAULTS` 25962, `_dash_finish_secondary_axes` 23214, copy-list anchor 33372, test_server.py:4001, test_help_claims_8.py:1112) match HEAD. Neither the template nor `_make_figure_body` is edited, so S14 stays batch 5's one template editor. The truth block (helpers above the S01 header, `_w30_done`, `` `w30_work' ``), the BUGS title, the one Results marker and the map anchor match section-01. S15 regenerates last in batch 5 (A152).
- (cross-file pass) E11 and 15-18: `test_help_claims_8.py::TestTheShippedFiles::test_80_to_140_directives` (s2gmanual 139 at `c96facd`, measured) added as a pin S15's regeneration turns red; 15-05 records the 26 counts and excludes it from its `-k`; 15-18 (now dash.sthlp and the test) flips it in place with the "80 to 140 directives" help sentence to the measured bounds, with a `Flipped:` line (g04).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:67-76 (P1.2) reads: "The title is bold and left-aligned (Stata centres it and does not bold it). Axis titles are italic. Subtitle, note and caption sit at x=0. Bokeh minor ticks are drawn and tick geometry is Bokeh's. s2color's vertical y tick labels are missing, as is stcolor's dashed grid. s1rcolor's ticks are invisible (black on black), and economist's y axis is wrong." GAPS2-D17 says `apply_to_figure` "sets only the title's colour and size, so every scheme keeps Bokeh's bold, left-aligned Title and italic axis labels"; GAPS2-D12 names three directives, `anglestyle vertical_tick vertical`, `linepattern major_grid dash` and `color tick white`, and says "None of these is in the shipped files"; GAPS2-D16 says "dash keeps Bokeh's defaults under every scheme: `major_tick_in` 2, `major_tick_out` 6 … economist's y axis on the left with a black line and ticks".

Measured at `c96facd`, the same in the saved page and the served app (research p1-02 §1, rows a-h, `probe_dash.py`, both modes):
- the title is `align=left font_style=bold` under s2color, stcolor, s1rcolor and economist (Bokeh's `Title` defaults; the saved page serialises no `align`);
- axis titles are `italic` (Bokeh's `axis_label_text_font_style`);
- subtitle, note and caption are `Label(x=0, x_units="screen")`, drawn at the frame's left edge (headless Chrome: frame left 52, every text at `sx=52`);
- every axis has `major_tick_in=2 major_tick_out=6` and black minor ticks;
- s2color's y labels are `horizontal`; stcolor's y grid is solid `#f0f0f0`; s1rcolor's ticks are `#000000` on a `#000000` region;
- economist's y axis is in `fig.left` with a black line and ticks.

twoway draws, measured again for this section (probe `p1.do`, StataNow 19.5, quoted under Evidence E8): s2color's `TTL` and `SUB` `text-anchor="middle"` at the plot-region centre, `NTE` and `CAP` at the plot region's left, no `font-weight` or `font-style` on any title; y labels `rotate(-90)`; ticks 1.388 Stata units long, outside, `#000000`, 0.2 units wide; s1rcolor's ticks `#FFFFFF`; economist's title, subtitle and caption anchored left, its note anchored right in the top band, its y labels right of the plot with no y line or ticks, its x ticks inside; under economist a `yaxis(2)` axis sits on the left with its ticks.

**After this section**, in both modes and before and after any filter move, every graph is drawn with its scheme's chrome: a centred, unbolded title (economist: left); upright axis titles; subtitle, note and caption placed by the scheme's clock position and justification as Bokeh `Title` rows (economist's note in the title's band, as twoway draws it); ticks of the scheme's length in Stata units, on its side, in its colour and width; the scheme's tick-label angle (s2color's vertical y labels); the scheme's grid pattern (stcolor's dashed grid); economist's axis sides, lines and ticks, axis 2 included. The 26 shipped scheme files and `test/fixtures/scheme_truth.json` carry the new keys with provenance, plus `system naturally_white` and the `p#bar`/`p#area` intensity chains that S16 and S30 consume.

**Why one section.** These are P1.2's chrome sub-claims a-h (research approach parts A-D and F); the intensity sub-claims i-j are S16's (register P1.2.4, A138). They share one code path: `SchemeParser` reads the keys, `apply_to_figure`/`apply_to_axis` apply them, `_dash_text_annotations` places the text boxes, and both modes call the same three (`_make_figure_body` at dash_render.py:30326/30385/30400, the generated `make_document` at :35203/35206/35261). `_make_figure_body` is not edited. S15 is batch 5's scheme regenerator (A152) and lands last in the batch.

**Decisions applied.**
- M1: the scheme's look, with a CHANGELOG "Results that change" line. Register P1.2.1: s2color's y labels go vertical, `ylabel(, angle(0))` is the escape, and `test_server.py:4001` is flipped. P1.2.3: no option to keep the old look. P1.2.6: economist's note sits in the title band. P1.2.9: the dashboard's own `.db-title` DOM header is unchanged.
- P1.2.7 (binding): **P1.3 (S21) owns the minor-tick bullet** and `test_help_claims_8.py`'s BasicTicker/minor-tick flips; S15 owns the extractor and regenerates first. So S15 styles the minor ticks Bokeh still draws (the scheme's `color minortick`, and none on an axis whose style draws no ticks) and does not remove them; S21's FixedTicker removes them on default axes in batch 7. The manifest's S15 scope also says "no Bokeh minor ticks"; this section follows the register (resolved in Notes).
- P1.2.8: a user scheme's `intensity bar`/`intensity area` stop being read in S16, not here. S15 keeps writing the shipped `intensity bar`/`intensity area` lines, because today's bars and areas read them.
- M5: no new refusal. A scheme value dash cannot use keeps today's rule for scheme files (one note, then the default), as `_bounded_int` and `_init_note_textbox` do. M6: valid keys print nothing.

**Test order and commit rule (rule 7, D1).** One cycle, one commit, subject ending `(WP-30 P1.2a)`.
- **15-01** writes the regression module `test/test_scheme_chrome.py` and runs it on the unmodified tree, saving `<scratch>/15-P1.2a-failure.txt`. It never commits.
- **15-02 to 15-05** add the SVG reader, twoway's fixture, the extractor's keys and the regenerated files. Each new table test is run red-first on the unmodified renderer, and its red lines are appended to the failure file.
- **15-06 to 15-09** make the fix. **15-10 to 15-15** extend the parity profile and flip every pinned test in place. **15-16 and 15-17** add the browser check and the `LK` truth block. **15-18** writes the help.
- **15-19** closes the entry and makes the one commit after one full run through the queue.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every default dashboard's chrome changes, through helpers both modes already share

**Why yellow.** Every page changes visibly (M1, RK-4), about 20 pinned tests move from `Label` to `Title`, and the shared copy list (`_glyph_layer_lines`, HIGH) gains a name. The truth is measured and exact, and one code path serves both modes.

**Risk factors.**
1. A `Title` is a side-panel row, and BokehJS draws a Title on a left or right panel vertically (`TitleView._get_position`, bokeh.js:27351ff; research critic correction 3). Mitigation: `_dash_textbox_place` never returns a left or right side (TR-15.7).
2. Economist's note must share the title's row, which a second `Title` cannot do. Mitigation: a `Label` placed by Bokeh `Node` coordinates on the title's row (E9, measured in headless Chrome on bokeh 3.9.0; `Node` is also in bokeh 3.8.0, Stata's Python).
3. Pinned tests the research missed. Mitigation: 15-15 runs every test file that names `Label`, `Title`, an axis side or a tick property, and the full run in 15-19 is the backstop. A red node found outside the listed files stops the section for a plan amendment (R12).
4. Order differences between the modes (the served app adds the second axis before the title options, the saved renderer after; E4). Mitigation: every new setting is made in `apply_to_figure`/`apply_to_axis`, which run first in both modes, and the in-band note is inserted at index 0 of `fig.center` in both.
5. Batch partners in the same class (`SchemeParser`: S13 edits `_lwidth`). Mitigation: S15 edits other methods and appends new ones; S13 lands first (R12, merge order).

**Mitigation, overall.** The fixture `chrome_truth.json` holds twoway's chrome for all 26 schemes, and `TestEveryShippedSchemeDrawsItsChrome` compares both modes against it, scheme by scheme. The parity profile gains the new fields, so all of `test_mode_parity.py`'s CORPUS compares them across the modes.

## Dependencies

- **Depends on:** S07 (batch 3: the 26 scheme files, the extractor's 26-name `SCHEMES`, `_BUILTIN_NAMES` at 26) and S08 (batch 3: `OptionTranslator.resolve_size(value, kind, default_pt, ref_in)`, `PX_PER_PT`, `SchemeParser.size_ref_in`). S01's entry `P1.2a`, its `WP30_OPEN` key, its `<!-- WP-30 P1.2a -->` marker in `### Results that change`, the S15 stub block and the S15 map anchors are prerequisites.
- **Blocks:** S16 (reads `naturally_white`, `p_bar_intensity`, `p_area_intensity`), S21 (extends these axes; removes minor ticks), S28 (centred panel titles), S29 (font style only where SMCL asks), S31 (axis sub-options over these defaults; `axis_side` for `alt`), S53 (by() edge axes), S56 (`_dash_textbox_place` for `text()` placement).
- **Parallel batch (5):** S13 (line-width ladder) and S14 (bar widths and caps). Merge order S13, S14, S15.
- **Can run with them because** S15 edits none of S13's or S14's functions (Boundaries), its tick widths go through `SchemeParser._lwidth`, which S13 rewrites, so S13's ladder applies on merge, and S15 is the batch's one regenerator (A152, R7).

## Evidence

Anchors are at `c96facd`. The worktree is cut from `batch-5-base.txt`, so the executor re-finds each by its quoted text.

**E1. The scheme sets only colours and sizes** (dash_render.py:7417-7440, `SchemeParser.apply_to_figure`/`apply_to_axis`):
```python
        if fig.title is not None:
            fig.title.text_color = self.title_color
            fig.title.text_font_size = self.heading_font_size

        for axis in list(fig.xaxis) + list(fig.yaxis):
            self.apply_to_axis(axis)

    def apply_to_axis(self, axis: Any) -> None:
        ...
        axis.axis_line_color = self.axis_line_color
        axis.axis_line_width = self.axis_line_width
        axis.axis_label_text_font_size = self.axis_title_font_size
        axis.major_label_text_font_size = self.tick_label_font_size
        axis.axis_label_text_color = self.axis_title_color
        axis.major_label_text_color = self.tick_label_color
```
No `align`, `text_font_style`, `axis_label_text_font_style`, tick property, `major_label_orientation`, `grid_line_dash` or axis side is set anywhere in the file (`grep -n 'major_tick_in\|major_tick_out\|grid_line_dash\|axis_label_text_font_style' dash_render.py` finds only the xtick path, E5). The grid loop (:7401-7414) sets grid colour and width per axis.

**E2. The text boxes are screen-unit Labels at x=0** (`_DASH_TEXTBOX_DEFAULTS` :25962-25966; `_dash_text_annotations` :25969-26018):
```python
_DASH_TEXTBOX_DEFAULTS = {
    "note":     {"size": 11.0, "color": "#555555", "y": 2.0, "side": "below"},
    "caption":  {"size": 12.0, "color": "#555555", "y": 2.0, "side": "below"},
    "subtitle": {"size": 13.0, "color": "#444444", "y": 0.0, "side": "above"},
}
...
        fig.add_layout(Label(
            x=0, y=d["y"], x_units="screen", y_units="screen", text=text,
            text_font_size=(f"{px:g}px" if px is not None else size_default),
            text_color=colour if colour is not None else color_default,
            background_fill_color=fill,
        ), d["side"])
```
`_DASH_TEXTBOX_DEFAULTS` is read only here (grep). It is in the constants tuple (:32934), so editing its value needs no copy-list change. `_dash_move_legend` (:21340-21375) inserts a legend after the side panel's axes and before everything else, by type, so it already keeps the legend nearest the plot whether the boxes are Labels or Titles.

**E3. Second axes hard-code their side** (`_dash_add_secondary_axes` :23073-23106; `_dash_finish_secondary_axes` :23208-23216):
```python
    for axis_key, var_key, rng_attr, name, side, kw in (
            ("yaxis", "yvar", "extra_y_ranges", "y2", "right", "y_range_name"),
            ("xaxis", "xvar", "extra_x_ranges", "x2", "above", "x_range_name")):
        ...
        if scheme is not None:
            scheme.apply_to_axis(ax)
        ...
        fig.add_layout(ax, side)
...
    for rng_attr, name, side, kw, dim, axis_key in (
            ("extra_y_ranges", "y2", "right", "y_range_name", 1, "yaxis"),
            ("extra_x_ranges", "x2", "above", "x_range_name", 0, "xaxis")):
        rng = getattr(fig, rng_attr).get(name)
        ...
        axes = [a for a in getattr(fig, side)
                if isinstance(a, (LinearAxis, LogAxis))
                and getattr(a, kw, None) == name]
```
An axis 2 put on the left would not be found here, so `ylabel2()`/`yscale2()` would reach no axis. The count-tick reader (:23363-23369) already walks both sides of each dimension. Bokeh's `fig.yaxis` is `left + right`, so it finds a moved axis 1.

**E4. Call order in the two modes.** Saved (`DashRenderer._make_figure_body`): `self.scheme.apply_to_figure(fig)` :30326, `_dash_figure_title` :30329, `_dash_style_axis_titles` :30330, region colours, `_dash_add_secondary_axes` :30385, `_dash_reference_lines`, `_dash_text_annotations` :30400, `_dash_apply_axis_options` :30405, the plot loop, `_dash_finish_secondary_axes` :30660. Served (generated by `ServerAppBuilder._generate_app_source`): `_DASH_SCHEME.apply_to_figure(fig)` :35203, `_dash_add_secondary_axes` :35206, `_dash_figure_title` :35211, region colours, `_dash_text_annotations` :35261, `_dash_reference_lines` :35263, `_dash_apply_axis_options` :35268, `_dash_finish_secondary_axes` :35417. In both, the scheme runs first and `_dash_apply_axis_options` after it, so an explicit `angle()` or `grid` wins. The references (Spans in `fig.center`) are added before the text boxes when saved and after them when served. That is why the in-band note goes to index 0 of `fig.center` (TR-15.8). The served scheme is rebuilt from `_SCHEME_PROPS` through `_init_properties` (:33446-33458), so new attributes need no copy-list entry.

**E5. The xtick path copies the major tick to the minor tick** (:22949-22957):
```python
        # A tick-only position is a major tick without its label: the same
        # length and stroke (measured in Stata, labelled or not).
        ax.minor_tick_in = ax.major_tick_in
        ax.minor_tick_out = ax.major_tick_out
        ax.minor_tick_line_color = ax.major_tick_line_color
        ax.minor_tick_line_width = ax.major_tick_line_width
```
It runs after the scheme, so a tick-only position takes the scheme's geometry with no edit. `_dash_apply_axis_spec` sets `major_label_orientation` only when `angle()` is given (:22846-22847).

**E6. The scheme files carry none of the keys.** `grep -l '^ *anglestyle\|^tickposition\|^color tick \|^linepattern major_grid\|^clockdir title_position\|^system' dash-*.scheme` finds no file. The extractor (scripts/extract_scheme_truth.py, 2234 lines): `SchemeResolver` :146 (`style(cls, name)` reads `style/<cls>-<name>.style`), `axis_grid_switches` :545, `resolve_intensity` :569, `resolve_linepattern` :588, `extract` :603 (output dict :1102-1275, `out.update(note_truth())` :1279), `expected_directives` :1371 (last group `], note_items)` :1645, de-duplication :1647), `update_scheme_file` :1852, `SCHEMES` :1957, `main` :1966 (`--out`, `--schemes`, `--schemes-dir`, `--stata-base`). Shipped files are updated in place: a missing directive is appended in a dated block, and the provenance block is rewritten. A second run changes nothing (`test_regenerating_a_shipped_file_is_a_no_op`).

**E7. Readers to reuse.** `SchemeParser._first_present` :6519 (one step of p#stub → pstub → p# → p); `_intensity` :6577 (clamped to 1.0; S16 lifts the clamp for the bar/area chains); `_lpattern` :6586 (unknown pattern noted, solid); `_yesno` :6671; `_bounded_int` :6690 (out of range noted, default); `_line_color` :6723 (`none` → None); `_bounded_lwidth` :6731 (0..`_LWIDTH_MAX_PX` 100). The p#bar chain is already resolved this way for `p_other_band_styles` at :7124-7125:
```python
            _ik = self._first_present((f"intensity p{_i}bar", "intensity pbar",
                                       f"intensity p{_i}", "intensity p"))
```
The echo rule for a bad style name is `_init_note_textbox`'s (:6774-6784): the value is shown only if it matches `[A-Za-z_][A-Za-z0-9_]{0,31}`, else "(a value that is no Stata style name)". `_dash_anglestyle_degrees` (:4960, with `_DASH_ANGLESTYLES` :4953) reads an anglestyle case-sensitively, or a number from -360 to 360. Both are in the served copy lists.

**E8. Stata truth, measured 03oct2026** (StataNow 19.5 MP; `scripts/stata_slot.sh <scratch>/s15/probe <scratch>/s15/probe/p1.do`; p1.do: `sysuse auto`; for S in s2color stcolor s1rcolor economist, `twoway scatter mpg weight, title("TTL") subtitle("SUB") note("NTE") caption("CAP") xtitle("XTL") ytitle("YTL") scheme(S)`; also `twoway scatter mpg weight || scatter price weight, yaxis(2) [title("TTL")] scheme(economist|s2color)`; each `graph export … .svg`). The SVGs were read with a 40-line scanner, and Stata units are `min(W,H)/100` of the viewBox:
```
s2color   rs=28.80  TTL x=2124.91 middle normal | SUB x=2124.91 middle | NTE/CAP x=408.00 start
          y labels rot -90 | ticks (390.8->350.8) 1.388 rs #000000 width 0.2 rs (outside)
stcolor   rs=32.40  TTL/SUB x=2904.69 middle | NTE/CAP x=542.19 start | y labels level (anchor end)
          grid #F0F0F0 drawn as 2.0-rs dashes
s1rcolor  ticks #FFFFFF 1.388 rs; y labels rot -90
economist rs=15.84  TTL/SUB/CAP x=90.29 start | NTE x=1333.03 end, y=121 (TTL y=157)
          y labels x=1364.51 start (right of the plot), no y ticks; x ticks 1240.9->1262.8 (inside) 1.387 rs
econ y2   y2 labels x=340.82 end (left), y2 ticks 373.8->351.8 1.388 rs; y1 labels x=1364.51 (right)
s2 y2     y2 labels x=3699.02 rot -90 (right), ticks 3569.1->3609.1 (outside)
```
A second probe (`p2.do`) added `plotregion(lcolor("1 2 3") lstyle(foreground))` to the s2color and economist scatters. It writes one `<rect … style="fill:none;stroke:#010203;stroke-width:W"/>` inset by W/2 from the plot region (s2color `x=393.68` with W=5.76, against region left 390.8). It leaves `TTL` and `NTE` at the same x and y as `p1.do`, so it is the reader's plot-region sentinel (TR-15.11).

Stata's own files (BASE/s and BASE/style):
- `anglestyle vertical_tick vertical` in s2color (:1965), with horizontal in seven files, so 11 of the 20 measured schemes draw vertical y labels (research §2). `anglestyle horizontal_tick horizontal` is set only in s2color.
- `linepattern major_grid dash` in four files, so 7 st* schemes have it by inheritance (stmono1 draws no grid). s2color has `solid` (:565), and `linepattern minor_grid dot` (:566).
- `color tick black`/`color minortick black` (s2color :349-350); white in s1rcolor. `gsize tick tiny` (1.3888 rs, gsize-tiny.style), `linewidth tick thin` (.2).
- `tickposition axis_tick outside` (s2color :1892), `inside` (economist :299).
- `axisstyle horizontal_default|vertical_default|horizontal_nogrid|vertical_nogrid` (s2color :1821-1824); economist `vertical_default vertical_nolinetick` (:276).
- Each axisstyle file's `set linestyle` (`none` means no line) and its majorstyle's tickstyle `show_ticks` give these flags: *_default, *_nogrid, *_withgrid: line yes, ticks yes; *_noline: line no, ticks yes; *_notick: line yes, ticks no; *_nolinetick: line no, ticks no (major_*_notickbig → tickstyle major_notickbig: `length zero`, `show_ticks no`).
- `yesno alt_xaxes no`, `yesno alt_yaxes no` (s2color :2167-2168); economist `alt_yaxes yes` (:387).
- `horizontal heading|subheading|body|small_body center` (s2color :1775-1780); economist heading, subheading and body `left` (:264-268).
- `clockdir title_position 12`, `subtitle_position 12`, `caption_position 7`, `note_position 7` (s2color :1920-1923); economist 11, 11, 7, 1 (:311-314).
- `system naturally_white 1` (s2color :28), `0` (s1rcolor :14).
- No Stata scheme declares `intensity p#bar`, `pbar`, `p#area`, `parea` or `p#` (a grep over BASE/s found only `intensity p inten80`), so all 26 resolve their bar and area chains to `intensity p`.

**E9. Bokeh facts, measured on bokeh 3.9.0** (headless Chrome through `test/range_probe.py`; `<scratch>/s15/node_probe.py`):
- A Title in `above` takes a row the frame's width: `TTL` `[29, 770, 0, 25]`, `SUB` `[29, 770, 25, 50]`. `align="center"` puts it at the frame's centre (`sx=399.5`), `align="left"` at the frame's left (`sx=29`).
- A two-line Title takes a 40-px row (`'SUB line one\nSUB line two'` `[29, 770, 25, 65]`).
- `Label(x=Node(target=fig.title, symbol="right"), y=Node(target=fig.title, symbol="top"), anchor="top_right")` resolves to `sx=770, sy=0`, inside the title's row.
- `Label.x` accepts `Instance(Node)` in bokeh 3.8.0 too (`/opt/anaconda3/bin/python3`).
- `fig.above` is `[]` for `figure(title="T")`: `fig.title` is not in the side lists.

**E10. Blast radius** (`gitnexus impact <sym> -d upstream -r dash`, 03oct2026): `SchemeParser.apply_to_figure` LOW (3), `apply_to_axis` LOW (3), `_init_properties` LOW (1), `_dash_text_annotations` LOW (3), `_dash_add_secondary_axes` LOW (3), `_dash_finish_secondary_axes` LOW (3), extractor `expected_directives` LOW (3). `ServerAppBuilder._glyph_layer_lines` is **HIGH** (4): warn, for one appended name. Extractor `extract` is UNKNOWN (the name is ambiguous); grep finds its callers, `main` and `test_scheme_fidelity.py`. The generated call sites (:35203, :35206, :35261, :35417) are source text, confirmed by grep. Not edited: `_make_figure_body` (CRITICAL), `_dash_apply_axis_spec` (HIGH), `_generate_app_source`.

**E11. Tests that pin today's behaviour** (flip in place with a `Flipped:` line; never delete):
- `test/test_server.py::TestServerAxisAngle::test_angle_make_document_runs` (:4001, y `"horizontal"` under s2color) — named by the manifest and P1.2.1.
- `test/test_mode_parity.py::TestTheYLabelAngleEntry::test_the_control_reads_horizontal_without_the_option` (:3146-3149); `_annotations` (:482-528: the Label branch reads `float(r.x)`, and no branch profiles a side-panel Title).
- `test/test_graph_options.py::TestNote::test_note_creates_label` (:185), `::TestNote::test_note_is_canvas_text_not_html` (:193), `::TestCaption::test_caption_creates_label` (:211), `::TestCaption::test_both_note_and_caption` (:218), `::TestSubtitle::test_subtitle_creates_label_above` (:307), `::TestSubtitle::test_subtitle_is_canvas_text_not_html` (:315), `::TestSubtitle::test_no_subtitle_no_label` (:323, passes vacuously once there is no Label).
- `test/test_label_sinks.py` `SINKS` rows `graph_subtitle`, `graph_note`, `graph_caption` (:581-583) and the module table (:40).
- `test/test_textbox_multiline.py` helpers `_labels` (:81) and `_drawn` (:524); `::TestMultilineReachesTheDocument::test_the_caption_is_positioned_where_it_can_be_drawn` (:229); `::TestMultilineReachesTheDocument::test_the_caption_is_added_after_the_note` (:253); `::TestTextboxAdversarial::test_macro_smcl_markup_and_python_in_a_string_arrive_as_written` (:680, `_page_titles(page) == [payload]` at :699).
- `test/test_scheme_consumption.py` helper `_labels` (:718) and the tests that call it.
- `test/test_scheme_rendered_output.py` helpers `_labels`/`_label` (:288-298); `::TestTheLegend::test_the_scheme_placed_legend_sits_nearest_the_plot` (:676, `isinstance(r, Label)` at :695).
- `test/test_scheme_review_fixes.py::TestSidePanelLegendOrder::test_the_legend_precedes_every_label_and_follows_the_axis` (:266).
- `test/test_adversarial_matrix.py::TestGraphTextBounds::test_a_long_title_is_drawn_once_in_bounded_time` (:3058-3061: one Title, the note a Label).
- `test/test_html_output.py::TestAdversarialPlotOptions::test_xss_in_note_option_escaped` (:1454, `"Label"`).
- `test/test_saved_stale_cue.py::TestTheTitlePlacement::test_the_cue_sits_nearest_the_frame_with_a_top_legend_and_subtitle` (:867, `["Title", "Legend", "Label"]`).
- `test/test_axis_options.py::TestTitleTextFidelity::test_note_and_caption_do_not_overlap` (:513) and `::TestTitleTextFidelity::test_the_caption_sits_below_the_note` (:542), which select `hasattr(r, "y")`. A Title has no `y`.
- `test/test_help_claims_8.py::TestTheShippedFiles::test_no_directive_for_what_dash_does_not_draw` (:1104; its regex `tick(?!_label)` refuses the new tick keys).
- `test/test_help_claims_8.py::TestTheShippedFiles::test_80_to_140_directives` (:1014-1030; `assert 80 <= n <= 140` per file and the help regex `80\s+to\s+140\s+directives`, dash.sthlp:3537). Measured at `c96facd` by the test's own rule: 80 to 139 (s2gmanual 139), so TR-15.1's chrome group (about two dozen directives per file) carries s2gmanual past 140. Flipped in 15-18 with the help sentence, to the counts measured on the regenerated files (R10; S24 later renames and re-measures it).
- `test/test_json_escaping.cscript` JSE-46 (`_jg_drawn Label` for sp sc np nc cp cc, :1930-1934) and JSE-65 (`_jg_drawn Label` for s n c, :3552-3558).
- `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` (`_SINGLE_Y_BASELINE_SHA256`, R10: re-derived, with the reason in the commit body).
- `test/test_scheme_review_fixes.py::TestHostileSchemeValues::test_three_hostile_values_give_three_warnings_and_the_defaults` (:544, grid 0.8 → 0.768), `::test_every_negative_linewidth_is_refused[linewidth p-default_line_width-1.5]` (:553, 1.5 → 1.152; S13 flips the other two rows) and `::test_the_hostile_scheme_still_renders` (:583, 0.8 → 0.768): the two width defaults of TR-15.3 (S13 D-13g). These are not red at S15's base (there `translate_lwidth` still has the old ladder, so the defaults keep 1.5/0.8): they turn red only on the merged tree, so they are rewritten to rung expressions that hold on both trees (15-12), not run red-first.

Not flipped (P1.2.7, S21's): `test/test_help_claims_8.py::TestDashDrawsBokehsMinorTicks::test_the_default_axis_has_minor_ticks` (:1225) and `::test_the_help_says_so` (:1232). Green before and after S15: S15 sets `minor_tick_line_color` to the scheme's `#000000` under s2color, never None on a ticked axis. Guards that stay green: `test/test_scheme_fallback_provenance.py::TestTheFallbackMirrorsS2color::test_every_style_attribute_matches` (it turns red if a new attribute lacks its `_FALLBACK_PROPS` entry), `test/test_textbox_no_text.py::TestSchemeApplyToAxis::test_unit` (`_AXIS_PROPS` holds none of the new properties), `test/test_graph_options.py::TestAxisLabelAngle::test_xlabel_no_angle_orientation_unchanged` (x stays the string `"horizontal"` because a 0° anglestyle writes the string, TR-15.4), `test/test_help_claims_8.py` :241-243 (the xtick copy).

## User stories

- **US-15.1** As a twoway user, I want `dash scatter mpg weight, title("T") subtitle("S") note("N") caption("C")` to put each text where my scheme puts it, centred or left and not bold, so the dashboard reads like the Stata graph in my report.
- **US-15.2** As a twoway user, I want my scheme's ticks, tick-label angle and grid pattern (s2color's vertical y labels, stcolor's dashed grid, s1rcolor's white ticks), with `ylabel(, angle(0))` keeping labels level when I ask.
- **US-15.3** As an economist-scheme user, I want the y axis on the right with no line or ticks, inward x ticks, my note in the title's band, and `yaxis(2)` on the left with its ticks, as Stata draws them.
- **US-15.4** As a dashboard publisher, I want the saved page and the served app to show the same chrome, before and after any filter move.
- **US-15.5** As a scheme author, I want my scheme's `anglestyle`, `tickposition`, `axisstyle`, `horizontal`, `clockdir`, `color tick` and `linepattern major_grid` lines read as Stata reads them, and a value dash cannot use named once without echoing markup.

## Business requirements

Each holds in both modes, before and after a filter move, for each of the 26 shipped schemes, measured against twoway (`chrome_truth.json`).
- **BR-15.1** The title is not bold and is aligned by its clock position and `horizontal heading`: centred in the 25 schemes with `title_position 12`/heading center, left under economist. by() panel titles are not bold and are centred. `title(, size() color())` still wins.
- **BR-15.2** Axis titles, axis 2 included, are upright.
- **BR-15.3** Subtitle, note and caption each sit on the side and at the alignment their scheme clock and justification give. Clocks 11, 12, 1 are above and 5, 6, 7 below; 11 and 7 are left, 1 and 5 right, and 12 and 6 follow the justification. The legend stays nearest the plot, the note nearer than the caption, and the subtitle nearer than the title. Economist's note is drawn in the title's band at the top right, in its box.
- **BR-15.4** Major ticks have the scheme's `gsize tick` length in Stata units (5.33 px at the 4-inch reference for `tiny`), on the side `tickposition` gives, in `color tick` and at `linewidth tick` (through the line ladder). An axis whose axisstyle draws no ticks draws none, and no line where it draws none.
- **BR-15.5** Tick labels take `anglestyle horizontal_tick` (x) and `vertical_tick` (y): vertical y labels under s2color, s2mono, s2gcolor, s1color, s1mono, s1rcolor, sj, s2manual, s1manual, s2gmanual and s2color8. An explicit `angle()` wins.
- **BR-15.6** Gridlines take `linepattern major_grid`/`minor_grid`: dashed under stcolor, stcolor_alt, stgcolor, stgcolor_alt, stmono2, sttrans, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta and stgcolor_mv (and stmono1, which draws no y grid), solid under the other 14. `xlabel(, grid)` keeps the scheme's pattern.
- **BR-15.7** Under economist, axis 1 of y is on the right with no line and no ticks; a `yaxis(2)` axis is on the left with its line and inward ticks, and `ylabel2()`/`yscale2()` reach it; x ticks point inward.
- **BR-15.8** A user scheme's new keys are read with Stata's semantics. A value dash cannot use gives one note and the s2color default, and the note shows the value only when it is a Stata style name. Valid values print nothing.
- **BR-15.9** The shipped files and `scheme_truth.json` carry the new keys with provenance, and `system naturally_white` and the p#bar/p#area intensity chains are parsed (S16 draws them). The fallback scheme equals s2color attribute by attribute.
- **BR-15.10** The help describes the chrome, and CHANGELOG "Results that change" names the old and new look.

## Technical requirements

- **TR-15.1 The extractor** (`scripts/extract_scheme_truth.py`). Add module functions after `resolve_linepattern` (:588), each with a docstring citing its style file:
  - `resolve_anglestyle(r, token) -> {"name", "degrees"}` reads `set val` of `style/anglestyle-<name>.style`, or a literal number.
  - `axis_style_flags(r, role_key) -> {"role", "axisstyle", "declared", "line", "ticks", "style_file"}` reads `axisstyle <role_key>`, the style file's `set linestyle` (`none` means line False) and `set majorstyle scheme <tickset>`. It then follows `ticksetstyle <tickset>` in the scheme to `style/ticksetstyle-<name>.style`'s `set tickstyle scheme <ts>`, and `tickstyle <ts>` to `style/tickstyle-<name>.style`'s `set show_ticks`.
  - `AXIS2_ROLES = {"x": "horizontal_nogrid", "y": "vertical_nogrid"}` beside `AXIS_ROLES` (:542), for the second axis. economist's measured y2 (line and ticks, E8) is what `vertical_nogrid` gives, and `vertical_default` would give no line.
  - In `extract` add `chrome_truth()` (beside `note_truth`, :1018) and `out.update(chrome_truth())` after :1279. Its fixture keys:
    - `tick_angle_x`, `tick_angle_y` (resolve_anglestyle of `horizontal_tick`/`vertical_tick`);
    - `major_grid_pattern`, `minor_grid_pattern` (resolve_linepattern);
    - `tick_color`, `minortick_color` (ColorResolver, `None` for Stata's `none`);
    - `tick_line_width` (resolve_linewidth); `tick_length` (resolve_sized gsize);
    - `tick_position` (literal `outside|inside|crossing`);
    - `axis_styles` (`{"x","y","x2","y2"}` from `axis_style_flags`);
    - `alt_axes` (`{"x","y"}` yesno);
    - `justification` (`{"heading","subheading","body","small_body"}`);
    - `text_positions` (`{"title","subtitle","note","caption"}` clockdir ints);
    - `naturally_white` (0/1 from `system naturally_white`);
    - `p_bar_intensity`, `p_area_intensity` (15 each, `resolve_intensity` over the chain `p#bar → pbar → p# → p` and `p#area → parea → p# → p`).

    Each key gets `sources` and `provenance` entries through the existing `getsrc`/`prov_entry`, inferred where the chain falls back.
  - In `expected_directives`, before the de-duplication (:1647), add one group with a comment naming the style files. Its directives are the Stata keys with their effective values: `anglestyle horizontal_tick|vertical_tick <name>`, `linepattern major_grid|minor_grid <name>`, `color tick|minortick #rrggbb`, `linewidth tick <name>`, `gsize tick <name>`, `tickposition axis_tick <name>`, `axisstyle horizontal_default|vertical_default|horizontal_nogrid|vertical_nogrid <name>`, `yesno alt_xaxes|alt_yaxes yes|no`, `horizontal heading|subheading|body|small_body <name>`, `clockdir title_position|subtitle_position|note_position|caption_position <n>`, `system naturally_white <0|1>`, and `intensity p<n>bar|pbar|p<n>area|parea` only where Stata's chain declares them (none of the 26, E8).
  - `intensity bar`/`intensity area` stay as written (P1.2.8 note).
  - The stale `linewidth` `dash_rule` sentence of `_meta.units` (extract_scheme_truth.py:2140-2144, "px = value * 5.0 … `_LWIDTH_MAP` …") becomes "a linewidth keyword or number is Stata units, px = max(units x 2.88, 0.3) x 4/3 (WP-30 P1.12b)", the rule S13 lands in this batch (S13 Notes). No test reads it.
- **TR-15.2 Regeneration** (A152, R7). Run `python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json`, which writes all 26 schemes by default and updates every `dash-<name>.scheme` in the package root. Then check that every pre-existing fixture key of every scheme is unchanged, probe by probe, outside `_meta.generated_utc`, `_meta.provenance`, `_meta.units.linewidth.dash_rule` (TR-15.1) and the new keys (a Python comparison against `git show HEAD:test/fixtures/scheme_truth.json`), and that every pre-existing directive line of every scheme file is unchanged (a `diff` restricted to lines that do not start with `*`, ignoring added lines). A second run prints `up to date` for all 26. Generated files are never hand-edited.
- **TR-15.3 `SchemeParser` reads the keys** (class :5646). In `_init_properties`, after the grid switches:
  - `tick_angle_x`/`tick_angle_y` (degrees, through new `_angle(key, default_deg)`: `_dash_anglestyle_degrees` of the raw value; None gives the default and one note by the E7 echo rule);
  - `major_grid_dash`/`minor_grid_dash` (`_lpattern`);
  - `tick_color` (`_line_color("color tick", "#000000")`) and `minortick_color` (`_line_color("color minortick", <tick_color or "#000000">)`);
  - `tick_line_width` (`_bounded_lwidth("linewidth tick", self.axis_line_width)`);
  - `tick_length_px` (new `_tick_length_px()`: `OptionTranslator.resolve_size(raw, "gap", 4.0, self.size_ref_in) * OptionTranslator.PX_PER_PT` for the raw `gsize tick`, clamped to 0..100; ValueError gives 4 pt and one note; absent gives 4 pt silently);
  - `tick_position` (new `_choice(key, allowed, default, what)`, allowed `("outside", "inside", "crossing")`, default `"outside"`);
  - `axis_styles` (a dict keyed `("x",1)`, `("y",1)`, `("x",2)`, `("y",2)`, through `_choice` over the horizontal or vertical names of the new class attribute `_AXISSTYLE_FLAGS`; defaults `horizontal_default`, `vertical_default`, `horizontal_nogrid`, `vertical_nogrid`);
  - `alt_xaxes`/`alt_yaxes` (`_yesno`, default False);
  - `text_just` (`{"heading","subheading","body","small_body"}`, `_choice` over `("left","center","right")`, default `"center"`);
  - `text_clock` (`{"title": 12, "subtitle": 12, "note": 7, "caption": 7}` defaults, `_bounded_int(…, 0, 12, …)`);
  - `naturally_white` (`bool(_bounded_int("system naturally_white", 1, 0, 1, …))`);
  - `p_bar_intensity` and `p_area_intensity` (15 floats each: `_intensity(_first_present((f"intensity p{i}bar", "intensity pbar", f"intensity p{i}", "intensity p")) or "intensity p", self.fill_alpha)`, and the area twin).

  S15 is batch 5's one `_init_properties` editor (A139), so it also takes S13's two width defaults (S13 D-13g): `self._lwidth("linewidth p", 1.5)` becomes `self._lwidth("linewidth p", OptionTranslator.translate_lwidth("medium"))` and `self._lwidth("linewidth major_grid", 0.8)` becomes `self._lwidth("linewidth major_grid", OptionTranslator.translate_lwidth("thin"))` (1.152 and 0.768 px on S13's ladder, which lands first). They are reached only when a scheme file lacks the key or holds a value `_lwidth` refuses.

  Add the class attribute `_AXISSTYLE_FLAGS: dict[str, tuple[bool, bool]]` (line, ticks), with the 12 names and flags of E8 and a comment citing each style file. Add the public methods `axis_flags(which, number=1) -> (line, ticks)` and `axis_side(which, number=1) -> str`: y1 `"right"` if `alt_yaxes` else `"left"`, y2 the opposite; x1 `"above"` if `alt_xaxes` else `"below"`, x2 the opposite. `_choice` returns the raw value when it is in *allowed*; otherwise the default plus one note through the call `_init_note_textbox` uses at the base (S06 may have moved it to `_dash_emit_note`), shown by the E7 echo rule. `_FALLBACK_PROPS` gains, at s2color's values: `"anglestyle horizontal_tick": "horizontal"`, `"anglestyle vertical_tick": "vertical"`, `"linepattern major_grid": "solid"`, `"linepattern minor_grid": "dot"`, `"color tick": "black"`, `"color minortick": "black"`, `"linewidth tick": "thin"`, `"gsize tick": "tiny"`, `"tickposition axis_tick": "outside"`, the four `axisstyle` keys at their own names, `"yesno alt_xaxes": "no"`, `"yesno alt_yaxes": "no"`, the four `horizontal` keys `"center"`, `"clockdir title_position": "12"`, `"clockdir subtitle_position": "12"`, `"clockdir note_position": "7"`, `"clockdir caption_position": "7"`, `"system naturally_white": "1"`.
- **TR-15.4 `apply_to_axis(self, axis, which=None, number=1)`**. Keep today's six settings. Add, for every call:
  - `axis.axis_label_text_font_style = "normal"`;
  - `major_tick_line_color = self.tick_color`, `major_tick_line_width = self.tick_line_width`;
  - `major_tick_in`/`major_tick_out` from `tick_length_px` L and `tick_position` (outside: 0/L; inside: L/0; crossing: L/2 each);
  - `minor_tick_line_color = self.minortick_color`.

  When `which` is `"x"` or `"y"`:
  - `major_label_orientation` is the string `"horizontal"` when the role's angle (`tick_angle_x` or `tick_angle_y`) is 0, else `math.radians(angle)`;
  - with `(line, ticks) = self.axis_flags(which, number)`: no line sets `axis_line_color = None`; no ticks sets `major_tick_line_color = None`, `major_tick_in = major_tick_out = 0` and `minor_tick_line_color = None`.
- **TR-15.5 `apply_to_figure`**.
  - The grid loop (:7401-7414) also sets `grid.grid_line_dash = list(self.major_grid_dash)` and `grid.minor_grid_line_dash = list(self.minor_grid_dash)`, whether or not the grid is drawn, so an explicit `grid` shows the scheme's pattern.
  - The title block (:7422-7424) also sets `text_font_style = "normal"` and `align` from `_dash_textbox_place(self.text_clock["title"], self.text_just["heading"])`, and sets `fig.title_location` only when the side differs from `"above"`.
  - The axis loop calls `apply_to_axis(axis, "x", 1)` on `fig.xaxis` and `apply_to_axis(axis, "y", 1)` on `fig.yaxis`.
  - Last, when `axis_side("y", 1) == "right"`, each `Axis` in `fig.left` moves to the front of `fig.right`; when `axis_side("x", 1) == "above"`, each `Axis` in `fig.below` moves to the front of `fig.above`. Only primary axes exist at this point in both modes (E4).
- **TR-15.6 Second axes.** `_dash_add_secondary_axes`: `side = scheme.axis_side(n, 2) if scheme is not None else <today's "right"/"above">`, and `scheme.apply_to_axis(ax, n, 2)` in place of `scheme.apply_to_axis(ax)` (:23099). `_dash_finish_secondary_axes`: the axis search (:23214) walks `("left", "right")` for y2 and `("below", "above")` for x2, in place of the one `side`. Its `side` tuple field is then unused; drop it. No signature changes.
- **TR-15.7 `_dash_textbox_place(clock, just) -> tuple[str, str]`** (new module function, placed directly above `_DASH_TEXTBOX_DEFAULTS`). A total, pure function with its table as a local literal: 11 and 10 → `("above","left")`; 12 and 0 → `("above", J)`; 1 and 2 → `("above","right")`; 3, 4 and 5 → `("below","right")`; 6 → `("below", J)`; 7, 8 and 9 → `("below","left")`. Here J is *just* when it is `"left"`, `"center"` or `"right"`, else `"center"`. A clock that is not an `int` (a `bool` included) or lies outside 0..12 gives `("above","center")`. It never returns `"left"` or `"right"` as a side (risk 1). The help documents 2-4 and 8-10 as drawn on the nearer horizontal side, which only a user scheme can ask for (P2.4 owns `position()`).
- **TR-15.8 `_dash_text_annotations`**. `_DASH_TEXTBOX_DEFAULTS` loses `"y"`/`"side"` and gains `"clock"` (subtitle 12, note 7, caption 7) and `"just"` (`"center"`) for a caller with no scheme. With a scheme, the clock is `scheme.text_clock[ann_key]` and the justification is `scheme.text_just` of `subheading`, `small_body` or `body`, for the subtitle, note and caption. Text, opts, size, colour and fill are computed as today, including whatever S09 put between `_dash_textbox` and the model (its graph-text pass, unchanged). Then:
  - **In the title band** when `side == "above"`, the clock is 1 or 11, `fig.title` has non-blank text, `fig.title_location == "above"`, and `fig.title.align` is the opposite corner (`"left"` for a box at 1, `"right"` at 11). Then `label = Label(x=Node(target=fig.title, symbol=align), y=Node(target=fig.title, symbol="top"), anchor="top_" + align, text=…, text_font_size=…, text_color=…, background_fill_color=fill)` and `fig.center = [label] + list(fig.center)`.
  - **Otherwise** `fig.add_layout(Title(text=…, align=align, text_font_style="normal", text_font_size=…, text_color=…, background_fill_color=fill), side)`. The loop order (note, caption, subtitle) stays, so the note is nearer the plot than the caption.

  The local import becomes `from bokeh.models import Label, Node, Title`. Text reaches only `Title.text`/`Label.text`, canvas text, as today.
- **TR-15.9 Both modes.**
  - R2 row S15: `"_dash_textbox_place"` goes into the functions tuple of `ServerAppBuilder._glyph_layer_lines` after `"_dash_textbox_or_default",` (33372). Append only.
  - `SchemeParser`'s new methods and `_AXISSTYLE_FLAGS` travel with the class (:33436).
  - No constant is added (the clock table is a local literal).
  - `_dash_anglestyle_degrees` and `_dash_display` are already copied.
  - `TestTheServedAppCarriesEveryName::test_every_listed_name_exists` and `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` stay green.
- **TR-15.10 No JavaScript twin.** No saved-page script reads or writes a title, text-box, tick, angle, grid-dash or axis-side property (the saved move toggles only the stale cue's `visible`, E4). A guard test walks every `CustomJS.code` of a built page and `_FILTER_JS` for those property names. The served move recomputes sources only, so chrome is unchanged after a move in both modes; tests check this through `_served_after_move`.
- **TR-15.11 twoway's chrome fixture.**
  - `scripts/svg_chrome.py` (new, stdlib only, imports `svg_truth`'s public names) holds the readers:
    - `svg_region(path, sentinel="#010203")`: the sentinel `<rect>` grown by half its stroke-width;
    - `svg_text_place(path, text, region)`: `{"side": "above|below|left|right|inside", "align": "left|center|right"}` from `text-anchor` (absent is start), with `weight` and `style` from the style attribute;
    - `svg_label_rotation(path, axis, region)`: the rotation in degrees of the numeric tick labels beside that edge;
    - `svg_label_side(path, axis, region)`: `left|right` or `below|above`;
    - `svg_ticks(path, edge, region)`: `{"n", "position", "length_rs", "color", "width_rs"}` of single short lines touching that region edge. Collinear runs of three or more segments are gridlines, not ticks. Outside means the free end is beyond the edge, inside within it, crossing both;
    - `svg_axis_line(path, edge, region)`: True when a line of at least half the edge lies on it;
    - `svg_grid(path, axis, region)`: `{"drawn", "dashed", "color"}`, where dashed means more than one collinear segment per gridline.

    `rs = min(viewBox W, H) / 100`. Regexes are anchored on attributes with no nested quantifier.
  - `scripts/extract_chrome_truth.do` (new, in S02's path-free form, A130) writes `test/fixtures/chrome_truth.json` (Stata truth below). The python block imports `svg_chrome` from `<repo>/scripts`, reads macros through `sfi.Macro`, never calls Stata, never uses `shell=True`, and spells a backtick `\x60`.
- **TR-15.12 Registries.** Under S01's anchor `# WP-30 S15 (P1.2a): Scheme chrome: titles, ticks, grid, economist axes (P1.2 part a, M1)` in `test/function_test_map.py` `FUNCTIONS`, alphabetical:
  - `SchemeParser._angle` → `test/test_scheme_chrome.py::TestHostileChromeKeys::test_an_unknown_name_falls_back_once`;
  - `SchemeParser._choice` → the same node;
  - `SchemeParser._tick_length_px` → `test/test_scheme_chrome.py::TestTheChromeKeysAreRead::test_the_tick_length_is_gsize_tick_in_stata_units`;
  - `SchemeParser.axis_flags` → `…::TestTheChromeKeysAreRead::test_axisstyle_names_map_to_line_and_tick_flags`;
  - `SchemeParser.axis_side` → `…::TestTheChromeKeysAreRead::test_axis_side_reads_the_alt_keys`;
  - `_dash_textbox_place` → `test/test_scheme_chrome.py::TestTextboxPlace::test_every_clock`.

  `test/program_coverage_map.py` is unchanged (no Stata program).
- **TR-15.13 Help** (R3: Stata scheme support and Axis and Display Options, S15's paragraphs only); see 15-18.
- **TR-15.14 Tracking.** Close `P1.2a` in place in BUGS.md, delete its `WP30_OPEN` line, and replace `<!-- WP-30 P1.2a -->` in place (R4, R5). The text is in 15-19.
- **TR-15.15 Security (rule 1).**
  - Scheme files are data. Every new value is whitelisted (`_choice`, `_AXISSTYLE_FLAGS`), bounded (clocks 0..12, naturally_white 0..1, tick length 0..100 px, widths through `_bounded_lwidth`, angles -360..360) or a colour through `_color`.
  - A bad value is echoed only when Stata-name-shaped (at most 32 characters), else as a fixed phrase.
  - Text-box text reaches only canvas text (`Title.text`, `Label.text`; `test_label_sinks.py` keeps them `CANVAS`).
  - `Node` targets are model references, never user text.
  - No `eval`, `exec`, `shell=True` or path built from a scheme value. The SVG reader's regexes run in linear time.
  - The extractor writes only under its work directory and the fixture path.

## Boundaries

- **Batch partners.** S13 owns `_LWIDTH_MAP`, `translate_lwidth`, `SchemeParser._lwidth`, `_apply_line_opts`, `_apply_marker_opts`' mlwidth, `_ci_band_style`, `_extract_region_lwidth`, `_dash_apply_z_options`, `_dash_refline_draw` and dash.ado's lwidth bounds. S14 owns `map_bar`, `map_rbar`, `map_rcap`, `map_rcapsym`, `GlyphMapper._tag_spacing`, `_FILTER_JS`, `_build_filter_widgets` and `_dash_copy_redraw_geometry`. S15 touches none of them, and calls `_lwidth` only through `_bounded_lwidth`.
- **Not edited:** `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, `_dash_apply_axis_spec`, `_dash_apply_axis_options`, `_dash_figure_title`, `_dash_style_axis_titles`, `_dash_move_legend`, the four appliers, `GlyphMapper`, dash.ado, dash_parse.mata, `scripts/svg_truth.py`, `test/cert_svg.do`, every tracking document but BUGS.md and CHANGELOG.md (A145).
- **Later sections (do not do their part):**
  - S16: marker opacity, fill blends, `fintensity()`, consuming `naturally_white` and the intensity chains, the `_intensity` clamp, ROADMAP.md:2051.
  - S21: removing Bokeh's minor ticks (FixedTicker), the ticker and padding, `TestDashDrawsBokehsMinorTicks`.
  - S24: scheme keys on every layer, and dropping the dead `intensity bar`/`intensity area` lines from the extractor after S16.
  - S28: by() panel labels as separate titles.
  - S29: SMCL font style.
  - S31: `noline`, `noticks`, `tlength()`, `tposition()`, `alt`, `labcolor()`, `glpattern()`, anglestyle names in `angle()`.
  - S33: ColorBar chrome (its `title_text_font_style`). P2.5: the legend key size (GAPS2-D16-e).
  - S53: by() edge axes, which must follow `axis_side`.
  - S56: `text()`.
  - P2.4: `title(, position() justification() ring())`, which may reuse `_dash_textbox_place`.
  - P2.2: `xmtick()`/`ymtick()`.
- **Decisions:** `.db-title` is unchanged (P1.2.9). PLAN.md's P1.2 row names `test_default_look.py` and `look_truth.json`; no section creates them (review): S15's are `test/test_scheme_chrome.py` and `chrome_truth.json`, and S16's `test/test_intensity_blend.py` and `intensity_truth.json` (PLAN.md's row is a consistency fix, g03.md).

## Stata truth

**New fixture** `test/fixtures/chrome_truth.json`, written by the new `scripts/extract_chrome_truth.do`.
- **Header.** The do-file opens with S02's path-free header (copied from an S02-converted extractor such as `scripts/extract_text_truth.do`): `local repo : env DASH_REPO`, else `c(pwd)` when it holds `dash.ado`, else `exit 601`; then ``adopath ++ "`repo'/"`` and `global dash_nobrowser 1`.
- **Stamp (D12).** It copies the `_meta` stamp of extract_text_truth.do (:74-93, :445-450): `stata_version`, `born_date`, `dash_commit` (from ``git -C "`repo'" rev-parse HEAD`` written by `shell` to a tempfile, checked at 40 hex characters), `extracted`, plus `units: "rs = min(viewBox W, H)/100"`.
- **Probes.** `sysuse auto, clear`, `set graphics off`. Every graph carries the sentinel `plotregion(lcolor("1 2 3") lstyle(foreground))`.
  - For each S of the 26 names (a literal list in the do-file; the fixture test asserts it equals `SchemeParser._BUILTIN_NAMES`): `twoway scatter mpg weight, title("TTL") subtitle("SUB") note("NTE") caption("CAP") xtitle("XTL") ytitle("YTL") <sentinel> scheme(S)`, then `graph export "<work>/ck_S.svg", replace`.
  - `economist_y2` and `s2color_y2`: `twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("TTL") <sentinel> scheme(…)`.
  - `s2color_yh`: `twoway scatter mpg weight, ylabel(, angle(horizontal)) <sentinel> scheme(s2color)`.
  - `stcolor_xgrid` and `s2color_xgrid`: `twoway scatter mpg weight, xlabel(, grid) <sentinel> scheme(…)`.
- **Record per probe** (python block through `svg_chrome`):
  - `texts` (`TTL`, `SUB`, `NTE`, `CAP`, `XTL`, `YTL` → side, align, weight, style; absent texts omitted);
  - `label_rotation` (`x`, `y`, `y2` where present), `label_side` (`y`, `y2`);
  - `ticks` (`x`, `y`, `y2` → n, position, length_rs, color, width_rs);
  - `axis_line` (`x`, `y`, `y2`), `grid` (`x`, `y` → drawn, dashed, color), `minor_ticks` (`x`, `y` counts).
- **Run** (from the worktree; the log lands in `<scratch>/s15/ext`):
  ```sh
  mkdir -p <scratch>/s15/ext
  DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s15/ext $WT/scripts/extract_chrome_truth.do
  ```
- **Expected anchors** (E8): s2color TTL `above/center/normal`, NTE `below/left`, y rotation 90, x ticks `outside` 1.39 rs `#000000`; s1rcolor tick colour `#ffffff`; stcolor y grid dashed; economist TTL `above/left`, NTE `above/right`, y label side `right`, y ticks n 0, y axis line False, x ticks `inside`; economist_y2's y2 label side `left`, y2 ticks `inside`, y2 line True.
- **Committing.** `git add -f test/fixtures/chrome_truth.json`. It is named by `test/test_scheme_chrome.py::TestEveryShippedSchemeDrawsItsChrome` (`test_fixtures_are_committed.py`). A regenerated fixture is never hand-patched.

**Regenerated fixture** `test/fixtures/scheme_truth.json` by `scripts/extract_scheme_truth.py` (TR-15.2), which reads Stata's files and never runs Stata. Its existing `_meta` keys stay (S07: D12's `dash_commit`/`extracted` belong to do-file extractors). `git add -f`.

**Truth block** `test/test_wp30_truth.cscript`, between S01's `display as text "S15 start …"` and `"S15 end …"` lines, under `* ==== S15 P1.2a: Scheme chrome: titles, ticks, grid, economist axes ====`. Python helpers sit directly above that header and declare nothing global but `S15_*` macros. They are:
- `_s15_tw()`, which reads `S15_SVG` with `svg_chrome` and sets `S15_TW` to the summary string `ttl;sub;nte;cap;axst;yrot;yside;xtick;ytick;yline;ygrid;y2side;y2tick;y2line` (each field the record's value, `-` when absent);
- `_s15_page()`, which reads the saved page `S15_PAGE` through its embedded JSON models (the S07 `_s07_page` method) into `S15_D` in the same vocabulary;
- `_s15_app()`, which builds `make_document(Document())` from the served `S15_APP` into `S15_S`, fires the Select whose `_dash_var` is `S15_MOVE` to its second option, and sets `S15_SAME_AFTER`.

Dash's vocabulary maps a Title's `align` and panel side, an in-band Label's anchor (`top_right` → `above/right`), `text_font_style`, `axis_label_text_font_style`, orientation (`pi/2` → 90, `"horizontal"`/0 → 0), the axis's panel, `major_tick_in`/`out` (position; length / 3.84 to 2 decimals), `major_tick_line_color`, `axis_line_color is None`, and `len(grid_line_dash) > 0`. Every argument crosses through `sfi.Macro`; no macro text is pasted into Python. Cases (each `sysuse auto, clear`; pages under `` `w30_work' ``; each ends `_w30_done LK-0k "<what>"`; files erased):

| Id | twoway side | dash side | PASS when |
|---|---|---|---|
| LK-01 | for S in s2color stcolor economist: the 26-scheme scatter of the fixture, with the sentinel, to SVG; `_s15_tw` | `dash scatter mpg weight, title("TTL") subtitle("SUB") note("NTE") caption("CAP") xtitle("XTL") ytitle("YTL") scheme(S) saving(lk1_S.html)`; `_s15_page`; served `dash build, server saving(lk1_S.py) replace nobrowser filter(foreign, type(dropdown))`; `_s15_app` with `S15_MOVE foreign` | the ttl, sub, nte, cap and axst fields equal in all three; `S15_SAME_AFTER == 1` |
| LK-02 | for S in s2color s1rcolor sj stcolor economist: same SVG | same pages | yrot equal (90 for the first three, 0 for the last two) |
| LK-03 | `twoway scatter mpg weight, ylabel(, angle(horizontal)) scheme(s2color)` | the same dash options | yrot 0 everywhere |
| LK-04 | for S in s2color s1rcolor stcolor economist | same pages | the xtick fields (position, length within 0.02 rs, colour) and the ytick fields equal |
| LK-05 | `xlabel(, grid)` under stcolor and s2color; and the plain stcolor scatter | the same dash options | ygrid dashed equal; the x grid's dashed equals twoway's |
| LK-06 | `twoway (scatter mpg weight) (scatter price weight, yaxis(2)), scheme(economist)`, then `scheme(s2color)` | the same layers in dash (`yaxis(2)` on the second), both modes | yside, yline, ytick, y2side, y2tick, y2line equal |
| LK-07 | — | LK-01's economist and s2color apps after the move | `S15_SAME_AFTER == 1` for both |

No case prints SKIP. The header comment list of blocks gains `S15  P1.2a scheme chrome against twoway (LK-01..LK-07)`. Run through the driver with `WP30_ONLY=S15`:
```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > <scratch>/s15/run_test_wp30_truth.do
WP30_ONLY=S15 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s15 <scratch>/s15/run_test_wp30_truth.do
```

## TDD test stubs

### Regression tests, `test/test_scheme_chrome.py` (new; red at the batch-5 base unless marked guard)

Module helpers: `_spec(scheme, graph_opts, plots=None)`, which builds the auto-like frame of `test_mode_parity` (`_DF`) with a scatter layer; `_saved(spec)` and `_served(spec)` (`test_mode_parity._standalone`/`_served`, returning the single `Plot`); `_textboxes(fig)`, which returns `[(kind, side, align_or_anchor, text)]` for every side-panel Title (excluding `fig.title` and tags `dash_stale_cue`) and every Label; `MODES = ("saved", "served")`. The docstring quotes E8's twoway lines and the probe command and date.

- Test: TestTheTitleIsTheHeadingBox::test_the_title_is_centred_and_not_bold[s2color|stcolor][mode]: `fig.title.align == "center"` and `text_font_style == "normal"`.
- Test: TestTheTitleIsTheHeadingBox::test_economists_title_is_left_and_not_bold[mode].
- Test: TestTheTitleIsTheHeadingBox::test_a_by_panel_title_is_not_bold_and_centred[mode] (`by(foreign)`, every panel figure).
- Test: TestTheTitleIsTheHeadingBox::test_an_explicit_size_and_colour_still_win[mode] (guard).
- Test: TestAxisTitlesAreUpright::test_x_and_y_titles_are_normal[mode].
- Test: TestAxisTitlesAreUpright::test_second_axis_titles_are_normal[mode] (`yaxis(2)` and `xaxis(2)` layers).
- Test: TestTextboxesSitAtTheirClock::test_the_subtitle_is_a_centred_title_above[mode].
- Test: TestTextboxesSitAtTheirClock::test_note_and_caption_are_left_titles_below_note_first[mode].
- Test: TestTextboxesSitAtTheirClock::test_economists_note_is_in_the_title_band[mode]: a Label whose x and y are `Node`s targeting `fig.title`, symbols `right`/`top`, anchor `top_right`, `background_fill_color == "#7b92a8"`, `fig.center[0]` is that label.
- Test: TestTextboxesSitAtTheirClock::test_economists_subtitle_and_caption_are_left[mode].
- Test: TestTextboxesSitAtTheirClock::test_the_legend_stays_nearest_the_plot[mode] (`legend(position(12))` plus subtitle: `fig.above` is `[Legend, Title]` in type order).
- Test: TestTextboxesSitAtTheirClock::test_the_texts_are_canvas_text_as_typed[mode] (guard: `<script>x</script>` and `R&D` reach `text` unescaped).
- Test: TestTickGeometry::test_ticks_are_the_schemes_length_outside[mode] (s2color: in 0, out `1.3888*2.88*4/3` ± 0.01).
- Test: TestTickGeometry::test_economists_x_ticks_point_inward[mode].
- Test: TestTickGeometry::test_s1rcolors_ticks_are_white[mode] (major and minor `#ffffff`).
- Test: TestTickGeometry::test_the_tick_width_is_linewidth_tick[mode] (`== scheme.tick_line_width == SchemeParser("s2color")._lwidth("linewidth tick", …)`; never a literal, so S13's ladder applies on merge).
- Test: TestTickGeometry::test_an_xtick_only_position_looks_like_a_major_tick[mode] (guard).
- Test: TestTickLabelAngle::test_s2colors_y_labels_are_vertical[mode] (`== pytest.approx(math.pi/2)`, x stays `"horizontal"`).
- Test: TestTickLabelAngle::test_stcolors_y_labels_stay_level[mode] (guard).
- Test: TestTickLabelAngle::test_an_explicit_horizontal_angle_wins[mode] (guard: `ylabel(, angle(horizontal))` gives 0.0).
- Test: TestGridPattern::test_stcolors_grid_is_dashed[mode] (`ygrid` dash equals `OptionTranslator.translate_lpattern("dash")`).
- Test: TestGridPattern::test_s2colors_grid_is_solid[mode] (guard).
- Test: TestGridPattern::test_xlabel_grid_keeps_the_scheme_pattern[mode] (stcolor `xlabel(, grid)`).
- Test: TestEconomistAxes::test_the_y_axis_is_right_without_line_or_ticks[mode].
- Test: TestEconomistAxes::test_axis_two_is_left_with_line_and_inward_ticks[mode].
- Test: TestEconomistAxes::test_ylabel2_reaches_the_left_axis_two[mode] (`ylabel2: "5000 10000 15000"` gives those ticks on the left axis).
- Test: TestEconomistAxes::test_s2colors_axis_two_stays_right[mode] (guard).
- Test: TestChromeAfterAMove::test_the_served_chrome_is_unchanged_after_a_move[s2color|economist] (guard: `test_mode_parity._served_after_move` profiles equal the unmoved ones; it gains the chrome fields when 15-10 extends the profile).
- Test: TestChromeAfterAMove::test_no_saved_script_writes_chrome (guard: no `CustomJS.code` of a built page and no `_FILTER_JS` text holds `align`, `text_font_style`, `major_tick_`, `major_label_orientation`, `grid_line_dash`, `axis_line_color`).
- Test: TestTheChromeKeysAreRead::test_s2color_stcolor_s1rcolor_economist_values (every new attribute against E8).
- Test: TestTheChromeKeysAreRead::test_the_tick_length_is_gsize_tick_in_stata_units (`tiny` gives 5.333 px; a user `gsize tick small` gives `2.777*2.88*4/3`).
- Test: TestTheChromeKeysAreRead::test_axisstyle_names_map_to_line_and_tick_flags (all 12 names).
- Test: TestTheChromeKeysAreRead::test_axis_side_reads_the_alt_keys.
- Test: TestTheChromeKeysAreRead::test_the_bar_and_area_intensity_chains_follow_statas_order (user scheme `#include s2color` + `intensity p2bar inten40` + `intensity parea inten30`: `p_bar_intensity[0:2] == [0.8, 0.4]`, `p_area_intensity` all 0.3).
- Test: TestTheChromeKeysAreRead::test_naturally_white (s2color True, s1rcolor False).
- Test: TestHostileChromeKeys::test_an_unknown_name_falls_back_once[…] (user scheme lines `anglestyle vertical_tick Vertical`, `tickposition axis_tick <script>`, `axisstyle vertical_default ../../etc/passwd`, `horizontal heading` plus 5000 x, `clockdir note_position 99`, `system naturally_white 7`: each attribute is the s2color default, one note per key, and no note holds `<script>` or exceeds 400 characters).
- Test: TestHostileChromeKeys::test_an_absurd_tick_length_is_bounded[1e308|-5|nan].
- Test: TestTextboxPlace::test_every_clock (13 clocks × 3 justifications against TR-15.7's table).
- Test: TestTextboxPlace::test_junk_is_the_default (`None`, `"12"`, `13`, `-1`, `True`, `3.5`; `just` `"x"` gives `"center"`).

Added in 15-03 after the fixture exists (red at base, appended to the failure file):
- Test: TestEveryShippedSchemeDrawsItsChrome::test_the_fixture_is_stamped_and_complete (26 names plus 5 probes; `_meta` four D12 keys).
- Test: TestEveryShippedSchemeDrawsItsChrome::test_matches_twoway[<26 names>][mode] (title, the three boxes, axis-title style, y rotation and side, x and y ticks, axis lines, grids; tick width and minor ticks are not compared: S13's and S21's).
- Test: TestEveryShippedSchemeDrawsItsChrome::test_the_extra_probes[economist_y2|s2color_y2|s2color_yh|stcolor_xgrid|s2color_xgrid][mode].

### `test/test_svg_chrome.py` (new; unit tests of `scripts/svg_chrome.py` on synthetic SVG text written to `tmp_path`)

- Test: TestTheRegion::test_the_sentinel_rect_grown_by_half_its_stroke.
- Test: TestTextPlace::test_anchor_and_side_and_weight (start/middle/end/absent; above/below; bold/italic).
- Test: TestTicks::test_outside_inside_crossing_and_length_in_rs.
- Test: TestTicks::test_a_dashed_gridline_is_not_a_tick.
- Test: TestAxisLine::test_present_and_absent.
- Test: TestGrid::test_solid_and_dashed.
- Test: TestLabels::test_rotation_and_side.
- Test: TestHostileSvg::test_a_megabyte_of_angle_brackets_reads_in_under_a_second.

### `test/test_scheme_fidelity.py` (appended)

- Test: test_the_chrome_keys_are_resolved[name] (`_CHROME_KEYS` present for all 26).
- Test: test_the_chrome_anchors (E8's values for s2color, stcolor, s1rcolor, economist).
- Test: test_resolve_anglestyle_reads_the_style_file.
- Test: test_axis_style_flags_for_every_axisstyle_file (the 12 files).
- Test: test_the_parser_axisstyle_table_is_statas (`SchemeParser._AXISSTYLE_FLAGS` equals the extractor's flags for the 12 names).

These run red-first in 15-04, appended to the failure file.

### Flips (in place; `Flipped:` lines; 15-05, 15-10 to 15-15, 15-18)

The E11 list. Each flip keeps its node name and asserts the new model (`Title` for subtitle, note and caption; the parity control reads `_num(math.pi / 2)` under s2color; the stale cue order `["Title", "Legend", "Title"]`; JSE-46/JSE-65 `_jg_drawn Title`). The shipped-files regex drops `tick(?!_label)` and keeps the rest. Reason line: `was wrong because twoway draws <the measured fact>, and S15 (P1.2a) draws it so in both modes`.

### Guards and parity (15-10)

- `test/test_mode_parity.py`:
  - `_annotations` gains a side-panel `Title` branch (kind, text, font, colour, align, font_style, side, background; tags `dash_stale_cue` excluded), and the Label branch records a `Node` coordinate as `("node", type(target).__name__, symbol, offset)` plus `anchor`;
  - `_axes.one` gains `label_style`, `tick_in`, `tick_out`, `tick_color`, `tick_width`, `line_color`, `minor_tick_color` and the axis's panel;
  - `_chrome` gains `title_align`, `title_location`, `xgrid_dash`, `ygrid_dash`;
  - `CORPUS` gains `scheme chrome: economist titles, note and axis 2`, `scheme chrome: stcolor grid and xlabel grid` and `scheme chrome: s1rcolor ticks`, and `MOVE_CORPUS` an economist case.

  `ALLOWED` and `_MUST_WARN` are not edited (R8).

### Mutation table (each must turn a named test red)

| Mutation | Red test |
|---|---|
| `apply_to_axis` skips `axis_label_text_font_style` | TestAxisTitlesAreUpright |
| `_dash_textbox_place(1, …)` returns `"center"` | TestTextboxPlace::test_every_clock, TestEveryShippedSchemeDrawsItsChrome[economist] |
| in-band Label appended, not inserted at index 0 | test_mode_parity CORPUS `scheme chrome: economist …` with an `xline` |
| `_dash_finish_secondary_axes` searches only `"right"` | TestEconomistAxes::test_ylabel2_reaches_the_left_axis_two |
| `_FALLBACK_PROPS` loses `"tickposition axis_tick"` | test_scheme_fallback_provenance |
| `"_dash_textbox_place"` missing from the copy list | every served case (NameError), `test_every_listed_name_exists` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Title, axis titles, text boxes, ticks, angle, grid, economist axes | pytest `test/test_scheme_chrome.py` | `chrome_truth.json`, literals of E8 | yes, plus served after a move |
| SVG reader | pytest `test/test_svg_chrome.py` | synthetic SVG | n/a |
| Extractor keys and shipped files | pytest `test/test_scheme_fidelity.py`, `test_scheme_fallback_provenance.py` | `scheme_truth.json` | n/a (data) |
| Parity of every new field over the corpus | pytest `test/test_mode_parity.py` | — | yes |
| Placement as BokehJS draws it | pytest `test/test_scheme_chrome_browser.py` (headless Chrome; skips without it; red under `DASH_STRICT=1`) | — | saved page and a served `file_html` |
| twoway against both modes, live | cscript `test_wp30_truth.cscript` LK-01..LK-07 (`WP30_ONLY=S15`) | — | yes, plus after a move |
| Text sinks unchanged | pytest `test/test_label_sinks.py`, `test_json_escaping.cscript` JSE-46/65 | — | yes |
| Copy list | pytest `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` | — | served |

**Acceptance criteria.**
- **AC-15.1** `TestEveryShippedSchemeDrawsItsChrome::test_matches_twoway` passes for all 26 schemes in both modes, and the five extra probes pass.
- **AC-15.2** Under s2color, `fig.title.align == "center"`, its `text_font_style == "normal"`, every axis `axis_label_text_font_style == "normal"`, the y orientation is π/2, and the ticks are 0/5.33 px `#000000`, in both modes and after a served move.
- **AC-15.3** Under economist, the y axis is in `fig.right` with `axis_line_color is None` and no ticks; a `yaxis(2)` axis is in `fig.left` with a line and inward ticks; the note is the in-band Label of TR-15.8; the x ticks are inward.
- **AC-15.4** `LK-01`..`LK-07` print PASS, and the block prints `ALL CHECKS PASSED` with `WP30_ONLY=S15`.
- **AC-15.5** The regenerated files keep every pre-existing record and directive, and a second extractor run prints `up to date` 26 times.
- **AC-15.6** Every E11 pin is flipped with a `Flipped:` line, `TestDashDrawsBokehsMinorTicks` is untouched and green, and the full suite has 0 failed.
- **AC-15.7** BUGS.md `P1.2a` is closed, its `WP30_OPEN` key is gone, the marker is replaced, and `test_tracking_documents.py` passes.

## Tasks

**Commit boundary.** Tasks 15-01 to 15-19 form the one P1.2a commit. Subject: `Draw each scheme's titles, ticks, grid and axes as Stata draws them (WP-30 P1.2a)`. It is made by 15-19 on `wp30-s15` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s15`, after one full run through the queue. The body:
- opens with `<scratch>/15-P1.2a-failure.txt`;
- gives the measured defect (Overview) and what changed where (TR-15.1 to TR-15.9);
- then carries one line each of `Regression: test/test_scheme_chrome.py::<Class>::<test> -- failed at <batch-5 base sha> with <text>`, `Flipped: <node> -- <old> was wrong because <why>` (from `<scratch>/s15/15-flips.txt`), `Fixture: test/fixtures/chrome_truth.json (scripts/extract_chrome_truth.do)`, `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`, the digest line `Rebaselined: test/test_varlist_expansion.py _SINGLE_Y_BASELINE_SHA256 -- the single-y page now carries the scheme's title, axis and tick chrome`, and `BUGS.md: "<title>" (closed)`.

Every command runs from `$WT`. No subject, body, BUGS, CHANGELOG or help line names a tool or vendor (G7).

<task type="auto" id="15-01">
  <name>Write the failing chrome regression tests</name>
  <files>test/test_scheme_chrome.py</files>
  <action><![CDATA[
    Check the cut: `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-5-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s15`. Run `mkdir -p <scratch>/s15`. Confirm that `<scratch>/batch-5-impact.txt` holds E10's rows; append any missing one (`gitnexus impact <sym> -d upstream -r dash` in the main checkout).

    Create `test/test_scheme_chrome.py` with the module helpers and every class and test of "TDD test stubs / Regression tests" except the three fixture-table tests (15-03 adds those). The docstring quotes DROPIN P1.2, E8's twoway lines with the `p1.do` command and date, and register P1.2.1, P1.2.6 and P1.2.7. Expected values are literals from E8 and E7, with each source cited in a comment; tick widths are read from `SchemeParser`, never written as numbers.

    Run `python3 -m pytest test/test_scheme_chrome.py -q -n0 -p no:cacheprovider -rf > <scratch>/s15/15-01.log 2>&1`. Write `<scratch>/15-P1.2a-failure.txt`: the base sha, each FAILED node with its one-line reason, then the guards that passed. Do not commit, and do not weaken a test to pass.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s15/15-01.log` is at least 40; `grep -c "'left' == 'center'\|'bold'\|'italic'\|AttributeError\|NameError" <scratch>/s15/15-01.log` is at least 4; the guard nodes (an_explicit_size_and_colour_still_win, the_texts_are_canvas_text_as_typed, an_xtick_only_position, stcolors_y_labels_stay_level, an_explicit_horizontal_angle_wins, s2colors_grid_is_solid, s2colors_axis_two_stays_right, served_chrome_is_unchanged_after_a_move, no_saved_script_writes_chrome) pass; `test -s <scratch>/15-P1.2a-failure.txt`.]]></verify>
  <done>Every regression test of the section existed, the defects were shown failing on the unmodified tree, and the failure text was saved.</done>
</task>

<task type="auto" id="15-02">
  <name>Add the SVG chrome reader</name>
  <files>scripts/svg_chrome.py, test/test_svg_chrome.py</files>
  <action><![CDATA[
    Create `scripts/svg_chrome.py` as TR-15.11 specifies: stdlib only, importing `svg_truth` by name from its own directory, with a module docstring stating the sentinel rule (E8, `p2.do`), the Stata-unit rule and svg_truth.py's caller rules. The public functions are `svg_region`, `svg_text_place`, `svg_label_rotation`, `svg_label_side`, `svg_ticks`, `svg_axis_line` and `svg_grid`. Each returns plain values, never raises on a well-formed SVG, and returns None for a missing sentinel.

    Create `test/test_svg_chrome.py` with the tests of "TDD test stubs / test_svg_chrome.py". Each builds a minimal SVG string modelled on E8's elements (a `<rect … style="fill:none;stroke:#010203;stroke-width:5.76"/>`, `<line>` ticks, `<text … text-anchor=…>`), so no Stata is needed. Then run the five E8 SVGs in `<scratch>/s15/probe` through the reader and check that it reproduces E8's table (a scratch check, not a test).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_svg_chrome.py -q -n0 -p no:cacheprovider` passes; `python3 -c "import sys; sys.path.insert(0,'scripts'); import svg_chrome as s; r=s.svg_region('<scratch>/s15/probe/p2_s2color.svg'); print(round(r['left'],1))"` prints `390.8`.]]></verify>
  <done>A tested reader turned a twoway SVG into side, alignment, rotation, tick, axis-line and grid facts in Stata units.</done>
</task>

<task type="auto" id="15-03">
  <name>Extract twoway's chrome for 26 schemes</name>
  <files>scripts/extract_chrome_truth.do, test/fixtures/chrome_truth.json, test/test_scheme_chrome.py</files>
  <action><![CDATA[
    Create `scripts/extract_chrome_truth.do` exactly as "Stata truth" specifies (S02's header, the D12 stamp copied from extract_text_truth.do, the 26 plus 5 probes with the sentinel, the python block through `svg_chrome`, SVGs under a fresh work directory from `tempfile`, erased at the end). Run it with `DASH_REPO=$WT` through `scripts/stata_slot.sh <scratch>/s15/ext` and read the log. The fixture must hold E8's expected anchors; if one differs, stop and report, because the reader or the probe is wrong, not Stata.

    `git add -f test/fixtures/chrome_truth.json`. Append the three fixture-table tests of "TDD test stubs" to test/test_scheme_chrome.py, with helpers `_twoway_view(record)` and `_dash_view(fig)` mapping both sides to the vocabulary of the "Stata truth" truth block. Run them on the unmodified renderer, and append their FAILED nodes under the heading `Fixture tables, red at base` to the failure file.
  ]]></action>
  <verify><![CDATA[`grep -cE '^r\([0-9]+\);' <scratch>/s15/ext/extract_chrome_truth.log` prints 0; `python3 -c "import json; d=json.load(open('test/fixtures/chrome_truth.json')); print(len([k for k in d if k!='_meta']), sorted(d['_meta']))"` prints `31` and a list holding `born_date`, `dash_commit`, `extracted`, `stata_version`; `python3 -m pytest test/test_scheme_chrome.py -q -n0 -p no:cacheprovider -k "stamped_and_complete"` passes.]]></verify>
  <done>twoway's chrome for every shipped scheme and five option probes was recorded with its provenance stamp, and the table tests failed on the unmodified renderer.</done>
</task>

<task type="auto" id="15-04">
  <name>Carry the chrome keys in the extractor</name>
  <files>scripts/extract_scheme_truth.py, test/test_scheme_fidelity.py</files>
  <action><![CDATA[
    First append the tests of "TDD test stubs / test_scheme_fidelity.py" to test/test_scheme_fidelity.py, with `_CHROME_KEYS` beside `_S3_KEYS`. Run them, and append their red nodes to the failure file under `Extractor keys, red at base`.

    Then make TR-15.1's additions: `resolve_anglestyle` and `axis_style_flags` after `resolve_linepattern` (:588), `AXIS2_ROLES` beside `AXIS_ROLES` (:542), `chrome_truth()` beside `note_truth()` with `out.update(chrome_truth())` after :1279, and the one new `expected_directives` group before the de-duplication at :1647. Its comment lines name the style files and say that the values are effective, as the plot-region group's comment does. Do not run the regeneration yet.
  ]]></action>
  <verify><![CDATA[`python3 -c "import sys; sys.path.insert(0,'scripts'); import extract_scheme_truth as x; e=x.extract(x.DEFAULT_STATA_BASE,'economist'); print(e['tick_position'], e['alt_axes'], e['axis_styles']['y']['line'], e['text_positions']['note'], e['naturally_white'])"` prints `inside {'x': False, 'y': True} False 1 1`; the new test_scheme_fidelity tests other than `test_the_chrome_keys_are_resolved` and `test_the_parser_axisstyle_table_is_statas` pass.]]></verify>
  <done>The extractor resolved every chrome key with provenance through Stata's own chains and style files.</done>
</task>

<task type="auto" id="15-05">
  <name>Regenerate the 26 scheme files and fixture</name>
  <files>dash-*.scheme (the 26), test/fixtures/scheme_truth.json, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Run `python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json`. Make TR-15.2's two checks, writing the scripts to `<scratch>/s15/regen_check.py`, and save their output to `<scratch>/s15/regen_check.txt`: every pre-existing fixture key unchanged per scheme outside `_meta.generated_utc`, `_meta.provenance` and `_meta.units.linewidth.dash_rule`, and every pre-existing directive line of each `dash-*.scheme` unchanged. Run the extractor a second time, with its output saved to `<scratch>/s15/regen2.log` (`> <scratch>/s15/regen2.log 2>&1`), and confirm that it prints `up to date` for each of the 26. Run `git add -f test/fixtures/scheme_truth.json`.

    Write each regenerated file's directive count, by `test_80_to_140_directives`' own rule (`_directives` of the file, keys not starting `sequence` or `label`), one `<name> <n>` line per scheme, to `<scratch>/s15/directive_counts.txt`, with the minimum and maximum on its last line; 15-18 uses them.

    In test/test_help_claims_8.py, flip `TestTheShippedFiles::test_no_directive_for_what_dash_does_not_draw` in place. The regex drops `|tick(?!_label)`, the docstring's "tick geometry" becomes "margins", and the trailing comment is `# P1.2a: the scheme's tick keys are carried and drawn`. Append the `Flipped:` line to `<scratch>/s15/15-flips.txt`.
  ]]></action>
  <verify><![CDATA[`grep -l '^tickposition axis_tick' dash-*.scheme | wc -l` prints 26; `grep -c 'up to date' <scratch>/s15/regen2.log` is 26; `<scratch>/s15/regen_check.txt` ends `unchanged: 26 schemes`; `python3 -m pytest test/test_scheme_fidelity.py test/test_help_claims_8.py -q -n0 -p no:cacheprovider -k "(fixture or regenerating or carries or directive or chrome_keys_are_resolved or anchors) and not 80_to_140"` passes (`test_80_to_140_directives` is flipped with its help sentence in 15-18); `<scratch>/s15/directive_counts.txt` lists 26 counts.]]></verify>
  <done>The 26 shipped files and the fixture carried every chrome key with provenance, and every earlier record and directive was unchanged.</done>
</task>

<task type="auto" id="15-06">
  <name>Read the chrome keys in SchemeParser</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    In `SchemeParser` (class :5646) make TR-15.3:
    - the `_FALLBACK_PROPS` entries (appended after `"linewidth ci2_area": "medium",`, with a comment citing scheme-s2color.scheme's lines from E8);
    - the class attribute `_AXISSTYLE_FLAGS` (after `_BUILTIN_NAMES`, citing the 12 style files);
    - the private methods `_choice`, `_angle` and `_tick_length_px` (after `_bounded_int`);
    - the public `axis_flags` and `axis_side` (after `_cycle_for`);
    - the attributes read in `_init_properties` after the grid switches, and the two width defaults of TR-15.3 (S13 D-13g).

    `_choice` and `_angle` emit their note through the same call `_init_note_textbox` uses at the base, with the E7 echo rule. Add the five SchemeParser keys of TR-15.12 under S15's anchor in test/function_test_map.py, alphabetically. Do not edit `apply_to_figure` or `apply_to_axis` yet.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_chrome.py -q -n0 -p no:cacheprovider -k "ChromeKeysAreRead or HostileChromeKeys"` passes; `python3 -m pytest test/test_scheme_fallback_provenance.py test/test_scheme_fidelity.py test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes (the map's `_dash_textbox_place` entry is added in 15-07).]]></verify>
  <done>SchemeParser exposed every chrome key, bounded and whitelisted, with a fallback equal to s2color.</done>
</task>

<task type="auto" id="15-07">
  <name>Style figures and axes from the scheme</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    First define `_dash_textbox_place` directly above `_DASH_TEXTBOX_DEFAULTS` (:25962) as TR-15.7 specifies, because `apply_to_figure` calls it. Its docstring gives the table, the reason it never returns a side panel (E9; bokeh.js TitleView) and P2.4's future reuse. Add `"_dash_textbox_place",` to the functions tuple of `ServerAppBuilder._glyph_layer_lines` directly after `"_dash_textbox_or_default",` (R2 row S15), and `'_dash_textbox_place': 'test/test_scheme_chrome.py::TestTextboxPlace::test_every_clock',` under S15's anchor in test/function_test_map.py.

    Then make TR-15.4 in `SchemeParser.apply_to_axis` (signature `apply_to_axis(self, axis, which=None, number=1)`, docstring extended) and TR-15.5 in `apply_to_figure`: the grid dash, the title style and alignment, the role-aware axis loop, and the axis moves for `alt`. Each new statement gets a comment naming its Stata key and the measured fact from E8. Check that `math` is imported at module level before adding an import.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_chrome.py -q -n0 -p no:cacheprovider -k "TextboxPlace or Title or Upright or TickGeometry or TickLabelAngle or GridPattern or the_y_axis_is_right"` passes in both modes; `python3 -m pytest test/test_textbox_no_text.py test/test_help_claims_8.py test/test_statistical_helpers.py test/test_resource_limits.py -q -p no:cacheprovider -k "ApplyToAxis or MinorTicks or CarriesEveryName or DefinesEveryName"` passes.]]></verify>
  <done>Every figure and axis took its scheme's title style and alignment, axis-title style, tick geometry, label angle, grid pattern and axis sides, in both modes, and the clock helper reached the served app.</done>
</task>

<task type="auto" id="15-08">
  <name>Put second axes on the scheme's side</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-15.6:
    - in `_dash_add_secondary_axes` (:23034), compute the side from `scheme.axis_side(n, 2)` when a scheme is given, and call `scheme.apply_to_axis(ax, n, 2)` at :23099;
    - in `_dash_finish_secondary_axes` (:23172), search both sides of the dimension at :23214 and drop the unused `side` field of its tuple.

    Extend both docstrings by one sentence on economist (E8's econ y2 line). Run test/test_dual_axis.py, test/test_axis2_suboptions.py and test/test_help_claims_7.py, which pin s2color's right-hand axis 2, and confirm they stay green.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_chrome.py -q -n0 -p no:cacheprovider -k EconomistAxes` passes; `python3 -m pytest test/test_dual_axis.py test/test_axis2_suboptions.py test/test_help_claims_7.py -q -p no:cacheprovider` shows 0 failed.]]></verify>
  <done>A second axis sat opposite axis 1 on the scheme's side and took the second axis's style, and its labels and scale options reached it on either side.</done>
</task>

<task type="auto" id="15-09">
  <name>Place text boxes by clock as Titles</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Rewrite `_DASH_TEXTBOX_DEFAULTS` (:25962) and `_dash_text_annotations` (:25969) as TR-15.8 specifies, keeping whatever S09 put between `_dash_textbox` and the model unchanged. The docstring states the ring order, the title-band rule (register P1.2.6) and why the Label goes to `fig.center[0]` (E4). No copy-list change: both names are already copied, and `_dash_textbox_place` was added in 15-07.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_chrome.py -q -n0 -p no:cacheprovider` passes (every class, the fixture tables included); `python3 -m pytest test/test_function_test_map.py test/test_statistical_helpers.py -q -p no:cacheprovider -k "function or CarriesEveryName"` passes.]]></verify>
  <done>Subtitle, note and caption were drawn where the scheme's clock and justification put them, as Title rows or in the title's band, in both modes.</done>
</task>

<task type="auto" id="15-10">
  <name>Extend the parity profile and corpus</name>
  <files>test/test_mode_parity.py</files>
  <action><![CDATA[
    Make the profile and corpus changes of "TDD test stubs / Guards and parity": the `_annotations` Title branch and Node handling, the new `_axes.one` and `_chrome` fields, three CORPUS cases and one MOVE_CORPUS case appended at the ends of their lists under `# WP-30 P1.2a: scheme chrome` (R8).

    Flip `TestTheYLabelAngleEntry::test_the_control_reads_horizontal_without_the_option` in place: the control reads `_num(math.pi / 2)` under the default s2color, and its docstring says that the scheme's `anglestyle vertical_tick` turns the bare scatter's labels and that `TestTickLabelAngle` pins the explicit horizontal case. Append the `Flipped:` line. Run the whole file. A parity failure is a defect of 15-07 to 15-09; fix it there, never in `ALLOWED`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py -q -p no:cacheprovider` shows 0 failed; `grep -c "WP-30 P1.2a: scheme chrome" test/test_mode_parity.py` is at least 2.]]></verify>
  <done>The parity profile compared the new chrome fields over the whole corpus and after a served move, and both modes agreed.</done>
</task>

<task type="auto" id="15-11">
  <name>Flip the Label pins in three files</name>
  <files>test/test_graph_options.py, test/test_label_sinks.py, test/test_textbox_multiline.py</files>
  <action><![CDATA[
    Flip in place the E11 nodes of these files:
    - test_graph_options.py: the seven TestNote, TestCaption and TestSubtitle nodes select side-panel `Title`s (excluding `fig.title`), and `test_no_subtitle_no_label` asserts no side-panel Title above;
    - test_label_sinks.py: rows :581-583 become `("Title",)` for subtitle and caption and `("Title", "Label")` for the note, and the module table at :40 reads `Title.text (Label.text for economist's note)`;
    - test_textbox_multiline.py: the helpers `_labels` and `_drawn` collect Label or side-panel Title text; the two caption tests assert two Title rows in `fig.below`, note first (the `y >= 0` check becomes "both are Titles in fig.below", since a Title has no screen offset); :699 asserts `[payload, payload]` (the title and the note).

    Append one `Flipped:` line per node to `<scratch>/s15/15-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_graph_options.py test/test_label_sinks.py test/test_textbox_multiline.py -q -p no:cacheprovider` shows 0 failed; `grep -c '^Flipped:' <scratch>/s15/15-flips.txt` is at least 14.]]></verify>
  <done>The text-box pins asserted Title rows and still checked the text as typed, and each flip was recorded with its reason.</done>
</task>

<task type="auto" id="15-12">
  <name>Flip the scheme test helpers</name>
  <files>test/test_scheme_consumption.py, test/test_scheme_rendered_output.py, test/test_scheme_review_fixes.py</files>
  <action><![CDATA[
    Flip in place:
    - test_scheme_consumption.py's `_labels` (:718) and test_scheme_rendered_output.py's `_labels`/`_label` (:288-298), so each collects side-panel Titles and Labels carrying the text (the economist note is the Label);
    - `TestTheLegend::test_the_scheme_placed_legend_sits_nearest_the_plot` (:695) and `TestSidePanelLegendOrder::test_the_legend_precedes_every_label_and_follows_the_axis` (:266), so their `labels` index list includes `Title`s;
    - `TestHostileSchemeValues`' three width-default pins of E11: the grid asserts at :544 and :583 become `pytest.approx(dr.OptionTranslator.translate_lwidth("thin"))`, and the `linewidth p` row's 1.5 at :553 becomes `dr.OptionTranslator.translate_lwidth("medium")` (expressions, so they hold at S15's base and on the merged tree, where they are 0.768 and 1.152), each with a comment `# WP-30 P1.2a: the default is the medium/thin rung on Stata's ladder (S13 D-13g)`. S13's two rows (:554-555) are already 0.768; if the merger kept both sides by hand, check all three rows.

    The legend-order assertions keep their meaning. Append the `Flipped:` lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_consumption.py test/test_scheme_rendered_output.py test/test_scheme_review_fixes.py -q -p no:cacheprovider` shows 0 failed.]]></verify>
  <done>The scheme suites read text boxes as Titles or the in-band Label and kept checking the ring order.</done>
</task>

<task type="auto" id="15-13">
  <name>Flip the remaining model pins</name>
  <files>test/test_adversarial_matrix.py, test/test_html_output.py, test/test_saved_stale_cue.py</files>
  <action><![CDATA[
    Flip in place:
    - `TestGraphTextBounds::test_a_long_title_is_drawn_once_in_bounded_time`: Titles `[title, note]` in document order, no Label, the note held by `("Title", "text")`, and each text still drawn once, escaped once;
    - `TestAdversarialPlotOptions::test_xss_in_note_option_escaped`: `"Title"`;
    - `TestTheTitlePlacement::test_the_cue_sits_nearest_the_frame_with_a_top_legend_and_subtitle`: `["Title", "Legend", "Title"]`, with `f.above[0].tags == ["dash_stale_cue"]` kept.

    Append the `Flipped:` lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_adversarial_matrix.py test/test_html_output.py test/test_saved_stale_cue.py -q -p no:cacheprovider` shows 0 failed.]]></verify>
  <done>The bounds, escaping and stale-cue pins asserted the note and subtitle as Titles, with their security checks intact.</done>
</task>

<task type="auto" id="15-14">
  <name>Flip the angle and ring pins</name>
  <files>test/test_server.py, test/test_axis_options.py, test/test_json_escaping.cscript</files>
  <action><![CDATA[
    Flip in place:
    - `TestServerAxisAngle::test_angle_make_document_runs` at :4001: the served y axis, asked nothing, reads `pytest.approx(math.pi / 2)` (s2color's `anglestyle vertical_tick vertical`, register P1.2.1), and the docstring's control sentence is restated;
    - `TestTitleTextFidelity::test_note_and_caption_do_not_overlap` and `::test_the_caption_sits_below_the_note`: select the `Title`s in `fig.below` and assert two distinct rows, note first;
    - test_json_escaping.cscript JSE-46 (:1930-1934) and JSE-65 (:3552-3558): `_jg_drawn Title` in place of `_jg_drawn Label`, and the comment says why.

    Run the cscript through the driver (BRIEF "Running one cscript"), with the log at `<scratch>/s15/run_test_json_escaping.log`. Append the `Flipped:` lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_server.py test/test_axis_options.py -q -p no:cacheprovider -k "Angle or TitleTextFidelity"` passes; `grep -c "JSE-46 PASS\|JSE-65 PASS" <scratch>/s15/run_test_json_escaping.log` prints 2 and the log ends with the script's ALL CHECKS PASSED line.]]></verify>
  <done>The angle, ring and escaping pins asserted the scheme's angle and the Title rows in both modes.</done>
</task>

<task type="auto" id="15-15">
  <name>Sweep the text and axis test files</name>
  <files>test/test_varlist_expansion.py</files>
  <action><![CDATA[
    Re-derive `_SINGLE_Y_BASELINE_SHA256` (:393-403) by running its test and copying the printed actual digest, with the trailing comment `# <old> -> <new>: P1.2a the scheme's title, axis and tick chrome` (R10).

    Then run every test file that mentions `Label(`, `"Title"`, `fig.left`, `fig.right`, `major_label_orientation`, `axis_label_text`, `grid_line` or `minor_tick`: `grep -l` over `test/test_*.py`, minus the files already run, listed in `<scratch>/s15/sweep-files.txt`. Run them as one pytest file list (`-q -p no:cacheprovider`). Any red node is either a defect of 15-07 to 15-09 (fix it there) or a pin of today's chrome that E11 missed. For a missed pin, stop and report its node and reason to the orchestrator, which amends this section (R12), rather than editing a fourth file in this task.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_varlist_expansion.py -q -n0 -p no:cacheprovider -k single_y` passes; the sweep log `<scratch>/s15/sweep.log` shows 0 failed.]]></verify>
  <done>The single-y digest carried the new chrome with its reason, and no other test file pinned the old chrome.</done>
</task>

<task type="auto" id="15-16">
  <name>Add the browser placement check</name>
  <files>test/test_scheme_chrome_browser.py</files>
  <action><![CDATA[
    Create `test/test_scheme_chrome_browser.py` in `test_stale_cue_browser.py`'s frame: Chrome is found as `responsive_probe` finds it, the tests skip without it, and a skip is red under `DASH_STRICT=1`. Drive `range_probe.RangeProbe` with a JS read in the form of E9's probe: the frame bbox, each Title view's panel bbox and `_get_position()`, and each Label view's `_rect`.

    Cases, on the saved page and on a served document written with `bokeh.embed.file_html`:
    - (a) s2color: the title and subtitle x within 1 px of the frame's horizontal centre; note and caption x within 1 px of the frame's left; note row above caption row;
    - (b) economist: the note's rect right within 1 px of the frame's right, its top at the title row's top, and its bottom at most the title row's bottom plus 2 px;
    - (c) economist: the y axis view's bbox left at or beyond the frame's right.
  ]]></action>
  <verify><![CDATA[`DASH_STRICT=1 python3 -m pytest test/test_scheme_chrome_browser.py -q -n0 -p no:cacheprovider` passes on this Mac (Chrome present).]]></verify>
  <done>BokehJS was shown drawing the centred title and subtitle, the left note and caption, economist's in-band note and its right-hand axis where twoway draws them, in both modes.</done>
</task>

<task type="auto" id="15-17">
  <name>Write the LK truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Fill S15's stub block with LK-01..LK-07 and its python helpers `_s15_tw`, `_s15_page` and `_s15_app`, exactly as "Stata truth / Truth block" specifies, between S15's own start and end lines, with the helpers directly above `* ==== S15 P1.2a: …` (R1). Add the block's line to the header's block list.

    Run it alone through the driver with `WP30_ONLY=S15`, with the log at `<scratch>/s15/run_test_wp30_truth.log`. Then run `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider -k Wp30`.
  ]]></action>
  <verify><![CDATA[`grep -c "^LK-0[1-7] PASS" <scratch>/s15/run_test_wp30_truth.log` prints 7, the log holds `test_wp30_truth: ALL CHECKS PASSED`, and the hygiene tests pass.]]></verify>
  <done>twoway's chrome was certified live against the saved page and the served app, before and after a move, in seven cases.</done>
</task>

<task type="auto" id="15-18">
  <name>Document the scheme chrome</name>
  <files>dash.sthlp, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Edit only S15's paragraphs (R3, A155):
    - Stata scheme support, Grids (:3380-3391): the grid's `linepattern major_grid`/`minor_grid` (stcolor's dashes, kept by `xlabel(, grid)`), and in place of "Tick geometry is not the scheme's (see below)" the tick facts: length `gsize tick` in Stata units, side `tickposition axis_tick`, `color tick`, `linewidth tick`, the axisstyle line and tick flags, and economist's axis sides. Keep the sentence that Bokeh's minor ticks remain on default-labelled axes, which `TestDashDrawsBokehsMinorTicks::test_the_help_says_so` pins (S21 rewrites it).
    - Text (:3393-3405): titles are not bold; the title, subtitle, note and caption are placed by `clockdir …_position` and `horizontal heading|subheading|small_body|body`; axis titles are upright; economist's note sits in the title's band; a user scheme's clocks 2-4 and 8-10 are drawn on the nearer horizontal side (TR-15.7).
    - Series (:3357-3380): one sentence that `system naturally_white` and the `intensity p#bar`/`p#area` chains are carried in the shipped files.
    - The shipped-files paragraph (:3546-3556): "margins and tick geometry" becomes "margins".
    - What the shipped files are (:3534-3537): "80 to 140 directives" becomes "<lo> to <hi> directives", where `<lo>` is the minimum of `<scratch>/s15/directive_counts.txt` rounded down to a multiple of ten and `<hi>` its maximum rounded up to one. In the same task, flip `test/test_help_claims_8.py::TestTheShippedFiles::test_80_to_140_directives` in place (node name kept): `assert <lo> <= n <= <hi>`, the help regex `<lo>\s+to\s+<hi>\s+directives`, and the docstring's per-family counts re-stated from the counts file. Append its `Flipped:` line (`80 <= n <= 140 was wrong because S15 (P1.2a) carries the scheme's chrome keys, measured <min> to <max>`) to `<scratch>/s15/15-flips.txt`.
    - Axis and Display Options, angle() (:2834-2837): without `angle()` the labels take the scheme's `anglestyle` (vertical y labels under s2color and ten other schemes, named), and `angle(0)` or `angle(horizontal)` keeps them level.
    - Axis and Display Options, xtick (:2918-2921): "at the major ticks' length" becomes "at the major ticks' length, colour and width, which are the scheme's".

    No line names a tool or vendor.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_8.py test/test_help_claims_7.py test/test_help_examples.py -q -p no:cacheprovider` shows 0 failed; `grep -c "anglestyle" dash.sthlp` rises by at least 2; `grep -c "tick geometry" dash.sthlp` is 0; `grep -c "<lo> to <hi> directives" dash.sthlp` prints 1 with the bounds 15-18 measured.]]></verify>
  <done>The help described the scheme's chrome as dash now draws it and kept the minor-tick disclosure for S21.</done>
</task>

<task type="auto" id="15-19">
  <name>Close P1.2a and commit once</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    In BUGS.md, change the entry titled "The default chrome differs from every scheme: …" in place to `- [x] Title:`, and replace its Resolution line with: `  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.2a). Every graph's title, axis titles, subtitle, note and caption, ticks, tick-label angle, grid pattern and axis sides are drawn from the scheme's own keys in Stata units, in SchemeParser.apply_to_figure/apply_to_axis, _dash_text_annotations (through _dash_textbox_place) and _dash_add_secondary_axes/_dash_finish_secondary_axes, in the saved page and the served app and after a filter move; the 26 shipped schemes and scheme_truth.json carry the keys. Pinned by test/test_scheme_chrome.py::TestEveryShippedSchemeDrawsItsChrome::test_matches_twoway, test/test_scheme_chrome.py::TestEconomistAxes::test_axis_two_is_left_with_line_and_inward_ticks, test/test_wp30_truth.cscript LK-01; fixture test/fixtures/chrome_truth.json. Residual, deferred (WP-30): Bokeh's minor ticks on default axes are removed by section 21 (P1.3a), which owns them under ruling P1.2.7.`

    Delete only the `"P1.2a": …` line of `WP30_OPEN` in test/test_tracking_documents.py. In CHANGELOG.md, replace `<!-- WP-30 P1.2a -->` in place with the line of Notes "CHANGELOG line". Then:
    - run `python3 -m pytest test/test_tracking_documents.py test/test_scheme_chrome.py test/test_svg_chrome.py -q -p no:cacheprovider`;
    - run `git -C $WT merge --no-edit main` (expect `Already up to date.`);
    - run one full suite through `<scratch>/full_suite_queue.sh $WT <scratch>/15-full-1.log`, read its `exit=` line, and apply E6 for a known flaky test;
    - check scope (G6: `git diff --name-only` holds only this section's files; never the project instructions file, .gitignore or AGENTS.md, E7);
    - write the message per "Commit boundary" to `<scratch>/s15/msg.txt`, run G7 (`grep -Eic 'claude|anthropic'` prints 0), confirm `git branch --show-current` prints `wp30-s15`, `git add` the changed paths (`git add -f` for the two fixtures), and run `git commit -F <scratch>/s15/msg.txt`;
    - run G7 again on `git log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/15-full-1.log` reads `exit=0` and its summary shows 0 failed; `grep -c 'WP-30 P1.2a -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.2a": "' test/test_tracking_documents.py` prints 0; `git log -1 --format=%s` ends `(WP-30 P1.2a)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>P1.2a was closed in BUGS.md, its key and marker were replaced, and the section landed as one green commit on wp30-s15.</done>
</task>

## Section completion criteria

- AC-15.1 to AC-15.7 hold on `wp30-s15`, and one commit ends `(WP-30 P1.2a)`.
- `chrome_truth.json` (31 records, D12 stamp) and the regenerated `scheme_truth.json` are tracked, each named by a test.
- `"_dash_textbox_place"` follows `"_dash_textbox_or_default",` in the functions tuple, and S15's six map keys sit under its anchor.
- No file outside the task lists changed. `_make_figure_body`, `_generate_app_source` and the partners' functions are untouched (`gitnexus detect-changes` at landing names only TR-15's symbols and the extractor's).
- `TestDashDrawsBokehsMinorTicks` is unchanged and green.

## Notes

- **`_dash_textbox_place` lands in 15-07,** with its copy-list entry and map key, because `apply_to_figure` calls it for the title; 15-09 then uses it for the text boxes. The tree is expected green from 15-09 on, and is proved green only by 15-19's full run.
- **Renderer order (E4).** Never move the chrome into a later helper: the served app adds axis 2 before `_dash_figure_title` and the saved renderer after it. Only `apply_to_figure`/`apply_to_axis` run first in both modes. The in-band Label goes to `fig.center[0]` because the Spans precede it when saved and follow it when served.
- **`size_ref_in`** is S08's attribute. If the batch-5 base names it differently, use S08's name; do not add a second one.
- **S13 merge.** S13 lands first and rewrites `SchemeParser._lwidth`; it edits neither `_init_properties` nor `_FALLBACK_PROPS` (S13 D-13g), so S15 is their one batch-5 editor. S15's tick width goes through `_bounded_lwidth` → `_lwidth`, and its tests compare with `SchemeParser`, never a literal, so the merged tree is green with S13's ladder. S15's two width defaults (TR-15.3) use `translate_lwidth`, so they are S13's rungs once merged; at S15's own base (S13 not landed in the worktree) they are the old ladder's 1.5/0.8, so 15-12's three hostile flips are written as `OptionTranslator.translate_lwidth("thin")`/`("medium")` expressions, never literals, and hold on both trees. The parametrize rows of `test_every_negative_linewidth_is_refused` are adjacent to S13's: the merger keeps S13's two rows and S15's one.
- **Regeneration conflicts (R7).** S15 is the batch's only regenerator. A conflict in a `dash-*.scheme` or `scheme_truth.json` is resolved by re-running TR-15.2's command on the merged tree, never by hand, and the merge log records it.
- **Pinned digest (R10).** S13 also moves `_SINGLE_Y_BASELINE_SHA256`. The merger re-derives it after S15's landing and names it in the merge log.
- **Help (R3).** In batch 5, S15 alone edits Stata scheme support and Axis and Display Options; S13 edits Marker and Transparency Options, and S14 Plot types.
- **CHANGELOG (R4).** S15 replaces only `<!-- WP-30 P1.2a -->` in the `**WP-30 (drop-in P1, 03oct2026)**` group of `### Results that change`.
- **BUGS and `WP30_OPEN` (R5).** S15 edits only its own entry and its own key line; adjacent deletions by S13 and S14 conflict in context only.
- **Mode parity (R8).** S15 appends CORPUS cases and edits the profile functions `_annotations`, `_axes` and `_chrome` (no partner of batch 5 edits them, per the batch-5 file table). It never edits `ALLOWED` or `_MUST_WARN`.
- **python_exec hazard.** The extractor and the truth block run under Stata's Python. After the run, `~/.stata19/console/stata19.rc` must still hold the maintainer's `python_exec` (E12).
- **Commit-body line forms** are in "Commit boundary". `Flipped:` reasons name the measured fact (E8) and register P1.2.1 where it applies.
- **CHANGELOG line** (replaces the marker, one line): `- Every graph's chrome is drawn from its scheme, in both modes and after a filter move: under the default s2color, `dash scatter mpg weight, title(T)` drew the title bold at the left and now draws it centred and not bold (left under economist); axis titles were italic and are now upright; subtitle(), note() and caption() were drawn at the plot's left edge and are now placed by the scheme's clock position and justification (the subtitle centred above, the note and caption at the left below, economist's note in its box at the top right beside the title); y tick labels were level and are now vertical under s2color, s2mono, s2gcolor, s1color, s1mono, s1rcolor, sj, s2manual, s1manual, s2gmanual and s2color8 (`ylabel(, angle(0))` keeps them level); ticks were 2 px inside and 6 px outside in black and are now the scheme's `gsize tick` (5.33 px for tiny) outside, or inside under economist, in `color tick` (white under s1rcolor, where they could not be seen) at `linewidth tick`; the major grid was solid and is now dashed under the st* schemes that dash it; under economist the y axis was on the left with a black line and ticks and is now on the right with neither, and a yaxis(2) axis is on the left with its line and ticks. (WP-30, P1.2a)`
- **Resolved (review): P1.2.7 against the manifest.** The manifest's S15 scope lists "no Bokeh minor ticks"; register P1.2.7 gives the minor-tick bullet and `test_help_claims_8.py`'s minor-tick/BasicTicker flips to P1.3 (S21). The register is the authority for per-question rulings (index "Per-question rulings"), so this section follows it: minor ticks stay until batch 7, styled by the scheme. The manifest's wording is a consistency-pass fix (g03.md), not a maintainer question.

### Notes for the closeout (S58; tracking documents are S58's, A145)

- **GAPS2 Tracked lines.**
  - D12 (a-c), D17 (a-d; B29 is "same gap as D17") and REM-11-04-A1-ALIGN are closed by this commit.
  - D16: c (tick geometry) and d (economist's axis) are closed here, and a (minor ticks) by S21's commit under P1.2.7. S01's S58.2 table lists D16 under P1.2a only, so add P1.3a to D16's entries before marking it Closed. D16-b (xmtick) stays P2.2 and D16-e (legend key size) P2.5.
  - B25-c (s2color's vertical y labels) is closed here; B25 as a whole closes with P1.3a/P1.3b.
- **DROPIN-REMAINING.md P1.2.** Bullets 1-6 are closed by P1.2a (bullet 4's minor ticks by P1.3a); bullet 7 belongs to P1.2b.
- **For S24 (the next regenerator touching intensities).** After S16, the shipped `intensity bar`/`intensity area` lines are unread (P1.2.8). S24's extractor edit drops those two groups and their fallback entries, and flips `test_scheme_consumption.py::test_the_key_is_read_somewhere[bar_alpha|area_alpha]` if S16 has not.
- **P2.4.** `_dash_textbox_place` is the clock table that `title(, position())` will reuse. Clocks 2-4 and 8-10 then need a Label beside the frame (not a side Title, E9) to match twoway.
