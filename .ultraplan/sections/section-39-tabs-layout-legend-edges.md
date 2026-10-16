# Section 39: tabs(), layout() and legend edges

> Part of: WP-31 · GAPS3 rows: D14, D16 · Risk: green · Batch: 13 · Depends on: 31 · Blocks: -- · Tasks: 3, 2 commits · Case-id prefix: U39

## Overview

**What is wrong today.** GAPS3 D14 (GAPS3.md:164): "`tabs()` drops unregistered names silently (layout() now names them); served `layout(s1:1,1 s2:1,1)` overwrites the cell silently; no per-tab `layout()`." Evidence dash_render.py:36001 (`safe = [x for x in items if x in valid]` in `_dash_parse_tabs`) and :50709-50712 (the served grid's `_slots[_r][_c] = _dash_cell(_nm)` for every placement, the second name overwriting the first). GAPS3 D16 (:166): "`legend(po(9) top)` names `top` first; `title("T", prefix suffix)` prints no "option prefix ignored" line; values nested in `legend(region())`/`legend(title())` unchecked." Evidence dash.ado:2860-2884 (`_dash_check_legend`, run from `_dash_validate_opts` at :4010 and from `_dash_plot` at :7088, before `_dash_subopt_check legend` at :6979) and dash_parse.mata:8206-8219 (`_dash_subreq_*`, twoway's sub-option refusals). Register rows P2.1 (narrowed: "only the served same-cell collision and `tabs()` stay silent") and P2.59.

Measured at `6370ca4` (read from the code; re-measured by 39-01):
- `_dash_parse_tabs(tabs_str, all_names, limit)` (:35974) keeps `safe = [x for x in items if x in valid]` and drops a tab left empty; nothing is printed and dash.ado has no tabs() name check (`grep -n "tabs" dash.ado` shows the option declared at :4046 and written at :10479, no registry check). dash.sthlp:1576-1577 documents the silence: "Names that are not in the registry are ignored without a message".
- Mata `_dash_layout_refusal` (:1618-1679) refuses an unknown name and a name placed twice, and `_dash_layout_scan` (:1483) reads `name:row,col` pairs; no rule refuses two names in one cell. The saved grid (`_dash_placement_map`, :39769; the DashRenderer grid at :44732-44800) and the served grid (:50706-50720) each fill `_slots[_r][_c]` in order, the later name overwriting; the renderer's `_dash_layout_check` (:3550) reports a repeated *name*, not a repeated *cell*.
- A tab segment is `title: name name` (:35994-36000); `layout(` inside a segment is read as a name and dropped as unregistered.
- `_dash_check_legend` (:2860-2884) scans the legend text for `top bottom left right` and exits 198 with "option top not allowed" before the Mata sub-option check (:6979) reads `po(9)`; twoway's parser reads left to right, so on `legend(po(9) top)` it refuses `po()` first (measured in 39-01).
- `_dash_subreq_check("title:<name>")` refuses sub-options but prints no line for `prefix` beside `suffix`; twoway prints an "ignored" line (text measured in 39-01). Nested `region()`/`title()` arguments are not resolved: `legend(region(lcolor(bogus)))` and `legend(title("T", size(bogus)))` reach the renderer.
- `_DASH_LEGEND_LABEL_RE = re.compile(r"\s*\+?(\d{1,6})(\s.*)", re.S)` (:37102) needs text after the number; `legend(label(1))` fails `fullmatch` (:28325) and key 1 keeps its text, where twoway blanks it (research/stata-ground-truth.md §7).

**After this section**: dash.ado refuses a `tabs()` name not in the registry with the sentence form of layout()'s refusal (D-39.a); a `layout()` placing two names in one cell is refused in Mata, and the renderer's `_dash_layout_check` reports the same collision for a spec that did not come through dash.ado (both grids then draw the same thing); a tab segment may end with `, layout(<rows cols> | <name:row,col ...>)` over that tab's names (D-39.b), checked in Mata and drawn by both grids. `legend(po(9) top)` is refused with twoway's first line; `title("T", prefix suffix)` prints twoway's ignored line; values nested in `legend(region())` and `legend(title())` are checked as twoway checks them (measured); `legend(label(1))` blanks key 1 in both modes.

**Test order and commit rule (rule 7, M6).** Two rows, two commits in the order D14, D16: `(WP-31 D14)`, `(WP-31 D16)`. 39-01 writes the extractor, fixture, `test/test_tabs_layout_edges.py` (D14) and `test/test_legend_edges.py` (D16) and the U39 cases, runs them red and saves `<scratch>/39-01-failure.txt`; 39-02 fixes D14 and commits it with its test file; 39-03 fixes D16 and commits it with its test file. Each commit stages only its row's files, so no commit is red.

### Section decisions (this file; binding on the executor)

