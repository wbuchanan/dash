# Section 02: Stata truth helper

> Part of: WP-28 · Gaps: none of its own (the truth reader for B1, B2, B3, B5, B6, B7, D1, G16, X2) · Risk: yellow · Batch: 1 · Depends on: none · Blocks: 13, 14, 15, 16, 18 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **1** · Depends on **none** · Blocks **13, 14, 15, 16, 18** · Risk **yellow** · Commits: one commit (S02)

- D6: task 02-07's `make cert` moves to S19; a section never launches the full cert suite.
- D10: S18 rewires `scripts/extract_axis_truth.do` onto `scripts/svg_truth.py` when it regenerates `axis_truth.json`; S02 only notes the hand-over.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

Eight of the 22 gaps are proved against what twoway *draws*: title, axis-title and legend text (B3, B5, B6, B7), tick label text (B1, G16), marker fills (D1, X2) and the drawn axis extent (B2). Today the repository has no shared way to read a twoway drawing. Research report C §8 counts seven private readers: `scripts/extract_axis_truth.do` parses `<text>`, `<line>` and `<rect>` elements in a 1,000-line `python:` block; `test_help_claims_8.cscript` has `_hc_svg`, `_hc_svg_maxfont` and `_hc_svg_same`; `test_help_claims_2.cscript` searches raw bytes for `>Domestic<`; `test_help_claims_5.cscript` and `test_help_claims_6.cscript` export and read on their own; `test_bug_regressions.cscript` has a Python `_br03_svg`; `test_twoway_option_parity.cscript` counts `>ZQLAB1<` with `_ztp_count`. Each one re-discovers the same facts about Stata's SVG writer, and none of them knows that Stata writes a run of spaces as U+00A0 (report D §11, `svg_options.sthlp:128-137`), so a title with two words can fail an exact match for no visible reason.

For B2 the situation is worse than "no helper": the one committed `.Graph` reading (`natscale_axes_truth.json._meta`, `.Graph.graphs[k].yaxis1.plotregion.yscale.min/max`) gave the *data* range [12, 41] for a graph whose ticks run 10(10)40, not the drawn extent (report A §B2 "Truth already on disk"); `.Graph` has no member called `range_min` (report D §11); and `axis_truth.json` already holds SVG-fitted drawn extents for four `range()` probes that no test reads. DISCOVERY Q14, as amended, settles the method: axis extents come from the SVG, by fitting the pixel-to-data map over the labelled ticks and mapping the plot-region edges (the method of `extract_axis_truth.do:760-790`), and `.Graph.plotregion1.yscale.{min,max,curmin,curmax}` is probed once and used only where it matches the SVG.

After this section there is one reader, `scripts/svg_truth.py`, that every extract script and every certification script uses; a set of Stata programs in `test/cert_svg.do` so a cscript can export a twoway graph and ask about its text, fills and extent in three lines; a smoke fixture, `test/fixtures/svg_truth_smoke.json` plus the exported SVG it was read from, proving the reader on a real Stata drawing and recording the `.Graph` probe's verdict; a pytest module pinning the reader without Stata; and the seven private readers rewired to it where the rewiring can be shown not to change a verdict. Sections 13-16 and 18 write their `extract_*_truth.do` scripts and cscripts against these names and nothing else.

**Test order (CLAUDE.md rule 7): task 02-01 writes every failing test for the section**, runs them against the unmodified tree and records the failure. Tasks 02-02 to 02-06 turn them green a component at a time; 02-07 adds the equivalence pin for `extract_axis_truth.do` and runs the full suite.

## Risk: [yellow] — new shared code that five certification scripts and one truth script come to depend on, with one Stata probe whose answer is unknown

**Why.** The module and the Stata programs are new code with no user-visible surface, which would be green; but the consolidation edits five certification scripts whose verdicts must not move, a Stata run is needed to produce the fixture, and the `.Graph` probe may show that no member equals the drawn extent, in which case section 18 has only the SVG.

**Risk factors.**
1. A rewired cscript reads a different element than its private helper did (a legend key without `text-anchor`, a title with U+00A0) and its verdict flips for a reason that is not a defect.
2. `python:` inside a `.do` file expands a backtick/apostrophe pair as a macro (`extract_axis_truth.do:58-63`), so a regex with a literal backtick silently matches nothing.
3. Concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`, turning every Python cscript into a skip (memory note `project_stata_cert_suite`; RESEARCH "Cross-cutting" 7).
4. The `.Graph` scale members may be empty under `nodraw` or under `set graphics off`, or may hold the data range.

**Mitigation.** Each rewired helper keeps its program name and return shape and is run before and after the edit with the same PASS lines (02-05, 02-06); the reader lives in a `.py` file outside any `python:` block, so backticks in its regexes are safe, and the smoke script's block is checked by a pytest for backticks and Stata calls; at most three Stata sessions run at once and `display c(python_exec)` is checked before a run of skips is believed; the probe records every candidate member under both a drawn and a `nodraw` graph and writes which of them matches the SVG, so a "none" answer is a recorded fact, not a failure.

## Dependencies

- **Depends on:** none. The module reads files; the Stata programs use only `graph export` and `.Graph` members that exist in StataNow 19.5.
- **Blocks:** 13 (textbox: title and axis-title text), 14 (axis labels: tick text), 15 (legend text and order), 16 (colorvar fills), 18 (axis extents).
- **Parallel batch:** 1. **Can run with** every other batch-1 section: it touches no file another batch-1 section edits except `test/run_all_cscripts.do` and `test/test_cscript_hygiene.py` (see Notes on merging).

Why: the four consumers write their truth scripts against the API names below, so the names are fixed here and the consumers are not started until this section's tests are green.

## Evidence

### What Stata's SVG writer emits (report D §11, measured in `extract_axis_truth.do:44-56`)

- The plotregion is a solid-fill `<rect>` written before its border; regions come outermost first (canvas, graphregion, plotregion, legend / by-panel regions).
- Each tick is a short black `<line>` touching a plotregion edge; each tick label is a `<text>` whose `x` (x axis) or `y` (y axis) is at the tick.
- Gridlines are dashed multi-segment `<line>` groups.
- Legend keys are `<text>` elements **without** `text-anchor`; titles and labels carry `font-size:NNpx` inside `style` (`test_help_claims_8.cscript:229-236`).
- Colours are `stroke:#RRGGBB` / `fill:#RRGGBB` in upper case; sttrans's `%20` becomes `fill-opacity 0.20` (`dash_render.py:4110-4111`).
- `nbsp(on)` is the default (`svg_options.sthlp:128-137`): a run of spaces inside a string is written as U+00A0. `pre(off)`; `version(on)` writes the Stata version; `ignorefont(off)` writes `font-family`; subscripts use `dy`.
- No `.svg` is checked into the repository.

### The fitting method to generalise (`scripts/extract_axis_truth.do`)

The header (1-63) explains why a `.gph` is not a tick oracle (it stores `.xaxis1.major.suggest_ticks 10`, a request) and why the SVG is. `parse_svg` (484-593) collects `texts` (x, y, anchor, rotate, font_size, fill, font_family, text via `html.unescape`), `hlines`/`vlines`/`diaglines`, `rects`, the `viewBox` canvas and the first solid-fill non-canvas rect as `plotregion`. `label_value` (595-600) turns a label into a number (`−` to `-`, commas stripped). `axis_facts` (627-792) finds the tick marks at a plotregion edge, the nearest row or column of `<text>` as the labels, then fits:

