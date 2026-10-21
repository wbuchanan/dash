# Section 36-02: WebGL: dashed lines on canvas, switch on drawn rows

> Part of: WP-36 (Python discovery and environment) · Items: DG-14 · Risk: yellow · Batch: 36.1 · Depends on: none · Blocks: none · Tasks: 3, 1 commit · Case-id prefix: Q3602

## Overview

**What is wrong today.** The audit (package 2, DG-14, audit :115-117 and appendix :3332-3337): "WebGL above 10,000 dataset rows: thick dashed lines draw speckled; the switch counts the dataset's rows, not the graph's." The figure's backend is chosen once, from `len(self.df)` (dash_render.py:63396-63397; the served twin is the string literal `n_rows = len(df)` at :70284-70285): every figure of a dashboard whose dataset has more than `_WEBGL_THRESHOLD` = 10,000 rows (:5567) is drawn with WebGL, even a graph of `in 1/100`. Bokeh's WebGL line shader breaks dashed and dotted lines up: research [B] §4.7 measured, on the real GPU (ANGLE Metal) and on SwiftShader, an ink IoU against the canvas drawing of 0.435 for a 4 px dotted line and 0.615-0.801 for dashed lines at 20,000 vertices, against 0.917 for a solid line. Bokeh has no per-renderer backend ([B] §4.7: `output_backend` is on `Plot` only), so a dashed line can stay on canvas only if its whole figure does.

**What will be true after.** Ruling M8 / Q34: the switch counts the rows the figure draws (the rows its source carries, or the rows its view keeps), and a figure that draws any Line, MultiLine or Step glyph with a non-solid dash pattern stays on canvas whatever its row count. Both modes decide the same way. A headless-Chrome check with WebGL actually on (SwiftShader) pins that a dashed line above the threshold is drawn on canvas and matches a canvas reference.

**Why one section.** One item with two halves in the same two lines of code: the backend choice in `_make_figure_body` and its served twin.

**Test order and commit rule.** Task 36-02-01 gives the browser probes their flags attribute (TR-36-02.5, a test-harness change only, so the pixel test runs with WebGL on), writes the failing unit and browser tests and saves the failure text, no commit; 36-02-02 makes the change in both renderers; 36-02-03 runs the tests and the parity entry, closes the item and commits once with the subject ending `(WP-36 DG-14)`.

### Section decisions

- **D-36-02.a "Rows the graph draws".** Saved: `_dash_drawn_rows(source, facet_view)` -- the number of True values of the view's `BooleanFilter.booleans` (or the length of its `IndexFilter.indices`) when the figure has a view, else the number of rows the figure's source carries (the length of its row-id column, named by 35-08's `_dash_row_id(spec)`; the source being already graph-qualified and, under by(), the panel's: dash_render.py:64886-64996). Served: `len(g_df)` (`g_df` "arrives QUALIFIED from the caller", :70259-70261). A layer's own `if`/`in` view is not counted: the figure's backend serves every layer, and the largest layer is at most the figure's rows. With no qualifier and no by() the count equals `len(self.df)`, so today's choice is unchanged there.
- **D-36-02.b Dashed means a non-empty `line_dash`.** Bokeh stores every pattern as a list ("solid" is `[]`, "dashed" `[6]`, "4 4" `[4, 4]`; measured on 3.8.0 and 3.9.0). After the layer loop, `_dash_dashes_on_canvas(fig)` sets `fig.output_backend = "canvas"` when the figure is `"webgl"` and any of its renderers is a `GlyphRenderer` whose `glyph` is a `Line`, `MultiLine` or `Step` with a non-empty `line_dash`. Only those three glyphs have a GL line path among the glyphs dash draws as lines ([B] §4.7); Segment, Patch, VArea, Span and the annotations always paint on canvas and are not inspected.
- **D-36-02.c The pixel check runs in the release tier.** It needs Chrome with WebGL on: `--disable-gpu --enable-unsafe-swiftshader` ([B] §4.7, measured working; CI-stable). The probe's flags become a class attribute so one subclass can change them; every existing probe keeps `--disable-gpu` alone.

## Risk: [yellow] -- the backend of every large figure in both modes