- **D-39.a tabs() names are refused like layout() names (confirmed: DECISIONS D5, r(198)).** dash has no twoway rule here (tabs() is dash's own option), so the refusal is dash's existing sentence form: Mata `_dash_tabs_refusal(tabs, registry)` returns `""` or `tabs() name 'x' not found in registry.`, dash.ado's build path refuses with the same rc `_dash_layout_refusal`'s caller uses (the executor reads the caller: `grep -n "_dash_layout_refusal" dash.ado`). The renderer's `_dash_parse_tabs` keeps dropping unknown names for a spec that did not come through dash.ado but warns once (`_dash_warn_once(("tabs", "unknown"), "dash: tabs(): <names> are not registered graphs or KPI cards, so they are not placed.")`), as `_dash_layout_check` does for layout(). A CHANGELOG "Changed behaviour" line names the refusal (M5 applies to newly refused forms).
- **D-39.b Per-tab layout grammar.** `tabs(Title: a b c, layout(2 2) / Detail: d e, layout(d:1,1 e:1,2))`: the text after a segment's first top-level comma is that tab's options; the only option is `layout()` in the grid or placement form (no `bs`, no `auto`); its names must be among the segment's names and each placed once, each cell used once. Refused in Mata (`_dash_tabs_refusal`) with `tabs(): layout() <the same sentence _dash_layout_refusal gives>`. The renderer's `_dash_parse_tabs` returns `[(title, names, layout_or_None)]` and both grids build a tab's panel through the same `_dash_tab_grid(names, layout)` helper (saved: `_dash_tab_panels`; served: the template's tab builder). A tab without `, layout()` keeps today's auto grid.
- **D-39.c Same-cell collision is a refusal.** `_dash_layout_refusal` gains, after the twice-placed check, `layout() places '<a>' and '<b>' in the same cell <r>,<c>.`; `_dash_layout_check` reports `<a> and <b> are placed in the same cell <r>,<c>, so <b> is not placed` for a spec outside dash.ado. The first name keeps the cell in both grids (today's saved behaviour; the served grid is changed to match).
- **D-39.d Legend refusals in twoway's order.** `_dash_check_legend` stops scanning for the four keywords on its own; instead `_dash_validate_opts` calls Mata `_dash_subreq_check("legend")` on the recorded legend copies *before* the keyword scan, so the first token twoway refuses is named first; the keyword message (dash's own advice for `top` etc.) is kept for the case where the keyword comes first. The measured line for `legend(po(9) top)` (fixture `legend.po9_top`) decides whether twoway's text is "option po() not allowed" (then dash's existing table gives it) or something else (then that text is used verbatim).
- **D-39.e `prefix suffix` prints twoway's line.** `_dash_subreq_check("title:<name>")` prints, through `_dash_say("text", ...)`, the fixture's `title.prefix_suffix` line when both words are present in one copy, and draws what twoway draws (the fixture's SVG decides which word wins: expected `suffix`, "prefix ignored").
- **D-39.f Nested values are checked as twoway checks them.** `_dash_subreq_add` records `region()`'s argument under kind `legend_region` (resolved with the area table `_DASH_BY_GRAMMAR`'s stage-3 region reader, i.e. `_dash_region_spec`'s names) and `title()`'s argument under `legend_title` (the title table `_DASH_TITLE_SUBOPT_TABLE`); `_dash_subreq_check("legend")` resolves them after the legend's own tokens. The fixture's `nested.*` rows give the rc and line per probe; dash copies rc and line for each refused probe and stays silent for each accepted one.
- **D-39.g `label(#)` blanks the key.** `_DASH_LEGEND_LABEL_RE = re.compile(r"\s*\+?(\d{1,6})(\s.*)?", re.S)` and `texts[n] = _textbox_lines(lm.group(2) or "")`, giving `[""]`; the served copy is the same text (both the regex and `_dash_apply_legend` travel by name). Mata's legend check already accepts `label(1)` (an integer).

## Risk: [green] -- refusals and two small readers; no drawing changes except a blank key and a per-tab grid

**Why.** The edits are to parsers and checks; the drawing change is confined to `legend(label(#))`, the served grid's collision order and the per-tab layout.

**Risk factors.**
1. Making `tabs()` unknown names a refusal changes do-files that relied on the silence (M5 names it in CHANGELOG).
2. The per-tab layout grammar is new text in tabs(); the first top-level comma must not split a title (titles cannot hold a colon or a slash today; a comma in a title now ends it -- documented).
3. Pinned tests: test_layout_tabs.py `TestTabsAreNotSilentlyConditional`, test_layout_placement.py, test_legend_order.py `TestLabelByNumber`, test_axis_options.py `TestLegendRule`, test_json_escaping.cscript JSE-47 (legend(top) order), test_help_claims_* nodes reading dash.sthlp:1576-1577 and :870.
4. Batch partners: S38 edits `_dash_reference_lines`; S40 the symbol/pattern translators. No shared function.

**Mitigation.**
1. The Changed-behaviour line and the help sentence; the refusal names the names.
2. `TestPerTabLayout::test_comma_in_title_is_the_options_split` pins the rule; the help says so.
3. Flips in place with the reason (R9).
4. None needed.

## Dependencies

- **Depends on: 31** (batch 10, legend geometry): S31 edited `_dash_apply_legend` and the legend tables; S39 reads its tree for `_DASH_LEGEND_SUBOPTS`, `_dash_legend_parts` and the Mata legend tables.
- **Blocks:** none. S56 (help) reads S39's Tabs and legend sentences.
- **Parallel batch: 13**, merge order 38, 39, 40. **Can run with S38 and S40:** disjoint functions (Dependencies of S38 list them).

## Evidence

All anchors at `6370ca4`; re-read before editing.

### tabs()

```python
35974 def _dash_parse_tabs(tabs_str, all_names, limit=None):
35990     valid = set(all_names)
35994         if ":" in segment:
35995             raw_title, _, items_str = segment.partition(":")
35996             title = raw_title.strip()
35997             items = [x.strip() for x in items_str.split() if x.strip()]
36001         safe = [x for x in items if x in valid]
36002         if safe:
36003             result.append((title, safe))
```

`_dash_tab_panels(tabs_spec, cell_of)` (:36015) builds the saved tabs; the served template builds its own from the same parse (`grep -n "_dash_parse_tabs" dash_render.py` lists the template line). dash.ado declares `tabs(string asis)` in `dash build`'s syntax (:4046 `tabs=50,500` is the limit entry) and writes it to the JSON at :10478-10479; no registry check.

### layout()

Mata `_dash_layout_refusal` (:1618-1679): the `bs` branch, then

```
1670    for (i = 1; i <= cols(nms); i++) {
1671        if (!anyof(reg, nms[i])) return("layout() name '" + nms[i] + "' not found in registry.")
1672        // Placed twice, it kept its last place without a word.
1673        if (i > 1) {
1674            if (anyof(nms[|1 \ i - 1|], nms[i])) {
1675                return("layout() places '" + nms[i] + "' more than once.")
```

`_dash_layout_scan(layout, names)` (:1483) hands back the names only; the cells are not compared. Renderer `_dash_layout_check` (:3550-3611): a repeated name keeps its first place; unknown names reported; no cell check. Served grid (:50706-50720):

```python
50709            '            for _nm, (_r, _c) in placement.items():',
50710            '                if 0 <= _r < rows_n and 0 <= _c < cols_n:',
50711            '                    _slots[_r][_c] = _dash_cell(_nm)',
```

The saved grid (:44732-44800) fills `_slots` the same way from `self._placement_map(layout_opt)`; both overwrite, so the "saved keeps the first" claim of the register is for the *name* rule, not the cell -- 39-01 measures both grids.

### legend edges

dash.ado `_dash_check_legend` (:2860-2884): the `gettoken` loop and `display as error "option `kw' not allowed"` with dash's advice line, `exit 198`. Called at :4010 (`_dash_check_legend `"`macval(_leg)'"'`, `_leg` = `s(g_legend)`) inside `_dash_validate_opts` and at :7088 (`_dash_check_legend `"`macval(g_legend)'"'`, the after-comma legend) inside `_dash_plot`; `_dash_subopt_check legend` runs at :6979 in `_dash_plot`. dash_parse.mata :8206-8219: `_dash_subreq_clear/add/check/accept` -- "refuses the first problem with twoway's words through _dash_say, r(198)". `_dash_subopt_resolve` (:37009) returns `(names, (c, i, 198, "option po() not allowed"))` for an unknown token.

```python
37102 _DASH_LEGEND_LABEL_RE = re.compile(r"\s*\+?(\d{1,6})(\s.*)", re.S)
28325                lm = _DASH_LEGEND_LABEL_RE.fullmatch(_arg)
28326                if lm and int(lm.group(1)) in texts:
28327                    texts[int(lm.group(1))] = _textbox_lines(lm.group(2))
```

### Stata rules (research/stata-ground-truth.md §7)

- `_fr_legend_parse_and_log.ado` :20-24 `POSition RING STYle ORDER SHOWINDEX NOSPAN SPAN`; contents :197-216; "remaining options go to the textbox-style parser (:220-221)"; `label(# "text")` needs an integer (:350-359). Stata's `syntax` refuses the first option it cannot parse, left to right.
- `_fr_title_parse_and_log.ado` :17-18 `NOSPAN SPAN PREFIX SUFFIX POSition RING STYle`; the prefix/suffix conflict line is measured (fixture `title.prefix_suffix`).
- `legend_options.sthlp`: `region(areastyle_options)`, `title(tinfo)`; a bad colour inside them is a twoway note or refusal (measured).

### Fixtures on disk

`test/fixtures/subopt_abbrev_truth.json` (legend/axis abbreviations), `legend_*` truth files test_legend_order.py reads. S39 adds `tabs_legend_edges_truth.json`.

### Tests that pin today's behaviour (flip in place, never delete)

- test/test_layout_tabs.py::TestTabsAreNotSilentlyConditional -- nodes asserting an unknown tab name is dropped silently (saved and served).
- test/test_layout_placement.py::TestPlacementIsHonoured -- nodes asserting `s1:1,1 s2:1,1` draws s2 (served) or s1 (saved).
- test/test_legend_order.py::TestLabelByNumber -- a node asserting `label(1)` leaves the key's text.
- test/test_axis_options.py::TestLegendRule -- nodes asserting `legend(po(9) top)` names `top`.
- test/test_json_escaping.cscript JSE-47 and test/test_option_validation.cscript cases asserting the `top` line for a mixed legend; test_help_claims_* nodes reading dash.sthlp:1576-1577 ("ignored without a message") and :870.

The exact red list is measured by 39-01 into `<scratch>/39-flips.txt`.

## User stories

- **US-39.1** As a dashboard author who misspelt a graph name in `tabs()`, I want dash to refuse and name it, as `layout()` does, so that a tab is never silently incomplete.
- **US-39.2** As a dashboard author placing two graphs in one cell by mistake, I want the collision refused rather than one graph vanishing in the served app.
- **US-39.3** As a dashboard author, I want `tabs(Overview: k1 s1, layout(1 2) / Detail: s2 s3)` to lay out each tab as I ask.
- **US-39.4** As a Stata user, I want `legend(po(9) top)`, `title("T", prefix suffix)`, `legend(region(lcolor(bogus)))` and `legend(label(1))` to behave as under twoway: the same first error, the same ignored line, the same checks, a blank key.

## Business requirements

- **BR-39.1** A `tabs()` name not in the registry is refused by `dash build` with a sentence naming it; the renderer warns for a spec that bypassed dash.ado.
- **BR-39.2** A `layout()` placing two names in one cell is refused; both grids draw the first name when a bypassing spec collides.
- **BR-39.3** A tab's `, layout()` draws that tab in the named grid or placement, saved and served; a malformed one is refused.
- **BR-39.4** `legend(po(9) top)` produces twoway's first line; `title("T", prefix suffix)` prints twoway's ignored line and draws twoway's choice; each nested probe in the fixture is refused or accepted as twoway does; `legend(label(1))` blanks key 1 in both modes.

## Technical requirements

- **TR-39.1** Mata `_dash_tabs_refusal(string scalar tabs, string scalar registry)` after `_dash_layout_refusal` (:1679): splits on `/`, each segment on its first `:` (title) and first top-level comma (options), checks every name against *registry* (D-39.a) and the options against the per-tab grammar (D-39.b), reusing `_dash_layout_scan` for the placement form; header index entry; `_needed` entry (dash.ado:448-479, alphabetical); dash.ado's `dash build` path calls it where `_dash_layout_refusal` is called (same rc, `_dash_say("err", ...)`); `test/program_coverage_map.py` entry naming `test_option_validation.cscript:U39-01`.
- **TR-39.2** `_dash_layout_refusal` gains the same-cell check after :1676 (D-39.c): `_dash_layout_scan` (:1483, already walks `name:row,col`) is extended with an optional third argument, a `cells` string rowvector it fills with one `r,c` string per name in name order (callers passing two arguments are unchanged); no third function (`_dash_layout_cells(layout)` already exists at :1569 returning the cell COUNT and is not touched -- REVIEW-3d F6); two equal cells -> the sentence.
- **TR-39.3** `_dash_layout_check` (:3550) reports the collision (D-39.c) in its `problems` list, keeping the first name; the served grid's placement fill skips a cell already taken: ONE guard line `if _slots[_r][_c] is None:` wrapping the assignment at :50711 only (the `_taken`/`_free` bookkeeping at :50712-50718 and the auto-fill assignment at :50719 are unchanged -- REVIEW-3d F10), matching the saved grid.
- **TR-39.4** `_dash_parse_tabs` (:35974) returns three-tuples `(title, names, layout)`; `layout` from the segment's `, layout(...)` text through `_dash_grid_dims` (:3460) or `_dash_placement_map` (:39769) restricted to the tab's names; a bypassing spec's bad layout is dropped with a `_dash_warn_once`. `_dash_tab_grid(names, layout, cell_of)` new module function after `_dash_tab_panels` (:36015) builds the tab's grid rows; `_dash_tab_panels` and the template's tab builder call it. Copy list: `"_dash_tab_grid",` after `"_dash_parse_tabs",` in the functions tuple (grep the entry; add `_dash_parse_tabs` beside it if absent). The template edit is the tab-builder lines only (S39 is batch 13's `_generate_app_source` editor; S38's and S40's Boundaries say they do not edit it). `test/function_test_map.py` entries for `_dash_tab_grid` and the new Mata function.
- **TR-39.5** dash.ado calls `_dash_check_legend` at two sites: :4010 in `_dash_validate_opts` (`_leg`, which is `s(g_legend)`) and :7088 in `_dash_plot` (`g_legend`, the after-comma legend, WP-23) -- REVIEW-3d F7. 39-01 measures which site fires first for `legend(po(9) top)`; at that site (and the other, if it can be reached first for another form), record the legend copies with `_dash_subreq_add` and run `_dash_subopt_check legend` (the existing program at :2794) before `_dash_check_legend`, so twoway's first refusal comes first (D-39.d); the later call at :6979 stays (idempotent: the record is cleared after a check). `_dash_check_legend` is unchanged.
- **TR-39.6** Mata `_dash_subreq_check`: the `title:` kinds print the fixture's `title.prefix_suffix` line when both `prefix` and `suffix` are present in one copy (D-39.e) through `_dash_say("text", ...)`; the renderer's title reader (`_dash_textbox`, the `prefix`/`suffix` branch at :6353) draws the fixture's winner. New kinds `legend_region` and `legend_title` recorded by `_dash_subreq_add` from the `region()`/`title()` arguments and checked after the legend tokens (D-39.f); refused probes copy rc and line.
- **TR-39.7** `_DASH_LEGEND_LABEL_RE` (:37102) and :28327 per D-39.g. The regex's second user is :28354 (`lastlabel`, unchanged: `lastlabel(1)` now matches with `group(2)` None and the code reads `group(1)` only); `TestLabelBlank::test_regex` covers both forms (REVIEW-3d F9).
- **TR-39.8** Help (R3): Tabs :1551-1584 -- :1576-1577 rewritten ("A name not in the registry is refused, as layout() refuses it"), the per-tab `, layout()` form added after :1558 with one example, and the comma rule; Layout :1473-1550 -- one sentence on the same-cell refusal; Differences from twoway :866-890 -- `title("T", prefix suffix)` prints twoway's line and draws its choice; `legend(label(1))` blanks the key; Dashboard Options :1277 synopt unchanged. TWOWAY_COVERAGE_AUDIT.md :158 ("Unknown item names are silently ignored") rewritten; :136 gains `prefix/suffix conflict line`.
- **TR-39.9** Parity (R8): `CORPUS` entries `"tabs per-tab layout"`, `"legend label(1) blank"`; no move entry.

### Code and verbatim texts (copy, do not paraphrase)

**Mata `_dash_tabs_refusal(tabs, registry)`** (after `_dash_layout_refusal`):

```
// _dash_tabs_refusal(tabs, registry): "" when every name of every tab is
// registered and every per-tab layout() reads whole over that tab's names
// (WP-31 D14, D-39.a, D-39.b); otherwise the refusal, without the command.
string scalar _dash_tabs_refusal(string scalar tabs, string scalar registry)
{
    string rowvector segs, reg, nms, opts, toks
    string scalar    seg, body, lay, names, r
    real scalar      i, j, c
    reg  = tokens(registry)
    segs = tokens(subinstr(tabs, "/", char(1)), char(1))
    for (i = 1; i <= cols(segs); i++) {
        seg = strtrim(segs[i])
        if (seg == "") continue
        c = strpos(seg, ":")
        body = (c ? substr(seg, c + 1, .) : seg)
        // the first top-level comma ends the names (quote-aware):
        opts = _dash_rep_toks(body, 1)   // the existing top-level splitter
        body = opts[1]
        nms  = tokens(body)
        for (j = 1; j <= cols(nms); j++) {
            if (!anyof(reg, nms[j])) return("tabs() name '" + nms[j] + "' not found in registry.")
        }
        if (cols(opts) > 1) {
            toks = _dash_rep_toks(opts[2], 0)
            for (j = 1; j <= cols(toks); j++) {
                if (_dash_rep_optname(toks[j]) != "layout") return("tabs(): option " + _dash_rep_optname(toks[j]) + "() not allowed")
                lay = _dash_rep_value(toks[j])
                if (strlower(substr(strtrim(lay), 1, 2)) == "bs") return("tabs(): layout() must be 'N M' grid or 'name:row,col' placement inside a tab.")
                r = _dash_layout_refusal(lay, body)
                if (r != "") return("tabs(): " + r)
            }
        }
    }
    return("")
}
```

`_dash_rep_toks(text, mode)` and `_dash_rep_optname(tok)` exist (dash_parse.mata :4376, :4531); the executor confirms their exact semantics (mode 1 = split on top-level commas) and substitutes the real helpers if the split lives elsewhere; `_dash_rep_value(tok)` (:5794) is the value reader the `_dash_rep_*` family uses (REVIEW-3d F5: `_dash_subopt_arg_mata` does not exist). Passing *body* as the registry to `_dash_layout_refusal` restricts the names to the tab's own.

**The same-cell check** (in `_dash_layout_refusal`, after :1676), with `cells` the `r,c` strings `_dash_layout_scan` hands back in name order:

```
        if (i > 1) {
            for (j = 1; j < i; j++) {
                if (cells[j] == cells[i]) {
                    return("layout() places '" + nms[j] + "' and '" + nms[i] + "' in the same cell " + cells[i] + ".")
                }
            }
        }
```

**`_dash_tab_grid(names, layout, cell_of)`:**

```python
def _dash_tab_grid(names, layout, cell_of):
    """One tab's grid rows (WP-31 D14, D-39.b): the names in a `rows cols'
    grid or `name:row,col' placement when *layout* names one, else the
    auto grid both modes draw today.  *cell_of* maps a name to its cell."""
    names = list(names)
    if layout:
        dims = _dash_grid_dims(layout)
        if dims:
            rows_n, cols_n = dims
        else:
            placement = _dash_placement_map(layout, set(names))
            rows_n = max((r for r, _ in placement.values()), default=0) + 1
            cols_n = max((c for _, c in placement.values()), default=0) + 1
        slots = [[None] * cols_n for _ in range(rows_n)]
        placed = set()
        if not dims:
            for nm, (r, c) in placement.items():
                if 0 <= r < rows_n and 0 <= c < cols_n and slots[r][c] is None:
                    slots[r][c] = cell_of(nm)
                    placed.add(nm)
        free = [(r, c) for r in range(rows_n) for c in range(cols_n)
                if slots[r][c] is None]
        for nm in [n for n in names if n not in placed]:
            if not free:
                break
            r, c = free.pop(0)
            slots[r][c] = cell_of(nm)
        return slots
    cols_n = _dash_auto_grid_cols(len(names), None)
    cells = [cell_of(n) for n in names]
    while len(cells) % max(1, cols_n):
        cells.append(None)
    return [cells[i:i + cols_n] for i in range(0, len(cells), cols_n)]
```

(`_dash_auto_grid_cols(n, figures=None)` is the module function at :35496, already on the copy list (:47141); :50700 is the served grid's emitted call `_dash_auto_grid_cols(len(grid_names), figures)`; the executor passes the figures where the saved path has them.)

**Help sentences.** Tabs (:1576-1577 replaced; the new form after :1558): `A name that is not in the registry is refused, as {cmd:layout()} refuses one, and the message names it.  A tab may end with {cmd:, layout()} in the grid form ({cmd:layout(1 2)}) or the placement form ({cmd:layout(g1:1,1 g2:1,2)}) over that tab's names; the first comma of a tab ends its names, so a tab title cannot hold a comma, a colon or a slash.` Example: `{cmd:. dash build, saving(d.html) tabs(Overview: k1 s1, layout(1 2) / Detail: s2 s3) replace}`. Layout: `Two names placed in the same cell are refused, and the message names both.` Differences from twoway (:870 region): `{cmd:title("T", prefix suffix)} prints {cmd:twoway}'s line, <the fixture's text>, and draws what {cmd:twoway} draws; {cmd:legend(label(1))} with no text blanks key 1, as in {cmd:twoway}; the words inside {cmd:legend(region())} and {cmd:legend(title())} are checked as {cmd:twoway} checks them.`

**BUGS.md Resolutions.** D14: `  - Resolution: Fixed <ddmonyyyy> (WP-31, D14). _dash_tabs_refusal refuses a tabs() name not in the registry and a malformed per-tab layout(); _dash_layout_refusal refuses two names in one cell; _dash_parse_tabs warns for a spec that bypassed dash.ado and returns each tab's layout; _dash_tab_grid draws a tab's grid or placement in both renderers; _dash_layout_check reports a same-cell collision and the served grid keeps the first name as the saved page does. Pinned by test/test_tabs_layout_edges.py::TestPerTabLayout::test_grid, test/test_tabs_layout_edges.py::TestSameCell::test_served_first, test/test_wp31_truth.cscript U39-02, test/test_option_validation.cscript U39-01; fixture test/fixtures/tabs_legend_edges_truth.json. Closes GAPS3 D14 (WP-31, D14).` D16: `  - Resolution: Fixed <ddmonyyyy> (WP-31, D16). _dash_validate_opts runs the legend sub-option check before the keyword scan, so legend(po(9) top) is refused with twoway's first line; _dash_subreq_check prints twoway's line for title(, prefix suffix) and checks the words inside legend(region()) and legend(title()) as twoway does; _DASH_LEGEND_LABEL_RE accepts label(#) with no text and _dash_apply_legend blanks the key, in both renderers. Pinned by test/test_legend_edges.py::TestLabelBlank::test_blank, test/test_option_validation.cscript U39-03, test/test_option_validation.cscript U39-05, test/test_wp31_truth.cscript U39-06; fixture test/fixtures/tabs_legend_edges_truth.json. Closes GAPS3 D16 (WP-31, D16).`

**CHANGELOG lines.** D14 Changed behaviour: `- tabs() with a name that is not registered, and layout() placing two names in one cell, are refused and the message names them; the name was dropped from the tab, and the second graph took the cell in the served app, without a word. (WP-31, D14)` D14 Results: `- A tab takes its own layout(): tabs(Overview: k1 s1, layout(1 2) / Detail: s2 s3) draws the first tab as one row of two. (WP-31, D14)` D16 Changed behaviour: `- legend(po(9) top) named top; it is now refused with twoway's first line, <the fixture's text>; the words inside legend(region()) and legend(title()) are checked as twoway checks them (<the fixture's refused probes>). (WP-31, D16)` D16 Results: `- legend(label(1)) with no text kept the key's label, now blank as in twoway; title("T", prefix suffix) prints twoway's line, <the fixture's text>, and draws <the fixture's winner>. (WP-31, D16)`

### Both-mode call sites (grep first; anchors drift)

| Change | Saved renderer | Served app | Finder |
|---|---|---|---|
| tabs parse and grid | `_dash_parse_tabs` -> `_dash_tab_panels(tabs_spec, cell_of)` (:36015) -> `_dash_tab_grid` | the template's tab builder (the emitted lines around `_dash_parse_tabs(` in `_generate_app_source`) -> `_dash_tab_grid` | `grep -n "_dash_parse_tabs(\|_dash_tab_panels(" dash_render.py` |
| same-cell first wins | the DashRenderer grid `_slots` fill (:44760-44790) | the emitted line :50711 gains the guard `if _slots[_r][_c] is None:` (:50719 unchanged) | `grep -n "_slots\[_r\]\[_c\] = _dash_cell" dash_render.py` |
| layout check report | `_dash_layout_check` from `_dash_cap_spec` (:4136; both modes run the cap) | the same | `grep -n "_dash_layout_check(" dash_render.py` |
| legend label blank | `_dash_apply_legend` :28325-28327 (copied) | the same | `grep -n "_DASH_LEGEND_LABEL_RE" dash_render.py` |
| refusals | dash.ado (`dash build` path; `_dash_validate_opts`) -> Mata | n/a | `grep -n "_dash_layout_refusal\|_dash_check_legend\|_dash_subopt_check legend" dash.ado` |

### Measured red list procedure (39-01)

On a scratch copy, change `_dash_parse_tabs`'s return shape, the served `_slots` fill, the label regex and the order of the two legend checks; run `python3 -m pytest test/test_layout_tabs.py test/test_layout_placement.py test/test_legend_order.py test/test_axis_options.py test/test_subopt_abbrev.py test/test_help_claims_*.py -q -n0 -p no:cacheprovider -rf` and the two cscripts through the driver; copy the failing ids and FAIL cases with reasons into `<scratch>/39-flips.txt`; delete the copy. JSE-47 (test_json_escaping.cscript) is listed only if its expected line changes under the fixture's `legend.jse47`.

### What is dash's and what is twoway's

`tabs()` and `layout()` are dash's options: their refusals are dash's existing sentence forms (`layout() name 'x' not found in registry.`, `layout() places 'x' more than once.`), extended, and the CHANGELOG names them under Changed behaviour because a do-file that relied on the silence now stops (M5's rule for newly refused forms). `legend()` and `title()` are twoway's: every line and return code is the fixture's, never typed from memory (Q17); where the fixture shows twoway accepting a nested probe, dash stays silent.

## Boundaries

- Not the legend's geometry or `order()` (S31 landed); not `_dash_apply_legend` beyond :28325-28327.
- Not the `bs` layout grammar; not the auto grid (`_dash_auto_grid_cols`); not `_dash_layout_cell` (S48, batch 16).
- Not `_FILTER_JS`, `_make_figure_body`, `_build_filter_widgets`, the appliers (R12); the template edit is the tab builder only.
- No twoway rule invented: tabs()/layout() refusals are dash's own sentences (dash options); the legend/title rules are measured.

## Stata truth

**New extractor** `scripts/extract_tabs_legend_edges_truth.do` (path-free form of scripts/extract_by_grid_truth.do :1-45), run as `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s39/x $WT/scripts/extract_tabs_legend_edges_truth.do`, writing `test/fixtures/tabs_legend_edges_truth.json` (`git add -f`; `_meta` five keys). twoway only (tabs()/layout() rows are dash's and have no twoway half); `sysuse auto`; `set scheme s2color`.

| Key | twoway command (`capture noisily twoway scatter mpg weight, ...`) | Recorded |
|---|---|---|
| `legend.po9_top`, `legend.top_po9`, `legend.top` | `legend(po(9) top)`, `legend(top po(9))`, `legend(top)` | rc, first error line |
| `title.prefix_suffix`, `title.suffix_prefix` | `title("T", prefix suffix)`, `title("T", suffix prefix)` | rc, every log line, the drawn title text (SVG) |
| `nested.region_lcolor_bogus`, `nested.region_fcolor_red`, `nested.region_bad_word`, `nested.title_size_bogus`, `nested.title_size_large`, `nested.title_bad_word` | `legend(region(lcolor(bogus)))`, `legend(region(fcolor(red)))`, `legend(region(xx))`, `legend(title("T", size(bogus)))`, `legend(title("T", size(large)))`, `legend(title("T", xx))` | rc, log lines, drawn legend box colour / title size |
| `label.one`, `label.one_text` | `scatter mpg weight || scatter price weight, legend(label(1))`, `legend(label(1 "A"))` | rc, the legend key texts from the SVG |

**Truth blocks** (R1; one per row, DECISIONS A14): `test/test_wp31_truth.cscript`, header `* ==== S39 D14: tabs() and layout() edges ====` holding U39-02 (appended by 39-01) and header `* ==== S39 D16: legend edges ====` holding U39-06 (appended by 39-03, so the D14 commit stages no red D16 case); helpers `_ut_*`, cases ending `_w31_done U39-0k`; refusal cases in `test_option_validation.cscript` before `// Summary` (U39-01 appended by 39-01; U39-03, U39-04, U39-05 appended by 39-03):
- **U39-01** (option_validation) `dash build, saving(x.html) tabs(A: nosuch g1) replace` after registering `g1`: rc equals layout()'s unknown-name rc and the line is `tabs() name 'nosuch' not found in registry.`; `layout(g1:1,1 g2:1,1)` rc the same and `layout() places 'g1' and 'g2' in the same cell 1,1.`; `tabs(A: g1 g2, layout(3 3 3))` refused with the layout form sentence; `tabs(A: g1 g2, layout(1 2))` rc 0.
- **U39-02** (truth) `tabs(A: g1 g2, layout(1 2) / B: g3)` saved and served: tab A's grid is 1 x 2 with g1 then g2; tab B auto.
- **U39-03** (option_validation) `dash scatter mpg weight, legend(po(9) top)`: rc and line equal twoway's `legend.po9_top`; `legend(top po(9))` equal `legend.top_po9`; `legend(top)` keeps dash's advice line after twoway's line (or dash's line alone if twoway's first line is the keyword's).
- **U39-04** (option_validation) `title("T", prefix suffix)`: dash's log holds twoway's `title.prefix_suffix` line; the drawn title text equals the fixture's.
- **U39-05** (option_validation) each `nested.*` probe: rc equals twoway's; a refused probe's line equals twoway's; an accepted probe's log holds no new note.
- **U39-06** (truth) `legend(label(1))` on two layers: key 1's text is `""` saved and served; `label(1 "A")` is `A`.

## TDD test stubs

### Regression tests, red at `6370ca4` unless marked guard

`test/test_tabs_layout_edges.py` (D14; helpers: saved/served builders from test_layout_tabs.py):
- Test: fixture `_meta`/keys -- `TestTheFixture::test_meta`, `::test_keys` (guard).
- Test: `_dash_parse_tabs` returns three-tuples; an unknown name warns once; a known spec is unchanged -- `TestParseTabs::test_shape`, `::test_unknown_warns`, `::test_known_silent` (red: two-tuples, silence).
- Test: per-tab `layout(1 2)` and `layout(a:1,1 b:1,2)` give the tab's grid; a name outside the tab, a repeated cell or `bs` is dropped with a warning (bypassing spec) -- `TestPerTabLayout::test_grid[mode]`, `::test_placement[mode]`, `::test_bad_forms_warn`, `::test_comma_in_title_is_the_options_split` (red).
- Test: the served and saved grids keep the first name on a same-cell collision and `_dash_layout_check` reports it -- `TestSameCell::test_saved_first`, `::test_served_first`, `::test_check_reports` (red: served draws the second; no report).
- Test: `_dash_tab_grid` is in the copy list; the template calls it -- `TestServedCopy::test_names`, `::test_template_call` (red).

`test/test_legend_edges.py` (D16):
- Test: `_DASH_LEGEND_LABEL_RE` matches `1` (group(2) None) and `1 A`, and `lastlabel(1)` at :28354 still resolves key 1; `legend(label(1))` blanks key 1 in both modes; `label(1 "A")` keeps `A` -- `TestLabelBlank::test_regex`, `::test_blank[mode]`, `::test_text[mode]` (red).
- Test: the renderer's title reader draws the fixture's prefix/suffix winner -- `TestPrefixSuffix::test_winner[mode]` (red or guard per fixture).
- Test: the fixture's `legend.*`, `title.*`, `nested.*` records exist with rc and lines (guard); the Mata nested kinds exist in dash_parse.mata (`legend_region`, `legend_title`) -- `TestTheChecks::test_kinds_exist` (red; reads the source).

### Cases in cscripts
- D14 (written by 39-01): `test_wp31_truth.cscript` U39-02 (red); `test_option_validation.cscript` U39-01 (red). D16 (written by 39-03 on the D14 tree): `test_wp31_truth.cscript` U39-06 (red); `test_option_validation.cscript` U39-03, U39-04, U39-05 (red).

### Flips (in place, each with a `Flipped:` line)
From `<scratch>/39-flips.txt`; D14 docstrings gain "tabs() refuses unknown names and same-cell placements are refused, as layout() refuses its errors (WP-31 D14)"; D16 docstrings "twoway refuses legend() tokens left to right, prints the prefix/suffix line, checks nested values and blanks label(#) (WP-31 D16)". JSE-47 in test_json_escaping.cscript is flipped in place only if twoway's first line for `legend(label(1 "'90s") top)` differs from dash's today (fixture `legend.top` and the measured JSE-47 probe in 39-01).

### Parity corpus (R8; guards at base)
TR-39.9's entries.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| tabs() unknown names | cscript U39-01; pytest `TestParseTabs` | -- | yes |
| per-tab layout | pytest `TestPerTabLayout`; U39-02 | -- | yes |
| same-cell collision | pytest `TestSameCell`; U39-01 | -- | yes |
| legend token order | cscript U39-03 | `legend.*` | n/a |
| prefix/suffix line and winner | cscript U39-04; pytest `TestPrefixSuffix` | `title.*` | yes |
| nested values | cscript U39-05 | `nested.*` | n/a |
| label(#) blank | pytest `TestLabelBlank`; U39-06 | `label.*` | yes |
| parity | `python3 -m pytest test/test_mode_parity.py -q -n0` | -- | yes |

**Acceptance criteria**
- **AC-39.1** `tabs(A: nosuch g1)` is refused with `tabs() name 'nosuch' not found in registry.`; `layout(g1:1,1 g2:1,1)` with `layout() places 'g1' and 'g2' in the same cell 1,1.`; both grids keep the first name for a bypassing spec and `_dash_layout_check` reports it.
- **AC-39.2** `tabs(A: g1 g2, layout(1 2))` draws tab A as 1 x 2 in both modes; bad per-tab forms are refused.
- **AC-39.3** `legend(po(9) top)` and `legend(top po(9))` give twoway's first lines; `title("T", prefix suffix)` prints twoway's line and draws its winner; every `nested.*` probe matches twoway's rc and line; `legend(label(1))` blanks key 1 in both modes.
- **AC-39.4** `WP31_ONLY=S39` prints U39-02 and U39-06 PASS; test_option_validation.cscript prints U39-01, 03, 04, 05 PASS and ALL CHECKS PASSED; no SKIP; two green commits `(WP-31 D14)`, `(WP-31 D16)`.

## Tasks

**Commit boundary.** 39-01 commits nothing. 39-02 makes the D14 commit, subject `Refuse unknown tabs() names and same-cell placements, and draw a per-tab layout() (WP-31 D14)`; 39-03 the D16 commit, `Refuse legend() tokens in twoway's order, print the prefix/suffix line, check nested values and blank label(#) (WP-31 D16)`. Both on `wp31-s39` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s39`. Bodies per BRIEF: the saved failure text, the measured defect, the change, `Regression:`, `Flipped:` lines, `Fixture: test/fixtures/tabs_legend_edges_truth.json (scripts/extract_tabs_legend_edges_truth.do)` (D16; D14 names it as shared), `BUGS.md: "<title>" (closed)`, `GAPS3: <row> Tracked`. Each Tracked line reads `commit pending` (A11); no amend.

<task type="auto" id="39-01">
  <name>Measure twoway and write the failing tests</name>
  <files>scripts/extract_tabs_legend_edges_truth.do, test/fixtures/tabs_legend_edges_truth.json, test/test_tabs_layout_edges.py</files>
  <action><![CDATA[
    Check `git -C $WT rev-parse HEAD` equals `<scratch>/batch-13-base.txt` and the branch is `wp31-s39`; `mkdir -p <scratch>/s39/x`. Create scripts/extract_tabs_legend_edges_truth.do by the "Stata truth" table (head from scripts/extract_by_grid_truth.do :1-45; also probe `legend(label(1 "'90s") top)` for JSE-47 and record it as `legend.jse47`), run it through the slot, `git add -f test/fixtures/tabs_legend_edges_truth.json`, and write the measured lines (`legend.po9_top`, `title.prefix_suffix` and its winner, each `nested.*` rc) to `<scratch>/s39/measured.txt`. Create test/test_tabs_layout_edges.py and test/test_legend_edges.py with the classes of "TDD test stubs". Append the D14 block (`* ==== S39 D14: tabs() and layout() edges ====`, U39-02) to test/test_wp31_truth.cscript above the marker line and U39-01 to test/test_option_validation.cscript before `// Summary` (the D16 cases are 39-03's, A14). Measure which `_dash_check_legend` site fires first for `legend(po(9) top)` (dash.ado:4010 or :7088; TR-39.5) and record it in `<scratch>/s39/measured.txt`. Run `python3 -m pytest test/test_tabs_layout_edges.py test/test_legend_edges.py -q -n0 -p no:cacheprovider -rf > <scratch>/s39/39-01.log 2>&1` and both cscripts through the driver (`WP31_ONLY=S39`); write `<scratch>/39-01-failure.txt`; list the pins a simulated fix turns red into `<scratch>/39-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/tabs_legend_edges_truth.json'));print(sorted(d['_meta']))"` prints `['born_date', 'dash_commit', 'extracted', 'source', 'stata_version']`; `grep -c FAILED <scratch>/s39/39-01.log` is at least 12 and none names `TestTheFixture`; `grep -c "U39-0[12] FAIL" <scratch>/s39/run_test_wp31_truth.log <scratch>/s39/run_test_option_validation.log` totals 2; no SKIP; `grep -c "4010\|7088" <scratch>/s39/measured.txt` prints 1; `test -s <scratch>/39-01-failure.txt`.]]></verify>
  <done>twoway's legend and title refusal lines, nested-value checks and blank-label drawing were recorded in a stamped fixture, and every regression test and case was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="39-02">
  <name>Refuse tabs and cell errors, draw per-tab layouts</name>
  <files>dash_parse.mata, dash.ado, dash_render.py</files>
  <action><![CDATA[
    In dash_parse.mata: add `_dash_tabs_refusal` after `_dash_layout_refusal` (:1679; TR-39.1, D-39.a, D-39.b) with its header-index line; extend `_dash_layout_refusal` with the same-cell check after :1676 (TR-39.2, D-39.c), extending `_dash_layout_scan` (:1483) with the optional `cells` rowvector argument (no new function; `_dash_layout_cells` at :1569 is untouched). In dash.ado: the `_needed` entries (alphabetical, :448-479); call `_dash_tabs_refusal` in `dash build`'s validation where `_dash_layout_refusal` is called, refusing with the same rc through `_dash_say("err", ...)`. In dash_render.py: `_dash_parse_tabs` (:35974) returns `(title, names, layout)` and warns once for unknown names and bad per-tab forms; `_dash_tab_grid` after `_dash_tab_panels` (:36015), called by `_dash_tab_panels` and the template's tab builder (TR-39.4); `_dash_layout_check` (:3550) reports the collision; the served grid's placement assignment (:50711) gains the one `if _slots[_r][_c] is None:` guard (:50719 unchanged). Copy-list entry `"_dash_tab_grid",` after `"_dash_parse_tabs",` (adding `"_dash_parse_tabs",` if absent). Flip the D14 nodes of `<scratch>/39-flips.txt`; add `test/function_test_map.py` and `test/program_coverage_map.py` entries. Help (TR-39.8): Tabs :1551-1584 and Layout :1473-1550; TWOWAY_COVERAGE_AUDIT.md :158. Close the D14 BUGS.md entry (Resolution naming `_dash_tabs_refusal`, `_dash_layout_refusal`, `_dash_parse_tabs`, `_dash_tab_grid`, `_dash_layout_check`, the served grid, both renderers), rewrite the D14 Tracked line to `- **D14 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (A11; the merger writes the sha), replace the `<!-- WP-31 D14 -->` markers (Changed behaviour: `tabs()` with an unregistered name and a `layout()` placing two names in one cell are refused, naming them; they were drawn without the name or with the second graph only; Results: `layout(s1:1,1 s2:1,1)` served drew s2, a bypassing spec now draws s1 as the saved page did). Run `python3 -m pytest test/test_tabs_layout_edges.py test/test_layout_tabs.py test/test_layout_placement.py test/test_help_conformance.py test/test_tracking_documents.py test/test_statistical_helpers.py -q -p no:cacheprovider` plus the D14 files `<scratch>/39-flips.txt` names, and both cscripts through the driver. Stage dash_parse.mata dash.ado dash_render.py dash.sthlp TWOWAY_COVERAGE_AUDIT.md BUGS.md CHANGELOG.md GAPS3.md scripts/extract_tabs_legend_edges_truth.do test/test_tabs_layout_edges.py test/test_wp31_truth.cscript test/test_option_validation.cscript test/function_test_map.py test/program_coverage_map.py and the flipped D14 files; `git add -f test/fixtures/tabs_legend_edges_truth.json`; NOT test/test_legend_edges.py. Commit with the D14 subject; grep the message for `claude|anthropic` before and after.
  ]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; the driver logs show `U39-01 PASS` and `U39-02 PASS`, `ALL CHECKS PASSED`, no SKIP (no D16 case exists on this tree yet); `git log -1 --format=%s` ends `(WP-31 D14)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 D14 -->' CHANGELOG.md` prints 0; `git show --stat HEAD | grep -c test_legend_edges` prints 0; `grep -c "ignored without a message" dash.sthlp` prints 0.]]></verify>
  <done>Unknown tabs() names and same-cell placements were refused in Mata and reported by the renderer, both grids kept the first name, per-tab layout() was drawn in both renderers, and D14 was committed green.</done>
</task>

<task type="auto" id="39-03">
  <name>Match twoway's legend and title edges</name>
  <files>dash.ado, dash_parse.mata, dash_render.py</files>
  <action><![CDATA[
    Append the D16 block (`* ==== S39 D16: legend edges ====`, U39-06) to test/test_wp31_truth.cscript above the marker line and U39-03, U39-04, U39-05 to test/test_option_validation.cscript before `// Summary` (A14). Re-run `python3 -m pytest test/test_legend_edges.py -q -n0 -p no:cacheprovider -rf > <scratch>/s39/39-03-red.log 2>&1` and both cscripts through the driver on the D14 tree (U39-03..U39-06 FAIL) and append the text to `<scratch>/39-01-failure.txt` under `D16`. In dash.ado `_dash_validate_opts` (:4010): record the legend copies and run `_dash_subopt_check legend` before `_dash_check_legend` (TR-39.5, D-39.d). In dash_parse.mata `_dash_subreq_*` (:8206-8300): the `prefix suffix` line (D-39.e, the fixture's text verbatim through `_dash_say("text", ...)`), the `legend_region`/`legend_title` kinds (D-39.f) refusing the fixture's refused probes with their lines. In dash_render.py: `_DASH_LEGEND_LABEL_RE` (:37102) and :28327 per D-39.g; the title reader's prefix/suffix winner per the fixture. Flip the D16 nodes of `<scratch>/39-flips.txt` (JSE-47 only if the fixture says twoway's first line differs). Append TR-39.9's parity entries under `# WP-31 D14/D16`. Help (TR-39.8): Differences from twoway :866-890 and the legend `label()` sentence (:4268 region, `grep -n "legend(label(0" dash.sthlp`); TWOWAY_COVERAGE_AUDIT.md :136. Close the D16 BUGS.md entry (Resolution naming `_dash_validate_opts`, `_dash_subreq_check`, `_DASH_LEGEND_LABEL_RE`, `_dash_apply_legend`, both renderers), rewrite the D16 Tracked line to `- **D16 Tracked:** Closed in WP-31, BUGS.md "<title>", commit pending.` (A11), replace the `<!-- WP-31 D16 -->` markers (Changed behaviour: `legend(po(9) top)` named `top`, now twoway's first line; nested values in `legend(region())`/`legend(title())` are checked as twoway checks them; Results: `legend(label(1))` kept the key's text, now blank; `title("T", prefix suffix)` prints twoway's line). Run `python3 -m pytest test/test_legend_edges.py test/test_legend_order.py test/test_axis_options.py test/test_subopt_abbrev.py test/test_mode_parity.py test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider` plus the D16 files `<scratch>/39-flips.txt` names, and test_option_validation.cscript, test_json_escaping.cscript (if JSE-47 flipped) and the truth block through the driver. Stage dash.ado dash_parse.mata dash_render.py dash.sthlp TWOWAY_COVERAGE_AUDIT.md BUGS.md CHANGELOG.md GAPS3.md test/test_legend_edges.py test/test_mode_parity.py test/test_option_validation.cscript test/test_wp31_truth.cscript and the flipped D16 files (test/test_json_escaping.cscript if flipped); commit with the D16 subject; grep the message. Report both shas.
  ]]></action>
  <verify><![CDATA[The pytest run reports 0 failed; the driver logs show `U39-03 PASS`, `U39-04 PASS`, `U39-05 PASS`, `U39-06 PASS`, `ALL CHECKS PASSED`, no SKIP; `python3 -c "import dash_render as d; print(bool(d._DASH_LEGEND_LABEL_RE.fullmatch('1')))"` prints True; `git log -1 --format=%s` ends `(WP-31 D16)`; `git log -2 --format=%s | grep -c "(WP-31 D14)\|(WP-31 D16)"` prints 2; `git log -2 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-31 D16 -->' CHANGELOG.md` prints 0.]]></verify>
  <done>legend() tokens were refused in twoway's order, the prefix/suffix line printed, nested region()/title() values checked as twoway checks them, label(#) blanked its key in both renderers, and D16 was committed green as the section's second commit.</done>
</task>

## Section completion criteria

- `tabs()` unknown names and same-cell placements refused in Mata with dash's sentences; the renderer reports both for bypassing specs; both grids keep the first name; per-tab `, layout()` drawn in both modes.
- `legend(po(9) top)`, `title("T", prefix suffix)`, the nested probes and `legend(label(1))` match the fixture in both modes.
- `tabs_legend_edges_truth.json` stamped and named; U39-01..U39-06 PASS; flips recorded; two green commits; two BUGS.md entries closed; two Tracked lines; four markers replaced; help, audit, maps, corpus updated.

## Notes

- **Order of refusals in dash.ado.** `_dash_validate_opts` runs the sub-option check before `_dash_check_legend` only for the legend kind; the `region`/`zlabel`/`title` checks at :6978-6992 stay where they are (region before plotregion before legend, as the help's Region Styling paragraph says).
- **The per-tab comma.** A title cannot hold a colon or a slash today; with D-39.b it cannot hold a top-level comma either; the help says so. Quote-aware splitting is `_dash_by_tokens_commas`'s job (already on the copy list, :47224): reuse it.
- **Template edit (R12).** S39 is batch 13's `_generate_app_source` editor: the tab-builder lines and the one guard line at :50711 only (:50719 unchanged).
- **python_exec hazard** (project memory) after each cscript run; a SKIP is not a pass.
- **Shared files.** R1: two truth blocks (D14: U39-02; D16: U39-06), U39-01/03/04/05 in test_option_validation.cscript, each row's cases appended by its own closing step (A14), JSE-47 flipped in place only if measured; R2: one function after `_dash_parse_tabs`; R3: Tabs, Layout, Differences from twoway (the two sentences named), the legend label() sentence; R4: four markers; R5: two entries, two Tracked lines; R6: one Mata function, one `_needed` entry, one build-path call, the `_dash_validate_opts` reorder; R7: one extractor; R8: corpus; R9: flips; R10: none; R12: the template's tab builder and grid lines.
- **Commit-body line forms** are BRIEF's; `failed at` is `batch-13-base.txt`'s sha for D14, the D14 sha for D16.
- **For S48 (batch 16, `_dash_layout_cell`).** The per-tab layout passes through `_dash_tab_grid`, not `_dash_layout_cell`; S48's data table joins a cell, not a tab.
- **Decided (DECISIONS D5).** D-39.a: `tabs()` with an unknown graph name is refused r(198), as `layout()` is; the maintainer confirmed it; the Changed-behaviour CHANGELOG line of "CHANGELOG lines" records it. Not for ratification.
- **Decisions for maintainer ratification.** D-39.b (the per-tab `, layout()` grammar and the comma rule), D-39.c (same-cell collision refused), D-39.d (sub-option check before the keyword scan).

## Addendum (15oct2026, DECISIONS D23): row D16b added to this section

### D16b: A bare quoted string after the comma is named in the note where twoway refuses it as quotes unbalanced

**Gap.** twoway's option parser refuses a bare quoted string among the options (`, "abc"` or `, "$G" name(x)`) with "quotes unbalanced", r(198), on every plot type (S26 measured scatter, contour, contourline). dash's catch-all keeps the string and names it in the note; test_json_escaping.cscript JSE-69 pins that and checks the macro text is never expanded.

**Requirement.** Measure twoway across placements (plot options, graph options after `||`, inside `( )`), refuse each bare string as twoway does in its words and code, and flip JSE-69 to the refusal while keeping its check that the text is never expanded; a Changed-behaviour line names the refused form. S26's `_dash_opt_tokens` (Mata) splits option text by value and may be reused.

**Fits S39** because S39 matches twoway's refusal order and messages for option forms (D16) in batch 13.

**Process (binding).** As every row: measure twoway first (the measurement wins over this text; record a deviation); failing tests first with saved failure text; ONE commit with subject ending `(WP-31 D16b)`; close the BUGS.md entry "A bare quoted string after the comma is named in the note where twoway refuses it as quotes unbalanced" (Resolution ending `Closes GAPS3 D16 (WP-31, D16b).`), delete its `"D16b":` WP31_OPEN line, rewrite GAPS3.md's `- **D16b Tracked:**` line to `Closed in WP-31, BUGS.md "<title>", commit pending.`, replace `<!-- WP-31 D16b -->` under `### Changed behaviour (may need your do-files changed)` with a line ending `(WP-31, D16b)`. dash replaces twoway (D13).

## Addendum (15oct2026, DECISIONS D25): row D4b added to this section

### D4b: Legend stacked, symplacement(), colgap() and the legend's own subtitle(), note() and caption() are named, not drawn

**Gap.** S31's `_dash_apply_legend` draws the legend's geometry, clock/ring, holes, rows/cols, label(#) blanking and the key merge; `stacked`, `symplacement()`, `colgap()` and legend(subtitle() note() caption()) remain named.

**Requirement.** Measure twoway for each (fixture via an extract script), then draw: colgap() as the legend's column spacing, symplacement() as the glyph's alignment in the key box, stacked as text below the symbol, and the legend's own subtitle/note/caption as text above/below the legend box (Bokeh Legend has a title only: use Labels or a wrapping layout); both modes. Where Bokeh cannot express one, document it with a measured example (M17) and keep it named. textfirst stays out of scope (PRD section 7).

**Fits S39** because S39 handles the legend label edges (D16) in batch 13.

**Process (binding).** As every row: measure twoway first (the measurement wins over this text; record a deviation); failing tests first with saved failure text; ONE commit with subject ending `(WP-31 D4b)`; close the BUGS.md entry "Legend stacked, symplacement(), colgap() and the legend's own subtitle(), note() and caption() are named, not drawn" (Resolution ending `Closes GAPS3 D4 (WP-31, D4b).`), delete its `"D4b":` WP31_OPEN line, rewrite GAPS3.md's `- **D4b Tracked:**` line to `Closed in WP-31, BUGS.md "<title>", commit pending.`, replace `<!-- WP-31 D4b -->` under `### Results that change` with a line ending `(WP-31, D4b)`. dash replaces twoway (D13).

## Addendum (16oct2026, DECISIONS D32): row D10b added to this section

### D10b: by()'s shrink, overallshrink, region margins, array outline and the econ, stata7, combine and rescale bystyles are named, not drawn

**Gap.** S36 drew by()'s regions per panel and named the rest; S37's `_dash_graph_margin` returns early on by() graphs because their graph region holds the whole array.

**Requirement.** Using `test/fixtures/by_remainder_truth.json` (re-extract with any new probes): scale the panel contents by twoway's shrink factor for shrink/overallshrink; inset the panel grid once by by()'s region margin(); draw by()'s plotregion() outline once around the array (a wrapper box on the grid layout); draw the econ, stata7, combine, rescale and altleg bystyles' remaining attributes; both modes; drop each from the note as it is drawn.

**Fits S39** because S39 owns the dashboard layout checks and grid cells in batch 13.

**Process (binding).** As every row: measure twoway first (the measurement wins over this text; record a deviation); failing tests first with saved failure text; ONE commit with subject ending `(WP-31 D10b)`; close the BUGS.md entry "by()'s shrink, overallshrink, region margins, array outline and the econ, stata7, combine and rescale bystyles are named, not drawn" (Resolution ending `Closes GAPS3 D10 (WP-31, D10b).`), delete its `"D10b":` WP31_OPEN line, rewrite GAPS3.md's `- **D10b Tracked:**` line to `Closed in WP-31, BUGS.md "<title>", commit pending.`, replace `<!-- WP-31 D10b -->` under `### Results that change` with a line ending `(WP-31, D10b)`. dash replaces twoway (D13).

## Addendum (16oct2026, DECISIONS D32): row D11b added to this section

### D11b: margin(l+1e400) draws zeros with a note where twoway draws a medium margin

**Gap.** `_dash_margin_sides` gives zeros for `l+1e400`; twoway gives medium with the gsize note. `l+3pt`'s geometry is unmeasured.

**Requirement.** Probe both in plotregion() and graphregion() (extend scripts/extract_region_remainder_truth.do), then match the margin and the note; both modes.

**Fits S39** because S39 takes D10b's region margins in the same batch.

**Process (binding).** As every row: measure twoway first (the measurement wins over this text; record a deviation); failing tests first with saved failure text; ONE commit with subject ending `(WP-31 D11b)`; close the BUGS.md entry "margin(l+1e400) draws zeros with a note where twoway draws a medium margin" (Resolution ending `Closes GAPS3 D11 (WP-31, D11b).`), delete its `"D11b":` WP31_OPEN line, rewrite GAPS3.md's `- **D11b Tracked:**` line to `Closed in WP-31, BUGS.md "<title>", commit pending.`, replace `<!-- WP-31 D11b -->` under `### Results that change` with a line ending `(WP-31, D11b)`. dash replaces twoway (D13).

