# Section 40: Marker symbols and line patterns

> Part of: WP-31 · GAPS3 rows: E1, E2, E12 · Risk: yellow · Batch: 13 · Depends on: 01 · Blocks: 44 · Tasks: 4, 2 commits · Case-id prefix: U40

## Overview

**What is wrong today.** GAPS3 E1 (GAPS3.md:180): "Symbols: `arrow`, `arrowf`, `A`, `a`, `|` refused (noted, scheme symbol drawn); `pipe` drawn as a horizontal dash (twoway's is vertical); `point`/`p` at full 8 px; `V` as a filled inverted triangle; lower-case shorthands `o d s t x v` at full size; `star asterisk hexagon dot` accepted where twoway refuses." GAPS3 E2 (:181): "Line patterns: formula strings (`-.`, `--..`, `_`, `#`) refused in options and schemes (solid drawn); `-_-` drawn as dash_dot; dot geometry `[2,4]` vs Stata `.1 .7`, shortdash `[4,4]` vs `.8 .7`, tight_dot `[1,2]` vs `.1 .4`, vshortdash `[3,3]` vs `.5 .7`; `mlpattern()` pending (never read)." GAPS3 E12 (:191, NEW): "Case folding: `translate_msymbol` and `translate_lpattern` lower-case names (`CIRCLE`, `Dash` drawn); Stata style names are case-sensitive (measured for anglestyle). `_INTENSITY["max"]` 9999.99 vs the style file's 999999 (no visible effect)."

At `6370ca4` `OptionTranslator._MARKER_MAP` (dash_render.py:6932-6987) maps 50 names to Bokeh markers; `translate_msymbol` (:7536-7559) tries the name then its lower case; `_SMALL_SYMBOL_FACTOR` (:6923-6930) is keyed by full `sm*` names only ("so the one- and two-letter shorthands keep their size (P2.11)"). `_LPATTERN_MAP` (:7253-7281) holds pixel arrays invented for a medium line (`"dash": [8, 4]`, `"dot": [2, 4]`); `translate_lpattern` (:7633-7651) lower-cases and raises for a formula; `SchemeParser._lpattern` (:9786-9803) catches that and warns "falling back to solid". `mlpattern` is declared and parked on the pending list (dash.ado:1343). Stata's own pattern decoder (`B/l/linepattern.class` `_DecodePat`, :144-212) gives exact numbers for every formula character and the 17 `style/linepattern-*.style` files give every named pattern's numbers (`dash` "2 1", `dot` ".1 .7", `shortdash` ".8 .7", `tight_dot` ".1 .4", `vshortdash` ".5 .7"); those numbers are in units of the pen width (`gdi linedash`, compiled), which U40's probe measures from twoway's SVG.

**After this section**, in both modes: every one of Stata's 28 `style/symbol-*.style` symbols and the synonyms of `symbolstyle.sthlp` draws (arrowheads, the vertical pipe, the one-pixel point, hollow `V`, the small shorthands at the small factor); a name twoway does not know (`star`, `asterisk`, `hexagon`, `dot`, `CIRCLE`) gets twoway's "not found" note and the scheme's symbol, as the measured probe says; every named pattern draws the geometry of its style file scaled by the line's own width, every formula string is decoded as `_DecodePat` decodes it, and `mlpattern()` dashes a marker's outline. Names stay case-sensitive where twoway's are (branch on U40-07). `_INTENSITY["max"]` is left at 9999.99 (999999 percent is 9999.99 as a fraction; the comment is corrected, no behaviour changes).

**Why these rows share a section.** E1, E2 and E12 are the three translators of `OptionTranslator` (symbol, pattern, case folding) and their one scheme reader; S44 (batch 15) builds its style-file resolver on top of `translate_lpattern(value, width_px)` and `symbol_traits`, which is why S40 lands two batches earlier (index: S40 blocks S44).