```python
 751    pairs = [(px, label_value(l)) for px, l in zip(lab_px, labels)
 752             if l is not None and label_value(l) is not None]
 754    if len(pairs) >= 2:
 755        for space in ("linear", "log10"):
 ...
 764            slope = (v1 - v0) / (p1 - p0)
 765            resid = max(abs((v - v0) - slope * (px - p0)) for px, v in pp)
 767            if resid / scale < 1e-3 or len(pp) == 2:
 ...
 771                if which == "x":
 772                    lo, hi = inv(pr["left"]), inv(pr["right"])
 773                else:
 774                    lo, hi = inv(pr["bottom"]), inv(pr["top"])
 775                out["mapping"] = {
 ...
 781                    "axis_low": min(lo, hi),
 782                    "axis_high": max(lo, hi),
 783                    "reversed": bool(hi < lo),
```
```

The fixture's own description of the method (1148-1153): "axis_low / axis_high are the DATA values at the two plotregion edges, obtained by inverting the tick-pixel -> tick-value map." The values on disk that section 18 will assert against (`test/fixtures/axis_truth.json`, `probes[id].y_axis.mapping`):

| Probe | Option | axis_low | axis_high |
|---|---|---|---|
| `b_default` | none | 9.12 | 41.88 |
| `b_range_0` | `yscale(range(0))` | −1.16 | 42.16 |
| `b_range_60` | `yscale(range(60))` | 8.58 | 61.42 |
| `b_range_narrow` | `yscale(range(20 30))` | 9.12 | 41.88 |
| `b_range_0_50` | `yscale(range(0 50))` | −1.42 | 51.42 |

The trap the header records (58-63): a literal backtick inside a `python:` block is eaten by macro expansion; every regex there spells it `\x60`. The block never calls Stata: `SFIToolkit.stata()` from a do-file block desynchronises the interpreter (52-55).

### The `.Graph` members (report D §11)

`scale.class:19-27` holds `min`, `max` ("permanent"), `curmin`, `curmax` ("temporary"); `axis.class:179-183` reads `.plotregion.yscale.min/.max`; `tickset_g.class:246-252` widens a degenerate range and pushes the tick range into the scale with `.scale.addcur`. Candidate paths: `.Graph.plotregion1.yscale.{min,max,curmin,curmax}` and `.Graph.yaxis1.major.{min,max,delta}`. The one reading in a cscript today is `test_help_claims_6.cscript:689-693`:

```stata
 690    quietly twoway `t' mpg weight in 1/3, name(hc6b, replace)
 691    local m0 "`.hc6b.plotregion1.yscale.curmin'"
 692    quietly twoway `t' mpg weight in 1/3, base(0) name(hc6b, replace)
 693    local m1 "`.hc6b.plotregion1.yscale.curmin'"
```

which asserts `curmin` is "17" by default and "0" with `base(0)` on three cars with mpg 17-22: so `curmin` is populated after a batch-mode draw, and on that graph it is the **data** minimum, not a drawn extent (twoway's y axis there "stops at 17"). Note the object name: a graph made with `name(hc6b)` is `.hc6b`; the current graph is `.Graph`.

### The seven private readers (report C §8), what each reads, and its verdict

| Script | Helper | Reads | Used by | Rewired here? |
|---|---|---|---|---|
| `scripts/extract_axis_truth.do` | `parse_svg`, `label_value`, `line_groups`, `axis_facts` (484-792) | texts, lines, rects, plotregion, tick fit | `test_axis_options.py` through `axis_truth.json` | **No** (pinned for equivalence, 02-07; see Boundaries) |
| `test/test_help_claims_8.cscript` | `_hc_svg` (354-366) exports; `_hc_svg_maxfont` (229-241) largest `font-size`; `_hc_svg_same` (161-171), `_hc_svg_path`, `_hc_svg_moves`, `_hc_svg_x_sorted`, `_hc_ndiff3` compare `<path>` data | export; text size; paths | HC8-03/04/05 (440-470), HC8-13 (613-627) | export and maxfont: yes; path readers: kept (out of the reader's remit) |
| `test/test_help_claims_2.cscript` | `_hc2_rawhas` (192-202) byte search | `>Domestic<`, `>1</text>` at HC2-41 (1020-1029) | HC2-41a/b | the two SVG uses: yes; its BOM/CRLF uses at HC2-40: kept |
| `test/test_help_claims_5.cscript` | `_hc5_svg` (217-228) | export of the current graph | HC5 cases | yes |
| `test/test_help_claims_6.cscript` | `_hc6_first_r` (about 1000-1013) first `<circle r=`; inline exports at 1015-1020 | marker radius | HC6-53 | export: yes; radius: kept |
| `test/test_bug_regressions.cscript` | `_br03_svg` (python, 519-548) | y labels left of the axis, horizontal gridlines | BR-03 | yes |
| `test/test_twoway_option_parity.cscript` | `_ztp_count` (Mata about 610-622, program 641-646) byte count | `>ZQLAB1<` (745), `>ZQFOR<`/`>ZQDOM<` (798-800), `stroke:#FF0000` (842) | TP-09/10/11 | the three text counts: yes; the stroke count and its HTML uses (`_ztp_labelsets`, `_ztp_redline`): kept |

`scripts/extract_scheme_truth.py` is listed with them in report C but reads scheme files, not SVG (its SVG mentions are measurements quoted in its docstring); it is not touched.

### The certification-helper pattern to follow (`test/cert_helpers.do`)

