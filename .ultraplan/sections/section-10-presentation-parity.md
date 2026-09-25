# Section 10: Saved/served presentation parity (E14)

> Part of: WP-28 · Gaps: E14 · Risk: yellow · Batch: 1 · Depends on: none · Blocks: 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **1** · Depends on **none** · Blocks **19** · Risk **yellow** · Commits: one commit (E14) → CHANGELOG `Results that change` (bar move) and `Fixed in WP-28` (other four items): two markers

- D8: add a `type="checkpoint"` task at the end of the section (the bs filter-bar move is the one deliberate picture change).
- Add `_md_span` and `_cell_height_class` to the served copy list; every grid child must carry `db-bs-cell`.
- D7: split 10-01.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

dash is one product with two renderers: `DashRenderer` writes the saved offline page and
`ServerAppBuilder` writes a `bokeh serve` app, and dash.sthlp's mode table promises the same
layout and toolbar in both. GAPS2 E14 (audit of 25sep2026 at `91d97be`) measures five places
where the two pages still present the dashboard differently, and three of them are written
into the help as limitations: "The served page has no viewport meta"; "The served app dims
unselected points at Bokeh's 0.1, not dash's 0.15, because `_apply_nonselection_dimming`
runs only when saving"; "rspike and rconnected markers show a selection only when saved";
"Served `layout(bs)` does not reflow at 992 px and lacks the KPI cells' minimum heights";
"The saved `layout(bs)` page puts the filter bar above the title; test_mode_parity.py ALLOWED
exempts this". None of the five changes a number; each changes what a viewer sees, and the
fifth is a picture change to the saved page itself (DISCOVERY Q11: the saved bar moves below
the header, where the served app and every other layout already put it).

After this section the served page carries the saved page's viewport `<meta>`; a brush in
either mode dims the unselected points of a linked graph to `_NONSELECTION_ALPHA` (0.15);
a served `rspike` or `rconnected` in a link group draws the group's shared source through
an `IndexFilter` view, so a selection reaches it as it does on the saved page; the served
`layout(bs)` GridBox takes the saved page's half rows between 768 and 991 px and its KPI
cells' minimum heights (130/150/170 px, 120 below 768), through one stylesheet on the grid
and the saved page's own class names on its children; and the saved bs page's filter bar
sits below the title. The one difference research found beyond E14 -- under
`filterposition(left)` the saved bs page draws the header inside the content column
(`dash_render.py:22699-22711`) where the served app draws it above sidebar and content
(`:27242-27263`) -- is **recorded** in dash.sthlp and in this section's Notes, not fixed
(DISCOVERY amendments; PRD §7).

The five items share this section because they are the whole of one gap, they touch only
presentation code no other WP-28 section edits (the served template, the dimming helper,
the served range branch, the bs grid, the bs page assembly), and they are proven by the same
three instruments: the parity corpus (`test/test_mode_parity.py`), the served bs layout
tests (`test/test_served_bs_layout.py`) and the headless-Chrome layout runner
(`test/test_responsive_layout.py`, skipped without Chrome and red under `DASH_STRICT=1`).

**Test order (CLAUDE.md rule 7): task 10-01 writes every model-level regression test, runs
it against the unmodified tree and records the failure; task 10-02 writes the Chrome tests
the same way.** Tasks 10-03 to 10-07 turn them green one item at a time, flipping the tests
that pin today's behaviour in the same commit as each fix; 10-08 writes the help, the
CHANGELOG and the closed BUGS.md entry.

## Risk: [yellow] — five small edits, but item 4 relies on a Bokeh mechanism the library does not document, and item 5 changes a picture every saved bs page has shown

- **Why yellow.** Items 1, 2 and 5 are a constant, a function move and a reorder. Item 3
  changes which source a served range layer draws, which touches the served filter-move
  machinery (`_dash_refresh_linked`, `_dash_own_redrawn_views`). Item 4 needs per-child CSS
  on a Bokeh `GridBox`, which PRD §10 risk 2 flags: "if Bokeh cannot carry it, the item is
  recorded as a residual rather than faked".
- **Risk factors.** (a) The served copy lists: a helper the app calls that is not in the
  functions list is a `NameError` in every served session -- `_md_span` and
  `_cell_height_class` are not copied today. (b) A GridBox child's placement is written by
  BokehJS into the child's own shadow root; a rule that loses the cascade would change
  nothing and the model-level tests would still pass. (c) The parity corpus's bs reader
  reads the grid alone; relaxing its guard without an order-sensitive reader would let the
  bar sit anywhere.
- **Mitigation.** (a) The generated app's source is parsed for the two helpers
  (`TestTheBsGridStylesheet::test_the_helpers_it_calls_are_in_the_app`). (b) The mechanism
  was **measured in headless Chrome on Bokeh 3.9.0 before this section was written** (see
  Evidence, item 4): the stylesheet on the grid moves four span-3 cards to two per line at
  768 and 991 px and back to four at 1440; the Chrome test repeats that measurement on a real
  dashboard in both modes. (c) The bs reader becomes a page-ordered flat list compared with
  the served roots flattened the same way, so the bar's position is what is compared.

## Dependencies

- Depends on: none. Every function this section edits is disjoint from the other batch-1
  sections (S04 edits the format writer, S05 `map_histogram`, S07/S08 dash.ado's parsers
  and `_dash_cell_cap`, S09 the launcher).
- Blocks: section-19 (closeout lifts this section's CHANGELOG lines and GAPS2 Tracked line).
- Parallel batch: 1. Can run with every other batch-1 section; its `dash_render.py` regions
  (2169-2195, 2307-2314, 18606-18659, 19439-19466, 21855-21874, 22712-22731, the copy lists
  at 24381/24425-24428/24466-24687, 26012-26024, 26479) are edited by no other section.

## Evidence

All anchors at `91d97be`, from `.ultraplan/research/codebase-formats-filters-histogram-parity.md`
§4 and re-read for this section.

### Item 1 -- the served page has no viewport meta

`_dash_served_template`, `dash_render.py:2169-2195`, adds only the CSP to Bokeh's preamble:

```python
2189    from bokeh.core.templates import FILE
2190    return FILE.environment.from_string(
2191        "{% extends base %}\n"
2192        "{% block preamble %}{{ super() }}    "
2193        + _dash_csp_meta(_DASH_CSP_SERVED)
2194        + "\n{% endblock %}",
2195        globals={"base": FILE})
```

The saved page's `_CSP_META`, `:2307-2314`, carries the tag with the reason:

```python
2307 _CSP_META = (
2308     _dash_csp_meta(_DASH_CSP_STANDALONE)
2309     # Without this a mobile browser lays the page out at its 980px default
2310     # and zooms the whole thing out to fit, so every breakpoint below 980px
2311     # is unreachable on a phone and the text is unreadable.  Found by opening
2312     # a dashboard at 375px: window.innerWidth reported 980.
2313     + '\n<meta name="viewport" content="width=device-width, initial-scale=1">'
2314 )
```

The served app sets the template at `:25824` (`doc.template = _dash_served_template()`).
The template function's **source is copied into the app** (functions list `:24618`,
`"_dash_csp_meta", "_dash_served_template"`), and the app's source is checked for a raw
script tag (`test/test_csp.py:190-204`): the docstring at `:2179` says "No literal tag
names here". A `<meta` literal is not a script tag, and `_dash_csp_meta` already returns
one, so a module constant holding the viewport tag is safe -- and it must be in the
**constants** copy list (`:24381` names `_DASH_CSP_SERVED`) or the copied template raises
`NameError` in the app.

### Item 2 -- the served app dims at Bokeh's 0.1

`_NONSELECTION_ALPHA = 0.15` at `:1996`, a deliberate legibility constant. The dimming is a
**method**, `DashRenderer._apply_nonselection_dimming`, `:21855-21874`:

```python
21869        for renderer in fig.renderers:
21870            ns = getattr(renderer, "nonselection_glyph", None)
21871            if ns is None:
21872                continue
21873            if hasattr(ns, "fill_alpha"):
21874                ns.fill_alpha = _NONSELECTION_ALPHA
21875            if hasattr(ns, "line_alpha"):
21876                ns.line_alpha = _NONSELECTION_ALPHA
```

called at `:23309` (by() panels, `if name in link_names`) and `:23332` (plain graphs). A
method cannot be copied by the functions list, which copies module-level `def`s by
`inspect.getsource` (`:24466-24687`); `_NONSELECTION_ALPHA` is already in the constants
list (`:24340`) and unused in the app. In the served template `linked_names` is computed
at `:25888` (`_dash_link_names`), `_dash_figure_for(g, gname, g_df, _fac_label=None)` at
`:26109` builds one figure (a graph or one by() panel) and ends with `return fig` at
`:26479`; its callers are `:26506` and `:26528` (plain graphs) and `:26583` (panels), and
the panel loop adds each panel's name to `linked_names` before calling it (`:26566-26570`).
So one call at the end of `_dash_figure_for`, gated on `gname in linked_names`, covers
graphs and panels alike.

### Item 3 -- served rspike and rconnected draw a private source

`map_rspike`, `:10070-10105`, draws from the source it is given and honours `view=`:

```python
10096        _rseg_kwargs: dict = dict(x0=xvar, y0=y1var, x1=xvar, y1=y2var, source=source,
...
10100        if view is not None:
10101            _rseg_kwargs["view"] = view
10102        r = fig.segment(**_rseg_kwargs)
```

`map_rconnected`, `:10256-10298`, is `map_line` + `map_scatter` on `source`, twice, each with
`view=view` -- the line a sorted copy, the markers the source itself (as `connected` is).
The saved `_add_glyph` hands both the graph's shared source with the plot view. The served
range branch, `:26012-26024`, never does:

