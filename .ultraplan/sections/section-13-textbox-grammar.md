# Section 13: Textbox grammar (B3, B6, B7)

> Part of: WP-28 · Gaps: B3, B6, B7 · Risk: yellow · Batch: 2 · Depends on: 02 · Blocks: 15, 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **02** · Blocks **15, 19** · Risk **yellow** · Commits: three commits: B3, B6, B7 → CHANGELOG `Results that change`

- D10: read `size` (not `font_size`) from `svg_texts`; the B6 BUGS.md title is `An empty xtitle() or ytitle() does not remove the axis title` (no quotation marks in a title).
- R1: register `test_textbox_grammar.cscript` in `test/run_all_cscripts.do` and bump the hygiene pins.
- Stub: a compound-quoted `ytitle2`.
- D7: split 13-01.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

Every text option twoway takes -- `title()`, `subtitle()`, `note()`, `caption()`, `xtitle()`, `ytitle()`, and dash's own `ytitle2()`/`xtitle2()` -- is a textbox: `"string" ["string" ...] [, suboptions]`, where each string is a line and the sub-options may be abbreviated to Stata's documented minimums (`c:olor`, `si:ze`, `j:ustification` ...). dash reads the sub-options only under their full names, so GAPS2 measures that `title("T", c(red))` draws the three lines `T`, `,`, `c(red)` in the scheme's colour with no warning, and `ytitle("Volume", axis(2))` titles the left axis with the whole tail as text (B3). `xtitle("")`, which `axis_title_options.sthlp:218-228` makes the standard way to remove an axis title, still draws `weight`, and `ytitle("")` still draws `mpg` (B6). `ytitle2("P2")` draws `"P2"` with its quote marks, `ytitle2("a" "b")` one quoted line, and `ytitle2("P2", size(large))` the sub-option verbatim (B7). All of it in both render modes, rc 0.

After this section a textbox is read as twoway reads it: any legal spelling of a sub-option is either honoured (`size()`, `color()`, `prefix`, `suffix`, `axis(1|2)`) or named once in the note, never drawn; `axis(2)` on `ytitle()`/`xtitle()` routes the title to the second axis before dash.ado's repeat merge can fold it into the first axis's copy; an option given with empty text removes the title while an absent option keeps the default; and the second axis's title goes through the same reader, the same lines and the same `size()`/`color()` styling as the first, whichever renderer adds the axis first. Honoured options print nothing (DISCOVERY Q22).

The three gaps share one component: `_parse_textbox_opt` and the table it splits on, `_dash_textbox` which names what is not honoured, `_dash_axis_labels` which turns the text into an axis title, and `_dash_add_secondary_axes`, the one reader of `{n}title2`. Truth comes from twoway's own SVG through section 02's helper, recorded once into `test/fixtures/text_truth.json` by a new `scripts/extract_text_truth.do`, which section 15 extends with its legend probes.

**Test order (project rule 7): task 13-01 writes every regression test for this section**, runs it against the unmodified tree, and records the failure. 13-02 records the truth; 13-03 through 13-09 turn the tests green a gap at a time; 13-10 closes the entries.

## Risk: [yellow] — one table drives every text option in both renderers, and one Mata rewrite runs before every option list is parsed

- **Why:** the split regex and the honoured set are consulted for every title, note, caption and axis title dash draws; a wrong minimum abbreviation silently changes what is text and what is a sub-option. The Mata routing rewrites raw option text before `-syntax-` sees it.
- **Risk factors:** (1) the served app receives `_TEXTBOX_SUBOPT_RE` and `_DASH_TEXTBOX_HONOURED` by copy (constants list 24326-24428), so a table that is not in the list leaves the two modes reading different grammars; (2) the two renderers call `_dash_add_secondary_axes` on opposite sides of `_dash_style_axis_titles` (saved 22096 after, template 26207 before); (3) `_dash_rep_merge` (dash_parse.mata 4826-4855) folds every copy of `ytitle` into one before Python runs, so a Python-only routing cannot draw `ytitle("a") ytitle("b", axis(2))`; (4) 40 pinned tests read `_parse_textbox_opt`'s split.
- **Mitigation:** the table is transcribed from Stata's help and pinned by a test over every prefix of every name; the split rule becomes twoway's own `_parse comma` (the first top-level comma followed by a name), so the 15 measured split cases and the 35 measured line cases keep passing unchanged; styling of the second axis moves inside `_dash_add_secondary_axes` so renderer order cannot matter; the Mata route is proven by a cscript that stores both titles, and a Python rewrite beside `_dash_lone_second_axes` covers hand-built specs and pytest; every honoured spelling is asserted quiet in both modes.

## Dependencies

- **Depends on:** section 02 (`scripts/svg_truth.py`, `test/cert_svg.do`).
- **Blocks:** section 19.
- **Parallel batch:** 2. **Can run with:** 11, 12, 14, 15, 16, 17. Section 15 appends legend probes to the extract script this section creates: merge 13 before 15 and regenerate the fixture once on the merged tree (Notes).
- Why: the cscript and the extract script read twoway's SVG through section 02's helper; nothing else in batch 2 touches `_parse_textbox_opt`, `_dash_textbox`, `_dash_axis_labels` or `_dash_add_secondary_axes`.

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

Verified by research: `_parse_textbox_opt('"T", c(red)')` returns `('T\n,\nc(red)', {})` and `'"Volume", axis(2)'` returns `('Volume\n,\naxis(2)', {})`. `_textbox_color` (2597-2611) reads `color`/`colour`; `_textbox_size` (2577-2594) reads `size`. `_dash_textbox` (18861-18878) names every tail token whose name is not in `_DASH_TEXTBOX_HONOURED = frozenset({"size", "color", "colour"})` (18858), compared as written. Callers of `_parse_textbox_opt`: 18870, 18916 (`_dash_style_axis_titles`), 21978 (saved figure title), template 26149. Callers of `_dash_textbox`: 16034-16035 (`_dash_axis_labels`), 18889 (`_dash_figure_title`), 18968 (`_dash_text_annotations`).

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

`ServerAppBuilder` copies constants at 24326-24428 (`_TEXTBOX_SUBOPT_RE`, `_DASH_TEXTBOX_HONOURED` are listed; a compiled regex is written as `re.compile(pattern, flags)` at 24438-24444; every other value as `%r`) and functions at 24466-24687 (`_parse_textbox_opt`, `_textbox_split_point`, `_textbox_lines`, `_textbox_string_end`, `_textbox_size`, `_textbox_color`, `_dash_textbox`, `_dash_style_axis_titles`, `_dash_axis_labels`, `_dash_add_secondary_axes`, `_dash_lone_second_axes` are listed). `test/function_test_map.py` must name a test for every new function.

