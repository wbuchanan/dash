# Section 09: TeX delimiters inert on every canvas sink (P1.11 part a)

> Part of: WP-30 · Items: P1.11 part a (entry `P1.11a`; GAPS2-D3's TeX half, DROPIN's GAPS2-D3-e, and GAPS2-J5) · Risk: yellow · Batch: 3 (merge order S07, S08, S09) · Depends on: 01 · Blocks: 29 · Tasks: 8, 1 commit · Case prefix: TX

## Review amendments

- Fixed (major): the truth block's header read "TeX delimiters drawn as typed …", not S01's stub header ("TeX delimiters inert on every canvas sink"); TR-01.10 forbids editing it. The block now keeps S01's header, gate and end lines byte for byte, and the hedge about the helper names is replaced by S01's `_w30_expect`/`_w30_done`/`w30_work`.
- Fixed (major): `$S` was this planning session's scratchpad path, which does not exist at execution, and S09's files sat at the scratch root beside its partners'. `$S` is now `<scratch>/s09`; the batch base, impact file and queue script are read from `<scratch>`.
- Fixed (minor): the truth block now erases its five files and drops its two graphs before its end line (TR-01.10 item 4).
- Checked: anchors at HEAD (`_dash_inert_tex` 24012-24044, the loop end of `_build_sources_and_figures` 31685-31689, the generated `_dash_share_by_scales` lines 35653-35656, the copy-list anchor 33276-33279) match. The TX-03 inert needle was checked against Bokeh's embedding: a title `\⁠(y` is written `\⁠(y` in the page JSON, which the needle matches.
- Checked: batch 3 shares no function. S09 alone edits `_build_sources_and_figures` and `_generate_app_source`. It only reads what S08 edits (`_dash_apply_legend`, `_dash_apply_z_options`, `_textbox_size`), and its pass runs after them.
- Cross-file (notes file): index R3 does not list S09 for its Server Mode sentence (dash.sthlp:1721-1725). No batch-3 partner edits that title.
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:101 (P1.11) reads: "`$$…$$` in a title triggers MathJax, which grows the page from 1.3 MB to 3.1 MB." GAPS2.md:1739 (J5) reads: "A `$$..$$`, `\(..\)` or `\[..\]` pair in a title, note, axis title or tick label is typeset by MathJax". twoway draws those characters as typed. Measured at `c96facd` (StataNow 19.5, `scripts/stata_slot.sh`, scratch `tx1.do`/`tx4.do`):

