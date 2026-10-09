# Section 33: Marker-label and colour-key chrome; unread directives retained (P1.4 part b)

> Part of: WP-30 · Items: P1.4 part b (entry `P1.4b`) · Risk: yellow · Batch: 11 · Depends on: 06, 08, 24, 30 · Blocks: 34, 37 · Tasks: 13, 1 commit · Case prefix: MK

## Review amendments

- Collision (major): `map_pccapsym` is S32's too (TR-32.10 `role="aline"`), and `map_scatter` if S32's TR-32.6 moves a read out of it; D-33b, Risk 2, E2, Dependencies, Boundaries and the maintainer question now name seven (or eight) shared mappers. Q1 is restated as a **Maintainer question** with why S33 cannot yield.
- Collision (major): TR-33.4 and 33-08 no longer allow a helper taken from `apply_to_axis` (S31's this batch); the tick pair is computed inline with S31's rounding, and a new test holds it equal to `apply_to_axis` on the merged tree. Checked: the ColorBar chrome edits neither `_dash_apply_z_options` nor `apply_to_figure`.
- Partner hunks kept apart: TR-33.1 now places every new SchemeParser member away from S32's `style_bundle` and S31's `apply_to_axis`.
- Security (minor): `_parse_lines` records only the 21 listed keys, so the record is bounded whatever the file's size; `_gsize` is called once per distinct label-size key (one note, not 15); the hostile-name test also checks SMCL braces through S06's `_dash_emit_note`.
- S32 interplay recorded: under S32's index override, `pstyle(p#)` labels take `p#label` (twoway, S32's E3); a merged-tree check is in the maintainer question.
- Tests: the served move uses `test_served_linked_views._fire(doc, var, value)` (the cited `test_mode_parity._fire` takes a widget); a `ztitle(, size(*2))` regression test checks S08's multiplier now starts from the scheme's axis-title size.
- Tasks: 33-09's verify named a non-existent `test/test_custom_scheme.py` (now test_scheme.py, test_server_scheme.py and test_immediate_scheme.py); 33-10's "passes except" is now a `-k` deselection; 33-11's verify could not pass before 33-14's help edit, so the directive-count test runs in 33-14.
- Tracking: the BUGS.md title is copied verbatim from section-01 Appendix B into 33-15, the commit body and the GAPS2 Tracked line; the Resolution says the served 9px default was already gone at `c96facd`; the closeout notes list the five manifest source ids, `color label` among them.
- Rejected: "the scope says sub-claims g, i, not e, f, g": A138 and S24's D-24g reconcile the letterings, and the content (label size and colour, ColorBar chrome, unread note) is the same.
- Rejected: "`color label` must be named (manifest)": twoway ignores it (E6), so M6 keeps dash silent; the example is closed by `test_color_label_is_not_a_marker_label_key` and `test_keys_twoway_ignores`.
- Rejected: "the served 9px default needs a fix": `grep -n 9px dash_render.py` finds none at `c96facd`, and there is one `LabelSet(` (9499), built by `_apply_mlabel_opts` in both modes.