### Fixtures on disk

`test/fixtures/axis_truth.json` (233 probes) records title probes under `findings.titles_notes_captions` and `title_text_fidelity` but no abbreviation, `axis(2)`, empty-title or `ytitle2` case. No `.svg` is committed. This section adds `test/fixtures/text_truth.json`.

### Existing tests that pin today's behaviour (flip, never delete)

- `test/test_json_escaping.cscript` JSE-46 case `jg46k` (1974-2011): the count `_jg_drawn LinearAxis` with `JG_WANT` = `line 1\nline 2` is asserted `1`; after B7 the right axis of `jg46k` draws it too, so the count becomes `2`. Extend the case to compare that axis with twoway's SVG for `ytitle("a" "b", axis(2))`.
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
- **BR-13.2** `size()` and `color()` under any legal spelling change the drawn size and colour; `prefix`, `suffix` and `axis(1)`/`axis(2)` are applied; every other sub-option is named. Applied sub-options print nothing.
- **BR-13.3** A word after the sub-option comma that is not in Stata's table (`colour`, `style`, a misspelling) is named, not drawn.
- **BR-13.4** `ytitle("T", axis(2))` and `xtitle("T", axis(2))` title the second axis, with any other sub-options kept; `axis(1)` titles the first; `axis(3)` and above are named. `ytitle("a") ytitle("b", axis(2))` titles both axes.
- **BR-13.5** `xtitle("")`, `ytitle("")`, `xtitle("", size(large))` and `ytitle("", axis(2))` draw no title on that axis; an absent option keeps twoway's default (variable label, `Density`, `kdensity <var>`).
- **BR-13.6** `ytitle2()`/`xtitle2()` draw their text without quote marks, one line per string, with `size()` and `color()` applied and the rest named, identically in both modes.
- **BR-13.7** A lone `ytitle("x", suffix)` draws the default title then `x`; `prefix` the reverse; on `title()`, `subtitle()`, `note()` and `caption()` a lone `prefix`/`suffix` changes nothing and says nothing.
- **BR-13.8** Every drawn text and colour is what twoway's SVG draws for the same command, recorded in `test/fixtures/text_truth.json`.

## Technical requirements