**Why.** Every figure passes through the backend choice; a mistake turns large scatters back to canvas (slow) or leaves dashes speckled.

**Risk factors.** 1. A figure with a link() view must count the view's rows, not the shared source's. 2. The served literal and the saved code must agree. 3. Existing tests pin `webgl` on a 10,001-row scatter (test_html_output.py:1980-1995, test_csp_browser.py:464, :741, test_export_svg.py:405-414). 4. `fig.renderers` holds every renderer, the legend-only and invisible extent scatters among them.

**Mitigation.** 1. TR-36-02.1 reads the view's filter. 2. One unit test renders both modes with the threshold patched low and compares the backends. 3. Those pins are solid scatters with no qualifier: they stay `webgl` (guards, not flips). 4. Only Line/MultiLine/Step glyphs with a dash decide; a solid line or a scatter never does.

## Dependencies

- **Depends on:** none in WP-36. It builds on 35-08 (WP-35, landed): the row-id column is read through that section's per-spec accessor, not the module constant (REVIEW R2-40).
- **Blocks:** none.
- **Parallel batch:** 36.1, with 36-01 and 36-03; merge order 36-01, 36-02, 36-03.
- **Can run with:** both: 36-01 edits dash.ado's Python programs, dash_setup and the harness gates; 36-03 edits dash.ado's registration and dash_parse.mata. This section edits only dash_render.py (`_make_figure_body`, one served literal, the served function tuple, two new module functions), test/range_probe.py and test/test_csp_browser.py (a flags attribute), and owns `_make_figure_body` and the served backend lines in the batch (R12).

## Evidence

### Saved backend (dash_render.py, re-read before editing)

```python
5567  _WEBGL_THRESHOLD = 10_000
...
63395         # Enable WebGL for large datasets
63396         n_rows = len(self.df)
63397         backend = "webgl" if n_rows > _WEBGL_THRESHOLD else "canvas"
...
63422             output_backend=backend,
```
`_make_figure_body(self, graph_spec, source, facet_view=None, rescale=frozenset())` (:63356). The figure is finished at :64002-64010 (`_dash_apply_scale(fig, ...)`, `_dash_overhangs(fig, graph_opts)`, `_dash_apply_frame_aspect(...)`, `return fig`). Callers: `_make_figure` (:63341, :63350) from :65042 (by() panels, `facet_view=panel_view_r`) and :65109 (`facet_view=_qual_view`, a `CDSView(filter=BooleanFilter(...))` for linked graphs with qualifiers, built :64887-64899).

### Served backend (string literals in `ServerAppBuilder._generate_app_source_body`)

```python
70284             "        n_rows = len(df)",
70285             "        backend = 'webgl' if n_rows > _WEBGL_THRESHOLD else 'canvas'",
```
inside the generated `_dash_figure_for(g, gname, g_df, _fac_label=None, _rescale=frozenset())` (:70235); the figure is finished at :70698-70703 (`_dash_apply_scale(fig, ...)`, `_dash_overhangs(fig, go)`). The constant is written into the app at :68283. The served function tuple (:68102-68113) holds `_dash_apply_frame_aspect, _dash_overhangs, _dash_fxy_size,`.

### Dash patterns

Line patterns come from `translate_lpattern` (:9019) and the `line_dash` chains (:11989, :12392-12445, :12845); the scheme's default p#linepattern can itself be dashed (e.g. s1mono). Bokeh 3.8.0 and 3.9.0: `Line(line_dash="solid").line_dash == []`, `"dashed"` → `[6]`, `"dotted"` → `[2, 4]` (checked 20oct2026 in both).

### The measurement

[B] §4.7 (`$SCRATCH/r3/exp_webgl_dash.py`): a 500x200 figure per (backend, width, pattern), 20,000 vertices; ink = alpha > 0 and red < 128 in `Bokeh.index.find_one(model).export('png').canvas`'s pixels; IoU of webgl against canvas: GPU 0.615 (1 px dashed), 0.758 (4 px), 0.801 (8 px), 0.435 (4 px dotted), 0.685 (dashdot), 0.917 (solid); SwiftShader 0.565 / 0.844 / 0.859 / 0.553 / 0.767 / 0.961. Every existing browser probe passes `--disable-gpu`, which in Chrome 155 turns WebGL off completely, so `test_export_svg.py::test_a_webgl_figure_exports_as_vector` passes only because WebGL is off.

