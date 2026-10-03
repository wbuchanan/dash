# Section 06: hover() variables exported

> Part of: WP-29 · P0: P0.10 · Risk: yellow · Batch: 1 · Depends on: 01 · Blocks: 14 · Tasks: 11, 1 commit (P0.10)

## Review amendments (design review u09, 30sep2026) — binding; they override any conflicting text below

> Batch **1** · Depends on **01** · Blocks **14** · Risk **yellow** · Commits: one (P0.10) → CHANGELOG `### Fixed in WP-29` (the one marker S01 places for P0.10)

The reviewed design (u09-hover-export, verdict "sound with amendments") is carried with every amendment applied:

- **A1 (count only where a layer can show it).** hover()'s variables are ALWAYS exported (all_vars on the build route, needed_vars on the one-line route), so the served app and the new missing-variable note behave alike. They are COUNTED on the saved page (row_vars, the one-line `_dash_nvars`, the saved `_dash_byte_cap` list) only when some layer of the graph can show them: some plot type outside `_pt_univar _pt_onefit _pt_literal` (`_dash_plottype_families`, dash.ado:3058-3071), which is exactly the computed and literal set of `_dash_note_hover_unreached` (dash_render.py:24660-24666). The Python twin tests `_DASH_COMPUTED_ONLY_TYPES | _DASH_LITERAL_TYPES`. DL-03e therefore keeps its count (74 values, 74 x 1); only its PASS text, which says the variable "is not exported", is flipped. The optional part of A1 (hover() not marking a computed-only graph as touched) is NOT taken: `_dash_graph_touched` is unchanged, and the over-count it leaves is a recorded residual.
- **A1, two consequences this section adds (found while writing it, from the code):**
  - (a) `csv` puts every exported column in the saved page's download (`_dash_embedded_cells` returns every column under csv, dash_render.py:1190-1191), so under csv a hover() variable counts whatever the graph. The Stata "can show" flag is `csv given OR some layer can show it`.
  - (b) The saved renderer re-checks the bytes limit over EVERY string column of the data file (`_dash_refuse_overbytes(self.df, self.string_vars, ...)`, dash_render.py:25108-25110). If Stata left a hidden hover() string out of its count but the renderer counted it, `dash histogram price, hover(make)` at a low `$dash_max_bytes` would pass Stata and die in Python. A twin `_dash_hover_unembedded(spec)` removes exactly the names Stata leaves out, and the served side keeps counting every column, as dash.ado's served route does.
- **A2.** HX-07 (Unicode) reads the saved page's JSON decoded (`json.loads`), never as raw text: Bokeh writes non-ASCII escaped.
- **A3.** No new test pins the blank row label of an unlabelled hover-only variable (P0.3, section 03, merges before this section in batch 1 but is not in this worktree). One test, `TestAnUnlabelledHoverOnlyVariable`, asserts the variable's name once S03's `_dash_var_label` exists and `""` before, so the assertion tightens by itself when S03 lands. Every test that asserts label text passes `var_labels` explicitly or uses auto's own labels (index A7).
- **A4.** The extractor cuts an echoed bad word to 80 characters (the first 77 and `...`); the note is ONE per graph (`_dash_warn_once(("hover-missing", gname))`), at most three names plus `and N more`. Both are pinned (HX-12, HX-25; `test_missing_hover_names_are_one_bounded_note`).
- **A5.** Direct Mata unit cases HX-20..HX-25 call `_dash_extract_hover_vars` by name and assert on what it returns. `program_coverage_map.py` names HX-20 first.
- **A6.** HX-19 fails at the base. It asserts `AMC Concord`, the `@{make}` field, a list of tooltips, no `{safe}`, and the hostile value present only as data, in both modes.
- **A7.** HX-08 covers `link()`, saved and served.
- **A8.** HX-01 (saved) and HX-03 (served) assert 74 rows with the 5 missing rep78 kept. `TestRowsWithAMissingHoverValueAreKept` adds the saved twin of `test_server_layer_defects.py:701`.
- **A9.** The "no JavaScript change" guard covers a plain scatter, by(), a yaxis(2) second layer and a line. HX-05 covers by(foreign), served, after a move.
- **A10.** Per index A3 the truth block is `* ==== S06 P0.10: ... ====` in `test/test_wp29_truth.cscript`, gated `WP29_ONLY=S06`. `test_gaps2_truth.cscript` is edited only to flip AL-19 in place (index R1). Refusals HX-10..HX-19 and the direct cases go into `test_adversarial.cscript` (index R1 table).
- **A11.** GitNexus has no index for this repository (`list_repos` on 30sep2026 lists only TYME and PhotoShootPlannerPro). Task 06-01 indexes the worktree and runs impact on every symbol this section edits before any edit.

**Truth disputes, resolved by re-measuring at 7421d3d (Stata through `scripts/stata_slot.sh`):**
- The design's "888 bytes" for `hover(make)` is wrong. `sum(strlen(make))` on auto is **871** (`MAKEBYTES=871`). `dash scatter mpg weight, mlabel(make)` at `$dash_max_bytes 100` reports `871 bytes of text (in 1 string variable)` through the same `_dash_byte_cap` (m2.log:114). HX-16 computes the expected number live.
- DL-03e stays at 74 under A1 (review truth dispute 1). The served twin of DL-03e changes from 74 x 1 (measured `D1S rc=134 ... 74 values (74 observations x 1 variable)`) to 148 x 2, because the served app embeds every exported column.

**Index deltas applied:**
- The BUGS.md entry is S01's open entry, closed in place (index A4).
- `GAPS2.md`, `ROADMAP.md`, `DROPIN-REMAINING.md` and `REMAINING.md` are S15's (index A5). Their text is in "Notes for the closeout".
- The served copy-list entry goes after `"_dash_csv_payload", "_dash_frame_filter_mask",` (index R2 anchor 28629), not beside `_dash_note_hover_unreached`.
- The CHANGELOG has one marker for P0.10, under `### Fixed in WP-29` (index "P0 coverage"). The changed-behaviour sentences go in that marker's lines.

## Overview

`hover(varlist)` is dash's own option: twoway refuses it (`twoway scatter mpg weight, hover(rep78)` → `option hover() not allowed`, r(198), measured; already pinned by `test_help_claims_2.cscript` HC2-14C). The promise is in dash.sthlp:2606-2630: hover() "adds the variables' values to the tooltip of every layer whose marks are observations ... in the saved dashboard and the served app alike".

DROPIN-REMAINING P0.10 measured that the promise fails for the common case: a variable named ONLY in hover() is never exported. `dash scatter mpg weight, hover(rep78)` returns rc 0, the page holds no `@{rep78}`, no `__dash_hover_rep78` and no `Poor`, and the tooltip shows weight and mpg alone. The same happens through `name()` + `dash build`, and in the served app (tooltips `[('Weight (lbs.)','@{weight}{custom}'), ('Mileage (mpg)','@{mpg}{custom}')]`, CDS columns `['index','mpg','weight']`), with no note in any mode. The renderers are already right once the column is there: they drop an absent name in silence (`_collect_graph_vars`, `_dash_build_hover`, the served `_hover_cols_of`). Nothing pins the defect in pytest, because every pytest builds its data from a full DataFrame. Two cscripts pin it: DL-03e's PASS text says so, and AL-19 passes only because its hover variable is also plotted.

After this section:
- Every variable hover() names is read and checked in Mata (`_dash_extract_hover_vars`) and exported on both routes, in both modes.
- It is counted against `$dash_max_cells` and `$dash_max_bytes` wherever the page really holds it: the saved page when a layer can show it (or csv), the served app always.
- A hover() variable dropped after `name()` is refused at `dash build`/`dash serve` with r(111), and a hand-edited registry value that is not a list of names with r(198), before anything is written.
- The renderers name, in one bounded note per graph, any hover() variable a spec names that the data does not hold.

The saved page's filter JavaScript needs no change: a hover-only column already follows a move once it is in the data (measured, A9 guards).

**Test order (CLAUDE.md rule 7) and commit rule (index step 1).**
1. Tasks 06-03, 06-04 and 06-05 write every regression test (pytest and cscript) and run them against the unmodified worktree. They save the failure text to `<scratch>/06-P0.10-failure.txt` and do not commit.
2. Tasks 06-06 to 06-08 make the fix.
3. Task 06-09 turns the section green.
4. Task 06-10 updates the help.
5. Task 06-11 closes the entry and makes the section's ONE commit, subject ending `(WP-29 P0.10)`, whose body opens with the saved failure text. No test-only commit exists.

## Risk: [yellow] — one export list feeds three counts in two languages, and the counts must agree or a dashboard Stata accepts dies in the renderer

**Why.** The fix itself is a union into two export lists. The risk is in what follows the export:
- the saved cells count (Mata `row_vars`, one-line `_dash_nvars`, Python `_dash_embedded_cells`);
- the bytes count (Mata `_dash_byte_cap`, Python `_dash_refuse_overbytes`);
- the served count.

Each has a twin in the other language. A disagreement shows as a refusal in one place and not the other, or as a Python traceback after Stata said yes.

**Risk factors.**
1. A1's "can show" rule must be the same test in Mata (`_dash_spec_types_in` over three family lists) and Python (`_DASH_COMPUTED_ONLY_TYPES | _DASH_LITERAL_TYPES`, exact type match like `_dash_graph_computed_cells`).
2. csv changes what the saved page holds.
3. Names come from user-editable registry globals and reach `_dash_write_data` and messages.
4. The new note fires for any spec-JSON hover() name absent from a test DataFrame, across 96+ test files.
5. Dashboards near `$dash_max_cells`/`$dash_max_bytes` that use hover() can now be refused, because the columns are really embedded now.
6. S14 (batch 3) rewrites the same export lists for P0.11.
7. `_make_figure_body` is an expected HIGH-impact symbol (index R8).

**Mitigation.**
1. One family list per language, plus `TestTheTwoLanguagesAgree::test_the_types_hover_cannot_reach_agree`, which reads dash.ado's `c_local` lines and the note's literal tables.
2. csv in the Stata flag; `_dash_embedded_cells` already returns every column under csv; HX-17 has a csv sub-case.
3. `_dash_is_varname` + `_st_varindex(w, 0)` before any use; 80-character bounded echoes through `_dash_say`.
4. One note per graph, keyed on the graph. The full suite is run once in 06-11.
5. A CHANGELOG line names the change with numbers.
6. S14 depends on S06 (index), so it builds on these unions.
7. Checkpoint 06-02.

## Dependencies

- **Depends on:** section 01. It provides the open BUGS.md entry for P0.10, the `<!-- WP-29 P0.10 -->` marker under `### Fixed in WP-29`, the `WP29_OPEN["P0.10"]` key, and `test/test_wp29_truth.cscript` with its tally helpers and the line `* ==== append new blocks above this line ====`.
- **Blocks:** section 14. u10 restricts every consumer to the rows it reads and needs the hover columns in the export list (index "14 ← 02, 06, 07, 08, 11").
- **Parallel batch:** 1. Merge order `S01, S09, S03, S02, S04, S06, S07, S05, S08`. Can run with 02, 03, 04, 05, 07, 08, 09.
- **Why this order:**
  - S02 and S04 also edit dash.ado/dash_parse.mata, in the plot-option parse and after the segment loop. S06's hunks are in the export path (dash.ado:5981-6090, 6857-7115) and in dash_parse.mata section 6a. Later hunks apply to the earlier text.
  - S08 rewrites every temp-file writer after S06 lands.
  - S03 lands the unlabelled-variable rule before S06 (A3).

## Evidence

### Measured at 7421d3d

Stata 19.5 runs through `scripts/stata_slot.sh <scratch>/wp29/s06 <file>.do`, with `sysuse auto` unless noted:

| Command | Result |
|---|---|
| `twoway scatter mpg weight, hover(rep78)` | `option hover() not allowed`, `TW rc=198` (m1.log:49-52) |
| `dash scatter mpg weight, hover(rep78) saving(a1.html)` | `A1 rc=0`; a1.html holds 0 × `__dash_hover_rep78`, 0 × `Poor`, 0 × `"rep78"` |
| `dash scatter mpg weight, hover(rep78) name(g1)` then `dash build, saving(b1.html)` | `B1 rc=0`; 0 hits |
| … then `dash build, server saving(c1.py)` | `C1 rc=0`. Loading the app into a `Document` gives tooltips `[('Weight (lbs.)', '@{weight}{custom}'), ('Mileage (mpg)', '@{mpg}{custom}')]`, CDS `['index', 'mpg', 'weight']` (74 rows), warnings `[]` |
| `preserve; drop rep78; dash build, saving(b2.html)` | `B2 rc=0`, silently (a dropped plotted variable is r(111), research M2B2) |
| Registry `"hover":"mpg;("` (hand-edited with `subinstr`), then `dash build` | `H11 rc=0`, silently |
| `$dash_max_cells 70`: `dash histogram price, bin(10) hover(foreign)`, one-line / build / build server | each r(134) `74 values (74 observations x 1 variable)` (m1.log:128-150) |
| `$dash_max_cells 200`: `dash scatter mpg weight, hover(rep78 headroom trunk)`, server / one-line | `H13 rc=0`, `H14 rc=0` (counted 148 = 74 x 2) |
| `$dash_max_bytes 100`: `dash scatter mpg weight, hover(make)` | `H15 rc=0`. With `mlabel(make)` instead: `871 bytes of text (in 1 string variable)`, r(134) |
| `$dash_max_bytes 100`: `dash histogram price, bin(10) hover(make)`, one-line / build / server | `H16a/b/c rc=0` |
| `$dash_max_cells 30`: `dash scatteri 1 2 3 4, hover(mpg)` | `H18 rc=0`, note `dash: hover() does not reach plot 1 (scatteri): its points are typed in the command, ...` |
| Registry JSON | `{"plots":[...],"graph_options":{"name":"g1","hover":"rep78 headroom rep78"},...}`: duplicates are kept. `hover(make größe)` is stored raw UTF-8 `"hover":"make größe"`. `hover(rep)` is stored `"hover":"rep78"` (unab at registration). |
| auto | `isid make` passes; 22 cars have `foreign == 1`; 5 have rep78 missing |

Mata building blocks (m3.log, m4.log):
- `_st_varindex("rep", 0)` is `.`; `_st_varindex("rep", 1)` is 4; `größe` resolves.
- `_dash_json_get_str` on `{"hover":"gr` + char(92) + `u00f6` + char(92) + `u00dfe mpg"}` gives `größe mpg`.
- A title holding the escaped text `\"hover\":\"nosuch\"` is not read (`HV2=[]`), and a real key after it is (`HV3=[mpg]`).
- `_dash_blank_words("mpg" + char(9) + "weight  mpg")` gives `mpg weight mpg`.
- `_dash_is_varname` gives 1 / 0 / 0 / 1 for `größe`, `mpg;(`, 200 × `a`, `_n`.
- `: label (rep78) .` is `.`.

Python twin at 7421d3d (probe p1.py):

```
scatter+hover z        (['y', 'x'], 0)
hist+hover z           (['x'], 0)
scatteri+hover z       ([], 0)
scatter+lfit+hover z   (['y', 'x'], 0)
```

Saved filter move with the column present (spec route; probe p3.py using `test_saved_filter_layers._render`/`_move`). Each row is (rows, aligned) for every source carrying `__dash_hover_foreign`:
- dropdown rep→3: `[(4, True)]`
- by(rep) + price range 4500-11385: `[(0, True), (4, True), (2, True)]`
- scatter + yaxis(2) scatter: `[(6, True)]`
- line: `[(6, True)]`

The JavaScript is already right.

A hostile string in a hover column on the saved page (probe p4.py, spec route): raw `<img src=x onerror=alert(1)>` occurs 0 times. `@{make}` occurs once. The tooltips are `[('weight','@{weight}'), ('mpg','@{mpg}'), ('make','@{make}')]`.

Saved page JSON (bokeh 3.9.0): one `<script type="application/json">` block. A column is a `["mpg", [74 values]]` pair in a `{"type":"map","entries":[...]}` object. Tooltips are a `"tooltips": [["Weight (lbs.)","@{weight}{custom}"], ...]` attribute.

### The defect, in code

`_dash_extract_vars` (dash_parse.mata:2148-2190) scans only plot keys:

```mata
keys    = (char(34)+"yvar"+char(34)+":",   char(34)+"xvar"+char(34)+":",  char(34)+"var"+char(34)+":",
           ...
           char(34)+"mlabel"+char(34)+":",
           char(34)+"colorvar"+char(34)+":",
           char(34)+"wexp"+char(34)+":")
```

It takes a raw value between quotes as ONE name, decoding and checking nothing, so it must not simply gain `"hover"`.

One-line route, `_dash_render_immediate` (dash.ado:5888). needed_vars is plot keys plus by() (5980-6001):