The header (1-40) explains why a file's content must never reach a macro: Bokeh's JSON holds `"` and `` `" `` sequences that end a compound quote, and "the content was being parsed as Stata code". Mata reads the file whole (`_cert_read`, 1 MB pieces, because `fget()` returns a 32,768-character line in pieces) and programs return only numbers: `cert_file_has` → `r(found)`, `cert_log_has` → `r(found)`, `r(count)`, `cert_file_count` → `r(count)`; each is `rclass` and so **clobbers `r()`** (memory note: `cert_file_has clobbers r()`). A file that cannot be opened is `exit 603`, never "absent". `test_conformance.cscript` C-00 (81-148) holds the helpers to what they claim on files of known content. `cert_helpers.do` sets `global dash_nobrowser 1` because `cscript` drops every global (48-58).

### Guards that shape the deliverables

- `test/test_cscript_hygiene.py:282-296` pins `len(_CSCRIPTS) == 65`; `:418` requires every cscript to be registered in `test/run_all_cscripts.do`; `:296-310` lists the scripts that skip for Python; `:400` refuses `"\`ln'"`-style expansion of a line read from a file; `:507` refuses a macro expanded inside a Python string literal on a `python:` line (ado files; followed here as a rule).
- `test/test_fixtures_are_committed.py`: every file under `test/fixtures` must be tracked by git (`.git/info/exclude` hides `*.json` and `*.txt`, so `git add -f`) and named by a test file or cscript (`_named_by`, 155-166); every `.do` under `test/` must be named by another script (`test_every_do_file_is_named_by_another_script_or_test`, 240-249). git tracks 38 files under `test/fixtures` today.
- `test/run_all_cscripts.do`: one block per script (`[ RUN ]`, `do`, rc 222 → `[ SKIP]`, 0 → `[ PASS]`, else `[ FAIL]`), the last is #65 `test_ci_band_options.cscript`; `scripts/cert_verdict.py` counts `do "<name><![CDATA[.cscript"` lines as registrations.
- `test/function_test_map.py` covers `dash_render.py` only (`test_function_test_map.py:62`); `test/program_coverage_map.py` covers `dash.ado`, `dash_setup.ado` and `dash_parse.mata` only (`test_no_orphans.py:52-53`). Neither reaches `scripts/svg_truth.py` or `test/cert_svg.do`; rule 3 is met for them by `test/test_svg_truth.py` and `test/test_cert_svg.cscript` directly.

### Existing tests that pin today's behaviour (flip, never delete)

- `test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script` — `65` becomes `66` when `test_cert_svg.cscript` lands (02-03).

No other test's expected value changes: the five rewired cscripts keep every `PASS` line, and `axis_truth.json` is not regenerated.

## User stories

- **US-02.1** As the maintainer, I want one reader for twoway's exported drawing so that every fixture in WP-28 measures title, label, legend, fill and extent the same way and a fix in the reader reaches every fixture.
- **US-02.2** As the maintainer writing a certification script, I want to export a twoway graph and ask "does it draw this text", "what colours does it fill with" and "where does its y axis end" in three commands that return through `r()`, so that a cscript for B3, B5 or X2 is a page, not a private parser.
- **US-02.3** As the maintainer, I want to know which `.Graph` member, if any, is the drawn axis extent, measured once and recorded beside the SVG's answer, so that section 18 does not build on a member that holds the data range.
- **US-02.4** As the maintainer, I want the reader pinned by pytest against a committed Stata drawing so that a change to the reader is caught on any machine without running Stata.
- **US-02.5** As the Stata user pasting twoway syntax, I want dash's claim "the same picture as twoway" to rest on twoway's own drawing, so that a text or colour dash draws differently is a measured defect, not an opinion.

## Business requirements

- **BR-02.1** Every `<text>` element of a Stata SVG is read with its text (U+00A0 read as a space, entities decoded), position, font size, anchor and fill, and an exact text match succeeds for any string twoway drew, including one with two consecutive spaces.
- **BR-02.2** The fill colours of a drawing are reported grouped by colour with the number of elements each fills and the element kinds, marker fills separable from region rectangles, opacity carried, colour case-insensitive.
- **BR-02.3** The drawn extent of an axis is the data value at each plot-region edge, fitted over the labelled ticks (linear, else log10), and equals what `extract_axis_truth.do` computes on the same SVG.
- **BR-02.4** When the tick labels are text (`xlabel(1 "2019" 2 "2020")`), the caller can supply the tick values in label order and still get the extent.
- **BR-02.5** A cscript reports through `r()` and files; no byte of an SVG is ever expanded into a macro; a file that cannot be opened is `r(603)`.
- **BR-02.6** The `.Graph` scale and tick members are recorded for a drawn and a `nodraw` graph, with which of them matches the SVG-fitted extent, or "none".
- **BR-02.7** The five rewired certification scripts print the same `PASS` lines before and after the rewiring; `axis_truth.json` is byte-identical.
- **BR-02.8** The fixture is produced by a script whose Python never calls Stata and holds no backtick, is committed with `git add -f`, and is named by a test.
- **BR-02.9** A missing fixture or a missing `node`-free dependency fails; nothing in this section skips.

## Technical requirements

### TR-02.1 `scripts/svg_truth.py` — the reader (stdlib only: `re`, `html`, `math`, `json`, `collections`)

Public names (fixed; consumers are written against them):

| Name | Signature | Returns |
|---|---|---|
| `normalise_text` | `(s: str) -> str` | `html.unescape(s)` then `" "` → `" "`, nothing else (runs of spaces are kept) |
| `svg_document` | `(path) -> dict` | `{"texts", "hlines", "vlines", "diaglines", "rects", "circles", "paths", "canvas", "regions", "plotregion", "axis_line", "version"}` — `parse_svg` lifted, plus `circles` (`cx`, `cy`, `r`, `fill`, `stroke`, `fill_opacity`, `stroke_opacity`), `paths` (`d`, `fill`, `stroke`, opacities) and the `<desc>`/version line |
| `svg_texts` | `(path) -> list[dict]` | one dict per `<text>` in document order: `text` (normalised), `raw`, `x`, `y`, `size` (px, from `font-size`), `anchor` (`None` when absent), `fill` (lower-case `#rrggbb` or `None`), `rotate`, `font_family` |
| `svg_has_text` | `(path, text, *, lower=False) -> int` | the number of `<text>` elements whose normalised text equals `text` (case-insensitive under `lower`) |
| `svg_fills` | `(path, *, elements=("circle", "path", "polygon", "rect")) -> dict` | `{colour: {"n": int, "kinds": {"circle": k, ...}, "opacity": sorted list of distinct fill-opacity values}}`; colour lower-cased; `none` and absent fills excluded |
| `svg_marker_fills` | `(path) -> dict` | `svg_fills(path, elements=("circle", "path", "polygon"))` — rects (canvas, regions, bars) excluded |
| `svg_lines` | `(path) -> dict` | `{"h": [...], "v": [...], "diag": [...]}` with `x1`, `y1`, `x2`, `y2`, `stroke` (lower-case), `width`, `dasharray`; `line_groups(lines, coord)` lifted as a public helper |
| `svg_plotregion` | `(path) -> dict | None` | `{"left", "top", "right", "bottom", "fill", "source"}` — the first solid-fill non-canvas rect, else the axis-line box |
| `label_value` | `(s) -> float | None` | lifted verbatim |
| `svg_axis_extent` | `(path, axis, tick_values=None) -> dict | None` | `axis` is `"x"` or `"y"`; `{"low", "high", "space", "reversed", "tick_px", "tick_labels", "tick_values", "residual", "plotregion", "n_ticks"}`; `None` when fewer than two ticks pair with a value, with the reason in `svg_axis_extent.last_reason` (a module-level `LAST_REASON` string is acceptable) |
| `fit_axis_mapping` | `(pairs, edge_start, edge_end) -> dict | None` | the fit of 751-784 on `[(px, value)]`, trying linear then log10 with the `1e-3` residual rule; returns `low`, `high`, `space`, `reversed`, `residual`, `units_per_px` |

Rules:
- `svg_axis_extent` locates ticks and labels exactly as `axis_facts` does (black short lines at the near edge; the row or column of text nearest that edge; nearest-text pairing within 250 px). When `tick_values` is given it must have one entry per tick pixel in axis order (left to right, bottom to top) and replaces `label_value(label)`; a length mismatch raises `ValueError` naming both counts.
- Every colour string is lower-cased at read time; Stata writes `#FF0000`, dash's scheme tables write `#ff0000`.
- `svg_texts` never drops an element: a legend key without `text-anchor`, a rotated axis title, an empty `<text></text>` are all returned.
- The module has no import of `sfi`, `pandas`, `numpy` or `dash_render`; it must import under Stata's Python 3.13 and the development 3.14.
- Backticks may appear in the module's regexes (it is a `.py` file); they may not appear in any `python:` block that imports it.
- Imported by pytest as `sys.path.insert(0, os.path.join(_ROOT, "scripts")); import svg_truth`; by a do-file block as `sys.path.insert(0, Macro.getGlobal("ZS_REPO") + "/scripts")`; by `cert_svg.do` as described in TR-02.2.

### TR-02.2 `test/cert_svg.do` — the Stata programs