```python
26018            _ly_src, _ok = _dash_range_source(
26019                g_df, y1var, y2var, xvar, opts.get('mlabel', ''),
26020                extra_cols=_hv + _dash_option_columns(opts, df.columns))
26021            if _ok:
26022                _dash_add_glyph(
26023                    _DASH_MAPPER, fig, _ly_src, ptype, y1var, xvar,
26024                    opts, y2var=y2var, color_idx=_sidx)
```

`_dash_range_source`, `:19439-19466`, builds `ColumnDataSource(g_df[cols])` every time and
returns `(source, ok)`; it keeps NaN rows on purpose (its docstring: a missing end is the
mapper's to leave out). `_dash_layer_source`, `:19391-19436`, is the model to copy:

```python
19425    view = None
19426    if gname in linked_names and xvar and yvar:
19427        csrc = shared_source
19428        if len(clean) != len(df):
19429            pos = [shared_pos[_l] for _l in clean.index if _l in shared_pos]
19430            view = CDSView(filter=IndexFilter(pos))
```

Everything the linked form needs is already in the app: `shared_source` carries every
range variable (`all_vars` at `:25893-25907` reads `yvar1`, `yvar2`, `y1var`, `y2var`, the
option columns and `hover()`), `_shared_pos` is at `:25926`, `_dash_add_glyph`
(`:20874-20896`) forwards `view=` to the range mapper (`:20895`), and the filter-move
machinery is generic: `_dash_linked_views` (`:18024-18055`) lists **every** `IndexFilter`
view over the shared source in any figure's renderers, `_dash_refresh_linked`
(`:18058-18108`) recounts their positions after a move, and a source a mapper *built*
(rconnected's two sorted line copies) is registered for redraw at `:26355-26375` exactly as
`connected`'s line is today. The redraw closure `_redraw` (`:26090`) calls `_dash_draw_layer`
with an empty linked set, so the redraw path keeps building private sources and copying
their data onto the live copies -- unchanged.

### Item 4 -- the served bs grid has no half rows and no KPI cell heights

The saved page's CSS, `_DASH_GRID_CSS` `:2318-2402`, has three bands and the heights:

```
2349 @media(min-width:768px){
2350 .db-col-md-1{flex:0 0 8.3333%;max-width:8.3333%}
...
2363 @media(min-width:992px){
2364 .db-col-lg-1{flex:0 0 8.3333%;max-width:8.3333%}
...
2381 .db-cell-h-sm{min-height:130px}
2382 .db-cell-h-md{min-height:150px}
2383 .db-cell-h-lg{min-height:170px}
2384 @media(max-width:767px){
2385 .db-cell-h-sm,.db-cell-h-md,.db-cell-h-lg{min-height:120px}
2386 }
```

Each saved cell is classed at `:22653-22666`:

```python
22656                    f'<div class="db-col-12 db-col-sm-12 '
22657                    f'db-col-md-{_md_span(span)} db-col-lg-{span}'
...
22662                    f'{" db-cell-h-" + _cell_height_class(span) if _is_kpi else ""}">'
```

with `_md_span` (`:5246-5262`: a span of 4 or less becomes 6, otherwise itself) and
`_cell_height_class` (`:5265-5282`: `lg` at 12, `md` from 6, else `sm`). The KPI card's own
markup (`:13629-13640`) has `min-height:110px` and the cell's class adds the rest.

The served grid, `_dash_bs_grid` `:18606-18659`, is a `GridBox(cols=[_DASH_BS_TRACK]*12,
spacing=16, sizing_mode="stretch_width")` passed through `_dash_reflow` (`:17824-17876`),
whose GridBox branch appends one rule:

```python
17858        css = ("@media (max-width: %.2fpx) { :host { display: flex "
17859               "!important; flex-direction: column !important; } }" % below)
```

Nothing sets a child's md span or a card's cell height; served KPI Divs carry only
`_dash_kpi_stylesheets()` (`:25318`, `:26651`). The served template's bs call site is
`:27175-27180` (`_kpi_names` is computed there from `_dash_kpi_keys`). **`_md_span` and
`_cell_height_class` are not in the functions copy list** (`:24466-24687`; `_dash_bs_grid`,
`_dash_bs_grid_cells`, `_dash_reflow` are, at `:24651-24658`).

**How BokehJS places a GridBox child, read from the installed 3.9.0 bundle**
(`/opt/homebrew/lib/python3.14/site-packages/bokeh/server/static/js/bokeh.js`):

- `CSSGridBoxView._update_layout` (bokeh.js `:56318-56340`) writes each child's position
  as a `:host` rule into the child's own `parent_style` stylesheet -- not as an inline
  `style=` attribute:
  ```js
  56333                styles.grid_row_start = `${row + 1}`;
  56334                styles.grid_row_end = `span ${row_span}`;
  56335                styles.grid_column_start = `${col + 1}`;
  56336                styles.grid_column_end = `span ${col_span}`;
  56337                view.parent_style.append(":host", styles);
  ```
  `parent_style` is `new InlineStyleSheet("", "parent", true)` (`:11621`) installed in the
  child's shadow root (`computed_stylesheets`, `:11623`; `_apply_stylesheets` installs into
  `this.shadow_el`, `:13694-13697`). The grid's own template is written to its own `style`
  sheet (`:56408-56410`, `grid_template_rows/columns`).
- A model's `css_classes` are added to its host element (`_css_classes` yields
  `this.model.css_classes`, `:11635-11637`; `class_list.add`, `:13699-13702`), and that
  element is appended into the **parent's** shadow root, so a rule in the GridBox's own
  stylesheets can select it as `:host > .db-col-md-6`. `_dash_reflow`'s `:host > .bk-GridBox`
  rule (`:17869-17871`) already relies on exactly this.
- A model's `stylesheets` (`ui_element.py:97-110`) install into that model's own shadow
  root, "use `:host` to access the root DOM element".

So both mechanisms the requirement names exist. Which one wins the cascade against Bokeh's
placement rule: Bokeh's rule is a *normal* `:host` declaration in the child's shadow tree;
CSS Cascade Level 5 §6.2 ("Context") gives a normal declaration from the **outer**
encapsulation context precedence over one from the inner, before specificity is even
compared. The GridBox's shadow tree is outer to the child's, so a normal `:host > .cls`
rule on the grid beats the child's `parent_style` without `!important`. (`_dash_reflow`'s
`!important` is a different case: it overrides Bokeh's `display: grid` in the *same* shadow
root.) A child `stylesheets` rule would also work -- same context as `parent_style`, later
in `_stylesheets()` order (`:13684-13688`: static, computed, user), or with `!important`.

**Measured, 25sep2026, Bokeh 3.9.0, Google Chrome 153 headless, through the repo's own
iframe method** (`test/responsive_probe.py`): a `GridBox` of four span-3 `Div` cards
(`css_classes=["db-bs-cell", "db-col-md-6", "db-col-lg-3", "db-cell-h-sm"]`, the first
also `db-bs-first`), two span-6 figures (`db-col-md-6 db-col-lg-6`, the first
`db-bs-first`) and one span-12 figure (`db-col-md-12 db-col-lg-12 db-bs-first`), with
`_dash_reflow`'s stacking rule and **one** `InlineStyleSheet` on the grid holding the CSS
of TR-10.9:

| width | without the grid stylesheet | with it |
|---|---|---|
| 375 | cards stacked, cell 365 x 110; canvases 375 wide | cards stacked, cell 365 x **120**; canvases 375 |
| 768 | four cards across, 170 x 110; figures 375, 376 side by side, then 767 | cards **two per line** (366 x **130**, lines at y=5 and y=161); figures 375, 376 side by side below them, then 767 |
| 991 | four across, 226 x 110 | two per line, 477 x 130 |
| 1440 | four across, 338 x 110 | four across, 338 x 130 |

That is the saved page's md layout (four cards at `db-col-md-6` wrap two per line; the
span-6 figures stay side by side; the span-12 alone). A first run that classed only the
cards left the figures at their explicit rows and pushed cards 3-4 below them: **every
child must carry `db-bs-cell` (`grid-row: auto`)**, or explicit and automatic placement
mix.

### Item 5 -- the saved bs page puts the filter bar above the title

`_render_bootstrap_html`, `:22712-22731`:

```python
22714            # Horizontal filter bar above main content
22715            filter_bar_html = ""
...
22726            page_body_html = (
22727                f"{filter_bar_html}"
22728                f"{header_html}"
22729                f"{tabs_section_html}\n"
22730                f"{grid_section_html}\n"
22731            )
```

`header_html` is the joined `_dash_header_fragments` (`:18660-18676`: an `<h2 class="db-title"
…>` and a `<p class="db-subtitle" …>`, escaped once). The served app, `:27242-27263`, builds
`column(filter_bar, content)` and then `column(*_dash_header_models(...), layout)` -- header
above bar above content -- as the saved non-bs layout does. The `filterposition(left)`
branch (`:22699-22711`) draws the header inside the `db-col-md-10` content column beside the
sidebar; served, the header sits above `row(sidebar, content)` (`:27246-27253`). That is
the recorded difference.

The parity harness: `ALLOWED["layout(bs) is standalone markup"]`, `test/test_mode_parity.py:119-138`,
ends "…a layout(bs) entry sets no filter(), tabs(), title() or subtitle(): the saved page puts
its filters above the title (or, filterposition(left), beside it), and the served app -- as
the saved page under every other layout -- below it." `_render_pair` (`:845-897`) reads a bs
page's grid with `_bs_markup_tree` (`:808-843`, cells from `db-col-lg-N` and `data-root-id`,
placed as a browser at 992 px places them) and takes the widgets from `r.filter_widgets`.
`test_same_document_tree` (`:1489-1508`) refuses a bs entry that sets any of the four. The
served tree is `_layout_tree` (`:736-780`), which spells a `Column` as `("Column", [...])`,
a `Row` as `("Row", [("Widget", profile), ...])`, a header Div as `("Div", ("text", text))`.

### The tests that pin today's behaviour (flip, never delete)

