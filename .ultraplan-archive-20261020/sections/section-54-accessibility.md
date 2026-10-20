# Section 54: Accessibility -- ARIA names, keyboard tabs, contrast, axe-core

> Part of: WP-31 · GAPS3 rows: K6 · Risk: yellow · Batch: 18 · Depends on: 48, 49 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U54

## Overview

**What is wrong today.** GAPS3 K6 (GAPS3.md:286): "Accessibility (one `aria-live` region, no alt text) and English-only interface." research/codebase-mechanics.md §8: "The only `role`/`aria` markup is `_DASH_STALE_STATUS_HTML` (:1905-1910). The served "Updating..." `Div` (:50608) has none." `_dash_kpi_card_html` (:22900-22957) writes `div.db-kpi-card` with no role; `_dash_filter_widget` (:34566) builds widgets with a `title` but no `aria-label`; figures have no accessible name (`<canvas>` carries nothing, the events layer is a `div tabIndex=0` with no role, research/bokeh-web.md §7); `Tabs` headers are `div tabIndex=0` with a click handler only, so Enter and Space do nothing (§7). No test measures colour contrast of the 26 shipped schemes.

**After this section** (DISCOVERY Q34, M19): every figure's host carries `role="img"` and an `aria-label` (the graph's title text, else a sentence from its plots); every filter widget, the reset button, the table toggle and the DataTable carry `aria-label`s; every KPI card Div carries `role="group"` and `aria-label` (its title); the `Tabs` host carries `role="tablist"` and a `document_ready` `CustomJS` adds keydown handlers (Enter, Space, ArrowLeft/Right, Home, End) to the tab headers; the served "Updating..." Div gets `role="status" aria-live="polite"`; a pytest checks WCAG AA contrast (4.5:1) of the text/background pairs of all 26 schemes with the formula from research §7; and a release-tier test injects axe-core 4.12.1 (fetched by the test from cdnjs into a scratch directory, never into the page) through `_CspProbe` and asserts zero violations on two rendered pages in each mode.

**Why one section.** One cross-cutting concern with one mechanism (`html_attributes`, research §7) across six model builders, one keyboard hook, two tests.

**Test order and commit rule.** One cycle, one commit `(WP-31 K6)`: 54-01 tests red; 54-02 attributes in both modes; 54-03 the keyboard hook, contrast test fixtures; 54-04 axe-core run, help, close, commit.

### Section decisions (binding on the executor)