Loaded with `quietly do "cert_svg.do"` from `test/` **after `cscript` and before any `cd`**, exactly as `cert_helpers.do` is. On load it: sets `global dash_nobrowser 1` (so a script that loads only this file still satisfies `test_cscript_hygiene.py`'s nobrowser rule); computes `global cert_svg_scripts "<abs path of c(pwd)>/../scripts"` and `confirm file "${cert_svg_scripts}/svg_truth.py"` (else `display as error` and `exit 601`); if `c(python_exec)` is empty, `display as error "SKIP: Python not available."` and `exit 222`; then runs **one** top-level `python:` … `end` block that does `sys.path.insert(0, Macro.getGlobal("cert_svg_scripts"))`, `import svg_truth`, and defines the functions `_cert_svg_texts()`, `_cert_svg_has_text()`, `_cert_svg_fills()`, `_cert_svg_extent()`. Each Stata program is a one-line `python: _cert_svg_xxx()` call; the function reads its arguments with `Macro.getLocal(...)` and answers with `Macro.setLocal(...)`/`Scalar.setValue(...)`. (A `python:` block cannot sit inside `program define`: its `end` ends the program. The one-liner form runs in the same interpreter, so functions defined at load time persist.) No macro is interpolated into Python source; no backtick appears in the block.

Every program is `rclass` and **clobbers `r()`**, like `cert_file_has`: a caller saves what it needs from `r()` first. Say so in each program's header comment.

| Program | Syntax | Returns |
|---|---|---|
| `cert_svg_export` | `cert_svg_export [, name(graph) file(path)]` | `r(rc)` of `graph export`; `r(file)` the absolute path written. `name()` defaults to the current graph. `file()` defaults to `c(tmpdir)dash_cert_svg/<name or Graph>.svg`; a bare file name (no `/`) is placed under that directory (created with `capture mkdir`); an absolute path is used as given. Runs `capture graph export "<file>", [name(<graph>)] replace as(svg)` and does **not** drop the graph. |
| `cert_svg_texts` | `cert_svg_texts, file(path) [list(path)]` | `r(n)` texts; `r(list)` a JSON-lines file (default `<file>.texts.jsonl`), one object per `<text>` with the `svg_texts` keys; `r(maxsize)`, `r(minsize)` the extreme font sizes (missing when no text). |
| `cert_svg_has_text` | `cert_svg_has_text, file(path) text(string) [lower]` | `r(found)` 0/1; `r(count)` the number of matching elements. Exact match on the normalised text, whole element. The text is passed through `Macro.getLocal("text")`, never inlined. |
| `cert_svg_fills` | `cert_svg_fills, file(path) [markers list(path)]` | `r(n)` distinct colours; `r(colours)` the colours space-separated in descending count order (hex tokens, safe to expand); `r(list)` a tab-separated file `colour<TAB>n<TAB>kinds<TAB>opacities` (default `<file>.fills.tsv`). `markers` restricts to `svg_marker_fills`. |
| `cert_svg_extent` | `cert_svg_extent, file(path) axis(x|y) [values(numlist)]` | `r(low)`, `r(high)`, `r(space)` (`linear`/`log10`), `r(reversed)`, `r(n_ticks)`; all missing and `r(reason)` set when the fit is impossible. `values()` is `tick_values`. |
| `cert_graph_scale` | `cert_graph_scale, axis(x|y) [name(graph)]` | `r(min)`, `r(max)`, `r(curmin)`, `r(curmax)` from `.<obj>.plotregion1.<axis>scale.*`; `r(major_min)`, `r(major_max)`, `r(major_delta)` from `.<obj>.<axis>axis1.major.*`; each read under `capture` and left missing when the member is empty or absent. `<obj>` is `Graph` by default, else the `name()`. No Python. |

A file that cannot be read is `exit 603` with the path, as `cert_file_has` does. `cert_svg_export` with no graph in memory returns `r(rc)` = the `graph export` code and prints nothing.

### TR-02.3 `scripts/extract_svg_truth_smoke.do` → `test/fixtures/svg_truth_smoke.json` and `test/fixtures/svg_truth_smoke.svg`

Header in the style of `extract_axis_truth.do:1-63`: purpose, the run command, the two traps (no Stata from Python; `\x60`). Body:

1. `clear all`, `set graphics off`, `set more off`; globals `ZS_REPO`, `ZS_OUT`, `ZS_SVG` (the committed copy `test/fixtures/svg_truth_smoke.svg`), `ZS_WORK` (`c(tmpdir)dash_svg_smoke`, made with `capture mkdir`); record `c(stata_version)`, `c(flavor)`, `c(edition_real)`, `c(born_date)`, `c(current_date)`, `c(scheme)`.
2. `quietly do "${ZS_REPO}/test/cert_svg.do"` — the smoke run proves the Stata programs too. (`cert_svg.do` computes its scripts directory from `c(pwd)`, so the script first does `cd "${ZS_REPO}/test"`, loads it, and `cd`s back; record the fact in a comment.)
3. `sysuse auto, clear`, then exactly:
   ```stata
   twoway (scatter mpg weight if foreign == 0) (scatter mpg weight if foreign == 1), ///
       title("Smoke  title") ytitle("Miles per gallon") ///
       legend(order(1 "Domestic cars" 2 "Foreign cars")) ///
       yscale(range(0 60)) name(zsvg, replace)
   ```
   (two spaces in the title on purpose: the U+00A0 case.)
4. `cert_svg_export, name(zsvg) file("${ZS_WORK}/smoke.svg")`; assert `r(rc) == 0`; `copy "<r(file)>" "${ZS_SVG}", replace`.
5. `cert_graph_scale, axis(y) name(zsvg)` — write every returned value to the record file as `PROBE|drawn|y|min|max|curmin|curmax|major_min|major_max|major_delta`; the same for `axis(x)`. Then `twoway ..., nodraw name(zsvgn, replace)` with the same options and `cert_graph_scale ... name(zsvgn)` → `PROBE|nodraw|...`.
6. `cert_svg_texts`, `cert_svg_has_text` for the title, the y title and each legend text, `cert_svg_fills, markers`, `cert_svg_extent, axis(y)` and `axis(x)` — each written to the record file as `CERT|<program>|<values>` so the fixture pins what the *programs* returned as well as what the module returns.
7. One trailing `python:` block: reads the record file with `Macro.getGlobal`, `sys.path.insert(0, ZS_REPO + "/scripts")`, `import svg_truth`, reads `ZS_SVG` through the module, and writes the fixture with `json.dump(doc, fh, indent=2, sort_keys=True)`. Keys:
   - `_meta`: `stata_version`, `flavor`, `edition`, `born`, `date`, `scheme`, `command`, `script`, `svg` (`"test/fixtures/svg_truth_smoke.svg"`).
   - `texts`: `svg_texts` output in full.
   - `title`: `{"text": "Smoke  title", "found": n}`; `ytitle`: the same for `"Miles per gallon"`; `legend`: `{"texts": [...], "found": [...]}` for the two labels.
   - `marker_fills`: `svg_marker_fills` output (two colours expected under the current scheme, 52 and 22 elements).
   - `y_extent`, `x_extent`: `svg_axis_extent` output.
   - `graph_probe`: `{"drawn": {"y": {...}, "x": {...}}, "nodraw": {...}}` from the `PROBE` records, missing written as `null`.
   - `matches_svg`: for each candidate pair (`plotregion1.yscale.min/max`, `.curmin/.curmax`, `yaxis1.major.min/max`), `true` when both ends are within `0.005 × (high − low)` of `y_extent`, else `false`; and `"drawn_extent_member"`: the first matching name or `"none"`.
   - `cert_programs`: the `CERT` records, so the pytest can hold `cert_svg_*` to the module.
   - `unverified`: anything a step could not establish, with the reason.
8. `display "WROTE ${ZS_OUT}"`.

### TR-02.4 `test/fixtures/svg_truth_tiny.svg` — a hand-written SVG in Stata's dialect

About 40 lines: a `viewBox`, a white canvas rect, a plotregion rect (`fill:#FFFFFF`), four black tick lines at the left edge with labels `0`, `10`, `100`, `1000` (so a log fit is needed), three black tick lines at the bottom with labels `2019`, `2020` and a text label `"Q3"` (so `tick_values` is needed), a title `Two&#160;words` written with the entity **and** a second text with a literal U+00A0 byte, a text with `text-anchor="middle"`, a legend key with no anchor, a rotated y title (`transform="rotate(-90 ...)"`), three `<circle>` with `fill:#1A476F`, one with `fill:#90353B;fill-opacity:0.20`, one `<path>` with `fill:#90353B`, a dashed gridline group and one diagonal line. It is not a Stata export; it exists so every branch of the reader has a pin that Stata did not write.

### TR-02.5 `test/test_svg_truth.py` — one test per function (rule 3)

Loads the module and the three fixtures; **fails, never skips**, when a fixture is missing (`pytest.fail("section 02 fixture missing: ...")`, as `test_axis_options.py:40-47` asserts). Classes and tests are listed under TDD test stubs.

### TR-02.6 `test/test_cert_svg.cscript` — the programs held to their claims

Registered as script #66 in `test/run_all_cscripts.do` (a block copied from #65's, name changed); `test_cscript_hygiene.py:294` count bumped to 66. Loads `cert_helpers.do` and `cert_svg.do`; gates on `c(python_exec)` (exit 222). Cases CS-01 … CS-08 under TDD test stubs. It names `svg_truth_smoke.json` and `cert_svg.do` in its text, which is what `test_fixtures_are_committed.py` needs.

### TR-02.7 Consolidation edits (BR-02.7)

| Script | Edit |
|---|---|
| `test_help_claims_8.cscript` | `_hc_svg` keeps its name and arguments; its `graph export` line becomes `cert_svg_export, name(_hcg) file("<file>")` and `r(rc)` is taken from it. `_hc_svg_maxfont` calls are replaced by `cert_svg_texts, file(...)` then `r(maxsize)` (HC8-04, 456-458). `_hc_svg_same` and the path readers stay. Load `cert_svg.do` beside `cert_helpers.do` (83), before the `cd "\`hc_dir'"` at 259. |
| `test_help_claims_2.cscript` | HC2-41a/b (1021-1029): the two `graph export` lines become `cert_svg_export, file("<svg>")`; `_hc2_rawhas(svg, "Domestic")` (1023, 1028) becomes `cert_svg_has_text, file("<svg>") text("Domestic")` → `r(found)`; `_hc2_rawhas(svg, ">1</text>")` becomes `cert_svg_has_text ... text("1")`. `_hc2_rawhas` stays for HC2-40. |
| `test_help_claims_5.cscript` | `_hc5_svg` (217-228): `quietly graph export "\`path'", replace` becomes `cert_svg_export, file("\`path'")`; `r(rc)` unchanged in meaning. |
| `test_help_claims_6.cscript` | HC6-53 (1015-1020): the two `graph export ... name(hc6s)` lines become `cert_svg_export, name(hc6s) file(...)`. `_hc6_first_r` stays. |
| `test_bug_regressions.cscript` | `_br03_svg` (519-548) keeps its name and `(sorted labels, sorted grid)` return; its body becomes: `sys.path.insert(0, os.path.dirname(Macro.getGlobal("br03_render")) + "/scripts")`, `import svg_truth`, `doc = svg_truth.svg_document(path)`; labels = the numeric `svg_texts` left of the longest black vertical line (`doc["axis_line"]["v_x"]`), grid = horizontal lines not black spanning at least half the canvas width. The two `graph export` lines at 495/498 become `cert_svg_export, name(br03) file(...)`. |
| `test_twoway_option_parity.cscript` | The three `_ztp_count "\`svgfile'" ">ZQLAB1<"`/`">ZQFOR<"`/`">ZQDOM<"` calls (745, 798, 800) become `cert_svg_has_text, file("\`svgfile'") text("ZQLAB1")` (etc.) with `r(count)` in place of `r(n)`; the `graph export` lines at 743/796/840 become `cert_svg_export, file("\`svgfile'")`. `_ztp_count` stays for `stroke:#FF0000` (842) and the page counts. |

Each of the six scripts loads `cert_svg.do` right after `cert_helpers.do`. Before and after each edit the script is run alone (Stata invocation below) and its `PASS`/`FAIL` lines diffed; the diff must be empty.

### TR-02.8 Documentation and tracking

No gap closes here, so no BUGS.md entry, no `dash.sthlp` paragraph and no CHANGELOG line are written in this section; section 19 records the tooling under WP-28. The module docstring and `cert_svg.do` header are the documentation: each states the invocation rule (CLAUDE.md rule 10), `STATATMP=<dir>/tmp/` with the trailing slash, `git add -f` for fixtures, that `test_fixtures_are_committed.py` requires a test to name each fixture, and that a do-file's `python:` block never calls Stata and writes a backtick as `\x60`.

## Boundaries

- **Do not regenerate `test/fixtures/axis_truth.json`** and do not edit the `python:` block of `scripts/extract_axis_truth.do`. Its fixture is committed and cannot be re-checked without a full Stata re-run; section 18 extends and re-runs that script and is the point at which switching it to the module is safe. This section pins the two readers to each other instead (02-07).
- Do not touch `dash_render.py`, `dash.ado`, `dash_parse.mata`, `dash.sthlp`, `CHANGELOG.md`, `BUGS.md`, `ROADMAP.md`.
- Do not change what any cscript asserts; only how it reads an SVG. The path, radius and byte readers named "kept" above stay as they are.
- Do not add probes for other sections' gaps to the smoke script. Sections 13-16 and 18 write their own `scripts/extract_*_truth.do` against `svg_truth` and `cert_svg.do`; the smoke script stays one command.
- Do not implement any gap's fix (B2's hull, B1's parser, D1's quote-strip); this section reads truth, it does not draw.
- Do not call Stata from a Python block, and do not launch the GUI (rule 10; `.claude/hooks/block-stata-gui.sh`).
- Do not add a `pytest.mark.skipif` anywhere in this section: a missing fixture, module or Python is a failure (PRD §8 "no skips").

