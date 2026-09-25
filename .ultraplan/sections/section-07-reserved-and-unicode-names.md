# Section 07: Reserved and Unicode names (G1, G5)

> Part of: WP-28 · Gaps: G1, G5 · Risk: yellow · Batch: 1 · Depends on: none · Blocks: 14, 17, 19 · Tasks: 15, 2 commits


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **1** · Depends on **none** · Blocks **14, 17, 19** · Risk **yellow** · Commits: two commits: G1 → CHANGELOG `Changed behaviour`; G5 → `Fixed in WP-28`

- D7: the test-writing task was split one task per file (07-01, 07-02, 07-03 for G1; 07-11, 07-12 for G5) and the flip tasks re-partitioned (07-05 to 07-08, the last holding the two one-line pins) so that no task edits a hidden fourth file, as feasibility.md proposes.
- D11 (`sections/BRIEF.md` "Certification scripts", `sections/index.md` rule R1): no new certification script. QS-06 of `test/test_qualifier_in_stata.cscript` is extended for the `__dash` refusal and UN-01..UN-03 join `test/test_statistical_options.cscript`; `test/run_all_cscripts.do` and the hygiene pins of `test/test_cscript_hygiene.py` are not edited by this section.
- The guard test's grep must not match the section's own prefix table.
- D1: G1's failing tests are written before G1's fix and G5's before G5's fix (after the G1 commit), so the full suite is green at each of the two commits.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

Two gaps about which variable names dash reads as the user's data. **G1** (S1): dash.sthlp:166-171 reserves only names beginning `__dashq`, so every other valid Stata name should be read as data. It is not: `_ROW_ID_COLUMN = "__dash_row__"` (dash_render.py:2008) is written into every graph source *after* the user's columns (`_make_source`, 21416), and GAPS2 measured "a y holding 100..140 was drawn as 0..4 with no note". Four more families of internal columns share the user's namespace under names no rule reserves: `__mlabel__{var}` and `__mlabel__{var}__fmt_{hex}` (6750, 6965: a user column of that name is *read as the label text*), `__mlabel_values__`/`__mlabel_x__`/`__mlabel_y__` and `__dash_pc_row__` (10832-10890, 11544), `__{ptype}_label__` (11345) and the jitter columns `_x_jit`/`_y_jit` (5498-5499: overwritten in the jittered copy). The JS twin hard-codes `const ROW_ID = "__dash_row__"` (14219) where the brush script fills it from the constant (23499).

**G5** (S3): Stata 14+ names may hold Unicode letters, and dash accepts them in most places (the by() check at dash_parse.mata:2916 uses `\p{L}`; `test_statistical_options.cscript:482` uses `[aw=größe]`). But `_dash_is_name` (dash_parse.mata:827-840) is ASCII-only, so `filter(größe)` is refused "not a valid Stata variable name", r(198); the KPI pattern at dash.ado:6094-6097 refuses `dash kpi mean(größe)` with "syntax is stat(varname)"; and — bigger than GAPS2 says (research C §4) — the renderer's `_DASH_VARNAME_RE` (19207) is ASCII-only too, so a Unicode `by()` is drawn without panels with a warning in both modes, a Unicode `hover()` field is left out of the tooltip, a Unicode `filter()` builds no widget, and `_apply_colorvar` (6365) silently draws no colours.

After this section: (1) every column dash makes up is named under one prefix, `__dash`; (2) a user variable whose name begins `__dash` is refused with r(110) on every route with data, by dash.ado and by both renderers, and every other Stata name — `__mlabel__y`, `_x_jit`, `x`, `top` — is read as the user's data; (3) a Unicode variable name works in `filter()`, `dash kpi`, `by()`, `hover()` and `colorvar()`, in both modes, and a name that is not a Stata name (markup, a brace, a quote, 33 characters) is still refused at every one of those sites. Both gaps are one rule — *which names are the user's* — enforced at the same three places (dash.ado, dash_parse.mata, the two renderers), which is why they share a section.

**Test order (CLAUDE.md rule 7) and commit rule (D1).** Tasks 07-01 to 07-03 write G1's regression tests (two pytest files and the QS-06 cases), run them against the unmodified tree and save the failure text to the scratch directory -- nothing is committed (a red tree is never committed, rule 4); 07-04 to 07-09 turn them green, flip the pinned tests and add the refusal; 07-10 closes the G1 entry and makes the G1 commit, subject ending `(GAPS2 G1)`, body opening with the saved failure text (S01 TR-01.9). G5's regression tests are written only then -- 07-11 and 07-12, run against the tree the G1 commit leaves, which is unmodified at every G5 site (`_dash_is_name`, the KPI pattern, `_DASH_VARNAME_RE` and its six sites are as at 91d97be) -- so that the full suite is green when G1 is committed; 07-13 and 07-14 turn them green; 07-15 closes the G5 entry and makes the G5 commit, subject ending `(GAPS2 G5)`. The failing tests of each gap land in that gap's commit, never alone.

## Risk: [yellow] — a mechanical rename across ~16 pytest files, a widened refusal that newly rejects real names, and a name predicate that is a security surface

