# Section 13: Textbox grammar (B3, B6, B7)

> Part of: WP-28 · Gaps: B3, B6, B7 · Risk: yellow · Batch: 2 · Depends on: 02 · Blocks: 15, 19 · Tasks: 15, 3 commits (B7, B3, B6)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **02** · Blocks **15, 19** · Risk **yellow** · Commits: three commits, one per gap, made in the order B7 (13-01..13-03), B3 (13-04..13-12), B6 (13-13..13-15) → CHANGELOG `Results that change` (three markers)

- D10: read `size` (not the raw SVG inventory's key) from `svg_texts`; the fixture's metadata key is `_meta`; the B6 BUGS.md title is `An empty xtitle() or ytitle() does not remove the axis title` (no quotation marks in a title).
- D11: TBG-01..TBG-06 are a block `* ==== S13 B3 B6 B7: textbox grammar ====` of the one truth script `test/test_gaps2_truth.cscript` (13-05 adds TBG-01, 02, 03, 05, 06; 13-13 adds TBG-04); no new cscript, no runner edit, no hygiene-pin edit; JSE-46's extension stays in `test/test_json_escaping.cscript`.
- Stubs: a compound-quoted `ytitle2`; a full name beside an abbreviation (`size(large) c(red)`); the hostile-title probe TBG-06; the `_meta` keys.
- D1/D7: each gap's failing tests are written by that gap's first task (13-01, 13-04, 13-13) and land in that gap's commit; B7 is closed first because B3's `axis(2)` route and B6's `ytitle2("")` are only visible once the second axis's title is read as a textbox.
- D4 merge order (index.md): this section merges before S17, S16 and S14 in batch 2 (S16 calls `_dash_textbox`).

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

Every text option twoway takes -- `title()`, `subtitle()`, `note()`, `caption()`, `xtitle()`, `ytitle()`, and dash's own `ytitle2()`/`xtitle2()` -- is a textbox: `"string" ["string" ...] [, suboptions]`, where each string is a line and the sub-options may be abbreviated to Stata's documented minimums (`c:olor`, `si:ze`, `j:ustification` ...). dash reads the sub-options only under their full names, so GAPS2 measures that `title("T", c(red))` draws the three lines `T`, `,`, `c(red)` in the scheme's colour with no warning, and `ytitle("Volume", axis(2))` titles the left axis with the whole tail as text (B3). `xtitle("")`, which `axis_title_options.sthlp:218-228` makes the standard way to remove an axis title, still draws `weight`, and `ytitle("")` still draws `mpg` (B6). `ytitle2("P2")` draws `"P2"` with its quote marks, `ytitle2("a" "b")` one quoted line, and `ytitle2("P2", size(large))` the sub-option verbatim (B7). All of it in both render modes, rc 0.

After this section a textbox is read as twoway reads it: any legal spelling of a sub-option is either honoured (`size()`, `color()`, `prefix`, `suffix`, `axis(1|2)`) or named once in the note, never drawn; `axis(2)` on `ytitle()`/`xtitle()` routes the title to the second axis before dash.ado's repeat merge can fold it into the first axis's copy; an option given with empty text removes the title while an absent option keeps the default; and the second axis's title goes through the same reader, the same lines and the same `size()`/`color()` styling as the first, whichever renderer adds the axis first. Honoured options print nothing (DISCOVERY Q22).

The three gaps share one component: `_parse_textbox_opt` and the table it splits on, `_dash_textbox` which names what is not honoured, `_dash_axis_labels` which turns the text into an axis title, and `_dash_add_secondary_axes`, the one reader of `{n}title2`. Truth comes from twoway's own SVG through section 02's helper, recorded once into `test/fixtures/text_truth.json` by a new `scripts/extract_text_truth.do`, which section 15 (batch 3) extends with its legend probes.

**Test order (CLAUDE.md rule 7) and commit rule (D1): each gap's first task writes that gap's regression tests**, runs them against the tree before the gap's fix and saves the failure text to the scratch directory -- it does not commit (a red tree is never committed, rule 4). B7 goes first (13-01 tests, 13-02 fix, 13-03 close and commit `(GAPS2 B7)`), because B3's `axis(2)` route hands the second axis a raw textbox and B6's `ytitle2("")` needs the same reader; then B3 (13-04 tests, 13-05 truth block, 13-06 fixture, 13-07 to 13-11 fix and flips, 13-12 close and commit `(GAPS2 B3)`); then B6 (13-13 tests, 13-14 fix, 13-15 close and commit `(GAPS2 B6)`). Each commit's body opens with its gap's saved failure text (Q24; S01 TR-01.9); the failing tests land in that commit, never alone.

## Risk: [yellow] — one table drives every text option in both renderers, and one Mata rewrite runs before every option list is parsed

- **Why:** the split regex and the honoured set are consulted for every title, note, caption and axis title dash draws; a wrong minimum abbreviation silently changes what is text and what is a sub-option. The Mata routing rewrites raw option text before `-syntax-` sees it.
- **Risk factors:** (1) the served app receives `_TEXTBOX_SUBOPT_RE` and `_DASH_TEXTBOX_HONOURED` by copy (constants list 24326-24428), so a table that is not in the list leaves the two modes reading different grammars; (2) the two renderers call `_dash_add_secondary_axes` on opposite sides of `_dash_style_axis_titles` (saved 22096 after, template 26207 before); (3) `_dash_rep_merge` (dash_parse.mata 4826-4855) folds every copy of `ytitle` into one before Python runs, so a Python-only routing cannot draw `ytitle("a") ytitle("b", axis(2))`; (4) 40 pinned tests read `_parse_textbox_opt`'s split; (5) `_dash_route_axis2` runs on the raw option text of every `dash` command before `syntax`, so an exception there is an r(3xxx) on every call, and a title holding `'`, `$`, a backtick or the text `axis(2)` inside quotes must pass through it unchanged.
- **Mitigation:** the table is transcribed from Stata's help and pinned by a test over every prefix of every name; the split rule becomes twoway's own `_parse comma` (the first top-level comma followed by a name), so the 15 measured split cases and the 35 measured line cases keep passing unchanged; styling of the second axis moves inside `_dash_add_secondary_axes` so renderer order cannot matter; the Mata route is proven by a truth-script case that stores both titles, everything it does not rewrite is returned as typed, and the hostile-title case TBG-06 (JSE-42..49's titles) proves nothing is expanded; a Python rewrite beside `_dash_lone_second_axes` covers hand-built specs and pytest; every honoured spelling is asserted quiet in both modes.

## Dependencies

- **Depends on:** section 02 (`scripts/svg_truth.py`: `svg_texts` entries with `text`, `x`, `y`, `size`; `svg_fills`; `test/cert_svg.do`: `cert_svg_export` -> `r(rc)`/`r(file)`, `cert_svg_texts` -> `r(n)`/`r(list)`, `cert_svg_has_text` -> `r(found)`, `cert_svg_fills` -> `r(colours)`; and `test/test_gaps2_truth.cscript`, the one truth script, registered by S02 as runner block 67).
- **Blocks:** section 15 (batch 3: it appends legend probes to `scripts/extract_text_truth.do` and regenerates the fixture once, rule R5) and section 19.
- **Parallel batch:** 2. **Can run with:** 04, 05, 14, 16, 17. Merge order inside batch 2 is S04, S05, S13, S17, S16, S14: this section merges before S17, S16 and S14 because section 16 calls `_dash_textbox(raw, "ztitle", seen, key)` and must read its `ztitle()` sub-options on this section's canonicalised table (rule R2).
- Why: the truth block and the extract script read twoway's SVG through section 02's helper; nothing else in batch 2 edits `_parse_textbox_opt`, `_dash_textbox`, `_dash_axis_labels` or `_dash_add_secondary_axes`.

## Evidence

Anchors are at `91d97be` (research report A, checked 2026-09-25).

### B3: the table, the split and the names as written

`_TEXTBOX_SUBOPTS` and the regex built from it, `dash_render.py:2438-2445`:

```python
_TEXTBOX_SUBOPTS = (
    "size", "color", "colour", "position", "pos", "span", "box", "nobox",
    "justification", "just", "alignment", "margin", "linegap", "bexpand",
    "bmargin", "fcolor", "lcolor", "lwidth", "lpattern", "orientation",
    "ring", "placement", "width", "height", "tstyle", "style",
)
_TEXTBOX_SUBOPT_RE = re.compile(
    r",\s*(?=(?:" + "|".join(_TEXTBOX_SUBOPTS) + r")\b)", re.I)
```

`_textbox_split_point` (2484-2525) returns the index of the first comma outside every string and every parenthesis, and only when `_TEXTBOX_SUBOPT_RE.match(text, i)` succeeds there. `_parse_textbox_opt` (2614-2682) keeps sub-option names as written:

```python
    scan = tail[:tail.rfind(")") + 1]
    for m2 in re.finditer(r"\b([A-Za-z_]+)\s*\(([^)]*)\)", scan):
        opts[m2.group(1).lower()] = m2.group(2).strip()
    for flag in ("span", "box", "nobox"):
```

Verified by research: `_parse_textbox_opt('"T", c(red)')` returns `('T\n,\nc(red)', {})` and `'"Volume", axis(2)'` returns `('Volume\n,\naxis(2)', {})`. `_textbox_color` (2597-2611) reads `color`/`colour`; `_textbox_size` (2577-2594) reads `size`. `_dash_textbox` (18861-18878) names every tail token whose name is not in `_DASH_TEXTBOX_HONOURED = frozenset({"size", "color", "colour"})` (18858), compared as written. Callers of `_parse_textbox_opt`: 18870, 18916 (`_dash_style_axis_titles`), 21978 (saved figure title), template 26149. Callers of `_dash_textbox`: 16034-16035 (`_dash_axis_labels`), 18889 (`_dash_figure_title`), 18968 (`_dash_text_annotations`); section 16 adds a `ztitle` caller in this batch.

Stata's table (`textbox_options.sthlp:41-77`, `title_options.sthlp:56-66`, `axis_title_options.sthlp:54-63`; report D §4):

| full | minimum | full | minimum |
|---|---|---|---|
| tstyle | tsty | bcolor | bc |
| orientation | orient | fcolor | fc |
| size | si | lstyle | ls |
| color | c | lpattern | lp |
| justification | j | lwidth | lw |
| alignment | al | lcolor | lc |
| margin | m | lalign | la |
| linegap, width, height | full | bmargin | bm |
| box, nobox | full | bexpand | bex |
| placement | place | position | pos |
| ring, span, prefix, suffix | full | axis (axis titles, 1-9) | full |

`colour` and `style` are not in Stata's help: `title("T", colour(red))` is refused by twoway, r(198), as is `style()` (the textbox word is `tstyle`; `style()` belongs to `legend()` and `region()`). twoway splits text from sub-options with `_parse comma` (`_fr_title_parse_and_log.ado`): the first comma outside every string and parenthesis, which the current docstring at 2489-2492 already cites.

`prefix`/`suffix` (`title_options.sthlp:321-347`, `axis_title_options.sthlp:244-264`): `suffix` appends its lines after the earlier text, `prefix` puts them before; on a lone axis title the earlier text is the default title (`xtitle("in days", suffix)` draws "analysis time" / "in days"). dash.ado already merges repeated copies this way: `_dash_rep_merge` (dash_parse.mata 4826-4855) builds `body = strtrim(b1) + " " + strtrim(b2)` for `suffix` and drops the word (`drop = ("suffix", "prefix")`), and `test_twoway_option_parity.cscript` TP-14a row r18 pins `title(A) title(B, suffix)` against twoway's SVG. A lone copy passes through to Python with the word in its tail.

`axis(2)` routing: nothing reads `axis(#)` today (GAPS2 B15). The Mata repeat merge treats every copy of `ytitle` as one option of category "T" (`_dash_rep_cat` 4242-4258): `_dash_rep_reduce` (4874-4950) merges copies within one list, dash.ado 4672 merges a segment's `_sg_ytitle` into `g_ytitle`, and 4695 merges the after-comma copy, all through `_dash_rep_merge`, so `ytitle("a") ytitle("b", axis(2))` reaches the spec as the single `ytitle` `"b", axis(2)`. The two places a raw option list is handed to a parser are `_dash_parse_plot_opts , `macval(opts_raw)'` (dash.ado 3783, inside `_dash_process_segment`) and `_dash_parse_graph_opts , `macval(gopts_raw)'` (4498). Both parsers declare `YTitle(string asis)`, `XTitle(string asis)`, `YTITLE2(string asis)` and `XTITLE2(string asis)` (702, 708, 935, 941); a bare `ytitle(` binds to `YTitle` (comment at 685). Reusable Mata: `_dash_rep_toks(s, commas)` (4069), `_dash_rep_optname` (4115), `_dash_rep_value` (4128), `_dash_rep_split(v, body, sub)` (4727). Python side: `_dash_lone_second_axes(spec)` (1639-1702) runs at 21031 (saved) and 24252 (served) and moves `ytitle2` into `ytitle` when every layer is on axis 2, so a routing rewrite must run before it.

### B6: empty text is "absent"

`_dash_axis_labels` (16003-16038):

```python
    x_text, _ = _dash_textbox(go.get("xtitle", ""), "xtitle", seen, key)
    y_text, _ = _dash_textbox(go.get("ytitle", ""), "ytitle", seen, key)
    x_label = x_text or x_default
    y_label = y_text or y_default
```

`_dash_textbox('""', 'xtitle')` returns `('', {})` because an empty token ends the lines (2572-2573), and the spec carries `"xtitle":"\"\""` (dash.ado 4944-4952, `string asis` keeps the quotes), so the information is there and dropped on the `or`. Callers 21951 (saved) and template 26143-26144 (served); the result goes into `x_axis_label`/`y_axis_label` (21979-21980; 26151-26152). `_dash_lone_second_axes` 1692-1694 moves `ytitle2` only when `second.strip()` is non-empty, which a raw `""` is, so `ytitle2("")` survives the move into `ytitle` and then needs the same rule. `_dash_text_annotations` (18945) already skips an empty text; the figure title at 21978 has no default.

### B7: the second axis's title is raw

`_dash_add_secondary_axes` (16997-17030), the only reader of `{n}title2`:

```python
        n = name[0]
        toks = _dash_by_tokens(str(graph_opts.get(f"{n}scale2", "") or ""))
        is_log = "log" in [_dash_subopt_name(t) for t in toks]
        ax = (LogAxis if is_log else LinearAxis)(
            **{kw: name}, axis_label=graph_opts.get(f"{n}title2", ""))
        fig.add_layout(ax, side)
```

Callers: 22096 (saved, after `_dash_style_axis_titles` at 22041) and template 26207 (served, before it at 26211). `_dash_style_axis_titles` (18905-18929) styles only `_dash_primary_axes(axes, rattr)` (16832-16843). Its signature has no `seen`/`key`. dash.ado declares `YTITLE2(string asis)`/`XTITLE2(string asis)` (708) with aliases `yti2`/`xti2` (744, 747), so the quotes reach the spec; JSE-46 `jg46k` (`test_json_escaping.cscript:1974`) pins that `ytitle2("line 1" "line 2")` is stored as typed and counts one `LinearAxis` drawing `line 1\nline 2` (the first axis of `jg46i`).

### Served-copy mechanics

`ServerAppBuilder` copies constants at 24326-24428 (`_TEXTBOX_SUBOPT_RE` is the tuple's first entry and `_DASH_TEXTBOX_HONOURED` is listed at 24362; `_TEXTBOX_SUBOPTS` is NOT in the tuple at 91d97be, so the served `_textbox_canon` would raise `NameError` unless this section adds it; a compiled regex is written as `re.compile(pattern, flags)` at 24438-24444; every other value as `%r`) and functions at 24466-24687 (`_parse_textbox_opt`, `_textbox_split_point`, `_textbox_lines`, `_textbox_string_end`, `_textbox_size`, `_textbox_color`, `_dash_textbox` (24667), `_dash_style_axis_titles`, `_dash_axis_labels`, `_dash_add_secondary_axes`, `_dash_lone_second_axes` are listed). `test/function_test_map.py` must name a test for every new function.

### Fixtures on disk

`test/fixtures/axis_truth.json` (233 probes) records title probes under `findings.titles_notes_captions` and `title_text_fidelity` but no abbreviation, `axis(2)`, empty-title or `ytitle2` case. No `.svg` is committed. This section adds `test/fixtures/text_truth.json`.

### Existing tests that pin today's behaviour (flip, never delete)

- `test/test_json_escaping.cscript` JSE-46 case `jg46k` (1974-2011): the count `_jg_drawn LinearAxis` with `JG_WANT` = `line 1\nline 2` is asserted `1`; after B7 the right axis of `jg46k` draws it too, so the count becomes `2`. Extend the case (`jg46l`) to compare dash's right axis with twoway's SVG for `ytitle("a" "b", axis(2))`.
- `test/test_dual_axis.py::TestSecondaryAxisOptions::test_ytitle2_on_right_axis` (178): passes on an unquoted value; extend with the quoted, two-line and `size(large)` forms so it fails at `91d97be`.
- `test/test_axis_options.py::TestTitleTextFidelity` (429-521): extend with `c(red)`/`si(large)` and the fixture's texts.
- `test/test_textbox_multiline.py::TestParseTextboxOpt` (97) and `TestTextboxSplitPoint` (431): add abbreviation and foreign-word cases; the 35 `_MEASURED_LINES`, 6 `_MEASURED_EMPTY` and 15 `_MEASURED_SPLITS` cases (282-393) stay as they are and must keep passing.
- `test/test_suboption_warnings.py` `SUBOPTIONS` (43-79) rows "xtitle orientation" and "ytitle size and justification", and `TestTheHonouredOnesStayQuiet` (100-119): add rows for `c()`, `si()`, `orient()`, `bc()`, `prefix`, `axis(1)`.
- `test/test_mode_parity.py` corpus case "yaxis(2) with ytitle2, ylabel2 and yscale2(log)" (1211): a guard, not a flip; it must pass with the second axis styled identically in both modes.
- `test/test_twoway_option_parity.cscript` TP-14a rows r15-r19 (title repeats with `color()` and `suffix`): guards.

## User stories

- **US-13.1** As the Stata user pasting twoway syntax, I want `title("T", c(red))`, `si(large)`, `j(left)` and every other documented abbreviation to be read as the sub-option it is, so that the page never shows my sub-options as title text.
- **US-13.2** As the Stata user, I want `ytitle("Volume", axis(2))` to title the right-hand axis, and `ytitle("Left") ytitle("Right", axis(2))` to title both, so that a twoway command with a second axis pastes unchanged.
- **US-13.3** As the Stata user, I want `xtitle("")` and `ytitle("")` to remove the axis titles, and `ytitle("", axis(2))` the second axis's, so that the standard twoway idiom works.
- **US-13.4** As the Stata user, I want `ytitle2("a" "b", size(large))` to draw two lines at that size without quote marks, so that the second axis's title behaves like the first's.
- **US-13.5** As the Stata user, I want `ytitle("extra", suffix)` to add a line after the default title, as twoway does, so that repeated and suffixed titles paste unchanged.
- **US-13.6** As the dashboard viewer, I want the saved page and the served app to show the same titles at the same sizes and colours.
- **US-13.7** As the maintainer, I want each of B3, B6 and B7 closed by a test that failed at `91d97be`, recorded in BUGS.md and CHANGELOG.

## Business requirements

- **BR-13.1** For `title`, `subtitle`, `note`, `caption`, `xtitle`, `ytitle`, `ytitle2` and `xtitle2`, every spelling of every sub-option in Stata's table, from its minimum abbreviation to its full name, is either applied or named once in the note; none is drawn as text, in either render mode.
- **BR-13.2** `size()` and `color()` under any legal spelling change the drawn size and colour, alone or beside each other's full name; `prefix`, `suffix` and `axis(1)`/`axis(2)` are applied; every other sub-option is named. Applied sub-options print nothing.
- **BR-13.3** A word after the sub-option comma that is not in Stata's table (`colour`, `style`, a misspelling) is named, not drawn.
- **BR-13.4** `ytitle("T", axis(2))` and `xtitle("T", axis(2))` title the second axis, with any other sub-options kept; `axis(1)` titles the first; `axis(3)` and above are named. `ytitle("a") ytitle("b", axis(2))` titles both axes. A title whose quoted text holds `axis(2)`, a `'`, a `$` or a backtick is drawn as typed.
- **BR-13.5** `xtitle("")`, `ytitle("")`, `xtitle("", size(large))` and `ytitle("", axis(2))` draw no title on that axis; an absent option keeps twoway's default (variable label, `Density`, `kdensity <var>`).
- **BR-13.6** `ytitle2()`/`xtitle2()` draw their text without quote marks, one line per string, a compound-quoted string with its inner quotes, with `size()` and `color()` applied and the rest named, identically in both modes.
- **BR-13.7** A lone `ytitle("x", suffix)` draws the default title then `x`; `prefix` the reverse; on `title()`, `subtitle()`, `note()` and `caption()` a lone `prefix`/`suffix` changes nothing and says nothing.
- **BR-13.8** Every drawn text and colour is what twoway's SVG draws for the same command, recorded in `test/fixtures/text_truth.json`.

## Technical requirements

- **TR-13.1** Replace `_TEXTBOX_SUBOPTS` (2438) with a tuple of `(full, minimum)` pairs transcribed from the table above, in that order, and add `_textbox_canon(name)` returning the full name for any spelling with `len(name) >= len(minimum)` and `full.startswith(name)`, else `None`. `colour` and `style` are not in the table.
- **TR-13.2** `_TEXTBOX_SUBOPT_RE` (2444) becomes `re.compile(r",\s*(?=[A-Za-z_])")`: a comma followed by a name start. `_textbox_split_point` (2484) keeps its scan and its parenthesis and string rules; the name check is gone, so the split is twoway's `_parse comma` for any word. A comma followed by a digit, a quote or nothing stays text.
- **TR-13.3** `_parse_textbox_opt` (2614) stores each `name(value)` under `_textbox_canon(name) or name.lower()` and reads the bare words of the tail with `_dash_by_tokens`, storing every flag word (`span`, `box`, `nobox`, `bexpand`/`bex`, `prefix`, `suffix`) under its canonical name; `_textbox_color` (2597) reads `color` only.
- **TR-13.4** `_DASH_TEXTBOX_HONOURED` (18858) becomes `frozenset({"size", "color", "prefix", "suffix", "axis"})`; `_dash_textbox` (18861) compares `_textbox_canon(_dash_subopt_name(tok))` and names the rest as written, `axis(#)` included when `#` is not 1 or 2 or the option is not an axis title.
- **TR-13.5** New `_dash_route_axis_titles(spec)` beside `_dash_lone_second_axes` (1639): for each graph's `graph_options`, for `ytitle`/`xtitle`, when `_parse_textbox_opt(raw)[1].get("axis") == "2"` move the raw value, minus the `axis(2)` token, to `ytitle2`/`xtitle2` (kept as the raw value with its other sub-options), and drop `ytitle`; when `"1"`, keep the value in place minus the token; an explicit `ytitle2` already present wins and the routed copy is dropped with `_dash_warn_once` naming it. Pure function, new dict, wrong-shaped spec returned as it came. Called in both loaders immediately BEFORE `_dash_lone_second_axes` (21031, 24252). Added to the function copy list (24466-24687) immediately after `"_dash_textbox"` (24667), with `_textbox_canon`, and to `test/function_test_map.py`.
- **TR-13.6** New Mata `_dash_route_axis2(opts)` in dash_parse.mata beside `_dash_rep_split`: over `_dash_rep_toks(opts, 0)`, a word whose `_dash_rep_optname` is a prefix of `ytitle` or `xtitle` of length 3 or more (`yti`, `ytit`, ... `ytitle`; never `yti2`) and whose `_dash_rep_split` sub-options hold a word equal, lower-cased and blanks trimmed inside the parentheses, to `axis(2)`, is rewritten as `ytitle2(`body`[, other sub-options])` (`xtitle2` likewise); one holding `axis(1)` loses that word; everything else is returned as typed, a quoted body byte for byte (TBG-06). No regex (memory: `regexm` follows the caller's version); `strlower`, `strtrim`, `strpos` only. Called from dash.ado before `_dash_parse_plot_opts , `macval(opts_raw)'` (3783) as `mata: st_local("opts_raw", _dash_route_axis2(st_local("opts_raw")))` and before `_dash_parse_graph_opts , `macval(gopts_raw)'` (4498) on `gopts_raw`. Entry in `test/program_coverage_map.py` under `dash_parse.mata` naming `test_gaps2_truth.cscript:TBG-03` and `:TBG-02`.
- **TR-13.7** `_dash_axis_labels` (16003): per axis `text, opts = _dash_textbox(raw, ...)` and `given = bool(str(raw or "").strip())`; `label = text if given else default` (B6); with `suffix` in the sub-options `label = default + ("\n" + text if text else "")`, with `prefix` `(text + "\n" if text else "") + default` (B3). B3's task 13-08 adds the `prefix`/`suffix` arms on today's `text or default`; B6's task 13-14 replaces that `or` with the `given` rule. The same rule holds for `ytitle2`/`xtitle2` inside `_dash_add_secondary_axes` (no default there today, so `given` and empty gives `''`, which `_dash_textbox` of a raw `""` already returns once B7's read is in place).
- **TR-13.8** `_dash_add_secondary_axes(fig, plots, graph_opts, frame, seen=None, key="")` (16997): `text, opts = _dash_textbox(graph_opts.get(f"{n}title2", ""), f"{n}title2", seen, key)`; `axis_label=text`; then `px = _textbox_size(opts, None)` and `colour = _textbox_color(opts, None)` set on `ax`, inside the function, the same two axis-label text properties `_dash_style_axis_titles` (18905-18929) sets on the primary axes (the font size as `f"{px:g}px"`, the colour when not `None`). Both call sites pass the renderer's `seen`/`key`: 22096 `_seen, _gkey`; template 26207 `_reported_subopts, gname`.
- **TR-13.9** `scripts/extract_text_truth.do` writes `test/fixtures/text_truth.json` (Stata truth below); `test/test_textbox_grammar.py` pins it; the block `* ==== S13 B3 B6 B7: textbox grammar ====` of `test/test_gaps2_truth.cscript` (D11) compares a live twoway export with dash's page through `cert_svg_*`; JSE-46's extension stays in `test/test_json_escaping.cscript`. No new `.cscript`, no edit to `test/run_all_cscripts.do` or `test/test_cscript_hygiene.py`.
- **TR-13.10** Security (project rule 1): title and axis-title text stays canvas text (never `html.escape`d, as 16013-16015 documents); the Mata rewrite reads the option text by value through `st_local` and returns it to a local read through `macval()`, never expanding it; the Python rewrite touches only the two title keys; no `eval`, no `shell`.
- **TR-13.11** Documents, one closing task per gap: dash.sthlp 519-525 (sub-options under any spelling applied or named; B3), 2396-2399 (`axis(2)` now read; B3), 455-458 (empty text clears the title; B6; the prefix/suffix sentence is B3's), 2403-2417 (`ytitle2(tinfo)`/`xtitle2(tinfo)` with the textbox grammar; B7). CHANGELOG: the markers `<!-- WP-28 B3 -->`, `<!-- WP-28 B6 -->` and `<!-- WP-28 B7 -->` sit in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of the release's `### Results that change` list (S01, D2); each gap's closing task replaces its own marker in place with one line ending `(WP-28, <ID>)` naming the command, the old picture (the recorded failure, Q24) and the new, and adds nothing anywhere else. BUGS.md: three closed entries appended at the end in the D3 form, titles `Textbox sub-option abbreviations are drawn as title text` (B3), `An empty xtitle() or ytitle() does not remove the axis title` (B6), `ytitle2() and xtitle2() draw their quote marks and ignore textbox grammar` (B7); no title holds `"`.
- **TR-13.12** Fixture provenance (D12): the do-file stores `local stata_version = c(stata_version)`, `local born_date = c(born_date)`, `local extracted = c(current_date)`, captures `git rev-parse HEAD` with `shell cd "${ZA_REPO}" && git rev-parse HEAD > "`gitrev'"` into a `tempfile` and reads it into `local dash_commit`; the python block reads the four through `sfi.Macro.getLocal` (never `shell=True`, never a Stata call) and writes them into `_meta` beside `scheme_in_force` and `method`; `TestTheFixtureIsPinned::test_meta_carries_the_stata_build` asserts the four keys exist and compares nothing.

## Boundaries

- Do not touch `_dash_apply_legend`, `_dash_legend_entries`, `_DASH_LEGEND_*` (section 15), `_dash_parse_axis_label_opt`/`_dash_parse_axis_spec` (section 14), `_dash_apply_scale_ranges`/`_dash_finish_secondary_axes` (section 18), `GlyphMapper._apply_colorvar` (section 16), `SchemeParser` (section 6).
- `ylabel(, axis(2))`, `yscale(, axis(2))`, `xline(, axis(2))` stay as they are (GAPS2 B15, not in scope); only the two title options route.
- A second axis's default title (twoway: the label of the variable on that axis) is not added; `ytitle2` absent stays `''`.
- The scheme's axis-title font is not applied to a second axis added after `apply_to_figure` in either mode today; unchanged here.
- `t1title()` .. `r2title()`, `title2()`, `subtitle2()` stay pending (dash.ado 768-797) and named.
- `ytitle("T", axis(2))` on a graph with no layer on axis 2 keeps today's behaviour (the routed `ytitle2` is not drawn, nothing is said); twoway's answer is recorded in the fixture (`t_axis2_no_layer`), not acted on and not pinned.
- No new `.cscript`, no runner or hygiene-pin edit (D11); the legend probes and the fixture's second regeneration are section 15's (batch 3, rule R5).
- PRD §7 exclusions and DISCOVERY Q22 (silent when honoured) hold.

## Stata truth

New `scripts/extract_text_truth.do` → `test/fixtures/text_truth.json`, in `extract_axis_truth.do`'s shape: the `*!` header stating the method, `clear all`, `set graphics off`, `global ZA_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"` and `ZA_OUT`/`ZA_WORK`/`ZA_REC` set by the script itself (so the script is run directly through the wrapper), a `zp` program registering six arguments `id group dataset command option control` (the sixth is the id of the companion probe whose texts are subtracted; empty for a control itself), the export loop of `extract_axis_truth.do:392-428` (SVG only, no `.gph`), `capture noisily` per probe with `rc` recorded, the `_meta` locals and the `git rev-parse HEAD` capture of TR-13.12, and ONE trailing `python:` block that reads the record file, imports `svg_truth` from `${ZA_REPO}/scripts` via `sys.path.insert`, and writes the JSON. The block never calls Stata; a backtick is spelled `\x60`; spaces written as U+00A0 by `nbsp(on)` are normalised to a space before comparing.

Per probe the fixture records `{"group", "command", "rc", "control", "texts" (every `<text>` string in document order), "fills" (`sorted(svg_fills(svg))` -- the dict's keys, lower-cased), "added_texts" (multiset difference probe minus control, probe order), "removed_texts" (control minus probe), "added_fills" (a set difference; the fills list carries no counts), "text_sizes" ({text: px} from each `svg_texts` entry's `size` key, S02 TR-02.1)}`. The python block keeps the per-entry `svg_texts` dicts (`text`, `x`, `y`, `size`, ...) until each record's lists are built and only then projects to `text`, because section 15's `legend` group sorts entries by `y` then `x` (consistency #34). Group `title` probes (section 15 adds group `legend` in the marked region after these, before the export loop):

```
zp "t_default"          "title" "auto" "twoway scatter mpg weight" "" ""
zp "t_y2_default"       "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" "" ""
zp "t_hist_default"     "title" "auto" "twoway histogram mpg" "" ""
zp "t_kdens_default"    "title" "auto" "twoway kdensity mpg" "" ""
zp "t_c_red"            "title" "auto" "twoway scatter mpg weight" `"title("T", c(red))"' "t_default"
zp "t_color_red"        "title" "auto" "twoway scatter mpg weight" `"title("T", color(red))"' "t_default"
zp "t_si_large"         "title" "auto" "twoway scatter mpg weight" `"title("T", si(large))"' "t_default"
zp "t_size_large"       "title" "auto" "twoway scatter mpg weight" `"title("T", size(large))"' "t_default"
zp "t_size_color_abbr"  "title" "auto" "twoway scatter mpg weight" `"title("T", si(large) c(red))"' "t_default"
zp "t_size_c"           "title" "auto" "twoway scatter mpg weight" `"title("T", size(large) c(red))"' "t_default"
zp "t_color_si"         "title" "auto" "twoway scatter mpg weight" `"title("T", color(red) si(large))"' "t_default"
zp "t_j_left"           "title" "auto" "twoway scatter mpg weight" `"title("A" "Bee", j(left))"' "t_default"
zp "t_bc_nobox"         "title" "auto" "twoway scatter mpg weight" `"title("T", bc(red))"' "t_default"
zp "t_box_bc"           "title" "auto" "twoway scatter mpg weight" `"title("T", box bc(red))"' "t_default"
zp "t_subtitle_c"       "title" "auto" "twoway scatter mpg weight" `"subtitle("S", c(red))"' "t_default"
zp "t_note_si"          "title" "auto" "twoway scatter mpg weight" `"note("N", si(large))"' "t_default"
zp "t_caption_c"        "title" "auto" "twoway scatter mpg weight" `"caption("C", c(red))"' "t_default"
zp "t_xtitle_c"         "title" "auto" "twoway scatter mpg weight" `"xtitle("W", c(red))"' "t_default"
zp "t_ytitle_si"        "title" "auto" "twoway scatter mpg weight" `"ytitle("M", si(large))"' "t_default"
zp "t_xtitle_orient"    "title" "auto" "twoway scatter mpg weight" `"xtitle("Weight", orient(vertical))"' "t_default"
zp "t_ytitle_axis2"     "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("Volume", axis(2))"' "t_y2_default"
zp "t_ytitle_axis2_two" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("a" "b", axis(2))"' "t_y2_default"
zp "t_ytitle_axis2_compound" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle(`"c "q" d"', axis(2))"' "t_y2_default"
zp "t_ytitle_both"      "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("Left") ytitle("Right", axis(2))"' "t_y2_default"
zp "t_ytitle_axis2_size" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("P2", size(large) axis(2))"' "t_y2_default"
zp "t_ytitle_axis2_empty" "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("", axis(2))"' "t_y2_default"
zp "t_ytitle_axis1"     "title" "auto" "twoway scatter mpg weight" `"ytitle("One", axis(1))"' "t_default"
zp "t_ytitle_axis2_lone" "title" "auto" "twoway scatter mpg weight, yaxis(2)" `"ytitle("Lone", axis(2))"' ""
zp "t_axis3"            "title" "auto" "twoway (scatter mpg weight) (line price weight, yaxis(2))" `"ytitle("T", axis(3))"' "t_y2_default"
zp "t_axis2_no_layer"   "title" "auto" "twoway scatter mpg weight" `"ytitle("T", axis(2))"' "t_default"
zp "t_xtitle_empty"     "title" "auto" "twoway scatter mpg weight" `"xtitle("")"' "t_default"
zp "t_ytitle_empty"     "title" "auto" "twoway scatter mpg weight" `"ytitle("")"' "t_default"
zp "t_both_empty"       "title" "auto" "twoway scatter mpg weight" `"xtitle("") ytitle("")"' "t_default"
zp "t_xtitle_empty_size" "title" "auto" "twoway scatter mpg weight" `"xtitle("", size(large))"' "t_default"
zp "t_hist_ytitle_empty" "title" "auto" "twoway histogram mpg" `"ytitle("")"' "t_hist_default"
zp "t_ytitle_suffix"    "title" "auto" "twoway scatter mpg weight" `"ytitle("extra", suffix)"' "t_default"
zp "t_ytitle_prefix"    "title" "auto" "twoway scatter mpg weight" `"ytitle("pre", prefix)"' "t_default"
zp "t_title_suffix"     "title" "auto" "twoway scatter mpg weight" `"title("T", suffix)"' "t_default"
zp "t_title_two_suffix" "title" "auto" "twoway scatter mpg weight" `"title("A") title("B", suffix)"' "t_default"
zp "t_xtitle_two_suffix" "title" "auto" "twoway scatter mpg weight" `"xtitle("A") xtitle("B", suffix)"' "t_default"
zp "t_colour_refused"   "title" "auto" "twoway scatter mpg weight" `"title("T", colour(red))"' "t_default"
zp "t_style_refused"    "title" "auto" "twoway scatter mpg weight" `"title("T", style(x))"' "t_default"
* ---- section 15: legend probes ----
```

43 probes. The six empty-title ids (`t_ytitle_axis2_empty`, `t_xtitle_empty`, `t_ytitle_empty`, `t_both_empty`, `t_xtitle_empty_size`, `t_hist_ytitle_empty`) are B6's; `t_ytitle_axis2_two`, `t_ytitle_axis2_compound` and `t_ytitle_axis2_size` need B7's read and B3's route; `t_axis3` and `t_axis2_no_layer` are recorded, not pinned (Boundaries).

The script sets its own directories, so it is run directly through the slot wrapper (D6, index.md step 0; it implements CLAUDE.md rule 10's console invocation under one of three slots and sets `STATATMP=/tmp/dash-s13/tmp/` with the trailing slash), never the GUI:

```
scripts/stata_slot.sh /tmp/dash-s13 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_text_truth.do
```

Read `/tmp/dash-s13/extract_text_truth.log`. Then `git add -f test/fixtures/text_truth.json` (`.git/info/exclude` drops `*.json` otherwise) and confirm `test/test_fixtures_are_committed.py` passes: the fixture is named by `test_textbox_grammar.py`. The fixture's `_meta` records `stata_version`, `born_date`, `dash_commit`, `extracted` (D12, TR-13.12), the scheme in force, and the method sentence. Section 15 regenerates the fixture once more in batch 3 (rule R5); this section regenerates it once and never patches it by hand.

A cscript (`test_gaps2_truth.cscript`, `test_json_escaping.cscript`, `test_twoway_option_parity.cscript`) resolves `cert_helpers.do`, `cert_svg.do` and `adodir ".."` from `test/`, as `test/run_all_cscripts.do` does with its `cd`, so it is run through a two-line driver written into the scratch directory:

```
mkdir -p /tmp/dash-s13
printf 'cd "%s/test"\ndo "%s/test/%s"\n' /Users/billy/Desktop/Programs/StataPrograms/d/dash /Users/billy/Desktop/Programs/StataPrograms/d/dash test_gaps2_truth.cscript > /tmp/dash-s13/run_test_gaps2_truth.do
GAPS2_ONLY=S13 scripts/stata_slot.sh /tmp/dash-s13 /tmp/dash-s13/run_test_gaps2_truth.do
```

(the same two lines with `test_json_escaping.cscript` or `test_twoway_option_parity.cscript` and no `GAPS2_ONLY` for the other two). The logs are `/tmp/dash-s13/run_<script>.log`; `GAPS2_ONLY=S13` makes the truth script run only this section's block. Every script exits 222 itself when `c(python_exec)` is empty; a SKIP is not a pass.

## TDD test stubs

New file `test/test_textbox_grammar.py`, created by 13-01 with the B7 class and extended by 13-04 (B3) and 13-13 (B6); both-mode helpers imported from `test_textbox_multiline._both_modes`/`_drawn` (520-552, 502-517) and `test_dual_axis._lone_figure` (311-335); a `_second_axis(fig, side)` helper returning the `ContinuousAxis` in `fig.right`/`fig.above` whose `y_range_name`/`x_range_name` is `y2`/`x2`; a `truth()` module fixture like `test_axis_options.py:40-47` that fails, never skips, when the fixture is missing. Each gap's regression stubs fail on the tree before that gap's fix and their failure text is saved by the gap's first task (Q24).

B7 (13-01):

- Test: `ytitle2("P2")` draws `P2` (no quotes), `"a" "b"` two lines, `` `"c "q" d"' `` draws `c "q" d` (F-18), `"P2", size(large)` sized, `"P2", color(red)` red, `"P2", bogus(1)` named once; saved and served font sizes equal — `test_textbox_grammar.py::TestSecondAxisTitleIsATextbox::test_text_lines_size_colour` (fails: `"P2"` with its quote marks).
- Test: `xtitle2()` is read the same way on the top axis — `::TestSecondAxisTitleIsATextbox::test_xtitle2_is_read_the_same_way`.
- Test: `ytitle2("P2", size(large))` gives the same axis-label font size (the property `_dash_style_axis_titles` sets) in the saved figure (axis added after `_dash_style_axis_titles`) and the served one (added before) — `::TestSecondAxisTitleIsATextbox::test_styling_holds_in_either_renderer_order`.
- Extended: `test_dual_axis.py::TestSecondaryAxisOptions::test_ytitle2_on_right_axis` asserts the label is exactly `Secondary Y`; new `test_ytitle2_lines_size_and_colour` (`'"a" "b", size(large) color(red)'`).
- JSE-46 `jg46k` extended: the `LinearAxis` count for `line 1\nline 2` is `2`; new `jg46l`: `dash (scatter mpg weight) (line price weight, yaxis(2)), ytitle2("a" "b") name(jg46l)` draws `a\nb` on dash's right axis, and twoway's SVG for `twoway (scatter mpg weight) (line price weight, yaxis(2)), ytitle("a" "b", axis(2))`, exported through `cert_svg_export`, holds `a` and `b` (`cert_svg_has_text, file() text("a")` and `text("b")`, `r(found)`).

B3 (13-04, truth block 13-05):

- Test: `title("T", c(red))` draws the text `T` in `#ff0000` in both modes — `::TestAbbreviationsAreSubOptions::test_c_red_is_a_red_title` (fails: text `T\n,\nc(red)`).
- Test: every spelling of `size` (`si` .. `size`) changes the title's font size and leaves the text bare, both modes — `::TestAbbreviationsAreSubOptions::test_every_size_spelling`.
- Test: `title("T", size(large) c(red))` and `title("T", color(red) si(large))` are red and large in both modes, nothing named (F-16) — `::TestAbbreviationsAreSubOptions::test_a_full_name_and_an_abbreviation_together`.
- Test: table over the six text options × every name × its minimum, an intermediate and its full spelling: `size`/`color` applied, the rest named exactly once in both modes, the text bare — `::TestEverySpellingOnEveryOption::test_spelling` (parametrised; fails today for every abbreviation).
- Test: `ytitle2`/`xtitle2` × `size`/`si`/`color`/`c` style the second axis, both modes (B7's read is on the tree) — `::TestEverySpellingOnEveryOption::test_second_axis_spelling`.
- Test: `colour(red)` and `style(x)` are named, not drawn, and `_textbox_canon("colour") is None` — `::TestForeignWordsAreNamed::test_colour_and_style`.
- Test: `ytitle("Volume", axis(2))` titles the right axis `Volume` and leaves the left axis's default, both modes — `::TestAxisTwoRouting::test_axis_2_titles_the_right_axis` (fails: left axis `Volume\n,\naxis(2)`).
- Test: `ytitle("a" "b", axis(2))` draws two lines on the right axis; `"P2", size(large) axis(2)` sized — `::TestAxisTwoRouting::test_lines_and_size_survive_the_route`.
- Test: `ytitle("Lone", axis(2))` on a lone-axis(2) graph titles the one left axis, both modes (the route runs before the lone rewrite) — `::TestAxisTwoRouting::test_the_route_runs_before_the_lone_rewrite`.
- Test: `_dash_route_axis_titles` unit cases: `axis(1)` stays, `axis(3)` untouched and later named, explicit `ytitle2` kept with one warning, malformed spec passthrough, caller's dict unmodified — `::TestAxisTwoRouting::test_route_axis_titles_unit`.
- Test: `ytitle("extra", suffix)` draws the fixture's `t_ytitle_suffix` lines (default then `extra`); `prefix` the reverse; a lone `title("T", suffix)` draws `T` and warns nothing — `::TestPrefixSuffix::test_lone_suffix_and_prefix`.
- Test: dash's drawn title text and colour equal the fixture's `added_texts`/`added_fills` for every `title` probe with `rc` 0 except the six empty-title ids (B6's) and `t_axis3`/`t_axis2_no_layer` (recorded, not pinned) — `::TestTheFixtureIsPinned::test_dash_draws_what_twoway_draws` (parametrised).
- Test: `truth()['_meta']` holds `stata_version`, `born_date`, `dash_commit` and `extracted` (nothing compared, D12) — `::TestTheFixtureIsPinned::test_meta_carries_the_stata_build`.
- Test: the served app source defines `_TEXTBOX_SUBOPTS`, `_textbox_canon`, `_dash_route_axis_titles`, `_DASH_TEXTBOX_HONOURED` — `::TestTheServedCopy::test_the_names_are_copied`.
- Test: `_textbox_canon` maps every prefix of every name from its minimum to its full name, shorter prefixes to `None`, and the table equals Stata's (hard-coded) — `::TestTheTable::test_every_prefix` (fails: `AttributeError`).
- Test: `_parse_textbox_opt('"a", c(red) si(large) bex')` → `{"color": "red", "size": "large", "bexpand": "bexpand"}` — `::TestTheTable::test_parse_canonicalises`.
- Test: the 56 measured line/empty/split cases of `test_textbox_multiline.py` still pass (`python3 -m pytest test/test_textbox_multiline.py`) — a guard, not a stub.
- Extended: `test_axis_options.py::TestTitleTextFidelity::test_abbreviated_size_and_colour_are_applied` (`'T, si(large) c(red)'` against `truth()['probes']['t_size_color_abbr']`).
- Flipped rows in `test_suboption_warnings.py`: `SUBOPTIONS` gains `("title c and bc", {"title": 'T, c(red) bc(red)'}, None, "title", ["bc(red)"], ["c"])`, `("xtitle orient", {"xtitle": "Weight, orient(vertical)"}, None, "xtitle", ["orient(vertical)"], [])`, `("ytitle axis 3", {"ytitle": "M, axis(3)"}, None, "ytitle", ["axis(3)"], [])`; `TestTheHonouredOnesStayQuiet` gains `{"ytitle": 'M, si(large) c(red) prefix'}`, `{"xtitle": 'W, axis(1)'}`.
- Truth block `* ==== S13 B3 B6 B7: textbox grammar ====` of `test/test_gaps2_truth.cscript`: TBG-01 `title("T", c(red))`: `cert_svg_has_text, file() text("T")` returns `r(found)` 1 and `text("c(red)")` 0, and `cert_svg_fills`'s `r(colours)` holds `#ff0000`; dash's page has `"text":"T"` and `"text_color":"#ff0000"`; TBG-02 `ytitle("Volume", axis(2))`: twoway's SVG has `Volume`; dash's page has a `LinearAxis` with `y_range_name` `y2` and `axis_label` `Volume`, the left axis `Mileage (mpg)`; the stored spec carries `ytitle2` and no `ytitle`; TBG-03 `ytitle("Left") ytitle("Right", axis(2))`: the stored spec carries `ytitle` `"Left"` and `ytitle2` `"Right"` (Mata-only proof); TBG-05 `ytitle("extra", suffix)`: twoway's texts hold `Mileage (mpg)` and `extra`; dash's left axis label is `Mileage (mpg)\nextra`; TBG-06 hostile titles (JSE-42..49's forms: `` title(`"'90s"') ``, a `$`, a backtick, and `title("say axis(2) here")`) pass through `_dash_route_axis2` unchanged: the stored spec's `title` values equal the typed text, `rc` is 0, and no `ytitle2` appears. TBG-04 is B6's (below).

B6 (13-13):

- Test: `xtitle("")` and `ytitle("")` give `''` labels in both modes; the fixture's `removed_texts` for `t_both_empty` holds both default titles — `::TestEmptyTitles::test_empty_text_removes_the_title` (fails: `weight`/`mpg`).
- Test: `xtitle("", size(large))` gives `''` — `::TestEmptyTitles::test_empty_text_with_a_sub_option`.
- Test: absent options keep `Density` on a histogram and `kdensity x` on a kdensity; `ytitle("")` on a histogram removes `Density` — `::TestEmptyTitles::test_defaults_stay_when_absent`.
- Test: `ytitle2("")` gives `''` on the right axis; `ytitle2("")` on a lone-axis(2) graph gives `''` on the left — `::TestEmptyTitles::test_second_axis_empty` (fails on the lone case: `mpg`).
- Test: for the six empty-title probes, dash's axis labels are `''` and the probe's `removed_texts` hold the default title — `::TestEmptyTitles::test_the_fixture_probes_show_no_title` (parametrised).
- Extended: `test_dual_axis.py::TestTheLoneAxisRewrite::test_an_empty_second_title_is_moved_and_removes_the_title` (both modes through `_lone_figure`: `{"ytitle2": '""'}` gives `''` on the left axis).
- Truth block case TBG-04 `xtitle("") ytitle("")`: twoway's SVG lacks `Weight (lbs.)` and `Mileage (mpg)`; dash's axis labels are empty.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| Abbreviation table and canonicalisation | pytest `TestTheTable` | none | n/a |
| Every spelling on every option, honoured or named | pytest `TestEverySpellingOnEveryOption` | none | yes |
| Foreign words named | pytest `TestForeignWordsAreNamed` | `text_truth.json` (`rc` of `t_colour_refused`) | yes |
| `axis(2)` routing, Python | pytest `TestAxisTwoRouting` | `text_truth.json` | yes |
| `axis(2)` routing, Mata (two copies); hostile titles unchanged | truth block TBG-02, TBG-03, TBG-06 | live twoway export | saved page |
| Empty titles | pytest `TestEmptyTitles`; truth block TBG-04 | `text_truth.json` | yes |
| Second-axis textbox | pytest `TestSecondAxisTitleIsATextbox`; JSE-46 | none; live export | yes |
| prefix/suffix | pytest `TestPrefixSuffix`; truth block TBG-05; TP-14a guard | `text_truth.json` | yes |
| twoway's text and colour | pytest `TestTheFixtureIsPinned`; truth block TBG-01 | `text_truth.json`; live export | yes |
| Fixture `_meta` stamp | pytest `TestTheFixtureIsPinned::test_meta_carries_the_stata_build` | `text_truth.json` | n/a |
| Served copy carries the names | pytest `TestTheServedCopy` | none | served |
| Measured line/split cases unchanged | pytest `test_textbox_multiline.py` | none | yes |
| Fixture committed and named | `test_fixtures_are_committed.py` | `text_truth.json` | n/a |

Acceptance criteria:
- **AC-13.1** Every test stub above passes; each regression stub failed on the tree before its gap's fix with the failure recorded in that gap's commit body (`<scratch>/13-01-failure.txt`, `13-04-failure.txt`, `13-13-failure.txt`).
- **AC-13.2** `python3 -m pytest test/ -q` is green under both interpreters with no skip added before each of the three commits; the `S13` block of `test_gaps2_truth.cscript`, JSE-46 and TP-14a pass under Stata's Python.
- **AC-13.3** BUGS.md holds three closed entries in the D3 form naming their tests; dash.sthlp 455-458, 519-525, 2396-2417 updated; the three markers `<!-- WP-28 B3 -->`, `<!-- WP-28 B6 -->`, `<!-- WP-28 B7 -->` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group of `### Results that change` are replaced by lines ending `(WP-28, B3)`, `(WP-28, B6)`, `(WP-28, B7)`.
- **AC-13.4** No `dash:` warning is printed for any honoured spelling in either mode (Q22).
- **AC-13.5** Three commits on `wp28-s13` with subjects ending `(GAPS2 B7)`, `(GAPS2 B3)`, `(GAPS2 B6)`, in that order, each with a green full suite; no test-only commit.

## Tasks

Commit boundary: **three commits, in this order** -- **B7** = 13-01..13-03 (subject ending `(GAPS2 B7)`), **B3** = 13-04..13-12 (`(GAPS2 B3)`; the fixture of 13-06 lands here with a `Fixture:` line), **B6** = 13-13..13-15 (`(GAPS2 B6)`). B7 goes first because B3's `axis(2)` route hands the second axis a raw textbox and B6's `ytitle2("")` needs the same reader. Each closing task runs the full pytest suite once in the worktree before its commit (CLAUDE.md rules 4 and 11; the third launch in one session is written `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q`, which `.claude/hooks/guard-full-suite.sh` allows), commits on the worktree branch `wp28-s13`, and the merger lands the three commits on `s3-bugs` in order with the same messages (index.md step 1). Each body opens with its gap's saved failure text (Q24) and carries S01 TR-01.9's `Regression:` / `Flipped:` / `Fixture:` / `BUGS.md:` lines. Every Stata run goes through `scripts/stata_slot.sh` (D6): the extract script directly, a cscript through the driver of "Stata truth". No AI references anywhere.

<task type="auto" id="13-01">
  <name>Write the failing B7 tests</name>
  <files>test/test_textbox_grammar.py, test/test_dual_axis.py, test/test_json_escaping.cscript</files>
  <action><![CDATA[
    Create `test/test_textbox_grammar.py` with a module docstring stating the three measured symptoms of GAPS2 B3, B6 and B7, the shared helpers ("TDD test stubs": `_both_modes`/`_drawn` from `test_textbox_multiline`, `_lone_figure` from `test_dual_axis`, `_second_axis`, and the `truth()` fixture that calls `pytest.fail("section 13 task 13-06 must land first: test/fixtures/text_truth.json is missing")`, never skips), and the class `TestSecondAxisTitleIsATextbox` with exactly the three stub names (later tasks append the B3 and B6 classes to this file). Extend `test/test_dual_axis.py::TestSecondaryAxisOptions::test_ytitle2_on_right_axis` to assert the label is exactly `Secondary Y` and add `test_ytitle2_lines_size_and_colour` (`'"a" "b", size(large) color(red)'`). In `test/test_json_escaping.cscript` JSE-46 (1974-2011) change the expected `LinearAxis` count for `line 1\nline 2` from `1` to `2` and add `jg46l` as the stub describes (dash side `ytitle2("a" "b")`, twoway side `ytitle("a" "b", axis(2))` exported through `cert_svg_export` and read with `cert_svg_has_text`; load `cert_svg.do` after the `cscript` line and before any `cd` if the script does not load it yet). Run `python3 -m pytest test/test_textbox_grammar.py test/test_dual_axis.py -q` and JSE-46 through the driver (`run_test_json_escaping.do`) against the unmodified tree. Do not commit: save the failure output (`"P2"` with its quote marks, `"a" "b"` on one line, `size(large)` drawn as text, the count `1`) to `<scratch>/13-01-failure.txt`; it opens the B7 commit's body and its values are the CHANGELOG's old picture (Q24, S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q 2>&1 | tail -5` reports 0 passed, no collection error, and the headline failure shows `"P2"` with its quote marks; `grep -c 'JSE-46' /tmp/dash-s13/run_test_json_escaping.log` is non-zero and the case fails on the count `1`; `<scratch>/13-01-failure.txt` exists.]]></verify>
  <done>The B7 regression tests existed, collected, and failed against the unmodified tree for the reason the gap describes, with no product file changed and nothing committed.</done>
</task>

<task type="auto" id="13-02">
  <name>Read the second axis's title as a textbox</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Change `_dash_add_secondary_axes` (16997-17030) to the signature and body of TR-13.8: `seen=None, key=""` parameters; `text, opts = _dash_textbox(graph_opts.get(f"{n}title2", ""), f"{n}title2", seen, key)`; `axis_label=text`; after `fig.add_layout(ax, side)` apply `_textbox_size`/`_textbox_color` to the two axis-label text properties `_dash_style_axis_titles` (18905-18929) sets on the primary axes (the font size as `f"{px:g}px"`, the colour when not `None`), with a comment that the saved renderer adds this axis after `_dash_style_axis_titles` and the template before it, which is why the styling lives here. Update the two call sites: 22096 `_dash_add_secondary_axes(fig, plots, graph_opts, _source_frame(source, self.df), _seen, _gkey)`; template 26207 `_dash_add_secondary_axes(fig, plots, go, g_df, _reported_subopts, gname)`. Run `test/test_textbox_grammar.py`, `test/test_dual_axis.py`, `test/test_mode_parity.py -k yaxis`, then JSE-46 through the driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py test/test_dual_axis.py -q 2>&1 | tail -3` is green including `TestSecondAxisTitleIsATextbox`; `/tmp/dash-s13/run_test_json_escaping.log` shows the `LinearAxis` count `2` and `jg46l` equal to twoway's texts, with `grep -c '^r([0-9]*);' /tmp/dash-s13/run_test_json_escaping.log` printing 0; the served and saved y2 axes carry the same label font size in `test_mode_parity`'s y2 case.]]></verify>
  <done>`ytitle2()`/`xtitle2()` drew their lines without quote marks, sized and coloured by their sub-options and naming the rest, the same in both renderers whatever the order the axis was added.</done>
</task>

<task type="auto" id="13-03">
  <name>Close B7 in the tracking documents</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append at the end of BUGS.md (S01 TR-01.8; never mid-file) the closed entry `- [x] Title: ytitle2() and xtitle2() draw their quote marks and ignore textbox grammar` with File Names and Line Numbers (`dash_render.py` `_dash_add_secondary_axes`), Description (GAPS2 B7's measured symptoms), Suggested fix, and `- Resolution: Fixed <ddmonyyyy> (WP-28, B7). _dash_add_secondary_axes reads {n}title2 through _dash_textbox (lines joined, compound quotes kept, size() and color() applied, the rest named) and styles the axis inside the function, so both renderers agree whichever adds the axis first. Pinned by test/test_textbox_grammar.py::TestSecondAxisTitleIsATextbox::test_text_lines_size_colour, test/test_dual_axis.py::TestSecondaryAxisOptions::test_ytitle2_lines_size_and_colour, test/test_json_escaping.cscript JSE-46.` -- the title holds no `"`. Update dash.sthlp 2411 and 2417 so `ytitle2(tinfo)`/`xtitle2(tinfo)` carry the textbox grammar (strings as lines, `size()`, `color()`); grep `test/test_help_claims_*.cscript` and `test/test_help_examples.py` for the changed sentences and update any pin. In `CHANGELOG.md` replace the marker `<!-- WP-28 B7 -->` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of the release's `### Results that change` list (S01 placed it there, D2) with ONE line ending `(WP-28, B7)`: `ytitle2("P2")` drew `"P2"` with its quote marks, `ytitle2("a" "b")` one quoted line and `ytitle2("P2", size(large))` the sub-option as text (the pictures `<scratch>/13-01-failure.txt` recorded, Q24), now `P2`, two lines, and a sized title. Write nothing under any other heading. Run the full pytest suite once in the worktree (`python3 -m pytest test/ -q`, the first of this section's three launches), then JSE-46 through the driver; grep the three files and the message for `claude|anthropic`; commit 13-01..13-03 on the worktree branch `wp28-s13` as ONE commit, subject ending `(GAPS2 B7)`, body opening with `<scratch>/13-01-failure.txt` and carrying the `Regression:` / `Flipped:` (JSE-46's count, `test_ytitle2_on_right_axis`) / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` with this message (index.md step 1).
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py test/test_help_examples.py -q` passes; `grep -c '<!-- WP-28 B7 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, B7)' CHANGELOG.md BUGS.md` prints 2; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0 and `git log -1 --format=%s | grep -c '(GAPS2 B7)'` prints 1.]]></verify>
  <done>B7 was closed in BUGS.md naming its tests, the help gave the second axis's title the textbox grammar, the B7 marker was replaced by the line with the recorded old picture, and one green commit on `wp28-s13` carried it.</done>
</task>

<task type="auto" id="13-04">
  <name>Write the failing B3 tests</name>
  <files>test/test_textbox_grammar.py, test/test_axis_options.py, test/test_suboption_warnings.py</files>
  <action><![CDATA[
    Append to `test/test_textbox_grammar.py` the B3 classes with exactly the stub names: `TestTheTable`, `TestAbbreviationsAreSubOptions` (including `test_a_full_name_and_an_abbreviation_together`), `TestEverySpellingOnEveryOption` (including `test_second_axis_spelling`), `TestForeignWordsAreNamed`, `TestAxisTwoRouting`, `TestPrefixSuffix`, `TestTheFixtureIsPinned` (parametrised over the fixture's `title` probes with `rc` 0 minus the six empty-title ids and `t_axis3`/`t_axis2_no_layer`, plus `test_meta_carries_the_stata_build`) and `TestTheServedCopy`. Extend `test/test_axis_options.py::TestTitleTextFidelity` with `test_abbreviated_size_and_colour_are_applied` (`'T, si(large) c(red)'` against `truth()['probes']['t_size_color_abbr']`). Extend `test/test_suboption_warnings.py` `SUBOPTIONS` and `TestTheHonouredOnesStayQuiet` with the rows listed under "TDD test stubs". Do not touch dash_render.py. Run `python3 -m pytest test/test_textbox_grammar.py test/test_axis_options.py test/test_suboption_warnings.py -q` against the tree as the B7 commit left it. Do not commit: save the failure output (`T\n,\nc(red)`, the left axis `Volume\n,\naxis(2)`, `AttributeError` for `_textbox_canon`; the fixture-pinned cases fail on the missing fixture until 13-06 and are re-run there) to `<scratch>/13-04-failure.txt`; it opens the B3 commit's body (Q24, S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q -k "not SecondAxisTitle" 2>&1 | tail -5` reports 0 passed and no collection error; `python3 -m pytest test/test_textbox_grammar.py -q -k c_red 2>&1 | grep -c "c(red)"` is non-zero (the headline fails with the sub-option drawn as text, not with an exception); `<scratch>/13-04-failure.txt` exists.]]></verify>
  <done>The B3 regression tests existed, collected, and failed for the reason the gap describes, with no product file changed and nothing committed.</done>
</task>

<task type="auto" id="13-05">
  <name>Append the B3 cases to the truth script</name>
  <files>test/test_gaps2_truth.cscript</files>
  <action><![CDATA[
    Append to `test/test_gaps2_truth.cscript` (S02 created it in batch 1 and registered it as runner block 67; it opens with the Python gate that exits 222, loads `cert_helpers.do` and `cert_svg.do`, sets `global dash_nobrowser 1`, and ends with the line `* ==== append new blocks above this line ====`), above that last line and after every earlier section's block (rule R1: blocks in section order), the block
```
* ==== S13 B3 B6 B7: textbox grammar ====
local only : env GAPS2_ONLY
if inlist("`only'", "", "S13") {
    display as text "S13 start `c(current_time)'"
    ... TBG-01, TBG-02, TBG-03, TBG-05, TBG-06 (TBG-04 is added by 13-13) ...
    display as text "S13 end `c(current_time)'"
}
* ==== end S13 ====
```
    with the cases as "TDD test stubs" describe: `sysuse auto, clear` inside the `if`; each case exports twoway's graph through `cert_svg_export`, reads it with `cert_svg_has_text`/`cert_svg_fills`, builds dash's page with `dash ... name(tbgN)` and `dash build, saving()`, reads the page with a `python:` block modelled on `test_json_escaping.cscript`'s `_jg_drawn` (1492) that lists `LinearAxis` models with their `y_range_name` and `axis_label`, and reads the stored spec with `_dash_json_get_str` as `test_textbox_multiline.cscript:56-64` does; each case displays `TBG-0n PASS` or `TBG-0n FAIL: <why>` through the script's PASS/FAIL helper and never `exit`s on a failure, so later blocks still run. Edit neither `test/run_all_cscripts.do` nor `test/test_cscript_hygiene.py` (D11: S02 alone set the pins). Run the block with the driver of "Stata truth" under `GAPS2_ONLY=S13` against the tree as the B7 commit left it and append the TBG lines of `/tmp/dash-s13/run_test_gaps2_truth.log` to `<scratch>/13-04-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "TBG-0[12356]" /tmp/dash-s13/run_test_gaps2_truth.log` is at least 5, TBG-01 fails on a page holding `c(red)` and TBG-02 on the left axis titled `Volume`, and `grep -c '^r([0-9]*);' /tmp/dash-s13/run_test_gaps2_truth.log` prints 0 (the block reports, it does not abort).]]></verify>
  <done>The B3 certification cases existed in the one truth script's S13 block and failed against the pre-fix tree for the reasons the gap describes, with nothing committed.</done>
</task>

<task type="auto" id="13-06">
  <name>Record twoway's title truth into text_truth.json</name>
  <files>scripts/extract_text_truth.do, test/fixtures/text_truth.json</files>
  <action><![CDATA[
    Create `scripts/extract_text_truth.do` as "Stata truth" specifies: the `*!` header (method, invocation, the backtick trap), the absolute `global ZA_REPO` and the derived `ZA_OUT`/`ZA_WORK`/`ZA_REC`, `zp` with the sixth `control` argument stored in `ZA_CTL_<n>`, the 43 `title` probes in the order listed, the marked empty region `* ---- section 15: legend probes ----` after them, the export loop copied from `extract_axis_truth.do:392-428` without the `.gph` save (record `PROBE|id|grp|ds|rc|rcx|svg|ctl|shown`), the `_meta` locals and the `tempfile`/`shell cd "${ZA_REPO}" && git rev-parse HEAD` capture of TR-13.12, and one trailing `python:` block that inserts `${ZA_REPO}/scripts` on `sys.path`, imports `svg_truth`, calls `svg_texts` and `svg_fills` per measured probe, keeps the per-entry `svg_texts` dicts until each record's lists are built, normalises U+00A0 to a space, computes `added_texts`/`removed_texts` by `collections.Counter` difference keeping the probe's order and `added_fills` as a set difference, records `text_sizes` from the entries' `size` key, reads the four `_meta` values through `sfi.Macro.getLocal`, and dumps `{"_meta": {...}, "probes": {...}}` with `sort_keys=True`. Spell any backtick in the block as `\x60`; never call Stata from it. Run `scripts/stata_slot.sh /tmp/dash-s13 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_text_truth.do`, check `/tmp/dash-s13/extract_text_truth.log` ends `WROTE .../text_truth.json` with 43 measured probes (`t_colour_refused`, `t_style_refused` and possibly `t_axis3`/`t_axis2_no_layer` record `rc` 198 and no SVG; every other `rc` is 0), then `git add -f test/fixtures/text_truth.json`. Re-run `python3 -m pytest test/test_textbox_grammar.py -q` and append to `<scratch>/13-04-failure.txt` which stubs now fail for their behavioural reason.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/text_truth.json'));p=d['probes'];print(len(p), sorted(d['_meta'])[:4], p['t_c_red']['added_texts'], p['t_c_red']['added_fills'], p['t_both_empty']['removed_texts'])"` prints 43, a list holding `born_date`, `dash_commit`, `extracted` and `stata_version` among the keys, `['T']`, a list holding red, and the two default titles; `git ls-files test/fixtures/text_truth.json` lists it; `python3 -m pytest test/test_fixtures_are_committed.py test/test_textbox_grammar.py -q -k "fixtures_are_committed or meta_carries" 2>&1 | tail -2` passes.]]></verify>
  <done>twoway's drawn text, colour and font size for every title, axis-title, `axis(2)`, empty-title, prefix/suffix and refused-word case was committed as `test/fixtures/text_truth.json`, stamped with the Stata build and commit it was measured with, by a script that names its method.</done>
</task>

<task type="auto" id="13-07">
  <name>Replace the sub-option table and canonicalise names</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    At `dash_render.py:2438-2445` replace `_TEXTBOX_SUBOPTS` with the `(full, minimum)` tuple of TR-13.1 (a comment citing `textbox_options.sthlp:41-77`, `title_options.sthlp:56-66`, `axis_title_options.sthlp:54-63`, and that `colour`/`style` are refused by twoway and so are left out), add `_textbox_canon(name)` (TR-13.1; lower-case the name; return the one full name whose minimum is a prefix of it and which it is a prefix of; `None` otherwise) and set `_TEXTBOX_SUBOPT_RE = re.compile(r",\s*(?=[A-Za-z_])")` with a comment that this is twoway's `_parse comma`. In `_parse_textbox_opt` (2614) keep `split_at`/`tail` as they are, store `opts[_textbox_canon(m2.group(1)) or m2.group(1).lower()] = ...`, and replace the three-flag loop with `for tok in _dash_by_tokens(tail.strip()): if "(" not in tok: nm = _textbox_canon(tok); if nm in ("span","box","nobox","bexpand","prefix","suffix"): opts[nm] = nm`. In `_textbox_color` (2597) read `opts.get("color", "")` only. Insert `"_TEXTBOX_SUBOPTS"` into the served constants tuple (24326-24428) immediately before `"_TEXTBOX_SUBOPT_RE"`, its first entry (a tuple of tuples writes as `%r`), and `"_textbox_canon"` into the function tuple (24466-24687) immediately after `"_dash_textbox"` (24667). Add `_textbox_canon` to `test/function_test_map.py` in alphabetical place naming `test/test_textbox_grammar.py::TestTheTable::test_every_prefix`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import dash_render as d;print(d._textbox_canon('c'),d._textbox_canon('si'),d._textbox_canon('bex'),d._textbox_canon('colour'),d._textbox_canon('s'),d._parse_textbox_opt('\"T\", c(red) si(large) bex'))"` prints `color size bexpand None None ('T', {'color': 'red', 'size': 'large', 'bexpand': 'bexpand'})`; `python3 -m pytest test/test_textbox_grammar.py -q -k "TestTheTable or TestAbbreviationsAreSubOptions" test/test_textbox_multiline.py test/test_function_test_map.py -q 2>&1 | tail -3` is green.]]></verify>
  <done>Every legal spelling of every textbox sub-option split off the text and reached `_textbox_size`/`_textbox_color` under its full name, in both renderers; the 56 measured line and split cases still passed.</done>
</task>

<task type="auto" id="13-08">
  <name>Name the rest and honour prefix, suffix, axis</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Set `_DASH_TEXTBOX_HONOURED = frozenset({"size", "color", "prefix", "suffix", "axis"})` (18858) and in `_dash_textbox` (18861-18878) compute `bad` as the tokens whose `_textbox_canon(_dash_subopt_name(t))` is not in the set, plus any `axis(#)` token whose argument stripped is not `1` or `2` or whose `option` is not one of `xtitle`, `ytitle`, `xtitle2`, `ytitle2`; report through `_dash_report_suboptions(option, bad, seen, key)` as today. In `_dash_axis_labels` (16003-16038) apply TR-13.7's B3 arms: take `opts` from `_dash_textbox` and build the label from today's `text or default` plus the `suffix` (`default + "\n" + text`) and `prefix` (`text + "\n" + default`) forms; leave the empty-text `or` in place (B6's task 13-14 replaces it). Do not touch `_dash_add_secondary_axes` (13-02 already reads it through `_dash_textbox`, which now canonicalises).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q -k "EverySpelling or Foreign or PrefixSuffix or second_axis_spelling" test/test_suboption_warnings.py test/test_axis_options.py -q 2>&1 | tail -3` is green; `python3 -c "import warnings,dash_render as d;warnings.simplefilter('error');print(d._dash_textbox('\"M\", si(large) c(red) prefix axis(1)','ytitle'))"` prints `('M', {...})` without raising.]]></verify>
  <done>Every sub-option not drawn was named once as written and every honoured one was silent, in both renderers; a lone `suffix`/`prefix` on an axis title added its line after or before the default.</done>
</task>

<task type="auto" id="13-09">
  <name>Add the Python axis(2) title rewrite</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Immediately above `_dash_lone_second_axes` (1639) add `_dash_route_axis_titles(spec)` per TR-13.5: iterate `spec["graphs"]`, for each `graph_options` dict and each `side` in `("y", "x")`, `raw = go.get(f"{side}title")`; when `raw` is a string, `_, opts = _parse_textbox_opt(raw)`; if `opts.get("axis", "").strip() == "2"`, cut the raw value at `_textbox_split_point(raw)`, drop the token whose `_dash_subopt_name` is `axis` from `_dash_by_tokens(tail)`, rebuild `head + (", " + " ".join(rest) if rest else "")`, and if `f"{side}title2"` is absent set it to that and pop `f"{side}title"`, else pop `f"{side}title"` and `_dash_warn_once(("route", key, side), "dash: %stitle(..., axis(2)) and %stitle2() both given; %stitle2() is drawn" % (side, side, side))`; if `"1"`, keep the rebuilt value under `f"{side}title"`. Return a new spec, the caller's untouched; return a wrong-shaped spec as it came, as `_dash_lone_second_axes` does. Call it at 21030 (`self.master_spec = _dash_route_axis_titles(self.master_spec)`) and 24251 (`self.spec = ...`), each on the line BEFORE the `_dash_lone_second_axes` call. Insert `"_dash_route_axis_titles"` into the function tuple after `"_textbox_canon"` (which 13-07 placed after `"_dash_textbox"`) and add it to `test/function_test_map.py` naming `test/test_textbox_grammar.py::TestAxisTwoRouting::test_route_axis_titles_unit`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q -k "TestAxisTwoRouting" 2>&1 | tail -3` passes every case (including the lone-axis case in both modes); `python3 -c "import dash_render as d;s={'graphs':[{'plots':[{'type':'scatter','options':{}}],'graph_options':{'ytitle':'\"P2\", size(large) axis(2)'}}]};print(d._dash_route_axis_titles(s)['graphs'][0]['graph_options'])"` prints `{'ytitle2': '"P2", size(large)'}`.]]></verify>
  <done>A spec carrying `ytitle("...", axis(2))` or `xtitle("...", axis(2))` was drawn with that title on the second axis by both loaders, before the lone-axis rewrite, with any other sub-options kept.</done>
</task>

<task type="auto" id="13-10">
  <name>Route axis(2) titles in Mata</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    In `dash_parse.mata`, after `_dash_rep_split` (4727), add `string scalar _dash_route_axis2(string scalar opts)` per TR-13.6: `toks = _dash_rep_toks(opts, 0)`; for each token, `nm = strlower(_dash_rep_optname(tok))`; when `strlen(nm) >= 3` and (`substr("ytitle", 1, strlen(nm)) == nm` or `substr("xtitle", 1, strlen(nm)) == nm`) and the token has a value, split it with `_dash_rep_split(_dash_rep_value(tok), body, sub)`, walk `_dash_rep_toks(sub, 1)`, and for a word whose `strlower` starts with `axis(` and ends with `)` read the argument with `strtrim(substr(w, 6, strlen(w) - 6))`: `"2"` rewrites the token as `substr(nm, 1, 1) + "title2(" + body + (rest == "" ? "" : ", " + rest) + ")"`, `"1"` as `substr(nm, 1, 1) + "title(" + body + (rest == "" ? "" : ", " + rest) + ")"`; any other argument, and every other token, is kept as typed (a quoted body byte for byte). Join with a blank and return. Document that `_dash_rep_merge` would otherwise fold both copies into one `ytitle`. In `dash.ado`, insert `mata: st_local("opts_raw", _dash_route_axis2(st_local("opts_raw")))` on the line before `_dash_parse_plot_opts , `macval(opts_raw)'` (3783) and `mata: st_local("gopts_raw", _dash_route_axis2(st_local("gopts_raw")))` before `_dash_parse_graph_opts , `macval(gopts_raw)'` (4498), with a comment naming the merge. No library rebuild exists or is needed: dash_parse.mata is `run` from dash.ado. Add `"_dash_route_axis2": ("test_gaps2_truth.cscript:TBG-03", "test_gaps2_truth.cscript:TBG-02")` under `"dash_parse.mata"` in `test/program_coverage_map.py`. Run the S13 block (`GAPS2_ONLY=S13`), JSE-46 and `test_twoway_option_parity.cscript` (TP-14a rows r15-r19 must still pass) through the driver. If TBG-03 cannot be made to pass without weakening it, stop and report: the Python rewrite of 13-09 stays, the two-copy case is recorded as a residual in the B3 BUGS.md entry, and 13-12 marks it -- do not delete the case.
  ]]></action>
  <verify><![CDATA[`grep -c "TBG-0[12356] PASS" /tmp/dash-s13/run_test_gaps2_truth.log` prints 5 (TBG-03: the stored spec carries `ytitle` `"Left"` and `ytitle2` `"Right"` for `ytitle("Left") ytitle("Right", axis(2))`; TBG-06: every hostile title stored as typed); `python3 -m pytest test/test_program_coverage_map.py -q` passes; `/tmp/dash-s13/run_test_twoway_option_parity.log` still reports TP-14 PASS and `grep -c '^r([0-9]*);' /tmp/dash-s13/run_test_twoway_option_parity.log` prints 0.]]></verify>
  <done>`ytitle("a") ytitle("b", axis(2))` reached the spec as two options, `ytitle` and `ytitle2`, because `axis(2)` copies were routed before `_dash_rep_reduce`, the segment merge and the after-comma merge folded copies, and every other title passed through unchanged.</done>
</task>

<task type="auto" id="13-11">
  <name>Flip the pinned textbox tests</name>
  <files>test/test_textbox_multiline.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    In `test/test_textbox_multiline.py::TestParseTextboxOpt` add `test_abbreviations_are_the_same_sub_options` (`'"a", si(large) c(red)'` equals `'"a", size(large) color(red)'`) and in `TestTextboxSplitPoint` add `test_a_comma_before_any_word_splits` (`'"a", bogus(1)'` splits at 3; `'"a", 2 more'` and `'"a", "b"'` do not). In `test/test_mode_parity.py` `CORPUS` add two cases beside 1211: `title("T", c(red)) xtitle("W", si(large))` and `ytitle("Volume", axis(2))` on a y2 layer; each must pass the parity profile without an `ALLOWED` entry (rule R6: `CORPUS` is appended, `ALLOWED` and `_MUST_WARN` are never edited here). Run both files and record the flips as `Flipped:` lines in `<scratch>/13-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_multiline.py test/test_mode_parity.py -q 2>&1 | tail -3` is green with the new cases collected (grep the `-v` output for their ids).]]></verify>
  <done>The parser's pinned tests covered abbreviations and the widened split, and the parity corpus proved both modes drew the abbreviation and `axis(2)` behaviours alike.</done>
</task>

<task type="auto" id="13-12">
  <name>Close B3 in the tracking documents</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append at the end of BUGS.md the closed entry `- [x] Title: Textbox sub-option abbreviations are drawn as title text` with File Names and Line Numbers (`dash_render.py` `_TEXTBOX_SUBOPTS`, `_parse_textbox_opt`, `_dash_textbox`, `_dash_axis_labels`, `_dash_route_axis_titles`; `dash_parse.mata` `_dash_route_axis2`), Description (GAPS2 B3's measured symptoms), Suggested fix, and `- Resolution: Fixed <ddmonyyyy> (WP-28, B3). Sub-options are canonicalised from any of Stata's spellings by _textbox_canon and _parse_textbox_opt, honoured (size, color, prefix, suffix, axis) or named by _dash_textbox, and ytitle(, axis(2))/xtitle(, axis(2)) are routed to the second axis by _dash_route_axis2 in Mata before the repeat merge and by _dash_route_axis_titles in both loaders. Pinned by test/test_textbox_grammar.py::TestAbbreviationsAreSubOptions::test_c_red_is_a_red_title, ::TestAxisTwoRouting::test_axis_2_titles_the_right_axis, test/test_gaps2_truth.cscript TBG-01, TBG-02, TBG-03; fixture test/fixtures/text_truth.json.` plus, only if 13-10 stopped, `Residual, deferred (WP-28): two copies of ytitle() with axis(2) fold into one before Python (dash_parse.mata _dash_rep_merge).` -- the title holds no `"`. Update dash.sthlp: 519-525 say a sub-option under any of Stata's abbreviations is applied (`size()`, `color()`, `prefix`, `suffix`, `axis()`) or named, a word that is not a textbox sub-option is named, and `prefix`/`suffix` add their lines; 2396-2399 replace "which dash does not read as the second axis's" with the sentence that `ytitle(, axis(2))` and `xtitle(, axis(2))` are read as the second axis's title while `ylabel(, axis(2))` and `yscale(, axis(2))` are still named. Grep `test/test_help_claims_*.cscript` and `test/test_help_examples.py` for the changed sentences and update any pin. In `CHANGELOG.md` replace the marker `<!-- WP-28 B3 -->` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of the release's `### Results that change` list (S01, D2) with ONE line ending `(WP-28, B3)`: `title("T", c(red))` drew three lines `T`, `,`, `c(red)` in the scheme colour and `ytitle("Volume", axis(2))` titled the left axis with three lines (the pictures `<scratch>/13-04-failure.txt` recorded, Q24), now `T` in red and the right axis titled `Volume`. Write nothing under any other heading. Run the full pytest suite once in the worktree (`python3 -m pytest test/ -q`, the second launch), then the S13 block through the driver; grep the three files and the message for `claude|anthropic`; commit 13-04..13-12 on `wp28-s13` as ONE commit, subject ending `(GAPS2 B3)`, body opening with `<scratch>/13-04-failure.txt` and carrying the `Regression:` / `Flipped:` (from `<scratch>/13-flips.txt`) / `Fixture: test/fixtures/text_truth.json (scripts/extract_text_truth.do)` / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` with this message (index.md step 1).
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py test/test_help_examples.py -q` passes; `grep -c '<!-- WP-28 B3 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, B3)' CHANGELOG.md BUGS.md` prints 2; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0 and `git log -1 --format=%s | grep -c '(GAPS2 B3)'` prints 1.]]></verify>
  <done>B3 was closed in BUGS.md naming its tests, the help described the grammar dash reads, the B3 marker was replaced by the line with the recorded old pictures, and one green commit on `wp28-s13` carried the fixture and the fix.</done>
</task>

<task type="auto" id="13-13">
  <name>Write the failing B6 tests</name>
  <files>test/test_textbox_grammar.py, test/test_dual_axis.py, test/test_gaps2_truth.cscript</files>
  <action><![CDATA[
    Append to `test/test_textbox_grammar.py` the class `TestEmptyTitles` with exactly the five stub names (the fixture-pinned one parametrised over the six empty-title ids). In `test/test_dual_axis.py::TestTheLoneAxisRewrite` add `test_an_empty_second_title_is_moved_and_removes_the_title` (both modes through `_lone_figure`: `{"ytitle2": '""'}` gives `''` on the left axis). In the S13 block of `test/test_gaps2_truth.cscript` insert TBG-04 between TBG-03 and TBG-05: `xtitle("") ytitle("")`: twoway's SVG lacks `Weight (lbs.)` and `Mileage (mpg)` (`cert_svg_has_text` `r(found)` 0 for both) and dash's page's axis labels are empty. Do not touch dash_render.py. Run `python3 -m pytest test/test_textbox_grammar.py -k TestEmptyTitles test/test_dual_axis.py -q` and the S13 block through the driver against the tree as the B3 commit left it. Do not commit: save the failure output (`weight`/`mpg` drawn for empty text; the lone `ytitle2("")` drawing `mpg`; TBG-04's page holding the default titles) to `<scratch>/13-13-failure.txt` (Q24, S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q -k TestEmptyTitles 2>&1 | tail -5` reports 0 passed and no collection error, the headline failure showing `weight`; `grep -c "TBG-04" /tmp/dash-s13/run_test_gaps2_truth.log` is non-zero and TBG-04 fails; `<scratch>/13-13-failure.txt` exists.]]></verify>
  <done>The B6 regression tests existed, collected, and failed for the reason the gap describes, with no product file changed and nothing committed.</done>
</task>

<task type="auto" id="13-14">
  <name>Make empty text remove an axis title</name>
  <files>dash_render.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    In `_dash_axis_labels` (16003-16038) replace the `text or default` of 13-08 with TR-13.7's `given` rule: `given = bool(str(raw or "").strip())`, `label = text if given else default`, the `prefix`/`suffix` arms unchanged, so `xtitle("")`, `ytitle("")` and `xtitle("", size(large))` give `''` while an absent option keeps the default. In `_dash_add_secondary_axes` confirm a raw `""` gives `''` through `_dash_textbox` (13-02) and leave `_dash_lone_second_axes` 1692-1694 as it is, with a comment that a raw `""` is deliberately moved so `ytitle("", axis(2))` and `ytitle2("")` on a lone graph remove the one title. In `test/test_mode_parity.py` `CORPUS` add the case `xtitle("") ytitle("")` beside 1211; it must pass the parity profile without an `ALLOWED` entry (rule R6). Run `test/test_textbox_grammar.py -k TestEmptyTitles`, `test/test_dual_axis.py`, `test/test_mode_parity.py`, then the S13 block through the driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q -k TestEmptyTitles test/test_dual_axis.py test/test_mode_parity.py -q 2>&1 | tail -3` is green; `grep -c "TBG-0[1-6] PASS" /tmp/dash-s13/run_test_gaps2_truth.log` prints 6.]]></verify>
  <done>An axis title option given with empty text drew no title on that axis, in both modes and on the second axis, while an absent option kept twoway's default.</done>
</task>

<task type="auto" id="13-15">
  <name>Close B6 in the tracking documents</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append at the end of BUGS.md the closed entry `- [x] Title: An empty xtitle() or ytitle() does not remove the axis title` with File Names and Line Numbers (`dash_render.py` `_dash_axis_labels`, `_dash_lone_second_axes`), Description (GAPS2 B6's measured symptoms), Suggested fix, and `- Resolution: Fixed <ddmonyyyy> (WP-28, B6). _dash_axis_labels distinguishes an option given with empty text (no title) from an absent option (twoway's default), for xtitle(), ytitle(), ytitle(, axis(2)) and ytitle2(), in both renderers. Pinned by test/test_textbox_grammar.py::TestEmptyTitles::test_empty_text_removes_the_title, ::TestEmptyTitles::test_second_axis_empty, test/test_gaps2_truth.cscript TBG-04.` -- the title holds no `"` (spell empty text as "empty", never as `("")`). Update dash.sthlp 455-458: `xtitle("")`, `ytitle("")` and `ytitle("", axis(2))` remove the title; grep `test/test_help_claims_*.cscript` and `test/test_help_examples.py` for the changed sentences and update any pin. In `CHANGELOG.md` replace the marker `<!-- WP-28 B6 -->` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of the release's `### Results that change` list (S01, D2) with ONE line ending `(WP-28, B6)`: `xtitle("")` drew `weight` and `ytitle("")` drew `mpg` (the pictures `<scratch>/13-13-failure.txt` recorded, Q24), now no title. Write nothing under any other heading. Run the full pytest suite once in the worktree as `FULL_SUITE_RERUN=1 python3 -m pytest test/ -q` (the third launch of this session; the guard hook refuses it without the prefix), then the S13 block through the driver; grep the three files and the message for `claude|anthropic`; commit 13-13..13-15 on `wp28-s13` as ONE commit, subject ending `(GAPS2 B6)`, body opening with `<scratch>/13-13-failure.txt` and carrying the `Regression:` / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` with this message (index.md step 1); report `git checkout main && git merge s3-bugs` without running it.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py test/test_help_examples.py -q` passes; `grep -c '<!-- WP-28 B[367] -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, B6)' CHANGELOG.md BUGS.md` prints 2; `git log -3 --format=%B | grep -ci 'claude\|anthropic'` prints 0 and `git log -3 --format=%s | grep -c '(GAPS2 B[367])'` prints 3.]]></verify>
  <done>B6 was closed in BUGS.md naming its tests, the help stated that empty text removes a title, the B6 marker was replaced by the line with the recorded old picture, and the section's third green commit on `wp28-s13` carried it.</done>
</task>

## Section completion criteria

- All stubs of 13-01, 13-04 and 13-13 pass in both modes; each failed on the tree before its gap's fix for its recorded reason; no test was deleted.
- `test/fixtures/text_truth.json` is committed with its `_meta` stamp, named by `test_textbox_grammar.py`, its `title` probes pinned by `TestTheFixtureIsPinned` and `TestEmptyTitles`, and the marked region `* ---- section 15: legend probes ----` is in `scripts/extract_text_truth.do` for section 15.
- Three commits on `wp28-s13`, subjects ending `(GAPS2 B7)`, `(GAPS2 B3)`, `(GAPS2 B6)` in that order, each after a green full suite; no test-only commit exists (D1).
- The S13 block of `test_gaps2_truth.cscript` (TBG-01..06), `test_json_escaping.cscript`, `test_twoway_option_parity.cscript` and `test_textbox_multiline.cscript` pass under Stata's Python with no skip; no new `.cscript` file, no runner or hygiene-pin edit (D11).
- `_TEXTBOX_SUBOPTS` (before `_TEXTBOX_SUBOPT_RE`), `_textbox_canon` and `_dash_route_axis_titles` (after `_dash_textbox`) are in the served copy lists and `function_test_map.py`; `_dash_route_axis2` is in `program_coverage_map.py` citing TBG-03 and TBG-02.
- Three closed BUGS.md entries in the D3 form; dash.sthlp updated; the three markers replaced; no `dash:` note for any honoured spelling.

## Notes

- **Gap order.** B7 (the second axis's textbox read) precedes B3 and B6 because a routed `ytitle("Volume", axis(2))` reaches `_dash_add_secondary_axes` as the raw value `"Volume"` and only the textbox read draws it without quotes; likewise `ytitle2("")`. The GAPS2 numbering is not an execution order.
- **Renderer order.** Saved: scheme 22037 → `_dash_figure_title`/`_dash_style_axis_titles` 22040-22041 → `_dash_add_secondary_axes` 22096. Template: scheme 26204 → `_dash_add_secondary_axes` 26207 → styling 26210-26211. Styling the second axis inside the function is what makes the order irrelevant; do not move the call sites.
- **Copy lists (rule R2).** `_TEXTBOX_SUBOPTS` is not in the constants tuple at 91d97be: insert it before `_TEXTBOX_SUBOPT_RE`, the tuple's first entry (a tuple of tuples writes as `%r`, 24447; a compiled regex through the `pattern`/`flags` branch); `_textbox_canon` and `_dash_route_axis_titles` go after `_dash_textbox` (24667). Forgetting `_TEXTBOX_SUBOPTS` leaves the served `_textbox_canon` raising `NameError` at runtime -- `TestTheServedCopy` catches it, as does `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`. `function_test_map.py` and `program_coverage_map.py` entries go in alphabetical place; the merger resolves append conflicts.
- **Commit bodies** use S01 TR-01.9's line forms verbatim: `Regression: test/<file>.py::<Class>::<test> -- failed at 91d97be with <text>`, `Flipped: <node> -- <old expectation> was wrong because <why>` (one per flip), `Fixture: test/fixtures/text_truth.json (scripts/extract_text_truth.do)` (the B3 commit), `BUGS.md: "<title>" (closed)`.
- **Shared registries (rules R1-R6).** R1: the TBG cases are one block of `test_gaps2_truth.cscript`, appended above its closing line in section order; the runner and the hygiene pins are never edited. R3: BUGS.md is appended at the end, each gap replaces only its own marker, and dash.sthlp 455-458, 519-525, 2396-2417 are this section's paragraphs. R5: `text_truth.json` is regenerated once here and once by section 15 in batch 3, never patched by hand. R6: `CORPUS` gains three cases; `ALLOWED` and `_MUST_WARN` are never edited here.
- **The split widened on purpose.** Under the old regex `title(Sales, and more)` (unquoted) kept its comma; under `_parse comma` it is `Sales` with `and more` named, which is nearer twoway's r(198) than drawing it. Every quoted comma case (`TestCommaInsideTheUsersText`, `_MEASURED_SPLITS`) is inside a string or parentheses and unaffected.
- **Mata rewrite hazards.** Read `opts_raw` with `st_local`, never through a macro expansion; `"'` inside a title would end a compound quote. TBG-06 runs the rewrite over `title(`"'90s"')`-shaped values (JSE-42..49) and a quoted `axis(2)` to show nothing is expanded or routed. `yti2(` has optname `yti2`, not a prefix of `ytitle`, so aliases are untouched. `_dash_rep_scan` will see `ytitle(` and `ytitle2(` as prefix-related spellings and put each to the parser alone; they bind to different keys and do not merge.
- **The lone-axis rewrite.** `_dash_route_axis_titles` must run first: after routing, a lone-axis(2) graph's `ytitle2` is moved into `ytitle` by `_dash_lone_second_axes` and drawn on the one left axis, which is twoway's picture (`t_ytitle_axis2_lone`).
- **Fixture exclude rule.** `.git/info/exclude` carries `*.json`; `git add -f`. `test_fixtures_are_committed.py` needs the file name `text_truth.json` to appear as a whole token in a test file; `test_textbox_grammar.py` names it.
- **BUGS.md titles hold no `"`** (S01 TR-01.8): spell empty text as "empty", not `("")`.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; a run of cscript skips is then not a pass. Check `c(python_exec)` before trusting skips; the slot wrapper is what keeps Stata sessions at three.
- **Stata invocation.** Every run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (D6): the extract script directly (it sets its own directories), a cscript through the two-line driver of "Stata truth" (it resolves its helpers from `test/`); never the GUI, never a bare `stata-mp`, never the full cert suite inside a section (S19 runs it).
- **Merge with section 15.** Section 15 (batch 3) appends `zp` lines in the marked region and regenerates the fixture once; the regenerated fixture must leave every `title` probe's records unchanged, checked probe by probe outside `_meta`, never by a diff's line count.
- **Unquoted suffix.** `_dash_rep_merge` joins `title(A) title(B, suffix)` as `A B`, which TP-14a r18 measured identical to twoway's SVG; the quoted form `title("A") title("B", suffix)` joins as `"A" "B"`, two lines. `t_title_two_suffix` pins whichever twoway draws; if it disagrees with the merge, record it in the B3 entry rather than changing the merge here.
- **Line numbers drift** by the lines each task adds (13-07 about +30 at 2438; 13-09 about +45 at 1639). Anchors are also given as symbols; the symbol is authoritative.