## Stata truth

**Script:** `scripts/extract_svg_truth_smoke.do` → `test/fixtures/svg_truth_smoke.json` and `test/fixtures/svg_truth_smoke.svg`. One twoway command (TR-02.3 step 3). Probes: `cert_graph_scale, axis(y|x)` on the drawn and the `nodraw` graph; `cert_svg_*` on the export.

**Invocation** (CLAUDE.md rule 10; RESEARCH "Cross-cutting" 7), from a scratch directory that is not the log's directory of any other run:

```sh
S=<scratch>/s02 && mkdir -p "$S/tmp" && cd "$S" && \
STATATMP="$S/tmp/" arch -arm64 /usr/local/bin/stata-mp -b do \
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_svg_truth_smoke.do
```

`STATATMP` carries the trailing slash and is not the directory the batch log is written to (`$S`). Never `open -a StataMP`, never the GUI binary. At most three Stata sessions at once; if a cscript run shows a wall of `[ SKIP]` in under a second, run `display c(python_exec)` in a fresh batch session before believing it, and restore with `set python_exec /opt/anaconda3/bin/python3, permanently` if it is empty.

**A cscript alone** (used by TR-02.7's before/after diff and by 02-03):

```sh
S=<scratch>/s02-cert && mkdir -p "$S/tmp" && cd /Users/billy/Desktop/Programs/StataPrograms/d/dash/test && \
STATATMP="$S/tmp/" arch -arm64 /usr/local/bin/stata-mp -b do test_cert_svg.cscript && \
grep -E "PASS|FAIL" test_cert_svg.log
```

(A cscript is run from `test/` because it loads `cert_helpers.do` by relative path; the log then lands in `test/`, which `.git/info/exclude` hides through `*.log`.)

**Fixture keys added:** the whole of `svg_truth_smoke.json` (TR-02.3 step 7) and the SVG it was read from. **Commit with** `git add -f test/fixtures/svg_truth_smoke.json test/fixtures/svg_truth_smoke.svg test/fixtures/svg_truth_tiny.svg` (`*.svg` is not excluded, `-f` is harmless). `test/test_svg_truth.py` names all three by file name and `test/test_cert_svg.cscript` names the JSON, which satisfies `test_fixtures_are_committed.py`.

## TDD test stubs

All pytest stubs live in `test/test_svg_truth.py`; the cscript cases in `test/test_cert_svg.cscript`. The first group are the section's regression tests: every one fails at `91d97be` — the pytest module with `ModuleNotFoundError: No module named 'svg_truth'` (collection fails at import: record that as the failure), the cscript with `r(601)` on `do "cert_svg.do"`.

- Test: `test_svg_truth.py::TestTexts::test_nbsp_is_read_as_a_space` — the tiny SVG's `Two&#160;words` and the literal-U+00A0 element both normalise to `"Two words"`; `raw` keeps the byte.
- Test: `test_svg_truth.py::TestTexts::test_position_size_anchor_fill_and_rotation_are_read` — the middle-anchored title, the anchorless legend key (`anchor is None`), the rotated y title (`rotate == -90`), a `fill` lower-cased.
- Test: `test_svg_truth.py::TestTexts::test_svg_has_text_matches_the_whole_element_exactly_and_lower_optionally`.
- Test: `test_svg_truth.py::TestFills::test_fills_are_grouped_by_colour_with_counts_and_kinds` — `#1a476f` n=3 kinds circle 3; `#90353b` n=2 kinds circle 1 path 1, opacity `[0.2]` beside opaque.
- Test: `test_svg_truth.py::TestFills::test_marker_fills_exclude_rects` — the white canvas and plotregion are absent from `svg_marker_fills`.
- Test: `test_svg_truth.py::TestLines::test_horizontal_vertical_and_diagonal_lines_are_split_and_grouped` — the dashed gridline is one group with `n_segments > 1`.
- Test: `test_svg_truth.py::TestPlotregion::test_the_first_solid_non_canvas_rect_is_the_plotregion`.
- Test: `test_svg_truth.py::TestAxisExtent::test_a_log_axis_is_fitted_in_log_space` — tiny SVG y: `space == "log10"`, `low < 0 + eps` is not required; assert `low` and `high` equal the hand-computed inversion of the four labelled ticks to 1e-6.
- Test: `test_svg_truth.py::TestAxisExtent::test_supplied_tick_values_replace_unreadable_labels` — tiny SVG x with `tick_values=[1, 2, 3]` fits; without them (`"Q3"` unreadable) it fits on the two numeric labels and `n_ticks == 3`.
- Test: `test_svg_truth.py::TestAxisExtent::test_a_length_mismatch_in_tick_values_raises` — `ValueError` naming 3 and 2.
- Test: `test_svg_truth.py::TestAxisExtent::test_fewer_than_two_pairs_returns_none_with_a_reason`.
- Test: `test_svg_truth.py::TestTheSmokeFixture::test_the_module_reads_the_committed_stata_svg_as_the_fixture_records` — `svg_texts`, `svg_marker_fills`, `svg_axis_extent(y)`, `svg_axis_extent(x)` on `svg_truth_smoke.svg` equal the fixture's `texts`, `marker_fills`, `y_extent`, `x_extent` (floats at 1e-9).
- Test: `test_svg_truth.py::TestTheSmokeFixture::test_title_axis_title_and_legend_text_are_found_once_each` — `"Smoke  title"` (two spaces) found exactly once, `"Miles per gallon"` once, `"Domestic cars"` and `"Foreign cars"` once each; and `svg_has_text(svg, "Smoke title")` (one space) is 0.
- Test: `test_svg_truth.py::TestTheSmokeFixture::test_two_marker_fills_of_52_and_22_elements` — auto's 52 domestic and 22 foreign cars.
- Test: `test_svg_truth.py::TestTheSmokeFixture::test_the_y_extent_covers_range_0_60_and_the_x_extent_covers_the_data` — `y_extent.low <= 0`, `y_extent.high >= 60`, `x_extent.low <= 1760`, `x_extent.high >= 4840`.
- Test: `test_svg_truth.py::TestTheSmokeFixture::test_the_graph_probe_is_recorded_with_a_verdict` — `graph_probe.drawn.y` has the seven keys; `matches_svg.drawn_extent_member` is a string, and if it is not `"none"` the named member's values are within the tolerance of `y_extent`.
- Test: `test_svg_truth.py::TestTheSmokeFixture::test_the_cert_programs_agreed_with_the_module` — every `cert_programs` record (`n`, `found`, `count`, `colours`, `low`, `high`) equals the module's answer on the same SVG.
- Test: `test_svg_truth.py::TestTheSmokeFixture::test_the_fixture_names_its_stata_and_scheme` — `_meta.stata_version`, `_meta.scheme`, `_meta.command` present and the command holds `yscale(range(0 60))`.
- Test: `test_svg_truth.py::TestScriptHygiene::test_the_smoke_script_python_block_has_no_backtick_and_no_stata_call` — read the `.do` text from `python:` to `end`; assert no backtick character and no `SFIToolkit.stata`/`stata(`.
- Test: `test_svg_truth.py::TestScriptHygiene::test_cert_svg_do_interpolates_no_macro_into_python` — no `` `...' `` inside the `python:` block of `cert_svg.do`, and every `python:` one-liner is `python: _cert_svg_<name>()`.
- Test: `test_svg_truth.py::TestScriptHygiene::test_the_module_imports_nothing_but_the_stdlib` — walk `ast.parse` of `svg_truth.py` for imports; all in `sys.stdlib_module_names`.
- Test: `test_svg_truth.py::TestEquivalenceWithExtractAxisTruth::test_the_module_reproduces_the_private_reader_on_both_svgs` (added by 02-07) — exec the text between `python:` and the `# .gph parsing` banner of `scripts/extract_axis_truth.do` in a namespace whose `Macro` is a stub; assert `svg_texts(p)` equals `parse_svg(p)["texts"]` after `normalise_text`, and `svg_axis_extent(p, "y")["low"/"high"]` equals `axis_facts(parse_svg(p), "y")["mapping"]["axis_low"/"axis_high"]` to 1e-9, for the smoke SVG and the tiny SVG.

cscript cases (each prints `CS-nn PASS: ...` through a local `_cs_done` in the `_hc_done` style, so `program_coverage_map`-style references can name them later):

- CS-01 `cert_svg_export` on `twoway scatter mpg weight, name(cs1)`: `r(rc) == 0`, `r(file)` exists under `c(tmpdir)dash_cert_svg/`, and `cert_file_has "<file>", needle("<svg")`.
- CS-02 `cert_svg_texts`: `r(n) > 0`, `r(list)` exists with `r(n)` lines, `r(maxsize) >= r(minsize) > 0`.
- CS-03 `cert_svg_has_text` on `title("a  b")` (two spaces): `text("a  b")` found, `text("a b")` not, `text("A  B") lower` found; `r(count) == 1`.
- CS-04 `cert_svg_fills, markers` on `mcolor(red)`: `r(colours)` holds `#ff0000` and its `n` in `r(list)` is 74.
- CS-05 `cert_svg_extent, axis(y)` on the smoke command: `r(low) <= 0`, `r(high) >= 60`, and both within 0.01 of `svg_truth_smoke.json`'s `y_extent` (same Stata, same scheme: read the fixture with `cert_file_has` on the formatted numbers written by the smoke script into `cert_programs`).
- CS-06 `cert_svg_extent, axis(x) values(1 2)` on `xlabel(2000 "low" 4000 "high")`: fits; without `values()` returns missing with `r(reason)`.
- CS-07 `cert_graph_scale, axis(y) name(cs1)` returns numbers for `curmin`/`curmax` on a drawn graph; the member the fixture names in `drawn_extent_member` (if not `none`) matches `cert_svg_extent`'s answer within `0.005 × span`.
- CS-08 `r()` is clobbered: after `summarize mpg`, `cert_svg_texts` leaves `r(mean)` undefined; a missing file is `r(603)` for each program.

**Pinned test to flip** (same commit as 02-03): `test/test_cscript_hygiene.py::TestTheChecksReachEveryScript::test_the_glob_finds_every_script`, 65 → 66, comment extended with "WP-28's test_cert_svg".

**Mutation table** — apply, confirm the named test fails, revert:

| break this | test that must die |
|---|---|
| in `normalise_text`, drop the ` ` replacement | `TestTexts::test_nbsp_is_read_as_a_space`, `TestTheSmokeFixture::test_title_axis_title_and_legend_text_are_found_once_each` |
| in `svg_fills`, stop lower-casing | `TestFills::test_fills_are_grouped_by_colour_with_counts_and_kinds` (tiny SVG writes upper case) |
| in `fit_axis_mapping`, skip the log10 attempt | `TestAxisExtent::test_a_log_axis_is_fitted_in_log_space` |
| in `svg_axis_extent`, map the far edge with the near edge's pixel | `TestTheSmokeFixture::test_the_module_reads_the_committed_stata_svg_as_the_fixture_records`, `TestEquivalenceWithExtractAxisTruth` |
| in `cert_svg_has_text`, compare `raw` not `text` | CS-03 |
| in `cert_graph_scale`, read `.Graph` when `name()` is given | CS-07 (no current `.Graph` after `graph drop _all`) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Every reader function on a hand-written Stata-dialect SVG | pytest `test_svg_truth.py` | `svg_truth_tiny.svg` | n/a (no page) |
| The reader on a real Stata drawing: text, fills, extents | pytest | `svg_truth_smoke.svg`, `svg_truth_smoke.json` | n/a |
| The `.Graph` probe verdict is recorded and consistent | pytest + Stata (smoke script) | `svg_truth_smoke.json` | n/a |
| The reader equals `extract_axis_truth.do`'s private reader | pytest (exec of the script's text) | both SVGs | n/a |
| The Stata programs return what the module returns | cscript `test_cert_svg.cscript` CS-01..08 | `svg_truth_smoke.json` | n/a |
| Script hygiene (no backtick, no Stata call, no inlined macro, stdlib only) | pytest | scripts as text | n/a |
| Five rewired cscripts keep every PASS line | Stata, each script alone, before/after diff | none | n/a |
| Fixtures tracked and named | pytest `test_fixtures_are_committed.py` (existing) | all three | n/a |
| Runner registration and count | pytest `test_cscript_hygiene.py` (existing, flipped) | none | n/a |