- **Why.** The renames touch nothing statistical, but ~16 test files pin the old literals (listed under Evidence) and every one must be flipped, not deleted, in the same commit. The `__dash` refusal is a **changed behaviour**: a dataset holding a variable named `__dash_anything` built yesterday and is refused today (the release's top-level `### Changed behaviour (may need your do-files changed)` list, D2). The renderer's name predicate guards tooltip fields against `}`/`{safe}` injection (19925-19932); replacing an ASCII regex with a Unicode-aware check must not admit a brace, quote, blank or dollar sign.
- **Risk factors.** (a) A literal missed in the rename leaves one internal column outside the prefix and the guard test is the only thing that catches it. (b) `_DASH_VARNAME_RE` is in the served constants copy list (24372); deleting it without removing the entry, or using `_dash_is_stata_name` in a copied function without adding it to the functions copy list (after `"_dash_parse_filter_raw"`, 24687), is a NameError on the served page at draw time, not at build time. (c) `_dash_is_stata_name` also caps names at 32 characters; a hand-written spec with a 33-character column in `hover()` is newly left out (with the note). Stata cannot make such a name.
- **Mitigation.** A guard test scans `dash_render.py`'s string constants for anything that looks like a column outside the prefix; `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` and `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` catch (b); adversarial cases at every G5 site pin (c).

## Dependencies

- Depends on: none — every edit is in a region no other batch-1 section touches (`_make_source`, the mlabel/pc/rscatter/jitter column names, `_dash_take_qual_columns`, `_DASH_VARNAME_RE`'s five sites, dash.ado's `_dash_qual_gen` and the KPI pattern, dash_parse.mata's filter refusal).
- Blocks: section 14 (`_dash_is_stata_name` by this name, D10; the `__dash_hover_{var}` naming rule of TR-07.3), section 17 (the `ROW_ID` fill and the `__dash_mlabel_*` names), section 19 (closeout).
- Parallel batch: 1. Can run with every other batch-1 section. **Batch-1 merge order (`sections/index.md` step 1): S01, S03, S02, S06, S07, S08, S09, S10** — S03 lands before this section (both edit `test/test_saved_filter_layers.py` and `test/test_statistical_helpers.py`'s neighbourhood; S03 deletes 85-214 of the former, this section flips 475-478 and 999-1035); this section lands before S08, which factors `_dash_filter_excludes` out of the text of `_dash_filter_refusal` as this section leaves it (TR-07.6 changes 3453 and 3457 of that function). **Shared edits to reconcile at the merge (R2, R3):** the two served copy lists in `dash_render.py` (constants beside `_ROW_ID_COLUMN` 24340 and `_DASH_QUAL_PREFIX` 24390, `_DASH_VARNAME_RE` deleted at 24372; functions after `"_dash_parse_filter_raw"` 24687), `test/program_coverage_map.py` (alphabetical place), `test/test_qualifier_in_stata.cscript` and `test/test_statistical_options.cscript` (cases appended to existing scripts; no runner block and no hygiene pin, D11), `BUGS.md` (appended at the end), `CHANGELOG.md` (the G1 and G5 markers only), `dash.sthlp` (166-171, 1108-1109, 1194-1197).
- Section 14 (B1/G16) will add a hover text column; it must name it `__dash_hover_{var}` (TR-07.3 fixes the naming rule it follows).

## Evidence

### G1 — the internal columns and where each collides (research C §1.1, checked at `91d97be`)

| Name today | Where | Collision | Name after this section |
|---|---|---|---|
| `__dash_row__` (`_ROW_ID_COLUMN`) | 2008; written at `_make_source` 21416 | overwrites a user column | **kept**: `__dash_row__` |
| `__dash_pc_row__` | 10838, 10849 | overwrites in the pc `clean` frame | **kept**: `__dash_pc_row__` |
| `__mlabel__{var}` | 6750 | a user column is read as label text | `__dash_mlabel_{var}` |
| `__mlabel__{var}__fmt_{hex}` | 6965 | same | `__dash_mlabel_{var}_fmt_{hex}` |
| `__mlabel_values__`, `__mlabel_x__`, `__mlabel_y__` | 10832-10890 (pc), 11544-11565 (rscatter) | overwritten in `clean` | `__dash_mlabel_values`, `__dash_mlabel_x`, `__dash_mlabel_y` |
| `__{ptype}_label__` | 11345 | none (literal source) — renamed for the one rule | `__dash_{ptype}_label` |
| `_x_jit`, `_y_jit` (+ `_2`, `_3` … in the linked variant 5556-5566) | 5498-5500; `_dash_keep_jitter` 18246 | overwritten in the jittered copy | `__dash_xjit`, `__dash_yjit` (+ `_2`, …) |
| `__dashfix<12 hex>` strL | 1296-1301, made in the user's data by `_dash_write_stata_data` | none (dropped after reading) | kept; already under the prefix |
| derived glyph fields `x`, `y`, `x0`, `y0`, `x1`, `y1`, `top`, `left`, `right`, `lo`, `hi`, `count`, `density` | rebuilt sources; `_carry_cols` (5573-5613) never overwrites them | `hover()`/`mlabel()` on a user variable of that name read the derived value | **residual** (recorded, not fixed) |

`_make_source`, 21411-21417:

```python
21411        data_dict = {v: (frame[v].to_numpy()
21412                         if pd.api.types.is_datetime64_any_dtype(frame[v])
21413                         else frame[v].tolist())
21414                     for v in available}
21415        # The row's position in the primary frame, so the filter callback can
21416        # mask this source by identity however short or reordered it is.
21417        data_dict[_ROW_ID_COLUMN] = self._row_ids_for(frame)
```

The JS literal, 14219, inside `_FILTER_JS` (assembled at 14177 as `_DASH_FILTER_MASK_JS + """…"""`, used as `code=_FILTER_JS` at 15083, 15141, 15200):

```js
14219 const ROW_ID = "__dash_row__";
```

and the brush script that already fills it in, 23498-23502:

```python
23498        code = (
23499            'const ROW_ID = "%s";\n' % _ROW_ID_COLUMN
23500            + "const kpi_config = JSON.parse(kpi_config_json);\n"
```

The Stata refusal, `_dash_qual_gen`, dash.ado:4255-4261 (called at 5943 on the one-line route and 6893 in `_dash_prepare_spec`, i.e. `dash build`, `build, server`, `serve`; both calls sit in the branch that has data, so a dashboard of literal plots alone never runs it):

```stata
4255    capture unab _dq_clash : __dashq*
4256    if _rc == 0 {
4257        local _dq_first : word 1 of `_dq_clash'
4258        display as error "`cmdname': variable `_dq_first' is named with the prefix __dashq, which is reserved for the qualifier columns dash exports."
4259        display as error "      Rename it first, for example: rename `_dq_first' newname"
4260        exit 110
4261    }
```

The renderer's copy, `_dash_take_qual_columns` 20319-20360 (called at 21180 in `_load_data`, before `_make_source` adds the row id, and by the generated app's loader, template line 25742), refusing at 20334-20342 only the qualifier prefix:

```python
20277 _DASH_QUAL_PREFIX = "__dashq"
20279 _DASH_QUAL_NAME_RE = re.compile(r"__dashq[1-9][0-9]{0,4}\Z")
...
20334    reserved = [c for c in cols if c.startswith(_DASH_QUAL_PREFIX)]
20335    for c in reserved:
20336        if c not in names:
20337            raise ValueError(
20338                "dash: the data hold a column named %r; names beginning "
20339                "with %s are reserved for the qualifier columns dash "
20340                "exports." % (c[:40], _DASH_QUAL_PREFIX))
```

and the served builder's early trigger, 25000-25003: `if _dash_qual_cols_named(self.spec) or (_DASH_QUAL_PREFIX in self._raw_data_str): self._frame()`.

Layout and model keys holding `__` (`__missing__` 6475-6580, `__all__` 13986/17581, `__tabs__` and `__fw_<i>__` 22575-22681, `<name>__by__<i>`) are not columns; `_dash_reserved_name` (1547) already refuses a registered name holding `__`. They are the guard test's allowlist.

**Stata rule.** r(110) "___ already defined" ([P] error, research D §12): the code dash already uses for the `__dashq` clash. The help paragraph is dash.sthlp:166-171 ("names beginning with {cmd:__dashq} are reserved, and data holding such a variable are refused with {cmd:r(110)}").

### G5 — the ASCII-only sites

dash_parse.mata:827-840 (`_dash_is_name`, also validating layout names at 891 and option words at 4030/4123 — **do not change it**) and its filter caller at 3452-3461:

```mata
3452        v     = items[1]
3453        if (!_dash_is_name(v)) {
3454            // Every character a name cannot hold, and at most 40 of them:
3455            // this text is by definition not a variable name, and is shown.
3456            return("filter() names '" +
3457                   ustrregexra(usubstr(v, 1, 40), "[^A-Za-z0-9_.\-]", "?") +
3458                   "', which is not a valid Stata variable name.")
3459        }
```

The by() rule that is already right, 2914-2918: `if (!ustrregexm(w[j], "^[\p{L}_][\p{L}\p{N}_]*$") | ustrlen(w[j]) > 32)`.

dash.ado:6094-6100, the KPI pattern (Mata's `regexm`, read by value for the JSE-58 reason in the comment above it):

```stata
6094    mata: st_local("_kst_ok", strofreal(regexm(st_local("statspec"), ///
6095        "^([a-zA-Z0-9.]+)\(([a-zA-Z_][a-zA-Z0-9_]*)\)$"))); ///
6096        st_local("stat", st_local("_kst_ok") == "1" ? regexs(1) : ""); ///
6097        st_local("kpi_var", st_local("_kst_ok") == "1" ? regexs(2) : "")
6098    if !`_kst_ok' {
6099        display as error "dash kpi: syntax is stat(varname), e.g. mean(mpg)."
6100        exit(198)
```

then `confirm variable `kpi_var'` (6142) and the numeric check (6147-6153, r(109)). Graph names (5617/5639) and KPI names (6172/6184) stay ASCII on purpose: they become global macro names (`dash_json_<name>`, `dash_kpi_<name>__<field>`).

dash_render.py: `_DASH_VARNAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")` (19207), used at 15513 (`_dash_parse_by`: "the graph is drawn without panels"), 19340 (filter variable: "is not a valid variable name; no widget was built"), 19362 (exclude() names), 19932 (hover field: "is not a plain name; leaving it out of the tooltip"), 20022 (`_drawn_field`); the inline copy in `_apply_colorvar` 6364-6366 (`if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", varname): return`); and the Unicode-aware check that already exists, 1183-1190:

```python
1183 def _dash_is_stata_name(name):
...
1189     return (isinstance(name, str) and 0 < len(name) <= 32
1190             and name.isidentifier())
```

`str.isidentifier()` admits Unicode letters and digits and the underscore and nothing else — no brace, quote, blank, dollar sign or backtick — which is exactly the property the hover site relies on. `_DASH_VARNAME_RE` is in the served constants list (24372); `_dash_is_stata_name` is not in the functions list (24466-24687, whose last entry today is `"_dash_parse_filter_raw"` at 24687).

**Stata rule.** A variable name is 1-32 characters of letters (Unicode included), digits and underscores, not starting with a digit ([U] 11.3 Naming conventions; the rule dash_parse.mata:2916 already writes as `^[\p{L}_][\p{L}\p{N}_]*$` with `ustrlen(...) <= 32`).

### Fixtures on disk

None are used. Truth is Stata's own r(110) and `summarize`'s `r(mean)`, measured at run time in the cscripts.

### Existing tests that pin today's behaviour (flip, never delete)

G1 renames — each names an old literal and must be edited to the new name in the G1 commit:

- `test/test_jitter.py::TestMapScatterJitter::test_jitter_uses_jit_columns_as_xy` (57-58), `::test_jitter_cds_retains_original_columns` (76-77), `::test_deterministic_with_jseed` (87-88), `::test_different_jseed_produces_different_jitter` (99-100), `::test_extreme_jitter_value_no_crash` (133); `TestJitterOnOtherPlots::test_jitter_on_dot_plot` (148); `TestJitterNotOnLinePlot::test_line_plot_ignores_jitter` (186); `TestJitterHtmlIntegration::test_html_contains_jit_column` (239), `::test_html_no_jit_column_without_jitter` (244); `TestEverySeedSiteReadsBothSpellings::test_the_served_app_reads_jitterseed` (497-498).
- `test/test_html_verification.py::TestGlyphCount::test_scatter_with_jitter_has_jit_column` (294), `::test_scatter_no_jitter_has_no_jit_column` (300), `::test_jit_column_differs_from_original` (313-332).
- `test/test_option_validation.py::TestABadValueNoLongerAbortsTheRender::test_negative_jitterseed` (734).
- `test/test_date_range.py::TestAComputedLayerIsDrawnOnTheDateAxis::test_a_jittered_date_with_a_missing_one_stays_on_the_axis` (805-807).
- `test/test_saved_filter_layers.py::TestAJitteredScatterFollowsAMove::test_the_kept_points_stay_where_they_were` (475-478); `TestALinkedJitteredScatter::test_the_column_helper` (1025-1035: `("_x_jit", "_y_jit")` and `("_x_jit_2", "_y_jit_2")`); `TestALinkedJitteredScatter::test_a_variable_named_like_the_jitter_column_is_kept` (999-1008) **keeps its meaning** — a user variable `_x_jit` is drawn with its own values — and needs only its comment updated: the glyph now draws `__dash_xjit`.
- `test/test_server.py::TestServerFilterPreservesDerivedColumns::test_filter_callback_updates_all_layer_sources` (7461-7477: `__mlabel__foreign`), `::test_a_derived_column_keeps_each_kept_rows_value_after_a_move` (7547), `::test_make_document_with_filter_does_not_raise` (7596), `::test_filter_callback_preserves_derived_column_length` (7652).
- `test/test_served_filter_move.py` module fixture at 216 (`__mlabel__rep`), `TestTheUnlinkedRefresh::test_it_writes_the_rows_of_its_own_that_the_move_keeps` (232), `::test_the_rule_it_replaced_differs_on_this_source` (272-278), `TestAdversarialFilterMoves::test_a_move_over_many_rows_is_linear` (703-710, `__mlabel__x`).
- `test/test_server_facets.py::TestEveryTypeFacetsTheSameWayInBothModes::test_marker_labels_and_hover_reach_every_panel` (268).
- `test/test_twoway_option_parity.py::TestTheConnectingLineOptions::test_mlabformat_on_a_date_variable_is_named_and_the_dates_kept` (633), `::test_the_formatted_column_is_named_by_variable_and_format` (641).
- `test/test_marker_label_parity.py::TestAdversarialMarkerLabels::test_a_huge_label_set_is_read_at_once` (939).
- `test/test_qualifier_columns.py::TestTakingTheColumnsOut::test_a_reserved_column_the_spec_does_not_name_is_refused` matches `"reserved"` — keep that word in the widened message; it does not flip.
- `test/test_kpi_values.py::TestQualifiedKpiUnderFiltering::test_an_unqualified_kpi_carries_no_row_list` (727) and `test/test_kpi_brush.py::TestTheShippedBrushJsActuallyComputes::test_the_help_still_claims_standalone_brush_support` (260) write `const ROW_ID = "__dash_row__"` by hand; the name is kept, so they do not flip. Switch them to `dr._ROW_ID_COLUMN` if convenient.
- `test/test_qualifier_in_stata.cscript` QS-06 (491-519): `rename mpg __dashqz` is still r(110) and `cert_log_has ... needle("reserved")` still holds — the case is extended, not flipped.

G5 — nothing pins the ASCII-only behaviour by a Unicode example (`grep -nP '[^\x00-\x7F]' test/*.py` finds no Unicode variable name in a by/filter/hover/colorvar test). The injection tests that must keep passing unchanged: `test/test_help_claims_1.py` (`_BAD = "x}<img src=x onerror=alert(1)>"`, 687; `_NOTE` 748), `test/test_security_surface.py` (957, `<script>alert(1)</script>` as a filter variable), `test/test_filter_label.py` (252), `test/test_mode_parity.py` (2869).

## User stories

- **US-07.1** As the Stata user pasting twoway syntax, I want a variable of mine named `__mlabel__y`, `_x_jit` or `__dash_row__` never to be silently replaced by a column dash makes up, so that the page draws my numbers or tells me it cannot.
- **US-07.2** As the Stata user, I want a variable whose name dash reserves to be refused before anything is exported, with Stata's own code and a message naming the prefix and how to rename it, so that I learn it once and at once.
- **US-07.3** As the Stata user with Unicode variable names, I want `filter(größe)`, `dash kpi mean(größe)`, `by(größe)`, `hover(größe)` and `colorvar(größe)` to work exactly as their ASCII spellings do, in the saved page and the served app.
- **US-07.4** As the dashboard viewer, I want a tooltip, a filter and a colour key never to carry a name that can break the page's markup, whatever the data file holds.
- **US-07.5** As the maintainer, I want one rule for every internal column name, checked by a test, so that the next internal column (section 14's hover text column) cannot reintroduce G1.

## Business requirements

- **BR-07.1** A dataset holding a variable whose name begins with `__dash` is refused with r(110) by every route that exports data (`dash <plot> …, saving()`, `dash build`, `dash build, server`, `dash serve`), before any export, naming the variable and the prefix, with the data left as they were.
- **BR-07.2** A spec or data file holding a column whose name begins with `__dash` and that the spec does not name as a qualifier column is refused by the saved renderer and by the served builder with a named error, never a traceback.
- **BR-07.3** Every other valid Stata name is read as the user's data in both modes: a variable named `__mlabel__y`, `_x_jit`, `__mlabel_values__`, `x` or `top` draws its own values as a plot variable.
- **BR-07.4** A Unicode variable name is accepted wherever an ASCII one is: `filter()` (every type), `dash kpi stat()`, `by()`, `hover()`, `colorvar()`; its widget, panels, tooltip field and colours are built in both modes with no note.
- **BR-07.5** A name that is not a Stata name — holding a brace, a quote, a blank, `$`, a backtick, markup, or longer than 32 characters — is refused at each of those sites with the note or error it gets today.
- **BR-07.6** dash.sthlp states the reserved prefix, the two residuals (the qualifier columns still made in the data in memory, so a dataset at `c(maxvar)` may fail; a variable named like a drawn glyph field is shadowed in `hover()`/`mlabel()`), and that names may hold Unicode letters.
- **BR-07.7** Once a name is honoured, nothing is printed (DISCOVERY Q22).

## Technical requirements

- **TR-07.1** `dash_render.py`: `_DASH_RESERVED_PREFIX = "__dash"` next to `_DASH_QUAL_PREFIX` (20277); `_dash_take_qual_columns` refuses any column `c.startswith(_DASH_RESERVED_PREFIX)` that `_dash_qual_cols_named(spec)` does not list — so a spec-named `__dashq<k>` still passes — with `ValueError("dash: the data hold a column named %r; names beginning with __dash are reserved for the columns dash makes.")`; the served builder's trigger at 25002 tests `_DASH_RESERVED_PREFIX in self._raw_data_str`; the constant joins the served constants list beside `"_DASH_QUAL_PREFIX"` (24390; `sections/index.md` rule R2).
- **TR-07.2** Column-name constants, all module-level and all in the served constants copy list beside `"_ROW_ID_COLUMN"` (24340; `sections/index.md` rule R2) — GlyphMapper reads them, so `TestTheServedAppCarriesEveryName` demands them: `_ROW_ID_COLUMN = "__dash_row__"` (unchanged), `_DASH_PC_ROW_COLUMN = "__dash_pc_row__"`, `_DASH_MLABEL_PREFIX = "__dash_mlabel_"`, `_DASH_MLABEL_VALUES = "__dash_mlabel_values"`, `_DASH_MLABEL_X = "__dash_mlabel_x"`, `_DASH_MLABEL_Y = "__dash_mlabel_y"`, `_DASH_JITTER_X = "__dash_xjit"`, `_DASH_JITTER_Y = "__dash_yjit"`, `_DASH_LABEL_SUFFIX = "_label"`. The sites: 6750 → `f"{_DASH_MLABEL_PREFIX}{mlabel_var}"`; 6965 → `f"{_DASH_MLABEL_PREFIX}{var}_fmt_{hex}"`; 10832-10890 and 11544-11565 → the three mlabel constants and `_DASH_PC_ROW_COLUMN`; 11345 → `f"{_DASH_RESERVED_PREFIX}_{ptype}{_DASH_LABEL_SUFFIX}"` (`__dash_scatteri_label`); 5498-5500 → the jitter constants; 5560 → `f"{_DASH_JITTER_X}{sfx}"`; 18246 → `col.startswith(_DASH_JITTER_X) or col.startswith(_DASH_JITTER_Y)`. No new function: f-strings over the constants, so `test/function_test_map.py` is untouched.
- **TR-07.3** The naming rule, written as a comment above `_DASH_RESERVED_PREFIX` and enforced by `test/test_internal_column_names.py`: every column a renderer makes up is `__dash_<what>` (a trailing `__` is kept only on the two legacy row-id names); section 14's hover text column is `__dash_hover_{var}`.
- **TR-07.4** JS twin: the literal at 14219 becomes a placeholder filled from the constant when `_FILTER_JS` is assembled — `_FILTER_JS = (_DASH_FILTER_MASK_JS + """…const ROW_ID = __DASH_ROW_ID__;…""").replace("__DASH_ROW_ID__", json.dumps(_ROW_ID_COLUMN))` — so the JS and Python twins cannot disagree; the brush script (23499) is unchanged.
- **TR-07.5** dash.ado `_dash_qual_gen` 4255-4261: `capture unab _dq_clash : __dash*`; message "`cmdname': variable `_dq_first' is named with the prefix __dash, which is reserved for the columns dash makes (its qualifier columns __dashq#, its row identity __dash_row__ and its marker-label and jitter columns)." then the existing "Rename it first, for example: rename `_dq_first' newname"; `exit 110`. Both callers (5943, 6893) are unchanged.
- **TR-07.6** dash_parse.mata: a new function `real scalar _dash_is_varname(string scalar s)` returning `ustrregexm(s, "^[\p{L}_][\p{L}\p{N}_]*$") & ustrlen(s) <= 32` (the 2916 rule), placed next to `_dash_is_name`; `_dash_filter_refusal` calls it at 3453 instead of `_dash_is_name`; the echo class at 3457 becomes `"[^\p{L}\p{N}_.\-]"`; the docstring at 3409-3410 says "a Stata name" not "an ASCII Stata name". `_dash_is_name` is unchanged. Entry in `test/program_coverage_map.py`, in alphabetical place: `"_dash_is_varname": ("test_statistical_options.cscript:UN-02",)` (UN-02 exercises the accepted Unicode name and, as its negative control, the refused brace).
- **TR-07.7** dash.ado 6094-6100: `ustrregexm(st_local("statspec"), "^([a-zA-Z0-9.]+)\(([\p{L}_][\p{L}\p{N}_]*)\)$")` with `ustrregexs(1)`/`ustrregexs(2)`, and the refusal also fires when `ustrlen(kpi_var) > 32`; the message stays "dash kpi: syntax is stat(varname), e.g. mean(mpg)."; `confirm variable` (6142) and the numeric check (6147) follow as today. ICU regex, so the caller's `version` does not change the engine (the note above 5629 is about Stata's `regexm`, not `ustrregexm`).
- **TR-07.8** dash_render.py: the five `_DASH_VARNAME_RE` sites (15513, 19340, 19362, 19932, 20022) and the inline regex at 6365 call `_dash_is_stata_name(...)`; `_DASH_VARNAME_RE` (19207) is deleted and its entry removed from the served constants list (24372); `"_dash_is_stata_name"` is added to the served functions list immediately after `"_dash_parse_filter_raw"` (24687, the tuple's last entry today; S09 appends its launcher names after it at the merge, R2). Messages are unchanged. `_dash_is_stata_name`'s existing entry in `function_test_map.py` stands (the map takes one string per key; leave the existing one).
- **TR-07.9** dash.sthlp:166-171 rewritten for the `__dash` prefix and the two residuals (G1 commit); the `filter()` paragraph (1108-1109) and the `dash kpi` syntax paragraph (1194-1197) say the name may hold Unicode letters, as any Stata name (G5 commit). CHANGELOG (D2; `sections/index.md` rule R3, section-01 TR-01.7): the G1 line replaces, in place, the marker `<!-- WP-28 G1 -->` that S01 put at the end of the release's top-level `### Changed behaviour (may need your do-files changed)` list (CHANGELOG.md:280) — the renames are folded into that one line, which ends `(WP-28, G1)`; the G5 line replaces, in place, the marker `<!-- WP-28 G5 -->` under the heading `### Fixed in WP-28` that S01 creates directly above `### Fixed after WP-27 (the S3 batch, 24sep2026)` (:338), and ends `(WP-28, G5)`; nothing else is added anywhere in CHANGELOG.md. BUGS.md (D3): one closed entry per gap, appended at the END of BUGS.md, the field written `- Resolution: Fixed <ddmonyyyy> (WP-28, G1). <what changed, in which functions, in both renderers>. Pinned by test/<file>.py::<Class>::<test>, test/<script>.cscript <CASE-ID>. Residual, deferred (WP-28): <what and why>.` (G1 carries the two residuals; G5 has none); titles hold no `"`.
- **TR-07.10** Security (CLAUDE.md rule 1): every name reaching a Bokeh field, a tooltip, a widget title or a Stata command passes `_dash_is_stata_name` / `_dash_is_varname`; the refused text is echoed only through `_dash_display` (Python) or the `ustrregexra` echo (Mata), never raw.
- **TR-07.11** Certification homes (D11 (`sections/BRIEF.md` "Certification scripts", `sections/index.md` rule R1)): no new `.cscript` file. The `__dash` refusal extends QS-06 of `test/test_qualifier_in_stata.cscript` (it already holds the `__dashqz` case and the `python:` reader `_qs_page`); the Unicode cases UN-01..UN-03 are appended to `test/test_statistical_options.cscript` after SO-30u (482-484, which already builds `größe`), the two page-reading cases inside a `if c(python_exec) != ""` region in the form of the one at 710. Neither `test/run_all_cscripts.do` nor the pins at `test/test_cscript_hygiene.py:292,308` change. `by()`, `hover()` and `colorvar()` on a Unicode name are pinned by `test/test_unicode_names.py` in both modes and get no cscript case: there is no twoway drawing or Stata value to compare.

## Boundaries

- Do not change `_dash_is_name` (827-840): layout names and option words stay ASCII by design.
- Do not touch graph and KPI name validation (dash.ado 5617/5639, 6172/6184): those names become global macro names and stay ASCII.
- Do not export from a temporary frame or move the `__dashq<k>`/`__dashfix<hex>` generation out of the user's data: the `c(maxvar)` room issue is a recorded residual (PRD §7, DISCOVERY Q7).
- Do not make `_carry_cols` (5573) overwrite the derived glyph fields, and do not rename the glyph fields: the `x`/`y`/`top`/`count`/`density` shadowing in `hover()`/`mlabel()` is a recorded residual (RESEARCH conflict 3).
- Do not change what `_dash_reserved_name` (1547) refuses for registered graph/KPI names, nor `_dash_qual_cols_named`.
- Do not add a hover text column (section 14) or touch `_dash_build_hover`'s fields beyond the name check.
- Do not change `_dash_write_stata_data`'s own name check (it already uses `_dash_is_stata_name`).
- Do not create a certification script, edit `test/run_all_cscripts.do` or the hygiene pins (D11); do not edit `_dash_filter_refusal` beyond lines 3453 and 3457 (S08 refactors the rest after this section merges).
- No new plot types; nothing from the other GAPS2 gaps.

## Stata truth

None: no extract script and no fixture. The truth this section pins is Stata's own r(110) and `summarize`'s `r(mean)`, both read at run time by the cscripts. Stata is run only through the slot wrapper (D6, `index.md` step 0), which implements CLAUDE.md rule 10 — `cd <dir> && STATATMP=<dir>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do <file>` under one of three `mkdir` slots, never the GUI. A cscript cannot be handed to the wrapper directly: `run_all_cscripts.do` does `cd "<repo>/test"` before `do "test_x.cscript"`, and every cscript opens `cscript "…" adodir ".."` and loads `cert_helpers.do`, `../dash_parse.mata` and `../dash.ado` relative to that directory. So each single-script run goes through a two-line driver written into the scratch directory (`sections/BRIEF.md` "Running one cscript", `sections/index.md` step 0a):

```
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "<script>.cscript" > <scratch>/run_<script>.do
scripts/stata_slot.sh <scratch> <scratch>/run_<script>.do
```

where `<scratch>` is this section's scratch directory (say `/tmp/dash-s07`) and `<repo>` the root of the tree under test — this section's worktree; the main checkout is `/Users/billy/Desktop/Programs/StataPrograms/d/dash`. The batch log is `<scratch>/run_<script>.log` and `STATATMP` is `<scratch>/tmp/`, so nothing is written into the worktree. At most three Stata sessions run at once across all batch-1 agents (the slots enforce it; research C §8: more can drop `python_exec` from `~/.stata19/console/stata19.rc`; check `display c(python_exec)` in a log before trusting a skip). No fixture, so no `git add -f`.

## TDD test stubs

The regression tests first — each fails at `91d97be` for the reason given. G1's are written in 07-01..07-03, G5's in 07-11..07-12 (after the G1 commit, against a tree unmodified at every G5 site).

`test/test_reserved_names.py`, new class `TestTheDashPrefix` (task 07-01):
- Test: `test_a_column_under_the_prefix_is_refused_in_both_modes[name]` — parametrised over `__dash_row__`, `__dash_mlabel_y`, `__dash_xjit`, `__dashfix0a1b2c3d4e5f`, `__dash`; a data file with that column and a scatter over it: `DashRenderer(sp, dp)` (the refusal is in `__init__` → `_load_data`) and `ServerAppBuilder(sp, dp).build(ap)` both raise `ValueError` matching `"reserved"` and `"__dash"`. **Pre-fix: no error; `__dash_row__` is overwritten and the others drawn** (the ValueError is raised only for `__dashq*`).
- Test: `test_a_qualifier_column_the_spec_names_still_passes` — `__dashq1` named by `qual_col` renders in both modes (control; passes before and after).
- Test: `test_a_name_dash_no_longer_makes_is_drawn_with_its_own_values[name]` — parametrised over `__mlabel__y`, `_x_jit`, `__mlabel_values__`, `_y_jit`, `x`, `top`: a scatter with that column as its y (plus `jitter(5)` for the jitter names and `mlabel(<name>)` for the mlabel names) draws, in both modes, the y values equal to the frame's, and for the mlabel case the label text column is `__dash_mlabel_<name>` and holds the frame's values as text. **Pre-fix: `__mlabel__y` as `mlabel(__mlabel__y)` reads the user column as label text (guard `if text_col not in source.data`), and `_x_jit` with jitter is overwritten.**
- Test: `test_the_stata_side_and_the_help_share_the_prefix` — reads `dash.ado` for `unab _dq_clash : __dash*` and `dash.sthlp` for `{cmd:__dash}` and asserts `dr._DASH_RESERVED_PREFIX == "__dash"`. **Pre-fix: dash.ado has `__dashq*`.**

`test/test_internal_column_names.py` (new; task 07-02):
- Test: `TestEveryInternalColumnIsUnderThePrefix::test_no_column_literal_escapes_the_prefix` — `ast.walk` over `dash_render.py`'s string constants (including f-string literal parts): no constant contains `__mlabel`, `_x_jit`, `_y_jit` or `_label__`; every constant that starts with `__` and is not in the allowlist `{"__missing__", "__all__", "__tabs__", "__fw_", "__by__", "__builtins__", "__name__", "__main__", "__future__", "__dashq", "__dashfix", "__DASH_ROW_ID__"}` (prefix match) starts with `__dash`. The scan reads `dash_render.py` only, never the plan files or this section's own table. **Pre-fix: fails on 6750, 6965, 10832, 10861, 10863, 11345, 5498-5500, 5560, 18246.**
- Test: `test_every_column_constant_starts_with_the_prefix` — each constant of TR-07.2 exists and `startswith("__dash")`. **Pre-fix: AttributeError.**
- Test: `TestTheJsTwin::test_the_filter_js_row_id_is_filled_from_the_constant` — the module source between `_FILTER_JS = ` and the next top-level assignment holds no `"__dash_row__"` literal, and `dr._FILTER_JS` contains `'const ROW_ID = "%s";' % dr._ROW_ID_COLUMN` exactly once. **Pre-fix: the literal is present.**
- Test: `TestTheRenamedColumns::test_the_marker_label_columns_in_both_modes` — `mlabel(foreign)` and `mlabel(price) mlabformat(%9.2f)` on a scatter: the layer's source has `__dash_mlabel_foreign` and `__dash_mlabel_price_fmt_<hex>` in the saved page and the served document, and no column starting `__mlabel`. **Pre-fix: the old names.**
- Test: `test_the_jitter_columns_in_both_modes` — `jitter(5)`: the glyph draws `__dash_xjit`/`__dash_yjit`; under `link(_all)` the shared source gains `__dash_xjit` and, for a second jittered layer, `__dash_xjit_2`. **Pre-fix: `_x_jit`.**
- Test: `test_the_pc_and_rscatter_label_columns_in_both_modes` — `pcscatter … mlabel(v)` and `rscatter … mlabel(v)`: the marker source holds `__dash_mlabel_values`, `__dash_mlabel_x`, `__dash_mlabel_y` (pc) and `__dash_pc_row__`. **Pre-fix: the old names.**
- Test: `test_the_literal_label_column_in_both_modes` — `scatteri 1 2 "a"`: the label source's text column is `__dash_scatteri_label`. **Pre-fix: `__scatteri_label__`.**

`test/test_unicode_names.py` (new; task 07-11; both modes through `test_mode_parity._spec`/`_standalone`/`_served` with `monkeypatch.setattr(tp, "_DF", df)` where `df = tp._DF.rename(columns={"price": "größe", "foreign": "ausländisch"})`, the pattern of `test_help_claims_1.py:_run`):
- Test: `TestTheNameCheck::test_unicode_letters_pass_and_markup_does_not` — `_dash_is_stata_name` is True for `größe`, `ausländisch`, `_x`, `a1`, `"a"*32`; False for `x}<img src=x>`, `a b`, `a"b`, `$m`, `` a`b ``, `1a`, `""`, `"a"*33`, `None`. (Passes before and after; it pins the predicate every site now relies on.)
- Test: `TestFilterOnAUnicodeName::test_the_parser_keeps_the_name` — `_dash_parse_filter_raw("größe, type(range)")` returns one spec with variable `größe` and no warning. **Pre-fix: `[]` and "is not a valid variable name".**
- Test: `test_a_range_widget_is_built_in_both_modes` and `test_a_dropdown_is_built_in_both_modes` — `filter(größe, type(range))` / `type(dropdown)`: one `RangeSlider` / `Select` titled from `größe` in the saved renderer's `filter_widgets` and in the served document; no "refused" warning. **Pre-fix: no widget.**
- Test: `TestByOnAUnicodeName::test_panels_are_drawn_in_both_modes` — `by(ausländisch)` draws two figures in both modes and no "drawn without panels" warning; `_dash_parse_by("ausländisch")[0] == "ausländisch"`. **Pre-fix: one figure and the warning.**
- Test: `TestHoverOnAUnicodeName::test_the_tooltip_field_is_kept_in_both_modes` — `hover(größe)`: the HoverTool's tooltips carry `@{größe}` in both modes and no "not a plain name" note. **Pre-fix: left out with the note.**
- Test: `TestColorvarOnAUnicodeName::test_colours_are_drawn_in_both_modes` — `colorvar(ausländisch)`: the scatter renderer's fill colour is a field transform (a `CategoricalColorMapper`/`LinearColorMapper` on the figure) in both modes. **Pre-fix: no mapper, plain colour, nothing said.**
- Test: `TestAdversarialUnicodeNames::test_a_non_name_is_still_refused_at_every_site[name]` — parametrised over `x}<img src=x onerror=alert(1)>`, `a"b`, `a b`, `größe$x`, `"ä"*33`: `_dash_parse_filter_raw` refuses with the note, `_dash_parse_by` warns and returns no panels, hover leaves it out with the note, `_apply_colorvar` returns without a mapper; nothing raw appears in any warning (`_dash_display`). (Passes before and after for the ASCII cases; the 33-character case is new.)
- Test: `TestTheServedAppCarriesTheCheck::test_the_generated_app_defines_dash_is_stata_name` — the built app source defines `_dash_is_stata_name` and no longer defines `_DASH_VARNAME_RE`. **Pre-fix: the reverse.**

Certification cases (D11: no new script; each joins the script of its area):
- `test/test_qualifier_in_stata.cscript` QS-06 extended (task 07-03; after the existing `rename __dashqz mpg` at 516): `rename price __dash_row__` → `_qs_run` on the one-line route and on `dash build` both r(110) with `cert_log_has needle("prefix __dash")`; `confirm variable __dash_row__` and its values unchanged; `rename __dash_row__ price`; `generate byte __dash_x = 1` → r(110) on the one-line route; `drop __dash_x`. Then `rename mpg x`: `dash scatter x rowid, saving()` is rc 0 and the page's scatter y column `x` equals Stata's `x` (a new reader `_qs_col(name)` in the python block returning the joined values of the first Scatter source's column, compared with a Stata-built list); `rename x top` and the same with `dash bar top rowid`; rename back. **Pre-fix: `__dash_row__` builds with rc 0.**
- `test/test_statistical_options.cscript` UN-01..UN-03 (task 07-12), each ending with the file's own `_so_tally "UN-0k" <bad> "<text>"` so the closing summary counts it, and each restoring `sysuse auto` with `rename price größe` and `rename foreign ausländisch` undone afterwards. UN-01: `dash kpi mean(größe), name(k1)` rc 0 and `reldif(${dash_kpi_k1__val}, r(mean))` of `summarize größe` below 1e-15 (the HC4 pattern at test_help_claims_4.cscript:324-326); then, as the case's negative control, `dash kpi mean(größe123456789012345678901234567890)` (33 characters) → r(198) "syntax is stat(varname)". UN-02 (inside a `if c(python_exec) != ""` region in the form of 710): `dash scatter mpg weight, name(g1)` then `dash build, saving() replace nobrowser filter(größe, type(range))` rc 0 and the page holds a `RangeSlider` whose title holds `größe` — read by a small `python:` reader `_un_page_has(needle)` that json-loads the page's `<script type="application/json">` block and searches `json.dumps(docs, ensure_ascii=False)` (Bokeh writes non-ASCII as `\uXXXX`, so a raw `cert_file_has` search for `größe` fails); then its negative control `filter(x}y, type(range))` → r(198) "not a valid Stata variable name" with the brace shown as `?`. UN-03: the same build with `type(dropdown)` → `Select`. **Pre-fix: UN-01's positive r(198) at the KPI pattern; UN-02's and UN-03's positives r(198) at the filter parse; the two negative controls pass before and after.** `by()`, `hover()` and `colorvar()` on a Unicode name have no cscript case (TR-07.11).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| `__dash*` column refused by the renderers, named error | pytest `test_reserved_names.py::TestTheDashPrefix` | none | yes |
| `__dash*` variable refused r(110) on every route with data | cscript `test_qualifier_in_stata.cscript` QS-06 (extended) | none | one-line + build (saved) |
| Old internal names and glyph-field names draw the user's values | pytest `TestTheDashPrefix::…drawn_with_its_own_values`; cscript QS-06 (`x`, `top`) | none | yes |
| No internal column outside the prefix (guard) | pytest `test_internal_column_names.py` | none | n/a (source scan) |
| JS `ROW_ID` filled from the constant | pytest `TestTheJsTwin` | none | saved (JS only) |
| Renamed columns in every mapper | pytest `TestTheRenamedColumns` | none | yes |
| Unicode `filter()`, `by()`, `hover()`, `colorvar()` | pytest `test_unicode_names.py`; cscript `test_statistical_options.cscript` UN-02, UN-03 (filter widgets) | none | yes |
| Unicode `dash kpi` equals `summarize` | cscript `test_statistical_options.cscript` UN-01 | none | n/a (Stata) |
| Non-names still refused at every site | pytest `TestAdversarialUnicodeNames`; cscript UN-01 and UN-02 negative controls | none | yes |
| Served app carries `_dash_is_stata_name`, not `_DASH_VARNAME_RE` | pytest `TestTheServedAppCarriesTheCheck` + existing guards | none | served |
| `[aw=größe]` still accepted | cscript `test_statistical_options.cscript` SO-30u (existing) | none | n/a |
| Help and code agree on the prefix | pytest `…share_the_prefix` | none | n/a |

Acceptance criteria:
- **AC-07.1** `sysuse auto; rename price __dash_row__; dash scatter mpg weight, saving(x.html)` is r(110), prints the prefix `__dash` and a `rename` hint, writes no file and leaves the data unchanged; the same through `dash build`, `dash build, server` and `dash serve`.
- **AC-07.2** A data file with a column `__dash_row__` makes `DashRenderer(...)` and `ServerAppBuilder(...).build()` raise `ValueError` naming "reserved"; a spec-named `__dashq1` still passes.
- **AC-07.3** `rename mpg _x_jit; dash scatter _x_jit weight, jitter(5) saving(x.html)` draws `_x_jit`'s values jittered from the user's column, both modes; `mlabel(__mlabel__y)` labels with the user's values.
- **AC-07.4** `grep -n '__mlabel\|_x_jit\|_y_jit\|_label__' dash_render.py | grep -v ':[[:space:]]*#'` prints nothing (only a `#` comment line may still say an old name; code and docstrings may not), and the guard test passes.
- **AC-07.5** With `rename price größe`: `dash kpi mean(größe)` equals `summarize`; `filter(größe, type(range))`, `type(dropdown)`, `by(größe)`, `hover(größe)`, `colorvar(größe)` build their widget, panels, field and colours in both modes with nothing printed.
- **AC-07.6** Every injection case of `test_help_claims_1.py`, `test_security_surface.py`, `test_filter_label.py` and `test_mode_parity.py:2869` passes unchanged.
- **AC-07.7** `python3 -m pytest test/ -q` is green under both interpreters before each of the two commits; `test_qualifier_in_stata.cscript` and `test_statistical_options.cscript` pass under Stata's Python with QS-06 and UN-01..UN-03 present; BUGS.md holds closed G1 and G5 entries naming their tests in the D3 form.

## Tasks

Commit boundary: **two commits, one per gap (D1).** The G1 commit holds 07-01 to 07-10 (the two new pytest files, the QS-06 cases, the renames, the ten flipped test files, the prefix refusal on both sides, the help paragraph, the G1 CHANGELOG line and the closed G1 entry), subject ending `(GAPS2 G1)`; the G5 commit holds 07-11 to 07-15 (the Unicode pytest file, the UN cases, the Mata/ado and renderer name checks, the two help sentences, the G5 CHANGELOG line and the closed G5 entry), subject ending `(GAPS2 G5)`. Each body opens with that gap's saved failure text and carries the `Regression:` / `Flipped:` / `BUGS.md:` lines of S01 TR-01.9; the full pytest suite runs green once before each commit (CLAUDE.md rules 4 and 11: two full runs in the session, one per commit, never two at once). No task commits a red tree. Every Stata run goes through `scripts/stata_slot.sh <scratch> <scratch>/run_<script>.do`, the two-line driver of "Stata truth" (D6; `sections/BRIEF.md` "Running one cscript", `sections/index.md` step 0a). The section executes in its own worktree on the branch `wp28-s07`; each closing task commits there after the worktree's own full run, and the merger lands it on `s3-bugs` with the task's message after `git merge --no-edit main` and the batch's full run (`sections/index.md` step 1). Line numbers are those of 91d97be; every site is also named by its symbol, and the symbol is authoritative. No AI references anywhere.

<task type="auto" id="07-01">
  <name>Write the failing reserved-name tests</name>
  <files>test/test_reserved_names.py</files>
  <action><![CDATA[
    Write only tests; do not touch dash_render.py, dash.ado or dash_parse.mata. Append class `TestTheDashPrefix` to `test/test_reserved_names.py` with the four tests named in "TDD test stubs" under that file, built on that file's `_graph`/`_spec` helpers and `test_adversarial_matrix._write_inputs`/`_load_app` for the served side; the parametrised refusal test asserts `ValueError` with `match="reserved"` from both `dr.DashRenderer(sp, dp)` and `dr.ServerAppBuilder(sp, dp).build(ap)`; the own-values test builds the jitter and mlabel variants through `test_mode_parity._spec`/`_standalone`/`_served` and reads the drawn y column from the first Scatter source in each mode. Run `python3 -m pytest test/test_reserved_names.py -q` against the unmodified tree: the three regression tests fail for the reasons the stubs give and the control passes. Do not commit: save the failure output to the scratch directory as `<scratch>/07-01-failure.txt`; it becomes the opening paragraph of the G1 commit (S01 TR-01.9, Q24).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_reserved_names.py -q 2>&1 | tail -15` collects cleanly and reports the parametrised refusal test failing with "DID NOT RAISE", the own-values test failing on `__mlabel__y` (label text) and `_x_jit` (overwritten values), and `test_the_stata_side_and_the_help_share_the_prefix` failing with `AttributeError: _DASH_RESERVED_PREFIX`; `<scratch>/07-01-failure.txt` exists and `git status --short dash_render.py dash.ado dash_parse.mata` prints nothing.]]></verify>
  <done>The reserved-name regression tests existed, collected and failed against the unmodified tree for the reasons the gap describes, with no product file changed and nothing committed.</done>
</task>

<task type="auto" id="07-02">
  <name>Write the failing internal-column guard tests</name>
  <files>test/test_internal_column_names.py</files>
  <action><![CDATA[
    Create `test/test_internal_column_names.py` with `TestEveryInternalColumnIsUnderThePrefix`, `TestTheJsTwin` and `TestTheRenamedColumns` as the stubs specify. The source scan uses `ast.parse` over `dash_render.py`'s file and walks `ast.Constant` (str) and `ast.JoinedStr` parts; put the allowlist in a module-level tuple with a comment naming each entry's role (layout key, sentinel, dunder, the JS placeholder); the scan never reads any file but `dash_render.py`. The both-mode cases use `test_mode_parity._spec`, `_standalone`, `_served` and read each layer's source columns by name. Run `python3 -m pytest test/test_internal_column_names.py -q` against the unmodified tree and append the failure output to `<scratch>/07-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_internal_column_names.py -q 2>&1 | tail -15` collects cleanly; `test_no_column_literal_escapes_the_prefix` fails listing the literals at the sites of TR-07.2, `test_every_column_constant_starts_with_the_prefix` and the JS-twin test fail with `AttributeError`/the present literal, and the three renamed-column tests fail on the old names in both modes; `git status --short dash_render.py` prints nothing.]]></verify>
  <done>The guard file existed, collected and failed against the unmodified tree on every internal column outside the prefix, with no product file changed.</done>
</task>

<task type="auto" id="07-03">
  <name>Write the failing QS-06 prefix cases</name>
  <files>test/test_qualifier_in_stata.cscript</files>
  <action><![CDATA[
    Extend QS-06 in `test/test_qualifier_in_stata.cscript` after line 516 (`rename __dashqz mpg`) with the `__dash_row__`, `__dash_x`, `x` and `top` cases of the stubs, keeping the existing `cert_log_has ... needle("reserved")` assertion and adding `needle("prefix __dash")` for the two new refusals. Add `_qs_col(name)` to the file's `python:` block (after `_qs_page`, 184), returning the first Scatter (or Quad for the bar) source's column joined with blanks through `_qs_M.setGlobal("QS_COL", ...)`; keep the block free of backslashes, backticks and dollar signs as its comment demands. Keep the header's `*! Tests: QS-01 .. QS-21` line as it is (no case id is added; QS-06 grows). Run the script against the unmodified tree through the driver of "Stata truth" (write `<scratch>/run_test_qualifier_in_stata.do`, then `scripts/stata_slot.sh <scratch> <scratch>/run_test_qualifier_in_stata.do`); read `<scratch>/run_test_qualifier_in_stata.log`: it stops in QS-06 at the first new assertion (rc 0 where 110 is asserted). Append that failing case's text to `<scratch>/07-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c 'prefix __dash' test/test_qualifier_in_stata.cscript` prints at least 2; the batch log against the unmodified tree ends in QS-06 with `assertion is false` at the `__dash_row__` rc check and holds `display c(python_exec)`'s value (not a skip); `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -2` still passes (no new script, no pin changed).]]></verify>
  <done>QS-06 carried the reserved-prefix and own-values cases and failed against the unmodified tree because a `__dash_row__` variable built with rc 0.</done>
</task>

<task type="auto" id="07-04">
  <name>Rename every internal column under the prefix</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add the constants of TR-07.2 immediately after `_ROW_ID_COLUMN` (2008), with the naming rule of TR-07.3 as a comment; `_DASH_RESERVED_PREFIX` goes beside `_DASH_QUAL_PREFIX` (20277) and the column constants reference it. Replace every literal at the sites listed in TR-07.2 (6750, 6965, 10832-10890, 11544-11565, 11345, 5498-5500, 5560, 18246) with the constants; rewrite the docstrings that name `_x_jit`/`_y_jit` (5460, 5511, 18226) so no string constant of the module names an old column (the guard test walks docstrings too; a `#` comment may keep the old name for the reader). Fill the JS literal per TR-07.4 (14219; `json` is imported at module level). Add every new constant to the served constants copy list beside `"_ROW_ID_COLUMN"` (24340) and `_DASH_RESERVED_PREFIX` beside `"_DASH_QUAL_PREFIX"` (24390), rule R2. Do not change `_dash_take_qual_columns` yet (07-09). Line numbers are pre-edit; locate each site by its symbol.
  ]]></action>
  <verify><![CDATA[`grep -n '__mlabel\|_x_jit\|_y_jit\|_label__' dash_render.py | grep -v ':[[:space:]]*#'` prints nothing; `python3 -m pytest test/test_internal_column_names.py test/test_statistical_helpers.py -k "InternalColumn or JsTwin or RenamedColumns or CarriesEveryName" -q 2>&1 | tail -3` passes; `python3 -m pytest test/test_jitter.py -q 2>&1 | tail -3` now fails only on old-literal assertions.]]></verify>
  <done>Every column dash_render.py makes up was named under the `__dash` prefix through module constants, the JS ROW_ID was filled from the constant, the served app carried every new constant, and the guard test passed.</done>
</task>

<task type="auto" id="07-05">
  <name>Flip the pinned jitter tests</name>
  <files>test/test_jitter.py, test/test_html_verification.py</files>
  <action><![CDATA[
    Edit each test named under Evidence in these two files to expect `dr._DASH_JITTER_X`/`dr._DASH_JITTER_Y` (import the constants rather than writing `"__dash_xjit"` by hand, so a later rename flips nothing). Add one comment per flipped assertion: "G1: the jitter columns are named under the __dash prefix". Do not delete any test; do not weaken any assertion. Record each flip as a `Flipped:` line for the G1 commit body.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_jitter.py test/test_html_verification.py -q 2>&1 | tail -3` passes; `grep -c '_DASH_JITTER_X' test/test_jitter.py test/test_html_verification.py` prints a count of at least 8 and 3 respectively.]]></verify>
  <done>The two jitter files pinned the new jitter column names through the module constants and passed.</done>
</task>

<task type="auto" id="07-06">
  <name>Flip the pinned server and filter-move tests</name>
  <files>test/test_saved_filter_layers.py, test/test_date_range.py, test/test_server.py</files>
  <action><![CDATA[
    In `test_saved_filter_layers.py` flip `TestAJitteredScatterFollowsAMove::test_the_kept_points_stay_where_they_were` (475-478) and `TestALinkedJitteredScatter::test_the_column_helper` (1025-1035; the suffix form becomes `f"{dr._DASH_JITTER_X}_2"`), and update the comment of `test_a_variable_named_like_the_jitter_column_is_kept` (999-1008) to say the glyph draws `__dash_xjit`, keeping its assertions. In `test_date_range.py` flip 805-807. In `test_server.py` flip the `TestServerFilterPreservesDerivedColumns` cases (7461-7652: `__mlabel__foreign` becomes `dr._DASH_MLABEL_PREFIX + "foreign"`, the jitter set the constants). Same comment rule and `Flipped:` record as 07-05. S03's edit of `test_saved_filter_layers.py` (85-214) is disjoint from these lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_saved_filter_layers.py test/test_date_range.py test/test_server.py -q -k "Jitter or Derived or jittered" 2>&1 | tail -3` passes.]]></verify>
  <done>The saved-page, date-axis and served-filter tests pinned the new names through the constants.</done>
</task>

<task type="auto" id="07-07">
  <name>Flip the remaining pinned name tests</name>
  <files>test/test_served_filter_move.py, test/test_server_facets.py, test/test_twoway_option_parity.py</files>
  <action><![CDATA[
    Flip the cases named under Evidence in these three files (`__mlabel__rep`, `__mlabel__x`, `__mlabel__when`, `__mlabel__v__fmt_<hex>` become the `_DASH_MLABEL_PREFIX` forms; the fmt column is `f"{dr._DASH_MLABEL_PREFIX}v_fmt_{hex}"`). Same comment rule and `Flipped:` record as 07-05. Run the three files.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_served_filter_move.py test/test_server_facets.py test/test_twoway_option_parity.py -q 2>&1 | tail -3` passes.]]></verify>
  <done>The served filter-move, facet and twoway-parity tests pinned the new marker-label column names through the constants.</done>
</task>

<task type="auto" id="07-08">
  <name>Flip the two one-line pins</name>
  <files>test/test_option_validation.py, test/test_marker_label_parity.py</files>
  <action><![CDATA[
    Flip `test/test_option_validation.py::TestABadValueNoLongerAbortsTheRender::test_negative_jitterseed` (734) to `dr._DASH_JITTER_X` and `test/test_marker_label_parity.py::TestAdversarialMarkerLabels::test_a_huge_label_set_is_read_at_once` (939) to `dr._DASH_MLABEL_PREFIX + "..."`, each one line, with the G1 comment and a `Flipped:` record. Run the ten flipped files together once.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_option_validation.py test/test_marker_label_parity.py test/test_jitter.py test/test_html_verification.py test/test_saved_filter_layers.py test/test_date_range.py test/test_server.py test/test_served_filter_move.py test/test_server_facets.py test/test_twoway_option_parity.py -q 2>&1 | tail -3` passes; `grep -rn '__mlabel__\|"_x_jit\|"_y_jit' test/*.py` prints only the docstring and the user-variable case of `test_saved_filter_layers.py:999-1008`, nothing that names a dash-made column.]]></verify>
  <done>No test pinned an old internal column name, and every flipped assertion carried the G1 comment.</done>
</task>

<task type="auto" id="07-09">
  <name>Reserve the prefix on both sides</name>
  <files>dash.ado, dash_render.py</files>
  <action><![CDATA[
    dash.ado 4255-4261: apply TR-07.5 (`unab _dq_clash : __dash*`, the new first line, the existing rename hint, `exit 110`); update the comment block above `_dash_qual_gen` (4230-4250) to say the prefix covers every column dash makes. dash_render.py: apply TR-07.1 in `_dash_take_qual_columns` (the `reserved` list tests `_DASH_RESERVED_PREFIX`; the message keeps the word "reserved" for `test_qualifier_columns.py` and QS-06) and at the served trigger 25002; update the module comment above `_DASH_QUAL_PREFIX` (20276-20277). Run `python3 -m pytest test/test_reserved_names.py test/test_qualifier_columns.py test/test_internal_column_names.py -q`, then the QS cscript through its driver (`scripts/stata_slot.sh <scratch> <scratch>/run_test_qualifier_in_stata.do`).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_reserved_names.py test/test_qualifier_columns.py test/test_internal_column_names.py -q 2>&1 | tail -3` passes; `<scratch>/run_test_qualifier_in_stata.log` shows `QS-06 PASS` and every later QS case's PASS line, and `grep -c '^r([0-9]*);' <scratch>/run_test_qualifier_in_stata.log` prints 0.]]></verify>
  <done>A variable named under `__dash` was refused with r(110) by dash.ado on every route with data and with a named ValueError by both renderers, while a spec-named qualifier column still passed.</done>
</task>

<task type="auto" id="07-10">
  <name>Document and close G1</name>
  <files>dash.sthlp, CHANGELOG.md, BUGS.md</files>
  <action><![CDATA[
    dash.sthlp:166-171: replace the `__dashq` sentence with one saying names beginning with `{cmd:__dash}` are reserved for the columns dash makes (the qualifier columns `{cmd:__dashq}{it:#}`, the row identity `{cmd:__dash_row__}`, its marker-label and jitter columns), that data holding such a variable are refused with `{cmd:r(110)}`, and that every other Stata name is read as data; add a `{pstd}` paragraph stating the two residuals in the words of the BUGS.md entry below. CHANGELOG.md: replace, in place, the marker `<!-- WP-28 G1 -->` that S01 put at the end of the release's top-level `### Changed behaviour (may need your do-files changed)` list (:280; D2, `sections/index.md` rule R3, section-01 TR-01.7) with one line ending `(WP-28, G1)`: a variable whose name begins `__dash` is refused with r(110) before any export (rename it first); every column dash makes is now named under that prefix (`__dash_mlabel_*`, `__dash_xjit`/`__dash_yjit`, `__dash_pc_row__`, `__dash_<type>_label`), so a variable named `__mlabel__y`, `_x_jit` or `top` is drawn with its own values where `__dash_row__` was overwritten and `__mlabel__y` read as label text; add nothing else anywhere in CHANGELOG.md (the G5 marker under `### Fixed in WP-28` is 07-15's). BUGS.md: append at the END of the file the closed entry `- [x] Title: An internal column name could overwrite a user variable, and only __dashq was reserved` with File Names and Line Numbers (dash_render.py `_make_source`, `_apply_mlabel_opts`, `_build_jitter_source`, `_dash_take_qual_columns`; dash.ado `_dash_qual_gen`; dash.sthlp), Description (GAPS2 G1's measured symptom, quoted), Suggested fix (reserve `__dash`, rename every internal column under it), and `- Resolution: Fixed <ddmonyyyy> (WP-28, G1). Every column dash makes is named under the __dash prefix through module constants (the marker-label, pc/rscatter, literal-label and jitter columns; the JS ROW_ID is filled from _ROW_ID_COLUMN), and a variable whose name begins __dash is refused with r(110) by _dash_qual_gen in dash.ado and with a named ValueError by _dash_take_qual_columns in both renderers. Pinned by test/test_reserved_names.py::TestTheDashPrefix::test_a_column_under_the_prefix_is_refused_in_both_modes, test/test_internal_column_names.py::TestEveryInternalColumnIsUnderThePrefix::test_no_column_literal_escapes_the_prefix, test/test_qualifier_in_stata.cscript QS-06. Residual, deferred (WP-28): the qualifier, by()-order and ustrfix columns are still generated in the data in memory, so a dataset at c(maxvar) may fail with r(900); a variable named like a drawn glyph field (x, y, x0, top, count, density and the like) draws its own values as a plot variable but is shadowed by the derived field in hover() and mlabel().` The title holds no `"`. Then run the full pytest suite once in the worktree (`python3 -m pytest test/ -q`, the first of the session's two full runs; CLAUDE.md rule 4), run the QS cscript through its driver again, grep the three documents and the message for `claude\|anthropic`, and commit every file 07-01 to 07-10 touched (the two new pytest files, the cscript, the ten flipped test files, dash_render.py, dash.ado, dash.sthlp, CHANGELOG.md, BUGS.md) on the worktree branch `wp28-s07` as ONE commit, subject ending `(GAPS2 G1)`, body opening with `<scratch>/07-01-failure.txt` and carrying the `Regression:` / `Flipped:` / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` with this message after `git merge --no-edit main` and the batch's full run (`sections/index.md` step 1).
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py test/test_help_claims_4.py -q 2>&1 | tail -3` passes; `grep -c '<!-- WP-28 G1 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, G1)' CHANGELOG.md BUGS.md` prints 1 for each file; `grep -c '{cmd:__dash}' dash.sthlp` is at least 1 and `grep -c '__dashq}{it:#}, which no' dash.sthlp` prints 0; `git log -1 --format=%s | grep -c '(GAPS2 G1)'` prints 1 and `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0; `git status --short` prints nothing.]]></verify>
  <done>G1 was closed in BUGS.md with both residuals, the help stated the prefix, the G1 CHANGELOG marker was replaced, and one green commit on the worktree branch `wp28-s07` carried the gap for the merger.</done>
</task>

<task type="auto" id="07-11">
  <name>Write the failing Unicode-name tests</name>
  <files>test/test_unicode_names.py</files>
  <action><![CDATA[
    Create `test/test_unicode_names.py` with the classes and tests of the stubs; rename columns of `tp._DF` through `monkeypatch.setattr(tp, "_DF", df)`; read hover tooltips from `HoverTool.tooltips`, the colorvar mapper from the scatter renderer's `glyph.fill_color` (a dict with `"transform"`), widgets from `renderer.filter_widgets` (saved) and `doc.select({"type": RangeSlider})` (served). Run `python3 -m pytest test/test_unicode_names.py -q` against the tree the G1 commit leaves (unmodified at every G5 site): every regression test fails for the pre-fix reason in the stubs and the controls (`TestTheNameCheck`, the ASCII adversarial cases) pass. Do not commit: save the failure output to `<scratch>/07-11-failure.txt`; it opens the G5 commit's body (S01 TR-01.9, Q24).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unicode_names.py -q 2>&1 | tail -15` collects cleanly and shows the filter, by(), hover(), colorvar() and served-copy tests failing (no widget, one figure, the "not a plain name" note, no mapper, `_DASH_VARNAME_RE` present) with `TestTheNameCheck` passing; `<scratch>/07-11-failure.txt` exists; `git status --short dash_render.py dash.ado dash_parse.mata` prints nothing.]]></verify>
  <done>The Unicode-name regression tests existed, collected and failed against the post-G1 tree at every G5 site for the reasons the gap describes.</done>
</task>

<task type="auto" id="07-12">
  <name>Write the failing UN certification cases</name>
  <files>test/test_statistical_options.cscript</files>
  <action><![CDATA[
    Append UN-01..UN-03 to `test/test_statistical_options.cscript` after SO-30u (482-484) as the stubs specify: UN-01 outside any Python guard (the KPI equals `summarize`'s `r(mean)`; the 33-character name is its negative control); UN-02 and UN-03 inside a `if c(python_exec) != ""` region in the form of the one at 710, with a small `python:` reader `_un_page_has(needle)` that json-loads the page's `<script type="application/json">` block and searches `json.dumps(docs, ensure_ascii=False)` (UN-02's negative control is `filter(x}y, type(range))` refused with the brace shown as `?`). Each case tallies through `_so_tally` and restores the data (`rename größe price`, `rename ausländisch foreign`, `dash clear`). Extend the header's `*! Tests:` line with `UN-01..UN-03 (WP-28 G5)`. Run the script against the current tree through its driver (write `<scratch>/run_test_statistical_options.do` as in "Stata truth", then `scripts/stata_slot.sh <scratch> <scratch>/run_test_statistical_options.do`); read `<scratch>/run_test_statistical_options.log`: the SO cases still pass, UN-01's positive fails with r(198) "syntax is stat(varname)", UN-02's and UN-03's positives fail with r(198) at the filter parse, the two negatives pass, and the closing summary counts three failures. Append the failing case text to `<scratch>/07-11-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '"UN-0[1-3]"' test/test_statistical_options.cscript` prints at least 3; the batch log ends `test_statistical_options: 3 CHECK(S) FAILED` with `failing: UN-01 UN-02 UN-03` (in the file's summary form) and holds `c(python_exec)`'s value, not a skip; `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -2` still passes.]]></verify>
  <done>The three Unicode certification cases lived in the statistical-options script and failed against the pre-fix tree because `dash kpi` and `filter()` refused a Unicode name.</done>
</task>

<task type="auto" id="07-13">
  <name>Accept Unicode names in filter() and dash kpi</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    dash_parse.mata: add `_dash_is_varname` (TR-07.6) directly after `_dash_is_name`, with a comment that it is the by() rule of 2916 and that `_dash_is_name` stays ASCII for layout and option words; call it at 3453; widen the echo class at 3457 to `[^\p{L}\p{N}_.\-]`; fix the docstring at 3409-3410; touch nothing else in `_dash_filter_refusal` (S08 refactors its exclude() reading after this section merges). Optionally make 2916 call it too (same semantics). dash.ado 6094-6100: apply TR-07.7, keeping the "read by value, in Mata, in one statement" structure and the JSE-58 comment; the length check reads `ustrlen(st_local("kpi_var")) > 32` inside the same Mata statement, folding into `_kst_ok`. `test/program_coverage_map.py`: add `"_dash_is_varname": ("test_statistical_options.cscript:UN-02",)` in alphabetical place. Run `test_statistical_options.cscript` through its driver (UN-01 now passes; UN-02 and UN-03 still fail in the renderer, which builds no widget until 07-14; SO-30u still passes), then `python3 -m pytest test/test_program_coverage_map.py test/test_no_orphans.py -q`.
  ]]></action>
  <verify><![CDATA[The batch log shows UN-01 passing (its `_so_tally` line clean) and the summary `2 CHECK(S) FAILED` naming UN-02 and UN-03 only; `python3 -m pytest test/test_program_coverage_map.py test/test_no_orphans.py -q 2>&1 | tail -3` passes; `grep -c '_dash_is_varname' dash_parse.mata` is at least 2.]]></verify>
  <done>dash.ado and dash_parse.mata accepted a Unicode variable name in `dash kpi` and `filter()` under the 2916 rule, refused a non-name or a 33-character name as before, and the new Mata function was mapped to its case.</done>
</task>

<task type="auto" id="07-14">
  <name>Replace the ASCII name regex</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-07.8: at 15513, 19340, 19362, 19932 and 20022 call `_dash_is_stata_name(x)` in place of `_DASH_VARNAME_RE.match(x)`; at 6364-6366 replace the inline `re.fullmatch` with `_dash_is_stata_name(varname)` and keep the `# Security:` comment, extending it to say why `isidentifier()` is sufficient (no brace, quote, blank, `$` or backtick can pass); delete `_DASH_VARNAME_RE` (19207) and its entry in the served constants list (24372); add `"_dash_is_stata_name"` to the served functions list immediately after `"_dash_parse_filter_raw"` (24687). Messages are unchanged (Q22: nothing new is printed when a name is honoured). Run the Unicode file, the injection files and the served-name guards.
  ]]></action>
  <verify><![CDATA[`grep -c "_DASH_VARNAME_RE" dash_render.py` prints 0; `python3 -m pytest test/test_unicode_names.py test/test_help_claims_1.py test/test_security_surface.py test/test_filter_label.py test/test_statistical_helpers.py test/test_resource_limits.py -q -k "Unicode or Name or name or tooltip or CarriesEveryName or DefinesEveryName" 2>&1 | tail -3` passes.]]></verify>
  <done>Every renderer name check was `_dash_is_stata_name`, the served app defined it and no longer needed `_DASH_VARNAME_RE`, and every injection test still passed.</done>
</task>

<task type="auto" id="07-15">
  <name>Document and close G5</name>
  <files>dash.sthlp, CHANGELOG.md, BUGS.md</files>
  <action><![CDATA[
    dash.sthlp: at 1108-1109 (filter) and 1194-1197 (dash kpi) add that `{it:varname}` may hold Unicode letters, as any Stata name. CHANGELOG.md: replace, in place, the marker `<!-- WP-28 G5 -->` under the heading `### Fixed in WP-28` (which S01 created directly above `### Fixed after WP-27 (the S3 batch, 24sep2026)`; D2, `sections/index.md` rule R3, section-01 TR-01.7) with one line ending `(WP-28, G5)`: a Unicode variable name (`größe`) now works in `filter()`, `dash kpi`, `by()`, `hover()` and `colorvar()` in both modes, where `filter()` and `dash kpi` refused it with r(198) and the renderers drew no panels, tooltip field, widget or colours; add nothing else anywhere in CHANGELOG.md. BUGS.md: append at the END of the file the closed entry `- [x] Title: Unicode variable names are refused by filter() and dash kpi and ignored by the renderer` with File Names and Line Numbers (dash_parse.mata `_dash_filter_refusal`, `_dash_is_varname`; dash.ado the `dash kpi` pattern 6094-6100; dash_render.py `_dash_is_stata_name` and its six call sites), Description (GAPS2 G5's measured symptom plus research C §4's renderer finding), Suggested fix (the 2916 rule at every site), and `- Resolution: Fixed <ddmonyyyy> (WP-28, G5). filter() and dash kpi read a name by Stata's own rule (Unicode letters, digits, underscore, 32 characters) through _dash_is_varname in dash_parse.mata and an ICU pattern in dash.ado, and every renderer name check (by(), filter(), exclude(), hover(), _drawn_field, colorvar) calls _dash_is_stata_name in both renderers, the served app carrying it in place of _DASH_VARNAME_RE. Pinned by test/test_unicode_names.py::TestFilterOnAUnicodeName::test_a_range_widget_is_built_in_both_modes, test/test_unicode_names.py::TestByOnAUnicodeName::test_panels_are_drawn_in_both_modes, test/test_statistical_options.cscript UN-01.` The title holds no `"`. Then run `python3 -m pytest test/test_tracking_documents.py test/test_help_claims_4.py test/test_resource_limits.py -q -k "Tracking or Closed or Help or help"`, the full pytest suite once in the worktree (`python3 -m pytest test/ -q`, the session's second and last full run), then `test_statistical_options.cscript` and `test_qualifier_in_stata.cscript` through their drivers one after the other; grep the three documents and the message for `claude\|anthropic`; commit every file 07-11 to 07-15 touched (the new pytest file, the cscript, dash_parse.mata, dash.ado, test/program_coverage_map.py, dash_render.py, dash.sthlp, CHANGELOG.md, BUGS.md) on the worktree branch `wp28-s07` as ONE commit, subject ending `(GAPS2 G5)`, body opening with `<scratch>/07-11-failure.txt` and carrying the `Regression:` / `BUGS.md: "<title>" (closed)` lines; the merger lands it on `s3-bugs` with this message (`sections/index.md` step 1); report that landing command without running it.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; both batch logs end in their PASS summaries (`test_statistical_options: ALL CHECKS PASSED` with UN-01..UN-03 tallied clean; every QS case passing) with `grep -c '^r([0-9]*);' <scratch>/run_test_statistical_options.log <scratch>/run_test_qualifier_in_stata.log` printing 0 for each; `grep -c '<!-- WP-28 G5 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, G5)' CHANGELOG.md BUGS.md` prints 1 for each file; `git log -1 --format=%s | grep -c '(GAPS2 G5)'` prints 1 and `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0; `git status --short` prints nothing.]]></verify>
  <done>G5 was closed in BUGS.md naming its tests, both help sentences and the G5 CHANGELOG line were written, and one green commit on the worktree branch `wp28-s07` carried the gap for the merger.</done>
</task>

## Section completion criteria

- `test/test_reserved_names.py::TestTheDashPrefix`, `test/test_internal_column_names.py` and `test/test_unicode_names.py` pass; each regression test in them failed on the pre-fix tree for its recorded reason (`<scratch>/07-01-failure.txt`, `<scratch>/07-11-failure.txt`).
- Every test listed under "Existing tests that pin today's behaviour" is flipped in the G1 commit with a comment, none deleted.
- `test_qualifier_in_stata.cscript` (QS-06 extended) and `test_statistical_options.cscript` (UN-01..UN-03 added) pass under Stata's Python; no new `.cscript` file exists; `test/run_all_cscripts.do` and the hygiene pins are untouched by this section (D11).
- `grep -n '__mlabel\|_x_jit\|_y_jit\|_label__' dash_render.py | grep -v ':[[:space:]]*#'` and `grep -n '_DASH_VARNAME_RE' dash_render.py` print nothing.
- BUGS.md holds closed G1 (with both residuals) and G5 entries in the D3 form naming existing tests; dash.sthlp updated; the `<!-- WP-28 G1 -->` and `<!-- WP-28 G5 -->` markers are replaced by lines ending `(WP-28, G1)` / `(WP-28, G5)`; no AI reference in any commit, entry or help text.
- Two commits on the worktree branch `wp28-s07`, one per gap, subjects ending `(GAPS2 G1)` and `(GAPS2 G5)`, landed on `s3-bugs` by the merger (index.md step 1); the full pytest suite green in the worktree before each; no test-only commit exists (D1).

## Notes

- **Line numbers drift.** 07-04 inserts ~15 lines near 2008 and ~1 near 20277; every later anchor in this section is pre-edit and every site is also named by symbol. Locate by symbol.
- **Commit bodies** use S01 TR-01.9's line forms verbatim: `Regression: test/<file>.py::<Class>::<test> -- failed at 91d97be with <text>` (the QS-06 and UN cases cited as `test/<script>.cscript <CASE-ID>`), `Flipped: <node> -- <old expectation> was wrong because <why>` (one per flipped test, G1 only), `BUGS.md: "<title>" (closed)`; no `Fixture:` line (none here).
- **Shared registries (rules R1-R6).** R2: the served constants list gains the column constants beside `"_ROW_ID_COLUMN"` (24340) and `_DASH_RESERVED_PREFIX` beside `"_DASH_QUAL_PREFIX"` (24390), loses `"_DASH_VARNAME_RE"` (24372); the functions list gains `"_dash_is_stata_name"` after `"_dash_parse_filter_raw"` (24687) — S09 appends its launcher names at the end of the same tuple after this section merges, and the merger resolves the append by hand; `test/program_coverage_map.py` gains one key in alphabetical place. R1: no cscript is registered and no pin moves (D11). R3: BUGS.md entries are appended at the end in merge order; only the G1 and G5 CHANGELOG markers are replaced; dash.sthlp 166-171, 1108-1109 and 1194-1197 belong to this section alone. R4-R6: nothing here.
- **Merge order within batch 1 (`sections/index.md` step 1):** S03 before this section (`test_saved_filter_layers.py`, `test_statistical_helpers.py`), this section before S08 (`_dash_filter_refusal` in dash_parse.mata: S08 factors `_dash_filter_excludes` out of the post-S07 text, so S08's hunk is applied on a tree that already holds TR-07.6's two changed lines).
- **Copy lists.** A constant GlyphMapper reads (every `_DASH_MLABEL_*`, `_DASH_JITTER_*`, `_DASH_PC_ROW_COLUMN`, `_DASH_RESERVED_PREFIX`) must be in the constants list (24326-24428); a function a copied function calls (`_dash_is_stata_name`) must be in the functions list (24466-24687). The guards `TestTheServedAppCarriesEveryName` and `TestTheServedAppDefinesEveryNameItReads` fail at build time when one is missing; a miss that escapes them is a NameError at draw time on the served page.
- **`_DASH_VARNAME_RE` is deleted**, so its copy-list entry must go in the same edit or `getattr(_mod, _name, None)` returns None and the builder raises. Section 14 uses `_dash_is_stata_name` by this name (D10); do not rename it.
- **The QS-06 message needle.** `cert_log_has needle("reserved")` must still match; the new first line keeps the word. P19-11's "the log holds these two lines and nothing else" rule applies to `_dash_cell_cap`, not to this refusal, but keep the refusal at two lines all the same.
- **Bokeh escapes non-ASCII** in the page's JSON (`ö`), so a cscript must decode the page before searching for `größe`; the pytest side reads models, not text.
- **`isidentifier()` and Stata names differ at the edges** (`ª`, `²`, NFKC forms); Stata cannot produce such a name through `rename`, and the hover site's safety property — no brace, quote, blank, `$` or backtick — holds for every identifier. Do not replace it with `\w`-based regex: Python's `\w` admits digits in first position only through `[^\W\d]`, and no `\p{L}` exists in `re`.
- **`ustrregexm` vs `regexm`.** dash.ado's comments (5629-5631) warn that Stata's `regexm` follows the caller's `version`; the KPI pattern is Mata's function and the replacement `ustrregexm` is ICU in every version, so the `{0,31}` avoidance does not apply — the length is still checked separately with `ustrlen` for clarity.
- **Certification homes (D11).** QS-06 grows inside `test_qualifier_in_stata.cscript`; UN-01..UN-03 live in `test_statistical_options.cscript`, whose failures are tallied (the script exits 9 at its summary, it does not stop at the first bad case) and whose page-reading cases sit inside a `c(python_exec)` region, so a run without Python passes them silently: check `c(python_exec)` in the log before reading a clean summary as a pass. No runner block, no hygiene pin, no new file.
- **Stata invocation.** Every run is `scripts/stata_slot.sh <scratch> <scratch>/run_<script>.do` with the two-line driver of "Stata truth" (D6; `sections/BRIEF.md` "Running one cscript", `sections/index.md` step 0a): the wrapper takes one of three `mkdir` slots, sets `STATATMP=<scratch>/tmp/` (trailing slash) and runs CLAUDE.md rule 10's console command; the driver `cd`s into `<repo>/test` because the cscripts load their helpers by relative path; never the GUI, never a bare `stata-mp`, never `make cert` inside a section. The log is `<scratch>/run_<script>.log`; nothing is written into the worktree. The two scripts here take about a minute each; run them one at a time.
- **Worktree and branch (`sections/index.md` step 1).** This section runs in its own worktree on `wp28-s07`; `git merge --no-edit main` and the batch's full run are the merger's steps (index.md step 1); the two commits here are made on `wp28-s07` after the worktree's own full run, and the merger lands each on `s3-bugs` with the task's message.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`, turning every Python cscript into a skip, and a skip is not a pass: check `display c(python_exec)` before trusting a skip; restore with `set python_exec /opt/anaconda3/bin/python3, permanently`.
- **Two full-suite launches per session.** `.claude/hooks/guard-full-suite.sh` refuses a third `python3 -m pytest test/ -q` in one session unless prefixed `FULL_SUITE_RERUN=1`; this section needs exactly two (07-10, 07-15); run only the changed files between tasks.
- **Silence.** No new note anywhere: a Unicode name that is honoured prints nothing (Q22); the only outputs added are refusals.