### Tests that pin today's behaviour

- test/test_html_output.py::TestWebglBackendLargeData (:1980-2015) and TestOutputBackendAndVisualMarkers::test_canvas_backend_omits_output_backend_key (:1897): a 10,001-row solid scatter is `webgl` -- stays true (guard).
- test/test_csp_browser.py `big` (:464) and `mixed_big` (:657, :741), test/test_export_svg.py:251-254 (`canvas` or `webgl`), :405-414 -- solid scatters: unchanged.
- No test qualifies a large dataset or draws a dashed line on a large one.

## User stories

- US-36-02.1 As a Stata user with an existing twoway command, I want `line y x, lpattern(dash)` on 50,000 rows to draw clean dashes, so that the picture is twoway's.
- US-36-02.2 As a dashboard author, I want a small graph of a large dataset (`in 1/100`, a by() panel) drawn the way a small dataset's is, so that it looks the same as its siblings.

## Business requirements

- BR-36-02.1 A graph that draws any dashed, dotted or patterned line is drawn on canvas in both modes, whatever its row count.
- BR-36-02.2 A graph's switch to WebGL depends on the rows that graph draws, not on the dataset's size.
- BR-36-02.3 A large solid scatter keeps WebGL, as today.

## Technical requirements

- **TR-36-02.1** New module functions in dash_render.py, placed directly after `_dash_overhangs` (re-read where it is defined):
  ```python
  def _dash_drawn_rows(source, facet_view=None, row_id=None):
      """The rows a figure draws (WP-36 DG-14): those *facet_view*'s filter
      keeps -- the True values of a BooleanFilter's booleans, the indices
      of an IndexFilter -- else every row *source* carries, counted on its
      row-id column *row_id* (the spec's, from 35-08's accessor) when the
      source has it.  The figure's source is already the graph's qualified
      rows, or a by() panel's (DashRenderer.render, 'Handle by()
      faceting')."""
      f = getattr(facet_view, "filter", None)
      b = getattr(f, "booleans", None)
      if b is not None:
          return int(np.count_nonzero(np.asarray(b, dtype=bool)))
      ix = getattr(f, "indices", None)
      if ix is not None:
          return len(list(ix))
      data = getattr(source, "data", None) or {}
      if row_id and row_id in data:
          return len(data[row_id])
      return max((len(v) for v in data.values()), default=0)


  def _dash_dashes_on_canvas(fig):
      """Keep a WebGL figure on canvas when it draws a dashed line (WP-36
      DG-14): Bokeh's WebGL line shader breaks dashes and dots up (ink IoU
      0.44-0.80 against canvas at 20,000 vertices, measured on the GPU and
      on SwiftShader), and a backend is a figure's, not a renderer's.  A
      Line, MultiLine or Step glyph with a non-empty line_dash decides;
      returns *fig*."""
      if getattr(fig, "output_backend", "canvas") != "webgl":
          return fig
      from bokeh.models import GlyphRenderer, Line, MultiLine, Step
      for r in list(getattr(fig, "renderers", None) or []):
          g = getattr(r, "glyph", None) if isinstance(r, GlyphRenderer) else None
          if isinstance(g, (Line, MultiLine, Step)) and list(g.line_dash or []):
              fig.output_backend = "canvas"
              break
      return fig
  ```