**Test order and commit rule (BRIEF).** Two cycles, one commit per row: `(WP-31 E1)` for the symbols (E12's symbol half rides in it) and `(WP-31 E2)` for the patterns (E12's pattern half rides in it). 40-01 writes the extractor and the red tests for both rows and never commits; 40-02 fixes E1 and commits; 40-03 fixes E2 (the red E2 tests written in 40-01 are run against the tree E1's commit leaves) and commits; 40-04 is the hand-back check. No test-only commit exists.

### Section decisions (binding on the executor)

- **D-40a. Arrowheads are Bokeh `triangle` markers, hollow for `arrow`/`a`, filled for `arrowf`/`A`, at the small-symbol factor the probe measures.** Bokeh's marker set has no open arrowhead. U40-01 exports `msymbol(arrow)` and `msymbol(arrowf)` SVGs and records each marker's path: filled or `fill="none"`, vertex count, bounding-box aspect and the apex direction. If the measured `arrow` is two strokes meeting at the apex (no base edge), dash draws the hollow triangle and the help documents the base edge as the measured difference (M17); if it is a closed polygon, the triangle is exact. The apex points up (Stata's `_gr_arrowhead` default orientation is along +y for a symbol; the probe confirms) so no base angle is needed.
- **D-40b. `pipe` and `|` are Bokeh's `dash` marker rotated a quarter turn.** A class dict `_SYMBOL_BASE_ANGLE = {"pipe": math.pi / 2, "|": math.pi / 2}` is read by `_apply_marker_opts` after the symbol is set and before `msangle()` is added, so `msymbol(pipe) msangle(45)` is the vertical dash turned a further 45 degrees, as twoway turns it.
- **D-40c. `point` and `p` are a fixed one-pixel `circle` with no outline**, whatever `msize()` says: `_SYMBOL_FIXED_PX = {"point": 1.0, "p": 1.0}` is read where the small-symbol factor is read (the two sites :13485 and :14848). U40-01 measures the point's drawn radius at the default and under `msize(large)`; if twoway scales it, the dict is dropped and `point` takes the factor the probe gives instead (the task branches).
- **D-40d. `V` is `v`'s symbol.** Stata ships one resource for both (`style/symbol-V.style` and `symbol-v.style`, both `label resource "SYMBOL-V"`), so `V` draws as `v` draws: `inverted_triangle`, filled, at the small factor the probe gives for `v`/`smv` (today 1.0). The GAPS3 words "V as a filled inverted triangle" are measured; if the probe shows `V` hollow, `"V"` joins `_HOLLOW_SYMBOLS` (branch).
- **D-40e. The lower-case shorthands take the small factors.** `o d s t` and their hollow forms `oh dh sh th` are `smcircle`, `smdiamond`, `smsquare`, `smtriangle` and their hollows in `symbolstyle.sthlp`'s synonym table, so they join `_SMALL_SYMBOL_FACTOR` with the same values (`sqrt(0.5)`, `0.75`); `x`/`v` stay 1.0 (P1.4a measured smx and smv drawn as x and v). The "keyed by full name only" comment (:6919-6922) is replaced.
- **D-40f. The symbol names twoway does not know leave the map.** `star`, `asterisk`, `hexagon`, `hexagon_hollow` and `dot` are deleted from `_MARKER_MAP` so they reach `_dash_style_note` ("marker symbol") and the scheme's symbol is drawn, which is what U40-05 measures twoway doing (a note, rc 0). If twoway instead returns r(198) for any of them, that name is refused in dash.ado's `_dash_option_rules` with the measured words (branch; a CHANGELOG Changed-behaviour line is then added under M5).
- **D-40g. Patterns are Stata numbers scaled by the pen width at apply time.** `_LPATTERN_MAP` is rewritten to hold the 17 style files' numbers as floats (`"dash": [2.0, 1.0]`, `"dot": [0.1, 0.7]`, ...); `translate_lpattern(value, width_px=None)` returns `[round(v * unit, 3) for v in numbers]` where `unit = max(width_px, _LPATTERN_MIN_WIDTH_PX) * _LPATTERN_UNIT_PER_WIDTH`, both constants written from the fixture's `unit_per_width` and `min_width_px` keys (U40-01 measures `stroke-dasharray / stroke-width` of `lpattern(dash)` at `lwidth(medium)`, `lwidth(thick)` and `lwidth(vvthin)`; the hypothesis is 1.0 and the medium width). `width_px=None` means the medium line (`_LWIDTH_RS["medium"] * PT_PER_RS * PX_PER_PT` = 1.152 px). Every caller passes the glyph's own `line_width` (TR-40.9).
- **D-40h. Formulas follow `_DecodePat` character for character.** `l` adds a 4.6 line (joined to a preceding line); `_` adds a .45 space, a 3.70 dash, a .45 space; `-` .3, 1.4, .3; `.` .3, .1, .3; `#` a .45 space; adjacent spaces merge; a leading space is carried to the tail; a text of `l`s alone is solid (`setstyle`, linepattern.class:73-75); any other character makes the text invalid. An invalid formula in an option is noted and solid is drawn (twoway: `"<text>, invalid line pattern"` r(198) -- U40-08 measures; if r(198), dash.ado's rule for `lpattern` refuses it with those words, branch). The old special key `"-_-"` is deleted: the decoder gives dash, long dash, dash.
- **D-40i. `mlpattern()` is a per-y stylelist key** written through `_dash_stylelist_pick`, read by `_apply_marker_opts` onto `glyph.line_dash` with the marker's own `line_width`.
- **D-40j. Case folding follows U40-07's measurement.** If twoway notes `msymbol(CIRCLE)` and `lpattern(Dash)` as not found, the `.lower()` fallbacks at :7550-7553 and :7645 are removed and the `_SMALL_SYMBOL_FACTOR`/`_HOLLOW_SYMBOLS` reads use the typed key only; if twoway draws them, the fallbacks stay and the test pins that. Scheme files are read as typed either way (Stata's scheme values are lower-case).

## Risk: [yellow] -- every marker and dashed line in every scheme changes geometry, and six callers of `translate_lpattern` gain a width argument

**Why.** `_LPATTERN_MAP`'s values change meaning (pixels to pen-width units), so every pinned dash array in the suite moves; the symbol map loses five names and gains eight; the scheme reader's warning path changes.

**Risk factors.**
1. Pinned dash arrays: test_scheme_consumption.py `TestLinePatternFollowsStatasOwnChain` (:977), test_server_scheme.py `test_an_explicit_lpattern_still_wins`, test_glyphs.py and test_option_validation.py cases asserting `[8, 4]`-form lists.
2. A caller of `translate_lpattern` left without a width draws a medium-width pattern on a thick line (visible but not red).
3. The unit per width is compiled (`gdi linedash`); a wrong hypothesis would scale every pattern.
4. Removing `star`/`hexagon` from the map makes `mono` schemes that declare them unparseable? No: the shipped schemes declare `smdiamond`/`smtriangle` (comment at :6968-6972), which stay; U40 greps the 26 `dash-*.scheme` files for every `symbol ` value before deleting a key.
5. `_apply_marker_opts` is one of the four appliers (R12): S40 is batch 13's only editor of it (S38 edits reference lines, S39 tabs/legend edges).

**Mitigation.** 1: 40-01 lists every red node by running the four files and flips them in 40-03 with the reason "a pattern is Stata's numbers times the pen width (E2)". 2: `test_every_translate_lpattern_call_passes_a_width` reads dash_render.py's source for `translate_lpattern(` calls and asserts each has a second argument. 3: the fixture carries three widths; the test asserts the drawn array at each equals the fixture's measured dasharray within 0.05 px. 4: `test_no_shipped_scheme_names_a_deleted_symbol`. 5: index owner table.

## Dependencies

- **Depends on: 01** (tracking foundation: BUGS entries E1/E2/E12 open, CHANGELOG markers, GAPS3 Tracked lines, `test_wp31_truth.cscript` block 70).
- **Blocks: 44.** S44's resolver reads `linestyle-*.style` `pattern` values through `translate_lpattern(value, width_px)` and `markerstyle-*.style` symbols through `symbol_traits`; both signatures are fixed here.
- **Parallel batch: 13**, merge order S38, S39, S40. **Can run with S38 and S39**: neither edits `OptionTranslator`, `_apply_marker_opts`, `_apply_line_opts`, `SchemeParser._lpattern*` or dash.ado's plot parser.

## Evidence

All anchors at `6370ca4` (dash_render.py 52,280 lines; dash.ado 11,039; dash_parse.mata 9,789).

### The symbol map and its readers

dash_render.py:6932-6987 (`_MARKER_MAP`): `"pipe": "dash"` (:6962), `"point": "circle"` (:6968), `"star": "star"`, `"asterisk": "asterisk"`, `"hexagon": "hex"`, `"hexagon_hollow": "hex"`, `"dot": "dot"` (:6964-6969), `"v": "inverted_triangle"`, `"smv": "inverted_triangle"` (:6984-6985); no `arrow`, `arrowf`, `A`, `a`, `|`, `V`. `_SMALL_SYMBOL_FACTOR` (:6923-6930) keys: `smcircle smcircle_hollow smdiamond smdiamond_hollow smsquare smsquare_hollow smplus smtriangle smtriangle_hollow smx smv`. `_HOLLOW_SYMBOLS` (:6907-6912). `translate_msymbol` (:7536-7559):

```python
7550        result = (
7551            OptionTranslator._MARKER_MAP.get(v)
7552            or OptionTranslator._MARKER_MAP.get(v.lower())
7553        )
```

`symbol_traits` (:7562-7574) returns `(marker, hollow, factor)` with `fac.get(key, fac.get(low, 1.0))`. Readers: `_apply_marker_opts` msymbol branch (:13347-13353, `_dash_style_note("msymbol", ..., "marker symbol")` on ValueError), the hollow/factor read (:13480-13489), `msangle` (:13463-13471, `glyph.angle = radians`), the scheme cycle `default_symbol_traits` (:10916, :11083) and the size path (:14848-14851). The served app copies the class whole (R2: no copy-list entry).

### The pattern map and its readers

`_LPATTERN_MAP` (:7253-7281): `"dash": [8, 4]`, `"-": [8, 4]`, `"dot": [2, 4]`, `".": [2, 4]`, `"dash_dot": [8, 4, 2, 4]`, `"-_-": [8, 4, 2, 4]`, `"shortdash": [4, 4]`, `"vshortdash": [3, 3]`, `"tight_dot": [1, 2]`, `"blank": [0, 100]`. `translate_lpattern` (:7633-7651) `v = value.strip().lower()`. Callers (grep `translate_lpattern(`): :6602 (`_dash_region_spec`'s line look), :9795 (`SchemeParser._lpattern`), :11253 (style bundle line pattern), :12749 (`_style_restyle` keys `lpattern`/`alpattern`), :13230 (`_apply_line_opts`), :30857 (`_dash_apply_scale_look`). `_lpattern_chain` (:9805-9830) is called at :10307, :10320 (p# line and area chains), :10701, :10718, :10756.

### Stata's rule

- `B/l/linepatternstyle.sthlp:38-46, 119-134`: a formula is any combination of `_` (long dash), `-` (medium dash), `.` (short dash, "almost a dot"), `#` (blank), in double quotes.
- `B/l/linepattern.class:144-212` `_DecodePat`: `l` -> `_add_line 4.6`; `_` -> `_add_space .45`, `3.70`, `_add_space .45`; `-` -> `.3`, `1.4`, `.3`; `.` -> `.3`, `.1`, `.3`; `#` -> `_add_space .45`; any other character -> invalid. `_add_space` (:215-228) merges into a preceding space (`adding`) and defers a leading space to the tail (`tailsp`); `_add_line` (:230-241) joins to a preceding line. `setstyle` (:62-109): a numlist is taken as is; a text of `l`s is solid; a scheme value or a typed value made only of `l_-.# ` is decoded; an invalid one prints `"<style> , invalid line pattern"` r(198).
- The 17 `B/style/linepattern-*.style` numbers: blank "0 10"; dash "2 1"; dash_3dot "2 .9 .1 .9 .1 .9 .1 .9"; dash_dot "2 .9 .1 .9"; dash_dot_dot "2 .9 .1 .9 .1 .9"; dot ".1 .7"; longdash "4 1"; longdash_3dot "4 1 .1 1 .1 1 .1 1"; longdash_dot "4 1 .1 1"; longdash_dot_dot "4 1 .1 1 .1 1"; longdash_shortdash "4 1 .8 1 .8 1 .8"; shortdash ".8 .7"; shortdash_dot ".8 .8 .1 .8"; shortdash_dot_dot ".8 .8 .1 .8 .1 .8"; solid ""; tight_dot ".1 .4"; vshortdash ".5 .7". (`shortdot` has no style file: its map entry is deleted; `translate_lpattern("shortdot")` then notes.)
- Symbols: the 28 `B/style/symbol-*.style` files are `arrow arrowf circle circle_hollow diamond diamond_hollow lgx none pipe plus point smcircle smcircle_hollow smdiamond smdiamond_hollow smplus smsquare smsquare_hollow smtriangle smtriangle_hollow smv smx square square_hollow triangle triangle_hollow v x`, plus `V` (same resource as `v`). Synonyms (`B/s/symbolstyle.sthlp:20-70`): `O D S T + X A a |` for `circle diamond square triangle plus x arrowf arrow pipe`, `o d s t x v` for `smcircle smdiamond smsquare smtriangle smx smv`, `Oh Dh Sh Th oh dh sh th` for the hollow forms, `p` for `point`, `i` for `none`. Shapes are compiled (research/stata-ground-truth.md §6: "Symbols `arrow`/`arrowf` exist only as resource names ... needs measurement").
- Case: Stata's style lookup is case-sensitive (`_style_kind` docstring :11108-11110, measured for anglestyle); GAPS3 E12 asks for the symbol and pattern measurement.

### Tests that pin today's behaviour (to flip, never delete)

- test/test_scheme_consumption.py::TestLinePatternFollowsStatasOwnChain (every node asserting a literal pixel list).
- test/test_server_scheme.py::test_an_explicit_lpattern_still_wins.
- test/test_option_validation.py::TestTheDefaultIsWhatTheSchemeGives (nodes naming `star`/`hexagon`), ::TestAnUnknownStyleNameIsNamedOnceInBothModes (if a node uses `msymbol(hexagon)` as a KNOWN name).
- test/test_glyphs.py nodes asserting `line_dash == [8, 4]` or `[2, 4]`; test/test_markers*.py nodes asserting `pipe` draws `dash` with angle 0 or `point` size 8.
- test/test_unsupported_report_is_true.py: `mlpattern` moves from `PLOT_VALUES` to `LIVE_VALUES`, counts at :725-726 move with a `# old -> new: E2 mlpattern drawn` comment; test_help_conformance.py::TestTheUnsupportedSectionIsTrue follows the help edit.

40-01 runs `python3 -m pytest test/test_scheme_consumption.py test/test_server_scheme.py test/test_option_validation.py test/test_glyphs.py test/test_unsupported_report_is_true.py -q -n0 -p no:cacheprovider` on a scratch copy carrying the fix to list the exact nodes (`<scratch>/s40/40-flips.txt`).

## User stories

- US-40.1 As a Stata user, I want `msymbol(arrow)`, `msymbol(A)`, `msymbol(|)` and `msymbol(pipe)` to draw the arrowhead and the vertical bar twoway draws, so that my do-file's markers look the same.
- US-40.2 As a Stata user, I want `msymbol(p)` to be a dot and `msymbol(o d s t)` small, so that dense scatters read as they do in twoway.
- US-40.3 As a Stata user, I want `lpattern("-.")`, `lpattern("_")` and a scheme's `linepattern p1line "--.."` to draw those formulas, and `lpattern(dot)` on a thick line to have thick dots, so that line styles are twoway's.
- US-40.4 As a Stata user, I want `mlpattern(dash)` to dash my markers' outlines, and a non-Stata symbol name to get twoway's note rather than a drawing twoway would not make.
- US-40.5 As a maintainer, I want the style-file resolver (S44) to read pattern and symbol names through one translator each.

## Business requirements

- BR-40.1 Every name of Stata's symbol table and synonym list draws a marker; `pipe`/`|` is vertical; `point`/`p` is one pixel; `arrow`/`a` is hollow and `arrowf`/`A` filled; `V` equals `v`; `o d s t oh dh sh th` are small.
- BR-40.2 A symbol or pattern name twoway does not know is handled as twoway handles it (note and default, or refusal), per the measured probe; the user's text is never echoed beyond `_dash_display`'s 80 printable characters.
- BR-40.3 Every named pattern's on/off lengths are its style file's numbers times the pen width; a formula is decoded as Stata decodes it; a dashed thick line has longer dashes than a dashed thin line.
- BR-40.4 `mlpattern()` is drawn on marker outlines and leaves the note, the help's Unsupported list and TWOWAY_COVERAGE_AUDIT.md in the same commit.
- BR-40.5 Saved page and served app draw the same marker, angle, size and dash array for the same spec, before and after a filter move.
- BR-40.6 Nothing is printed when the option is honoured (Q36).

## Technical requirements

- TR-40.1 `_MARKER_MAP` (:6932-6987): add `"arrow": "triangle"`, `"a": "triangle"`, `"arrowf": "triangle"`, `"A": "triangle"`, `"pipe": "dash"` (kept), `"|": "dash"`, `"V": "inverted_triangle"`, `"lgx": "x"` (kept); delete `"star"`, `"asterisk"`, `"hexagon"`, `"hexagon_hollow"`, `"dot"` (D-40f). Add `"arrow"`, `"a"` to `_HOLLOW_SYMBOLS` (:6907-6912) and `"hexagon_hollow"` out of it.
- TR-40.2 `_SMALL_SYMBOL_FACTOR` (:6923-6930): add `"o": math.sqrt(0.5), "oh": math.sqrt(0.5), "d": math.sqrt(0.5), "dh": math.sqrt(0.5), "s": math.sqrt(0.5), "sh": math.sqrt(0.5), "t": 0.75, "th": 0.75`, and `"arrow"`, `"a"`, `"arrowf"`, `"A"` at the factor the fixture's `arrow_factor`/`arrowf_factor` give (rounded to 3 places). Replace the comment :6919-6922 with: `# The one- and two-letter shorthands are the sm* symbols (symbolstyle.sthlp), so they take the same factors (WP-31 E1).`
- TR-40.3 New class dicts after `_SMALL_SYMBOL_FACTOR`: `_SYMBOL_BASE_ANGLE: dict = {"pipe": math.pi / 2, "|": math.pi / 2}` and `_SYMBOL_FIXED_PX: dict = {"point": 1.0, "p": 1.0}` (D-40b, D-40c; both class members, copied with the class).
- TR-40.4 `_apply_marker_opts` msymbol branch (:13347-13353): after `glyph.marker = ...` add
  ```python
  _ba = OptionTranslator._SYMBOL_BASE_ANGLE.get(str(options["msymbol"]).strip())
  if _ba is not None and hasattr(glyph, "angle"):
      glyph.angle = _ba
  ```
  and in the msangle branch (:13465-13471) replace the assignment with `glyph.angle = float(getattr(glyph, "angle", 0.0) or 0.0) + math.radians(angle_deg)` so the base angle is kept. The scheme-cycle symbol path (:11083, `default_symbol_traits`) applies the same base angle for a scheme `symbol p# pipe`.
- TR-40.5 The two factor reads (:13485 and :14848-14851): after the factor is known, `if _sym_raw.strip() in OptionTranslator._SYMBOL_FIXED_PX: size = OptionTranslator._SYMBOL_FIXED_PX[...]; line_width = 0` on the marker glyph (size in px, outline off), skipping the `msize()` multiplication.
- TR-40.6 `translate_msymbol` (:7536-7559) and `symbol_traits` (:7562-7574): per D-40j, either delete the `.lower()` fallback (`v.lower()` at :7552, `low` at :7571-7574) or keep it; the docstring states the measured rule and cites `test/fixtures/symbol_pattern_truth.json`.
- TR-40.7 `_LPATTERN_MAP` (:7253-7281): values become the style files' float lists (Evidence); keys: the 17 file names plus `"l"` and `"solid"` as `[]` and `"blank"`/`"b"` as `[0.0, 10.0]`; delete `"-"`, `"."`, `"-_-"`, `"shortdot"` (formulas and the non-file name). Two new class constants after it: `_LPATTERN_UNIT_PER_WIDTH: float = <fixture unit_per_width>` and `_LPATTERN_MIN_WIDTH_PX: float = <fixture min_width_px>`, each with a comment naming the fixture key and the probe date.
- TR-40.8 New staticmethod `OptionTranslator.lpattern_formula(text) -> "list[float] | None"` directly above `translate_lpattern`, the port of `_DecodePat` (D-40h): returns `[]` for a text of `l`s, None for any character outside `l_-.# `, else the number list (at most 2 × len(text) + 1 entries; input bounded at 200 characters, longer is None). Pure arithmetic, no regex on user text beyond `fullmatch(r"[l_\-.# ]{1,200}")`.
- TR-40.9 `translate_lpattern(value, width_px=None)` (:7633): strip; if the key is in `_LPATTERN_MAP` take its numbers; else if `lpattern_formula` returns a list take it; else raise ValueError (the note path). Then `unit = max(float(width_px) if width_px is not None else T._LWIDTH_RS["medium"] * T.PT_PER_RS * T.PX_PER_PT, T._LPATTERN_MIN_WIDTH_PX) * T._LPATTERN_UNIT_PER_WIDTH`; return `[round(v * unit, 3) for v in numbers]` (`[]` stays `[]`). Case per D-40j. Every caller passes the glyph's width: :6602 `width_px=st.get("line_width")`, :11253 the bundle's `line_width`, :12749 `getattr(r.glyph, "line_width", None)`, :13230 `glyph.line_width` (after `lwidth()` has been applied: move the lpattern block below the lwidth block), :30857 the look's resolved width.
- TR-40.10 `SchemeParser._lpattern(key, width_px=None)` and `_lpattern_chain(keys, width_px=None)` (:9786, :9805) pass `width_px` through; the p# chain calls at :10307 and :10320 pass the width the same bundle computes (`plot_line_width`); :10395, :10597-10598, :10701, :10718, :10756 pass their own width keys (`xyline`, `major_grid`, `minor_grid`, `ci`, `p#other` widths already read beside them). The warning text at :9797-9801 becomes "is not a Stata pattern name or formula; falling back to solid".
- TR-40.11 `mlpattern()`: dash.ado -- delete :1343; add `mlpattern` to `_dash_stylelist_keys()` (dash_parse.mata:5285, after `mlwidth`) and to `_dash_plot_opts_to_json`'s key list (dash.ado:4441-4458, after `mlwidth`); it is already declared (`MLPattern(string asis)`) and sreturned. dash_render.py `_apply_marker_opts`: after the `mlwidth` branch add
  ```python
  if "mlpattern" in options:
      try:
          glyph.line_dash = self.tr.translate_lpattern(
              options["mlpattern"], getattr(glyph, "line_width", None))
      except ValueError:
          _dash_style_note("mlpattern", options["mlpattern"], "line pattern")
      except AttributeError:
          pass
  ```
- TR-40.12 Both renderers: all edits are `OptionTranslator`/`SchemeParser`/`GlyphMapper` members (copied by source); no copy-list entry. `test/function_test_map.py`: add `"OptionTranslator.lpattern_formula": "test/test_symbol_pattern.py::TestFormulas::test_decodepat_table"`. No new Stata program.
- TR-40.13 Help (R3, S40's paragraphs): dash.sthlp:1051-1053 (the "Colours (but for a comma), msymbol(), lpattern()" sentence: add "a symbol or pattern name twoway does not know gets twoway's note"), :4624-4626 (symbol cycle paragraph: list the arrowheads, pipe, point and shorthands), :3984-3987 (`lpattern()`: "a name or a formula in double quotes, `"-."`, scaled by the line's width"), delete :5029-5033 (the `mlpattern` Unsupported entry) and the example :4978-4979 (replace `mlpattern(dash)` with `mlabwidth(2)` so the example still shows a note). TWOWAY_COVERAGE_AUDIT.md:112 gains `[WP-31 E1/E2: corrected -- every Stata symbol drawn; mlpattern() drawn]`; :169 drops `mlpattern`.


### Reference table TR-40.A: the symbol map after S40 (every row exact; `fac` = `_SMALL_SYMBOL_FACTOR`, `hollow` = `_HOLLOW_SYMBOLS`, `angle` = `_SYMBOL_BASE_ANGLE`, `px` = `_SYMBOL_FIXED_PX`)

| Stata name(s) | Bokeh marker | hollow | fac | angle | px |
|---|---|---|---|---|---|
| circle, O | circle | no | 1.0 | -- | -- |
| circle_hollow, Oh | circle | yes | 1.0 | -- | -- |
| smcircle, o | circle | no | sqrt(0.5) | -- | -- |
| smcircle_hollow, oh | circle | yes | sqrt(0.5) | -- | -- |
| diamond, D | diamond | no | 1.0 | -- | -- |
| diamond_hollow, Dh | diamond | yes | 1.0 | -- | -- |
| smdiamond, d | diamond | no | sqrt(0.5) | -- | -- |
| smdiamond_hollow, dh | diamond | yes | sqrt(0.5) | -- | -- |
| square, S | square | no | 1.0 | -- | -- |
| square_hollow, Sh | square | yes | 1.0 | -- | -- |
| smsquare, s | square | no | sqrt(0.5) | -- | -- |
| smsquare_hollow, sh | square | yes | sqrt(0.5) | -- | -- |
| triangle, T | triangle | no | 1.0 | -- | -- |
| triangle_hollow, Th | triangle | yes | 1.0 | -- | -- |
| smtriangle, t | triangle | no | 0.75 | -- | -- |
| smtriangle_hollow, th | triangle | yes | 0.75 | -- | -- |
| plus, + | plus | no | 1.0 | -- | -- |
| smplus | plus | no | sqrt(0.5) | -- | -- |
| x, X | x | no | 1.0 | -- | -- |
| smx, lgx | x | no | 1.0 (smx), 1.0 (lgx: measured U40) | -- | -- |
| v, V, smv | inverted_triangle | no (V per D-40d) | 1.0 | -- | -- |
| arrow, a | triangle | yes | fixture `sym.arrow.factor` | -- | -- |
| arrowf, A | triangle | no | fixture `sym.arrowf.factor` | -- | -- |
| pipe, \| | dash | no | 1.0 | pi/2 | -- |
| point, p | circle | no | -- | -- | 1.0 (D-40c) |
| none, i, invisible | circle (alpha 0 via `_INVISIBLE_SYMBOLS`) | -- | -- | -- | -- |
| star, asterisk, hexagon, hexagon_hollow, dot, CIRCLE (and every other text) | ValueError -> `_dash_style_note("msymbol", value, "marker symbol")`, the scheme's symbol drawn | | | | |

`lgx` ("large x") has a style file but no synonym; its factor is measured by adding `lgx` to the probe's symbol list (today 1.0).

### Reference table TR-40.B: `_LPATTERN_MAP` after S40 and the worked formulas

Values are Stata's numbers (pen-width units, D-40g). At the medium width (1.152 px, hypothesis `unit_per_width` = 1) `dash` is `[2.304, 1.152]` px -- the fixture decides the unit.

| key | numbers | | key | numbers |
|---|---|---|---|---|
| solid, l | [] | | longdash_3dot | [4, 1, .1, 1, .1, 1, .1, 1] |
| blank, b | [0, 10] | | longdash_dot | [4, 1, .1, 1] |
| dash | [2, 1] | | longdash_dot_dot | [4, 1, .1, 1, .1, 1] |
| dash_3dot | [2, .9, .1, .9, .1, .9, .1, .9] | | longdash_shortdash | [4, 1, .8, 1, .8, 1, .8] |
| dash_dot | [2, .9, .1, .9] | | shortdash | [.8, .7] |
| dash_dot_dot | [2, .9, .1, .9, .1, .9] | | shortdash_dot | [.8, .8, .1, .8] |
| dot | [.1, .7] | | shortdash_dot_dot | [.8, .8, .1, .8, .1, .8] |
| longdash | [4, 1] | | tight_dot | [.1, .4] |
| vshortdash | [.5, .7] | | (deleted: `-`, `.`, `-_-`, `shortdot`) | |

`lpattern_formula` worked by hand from `_DecodePat` (the test `TestFormulas::test_decodepat_table` pins these against the fixture's dasharray / unit):

| formula | steps | numbers |
|---|---|---|
| `"-."` | `-`: leading .3 deferred (tail .3), 1.4, .3; `.`: .3 merges -> .6, .1, .3; tail +.3 -> .6 | [1.4, .6, .1, .6] |
| `"_"` | leading .45 deferred; 3.70; .45; tail +.45 -> .9 | [3.70, .9] |
| `"--.."` | 1.4, .6, 1.4, .6, .1, .6, .1, (.3 + tail .3) | [1.4, .6, 1.4, .6, .1, .6, .1, .6] |
| `"-_-"` | 1.4, (.3+.45) .75, 3.70, (.45+.3) .75, 1.4, (.3 + tail .3) .6 | [1.4, .75, 3.70, .75, 1.4, .6] |
| `"_--_#"` | 3.70, .75, 1.4, .6, 1.4, .75, 3.70, (.45 + .45 + tail .45) 1.35 | [3.70, .75, 1.4, .6, 1.4, .75, 3.70, 1.35] |
| `"#"` | one space with no line: `_add_space` on an empty array only sets the tail; the tail is added only when the array is non-empty -> [] | [] (solid) |
| `"l"`, `"ll"` | all `l` -> solid (setstyle) | [] |
| `"-x"` | `x` invalid -> None (note or refusal per U40-08) | None |

Port (TR-40.8), to be pasted above `translate_lpattern`:

```python
    _LPATTERN_FORMULA_RE = re.compile(r"[l_\-.# ]{1,200}")

    @staticmethod
    def lpattern_formula(text: str) -> "list[float] | None":
        """Stata's line-pattern formula decoded as linepattern.class
        _DecodePat decodes it (WP-31 E2): the numbers in pen-width units,
        [] for solid, None for a character outside ``l _ - . #``."""
        s = str(text).strip()
        if not s or OptionTranslator._LPATTERN_FORMULA_RE.fullmatch(s) is None:
            return None
        if s.replace("l", "") == "":
            return []
        arr: list = []
        was_space = True
        tail = 0.0
        def add_space(sp):
            nonlocal tail
            if not arr:
                tail += sp
                return
            if was_space:
                arr[-1] += sp
            else:
                arr.append(sp)
        def add_line(ln):
            if arr and not was_space:
                arr[-1] += ln
            else:
                arr.append(ln)
        for ch in s:
            if ch == " ":
                continue
            if ch == "l":
                add_line(4.6); was_space = False; continue
            if ch == "#":
                add_space(0.45); was_space = True; continue
            sp, ln = {"_": (0.45, 3.70), "-": (0.3, 1.4), ".": (0.3, 0.1)}[ch]
            add_space(sp); was_space = False
            arr.append(ln); was_space = False
            add_space(sp); was_space = True
        if arr and tail:
            if was_space:
                arr[-1] += tail
            else:
                arr.append(tail)
        return [round(v, 6) for v in arr]
```
(`_add_line`'s "join to a preceding line" and `_add_space`'s "merge into a preceding space" are the two `was_space` branches; `#` on an empty array only grows the tail, so `"#"` alone is solid, as the class gives.)

### Verbatim entries TR-40.C

- test/function_test_map.py, after the `"OptionTranslator.translate_lpattern"` entry: `"OptionTranslator.lpattern_formula": "test/test_symbol_pattern.py::TestFormulas::test_decodepat_table",`.
- dash.ado `_dash_plot_opts_to_json` key list (:4441-4458): add `mlpattern` directly after `mlwidth`. dash_parse.mata:5285: `"mlabcolor mlabsize ..."` line is preceded by `"mcolor msymbol msize msangle mfcolor mlcolor mlwidth mlpattern "`.
- dash.sthlp Unsupported list: delete the two `{phang2}` lines :5029-5033 whole; the example at :4978-4979 becomes `{cmd:. dash scatter mpg weight, mlabwidth(2) t1title("hi")}` / `(note: dash: ignoring unsupported option(s): mlabwidth() t1title())`.
- TWOWAY_COVERAGE_AUDIT.md:112 (Marker styling row) appended: `[WP-31 E1, commit <sha>: corrected -- every Stata symbol drawn] [WP-31 E2, commit <sha>: corrected -- mlpattern() drawn]`; :169 the word `mlpattern` and its comma removed from the ignored list.
- CHANGELOG Results lines (marker replacement): `- msymbol(pipe) drew a horizontal dash; it is twoway's vertical bar. msymbol(point) drew an 8 px circle; it is one pixel. msymbol(o d s t) drew full-size symbols; they are the small symbols (WP-31, E1)` and `- lpattern(dot) drew [2, 4] px at every width; it is Stata's .1 .7 pen widths (and every named pattern its style file's numbers); formulas such as "-." are drawn; mlpattern() is drawn (WP-31, E2)`.

## Boundaries

- Does not touch `_apply_line_opts`'s colour or width logic, `resolve_size`, `line_px` or `_LWIDTH_*` (S41's).
- Does not read `*.style` files (S44) or scheme class directives; the scheme's `linepattern`/`symbol` keys are read as today.
- Does not draw pcarrow heads (S02) or the arrow `msize`/`barbsize` options (research §6).
- No CMYK/HSV in schemes (M7); no new dependency (M22); `_FILTER_JS` untouched (angles and dash arrays are glyph properties the saved copy loop keeps).
- `_INTENSITY["max"]` stays 9999.99; only its comment changes (E12's second half).

## Stata truth

Script `scripts/extract_symbol_pattern_truth.do` -> `test/fixtures/symbol_pattern_truth.json` (`_meta` per R7; `shell git rev-parse HEAD` into a local; python block reads `Macro.getLocal`). Run `DASH_REPO=$WT scripts/stata_slot.sh <scratch> $WT/scripts/extract_symbol_pattern_truth.do`; `git add -f` the fixture; named by test_symbol_pattern.py.

| Key | Command (sysuse auto, s2color, name(sp#)) | Recorded |
|---|---|---|
| `sym.<name>` for name in arrow arrowf A a pipe \| point p V v o d s t oh dh sh th x smv | `scatter mpg weight, msymbol(<name>)` + `graph export <name>.svg` | rc; the first marker's SVG element: tag, `fill` (none or colour), `d` path or `r`, vertex count, bbox width/height, apex direction (`up`/`down`); `factor` = bbox height / the `O` marker's bbox height |
| `sym.<name>` for name in star asterisk hexagon dot CIRCLE Circle | same | rc; the log's note line (`named style ... not found in class symbol`) or error line; the drawn marker's `r` or path |
| `sym.point_large` | `..., msymbol(point) msize(large)` | the point's bbox height, beside `sym.point` |
| `pat.<name>` for the 17 file names | `line mpg weight, lpattern(<name>) sort` + export | rc; `stroke-dasharray` and `stroke-width` of the series path |
| `pat.dash_w.<w>` for w in vvthin medium thick vthick | `line mpg weight, lpattern(dash) lwidth(<w>)` | dasharray, stroke-width; the python block writes `unit_per_width` = median over w of (dasharray[0] / 2) / stroke-width and `min_width_px` = the smallest stroke-width at which dasharray[0]/stroke-width still equals the medium ratio (vvthin shows the floor) |
| `pat.formula.<i>` for `"-."`, `"--.."`, `"_"`, `"#"`, `"-_-"`, `"_--_#"`, `"l"`, `"ll"`, `"-x"`, `"Dash"`, `"DASH"` | `line ..., lpattern("<f>")` | rc; the log's error or note; dasharray |
| `pat.scheme_formula` | a scheme file `scheme-u40.scheme` in the work dir with `#include s2color` and `linepattern p1line "--.."`; `line mpg weight, scheme(u40)` | dasharray |
| `mlp.<p>` for dash, dot | `scatter mpg weight, msymbol(Oh) mlpattern(<p>) msize(vlarge)` | the marker circle's `stroke-dasharray` |

**Truth block** in `test/test_wp31_truth.cscript` above the marker line, `* ==== S40 E1 E2: Marker symbols and line patterns ====`, gated `if inlist("`only'", "", "S40") & `: list posof "S40" in w31_run' {`, cases: U40-01 the fixture is stamped and holds every key; U40-02 (per symbol) dash's saved and served marker equals the table (marker name, hollow, angle, factor) -- rendered through `_dash_serve_spec` and a `python:` helper reading `glyph.marker`, `fill_alpha`, `angle`, `size`; U40-03 dash's dash array for every named pattern at medium equals the fixture's dasharray within 0.05; U40-04 the same at vvthin, thick and vthick; U40-05 `msymbol(star)` and `msymbol(dot)` log twoway's note text (or rc) in dash and twoway alike, same session (`capture noisily twoway` beside `capture noisily dash`); U40-06 the seven formulas draw the fixture's arrays, and `"-x"` behaves as twoway's rc says; U40-07 `msymbol(CIRCLE)` and `lpattern(Dash)` behave as twoway's rc/note says; U40-08 `mlpattern(dash)` dashes the marker outline in both modes and nothing is printed. Refusal cases, if any branch refuses, go to test_option_validation.cscript as U40-09.. with `capture twoway` beside `capture dash`.

## TDD test stubs

### Regression tests, `test/test_symbol_pattern.py` (new; red at 6370ca4 unless marked guard)

Helpers: `_figs(mode, spec, df)` as test_date_range.py's `_saved`/`_served`; `plot_for` from test_server_layer_defects; the fixture read once; drawing classes parametrized `mode in ("saved", "served")`.

- Test: fixture stamped, every key present -- `TestTheFixture::test_meta`, `::test_every_probe` (guard after 40-01).
- Test: `translate_msymbol` of each of the 28 names and synonyms returns the table's Bokeh marker; `arrow`/`a` hollow, `arrowf`/`A` filled -- `TestSymbols::test_every_stata_symbol[name]` (red: ValueError for arrow arrowf A a |, V).
- Test: `star asterisk hexagon hexagon_hollow dot` raise ValueError and draw the scheme symbol with one note in both modes -- `::test_non_stata_names_note[mode-name]` (red: drawn).
- Test: `pipe`/`|` glyph `marker == "dash"`, `angle == pi/2`; with `msangle(45)` `angle == pi/2 + pi/4` -- `::test_pipe_is_vertical[mode]`, `::test_pipe_keeps_msangle[mode]` (red).
- Test: `point`/`p` size 1.0 and `line_width == 0` at default and under `msize(large)` -- `::test_point_is_one_pixel[mode-msize]` (red: 8 px; branch D-40c).
- Test: `o d s t oh dh sh th` sizes equal the `sm*` sizes; `x v` unchanged -- `::test_shorthands_are_small[mode-name]` (red).
- Test: `V` draws as `v` -- `::test_V_equals_v[mode]` (red).
- Test: case folding per fixture -- `::test_case_is_twoways[mode]` (red or guard by branch).
- Test: `lpattern_formula` on the eleven formulas equals `_DecodePat`'s numbers (`"-."` -> `[1.4, 0.6, 0.1, 0.6]`? no: computed by the port and pinned against the fixture's dasharray / unit) -- `TestFormulas::test_decodepat_table` (red: AttributeError), `::test_l_is_solid`, `::test_invalid_char_is_none`, `::test_bounded_length`.
- Test: `translate_lpattern(name, w)` equals fixture dasharray at the four widths -- `TestNamedPatterns::test_every_file_name[name]`, `::test_scales_with_width[w]` (red: fixed pixel lists).
- Test: every `translate_lpattern(` call in dash_render.py has a width argument (source scan) -- `::test_every_call_passes_a_width` (red).
- Test: a scheme `linepattern p1line "--.."` draws the formula; an invalid scheme pattern warns and draws solid -- `TestSchemePatterns::test_formula_in_scheme[mode]`, `::test_invalid_notes_once` (red).
- Test: `mlpattern(dash)` sets the marker glyph's `line_dash` to the dash array at the marker's outline width, silently, both modes; it is not on the pending list; the help has no Unsupported entry for it -- `TestMlpattern::test_outline_is_dashed[mode]`, `::test_silent`, `::test_not_pending` (red).
- Test: after a saved and a served filter move, marker angle, size and dash array are unchanged -- `TestAfterAMove::test_saved`, `::test_served` (guard).
- Test: no `dash-*.scheme` names a deleted symbol -- `::test_no_shipped_scheme_names_a_deleted_symbol` (guard).

### Cases in cscripts

- test_wp31_truth.cscript U40-01..U40-08 (red at base but U40-01).
- test_option_validation.cscript U40-09.. only if a branch refuses (then red at base).

### Flips (in place, `Flipped:` lines)

The nodes `<scratch>/s40/40-flips.txt` lists (Evidence); docstring reason "a pattern is Stata's numbers times the pen width, and the symbol table is Stata's (WP-31 E1/E2)". test_unsupported_report_is_true.py counts move with `# 196 -> 195: E2 mlpattern drawn` (verify the numbers against the file at the batch-13 base).

### Parity corpus (R8)

test_mode_parity.py `CORPUS` under `# WP-31 E1/E2`: "msymbol(arrow)", "msymbol(pipe) msangle(30)", "msymbol(p)", "lpattern(\"-_-\") lwidth(thick)", "mlpattern(dot) msymbol(Oh)"; `MOVE_CORPUS`: "lpattern(dash) lwidth(thick), dropdown to Foreign".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Symbol table, angles, sizes | pytest test_symbol_pattern.py | symbol_pattern_truth.json | yes |
| Non-Stata names note or refuse | pytest + cscript U40-05 | same | yes |
| Pattern numbers × width | pytest + cscript U40-03/04 | same | yes |
| Formulas, scheme formulas | pytest + cscript U40-06 | same | yes |
| Case folding | cscript U40-07 + pytest | same | yes |
| mlpattern | pytest + cscript U40-08 | -- | yes |
| Help/Unsupported/audit | test_help_conformance.py, test_unsupported_report_is_true.py | -- | -- |

AC-40.1 every fixture symbol draws its marker; AC-40.2 dash arrays within 0.05 px of twoway's at four widths; AC-40.3 formulas decode as `_DecodePat`; AC-40.4 `mlpattern()` drawn and delisted; AC-40.5 unknown names handled as measured; AC-40.6 two green commits, flips recorded.

## Tasks

**Commit boundary.** 40-01 and 40-02 form the E1 commit, subject `Draw every Stata marker symbol, as twoway does (WP-31 E1)`; 40-03 forms the E2 commit, subject `Draw line patterns from Stata's numbers scaled by the pen width, and mlpattern() (WP-31 E2)`; E12's two halves are named in both bodies (`GAPS3: E12 Tracked` closed in the E2 commit). Bodies in BRIEF's line forms, opening with `<scratch>/40-01-failure.txt`'s text (E1 part) and its E2 part. `$WT=<worktrees>/wp31-s40`.

<task type="auto" id="40-01">
  <name>Measure twoway symbols and patterns, write failing tests</name>
  <files>scripts/extract_symbol_pattern_truth.do, test/fixtures/symbol_pattern_truth.json, test/test_symbol_pattern.py</files>
  <action><![CDATA[
    Check `git -C $WT branch --show-current` prints wp31-s40 and `git -C $WT rev-parse HEAD` equals the batch-13 base. Create scripts/extract_symbol_pattern_truth.do from the "Stata truth" table (head copied from scripts/extract_date_axes_truth.do: DASH_REPO guards, adopath, mata and ado loads, `global dash_nobrowser 1`, work dir in c(tmpdir), `shell git rev-parse HEAD`); the python block parses each SVG with xml.etree (no regex over the whole file), writes the keys and `unit_per_width`/`min_width_px`, `_meta` with the five keys, sort_keys. Run it through the slot; `git add -f test/fixtures/symbol_pattern_truth.json`. Create test/test_symbol_pattern.py with exactly the classes of "TDD test stubs", reading the fixture for every expectation (no literal dash arrays). Run `python3 -m pytest test/test_symbol_pattern.py -q -n0 -p no:cacheprovider -rf > <scratch>/s40/40-01.log 2>&1` and write `<scratch>/40-01-failure.txt` (base sha, each FAILED node and its one-line reason, the guards). On a scratch copy of dash_render.py carrying TR-40.1..TR-40.10, run the five pinned files of Evidence and write the red node list to `<scratch>/s40/40-flips.txt`. Write U40-01..U40-08 into test/test_wp31_truth.cscript's S40 block (gate form of BRIEF R1) and run it with `WP31_ONLY=S40` through the driver; append its FAIL lines to the failure file. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/symbol_pattern_truth.json'));print(sorted(d['_meta']), 'unit_per_width' in d, len([k for k in d if k.startswith('sym.')]))"` prints the five keys, True and at least 26; `grep -c FAILED <scratch>/s40/40-01.log` is at least 20; `grep -c "U40-0[2-8] FAIL" <scratch>/s40/run_test_wp31_truth.log` is 7; `grep -c SKIP <scratch>/s40/run_test_wp31_truth.log` is 0; `test -s <scratch>/40-01-failure.txt`.]]></verify>
  <done>twoway's symbol shapes, pattern arrays at four widths, formula decodings and note/refusal texts were recorded in a stamped fixture, and every regression test and truth case was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="40-02">
  <name>Draw every Stata symbol and commit E1</name>
  <files>dash_render.py, dash.sthlp, BUGS.md</files>
  <action><![CDATA[
    Apply TR-40.1 to TR-40.6 in dash_render.py, branching on the fixture: D-40a (arrow factor and hollow from `sym.arrow`/`sym.arrowf`), D-40c (`sym.point_large` equal to `sym.point` keeps `_SYMBOL_FIXED_PX`; else drop it and give `point`/`p` the measured factor), D-40d (`sym.V` fill), D-40f (if any of `sym.star|asterisk|hexagon|dot` has rc 198, add an `msymbol=enum,...` rule is NOT the route: add the five names to a new Mata-free check in `_dash_validate_value`'s `style` kind for option msymbol printing the measured text, and a CHANGELOG Changed-behaviour line), D-40j (`sym.CIRCLE`). Correct the `_INTENSITY["max"]` comment at :8946-8948 to "999999 percent, 9999.99 as a fraction". Edit the help paragraphs of TR-40.13 that concern symbols (:1051-1053, :4624-4626) and TWOWAY_COVERAGE_AUDIT.md:112's symbol words. Flip the symbol nodes of `<scratch>/s40/40-flips.txt` in place. Run test/test_symbol_pattern.py (symbol classes green, pattern classes still red), the flipped files, test_help_conformance.py, test_mode_parity.py -k "msymbol", and the S40 cscript block (U40-02, U40-05, U40-07 PASS). Close BUGS.md's E1 entry (Resolution form of BRIEF), rewrite GAPS3's `E1 Tracked` line, replace the `<!-- WP-31 E1 -->` marker(s). Commit on wp31-s40 with the E1 subject and body; grep the commit message for tooling or vendor names (CLAUDE.md rule 6); the count must be 0.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_symbol_pattern.py -q -n0 -p no:cacheprovider -k "Symbols or Fixture or AfterAMove" ` ends `passed` with 0 failed; `grep -c "U40-0[257] PASS" <scratch>/s40/run_test_wp31_truth.log` is 3; `git log -1 --format=%s` ends `(WP-31 E1)`; `grep -c '^- \[x\] Title:.*arrow' BUGS.md` is at least 1.]]></verify>
  <done>Every Stata symbol name and synonym draws twoway's marker in both modes, non-Stata names are handled as twoway handles them, and the E1 commit was made with the regression, flip, fixture, BUGS and GAPS3 lines.</done>
</task>

<task type="auto" id="40-03">
  <name>Scale patterns by width, decode formulas, draw mlpattern, commit E2</name>
  <files>dash_render.py, dash.ado, dash_parse.mata</files>
  <action><![CDATA[
    Apply TR-40.7 to TR-40.11 (constants from the fixture's `unit_per_width` and `min_width_px`; D-40h's refusal branch if `pat.formula."-x"` has rc 198: add `lpattern=lpat` is NOT a kind: add a `_dash_lpattern_formula_ok(text)` Mata function (header index, `_needed` list dash.ado:448-479 alphabetical, test/program_coverage_map.py `"dash_parse.mata": {"_dash_lpattern_formula_ok": ("test_option_validation.cscript:U40-09",)}`) called from `_dash_validate_value`'s style kind for lpattern/mlpattern/clpattern/alpattern, printing the measured text, with a CHANGELOG Changed-behaviour line). Then edit dash.sthlp :3984-3987, delete :5029-5033 and rewrite the example :4978-4979 (TR-40.13), TWOWAY_COVERAGE_AUDIT.md:112 and :169, test_unsupported_report_is_true.py (mlpattern to LIVE_VALUES with two values `dash`/`dot`; counts with the `# old -> new: E2 ...` comment), function_test_map.py (TR-40.12). Flip the pattern nodes of 40-flips.txt in place. Run test/test_symbol_pattern.py (all green), the flipped files, test_help_conformance.py, test_unsupported_report_is_true.py, test_help_claims_8.py -k mlpattern, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test_function_test_map.py, test_program_coverage_map.py, test_mode_parity.py -k "lpattern or mlpattern", and the S40 block (U40-03, U40-04, U40-06, U40-08 PASS; U40-09.. if written). Close BUGS.md's E2 and E12 entries, rewrite their GAPS3 Tracked lines, replace the E2 and E12 markers. Commit with the E2 subject; no tooling names.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_symbol_pattern.py test/test_unsupported_report_is_true.py test/test_help_conformance.py test/test_function_test_map.py -q -p no:cacheprovider` ends with 0 failed; `grep -c "U40-0[3468] PASS" <scratch>/s40/run_test_wp31_truth.log` is 4; `grep -c "mlpattern" dash.ado` shows no `_dash_pending` line (`grep -c "_dash_pending.*mlpattern" dash.ado` prints 0); `git log -1 --format=%s` ends `(WP-31 E2)`; `grep -c '^- \*\*E1[2]* Tracked:\*\* Closed' GAPS3.md` prints 2.]]></verify>
  <done>Named patterns draw their style file's numbers times the pen width, formulas decode as Stata decodes them, mlpattern() dashes marker outlines in both modes, and the E2 commit closed E2 and E12.</done>
</task>

<task type="auto" id="40-04">
  <name>Hand back S40 with its gate checks</name>
  <files>none</files>
  <action><![CDATA[
    Run `python3 -m pytest test/test_symbol_pattern.py test/test_scheme_consumption.py test/test_server_scheme.py test/test_option_validation.py test/test_glyphs.py test/test_label_sinks.py -q -p no:cacheprovider` and the S40 block once more through the driver (`WP31_ONLY=S40`); confirm `git -C $WT log --format=%s <base>..HEAD` prints exactly two subjects ending `(WP-31 E1)` and `(WP-31 E2)`; confirm every `Flipped:` line in both bodies names a node in 40-flips.txt and vice versa; confirm no `_dash_pending` line names mlpattern and dash.sthlp's Unsupported section has no `mlpattern`. Write `<scratch>/s40/handback.txt`: the two shas, the fixture path, the branch decisions taken (D-40a shape, D-40c, D-40d, D-40f, D-40h, D-40j each with the measured value), and any residual for M12 (e.g. the arrowhead base edge if `arrow` is two strokes).
  ]]></action>
  <verify><![CDATA[The pytest run ends with 0 failed; `grep -c "FAIL" <scratch>/s40/run_test_wp31_truth.log` prints 0 and `grep -c "S40 end" <scratch>/s40/run_test_wp31_truth.log` prints 1; `test -s <scratch>/s40/handback.txt`.]]></verify>
  <done>S40's two commits were verified green on their own and directly covering tests and the cscript block, and the hand-back note records every measured branch.</done>
</task>

## Section completion criteria

- Every name of the symbol table draws its marker in both modes; `pipe` vertical; `point` one pixel (or the measured rule); `arrow`/`arrowf` per D-40a; shorthands small; non-Stata names handled as measured.
- Every named pattern and formula draws Stata's numbers times the pen width at every width; the scheme reader accepts formulas; `mlpattern()` drawn and delisted everywhere (pending list, help, audit, tests).
- Case folding matches U40-07; `_INTENSITY` unchanged but documented.
- Two green commits with the line forms; BUGS.md E1, E2, E12 closed; GAPS3 Tracked lines rewritten; markers replaced; fixture stamped and named.

## Notes

- **Order inside `_apply_marker_opts`:** msymbol sets the base angle first, msangle adds to it, mlwidth before mlpattern (the dash array scales by the outline width). In `_apply_line_opts` move the lpattern block below lwidth for the same reason.
- **Renderer order:** the served app copies the three classes whole; a module-level helper would need a copy-list entry -- TR-40.8 is a staticmethod on purpose.
- **Fixture exclude rule:** `.gitignore` excludes fixtures; `git add -f`.
- **python_exec hazard** (project memory): check `~/.stata19/console/stata19.rc` after each slot run; a SKIP is not a pass.
- **Shared files (R1-R13).** R1: S40 block only, helpers above the header; U40-09.. in test_option_validation.cscript only if a branch refuses. R2: no entries. R3: the paragraphs of TR-40.13 only. R4: E1, E2, E12 markers. R5: three entries, three Tracked lines. R6: dash.ado :1343 deleted, JSON key list, `_needed` only if the Mata function is added. R7: one extractor. R8: corpus appended. R9: flips in place. R10: test_unsupported_report_is_true.py counts. R12: S40 is batch 13's `_apply_marker_opts`/`_apply_line_opts` editor; no `_FILTER_JS` edit.
- **For S44 (batch 15):** `translate_lpattern(value, width_px)` and `symbol_traits(value)` are the two entry points its resolver calls for `pattern` and `symbol` attributes; `_LPATTERN_MAP` keys are exactly the 17 file names.
- **Commit-body line forms** are BRIEF's: `Regression: test/test_symbol_pattern.py::<Class>::<test> -- failed at 6370ca4 with <text>`, `Flipped: ...`, `Fixture: test/fixtures/symbol_pattern_truth.json (scripts/extract_symbol_pattern_truth.do)`, `BUGS.md: "<title>" (closed)`, `GAPS3: E1 Tracked` (and E2, E12).