| test | pins | flip to |
|---|---|---|
| `test/test_help_claims_4.py::TestTheLauncherServes::test_the_page_has_no_mobile_viewport` (`:1643`) | no viewport in the served page | `test_the_page_has_a_mobile_viewport`: exactly one, `_DASH_VIEWPORT_META`, after the CSP meta |
| `test/test_csp.py::TestTheServedTemplate::test_it_is_bokehs_page_plus_the_meta` (`:457-466`) | Bokeh's page plus the CSP meta only | strip both metas, then equal to Bokeh's page |
| `test/test_help_claims_4.py::TestTheModesDifferHere::test_a_brush_dims_unselected_points_less_when_served` (`:1671-1685`, `assert served == {0.1}`) | served dims at 0.1 | `test_a_brush_dims_unselected_points_alike_when_served`: `served == {0.15} == saved` |
| `test/test_help_claims_3.py::TestASelectionReachesTheLayersThatDrawTheGroupsRows::test_two_range_layers_draw_it_only_on_the_saved_page` (`:735-739`) | served rspike/rconnected draw their own | `test_two_range_layers_draw_it_in_both_modes`: `any(saved) and any(served)`, and for rconnected `sorted(saved) == sorted(served)` |
| `test/test_help_claims_5.py::TestAFacetedGraphInALinkGroup` docstring (`:840-850`, "rbar, rspike and rconnected's markers share it on the saved page only") | prose | "rspike and the markers of rconnected share it in both modes; rbar draws its own rows in both" |
| `test/test_mode_parity.py` `ALLOWED["layout(bs) is standalone markup"]` (`:119-138`) and `_Agree.test_same_document_tree` (`:1489-1508`) | bs entries carry nothing outside the grid | the key describes the page-ordered reading; the guard is removed |
| `test/test_responsive_layout.py::TestServedDocumentsFitInChrome` docstring (`:255-260`, "it declares no viewport; dash.sthlp says so") and the module docstring | prose | the served page is rendered through the served template and declares the viewport |
| `test/test_mode_parity.py` corpus entries `hover() on a linked graph` (`:1135`), `marker labels on a linked graph` (`:1138`), `colorvar() on a linked graph` (`:1147`), `two graphs, link()` (`:1261`), `link(_all)` (`:1263`), `a linked faceted graph` (`:1265`) | pass today only because the profile does not record dimming | once `_glyph_profile` records `dim`, these fail at `91d97be` (0.15 vs 0.1) and pass after 10-04 -- no edit to the entries |

Not pinned, so untouched: `test/test_help_claims_5.py::TestAFacetedGraphInALinkGroup::test_a_layer_with_a_source_of_its_own_does_not`
(bar, lfit, rcap, rscatter -- all still draw their own; `map_rcap` and `map_rscatter` build
`ColumnDataSource(self._carry_cols(...))`/`ColumnDataSource(_rs_cols)` copies in both modes),
`test/test_served_bs_layout.py::TestBsGrid::test_a_gridbox_of_twelve_equal_columns` (the
children tuples are unchanged; classes are extra), `test/test_layout.py:492-504` (`db-container`
count), `test/test_geometry.py:459-473` (the saved viewport, unchanged text),
`test/test_help_claims_3.py::test_the_linking_section` (`:930`: needs `{cmd:dot}` and
`{cmd:rbar}` in the linking paragraph -- keep both words when rewriting dash.sthlp).

### Help text this section rewrites

- dash.sthlp `:1010-1020` (linking): "…except that a saved dashboard shows it on {cmd:rspike}
  and the markers of {cmd:rconnected}, where a served one does not."
