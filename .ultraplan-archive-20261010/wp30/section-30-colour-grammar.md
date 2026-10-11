# Section 30: Stata colour grammar (P1.13 part a)

> Part of: WP-30 · Items: P1.13 part a (entry `P1.13a`) · Risk: yellow · Batch: 10 · Depends on: 08, 16, 24 · Blocks: 31, 33, 34, 38, 39, 43, 56 · Tasks: 17, 1 commit · Case prefix: CG

## Review amendments

- Fixed (blocker, the writer's interrupted end): the "Prototype measurement" paragraph ended `Its result: PROTOTYPE_RESULT_PLACEHOLDER`; it now states the measured result E6 already quotes (43 failed, 10,237 passed; every red a row of E6 but the map test). The file is otherwise complete through "Notes for the closeout", and every task, TR and E6 row cross-references resolve.
- Fixed (major): the commit boundary said the commit is made by 30-15; it is made by 30-17 (30-15 adds the parity cases and the truth block).
- Fixed (major): 30-10 ran `extract_scheme_truth.py` "with the flags S07 recorded", but `--out` is required (`scripts/extract_scheme_truth.py:1970`); the exact command is now given, as S33 runs it.
- Fixed (minor): the failure file sits at `<scratch>/30-P1.13a-failure.txt` (index step 1), not under `s30/`; the section decisions D-30a..h moved out of this block to the end of the Overview, unchanged.
- Checked at `c96facd`: `OptionTranslator` :5098 (`parse_color_alpha` :5379, `_means_no_color` :5440, `translate_mcolor` :5445, `translate_lcolor` :5573), `SchemeParser._color` :6466, `_color_alpha` :6491, `_init_properties` :6806, `self.tr = translator or OptionTranslator()` :7941, `_textbox_color` :4839, `_dash_graph_color` :15407, `_resolve_kpi_color` :17054, `_dash_refline_draw` :26327, the extractor's `_apply_intensity` :304 and `ColorResolver.resolve_with_opacity` :342, `_dash_option_rules` :2025 (no colour rule today), HC2-16p/q (test_help_claims_2.cscript:555-556): all as quoted. S16's `_blend_intensity(hexval, f, naturally_white=True)`, S08's `stata_number` and S06's untouched `_dash_style_note(option, value, what, using=…)` match the calls TR-30.5/30.6 make.
- Checked: batch 10. S30 edits no function S28 or S29 edits (S28 reads `_textbox_color` and `SchemeParser.apply_to_figure`; S29 edits the pass, `_apply_mlabel_opts` and the filter DOM text). Shared test files (`test_mode_parity.py` CORPUS, `test_html_output.py`, `test_help_claims_2.py`) take distinct hunks; S30 regenerates last (A152). M5 (comma refusal in twoway's rc and words), M6 (malformed numbers silent) and M1 hold. Tracking forms match section-01 (title, both lists `Results that change` and `Changed behaviour`, stub header, subject).
- Rejected: "fall back to the included scheme's colour" (GAPS2 D7 plan step 4): twoway draws black (D-30h).
- (cross-file pass) Notes commit-message line: `BUGS.md: "Stata colour grammar (P1.13 part a)" (closed)` named the section, not the entry; now `BUGS.md: "<WP30_OPEN["P1.13a"]>" (closed)` (title as S01 Appendix B writes it), the "or" dropped (g01).
- (cross-file pass) 30-17 verify: added the key-deletion check `grep -c '^    "P1.13a": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.
- (ratification 06oct2026) Item 27 (A37, P1.12.6) is "Fix in WP-30": S08 (batch 3) syncs the nonselection and muted copies after the appliers; P2.49 is not filed. 30-14 no longer reports a failure of S08's old guard as P2.49's: S08's brushed-copy tests must stay green and a failure is a regression of S08's fix; 30-14's sweep now includes their file. Boundaries state that S30's colours reach the copies through S08's sync (S30 adds no styled property, so no test is added).

## Overview

**What is wrong today.**

DROPIN-REMAINING.md:103 reads: "`navy*.5`, `*.5`, CMYK, HSV and bg/fg are refused. An unreadable scheme colour falls back to #000000." GAPS2 D7 (GAPS2.md:918-927) gives the gap: `translate_mcolor` "accepts only names, 3-number RGB and #hex"; `navy*.5`, `"0 0 0 255"`, `"hsv 240 1 1"`, `bg`, `fg` and `stblue*.3` "all raise `ValueError` and keep the scheme colour with a note".

Measured at `c96facd` (scratch, `python3 -c` over `dash_render`):

```
'navy*.5'      -> ValueError | parse_color_alpha: (None, None)
'0 0 0 255'    -> ValueError | (None, None)
'hsv 240 1 1'  -> ValueError | (None, None)
'bg'           -> ValueError | (None, None)
'Navy'         -> #1a476f    | ('#1a476f', None)        twoway: note + black
'grey'         -> #808080    | ('#808080', None)        twoway: note + black
'#f00'         -> #f00       | ('#f00', None)           twoway: default, silent
'255,0,128'    -> #ff0080    | ('#ff0080', None)        twoway: r(198) invalid '0'
'%50'          -> #000000    | (None, 0.5)
scheme "#include s2color / color background bogus / color heading bogus / color p1 navy*.5 / color p2 Navy":
  background #d9e8f0  title #000000  p1 #000000  p2 #1a476f
```

In Stata, `dash scatter mpg weight, mcolor(navy*.5)` draws the scheme default with a note (research p1-13 §2: `#1a85ff + note` under stcolor). Saved and served agree, so this is one defect in both modes.

**After this section,** in both modes and before and after a filter move, every colour option and every scheme file read by dash follows Stata's colour grammar as StataNow 19.5 draws it:
- `colour*#`, with twoway's rounding and its clamp above 1, and multiplied rather than blended under `system naturally_white 0`;
- CMYK `"# # # #"` (proportions or integers);
- HSV `"hsv # # #"` (the hue wraps);
- `bg`, `fg`, `background` and `foreground` from the scheme;
- quoted forms with intensity;
- `%#` and `*#` in either order.

These rules also hold:
- An unknown, wrong-case or out-of-range colour draws black (a bar `#333333`), with the note, wherever this section reaches it (D-30c).
- A malformed hex, multiplier or opacity keeps the default, silently, as twoway does.
- A comma-written colour is refused in twoway's words.
- An unreadable colour in a scheme file draws what twoway draws for that key: black with a note for an unknown name, white for a malformed number.
- The extractor reads the same grammar, and the shipped files are regenerated, which is a no-op.

**Why one section.** Every one of these is one function's grammar, `translate_mcolor`/`parse_color_alpha`, and its scheme twin `SchemeParser._color`/`_color_alpha`. P1.13 is split (A138): bare `*#`/`%#` at every site, and the remaining direct sites, are S43's (P1.13b). This section edits no applier and no mapper.

**Test order and commit rule.** Task 30-01 writes every regression test of this section into `test/test_colour_grammar.py`. It runs them against the unmodified worktree (the batch-10 base) and saves the failure text to `<scratch>/30-P1.13a-failure.txt`; it does not commit. 30-02 adds the Stata fixture and its fixture-driven class. Tasks 30-03 to 30-16 turn the tests green, flip the pinned tests with their reasons and update the help. 30-17 runs the full suite once through the queue, closes the BUGS.md entry and makes the section's one commit, `… (WP-30 P1.13a)`. No test-only commit exists, and no red tree is committed (rule 4).

### Section decisions (this file; they apply the binding M decisions and register rows, and record what was measured while writing it)

- **D-30a — one reader, three answers.** `OptionTranslator.stata_colour(value, *, context="option", background="#eaf2f3", foreground="#000000", naturally_white=True)` returns `(status, hex, alpha)`. `status` is `"ok"` (the colour; `hex` is `None` only for a value with no colour of its own, a bare `*#` or `%#`), `"keep"` (option context only: the site keeps its own colour, silently) or `"unknown"` (`hex` is black with the value's own multiplier and opacity applied; the caller notes it). `translate_mcolor`, `translate_lcolor` and `parse_color_alpha` delegate to it and keep their signatures (keyword-only context arguments added). No caller of theirs is edited except the four module readers of TR-30.7 and TR-30.8.
- **D-30b — the mapper's translator knows its scheme.** `GlyphMapper.__init__` builds `OptionTranslator(scheme_of=lambda: self.scheme)`, whose three colour readers are instance attributes that pass the scheme's `bg`/`fg` lookups and `naturally_white`. Every applier and mapper site (`self.tr.…`) therefore reads `bg`, `fg` and `colour*#` with the graph's own scheme, including a graph-level `scheme()` swapped onto the mapper (dash_render.py:30186-30193), without one applier or mapper being edited (manifest notes; R12).
- **D-30c — where "unknown is black" lands in this section.** Through `parse_color_alpha` it reaches every applier site: markers (`mcolor`, `mfcolor`, `mlcolor`, a folded `color`), lines (`lcolor`, `clcolor`, a folded `color`), fills (`fcolor`, then S16's blend: a bar's black becomes `#333333`) and the CI band. S30 also edits the module readers `_textbox_color`, `_dash_graph_color` and `_dash_refline_draw` (register P1.13.1: textbox, graph colour, refline). The direct `translate_mcolor` sites inside appliers and mappers keep today's note and scheme colour for an unknown value until S43 routes them through `parse_color_alpha`. These are `_apply_mlabel_opts` (`mlabcolor`), `_apply_colorvar` (`colormissing`), `map_bar`/`map_rbar` (`color`, `bfcolor`, `blcolor`), `map_area`/`map_rarea` (`color`), `_histogram_quads`, `map_dropline`, `map_rcapsym`, `map_scatteri`, `map_pcarrow` and `map_pcbarrow`. The valid new forms (`navy*.5`, CMYK, HSV, `bg`/`fg`) already work at those sites through the bound `translate_mcolor`.
- **D-30d — five corrections to research p1-13, measured 03oct2026 (Evidence E3).** (1) An invalid multiplier does not keep the base: it keeps the **site's default**, silently (`mcolor(red*abc)` draws `#1A476F`, not red). Only an empty one is ignored (`red*` is red). (2) An unknown base still takes its multiplier and opacity: `mcolor(Red*.5)` is `#808080` and `mcolor(Red%50)` is black at 0.5, each with the note. (3) `bg`/`fg` are a named-style lookup of the scheme's own `color background`/`color foreground` text. It fails, giving black and a note, when that text is RGB, HSV, CMYK, `%#` or `*#`. (4) Scheme files follow their own rules: a comma separates numbers, and a malformed hex, multiplier, opacity or comma list draws white, silently. (5) The `hsv` keyword is case-insensitive (`"HSV 240 1 1"` is blue). Colour names are not.
- **D-30e — the `bg`/`fg` lookup on dash's own files.** dash's shipped files carry every Stata colour name as resolved hex. So a raw `#rrggbb` counts as a name for the lookup, as does every name of the colour table. The cost is a measured residual: a user scheme that writes `color background "#ff0000"` gives `bg` = red in dash and black with a note in twoway (probe t05).
- **D-30f — the comma refusal lives in dash.ado's rule table.** A new rule kind `colour` covers the twelve plot colour options twoway refuses it on, and refuses with twoway's words `invalid '<word>'`, r(198). `bgcolor()` is not given the rule, because twoway accepts `bgcolor("1,2,3")`. Nor are dash's own `plotbgcolor()`, `colormissing()` and KPI colours. A comma inside a structured option's sub-option (`title(…, color())`, region colours, `xline(…, lcolor())`) is still read by the renderer as an unknown colour (black, noted) where twoway refuses it. This is filed for the closeout.
- **D-30g — `_COLOR_MAP` loses `""` and the four British spellings** (register P1.13.3, P1.13.5's `""` part; IR-6). `OptionTranslator._BRITISH_SPELLINGS` keeps them for the KPI alone, which also keeps a case-insensitive Stata lookup ahead of CSS (P1.13.2), so every KPI colour accepted at `c96facd` is unchanged.
- **D-30h — not implemented: GAPS2 D7 plan step 4** ("fall back to the included scheme's value, not #000000"). twoway draws black for an unreadable scheme name (critic, research p1-13 §3), so dash draws black too.

## Risk: [yellow] — the colour readers every layer, title, region and scheme goes through

**Why.** `translate_mcolor` is CRITICAL (26 impacted, a lower bound: about 25 call sites through `self.tr` are not resolved by the index). `_textbox_color`, `_resolve_kpi_color`, the extractor's `_apply_intensity` and `ColorResolver.resolve_with_opacity` are CRITICAL too, and `SchemeParser._color` is HIGH. Unknown colours turn black where they drew the scheme's colour. That is a visible look change (M1, RK-4) in every dashboard that carries a typo.

**Risk factors.**
1. The bound translator (D-30b) changes what `self.tr` is on every mapper. A test that passes its own `OptionTranslator()` gets a bound copy, and anything else passed is kept (TR-30.5).
2. Scheme reads become order-dependent: `color foreground`, then `color background`, then the rest, because `bg`/`fg` resolve to them.
3. The interim state up to S43: direct mapper sites still draw the scheme colour for an unknown name, so a bar's `color(bogus)` draws a scheme fill with a black outline (the line applier's fold). Titles and graph regions read `bg`, `fg` and `*#` with s2color's background, foreground and blend rule under every scheme. It exists only on `wp30-p1`, and no release is cut before S58.
4. The list of tests pinning today's behaviour is long. A prototype measured it (Evidence E6: 21 rows), and 30-14 re-measures it on the worktree.

**Mitigation.** The reader is pure and fully table-tested against 175 measured values before any site is touched (30-03). Every changed site is compared with twoway's SVG in both modes and after a move (30-13). The flip list is re-measured on the worktree, never trusted (R9). Impact runs at the batch base for every symbol in Evidence E7 (index 10.0), and its HIGH/CRITICAL warnings are reported once.

## Dependencies

- **Depends on: 08, 16, 24** (and, through them, S06's note channel and S15's `naturally_white`).
  - S08 provides `OptionTranslator.stata_number` (the one number grammar: `+.5`, `5e-1`, `1d3`; at most 64 characters; finite or `None`).
  - S15 provides `SchemeParser.naturally_white` (S16 consumes it), with s1rcolor's `system naturally_white 0` in the shipped file.
  - S16 provides `GlyphMapper._blend_intensity(hexval, f, naturally_white=True)`: the one intensity rule with the clamp above 1. `colour*#` calls it, and `_apply_fill_opts` blends the fill's resolved colour again (twoway composes the two: `bar …, color(navy*.5)` is `#A4B5C5`).
  - S24 stops reading `color p#mark`, so `color p1mark bogus` cannot turn markers black (register P1.13.7; twoway ignores `p#mark`).
  - S06's channel prints every `_dash_style_note` and `dash scheme:` warning as twoway's `(note: …)`.
- **Blocks:** S31 (labcolor and the axis-line colour read this grammar), S33 (marker-label and colour-key colours from the scheme), S34 (third-party schemes' quoted-RGB, CMYK and HSV colours), S38 (region colours, `%#`), S39 (`xline` colours), S43 (bare `*#`/`%#` and the remaining direct sites) and S56 (`text()` colour through `_textbox_color`).
- **Parallel batch 10:** S28 (by() panel labels and overall text) and S29 (SMCL in graph text). Merge order is S28, S29, S30: S30 regenerates and lands last (A152).
- **Can run with:** both partners. No function is shared. S28 edits `_build_sources_and_figures`, `_dash_facet_label`, `DashRenderer._facet_label` and the template's by() titles. S29 edits `_apply_mlabel_opts`, `_mlabel_column_kind` and `_dash_finish_graph_text`. S30 edits none of these.

## Evidence

Anchors are at `c96facd` (re-verified while writing this file). Earlier batches (S06, S08, S13, S15, S16, S24) move line numbers, so the symbols govern.

### E1 — the option reader (dash_render.py)

`OptionTranslator` (class 5098). `_COLOR_MAP` (5122-5232) holds Stata's 92 names, plus an empty key and four British spellings:

```
5222        # An unset colour option.  Not a Stata name; kept because callers
5223        # resolve an empty option through this table.
5224        "":                "#000000",
5226        # British spellings, dash's own convenience.  Stata accepts only
5228        "bluishgrey":      "#d9e6eb",
5229        "dimgrey":         "#e8e8e8",
5230        "grey":            "#808080",
5231        "ltbluishgrey":    "#eaf2f3",
```

`translate_mcolor` (5445-5513) strips `%`, lower-cases, accepts three integers (with commas), a name, or 3/6-digit hex, and raises otherwise:

```
5473        v = v.lower()
5476        parts = v.replace(",", " ").split()
5485        # Named color lookup (case-insensitive)
5486        if v in OptionTranslator._COLOR_MAP:
5487            return OptionTranslator._COLOR_MAP[v]
5506        if re.fullmatch(r"#(?:[0-9a-f]{3}|[0-9a-f]{6})", v):
5507            return v
5509        raise ValueError(
5510            f"Unknown Stata color: '{value}'. "
```

`parse_color_alpha(value, option="")` (5379-5428) splits the last `%`, resolves the rest through `translate_mcolor`, and notes an unknown name through `_dash_style_note` when `option` is given:

```
5420        if v:
5421            try:
5422                hex_color = OptionTranslator.translate_mcolor(v)
5423            except ValueError:
5426                if option:
5427                    _dash_style_note(option, value, "colour")
5428        return hex_color, alpha
```

`translate_lcolor` (5573-5575) is `return OptionTranslator.translate_mcolor(value)`. `_means_no_color` (5440) lower-cases `none` (unchanged here). `_dash_style_note(option, value, what, using="the scheme's default", prefix="dash")` (15371-15404) echoes the value through `_dash_display` (printable, at most 80 characters) and de-duplicates per `(prefix, option, value, what)` per render.

### E2 — the scheme reader (dash_render.py)

`SchemeParser._color` (6466-6489) returns the default for an absent key and warns and returns the default for a present unreadable one:

```
6476        raw = self._props.get(key, "").strip()
6477        if not raw:
6478            return default
6479        try:
6480            return OptionTranslator.translate_mcolor(raw)
6481        except ValueError:
6482            warnings.warn(
6483                f"dash scheme: colour '{raw}' (from '{key}') is not a colour "
6484                f"dash recognises; falling back to {default}. The rendered "
```

The warning echoes `raw` unbounded. `_color_alpha` (6491-6517) reads `%NN` through `parse_color_alpha(raw)` and falls back through `_color`. `_stub_color_alpha` (6527-6541) walks `p#stub → pstub → p# → p`, and its docstring says a present unreadable step "falls back to the rest of the chain rather than to black". `_line_color` (6723-6729) and `_band_color` (7139-7145) test `none` and then call `_color`/`_color_alpha`. `_init_properties` (6806) reads `color background` first, with an absent default of `#d9e8f0`:

```
6809        self.background_color: str = self._color("color background", "#d9e8f0")
6810        self.plotregion_color: str = self._color("color plotregion", "#ffffff")
6818        self.title_color: str = self._color("color heading", "#000000")
```

`color foreground` is in `_FALLBACK_PROPS` (5789, `black`) and in all 20 shipped files (e.g. dash-s2color.scheme:165, dash-s1rcolor.scheme:180 `#ffffff`), but it has no consumer (comment at 6945-6947: "has no consumer here by design"). Every colour value in the 20 shipped files is lower-case `#rrggbb` (optionally `%NN`) or `none`, and every colour in `_FALLBACK_PROPS` is a lower-case Stata name or hex (measured with `grep`/`awk` over the files).

### E3 — Stata truth (StataNow 19.5 MP, s2color unless named; research p1-13 §3 and the critic, plus probes p2-p12 run while writing this file)

Method: `twoway scatter mpg weight, mcolor(<v>)`, then `graph export .svg`, with the marker fill read by `scripts/svg_truth.py`'s `svg_marker_fills`. Scheme probes are a user file `#include s2color` plus the line shown. All 175 values below were checked against a prototype of TR-30.1 to TR-30.4 (scratch `s30-proto/grammar.py`): 175 of 175 agree.

**Intensity (option context).** f ≤ 1: `255-(255-c)f`. f > 1: `c/f`, rounded half up. When a non-zero channel would round to 0, every channel is divided by the smallest non-zero channel instead.

```
navy #1a476f  *.5 #8da3b7  *.25 #c6d1db  *.75 #537593  *.333 #b3c2cf  *.1 #e8edf1  *.01 #fdfdfe
*0 #ffffff  *1e-5 #ffffff  *1.5 #112f4a  *2 #0d2438  *3 #091825  *5 #050e16  *10 #03070b
*20 #010406  *30 #010204  *50 #010102  *100 and *1000 #010304
maroon*1.25 #732a2f  gs8*3 #2b2b2b  red*10 #1a0000  gs8*100 #010101  white*255 #010101
red*.5 #ff8080  fg*.5 #808080  bg*.5 #f5f9f9  none*.5 #808080  "#FF0000*.5" #ff8080
"0 255 255*1.2" #00d5d5  "hsv 240 1 1*.5" #8080ff  "0 0 0 128*.5" #bfbfbf
red*+.5 and red*5e-1 #ff8080   red* (empty) #ff0000
UNCLEAR: navy*52 #010304 (26/52 rounds to 1, yet Stata clamps); excluded with this reason
```

**naturally_white 0** (s1rcolor): `navy*.5` `#0d2438`, `navy*1.5` `#276ba7`, `fg*.5` `#808080` (fg is white), `bg*.5` `#000000`, `"hsv 240 1 1*.5"` `#000080`. CMYK is unaffected (`"0 0 0 128"` `#7f7f7f`).

**CMYK.** When all four values are ≤ 1 they are proportions, each `floor(v·255)`; otherwise they must be integers 0-255. Each channel is `max(0, 255-(C+K))`, likewise for M and Y:

```
"0 0 0 255" #000000  "0 0 0 1" #000000  "85 40 0 144" #1a476f  ".334 .157 0 .565" #1a476f
"0 255 255 0" #ff0000  "10 10 5 0" #f5f5fa  "128 0 0 0" #7fffff  "100 100 100 100" #373737
"200 0 0 100" #009b9b  "0 0 0 .5" #808080  "0 0 0 .3" #b3b3b3  ".5 .5 .5 .5" #010101
".2 .4 .6 .1" #b3804d  "1 0 0 0" #00ffff  "1 1 1 1" #000000  "0 0 0 2" #fdfdfd  "0 0 0 128" #7f7f7f
note + black: "0 0 0 300" "0 0 0 127.5" "0 0 0 -1" "0 0 0 1e400" "0 0 0 0 0"
```

**HSV.** Standard HSV: the hue wraps mod 360, S and V lie in [0,1], and each channel is `floor(x·255)`. The keyword is case-insensitive and blanks repeat freely:

```
"hsv 240 1 1" #0000ff  "hsv 0 0 1" #ffffff  "hsv 209 .766 .435" #19456e  "hsv 120 1 .502" #008000
"hsv 30 .5 .5" #7f5f3f  "hsv 0 0 .5" #7f7f7f  "hsv 180 .5 1" #7fffff  "hsv 300 .25 .75" #bf8fbf
"hsv 90 .3 .9" #c3e5a0  "hsv 200 .7 .3" #163a4c  "hsv 15.5 1 1" #ff4100  "hsv 360 1 1" #ff0000
"hsv 400 1 1" #ffaa00  "hsv -30 1 1" #ff007f  "hsv 0 0 0" #000000  "HSV 240 1 1" #0000ff
note + black: "hsv 240 2 1" "hsv 240 -1 1" "hsv 240 1" "hsv 240 1 1 0" "hsv 1e400 1 1" hsv
```

**bg / fg.** s2color: bg `#eaf2f3`, fg `#000000`. stcolor: `#ffffff`/`#000000`. economist: `#c6d3df`/`#000000`. s1rcolor: `#000000`/`#ffffff`. `background` = `bg`, and `foreground` = `fg`. `BG`, `Bg` and `FOREGROUND` give the note and black. `bg` and `fg` are a named-style lookup of the scheme's raw text (probes p3/p4, all `#include s2color`; the probe names are used below and as the `bgfg` fixture rows):

```
t01-t05  color background "255 0 0" / "hsv 0 1 1" / "0 255 255 0" / red%50 / "#ff0000", then color p1 bg:
         the region is red, p1 is #000000 with "(note: named style 255 0 0 not found in class color …)"
t06      color background navy*.5 + mcolor(bg): region #8da3b7, p1 #000000 + note (si: the same with color p1 bg)
t21      color foreground "0 128 0" + mcolor(fg): #000000 + note
t20      color background red + mcolor(bg*.5): #ff8080   (a name resolves)
sa / sb  color background bg: background #000000 + note      color background fg: #000000, silent
sc / sd  color foreground bg + color p1 fg: #000000 + note    color foreground fg + color p1 fg: #000000 + note
sj       UNCLEAR (excluded): color background red + color foreground bg + color p1 fg drew a #f0f0f0 region and p1 #606060
```

Stata's own schemes write both keys as names (s2color `ltbluishgray`/`black`, stcolor `white`, economist `ebg`/`black`, s1rcolor `black`/`white`, s2mono `gs15`/`black`; `grep` over `ado/base/s/scheme-*.scheme`).

**Unknown, wrong case, out of range (option context): note plus black, and the value's own `*#` and `%#` still apply.**

```
bogus, Navy, grey, BG, "300 0 0", "255 0", "1.5 0 0", "255 0 0 0 0": #000000 + "(note:  named style <v> not found in class color, default attributes used)"
Red*.5 #808080 + note    Red%50 #000000 at 0.5 + note
mlabcolor(bogus): black labels + note    title("T", color(bogus)) #000000    yline(25, lcolor(bogus)) #000000
```

**Malformed numbers (option context): the site keeps its default, silently** (s2color p1 is `#1a476f`, so a red base tells the two apart):

```
"#F00" "#ff00" "#GG0000" "#F00%50" red%150 red%abc navy%50%30 *abc "" bogus%150 bogus*abc
red*abc red*-1 red*1e400 red*.5*2 red**.5 red*. red%50*abc "0 255 0*abc": all #1a476f, no note
red% (empty opacity): #ff0000      #ff0000, #FF0000, "#ff0000": #ff0000
```

**Opacity with intensity:** `navy*.5%50` and `navy%50*.5` give `#8da3b7` at 0.5. `*.5%50` gives `#8da3b7` at 0.5 (the bare multiplier is S43's). `"0 255 0%50*.5"` gives `#80ff80` at 0.5, `"hsv 240 1 1%50"` and `"0 0 255%50"` give `#0000ff` at 0.5, and `"hsv 240 1 1%50*.5"` gives `#8080ff` at 0.5.

**Scheme-file context** (`#include s2color` plus one line; p1's marker fill):

```
navy*.5 #8da3b7   "0 0 0 255" #000000   "hsv 240 1 1" #0000ff   "0 255 255 0" #ff0000   "0 0 0 128" #7f7f7f
navy*1.5%50 #112f4a at 0.5   navy*+.5 #8da3b7   "hsv 240 1 1*.5" #8080ff   "hsv 400 1 1" #ffaa00   navy*0 #ffffff
navy* #1a476f   "#ff0000" and "#FF0000" #ff0000   "255,0,0" #ff0000   "1,2,3,4" #faf9f8
white, silent: *.5  "#F00"  "#0F0"  "#ff00"  "#GG0000"  navy*abc  navy*-1  navy*1e400  navy*.5*2  navy**.5
               red%150  bogus%150  "255,0"  red% is red (empty opacity ignored)   %50: white at 0.5
black + note: bogus  Navy  grey  "255 0"  "300 0 0"  "0 0 0 300"  "hsv 240 2 1"  "hsv 240 1"  "1.5 0 0"  "255 0 0 0 0"
              Navy*.5 #808080   bogus%50 black at 0.5   color p1 0 0 255 (unquoted: third token "0")
color background bogus: background #000000 + note    color heading bogus: title #000000 + note
color plotregion bogus: a black plot region          color p1lineplot bogus: line #000000 + note
color p1bar bogus: fill #333333 (black at inten80) + note    color p1mark bogus / red: ignored (S24)
color background #}a{b;c and color heading #%d{e;f: background #FFFFFF and title #FFFFFF, no note (probe v01)
```

**Comma-written colours (option context), probes p2/p8/p9:**

```
mcolor(255,0,0) / mcolor("255,0,128") / mcolor("255, 0, 128") / mfcolor("0,0,0") / mcolor("255,0"): invalid '0'  r(198)
lcolor("1,2,3") / mlcolor / clcolor / alcolor / bfcolor / blcolor / fcolor / mlabcolor / acolor ("1,2,3"): invalid '2'  r(198)
mcolor("red,blue") invalid 'blue'   mcolor("1, x y") invalid 'x'   mcolor(",1") invalid '1'   mcolor("a b,c d") invalid 'c'
mcolor("navy*.5,2") invalid '2'   mcolor("255 0,0") invalid '0'   mcolor("1,") invalid 'editcopy'
mcolor(red "255,0,0") on two y: invalid '0'   title("T", color("255,0,0")), xline(…, lcolor("255,0,0")), graphregion(color("255,0,0")): invalid '0'
mcolor("1,,2"): rc 0, note "named style 1 2 not found", black    mcolor("red",blue): rc 0, no note
bgcolor("1,2,3"): rc 0    plotbgcolor(), colormissing(): "option … not allowed" (not twoway options)
```

twoway prints the word followed by one blank (`invalid '0' `). The rule: when the text after the first comma does not itself start with a comma, its first word (words split at blanks and commas) is named. With no word, the name is `editcopy`.

### E4 — the module readers (dash_render.py)

`_textbox_color` (4839-4855) warns "ignoring it" and returns the caller's default (always `None`):

```
4845    raw = opts.get("color", "")
4846    if not raw:
4847        return default
4848    try:
4849        return OptionTranslator.translate_mcolor(raw)
4850    except (ValueError, TypeError):
4851        warnings.warn(
4852            f"dash: color({raw}) is not a recognised colour; ignoring it.",
```

`_dash_graph_color(option, raw)` (15407-15425) notes the value and returns `""`. It is called by the saved figure body (30340-30376) and as emitted strings by the served template (35226-35255):

```
15421    try:
15422        return OptionTranslator.translate_mcolor(raw)
15423    except (ValueError, TypeError):
15424        _dash_style_note(option, raw, "colour")
15425        return ""
```

`_dash_refline_draw` (26327-26371) reads `lcolor` through a loop table, noting "the default" (26343-26355). Its `scheme` argument is in hand. `_resolve_kpi_color` (17054-17110) is "Translate first, then sanitise", and its CSS fallback admits a CSS name or a hex or functional form:

```
17092    raw = (val or "").strip()
17095        return _sanitize_css_color(OptionTranslator.translate_mcolor(raw),
17096                                   default)
17097    except (ValueError, TypeError):
17098        pass
17104    safe = _sanitize_css_color(raw, "")
17105    if safe and (not raw.isalpha() or raw.lower() in _CSS_NAMED_COLORS):
```

Copy lists (R2): `"_textbox_color"` (33360), `"_dash_refline_draw"` (33383) and `"_resolve_kpi_color", "_sanitize_css_color"` (33393) are in `_glyph_layer_lines`' function tuple. `_dash_graph_color` is in `_shared_stat_lines` (33542). The three classes travel by source (33436). The served app builds `_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)` (33479) after `_dash_build_scheme()` rebuilds the parser from `_SCHEME_PROPS` and calls `_init_properties()` (33452-33459). No copy-list entry changes in this section.

`GlyphMapper.__init__` (7929): `self.tr = translator or OptionTranslator()` (7941). `test/conftest.py:365` builds `GlyphMapper(OptionTranslator(), scheme)`, and test_glyphs.py:2329-2451 builds `GlyphMapper(OptionTranslator())`. No test compares `gm.tr` by identity (`grep`).

### E5 — the extractor (scripts/extract_scheme_truth.py) and dash.ado

`_apply_intensity(rgb, f)` (304-317) has no clamp, ignores `naturally_white`, and clips to [0,255]. Its docstring claims verification. `ColorResolver.resolve_with_opacity` (342-411) reads three integers, `bg`/`fg` recursively, and a style-file name through `low = tok.lower()`, and records anything else in `unresolved`. It knows no CMYK or HSV. Every one of Stata's 92 `color-*.style` files has a lower-case name (`ls`). Stata's shipped schemes use `*#` only in stcolor (`color histogram_line stc1*0.7`, `ci2_* khaki*0.3`, all f < 1), and only s1rcolor sets `naturally_white 0`, with no `*#` colour. A regeneration with the new rule is therefore expected to change nothing outside `_meta`.

dash.ado: the option-validation table (`// BEGIN option-validation table (WP-15)`) has `_dash_option_rules` (2025), with the plot list at 2028-2041, and `_dash_validate_value` (2125), which reads its value by value through `_dash_text_args` into scalars `V`/`T`. Colours have no rule. The header comment (1978-1983) says a style name, colour included, "falls back on the scheme". `test/test_option_validation.py` reads the table: `KINDS` (63) must equal `_validator_kinds()` (171), and `_MATA_ALLOWED` (386) bounds the Mata calls a validator may make (`_dash_say`, `_dash_text_args`, `st_local`, `st_global`, `st_strscalar`, `strofreal`, `strtrim`, `strpos`, `char`).

### E6 — tests that pin today's behaviour (flipped, never deleted; R9)

Found by `grep` and by a prototype run of 42 candidate files (43 failed, 10,237 passed; Notes, "Prototype measurement") (TR-30.1 to TR-30.8 applied to a `git archive` of `c96facd` in scratch). The prototype did not carry S15 or S16, so 30-12 re-measures on the worktree.

| # | Node | Today | After (reason) |
|---|---|---|---|
| F1 | `test/test_options.py::TestColorEdgeCases::test_case_insensitive_color` (244) | `RED` = `red` | `translate_mcolor("RED")` raises; `parse_color_alpha("RED", "mcolor")` is black with the note (twoway notes `Red`, P1.13.2) |
| F2 | `test/test_options.py::TestColorEdgeCases::test_an_out_of_range_rgb_draws_the_default_with_a_note` (284-299) | scheme default, "using the scheme's default." | `#000000`, "dash: mcolor(300 0 0) is not a recognised colour; using black." (twoway draws black, P1.13.1; its docstring's "draws the default colour" is the measured error) |
| F3 | `test/test_option_validation.py::TestTheNoteHelper::test_parse_color_alpha_notes_only_when_told_the_option` (849) | `(None, None)`, `(None, 0.4)` | `("#000000", None)` silent; `("#000000", 0.4)` with "…; using black." |
| F4 | `test/test_option_validation.py::TestTheDefaultIsWhatTheSchemeGives::test_a_bad_mcolor_draws_the_schemes_colour` (663) | p1 | `#000000` (renamed in place to `test_a_bad_mcolor_draws_black`) |
| F5 | `test/test_option_validation.py::TestTheRemainingSilentSites::test_a_graph_level_colour` (1077, 5 params) | "using the scheme's default.", chrome kept | "…; using black.", and the property the option sets is `#000000` in both modes (the equality assertions kept) |
| F6 | `test/test_security_surface.py::TestAColourMustBeAColour::test_a_scheme_cannot_break_out_of_its_css_rule` (161) | body `#d9e8f0`, two notes | body `background-color: #ffffff;`, title `color: #ffffff`, no colour note (probe v01: twoway draws both white, silently); the one-rule-per-line, selector-list and KPI-control assertions kept |
| F7 | `test/test_security_surface.py::TestAColourMustBeAColour::test_real_hex_still_passes` (157; params `#fff`, `#FFF`, `#abc`) | 3-digit hex passes | the 3-digit params move to a sibling assertion that `translate_mcolor` raises (twoway keeps the default); the 6-digit params kept |
| F8 | `test/test_color_fidelity.py::TestTheAliasesStillWork::test_an_alias_resolves_to_its_canonical_colour` (127, 4 params) | alias = canonical | the British spellings are not keys of `_COLOR_MAP`, and `OptionTranslator._BRITISH_SPELLINGS[alias] == canonical` (IR-6) |
| F9 | `test/test_color_alias.py::TestColorReachesTheCommonPlotTypes::test_a_bad_colour_name_does_not_take_the_render_down` (120; map_scatter, map_line) | scheme default | `#000000` with "…; using black." (both go through `parse_color_alpha`) |
| F10 | `test/test_help_claims_2.py::TestAColourWrittenWithCommasIsReadAsTheTriplet::test_both_modes_draw_red_and_say_nothing` (438) | red, silent | a hand-written spec reaching the renderer draws `#000000` with one note in both modes; the class docstring cites the r(198) in Stata |
| F11 | `test/test_help_claims_2.cscript` HC2-16p (555), HC2-16q (556) | rc 0; registered `255,0,0` | rc 198 with `invalid '0'`; no graph `hc` registered |
| F12 | `test/test_option_validation.py::TestTheRemainingSilentSites::test_a_reference_line_sub_option[lcolor]` | "…; using the default." | "dash: xline(lcolor(notacolour)) is not a recognised colour; using black.", and the Span's `line_color` `#000000` in both modes (twoway's `yline(25, lcolor(bogus))` is black) |
| F13 | `test/test_help_claims_2.py::TestAnUnknownStyleInsideAStructuredOption::test_one_note_and_the_schemes_default_in_both_modes` (the `color(bogus)` params: title under s2color and s1rcolor, xtitle and ytitle under s1rcolor) | the scheme's colour | `#000000` in both modes, one note (twoway's `title("T", color(bogus))` is black); the size params unchanged; the s2color axis-title params pass already (their default is black) |
| F14 | `test/test_ci_band_style.py::TestAdversarial::test_a_bad_colour_is_noted_and_the_scheme_kept` (the 7 `acolor` params: `` red`=1' ``, `$(rm -rf)`, `<script>`, `1e400`, `nan`, 300 `x`, `\u202ered`) | the band keeps `#c0c0c0`/`#ff0000` | the band is `#000000`, noted once, and the value never reaches a model raw (an unknown colour is black, P1.13.1) |
| F15 | `test/test_help_claims_7.py::TestRegionColours::test_an_unknown_colour_is_named_and_the_scheme_kept` (saved, served) | the scheme's region colour | `#000000`, named (renamed in place to `test_an_unknown_colour_is_named_and_drawn_black`) |
| F16 | `test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_a_hostile_colour_is_refused_not_passed_through` and `::test_quotes_that_are_not_a_pair_are_not_stripped` | the base figure's colours | the regions are `#000000`, never the raw text; the note naming the payload, and the compound-quote `#ff0000` control, kept |
| F17 | `test/test_scheme_coercion.py::TestColor::test_the_warning_says_the_output_will_not_match_stata` | "match Stata" in the warning | renamed in place to `test_the_warning_says_black_as_twoway`: "using black, as twoway does" (dash now draws what Stata draws) |
| F18 | `test/test_scheme.py::TestCssBlock::test_xss_escaped_in_css` | the payload CSS equals the clean CSS | equal except the body rule, which is `background-color: #ffffff;` (twoway draws a malformed `#}a{b;c` white); `<script>` absent; the rule and declaration counts kept |
| F19 | `test/test_scheme_resolution.py::TestTheParserCarriesTheColourOpacity::test_an_unresolvable_colour_carries_no_opacity` | `nosuchcolour%20` gives `#000000`, opacity None | `#000000` at 0.2, with the warning (twoway's `color p1 bogus%50` is black at 0.5); renamed in place to `test_an_unknown_colour_keeps_its_opacity`; `function_test_map.py`'s `SchemeParser._color` key is repointed by 30-05 to `test/test_colour_grammar.py::TestSchemeFiles::test_an_unreadable_key_draws_black_with_one_note` |
| F20 | `test/test_twoway_option_parity.py::TestTheConnectingLineOptions::test_a_bad_clcolor_is_named_as_written` | "…; using the scheme's default." | "…; using black." |
| F21 | `test/test_html_output.py::TestAdversarialPlotOptions::test_injection_in_lcolor_produces_valid_html`, `::test_injection_in_mcolor_produces_valid_html` | warns "…; using the scheme's default" | warns "…; using black"; the valid-HTML assertions kept |
| — | `test/test_option_validation.py` `KINDS` (63) | 13 kinds | gains `"colour"` (not a flip: the table gained a kind) |
| — | `test/test_option_validation.py` `_MATA_ALLOWED` (386) | — | unchanged: the `colour` branch uses ado string functions and allowed Mata only |
| — | `test/test_scheme_fidelity.py::test_color_does_not_swallow_unresolvable_token` (775) | — | stays green: `stc1` resolves, and the unknown token is still reported by name and key |
| — | `test/test_option_validation.py::TestOneNotePerOptionPerRender`, `::TestAnUnknownStyleNameIsNamedOnceInBothModes`, `test/test_mode_parity.py` `_MUST_WARN` "clcolor(notacolour)…" | — | stay green: they match the note's prefix or "; using " |
| — | `test/test_option_validation.py::TestTheRemainingSilentSites::test_area_color`, `::test_bar_color_beside_blcolor` | — | stay green (direct mapper sites, S43) |

Every prototype red is a row above, except `test_function_test_map.py::test_every_function_has_an_entry` (the prototype added no map entries). 30-14 appends every further node it finds to `$S/30-flips.txt`, each with its old expectation and reason, and classifies it as in TR-30.12.

### E7 — blast radius (`gitnexus impact <symbol> -d upstream -r dash`, run 03oct2026 at `c96facd`)

| Symbol | Risk (impacted) | Note |
|---|---|---|
| `OptionTranslator.translate_mcolor` | CRITICAL (26) | lower bound; about 25 `self.tr` sites are not resolved by the index |
| `OptionTranslator.parse_color_alpha` | LOW (5) | lower bound: 9 calls in 7 appliers by `grep`; treated as HIGH |
| `OptionTranslator.translate_lcolor` | UNKNOWN (0) | `grep`: `map_pcarrow` (14069), `map_pcbarrow` (14150), tests; unresolved |
| `GlyphMapper.__init__` | UNKNOWN (ambiguous name) | every glyph is drawn through the mapper it builds; treated as HIGH |
| `SchemeParser._color` | HIGH (7) | |
| `SchemeParser._color_alpha` | LOW (4) | |
| `SchemeParser._init_properties` | LOW (1) | every scheme, both modes |
| `SchemeParser._stub_color_alpha`, `_line_color`, `_band_color` | LOW (2), HIGH (3), LOW (2) | behaviour changes through `_color`/`_color_alpha`; docstring edit only |
| `_textbox_color` | CRITICAL (9) | |
| `_dash_graph_color` | LOW (3) | plus 5 emitted calls in the served template the index cannot see |
| `_dash_refline_draw` | LOW (3) | |
| `_resolve_kpi_color` | CRITICAL (7) | |
| `_apply_intensity` (scripts/extract_scheme_truth.py) | CRITICAL (9) | |
| `ColorResolver.resolve_with_opacity` | CRITICAL (13) | |
| `_dash_validate_value`, `_dash_option_rules` (dash.ado) | UNKNOWN | Stata programs are not indexed; `grep`: called at 2580, 2692, 2713, 5349, 5371, 7069, 7451 |

## User stories

- **US-30.1** As a twoway user, I want `mcolor(navy*.5)`, `lcolor(maroon*1.25)` and `fcolor("0 255 255*1.2")` drawn at Stata's intensity, so a lighter or darker series looks as it does in my Stata graph.
- **US-30.2** As a twoway user, I want CMYK (`"85 40 0 144"`, `".334 .157 0 .565"`) and HSV (`"hsv 209 .766 .435"`) colours drawn, so colours copied from a style guide work unchanged.
- **US-30.3** As a twoway user, I want `bg`, `fg`, `background` and `foreground` to mean my scheme's colours (white on s1rcolor, black on s2color), so `mcolor(fg)` reads on any background.
- **US-30.4** As a twoway user, I want `navy*.5%50` and `navy%50*.5` to give the same light, half-transparent colour, as in Stata.
- **US-30.5** As a twoway user, I want a mistyped colour (`mcolor(bogus)`, `mcolor(Navy)`, `mcolor(grey)`) drawn black with a note, as twoway draws it, so the mistake is as visible in my dashboard as in my Stata graph.
- **US-30.6** As a twoway user, I want `mcolor(255,0,0)` refused with twoway's message, so a do-file that fails in Stata fails the same way in dash.
- **US-30.7** As a scheme author, I want my scheme file's `color p1 navy*.5`, `color p2 "hsv 240 1 1"`, `color p3 bg` and `system naturally_white 0` read as Stata reads them, and an unreadable colour drawn as twoway draws it.
- **US-30.8** As a dashboard publisher, I want a KPI card's colour to stay the colour it was (`Navy`, `grey`, `#FFF`, CSS names), while gaining Stata's grammar.

## Business requirements

Each holds in the saved page and the served app, before and after a filter move.

- **BR-30.1** `colour*#` draws Stata's colour: towards white for # ≤ 1 and divided for # > 1, rounded half up, with Stata's clamp to the smallest non-zero channel; multiplied under `naturally_white 0`. An empty multiplier is ignored. A multiplier that is not a non-negative finite number keeps the object's default colour, silently.
- **BR-30.2** CMYK `"C M Y K"` and `"hsv H S V"` are drawn by twoway's rules. Out-of-range or malformed forms are unknown colours (BR-30.5).
- **BR-30.3** `bg`/`background` and `fg`/`foreground` (lower case) are the scheme's `color background` and `color foreground` when the scheme names those by a colour name or a hex code. Otherwise they are unknown colours.
- **BR-30.4** `%#` (0-100) sets the opacity beside `*#` in either order, in quoted forms too. An empty `%` is ignored. Any other opacity keeps the default, silently.
- **BR-30.5** Colour names are case-sensitive, and `grey`, `dimgrey`, `bluishgrey` and `ltbluishgrey` are not names. An unknown name, or an RGB/CMYK/HSV value out of range or malformed, draws black: its own `*#` and `%#` still apply, and a bar draws `#333333` at its intensity. One note names the option and value. This holds at the marker, line, fill, CI band, title/subtitle/note/caption/axis-title, graph and plot region and reference-line colour options. The remaining direct sites are BR-30.13's.
- **BR-30.6** A short or otherwise malformed hex code (`#F00`, `#ff00`, `#GG0000`) keeps the default, silently. A 6-digit hex in either case is drawn.
- **BR-30.7** A colour written with a comma in a plot colour option (`mcolor`, `mfcolor`, `mlcolor`, `mlabcolor`, `lcolor`, `fcolor`, `color`, `acolor`, `alcolor`, `bfcolor`, `blcolor`, `clcolor`, each element of a stylelist included) is refused before any Python runs. The refusal is r(198) with twoway's words `invalid '<word>'`, and nothing is registered.
- **BR-30.8** In a scheme file a colour follows the same grammar, with twoway's scheme-file rules: commas separate numbers; a malformed hex, multiplier, opacity or comma list draws white, silently; an unknown name or out-of-range value draws black with one note per key; a key that is absent keeps dash's default. The p# chains no longer skip an unreadable step.
- **BR-30.9** A scheme's `system naturally_white 0` makes `colour*#` multiply, in options and in that scheme's own colours.
- **BR-30.10** A KPI colour accepted at `c96facd` draws the same colour: Stata names in any case, the British spellings, 3-digit hex and CSS forms. A KPI colour also reads the Stata grammar (`navy*.5`, CMYK, HSV).
- **BR-30.11** Every colour dash writes to a figure, a CSS rule or a KPI style is `#rrggbb`, or a value the CSS sanitiser accepts, whatever the input text. Echoed text is bounded.
- **BR-30.12** The extractor reads Stata's scheme files with the same intensity rule (clamp and `naturally_white`), CMYK, HSV and case-sensitive names, and regenerating the shipped files changes nothing outside `_meta`.
- **BR-30.13** (interim, until S43) At the direct sites of D-30c, an unknown colour keeps today's scheme colour and note, and a valid new form is drawn. Titles and graph regions read `bg`, `fg` and `*#` with s2color's background, foreground and blend rule. The help says so.

## Technical requirements

- **TR-30.1 Constants on `OptionTranslator`** (class 5098; after `_COLOR_MAP`).
  - Delete the `""` entry (5222-5224) and the British block (5226-5231) from `_COLOR_MAP`.
  - Add `_BRITISH_SPELLINGS: dict[str, str] = {"grey": "gray", "dimgrey": "dimgray", "bluishgrey": "bluishgray", "ltbluishgrey": "ltbluishgray"}`, with a comment that these are not Stata names and only the KPI's lenient lookup reads them.
  - Add `_COLOUR_TEXT_MAX = 200` and `_HEX6_RE = re.compile(r"#[0-9A-Fa-f]{6}")`.
  - Add `_FALLBACK_BG = "#eaf2f3"` and `_FALLBACK_FG = "#000000"` (s2color's, the fallback scheme's).
  - Update the class docstring: the colour readers of an instance built with `scheme_of` read that scheme (TR-30.5); everything else stays static.
- **TR-30.2 `@staticmethod _colour_parts(text) -> tuple[str, str | None, str | None]`.**
  - `i` is the first index of `*` or `%`. With neither, return `(text.strip(), None, None)`.
  - Otherwise `base = text[:i].strip()` and `rest = text[i:]`. Take the other marker's first index in `rest` after position 0. The text between the markers belongs to the first marker, and the text after the second belongs to the second.
  - Returns `(base, mult, pct)`, raw. No regex and no recursion.
  - Examples: `navy*.5%50` gives `("navy", ".5", "50")`; `navy%50*.5` gives `("navy", ".5", "50")`; `navy*.5*2` gives `("navy", ".5*2", None)`; `red%` gives `("red", None, "")`.
- **TR-30.3 `@staticmethod _colour_cmyk(nums) -> str | None` and `@staticmethod _colour_hsv(h, s, v) -> str | None`**, by E3's rules.
  - Both use `math.floor(x * 255 + 1e-9)` for every truncation, and both return `None` out of range.
  - CMYK: when all four values are ≤ 1 (and ≥ 0) they are proportions; otherwise each must be an integer 0-255.
  - HSV: `h % 360.0`; S and V must lie in [0, 1]. The sector is `int(h/60) % 6`.
  - Both return lower-case `#rrggbb`.
- **TR-30.4 `@staticmethod _colour_base(base, context, background, foreground) -> tuple[str, str | None]`** returns `("ok", hex)`, `("malformed", None)` or `("unknown", None)`, in this order:
  1. an exact key of `_COLOR_MAP` gives its hex;
  2. `bg`/`background` give `background`, and `fg`/`foreground` give `foreground`, exact lower case; a `None` in that argument gives unknown;
  3. text starting with `#`: `_HEX6_RE.fullmatch` gives the lower-cased hex, anything else malformed;
  4. scheme context only, text holding a comma: split at commas and strip each part. Three integers 0-255 give RGB and four numbers give CMYK; out-of-range numbers are unknown, and any other count or non-number is malformed;
  5. blank-split tokens whose first token, lower-cased, is `hsv`: exactly three numbers through `_colour_hsv`, else unknown;
  6. three numbers that are integers 0-255 give RGB, other numbers are unknown;
  7. four numbers through `_colour_cmyk`, `None` being unknown;
  8. anything else is unknown.

  Numbers are read only through S08's `OptionTranslator.stata_number`. An option-context comma reaches step 8 and is unknown, so a hand-written spec is noted and drawn black.
- **TR-30.5 `@staticmethod stata_colour(value, *, context="option", background=_FALLBACK_BG, foreground=_FALLBACK_FG, naturally_white=True) -> tuple[str, str | None, float | None]`** (D-30a).
  - A `context` other than `"option"` or `"scheme"` raises `ValueError` (a programming error).
  - `text = str(value).strip()`. If it is longer than `_COLOUR_TEXT_MAX`, return `("unknown", "#000000", None)`.
  - Let KEEP be `("keep", None, None)` in option context and `("ok", "#ffffff", None)` in scheme context. Empty text returns KEEP.
  - `base, mult, pct = _colour_parts(text)`.
  - `mult` not `None` and not blank: `f = stata_number(mult)`. `None` or `f < 0` returns KEEP.
  - `pct` not `None` and not blank: `p = stata_number(pct)`. `None` or outside [0, 100] returns KEEP; otherwise `alpha = p / 100`.
  - An empty `base` returns `("ok", "#ffffff" if scheme else None, alpha)`.
  - `st, hx = _colour_base(…)`. Malformed returns KEEP. Unknown gives `status = "unknown"` and `hx = "#000000"`.
  - If `f` is set, `hx = GlyphMapper._blend_intensity(hx, f, bool(naturally_white))`.
  - Return `(status, hx, alpha)`. It never logs, never notes and never evaluates text, and every `hx` it returns fullmatches `#[0-9a-f]{6}`.
- **TR-30.6 The three readers delegate** (keyword-only context `**ctx` passed straight to `stata_colour`; `context` is never taken from a caller of these three).
  - `translate_mcolor(value, **ctx) -> str` returns `hx` when the status is `"ok"` and `hx` is not `None`. Otherwise it raises `ValueError("Unknown Stata color: '<value>'. …")`, with today's message unchanged (pinned by `test_an_out_of_range_rgb_is_refused_not_clamped`).
  - `translate_lcolor(value, **ctx)` passes `**ctx`.
  - `parse_color_alpha(value, option="", **ctx)`:
    - `"keep"` returns `(None, None)`, silently;
    - `"unknown"` calls `_dash_style_note(option, value, "colour", "black")` when `option` is given, and returns `(hx, alpha)`;
    - `"ok"` returns `(hx, alpha)`, where `hx` is `None` for a bare `*#`/`%#`.
  - Update the docstrings (the `%` paragraph, the three answers, what is noted).
- **TR-30.7 The bound translator** (D-30b).
  - New `def __init__(self, scheme_of=None)` stores `self._scheme_of`.
  - When `scheme_of` is callable it sets three instance attributes. Each is a `lambda` (no nested `def`, so no extra map entry) that calls the static method with `**{**self.colour_context(), **kw}`, so an explicit keyword still wins:
    - `self.translate_mcolor = lambda value, **kw: …`;
    - `self.translate_lcolor = lambda value, **kw: …`;
    - `self.parse_color_alpha = lambda value, option="", **kw: …`.
  - `def colour_context(self) -> dict` returns `OptionTranslator.scheme_colour_context(self._scheme_of())`.
  - `@staticmethod scheme_colour_context(scheme) -> dict` returns `{}` for `None`, else `{"background": scheme.bg_lookup, "foreground": scheme.fg_lookup, "naturally_white": bool(scheme.naturally_white)}`, read with `getattr` and the `_FALLBACK_*` values and `True` as defaults.
  - In `GlyphMapper.__init__` replace 7941 with: if `translator` is `None`, or is exactly an `OptionTranslator` whose `_scheme_of` is `None`, then `self.tr = OptionTranslator(scheme_of=lambda: self.scheme)`; otherwise `self.tr = translator`. Add a comment citing D-30b. The lambda reads `self.scheme` at call time, so the per-graph swap (30186-30193) is honoured.
- **TR-30.8 Module readers** (in place; already on the copy lists).
  - `_textbox_color(opts, default)`: when `raw` is non-empty, `hx, _a = OptionTranslator.parse_color_alpha(str(raw), "color")`, returning `hx` if not `None`, else `default`. An unknown value gives black with "dash: color(<v>) is not a recognised colour; using black."; a malformed one gives the default, silently. The docstring says the opacity and a bare `*#`/`%#` are S43's.
  - `_dash_graph_color(option, raw)`: `hx, _a = OptionTranslator.parse_color_alpha(str(raw), option)`, then `return hx or ""`. Docstring: an unknown colour is black with the note, as twoway draws it.
  - `_dash_refline_draw`: remove `lcolor` from the loop table. Before the loop, when `style.get("lcolor")`, call `OptionTranslator.parse_color_alpha(style["lcolor"], f"{opt}(lcolor)", **OptionTranslator.scheme_colour_context(scheme))` and set `kw["line_color"]` when the hex is not `None`. `lpattern` and `lwidth` stay in the loop.
  - `_resolve_kpi_color` (P1.13.2, D-30g): (1) `translate_mcolor(raw)`, sanitised, as today. (2) `low = raw.lower()`, mapped through `_BRITISH_SPELLINGS`: a `_COLOR_MAP` key gives its hex sanitised; `#` plus three hex digits gives `low`; else `translate_mcolor(low)` (the grammar on lower-cased text). (3) The CSS branch, unchanged. Add a docstring paragraph: the card is dash's own, so it keeps its leniency.
- **TR-30.9 `SchemeParser`.**
  - **First statements of `_init_properties`:**
    - move S15's `self.naturally_white` assignment to be the first statement (whatever line it is on at the batch base);
    - set `self._colour_bg = None` and `self._colour_fg = None`;
    - `self.foreground_color: str = self._color("color foreground", "#000000")`;
    - `self.fg_lookup = self._named_lookup("color foreground", self.foreground_color, "#000000")`, then `self._colour_fg = self.fg_lookup`;
    - read `self.background_color` as today (absent default `#d9e8f0`);
    - `self.bg_lookup = self._named_lookup("color background", self.background_color, "#d9e8f0")`, then `self._colour_bg = self.bg_lookup`;
    - then every other key, as today.
  - **New `_named_lookup(self, key, resolved, absent) -> str | None`:** `absent` when the key is absent. `resolved` when the raw text (stripped) is an exact `_COLOR_MAP` key or `_HEX6_RE`-fullmatches (D-30e). Otherwise `None`.
  - **`_color_alpha(key, default, default_alpha)`:** absent gives `(default, default_alpha)`.
    - Otherwise `st, hx, a = OptionTranslator.stata_colour(raw, context="scheme", background=getattr(self, "_colour_bg", None), foreground=getattr(self, "_colour_fg", None), naturally_white=getattr(self, "naturally_white", True))`.
    - An `"unknown"` status warns once: `dash scheme: colour '<_dash_display(raw)>' (from '<key>') is not a colour; using black, as twoway does.` (stacklevel 3).
    - Return `(hx, a)`.
  - **`_color(key, default)`** is `self._color_alpha(key, default)[0]`.
  - Rewrite both docstrings: absent keys are silent inheritance; a present unknown name draws black with the note; a malformed number draws white silently, as twoway; `%NN` is kept by `_color_alpha` only.
  - `_stub_color_alpha`'s docstring: a present unreadable step draws what twoway draws (black or white), not the rest of the chain.
  - `_line_color`/`_band_color`: code unchanged.
  - `_FALLBACK_PROPS`: unchanged (`color foreground` is there; S15 added `system naturally_white`).
  - Update the comment at 6945-6947: `color foreground` is now read as `foreground_color` and is what `fg` means.
- **TR-30.10 The extractor** (scripts/extract_scheme_truth.py).
  - **`_apply_intensity(rgb, f, naturally_white=True)`:** E3's rule, with the clamp and the `naturally_white 0` product, the same as `GlyphMapper._blend_intensity`. The extractor stays standalone: no import of `dash_render`. The docstring cites E3 and the UNCLEAR navy*52.
  - **`ColorResolver.resolve_with_opacity`:**
    - names are looked up only when exactly lower case (Stata's 92 style files are), so a `Navy` token is unresolved;
    - CMYK and HSV go through private copies of TR-30.3, `_cmyk_hex` and `_hsv_hex` (keyword case-insensitive);
    - commas separate numbers;
    - `bg`/`fg` follow the named-lookup rule (a style name or hex in the scheme's raw text);
    - `naturally_white` is read from `self.r.get("system", "naturally_white")` (S15's key), default 1;
    - `*#` goes through `_apply_intensity`;
    - malformed and unknown tokens stay in `unresolved` and return `(None, None)`: the extractor reports, it does not guess, since Stata's shipped files contain neither.
  - Regenerate (A152): `python3 scripts/extract_scheme_truth.py` (all 26 shipped schemes). The expected diff is empty in every `dash-*.scheme` file, and in `test/fixtures/scheme_truth.json` outside `_meta`.
- **TR-30.11 dash.ado.**
  - In `_dash_option_rules`' `local plot` list, append `mcolor=colour mfcolor=colour mlcolor=colour mlabcolor=colour lcolor=colour fcolor=colour color=colour acolor=colour alcolor=colour bfcolor=colour blcolor=colour clcolor=colour`.
  - Add one sentence to the table's header comment: the `colour` kind refuses only a comma-written colour, as twoway does; everything else in a colour is the renderer's. Correct 1978-1983 for colours: an unknown colour is drawn black with the note.
  - In `_dash_validate_value` add a branch `else if "\`kind'" == "colour" {` that uses only ado string functions on scalar `T` plus Mata calls already in `_MATA_ALLOWED`:
    - strip one enclosing pair of double quotes (`char(34)`);
    - when the rest holds no further `"` and holds a comma at `p = ustrpos(…, ",")`, and the text after it does not start with `,`, take the word: after the first comma, with commas turned to blanks, `ustrtrim`, the first `word()`, cut to 80 characters, else `editcopy`;
    - print it with `mata: _dash_say("err", "invalid '", st_strscalar(st_local("W")), "' ")` and `exit 198`.

  No Mata function is added, so `_needed`, the Mata header and `program_coverage_map.py` are unchanged. S11's `_dash_stylelist_check` applies the rule to each element.
- **TR-30.12 Registries.**
  - Under `# WP-30 S30 (P1.13a): Stata colour grammar` in `test/function_test_map.py` `FUNCTIONS`, alphabetical, each mapped to its 30-01 node:
    - `OptionTranslator.__init__`, `OptionTranslator._colour_base`, `OptionTranslator._colour_cmyk`, `OptionTranslator._colour_hsv`, `OptionTranslator._colour_parts`;
    - `OptionTranslator.colour_context`, `OptionTranslator.scheme_colour_context`, `OptionTranslator.stata_colour`;
    - `SchemeParser._named_lookup`.
  - Existing keys keep their nodes, unless a flip renames one (F4), in which case it is repointed in place.
  - `test/test_option_validation.py` `KINDS` gains `"colour"`.
  - No copy-list change (R2 row S30) and no `program_coverage_map.py` change.
- **TR-30.13 Both modes.**
  - Colours are resolved at build in the saved renderer and at every `make_document` and recompute in the served app, by the same classes. No JS twin is needed: no saved-page `CustomJS` resolves a colour.
  - The KPI's JS rebuild writes `color`/`bgcolor` resolved at build by `_resolve_kpi_color` (31811-31814), and the served app re-resolves them per callback through `_dash_kpi_card_html`. Tests assert both are unchanged after a filter move.
- **TR-30.14 Security (rule 1).**
  - Input is bounded: 200 characters in `stata_colour`, 64 in `stata_number`. There is no backtracking regex (one anchored `fullmatch` on a fixed pattern), no `eval`, and no `float()` on raw text.
  - Every returned colour is `#[0-9a-f]{6}`. `css_block`'s colours are therefore hex, so a scheme cannot open a rule.
  - Echoes go through `_dash_display` (80 printable characters): the option note and, new, the scheme warning (unbounded at `c96facd`). The Stata refusal echoes at most 80 characters through `_dash_say` (SMCL-escaped).
  - The fixture extractor writes only under a `tempfile` directory in `c(tmpdir)`, with no `shell=True`. Its one `shell` call is `git -C "<root>" rev-parse HEAD`.

## Boundaries

- **S28 (batch 10):** `_build_sources_and_figures`, `_dash_facet_label`, `DashRenderer._facet_label`, the template's by() titles, `test_label_sinks.py`. Not touched.
- **S29 (batch 10):** `_apply_mlabel_opts`, `_mlabel_column_kind`, `_dash_finish_graph_text`, `_dash_graph_text` and its tables, help "Text in graphs". Not touched; `mlabcolor`'s unknown value stays S43's.
- **S43 (P1.13b, batch 15):**
  - a bare `*#`/`%#` at every site with the site's base colour (including `title(…, color(*.5))`, `graphregion(color(*.5))`, KPI, xline);
  - `%#` kept at every direct `translate_mcolor` site;
  - black for an unknown colour at those direct sites (D-30c list);
  - passing each figure's scheme to `_textbox_color`, `_dash_graph_color` and `_resolve_kpi_color`, which ends BR-30.13's interim;
  - a `base=` argument to `stata_colour`.

  S30 neither adds `base` nor edits any applier or mapper.
- **S08 (A37, ratification 06oct2026: fixed in WP-30).** S08 (batch 3) copies the styled properties to each renderer's `nonselection_glyph` and `muted_glyph` after the option appliers run, keeping dash's nonselection alpha, in both modes; P2.49 is not filed. S30 adds no styled property and no write site: its colours change the values the existing appliers write to `fill_color`, `line_color` and their alphas (and, through S16's blend, the fill), so they reach the brushed and muted copies through S08's sync. S30 adds no brushed-copy test: S08's brushed-copy tests cover colour, and 30-14 runs them.
- **S16:** `_blend_intensity` and `_apply_fill_opts` are called, not edited. **S08:** `stata_number` is called, not edited. **S15:** only `naturally_white`'s line moves (TR-30.9). **S24:** p#markfill/p#markline readers are not touched.
- **S31, S38, S39:** labcolor, axis-line, region (`_extract_region_*`, S38 replaces them) and refline sub-option colours build on this reader. The comma refusal inside sub-options (D-30f) is theirs or the closeout's.
- **S34:** third-party schemes along the ado-path. S30 reads whatever file `SchemeParser` is given.
- **Not edited:** `_make_figure_body`, `_generate_app_source`, `_build_filter_widgets`, the four appliers, every `map_*`, `_apply_colorvar`, `_histogram_quads`, `_means_no_color`, `_sanitize_css_color`, `_CSS_NAMED_COLORS`, the copy lists, `_FALLBACK_PROPS`, dash_parse.mata, any runner block or hygiene pin, and any tracking document beyond BUGS.md and CHANGELOG.md (A145).
- **Decisions applied:** M1 (twoway's look: black, white, intensity), M5 (the comma refusal in twoway's rc and words; nothing else refused), M6 (malformed numbers silent, as twoway), and register rows P1.13.1-P1.13.3, P1.13.5 (the `""` key), P1.13.6, P1.13.7 and IR-6.

## Stata truth

**New extractor** `scripts/extract_colour_grammar_truth.do` writes the **new fixture** `test/fixtures/colour_grammar_truth.json` (`git add -f`; `.git/info/exclude:58` ignores `*.json`).
- It copies S16's `scripts/extract_intensity_truth.do` form (S02's path-free form, A130, R7): the root is `DASH_REPO`, else `c(pwd)` when it holds `dash.ado` and `test/run_all_cscripts.do`, else `exit 601` with "set DASH_REPO to the dash repository".
- It opens with `adopath ++ "<root>/"` and `global dash_nobrowser 1`, then `version 19`, `set graphics off`, `set more off`.
- User schemes `scheme-cg<NN>.scheme` are written into a `tempfile`-named directory under `c(tmpdir)`, which is `adopath ++`'d and `cd`'d into for the scheme probes. Nothing is written into the repository except the fixture.
- Run: `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh $S $WT/scripts/extract_colour_grammar_truth.do` (log `$S/extract_colour_grammar_truth.log`). No other section runs it (R7).

**Method.**
- `sysuse auto, clear`; `gen lo = mpg - 3`; `gen hi = mpg + 3`.
- Each probe is `_cg_probe id context scheme kind command`. It runs `capture noisily <command>` inside `log using …, text`, records `_rc` and the log's `(note:` and `invalid '` lines, then `graph export "<dir>/<id>.svg", replace` when rc is 0.
- One closing `python:` block (no Stata call inside, no `shell=True`, a backtick written `\x60`) reads every SVG through `scripts/svg_truth.py`, by kind:
  - `marker`: `svg_marker_fills`, the dominant fill and its opacity;
  - `line`: the dominant stroke of `svg_lines` that is not an axis line;
  - `text`: the fill of the `svg_texts` entry whose text is `T`;
  - `region`: the first `rect` of `svg_fills(elements=("rect",))`;
  - `bar`: the dominant `rect` fill inside the plot region.

**Probes** (ids `<group>_<NN>`, numbered from 01 within each group in table order; the first `comma` probe is `comma_01`):

| Group | Command | Values |
|---|---|---|
| `opt` (marker, option) | `twoway scatter mpg weight, mcolor(<v>) scheme(s2color)` | every option-context value of E3, in E3's order (intensity, CMYK, HSV, bg/fg, unknown, malformed, opacity) |
| `s1r` (marker) | the same, `scheme(s1rcolor)` | `navy*.5`, `navy*1.5`, `fg`, `bg`, `fg*.5`, `bg*.5`, `"hsv 240 1 1*.5"`, `"0 0 0 128"` |
| `bgs` (marker) | the same, `scheme(stcolor)` and `scheme(economist)` | `bg`, `fg` |
| `sch` (marker, scheme) | `twoway scatter mpg weight, scheme(cg<NN>)`, the file `#include s2color` plus `color p1 <v>` | every scheme-context value of E3 |
| `bgfg` | the files of E3's bg/fg block (t01-t06, t20, t21, sa-sd, si, and sj recorded but excluded) | marker and region |
| `site` | `line mpg weight, lcolor(navy*.5)`; `line mpg weight, lcolor(bogus)`; `bar mpg rep78 if rep78<., lcolor(none) fcolor(bogus)`; `bar mpg rep78 if rep78<., lcolor(none) color(navy*.5)`; `scatter mpg weight, title("T", color(bogus))`; `scatter mpg weight, title("T", color(navy*.5))`; `scatter mpg weight, xline(3000, lcolor(bogus))`; `scatter mpg weight, graphregion(color(bogus))`; `scatter mpg weight, mlabel(make) mlabcolor(bogus)` (`"owner": "S43"`); `bar …, color(bogus)` (`"owner": "S43"`) | line / bar / text / region kinds |
| `comma` (refusal) | `twoway scatter mpg weight, mcolor(<v>)` and `lcolor` on `line` | `"255,0,128"`, `"255, 0, 128"`, `"1,2,3"` (lcolor), `"red,blue"`, `"1,"`, `"1,,2"`, `bgcolor("1,2,3")` |

**Fixture keys.**

```
{"_meta": {"stata_version", "born_date", "dash_commit", "extracted",
           "excluded": {<id of the opt probe navy*52>: "UNCLEAR clamp at an exact half (research p1-13 section 3)",
                        <id of the bgfg probe sj>: "UNCLEAR: color foreground bg after color background red"}},
 "probes": {id: {"group", "context", "scheme", "value", "command", "rc", "notes", "refusal",
                 "fill", "opacity", "owner"}}}
```

- `dash_commit` comes from `shell git -C "<root>" rev-parse HEAD > <tempfile>`, read back with `file read` and reaching Python through `Macro.getLocal` (D12).
- The excluded probes are still run and recorded, never asserted.
- A recorded value that differs from E3 is investigated and reported, never patched (R7).

**Truth block** (`test/test_wp30_truth.cscript`, S30's stub between `* ==== S30 P1.13a: Stata colour grammar ====` and `* ==== end S30 ====`; gate `local only : env WP30_ONLY` then `` if inlist("`only'", "", "S30") { ``).
- Helpers go directly above S30's header, outside every gate. They are copies of S16's `_s16_page`, `_s16_app` and `_s16_svg` renamed `_s30_*` (`version 19`).
  - `_s30_page` and `_s30_app` return `S30_FILLS`: for every glyph renderer in document order, `Type:fill_color:fill_alpha:line_color`, joined by `;`. They also return the figure's `border_fill_color` and the title's `text_color`.
  - `_s30_app` adds `S30_SAME_AFTER` after a `Select` move on `foreign` to `Foreign`.
  - `_s30_svg` wraps `cert_svg_fills`.
- Each case runs twoway and dash on the same command, saving with `saving(<w30_work>/s30.html, replace)` and building with `dash build, server` into `w30_work`, and checks through `_w30_expect`/`_w30_done`:

| Case | Check |
|---|---|
| CG-10 | s2color `scatter mpg weight, mcolor(V)`, V in `navy*.5`, `navy*100`, `"85 40 0 144"`, `"hsv 209 .766 .435"`, `bg`, `fg`, `navy*.5%50`: twoway's fill (and opacity) equals the saved and served Scatter's `fill_color`/`fill_alpha` |
| CG-11 | `mcolor(bogus)`, `mcolor(Navy)`, `mcolor(grey)`, `mcolor("300 0 0")`: twoway and dash both `#000000`; twoway's log holds `named style`; dash's log holds exactly one `(note:` line naming `mcolor(` |
| CG-12 | `mcolor(red*abc)`, `mcolor("#F00")`: both draw `#1A476F` and neither log holds a colour note |
| CG-13 | s1rcolor `mcolor(navy*.5)`, `mcolor(fg)`: equal in both modes |
| CG-14 | a user scheme (`#include s2color`, `color p1 navy*.5`, `color p2 "hsv 240 1 1"`, `color background bogus`), command `(scatter mpg weight) (scatter price weight, yaxis(2))`: both markers and the graph region equal twoway's in both modes |
| CG-15 | `bar …, fcolor(bogus)` `#333333`; `line …, lcolor(navy*.5)`; `title("T", color(bogus))`; `xline(3000, lcolor(bogus))`: equal in both modes |
| CG-16 | `S30_SAME_AFTER` = 1 for CG-10's `navy*.5` and CG-14's scheme |

**Area script cases** (refusals and messages; R1: one contiguous run in `test/test_option_validation.cscript`, directly before the comment that opens the `CV-nn` corpus block, after every earlier section's run). Helpers `_cg_case` (a copy of `_ov_case`, 440-464, registering `cg` plus the id's digits) and `_cg_refused` (a copy of `_ov_refused`, 503-, also asserting `dash_json_cg<NN>` is empty) sit directly above the run.

| Case | Command | Expect |
|---|---|---|
| CG-01 | `dash scatter mpg weight, mcolor("255,0,128") name(cg01)` | rc 198, log says `invalid '0'`, nothing registered |
| CG-02 | `dash line mpg weight, lcolor("1,2,3") name(cg02)` | rc 198, `invalid '2'` |
| CG-03 | `dash scatter mpg weight, mcolor("red,blue") name(cg03)` | rc 198, `invalid 'blue'` |
| CG-04 | `dash scatter mpg weight, mcolor("1,") name(cg04)` | rc 198, `invalid 'editcopy'` |
| CG-05 | `dash scatter mpg turn weight, mcolor(red "255,0,0") name(cg05)` | rc 198, `invalid '0'` |
| CG-06 | `dash scatter mpg weight, mcolor("1,,2") name(cg06)` | rc 0, registered (the renderer notes it) |
| CG-07 | `dash scatter mpg weight, bgcolor("1,2,3") name(cg07)` | rc 0 (twoway accepts it) |
| CG-08 | `dash scatter mpg weight, mcolor(navy*.5) name(cg08)` | rc 0, the spec carries `"mcolor":"navy*.5"` |

## TDD test stubs

**Regression tests written by 30-01** (`test/test_colour_grammar.py`).
- Each fails at the batch-10 base; the expected failure is given in brackets.
- Expectations are E3's literal hex, never computed through `dash_render`.
- Modes go through `test_scheme_resolution._draw` and `MODES`. Specs go through `test_mode_parity._spec`, and moves through `test_mode_parity._served_after_move`.
- User schemes are written into `tmp_path` under `monkeypatch.chdir`.
- Notes are counted with S06's needle helpers.

- Test: every option-context value of E3 gives its `(status, hex, alpha)` — `test/test_colour_grammar.py::TestStataColourOption::test_the_measured_option_values` [AttributeError: stata_colour]
- Test: CMYK proportions, integers and refusals — `…::TestStataColourOption::test_cmyk` [AttributeError]
- Test: HSV, wrap, case-insensitive keyword, refusals — `…::TestStataColourOption::test_hsv` [AttributeError]
- Test: every scheme-context value of E3 — `…::TestStataColourScheme::test_the_measured_scheme_values` [AttributeError]
- Test: naturally_white 0 multiplies (E3's five) — `…::TestNaturallyWhiteZero::test_s1rcolor_multiplies` [AttributeError]
- Test: `_colour_parts` either order, empty `*`/`%`, `*.5*2` — `…::TestTheParts::test_either_order` [AttributeError]
- Test: `translate_mcolor` returns the grammar's hex (`navy*.5` `#8da3b7`, `"0 0 0 255"`, `"hsv 240 1 1"`, `#FF0000` → `#ff0000`) — `…::TestTheTranslatorsDelegate::test_translate_mcolor_returns_the_grammars_hex` [ValueError]
- Test: `translate_mcolor` raises "Unknown Stata color" for `Navy`, `grey`, `bogus`, `#f00`, `255,0,128`, `%50`, `""`, `red*abc`, 10,000 characters — `…::test_translate_mcolor_refuses_what_it_cannot_draw` [no raise for Navy]
- Test: `parse_color_alpha` draws an unknown black, with "dash: mcolor(bogus) is not a recognised colour; using black." (`Red*.5` `#808080`, `Red%50` black at 0.5), silent without an option — `…::test_parse_color_alpha_draws_an_unknown_colour_black` [(None, None)]
- Test: `#F00`, `red%150`, `red*abc`, `*abc`, `""` give `(None, None)` with no warning — `…::test_parse_color_alpha_keeps_the_default_in_silence` [('#f00', None)]
- Test: `translate_lcolor` passes the context — `…::test_translate_lcolor_passes_the_context` [TypeError]
- Test: `GlyphMapper(scheme=SchemeParser("s1rcolor")).tr`: `fg` `#ffffff`, `navy*.5` `#0d2438` — `…::TestTheMapperReadsItsScheme::test_a_bound_translator_reads_its_scheme` [ValueError]
- Test: swapping `mapper.scheme` changes what `bg` means — `…::test_a_graphs_own_scheme_is_read` [ValueError]
- Test: an `OptionTranslator()` passed in is replaced by a bound one; any other object is kept — `…::test_a_plain_translator_is_bound_and_another_object_kept` [AttributeError]
- Test: `scheme_colour_context(SchemeParser("s2color"))` is `{"background": "#eaf2f3", "foreground": "#000000", "naturally_white": True}`, `{}` for None — `…::test_the_context_of_a_scheme` [AttributeError]
- Test: each scheme-file row of E3 (p1, background, heading, plotregion, p1lineplot, p1bar) — `…::TestSchemeFiles::test_each_scheme_row` [p1 #000000 for navy*.5]
- Test: `foreground_color` s2color `#000000`, s1rcolor `#ffffff`, a user `color foreground red` `#ff0000` — `…::test_foreground_is_read` [AttributeError]
- Test: `bg`/`fg` are a named lookup (E3's t01-t06, t20, t21, sa-sd, si; `bg_lookup`/`fg_lookup`) — `…::test_bg_and_fg_are_a_named_lookup` [AttributeError]
- Test: an unreadable key draws black with exactly one warning per key naming key and value — `…::test_an_unreadable_key_draws_black_with_one_note` [background #d9e8f0]
- Test: `#}a{b;c`, `navy*abc`, `%50` draw white (at 0.5 for `%50`) with no warning — `…::test_a_malformed_value_draws_white_in_silence` [#d9e8f0 and a warning]
- Test: `color p1 Navy`, `color p2 RED` draw black with a warning each — `…::test_names_are_case_sensitive` [#1a476f]
- Test: `_textbox_color`: bogus `#000000` with the "using black." note; `#F00` None silently; `navy*.5` `#8da3b7` — `…::TestModuleReaders::test_textbox_colour` [None and "ignoring it"]
- Test: `_dash_graph_color`: bogus `#000000` with the note; `#F00` `""` silently — `…::test_graph_colour` [""]
- Test: `xline(3000, lcolor(bogus))` Span `#000000` with "dash: xline(lcolor(bogus)) is not a recognised colour; using black."; `lcolor(fg)` under s1rcolor `#ffffff` — `…::test_refline_colour` [the scheme's xyline colour]
- Test: the KPI reads the grammar: `navy*.5` `#8da3b7`, `"hsv 240 1 1"` `#0000ff` — `…::TestTheKpiKeepsItsLeniency::test_the_kpi_reads_the_grammar` [the default]
- Test [both modes]: scatter `mcolor()` of `navy*.5`, `"85 40 0 144"`, `"hsv 240 1 1"`, `bg`, `bogus` (`#000000`), `Navy` (`#000000`), `red*abc` (the scheme's p1), `navy*.5%50` (alpha 0.5): the saved and served fill equal the literal, and the notes are identical — `…::TestBothModes::test_scatter_forms` [the scheme's p1]
- Test [both modes]: `line lcolor(navy*.5)` `#8da3b7`; `bar fcolor(bogus)` `#333333`; `bar color(navy*.5)` `#a4b5c5` — `…::TestBothModes::test_line_and_bar` [scheme colours]
- Test [both modes]: s1rcolor `mcolor(fg)` `#ffffff`, `mcolor(navy*.5)` `#0d2438` — `…::TestBothModes::test_s1rcolor` [p1]
- Test [both modes]: a user scheme (`color p1 navy*.5`, `color background bogus`): marker `#8da3b7`, figure `border_fill_color` `#000000` — `…::TestBothModes::test_a_user_scheme` [#000000 marker / #d9e8f0]
- Test [served, after a move]: CG-10's forms and CG-14's scheme draw the same fills after a `Select` move — `…::TestAfterAFilterMove::test_the_served_app_redraws_the_same_colours` [p1 before and after]
- Test [saved]: the KPI callback config's `color` is the build-resolved, sanitised colour of `navy*.5`, and no `CustomJS` arg or code holds the text `navy*.5` — `…::TestAfterAFilterMove::test_the_saved_page_writes_only_build_colours` [the default]
- Test: hostile inputs (10,000 characters, `*nan`, `*inf`, `*1e400`, 500 `*`, `%%%`, `#}a{b;c`, Arabic-Indic digits, NUL) in both contexts give a `#[0-9a-f]{6}` or None and one of the three statuses, never an exception — `…::TestOutputIsAlwaysHex::test_hostile_inputs` [AttributeError]
- Test: a 10,000-character scheme value gives a warning shorter than 400 characters — `…::test_a_long_scheme_value_is_named_briefly` [the full value echoed]
- Test: the extractor's `_apply_intensity` equals `GlyphMapper._blend_intensity` on a grid (c in 0, 1, 26, 71, 111, 128, 255; f in 0, .01, .5, 1, 1.5, 2, 10, 51, 100, 255; both `naturally_white`) — `…::TestExtractorAgrees::test_the_intensity_rule` [no clamp at f 100]
- Test: the extractor's `ColorResolver` reads E3's scheme-context `ok` values that need no bg/fg as `stata_colour` does (skipped with a reason if Stata's base is absent, as test_scheme_fidelity's extractor tests are) — `…::TestExtractorAgrees::test_the_resolver` [CMYK unresolved]
- Test: dash.ado's plot rules carry the twelve `=colour` tokens and `_dash_validate_value` a `colour` branch — `…::TestTheCommaIsRefusedInStata::test_the_rules_name_the_colour_kind` [absent]
- Test: `""`, `grey`, `dimgrey`, `bluishgrey`, `ltbluishgrey` are not keys of `_COLOR_MAP`; `_BRITISH_SPELLINGS` maps them to the US names — `…::TestTheBritishSpellingsAreNotStataNames::test_not_in_the_table` [present]

**Guard tests** (pass before and after, recorded in the failure file under "Guards"):
- Test: KPI values accepted at `c96facd` are unchanged: `Navy` `#1a476f`, `grey` `#808080`, `dimgrey` `#e8e8e8`, `bluishgrey` `#d9e6eb`, `ltbluishgrey` `#eaf2f3`, `#FFF` `#fff`, `rebeccapurple`, `rgb(1,2,3)`, `navy` `#1a476f` — `…::TestTheKpiKeepsItsLeniency::test_values_accepted_today_are_unchanged`
- Test: an absent `color background` keeps `#d9e8f0`, and `SchemeParser.fallback()`'s `background_color` and `title_color` equal `SchemeParser("s2color")`'s — `…::TestSchemeFiles::test_absent_keys_keep_their_defaults`

**Written by 30-02:** `…::TestStataTruth::test_each_probe` (every non-excluded, non-S43 probe: the reader's answer in its context and scheme equals the fixture's fill and opacity, and a refusal probe's `refusal` is the Stata words of BR-30.7; this fails until 30-06) and `…::TestStataTruth::test_the_meta_stamp` (the four D12 keys).

**Flipped (E6):** F1-F21 by 30-08 (F10, F11, F13) and 30-11 to 30-14, each with a `Flipped:` line.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Grammar, 175 measured values, hostile inputs | pytest `TestStataColourOption`, `TestStataColourScheme`, `TestNaturallyWhiteZero`, `TestTheParts`, `TestOutputIsAlwaysHex` | E3 literals | n/a (pure) |
| Readers and the bound translator | pytest `TestTheTranslatorsDelegate`, `TestTheMapperReadsItsScheme` | — | n/a |
| Scheme files | pytest `TestSchemeFiles` | user schemes in `tmp_path` | parser shared |
| Module readers and KPI | pytest `TestModuleReaders`, `TestTheKpiKeepsItsLeniency` | — | KPI in both |
| Drawn colours | pytest `TestBothModes`, `TestAfterAFilterMove` | — | yes, and after a move |
| Stata truth | pytest `TestStataTruth` | `colour_grammar_truth.json` | reader shared |
| Live twoway against both modes | `test_wp30_truth.cscript` S30 block, CG-10..CG-16, `WP30_ONLY=S30` | live SVG | yes, and after a served move |
| The comma refusal | `test_option_validation.cscript` CG-01..CG-08; `test_help_claims_2.cscript` HC2-16p/q | — | Stata side |
| Extractor | pytest `TestExtractorAgrees`; regeneration diff | `scheme_truth.json` | n/a |
| Parity corpus | pytest `test_mode_parity.py` (four new `CORPUS` cases) | — | yes |
| Registries | `test_function_test_map.py`, `test_option_validation.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` | — | — |

**Acceptance criteria.**
- **AC-30.1** Every E3 value (175, the two UNCLEAR excluded) is returned by `stata_colour` in its context, and every non-excluded, non-S43 probe of `colour_grammar_truth.json` matches in `TestStataTruth`.
- **AC-30.2** In both modes and after a served move, `mcolor(navy*.5)` draws `#8da3b7`, `mcolor(bogus)` `#000000` with one note, `mcolor(red*abc)` the scheme's p1 silently, `bar …, fcolor(bogus)` `#333333`, and s1rcolor `mcolor(fg)` `#ffffff`. CG-10..CG-16 print PASS.
- **AC-30.3** `dash scatter mpg weight, mcolor("255,0,128")` stops with `invalid '0'` and r(198), registering nothing. CG-01..CG-08 and HC2-16p/q pass.
- **AC-30.4** A user scheme's `color background bogus` draws a black graph region with one note. `#}a{b;c` draws white silently, and the CSS block holds only hex.
- **AC-30.5** Every KPI value accepted at `c96facd` draws the same colour (the guard).
- **AC-30.6** Regenerating the shipped files changes nothing outside `scheme_truth.json`'s `_meta`. `TestExtractorAgrees` passes.
- **AC-30.7** F1-F21 and every node in `$S/30-flips.txt` are flipped with their reasons, and none is deleted. The full suite is green once through the queue.

## Tasks

**Commit boundary.** All seventeen tasks are steps of one commit, `Read Stata's colour grammar in options and scheme files (WP-30 P1.13a)`, made by 30-17 on `wp30-s30`. The body opens with the contents of `<scratch>/30-P1.13a-failure.txt` (index step 1's place), followed by:
- the measured defect (Overview);
- what changed, and where (TR-30.1 to TR-30.11);
- one `Regression: test/test_colour_grammar.py::<Class>::<test> -- failed at <base sha> with <text>` line per regression class;
- the `Flipped:` lines of `$S/30-flips.txt`;
- `Fixture: test/fixtures/colour_grammar_truth.json (scripts/extract_colour_grammar_truth.do)`;
- `Regenerated: dash-*.scheme and test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py; no change outside _meta)`;
- `BUGS.md: "<WP30_OPEN["P1.13a"]>" (closed)`, the entry's title as section-01 Appendix B writes it (not the section name).

`WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s30` and `S=<scratch>/s30`, where `<scratch>` is the orchestrator's WP-30 scratch directory (index: Deltas).

<task type="auto" id="30-01">
  <name>Write the failing colour grammar tests</name>
  <files>test/test_colour_grammar.py</files>
  <action><![CDATA[
    Run `mkdir -p "$S"`. Check that `git -C $WT rev-parse HEAD` equals `<scratch>/batch-10-base.txt` and that `git -C $WT branch --show-current` prints `wp30-s30`; otherwise stop. Read `<scratch>/batch-10-impact.txt` and confirm that it records E7's HIGH/CRITICAL warnings with their approval. If one is missing, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout (never in $WT), append it, and report it before any edit.

    Check the prerequisites by grep in $WT, and stop and report if any is missing:
    - `def stata_number` in OptionTranslator (S08);
    - `self.naturally_white` assigned in `SchemeParser._init_properties` (S15), and `system naturally_white 0` in `dash-s1rcolor.scheme`;
    - `def _blend_intensity(hexval, f, naturally_white` (S16);
    - no read of `color p{i}mark` in `_init_properties` (S24);
    - `def _dash_emit_note` (S06).

    Create test/test_colour_grammar.py with every regression and guard test of "TDD test stubs", with exactly those class and test names and the helpers named there. The `TestStataTruth` class is not written here; 30-02 writes it. Parametrise the E3 tables as module constants `OPTION_TRUTH`, `SCHEME_TRUTH` and `BGFG_TRUTH`, each row `(value, status, hex, alpha)` with E3's literal hex. Mark the two UNCLEAR rows absent, with a comment giving the reason.

    Run `python3 -m pytest test/test_colour_grammar.py -q -n0 -p no:cacheprovider -rf > "$S/30-01.log" 2>&1`. Write `<scratch>/30-P1.13a-failure.txt`, holding:
    - the base sha;
    - each FAILED node with its first assertion or exception line;
    - under "Guards (pass before and after)", the two guard nodes, passing.

    Do not touch any other file. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/30-01.log"` is at least 35; `grep -E 'test_values_accepted_today_are_unchanged|test_absent_keys_keep_their_defaults' "$S/30-01.log" | grep -c FAILED` prints 0; `git -C $WT status --porcelain` lists only `?? test/test_colour_grammar.py`.]]></verify>
  <done>Every regression test of the section existed and failed on the unmodified tree for the stated reason, the guards passed, and the failure text was saved.</done>
</task>

<task type="auto" id="30-02">
  <name>Extract the colour grammar truth fixture</name>
  <files>scripts/extract_colour_grammar_truth.do, test/fixtures/colour_grammar_truth.json, test/test_colour_grammar.py</files>
  <action><![CDATA[
    Create scripts/extract_colour_grammar_truth.do as "Stata truth" specifies:
    - S16's extractor form, with `adopath ++` then `global dash_nobrowser 1`, `version 19`, `set graphics off`, `set more off`;
    - user schemes written only under a tempfile-named directory in c(tmpdir);
    - the `_cg_probe` program;
    - the probe groups `opt`, `s1r`, `bgs`, `sch`, `bgfg`, `site` and `comma`, in the order of the table;
    - one closing python block that reads the SVGs through scripts/svg_truth.py by kind and writes test/fixtures/colour_grammar_truth.json with the `_meta` stamp (D12) and the two exclusions.

    Run `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_colour_grammar_truth.do"`. Read the log. A python_exec drop (a SKIP or r(222)) is restored and re-run, because a skip is not a pass.

    Compare every probe with E3. A difference is investigated, reported and recorded in `$S/30-truth-diff.txt`, and never patched (R7). Add the class `TestStataTruth` (test_each_probe, test_the_meta_stamp) to test/test_colour_grammar.py: it skips probes with `owner` S43 and the two exclusions, and asserts a refusal probe's `refusal` text and rc 198. Then run `git -C $WT add -f test/fixtures/colour_grammar_truth.json`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('$WT/test/fixtures/colour_grammar_truth.json'));print(all(k in d['_meta'] for k in ('stata_version','born_date','dash_commit','extracted')), len(d['probes']) > 200, d['probes']['comma_01']['rc'])"` prints `True True 198`; `$S/30-truth-diff.txt` is empty or every line is explained; `python3 -m pytest test/test_colour_grammar.py::TestStataTruth::test_the_meta_stamp -q -n0 -p no:cacheprovider` passes and `::test_each_probe` fails (the reader is not built yet).]]></verify>
  <done>StataNow 19.5's answer for every colour form the section reads was recorded in a stamped, force-added fixture that agreed with Evidence E3, and a test read it.</done>
</task>

<task type="auto" id="30-03">
  <name>Add the grammar to OptionTranslator</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    In OptionTranslator (class at 5098 at c96facd):
    - apply TR-30.1: delete the `""` and British entries of `_COLOR_MAP`, and add `_BRITISH_SPELLINGS`, `_COLOUR_TEXT_MAX`, `_HEX6_RE`, `_FALLBACK_BG` and `_FALLBACK_FG`, each with a comment citing E3 or IR-6;
    - after `_means_no_color`, add the static methods `_colour_parts`, `_colour_cmyk`, `_colour_hsv`, `_colour_base` and `stata_colour`, exactly as TR-30.2 to TR-30.5 define them.

    Each docstring states the rule, and the measured examples of E3 it is checked against. `stata_colour`'s docstring also gives the three statuses, the two contexts, the UNCLEAR navy*52 and that the bare *# base is S43's. Numbers are read only through `OptionTranslator.stata_number`, and intensity only through `GlyphMapper._blend_intensity(hx, f, bool(naturally_white))`.

    Do not change `translate_mcolor`, `parse_color_alpha` or `translate_lcolor` yet. Add the five `OptionTranslator._colour_*` keys and `OptionTranslator.stata_colour` under the `# WP-30 S30 (P1.13a): Stata colour grammar` anchor of test/function_test_map.py, alphabetically, mapped to their 30-01 nodes.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_colour_grammar.py -q -n0 -p no:cacheprovider -k "TestStataColourOption or TestStataColourScheme or TestNaturallyWhiteZero or TestTheParts or TestOutputIsAlwaysHex or TestTheBritishSpellings"` passes; `python3 -m pytest test/test_function_test_map.py test/test_color_fidelity.py::TestEveryStataColourIsTheColourStataDraws -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>One pure reader answered every measured colour form in option and scheme context, held to Stata's 92 names, and was mapped to its tests.</done>
</task>

<task type="auto" id="30-04">
  <name>Delegate the readers and bind the mapper</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Rewrite `translate_mcolor`, `translate_lcolor` and `parse_color_alpha` as TR-30.6 says: they delegate to `stata_colour`, keep their signatures, add `**ctx`, keep the "Unknown Stata color" message, and send the unknown note through `_dash_style_note(option, value, "colour", "black")`. Add `OptionTranslator.__init__`, `colour_context` and `scheme_colour_context` (TR-30.7), with lambdas only, and update the class docstring.

    In `GlyphMapper.__init__` replace `self.tr = translator or OptionTranslator()` (7941) by TR-30.7's rule, with a comment citing D-30b and the per-graph swap of `DashRenderer` (30186-30193). Run `grep -n "deepcopy\|pickle" dash_render.py` and confirm that no mapper or translator is copied; report it if one is.

    Add `OptionTranslator.__init__`, `OptionTranslator.colour_context` and `OptionTranslator.scheme_colour_context` to the S30 anchor of test/function_test_map.py. Run test/test_colour_grammar.py, then test/test_options.py, test/test_color_alias.py, test/test_glyphs.py and test/test_option_validation.py into `$S/30-04.log`. The reds expected here are F1-F5 and F9. Any other red is recorded in `$S/30-flips.txt` (TR-30.12's classification) or corrected.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_colour_grammar.py -q -n0 -p no:cacheprovider -k "TestTheTranslatorsDelegate or TestTheMapperReadsItsScheme"` passes; `python3 -c "import dash_render as d; g=d.GlyphMapper(scheme=d.SchemeParser('s1rcolor')); print(g.tr.translate_mcolor('navy*.5'), g.tr.parse_color_alpha('bogus'))"` prints `#0d2438 ('#000000', None)`.]]></verify>
  <done>Every applier and mapper read the grammar with its own graph's scheme through the bound translator, an unknown colour from an applier was drawn black with the note, and no applier or mapper was edited.</done>
</task>

<task type="auto" id="30-05">
  <name>Read scheme colours with the grammar</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-30.9 in SchemeParser:
    - the new first statements of `_init_properties` (move S15's `naturally_white` line first; `_colour_bg`/`_colour_fg`; `foreground_color` and `fg_lookup`; `background_color` and `bg_lookup`);
    - the new `_named_lookup`;
    - `_color_alpha` through `OptionTranslator.stata_colour(raw, context="scheme", …)`, with the bounded warning "dash scheme: colour '<v>' (from '<key>') is not a colour; using black, as twoway does.";
    - `_color` as `_color_alpha(...)[0]`;
    - the docstrings of `_color`, `_color_alpha` and `_stub_color_alpha`, and the comment at 6945-6947.

    Leave `_line_color`, `_band_color` and `_FALLBACK_PROPS` untouched. Add `SchemeParser._named_lookup` to the S30 anchor of test/function_test_map.py, and repoint the existing `SchemeParser._color` key (260 at c96facd) to `test/test_colour_grammar.py::TestSchemeFiles::test_an_unreadable_key_draws_black_with_one_note`, because F19 renames its old node in 30-14.

    Confirm that the served rebuild (`_dash_build_scheme`: `__new__`, `_props`, `_init_properties()`) sets every new attribute: build an app with ServerAppBuilder for a spec under s1rcolor, and read `_DASH_SCHEME.fg_lookup` from the module (expect `#ffffff`).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_colour_grammar.py -q -n0 -p no:cacheprovider -k "TestSchemeFiles or test_a_long_scheme_value"` passes; `python3 -m pytest test/test_scheme_fidelity.py test/test_scheme_resolution.py test/test_scheme_fallback_provenance.py test/test_scheme_consumption.py -q -n 6 -p no:cacheprovider` passes except nodes recorded in `$S/30-flips.txt`.]]></verify>
  <done>Scheme files were read with Stata's colour grammar, the foreground and the bg/fg lookups were parsed in Stata's order, and an unreadable value drew what twoway draws for that key.</done>
</task>

<task type="auto" id="30-06">
  <name>Draw unknown colours black at module readers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-30.8:
    - `_textbox_color` through `parse_color_alpha(str(raw), "color")`;
    - `_dash_graph_color` through `parse_color_alpha(str(raw), option)`, returning `hx or ""`;
    - `_dash_refline_draw`'s `lcolor` read before the loop, with the scheme's context, the loop keeping `lpattern` and `lwidth`;
    - `_resolve_kpi_color`'s case-insensitive Stata lookup ahead of CSS (British spellings, 3-digit hex lower-cased, the grammar on the lower-cased text).

    Each docstring states the twoway rule it follows and what S43 adds. All four functions are already on the served copy lists (33360, 33383, 33393; `_dash_graph_color` in `_shared_stat_lines` 33542), so no list changes; confirm with `python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_colour_grammar.py -q -n 6 -p no:cacheprovider` passes except `TestExtractorAgrees` and `TestTheCommaIsRefusedInStata` (later tasks); `TestStataTruth::test_each_probe` passes.]]></verify>
  <done>Titles, graph and plot regions and reference lines drew an unknown colour black with the note in both modes, and the KPI kept every colour it drew before while gaining the grammar.</done>
</task>

<task type="auto" id="30-07">
  <name>Refuse comma colours in dash.ado</name>
  <files>dash.ado, test/test_option_validation.py, test/test_option_validation.cscript</files>
  <action><![CDATA[
    Apply TR-30.11 in dash.ado:
    - the twelve `=colour` tokens at the end of `_dash_option_rules`' `local plot`;
    - the header-comment sentence, and the correction of 1978-1983;
    - the `colour` branch of `_dash_validate_value`, using ado string functions and allowed Mata only, opening no new program.

    Add `"colour"` to `KINDS` in test/test_option_validation.py, with a comment naming WP-30 P1.13a.

    In test/test_option_validation.cscript add the helpers `_cg_case` and `_cg_refused` and the cases CG-01..CG-08 of "Area script cases", as one contiguous run directly before the comment that opens the CV corpus block. Update the script's `*!` header list with the eight cases.

    Run test/test_option_validation.py. Then run the script through the driver from the worktree: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_option_validation.cscript > "$S/run_test_option_validation.do"` and `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_option_validation.do"`.
  ]]></action>
  <verify><![CDATA[The log `$S/run_test_option_validation.log` prints `CG-01 PASS` .. `CG-08 PASS` and `test_option_validation: ALL CHECKS PASSED`; `python3 -m pytest test/test_option_validation.py -q -n 6 -p no:cacheprovider -k "TestTheTableIsWellFormed or TestEveryRuledOptionIsOneAParserDeclares or TestTheNewProgramsKeepTheirConstraints"` passes; `python3 -m pytest test/test_colour_grammar.py::TestTheCommaIsRefusedInStata -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>A comma-written plot colour was refused before any Python ran, in twoway's words and return code, element by element, and everything else in a colour stayed the renderer's to read.</done>
</task>

<task type="auto" id="30-08">
  <name>Flip HC2-16 and its Python twin</name>
  <files>test/test_help_claims_2.cscript, test/test_help_claims_2.py</files>
  <action><![CDATA[
    In test/test_help_claims_2.cscript:
    - flip HC2-16p (555) to `_hc2_dash "HC2-16p" 198 ... "invalid '0'"`;
    - replace HC2-16q's `_hc2_reg` (556) by an inline verdict through `_hc2_ok`, true when `st_global("dash_json_hc")` is empty ("no graph hc is registered"), in `_hc2_reg`'s mata form;
    - update the block's comment ("values twoway refuses and dash accepts" no longer covers HC2-16o-q, so say "and refuses, as twoway").

    In test/test_help_claims_2.py:
    - rename `TestAColourWrittenWithCommasIsReadAsTheTriplet` to `TestAColourWrittenWithCommasIsRefusedInStata` and its test to `test_a_hand_written_spec_is_noted_and_drawn_black`; it asserts `#000000` in both modes and exactly one note naming `mcolor(255,0,0)`, identical in both, and its docstring cites HC2-16o/p and the r(198);
    - flip F13: in `TestAnUnknownStyleInsideAStructuredOption::test_one_note_and_the_schemes_default_in_both_modes`, for a `color(...)` sub-option assert `#000000` in both modes (the size rows unchanged). Rename the test in place to `test_one_note_and_twoways_default_in_both_modes` and correct its docstring and assertion messages to say an unknown colour is black.

    Run the script through the driver as in 30-07, then the Python file. Append the `Flipped:` lines of F10, F11 and F13 to `$S/30-flips.txt`.
  ]]></action>
  <verify><![CDATA[The driver log prints HC2-16p and HC2-16q passing and `ALL` passed for test_help_claims_2; `python3 -m pytest test/test_help_claims_2.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>The help-claims pins said what dash now does with a comma-written colour, in Stata and in a hand-written spec, and with an unknown colour inside a title.</done>
</task>

<task type="auto" id="30-09">
  <name>Bring the extractor to the grammar</name>
  <files>scripts/extract_scheme_truth.py, test/test_colour_grammar.py</files>
  <action><![CDATA[
    Apply TR-30.10 to scripts/extract_scheme_truth.py:
    - `_apply_intensity(rgb, f, naturally_white=True)` with the clamp and the product rule, its docstring citing E3;
    - in `ColorResolver.resolve_with_opacity`: exact lower-case names; the private `_cmyk_hex` and `_hsv_hex`; comma separators; the named bg/fg lookup; `naturally_white` from `self.r.get("system", "naturally_white")`; malformed and unknown tokens kept in `unresolved`.

    The script must still not import dash_render. Complete `TestExtractorAgrees` in test/test_colour_grammar.py if 30-01 left a placeholder for its resolver fixture. Run it and test/test_scheme_fidelity.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_colour_grammar.py::TestExtractorAgrees test/test_scheme_fidelity.py -q -n 6 -p no:cacheprovider` passes; `grep -c "import dash_render\|from dash_render" scripts/extract_scheme_truth.py` prints 0.]]></verify>
  <done>The extractor read Stata's scheme files with the renderer's intensity rule, CMYK, HSV and case-sensitive names, proven equal by test.</done>
</task>

<task type="auto" id="30-10">
  <name>Regenerate the shipped schemes and fixture</name>
  <files>dash-*.scheme (the 26), test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    In $WT run `python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json > "$S/30-regen.log" 2>&1` (`--out` is required; the default `--schemes` list and `--schemes-dir` regenerate every shipped `dash-*.scheme` file, 26 after S07; `--stata-base` defaults to StataNow's `ado/base`), the command S33 uses.

    `git -C $WT diff --stat -- 'dash-*.scheme' test/fixtures/scheme_truth.json` must show no `dash-*.scheme` file. scheme_truth.json may change only inside `_meta`: check it with a short python3 comparison of the HEAD and worktree JSON with `_meta` removed, which prints `equal`. Any other difference stops the task: investigate it and report, and never patch a generated file (R7, A152).

    If `_meta` changed, `git -C $WT add -f test/fixtures/scheme_truth.json` at commit time (30-17).
  ]]></action>
  <verify><![CDATA[The comparison prints `equal`; `git -C $WT diff --name-only -- 'dash-*.scheme' | wc -l` prints 0; `python3 -m pytest test/test_scheme_fidelity.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>The batch's one regeneration ran on the new grammar and changed nothing that dash draws.</done>
</task>

<task type="auto" id="30-11">
  <name>Flip pinned tests, part one</name>
  <files>test/test_options.py, test/test_option_validation.py, test/test_security_surface.py</files>
  <action><![CDATA[
    Flip, each in place, with a comment naming WP-30 P1.13a and the measured twoway value of E3:
    - F1: `test_case_insensitive_color` asserts `translate_mcolor("RED")` raises and `parse_color_alpha("RED", "mcolor")` is `("#000000", None)` with the note; rename it in place to `test_colour_names_are_case_sensitive`.
    - F2: black, and the "using black." note; its docstring's "draws the default colour" is corrected to twoway's measured black.
    - F3: `("#000000", None)` silent, and `("#000000", 0.4)` with "dash: fcolor(notacolour%40) is not a recognised colour; using black.".
    - F4: rename to `test_a_bad_mcolor_draws_black`, asserting `#000000`.
    - F5: the note "dash: <text> is not a recognised colour; using black."; the option's own property is `#000000` in both modes; the three equality assertions are kept.
    - F12: the `lcolor` param of `test_a_reference_line_sub_option` expects "using black." and a Span `line_color` of `#000000` in both modes; the other params are unchanged.
    - F6: body `background-color: #ffffff;`; `.db-title` `color: #ffffff`; no warning containing either payload; the rule-shape, selector-list and KPI-control assertions are kept.
    - F7: the 6-digit params are kept, and a sibling parametrised test `test_a_short_hex_is_not_a_stata_colour` asserts `translate_mcolor` raises for `#fff`, `#FFF` and `#abc`.

    Run the three files. Append each `Flipped:` line to `$S/30-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_options.py test/test_option_validation.py test/test_security_surface.py -q -n 6 -p no:cacheprovider` passes; `grep -c '^Flipped:' "$S/30-flips.txt"` is at least 11.]]></verify>
  <done>The first set of tests that pinned the old colour behaviour asserted twoway's measured drawing instead, each with its reason, and none was deleted.</done>
</task>

<task type="auto" id="30-12">
  <name>Flip pinned tests, part two</name>
  <files>test/test_color_fidelity.py, test/test_color_alias.py, test/test_ci_band_style.py</files>
  <action><![CDATA[
    Flip, in place, each with a comment naming WP-30 P1.13a:
    - F8: the British spellings are not `_COLOR_MAP` keys, and `OptionTranslator._BRITISH_SPELLINGS[alias] == canonical`; rename to `test_a_british_spelling_is_not_a_stata_name` and update the class docstring.
    - F9: `#000000` and the "using black." note for map_scatter and map_line.
    - F14: for the seven `acolor` params of `TestAdversarial::test_a_bad_colour_is_noted_and_the_scheme_kept`, the band's fill is `#000000`, noted once, with no raw text on any model. Rename the test in place to `test_a_bad_colour_is_noted_and_drawn_black`; the params of other options are unchanged where they pass.

    Run the three files. Append each `Flipped:` line to `$S/30-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_color_fidelity.py test/test_color_alias.py test/test_ci_band_style.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>The British spellings, the common plot types and the confidence band were pinned to twoway's black for an unknown colour.</done>
</task>

<task type="auto" id="30-13">
  <name>Flip pinned tests, part three</name>
  <files>test/test_help_claims_7.py, test/test_scheme_coercion.py, test/test_scheme.py</files>
  <action><![CDATA[
    Flip, in place, each with a comment naming WP-30 P1.13a:
    - F15: `TestRegionColours::test_an_unknown_colour_is_named_and_the_scheme_kept` becomes `test_an_unknown_colour_is_named_and_drawn_black` (both params).
    - F16: in `TestAdversarialLegendAxesRegions`, the hostile region payload and the unpaired quote give `#000000` regions, never the raw text; the payload note and the compound-quote `#ff0000` control are kept.
    - F17: rename to `test_the_warning_says_black_as_twoway`, asserting "using black, as twoway does" in the warning.
    - F18: `test_xss_escaped_in_css` asserts the payload file's CSS equals the clean file's except the body rule, which is `background-color: #ffffff;`. Keep `<script>` absent, the positive control, and the rule and declaration counts.

    Run the three files. Append each `Flipped:` line to `$S/30-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_7.py test/test_scheme_coercion.py test/test_scheme.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>Region colours, the scheme warning and the scheme CSS block were pinned to what twoway draws for an unknown or malformed colour.</done>
</task>

<task type="auto" id="30-14">
  <name>Flip the rest and classify the sweep</name>
  <files>test/test_scheme_resolution.py, test/test_twoway_option_parity.py, test/test_html_output.py</files>
  <action><![CDATA[
    Flip, in place, each with a comment naming WP-30 P1.13a:
    - F19: rename to `test_an_unknown_colour_keeps_its_opacity`; it asserts `#000000` and `p_alphas[0] == 0.2`, with the warning naming the value.
    - F20: the note "…; using black.".
    - F21: both tests warn "…; using black"; the valid-HTML assertions are kept.

    Then run the 42 candidate files of Notes, "Prototype measurement", plus the file holding S08's brushed-copy tests, with `test/` paths (the full-suite hook needs them) at `-q -n 6 -p no:cacheprovider -rf`, into `$S/30-sweep.log`. Classify every FAILED node as one of F1-F21 or new:
    - a new node that pins case-insensitive names, British spellings, comma triplets, 3-digit hex, the scheme default for an unknown colour, the "using the scheme's default"/"ignoring it"/"falling back to"/"match Stata" texts for colours, or `#d9e8f0` for an unreadable background is flipped in its own file the same way, its line appended to `$S/30-flips.txt`, and the file staged in 30-17 (R9);
    - anything else is a defect of the fix, corrected before going on.

    S08's brushed-copy tests must stay green (A37, ratification 06oct2026): a failure among them is a regression of S08's fix, corrected in S30's code, never flipped.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_resolution.py test/test_twoway_option_parity.py test/test_html_output.py -q -n 6 -p no:cacheprovider` passes; every FAILED node of `$S/30-sweep.log` is named in `$S/30-flips.txt` or was fixed, and a re-run of the files they name passes.]]></verify>
  <done>Every pinned test the grammar turned red was found on the worktree and flipped with its reason or fixed.</done>
</task>

<task type="auto" id="30-15">
  <name>Add parity cases and the truth block</name>
  <files>test/test_mode_parity.py, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Append four `_case(...)` entries at the end of `CORPUS` in test/test_mode_parity.py, under a comment naming WP-30 P1.13a:
    - "scatter, the colour grammar" (`mcolor(navy*.5)`, `mfcolor("hsv 240 1 1")`, `mlcolor(bg)`);
    - "line, an unknown colour drawn black" (`lcolor(bogus)`), with its `_MUST_WARN` entry "dash: lcolor(bogus) is not a recognised colour; using black";
    - "bar, an unknown fill" (`fcolor(bogus)`);
    - "s1rcolor, fg" (build option scheme s1rcolor, `mcolor(fg*.5)`).

    Run `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider` (G3).

    Fill S01's S30 stub between its start and end lines with CG-10..CG-16 as "Stata truth / Truth block" specifies. The helpers `_s30_page`, `_s30_app` and `_s30_svg` (copies of S16's, renamed, `version 19`) go directly above S30's header. Files are written only under `` `w30_work' `` and erased before the end line.

    Run through the driver from the worktree: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_test_wp30_truth.do"` and `WP30_ONLY=S30 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_wp30_truth.do"`. Read the log. If python_exec was dropped (a SKIP or 222), restore it and re-run, because a skip is not a pass.
  ]]></action>
  <verify><![CDATA[test/test_mode_parity.py passes; `$S/run_test_wp30_truth.log` prints `S30 start`, `CG-10 PASS` .. `CG-16 PASS`, `S30 end` and `test_wp30_truth: ALL CHECKS PASSED`, with no SKIP line.]]></verify>
  <done>The parity corpus carried the new colour forms in both modes, and live twoway and both dash modes drew the same colours for the grammar's forms, an unknown colour, a malformed one and a user scheme, before and after a served move.</done>
</task>

<task type="auto" id="30-16">
  <name>Describe the colour grammar in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Edit only these paragraphs (R3; no batch-10 partner edits them). Write no number that a test of this section does not pin.
    - **Differences from twoway, `{marker validation}`:** an unknown or wrong-case colour is drawn black with the note, as twoway draws it; other style names keep the scheme's default.
    - **The structured-options paragraph** (the "A colour written with commas" sentence, c96facd:786-789): a colour written with commas in a plot colour option is refused, as twoway refuses it (`invalid '0'`, r(198)). Inside a structured option's sub-option it is drawn black with a note, which twoway refuses.
    - **Region Styling Options, the sentence "Each of these takes …" (c96facd:2716-2719):** the options take any Stata colour (see Colours), and an unknown colour is drawn black with a note. Keep the `bgcolor()` sentences, which are S38's.
    - **Marker and Transparency Options:** add a new paragraph `{marker colours}{ul:Colours.}`:
      - names, case-sensitive; `grey` and the other British spellings are not names;
      - `"R G B"`, CMYK `"C M Y K"` (proportions or integers), `"hsv H S V"` and `#rrggbb`;
      - `bg`/`fg`/`background`/`foreground` (the scheme's, when the scheme names them);
      - `*#` (lighter below 1, darker above, multiplied under a scheme's `system naturally_white 0`) and `%#`, in either order;
      - an unknown colour is black with a note (a bar at its intensity), a malformed hex, multiplier or opacity keeps the default silently, and a comma is refused;
      - BR-30.13's interim differences, stated plainly: a bare `*#` keeps the default colour; at `mlabcolor()`, `colormissing()`, `color()`/`bfcolor()`/`blcolor()` on bar and rbar, `color()` on area, rarea and histogram, and the pc, dropline, rcapsym and scatteri colour options, an unknown colour keeps the scheme's colour with the note; title and region colours read `bg`, `fg` and `*#` with s2color's.
    - **Stata scheme support, "What a scheme file of yours may include":** a colour in your file follows the same grammar, with twoway's scheme-file rules (commas separate numbers; a malformed number draws white; an unknown name draws black with a note; `system naturally_white 0`).

    Run the help-claims and help-conformance tests.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_2.py test/test_help_claims_7.py test/test_help_claims_8.py test/test_help_conformance.py -q -n 6 -p no:cacheprovider` passes; `grep -c "the triplet {cmd:255 0 0}" dash.sthlp` prints 0; `grep -c "marker colours" dash.sthlp` prints 1.]]></verify>
  <done>The help described Stata's colour grammar as dash reads it, the comma refusal, the scheme-file rules and the interim differences until section 43.</done>
</task>

<task type="auto" id="30-17">
  <name>Close P1.13a and commit the section</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP30_OPEN["P1.13a"]` and close that BUGS.md entry in place: `- [ ]` becomes `- [x]`, and its open `  - Resolution:` line is replaced by the Resolution of Notes, "Text for the closing task", with the indentation kept and only tests that exist named. Delete the `"P1.13a"` key line from `WP30_OPEN`. In CHANGELOG.md replace the `<!-- WP-30 P1.13a -->` marker in `### Results that change` and the one in `### Changed behaviour (may need your do-files changed)` with the lines of Notes, each ending `(WP-30, P1.13a)` (R4).

    Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Then run `git -C $WT merge --no-edit main`, expecting `Already up to date.`; otherwise stop and report (E9). Then make one full run through the queue: `<scratch>/full_suite_queue.sh $WT <scratch>/30-full-1.log`, launched in the background and waited for on its `exit=` line, never relaunched (E1; E6 for the known flaky tests).

    Check whether `test_varlist_expansion.py`'s `_SINGLE_Y_BASELINE_SHA256` failed. It is expected unchanged (no default colour changes). If it changed, investigate it before re-deriving with the R10 comment.

    Stage exactly:
    - dash_render.py, dash.ado, dash.sthlp, BUGS.md, CHANGELOG.md;
    - scripts/extract_colour_grammar_truth.do, scripts/extract_scheme_truth.py;
    - test/test_colour_grammar.py, test/function_test_map.py, test/test_option_validation.py, test/test_option_validation.cscript, test/test_help_claims_2.cscript, test/test_wp30_truth.cscript, test/test_tracking_documents.py, and the flipped files of `$S/30-flips.txt`;
    - `git add -f test/fixtures/colour_grammar_truth.json` (and test/fixtures/scheme_truth.json if 30-10 changed its `_meta`).

    Check `git diff --cached --name-status` (G6). Write the message to `$S/30-msg.txt` per the commit boundary and run G7 on it. Confirm that `git -C $WT branch --show-current` prints `wp30-s30`, commit with `git commit -F "$S/30-msg.txt"`, run G7 on `git log -1 --format=%B`, and report the sha and the message path to the merger.
  ]]></action>
  <verify><![CDATA[`grep -E '^exit=0' <scratch>/30-full-1.log` matches and its summary shows 0 failed; `git log -1 --format=%s` ends `(WP-30 P1.13a)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.13a -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.13a": "' test/test_tracking_documents.py` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.13a was closed naming tests that exist, its two CHANGELOG markers carried the measured old and new values, and the section's one green commit on wp30-s30 was ready for the merger.</done>
</task>

## Section completion criteria

- `OptionTranslator.stata_colour` answers all 175 values of E3 (two UNCLEAR excluded). `translate_mcolor`, `translate_lcolor` and `parse_color_alpha` delegate to it, and `_COLOR_MAP` holds exactly the 92 names of Stata's `color-*.style` files (97 keys at `c96facd`, `none` among the 92).
- The mapper's translator reads its graph's scheme. Every applier site draws an unknown colour black with the note, a malformed one in the default silently, and the new forms by Stata's rules, in both modes and after a served move.
- `SchemeParser` reads every colour through the grammar in scheme context, has `foreground_color`, `fg_lookup` and `bg_lookup`, and draws an unreadable value as twoway does. The CSS block holds only hex.
- `_textbox_color`, `_dash_graph_color` and `_dash_refline_draw` draw an unknown colour black with the note. The KPI's guard passes.
- dash.ado refuses a comma-written plot colour with `invalid '<word>'`, r(198). CG-01..CG-08, HC2-16p/q and CG-10..CG-16 pass.
- The extractor agrees with the renderer, and the regeneration changed nothing outside `_meta`.
- F1-F21 and every `$S/30-flips.txt` node are flipped with reasons, and none is deleted.
- One green commit `(WP-30 P1.13a)` exists on `wp30-s30`. BUGS.md's entry is closed in place, `WP30_OPEN` lost only `"P1.13a"`, and both markers are replaced.
- Not edited: every applier and `map_*`, `_apply_colorvar`, `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, `_build_filter_widgets`, the copy lists, `_FALLBACK_PROPS`, dash_parse.mata, any runner block or hygiene pin, any tracking document beyond BUGS.md and CHANGELOG.md.

## Notes

**Traps for the executor.**
1. **The bound translator is an instance attribute, not a method override.** A `staticmethod` is a non-data descriptor, so the lambdas set in `__init__` win for `self.tr.parse_color_alpha(...)`, while `OptionTranslator.parse_color_alpha(...)` (module readers, SchemeParser) stays unbound. Use no nested `def`: `test_function_test_map.py` maps every `def` at any depth.
2. **Order inside `_init_properties` matters.** `naturally_white` comes first, then foreground, then background, then the rest. The served `_dash_build_scheme` calls `_init_properties()` on a `__new__` instance, so nothing may be set in `__init__` alone.
3. **`_dash_style_note` de-duplicates on `(prefix, option, value, what)`.** A bar's `color(bogus)` is noted first by `map_bar`'s direct site (scheme fill, S43's), and the line applier's fold (black outline) is then silent. That is the interim of BR-30.13, not a defect to chase here.
4. **Stata's `(note: …)` appears twice per scatter in twoway's log** (fill and outline). dash prints one per render. CG-11 counts dash's notes, not twoway's.
5. **A comma refusal needs the value as stored.** After S11 the style options are `string asis`, so quotes reach the validator. The branch strips one enclosing pair and leaves alone a value with any other `"` (`mcolor("red",blue)`, which twoway accepts).
6. **R10:** `test_option_validation.py`'s `KINDS` is a pin of this table; write it with `# 13 -> 14: P1.13a the colour kind`. The single-y digest is not expected to move.
7. **R1:** CG-01..CG-08 go in `test_option_validation.cscript` as one run before the CV block, and CG-10..CG-16 inside S30's own truth block. CG ids are unused at `c96facd` (manifest), and CG-09 is left free.
8. **R2:** no copy-list change. R3: the help paragraphs above only. R4/R5: the two markers and the one key. R7: the regeneration runs last in the batch and is never hand-patched. R12: no applier or mapper is edited.
9. **Case-insensitive file systems:** the extractor's style lookup must reject a token that is not all lower case before opening `color-<tok>.style`, or macOS finds `color-navy.style` for `Navy`.

**Prototype measurement (03oct2026).** TR-30.1 to TR-30.8 were applied roughly to a `git archive` of `c96facd` in scratch (`s30-proto/patch.py`), and these 42 files were run at `-n 4`:

`test_colorvar_legend test_adversarial_matrix test_axis_options test_ci_band_style test_colorvar_forms test_dropline_marker_options test_example_simulation test_help_claims_2 test_color_fidelity test_immediate_scheme test_immediate_values test_color_alias test_installed_layout test_kpi_security test_help_claims_5 test_immediate_dashboards test_help_claims_8 test_options test_html_verification test_marker_label_parity test_release_verdict test_mode_parity test_option_validation test_scheme_coercion test_pccapsym_pcarrowi test_scheme_quoted_values test_pipeline_integration test_scheme_visual_truth test_scheme test_server test_scheme_fidelity test_server_kpi_card test_help_claims_7 test_scheme_consumption test_twoway_option_parity test_security_surface test_glyphs test_scheme_integration test_scheme_resolution test_html_output test_function_test_map test_statistical_helpers`

Its result: 43 failed, 10,237 passed. Every red was a row of E6 except `test_function_test_map.py::test_every_function_has_an_entry` (the prototype added no map entries). The prototype carried neither S15 nor S16, so 30-14's sweep re-measures on the worktree.

**Commit-body line forms (index Deltas, A141).**
- Subject: `Read Stata's colour grammar in options and scheme files (WP-30 P1.13a)`.
- `Regression: test/test_colour_grammar.py::TestStataColourOption::test_the_measured_option_values -- failed at <sha> with AttributeError: type object 'OptionTranslator' has no attribute 'stata_colour'`, one line per regression class.
- `Flipped: test/test_options.py::TestColorEdgeCases::test_case_insensitive_color -- RED read as red was wrong because twoway names are case-sensitive (named style Red not found, black)`, and likewise for each flip.
- No co-author or tool trailer (CLAUDE.md rule 6). G7 is checked on the message file and on the commit.

**Text for the closing task (30-17).**

BUGS.md Resolution (one line):

`  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.13a). Colours are read with Stata's colour grammar as StataNow 19.5 draws it: OptionTranslator.stata_colour reads colour*# (towards white below 1, divided above it with Stata's clamp to the smallest non-zero channel, multiplied under a scheme's system naturally_white 0, through GlyphMapper._blend_intensity), CMYK, HSV, bg/fg/background/foreground from the scheme, quoted forms and %# and *# in either order. translate_mcolor, translate_lcolor and parse_color_alpha delegate to it, and the glyph mapper's translator reads its own graph's scheme, so every marker, line, fill and confidence-band colour option draws an unknown or wrong-case colour black (a bar #333333) with a note, keeps the default silently for a malformed hex, multiplier or opacity, and draws the new forms, in the saved page and the served app before and after a filter move. _textbox_color, _dash_graph_color and _dash_refline_draw draw an unknown colour black with the note. SchemeParser reads every scheme colour in scheme context (a new foreground_color and the bg/fg lookups, an unknown name black with one note per key, a malformed number white, as twoway draws them). _COLOR_MAP holds only Stata's names: grey, dimgrey, bluishgrey and ltbluishgrey are unknown colours, kept for KPI cards alone, whose colours are unchanged. dash.ado refuses a comma-written plot colour with twoway's words, invalid '<word>', r(198). The scheme extractor reads the same grammar, and the shipped schemes regenerated unchanged. Pinned by test/test_colour_grammar.py::TestStataColourOption::test_the_measured_option_values, test/test_colour_grammar.py::TestStataColourScheme::test_the_measured_scheme_values, test/test_colour_grammar.py::TestTheMapperReadsItsScheme::test_a_bound_translator_reads_its_scheme, test/test_colour_grammar.py::TestSchemeFiles::test_an_unreadable_key_draws_black_with_one_note, test/test_colour_grammar.py::TestBothModes::test_scatter_forms, test/test_colour_grammar.py::TestAfterAFilterMove::test_the_served_app_redraws_the_same_colours, test/test_colour_grammar.py::TestTheKpiKeepsItsLeniency::test_values_accepted_today_are_unchanged, test/test_colour_grammar.py::TestStataTruth::test_each_probe, test/test_option_validation.cscript CG-01, test/test_wp30_truth.cscript CG-10; fixture test/fixtures/colour_grammar_truth.json. Residual, deferred (WP-30): a bare *# or %# and an unknown colour at mlabcolor(), colormissing(), the bar, rbar, area, rarea and histogram color(), bfcolor() and blcolor(), and the pc, dropline, rcapsym and scatteri colour options, and each figure's own scheme for title, region and KPI colours, are section 43's; a user scheme that writes color background or color foreground as a hex code gives bg/fg that colour where twoway draws black with a note; a comma-written colour inside a structured option's sub-option is noted and drawn black where twoway refuses it; navy*52 and color foreground bg after color background red are UNCLEAR and not matched.`

CHANGELOG `### Results that change` (replacing `<!-- WP-30 P1.13a -->`):

- `- Stata's colour grammar is read in every colour option and scheme file: dash scatter mpg weight, mcolor(navy*.5) drew the scheme's #1a476f with a note, now #8da3b7; mcolor("85 40 0 144") (CMYK) and mcolor("hsv 209 .766 .435") draw #1a476f and #19456e; mcolor(fg) draws the scheme's foreground (white under s1rcolor); a scheme file's color p1 navy*.5 drew #000000, now #8da3b7. (WP-30, P1.13a)`
- `- An unknown or wrong-case colour is drawn black with a note, as twoway draws it: mcolor(bogus), mcolor(Navy) and mcolor(grey) drew the scheme's colour (Navy and grey silently), now #000000; bar …, fcolor(bogus) draws #333333; title("T", color(bogus)), graphregion(color(bogus)) and xline(3000, lcolor(bogus)) draw black. A malformed hex code or multiplier keeps the default silently: mcolor(#f00) drew red, now the scheme's colour. (WP-30, P1.13a)`
- `- A scheme file's unreadable colour is drawn as twoway draws it: color background bogus drew #d9e8f0, now #000000 with a note; color background #}a{b;c is drawn white, silently. (WP-30, P1.13a)`

CHANGELOG `### Changed behaviour (may need your do-files changed)` (replacing `<!-- WP-30 P1.13a -->`):

- `- A colour written with commas in a plot colour option is refused, as twoway refuses it: dash scatter mpg weight, mcolor(255,0,0) drew red, now stops with invalid '0', r(198). Write the triplet with blanks, mcolor("255 0 0"). (WP-30, P1.13a)`

**Notes for later sections.**
- **S43:**
  - route the D-30c direct sites through `parse_color_alpha` (or `stata_colour` with a `base=` argument) for `%#`, a bare `*#`/`%#` and black on unknown;
  - pass each figure's scheme context to `_textbox_color`, `_dash_graph_color` and `_resolve_kpi_color` (`OptionTranslator.scheme_colour_context(scheme)`);
  - rewrite the interim sentences of the `{marker colours}` help paragraph;
  - measured bases: `mcolor(*.5)` `#8da3b7`, `mlabcolor(*.5)` `#8da3b7`, `title(…, color(*.5))` `#8f96a9`, `graphregion(color(*.5))` `#f5f9f9`, `xline(…, lcolor(%50))` `#c10534` at 0.5, `text(…, color(*.5))` `#808080` (research p1-13 §3, critic).
- **S31, S38, S39:** call `parse_color_alpha(value, option, **OptionTranslator.scheme_colour_context(scheme))` for labcolor, axis-line, region and refline colours, so there is one `%` reader (register P1.13.5). If a section refuses a comma-written sub-option colour (twoway: `invalid '<word>'`, r(198); E3's comma table), it reuses TR-30.11's word rule.
- **S34:** a third-party scheme reaches `SchemeParser` unchanged, and its quoted RGB, CMYK and HSV values are read by TR-30.9.

**Notes for the closeout (A145; S58 reads this).**
- **GAPS2 D7 (GAPS2.md:918-927):**
  - sub-claims D7-a (`colour*#`), D7-c (CMYK), D7-d (HSV) and D7-e (bg/fg) are closed by this section's commit (P1.13a);
  - D7-b (bare `*#`) stays open until S43 (P1.13b), which records D7 closed;
  - the Tracked line names both commits, and plan step 4 ("fall back to the included scheme's value") is recorded as not taken: twoway draws black (measured; D-30h).
- **DROPIN-REMAINING.md:103 (P1.13):** the "#000000 fallback" claim is true of twoway too. dash now matches twoway, black for an unreadable name and white for a malformed number, rather than "fixing" it.
- **New residuals for S58 to file (P2):**
  - (1) a user scheme's `color background`/`color foreground` written as hex: `bg`/`fg` resolve to it in dash, where twoway's named-style lookup fails (probe t05);
  - (2) a comma-written colour inside a structured option's sub-option (`title(…, color("1,2,3"))`, region colours, `xline(…, lcolor())`) is noted and drawn black, where twoway refuses it r(198), unless S38/S39 took it;
  - (3) the UNCLEAR navy*52 clamp and the `color foreground bg` cycle (probe sj), measured and not matched;
  - (4) `mcolor("red",blue)`, accepted by twoway with no note, reaches the renderer as one unknown colour.
- **Research p1-13 correction for the record:** an invalid multiplier keeps the site's default, not the base colour (D-30d).