- **TR-36-02.2 Saved.** :63395-63397 become `# The rows this figure draws, not the dataset's (WP-36 DG-14).` / `n_rows = _dash_drawn_rows(source, facet_view, _dash_row_id(self.master_spec))` / `backend = "webgl" if n_rows > _WEBGL_THRESHOLD else "canvas"`. The row-id column is read through 35-08's accessor (TR-35-08.4: `_dash_row_id(spec)`, a function of the spec's `_dash_prefix`) as it stands at the batch-36.1 base, never through the module constant `_ROW_ID_COLUMN` (dash_render.py:5589 at 090d928), which 35-08 turned into a per-spec name (REVIEW R2-40); re-read the accessor's name and argument and the renderer's spec attribute (`self.master_spec` at 090d928, dash_render.py:62105) before writing the line. The count of a BooleanFilter is `np.count_nonzero` (REVIEW R2-39): a pure-Python loop over up to 20M booleans per figure is not used. After `_dash_overhangs(fig, graph_opts)` (:64005) add `_dash_dashes_on_canvas(fig)` with the comment `# WP-36 DG-14: a dashed line keeps the figure on canvas.`
- **TR-36-02.3 Served (R2).** The literal at :70284 becomes `"        n_rows = len(g_df)",` with a preceding literal `"        # The rows this figure draws, not the dataset's (WP-36 DG-14).",`; after the literal `"        _dash_overhangs(fig, go)",` (:70702) add `"        _dash_dashes_on_canvas(fig)",`. Add `_dash_dashes_on_canvas,` to the served function tuple directly after `_dash_overhangs,` (:68113; insert, do not reorder). `_dash_drawn_rows` is saved-only (the served app counts `g_df`) and gets no tuple entry; `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` must stay green.
- **TR-36-02.4 Maps.** test/function_test_map.py `FUNCTIONS`, two lines directly after `'_dash_overhangs.<locals>.raise_to': 'test/test_sizing.py::TestOverhangs::test_never_lowers',` (test/function_test_map.py:614 at 090d928; re-read), in the file's own quoting: `'_dash_drawn_rows': 'test/test_webgl_backend.py::TestTheSwitchCountsDrawnRows::test_a_view_counts_its_kept_rows',` then `'_dash_dashes_on_canvas': 'test/test_webgl_backend.py::TestDashedLinesStayOnCanvas::test_the_helper',`.
- **TR-36-02.5 Probe flags (test harness only; applied by 36-02-01, before the failing run).** test/range_probe.py `RangeProbe`: add the class attribute `CHROME_GPU_FLAGS = ("--disable-gpu",)` and replace the literal `"--disable-gpu",` in its argv (:155) with `*self.CHROME_GPU_FLAGS,`; test/test_csp_browser.py `_CspProbe.__enter__` (:202) the same (it inherits the attribute). No other probe changes. Until this lands, `_CspProbe` hard-codes `--disable-gpu`, `_GlProbe.CHROME_GPU_FLAGS` has no effect and WebGL stays off, so the pixel test could not show the defect.
- **TR-36-02.6 Help (R3).** dash.sthlp has no WebGL sentence at 090d928 (`grep -n -i webgl dash.sthlp` finds none). Add one paragraph in Resource limits directly before `{pstd}` / `{ul:A served dashboard} has rate limits of its own; ...` (:3053-3054; re-read): `{pstd}` / `{ul:WebGL.}  A graph that draws more than 10,000 rows is drawn with WebGL, which is faster for many points, unless it draws a dashed, dotted or patterned line, which WebGL breaks up: such a graph is drawn on the ordinary canvas.  The rows counted are the graph's own -- the rows its qualifiers select, or its {cmd:by()} panel's -- not the dataset's.` Pinned by test/test_webgl_backend.py::TestTheHelp::test_the_webgl_paragraph (reads `_between(_help(), "{ul:WebGL.}", "{ul:A served dashboard}")`, flattened, and asserts the three facts: 10,000, dashed or dotted on canvas, the graph's own rows).

## Boundaries

- No other `_make_figure_body` change; no `_FILTER_JS` or axis-finisher edit (JS = no); no change to `_WEBGL_THRESHOLD` (10,000 stays).
- Do not switch individual renderers (impossible in Bokeh) and do not swap glyph types to avoid GL.
- No browser other than Chrome (A1, R14).

## Stata truth

None: twoway has one renderer; the reference is dash's own canvas drawing ([B] §4.7). A short block in test/test_wp36_truth.cscript records that the two Stata routes produce the backend rule (R1):
```
* ==== S02 DG-14: WebGL on the rows a graph draws, dashes on canvas ====
```
cases Q3602-1: on `set obs 20000` data (`gen x = _n`, `gen y = mod(_n, 97)`), `dash line y x, lpattern(dash) saving(<tmp>.html, replace)` writes a page whose Figure model has no `output_backend` key or `"canvas"` (read through a `python:` helper parsing the page's JSON with `json`, as cert_svg.do's helpers are called); Q3602-2 `dash scatter y x in 1/100, saving(...)` → canvas; Q3602-3 `dash scatter y x, saving(...)` → `"webgl"`.

## TDD test stubs

Failing first (task 01):
- Test: a qualified graph of a large dataset is canvas -- test/test_webgl_backend.py::TestTheSwitchCountsDrawnRows::test_in_1_100_on_20000_rows[std|srv] (spec: one scatter with graph `in_expr` `1/100`; saved via `_render_to_html`-style helper, served via the generated app's figure models as test_mode_parity renders them).
- Test: a by() panel under the threshold is canvas -- ::test_by_panels_count_their_own_rows[std|srv] (20,000 rows, `by(g)` with 5 groups of 4,000).
- Test: a linked graph with a qualifier counts its view -- ::test_a_view_counts_its_kept_rows (two graphs, `link(_all)`, one with `in 1/50`).
- Test: a dashed line is canvas -- test/test_webgl_backend.py::TestDashedLinesStayOnCanvas::test_lpattern_dash_on_20000_rows[std|srv], ::test_a_dashed_scheme_default_is_canvas (s1mono line p2), ::test_the_helper (a webgl figure with one `line(line_dash="dotted")` → canvas; one solid line and a scatter → webgl; a canvas figure is untouched).
- Test: guards -- ::test_a_solid_scatter_stays_webgl[std|srv] (10,001 rows, today's pin).
- Test: the help -- test/test_webgl_backend.py::TestTheHelp::test_the_webgl_paragraph (red: no such paragraph).
- Test: pixels -- test/test_webgl_backend_browser.py (release tier, `pytestmark = pytest.mark.release`): `class _GlProbe(test_csp_browser._CspProbe): CHROME_GPU_FLAGS = ("--disable-gpu", "--enable-unsafe-swiftshader")`; ::test_webgl_is_on_in_the_probe (a 20,000-row solid scatter page: `Bokeh.index.find_one(fig).canvas_view.webgl != null`), ::test_a_dashed_line_matches_a_canvas_reference (the dash page of `line y x, lpattern(dash) lwidth(thick)` on 20,000 rows: its figure is canvas, and its ink -- [B]'s rule over `export('png').canvas` -- has IoU >= 0.95 with a second page built from the same spec with `_WEBGL_THRESHOLD` patched to 10**9).
- cscript: Q3602-1..3.
- Parity: test/test_mode_parity.py `CORPUS` gains `_case("DG-14: a dashed line", [plot_for("line", {"lpattern": "dash"})])` after the last line entry (R8); its figure profile carries the backend through the existing `_figure_profile`; with the parity frame it is canvas in both, and TestDashedLinesStayOnCanvas covers the large case.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| drawn-row count (qualifier, by(), link view) | pytest test_webgl_backend.py TestTheSwitchCountsDrawnRows | -- | yes |
| dashed lines stay on canvas | pytest TestDashedLinesStayOnCanvas | -- | yes |
| WebGL on, dashed ink matches canvas | release pytest test_webgl_backend_browser.py (Chrome, SwiftShader) | -- | saved |
| Stata routes | cscript S02 Q3602-1..3 | -- | saved |
| parity | CORPUS "DG-14: a dashed line" | -- | yes |
| no plain DG-14 ledger or known-differences row; guard verdicts unchanged or regenerated | pytest test_corpus_ledger.py; `python3 test/known_differences.py DG-14` and its hygiene command; S09 block of test_wp33_truth.cscript (`WP33_ONLY=S09`) | corpus_ledger.json, corpus_guard_truth.json | n/a |

- AC-36-02.1 `line y x, lpattern(dash)` over 20,000 rows: no `output_backend` (canvas) in both modes, ink IoU >= 0.95 against canvas with WebGL on.
- AC-36-02.2 `scatter y x in 1/100` over 20,000 rows: canvas in both modes; `scatter y x` over 20,000: webgl.

## Tasks

**Commit boundary.** One commit by 36-02-03, subject `Draw dashed lines on canvas and switch to WebGL on the rows a graph draws (WP-36 DG-14)`, staging dash_render.py, dash.sthlp, test/range_probe.py, test/test_csp_browser.py, test/test_webgl_backend.py, test/test_webgl_backend_browser.py, test/test_mode_parity.py, test/function_test_map.py, the S02 block, TWOWAY_COVERAGE_AUDIT.md, BUGS.md, GAPS4.md, CHANGELOG.md, test/test_tracking_documents.py, plus scripts/corpus/ledger.tsv and test/fixtures/corpus_ledger.json (and test/fixtures/corpus_guard_truth.json) when 36-02-03's ledger step changes them, and each test file whose `*_KNOWN` or `*_DELIBERATE` table its known-differences step edits (BRIEF "The corpus ledger and the known-differences tables"). `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp36-s02` (BRIEF "Pull form": every command names the worktree by this absolute path; `scripts/stata_slot.sh` runs `cd <scratch>` before Stata starts, so a relative path is not found).

<task type="auto" id="36-02-01">
  <name>Write the failing backend and pixel tests</name>
  <files>test/test_webgl_backend.py, test/test_webgl_backend_browser.py, test/test_csp_browser.py</files>
  <action><![CDATA[
    In $WT, re-read dash_render.py:63385-63430, :64000-64010, :70270-70300, :70695-70705 and :68100-68115, and 35-08's row-id accessor (`grep -n 'def _dash_row_id' dash_render.py`), and record the anchors in `<scratch>/36-02-anchors.txt` (with test/range_probe.py:150-160 and test/test_csp_browser.py:195-206); run `node .gitnexus/run.cjs impact "_make_figure_body" --direction upstream --repo .` and the same for `_generate_app_source_body` and `_dash_overhangs`, writing callers and risk to `<scratch>/36-02/anchors.txt` (HIGH, CRITICAL or UNKNOWN named in the hand-back; an UNKNOWN confirmed with `grep -n` before editing). Apply TR-36-02.5 first (`CHROME_GPU_FLAGS` in test/range_probe.py's `RangeProbe` and in test/test_csp_browser.py's `_CspProbe.__enter__`; a test-harness change, so every existing probe still passes `--disable-gpu` alone). Create test/test_webgl_backend.py with the classes of "TDD test stubs", building specs with test/test_html_output.py's helpers (`_single_graph_spec`, `_make_data_json`, `_render_to_html`, `_figure_backends`) for the saved page and test_mode_parity's `_render_pair` route (or `dr.ServerAppBuilder` exactly as test_mode_parity builds the served side) for the served one; the both-modes cases are parametrised `["std", "srv"]`. Create test/test_webgl_backend_browser.py (release tier) with `_GlProbe` as in the stubs; the ink JS is [B] §4.7's rule. Append the S02 block (Q3602-1..3) above the marker of test/test_wp36_truth.cscript. Run `python3 -m pytest test/test_webgl_backend.py test/test_webgl_backend_browser.py -q -n0 -p no:cacheprovider -rf > <scratch>/36-02-01.log` and S02 through the driver with `WP36_ONLY=S02`; save the failing nodes and FAIL lines to `<scratch>/36-02-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/36-02-01.log` prints at least 8 (the qualified, by(), view and dashed cases in both modes, test_the_helper, the pixel test), and the solid-scatter guards and test_webgl_is_on_in_the_probe pass; `grep -c "Q3602-[12] FAIL" <scratch>/run_test_wp36_truth.log` prints 2 and `grep -c "Q3602-3 PASS"` prints 1; `test -s <scratch>/36-02-01-failure.txt`.]]></verify>
  <done>The drawn-row switch, the dashed-line rule and the WebGL pixel check existed as tests and were shown failing on the unmodified tree, with WebGL shown to be on in the probe.</done>
</task>

<task type="auto" id="36-02-02">
  <name>Count drawn rows and keep dashes on canvas</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `_dash_drawn_rows` and `_dash_dashes_on_canvas` (TR-36-02.1) after `_dash_overhangs`'s definition. Apply TR-36-02.2 at the saved backend lines and after `_dash_overhangs(fig, graph_opts)`; TR-36-02.3 at the served literals and the served function tuple; TR-36-02.4's two map entries. Run `python3 -m pytest test/test_webgl_backend.py test/test_html_output.py -k "webgl or backend or Backend" test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py test/test_csp.py -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[test_webgl_backend.py passes; the html_output webgl guards, TestTheServedAppCarriesEveryName, test_function_test_map.py and test_csp.py pass; `grep -c "_dash_dashes_on_canvas(fig)" dash_render.py` prints 3 (the definition, the saved call and the served literal); `grep -c "n_rows = len(self.df)" dash_render.py` prints 0.]]></verify>
  <done>Both renderers chose WebGL from the rows each figure draws and kept any figure with a dashed line on canvas.</done>
</task>

<task type="auto" id="36-02-03">
  <name>Pin pixels and parity, close DG-14</name>
  <files>dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[
    Run the release browser file (`python3 -m pytest test/test_webgl_backend_browser.py -q -n0 -p no:cacheprovider`; it needs Chrome: DASH_CHROME or the default path) and test/test_csp_browser.py -k "big or mixed_big" and test/test_export_svg.py::TestExport... -k webgl (the names at the base) to confirm the solid-scatter browser pins still read webgl. Add the CORPUS entry of the stubs after the last `line` entry of test_mode_parity.py and run `python3 -m pytest test/test_mode_parity.py -k "DG-14" -q -n0 -p no:cacheprovider` (a targeted run keeps the batch tier). Apply TR-36-02.6. Run S02 through the driver. Close the BUGS.md entry 33-01 opened for DG-14 (`grep -n 'WP-36 section 36-02 has not landed' BUGS.md`) in PD-4's closed form naming both modes and test_webgl_backend.py, Q3602-1..3 and the release pixel node; rewrite GAPS4.md's DG-14 Tracked line to `Closed in WP-36, BUGS.md "<title>", commit pending.`; delete DG-14 from `GAPS4_OPEN`; CHANGELOG `### Fixed in WP-36`: `- A dashed or dotted line in a graph of more than 10,000 rows drew broken up under WebGL, and a small graph of a large dataset used WebGL; such graphs are drawn on canvas, and the switch counts the rows a graph draws (WP-36, DG-14)`; append to TWOWAY_COVERAGE_AUDIT.md's Line styling row (:116, re-read) `[WP-36 DG-14: corrected -- a dashed or dotted line keeps its graph on canvas above 10,000 rows, and the WebGL switch counts the rows a graph draws]` (REVIEW R2-9). The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h): (1) run `awk -F'\t' '$1 == "DG-14" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the item's plain rows; a `DG-14 (documented)` or `DG-14 (residual)` row stays, A-10), rerun `python3 scripts/corpus/ledger.py` (33-05; no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py DG-14` (33-10) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion dict 33-10 names for it (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`, `ABBREV_DELIBERATE` in test/test_abbreviations.py for `ABBREV_KNOWN`, and beside 33-11..33-13's tables `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n); no ruling keeps a DG-14 difference on purpose (M8, Q34), so none is expected -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes, and stage each table file the step edited, by the path the printed row names; (3) run the corpus guard block (`WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do`, the driver of BRIEF "Running one cscript" written for test/test_wp33_truth.cscript with `<repo>` = `$WT`) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes), and put each Q3309-1 message and the fixture's `Fixture:` line in the commit body (a worse verdict this item's change does not explain is a regression: fix the code first, CLAUDE.md rule 2). Before committing, in `$WT`: `git pull --ff-only . main` (CLAUDE.md rule 4; at the batch base it prints `Already up to date.` -- if it refuses, stop and report to the orchestrator, never a merge commit on a section branch) and `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; HIGH or CRITICAL risk named in the hand-back). Grep the message for `claude|anthropic`, commit, grep again.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_webgl_backend.py test/test_webgl_backend_browser.py test/test_html_output.py test/test_function_test_map.py test/test_tracking_documents.py -q -p no:cacheprovider`'s last line reads `<n> passed in ...` with no `failed`, `error` or `skipped` (the browser file runs); the parity run's last line reads `<n> passed in ...` with no `failed` or `error`; `grep -c "Q3602-[1-3] PASS" <scratch>/run_test_wp36_truth.log` prints 3; `awk -F'\t' '$1 == "DG-14"' scripts/corpus/ledger.tsv | wc -l` prints 0, test/test_corpus_ledger.py passes, `python3 test/known_differences.py DG-14` prints no `<file>:<line>` row and the hygiene command it prints passes, and the S09 guard block ends with its pass line; `git log -1 --format=%s | grep -c "(WP-36 DG-14)"` prints 1; `grep -c "DG-14 Tracked:\*\* Closed in WP-36.*commit pending" GAPS4.md` prints 1.]]></verify>
  <done>DG-14 was closed: dashed lines drew on canvas and matched the canvas reference with WebGL on, small graphs of large data stayed on canvas, large solid scatters kept WebGL, the corpus ledger kept no plain DG-14 row, and the commit landed on wp36-s02.</done>
</task>

## Section completion criteria

- `_dash_drawn_rows` and `_dash_dashes_on_canvas` exist, mapped; the served app carries `_dash_dashes_on_canvas` and counts `len(g_df)`.
- test_webgl_backend.py and the release pixel test pass; the solid-scatter WebGL pins are untouched and green.
- The help states the rule; BUGS/GAPS4/CHANGELOG/GAPS4_OPEN updated in the one commit.
- No plain `DG-14` row is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table (`python3 test/known_differences.py DG-14` prints none); test/fixtures/corpus_ledger.json is regenerated from the ledger by `scripts/corpus/ledger.py`; test/test_corpus_ledger.py, the hygiene command and the S09 guard block pass; corpus_guard_truth.json is regenerated by its extract script if Q3309-1 reported any change for a guard example.

## Notes

- **Traps.** (1) `facet_view` for a linked graph is a `CDSView` whose `filter` may be rebuilt by `_register_view_filter` later; the count is read once at build, which is when the backend is fixed. (2) The browser test must not run with `--disable-gpu` alone: WebGL is then off and the test cannot fail (assert `canvas_view.webgl != null` on the solid page first). (3) Keep the IoU threshold at 0.95: canvas against canvas is 1.0, and [B]'s best WebGL dashed case is 0.86.
- **GitNexus and rule 4.** `impact` on `_make_figure_body`, `_generate_app_source_body` and `_dash_overhangs` before the first edit (36-02-01); `git pull --ff-only . main` (in `$WT`, BRIEF "Pull form") and `detect-changes --scope all` before the commit (36-02-03); HIGH, CRITICAL or UNKNOWN risk goes in the hand-back (REVIEW R2-8).
- **The corpus ledger and the known-differences tables (BRIEF, from WP-34 on).** 36-02-03 deletes DG-14's plain rows of scripts/corpus/ledger.tsv and regenerates test/fixtures/corpus_ledger.json with `scripts/corpus/ledger.py` (D-33-05.i), deletes every row `python3 test/known_differences.py DG-14` prints and runs the hygiene command it prints (D-33-10.h; no ruling keeps a DG-14 difference on purpose, so no deliberate-dict entry), and regenerates corpus_guard_truth.json with its extract script if Q3309-1 reports any change for a guard example (33-09).
- **Help paragraph owned (R3):** the new `{ul:WebGL.}` paragraph of Resource limits (TR-36-02.6); 40-02 later edits other Resource limits paragraphs and must keep it.
- **Merge rules touched:** R2 (one served tuple insertion, one literal edit, one literal added), R8 (one CORPUS entry), R12 (`_make_figure_body` and the served body: this section is batch 36.1's only editor), R14.
- **Commit-body line forms:** `Regression: test/test_webgl_backend.py::TestDashedLinesStayOnCanvas::test_lpattern_dash_on_20000_rows[std] -- failed at <base> with 'webgl' != 'canvas'`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` and `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` only when 36-02-03's ledger step changed them; `BUGS.md: "<title>" (closed)`; `GAPS4: DG-14 Tracked`; `TWOWAY_COVERAGE_AUDIT.md: Line styling row corrected`.