- **TR-13.1** Replace `_TEXTBOX_SUBOPTS` (2438) with a tuple of `(full, minimum)` pairs transcribed from the table above, in that order, and add `_textbox_canon(name)` returning the full name for any spelling with `len(name) >= len(minimum)` and `full.startswith(name)`, else `None`. `colour` and `style` are not in the table.
- **TR-13.2** `_TEXTBOX_SUBOPT_RE` (2444) becomes `re.compile(r",\s*(?=[A-Za-z_])")`: a comma followed by a name start. `_textbox_split_point` (2484) keeps its scan and its parenthesis and string rules; the name check is gone, so the split is twoway's `_parse comma` for any word. A comma followed by a digit, a quote or nothing stays text.
- **TR-13.3** `_parse_textbox_opt` (2614) stores each `name(value)` under `_textbox_canon(name) or name.lower()` and reads the bare words of the tail with `_dash_by_tokens`, storing every flag word (`span`, `box`, `nobox`, `bexpand`/`bex`, `prefix`, `suffix`) under its canonical name; `_textbox_color` (2597) reads `color` only.
- **TR-13.4** `_DASH_TEXTBOX_HONOURED` (18858) becomes `frozenset({"size", "color", "prefix", "suffix", "axis"})`; `_dash_textbox` (18861) compares `_textbox_canon(_dash_subopt_name(tok))` and names the rest as written, `axis(#)` included when `#` is not 1 or 2 or the option is not an axis title.
- **TR-13.5** New `_dash_route_axis_titles(spec)` beside `_dash_lone_second_axes` (1639): for each graph's `graph_options`, for `ytitle`/`xtitle`, when `_parse_textbox_opt(raw)[1].get("axis") == "2"` move the raw value, minus the `axis(2)` token, to `ytitle2`/`xtitle2` (kept as the raw value with its other sub-options), and drop `ytitle`; when `"1"`, keep the value in place minus the token; an explicit `ytitle2` already present wins and the routed copy is dropped with `_dash_warn_once` naming it. Pure function, new dict, wrong-shaped spec returned as it came. Called in both loaders immediately BEFORE `_dash_lone_second_axes` (21031, 24252). Added to the function copy list (24466-24687) and `test/function_test_map.py`.
- **TR-13.6** New Mata `_dash_route_axis2(opts)` in dash_parse.mata beside `_dash_rep_split`: over `_dash_rep_toks(opts, 0)`, a word whose `_dash_rep_optname` is a prefix of `ytitle` or `xtitle` of length 3 or more (`yti`, `ytit`, ... `ytitle`; never `yti2`) and whose `_dash_rep_split` sub-options hold a word equal, lower-cased and blanks trimmed inside the parentheses, to `axis(2)`, is rewritten as `ytitle2(`body`[, other sub-options])` (`xtitle2` likewise); one holding `axis(1)` loses that word; everything else is returned as typed. No regex (memory: `regexm` follows the caller's version); `strlower`, `strtrim`, `strpos` only. Called from dash.ado before `_dash_parse_plot_opts , `macval(opts_raw)'` (3783) as `mata: st_local("opts_raw", _dash_route_axis2(st_local("opts_raw")))` and before `_dash_parse_graph_opts , `macval(gopts_raw)'` (4498) on `gopts_raw`. Entry in `test/program_coverage_map.py` under `dash_parse.mata` naming `test_textbox_grammar.cscript:TBG-03`.
- **TR-13.7** `_dash_axis_labels` (16003): `given = bool(str(raw).strip())` per axis; `label = text if given else default`; with `suffix` in the sub-options `label = default + ("\n" + text if text else "")`, with `prefix` `(text + "\n" if text else "") + default`. Same rule for `ytitle2`/`xtitle2` inside `_dash_add_secondary_axes` (no default there today, so `given` and empty gives `''`).
- **TR-13.8** `_dash_add_secondary_axes(fig, plots, graph_opts, frame, seen=None, key="")` (16997): `text, opts = _dash_textbox(graph_opts.get(f"{n}title2", ""), f"{n}title2", seen, key)`; `axis_label=text`; then `px = _textbox_size(opts, None)` and `colour = _textbox_color(opts, None)` set `ax.axis_label_text_font_size = f"{px:g}px"` and `ax.axis_label_text_color` when not `None`, inside the function. Both call sites pass the renderer's `seen`/`key`: 22096 `_seen, _gkey`; template 26207 `_reported_subopts, gname`.
- **TR-13.9** `scripts/extract_text_truth.do` writes `test/fixtures/text_truth.json` (Stata truth below); `test/test_textbox_grammar.py` pins it; `test/test_textbox_grammar.cscript` compares a live twoway export with dash's page through `cert_svg_*`.
- **TR-13.10** Security (project rule 1): title and axis-title text stays canvas text (never `html.escape`d, as 16013-16015 documents); the Mata rewrite reads the option text by value through `st_local` and returns it to a local read through `macval()`, never expanding it; the Python rewrite touches only the two title keys; no `eval`, no `shell`.
- **TR-13.11** dash.sthlp: 519-525 (sub-options named), 455-458 (empty text clears; prefix/suffix), 2396-2399 and 2403-2417 (`axis(2)` now read; `ytitle2(tinfo)`); CHANGELOG "Results that change" one line per gap; BUGS.md three closed entries.

## Boundaries

- Do not touch `_dash_apply_legend`, `_dash_legend_entries`, `_DASH_LEGEND_*` (section 15), `_dash_parse_axis_label_opt`/`_dash_parse_axis_spec` (section 14), `_dash_apply_scale_ranges`/`_dash_finish_secondary_axes` (section 18), `GlyphMapper._apply_colorvar` (section 16), `SchemeParser` (section 6).
- `ylabel(, axis(2))`, `yscale(, axis(2))`, `xline(, axis(2))` stay as they are (GAPS2 B15, not in scope); only the two title options route.
- A second axis's default title (twoway: the label of the variable on that axis) is not added; `ytitle2` absent stays `''`.
- The scheme's axis-title font is not applied to a second axis added after `apply_to_figure` in either mode today; unchanged here.
- `t1title()` .. `r2title()`, `title2()`, `subtitle2()` stay pending (dash.ado 768-797) and named.
- `ytitle("T", axis(2))` on a graph with no layer on axis 2 keeps today's behaviour (the routed `ytitle2` is not drawn, nothing is said); twoway's answer is recorded in the fixture (`t_axis2_no_layer`), not acted on.
- PRD §7 exclusions and DISCOVERY Q22 (silent when honoured) hold.

## Stata truth

New `scripts/extract_text_truth.do` → `test/fixtures/text_truth.json`, in `extract_axis_truth.do`'s shape: the `*!` header stating the method, `clear all`, `set graphics off`, `global ZA_REPO`/`ZA_OUT`/`ZA_WORK`/`ZA_REC`, a `zp` program registering `id group dataset body opts control` (the sixth argument is the id of the companion probe whose texts are subtracted; empty for a control itself), the export loop of `extract_axis_truth.do:392-428` (SVG only, no `.gph`), `capture noisily` per probe with `rc` recorded, and ONE trailing `python:` block that reads the record file, imports `svg_truth` from `${ZA_REPO}/scripts` via `sys.path.insert`, and writes the JSON. The block never calls Stata; a backtick is spelled `\x60`; spaces written as U+00A0 by `nbsp(on)` are normalised to a space before comparing.

Per probe the fixture records `{"group", "command", "rc", "control", "texts" (every `<text>` string in document order), "fills" (sorted distinct fill colours, lower-cased), "added_texts" (multiset difference probe minus control, probe order), "removed_texts" (control minus probe), "added_fills", "font_sizes" ({text: px} from each `svg_texts` entry's `font_size`; the entries carry the keys of `extract_axis_truth.do`'s text inventory, section 02)}`. Group `title` probes (section 15 adds group `legend` after these, before the export loop):

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
```

Run from a scratch directory, never the GUI (project rule 10), at most three Stata sessions at once, each with its own `STATATMP` (trailing slash, apart from the log's directory):

```
mkdir -p /tmp/dash-s13/tmp && cd /tmp/dash-s13 && STATATMP=/tmp/dash-s13/tmp/ \
  arch -arm64 /usr/local/bin/stata-mp -b do \
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_text_truth.do
```

Then `git add -f test/fixtures/text_truth.json` (`.git/info/exclude` drops `*.json` otherwise) and confirm `test/test_fixtures_are_committed.py` passes: the fixture is named by `test_textbox_grammar.py` and `test_textbox_grammar.cscript`. The fixture's `meta` records `c(stata_version)`, `c(born_date)`, the date, the scheme in force, and the method sentence.

## TDD test stubs

New file `test/test_textbox_grammar.py`; both-mode helpers imported from `test_textbox_multiline._both_modes`/`_drawn` (520-552, 502-517) and `test_dual_axis._lone_figure` (311-335); a `truth()` fixture like `test_axis_options.py:40-47` that fails, never skips, when the fixture is missing. Regression stubs that fail at `91d97be` come first.

- Test: `title("T", c(red))` draws the text `T` in `#ff0000` in both modes — `test_textbox_grammar.py::TestAbbreviationsAreSubOptions::test_c_red_is_a_red_title` (fails: text `T\n,\nc(red)`).
- Test: every spelling of `size` (`si` .. `size`) changes the title's font size and leaves the text bare, both modes — `::TestAbbreviationsAreSubOptions::test_every_size_spelling`.
- Test: table over the six text options × every name × its minimum, an intermediate and its full spelling: `size`/`color` applied, the rest named exactly once in both modes, the text bare — `::TestEverySpellingOnEveryOption::test_spelling` (parametrised; fails today for every abbreviation).
- Test: `ytitle2`/`xtitle2` × `size`/`si`/`color`/`c` style the second axis, both modes — `::TestEverySpellingOnEveryOption::test_second_axis_spelling`.
- Test: `colour(red)` and `style(x)` are named, not drawn, and `_textbox_canon("colour") is None` — `::TestForeignWordsAreNamed::test_colour_and_style`.
- Test: `ytitle("Volume", axis(2))` titles the right axis `Volume` and leaves the left axis's default, both modes — `::TestAxisTwoRouting::test_axis_2_titles_the_right_axis` (fails: left axis `Volume\n,\naxis(2)`).
- Test: `ytitle("a" "b", axis(2))` two lines; `"P2", size(large) axis(2)` sized — `::TestAxisTwoRouting::test_lines_and_size_survive_the_route`.
- Test: `ytitle("Lone", axis(2))` on a lone-axis(2) graph titles the one left axis, both modes (the route runs before the lone rewrite) — `::TestAxisTwoRouting::test_the_route_runs_before_the_lone_rewrite`.
- Test: `_dash_route_axis_titles` unit cases: `axis(1)` stays, `axis(3)` untouched and later named, explicit `ytitle2` kept with one warning, malformed spec passthrough, caller's dict unmodified — `::TestAxisTwoRouting::test_route_axis_titles_unit`.
- Test: `xtitle("")` and `ytitle("")` give `''` labels in both modes; the fixture's `removed_texts` for `t_both_empty` holds both default titles — `::TestEmptyTitles::test_empty_text_removes_the_title` (fails: `weight`/`mpg`).
- Test: `xtitle("", size(large))` gives `''` — `::TestEmptyTitles::test_empty_text_with_a_sub_option`.
- Test: absent options keep `Density` on a histogram and `kdensity x` on a kdensity; `ytitle("")` on a histogram removes `Density` — `::TestEmptyTitles::test_defaults_stay_when_absent`.
- Test: `ytitle2("")` gives `''` on the right axis; `ytitle2("")` on a lone-axis(2) graph gives `''` on the left — `::TestEmptyTitles::test_second_axis_empty`.
- Test: `ytitle2("P2")` draws `P2` (no quotes), `"a" "b"` two lines, `"P2", size(large)` sized, `c(red)` red, an unknown sub-option named once; saved and served font sizes equal — `::TestSecondAxisTitleIsATextbox::test_text_lines_size_colour` (fails: `"P2"`).
- Test: `ytitle("extra", suffix)` draws the fixture's `t_ytitle_suffix` lines (default then `extra`); `prefix` the reverse; a lone `title("T", suffix)` draws `T` and warns nothing — `::TestPrefixSuffix::test_lone_suffix_and_prefix`.
- Test: dash's drawn title text and colour equal the fixture's `added_texts`/`added_fills` for every honoured `title` probe — `::TestTheFixtureIsPinned::test_dash_draws_what_twoway_draws` (parametrised over the fixture's group `title`).
- Test: the served app source defines `_TEXTBOX_SUBOPTS`, `_textbox_canon`, `_dash_route_axis_titles`, `_DASH_TEXTBOX_HONOURED` — `::TestTheServedCopy::test_the_names_are_copied`.
- Test: `_textbox_canon` maps every prefix of every name from its minimum to its full name, shorter prefixes to `None`, and the table equals Stata's (hard-coded) — `::TestTheTable::test_every_prefix` (fails: `AttributeError`).
- Test: `_parse_textbox_opt('"a", c(red) si(large) bex')` → `{"color": "red", "size": "large", "bexpand": "bexpand"}` — `::TestTheTable::test_parse_canonicalises`.
- Test: the 56 measured line/empty/split cases of `test_textbox_multiline.py` still pass (`python3 -m pytest test/test_textbox_multiline.py`) — a guard, not a stub.
- cscript `test/test_textbox_grammar.cscript` TBG-01 `title("T", c(red))`: `cert_svg_has_text, file() text("T")` returns `r(found)` 1 and `text("c(red)")` 0, and `cert_svg_fills`'s `r(colours)` holds `#ff0000`; dash's page has `"text":"T"` and `"text_color":"#ff0000"`; TBG-02 `ytitle("Volume", axis(2))`: twoway's SVG has `Volume`; dash's page has a `LinearAxis` with `y_range_name` `y2` and `axis_label` `Volume`, the left axis `Mileage (mpg)`; the stored spec carries `ytitle2` and no `ytitle`; TBG-03 `ytitle("Left") ytitle("Right", axis(2))`: the stored spec carries `ytitle` `"Left"` and `ytitle2` `"Right"` (Mata-only proof); TBG-04 `xtitle("") ytitle("")`: twoway's SVG lacks `Weight (lbs.)` and `Mileage (mpg)`; dash's axis labels are empty; TBG-05 `ytitle("extra", suffix)`: twoway's texts hold `Mileage (mpg)` and `extra`; dash's left axis label is `Mileage (mpg)\nextra`.
- JSE-46 `jg46k` extended: the `LinearAxis` count for `line 1\nline 2` is `2`, and `ytitle("a" "b", axis(2))` drawn on dash's right axis equals twoway's SVG texts `a`, `b` read with `cert_svg_has_text, file() text("a")` and `text("b")` (`r(found)`), the export made with `cert_svg_export`.
- Flipped rows in `test_suboption_warnings.py`: `SUBOPTIONS` gains `("title c and bc", {"title": 'T, c(red) bc(red)'}, None, "title", ["bc(red)"], ["c"])`, `("xtitle orient", {"xtitle": "Weight, orient(vertical)"}, None, "xtitle", ["orient(vertical)"], [])`, `("ytitle axis 3", {"ytitle": "M, axis(3)"}, None, "ytitle", ["axis(3)"], [])`; `TestTheHonouredOnesStayQuiet` gains `{"ytitle": 'M, si(large) c(red) prefix'}`, `{"xtitle": 'W, axis(1)'}`.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| Abbreviation table and canonicalisation | pytest `TestTheTable` | none | n/a |
| Every spelling on every option, honoured or named | pytest `TestEverySpellingOnEveryOption` | none | yes |
| Foreign words named | pytest `TestForeignWordsAreNamed` | `text_truth.json` (`rc` of `t_colour_refused`) | yes |
| `axis(2)` routing, Python | pytest `TestAxisTwoRouting` | `text_truth.json` | yes |
| `axis(2)` routing, Mata (two copies) | cscript TBG-02, TBG-03 | live twoway export | saved page |
| Empty titles | pytest `TestEmptyTitles`; cscript TBG-04 | `text_truth.json` | yes |
| Second-axis textbox | pytest `TestSecondAxisTitleIsATextbox`; JSE-46 | `text_truth.json` | yes |
| prefix/suffix | pytest `TestPrefixSuffix`; cscript TBG-05; TP-14a guard | `text_truth.json` | yes |
| twoway's text and colour | pytest `TestTheFixtureIsPinned`; cscript TBG-01 | `text_truth.json`; live export | yes |
| Served copy carries the names | pytest `TestTheServedCopy` | none | served |
| Measured line/split cases unchanged | pytest `test_textbox_multiline.py` | none | yes |
| Fixture committed and named | `test_fixtures_are_committed.py` | `text_truth.json` | n/a |

Acceptance criteria:
- **AC-13.1** Every test stub above passes; each regression stub failed at `91d97be` with the failure recorded in 13-01's commit message.
- **AC-13.2** `python3 -m pytest test/ -q` is green under both interpreters with no skip added; `test_textbox_grammar.cscript` and JSE-46 pass under Stata's Python.
- **AC-13.3** BUGS.md holds three closed entries naming their tests; dash.sthlp 455-458, 519-525, 2396-2417 updated; CHANGELOG "Results that change" lists the six changed pictures.
- **AC-13.4** No `dash:` warning is printed for any honoured spelling in either mode (Q22).

## Tasks

<task type="auto" id="13-01">
  <name>Write the failing tests for the section</name>
  <files>test/test_textbox_grammar.py (new), test/test_textbox_grammar.cscript (new), test/test_json_escaping.cscript</files>
  <action><![CDATA[
    Create `test/test_textbox_grammar.py` with the module docstring stating the three measured symptoms from GAPS2 B3, B6, B7 and every class and test named in "TDD test stubs", with exactly those names; import `_both_modes`/`_drawn` from `test_textbox_multiline` and `_lone_figure` from `test_dual_axis`; load `test/fixtures/text_truth.json` through a `truth()` fixture modelled on `test_axis_options.py:40-47` that calls `pytest.fail("section 13 task 13-02 must land first: test/fixtures/text_truth.json is missing")`, never skips. Assert drawn text with `fig.title.text`, `fig.xaxis[0].axis_label`, and for the second axis the `ContinuousAxis` in `fig.right`/`fig.above` whose `y_range_name`/`x_range_name` is `y2`/`x2`. Create `test/test_textbox_grammar.cscript` (`cscript "textbox grammar" adodir ".."`, `global dash_nobrowser 1`, the `c(python_exec)` guard, `do "cert_helpers.do"`, `quietly do "cert_svg.do"` -- after `cscript`, before any `cd`; it gates `c(python_exec)` and sets `dash_nobrowser` itself) with cases TBG-01..TBG-05 as the stubs describe, each displaying `TBG-0n PASS`; read dash's page with a `python:` block modelled on `test_json_escaping.cscript`'s `_jg_drawn` (1492) that lists `LinearAxis` models with their `y_range_name` and `axis_label`, and read the stored spec with `_dash_json_get_str` as `test_textbox_multiline.cscript:56-64` does. In `test_json_escaping.cscript` JSE-46 (1974-2011) change the expected `LinearAxis` count for `line 1\nline 2` from `1` to `2`, and add a `jg46l` command `dash (scatter mpg weight) (line price weight, yaxis(2)), ytitle("a" "b", axis(2)) name(jg46l)` whose right axis label `a\nb` is compared with `cert_svg_has_text` (`r(found)` for `a` and for `b`) on `twoway (scatter mpg weight) (line price weight, yaxis(2)), ytitle("a" "b", axis(2))` exported through `cert_svg_export`. Run `python3 -m pytest test/test_textbox_grammar.py -q` and the two cscripts from a scratch directory (`STATATMP=<dir>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do ...`) against the unmodified tree and paste the failure summary into the commit message; the fixture-pinned tests fail on the missing fixture until 13-02 and are re-run there.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q 2>&1 | tail -5` reports 0 passed and no collection error; `grep -c "c(red)" <pytest output>` is non-zero (the headline fails with the sub-option drawn as text, not with an exception); the TBG cscript log shows TBG-01 failing on a page holding `c(red)` and JSE-46 failing on the count `1`.]]></verify>
  <done>Every regression test for B3, B6 and B7 exists, collects, and fails against the unmodified tree for the reason each gap describes; no product file is changed.</done>
</task>

<task type="auto" id="13-02">
  <name>Record twoway's title truth into text_truth.json</name>
  <files>scripts/extract_text_truth.do (new), test/fixtures/text_truth.json (new)</files>
  <action><![CDATA[
    Write `scripts/extract_text_truth.do` as "Stata truth" specifies: the `*!` header (method, invocation, the backtick trap), `zp` with the sixth `control` argument stored in `ZA_CTL_<n>`, the 40 `title` probes in the order listed, a marked empty region `* ---- section 15: legend probes ----` after them, the export loop copied from `extract_axis_truth.do:392-428` without the `.gph` save (record `PROBE|id|grp|ds|rc|rcx|svg|ctl|shown`), and one trailing `python:` block that inserts `${ZA_REPO}/scripts` on `sys.path`, imports `svg_truth`, calls `svg_texts` and `svg_fills` per measured probe, normalises U+00A0 to a space, computes `added_texts`/`removed_texts`/`added_fills` against the control by `collections.Counter` difference keeping the probe's order, records `font_sizes`, and dumps `{"meta": {...}, "probes": {...}}` with `sort_keys=True`. Spell any backtick in the block as `\x60`; never call Stata from it. Run it from `/tmp/dash-s13` with `STATATMP=/tmp/dash-s13/tmp/` as shown, check the log ends `WROTE .../text_truth.json` with 40 measured probes (`t_colour_refused`, `t_style_refused` and possibly `t_axis3`/`t_axis2_no_layer` record `rc` 198 and no SVG; every other `rc` is 0), then `git add -f test/fixtures/text_truth.json`. Re-run `python3 -m pytest test/test_textbox_grammar.py -q` and record in the commit message which stubs now fail for their behavioural reason.
  ]]></action>
  <verify>`python3 -c "import json;d=json.load(open('test/fixtures/text_truth.json'));p=d['probes'];print(len(p), p['t_c_red']['added_texts'], p['t_c_red']['added_fills'], p['t_both_empty']['removed_texts'])"` prints 40, `['T']`, a list holding red, and the two default titles; `git ls-files test/fixtures/text_truth.json` lists it; `python3 -m pytest test/test_fixtures_are_committed.py -q` passes.</verify>
  <done>twoway's drawn text, colour and font size for every title, axis-title, `axis(2)`, empty-title, prefix/suffix and refused-word case is committed as `test/fixtures/text_truth.json`, produced by a script that names its method.</done>
</task>

<task type="auto" id="13-03">
  <name>Replace the sub-option table and canonicalise names</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    At `dash_render.py:2438-2445` replace `_TEXTBOX_SUBOPTS` with the `(full, minimum)` tuple of TR-13.1 (a comment citing `textbox_options.sthlp:41-77`, `title_options.sthlp:56-66`, `axis_title_options.sthlp:54-63`, and that `colour`/`style` are refused by twoway and so are left out), add `_textbox_canon(name)` (TR-13.1; lower-case the name; return the one full name whose minimum is a prefix of it and which it is a prefix of; `None` otherwise) and set `_TEXTBOX_SUBOPT_RE = re.compile(r",\s*(?=[A-Za-z_])")` with a comment that this is twoway's `_parse comma`. In `_parse_textbox_opt` (2614) keep `split_at`/`tail` as they are, store `opts[_textbox_canon(m2.group(1)) or m2.group(1).lower()] = ...`, and replace the three-flag loop with `for tok in _dash_by_tokens(tail.strip()): if "(" not in tok: nm = _textbox_canon(tok); if nm in ("span","box","nobox","bexpand","prefix","suffix"): opts[nm] = nm`. In `_textbox_color` (2597) read `opts.get("color", "")` only. Add `"_TEXTBOX_SUBOPTS"` to the constants list at 24326-24428 (a tuple of tuples writes as `%r`) and `"_textbox_canon"` to the function list at 24466-24687. Add `_textbox_canon` to `test/function_test_map.py` naming `test/test_textbox_grammar.py::TestTheTable::test_every_prefix`.
  </action>
  <verify><![CDATA[`python3 -c "import dash_render as d;print(d._textbox_canon('c'),d._textbox_canon('si'),d._textbox_canon('bex'),d._textbox_canon('colour'),d._textbox_canon('s'),d._parse_textbox_opt('\"T\", c(red) si(large) bex'))"` prints `color size bexpand None None ('T', {'color': 'red', 'size': 'large', 'bexpand': 'bexpand'})`; `python3 -m pytest test/test_textbox_grammar.py -q -k "TestTheTable or TestAbbreviationsAreSubOptions" test/test_textbox_multiline.py test/test_function_test_map.py -q 2>&1 | tail -3` is green.]]></verify>
  <done>Every legal spelling of every textbox sub-option splits off the text and reaches `_textbox_size`/`_textbox_color` under its full name, in both renderers; the 56 measured line and split cases still pass.</done>
</task>

<task type="auto" id="13-04">
  <name>Name the rest and honour prefix, suffix and axis</name>
  <files>dash_render.py, test/test_suboption_warnings.py, test/test_axis_options.py</files>
  <action>
    Set `_DASH_TEXTBOX_HONOURED = frozenset({"size", "color", "prefix", "suffix", "axis"})` (18858) and in `_dash_textbox` (18861-18878) compute `bad` as the tokens whose `_textbox_canon(_dash_subopt_name(t))` is not in the set, plus any `axis(#)` token whose argument stripped is not `1` or `2` or whose `option` is not one of `xtitle`, `ytitle`, `xtitle2`, `ytitle2`; report through `_dash_report_suboptions(option, bad, seen, key)` as today. In `_dash_axis_labels` (16003-16038) apply TR-13.7: read `raw`, `given = bool(str(raw or "").strip())`, take `opts` from `_dash_textbox`, and build the label from `given`, `prefix`, `suffix`. Extend `test/test_suboption_warnings.py` `SUBOPTIONS` and `TestTheHonouredOnesStayQuiet` with the rows listed under "TDD test stubs"; extend `test/test_axis_options.py::TestTitleTextFidelity` with `test_abbreviated_size_and_colour_are_applied` (`'T, si(large) c(red)'`) asserting against `truth()['probes']['t_size_color_abbr']`. Do not touch `_dash_add_secondary_axes` here (13-09).
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q -k "EverySpelling or Foreign or PrefixSuffix" test/test_suboption_warnings.py test/test_axis_options.py -q 2>&1 | tail -3` is green except the `test_second_axis_spelling` cases, which 13-09 closes; `python3 -c "import warnings,dash_render as d;warnings.simplefilter('error');print(d._dash_textbox('\"M\", si(large) c(red) prefix axis(1)','ytitle'))"` prints `('M', {...})` without raising.]]></verify>
  <done>Every sub-option not drawn is named once as written and every honoured one is silent, in both renderers; a lone `suffix`/`prefix` on an axis title adds its line after or before the default.</done>
</task>

<task type="auto" id="13-05">
  <name>Add the Python axis(2) title rewrite to both loaders</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    Immediately above `_dash_lone_second_axes` (1639) add `_dash_route_axis_titles(spec)` per TR-13.5: iterate `spec["graphs"]`, for each `graph_options` dict and each `side` in `("y", "x")`, `raw = go.get(f"{side}title")`; when `raw` is a string, `_, opts = _parse_textbox_opt(raw)`; if `opts.get("axis", "").strip() == "2"`, cut the raw value at `_textbox_split_point(raw)`, drop the token whose `_dash_subopt_name` is `axis` from `_dash_by_tokens(tail)`, rebuild `head + (", " + " ".join(rest) if rest else "")`, and if `f"{side}title2"` is absent set it to that and pop `f"{side}title"`, else pop `f"{side}title"` and `_dash_warn_once(("route", key, side), "dash: %stitle(..., axis(2)) and %stitle2() both given; %stitle2() is drawn" % (side, side, side))`; if `"1"`, keep the rebuilt value under `f"{side}title"`. Return a new spec, the caller's untouched; return a wrong-shaped spec as it came, as `_dash_lone_second_axes` does. Call it at 21030 (`self.master_spec = _dash_route_axis_titles(self.master_spec)`) and 24251 (`self.spec = ...`), each on the line BEFORE the `_dash_lone_second_axes` call. Add the name to the function copy list and to `test/function_test_map.py` naming `test/test_textbox_grammar.py::TestAxisTwoRouting::test_route_axis_titles_unit`.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q -k "TestAxisTwoRouting" 2>&1 | tail -3` passes every case (including the lone-axis case in both modes); `python3 -c "import dash_render as d;s={'graphs':[{'plots':[{'type':'scatter','options':{}}],'graph_options':{'ytitle':'\"P2\", size(large) axis(2)'}}]};print(d._dash_route_axis_titles(s)['graphs'][0]['graph_options'])"` prints `{'ytitle2': '"P2", size(large)'}`.]]></verify>
  <done>A spec carrying `ytitle("...", axis(2))` or `xtitle("...", axis(2))` is drawn with that title on the second axis by both loaders, before the lone-axis rewrite, with any other sub-options kept.</done>
</task>

<task type="auto" id="13-06">
  <name>Route axis(2) titles in Mata before the repeat merge</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    In `dash_parse.mata`, after `_dash_rep_split` (4727), add `string scalar _dash_route_axis2(string scalar opts)` per TR-13.6: `toks = _dash_rep_toks(opts, 0)`; for each token, `nm = strlower(_dash_rep_optname(tok))`; when `strlen(nm) >= 3` and (`substr("ytitle", 1, strlen(nm)) == nm` or `substr("xtitle", 1, strlen(nm)) == nm`) and the token has a value, split it with `_dash_rep_split(_dash_rep_value(tok), body, sub)`, walk `_dash_rep_toks(sub, 1)`, and for a word whose `strlower` starts with `axis(` and ends with `)` read the argument with `strtrim(substr(w, 6, strlen(w) - 6))`: `"2"` rewrites the token as `substr(nm, 1, 1) + "title2(" + body + (rest == "" ? "" : ", " + rest) + ")"`, `"1"` as `substr(nm, 1, 1) + "title(" + body + (rest == "" ? "" : ", " + rest) + ")"`; any other argument, and every other token, is kept as typed. Join with a blank and return. Document that `_dash_rep_merge` would otherwise fold both copies into one `ytitle`. In `dash.ado`, insert `mata: st_local("opts_raw", _dash_route_axis2(st_local("opts_raw")))` on the line before `_dash_parse_plot_opts , `macval(opts_raw)'` (3783) and `mata: st_local("gopts_raw", _dash_route_axis2(st_local("gopts_raw")))` before `_dash_parse_graph_opts , `macval(gopts_raw)'` (4498), with a comment naming the merge. Add `"_dash_route_axis2": ("test_textbox_grammar.cscript:TBG-03", "test_textbox_grammar.cscript:TBG-02")` under `"dash_parse.mata"` in `test/program_coverage_map.py`. Run the TBG cscript, JSE-46 and `test_twoway_option_parity.cscript` (TP-14a rows r15-r19 must still pass) from a scratch directory. If TBG-03 cannot be made to pass without weakening it, stop and report: the Python rewrite of 13-05 stays, the two-copy case is recorded as a residual in the B3 BUGS.md entry, and 13-10 marks it -- do not delete the case.
  ]]></action>
  <verify>The TBG cscript log shows `TBG-02 PASS` and `TBG-03 PASS` (the stored spec carries `ytitle` `"Left"` and `ytitle2` `"Right"` for `ytitle("Left") ytitle("Right", axis(2))`); `python3 -m pytest test/test_program_coverage_map.py -q` passes; `test_twoway_option_parity.cscript` still reports TP-14 PASS.</verify>
  <done>`ytitle("a") ytitle("b", axis(2))` reaches the spec as two options, `ytitle` and `ytitle2`, because `axis(2)` copies are routed before `_dash_rep_reduce`, the segment merge and the after-comma merge fold copies.</done>
</task>

<task type="auto" id="13-07">
  <name>Make empty text remove an axis title</name>
  <files>dash_render.py, test/test_dual_axis.py</files>
  <action>
    Confirm 13-04's `given` rule in `_dash_axis_labels` closes `xtitle("")`, `ytitle("")` and `xtitle("", size(large))`; add the same rule to `_dash_add_secondary_axes`'s title read (a raw `""` gives `''`, which is also what an absent option gives there, so only the naming path differs) and leave `_dash_lone_second_axes` 1692-1694 as it is, with a comment that a raw `""` is deliberately moved so `ytitle("", axis(2))` on a lone graph removes the one title. In `test/test_dual_axis.py::TestTheLoneAxisRewrite` add `test_an_empty_second_title_is_moved_and_removes_the_title` (both modes through `_lone_figure`: `{"ytitle2": '""'}` gives `''` on the left axis). Run `test/test_textbox_grammar.py -k TestEmptyTitles` and `test/test_dual_axis.py`.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py -q -k TestEmptyTitles test/test_dual_axis.py -q 2>&1 | tail -3` is green; the TBG cscript log shows `TBG-04 PASS`.]]></verify>
  <done>An axis title option given with empty text draws no title on that axis, in both modes and on the second axis, while an absent option keeps twoway's default.</done>
</task>

<task type="auto" id="13-08">
  <name>Flip the pinned tests that widen B3 and B6 coverage</name>
  <files>test/test_textbox_multiline.py, test/test_mode_parity.py</files>
  <action>
    In `test/test_textbox_multiline.py::TestParseTextboxOpt` add `test_abbreviations_are_the_same_sub_options` (`'"a", si(large) c(red)'` equals `'"a", size(large) color(red)'`) and in `TestTextboxSplitPoint` add `test_a_comma_before_any_word_splits` (`'"a", bogus(1)'` splits at 3; `'"a", 2 more'` and `'"a", "b"'` do not). In `test/test_mode_parity.py` `CORPUS` add three cases beside 1211: `title("T", c(red)) xtitle("W", si(large))`, `ytitle("Volume", axis(2))` on a y2 layer, and `xtitle("") ytitle("")`; each must pass the parity profile without an `ALLOWED` entry. Run both files.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_multiline.py test/test_mode_parity.py -q 2>&1 | tail -3` is green with the new cases collected (grep the `-v` output for their ids).]]></verify>
  <done>The parser's pinned tests cover abbreviations and the widened split, and the parity corpus proves both modes draw the new behaviours alike.</done>
</task>

<task type="auto" id="13-09">
  <name>Read the second axis's title as a textbox</name>
  <files>dash_render.py, test/test_dual_axis.py</files>
  <action>
    Change `_dash_add_secondary_axes` (16997-17030) to the signature and body of TR-13.8: `seen=None, key=""` parameters; `text, opts = _dash_textbox(graph_opts.get(f"{n}title2", ""), f"{n}title2", seen, key)`; `axis_label=text`; after `fig.add_layout(ax, side)` apply `_textbox_size`/`_textbox_color` to `ax.axis_label_text_font_size`/`ax.axis_label_text_color` when not `None`, with a comment that the saved renderer adds this axis after `_dash_style_axis_titles` and the template before it, which is why the styling lives here. Update the two call sites: 22096 `_dash_add_secondary_axes(fig, plots, graph_opts, _source_frame(source, self.df), _seen, _gkey)`; template 26207 `_dash_add_secondary_axes(fig, plots, go, g_df, _reported_subopts, gname)`. Extend `test/test_dual_axis.py::TestSecondaryAxisOptions::test_ytitle2_on_right_axis` to assert the label is exactly `Secondary Y` and add `test_ytitle2_lines_size_and_colour` (`'"a" "b", si(large) c(red)'`). Run `test/test_textbox_grammar.py`, `test/test_dual_axis.py`, `test/test_mode_parity.py -k yaxis`, then JSE-46 and the TBG cscript from a scratch directory.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_textbox_grammar.py test/test_dual_axis.py -q 2>&1 | tail -3` is green including `test_second_axis_spelling` and `TestSecondAxisTitleIsATextbox`; the JSE-46 log shows the `LinearAxis` count `2` and `jg46l` equal to twoway's texts; the served and saved `axis_label_text_font_size` of the y2 axis are equal in `test_mode_parity`'s y2 case.]]></verify>
  <done>`ytitle2()`/`xtitle2()` draw their lines without quote marks, sized and coloured by their sub-options and naming the rest, the same in both renderers whatever the order the axis is added.</done>