- **D-54a. Names are derived, never invented.** A figure's name: `_dash_graph_text_plain(title)` when the graph has a `title()`, else `"<type> of <y> versus <x>"` for the first plot (`_dash_hover_layer_vars` order: y then x; a univariate plot `"histogram of <var>"`; paired coordinates `"pcspike of y1 x1 to y2 x2"`), followed by `", <n> more layers"` when the graph has more than one plot. Variable labels are not used (they can be long); names are capped at 120 characters (`_dash_display(text, 120)`).
- **D-54b. Attributes go on the host (`html_attributes`), nothing walks shadow roots.** research §7's caveat is accepted: axe treats a `role=img` host with a name as accessible. Inner-element ARIA is not added (M19 says "host `html_attributes`").
- **D-54c. Contrast pairs and threshold.** Per scheme: (`color text`, `color background`), (`color text`, `color plotregion`), (`color text`, `color legend`), (`color tick_label` if present else `color text`, `color plotregion`), (the KPI value colour = `color text`, `color legend`). AA 4.5:1 for every pair; a scheme that fails is listed in a `KNOWN_LOW_CONTRAST` dict with the measured ratio and the help documents it ("the dark scheme s1rcolor ...") -- the test fails on an undocumented failure and on a documented one that now passes (R10-style drift pin). The measurement at `6370ca4` is 54-01's job; the dict is filled from it, never guessed.
- **D-54d. axe-core only in the test.** `test/axe_fetch.py` downloads `https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.12.1/axe.min.js` into `<scratch>/axe/axe.min.js` once per session (sha256 pinned in the test: measured on the first fetch, compared with cdnjs's published SRI hash for `axe-core/4.12.1/axe.min.js` -- recorded in the test's comment -- and committed as a constant only when the two agree, REVIEW-4 R4-37), skips when offline or without Chrome (red under `DASH_STRICT=1` as the other Chrome tests are); the script is injected through `responsive_probe.admit_script` (saved page: its sha256 joins the policy of the TEST COPY) or `Runtime.evaluate` after load through `_CspProbe._eval` (served). Run `axe.run(document, {runOnly: ['wcag2a','wcag2aa','wcag21aa']})`; assert `violations == []` after filtering none (no allow-list; a Bokeh-internal violation is a finding to report, and a failing node's `html` goes into the message).
- **D-54e. Keyboard activation.** `_DASH_TABS_KEYS_JS` (document_ready CustomJS, args `{"tabs": [Tabs models]}`): for each Tabs view (`Bokeh.index.find_one(t)`), find the header elements (`view.shadow_el.querySelectorAll('.bk-tab')`), set `role="tab"`, `aria-selected`, `tabindex` (0 on the active, -1 otherwise, roving) and add a `keydown` listener: Enter/Space → `t.active = i`; ArrowRight/ArrowLeft → focus and activate the next/previous (wrapping); Home/End → first/last; on `t.change` update `aria-selected`/`tabindex`. The header class name `.bk-tab` is read from the installed bundle by `test_the_tab_header_class_exists_in_the_bundle` (A109 pattern) and listed in `_DASH_BOKEH_INTERNALS`.

## Risk: [yellow] -- attributes on many models, a shadow-DOM hook, a network-dependent release test

**Why.** Six builders change; the hook touches Bokeh's internal class names; axe needs a download.

**Risk factors.** (1) `html_attributes` must not break parity (`_layout_tree` records models, not attributes -- extend to record `html_attributes` so both modes must agree); (2) `.bk-tab` may change across Bokeh versions; (3) the download may fail in CI (S60) -- skip with a reason, not a failure; (4) S53 adds its own `document_ready` hook in the same batch.

**Mitigation.** (1) parity extension and `test_both_modes_carry_the_same_attributes`; (2) bundle pin and `_DASH_BOKEH_INTERNALS` entry; (3) `pytest.skip("axe-core not fetched: <reason>")` unless `DASH_STRICT=1`; (4) disjoint lines, merger order S53 then S54.

## Dependencies

- **Depends on: 48** (toggle/table attributes), **49** (MultiChoice, reset button attributes). **Blocks: none.**
- **Parallel batch: 18** with S53 (export/print) and S55 (served hygiene). S54 edits `_dash_header_models`, `_dash_filter_widget`, `_dash_filter_reset_button`, `_dash_data_table`, `_make_kpi_div`/served `_dash_kpi_card` call, `_dash_tab_panels`, the figure builder's attribute line and adds one hook; S53 edits `_dash_name_save`, its constants and its hook; S55 edits the served template's header/launcher/health. No shared function.

## Evidence

### No names anywhere

`grep -n "html_attributes" dash_render.py` prints nothing at `6370ca4`. `grep -n 'aria-' dash_render.py` prints only :1906 (`_DASH_STALE_STATUS_HTML`).

### Builders

- Figures: `_make_figure_body` (saved, `DashRenderer`) and the served `_dash_figure_for` (template :49474 region) both call `figure(...)` through the shared figure factory (grep `def _dash_new_figure\|= figure(` to find the one construction both use; if two, set the attribute in a shared `_dash_name_figure(fig, graph)` called from both).
- Filters: `_dash_filter_widget` (:34566) returns `(widget, sentinel)`; set `widget.html_attributes = {"aria-label": title_plain}` before returning (every branch).
- KPI: `_make_kpi_div` (:44248) wraps `_dash_kpi_card_html` in a `Div(..., disable_math=True, stylesheets=[...])`; the served `_dash_kpi_card` (template :48112) builds the Div.
- Tabs: `_dash_tab_panels` (:36015-36037) returns `Tabs(tabs=panels, sizing_mode="stretch_width")`.
- Header: `_dash_header_models` (:36433-36449) returns Divs for title and subtitle.
- Served cue: template :50608 `Div` "Updating...".

### Schemes

26 files `dash-*.scheme` at the repo root (`dash-economist.scheme` ... `dash-sttrans.scheme`); keys `color text` (:159 in dash-s2color.scheme), `color background` (:36), `color plotregion` (:37), `color legend` (:38). `SchemeParser` exposes `text_color` (used by `_dash_kpi_card_html`), `background_color`, and reads any key through its `get`/`color_of` (grep `def color\b\|def get_color` in `SchemeParser`).

### The harness

`_CspProbe` (test/test_csp_browser.py:183-276): `_eval`, `read(js)`, `in_task`, `wait_change`; `responsive_probe.admit_script(page_html, script_html)` (test/responsive_probe.py:142-183) hashes a probe script into the saved page's policy; `find_chrome()` (:123). Both files are `pytestmark = pytest.mark.release`.

### Existing tests that pin today's behaviour

- test/test_mode_parity.py `_layout_tree` -- extended, not flipped.
- test/test_label_sinks.py (every text sink) -- `aria-label` is a new sink: add the figure name and widget title there as `html_attributes` values (text through `html.escape`? NO: `html_attributes` values are set by BokehJS `setAttribute`, which needs no escaping; the test asserts the raw text reaches the attribute and a `<script>` text stays inert).

## User stories

- **US-54.1** As a screen-reader user I want every graph, filter and card named so that I can navigate the dashboard.
- **US-54.2** As a keyboard user I want to switch tabs with Enter, Space and the arrow keys.
- **US-54.3** As an author I want to know which shipped schemes meet AA contrast so that I can choose one for an accessible report.
- **US-54.4** As a maintainer I want an automated checker to catch regressions.

## Business requirements

- **BR-54.1** Every figure, filter widget, reset button, table toggle, table, KPI card and tab strip has an accessible name derived from its own text; both modes alike.
- **BR-54.2** Tabs respond to Enter/Space/Arrow/Home/End with the active tab and focus moving together.
- **BR-54.3** Each shipped scheme's text/background pairs are measured; failures are documented by name.
- **BR-54.4** axe-core reports no violation on the checked pages in either mode.

## Technical requirements

- **TR-54.1 `_dash_figure_name(graph, plots)`** (shared; after `_dash_hover_layer_vars`): D-54a. `_dash_name_figure(fig, graph)` sets `fig.html_attributes = {"role": "img", "aria-label": name}`; called in both figure paths.
- **TR-54.2 Widgets.** `_dash_filter_widget`: `w.html_attributes = {"aria-label": _dash_graph_text_plain(title)}` in every branch (through one `_dash_aria(w, text)` helper that merges into an existing dict). `_dash_filter_reset_button`: `{"aria-label": "Reset filters"}`. S48's `_dash_data_table`: toggle `{"aria-label": "Show or hide the data table", "aria-expanded": "false"|"true"}` (the toggle CustomJS also writes `cb_obj.html_attributes = {...aria-expanded}`), table `{"role": "region", "aria-label": "Data table of <figure name>"}`.
- **TR-54.3 KPI cards.** `_make_kpi_div` and the served `_dash_kpi_card`: `Div(..., html_attributes={"role": "group", "aria-label": title_plain})`; the Div is rebuilt text-wise on moves (`.text` only), so the attributes persist.
- **TR-54.4 Tabs and header.** `_dash_tab_panels`: `Tabs(..., html_attributes={"role": "tablist", "aria-label": "Dashboard tabs"})`. `_dash_header_models`: the title Div `{"role": "heading", "aria-level": "1"}`, subtitle `{"role": "doc-subtitle"}`. Served cue (:50608): `html_attributes={"role": "status", "aria-live": "polite"}`.
- **TR-54.5 Hook.** `_DASH_TABS_KEYS_JS` (D-54e) after `_DASH_STALE_STATUS_HTML`; `_dash_tabs_keys_hook(tabs_models) -> CustomJS|None` (shared); registered on `document_ready` beside S53's hook in both modes. `_DASH_BOKEH_INTERNALS` gains `(".bk-tab header class and Tabs.active", "_DASH_TABS_KEYS_JS", "test/test_accessibility.py::TestTheBundle::test_the_tab_header_class_exists_in_the_bundle")`.
- **TR-54.6 Contrast test.** `test/test_scheme_contrast.py`: `rel_lum`/`contrast` per research §7 (verified: black/white 21.0, #777/#fff 4.478); parametrised over the 26 schemes × D-54c's pairs through `SchemeParser`; `KNOWN_LOW_CONTRAST = {("<scheme>", "<pair>"): <ratio measured>}` filled in 54-01 (measured with the test's own `--collect`-free run, printed and copied); the help's Schemes paragraph names them.
- **TR-54.7 axe test.** `test/axe_fetch.py` (D-54d) and `test/test_accessibility_axe.py` (`pytestmark = pytest.mark.release`): pages = `_standalone_page` of two specs (a scatter with a dropdown filter, a KPI and tabs; a histogram with a `table` and `type(multi)`) and the served documents of the same through test_server_serves' `_Served`; inject, `await axe.run(...)`, read `JSON.stringify(result.violations)` via `probe.read`, assert `[]` with each violation's `id`, `impact` and first node's `html` in the message. **The example pages (index G3; DECISIONS A30, REVIEW-4 R4-13):** the same file gains `TestAxeExamples::test_example_pages_have_no_violation[html]`, parametrised over the HTML files `make gate` builds from `examples/*.do` (`sorted(glob('examples/*.html'))` read at collection; the class is skipped with the reason `no examples/*.html built` when the glob is empty, so `make test` never needs them), selectable with `-k examples`; S61-04 runs `DASH_TEST_TIER=release python3 -m pytest test/test_accessibility_axe.py -k examples` after `make gate` has built the pages, and G3's wording ("axe-core reports 0 violations on the example pages") stands.
- **TR-54.8 Parity.** `_layout_tree` records `html_attributes` for every model it lists; `test_both_modes_carry_the_same_attributes` in test_accessibility.py renders the two specs in both modes and compares the attribute dicts by model kind and order.
- **TR-54.9 Maps and copy lists.** function_test_map: `_dash_figure_name`, `_dash_name_figure`, `_dash_aria`, `_dash_tabs_keys_hook`; copy list after `_dash_reference_lines`; constant after `_DASH_STALE_STATUS_HTML`'s entry.
- **TR-54.10 Help.** dash.sthlp: a new `{title:Accessibility}` paragraph after Exporting (names, keyboard tabs, the contrast list, the checker), owned by S54 (R3).

## Boundaries

- No export, print (S53), served env (S55) edits.
- No inner-element ARIA, no shadow-root walking except the tabs hook (D-54b, D-54e).
- No localisation (K6's "English-only" is a scope decision, M1).
- No scheme file change (contrast failures are documented, M7/M17).

## Stata truth

None. Truth block `* ==== S54 K6: accessibility ====`: `U54-1` a built page's JSON holds `"role":"img"` once per graph and `"aria-label"` on every filter widget (python: block over the saved HTML); `U54-2` a KPI page holds `"role":"group"`; `U54-3` a tabs page holds `"role":"tablist"` and the keys hook (`cert_file_has ... needle("keydown")`).

## TDD test stubs

Regression (red at 6370ca4), file `test/test_accessibility.py`:
- `TestFigureNames::test_role_img_and_title_name_both_modes`, `::test_name_from_plots_without_a_title`, `::test_capped_at_120`, `::test_pc_and_univariate_forms`.
- `TestWidgetNames::test_every_filter_type_has_an_aria_label`, `::test_reset_table_toggle_and_table`.
- `TestKpiCards::test_role_group_and_name_both_modes`, `::test_survives_a_text_rebuild`.
- `TestTabsAndHeader::test_tablist_heading_subtitle_status`, `::test_the_keys_hook_is_registered_once_both_modes`, `::test_the_hook_code_is_fixed_text`.
- `TestTheBundle::test_the_tab_header_class_exists_in_the_bundle`.
- `test_both_modes_carry_the_same_attributes` (TR-54.8).
- `test/test_scheme_contrast.py::TestAA::test_pair[scheme-pair]`, `::test_the_known_list_is_current` (fails when a listed pair now passes), `::test_the_formula_is_wcag` (the three verified ratios).
- `test/test_accessibility_axe.py::TestAxe::test_saved_pages_have_no_violation[spec]`, `::test_served_pages_have_no_violation[spec]`, `::test_the_bundle_hash_is_pinned` (release; skip without Chrome or network, red under DASH_STRICT=1 as its siblings); `::TestAxeExamples::test_example_pages_have_no_violation[html]` (release; skipped until `make gate` has built `examples/*.html`; run by S61-04, TR-54.7).
- Release (Chrome): `test_accessibility.py::TestKeyboardInChrome::test_arrow_and_enter_switch_tabs` through `_CspProbe` (dispatch `KeyboardEvent`s on the focused header, read `tabs.active`).

cscript: U54-1..U54-3. Flips: none expected (attributes are new); test_label_sinks.py gains the new sink (addition).

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| names and roles | pytest | none | yes |
| keys hook present; keys work | pytest; Chrome (release) | none | yes; saved |
| contrast | pytest over 26 schemes | none | -- |
| axe-core | Chrome (release) | axe.min.js in scratch | yes |
| axe-core on the example pages (G3) | Chrome (release), `-k examples`, run by S61-04 after `make gate` | examples/*.html | saved |
| parity of attributes | pytest | none | yes |
| page markers | cscript U54-1..3 | none | saved |

**AC-54.1** every stub green (release ones green or skipped with a reason); **AC-54.2** U54-1..3 pass; **AC-54.3** `KNOWN_LOW_CONTRAST` matches the help; **AC-54.4** test_csp.py, test_label_sinks.py, test_bokeh_internals.py green.

## Tasks

**Commit boundary.** 54-01..54-04 form the one commit `Name every figure, widget, card and tab for assistive technology, add keyboard tabs and contrast and axe checks (WP-31 K6)`.

<task type="auto" id="54-01">
  <name>Write the failing accessibility tests and measure contrast</name>
  <files>test/test_accessibility.py, test/test_scheme_contrast.py, test/test_wp31_truth.cscript</files>
  <action><![CDATA[Create test/test_accessibility.py and test/test_scheme_contrast.py with the stubs above (the contrast file first with an EMPTY KNOWN_LOW_CONTRAST; run it, copy every failing (scheme, pair, ratio) into the dict rounded to 3 decimals). Append the S54 truth block (U54-1..U54-3). Run `python3 -m pytest test/test_accessibility.py -q -m "not release"` on the unmodified tree; save to <scratch>/54-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[The test_accessibility.py tail prints failures only (AttributeError on _dash_figure_name); python3 -m pytest test/test_scheme_contrast.py -q passes once the dict is filled; test -s <scratch>/54-01-failure.txt]]></verify>
  <done>The regression tests exist and fail at 6370ca4; the contrast of the 26 schemes is measured and pinned.</done>
</task>

<task type="auto" id="54-02">
  <name>Set the host attributes in both modes</name>
  <files>dash_render.py, test/function_test_map.py, test/test_mode_parity.py</files>
  <action><![CDATA[Apply TR-54.1..TR-54.4 and TR-54.8 (the _layout_tree attribute record) and the copy-list entries; the served cue at :50608. Run test/test_accessibility.py -k "Names or Cards or TabsAndHeader or same_attributes" -m "not release", test/test_label_sinks.py, test/test_statistical_helpers.py -k CarriesEveryName, DASH_TEST_TIER=batch python3 -m pytest test/test_mode_parity.py -k "scatter and dropdown" (one existing entry, to prove the tree extension holds).]]></action>
  <verify><![CDATA[python3 -m pytest test/test_accessibility.py -q -m "not release" -k "not Bundle and not hook" prints all passed; test/test_label_sinks.py passes]]></verify>
  <done>Every figure, widget, card, tab strip and header carries its role and name in both modes.</done>
</task>

<task type="auto" id="54-03">
  <name>Add the keyboard hook and pin the bundle</name>
  <files>dash_render.py, test/test_bokeh_internals.py, dash.sthlp</files>
  <action><![CDATA[Apply TR-54.5 (_DASH_TABS_KEYS_JS, _dash_tabs_keys_hook registered on document_ready in both modes beside S53's hook, the _DASH_BOKEH_INTERNALS entry) and TR-54.10's help paragraph including the KNOWN_LOW_CONTRAST names. Run test/test_accessibility.py -k "hook or Bundle", test/test_bokeh_internals.py, test/test_csp.py, test/test_help_conformance.py, and the S54 truth block driver through scripts/stata_slot.sh.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_accessibility.py test/test_bokeh_internals.py test/test_csp.py -q -m "not release" passes; the cscript log shows U54-1..U54-3 PASS]]></verify>
  <done>Tabs are keyboard-operable through a sealed CustomJS, pinned to the bundle's header class.</done>
</task>

<task type="auto" id="54-04">
  <name>Run axe-core, close and commit K6</name>
  <files>test/axe_fetch.py, test/test_accessibility_axe.py, BUGS.md</files>
  <action><![CDATA[Create test/axe_fetch.py and test/test_accessibility_axe.py per TR-54.7 (the sha256 constant measured on the first fetch and compared with cdnjs's published SRI hash before it is committed, R4-37; the download lands in the scratch directory, is read with -I semantics (no import from it), and is injected as text; the TestAxeExamples parametrisation over examples/*.html, skipped when none is built). Run DASH_TEST_TIER=release python3 -m pytest test/test_accessibility_axe.py test/test_accessibility.py -m release -q; fix any violation axe reports in dash's own markup (never by allow-listing); a Bokeh-internal violation is recorded in the commit body and BUGS.md as a residual. Replace the <!-- WP-31 K6 --> marker under "### Fixed in WP-31" with "Every figure, filter, KPI card and tab strip carries an accessible name and role, tabs work from the keyboard, scheme contrast is measured and the pages pass an automated checker (WP-31, K6)". Close BUGS.md "Accessibility", rewrite the GAPS3 K6 Tracked line to the Closed form with `commit pending` (DECISIONS A11; the merger's step k.3b writes the sha; no amend). Commit on wp31-s54 with the body forms.]]></action>
  <verify><![CDATA[git log -1 --format=%s ends "(WP-31 K6)"; git log -1 --format=%B | grep -ci "claude\|anthropic" prints 0; python3 -m pytest test/test_tracking_documents.py test/test_fixtures_are_committed.py -q passes]]></verify>
  <done>K6 is committed with the checker in the release tier and the documents updated.</done>
</task>

## Section completion criteria

- `html_attributes` present on every listed model in both modes and equal across modes; the tabs hook registered once per page; contrast measured for 26 schemes with failures named in the help; axe-core reports zero violations (or a documented Bokeh-internal residual); one commit `(WP-31 K6)`.

## Notes

- **CSP (M11).** The hook is a `CustomJS`; axe is injected only into the TEST COPY of the page (`admit_script`) or through DevTools; the shipped page never names cdnjs.
- **Downloads.** The axe fetch is a test-time download into the scratch directory, pinned by sha256; nothing from it is imported or executed by Python (it is text sent to Chrome).
- **Security.** Attribute values are model properties set by BokehJS `setAttribute` (inert); names are capped at 120 characters.
- **Copy lists (R2):** `_DASH_TABS_KEYS_JS` after `_DASH_STALE_STATUS_HTML`'s entry (after S48/S49/S53's constants); functions after `_dash_reference_lines`.
- **Commit body forms:** `Regression: test/test_accessibility.py::TestFigureNames::test_role_img_and_title_name_both_modes -- failed at 6370ca4 with AssertionError: html_attributes == {}`; `BUGS.md: "Accessibility" (closed)`; `GAPS3: K6 Tracked`.
- **Decisions for ratification:** the name rule (D-54a); host-only ARIA (D-54b); the contrast pairs and the documented-failure list (D-54c); test-time axe download (D-54d). **Decided:** axe over the example pages through TR-54.7's parametrisation, run by S61-04 (A30, R4-13); the SRI comparison (R4-37).
- **Tracked line (A11):** `commit pending`; no amend. **A14:** 54-01 appends the one K6 block. **Files (A13):** `<files>` lists primary files; the tracking documents and flipped tests are implied.