- `:955-959` (phone width): "The served app does the same in a browser window of the same
  width; on a phone, see {help dash##server_mode:Server mode}."
- `:1321` (mode table): `Bootstrap {cmd:layout(bs)} | reflows | stacks below 768`.
- `:1345-1351` ("What reflow means"): "The served one keeps the rows and spans it was given
  down to a 768-pixel window…".
- `:1484-1496` ("What the served app does not do"): the viewport and dimming bullets.

Code docstrings that say the old thing: `_dash_bs_grid` `:18615-18618`, `_dash_reflow`
`:17844-17846`, the served template comment `:27170-27172`,
`_apply_nonselection_dimming` `:21856-21862`.

### Fixtures on disk

None. E14 is presentation; no Stata truth is involved.

## User stories

- **US-10.1** As a dashboard viewer on a phone, I want the served app laid out for my
  screen, so that its grids stack as the saved page's do instead of showing a zoomed-out
  desktop page.
- **US-10.2** As a dashboard viewer, I want a brush to dim the unselected points of linked
  graphs the same way whether I opened the saved page or the served app, so that the
  selection reads the same in both.
- **US-10.3** As a dashboard viewer, I want a box or lasso selection to light up an
  `rspike` and the markers of an `rconnected` in a linked served graph, as it does on the
  saved page, so that a range layer takes part in linking in both modes.
- **US-10.4** As a dashboard viewer on a tablet, I want a served `layout(bs)` dashboard to
  take the same half rows and KPI cell heights the saved one takes between 768 and 991 px,
  so that the two pages are one dashboard.
- **US-10.5** As a Stata user, I want a saved `layout(bs)` page to put its filter bar below
  the title, where the served app and every other layout put it, so that the two pages
  agree and the title is the first thing on the page.
- **US-10.6** As the maintainer, I want the parity corpus to compare a bs page's title,
  filter bar, tabs and grid in page order, so that no exemption hides a layout difference.

## Business requirements

- **BR-10.1** The served page declares the viewport the saved page declares, once, after
  its Content-Security-Policy meta and before anything else in the head.
- **BR-10.2** A linked figure's renderers dim their unselected points to the same opacity
  (0.15) in the saved page and the served app; an unlinked figure keeps Bokeh's own.
- **BR-10.3** In a served link group, an `rspike` segment and `rconnected`'s markers draw
  the group's shared source (through a view when the graph or layer has a qualifier), so a
  selection on the group shows on them; their lines, and `rbar`, `rcap`, `rscatter`,
  `rcapsym`, `rarea`, `rline`, `tsrline` still draw from data of their own, in both modes.
- **BR-10.4** After a filter move, a served linked range layer shows the rows the saved
  page shows (its own rows among those the filters keep).
- **BR-10.5** A served `layout(bs)` grid between 768 and 991 px wide puts a cell of four
  columns or fewer at half the row and keeps wider cells at their span, each bs row starting
  a line; from 992 px it keeps the spans it was given; below 768 it stacks. A served KPI
  card's cell is at least 130/150/170 px tall for a span under 6 / from 6 / of 12, and 120 px
  below 768 -- the saved page's numbers.
- **BR-10.6** A saved `layout(bs)` page with `filterposition(top)` draws its title and
  subtitle, then the filter bar, then the tab strip, then the grid; `filterposition(left)`
  is unchanged and documented as the one remaining layout difference.
- **BR-10.7** The help's server-mode section no longer lists the viewport or the dimming as
  differences; the mode table says `layout(bs)` reflows in both modes; the linking
  paragraph says rspike and rconnected show a selection in both.
- **BR-10.8** Nothing a user writes reaches a class name, a stylesheet or a meta tag: every
  class and every CSS number is built from integers and fixed words.

## Technical requirements

- **TR-10.1** Add `_DASH_VIEWPORT_META = '<meta name="viewport" content="width=device-width, initial-scale=1">'`
  as a module constant beside `_CSP_META` (`:2307`); `_CSP_META` becomes
  `_dash_csp_meta(_DASH_CSP_STANDALONE) + "\n" + _DASH_VIEWPORT_META` (the comment at
  `:2309-2312` stays); `_dash_served_template`'s preamble becomes
  `_dash_csp_meta(_DASH_CSP_SERVED) + "\n    " + _DASH_VIEWPORT_META + "\n"` (CSP first, so
  `test_csp.py`'s `_assert_first` holds). Add `"_DASH_VIEWPORT_META"` to the constants copy
  list beside `"_DASH_CSP_SERVED"` (`:24381`).
- **TR-10.2** Add a module-level `_dash_dim_nonselection(fig, alpha=_NONSELECTION_ALPHA) -> None`
  immediately before `class DashRenderer` (it is the body of `:21869-21876`, `alpha` in place
  of the constant). Delete the method `DashRenderer._apply_nonselection_dimming`
  (`:21855-21876`) and call `_dash_dim_nonselection(fig)` at `:23309` and `:23332`. Add
  `"_dash_dim_nonselection"` to the functions copy list beside `"_dash_refresh_linked"`
  (`:24641`). In the served template, insert before `"        return fig"` (`:26479`):
  `"        if gname in linked_names:"` / `"            _dash_dim_nonselection(fig, _NONSELECTION_ALPHA)"`.
  `test/function_test_map.py`: remove `'DashRenderer._apply_nonselection_dimming'` (`:44`),
  add `'_dash_dim_nonselection': 'test/test_linking.py::TestLinkedBrushing::test_linked_renderers_have_nonselection_alpha'`.
- **TR-10.3** Extend `_dash_range_source` (`:19439-19466`) in place -- no new function, so no
  copy-list or map change -- to
  `_dash_range_source(g_df, y1var, y2var, xvar, label_var, extra_cols=(), *, df=None, gname="", linked_names=(), shared_source=None, shared_pos=None)`
  returning `(source, view, ok)`: when `gname in linked_names and shared_source is not None`
  and the three variables are columns of `g_df`, return `shared_source` with
  `view = CDSView(filter=IndexFilter([shared_pos[l] for l in g_df.index if l in shared_pos]))`
  if `df is not None and len(g_df) != len(df)` else `None`; otherwise the private
  `ColumnDataSource(g_df[cols])` as today with `view=None`; `(None, None, False)` when a
  variable is missing. No `dropna`: a missing end stays the mapper's, as the docstring says.
  Update the one caller (`:26018-26024`) to pass `df=df, gname=gname, linked_names=_ln,
  shared_source=_shared, shared_pos=_shared_pos` and `view=_ly_view` to `_dash_add_glyph`.
  `_dash_linked_views`, `_dash_refresh_linked`, `_dash_own_redrawn_views` and the redraw
  registration at `:26355-26375` need no edit (Evidence, item 3).
- **TR-10.4** Add module constants beside `_DASH_BS_STACK_BELOW_PX` (`:191`):
  `_DASH_BS_LG_FROM_PX = 992` (the saved page's lg breakpoint, `:2363`),
  `_DASH_KPI_CELL_MIN_PX = (("sm", 130), ("md", 150), ("lg", 170))` and
  `_DASH_KPI_CELL_MIN_NARROW_PX = 120` (`:2381-2386`). Add all three to the constants copy
  list at `:24425-24428`.
- **TR-10.5** Add `_dash_bs_cell_classes(span, is_kpi, first) -> list[str]` next to
  `_dash_bs_grid_cells`: `["db-bs-cell", f"db-col-md-{_md_span(span)}", f"db-col-lg-{span}"]`
  plus `f"db-cell-h-{_cell_height_class(span)}"` when `is_kpi`, plus `"db-bs-first"` when
  `first`; `span` is first clamped to 1-12 as `_dash_bs_grid_cells` clamps it.
- **TR-10.6** Add `_dash_bs_grid_css() -> str` returning, built from the constants only:
  `"@media (min-width: %dpx) and (max-width: %.2fpx) { :host > .db-bs-cell { grid-row: auto; } "`
  with `_DASH_BS_STACK_BELOW_PX` and `_DASH_BS_LG_FROM_PX - 0.02`, then for n in 1..12
  `":host > .db-col-md-%d { grid-column: auto / span %d; } "`, then
  `":host > .db-bs-first { grid-column-start: 1; } } "`, then for each `(k, px)` of
  `_DASH_KPI_CELL_MIN_PX` `":host > .db-cell-h-%s { min-height: %dpx; } "`, then
  `"@media (max-width: %.2fpx) { :host > .db-cell-h-sm, :host > .db-cell-h-md, :host > .db-cell-h-lg { min-height: %dpx; } }"`
  with `_DASH_BS_STACK_BELOW_PX - 0.02` and `_DASH_KPI_CELL_MIN_NARROW_PX`. No
  `!important` (Evidence, item 4). The text must match `re.fullmatch(r"[\w\s:{}().;>,\-!@/]+", css)`.
- **TR-10.7** `_dash_bs_grid(rows, cell_of, kpi_names=())`: after the children are placed,
  set `m.css_classes = list(m.css_classes) + _dash_bs_cell_classes(c_span, name in kpi_names, first)`
  on each placed model, where `first` is true for the first *placed* cell of each bs row
  (a name `_dash_bs_grid_cells` dropped or a repeat is not first; repeats cannot reach the
  renderer since P20-31 refuses them in dash.ado); then, after `_dash_reflow`, append
  `InlineStyleSheet(css=_dash_bs_grid_css())` to the grid's `stylesheets`. Existing classes
  and stylesheets on a model are kept (extend, never replace). Update the served call site
  `:27177-27180` to pass `kpi_names=_kpi_names`. Rewrite the docstrings at `:18615-18618`,
  `:17844-17846` and the comment at `:27170-27172`.
- **TR-10.8** Add `"_dash_bs_cell_classes", "_dash_bs_grid_css", "_md_span", "_cell_height_class"`
  to the functions copy list beside `"_dash_bs_grid"` (`:24652`). `test/function_test_map.py`
  gains `'_dash_bs_cell_classes'` and `'_dash_bs_grid_css'` naming the tests of TR-10.13.
- **TR-10.9** The stylesheet's exact rule set is the one measured (Evidence, item 4);
  do not add `!important` to the grid rules and do not put the rules on the children.
- **TR-10.10** `_render_bootstrap_html` `:22726-22731`: `header_html + filter_bar_html +
  tabs_section_html + grid_section_html`; the comment at `:22714` becomes "Horizontal filter
  bar below the header, above the content, as the served app and every other layout". The
  `filterposition(left)` branch `:22699-22711` is untouched.
- **TR-10.11** `test/test_mode_parity.py`: (a) `_glyph_profile` (`:322`) records
  `entry["dim"] = (ns.fill_alpha, ns.line_alpha)` (each `_num`-rounded, `None` where
  absent) from `r.nonselection_glyph` and `entry["on_link_source"] =
  bool(getattr(r.data_source, "_dash_link_source", False))` (both modes mark the group's
  source: `:23178`, `:25923`). (b) New reader `_bs_markup_page(r, page, figures, embedded)`
  returning the container body's parts **in page order**, each spelled as `_layout_tree`
  spells its served twin: `("Div", ("text", fragment))` for each `<h2 class="db-title"…>…</h2>`
  and `<p class="db-subtitle"…>…</p>` (regex, position = match start); `("Row", [("Widget",
  _widget_profile(embedded[id])), …])` for the `data-root-id`s inside
  `<div class="db-row db-filter-bar">…</div>`; `_layout_tree(embedded[id], figures)` for the
  `data-root-id` inside the tabs cell `<div class="db-col-md-12">`; and `_bs_markup_tree(...)`
  for the grid, positioned at the first `db-row db-section` chunk holding a `db-col-lg-`
  cell; the parts sorted by position. (c) `_unwrap_columns(tree)`: a `("Column", kids)` is
  replaced by its unwrapped kids, a list of roots by their concatenation, anything else kept.
  (d) `_render_pair`: for a bs page `std_tree = _bs_markup_page(...)` and
  `srv_tree = _unwrap_columns(srv_tree)`; also `pair["std"]["cells"]` = `[(lg_span,
  sorted(classes))]` from each grid cell's class attribute (`db-col-md-N`, `db-col-lg-N`,
  `db-cell-h-*` only) in page order and `pair["srv"]["cells"]` = the same from each GridBox
  child's `css_classes` and `c_span`, in children order. (e) `test_same_document_tree` loses
  the `outside` guard; its docstring and `ALLOWED["layout(bs) is standalone markup"]` say
  the page is read in page order and compared flat. (f) Corpus entries of TR-10.14.
- **TR-10.12** `test/responsive_probe.py`: `PROBE_JS` adds `cells`: for each `.db-kpi-card`,
  `[cellWidth, cellHeight, cellClass]` of the nearest ancestor -- crossing a shadow root via
  `getRootNode().host` -- whose class list has one starting with `db-cell-h-`, or
  `[-1, -1, ""]`. `test/test_responsive_layout.py`: `_served_page` renders with
  `file_html(doc, INLINE, "served", template=dr._dash_served_template())`; `FAMILIES` gains
  `"bs_cards": _spec(_FOUR, _K4, layout="bs")` and `SERVED` gains it; the tests of TR-10.13.
- **TR-10.13** Tests, by file (the stubs below): `test/test_served_bs_layout.py` gets one
  class per item; `test/test_mode_parity.py` the profile keys, the readers, the corpus
  entries and `TestRangeLayersInALinkGroup`, `TestTheBsCellsCarryOneSetOfClasses`,
  `TestThePagesHeads`; `test/test_responsive_layout.py` the Chrome classes.
- **TR-10.14** Parity corpus entries: `_case("rspike and rconnected in a link group",
  bo={"link": "g1 g2"}, graphs=[("g1", [plot_for("rspike"), plot_for("rconnected")]),
  ("g2", [_sc()])])` and `_case("layout(bs) with a title, filters and tabs", bo={"layout":
  "bs", "title": "Title", "subtitle": "Sub", "filter": "foreign, type(dropdown); price,
  type(range)", "tabs": "A: g2"}, graphs=[("g1", [_sc()]), ("g2", [plot_for("line")])],
  kpis=[_kpi("k1")])`.
- **TR-10.15** Docs: dash.sthlp `:1010-1020`, `:955-959`, `:1321`, `:1345-1351`,
  `:1484-1496` rewritten as task 10-08 spells them; CHANGELOG "Results that change" gains a
  group; BUGS.md gains the closed entry.

## Boundaries

- Do not touch `_FILTER_JS`, `_DASH_FILTER_MASK_JS` or any estimator (C4/E4 are out of
  scope, DISCOVERY Q3); the saved page's filter callback is section 17's.
- Do not change `_dash_layer_source`, `_dash_linked_views`, `_dash_refresh_linked`,
  `_dash_own_redrawn_views` or `_dash_redraw_for`: item 3 only hands the range branch the
  same source and view the ordinary branch already gets.
- Do not fix the `filterposition(left)` header placement (`:22699-22711` vs `:27246-27253`):
  recorded in dash.sthlp and the Notes (DISCOVERY amendments, PRD §7).
- Do not change `_DASH_GRID_CSS` (the saved page's CSS) or the saved cell classes: the
  served grid copies them; the tests pin that the numbers agree.
- Do not change `_dash_reflow`'s existing rules, the GridBox's children tuples, `cols`,
  `spacing` or `sizing_mode`: `test_served_bs_layout.py::TestBsGrid` and the parity spans
  depend on them.
- Do not rename the ALLOWED key `"layout(bs) is standalone markup"`: it is consulted by
  name and the guard on the list checks that.
- Do not edit GAPS2.md's Tracked line or ROADMAP.md (section 19 and section 01).
- No user text reaches a class, a stylesheet or a meta tag (rule 1); nothing new is
  `exec`ed; the served CSP is unchanged.

## Stata truth

None. No extract script, no probe, no fixture key. The one Stata-side claim this section
touches (that twoway draws no marker labels on rspike) is already measured and unchanged.

## TDD test stubs

The first two groups fail at `91d97be`; task 10-01 writes group A, task 10-02 group B.
Both modes wherever a page exists.

**A. Model level (no browser) -- task 10-01**

`test/test_served_bs_layout.py`:

- Test: the served template renders `_DASH_VIEWPORT_META` once, after the CSP meta, before
  `</head>`, and `_CSP_META` holds the same text --
  `test_served_bs_layout.py::TestTheServedPageDeclaresTheSavedPagesViewport::test_one_viewport_after_the_policy`
  (render `dr._dash_served_template()` with `test_csp._file_context()`). Pre-fix:
  `AttributeError: _DASH_VIEWPORT_META`.
- Test: the generated app's source assigns `_DASH_VIEWPORT_META` (ast walk, as
  `test_csp.py::TestTheServedApp::test_the_source_defines_the_policy_constants`) --
  `::TestTheServedPageDeclaresTheSavedPagesViewport::test_the_app_carries_the_constant`.
- Test: `_dash_dim_nonselection(fig)` sets `fill_alpha` and `line_alpha` of every renderer's
  nonselection glyph to 0.15, `alpha=0.3` to 0.3, leaves a renderer with no nonselection
  glyph alone, returns None -- `::TestALinkedFigureDimsAlike::test_the_helper` (rule 3, one
  unit test per function). Pre-fix: `AttributeError`.
- Test: a served bs dashboard with `link="g1 g2"`: every renderer of g1 and g2 has
  `nonselection_glyph.fill_alpha == line_alpha == dr._NONSELECTION_ALPHA`; an unlinked g3 in
  the same document keeps Bokeh's 0.1 -- `::TestALinkedFigureDimsAlike::test_the_served_document`.
  Pre-fix: 0.1 on g1 and g2.
- Test: `_dash_range_source` unlinked returns `(ColumnDataSource, None, True)` with the
  frame's rows NaN included; linked over the whole frame `(shared, None, True)`; linked over
  a qualified frame `(shared, view, True)` with `view.filter.indices` the qualified rows'
  positions in `shared_pos`; a missing variable `(None, None, False)` --
  `::TestALinkedRangeLayerDrawsTheGroupsSource::test_the_helper` (four cases). Pre-fix:
  `TypeError` on the keyword arguments.
- Test: served, `link="g1 g2"`, g1 = rspike + rconnected, g2 = scatter: g1's `Segment`
  renderer and both `Scatter` renderers have `data_source is` g2's scatter source, with no
  view when g1 has no qualifier, and an `IndexFilter` view of the qualified positions when
  g1 carries `if_expr="foreign==1"`; g1's two `Line` renderers draw copies --
  `::TestALinkedRangeLayerDrawsTheGroupsSource::test_the_served_document`. Pre-fix: the
  Segment draws a private source.
- Test: after one served filter move (the widget's callback through
  `test_adversarial_matrix._unthrottled`), the qualified g1's Segment view names the same
  row labels as before, counted against the moved source (`source.data["index"]`), and the
  rconnected line copies hold the moved rows -- `::TestALinkedRangeLayerDrawsTheGroupsSource::test_after_a_filter_move`
  (BR-10.4).
- Test: `_dash_bs_cell_classes(3, True, True) == ["db-bs-cell", "db-col-md-6", "db-col-lg-3", "db-cell-h-sm", "db-bs-first"]`,
  `(8, False, False) == ["db-bs-cell", "db-col-md-8", "db-col-lg-8"]`, `(12, True, False)`
  ends `db-cell-h-lg`, `(6, True, False)` `db-cell-h-md`, `(99, …)` clamps to 12, `(0, …)`
  to 1 -- `::TestTheBsGridStylesheet::test_the_class_helper`.
- Test: `_dash_bs_grid_css()` holds the md media query `(min-width: 768px) and (max-width: 991.98px)`,
  `:host > .db-bs-cell { grid-row: auto; }`, the twelve `:host > .db-col-md-N { grid-column: auto / span N; }`,
  `:host > .db-bs-first { grid-column-start: 1; }`, the three height rules and the 767.98
  narrow rule at 120, contains no `!important`, and matches
  `re.fullmatch(r"[\w\s:{}().;>,\-!@/]+", css)` -- `::TestTheBsGridStylesheet::test_the_css_helper`.
- Test: the numbers equal the saved page's: parse `_DASH_GRID_CSS` for
  `\.db-cell-h-(sm|md|lg)\{min-height:(\d+)px\}`, the `@media(max-width:767px)` block's
  `min-height:(\d+)px`, and `@media(min-width:(\d+)px)` before `.db-col-lg-1`, and assert
  they equal `_DASH_KPI_CELL_MIN_PX`, `_DASH_KPI_CELL_MIN_NARROW_PX`, `_DASH_BS_LG_FROM_PX`
  -- `::TestTheBsGridStylesheet::test_the_numbers_are_the_saved_pages` (the pattern of
  `TestTheServedGridIsTheSavedPagesGrid::test_the_gutter_is_the_saved_pages`).
- Test: `_dash_bs_grid([[("k1",3),("k2",3)],[("g1",8),("g2",6)]], cell_of, kpi_names={"k1","k2"})`
  classes each child as TR-10.7 says (g2 wraps to a new lg line but is not `db-bs-first`),
  keeps a Div's existing `css_classes` and `stylesheets`, and the grid's stylesheets end
  with one whose `css == _dash_bs_grid_css()` after `_dash_reflow`'s --
  `::TestTheBsGridStylesheet::test_the_grid_classes_its_children_and_carries_the_sheet`.
- Test: with a hostile name and spans 0 and 99, every class matches `^db-[a-z0-9-]+$` and
  the css is unchanged -- `::TestTheBsGridStylesheet::test_nothing_of_the_user_reaches_the_classes_or_css`.
- Test: the generated app's source defines `_md_span`, `_cell_height_class`,
  `_dash_bs_cell_classes`, `_dash_bs_grid_css` (ast) -- `::TestTheBsGridStylesheet::test_the_helpers_it_calls_are_in_the_app`.
  Pre-fix: none of the four.
- Test: served bs document (`_served`) vs saved page (`_saved`): for each grid child, the
  classes the saved cell of the same name carries (`db-col-md-N db-col-lg-N [db-cell-h-*]`,
  read as `_saved_rows` reads spans) are a subset of the child's `css_classes` --
  `::TestTheBsGridStylesheet::test_the_served_cells_carry_the_saved_cells_classes`.
- Test: saved bs page with title, subtitle, `filter`, `tabs`: in the container body,
  `class="db-title"` < `class="db-subtitle"` < `db-filter-bar` < `class="db-col-md-12">` <
  `db-col-lg-`; and the served document's root is `Column[Div, Div, Column[Row, Column[Tabs, GridBox]]]`
  -- `::TestTheSavedBsPagePutsItsFilterBarBelowTheHeader::test_top`. Pre-fix: the bar
  precedes the title.
- Test: the same page without tabs; without a subtitle; with no filters (no bar at all) --
  `::TestTheSavedBsPagePutsItsFilterBarBelowTheHeader::test_without_tabs`, `::test_without_a_subtitle`, `::test_no_filters_no_bar`.
- Test: `filterposition(left)` is the recorded difference: the saved bs page's
  `db-col-md-10` chunk contains `class="db-title"` and the served root's first child is
  the header Div above a `Row` -- `::TestTheSavedBsPagePutsItsFilterBarBelowTheHeader::test_filterposition_left_is_recorded_not_changed`
  (passes before and after; it pins the recorded state so a later change is deliberate).

`test/test_mode_parity.py`:

- Test: `_glyph_profile` carries `dim` and `on_link_source` -- covered by the corpus:
  `TestTheTwoModesAgree::test_same_figures` for the six linked entries fails at `91d97be`
  with `dim (0.15, 0.15)` vs `(0.1, 0.1)` (record the diff text in 10-01's commit message).
- Test: `TestRangeLayersInALinkGroup::test_rspike_and_rconnected_draw_the_groups_source_in_both_modes`:
  for the entry "rspike and rconnected in a link group", in both modes g1's Segment and
  Scatter renderers report `on_link_source` True and the Line renderers False. Pre-fix:
  served Segment and Scatters False.
- Test: `TestTheBsCellsCarryOneSetOfClasses::test_each_bs_entry` (parametrised over the
  corpus entries whose id starts with `layout(bs`): `pair["std"]["cells"] == pair["srv"]["cells"]`.
  Pre-fix: served classes empty.
- Test: `TestTheTwoModesAgree::test_same_document_tree` for "layout(bs) with a title,
  filters and tabs" -- with the guard removed and the page-ordered reader in place, fails at
  `91d97be` at `/[0]`: standalone `("Row", …)`, server `("Div", …)`; passes after 10-07.
- Test: `TestThePagesHeads::test_both_pages_declare_one_viewport`: the saved page (from
  `_standalone_page`) and the served page (`file_html(doc, INLINE, template=dr._dash_served_template())`)
  each contain `dr._DASH_VIEWPORT_META` exactly once, after a CSP meta. Pre-fix:
  `AttributeError`.
- Test: `TestTheAllowedList` (the existing guard that every key is consulted) still passes:
  the key text changes, not the key.

**B. Chrome (skipped without Chrome; red under `DASH_STRICT=1`) -- task 10-02**

`test/test_responsive_layout.py`:

- Test: `TestTheServedPageCarriesTheSavedPagesHead::test_viewport_and_policy`:
  `_served_page(FAMILIES["bs_cards"])` holds `_DASH_VIEWPORT_META` once, after the CSP meta
  (no Chrome needed; it proves the Chrome tests see the served template).
- Test: `TestTheServedBsGridReflowsAsTheSavedOne::test_cards_and_canvases_agree[bs_cards|bs_facet]`:
  measure the saved page and the served page at `WIDTHS`; at each width the same number of
  cards and canvases; sorted canvas widths elementwise within 24 px; every card cell width
  under 0.30 W at 1440, between 0.40 W and 0.60 W at 768, over 0.90 W at 375, in both modes;
  cell heights at least 130 at 768 and 1440 and at least 120 at 375, the served cell height
  within 2 px of the saved, and the cell class `db-cell-h-sm` in both. Pre-fix at 768: four
  served cards across at about 0.22 W and cell heights 110.
- Test: `TestTheProbe::test_cells_are_reported`: a page with a `.db-kpi-card` inside a
  `div.db-cell-h-md` 150 px tall reports `cells == [[w, 150, "db-cell-h-md"]]`.
- Test: `TestServedDocumentsFitInChrome::test_served_document_fits[bs_cards]` (the new
  family in `SERVED`) and `TestPagesFitInChrome::test_saved_page_fits[bs_cards]`.

**Mutation table -- proof the tests are not vacuous.** Apply, confirm the named test fails,
revert:

| break this | test that must die |
|---|---|
| leave `_DASH_VIEWPORT_META` out of the constants copy list | `TestTheServedPageDeclaresTheSavedPagesViewport::test_the_app_carries_the_constant`, and every served session (`NameError`) |
| call `_dash_dim_nonselection` in `_dash_figure_for` without the `linked_names` gate | `TestALinkedFigureDimsAlike::test_the_served_document` (g3 at 0.15) |
| in `_dash_range_source` return `shared_source` with `view=None` for a qualified frame | `TestALinkedRangeLayerDrawsTheGroupsSource::test_the_served_document` (view missing) and `test_after_a_filter_move` |
| drop `"db-bs-cell"` from `_dash_bs_cell_classes` | `TestTheBsGridStylesheet::test_the_class_helper`; in Chrome, `test_cards_and_canvases_agree` (figures keep their rows at 768, as measured) |
| leave `_md_span` out of the functions copy list | `TestTheBsGridStylesheet::test_the_helpers_it_calls_are_in_the_app`, and `_served` raises `NameError` |
| put the header after the bar again | `TestTheSavedBsPagePutsItsFilterBarBelowTheHeader::test_top`, `test_same_document_tree["layout(bs) with a title, filters and tabs"]` |
| in `_bs_markup_page` assemble by role instead of sorting by position | put the header after the bar: the parity entry must still fail |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| viewport meta in the served template and the app's constants | pytest, `test_served_bs_layout.py`, `test_mode_parity.py::TestThePagesHeads`, `test_csp.py` (flipped), `test_help_claims_4.py` (flipped, a launched server) | none | yes (saved unchanged, served added) |
| dimming at 0.15 | pytest, `test_served_bs_layout.py::TestALinkedFigureDimsAlike`, the parity profile's `dim` on six linked entries, `test_help_claims_4.py` (flipped), `test_linking.py` (unchanged, now on the module function) | none | yes |
| rspike/rconnected on the group's source, and after a move | pytest, `test_served_bs_layout.py::TestALinkedRangeLayerDrawsTheGroupsSource`, `test_mode_parity.py::TestRangeLayersInALinkGroup` + corpus entry, `test_help_claims_3.py` (flipped) | none | yes |
| served bs classes and stylesheet; numbers equal the saved CSS; helpers copied | pytest, `test_served_bs_layout.py::TestTheBsGridStylesheet`, `test_mode_parity.py::TestTheBsCellsCarryOneSetOfClasses` | none | yes |
| the half rows and cell heights as drawn | Chrome, `test_responsive_layout.py::TestTheServedBsGridReflowsAsTheSavedOne` at 375/768/1440 | none | yes |
| the saved bar below the header | pytest, `test_served_bs_layout.py::TestTheSavedBsPagePutsItsFilterBarBelowTheHeader`, `test_mode_parity.py` page-ordered tree + corpus entry | none | yes |
| nothing of the user in classes/CSS | pytest, `TestTheBsGridStylesheet::test_nothing_of_the_user_reaches_the_classes_or_css`, `test_responsive_layout.py::TestReflowAdversarial` (unchanged) | none | served |
| every function has a test | pytest, `test_function_test_map.py` | none | n/a |
| help, CHANGELOG, BUGS.md | pytest, `test_tracking_documents.py`, `test_help_claims_3.py::test_the_linking_section`; the cert suite's help-claims scripts unchanged | none | n/a |
| release gate | `scripts/run_release_gate.sh` (section 19) renders every example, six of them `layout(bs)` | none | both |

Acceptance criteria:

- **AC-10.1** `_dash_served_template().render(ctx)` and a launched app's `/` each contain
  `_DASH_VIEWPORT_META` exactly once, after the CSP meta; `test_csp.py` passes with both
  metas stripped equal to Bokeh's page.
- **AC-10.2** In a served session of a `link(g1 g2)` dashboard every renderer of g1 and g2
  has nonselection alphas 0.15 and an unlinked g3 has 0.1; the six linked parity entries
  compare equal on `dim`.
- **AC-10.3** Served, in a link group, rspike's Segment and rconnected's Scatters draw the
  group's source (a view when qualified); the Lines draw copies; after a filter move the
  view names the layer's own rows among the kept ones; `test_help_claims_3.py`'s flipped
  test passes for both types.
- **AC-10.4** Every served bs GridBox child carries the saved cell's classes; the grid
  carries `_dash_bs_grid_css()`; the constants equal `_DASH_GRID_CSS`'s numbers; in Chrome
  at 768 px the cards of `bs_cards` and `bs_facet` sit two per line with cells at least 130
  px tall in both modes, four per line at 1440, one per line at 375 with cells at least 120.
- **AC-10.5** A saved bs page reads title, subtitle, filter bar, tabs, grid in that order;
  the parity entry "layout(bs) with a title, filters and tabs" compares equal flat;
  `filterposition(left)` is unchanged and pinned.
- **AC-10.6** The full pytest suite is green with no new skips (Chrome present on the
  maintainer's machine; `DASH_STRICT=1` red otherwise), `test_function_test_map.py` green,
  BUGS.md carries the closed E14 entry naming the tests, dash.sthlp and CHANGELOG updated.

## Tasks

<task type="auto" id="10-01">
  <name>Write the failing model-level tests</name>
  <files>test/test_served_bs_layout.py, test/test_mode_parity.py</files>
  <action>
    Write only tests; do not touch dash_render.py. In
    `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_served_bs_layout.py` add
    the five classes of stub group A with exactly the names listed (reuse `_spec`, `_saved`,
    `_served`, `_served_grid`, `_saved_rows`, `_name`; import `_file_context` from
    `test_csp` and `_unthrottled` from `test_adversarial_matrix`; `_spec` needs a `link=`
    build option and `filter`/`title`/`subtitle`/`tabs`/`filter_position` pass through
    `**bo` already). For the range tests build g1 as
    `{"plots": [plot_for("rspike"), plot_for("rconnected")], ...}` with `plot_for` from
    `test_server_layer_defects`, and read renderers by `type(rr.glyph).__name__` in
    ("Segment", "Scatter", "Line"). In `test/test_mode_parity.py`: add `dim` and
    `on_link_source` to `_glyph_profile` (TR-10.11a); write `_bs_markup_page` and
    `_unwrap_columns` (TR-10.11b-c) and use them in `_render_pair` for bs pages, adding
    `pair["std"]["cells"]`/`pair["srv"]["cells"]` (TR-10.11d); remove the `outside` guard
    from `test_same_document_tree` and rewrite its docstring and the ALLOWED key's text so
    it describes the page-ordered flat reading and says the `filterposition(left)` bs page
    is not in the corpus (the recorded difference); add the two corpus entries of TR-10.14
    and the classes `TestRangeLayersInALinkGroup`, `TestTheBsCellsCarryOneSetOfClasses`,
    `TestThePagesHeads`. Run both files and paste the failure summary into the commit
    message: the six linked entries must fail on `dim`, the new bs entry at `/[0]` with
    `("Row", ...)` against `("Div", ...)`, the viewport and helper tests with
    `AttributeError`/`TypeError`.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_served_bs_layout.py test/test_mode_parity.py -q 2>&1 | tail -40` collects cleanly; every new test fails; `-k "same_figures and linked"` shows `dim` in the diff text; `-k "same_document_tree and title"` shows standalone `Row` against server `Div` at `/[0]`; every pre-existing test in both files still passes except those two groups.]]></verify>
  <done>Group A exists, collects, and fails for the reasons the stubs name; dash_render.py is unmodified; the parity harness reads a bs page in page order and records dimming and link-source identity.</done>
</task>

<task type="auto" id="10-02">
  <name>Write the failing Chrome layout tests</name>
  <files>test/responsive_probe.py, test/test_responsive_layout.py</files>
  <action>
    In `test/responsive_probe.py` extend `PROBE_JS`'s result with `cells` (TR-10.12):
    inside the existing `.db-kpi-card` branch climb `el.parentElement`, and at a shadow root
    `el.getRootNode().host`, until an element whose `classList` has a class starting with
    `db-cell-h-`; push `[round(cell.width), round(cell.height), thatClass]` or `[-1,-1,""]`;
    dedupe as `kk` is deduped; update the module docstring's field list. In
    `test/test_responsive_layout.py`: `_served_page` renders with
    `file_html(doc, INLINE, "served", template=dr._dash_served_template())`; add
    `"bs_cards"` to `FAMILIES` and `SERVED`; rewrite the module docstring's sentence and
    `TestServedDocumentsFitInChrome`'s docstring (the served page now declares the
    viewport, rendered through the served template); add
    `TestTheServedPageCarriesTheSavedPagesHead`, `TestTheServedBsGridReflowsAsTheSavedOne`
    (one `rp.measure_many` per mode per family, then the assertions of stub group B) and
    `TestTheProbe::test_cells_are_reported`. Every Chrome test calls `_chrome()` first so it
    skips without Chrome and is red under `DASH_STRICT=1` (conftest). Record the pre-fix
    measurement (four served cards across at 768, cells 110 tall) in the commit message.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_responsive_layout.py -q 2>&1 | tail -20`: `test_viewport_and_policy` fails with `AttributeError`; `test_cards_and_canvases_agree[bs_cards]` fails at 768 naming the served card widths; `test_cells_are_reported` passes; every pre-existing test passes (Chrome is at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`).]]></verify>
  <done>The Chrome runner renders the served page through the served template, reports KPI cells, and its new bs parity test fails at 91d97be for the measured reason.</done>
</task>

<task type="auto" id="10-03">
  <name>Give the served page the viewport meta</name>
  <files>dash_render.py, test/test_help_claims_4.py, test/test_csp.py</files>
  <action>
    TR-10.1: add `_DASH_VIEWPORT_META` above `_CSP_META` (`dash_render.py:2307`), use it in
    `_CSP_META` and in `_dash_served_template`'s preamble after the CSP meta (keep the
    `{{ super() }}` and the four-space indent; keep the docstring's "no literal tag names"
    sentence true -- the constant, not the function, holds the tag), and add
    `"_DASH_VIEWPORT_META"` to the constants copy list beside `"_DASH_CSP_SERVED"`
    (`:24381`). Flip `test/test_help_claims_4.py`'s `test_the_page_has_no_mobile_viewport`
    (`:1643`) to `test_the_page_has_a_mobile_viewport`: the launched page holds
    `dr._DASH_VIEWPORT_META` once, after `Content-Security-Policy`, and the control assertion
    on `_CSP_META` stays; rewrite its docstring. Flip
    `test/test_csp.py::TestTheServedTemplate::test_it_is_bokehs_page_plus_the_meta`
    (`:457-466`) to strip the CSP meta and then `_DASH_VIEWPORT_META` (each once, with the
    surrounding whitespace as the current regex does) before comparing with Bokeh's page,
    and rename it `test_it_is_bokehs_page_plus_the_two_metas`.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_csp.py test/test_help_claims_4.py -k "viewport or template or policy" -q 2>&1 | tail -5` passes; `python3 -m pytest test/test_served_bs_layout.py test/test_mode_parity.py test/test_responsive_layout.py -k "Viewport or PagesHeads or CarriesTheSavedPagesHead" -q 2>&1 | tail -3` passes.]]></verify>
  <done>Both pages declare one viewport meta after their CSP meta, from one constant the app also carries, and the tests that pinned its absence assert its presence.</done>
</task>

<task type="auto" id="10-04">
  <name>Dim linked served figures at dash's alpha</name>
  <files>dash_render.py, test/function_test_map.py, test/test_help_claims_4.py</files>
  <action>
    TR-10.2: add `_dash_dim_nonselection(fig, alpha=_NONSELECTION_ALPHA)` immediately before
    `class DashRenderer` with the body of `:21869-21876` and a docstring that carries the
    method's reason (`:21856-21862`) and says it is copied into the app; delete the method
    `_apply_nonselection_dimming`; call the function at `:23309` and `:23332`; add
    `"_dash_dim_nonselection"` to the functions copy list beside `"_dash_refresh_linked"`
    (`:24641`); in the template insert the gated call before `"        return fig"`
    (`:26479`), citing that `linked_names` holds panel names too (`:26566-26570`). In
    `test/function_test_map.py` replace the `DashRenderer._apply_nonselection_dimming` entry
    with `'_dash_dim_nonselection': 'test/test_linking.py::TestLinkedBrushing::test_linked_renderers_have_nonselection_alpha'`.
    Flip `test/test_help_claims_4.py::TestTheModesDifferHere::test_a_brush_dims_unselected_points_less_when_served`
    to `test_a_brush_dims_unselected_points_alike_when_served` asserting
    `saved == served == {0.15}`, and rewrite the class docstring ("What the help's
    server-mode section says of the two pages, each measured").
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_served_bs_layout.py test/test_mode_parity.py test/test_help_claims_4.py test/test_help_claims_5.py test/test_linking.py test/test_function_test_map.py -k "Dims or dims or linked or same_figures or function" -q 2>&1 | tail -5` passes, the six linked parity entries included; `grep -c "_apply_nonselection_dimming" dash_render.py test/function_test_map.py` prints 0 for both.]]></verify>
  <done>One module-level dimming function serves both renderers and is copied into the app; a linked served figure dims at 0.15 and an unlinked one at Bokeh's 0.1.</done>
</task>

<task type="auto" id="10-05">
  <name>Draw served rspike and rconnected from the group's source</name>
  <files>dash_render.py, test/test_help_claims_3.py, test/test_help_claims_5.py</files>
  <action>
    TR-10.3: extend `_dash_range_source` (`dash_render.py:19439-19466`) with the keyword-only
    linked arguments and the `(source, view, ok)` return, keeping the private
    `ColumnDataSource(g_df[cols])` path and the no-`dropna` rule; rewrite its docstring to say
    it is `_dash_layer_source`'s rule for the range types and why a private source never
    saw a selection. Update the served range branch (`:26018-26024`) to pass `df=df,
    gname=gname, linked_names=_ln, shared_source=_shared, shared_pos=_shared_pos` and to
    call `_dash_add_glyph(..., y2var=y2var, view=_ly_view, color_idx=_sidx)`. Add a comment
    there that the redraw closure (`:26090`) still passes an empty linked set on purpose.
    Flip `test/test_help_claims_3.py::TestASelectionReachesTheLayersThatDrawTheGroupsRows::test_two_range_layers_draw_it_only_on_the_saved_page`
    to `test_two_range_layers_draw_it_in_both_modes` (`any(saved) and any(served)`; for
    rconnected `sorted(saved) == sorted(served)`). Rewrite the docstring of
    `test/test_help_claims_5.py::TestAFacetedGraphInALinkGroup` (`:840-850`): rspike and the
    markers of rconnected share the group's source in both modes; rbar draws its own rows.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_served_bs_layout.py test/test_mode_parity.py test/test_help_claims_3.py test/test_help_claims_5.py test/test_served_linked_views.py test/test_served_filter_move.py test/test_server_layer_defects.py -k "Range or range or rspike or rconnected or LinkGroup or move" -q 2>&1 | tail -5` passes; `python3 -m pytest test/test_scheme_review_fixes.py -q -k MarkColour 2>&1 | tail -2` passes (the map's test for `_dash_range_source`).]]></verify>
  <done>A served rspike or rconnected in a link group draws the shared source, through an IndexFilter view when qualified, follows a selection and a filter move as the saved page does, and every other range type still draws its own rows.</done>
</task>

<task type="auto" id="10-06">
  <name>Give the served bs grid the saved page's md rows and cell heights</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    TR-10.4 to TR-10.9: add the three constants beside `_DASH_BS_STACK_BELOW_PX` (`:191`)
    with comments citing the saved CSS lines; add `_dash_bs_cell_classes` and
    `_dash_bs_grid_css` next to `_dash_bs_grid_cells`, the latter's docstring recording the
    Bokeh mechanism in three sentences (BokehJS writes a child's place as a `:host` rule in
    the child's shadow root through `parent_style`; the child's host element sits in the
    grid's shadow root where `css_classes` land; a normal rule from the outer context wins,
    so no `!important`) and the measurement date; give `_dash_bs_grid` its `kpi_names=()`
    parameter, class every placed child and append the sheet after `_dash_reflow`; update
    the served call site (`:27177-27180`) to pass `kpi_names=_kpi_names`; add the four names
    of TR-10.8 to the functions copy list and the three constants to the constants list;
    rewrite the docstrings at `:18615-18618`, `:17844-17846` and the comment at
    `:27170-27172`. In `test/function_test_map.py` add
    `'_dash_bs_cell_classes': 'test/test_served_bs_layout.py::TestTheBsGridStylesheet::test_the_class_helper'`
    and `'_dash_bs_grid_css': 'test/test_served_bs_layout.py::TestTheBsGridStylesheet::test_the_css_helper'`.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_served_bs_layout.py test/test_mode_parity.py test/test_function_test_map.py -k "Stylesheet or Cells or bs or function" -q 2>&1 | tail -5` passes; `python3 -m pytest test/test_responsive_layout.py -q 2>&1 | tail -3` passes including `test_cards_and_canvases_agree[bs_cards]` and `[bs_facet]` at 375, 768 and 1440.]]></verify>
  <done>The served layout(bs) GridBox carries one stylesheet built from the saved page's numbers and its children the saved cells' classes; measured in Chrome, both pages put span-3 cards two per line at 768 px with 130 px cells, four per line at 1440, and one per line with 120 px cells at 375.</done>
</task>

<task type="auto" id="10-07">
  <name>Move the saved bs filter bar below the header</name>
  <files>dash_render.py</files>
  <action>
    TR-10.10: in `_render_bootstrap_html` (`dash_render.py:22712-22731`) assemble
    `page_body_html` as header, filter bar, tabs section, grid; rewrite the comment at
    `:22714`. Leave the `filterposition(left)` branch (`:22699-22711`) exactly as it is and
    add a two-line comment above it naming the recorded difference (the served app draws
    the header above sidebar and content, `:27246-27253`; dash.sthlp records it). Nothing
    else changes: the widgets, their ids and the grid markup are as before, so the JS filter
    callback and `test_scheme_review_fixes.py::TestBootstrapPageWithWidgets` are untouched.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_served_bs_layout.py test/test_mode_parity.py test/test_scheme_review_fixes.py test/test_layout.py test/test_geometry.py -k "FilterBar or same_document_tree or Bootstrap or bs" -q 2>&1 | tail -5` passes, `test_same_document_tree["layout(bs) with a title, filters and tabs"]` included.]]></verify>
  <done>A saved layout(bs) page draws its title, then its filter bar, then its tabs and grid, as the served app and every other layout do; filterposition(left) is unchanged and pinned as recorded.</done>
</task>

<task type="auto" id="10-08">
  <name>Document E14 and close its BUGS.md entry</name>
  <files>dash.sthlp, CHANGELOG.md, BUGS.md</files>
  <action>
    dash.sthlp: (1) `:1010-1020` -- linked graphs highlight a selection "in its {cmd:scatter},
    {cmd:connected} and {cmd:dot} layers, and on {cmd:rspike} and the markers of
    {cmd:rconnected}, which draw the group's rows in both modes"; the other layers list
    loses "and the range and paired-coordinate plots" in favour of "the other range and
    paired-coordinate plots", the "except that a saved dashboard…" clause goes, and the
    {cmd:rbar} sentence stays ("shows it in neither mode"). (2) `:957-959` -- "The served app
    does the same, on a phone as in a narrow window: both pages declare a viewport." (3)
    `:1321` -- `{col 5}Bootstrap {cmd:layout(bs)}{col 38}reflows{col 59}reflows`. (4)
    `:1345-1351` -- "A {cmd:layout(bs)} grid rearranges itself as the browser window narrows,
    in both modes: a cell of four columns or fewer takes half the row below 992 pixels,
    every cell takes the whole row below 768, and a KPI card's cell keeps a minimum height
    keyed to its span (130 pixels under six columns, 150 from six, 170 at twelve; 120 below
    768).  Every other grid stacks the same way in both modes when it is too narrow for its
    columns." (5) `:1484-1496` -- replace the block with "{ul:What still differs.}  The two
    pages are laid out alike: both declare a viewport for phones, both dim the unselected
    points of linked graphs to 15% when a brush is drawn, and a {cmd:layout(bs)} grid takes
    the same half rows and KPI cell heights in both.  One difference remains, recorded and
    not changed: under {cmd:layout(bs)} with {cmd:filterposition(left)}, the saved page draws
    the title and subtitle inside the content column beside the filter sidebar, where the
    served app draws them above the sidebar and the content together." CHANGELOG.md, under
    "### Results that change", a new group `**The two pages (WP-28, E14)**` with two bullets:
    the saved `layout(bs)` page's filter bar now sits below the title and subtitle, where
    the served app and every other layout put it (a picture change, no numbers); and the
    served app now declares the viewport, dims unselected linked points to 15% (was Bokeh's
    10%), shows a selection on rspike and rconnected's markers, and takes the saved
    `layout(bs)` half rows and KPI cell heights between 768 and 991 px -- `filterposition(left)`
    under `layout(bs)` still places the title differently, recorded in the help. BUGS.md:
    append the closed entry `- [x] Title: The saved page and the served app present the
    dashboard differently (GAPS2 E14)` with File Names and Line Numbers naming
    `_dash_served_template`, `_dash_dim_nonselection` (was `_apply_nonselection_dimming`),
    `_dash_range_source`, `_dash_bs_grid`, `_dash_bs_grid_css`, `_render_bootstrap_html`;
    Description quoting GAPS2 E14's five items; Suggested fix GAPS2's plan; Resolution
    "Fixed 2026 (WP-28)…" naming the mechanism for item 4 (one stylesheet on the GridBox,
    the saved classes on its children, measured in Chrome) and every test:
    `test/test_served_bs_layout.py::TestTheServedPageDeclaresTheSavedPagesViewport`,
    `::TestALinkedFigureDimsAlike`, `::TestALinkedRangeLayerDrawsTheGroupsSource`,
    `::TestTheBsGridStylesheet`, `::TestTheSavedBsPagePutsItsFilterBarBelowTheHeader`,
    `test/test_mode_parity.py::TestRangeLayersInALinkGroup`, `::TestTheBsCellsCarryOneSetOfClasses`,
    `::TestThePagesHeads`, `test/test_responsive_layout.py::TestTheServedBsGridReflowsAsTheSavedOne`,
    and the flipped `test/test_help_claims_4.py::TestTheModesDifferHere::test_a_brush_dims_unselected_points_alike_when_served`
    and `test/test_help_claims_3.py::TestASelectionReachesTheLayersThatDrawTheGroupsRows::test_two_range_layers_draw_it_in_both_modes`;
    state the `filterposition(left)` residual. No AI references anywhere. Then pull local
    main, run the full suite once (`python3 -m pytest test/ -q`) and the changed cscripts
    (none), fix anything red, commit on `s3-bugs`, and report the merge command without
    running it.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_tracking_documents.py test/test_help_claims_3.py test/test_help_claims_4.py -q 2>&1 | tail -3` passes; `python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no new skips; `grep -n "rspike" dash.sthlp | head -3` shows the both-modes wording and `grep -c "does not do" dash.sthlp` prints 0; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.]]></verify>
  <done>dash.sthlp, CHANGELOG.md and BUGS.md record E14 closed with its tests and its one recorded residual, and the full suite is green on the committed tree.</done>
</task>

## Section completion criteria

- Every stub of groups A and B exists under its listed name, failed at `91d97be` for the
  reason recorded in 10-01's and 10-02's commit messages, and passes at the section's head.
- Every test in the flip table is flipped, none deleted; `test_function_test_map.py` is
  green with `_dash_dim_nonselection`, `_dash_bs_cell_classes` and `_dash_bs_grid_css`
  mapped and `DashRenderer._apply_nonselection_dimming` gone.
- The generated app's source defines `_DASH_VIEWPORT_META`, `_DASH_BS_LG_FROM_PX`,
  `_DASH_KPI_CELL_MIN_PX`, `_DASH_KPI_CELL_MIN_NARROW_PX`, `_dash_dim_nonselection`,
  `_dash_bs_cell_classes`, `_dash_bs_grid_css`, `_md_span`, `_cell_height_class`.
- AC-10.1 to AC-10.6 hold; the Chrome measurements of AC-10.4 are recorded in 10-06's
  commit message.
- BUGS.md has the closed E14 entry; dash.sthlp no longer lists the viewport or the dimming
  as served limitations; CHANGELOG lists the bar move and the served changes under
  "Results that change"; the `filterposition(left)` difference is in all three.
- `python3 -m pytest test/ -q` green under both interpreters when section 19 runs it; the
  working tree holds nothing of this section uncommitted.

## Notes

- **Copy lists are the trap.** Four helpers the served app will now call are not copied
  today: `_md_span`, `_cell_height_class` (used by `_dash_bs_cell_classes`) and the two new
  bs helpers; one constant, `_DASH_VIEWPORT_META`, is referenced by the copied template
  function. A missing name is a `NameError` in every served session and in
  `test_served_bs_layout.py::_served`, not at build. `TestTheBsGridStylesheet::test_the_helpers_it_calls_are_in_the_app`
  and `TestTheServedPageDeclaresTheSavedPagesViewport::test_the_app_carries_the_constant`
  parse the app's source for them.
- **`db-bs-cell` on every child.** The measured first run classed only the cards and Chrome
  kept the figures at their explicit rows and pushed cards 3-4 below the wide figure. Under
  the md query every child must have `grid-row: auto`, or explicit and automatic placement
  mix.
- **No `!important` on the grid rules.** The child's placement is a normal `:host` rule in
  an inner shadow tree; the grid's normal rule wins on context. Adding `!important` would
  still work but would hide a regression in which the rule moved to the wrong context.
- **The GridBox stylesheet order.** `_dash_reflow` appends the 767.98 px stacking rule; the
  bs sheet is appended after it. Both apply at 375: the stacked flex column takes the
  narrow min-height.
- **`_dash_range_source` keeps NaN rows.** Do not add `dropna` when writing the linked
  view: a missing end is drawn as nothing by the mapper, and the view's positions must be
  `g_df.index`, not a cleaned subset, or `_dash_linked_views` records the wrong members.
- **The redraw path is unlinked on purpose.** `_dash_redraw_for`'s closure calls
  `_dash_draw_layer` with `set()` for linked names so the throwaway figure builds private
  sources; rconnected's two sorted line copies are matched by position with the live copies
  (`agg_sources[...]['sources']`), exactly as `connected` is today. Do not "fix" that.
- **The parity reader must be order-sensitive.** `_bs_markup_page` sorts by position in the
  page; assembling by role would pass with the bar anywhere. The mutation table has the
  check.
- **Renderer order.** The saved renderer dims in `_build_sources_and_figures` after each
  figure is built (`:23309`, `:23332`); the served app at the end of `_dash_figure_for`.
  Both run after every glyph is added, so both reach every renderer.
- **Two full-suite launches per session.** `.claude/hooks/guard-full-suite.sh` refuses a
  third `python3 -m pytest test/ -q` in one session unless prefixed `FULL_SUITE_RERUN=1`;
  run only the changed files between tasks and the full suite once before each commit.
- **Chrome.** `test/responsive_probe.py` finds `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
  (153.0.8010.54 measured); without it the Chrome tests skip and a `DASH_STRICT=1` run is
  red -- a skip is not a pass.
- **Commits.** One commit per task on `s3-bugs`; the E14 BUGS.md entry lands closed in
  10-08's commit (DISCOVERY Q4 amended). No AI references in messages, entries or help.
  Section 19 adds the GAPS2 Tracked line and the WP-28 traceability row; ROADMAP.md:3352's
  WP-21 "recorded for later" note is left as history.
- **Recorded, not fixed (PRD §7, DISCOVERY amendments):** under `layout(bs)` with
  `filterposition(left)` the saved page draws the header inside the content column
  (`dash_render.py:22699-22711`) and the served app above sidebar and content
  (`:27246-27253`). dash.sthlp's server-mode section says so; the bs corpus entry does not
  use `filterposition(left)`; `test_filterposition_left_is_recorded_not_changed` pins the
  state.
- **Inconsistencies found while writing.** GAPS2 E14 names the Chrome widths as 375/900/1440;
  the runner's `WIDTHS` are 375/768/1440 and this section uses the runner's. GAPS2 item 4
  says the reflow happens "at 992 px"; the saved CSS's half-row band is 768-991 px (md) and
  full spans from 992 (lg), which is what is copied. GAPS2's plan step 3 says "draw rspike
  and rconnected markers from row-identity copies"; the saved page in fact draws them from
  the shared source itself, and so does this section.