- `twoway scatter mpg weight, title("\(y\)") subtitle("\[z\]") note("\$\$ x \$\$") xtitle("\(a\) w") xlabel(2000 "\(t\)" 3000) legend(on label(1 "\(k\)"))` exported to SVG holds the six `<text>` runs `\(y\)`, `\[z\]`, `$$ x $$`, `\(a\) w`, `\(t\)`, `\(k\)`, exactly as typed.
- The same options in `dash scatter …, saving()` give a page that ships `bokeh-mathjax` and is **3,087,832 bytes**; the same page in plain words is **1,301,750 bytes** (+1,786,082, the MathJax bundle). In headless Chrome, BokehJS builds five `TeX` views on that page (Title, the colour bar's internal Title, Label, the axis label and a tick override) where twoway draws text.
- The served app draws the same TeX (Bokeh's server bundle always carries MathJax), and its canvas models hold the same raw pairs.

It is also a security surface (critic addition 7 in `research/p1-11.md`): every user string on a canvas sink reaches MathJax's TeX parser, whose `html` package makes `\href{javascript:…}` a live link and `\style{…}` a style attribute (`test_label_sinks.py`'s own TEX_DISPLAY and TEX_BRACKET payloads). WP-20 closed this only for slider titles (`_dash_inert_tex`) and Divs (`disable_math`); canvas text was left raw.

**After this section**, one document pass, `_dash_finish_graph_text`, runs last in each mode: at the end of `DashRenderer._build_sources_and_figures` (saved) and in the generated `make_document` after the figures, by() panel titles and shared by() scales are built (served). It applies only the existing `_dash_inert_tex` to every canvas text sink: Title, Label (subtitle, note, caption), every axis title and tick-label override, the tick-label formatter's map, the legend's entries and title, and the colour bar's title and tick labels. TeX pairs are drawn as typed, as twoway draws them; the saved page stops shipping MathJax (about 1.30 MB again); no user text reaches MathJax's TeX parser in either mode, before or after a filter move. Each model the pass visits is marked, so a second call is a no-op. Nothing is printed: twoway prints nothing for this text, and neither does dash (M6).

**Why this is one small section.** The pass is the seam S29 (P1.11b, batch 10) extends with the SMCL translator; S29 must never edit `_build_sources_and_figures` or `_generate_app_source` (manifest), so this section owns both call sites and the pass's shape (a mapping of figure key to figure, the sink table, the done-mark). The register's rulings bind it: A35 (P1.11.5: TeX drawn as typed, no opt-in; ratification item 7, pending) and A36 (P1.11.6: the served bundle's MathJax is left to P2.48).

**Test order and commit rule (rule 7, D1).** Task 09-01 writes every regression test of this entry (pytest and the S09 truth block), runs them against the unmodified tree and saves `$S/09-P1.11a-failure.txt`; it never commits. Tasks 09-02 to 09-07 make the fix, flip the pinned tests and register the names. Task 09-08 closes the entry, replaces both markers, runs the full suite through the queue and makes the section's one commit, `(WP-30 P1.11a)`. No test-only commit exists and no commit is red.

## Risk: [yellow] — one added call in a CRITICAL builder and one generated statement in a HIGH template change the text of every canvas sink holding a TeX pair, and 115 pinned test ids of a security inventory flip

**Why.** The edit sites are tiny, but the effect is document-wide, in two renderers, and order-dependent.

**Risk factors.**
1. `DashRenderer._build_sources_and_figures` is CRITICAL (14 impacted, 7 processes) and `ServerAppBuilder._generate_app_source` HIGH (5 impacted); a misplaced call misses late sinks (by() panel titles) or runs after `_stale_cue_args` copies the legend text.
2. A naive walk is slow: `fig.references()` visits every value of every column. Measured on a 100-panel `by()` graph of 20,000 rows: 7.08 s per pass (render 25.78 s against 13.14 s); the explicit walk of TR-09.2 takes 0.067 s.
3. The pinned TeX rows of `test_label_sinks.py` are a security inventory (WP-20, AC-20.2); a careless flip could hide a real regression.
4. A served name missing from the copy list fails only on the served page.
5. A sink created after the pass by a later section (S19, S28, S56) would keep a live pair.
6. Rewriting the formatter map or a legend label could change a page that holds no TeX (page digest, `_SINGLE_Y_BASELINE_SHA256`).

**Mitigation.**
1. Both call sites are pinned by order tests (TR-09.6, TR-09.7). `_build_filter_widgets` → `_stale_cue_args` runs after `_build_sources_and_figures` returns (render phases 3 then 5, dash_render.py:32675-32707), and a spy test asserts it.
2. The walk reads only the figure's title, its five side lists, each model's formatter and each legend's items; a test fails if `Model.references` is called during the pass, and a 100-panel bound is timed.
3. Each flip keeps the raw-text assertion for every non-TeX payload and adds, for the TeX payloads, "no delimiter left and the typed text shown once the joiner is removed". The prototype measurement below shows exactly the 115 expected ids turn red and nothing else in 13 related files.
4. `TestTheServedAppDefinesEveryNameItReads`, `TestTheServedAppCarriesEveryName` (with S01's `test_every_listed_name_exists`) and a source-order test run in task 09-04.
5. A guard test (`test_every_canvas_model_is_finished`, both modes) fails the day a later section adds a canvas sink after the pass without finishing and marking it.
6. A property is written only when its text changes, and the mark is a Python attribute that is never serialised. Measured with the prototype: `test_varlist_expansion.py` (the digest) passes unchanged, and the hostile `all` page is byte-identical (2,469,902 bytes before and after).

**Prototype (measured 03oct2026 at `c96facd` in scratch, not in the repo).** The pass of TR-09.1 to TR-09.5 was patched in through a pytest plugin (saved: wrapped `_build_sources_and_figures`; served: the generated source with the call inserted before `# ---- Persist per-graph qualifier metadata`):

```
python3 -m pytest -p s09_plugin test/test_label_sinks.py test/test_help_claims_7.py test/test_saved_stale_cue.py -q -n 6
115 failed, 1867 passed     (102 TestTextSinks::test_it_carries_the_raw_text, 12 ::test_a_tick_label_map_carries_the_raw_text,
                             1 test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_label_text_is_a_label_and_never_read)
python3 -m pytest -p s09_plugin test/test_saved_stale_cue.py test/test_mode_parity.py test/test_varlist_expansion.py \
    test/test_graph_options.py test/test_server_facets.py test/test_security_surface.py test/test_axis_options.py \
    test/test_colorvar_forms.py test/test_title_escaping.py -q -n 6
4847 passed
```

## Dependencies

- **Depends on: 01.** S01 provides the open BUGS.md entry `P1.11a` and its `WP30_OPEN` key; the two CHANGELOG markers `<!-- WP-30 P1.11a -->` (one at the end of `### Security`, one in the `**WP-30 (drop-in P1, 03oct2026)**` group of `### Results that change`); the S09 stub block of `test/test_wp30_truth.cscript`; the anchor `# WP-30 S09 (P1.11a): TeX delimiters inert on every canvas sink` at the end of `FUNCTIONS` in `test/function_test_map.py`.
- **Blocks: 29.** S29 extends `_dash_finish_graph_text` (and `_dash_finish_text_value`) with the SMCL translator and the style properties, and adds its own names after S09's in the copy list (R2 row S29).
- **Parallel batch: 3** with S07 (six schemes) and S08 (size units). **Merge order S07, S08, S09**: S09 lands last.
- **Can run with S07 and S08.** Neither edits `_build_sources_and_figures`, `_generate_app_source`, `_glyph_layer_lines` or `_dash_inert_tex` (R12; batch 3 subsection). S08 edits `_dash_apply_legend`, `_dash_apply_z_options`, `_textbox_size`, `_apply_mlabel_opts` and the axis `labsize` path, all of which this section reads through the pass and never edits.

## Evidence

All anchors are at `c96facd` (`dash_render.py` 37,689 lines). Symbols are authoritative if S07 or S08 shifts lines before S09 lands.

### E1. The one breaker that exists, and its only caller

`_dash_inert_tex`, dash_render.py:24012-24043, breaks every `$$`, `\(`, `\)`, `\[`, `\]` with U+2060 (`_DASH_WORD_JOINER`, :24009). It is idempotent (`TestInertTex::test_it_is_idempotent`):

```python
24036        return m.group(0) + _DASH_WORD_JOINER
24038    s = str(text)
24041    s = re.sub(r"\$(?=\$)", _wj, s)
24043    s = re.sub(r"\\(?=[()\[\]])", _wj, s)
         return s
```

Its only caller is `_dash_filter_title` (:24047; the call at :24060), for slider-family titles. `gitnexus impact _dash_inert_tex -d upstream -r dash`: HIGH, 5 impacted, direct caller `_dash_filter_title` only.

### E2. Where user text reaches a canvas sink raw (both modes share these helpers)

| Sink | Built at | What it carries |
|---|---|---|
| Title | saved `fig_kwargs = dict(title=_parse_textbox_opt(graph_opts.get("title", ""))[0], ...)` :30262-30263; served `_fig_kw = dict(title=_parse_textbox_opt(go.get('title', '') or '')[0], ...)` :35144-35145 | `title()` |
| by() panel Title | saved :31655-31656 `fig.title.text = f"{orig_title} — {label}" if orig_title else label`; served :35518-35520 | value labels, joined to the title |
| Label | `_dash_text_annotations` (:25969), `fig.add_layout(Label(... text=text, ...))` :26013 | `subtitle()`, `note()`, `caption()` |
| Axis label | `_dash_axis_labels` (:21665) → `x_axis_label`/`y_axis_label` :30236/:35139; second axis `fig.add_layout(ax, side)` :23106 | `xtitle()`/`ytitle()`/`ytitle2()`, variable labels |
| Tick overrides and map | `_dash_apply_axis_spec` (:22714): `axis_obj.major_label_overrides = overrides` :22786/:22801/:22819; the map formatter :22811-22815 | `xlabel(# "t")`, `valuelabel` ticks |
| Legend entries | `_dash_apply_legend` (:21400) `LegendItem(label={"value": "\n".join(texts[n])}, ...)` :21497; colorvar key `LegendItem(label=factor, ...)` :9202 | keys, `legend(label())`, value labels |
| Legend title | `Legend(items=legend_items, title=var_display, ...)` :9217 | colour variable's label, `ztitle()` |
| ColorBar title and labels | `ColorBar(..., title=var_display)` :9243-9245; `_dash_apply_z_options` `key_obj.title = text` :26136, `key_obj.major_label_overrides = {...}` :26176-26177 | colour variable's label, `ztitle()`, `zlabel(# "t")` |

The tick-label map formatter, dash_render.py:22811-22815 (the only `CustomJSTickFormatter` whose `args` is exactly `{"labels": <JSON>}`; the other, `_dash_fmt_tick_formatter` :21138-21155, carries a display format, never user text):

```python
22811            _labels = {str(k): str(v) for k, v in overrides.items()}
22812            axis_obj.formatter = CustomJSTickFormatter(
22813                args={"labels": json.dumps(_labels)},
22814                code="const m = JSON.parse(labels); "
22815                     "return m[String(tick)] || String(tick);")
```

The hostile harness confirms the inventory (research `both_modes.py`, payload `{bf:B} {&alpha} R{sup:2} \(y\)`): standalone and served carry raw pairs on `Title.text`, `Label.text`, `LinearAxis.axis_label`, `LinearAxis.major_label_overrides`, `CustomJSTickFormatter.args`, `LegendItem.label`, `Legend.title`, `ColorBar.title`; `_model_requires_mathjax` is true for Label, LinearAxis and Title in both modes.

### E3. What BokehJS parses as TeX, and when MathJax ships

Read in `bokeh/server/static/js/bokeh.js` (3.9.0; the same functions exist in 3.8.0, Stata's interpreter):
- `TextAnnotationView._init_text` (bokeh.js:27509-27512): `const _text = isString(text) ? parse_delimited_string(text) : text;` — Title and Label.
- `AxisView._init_axis_label` and `_init_major_labels` (bokeh.js:29641-29656): the axis label and every string in `major_label_overrides`.
- `BaseColorBarView` builds an internal `Title` and axis (bokeh.js:26899-26901, 26936-26938), so a ColorBar's title and tick overrides go through the same two views.
- `parse_delimited_string` (bokeh.js:27905-27941) matches only the literal pairs `$$…$$`, `\[…\]`, `\(…\)`; otherwise it returns `PlainText`.
- Not parsed: `TickFormatter.format_graphics` returns `TextBox` (bokeh.js:30269-30270), so a formatter's output is plain text; the Legend's entries and title are DOM text (`div({class: legend_css.label}, `${label}`)`, bokeh.js:39845; title :39930); `LabelSetView` uses `TextBox`.

In Python, `bokeh.embed.bundle._model_requires_mathjax` (bundle.py:397-436) ships MathJax for a saved page when a TextAnnotation's text, an AbstractSlider's title, an Axis's label or override, or a Div/Paragraph without `disable_math` holds a pair (it does not look at ColorBar). `bundle_for_objs_and_resources` (bundle.py:159-170) sets `use_mathjax = True` when `objs is None`, the server path, so a served page always loads the bundle (P2.48, A36).

Measured in headless Chrome (scratch `probe5.py`, `Bokeh.index.all_views()`, counting each view's `_text_view`/`_axis_label_view`/`_major_label_views` model type) on the saved page of `_spec([plot_for("scatter"), plot_for("lfit"), plot_for("scatter", {"colorvar": "price"})], {"filter": "foreign, type(dropdown)"}, {...})` (test_mode_parity helpers) with TeX in `title("\(y\)")`, `subtitle("\[z\]")`, `xtitle("$$x$$")`, `xlabel(3000 "\(t\)" 4000)`, `legend(label(2 "\(f\)"))` and `ztitle("\(c\)")`:

```
HEAD (c96facd)   {'tex': 5, 'plain': 2, 'where': ['Label.text', 'LinearAxis.axis_label', 'LinearAxis.override', 'Title.text', 'Title.text']}
with the pass    {'tex': 0, 'plain': 7, 'where': []}
```

### E4. Order: when each mode has built its last canvas sink

Saved, `DashRenderer.render` (:32603): `self._build_sources_and_figures(...)` (:32675), then 3b-3d (sources and the frozen-layer registry, no text), then `_build_kpi_html` (Divs), then `_build_filter_widgets` (:32707), which calls `_stale_cue_args` (:32241). `_stale_cue_args` (:32289-32371) copies each frozen layer's legend text into the callback config and adds the hidden caption `Title(text=_DASH_STALE_CUE_TEXT, tags=["dash_stale_cue"])` (a module constant):

```python
32330                        lab = it.label
32331                        if isinstance(lab, dict):
32332                            text = lab.get("value")
32333                        else:
32334                            text = getattr(lab, "value", None)
32343                        its.append([item_index[id(it)], text])
```

The saved filter script then writes that text back after a move, `_FILTER_JS` (:19341-19344):

```javascript
    for (let k = 0; k < _stl_items.length; k++) {
        if (_stl_item_text[k] === null) continue;
        _stl_items[k].label = {value: _stl_item_suffix[k] === null
            ? _stl_item_text[k] : _stl_item_text[k] + _stl_item_suffix[k]};
```

So the pass must run before `_stale_cue_args`, and then the label after a move is the finished text plus a constant suffix. No other saved script writes canvas text (a scan for `major_label_overrides =`, `.axis_label =`, `title.text =`, `.title =` finds only Python sites, :22786-26176, :31656).

The end of the saved figure loop, dash_render.py:31680-31689, the last statement of `_build_sources_and_figures`:

```python
31681                    _fig = self._make_figure(g, src, facet_view=_qual_view,
31682                                             rescale=_brs)
31683                    if name in link_names:
31684                        _dash_dim_nonselection(_fig)
31685                    self.figures[name] = _fig
31686                except Exception as exc:
31687                    raise RuntimeError(
31688                        f"dash_render: failed to build figure '{name}': {exc}"
31689                    ) from exc
```

Served, the generated `make_document`: the figure loop builds every graph and panel (`figures[gname] = _dash_figure_for(...)` :35562/:35584/:35646; panel titles inside `_dash_figure_for` :35518-35520), and closes with the by() scale sharing, dash_render.py:35653-35656:

```python
35653            "        _dash_share_by_scales([figures[_f] for _f, _ in _entries",
35654            "                               if _f in figures], _brs)",
35655            "",
35656            "    # ---- Persist per-graph qualifier metadata for filter callbacks ----",
```

After that come qualifier metadata, KPI Divs (`disable_math=True`) and the filter widgets (`# ---- Filter widgets + Python callbacks ----`). A served move redraws a layer on a throwaway `bokeh_figure()` and copies only its data (`_dash_redraw_for`, :35039-35093; `_dash_copy_redraw_geometry` :24941 copies widths); no generated statement writes `.label`, `axis_label`, `major_label_overrides` or a title after `make_document` returns (critic addition, research p1-11).

Panel keys are `f"{name}__by__{idx}"` in both modes (:31541, :31600, :35623), so a pass that walks `figures.items()` gives S29 each figure's owning graph without a new argument.

### E5. The served copy lists

`ServerAppBuilder._glyph_layer_lines` (def :32834), functions tuple :33077-33425; the anchor, dash_render.py:33276-33279:

```python
33276                         # _dash_filter_title neutralises TeX in the title;
33277                         # _dash_inert_tex is its callee and must travel too.
33278                         "_dash_inert_tex",
33279                         "_dash_filter_title",
```

Upper-case module constants a copied function reads are supplied by `_supply_missing_constants` (:36619-36640) whenever `ast.literal_eval(repr(value)) == value`; that is how `_DASH_WORD_JOINER` reaches the app today (generated line `_DASH_WORD_JOINER = '\u2060'`, measured), and how this section's two constants travel (R2 row S09: constants "—"). The generated app imports `json` and `re` at module level (measured).

### E6. twoway truth (StataNow 19.5, `graph export … as(svg)`, read with `scripts/svg_truth.py`)

```
tx1.do  twoway scatter mpg weight, title("\(y\)") subtitle("\[z\]") note("\$\$ x \$\$") xtitle("\(a\) w")
        xlabel(2000 "\(t\)" 3000) legend(on label(1 "\(k\)"))
        <text> runs: '\(t\)'  '\(a\) w'  '\(k\)'  '$$ x $$'  '\[z\]'  '\(y\)'
tx3.do  label variable mpg "\$\$ m \$\$"; label variable weight "\(w\) lbs";
        label define orig 0 "\(d\)" 1 "\$\$f\$\$"; twoway scatter mpg weight, by(foreign)
        <text> runs: '\(d\)'  '$$$'  '$$ m $$'  '\(w\) lbs'  'Graphs by Car origin'
```

Every TeX pair is drawn as typed. The one exception, `$$f$$` drawn `$$$`, is not TeX: twoway macro-expands `$name` inside a label when it draws it (`$f` is an empty global). That is a different root cause and is handed to the closeout (Notes); this section's tests avoid `$name` forms in labels.

### E7. The tests that pin today's behaviour (flipped in task 09-05, never deleted)

Re-measured with the prototype (Risk); exactly these turn red:
- `test/test_label_sinks.py::TestTextSinks::test_it_carries_the_raw_text` — 102 ids: `[standalone|served]-<sink>-[tex_inline|tex_display|tex_bracket]` for the 17 sinks `graph_title`, `graph_subtitle`, `graph_note`, `graph_caption`, `xtitle`, `ytitle`, `ytitle2`, `axis_title_from_variable_label`, `xlabel_tick_text`, `facet_title_from_value_label`, `colorbar_title_from_variable_label`, `colorbar_title_from_ztitle`, `legend_key_from_variable_label`, `legend_label_override`, `colorvar_legend_title_from_variable_label`, `colorvar_legend_title_from_ztitle`, `colorvar_legend_key_from_value_label`. Today it asserts `want in c.text` (the raw pair).
- `test/test_label_sinks.py::TestTextSinks::test_a_tick_label_map_carries_the_raw_text` — 12 ids: `[standalone|served]-[xlabel_tick_formatter_map|ylabel2_tick_formatter_map]-[tex_inline|tex_display|tex_bracket]`.
- `test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_label_text_is_a_label_and_never_read` — asserts `fig.legend[0].items[0].label.value == text` with `text` holding `$$\href{a}$$`.

Not affected (measured green with the prototype): `TestInventory`, `TestEverySinkIsReached`, `TestSliderTitles`, `TestHtmlSinks`, `TestDataSinks`, `TestTooltips`, `TestJavaScript`, `TestTeX`, `TestInertTex`, `TestPages`, `TestServedSource`, `TestTextSinks::test_mlabel_draws_the_raw_string_column`; `test_saved_stale_cue.py`; `test_mode_parity.py`; `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline`.

The docstring of `test_label_sinks.py` (lines 90-92: "A TeX string among them is rendered by MathJax to an SVG that is drawn as an image, which runs nothing"; lines 96-117, "The TeX finding") states today's behaviour and is rewritten in task 09-05.

### E8. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, index at `c96facd`)

| Symbol | Edit | Risk | Direct callers |
|---|---|---|---|
| `DashRenderer._build_sources_and_figures` | one call appended | CRITICAL (14 impacted, 7 processes) | `_setup_sources`, `render` |
| `ServerAppBuilder._generate_app_source` | one generated statement (plus three comment lines) | HIGH (5) | `build` |
| `ServerAppBuilder._glyph_layer_lines` | four tuple names | HIGH (4) | `_generate_app_source` |
| `_dash_inert_tex` | not edited (called) | HIGH (5) | `_dash_filter_title` |
| `DashRenderer._stale_cue_args` | not edited (order only) | CRITICAL (6) | `_build_filter_widgets` |
| new: `_dash_finish_graph_text`, `_dash_graph_text_models`, `_dash_graph_text_props`, `_dash_finish_text_value`, `_DASH_GRAPH_TEXT_SINKS`, `_DASH_GRAPH_TEXT_DONE` | added | no callers yet | — |

No `UNKNOWN` verdict; no Stata or Mata program is edited (dash.ado passes the text through intact, research p1-11 c1.do).

## User stories

- **US-09.1** As a twoway user, I want `title("\(y\)")`, `note("\$\$ x \$\$")`, `xlabel(2000 "\(t\)")` and a variable or value label holding `\[z\]` drawn exactly as I typed them, as twoway draws them, so my dashboard's text matches my Stata graph.
- **US-09.2** As a dashboard publisher, I want a saved page whose text holds a TeX pair to be the size of the same page without it (about 1.3 MB, not 3.1 MB), because nothing on it needs a TeX engine.
- **US-09.3** As a dashboard publisher, I want no text from my data or my options handed to MathJax in either mode, so a hostile label such as `$$\href{javascript:…}{x}$$` can never become a link or a style.
- **US-09.4** As a dashboard publisher, I want the text to stay as typed after any filter move, on the saved page and in the served app.
- **US-09.5** As the maintainer, I want a test that fails the day a later change adds canvas text that skips this rule, and a pass that later work extends without editing the two builders.

## Business requirements

- **BR-09.1** Every TeX delimiter pair (`$$…$$`, `\(…\)`, `\[…\]`) in text dash draws on a graph — graph title, subtitle, note, caption, x/y/second-axis titles (typed or from a variable label), tick labels (typed or value labels), by() panel titles, legend keys and titles, the colour bar's title and tick labels — is drawn as typed, in both modes. Removing the invisible joiner gives back exactly the typed text.
- **BR-09.2** A saved page holding such text does not ship `bokeh-mathjax`, and its size is within 2,000 bytes of the same page with the pairs replaced by plain words.
- **BR-09.3** No model of a saved or served document satisfies Bokeh's MathJax test (`_model_requires_mathjax`) because of user text, and no canvas text model holds a pair BokehJS parses (no `TeX` view in the browser).
- **BR-09.4** After a filter move, in both modes, the canvas text is the text drawn before the move (plus the stale-cue suffix on a saved frozen key), still without a live pair.
- **BR-09.5** Text without a TeX pair is drawn exactly as before: no page that holds none changes by a byte (beyond per-run ids).
- **BR-09.6** dash prints nothing about this text, in either mode (M6), and refuses nothing (M5: twoway accepts it).

## Technical requirements

- **TR-09.1 The sink table and the mark.** Directly after `_dash_inert_tex` (after its `return s`, dash_render.py:24043, and before `def _dash_filter_title`, :24047), add:

  ```python
  #: Every canvas text sink the document pass finishes (WP-30 P1.11a), as
  #: (Bokeh class, property, how the property holds its text).  twoway draws
  #: graph text as typed.  BokehJS 3.8-3.9 typesets a TeX delimiter pair with
  #: MathJax in a Title or Label (TextAnnotationView), an axis label or tick
  #: override (AxisView), and the Title and axis a ColorBar draws itself.  A
  #: Legend's entries and title are DOM text and a tick formatter's map comes
  #: back as plain text; they are finished too, so all of a graph's text
  #: follows one rule.
  _DASH_GRAPH_TEXT_SINKS = (
      ("Title", "text", "text"),
      ("Label", "text", "text"),
      ("Axis", "axis_label", "text"),
      ("Axis", "major_label_overrides", "map"),
      ("ColorBar", "title", "text"),
      ("ColorBar", "major_label_overrides", "map"),
      ("Legend", "title", "text"),
      ("LegendItem", "label", "value"),
      ("CustomJSTickFormatter", "args", "labels"),
  )

  #: The attribute the pass sets on each sink model it has finished: a plain
  #: Python attribute, never a Bokeh property, so it is not written into the
  #: page and a page whose text holds no TeX pair is unchanged.
  _DASH_GRAPH_TEXT_DONE = "_dash_graph_text"
  ```

- **TR-09.2 `_dash_graph_text_models(fig)`** returns, in this order, `fig.title` (if a Bokeh `Model`), then for each side in `("above", "below", "left", "right", "center")` every `Model` in that list, followed by its `formatter` when that is a `Model` (an Axis's or ColorBar's; a ColorBar's default `"auto"` is a string and skipped) and, for a `Legend`, each `Model` in its `items`. It never calls `references()` or reads a source (Risk 2). Local imports: `from bokeh.model import Model`, `from bokeh.models import Legend`. Use plain `for` loops (no nested `def`, no `lambda`; the function map counts nested functions). Docstring: what it walks, and the 7.08 s against 0.067 s measurement.

- **TR-09.3 `_dash_graph_text_props(model)`** returns a tuple of `(prop, how)` for each row of `_DASH_GRAPH_TEXT_SINKS` whose class (`getattr(bokeh.models, name, None)`) the model is an instance of, and `()` otherwise. A `CustomJSTickFormatter` counts only when its `args` keys are exactly `{"labels"}` and `args["labels"]` is a `str` (the map `_dash_apply_axis_spec` writes, E2); the display-format writer (`args` with `fmt`, `kind`, `storage`) is not a sink. It reads class names only from the constant table, never from the document.

- **TR-09.4 `_dash_finish_text_value(value, how)`** returns `(new, changed)` and never mutates its argument:
  - `"text"`: a `str` → `_dash_inert_tex(value)`; anything else (None, a Bokeh text model) is returned with `False`.
  - `"map"`: a non-empty mapping → `{k: _dash_inert_tex(v) if isinstance(v, str) else v}` over `dict(value).items()` (keys kept, non-string values kept); `changed` is `new != dict(value)`.
  - `"value"`: the fixed text of a LegendItem label — `value.value` for a Bokeh `Value`, `value["value"]` for a dict without `"field"`, or a bare `str` — finished and returned as `{"value": new}`; a `Field` label (no `value` attribute) or anything else is returned unchanged.
  - `"labels"`: `args = dict(value)`; `json.loads(args["labels"])`; if that raises `TypeError`/`ValueError`, or is not a `dict` whose values are all `str`, return unchanged; otherwise finish every value, and if any changed set `args["labels"] = json.dumps(new_map)` (default separators and key order, as :22813 writes it) and return `(args, True)`.
  - `changed` is False whenever the text held no delimiter; the caller then writes nothing (BR-09.5).

- **TR-09.5 `_dash_finish_graph_text(figures)`.** `figures` maps each graph's or panel's key to its figure (`self.figures`; the served `figures`). For each `(key, fig)` in `list(figures.items())`, for each model of `_dash_graph_text_models(fig)`: skip it if `id(model)` was seen this call or `getattr(model, _DASH_GRAPH_TEXT_DONE, False)` is true; record the id; get `_dash_graph_text_props(model)`; if empty, continue; set `setattr(model, _DASH_GRAPH_TEXT_DONE, True)`; for each `(prop, how)`, `new, diff = _dash_finish_text_value(getattr(model, prop), how)` and `setattr(model, prop, new)` only when `diff`. Return the number of models with at least one property rewritten. The docstring states: what twoway does (E6); why last (E4); that a sink created after the pass must be finished and marked by its creator, or carry constant text (the stale-cue caption); that the key is unused here and is how S29 finds a panel's graph (`<name>__by__<i>`); that nothing is printed (M6). It does not touch `GlyphRenderer.name`, `CategoricalColorMapper.factors`, sources, `LabelSet`, `HoverTool`, widgets or Divs.

- **TR-09.6 Saved call site.** After the `) from exc` that ends the "3. Build figures" loop (dash_render.py:31689), at method-body indentation (8 spaces), append:

  ```python
          # ---- 3e. Every canvas text drawn as typed (WP-30 P1.11a) ----
          # Last: every figure, by() panel title and shared by() scale is
          # built, and _build_filter_widgets (_stale_cue_args) has not yet
          # copied the legend text the saved filter script writes back.
          _dash_finish_graph_text(self.figures)
  ```

  `render()`, `_setup_sources` and `_build_figures` all reach it through `_build_sources_and_figures`; no other method is edited.

- **TR-09.7 Served call site and copy list.**
  - In `_generate_app_source`, between the line `""` that follows `"                               if _f in figures], _brs)",` (:35654-35655) and `"    # ---- Persist per-graph qualifier metadata for filter callbacks ----",` (:35656), insert:

    ```python
                "    # Every canvas text drawn as typed (WP-30 P1.11a): last, once",
                "    # every figure, by() panel title and shared scale is built,",
                "    # as the saved renderer's _build_sources_and_figures ends.",
                "    _dash_finish_graph_text(figures)",
                "",
    ```

  - In the `_glyph_layer_lines` functions tuple, after `"_dash_inert_tex",` (:33278) and before `"_dash_filter_title",`, insert one line `"_dash_finish_graph_text", "_dash_graph_text_models",` and one line `"_dash_graph_text_props", "_dash_finish_text_value",` with a comment `# The canvas-text pass (WP-30 P1.11a) and its helpers.` (R2 row S09). The two constants travel through `_supply_missing_constants` (E5); no constants-tuple entry.

- **TR-09.8 No JavaScript twin.** The pass runs in Python before either document is serialised. The only saved script that writes canvas text, `_FILTER_JS`'s stale-cue label rewrite (:19341-19344), writes text the pass has already finished (TR-09.6 order). No served callback writes canvas text (E4). `_FILTER_JS` is not edited.

- **TR-09.9 Registries.** Under the S09 anchor at the end of `FUNCTIONS` in `test/function_test_map.py`, alphabetically:
  - `'_dash_finish_graph_text': 'test/test_canvas_tex.py::TestTheDocumentPass::test_each_sink_is_finished'`
  - `'_dash_finish_text_value': 'test/test_canvas_tex.py::TestFinishTextValue::test_text_kind_breaks_every_delimiter'`
  - `'_dash_graph_text_models': 'test/test_canvas_tex.py::TestTheDocumentPass::test_the_walk_finds_every_text_model_and_no_source'`
  - `'_dash_graph_text_props': 'test/test_canvas_tex.py::TestTheDocumentPass::test_the_sink_props_name_only_text_sinks'`

  No Stata program or Mata function is added, so `test/program_coverage_map.py` is unchanged.

- **TR-09.10 Flips (R9).** In `test/test_label_sinks.py` add a module helper `_finished(c)` — true when `isinstance(c.model, getattr(bokeh.models, cls))` and `c.prop == prop` for some row of `dr._DASH_GRAPH_TEXT_SINKS`. In `TestTextSinks::test_it_carries_the_raw_text` and `::test_a_tick_label_map_carries_the_raw_text`, when `pid in TEX_PAYLOADS` and `_finished(c)`: assert no `_TEX_DELIM_RE` match, `not contains_tex_string(...)`, and `want in text.replace(WJ, "")`; otherwise keep `want in c.text` unchanged. Each test's docstring gains: "Flipped (WP-30 P1.11a): a TeX pair in canvas text was typeset by MathJax where twoway draws it as typed; every canvas sink now carries the typed text with each delimiter broken by a WORD JOINER, which the reader does not see." In `test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_label_text_is_a_label_and_never_read`, replace the last assertion with `lab = fig.legend[0].items[0].label.value`, `assert lab.replace(dr._DASH_WORD_JOINER, "") == text` and `assert not contains_tex_string(lab)` (import from `bokeh.embed.util`), with a one-line comment giving the same reason. Rewrite `test_label_sinks.py`'s docstring lines 90-92 and add a third paragraph to "The TeX finding" (lines 96-117) saying that canvas sinks are finished by `_dash_finish_graph_text` in both modes (WP-30 P1.11a) and a saved page no longer ships MathJax for them.

- **TR-09.11 Help.** In dash.sthlp, the Server Mode paragraph that begins "Within the file, data values are base64-encoded" (:1721-1725 at `c96facd`) and ends "never as markup of its own.", append (lines under 80 characters):

  ```
  Text drawn on a graph -- a title, subtitle, note, caption, axis title,
  tick label, legend key, {cmd:by()} panel title or colour key -- is never
  handed to a TeX engine: {cmd:$$}, {cmd:\(} and {cmd:\[} in it are drawn
  as typed, as {cmd:twoway} draws them, in a saved page and a served one.
  ```

  No other help paragraph is edited (A155; Notes R3).

- **TR-09.12 Security (rule 1).** The pass only inserts U+2060 before a delimiter's second character: output length is at most twice the input, time is linear (two `re.sub` with a one-character lookahead), and no markup or escaping is introduced (canvas text stays raw, as `TestTextSinks` requires). The label map stays data in `args`, decoded by `JSON.parse` in a constant `code` (`TestJavaScript` unchanged). No property name or class is read from the document; no `eval`, `exec`, shell or file access. In the served app the pass runs inside `make_document` on that session's own models; it mutates no module state (the mark is per model). The commit body names the threat closed: user text reaching MathJax's TeX parser (`\href{javascript:…}`, `\style{…}`) on every canvas sink, in both modes (G9).

- **TR-09.13 Budget.** The pass over a 100-panel by() graph adds well under 0.2 s (measured 0.067 s); `test_a_hundred_panels_take_well_under_a_second` bounds it at 1 s on hand-built figures.

## Boundaries

- **Not this section (S29, P1.11b, batch 10):** SMCL translation (`{bf:}`, `{&name}`, `{c #}`, font tags), `_dash_graph_text`, style properties (`text_font_style`, `title_text_font_style`, `label_text_font_style`), the mlabel column (`_apply_mlabel_opts`, `_mlabel_column_kind`, `LabelSet`), DOM sinks (`_dash_filter_title`, `Select`, `TabPanel`, tooltips), notes, `graph_text_truth.json`, the "Text in graphs" help paragraph. S09 leaves every DOM sink and the mlabel column raw.
- **Batch partners:** S07 owns the scheme extractor, the 26 scheme files, `scheme_truth.json`, `_dash_shipped_schemes`, `SchemeParser._BUILTIN_NAMES`, dash.pkg and the help's scheme section. S08 owns `translate_msize`, `resolve_size`, `_textbox_size`, `_mlabel_gap_px`, `_apply_marker_opts`, `_apply_mlabel_opts`, `_dash_apply_legend`, `_dash_apply_z_options`, the axis `labsize` path, dash.ado's size validation, the Marker Label Options help and CHANGELOG.md:522. S09 edits none of them.
- **Later sinks:** S19 (legend keys, default axis titles), S28 (by() titles, "Graphs by" note), S56 (`text()`/`ttext()` Labels) build their text raw before the pass, or finish and mark it themselves; `test_every_canvas_model_is_finished` holds them to it.
- **Not edited:** `_dash_inert_tex`, `_dash_filter_title`, `_stale_cue_args`, `_build_filter_widgets`, `_FILTER_JS`, `_dash_apply_axis_spec`, `_dash_text_annotations`, `_dash_axis_labels`, `GlyphMapper`, `dash.ado`, `dash_parse.mata`, `dash_setup.*`, `_DASH_WORD_JOINER`.
- **Residuals (register):** the served page still loads the MathJax bundle with Bokeh's server resources (P2.48, A36). twoway's macro expansion of `$name` inside labels is not reproduced (Notes for the closeout).
- **Decisions:** A35 (ratification item 7). If the maintainer strikes it in favour of an opt-in, this section is re-planned before batch 3's base is recorded (A151).

## Stata truth

**No fixture.** twoway's drawing of these texts is the identity (E6), so the comparison is made live, in the run, by the S09 block of `test/test_wp30_truth.cscript`; no extractor, no `_meta` stamp, no `git add -f`.

**The S09 block** fills S01's stub between its own start and end lines; S01's header line (`* ==== S09 P1.11a: TeX delimiters inert on every canvas sink ====`), its gate lines and `* ==== end S09 ====` are kept byte for byte (TR-01.10 item 4). It uses the scaffold's `_w30_expect`/`_w30_done` and `` `w30_work' `` (S01 TR-01.6), and erases its own files and graphs before its end line. Measured at `c96facd` with the same code in a scratch driver (`tx4.do`): TX-01 PASS; TX-02, TX-03, TX-04, TX-05 FAIL.

```stata
* ==== S09 P1.11a: TeX delimiters inert on every canvas sink ====
local only : env WP30_ONLY
if inlist("`only'", "", "S09") {
    display as text "S09 start " c(current_date) " " c(current_time)

    // TX-01 (guard, the truth): twoway draws each TeX pair as typed.
    sysuse auto, clear
    quietly twoway scatter mpg weight, title("\(y\)") subtitle("\[z\]") ///
        note("\$\$ x \$\$") xtitle("\(a\) w") xlabel(2000 "\(t\)" 3000) ///
        legend(on label(1 "\(k\)")) name(s09tx, replace)
    cert_svg_export, name(s09tx) file("`w30_work'/s09tx.svg")
    local s09_rc = r(rc)
    local s09_svg "`r(file)'"
    _w30_expect TX-01 "(`s09_rc' == 0)" "graph export rc `s09_rc'"
    foreach t in "\(y\)" "\[z\]" "\$\$ x \$\$" "\(a\) w" "\(t\)" "\(k\)" {
        cert_svg_has_text, file("`s09_svg'") text(`"`t'"')
        local s09_f = r(found)
        _w30_expect TX-01 "(`s09_f' == 1)" `"twoway did not draw `t' as typed"'
    }
    _w30_done TX-01 "twoway draws each TeX pair as typed"

    // TX-02: the same options in dash: the saved page ships no MathJax.
    quietly dash scatter mpg weight, title("\(y\)") subtitle("\[z\]") ///
        note("\$\$ x \$\$") xtitle("\(a\) w") xlabel(2000 "\(t\)" 3000) ///
        legend(on label(1 "\(k\)")) saving("`w30_work'/s09tx.html", replace)
    cert_file_has "`w30_work'/s09tx.html", needle("bokeh-mathjax")
    local s09_mj = r(found)
    _w30_expect TX-02 "(`s09_mj' == 0)" "the saved page ships bokeh-mathjax"
    _w30_done TX-02 "a saved page with TeX pairs ships no MathJax"

    // TX-03: the title is the typed text with its delimiters broken (the
    // page JSON writes U+2060 as \u2060 and a backslash as \\).
    cert_file_has "`w30_work'/s09tx.html", needle("\\\u2060(y\\\u2060)")
    local s09_in = r(found)
    cert_file_has "`w30_work'/s09tx.html", needle(`""text":"\\(y\\)""')
    local s09_raw = r(found)
    _w30_expect TX-03 "(`s09_in' == 1 & `s09_raw' == 0)" ///
        "title keeps a live pair (inert `s09_in', raw `s09_raw')"
    _w30_done TX-03 "the title is the typed text with its delimiters broken"

    // TX-04: the TeX page is the size of the same page in plain words.
    quietly dash scatter mpg weight, title("y") subtitle("z") note("x") ///
        xtitle("a w") xlabel(2000 "t" 3000) legend(on label(1 "k")) ///
        saving("`w30_work'/s09plain.html", replace)
    checksum "`w30_work'/s09tx.html"
    local s09_n1 = r(filelen)
    checksum "`w30_work'/s09plain.html"
    local s09_n0 = r(filelen)
    display as text "S09 sizes: TeX page `s09_n1' bytes, plain page `s09_n0' bytes"
    _w30_expect TX-04 "(abs(`s09_n1' - `s09_n0') < 2000)" ///
        "TeX page `s09_n1' bytes against plain `s09_n0'"
    _w30_done TX-04 "the TeX page is the plain page's size"

    // TX-05: labels reach the canvas as typed (variable labels as axis
    // titles, a value label as a by() panel title).  No $name form: twoway
    // macro-expands those inside labels (E6), which is not TeX.
    sysuse auto, clear
    label variable mpg "\$\$ m \$\$"
    label variable weight "\(w\) lbs"
    label define s09o 0 "\(d\)" 1 "Foreign", replace
    label values foreign s09o
    quietly twoway scatter mpg weight, by(foreign) name(s09lb, replace)
    cert_svg_export, name(s09lb) file("`w30_work'/s09lb.svg")
    local s09_svg "`r(file)'"
    foreach t in "\$\$ m \$\$" "\(w\) lbs" "\(d\)" {
        cert_svg_has_text, file("`s09_svg'") text(`"`t'"')
        local s09_f = r(found)
        _w30_expect TX-05 "(`s09_f' == 1)" `"twoway did not draw the label `t' as typed"'
    }
    quietly dash scatter mpg weight, by(foreign) saving("`w30_work'/s09lb.html", replace)
    cert_file_has "`w30_work'/s09lb.html", needle("bokeh-mathjax")
    local s09_mj = r(found)
    cert_file_has "`w30_work'/s09lb.html", needle("\\\u2060(d\\\u2060)")
    local s09_in = r(found)
    _w30_expect TX-05 "(`s09_mj' == 0 & `s09_in' == 1)" ///
        "labels: bokeh-mathjax `s09_mj', inert panel title `s09_in'"
    _w30_done TX-05 "labels are drawn as typed and ship no MathJax"

    foreach f in s09tx.svg s09tx.html s09plain.html s09lb.svg s09lb.html {
        capture erase "`w30_work'/`f'"
    }
    capture graph drop s09tx s09lb

    display as text "S09 end " c(current_date) " " c(current_time)
}
* ==== end S09 ====
```

The measured output at `c96facd` (scratch `tx4.log`):

```
TX-01 PASS: twoway draws each TeX pair as typed
TX-02 FAIL: the saved page ships bokeh-mathjax
TX-03 FAIL: the title keeps a live TeX pair (inert 0, raw 1)
S09 sizes: TeX page 3087832 bytes, plain page 1301750 bytes
TX-04 FAIL: TeX page 3087832 bytes against plain 1301750
TX-05 FAIL: labels: mathjax 1, inert panel title 0
```

**Running it.** Through the driver only (index "The cscript driver"), from the worktree: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_test_wp30_truth.do"`, then `WP30_ONLY=S09 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_wp30_truth.do"`; the log is `$S/run_test_wp30_truth.log`. A `SKIP` (rc 222, `python_exec` lost from `stata19.rc`) is not a pass.

## TDD test stubs

The regression tests (fail at the batch-3 base, task 09-01):

- Test: a TeX title's saved page ships no `bokeh-mathjax`, no model satisfies `_model_requires_mathjax`, and its length is within 2,000 bytes of the same spec with `title("y")` (measured at `c96facd` in the dev interpreter: 3,558,473 against 1,772,437 bytes) — `test/test_canvas_tex.py::TestTheSavedPage::test_a_tex_title_ships_no_mathjax`
- Test: a spy on `dr._dash_finish_graph_text` and `DashRenderer._stale_cue_args` (monkeypatch, recording order) shows the pass runs first on a spec with an lfit and a dropdown — `test/test_canvas_tex.py::TestTheSavedPage::test_the_pass_runs_before_the_stale_cue_reads_the_legend`
- Test: on that spec with `legend(label(2 "\(fit\)"))`, every `items` text in the callbacks' `stale_configs_json` holds no delimiter and equals `\(fit\)` once `WJ` is removed — `test/test_canvas_tex.py::TestAfterAFilterMove::test_saved_stale_cue_carries_the_finished_key`
- Test (node; `requires_node`): after moving the dropdown to Foreign under `JsSession` (test_saved_stale_cue's `_act`), the lfit's LegendItem label is `dr._dash_inert_tex("\\(fit\\)") + dr._DASH_STALE_SUFFIX["fit"]` and holds no delimiter; the Title text is unchanged — `test/test_canvas_tex.py::TestAfterAFilterMove::test_saved_key_after_the_move`
- Test: served (test_mode_parity `_served`, `_fire`): a snapshot of every finished sink's `(class, prop, value)` over all figures is equal before and after the Select move, and none holds a delimiter — `test/test_canvas_tex.py::TestAfterAFilterMove::test_served_text_is_unchanged_by_a_move`
- Test: both modes, `colorvar(price)` with `ztitle("\(c\)")` and `zlabel(5000 "$$a$$" 10000)`, and `colorvar(rep) colordiscrete` with `ztitle("\[d\]")`: ColorBar title and overrides, Legend title and keys hold no delimiter and show the typed text — `test/test_canvas_tex.py::TestBothModes::test_the_colour_key_text[standalone|served]`
- Test: both modes, `title("\(")` with `by(foreign, total)` and value label `1 "y\)"` (its own data, `conftest.make_data_json(_DF, {"origin": {"0": "Domestic", "1": "y\\)"}}, {"foreign": "origin"})`): no panel Title (Total included) holds a pair, though the pair `\( — y\)` exists only after the panel join — `test/test_canvas_tex.py::TestBothModes::test_a_pair_formed_by_the_panel_join_is_broken[standalone|served]`
- Test (guard for later sections): both modes, on the hostile `all` dashboard of `test_label_sinks.hostile_inputs`, every model for which `dr._dash_graph_text_props(m)` is non-empty carries the mark, except a Title tagged `dash_stale_cue` — `test/test_canvas_tex.py::TestBothModes::test_every_canvas_model_is_finished[standalone|served]`
- Test: the generated source holds `_dash_finish_graph_text(figures)` after the last `_dash_share_by_scales([figures[_f]` and after `fig.title.text = (f'{_own}`, and before `# ---- Persist per-graph qualifier metadata` and `# ---- Filter widgets + Python callbacks ----` — `test/test_canvas_tex.py::TestTheServedApp::test_make_document_runs_the_pass_after_the_panels_and_before_the_widgets`
- Test: the generated source defines the four functions with the same text as `inspect.getsource` (dedented) and assigns `_DASH_GRAPH_TEXT_SINKS` and `_DASH_GRAPH_TEXT_DONE` — `test/test_canvas_tex.py::TestTheServedApp::test_the_pass_travels_by_source`
- Test (Chrome; skip without it, red under `DASH_STRICT=1`, `_run_chrome` from `test_stale_cue_browser`): the saved page of E3's spec, probed with `Bokeh.index.all_views()`, has 0 `TeX` views and at least 7 `PlainText` ones — `test/test_canvas_tex.py::TestInChrome::test_bokehjs_draws_every_canvas_text_as_plain_text`
- Test: dash.sthlp's paragraph beginning "Within the file, data values are base64-encoded" holds "is never handed to a TeX engine" and "drawn as typed, as {cmd:twoway} draws them" (whitespace-normalised) — `test/test_canvas_tex.py::TestTheHelp::test_the_help_says_tex_is_drawn_as_typed`
- Test: both modes × `tex_inline|tex_display|tex_bracket`: no carrier for which `_finished(c)` holds has a delimiter or `contains_tex_string`, at least 40 such carriers exist (44 in each mode with the prototype), and no model satisfies `_model_requires_mathjax` (measured with the prototype: none, in both modes, for all three payloads) — `test/test_label_sinks.py::TestTeX::test_no_canvas_sink_holds_tex`
- Test: `tex_inline|tex_display|tex_bracket`: the saved hostile page holds no `bokeh-mathjax` (measured 4,228,742 → 2,443,240 bytes for `tex_inline` with the prototype) — `test/test_label_sinks.py::TestTeX::test_the_saved_page_ships_no_mathjax`
- Unit tests of the new functions (fail with `AttributeError` at the base):
  - `test/test_canvas_tex.py::TestFinishTextValue::test_text_kind_breaks_every_delimiter` — `"text"` over TestInertTex's delimiter list; `changed` true; joiner removed gives the input.
  - `::TestFinishTextValue::test_text_without_tex_is_unchanged_and_reported_so` — `("Price $", False)`, `(None, False)`.
  - `::TestFinishTextValue::test_map_kind_finishes_values_and_keeps_keys` — `{2000.0: "\(t\)", 3000.0: "plain"}`.
  - `::TestFinishTextValue::test_value_kind_finishes_a_fixed_label_and_leaves_a_field` — `Value`, dict, `str`; `Field("k")` unchanged.
  - `::TestFinishTextValue::test_labels_kind_rewrites_the_json_map` — `{"labels": json.dumps({"2000.0": "$$a$$"})}` → re-dumped, keys kept.
  - `::TestFinishTextValue::test_a_malformed_label_map_is_left_alone` — bad JSON, a list, a non-string value, a missing key.
  - `::TestTheDocumentPass::test_each_sink_is_finished` — a hand-built figure (title, x/y labels and overrides, a right `LinearAxis`, the label-map formatter, a `Label`, a `Legend` with a value and a field item, a `ColorBar` with title and overrides) all holding `\(x\)`: no delimiter left anywhere, joiner removed gives the input, return value 9.
  - `::TestTheDocumentPass::test_text_without_tex_leaves_the_document_unchanged` — the same figure in plain words in a `Document`: `json.dumps(doc.to_json(), sort_keys=True, default=str)` equal before and after; return 0.
  - `::TestTheDocumentPass::test_a_second_call_changes_nothing` — second call returns 0, document JSON equal.
  - `::TestTheDocumentPass::test_a_finished_model_is_not_visited_again` — a Title with the mark set and raw `\(x\)` keeps it (the contract for sinks made after the pass).
  - `::TestTheDocumentPass::test_every_other_model_is_left_alone` — a string column, a swatch renderer name, `CategoricalColorMapper.factors`, a `LabelSet(text="col")`, `HoverTool` tooltips and the display-format formatter, all holding `\(x\)`, are unchanged.
  - `::TestTheDocumentPass::test_the_walk_finds_every_text_model_and_no_source` — `_dash_graph_text_models` lists the title, the axes, the formatter, the legend and its items, the colour bar, and no `ColumnDataSource`; with `bokeh.model.Model.references` monkeypatched to raise, the pass completes.
  - `::TestTheDocumentPass::test_the_sink_props_name_only_text_sinks` — props for each sink class; `()` for the display-format formatter, a `Grid`, a `Span`.
  - `::TestTheDocumentPass::test_a_hundred_panels_take_well_under_a_second` — 100 hand-built figures; the pass under 1 s.

Guard tests (pass at the base; listed apart in the failure file):
- TX-01 (twoway truth).
- `test/test_mode_parity.py::TestTheTwoModesAgree` with the new CORPUS case `"TeX pairs in every canvas text (WP-30 P1.11a)"` (both modes agree before and after the fix).
- `test/test_label_sinks.py::TestInventory`, `::TestSliderTitles`, `::TestInertTex`, `::TestJavaScript` (unchanged; must stay green).

Pinned tests flipped in task 09-05 (E7): `test/test_label_sinks.py::TestTextSinks::test_it_carries_the_raw_text` (102 ids), `test/test_label_sinks.py::TestTextSinks::test_a_tick_label_map_carries_the_raw_text` (12 ids), `test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_label_text_is_a_label_and_never_read`.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| The four functions | pytest `test_canvas_tex.py::TestFinishTextValue`, `::TestTheDocumentPass` | hand-built Bokeh models | n/a (pure; the served copy is the same text) |
| Every canvas sink, hostile inputs | pytest `test_label_sinks.py` (TestTeX new, TestTextSinks flipped, TestInventory) | `hostile_inputs` | yes |
| Colour key, panel join, guard | pytest `test_canvas_tex.py::TestBothModes` | test_mode_parity `_DF` | yes |
| Saved page weight | pytest `TestTheSavedPage`; cscript TX-02, TX-04 | `_DF`; sysuse auto | saved |
| After a filter move | pytest `TestAfterAFilterMove` (stale-cue config; node; served `_fire`) | `_DF`, dropdown | yes |
| Served wiring | pytest `TestTheServedApp`; `TestTheServedAppDefinesEveryNameItReads`; `TestTheServedAppCarriesEveryName` | generated source | served |
| Parity | pytest `test_mode_parity.py` CORPUS case | `_DF` | yes |
| BokehJS draws plain text | headless Chrome `TestInChrome` | `_DF` | saved |
| twoway truth | cscript TX-01, TX-05 | sysuse auto | n/a |
| Help | pytest `TestTheHelp` | dash.sthlp | n/a |
| Registries and tracking | `test_function_test_map.py`, `test_tracking_documents.py`, `test_cscript_hygiene.py` | — | n/a |

**Acceptance criteria.**
- **AC-09.1** (BR-09.1) In both modes, every finished sink of the hostile dashboard and of `TestBothModes`'s specs holds no TeX delimiter, and removing U+2060 gives exactly the typed text.
- **AC-09.2** (BR-09.2) TX-02 and TX-04 PASS: no `bokeh-mathjax`, and the TeX page is within 2,000 bytes of the plain page (`S09 sizes:` line printed); `test_a_tex_title_ships_no_mathjax` and `test_the_saved_page_ships_no_mathjax` pass.
- **AC-09.3** (BR-09.3) `test_no_canvas_sink_holds_tex` passes in both modes; `TestInChrome` reports 0 `TeX` views.
- **AC-09.4** (BR-09.4) The three `TestAfterAFilterMove` tests pass (the node one is not skipped on this machine).
- **AC-09.5** (BR-09.5) `test_text_without_tex_leaves_the_document_unchanged` passes and `test_varlist_expansion.py::test_single_y_output_matches_prefix_baseline` passes with the batch-3 base's digest.
- **AC-09.6** (BR-09.6) No warning text is added: `test_mode_parity.py` (`_MUST_WARN` untouched) and the hostile builds' warnings are unchanged.
- **AC-09.7** Order: `test_the_pass_runs_before_the_stale_cue_reads_the_legend` and `test_make_document_runs_the_pass_after_the_panels_and_before_the_widgets` pass.
- **AC-09.8** The 115 flipped ids pass with their new expectations, and every other test in `test_label_sinks.py` and `test_help_claims_7.py` passes unchanged.
- **AC-09.9** TX-01..TX-05 print PASS under `WP30_ONLY=S09`, with no SKIP.
- **AC-09.10** The full suite through the queue reports 0 failed; the registry tests are green; G7 prints 0.

## Tasks

**Commit boundary.** All eight tasks form the one commit of entry `P1.11a`, made by task 09-08 on `wp30-s09` with the subject `Draw TeX delimiters in graph text as typed on every canvas sink (WP-30 P1.11a)`. `<scratch>` is the orchestrator's WP-30 scratch directory (index "Deltas"), `$S` is `<scratch>/s09` (created by 09-01 with `mkdir -p "$S"`), `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s09`; every command runs with `git -C "$WT"` or with `$WT` paths, never in the main checkout.

<task type="auto" id="09-01">
  <name>Write the failing tests and record them</name>
  <files>test/test_canvas_tex.py, test/test_label_sinks.py, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Run `mkdir -p "$S"`. Check `git -C "$WT" rev-parse HEAD` equals `cat "<scratch>/batch-3-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s09`; stop otherwise. Before editing anything, save the base count: `python3 -m pytest test/test_label_sinks.py test/test_help_claims_7.py --collect-only -q -p no:cacheprovider | tail -1 > "$S/09-collect-base.txt"`. Create `test/test_canvas_tex.py` with every `test_canvas_tex.py` stub of "TDD test stubs" (module docstring: the defect of the Overview, the twoway truth of E6, the BokehJS sites of E3; import helpers from `test_mode_parity` (`_spec`, `_standalone_page`, `_served`, `_fire`, `_widgets_of`, `_DF`), `test_saved_stale_cue` (`_render`, `_act`, `_items_of`, `_layer_rends`, `_text`), `test_server_layer_defects.plot_for`, `test_stale_cue_browser._run_chrome`, `js_runner.requires_node`, `responsive_probe`); reference the new names as `dr._dash_finish_graph_text` etc. so they fail with AttributeError now. In `test/test_label_sinks.py` add `_finished(c)` (TR-09.10) and the two new `TestTeX` tests. Replace the body of S01's S09 stub in `test/test_wp30_truth.cscript` with the block of "Stata truth", using S01's helper names. Run `python3 -m pytest test/test_canvas_tex.py "test/test_label_sinks.py::TestTeX" -q -n0 -p no:cacheprovider -rf > "$S/09-new.log" 2>&1` and the S09 block through the driver ("Stata truth", Running it). Write `$S/09-P1.11a-failure.txt`: the base sha, one failure line per regression test from `09-new.log`, the TX lines of `run_test_wp30_truth.log`, and the guard tests that pass (TX-01, the `all`-payload rows). Do not commit; do not edit `dash_render.py`.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/09-new.log"` is at least 30; `grep -c "TX-0[2-5] FAIL" "$S/run_test_wp30_truth.log"` prints 4 and `grep -c "TX-01 PASS" "$S/run_test_wp30_truth.log"` prints 1; `test -s "$S/09-P1.11a-failure.txt"`; `git -C "$WT" diff --name-only -- dash_render.py` prints nothing.]]></verify>
  <done>Every regression test of P1.11a was shown failing on the unmodified tree, the twoway truth case passed, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="09-02">
  <name>Add the canvas-text pass and its helpers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In dash_render.py, after `_dash_inert_tex`'s `return s` (24043) and before `def _dash_filter_title` (24047), add `_DASH_GRAPH_TEXT_SINKS` and `_DASH_GRAPH_TEXT_DONE` exactly as TR-09.1 gives them, then `_dash_graph_text_models` (TR-09.2), `_dash_graph_text_props` (TR-09.3), `_dash_finish_text_value` (TR-09.4) and `_dash_finish_graph_text` (TR-09.5), each with a docstring saying what it does and why (twoway truth E6, BokehJS sites E3, the order of E4, the 7.08 s walk). Use only local imports of bokeh names, plain loops (no nested def, lambda or comprehension holding a def), `json` and `_dash_inert_tex` from the module. Do not call the pass from anywhere yet, and touch no other function. The six names are new, so no impact run is needed for them.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_canvas_tex.py::TestFinishTextValue" "test/test_canvas_tex.py::TestTheDocumentPass" -q -n0 -p no:cacheprovider` passes (all tests of both classes); `python3 -c "import sys; sys.path.insert(0,'$WT'); import dash_render as d; print(len(d._DASH_GRAPH_TEXT_SINKS))"` prints 9.]]></verify>
  <done>The pass and its three helpers existed with unit tests green, and nothing yet called them.</done>
</task>

<task type="auto" id="09-03">
  <name>Run the pass after the saved build</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `DashRenderer._build_sources_and_figures`, after the `) from exc` that ends the "3. Build figures" loop (31689), add the four lines of TR-09.6 at 8-space indentation, as the method's last statement. This is the batch's one edit of this CRITICAL method (R12; impact recorded in `<scratch>/batch-3-impact.txt`). Edit nothing else.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_canvas_tex.py -q -n0 -p no:cacheprovider -k "TestTheSavedPage or standalone or test_saved_stale_cue_carries or test_saved_key_after_the_move or TestInChrome"` passes with no skip; `python3 -m pytest "test/test_label_sinks.py::TestTeX" -q -n0 -p no:cacheprovider -k standalone` passes; the S09 truth block through the driver prints TX-01..TX-05 PASS and a `S09 sizes:` line whose two numbers differ by under 2,000.]]></verify>
  <done>The saved page drew every canvas TeX pair as typed, shipped no MathJax, and kept the finished legend text through a filter move.</done>
</task>

<task type="auto" id="09-04">
  <name>Carry the pass to the served app</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `ServerAppBuilder._glyph_layer_lines`'s functions tuple, after `"_dash_inert_tex",` (33278) and before `"_dash_filter_title",`, insert the comment and two lines of TR-09.7. In `ServerAppBuilder._generate_app_source`, between the `""` at 35655 and `"    # ---- Persist per-graph qualifier metadata for filter callbacks ----",` (35656), insert the five generated lines of TR-09.7. This is the batch's one edit of `_generate_app_source` (R12). Edit nothing else.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_canvas_tex.py test/test_label_sinks.py -q -n0 -p no:cacheprovider -k "(served or TestTheServedApp or TestTeX or TestInventory or TestSliderTitles) and not TestTextSinks"` passes (TestTextSinks' served TeX rows stay red until 09-05 flips them); `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>The served app ran the same pass after its panels and shared scales were built, and its canvas text stayed inert after a filter move.</done>
</task>

<task type="auto" id="09-05">
  <name>Flip the pinned TeX expectations</name>
  <files>test/test_label_sinks.py, test/test_help_claims_7.py</files>
  <action><![CDATA[
    Apply TR-09.10: in `test/test_label_sinks.py` change `TestTextSinks::test_it_carries_the_raw_text` and `::test_a_tick_label_map_carries_the_raw_text` so a TeX payload on a `_finished` carrier asserts no delimiter, no `contains_tex_string` and `want in text.replace(WJ, "")`, every other case keeping `want in c.text`; add the "Flipped (WP-30 P1.11a)" sentence to both docstrings; rewrite the module docstring's lines 90-92 and add the third paragraph to "The TeX finding". In `test/test_help_claims_7.py` change the last assertion of `TestAdversarialLegendAxesRegions::test_label_text_is_a_label_and_never_read` as TR-09.10 says. Delete no test and no parametrisation. Write the three `Flipped:` lines (index R9 form, with the old expectation and why it was wrong) to `$S/09-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_label_sinks.py test/test_help_claims_7.py -q -n 6 -p no:cacheprovider` reports 0 failed, and its collected count equals the count in `$S/09-collect-base.txt` (written by 09-01 before any edit) plus 9, the ids of the two new `TestTeX` tests; `test -s "$S/09-flips.txt"`.]]></verify>
  <done>The 115 pinned TeX expectations were flipped in place with their reason, and both files were green.</done>
</task>

<task type="auto" id="09-06">
  <name>Register the names and the parity case</name>
  <files>test/function_test_map.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Under the anchor `# WP-30 S09 (P1.11a): TeX delimiters inert on every canvas sink` in `test/function_test_map.py`, add the four entries of TR-09.9 in alphabetical order. At the end of `CORPUS` in `test/test_mode_parity.py` (before its closing `]`, 1798 at the base; after any case S08 appended), add `_case("TeX pairs in every canvas text (WP-30 P1.11a)", [_sc(), plot_for("lfit")], go={"title": '"\\(y\\)"', "subtitle": '"\\[z\\]"', "xtitle": '"$$x$$"', "xlabel": '3000 "\\(t\\)" 4000', "legend": 'label(2 "\\(f\\)")'})`. Do not edit `ALLOWED` or `_MUST_WARN` (R8).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py -q -n0 -p no:cacheprovider` passes; `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider -k "TeX pairs"` passes (both modes agree).]]></verify>
  <done>The four new functions were mapped to their tests and the two modes were shown to agree on a dashboard whose every canvas text holds a TeX pair.</done>
</task>

<task type="auto" id="09-07">
  <name>State the rule in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    In dash.sthlp, find the paragraph that begins "Within the file, data values are base64-encoded" (1721-1725 at `c96facd`; search by text, since S04 may have moved it) and append the four lines of TR-09.11 after "never as markup of its own." in the same paragraph. Edit no other paragraph (A155, R3).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_canvas_tex.py::TestTheHelp" test/test_help_conformance.py -q -n 6 -p no:cacheprovider` passes; `awk 'length > 79' dash.sthlp | grep -c "TeX engine"` prints 0.]]></verify>
  <done>The help said that text on a graph is never handed to a TeX engine and is drawn as typed, as twoway draws it.</done>
</task>

<task type="auto" id="09-08">
  <name>Close the entry and make the commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.11a"]`. In BUGS.md close that entry in place (`- [x]`) and replace its Resolution with the text of "Notes: BUGS.md Resolution", today's date in `ddmonyyyy`. Delete the `"P1.11a"` key line of `WP30_OPEN` in `test/test_tracking_documents.py`. In CHANGELOG.md replace each `<!-- WP-30 P1.11a -->` in place with the line given under "Notes: CHANGELOG lines", using the two byte counts the 09-03 driver run printed. Run `python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider`; then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); then one full run, `"<scratch>/full_suite_queue.sh" "$WT" "$S/09-full-1.log"` in the background, waiting for its `exit=` line and reading the log (never relaunching it). Stage exactly `dash_render.py dash.sthlp BUGS.md CHANGELOG.md test/test_canvas_tex.py test/test_label_sinks.py test/test_help_claims_7.py test/test_mode_parity.py test/function_test_map.py test/test_tracking_documents.py test/test_wp30_truth.cscript`; check `git -C "$WT" diff --cached --name-only` lists those 11 and nothing else (G6). Write the message to `$S/09-message.txt` in the form of "Notes: commit message", check `grep -Eic 'claude|anthropic' "$S/09-message.txt"` prints 0, confirm the branch prints `wp30-s09`, commit with `git -C "$WT" commit -F "$S/09-message.txt"`, and check the committed message the same way. Report the sha and message to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/09-full-1.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.11a -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.11a": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.11a)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.11a was closed naming existing tests, its two CHANGELOG markers carried the measured old and new page sizes, and one green commit on wp30-s09 was ready for the merger.</done>
</task>

## Section completion criteria

- Every TeX pair in canvas text is drawn as typed in both modes, before and after a filter move; the saved page ships no MathJax for it; no canvas model holds a live pair (pytest, TX-01..TX-05, Chrome).
- `_dash_finish_graph_text`, `_dash_graph_text_models`, `_dash_graph_text_props`, `_dash_finish_text_value`, `_DASH_GRAPH_TEXT_SINKS` and `_DASH_GRAPH_TEXT_DONE` exist, are mapped (TR-09.9) and travel to the served app; the pass runs once at the end of `_build_sources_and_figures` and once in `make_document` before the filter widgets.
- A page whose text holds no TeX pair is unchanged (the single-y digest passes at the base's value).
- The 115 pinned ids are flipped in place with their reason; no test is deleted; the collected count grows.
- One green commit `(WP-30 P1.11a)` exists on `wp30-s09`; its body opens with the failure text and carries the `Regression:`, `Flipped:` and `BUGS.md:` lines; entry P1.11a is closed, its `WP30_OPEN` key deleted, both markers replaced, the help sentence added.
- No file outside the 11 staged is changed; no fixture, extractor, runner block, hygiene pin, program map or tracking document beyond BUGS.md and CHANGELOG.md is touched.

## Notes

- **Order is the whole design.** The pass must see every canvas sink, so it runs after the by() panel join (a pair can exist only after `f"{orig_title} — {label}"`) and after `_dash_share_by_scales`; and it must run before `_stale_cue_args` copies legend text. Do not move the saved call into `render()`: `_setup_sources`/`_build_figures` (the test seams) would then return raw figures.
- **The mark is a Python attribute, not `tags`.** `tags` would be serialised, change every page and its digest, and mix with `dash_stale_cue`, which tests search for. Bokeh accepts any attribute starting with `_` (measured on 3.8.0 and 3.9.0; the document JSON is unchanged by it).
- **Never walk `references()`.** It visits every column value (Risk factor 2: 7.08 s per call on 100 panels).
- **Legends and the formatter map are not TeX-parsed by BokehJS 3.8-3.9**; they are finished so that one rule holds and S29 extends one table. Their flips are part of the 115.
- **Served notes.** None are added; M6 holds in both modes, so S23's relay is not involved.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the truth script then exits 222, and a SKIP is not a pass. Check the file after the driver runs.
- **Merge rules for the shared files.** R1: the S09 block of `test_wp30_truth.cscript` only. R2: four names after `"_dash_inert_tex",`; four map entries under S09's anchor (adjacent to S08's anchor: a context-only conflict the merger resolves by keeping both). R3/A155: dash.sthlp's Server Mode paragraph at 1721-1725, which no other section names; S04 (batch 2) owns the next paragraph (the CSP). R4: the two `P1.11a` markers only. R5: the `P1.11a` entry and key only (S08 deletes the adjacent `P1.12a` key line: the merger applies both). R8: one CORPUS case appended after S08's. R9: the flips of E7. R10: S09 does not move `_SINGLE_Y_BASELINE_SHA256` (measured); if the merged tree's digest test fails after S08 and S09 land, the merger re-derives it as R10 says. R12: S09 is batch 3's only editor of `_build_sources_and_figures` and `_generate_app_source`.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` after `git apply` must list only `_build_sources_and_figures`, `_generate_app_source`, `_glyph_layer_lines`, the four new functions and two constants, and test symbols of the 11 files.
- **Commit message** (`$S/09-message.txt`). Subject: `Draw TeX delimiters in graph text as typed on every canvas sink (WP-30 P1.11a)`. Body, in order: the contents of `$S/09-P1.11a-failure.txt`; the measured defect (Overview's TX numbers and E3's Chrome counts); what changed and where (TR-09.1-TR-09.7, both modes); the threat closed (TR-09.12); then one line each:
  - `Regression: test/test_canvas_tex.py::TestTheSavedPage::test_a_tex_title_ships_no_mathjax -- failed at <batch-3 base sha> with <text>` and likewise for every regression test of "TDD test stubs" (pytest node ids; the cscript as `test/test_wp30_truth.cscript TX-02` … `TX-05`);
  - the three `Flipped:` lines of `$S/09-flips.txt`, e.g. `Flipped: test/test_label_sinks.py::TestTextSinks::test_it_carries_the_raw_text -- the raw TeX pair on a canvas sink was wrong because twoway draws it as typed and BokehJS typeset it with MathJax`;
  - `BUGS.md: "<WP30_OPEN["P1.11a"] title>" (closed)`.
  No fixture line. No tool or vendor name anywhere (G7).
- **BUGS.md Resolution** (one line, in place):
  TeX snippets go in backticks (BUGS.md is Markdown); test node ids stay bare, as the tracking test reads them.

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.11a). A TeX delimiter pair (`$$`, `\(`, `\[`) in text dash draws on a graph -- titles, subtitles, notes, captions, axis titles, tick labels and the tick-label map, by() panel titles, legend keys and titles, and the colour bar's title and tick labels -- reached BokehJS raw and was typeset by MathJax, where twoway draws it as typed; the saved page shipped MathJax for it (3,087,832 bytes against 1,301,750 for the same page in plain words) and user text reached MathJax's TeX parser, whose html package makes `\href{javascript:...}` a live link. One pass, _dash_finish_graph_text, now applies _dash_inert_tex to every canvas text sink, last in each mode: at the end of DashRenderer._build_sources_and_figures and in the served make_document once the panels and shared scales are built, so the text is drawn as typed before and after a filter move and no saved page ships MathJax for it. Pinned by test/test_canvas_tex.py::TestTheSavedPage::test_a_tex_title_ships_no_mathjax, test/test_label_sinks.py::TestTeX::test_no_canvas_sink_holds_tex, test/test_canvas_tex.py::TestAfterAFilterMove::test_served_text_is_unchanged_by_a_move, test/test_canvas_tex.py::TestInChrome::test_bokehjs_draws_every_canvas_text_as_plain_text, test/test_wp30_truth.cscript TX-02. Residual, deferred (WP-30): the served page still loads Bokeh's MathJax bundle, though no dash text reaches it (P2.48); SMCL tags in graph text are P1.11b.
  ```
- **CHANGELOG lines** (each replaces one marker in place; `<n1>`/`<n0>` are the 09-03 driver run's `S09 sizes:` numbers):
  Code goes in backticks: CHANGELOG.md is Markdown, where a bare `\(` renders as `(`.
  - Security:

    ```
    - Text drawn on a graph no longer reaches a TeX engine. A `$$…$$`, `\(…\)` or `\[…\]` pair in a title, subtitle, note, caption, axis title, tick label, legend key, by() panel title or colour key was typeset by MathJax, whose html package makes `\href{javascript:…}` a live link and `\style{…}` a style attribute; every delimiter in that text is now broken by an invisible word joiner, in the saved page and the served app, before and after a filter move. (WP-30, P1.11a)
    ```
  - Results that change:

    ```
    - TeX in graph text is drawn as typed, as twoway draws it: `dash scatter mpg weight, title("\(y\)") subtitle("\[z\]") note("\$\$ x \$\$")` drew typeset maths and wrote a 3,087,832-byte page carrying MathJax; it now draws the text as typed and the page is <n1> bytes, against <n0> for the same page in plain words. (WP-30, P1.11a)
    ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md D3:** the TeX half is closed by this commit; D3 stays open until P1.11b (S29) lands, then `- **Tracked:** Closed in WP-30, BUGS.md "<P1.11a title>" and "<P1.11b title>", commits <S09 sha>, <S29 sha>`. Its Gap line's anchor `_dash_inert_tex (dash_render.py:17456)` is stale (24012 at `c96facd`).
  - **GAPS2.md J5:** closed by this commit: `- **Tracked:** Closed in WP-30, BUGS.md "<P1.11a title>", commit <S09 sha>`, and `(WP-30, GAPS2-J5)` appended to the Resolution.
  - **ROADMAP.md:3039 and :3063-3066** (WP-20's sink walk, TR-20.3): add that canvas text sinks (Title, Label, axis labels and tick overrides, the tick-label map, legends, the colour bar) now carry TeX pairs inert in both modes (WP-30 P1.11a, `_dash_finish_graph_text`), so the saved page no longer loads MathJax for user text.
  - **DROPIN-REMAINING.md:101 (P1.11):** "TeX half closed by <S09 sha> (P1.11a); the SMCL half is P1.11b."
  - **P2.48** (register): the served bundle still ships `bokeh-mathjax` (1.79 MB per session), now unused by dash text.
  - **Proposed new P2 row (not TeX; different root cause, so not folded):** twoway macro-expands a `$name` inside a variable or value label when it draws it (measured: value label `$$f$$` drawn `$$$`, `scratch tx3.do`, StataNow 19.5); dash draws the stored label as typed.
  - **AGENTS.md invariant:** "every canvas text sink is finished by `_dash_finish_graph_text`, last in each mode; a sink made after it is finished and marked by its maker".