- (cross-file pass) 33-15 verify: added the key-deletion check `grep -c '^    "P1.4b": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- Row 4 answered CHANGED (ratification 06oct2026): "Do nothing" -- no unread-directive note, allow-list, count or S34 variant. M6 bullet, A150, A138, D-33a, D-33d to D-33f, the defect text, Risk, Dependencies, E4, E5, E6, E9, US-33.4/5, BR-33.4 to BR-33.6, TR-33.5, Boundaries, AC-33.4/5, Test plan, Traps, R2/R4 and "For later sections" now read: every directive is retained in the parsed scheme, none noted.
- Retention holds at `c96facd` (ratification 06oct2026): `_parse_lines` stores every directive of two or more tokens (6382-6385), `_include`'s dict is spliced whole (6372-6373), `__init__` keeps it (5981), nothing pops a key, and `_SCHEME_PROPS` copies it (33446). So `test/test_unread_scheme_directives.py` is now guards only (`TestUnreadDirectivesAreRetained`, `TestNoNoteForUnreadDirectives`, `TestHostileSchemes::test_a_large_file_is_kept_and_silent`), green at the base; no TR changes the parser (ratification 06oct2026).
- Read-recording, `_is_shipped_path`, the user-key record, `_UNREAD_TWOWAY_KEYS`, the note and their four map keys are dropped; TR-33.6/33.7 removed and TR-33.8 to TR-33.14 renumbered TR-33.6 to TR-33.12; the extractor's `twoway_unread_*` keys and the fixture's `unread` probe group (and w33s/w33q in the layer extractor) are dropped (ratification 06oct2026).
- Tasks 15 → 13 (ratification 06oct2026): old 33-09 (record keys and reads) and 33-10 (the note) removed; old 33-11 to 33-15 are now 33-09 to 33-13 (the amendments above keep the old numbers). MK-06 to MK-08 now check silence (`_cs_notes` 0); MK-09/MK-10 and w33z are dropped. The CHANGELOG has two lines (no note line), the help says unread directives are kept without a note, and the commit subject drops "and name unread scheme directives" (ratification 06oct2026).
- BUGS.md title unchanged (S01's); the Resolution closes its third clause by disposition, and GAPS2 D10-b closes the same way (ratification 06oct2026).
- The guards `test_keys_twoway_ignores` and the rest of `TestTheNoteIsSilentWhereTwowayIs`, `TestOncePerBuild`, `TestProvenance`, `TestTheReadRecorder` and `TestTheAllowListIsHonest` are dropped with the note; the `color label` example stays closed by `test_color_label_is_not_a_marker_label_key` (ratification 06oct2026).
The review pass applied both lenses.

## Overview

### Binding readings and section decisions

**Binding readings applied in this file** (decisions.md M1, M5, M6; decision-register P1.4.1, P1.4.4, X.1, X.2, X.4, X.5; index A138, A139, A145, A148, A150, A152, R1-R5, R7-R10, R12; ratification row 4, answered 06oct2026):
- **M1, P1.4.1.** The default marker-label size is Stata's text ladder, read through `SchemeParser._gsize` into the CSS-point string S08's `OptionTranslator.css_to_pt` reads, so `mlabsize(*#)` multiplies the scheme's size (S08's TR-08.9 rule, unchanged). The default colour is the scheme's marker-label colour. The colour key takes the scheme's text and tick style. Every look change gets a CHANGELOG line under "Results that change".
- **M6, P1.4.4 (A10, ratification row 4, answered 06oct2026, CHANGED).** The maintainer's answer: "Do nothing. Future versions of dash may expand to include those graphs, so processing those elements from the scheme files is important." It replaces M6's committed-list note. No directive dash does not read is noted, for any scheme (user, PLUS, third-party or shipped): there is no allow-list, no note, no count, and no ado-path variant of one in S34. The scheme parser keeps reading and retaining every directive it parses, none discarded, so a later version can draw what it holds (D-33d).
- **M5.** Nothing is refused.
- **A150, X.2.** S33 adds no note. A parser warning that exists already (an out-of-range `gsize plabel` through `_gsize`, raised once) still goes through S06's `_dash_note_scope`; tests count S06's needles, and the silence tests count zero.
- **A152.** S33 is batch 11's only scheme regenerator and lands last (merge order S31, S32, S33).
- **R12.** S33 is batch 11's only editor of `_apply_mlabel_opts`. It edits no other applier, no template (`_generate_app_source`), no `_make_figure_body`, no `_glyph_layer_lines` tuple.
- **A138.** S33 closes the research note's sub-claims e (marker-label size and colour), f (ColorBar chrome) and g (unread directives, closed by disposition: kept in the parsed scheme and not noted, ratification row 4), per S24's D-24g.

**Section decisions (this file).**
- **D-33a — the marker-label chain.** Colour: `color p#label → color plabel → color p# → color p`, with the opacity the step declares (`SchemeParser._stub_color_alpha(i, "label")`, the chain every p#stub key takes; Stata's `textboxstyle-p#.style` says `set color scheme p#label`). Size: `gsize p#label → gsize plabel → gsize p# → gsize p` (`set size scheme p#label`). `color label` and `gsize label` are not marker-label keys: twoway draws the same labels with or without them (measured, E6), so dash does not read them; like every other directive they stay in the parsed scheme (D-33d). GAPS2-D10's statement that `color label` reaches marker labels, and its plan's "s1rcolor's marker labels are white", are corrected by measurement: twoway draws s1rcolor's labels `#ffff00`, p1's colour.
- **D-33b — a label takes its own layer's style.** `_apply_mlabel_opts` gains a keyword `color_idx`, and each of its 11 calls (and `_immediate_labels`, which forwards it) passes the `color_idx` the mapper styles its own glyph with. Measured: a bar's labels are p2's colour on layer 2 and a pcarrow's p3's on layer 3 (E6). No mapper state and no option key carry the index. Seven of these functions are also S32's this batch (`map_bar`, `map_dropline`, `map_rcapsym`, `map_scatteri`, `map_pcarrow`, `map_pcbarrow` through S32's TR-32.9, and `map_pccapsym` through its TR-32.10 `role="aline"` keyword), and `map_scatter` is S32's too if S32's TR-32.6 moves an inline read out of it; see the maintainer question in Notes. With S32's TR-32.12 index override, a `pstyle(p#)`/`p(p#)` layer's `color_idx` is p#'s, so its labels take `p#label`, as twoway draws them (S32's E3: `p(p3)` labels in p3's colour).
- **D-33c — the colour key's chrome.** Tick labels take `gsize tick_label`/`color tick_label`; the title takes `gsize axis_title`/`color axis_title`, upright; ticks take the scheme's tick colour, width, length and side (S15's attributes); the bar's background is transparent so the graph region shows through, and no outline is drawn. Measured under s2color, s1manual, s1rcolor, economist and two user schemes (E6). twoway also turns the title to run up the key's right side and draws an axis line on the label side; Bokeh's ColorBar can do neither, so both go to P2.10 (Notes for the closeout).
- **D-33d — unread directives are retained, not noted (ratification row 4, 06oct2026).** `SchemeParser` already keeps every directive it parses at `c96facd`: `_parse_lines` stores each line of two or more tokens under its key (`props[tokens[0]] = tokens[1]` for a two-token class default, else `props[tokens[0] + " " + tokens[1]] = tokens[2]`, 6382-6385), splices an `#include`'s whole dict in where it stands (`props.update(self._include(…))`, 6372-6373; `_include` returns `_parse_file`'s dict, or `dict(self._FALLBACK_PROPS)`, 6389-6439), and `__init__` keeps the result whole as `self._props` (5980-5981). No line of the module pops, deletes or clears a `_props` key (the one assignment is 5981), and the served app's `_SCHEME_PROPS` is `dict(self.scheme._props)` (33446), so the app holds every directive too. Only what Stata's own `scheme.class` does not store is not stored: `sequence` and `label` lines and tokens after the third (6377-6378, and the docstring of `_parse_lines`); a one-token line is named by `_warn_unreadable_scheme_line`, as today. Retention therefore needs no code change: S33 pins it with guard tests green at the base (`TestUnreadDirectivesAreRetained`) and adds no note, list or count. The five shipped-but-unread keys (`color foreground`, `gsize text`, `yesno draw_major_grid`, `yesno draw_minor_grid`, `linepattern plotregion`) and E6's measured twoway-visible keys (`clockdir p`, `clockdir p1`…`p15`, the `textboxstyle` of `title`, `subtitle`, `caption`, `axis_title` and `tick`) are kept like any other.
- **D-33e — no read-recording and no provenance.** The withdrawn note's machinery is not built: `_props` stays the plain `dict` `_parse_file` returns; `_parse_lines`, `_parse_file`, `_include` and `SchemeParser.__init__` are not edited; and there is no `_ReadRecorder`, `_is_shipped_path`, user-key record, `unread_directives`, `_note_unread_directives`, `_MAX_UNREAD_NAMES` or `_UNREAD_TWOWAY_KEYS`. Nothing else in WP-30 needed them: S34's and S36's uses were the note's.
- **D-33f — silent everywhere.** A directive dash does not read produces no note at parse, at a saved, immediate or served build, or in the served app, for any scheme. `TestNoNoteForUnreadDirectives` and MK-06 to MK-08 pin this in both modes.
- **D-33g — S24's extractor is extended, not copied.** S33 adds its probe groups to `scripts/extract_scheme_layer_truth.do` and re-runs it, keeping one extractor per fixture so R7's "re-run on conflict" stays meaningful. Every S24 probe record is unchanged outside `_meta` (checked, 33-02). The manifest's "extends S24's fixture" and S24's Notes ("For later sections") allow this. S24 landed in batch 8; no batch-11 partner edits that file.
- **D-33h — options.** `mlabcolor(red)` keeps the scheme's label opacity (measured under sttrans: red at 0.20) and `mlabsize(*2)` doubles the scheme's size (measured: 2 × small). `mcolor()` leaves the label alone (measured). The `%NN` of `mlabcolor(red%70)` (twoway 0.70) is S43's (manifest S43: "%# opacity kept at every direct translate_mcolor site (_apply_mlabel_opts, …)").

### The defect and the fix

**What is wrong today.** DROPIN-REMAINING.md:83-85 (P1.4) reads: "Marker-label size and colour are fixed at 10px #444444. The ColorBar has no chrome. Unconsumed user-scheme directives are ignored silently." REMAINING.md:1289-1297 (11-04) adds that the server once used 9px; GAPS2-D10 says a user scheme "holding such lines parses with zero warnings". Measured at `c96facd`, in both modes:
- every marker label is `('10px', '#444444', alpha 1.0)` under s2color, s1rcolor and sttrans. twoway draws s2color's `#1a476f` at Stata's `small`, s1rcolor's `#ffff00` (dash's dark grey on a black page is close to unreadable), and sttrans's at opacity 0.20;
- the colour bar is a white box at 0.95 alpha with 11px `#444444` labels and a 13px italic `#444444` title under every scheme, s1rcolor's black page included. twoway draws the key on the graph region, its labels in the tick-label style and its title in the axis-title style;
- a user scheme setting `textboxstyle title subheading`, `textboxstyle axis_title heading`, `clockdir p 9` and `textboxstyle tick heading` parses with `warnings: []`. twoway draws all four differently (E6), and dash draws its defaults without a word. By the maintainer's ratification (row 4, 06oct2026) that silence is kept: the four directives stay in the parsed scheme for a later version to draw (D-33d), and are not noted.

The served 9px literal is already gone (`grep -n 9px dash_render.py` finds none): both modes build labels through `GlyphMapper._apply_mlabel_opts`, so one fix holds in both.

**After this section**, a marker label takes the scheme's marker-label colour, opacity and size, the same in both modes and after any filter move. `mlabcolor()`, `mlabsize()` and their `*#` forms act on that default. The colour bar's labels, title and ticks take the scheme's text and tick style, on the graph region. Every directive of every scheme stays in the parsed scheme, as at the base, and none that dash does not draw is noted (D-33d, D-33f).

**Why one section.** These are P1.4's text keys, split from S24's glyph keys (A138). They share the parser's new attributes, one extractor change with its regeneration (A152), and one fixture extension.

**Test order and commit rule (rule 7, D1).** One cycle, one commit.
- 33-01 writes the regression tests with twoway's literal values (E6), runs them on the unfixed worktree and saves `<scratch>/33-P1.4b-failure.txt`. It never commits.
- 33-02 and 33-03 extend S24's twoway fixture and add the fixture-driven tests, still red before the fix.
- 33-04 to 33-12 fix, regenerate, flip and certify.
- 33-13 closes the entry and makes the one commit, `(WP-30 P1.4b)`.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — one CRITICAL applier at 11 call sites, a 26-file regeneration, and every labelled or colour-keyed dashboard changes

**Why.** `_apply_mlabel_opts` is CRITICAL (16 impacted, 10 direct). Its signature gains a keyword passed at every call. Every shipped scheme gains a directive. Every dashboard with `mlabel()` or a continuous `colorvar()` looks different.

**Risk factors.**
1. A call site that forgets `color_idx` labels every layer in p1's style. That is silent in both modes.
2. Seven call-site functions (eight if S32 edits `map_scatter`) are S32's this batch (A139; the maintainer question in Notes). A conflict at landing could drop the keyword.
3. A later edit to the parser could drop a directive dash does not read, which ratification row 4 needs kept.
4. Regenerating 26 files could change records other than the new keys.
5. Twoway truth depends on SVG font sizes in Stata's units of the graph's smaller side, not CSS pixels.

**Mitigation.**
1. A test per labelled type compares the second layer's label colour with twoway's p2 (fixture group `mlabel_types`, both modes). 33-07's AST check (`$S/33-calls.txt`) shows all 13 calls passing `color_idx`.
2. The hunk is the call line only. S33 lands after S32 (merge order), and the merger re-adds the keyword by hand on conflict. The check in 1 runs on the merged tree.
3. `TestUnreadDirectivesAreRetained` pins every directive of a user scheme, of a user file it includes and of the 26 shipped files in `_props` and in the served `_SCHEME_PROPS`; it is green at the base and after.
4. 33-05 compares the regenerated fixture and files with `HEAD` and allows only the new keys.
5. Sizes are compared as Stata relative units: twoway's `font-size / (min(w, h) / 100)` against dash's `css_to_pt(size) / 2.88`, within 1%.

## Dependencies

- **Depends on: 06, 08, 24, 30.**
  - S06 (batch 2): `_dash_note_scope`/`_dash_emit_note`, the `(note:` form, and `_cs_notes` in `test/test_custom_scheme.cscript`.
  - S08 (batch 3): `OptionTranslator.resolve_size`, `css_pt`, `css_to_pt`, `PT_PER_RS`. Also `_apply_mlabel_opts(…, label_col=None, radius_px=None)`, whose `mlabsize` branch multiplies `css_to_pt(kwargs["text_font_size"])` (TR-08.9), and the 11 call sites passing `radius_px=self._mlabel_radius_px(...)`.
  - S24 (batch 8): `scripts/extract_scheme_layer_truth.do`, `scripts/svg_layer.py`, `test/fixtures/scheme_layer_truth.json`, the `p_markfill`/`p_markline` chains in `_init_properties`, `_STUB_KEY`'s new alternation, and the directive-count test `test_the_directive_count_is_what_the_help_says`.
  - S30 (batch 10): `_color_alpha` reads every colour form in scheme files, so `color plabel` and `color p#label` take S30's grammar.
  - Through earlier batches:
    - S01: the entry, `WP30_OPEN["P1.4b"]`, the marker `<!-- WP-30 P1.4b -->`, the stub block `S33` and the map anchor `# WP-30 S33 (P1.4b): Marker-label and colour-key chrome; unread directives retained (P1.4 part b)` (S01 writes it with this section's name).
    - S07: 26 shipped files.
    - S15: `tick_color`, `tick_line_width`, `tick_length_px`, `tick_position`, and the axis-title font style `normal`.
    - S29: SMCL in marker labels and on the colour key, applied after construction.
- **Blocks:**
  - **S34** (batch 12): resolves schemes along the ado-path, on S33's regenerated files and parser. It reads nothing of S33's since ratification row 4 withdrew the note; an ado-path scheme's directives are retained like any other (D-33d).
  - **S37** (batch 13): `mlabtextstyle()` resolves against `default_mlabel_style`.
- **Parallel batch: 11.** Merge order S31, S32, S33 (S33 last, A152).
- **Can run with:**
  - S31: the axis parse and apply functions.
  - S32: `_apply_marker_opts`, `_apply_line_opts`, the ten colour-reading mappers, the `role="aline"` call sites (TR-32.10), `_dash_plot_style_indices` and `style_bundle`. The maintainer question in Notes concerns the seven mappers both touch.
  - Neither partner edits `_apply_mlabel_opts`, `_apply_colorvar`, `_init_properties`, `_FALLBACK_PROPS`, the extractors or the scheme files. S33 edits neither S31's `SchemeParser.apply_to_axis`/`apply_to_figure`, `_dash_apply_z_options`, `_dash_apply_axis_spec` and `_dash_apply_tick_option`, nor S32's `style_bundle` and `_dash_plot_style_indices`: the colour-key chrome is a constructor argument in `_apply_colorvar`, which `_dash_apply_z_options` (S31's) overrides afterwards.

## Evidence

All anchors are at `c96facd` (dash_render.py 37,689 lines). Symbols are authoritative when lines drift; the executor re-reads each at the batch-11 base.

### E1 — the marker-label applier

`GlyphMapper._apply_mlabel_opts` (def 9302). The default size is a literal and no colour is set, so Bokeh's `#444444` is drawn:

```python
9424        kwargs: dict[str, Any] = dict(
9425            x=xvar,
9426            y=yvar,
9427            text=text_col,
9428            source=source,
9429            text_font_size="10px",
9430            x_offset=4,
9431            y_offset=4,
9432        )
```

The options replace the default (9449-9460):

```python
9449        if "mlabcolor" in options:
9450            try:
9451                kwargs["text_color"] = self.tr.translate_mcolor(options["mlabcolor"])
9452            except ValueError:
9453                _dash_style_note("mlabcolor", options["mlabcolor"], "colour")
9455        if "mlabsize" in options:
9456            try:
9457                size_px = self.tr.translate_msize(options["mlabsize"])
9458                kwargs["text_font_size"] = f"{size_px}px"
```

S08 (batch 3) rewrites the `mlabsize` branch as `css_pt(resolve_size(v, "text", css_to_pt(kwargs["text_font_size"]) or size_medium_pt("text"), ref))`. S08's Notes say: "The marker-label default size is 10px until S33".

### E2 — the 11 calls carry no layer index

`grep -n "_apply_mlabel_opts(" dash_render.py` gives the calls. Each enclosing mapper has `color_idx: int = 0` in its signature (checked one by one):

| Line | Function | In S32's ten (batch 11)? |
|---|---|---|
| 9861 | `map_scatter` (also draws connected, dot and rconnected) | only if S32's TR-32.6 moves an inline marker read out of it |
| 10289 | `map_bar` | yes |
| 13509 | `map_dropline` | yes |
| 13623, 13624 | `map_rcapsym` (one per end) | yes |
| 13953 | `map_pcscatter` | no |
| 14103 | `map_pcarrow` | yes |
| 14175 | `map_pcbarrow` | yes |
| 14282 | `map_pccapsym` | yes (S32 TR-32.10: `role="aline"` on its segment applier) |
| 14418 | `_immediate_labels` (no `color_idx` parameter) | no |
| 14632 | `map_rscatter` (`label_col=`) | no |

`_immediate_labels` (def 14355) is called by `map_scatteri` (13725, in S32's ten) and `map_pcarrowi` (14462):

```python
13724        if any(_labels):
13725            self._immediate_labels(fig, x_vals.tolist(), y_vals.tolist(),
13726                                   _labels, _clocks, options, "scatteri")
```

### E3 — the colour bar

`GlyphMapper._apply_colorvar` (def 8887), the continuous path:

```python
9241                # Raw: a ColorBar draws its title on the canvas, so escaping
9242                # it only showed the entities.
9243                _cbar = ColorBar(color_mapper=mapper, label_standoff=8,
9244                                width=12, location=(0, 0),
9245                                title=var_display)
```

`_dash_apply_z_options` (def 26106) runs afterwards (9260-9262), so `ztitle()` and `zlabel()` override any construction default:

```python
26134        text, topts = _dash_textbox_or_default(
26135            ztitle_raw, "ztitle", key_obj.title or "", seen, key)
26136        key_obj.title = text
26137        px = _textbox_size(topts, None)
26138        colour = _textbox_color(topts, None)
```

There is one `ColorBar(` in the file. The served app reaches it through `GlyphMapper`, which travels whole (class loop 33436-33438). The discrete key is a `Legend` (9217) styled by the legend chrome (`test_colorvar_legend.py:161` pins its background), so it is not touched.

### E4 — the scheme parser's storage (every directive kept) and the served rebuild

- `SchemeParser.__init__` (5977-5994) parses, stores the parsed dict whole and initialises:
  ```python
  5979        path = self._resolve_path(raw)
  5980        raw_props = self._parse_file(path, _visited=set())
  5981        self._props = raw_props
  ```
- `_parse_lines` stores a directive by its first two tokens (6377-6385) and splices an `#include` with `props.update(self._include(…))` (6372-6373):
  ```python
  6382            if len(tokens) == 2:
  6383                props[tokens[0]] = tokens[1]
  6384            else:
  6385                props[tokens[0] + " " + tokens[1]] = tokens[2]
  ```
- `_include` (6389-6439) resolves through `_resolve_cached` → `_parse_file`, or returns `dict(self._FALLBACK_PROPS)` (6439).
- Nothing removes a directive: `grep -n '_props\.pop\|del self\._props\|_props\.clear\|_props\[' dash_render.py` finds none, and the one assignment is 5981 (D-33d).
- `_safe_name` (6441-6446) bounds file text to 80 printable characters. `_MAX_INCLUDE_NOTES = 10` (6196).
- `fallback()` (5833-5841) and the emitted app (33446-33459) build a parser without a file:
  ```python
  5833        inst = cls.__new__(cls)
  5834        inst._props = dict(cls._FALLBACK_PROPS)
  ...
  5840        inst._init_properties()
  ```
  ```python
  33446            "_SCHEME_PROPS = %r" % (dict(getattr(self.scheme, "_props", {})),),
  ...
  33454            "    _s = SchemeParser.__new__(SchemeParser)",
  33455            "    _s._props = dict(_SCHEME_PROPS)",
  ```
- Every `_props` read in the class is `self._props.get(…)` (21 sites, `awk` over 5646-7880). Two are made after init: `_plot_lwidth_of` (7317), reached from `plot_line_width` (7371) and `_band_lwidth` (7151). There is no `self._props[` and no `in self._props`.
- The chain helpers: `_first_present` (6519-6525) and `_stub_color_alpha(i, stub)` (6527-6541), which walks `p<i><stub> → p<stub> → p<i> → p`. `_gsize` (6543-6574) returns a CSS point string, `"8pt"` for `small` (`_GSIZE_PT`, 5898-5915).
- The text attributes the colour key reads: `axis_title_color` (6834), `tick_label_color` (6835), `axis_title_font_size` (6964) and `tick_label_font_size` (6965).
- One parse per name per build: `DashRenderer._scheme_for` (30139-30156) caches by the name string. `ServerAppBuilder.__init__` resolves once (32829-32832). The `GlyphMapper` default (7957) resolves the shipped s2color.
- `__init__` is called through `resolve_or_fallback`'s `return cls(candidate)` (5856) and by tests.

### E5 — measured at `c96facd`, both modes

The probe is `<scratch>/wp30/s33-probe/head_probe.py`, run from `test/`. It draws `plot_for("scatter", {"mlabel": "mpg"})` and `{"colorvar": "price"}` through `test_scheme_resolution._draw` in both `MODES`:

```
s2color  standalone [('10px', '#444444', 1.0)]     served [('10px', '#444444', 1.0)]
s1rcolor standalone [('10px', '#444444', 1.0)]     served [('10px', '#444444', 1.0)]
sttrans  standalone [('10px', '#444444', 1.0)]     served [('10px', '#444444', 1.0)]
colorbar s1rcolor standalone #ffffff 0.95 11px #444444 13px #444444 italic #ffffff 5 0
colorbar s1rcolor served     #ffffff 0.95 11px #444444 13px #444444 italic #ffffff 5 0
```

(The tuples are text_font_size, text_color and text_alpha. The colour-bar columns are background colour and alpha, label size and colour, title size, colour and style, tick colour, tick in and tick out.)

`SchemeParser("scheme-w33s.scheme")` on E6's w33s file printed `warnings: []`. Its `_props` held, each under its key with the file's value (D-33d), `textboxstyle title subheading`, `textboxstyle axis_title heading`, `clockdir p 9`, `yesno plabelboxed yes` and `textboxstyle tick heading`.

**After a filter move.**
- Served: `_on_filter_change` copies redraw data onto live sources; annotation styles stay as built (research p1-04 §2).
- Saved: no page script writes a LabelSet or ColorBar style (`grep -n "text_color\|text_font_size\|major_label_text\|title_text" ` over the module's JavaScript strings finds none). `_dash_stale_glyph` (1130) dims glyph renderers' muted glyphs, not annotations.

So a construction-time default holds in both modes before and after a move.

### E6 — twoway truth (StataNow 19.5, `graph export` to SVG; sizes in Stata relative units = font-size / (min(canvas w, h)/100))

Probe do-files `p1.do` to `p5.do` in `<scratch>/wp30/s33-probe/` were run through `scripts/stata_slot.sh`. Each opens `adopath ++ "<repo>/"`, `global dash_nobrowser 1`, `version 19` and `set graphics off`, and writes the user schemes it needs into its own directory (on the ado-path as `.`). They were read with `scripts/svg_truth.py`'s `svg_document`. All printed no `r(` line.

**Marker labels**, `twoway (scatter mpg weight in 1/3, mlabel(make)), scheme(S) legend(off)`:

| Scheme | Label fill | Opacity | Size (rs) |
|---|---|---|---|
| s2color | `#1a476f` | — | 2.776 (small) |
| s1rcolor | `#ffff00` | — | 2.776 |
| stcolor (canvas 5400 × 3240) | `#1a85ff` | — | 2.776 |
| s1mono (`color plabel black`) | `#000000` | — | 2.776 |
| economist (canvas 1584 × 1584) | `#3e647d` | — | 2.778 |
| sttrans | `#1A476f` | `opacity:0.20` | 2.776 (89.94 / 32.4) |

**The chain and the options** (s2color unless named; the user files are `#include s2color` plus the lines shown):

| Probe | Result |
|---|---|
| w33a: `color plabel green`, `gsize plabel large` | `#008000`, 4.86 (large) |
| w33b: `color p1label blue`, `gsize p1label vlarge`, `color plabel green`; two layers | layer 1 `#0000ff` 5.556 (vlarge); layer 2 `#008000` 2.776 |
| w33c: `color label white`, `gsize label huge` | `#1a476f` 2.776: no change |
| `color p1 red` (research p1-04 t9) | red label |
| `mcolor(red)` | `#1a476f`: the label keeps p1 |
| `mlabsize(*2)` | `#1a476f` 5.556 = 2 × small |
| sttrans `mlabcolor(red)` / `mlabcolor(red%70)` / `mcolor(red)` | `#FF0000` at 0.20 / `#FF0000` at 0.70 / `#1A476f` at 0.20 |
| `(scatter …) (bar mpg weight in 1/3, mlabel(make)) (pcarrow mpg weight price length in 1/3, mlabel(make))` | bar labels `#90353b` (p2), pcarrow labels `#55752f` (p3) |

**The colour key**, `twoway scatter mpg weight, colorvar(price) scheme(S)`; texts right of the plot region:

| Scheme | Tick labels | Title (`rotate -90`) |
|---|---|---|
| s2color | `#000000` 3.472 (medsmall) | `#000000` 3.472 |
| s1manual (axis_title 3.9, tick_label 3.3) | `#000000` 3.301 | `#000000` 3.901 |
| s1rcolor | `#ffffff` 3.472 | `#ffffff` 3.472 |
| economist | `#000000` 3.819 | `#000000` 3.819 |
| w33k: `gsize axis_title vlarge`, `color axis_title red`, `gsize tick_label small`, `color tick_label blue` | `#0000ff` 2.776 | `#ff0000` 5.556 |

So the title is the axis title's style and the labels are the tick labels' style. Stata's `textboxstyle cleg_title clegend` (the subheading box) styles a `clegend(title())`, not the z title.

w33t (`color axisline orange`, `color tick purple`, `color clegend_line green`, `color clegend blue`):
- the key's four ticks run from x 3240 to 3280, outward toward the labels, `#800080` (`color tick`) at width 5.76;
- the key's axis line is the vertical at x 3240, `#ff7f00` (`color axisline`);
- no green stroke appears, and no rectangle other than the graph region (`#eaf2f3`) and the plot region lies behind the key.

**Unread keys** (recorded for a later version that draws them; by ratification row 4 they are retained, not noted): `(scatter mpg weight in 1/3, mlabel(make)) (scatter price weight in 1/3, mlabel(make) yaxis(2)), title("T") subtitle("S") caption("C") legend(on)`, against s2color:

| File | What twoway changed |
|---|---|
| w33s: `textboxstyle title subheading`, `textboxstyle axis_title heading`, `clockdir p 9`, `yesno plabelboxed yes`, `textboxstyle key_label heading`, `textboxstyle tick heading` | T 4.86 → 3.82; axis titles 3.47 → 4.86; labels end-anchored left of the point (x 1755 → 1691); tick labels 3.47 → 4.86. Legend keys unchanged (3.47); no label box (7 rects in both) |
| w33q: `clockdir p1 9`, `yesno p1labelboxed yes`, `textboxstyle subtitle heading`, `textboxstyle caption heading` | layer-1 labels left of the point, layer 2 unchanged; S 3.82 → 4.86; C 3.47 → 4.86 |

**Every StataCorp scheme's resolved values** (the extractor's own resolver, `python3 - <<EOF … e.SchemeResolver('/Applications/StataNow/ado/base').load(n) …`, all 26 names):
- every scheme has `gsize plabel small` and `clockdir p 3`;
- `color plabel black` in s1manual, s1mono, s2gmanual, s2manual, s2mono, sj, stmono1, stmono2 and stsj; no other scheme sets `color plabel` or any `p#label` key;
- `textboxstyle title heading`, `caption body`, `axis_title axis_title` and `tick tick_label` in all 26;
- `textboxstyle subtitle subheading_gs` in stcolor, stcolor_alt, stcolor_meta, stcolor_mv, stcoloralias, stgcolor, stgcolor_alt, stgcolor_meta, stgcolor_mv, stmono1 and stmono2, and `subheading` elsewhere. `textboxstyle-subheading_gs.style` takes the subheading's size and colour, as `textboxstyle-subheading.style` does.

**Stata's style files** (StataNow ado/base/style):
- `labelstyle-p#.style`: `set textstyle scheme p#label`, `set position scheme p#`, `set textgap scheme label_gap`;
- `textboxstyle-p#.style`: `set size scheme p#label`, `set color scheme p#label`;
- `axisstyle-clegend.style`: `set linestyle scheme axis`;
- scheme-s2color.scheme: :191 `gsize plabel small`, :1930 `clockdir p 3`, :1317-1319 `textboxstyle title heading`/`subtitle subheading`/`caption body`, :1347 `textboxstyle axis_title axis_title`, :1350 `textboxstyle tick tick_label`, :2235 `yesno plabelboxed no`.

### E7 — the extractor, the shipped files and the fallback

- `scripts/extract_scheme_truth.py`:
  - `extract` (603) builds the p# series with `p_series`/`p_color_series` (703-735; `p_mark_colors` at 736, `p_symbolsizes` at 741 through `resolve_sized`, 457);
  - `expected_directives` (1371) writes the declared stub keys with `declared_cycle` (1431), in the loop at 1465-1467, and the symbol-size cycle with `conv=name_of` (1553);
  - `_STUB_KEY` (1907-1912) drives `_drop_undeclared_stubs` (1915);
  - the command is `python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json` (`--stata-base` defaults to `/Applications/StataNow/ado/base`, 129).
- No shipped `dash-*.scheme` carries a `plabel` key (`grep -l plabel dash-*.scheme` prints nothing).
- `_FALLBACK_PROPS` (5728-5824) has no `gsize plabel`. `test_scheme_fallback_provenance.py` compares every public attribute of `fallback()` with the shipped s2color, so the key is needed once the parser reads it.

### E8 — tests that pin today's behaviour, tests extended, guards

No test pins the default label size or colour, or the colour bar's chrome. `grep -rn '"10px"\|444444\|0.95\|italic' test/*.py` finds none for a LabelSet or a ColorBar. `test_glyphs.py:2006`'s key comparison and `test_mode_parity.py`'s profiles compare both sides alike. S08 moved the explicit-`mlabsize()` pins (F6-F15) in batch 3. 33-09 re-measures the red list on the fixed worktree and flips whatever it finds, with `Flipped:` lines (R9).

Extended, not flipped:
- `test/test_scheme_consumption.py::TestNoParsedKeyIsDiscarded::test_the_key_is_read_somewhere` (:594): add `p_label_colors`, `p_label_alphas`, `p_label_sizes`.
- `test/test_scheme_consumption.py::…::test_the_shipped_file_draws_what_it_drew` (:1536-1554): add `"p_label_colors"` to the colour tuple.
- `test/test_scheme_fidelity.py` `COLOR_LISTS` (:210-215): add `"p_label_colors": ["color p{i}label", "color plabel", "color p{i}", "color p"]`.
- `test/test_help_claims_8.py::TestTheShippedFiles::test_the_directive_count_is_what_the_help_says` (S24's rename of :1013): re-measured bounds (+1 directive in every file, +2 in the nine monochrome ones).
- `test/test_mode_parity.py`: the ColorBar profile (:550-556) gains the chrome fields, the LabelSet profile (:513-520) gains `"alpha": _spec_of(r.text_alpha)`, and three `CORPUS` cases are appended (R8).

Guards that must stay green:
- `test/test_scheme_fallback_provenance.py::TestTheFallbackMirrorsS2color::test_every_style_attribute_matches`;
- `test/test_scheme_fidelity.py::test_regenerating_a_shipped_file_is_a_no_op` and `::test_an_older_translation_loses_its_resolved_stub_lines`;
- `test/test_colorvar_forms.py::…::test_ztitle_suboptions_keep_the_key_title`;
- `test/test_textbox_no_text.py::TestTheFixtureIsPinned` (`t_ztitle_*`);
- `test/test_marker_label_parity.py` (every test);
- `test/test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline`. Expected unchanged, since a single-y page has no label and no key. If it moves, the digest is re-derived with its reason (R10).

### E9 — blast radius (`gitnexus impact <sym> -d upstream -r dash`, 03oct2026)

| Symbol | Risk | Note |
|---|---|---|
| `GlyphMapper._apply_mlabel_opts` | **CRITICAL** (16; 10 direct) | warn; one keyword and a new default block |
| `GlyphMapper._apply_colorvar` | LOW (4; 1 direct) at `c96facd`; listed **HIGH** at index 11.0 | warn as HIGH; one constructor argument |
| `SchemeParser._parse_lines` | **HIGH** (3; 1 direct) | not edited (D-33e); its retention is pinned by guard tests |
| `SchemeParser.resolve_or_fallback`, `_parse_file`, `_include` | HIGH (6 / 3 / 3) | not edited |
| `_dash_apply_z_options` | HIGH (5) | not edited; it runs after S33's defaults |
| `SchemeParser._init_properties` | LOW (1) | one call line. Its real callers are three: `__init__`, `fallback()` and the emitted app |
| `GlyphMapper._immediate_labels` | LOW (4; 2 direct) | one keyword |
| `map_scatter`, `map_pcarrow`, `map_scatteri`, `map_pcarrowi` | LOW (3 each) | one call line each |
| `map_bar`, `map_dropline`, `map_rcapsym`, `map_pcscatter`, `map_pcbarrow`, `map_pccapsym`, `map_rscatter` | UNKNOWN | confirmed by `grep -n`: dispatched through `_dash_glyph_dispatch` (28501) / `_dash_pc_dispatch` in both modes. Recorded unresolved |
| `SchemeParser.__init__` | UNKNOWN ("not found") | confirmed by grep: `resolve_or_fallback` (5856) and tests; not edited (D-33e) |
| `_FALLBACK_PROPS` | UNKNOWN | class constant; read at 5834 and 6439 |
| extractor `extract`, `expected_directives`, `_STUB_KEY` | UNKNOWN / LOW (3) / — | `extract`'s callers are `main()` and `test_scheme_fidelity.py` |

## User stories

- **US-33.1** As a dashboard publisher, I want marker labels drawn in my scheme's label colour, opacity and size (yellow on s1rcolor's black, translucent under sttrans), so my labels read as they do in Stata.
- **US-33.2** As a twoway user with my own scheme, I want `color plabel`, `color p2label`, `gsize plabel` and `gsize p1label` to reach my labels, and `mlabsize(*2)` to double the scheme's size, so a scheme and a do-file written for twoway behave the same in dash.
- **US-33.3** As a dashboard publisher, I want a `colorvar()` colour bar's labels, title and ticks to match my axes, on the graph region, so the key does not show as a white box on a dark or tinted page.
- **US-33.4** As a scheme author, I want every directive in my file kept in the parsed scheme, so a later dash that draws those elements reads them from my file without my changing it.
- **US-33.5** As a twoway user, I want no note about directives dash does not draw yet, so the notes I see are ones I can act on.

## Business requirements

- **BR-33.1** With no label option, a marker label is drawn in the scheme's marker-label colour (`p#label`, else `plabel`, else the plot's colour), at that colour's declared opacity, and at the scheme's marker-label size (`p#label`, else `plabel`) in Stata's text units. The same holds in both modes, before and after any filter move, and on every labelled type, each label taking its own layer's style.
- **BR-33.2** `mlabcolor()` and `mlabsize()` win over the default. A colour without `%NN` keeps the scheme's label opacity, `mlabsize(*#)` multiplies the scheme's size, and `mcolor()`, `color label` and `gsize label` leave labels alone.
- **BR-33.3** A continuous colour key shows its tick labels in the scheme's tick-label size and colour, its title in the axis-title size and colour, upright, and its ticks in the scheme's tick colour, width, length and side, on the graph region with no box of its own, in both modes and after a move. `ztitle()` and `zlabel()` still win.
- **BR-33.4** Every directive a scheme file sets is kept in the parsed scheme under its key with its value, whether dash reads it or not: a user file's own lines, the lines of a user file it `#include`s, and every line of the 26 shipped files, in both modes (the served app's `_SCHEME_PROPS` carries them). Only what Stata itself does not store (`sequence` and `label` lines, tokens after the third) is not stored, as at the base.
- **BR-33.5** No note is printed for a directive dash does not read, for any scheme (shipped, a copy of StataCorp's, user, PLUS or third-party), at parse, at a saved, immediate or served build, or by the served app (ratification row 4, 06oct2026).
- **BR-33.6** A hostile scheme of many unread directives parses in time linear in its lines, prints nothing, and its values are never echoed.
- **BR-33.7** The shipped files carry the marker-label keys their Stata chain declares, and the fallback mirrors s2color's.

## Technical requirements

All in `dash_render.py` unless named. Line numbers are `c96facd`'s; the executor re-finds each by symbol.

- **TR-33.1 The parser's label style** (`SchemeParser`).
  - New method `_init_label_style(self) -> None`, called from `_init_properties` directly after the last `self.p_mark…` assignment S24 left (`grep -n "self.p_markline_alphas" dash_render.py`). It sets:
    - `self.p_label_colors: list[str]` and `self.p_label_alphas: list[float | None]` from `[self._stub_color_alpha(i, "label") for i in range(1, 16)]`;
    - `self.p_label_sizes: list[str]` as `self._gsize(self._first_present((f"gsize p{i}label", "gsize plabel", f"gsize p{i}", "gsize p")) or "gsize plabel", "8pt")` for i in 1..15, calling `_gsize` once per distinct key (a local dict), so an out-of-range `gsize plabel` warns once, not 15 times.

    Everything comes from `_props` alone (served rebuild, critic correction 3).
  - Placement: the new methods `_init_label_style`, `default_mlabel_style` and `colorbar_chrome` go directly after `_stub_color_alpha`. None is beside `plot_line_width` (where S32 inserts `style_bundle`) or `apply_to_axis` (S31's), so the batch's hunks stay apart.
  - New method `default_mlabel_style(self, index: int) -> "tuple[str, float | None, str]"`: `(p_label_colors[i], p_label_alphas[i], p_label_sizes[i])` with `i = int(index) % 15`, as `default_color` wraps.
  - `_FALLBACK_PROPS` gains `"gsize plabel": "small"` beside the other `gsize` keys (s2color sets no `color plabel`).
- **TR-33.2 The applier** (`GlyphMapper._apply_mlabel_opts`).
  - Add the keyword `color_idx: int = 0` after S08's `radius_px`.
  - Before the `kwargs` dict, read `_lc, _la, _ls = self.scheme.default_mlabel_style(color_idx)`. Set `text_font_size=_ls` (replacing `"10px"`) and `text_color=_lc`. When `_la is not None`, set `kwargs["text_alpha"] = float(_la)`.
  - The `mlabcolor` branch sets only `text_color`; it does not touch `text_alpha` (D-33h). The `mlabsize` branch is S08's and unchanged; it now multiplies the scheme's size.
  - Keep every line S08 and S29 left. Update the docstring: defaults from the scheme's marker-label keys (D-33a, E6).
- **TR-33.3 The calls.**
  - Each of the 11 calls (E2) passes `color_idx=color_idx`.
  - `_immediate_labels` gains `color_idx: int = 0`, forwards it to its call (14418), and receives `color_idx=color_idx` from `map_scatteri` (13725) and `map_pcarrowi` (14462).
  - Nothing else in those functions changes. The A139 note is Q1.
- **TR-33.4 The colour key.**
  - New `SchemeParser.colorbar_chrome(self) -> "dict[str, Any]"` returns:
    - `background_fill_alpha: 0.0`;
    - `major_label_text_font_size: self.tick_label_font_size`, `major_label_text_color: self.tick_label_color`;
    - `title_text_font_size: self.axis_title_font_size`, `title_text_color: self.axis_title_color`, `title_text_font_style: "normal"`;
    - `major_tick_line_color: self.tick_color`, `major_tick_line_width: self.tick_line_width`;
    - `major_tick_in`/`major_tick_out` from `self.tick_length_px` and `self.tick_position`, by S15's rule (outside 0/L, inside L/0, crossing L/2 each), computed inline in `colorbar_chrome` as Bokeh `Int`s with S31's rounding: `n = int(round(min(abs(L), 100.0)))` (non-finite L gives 0), `h = int(round(min(abs(L), 100.0) / 2.0))`. S33 does not edit `apply_to_axis` or extract a helper from it (S31 edits it this batch), and does not call S31's `_dash_tick_geometry` (absent from S33's worktree). `TestTheColourKeyTakesTheSchemeChrome::test_the_tick_pair_is_the_axis_rule` holds the two equal on the merged tree.
  - In `_apply_colorvar` the `ColorBar(…)` call (9243-9245) adds `**self.scheme.colorbar_chrome()`. `label_standoff`, `width`, `location` and `title` are kept. `bar_line_color` stays None (D-33c).
- **TR-33.5 Directive retention (no code change; ratification row 4, D-33d).**
  - `_parse_lines`, `_parse_file`, `_include` and `SchemeParser.__init__` are not edited, and `_props` stays the plain `dict` `_parse_file` returns (D-33e).
  - No note, list, count or read-recording is added (D-33e, D-33f).
  - `TestUnreadDirectivesAreRetained` and `TestNoNoteForUnreadDirectives` (guards, green at the base and after) pin that every parsed directive stays under its key with its value, in `_props` and in the served `_SCHEME_PROPS`, and that nothing is noted.
- **TR-33.6 The extractor** (`scripts/extract_scheme_truth.py`).
  - In `extract`, add:
    - `p_label_colors = p_color_series("p_label_colors", "label")`;
    - `p_label_sizes = p_series("p_label_sizes", "gsize", "label", lambda t: resolve_sized(r, "gsize", t))`.

    Return both in the result dict.
  - In `expected_directives`, add `("label", "p_label_colors")` to the colour stub loop (1465-1467). Add a group "Marker-label size gsize p#label: only the keys this scheme's #include chain declares (style/textboxstyle-p#.style: set size scheme p#label)" with `declared_cycle("gsize", "label", "p_label_sizes", False, conv=name_of)`.
  - In `_STUB_KEY`, add `label` to the `color` alternation S24 left and add `"gsize": re.compile(r"p\d+label")`.
- **TR-33.7 Regeneration** (A152, R7). Run TR-33.6's command. All 26 files gain `gsize plabel small`; the nine monochrome files also gain `color plabel #000000`. `scheme_truth.json` gains the new keys. Every other record is unchanged (33-05's check). Never hand-edit.
- **TR-33.8 The layer-truth extractor** (`scripts/extract_scheme_layer_truth.do`, S24's), as "Stata truth" specifies.
- **TR-33.9 Both modes, copy lists, JavaScript.**
  - Every new name is a `SchemeParser` or `GlyphMapper` member and travels with its class (class loop 33436-33438). R2 row S33: no constant or function added to either `_glyph_layer_lines` tuple, and no `_shared_stat_lines` change.
  - `_dash_build_scheme` is unchanged; the app's parser is built from `_SCHEME_PROPS`, which holds every parsed directive (D-33d).
  - No saved-page script reads or writes a label or key style, so there is no JavaScript twin. `TestAfterAFilterMove::test_no_saved_script_writes_label_or_key_style` pins that.
  - `TestTheServedAppCarriesEveryName` (with S01's `test_every_listed_name_exists`) and `TestTheServedAppDefinesEveryNameItReads` stay green (G4).
- **TR-33.10 Maps** (A148, X.5). `test/function_test_map.py`, under S33's anchor, alphabetically:
  - `'SchemeParser._init_label_style': 'test/test_label_key_chrome.py::TestTheParsersLabelStyle::test_props_alone_give_the_attributes'`
  - `'SchemeParser.colorbar_chrome': 'test/test_label_key_chrome.py::TestTheColourKeyTakesTheSchemeChrome::test_the_chrome_dict'`
  - `'SchemeParser.default_mlabel_style': 'test/test_label_key_chrome.py::TestTheParsersLabelStyle::test_the_index_wraps_at_fifteen'`

  Retention adds no function, so the retention tests map no key. No Stata program changes, so `program_coverage_map.py` is untouched.
- **TR-33.11 Help** (`dash.sthlp`, R3): the paragraphs and text of Notes, "Text for the closing task".
- **TR-33.12 Security (rule 1).**
  - S33 prints no new text from a scheme file: no note, and no key or value is echoed.
  - Retention adds no work: the parse stays one dict store per line, as at the base. `TestHostileSchemes::test_a_large_file_is_kept_and_silent` bounds a 30,000-line file at 2 s.
  - No `shell=True`. The fixture's python block never interpolates file text into code.

## Boundaries

- **Batch partners.**
  - S31 owns the axis parse and apply functions and any `z`-axis sub-option reaching the colour bar through `_dash_apply_z_options`.
  - S31 also owns `SchemeParser.apply_to_axis` and `apply_to_figure` (its `_dash_scheme_look`/`_dash_scheme_colours` stamps) and `_dash_tick_geometry`. S33's `colorbar_chrome` computes its tick pair inline (TR-33.4) and edits none of them.
  - S32 owns `_apply_marker_opts`, `_apply_line_opts`, `_apply_fill_opts`, `style_bundle`, `_dash_plot_style_indices`, the plot syntax, the colour reads of map_area, map_bar, `_histogram_quads`, map_rarea, map_rbar, map_dropline, map_rcapsym, map_scatteri, map_pcarrow and map_pcbarrow, and the `role="aline"` call sites (map_pccapsym among them). S33 adds only the `color_idx=` keyword on the `_apply_mlabel_opts`/`_immediate_labels` call line inside seven of them (eight if S32 edits `map_scatter`; maintainer question in Notes), and nothing else there.
- **Later sections.**
  - S34: ado-path lookup, `_resolve_path`, `resolve_or_fallback`, `_include`'s walk, and per-graph served scheme dicts. An ado-path file's directives are retained like any other, with no note (D-33d).
  - S36: other style names.
  - S37: `mlabvposition()`, `mlabtextstyle()`, and `clockdir p#` as a label position, if it reads it.
  - S43: bare `*#`/`%#` and `mlabcolor(red%70)`'s opacity.
  - S53: the by() colour key, which inherits this chrome.
  - P2.10: clegend options, the key's title orientation, the one-sided axis line and the bar width.
  - P2.55: user `.style` files.
- **Not edited:**
  - `_apply_marker_opts`, `_apply_line_opts`, `_apply_fill_opts`;
  - `_dash_apply_z_options`, `_dash_style_note`, `_dash_warn_once`;
  - `_parse_lines`, `_include`, `_parse_file`, `SchemeParser.__init__`, `_resolve_path`, `resolve_or_fallback`, `fallback`;
  - `_make_figure_body`, `_generate_app_source`, the `_glyph_layer_lines` tuples, `_FILTER_JS`;
  - dash.ado, dash_parse.mata, `scripts/svg_truth.py`, `scripts/svg_layer.py`;
  - any runner block or hygiene pin, and any tracking document beyond BUGS.md and CHANGELOG.md (A145).
- **Exclusions.**
  - The discrete colour key (a `Legend`) keeps the legend chrome.
  - No directive dash does not read is noted, and none is dropped (ratification row 4). A later section that starts drawing one reads it from `_props`, where it already is.

## Stata truth

**Extended extractor** `scripts/extract_scheme_layer_truth.do` (S24's; D-33g). It writes the same fixture, `test/fixtures/scheme_layer_truth.json`; `git add -f` is needed again (`.git/info/exclude:58`).
- S24's root rule, first lines (`adopath ++ "<root>/"`, `global dash_nobrowser 1`, `version 19`), `c(python_exec)` exit and D12 stamp all stay.
- Add, in S24's tempfile-named scheme directory, `scheme-<n>.scheme` for each user file, each starting `#include s2color`:

  | File | Lines after the include |
  |---|---|
  | w33a | `color plabel green`, `gsize plabel large` |
  | w33b | `color p1label blue`, `gsize p1label vlarge`, `color plabel green` |
  | w33c | `color label white`, `gsize label huge` |
  | w33d | `color p1 red` |
  | w33k | `gsize axis_title vlarge`, `color axis_title red`, `gsize tick_label small`, `color tick_label blue` |
  | w33t | `color axisline orange`, `color tick purple`, `color clegend_line green`, `color clegend blue` |

- Run: `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_scheme_layer_truth.do"`, with the log at `$S/extract_scheme_layer_truth.log`.

**Probes** (S24's `_sk_probe <id> <group> <scheme> <command>`, ids prefixed `s33_`; data `sysuse auto` with S24's `lo`/`hi`):

| Group | Commands (`twoway …`) | Schemes |
|---|---|---|
| mlabel | `(scatter mpg weight in 1/3, mlabel(make))` | s2color, s1rcolor, stcolor, s1mono, economist, sttrans, s2mono, stmono1 |
| mlabel_chain | the same command (w33a, w33c, w33d); `(scatter mpg weight in 1/3, mlabel(make)) (scatter price weight in 1/3, mlabel(make) yaxis(2))` (w33b); `… , mlabel(make) mcolor(red)`, `… mlabsize(*2)`, `… mlabcolor(red)` (s2color); `… mlabcolor(red)`, `… mcolor(red)` (sttrans) | as named |
| mlabel_types | `(scatter mpg weight in 1/3) (<t>, mlabel(make))` for `bar mpg weight in 1/3`, `dropline mpg weight in 1/3`, `rcapsym lo hi weight in 1/3`, `rscatter lo hi weight in 1/3`, `pcscatter mpg weight price length in 1/3`, `pcarrow mpg weight price length in 1/3`, `pcbarrow mpg weight price length in 1/3`, `pccapsym mpg weight price length in 1/3`, `connected mpg weight in 1/3`; `(scatter mpg weight in 1/3) (scatteri 20 3000 "lab")`; `(scatter mpg weight in 1/3) (pcarrowi 20 3000 30 4000 "lab")` | s2color |
| colorkey | `scatter mpg weight, colorvar(price)` | s2color, s1manual, s1rcolor, economist, w33k, w33t |

**The python block** adds a reader `_s33_texts(path)`:
- `svg_truth.svg_document(path)` gives `texts`, `canvas`, `plotregion`, `hlines` and `vlines`; rs = min(canvas w, h)/100;
- each text gets `{"text", "fill", "opacity", "size_rs", "rotate", "anchor", "x"}`. `opacity` is read from the element's `style` with the bounded regex `opacity:([0-9.]{1,8})`, None when absent;
- for `colorkey` probes, the lines with both x ≥ `plotregion.right` + 1 are added as `{"stroke", "width_rs", "length_rs", "vertical"}`;
- it never calls Stata, never uses `shell=True`, and writes a backtick as `\x60`.

**Fixture keys added** (S24's are kept byte-identical outside `_meta`):

```
"probes": {"s33_<group>_<tag>": {"group", "scheme", "command", "rc",
            "texts": [...], "key_lines": [...]   (colorkey only)}},
"derived": {"s33": {
   "label": {scheme: {"fill", "opacity", "size_rs"}},                      (mlabel; first label)
   "chain": {tag: [[fill, size_rs, opacity], ...]},                       (one entry per layer, document order, 3 labels per layer)
   "types": {ptype: fill},                                               (the second layer's label)
   "key": {scheme: {"label_fill", "label_rs", "title_fill", "title_rs", "title_rotate",
                    "tick_stroke", "tick_len_rs", "tick_side", "axis_stroke"}}}}
```

E6 gives the expected values. A difference is investigated and reported, never patched (R7). E6's unread-key probes are not re-run: by ratification row 4 nothing is drawn or noted for them, so the fixture records no `unread` group.

**Truth block** (`test/test_wp30_truth.cscript`, S33's stub, between `* ==== S33 P1.4b: Marker-label and colour-key chrome; unread directives retained ====` and `* ==== end S33 ====`, gated by `local only : env WP30_ONLY` and `` if inlist("`only'", "", "S33") { ``):
- Helpers directly above the header, each `version 19`. `_s33_tw <svg>` runs `_s33_texts` into globals. A python function `_s33_both(tag)` follows WP-29's S12 form (test_wp29_truth.cscript:4450-4540): `DashRenderer` and an exec'd `ServerAppBuilder` app from `_dash_serve_spec, specpath() datapath() scheme()`. It returns, per mode, the first LabelSet of each layer (`text_color|text_alpha|size_rs`) and the ColorBar's `label colour|label rs|title colour|title rs|tick colour`, and `S33_SAME_AFTER` (1 when the served values are unchanged after a `Select` move on `foreign` to `Foreign`).
- User files go under `` `w30_work' `` as both `scheme-<n>.scheme` (twoway) and `<n>.scheme` (dash's working-directory lookup at batch 11). The block `cd`s there for dash and back before its end line.

| Case | Check |
|---|---|
| MK-01 | s1rcolor `(scatter mpg weight in 1/3, mlabel(make))`: twoway's label fill `#ffff00` equals dash's `text_color` in both modes, and the sizes agree within 1% |
| MK-02 | w33b: layer 1 `#0000ff` at vlarge, layer 2 `#008000` at small, twoway and both modes |
| MK-03 | sttrans: twoway's label opacity 0.20 equals dash's `text_alpha` in both modes |
| MK-04 | w33k `scatter mpg weight, colorvar(price)`: twoway's key labels `#0000ff` at small and title `#ff0000` at vlarge equal dash's ColorBar label and title colour and size in both modes |
| MK-05 | `S33_SAME_AFTER` = 1 for MK-01's and MK-04's commands |

**Area script** (`test/test_custom_scheme.cscript`: messages, R1), appended as one run after its last case block. It uses the existing `_cs_run`, `_cs_log`, S06's `_cs_notes`, `_cs_expect` and `_cs_done`, with `w33s.scheme` (`#include s2color`, then `textboxstyle title subheading`, `textboxstyle axis_title heading`, `clockdir p 9`, `yesno plabelboxed yes`, `textboxstyle key_label heading`, `textboxstyle tick heading`) and `w33m.scheme` (`#include s2color` then `clockdir p<i> 9` for i = 1..15, `clockdir p 9`, `textboxstyle tick heading`) written into `cs_dir`:

| Case | Check |
|---|---|
| MK-06 | `dash scatter mpg weight, scheme(w33s) saving(a.html, replace)`: rc 0; `_cs_notes` 0 |
| MK-07 | two registrations then `dash build, scheme(w33s) saving(b.html) replace`, and `dash build, scheme(w33s) saving(c15.py) server replace`: rc 0 each; `_cs_notes` 0 each |
| MK-08 | `scheme(w33m)` on the immediate route: rc 0; `_cs_notes` 0 |

## TDD test stubs

**Regression tests written by 33-01** (twoway's literal values from E6; red at the batch-11 base). Modes come from `test_scheme_resolution._draw`/`MODES`, specs from `test_mode_parity._spec` with `test_server_layer_defects.plot_for`, user schemes from `test_scheme_review_fixes._user_scheme`, and moves from `test_served_linked_views._served_doc(tmp_path, spec)` with `test_served_linked_views._fire(doc, "foreign", <value>)`. Labels use `mlabel(mpg)` (the test data have no `make`). A size is compared as `OptionTranslator.css_to_pt(size) / OptionTranslator.PT_PER_RS` against twoway's rs, within 1%.

`test/test_label_key_chrome.py` (new):
- Test: s2color, s1rcolor, stcolor, s1mono, economist and sttrans labels match E6's table (fill, size rs 2.776, sttrans `text_alpha` 0.2) — `TestMarkerLabelsTakeTheSchemeLabelStyle::test_the_default_label_style[scheme-mode]`
- Test: w33a gives `#008000` at 4.861 rs — `TestTheLabelChain::test_plabel_reaches_every_layer[mode]`
- Test: w33b gives layer 1 `#0000ff` at 5.556 and layer 2 `#008000` at 2.778 — `TestTheLabelChain::test_p1label_reaches_layer_one_only[mode]`
- Test: w33c gives `#1a476f` at 2.778 — `TestTheLabelChain::test_color_label_is_not_a_marker_label_key[mode]`
- Test: w33d gives `#ff0000` — `TestTheLabelChain::test_color_p1_reaches_the_label[mode]`
- Test: s2color `mcolor(red)` gives the label `#1a476f` — `TestTheLabelChain::test_mcolor_leaves_the_label[mode]`
- Test: `(scatter)(bar, mlabel)(pcarrow, mlabel)` gives `#90353b` and `#55752f` — `TestEveryLabelledTypeTakesItsLayersColour::test_bar_and_pcarrow_as_measured[mode]`
- Test: sttrans `mlabcolor(red)` gives `#ff0000` with `text_alpha` 0.2 — `TestTheOptionsStillWin::test_mlabcolor_keeps_the_schemes_opacity[mode]`
- Test: s2color `mlabsize(*2)` gives 5.556 rs — `TestTheOptionsStillWin::test_mlabsize_star_multiplies_the_schemes_size[mode]`
- Test: the colour bar under s2color, s1manual, s1rcolor and economist matches E6's key table (label and title fill and rs) with `title_text_font_style == "normal"` — `TestTheColourKeyTakesTheSchemeChrome::test_the_key_text[scheme-mode]`
- Test: `background_fill_alpha == 0` — `TestTheColourKeyTakesTheSchemeChrome::test_the_key_sits_on_the_graph_region[mode]`
- Test: under s2color, `major_tick_line_color == scheme.tick_color`, `major_tick_line_width == scheme.tick_line_width`, `major_tick_in == 0` and `major_tick_out == round(scheme.tick_length_px)` — `TestTheColourKeyTakesTheSchemeChrome::test_the_ticks_are_the_schemes[mode]`
- Test: w33k's labels are `#0000ff` at 2.778 and its title `#ff0000` at 5.556; w33t's ticks are `#800080` — `TestTheColourKeyTakesTheSchemeChrome::test_a_user_schemes_text_and_tick_keys[mode]`
- Test: after a served `Select` move, the first LabelSet is still s1rcolor's `#ffff00` at small and the ColorBar's labels still `#ffffff` — `TestAfterAFilterMove::test_the_served_label_and_key_keep_their_style`
- Test (unit): for s2color (outside), economist (inside) and a `_props_scheme` parser whose tick position is crossing at an odd length, `colorbar_chrome()`'s `major_tick_in`/`major_tick_out` equal those `apply_to_axis` sets on a fresh `LinearAxis` from the same parser — `TestTheColourKeyTakesTheSchemeChrome::test_the_tick_pair_is_the_axis_rule[scheme]`
- Test: s1manual `ztitle(, size(*2))` draws the title at 2 × 3.901 rs within 1% (S08's TR-08.10 multiplies the size on the model, now the scheme's axis-title size; the rule E6 measured for `mlabsize(*2)`) — `TestTheColourKeyTakesTheSchemeChrome::test_ztitle_star_multiplies_the_schemes_title[mode]` (red at the base; kept out of the `ZOptions` guard class that 33-01's verify requires green)
- Test (unit): `colorbar_chrome()` has exactly TR-33.4's keys, with s2color's values — `TestTheColourKeyTakesTheSchemeChrome::test_the_chrome_dict`
- Test (unit): a parser built by `test_scheme_resolution._props_scheme({"gsize plabel": "large", "color p2label": "red"})` has `p_label_sizes[0] == "14pt"` and `p_label_colors[1] == "#ff0000"` — `TestTheParsersLabelStyle::test_props_alone_give_the_attributes`
- Test (unit): `default_mlabel_style(15) == default_mlabel_style(0)`, and index 1 is p2's — `TestTheParsersLabelStyle::test_the_index_wraps_at_fifteen`

`test/test_unread_scheme_directives.py` (new; every test is a guard, green at the base and after, D-33d; user files through `_user_scheme`, module constants `W33S`, `W33Q`, `W33M`, `W33INC` with E6's lines):
- Test: `w33s` (`#include s2color`, then E6's six w33s lines) parses with each of its six directives in `sp._props` under its key with the file's value (`textboxstyle title` → `subheading`, `clockdir p` → `9`, `yesno plabelboxed` → `yes`, …), and `w33q` (`clockdir p1 9`, `yesno p1labelboxed yes`, `textboxstyle subtitle heading`, `textboxstyle caption heading`) likewise — `TestUnreadDirectivesAreRetained::test_a_user_schemes_directives_are_kept`
- Test: a two-token line `w33default zz` in a user file is kept as `sp._props["w33default"] == "zz"` (6382-6383's class-default form) — `TestUnreadDirectivesAreRetained::test_a_class_default_line_is_kept`
- Test: a user file `#include w33inc` (in cwd, holding `clockdir p 9` and `textboxstyle tick heading`) keeps both in the including parser's `_props` — `TestUnreadDirectivesAreRetained::test_an_included_user_files_directives_are_kept`
- Test: for each of the 26 shipped names, every directive of its `dash-<n>.scheme` (tokenised with `SchemeParser._scheme_tokens`, `sequence` and `label` lines skipped, the last value of a repeated key) is in `SchemeParser(n)._props` with that value; the failure text names any of the five shipped-but-unread keys (`color foreground`, `gsize text`, `yesno draw_major_grid`, `yesno draw_minor_grid`, `linepattern plotregion`) that is missing — `TestUnreadDirectivesAreRetained::test_a_shipped_schemes_unread_keys_are_kept[name]` (26)
- Test: the served rebuild carries them: the `_SCHEME_PROPS` literal in the source `ServerAppBuilder(sp, dp).build(app)` writes for scheme `w33s` (`ast.literal_eval` of its right-hand side) holds w33s's six directives with their values — `TestUnreadDirectivesAreRetained::test_the_served_app_carries_them`
- Test: `SchemeParser` for `w33s`, `w33q` and `w33m` under `warnings.catch_warnings(record=True)` with `simplefilter("always")` records no warning — `TestNoNoteForUnreadDirectives::test_parsing_is_silent`
- Test: `plot_for("scatter", {"mlabel": "mpg"})` drawn through `test_scheme_resolution._draw` with scheme `w33s` in both `MODES`, and an exec'd served app's `make_document`, record no `UserWarning` whose text starts `dash scheme:` — `TestNoNoteForUnreadDirectives::test_builds_are_silent[mode]`
- Test: 30,000 lines cycling `clockdir p1`…`p15 9` parse within 2 s, record no warning, and keep the 15 keys at `9` — `TestHostileSchemes::test_a_large_file_is_kept_and_silent`

**Fixture-driven tests added by 33-03** (red before the fix):
- `test/test_label_key_chrome.py::TestTheFixture::test_the_s33_probes_are_recorded` (rc 0, every group present, the `_meta` stamp; passes once 33-02 ran)
- `test/test_label_key_chrome.py::TestMarkerLabelsAgainstTheFixture::test_each_probe[probe-mode]` (`derived.s33.label` and `chain`)
- `test/test_label_key_chrome.py::TestEveryLabelledTypeTakesItsLayersColour::test_the_second_layer[ptype-mode]` (`derived.s33.types`, all 11 types)
- `test/test_label_key_chrome.py::TestTheColourKeyAgainstTheFixture::test_each_probe[probe-mode]` (`derived.s33.key`)

**Added by 33-04 and 33-06** (red until the regeneration and the parser change):
- `test/test_label_key_chrome.py::TestTheParsersLabelStyle::test_each_shipped_scheme_matches_the_fixture[name]` (26: colours, opacities and `css_to_pt(p_label_sizes[i]) == p_label_sizes[i]["pt_at_4in"]`)
- `test/test_label_key_chrome.py::TestTheParsersLabelStyle::test_the_fallback_mirrors_s2color`

**Guard tests** (pass before and after; listed separately in the failure file), with every test of `test/test_unread_scheme_directives.py` above:
- `test/test_label_key_chrome.py::TestTheOptionsStillWin::test_mlabsize_keyword_wins[mode]` (`large` gives 4.861 rs)
- `TestZOptionsStillWin::test_ztitle_and_zlabel_win[mode]` (`ztitle(, size(large) color(red))` and `zlabel(, labsize(small))` set the ColorBar title and labels)
- `TestAfterAFilterMove::test_no_saved_script_writes_label_or_key_style` (no `CustomJS.code` of a built saved page and no module JavaScript string holds `text_color`, `text_font_size`, `text_alpha`, `major_label_text`, `title_text` or `major_tick_line`)

**Added by 33-12:** `test/test_unread_scheme_directives.py::TestTheHelpSaysTheyAreKept::test_kept_without_a_note` (dash.sthlp's "What a scheme file of yours may include" holds `kept with the scheme, without a note`, and no line holds `twoway draws and dash does not`).

**Pinned tests to flip:** none known at `c96facd` (E8). 33-09 re-measures and flips any it finds (R9).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Default label colour, opacity, size; chain; options | pytest `test_label_key_chrome.py`; cscript MK-01..MK-03 | `scheme_layer_truth.json` (`s33` label, chain) | yes, and the served move |
| Every labelled type uses its layer's style | pytest `TestEveryLabelledTypeTakesItsLayersColour` | `s33.types` | yes |
| Colour-key chrome; z options win | pytest; cscript MK-04 | `s33.key` | yes, and the served move |
| No saved script writes a label or key style | pytest guard | — | saved |
| Parser attributes, fallback, shipped files | pytest `TestTheParsersLabelStyle`, `test_scheme_fidelity.py`, `test_scheme_consumption.py`, `test_scheme_fallback_provenance.py` | `scheme_truth.json` | — |
| Unread directives retained (user, included and shipped files; served dict) and silent; hostile input | pytest `test_unread_scheme_directives.py`; cscript MK-06..MK-08 | — | saved, immediate, served build and app |
| Parity | `test_mode_parity.py` (3 new CORPUS cases; ColorBar and LabelSet profile fields) | — | yes (G3) |
| Registries | `test_function_test_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_cscript_hygiene.py`, `test_tracking_documents.py` | — | — |
| Help | `test_help_claims_8.py`, `TestTheHelpSaysTheyAreKept` | — | — |

**Acceptance criteria.**
- **AC-33.1** Under every probe of `s33.label` and `s33.chain`, dash's first LabelSet per layer has twoway's fill (case-folded), opacity and size (within 1%), in both modes and after a served move. MK-01 to MK-03 print PASS.
- **AC-33.2** On each of the 11 labelled types, the second layer's labels take twoway's p2 colour in both modes.
- **AC-33.3** Under every `s33.key` probe, the ColorBar's label and title colour and size match twoway's, the title is `normal`, `background_fill_alpha` is 0, and the ticks are the scheme's, in both modes. `ztitle()`/`zlabel()` still win. MK-04 and MK-05 print PASS.
- **AC-33.4** Every directive of w33s, w33q, a user `#include` file and each of the 26 shipped files is in the parsed `_props` under its key with its value, and w33s's are in the served app's `_SCHEME_PROPS`. `TestUnreadDirectivesAreRetained` passes at the base and after.
- **AC-33.5** No note for any directive dash does not read, for any scheme, at parse, at a saved, immediate or served build, or in the served app. `TestNoNoteForUnreadDirectives` and `TestHostileSchemes` pass; MK-06 to MK-08 print PASS.
- **AC-33.6** The 26 files carry `gsize plabel` (and `color plabel` in the nine monochrome ones). A second extractor run is a no-op. Every other fixture record is unchanged.
- **AC-33.7** `test_mode_parity.py`, the registries and the full suite are green, and `grep -c '<!-- WP-30 P1.4b -->' CHANGELOG.md` prints 0.

## Tasks

**Commit boundary.** Tasks 33-01 to 33-13 form the one commit of entry `P1.4b`, subject `Take marker-label and colour-key text from the scheme (WP-30 P1.4b)`.
- It is made by 33-13 on `wp30-s33` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s33` (`$WT`), after one full run through the queue.
- `$S` is `<scratch>/s33` (`<scratch>`: the orchestrator's WP-30 scratch directory, index "Deltas"). Every command runs from `$WT` unless it names the main checkout.
- The body:
  1. opens with `<scratch>/33-P1.4b-failure.txt`;
  2. then the measured defect (E5) and what changed, where, in both modes;
  3. then one line each:
     - `Regression: test/<file>.py::<Class>::<test> -- failed at <batch-11 base sha> with <text>`, one per regression class;
     - `Flipped: <node> -- <old expectation> was wrong because <why>`, one per line of `$S/33-flips.txt`;
     - `Fixture: test/fixtures/scheme_layer_truth.json (scripts/extract_scheme_layer_truth.do)`;
     - `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`;
     - `BUGS.md: "Marker-label size and colour are fixed, the colour key has no scheme chrome, and unread user-scheme directives are ignored silently" (closed)` (section-01 Appendix B's title, verbatim; it equals `WP30_OPEN["P1.4b"]`);
     - a `Rebaselined:` line only if a combined pin moved (R10).

No subject, body, BUGS line, CHANGELOG line or help line names a tool or vendor (G7). `grep -Eic 'claude|anthropic'` prints 0 on the message file before committing and on `git log -1 --format=%B` after. Never stage `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.ultraplan/` or any `*.html` (E7, G6).

<task type="auto" id="33-01">
  <name>Write the failing label, key and note tests</name>
  <files>test/test_label_key_chrome.py, test/test_unread_scheme_directives.py</files>
  <action><![CDATA[
    Run `mkdir -p "$S"`. Check that `git -C $WT rev-parse HEAD` equals `<scratch>/batch-11-base.txt` and that `git -C $WT branch --show-current` prints `wp30-s33`; otherwise stop.
    Read `<scratch>/batch-11-impact.txt` and confirm it records, with approval (index 11.0):
    - the CRITICAL warning for `_apply_mlabel_opts`;
    - HIGH for `_apply_colorvar` and `_parse_lines`.
    For any symbol missing from it (`_immediate_labels`, `_init_properties` and E9's mappers), run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout (never in $WT), append the result and report before editing.
    Check the predecessors in $WT with `grep -nE 'def resolve_size|def css_to_pt|def css_pt|PT_PER_RS' dash_render.py` (S08), `grep -n 'radius_px' dash_render.py` (S08's applier keyword), `grep -nE 'self\.(tick_color|tick_line_width|tick_length_px|tick_position)\b' dash_render.py` (S15), `grep -n 'def _dash_emit_note' dash_render.py` (S06), `test -f scripts/extract_scheme_layer_truth.do && test -f test/fixtures/scheme_layer_truth.json` (S24) and `grep -n 'self.p_markline_alphas' dash_render.py` (S24). If any is missing or renamed, stop and report.
    Create both files with every test of "TDD test stubs" under "Regression tests written by 33-01", "`test/test_unread_scheme_directives.py`" and "Guard tests". Use exactly those class and test names and the helpers named there, with twoway's literal values from E6. Put the user-scheme lines in module constants named `W33A` … `W33M` and `W33INC`, matching "Stata truth" and E6. If a retention or silence test fails here, the base has changed (D-33d): stop and report; do not edit `_parse_lines`.
    Run `python3 -m pytest test/test_label_key_chrome.py test/test_unread_scheme_directives.py -q -n0 -p no:cacheprovider -rf > "$S/33-01.log" 2>&1`.
    Write `<scratch>/33-P1.4b-failure.txt` with the base sha, then each FAILED line with its first assertion text, then the guard tests under "Guard tests (pass before and after)". Do not touch dash_render.py, and do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/33-01.log"` prints at least 40; `grep -E '^FAILED.*(test_unread_scheme_directives|keyword_wins|ZOptions|no_saved_script)' "$S/33-01.log"` prints nothing; `python3 -m pytest test/test_unread_scheme_directives.py -q -n0 -p no:cacheprovider` passes; `test -s <scratch>/33-P1.4b-failure.txt`.]]></verify>
  <done>Every 33-01 regression test existed with twoway's literal values and failed on the unfixed tree, the guards passed, and the failure text was saved.</done>
</task>

<task type="auto" id="33-02">
  <name>Extend the layer truth extractor and rerun it</name>
  <files>scripts/extract_scheme_layer_truth.do, test/fixtures/scheme_layer_truth.json</files>
  <action><![CDATA[
    Edit S24's scripts/extract_scheme_layer_truth.do exactly as "Stata truth" specifies:
    - the six user files, written with `file write` into S24's tempfile-named scheme directory;
    - the four probe groups through `_sk_probe`, with ids `s33_<group>_<tag>`;
    - `_s33_texts` and the `derived.s33` block, inside the existing python block, after S24's code.
    Change none of S24's lines or probes. Run `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_scheme_layer_truth.do"` and read `$S/extract_scheme_layer_truth.log`.
    Write `$S/33-layer-check.py`, which compares the new fixture with `git show HEAD:test/fixtures/scheme_layer_truth.json`:
    - every probe id not starting `s33_` and every `derived` key other than `s33` must be equal;
    - only `_meta` may differ.
    Save its output to `$S/33-layer-check.txt`. Check `derived.s33` against E6:
    - s1rcolor label `#ffff00`; sttrans opacity 0.2;
    - w33b `[[#0000ff, 5.556], [#008000, 2.776]]` within 1%;
    - types bar `#90353b`;
    - key s1manual title 3.901 and labels 3.301.
    A difference is investigated and reported, never patched (R7). Run `git add -f test/fixtures/scheme_layer_truth.json`.
  ]]></action>
  <verify><![CDATA[`grep -c '^r(' "$S/extract_scheme_layer_truth.log"` prints 0; `tail -1 "$S/33-layer-check.txt"` reads `unchanged: <N> S24 probes` with N the count at HEAD; `python3 -c "import json;d=json.load(open('test/fixtures/scheme_layer_truth.json'));s=d['derived']['s33'];print(sorted(s), s['label']['s1rcolor']['fill'])"` prints the four group keys (`chain`, `key`, `label`, `types`) and `#ffff00`.]]></verify>
  <done>scheme_layer_truth.json carried the S33 probes from live twoway exports, S24's records were unchanged, and the file was staged with git add -f.</done>
</task>

<task type="auto" id="33-03">
  <name>Add the fixture-driven label and key tests</name>
  <files>test/test_label_key_chrome.py</files>
  <action><![CDATA[
    Add the four tests of "Fixture-driven tests added by 33-03". They read `test/fixtures/scheme_layer_truth.json` and are parametrized over its `s33_*` probe ids and the two `MODES`. Each draws the probe's command as a dash spec with the same scheme (user files through `_user_scheme`) and compares as the literal tests do. Run the file with `-rf` into `$S/33-03.log`. Append the new FAILED lines (all but `test_the_s33_probes_are_recorded`, which passes) to `<scratch>/33-P1.4b-failure.txt` under "Fixture-driven (before the fix)". Do not touch dash_render.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_label_key_chrome.py::TestTheFixture -q -n0 -p no:cacheprovider -k probes_are_recorded` passes; `grep -c 'Fixture-driven (before the fix)' <scratch>/33-P1.4b-failure.txt` prints 1.]]></verify>
  <done>The fixture-driven tests existed, failed on the unfixed code where dash differs, and were recorded in the failure text.</done>
</task>

<task type="auto" id="33-04">
  <name>Teach the extractor the label keys</name>
  <files>scripts/extract_scheme_truth.py, test/test_scheme_fidelity.py</files>
  <action><![CDATA[
    Make TR-33.6 in scripts/extract_scheme_truth.py: `p_label_colors` and `p_label_sizes` in `extract`; the `label` colour stub and the `gsize p#label` group in `expected_directives`; and `_STUB_KEY`. In test/test_scheme_fidelity.py add the `COLOR_LISTS` row of E8.
  ]]></action>
  <verify><![CDATA[`python3 -c "import sys;sys.path.insert(0,'scripts');import extract_scheme_truth as x;e=x.extract(x.DEFAULT_STATA_BASE,'s1mono');f=x.extract(x.DEFAULT_STATA_BASE,'stcolor');print(e['p_label_colors'][0],e['p_label_sizes'][0]['name'],f['p_label_colors'][0])"` prints `#000000 small #1a85ff`.]]></verify>
  <done>The extractor resolved the marker-label colour and size chains for every scheme.</done>
</task>

<task type="auto" id="33-05">
  <name>Regenerate the 26 shipped scheme files</name>
  <files>dash-*.scheme (the 26), test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    Run `python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json`. Write `$S/regen_check.py` and save its output to `$S/regen_check.txt`. It checks two things:
    - the fixture against `git show HEAD:test/fixtures/scheme_truth.json`: only the new keys of TR-33.6, their `sources`/`provenance` entries and `_meta`'s run fields may differ;
    - each file's directives against HEAD's: only `gsize plabel` (26) and `color plabel` (the nine monochrome schemes of E6) may be added, with their provenance comments.
    Run the extractor a second time into `$S/regen2.log` and confirm `up to date` 26 times. Run `git add -f test/fixtures/scheme_truth.json`. Generated files are never hand-edited (R7).
  ]]></action>
  <verify><![CDATA[`grep -l '^gsize plabel ' dash-*.scheme | wc -l` prints 26; `grep -l '^color plabel ' dash-*.scheme | wc -l` prints 9; `grep -c 'up to date' "$S/regen2.log"` prints 26; `$S/regen_check.txt` ends `unchanged: 26 schemes`.]]></verify>
  <done>The 26 shipped files and scheme_truth.json carried the marker-label keys, with every other record unchanged.</done>
</task>

<task type="auto" id="33-06">
  <name>Give the parser the label style</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Make TR-33.1:
    - `SchemeParser._init_label_style`, called from `_init_properties` directly after the line `grep -n "self.p_markline_alphas" dash_render.py` finds;
    - `SchemeParser.default_mlabel_style`;
    - `"gsize plabel": "small"` in `_FALLBACK_PROPS` beside the other gsize keys.
    Docstrings cite E6 (Stata's textboxstyle-p#.style and the measured chain). Add `SchemeParser._init_label_style` and `SchemeParser.default_mlabel_style` to function_test_map.py under S33's anchor (TR-33.10). Add `TestTheParsersLabelStyle::test_each_shipped_scheme_matches_the_fixture[name]` and `::test_the_fallback_mirrors_s2color` to test/test_label_key_chrome.py. Run `test_label_key_chrome.py -k TheParsersLabelStyle`, `test_scheme_fallback_provenance.py` and `test_scheme_fidelity.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_label_key_chrome.py -q -n0 -p no:cacheprovider -k TheParsersLabelStyle` passes; `python3 -m pytest test/test_scheme_fallback_provenance.py test/test_scheme_fidelity.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>Every parser, the fallback and the served rebuild carried the scheme's 15 marker-label colours, opacities and sizes.</done>
</task>

<task type="auto" id="33-07">
  <name>Draw marker labels in the scheme's style</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    State in the progress output that `_apply_mlabel_opts` is CRITICAL (16 impacted) before editing it. Make TR-33.2 in `GlyphMapper._apply_mlabel_opts` and TR-33.3 at its 11 calls (E2) and in `_immediate_labels`. At each call, add only the keyword `color_idx=color_idx` to the existing call, keeping S08's `radius_px=` and every other argument. Write `$S/33-calls.py`, which parses dash_render.py with `ast`, finds every `Call` whose function is an attribute named `_apply_mlabel_opts` or `_immediate_labels`, and prints `<line> <name> <enclosing def> <has color_idx keyword>` for each, then `<n> calls pass color_idx` when every one does. Save its output to `$S/33-calls.txt` for the merger (Q1); the expected count is 13 (the 11 `_apply_mlabel_opts` calls, one of them inside `_immediate_labels`, and its 2 calls). Run `test_label_key_chrome.py -k "Label or Options or Labelled or AfterAFilterMove"` and `test_marker_label_parity.py`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_label_key_chrome.py -q -n0 -p no:cacheprovider -k "MarkerLabels or LabelChain or Labelled or OptionsStillWin or AfterAFilterMove"` passes; `python3 -m pytest test/test_marker_label_parity.py test/test_immediate_values.py test/test_pccapsym_pcarrowi.py -q -n 6 -p no:cacheprovider` passes; `tail -1 "$S/33-calls.txt"` prints `13 calls pass color_idx`.]]></verify>
  <done>Marker labels took the scheme's label colour, opacity and size at their own layer's index on every labelled type, in both modes and after a move.</done>
</task>

<task type="auto" id="33-08">
  <name>Give the colour bar the scheme's chrome</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    State that `_apply_colorvar` is treated as HIGH (index 11.0) before editing it. Add `SchemeParser.colorbar_chrome` per TR-33.4. Before writing the tick pair, read how S15's `apply_to_axis` maps `tick_length_px` and `tick_position` (`grep -n "tick_position" dash_render.py`) and compute the same pair inline with TR-33.4's rounding; do not edit `apply_to_axis` or `_dash_apply_z_options` (S31's this batch). Add `**self.scheme.colorbar_chrome()` to the `ColorBar(` call in `_apply_colorvar`, and nothing else there. Add the map entry. Run the colour-key tests and the existing z-option tests.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_label_key_chrome.py -q -n0 -p no:cacheprovider -k "ColourKey or ZOptions"` passes; `python3 -m pytest test/test_colorvar_forms.py test/test_colorvar_legend.py test/test_textbox_no_text.py test/test_help_claims_7.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>The colour bar showed the scheme's tick-label and axis-title text, upright, its tick style, and the graph region behind it, with ztitle() and zlabel() still winning.</done>
</task>

<task type="auto" id="33-09">
  <name>Re-measure pins and extend the key lists</name>
  <files>test/test_scheme_consumption.py, test/test_help_claims_8.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Run `python3 -m pytest test/ -q -n 6 -p no:cacheprovider -k "label or mlab or colorvar or ColorBar or scheme or ztitle or zlabel" -rf > "$S/33-09.log" 2>&1` (a selection, not the full suite). Write each failure outside S33's own files to `$S/33-flips.txt`, one `Flipped:` line each (R9): flip it in place with its reason, or investigate if the reason is not this section's change.
    Extend E8's rows:
    - the attribute list and the colour tuple in test_scheme_consumption.py;
    - the directive-count bounds in test_help_claims_8.py, measured on the regenerated files with the trailing comment `# <old> -> <new>: P1.4b gsize plabel and color plabel` (R10);
    - in test_mode_parity.py, `"alpha": _spec_of(r.text_alpha)` in the LabelSet profile, the chrome fields in the ColorBar profile (`label_font`, `label_color`, `title_font`, `title_color`, `title_style`, `tick_color`, `tick_in`, `tick_out`, `background_alpha`), and three CORPUS cases appended (R8): `_case("mlabel, s1rcolor", [plot_for("scatter", {"mlabel": "mpg"})], {"scheme": "s1rcolor"})`, `_case("colour bar, s1rcolor", [plot_for("scatter", {"colorvar": "price"})], {"scheme": "s1rcolor"})` and `_case("mlabel on bar and pcarrow, sttrans", [plot_for("scatter"), plot_for("bar", {"mlabel": "mpg"}), plot_for("pcarrow", {"mlabel": "mpg"})], {"scheme": "sttrans"})`.
    Leave `ALLOWED` and `_MUST_WARN` alone.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py test/test_scheme_consumption.py -q -n 6 -p no:cacheprovider` passes; `python3 -m pytest test/test_help_claims_8.py -q -n0 -p no:cacheprovider -k "not directive_count"` passes (the count test moves with the help, R10, and is run green in 33-12); `python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Every pin the change moved was flipped with its reason, the key lists covered the new attributes, and the parity corpus compared labels and colour bars in both modes.</done>
</task>

<task type="auto" id="33-10">
  <name>Add the silence cases to the scheme script</name>
  <files>test/test_custom_scheme.cscript</files>
  <action><![CDATA[
    Append MK-06 to MK-08 of "Stata truth / Area script" as one contiguous run after the script's last case block (R1). Write `w33s.scheme` and `w33m.scheme` into `cs_dir` with `file write`. Use `_cs_run`, `_cs_log`, S06's `_cs_notes`, `_cs_expect` and `_cs_done`. Add the two files, `a.html`, `b.html` and `c15.py` to the cleanup list. Write the driver `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_custom_scheme.cscript > "$S/run_cs.do"` and run `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_cs.do"`.
  ]]></action>
  <verify><![CDATA[`grep -c '^MK-0[6-8] PASS' "$S/run_cs.log"` prints 3; `grep -q 'test_custom_scheme: ALL CHECKS PASSED' "$S/run_cs.log"`; `grep -c 'FAIL' "$S/run_cs.log"` prints 0.]]></verify>
  <done>The custom-scheme script showed that a user scheme's unread directives print no note on any route, saved, immediate or served.</done>
</task>

<task type="auto" id="33-11">
  <name>Fill the S33 truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Write `_s33_tw` and the python function `_s33_both` directly above S33's header, outside every gate, each `version 19`. They are written in WP-29's S12 form (E6 cites it). Values pass through `Macro.setGlobal`; file text is never inlined into Python source; no `shell=True`.
    Write MK-01 to MK-05 between S33's start and end display lines. User files go only under `` `w30_work' `` (both names) and are erased before the end line, and the block restores the working directory.
    Write the driver `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_truth.do"` and run `WP30_ONLY=S33 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_truth.do"`.
  ]]></action>
  <verify><![CDATA[`grep -c '^MK-0[1-5] PASS' "$S/run_truth.log"` prints 5; `grep -q 'ALL CHECKS PASSED' "$S/run_truth.log"`; `grep -c 'FAIL' "$S/run_truth.log"` prints 0; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider -k Wp30` passes.]]></verify>
  <done>The truth block showed dash's marker labels and colour key matching twoway's in both modes and after a served move.</done>
</task>

<task type="auto" id="33-12">
  <name>Update the label, key and scheme help</name>
  <files>dash.sthlp, test/test_unread_scheme_directives.py</files>
  <action><![CDATA[
    Edit only the paragraphs Notes, "Text for the closing task / dash.sthlp", names:
    - Marker Label Options: the `mlabcolor` and `mlabsize` synopt lines;
    - Mapping a Variable to Colour: after the colour-bar sentence (3124-3126);
    - Stata scheme support: the Text paragraph (3393-3405), the end of "What a scheme file of yours may include" (before :3532's colour sentence) and "What the shipped files are" (the carried keys and the bounds 33-09 measured).
    Keep S08's, S15's, S17's and S24's sentences in those paragraphs (R3). Add `TestTheHelpSaysTheyAreKept::test_kept_without_a_note`. Run the help-claim files.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_8.py test/test_help_claims_5.py test/test_help_claims_7.py test/test_unread_scheme_directives.py -q -n 6 -p no:cacheprovider` passes, `test_the_directive_count_is_what_the_help_says` included; `grep -c 'twoway draws and dash does not' dash.sthlp` prints 0; `grep -c 'kept with the scheme, without a note' dash.sthlp` prints 1.]]></verify>
  <done>The help said where the label and colour-key styles come from, that directives dash does not draw are kept without a note, and what the shipped files carry.</done>
</task>

<task type="auto" id="33-13">
  <name>Close P1.4b and commit the section</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    The title is `Marker-label size and colour are fixed, the colour key has no scheme chrome, and unread user-scheme directives are ignored silently` (section-01 Appendix B; check it equals `WP30_OPEN["P1.4b"]`). Close that BUGS.md entry in place: `- [ ]` becomes `- [x]`, and its open `  - Resolution:` line is replaced by the Resolution in Notes, keeping the indentation. Delete the `"P1.4b"` key line from `WP30_OPEN`. In CHANGELOG.md, replace the `<!-- WP-30 P1.4b -->` marker in `### Results that change` with the two lines in Notes, each ending `(WP-30, P1.4b)` (R4). Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`.
    Run `git -C $WT merge --no-edit main` and expect `Already up to date.`; otherwise stop and report (E9). Make one full run through the queue: `<scratch>/full_suite_queue.sh $WT <scratch>/33-full-1.log`, launched in the background and waited for on its `exit=` line, never relaunched (E1; E6 for the known flaky tests).
    Stage exactly these, with `git add -f` on test/fixtures/scheme_layer_truth.json and test/fixtures/scheme_truth.json:
    - dash_render.py, dash.sthlp, BUGS.md, CHANGELOG.md;
    - the 26 dash-*.scheme files;
    - scripts/extract_scheme_truth.py, scripts/extract_scheme_layer_truth.do;
    - test/test_label_key_chrome.py, test/test_unread_scheme_directives.py, test/test_scheme_fidelity.py, test/test_scheme_consumption.py, test/test_help_claims_8.py, test/test_mode_parity.py, test/function_test_map.py, test/test_tracking_documents.py, test/test_wp30_truth.cscript, test/test_custom_scheme.cscript;
    - any file named in `$S/33-flips.txt`.
    Check `git diff --cached --name-status` (G6). Write the message to `$S/33-msg.txt` per the commit boundary and run G7 on it. Confirm `git -C $WT branch --show-current` prints `wp30-s33`. Commit with `git commit -F "$S/33-msg.txt"`, run G7 on `git log -1 --format=%B`, and report to the merger the sha, the message path and `$S/33-calls.txt` (Q1).
  ]]></action>
  <verify><![CDATA[`grep -E '^exit=0' <scratch>/33-full-1.log` matches and its summary shows 0 failed; `git log -1 --format=%s` ends `(WP-30 P1.4b)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.4b -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.4b": "' test/test_tracking_documents.py` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.4b was closed naming tests that exist, its CHANGELOG marker carried the measured old and new values, and the section's one green commit on wp30-s33 was ready for the merger.</done>
</task>

## Section completion criteria

- AC-33.1 to AC-33.7 hold. MK-01 to MK-08 print PASS. Every 33-01 regression test and every 33-03 fixture-driven test is green, and every guard stayed green throughout.
- `_apply_mlabel_opts` sets the scheme's label default and takes `color_idx`, which all 11 calls and `_immediate_labels` pass. `_apply_colorvar` passes `colorbar_chrome()`. `SchemeParser` has `_init_label_style`, `default_mlabel_style` and `colorbar_chrome`, and no note, allow-list or read-recording (D-33e); every parsed directive is still in `_props` (`TestUnreadDirectivesAreRetained`). `_FALLBACK_PROPS` has `gsize plabel`.
- `scheme_layer_truth.json` carries the `s33` probes, with S24's unchanged. `scheme_truth.json` and the 26 files are regenerated and never hand-edited, and a second run is a no-op. Both fixtures are staged with `git add -f`.
- function_test_map.py holds the three keys under S33's anchor. The served-name guards are green, with no copy-list change.
- BUGS.md `P1.4b` is closed, its `WP30_OPEN` key is gone, and its CHANGELOG marker is replaced by two lines. dash.sthlp's five places are updated.
- One commit on `wp30-s33`, subject ending `(WP-30 P1.4b)`, after one green full run.
- Not edited: `_apply_marker_opts`, `_apply_line_opts`, `_apply_fill_opts`, `_dash_apply_z_options`, `_parse_lines`, `_include`, `_parse_file`, `SchemeParser.__init__`, `resolve_or_fallback`, `fallback`, `_make_figure_body`, `_generate_app_source`, the copy-list tuples, dash.ado, dash_parse.mata, `scripts/svg_truth.py`, `scripts/svg_layer.py`, any runner block or hygiene pin, and any tracking document beyond BUGS.md and CHANGELOG.md.

## Notes

### Traps for the executor

1. **Sizes are Stata units, not pixels.** Compare twoway's `font-size / (min(w, h) / 100)` with dash's `css_to_pt(size) / 2.88`. stcolor's canvas is 5400 × 3240 and economist's 1584 × 1584, so a raw font-size comparison is wrong.
2. **Stata writes mixed-case hex** (`#1A476f`). Lower-case both sides.
3. **`mlabel(make)` in twoway, `mlabel(mpg)` in pytest.** The pytest data have no `make`; the label text does not matter, only its style.
4. **Retention is already true.** Every test of `test_unread_scheme_directives.py` is a guard (D-33d). If one fails at the base, the base has changed: stop and report. This section does not edit `_parse_lines`, `_include`, `_parse_file` or `SchemeParser.__init__`.
5. **S08's applier.** The `mlabsize` branch multiplies `css_to_pt(kwargs["text_font_size"])`. If S08's final text reads another variable, keep its rule and make sure the scheme's size is what it multiplies. `TestTheOptionsStillWin::test_mlabsize_star_multiplies_the_schemes_size` is the check.
6. **S29's SMCL pass** may set a LabelSet's or the ColorBar title's font style afterwards. S33's `title_text_font_style="normal"` is a construction default and must not be re-applied after S29's pass.
7. **User files in Stata.** Twoway finds `scheme-<n>.scheme` on the ado-path; dash at batch 11 reads `<n>.scheme` from the working directory (S34 adds the ado-path in batch 12). Write both names with identical text.
8. **python_exec hazard.** Several concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`, and a cscript then exits 222. A skip is not a pass: restore it and re-run.
9. **The red list is re-measured** (33-09). A node outside S33's files is investigated before it is flipped (R9).

### Shared files and merge rules

- **R1:** S33's truth block between its own start and end lines, with its helpers directly above its header. MK-06..MK-08 form one contiguous run at the end of `test_custom_scheme.cscript`'s last case block. No runner block or hygiene pin.
- **R2:** no copy-list entry (row S33). Three `function_test_map.py` keys under S33's anchor only.
- **R3:** dash.sthlp Marker Label Options (shared with S08 in batch 3 and S37 in batch 13), Mapping a Variable to Colour (S17 in batch 6), and Stata scheme support (S07, S15, S24 before; S34 and S36 in batch 12). S33 keeps their sentences.
- **R4:** one marker, `<!-- WP-30 P1.4b -->`, replaced in place by two lines.
- **R5:** BUGS.md `P1.4b` in place; only the `"P1.4b"` line of `WP30_OPEN` deleted.
- **R7:** both fixtures regenerated by their extractors (S33 is batch 11's regenerator, A152, landing last). On a conflict the merger re-runs `scripts/extract_scheme_truth.py` on the merged tree, and the layer extractor if S32 touched it.
- **R8:** three CORPUS cases appended. `ALLOWED`/`_MUST_WARN` untouched. Profile fields added for ColorBar and LabelSet.
- **R9:** `$S/33-flips.txt` lines in the body.
- **R10:** the directive-count bounds in `test_help_claims_8.py` and dash.sthlp move together. `_SINGLE_Y_BASELINE_SHA256` is expected unchanged; if it moves, the merger re-derives it.
- **R12:** S33 is batch 11's only editor of `_apply_mlabel_opts`.

### Open question for the maintainer

**Maintainer question:** Q1 — A139 and the seven shared mappers. D-33b needs the layer's index at each `_apply_mlabel_opts` call. Seven of the call-site functions are also edited by S32 in batch 11, which A139 forbids ("No two sections of a batch edit the same function"): `map_bar`, `map_dropline`, `map_rcapsym`, `map_scatteri`, `map_pcarrow`, `map_pcbarrow` (S32's TR-32.9) and `map_pccapsym` (S32's TR-32.10 `role="aline"`), plus `map_scatter` if S32's TR-32.6 moves an inline read out of it. S33's edit there is one keyword on one call line, a hunk apart from S32's. S33 cannot yield inside batch 11:
- carrying the index as mapper state set in `_dash_add_glyph`/`_dash_add_pc_glyph` still misses `map_scatteri`/`map_pcarrowi`, which `_make_figure_body` and the served template call directly (R12 editors in other batches), and D-33b rejects mapper state;
- moving S33 to batch 12 puts two regenerators there (S33, S36; A152) and pushes S34 to batch 13.
- **(a) Recommended.** Accept the exception for this keyword. S33 lands after S32 (merge order), and the merger re-adds `color_idx=color_idx` by hand on any conflict, checked against `$S/33-calls.txt` (13 calls) and `TestEveryLabelledTypeTakesItsLayersColour` on the merged tree. On that tree the merger also checks one S32 interplay by hand: `stcolor` `scatter mpg weight, mlabel(mpg) pstyle(p3)` labels in `#00bf7f` (p3; S32's E3 `p(p3)` row), through S32's `_dash_plot_style_indices` override reaching `color_idx`.
- **(b)** Move S33 to batch 12 and S34 to batch 13. Batch 12 would then hold two regenerators (S33, S36), which A152 forbids unless the batches are recut. Not recommended for a one-keyword hunk.

### Text for the closing task

**BUGS.md Resolution** (33-13; one line, in place):

`- Resolution: Fixed <ddmonyyyy> (WP-30, P1.4b). A marker label is drawn in the scheme's marker-label colour, opacity and size -- color p#label, else color plabel, else the plot's colour, and gsize p#label, else gsize plabel, in Stata's text units -- at its own layer's index on every labelled type (SchemeParser._init_label_style and default_mlabel_style, GlyphMapper._apply_mlabel_opts and its eleven calls, _immediate_labels); mlabcolor() keeps the scheme's opacity and mlabsize(*#) multiplies the scheme's size, while mcolor(), color label and gsize label leave labels alone, as in twoway. A colorvar() colour bar takes the scheme's tick-label size and colour for its labels, the axis-title size and colour for its upright title, and the scheme's tick colour, width and length, on the graph region (SchemeParser.colorbar_chrome, GlyphMapper._apply_colorvar). The third clause is closed by disposition: a scheme directive dash does not draw -- clockdir p, the textboxstyle of a title or of tick labels, or any other -- is kept in the parsed scheme under its key with its value (SchemeParser._parse_lines and _include store every directive, as they did at c96facd, and the served app's property dict carries them) for a later version to draw, and by the maintainer's ratification (06oct2026) it is not noted, in either mode. scripts/extract_scheme_truth.py and the 26 shipped files carry gsize plabel and, in the nine monochrome schemes, color plabel. The saved page and the served app draw the same, before and after a filter move: both build every marker label through the one applier, and the served app's 9px default was already gone at c96facd, so the one scheme default replaces the saved 10px in both. Pinned by test/test_label_key_chrome.py::TestMarkerLabelsTakeTheSchemeLabelStyle::test_the_default_label_style, test/test_label_key_chrome.py::TestTheLabelChain::test_p1label_reaches_layer_one_only, test/test_label_key_chrome.py::TestEveryLabelledTypeTakesItsLayersColour::test_the_second_layer, test/test_label_key_chrome.py::TestTheColourKeyTakesTheSchemeChrome::test_the_key_text, test/test_label_key_chrome.py::TestAfterAFilterMove::test_the_served_label_and_key_keep_their_style, test/test_unread_scheme_directives.py::TestUnreadDirectivesAreRetained::test_a_user_schemes_directives_are_kept, test/test_unread_scheme_directives.py::TestUnreadDirectivesAreRetained::test_a_shipped_schemes_unread_keys_are_kept, test/test_unread_scheme_directives.py::TestNoNoteForUnreadDirectives::test_builds_are_silent, test/test_wp30_truth.cscript MK-01, test/test_custom_scheme.cscript MK-06; fixture test/fixtures/scheme_layer_truth.json. Residual, deferred (WP-30): the colour key's title runs along the top of the bar where twoway turns it up the key's right side, and the key's axis line on its label side is not drawn (P2.10); mlabcolor()'s own %NN opacity is P1.13b's.`

**CHANGELOG.md** (33-13; replacing `<!-- WP-30 P1.4b -->` in the WP-30 group of `### Results that change`; the old values are 33-01's failure text and E5):
- `- Marker labels take the scheme's marker-label colour and size, as twoway draws them: under s2color \`dash scatter mpg weight, mlabel(make)\` labels in #1a476f at Stata's small (8pt), where they were #444444 at 10px under every scheme; under s1rcolor in yellow #ffff00 on the black page, and under sttrans at the scheme's 20% opacity. \`color plabel\`, \`color p#label\`, \`gsize plabel\` and \`gsize p#label\` in a scheme of yours reach them, and \`mlabsize(*2)\` doubles the scheme's size. (WP-30, P1.4b)`
- `- A colorvar() colour bar takes the scheme's text and ticks: its labels in the tick-label size and colour, its title in the axis-title size and colour, upright, its ticks in the scheme's tick colour, width and length, on the graph region. It was a white box at 95% opacity with 11px #444444 labels and a 13px italic #444444 title under every scheme, s1rcolor's black page included. (WP-30, P1.4b)`

**dash.sthlp** (33-12; SMCL as the surrounding text writes it):
- Marker Label Options, `mlabcolor` synopt, appended: `; by default the scheme's marker-label colour -- {cmd:color p}{it:#}{cmd:label}, else {cmd:color plabel}, else the plot's own colour, with its opacity, as {cmd:twoway} draws it; {cmd:mcolor()} and {cmd:color label} do not change it`.
- `mlabsize` synopt, appended: `; by default the scheme's {cmd:gsize p}{it:#}{cmd:label}, else {cmd:gsize plabel} ({cmd:small} in every shipped scheme), and {cmd:*}{it:#} multiplies that size`.
- Mapping a Variable to Colour, after "a colour bar is drawn beside the figure, where {cmd:twoway} bins it at its z axis's ticks.": `The colour bar sits on the graph region with no box of its own: its tick labels take the scheme's {cmd:tick_label} size and colour, its title the {cmd:axis_title} size and colour, upright, and its ticks the scheme's tick colour, width and length, as in {cmd:twoway}'s colour key. {cmd:twoway} turns the title to run up the key's right-hand side and draws an axis line on the side of its labels; {cmd:dash} draws the title above the bar and no axis line.`
- Stata scheme support, Text paragraph, before `{p_end}`: ` Marker labels take {cmd:color p}{it:#}{cmd:label} and {cmd:gsize p}{it:#}{cmd:label} (else {cmd:plabel}, else the plot's colour) -- not {cmd:color label} or {cmd:gsize label}, which {cmd:twoway}'s marker labels do not read -- and the colour bar's labels and title take {cmd:tick_label} and {cmd:axis_title}.`
- "What a scheme file of yours may include", before its last sentence: `A directive {cmd:dash} does not draw yet -- such as {cmd:clockdir p} (where marker labels sit) or the {cmd:textboxstyle} of a title -- is read and kept with the scheme, without a note, so a later {cmd:dash} that draws it takes it from your file.`
- "What the shipped files are": add `{cmd:gsize plabel}` (and `{cmd:color plabel}` where the chain declares it) to the carried keys, and write the bounds 33-09 measured.

### Notes for the closeout (S58; A145)

- **Sources closed by P1.4b** (manifest): REM-11-04-B1 (REMAINING.md:1289, the 10px/9px default), REM-S11-e2 (REMAINING.md:310, marker-label text sizing), REM-11-04-C11 (REMAINING.md:2771, ColorBar chrome), GAPS2-D10-a and GAPS2-D10-b (unread directives, closed by disposition: kept in the parsed scheme for later use and, by the maintainer's ratification of 06oct2026, not noted; the `color label` example: twoway ignores it, E6).
- **GAPS2 D10** (D10-a, D10-b) is closed by P1.4b. Tracked line: `Closed in WP-30 (P1.4b), BUGS.md "Marker-label size and colour are fixed, the colour key has no scheme chrome, and unread user-scheme directives are ignored silently", commit <sha>`. Record that D10's plan item 4 is corrected by measurement: s1rcolor's marker labels are #ffff00 (p1), not white, because twoway's marker labels read `p#label`/`plabel`/`p#`, never `color label`; and D10-b closes by disposition: the unread directives are kept in the parsed scheme for later use and, by the maintainer's ratification (06oct2026, row 4), not noted, so D10's proposed note is not built.
- **REMAINING.md**:
  - 11-04's first bullet (REMAINING.md:1289-1297, the 10px/9px marker-label size) is closed by P1.4b.
  - §1's row 11 (REMAINING.md:310, "scheme-driven text sizing (title, note, subtitle, mlabel) still ignored") has its marker-label part closed by P1.4b.
  - 11-04's ColorBar bullet (REMAINING.md:2771-…) is closed by P1.4b, with the residual below.
- **DROPIN-REMAINING.md P1.4** is closed once S24 and S33 have both landed. Note: "residuals: P2.10 (the colour key's title orientation and one-sided axis line)".
- **ROADMAP P2.10** gains two sub-claims: twoway turns the colour key's title up its right side, and draws an axis line on the key's label side. dash draws neither, because Bokeh's ColorBar has no title rotation and no one-sided line.
- **TWOWAY_COVERAGE_AUDIT.md**: no row changes for S33. The marker-label row's `mlabvposition()`/`mlabtextstyle()` are S37's.

### For later sections

- **S34** resolves along the ado-path. An ado-path scheme's directives are retained like any other and not noted (D-33d); S33 leaves it no provenance rule to keep. Its per-graph served property dicts carry every parsed directive, as `_SCHEME_PROPS` does.
- **S37** resolves `mlabtextstyle()` against `SchemeParser.default_mlabel_style(i)`. If it starts drawing `clockdir p#` as the default label position, it reads the value from `_props`, where it is already kept (D-33d).
- **S36** likewise reads any `textboxstyle` key it starts drawing from `_props`.
- Any later section that drops a parsed directive fails `TestUnreadDirectivesAreRetained`.
- **S43** owns `mlabcolor(red%70)`'s opacity (twoway 0.70, E6) and bare `*#`/`%#` on marker labels. Under sttrans, S33 leaves `mlabcolor(red%70)` at the scheme's 0.20.
- **S53**'s by() colour key is built by the same `_apply_colorvar` and inherits `colorbar_chrome()`.