```stata
5981    mata: _dash_extract_vars(`"`json_spec'"', "needed_vars")
5994    mata: _dash_extract_qual_vars(`"`json_spec'"', "_qualvars")
5995    foreach _qv of local _qualvars {
...
6001    local needed_vars = strtrim("`needed_vars'")
```

and is then the cells count (`local _dash_nvars : word count `needed_vars'`, 6061; `_dash_cell_cap`, 6080-6085), the bytes count (`_dash_byte_cap `needed_vars'`, 6086), the formats (6090) and the export (`_dash_write_data "`data_json_path'" `needed_vars' `_dash_qual_vars'`, 6116).

Build route, `_dash_prepare_spec` (dash.ado:6605). Per graph: `gvars` (6956-6963) and `qvars` (6966-6974) go into all_vars; the touched branch (6991-7006) puts them into row_vars. Filter variables follow (7009-7047). Then `_dash_cell_cap` for served (7109-7111) or saved (7112-7114), and ONE `_dash_byte_cap `all_vars'` for both (7115).

`_dash_graph_touched` (dash_parse.mata:5455-5476) already reads hover with `_dash_json_get_str`, so a hover() graph is always "touched" (row-counted); it is not changed here.

Renderers dropping an absent name in silence:
- saved `_collect_graph_vars`, dash_render.py:24971-24979: `if hv and hv not in seen and hv in df.columns`;
- `_dash_build_hover`, :23876: `if not _c or _c in _seen or _c not in _present: continue`;
- served `_hover_cols_of` (template :30247-30260) and the linked all_vars (:30098-30099): `if _hc in df.columns`.

Python twin `_dash_embedded_cells` (dash_render.py:1167-1240): a touched graph adds `_VAR_KEYS`, option columns, by() names and qualifier columns, never hover(). The saved bytes re-check is at :25108-25110; the served one at :29146-29160 counts every string column.

The note precedent `_dash_note_hover_unreached` (:24638-24684) holds its type tables as literals because "the served app copies this function by source". It is called at :26368-26370 (saved, `_make_figure_body`) and at template :30704-30709 (served `_dash_figure_for`, which reads `df` from `make_document`'s scope, as `len(df)` there shows). It is in the copy list at :28617. `_dash_display` (:23052) and `_dash_warn_once` (:13033) are copied already (:28806 and the warn helpers).

### Tests that pin today's behaviour (flip, never delete)

- `test/test_adversarial.cscript` **DL-03e** (:2973-2980). The expectation `74 values (74 observations x 1 variable)` STAYS (A1). The PASS text `hover() reaches the graph too; the hover variable itself is not exported and does not inflate the count` becomes false in its first clause and is flipped to `hover() reaches the graph too; its hover() variable is exported, but no layer of h1 can show it, so it does not inflate the count`.
- `test/test_gaps2_truth.cscript` **AL-19** (:1077-1086). It uses `dash scatter mpg rep78, hover(rep78)` (rep78 is plotted) under the comment `// rep78 is plotted, so it is exported: a hover()-only variable is not exported on the one-line route (BUGS.md, a residual of G16).` Flipped to `dash scatter mpg weight, hover(rep78)`, with the comment replaced. At the base it fails (no `__dash_hover_rep78`).
- `test/test_mode_parity.py::TestHoverReachesEveryLayerOrIsReported::test_a_huge_hover_list_is_one_note[saved|served]` (:3133-3142). The names `v0..v4999` are absent from `_DF`, so the new missing-variable note is a second `hover()` note. Flipped to: exactly one `does not reach` note, exactly one `not in the data` note ending `and 4,997 more; the tooltip leaves them out.`, and `v4999` in neither.
- Unchanged and still green: `test_embedded_cells.py::TestTheCount::test_touched_graphs_count_their_rows[hover]` (histogram with hover `x`, its own variable: `['x']` under A1 too), DL-01..DL-06's counts, OV-110/OV-111, HC2-11b, HC2-14C.

### GitNexus

`mcp__gitnexus__list_repos` (30sep2026) returns only `TYME` and `PhotoShootPlannerPro`. Task 06-01 runs `gitnexus analyze` in the worktree. That command also rewrites `CLAUDE.md`/`AGENTS.md` context files and writes `.gitnexus/` (gitignored only by the maintainer's uncommitted `.gitignore` line, so untracked in a worktree). It then records `gitnexus_impact` for:
- `_dash_embedded_cells`
- `_make_figure_body`
- `_generate_app_source` (ServerAppBuilder)
- `DashRenderer.__init__`
- `_dash_prepare_spec`
- `_dash_render_immediate`

R8 expects `_make_figure_body` HIGH.

## User stories

- **US-06.1** As a dashboard publisher, I want `dash scatter mpg weight, hover(rep78)` to show each car's repair record, as its value label (`Average`), in the tooltip of the saved page and of the served app, so that hover() does what the help says without my also plotting the variable.
- **US-06.2** As a dashboard reader, I want the tooltip to keep showing the right row's hover() values after I move a filter, under by() and on a second axis, in both modes.
- **US-06.3** As a dashboard publisher, I want a hover() variable that I dropped after registering the graph to stop `dash build`/`dash serve` with a message naming it, as a dropped plotted variable does, rather than vanish from the tooltip.
- **US-06.4** As a dashboard publisher, I want the data limits to count what the page really holds, a hover() column included, so that a refusal is truthful and a page never exceeds what dash promises to embed.
- **US-06.5** As the maintainer, I want any hover() name that reaches the renderer without being in the data to be named in one bounded note, so that the silent-drop class of defect cannot return unnoticed.
- **US-06.6** As the maintainer, I want names from user-editable registry globals checked before they reach any Stata command text or message, so that a hand-edited registry cannot inject code or flood the log.

## Business requirements

- **BR-06.1** Every variable named in a graph's hover() is in that graph's tooltip in the saved page and the served app, on the one-line route and through `dash build`/`dash serve`. For a variable with value labels, its label text is shown, equal row by row to Stata's `: label (var) value` (`.` for a missing value). This holds before and after any filter move, under by(), link(), a yaxis(2) layer, and for date, string and Unicode-named variables.
- **BR-06.2** Rows whose hover() variable is missing are drawn, as twoway draws them (74 markers for `scatter mpg weight` with 5 rep78 missing).
- **BR-06.3** On the saved page, a hover() variable counts toward `$dash_max_cells`, and a string one toward `$dash_max_bytes`, when some layer of its graph can show it (any type other than histogram, kdensity, the fits and smoothers, scatteri, pci, pcarrowi, function) or when csv is given. In a served app every hover() variable counts. The refusal is r(134), before anything is written, naming the count.
- **BR-06.4** `dash build`/`dash serve` refuse a hover() variable that is not in memory with r(111) and `<cmd>: graph '<g>': hover(): variable <name> not found`. They refuse a registry hover() value that is not a list of names with r(198), echoing at most 80 characters of it. In both cases no file is written.
- **BR-06.5** A hover() name absent from the data a renderer is given is named in one note per graph per render, identical in both modes. The note names at most three names (each printable, at most 80 characters) and counts the rest.
- **BR-06.6** No tooltip field ever carries `{safe}`; a string value reaches the page only as JSON data.
- **BR-06.7** The help says what is exported, what counts, and when r(111) is given. The CHANGELOG names the command, the old result and the new.

## Technical requirements

- **TR-06.1 Mata extractor (dash_parse.mata, new section 6a, placed after `_dash_extract_vars` ends at :2191 and before the `// 6b.` banner at :2195).** Write it exactly as follows, with this comment block above it:

  ```mata
  // ============================================================
  // 6a. hover() VARIABLE EXTRACTOR (WP-29 P0.10; used by
  //     _dash_prepare_spec and _dash_render_immediate)
  //     _dash_extract_hover_vars(json_str, out_macro, bad_macro, why_macro)
  //
  // The variables a graph's hover() names, each once, in the order first
  // written, blank-separated, into the caller's local out_macro.  hover()
  // is read the way _dash_graph_touched reads it -- _dash_json_get_str: the
  // first "hover":" key, its escapes decoded; a title holding that text
  // carries its quotes escaped and never matches -- and split as the
  // renderer splits it (_dash_blank_words).  Each word must be a Stata name
  // (_dash_is_varname) and the exact name of a variable in memory
  // (_st_varindex with no abbreviation: dash.ado stored the full names at
  // registration, OV-110).  The first word that is not stops the read:
  // bad_macro gets it, at most 80 characters (the first 77 and "..."),
  // why_macro "name" (not a Stata name) or "var" (no such variable), and
  // out_macro stays empty.  No word is ever run as code.
  // _dash_extract_vars is not used: it reads a raw value as ONE name and
  // decodes and checks nothing.
  // ============================================================
  void _dash_extract_hover_vars(string scalar json_str,
                                string scalar out_macro,
                                string scalar bad_macro,
                                string scalar why_macro)
  {
      string rowvector words
      string scalar    w, out
      real scalar      i
      transmorphic     seen

      st_local(out_macro, "")
      st_local(bad_macro, "")
      st_local(why_macro, "")
      _dash_json_get_str(json_str, "hover", "_dehv_raw")
      words = _dash_blank_words(st_local("_dehv_raw"))
      st_local("_dehv_raw", "")
      seen = asarray_create()
      out  = ""
      for (i = 1; i <= cols(words); i++) {
          w = words[i]
          if (asarray_contains(seen, w)) continue
          if (!_dash_is_varname(w)) {
              st_local(bad_macro, ustrlen(w) > 80 ? usubstr(w, 1, 77) + "..." : w)
              st_local(why_macro, "name")
              return
          }
          if (_st_varindex(w, 0) >= .) {
              st_local(bad_macro, w)
              st_local(why_macro, "var")
              return
          }
          asarray(seen, w, 1)
          out = out + (out == "" ? "" : " ") + w
      }
      st_local(out_macro, out)
  }
  ```

  Two separate `if`s: Mata's `|` is not relied on to short-circuit. The header index (dash_parse.mata:157-163, after the `_dash_extract_vars` entry) gains:

  ```
  *!   _dash_extract_hover_vars(json_str, out_macro, bad_macro, why_macro)
  *!       The variables a graph's hover() names, each once and checked, into
  *!       out_macro; the first word that is not one into bad_macro, with
  *!       why_macro "name" or "var" (WP-29 P0.10).
  ```

- **TR-06.2 One-line route (dash.ado `_dash_render_immediate`).**
  - **The extractor and its refusals.** Directly after the `_qualvars` loop (:5994-6000) and before `local needed_vars = strtrim(...)` (:6001), insert:

    ```stata
        // WP-29 P0.10: every variable hover() names is exported -- it was
        // not, so a variable named only there was left out of the tooltip
        // with rc 0 and no note.  Read and checked in Mata
        // (_dash_extract_hover_vars) before it reaches any command.  It is
        // COUNTED (_cap_vars: the cells and bytes limits) only when a layer
        // of this graph can show it: a graph made only of computed or
        // literal layers draws no observation, and the page holds none of
        // its rows (design review A1).
        local _hvars ""
        local _hv_bad ""
        local _hv_why ""
        mata: _dash_extract_hover_vars(st_local("json_spec"), "_hvars", "_hv_bad", "_hv_why")
        if "`_hv_why'" == "name" {
            mata: _dash_say("err", "dash: hover() must name variables (got: ", st_local("_hv_bad"), ")")
            exit 198
        }
        if "`_hv_why'" == "var" {
            mata: _dash_say("err", "dash: hover(): variable ", st_local("_hv_bad"), " not found")
            exit 111
        }
        local _cap_vars `needed_vars'
        if "`_hvars'" != "" {
            _dash_plottype_families
            local _hv_show = 1
            mata: st_local("_hv_show", strofreal(!_dash_spec_types_in( ///
                st_local("json_spec"), st_local("_pt_univar") + " " + ///
                st_local("_pt_onefit") + " " + st_local("_pt_literal"))))
            if `_hv_show' local _cap_vars : list _cap_vars | _hvars
            local needed_vars : list needed_vars | _hvars
        }
        local _cap_vars = strtrim("`_cap_vars'")
    ```

    These refusals cannot be reached from `dash <plot>` (registration refuses a bad name first, OV-111). They guard a spec handed to this program directly (P1A-74).
  - **The counts.** Replace `local _dash_nvars : word count `needed_vars'` (:6061) with `local _dash_nvars : word count `_cap_vars'`, and `_dash_byte_cap `needed_vars'` (:6086) with `_dash_byte_cap `_cap_vars'`. The export (:6116) and `_dash_formats_json "`needed_vars'"` (:6090) keep `needed_vars`.
  - **What follows.** A scatteri-only graph with hover(mpg) now takes the export path (needed_vars is not empty), with `_cap_vars` empty, so it is counted as 0 cells (HX-18).

- **TR-06.3 Build route (dash.ado `_dash_prepare_spec`).**
  - **Before the per-graph loop.** Next to `local row_vars ""` (:6864), add `local _hv_hide ""`.
  - **Inside the graph branch.** After the `qvars` loop (:6966-6974) and before the `_gc_` computation (:6982), insert the extractor call on `st_local("_qg_`k'")` with locals `_hv_k _hv_bad _hv_why`, then:
    - why `name` → `mata: _dash_say("err", "`cmdname': registry entry '" + st_local("gname") + "' holds a hover() value that is not a list of variable names (got: ", st_local("_hv_bad"), "). Run dash clear and register it again.")` and `exit 198`.
    - why `var` → `mata: _dash_say("err", "`cmdname': graph '" + st_local("gname") + "': hover(): variable ", st_local("_hv_bad"), " not found")` and `exit 111`.
    - Then `local _hv_show_`k' = 1`. If `"`_hv_k'" != "" & "`csv'" == ""`, set it with `mata: st_local("_hv_show_`k'", strofreal(!_dash_spec_types_in(st_local("_qg_`k'"), "`_pt_univar' `_pt_onefit' `_pt_literal'")))`.
    - If `_hv_show_`k'`: `local all_vars : list all_vars | _hv_k`. Else: `local _hv_hide : list _hv_hide | _hv_k`.
  - **Touched branch.** After the `_gqc_` loop (:7001-7004), add `if `_hv_show_`k'' local row_vars : list row_vars | _hv_k`. hover() always makes a graph touched (`_dash_graph_touched`), so this branch is the only one a non-empty `_hv_k` reaches.
  - **After the filter loop.** After `local all_vars = strtrim("`all_vars'")` (:7048) and before `_novars` (:7061), add:

    ```stata
        // WP-29 P0.10 (review A1): the saved page's text count leaves out
        // the hover() variables no layer of their graph can show; a served
        // app embeds every exported column, so it counts them.
        local _byte_vars "`all_vars'"
        local all_vars : list all_vars | _hv_hide
        local all_vars = strtrim("`all_vars'")
    ```

  - **The bytes cap by mode.** Move `_dash_byte_cap` into the mode branches (:7109-7115): served `_dash_byte_cap `all_vars'`, saved `_dash_byte_cap `_byte_vars'`. `_dash_nvars` (:7100) stays the word count of all_vars.
  - **Comments.** Update the comments at :6857-6863 and :7094-7097 and the `_dash_cell_cap` header (:2842-2846): "...that no filter, link(), csv or hover() reaches; hover()'s own variables are counted only for a graph one of whose layers can show them (WP-29 P0.10)".
  - **`dash serve`.** `_dash_serve_spec` calls `_dash_prepare_spec`, so `dash serve` is covered by the same edit.

- **TR-06.4 Required Mata list.** dash.ado `_dash_require_mata` `_needed` (:232-245) gains `_dash_extract_hover_vars` after `_dash_extract_vars`. `test_file_headers.py::TestTheMataLibraryHeader::test_its_public_api_is_the_list_dash_ado_needs` holds the header and this list equal.

- **TR-06.5 Python twins (dash_render.py, saved only; no copy-list entry).**
  - **`_dash_hover_shown(g)`.** New, right after `_dash_embedded_cells` (:1240). It returns True when graph dict `g` has no plot dicts, or some plot whose `str(p.get("type", ""))` (exact, no lowercasing, as `_dash_graph_computed_cells` reads it) is not in `_DASH_COMPUTED_ONLY_TYPES | _DASH_LITERAL_TYPES`. Both constants are module-level and resolved at call time.
  - **`_dash_hover_unembedded(spec)`.** New, after `_dash_hover_shown`. It returns `set()` under `_dash_csv_wanted(build_options)`. Otherwise it returns `hidden - other`, where:
    - `hidden` is the hover() names of graphs for which `_dash_hover_shown` is False;
    - `other` is every graph's plot `DashRenderer._VAR_KEYS` values and `_dash_option_columns(options)`, every graph's `_dash_parse_by(..., warn=False)[0].split()`, the hover() names of graphs that show them, every KPI's `var`, and every `_dash_parse_filter_raw(build["filter"], warn=False)` `varname`.

    This is the Python mirror of TR-06.3's `_hv_hide` minus `_byte_vars`.
  - **`_dash_embedded_cells`.** In the touched branch, after `for qc in _dash_graph_qual_cols(g): _add(qc)`, add `if _dash_hover_shown(g): for name in hover.split(): _add(name)`. Update the docstring: hover()'s variables count where a layer can show them.
  - **`DashRenderer.__init__`.** The bytes re-check (:25108) passes `set(self.string_vars) - _dash_hover_unembedded(self.master_spec)`.

- **TR-06.6 The note (dash_render.py, both renderers).**
  - **The function.** New `_dash_note_hover_missing(gname, hover_extra, columns)`, right after `_dash_note_hover_unreached` (before `_dash_glyph_dispatch`, :24687). It does nothing when `hover_extra` is empty or every name is in `columns`. Otherwise it collects the absent names, each once in order (a `set` for membership), and calls `_dash_warn_once(("hover-missing", str(gname)), msg, stacklevel=3)`:
    - `msg` = `f"dash: {where} names variable(s) not in the data -- {shown}; the tooltip leaves them out."`
    - `where` = `f"hover() of graph {_dash_display(gname)!r}"` if gname else `"hover()"`
    - `shown` = `", ".join(repr(_dash_display(n)) for n in missing[:3])`, plus `f" and {len(missing) - 3:,} more"` when more than 3 are absent.

    The docstring says it is copied into the served app by source and why it exists (spec-JSON callers; from Stata it cannot fire after this fix).
  - **Saved call.** In `DashRenderer._make_figure_body` (after the `_dash_note_hover_unreached(...)` call, :26368-26370): `_dash_note_hover_missing(graph_opts.get("name", "") or graph_spec.get("name", ""), _hover_extra_str.split() if _hover_extra_str else [], list(self.df.columns))`.
  - **Served call.** In `ServerAppBuilder._generate_app_source`'s emitted `_dash_figure_for`, after the three emitted lines of the `_dash_note_hover_unreached(` call (:30707-30709), emit:

    ```
    "        # hover() names the data does not hold, once per graph, in the",
    "        # saved renderer's words (WP-29 P0.10).",
    "        _dash_note_hover_missing(",
    "            go.get('name', '') or g.get('name', '') or gname,",
    "            _hv.split() if _hv else [], list(df.columns))",
    ```

  - **Copy list.** In the served functions copy list, add a new line `"_dash_note_hover_missing",` with the comment `# hover() names absent from the data (WP-29 P0.10).` directly after the line `"_dash_csv_payload", "_dash_frame_filter_mask",` (:28629; index R2 anchor).

- **TR-06.7 Maps.**
  - `test/function_test_map.py` gains these entries, in alphabetical place (each `_dash_hover_*` near the other `_dash_hover_*` keys, the note right after `'_dash_note_hover_unreached'` at :501):
    - `'_dash_note_hover_missing': 'test/test_mode_parity.py::TestHoverReachesEveryLayerOrIsReported::test_a_hover_variable_not_in_the_data_is_named'`
    - `'_dash_hover_shown': 'test/test_embedded_cells.py::TestTheHoverColumns::test_which_graphs_can_show_hover'`
    - `'_dash_hover_unembedded': 'test/test_embedded_cells.py::TestTheHoverColumns::test_the_names_only_an_unshowing_hover_gives'`
  - `test/program_coverage_map.py` gains `"_dash_extract_hover_vars": ("test_adversarial.cscript:HX-20", "test_wp29_truth.cscript:HX-01"),` after the `_dash_extract_qual_vars` entry (:382-383). It is a direct case first (A5).

- **TR-06.8 Security (rule 1).**
  - Registry text reaches no command before Mata validation.
  - Every echo goes through `_dash_say` (SMCL-escaped) and is bounded at 80 characters.
  - The renderer note is one line, bounded (3 names × 80 characters + the count), never markup, one per graph.
  - Tooltip fields keep passing `_dash_is_stata_name` and never gain `{safe}`.
  - The bytes and cells counts stay truthful in both languages (TR-06.2, 06.3, 06.5).

## Boundaries

- Do not change `_dash_extract_vars`, `_dash_extract_qual_vars`, `_dash_graph_touched` (its hover() clause stays; A1's optional part is a residual) or `_dash_computed_cells`.
- Do not change the saved filter JavaScript (`_FILTER_JS`, the snapshot code), `_collect_graph_vars`, `_dash_build_hover`, `_hover_cols_of` or the served linked all_vars. The A9 guards prove they need nothing.
- Do not change the row policy of the export (which observations are written): that is S14's (P0.11). Help text added here must not say "every row".
- Do not touch tooltip label text (P0.3, S03), the extended-missing display `.a` (GAPS2 G12, P2), or repeated hover() merging (pre-existing; residual).
- Do not edit `ALLOWED` in test_mode_parity.py (R6). `_MUST_WARN` gains only this section's new corpus key.
- No new `.cscript` file, no runner or hygiene-pin edit (index R1). `test_gaps2_truth.cscript` changes only at AL-19.
- `GAPS2.md`, `ROADMAP.md`, `REMAINING.md`, `.ultraplan/handoff/DROPIN-REMAINING.md` and `AGENTS.md` are S15's (index A5).
- Never stage `CLAUDE.md`, `.gitignore`, `.gitnexus/`, `AGENTS.md`, scratch or `*.html`.

## Stata truth

No fixture: twoway has no hover(), so the truth is Stata's own text per observation, computed live in the block.
- Labels: `local l : label (rep78) `=rep78[`i']'` per observation into a scratch string variable `_hx_lab`, created after the dash commands and read by the python block through `sfi.Data.get`.
- Variables, sets and counts: Stata itself (`isid make`, `count if foreign == 1`, `sum(strlen(make))`).

The block, appended to `test/test_wp29_truth.cscript` above `* ==== append new blocks above this line ====` in section-number order (index R1):

```
* ==== S06 P0.10: hover() variables exported ====
local only : env WP29_ONLY
if inlist("`only'", "", "S06") {
    display as text "S06 start `c(current_time)'"
    ... HX-01..HX-08 ...
    display as text "S06 end `c(current_time)'"
}
* ==== end S06 ====
```

The header list at the top of the script gains `*!   S06  P0.10 hover() variables exported (HX-01..HX-08)`.

Run (the worktree is `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s06`):

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp29_truth.cscript > <scratch>/run_test_wp29_truth.do
dash_nobrowser=1 WP29_ONLY=S06 "$WT/scripts/stata_slot.sh" <scratch> <scratch>/run_test_wp29_truth.do
```

Read `<scratch>/run_test_wp29_truth.log` and never relaunch to check. Use the same two-line driver for `test_adversarial.cscript` (no gate) and `test_gaps2_truth.cscript` (`GAPS2_ONLY=S14`, the block holding AL-19). A SKIP (exit 222, `c(python_exec)` empty) is not a pass.

## TDD test stubs

The base is `$(cat <scratch>/batch-1-base.txt)`. **RED** means it must fail at the base; **GUARD** means it passes at the base and pins what must not change.

**`test/test_embedded_cells.py`** (spec builders `_plot`, `_graph`, `_master`, `_LIMITS` already there):
- RED `TestTheCount::test_a_hover_only_variable_counts_on_a_graph_that_shows_it`: scatter yvar=y xvar=x, hover `z`, columns `[x, y, z]` → `(['y', 'x', 'z'], 0)`. Base: `(['y', 'x'], 0)`.
- RED `TestTheCount::test_a_hover_variable_on_a_mixed_graph_counts`: scatter + lfit, hover `z` → `row_cols == ['y', 'x', 'z']`.
- GUARD `TestTheCount::test_a_hover_variable_on_a_computed_only_graph_does_not_count`: histogram var=x, hover `z` → `(['x'], 0)` (A1).
- GUARD `TestTheCount::test_a_hover_variable_on_a_literal_only_graph_does_not_count`: scatteri, hover `z` → `([], 0)`. Also `function` → `([], 0)`.
- GUARD `TestTheCount::test_a_hover_name_not_in_the_columns_is_not_counted`: scatter, hover `nosuch` → `'nosuch' not in row_cols`.
- GUARD `TestTheCount::test_csv_counts_a_hover_variable_whatever_the_graph`: histogram, hover `z`, csv → `sorted(row_cols) == ['x', 'y', 'z']` (every column).
- RED `TestTheHoverColumns::test_which_graphs_can_show_hover`: `dr._dash_hover_shown`:
  - `scatter` True; `histogram` False; `scatteri` False; `function` False; `[scatter, lfit]` True; `[lfit, kdensity]` False; `[]` True;
  - `[{"type": "Histogram"}]` True (exact match, as Mata).
  - Base: AttributeError.
- RED `TestTheHoverColumns::test_the_names_only_an_unshowing_hover_gives`: `dr._dash_hover_unembedded`:
  - histogram hover `make` → `{"make"}`; the same with csv → `set()`;
  - with a KPI on `make` → `set()`; with a second scatter graph whose hover is `make` → `set()`; with `filter="make, type(dropdown)"` → `set()`;
  - histogram var=price hover `price` → `set()`; scatter hover `make` → `set()`.
- GUARD `TestTheTwoLanguagesAgree::test_the_types_hover_cannot_reach_agree`: the union of the `c_local _pt_univar`, `_pt_onefit` and `_pt_literal` words read from dash.ado == `dr._DASH_COMPUTED_ONLY_TYPES | dr._DASH_LITERAL_TYPES` == the union of the two frozensets in `inspect.getsource(dr._dash_note_hover_unreached)` (parse every quoted word inside `frozenset({...})`).

**`test/test_hover_export.py`** (new; module docstring cites P0.10 and the base measurements; reuses `test_mode_parity` as `tp`, `conftest.make_data_json`, `test_saved_filter_layers._render`):
- RED `TestBothRoutesExportHover`, text tests on dash.ado and dash_parse.mata. A program body is the text from `program define <name>` to the next `\nprogram define `.
  - `::test_the_extractor_is_required`: `_dash_extract_hover_vars` is a word of `_needed`.
  - `::test_the_immediate_route_unions_hover_into_needed_vars`: in `_dash_render_immediate`, `_dash_extract_hover_vars(st_local("json_spec")` comes before `_dash_cell_cap` and `_dash_write_data`; `local needed_vars : list needed_vars | _hvars` is present; `exit 198` and `exit 111` follow the call; `local _dash_nvars : word count `_cap_vars'` and `_dash_byte_cap `_cap_vars'` are present.
  - `::test_the_build_route_unions_hover_into_all_vars_and_row_vars`: in `_dash_prepare_spec`, the call on `st_local("_qg_` comes after `_dash_extract_qual_vars(st_local("_qg_` and before `_dash_graph_touched(`; `local all_vars : list all_vars | _hv_k`, `local row_vars : list row_vars | _hv_k` and `local all_vars : list all_vars | _hv_hide` are present; the refusals hold `exit 198` with `holds a hover() value` and `exit 111` with `hover(): variable `.
  - `::test_both_routes_test_the_three_families`: after the call, each body holds a `_dash_spec_types_in(` whose argument text names `_pt_univar`, `_pt_onefit` and `_pt_literal`; the build route's flag also reads `csv`.
  - `::test_the_saved_byte_cap_leaves_out_what_no_layer_shows`: `_dash_prepare_spec` holds `_dash_byte_cap `_byte_vars'` in the saved branch and `_dash_byte_cap `all_vars'` in the served branch, and no unconditional `_dash_byte_cap` after the branch.
  - `::test_the_mata_extractor_reads_the_value_as_designed`: the function body uses `_dash_json_get_str(json_str, "hover"`, `_dash_blank_words(`, `_dash_is_varname(`, `_st_varindex(w, 0)`, `asarray_create()` and `usubstr(w, 1, 77) + "..."`, and does not call `_dash_extract_vars`.
- `TestTheByteLimit`. Data: `tp._DF` plus `make` (ten strings of 30 characters). `make_data_json`, then set `variableIsString["make"]` and `variableTypeIsString["make"]` to True. `build_options={"limits": {"bytes": 100}}`.
  - GUARD `::test_a_string_hover_variable_a_layer_shows_counts_saved`: scatter hover `make` → `DashLimitError` matching `bytes of text`.
  - RED `::test_a_string_hover_variable_no_layer_shows_does_not_count_saved`: histogram var=mpg hover `make` → renders and has `g1`. Base: DashLimitError.
  - GUARD `::test_the_served_app_counts_it_whatever_the_graph`: the same histogram spec through `ServerAppBuilder(...).build(...)` → `DashLimitError` (a served app embeds every column).
- RED `TestTheServedApp::test_the_app_defines_and_calls_the_note`: the app source built from `tp._spec([tp.plot_for("scatter")], None, {"hover": "rep"})` contains `def _dash_note_hover_missing(` and `_dash_note_hover_missing(`.
- GUARD `TestRowsWithAMissingHoverValueAreKept::test_saved` and `::test_served` (A8): y/x/extra with `extra[1]` NaN, hover `extra`. The scatter source has 3 rows in both modes (saved: `r.figures["g1"]` renderer data length; served: the `test_server_layer_defects.py:701` pattern).
- GUARD `TestAnUnlabelledHoverOnlyVariable::test_its_row_label_follows_p0_3[saved|served]` (A3): the data JSON from `make_data_json(tp._DF)` with `["StataJSON"]["variableLabels"]["rep"]` set to `""` (so the test does not depend on S03's helper change), scatter mpg weight, hover `rep`. The HoverTool row whose field starts `@{rep}` has label `"rep"` if `hasattr(dr, "_dash_var_label")` (S03 landed) else `""`.

**`test/test_value_labels_drawn.py::TestHoverShowsValueLabels`** (all GUARD; A9; `test_saved_filter_layers._render`/`_move`; for every source holding `__dash_hover_foreign`, `[{0.0: "Domestic", 1.0: "Foreign"}[f] for f in src.data["foreign"]] == list(src.data["__dash_hover_foreign"])`, and the row totals below):
- `::test_a_hover_only_column_follows_a_saved_filter_move`: scatter, filter `rep, type(dropdown)` moved to option `3` → one source, 4 rows, `['Domestic', 'Domestic', 'Foreign', 'Domestic']`.
- `::test_a_hover_only_column_follows_a_move_under_by`: by `rep`, filter `price, type(range)` → `(4500.0, 11385.0)` → sources 0/4/2 rows, all aligned.
- `::test_a_hover_only_column_follows_a_move_on_a_second_axis`: `[scatter, scatter price weight yaxis(2)]` → 6 rows, aligned.
- `::test_a_hover_only_column_follows_a_move_on_a_line`: line → 6 rows, aligned.

**`test/test_mode_parity.py::TestHoverReachesEveryLayerOrIsReported`**:
- RED `::test_a_hover_variable_not_in_the_data_is_named[saved|served]`: scatter, hover `rep nosuch`. Notes containing `not in the data` == `["dash: hover() of graph 'g1' names variable(s) not in the data -- 'nosuch'; the tooltip leaves them out."]`; `_tools_showing(fig, "rep")` is non-empty and `_assert_rows_align(figs[0])` holds.
- RED `::test_missing_hover_names_are_one_bounded_note[saved|served]`: hover `rep v0 .. v4999` on one scatter. Exactly one `not in the data` note == `"... -- 'v0', 'v1', 'v2' and 4,997 more; the tooltip leaves them out."`; `'v4999'` absent; `len(note) <= 400`.
- RED `::test_a_hostile_absent_hover_name_is_shown_bounded[saved|served]`: one name `"x" * 50000 + chr(27) + "<script>" + "y" * 50000` (no whitespace, so `split()` keeps it whole). One note, no `"\n"`, no `chr(27)`, the quoted name part at most 82 characters (80 + quotes), `len(note) <= 400`; no HoverTool field contains `<script>` or `{safe}`.
- RED `::test_by_panels_name_a_missing_variable_once[saved|served]`: scatter, `{"hover": "rep nosuch", "by": "foreign"}` → two or more figures, exactly one `not in the data` note.
- FLIP `::test_a_huge_hover_list_is_one_note[saved|served]`: as described in Evidence.
- CORPUS (appended after the `"hover() of a date"` case):
  - `_case("hover() of a variable no layer plots, a dropdown filter", [_sc()], {"filter": "foreign, type(dropdown)"}, {"hover": "rep"})` (GUARD: parity);
  - `_case("hover() naming a variable not in the data", [_sc()], None, {"hover": "rep nosuch"})`, plus the `_MUST_WARN` key with value `"dash: hover() of graph 'g1' names variable(s) not in the data -- 'nosuch'"` (RED in `test_same_warnings`).

**`test/test_wp29_truth.cscript`**, block S06 (all RED). Setup:
- `sysuse auto, clear`;
- `label define alrep 1 "Poor" 2 "Fair" 3 "Average" 4 "Good" 5 "Excellent", replace`;
- `label values rep78 alrep`;
- `local d "`c(tmpdir)'dash_s06"` with `capture mkdir`.

One python helper `_hx_page(path)`:
- reads the file as UTF-8;
- `json.loads` every `<script type="application/json" ...>` body;
- returns the list of tooltip rows: every value under a `"tooltips"` key, flattened to `(label, field)` pairs;
- returns a dict of columns: every `[name, list]` pair inside a `{"type": "map", "entries": [...]}`, first one kept per name;
- returns the raw text.

The served loader is the KF-03 pattern (`test_gaps2_truth.cscript:1527-1545`): replace `if __name__ != '__main__':\n    make_document(curdoc())` with `pass`, `exec` into a dict, `make_document(Document())`. A widget is fired as `test_mode_parity._fire` does (set `value`, call `_callbacks["value"]` and `["value_throttled"]`), and found by `getattr(w, "_dash_var", None)`. Each case sets globals `hx_n<k>`/`hx_bad<k>` and is judged by the scaffold's expect/done helpers. Read their names at the top of `test_wp29_truth.cscript`; S01 copies `_gt_expect`/`_gt_done`.

- **HX-01** one-line saved: `dash scatter mpg weight, hover(rep78) saving("`d'/hx1.html") replace`, rc 0.
  - The decoded page has a tooltip row `("Repair record 1978", "@{__dash_hover_rep78}")`.
  - `Poor`, `Fair`, `Average`, `Good` and `Excellent` each occur.
  - Column `__dash_hover_rep78` has 74 entries equal, position by position, to Stata's `_hx_lab` (5 of them `.`), and column `mpg` equals Stata's mpg in order (which proves data order).
- **HX-02** named route: `dash scatter mpg weight, hover(rep78) name(g1)`, `dash build, saving("`d'/hx2.html") replace nobrowser`. Same checks.
- **HX-03** served as opened: `dash scatter mpg weight, hover(rep78 make) name(g1)`, `dash build, server saving("`d'/hx3.py") replace nobrowser`.
  - A HoverTool holds `("Repair record 1978", "@{__dash_hover_rep78}")` and a field starting `@{make}`.
  - The source it attaches to has 74 rows; for every row, `__dash_hover_rep78[i] == truth[make[i]]` (truth from `Data.get(["make", "_hx_lab"])`).
- **HX-04** served after a move: as HX-03 with `filter(foreign, type(dropdown))`; the Select whose option label is `Foreign` is fired. 22 rows; every row's make has `foreign == 1` in Stata; each label equals the truth.
- **HX-05** served, by(foreign), after a move: `dash scatter mpg weight, by(foreign) hover(rep78 make) name(g1)`, `dash build, server ... filter(price, type(range))`. The RangeSlider (`_dash_var == "price"`) is fired with `(5000.0, 15906.0)`.
  - The union of makes over every source carrying `__dash_hover_rep78` equals Stata's makes with `price >= 5000 & price <= 15906`.
  - Each source's makes share one `foreign` value.
  - Each label equals the truth.
- **HX-06** dates: `sysuse sp500, clear`, `dash scatter close open, hover(date volume) saving(...)`. The decoded page's tooltip fields include `@{date}{custom}` and one starting `@{volume}`. The served build (`dash scatter close open, hover(date volume) name(g1)`, `dash build, server ...`) does too.
- **HX-07** Unicode and string (A2): `sysuse auto`, `generate größe = mpg`, `dash scatter mpg weight, hover(make größe) saving(...)`.
  - Decoded: a tooltip field starting `@{größe}`, a field starting `@{make}`, column `größe` with 74 entries, column `make` with `AMC Concord` first.
  - Served: the CDS has `größe`.
  - No row label is asserted (A3).
- **HX-08** link (A7): `dash scatter mpg weight, hover(rep78) name(g1)`, `dash scatter price weight, hover(headroom) name(g2)`, then `dash build, link(g1 g2) filter(foreign, type(dropdown)) saving(...)` and the same with `server`.
  - In both modes, some HoverTool row has label `Repair record 1978` and some row has label `Headroom (in.)`.
  - Every `@{col}` field of each served HoverTool names a column present in every source the tool attaches to, with 74 rows.

**`test/test_adversarial.cscript`**: the run `* ==== WP-29 S06 P0.10: hover() export (HX-10..HX-25) ====` … `* ==== end WP-29 S06 ====`. It is appended after `* ==== end S08 ====` (:3034) and before `capture dash clear` / Final summary. It opens with `preserve`, `capture dash clear`, `sysuse auto, clear`, the alrep label, and closes with `macro drop dash_max_cells dash_max_bytes`, `capture dash clear`, `restore`. It uses `_adv_p19_run` and `cert_file_has` as DL-0x does; each case ends `display "HX-nn PASS: ..."`. Header `*!         HX-10..HX-25 (WP-29 P0.10)` after line 8; one summary line after :3091.
- **HX-10** (RED): `dash scatter mpg weight, hover(rep78) name(g1)`, `preserve`, `drop rep78`. Both `dash build, saving(f) replace nobrowser` and `dash build, server saving(f.py) replace nobrowser` give `r(rc) == 111`, the log has `dash build: graph 'g1': hover(): variable rep78 not found`, and `capture confirm file` gives `_rc != 0`. Then `restore`.
- **HX-11** (RED): the registry edited with `mata: st_global("dash_json_g1", subinstr(st_global("dash_json_g1"), char(34)+"hover"+char(34)+":"+char(34)+"rep78", char(34)+"hover"+char(34)+":"+char(34)+"mpg;(", 1))`. `dash build` gives r(198), the log has `registry entry 'g1' holds a hover() value that is not a list of variable names (got: mpg;()`, and no file.
- **HX-12** (RED, A4): the same with 200 × `a` (`200*"a"` in Mata). r(198); the log holds `(got: ` followed by 77 `a` and `...)`, and no line of the log holds 78 consecutive `a` (Mata: `strpos(cat(log), 78*"a") == 0` over the joined lines).
- **HX-13** (RED): the immediate route's defensive refusals, calling `_dash_render_immediate` directly on the edited `${dash_json_g1}`. The JSON cannot pass through `_adv_p19_run`'s one argument, so write that helper's pattern inline: `quietly log using <log>, name(_hx13) text replace`, `capture noisily _dash_render_immediate `"${dash_json_g1}"'`, `local rc = _rc`, `quietly log close _hx13`, then `cert_file_has` on the log:
  - hover `mpg;(` gives r(198) and `dash: hover() must name variables (got: mpg;()`;
  - hover `rep` gives r(111) and `dash: hover(): variable rep not found`;
  - the refusal comes before `_dash_write_data`, so no data file or page is written.
- **HX-14** (RED): `global dash_max_cells 200`, `dash scatter mpg weight, hover(rep78 headroom trunk) name(g1)`, `dash build, server saving(f.py) replace nobrowser` → r(134), `370 values (74 observations x 5 variables)`, `A served app embeds every observation of every variable it uses.`
- **HX-15** (RED): the one-line form with `saving()` → r(134), `370 values (74 observations x 5 variables)`.
- **HX-16** (RED): `global dash_max_bytes 100`; `mata: st_local("hxb", strofreal(sum(strlen(st_sdata(., "make")))))`; `local hxs : display %30.0fc `hxb'`, trimmed. `dash scatter mpg weight, hover(make) saving(...)` → r(134) and `dash: this dashboard would embed `hxs' bytes of text (in 1 string variable), more than the 100 dash embeds.` (871 on auto).
- **HX-17** (A1 and csv; mixed):
  - At `$dash_max_bytes 100`, `dash histogram price, bin(10) hover(make)`: the one-line form is rc 0 with the file written (GUARD); `name(h1)` + `dash build` is rc 0 (GUARD); `dash build, server` is r(134) with the bytes message (RED).
  - `macro drop dash_max_bytes`. At `$dash_max_cells 70`, `dash histogram price, bin(10) hover(foreign) name(h1)`: `dash build, server` is r(134), `148 values (74 observations x 2 variables)` and the served line (RED; base 74 x 1); `dash build, csv` is r(134) `148 values (74 observations x 2 variables)` (RED; base 74 x 1).
- **HX-18** (GUARD): `global dash_max_cells 30`, `dash scatteri 1 2 3 4, hover(mpg) saving(...)` → rc 0, the file is written, and the log holds `dash: hover() does not reach plot 1 (scatteri)`.
- **HX-19** (RED, A6): `replace make = "<img src=x onerror=alert(1)>" in 2`, `dash scatter mpg weight, hover(make) saving(...)`.
  - A python block reading the page asserts: the raw text holds no `<img src=x onerror=alert(1)>`; the decoded `make` column holds `AMC Concord` at 0 and the hostile string at 1; a tooltip field is `@{make}` and none contains `{safe}`.
  - The served build of the same: `HoverTool.tooltips` is a list, no field contains `{safe}`, and the CDS `make` holds the hostile string as data.
  - `sysuse auto, clear` afterwards.
- **HX-20** (RED: the function does not exist at the base, r(3499)): the JSON `{"graph_options":{"name":"g","hover":"gr` + char(92) + `u00f6` + char(92) + `u00dfe mpg"}}`, built with `char()` in Mata (never typed as a literal escape), with `generate größe = mpg` → out `größe mpg`, bad and why empty.
- **HX-21**: `{"graph_options":{"title":"x ` + char(92) + char(34) + `hover` + char(92) + char(34) + `:` + char(92) + char(34) + `nosuch` + char(92) + char(34) + ` y","name":"g"}}` → out, bad, why all empty. The same title followed by `,"hover":"mpg"` → out `mpg`.
- **HX-22**: hover `mpg weight mpg` → `mpg weight`; hover `mpg` + char(92) + `tweight` (a JSON tab escape) → `mpg weight`.
- **HX-23**: hover `rep` → out empty, bad `rep`, why `var`.
- **HX-24**: no hover key, `"hover":""` and `"hover":"   "` → out, bad, why all empty.
- **HX-25**: hover `200*"a"` → why `name`, bad == `77*"a" + "..."` (`ustrlen` 80). Hover `mpg` + char(96) + `x` + char(39) → why `name`, bad == that word. Hover `x;drop _all` (blank-split at the space, so the first word is `x;drop`) → why `name`, bad `x;drop`, and `_N` and `c(k)` are unchanged afterwards.

**`test/test_gaps2_truth.cscript`** AL-19 (RED): `dash scatter mpg weight, hover(rep78) saving("`d'/al19.html") replace`, with the comment `// WP-29 P0.10: rep78 is named only in hover(); it is exported.` replacing the residual comment. Its `_gt_done` text: `hover(rep78), a variable no layer plots, shows its value labels`.

**Mutation table** (each break must turn the named test red):

| break this | test that must die |
|---|---|
| drop the `needed_vars | _hvars` union | HX-01, `test_the_immediate_route_unions_hover_into_needed_vars` |
| drop the `all_vars | _hv_k` union | HX-02, HX-03, HX-08 |
| count hover on a computed-only graph (no `_hv_show`) | DL-03e (74 → 148), HX-17 one-line/build parts |
| leave csv out of the build flag | HX-17 csv part |
| Python twin counts hover everywhere | `test_a_hover_variable_on_a_computed_only_graph_does_not_count` |
| saved bytes re-check not twinned | `test_a_string_hover_variable_no_layer_shows_does_not_count_saved`, HX-17 one-line part |
| allow abbreviations (`_st_varindex(w, 1)`) | HX-23 |
| no 80-character cut | HX-12, HX-25 |
| read hover with a raw scan (`_dash_extract_vars` style) | HX-20, HX-21 |
| key the note on (gname, name) or on the panel | `test_missing_hover_names_are_one_bounded_note`, `test_by_panels_name_a_missing_variable_once` |
| echo a name without `_dash_display` | `test_a_hostile_absent_hover_name_is_shown_bounded` |
| omit the copy-list entry | `TestTheServedAppCarriesEveryName`, every `[served]` note test |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| hover-only variable in the tooltip, label text equal to Stata's per row, 74 rows kept | cscript HX-01..HX-03, AL-19 | none (Stata computes) | yes |
| after a filter move, by(), link() | cscript HX-04, HX-05, HX-08; pytest guards in test_value_labels_drawn.py | none | yes |
| date, string, Unicode | cscript HX-06, HX-07 | none | yes |
| cells and bytes counts (A1, csv, served) | cscript HX-14..HX-18, DL-03e; pytest TestTheCount, TestTheByteLimit | none | yes |
| refusals: dropped variable, hostile registry, immediate defensive | cscript HX-10..HX-13 | none | yes |
| hostile value | cscript HX-19 | none | yes |
| extractor unit cases | cscript HX-20..HX-25 (direct) | none | n/a |
| twins and the note | pytest TestTheHoverColumns, TestHoverReachesEveryLayerOrIsReported (new + flipped), CORPUS | none | yes |
| code shape on both routes | pytest TestBothRoutesExportHover | none | n/a |
| served names | test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads | none | served |
| maps and header | test_function_test_map.py, test_program_coverage_map.py, test_file_headers.py | none | n/a |

Acceptance criteria:
- **AC-06.1** These pass with no new skips: `python3 -m pytest test/test_embedded_cells.py test/test_hover_export.py test/test_value_labels_drawn.py test/test_mode_parity.py test/test_function_test_map.py test/test_program_coverage_map.py test/test_file_headers.py -q`, and `-k "CarriesEveryName or DefinesEveryNameItReads"` over `test/test_statistical_helpers.py test/test_resource_limits.py`.
- **AC-06.2** Under `WP29_ONLY=S06`, `test_wp29_truth.cscript` prints `HX-01 PASS` .. `HX-08 PASS` (8 lines), no `FAIL`, and its summary passes. `test_adversarial.cscript` prints `HX-10 PASS` .. `HX-25 PASS` (16 lines) and `DL-03e PASS: hover() reaches the graph too; its hover() variable is exported, but no layer of h1 can show it, so it does not inflate the count`. `test_gaps2_truth.cscript` under `GAPS2_ONLY=S14` prints `AL-19 PASS`.
- **AC-06.3** The full suite is green once in the worktree. BUGS.md's P0.10 entry is `- [x]` with `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.10). …` naming existing tests. `WP29_OPEN` has no `"P0.10"` key. `grep -c '<!-- WP-29 P0.10 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-29, P0.10)' CHANGELOG.md` prints 2.
- **AC-06.4** `gitnexus_detect_changes()` lists only this section's symbols. The commit subject ends `(WP-29 P0.10)`, and its message has no `claude|anthropic`.

## Tasks

**Commit boundary.** ONE commit, P0.10, holding 06-03 to 06-11. Subject: `Export every variable hover() names, saved and served (WP-29 P0.10)`. It is made by 06-11 on `wp29-s06` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s06`, after the section's one full pytest run there. The merger lands it on `wp29-p0` with the same message (index step 1).

The body:
1. opens with `<scratch>/06-P0.10-failure.txt`;
2. then the measured defect and what changed where;
3. then one `Regression: <node or script CASE> -- failed at <base sha> with <text>` line per RED test;
4. one `Flipped: <node> -- <old expectation> was wrong because <why>` line per flip (from `<scratch>/06-flips.txt`);
5. `BUGS.md: "<title>" (closed)`.

There is no `Fixture:` line. Every Stata run goes through `scripts/stata_slot.sh <scratch> <file>.do` with `dash_nobrowser=1`. Every cscript run goes through the two-line driver of "Stata truth". Never use the GUI and never a bare `stata-mp`. No AI references anywhere. `$WT` below is the worktree path; run git as `git -C "$WT"`.

<task type="auto" id="06-01">
  <name>Index the worktree and measure impact</name>
  <files>none</files>
  <action><![CDATA[
    Index and measure:
    1. In the worktree, run `(cd "$WT" && gitnexus analyze)`. analyze also rewrites context files and writes `.gitnexus/`, so then run `git -C "$WT" status --porcelain`. If `CLAUDE.md` or `AGENTS.md` changed, restore them with `git -C "$WT" checkout -- CLAUDE.md AGENTS.md`. Never stage `.gitnexus/`.
    2. Run `gitnexus_impact({target, direction: "upstream"})` for each of: `_dash_embedded_cells`, `_make_figure_body`, `_generate_app_source`, `__init__` of `DashRenderer` (use `gitnexus_context` to disambiguate), `_dash_prepare_spec`, `_dash_render_immediate`. If the index cannot resolve a Stata program, record that and use `grep -n` callers instead.
    3. Write each target's direct callers, affected processes and risk level to `<scratch>/06-impact.txt`.
  ]]></action>
  <verify><![CDATA[`<scratch>/06-impact.txt` has one block per target with a risk level; `git -C "$WT" status --porcelain` shows no modified tracked file.]]></verify>
  <done>The blast radius of every symbol this section edits was recorded and the worktree was left clean.</done>
</task>

<task type="auto" id="06-02">
  <name>Report HIGH-risk targets before editing</name>
  <files>none</files>
  <action><![CDATA[
    If any target in `<scratch>/06-impact.txt` is HIGH or CRITICAL (index R8 expects `_make_figure_body`), STOP before task 06-06. Send the orchestrator the target, its risk, its direct callers and the exact edit planned (TR-06.6: one added call after `_dash_note_hover_unreached`), and wait for an explicit go-ahead from the maintainer (CLAUDE.md GitNexus rules). Tasks 06-03 to 06-05 add tests only and may proceed meanwhile. If no target is HIGH or CRITICAL, record "no HIGH/CRITICAL" in the file and continue.
  ]]></action>
  <verify><![CDATA[`<scratch>/06-impact.txt` ends with either "no HIGH/CRITICAL" or the maintainer's recorded approval naming each HIGH/CRITICAL target.]]></verify>
  <done>Every HIGH or CRITICAL target was reported and approved before any source edit.</done>
</task>

<task type="auto" id="06-03">
  <name>Write the failing count and export tests</name>
  <files>test/test_embedded_cells.py, test/test_hover_export.py, test/test_value_labels_drawn.py</files>
  <action><![CDATA[
    Write the tests:
    1. In `test/test_embedded_cells.py`, add to `TestTheCount` the six tests and create `TestTheHoverColumns` with its two tests, exactly as "TDD test stubs" names them, using the file's `_plot`, `_graph`, `_master`, `_kpi`, `_LIMITS`. Add `TestTheTwoLanguagesAgree::test_the_types_hover_cannot_reach_agree`. Parse dash.ado with `re.search(r'c_local _pt_literal\s+"([^"]*)"', ado)` beside the existing univar/onefit reads, and the note's frozensets with `re.findall(r'"([a-z]+)"', block)` over the text between `computed = frozenset({` and `literal = frozenset({...})`.
    2. Create `test/test_hover_export.py`. Its module docstring states P0.10, the base measurements (one-line page with 0 × `__dash_hover_rep78`; served tooltips weight and mpg only) and the A1 rule. It holds `TestBothRoutesExportHover` (6 text tests), `TestTheByteLimit` (3), `TestTheServedApp` (1), `TestRowsWithAMissingHoverValueAreKept` (2) and `TestAnUnlabelledHoverOnlyVariable` (parametrised saved/served). Import `test_mode_parity as tp`, `from conftest import make_data_json`, and `dash_render as dr` after inserting the repo root and `test/` on `sys.path`, as `test_value_labels_drawn.py:17-22` does.
    3. In `test/test_value_labels_drawn.py`, add the four GUARD tests to `TestHoverShowsValueLabels`, importing `_render` and `_move` from `test_saved_filter_layers`.
    Do not touch any source file. Run the three files and keep the output for 06-05.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_embedded_cells.py test/test_hover_export.py test/test_value_labels_drawn.py -q -n0 -p no:cacheprovider 2>&1 | tail -25`:
- no collection error;
- the failures are exactly the RED tests of these three files in "TDD test stubs" (2 in TestTheCount, 2 in TestTheHoverColumns, 6 in TestBothRoutesExportHover, 1 in TestTheByteLimit, 1 in TestTheServedApp);
- every GUARD passes, including the four A9 guards (if one fails at the base, STOP and report: a JavaScript change would be needed, outside this design).]]></verify>
  <done>Every count, twin and export regression test existed and failed at the base for its recorded reason, and every guard passed.</done>
</task>

<task type="auto" id="06-04">
  <name>Write the failing note and parity tests</name>
  <files>test/test_mode_parity.py</files>
  <action><![CDATA[
    Write the parity tests:
    1. In `TestHoverReachesEveryLayerOrIsReported`, add the four RED tests of "TDD test stubs", each parametrised over `("saved", "served")` with `_figures_in`. Select notes with `[n for n in caught if "not in the data" in n]`.
    2. Flip `test_a_huge_hover_list_is_one_note` (:3133-3142): `unreached = [n for n in notes if "does not reach" in n]`, `missing = [n for n in notes if "not in the data" in n]`; assert `len(unreached) == 1`, `missing == ["dash: hover() of graph 'g1' names variable(s) not in the data -- 'v0', 'v1', 'v2' and 4,997 more; the tooltip leaves them out."]`, `len(notes) == 2`, and `"v4999"` in no note; keep `_assert_rows_align(figs[0])`. Add a docstring sentence naming WP-29 P0.10.
    3. Append the two CORPUS cases after `_case("hover() of a date", ...)` (:1649) and the `_MUST_WARN` entry.
    4. Append the flip to `<scratch>/06-flips.txt` as `Flipped: test/test_mode_parity.py::TestHoverReachesEveryLayerOrIsReported::test_a_huge_hover_list_is_one_note -- one hover() note in all was wrong because hover() names absent from the data now get their own bounded note (P0.10)`.
    Do not edit `ALLOWED`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py -q -p no:cacheprovider -k "Hover or hover" 2>&1 | tail -15`: the failures are exactly the 8 new RED nodes, the 2 flipped nodes and the `test_same_warnings` node of the "hover() naming a variable not in the data" case; every other node passes.]]></verify>
  <done>The note's regression tests and the flipped huge-list test failed at the base, and the new corpus cases were in place with only their must-warn check red.</done>
</task>

<task type="auto" id="06-05">
  <name>Write the failing certification cases</name>
  <files>test/test_wp29_truth.cscript, test/test_adversarial.cscript, test/test_gaps2_truth.cscript</files>
  <action><![CDATA[
    Write the certification cases:
    1. Append the S06 block of "Stata truth" (HX-01..HX-08, as "TDD test stubs" specifies) to `test/test_wp29_truth.cscript`, above `* ==== append new blocks above this line ====`. Use the scaffold's expect/done helpers (read their names at the script's top), never `exit` on a failure, and add the header line.
       - Build `_hx_lab` after each case's dash commands, read it in the python block with `sfi.Data.get`, then `drop _hx_lab`.
       - The python blocks read only generated files and Stata data. They never call back into Stata commands and never `exec` user data.
       - Separators inside globals are built with `chr(31)` in Python and `char(31)` in Mata.
    2. Append the run HX-10..HX-25 to `test/test_adversarial.cscript` after `* ==== end S08 ====`, plus the header and summary lines. Build every JSON with a backslash or a backtick from `char(92)`/`char(96)` in Mata, never from a typed escape.
    3. In `test/test_adversarial.cscript` DL-03e (:2980), change only the PASS text to the one in AC-06.2.
    4. In `test/test_gaps2_truth.cscript`, flip AL-19 (:1077-1086) as "TDD test stubs" says.
    5. Append to `<scratch>/06-flips.txt`:
       - `Flipped: test/test_adversarial.cscript DL-03e -- "the hover variable itself is not exported" was wrong because every hover() variable is now exported; it is still not counted, as no layer of a histogram can show it`;
       - `Flipped: test/test_gaps2_truth.cscript AL-19 -- hover(rep78) on a plotted rep78 hid the defect; it now names a variable no layer plots`.
    6. Run the three scripts through the driver against the unmodified source: `WP29_ONLY=S06` for the truth script, no gate for test_adversarial (it stops at its first failing case), `GAPS2_ONLY=S14` for test_gaps2_truth.
    7. Save into `<scratch>/06-P0.10-failure.txt` the failing pytest output of 06-03 and 06-04, then every `HX-0n FAIL:` line and the summary of the truth log, the first failing adversarial case and its r(), and the `AL-19 FAIL:` line.
    Do not commit.
  ]]></action>
  <verify><![CDATA[Checks:
- `grep -c "HX-0[1-8] FAIL" <scratch>/run_test_wp29_truth.log` prints 8 and `grep -c "HX-0[1-8] PASS"` prints 0;
- `<scratch>/run_test_adversarial.log` ends in an `assert` failure (r(9)) at HX-10 after printing `DL-03e PASS: hover() reaches the graph too; its hover() variable is exported, but no layer of h1 can show it, so it does not inflate the count`;
- `grep -c "AL-19 FAIL" <scratch>/run_test_gaps2_truth.log` prints at least 1;
- `<scratch>/06-P0.10-failure.txt` exists and holds all three.]]></verify>
  <done>Every certification case of this section existed and failed at the base, its failure text was saved for the commit body, and DL-03e's count stayed as it was.</done>
</task>

<task type="auto" id="06-06">
  <name>Add the Mata hover extractor</name>
  <files>dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    Insert `_dash_extract_hover_vars` with its comment block exactly as TR-06.1 gives it, as section 6a between the end of `_dash_extract_vars` (:2191) and the `// 6b. QUALIFIER / FACET VARIABLE EXTRACTOR` banner (:2195). Add its four header lines to the Public API after the `_dash_extract_vars` entry (:157-159). Add the `program_coverage_map.py` entry of TR-06.7 after `_dash_extract_qual_vars` (:382-383). Do not change `_dash_extract_vars`, `_dash_json_get_str`, `_dash_blank_words` or `_dash_graph_touched`.
  ]]></action>
  <verify><![CDATA[`grep -n "^void _dash_extract_hover_vars" dash_parse.mata` prints one line between the `_dash_extract_vars` definition and the `6b.` banner; `python3 -m pytest test/test_hover_export.py -q -n0 -p no:cacheprovider -k mata_extractor` passes.]]></verify>
  <done>dash_parse.mata held the checked, bounded hover() reader with its header entry, and the coverage map named its direct case first.</done>
</task>

<task type="auto" id="06-07">
  <name>Export and count hover on both routes</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-06.2 to `_dash_render_immediate` and TR-06.3 to `_dash_prepare_spec` exactly, then TR-06.4's `_needed` entry. Update the comments named in TR-06.3. Read each edited region afterwards:
    - `_cap_vars` is defined on every path, including the `_varfree` path;
    - `_hv_show_`k'` is set before the touched branch reads it;
    - the saved branch calls `_dash_byte_cap `_byte_vars'` and the served branch `_dash_byte_cap `all_vars'`.
    Echo user text only through `_dash_say` with the value as its third argument or `st_local(...)` inside the first, never by macro expansion of `_hv_bad` or `gname`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_hover_export.py -q -n0 -p no:cacheprovider -k BothRoutesExportHover` passes, and `python3 -m pytest test/test_file_headers.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider` passes (header and `_needed` agree; the new function has its map entry).]]></verify>
  <done>Both routes exported every hover() variable, counted it only where the page holds it, and refused a vanished or malformed one before writing anything.</done>
</task>

<task type="auto" id="06-08">
  <name>Twin, note and copy in the renderers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-06.5 and TR-06.6 in dash_render.py:
    - add `_dash_hover_shown` and `_dash_hover_unembedded` after `_dash_embedded_cells`, and the hover clause in `_dash_embedded_cells`;
    - change the saved bytes re-check in `DashRenderer.__init__` (:25108);
    - add `_dash_note_hover_missing` after `_dash_note_hover_unreached`, its saved call in `_make_figure_body` and its five emitted lines in the served `_dash_figure_for`;
    - add the copy-list line after `"_dash_csv_payload", "_dash_frame_filter_mask",` (index R2).
    Add the three `function_test_map.py` entries of TR-06.7. Do not touch `_collect_graph_vars`, `_dash_build_hover`, `_hover_cols_of` or any JavaScript.
  ]]></action>
  <verify><![CDATA[These pass:
- `python3 -m pytest test/test_embedded_cells.py test/test_hover_export.py test/test_value_labels_drawn.py -q -p no:cacheprovider`;
- `python3 -m pytest test/test_mode_parity.py -q -p no:cacheprovider -k "Hover or hover"`;
- `python3 -m pytest test/test_statistical_helpers.py test/test_resource_limits.py -q -p no:cacheprovider -k "CarriesEveryName or DefinesEveryNameItReads"`;
- `python3 -m pytest test/test_function_test_map.py -q -n0 -p no:cacheprovider`.]]></verify>
  <done>The saved page's counts agreed with Stata's, both renderers named an absent hover() variable once per graph in the same words, and the served app defined every name it read.</done>
</task>

<task type="auto" id="06-09">
  <name>Turn the certification cases green</name>
  <files>none</files>
  <action><![CDATA[
    Run the three scripts through the driver as in 06-05: `WP29_ONLY=S06` for test_wp29_truth, the whole test_adversarial, `GAPS2_ONLY=S14` for test_gaps2_truth. Then run, one at a time, the cscripts that use hover(): `test_option_validation.cscript`, `test_help_claims_2.cscript`, `test_help_claims_7.cscript`, `test_qualifier_in_stata.cscript`, `test_abbreviations.cscript`. Then run the changed pytest files of 06-08's verify together with `test/test_server_layer_defects.py test/test_value_labels_drawn.py test/test_csv_export.py` (any file `grep -l "hover" test/test_*.py` lists may be added). A failure in a test this section did not list is a regression of this section: fix the code, not the test. A test that pinned the old silence is flipped only with a `Flipped:` line in `<scratch>/06-flips.txt` and its reason.
  ]]></action>
  <verify><![CDATA[Checks:
- `grep -c "HX-0[1-8] PASS" <scratch>/run_test_wp29_truth.log` prints 8 and `grep -c " FAIL" <scratch>/run_test_wp29_truth.log` prints 0;
- `grep -c "HX-[12][0-9] PASS" <scratch>/run_test_adversarial.log` prints 16 and the log ends `All adversarial security tests PASSED.`;
- `grep -c "AL-19 PASS" <scratch>/run_test_gaps2_truth.log` prints 1;
- the five other scripts end with no `r(` error and no SKIP;
- the pytest runs report 0 failed.]]></verify>
  <done>Stata certified the export in both modes on every route, every refusal and count held, and no other hover() script or test regressed.</done>
</task>

<task type="auto" id="06-10">
  <name>Document hover export in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Edit only these paragraphs (index R3):
    1. **Tooltips** (:2606-2630): append, after its last sentence, that:
       - every variable hover() names is exported with the data whether or not a layer plots it, so its value is in the tooltip of the saved dashboard and the served app, before and after a filter move;
       - its values are part of the saved page's source like the variables the layers draw (no "every row" wording: S14 owns the row policy);
       - it counts toward `{cmd:$dash_max_cells}` (a string one also toward `{cmd:$dash_max_bytes}`) on the saved page when a layer of its graph can show it or `{cmd:csv}` is given, and always in a served app (`{help dash##limits:Resource limits}`);
       - `{cmd:dash build}` and `{cmd:dash serve}` refuse a hover() variable no longer in memory with r(111).
    2. **`$dash_max_cells` entry** (:1596-1603): "its variables -- the ones its layers plot and the ones {cmd:hover()} names when one of its layers can show them -- and qualifier columns".
    3. **`$dash_max_bytes` entry** (:1605-1610): a hover() string variable counts on the saved page under the same rule, and a served app counts every string variable it exports. Keep `default 50,000,000`, `at most 500,000,000` and `r(134)`, which `test_resource_limits.py::TestTheHelpDocumentsEveryLimit` reads.
    4. **"What the data limit counts"** (:1645-1656): add that a graph's hover() variables are among its counted variables when a layer can show them, and that a graph made only of computed layers or of scatteri, pci, pcarrowi or function exports them but does not count them unless csv is given.
    5. **:626-633**: after "a variable that does not exist is r(111)", add that dash build and dash serve also give r(111) for a hover() variable dropped after the graph was registered.
    Then run `grep -n "hover" test/test_help_claims_*.py test/test_resource_limits.py` and update any pin of a changed sentence.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_resource_limits.py test/test_help_claims_1.py test/test_help_claims_3.py test/test_help_claims_5.py -q -p no:cacheprovider` passes; `grep -c "hover()} names" dash.sthlp` prints at least 2.]]></verify>
  <done>The help stated what hover() exports, when it counts toward each limit, and the r(111) for a vanished variable, without touching another section's paragraphs.</done>
</task>

<task type="auto" id="06-11">
  <name>Close P0.10 and commit once</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Close the entry, run the suite and commit:
    1. Read the title of `WP29_OPEN["P0.10"]` in `test/test_tracking_documents.py` and find `- [ ] Title: <that title>` in BUGS.md (S01's open entry). Change it to `- [x]` in place, keep its other fields, and rewrite its Resolution (index "BUGS.md" delta form). The Resolution:
       - starts `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.10).`;
       - names `_dash_extract_hover_vars`, the needed_vars/all_vars/row_vars unions, the A1 counting rule with csv, the per-mode bytes cap, `_dash_hover_shown`/`_dash_hover_unembedded`/`_dash_embedded_cells`, `_dash_note_hover_missing` in both renderers and its copy-list entry;
       - is pinned by `test/test_embedded_cells.py::TestTheCount::test_a_hover_only_variable_counts_on_a_graph_that_shows_it`, `test/test_hover_export.py::TestBothRoutesExportHover::test_the_build_route_unions_hover_into_all_vars_and_row_vars`, `test/test_mode_parity.py::TestHoverReachesEveryLayerOrIsReported::test_a_hover_variable_not_in_the_data_is_named`, `test/test_wp29_truth.cscript HX-01`, `test/test_adversarial.cscript HX-10`;
       - ends `Residual, deferred (WP-29): ` listing: (1) a graph made only of computed or literal layers that hover() names is still counted by its own plotted rows on the saved page (the G3 touched rule; DL-03e's 74) although the page holds only its drawn output; (2) hover() written inside a layer's parentheses and after the comma keeps only the rightmost list; (3) .a-.z show as . in a tooltip (GAPS2 G12); (4) only if S03 has not merged: an unlabelled hover-only variable's row label is blank until P0.3.
    2. Delete the `"P0.10": ...` line from `WP29_OPEN`.
    3. In CHANGELOG.md, replace `<!-- WP-29 P0.10 -->` under `### Fixed in WP-29` with two lines ending `(WP-29, P0.10)`:
       - (a) `dash scatter mpg weight, hover(rep78)` now shows rep78, by its value label, in the tooltip of the saved page and the served app, on the one-line route and through dash build and dash serve, before and after a filter move; a variable named only in hover() was never exported, and the tooltip left it out with rc 0 and no note.
       - (b) hover()'s variables now count toward the data limits: on the saved page when a layer of the graph can show them (or csv is given), in a served app always. `dash scatter mpg weight, hover(rep78 headroom trunk)` at `dash_max_cells 200` counted 148 values and built; it is now refused with 370 values (74 observations x 5 variables), r(134). `dash build` and `dash serve` refuse a hover() variable dropped after name() with r(111) where they left it out with rc 0. The CSV download carries the hover() columns.
       The old values come from `<scratch>/06-P0.10-failure.txt` and the Evidence table.
    4. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`, then the section's ONE full run `python3 -m pytest test/ -q` in the worktree (read its log; never launch a second). A failure is fixed in code, or flipped with a `Flipped:` line, then only the failed file is rerun.
    5. Run `gitnexus_detect_changes()` and check `git -C "$WT" diff --cached --name-only` stages exactly: dash_parse.mata, dash.ado, dash_render.py, dash.sthlp, CHANGELOG.md, BUGS.md and the test files of this section.
    6. Write the message to `<scratch>/06-commit-msg.txt` in the Commit boundary form. Run `grep -Ei 'claude|anthropic' <scratch>/06-commit-msg.txt` (must print nothing), then `git -C "$WT" commit -F <scratch>/06-commit-msg.txt`, then grep `git -C "$WT" log -1 --format=%B` again.
  ]]></action>
  <verify><![CDATA[Checks:
- the full suite's tail reports 0 failed and no new skips;
- `grep -c '<!-- WP-29 P0.10 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-29, P0.10)' CHANGELOG.md` prints 2;
- `grep -c '(WP-29, P0.10)' BUGS.md` prints 1;
- `python3 -m pytest test/test_tracking_documents.py -q -n0` passes;
- `git -C "$WT" log -1 --format=%s | grep -c '(WP-29 P0.10)$'` prints 1 and `git -C "$WT" log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0;
- `git -C "$WT" show --stat HEAD` lists no CLAUDE.md, .gitignore, AGENTS.md, .gitnexus or *.html.]]></verify>
  <done>P0.10 was closed in BUGS.md naming existing tests, its CHANGELOG marker was replaced by the two lines, its WP29_OPEN key was gone, and one green commit on `wp29-s06` carried the whole section.</done>
</task>

## Section completion criteria

- On the one-line route, `dash build` and `dash build, server`, every hover() variable is exported. Its value-label text equals Stata's `: label` text on every row, 74 rows kept, in both modes, before and after a dropdown move, under by() and link(). This is proven by HX-01..HX-08 and AL-19 from Stata.
- Counts:
  - On the saved page, hover() variables count toward cells and bytes exactly when a layer can show them or csv is given; in a served app they always count. Stata and the Python twins agree (HX-14..HX-18, DL-03e unchanged at 74, TestTheCount, TestTheByteLimit).
  - A vanished hover() variable is r(111), a malformed registry value r(198) with an 80-character echo, and no file is written (HX-10..HX-13).
- The renderers name an absent hover() name once per graph in identical, bounded words in both modes. The served copy list carries the note.
- Tests: every RED test failed at the base and passes now; every flip has a `Flipped:` line; nothing was deleted; no new cscript, runner or hygiene edit.
- One commit on `wp29-s06`, subject ending `(WP-29 P0.10)`, with the BUGS.md entry closed in place, the marker replaced and `WP29_OPEN["P0.10"]` gone.

## Notes

- **Two lists, not one.** `needed_vars`/`all_vars` are the EXPORT (always with hover). `_cap_vars`/`row_vars`/`_byte_vars` are the SAVED COUNTS (hover only where shown, or under csv). The served counts use the export list. Mixing them up re-creates review truth dispute 1 (a 148 refusal for a page holding 10 bins) or a renderer refusal after Stata said yes.
- **Literal-only graphs.** `dash scatteri 1 2 3 4, hover(mpg)` now exports mpg (needed_vars is no longer empty, so `_varfree` is 0). It counts 0 cells and keeps its "does not reach" note (HX-18). Keep the extractor call BEFORE the `_varfree` test, as TR-06.2 places it.
- **Typed escapes.** A tool layer may decode a typed backslash-u sequence before it reaches the file (measured while writing this plan: a heredoc's backslash-u text arrived as `ö`). In cscripts build every backslash and backtick with `char(92)`/`char(96)`; in Python use `chr()`.
- **Registry echo.** `gname` comes from the registry; pass it through `st_local("gname")` inside the `_dash_say` call, never by macro expansion in the message.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. A truth run that exits 222 is a SKIP, not a pass; check `c(python_exec)`.
- **S13 (batch 2)** adds a served token. HX-03..HX-05, HX-08 and HX-19 load the app with the KF-03 pattern (`exec` + `make_document(Document())`), which never goes through HTTP. If S13 changes `make_document`'s entry, it keeps these cases working, as it must for KF-03.
- **S14 (batch 3)** narrows which ROWS are exported. It edits the same `_dash_prepare_spec`/`_dash_render_immediate` lines. Keep this section's unions as separate, commented statements so S14's patch applies to them.
- **Merge rules.**
  - R1: the S06 truth block goes in section order above the marker. The adversarial run is contiguous, after S02's run (merge order).
  - R2: one copy-list line after the `_dash_csv_payload` line; three function-map entries; one coverage-map entry.
  - R3: only the five help paragraphs of 06-10; only the P0.10 marker; only the P0.10 BUGS entry and `WP29_OPEN` key.
  - R4: the hover extraction is S06's alone; section 6a is the new function's place.
  - R6: two CORPUS cases and one `_MUST_WARN` key; `ALLOWED` untouched.
  - R7: three flips, each with its `Flipped:` line.
  - R8: 06-01/06-02.
- **Commit-body line forms.**
  - `Regression: test/test_embedded_cells.py::TestTheCount::test_a_hover_only_variable_counts_on_a_graph_that_shows_it -- failed at <base sha> with assert ['y', 'x'] == ['y', 'x', 'z']`
  - `Regression: test/test_wp29_truth.cscript HX-01 -- failed at <base sha> with HX-01 FAIL: <text>`
  - `Flipped: ...` as 06-04/06-05 recorded them.
  - `BUGS.md: "<title>" (closed)`.

### Notes for the closeout (S15; index A5: these documents are S15's alone)

- **GAPS2.md G16** (line 1492) **Tracked:** the residual "on the one-line route a hover()-only variable is not exported (BUGS.md's earlier hover-export entry)" is closed by this section's commit. The residual was also too narrow: the named route and the served app dropped the variable too (Evidence table). S15 decides FULLY vs PARTLY closed for G16 against its other residual ("an x or y variable not named in hover() keeps its number in the tooltip"), which this section does not touch.
- **GAPS2.md G3** (line 1414) and **BUGS.md:2632-2633** say hover() makes a graph's rows count. Amend G3's Tracked line with the rule: hover()'s own variables count only where a layer can show them or csv is given; the graph itself is still treated as touched. Do not edit the old BUGS entry.
- **DROPIN-REMAINING.md P0.10** (line 46): annotate it with this commit. Its sources REM-09-07-HOVER-EXPORT, GAPS2-G16-res and REM-09-07-HOVER-TEST are all answered: export, the residual, and the test that pinned the defect (DL-03e text, AL-19).
- **dash.sthlp:183 and GAPS2 G1:** the residual says a variable named like a derived glyph field (`top`, `y`) is shadowed in hover(). The design review found it not reproduced on the prototype for bar `hover(top)` and scatter `hover(y)`. Hover-only variables now reach that path, so S15.5 (help consistency) should re-measure it and correct the sentence if it is no longer true.
- **Residuals to list in S15.7:** the four in the closed entry's Resolution.
- **AGENTS.md invariant (S15.4):** "hover() variables are exported on both routes; counted on the saved page only where a layer can show them (or csv); Mata `_dash_spec_types_in(..., _pt_univar _pt_onefit _pt_literal)` and Python `_DASH_COMPUTED_ONLY_TYPES | _DASH_LITERAL_TYPES` are the one rule", with test `test_embedded_cells.py::TestTheTwoLanguagesAgree::test_the_types_hover_cannot_reach_agree`.