</task>

<task type="auto" id="13-10">
  <name>Close B3, B6 and B7 in the tracking documents</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action>
    Add three closed BUGS.md entries in the `- [x] Title:` form with File Names and Line Numbers / Description / Suggested fix / Resolution: B3 "Textbox sub-option abbreviations are drawn as title text" naming `test/test_textbox_grammar.py::TestAbbreviationsAreSubOptions::test_c_red_is_a_red_title`, `test/test_textbox_grammar.cscript` TBG-01..TBG-03 and, if 13-06 left one, the two-copy residual; B6 "xtitle("") and ytitle("") do not remove the axis title" naming `::TestEmptyTitles::test_empty_text_removes_the_title` and TBG-04; B7 "ytitle2()/xtitle2() draw their quote marks and ignore textbox grammar" naming `::TestSecondAxisTitleIsATextbox::test_text_lines_size_colour` and JSE-46. Update dash.sthlp: 519-525 say a sub-option under any of Stata's abbreviations is applied (`size()`, `color()`, `prefix`, `suffix`, `axis()`) or named, and a word that is not a textbox sub-option is named; 455-458 add that `xtitle("")`, `ytitle("")` and `ytitle("", axis(2))` remove the title and `prefix`/`suffix` add their lines; 2396-2399 replace "which dash does not read as the second axis's" with the sentence that `ytitle(, axis(2))` and `xtitle(, axis(2))` are read as the second axis's title while `ylabel(, axis(2))` and `yscale(, axis(2))` are still named; 2411 and 2417 make `ytitle2(tinfo)`/`xtitle2(tinfo)` with the textbox grammar. Grep `test/test_help_claims_*.cscript` and `test/test_help_examples.py` for the changed sentences and update any pin. Add to CHANGELOG "Results that change" one item per gap with command, old picture and new: `title("T", c(red))` (three lines, scheme colour → `T` in red), `ytitle("Volume", axis(2))` (left axis, three lines → right axis `Volume`), `xtitle("")` (variable label → no title), `ytitle2("P2")` / `"a" "b"` / `"P2", size(large)` (quotes, one line, verbatim → `P2`, two lines, sized). Run the full suite once, `python3 -m pytest test/ -q`, then the two cscripts, before committing; no AI references anywhere.
  </action>
  <verify><![CDATA[`python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py test/test_help_examples.py -q` passes; `grep -n 'c(red)\|axis(2)\|xtitle("")\|ytitle2' CHANGELOG.md` shows the four items under "Results that change"; `git log -3 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>B3, B6 and B7 are closed in BUGS.md naming their regression tests, the help describes the grammar dash now reads, and CHANGELOG records every changed picture.</done>
</task>

## Section completion criteria

- All 13-01 stubs pass in both modes; each failed at `91d97be` for its recorded reason.
- `test/fixtures/text_truth.json` is committed, named by two readers, and its `title` probes are pinned by `TestTheFixtureIsPinned`.
- `python3 -m pytest test/ -q` green under both interpreters; `test_textbox_grammar.cscript`, `test_json_escaping.cscript`, `test_twoway_option_parity.cscript`, `test_textbox_multiline.cscript` pass under Stata's Python with no skip.
- `_TEXTBOX_SUBOPTS`, `_textbox_canon`, `_dash_route_axis_titles` are in the served copy lists and `function_test_map.py`; `_dash_route_axis2` is in `program_coverage_map.py`.
- Three closed BUGS.md entries; dash.sthlp and CHANGELOG updated; no `dash:` note for any honoured spelling.

## Notes

- **Renderer order.** Saved: scheme 22037 → `_dash_figure_title`/`_dash_style_axis_titles` 22040-22041 → `_dash_add_secondary_axes` 22096. Template: scheme 26204 → `_dash_add_secondary_axes` 26207 → styling 26210-26211. Styling the second axis inside the function is what makes the order irrelevant; do not move the call sites.
- **Copy lists.** A tuple of tuples writes as `%r` (24447); a compiled regex through the `pattern`/`flags` branch. Forgetting `_TEXTBOX_SUBOPTS` in the constants list leaves the served `_textbox_canon` raising `NameError` at runtime -- `TestTheServedCopy` catches it, as does `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`.
- **The split widened on purpose.** Under the old regex `title(Sales, and more)` (unquoted) kept its comma; under `_parse comma` it is `Sales` with `and more` named, which is nearer twoway's r(198) than drawing it. Every quoted comma case (`TestCommaInsideTheUsersText`, `_MEASURED_SPLITS`) is inside a string or parentheses and unaffected.
- **Mata rewrite hazards.** Read `opts_raw` with `st_local`, never through a macro expansion; `"'` inside a title would end a compound quote. Test the rewrite with `title(`"'90s"')`-shaped values (JSE-42..49) to show nothing is expanded. `yti2(` has optname `yti2`, not a prefix of `ytitle`, so aliases are untouched. `_dash_rep_scan` will see `ytitle(` and `ytitle2(` as prefix-related spellings and put each to the parser alone; they bind to different keys and do not merge.
- **The lone-axis rewrite.** `_dash_route_axis_titles` must run first: after routing, a lone-axis(2) graph's `ytitle2` is moved into `ytitle` by `_dash_lone_second_axes` and drawn on the one left axis, which is twoway's picture (`t_ytitle_axis2_lone`).
- **Fixture exclude rule.** `.git/info/exclude` carries `*.json`; `git add -f`. `test_fixtures_are_committed.py` needs the file name `text_truth.json` to appear as a whole token in a test file or cscript.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; a run of cscript skips is then not a pass. Check `c(python_exec)` before trusting skips; at most three Stata runs at once.
- **Merge with section 15.** Section 15 appends `zp` lines in the marked region and regenerates the fixture. Merge 13 first, then 15's diff with `patch -p1`, then run the extract script once on the merged tree and `git add -f` the regenerated fixture.
- **Unquoted suffix.** `_dash_rep_merge` joins `title(A) title(B, suffix)` as `A B`, which TP-14a r18 measured identical to twoway's SVG; the quoted form `title("A") title("B", suffix)` joins as `"A" "B"`, two lines. `t_title_two_suffix` pins whichever twoway draws; if it disagrees with the merge, record it in the B3 entry rather than changing the merge here.
- **Line numbers drift** by the lines each task adds (13-03 about +30 at 2438; 13-05 about +45 at 1639). Anchors are also given as symbols; the symbol is authoritative.