Acceptance criteria:

- **AC-02.1** `python3 -m pytest test/test_svg_truth.py -q` passes with 0 skipped under both interpreters (`make test`, `make test-dev`).
- **AC-02.2** `test_cert_svg.cscript` prints CS-01..CS-08 PASS through the console binary and is registered as #66; `scripts/run_cert_suite.sh` reports 66 of 66.
- **AC-02.3** `git diff --stat 91d97be -- test/fixtures/axis_truth.json` is empty; the before/after PASS-line diffs of the six edited cscripts are empty.
- **AC-02.4** `svg_truth_smoke.json` records `matches_svg.drawn_extent_member` and `graph_probe.drawn`/`nodraw`; section 18 can read the verdict without running Stata.
- **AC-02.5** `git ls-files test/fixtures` lists the three new files; `test_fixtures_are_committed.py` passes.
- **AC-02.6** The full suite (`python3 -m pytest test/ -q`) is green once on the merged tree before the section's last commit.

## Tasks

<task type="auto" id="02-01">
  <name>Write the failing tests and the tiny SVG]]></name>
  <files>test/test_svg_truth.py, test/test_cert_svg.cscript, test/fixtures/svg_truth_tiny.svg</files>
  <action>
    Create the pytest module with every class and test named under "TDD test stubs" except `TestEquivalenceWithExtractAxisTruth` (02-07). Header as `test/test_axis_options.py:16-31` (`_HERE`, `sys.path` inserts for the repo root and `scripts/`), a module docstring stating the section's purpose in the terms of the Overview's first paragraph, `pytest.fail(...)` (never skip) for a missing fixture or module, and the three fixture paths spelled by file name so `test_fixtures_are_committed.py` sees them. Write `test/fixtures/svg_truth_tiny.svg` to TR-02.4 with the expected numbers computed by hand in a comment block at the top of the test module (tick pixels, label values, the log10 inversion). Create `test/test_cert_svg.cscript` in the `test_help_claims_8.cscript` style (`cscript "cert_svg: the SVG readers"`, `adopath ++ ".."`, the `c(python_exec)` gate with `exit 222`, `quietly do "cert_helpers.do"`, `quietly do "cert_svg.do"`, `_cs_expect`/`_cs_done` helpers, CS-01..CS-08, a final `if ${cs_nfail} exit 9`). Do not create `scripts/svg_truth.py` or `test/cert_svg.do` in this task. Run the pytest file and the cscript against the unmodified tree; paste the failures (the `ModuleNotFoundError`, the `r(601)`) into the commit message. Commit on `s3-bugs` with no AI reference.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_svg_truth.py -q 2>&1 | tail -5` shows a collection error naming `svg_truth`. Running the cscript alone (Stata truth section) logs `file cert_svg.do not found` and rc 601. `git status --short` lists exactly the three new files.]]></verify>
  <done>The section's tests exist, collect against a module that does not yet exist and fail for that reason, and the hand-written SVG they read is committed.</done>
</task>

<task type="auto" id="02-02">
  <name>Write the shared SVG reader module</name>
  <files>scripts/svg_truth.py</files>
  <action><![CDATA[
    Create `scripts/svg_truth.py` to TR-02.1. Lift `parse_svg` (as `svg_document`, extended with `circles`, `paths` and `version`), `label_value`, `line_groups` and the fit at 751-784 (as `fit_axis_mapping`) from `scripts/extract_axis_truth.do:484-792`, keeping the tick and label location rules of `axis_facts` inside `svg_axis_extent`; add `normalise_text`, `svg_texts`, `svg_has_text`, `svg_fills`, `svg_marker_fills`, `svg_lines`, `svg_plotregion` and the `tick_values` path with its `ValueError`. Lower-case every colour at read time. Module docstring: what Stata's writer emits (the Evidence list), the four rules (rule 10 invocation, `STATATMP=<dir>/tmp/`, `git add -f`, no Stata call and `\x60` in a `python:` block), and the fact that this file may hold backticks because it is not a `python:` block. Give every public function a docstring with its return shape. Stdlib only.
  ]]></action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_svg_truth.py -q -k "TestTexts or TestFills or TestLines or TestPlotregion or TestAxisExtent or TestScriptHygiene" 2>&1 | tail -3` passes every case except the two `TestScriptHygiene` tests that read files 02-03 and 02-04 create; `-k TestTheSmokeFixture` fails on the missing fixture with the `pytest.fail` message, not a skip. `/opt/anaconda3/bin/python3 -c "import sys; sys.path.insert(0,'scripts'); import svg_truth"` prints nothing.]]></verify>
  <done>`scripts/svg_truth.py` exists, imports under both interpreters, and every reader is pinned by the tiny SVG; the smoke tests still fail because no fixture exists.</done>
</task>

<task type="auto" id="02-03">
  <name>Write the Stata programs and register the cscript</name>
  <files>test/cert_svg.do, test/run_all_cscripts.do, test/test_cscript_hygiene.py</files>
  <action><![CDATA[
    Create `test/cert_svg.do` to TR-02.2: header in the `cert_helpers.do` voice (why one reader, why `r()` is clobbered, the load-order rule "after `cscript`, before any `cd`"), `global dash_nobrowser 1`, the scripts-directory global with `confirm file`, the `c(python_exec)` gate, one top-level `python:` block defining `_cert_svg_texts`, `_cert_svg_has_text`, `_cert_svg_fills`, `_cert_svg_extent` (arguments through `Macro.getLocal`, results through `Macro.setLocal`, no backtick, no macro inside a string literal), and the six `rclass` programs, `cert_graph_scale` reading its members under `capture` with `.Graph` or `.<name>`. Append block #66 for `test_cert_svg.cscript` to `test/run_all_cscripts.do` after #65, copied from #65's block. In `test/test_cscript_hygiene.py:294` change 65 to 66 and extend the comment. Run the cscript alone.
  ]]></action>
  <verify><![CDATA[The cscript log shows CS-01, CS-02, CS-03, CS-04, CS-06 and CS-08 PASS and CS-05/CS-07 FAIL only on the missing fixture. `python3 -m pytest test/test_cscript_hygiene.py test/test_fixtures_are_committed.py -q 2>&1 | tail -3` passes (`cert_svg.do` is named by the cscript; the count is 66). `python3 -m pytest test/test_svg_truth.py -q -k test_cert_svg_do_interpolates 2>&1 | tail -2` passes.]]></verify>
  <done>Six certification programs exist, are exercised by a registered cscript, and read every path and needle through `Macro.getLocal`.</done>
</task>

<task type="auto" id="02-04">
  <name>Extract the smoke fixture from Stata</name>
  <files>scripts/extract_svg_truth_smoke.do, test/fixtures/svg_truth_smoke.json, test/fixtures/svg_truth_smoke.svg</files>
  <action>
    Write `scripts/extract_svg_truth_smoke.do` to TR-02.3 (steps 1-8) with the header traps. Run it once with the invocation under "Stata truth" (one session; check `c(python_exec)` if the log shows a Python skip). Inspect the fixture: `matches_svg.drawn_extent_member` must be a string; `marker_fills` must show two colours with 52 and 22; `title.found` must be 1. If `y_extent` is `None`, the tick-label pairing failed on a real drawing: fix `svg_axis_extent` in `scripts/svg_truth.py` (allowed here as the one exception to this task's file list, recorded in the commit message) and re-run. Commit the fixture and the SVG with `git add -f`.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_svg_truth.py -q 2>&1 | tail -3` passes every test but `TestEquivalenceWithExtractAxisTruth` (not yet written), 0 skipped. The cscript alone now prints CS-01..CS-08 PASS. `git ls-files test/fixtures | grep -c svg_truth` prints 3. `grep -c '\x60' scripts/extract_svg_truth_smoke.do` (a literal backtick in the python block) prints 0 for the block's line range.]]></verify>
  <done>A real twoway drawing and the module's reading of it are committed, together with the `.Graph` probe's recorded verdict on which member, if any, is the drawn extent.</done>
</task>

<task type="auto" id="02-05">
  <name>Rewire the help-claims scripts to the shared readers</name>
  <files>test/test_help_claims_8.cscript, test/test_help_claims_2.cscript, test/test_help_claims_5.cscript</files>
  <action><![CDATA[
    Before editing, run each of the three scripts alone (Stata truth section) and save `grep -E "PASS|FAIL" <script>.log` to the scratch directory. Apply the TR-02.7 edits for `test_help_claims_8.cscript` (`_hc_svg` export line, `_hc_svg_maxfont` → `cert_svg_texts` `r(maxsize)` at HC8-04, load `cert_svg.do` at 83 before the `cd`), `test_help_claims_2.cscript` (HC2-41a/b) and `test_help_claims_5.cscript` (`_hc5_svg`). Keep every program name and every `r()` name the callers read; where a caller read `r(n)` from `_ztp`-style helpers, keep `r(n)` by copying `r(count)` into it inside the wrapper. Re-run the three scripts and diff the PASS/FAIL lines against the saved copies: the diff must be empty. Put the three diffs' emptiness in the commit message.
  ]]></action>
  <verify>`diff` of the before/after PASS-FAIL lines is empty for all three scripts; each log ends with its script's own summary line unchanged. `grep -c "cert_svg_export" test/test_help_claims_8.cscript test/test_help_claims_2.cscript test/test_help_claims_5.cscript` prints 1, 2, 1 or more.</verify>
  <done>Three certification scripts export and read SVGs through `cert_svg.do` and print exactly the verdicts they printed before.</done>
</task>

<task type="auto" id="02-06">
  <name>Rewire the regression, parity and claims-6 scripts</name>
  <files>test/test_bug_regressions.cscript, test/test_twoway_option_parity.cscript, test/test_help_claims_6.cscript</files>
  <action>
    Same procedure as 02-05 for `_br03_svg` (body through `svg_truth`, return shape unchanged; exports through `cert_svg_export, name(br03)`), the three `_ztp_count` text calls and three exports in `test_twoway_option_parity.cscript` (TP-09..11), and the two HC6-53 exports in `test_help_claims_6.cscript`. `_br03_svg` imports the module from `os.path.dirname(Macro.getGlobal("br03_render")) + "/scripts"`; the `python:` block it lives in must still contain no backtick. Leave `_ztp_count`, `_ztp_labelsets`, `_ztp_redline` and `_hc6_first_r` in place. Re-run all three and diff as before.
  </action>
  <verify><![CDATA[Before/after PASS-FAIL diffs are empty for all three. `python3 -m pytest test/test_cscript_hygiene.py -q 2>&1 | tail -2` passes (no `"\`ln'"` expansion introduced; every script still registered).]]></verify>
  <done>Every private SVG reader that the shared module can replace has been replaced, and the ones it cannot (path, radius and byte counters) are named as kept.</done>
</task>

<task type="auto" id="02-07">
  <name>Pin the module to extract_axis_truth's reader and run the suite</name>
  <files>test/test_svg_truth.py</files>
  <action><![CDATA[
    Add `TestEquivalenceWithExtractAxisTruth::test_the_module_reproduces_the_private_reader_on_both_svgs`: read `scripts/extract_axis_truth.do`, take the text from the line after `python:` to the line before the `# .gph parsing -- the declarative record` banner, replace the `from sfi import Macro` line with a stub class exposing `getGlobal`, `exec` it in a fresh namespace, and compare its `parse_svg`/`axis_facts` output with `svg_truth`'s on `svg_truth_smoke.svg` and `svg_truth_tiny.svg` as the stub describes. Add a comment naming this as the reason `extract_axis_truth.do` keeps its private copy until section 18 re-runs it. Then run the full suite once under the development interpreter (`python3 -m pytest test/ -q`) and once under Stata's (`make test`), and the certification suite (`make cert`). Fix any regression in the code this section wrote, never by weakening a test. Commit; report the merge command `git checkout main && git merge --no-ff s3-bugs` without running it.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_svg_truth.py -q 2>&1 | tail -2` passes, 0 skipped. `python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no skips beyond those the tree already had at `91d97be` under this interpreter. `sh scripts/run_cert_suite.sh` ends with 66 of 66 registered scripts passed.]]></verify>
  <done>The two readers are held equal by a test that runs without Stata, both suites are green with the section's files in the tree, and sections 13-16 and 18 have `svg_truth`, `cert_svg.do` and a recorded `.Graph` verdict to build on.</done>
</task>

## Section completion criteria

1. `scripts/svg_truth.py` exposes exactly the public names of TR-02.1 with the documented return shapes, and `test/test_svg_truth.py` has a passing test per function.
2. `test/cert_svg.do` exposes `cert_svg_export`, `cert_svg_texts`, `cert_svg_has_text`, `cert_svg_fills`, `cert_svg_extent`, `cert_graph_scale`, each `rclass`, each documented as clobbering `r()`, and `test_cert_svg.cscript` (#66) passes CS-01..CS-08.
3. `test/fixtures/svg_truth_smoke.json` and `.svg` and `svg_truth_tiny.svg` are tracked by git and named by tests; the fixture records the `.Graph` probe and its verdict.
4. The six cscripts of TR-02.7 print unchanged verdicts; `axis_truth.json` is unchanged; the equivalence test passes.
5. `test_cscript_hygiene.py`'s count is 66; both pytest runs and the certification suite are green; no skip was added.
6. No file outside the task lists was modified; no BUGS.md, CHANGELOG or help edit was made.

## Notes

- **Load order.** `cscript` drops every global (cert_helpers.do:48-58), so `cert_svg.do` is loaded after the `cscript` line; it computes its scripts directory from `c(pwd)`, so load it before a script `cd`s away (`test_help_claims_8.cscript` `cd`s at 259).
- **`python:` inside a program.** Not possible (the block's `end` ends the program). Define the functions once at load time, call them as one-liners. The one-liner `python: _cert_svg_texts()` runs in the same interpreter session, so the definitions persist for the whole batch run.
- **Backticks.** The module may hold them; no `python:` block may. `TestScriptHygiene` checks the smoke script and `cert_svg.do`; check any new block by hand the same way.
- **Named graphs.** `.Graph` is the current graph; `name(zsvg)` makes `.zsvg`. `cert_graph_scale` takes `name()` for that reason; after `graph drop _all` there is no `.Graph` at all, so reading it is an error to `capture`.
- **`set graphics off`** is fine for `graph export` (every extract script does it) and for `.Graph` members after a batch draw (`test_help_claims_6.cscript:691`); `nodraw` may leave `curmin`/`curmax` empty, which the fixture records as `null` rather than treating as an error.
- **Colour case.** Stata's SVG writes `#FF0000`; the module lower-cases; a cscript comparing to a scheme value compares lower case.
- **Two spaces.** `title("Smoke  title")` is the nbsp case on purpose; a test that "fixes" the title to one space has removed the point of the fixture.
- **Merging.** Every batch-1 section that adds a cscript edits `test/run_all_cscripts.do` (append a block) and `test_cscript_hygiene.py:294` (the count). With `patch -p1` the count line will conflict; the merger sets it to the final number and the runner keeps every appended block. Say so in this section's commit message.
- **Stata sessions.** Never more than three at once across all batch-1 agents; a run of `[ SKIP]` lines in under a second means `python_exec` was dropped, not that the scripts skip.
- **STATATMP.** The trailing slash is required; the directory must not be the one the batch log is written to (HC4-21 scans `c(tmpdir)`).
- **Fixture hygiene.** `git add -f` for the JSON; `test_fixtures_are_committed.py` requires the file name to appear in a test or cscript as a whole token, which `test_svg_truth.py` and `test_cert_svg.cscript` do.
- **What section 18 must read from here.** `svg_truth_smoke.json.matches_svg.drawn_extent_member` decides whether B2's cscript may read `.Graph` at all; if it is `"none"`, B2's truth is SVG-only, as DISCOVERY's amended Q14 allows.
